"""THROWAWAY: inspect .miz round trips as data, never execute mission Lua.

snapshot BEFORE.miz [AFTER.miz] --output report.json
seed INPUT.miz OUTPUT.miz  (four-aircraft scratch fixture, never overwrites)
repack INPUT.miz OUTPUT.miz  (ZIP-only control, not a Mission Editor save)
"""
import argparse
import copy
import hashlib
import json
import re
import zipfile
from pathlib import Path


class LuaData:
    """Bounded data-only subset used by serialized DCS mission tables."""
    def __init__(self, text):
        self.text, self.pos = text, 0

    def skip(self):
        while True:
            m = re.match(r'\s+|--\[(=*)\[', self.text[self.pos:])
            if m:
                self.pos += m.end()
                if m.group(1) is not None:
                    end = self.text.index(']' + m.group(1) + ']', self.pos)
                    self.pos = end + len(m.group(1)) + 2
            elif self.text.startswith('--', self.pos):
                end = self.text.find('\n', self.pos)
                self.pos = len(self.text) if end < 0 else end + 1
            else:
                return

    def take(self, token):
        self.skip()
        if not self.text.startswith(token, self.pos):
            raise ValueError(f'Expected {token!r} at {self.pos}; unsupported Lua data')
        self.pos += len(token)

    def value(self, depth=0):
        if depth > 100:
            raise ValueError('Table nesting too deep')
        self.skip()
        c = self.text[self.pos:self.pos + 1]
        if c == '{':
            self.pos += 1
            result, index = {}, 1
            while True:
                self.skip()
                if self.text.startswith('}', self.pos):
                    self.pos += 1
                    return result
                if self.text.startswith('[', self.pos) and not re.match(r'\[(=*)\[', self.text[self.pos:]):
                    self.pos += 1
                    key = self.value(depth + 1)
                    self.take(']')
                    self.take('=')
                else:
                    m = re.match(r'([A-Za-z_]\w*)\s*=', self.text[self.pos:])
                    if m:
                        key = m.group(1)
                        self.pos += m.end()
                    else:
                        key, index = index, index + 1
                if key in result:
                    raise ValueError('Duplicate table key')
                result[key] = self.value(depth + 1)
                self.skip()
                if self.text[self.pos:self.pos + 1] in (',', ';'):
                    self.pos += 1
        if c in ('"', "'"):
            self.pos += 1
            out = []
            while self.pos < len(self.text):
                ch = self.text[self.pos]
                self.pos += 1
                if ch == c:
                    return ''.join(out)
                if ch != '\\':
                    out.append(ch)
                    continue
                ch = self.text[self.pos]
                self.pos += 1
                if ch.isdigit():
                    digits = ch
                    while len(digits) < 3 and self.text[self.pos:self.pos + 1].isdigit():
                        digits += self.text[self.pos]
                        self.pos += 1
                    out.append(chr(int(digits)))
                elif ch in 'abfnrtv':
                    out.append(dict(zip('abfnrtv', '\a\b\f\n\r\t\v'))[ch])
                elif ch in ('\\', '"', "'", '\n'):
                    out.append(ch)
                elif ch == '\r':
                    if self.text[self.pos:self.pos + 1] == '\n':
                        self.pos += 1
                    out.append('\n')
                else:
                    raise ValueError(f'Unsupported escape {ch!r}')
            raise ValueError('Unterminated string')
        m = re.match(r'\[(=*)\[', self.text[self.pos:])
        if m:
            self.pos += m.end()
            end_token = ']' + m.group(1) + ']'
            end = self.text.index(end_token, self.pos)
            value = self.text[self.pos:end]
            self.pos = end + len(end_token)
            return value[1:] if value.startswith('\n') else value
        m = re.match(r'-?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?|true\b|false\b|nil\b', self.text[self.pos:])
        if not m:
            raise ValueError(f'Executable or unsupported Lua at {self.pos}')
        self.pos += m.end()
        token = m.group()
        if token in ('true', 'false', 'nil'):
            return {'true': True, 'false': False, 'nil': None}[token]
        number = float(token)
        if not float('-inf') < number < float('inf'):
            raise ValueError('Nonfinite number')
        return int(number) if number.is_integer() else number

    def mission(self):
        self.take('mission')
        self.take('=')
        result = self.value()
        self.skip()
        if self.pos != len(self.text):
            raise ValueError('Trailing executable or unsupported Lua')
        return result


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    # Preserve numeric/string key types and sequence indices. Sorting aircraft
    # inventories below is a comparison aid, never evidence of persistent identity.
    if isinstance(value, dict):
        return ['table', sorted([[canonical(k), canonical(v)] for k, v in value.items()], key=lambda p: json.dumps(p[0]))]
    return value


def structural_sha(value):
    return sha(json.dumps(canonical(value), ensure_ascii=False, separators=(',', ':')).encode())


