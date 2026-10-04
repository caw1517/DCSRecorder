"""Check real DCS boundary evidence; this cannot be replaced by a mock pass."""
import csv,sys
from pathlib import Path
rows=0;last=-1.;sessions=0;worst=0.;max_time=0.;offenders=0
for r in csv.DictReader(Path(sys.argv[1]).open()):
    if None in r or any(v is None for v in r.values()):continue
    if r['phase']!='after_step' or float(r['replay_time'])!=0:continue
    t=float(r['model_time'])
    if t<last:sessions+=1
    last=t
    if t<.1:continue # initial native substeps precede the first advancing SDK tick
    max_time=max(max_time,t);rows+=1
    err=max(abs(float(r['precise_'+axis])-float(r['target_'+axis])) for axis in 'xyz')
    worst=max(worst,err)
    if r['readable']!='1' or err>1e-5:offenders+=1
passed=rows>0 and max_time>=30 and offenders==0
print(f'{"PASS" if passed else "FAIL"}: {rows} held post-step samples, {sessions+1} sessions; max position error {worst:.9f} m; {offenders} outside 0.00001 m; covered {max_time:.2f} s')
sys.exit(0 if passed else 1)
