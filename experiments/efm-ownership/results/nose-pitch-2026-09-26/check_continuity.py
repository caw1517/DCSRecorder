"""Read-only trace measurement; not a regression test for the visual symptom."""
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = Path(r'C:\Users\w_can\Saved Games\DCS\DCSRecorder\recordings\20260926T224052Z-0001.csv')

def angle(a, b):
    dot = sum(x*y for x, y in zip(a, b))
    norm = math.sqrt(sum(x*x for x in a)*sum(x*x for x in b))
    return math.degrees(math.acos(max(-1, min(1, dot/norm))))

def summarize(points):
    steps = []
    for a, b in zip(points, points[1:]):
        dt = b[0]-a[0]
        if dt <= 0:
            continue
        steps.append({'time': b[0], 'dt': dt, 'forward_step_deg': angle(a[1], b[1]),
                      'up_step_deg': angle(a[2], b[2])})
    return {'samples': len(points), 'max_dt': max(p['dt'] for p in steps),
            'largest_forward_steps': sorted(steps, key=lambda p:p['forward_step_deg'], reverse=True)[:3],
            'largest_up_steps': sorted(steps, key=lambda p:p['up_step_deg'], reverse=True)[:3]}

lines = SOURCE.read_text().splitlines()
rows = [r for r in csv.DictReader(lines[next(i for i, s in enumerate(lines) if s.startswith('t,x,')):]) if r['t'] != 'END']
source = [(float(r['t'])-float(rows[0]['t']), [float(r[k]) for k in ('fx','fy','fz')],
           [float(r[k]) for k in ('ux','uy','uz')]) for r in rows]
runs = []
for r in csv.DictReader((ROOT/'native-motion-15596.csv').open()):
    if r['status'] == 'captured':
        runs.append([])
    elif r['status'] == 'called':
        runs[-1].append((float(r['object_time']), [float(r[f'command{i}']) for i in (0,1,2)],
                        [float(r[f'command{i}']) for i in (4,5,6)]))
mission_runs = []
for line in (ROOT/'dcs.log').read_text(errors='replace').splitlines():
    if 'DCS_PLAYBACK_SAMPLE,playing,StagedPlayback,' not in line:
        continue
    values = line.split('DCS_PLAYBACK_SAMPLE,',1)[1].split(',')
    t = float(values[2])
    if not mission_runs or t <= mission_runs[-1][-1][0]:
        mission_runs.append([])
    mission_runs[-1].append((t, list(map(float, values[6:9])), list(map(float, values[9:12]))))
report = {'source': summarize(source), 'native_commands': [summarize(r) for r in runs],
          'mission_samples': [summarize(r) for r in mission_runs]}
comparisons = []
for commands, samples in zip(runs, mission_runs):
    lookup = {round(p[0], 2): p for p in commands}
    differences = []
    for sample in samples:
        command = lookup.get(round(sample[0], 2))
        if command:
            differences.append({'mission_time': sample[0], 'elapsed': sample[0]-commands[0][0],
                                'forward_error_deg': angle(sample[1], command[1]),
                                'up_error_deg': angle(sample[2], command[2])})
    comparisons.append({'largest_forward_errors': sorted(differences, key=lambda p:p['forward_error_deg'],reverse=True)[:5],
                        'largest_up_errors': sorted(differences, key=lambda p:p['up_error_deg'],reverse=True)[:5]})
(ROOT/'continuity.json').write_text(json.dumps(report, indent=2))
(ROOT/'mission-vs-native.json').write_text(json.dumps(comparisons, indent=2))
for name, results in report.items():
    for i, result in enumerate(results if isinstance(results,list) else [results],1):
        print(name, i, 'samples',result['samples'], 'max_dt',round(result['max_dt'],6),
              'max_forward_step_deg',round(result['largest_forward_steps'][0]['forward_step_deg'],6),
              'max_up_step_deg',round(result['largest_up_steps'][0]['up_step_deg'],6))
