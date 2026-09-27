"""Prepare a reviewed local playback package from one completed take. Never installs."""
from pathlib import Path
import argparse,hashlib,json,math,shutil,zipfile
from recorded_flight import read,convert
from prepare_recording import ROOT,DCS,BASE,lua,checks,pack

def prepare(recording,output):
    metadata,samples,raw=read(recording)
    if metadata['exterior_available']:raise ValueError('Exterior recordings require the staged playback packager')
    # The first live prototype has one available livery registered for its custom type.
    # Do not silently substitute another livery if the mission was edited.
    if metadata['livery']!='Blue Angels Jet Team':
        raise ValueError('This prototype currently packages Blue Angels Jet Team only; register the recorded livery before playback')
    first=samples[0];r=raw[0]
    pitch=math.asin(max(-1,min(1,float(r['fy']))))
    if abs(pitch)>math.radians(10) or float(r['uy'])<math.cos(math.radians(10)):
        raise ValueError('Begin the first take straight and approximately level for native capture alignment')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    convert(recording,output/'recorded-flight.txt')
    config={'x':first[1],'y':first[2],'z':first[3],'vx':first[8],'vy':first[9],'vz':first[10],
            'heading':math.atan2(float(r['fz']),float(r['fx'])),'speed':math.sqrt(sum(v*v for v in first[8:11])),
            'livery':metadata['livery'],
            'briefing':f"Actual recorded-flight playback: {metadata['duration']:.1f} seconds. Begins at mission 5s, releases at {5+metadata['duration']:.1f}s. First 2s acquire attitude; remaining motion follows the recorded flight. Start is translated to the playback aircraft's captured position. Speed brake follows recording; lights off. Engine effects/sound are not yet matched."}
    if not 1000<=config['y']-5*config['vy']<=4970:raise ValueError('Initial altitude leaves insufficient spawn margin')
    (output/'config.lua').write_text('return {\n'+''.join(f'[{json.dumps(k)}]={json.dumps(v)},\n' for k,v in config.items())+'}\n')
    with zipfile.ZipFile(BASE) as src:(output/'baseline.lua').write_bytes(src.read('mission'))
    lua('make_recorded_playback_mission.lua',output/'baseline.lua',output/'config.lua',output/'mission')
    checks(output/'mission',2)
    mission=output/'EFM-Probe-Hornet-recorded-flight.miz';pack(output/'mission',mission)
    shutil.copy2(ROOT/'build/Release/HornetRecordedProbe.dll',output/'HornetProbe.dll')
    shutil.copy2(recording,output/'source-recording.csv')
    manifest={'status':'Prepared; live DCS validation pending','recording':str(Path(recording).resolve()),**metadata,
        'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [mission,output/'HornetProbe.dll',output/'recorded-flight.txt']}}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('recording');p.add_argument('output');a=p.parse_args()
    print(json.dumps(prepare(a.recording,a.output),indent=2))
