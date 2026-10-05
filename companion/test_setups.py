"""Setup switching against a small fake installation."""
import json, tempfile, unittest, zipfile
from pathlib import Path
from unittest.mock import patch
import setups


class Setups(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.saved = Path(self.tmp.name)/'saved'
        for module in ('DCSRecorder-Hornet', 'DCSRecorder-Hornet-Staged', 'DCSRecorder-Hornet-Authored-Test'):
            (self.saved/'Mods/aircraft'/module/'bin').mkdir(parents=True)
            (self.saved/'Mods/aircraft'/module/'entry.lua').write_text(module, encoding='utf-8')
            (self.saved/'Mods/aircraft'/module/'bin/recorded-flight.txt').write_text('tape ' + module, encoding='utf-8')
        hooks = self.saved/'Scripts/Hooks'; hooks.mkdir(parents=True)
        for hook in ('dcs-recorder-autosave.lua', 'DCSRecorderAuthoredControl.lua', 'dcs-recorder-sounder-logging.lua', 'DCS-SRS-hook.lua'):
            (hooks/hook).write_text(hook, encoding='utf-8')
        for folder in ('DCSRecorderEngineCapture', 'DCSRecorderReleaseControl'):
            (self.saved/'Scripts'/folder).mkdir(); (self.saved/'Scripts'/folder/'x.lua').write_text(folder, encoding='utf-8')
        (self.saved/'Missions').mkdir()
        for name, unit in (('old.miz', 'DCSRecorder-Hornet-Staged'), ('test.miz', 'DCSRecorder-Hornet-Authored-Test'),
                           ('mine.miz', 'DCSRecorder-Hornet'), ('stock.miz', 'FA-18C_hornet')):
            with zipfile.ZipFile(self.saved/'Missions'/name, 'w') as z: z.writestr('mission', f'mission = {{["type"] = "{unit}"}}')
        (self.saved/'DCSRecorder').mkdir()
        self.settings = self.saved/'DCSRecorder/companion-settings.json'
        self.settings.write_text(json.dumps(dict(saved_games=str(self.saved), setup='legacy', dcs='D:/DCS World')), encoding='utf-8')
        self.running = patch('setups.dcs_running', return_value=False); self.running.start()

    def tearDown(self): self.running.stop(); self.tmp.cleanup()

    def tree(self): return {p.relative_to(self.saved).as_posix(): p.read_bytes() for p in self.saved.rglob('*') if p.is_file()
                            and not p.relative_to(self.saved).as_posix().startswith('DCSRecorder/')}

    def test_normal_moves_everything_else_and_restore_brings_it_back(self):
        moved = setups.to_normal(self.settings)
        self.assertEqual(moved['legacy'], ['Mods/aircraft/DCSRecorder-Hornet-Staged', 'Missions/old.miz'])
        self.assertEqual(sorted(moved['developer']), ['Missions/test.miz', 'Mods/aircraft/DCSRecorder-Hornet-Authored-Test',
                                                      'Scripts/DCSRecorderReleaseControl', 'Scripts/Hooks/dcs-recorder-sounder-logging.lua'])
        self.assertEqual(sorted(self.tree()), sorted(['Mods/aircraft/DCSRecorder-Hornet/entry.lua', 'Mods/aircraft/DCSRecorder-Hornet/bin/recorded-flight.txt',
                                                      'Scripts/Hooks/dcs-recorder-autosave.lua', 'Scripts/Hooks/DCSRecorderAuthoredControl.lua',
                                                      'Scripts/Hooks/DCS-SRS-hook.lua', 'Scripts/DCSRecorderEngineCapture/x.lua',
                                                      'Missions/mine.miz', 'Missions/stock.miz']))
        self.assertNotIn('setup', json.loads(self.settings.read_text(encoding='utf-8')))
        self.assertEqual(setups.status(self.settings)['stored'], {'legacy': True, 'developer': True})
        setups.restore('developer', self.settings)
        with self.assertRaisesRegex(ValueError, 'No stored developer'): setups.restore('developer', self.settings)

    def test_restore_legacy_sets_legacy_setup_and_restores_bytes(self):
        before = self.tree()
        setups.to_normal(self.settings)
        setups.restore('legacy', self.settings); setups.restore('developer', self.settings)
        self.assertEqual(self.tree(), before)
        self.assertEqual(json.loads(self.settings.read_text(encoding='utf-8'))['setup'], 'legacy')
        self.assertEqual(setups.status(self.settings)['stored'], {'legacy': False, 'developer': False})

    def test_refuses_overwrite_and_running_dcs(self):
        setups.to_normal(self.settings)
        (self.saved/'Missions/old.miz').write_bytes(b'new file in the way')
        with self.assertRaisesRegex(ValueError, 'Would overwrite'): setups.restore('legacy', self.settings)
        self.assertTrue((self.saved/'DCSRecorder/setups/legacy/Mods/aircraft/DCSRecorder-Hornet-Staged/entry.lua').exists())
        with patch('setups.dcs_running', return_value=True), self.assertRaisesRegex(SystemExit, 'Close DCS'):
            setups.restore('developer', self.settings)


if __name__ == '__main__':
    unittest.main()
