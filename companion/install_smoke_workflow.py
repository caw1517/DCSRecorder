"""Prepare a backed-up v4 save-hook update and practice mission; keep native playback intact."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path
from library import Library, SUPPORTED_BUILD, digest
from install_engine_workflow import install

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EXPERIMENT = ROOT/'experiments/efm-ownership'


def prepare(settings_path, output):
    settings = json.loads(settings_path.read_text(encoding='utf-8-sig'))
    saved = Path(settings['saved_games']).resolve()
    dcs = Path(settings['dcs'])
    assert settings.get('engine_capture') is True, 'Verified engine capture must already be installed'
    assert json.loads((dcs/'autoupdate.cfg').read_text(encoding='utf-8-sig'))['version'] == SUPPORTED_BUILD
    old_hook = saved/'Scripts/Hooks/dcs-recorder-autosave.lua'
    expected = subprocess.run(['git','show','6baf9ec:companion/recording_sink.lua'],cwd=ROOT,
                              capture_output=True,check=True).stdout
    assert old_hook.read_bytes().replace(b'\r\n',b'\n') == expected.replace(b'\r\n',b'\n'), 'Unexpected existing save hook'
    for name in ('Engine','Smoke'):
        assert digest(saved/f'Scripts/DCSRecorder{name}Capture/Native{name}Capture.dll') == digest(EXPERIMENT/f'build/Release/Native{name}Capture.dll')
    assert digest(saved/'Scripts/DCSRecorderEngineCapture/engine_capture.lua') == digest(HERE/'engine_capture.lua')
    output.mkdir(parents=True,exist_ok=False)
    package = output/'files'
    for source,relative in [(HERE/'recording_sink.lua','Scripts/Hooks/dcs-recorder-autosave.lua'),
                            (HERE/'smoke_capture.lua','Scripts/DCSRecorderSmokeCapture/smoke_capture.lua')]:
        target=package/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    updated=dict(settings,smoke_capture=True)
    target=package/'DCSRecorder/companion-settings.json';target.parent.mkdir(parents=True)
    target.write_text(json.dumps(updated,indent=2),encoding='utf-8')
    # Generate and check in a staging Saved Games tree; no running-game files are touched.
    staged=dict(updated,saved_games=str(output/'staging'))
    mission=Library(staged,running=lambda:False).practice()
    target=package/'Missions'/Path(mission['mission']).name;target.parent.mkdir(parents=True)
    shutil.copy2(mission['mission'],target)
    files={p.relative_to(package).as_posix():digest(p) for p in package.rglob('*') if p.is_file()}
    old={name:digest(saved/name) if (saved/name).exists() else None for name in files}
    allowed={'Scripts/Hooks/dcs-recorder-autosave.lua','DCSRecorder/companion-settings.json'}
    assert all(value is None or name in allowed for name,value in old.items()), 'Existing additive files must not be replaced'
    protected=[p for parent in ('DCSRecorder/recordings','Mods/aircraft','Scripts','Missions')
               for p in (saved/parent).rglob('*') if p.is_file() and p.relative_to(saved).as_posix() not in files
               and 'probe-logs' not in p.parts]
    manifest=dict(saved_games=str(saved),files=files,expected_existing=old,
                  protected={p.relative_to(saved).as_posix():digest(p) for p in protected},
                  practice_mission=str(saved/'Missions'/target.name))
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(f'Prepared {len(files)} files, checked white-smoke mission; {len(protected)} protected files; no installed changes')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=('prepare','install'))
    parser.add_argument('output',type=Path)
    parser.add_argument('--settings',type=Path)
    args=parser.parse_args()
    if args.mode=='prepare':
        assert args.settings
        prepare(args.settings,args.output)
    else:
        install(args.output)
