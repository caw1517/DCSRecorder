"""Compare actual SDK writes with later mission reads from the live actuator test."""
import argparse
import bisect
import csv
import json
import math
import statistics
from pathlib import Path

CHANNELS = [0, 3, 5, *range(9, 19), 21]

def analyze(trace, logfile, run=-1):
    # Mission restarts reuse object IDs and elapsed clocks. Never combine runs.
    native_runs = []
    with trace.open(newline='') as stream:
        for row in csv.DictReader(stream):
            if int(row['call']) == 1 and int(row['arg']) == CHANNELS[0]:
                native_runs.append([])
            assert native_runs, 'Native trace starts mid-run'
            native_runs[-1].append(row)
    mission_runs = []
    for line in logfile.read_text(encoding='utf-8', errors='replace').splitlines():
        if 'DCSSTATE_PLAYBACK,BEGIN,' in line:
            mission_runs.append([])
        if 'DCSSTATE_PLAYBACK,DATA,' in line:
            assert mission_runs, 'Mission trace starts mid-run'
            mission_runs[-1].append(line)
    assert len(native_runs) == len(mission_runs), 'Native/mission run counts differ; provide matching logs'
    index = len(native_runs)-1 if run == -1 else run-1
    assert 0 <= index < len(native_runs), 'Requested run unavailable'
    frames = {}
    immediate = {c: [] for c in CHANNELS}
    retention = {c: [] for c in CHANNELS}
    for row in native_runs[index]:
            c = int(row['arg'])
            t = float(row['elapsed'])
            requested = float(row['requested'])
            immediate[c].append(abs(float(row['after']) - requested))
            if row['previous_requested']:
                retention[c].append(abs(float(row['before']) - float(row['previous_requested'])))
            frames.setdefault(t, {})[c] = requested
    times = sorted(frames)
    assert times and all(set(values) == set(CHANNELS) for values in frames.values()), 'Incomplete native frame'
    observed = {c: [] for c in CHANNELS}
    pitch = {c: {'requested': [], 'observed': []} for c in (15, 16)}
    for line in mission_runs[index]:
        row = next(csv.reader([line.split('DCSSTATE_PLAYBACK,DATA,', 1)[1]]))
        assert len(row) == 3 + len(CHANNELS), 'Malformed mission row'
        elapsed = float(row[1])
        i = bisect.bisect_left(times, elapsed)
        candidates = times[max(0, i-1):i+1]
        sample_time = min(candidates, key=lambda value: abs(value-elapsed))
        assert abs(sample_time-elapsed) < 0.001, 'No matching native callback clock'
        for c, value in zip(CHANNELS, row[3:]):
            requested = frames[sample_time][c]
            actual = float(value)
            assert math.isfinite(actual)
            observed[c].append(abs(actual-requested))
            if row[2] == 'pitch' and c in pitch:
                pitch[c]['requested'].append(requested)
                pitch[c]['observed'].append(actual)
    def stats(values):
        assert values, 'Missing observations'
        return {'mean': statistics.mean(values), 'max': max(values),
                'p95': sorted(values)[int((len(values)-1)*0.95)]}
    summary = {'run': index+1, 'runs': len(native_runs), 'native_frames': len(times), 'mission_samples': len(observed[15]), 'channels': {}}
    for c in CHANNELS:
        summary['channels'][str(c)] = {'immediate': stats(immediate[c]),
                                     'next_callback': stats(retention[c]),
                                     'mission': stats(observed[c])}
    summary['pitch_ranges'] = {str(c): {key: [min(values), max(values)] if values else None for key, values in data.items()}
                               for c, data in pitch.items()}
    return summary

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('trace', type=Path)
    parser.add_argument('logfile', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--assert-stabilators', action='store_true')
    parser.add_argument('--run', type=int, default=-1, help='1-based mission run; default last')
    args = parser.parse_args()
    summary = analyze(args.trace, args.logfile, args.run)
    print(f"Run {summary['run']} of {summary['runs']}")
    print('arg | immediate max | next callback MAE | mission MAE | mission p95')
    for c, data in summary['channels'].items():
        print(f"{c:>3} | {data['immediate']['max']:.6f} | {data['next_callback']['mean']:.6f} | {data['mission']['mean']:.6f} | {data['mission']['p95']:.6f}")
    print(json.dumps(summary['pitch_ranges'], indent=2))
    if args.output:
        args.output.write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    if args.assert_stabilators:
        # Diagnostic gate in normalized argument units, not a product tolerance.
        bad = [c for c in ('15', '16') if summary['channels'][c]['mission']['p95'] > 0.01]
        if bad:
            raise SystemExit('FAIL: stabilator values do not survive to mission observation: '+', '.join(bad))
        print('PASS: stabilator mission-read p95 error <= 0.01 normalized argument units')
