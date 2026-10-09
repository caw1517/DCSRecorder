"""A formation take saves its shared epoch and in-take events in its metadata."""
import subprocess, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'experiments/efm-ownership'))
from recorded_flight import read
from formations import events

LUAE = Path('D:/DCS World/bin/luae.exe')


@unittest.skipUnless(LUAE.exists(), 'needs DCS luae.exe')
class FormationRecording(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        (self.root/'DCSRecorder/recordings').mkdir(parents=True)

    def tearDown(self): self.temp.cleanup()

    def capture(self, mode):
        here = Path(__file__).parent
        run = subprocess.run(list(map(str, [LUAE, here/'test_engine_sink.lua', here/'recording_sink.lua', here/'engine_capture.lua',
                                            self.root, mode, here/'smoke_capture.lua', 'contact', '2.9.30.28536'])),
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout+run.stderr)
        folder = self.root/'DCSRecorder/recordings'
        return list(folder.glob('*.csv')), list(folder.glob('*.partial')), (self.root/'DCSRecorder/save-status.txt').read_text()

    def test_events_join_the_metadata_when_the_take_is_saved(self):
        (take,), partial, status = self.capture('formation')
        self.assertEqual(partial, [])
        metadata, samples, raw = read(take)
        self.assertEqual((metadata['formation_id'], metadata['formation_version'], metadata['formation_epoch']),
                         ('f'*32, '3', '10.000000000'))
        self.assertEqual(float(raw[0]['t']), float(metadata['formation_epoch']))  # time zero is the shared epoch
        self.assertEqual([(e['kind'], e['association'][0], e['t']) for e in events(metadata['formation_events'])],
                         [('not_ready', 'c', None), ('failed', 'a', 2.0), ('ended', 'b', 3.0)])
        self.assertTrue(status.startswith('READY'))

    def test_an_interrupted_formation_take_stays_incomplete(self):
        saved, partial, _ = self.capture('formation_restart')
        self.assertEqual((saved, len(partial)), ([], 1))

    def test_a_malformed_event_fails_the_take(self):
        saved, partial, status = self.capture('formation_bad_event')
        self.assertEqual((saved, len(partial)), ([], 1))
        self.assertTrue(status.startswith('FAILED'), status)


if __name__ == '__main__':
    unittest.main()
