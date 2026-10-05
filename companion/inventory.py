"""Read-only inventory of everything DCSRecorder has installed or produced.

Lists registered playback/experiment types, their controllers and active tapes,
hooks and scripts, companion settings and data, user liveries, and every saved
mission that references a DCSRecorder type, each file with its SHA-256. It is the
exact manifest the registration decision requires before any installation change.
Nothing is modified.
Usage: python inventory.py <output manifest.json> [settings.json]
       python inventory.py snapshot <archive root> [settings.json]   (copies and verifies; DCS closed)
"""
from pathlib import Path
import hashlib, json, re, subprocess, sys, zipfile
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
SETTINGS = Path.home()/'Saved Games/DCS/DCSRecorder/companion-settings.json'
HOOK = re.compile(r'(dcs-recorder|DCSRecorder|ownership-id-map)', re.I)
TYPE = re.compile(r'\["type"\]\s*=\s*"(DCSRecorder-[^"]+)"')
# Held open by a running companion; listed but neither hashed nor copied.
VOLATILE = {'companion.lock'}


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''): h.update(block)
    return h.hexdigest()


def files(root, base):
    """Every file under `root`, relative to `base`, with size and hash."""
    out = {}
    for p in sorted(root.rglob('*') if root.is_dir() else [root]):
        if p.is_file():
            out[p.relative_to(base).as_posix()] = dict(size=p.stat().st_size,
                                                       sha256=None if p.name in VOLATILE else digest(p))
    return out


def first_line(path):
    try: return path.read_text(encoding='utf-8', errors='replace').split('\n', 1)[0].strip()
    except OSError: return None


def module(folder):
    entry = folder/'entry.lua'
    text = entry.read_text(encoding='utf-8', errors='replace') if entry.exists() else ''
    find = lambda pattern: (re.search(pattern, text) or [None, None])[1]
    type_id = find(r"local\s+id\s*=\s*'([^']+)'") or find(r'declare_plugin\s*\(\s*"([^"]+)"')
    binaries = re.findall(r"'([^']+)'", find(r'binaries\s*=\s*\{([^}]*)\}') or '')
    tape = folder/'bin/recorded-flight.txt'
    return dict(type_id=type_id, display_name=find(r"displayName\s*=\s*'([^']+)'"), binaries=binaries,
                dlls={p.name: digest(p) for p in sorted((folder/'bin').glob('*.dll'))},
                tape=dict(version=first_line(tape), sha256=digest(tape)) if tape.exists() else None,
                liveries=sorted(p.name for p in (folder/'Liveries').iterdir()) if (folder/'Liveries').is_dir() else [])


def mission_refs(path):
    """Recorder types in the mission's units, and archive members naming DCSRecorder."""
    try:
        with zipfile.ZipFile(path) as z:
            types, members = set(), []
            for name in z.namelist():
                text = z.read(name).decode('utf-8', errors='replace')
                if name == 'mission': types |= set(TYPE.findall(text))
                if 'DCSRecorder' in text or 'dcs-recorder' in text: members.append(name)
            return sorted(types), members, None
    except (zipfile.BadZipFile, OSError) as e:
        return [], [], str(e)


