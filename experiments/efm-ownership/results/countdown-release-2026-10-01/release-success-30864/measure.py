"""Measure the retained normal release run; does not establish pause acceptance."""
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
import shutil

run = Path(__file__).resolve().parent
raw = run / 'raw'
package = run.parent / 'gear-package-v5'
manifest = json.loads((package / 'manifest.json').read_text(encoding='utf-8-sig'))
installed = Path('C:/Users/w_can/Saved Games/DCS')
hashes = {}
for name, expected in manifest['files'].items():
    data = (installed / name).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    assert digest == expected, name
    target = raw / 'installed' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    hashes[name] = digest
shutil.copy2(package / 'manifest.json', raw / 'manifest.json')
tape_path = next((raw / 'installed').rglob('recorded-flight.txt'))
first = list(map(float, tape_path.read_text().splitlines()[7].split()))
assert len(first) == 50

def read(pattern):
    paths = list(raw.glob(pattern))
    assert len(paths) == 1
    with paths[0].open(newline='') as f:
        return list(csv.DictReader(f))

lines = (raw / 'dcs.log').read_text(encoding='utf-8', errors='replace').splitlines()
events = [s.split('DCSR_RELEASE ', 1)[1].split(',') for s in lines
          if 'SCRIPTING (Main): DCSR_RELEASE ' in s]
counts = Counter(r[0] for r in events)
assert counts['COMPLETE'] == counts['COUNTDOWN'] == counts['REQUEST'] == counts['PLAYER_RELEASED'] == 1
assert not counts['FAILED']
event = {r[0]: r for r in events if r[0] != 'SAMPLE'}
objects = read('objects-*.csv')
native_counts = Counter(r['event'] for r in objects)
assert native_counts['release_epoch'] == native_counts['release_committed'] == 1
epoch = float(next(r['object_time'] for r in objects if r['event'] == 'release_epoch'))
samples = [r for r in events if r[0] == 'SAMPLE']
assert all(len(r) == 51 for r in samples)
held = [r for r in samples if r[1] in ('waiting', 'countdown')]
report = {'scope': 'Normal live airborne countdown/release; pause and repeated-request runs remain pending',
          'pid': 30864, 'installed_hashes': hashes, 'mission_event_counts': dict(counts),
          'native_event_counts': dict(native_counts),
          'countdown_model_seconds': float(event['REQUEST'][3]) - float(event['COUNTDOWN'][1]),
          'request_to_player_release_seconds': float(event['PLAYER_RELEASED'][3]) - float(event['REQUEST'][3]),
          'native_epoch': epoch,
          'player_to_native_epoch_seconds': epoch - float(event['PLAYER_RELEASED'][3]),
          'held': {}}
assert abs(report['countdown_model_seconds'] - 3) < 1e-9
for name in ('Observer', 'StagedPlayback'):
    rows = [r for r in held if r[2] == name]
    positions = [list(map(float, r[4:7])) for r in rows]
    drift = max(math.dist(p, positions[0]) for p in positions)
    report['held'][name] = {'samples': len(rows), 'position_drift_m': drift,
                          'replay_values': sorted({float(r[16]) for r in rows})}
    assert drift == 0
    if name == 'StagedPlayback':
        assert report['held'][name]['replay_values'] == [0]
motion = [r for r in read('native-motion-*.csv') if r['status'] == 'called']
released = next(r for r in motion if abs(float(r['object_time']) - epoch) < 1e-9)
velocity = [float(released[f'velocity_command{i}']) for i in range(3)]
held_motion = [r for r in motion if float(r['object_time']) < epoch]
assert all(float(r[f'velocity_command{i}']) == 0 for r in held_motion for i in range(3))
report['motion'] = {'writes': len(motion), 'held_writes': len(held_motion),
                    'all_motion_matched': all(r['motion_matched'] == '1' for r in motion),
                    'initial_velocity_command_mps': velocity,
                    'initial_velocity_source_error_mps': math.dist(velocity, first[8:11]),
                    'initial_position_source_error_m': math.dist(
                        [float(released[f'command{i}']) for i in range(12, 15)], first[1:4])}
assert report['motion']['all_motion_matched']
assert report['motion']['initial_velocity_source_error_mps'] < 1e-8
assert report['motion']['initial_position_source_error_m'] < 1e-8
exterior = read('exterior-*.csv')
engine = [r for r in read('engine-*.csv') if r['engine'] in ('1', '2')]
report['state'] = {'exterior_rows': len(exterior),
                   'exterior_max_write_readback_error': max(abs(float(r['requested']) - float(r['after'])) for r in exterior),
                   'engine_overrides': len(engine),
                   'all_engine_reads_overridden': all(r['overridden'] == '1' for r in engine),
                   'exterior_replay_range': [min(float(r['elapsed']) for r in exterior), max(float(r['elapsed']) for r in exterior)],
                   'engine_replay_range': [min(float(r['elapsed']) for r in engine), max(float(r['elapsed']) for r in engine)]}
report['user_review'] = {'normal_run': 'Okay, it seems to work great.',
                         'visible_smoke_at_release': 'Yes, smoke was visible at release'}
(run / 'analysis.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k not in ('installed_hashes', 'native_event_counts')}, indent=2))
