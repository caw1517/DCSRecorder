"""Switch the installed DCS Recorder setup between normal, legacy and developer.

The normal setup keeps only what authored recording and playback need. Every
other DCSRecorder registration, hook, script folder and mission that uses a
non-normal type is moved (never deleted) to DCSRecorder/setups/<legacy|developer>,
outside the folders DCS scans. Moves stay on the same drive, are hash-verified
and recorded in that folder's setup.json; a failed switch undoes its moves.
Restoring a set moves it back. DCS must be closed.
Usage: python setups.py status | normal | restore <legacy|developer>  [settings.json]
"""
from pathlib import Path
import json, os, sys
from datetime import datetime, timezone
from inventory import SETTINGS, HOOK, dcs_running, files, mission_refs

NORMAL_MODULES = {'DCSRecorder-Hornet'}
NORMAL_HOOKS = {'dcs-recorder-autosave.lua', 'DCSRecorderAuthoredControl.lua'}
NORMAL_SCRIPTS = {'DCSRecorderEngineCapture', 'DCSRecorderSmokeCapture', 'DCSRecorderAuthoredControl'}
# Legacy staged playback types; the companion's legacy setup plays older takes on them.
LEGACY_MODULES = {'DCSRecorder-Hornet-Staged', 'DCSRecorder-Hornet-State-Staged', 'DCSRecorder-Hornet-Engine-Staged',
                  'DCSRecorder-Hornet-Lights-Staged', 'DCSRecorder-Hornet-Canopy-Staged',
                  'DCSRecorder-Hornet-Wheels-Staged', 'DCSRecorder-Hornet-Wheels-Trial2930'}
GROUPS = ('legacy', 'developer')


def load(settings_path):
    settings = json.loads(Path(settings_path).read_text(encoding='utf-8-sig'))
    return settings, Path(settings['saved_games'])


def installed(saved):
    """Every non-normal recorder item now in the active installation, by group,
    as paths relative to Saved Games."""
    out = {g: [] for g in GROUPS}
    for p in sorted((saved/'Mods/aircraft').glob('DCSRecorder-*')):
        if p.name not in NORMAL_MODULES:
            out['legacy' if p.name in LEGACY_MODULES else 'developer'].append(p.relative_to(saved).as_posix())
    for p in sorted((saved/'Scripts/Hooks').glob('*')):
        if HOOK.search(p.name) and p.name not in NORMAL_HOOKS: out['developer'].append(p.relative_to(saved).as_posix())
    for p in sorted((saved/'Scripts').glob('*')):
        if p.is_dir() and p.name != 'Hooks' and HOOK.search(p.name) and p.name not in NORMAL_SCRIPTS:
            out['developer'].append(p.relative_to(saved).as_posix())
    # Missions that would not load without a moved type go with that type's set.
    for p in sorted((saved/'Missions').rglob('*.miz')):
        types = set(mission_refs(p)[0]) - NORMAL_MODULES
        if types:
            out['legacy' if types <= LEGACY_MODULES else 'developer'].append(p.relative_to(saved).as_posix())
    return out


def write_json(path, value):
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    os.replace(temporary, path)


def set_setup(settings_path, legacy):
    settings = json.loads(Path(settings_path).read_text(encoding='utf-8-sig'))
    settings.pop('setup', None)
    if legacy: settings['setup'] = 'legacy'
    write_json(Path(settings_path), settings)


def move(items, source_root, target_root, saved):
    """Rename each item from source_root to target_root (same drive), verifying
    every file hash; undo all moves if any step fails. Returns the file manifest."""
    plan = [(source_root/i, target_root/i) for i in items]
    for source, target in plan:
        if not source.exists(): raise ValueError('Missing: ' + str(source))
        if target.exists(): raise ValueError('Would overwrite: ' + str(target))
    if any(os.stat(s).st_dev != os.stat(target_root if target_root.exists() else saved).st_dev for s, _ in plan):
        raise ValueError('Setups must stay on the drive that holds Saved Games.')
    manifest, done = {}, []
    try:
        for item, (source, target) in zip(items, plan):
            before = {k: v for k, v in files(source, source_root).items()}
            target.parent.mkdir(parents=True, exist_ok=True)
            os.rename(source, target); done.append((source, target))
            after = files(target, target_root)
            if after != before: raise ValueError('Moved files changed: ' + item)
            manifest.update(after)
    except Exception:
        for source, target in reversed(done): os.rename(target, source)
        raise
    return manifest


def to_normal(settings_path=SETTINGS):
    if dcs_running(): raise SystemExit('Close DCS before switching setups.')
    settings, saved = load(settings_path)
    found, store, moved = installed(saved), saved/'DCSRecorder/setups', {}
    for group in GROUPS:
        if not found[group]: continue
        if (store/group/'setup.json').exists():
            raise ValueError(f'The {group} set is already stored; restore it before switching again.')
        (store/group).mkdir(parents=True, exist_ok=True)
        try:
            manifest = move(found[group], saved, store/group, saved)
        except Exception:
            for done in moved: move(moved[done], store/done, saved, saved); (store/done/'setup.json').unlink()
            raise
        write_json(store/group/'setup.json', dict(group=group, stored=datetime.now(timezone.utc).isoformat(timespec='seconds'),
                                                  items=found[group], files=manifest))
        moved[group] = found[group]
    set_setup(settings_path, legacy=False)
    return moved


def restore(group, settings_path=SETTINGS):
    if group not in GROUPS: raise ValueError('Choose legacy or developer.')
    if dcs_running(): raise SystemExit('Close DCS before switching setups.')
    settings, saved = load(settings_path)
    record = saved/'DCSRecorder/setups'/group/'setup.json'
    if not record.exists(): raise ValueError(f'No stored {group} set.')
    stored = json.loads(record.read_text(encoding='utf-8'))
    manifest = move(stored['items'], record.parent, saved, saved)
    if manifest != stored['files']: raise ValueError('Restored files differ from the stored manifest.')
    record.rename(record.with_name('restored-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '.json'))
    if group == 'legacy': set_setup(settings_path, legacy=True)
    return stored['items']


def status(settings_path=SETTINGS):
    settings, saved = load(settings_path)
    store = saved/'DCSRecorder/setups'
    return dict(setup=settings.get('setup', 'normal'), installed=installed(saved),
                stored={g: (store/g/'setup.json').exists() for g in GROUPS})


if __name__ == '__main__':
    command = sys.argv[1] if len(sys.argv) > 1 else 'status'
    if command == 'normal':
        moved = to_normal(*sys.argv[2:3])
        print(json.dumps({g: len(v) for g, v in moved.items()}), 'items moved; companion setup is now normal')
    elif command == 'restore':
        print(len(restore(sys.argv[2], *sys.argv[3:4])), 'items restored')
    else:
        print(json.dumps(status(*sys.argv[2:3]), indent=1))
