# Roadmap: complete one-aircraft playback first

Updated 29 September 2026. The [GitHub map](https://github.com/caw1517/DCSRecorder/issues/1)
is the issue-tracking entry point.

## V1 scope and V2 backlog

The user selected **white smoke only for V1**. The supported Hornet visual/engine
fidelity milestone is accepted, including the final combined flight and refueling
light. Numerical audit, lifecycle evidence and 44 regression checks are recorded
in the [final acceptance record](../experiments/efm-ownership/results/fidelity-final-2026-09-29/README.md).
A small measured speed-brake residual (up to 0.010002 on its 0–1 scale) is retained
under exact synchronized-state work. By user choice, landing/taxi ground
illumination will be checked with ground operations.

These features are explicitly deferred to V2 and do not block V1:

- [Improve playback engine sound depth (V2)](https://github.com/caw1517/DCSRecorder/issues/12): investigate and refine the small perceived bass/impact difference while preserving accepted recorded power response.
- [Add multicolor demonstration smoke (V2)](https://github.com/caw1517/DCSRecorder/issues/13): validate and retain selected smoke-generator colors beyond white.

## Current milestone

[Visual and engine-state fidelity](https://github.com/caw1517/DCSRecorder/issues/6)
is accepted for the documented Hornet V1 scope. Next: exact original starting
position and synchronized state, followed by the ground-flight envelope.


The [single-aircraft record-to-replay workflow](https://github.com/caw1517/DCSRecorder/issues/5)
is implemented and accepted for the current airborne scope. The local companion
saves completed takes automatically, lists/renames/validates them and generates
practice/playback missions. The latest fast-roll take completed successfully after
removing prototype altitude/rate caps. The nose-jump fix remains active.

The player waits in Active Pause; F10 starts a three-second countdown. Actual
release/activation anchors playback. The lead receives the original first-sample
pose, velocity and speed brake without acquisition blending or translation; the
player starts approximately 150 feet behind. Completion removes the lead and
leaves the mission running. Restarting the mission replays the take.

The user accepted all remaining requested workflow checks. Automated and telemetry
results are recorded separately from that manual confirmation in the
[validation record](validation/workflow-2026-09-26.md). This closes the workflow
milestone, not the full one-aircraft product milestone.

## Standing decisions

- One player, one account, one DCS process. Multiplayer is out of scope.
- Finish one-aircraft fidelity before implementing layers.
- Reproduce measured flight motion rather than guessing pilot inputs.
- Zero wind remains the supported baseline; wind compensation is not a current gate.
- Preserve original recordings and original placement by default.
- Place generated missions directly in the user's `Saved Games/DCS/Missions`
  folder. This includes diagnostic missions; retain existing files and use a new
  filename when needed. The user confirmed this preference after the exterior-state diagnostic.
- Full ground-to-ground demonstrations are required eventually: stationary hot
  start, taxi, takeoff, 250–500 ft low passes, hard turns, approach, touchdown and
  rollout. The requested 7.5-G / 350-knot turn is an acceptance target. Artificial
  altitude or maneuver caps are not product requirements.
- Initial aircraft pose and all supported state must represent the same recorded
  moment. Exact cockpit systems or internal engine reconstruction is distinct
  from observable exterior/engine-state reproduction.
- Synchronized lead-call voice is future work, with no promised timing precision.

## Follow-up work

| Work | Remaining scope |
| --- | --- |
| [Exact starting position and state](https://github.com/caw1517/DCSRecorder/issues/11) | Extend accepted exact airborne initialization to stationary hot ground starts, original parking/demo spots and synchronized aircraft state. Resolve the measured speed-brake retention residual and assess complete pre-release state. |
| [Flight envelope through takeoff and landing](https://github.com/caw1517/DCSRecorder/issues/7) | Validate ground transitions, landing/taxi light ground illumination, low passes, hard maneuvers and longer full-demo durations. Remove remaining speed/duration restrictions as the corresponding behavior is implemented and verified. |
| [Essential physical interactions](https://github.com/caw1517/DCSRecorder/issues/3) | Ground contact, collision/damage and wake in both directions; decide how physical disturbances affect the recorded path. |
| [Installation and compatibility](https://github.com/caw1517/DCSRecorder/issues/8) | Portable setup, local asset preparation, supported-build maintenance, rollback and performance. |
| [Layered playback](https://github.com/caw1517/DCSRecorder/issues/9) | After one-aircraft gates: independently identified takes sharing a playback clock while another is recorded. Preserve originals and verify timing/performance. |
| [Recorded lead calls](https://github.com/caw1517/DCSRecorder/issues/10) | Research audio capture/delivery, onset/latency, drift, pause alignment and synchronization. Ordering relative to layers remains open. |

## Historical checkpoints

These entries record the progression of experiments; current status is above.

The fresh application workflow is accepted after the
[missing-gear diagnosis](../experiments/efm-ownership/results/application-gear-2026-09-27/README.md).
The old take lacked gear channels; a fresh version-two take captures all three
through 0..1, and the user reports successful playback. The app identifies
motion-only takes and generates clearly named exterior-capable practice missions.
Engine-state work can resume; integrated endpoint/restart evidence remains open.

The full engine diagnostic capture passes alignment checks. The user accepted
the isolated nozzle/flame playback, corroborated by numerical retention, but
heard idle-like sound throughout. See the [live result](../experiments/efm-ownership/results/engine-playback-2026-09-27/README.md).
The follow-up callback probe recorded zero ordinary EFM engine-parameter calls
during 41.8 seconds of playback. The next experiment is
**DCSRecorder-Sound-Routing-Test.miz**, a 15-second alternating engine/afterburner
sample test through a separate spatial sound script. It tests audio control;
sound fidelity and integration with recorded motion remain open. No new throttle
capture is needed. See the [sound-path finding](../experiments/efm-ownership/results/engine-sound-2026-09-27/README.md).

That 15-second test completed but sounded idle throughout. Offline execution of
the retained DCS sounder loader exposed a logging assumption: sounders lack file
I/O, so missing sounder.log did not establish non-execution. A temporary scoped
logging repeat also sounded idle and produced no script diagnostics. The separate
test DLL's guarded observer confirmed the custom sounder selection and instance
presence throughout the next live run. The logging filter then proved incomplete:
DCS's ALL mask excludes TRACE. The temporary hook now explicitly includes TRACE,
with a startup self-check. The next live run logged source creation and all five
audio phases at their expected times, but the user still heard idle throughout.
A separate **DCSRecorder-Sound-Audibility-Test.miz** now compares a generated
control tone, stock samples and an explicitly defined afterburner source, with
playing-state and engine-input logs. Its sources reported playing, but the user
heard no beeps and was uncertain about other changes; audibility is not accepted.
The user reaffirmed recording/replaying engine parameters with DCS deriving the
sound. Sample-routing tests are set aside; investigate the native engine-parameter
interface using the existing RPM capture and independently validated afterburner
state. A separate **DCSRecorder-Native-RPM-Playback.miz** is now installed for the
first native getter replay: 3 seconds original RPM, 48.899 seconds of recorded
core RPM, then 3 seconds after restoration. It retains DCS's stock renderer and
logs actual callers and returned values. Offline boundary, package and mission
checks pass. The first live run confirms 24,450 Sound.dll core-RPM overrides
matching the recording and clean restoration. The user heard a slight change,
but no afterburner and less intensity than the real aircraft. Core RPM delivery
is established; sound fidelity is not accepted. Native sound also consumes fan
RPM and thrust-related inputs. Establish capture of the real aircraft's missing
fan and power/AB inputs before replaying them; do not infer thrust from RPM alone.
An additive read-only player capture helper is now installed using the cockpit's
current-aircraft interface. Its offline Lua/loading/lifecycle checks pass. The
first steady run captured 235 valid native samples: core RPM agrees with Export,
fan/power values are present, and aircraft identity/timing association passes.
The full labeled run also passed: 2,039 samples over 101.905 s, measured fan/power
values above one, and exact equality between the two captured power getters.
A separate **DCSRecorder-Native-Engine-Playback.miz** is installed to replay the
measured core/fan/power values through guarded getters and stock DCS sound.
Offline checks pass; installation verified 10 hashes and 88 protected files
unchanged. Its first live run passed: 132,496 Sound.dll overrides across all six
channels matched the recording within 1.20e-7, both power consumers were reached,
and the original getters restored. The user found the sounds good and accurate.
No afterburner visual appeared; this isolated test omitted nozzle/flame writes.
Combine the accepted engine-parameter sound path and captured appearance on one
clock before integrating with recorded motion and the normal recording workflow.
See the [accepted native sound test](../experiments/efm-ownership/results/native-engine-playback-2026-09-27/README.md).
A separate **DCSRecorder-Engine-Combined-Playback.miz** now combines the six native
engine parameters and four captured nozzle/flame arguments on one clock. The
shared getter/animation boundary, source alignment and mission checks pass;
installation verified 10 hashes and 99 protected files unchanged. The user
accepted combined visuals and sound. Live traces confirm 132,366 sound overrides
and 40,736 appearance records matched the shared tape. The session stopped 85 ms
before tape end in the retained trace; the user subsequently confirmed automatic
completion as verified. That manual confirmation closes the combined completion
gate without changing the earlier trace's scope.
The version-three workflow is now installed: motion, surfaces, nozzle/flame
arguments and native engine parameters share one playback clock. New practice
missions save native timestamps and all eight raw getter values; conversion
aligns the six playback parameters to motion. The companion labels new takes
**Motion + surfaces + engines** and uses a separate engine-capable staged module.
Nineteen companion tests and five relevant native/mission checks pass. Following
the mission/Export ID correction, the user successfully recorded and replayed
the 31.98-second, 1,600-sample version-three flight named **Test** through the app
and reported "Worked great!" The saved data passes conversion, the regenerated
tape matches the activated tape, and the live mission reached `COMPLETE`.
See the [workflow integration record](../experiments/efm-ownership/results/engine-workflow-2026-09-27/README.md).
See the
[combined engine test](../experiments/efm-ownership/results/combined-engine-playback-2026-09-27/README.md).
See the [native capture record](../experiments/efm-ownership/results/native-engine-capture-2026-09-27/README.md).
See the [native RPM test](../experiments/efm-ownership/results/native-rpm-2026-09-27/README.md) and
[routing diagnosis](../experiments/efm-ownership/results/sound-routing-2026-09-27/README.md).

Afterburners, takeoff/landing and ground staging are explicitly deferred from the
completed first app workflow. They remain required for the broader single-aircraft
milestone; their existing tickets stay open.

## Placement and state design

The user wants to choose each aircraft's ground or airborne starting location,
including side-by-side ramp arrangements retained as flights are layered. Fixed
trail spacing serves the present airborne workflow. Decide how deliberate relocation
transforms the entire recorded path, especially near terrain; preserve original
placement by default. This is not authorization to implement multiple aircraft now.

Save a complete initial snapshot of supported state, not only subsequent changes.
If later-start/trim controls are eventually added, reconstruct both pose and state
at that timestamp. Hold them until the playback clock starts. Test first taxi motion,
contact and mission restart instead of accepting a later visual approximation.

Cross-aircraft support should reuse the motion controller with tested per-type
registration, model/livery dependencies and state mappings. A Hornet demonstration
does not establish F-16 or F-15 support. Preserve exact module/variant identity.

## Present limits and unresolved decisions

The tested configuration is DCS 2.9.29.27468, Hornet/Blue Angels, Caucasus, zero wind,
airborne, nearly level at the start, 5–300 seconds and 70–260 m/s. Altitude and rate
caps were removed from staged playback. Finite-data, continuity, object ownership
and build-signature checks remain. The implementation still uses private,
build-specific native access; another DCS update is not automatically compatible.

Product-wide position/attitude/timing tolerances remain to be agreed from actual
close-formation results. Current engineering measurements are not universal fidelity
guarantees. Decide behavior after impacts or wake disturbances using physical evidence.
Portable distribution and broader flight/aircraft state remain unfinished.
