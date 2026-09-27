"""THROWAWAY: package the engine observation mission; generated DCS assets stay local."""
import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def prepare(output, dcs, baseline):
    version = json.loads((dcs/'autoupdate.cfg').read_text(encoding='utf-8-sig'))['version']
    if version != '2.9.29.27468':
        raise ValueError('Engine diagnostic targets DCS 2.9.29.27468')
    output.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(baseline) as archive:
        (output/'baseline.lua').write_bytes(archive.read('mission'))
    description = ('READ-ONLY ENGINE DIAGNOSTIC. One stock Hornet; no playback aircraft. '
        'F10 > Engine state diagnostic > Start capture. Mark each phase before moving '
        'throttles: baseline, both idle, both military (maximum dry), left afterburner '
        '(right dry), right afterburner (left dry), both afterburner, both dry. '
        'Hold each briefly and keep control of the aircraft. Observe left/right nozzle '
        'motion, visible flame and engine sound separately; external-view video is useful. '
        'Markers only label the log. Stop capture when done and retain this DCS session '
        'for log collection. Four-minute maximum; this is not a library recording. '
        'The separate GUI diagnostic hook must be installed and DCS restarted first.')
    (output/'description.txt').write_text(description, encoding='utf-8')
    def lua(script, *args):
        subprocess.run([str(dcs/'bin/luae.exe'),str(ROOT/script),*map(str,args)],check=True)
    lua('make_recording_mission.lua',output/'baseline.lua',HERE/'capture.lua',output/'mission',output/'description.txt')
    lua('verify_hornet_requirements.lua',output/'mission',dcs/'Mods/aircraft/FA-18C/entry.lua',dcs/'MissionEditor/modules/me_mission.lua')
    lua('verify_hornet_routes.lua',output/'mission',dcs/'MissionEditor/modules/me_route.lua',1)
    lua('verify_hornet_configuration.lua',output/'mission',dcs,1)
    destination=output/'DCSRecorder-Engine-State-Diagnostic.miz'
    with zipfile.ZipFile(baseline) as source, zipfile.ZipFile(destination,'x',zipfile.ZIP_DEFLATED) as target:
        for entry in source.infolist():
            target.writestr(entry,(output/'mission').read_bytes() if entry.filename=='mission' else source.read(entry.filename))
    shutil.copy2(HERE/'engine-hook.lua',output/'dcs-recorder-engine-diagnostic.lua')
    files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [destination,output/'dcs-recorder-engine-diagnostic.lua']}
    (output/'manifest.json').write_text(json.dumps({'status':'Prepared; live engine capture pending','build':version,'files':files},indent=2))
    return destination


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('output',type=Path)
    parser.add_argument('--dcs',type=Path,default=Path('D:/DCS World'))
    parser.add_argument('--baseline',type=Path,default=ROOT/'package/hornet-prototype/EFM-Probe-Hornet-left-roll-400KIAS.miz')
    args=parser.parse_args()
    print(prepare(args.output,args.dcs,args.baseline))
