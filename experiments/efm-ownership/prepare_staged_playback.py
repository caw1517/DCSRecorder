"""Build a separate, version-gated staged playback package. Never installs."""
import argparse, hashlib, json, math, shutil, subprocess, zipfile
from pathlib import Path
from recorded_flight import read, convert
ROOT=Path(__file__).resolve().parent
SUPPORTED_BUILD='2.9.29.27468'


def lua_literal(value):
    if isinstance(value, dict):
        return '{'+','.join('['+lua_literal(k)+']='+lua_literal(v) for k,v in value.items())+'}'
    if isinstance(value, list):
        return '{'+','.join(map(lua_literal,value))+'}'
    return json.dumps(value,allow_nan=False)

def fingerprint(data):
    value=14695981039346656037
    for byte in data:value=((value^byte)*1099511628211)&0xffffffffffffffff
    return value

def prepare(recording,output,baseline,donor_mod,dcs):
    recording,output,baseline,donor_mod,dcs=map(Path,(recording,output,baseline,donor_mod,dcs))
    actual=json.loads((dcs/'autoupdate.cfg').read_text(encoding='utf-8-sig'))['version']
    if actual!=SUPPORTED_BUILD:raise ValueError(f'Unsupported DCS build {actual}; this experiment targets {SUPPORTED_BUILD}')
    metadata,samples,raw=read(recording)
    if metadata['livery']!='Blue Angels Jet Team':raise ValueError('This experiment supports Blue Angels Jet Team only')
    first=samples[0];r=raw[0]
    if abs(math.asin(max(-1,min(1,float(r['fy'])))))>math.radians(10) or float(r['uy'])<math.cos(math.radians(10)):
        raise ValueError('Current staged airborne test requires a near-level first sample')
    if output.exists():raise ValueError('Use a fresh output directory; prior packages are preserved')
    module='DCSRecorder-Hornet-Engine-Staged' if metadata['engine_available'] else 'DCSRecorder-Hornet-State-Staged' if metadata['exterior_available'] else 'DCSRecorder-Hornet-Staged'
    binary='HornetEngineStagedProbe' if metadata['engine_available'] else 'HornetStateStagedProbe' if metadata['exterior_available'] else 'HornetStagedProbe'
    if metadata['lights_available']:module,binary='DCSRecorder-Hornet-Lights-Staged','HornetLightsStagedProbe'
    if metadata['canopy_available']:module,binary='DCSRecorder-Hornet-Canopy-Staged','HornetCanopyStagedProbe'
    dll=ROOT/'build/Release'/f'{binary}.dll'
    for file in (baseline,dll,donor_mod/'entry.lua',donor_mod/'aircraft.lua'):
        if not file.is_file():raise ValueError(f'Missing preparation dependency: {file}')
    output.mkdir(parents=True)
    mod=output/module;(mod/'bin').mkdir(parents=True)
    convert(recording,mod/'bin/recorded-flight.txt')
    token=fingerprint((mod/'bin/recorded-flight.txt').read_bytes())
    config=dict(x=first[1],y=first[2],z=first[3],heading=math.atan2(float(r['fz']),float(r['fx'])),
                speed=math.sqrt(sum(v*v for v in first[8:11])),duration=metadata['duration'],
                token_high=((token>>40)&0xffffff)/16777216,token_low=(token&0xffffff)/16777216,
                aircraft=module,exterior=1 if metadata['exterior_available'] else 0,lights=metadata['lights_available'],canopy=metadata['canopy_available'])
    if metadata['smoke_available']:
        config.update(smoke_events=metadata['smoke_events'],smoke_clsid=metadata['smoke_clsid'])
    (output/'config.lua').write_text('return '+lua_literal(config)+'\n')
    for name in ('entry.lua','aircraft.lua'):
        text=(donor_mod/name).read_text(encoding='utf-8-sig').replace('DCSRecorder-Hornet-Probe',module)
        if name=='entry.lua':text=text.replace('HornetProbe',binary)
        (mod/name).write_text(text,encoding='utf-8')
    for name in ('Cockpit','Datalinks','Liveries'):shutil.copytree(donor_mod/name,mod/name)
    (mod/'Liveries/DCSRecorder-Hornet-Probe').rename(mod/'Liveries'/module)
    shutil.copy2(dll,mod/'bin'/f'{binary}.dll')
    shutil.copy2(recording,output/'source-recording.csv')
    with zipfile.ZipFile(baseline) as source:(output/'baseline.lua').write_bytes(source.read('mission'))
    def lua(script,*args):
        subprocess.run([str(dcs/'bin/luae.exe'),str(ROOT/script),*[str(a) for a in args]],check=True)
    lua('make_staged_playback_mission.lua',output/'baseline.lua',ROOT/'staged_playback_mission.lua',output/'config.lua',output/'mission')
    lua('verify_hornet_requirements.lua',output/'mission',dcs/'Mods/aircraft/FA-18C/entry.lua',dcs/'MissionEditor/modules/me_mission.lua')
    lua('verify_hornet_routes.lua',output/'mission',dcs/'MissionEditor/modules/me_route.lua',2)
    lua('verify_hornet_configuration.lua',output/'mission',dcs,2,*(['StagedPlayback'] if metadata['smoke_available'] else []))
    mission=output/'DCSRecorder-Staged-Playback.miz'
    with zipfile.ZipFile(baseline) as source,zipfile.ZipFile(mission,'w',zipfile.ZIP_DEFLATED) as target:
        for entry in source.infolist():target.writestr(entry,(output/'mission').read_bytes() if entry.filename=='mission' else source.read(entry.filename))
    manifest={'status':'Prepared; native/mission handshake and live exact-start validation pending',
              'dcs_build':actual,'profile':'staged-canopy-v1' if metadata['canopy_available'] else 'staged-lights-v1' if metadata['lights_available'] else 'staged-engine-v1' if metadata['engine_available'] else 'staged-exterior-v1' if metadata['exterior_available'] else 'staged-v1',
              'module':module,'binary':binary,'recording':metadata,'initial':config,
              'files':{p.relative_to(output).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in output.rglob('*') if p.is_file()}}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('recording');p.add_argument('output');p.add_argument('--baseline',required=True)
    p.add_argument('--donor-mod',required=True);p.add_argument('--dcs',default='D:/DCS World');a=p.parse_args()
    print(json.dumps(prepare(a.recording,a.output,a.baseline,a.donor_mod,a.dcs),indent=2))
