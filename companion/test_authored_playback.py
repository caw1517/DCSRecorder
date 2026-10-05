"""Companion authored playback against the real take/source evidence and installed DCS."""
import copy, json, shutil, tempfile, unittest
from pathlib import Path
from library import Library, EXPERIMENT, TRIAL_BUILD, digest

EVIDENCE = EXPERIMENT/'results/authored-preparation-2026-10-02'
TAKE = EVIDENCE/'recording-v4-live/20261003T174448Z-0001.csv'
SOURCE = EVIDENCE/'source-v4/054-Authored-Scene.miz'
DCS = Path('D:/DCS World')
MODULE, CONTROL = 'DCSRecorder-Hornet', 'DCSRecorderAuthoredControl'


@unittest.skipUnless(TAKE.exists() and (DCS/'bin/luae.exe').exists(), 'needs the authored evidence and DCS')
class AuthoredPlayback(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); root = Path(self.tmp.name)
        self.saved = root/'saved'
        self.lib = Library(dict(saved_games=str(self.saved), dcs=str(DCS), build_trial=TRIAL_BUILD), running=lambda: False)
        shutil.copy2(TAKE, self.lib.recordings/TAKE.name)
        (self.saved/'Missions').mkdir(parents=True)
        shutil.copy2(SOURCE, self.saved/'Missions'/SOURCE.name)

    def tearDown(self): self.tmp.cleanup()

    def options(self): return self.lib.authored_playback_options(TAKE.name)

    def player(self, name): return next(p['id'] for p in self.options()['players'] if p['name'] == name)

    def test_listed_with_players_other_than_the_recorded_aircraft(self):
        entry = self.lib.entries()[0]
        self.assertTrue(entry['supported'] and entry['authored'])
        options = self.options()
        self.assertEqual(options['lead'], 'Record Hornet')
        self.assertEqual([p['name'] for p in options['players']], ['Wing Hornet', 'Scene Witness'])
        self.assertEqual(options['source_sha256'], digest(SOURCE))

    def test_install_then_update_replaces_only_per_take_files(self):
        sha = self.options()['source_sha256']
        first = Path(self.lib.authored_playback(TAKE.name, self.player('Wing Hornet'), sha)['mission'])
        self.assertTrue(first.exists())
        module = self.saved/'Mods/aircraft'/MODULE
        dll, expected = module/'bin/DCSRecorderHornet.dll', self.saved/'Scripts'/CONTROL/'expected.lua'
        dll_hash, expected_hash, first_hash = digest(dll), digest(expected), digest(first)
        second = Path(self.lib.authored_playback(TAKE.name, self.player('Scene Witness'), sha)['mission'])
        self.assertNotEqual(first, second)
        self.assertEqual(digest(first), first_hash)            # earlier mission never overwritten
        self.assertEqual(digest(dll), dll_hash)                # shared module untouched
        self.assertNotEqual(digest(expected), expected_hash)   # per-take reference replaced
        hook = (self.saved/'Scripts/Hooks'/(CONTROL+'.lua')).read_text(encoding='utf-8')
        self.assertIn(second.name, hook); self.assertNotIn(first.name, hook)
        backups = list((self.lib.home/'backups').rglob('expected.lua'))
        self.assertEqual(len(backups), 1); self.assertEqual(digest(backups[0]), expected_hash)

    def test_drifted_shared_module_file_is_refused_without_changes(self):
        sha = self.options()['source_sha256']
        self.lib.authored_playback(TAKE.name, self.player('Wing Hornet'), sha)
        entry = self.saved/'Mods/aircraft'/MODULE/'entry.lua'
        entry.write_text(entry.read_text(encoding='utf-8')+'\n-- local edit\n', encoding='utf-8')
        expected = self.saved/'Scripts'/CONTROL/'expected.lua'; before = digest(expected)
        missions = sorted((self.saved/'Missions').glob('*.miz'))
        with self.assertRaisesRegex(ValueError, 'differs from this app'):
            self.lib.authored_playback(TAKE.name, self.player('Scene Witness'), sha)
        self.assertEqual(digest(expected), before)
        self.assertEqual(sorted((self.saved/'Missions').glob('*.miz')), missions)

    def test_missing_or_changed_source_is_refused(self):
        sha = self.options()['source_sha256']
        with self.assertRaisesRegex(ValueError, 'changed'):
            self.lib.authored_playback(TAKE.name, self.player('Wing Hornet'), '0'*64)
        (self.saved/'Missions'/SOURCE.name).unlink()
        with self.assertRaisesRegex(ValueError, 'was not found'):
            self.lib.authored_playback(TAKE.name, 12202, sha)
        self.assertFalse((self.saved/'Mods').exists())

    def test_recorded_aircraft_cannot_be_the_player(self):
        with self.assertRaisesRegex(ValueError, 'different stock Hornet'):
            self.lib.authored_playback(TAKE.name, 12201, self.options()['source_sha256'])


