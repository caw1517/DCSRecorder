"""Measure retained simulator-time progression across the live countdown pause."""
import csv
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
from collections import Counter

run = Path(__file__).resolve().parent
raw = run / 'raw'
manifest_path = run.parent / 'gear-package-v5/manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
hashes = {}
for name, expected in manifest['files'].items():
    data = (Path('C:/Users/w_can/Saved Games/DCS') / name).read_bytes()
    hashes[name] = hashlib.sha256(data).hexdigest()
    assert hashes[name] == expected, name
(raw / 'manifest.json').write_bytes(manifest_path.read_bytes())
events = []
for line in (raw / 'dcs.log').read_text(encoding='utf-8', errors='replace').splitlines():
    if 'SCRIPTING (Main): DCSR_RELEASE ' in line:
        wall = datetime.strptime(line[:23], '%Y-%m-%d %H:%M:%S.%f').timestamp()
        events.append((wall, line.split('DCSR_RELEASE ', 1)[1].split(',')))
counts = Counter(r[0] for _, r in events)
assert not counts['FAILED']
assert all(counts[n] == 1 for n in ('COUNTDOWN', 'REQUEST', 'PLAYER_RELEASED', 'NATIVE_RUNNING', 'COMPLETE'))
single = {r[0]: (w, r) for w, r in events if r[0] != 'SAMPLE'}
model_span = float(single['REQUEST'][1][3]) - float(single['COUNTDOWN'][1][1])
wall_span = single['REQUEST'][0] - single['COUNTDOWN'][0]
assert abs(model_span - 3) < 1e-9
assert wall_span > model_span + 1
held_report = {}
gaps = []
for name in ('Observer', 'StagedPlayback'):
    rows = [(w, r) for w, r in events if r[0] == 'SAMPLE' and r[2] == name and r[1] in ('waiting', 'countdown')]
    positions = [list(map(float, r[4:7])) for _, r in rows]
    drift = max(math.dist(p, positions[0]) for p in positions)
    assert drift == 0
    held_report[name] = {'samples': len(rows), 'position_drift_m': drift}
    if name == 'StagedPlayback':
        assert {float(r[16]) for _, r in rows} == {0}
        for (wa, a), (wb, b) in zip(rows, rows[1:]):
            if a[1] == b[1] == 'countdown' and wb - wa > .5:
                gaps.append({'wall_seconds': wb-wa, 'model_seconds': float(b[3])-float(a[3]),
                             'replay_before': float(a[16]), 'replay_after': float(b[16])})
assert gaps and all(g['model_seconds'] < .1 for g in gaps)
with next(raw.glob('native-motion-*.csv')).open(newline='') as f:
    motion = [r for r in csv.DictReader(f) if r['status'] == 'called']
native_gaps = []
for a, b in zip(motion, motion[1:]):
    wall_delta = float(b['wall_seconds'])-float(a['wall_seconds'])
    if wall_delta > .5:
        native_gaps.append({'wall_seconds': wall_delta,
                            'object_time_before': float(a['object_time']),
                            'object_time_after': float(b['object_time']),
                            'model_seconds': float(b['object_time'])-float(a['object_time'])})
report = {'scope': 'Live pause during countdown; other adversarial live checks remain open',
          'pid': 19800, 'user_review': 'Worked', 'installed_hashes': hashes,
          'mission_event_counts': dict(counts), 'countdown_model_seconds': model_span,
          'countdown_wall_seconds': wall_span, 'held': held_report,
          'countdown_sample_gaps': gaps, 'native_wall_gaps': native_gaps,
          'player_to_native_epoch_seconds': float(single['NATIVE_RUNNING'][1][1])-float(single['PLAYER_RELEASED'][1][3])}
(run / 'analysis.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k != 'installed_hashes'}, indent=2))
