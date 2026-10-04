"""Prepare/install the opt-in 2.9.30 companion trial, preserving prior files."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
from library import Library, EXPERIMENT, TRIAL_BUILD, digest
from install_engine_workflow import install

HERE=Path(__file__).resolve().parent
MODULE='DCSRecorder-Hornet-Wheels-Trial2930'
BINARY='HornetWheelsTrial2930'

def prepare(settings_path,output):
    settings=json.loads(settings_path.read_text(encoding='utf-8-sig'))
    updated=dict(settings,build_trial=TRIAL_BUILD)
    library=Library(updated);library.check_environment()
    if not all(updated.get(k) for k in ('engine_capture','smoke_capture','lights_capture','canopy_capture','wheels_capture')):
        raise ValueError('This trial requires the existing complete capture workflow')
    output.mkdir(parents=True,exist_ok=False);package=output/'files'
    saved=Path(settings['saved_games']);mod=package/'Mods/aircraft'/MODULE
    (mod/'bin').mkdir(parents=True);donor=Path(settings['donor_mod'])
    for name in ('entry.lua','aircraft.lua'):
        text=(donor/name).read_text(encoding='utf-8-sig').replace('DCSRecorder-Hornet-Probe',MODULE)
        if name=='entry.lua':text=text.replace('HornetProbe',BINARY).replace('DCS Recorder Hornet Prototype','DCS Recorder Build Trial')
        (mod/name).write_text(text,encoding='utf-8')
    for name in ('Cockpit','Datalinks','Liveries'):shutil.copytree(donor/name,mod/name)
    (mod/'Liveries/DCSRecorder-Hornet-Probe').rename(mod/'Liveries'/MODULE)
    shutil.copy2(EXPERIMENT/'build/Release'/f'{BINARY}.dll',mod/'bin'/f'{BINARY}.dll')
    replacements={
        'Scripts/Hooks/dcs-recorder-autosave.lua':'recording_sink.lua',
        'Scripts/DCSRecorderEngineCapture/engine_capture.lua':'engine_capture.lua',
        'Scripts/DCSRecorderSmokeCapture/smoke_capture.lua':'smoke_capture.lua'}
    for relative,source in replacements.items():
        installed=saved/relative
        # Only replace this repository's known previous scripts, preserving exact
        # installed bytes in the installer's backup before changes.
        previous=subprocess.run(['git','show','HEAD:companion/'+source],cwd=HERE,
            capture_output=True,text=True,check=True).stdout
        if installed.read_text(encoding='utf-8-sig')!=previous:
            raise ValueError('Installed script differs from the previous tracked version: '+relative)
        target=package/relative;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(HERE/source,target)
    for name in ('Engine','Smoke'):
        target=package/f'Scripts/DCSRecorder{name}Capture/Native{name}Capture2930.dll'
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(EXPERIMENT/f'build/Release/Native{name}Capture2930.dll',target)
    target=package/'DCSRecorder/companion-settings.json';target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(updated,indent=2),encoding='utf-8')
    files={p.relative_to(package).as_posix():digest(p) for p in package.rglob('*') if p.is_file()}
    old={name:digest(saved/name) if (saved/name).exists() else None for name in files}
    allowed=set(replacements)|{'DCSRecorder/companion-settings.json'}
    if any(value is not None and name not in allowed for name,value in old.items()):
        raise ValueError('An additive trial file already exists')
    protected=[p for parent in ('DCSRecorder/recordings','Mods/aircraft','Scripts','Missions')
        for p in (saved/parent).rglob('*') if p.is_file() and p.relative_to(saved).as_posix() not in files
        and not any(part in ('probe-logs','state-logs','layout-logs') for part in p.parts)
        and p.suffix.lower() in ('.lua','.dll','.txt','.csv','.miz','.json')]
    manifest=dict(saved_games=str(saved),build=TRIAL_BUILD,files=files,expected_existing=old,
                  protected={p.relative_to(saved).as_posix():digest(p) for p in protected})
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print(f'Prepared {len(files)} trial files; {len(protected)} existing files protected')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=('prepare','install'));p.add_argument('output',type=Path)
    p.add_argument('--settings',type=Path);a=p.parse_args()
    if a.mode=='prepare':prepare(a.settings,a.output)
    else:
        manifest=json.loads((a.output/'manifest.json').read_text())
        updated=json.loads((a.output/'files/DCSRecorder/companion-settings.json').read_text())
        Library(updated).check_environment()
        install(a.output)
