"""Source against playback by phase, at common replay times.

Usage: python analyze_run.py <run folder> [source csv]

Lead SAMPLE rows read the pose after native integration of the tick whose replay
time they carry, so pose and velocity are compared at replay + OFFSET (fitted and
reported). Draw arguments are compared at the sample's own replay time. Supported
state retention comes from exterior-*.csv (requested against post-animation read).
"""
import bisect, csv, glob, math, statistics, sys
from pathlib import Path

HERE = Path(__file__).parent
run = HERE / sys.argv[1]
source = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / 'source/20261004T200936Z-0001.csv'
ARGS = [0,3,5,9,10,11,12,13,14,15,16,17,18,21,38,88,190,191,192,193,210,212,1,6,4,101,103,102,2,89,90,28,29]
STROBE = {192, 193}
WHEEL_ROTATION = {101, 102, 103}
# Acceptance limits agreed with the user on 4 October 2026 (#28).
LIMITS = dict(horizontal=0.10, vertical=0.05, attitude=0.5, velocity_ground=0.25, velocity_air=2.0,
              clock_ms=20, state=1e-3, retention=1e-6, ground_clearance=0.01, parked_drift=0.001)
LOAD_TRANSIENT = 0.2  # s after mission load, excluded from held staging
failures = []

# Source
lines = source.read_text(encoding='utf-8').splitlines()
h = next(i for i, l in enumerate(lines) if l.startswith('t,x,'))
cols = lines[h].split(',')
src = []
for l in lines[h+1:]:
    if l.startswith('END'): break
    d = dict(zip(cols, l.split(',')))
    src.append({k: float(v) if v else math.nan for k, v in d.items()})
t0 = src[0]['t']; ts = [r['t'] - t0 for r in src]
TOUCHDOWN = next(ts[i] for i in range(1, len(src)) if src[i-1]['in_air'] == 1 and src[i]['in_air'] == 0)
LIFTOFF = next(ts[i] for i in range(1, len(src)) if src[i-1]['in_air'] == 0 and src[i]['in_air'] == 1)

def at(t, keys):
    i = max(1, min(len(ts)-1, bisect.bisect_right(ts, t)))
    a, b = src[i-1], src[i]; w = max(0, min(1, (t-ts[i-1])/(ts[i]-ts[i-1])))
    return [a[k]+(b[k]-a[k])*w for k in keys]
def prev(t, key):
    i = max(0, min(len(ts)-1, bisect.bisect_right(ts, t+1e-9)-1)); return src[i][key]

# Playback lead samples
samples, contact = [], []
log = (run/'dcs-playback.log').read_text(encoding='utf-8', errors='replace').splitlines()
seen = set()
for l in log:
    if ' SAMPLE,' in l and 'Lead' in l:
        a = l.split(' SAMPLE,')[1].split(',')
        key = ('S', a[0], a[2])
        if key in seen: continue
        seen.add(key)
        samples.append(dict(phase=a[0], time=float(a[2]), p=[float(v) for v in a[3:6]], f=[float(v) for v in a[6:9]],
                            u=[float(v) for v in a[9:12]], v=[float(v) for v in a[12:15]], replay=float(a[15]),
                            args=dict(zip(ARGS, map(float, a[17:17+len(ARGS)])))))
    elif ' CONTACT,' in l:
        a = l.split(' CONTACT,')[1].split(',')
        key = ('C', a[0], a[1])
        if key in seen: continue
        seen.add(key)
        contact.append(dict(phase=a[0], time=float(a[1]), in_air=int(a[2]), clearance=float(a[4]), life=float(a[5])))
replay_of = {s['time']: s['replay'] for s in samples}

def phase_of(s):
    if s['phase'] in ('waiting', 'countdown'): return 'held'
    if s['phase'] == 'parked': return 'parked'
    if s['phase'] != 'playing': return None
    t = s['replay']
    if t < LIFTOFF - 3: return 'taxi out + roll'
    if t < LIFTOFF + 5: return 'liftoff (-3/+5 s)'
    if t < TOUCHDOWN - 5: return 'airborne'
    if t < TOUCHDOWN + 3: return 'touchdown (-5/+3 s)'
    return 'rollout + taxi in'

def angle(a, b):
    d = sum(x*y for x, y in zip(a, b)) / (math.hypot(*a)*math.hypot(*b)); return math.degrees(math.acos(max(-1, min(1, d))))

def pose_error(s, offset):
    t = 0 if s['phase'] in ('waiting', 'countdown') else s['replay'] + (0 if s['phase'] == 'parked' else offset)
    x, y, z, vx, vy, vz, fx, fy, fz, ux, uy, uz = at(t, ['x','y','z','vx','vy','vz','fx','fy','fz','ux','uy','uz'])
    p = s['p']
    return (math.hypot(p[0]-x, p[2]-z), p[1]-y, max(angle(s['f'], [fx,fy,fz]), angle(s['u'], [ux,uy,uz])),
            math.dist(s['v'], [vx,vy,vz]) if s['phase'] == 'playing' else 0.0)

# Fit the sampling offset on airborne flight.
flight = [s for s in samples if phase_of(s) == 'airborne']
offsets = [k*0.005 for k in range(-4, 13)]
best = min(offsets, key=lambda o: statistics.mean(pose_error(s, o)[0] for s in flight[::5]))
print(f'{run.name}: {len(samples)} lead samples; liftoff {LIFTOFF:.2f} s, touchdown {TOUCHDOWN:.2f} s; fitted sampling offset {best*1000:.0f} ms')

