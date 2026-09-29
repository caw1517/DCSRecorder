# Normal wheel capture/playback integration — 29 September 2026

Status: normal live capture/playback accepted for the demonstrated airborne take.
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

## First normal capture

The user completed `20260929T205005Z-0001.csv`: 1,611 samples over 32.20 seconds,
speed 178.9885–223.3675 m/s, with the expected version-seven metadata. The running
companion reports it supported as “Motion + surfaces + engines + smoke + lights
+ canopy + wheels.” Source SHA-256:
`3dae246d802655b782051c9628615dedeaeae2a8b2f2cd2a67bdf027b230385b`.
The original and evidence/package copies are byte-identical.

All 11,277 saved wheel-channel values and all 1,611 sample times exactly match
the mission log. In this airborne take all three compression values are zero,
all three wheel phases are one, and steering is centered at zero. These are
measured states, not substituted defaults. The accepted separate taxi test
covers changing wheel/steering/suspension behavior; this take exercises the
normal app path and airborne initial state.

Prepared `package/wheels-normal-playback` using `DCSRecorder-Hornet-Wheels-Staged`.
The actual converted tape passes native load/evaluation, all wheel samples,
midpoints, initial/final holds and SDK guards; generated mission dependency,
route and configuration checks pass. Normal live playback remains pending.
The user has been asked to close DCS before activating its tape and mission.

After the user confirmed DCS closed, activated the checked package through the
normal library activation path. Installed mission:
`DCSRecorder-Playback-4a6e6f9a.miz`, generation
`4a6e6f9a6b1d4abb8842895465df7c72`. All 730 protected existing file hashes and
the original recording hash remain unchanged. The active wheel-controller tape
and metadata match the prepared package. Live normal playback is the next gate.

## Normal playback accepted

The user reports “Looked good for me” for `DCSRecorder-Playback-4a6e6f9a.miz`.
Evidence from process 24484 is saved under ignored `playback-accepted/` before
further work. All seven channels match the recorded values on every one of
1,612 native post-animation updates and all 1,613 later mission reads during
playing/completion. DCS resets the three wheel phases before each native update;
the integrated callback restores recorded phase one. Compression and steering
remain zero throughout this airborne take, as captured.

The pre-release observations are kept separate: 189 waiting, 150 countdown and
one release-requested read contain zeros, including raw wheel phase zero rather
than one. Those wheel phases represent the same endpoint of the measured
period-one rotation, but this evidence does not claim raw snapshot equality
before release or validate arbitrary nonzero initial ground states. Exact raw
matching is established once recorded playback begins.

Mission COMPLETE occurs at 39.040 seconds, reporting elapsed approximately
32.22 seconds; the 32.20-second tape endpoint is clamped and applied before
completion is published. Native events confirm `staged_exterior_complete` and
object destruction. Cleanup reports `step_hook_already_replaced`, the guarded
destruction path that clears ownership without overwriting the destructor's
replacement table. Other appearance immediate readbacks agree within log
precision (maximum difference about 1e-14); broader motion/engine numerical
review remains a separate gate. Original recording SHA-256 is unchanged.

Normal wheel capture, library classification, conversion, activation and playback
are accepted for this flight. The separate accepted taxi animation test supplies
changing strut/wheel/NWS evidence. Remaining light evidence, numerical review and
combined regression keep the fidelity issue open. Ground starts/contact,
high-speed/reverse wheel sampling and takeoff/landing remain distinct work.
