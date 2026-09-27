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


def prepare(logfile,output,dcs,donor,baseline):
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
    mod=output/MODULE;(mod/'bin').mkdir(parents=True)
    tape=['DCS_ENGINE_PROTOTYPE_V1',str(len(rows)),' '.join(map(str,CHANNELS))]
    tape+=[' '.join(format(v,'.12g') for v in row) for row in rows]
    (mod/'bin/exterior-state.txt').write_text('\n'.join(tape)+'\n',encoding='ascii')
    for name in ('entry.lua','aircraft.lua'):
        text=(donor/name).read_text(encoding='utf-8-sig')
        assert 'DCSRecorder-Hornet-Probe' in text
        text=text.replace('DCSRecorder-Hornet-Probe',MODULE)
        if name=='entry.lua':
            text=text.replace('HornetProbe',BINARY).replace('DCS Recorder Hornet Prototype','DCS Recorder Engine Appearance Test')
        (mod/name).write_text(text,encoding='utf-8')
    for name in ('Cockpit','Datalinks','Liveries'): shutil.copytree(donor/name,mod/name)
    (mod/'Liveries/DCSRecorder-Hornet-Probe').rename(mod/'Liveries'/MODULE)
    shutil.copy2(ROOT/('build/Release/'+BINARY+'.dll'),mod/('bin/'+BINARY+'.dll'))
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
    config='return {aircraft='+json.dumps(MODULE)+',duration='+str(summary['duration'])+',description='+json.dumps(description)+',markers={\n'
    config+=''.join('{time='+str(m['time']-first)+',segment='+json.dumps(m['segment'])+'},\n' for m in summary['markers'])+'}}\n'
    (output/'config.lua').write_text(config,encoding='utf-8')
    def lua(script,*args):subprocess.run([str(dcs/'bin/luae.exe'),str(ROOT/script),*map(str,args)],check=True)
    lua('state-prototype/make_playback.lua',output/'baseline.lua',HERE/'playback_mission.lua',output/'config.lua',output/'mission')
    lua('verify_hornet_requirements.lua',output/'mission',dcs/'Mods/aircraft/FA-18C/entry.lua',dcs/'MissionEditor/modules/me_mission.lua')
    lua('verify_hornet_routes.lua',output/'mission',dcs/'MissionEditor/modules/me_route.lua',2)
    lua('verify_hornet_configuration.lua',output/'mission',dcs,2)
    mission=output/'DCSRecorder-Engine-Appearance-Playback.miz'
    with zipfile.ZipFile(baseline) as source,zipfile.ZipFile(mission,'x',zipfile.ZIP_DEFLATED) as target:
        for entry in source.infolist():target.writestr(entry,(output/'mission').read_bytes() if entry.filename=='mission' else source.read(entry.filename))
    manifest={'status':'Prepared; live appearance retention/rendering pending','module':MODULE,'binary':BINARY,
        'samples':len(rows),'duration':summary['duration'],'channels':CHANNELS,'run_index':len(summaries)-1,
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
    args=parser.parse_args();print(prepare(args.log,args.output,args.dcs,args.donor,args.baseline))
