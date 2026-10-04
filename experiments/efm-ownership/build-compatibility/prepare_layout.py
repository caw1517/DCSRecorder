"""Prepare an isolated AI object with read-only SDK/native field observation."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile
from prepare import data,HERE

MODULE='DCSRecorder-Hornet-Layout-Check'
BINARY='HornetLayoutProbe'
MISSION='046-Hornet-Layout-Check.miz'

def prepare(source,donor,output,dcs):
    if json.loads((dcs/'autoupdate.cfg').read_text(encoding='utf-8-sig'))['version']!='2.9.30.28536':
        raise ValueError('Read-only diagnostic requires DCS 2.9.30.28536')
    if output.exists():raise ValueError('Use a fresh output directory')
    entries,m=data.read(source)
    rows=data.aircraft(m)
    if len(rows)!=2 or sorted(r['unit']['name'] for r in rows)!=['Observer','Probe']:
        raise ValueError('Requires known two-aircraft ownership fixture')
    for row in rows:
        unit=row['unit']
        if unit['name']=='Probe':
            assert unit['type']=='DCSRecorder-Hornet-Probe' and unit['skill']!='Player'
            unit['type']=MODULE
        else:assert unit['type']=='FA-18C_hornet' and unit['skill']=='Player'
    script=(HERE/'layout_mission.lua').read_text()
    m['trigrules'][1]['actions'][1]['text']=script
    m['trigrules'][1]['comment']='Read-only object layout observation'
    m['trig']['actions'][1]='a_do_script('+data.serialize(script)+');'
    m['descriptionText']='READ-ONLY OBJECT LAYOUT CHECK. Click Fly, let the mission run for 20 seconds, then exit DCS normally. Your aircraft is a stock Hornet. The diagnostic AI lead flies normally while its object identity and fields are read. No native setters or hooks, hold, playback or release run.'
    output.mkdir(parents=True)
    mod=output/MODULE
    (mod/'bin').mkdir(parents=True)
    for name in ('entry.lua','aircraft.lua'):
        text=(donor/name).read_text(encoding='utf-8-sig').replace('DCSRecorder-Hornet-Probe',MODULE)
        if name=='entry.lua':text=text.replace('HornetProbe',BINARY).replace('DCS Recorder Hornet Prototype','DCS Recorder Read-only Layout Check')
        (mod/name).write_text(text,encoding='utf-8')
    for name in ('Cockpit','Datalinks','Liveries'):shutil.copytree(donor/name,mod/name)
    (mod/'Liveries/DCSRecorder-Hornet-Probe').rename(mod/'Liveries'/MODULE)
    shutil.copy2(HERE.parent/'build/Release'/f'{BINARY}.dll',mod/'bin'/f'{BINARY}.dll')
    mission='mission = '+data.serialize(m)
    (output/'mission.lua').write_text(mission,encoding='utf-8')
    for script_name,args in (
        ('verify_hornet_requirements.lua',[output/'mission.lua',dcs/'Mods/aircraft/FA-18C/entry.lua',dcs/'MissionEditor/modules/me_mission.lua']),
        ('verify_hornet_routes.lua',[output/'mission.lua',dcs/'MissionEditor/modules/me_route.lua',2]),
        ('verify_hornet_configuration.lua',[output/'mission.lua',dcs,2])):
        subprocess.run([str(dcs/'bin/luae.exe'),str(HERE.parent/script_name),*map(str,args)],check=True)
    with zipfile.ZipFile(output/MISSION,'x',zipfile.ZIP_DEFLATED) as z:
        for name,raw in entries.items():z.writestr(name,mission.encode() if name=='mission' else raw)
    files=[p for p in mod.rglob('*') if p.is_file()]+[output/MISSION]
    report=dict(status='Read-only object layout diagnostic; live verification pending',build='2.9.30.28536',module=MODULE,
                files={p.relative_to(output).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],files=len(files),mission=MISSION)))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('donor',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--dcs',type=Path,default=Path('D:/DCS World'));a=p.parse_args()
    prepare(a.source,a.donor,a.output,a.dcs)
