-- Compatibility replacement for the failed capture hook.
-- Capture runs inside EFM-Probe-Hornet-record.miz using env.info.
-- No callbacks or GUI-to-mission bridge are required.
log.write('DCS_RECORDER',log.INFO,'Mission-log recorder installed; capture is controlled by the mission F10 menu.')
