"""Measured smoke through automatic save, immutable library and generated missions."""
import csv
import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from library import Library, EXPERIMENT
from recorded_flight import read, convert


class SmokeWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.library = Library(dict(setup='legacy',saved_games=str(self.root), dcs='D:/DCS World',
            engine_capture=True, smoke_capture=True,
            baseline_mission=str(EXPERIMENT/'package/hornet-prototype/EFM-Probe-Hornet-left-roll-400KIAS.miz'),
            donor_mod=str(EXPERIMENT/'package/hornet-prototype/DCSRecorder-Hornet-Probe')), running=lambda: False)

    def tearDown(self):
        self.temp.cleanup()

    def capture(self, mode='normal'):
        here = Path(__file__).parent
        run = subprocess.run(['D:/DCS World/bin/luae.exe', str(here/'test_engine_sink.lua'),
                              str(here/'recording_sink.lua'), str(here/'engine_capture.lua'),
                              str(self.root), mode, str(here/'smoke_capture.lua')], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout+run.stderr)
        return list(self.library.recordings.glob('*.csv'))

    def test_saved_measurements_generate_step_events_and_accepted_native_tape(self):
        source, = self.capture()
        original = source.read_bytes()
        metadata, samples, raw = read(source)
        self.assertTrue(metadata['smoke_available'])
        self.assertEqual(metadata['recording_version'], 4)
        self.assertEqual([e['on'] for e in metadata['smoke_events']], [False, True, False])
        for event, expected in zip(metadata['smoke_events'], [0, 2.01, 4.01]):
            self.assertAlmostEqual(event['time'], expected)
        self.assertEqual(len(samples[0]), 35)
        self.assertEqual(len(raw[0]), 47)
        self.assertEqual(self.library.entries()[0]['status_label'], 'Motion + surfaces + engines + smoke')
        tape = self.root/'recorded-flight.txt'
        convert(source, tape)
        self.assertEqual(tape.read_text().splitlines()[0], 'DCSREC_PLAYBACK_V3')
        run = subprocess.run([str(EXPERIMENT/'build/Release/recorded_path_check.exe'), str(tape)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout+run.stderr)
        self.library.rename(source.name, 'Measured smoke')
        self.assertEqual(source.read_bytes(), original)
        with patch.object(self.library, 'activate') as activate:
            self.library.playback(source.name)
        output, manifest, _ = activate.call_args.args
        self.assertEqual(manifest['module'], 'DCSRecorder-Hornet-Engine-Staged')
        self.assertEqual(manifest['initial']['smoke_events'], metadata['smoke_events'])
        harness = self.root/'check.lua'
        harness.write_text("dofile(arg[1]); local found=0; for _,c in pairs(mission.coalition.blue.country)do for _,g in pairs((c.plane or {}).group or {})do for _,u in pairs(g.units)do if u.name=='StagedPlayback' then assert(u.payload.pylons[10].CLSID=='{INV-SMOKE-WHITE}');found=found+1 else assert(not u.payload.pylons[10])end end end end; assert(found==1); local text=mission.trigrules[1].actions[2].text; assert(text:find('smoke_events',1,true)); assert(text:find('SMOKE_ON_OFF',1,true))")
        run = subprocess.run(['D:/DCS World/bin/luae.exe',str(harness),str(output/'mission')], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout+run.stderr)

    def test_capture_failures_retain_partial_and_never_publish(self):
        for mode in ['smoke_missing','smoke_unavailable','smoke_mismatch','smoke_identity','smoke_clock']:
            with self.subTest(mode=mode):
                self.assertEqual(self.capture(mode), [])
                self.assertTrue((self.library.home/'save-status.txt').read_text().startswith('FAILED'))
        self.assertEqual(len(list(self.library.recordings.glob('*.partial'))), 5)

    def test_invalid_state_clock_and_loadout_are_rejected(self):
        source, = self.capture()
        with source.open() as stream: rows = list(csv.reader(stream))
        h = next(i for i,r in enumerate(rows) if r[0]=='t')
        for field,value in [('smoke_on','0.5'),('smoke_on','nan'),('smoke_time','10.2'),('smoke_clsid','{INV-SMOKE-RED}')]:
            with self.subTest(field=field,value=value):
                changed = [r[:] for r in rows]
                if field=='smoke_clsid':
                    next(r for r in changed if r[0]==field)[1]=value
                else: changed[h+1][rows[h].index(field)]=value
                with source.open('w',newline='') as stream: csv.writer(stream).writerows(changed)
                with self.assertRaises(ValueError): read(source)

    def test_practice_fits_station_and_emits_v4_metadata(self):
        practice = self.library.practice()
        self.assertIn('Practice-Smoke-', practice['mission'])
        with zipfile.ZipFile(practice['mission']) as archive:
            mission = self.root/'mission.lua';mission.write_bytes(archive.read('mission'))
        harness = (EXPERIMENT/'check_recording.lua').read_text().replace(
            'function unit:isExist()', 'function unit:getID() return 2 end\nfunction unit:isExist()').replace(
            ' assert(i>=9', ' if i==28 or i==29 or i==89 or i==90 then return .5 end\n assert(i>=9')
        path = self.root/'capture.lua';path.write_text(harness)
        run = subprocess.run(['D:/DCS World/bin/luae.exe',str(path),str(EXPERIMENT),str(self.root),str(mission)], capture_output=True, text=True)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        line = next(l for l in (self.root/'dcs.log').read_text().splitlines() if 'DCSREC_LOG,1,BEGIN,' in l)
        metadata = bytes.fromhex(line.rsplit(',',1)[1]).decode()
        self.assertTrue(metadata.startswith('DCSREC,4\n'))
        self.assertIn('\nsmoke_clsid,{INV-SMOKE-WHITE}\n',metadata)


if __name__ == '__main__':
    unittest.main()
