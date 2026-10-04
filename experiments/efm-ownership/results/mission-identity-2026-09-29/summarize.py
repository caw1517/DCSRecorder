"""Local observed-data comparison; no simulator behavior is mocked."""
import json
from pathlib import Path
root = Path(__file__).parent

def snapshot(stem):
    data=json.loads((root/(stem+'.json')).read_text(encoding='utf-8'))
    return data['snapshots'][-1] if 'snapshots' in data else data

def differences(a,b,path=''):
    if isinstance(a,dict) and isinstance(b,dict):
        for key in sorted(set(a)|set(b)):
            if key not in a or key not in b:
                yield {'path':path+'/'+key,'before':a.get(key),'after':b.get(key)}
            else:
                yield from differences(a[key],b[key],path+'/'+key)
    elif a != b:
        yield {'path':path,'before':a,'after':b}

stems=['02-editor-input','03-editor-save-as','04-editor-resave','05-editor-rename','06-editor-seven-aircraft','07-editor-deleted','08-editor-recreated','09-editor-reopened']
observed=[(name,snapshot(name)) for name in stems if (root/(name+'.json')).exists()]
report={'evidence':'Actual saved archive comparisons; no recording/playback association implementation tested.','snapshots':[],'transitions':[]}
for name,s in observed:
    report['snapshots'].append({'name':name,'sha256':s['archive_sha256'],'mission_table_sha256':s['mission_table_sha256'],'count':len(s['aircraft']),
        'identifiers':[{'unit_id':u['unit']['unitId'],'unit_name':u['unit']['name'],'group_id':u['group_id'],'group_name':u['group_name']} for u in s['aircraft']],
        'custom_root_field':'dcsrecorder_probe_lineage' in s['top_level_keys'],
        'custom_unit_fields':any('dcsrecorder_probe_uuid' in u['unit'] for u in s['aircraft']),
        'root_archive_marker':'dcsrecorder-probe.json' in s['entries_sha256'],
        'nested_archive_marker':'DCSRecorderProbe/identity.json' in s['entries_sha256']})
for (oldname,a),(newname,b) in zip(observed,observed[1:]):
    au={u['unit']['unitId']:u for u in a['aircraft']};bu={u['unit']['unitId']:u for u in b['aircraft']}
    report['transitions'].append({'before':oldname,'after':newname,'added':sorted(bu.keys()-au.keys()),'removed':sorted(au.keys()-bu.keys()),
        'common_aircraft_changes':{str(k):list(differences(au[k],bu[k])) for k in au.keys()&bu.keys() if au[k]!=bu[k]},
        'changed_archive_entries':[k for k in sorted(set(a['entries_sha256'])|set(b['entries_sha256'])) if a['entries_sha256'].get(k)!=b['entries_sha256'].get(k)]})
(root/'live-summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report['transitions'],indent=2))
