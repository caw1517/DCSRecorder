"""Local flight library and mission preparation. No third-party Python dependencies."""
from __future__ import annotations
import csv, hashlib, json, os, shutil, subprocess, sys, tempfile, uuid, zipfile
from pathlib import Path

EXPERIMENT = Path(__file__).resolve().parents[1] / 'experiments' / 'efm-ownership'
sys.path.insert(0, str(EXPERIMENT))
from recorded_flight import read
from prepare_staged_playback import prepare, SUPPORTED_BUILD


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dcs_running():
    result = subprocess.run(['tasklist.exe', '/FI', 'IMAGENAME eq DCS.exe', '/FO', 'CSV', '/NH'],
                            capture_output=True, text=True, check=True,
                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    return any(row and row[0].lower() == 'dcs.exe' for row in csv.reader(result.stdout.splitlines()))


class Library:
    def __init__(self, settings, running=dcs_running):
        self.settings = settings
        self.saved = Path(settings['saved_games'])
        self.home = self.saved / 'DCSRecorder'
        self.recordings = self.home / 'recordings'
        self.recordings.mkdir(parents=True, exist_ok=True)
        self.running = running

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
        if metadata['livery'] != 'Blue Angels Jet Team':
            raise ValueError('Only Blue Angels Jet Team is currently supported.')
        # Old accepted baseline has no capture build/weather fields; only its exact
        # content hash is grandfathered. New practice missions capture these fields.
        if digest(path) != self.settings.get('accepted_baseline_sha256'):
            if metadata.get('capture_build') != SUPPORTED_BUILD:
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
                    'supported': False, 'duration': None}
            namefile = path.with_suffix('.name.json')
            if namefile.exists():
                try:
                    item['name'] = json.loads(namefile.read_text(encoding='utf-8'))['name']
                except (ValueError, KeyError, OSError):
                    pass
            try:
                metadata = self.validate(path)
                item.update(supported=True, duration=metadata['duration'], reason='Ready for playback')
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
        if actual != SUPPORTED_BUILD:
            raise ValueError(f'DCS {actual} is unsupported. This version requires {SUPPORTED_BUILD}.')
        if require_closed and self.running():
            raise ValueError('Close DCS before preparing or installing a mission, then try again.')
        return dcs

    def practice(self):
        dcs = self.check_environment()
        destination = self.saved / 'Missions' / ('DCSRecorder-Practice-' + uuid.uuid4().hex[:8] + '.miz')
        script = (EXPERIMENT / 'record_flight_mission.lua').read_text(encoding='utf-8-sig')
        # Metadata and wording are specific to the app-generated practice mission.
        script = script.replace("'\\nsource,'..csv(r.source)..'\\n'", "'\\nsource,'..csv(r.source)..'\\ncapture_build," + SUPPORTED_BUILD + "\\nwind_ground,'..tostring(env.mission.weather.wind.atGround.speed)..'\\nwind_2000,'..tostring(env.mission.weather.wind.at2000.speed)..'\\nwind_8000,'..tostring(env.mission.weather.wind.at8000.speed)..'\\n'")
        assert 'capture_build,' in script
        script = script.replace(' samples written to DCS.log. Ready for extraction. Keep this DCS session until the recording is collected.',
                                ' samples captured. Automatic save is pending; confirm the take appears in the companion flight library before closing DCS.')
        script = script.replace(' into DCS.log.', '. Use the companion flight library to confirm automatic saving after Stop.')
        with tempfile.TemporaryDirectory(dir=self.home) as folder:
            folder = Path(folder)
            with zipfile.ZipFile(self.settings['baseline_mission']) as source:
                (folder / 'baseline.lua').write_bytes(source.read('mission'))
            (folder / 'recorder.lua').write_text(script, encoding='utf-8')
            (folder / 'description.txt').write_text('DCS Recorder practice. Fly the stock Hornet in calm air. F10 > DCS Recorder > Start recording. Begin nearly level and airborne. Fast rolls and low-altitude airborne playback are under live validation. Ground starts and takeoff/landing playback are still being implemented. Record 5 to 300 seconds. F10 > Stop recording saves the take automatically. Confirm the take appears in the companion flight library before closing DCS.', encoding='utf-8')
            self.lua(dcs, 'make_recording_mission.lua', folder / 'baseline.lua', folder / 'recorder.lua', folder / 'mission', folder / 'description.txt')
            self.verify_mission(dcs, folder / 'mission', 1)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(self.settings['baseline_mission']) as source, zipfile.ZipFile(destination, 'x', zipfile.ZIP_DEFLATED) as target:
                for entry in source.infolist():
                    target.writestr(entry, (folder / 'mission').read_bytes() if entry.filename == 'mission' else source.read(entry.filename))
        return {'mission': str(destination), 'message': 'Practice mission created. Start DCS, fly it, and use F10 Start/Stop recording. Confirm the saved take appears here.'}

    def lua(self, dcs, script, *args):
        result = subprocess.run([str(dcs / 'bin/luae.exe'), str(EXPERIMENT / script), *map(str, args)],
                                capture_output=True, text=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if result.returncode:
            raise ValueError(result.stdout + result.stderr)

    def verify_mission(self, dcs, mission, count):
        self.lua(dcs, 'verify_hornet_requirements.lua', mission, dcs / 'Mods/aircraft/FA-18C/entry.lua', dcs / 'MissionEditor/modules/me_mission.lua')
        self.lua(dcs, 'verify_hornet_routes.lua', mission, dcs / 'MissionEditor/modules/me_route.lua', count)
        self.lua(dcs, 'verify_hornet_configuration.lua', mission, dcs, count)

    def playback(self, key):
        source = self.source(key)
        self.validate(source)
        dcs = self.check_environment()
        generation = uuid.uuid4().hex
        output = self.home / 'packages' / generation
        output.parent.mkdir(parents=True, exist_ok=True)
        manifest = prepare(source, output, self.settings['baseline_mission'], self.settings['donor_mod'], dcs)
        # Recheck immediately before replacing anything in the active installation.
        self.check_environment()
        self.activate(output, manifest, generation)
        mission = self.saved / 'Missions' / ('DCSRecorder-Playback-' + generation[:8] + '.miz')
        return {'mission': str(mission), 'message': 'Playback mission ready. Load this mission in DCS, then F10 > DCS Recorder > Start playback. Restart the mission to replay.'}

    def activate(self, output, manifest, generation):
        mod = self.saved / 'Mods/aircraft/DCSRecorder-Hornet-Staged'
        # Install once with the tested installer. Updates replace only the tape,
        # with the previous tape retained. DLL changes require explicit setup.
        if not mod.is_dir():
            raise ValueError('The staged playback module is missing. Install the tested module before generating playback.')
        incoming = output / 'DCSRecorder-Hornet-Staged'
        if digest(mod / 'bin/HornetStagedProbe.dll') != digest(incoming / 'bin/HornetStagedProbe.dll'):
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
