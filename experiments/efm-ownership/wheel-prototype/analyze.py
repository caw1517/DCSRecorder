"""Report raw wheel/compression changes without assuming a rotation period."""
import argparse
import json
import math
from pathlib import Path

CHANNELS = [0, 5, 3, 1, 6, 4, 101, 103, 102]
STEERING_CHANNELS = CHANNELS + [2, 17, 18]


def analyze(path):
    rows = []
    start = end = None
    marks = []
    declared = False
    protocol = None
    channels = None
    for line in path.read_text(errors='replace').splitlines():
        if 'DCSWHEEL,' not in line:
            continue
        version, data = line.split('DCSWHEEL,', 1)[1].split(',', 1)
        assert version in ('1', '2') and protocol in (None, version), 'Separate protocol versions before analysis'
        protocol = version
        fields = data.split(',')
        if fields[0] == 'BEGIN':
            assert start is None, 'Separate mission runs before analysis'
            start = float(fields[1])
            assert fields[3] == 'FA-18C_hornet'
        elif fields[0] == 'CHANNELS':
            channels = list(map(int, fields[1:]))
            assert channels == (STEERING_CHANNELS if protocol == '2' else CHANNELS)
            declared = True
        elif fields[0] == 'MARK':
            marks.append(dict(time=float(fields[1]), label=fields[2]))
        elif fields[0] == 'DATA':
            assert declared and start is not None and end is None
            assert int(fields[1]) == len(rows)+1, 'Missing or duplicate sample'
            row = list(map(float, fields[2:]))
            assert len(row) == 7+len(channels) and all(map(math.isfinite, row))
            if rows:
                assert 0 < row[0]-rows[-1][0] <= .1, 'Non-monotonic or gapped clock'
            rows.append(row)
        elif fields[0] == 'END':
            assert end is None and fields[1] == 'user_stop', 'Capture did not finish normally'
            assert int(fields[2]) == len(rows)
            end = float(fields[3])
    assert start is not None and end is not None and len(rows) >= 250, 'Incomplete/short capture'
    speeds = [math.sqrt(sum(v*v for v in r[4:7])) for r in rows]
    report = dict(protocol=int(protocol), samples=len(rows), duration=end-start, max_gap=max(b[0]-a[0] for a,b in zip(rows, rows[1:])),
        speed_range=[min(speeds), max(speeds)], stopped_samples=sum(s<.05 for s in speeds),
        rolling_samples=sum(s>.5 for s in speeds), marks=marks, channels={})
    for i, channel in enumerate(channels):
        values = [r[7+i] for r in rows]
        deltas = [b-a for a,b in zip(values, values[1:])]
        report['channels'][channel] = dict(min=min(values), max=max(values), initial=values[0], final=values[-1],
            changes=sum(abs(d)>1e-8 for d in deltas), max_raw_step=max(map(abs, deltas)),
            large_raw_steps=[dict(time=rows[j+1][0], before=values[j], after=values[j+1], speed=speeds[j+1])
                for j,d in enumerate(deltas) if abs(d)>.5][:20])
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('log', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = analyze(args.log)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(f'PASS: {result["samples"]} ordered samples; max gap {result["max_gap"]:.6f}s; raw ranges saved (rotation period not assumed)')
