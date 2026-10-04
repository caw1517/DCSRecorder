"""Check that every ResKey_/DictKey_ a mission references resolves in DCS.

Mirrors Scripts/dictionary.lua getValueResource: a key resolves in the locale's
mapResource, else DEFAULT; the resolved l10n/<locale>/<file> must be an archive
member. Dictionary keys follow the same locale-then-DEFAULT rule.
Usage: python check_resources.py <mission.miz>
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]/'companion'))
import authored_missions as a


def problems(blob):
    entries = a.zip_entries(blob)
    mission = a.LuaData(entries['mission'].decode('utf-8-sig')).mission()
    tables = {}
    for name, data in entries.items():
        parts = name.split('/')
        if len(parts) == 3 and parts[0] == 'l10n' and parts[2] in ('mapResource', 'dictionary'):
            table = a.LuaData(data.decode('utf-8-sig')).assignment(parts[2])
            tables.setdefault(parts[2], {})[parts[1]] = table
    refs = sorted({s for s in a.strings(mission) if s.startswith(('ResKey_', 'DictKey_'))})
    locales = sorted(set(tables.get('mapResource', {})) | set(tables.get('dictionary', {})) | {'DEFAULT'})
    found = []
    for ref in refs:
        kind = 'mapResource' if ref.startswith('ResKey_') else 'dictionary'
        for locale in locales:
            source = next((l for l in (locale, 'DEFAULT') if ref in tables.get(kind, {}).get(l, {})), None)
            if source is None:
                found.append(f'{ref} does not resolve for locale {locale}')
            elif kind == 'mapResource' and f'l10n/{source}/{tables[kind][source][ref]}' not in entries:
                found.append(f'{ref} -> missing archive member l10n/{source}/{tables[kind][source][ref]}')
    return refs, found


if __name__ == '__main__':
    refs, found = problems(Path(sys.argv[1]).read_bytes())
    for line in found:
        print('FAIL ' + line)
    if found:
        sys.exit(1)
    print(f'PASS {len(refs)} resource/dictionary reference(s) resolve for every locale')
