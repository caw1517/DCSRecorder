"""Versioned Hornet exterior columns. Argument 21 remains the speedbrake field."""
PROFILE = 'hornet-exterior-v1'
CHANNELS = (0, 3, 5, *range(9, 19))
BASE_COLUMNS = 't,x,y,z,fx,fy,fz,ux,uy,uz,rx,ry,rz,vx,vy,vz,speedbrake,rpm_left,rpm_right'.split(',')
STATE_COLUMNS = [f'arg_{c}' for c in CHANNELS]

def columns(version, smoke_available=True):
    if version not in (1, 2, 3, 4, 5, 6, 7, 8):
        raise ValueError('Unsupported recording version')
    from engine_state import COLUMNS
    from smoke_state import COLUMNS as SMOKE_COLUMNS
    from light_state import COLUMNS as LIGHT_COLUMNS
    from canopy_state import COLUMNS as CANOPY_COLUMNS
    from wheel_state import COLUMNS as WHEEL_COLUMNS
    from contact_state import COLUMNS as CONTACT_COLUMNS
    return BASE_COLUMNS + (STATE_COLUMNS if version >= 2 else []) + (COLUMNS if version >= 3 else []) + (SMOKE_COLUMNS if version == 4 or (version >= 5 and smoke_available) else []) + (LIGHT_COLUMNS if version >= 5 else []) + (CANOPY_COLUMNS if version >= 6 else []) + (WHEEL_COLUMNS if version >= 7 else []) + (CONTACT_COLUMNS if version >= 8 else [])
