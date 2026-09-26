# DCS precise playback feasibility

Research date: 2026-09-23. Scope: single-player DCS World only. The product requires recorded flights reproduced as independently visible playback aircraft while the user flies and records another aircraft. Loops, rolls, inverted flight, tight turns, takeoff, and landing remain requirements. Multiplayer is excluded permanently.

Scope clarification during research: the user approved synthetic-path testing first, accepts mods or a local headless server with synthetic input, and requires physical interactions including collisions and wake. The experience must remain solo; a local server may be an implementation detail, not a multiplayer product. A visual-only ghost is insufficient.

## Provisional verdict

**Recording is supported in principle; precise layered playback remains unproven.** The decisive question is whether an integration can continuously control a separate aircraft's position and orientation while the player retains their own aircraft. An AI route-following demonstration would not establish this.

The reviewed public interfaces do not establish a supported way to impose an arbitrary time-indexed pose on a non-player aircraft. This is a finding about the examined documentation, **not proof that DCS cannot do it**. No simulator experiment was performed. ED's scripting introduction explicitly identifies its documentation as applying to DCS World 1.2.6, so a current-installation API inspection is necessary before a definitive verdict. [ED scripting introduction](https://www.digitalcombatsimulator.com/en/support/faq/1252/)

## Evidence and implications

