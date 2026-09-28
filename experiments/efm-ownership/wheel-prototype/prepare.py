"""Prepare the isolated Hornet wheel/suspension diagnostic; no installation."""
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
DCS=Path('D:/DCS World')
OUTPUT=ROOT/'package/wheel-ready'
BASELINE=ROOT/'package/hornet-prototype/EFM-Probe-Hornet-left-roll-400KIAS.miz'
GROUND=DCS/'Mods/aircraft/FA-18C/Missions/QuickStart/Caucasus FA-18C Cold and Dark.miz'


def prepare():
    assert json.loads((DCS/'autoupdate.cfg').read_text(encoding='utf-8-sig'))['version']=='2.9.29.27468'
    OUTPUT.mkdir(parents=True,exist_ok=False)
    for archive,name in ((BASELINE,'baseline.lua'),(GROUND,'ground.lua')):
        with zipfile.ZipFile(archive)as source:(OUTPUT/name).write_bytes(source.read('mission'))
    def lua(script,*args):subprocess.run([str(DCS/'bin/luae.exe'),str(script),*map(str,args)],check=True)
    lua(ROOT/'make_recording_mission.lua',OUTPUT/'baseline.lua',HERE/'capture.lua',OUTPUT/'clean.lua')
    lua(ROOT/'verify_hornet_configuration.lua',OUTPUT/'clean.lua',DCS,1)
    lua(HERE/'configure.lua',OUTPUT/'clean.lua',OUTPUT/'ground.lua',HERE/'capture.lua',OUTPUT/'mission',DCS)
    lua(ROOT/'verify_hornet_requirements.lua',OUTPUT/'mission',DCS/'Mods/aircraft/FA-18C/entry.lua',DCS/'MissionEditor/modules/me_mission.lua')
    lua(ROOT/'verify_hornet_routes.lua',OUTPUT/'mission',DCS/'MissionEditor/modules/me_route.lua',1)
    lua(HERE/'check_capture.lua',OUTPUT/'mission',DCS,OUTPUT/'fixture.log')
    subprocess.run([sys.executable,str(HERE/'analyze.py'),str(OUTPUT/'fixture.log'),str(OUTPUT/'fixture-analysis.json')],check=True)
    mission=OUTPUT/'DCSRecorder-Wheel-Diagnostic.miz'
    with zipfile.ZipFile(BASELINE)as source,zipfile.ZipFile(mission,'x',zipfile.ZIP_DEFLATED)as target:
        for entry in source.infolist():target.writestr(entry,(OUTPUT/'mission').read_bytes() if entry.filename=='mission' else source.read(entry.filename))
    manifest=dict(mission=mission.name,sha256=hashlib.sha256(mission.read_bytes()).hexdigest(),
        ground_source_sha256=hashlib.sha256((OUTPUT/'ground.lua').read_bytes()).hexdigest(),status='offline checked; live wheel mapping pending')
    (OUTPUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(mission)


if __name__=='__main__':prepare()
