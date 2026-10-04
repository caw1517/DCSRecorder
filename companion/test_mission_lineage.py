"""Contracts for companion-owned lineages, revisions and aircraft associations."""
import copy
from pathlib import Path
import tempfile
import unittest
import authored_missions as a
from mission_lineage import Registry


def group(uid, x):
    return dict(name=f'group {uid}', groupId=uid+100, units={1: dict(name=f'unit {uid}', unitId=uid, type='FA-18C_hornet',
                skill='High', livery_id='Blue Angels Jet Team', x=x, y=99, alt=2000, heading=0.5)},
                route=dict(points={1: dict(type='Turning Point', x=x, y=99, alt=2000, task=dict(id='ComboTask', params=dict(tasks={})))}))


class Lineages(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        self.registry = Registry(self.root/'home')
        self.m = dict(theatre='Caucasus', weather=dict(wind={k: dict(speed=0) for k in ('atGround', 'at2000', 'at8000')}),
                      coalition=dict(blue=dict(country={1: dict(id=2, plane=dict(group={i: group(10+i, 1000*i) for i in range(1, 5)}))})),
                      descriptionText='DictKey_brief', trig={}, trigrules={})
        self.entries = {'l10n/DEFAULT/dictionary': b'dictionary={brief="original"}', 'l10n/DEFAULT/sound.ogg': b'bytes'}
        self.four = self.write('four.miz')
        self.revision = self.registry.create_lineage(self.four, a.sha(self.four.read_bytes()), 'Ramp scene')
        self.lineage = self.revision['lineage']
        self.lead = self.registry.association_for(self.revision, 11)

    def tearDown(self): self.tmp.cleanup()

    def write(self, name, mission=None):
        entries = dict(self.entries, mission=a.encoded('mission', mission or self.m))
        path = self.root/name; path.write_bytes(a.packed(entries)); return path

    def groups(self, mission): return mission['coalition']['blue']['country'][1]['plane']['group']

    def seven(self, reverse=True):
        """Three Hornets added in Mission Editor, with the group container reordered."""
        m = copy.deepcopy(self.m); groups = self.groups(m)
        for uid in (15, 16, 17):
            groups[len(groups)+1] = group(uid, 1000*(uid-10))
        if reverse:
            m['coalition']['blue']['country'][1]['plane']['group'] = {i+1: g for i, g in enumerate(reversed(list(groups.values())))}
        return m

    def join(self, mission, decisions, name='next.miz'):
        path = self.write(name, mission)
        return self.registry.join(path, a.sha(path.read_bytes()), self.lineage, decisions)

    def review(self, mission, name='next.miz'):
        path = self.write(name, mission)
        return self.registry.review(path, a.sha(path.read_bytes()), self.lineage)

    def record(self, association=None, source=None):
        return dict(lineage=self.lineage, association=association or self.lead, source_sha256=source or self.revision['sha256'])

    def test_four_to_seven_expansion_keeps_the_recorded_aircraft(self):
        review = self.review(self.seven())
        item, = review['aircraft']
        self.assertEqual(item['proposed'], 11)
        self.assertEqual(len(item['candidates']), 7)  # count and order are not used to decide
        self.assertEqual([a['name'] for a in review['changes']['aircraft_added']], ['unit 15', 'unit 16', 'unit 17'])
        seven = self.join(self.seven(), {self.lead: 11})
        scenes = self.registry.scenes(self.record())
        self.assertEqual([(s['sha256'], s['saved']) for s in scenes], [(self.revision['sha256'], True), (seven['sha256'], False)])
        self.assertEqual(self.registry.mapping(seven)[self.lead]['decision'], 'confirmed')
        # A newly recorded aircraft has no counterpart in the older saved scene.
        added = self.registry.association_for(seven, 15)
        self.assertEqual([s['sha256'] for s in self.registry.scenes(self.record(added, seven['sha256']))], [seven['sha256']])
        # Repeat use of the same approved revision reuses its decision.
        self.assertEqual(self.registry.association_for(seven, 11), self.lead)

    def test_every_recorded_aircraft_needs_an_explicit_decision(self):
        with self.assertRaisesRegex(ValueError, 'Confirm every recorded aircraft'):
            self.join(self.seven(), {})
        with self.assertRaisesRegex(ValueError, 'Confirm every recorded aircraft'):
            self.join(self.seven(), {self.lead: 11, 'other': 12})
        self.assertEqual(len(self.registry.revisions(self.lineage)), 1)

    def test_moved_recorded_aircraft_cannot_be_confirmed(self):
        m = self.seven(); self.groups(m)[7]['units'][1]['x'] += 5  # unit 11, after the reorder
        self.assertEqual(a.selected_row(m, 11)['unit']['x'], 1005)
        item, = self.review(m)['aircraft']
        self.assertIsNone(item['proposed'])
        with self.assertRaisesRegex(ValueError, 'authored start or configuration'):
            self.join(m, {self.lead: 11})
        # Marking it absent saves the revision; the take keeps only its saved scene.
        self.join(m, {self.lead: None})
        self.assertEqual(len(self.registry.scenes(self.record())), 1)

    def test_reused_id_and_name_are_only_hints(self):
        m = copy.deepcopy(self.m); self.groups(m)[1] = group(11, 9000)  # deleted, recreated elsewhere
        item, = self.review(m)['aircraft']
        replacement = next(c for c in item['candidates'] if c['id'] == 11)
        self.assertEqual(replacement['hints'], ['same unit ID', 'same name'])
        self.assertFalse(replacement['compatible']); self.assertIsNone(item['proposed'])
        with self.assertRaisesRegex(ValueError, 'authored start or configuration'):
            self.join(m, {self.lead: 11})

    def test_rename_needs_confirmation_but_keeps_the_association(self):
        m = copy.deepcopy(self.m); self.groups(m)[1]['units'][1]['name'] = 'Lead'; self.groups(m)[1]['name'] = 'Lead group'
        item, = self.review(m)['aircraft']
        self.assertEqual(item['proposed'], 11)  # proposed, still not decided
        self.groups(m)[1]['units'][1]['skill'] = 'Player'  # role field, overwritten by every preparation
        revision = self.join(m, {self.lead: 11})
        self.assertEqual(self.registry.scenes(self.record())[1]['lead_name'], 'Lead')
        self.assertEqual(self.registry.mapping(revision)[self.lead]['unit_name'], 'Lead')

    def test_ambiguous_terrain_and_duplicate_revisions_are_refused(self):
        m = self.seven(False); self.groups(m)[5]['units'][1]['unitId'] = 11
        with self.assertRaisesRegex(ValueError, 'Duplicate aircraft IDs'):
            self.review(m)
        m = copy.deepcopy(self.m); m['theatre'] = 'Syria'
        with self.assertRaisesRegex(ValueError, 'terrain differs'):
            self.review(m)
        with self.assertRaisesRegex(ValueError, 'already saved'):
            self.registry.create_lineage(self.four, a.sha(self.four.read_bytes()), 'Again')
        with self.assertRaisesRegex(ValueError, 'changed after inspection'):
            self.registry.create_lineage(self.four, '0'*64, 'Stale')

    def test_saved_scene_is_immutable_and_survives_source_edits(self):
        snapshot = self.registry.snapshot(self.revision)
        self.write('four.miz', self.seven())  # the user keeps editing the original file
        self.assertEqual(a.sha(snapshot.read_bytes()), self.revision['sha256'])
        with self.assertRaises(FileExistsError):
            self.registry._store(self.lineage, snapshot, snapshot.read_bytes(), None)  # records are never replaced

    def bind(self, metadata, packages):
        take = self.root/'take.csv'
        if not take.exists(): take.write_bytes(b'DCSREC,7\nexample take bytes\n')
        return self.registry.bind_take(take, metadata, packages)

    def metadata(self, **changes):
        return dict(dict(authored_source_sha256=self.revision['sha256'], authored_lineage=self.lineage,
                         authored_association=self.lead, source_unit_id='11'), **changes)

    def package(self, prepared='p'*64):
        return ('generation', dict(source_sha256=self.revision['sha256'], association=self.lead, prepared_sha256=prepared))

    def test_take_binding_is_persisted_once(self):
        record = self.bind(self.metadata(), [self.package()])
        self.assertEqual((record['prepared_sha256'], record['unit_id'], record['recording_package']), ('p'*64, 11, 'generation'))
        self.assertEqual(self.bind(self.metadata(), []), record)  # read back, never recomputed
        (self.root/'take.csv').write_bytes(b'edited')
        with self.assertRaisesRegex(ValueError, 'changed after it was saved'):
            self.bind(self.metadata(), [self.package()])

    def test_takes_without_or_with_inconsistent_provenance(self):
        self.assertIsNone(self.bind(dict(authored_source_sha256=self.revision['sha256'], source_unit_id='11'), []))
        with self.assertRaisesRegex(ValueError, 'does not match its saved association'):
            self.bind(self.metadata(source_unit_id='12'), [self.package()])
        with self.assertRaisesRegex(ValueError, 'missing or ambiguous'):
            self.bind(self.metadata(), [self.package(), ('other', dict(self.package()[1], prepared_sha256='q'*64))])
        with self.assertRaisesRegex(ValueError, 'missing from the companion history'):
            self.bind(self.metadata(authored_source_sha256='0'*64), [self.package()])

    def playback(self, source, unit=11, player=12):
        first = [0.0]*50; first[1:4] = [100, 1800, 200]; first[8:11] = [140, 0, 0]
        metadata = dict(authored_source_sha256=self.revision['sha256'], source='unit 11', source_unit_id='11',
                        livery='Blue Angels Jet Team', aircraft='FA-18C_hornet', capture_build=a.BUILD, duration=8.7,
                        exterior_available=True, engine_available=True, lights_available=True, canopy_available=True, wheels_available=True)
        return a.playback_entries(source, unit, player, metadata, first, dict(fx=1, fz=0), 'DCSRecorder-Hornet-Authored-Test', 42,
                                  saved=self.registry.snapshot(self.revision))

    def test_playback_in_a_confirmed_newer_scene(self):
        m = self.seven(); a.selected_row(m, 11)['unit']['name'] = 'Lead'
        seven = self.join(m, {self.lead: 11})
        _, entries, mission, manifest = self.playback(self.registry.snapshot(seven), player=16)
        self.assertEqual((manifest['selected_name'], manifest['player_name']), ('Lead', 'unit 16'))
        self.assertEqual(manifest['saved_scene_sha256'], self.revision['sha256'])
        self.assertEqual(manifest['source_sha256'], seven['sha256'])
        self.assertTrue(manifest['preservation']['restored_structure_equals_source'])
        lead = a.selected_row(mission, 11)['unit']
        self.assertEqual((lead['x'], lead['alt'], lead['y']), (100, 1800, 200))  # the take's first pose, untranslated

    def test_playback_refuses_a_moved_recorded_aircraft_even_if_mapped_elsewhere(self):
        m = self.seven(); a.selected_row(m, 11)['group']['route']['points'][1]['alt'] = 2500
        path = self.write('moved.miz', m)
        with self.assertRaisesRegex(ValueError, 'differs in this scene'):
            self.playback(path)


if __name__ == '__main__':
    unittest.main()
