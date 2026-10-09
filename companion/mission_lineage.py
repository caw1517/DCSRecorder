"""Companion-owned authored-mission lineages, revisions and aircraft associations.

A lineage is one authored mission as the user keeps editing it. Each revision is an
immutable source snapshot. An association is one aircraft followed across revisions.
Editor IDs, names, counts and container order are only hints: joining a changed
revision requires one explicit decision per known association, recorded once and
never rewritten. Takes point at the revision, association and prepared copy that
actually produced them; takes without that provenance stay on the exact-source path.
"""
from __future__ import annotations
import copy, datetime, json, uuid
from pathlib import Path
import authored_missions as a

PROFILE = 'authored-lineage-v1'


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')


def write_once(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = value if isinstance(value, bytes) else (json.dumps(value, indent=2, sort_keys=True) + '\n').encode('utf-8')
    with path.open('xb') as stream:  # immutable: an existing record is never replaced
        stream.write(data)


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def describe(row):
    unit, group = row['unit'], row['group']
    start = group.get('route', {}).get('points', {}).get(1, {})
    return dict(id=unit.get('unitId'), name=unit.get('name'), group=group.get('name'), group_id=group.get('groupId'),
                type=unit.get('type'), livery=unit.get('livery_id'), skill=unit.get('skill'), start=start.get('type'),
                x=unit.get('x'), y=unit.get('y'), alt=unit.get('alt'), heading=unit.get('heading'))


def dictionary(entries):
    blob = entries.get('l10n/DEFAULT/dictionary')
    if blob is None:
        return {}
    return a.LuaData(blob.decode('utf-8-sig')).assignment('dictionary')


def scene_changes(old_entries, old_mission, new_entries, new_mission):
    """A review summary. Unit IDs are used only to line rows up for display."""
    old = {r['unit'].get('unitId'): r for r in a.aircraft(old_mission)}
    new = {r['unit'].get('unitId'): r for r in a.aircraft(new_mission)}
    changed = [dict(**describe(new[i]), changes=a.compatibility(old[i], new[i])[:12]) for i in sorted(set(old) & set(new), key=str)
               if a.compatibility(old[i], new[i]) or old[i]['unit'].get('name') != new[i]['unit'].get('name')]
    def without_aircraft(mission):
        m = copy.deepcopy(mission)
        for coalition in m.get('coalition', {}).values():
            for country in (coalition.get('country', {}) if isinstance(coalition, dict) else {}).values():
                country.pop('plane', None); country.pop('helicopter', None)
        return m
    o, n = without_aircraft(old_mission), without_aircraft(new_mission)
    settings = sorted(str(k) for k in set(o) | set(n) if o.get(k) != n.get(k))
    od, nd = dictionary(old_entries), dictionary(new_entries)
    members = sorted(set(old_entries) | set(new_entries))
    return dict(
        aircraft_added=[describe(new[i]) for i in sorted(set(new) - set(old), key=str)],
        aircraft_removed=[describe(old[i]) for i in sorted(set(old) - set(new), key=str)],
        aircraft_changed=changed,
        mission_settings_changed=settings,
        text_changed=sorted(str(k) for k in set(od) | set(nd) if od.get(k) != nd.get(k)),
        resources_changed=[m for m in members if m not in ('mission', 'l10n/DEFAULT/dictionary')
                           and old_entries.get(m) != new_entries.get(m)],
        note='Review only: this does not certify script safety or collision clearance.')


class Registry:
    def __init__(self, home):
        self.root = Path(home) / 'lineages'
        self.provenance = Path(home) / 'take-provenance'

    # Lineages and revisions -------------------------------------------------

    def lineages(self):
        result = []
        for path in sorted(self.root.glob('*/lineage.json')):
            item = load(path)
            item['revisions'] = self.revisions(item['id'])
            result.append(item)
        return sorted(result, key=lambda l: l['created'])

    def lineage(self, lineage_id):
        if not isinstance(lineage_id, str) or not lineage_id.isalnum():
            raise ValueError('Choose an authored mission from the list.')
        path = self.root / lineage_id / 'lineage.json'
        if not path.is_file():
            raise ValueError('That authored mission history is missing.')
        return load(path)

    def revisions(self, lineage_id):
        rows = [load(p) for p in (self.root / lineage_id / 'revisions').glob('*/revision.json')]
        return sorted(rows, key=lambda r: (r['imported_at'], r['sha256']))

    def find_revision(self, sha256):
        hits = [p.parent for p in self.root.glob(f'*/revisions/{sha256}/revision.json')] if len(sha256) == 64 and sha256.isalnum() else []
        if len(hits) > 1:
            raise ValueError('This mission revision belongs to more than one history; refusing to guess.')
        return load(hits[0] / 'revision.json') if hits else None

    def revision_dir(self, revision):
        return self.root / revision['lineage'] / 'revisions' / revision['sha256']

    def snapshot(self, revision):
        path = self.revision_dir(revision) / 'source.miz'
        if a.sha(path.read_bytes()) != revision['sha256']:
            raise ValueError('The saved scene for this revision is damaged.')
        return path

    def mapping(self, revision):
        """association -> decision for this revision; decisions are immutable files."""
        return {p.stem: load(p) for p in (self.revision_dir(revision) / 'mapping').glob('*.json')}

    def associations(self, lineage_id):
        return {p.stem: load(p) for p in (self.root / lineage_id / 'associations').glob('*.json')}

    def _store(self, lineage_id, path, blob, parent):
        mission = a.read_source(path)[2]
        revision = dict(profile=PROFILE, lineage=lineage_id, sha256=a.sha(blob), parent=parent, imported_at=now(),
                        imported_from=Path(path).name, theatre=mission.get('theatre'), aircraft=len(a.aircraft(mission)))
        directory = self.root / lineage_id / 'revisions' / revision['sha256']
        write_once(directory / 'source.miz', blob)
        write_once(directory / 'revision.json', revision)
        return revision

    def _source(self, path, sha256):
        blob = Path(path).read_bytes()
        if a.sha(blob) != sha256:
            raise ValueError('The authored mission changed after inspection. Inspect it again.')
        a.inspect(path)  # refuses generated copies, duplicate IDs/names and executable data
        if self.find_revision(sha256):
            raise ValueError('This exact revision is already saved.')
        return blob

    def create_lineage(self, path, sha256, name):
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 100:
            raise ValueError('Name the authored mission (1–100 characters).')
        blob = self._source(path, sha256)
        lineage_id = uuid.uuid4().hex
        write_once(self.root / lineage_id / 'lineage.json', dict(id=lineage_id, name=name.strip(), created=now(), profile=PROFILE))
        return self._store(lineage_id, path, blob, None)

    def reference_rows(self, lineage_id):
        """association -> (revision, row) from the latest revision where it was present."""
        result = {}
        for revision in self.revisions(lineage_id):
            mission = a.read_source(self.snapshot(revision))[2]
            for association, decision in self.mapping(revision).items():
                if decision['unit_id'] is not None:
                    result[association] = (revision, a.selected_row(mission, decision['unit_id']))
        return result

    def review(self, path, sha256, lineage_id):
        """Changes and candidate aircraft for joining this source to a lineage."""
        self.lineage(lineage_id)
        if a.sha(Path(path).read_bytes()) != sha256:
            raise ValueError('The authored mission changed after inspection. Inspect it again.')
        if self.find_revision(sha256):
            raise ValueError('This exact revision is already saved.')
        _, entries, mission = a.read_source(path)
        a.inspect(path)
        revisions = self.revisions(lineage_id)
        base = revisions[-1]
        base_blob, base_entries, base_mission = a.read_source(self.snapshot(base))
        if mission.get('theatre') != base_mission.get('theatre'):
            raise ValueError('The terrain differs from this authored mission. Start a new authored mission instead.')
        rows = a.aircraft(mission)
        known = self.associations(lineage_id)
        aircraft = []
        for association, (revision, old) in sorted(self.reference_rows(lineage_id).items()):
            candidates = []
            for row in rows:
                if row['unit'].get('type') != old['unit'].get('type'):
                    continue
                diff = a.compatibility(old, row)
                hint = [h for h, same in (('same unit ID', row['unit'].get('unitId') == old['unit'].get('unitId')),
                                          ('same name', row['unit'].get('name') == old['unit'].get('name'))) if same]
                candidates.append(dict(**describe(row), compatible=not diff, differences=diff[:12], hints=hint))
            # Hints only propose; they never decide. A unique compatible hinted
            # candidate is preselected for the user to confirm.
            hinted = [c for c in candidates if c['hints'] and c['compatible']]
            aircraft.append(dict(association=association, recorded_as=describe(old), reference_revision=revision['sha256'],
                                 created=known[association]['created'], candidates=candidates,
                                 proposed=hinted[0]['id'] if len(hinted) == 1 else None))
        return dict(lineage=lineage_id, base=base['sha256'], sha256=sha256, aircraft=aircraft,
                    changes=scene_changes(base_entries, base_mission, entries, mission))

    def join(self, path, sha256, lineage_id, decisions):
        """Save a changed revision with one explicit decision per known association."""
        review = self.review(path, sha256, lineage_id)
        if not isinstance(decisions, dict):
            raise ValueError('Confirm each recorded aircraft.')
        expected = {item['association'] for item in review['aircraft']}
        if set(decisions) != expected:
            raise ValueError('Confirm every recorded aircraft, or mark it as not in this revision.')
        chosen = {}
        for item in review['aircraft']:
            unit = decisions[item['association']]
            if unit is None:
                continue
            match = [c for c in item['candidates'] if c['id'] == unit]
            if len(match) != 1:
                raise ValueError(f"{item['recorded_as']['name']}: the chosen aircraft is missing or ambiguous.")
            if not match[0]['compatible']:
                raise ValueError(f"{item['recorded_as']['name']}: the chosen aircraft's authored start or configuration "
                                 'changed (' + ', '.join(match[0]['differences'][:4]) + '). Restore it in Mission Editor or use the saved scene.')
            if unit in chosen.values():
                raise ValueError('One aircraft cannot stand for two recorded aircraft.')
            chosen[item['association']] = unit
        blob = self._source(path, sha256)
        revision = self._store(lineage_id, path, blob, review['base'])
        mission = a.read_source(self.snapshot(revision))[2]
        for association, unit in decisions.items():
            row = a.selected_row(mission, unit) if unit is not None else None
            write_once(self.revision_dir(revision) / 'mapping' / f'{association}.json',
                       dict(association=association, unit_id=unit, unit_name=row['unit']['name'] if row else None,
                            decision='confirmed' if row else 'absent', decided_at=now()))
        return revision

    def association_for(self, revision, unit_id):
        """The association for a recording aircraft; new aircraft get a new one."""
        mission = a.read_source(self.snapshot(revision))[2]
        row = a.selected_row(mission, unit_id)
        for association, decision in self.mapping(revision).items():
            if decision['unit_id'] == unit_id:
                return association
        association = uuid.uuid4().hex
        write_once(self.root / revision['lineage'] / 'associations' / f'{association}.json',
                   dict(id=association, lineage=revision['lineage'], created=now(), created_revision=revision['sha256'],
                        created_unit_id=unit_id, created_name=row['unit']['name']))
        write_once(self.revision_dir(revision) / 'mapping' / f'{association}.json',
                   dict(association=association, unit_id=unit_id, unit_name=row['unit']['name'], decision='created', decided_at=now()))
        return association

    # Takes -------------------------------------------------------------------

    def bind_take(self, take, metadata, packages):
        """Persist a take's provenance once. None means no association was recorded."""
        association, lineage_id = metadata.get('authored_association'), metadata.get('authored_lineage')
        if not association:
            return None
        take = Path(take)
        record_path = self.provenance / (take.name + '.json')
        digest = a.sha(take.read_bytes())
        if record_path.exists():
            record = load(record_path)
            if record['take_sha256'] != digest:
                raise ValueError('This recording changed after it was saved; its provenance no longer matches.')
            return record
        revision = self.find_revision(metadata.get('authored_source_sha256', ''))
        if not revision or revision['lineage'] != lineage_id:
            raise ValueError('The saved scene for this take is missing from the companion history.')
        decision = self.mapping(revision).get(association)
        if not decision or str(decision['unit_id']) != metadata.get('source_unit_id'):
            raise ValueError('The recorded aircraft does not match its saved association.')
        prepared = {m['prepared_sha256']: (generation, m) for generation, m in packages
                    if m.get('source_sha256') == revision['sha256'] and m.get('association') == association}
        if len(prepared) != 1:
            raise ValueError('The recording copy for this take is missing or ambiguous.')
        (prepared_sha, (generation, manifest)), = prepared.items()
        from formations import flown_against
        record = dict(profile=PROFILE, take=take.name, take_sha256=digest, lineage=lineage_id, association=association,
                      source_sha256=revision['sha256'], prepared_sha256=prepared_sha, recording_package=generation,
                      unit_id=decision['unit_id'], unit_name=decision['unit_name'], bound_at=now())
        against = flown_against(metadata, manifest)  # refuses a take whose package does not match
        if against is not None:
            record['flown_against'] = against
        try:
            write_once(record_path, record)
        except FileExistsError:
            return self.bind_take(take, metadata, packages)
        return record

    def scenes(self, record):
        """Scenes a take can play in: its saved scene first, then confirmed revisions."""
        original = self.find_revision(record['source_sha256'])
        result = []
        for revision in self.revisions(record['lineage']):
            decision = self.mapping(revision).get(record['association'])
            if not decision or decision['unit_id'] is None:
                continue
            result.append(dict(sha256=revision['sha256'], saved=revision['sha256'] == original['sha256'],
                               label=revision['imported_from'] + ' · ' + revision['imported_at'][:16].replace('T', ' ') + ' UTC',
                               lead_id=decision['unit_id'], lead_name=decision['unit_name'], revision=revision))
        result.sort(key=lambda s: not s['saved'])
        return result
