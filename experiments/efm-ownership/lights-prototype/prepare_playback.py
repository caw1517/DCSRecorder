"""Build a separate SDK-only actuator from one validated real light capture."""
import argparse
import hashlib
import json
import math
import shutil
import subprocess
import zipfile
from pathlib import Path
from analyze import analyze

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
DCS=Path('D:/DCS World')
MODULE='DCSRecorder-Hornet-Lights'
BINARY='HornetLightsProbe'
MISSION='DCSRecorder-Lights-Playback.miz'
CHANNELS=[0,3,5,88,190,191,192,193,210,212]


def prepare(log,output):
    assert json.loads((DCS/'autoupdate.cfg').read_text(encoding='utf-8-sig'))['version']=='2.9.29.27468'
    summary=analyze(log)
    rows=[]
    for line in log.read_text(errors='replace').splitlines():
        if 'DCSLIGHT,1,DATA,' not in line:continue
        fields=line.split('DCSLIGHT,1,DATA,',1)[1].split(',')
        rows.append([float(fields[1]),*map(float,fields[3:])])
    assert len(rows)==summary['samples']
    origin=rows[0][0]
    for row in rows:
        row[0]-=origin
        assert len(row)==11 and all(math.isfinite(v) and 0<=v<=1 for v in row[1:])
    output.mkdir(parents=True,exist_ok=False)
    mod=output/MODULE;(mod/'bin').mkdir(parents=True)
    donor=Path.home()/'Saved Games/DCS/Mods/aircraft/DCSRecorder-Hornet-Probe'
    for name in ('entry.lua','aircraft.lua'):
        text=(donor/name).read_text(encoding='utf-8-sig')
        assert 'DCSRecorder-Hornet-Probe' in text
        text=text.replace('DCSRecorder-Hornet-Probe',MODULE)
        if name=='entry.lua':text=text.replace('HornetProbe',BINARY).replace('DCS Recorder Hornet Prototype','DCS Recorder Captured Lights Test')
        (mod/name).write_text(text,encoding='utf-8')
    for name in ('Cockpit','Datalinks','Liveries'):shutil.copytree(donor/name,mod/name)
    (mod/'Liveries/DCSRecorder-Hornet-Probe').rename(mod/'Liveries'/MODULE)
    shutil.copy2(ROOT/('build/Release/'+BINARY+'.dll'),mod/('bin/'+BINARY+'.dll'))
    tape=['DCS_LIGHT_PROTOTYPE_V1',str(len(rows)),' '.join(map(str,CHANNELS))]
    tape+=[' '.join(format(v,'.12g') for v in row) for row in rows]
    (mod/'bin/exterior-state.txt').write_text('\n'.join(tape)+'\n',encoding='ascii')
    subprocess.run([str(ROOT/'build/Release/lights_playback_check.exe'),str(mod/('bin/'+BINARY+'.dll'))],check=True)
    # Fixture logs are local diagnostics, not aircraft assets.
    baseline=ROOT/'package/hornet-prototype/EFM-Probe-Hornet-left-roll-400KIAS.miz'
    with zipfile.ZipFile(baseline)as source:(output/'baseline.lua').write_bytes(source.read('mission'))
    description=('CAPTURED LIGHT PLAYBACK. Leave Active Pause on until F10 > Light playback > Start captured light sequence. '
        'Start releases your aircraft and spawns the separate playback lead. F2 to the lead; watch position/formation dim and bright, '
        'strobe dim and bright, landing/taxi and off. Allow about 80 seconds until lead removal. This test replays actual sampled '
        'gear/light arguments on an ordinary AI route, not recorded motion or engine state. Leave DCS open for log collection.')
    config='return {aircraft='+json.dumps(MODULE)+',duration='+str(rows[-1][0])+',description='+json.dumps(description)+',markers={\n'
    config+=''.join('{time='+str(p['time']-origin)+',segment='+json.dumps(p['name'])+'},\n' for p in summary['phases'].values())+'}}\n'
    (output/'config.lua').write_text(config)
    def lua(script,*args):subprocess.run([str(DCS/'bin/luae.exe'),str(script),*map(str,args)],check=True)
    lua(ROOT/'state-prototype/make_playback.lua',output/'baseline.lua',HERE/'playback_mission.lua',output/'config.lua',output/'day-mission.lua')
    # Serialize the complete mission after setting nighttime; do not patch archive bytes.
    (output/'night.lua').write_text("dofile(arg[1]);mission.start_time=22*3600;local f=assert(io.open(arg[2],'wb'));"
        "local function s(v)if type(v)=='string'then return string.format('%q',v)end;"
        "if type(v)~='table'then return tostring(v)end;local r={'{'};for k,x in pairs(v)do r[#r+1]='['..s(k)..']='..s(x)..','end;"
        "r[#r+1]='}';return table.concat(r)end;f:write('mission = ',s(mission));f:close()")
    lua(output/'night.lua',output/'day-mission.lua',output/'mission')
    lua(ROOT/'verify_hornet_requirements.lua',output/'mission',DCS/'Mods/aircraft/FA-18C/entry.lua',DCS/'MissionEditor/modules/me_mission.lua')
    lua(ROOT/'verify_hornet_routes.lua',output/'mission',DCS/'MissionEditor/modules/me_route.lua',2)
    lua(ROOT/'verify_hornet_configuration.lua',output/'mission',DCS,2)
    lua(HERE/'check_playback_mission.lua',HERE/'playback_mission.lua')
    destination=output/MISSION
    with zipfile.ZipFile(baseline)as source,zipfile.ZipFile(destination,'x',zipfile.ZIP_DEFLATED)as target:
        for entry in source.infolist():target.writestr(entry,(output/'mission').read_bytes() if entry.filename=='mission' else source.read(entry.filename))
    assets=[destination,*[p for p in mod.rglob('*') if p.is_file() and 'state-logs' not in p.parts]]
    manifest=dict(module=MODULE,binary=BINARY,mission=MISSION,source_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),
        samples=len(rows),origin=origin,duration=rows[-1][0],channels=CHANNELS,status='offline checked; live retention/rendering pending',
        files={p.relative_to(output).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in assets})
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(destination)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('log',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();prepare(args.log,args.output)
