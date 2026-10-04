import csv, hashlib, json, math, re
from pathlib import Path
root=Path(__file__).resolve().parent
source=root/'raw/source-recording.csv'
lines=source.read_text().splitlines()
header=next(i for i,l in enumerate(lines) if l.startswith('t,x,'))
rows=list(csv.DictReader(lines[header:-1]))
assert lines[-1]==f'END,user_stop,{len(rows)}'
log=(root/'raw/dcs.log').read_text(encoding='utf-8',errors='replace')
runs=[]
for line in log.splitlines():
    if 'DCSGROUND,1,' not in line:continue
    s=line.split('DCSGROUND,1,',1)[1]
    if s.startswith('BEGIN,'):runs.append(dict(begin=s,rows=[],end=None,errors=[]))
    if not runs:continue
    if s.startswith('DATA,'):runs[-1]['rows'].append(s.split(','))
    if s.startswith('END,'):runs[-1]['end']=s
    if s.startswith('ERROR,'):runs[-1]['errors'].append(s)
run=runs[-1]
assert not run['errors'] and len(run['rows'])==len(rows)
assert run['end']==f'END,1,{len(rows)},stopped'
contacts=[]
for i,(r,g) in enumerate(zip(rows,run['rows']),1):
    assert int(g[2])==i and float(g[3])==float(r['t'])
    contacts.append(dict(zip(['unit_id','in_air','terrain_height','origin_agl','life','life0','surface_type'],map(float,g[4:]))))
    assert contacts[-1]['unit_id']==1 and contacts[-1]['in_air']==0 and contacts[-1]['life']==contacts[-1]['life0']==20
    assert all(math.isfinite(v) for v in contacts[-1].values())
speed=[math.sqrt(sum(float(r[k])**2 for k in ['vx','vy','vz'])) for r in rows]
pos=[[float(r[k]) for k in ['x','y','z']] for r in rows]
times=[float(r['t']) for r in rows];start=times[0]
def rangeof(key):return [min(float(r[key]) for r in rows),max(float(r[key]) for r in rows)]
moving=[i for i,v in enumerate(speed) if v>.1]
summary=dict(source=source.name,sha256=hashlib.sha256(source.read_bytes()).hexdigest(),samples=len(rows),duration=times[-1]-start,
    contact_rows=len(contacts),contact_alignment='Exact sample number and source timestamp',all_samples_grounded=True,life=[20,20],
    initial_position=pos[0],initial_velocity=[float(rows[0][k]) for k in ['vx','vy','vz']],
    speed_mps=dict(initial=speed[0],max=max(speed),final=speed[-1]),path_length_m=sum(math.dist(a,b) for a,b in zip(pos,pos[1:])),
    displacement_m=math.dist(pos[0],pos[-1]),first_above_point_one_mps_at=times[moving[0]]-start if moving else None,
    last_above_point_one_mps_at=times[moving[-1]]-start if moving else None,
    origin_agl_m=[min(r['origin_agl'] for r in contacts),max(r['origin_agl'] for r in contacts)],
    gear={k:rangeof(k) for k in ['arg_0','arg_3','arg_5']},engines={k:rangeof(k) for k in ['engine_core_left','engine_core_right']},
    max_sample_gap=max(b-a for a,b in zip(times,times[1:])),
    status='Complete real ground source, paired contact/health evidence; playback remains unverified')
(root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
(root/'contact.json').write_text(json.dumps(dict(begin=run['begin'],end=run['end'],rows=[dict(t=float(r['t']),**g) for r,g in zip(rows,contacts)]),indent=2)+'\n')
print(json.dumps(summary,indent=2))
