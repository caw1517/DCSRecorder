"""Offline packaging check for the formation prototype.

Uses the authored fixture scene (three Hornets) and its real recorded take. The
second take is that same recording relabelled as flown from Wing Hornet: enough
to package and run the generated hook/mission checks, never for flight.
Run: python -m unittest test_prepare -v   (needs DCS and a built HornetFormationProbe)
"""
import json, re, tempfile, unittest, zipfile
from pathlib import Path
import prepare

EVIDENCE = prepare.EFM/'results/authored-preparation-2026-10-02'
TAKE = EVIDENCE/'recording-v4-live/20261003T174448Z-0001.csv'
SOURCE = EVIDENCE/'source-v4/054-Authored-Scene.miz'


@unittest.skipUnless(TAKE.exists() and prepare.CONTROLLER.exists() and (prepare.DCS/'bin/luae.exe').exists(),
                     'needs the authored evidence, DCS and a built formation controller')
class FormationPackage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        text = TAKE.read_text(encoding='utf-8')
        wing = text.replace('source_unit_id,12201\n', 'source_unit_id,12202\n', 1).replace('source,"Record Hornet"\n', 'source,"Wing Hornet"\n', 1)
        # Same flight, one late sample 1 mm apart, so the two tapes differ.
        lines = wing.split('\n'); row = lines[-3].split(',')
        row[1] = repr(float(row[1])+0.001); lines[-3] = ','.join(row); wing = '\n'.join(lines)
        self.assertNotEqual(wing, text)
        self.wing = self.root/'wing.csv'; self.wing.write_text(wing, encoding='utf-8', newline='')

    def tearDown(self): self.tmp.cleanup()

    def build(self, takes, player=12203, name='070-Formation-Test.miz'):
        return prepare.build(SOURCE, player, self.root/'out', name, takes, allow_airborne=True)

    def test_two_positions_share_one_module_and_hook(self):
        result = self.build([(TAKE, 12201), (self.wing, 12202)])
        payload = self.root/'out/payload'
        tapes = sorted((payload/'Mods/aircraft'/prepare.MODULE/'bin/takes').glob('*.txt'))
        self.assertEqual([t.name for t in tapes], ['position-1.txt', 'position-2.txt'])
        self.assertEqual(len({p['token'] for p in result['positions']}), 2)
        self.assertEqual([p['name'] for p in result['positions']], ['Record Hornet', 'Wing Hornet'])
        # One playback type for every position; the player keeps the stock Hornet.
        with zipfile.ZipFile(payload/'Missions/070-Formation-Test.miz') as z:
            mission = z.read('mission').decode('utf-8')
        self.assertEqual(len(re.findall(r'\["type"\]\s*=\s*"'+re.escape(prepare.MODULE)+'"', mission)), 2)
        self.assertEqual(len(list(payload.glob('Mods/aircraft/*'))), 1)
        expected = (payload/'Scripts'/prepare.CONTROL/'expected.lua').read_text(encoding='utf-8')
        for unit in (12201, 12202): self.assertIn(f'["unit_id"]={unit},', expected)
        self.assertTrue(result['files'])
        self.assertEqual(json.loads((self.root/'out/manifest.json').read_text())['profile'], prepare.PROFILE)

    def test_refusals(self):
        with self.assertRaisesRegex(ValueError, 'at least two'):
            self.build([(TAKE, 12201)])
        with self.assertRaisesRegex(ValueError, 'its own aircraft'):
            self.build([(TAKE, 12201), (self.wing, 12201)])
        with self.assertRaisesRegex(ValueError, 'its own aircraft'):
            self.build([(TAKE, 12201), (self.wing, 12202)], player=12202)
        with self.assertRaisesRegex(ValueError, 'was flown from'):
            self.build([(TAKE, 12202), (self.wing, 12201)])
        with self.assertRaisesRegex(ValueError, 'ground-contact'):
            prepare.build(SOURCE, 12203, self.root/'live', 'x.miz', [(TAKE, 12201), (self.wing, 12202)])


if __name__ == '__main__':
    unittest.main()
