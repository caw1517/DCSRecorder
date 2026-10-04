"""Playback vs source pose around contact transitions (lead SAMPLE rows)."""
import bisect, math, sys
from pathlib import Path
HERE = Path(__file__).parent
run = HERE / (sys.argv[1] if len(sys.argv) > 1 else 'live-1')
lines = (HERE/'source/20261004T200936Z-0001.csv').read_text(encoding='utf-8').splitlines()
h = next(i for i, l in enumerate(lines) if l.startswith('t,x,'))
cols = lines[h].split(',')
src = []
for l in lines[h+1:]:
    if l.startswith('END'): break
    f = dict(zip(cols, l.split(',')))
    src.append([float(f[k]) for k in ('t','x','y','z','vx','vy','vz','in_air','terrain_height')])
t0 = src[0][0]; ts = [r[0]-t0 for r in src]
def at(t):
    i = max(1, min(len(ts)-1, bisect.bisect_left(ts, t))); a, b = src[i-1], src[i]
    w = (t-ts[i-1])/(ts[i]-ts[i-1]); return [a[k]+(b[k]-a[k])*w for k in range(len(a))], int(a[7])
rows = []
for l in (run/'dcs-playback.log').read_text(encoding='utf-8', errors='replace').splitlines():
    if ' SAMPLE,' not in l or 'Lead' not in l: continue
    a = l.split(' SAMPLE,')[1].split(',')
    if a[0] != 'playing': continue
    replay = float(a[15]); rows.append((replay, [float(v) for v in a[3:6]], [float(v) for v in a[12:15]], float(a[16])))
print(run.name, 'running lead samples', len(rows), 'replay %.2f..%.2f' % (rows[0][0], rows[-1][0]))
lo, hi = (float(sys.argv[2]), float(sys.argv[3])) if len(sys.argv) > 3 else (28, 40)
worst = (0, None)
for replay, p, v, status in rows:
    s, air = at(replay); dy = p[1]-s[2]; dh = math.hypot(p[0]-s[1], p[2]-s[3])
    if abs(dy) > abs(worst[0]): worst = (dy, replay)
    if lo <= replay <= hi:
        print('replay %7.3f air %d dy %+8.3f dh %7.3f  vy play %+7.2f src %+7.2f  agl src %.2f' % (replay, air, dy, dh, v[1], s[5], s[2]-s[8]))
print('worst vertical error %+.3f m at replay %.3f' % worst)
