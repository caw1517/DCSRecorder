import importlib.util
import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
root=Path(__file__).parent
repo=root.parents[4]
spec=importlib.util.spec_from_file_location('probe',repo/'companion/mission-identity-probe.prototype.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)

def diff(a,b,path=''):
    if isinstance(a,dict) and isinstance(b,dict):
        for k in sorted(set(a)|set(b),key=str):
            if k not in a or k not in b: yield path+'/'+str(k)
            else: yield from diff(a[k],b[k],path+'/'+str(k))
    elif a!=b: yield path

def inspect(name):
    p=root/(name+'.miz')
    if not p.exists(): p=root.parent/(name+'.miz')
    s=probe.snapshot(p)
    _,m=probe.read(p)
    s['group_order']=[g['groupId'] for _,g in sorted(m['coalition']['blue']['country'][1]['plane']['group'].items())]
    return s

pairs=[('09-editor-reopened','13-editor-copy'),('10-controlled-four-input','14-controlled-four-saved'),
       ('11-controlled-seven-input','15-controlled-seven-saved'),('14-controlled-four-saved','15-controlled-seven-saved'),
       ('12-reordered-seven-input','16-reordered-seven-saved'),('15-controlled-seven-saved','16-reordered-seven-saved')]
report=[]
for a,b in pairs:
    try: old,new=inspect(a),inspect(b)
    except FileNotFoundError: continue
    au={u['unit']['unitId']:u for u in old['aircraft']};bu={u['unit']['unitId']:u for u in new['aircraft']}
    report.append({'before':a,'after':b,'before_hash':old['archive_sha256'],'after_hash':new['archive_sha256'],
                  'before_group_order':old['group_order'],'after_group_order':new['group_order'],
                  'added_ids':sorted(bu.keys()-au.keys()),'removed_ids':sorted(au.keys()-bu.keys()),
                  'common_aircraft_changed_paths':{str(k):list(diff(au[k],bu[k])) for k in au.keys()&bu.keys() if au[k]!=bu[k]},
                  'inventory_equal':au==bu})
(repo/'companion/mission-identity-remaining-observations.prototype.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
