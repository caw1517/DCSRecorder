"""Summarize measured canopy responses per applied phase, without inferring rendering."""
import argparse
import json
import math
from pathlib import Path


def analyze(path):
    channels=None
    phases={}
    requests={}
    rows=[]
    start=end=None
    for line in path.read_text(errors='replace').splitlines():
        if 'DCSCANOPY,1,' not in line:continue
        row=line.split('DCSCANOPY,1,',1)[1].split(',')
        event=row[0]
        if event=='BEGIN':
            assert start is None,'Separate mission sessions before analysis'
            start=float(row[1]);assert row[3]=='FA-18C_hornet'
        elif event=='CHANNELS':
            channels=list(map(int,row[1:]));assert channels==[38]
        elif event=='REQUEST':
            phase=int(row[1]);assert phase==len(requests)+1
            requests[phase]=float(row[2])
        elif event=='APPLIED':
            phase=int(row[1]);t=float(row[2]);assert phase==len(phases)+1
            assert 0<=t-requests[phase]<=3
            phases[phase]=dict(name=row[3],time=t,request_delay=t-requests[phase])
        elif event=='DATA':
            assert end is None and channels and int(row[1])==len(rows)+1,'Missing/out-of-order sample'
            t=float(row[2]);phase=int(row[3]);values=list(map(float,row[4:]))
            assert len(values)==len(channels) and all(map(math.isfinite,[t,*values]))
            assert phase==len(phases),'Sample phase disagrees with applied phase'
            if rows:assert 0<t-rows[-1][0]<.101,'Sample clock gap'
            rows.append((t,phase,values))
        elif event=='END':
            assert end is None and row[1]=='complete','Incomplete diagnostic: '+row[1]
            assert int(row[2])==len(rows),'END count mismatch'
            end=float(row[3])
    assert start is not None and end is not None and len(phases)==10 and len(rows)>2000,'Missing capture/phases'
    output=dict(samples=len(rows),duration=end-start,max_gap=max(b[0]-a[0]for a,b in zip(rows,rows[1:])),phases={})
    for phase,metadata in phases.items():
        selected=[v for t,p,v in rows if p==phase and t>=metadata['time']+.5]
        assert selected,'No settled samples for phase'
        observations={}
        for i,channel in enumerate(channels):
            values=[v[i]for v in selected]
            observations[str(channel)]=dict(min=min(values),max=max(values),mean=sum(values)/len(values),
                changes=sum(a!=b for a,b in zip(values,values[1:])))
        output['phases'][phase]={**metadata,'settled_samples':len(selected),'arguments':observations}
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('log',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();result=analyze(args.log)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(f'PASS: {result["samples"]} samples, {len(result["phases"])} phases, maximum gap {result["max_gap"]:.6f}s; measured ranges saved to {args.output}')
