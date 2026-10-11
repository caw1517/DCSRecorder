"""Install the formation-aware save hook and capture scripts, with backups.

The save hook adds formation events and capture-hitch counts to takes that
declare them; the capture scripts accept hitches up to a take's declared
tolerance. Takes that declare neither are saved exactly as before. Refuses
unless DCS is closed and every installed file is a known earlier version;
installs all files or none.
Usage: python install_formation_hook.py --settings <companion-settings.json> [--rollback <backup dir>]
"""
import argparse, datetime, json, shutil, subprocess
from pathlib import Path
from library import dcs_running, digest

HERE = Path(__file__).resolve().parent
# Installed path -> (source, commits whose version may be replaced).
FILES = {
    'Scripts/Hooks/dcs-recorder-autosave.lua': ('recording_sink.lua', ('e869935', 'e79d241', 'b0c753b')),
    'Scripts/DCSRecorderEngineCapture/engine_capture.lua': ('engine_capture.lua', ('e869935', 'b0c753b')),
    'Scripts/DCSRecorderSmokeCapture/smoke_capture.lua': ('smoke_capture.lua', ('e869935', 'b0c753b')),
}


def normalized(data):
    return data.replace(b'\r\n', b'\n')


def known(name, source, commits):
    return {normalized(subprocess.run(['git', 'show', f'{c}:companion/{source}'], cwd=HERE, capture_output=True, check=True).stdout)
            for c in commits}


def install(settings_path):
    saved = Path(json.loads(Path(settings_path).read_text(encoding='utf-8-sig'))['saved_games'])
    if dcs_running():
        raise SystemExit('Close DCS before updating the recording scripts.')
    plan = []
    for name, (source, commits) in FILES.items():
        target, source = saved/name, HERE/source
        if digest(target) == digest(source):
            continue
        if normalized(target.read_bytes()) not in known(name, source.name, commits):
            raise SystemExit(f'{name} is not a known earlier version; nothing was changed.')
        plan.append((name, source, target))
    if not plan:
        print('Already installed.'); return
    backup = saved/'DCSRecorder/backups'/('formation-scripts-' + datetime.datetime.now().strftime('%Y%m%dT%H%M%S'))
    done = []
    try:
        for name, source, target in plan:
            (backup/name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, backup/name)
            temporary = target.with_name(target.name + '.formation.tmp')
            shutil.copy2(source, temporary)
            temporary.replace(target); done.append((name, target))
            if digest(target) != digest(source):
                raise RuntimeError('verification failed: ' + name)
    except Exception:
        for name, target in done:
            shutil.copy2(backup/name, target)
        raise SystemExit('Install failed; every file was restored.')
    print('Installed:', ', '.join(n for n, *_ in plan), '\nBackup', backup, '\nRestart DCS to load them.')


def rollback(settings_path, backup):
    saved = Path(json.loads(Path(settings_path).read_text(encoding='utf-8-sig'))['saved_games'])
    if dcs_running():
        raise SystemExit('Close DCS before restoring the recording scripts.')
    for name in FILES:
        if (Path(backup)/name).exists():
            shutil.copy2(Path(backup)/name, saved/name); print('Restored', name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--settings', required=True)
    parser.add_argument('--rollback')
    args = parser.parse_args()
    rollback(args.settings, args.rollback) if args.rollback else install(args.settings)
