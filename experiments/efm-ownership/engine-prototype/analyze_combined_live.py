"""Validate simultaneous native parameter consumption and appearance writes."""
import argparse
import bisect
import collections
import csv
import json
from pathlib import Path
from analyze_parameter_live import inspect


def analyze(calls, events, tape_path, appearance):
    result = inspect(calls, events, tape_path)
    lines = tape_path.read_text().splitlines()
    assert lines[0] == 'DCS_ENGINE_COMBINED_V1'
    tape = [list(map(float, line.split())) for line in lines[2:]]
    times = [r[0] for r in tape]
    phase = float(next(r['time'] for r in result['events']
                       if r['event'] == 'baseline_begin')) + 3
    with appearance.open() as stream:
        rows = list(csv.DictReader(stream))
    assert {r['id'] for r in rows} == {result['events'][1]['id']}
    channels = [28, 29, 89, 90]
    groups = collections.defaultdict(list)
    requested_error = written_error = 0
    for row in rows:
        t = float(row['recorded_time'])
        assert 0 <= t < times[-1]
        assert abs(float(row['time']) - phase - t) < 1e-7
        c = channels.index(int(row['arg'])) + 7
        i = max(0, min(bisect.bisect_right(times, t) - 1, len(tape) - 2))
        a, b = tape[i:i + 2]
        expected = a[c] + (b[c] - a[c]) * (t - a[0]) / (b[0] - a[0])
        requested_error = max(requested_error, abs(float(row['requested']) - expected))
        written_error = max(written_error, abs(float(row['after']) - expected))
        groups[(row['stage'], int(row['arg']))].append(row)
    assert requested_error < 1e-6 and written_error < 1e-5
    assert set(groups) == {(stage, c) for stage in ('sdk', 'post_animation') for c in channels}
    for (stage, channel), group in groups.items():
        stamps = sorted({float(r['recorded_time']) for r in group})
        assert stamps[0] <= .021 and times[-1] - stamps[-1] <= .041
        assert max(b - a for a, b in zip(stamps, stamps[1:])) <= .041
    result['appearance'] = {
        'delivery': 'passed', 'visual_rendering': 'requires separate human verdict',
        'rows': len(rows), 'maximum_requested_error': requested_error,
        'maximum_written_error': written_error,
        'groups': [dict(stage=stage, arg=channel, rows=len(group))
                   for (stage, channel), group in groups.items()]}
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('calls', 'events', 'tape', 'appearance', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    result = analyze(args.calls, args.events, args.tape, args.appearance)
    args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('PASS: native sound consumption and all four SDK/post-animation channels match one tape and clock; clean restoration')
