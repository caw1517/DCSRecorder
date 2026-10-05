"""A short burst of mission log rows must not discard an otherwise valid take."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from library import Library,TRIAL_BUILD
from recorded_flight import read

class CaptureBatchTests(unittest.TestCase):
    def capture(self,mode):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        root=Path(temp.name);here=Path(__file__).parent
        library=Library(dict(setup='legacy',saved_games=str(root),dcs='D:/DCS World',build_trial=TRIAL_BUILD),running=lambda:False)
        result=subprocess.run(['D:/DCS World/bin/luae.exe',str(here/'test_engine_sink.lua'),
            str(here/'recording_sink.lua'),str(here/'engine_capture.lua'),str(root),mode,
            str(here/'smoke_capture.lua'),'wheels',TRIAL_BUILD],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        return library,list(library.recordings.glob('*.csv'))

    def test_short_midflight_batch_retains_every_sample_and_saves(self):
        library,files=self.capture('batch')
        self.assertEqual(len(files),1,(library.home/'save-status.txt').read_text())
        metadata,samples,raw=read(files[0])
        self.assertEqual(len(raw),301)
        self.assertEqual(metadata['capture_timing'],'frame-batch-v1')
        self.assertAlmostEqual(float(raw[100]['engine_time'])-float(raw[100]['t']),.07)
        self.assertEqual(len({row['engine_time'] for row in raw[100:104]}),1)
        self.assertEqual(len({row['smoke_time'] for row in raw[100:104]}),1)
        self.assertEqual(len(samples),301)
        self.assertTrue(library.entries()[0]['supported'])

    def test_initial_state_and_long_gaps_still_refused(self):
        for mode in ('batch_initial','batch_long'):
            with self.subTest(mode=mode):
                library,files=self.capture(mode)
                self.assertEqual(files,[])
                self.assertTrue(list(library.recordings.glob('*.partial')))

    def test_batch_requires_explicit_known_profile_and_build(self):
        _,files=self.capture('batch')
        source=files[0];original=source.read_text()
        for text,message in (
            (original.replace('capture_timing,frame-batch-v1\n',''),'within 50 ms'),
            (original.replace('frame-batch-v1','unknown'),'Unsupported capture timing'),
            (original.replace(TRIAL_BUILD,'2.9.29.27468'),'Unsupported capture timing')):
            with self.subTest(message=message):
                source.write_text(text)
                with self.assertRaisesRegex(ValueError,message):read(source)

if __name__=='__main__':unittest.main()
