"""Prepare a separate airborne real-object hold control from a validated take."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

HERE=Path(__file__).resolve().parent
EFM=HERE.parent
ROOT=EFM.parent.parent
sys.path.insert(0,str(EFM))
from prepare_staged_playback import prepare
from recorded_flight import read
spec=importlib.util.spec_from_file_location('fixture_data',ROOT/'companion/mission-identity-probe.prototype.py')
data=importlib.util.module_from_spec(spec);spec.loader.exec_module(data)
MODULE='DCSRecorder-Hornet-Held-Test'
BINARY='HornetHeldProbe'
MISSION='040-Hornet-Held-Start.miz'

def build(recording,output,baseline,donor,dcs,*,snapshot=False):
    module='DCSRecorder-Hornet-Snapshot-Test' if snapshot else MODULE
    binary='HornetSnapshotProbe' if snapshot else BINARY
    mission='042-Hornet-Snapshot-Hold.miz' if snapshot else MISSION
    output=output.resolve()
    if output.exists():raise ValueError('Use a fresh package directory')
    metadata,samples,_=read(recording)
    if snapshot:
        first=samples[0]
        if not all(metadata[k] for k in ('exterior_available','engine_available','lights_available','canopy_available','wheels_available','smoke_available')):
            raise ValueError('Snapshot control requires all supported capture groups')
        if (first[11]<.5 and min(first[12:15])<.9) or not metadata['smoke_events'][0]['on'] or max(first[35:42])<.1:
            raise ValueError('Snapshot control requires initial gear down or brake extended, plus smoke ON and nonzero lights')
    base=prepare(recording,output/'base',baseline,donor,dcs,held_diagnostic=True)
    metadata=base['recording']
    if not all(metadata[k] for k in ('exterior_available','engine_available','lights_available','canopy_available','wheels_available','smoke_available')):
        raise ValueError('Hold control requires complete supported initial capture')
    mod=output/module
    shutil.copytree(output/'base'/base['module'],mod)
    for name in ('entry.lua','aircraft.lua'):
        path=mod/name
        path.write_text(path.read_text(encoding='utf-8').replace(base['module'],module).replace(base['binary'],binary),encoding='utf-8')
    # Rename only a freshly generated livery directory, inside this package.
    old=(mod/'Liveries'/base['module']).resolve();new=(mod/'Liveries'/module).resolve()
    assert old.is_relative_to(output) and new.is_relative_to(output)
    old.rename(new)
    shutil.copy2(EFM/'build/Release'/f'{binary}.dll',mod/'bin'/f'{binary}.dll')
    m=data.LuaData((output/'base/mission').read_text(encoding='utf-8')).mission()
    groups=m['coalition']['blue']['country'][1]['plane']['group']
    player=None
    for g in groups.values():
        u=g['units'][1]
        if u['name']=='Observer':player=g
        else:
            assert u['name']=='StagedPlayback'
            u['type']=module;g['lateActivation']=False
    assert player is not None
    witness=copy.deepcopy(player);unit=witness['units'][1]
    witness['groupId']=max(g['groupId'] for g in groups.values())+1
    unit['unitId']=max(g['units'][1]['unitId'] for g in groups.values())+1
    witness['name']='SceneWitnessGroup';unit['name']='SceneWitness';unit['skill']='High'
    # The unrelated stock aircraft demonstrates that Active Pause is not global.
    unit['y']+=800;witness['y']+=800
    for point in witness['route']['points'].values():point['y']+=800
    groups[max(groups)+1]=witness
    c=base['initial']
    config=dict(token_high=c['token_high'],token_low=c['token_low'],smoke=c['smoke_events'][0]['on'])
    if snapshot:
        first=samples[0]
        config['expected']={21:first[11],38:first[42]}
        for channels,values in (([0,3,5,9,10,11,12,13,14,15,16,17,18],first[12:25]),
                ([28,29,89,90],first[25:29]),([88,190,191,192,193,210,212],first[35:42]),
                ([1,6,4,101,103,102,2],first[43:50])):
            config['expected'].update(zip(channels,values))
    script='DCSR_HELD_CONFIG='+data.serialize(config)+'\n'+(HERE/'mission.lua').read_text(encoding='utf-8')
    lights_rule=copy.deepcopy(m['trigrules'][2])
    lights_trig={key:copy.deepcopy(value[2]) for key,value in m['trig'].items() if 2 in value}
    m['trigrules']={1:dict(comment='Isolated visible real-object hold',predicate='triggerStart',eventlist='',rules={},
        actions={1:dict(predicate='a_set_command',command=816),2:dict(predicate='a_do_script',text=script)})}
    m['trig']={key:{} for key in ('actions','conditions','func','funcStartup','flag')}
    m['trig']['actions'][1]='a_set_command(816);a_do_script('+data.serialize(script)+');'
    m['trig']['conditions'][1]='return(true)';m['trig']['flag'][1]=True
    m['trig']['funcStartup'][1]='if mission.trig.conditions[1]() then mission.trig.actions[1]() end'
    m['trigrules'][2]=lights_rule
    for key,value in lights_trig.items():m['trig'][key][2]=value
    m['descriptionText']='HELD START CONTROL. Click Fly and inspect the lead ahead for 30 seconds. Your stock Hornet is held by Active Pause. The real playback aircraft should stay at the first recorded pose with supported state and engine sound held. A third stock aircraft continues flying. Do not toggle pause. No release/countdown is offered. Exit when the observation-complete message appears, and report drift, flicker or sound changes.'
    (output/'mission.lua').write_text('mission = '+data.serialize(m),encoding='utf-8')
    # Only generated content is executed by the installed fixture validators.
    for script_name,args in (
        ('verify_hornet_requirements.lua',[output/'mission.lua',dcs/'Mods/aircraft/FA-18C/entry.lua',dcs/'MissionEditor/modules/me_mission.lua']),
        ('verify_hornet_routes.lua',[output/'mission.lua',dcs/'MissionEditor/modules/me_route.lua',3]),
        ('verify_hornet_configuration.lua',[output/'mission.lua',dcs,3,'StagedPlayback'])):
        subprocess.run([str(dcs/'bin/luae.exe'),str(EFM/script_name),*map(str,args)],check=True)
    with zipfile.ZipFile(output/'base/DCSRecorder-Staged-Playback.miz') as src,zipfile.ZipFile(output/mission,'x',zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():dst.writestr(item,(output/'mission.lua').read_bytes() if item.filename=='mission' else src.read(item.filename))
    # The copied accepted DLL is retained as package source evidence, but only
    # the new module's named binary is installed/registered.
    files=[p for p in mod.rglob('*') if p.is_file() and (p.suffix.lower()!='.dll' or p.name==f'{binary}.dll')]
    files.append(output/mission)
    manifest=dict(profile='snapshot-airborne-v1' if snapshot else 'held-start-airborne-v1',dcs_build=base['dcs_build'],module=module,binary=binary,mission=mission,
        recording=metadata,initial=c,status='Prepared; real-object hold awaits live evidence',
        files={p.relative_to(output).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=manifest['status'],module=module,mission=mission,files=len(files)),indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('recording',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--baseline',type=Path,required=True);p.add_argument('--donor',type=Path,required=True)
    p.add_argument('--dcs',type=Path,default=Path('D:/DCS World'));p.add_argument('--snapshot',action='store_true');a=p.parse_args()
    build(a.recording,a.output,a.baseline,a.donor,a.dcs,snapshot=a.snapshot)
