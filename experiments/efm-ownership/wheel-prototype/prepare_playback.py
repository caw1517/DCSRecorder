"""Prepare a separate SDK-only actuator using the measured low-speed wheel/steering capture."""
import argparse
import hashlib
import json
import math
import shutil
import subprocess
import zipfile
from pathlib import Path
from analyze import analyze

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DCS = Path('D:/DCS World')
MODULE = 'DCSRecorder-Hornet-Wheels'
BINARY = 'HornetWheelProbe'
MISSION = 'DCSRecorder-Wheel-Playback.miz'


def prepare(log, output):
    assert json.loads((DCS/'autoupdate.cfg').read_text(encoding='utf-8-sig'))['version'] == '2.9.29.27468'
    summary = analyze(log)
    assert summary['protocol'] == 2, 'Steering capture required'
    assert summary['speed_range'][1] < 5, 'This replay is checked only for the measured slow taxi'
    rows = []
    for line in log.read_text(errors='replace').splitlines():
        if 'DCSWHEEL,2,DATA,' not in line:
            continue
        fields = line.split('DCSWHEEL,2,DATA,', 1)[1].split(',')
        rows.append([float(fields[1]), *map(float, fields[8:18])])
    assert len(rows) == summary['samples']
    origin = rows[0][0]
    for row in rows:
        row[0] -= origin
        assert len(row) == 11 and all(map(math.isfinite, row))
        assert all(0 <= v <= 1 for v in row[1:10]) and -1 <= row[10] <= 1
    for a, b in zip(rows, rows[1:]):
        for i in (7, 8, 9):
            delta = b[i] - a[i]
            assert abs(delta - round(delta)) < .1, 'Outside measured low-speed rotation step'
    output.mkdir(parents=True, exist_ok=False)
    mod = output/MODULE
    (mod/'bin').mkdir(parents=True)
    donor = Path.home()/'Saved Games/DCS/Mods/aircraft/DCSRecorder-Hornet-Probe'
    for name in ('entry.lua', 'aircraft.lua'):
        text = (donor/name).read_text(encoding='utf-8-sig')
        assert 'DCSRecorder-Hornet-Probe' in text
        text = text.replace('DCSRecorder-Hornet-Probe', MODULE)
        if name == 'entry.lua':
            text = text.replace('HornetProbe', BINARY).replace('DCS Recorder Hornet Prototype', 'DCS Recorder Captured Wheel Test')
        (mod/name).write_text(text, encoding='utf-8')
    for name in ('Cockpit', 'Datalinks', 'Liveries'):
        shutil.copytree(donor/name, mod/name)
    (mod/'Liveries/DCSRecorder-Hornet-Probe').rename(mod/'Liveries'/MODULE)
    shutil.copy2(ROOT/('build/Release/'+BINARY+'.dll'), mod/('bin/'+BINARY+'.dll'))
    tape = ['DCS_WHEEL_PROTOTYPE_V1', str(len(rows)), '0 5 3 1 6 4 101 103 102 2']
    tape += [' '.join(format(v, '.12g') for v in row) for row in rows]
    (mod/'bin/exterior-state.txt').write_text('\n'.join(tape)+'\n', encoding='ascii')
    subprocess.run([str(ROOT/'build/Release/wheel_playback_check.exe'), str(mod/('bin/'+BINARY+'.dll'))], check=True)

    baseline = ROOT/'package/hornet-prototype/EFM-Probe-Hornet-left-roll-400KIAS.miz'
    with zipfile.ZipFile(baseline) as source:
        (output/'baseline.lua').write_bytes(source.read('mission'))
    description = ('CAPTURED WHEEL PLAYBACK. Leave Active Pause on until F10 > Wheel playback > Start captured wheel sequence. '
        'Start releases your aircraft and spawns the separate airborne test lead. F2 to the lead; zoom into its lowered gear. '
        'Watch wheels roll and stop, strut compression and nose-wheel steering left, center, right, center. '
        'Allow about one minute until lead removal. This presentation-only experiment replays the actual slow taxi '
        'animations on an ordinary airborne route. It does not replay the taxi path or validate ground contact. '
        'Leave DCS open for log collection.')
    config = 'return {aircraft='+json.dumps(MODULE)+',duration='+str(rows[-1][0])+',description='+json.dumps(description)+',markers={\n'
    config += ''.join('{time='+str(p['time']-origin)+',segment='+json.dumps(p['label'])+'},\n' for p in summary['marks'])+'}}\n'
    (output/'config.lua').write_text(config)

    def lua(script, *args):
        subprocess.run([str(DCS/'bin/luae.exe'), str(script), *map(str, args)], check=True)

    lua(ROOT/'state-prototype/make_playback.lua', output/'baseline.lua', HERE/'playback_mission.lua', output/'config.lua', output/'mission')
    lua(ROOT/'verify_hornet_requirements.lua', output/'mission', DCS/'Mods/aircraft/FA-18C/entry.lua', DCS/'MissionEditor/modules/me_mission.lua')
    lua(ROOT/'verify_hornet_routes.lua', output/'mission', DCS/'MissionEditor/modules/me_route.lua', 2)
    lua(ROOT/'verify_hornet_configuration.lua', output/'mission', DCS, 2)
    lua(HERE/'check_playback_mission.lua', HERE/'playback_mission.lua')
    destination = output/MISSION
    with zipfile.ZipFile(baseline) as source, zipfile.ZipFile(destination, 'x', zipfile.ZIP_DEFLATED) as target:
        for entry in source.infolist():
            target.writestr(entry, (output/'mission').read_bytes() if entry.filename == 'mission' else source.read(entry.filename))
    assets = [destination, *[p for p in mod.rglob('*') if p.is_file() and 'state-logs' not in p.parts]]
    manifest = dict(module=MODULE, binary=BINARY, mission=MISSION, source_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),
        samples=len(rows), origin=origin, duration=rows[-1][0], channels=[0,5,3,1,6,4,101,103,102,2], status='offline checked; live retention/rendering pending',
        files={p.relative_to(output).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in assets})
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(destination)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('log', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    prepare(args.log, args.output)
