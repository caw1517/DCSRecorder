"""Check recorded native engine values against independent Export/mission data."""
import argparse
import bisect
import csv
import json
import math
from pathlib import Path
from analyze import analyze

CHANNELS=['core1','fan1','thrust_e0_1','power_f0_1','core2','fan2','thrust_e0_2','power_f0_2']

def inspect(path):
    ordinary=analyze(path)
    takes=[];take=None
    for line in path.read_text(encoding='utf-8-sig',errors='replace').splitlines():
        if 'DCSENGINE_MISSION,1,BEGIN,' in line:
            take={'native':[],'mission':[],'export':{},'segments':{},'errors':[]};takes.append(take)
        if take is None:continue
        for kind in ('MISSION','EXPORT','NATIVE'):
            prefix=f'DCSENGINE_{kind},1,'
            if prefix not in line:continue
            row=next(csv.reader([line.split(prefix,1)[1]]))
            if row[0]=='DATA':
                if kind=='MISSION':
                    take['segments'][int(row[2])]=row[4]
                    take['mission'].append((float(row[3]),list(map(float,row[5:8]))))
                elif kind=='EXPORT':take['export'][int(row[2])]=row
                else:take['native'].append(row)
            elif kind=='NATIVE' and row[0] in ('ERROR','UNAVAILABLE'):take['errors'].append(row)
            elif kind=='NATIVE' and row[0]=='END':take['end']=row
    assert len(takes)==len(ordinary)
    results=[]
    for take,base in zip(takes,ordinary):
        rows=take['native'];issues=list(take['errors'])
        if not base['alignment_screen_passes']:issues.append('Export/mission alignment screen failed')
        if len(rows)!=base['rows']:issues.append('Native row count differs from mission')
        if take.get('end')!=['END',base['take'],'user_stop',str(base['rows'])]:issues.append('Native footer missing or mismatched')
        identities=set();rpm_errors=[];clock_deltas=[];positions=[];read_spans=[];ranges={}
        mission_times=[r[0]for r in take['mission']];residuals=[];last=None
        for i,row in enumerate(rows,1):
            if len(row)!=26 or row[11]!='OK':issues.append('Unavailable/malformed native row');continue
            if row[1]!=base['take'] or int(row[2])!=i:issues.append('Native take/sequence mismatch')
            values=list(map(float,row[15:23]));start,end=map(float,row[3:5]);position=list(map(float,row[6:9]))
            export_rpm=list(map(float,row[9:11]))
            if not all(math.isfinite(v)for v in [start,end,*position,*values,*export_rpm]):issues.append('Nonfinite values');continue
            if last is not None and not 0<start-last<=.15:issues.append('Native clock gap/reversal')
            last=start
            index=bisect.bisect_right(mission_times,start)-1
            if 0<=index<len(mission_times)-1:
                (ta,pa),(tb,pb)=take['mission'][index:index+2]
                weight=(start-ta)/(tb-ta)
                residuals.append(math.dist(position,[a+weight*(b-a)for a,b in zip(pa,pb)]))
            identities.add(tuple([row[5],*row[12:15],*row[23:26]]))
            read_spans.append(end-start)
            rpm_errors.extend(abs(values[j*4]-export_rpm[j]/100)for j in (0,1))
            other=take['export'].get(i)
            if other:
                clock_deltas.append(start-float(other[3]))
                positions.append(math.dist(position,list(map(float,other[7:10]))))
                if row[5]!=other[4]:issues.append('Native/Export player ID mismatch')
            else:issues.append('Missing independent Export sample')
            group=ranges.setdefault(take['segments'].get(i,'unknown'),{})
            for name,value in zip(CHANNELS,values):
                bounds=group.setdefault(name,[value,value]);bounds[0]=min(bounds[0],value);bounds[1]=max(bounds[1],value)
        if len(identities)!=1:issues.append('Native player/class/offset/thread/getter identity changed or missing')
        if not rpm_errors or max(rpm_errors)>1e-5:issues.append('Core RPM disagrees with same-sample Export RPM')
        if not read_spans or min(read_spans)<0 or max(read_spans)>.02:issues.append('Native read span outside screen')
        # These two GUI hooks sample on the same frame; unlike mission/Export IDs,
        # their Export IDs should agree. Flag timing differences rather than infer identity.
        if not clock_deltas or max(map(abs,clock_deltas))>.02:issues.append('Native/Export clock gap')
        if len(residuals)<max(2,len(rows)-2) or max(residuals,default=math.inf)>1:issues.append('Native/mission time-matched position screen failed')
        results.append({'take':base['take'],'rows':len(rows),'duration':float(rows[-1][3])-float(rows[0][3]) if rows else 0,
            'passes':not issues,'issues':issues,'identity':[list(v)for v in identities],
            'max_core_export_error':max(rpm_errors,default=None),'read_span_seconds':[min(read_spans),max(read_spans)]if read_spans else None,
            'max_independent_export_clock_delta':max(map(abs,clock_deltas),default=None),
            'max_independent_export_position_delta':max(positions,default=None),
            'time_matched_native_position_samples':len(residuals),
            'max_time_matched_native_position_error_m':max(residuals,default=None),
            'mission_export_alignment':base['alignment_screen_passes'],'segments':ranges})
    return results

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('log',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();results=inspect(args.log)
    args.output.write_text(json.dumps(results,indent=2),encoding='utf-8')
    for result in results:print(json.dumps(result,indent=2))
    raise SystemExit(0 if all(r['passes']for r in results)else 1)
