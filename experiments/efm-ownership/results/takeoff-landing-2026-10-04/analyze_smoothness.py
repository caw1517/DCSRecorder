"""Per-step smoothness of the rendered pose (after_animation) by phase."""
import csv, math, sys, statistics
from pathlib import Path
run = Path(__file__).parent / sys.argv[1]
f = next(run.glob('ground-pose-*.csv'))
rows = [r for r in csv.DictReader(open(f)) if r['phase'] == 'after_animation']
pts = [(float(r['replay_time']), [float(r[k]) for k in ('precise_x','precise_y','precise_z')], [float(r[k]) for k in ('target_x','target_y','target_z')]) for r in rows]
# collapse duplicate replay times (same step traced twice)
seen = {}; 
for t, p, g in pts: seen[round(t, 3)] = (p, g)
ts = sorted(seen)
print(run.name, 'rendered steps', len(ts), 'replay %.2f..%.2f' % (ts[0], ts[-1]))
phases = [('taxi before takeoff', 2, 30), ('takeoff roll+climb', 30, 40), ('flight', 60, 200), ('final approach', 210, 220.1), ('touchdown+rollout', 220.1, 235), ('rollout/taxi', 235, 260)]
for name, a, b in phases:
    sel = [t for t in ts if a <= t < b]
    if len(sel) < 5: continue
    err = [math.dist(seen[t][0], seen[t][1]) for t in sel]
    dy = [seen[t][0][1] - seen[t][1][1] for t in sel]
    # jerkiness: second difference of rendered position vs target's second difference
    j = []
    for i in range(1, len(sel)-1):
        t0, t1, t2 = sel[i-1], sel[i], sel[i+1]
        if abs((t2-t1)-(t1-t0)) > 1e-6 or t2-t1 > .03: continue
        acc_r = [seen[t2][0][k]-2*seen[t1][0][k]+seen[t0][0][k] for k in range(3)]
        acc_g = [seen[t2][1][k]-2*seen[t1][1][k]+seen[t0][1][k] for k in range(3)]
        j.append(math.dist(acc_r, acc_g))
    print('%-22s err mean %.3f max %.3f | dy mean %+.3f min %+.3f max %+.3f | 2nd-diff excess p50 %.4f p95 %.4f max %.4f m' % (
        name, statistics.mean(err), max(err), statistics.mean(dy), min(dy), max(dy),
        statistics.median(j), sorted(j)[int(.95*len(j))], max(j)))
