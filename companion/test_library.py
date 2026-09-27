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
        self.library = Library({'saved_games': str(self.root / 'saved'), 'dcs': str(self.dcs), 'accepted_baseline_sha256': digest(BASELINE)}, running=lambda: False)
        self.source = self.library.recordings / 'baseline.csv'; shutil.copy2(BASELINE, self.source)

    def tearDown(self):
        self.temp.cleanup()

    def test_baseline_and_rename_preserve_data(self):
        original = self.source.read_bytes()
        self.assertTrue(self.library.entries()[0]['supported'])
        self.library.rename('baseline.csv', 'My first flight')
        self.assertEqual(self.library.entries()[0]['name'], 'My first flight')
        self.assertEqual(self.source.read_bytes(), original)

    def test_incomplete_and_error_takes_are_not_playable(self):
        text = self.source.read_text()
        self.source.write_text(text[:text.rfind('END,')])
        self.assertFalse(self.library.entries()[0]['supported'])
        self.source.write_text(text.replace('END,user_stop,', 'END,mission_stop,'))
        self.assertFalse(self.library.entries()[0]['supported'])
        (self.library.recordings / 'unfinished.partial').write_text('partial')
        self.assertEqual(len(self.library.entries()), 1)

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

if __name__=='__main__':unittest.main()
