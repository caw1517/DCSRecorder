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

    def test_recorded_speed_is_never_limited(self):
        metadata, samples, _ = read(TAKE)
        self.assertTrue(metadata['surface_available'])
        self.assertEqual({s[-1] for s in samples}, {1})
        text = TAKE.read_text(encoding='utf-8')
        rows = list(csv.reader(io.StringIO(text)))
        header = next(i for i, r in enumerate(rows) if r and r[0] == 't')
        rows[header+1][rows[header].index('in_air')] = '1'  # stationary first sample, declared airborne
        changed = self.root/'changed.csv'
        with changed.open('w', newline='', encoding='utf-8') as f: csv.writer(f, lineterminator='\n').writerows(rows)
        metadata, samples, _ = read(changed)  # slow airborne sample is accepted
        self.assertEqual(samples[0][-1], 0)

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

    def rewritten(self, change):
        rows = list(csv.reader(io.StringIO(TAKE.read_text(encoding='utf-8'))))
        header = next(i for i, r in enumerate(rows) if r and r[0] == 't')
        rows = change(rows, header, rows[header])
        path = self.root/'rewritten.csv'
        with path.open('w', newline='', encoding='utf-8') as f: csv.writer(f, lineterminator='\n').writerows(rows)
        return read(path)[0]['parked_endpoint']

    def test_parked_endpoint_measured_and_configured(self):
        endpoint = read(TAKE)[0]['parked_endpoint']
        self.assertTrue(endpoint['eligible'])
        self.assertGreater(endpoint['measured']['tail_seconds'], 6)
        manifest = self.build()['mission_manifest']
        self.assertTrue(manifest['initial']['parked'] and manifest['initial']['contact'])
        self.assertEqual(manifest['parked_endpoint'], endpoint)

    def test_moving_or_engine_off_ending_is_not_parked(self):
        def cut(rows, header, names):
            # End the take one second after the taxi stop began (still decelerating).
            body = rows[header+1:-1]
            keep = next(i for i, r in enumerate(body) if float(r[0])-float(body[0][0]) > 20.0)
            return rows[:header+1]+body[:keep]+[['END', 'user_stop', str(keep)]]
        moving = self.rewritten(cut)
        self.assertFalse(moving['eligible'])
        self.assertIn('moving', moving['measured']['boundary_failure'])

        def engine_off(rows, header, names):
            column = names.index('engine_core_right')
            for row in rows[-60:-1]: row[column] = '0.3'
            return rows
        stopped = self.rewritten(engine_off)
        self.assertFalse(stopped['eligible'])
        self.assertEqual(stopped['measured']['boundary_failure'], ['engines_not_running'])

    @unittest.skipUnless((EVIDENCE/'source/Issue11-NightSmoke_Parking_V1.miz').exists(), 'needs the night mission')
    def test_other_client_slots_are_kept_but_a_second_player_is_refused(self):
        night = EVIDENCE/'source/Issue11-NightSmoke_Parking_V1.miz'
        manifest = a.prepare_recording(night, 2, self.root/'record')
        self.assertIn('Client slot "Aerial-2-1" (not flown in this session)', manifest['behavior']['preserved'])
        mission = a.read_source(night)[2]
        other = next(r for r in a.aircraft(mission) if r['unit']['unitId'] == 4)
        self.assertEqual(other['unit']['skill'], 'Client')
        other['unit']['skill'] = 'Player'
        with self.assertRaisesRegex(ValueError, '"Aerial-2-1" is also set to Player'):
            a.validate_supported(mission, [2])

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
