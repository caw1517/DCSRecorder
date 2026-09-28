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
