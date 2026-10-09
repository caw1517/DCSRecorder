"""Formations and their write-once versions, stored under their authored mission.

A formation belongs to one authored mission (lineage) and names, per aircraft
association, the take that plays there. Versions are numbered in creation order,
are never rewritten, and each names its base version. Takes are referenced by
filename and sha256, never owned. Flown-against flags are not stored: they are
derived per pair from each take's flown-against record (see `flown_against`).

Layout, beside mission_lineage.Registry:
  lineages/<lineage>/formations/<formation>/formation.json   id, created, solo take
  lineages/<lineage>/formations/<formation>/name.json        replaceable name
  lineages/<lineage>/formations/<formation>/versions/<n>.json
"""
from __future__ import annotations
import json, os, re, tempfile, uuid
from mission_lineage import load, now, write_once

FORMATION_PROFILE = 'formation-v1'
EVENT = re.compile(r'^(not_ready|failed|ended):([0-9a-f]{32})(?:@([0-9]+(?:\.[0-9]+)?))?$')


def clean_name(name):
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 100 or any(ord(c) < 32 for c in name):
        raise ValueError('Name the formation (1–100 characters).')
    return name.strip()


def events(text):
    """Recorder events: 'kind:<association>[@<replay time>]' joined by ';'."""
    result = []
    for item in filter(None, (text or '').split(';')):
        match = EVENT.match(item)
        if not match or (match[1] == 'not_ready') != (match[3] is None):
            raise ValueError('The take\'s formation events are damaged.')
        result.append(dict(kind=match[1], association=match[2], t=None if match[3] is None else float(match[3])))
    return result


def flown_against(metadata, manifest):
    """Join the recorder's half (epoch, events) with the prepared package's half
    (formation, version, takes played, muted). None for a take not recorded
    against a formation; refuses a take whose package does not match."""
    plan = manifest.get('formation') if manifest else None
    recorded = {k: metadata.get(k) for k in ('formation_id', 'formation_version', 'formation_epoch')}
    if plan is None:
        if any(v is not None for v in recorded.values()):
            raise ValueError('This take says it was flown against a formation, but its recording copy has none.')
        return None
    if recorded['formation_id'] != plan['formation'] or recorded['formation_version'] != str(plan['version']):
        raise ValueError('This take was recorded against a different formation version than its recording copy.')
    try:
        epoch = float(recorded['formation_epoch'])
    except (TypeError, ValueError):
        raise ValueError('This formation take has no shared epoch.') from None
    played = plan['played']
    happened = events(metadata.get('formation_events'))
    if any(e['association'] not in played for e in happened):
        raise ValueError('The take names an aircraft that did not play in its recording copy.')
    not_ready = sorted({e['association'] for e in happened if e['kind'] == 'not_ready'})
    return dict(formation=plan['formation'], version=plan['version'], position=manifest['association'], epoch=epoch,
                played={k: v for k, v in played.items() if k not in not_ready}, muted=sorted(plan['muted']),
                not_ready=not_ready, events=[e for e in happened if e['kind'] != 'not_ready'])


