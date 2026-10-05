"""Local flight library and mission preparation. No third-party Python dependencies."""
from __future__ import annotations
import csv, hashlib, json, os, shutil, subprocess, sys, tempfile, uuid, zipfile
from pathlib import Path

EXPERIMENT = Path(__file__).resolve().parents[1] / 'experiments' / 'efm-ownership'
sys.path.insert(0, str(EXPERIMENT))
sys.path.insert(0, str(EXPERIMENT / 'authored-preparation'))
from recorded_flight import read
from prepare_staged_playback import prepare, SUPPORTED_BUILD, TRIAL_BUILD

LEGACY_STATE_NOTICE = ('Gear, flaps and control surfaces were not recorded and cannot replay. '
                       'Create a new practice mission and record again to capture them.')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def review_notes(behavior):
    """Preserved Mission Editor defaults and lifecycle consequences, for review."""
    text = ''
    if behavior['preserved']:
        text += '\n\nKept unchanged (they do not move the aircraft):\n- ' + '\n- '.join(behavior['preserved'])
    if behavior['lifecycle']:
        text += '\n\nAuthored triggers that will observe playback:\n- ' + '\n- '.join(behavior['lifecycle'])
    return text


def dcs_running():
    result = subprocess.run(['tasklist.exe', '/FI', 'IMAGENAME eq DCS.exe', '/FO', 'CSV', '/NH'],
                            capture_output=True, text=True, check=True,
                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    return any(row and row[0].lower() == 'dcs.exe' for row in csv.reader(result.stdout.splitlines()))


class Library:
    def __init__(self, settings, running=dcs_running):
        self.settings = settings
        if settings.get('build_trial') not in (None,TRIAL_BUILD):
            raise ValueError('Unknown companion build trial')
        self.build_trial=settings.get('build_trial')==TRIAL_BUILD
        self.build=TRIAL_BUILD if self.build_trial else SUPPORTED_BUILD
        self.saved = Path(settings['saved_games'])
        self.home = self.saved / 'DCSRecorder'
        self.recordings = self.home / 'recordings'
        self.recordings.mkdir(parents=True, exist_ok=True)
        self.running = running
        from mission_lineage import Registry
        self.lineage = Registry(self.home)

    def source(self, key):
        # Only direct CSV children returned by the library are selectable.
        if not isinstance(key, str) or Path(key).name != key or '/' in key or '\\' in key or ':' in key or not key.endswith('.csv'):
            raise ValueError('Choose a recording from the flight library.')
        path = self.recordings / key
        if path.is_symlink() or not path.is_file():
            raise ValueError('Recording is missing; refresh the library.')
        return path

    def validate(self, path):
        metadata, samples, raw = read(path)
        from authored_missions import supported_livery
        if not supported_livery(metadata['livery']):
            raise ValueError('Only Blue Angels Jet Team is currently supported.')
        # Old accepted baseline has no capture build/weather fields; only its exact
        # content hash is grandfathered. New practice missions capture these fields.
        if self.build_trial or digest(path) != self.settings.get('accepted_baseline_sha256'):
            if metadata.get('capture_build') != self.build:
                raise ValueError('Recording build is missing or unsupported.')
            if any(metadata.get(k) != '0' for k in ('wind_ground', 'wind_2000', 'wind_8000')):
                raise ValueError('Recording must have verified zero wind.')
        import math
        if abs(float(raw[0]['fy'])) > math.sin(math.radians(10)) or float(raw[0]['uy']) < math.cos(math.radians(10)):
            raise ValueError('Begin recording nearly level (within 10 degrees).')
        # The UI offers only explicitly stopped takes, even if the legacy converter
        # permits older non-user-stop footers.
        with Path(path).open(encoding='utf-8-sig', newline='') as stream:
            footer = list(csv.reader(stream))[-1]
        if footer[1] != 'user_stop':
            raise ValueError('Recording was not explicitly stopped using F10 Stop.')
        return metadata

    def entries(self):
        result = []
        for path in sorted(self.recordings.glob('*.csv'), reverse=True):
            if path.is_symlink():
                continue
            item = {'id': path.name, 'name': path.stem, 'created': path.stat().st_mtime,
                    'supported': False, 'duration': None, 'status_label': 'Unsupported'}
            namefile = path.with_suffix('.name.json')
            if namefile.exists():
                try:
                    item['name'] = json.loads(namefile.read_text(encoding='utf-8'))['name']
                except (ValueError, KeyError, OSError):
                    pass
            try:
                metadata = self.validate(path)
                exterior = metadata['exterior_available']
                engine = metadata['engine_available']
                smoke = metadata['smoke_available']
                item.update(supported=True, duration=metadata['duration'],
                            status_label='Motion + surfaces + engines + smoke' if smoke else 'Motion + surfaces + engines' if engine else ('Motion + surfaces' if exterior else 'Motion only'),
                            reason='Ready for playback with recorded surfaces, engines and white-smoke timing.' if smoke else 'Ready for playback with recorded surfaces, engine sound, nozzles and afterburner flames. Smoke was not captured.' if engine else 'Ready for playback with recorded gear, flaps and control surfaces. Engine sound and flames were not captured.'
                            if exterior else 'Motion playback available. ' + LEGACY_STATE_NOTICE)
                if metadata['lights_available']:
                    item['status_label'] += ' + lights'
                    item['reason'] += ' Exterior light brightness and strobe timing are recorded.'
                if metadata['canopy_available']:
                    item['status_label'] += ' + canopy'
                    item['reason'] += ' Canopy position and transitions are recorded.'
                if metadata['wheels_available']:
                    item['status_label'] += ' + wheels'
                    item['reason'] += ' Wheel rotation, suspension and nose-wheel steering are recorded.'
                if metadata.get('surface_available'):
                    item['status_label'] += ' + ground'
                    item['reason'] += ' Ground contact is recorded; grounded segments play back on the ground controller.'
                if metadata.get('authored_source_sha256'):
                    record = self.lineage.bind_take(path, metadata, self.authored_packages())
                    item.update(authored=True, status_label='Authored scene · '+item['status_label'],
                                reason='Plays back inside its saved Mission Editor scene, or a newer revision where you confirmed this aircraft. Choose the stock Hornet you will fly; it keeps its authored start.'
                                if record else 'Recorded before aircraft association: plays back only in its exact source mission. Choose the stock Hornet you will fly; it keeps its authored start.')
            except (ValueError, OSError, OverflowError) as exc:
                item['reason'] = str(exc)
            result.append(item)
        return result

    def rename(self, key, name):
        source = self.source(key)
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 100 or any(ord(c) < 32 for c in name):
            raise ValueError('Use a name of 1–100 characters.')
        destination = source.with_suffix('.name.json')
        temp = destination.with_suffix('.tmp-' + uuid.uuid4().hex)
        temp.write_text(json.dumps({'name': name.strip()}, ensure_ascii=False), encoding='utf-8')
        os.replace(temp, destination)  # Recording bytes and identity never change.

    def check_environment(self, require_closed=True):
        dcs = Path(self.settings['dcs'])
        actual = json.loads((dcs / 'autoupdate.cfg').read_text(encoding='utf-8-sig'))['version']
        if actual != self.build:
            raise ValueError(f'DCS {actual} is unsupported. This version requires {self.build}.')
        if require_closed and self.running():
            raise ValueError('Close DCS before preparing or installing a mission, then try again.')
        return dcs

    def authored_inspect(self, path):
        from authored_missions import inspect
        info = inspect(Path(path))
        revision = self.lineage.find_revision(info['sha256'])
        if revision:
            mapping = {d['unit_id'] for d in self.lineage.mapping(revision).values() if d['unit_id'] is not None}
            info['revision'] = dict(lineage=revision['lineage'], name=self.lineage.lineage(revision['lineage'])['name'],
                                    imported_at=revision['imported_at'])
            for aircraft in info['aircraft']:
                aircraft['associated'] = aircraft['id'] in mapping
        else:
            info['lineages'] = [dict(id=l['id'], name=l['name'], revisions=len(l['revisions']),
                                     latest=l['revisions'][-1]['imported_from'] if l['revisions'] else None)
                                for l in self.lineage.lineages()]
        return info

    def authored_review(self, path, source_sha256, lineage):
        return self.lineage.review(Path(path), source_sha256, lineage)

    def authored_save_revision(self, path, source_sha256, lineage=None, name=None, decisions=None):
        """Save an immutable scene revision: a new authored mission, or a changed
        revision of an existing one with each recorded aircraft confirmed once."""
        if lineage is None:
            self.lineage.create_lineage(Path(path), source_sha256, name)
            return {'message': 'Saved as a new authored mission. Choose the Hornet to record.'}
        # JSON object keys are strings; unit IDs are numbers or null.
        decisions = {k: (None if v is None else int(v)) for k, v in (decisions or {}).items()}
        self.lineage.join(Path(path), source_sha256, lineage, decisions)
        kept = sum(1 for v in decisions.values() if v is not None)
        return {'message': f'Revision saved. {kept} recorded aircraft confirmed; earlier takes keep their own saved scenes.'}

    def authored_packages(self):
        result = []
        for path in sorted((self.home / 'authored').glob('*/manifest.json')):
            try:
                result.append((path.parent.name, json.loads(path.read_text(encoding='utf-8'))))
            except (ValueError, OSError):
                continue
        return result

    def authored_recording(self, path, unit_id, source_sha256):
        from authored_missions import prepare_recording, read_source, validate_supported, BUILD
        self.check_environment()
        if self.build != BUILD or not self.settings.get('wheels_capture'):
            raise ValueError('Authored preparation requires the installed complete-state capture profile for '+BUILD)
        revision = self.lineage.find_revision(source_sha256)
        if not revision:
            raise ValueError('Save this mission revision in DCS Recorder before recording.')
        snapshot = self.lineage.snapshot(revision)
        validate_supported(read_source(snapshot)[2], [int(unit_id)])  # before any association is created
        association = self.lineage.association_for(revision, int(unit_id))
        generation = uuid.uuid4().hex
        output = self.home / 'authored' / generation
        # Prepared from the immutable saved scene, so the take's revision always exists.
        manifest = prepare_recording(snapshot, int(unit_id), output, source_sha256, revision['lineage'], association)
        self.check_environment()
        destination = self.saved / 'Missions' / ('DCSRecorder-Authored-Recording-'+generation[:8]+'.miz')
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('xb') as target:
            target.write((output/'prepared.miz').read_bytes())
        if digest(destination) != manifest['prepared_sha256']:
            raise ValueError('Installed recording mission hash mismatch.')
        return {'mission':str(destination), 'package':generation,
                'message':'Recording copy prepared for '+manifest['selected_name']+'. The authored source, briefing and embedded resources are preserved. Use F10 Start/Stop recording; confirm the take is saved before exiting.'
                          + review_notes(manifest['behavior'])}

    def authored_source(self, sha256):
        """The exact authored source of a take: a saved recording package, else Missions."""
        candidates = sorted((self.home/'authored').glob('*/source.miz')) + sorted((self.saved/'Missions').glob('*.miz'))
        for path in candidates:
            if not path.is_symlink() and path.is_file() and digest(path) == sha256:
                return path
        raise ValueError('The exact authored mission this take was recorded from was not found. '
                         'Keep the original .miz in Saved Games/DCS/Missions; edited revisions need a new recording.')

    def authored_take(self, key):
        source = self.source(key)
        metadata = self.validate(source)
        if not metadata.get('authored_source_sha256'):
            raise ValueError('This take was not recorded from an authored mission.')
        return source, metadata, self.lineage.bind_take(source, metadata, self.authored_packages())

    def authored_scenes(self, metadata, record):
        """(scene, source path, saved scene path or None). The saved scene comes first."""
        if record is None:
            # Recorded before association: only its exact source; no history is invented.
            mission = self.authored_source(metadata['authored_source_sha256'])
            return [(dict(sha256=digest(mission), saved=True, label=mission.name, lead_id=int(metadata['source_unit_id']),
                          lead_name=metadata['source']), mission, None)]
        original = self.lineage.snapshot(self.lineage.find_revision(record['source_sha256']))
        return [(scene, self.lineage.snapshot(scene.pop('revision')), None if scene['saved'] else original)
                for scene in self.lineage.scenes(record)]

    def authored_playback_options(self, key):
        from authored_missions import inspect
        _, metadata, record = self.authored_take(key)
        scenes = []
        for scene, mission, _ in self.authored_scenes(metadata, record):
            players = [a for a in inspect(mission)['aircraft'] if a['type'] == 'FA-18C_hornet' and a['id'] != scene['lead_id']]
            scenes.append(dict(scene, players=players))
        # The saved scene is first and is the default.
        return {'lead': metadata['source'], 'provenance': 'associated' if record else 'exact source only', 'scenes': scenes,
                'source_sha256': scenes[0]['sha256'], 'players': scenes[0]['players']}

    def authored_playback(self, key, player_id, source_sha256):
        """`source_sha256` names the chosen scene: the saved scene or a confirmed revision."""
        take, metadata, record = self.authored_take(key)
        chosen = [s for s in self.authored_scenes(metadata, record) if s[0]['sha256'] == source_sha256]
        if len(chosen) != 1:
            raise ValueError('The authored mission changed. Select the flight again.')
        scene, mission, saved = chosen[0]
        from prepare_playback import build
        dcs = self.check_environment()
        generation = uuid.uuid4().hex
        output = self.home / 'authored-playback' / generation
        output.parent.mkdir(parents=True, exist_ok=True)
        name = 'DCSRecorder-Authored-Playback-' + generation[:8] + '.miz'
        manifest = build(take, mission, scene['lead_id'], int(player_id), output, name, dcs=dcs, saved=saved,
                         saved_games=self.saved)
        (output / 'take-provenance.json').write_text(json.dumps(dict(take=record, scene_sha256=scene['sha256'],
                                                     saved_scene=scene['saved']), indent=2), encoding='utf-8')
        self.check_environment()
        self.install_authored(output, manifest, generation)
        player = manifest['mission_manifest']['player_name']
        ending = {True: ' At the end it stays parked with engines running until you exit or restart.',
                  False: ' It did not end in an eligible parked position, so it is removed at the end.'
                  }.get(manifest['mission_manifest']['initial'].get('parked'), '')
        return {'mission': str(self.saved / 'Missions' / name),
                'message': f'Playback mission ready. You fly {player} from its authored start. Load it, wait for Ready, '
                           'then F10 > DCS Recorder playback > Start playback.' + ending + ' Earlier authored playback missions now refuse to start.'
                           + review_notes(manifest['mission_manifest']['behavior'])
                           + ''.join(' ' + n for n in manifest.get('notices', []))}

    def install_authored(self, output, manifest, generation):
        """Install only what this take changes. Shared module files must already
        match exactly; per-take files are replaced after a backup, with rollback."""
        payload, module, control = output / 'payload', manifest['module'], manifest['control']
        # The controller differs between airborne and ground (surface) takes, and
        # aircraft.lua mirrors the lead's mod stores (Blue Angels HANHART).
        per_take = {f'Mods/aircraft/{module}/bin/recorded-flight.txt', f'Mods/aircraft/{module}/bin/recorded-flight.json',
                    f'Mods/aircraft/{module}/aircraft.lua',
                    f"Mods/aircraft/{module}/bin/{manifest['binary']}.dll",
                    f'Scripts/{control}/expected.lua', f'Scripts/Hooks/{control}.lua'}
        mission = 'Missions/' + manifest['mission']
        fresh = not (self.saved/'Mods/aircraft'/module).exists() and not (self.saved/'Scripts'/control).exists()
        plan = []
        for name, expected in manifest['files'].items():
            source, target = payload / name, self.saved / name
            if digest(source) != expected:
                raise ValueError('Prepared package changed; nothing was installed.')
            if name == mission or fresh:
                if target.exists():
                    raise ValueError('An existing file would be overwritten: ' + name)
                plan.append((name, source, target, False))
            elif not target.is_file():
                raise ValueError('The installed authored playback module is incomplete: ' + name)
            elif digest(target) != expected:
                if name not in per_take:
                    raise ValueError('Installed playback module differs from this app: ' + name)
                plan.append((name, source, target, True))
        backup = self.home / 'backups' / generation
        done = []
        try:
            for name, source, target, existed in plan:
                if existed:
                    (backup / name).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(target, backup / name)
                target.parent.mkdir(parents=True, exist_ok=True)
                temporary = target.with_name(target.name + '.' + generation + '.tmp')
                shutil.copy2(source, temporary)
                if existed:
                    os.replace(temporary, target)
                else:
                    os.rename(temporary, target)  # fails rather than overwriting
                done.append((name, target, existed))
                if digest(target) != manifest['files'][name]:
                    raise ValueError('Installed file verification failed: ' + name)
        except Exception:
            for name, target, existed in reversed(done):
                if existed:
                    shutil.copy2(backup / name, target)
                elif target.exists():
                    target.unlink()
            raise
        (output / 'activation.json').write_text(json.dumps({'installed': [n for n, *_ in plan], 'backup': str(backup)}, indent=2), encoding='utf-8')

    def practice(self):
        dcs = self.check_environment()
        engine = self.settings.get('engine_capture', False)
        smoke = self.settings.get('smoke_capture', False)
        lights = self.settings.get('lights_capture', False)
        canopy = self.settings.get('canopy_capture', False)
        wheels = self.settings.get('wheels_capture', False)
        if wheels and not canopy:
            raise ValueError('Wheel capture requires the installed canopy, lights and engine workflow.')
        if canopy and not (lights and engine):
            raise ValueError('Canopy capture requires the installed lights and engine workflow.')
        if lights and not engine:
            raise ValueError('Light capture requires the installed engine capture workflow.')
        if smoke and not engine:
            raise ValueError('Smoke capture requires the installed engine capture workflow.')
        prefix = 'DCSRecorder-Practice-Smoke-' if smoke else 'DCSRecorder-Practice-Engine-' if engine else 'DCSRecorder-Practice-Exterior-'
        if lights: prefix = 'DCSRecorder-Practice-Lights-'
        if canopy: prefix = 'DCSRecorder-Practice-Canopy-'
        if wheels: prefix = 'DCSRecorder-Practice-Wheels-'
        destination = self.saved / 'Missions' / (prefix + uuid.uuid4().hex[:8] + '.miz')
        script = (EXPERIMENT / ('record_flight_engine_mission.lua' if engine else 'record_flight_mission.lua')).read_text(encoding='utf-8-sig')
        # Metadata and wording are specific to the app-generated practice mission.
        script = script.replace("csv(r.source)..'\\n'", "csv(r.source)..'\\ncapture_build," + self.build + "\\nwind_ground,'..tostring(env.mission.weather.wind.atGround.speed)..'\\nwind_2000,'..tostring(env.mission.weather.wind.at2000.speed)..'\\nwind_8000,'..tostring(env.mission.weather.wind.at8000.speed)..'\\n'")
        assert 'capture_build,' in script
        if self.build_trial:
            script=script.replace('capture_build,'+self.build,'capture_timing,frame-batch-v1\\ncapture_build,'+self.build)
        if smoke:
            script = 'DCSRECORDER_SMOKE=true\n' + script
        if lights:
            script = 'DCSRECORDER_LIGHTS=true\n' + script
        if canopy:
            script = 'DCSRECORDER_CANOPY=true\n' + script
        if wheels:
            script = 'DCSRECORDER_WHEELS=true\n' + script
        script = script.replace(' samples written to DCS.log. Ready for extraction. Keep this DCS session until the recording is collected.',
                                ' samples captured. Automatic save is pending; confirm the take appears in the companion flight library before closing DCS.')
        script = script.replace(' into DCS.log.', '. Use the companion flight library to confirm automatic saving after Stop.')
        with tempfile.TemporaryDirectory(dir=self.home) as folder:
            folder = Path(folder)
            with zipfile.ZipFile(self.settings['baseline_mission']) as source:
                (folder / 'baseline.lua').write_bytes(source.read('mission'))
            (folder / 'recorder.lua').write_text(script, encoding='utf-8')
            (folder / 'description.txt').write_text(('DCS Recorder practice with recorded engine sound, nozzles, flames and surfaces. ' if engine else '') + 'DCS Recorder practice with gear, flaps and control-surface capture. Fly the stock Hornet in calm air. F10 > DCS Recorder > Start recording. Begin nearly level and airborne. Fast rolls and low-altitude airborne playback are under live validation. Ground starts and takeoff/landing playback are still being implemented. Record 5 to 300 seconds. F10 > Stop recording saves the take automatically. Confirm the take appears in the companion flight library before closing DCS.', encoding='utf-8')
            if smoke:
                description = folder / 'description.txt'
                description.write_text('White smoke is fitted on station 10 and captured with the flight. Use Smoke Device - ON/OFF to switch it. ' + description.read_text(encoding='utf-8'), encoding='utf-8')
            self.lua(dcs, 'make_recording_mission.lua', folder / 'baseline.lua', folder / 'recorder.lua', folder / 'mission', folder / 'description.txt', *(['{INV-SMOKE-WHITE}'] if smoke else []))
            self.verify_mission(dcs, folder / 'mission', 1, 'Observer' if smoke else None)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(self.settings['baseline_mission']) as source, zipfile.ZipFile(destination, 'x', zipfile.ZIP_DEFLATED) as target:
                for entry in source.infolist():
                    target.writestr(entry, (folder / 'mission').read_bytes() if entry.filename == 'mission' else source.read(entry.filename))
        if wheels:
            return {'mission': str(destination), 'message': 'Practice mission created with recorded wheels, suspension, steering, canopy, lights, surfaces and engines.' + (' White smoke is fitted and captured.' if smoke else '') + ' Record with F10 Start/Stop, then confirm the saved take includes wheels in the flight library.'}
        if canopy:
            return {'mission': str(destination), 'message': 'Practice mission created with canopy, lights, surfaces and engines.' + (' White smoke is fitted and captured.' if smoke else '') + ' Record with F10 Start/Stop, then confirm the saved take includes canopy in the flight library.'}
        if lights:
            return {'mission': str(destination), 'message': 'Practice mission created with recorded lights, surfaces and engines.' + (' White smoke is fitted and captured.' if smoke else '') + ' Record with F10 Start/Stop, then confirm the saved take includes lights in the flight library.'}
        if smoke:
            return {'mission': str(destination), 'message': 'Practice mission created with white smoke fitted on station 10. Record with F10 Start/Stop and use Smoke Device - ON/OFF to switch smoke. The saved take will say Motion + surfaces + engines + smoke.'}
        if engine:
            return {'mission': str(destination), 'message': 'Practice mission created with motion, surfaces and engine capture. Load this exact new mission. Record with F10 Start/Stop, then confirm the take says Motion + surfaces + engines in the flight library.'}
        return {'mission': str(destination), 'message': 'Practice mission created with gear, flaps and control-surface capture. Load this exact mission in DCS; older practice missions do not gain the new capture features. Use F10 Start/Stop recording, then confirm the saved take says Motion + surfaces here.'}

    def lua(self, dcs, script, *args):
        result = subprocess.run([str(dcs / 'bin/luae.exe'), str(EXPERIMENT / script), *map(str, args)],
                                capture_output=True, text=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if result.returncode:
            raise ValueError(result.stdout + result.stderr)

    def verify_mission(self, dcs, mission, count, smoke_unit=None):
        self.lua(dcs, 'verify_hornet_requirements.lua', mission, dcs / 'Mods/aircraft/FA-18C/entry.lua', dcs / 'MissionEditor/modules/me_mission.lua')
        self.lua(dcs, 'verify_hornet_routes.lua', mission, dcs / 'MissionEditor/modules/me_route.lua', count)
        self.lua(dcs, 'verify_hornet_configuration.lua', mission, dcs, count, *([smoke_unit] if smoke_unit else []))

    def playback(self, key):
        source = self.source(key)
        metadata = self.validate(source)
        if metadata.get('authored_source_sha256'):
            raise ValueError('This take belongs to an authored scene. Authored playback preparation is still being validated; the legacy practice-mission builder cannot preserve its scene.')
        dcs = self.check_environment()
        generation = uuid.uuid4().hex
        output = self.home / 'packages' / generation
        output.parent.mkdir(parents=True, exist_ok=True)
        manifest = prepare(source, output, self.settings['baseline_mission'], self.settings['donor_mod'], dcs,build_trial=self.build_trial)
        # Recheck immediately before replacing anything in the active installation.
        self.check_environment()
        self.activate(output, manifest, generation)
        mission = self.saved / 'Missions' / ('DCSRecorder-Playback-' + generation[:8] + '.miz')
        message = 'Playback mission ready. Load this mission in DCS, then F10 > DCS Recorder > Start playback. Restart the mission to replay.'
        if not metadata['exterior_available']:
            message += '\n\nMotion only: ' + LEGACY_STATE_NOTICE
        return {'mission': str(mission), 'message': message}

    def activate(self, output, manifest, generation):
        module=manifest.get('module','DCSRecorder-Hornet-Staged')
        binary=manifest.get('binary','HornetStagedProbe')
        allowed=(('DCSRecorder-Hornet-Wheels-Trial2930','HornetWheelsTrial2930'),) if self.build_trial else (('DCSRecorder-Hornet-Staged','HornetStagedProbe'),('DCSRecorder-Hornet-State-Staged','HornetStateStagedProbe'),('DCSRecorder-Hornet-Engine-Staged','HornetEngineStagedProbe'),('DCSRecorder-Hornet-Lights-Staged','HornetLightsStagedProbe'),('DCSRecorder-Hornet-Canopy-Staged','HornetCanopyStagedProbe'),('DCSRecorder-Hornet-Wheels-Staged','HornetWheelsStagedProbe'))
        if (module,binary) not in allowed:
            raise ValueError('Unsupported playback module')
        mod = self.saved / 'Mods/aircraft' / module
        # Install once with the tested installer. Updates replace only the tape,
        # with the previous tape retained. DLL changes require explicit setup.
        if not mod.is_dir():
            raise ValueError('The staged playback module is missing. Install the tested module before generating playback.')
        incoming = output / module
        if digest(mod / 'bin' / (binary+'.dll')) != digest(incoming / 'bin' / (binary+'.dll')):
            raise ValueError('Installed playback controller differs from this app. Close DCS and update the module through setup.')
        for relative, expected in manifest['files'].items():
            if digest(output / relative) != expected:
                raise ValueError('Prepared package changed; no active files were replaced.')
        destination = self.saved / 'Missions' / ('DCSRecorder-Playback-' + generation[:8] + '.miz')
        destination.parent.mkdir(parents=True, exist_ok=True)
        backup = self.home / 'backups' / generation
        backup.mkdir(parents=True)
        replacements = []
        replaced = []
        try:
            for name in ('recorded-flight.txt', 'recorded-flight.json'):
                target = mod / 'bin' / name
                if target.exists():
                    shutil.copy2(target, backup / name)
                temporary = target.with_name(name + '.' + generation + '.tmp')
                shutil.copy2(incoming / 'bin' / name, temporary)
                replacements.append((target, temporary, (backup / name).exists()))
            self.check_environment()
            for target, temporary, existed in replacements:
                os.replace(temporary, target)
                replaced.append((target, temporary, existed))
            # An existing mission is never overwritten; its fingerprint prevents
            # it from playing a newly selected tape accidentally.
            with destination.open('xb') as stream:
                stream.write((output / 'DCSRecorder-Staged-Playback.miz').read_bytes())
            for target, temporary, existed in replacements:
                if digest(target) != digest(incoming / 'bin' / target.name):
                    raise ValueError('Installed tape verification failed.')
        except Exception:
            for target, temporary, existed in replaced:
                if existed:
                    shutil.copy2(backup / target.name, target)
                elif target.exists():
                    target.unlink()
            for target, temporary, existed in replacements:
                if temporary.exists(): temporary.unlink()
            raise
        (output / 'activation.json').write_text(json.dumps({'mission': str(destination), 'recording': str(output / 'source-recording.csv'), 'backup': str(backup)}, indent=2), encoding='utf-8')
