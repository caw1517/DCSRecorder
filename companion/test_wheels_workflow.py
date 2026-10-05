"""Exercise wheel capture through save, library, native tape and mission packaging."""
import csv
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from library import Library, EXPERIMENT
from recorded_flight import read, convert


class WheelWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.library = Library(dict(setup='legacy',saved_games=str(self.root), dcs='D:/DCS World',
            engine_capture=True, smoke_capture=True, lights_capture=True, canopy_capture=True, wheels_capture=True,
            baseline_mission=str(EXPERIMENT/'package/hornet-prototype/EFM-Probe-Hornet-left-roll-400KIAS.miz'),
            donor_mod=str(EXPERIMENT/'package/hornet-prototype/DCSRecorder-Hornet-Probe')), running=lambda: False)

    def tearDown(self):
        self.temp.cleanup()

    def run_checked(self, command):
        run = subprocess.run(list(map(str, command)), capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout+run.stderr)

    def capture(self, smoke=True, mode='normal'):
        here = Path(__file__).parent
        self.run_checked(['D:/DCS World/bin/luae.exe', here/'test_engine_sink.lua', here/'recording_sink.lua',
            here/'engine_capture.lua', self.root, mode, here/'smoke_capture.lua' if smoke else '-', 'wheels'])
        return list(self.library.recordings.glob('*.csv'))

    def test_save_convert_package_preserves_initial_and_transitions(self):
        source, = self.capture()
        original = source.read_bytes()
        metadata, samples, raw = read(source)
        self.assertTrue(metadata['wheels_available'] and metadata['canopy_available'] and metadata['lights_available'] and metadata['smoke_available'])
        self.assertEqual(metadata['recording_version'], 7)
        self.assertEqual(len(raw[0]), 62)
        self.assertEqual(len(samples[0]), 50)
        self.assertEqual(samples[0][-1], -.7)
        self.assertEqual(samples[150][-1], 0)
        self.assertEqual(samples[-1][-1], .7)
        self.assertTrue(self.library.entries()[0]['status_label'].endswith(' + lights + canopy + wheels'))
        tape = self.root/'recorded-flight.txt'
        convert(source, tape)
        self.assertEqual(tape.read_text().splitlines()[0], 'DCSREC_PLAYBACK_V6')
        self.run_checked([EXPERIMENT/'build/Release/wheels_integrated_check.exe', tape])
        self.run_checked([EXPERIMENT/'build/Release/recorded_path_check.exe', tape])
        with patch.object(self.library, 'activate') as activate:
            self.library.playback(source.name)
        output, manifest, _ = activate.call_args.args
        self.assertEqual(manifest['module'], 'DCSRecorder-Hornet-Wheels-Staged')
        self.assertTrue(manifest['initial']['wheels'])
        self.assertEqual(manifest['initial']['smoke_events'], metadata['smoke_events'])
        harness = self.root/'check_config.lua'
        harness.write_text("dofile(arg[1]);local text=mission.trigrules[1].actions[2].text;"
            "local prefix=assert(text:match('^(.-)\\n%-%- Staged recorded playback'));assert(loadstring(prefix))();"
            "assert(DCS_STAGED_CONFIG.wheels==true and DCS_STAGED_CONFIG.canopy==true and DCS_STAGED_CONFIG.lights==true and DCS_STAGED_CONFIG.exterior==1)")
        self.run_checked(['D:/DCS World/bin/luae.exe', harness, output/'mission'])
        installed = self.library.saved/'Mods/aircraft'/manifest['module']
        shutil.copytree(output/manifest['module'], installed)
        prior_tape = b'previous canopy tape retained for rollback'
        (installed/'bin/recorded-flight.txt').write_bytes(prior_tape)
        self.library.activate(output, manifest, 'wheels-activation-test')
        self.assertEqual((installed/'bin/recorded-flight.txt').read_bytes(),
                         (output/manifest['module']/'bin/recorded-flight.txt').read_bytes())
        self.assertEqual((self.library.home/'backups/wheels-activation-test/recorded-flight.txt').read_bytes(), prior_tape)
        self.assertTrue((self.library.saved/'Missions/DCSRecorder-Playback-wheels-a.miz').is_file())
        self.assertEqual(source.read_bytes(), original)

    def test_optional_smoke_and_nonzero_initial_state(self):
        source, = self.capture(smoke=False)
        with source.open() as stream:
            rows = list(csv.reader(stream))
        header = next(i for i, row in enumerate(rows) if row[0] == 't')
        rows[header+1][-1] = '-0.391806871'
        with source.open('w', newline='') as stream:
            csv.writer(stream).writerows(rows)
        metadata, samples, raw = read(source)
        self.assertFalse(metadata['smoke_available'])
        self.assertTrue(metadata['canopy_available'])
        self.assertEqual(len(raw[0]), 60)
        self.assertEqual(samples[0][-1], -.391806871)
        tape = self.root/'initial-open.txt'
        convert(source, tape)
        self.run_checked([EXPERIMENT/'build/Release/wheels_integrated_check.exe', tape])

    def test_invalid_wheels_never_publish_and_import_rejects(self):
        self.assertEqual(self.capture(mode='invalid_wheel'), [])
        self.assertTrue((self.library.home/'save-status.txt').read_text().startswith('FAILED'))
        source, = self.capture()
        with source.open() as stream:
            rows = list(csv.reader(stream))
        header = next(i for i, row in enumerate(rows) if row[0] == 't')
        for value in ('nan', '-1.1', '1.1'):
            changed = [row[:] for row in rows]
            changed[header+1][-1] = value
            with source.open('w', newline='') as stream:
                csv.writer(stream).writerows(changed)
            with self.assertRaises(ValueError):
                read(source)
        changed = [row[:] for row in rows]
        changed[next(i for i, row in enumerate(changed) if row[0] == 'wheel_profile')][1] = 'unknown'
        with source.open('w', newline='') as stream:
            csv.writer(stream).writerows(changed)
        with self.assertRaisesRegex(ValueError, 'wheel profile'):
            read(source)

    def test_library_explains_invalid_speed_brake(self):
        source, = self.capture()
        with source.open() as stream:
            rows = list(csv.reader(stream))
        header = next(i for i, row in enumerate(rows) if row[0] == 't')
        for column, value, expected in (
            ('speedbrake', '1.1', 'Invalid speed-brake value 1.1 at 1.00 s'),
        ):
            with self.subTest(column=column, value=value):
                changed = [row[:] for row in rows]
                changed[header+51][rows[header].index(column)] = value
                with source.open('w', newline='') as stream:
                    csv.writer(stream).writerows(changed)
                original = source.read_bytes()
                entry, = self.library.entries()
                self.assertFalse(entry['supported'])
                self.assertIn(expected, entry['reason'])
                self.assertEqual(source.read_bytes(), original)


    def test_library_never_limits_recorded_speed(self):
        source, = self.capture()
        with source.open() as stream:
            rows = list(csv.reader(stream))
        header = next(i for i, row in enumerate(rows) if row[0] == 't')
        changed = [row[:] for row in rows]
        changed[header+51][rows[header].index('vx')] = '267.668715'
        with source.open('w', newline='') as stream:
            csv.writer(stream).writerows(changed)
        entry, = self.library.entries()
        self.assertNotIn('Recorded speed', entry['reason'])
        self.assertNotIn('playback m', entry['reason'])
    def test_packaged_practice_emits_measured_wheels(self):
        result = self.library.practice()
        with zipfile.ZipFile(result['mission']) as archive:
            mission = self.root/'mission.lua'
            mission.write_bytes(archive.read('mission'))
        harness = (EXPERIMENT/'check_recording.lua').read_text().replace(
            'function unit:isExist()', 'function unit:getID() return 2 end\nfunction unit:isExist()').replace(
            ' assert(i>=9', ' if i==2 then return -.391806871 end\n if i==1 or i==4 or i==6 or i==101 or i==102 or i==103 then return .75 end\n if i==38 then return .391806871 end\n if i==28 or i==29 or i==89 or i==90 or i==88 or (i>=190 and i<=193) or i==210 or i==212 then return .5 end\n assert(i>=9')
        path = self.root/'capture.lua'
        path.write_text(harness)
        self.run_checked(['D:/DCS World/bin/luae.exe', path, EXPERIMENT, self.root, mission])
        lines = (self.root/'dcs.log').read_text().splitlines()
        metadata = bytes.fromhex(next(line for line in lines if 'DCSREC_LOG,1,BEGIN,' in line).rsplit(',', 1)[1]).decode()
        self.assertTrue(metadata.startswith('DCSREC,7\n'))
        self.assertIn('wheel_profile,hornet-wheels-v1', metadata)
        fields = next(line for line in lines if 'DCSREC_LOG,1,DATA,' in line).split('DCSREC_LOG,1,DATA,')[1].split(',')[2:]
        self.assertEqual(len(fields), 51)
        self.assertEqual(float(fields[-1]), -.391806871)


if __name__ == '__main__':
    unittest.main()
