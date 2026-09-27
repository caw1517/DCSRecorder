"""THROWAWAY: package a read-only stock-Hornet observation mission locally."""
import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

def prepare(output, dcs, baseline):
    version = json.loads((dcs / 'autoupdate.cfg').read_text(encoding='utf-8-sig'))['version']
    if version != '2.9.29.27468':
        raise ValueError('Diagnostic mappings target DCS 2.9.29.27468')
    output.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(baseline) as archive:
        (output / 'baseline.lua').write_bytes(archive.read('mission'))
    description = (
        'READ-ONLY EXTERIOR STATE DIAGNOSTIC. One stock Hornet; no playback aircraft. '
        'Slow to an appropriate gear/flap operating speed before changing configuration. '
        'F10 > Exterior state diagnostic > Start capture. Mark each segment before '
        'changing gear, flaps, pitch, roll, rudder or speed brake, one at a time. '
        'Hold each position for several seconds and return to baseline. Stop capture '
        'when finished. The diagnostic observes arguments 0-30 at 20 Hz for at most '
        'four minutes. Preserve DCS.log before the next DCS session. This is not a '
        'flight-library recording and does not test playback or ground contact.'
    )
    (output / 'description.txt').write_text(description, encoding='utf-8')
    def lua(script, *args):
        subprocess.run([str(dcs / 'bin/luae.exe'), str(ROOT / script), *map(str,args)], check=True)
    lua('make_recording_mission.lua', output / 'baseline.lua', HERE / 'capture.lua', output / 'mission', output / 'description.txt')
    lua('verify_hornet_requirements.lua', output / 'mission', dcs / 'Mods/aircraft/FA-18C/entry.lua', dcs / 'MissionEditor/modules/me_mission.lua')
    lua('verify_hornet_routes.lua', output / 'mission', dcs / 'MissionEditor/modules/me_route.lua', 1)
    lua('verify_hornet_configuration.lua', output / 'mission', dcs, 1)
    destination = output / 'DCSRecorder-Exterior-State-Diagnostic.miz'
    with zipfile.ZipFile(baseline) as source, zipfile.ZipFile(destination, 'x', zipfile.ZIP_DEFLATED) as target:
        for entry in source.infolist():
            target.writestr(entry, (output / 'mission').read_bytes() if entry.filename == 'mission' else source.read(entry.filename))
    (output / 'manifest.json').write_text(json.dumps({
        'status': 'Prepared; live observation pending', 'dcs_build': version,
        'mission_sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
        'capture_sha256': hashlib.sha256((HERE / 'capture.lua').read_bytes()).hexdigest(),
        'baseline_sha256': hashlib.sha256(baseline.read_bytes()).hexdigest(),
    }, indent=2) + '\n', encoding='utf-8')
    return destination

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    parser.add_argument('--dcs', type=Path, default=Path('D:/DCS World'))
    parser.add_argument('--baseline', type=Path, default=ROOT / 'package/hornet-prototype/EFM-Probe-Hornet-left-roll-400KIAS.miz')
    args = parser.parse_args()
    print(prepare(args.output, args.dcs, args.baseline))
