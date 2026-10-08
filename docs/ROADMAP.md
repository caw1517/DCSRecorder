# Roadmap: complete one-aircraft playback first

Updated 30 September 2026. The [GitHub map](https://github.com/caw1517/DCSRecorder/issues/1)
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

The normal airborne companion workflow is accepted on DCS 2.9.30.28536 after
the compatibility update and capture-batching fix. The user confirmed working
gear, spoilers and smoke, fluid playback and smooth formation flying; a
57.24-second recording validates and playback completion is logged. See the
[live acceptance checkpoint](../experiments/efm-ownership/results/held-start-2026-09-30/README.md).
The installed opt-in profile remains selected. The bounded thirty-second
[airborne held-staging control](../experiments/efm-ownership/results/held-staging-2026-09-30/README.md)
is now accepted: the real lead remained still, the scene witness kept flying,
and the user confirmed steady engine sound. Complete initial-snapshot coverage,
countdown/release, ground staging and ground-to-ground work below remain open.

[Visual and engine-state fidelity](https://github.com/caw1517/DCSRecorder/issues/6)
is accepted for the documented Hornet V1 scope. Next:
[Complete Hornet mission setup and hot-start parking-to-parking playback](https://github.com/caw1517/DCSRecorder/issues/11).
The user confirmed DCS Mission Editor authoring, original recorded placement,
visible held staging, and parked completion with engines running. This remains
one-aircraft playback; layers and additional aircraft types follow later.

The current wayfinder pass defines the implementation route and acceptance
contract. The user accepted
[Choose Mission Editor integration for authored recording and playback missions](https://github.com/caw1517/DCSRecorder/issues/14#issuecomment-5900259507):
Mission Editor authoring, companion-prepared copies, saved mission revisions,
explicit review of updated scenes and refusal to relocate a recorded path.
[Choose a concise aircraft registration and compatibility strategy](https://github.com/caw1517/DCSRecorder/issues/16)
can be considered independently. The integration decision precedes
[Choose visible staging and parked completion for playback aircraft](https://github.com/caw1517/DCSRecorder/issues/15),
which precedes
[Agree on parking-to-parking validation and acceptance](https://github.com/caw1517/DCSRecorder/issues/17).
These are decision tickets; closing them does not establish implementation or
simulator acceptance. The GitHub map carries native sub-issues and blockers.

The user accepted the
[visible staging and parked completion lifecycle](https://github.com/caw1517/DCSRecorder/issues/15):
test the real playback aircraft held visibly at its complete initial snapshot,
release motion and supported state on one clock after the countdown, and retain
a validated hot parking endpoint. The surrounding mission keeps running; valid
non-parking endings remove the playback aircraft while the player's flight
continues. A stand-in is conditional on proving a seamless handoff. Failure
cleanup and full mission restart are part of the contract. The reviewed demo is
preserved on `codex/prototype-playback-lifecycle`; the issue resolution owns the
details and bounded experiments. Simulator implementation and evidence remain open.

The integration decision exposed two bounded follow-ups:
[Prove mission identity and edit detection across Mission Editor saves](https://github.com/caw1517/DCSRecorder/issues/18)
and [Define compatibility with authored triggers and aircraft tasks](https://github.com/caw1517/DCSRecorder/issues/19).
The latter follows the lifecycle decision. Both retain required evidence before
ground-operations completion. The reviewed throwaway prototype is captured on
`codex/prototype-mission-editor-workflow`; it is not production implementation.


The [single-aircraft record-to-replay workflow](https://github.com/caw1517/DCSRecorder/issues/5)
is implemented and accepted for the current airborne scope. The local companion
saves completed takes automatically, lists/renames/validates them and generates
practice/playback missions. The latest fast-roll take completed successfully after
removing prototype altitude/rate caps. The nose-jump fix remains active.

In the accepted airborne implementation, the player waits in Active Pause; F10
starts a three-second countdown. Actual
release/activation anchors playback. The lead receives the original first-sample
pose, velocity and speed brake without acquisition blending or translation; the
player starts approximately 150 feet behind. Completion removes the lead and
leaves the mission running. Restarting the mission replays the take. The agreed
ground milestone will replace removal after a parking-to-parking take with
parked completion; that behavior is not implemented by this planning update.

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
| [Complete Hornet mission setup and hot-start parking-to-parking playback](https://github.com/caw1517/DCSRecorder/issues/11) | Mission Editor integration, original authored placement, visible held staging, synchronized initial state, complete ground-to-ground playback, parked completion and concise aircraft registration. Preserve the measured speed-brake retention follow-up and coordinate the existing envelope/physics gates. |
| [Flight envelope through takeoff and landing](https://github.com/caw1517/DCSRecorder/issues/7) | Accepted 8 October 2026. See [Supported envelope](../README.md#supported-envelope) and the [envelope results](../experiments/efm-ownership/results/envelope-2026-10-07/README.md). The post-liftoff drift continues in [#37](https://github.com/caw1517/DCSRecorder/issues/37). |
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

The user will choose ground or airborne starting locations before recording in
DCS Mission Editor, along with trucks, scenery and visual reference objects.
Recording/playback preparation must preserve the authored scene. A companion
preparation step is acceptable where needed, but DCS Mission Editor is the
preferred authoring interface. Fixed trail spacing serves the current airborne
implementation, not the final authoring workflow.

Replay recordings at their original world coordinates. Deliberate relocation of
an existing flight is outside the current effort. Investigate prevention or
detection of edited placement mismatches and decide refusal versus warning from
evidence. Examples of six, twelve or forty aircraft describe possible future
arrangements, not a capacity guarantee or authorization to implement layers now.

Adding aircraft creates a new authored mission revision. Existing takes retain
their saved scenes and original paths; a reviewed compatible expanded scene can
also be selected. A four-aircraft mission can therefore grow to seven without
discarding earlier takes. Bind recordings to stable per-aircraft association,
not array order or aircraft count. New aircraft can be recording subjects or the
player alongside one existing take; simultaneous playback remains later work.

Before release, aircraft must be visible at their intended starting positions
while the user looks around from a held position. Ground and airborne staging
are required; taxiing or flying into position before release is unnecessary for
V1. A temporary stand-in is only an implementation option. Whole-mission pause
semantics and behavior for incomplete or airborne-ending takes remain decisions.
After a parking-to-parking take, keep the playback aircraft parked with engines
running and supported final state held until mission exit or restart.

Reduce Mission Editor clutter from experimental and schema-specific aircraft
registrations while preserving or explicitly migrating old recordings and
missions. Inventory and a migration/rollback plan precede installed-file cleanup.
Startup/shutdown are V2; other aircraft and layered playback remain later work.

Save a complete initial snapshot of supported state, not only subsequent changes.
If later-start/trim controls are eventually added, reconstruct both pose and state
at that timestamp. Hold them until the playback clock starts. Test first taxi motion,
contact and mission restart instead of accepting a later visual approximation.

Cross-aircraft support should reuse the motion controller with tested per-type
registration, model/livery dependencies and state mappings. A Hornet demonstration
does not establish F-16 or F-15 support. Preserve exact module/variant identity.

## Present limits and unresolved decisions

The demonstrated envelope is in the [README](../README.md#supported-envelope), accepted under [Validate the single-aircraft flight envelope through takeoff and landing](https://github.com/caw1517/DCSRecorder/issues/7) on 8 October 2026. The old 5–300 s and 70–260 m/s bounds are retired. Finite-data, continuity, object ownership and build-signature checks remain. The implementation still uses private, build-specific native access; another DCS update is not automatically compatible.

Position, attitude, velocity, timing and state limits were agreed in [#28](https://github.com/caw1517/DCSRecorder/issues/28). Decide behavior after impacts or wake disturbances using physical evidence.
Portable distribution and broader flight/aircraft state remain unfinished.
