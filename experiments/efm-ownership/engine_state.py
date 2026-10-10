"""Version-three native engine capture and alignment on the motion clock."""
import bisect
import math

PROFILE = 'hornet-native-engine-v1'
APPEARANCE = [f'arg_{c}' for c in (28, 29, 89, 90)]
NATIVE = [f'engine_{channel}_{side}' for side in ('left', 'right')
          for channel in ('core', 'fan', 'thrust', 'power')]
COLUMNS = APPEARANCE + ['engine_time'] + NATIVE


def align(raw, max_delay=.05, gap_limit=.15):
    times = [float(r['engine_time']) for r in raw]
    values = [[float(r[c]) for c in NATIVE] for r in raw]
    for i, (t, v) in enumerate(zip(times, values)):
        delay_limit = max_delay if i else .05
        if not math.isfinite(t) or not 0 <= t - float(raw[i]['t']) <= delay_limit:
            raise ValueError(f'Native engine sample must be within {delay_limit*1000:g} ms after its motion sample')
        if i and not 0 <= t - times[i-1] <= gap_limit:
            raise ValueError('Native engine clock gap or reversal')
        if i and t == times[i-1] and v != values[i-1]:
            raise ValueError('Native engine values disagree at the same timestamp')
        if any(not math.isfinite(x) or not 0 <= x <= (1.2 if c % 4 < 2 else 4)
               for c, x in enumerate(v)):
            raise ValueError('Invalid native engine values')
        if v[2] != v[3] or v[6] != v[7]:
            raise ValueError('Native thrust/power differ; current playback requires equal E0/F0')
    # Multiple motion rows can be consumed in one GUI frame. Identical native
    # reads at that frame's clock are one observation, not invented samples.
    unique = [(t, v) for i, (t, v) in enumerate(zip(times, values)) if not i or t != times[i-1]]
    if len(unique) < 2:
        raise ValueError('Not enough distinct native engine sample times')
    times, values = map(list, zip(*unique))
    result = []
    for row in raw:
        t = max(times[0], min(times[-1], float(row['t'])))
        i = max(0, min(bisect.bisect_right(times, t)-1, len(times)-2))
        u = (t-times[i])/(times[i+1]-times[i])
        appearance = [float(row[c]) for c in APPEARANCE]
        if any(not math.isfinite(v) or not 0 <= v <= 1 for v in appearance):
            raise ValueError('Invalid engine appearance')
        result.append(appearance + [values[i][c]+u*(values[i+1][c]-values[i][c])
                                    for c in (0, 1, 2, 4, 5, 6)])
    return result
