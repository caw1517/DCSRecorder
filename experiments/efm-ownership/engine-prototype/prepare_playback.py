"""THROWAWAY: replay the last complete engine diagnostic's four appearance channels."""
import argparse
import csv
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
CHANNELS=[28,29,89,90]
MODULE='DCSRecorder-Hornet-Engine-Appearance'
BINARY='HornetEngineAppearanceProbe'
VARIANTS={MODULE:(BINARY,'DCSRecorder-Engine-Appearance-Playback.miz'),
    'DCSRecorder-Hornet-Engine-Sound-Probe':('HornetEngineSoundProbe','DCSRecorder-Engine-Sound-Probe.miz'),
    'DCSRecorder-Hornet-Sounder-Test':('HornetEngineSounderProbe','DCSRecorder-Sound-Routing-Test.miz'),
    'DCSRecorder-Hornet-Audibility-Test':('HornetEngineAudibilityProbe','DCSRecorder-Sound-Audibility-Test.miz'),
    'DCSRecorder-Hornet-Native-RPM':('HornetNativeRPMProbe','DCSRecorder-Native-RPM-Playback.miz'),
    'DCSRecorder-Hornet-Native-Engine':('HornetNativeEngineProbe','DCSRecorder-Native-Engine-Playback.miz')}


def prepare(logfile,output,dcs,donor,baseline,sound_probe=False,sounder_probe=False,saved=None,audibility_probe=False,rpm_probe=False,parameter_probe=False):
    assert sum(map(bool,(sound_probe,sounder_probe,audibility_probe,rpm_probe,parameter_probe)))<=1
    module='DCSRecorder-Hornet-Engine-Sound-Probe' if sound_probe else MODULE
    if sounder_probe: module='DCSRecorder-Hornet-Sounder-Test'
    if audibility_probe: module='DCSRecorder-Hornet-Audibility-Test'
    if rpm_probe: module='DCSRecorder-Hornet-Native-RPM'
    if parameter_probe: module='DCSRecorder-Hornet-Native-Engine'
    binary,mission_name=VARIANTS[module]
    if json.loads((dcs/'autoupdate.cfg').read_text(encoding='utf-8-sig'))['version']!='2.9.29.27468':
        raise ValueError('Engine actuator targets DCS 2.9.29.27468')
    summaries=analyze(logfile);summary=summaries[-1]
    if not summary['alignment_screen_passes']: raise ValueError('Latest take fails capture/alignment checks')
    required={'both_idle','both_military','left_afterburner','right_afterburner','both_afterburner','both_dry'}
    if not required.issubset(summary['segments']): raise ValueError('Latest take lacks throttle phases')
    # Restarted missions can reuse take IDs: select by BEGIN occurrence, not ID.
    rows=[];order=None
    for line in logfile.read_text(encoding='utf-8-sig',errors='replace').splitlines():
        prefix='DCSENGINE_MISSION,1,'
        if prefix not in line: continue
        fields=next(csv.reader([line.split(prefix,1)[1]]))
        if fields[0]=='BEGIN': rows=[];order=None
        elif fields[0]=='CHANNELS': order=list(map(int,fields[2:]))
        elif fields[0]=='DATA':
            assert order is not None
            values=dict(zip(order,map(float,fields[8:])))
            rows.append([float(fields[3]),*[values[c] for c in CHANNELS]])
    assert len(rows)==summary['rows']
    first=rows[0][0]
    for row in rows:
        row[0]-=first
        assert all(math.isfinite(v) and 0<=v<=1 for v in row[1:])
    output.mkdir(parents=True,exist_ok=False)
    mod=output/module;(mod/'bin').mkdir(parents=True)
    tape=['DCS_ENGINE_PROTOTYPE_V1',str(len(rows)),' '.join(map(str,CHANNELS))]
    tape+=[' '.join(format(v,'.12g') for v in row) for row in rows]
    rpm_metadata=None
    if rpm_probe or parameter_probe:
        if parameter_probe:
            from parameter_tape import prepare as prepare_native
        else:
            from rpm_tape import prepare as prepare_native
        rpm_metadata=prepare_native(logfile,mod/('bin/recorded-engine.txt' if parameter_probe else 'bin/recorded-rpm.txt'))
        first=rpm_metadata['origin']
        summary['duration']=rpm_metadata['duration']
    else:
        (mod/'bin/exterior-state.txt').write_text('\n'.join(tape)+'\n',encoding='ascii')
    for name in ('entry.lua','aircraft.lua'):
        text=(donor/name).read_text(encoding='utf-8-sig')
        assert 'DCSRecorder-Hornet-Probe' in text
        text=text.replace('DCSRecorder-Hornet-Probe',module)
        if name=='entry.lua':
            text=text.replace('HornetProbe',binary).replace('DCS Recorder Hornet Prototype',
                'DCS Recorder Native Engine Test' if parameter_probe else
                'DCS Recorder Native RPM Test' if rpm_probe else
                'DCS Recorder Sound Audibility Test' if audibility_probe else
                'DCS Recorder Sound Routing Test' if sounder_probe else
                ('DCS Recorder Engine Sound Probe' if sound_probe else 'DCS Recorder Engine Appearance Test'))
        elif sounder_probe or audibility_probe:
            needle='    add_aircraft(FA_18_Base)'
            assert text.count(needle)==1
            sounder_name='DCSRecorderAudibilityTest' if audibility_probe else 'DCSRecorderSounderTest'
            text=text.replace(needle,"    FA_18_Base.sounderName = 'Aircraft/Planes/"+sounder_name+"'\n"+needle)
        (mod/name).write_text(text,encoding='utf-8')
    if sounder_probe:
        assert saved is not None
        sounder=mod/'Sounds/Sounders/Aircraft/Planes/DCSRecorderSounderTest.lua'
        sounder.parent.mkdir(parents=True)
        logpath=(saved/'Mods/aircraft'/module/'sounder.log').as_posix()
        sounder.write_text('DCS_SOUND_LOG='+json.dumps(logpath)+'\n'+(HERE/'sounder_probe.lua').read_text(),encoding='utf-8')
    if audibility_probe:
        from audibility_assets import prepare as prepare_assets
        prepare_assets(mod)
        sounder=mod/'Sounds/Sounders/Aircraft/Planes/DCSRecorderAudibilityTest.lua'
        sounder.parent.mkdir(parents=True)
        sounder.write_bytes((HERE/'audibility_probe.lua').read_bytes())
    for name in ('Cockpit','Datalinks','Liveries'): shutil.copytree(donor/name,mod/name)
    (mod/'Liveries/DCSRecorder-Hornet-Probe').rename(mod/'Liveries'/module)
    shutil.copy2(ROOT/('build/Release/'+binary+'.dll'),mod/('bin/'+binary+'.dll'))
    with zipfile.ZipFile(baseline) as source:(output/'baseline.lua').write_bytes(source.read('mission'))
    description=('ENGINE APPEARANCE PLAYBACK TEST. Active Pause holds your Hornet until '
        'F10 > Engine appearance playback > Start captured engine sequence. F2 to inspect '
        'the separate lead. Watch each nozzle and afterburner flame through the announced '
        'throttle phases. Listen separately; engine sound is not driven by this experiment. '
        f'The captured argument sequence lasts {summary["duration"]:.2f} seconds, then holds '
        'for eight seconds before removing the lead. Let the lead disappear. This isolated '
        'test writes four appearance arguments after native animation; the lead follows '
        'an ordinary AI route, not the recorded flight path. Live success is unverified. '
        'Retain the DCS session for log collection. Do not manually toggle Active Pause.')
    if sound_probe:
        description=('ENGINE SOUND CALLBACK PROBE. Logs whether DCS requests engine parameters; '
            'all returned values remain unchanged. Audio is not corrected by this probe. '
            'Use F10 > Engine appearance playback > Start captured engine sequence, then F2 '
            'to watch the lead. Allow about 57 seconds until the lead disappears. '
            'The accepted nozzle/flame sequence follows an ordinary AI route. '
            'Retain this session for log collection. Do not manually toggle Active Pause.')
    if sounder_probe:
        description=('SOUND ROUTING TEST. F10 > Sound routing test > Start sound test; F2 to the lead. '
            'Expected: engine sample 3 seconds, afterburner sample 3 seconds, repeated once, then silence. '
            'The lead disappears after 15 seconds. This synthetic audio pattern tests direct spatial '
            'sound control; it is not synchronized to the nozzle/flame animation or a recorded engine. '
            'Retain this session for log collection. Do not manually toggle Active Pause.')
    if audibility_probe:
        description=('SOUND AUDIBILITY TEST. F10 > Sound audibility test > Start sound test; F2 to the lead. '
            'Four 3-second phases: stock engine, quiet control beeps, stock afterburner, '
            'afterburner with explicit distance settings; then 3 seconds with test sources stopped. '
            'Watch the phase labels. The lead disappears after 15 seconds. '
            'Report which phases were audible. This is an audio diagnostic, not recorded engine playback. '
            'Retain this session for log collection. Do not manually toggle Active Pause.')
    if rpm_probe:
        description=('NATIVE RPM PLAYBACK TEST. F10 > Native RPM playback > Start recorded RPM test; F2 to the lead. '
            f'Original engine RPM for 3 seconds, recorded core RPM for {summary["duration"]:.2f} seconds, '
            'then restore the original getter for 3 seconds and remove the lead. '
            'Listen for pitch changes at the labeled recorded idle/military transitions. '
            'Uses the normal DCS aircraft sound renderer, with no custom sound scripts or samples. '
            'Only the outward-facing core-RPM getter changes: fan RPM, thrust, afterburner, engine physics '
            'and recorded appearance are not replayed in this isolated test. The aircraft follows an AI route. '
            'Retain the session for log collection. Do not manually toggle Active Pause.')
    if parameter_probe:
        description=('NATIVE ENGINE PLAYBACK TEST. F10 > Native engine playback > Start recorded engine test; F2 to the lead. '
            f'Original parameters for 3 seconds, captured core/fan RPM and power for {summary["duration"]:.2f} seconds, '
            'then restore the original getters for 3 seconds and remove the lead. '
            'Listen for engine intensity and afterburner changes. Phase labels describe original throttle markers; '
            'playback follows the measured values, including transitions. Uses stock DCS sound, no custom samples. '
            'Only outward-facing native getters change. Physical engine simulation, recorded appearance and '
            'recorded trajectory are not restored; the lead follows an AI route. '
            'Retain the session for log collection. Do not manually toggle Active Pause.')
    config='return {aircraft='+json.dumps(module)+',duration='+str(summary['duration'])+',description='+json.dumps(description)+',markers={\n'
    config+=''.join('{time='+str(m['time']-first)+',segment='+json.dumps(m['segment'])+'},\n' for m in summary['markers'])+'}}\n'
    (output/'config.lua').write_text(config,encoding='utf-8')
    def lua(script,*args):subprocess.run([str(dcs/'bin/luae.exe'),str(ROOT/script),*map(str,args)],check=True)
    lua('state-prototype/make_playback.lua',output/'baseline.lua',HERE/('parameter_mission.lua' if parameter_probe else ('rpm_mission.lua' if rpm_probe else ('audibility_mission.lua' if audibility_probe else ('sounder_mission.lua' if sounder_probe else 'playback_mission.lua')))),output/'config.lua',output/'mission')
    lua('verify_hornet_requirements.lua',output/'mission',dcs/'Mods/aircraft/FA-18C/entry.lua',dcs/'MissionEditor/modules/me_mission.lua')
    lua('verify_hornet_routes.lua',output/'mission',dcs/'MissionEditor/modules/me_route.lua',2)
    lua('verify_hornet_configuration.lua',output/'mission',dcs,2)
    mission=output/mission_name
    with zipfile.ZipFile(baseline) as source,zipfile.ZipFile(mission,'x',zipfile.ZIP_DEFLATED) as target:
        for entry in source.infolist():target.writestr(entry,(output/'mission').read_bytes() if entry.filename=='mission' else source.read(entry.filename))
    manifest={'status':'Prepared; native engine parameter consumption and sound pending' if parameter_probe else ('Prepared; native RPM consumption and sound pending' if rpm_probe else ('Prepared; live audibility pending' if audibility_probe else ('Prepared; live sound routing pending' if sounder_probe else ('Prepared; live sound callback observation pending' if sound_probe else 'Prepared; live appearance retention/rendering pending')))),
        'module':module,'binary':binary,'sound_probe':sound_probe,'sounder_probe':sounder_probe,'audibility_probe':audibility_probe,'rpm_probe':rpm_probe,'parameter_probe':parameter_probe,
        'rpm_metadata':None if parameter_probe else rpm_metadata,'parameter_metadata':rpm_metadata if parameter_probe else None,
        'samples':len(rows),'duration':summary['duration'],'channels':(rpm_metadata['channels'] if parameter_probe else (['rpm_left','rpm_right'] if rpm_probe else CHANNELS)),'run_index':len(summaries)-1,
        'source_sha256':hashlib.sha256(logfile.read_bytes()).hexdigest(),
        'files':{p.relative_to(output).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [mission,*mod.rglob('*')] if p.is_file()}}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2))
    return mission


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('log',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--dcs',type=Path,default=Path('D:/DCS World'))
    parser.add_argument('--donor',type=Path,default=ROOT/'package/hornet-prototype/DCSRecorder-Hornet-Probe')
    parser.add_argument('--baseline',type=Path,default=ROOT/'package/hornet-prototype/EFM-Probe-Hornet-left-roll-400KIAS.miz')
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--sound-probe',action='store_true');mode.add_argument('--sounder-probe',action='store_true')
    mode.add_argument('--audibility-probe',action='store_true')
    mode.add_argument('--rpm-probe',action='store_true')
    mode.add_argument('--parameter-probe',action='store_true')
    parser.add_argument('--saved-games',type=Path,default=Path.home()/'Saved Games/DCS')
    args=parser.parse_args();print(prepare(args.log,args.output,args.dcs,args.donor,args.baseline,args.sound_probe,args.sounder_probe,args.saved_games,args.audibility_probe,args.rpm_probe,args.parameter_probe))
