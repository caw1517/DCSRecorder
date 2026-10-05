import csv, io, json, os, shutil, subprocess, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from library import Library, EXPERIMENT, SUPPORTED_BUILD, digest

BASELINE = Path(os.environ.get('DCSREC_TEST_BASELINE', 'E:/Projects/DCS_Recorder/experiments/efm-ownership/package/first-recorded-flight/source-recording.csv'))

class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.dcs = self.root / 'dcs'; self.dcs.mkdir()
        (self.dcs / 'autoupdate.cfg').write_text(json.dumps({'version': SUPPORTED_BUILD}))
        self.library = Library({'setup': 'legacy', 'saved_games': str(self.root / 'saved'), 'dcs': str(self.dcs), 'accepted_baseline_sha256': digest(BASELINE)}, running=lambda: False)
        self.source = self.library.recordings / 'baseline.csv'; shutil.copy2(BASELINE, self.source)

    def tearDown(self):
        self.temp.cleanup()

    def test_baseline_and_rename_preserve_data(self):
        original = self.source.read_bytes()
        self.assertTrue(self.library.entries()[0]['supported'])
        self.library.rename('baseline.csv', 'My first flight')
        self.assertEqual(self.library.entries()[0]['name'], 'My first flight')
        self.assertEqual(self.source.read_bytes(), original)

    def test_normal_setup_lists_legacy_takes_but_offers_no_legacy_workflow(self):
        original = self.source.read_bytes()
        normal = Library({'saved_games': str(self.root / 'saved'), 'dcs': str(self.dcs),
                          'accepted_baseline_sha256': digest(BASELINE)}, running=lambda: False)
        entry = normal.entries()[0]
        self.assertEqual((entry['supported'], entry['legacy'], entry['status_label']), (False, True, 'Legacy · Motion only'))
        self.assertIn('play back only in the legacy setup', entry['reason'])
        with patch('library.prepare') as prepare:
            with self.assertRaisesRegex(ValueError, 'only in the legacy setup'): normal.playback('baseline.csv')
            prepare.assert_not_called()
        with self.assertRaisesRegex(ValueError, 'Practice missions belong to the legacy setup'): normal.practice()
        self.assertEqual(self.source.read_bytes(), original)
        with self.assertRaisesRegex(ValueError, 'Unknown companion setup'):
            Library({'setup': 'other', 'saved_games': str(self.root / 'saved')}, running=lambda: False)

    def test_legacy_take_explains_missing_gear_before_and_after_generation(self):
        original = self.source.read_bytes()
        entry = self.library.entries()[0]
        self.assertTrue(entry['supported'])
        self.assertEqual(entry['status_label'], 'Motion only')
        self.assertIn('Gear, flaps and control surfaces were not recorded', entry['reason'])
        self.assertIn('Create a new practice mission', entry['reason'])
        self.library.settings.update(baseline_mission='unused', donor_mod='unused')
        with patch('library.prepare', return_value={}), patch.object(self.library, 'activate'):
            result = self.library.playback('baseline.csv')
        self.assertIn('Gear, flaps and control surfaces were not recorded', result['message'])
        self.assertEqual(self.source.read_bytes(), original)

    def test_app_practice_captures_gear_and_selects_exterior_playback(self):
        import zipfile
        from extract_recording_log import extract
        from recorded_flight import read
        dcs = Path('D:/DCS World')
        self.library.settings.update(
            dcs=str(dcs),
            baseline_mission=str(EXPERIMENT/'package/hornet-prototype/EFM-Probe-Hornet-left-roll-400KIAS.miz'),
            donor_mod=str(EXPERIMENT/'package/hornet-prototype/DCSRecorder-Hornet-Probe'))
        practice = self.library.practice()
        self.assertIn('gear', practice['message'])
        mission = self.root/'mission.lua'
        with zipfile.ZipFile(practice['mission']) as archive:
            mission.write_bytes(archive.read('mission'))
        # Exercise the exact app-generated capture with a simulated deploying gear.
        harness = self.root/'capture.lua'
        harness.write_text((EXPERIMENT/'check_recording.lua').read_text().replace(
            'return (now-10)/20', 'return math.min(1,(now-10)/3)'))
        result = subprocess.run([str(dcs/'bin/luae.exe'), str(harness), str(EXPERIMENT),
                                 str(self.root), str(mission)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        recording = extract(self.root/'dcs.log', self.library.recordings)[0]
        original = recording.read_bytes()
        metadata, samples, rows = read(recording)
        self.assertTrue(metadata['exterior_available'])
        for key in ('arg_0', 'arg_3', 'arg_5'):
            values = [float(row[key]) for row in rows]
            self.assertLess(min(values), 0.01)
            self.assertEqual(max(values), 1)
        entry = next(item for item in self.library.entries() if item['id'] == recording.name)
        self.assertEqual(entry['status_label'], 'Motion + surfaces')
        with patch.object(self.library, 'activate') as activate:
            self.library.playback(recording.name)
        output, manifest, _ = activate.call_args.args
        self.assertEqual(manifest['module'], 'DCSRecorder-Hornet-State-Staged')
        tape = output/manifest['module']/'bin/recorded-flight.txt'
        lines = tape.read_text().splitlines()
        self.assertEqual(lines[0], 'DCSREC_PLAYBACK_V2')
        # Native tape: t, pose, velocity, brake, then three gear values.
        native = [list(map(float, line.split())) for line in lines[3:]]
        for index in (12, 13, 14):
            self.assertEqual([row[index] for row in native],
                             [row[index] for row in samples])
        check = subprocess.run([str(EXPERIMENT/'build/Release/recorded_path_check.exe'), str(tape)],
                               capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stdout+check.stderr)
        self.assertEqual(recording.read_bytes(), original)

    def test_incomplete_and_error_takes_are_not_playable(self):
        text = self.source.read_text()
        self.source.write_text(text[:text.rfind('END,')])
        self.assertFalse(self.library.entries()[0]['supported'])
        self.source.write_text(text.replace('END,user_stop,', 'END,mission_stop,'))
        self.assertFalse(self.library.entries()[0]['supported'])
        (self.library.recordings / 'unfinished.partial').write_text('partial')
        self.assertEqual(len(self.library.entries()), 1)

    def test_damaged_files_are_refused_apart_from_stopped_takes(self):
        # A take deliberately stopped with F10 Stop (at any point) stays playable;
        # every damaged or unfinished form is refused before staging, each with its own reason.
        text = self.source.read_text().replace('source,', f'capture_build,{SUPPORTED_BUILD}\nwind_ground,0\nwind_2000,0\nwind_8000,0\nsource,')
        self.source.write_text(text)
        self.assertTrue(self.library.entries()[0]['supported'])
        lines = text.splitlines(keepends=True)
        footer = next(i for i, line in enumerate(lines) if line.startswith('END,'))
        middle = footer // 2 + 4
        damaged = {
            'Recording is incomplete': text[:text.rfind('END,')],
            'Truncated sample row': ''.join(lines[:middle]) + lines[middle].rsplit(',', 3)[0] + '\n' + ''.join(lines[middle+1:]),
            'footer/sample count mismatch': ''.join(lines[:middle] + lines[middle+1:]),
            'aircraft loss/error': text.replace('END,user_stop,', 'END,aircraft_lost,'),
            'not explicitly stopped': text.replace('END,user_stop,', 'END,mission_stop,'),
        }
        for reason, content in damaged.items():
            self.source.write_text(content)
            entry = self.library.entries()[0]
            self.assertFalse(entry['supported'], reason)
            self.assertIn(reason, entry['reason'])

    def test_new_recording_requires_build_and_weather(self):
        text = self.source.read_text()
        self.source.write_text(text.replace('source,', 'note,new\nsource,'))
        self.assertFalse(self.library.entries()[0]['supported'])
        self.source.write_text(text.replace('source,', f'capture_build,{SUPPORTED_BUILD}\nwind_ground,0\nwind_2000,0\nwind_8000,0\nsource,'))
        self.assertTrue(self.library.entries()[0]['supported'])
        self.source.write_text(self.source.read_text().replace('wind_2000,0', 'wind_2000,5'))
        self.assertFalse(self.library.entries()[0]['supported'])

    def test_traversal_and_missing_source_rejected(self):
        for key in ('../baseline.csv', '..\\baseline.csv', 'C:baseline.csv', 'missing.csv'):
            with self.assertRaises(ValueError): self.library.source(key)

    def test_running_dcs_and_unsupported_build_block_mutation(self):
        self.library.running = lambda: True
        with self.assertRaisesRegex(ValueError, 'Close DCS'): self.library.check_environment()
        self.library.running = lambda: False
        (self.dcs / 'autoupdate.cfg').write_text('{"version":"new"}')
        with self.assertRaisesRegex(ValueError, 'unsupported'): self.library.check_environment()

    def test_failed_activation_rolls_back_changed_tapes(self):
        output=self.root/'package'; incoming=output/'DCSRecorder-Hornet-Staged/bin'; incoming.mkdir(parents=True)
        mod=self.library.saved/'Mods/aircraft/DCSRecorder-Hornet-Staged/bin'; mod.mkdir(parents=True)
        for name in ('HornetStagedProbe.dll','recorded-flight.txt','recorded-flight.json'):
            (incoming/name).write_text('new'); (mod/name).write_text('new' if name.endswith('.dll') else 'old')
        (output/'DCSRecorder-Staged-Playback.miz').write_text('mission')
        manifest={'files':{p.relative_to(output).as_posix():digest(p) for p in output.rglob('*') if p.is_file()}}
        original_replace=os.replace
        calls=[]
        def fail_second(source,target):
            calls.append(target)
            if len(calls)==2:raise OSError('simulated activation failure')
            original_replace(source,target)
        with patch('library.os.replace',side_effect=fail_second):
            with self.assertRaises(OSError):self.library.activate(output,manifest,'test1234')
        self.assertEqual((mod/'recorded-flight.txt').read_text(),'old')
        self.assertEqual((mod/'recorded-flight.json').read_text(),'old')

    def test_log_sink_saves_when_dcs_refuses_active_log_reads(self):
        saved=self.root/'locked-hook'; (saved/'Logs').mkdir(parents=True); (saved/'DCSRecorder/recordings').mkdir(parents=True)
        result=subprocess.run(['D:/DCS World/bin/luae.exe',str(Path(__file__).with_name('test_recording_sink.lua')),str(Path(__file__).with_name('recording_sink.lua')),str(saved),'deny_log_read'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(len(list((saved/'DCSRecorder/recordings').glob('*.csv'))),2,
                         'Explicit F10 Stop must publish both completed takes even when the active log cannot be opened')

    def test_log_sink_handles_dcs_void_success_io(self):
        saved=self.root/'void-hook'; (saved/'Logs').mkdir(parents=True); (saved/'DCSRecorder/recordings').mkdir(parents=True)
        result=subprocess.run(['D:/DCS World/bin/luae.exe',str(Path(__file__).with_name('test_recording_sink.lua')),str(Path(__file__).with_name('recording_sink.lua')),str(saved),'dcs_void_io'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(len(list((saved/'DCSRecorder/recordings').glob('*.csv'))),2,
                         'DCS-style successful file operations with no return value must not abandon completed takes')

    def test_log_sink_completes_only_explicit_valid_stops(self):
        saved=self.root/'hook'; (saved/'Logs').mkdir(parents=True); (saved/'DCSRecorder/recordings').mkdir(parents=True)
        result=subprocess.run(['D:/DCS World/bin/luae.exe',str(Path(__file__).with_name('test_recording_sink.lua')),str(Path(__file__).with_name('recording_sink.lua')),str(saved)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        files=list((saved/'DCSRecorder/recordings').glob('*.csv'))
        self.assertEqual(len(files),2)
        for file in files:
            with file.open() as stream: rows=list(csv.reader(stream))
            self.assertEqual(rows[-1],['END','user_stop','2'])
        self.assertEqual(len(list((saved/'DCSRecorder/recordings').glob('*.partial'))),3)

    def test_v2_sink_preserves_signed_surface_columns(self):
        saved=self.root/'v2-hook'; (saved/'Logs').mkdir(parents=True); (saved/'DCSRecorder/recordings').mkdir(parents=True)
        result=subprocess.run(['D:/DCS World/bin/luae.exe',str(Path(__file__).with_name('test_recording_sink.lua')),str(Path(__file__).with_name('recording_sink.lua')),str(saved),'dcs_void_io','v2'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        files=list((saved/'DCSRecorder/recordings').glob('*.csv'))
        self.assertEqual(len(files),2)
        for file in files:
            with file.open() as stream: rows=list(csv.reader(stream))
            self.assertEqual(rows[0],['DCSREC','2'])
            header=next(i for i,row in enumerate(rows) if row[0]=='t')
            self.assertEqual(len(rows[header]),32)
            self.assertEqual(dict(zip(rows[header],rows[header+1]))['arg_9'],'-0.4')

    def test_exterior_activation_preserves_legacy_controller_and_tape(self):
        module='DCSRecorder-Hornet-State-Staged';binary='HornetStateStagedProbe'
        output=self.root/'exterior-package'; incoming=output/module/'bin';incoming.mkdir(parents=True)
        mod=self.library.saved/'Mods/aircraft'/module/'bin';mod.mkdir(parents=True)
        legacy=self.library.saved/'Mods/aircraft/DCSRecorder-Hornet-Staged/bin';legacy.mkdir(parents=True)
        (legacy/'recorded-flight.txt').write_text('accepted legacy tape')
        (legacy/'HornetStagedProbe.dll').write_text('accepted legacy controller')
        for name in (binary+'.dll','recorded-flight.txt','recorded-flight.json'):(incoming/name).write_text('new')
        (mod/(binary+'.dll')).write_text('new')
        (output/'DCSRecorder-Staged-Playback.miz').write_text('mission')
        manifest={'module':module,'binary':binary,'files':{p.relative_to(output).as_posix():digest(p) for p in output.rglob('*') if p.is_file()}}
        self.library.activate(output,manifest,'exterior-test')
        self.assertEqual((mod/'recorded-flight.txt').read_text(),'new')
        self.assertEqual((legacy/'recorded-flight.txt').read_text(),'accepted legacy tape')
        self.assertEqual((legacy/'HornetStagedProbe.dll').read_text(),'accepted legacy controller')

    def test_exterior_activation_preserves_legacy_controller_and_tape(self):
        module='DCSRecorder-Hornet-State-Staged';binary='HornetStateStagedProbe'
        output=self.root/'exterior-package'; incoming=output/module/'bin';incoming.mkdir(parents=True)
        mod=self.library.saved/'Mods/aircraft'/module/'bin';mod.mkdir(parents=True)
        legacy=self.library.saved/'Mods/aircraft/DCSRecorder-Hornet-Staged/bin';legacy.mkdir(parents=True)
        (legacy/'recorded-flight.txt').write_text('accepted legacy tape')
        (legacy/'HornetStagedProbe.dll').write_text('accepted legacy controller')
        for name in (binary+'.dll','recorded-flight.txt','recorded-flight.json'):(incoming/name).write_text('new')
        (mod/(binary+'.dll')).write_text('new')
        (output/'DCSRecorder-Staged-Playback.miz').write_text('mission')
        manifest={'module':module,'binary':binary,'files':{p.relative_to(output).as_posix():digest(p) for p in output.rglob('*') if p.is_file()}}
        self.library.activate(output,manifest,'exterior-test')
        self.assertEqual((mod/'recorded-flight.txt').read_text(),'new')
        self.assertEqual((legacy/'recorded-flight.txt').read_text(),'accepted legacy tape')
        self.assertEqual((legacy/'HornetStagedProbe.dll').read_text(),'accepted legacy controller')

if __name__=='__main__':unittest.main()
