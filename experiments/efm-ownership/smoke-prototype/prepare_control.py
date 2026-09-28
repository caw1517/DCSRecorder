"""Add a synthetic smoke-control test to a copy of the accepted playback mission."""
import hashlib
import json
import zipfile
from pathlib import Path
from prepare import ROOT, HERE, DCS, lua

SAVED=Path('C:/Users/w_can/Saved Games/DCS')
SOURCE=SAVED/'Missions/DCSRecorder-Playback-a2770a03.miz'
OUTPUT=ROOT/'package/smoke-control'


def prepare():
    assert json.loads((DCS/'autoupdate.cfg').read_text(encoding='utf-8-sig'))['version']=='2.9.29.27468'
    binary=SAVED/'Mods/aircraft/DCSRecorder-Hornet-Engine-Staged/bin'
    tape=binary/'recorded-flight.txt'
    assert hashlib.sha256(tape.read_bytes()).hexdigest()=='2faec4156e66c0c730969288474161d565270946c855aa37873ae8bf53810930', 'Activate the accepted Test flight first'
    descriptor=(binary.parent/'aircraft.lua').read_bytes()
    assert b'{INV-SMOKE-WHITE}' in descriptor
    OUTPUT.mkdir(parents=True,exist_ok=False)
    with zipfile.ZipFile(SOURCE) as archive:
        (OUTPUT/'baseline.lua').write_bytes(archive.read('mission'))
    lua(HERE/'configure_control.lua',OUTPUT/'baseline.lua',HERE/'control.lua',OUTPUT/'mission')
    lua(HERE/'check_control.lua',HERE/'control.lua')
    lua(ROOT/'verify_hornet_requirements.lua',OUTPUT/'mission',DCS/'Mods/aircraft/FA-18C/entry.lua',DCS/'MissionEditor/modules/me_mission.lua')
    lua(ROOT/'verify_hornet_routes.lua',OUTPUT/'mission',DCS/'MissionEditor/modules/me_route.lua',2)
    destination=OUTPUT/'DCSRecorder-Smoke-Control-Test.miz'
    with zipfile.ZipFile(SOURCE) as source,zipfile.ZipFile(destination,'x',zipfile.ZIP_DEFLATED) as target:
        for entry in source.infolist():
            target.writestr(entry,(OUTPUT/'mission').read_bytes() if entry.filename=='mission' else source.read(entry.filename))
    (OUTPUT/'manifest.json').write_text(json.dumps(dict(mission=destination.name,
        sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        tape_sha256=hashlib.sha256(tape.read_bytes()).hexdigest(),
        status='offline checked; rendered smoke not verified'),indent=2))
    print(destination)


if __name__=='__main__':prepare()
