"""The companion's formation workflow end to end, offline: start from a solo take,
record a position against it, make the version, play it, against the real
authored evidence, installed DCS and the locally built formation controller."""
import functools, json, shutil, tempfile, unittest
from pathlib import Path
from unittest import mock
from library import Library, EXPERIMENT, TRIAL_BUILD, digest

EVIDENCE = EXPERIMENT/'results/authored-preparation-2026-10-02'
TAKE = EVIDENCE/'recording-v4-live/20261003T174448Z-0001.csv'
SOURCE = EVIDENCE/'source-v4/054-Authored-Scene.miz'
DCS = Path('D:/DCS World')
CONTROLLER = EXPERIMENT/'build/Release/HornetFormationProbe.dll'
MODULE = 'DCSRecorder-Hornet-Formation'


@unittest.skipUnless(TAKE.exists() and CONTROLLER.exists() and (DCS/'bin/luae.exe').exists(),
                     'needs the authored evidence, DCS and a built formation controller')
class FormationLibrary(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); root = Path(self.tmp.name)
        self.saved = root/'saved'
        self.lib = Library(dict(saved_games=str(self.saved), dcs=str(DCS), build_trial=TRIAL_BUILD), running=lambda: False)
        (self.saved/'Missions').mkdir(parents=True)
        source = self.saved/'Missions'/SOURCE.name; shutil.copy2(SOURCE, source)
        self.revision = self.lib.lineage.create_lineage(source, digest(source), 'Diamond scene')
        self.lineage, self.sha = self.revision['lineage'], self.revision['sha256']
        self.lead = self.lib.lineage.association_for(self.revision, 12201)
        self.wing = self.lib.lineage.association_for(self.revision, 12202)
        # The lead's solo take and the recording copy it came from.
        package = self.lib.home/'authored/lead-copy'; package.mkdir(parents=True)
        (package/'manifest.json').write_text(json.dumps(dict(source_sha256=self.sha, association=self.lead, prepared_sha256='p'*64)))
        self.write_take('lead.csv', self.lead)
        # The fixture take is airborne; the formation controller plays ground takes live.
        real = self.lib.formation_builder
        def builder():
            module = real(); module.build = functools.partial(module.build, allow_airborne=True); return module
        patcher = mock.patch.object(self.lib, 'formation_builder', builder); patcher.start(); self.addCleanup(patcher.stop)

    def tearDown(self): self.tmp.cleanup()

    def write_take(self, name, association, unit=None, extra=''):
        text = TAKE.read_text(encoding='utf-8')
        anchor = f'authored_source_sha256,{self.sha}\n'
        self.assertIn(anchor, text)
        text = text.replace(anchor, anchor + f'authored_lineage,{self.lineage}\nauthored_association,{association}\n' + extra, 1)
        if unit:
            text = text.replace('source_unit_id,12201\n', f'source_unit_id,{unit[0]}\n', 1).replace('source,"Record Hornet"\n', f'source,"{unit[1]}"\n', 1)
            lines = text.split('\n'); row = lines[-3].split(','); row[1] = repr(float(row[1])+0.001); lines[-3] = ','.join(row)
            text = '\n'.join(lines)  # a distinct tape
        (self.lib.recordings/name).write_text(text, encoding='utf-8', newline='')

    def entry(self, name): return next(e for e in self.lib.entries() if e['id'] == name)

    def test_start_record_make_version_and_play(self):
        self.assertTrue(self.entry('lead.csv')['can_start_formation'])
        self.lib.formation_start('lead.csv', 'Diamond')
        (group,) = self.lib.formations()
        (formation,) = group['formations']
        self.assertEqual((group['mission'], formation['name'], [v['label'] for v in formation['versions']]),
                         ('Diamond scene', 'Diamond', ['v1 · started']))
        self.assertEqual(self.entry('lead.csv')['in_formations'], ['Diamond v1'])
        fid = formation['id']
        options = self.lib.formation_options(self.lineage, fid, 1)
        aircraft = {a['name']: a['position'] for a in options['scenes'][0]['aircraft']}
        self.assertEqual(aircraft, {'Record Hornet': self.lead, 'Wing Hornet': None, 'Scene Witness': None})

        # Record Wing against v1: the take-less Scene Witness is left out.
        result = self.lib.formation_recording(self.lineage, fid, 1, self.sha, 12202)
        mission = Path(result['mission'])
        self.assertTrue(mission.exists() and 'Left out: Scene Witness.' in result['message'])
        takes = sorted(p.name for p in (self.saved/'Mods/aircraft'/MODULE/'bin/takes').glob('*.txt'))
        self.assertEqual(takes, ['position-1.txt'])
        hook = (self.saved/'Scripts/Hooks/DCSRecorderFormationControl.lua').read_text(encoding='utf-8')
        self.assertIn('released(', hook)
        self.assertEqual(digest(SOURCE), self.sha)  # the authored source is untouched

        # The take that copy produced: the shared epoch and the lead's ending.
        played = json.dumps({self.lead: dict(take='lead.csv', sha256=digest(self.lib.recordings/'lead.csv'))})
        self.write_take('wing.csv', self.wing, (12202, 'Wing Hornet'),
                        extra=f"formation_id,{fid}\nformation_version,1\nformation_epoch,33.000000000\nformation_events,ended:{self.lead}@80.000\n")
        offer = self.entry('wing.csv')['offer']
        self.assertEqual((offer['formation'], offer['base'], offer['made'], offer['declined']), ('Diamond', 1, None, False))
        self.assertFalse(self.entry('wing.csv')['can_start_formation'])
        self.lib.formation_decline('wing.csv')
        self.assertTrue(self.entry('wing.csv')['offer']['declined'])
        self.lib.formation_make_version('wing.csv')  # Make version from this take, later
        self.assertEqual(self.entry('wing.csv')['offer']['made'], 2)
        with self.assertRaisesRegex(ValueError, 'already made version 2'):
            self.lib.formation_make_version('wing.csv')

        (formation,) = self.lib.formations()[0]['formations']
        v2 = next(v for v in formation['versions'] if v['number'] == 2)
        self.assertEqual(v2['label'], 'v2 · from v1 · added Wing Hornet')
        summary = {p['aircraft']: p['summary'] for p in v2['positions']}
        self.assertEqual(summary, {'Record Hornet': 'not flown against Wing Hornet', 'Wing Hornet': 'flown against all'})

        # Play v2 from the free aircraft; a position's aircraft is refused.
        with self.assertRaisesRegex(ValueError, 'holds a take'):
            self.lib.formation_play(self.lineage, fid, 2, self.sha, 12201)
        played = Path(self.lib.formation_play(self.lineage, fid, 2, self.sha, 12203)['mission'])
        self.assertTrue(played.exists() and mission.exists())  # earlier copies are never overwritten
        takes = sorted(p.name for p in (self.saved/'Mods/aircraft'/MODULE/'bin/takes').glob('*.txt'))
        self.assertEqual(takes, ['position-1.txt', 'position-2.txt'])

        # Re-fly Wing against v2 with Lead muted is refused: nothing would play.
        with self.assertRaisesRegex(ValueError, 'Every other position is muted'):
            self.lib.formation_recording(self.lineage, fid, 2, self.sha, 12202, [self.lead])
        with self.assertRaisesRegex(ValueError, 'Only other positions'):
            self.lib.formation_recording(self.lineage, fid, 2, self.sha, 12202, [self.wing])

    def test_old_takes_cannot_start_a_formation(self):
        shutil.copy2(TAKE, self.lib.recordings/'old.csv')
        self.assertFalse(self.entry('old.csv').get('can_start_formation'))
        with self.assertRaisesRegex(ValueError, 'before aircraft associations'):
            self.lib.formation_start('old.csv', 'Diamond')


if __name__ == '__main__':
    unittest.main()
