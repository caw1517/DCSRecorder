# Synchronized exterior recording/playback integration

Status: implemented, installed, offline checks and fresh live capture passed;
the user visually accepted combined motion/state playback. This continues the visually and
numerically accepted isolated stabilator test. The broader visual/engine-state
issue remains open.

## Recording contract

`DCSREC,2` retains the nineteen legacy CSV columns and appends `arg_0`, `arg_3`,
`arg_5`, and `arg_9` through `arg_18`, in that order. Metadata requires
`state_profile,hornet-exterior-v1`. Argument 21 retains the `speedbrake` column;
RPM placeholders remain empty. Values are sampled in the same mission callback
as pose/velocity at 20 ms cadence, including the first state snapshot. Gear is
bounded 0..1; flaps/control surfaces retain -1..1 signs. Missing, nonfinite,
malformed or unsupported-profile state is rejected by conversion.

The log transport envelope remains `DCSREC_LOG,1`; BEGIN metadata specifies the
recording version. The durable GUI-history sink and offline extractor select
columns by that version. Explicit Stop, contiguous sequence, footer, persisted-byte
checks and partial-file behavior are retained.

Version-two native tapes use `DCSREC_PLAYBACK_V2`, sample count, then the exact
profile name. Motion/brake rows append thirteen exterior values. The native reader
validates the whole tape before exposing samples. Linear surface interpolation
shares the motion interval and preserves the initial snapshot and endpoints.
Version-one recordings are not rewritten or filled with invented surface values;
the companion identifies missing exterior capture and selects the legacy module.

## Controller

`HornetStateStagedProbe.dll` / `DCSRecorder-Hornet-State-Staged` is separate from
the accepted legacy installation. A single per-object shadow table owns both the
pre-step motion correction and typed post-animation callback. Unrelated slots
and RTTI remain intact; thread/build/ownership checks and restoration cover both
callbacks together. Independent prototype hooks are not stacked.

The first surface sample is applied with initial pose/brake. SDK callbacks update
desired surfaces on the motion clock; the animation callback reapplies all
thirteen after native animation. Extending the accepted stabilator boundary to
the other surfaces is intended to remove their smaller native overwrites, and
requires this fresh combined comparison. Completion is published only after the
final surface application. Missing callbacks or failed writes/trace output stop
the integration test.

`exterior-<PID>.csv` logs requested/pre-repair/post-repair values.
`DCS_PLAYBACK_EXTERIOR` mission observations include controller elapsed time
(argument 996) and the fourteen surface/brake values. Native motion, mission pose
and lifecycle traces remain available.

## Checks and deployment

- 15 CTests pass: combined motion/animation dispatch, argument forwarding, repeated
  calls, ownership/thread isolation, restoration, native profile/signed initial
  state/interpolation/endpoint checks, and mission completion/failure.
- 12 companion tests pass, including both CSV versions through the Lua sink,
  DCS-style void-success I/O, signed state, and separate-module activation.
- Two capture/conversion checks pass, covering packaged Lua capture, pause/restart,
  malformed state/profile rejection, staged generation and the native tape reader.
- A scratch Saved Games tree exercises the real companion workflow: Create
  practice mission, execute its Lua with a simulated aircraft, extract and validate
  the version-two CSV with build/weather metadata, generate/activate playback,
  and evaluate its tape in the native reader. Source bytes are unchanged. That
  simulated recording is not installed in the user's flight library.

After the user closed DCS, ten deployed files matched the manifest: the separate
module (without a fabricated tape), updated autosave hook, and
`DCSRecorder-Exterior-Integrated-Capture.miz` directly in Missions. Legacy DLL and
tape hashes remained unchanged. The previous hook and launcher configuration are
backed up under `DCSRecorder/backups`.

The companion was running from an older worktree. Its launcher now points to
`E:/Projects/DCS_Recorder/companion`; the verified instance was restarted at the
same loopback URL. The API confirms the current hook hash and all four existing
recordings remain supported. Local manifests and scratch artifacts are under
`package/exterior-integration-setup` (ignored).

## Fresh synchronized capture and live acceptance

The fresh take `20260927T033114Z-0002.csv` passes companion validation: 35.48 seconds,
1,775 synchronized version-two samples, `hornet-exterior-v1`, DCS 2.9.29.27468.
Ground speed stays between 101.29 and 218.12 m/s. All three gear channels and the
speedbrake span 0..1; both stabilators, flaps, ailerons, leading-edge flaps and
rudders vary. The earlier take containing a landing remains preserved but is
unsupported by the current airborne speed guard.

The new take passes module-dependency, route timing, clean-controls and native
tape evaluation checks. After the user closed DCS, the companion activation path
installed **DCSRecorder-Playback-exterior.miz** directly in Saved Games/DCS/Missions.
The source CSV is byte-identical (SHA256
`93705d1e7364f0133519ab90b4f81fb955728208a5635aa05d264861978815d4`), the installed
controller matches the build, and the accepted legacy DLL and tape are unchanged.
Local verification and activation manifests are under
`package/exterior-live-20260927T033114` (ignored).

The user reports: “Everything looked great” and “all the flight controls we were
testing worked flawlessly.” This accepts the combined flight-path and tested
gear/flap/control-surface appearance, including the repaired stabilators. The
user also observed continuous afterburner appearance. Engine state is not captured
or actuated by this profile, so that remains an outstanding fidelity defect;
this acceptance does not cover nozzles, afterburner effects or sound.

This checkpoint records visual feedback only. It does not independently establish
numerical retention, automatic completion/removal or mission-restart behavior;
those require the integrated runtime traces. Suspension/wheels, canopy, smoke,
lights and engine/nozzle/effects/sound remain outstanding groups. Next engine
work must establish synchronized per-engine capture and playback actuation,
including a non-afterburning case and separate left/right transitions. Nozzle
geometry and audible engine behavior require their own comparisons.
