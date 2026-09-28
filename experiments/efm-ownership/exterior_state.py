"""Versioned Hornet exterior columns. Argument 21 remains the speedbrake field."""
PROFILE = 'hornet-exterior-v1'
CHANNELS = (0, 3, 5, *range(9, 19))
BASE_COLUMNS = 't,x,y,z,fx,fy,fz,ux,uy,uz,rx,ry,rz,vx,vy,vz,speedbrake,rpm_left,rpm_right'.split(',')
STATE_COLUMNS = [f'arg_{c}' for c in CHANNELS]

def columns(version):
    if version not in (1, 2, 3):
        raise ValueError('Unsupported recording version')
    from engine_state import COLUMNS
    return BASE_COLUMNS + (STATE_COLUMNS if version >= 2 else []) + (COLUMNS if version == 3 else [])
