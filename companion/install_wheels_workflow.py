"""Stage the v7 save hook and separate integrated wheel controller with rollback."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path
from library import Library, SUPPORTED_BUILD, digest
from install_engine_workflow import install

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
EXPERIMENT=ROOT/'experiments/efm-ownership'
MODULE='DCSRecorder-Hornet-Wheels-Staged'
BINARY='HornetWheelsStagedProbe'


def prepare(settings_path,output):
    settings=json.loads(settings_path.read_text(encoding='utf-8-sig'))
    saved=Path(settings['saved_games']).resolve();dcs=Path(settings['dcs'])
    assert settings.get('engine_capture') is True
    assert json.loads((dcs/'autoupdate.cfg').read_text(encoding='utf-8-sig'))['version']==SUPPORTED_BUILD
    old_hook=saved/'Scripts/Hooks/dcs-recorder-autosave.lua'
    expected=subprocess.run(['git','show','20cca98:companion/recording_sink.lua'],cwd=ROOT,capture_output=True,check=True).stdout
    assert old_hook.read_bytes().replace(b'\r\n',b'\n')==expected.replace(b'\r\n',b'\n'),'Unexpected existing save hook'
    for name in ('Engine','Smoke') if settings.get('smoke_capture') else ('Engine',):
        assert digest(saved/f'Scripts/DCSRecorder{name}Capture/Native{name}Capture.dll')==digest(EXPERIMENT/f'build/Release/Native{name}Capture.dll')
        assert digest(saved/f'Scripts/DCSRecorder{name}Capture/{name.lower()}_capture.lua')==digest(HERE/f'{name.lower()}_capture.lua')
    output.mkdir(parents=True,exist_ok=False);package=output/'files';mod=package/'Mods/aircraft'/MODULE
    (mod/'bin').mkdir(parents=True);donor=Path(settings['donor_mod'])
    for name in ('entry.lua','aircraft.lua'):
        text=(donor/name).read_text(encoding='utf-8-sig').replace('DCSRecorder-Hornet-Probe',MODULE)
        if name=='entry.lua':text=text.replace('HornetProbe',BINARY).replace('DCS Recorder Hornet Prototype','DCS Recorder Wheel Playback')
        (mod/name).write_text(text,encoding='utf-8')
    for name in ('Cockpit','Datalinks','Liveries'):shutil.copytree(donor/name,mod/name)
    (mod/'Liveries/DCSRecorder-Hornet-Probe').rename(mod/'Liveries'/MODULE)
    shutil.copy2(EXPERIMENT/('build/Release/'+BINARY+'.dll'),mod/('bin/'+BINARY+'.dll'))
    target=package/'Scripts/Hooks/dcs-recorder-autosave.lua';target.parent.mkdir(parents=True)
    shutil.copy2(HERE/'recording_sink.lua',target)
    updated=dict(settings,lights_capture=True,canopy_capture=True,wheels_capture=True)
    target=package/'DCSRecorder/companion-settings.json';target.parent.mkdir(parents=True)
    target.write_text(json.dumps(updated,indent=2),encoding='utf-8')
    mission=Library(dict(updated,saved_games=str(output/'staging')),running=lambda:False).practice()
    target=package/'Missions'/Path(mission['mission']).name;target.parent.mkdir(parents=True)
    shutil.copy2(mission['mission'],target)
    files={p.relative_to(package).as_posix():digest(p) for p in package.rglob('*') if p.is_file()}
    old={name:digest(saved/name) if (saved/name).exists() else None for name in files}
    allowed={'Scripts/Hooks/dcs-recorder-autosave.lua','DCSRecorder/companion-settings.json'}
    assert all(value is None or name in allowed for name,value in old.items()),'Existing additive files must not be replaced'
    protected=[p for parent in ('DCSRecorder/recordings','Mods/aircraft','Scripts','Missions')
        for p in (saved/parent).rglob('*') if p.is_file() and p.relative_to(saved).as_posix() not in files
        and not any(part in ('probe-logs','state-logs') for part in p.parts)
        and p.suffix.lower() in ('.lua','.dll','.txt','.csv','.miz','.json')]
    manifest=dict(saved_games=str(saved),files=files,expected_existing=old,
        protected={p.relative_to(saved).as_posix():digest(p) for p in protected},practice_mission=str(saved/'Missions'/target.name))
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(f'Prepared {len(files)} checked files and practice mission; {len(protected)} protected files; no installed changes')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=('prepare','install'));parser.add_argument('output',type=Path)
    parser.add_argument('--settings',type=Path);args=parser.parse_args()
    if args.mode=='prepare':
        assert args.settings;prepare(args.settings,args.output)
    else:install(args.output)
