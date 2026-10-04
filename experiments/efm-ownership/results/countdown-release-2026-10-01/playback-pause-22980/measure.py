"""Measure the deliberate live playback pause from retained mission/native logs."""
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
epoch = float(single['NATIVE_RUNNING'][1][1])
rows = [(w,r) for w,r in events if r[0] == 'SAMPLE' and r[2] == 'StagedPlayback' and r[1] == 'playing']
gaps = []
for (wa,a),(wb,b) in zip(rows, rows[1:]):
    if wb-wa > 1:
        gaps.append({'wall_seconds': wb-wa, 'model_seconds': float(b[3])-float(a[3]),
                     'replay_before': float(a[16]), 'replay_after': float(b[16]),
                     'replay_advance_seconds': float(b[16])-float(a[16]),
                     'position_advance_m': math.dist(list(map(float,a[4:7])),list(map(float,b[4:7])))})
assert gaps and all(g['model_seconds'] < .1 and g['replay_advance_seconds'] < .1 for g in gaps)
with next(raw.glob('native-motion-*.csv')).open(newline='') as f:
    motion = [r for r in csv.DictReader(f) if r['status'] == 'called']
native_gaps = []
for a,b in zip(motion,motion[1:]):
    wall_delta = float(b['wall_seconds'])-float(a['wall_seconds'])
    if wall_delta > 1 and float(a['object_time']) >= epoch:
        native_gaps.append({'wall_seconds': wall_delta, 'model_seconds': float(b['object_time'])-float(a['object_time']),
                            'replay_before': float(a['object_time'])-epoch, 'replay_after': float(b['object_time'])-epoch,
                            'command_position_advance_m': math.dist([float(a[f'command{i}']) for i in range(12,15)],
                                                                  [float(b[f'command{i}']) for i in range(12,15)])})
assert native_gaps and all(g['model_seconds'] < .1 for g in native_gaps)
with next(raw.glob('objects-*.csv')).open(newline='') as f:
    objects = list(csv.DictReader(f))
complete = [r for r in objects if r['event'] == 'staged_exterior_complete']
assert len(complete) == 1
duration = float(complete[0]['object_time'])-epoch
assert abs(duration-8.7) < 1e-8
report = {'scope': 'Deliberate live regular simulator pause during playback', 'pid':22980,
          'user_review': 'Looked good', 'installed_hashes': hashes, 'mission_event_counts':dict(counts),
          'playback_wall_seconds': single['COMPLETE'][0]-single['NATIVE_RUNNING'][0],
          'native_playback_seconds':duration, 'mission_pause_gaps':gaps, 'native_pause_gaps':native_gaps,
          'all_native_motion_matched':all(r['motion_matched']=='1' for r in motion)}
assert report['all_native_motion_matched']
(run / 'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k != 'installed_hashes'},indent=2))
