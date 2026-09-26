"""Package the stock-Hornet recording mission; no changes to the installed DLL."""
from pathlib import Path
import json,subprocess,zipfile

ROOT=Path(__file__).resolve().parent
DCS=Path('D:/DCS World')
BASE=ROOT/'package/hornet-prototype/EFM-Probe-Hornet-left-roll-400KIAS.miz'

def lua(script,*args):
    subprocess.run([str(DCS/'bin/luae.exe'),str(ROOT/script),*[str(a) for a in args]],check=True)

def checks(mission,count):
    lua('verify_hornet_requirements.lua',mission,DCS/'Mods/aircraft/FA-18C/entry.lua',DCS/'MissionEditor/modules/me_mission.lua')
    lua('verify_hornet_routes.lua',mission,DCS/'MissionEditor/modules/me_route.lua',count)
    lua('verify_hornet_configuration.lua',mission,DCS,count)

def pack(mission,destination):
    with zipfile.ZipFile(BASE) as src,zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as dest:
        for entry in src.infolist():
            dest.writestr(entry,mission.read_bytes() if entry.filename=='mission' else src.read(entry.filename))

def prepare():
    output=ROOT/'package/recording';output.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(BASE) as src:(output/'baseline.lua').write_bytes(src.read('mission'))
    lua('make_recording_mission.lua',output/'baseline.lua',ROOT/'record_flight_mission.lua',output/'mission')
    checks(output/'mission',1)
    destination=output/'EFM-Probe-Hornet-record.miz';pack(output/'mission',destination)
    return destination

if __name__=='__main__':print(prepare())
