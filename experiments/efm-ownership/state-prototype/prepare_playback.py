"""THROWAWAY: package the isolated exterior actuator; installation is separate."""
import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path
from analyze import analyze

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CHANNELS = [0, 3, 5, *range(9, 19), 21]
TYPE = 'DCSRecorder-Hornet-State'

def prepare(logfile, output, dcs, donor, baseline, post_step=False, post_animation=False):
    assert not (post_step and post_animation)
    assert json.loads((dcs / 'autoupdate.cfg').read_text(encoding='utf-8-sig'))['version'] == '2.9.29.27468'
    output.mkdir(parents=True, exist_ok=False)
    summary = analyze(logfile, output / 'capture')
    with (output / 'capture/arguments.csv').open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    module_type = TYPE + ('-PostAnimation' if post_animation else '-PostStep' if post_step else '')
    binary = 'HornetStateAnimationProbe' if post_animation else 'HornetStatePostStepProbe' if post_step else 'HornetStateProbe'
    mod = output / module_type
    (mod / 'bin').mkdir(parents=True)
    tape = ['DCS_EXTERIOR_PROTOTYPE_V1', str(len(rows)), ' '.join(map(str, CHANNELS))]
    for row in rows:
        values = [float(row[f'arg_{c}']) for c in CHANNELS]
        assert all((-1 if c not in (0, 3, 5, 21) else 0) <= value <= 1 for c, value in zip(CHANNELS, values))
        tape.append(' '.join([f"{float(row['t'])-summary['first_time']:.9f}", *map(str, values)]))
    (mod / 'bin/exterior-state.txt').write_text('\n'.join(tape) + '\n', encoding='ascii')
    for name in ('entry.lua', 'aircraft.lua'):
        text = (donor / name).read_text(encoding='utf-8-sig')
        assert 'DCSRecorder-Hornet-Probe' in text
        text = text.replace('DCSRecorder-Hornet-Probe', module_type)
        if name == 'entry.lua':
            text = text.replace('HornetProbe', binary).replace('DCS Recorder Hornet Prototype', 'DCS Recorder Exterior State Test')
        (mod / name).write_text(text, encoding='utf-8')
    for folder in ('Cockpit', 'Datalinks', 'Liveries'):
        shutil.copytree(donor / folder, mod / folder)
    (mod / 'Liveries/DCSRecorder-Hornet-Probe').rename(mod / 'Liveries' / module_type)
    shutil.copy2(ROOT / ('build/Release/' + binary + '.dll'), mod / ('bin/' + binary + '.dll'))
    with zipfile.ZipFile(baseline) as source:
        (output / 'baseline.lua').write_bytes(source.read('mission'))
    markers = [{'time': m['time'] - summary['first_time'], 'segment': m['segment']} for m in summary['markers']]
    config = 'return {aircraft=' + json.dumps(module_type) + ',post_step=' + str(post_step).lower() + ',post_animation=' + str(post_animation).lower() + ',duration=' + str(summary['duration']) + ',markers={\n'
    config += ''.join('{time=' + str(m['time']) + ',segment=' + json.dumps(m['segment']) + '},\n' for m in markers) + '}}\n'
    (output / 'config.lua').write_text(config, encoding='utf-8')
    def lua(script, *args):
        subprocess.run([str(dcs / 'bin/luae.exe'), str(ROOT / script), *map(str, args)], check=True)
    lua('state-prototype/make_playback.lua', output / 'baseline.lua', HERE / 'playback_mission.lua', output / 'config.lua', output / 'mission')
    lua('verify_hornet_requirements.lua', output / 'mission', dcs / 'Mods/aircraft/FA-18C/entry.lua', dcs / 'MissionEditor/modules/me_mission.lua')
    lua('verify_hornet_routes.lua', output / 'mission', dcs / 'MissionEditor/modules/me_route.lua', 2)
    lua('verify_hornet_configuration.lua', output / 'mission', dcs, 2)
    mission = output / ('DCSRecorder-Stabilator-Animation.miz' if post_animation else 'DCSRecorder-Exterior-State-Stabilator.miz' if post_step else 'DCSRecorder-Exterior-State-Playback.miz')
    with zipfile.ZipFile(baseline) as source, zipfile.ZipFile(mission, 'x', zipfile.ZIP_DEFLATED) as target:
        for entry in source.infolist():
            target.writestr(entry, (output / 'mission').read_bytes() if entry.filename == 'mission' else source.read(entry.filename))
    manifest = {'status': 'Prepared; live SDK retention and rendering pending',
                'dcs_build': '2.9.29.27468', 'source_log_sha256': summary['source_sha256'],
                'samples': len(rows), 'duration': summary['duration'], 'channels': CHANNELS,
                'post_step_stabilators': post_step,
                'post_animation_stabilators': post_animation,
                'files': {p.relative_to(output).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in [mission, *mod.rglob('*')] if p.is_file()}}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(mission)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('logfile', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--dcs', type=Path, default=Path('D:/DCS World'))
    parser.add_argument('--donor', type=Path, default=Path.home() / 'Saved Games/DCS/Mods/aircraft/DCSRecorder-Hornet-Probe')
    parser.add_argument('--baseline', type=Path, default=ROOT / 'package/hornet-prototype/EFM-Probe-Hornet-left-roll-400KIAS.miz')
    timing = parser.add_mutually_exclusive_group()
    timing.add_argument('--post-step', action='store_true')
    timing.add_argument('--post-animation', action='store_true')
    args = parser.parse_args()
    prepare(args.logfile, args.output, args.dcs, args.donor, args.baseline, args.post_step, args.post_animation)
