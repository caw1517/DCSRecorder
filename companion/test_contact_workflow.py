"""Exercise version-8 ground-contact capture through save, read and native tape."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from library import EXPERIMENT
from recorded_flight import read, convert
import authored_missions


class ContactWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        # The Lua fixture's mkdir is a stub; the companion normally creates this folder.
        (self.root/'DCSRecorder/recordings').mkdir(parents=True)

    def tearDown(self):
        self.temp.cleanup()

    def capture(self, mode='normal'):
        here = Path(__file__).parent
        run = subprocess.run(list(map(str, ['D:/DCS World/bin/luae.exe', here/'test_engine_sink.lua', here/'recording_sink.lua',
            here/'engine_capture.lua', self.root, mode, here/'smoke_capture.lua', 'contact'])), capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout+run.stderr)
        return list((self.root/'DCSRecorder/recordings').glob('*.csv'))

    def test_save_read_and_tape_keep_contact_evidence(self):
        source, = self.capture()
        metadata, samples, raw = read(source)
        self.assertEqual(metadata['recording_version'], 8)
        self.assertTrue(metadata['contact_available'] and metadata['wheels_available'])
        self.assertEqual(len(raw[0]), 67)
        self.assertEqual((raw[0]['in_air'], raw[0]['surface_type'], raw[-1]['in_air']), ('0', '5', '1'))
        contact = metadata['contact']
        self.assertEqual((contact['grounded_samples'], contact['airborne_samples']), (200, 101))
        self.assertTrue(contact['first_grounded'] and not contact['last_grounded'] and contact['health_unchanged'])
        self.assertEqual(contact['grounded_origin_agl'], [1987.5, 1987.5])
        self.assertEqual(contact['surfaces'], [5])
        # Grounded rows add one contact flag per sample on the V7 surface tape.
        self.assertTrue(metadata['surface_available'])
        self.assertEqual((len(samples[0]), samples[0][-1], samples[-1][-1]), (51, 1, 0))
        tape = self.root/'recorded-flight.txt'
        convert(source, tape)
        self.assertEqual(tape.read_text().splitlines()[0], 'DCSREC_PLAYBACK_V7')

    def test_damage_is_reported_not_hidden(self):
        source, = self.capture('damaged')
        metadata, _, _ = read(source)
        self.assertFalse(metadata['contact']['health_unchanged'])

    def test_invalid_contact_is_not_saved(self):
        self.assertEqual(self.capture('invalid_contact'), [])
        self.assertEqual(len(list((self.root/'DCSRecorder/recordings').glob('*.partial'))), 1)
        self.assertIn('Invalid contact value', (self.root/'DCSRecorder/save-status.txt').read_text())

    def test_authored_recorder_requests_contact(self):
        script = authored_missions.record_script('Record Hornet', 'DCSR_AUTHORED_2', 'a'*64)
        self.assertTrue(script.startswith('DCSR_AUTHORED_2_CONTACT=true\nDCSR_AUTHORED_2_WHEELS=true\n'))
        self.assertIn("'\\ncontact_profile,hornet-contact-v1'", script)
        self.assertTrue((EXPERIMENT/'contact_state.py').exists())
        self.assertNotIn('_SMOKE=true', script)

    def test_authored_recorder_requests_smoke_only_with_white_pod(self):
        pod = dict(payload=dict(pylons={10: dict(CLSID='{INV-SMOKE-WHITE}')}))
        self.assertTrue(authored_missions.carries_smoke(pod))
        self.assertFalse(authored_missions.carries_smoke(dict(payload=dict(pylons={10: dict(CLSID='<CLEAN>')}))))
        self.assertFalse(authored_missions.carries_smoke({}))
        script = authored_missions.record_script('Record Hornet', 'DCSR_AUTHORED_2', 'a'*64, smoke=True)
        self.assertTrue(script.startswith('DCSR_AUTHORED_2_SMOKE=true\nDCSR_AUTHORED_2_CONTACT=true\n'))


if __name__ == '__main__':
    unittest.main()
