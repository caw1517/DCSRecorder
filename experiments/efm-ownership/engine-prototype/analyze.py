"""Summarize measured engine channels without inferring afterburner from RPM.

Log delivery pairs observations, not sample instants. Report the actual clocks,
IDs and positional separation before deciding whether streams can be integrated.
"""
import argparse
import csv
import json
import math
from pathlib import Path

ENGINE = ['rpm_left','rpm_right','temperature_left','temperature_right','fuel_flow_left','fuel_flow_right']


def analyze(path):
    takes=[]
    current=None
    for line in Path(path).read_text(encoding='utf-8-sig',errors='replace').splitlines():
        for kind in ('MISSION','EXPORT'):
            prefix=f'DCSENGINE_{kind},1,'
            if prefix not in line:
                continue
            row=next(csv.reader([line.split(prefix,1)[1]]))
            event=row[0]
            if kind=='MISSION' and event=='BEGIN':
                current={'take':row[1],'mission_id':int(row[3]),'mission':[], 'export':{},'issues':[], 'marks':[]}
                takes.append(current)
            if current is None or event=='READY':
                continue
            if row[1]!=current['take']:
                if event=='ERROR': current['issues'].append(','.join(row))
                continue
            if kind=='MISSION' and event=='CHANNELS':
                current['channels']=list(map(int,row[2:]))
            elif kind=='MISSION' and event=='MARK':
                current['marks'].append({'time':float(row[2]),'segment':row[3]})
            elif event in ('ERROR','UNAVAILABLE'):
                current['issues'].append(','.join(row))
            elif event=='DATA':
                seq=int(row[2])
                if kind=='MISSION':
                    if seq!=len(current['mission'])+1: raise ValueError('Mission sequence gap/duplicate')
                    if len(row)!=8+len(current['channels']): raise ValueError('Mission row width')
                    current['mission'].append({'seq':seq,'t':float(row[3]),'segment':row[4],
                        'position':list(map(float,row[5:8])),'args':list(map(float,row[8:]))})
                else:
                    if seq in current['export']: raise ValueError('Duplicate Export row')
                    if len(row)!=17: raise ValueError('Export row width')
                    current['export'][seq]={'t':float(row[3]),'id':int(row[4]),'type':row[5],'name':row[6],
                        'position':list(map(float,row[7:10])),'engine':list(map(float,row[10:16])),'end':float(row[16])}
            elif event=='END':
                current[kind.lower()+'_end']={'reason':row[2],'rows':int(row[3])}
    if not takes: raise ValueError('No engine diagnostic takes')
    results=[]
    for take in takes:
        rows=take['mission'];exports=take['export']
        if not rows: raise ValueError('No mission samples')
        complete=all(take.get(kind+'_end')=={'reason':'user_stop','rows':len(rows)} for kind in ('mission','export'))
        issues=take['issues'][:]
        if not complete: issues.append('Missing/non-user-stop/count-mismatched footer')
        if set(exports)!=set(range(1,len(rows)+1)): issues.append('Missing or extra Export samples')
        delays=[];spans=[];separations=[];ids=set();groups={}
        previous=None
        for row in rows:
            if previous is not None and row['t']<=previous: raise ValueError('Non-monotonic mission clock')
            previous=row['t']
            if not all(math.isfinite(v) for v in [row['t'],*row['position'],*row['args']]): raise ValueError('Nonfinite mission sample')
            obs=exports.get(row['seq'])
            if obs is None: continue
            if obs['type']!='FA-18C_hornet' or obs['name']!='Observer': issues.append('Ownship identity mismatch')
            values=[obs['t'],obs['end'],*obs['engine'],*obs['position']]
            if not all(math.isfinite(v) for v in values): raise ValueError('Nonfinite Export sample')
            ids.add(obs['id']);delays.append(obs['t']-row['t']);spans.append(obs['end']-obs['t'])
            separations.append(math.dist(row['position'],obs['position']))
            group=groups.setdefault(row['segment'],{})
            for name,value in zip([f'arg_{i}' for i in take['channels']]+ENGINE,row['args']+obs['engine']):
                bounds=group.setdefault(name,[value,value]);bounds[0]=min(bounds[0],value);bounds[1]=max(bounds[1],value)
        # These are screening bounds for this diagnostic, not product guarantees.
        timely=bool(delays) and min(delays)>=-0.02 and max(delays)<=0.1 and min(spans)>=0 and max(spans)<=0.02
        identity=ids=={take['mission_id']}
        results.append({'take':take['take'],'rows':len(rows),'export_rows':len(exports),
            'duration':rows[-1]['t']-rows[0]['t'],'issues':issues,'complete':complete,
            'mission_id':take['mission_id'],'export_ids':sorted(ids),'same_numeric_id':identity,
            'export_minus_mission_seconds':[min(delays),max(delays)] if delays else None,
            'export_read_span_seconds':[min(spans),max(spans)] if spans else None,
            'max_position_separation_m':max(separations) if separations else None,
            'alignment_screen_passes':complete and not issues and timely and identity,
            'markers':take['marks'],'segments':groups})
    return results


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('log',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    results=analyze(args.log)
    args.output.write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
    for result in results:
        print({k:v for k,v in result.items() if k not in ('segments','markers')})
    raise SystemExit(0 if all(r['alignment_screen_passes'] for r in results) else 1)
