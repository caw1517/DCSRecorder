"""Contracts for formations, write-once versions and derived flown-against flags."""
import hashlib
import tempfile
import unittest
from pathlib import Path
import authored_missions as a
from formations import Formations, flown_against
from test_mission_lineage import group
from mission_lineage import Registry


class FormationStore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        self.registry = Registry(self.root/'home')
        self.m = dict(theatre='Caucasus', weather=dict(wind={k: dict(speed=0) for k in ('atGround', 'at2000', 'at8000')}),
                      coalition=dict(blue=dict(country={1: dict(id=2, plane=dict(group={i: group(10+i, 1000*i) for i in range(1, 5)}))})),
                      descriptionText='DictKey_brief', trig={}, trigrules={})
        self.entries = {'l10n/DEFAULT/dictionary': b'dictionary={brief="original"}'}
        path = self.write('diamond.miz', self.m)
        self.revision = self.registry.create_lineage(path, a.sha(path.read_bytes()), 'Diamond')
        self.lineage = self.revision['lineage']
        self.lead, self.two, self.three = (self.registry.association_for(self.revision, u) for u in (11, 12, 13))
        self.store = Formations(self.registry)
        self.records = {}

    def tearDown(self): self.tmp.cleanup()

    def write(self, name, mission):
        path = self.root/name; path.write_bytes(a.packed(dict(self.entries, mission=a.encoded('mission', mission)))); return path

    def take(self, name, association, unit, plan=None, **metadata):
        """Bind a take through the registry, as the library does."""
        path = self.root/name; path.write_bytes(f'DCSREC,8\n{name}\n'.encode())
        prepared = hashlib.sha256(name.encode()).hexdigest()
        manifest = dict(source_sha256=self.revision['sha256'], association=association, prepared_sha256=prepared)
        if plan:
            manifest['formation'] = dict(plan, position=association)
        meta = dict(authored_source_sha256=self.revision['sha256'], authored_lineage=self.lineage,
                    authored_association=association, source_unit_id=str(unit), **metadata)
        record = self.registry.bind_take(path, meta, [(name, manifest)])
        self.records[name] = record
        return record

    def against(self, version, muted=(), events='', recorded=None):
        """A recording copy of `version`, with every non-muted position other than the flown one playing."""
        def plan(position):
            played = {k: v for k, v in version['positions'].items() if k != position and k not in muted}
            return dict(formation=self.formation, version=version['number'], played=played, muted=list(muted))
        def metadata(**extra):
            return dict(dict(formation_id=self.formation, formation_version=str(version['number']), formation_epoch='33.000',
                             formation_events=events), **(recorded or {}), **extra)
        return plan, metadata

    def record_against(self, name, version, association, unit, muted=(), events=''):
        plan, metadata = self.against(version, muted, events)
        return self.take(name, association, unit, plan(association), **metadata())

    def build_v4(self):
        lead = self.take('lead.csv', self.lead, 11)
        v1 = self.store.start(lead, 'Diamond')
        self.formation = self.store.formations(self.lineage)[0]['id']
        v2 = self.store.make_version(self.record_against('two.csv', v1, self.two, 12))
        v3 = self.store.make_version(self.record_against('three.csv', v2, self.three, 13))
        v3_bytes = (self.registry.root/self.lineage/'formations'/self.formation/'versions'/'3.json').read_bytes()
        v4 = self.store.make_version(self.record_against('two-refly.csv', v3, self.two, 12))
        return v1, v2, v3, v4, v3_bytes

    def test_a_formation_starts_from_an_associated_solo_take(self):
        lead = self.take('lead.csv', self.lead, 11)
        self.assertNotIn('flown_against', lead)
        v1 = self.store.start(lead, '  Diamond ')
        formation = self.store.formations(self.lineage)[0]
        self.assertEqual((formation['name'], formation['started_from']['take'], v1['number'], v1['base']), ('Diamond', 'lead.csv', 1, None))
        self.assertEqual(v1['positions'], {self.lead: dict(take='lead.csv', sha256=lead['take_sha256'])})
        with self.assertRaisesRegex(ValueError, 'before aircraft associations'):
            self.store.start(None, 'Old take')
        with self.assertRaisesRegex(ValueError, '1–100'):
            self.store.start(lead, ' ')

    def test_build_sequence_keeps_every_version_and_names_its_base(self):
        v1, v2, v3, v4, v3_bytes = self.build_v4()
        self.assertEqual([v['base'] for v in (v1, v2, v3, v4)], [None, 1, 2, 3])
        self.assertEqual(set(v4['positions']), {self.lead, self.two, self.three})
        self.assertEqual(v4['positions'][self.two]['take'], 'two-refly.csv')
        self.assertEqual(v3['positions'][self.two]['take'], 'two.csv')
        path = self.registry.root/self.lineage/'formations'/self.formation/'versions'/'3.json'
        self.assertEqual(path.read_bytes(), v3_bytes)  # earlier versions are byte-identical
        with self.assertRaises(FileExistsError):
            from mission_lineage import write_once; write_once(path, {})
        self.assertEqual(self.store.version(self.lineage, self.formation)['number'], 4)  # latest by default
        self.assertEqual(self.store.memberships(self.lineage)['lead.csv'], ['Diamond v1', 'Diamond v2', 'Diamond v3', 'Diamond v4'])

    def test_flags_are_derived_per_pair_and_mark_older_takes_after_a_refly(self):
        *_, v3, v4, _ = self.build_v4()
        flags = self.store.flags(v4, self.records)
        self.assertEqual(flags[self.three][self.two], dict(state='not_flown_against', reason='recorded_later'))  # #3 vs #2'
        self.assertEqual(flags[self.three][self.lead], dict(state='flown_against'))
        self.assertEqual(flags[self.two][self.three], dict(state='flown_against'))
        self.assertEqual(flags[self.lead][self.two], dict(state='not_flown_against', reason='recorded_later'))  # solo lead
        self.assertEqual(self.store.flags(v3, self.records)[self.three][self.two], dict(state='flown_against'))

    def test_mute_failure_and_not_ready_flags(self):
        *_, v4, _ = self.build_v4()
        events = f'failed:{self.lead}@41.25;ended:{self.two}@80.5'
        take = self.record_against('three-muted.csv', v4, self.three, 13, muted=(self.lead,))
        self.assertEqual(take['flown_against']['muted'], [self.lead])
        v5 = self.store.make_version(take)
        flags = self.store.flags(v5, self.records)
        self.assertEqual(flags[self.three][self.lead], dict(state='not_flown_against', reason='muted'))
        self.assertEqual(v5['positions'][self.lead], v4['positions'][self.lead])  # a muted position keeps its take
        take = self.record_against('three-failed.csv', v4, self.three, 13, events=events)
        flags = self.store.flags(self.store.make_version(take), self.records)
        self.assertEqual(flags[self.three][self.lead], dict(state='flown_against_until', t=41.25))
        take = self.record_against('three-late.csv', v4, self.three, 13, events=f'not_ready:{self.two}')
        self.assertEqual((take['flown_against']['not_ready'], list(take['flown_against']['played'])), ([self.two], [self.lead]))
        flags = self.store.flags(self.store.make_version(take), self.records)
        self.assertEqual(flags[self.three][self.two], dict(state='not_flown_against', reason='not_ready'))

    def test_a_declined_offer_can_become_a_version_later_once(self):
        *_, v4, _ = self.build_v4()
        take = self.record_against('declined.csv', v4, self.three, 13)
        base, positions = self.store.offer(take)
        self.assertEqual((base['number'], positions[self.three]['take']), (4, 'declined.csv'))
        self.assertEqual(len(self.store.versions(self.lineage, self.formation)), 4)  # declining writes nothing
        v5 = self.store.make_version(take)
        self.assertEqual((v5['number'], v5['base'], v5['created_by']['take']), (5, 4, 'declined.csv'))
        with self.assertRaisesRegex(ValueError, 'already made version 5'):
            self.store.make_version(take)
        with self.assertRaisesRegex(ValueError, 'not recorded against a formation'):
            self.store.make_version(self.records['lead.csv'])

    def test_any_version_can_be_the_base(self):
        v1, v2, *_ = self.build_v4()
        v5 = self.store.make_version(self.record_against('three-from-v2.csv', v2, self.three, 13))
        self.assertEqual((v5['number'], v5['base']), (5, 2))

    def test_binding_refuses_a_take_whose_package_does_not_match(self):
        v1, *_ = self.build_v4()
        plan, metadata = self.against(v1)
        for bad, message in ((dict(formation_version='2'), 'different formation version'),
                             (dict(formation_epoch=None), 'no shared epoch'),
                             (dict(formation_events=f'failed:{self.three}@3'), 'did not play'),
                             (dict(formation_events='failed:zz'), 'damaged')):
            with self.subTest(bad=bad), self.assertRaisesRegex(ValueError, message):
                self.take(f'bad-{len(bad)}-{message[:4]}.csv', self.three, 13, plan(self.three), **dict(metadata(), **bad))
        with self.assertRaisesRegex(ValueError, 'recording copy has none'):
            self.take('stray.csv', self.three, 13, None, **metadata())
        self.assertIsNone(flown_against({}, dict(prepared_sha256='x')))

    def test_rename_replaces_only_the_name(self):
        self.build_v4()
        self.store.rename(self.lineage, self.formation, 'Diamond show')
        self.assertEqual(self.store.formation(self.lineage, self.formation)['name'], 'Diamond show')
        self.assertEqual(len(self.store.versions(self.lineage, self.formation)), 4)

    def test_a_version_plays_only_where_every_position_is_confirmed(self):
        *_, v4, _ = self.build_v4()
        # A later revision where #3 is marked not present.
        path = self.write('without-three.miz', dict(self.m, descriptionText='DictKey_changed'))
        self.registry.join(path, a.sha(path.read_bytes()), self.lineage, {self.lead: 11, self.two: 12, self.three: None})
        playable, missing = self.store.scenes(self.lineage, v4)
        self.assertEqual([p['label'] for p in playable], ['diamond.miz'])
        self.assertEqual((missing[0]['label'], missing[0]['missing']), ('without-three.miz', [self.three]))
        self.assertEqual(playable[0]['units'], {self.lead: 11, self.two: 12, self.three: 13})


if __name__ == '__main__':
    unittest.main()
