"""Exercise measured lights through the actual save hook, library and native tape."""
import csv
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from library import Library, EXPERIMENT
from recorded_flight import read, convert


class LightsWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.library=Library(dict(saved_games=str(self.root),dcs='D:/DCS World',engine_capture=True,
            smoke_capture=True,lights_capture=True,
            baseline_mission=str(EXPERIMENT/'package/hornet-prototype/EFM-Probe-Hornet-left-roll-400KIAS.miz'),
            donor_mod=str(EXPERIMENT/'package/hornet-prototype/DCSRecorder-Hornet-Probe')),running=lambda:False)

    def tearDown(self):self.temp.cleanup()

    def capture(self,smoke=True,mode='normal'):
        here=Path(__file__).parent
        run=subprocess.run(['D:/DCS World/bin/luae.exe',str(here/'test_engine_sink.lua'),str(here/'recording_sink.lua'),
            str(here/'engine_capture.lua'),str(self.root),mode,str(here/'smoke_capture.lua') if smoke else '-', 'lights'],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        return list(self.library.recordings.glob('*.csv'))

    def test_saved_lights_smoke_tape_and_module_selection(self):
        source,=self.capture();original=source.read_bytes()
        metadata,samples,raw=read(source)
        self.assertTrue(metadata['lights_available'] and metadata['smoke_available'])
        self.assertEqual(metadata['recording_version'],5)
        self.assertEqual(len(raw[0]),54);self.assertEqual(len(samples[0]),42)
        self.assertEqual(samples[0][-7:],[.1,.2,.3,.4,0,.6,.7])
        self.assertEqual(samples[2][-3],.9)
        self.assertEqual(self.library.entries()[0]['status_label'],'Motion + surfaces + engines + smoke + lights')
        tape=self.root/'recorded-flight.txt';convert(source,tape)
        self.assertEqual(tape.read_text().splitlines()[0],'DCSREC_PLAYBACK_V4')
        run=subprocess.run([str(EXPERIMENT/'build/Release/recorded_path_check.exe'),str(tape)],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        with patch.object(self.library,'activate')as activate:self.library.playback(source.name)
        output,manifest,_=activate.call_args.args
        self.assertEqual(manifest['module'],'DCSRecorder-Hornet-Lights-Staged')
        self.assertTrue(manifest['initial']['lights'])
        self.assertEqual(manifest['initial']['smoke_events'],metadata['smoke_events'])
        harness=self.root/'check_telemetry.lua'
        harness.write_text("dofile(arg[1]); local text=mission.trigrules[1].actions[2].text; "
            "local prefix=assert(text:match('^(.-)\\n%-%- Staged recorded playback')); "
            "assert(loadstring(prefix))(); assert(DCS_STAGED_CONFIG.exterior==1,'Missing exterior telemetry flag'); "
            "assert(DCS_STAGED_CONFIG.lights==true,'Missing light telemetry flag')")
        run=subprocess.run(['D:/DCS World/bin/luae.exe',str(harness),str(output/'mission')],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertEqual(source.read_bytes(),original)

    def test_lights_without_smoke(self):
        source,=self.capture(smoke=False);metadata,samples,raw=read(source)
        self.assertTrue(metadata['lights_available']);self.assertFalse(metadata['smoke_available'])
        self.assertEqual(len(raw[0]),52);self.assertEqual(len(samples[0]),42)
        self.assertEqual(self.library.entries()[0]['status_label'],'Motion + surfaces + engines + lights')

    def test_invalid_lights_never_publish_and_import_rejects(self):
        self.assertEqual(self.capture(mode='invalid_light'),[])
        self.assertTrue((self.library.home/'save-status.txt').read_text().startswith('FAILED'))
        source,=self.capture()
        with source.open()as stream:rows=list(csv.reader(stream))
        header=next(i for i,r in enumerate(rows)if r[0]=='t')
        for value in ('nan','-0.1','1.1'):
            changed=[r[:]for r in rows];changed[header+1][rows[header].index('arg_88')]=value
            with source.open('w',newline='')as stream:csv.writer(stream).writerows(changed)
            with self.assertRaises(ValueError):read(source)

    def test_packaged_practice_emits_measured_light_channels(self):
        result=self.library.practice()
        with zipfile.ZipFile(result['mission'])as archive:
            mission=self.root/'mission.lua';mission.write_bytes(archive.read('mission'))
        harness=(EXPERIMENT/'check_recording.lua').read_text().replace(
            'function unit:isExist()','function unit:getID() return 2 end\nfunction unit:isExist()').replace(
            ' assert(i>=9',' if i==28 or i==29 or i==89 or i==90 or i==88 or (i>=190 and i<=193) or i==210 or i==212 then return .5 end\n assert(i>=9')
        path=self.root/'capture.lua';path.write_text(harness)
        run=subprocess.run(['D:/DCS World/bin/luae.exe',str(path),str(EXPERIMENT),str(self.root),str(mission)],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        lines=(self.root/'dcs.log').read_text().splitlines()
        metadata=bytes.fromhex(next(l for l in lines if 'DCSREC_LOG,1,BEGIN,' in l).rsplit(',',1)[1]).decode()
        self.assertTrue(metadata.startswith('DCSREC,5\n'));self.assertIn('light_profile,hornet-lights-v1',metadata)
        fields=next(l for l in lines if 'DCSREC_LOG,1,DATA,' in l).split('DCSREC_LOG,1,DATA,')[1].split(',')[2:]
        self.assertEqual(len(fields),43);self.assertEqual(fields[-7:],['0.5']*7)


if __name__=='__main__':unittest.main()
