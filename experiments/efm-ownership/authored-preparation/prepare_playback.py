"""Build an authored playback package from a real take and its exact source mission.

Reuses the accepted airborne release package (countdown-release gear-package-v5):
its module files and DLL bytes under a distinct module/binary name, its hook with
names substituted (as ground-start did), and release-start/mission.lua through
authored_missions.playback_entries. The hook's exact loaded-mission reference is
predicted by loaded_reference.py, which reproduces real DCS loads.
Usage: python prepare_playback.py <take.csv> <source.miz> <lead id> <player id> <output dir>
"""
from pathlib import Path
import hashlib, json, math, shutil, subprocess, sys
HERE = Path(__file__).resolve().parent
EFM = HERE.parent
REPO = EFM.parents[1]
sys.path.insert(0, str(REPO/'companion')); sys.path.insert(0, str(EFM)); sys.path.insert(0, str(HERE))
import authored_missions as a
from recorded_flight import read, convert
from prepare_staged_playback import fingerprint
import loaded_reference, check_resources

DCS = Path('D:/DCS World')
SEED = EFM/'results/countdown-release-2026-10-01/gear-package-v5'
# Takes with grounded samples use the separately built surface controller
# (release control plus contact-driven ground pose restoration).
SURFACE = EFM/'results/surface-start-2026-10-03/controller'
MODULE, BINARY = 'DCSRecorder-Hornet-Authored-Test', 'HornetAuthoredProbe'
CONTROL = 'DCSRecorderAuthoredControl'


def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def validate_take(metadata, raw, footer):
    # Same take gates as the companion's legacy path (library.Library.validate).
    if not a.supported_livery(metadata.get('livery')): raise ValueError('Unsupported livery')
    if metadata.get('capture_build') != a.BUILD: raise ValueError('Take build differs')
    if any(metadata.get(k) != '0' for k in ('wind_ground', 'wind_2000', 'wind_8000')): raise ValueError('Take lacks verified zero wind')
    if abs(float(raw[0]['fy'])) > math.sin(math.radians(10)) or float(raw[0]['uy']) < math.cos(math.radians(10)):
        raise ValueError('Take must begin nearly level (within 10 degrees)')
    if footer != 'user_stop': raise ValueError('Take did not end with F10 Stop')


def plane_groups(mission):
    # The count verify_hornet_routes.lua checks: every plane group in the mission.
    return sum(len((c.get('plane') or {}).get('group') or {}) for side in mission['coalition'].values()
               if isinstance(side, dict) for c in (side.get('country') or {}).values())


def installed_plugins(dcs, saved_games):
    """Plugin IDs declared by installed entry.lua files (DCS and Saved Games mods)."""
    import re
    ids = set()
    for root in (dcs/'Mods', dcs/'CoreMods', saved_games/'Mods'):
        for entry in root.glob('*/*/entry.lua') if root.exists() else []:
            text = entry.read_text(encoding='utf-8', errors='replace')
            # Literal IDs, or the stock modules' `local self_ID = "..."` form.
            match = re.search(r'declare_plugin\s*\(\s*"([^"]+)"', text) or re.search(r'local\s+self_ID\s*=\s*"([^"]+)"', text)
            if match: ids.add(match.group(1))
    return ids


def scene_plugins(mission, dcs, saved_games):
    """Required modules other than the stock Hornet, each confirmed installed."""
    required = set((mission.get('requiredModules') or {}).values())
    missing = required - installed_plugins(dcs, saved_games)
    if missing:
        raise ValueError('This scene needs modules that are not installed: ' + ', '.join(sorted(missing)))
    return sorted(required)


