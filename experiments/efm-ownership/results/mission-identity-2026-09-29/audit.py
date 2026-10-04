"""Summarize locally observed archives without publishing mission contents."""
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
repo = Path(__file__).resolve().parents[4]
root = Path(__file__).parent
spec = importlib.util.spec_from_file_location('probe', repo / 'companion/mission-identity-probe.prototype.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

def changes(a, b, path=''):
    if isinstance(a, dict) and isinstance(b, dict):
        for key in sorted(set(a) | set(b), key=str):
            sub = path + '/' + str(key)
            if key not in a or key not in b:
                yield sub
            else:
                yield from changes(a[key], b[key], sub)
    elif a != b:
        yield path

stems = ['02-editor-input', '03-editor-save-as', '04-editor-resave', '05-editor-rename',
         '06-editor-seven-aircraft', '07-editor-deleted', '08-editor-recreated', '09-editor-reopened']
snapshots = [probe.snapshot(root / (s + '.miz')) for s in stems]
missions = [probe.read(root / (s + '.miz'))[1] for s in stems]
report = {'build': '2.9.29.27468', 'date_local': '2026-09-29',
          'scope': 'Observed scratch Mission Editor archive saves; airborne stock Hornets. No flight, recording, playback, or runtime-verifier validation.',
          'snapshots': [], 'transitions': []}
for stem, s in zip(stems, snapshots):
    report['snapshots'].append({
        'name': stem, 'archive_sha256': s['archive_sha256'],
        'mission_table_sha256': s['mission_table_sha256'],
        'aircraft_inventory_sha256': s['aircraft_inventory_sha256'],
        'aircraft': [{'unit_id': u['unit']['unitId'], 'unit_name': u['unit']['name'],
                      'group_id': u['group_id'], 'group_name': u['group_name']} for u in s['aircraft']],
        'custom_root_field': 'dcsrecorder_probe_lineage' in s['top_level_keys'],
        'custom_unit_fields': any('dcsrecorder_probe_uuid' in u['unit'] for u in s['aircraft']),
        'root_archive_marker': 'dcsrecorder-probe.json' in s['entries_sha256'],
        'nested_archive_marker': 'DCSRecorderProbe/identity.json' in s['entries_sha256']})
for i in range(1, len(stems)):
    a, b = snapshots[i-1:i+1]
    au = {u['unit']['unitId']: u for u in a['aircraft']}
    bu = {u['unit']['unitId']: u for u in b['aircraft']}
    report['transitions'].append({
        'before': stems[i-1], 'after': stems[i],
        'added_ids': sorted(bu.keys()-au.keys()), 'removed_ids': sorted(au.keys()-bu.keys()),
        'common_aircraft_changed_paths': {str(k): list(changes(au[k], bu[k])) for k in au.keys() & bu.keys() if au[k] != bu[k]},
        'mission_changed_paths': list(changes(missions[i-1], missions[i])),
        'changed_archive_entries': [k for k in sorted(set(a['entries_sha256']) | set(b['entries_sha256']))
                                    if a['entries_sha256'].get(k) != b['entries_sha256'].get(k)]})
before = next(u for u in snapshots[4]['aircraft'] if u['unit']['unitId'] == 10117)
after = next(u for u in snapshots[6]['aircraft'] if u['unit']['unitId'] == 10117)
report['delete_recreate'] = {
    'unit_id_reused': before['unit']['unitId'] == after['unit']['unitId'],
    'group_id_reused': before['group_id'] == after['group_id'],
    'unit_name_reused': before['unit']['name'] == after['unit']['name'],
    'group_name_reused': before['group_name'] == after['group_name'],
    'changed_paths': list(changes(before, after)),
    'before_xy': [before['unit']['x'], before['unit']['y']],
    'after_xy': [after['unit']['x'], after['unit']['y']]}
output = repo / 'companion/mission-identity-observations.prototype.json'
output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'delete_recreate': report['delete_recreate'], 'transitions': [
    {'after': t['after'], 'mission_changed_paths': t['mission_changed_paths'],
     'common_aircraft_changed_paths': t['common_aircraft_changed_paths']} for t in report['transitions'][1:]]}, indent=2))
