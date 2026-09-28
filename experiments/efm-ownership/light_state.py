"""Measured exterior light brightness on the mission sample clock."""
PROFILE = 'hornet-lights-v1'
CHANNELS = (88, 190, 191, 192, 193, 210, 212)
COLUMNS = [f'arg_{c}' for c in CHANNELS]
