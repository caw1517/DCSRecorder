# Synchronized exterior recording/playback integration

Status: implemented, installed, offline checks passed; fresh live capture and
combined motion/state playback remain pending. This continues the visually and
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

## Next live comparison

Start DCS and fly **DCSRecorder-Exterior-Integrated-Capture**. Begin nearly level,
use F10 Start, then exercise pitch/roll/rudder and gear/flaps/brake while airborne.
Use F10 Stop and confirm the take appears in the companion. A fresh capture is
required: the older motion take and separate surface diagnostic are different
flights and must not be spliced together.

With DCS closed, generate playback for the new take in the companion. Start its
F10 countdown, inspect the lead, allow completion, and test mission restart.
Compare source/requested/post-animation/mission values, initial pose/state, path
continuity and cleanup before accepting this group. Suspension/wheels, canopy,
smoke, lights and engine/nozzle/effects/sound remain outstanding groups.
