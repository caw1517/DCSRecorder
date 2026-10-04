"""Derive a separate countdown control from a hash-verified snapshot package."""
import argparse
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
from recorded_flight import read
spec=importlib.util.spec_from_file_location('fixture_data',ROOT/'companion/mission-identity-probe.prototype.py')
data=importlib.util.module_from_spec(spec);spec.loader.exec_module(data)
MODULE='DCSRecorder-Hornet-Release-Test'
BINARY='HornetReleaseProbe'
MISSION='043-Hornet-Countdown-Release.miz'

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def prepare(seed,output,dcs):
    seed,output=seed.resolve(),output.resolve()
    if output.exists():raise ValueError('Use a fresh output directory')
    source=json.loads((seed/'manifest.json').read_text(encoding='utf-8-sig'))
    if source['profile']!='snapshot-airborne-v1':raise ValueError('Expected a complete snapshot control')
    build=json.loads((dcs/'autoupdate.cfg').read_text(encoding='utf-8-sig'))['version']
    if build!=source['dcs_build'] or build!='2.9.30.28536':raise ValueError('Unsupported installed build')
    for name,sha in source['files'].items():
        path=(seed/name).resolve()
        if not path.is_relative_to(seed) or digest(path)!=sha:raise ValueError('Seed hash mismatch: '+name)
    recording=seed/'base/source-recording.csv'
    metadata,samples,_=read(recording)
    if metadata!=source['recording']:raise ValueError('Seed source metadata differs from snapshot')
    tape=(seed/source['module']/'bin/recorded-flight.txt').read_text().splitlines()
    if tape[0]!='DCSREC_PLAYBACK_V6' or tape[7:]!=[' '.join(f'{v:.15g}' for v in row) for row in samples]:
        raise ValueError('Seed source samples differ from the verified native tape')
    if not all(metadata[k] for k in ('exterior_available','engine_available','lights_available','canopy_available','wheels_available','smoke_available')):
        raise ValueError('Incomplete initial snapshot')
    first=samples[0]
    expected={21:first[11],38:first[42]}
    for channels,values in (([0,3,5,9,10,11,12,13,14,15,16,17,18],first[12:25]),
            ([28,29,89,90],first[25:29]),([88,190,191,192,193,210,212],first[35:42]),
            ([1,6,4,101,103,102,2],first[43:50])):expected.update(zip(channels,values))
    config=dict(token_high=source['initial']['token_high'],token_low=source['initial']['token_low'],
        expected=expected,smoke_events=metadata['smoke_events'],duration=metadata['duration'])
    payload=output/'payload';mod=payload/'Mods/aircraft'/MODULE
    for name in source['files']:
        relative=Path(name)
        if relative.parts[0]!=source['module']:continue
        if relative.suffix=='.dll':continue
        target=mod.joinpath(*relative.parts[1:])
        target=Path(str(target).replace(source['module'],MODULE))
        target.parent.mkdir(parents=True,exist_ok=True)
        if relative.name in ('entry.lua','aircraft.lua'):
            target.write_text((seed/name).read_text(encoding='utf-8').replace(source['module'],MODULE).replace(source['binary'],BINARY),encoding='utf-8')
        else:shutil.copy2(seed/name,target)
    shutil.copy2(EFM/'build/Release'/f'{BINARY}.dll',mod/'bin'/f'{BINARY}.dll')
    with zipfile.ZipFile(seed/source['mission']) as src:entries={i.filename:src.read(i) for i in src.infolist()}
    mission=data.LuaData(entries['mission'].decode('utf-8-sig')).mission()
    groups=mission['coalition']['blue']['country'][1]['plane']['group']
    leads=[g for g in groups.values() if g['units'][1]['name']=='StagedPlayback']
    assert len(leads)==1 and len(groups)==3 and not leads[0]['lateActivation']
    leads[0]['units'][1]['type']=MODULE
    # DCS fills missing Hornet properties/datalink data when loading. Prepare
    # those same defaults explicitly; retain strict full-field comparison.
    defaults_input=output/'defaults-input.lua'
    defaults_output=output/'resolved-defaults.lua'
    defaults_input.write_text('mission = '+data.serialize(mission),encoding='utf-8')
    subprocess.run([str(dcs/'bin/luae.exe'),str(HERE/'prepare_defaults.lua'),str(defaults_input),str(defaults_output),
        str(dcs),str(mod/'aircraft.lua'),str(HERE/'loaded_defaults.lua')],check=True)
    parser=data.LuaData(defaults_output.read_text(encoding='utf-8'));parser.take('return');defaults=parser.value()
    for group in groups.values():
        for unit in group['units'].values():unit.update(defaults[unit['unitId']])
    lua_config=dict(config,smoke_events=dict(enumerate(config['smoke_events'],1)))
    script='DCSR_RELEASE_CONFIG='+data.serialize(lua_config)+'\n'+(HERE/'mission.lua').read_text(encoding='utf-8')
    mission['trigrules'][1]['comment']='Held snapshot with one-shot countdown release'
    mission['trigrules'][1]['actions'][2]['text']=script
    mission['trig']['actions'][1]='a_set_command(816);a_do_script('+data.serialize(script)+');'
    # Failure cleanup is local to the mission and works even if the user hook
    # never loads. Normal release uses the direct hook dispatch, not this rule.
    mission['trigrules'][3]=dict(comment='Release owned player hold on diagnostic failure',predicate='triggerOnce',eventlist='',
        rules={1:dict(predicate='c_flag_is_true',flag='DCSR_RELEASE_CLEANUP')},
        actions={1:dict(predicate='a_set_command',command=816),2:dict(predicate='a_do_script',text='DCSR_RELEASE.cleaned()')})
    mission['trig']['conditions'][3]='return(c_flag_is_true("DCSR_RELEASE_CLEANUP"))'
    mission['trig']['actions'][3]='a_set_command(816);a_do_script("DCSR_RELEASE.cleaned()");mission.trig.func[3]=nil;'
    mission['trig']['func'][3]='if mission.trig.conditions[3]() then mission.trig.actions[3]() end'
    mission['trig']['flag'][3]=True
    description=('COUNTDOWN RELEASE CONTROL. Click Fly and wait for Ready. Inspect the held gear-down lead, '
        'then F10 > DCS Recorder release test > Start playback. A three-second countdown releases both aircraft. '
        'Do not toggle Active Pause. Watch the first movement and smoke onset, let the short flight finish, '
        'and exit normally. This is a separate airborne diagnostic, not ground or full workflow acceptance.')
    # Use a localized dictionary key, matching the proven loaded-field checker.
    parser=data.LuaData(entries['l10n/DEFAULT/dictionary'].decode('utf-8-sig'))
    parser.take('dictionary');parser.take('=');dictionary=parser.value()
    dictionary['DictKey_release_description']=description
    mission['descriptionText']='DictKey_release_description'
    entries['l10n/DEFAULT/dictionary']=('dictionary = '+data.serialize(dictionary)).encode('utf-8')
    entries['mission']=('mission = '+data.serialize(mission)).encode('utf-8')
    (output/'mission.lua').write_bytes(entries['mission'])
    for validator,args in (
        ('release-start/check_package.lua',[output/'mission.lua']),
        ('verify_hornet_requirements.lua',[output/'mission.lua',dcs/'Mods/aircraft/FA-18C/entry.lua',dcs/'MissionEditor/modules/me_mission.lua']),
        ('verify_hornet_routes.lua',[output/'mission.lua',dcs/'MissionEditor/modules/me_route.lua',3]),
        ('verify_hornet_configuration.lua',[output/'mission.lua',dcs,3,'StagedPlayback'])):
        subprocess.run([str(dcs/'bin/luae.exe'),str(EFM/validator),*map(str,args)],check=True)
    (payload/'Missions').mkdir()
    with zipfile.ZipFile(payload/'Missions'/MISSION,'x',zipfile.ZIP_DEFLATED) as dst:
        for name,content in entries.items():dst.writestr(name,content)
    hookdir=payload/'Scripts/DCSRecorderReleaseControl';hookdir.mkdir(parents=True)
    fields=['theatre','weather','coalition','trigrules','date','start_time','forcedOptions']
    reference=dict(high=config['token_high'],low=config['token_low'],fields=dict(enumerate(fields,1)),
        mission={field:mission[field] for field in fields},description=description)
    (hookdir/'expected.lua').write_text('return '+data.serialize(reference)+'\n',encoding='utf-8')
    subprocess.run([str(dcs/'bin/luae.exe'),str(HERE/'check_loaded_defaults.lua'),str(ROOT),str(output),str(dcs)],check=True)
    shutil.copy2(ROOT/'companion/session_guard.lua',hookdir/'session_guard.lua')
    (payload/'Scripts/Hooks').mkdir()
    shutil.copy2(HERE/'hook.lua',payload/'Scripts/Hooks/DCSRecorderReleaseControl.lua')
    shutil.copy2(recording,output/'source-recording.csv')
    manifest=dict(profile='release-airborne-v1',dcs_build=build,module=MODULE,binary=BINARY,mission=MISSION,
        source_manifest=str(seed/'manifest.json'),source_manifest_sha256=digest(seed/'manifest.json'),
        installed_default_sources={name:digest(dcs/name) for name in (
            'CoreMods/aircraft/FA-18C/FA-18C_hornet.lua','CoreMods/aircraft/FA-18C/Datalinks/AddProp.lua',
            'CoreMods/aircraft/FA-18C/Datalinks/Link16.lua','MissionEditor/modules/me_paramFM.lua')},
        recording=metadata,initial=config,status='Prepared; live release, first movement and smoke emission unverified',
        files={p.relative_to(payload).as_posix():digest(p) for p in payload.rglob('*') if p.is_file()})
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=manifest['status'],files=len(manifest['files']),mission=MISSION),indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('seed',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--dcs',type=Path,default=Path('D:/DCS World'));a=p.parse_args()
    prepare(a.seed,a.output,a.dcs)
