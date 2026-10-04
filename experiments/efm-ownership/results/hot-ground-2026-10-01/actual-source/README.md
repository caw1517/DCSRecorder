# Actual hot-ground source and first playback package

The corrected capture produced `20261001T225123Z-0002.csv`: 991 samples over
19.8 seconds, with exactly matching contact sample numbers and timestamps.
The take starts stationary, moves about 26.4 m with a maximum speed of 2.821 m/s,
then stops. All recorded in-air flags are false, all three gear channels remain
down, both engines run, and health remains 20/20. These are source observations,
not playback acceptance or newly agreed tolerances.

`raw/` preserves the complete source CSV and DCS log. `summary.json` and
`contact.json` retain the measurements and contact association. The earlier
failed capture is retained separately; its unit-ID type defect was reproduced
with the real string return and repaired before this successful capture.

The ground prototype uses the normal validated converter with an explicit
trial argument. It requires this exact reviewed source hash plus a complete,
aligned and healthy grounded contact stream. Normal calls still reject speeds
below 70 m/s. The separate native build accepts only this converted tape's
compiled fingerprint and a 0–5 m/s experimental motion envelope. Altered tapes
are refused. The 5 m/s bound is a test guard, not a product capability claim.
Native identity, build, ownership, pose-step and all ordinary data guards remain.

`049-Hornet-Ground-Hold-Release.miz` uses one real custom playback object at the
recorded initial horizontal position and a nearby held stock player. The native
controller applies the exact original 3D pose/state and zero hold motion. An
independent stock witness flies while the mission runs. Ground spawning,
first-visible placement, contact, 30-second held inspection and countdown/release
still require the user-operated simulator check. Full parked completion is
outside this task: this diagnostic removes the lead at the recording end.

Offline native tests pass: actual-tape interpolation, a 33-second held/countdown
clock, original initial release velocity, altered-tape refusal, unchanged normal
airborne refusal/regression, release clock, SDK callback contract and bridge
refusal. Generated mission tests cover early-start refusal, countdown, duplicate
requests, pause, readiness failure, cleanup and completion. The hook tests cover
loaded-field mismatch, stale session, commit/ack failures and restart. Aircraft
dependency, route validation, initial light commands and all 33 initial supported
channels pass. These checks do not establish live contact or loaded-reference
equivalence for the new ground mission.

No acceptance checklist has been checked off. Next: load the new ground mission,
click Fly and observe the held aircraft for 30 seconds without requesting release.
Retain native logs, mission telemetry, contact/health data and user review before
the separate release/first-taxi observation.
