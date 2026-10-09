"""Build a formation prototype package: N recorded flights from one exact authored
scene, each played by its own aircraft of one playback module, plus the player.

Each take comes from this scene or, given its own saved scene, from an earlier
revision where its aircraft is authored identically; each from a different
aircraft. Every other authored aircraft (muted or without a take) is removed from
the prepared copy as a declared edit. The module carries every take under
bin/takes/; the control hook assigns each aircraft its take by runtime ID. The
controller is the locally built HornetFormationProbe.dll, installed under a
developer-only type so the normal playback module is never touched.

With `record`, the copy also records the player's position against the formation:
the recorder is injected for the player's aircraft and begins at the countdown
release with the shared epoch as time zero (no F10 Start).
Usage: python prepare.py <source.miz> <player unit id> <output dir> <mission name> <take.csv>=<unit id> ...
"""
from pathlib import Path
import json, shutil, subprocess, sys
HERE = Path(__file__).resolve().parent
EFM = HERE.parent
REPO = EFM.parents[1]
AUTHORED = EFM/'authored-preparation'
for path in (AUTHORED, EFM, REPO/'companion'):
    sys.path.insert(0, str(path))
import authored_missions as a
import prepare_playback as single
from recorded_flight import read, convert
from prepare_staged_playback import fingerprint
import loaded_reference, check_resources

DCS = Path('D:/DCS World')
CONTROLLER = EFM/'build/Release/HornetFormationProbe.dll'
MODULE, BINARY, DISPLAY = ('DCSRecorder-Hornet-Formation', 'DCSRecorderHornetFormation',
                           'DCS Recorder Hornet (formation prototype)')
CONTROL = 'DCSRecorderFormationControl'
PROFILE = 'formation-prototype-v1'


def bridge_key(token):
    return ((token >> 40) & 0xffffff)/16777216, (token & 0xffffff)/16777216


