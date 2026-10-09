"""Install the formation-aware save hook over the proven one, with a backup.

The formation hook only adds formation events to takes that declare a formation;
every other take is saved byte-for-byte as before. Refuses unless DCS is closed
and the installed hook is exactly the proven e869935 version (or already current).
Usage: python install_formation_hook.py --settings <companion-settings.json> [--rollback <backup dir>]
"""
import argparse, datetime, json, shutil, subprocess
from pathlib import Path
from library import dcs_running, digest

HERE = Path(__file__).resolve().parent
PROVEN = 'e869935'


def normalized(data):
    return data.replace(b'\r\n', b'\n')


def install(settings_path):
    settings = json.loads(Path(settings_path).read_text(encoding='utf-8-sig'))
    saved = Path(settings['saved_games'])
    target = saved/'Scripts/Hooks/dcs-recorder-autosave.lua'
    source = HERE/'recording_sink.lua'
    if dcs_running():
        raise SystemExit('Close DCS before updating the automatic save hook.')
    if digest(target) == digest(source):
        print('Already installed:', target); return
    proven = subprocess.run(['git', 'show', f'{PROVEN}:companion/recording_sink.lua'], cwd=HERE, capture_output=True, check=True).stdout
    if normalized(target.read_bytes()) != normalized(proven):
        raise SystemExit('The installed save hook is not the proven version; nothing was changed.')
    backup = saved/'DCSRecorder/backups'/('formation-hook-' + datetime.datetime.now().strftime('%Y%m%dT%H%M%S'))
    backup.mkdir(parents=True)
    shutil.copy2(target, backup/target.name)
    temporary = target.with_name(target.name + '.formation.tmp')
    shutil.copy2(source, temporary)
    temporary.replace(target)
    if digest(target) != digest(source):
        shutil.copy2(backup/target.name, target)
        raise SystemExit('Installed hook verification failed; the proven hook was restored.')
    print('Installed', target, '\nBackup', backup/target.name, '\nRestart DCS to load it.')


def rollback(settings_path, backup):
    settings = json.loads(Path(settings_path).read_text(encoding='utf-8-sig'))
    target = Path(settings['saved_games'])/'Scripts/Hooks/dcs-recorder-autosave.lua'
    if dcs_running():
        raise SystemExit('Close DCS before restoring the automatic save hook.')
    shutil.copy2(Path(backup)/target.name, target)
    print('Restored', target)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--settings', required=True)
    parser.add_argument('--rollback')
    args = parser.parse_args()
    rollback(args.settings, args.rollback) if args.rollback else install(args.settings)
