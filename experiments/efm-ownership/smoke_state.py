"""Version-four measured smoke transitions, using their own simulation timestamps."""
import math

PROFILE = 'hornet-native-smoke-v1'
CLSID = '{INV-SMOKE-WHITE}'
COLUMNS = ['smoke_time', 'smoke_on']


def transitions(metadata, raw):
    if (metadata.get('smoke_profile') != PROFILE or metadata.get('smoke_station') != '10'
            or metadata.get('smoke_clsid') != CLSID):
        raise ValueError('Unsupported smoke profile/loadout; only station-10 white smoke is verified')
    first = float(raw[0]['t'])
    end = float(raw[-1]['t'])
    events = []
    previous_time = previous_state = None
    for row in raw:
        t = float(row['smoke_time'])
        if row['smoke_on'] not in ('0', '1'):
            raise ValueError('Smoke state must be measured OFF or ON')
        on = int(row['smoke_on'])
        if not math.isfinite(t) or not 0 <= t - float(row['t']) <= .05:
            raise ValueError('Smoke sample must be within 50 ms after its motion sample')
        if previous_time is not None:
            if not 0 <= t - previous_time <= .15:
                raise ValueError('Smoke clock gap or reversal')
            if t == previous_time and on != previous_state:
                raise ValueError('Smoke states disagree at one timestamp')
        # Initialize from the first measured state (at most 50 ms after motion).
        # Subsequent changes keep their actual capture time, with no interpolation.
        if not events:
            events.append(dict(time=0.0, on=bool(on)))
        elif on != previous_state and t <= end:
            events.append(dict(time=t-first, on=bool(on)))
        previous_time, previous_state = t, on
    return events
