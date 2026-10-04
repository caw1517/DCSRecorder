"""Contact-driven ground playback against the real taxi take and its authored scenes."""
import csv, io, json, shutil, sys, tempfile, unittest
from pathlib import Path
from library import Library, EXPERIMENT, TRIAL_BUILD, digest
from recorded_flight import read
import authored_missions as a

EVIDENCE = EXPERIMENT/'results/surface-start-2026-10-03'
TAKE = EVIDENCE/'source/20261004T033450Z-0001.csv'
SAVED = EVIDENCE/'source/Issue11-Parking_Test.miz'      # the take's own scene
EXPANDED = EVIDENCE/'source/Issue11-Parking_Test_V2.miz'  # adds a player Hornet
CONTROLLER = EVIDENCE/'controller'
AIRBORNE = EXPERIMENT/'results/authored-preparation-2026-10-02'
DCS = Path('D:/DCS World')
MODULE, CONTROL = 'DCSRecorder-Hornet-Authored-Test', 'DCSRecorderAuthoredControl'
sys.path.insert(0, str(EXPERIMENT/'authored-preparation'))


@unittest.skipUnless(TAKE.exists() and EXPANDED.exists() and (CONTROLLER/'HornetSurfaceProbe.dll').exists()
                     and (DCS/'bin/luae.exe').exists(), 'needs the surface evidence and DCS')
class SurfacePlayback(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)

    def tearDown(self): self.tmp.cleanup()

    def build(self, name='ground', saved_games=Path.home()/'Saved Games/DCS'):
        from prepare_playback import build
        return build(TAKE, EXPANDED, 2, 4, self.root/name, 'DCSRecorder-Authored-Playback-test.miz',
                     dcs=DCS, saved=SAVED, saved_games=saved_games)

    def test_grounded_rows_may_be_stationary_but_airborne_rows_may_not(self):
        metadata, samples, _ = read(TAKE)
        self.assertTrue(metadata['surface_available'])
        self.assertEqual({s[-1] for s in samples}, {1})
        text = TAKE.read_text(encoding='utf-8')
        rows = list(csv.reader(io.StringIO(text)))
        header = next(i for i, r in enumerate(rows) if r and r[0] == 't')
        rows[header+1][rows[header].index('in_air')] = '1'  # stationary first sample, declared airborne
        changed = self.root/'changed.csv'
        with changed.open('w', newline='', encoding='utf-8') as f: csv.writer(f, lineterminator='\n').writerows(rows)
        with self.assertRaisesRegex(ValueError, 'below the current airborne playback minimum'):
            read(changed)

    def test_ground_package_uses_surface_controller_and_hot_ground_start(self):
        result = self.build()
        frozen = json.loads((CONTROLLER/'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(result['profile'], 'authored-playback-ground-v1')
        self.assertEqual(result['controller_sha256'], frozen['sha256'])
        tape = self.root/'ground/payload/Mods/aircraft'/MODULE/'bin/recorded-flight.txt'
        self.assertEqual(tape.read_text().splitlines()[0], 'DCSREC_PLAYBACK_V7')
        mission = a.LuaData((self.root/'ground/mission.lua').read_text(encoding='utf-8')).assignment('mission')
        lead, player = sorted(a.aircraft(mission), key=lambda r: r['unit']['unitId'])
        self.assertEqual((lead['unit']['type'], lead['group']['route']['points'][1]['type']), (MODULE, 'TakeOffGroundHot'))
        self.assertLess(lead['unit']['speed'], 0.01)
        self.assertEqual(player['unit']['skill'], 'Player')
        self.assertEqual(player['group']['route']['points'][1]['type'], 'TakeOffGroundHot')
        self.assertIn('Blue Angels Mods by Razor, Coop & Thomaz', mission['requiredModules'])

    def test_scene_module_that_is_not_installed_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'needs modules that are not installed: Blue Angels Mods'):
            self.build(saved_games=self.root/'empty')

    @unittest.skipUnless((AIRBORNE/'recording-v4-live/20261003T174448Z-0001.csv').exists(), 'needs airborne evidence')
    def test_controller_switches_per_take_with_backup(self):
        saved = self.root/'saved'
        lib = Library(dict(saved_games=str(saved), dcs=str(DCS), build_trial=TRIAL_BUILD), running=lambda: False)
        take = AIRBORNE/'recording-v4-live/20261003T174448Z-0001.csv'
        shutil.copy2(take, lib.recordings/take.name)
        (saved/'Missions').mkdir(parents=True)
        shutil.copy2(AIRBORNE/'source-v4/054-Authored-Scene.miz', saved/'Missions/054-Authored-Scene.miz')
        options = lib.authored_playback_options(take.name)
        player = next(p['id'] for p in options['players'] if p['name'] == 'Wing Hornet')
        lib.authored_playback(take.name, player, options['source_sha256'])
        dll = saved/'Mods/aircraft'/MODULE/'bin/HornetAuthoredProbe.dll'
        airborne = digest(dll)
        manifest = self.build()
        lib.install_authored(self.root/'ground', manifest, 'ground-generation')
        self.assertEqual(digest(dll), manifest['controller_sha256'])
        self.assertNotEqual(airborne, manifest['controller_sha256'])
        backup = lib.home/'backups/ground-generation/Mods/aircraft'/MODULE/'bin/HornetAuthoredProbe.dll'
        self.assertEqual(digest(backup), airborne)


if __name__ == '__main__':
    unittest.main()
