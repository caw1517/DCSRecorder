"""Compare captured controller poses with the DCS mission API at matching times.

This detects the observed API/controller discrepancy, not rendered pixels.
One degree is a diagnostic threshold, not a product fidelity specification.
"""
import csv
import argparse
import math
import sys
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('root',nargs='?',type=Path,default=Path(__file__).resolve().parent)
parser.add_argument('--native-file',default='native-motion-15596.csv')
parser.add_argument('--mission-log',default='dcs.log')
args=parser.parse_args()
root=args.root

def angle(a,b):
    cosine=sum(x*y for x,y in zip(a,b))/math.sqrt(sum(x*x for x in a)*sum(x*x for x in b))
    return math.degrees(math.acos(max(-1,min(1,cosine))))

native=[]
for r in csv.DictReader((root/args.native_file).open()):
    if r['status']=='captured':
        native.append([])
    elif r['status']=='called':
        native[-1].append((float(r['object_time']), [float(r[f'command{i}']) for i in (0,1,2)],
                           [float(r[f'command{i}']) for i in (12,13,14)]))
mission=[]
for line in (root/args.mission_log).read_text(errors='replace').splitlines():
    if 'DCS_PLAYBACK_SAMPLE,playing,StagedPlayback,' not in line:
        continue
    v=line.split('DCS_PLAYBACK_SAMPLE,',1)[1].split(',')
    t=float(v[2])
    if not mission or t<=mission[-1][-1][0]:
        mission.append([])
    mission[-1].append((t,list(map(float,v[6:9])),list(map(float,v[3:6]))))
assert len(native)==len(mission), 'Run correspondence needs investigation'
failed=False
for i,(commands,samples) in enumerate(zip(native,mission),1):
    lookup={round(p[0],2):n for n,p in enumerate(commands)}
    measurements=[]
    for t,forward,position in samples:
        n=lookup.get(round(t,2))
        if n is None or t-commands[0][0]<.2:
            continue
        command=commands[n]
        # Allow either adjacent controller tick; callback order cannot explain
        # an error that survives this conservative +/-20 ms allowance.
        near=commands[max(0,n-1):n+2]
        error=min(angle(forward,p[1]) for p in near)
        measurements.append((error,t-commands[0][0],math.dist(position,command[2])))
    assert measurements, 'No aligned samples'
    peak=max(measurements)
    failed |= peak[0]>1
    print(f"{'FAIL' if peak[0]>1 else 'PASS'} run {i}: nose discrepancy {peak[0]:.4f} deg "
          f"at {peak[1]:.3f}s, aligned position difference {peak[2]:.4f}m; +/-20ms allowed")
sys.exit(1 if failed else 0)
