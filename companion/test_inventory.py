"""Inventory and snapshot against a small fake DCS installation."""
import json, tempfile, unittest, zipfile
from unittest.mock import patch
from pathlib import Path
import inventory


class Inventory(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); root = Path(self.tmp.name)
        self.dcs, self.saved = root/'dcs', root/'saved'
        (self.dcs).mkdir(); (self.dcs/'autoupdate.cfg').write_text('{"version": "2.9.30.28536"}', encoding='utf-8')
        mod = self.saved/'Mods/aircraft/DCSRecorder-Hornet-Staged'; (mod/'bin').mkdir(parents=True)
        (mod/'entry.lua').write_text("local id = 'DCSRecorder-Hornet-Staged'\ndeclare_plugin(id, {displayName='DCS Recorder Hornet Prototype',\n"
                                     "binaries={'HornetStagedProbe'}})\n", encoding='utf-8')
        (mod/'bin/HornetStagedProbe.dll').write_bytes(b'dll')
        (mod/'bin/recorded-flight.txt').write_text('DCSREC_PLAYBACK_V1\n1,2,3\n', encoding='utf-8')
        (self.saved/'Mods/aircraft/uh60l').mkdir(); (self.saved/'Mods/aircraft/uh60l/entry.lua').write_text('x', encoding='utf-8')
        (self.saved/'Scripts/Hooks').mkdir(parents=True)
        (self.saved/'Scripts/Hooks/dcs-recorder.lua').write_text('hook', encoding='utf-8')
        (self.saved/'Scripts/Hooks/DCS-SRS-hook.lua').write_text('srs', encoding='utf-8')
        home = self.saved/'DCSRecorder'; (home/'recordings').mkdir(parents=True)
        (home/'recordings/a.csv').write_text('DCSREC,8\n', encoding='utf-8')
        (home/'companion.lock').write_text('pid', encoding='utf-8')
        self.settings = home/'companion-settings.json'
        self.settings.write_text(json.dumps(dict(dcs=str(self.dcs), saved_games=str(self.saved))), encoding='utf-8')
        (self.saved/'Missions').mkdir()
        for name, unit in (('uses.miz', 'DCSRecorder-Hornet-Staged'), ('gone.miz', 'DCSRecorder-Hornet-Lights-Staged'), ('stock.miz', 'FA-18C_hornet')):
            with zipfile.ZipFile(self.saved/'Missions'/name, 'w') as z: z.writestr('mission', f'mission = {{["type"] = "{unit}"}}')
        (self.saved/'Missions/broken.miz').write_bytes(b'not a zip')

    def tearDown(self): self.tmp.cleanup()

    def test_inventory_lists_recorder_files_only(self):
        m = inventory.inventory(self.settings)
        self.assertEqual(m['dcs']['build'], '2.9.30.28536')
        mod = m['modules']['DCSRecorder-Hornet-Staged']
        self.assertEqual((mod['type_id'], mod['binaries'], mod['tape']['version']),
                         ('DCSRecorder-Hornet-Staged', ['HornetStagedProbe'], 'DCSREC_PLAYBACK_V1'))
        self.assertEqual(m['hooks'], ['dcs-recorder.lua'])
        self.assertEqual(sorted(m['missions']), ['Missions/gone.miz', 'Missions/uses.miz'])
        self.assertEqual(m['missions']['Missions/gone.miz']['unregistered'], ['DCSRecorder-Hornet-Lights-Staged'])
        self.assertIn('Missions/broken.miz', m['unreadable_missions'])
        self.assertEqual(m['recordings'], {'a.csv': 'DCSREC,8'})
        self.assertNotIn('Mods/aircraft/uh60l/entry.lua', m['files'])
        self.assertNotIn('Scripts/Hooks/DCS-SRS-hook.lua', m['files'])
        self.assertIsNone(m['files']['DCSRecorder/companion.lock']['sha256'])

    def test_snapshot_copies_and_verifies_without_touching_originals(self):
        before = {p: p.read_bytes() for p in self.saved.rglob('*') if p.is_file()}
        with patch('inventory.dcs_running', return_value=True), self.assertRaisesRegex(SystemExit, 'Close DCS'):
            inventory.snapshot(Path(self.tmp.name)/'archive', self.settings)
        with patch('inventory.dcs_running', return_value=False):
            target, m, result = inventory.snapshot(Path(self.tmp.name)/'archive', self.settings)
        self.assertTrue(result['verified'], result)
        self.assertEqual(result['files'], len(m['files']) - 1)
        self.assertEqual(result['listed_not_copied'], ['DCSRecorder/companion.lock'])
        self.assertEqual((target/'files/Mods/aircraft/DCSRecorder-Hornet-Staged/bin/recorded-flight.txt').read_text(encoding='utf-8'),
                         'DCSREC_PLAYBACK_V1\n1,2,3\n')
        self.assertEqual(before, {p: p.read_bytes() for p in self.saved.rglob('*') if p.is_file()})


if __name__ == '__main__':
    unittest.main()
