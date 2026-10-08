"""Per-manoeuvre check of a replay against the agreed #28 limits (envelope ticket #7).

Usage: python analyze_envelope.py <run folder> <source csv> <windows json>
Runs analyze_run.py for the shared parsing and error model, then reports each
named replay-time window. The post-liftoff exclusion (#37) is reported separately.
"""
import contextlib, io, json, math, runpy, sys
from pathlib import Path

run, source, windows = sys.argv[1], sys.argv[2], json.loads(Path(sys.argv[3]).read_text())
sys.argv = ['analyze_run.py', run, source]
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(str(Path(__file__).parent / 'analyze_run.py'))
samples, pose_error, best, at, ts, L = g['samples'], g['pose_error'], g['best'], g['at'], g['ts'], g['LIMITS']
EXCLUDED = (67.1, 74.2)  # post-liftoff drift window, known exception (#37); replay times carry float error, so allow half a tick
playing = [s for s in samples if s['phase'] == 'playing' and s['replay'] + best <= ts[-1]]

def report(name, lo, hi, exclude=False):
    sel = [s for s in playing if lo <= s['replay'] < hi and not (exclude and EXCLUDED[0] - 0.005 <= s["replay"] < EXCLUDED[1])]
    if not sel: return
    e = [pose_error(s, best) for s in sel]
    m = [max(abs(x[k]) for x in e) for k in range(4)]
    lim = [L['horizontal'], L['vertical'], L['attitude'], L['velocity_air']]
    worst = max(sel, key=lambda s: pose_error(s, best)[0])['replay']
    verdict = 'PASS' if all(a <= b for a, b in zip(m, lim)) else 'FAIL'
    print(f'  {name:34s} {lo:7.1f}-{hi:7.1f} s n={len(sel):6d} | horiz {m[0]:.3f} (at {worst:.1f}) vert {m[1]:.3f} att {m[2]:.3f} vel {m[3]:.3f} | {verdict}')

print(f'{Path(run).name}: offset {best*1000:.0f} ms; limits horiz {L["horizontal"]} vert {L["vertical"]} att {L["attitude"]} vel {L["velocity_air"]}')
for w in windows:
    report(w['name'], w['from'], w['to'], w.get('exclude', False))