@unittest.skipUnless(TAKE.exists() and (DCS/'bin/luae.exe').exists(), 'needs the authored evidence and DCS')
class AssociatedPlayback(unittest.TestCase):
    """A take recorded through a saved revision plays in that scene and in a confirmed expansion."""
    def setUp(self):
        import authored_missions as a
        self.a = a
        self.tmp = tempfile.TemporaryDirectory(); root = Path(self.tmp.name)
        self.saved = root/'saved'
        self.lib = Library(dict(saved_games=str(self.saved), dcs=str(DCS), build_trial=TRIAL_BUILD, wheels_capture=True), running=lambda: False)
        (self.saved/'Missions').mkdir(parents=True)
        self.source = self.saved/'Missions'/SOURCE.name
        shutil.copy2(SOURCE, self.source)
        self.sha = digest(self.source)
        self.lib.authored_save_revision(self.source, self.sha, name='Authored scene')
        recording = self.lib.authored_recording(self.source, 12201, self.sha)
        manifest = json.loads((self.lib.home/'authored'/recording['package']/'manifest.json').read_text(encoding='utf-8'))
        self.association = manifest['association']
        # The evidence take as this recording copy now captures it: same flight, plus
        # the lineage/association lines that record_script adds.
        text = TAKE.read_text(encoding='utf-8')
        line = f'authored_source_sha256,{self.sha}\n'
        self.assertIn(line, text)
        provenance = f"authored_lineage,{manifest['lineage']}\nauthored_association,{self.association}\n"
        (self.lib.recordings/TAKE.name).write_text(text.replace(line, line+provenance), encoding='utf-8', newline='')

    def tearDown(self): self.tmp.cleanup()

    def expanded(self):
        """Three Hornets added alongside the existing three; the recorded aircraft is untouched."""
        a = self.a
        _, entries, mission = a.read_source(SOURCE)
        wing = a.selected_row(mission, 12202)
        container = next(c['plane']['group'] for s in mission['coalition'].values() for c in s['country'].values()
                         if 'plane' in c and any(g is wing['group'] for g in c['plane']['group'].values()))
        top_unit = max(r['unit']['unitId'] for r in a.aircraft(mission))
        top_group = max(r['group']['groupId'] for r in a.aircraft(mission))
        for n in range(1, 4):
            g = copy.deepcopy(wing['group']); u = g['units'][1]
            g['groupId'], g['name'] = top_group+n, f'Added Group {n}'
            u['unitId'], u['name'] = top_unit+n, f'Added Hornet {n}'
            for node in (u, g, *g['route']['points'].values()):
                node['x'] += 300*n
            container[max(container)+1] = g
        entries = dict(entries, mission=a.encoded('mission', mission))
        path = self.saved/'Missions'/'054-Authored-Scene-expanded.miz'
        path.write_bytes(a.packed(entries))
        return path, top_unit+1

    def test_new_take_is_bound_and_plays_in_a_confirmed_expansion(self):
        entry = self.lib.entries()[0]
        self.assertTrue(entry['supported'] and entry['authored'])
        self.assertIn('newer revision', entry['reason'])
        record = json.loads((self.lib.home/'take-provenance'/(TAKE.name+'.json')).read_text(encoding='utf-8'))
        self.assertEqual((record['association'], record['unit_id'], record['source_sha256']), (self.association, 12201, self.sha))
        options = self.lib.authored_playback_options(TAKE.name)
        self.assertEqual([s['saved'] for s in options['scenes']], [True])

        path, added = self.expanded()
        info = self.lib.authored_inspect(path)
        self.assertNotIn('revision', info)
        review = self.lib.authored_review(path, info['sha256'], info['lineages'][0]['id'])
        item, = review['aircraft']
        self.assertEqual(item['proposed'], 12201)
        self.assertEqual(len(review['changes']['aircraft_added']), 3)
        self.lib.authored_save_revision(path, info['sha256'], info['lineages'][0]['id'], decisions={self.association: 12201})

        options = self.lib.authored_playback_options(TAKE.name)
        self.assertEqual([s['saved'] for s in options['scenes']], [True, False])
        newer = options['scenes'][1]
        self.assertIn(added, [p['id'] for p in newer['players']])
        mission = Path(self.lib.authored_playback(TAKE.name, added, newer['sha256'])['mission'])
        self.assertTrue(mission.exists())
        package, = (self.lib.home/'authored-playback').iterdir()
        built = json.loads((package/'manifest.json').read_text(encoding='utf-8'))['mission_manifest']
        self.assertEqual((built['source_sha256'], built['saved_scene_sha256']), (newer['sha256'], self.sha))
        self.assertEqual(built['player_name'], 'Added Hornet 1')
        # The saved scene is still offered and untouched.
        self.assertEqual(digest(self.lib.lineage.snapshot(self.lib.lineage.find_revision(self.sha))), self.sha)

    def test_unrecorded_revision_cannot_be_used_and_legacy_take_stays_exact(self):
        path, _ = self.expanded()
        with self.assertRaisesRegex(ValueError, 'Save this mission revision'):
            self.lib.authored_recording(path, 12201, digest(path))
        shutil.copy2(TAKE, self.lib.recordings/('legacy-'+TAKE.name))
        options = self.lib.authored_playback_options('legacy-'+TAKE.name)
        self.assertEqual(options['provenance'], 'exact source only')
        self.assertEqual(len(options['scenes']), 1)


if __name__ == '__main__': unittest.main()
