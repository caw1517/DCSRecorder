import csv,json,collections,re
from pathlib import Path
p=Path(__file__).resolve().parent
stats={}
first=[]
for r in csv.DictReader((p/'raw/ground-pose-26844.csv').open()):
    if None in r or any(v is None for v in r.values()):continue
    key=r['id']+'/'+r['phase']
    s=stats.setdefault(key,dict(count=0,first=r,last=None,y_error_min=1e9,y_error_max=-1e9,replay_max=0))
    e=float(r['precise_y'])-float(r['target_y'])
    s.update(count=s['count']+1,last=r,y_error_min=min(s['y_error_min'],e),y_error_max=max(s['y_error_max'],e),replay_max=max(s['replay_max'],float(r['replay_time'])))
    if r['phase']=='before_step' and (int(r['call'])<6 or abs(float(r['model_time'])-10)<.001):first.append(r)
events=[];samples={};contacts={}
for line in (p/'raw/dcs.log').open(errors='replace'):
    if 'DCSR_RELEASE ' not in line:continue
    a=line.split('DCSR_RELEASE ',1)[1].strip().split(',')
    if a[0]=='SAMPLE' and a[2]=='StagedPlayback':
        key=a[1];s=samples.setdefault(key,dict(count=0,first=a,last=None,y_min=1e9,y_max=-1e9))
        y=float(a[5]);s.update(count=s['count']+1,last=a,y_min=min(s['y_min'],y),y_max=max(s['y_max'],y))
    elif a[0]=='CONTACT' and a[2]=='StagedPlayback': contacts[a[1]]=a
    elif a[0] in ['READY','INSPECTION_COMPLETE','FAILED','RELEASED']:events.append(line.strip())
out=dict(trace=stats,early=first,samples=samples,contacts=contacts,events=events)
(p/'summary.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
