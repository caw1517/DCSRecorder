# Roadmap: complete one-aircraft playback first

Updated 26 September 2026. The [GitHub map](https://github.com/caw1517/DCSRecorder/issues/1)
is the issue-tracking entry point.

## Current milestone

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
| [Visual and engine state](https://github.com/caw1517/DCSRecorder/issues/6) | The user visually accepted combined version-two motion and gear/flap/control-surface playback, including stabilators. Continuous afterburner appearance remains an acknowledged engine-state gap. Retain integrated numerical/lifecycle checks; next add suspension compression, wheel spin, canopy, smoke, lights, separate engine nozzles, afterburner effects and sound. Coordinate suspension/wheel evidence with ground-contact tests. Speed brake already follows the tape. |
| [Exact starting position and state](https://github.com/caw1517/DCSRecorder/issues/11) | Extend accepted exact airborne initialization to stationary hot ground starts, original parking/demo spots and synchronized aircraft state. |
| [Flight envelope through takeoff and landing](https://github.com/caw1517/DCSRecorder/issues/7) | Validate ground transitions, low passes, hard maneuvers and longer full-demo durations. Remove remaining speed/duration restrictions as the corresponding behavior is implemented and verified. |
| [Essential physical interactions](https://github.com/caw1517/DCSRecorder/issues/3) | Ground contact, collision/damage and wake in both directions; decide how physical disturbances affect the recorded path. |
| [Installation and compatibility](https://github.com/caw1517/DCSRecorder/issues/8) | Portable setup, local asset preparation, supported-build maintenance, rollback and performance. |
| [Layered playback](https://github.com/caw1517/DCSRecorder/issues/9) | After one-aircraft gates: independently identified takes sharing a playback clock while another is recorded. Preserve originals and verify timing/performance. |
| [Recorded lead calls](https://github.com/caw1517/DCSRecorder/issues/10) | Research audio capture/delivery, onset/latency, drift, pause alignment and synchronization. Ordering relative to layers remains open. |

Before expanding engine work, verify a fresh application take after the
[missing-gear diagnosis](../experiments/efm-ownership/results/application-gear-2026-09-27/README.md).
The affected take used the legacy format without gear channels; the installed
old practice mission reproduces that omission. The app now identifies motion-only
takes and generates clearly named exterior-capable practice missions. Fresh live
capture/playback acceptance remains pending.

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
