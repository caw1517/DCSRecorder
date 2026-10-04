"""Make an additive snapshot capture mission from a current normal practice mission."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import zipfile

HERE=Path(__file__).resolve().parent
EFM=HERE.parent
spec=importlib.util.spec_from_file_location('mission_data',EFM.parent.parent/'companion/mission-identity-probe.prototype.py')
data=importlib.util.module_from_spec(spec);spec.loader.exec_module(data)


def prepare(source,output,dcs):
    if json.loads((dcs/'autoupdate.cfg').read_text(encoding='utf-8-sig'))['version']!='2.9.30.28536':
        raise ValueError('Snapshot capture requires the current bounded build profile')
    with zipfile.ZipFile(source) as archive:
        m=data.LuaData(archive.read('mission').decode('utf-8-sig')).mission()
    output.mkdir(parents=True,exist_ok=False)
    baseline=output/'baseline.lua'
    baseline.write_text('mission = '+data.serialize(m),encoding='utf-8')
    subprocess.run([str(dcs/'bin/luae.exe'),str(EFM/'verify_hornet_configuration.lua'),str(baseline),str(dcs),'1','Observer'],check=True)
    startup=m['trigrules'][1]['actions'][1]['text']
    for required in ('DCSRECORDER_WHEELS=true','DCSRECORDER_SMOKE=true','capture_build,2.9.30.28536','frame-batch-v1'):
        if required not in startup:raise ValueError('Source must be a current complete normal practice mission: '+required)
    assert len(m['trigrules'])==2, 'Unexpected source triggers'
    description=('SNAPSHOT CAPTURE. Lights come on automatically. Fly wings level at about 200 KIAS. '
        'Before recording: lower gear, extend speed brake and turn white smoke ON. '
        'Keep canopy closed and use enough power to stay above 70 m/s (136 knots ground speed). '
        'Once stable and nearly level, F10 > DCS Recorder > Start recording. '
        'Hold this state for 8-10 seconds, then F10 > DCS Recorder > Stop recording. '
        'Exit the mission normally after the save message. Do not use Active Pause during recording.')
    m['descriptionText']=description
    prompt='trigger.action.outText('+data.serialize(description)+',60)'
    startup+='\n'+prompt
    m['trigrules'][1]['actions'][1]['text']=startup
    m['trig']['actions'][1]='a_do_script('+data.serialize(startup)+');'
    lights=m['trigrules'][2]
    lights['comment']='Snapshot capture exterior lights on'
    for action in lights['actions'].values():
        assert action['predicate']=='a_cockpit_perform_clickable_action'
        action['value']=1
    # Resolve the installed Hornet's master-light command rather than assuming IDs.
    resolver=output/'resolve_lights.lua'
    resolver.write_text("dofile(arg[1]..'/Mods/aircraft/FA-18C/Cockpit/Scripts/devices.lua')\n"
        "dofile(arg[1]..'/Mods/aircraft/FA-18C/Cockpit/Scripts/command_defs.lua')\n"
        "print(devices.HOTAS,hotas_commands.THROTTLE_EXTERIOR_LIGHTS)\n")
    result=subprocess.run([str(dcs/'bin/luae.exe'),str(resolver),str(dcs)],capture_output=True,text=True,check=True)
    device,command=map(int,result.stdout.split())
    lights['actions'][5]=dict(predicate='a_cockpit_perform_clickable_action',cockpit_device=device,
        command=command,value=1,COCKPIT_ADDITIONAL_PLUGIN='')
    m['trig']['actions'][2]=''.join('a_cockpit_perform_clickable_action(%d,%d,1,"");'%(a['cockpit_device'],a['command'])
        for a in lights['actions'].values())+'mission.trig.func[2]=nil;'
    groups=m['coalition']['blue']['country'][1]['plane']['group']
    assert len(groups)==1
    group=next(iter(groups.values()));unit=group['units'][1]
    assert unit['name']=='Observer' and unit['type']=='FA-18C_hornet' and unit['skill']=='Player'
    unit['speed']=105
    for i,point in group['route']['points'].items():point['speed']=105;point['ETA']=(i-1)*20000/105
    script=output/'mission.lua'
    script.write_text('mission = '+data.serialize(m),encoding='utf-8')
    for validator,args in (
        ('verify_hornet_requirements.lua',[script,dcs/'Mods/aircraft/FA-18C/entry.lua',dcs/'MissionEditor/modules/me_mission.lua']),
        ('verify_hornet_routes.lua',[script,dcs/'MissionEditor/modules/me_route.lua',1]),
        ('held-start/check_capture.lua',[script,dcs])):
        subprocess.run([str(dcs/'bin/luae.exe'),str(EFM/validator),*map(str,args)],check=True)
    mission=output/'041-Hornet-Snapshot-Capture.miz'
    with zipfile.ZipFile(source) as src,zipfile.ZipFile(mission,'x',zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():dst.writestr(item,script.read_bytes() if item.filename=='mission' else src.read(item.filename))
    manifest=dict(mission=mission.name,sha256=hashlib.sha256(mission.read_bytes()).hexdigest(),
        source=str(source.resolve()),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        status='Prepared; fresh source recording and live snapshot acceptance pending')
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--dcs',type=Path,default=Path('D:/DCS World'));a=p.parse_args()
    prepare(a.source,a.output,a.dcs)
