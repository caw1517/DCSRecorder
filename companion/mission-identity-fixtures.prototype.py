"""THROWAWAY controlled fixtures; writes new archives only, never edits originals."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import zipfile

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('identity_probe', Path(__file__).with_name('mission-identity-probe.prototype.py'))
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
source, destination = map(Path, sys.argv[1:3])
destination.mkdir(parents=True, exist_ok=True)
entries, baseline = probe.read(source)

def groups(m):
    return m['coalition']['blue']['country'][1]['plane']['group']

def write(name, mission, compression=zipfile.ZIP_DEFLATED, reverse=False):
    data = dict(entries)
    data['mission'] = ('mission = ' + probe.serialize(mission)).encode('utf-8')
    path = destination / (name + '.miz')
    with zipfile.ZipFile(path, 'x', compression=compression) as archive:
        for key, value in (reversed(list(data.items())) if reverse else data.items()):
            archive.writestr(key, value)
    snap = probe.snapshot(path)
    (destination / (name + '.json')).write_text(json.dumps(snap, indent=2)+'\n', encoding='utf-8')
    return snap

four = copy.deepcopy(baseline)
four['coalition']['blue']['country'][1]['plane']['group'] = {i:g for i,g in groups(four).items() if i <= 4}
seven = copy.deepcopy(baseline)
reordered = copy.deepcopy(seven)
reordered['coalition']['blue']['country'][1]['plane']['group'] = dict(enumerate(reversed(list(groups(reordered).values())), 1))
report = [write('10-controlled-four-input', four), write('11-controlled-seven-input', seven),
          write('12-reordered-seven-input', reordered)]

runtime = copy.deepcopy(four)
runtime['coalition']['blue']['country'][1]['plane']['group'] = {1:groups(runtime)[1]}
runtime['descriptionText'] = 'IDENTITY_LOAD_PROBE_ORIGINAL: disposable load diagnostic; no recorder/playback.'
runtime['descriptionBlueTask'] = 'Disposable load diagnostic. Exit after observing load.'
runtime['descriptionRedTask'] = ''
runtime['forcedOptions'] = dict(runtime.get('forcedOptions', {}), immortal=True)
runtime['trigrules'] = {}
runtime['trig'] = {k:{} for k in ('actions','conditions','func','funcStartup','flag')}
# A simple startup log proves that mission execution occurred; it does not approve the load.
runtime['trig']['funcStartup'][1] = "env.info('IDENTITY_PROBE_MISSION_SCRIPT ORIGINAL')"
report.append(write('20-Identity-LoadProbe-valid', runtime))
edited = copy.deepcopy(runtime)
edited['descriptionText'] = 'IDENTITY_LOAD_PROBE_EDITED: disposable changed-copy diagnostic.'
edited['trig']['funcStartup'][1] = "env.info('IDENTITY_PROBE_MISSION_SCRIPT EDITED')"
report.append(write('21-Identity-LoadProbe-edited', edited))
report.append(write('22-Identity-LoadProbe-repacked', runtime, compression=zipfile.ZIP_STORED, reverse=True))
print(json.dumps([{'name':Path(s['path']).name,'sha256':s['archive_sha256'],'aircraft':len(s['aircraft'])} for s in report], indent=2))
