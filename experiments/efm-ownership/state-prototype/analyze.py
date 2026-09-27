"""THROWAWAY: validate a single diagnostic take and summarize observed ranges."""
import argparse
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path

def analyze(logfile, output):
    source = logfile.read_bytes()
    records = list(csv.reader(
        line.split('DCSSTATE_LOG,1,', 1)[1].strip()
        for line in source.decode('utf-8', errors='replace').splitlines()
        if 'DCSSTATE_LOG,1,' in line
    ))
    begins = [r for r in records if r[0] == 'BEGIN']
    headers = [r for r in records if r[0] == 'CHANNELS']
    ends = [r for r in records if r[0] == 'END']
    assert len(begins) == len(headers) == len(ends) == 1, 'Expected one complete take'
    take = begins[0][1]
    assert begins[0][2] == 'FA-18C_hornet'
    assert all(r[1] == take for r in records), 'Mixed take identifiers'
    channels = list(map(int, headers[0][2:]))
    assert channels == list(range(31)), 'Unexpected channel layout'
    rows = [r for r in records if r[0] == 'DATA']
    assert len(rows) >= 2 and ends[0][2] == 'user_stop'
    assert int(ends[0][3]) == len(rows), 'Footer count mismatch'
    assert all(int(r[2]) == i + 1 and len(r) == 36 for i, r in enumerate(rows)), 'Missing or malformed row'
    times = [float(r[3]) for r in rows]
    assert all(math.isfinite(v) for v in times)
    deltas = [b - a for a, b in zip(times, times[1:])]
    assert all(d > 0 for d in deltas), 'Non-monotonic capture'
    assert all(math.isfinite(float(v)) for r in rows for v in r[5:])
    segment = 'baseline'
    marks = []
    for r in records:
        if r[0] == 'MARK':
            segment = r[3]
            marks.append({'time': float(r[2]), 'segment': segment})
        elif r[0] == 'DATA':
            assert r[4] == segment, 'Marker/data mismatch'
    summary = {
        'source_sha256': hashlib.sha256(source).hexdigest(),
        'samples': len(rows), 'first_time': times[0], 'last_time': times[-1],
        'duration': times[-1] - times[0], 'median_dt': statistics.median(deltas),
        'min_dt': min(deltas), 'max_dt': max(deltas), 'markers': marks, 'segments': {},
    }
    for segment in dict.fromkeys(r[4] for r in rows):
        group = [r for r in rows if r[4] == segment]
        changed = {}
        for c in channels:
            values = [float(r[c + 5]) for r in group]
            if max(values) - min(values) > 0.0001:
                changed[str(c)] = dict(min=min(values), max=max(values), start=values[0], end=values[-1])
        summary['segments'][segment] = dict(samples=len(group), start=float(group[0][3]), end=float(group[-1][3]), changed=changed)
    output.mkdir(parents=True, exist_ok=True)
    with (output / 'arguments.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['take', 'row', 't', 'segment', *[f'arg_{c}' for c in channels]])
        writer.writerows(r[1:] for r in rows)
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(f"PASS: {len(rows)} consecutive finite samples, {summary['duration']:.2f}s, "
          f"{len(marks)} markers, dt {min(deltas):.6f}-{max(deltas):.6f}s, explicit user_stop")
    return summary

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('logfile', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    analyze(args.logfile, args.output)
