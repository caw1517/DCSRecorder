"""Prepare separate mission copies from an immutable authored archive.

Selection IDs are scoped to one exact archive, not persistent aircraft identity;
mission_lineage.py owns cross-revision association. Loaded-session authorization
belongs to a later gate.
"""
from __future__ import annotations
import copy
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import math
import zipfile
from mission_data import LuaData, serialize

ROOT = Path(__file__).resolve().parents[1]
EFM = ROOT / 'experiments/efm-ownership'
BUILD = '2.9.30.28536'
MARKER = 'DCSRecorder/preparation.json'
LIVERY = 'Blue Angels Jet Team'


def supported_livery(value):
    # The legacy staged playback modules carry only this livery.
    # Mission Editor saves the livery folder ID in lower case; Windows folder names
    # (and so DCS livery lookup) ignore case. Same livery, either spelling.
    return isinstance(value, str) and value.casefold() == LIVERY.casefold()


def same_livery(a, b):
    return isinstance(a, str) and isinstance(b, str) and a.casefold() == b.casefold()


def hornet_liveries(folder):
    """The FA-18C_hornet livery folder inside `folder`, matched in any case."""
    return [p for p in (folder.iterdir() if folder.is_dir() else []) if p.is_dir() and p.name.casefold() == 'fa-18c_hornet']


def find_livery(livery_id, dcs, saved_games):
    """The Hornet livery (folder or .zip) DCS loads for this ID. Searched in order:
    the user's Saved Games liveries, the stock Hornet's, then those of installed DCS
    modules such as campaigns (Mods/<kind>/<module>/Liveries). Refuses when it is
    missing, or found more than once at the same level."""
    dcs = Path(dcs)
    tiers = ((Path(saved_games)/'Liveries/FA-18C_hornet',), (dcs/'CoreMods/aircraft/FA-18C/Liveries/FA-18C_hornet',),
             tuple(r for m in sorted((dcs/'Mods').glob('*/*')) for r in hornet_liveries(m/'Liveries')))
    for roots in tiers:
        found = [p for root in roots for p in (root.iterdir() if root.is_dir() else [])
                 if same_livery(p.name[:-4] if p.suffix.lower() == '.zip' and p.is_file() else p.name, livery_id)
                 and (p.is_dir() or p.suffix.lower() == '.zip')]
        if len(found) > 1:
            raise ValueError(f'The livery "{livery_id}" exists more than once ('
                             + '; '.join(str(p) for p in found) + '). Keep one copy.')
        if found:
            return found[0]
    raise ValueError(f'The livery "{livery_id}" was not found in the stock Hornet liveries, the liveries of installed '
                     'DCS modules or Saved Games/DCS/Liveries/FA-18C_hornet. Install it there, or choose another livery '
                     'in Mission Editor.')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(name, value):
    return (name + ' = ' + serialize(value) + '\n').encode('utf-8')


