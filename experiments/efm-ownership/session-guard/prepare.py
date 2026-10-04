"""Create bounded loaded-session controls; no production mission preparation."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('fixture_data', ROOT / 'companion/mission-identity-probe.prototype.py')
data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(data)


def parse_table(raw, variable):
    parser = data.LuaData(raw.decode('utf-8-sig'))
    parser.take(variable)
    parser.take('=')
    result = parser.value()
    parser.skip()
    if parser.pos != len(parser.text):
        raise ValueError('Trailing Lua in fixture data')
    return result


def prepare(source, output):
    if output.exists():
        raise ValueError('Use a new output directory; existing evidence is preserved')
    entries, mission = data.read(source)
    mission = copy.deepcopy(mission)
    rows = data.aircraft(mission)
    if len(rows) != 1 or rows[0]['unit']['type'] != 'FA-18C_hornet' or rows[0]['unit']['skill'] != 'Player':
        raise ValueError('Expected the known single stock-Hornet player fixture')
    package = uuid.uuid4().hex
    module = (ROOT / 'companion/session_guard.lua').read_text(encoding='utf-8')
    script = ('DCSR_SESSION_GUARD_MODULE=(function()\n' + module + '\nend)()\n'
              + 'DCSR_SESSION_GUARD_PACKAGE=' + data.serialize(package) + '\n'
              + (HERE / 'mission.lua').read_text(encoding='utf-8'))
    mission['trigrules'] = {1:dict(comment='Bounded session guard control', predicate='triggerStart',
        eventlist='', rules={}, actions={1:dict(predicate='a_do_script', text=script)})}
    mission['trig'] = {key:{} for key in ('actions', 'conditions', 'func', 'funcStartup', 'flag')}
    mission['trig']['actions'][1] = 'a_do_script(' + data.serialize(script) + ');'
    mission['trig']['conditions'][1] = 'return(true)'
    mission['trig']['flag'][1] = True
    mission['trig']['funcStartup'][1] = 'if mission.trig.conditions[1]() then mission.trig.actions[1]() end'
    description = ('SESSION GUARD ORIGINAL. Disposable stock-Hornet control; no recording or playback. '
        'Click Fly, then F10 > DCS Recorder session check > Request guarded release. '
        'Observe the result and exit. The aircraft is not held.')
    mission['descriptionText'] = 'DictKey_session_guard_description'
    mission['descriptionBlueTask'] = ''
    mission['descriptionRedTask'] = ''
    dictionary = parse_table(entries['l10n/DEFAULT/dictionary'], 'dictionary')
    dictionary['DictKey_session_guard_description'] = description
    entries['mission'] = ('mission = ' + data.serialize(mission)).encode('utf-8')
    entries['l10n/DEFAULT/dictionary'] = ('dictionary = ' + data.serialize(dictionary)).encode('utf-8')
    fields = ['theatre', 'weather', 'coalition', 'trigrules', 'date', 'start_time', 'forcedOptions']
    if any(field not in mission for field in fields):
        raise ValueError('Missing expected fixture field')
    expected = dict(package=package, fields=dict(enumerate(fields, 1)),
                    mission={field:mission[field] for field in fields}, description=description)
    output.mkdir(parents=True)
    (output / 'expected.lua').write_text('return ' + data.serialize(expected) + '\n', encoding='utf-8')
    def archive(name, contents, compression=zipfile.ZIP_DEFLATED):
        with zipfile.ZipFile(output / name, 'x', compression=compression) as z:
            for key, value in sorted(contents.items()):
                z.writestr(key, value)
    archive('030-Session-Guard-valid.miz', entries)
    edited = dict(entries)
    dictionary['DictKey_session_guard_description'] = description.replace('ORIGINAL', 'EDITED')
    edited['l10n/DEFAULT/dictionary'] = ('dictionary = ' + data.serialize(dictionary)).encode('utf-8')
    archive('031-Session-Guard-edited.miz', edited)
    archive('032-Session-Guard-repacked.miz', entries, zipfile.ZIP_STORED)
    for path in output.glob('*.miz'):
        data.read(path)
    report = dict(package=package, status='Prepared; live session/bridge checks pending',
        compared_fields=fields + ['localized description'],
        excluded=['resource bytes', 'other localized fields', 'mission options', 'arbitrary script effects',
                  'native playback authorization', 'held staging'],
        files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir() if p.is_file()})
    (output / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    prepare(args.source, args.output)
