"""Measured Hornet strut, wheel phase and steering channels (gear is exterior)."""
PROFILE = 'hornet-wheels-v1'
CHANNELS = (1, 6, 4, 101, 103, 102, 2)
COLUMNS = [f'arg_{c}' for c in CHANNELS]