def packed(entries):
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, content in sorted(entries.items()):
            info = zipfile.ZipInfo(name, (2000, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, content)
    return out.getvalue()


def read_source(path):
    blob = Path(path).read_bytes()
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or sum(i.file_size for i in archive.infolist()) > 100_000_000:
            raise ValueError('Mission has duplicate entries or exceeds the supported 100 MB size.')
        if any(PurePosixPath(n).is_absolute() or '..' in PurePosixPath(n).parts or ':' in n or '\\' in n for n in names):
            raise ValueError('Mission contains an invalid archive path.')
        entries = {n: archive.read(n) for n in names}
    if MARKER in entries or any(n.startswith(('DCSRecorderBehaviorProbe/', 'DCSRecorderIdentity')) for n in entries):
        raise ValueError('Choose the original authored mission; generated copies are not authored inputs.')
    mission = LuaData(entries['mission'].decode('utf-8-sig')).mission()
    if not isinstance(mission, dict):
        raise ValueError('Expected a serialized mission table.')
    # Removing a marker does not make owned controls or custom aircraft authored.
    if any('DCSRECORDER' in v or 'DCSR_RELEASE' in v for v in strings(mission)):
        raise ValueError('Recorder controls already exist. Choose the original authored mission.')
    if any(str(row['unit'].get('type', '')).startswith('DCSRecorder-') for row in aircraft(mission)):
        raise ValueError('Author with stock aircraft, not a generated playback module.')
    return blob, entries, mission


def strings(value):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from strings(k)
            yield from strings(v)
    elif isinstance(value, str):
        yield value


def aircraft(mission):
    rows = []
    for side, coalition in mission.get('coalition', {}).items():
        if not isinstance(coalition, dict):
            continue
        for country in coalition.get('country', {}).values():
            for kind in ('plane', 'helicopter'):
                for group in country.get(kind, {}).get('group', {}).values():
                    for unit in group.get('units', {}).values():
                        rows.append(dict(side=side, country=country.get('id'), kind=kind, group=group, unit=unit))
    return rows


def selected_row(mission, unit_id):
    rows = [r for r in aircraft(mission) if r['unit'].get('unitId') == unit_id]
    if len(rows) != 1:
        raise ValueError('Selected aircraft is missing or its unit ID is ambiguous.')
    return rows[0]


def identity_free(row):
    """An aircraft's authored content apart from its editor names and IDs, and the
    skill field that every recording/playback role assignment overwrites."""
    group = copy.deepcopy(row['group'])
    group.pop('name', None); group.pop('groupId', None)
    for unit in group.get('units', {}).values():
        unit.pop('name', None); unit.pop('unitId', None); unit.pop('skill', None)
    return dict(side=row['side'], country=row['country'], kind=row['kind'], group=group)


def differences(old, new, path=''):
    if isinstance(old, dict) and isinstance(new, dict):
        out = []
        for key in sorted(set(old) | set(new), key=str):
            child = f'{path}.{key}' if path else str(key)
            if key not in old:
                out.append(child + ' added')
            elif key not in new:
                out.append(child + ' removed')
            else:
                out += differences(old[key], new[key], child)
        return out
    return [] if old == new else [path or 'value']


def compatibility(old_row, new_row):
    """Empty when an aircraft is authored identically apart from names and IDs.

    No tolerance is guessed: placement, start, livery, payload, properties, route and
    group settings must match exactly (observed Mission Editor saves retain them).
    """
    return differences(identity_free(old_row), identity_free(new_row))


def selected(mission, unit_id):
    row = selected_row(mission, unit_id)
    if row['kind'] != 'plane' or row['unit']['type'] != 'FA-18C_hornet':
        raise ValueError('Select an ordinary stock F/A-18C Hornet.')
    if len(row['group']['units']) != 1:
        raise ValueError('Put each selected Hornet in its own group in Mission Editor; group splitting is not supported yet.')
    if row['group'].get('lateActivation') or row['group'].get('uncontrolled'):
        raise ValueError('Selected Hornets must be active at mission start, with engines running.')
    start = row['group'].get('route', {}).get('points', {}).get(1, {})
    if start.get('type') not in ('Turning Point', 'TakeOffParkingHot', 'TakeOffGroundHot', 'TakeOff'):
        raise ValueError('Use an airborne or hot start for the selected Hornet.')
    return row


def inspect(path):
    blob, entries, mission = read_source(path)
    rows = aircraft(mission)
    ids = [r['unit'].get('unitId') for r in rows]
    names = [r['unit'].get('name') for r in rows]
    if len(ids) != len(set(ids)) or len(names) != len(set(names)):
        raise ValueError('Duplicate aircraft IDs or names make selection ambiguous.')
    return {'source': str(Path(path).resolve()), 'sha256': sha(blob), 'theatre': mission.get('theatre'),
            'aircraft': [dict(id=r['unit'].get('unitId'), name=r['unit'].get('name'),
                              type=r['unit'].get('type'), skill=r['unit'].get('skill'),
                              group=r['group'].get('name'), start=r['group'].get('route', {}).get('points', {}).get(1, {}).get('type'))
                         for r in rows], 'archive_members': len(entries)}


RECOVERY = ('This mission copy changed, or its identity could not be verified. Open the authored mission in Mission Editor, '
            'save it, and generate a new recording/playback copy in DCS Recorder. You can also use the scene saved with this take. '
            'The recorded flight has not been changed.')
TRIGGER_CONDITIONS = {'c_time_after', 'c_flag_is_true', 'c_flag_is_false', 'c_unit_alive', 'c_group_alive'}
TRIGGER_ACTIONS = {'a_set_flag_value', 'a_set_flag', 'a_clear_flag', 'a_out_text_delay', 'a_out_sound'}


def mission_editor_default(task, group):
    """The two automatic first-waypoint actions DCS 2.9.30 Mission Editor adds to a
    newly placed Hornet (me_action_db.lua: EPLRS; option 35 ALLOW_FORMATION_SIDE_SWAP).
    Neither moves the aircraft or changes its lifecycle. Only these exact forms
    qualify; edited or other automatic actions remain unclassified."""
    if not isinstance(task, dict) or set(task) != {'enabled', 'auto', 'id', 'number', 'params'}:
        return None
    if task['enabled'] is not True or task['auto'] is not True or task['id'] != 'WrappedAction' or set(task['params']) != {'action'}:
        return None
    action = task['params']['action']
    # EPLRS groupId is a datalink network number (getNewTblGroupIdForEPLRS: first
    # free 1-99 among airborne groups, else 0), not the mission group ID.
    eplrs = action.get('params') if action.get('id') == 'EPLRS' and set(action) == {'id', 'params'} else None
    if isinstance(eplrs, dict) and set(eplrs) == {'value', 'groupId'} and eplrs['value'] is True \
            and type(eplrs['groupId']) is int and 0 <= eplrs['groupId'] <= 99:
        return 'EPLRS datalink on'
    if action == {'id': 'Option', 'params': {'value': True, 'name': 35}}:
        return 'allow formation side swap'
    return None


def task_label(task):
    if not isinstance(task, dict):
        return 'unknown task'
    action = task.get('params', {}).get('action', {})
    name = str(task.get('id') or 'unknown task')
    if isinstance(action, dict) and action.get('id'):
        name += ' ' + str(action['id'])
        if action['id'] == 'Option':
            name += ' ' + str(action.get('params', {}).get('name'))
    return name + (' (added automatically by Mission Editor)' if task.get('auto') else '')


def behavior_report(mission, role_ids):
    """Every authored behavior conflict for these roles, not only the first.

    Conflicts refuse preparation and are never removed; preserved Mission Editor
    defaults and lifecycle consequences are reported for review. Unknown scripts
    are never approved by scanning their text."""
    conflicts, preserved, lifecycle = [], [], []
    rows = [selected_row(mission, i) for i in role_ids]
    for row in rows:
        name, group = row['unit']['name'], row['group']
        for p, point in group.get('route', {}).get('points', {}).items():
            task = point.get('task', {})
            if not task:
                continue
            if task.get('id') != 'ComboTask' or set(task.get('params', {})) - {'tasks'}:
                conflicts.append(f'{name}, route point {p}: task {task_label(task)}')
                continue
            for n, item in task['params'].get('tasks', {}).items():
                default = mission_editor_default(item, group)
                if default:
                    preserved.append(f'{name}, route point {p}, action {n}: {default} (Mission Editor default)')
                else:
                    conflicts.append(f'{name}, route point {p}, action {n}: {task_label(item)}')
        for n, item in (group.get('tasks') or {}).items():
            conflicts.append(f'{name}, group task {n}: {task_label(item)}')
    units = {r['unit']['unitId']: r['unit']['name'] for r in rows}
    groups = {r['group'].get('groupId'): r['unit']['name'] for r in rows}
    for index, rule in mission.get('trigrules', {}).items():
        label = f'Trigger {index} "{rule.get("comment") or "unnamed"}"'
        if rule.get('predicate') not in ('triggerStart', 'triggerOnce'):
            conflicts.append(f'{label}: unsupported trigger type {rule.get("predicate")}')
        for kind, allowed, noun in (('rules', TRIGGER_CONDITIONS, 'condition'), ('actions', TRIGGER_ACTIONS, 'action')):
            for n, item in rule.get(kind, {}).items():
                pred = item.get('predicate')
                if pred not in allowed:
                    conflicts.append(f'{label}, {noun} {n}: unclassified {pred}')
                    continue
                who = (units.get(item.get('unit')) if pred == 'c_unit_alive' else
                       groups.get(item.get('group')) if pred == 'c_group_alive' else None)
                if who:
                    lifecycle.append(f'{label} checks whether {who} exists. During playback it sees the playback aircraft, '
                                     'which stays parked at parked completion and is removed at other endings.')
    try:
        verify_compiled_triggers(mission)
    except ValueError as error:
        conflicts.append(str(error))

    def scripts(value, where):
        if isinstance(value, dict):
            if value.get('id') in ('Script', 'ScriptFile'):
                conflicts.append(f'{where}: script task without a supported adapter')
                return
            for child in value.values():
                scripts(child, where)
    for row in aircraft(mission):
        scripts(row['group'], f"{row['unit']['name']} (group {row['group'].get('name')})")
    scripts({k: v for k, v in mission.items() if k != 'coalition'}, 'Mission data')
    scripts({'coalition': {side: {k: v for k, v in c.items() if k != 'country'} if isinstance(c, dict) else c
                           for side, c in mission.get('coalition', {}).items()}}, 'Coalition data')
    for side, coalition in mission.get('coalition', {}).items():
        for country in (coalition.get('country', {}) if isinstance(coalition, dict) else {}).values():
            for kind, content in country.items():
                if kind not in ('plane', 'helicopter'):
                    scripts(content, f'{kind} objects')
    return dict(conflicts=list(dict.fromkeys(conflicts)), preserved=preserved, lifecycle=lifecycle)


def refusal(conflicts):
    return ('Preparation refused. These authored triggers or tasks conflict with the selected aircraft or are unclassified. '
            'They have been preserved, not removed:\n- ' + '\n- '.join(conflicts) +
            '\nEdit them in Mission Editor, or select a different aircraft.')


def validate_supported(mission, role_ids):
    wind = mission.get('weather', {}).get('wind', {})
    if mission.get('theatre') != 'Caucasus' or set(wind) != {'atGround', 'at2000', 'at8000'} or any(w.get('speed') != 0 for w in wind.values()):
        raise ValueError('This preparation profile requires Caucasus and zero wind.')
    rows = [selected(mission, i) for i in role_ids]
    # Authors may place every aircraft ahead of time. Other Client slots stay
    # unchanged (single player does not fly them); only one Player can exist.
    others = []
    for row in aircraft(mission):
        if row['unit']['unitId'] in role_ids:
            continue
        if row['unit'].get('skill') == 'Player':
            raise ValueError(f"\"{row['unit'].get('name')}\" is also set to Player. Set it to Client in Mission Editor; "
                             'DCS Recorder makes the aircraft you choose the Player.')
        if row['unit'].get('skill') == 'Client':
            others.append(row['unit'].get('name'))
    report = behavior_report(mission, role_ids)
    if report['conflicts']:
        raise ValueError(refusal(report['conflicts']))
    report['preserved'] += [f'Client slot "{name}" (not flown in this session)' for name in others]
    return rows, report


def compiled_trigger(index, rule):
    """Bounded compiler for the explicitly supported native trigger subset."""
    conditions, actions = [], []
    for item in rule.get('rules', {}).values():
        pred = item['predicate']
        field = {'c_time_after':'seconds', 'c_flag_is_true':'flag', 'c_flag_is_false':'flag',
                 'c_unit_alive':'unit', 'c_group_alive':'group'}[pred]
        conditions.append(pred+'('+serialize(item[field])+')')
    for item in rule.get('actions', {}).values():
        pred = item['predicate']
        if pred == 'a_set_flag_value':
            args = [serialize(str(item['flag'])), serialize(item['value'])]
        elif pred in ('a_set_flag', 'a_clear_flag'):
            args = [serialize(str(item['flag']))]
        elif pred == 'a_out_text_delay':
            args = ['getValueDictByKey('+serialize(item['text'])+')', serialize(item['seconds']),
                    serialize(item.get('clearview',False)), serialize(item.get('start_delay',0))]
        elif pred == 'a_out_sound':
            args = ['getValueResourceByKey('+serialize(item['file'])+')', serialize(item.get('start_delay',0))]
        else:
            raise ValueError('Unsupported authored action: '+pred)
        actions.append(pred+'('+', '.join(args)+');')
    once = rule['predicate'] == 'triggerOnce'
    action = ''.join(actions)+(f' mission.trig.func[{index}]=nil;' if once else '')
    return {'conditions':'return('+(' and '.join(conditions) or 'true')+')', 'actions':action, 'flag':True,
            'func' if once else 'funcStartup':f'if mission.trig.conditions[{index}]() then mission.trig.actions[{index}]() end'}


def lua_tokens(text):
    # Tokenize whitespace outside strings; do not change string contents or run Lua.
    pattern = r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[A-Za-z_]\w*|\d+(?:\.\d+)?|[^\s]'
    return re.findall(pattern, text)


def verify_compiled_triggers(mission):
    expected = {k:{} for k in ('actions','conditions','func','funcStartup','flag')}
    for index, rule in mission.get('trigrules', {}).items():
        for field, value in compiled_trigger(index, rule).items():
            expected[field][index] = value
    trig = mission.get('trig', {})
    # Mission Editor always saves these tables; empty means no event/custom
    # triggers. Any content is unclassified behavior and stays refused.
    trig = {k: v for k, v in trig.items() if not (k in ('events', 'custom', 'customStartup') and v == {})}
    if set(trig)-set(expected):
        raise ValueError('Unknown compiled trigger table. Save a supported source in Mission Editor.')
    for field, values in expected.items():
        actual = trig.get(field, {})
        if set(actual) != set(values):
            raise ValueError(f'Authored source/compiled trigger indices differ in {field}.')
        for index, value in values.items():
            same = lua_tokens(actual[index]) == lua_tokens(value) if isinstance(value,str) and isinstance(actual[index],str) else value == actual[index]
            if not same:
                raise ValueError(f'Authored trigger {index} has unclassified compiled {field}; preparation cannot certify it.')


def allocate(mission, entries):
    text = '\n'.join(strings(mission)) + '\n' + '\n'.join(entries)
    n = 1
    while f'DCSR_AUTHORED_{n}' in text:
        n += 1
    tables = [mission.get('trigrules', {})] + list(mission.get('trig', {}).values())
    indices = [i for t in tables if isinstance(t, dict) for i in t if isinstance(i, int)]
    return f'DCSR_AUTHORED_{n}', max([0, *indices]) + 1


def append_start(mission, index, script, label):
    mission.setdefault('trigrules', {})[index] = dict(comment=label, predicate='triggerStart', eventlist='', rules={},
                                                   actions={1: dict(predicate='a_do_script', text=script)})
    trig = mission.setdefault('trig', {})
    for key in ('actions', 'conditions', 'func', 'funcStartup', 'flag'):
        trig.setdefault(key, {})
    trig['actions'][index] = 'a_do_script(' + serialize(script) + ');'
    trig['conditions'][index] = 'return(true)'
    trig['flag'][index] = True
    trig['funcStartup'][index] = f'if mission.trig.conditions[{index}]() then mission.trig.actions[{index}]() end'


def carries_smoke(unit):
    """The recorder's smoke profile: the white smoke pod on station 10."""
    return (((unit.get('payload') or {}).get('pylons') or {}).get(10) or {}).get('CLSID') == '{INV-SMOKE-WHITE}'


def record_script(name, namespace, source_sha, lineage=None, association=None, smoke=False, formation=False, package=None):
    script = (EFM/'record_flight_engine_mission.lua').read_text(encoding='utf-8-sig')
    script = script.replace("source='Observer'", 'source=' + serialize(name))
    old = "csv(r.source)..'\\n'"
    # Lineage/association IDs let the companion bind the saved take to its history.
    provenance = f'\\nauthored_lineage,{lineage}\\nauthored_association,{association}' if association else ''
    # The recording copy that produced the take, so binding never has to choose.
    provenance += f'\\nauthored_package,{package}' if package else ''
    extra = f'\\nauthored_source_sha256,{source_sha}{provenance}\\ncapture_timing,frame-batch-v1\\ncapture_build,{BUILD}\\nwind_ground,0\\nwind_2000,0\\nwind_8000,0\\n'
    assert script.count(old) == 1
    script = script.replace(old, 'csv(r.source)..' + serialize(extra.replace('\\n', '\n')))
    # White smoke is captured only when the aircraft carries the smoke pod (V1: white only).
    # Formation recordings have no F10 Start: the formation control begins them at release.
    script = ('DCSRECORDER_FORMATION=true\n' if formation else '') + ('DCSRECORDER_SMOKE=true\n' if smoke else '') + ('DCSRECORDER_CONTACT=true\nDCSRECORDER_WHEELS=true\nDCSRECORDER_CANOPY=true\nDCSRECORDER_LIGHTS=true\n' + script)
    # Only this capture's Lua global names change; the log protocol remains the
    # installed autosave/native-capture contract.
    script = script.replace('DCSRECORDER', namespace)
    script = script.replace(' samples written to DCS.log. Ready for extraction. Keep this DCS session until the recording is collected.',
                            ' samples captured. Confirm the saved take in the companion before exiting.')
    return script


def verify_preservation(source_entries, source_mission, entries, mission, edits, trigger_indices):
    restored = copy.deepcopy(mission)
    for path, old in reversed(edits):
        node = restored
        for k in path[:-1]:
            node = node[k]
        if old == {'__absent__': True}:
            node.pop(path[-1], None)
        else:
            node[path[-1]] = old
    for i in trigger_indices:
        restored.get('trigrules', {}).pop(i, None)
        for table in restored.get('trig', {}).values():
            if isinstance(table, dict):
                table.pop(i, None)
    # Empty trigger containers may be the only structural additions in an empty source.
    for top in ('trig', 'trigrules'):
        if top not in source_mission:
            restored.pop(top, None)
    if 'trig' in source_mission:
        for key in set(restored['trig'])-set(source_mission['trig']):
            if restored['trig'][key]:
                raise ValueError('Unexpected trigger additions.')
            del restored['trig'][key]
    if restored != source_mission:
        raise ValueError('Source/prepared structural comparison failed outside declared role/control changes.')
    unchanged = [n for n in source_entries if n != 'mission']
    if any(entries.get(n) != source_entries[n] for n in unchanged):
        raise ValueError('An authored resource or localization entry changed.')
    return dict(restored_structure_equals_source=True, unchanged_archive_members=unchanged,
                changed_existing_members=['mission'], added_members=sorted(set(entries)-set(source_entries)))


def role_edit(mission, row, key, value, edits):
    def find(node, path):
        if node is row:
            return path
        if isinstance(node, dict):
            for k, v in node.items():
                result = find(v, path+[k])
                if result is not None:
                    return result
        return None
    path = find(mission, [])
    if path is None:
        raise ValueError('Role no longer belongs to mission.')
    edits.append((path+[key], copy.deepcopy(row.get(key, {'__absent__': True}))))
    row[key] = value


def role_remove(mission, row, key, edits):
    """Declared removal of one role field; verify_preservation restores it."""
    role_edit(mission, row, key, None, edits)
    del row[key]


UNIT_KEYS, GROUP_KEYS = ('unitId', 'unit', 'linkUnit'), ('groupId', 'group')


def remove_aircraft(mission, keep_ids, edits):
    """Declared removal of every aircraft not in `keep_ids` (muted or take-less
    formation positions); verify_preservation restores each changed container.
    Groups and units are renumbered contiguously. Refuses when anything left in
    the mission still refers to a removed aircraft. Returns the removed names."""
    removed, removed_units, removed_groups = [], set(), set()
    for side, coalition in mission.get('coalition', {}).items():
        if not isinstance(coalition, dict):
            continue
        for country_key, country in coalition.get('country', {}).items():
            for kind in ('plane', 'helicopter'):
                container = country.get(kind, {}).get('group')
                if not container:
                    continue
                kept, changed = [], False
                for group in container.values():
                    units = list(group.get('units', {}).values())
                    staying = [u for u in units if u.get('unitId') in keep_ids]
                    for unit in units:
                        if unit not in staying:
                            removed.append(unit.get('name')); removed_units.add(unit.get('unitId'))
                    if len(staying) != len(units):
                        changed = True
                        if not staying:
                            removed_groups.add(group.get('groupId'))
                    if staying:
                        kept.append((group, staying, len(staying) != len(units)))
                if not changed:
                    continue
                edits.append((['coalition', side, 'country', country_key, kind, 'group'], copy.deepcopy(container)))
                for group, staying, partial in kept:
                    if partial:
                        group['units'] = {i: u for i, u in enumerate(staying, 1)}
                country[kind]['group'] = {i: g for i, (g, _, _) in enumerate(kept, 1)}
    def references(node, path=()):
        if isinstance(node, dict):
            for key, value in node.items():
                ids = removed_units if key in UNIT_KEYS else removed_groups if key in GROUP_KEYS else ()
                if not isinstance(value, (dict, list)) and value in ids:
                    yield '/'.join(map(str, path + (key,)))
                yield from references(value, path + (key,))
    found = list(references(mission))
    if found:
        raise ValueError('Preparation refused. The mission still refers to an aircraft that is left out of this formation '
                         '(muted or without a take): ' + ', '.join(found[:6]) + '. Edit it in Mission Editor, or record that position first.')
    return removed


def prepare_recording(source, unit_id, output, expected_sha=None, lineage=None, association=None, package=None):
    blob, original_entries, original = read_source(source)
    if expected_sha and sha(blob) != expected_sha:
        raise ValueError('The authored mission changed after selection. Inspect it again.')
    mission, entries = copy.deepcopy(original), dict(original_entries)
    (row,), behavior = validate_supported(mission, [unit_id])
    namespace, index = allocate(mission, entries)
    edits = []
    role_edit(mission, row['unit'], 'skill', 'Player', edits)
    script = record_script(row['unit']['name'], namespace, sha(blob), lineage, association, smoke=carries_smoke(row['unit']), package=package)
    append_start(mission, index, script, 'DCS Recorder: record selected authored Hornet')
    manifest = dict(profile='authored-recording-v1', build=BUILD, source_sha256=sha(blob),
                    selected_id=unit_id, selected_name=row['unit']['name'], namespace=namespace,
                    lineage=lineage, association=association,
                    trigger_indices=[index], role_edits=edits, behavior=behavior,
                    message='F10 > DCS Recorder > Start recording / Stop recording. Authored briefing and scene are preserved.')
    entries[MARKER] = json.dumps(manifest, sort_keys=True).encode()
    entries['mission'] = encoded('mission', mission)
    manifest['preservation'] = verify_preservation(original_entries, original, entries, mission, edits, [index])
    return save_package(output, blob, entries, manifest)


def playback_entries(source, unit_id, player_id, metadata, first, raw_first, module, token, saved=None, faults=False, drop_stations=(),
                     livery_name=None):
    """Build playback mission data without touching a simulator installation.

    `saved` is the take's own saved scene when `source` is a newer, explicitly
    confirmed revision; `unit_id` is then the confirmed counterpart of the recorded
    aircraft, which must be authored identically apart from its name and IDs.
    `faults` adds the developer fault-injection menu (diagnostic packages only).
    `livery_name` is the recorded livery as installed in the playback module; the
    lead names it exactly (Mission Editor may save the ID in another case).
    `drop_stations` are lead pylons whose mod store this installation no longer
    provides; they are removed so the playback aircraft carries nothing there.
    """
    blob, original_entries, original = read_source(source)
    if unit_id == player_id:
        raise ValueError('Choose a different stock Hornet for the player. Add it in Mission Editor if missing.')
    saved_blob = Path(saved).read_bytes() if saved else blob
    if metadata.get('authored_source_sha256') != sha(saved_blob):
        raise ValueError('This take does not belong to the exact authored source. Use the scene saved with it.')
    mission, entries = copy.deepcopy(original), dict(original_entries)
    (lead, player), behavior = validate_supported(mission, [unit_id, player_id])
    if saved:
        recorded = selected(read_source(saved)[2], int(metadata['source_unit_id']))
        if metadata.get('source') != recorded['unit']['name']:
            raise ValueError('The saved scene does not contain the recorded aircraft.')
        changed = compatibility(recorded, lead)
        if changed:
            raise ValueError("The recorded aircraft's authored start or configuration differs in this scene ("
                             + ', '.join(changed[:4]) + '). Use the saved scene; the recorded flight is never moved.')
    elif metadata.get('source') != lead['unit']['name']:
        raise ValueError('Selected playback aircraft does not match the recorded source name.')
    check_playback_take(lead, metadata)
    namespace, index = allocate(mission, entries)
    edits=[]
    config=place_playback(mission,lead,player,metadata,first,raw_first,module,token,edits,drop_stations,livery_name)
    if faults:config['faults']=True
    script=(EFM/'release-start/mission.lua').read_text(encoding='utf-8')
    # Replace exact literals before inserting arbitrary authored names.
    script=script.replace("'StagedPlayback'",'__LEAD_NAME__').replace("'Observer'",'__PLAYER_NAME__')
    script=script.replace(";sample('SceneWitness')",'')
    # Authored playback only: a release the hook could not verify (absent checker,
    # mismatched loaded mission, stale request) is an identity refusal with the
    # approved recovery text. Native readiness failures keep their diagnostic.
    for old,new in (("'Release test: '","'DCS Recorder: '"),
                    ("if now-s.started>10 then s.fail('bridge_or_native_readiness_timeout')",
                     "if now-s.started>10 then s.fail(matched(u) and status==.125 and 'identity_unverified' or 'bridge_or_native_readiness_timeout')"),
                    ("notice('FAILED: '..tostring(reason)..'. The playback aircraft was removed; the mission continues. Logs were retained.')",
                     "notice(IDENTITY[reason] and RECOVERY or 'FAILED: '..tostring(reason)..'. The playback aircraft was removed; the mission continues. Logs were retained.')")):
        if script.count(old)!=1:raise ValueError('Release mission script changed: '+old)
        script=script.replace(old,new)
    script=('local IDENTITY={identity_unverified=true,stale_or_mismatched_request=true}\n'
            'local RECOVERY='+serialize('Playback blocked. '+RECOVERY)+'\n'+script)
    script=script.replace('DCSR_RELEASE',namespace).replace('DCS Recorder release test','DCS Recorder playback')
    script=script.replace('__LEAD_NAME__',serialize(lead['unit']['name'])).replace('__PLAYER_NAME__',serialize(player['unit']['name']))
    script=namespace+'_CONFIG='+serialize(config)+'\n'+script
    cleanup=install_control(mission,index,namespace,script)
    manifest=dict(profile='authored-playback-v1',build=BUILD,source_sha256=sha(blob),saved_scene_sha256=sha(saved_blob),selected_id=unit_id,
                  selected_name=lead['unit']['name'],player_id=player_id,player_name=player['unit']['name'],
                  namespace=namespace,trigger_indices=[index,cleanup],role_edits=edits,initial=config,
                  player_authored_start_preserved=True,behavior=behavior,
                  parked_endpoint=metadata.get('parked_endpoint'))
    # Check the entire player's authored group apart from the deliberate skill change.
    player_check=copy.deepcopy(player['group'])
    next(iter(player_check['units'].values()))['skill']=selected(original,player_id)['unit']['skill']
    if player_check!=selected(original,player_id)['group']:
        raise ValueError('Player authored placement or configuration changed.')
    entries[MARKER]=json.dumps(manifest,sort_keys=True).encode()
    entries['mission']=encoded('mission',mission)
    manifest['preservation']=verify_preservation(original_entries,original,entries,mission,edits,[index,cleanup])
    return blob,entries,mission,manifest


def check_playback_take(lead, metadata):
    """Refuse a take its authored aircraft cannot play back exactly."""
    # The recorded livery plays back; the authored aircraft must carry the same one.
    if not same_livery(metadata.get('livery'), lead['unit'].get('livery_id')) or metadata.get('aircraft') != lead['unit']['type']:
        raise ValueError('Recorded aircraft configuration differs from the source selection.')
    if not all(metadata.get(k) for k in ('exterior_available','engine_available','lights_available','canopy_available','wheels_available')):
        raise ValueError('Authored playback requires the complete supported snapshot.')
    if metadata.get('capture_build') != BUILD:
        raise ValueError('Recording build differs from the supported profile.')


def place_playback(mission, lead, player, metadata, first, raw_first, module, token, edits, drop_stations=(), livery_name=None):
    """Make `lead` a playback aircraft at its take's first pose and, when given,
    `player` the player's aircraft; returns the lead's control configuration."""
    # 12 significant digits survive DCS's load/save serialization unchanged, so the
    # loaded mission can be compared exactly. Native playback uses the tape pose.
    g12=lambda v:float(format(v,'.12g'))
    first=list(first);first[1:4]=map(g12,first[1:4])
    speed=g12(math.sqrt(sum(v*v for v in first[8:11])))
    heading=g12(math.atan2(float(raw_first['fz']),float(raw_first['fx'])))
    for key,value in dict(type=module,skill='High',x=first[1],y=first[3],alt=first[2],
                          alt_type='BARO',speed=speed,heading=heading,psi=-heading).items():
        role_edit(mission,lead['unit'],key,value,edits)
    for key,value in dict(x=first[1],y=first[3]).items():role_edit(mission,lead['group'],key,value,edits)
    # Playback starts at the actual recording's first pose, even if capture began
    # after spawn. No translation or invented player offset is introduced.
    point=lead['group']['route']['points'][1]
    # A take whose first sample is grounded (version-8 contact) starts as a hot
    # ground start at that exact pose; a parking slot would move it.
    grounded=raw_first.get('in_air')=='0'
    for key,value in dict(x=first[1],y=first[3],alt=first[2],alt_type='BARO',speed=speed,
                          type='TakeOffGroundHot' if grounded else 'Turning Point',
                          action='From Ground Area Hot' if grounded else 'Turning Point').items():role_edit(mission,point,key,value,edits)
    if grounded:
        for row in (lead['unit'],point):
            for key in ('parking','parking_id','parking_landing','airdromeId','helipadId','linkUnit'):
                if key in row:role_remove(mission,row,key,edits)
    # The tape flies the aircraft, but its DCS AI still follows the authored route.
    # Once past the last waypoint it heads home to land and lowers its own gear,
    # opening gear doors the tape never recorded (Diamond, 9 October 2026). An
    # endless orbit at the last waypoint keeps the route from ever finishing.
    # Playback aircraft are also immortal: a damaged one's AI ejected its pilot
    # while the tape flew on (Diamond, 10 October 2026), and damage slowed its
    # stepping to 10 Hz. Bumps still happen; the aircraft stays intact.
    points=lead['group']['route']['points'];first_point,last=points[min(points)],points[max(points)]
    def added(point,entries):
        task=copy.deepcopy(point.get('task') or {'id':'ComboTask','params':{'tasks':{}}})
        if task.get('id')!='ComboTask':task={'id':'ComboTask','params':{'tasks':{1:dict(task,number=1)}}}
        tasks=task['params'].setdefault('tasks',{})
        for entry in entries:
            number=max(tasks,default=0)+1;tasks[number]=dict(entry,number=number,auto=False,enabled=True)
        return task
    immortal=dict(id='WrappedAction',params=dict(action=dict(id='SetImmortal',params=dict(value=True))))
    orbit=dict(id='Orbit',params=dict(pattern='Circle',altitude=last.get('alt',first[2]),speed=last.get('speed',speed)))
    if first_point is last:role_edit(mission,last,'task',added(last,[immortal,orbit]),edits)
    else:
        role_edit(mission,first_point,'task',added(first_point,[immortal]),edits)
        role_edit(mission,last,'task',added(last,[orbit]),edits)
    if player:role_edit(mission,player['unit'],'skill','Player',edits)
    if livery_name and lead['unit'].get('livery_id')!=livery_name:
        if not same_livery(livery_name,lead['unit'].get('livery_id')):raise ValueError('Installed livery differs from the recorded one.')
        role_edit(mission,lead['unit'],'livery_id',livery_name,edits)
    pylons=(lead['unit'].get('payload') or {}).get('pylons') or {}
    for station in drop_stations:role_remove(mission,pylons,station,edits)
    expected={21:first[11],38:first[42]}
    for channels,values in (([0,3,5,9,10,11,12,13,14,15,16,17,18],first[12:25]),
                            ([28,29,89,90],first[25:29]),([88,190,191,192,193,210,212],first[35:42]),
                            ([1,6,4,101,103,102,2],first[43:50])):expected.update(zip(channels,values))
    config=dict(expected=expected,token_high=((token>>40)&0xffffff)/16777216,
                token_low=(token&0xffffff)/16777216,duration=metadata['duration'],
                smoke_events=dict(enumerate(metadata.get('smoke_events') or [dict(time=0,on=False)],1)))
    if metadata.get('surface_available'):
        # Ground takes log playback-side contact; a measured eligible endpoint stays parked.
        config.update(contact=True,parked=bool((metadata.get('parked_endpoint') or {}).get('eligible')),replay_scale=100000)
    return config


def install_control(mission, index, namespace, script):
    """Install the hold/release control at trigger `index` and its failure cleanup
    at the next index; returns the cleanup index."""
    append_start(mission,index,script,'DCS Recorder: hold and release selected playback aircraft')
    mission['trigrules'][index]['actions']={1:dict(predicate='a_set_command',command=816),
                                           2:dict(predicate='a_do_script',text=script)}
    mission['trig']['actions'][index]='a_set_command(816);'+mission['trig']['actions'][index]
    cleanup=index+1
    mission['trigrules'][cleanup]=dict(comment='DCS Recorder: release owned hold on failure',predicate='triggerOnce',eventlist='',
        rules={1:dict(predicate='c_flag_is_true',flag=namespace+'_CLEANUP')},
        actions={1:dict(predicate='a_set_command',command=816),2:dict(predicate='a_do_script',text=namespace+'.cleaned()')})
    trig=mission['trig'];trig['conditions'][cleanup]='return(c_flag_is_true('+serialize(namespace+'_CLEANUP')+'))'
    trig['actions'][cleanup]='a_set_command(816);a_do_script('+serialize(namespace+'.cleaned()')+f');mission.trig.func[{cleanup}]=nil;'
    trig['func'][cleanup]=f'if mission.trig.conditions[{cleanup}]() then mission.trig.actions[{cleanup}]() end'
    trig['flag'][cleanup]=True
    return cleanup


def save_package(output, source, entries, manifest):
    output = Path(output)
    data = packed(entries)
    output.mkdir(parents=True, exist_ok=False)
    (output/'source.miz').write_bytes(source)
    (output/'prepared.miz').write_bytes(data)
    manifest['prepared_sha256'] = sha(data)
    manifest['source_member_hashes'] = {n:sha(v) for n,v in zip_entries(source).items()}
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    return manifest


def zip_entries(blob):
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        return {n:archive.read(n) for n in archive.namelist()}