def build(take, source, lead_id, player_id, output, mission_name, dcs=DCS, saved=None,
          saved_games=Path.home()/'Saved Games/DCS'):
    """`saved` is the take's own scene when `source` is a confirmed newer revision."""
    dcs = Path(dcs)
    take, source, output = Path(take), Path(source), Path(output)
    if output.exists(): raise ValueError('Use a fresh output directory')
    seed = json.loads((SEED/'manifest.json').read_text(encoding='utf-8-sig'))
    for name, sha in seed['files'].items():
        if digest(SEED/'payload'/name) != sha: raise ValueError('Seed package hash mismatch: '+name)
    metadata, samples, raw = read(take)
    footer = take.read_text(encoding='utf-8').strip().splitlines()[-1].split(',')[1]
    validate_take(metadata, raw, footer)
    payload = output/'payload'; mod = payload/'Mods/aircraft'/MODULE
    oldmod = SEED/'payload/Mods/aircraft'/seed['module']
    shutil.copytree(oldmod, mod, ignore=shutil.ignore_patterns('*.dll', 'recorded-flight.*'))
    for name in ('entry.lua', 'aircraft.lua'):
        p = mod/name
        p.write_text(p.read_text(encoding='utf-8-sig').replace(seed['module'], MODULE).replace(seed['binary'], BINARY), encoding='utf-8')
    (mod/'Liveries'/seed['module']).rename(mod/'Liveries'/MODULE)
    # Same accepted bytes; a distinct file name so Windows never shares the
    # loaded release-test DLL instance with this module.
    if metadata.get('surface_available'):
        surface = json.loads((SURFACE/'manifest.json').read_text(encoding='utf-8'))
        if digest(SURFACE/surface['binary']) != surface['sha256']: raise ValueError('Surface controller hash mismatch')
        shutil.copy2(SURFACE/surface['binary'], mod/'bin'/f'{BINARY}.dll')
    else:
        shutil.copy2(oldmod/'bin'/f"{seed['binary']}.dll", mod/'bin'/f'{BINARY}.dll')
    convert(take, mod/'bin/recorded-flight.txt')
    token = fingerprint((mod/'bin/recorded-flight.txt').read_bytes())
    blob, entries, mission, manifest = a.playback_entries(source, lead_id, player_id, metadata, samples[0], raw[0], MODULE, token, saved)
    namespace = manifest['namespace']
    mission_lua = output/'mission.lua'; mission_lua.parent.mkdir(parents=True, exist_ok=True)
    mission_lua.write_bytes(entries['mission'])
    control = output/'control.lua'
    control.write_text(mission['trigrules'][manifest['trigger_indices'][0]]['actions'][2]['text'], encoding='utf-8')
    (payload/'Missions').mkdir(parents=True)
    miz = payload/'Missions'/mission_name
    miz.write_bytes(a.packed(entries))
    # Hook: exact loaded-mission reference plus the authored localized briefing.
    hookdir = payload/'Scripts'/CONTROL; hookdir.mkdir(parents=True)
    dictionary = a.LuaData(entries['l10n/DEFAULT/dictionary'].decode('utf-8-sig')).assignment('dictionary')
    description = dictionary.get(mission['descriptionText'], mission['descriptionText'])
    reference = loaded_reference.loaded(mission, dcs, mod/'aircraft.lua', MODULE)
    fields = dict(enumerate(loaded_reference.FIELDS, 1))
    # Approval is bound to this take, this prepared revision and its scene; the
    # loaded-mission comparison and tape token enforce them, and the hook logs them.
    expected = dict(high=((token >> 40) & 0xffffff)/16777216, low=(token & 0xffffff)/16777216, fields=fields,
                    mission=reference, description=description, take_sha256=digest(take),
                    prepared_sha256=digest(miz), scene_sha256=manifest['saved_scene_sha256'])
    assert expected['high'] == manifest['initial']['token_high'] and expected['low'] == manifest['initial']['token_low']
    (hookdir/'expected.lua').write_text('return '+a.serialize(expected)+'\n', encoding='utf-8')
    shutil.copy2(REPO/'companion/session_guard.lua', hookdir/'session_guard.lua')
    hook = (EFM/'release-start/hook.lua').read_text(encoding='utf-8')
    for old, new in (('DCSRecorderReleaseControl', CONTROL), (seed['module'], MODULE), (seed['binary'], BINARY),
                     (seed['mission'], mission_name), ('DCSR_RELEASE', namespace),
                     ("active=true;emit('START,'..session)",
                      "active=true;emit('START,'..session..',take='..expected.take_sha256..',prepared='..expected.prepared_sha256..',scene='..expected.scene_sha256)")):
        if old not in hook: raise ValueError('Release hook changed: '+old)
        hook = hook.replace(old, new)
    (payload/'Scripts/Hooks').mkdir(parents=True)
    (payload/'Scripts/Hooks'/f'{CONTROL}.lua').write_text(hook, encoding='utf-8')
    luae = str(dcs/'bin/luae.exe')
    for args in ([HERE/'check_me_zones.lua', mission_lua],
                 [EFM/'verify_hornet_requirements.lua', mission_lua, dcs/'Mods/aircraft/FA-18C/entry.lua', dcs/'MissionEditor/modules/me_mission.lua', 'authored', *scene_plugins(mission, dcs, Path(saved_games))],
                 [EFM/'verify_hornet_routes.lua', mission_lua, dcs/'MissionEditor/modules/me_route.lua', plane_groups(mission)],
                 [HERE/'check_authored_hook.lua', payload, CONTROL, mission_name, namespace],
                 [HERE/'check_authored_mission.lua', control, namespace, manifest['selected_name']]):
        subprocess.run([luae, *map(str, args)], check=True)
    refs, problems = check_resources.problems(miz.read_bytes())
    if problems: raise ValueError('Unresolved resources: '+'; '.join(problems))
    result = dict(profile='authored-playback-ground-v1' if metadata.get('surface_available') else 'authored-playback-airborne-v1',
                  controller_sha256=digest(mod/'bin'/f'{BINARY}.dll'), dcs_build=a.BUILD, module=MODULE, binary=BINARY,
                  control=CONTROL, mission=mission_name, take=take.name, take_sha256=digest(take),
                  source_sha256=manifest['source_sha256'], seed_manifest_sha256=digest(SEED/'manifest.json'),
                  recording=metadata, mission_manifest=manifest,
                  status='Offline checked; live readiness, release and scene comparison pending',
                  files={p.relative_to(payload).as_posix(): digest(p) for p in sorted(payload.rglob('*')) if p.is_file()})
    (output/'manifest.json').write_text(json.dumps(result, indent=2, default=str)+'\n', encoding='utf-8')
    shutil.copy2(take, output/take.name); shutil.copy2(source, output/'source.miz')
    if saved: shutil.copy2(saved, output/'saved-scene.miz')
    print(json.dumps(dict(mission=mission_name, namespace=namespace, files=len(result['files']),
                          player=manifest['player_name'], lead=manifest['selected_name']), indent=2))
    return result


if __name__ == '__main__':
    t, s, lead, player, out = sys.argv[1:6]
    build(t, s, int(lead), int(player), out, sys.argv[6] if len(sys.argv) > 6 else '056-Authored-Playback.miz')
