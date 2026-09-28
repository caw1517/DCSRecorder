"""Integration checks for v3 automatic saving, schema, library and native tape."""
import csv
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from library import Library, EXPERIMENT
from recorded_flight import read, convert
from unittest.mock import patch
import zipfile


class EngineWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.library = Library({'saved_games': str(self.root), 'dcs': 'D:/DCS World'}, running=lambda: False)

    def tearDown(self):
        self.temp.cleanup()

    def capture(self, mode='normal'):
        here = Path(__file__).parent
        run = subprocess.run(['D:/DCS World/bin/luae.exe', str(here/'test_engine_sink.lua'),
                              str(here/'recording_sink.lua'), str(here/'engine_capture.lua'),
                              str(self.root), mode], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout+run.stderr)
        return list(self.library.recordings.glob('*.csv'))

    def test_capture_library_conversion_and_native_loader(self):
        files = self.capture();self.assertEqual(len(files), 1)
        source = files[0];original = source.read_bytes()
        metadata, samples, rows = read(source)
        self.assertTrue(metadata['engine_available'])
        self.assertEqual(len(samples[0]), 35)
        self.assertEqual(samples[0][25:29], [.8, .7, .5, .4])
        self.assertEqual(samples[0][29:], [.99, 1.06, 2.3, .98, .95, 1.15])
        self.assertEqual(self.library.entries()[0]['status_label'], 'Motion + surfaces + engines')
        tape = self.root/'recorded-flight.txt';convert(source, tape)
        self.assertEqual(tape.read_text().splitlines()[:4],
                         ['DCSREC_PLAYBACK_V3', '301', 'hornet-exterior-v1', 'hornet-native-engine-v1'])
        run = subprocess.run([str(EXPERIMENT/'build/Release/recorded_path_check.exe'), str(tape)],
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout+run.stderr)
        self.library.rename(source.name, 'Engine fixture')
        self.assertEqual(source.read_bytes(), original)

    def test_unavailable_or_mismatched_native_data_is_never_published(self):
        for mode in ('missing', 'late', 'wrong_player', 'unequal'):
            with self.subTest(mode=mode):
                self.assertEqual(self.capture(mode), [])
        self.assertEqual(len(list(self.library.recordings.glob('*.partial'))), 4)

    def test_native_timing_and_power_rejected(self):
        source = self.capture()[0]
        with source.open() as stream: rows = list(csv.reader(stream))
        header = next(i for i,r in enumerate(rows) if r[0]=='t')
        for field,value in [('engine_time','12'), ('engine_power_left','2.1'), ('engine_fan_left','nan')]:
            with self.subTest(field=field):
                changed = [r[:] for r in rows];changed[header+1][rows[header].index(field)] = value
                with source.open('w', newline='') as stream:csv.writer(stream).writerows(changed)
                with self.assertRaises(ValueError):read(source)


    def test_two_motion_samples_in_one_gui_frame_preserve_native_time(self):
        source = self.capture()[0]
        with source.open() as stream: rows = list(csv.reader(stream))
        header = next(i for i,r in enumerate(rows) if r[0]=='t')
        col = rows[header].index('engine_time')
        rows[header+1][col] = rows[header+2][col]
        with source.open('w', newline='') as stream:csv.writer(stream).writerows(rows)
        self.assertTrue(read(source)[0]['engine_available'])

    def test_new_practice_and_playback_choose_engine_pipeline(self):
        self.library.settings.update(engine_capture=True,
            baseline_mission=str(EXPERIMENT/'package/hornet-prototype/EFM-Probe-Hornet-left-roll-400KIAS.miz'),
            donor_mod=str(EXPERIMENT/'package/hornet-prototype/DCSRecorder-Hornet-Probe'))
        practice = self.library.practice()
        self.assertIn('Motion + surfaces + engines', practice['message'])
        self.assertIn('Practice-Engine-', practice['mission'])
        with zipfile.ZipFile(practice['mission']) as archive:
            mission = self.root/'mission.lua';mission.write_bytes(archive.read('mission'))
        harness = (EXPERIMENT/'check_recording.lua').read_text().replace(
            'function unit:isExist()', 'function unit:getID() return 16777472 end\nfunction unit:isExist()').replace(
            ' assert(i>=9', ' if i==28 or i==29 or i==89 or i==90 then return .5 end\n assert(i>=9')
        path = self.root/'capture.lua';path.write_text(harness)
        run = subprocess.run(['D:/DCS World/bin/luae.exe', str(path), str(EXPERIMENT), str(self.root), str(mission)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout+run.stderr)
        source = self.capture()[0]
        with patch.object(self.library, 'activate') as activate:
            self.library.playback(source.name)
        output, manifest, _ = activate.call_args.args
        self.assertEqual(manifest['module'], 'DCSRecorder-Hornet-Engine-Staged')
        self.assertEqual(manifest['recording']['recording_version'], 3)
        module = self.root/'Mods/aircraft'/manifest['module']/'bin';module.mkdir(parents=True)
        import shutil
        shutil.copy2(output/manifest['module']/'bin/HornetEngineStagedProbe.dll', module)
        self.library.activate(output, manifest, 'engine-fixture')
        self.assertEqual((module/'recorded-flight.txt').read_bytes(), (output/manifest['module']/'bin/recorded-flight.txt').read_bytes())


if __name__ == '__main__':
    unittest.main()