| Surface | Documented evidence | Implication / remaining uncertainty |
| --- | --- | --- |
| Mission scripting: observation | `Object.getPosition()` returns a `Position3`; `getVelocity()` returns velocity. The published Object methods expose getters, existence/destruction, and descriptors, with no pose setter listed. [ED Object reference](https://www.digitalcombatsimulator.com/en/support/faq/1259/) | Reading an aircraft's movement is feasible. A setter must be independently demonstrated; do not invent `Unit:setPosition()` or assume a community wrapper adds engine capability. |
| Pose and time representation | `Position3` contains position and three orientation basis vectors. Model time drives simulation and can stop or change rate. [ED types reference](https://www.digitalcombatsimulator.com/en/support/faq/1256/) | Store simulation timestamps and complete orientation. Proposed implementation: use quaternions for interpolation, with coordinate conventions validated against observed DCS poses. |
| Mission scripting: actuation | Controller supports tasks, commands, options, and waypoint routes. The route model expresses destinations, speed and arrival timing; it does not document per-sample aircraft attitude control. [ED Controller reference](https://www.digitalcombatsimulator.com/en/support/faq/1267/) | Tasking an AI pilot is not evidence of faithful playback. A roll task, even if available in the current build, would only prove the AI can perform a maneuver. |
| Export recording | The maintainer's `dcs-export-core` implementation reads `LoGetSelfData()` and `LoGetModelTime()`. [Project source](https://github.com/jboecker/dcs-export-core/blob/master/DcsExportCore/Protocol.lua) | A real exporter demonstrates player-state/time access. This source does not establish write access to another aircraft or all animation channels. Validate full pose and sampling in the installed build. |
| External flight model (EFM) | The published F-16Demo integration header describes simulation results returned as forces/moments. Its `ed_fm_set_current_state` callback supplies the flight model with current state. [Integration header](https://github.com/RagnarDa/F-16Demo/blob/master/FlightModel/F_16Demo/include/FM/wHumanCustomPhysicsAPI.h) | The callback name is not a pose-write API. A feedback controller using forces is a speculative alternative, not exact replay. Whether this interface operates for independently controlled non-player instances must be proved first. This is an integration project's copy of the API, not a promise about current SDK availability. |

Mission scripts run in an isolated environment. An Export API name cannot simply be assumed callable from a mission script, or vice versa. [ED Lua environment](https://www.digitalcombatsimulator.com/en/support/faq/1253/)

The same EFM header exposes `ed_fm_make_balance` with mutable dynamic values and yaw/pitch/roll, but describes it as an initialization callback after an airborne hot start. Its signature has no position output. This is not evidence of continuous kinematic playback control. No own-source mod demonstrating supported continuous non-player pose override was established in this bounded review; EFM investigation remains open. [EFM balance declaration](https://github.com/RagnarDa/F-16Demo/blob/master/FlightModel/F_16Demo/include/FM/wHumanCustomPhysicsAPI.h#L410)

## First proof of concept: actuator gate

### Bounded follow-up: server, synthetic inputs, and native replay

- **Headless hosting exists.** ED distributes a dedicated server that runs without 3D graphics or sound and defaults to server/no-render launch options. This verifies the infrastructure option, not an aircraft actuator or a bot pilot. The source does not establish that a headless server can instantiate multiple human flight-model clients or accept per-aircraft stick input. [ED dedicated server](https://www.digitalcombatsimulator.com/en/downloads/world/server/)
- **External command transport exists.** The `dcs-udp-set` maintainer describes a UDP listener emitting `LoSetCommand`, motivated by mode switching for FC3 aircraft. That establishes a real command-injection integration, but not independent control of arbitrary AI aircraft or six-axis pose writes. Synthetic inputs still require proof of target selection, physics behavior, and trajectory accuracy. [Maintainer repository](https://github.com/RafaPolit/dcs-udp-set)
- **RPC does not by itself supply missing actuation.** DCS-gRPC connects external clients to a running mission. Its reviewed Unit service includes position/transform getters, emission control, destruction, and other queries, but no transform setter. It may be useful for measurement and test orchestration; wrapping an API is not evidence of new engine capabilities. [Project](https://github.com/DCS-gRPC/rust-server), [Unit service source](https://github.com/DCS-gRPC/rust-server/blob/main/protos/dcs/unit/v0/unit.proto)
- **Native replay needs its own demonstration.** ED's changelog documents fixes for track saving and replay, establishing the maintained native mechanism. It does not establish independent aircraft replay inside a live mission or merging recorded flights. This review does not rely on community assertions that all track data are only control inputs. [ED release changelog](https://www.digitalcombatsimulator.com/en/news/changelog/release/?PAGEN_2=3)

These sources leave issue [#2](https://github.com/caw1517/DCSRecorder/issues/2) open. Next evidence needed is a current-runtime actuation demonstration or an authoritative SDK answer, then measurements against the physical-participation gates. No branch exists and no simulator experiment has been run.

### Experiment

**Do not begin with a recorder UI.** First identify and demonstrate a supported actuator. Inspect current installed Lua/API documentation, examples, and exposed functions read-only; record the DCS build, aircraft type, and integration environment. Investigate a documented SDK/custom visual entity route if ordinary aircraft APIs do not provide it. Do not assume private SDK access or a custom entity is available.

The proposed test, once an actuator exists:

1. Create one player aircraft and one persistent playback aircraft in a simple single-player mission, initially high above terrain.
2. Drive the playback aircraft along a synthetic timeline: straight segment, constant-rate full roll, banked turn, full vertical loop, inverted segment. Generate pose from time, independently of the current frame rate. Use a smooth trajectory rather than discontinuous attitude steps.
3. Sample actual position and orientation separately from the requested pose. Report maximum and RMS position error, angular error, timing error, and frame-time cost. Also check for snapping, respawning, drift, and AI overriding the requested motion.
4. Repeat at different frame rates and through pause/resume. Add a second playback aircraft on the same clock. Confirm the player can still fly independently alongside both.
5. Only after that passes, add a short recorded flight. Then test takeoff, landing, touchdown, and ground roll explicitly; an airborne test does not establish ground-contact behavior. Add gear, flaps, control surfaces, smoke, lights, and other visual channels as separate fidelity checks.
6. Treat physical participation as an independent pass/fail gate: establish collision geometry/damage and wake effects on the user aircraft using controlled comparisons. Exact path playback must coexist with these interactions. Specify whether the playback aircraft itself deviates or is damaged after contact; blindly forcing pose back onto the timeline could conflict with that behavior. A rendered model following a path does not prove this requirement.

Proposed initial engineering targets, **not user-approved acceptance criteria**: below 0.25 m position error, 0.5 degrees orientation error, and one rendered frame of phase error, with no persistent drift over five minutes. Tight formation may demand stricter limits; retain measured results rather than declaring success solely from video. Finite sampling/interpolation requires an explicit meaning of “one-to-one.”

If no viable actuator is found, the POC outcome is a documented capability gap and a precise SDK/vendor question: can a supported interface drive several non-player aircraft or suitable visual entities by timestamped position, orientation, and animation state while a single-player aircraft remains user-controlled? Do not substitute approximate waypoint playback and call the requirement satisfied.

## Unresolved questions

- Does the current DCS build expose a relevant supported pose setter or replay-entity interface absent from the older public documentation?
- Can a custom entity or EFM route support multiple independently driven non-player instances? Does it preserve aircraft appearance and animations?
- Can native track machinery be used for independent layered entities? No reviewed primary source establishes this; native replay existence alone is insufficient evidence.
- Can playback stay visually faithful through ground contact without the simulation fighting the imposed trajectory?
- Can a mod or local headless-server approach drive a physically participating aircraft with sufficient accuracy? Synthetic stick/throttle inputs imply a trajectory-following controller unless a direct state interface is established; exact motion and disturbance response require measured validation. No supported mechanism was established in this review.
- Which visual channels are observable and writable for the selected aircraft? Movement fidelity does not automatically include gear, smoke, surfaces, or lights.

## Research limitations

This is source research and a proposed experiment, not a working prototype or a final feasibility verdict. Official documentation is old and community integration source may lag current builds. No runtime measurements were taken. The workspace is not Git-initialized (`git status` reports that it is not a repository), so no research branch or commit was created. Only this note was written by the research delegate.
