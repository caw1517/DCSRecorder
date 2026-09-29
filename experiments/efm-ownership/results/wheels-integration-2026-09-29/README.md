# Normal wheel capture/playback integration — 29 September 2026

Status: implemented, checked and installed; normal live capture/playback pending.
The [separate taxi animation test](../wheels-2026-09-28/README.md) is already
accepted visually and numerically for wheel rotation, strut motion and NWS.

Version-seven recordings append `wheel_profile,hornet-wheels-v1` and seven raw
channels after the existing canopy field: nose/left/right compression 1/6/4,
nose/left/right wheel phase 101/103/102, and signed nose-wheel steering 2.
Gear deployment stays in the established exterior profile. The mission emits
51 fields. The save hook validates the appended appearance fields, passes the
existing 36-field engine input to the unchanged native capture helpers, and
restores the appearance suffix afterward. Completed CSVs have 62 fields with
white smoke or 60 without it. Failed/incomplete captures remain partial.

The importer validates profile, column order, finite/ranged values and existing
motion constraints. It produces native tape version six with 50 fields per
sample and the wheel profile after canopy. Older recordings retain their
original tape version and module. No source recording is rewritten.

`DCSRecorder-Hornet-Wheels-Staged` / `HornetWheelsStagedProbe.dll` is a separate
integrated controller. Initial values, active playback and endpoint values use
the common recorded clock. Compression/steering interpolate linearly; wheel
phase uses the accepted period-one short arc, with raw endpoints and constant
holds preserved. The existing post-animation callback reapplies the wheels
alongside surfaces, engine appearance, lights and canopy; no second competing
hook is introduced. Gear deployment is repaired through the existing exterior
writer. Mission telemetry includes `DCS_PLAYBACK_WHEELS` on the same elapsed
clock for later retention checks.

The library labels new takes `+ wheels`, routes them to the new module and
permits actual activation with tape rollback. `wheels_capture` requires the
canopy/lights/engine workflow; white smoke remains optional. The current airborne
speed/start/duration guards remain unchanged. Recording these channels does not
enable ground starts, taxi trajectory playback or contact physics. High-speed
wheel aliasing, reverse rotation and unloaded/ground transitions still need
separate validation; no wheel phase is synthesized from aircraft speed.

Validation: all **37 companion tests** pass, including version-seven save,
library classification, native conversion, mission configuration forwarding,
actual activation/backup, optional smoke, signed steering, malformed-value/profile
rejection and immutable source bytes. The native converted-tape check exercises
every sample/midpoint, circular wrap interpolation, initial/final holds and SDK
identity/bounds/value guards. The packaged practice harness confirms the live
mission samples signed argument 2 and emits the new metadata/field count.
Seven native/lifecycle checks pass: recorded geometry, native step boundary,
staged contract, mission lifecycle, wheel animation repair, new controller callback
contract and combined engine boundary. Fixtures establish plumbing, not new
physical flight behavior.

Installation package `package/wheels-workflow` contains eleven verified files.
DCS and the companion were already closed. The installer preserved all 713
protected file hashes and backed up the previous hook/settings. Engine/smoke
capture helpers, older installed controllers and existing recordings remain
unchanged. New practice mission:
`DCSRecorder-Practice-Wheels-d46c24a8.miz`.

The companion restarted at `http://127.0.0.1:46543/` (process 25796 at this
checkpoint). Its library endpoint reports the current hook installed, seven
existing recordings and two existing partials. The user has instructions for
a short normal airborne take and confirmation of `+ wheels` in the app.
Live source values and the generated normal playback still await acceptance.
