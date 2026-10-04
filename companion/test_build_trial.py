"""The new build is opt-in; test the complete capture-to-package trial path."""
import json
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from library import Library, EXPERIMENT, TRIAL_BUILD


class BuildTrialTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.settings=dict(saved_games=str(self.root),dcs='D:/DCS World',build_trial=TRIAL_BUILD,
            engine_capture=True,smoke_capture=True,lights_capture=True,canopy_capture=True,wheels_capture=True,
            baseline_mission=str(EXPERIMENT/'package/hornet-prototype/EFM-Probe-Hornet-left-roll-400KIAS.miz'),
            donor_mod=str(EXPERIMENT/'package/hornet-prototype/DCSRecorder-Hornet-Probe'))
        self.library=Library(self.settings,running=lambda:False)

    def tearDown(self):self.temp.cleanup()

    def test_capture_selects_new_helpers_and_playback_profile(self):
        here=Path(__file__).parent
        run=subprocess.run(['D:/DCS World/bin/luae.exe',str(here/'test_engine_sink.lua'),
            str(here/'recording_sink.lua'),str(here/'engine_capture.lua'),str(self.root),'normal',
            str(here/'smoke_capture.lua'),'wheels',TRIAL_BUILD],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        source,=self.library.recordings.glob('*.csv')
        before=source.read_bytes()
        self.assertEqual(self.library.validate(source)['capture_build'],TRIAL_BUILD)
        with patch.object(self.library,'activate') as activate:self.library.playback(source.name)
        output,manifest,_=activate.call_args.args
        self.assertEqual(manifest['dcs_build'],TRIAL_BUILD)
        self.assertEqual(manifest['module'],'DCSRecorder-Hornet-Wheels-Trial2930')
        self.assertEqual(manifest['binary'],'HornetWheelsTrial2930')
        self.assertTrue(manifest['recording']['smoke_available'])
        installed=self.library.saved/'Mods/aircraft'/manifest['module']
        shutil.copytree(output/manifest['module'],installed)
        self.library.activate(output,manifest,'trial-test')
        self.assertTrue((self.library.saved/'Missions/DCSRecorder-Playback-trial-te.miz').is_file())
        self.assertEqual((installed/'bin/recorded-flight.txt').read_bytes(),
                         (output/manifest['module']/'bin/recorded-flight.txt').read_bytes())
        self.assertEqual(source.read_bytes(),before)
        legacy=Library(dict(self.settings,build_trial=None),running=lambda:False)
        with self.assertRaisesRegex(ValueError,'unsupported'):legacy.validate(source)

    def test_practice_writes_actual_trial_build(self):
        result=self.library.practice()
        with zipfile.ZipFile(result['mission']) as archive:text=archive.read('mission').decode()
        self.assertIn('capture_build,'+TRIAL_BUILD,text)
        self.assertIn('capture_timing,frame-batch-v1',text)
        self.assertNotIn('capture_build,2.9.29.27468',text)

    def test_trial_never_accepts_unknown_build_or_legacy_module(self):
        with self.assertRaisesRegex(ValueError,'Unknown'):
            Library(dict(self.settings,build_trial='future'))
        with self.assertRaisesRegex(ValueError,'Unsupported playback module'):
            self.library.activate(self.root,dict(module='DCSRecorder-Hornet-Wheels-Staged',binary='HornetWheelsStagedProbe'),'test')
        fake=self.root/'fake';fake.mkdir();(fake/'autoupdate.cfg').write_text(json.dumps(dict(version='future')))
        self.library.settings['dcs']=str(fake)
        with self.assertRaisesRegex(ValueError,'unsupported'):self.library.check_environment()


if __name__=='__main__':unittest.main()