def read(path):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or sum(i.file_size for i in archive.infolist()) > 100_000_000:
            raise ValueError('Duplicate entries or oversized fixture')
        entries = {n: archive.read(n) for n in names}
    return entries, LuaData(entries['mission'].decode('utf-8-sig')).mission()


def aircraft(mission):
    result = []
    for side, coalition in mission.get('coalition', {}).items():
        if not isinstance(coalition, dict):
            continue
        for country in coalition.get('country', {}).values():
            for category in ('plane', 'helicopter'):
                for group in country.get(category, {}).get('group', {}).values():
                    for unit in group.get('units', {}).values():
                        result.append(dict(side=side, country=country.get('id'), category=category,
                                           group_id=group.get('groupId'), group_name=group.get('name'),
                                           unit=unit, route=group.get('route'),
                                           group_settings={k: v for k, v in group.items() if k not in ('units', 'route')}))
    return sorted(result, key=lambda r: (str(r['unit'].get('unitId')), str(r['unit'].get('name'))))


def snapshot(path):
    entries, mission = read(path)
    rows = aircraft(mission)
    return dict(path=str(path), archive_sha256=sha(Path(path).read_bytes()),
                entries_sha256={n: sha(b) for n, b in sorted(entries.items())},
                mission_table_sha256=structural_sha(mission),
                aircraft_inventory_sha256=structural_sha(rows),
                theatre=mission.get('theatre'), weather=mission.get('weather'),
                top_level_keys=sorted(mission), aircraft=rows,
                identity_conclusion='Inventory only. Equality of IDs/names/configuration does not prove continuity.')


def serialize(value):
    if isinstance(value, dict):
        return '{\n' + ''.join(f'[{serialize(k)}]={serialize(v)},\n' for k, v in value.items()) + '}'
    if isinstance(value, str):
        return '"' + ''.join('\\%03d' % ord(c) if ord(c) < 32 else '\\' + c if c in '\\"' else c for c in value) + '"'
    if value is None:
        return 'nil'
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def seed(source, target):
    entries, mission = read(source)
    countries = mission['coalition']['blue']['country']
    country = next(c for c in countries.values() if c.get('plane', {}).get('group'))
    original = copy.deepcopy(next(iter(country['plane']['group'].values())))
    used = [r['unit'].get('unitId', 0) for r in aircraft(mission)]
    # Scratch-only IDs chosen above every numeric unit/group ID in the mission.
    def all_ids(v):
        if isinstance(v, dict):
            for k, x in v.items():
                if k in ('unitId', 'groupId') and isinstance(x, int):
                    yield x
                yield from all_ids(x)
    offset = max([10000, *used, *all_ids(mission)]) + 100
    groups = {}
    for i in range(1, 5):
        group = copy.deepcopy(original)
        unit = copy.deepcopy(next(iter(group['units'].values())))
        group.update(groupId=offset + i, name=f'Identity Probe Group {i}', lateActivation=False)
        unit.update(unitId=offset + 10 + i, name=f'Identity Probe Aircraft {i}',
                    type='FA-18C_hornet', skill='Player' if i == 1 else 'High')
        unit['x'] += (i - 1) * 300
        group['x'], group['y'] = unit['x'], unit['y']
        group['units'] = {1: unit}
        for point in group.get('route', {}).get('points', {}).values():
            point['x'] += (i - 1) * 300
        unit['dcsrecorder_probe_uuid'] = f'PROTOTYPE-AIRCRAFT-{i}'
        groups[i] = group
    country['plane']['group'] = groups
    mission['dcsrecorder_probe_lineage'] = 'PROTOTYPE-LINEAGE'
    mission['trigrules'] = {}
    mission['trig'] = {k: {} for k in ('actions', 'conditions', 'func', 'funcStartup', 'flag')}
    mission['descriptionText'] = 'THROWAWAY identity probe. Four stock Hornets. Save copies only; do not fly.'
    entries['mission'] = ('mission = ' + serialize(mission)).encode()
    entries['dcsrecorder-probe.json'] = b'{"purpose":"unknown archive member survival probe"}'
    entries['DCSRecorderProbe/identity.json'] = b'{"purpose":"nested archive member survival probe","lineage":"PROTOTYPE-LINEAGE"}'
    with zipfile.ZipFile(target, 'x', zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)
    return snapshot(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('snapshot', 'seed', 'repack'))
    parser.add_argument('paths', nargs='+', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.command == 'seed':
        report = seed(*args.paths)
    elif args.command == 'repack':
        source, target = args.paths
        entries, _ = read(source)
        with zipfile.ZipFile(target, 'x', zipfile.ZIP_STORED) as archive:
            for name, data in reversed(list(entries.items())):
                archive.writestr(name, data)
        report = {'observation': 'ZIP-only control; NOT a Mission Editor save',
                  'before': snapshot(source), 'after': snapshot(target)}
    else:
        report = {'snapshots': [snapshot(p) for p in args.paths]}
    if args.output:
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        print(args.output)
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
