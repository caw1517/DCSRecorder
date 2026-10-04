"""Parked-endpoint eligibility for version-8 takes: the final interval must be
stationary, grounded, undamaged and engines-running. Read-only.

The thresholds are PROVISIONAL baselines for measurement, not agreed tolerances;
they are reported with every result and are to be agreed with the user under the
tolerance task. A zero-speed last sample or wheel compression alone never qualifies.
"""
import math
import contact_state

PROFILE = 'hornet-parked-endpoint-v1-provisional'
MIN_TAIL_SECONDS = 2.0       # final interval that must satisfy every criterion
MAX_SPEED = 0.05             # m/s, every sample in the interval
MAX_DISPLACEMENT = 0.05      # m, from the final position
MAX_HEADING_CHANGE = 0.2     # degrees, from the final heading
MIN_ENGINE_CORE = 0.5        # both engines' normalized core speed (idle about 0.65)


def heading(row):
    return math.degrees(math.atan2(float(row['fz']), float(row['fx'])))


def endpoint(raw):
    """Measure the longest final interval meeting every criterion; eligible if long enough."""
    last = raw[-1]
    end = [float(last[k]) for k in ('x', 'y', 'z')]
    life0 = contact_state.parse(raw[0])[2]
    reasons = []
    start = len(raw)
    for i in range(len(raw)-1, -1, -1):
        r = raw[i]
        air, _, life, _, _ = contact_state.parse(r)
        speed = math.sqrt(sum(float(r[k])**2 for k in ('vx', 'vy', 'vz')))
        moved = math.dist([float(r[k]) for k in ('x', 'y', 'z')], end)
        turned = abs((heading(r)-heading(last)+180) % 360-180)
        core = min(float(r['engine_core_left']), float(r['engine_core_right']))
        failed = [name for name, bad in (('airborne', air != 0), ('moving', speed > MAX_SPEED),
                                         ('displaced', moved > MAX_DISPLACEMENT), ('turned', turned > MAX_HEADING_CHANGE),
                                         ('engines_not_running', core < MIN_ENGINE_CORE), ('damaged', life < life0)) if bad]
        if failed:
            reasons = failed
            break
        start = i
    tail = float(last['t'])-float(raw[start]['t']) if start < len(raw) else 0.0
    window = raw[start:]
    measured = dict(tail_seconds=round(tail, 3), samples=len(window),
                    boundary_failure=reasons or ['take_start'])
    if window:
        measured.update(
            max_speed=max(math.sqrt(sum(float(r[k])**2 for k in ('vx', 'vy', 'vz'))) for r in window),
            max_displacement=max(math.dist([float(r[k]) for k in ('x', 'y', 'z')], end) for r in window),
            max_heading_change=max(abs((heading(r)-heading(last)+180) % 360-180) for r in window),
            min_engine_core=min(min(float(r['engine_core_left']), float(r['engine_core_right'])) for r in window))
    return dict(profile=PROFILE, eligible=tail >= MIN_TAIL_SECONDS,
                criteria=dict(min_tail_seconds=MIN_TAIL_SECONDS, max_speed=MAX_SPEED, max_displacement=MAX_DISPLACEMENT,
                              max_heading_change=MAX_HEADING_CHANGE, min_engine_core=MIN_ENGINE_CORE, health='unchanged',
                              contact='grounded'),
                measured=measured)
