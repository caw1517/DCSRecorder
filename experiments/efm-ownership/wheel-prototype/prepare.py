"""Prepare the isolated Hornet wheel/suspension diagnostic; no installation."""
import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
DCS=Path('D:/DCS World')
BASELINE=ROOT/'package/hornet-prototype/EFM-Probe-Hornet-left-roll-400KIAS.miz'
GROUND=DCS/'Mods/aircraft/FA-18C/Missions/QuickStart/Caucasus FA-18C Cold and Dark.miz'


def prepare(steering=False):
    output=ROOT/('package/wheel-steering-ready' if steering else 'package/wheel-ready')
    assert json.loads((DCS/'autoupdate.cfg').read_text(encoding='utf-8-sig'))['version']=='2.9.29.27468'
    output.mkdir(parents=True,exist_ok=False)
    for archive,name in ((BASELINE,'baseline.lua'),(GROUND,'ground.lua')):
        with zipfile.ZipFile(archive)as source:(output/name).write_bytes(source.read('mission'))
    def lua(script,*args):subprocess.run([str(DCS/'bin/luae.exe'),str(script),*map(str,args)],check=True)
    lua(ROOT/'make_recording_mission.lua',output/'baseline.lua',HERE/'capture.lua',output/'clean.lua')
    lua(ROOT/'verify_hornet_configuration.lua',output/'clean.lua',DCS,1)
    lua(HERE/'configure.lua',output/'clean.lua',output/'ground.lua',HERE/'capture.lua',output/'mission',DCS,*(['steering'] if steering else []))
    lua(ROOT/'verify_hornet_requirements.lua',output/'mission',DCS/'Mods/aircraft/FA-18C/entry.lua',DCS/'MissionEditor/modules/me_mission.lua')
    lua(ROOT/'verify_hornet_routes.lua',output/'mission',DCS/'MissionEditor/modules/me_route.lua',1)
    lua(HERE/'check_capture.lua',output/'mission',DCS,output/'fixture.log')
    subprocess.run([sys.executable,str(HERE/'analyze.py'),str(output/'fixture.log'),str(output/'fixture-analysis.json')],check=True)
    mission=output/('DCSRecorder-Wheel-Steering-Diagnostic.miz' if steering else 'DCSRecorder-Wheel-Diagnostic.miz')
    with zipfile.ZipFile(BASELINE)as source,zipfile.ZipFile(mission,'x',zipfile.ZIP_DEFLATED)as target:
        for entry in source.infolist():target.writestr(entry,(output/'mission').read_bytes() if entry.filename=='mission' else source.read(entry.filename))
    manifest=dict(mission=mission.name,sha256=hashlib.sha256(mission.read_bytes()).hexdigest(),
        ground_source_sha256=hashlib.sha256((output/'ground.lua').read_bytes()).hexdigest(),status='offline checked; live wheel mapping pending')
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(mission)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--steering',action='store_true')
    prepare(parser.parse_args().steering)