def inventory(settings_path=SETTINGS):
    settings = json.loads(Path(settings_path).read_text(encoding='utf-8-sig'))
    saved, dcs = Path(settings['saved_games']), Path(settings['dcs'])
    build = json.loads((dcs/'autoupdate.cfg').read_text(encoding='utf-8-sig'))['version']
    modules = {p.name: module(p) for p in sorted((saved/'Mods/aircraft').glob('DCSRecorder-*'))}
    registered = {m['type_id'] for m in modules.values()}
    scripts = sorted(p for p in (saved/'Scripts').glob('*') if HOOK.search(p.name))
    hooks = sorted(p for p in (saved/'Scripts/Hooks').glob('*') if HOOK.search(p.name))
    export = saved/'Scripts/Export.lua'
    missions, unreadable = {}, {}
    for p in sorted(saved.rglob('*.miz')):
        types, members, error = mission_refs(p)
        if error: unreadable[p.relative_to(saved).as_posix()] = error
        elif types or members:
            missions[p.relative_to(saved).as_posix()] = dict(sha256=digest(p), types=types, members=members,
                                                             unregistered=sorted(set(types) - registered))
    recordings = {p.name: first_line(p) for p in sorted((saved/'DCSRecorder/recordings').glob('*.csv'))}
    stock = dcs/'CoreMods/aircraft/FA-18C/FA-18C_hornet.lua'
    try: commit = subprocess.run(['git', '-C', str(HERE), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    except OSError: commit = None
    groups = {'modules': [saved/'Mods/aircraft'/n for n in modules], 'scripts': scripts, 'hooks': hooks,
              'companion': [saved/'DCSRecorder'],
              'liveries': sorted(p for p in (saved/'Liveries').glob('*/*') if 'DCSRecorder' in p.name) if (saved/'Liveries').exists() else [],
              'missions': [saved/m for m in missions]}
    listed = {}
    for group, roots in groups.items():
        for root in roots: listed.update({k: dict(v, group=group) for k, v in files(root, saved).items()})
    return dict(
        created=datetime.now(timezone.utc).isoformat(timespec='seconds'), companion_commit=commit,
        dcs=dict(path=str(dcs), build=build, stock_hornet_sha256=digest(stock) if stock.exists() else None),
        saved_games=str(saved), settings=settings, modules=modules,
        hooks=[p.name for p in hooks], scripts=[p.name for p in scripts],
        export_lua=dict(sha256=digest(export), references_recorder=bool(HOOK.search(export.read_text(encoding='utf-8', errors='replace'))))
        if export.exists() else None,
        recordings=recordings, missions=missions, unreadable_missions=unreadable,
        scope_note='Missions are scanned only under Saved Games/DCS, by unit type and by any archive member '
                   'naming DCSRecorder; references elsewhere are not inventoried.',
        files=listed)


def summary(m):
    lines = [f"DCS {m['dcs']['build']}; {len(m['modules'])} DCSRecorder modules; {len(m['hooks'])} hooks; "
             f"{len(m['scripts'])} script folders; {len(m['recordings'])} companion recordings; "
             f"{len(m['missions'])} missions referencing DCSRecorder; {len(m['files'])} files, "
             f"{sum(f['size'] for f in m['files'].values())/2**30:.2f} GiB"]
    for name, mod in m['modules'].items():
        tape = (mod['tape'] or {}).get('version') or '-'
        lines.append(f"  {name}: '{mod['display_name']}' dll={','.join(mod['dlls']) or '-'} tape={tape}")
    for name, mis in m['missions'].items():
        flag = f" UNREGISTERED {mis['unregistered']}" if mis['unregistered'] else ''
        lines.append(f"  {name}: {','.join(mis['types']) or '(script/members only)'}{flag}")
    for name, error in m['unreadable_missions'].items(): lines.append(f'  unreadable {name}: {error}')
    return '\n'.join(lines)


def dcs_running():
    result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq DCS.exe', '/NH'], capture_output=True, text=True)
    return 'DCS.exe' in result.stdout


def snapshot(archive_root, settings_path=SETTINGS):
    """Copy every inventoried file into a new archive folder and verify each copy.

    Originals are only read. The archive holds manifest.json (the inventory) and
    files/<path relative to Saved Games>; verification.json records the result.
    """
    import shutil
    if dcs_running(): raise SystemExit('Close DCS before taking a snapshot.')
    m = inventory(settings_path)
    target = Path(archive_root)/('snapshot-' + m['created'].replace(':', '').replace('+0000', 'Z'))
    target.mkdir(parents=True, exist_ok=False)
    (target/'manifest.json').write_text(json.dumps(m, indent=1) + '\n', encoding='utf-8')
    saved = Path(m['saved_games'])
    copied = {rel: f for rel, f in m['files'].items() if Path(rel).name not in VOLATILE}
    for rel in copied:
        (target/'files'/rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(saved/rel, target/'files'/rel)
    failures = [rel for rel, f in copied.items()
                if (target/'files'/rel).stat().st_size != f['size'] or (f['sha256'] and digest(target/'files'/rel) != f['sha256'])]
    extra = sorted(p.relative_to(target/'files').as_posix() for p in (target/'files').rglob('*')
                   if p.is_file() and p.relative_to(target/'files').as_posix() not in copied)
    result = dict(verified=not failures and not extra, files=len(copied), listed_not_copied=sorted(set(m['files']) - set(copied)), failures=failures, unexpected=extra,
                  manifest_sha256=digest(target/'manifest.json'))
    (target/'verification.json').write_text(json.dumps(result, indent=1) + '\n', encoding='utf-8')
    return target, m, result


if __name__ == '__main__':
    if sys.argv[1] == 'snapshot':
        target, m, result = snapshot(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else SETTINGS)
        print(summary(m).split('\n')[0])
        print(f"{target}: {'VERIFIED' if result['verified'] else 'FAILED'} {result['files']} files; "
              f"{len(result['failures'])} mismatches; {len(result['unexpected'])} unexpected")
        raise SystemExit(0 if result['verified'] else 1)
    out = Path(sys.argv[1])
    if out.exists(): raise SystemExit('Refusing to overwrite ' + str(out))
    m = inventory(sys.argv[2] if len(sys.argv) > 2 else SETTINGS)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(m, indent=1) + '\n', encoding='utf-8')
    print(summary(m))
