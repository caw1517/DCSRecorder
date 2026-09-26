# Roadmap: complete one-aircraft playback first

Updated 26 September 2026. The [GitHub map](https://github.com/caw1517/DCSRecorder/issues/1)
is the issue-tracking entry point. This document records the current priorities;
historical experiment instructions do not override them.

## Decisions so far

- One player, one account, one DCS process in the demonstrated setup. No
  multiplayer product or second-account workaround.
- Finish one-aircraft playback before implementing layers.
- Reproduce measured flight motion; do not recreate it by guessing pilot inputs.
- Keep missions wind-free for the present supported baseline. Wind compensation
  is not a prerequisite requested by the user.
- A successful airborne prototype exists. Its build-specific integration and
  remaining physics requirements prevent a finished-product feasibility claim.
- Voice calls synchronized to the flight belong in the future roadmap. Their
  capture/playback interfaces and attainable timing accuracy need investigation.
- A chosen playback start must reproduce its original location, heading,
  attitude, movement and supported aircraft state together. Ground starts from
  a specific parking/demo spot, including after engine startup, are an explicit
  requirement. Current airborne acquisition/translation is a prototype convenience.

## Companion application and exact starts

Proposed workflow: fly and record in DCS, select a saved take in a companion app,
generate a playback mission, then load it in DCS. The existing extraction,
validation and mission tools provide a starting point; a finished app does not
exist. Issue #5 should resolve the app's scope and division of responsibilities
before choosing a UI/framework. The in-DCS component still samples and controls
aircraft; the external app manages takes and prepares files/missions.

Exact start means location and state at **the same recorded moment**: for example,
the original parking spot after engines are running, with matching gear, flaps,
canopy, brake, lights and supported engine/animation values. Save an initial state
snapshot, not only subsequent changes. If selecting a later timestamp is offered,
reconstruct its state too. Initialize and hold the state until playback starts,
without spending the opening seconds sliding or blending into alignment. Verify
original mission/terrain context, parking/contact placement and timing. Exact
cockpit-system restoration and engine internals are distinct from the external
state we can actually observe/control; capability gaps must remain explicit.

The current five-second lead-in, two-second attitude acquisition, capture-relative
translation and airborne-only guards cannot satisfy ground starts. Coordinate
exact-start work with #6 state fidelity, #7 ground transitions and #3 physics.
Relocating playback could be a separate deliberate mode; preserving the original
start is the baseline requirement.

Cross-aircraft ambition is one reusable motion controller plus tested setup and
state mappings for each type. The current Hornet registration is custom-built
from installed assets. Automatically switching between F/A-18C, F-16 and a chosen
F-15 variant is not implemented or validated. Save precise module/type/livery
identity and reject unsupported combinations rather than substituting. This
belongs to #6 and #8 as support grows.

## Sequence and completion gates

| Stage | Status | What completion means |
| --- | --- | --- |
| Independent motion and a real take | Demonstrated in the current setup | Retain the accepted short-flight baseline and repeatable measurements. |
| Reliable single-aircraft workflow | Next | Record, stop, retain, select and replay a take without manual log handling or mismatched packages; clear errors and safe end/restart behavior. Validate repeated/longer takes, pause/resume, timing, positioning and different frame rates. |
| Faithful aircraft appearance and engine state | Before single-aircraft milestone is complete | Establish which required state can be captured and replayed: recorded aircraft/livery, gear, flaps, surfaces, brake, smoke, lights, engine RPM/nozzles/afterburner and associated sound. Verify rather than infer engine effects from trajectory. |
| Flight envelope and physical participation | Before claiming full flight playback | Broaden guards only with evidence. Test stronger maneuvers and inverted flight, then taxi/takeoff/touchdown/rollout. Test collision/damage and wake in both directions. Decide how interruption or physical disturbance affects the recorded path. |
| Repeatable installation and compatibility | Before calling it a usable product | Remove developer-machine assumptions, validate build compatibility, fail clearly on unsupported DCS versions, package safely and support rollback. Measure overhead and repeatability. |
| Layered playback | Deferred until one-aircraft milestone | Replay an existing take while recording a new one, preserve originals and timing, then replay multiple independently identified aircraft. Test shared-clock alignment and performance. |
| Synchronized recorded voice | Deferred; ordering relative to layers remains open | Capture lead calls while flying and replay them against the same flight clock; validate onset alignment, latency, drift, pauses and any offset/restart controls. No numerical sync guarantee is established yet. |

The next implementation step is the single-aircraft take workflow and repeatable
regression runs. Aircraft state and physics then deepen fidelity within that same
single-aircraft scope. General aircraft compatibility is not established by the
TF-51D and Hornet experiments; define a tested support list as capability grows.

## GitHub tracking

Completed: [independent control #2](https://github.com/caw1517/DCSRecorder/issues/2)
and [initial proof of concept #4](https://github.com/caw1517/DCSRecorder/issues/4).

1. [Reliable single-aircraft workflow #5](https://github.com/caw1517/DCSRecorder/issues/5).
   Plan its start contract with [exact position and state #11](https://github.com/caw1517/DCSRecorder/issues/11).
2. [Visual and engine state #6](https://github.com/caw1517/DCSRecorder/issues/6).
3. [Flight envelope and takeoff/landing #7](https://github.com/caw1517/DCSRecorder/issues/7),
   with [essential physical interactions #3](https://github.com/caw1517/DCSRecorder/issues/3).
4. [Portable setup and compatibility #8](https://github.com/caw1517/DCSRecorder/issues/8).
5. [Layered playback #9](https://github.com/caw1517/DCSRecorder/issues/9), deferred
   behind the single-aircraft gates above.
6. [Synchronized lead-call voice #10](https://github.com/caw1517/DCSRecorder/issues/10),
   deferred research; ordering relative to layers remains open.

## Current evidence

The first real take is 38.78 seconds at 50 samples/second. The initial replay
showed native velocity being redirected along the nose, despite the recorded
aircraft's angle of attack. Restoring linear/angular motion immediately before
integration reduced mean inter-update position correction by about 90%, from
18.84 to 1.88 cm, in the matched comparison window. The user reported “SO much
better.” Follow-up process 45780 passed the recorded-velocity and correction
checks; all 1,940 restorations succeeded and the override restored on release.

This establishes the short calm-air case. It does not prove zero jitter,
pixel-perfect rendering, collision/wake fidelity, all maneuvers, long-run sync,
pause behavior in DCS, or compatibility with another game update.

Evidence: [recorded-flight implementation](research/dcs-recorded-flight-prototype.md),
[jitter diagnosis and follow-up](../experiments/efm-ownership/results/recorded-jitter-2026-09-26/README.md).

## Open decisions and risks

- Should playback interrupt, deviate or stop after impact/damage? The user has
  deferred that decision until physical-interaction evidence exists.
- Set practical path/timing tolerances using close-formation tests. Existing
  telemetry thresholds are engineering checks, not a user-approved fidelity spec.
- Choose clear start/end, reset and absolute/relative placement behavior.
- Determine which exterior/engine channels are available for each supported type.
- Establish whether the private native integration can be maintained reliably
  across supported DCS builds. Current success is local, not a compatibility promise.
- Investigate microphone capture and DCS audio delivery later. Use simulation
  time as the synchronization reference; map real-time audio samples explicitly,
  especially across pauses. Do not promise “perfect sync” before measurements.
