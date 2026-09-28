# Normal canopy workflow — 28 September 2026

Status: implemented, offline checked and installed; a new normal
recording/playback run remains pending. The [isolated captured-canopy replay](../canopy-2026-09-28/README.md)
is already accepted visually and numerically.

New canopy-enabled practice missions sample exterior argument 38 on the same
50 Hz mission clock as motion, surfaces and lights. Recording version six adds
`canopy_profile,hornet-canopy-v1` and `arg_38` after the lights. Measured values
remain unchanged, including the initial position and the observed fully-open
value of about 0.9. The sink validates all appended appearance data, preserves
the engine helper's existing 36-field input, and saves the appended state after
engine/optional-smoke measurements. Invalid samples never become ready flights.

The library displays `+ canopy` and chooses the new
`DCSRecorder-Hornet-Canopy-Staged` module / `HornetCanopyStagedProbe.dll`.
Native tape version five contains 43 fields: the existing 42 motion/surface/
engine/light fields plus canopy. Initial state, transitions and endpoint use the
same native playback clock. The shared animation callback applies and traces
canopy with the other recorded appearance channels. Generated missions also
forward the canopy flag and emit independent later canopy reads.

Older recording versions retain their tape format, library descriptions and
module selection. Source recordings are immutable. White smoke remains optional
and white-only; ground starts, jettison and internal cockpit restoration remain
outside this change.

Validation passed:

- All 31 companion tests, including four canopy workflow tests through the real
  Lua save hook, library, conversion and mission packaging. Cases cover optional
  smoke, a nonzero initial canopy position, changing values, invalid values and
  profile, source immutability and packaged capture/telemetry configuration.
- The converted native tape's every canopy sample/midpoint, initial/final holds
  and guarded SDK writes; ordinary recorded motion is also evaluated at 100 Hz.
- Six CTest checks for native motion geometry, native step boundary, staged
  contract/lifecycle, animation boundary and the new module callback contract.

`companion/install_canopy_workflow.py prepare` produced the ignored
`package/canopy-workflow`: eleven files and 643 protected file hashes. The package
contains a new `DCSRecorder-Practice-Canopy-0adb0c4b.miz`, updated save hook and
settings, and a separate playback module. Installation backs up the prior hook
and settings, validates hashes and requires DCS closed to reload modules/hooks.
After the user confirmed DCS was closed, installation verified all eleven
installed hashes and all 643 protected files unchanged. The prior hook and
settings were backed up under `package/canopy-workflow/backup`. The new practice
mission is installed in Saved Games/DCS/Missions. Existing recordings, active
tapes and previously accepted playback modules were preserved.

The companion was restarted on its existing `http://127.0.0.1:46543/` address
with the new code/settings. Its library API recognizes the installed hook and
reports all five existing recordings supported. The user has been asked to make
a short normal take in the new mission, retaining usual canopy/light settings,
and confirm the library adds `+ canopy`. This verifies the ordinary integration;
changing-canopy rendering is already covered by the accepted isolated replay.

## First normal take: saved, outside current speed support

The user's “unsupported” report was reproduced through both the live library API
and direct library validation. `20260928T164034Z-0001.csv` is a completed
version-six recording: 354 samples, 7.06 seconds, explicit user stop, canopy
closed throughout. SHA-256 remains
`15a8f3cf07e4bd36c9de9f047727a4abef050064e4acc0ac2bf3cb2e11432ca3`.
The capture and log are preserved in ignored `unsupported-capture/`.

Measured world speed rises from 243.48 to 267.67 m/s (maximum about 520.3 knots).
It first exceeds the existing 260 m/s playback cap at 4.72 seconds. Saved motion
fields match the raw mission rows exactly; position derivatives and velocity
agree within 0.01082 m/s. This is a real envelope crossing, not shifted canopy
columns or a units conversion error. Capture succeeded; playback remains outside
the current supported range. No cap was raised and no source data was edited.

The converter previously combined speed and speed-brake errors into a generic
message mentioning ground transitions. It now reports the precise value,
elapsed time and applicable limit separately, and distinguishes ground speed
from indicated airspeed. A regression through the actual save/library path
failed for overspeed, underspeed and invalid speed brake before this change;
all 32 companion tests pass afterward. The restarted app was checked against
the original take and now serves the precise limit reason. DCS was left running.

A second take (`20260928T164051Z-0002.partial`) separately stopped saving when
the engine sampler exceeded its 50 ms timing guard. It was retained and copied
for diagnosis, not promoted or filled with invented engine samples. That later
failure explains the current save-status message; it did not invalidate the
completed first take. Its scheduling cause is not established.

The user has been asked to record a short level cruise at moderate speed in the
same mission. Successful normal playback remains pending. Broader speed support
belongs with [Validate the single-aircraft flight envelope through takeoff and landing](https://github.com/caw1517/DCSRecorder/issues/7).

## Supported normal take and activation regression

The user confirmed the next take appears correctly in the app.
`20260928T164529Z-0003.csv` passes library validation: 363 samples / 7.24 seconds,
163.79–178.91 m/s world speed and canopy closed (0) throughout. SHA-256:
`632c1089ce107d1075263f9ae4df5f86115f9dc85a5be10d6243834546257e90`.
The source and log are saved under ignored `capture-ready/`.

Its package in ignored `package/canopy-normal-playback` passes installed mission,
route and configuration checks, plus native canopy samples/interpolation/holds
and recorded-motion evaluation. Preparing activation exposed a missed module
allowlist entry for `DCSRecorder-Hornet-Canopy-Staged`. The earlier workflow test
mocked activation and therefore did not cover that boundary. The test now calls
real activation in a temporary installation, checks the copied tape/mission and
backup, and failed with `Unsupported playback module` before the allowlist fix.
All 32 companion tests pass with that actual activation path covered.

After the user confirmed DCS was closed, the real activation path installed
`DCSRecorder-Playback-b0f5a770.miz` and the new module's checked tape. All 500
protected file hashes remained unchanged, including the source recording.
The activation report is saved under ignored `capture-ready/activation.json`.
Normal live playback remains pending. The speed cap is a temporary validated-
envelope restriction, not a demonstrated DCS limit or final product requirement;
the roadmap already calls for removing remaining speed/duration restrictions as
the corresponding behavior is implemented and verified.
