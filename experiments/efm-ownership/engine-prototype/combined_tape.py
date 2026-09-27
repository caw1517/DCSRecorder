"""Align captured appearance to native sample times, preserving engine values."""
import bisect
import csv
import math
from parameter_tape import prepare as prepare_native

CHANNELS = [28, 29, 89, 90]


def prepare(logfile, target):
    metadata = prepare_native(logfile, target)
    native = [list(map(float, line.split())) for line in target.read_text().splitlines()[2:]]
    appearance = []
    order = None
    for line in logfile.read_text(encoding='utf-8-sig').splitlines():
        prefix = 'DCSENGINE_MISSION,1,'
        if prefix not in line:
            continue
        row = next(csv.reader([line.split(prefix, 1)[1]]))
        if row[0] == 'BEGIN':
            appearance = []
            order = None
        elif row[0] == 'CHANNELS':
            order = list(map(int, row[2:]))
        elif row[0] == 'DATA':
            assert order is not None
            values = dict(zip(order, map(float, row[8:])))
            appearance.append([float(row[3]), *[values[c] for c in CHANNELS]])
    assert len(appearance) >= 2
    assert all(math.isfinite(v) for row in appearance for v in row)
    assert all(0 <= v <= 1 for row in appearance for v in row[1:])
    times = [row[0] for row in appearance]
    assert all(0 < b - a <= .15 for a, b in zip(times, times[1:]))
    endpoint_hold = 0
    for row in native:
        absolute = metadata['origin'] + row[0]
        clamped = max(times[0], min(times[-1], absolute))
        endpoint_hold = max(endpoint_hold, abs(absolute - clamped))
        assert abs(absolute - clamped) <= .05, 'Appearance does not cover native capture'
        index = max(0, min(bisect.bisect_right(times, clamped) - 1, len(times) - 2))
        a, b = appearance[index:index + 2]
        weight = (clamped - a[0]) / (b[0] - a[0])
        row.extend(a[c] + weight * (b[c] - a[c]) for c in range(1, 5))
    target.write_text('DCS_ENGINE_COMBINED_V1\n' + str(len(native)) + '\n' +
                      '\n'.join(' '.join(format(v, '.12g') for v in row) for row in native) + '\n',
                      encoding='ascii')
    metadata['appearance_channels'] = CHANNELS
    metadata['appearance_samples'] = len(appearance)
    metadata['appearance_endpoint_hold_seconds'] = endpoint_hold
    metadata['appearance_alignment'] = 'Linear interpolation at native absolute model times; no per-stream rebasing'
    return metadata
