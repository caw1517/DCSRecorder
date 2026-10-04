"""Build the separate, real-take-bound ground hold/release experiment."""
from pathlib import Path
import copy,hashlib,importlib.util,json,math,shutil,subprocess,sys,zipfile

HERE=Path(__file__).resolve().parent
WORK=HERE.parent
REPO=Path('E:/Projects/DCS_Recorder')
EFM=REPO/'experiments/efm-ownership'
spec=importlib.util.spec_from_file_location('mission_data',REPO/'companion/mission-identity-probe.prototype.py')
data=importlib.util.module_from_spec(spec);spec.loader.exec_module(data)
MODULE='DCSRecorder-Hornet-Ground-Test'
BINARY='HornetGroundProbe'
MISSION='049-Hornet-Ground-Hold-Release.miz'
CONTROL='DCSRecorderGroundControl'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def replace(text,old,new):
    assert text.count(old)==1,old
    return text.replace(old,new)

def build(out):
    seed=EFM/'results/countdown-release-2026-10-01/gear-package-v5'
    manifest=json.loads((seed/'manifest.json').read_text(encoding='utf-8-sig'))
    for name,sha in manifest['files'].items():assert digest(seed/'payload'/name)==sha,name
    assert not out.exists()
    out.mkdir(parents=True)
    payload=out/'payload'
    mod=payload/'Mods/aircraft'/MODULE
    oldmod=seed/'payload/Mods/aircraft'/manifest['module']
    shutil.copytree(oldmod,mod,ignore=shutil.ignore_patterns('*.dll'))
    for name in ('entry.lua','aircraft.lua'):
        p=mod/name;p.write_text(p.read_text(encoding='utf-8-sig').replace(manifest['module'],MODULE).replace(manifest['binary'],BINARY),encoding='utf-8')
    livery=mod/'Liveries'/manifest['module']
    if livery.exists():livery.rename(mod/'Liveries'/MODULE)
    shutil.copy2(WORK/'ground-build/Release'/f'{BINARY}.dll',mod/'bin'/f'{BINARY}.dll')
    for name in ('recorded-flight.txt','recorded-flight.json'):shutil.copy2(WORK/'ground-tape'/name,mod/'bin'/name)
    metadata=json.loads((WORK/'ground-tape/recorded-flight.json').read_text())
    initial=json.loads((WORK/'ground-tape/initial.json').read_text())
    first=initial['sample'];raw=initial['raw']
    config=dict(token_high=initial['high'],token_low=initial['low'],expected={21:first[11],38:first[42]},
                smoke_events=dict(enumerate(metadata['smoke_events'],1)),duration=metadata['duration'],minimum_hold=30,ground=True)
    for channels,values in (([0,3,5,9,10,11,12,13,14,15,16,17,18],first[12:25]),
            ([28,29,89,90],first[25:29]),([88,190,191,192,193,210,212],first[35:42]),
            ([1,6,4,101,103,102,2],first[43:50])):config['expected'].update(zip(channels,values))
    # Begin with the already reviewed loaded-field shape from airborne acceptance.
    with zipfile.ZipFile(seed/'payload/Missions'/manifest['mission']) as z:entries={n:z.read(n) for n in z.namelist()}
    m=data.LuaData(entries['mission'].decode('utf-8-sig')).mission()
    p=data.LuaData((seed/'payload/Scripts/DCSRecorderReleaseControl/expected.lua').read_text(encoding='utf-8'));p.take('return');reference=p.value()
    for field,value in reference['mission'].items():m[field]=copy.deepcopy(value)
    capture=data.LuaData((WORK/'hot-ground-capture-package-v2/mission.lua').read_text()).mission()
    for field in ('theatre','weather','date','start_time'):m[field]=copy.deepcopy(capture[field])
    groups=m['coalition']['blue']['country'][1]['plane']['group']
    heading=float(format(math.atan2(float(raw['fz']),float(raw['fx'])),'.14g'))
    for group in groups.values():
        u=group['units'][1];name=u['name']
        if name=='SceneWitness':
            x,z=first[1]+500,first[3]+600;alt=500;speed=140
        else:
            offset=45.72 if name=='Observer' else 0
            x,z=first[1]-offset*math.cos(heading),first[3]-offset*math.sin(heading)
            x,z=float(format(x,'.12g')),float(format(z,'.12g'))
            alt=first[2];speed=0
            if name=='StagedPlayback':u['type']=MODULE
        u.update(x=x,y=z,alt=alt,alt_type='BARO',heading=heading,psi=-heading,speed=speed)
        for key in ('parking','parking_id','airdromeId','linkUnit','helipadId'):u.pop(key,None)
        group.update(x=x,y=z,lateActivation=False,uncontrolled=False,start_time=0)
        base=copy.deepcopy(group['route']['points'][1])
        for key in ('airdromeId','helipadId','linkUnit'):base.pop(key,None)
        base.update(x=x,y=z,alt=alt,alt_type='BARO',speed=speed,speed_locked=True,ETA=0,ETA_locked=True,
                    type='Turning Point' if name=='SceneWitness' else 'TakeOffGroundHot',
                    action='Turning Point' if name=='SceneWitness' else 'From Ground Area Hot',
                    task=dict(id='ComboTask',params=dict(tasks={})))
        if name=='SceneWitness':
            second=copy.deepcopy(base);second.update(x=x+20000*math.cos(heading),y=z+20000*math.sin(heading),ETA=20000/140,ETA_locked=False)
            group['route']['points']={1:base,2:second}
        else:group['route']['points']={1:base}
    script=(EFM/'release-start/mission.lua').read_text()
    script=replace(script,"s.phase='waiting';emit('READY,'..session..','..generation)","s.phase='waiting';s.ready_time=timer.getTime();emit('READY,'..session..','..generation)")
    script=replace(script,"notice('Ready. Inspect the held lead, then F10 > DCS Recorder release test > Start playback. Do not toggle Active Pause.')",
        "notice('Ready. Inspect the ground aircraft for 30 seconds. Wait for Inspection complete before requesting playback. Do not toggle Active Pause.')")
    script=replace(script,"    elseif s.phase=='waiting' or s.phase=='countdown' then",'''    elseif s.phase=='waiting' or s.phase=='countdown' then
        if not s.inspected and now-s.ready_time>=c.minimum_hold then
            s.inspected=true;emit('INSPECTION_COMPLETE');notice('Inspection complete. Report the held aircraft appearance before starting playback.')
        end''')
    script=replace(script,"    s.phase='countdown';s.countdown_time=timer.getTime();emit",'''    if not s.inspected then notice('Complete the 30-second inspection first.');return end
    s.phase='countdown';s.countdown_time=timer.getTime();emit''')
    script=replace(script,"    local p,v=u:getPosition(),u:getVelocity();local values={}",'''    local p,v=u:getPosition(),u:getVelocity();local values={}
    if name~='SceneWitness' then
        local h=land.getHeight({x=p.p.x,y=p.p.z})
        local life,life0=u:getLife(),u:getLife0()
        emit(string.format('CONTACT,%s,%s,%.9f,%.9f,%s,%d,%.12g,%.12g,%.12g,%.12g,%d',
            s.phase,name,timer.getTime(),1000*u:getDrawArgumentValue(996),tostring(u:getID()),u:inAir() and 1 or 0,
            h,p.p.y-h,life,life0,land.getSurfaceType({x=p.p.x,y=p.p.z})))
    end''')
    script=script.replace('DCS Recorder release test','DCS Recorder ground test')
    script=script.replace('Watch first movement and smoke, then let the short recording finish.','Watch the first taxi movement. This test removes the aircraft at the end; parked completion is a later test.')
    startup='DCSR_RELEASE_CONFIG='+data.serialize(config)+'\n'+script
    m['trigrules'][1]['comment']='Ground snapshot, 30-second held inspection and three-second release'
    m['trigrules'][1]['actions'][2]['text']=startup
    m['trig']['actions'][1]='a_set_command(816);a_do_script('+data.serialize(startup)+');'
    description=('GROUND HOLD AND RELEASE. Click Fly and wait for Ready. Inspect the lead aircraft on the ground for 30 seconds. '
        'Watch for sliding, bouncing, sinking, damage or state changes. The stock witness aircraft and mission keep running. '
        'Report the held result before using F10 > DCS Recorder ground test > Start playback. '
        'Do not toggle Active Pause. Keep your brakes held at release. The countdown lasts three seconds; '
        'the recording then stays stationary briefly before taxiing. This test removes the lead at the end; parked completion is later.')
    p=data.LuaData(entries['l10n/DEFAULT/dictionary'].decode('utf-8-sig'));p.take('dictionary');p.take('=');dictionary=p.value()
    dictionary['DictKey_ground_description']=description;m['descriptionText']='DictKey_ground_description'
    entries['l10n/DEFAULT/dictionary']=('dictionary = '+data.serialize(dictionary)).encode()
    entries['mission']=('mission = '+data.serialize(m)).encode()
    (out/'mission.lua').write_bytes(entries['mission']);(out/'mission-control.lua').write_text(script)
    (payload/'Missions').mkdir(parents=True)
    with zipfile.ZipFile(payload/'Missions'/MISSION,'x',zipfile.ZIP_DEFLATED) as z:
        for name,body in entries.items():z.writestr(name,body)
    hookdir=payload/'Scripts'/CONTROL;hookdir.mkdir(parents=True)
    fields=reference['fields']
    expected=dict(high=config['token_high'],low=config['token_low'],fields=fields,
                  mission={key:m[key] for key in fields.values()},description=description)
    (hookdir/'expected.lua').write_text('return '+data.serialize(expected)+'\n',encoding='utf-8')
    shutil.copy2(REPO/'companion/session_guard.lua',hookdir/'session_guard.lua')
    hook=(EFM/'release-start/hook.lua').read_text().replace('DCSRecorderReleaseControl',CONTROL).replace(manifest['module'],MODULE).replace(manifest['binary'],BINARY).replace(manifest['mission'],MISSION)
    (payload/'Scripts/Hooks').mkdir(parents=True)
    (payload/'Scripts/Hooks'/f'{CONTROL}.lua').write_text(hook)
    for validator,args in (
        (EFM/'release-start/check_package.lua',[out/'mission.lua']),
        (EFM/'verify_hornet_requirements.lua',[out/'mission.lua',Path('D:/DCS World/Mods/aircraft/FA-18C/entry.lua'),Path('D:/DCS World/MissionEditor/modules/me_mission.lua')]),
        (EFM/'verify_hornet_routes.lua',[out/'mission.lua',Path('D:/DCS World/MissionEditor/modules/me_route.lua'),3]),
        (EFM/'verify_hornet_configuration.lua',[out/'mission.lua',Path('D:/DCS World'),3,'StagedPlayback'])):
        subprocess.run(['D:/DCS World/bin/luae.exe',str(validator),*map(str,args)],check=True)
    result=dict(profile='ground-start-bound-take-v1',dcs_build='2.9.30.28536',module=MODULE,binary=BINARY,mission=MISSION,
                recording=metadata,initial=config,source_package_manifest=digest(seed/'manifest.json'),
                status='Offline checked; held placement, ground contact and release require live review',
                files={p.relative_to(payload).as_posix():digest(p) for p in payload.rglob('*') if p.is_file()})
    (out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    installer=(EFM/'release-start/Install-Control.ps1').read_text().replace('release-airborne-v1','ground-start-bound-take-v1').replace(manifest['module'],MODULE).replace(manifest['binary'],BINARY).replace(manifest['mission'],MISSION).replace('DCSRecorderReleaseControl',CONTROL)
    (out/'Install-Control.ps1').write_text(installer)
    print('Prepared',MISSION,'with',len(result['files']),'payload files')

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('output',type=Path)
    parser.add_argument('--workspace',type=Path,default=WORK,help='Directory containing ground-source, ground-tape, ground-build and hot-ground-capture-package-v2')
    args=parser.parse_args();WORK=args.workspace.resolve();build(args.output.resolve())