def build(source, player_id, output, mission_name, takes, dcs=DCS, saved_games=Path.home()/'Saved Games/DCS', allow_airborne=False,
          record=None):
    """`takes` is a list of (take path, authored unit id[, the take's own saved
    scene]), one per playing position. `record`, when recording the player's
    position, is dict(formation, version, lineage, association, associations
    {unit id: association} for the playing positions, played {association:
    {take, sha256}}, muted [association]). `allow_airborne` is for offline
    packaging tests only: airborne starts on the formation (surface) controller
    have no live evidence."""
    dcs, source, output = Path(dcs), Path(source), Path(output)
    if output.exists(): raise ValueError('Use a fresh output directory')
    takes = [(t[0], t[1], t[2] if len(t) > 2 else None) for t in takes]
    if not takes: raise ValueError('A formation needs at least one recorded flight')
    unit_ids = [int(u) for _, u, _ in takes]
    if len(set(unit_ids)) != len(unit_ids) or player_id in unit_ids:
        raise ValueError('Each recorded flight needs its own aircraft, and the player another one')
    seed = json.loads((single.SEED/'manifest.json').read_text(encoding='utf-8-sig'))
    for name, sha in seed['files'].items():
        if single.digest(single.SEED/'payload'/name) != sha: raise ValueError('Seed package hash mismatch: '+name)
    if not CONTROLLER.is_file(): raise ValueError('Build HornetFormationProbe first')

    blob, original_entries, original = a.read_source(source)
    mission, entries = a.copy.deepcopy(original), dict(original_entries)
    rows, behavior = a.validate_supported(mission, unit_ids+[player_id])
    leads, player = rows[:-1], rows[-1]
    edits = []
    # Muted and take-less aircraft are left out: the ramp holds only the playing
    # aircraft and the player. A declared, reversible edit; the source is untouched.
    removed = a.remove_aircraft(mission, set(unit_ids+[player_id]), edits)
    removals = len(edits)  # whole aircraft containers: verified below, listed by name

    payload = output/'payload'; mod = payload/'Mods/aircraft'/MODULE
    oldmod = single.SEED/'payload/Mods/aircraft'/seed['module']
    shutil.copytree(oldmod, mod, ignore=shutil.ignore_patterns('*.dll', 'recorded-flight.*', 'Liveries'))
    for name in ('entry.lua', 'aircraft.lua'):
        p = mod/name
        text = p.read_text(encoding='utf-8-sig').replace(seed['module'], MODULE).replace(seed['binary'], BINARY)
        if name == 'entry.lua':
            if text.count("displayName='DCS Recorder Hornet Prototype'") != 1: raise ValueError('Seed entry.lua changed')
            text = text.replace("displayName='DCS Recorder Hornet Prototype'", f"displayName='{DISPLAY}'")
        p.write_text(text, encoding='utf-8')
    shutil.copy2(CONTROLLER, mod/'bin'/f'{BINARY}.dll')
    (mod/'bin/takes').mkdir(parents=True)
    (mod/'Liveries'/MODULE).mkdir(parents=True)

    namespace, index = a.allocate(mission, entries)
    positions, hook_positions, mirror, notices, records = [], [], [], [], []
    for number, ((take, unit_id, saved), lead) in enumerate(zip(takes, leads), 1):
        take = Path(take)
        metadata, samples, raw = read(take)
        footer = take.read_text(encoding='utf-8').strip().splitlines()[-1].split(',')[1]
        single.validate_take(metadata, raw, footer)
        if saved is None:
            if metadata.get('authored_source_sha256') != a.sha(blob):
                raise ValueError(f'{take.name} was not recorded in this exact scene revision')
            if metadata.get('source') != lead['unit']['name'] or int(metadata.get('source_unit_id')) != int(unit_id):
                raise ValueError(f"{take.name} was flown from {metadata.get('source')}, not {lead['unit']['name']}")
        else:
            # A take from an earlier revision plays its confirmed counterpart, which
            # must be authored identically; the recorded flight is never moved.
            if metadata.get('authored_source_sha256') != a.sha(Path(saved).read_bytes()):
                raise ValueError(f'{take.name} does not belong to the saved scene given for it')
            recorded = a.selected(a.read_source(saved)[2], int(metadata['source_unit_id']))
            if metadata.get('source') != recorded['unit']['name']:
                raise ValueError(f'The saved scene for {take.name} does not contain the recorded aircraft')
            changed = a.compatibility(recorded, lead)
            if changed:
                raise ValueError(f"{take.name}: the recorded aircraft's authored start or configuration differs in this scene ("
                                 + ', '.join(changed[:4]) + ')')
        if not metadata.get('surface_available') and not allow_airborne:
            raise ValueError('The formation controller plays ground-contact takes')
        a.check_playback_take(lead, metadata)
        livery = a.find_livery(metadata.get('livery'), dcs, saved_games)
        installed = mod/'Liveries'/MODULE/livery.name
        if not installed.exists(): (shutil.copytree if livery.is_dir() else shutil.copy2)(livery, installed)
        tape = mod/'bin/takes'/f'position-{number}.txt'
        convert(take, tape)
        token = fingerprint(tape.read_bytes())
        lines, dropped = single.plan_stores(mod/'aircraft.lua', lead['unit'], dcs, Path(saved_games))
        mirror += [l for l in lines if l not in mirror]
        notices += [dropped[s] for s in sorted(dropped)]
        config = a.place_playback(mission, lead, player if number == 1 else None, metadata, samples[0], raw[0], MODULE, token,
                                  edits, drop_stations=sorted(dropped),
                                  livery_name=livery.stem if livery.is_file() else livery.name)
        config['name'] = lead['unit']['name']
        if record:
            config['association'] = record['associations'][int(unit_id)]
        positions.append(config)
        high, low = bridge_key(token)
        hook_positions.append(dict(name=lead['unit']['name'], unit_id=int(unit_id), high=high, low=low, take_sha256=single.digest(take)))
        records.append(dict(take=take.name, take_sha256=single.digest(take), unit_id=int(unit_id), name=lead['unit']['name'],
                            tape=tape.name, token=f'{token:016x}', duration=metadata['duration'], livery=livery.name,
                            parked=config.get('parked')))
    keys = [(p['high'], p['low']) for p in hook_positions]
    if len(set(keys)) != len(keys): raise ValueError('Two takes share a bridge key; re-record one')

    config = dict(player=player['unit']['name'], positions=dict(enumerate(positions, 1)))
    script = (HERE/'mission.lua').read_text(encoding='utf-8').replace('DCSR_FORMATION', namespace)
    if record:
        config['record'] = dict(formation=record['formation'], version=record['version'])
        if set(record['played']) != {p['association'] for p in positions}:
            raise ValueError('The playing positions differ from the formation plan')
        # The recorder runs first, in its own function scope and namespace.
        recorder = a.record_script(player['unit']['name'], namespace+'_REC', a.sha(blob), record['lineage'],
                                   record['association'], smoke=a.carries_smoke(player['unit']), formation=True)
        script = '(function()\n'+recorder+'\nend)()\n'+script
    script = namespace+'_CONFIG='+a.serialize(config)+'\n'+script
    cleanup = a.install_control(mission, index, namespace, script)
    manifest = dict(profile=PROFILE, build=a.BUILD, source_sha256=a.sha(blob), saved_scene_sha256=a.sha(blob),
                    positions=records, player_id=player_id, player_name=player['unit']['name'], namespace=namespace,
                    trigger_indices=[index, cleanup], role_edits=edits[removals:], initial=config, behavior=behavior, removed=removed)
    player_check = a.copy.deepcopy(player['group'])
    next(iter(player_check['units'].values()))['skill'] = a.selected(original, player_id)['unit']['skill']
    if player_check != a.selected(original, player_id)['group']:
        raise ValueError('Player authored placement or configuration changed.')
    entries[a.MARKER] = json.dumps(manifest, sort_keys=True).encode()
    entries['mission'] = a.encoded('mission', mission)
    manifest['preservation'] = a.verify_preservation(original_entries, original, entries, mission, edits, [index, cleanup])

    mission_lua = output/'mission.lua'; mission_lua.parent.mkdir(parents=True, exist_ok=True)
    mission_lua.write_bytes(entries['mission'])
    control = output/'control.lua'
    control.write_text(mission['trigrules'][index]['actions'][2]['text'], encoding='utf-8')
    (payload/'Missions').mkdir(parents=True)
    miz = payload/'Missions'/mission_name
    miz.write_bytes(a.packed(entries))

    hookdir = payload/'Scripts'/CONTROL; hookdir.mkdir(parents=True)
    dictionary = a.LuaData(entries['l10n/DEFAULT/dictionary'].decode('utf-8-sig')).assignment('dictionary')
    description = dictionary.get(mission['descriptionText'], mission['descriptionText'])
    reference = loaded_reference.loaded(mission, dcs, mod/'aircraft.lua', MODULE)
    expected = dict(positions=dict(enumerate(hook_positions, 1)), fields=dict(enumerate(loaded_reference.FIELDS, 1)),
                    mission=reference, description=description, prepared_sha256=single.digest(miz),
                    scene_sha256=a.sha(blob), mission_name=mission_name, module=MODULE, binary=BINARY)
    (hookdir/'expected.lua').write_text('return '+a.serialize(expected)+'\n', encoding='utf-8')
    shutil.copy2(REPO/'companion/session_guard.lua', hookdir/'session_guard.lua')
    hook = (HERE/'hook.lua').read_text(encoding='utf-8').replace('DCSR_FORMATION', namespace)
    (payload/'Scripts/Hooks').mkdir(parents=True)
    (payload/'Scripts/Hooks'/f'{CONTROL}.lua').write_text(hook, encoding='utf-8')

    luae = str(dcs/'bin/luae.exe')
    for args in ([AUTHORED/'check_me_zones.lua', mission_lua],
                 [EFM/'verify_hornet_requirements.lua', mission_lua, dcs/'Mods/aircraft/FA-18C/entry.lua',
                  dcs/'MissionEditor/modules/me_mission.lua', 'authored', *single.scene_plugins(mission, dcs, Path(saved_games))],
                 [EFM/'verify_hornet_routes.lua', mission_lua, dcs/'MissionEditor/modules/me_route.lua', single.plane_groups(mission)],
                 [HERE/'check_mission.lua', control, namespace, *(['single'] if len(positions) == 1 else [])],
                 [HERE/'check_hook.lua', payload, CONTROL, namespace]):
        subprocess.run([luae, *map(str, args)], check=True)
    single.mirror_stores(mod/'aircraft.lua', mirror)
    refs, problems = check_resources.problems(miz.read_bytes())
    if problems: raise ValueError('Unresolved resources: '+'; '.join(problems))
    result = dict(profile=PROFILE, controller_sha256=single.digest(mod/'bin'/f'{BINARY}.dll'), dcs_build=a.BUILD,
                  module=MODULE, binary=BINARY, control=CONTROL, mission=mission_name, positions=records,
                  source_sha256=manifest['source_sha256'], seed_manifest_sha256=single.digest(single.SEED/'manifest.json'),
                  mission_manifest=manifest, notices=notices,
                  status='Offline checked; live assignment, release and one-aircraft removal pending', removed=removed,
                  files={p.relative_to(payload).as_posix(): single.digest(p) for p in sorted(payload.rglob('*')) if p.is_file()})
    if record:
        # Read by take binding: the recording copy's half of the flown-against record.
        result.update(association=record['association'], lineage=record['lineage'], selected_id=player_id,
                      prepared_sha256=single.digest(miz),
                      formation=dict(formation=record['formation'], version=record['version'], played=record['played'],
                                     muted=sorted(record['muted'])))
    (output/'manifest.json').write_text(json.dumps(result, indent=2, default=str)+'\n', encoding='utf-8')
    shutil.copy2(source, output/'source.miz')
    for take, _, _ in takes: shutil.copy2(take, output/Path(take).name)
    print(json.dumps(dict(mission=mission_name, namespace=namespace, files=len(result['files']), player=manifest['player_name'],
                          positions=[r['name'] for r in records]), indent=2))
    return result


if __name__ == '__main__':
    source, player, out, name, *pairs = sys.argv[1:]
    build(source, int(player), out, name, [tuple(p.rsplit('=', 1)) for p in pairs])
