"""A declared capture-hitch tolerance keeps a take through a rendering hitch."""
import subprocess, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'experiments/efm-ownership'))
from recorded_flight import read

LUAE = Path('D:/DCS World/bin/luae.exe')


@unittest.skipUnless(LUAE.exists(), 'needs DCS luae.exe')
class CaptureHitches(unittest.TestCase):
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
        return list(folder.glob('*.csv')), (self.root/'DCSRecorder/save-status.txt').read_text()

    def test_a_hitch_is_counted_and_the_take_plays(self):
        (take,), status = self.capture('batch_hitch')
        metadata, samples, raw = read(take)
        self.assertEqual((metadata['capture_hitch_tolerance'], metadata['capture_hitches']), ('1.0', '1'))
        self.assertTrue(400 <= int(metadata['capture_max_hitch_ms']) <= 450)
        self.assertEqual(len(samples), 301)

    def test_a_hitch_over_the_limit_still_fails(self):
        saved, status = self.capture('batch_hitch_over')
        self.assertEqual(saved, [])
        self.assertIn('over 1000 ms', status)

    def test_without_the_declaration_the_strict_limit_holds(self):
        saved, status = self.capture('batch_long')  # a 0.2 s batch on an undeclared take
        self.assertEqual(saved, [])


if __name__ == '__main__':
    unittest.main()
