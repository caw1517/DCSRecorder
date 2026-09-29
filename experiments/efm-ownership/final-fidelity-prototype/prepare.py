"""Prepare final combined capture from an existing normal wheels mission."""
import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def prepare(source, output, dcs):
    output.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(source) as archive:
        (output/'baseline.lua').write_bytes(archive.read('mission'))
    def lua(script, *args):
        subprocess.run([str(dcs/'bin/luae.exe'), str(script), *map(str,args)],check=True)
    lua(ROOT/'verify_hornet_configuration.lua',output/'baseline.lua',dcs,1,'Observer')
    lua(HERE/'configure.lua',output/'baseline.lua',output/'mission',dcs)
    lua(ROOT/'verify_hornet_requirements.lua',output/'mission',dcs/'Mods/aircraft/FA-18C/entry.lua',dcs/'MissionEditor/modules/me_mission.lua')
    lua(ROOT/'verify_hornet_routes.lua',output/'mission',dcs/'MissionEditor/modules/me_route.lua',1)
    lua(HERE/'check_sequence.lua',output/'mission')
    mission=output/'DCSRecorder-Final-Fidelity-Capture.miz'
    with zipfile.ZipFile(source) as archive,zipfile.ZipFile(mission,'x',zipfile.ZIP_DEFLATED) as target:
        for entry in archive.infolist():
            target.writestr(entry,(output/'mission').read_bytes() if entry.filename=='mission' else archive.read(entry.filename))
    (output/'manifest.json').write_text(json.dumps(dict(mission=mission.name,sha256=hashlib.sha256(mission.read_bytes()).hexdigest(),source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest()),indent=2))
    print(mission)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('source','output','dcs'): p.add_argument(name,type=Path)
    a=p.parse_args();prepare(a.source,a.output,a.dcs)
