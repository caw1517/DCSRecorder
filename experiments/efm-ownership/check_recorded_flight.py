"""End-to-end Lua capture -> CSV validation -> playback package, plus bad-take rejection."""
import csv,io,math,subprocess,tempfile,unittest
from pathlib import Path
from prepare_recording import ROOT,DCS,prepare
from prepare_staged_playback import prepare as prepare_playback
from recorded_flight import read,quaternion
from extract_recording_log import extract

class CaptureChecks(unittest.TestCase):
    def test_inverted_quaternion(self):
        for angle in [-3.7,-math.pi,-1,0,1,math.pi,3.7]:
            c,s=math.cos(angle),math.sin(angle)
            q=quaternion([1,0,0],[0,c,s],[0,-s,c])
            self.assertAlmostEqual(abs(q[0]*math.cos(angle/2)+q[1]*math.sin(angle/2)),1)

    def test_capture_and_import(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'package') as folder:
            out=Path(folder);(out/'DCSRecorder/recordings').mkdir(parents=True)
            prepare()
            result=subprocess.run([str(DCS/'bin/luae.exe'),str(ROOT/'check_recording.lua'),str(ROOT),out.as_posix(),str(ROOT/'package/recording/mission')],check=True,capture_output=True,text=True)
            logfile=Path(result.stdout.strip().splitlines()[-1])
            paths=extract(logfile,out/'DCSRecorder/recordings')
            self.assertEqual(len(paths),2)
            recording=paths[0]
            meta,samples,raw=read(recording)
            self.assertEqual(meta['samples'],301);self.assertAlmostEqual(meta['duration'],6)
            self.assertEqual(samples[-1][11],0.5);self.assertEqual(raw[-1]['rpm_left'],'')
            self.assertTrue(meta['exterior_available']);self.assertEqual(meta['state_profile'],'hornet-exterior-v1')
            self.assertLess(samples[0][15],0) # signed flap value survives
            self.assertEqual(extract(logfile,out/'DCSRecorder/recordings'),paths)
            brokenlog=out/'gap.log'
            lines=logfile.read_text().splitlines(True)
            brokenlog.write_text(''.join(line for line in lines if 'DCSREC_LOG,1,DATA,1,100,' not in line))
            with self.assertRaisesRegex(ValueError,'Missing or duplicate'):extract(brokenlog,out/'broken')
            manifest=prepare_playback(recording,out/'playback',ROOT/'package/hornet-prototype/EFM-Probe-Hornet-left-roll-400KIAS.miz',ROOT/'package/hornet-prototype/DCSRecorder-Hornet-Probe',DCS)
            subprocess.run([str(ROOT/'build/Release/recorded_path_check.exe'),str(out/'playback/DCSRecorder-Hornet-State-Staged/bin/recorded-flight.txt')],check=True)
            self.assertEqual(manifest['recording']['livery'],'Blue Angels Jet Team')
            original=list(csv.reader(io.StringIO(recording.read_text())))
            def rejected(rows,message):
                broken=out/'broken.csv'
                with broken.open('w',newline='') as f:csv.writer(f).writerows(rows)
                with self.assertRaisesRegex(ValueError,message):read(broken)
            rejected(original[:-1],'incomplete')
            first=next(i for i,row in enumerate(original) if row and row[0]=='t')+1
            altered=[row[:] for row in original];altered[first+1][0]=altered[first][0];rejected(altered,'Non-monotonic')
            altered=[row[:] for row in original];altered[first+1][2]='nan';rejected(altered,'Non-finite')
            altered=[row[:] for row in original];altered[first+1][1]='999999';rejected(altered,'discontinuity')
            for bad in ('nan','1.1',''):
                altered=[row[:] for row in original];altered[first][19]=bad;rejected(altered,'exterior|convert string')
            altered=[row[:] for row in original];altered[4][1]='unknown';rejected(altered,'profile')
            altered=[row[:] for row in original];altered[1][1]='TF-51D';rejected(altered,'Hornet')
            altered=[row[:] for row in original];altered[-1][1]='aircraft_lost';rejected(altered,'loss/error')
            altered=[row[:] for row in original];altered[first-1]=[];rejected(altered,'columns')
            print(result.stdout.strip())

if __name__=='__main__':unittest.main()
