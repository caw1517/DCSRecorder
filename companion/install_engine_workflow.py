"""Prepare/install the separate v3 controller and backed-up automatic-save update."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from library import dcs_running, SUPPORTED_BUILD

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EXPERIMENT = ROOT/'experiments/efm-ownership'
MODULE = 'DCSRecorder-Hornet-Engine-Staged'
BINARY = 'HornetEngineStagedProbe.dll'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(settings_path, output):
    settings = json.loads(settings_path.read_text(encoding='utf-8-sig'))
    saved = Path(settings['saved_games']).resolve()
    dcs = Path(settings['dcs'])
    assert json.loads((dcs/'autoupdate.cfg').read_text(encoding='utf-8-sig'))['version'] == SUPPORTED_BUILD
    old_hook = saved/'Scripts/Hooks/dcs-recorder-autosave.lua'
    expected = subprocess.run(['git', 'show', '97794be:companion/recording_sink.lua'],
                              cwd=ROOT, capture_output=True, check=True).stdout
    assert old_hook.read_bytes().replace(b'\r\n', b'\n') == expected.replace(b'\r\n', b'\n'), 'Unexpected existing save hook'
    helper = saved/'Scripts/DCSRecorderEngineCapture/NativeEngineCapture.dll'
    assert digest(helper) == digest(EXPERIMENT/'build/Release/NativeEngineCapture.dll'), 'Capture helper differs from checked build'
    output.mkdir(parents=True, exist_ok=False)
    package = output/'files'
    mod = package/'Mods/aircraft'/MODULE
    (mod/'bin').mkdir(parents=True)
    donor = Path(settings['donor_mod'])
    for name in ('entry.lua', 'aircraft.lua'):
        text = (donor/name).read_text(encoding='utf-8-sig').replace('DCSRecorder-Hornet-Probe', MODULE)
        if name == 'entry.lua':
            text = text.replace('HornetProbe', BINARY[:-4]).replace('DCS Recorder Hornet Prototype', 'DCS Recorder Engine Playback')
        (mod/name).write_text(text, encoding='utf-8')
    for name in ('Cockpit', 'Datalinks', 'Liveries'):
        shutil.copytree(donor/name, mod/name)
    (mod/'Liveries/DCSRecorder-Hornet-Probe').rename(mod/'Liveries'/MODULE)
    shutil.copy2(EXPERIMENT/'build/Release'/BINARY, mod/'bin'/BINARY)
    for source, relative in ((HERE/'recording_sink.lua', 'Scripts/Hooks/dcs-recorder-autosave.lua'),
                             (HERE/'engine_capture.lua', 'Scripts/DCSRecorderEngineCapture/engine_capture.lua')):
        destination = package/relative;destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    updated = dict(settings, engine_capture=True)
    destination = package/'DCSRecorder/companion-settings.json';destination.parent.mkdir(parents=True)
    destination.write_text(json.dumps(updated, indent=2), encoding='utf-8')
    files = {p.relative_to(package).as_posix(): digest(p) for p in package.rglob('*') if p.is_file()}
    old = {name: digest(saved/name) if (saved/name).exists() else None for name in files}
    allowed = {'Scripts/Hooks/dcs-recorder-autosave.lua', 'DCSRecorder/companion-settings.json'}
    assert all(value is None or name in allowed for name, value in old.items()), 'Existing new-module files must not be replaced'
    protected = [p for parent in ('DCSRecorder/recordings', 'Mods/aircraft', 'Scripts/Hooks', 'Scripts/DCSRecorderEngineCapture')
                 for p in (saved/parent).rglob('*') if p.is_file() and p.relative_to(saved).as_posix() not in files]
    export = saved/'Scripts/Export.lua'
    if export.exists():protected.append(export)
    manifest = {'saved_games': str(saved), 'files': files, 'expected_existing': old,
                'protected': {p.relative_to(saved).as_posix(): digest(p) for p in protected}}
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(f'Prepared {len(files)} files; {len(protected)} protected files; no installed changes')


def install(output):
    assert not dcs_running(), 'Close DCS before installing'
    manifest = json.loads((output/'manifest.json').read_text())
    saved = Path(manifest['saved_games']).resolve()
    files = manifest['files']
    for relative, expected in files.items():
        source = (output/'files'/relative).resolve();target = (saved/relative).resolve()
        assert source.is_relative_to((output/'files').resolve()) and target.is_relative_to(saved)
        assert digest(source) == expected
        assert (digest(target) if target.exists() else None) == manifest['expected_existing'][relative]
    for relative, expected in manifest['protected'].items():assert digest(saved/relative) == expected
    backup = output/'backup';backup.mkdir(exist_ok=False)
    for relative, prior in manifest['expected_existing'].items():
        if prior is not None:
            target = backup/relative;target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(saved/relative, target)
            assert digest(target) == prior
    replaced = []
    try:
        for relative in files:
            target = saved/relative;target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name+'.engine-install.tmp')
            with temporary.open('xb') as stream:stream.write((output/'files'/relative).read_bytes())
            os.replace(temporary, target);replaced.append(relative)
            assert digest(target) == files[relative]
        for relative, expected in manifest['protected'].items():assert digest(saved/relative) == expected
    except Exception:
        for relative in reversed(replaced):
            target = saved/relative
            if manifest['expected_existing'][relative] is not None:shutil.copy2(backup/relative, target)
            else:target.unlink()
        raise
    (output/'installation.json').write_text(json.dumps({'installed': files, 'protected_unchanged': len(manifest['protected'])}, indent=2))
    print(f'PASS: {len(files)} installed hashes; {len(manifest["protected"])} protected files unchanged; prior hook/settings backed up')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare', 'install'))
    parser.add_argument('output', type=Path)
    parser.add_argument('--settings', type=Path)
    args = parser.parse_args()
    if args.mode == 'prepare':
        assert args.settings
        prepare(args.settings, args.output)
    else:
        install(args.output)
