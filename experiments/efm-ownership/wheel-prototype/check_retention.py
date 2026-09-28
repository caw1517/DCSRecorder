"""Compare SDK writes with later mission reads on the playback elapsed clock."""
import argparse
import bisect
import csv
import json
import math
from pathlib import Path

CHANNELS=[0,5,3,1,6,4,101,103,102,2]


def analyze(trace,log):
    summary={str(c):dict(native_rows=0,immediate_max_error=0,between_calls_max_error=0,
        mission_rows=0,mission_mismatches=0,mission_max_error=0,first_mismatch=None) for c in CHANNELS}
    groups={};identity=None;last_call=0;last_time=-1
    with trace.open()as stream:
        for row in csv.DictReader(stream):
            c=int(row['arg']);call=int(row['call']);t=float(row['elapsed'])
            assert c in CHANNELS and call in (last_call,last_call+1) and t>=last_time
            if identity is None:identity=row['id']
            assert row['id']==identity,'Separate objects before analysis'
            last_call=call;last_time=t
            values=[float(row[k]) for k in ('requested','before','after')]
            assert all(map(math.isfinite,[t,*values]))
            requested,before,after=values;s=summary[str(c)];s['native_rows']+=1
            s['immediate_max_error']=max(s['immediate_max_error'],abs(after-requested))
            if row['previous_requested']:
                s['between_calls_max_error']=max(s['between_calls_max_error'],abs(before-float(row['previous_requested'])))
            group=groups.setdefault(t,{})
            assert c not in group,'Duplicate channel/time'
            group[c]=requested
    assert groups and all(set(g)==set(CHANNELS) for g in groups.values())
    times=sorted(groups);count=0;max_rounding=0;begins=0;complete=False
    for line in log.read_text(errors='replace').splitlines():
        if 'DCSWHEEL_PLAYBACK,BEGIN,' in line:begins+=1
        if 'DCSWHEEL_PLAYBACK,END,' in line:
            assert line.endswith('DCSWHEEL_PLAYBACK,END,complete'),'Incomplete playback'
            assert not complete;complete=True
        if 'DCSWHEEL_PLAYBACK,DATA,' not in line:continue
        assert not complete
        fields=line.split('DCSWHEEL_PLAYBACK,DATA,',1)[1].split(',')
        elapsed=float(fields[1]);values=list(map(float,fields[3:]))
        assert len(values)==len(CHANNELS) and all(map(math.isfinite,[elapsed,*values]))
        index=bisect.bisect_left(times,elapsed)
        nearest=min(times[max(0,index-1):index+1],key=lambda t:abs(t-elapsed))
        rounding=abs(nearest-elapsed);assert rounding<.0001,'Mission clock does not match an SDK sample'
        max_rounding=max(max_rounding,rounding);count+=1
        for c,value in zip(CHANNELS,values):
            s=summary[str(c)];s['mission_rows']+=1
            error=abs(value-groups[nearest][c]);s['mission_max_error']=max(s['mission_max_error'],error)
            if error>1e-5:
                s['mission_mismatches']+=1
                if s['first_mismatch'] is None:s['first_mismatch']=dict(elapsed=elapsed,phase=fields[2],requested=groups[nearest][c],observed=value)
    assert begins==1 and complete and count>0
    assert all(s['immediate_max_error']<=1e-5 for s in summary.values()),'Immediate SDK write mismatch'
    return dict(object_id=identity,native_calls=len(groups),mission_samples=count,elapsed_end=times[-1],
        max_elapsed_rounding=max_rounding,channels=summary)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('trace',type=Path);parser.add_argument('log',type=Path)
    parser.add_argument('output',type=Path);parser.add_argument('--assert-wheels',action='store_true')
    args=parser.parse_args();result=analyze(args.trace,args.log)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    failed=[c for c in CHANNELS if result['channels'][str(c)]['mission_max_error']>1e-5]
    print(f"{result['native_calls']} SDK calls; {result['mission_samples']} later reads; wheels mismatches: {failed}")
    if args.assert_wheels and failed:raise SystemExit('FAIL: wheels values changed after SDK write: '+str(failed))
