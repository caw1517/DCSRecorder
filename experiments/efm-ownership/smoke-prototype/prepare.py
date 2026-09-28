"""Separate smoke observation mission; packaged game assets remain local."""
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DCS = Path('D:/DCS World')
OUTPUT = ROOT/'package/smoke-diagnostic'
BASELINE = ROOT/'package/hornet-prototype/EFM-Probe-Hornet-left-roll-400KIAS.miz'


def lua(script, *args):
    subprocess.run([str(DCS/'bin/luae.exe'), str(script), *map(str,args)], check=True)


def prepare():
    assert json.loads((DCS/'autoupdate.cfg').read_text(encoding='utf-8-sig'))['version']=='2.9.29.27468'
    OUTPUT.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(BASELINE) as archive:
        (OUTPUT/'baseline.lua').write_bytes(archive.read('mission'))
    (OUTPUT/'description.txt').write_text(
        'SMOKE OBSERVATION ONLY. Stock Hornet with WHITE smoke generator on SMK station 10. '
        'Bind Controls > F/A-18C Sim > General > Smoke Device - ON/OFF. '
        'F10 > Smoke diagnostic > Start capture. Observe smoke externally. '
        'Mark visibly OFF and hold five seconds; toggle smoke ON, mark visibly ON and hold five seconds; '
        'repeat OFF/ON/OFF, then Stop capture. Markers do not operate smoke. '
        'Keep DCS open for log collection. Two-minute maximum, 5 Hz observation. '
        'This diagnostic does not create a flight-library entry or replay smoke.', encoding='utf-8')
    lua(ROOT/'make_recording_mission.lua', OUTPUT/'baseline.lua', HERE/'capture.lua', OUTPUT/'clean.lua', OUTPUT/'description.txt')
    lua(ROOT/'verify_hornet_configuration.lua', OUTPUT/'clean.lua', DCS, 1)
    lua(HERE/'configure.lua', OUTPUT/'clean.lua', OUTPUT/'mission', DCS)
    lua(ROOT/'verify_hornet_requirements.lua', OUTPUT/'mission', DCS/'Mods/aircraft/FA-18C/entry.lua', DCS/'MissionEditor/modules/me_mission.lua')
    lua(ROOT/'verify_hornet_routes.lua', OUTPUT/'mission', DCS/'MissionEditor/modules/me_route.lua', 1)
    lua(HERE/'check_capture.lua', OUTPUT/'mission')
    destination=OUTPUT/'DCSRecorder-Smoke-Diagnostic.miz'
    with zipfile.ZipFile(BASELINE) as source, zipfile.ZipFile(destination,'x',zipfile.ZIP_DEFLATED) as target:
        for entry in source.infolist():
            target.writestr(entry, (OUTPUT/'mission').read_bytes() if entry.filename=='mission' else source.read(entry.filename))
    manifest={'mission':destination.name,'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),
              'station':10,'CLSID':'{INV-SMOKE-WHITE}','status':'offline checked; live observation pending'}
    (OUTPUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print(destination)


if __name__=='__main__':prepare()