class Formations:
    def __init__(self, registry):
        self.registry = registry

    def _dir(self, lineage_id, formation_id=None):
        self.registry.lineage(lineage_id)
        base = self.registry.root / lineage_id / 'formations'
        if formation_id is None:
            return base
        if not isinstance(formation_id, str) or not formation_id.isalnum() or not (base / formation_id / 'formation.json').is_file():
            raise ValueError('That formation is missing; refresh the library.')
        return base / formation_id

    # Reading -----------------------------------------------------------------

    def formation(self, lineage_id, formation_id):
        directory = self._dir(lineage_id, formation_id)
        item = load(directory / 'formation.json')
        item['name'] = load(directory / 'name.json')['name']
        item['versions'] = self.versions(lineage_id, formation_id)
        return item

    def formations(self, lineage_id):
        base = self._dir(lineage_id)
        rows = [self.formation(lineage_id, p.parent.name) for p in base.glob('*/formation.json')]
        return sorted(rows, key=lambda f: f['created'])

    def versions(self, lineage_id, formation_id):
        directory = self._dir(lineage_id, formation_id) / 'versions'
        return sorted((load(p) for p in directory.glob('*.json')), key=lambda v: v['number'])

    def version(self, lineage_id, formation_id, number=None):
        versions = self.versions(lineage_id, formation_id)
        if number is None:
            return versions[-1]  # Play and Record default to the latest
        match = [v for v in versions if v['number'] == number]
        if not match:
            raise ValueError('That formation version is missing.')
        return match[0]

    def memberships(self, lineage_id):
        """take filename -> ['Diamond v2', ...] for the takes-list badge."""
        result = {}
        for formation in self.formations(lineage_id):
            for version in formation['versions']:
                for position in version['positions'].values():
                    result.setdefault(position['take'], []).append(f"{formation['name']} v{version['number']}")
        return result

    # Writing -----------------------------------------------------------------

    def start(self, record, name):
        """Start a formation from a solo take with an aircraft association: version 1."""
        if not record or not record.get('association'):
            raise ValueError('This take was recorded before aircraft associations, so it cannot start a formation. '
                             'Record it again from a saved mission revision.')
        name = clean_name(name)
        formation_id = uuid.uuid4().hex
        directory = self._dir(record['lineage']) / formation_id
        write_once(directory / 'formation.json', dict(id=formation_id, lineage=record['lineage'], created=now(),
                                                      started_from=dict(take=record['take'], sha256=record['take_sha256']),
                                                      profile=FORMATION_PROFILE))
        write_once(directory / 'name.json', dict(name=name))
        positions = {record['association']: dict(take=record['take'], sha256=record['take_sha256'])}
        return self._write_version(record['lineage'], formation_id, None, record, positions)

    def rename(self, lineage_id, formation_id, name):
        directory = self._dir(lineage_id, formation_id)
        data = (json.dumps(dict(name=clean_name(name)), indent=2) + '\n').encode('utf-8')
        handle, temporary = tempfile.mkstemp(dir=directory, suffix='.tmp')
        with os.fdopen(handle, 'wb') as stream:
            stream.write(data)
        os.replace(temporary, directory / 'name.json')  # the name is the one replaceable record

    def offer(self, record):
        """The version a formation take would create: its base with its position set
        to this take. Muted and not-ready positions keep their existing takes."""
        against = record.get('flown_against') if record else None
        if not against:
            raise ValueError('This take was not recorded against a formation.')
        base = self.version(record['lineage'], against['formation'], against['version'])
        if record['association'] != against['position']:
            raise ValueError('This take was flown from a different aircraft than its recording copy chose.')
        positions = dict(base['positions'])
        positions[record['association']] = dict(take=record['take'], sha256=record['take_sha256'])
        return base, positions

    def make_version(self, record):
        """Accept an offer now or later ('Make version from this take')."""
        base, positions = self.offer(record)
        formation_id = record['flown_against']['formation']
        for existing in self.versions(record['lineage'], formation_id):
            if existing['created_by'] == dict(take=record['take'], sha256=record['take_sha256']):
                raise ValueError(f"This take already made version {existing['number']}.")
        return self._write_version(record['lineage'], formation_id, base['number'], record, positions)

    def _write_version(self, lineage_id, formation_id, base, record, positions):
        directory = self._dir(lineage_id, formation_id) / 'versions'
        while True:  # numbered in creation order; a concurrent writer takes the next number
            number = len(list(directory.glob('*.json'))) + 1
            version = dict(number=number, base=base, created=now(), positions=positions,
                           created_by=dict(take=record['take'], sha256=record['take_sha256']))
            try:
                write_once(directory / f'{number}.json', version)
                return version
            except FileExistsError:
                continue

    # Derived views -------------------------------------------------------------

    def flags(self, version, records):
        """Per position, per other position: played, or why not. `records` maps take
        filename -> its take-provenance record. Nothing here is stored."""
        result = {}
        for association, position in version['positions'].items():
            own = records.get(position['take'])
            if not own or own['take_sha256'] != position['sha256']:
                raise ValueError('A take in this formation changed or is missing; refusing to show its flags.')
            against = own.get('flown_against') or {}
            failed = {e['association']: e['t'] for e in against.get('events', []) if e['kind'] == 'failed'}
            pairs = {}
            for other, take in version['positions'].items():
                if other == association:
                    continue
                if against.get('played', {}).get(other) == take:
                    pairs[other] = dict(state='flown_against_until', t=failed[other]) if other in failed else dict(state='flown_against')
                else:
                    reason = 'muted' if other in against.get('muted', []) else 'not_ready' if other in against.get('not_ready', []) else 'recorded_later'
                    pairs[other] = dict(state='not_flown_against', reason=reason)
            result[association] = pairs
        return result

    def scenes(self, lineage_id, version):
        """Revisions where every position's association is confirmed, newest first.
        Positions are never dropped: a revision missing one is named, not offered."""
        playable, missing = [], []
        for revision in reversed(self.registry.revisions(lineage_id)):
            mapping = self.registry.mapping(revision)
            absent = [a for a in version['positions'] if not mapping.get(a) or mapping[a]['unit_id'] is None]
            if absent:
                missing.append(dict(sha256=revision['sha256'], label=revision['imported_from'], missing=absent))
            else:
                playable.append(dict(sha256=revision['sha256'], label=revision['imported_from'], revision=revision,
                                     units={a: mapping[a]['unit_id'] for a in version['positions']}))
        return playable, missing
