"""Compare isolated read-only native telemetry with mission-side observations."""
import argparse
import bisect
from collections import Counter
import hashlib
import json
import math
from pathlib import Path


def analyze(native,mission):
    rows=[json.loads(line) for line in native.read_text().splitlines()]
    status=Counter(row['status'] for row in rows)
    samples=[row for row in rows if row['status']=='read']
    times=[row['time'] for row in samples]
    if not samples or times!=sorted(set(times)):raise ValueError('Missing samples or ambiguous multiple runs')
    lines=mission.read_text().splitlines()
    observed=[]
    for line in lines:
        if 'DCSR_LAYOUT,SAMPLE,' not in line:continue
        fields=line.split('DCSR_LAYOUT,SAMPLE,',1)[1].split(',')
        observed.append(dict(time=float(fields[0]),id=int(fields[1]),
                             position=list(map(float,fields[2:5])),velocity=list(map(float,fields[5:8]))))
    def errors(shift):
        pe=[];ve=[]
        for row in observed:
            t=row['time']+shift;i=bisect.bisect_right(times,t)-1
            if i<0 or i+1>=len(samples):continue
            a,b=samples[i:i+2];fraction=(t-a['time'])/(b['time']-a['time'])
            for key,out in (('position',pe),('velocity',ve)):
                value=[x+(y-x)*fraction for x,y in zip(a[key],b[key])]
                out.append(math.dist(row[key],value))
        if not pe:raise ValueError('No overlapping observations')
        return dict(count=len(pe),position_rms_m=math.sqrt(sum(v*v for v in pe)/len(pe)),
                    position_max_m=max(pe),velocity_max_mps=max(ve))
    shifts=[(k/1000,errors(k/1000)) for k in range(-40,41)]
    shift,best=min(shifts,key=lambda item:item[1]['position_rms_m'])
    return dict(status='Read-only field comparison; native setters and hooks remain untested',
        statuses=dict(status),native_samples=len(samples),mission_samples=len(observed),
        completed=sum('DCSR_LAYOUT,COMPLETE' in line for line in lines)==1,
        native_ids=sorted({r['id'] for r in samples}),mission_ids=sorted({r['id'] for r in observed}),
        all_null_fm=all(not r['fm_present'] for r in samples),engine_counts=sorted({r['engine_count'] for r in samples}),
        raw_clock_comparison=errors(0),best_observed_phase_offset_seconds=shift,phase_aligned_comparison=best,
        position_representation_max_m=max(math.dist(r['position'],r['coarse_position']) for r in samples),
        pitch_range=[min(r['pitch'] for r in samples),max(r['pitch'] for r in samples)],
        pitch_rate_range=[min(r['pitch_rate'] for r in samples),max(r['pitch_rate'] for r in samples)],
        sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (native,mission)})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('native',type=Path);p.add_argument('mission',type=Path);p.add_argument('report',type=Path)
    a=p.parse_args();report=analyze(a.native,a.mission)
    a.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