def stats(v):
    v = sorted(abs(x) for x in v); return f'max {v[-1]:.3f} p95 {v[int(.95*(len(v)-1))]:.3f} rms {math.sqrt(sum(x*x for x in v)/len(v)):.3f}'
print('\nPose (horizontal m, vertical m, attitude deg, velocity m/s)')
order = ['held', 'taxi out + roll', 'liftoff (-3/+5 s)', 'airborne', 'touchdown (-5/+3 s)', 'rollout + taxi in', 'parked']
for ph in order:
    sel = [s for s in samples if phase_of(s) == ph and not (ph == 'held' and s['time'] < samples[0]['time'] + LOAD_TRANSIENT)]
    if not sel: continue
    e = [pose_error(s, best) for s in sel]
    vlim = LIMITS['velocity_air'] if ph in ('airborne', 'liftoff (-3/+5 s)', 'touchdown (-5/+3 s)') else LIMITS['velocity_ground']
    for name, k, lim in (('horizontal', 0, LIMITS['horizontal']), ('vertical', 1, LIMITS['vertical']),
                         ('attitude', 2, LIMITS['attitude']), ('velocity', 3, vlim)):
        value = max(abs(x[k]) for x in e)
        if value > lim: failures.append(f'{ph} {name} {value:.3f} > {lim}')
    print(f'  {ph:20s} n={len(sel):5d} | horiz {stats([x[0] for x in e])} | vert {stats([x[1] for x in e])} | att {stats([x[2] for x in e])} | vel {stats([x[3] for x in e])}')

print('\nDraw arguments against source at the same replay time (playing and parked)')
worst = {}
for s in samples:
    if s['phase'] not in ('playing', 'parked'): continue
    for a, v in s['args'].items():
        col = f'arg_{a}'
        if col not in src[0]: continue
        if a in STROBE: ref = prev(s['replay'], col)  # sampled edge, not interpolated
        else: ref = at(s['replay'], [col])[0]
        d = abs(v-ref)
        if a in WHEEL_ROTATION: d = min(d, 1-d)  # rotation wraps at 1
        worst.setdefault(a, []).append(d)
for a in ARGS:
    if a in worst:
        d = worst[a]; n = sum(1 for x in d if x > 1e-4)
        if a not in STROBE and max(d) > LIMITS['state']: failures.append(f'arg {a} {max(d):.4f} > {LIMITS["state"]}')
        if max(d) > 1e-4: print(f'  arg {a:3d}: max {max(d):.4f}, {n}/{len(d)} reads differ by >1e-4' + (' (strobe edge)' if a in STROBE else ''))
print('  all other compared arguments within 1e-4')

ext = next(run.glob('exterior-*.csv'), None)
if ext:
    diff, n = 0.0, 0
    for r in csv.DictReader(open(ext)):
        if r['after'] in ('', None) or r['requested'] in ('', None): continue
        diff = max(diff, abs(float(r['after'])-float(r['requested']))); n += 1
    if diff > LIMITS['retention']: failures.append(f'retention {diff:.2e}')
    print(f'\nSupported-state retention: {n} post-animation reads, max |after - requested| = {diff:.2e}')

print('\nContact (playback in-air flag and origin clearance against source)')
for ph in order[1:]:
    sel = [c for c in contact if c['time'] in replay_of and phase_of(next(s for s in samples if s['time'] == c['time'])) == ph] if contact else []
    if not sel: continue
    mism = [c for c in sel if c['phase'] == 'playing' and c['in_air'] != int(prev(replay_of[c['time']]+best, 'in_air'))]
    clr = [c['clearance'] - (at(replay_of[c['time']]+(0 if c['phase']=='parked' else best), ['y'])[0] - at(replay_of[c['time']], ['terrain_height'])[0]) for c in sel]
    print(f'  {ph:20s} n={len(sel):5d} | in-air mismatches {len(mism)} | clearance minus source {stats(clr)} | life min {min(c["life"] for c in sel):.0f}')
    if mism: print('    mismatch replay times: ' + ', '.join(f'{replay_of[c["time"]]:.2f}' for c in mism[:12]))
    if ph in ('taxi out + roll', 'rollout + taxi in', 'parked') and max(abs(x) for x in clr) > LIMITS['ground_clearance']:
        failures.append(f'{ph} ground clearance {max(abs(x) for x in clr):.3f}')
    if min(c['life'] for c in sel) < max(c['life'] for c in contact): failures.append(f'{ph} life lost')

park = [s for s in samples if s['phase'] == 'parked']
if park:
    p0 = park[0]['p']
    drift_m = max(math.dist(s["p"], p0) for s in park)
    print(f'\nParked hold: {park[-1]["time"]-park[0]["time"]:.1f} s; max drift from first parked pose {drift_m:.6f} m')
    if drift_m > LIMITS['parked_drift']: failures.append(f'parked drift {drift_m:.4f}')
running = [s for s in samples if s['phase'] == 'playing']
drift = [s['replay'] - (s['time'] - running[0]['time']) for s in running]
print(f'Replay clock against model time while playing: drift {min(drift)*1000:+.1f} .. {max(drift)*1000:+.1f} ms')
if max(abs(x) for x in drift)*1000 > LIMITS['clock_ms']: failures.append('replay clock drift')
print('\nAgreed limits (#28): ' + ('PASS' if not failures else 'FAIL: ' + '; '.join(failures)))
print("DCS's reported inAir() is not a gated channel; see the in-air mismatches above.")
