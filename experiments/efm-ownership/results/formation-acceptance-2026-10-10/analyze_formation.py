"""Formation playback against each aircraft's own take, and pair separation.

Usage: python analyze_formation.py <run folder> <aircraft name>=<take csv> ...

Applies the single-aircraft method and #28 limits (envelope-2026-10-07/analyze_run.py)
to every playback aircraft: mission SAMPLE rows read the pose after native
integration of the tick whose replay time they carry, so pose is compared at
replay + a fitted offset. Separation (gate 2) is measured, not gated: at each
shared sample, the distance between two playback aircraft against the distance
between their takes at that replay time plus the same fitted offset.
"""
import bisect, math, statistics, sys
from pathlib import Path

LIMITS = dict(horizontal=0.10, vertical=0.05, attitude=0.5, velocity_ground=0.25, velocity_air=2.0)


class Take:
    def __init__(self, path):
        lines = Path(path).read_text(encoding='utf-8').splitlines()
        h = next(i for i, l in enumerate(lines) if l.startswith('t,x,'))
        cols = lines[h].split(',')
        self.rows = []
        for l in lines[h+1:]:
            if l.startswith('END'): break
            self.rows.append({k: float(v) if v else math.nan for k, v in zip(cols, l.split(','))})
        t0 = self.rows[0]['t']; self.ts = [r['t']-t0 for r in self.rows]
        air = [r.get('in_air', 1) for r in self.rows]
        self.liftoff = next((self.ts[i] for i in range(1, len(air)) if air[i-1] == 0 and air[i] == 1), -math.inf)
        self.touchdown = next((self.ts[i] for i in range(len(air)-1, 0, -1) if air[i-1] == 1 and air[i] == 0), math.inf)

    def at(self, t, keys):
        i = max(1, min(len(self.ts)-1, bisect.bisect_right(self.ts, t)))
        a, b = self.rows[i-1], self.rows[i]; w = max(0, min(1, (t-self.ts[i-1])/(self.ts[i]-self.ts[i-1])))
        return [a[k]+(b[k]-a[k])*w for k in keys]


def angle(a, b):
    d = sum(x*y for x, y in zip(a, b))/(math.hypot(*a)*math.hypot(*b)); return math.degrees(math.acos(max(-1, min(1, d))))


def main():
    run = Path(sys.argv[1]); takes = {n: Take(p) for n, p in (a.split('=', 1) for a in sys.argv[2:])}
    samples = {n: [] for n in takes}; seen = set()
    for line in (run/'dcs-playback.log').read_text(encoding='utf-8', errors='replace').splitlines():
        if ' SAMPLE,' not in line: continue
        a = line.split(' SAMPLE,')[1].split(',')
        if a[1] not in takes or a[0] != 'playing' or (a[1], a[2]) in seen: continue
        seen.add((a[1], a[2]))
        samples[a[1]].append(dict(time=float(a[2]), p=[float(v) for v in a[3:6]], f=[float(v) for v in a[6:9]],
                                  u=[float(v) for v in a[9:12]], v=[float(v) for v in a[12:15]], replay=float(a[15])))
    failures, offsets = [], {}
    for name, take in takes.items():
        ss = samples[name]
        def error(s, o):
            x, y, z, vx, vy, vz, fx, fy, fz, ux, uy, uz = take.at(s['replay']+o, ['x','y','z','vx','vy','vz','fx','fy','fz','ux','uy','uz'])
            p = s['p']
            return math.hypot(p[0]-x, p[2]-z), p[1]-y, max(angle(s['f'], [fx,fy,fz]), angle(s['u'], [ux,uy,uz])), math.dist(s['v'], [vx,vy,vz])
        def phase(t):
            if t < take.liftoff-3: return 'taxi out + roll'
            if t < take.liftoff+5: return 'liftoff (-3/+5 s)'
            if t < take.touchdown-5: return 'airborne'
            if t < take.touchdown+3: return 'touchdown (-5/+3 s)'
            return 'rollout + taxi in'
        flight = [s for s in ss if phase(s['replay']) == 'airborne']
        best = min((k*0.005 for k in range(-4, 13)), key=lambda o: statistics.mean(error(s, o)[0] for s in flight[::5]))
        offsets[name] = best
        print(f'\n{name}: {len(ss)} playing samples; liftoff {take.liftoff:.2f} s, touchdown {take.touchdown:.2f} s; fitted offset {best*1000:.0f} ms')
        for ph in ('taxi out + roll', 'liftoff (-3/+5 s)', 'airborne', 'touchdown (-5/+3 s)', 'rollout + taxi in'):
            sel = [s for s in ss if phase(s['replay']) == ph and s['replay']+best <= take.ts[-1]]
            if not sel: continue
            e = [error(s, best) for s in sel]
            vlim = LIMITS['velocity_air'] if ph in ('airborne', 'liftoff (-3/+5 s)', 'touchdown (-5/+3 s)') else LIMITS['velocity_ground']
            parts = []
            for label, k, lim in (('horiz', 0, LIMITS['horizontal']), ('vert', 1, LIMITS['vertical']), ('att', 2, LIMITS['attitude']), ('vel', 3, vlim)):
                v = sorted(abs(x[k]) for x in e)
                parts.append(f'{label} max {v[-1]:.3f} p95 {v[int(.95*(len(v)-1))]:.3f}')
                if v[-1] > lim: failures.append(f'{name} {ph} {label} {v[-1]:.3f} > {lim}')
            print(f'  {ph:20s} n={len(sel):5d} | ' + ' | '.join(parts))
    names = list(takes)
    for i, a in enumerate(names):
        for b in names[i+1:]:
            other = {s['time']: s for s in samples[b]}
            diffs, gaps = [], []
            for s in samples[a]:
                t = other.get(s['time'])
                if not t: continue
                played = math.dist(s['p'], t['p'])
                # Both takes at the replay time the sampled poses actually carry.
                recorded = math.dist(takes[a].at(s['replay']+offsets[a], ['x','y','z']), takes[b].at(t['replay']+offsets[b], ['x','y','z']))
                diffs.append(played-recorded); gaps.append(recorded)
            if diffs:
                v = sorted(abs(d) for d in diffs)
                print(f'\nSeparation {a} / {b}: {len(diffs)} shared samples; recorded spacing min {min(gaps):.2f} m; '
                      f'playback minus recording max {v[-1]:.3f} m p95 {v[int(.95*(len(v)-1))]:.3f} m (measured, not gated)')
    print('\nFAILURES:\n- ' + '\n- '.join(failures) if failures else '\nAll compared phases within the #28 limits.')


if __name__ == '__main__':
    main()
