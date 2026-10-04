"""Per-sample source ground-contact evidence (recording version 8). Read-only DCS values.

Origin AGL is aircraft-origin height above terrain, not wheel clearance; in-air
state and health are evidence for later eligibility rules, not proof of contact.
"""
import math

PROFILE = 'hornet-contact-v1'
COLUMNS = ['in_air', 'terrain_height', 'life', 'life0', 'surface_type']
# DCS land.SurfaceType: LAND, SHALLOW_WATER, WATER, ROAD, RUNWAY.
SURFACES = (1, 2, 3, 4, 5)


def parse(row):
    """Return (in_air, terrain_height, life, life0, surface) or raise for invalid evidence."""
    values = [float(row[k]) for k in COLUMNS]
    if not all(math.isfinite(v) for v in values):
        raise ValueError('Non-finite contact sample')
    air, height, life, life0, surface = values
    if air not in (0, 1) or surface not in SURFACES or life0 <= 0 or not 0 <= life <= life0:
        raise ValueError('Invalid contact sample')
    return int(air), height, life, life0, int(surface)


def summary(raw):
    """Contact facts later ground-eligibility rules build on; no eligibility decision here."""
    rows = [parse(r) for r in raw]
    grounded = [i for i, r in enumerate(rows) if r[0] == 0]
    agl = [float(raw[i]['y']) - rows[i][1] for i in grounded]
    return dict(profile=PROFILE, grounded_samples=len(grounded), airborne_samples=len(rows)-len(grounded),
                first_grounded=bool(rows) and rows[0][0] == 0, last_grounded=bool(rows) and rows[-1][0] == 0,
                health_unchanged=all(r[2] == rows[0][2] for r in rows) and rows[0][2] == rows[0][3],
                grounded_origin_agl=[min(agl), max(agl)] if agl else None,
                surfaces=sorted({rows[i][4] for i in grounded}))
