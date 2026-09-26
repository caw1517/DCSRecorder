# Independent aircraft control: EFM follow-up

Research date: 2026-09-23. Follow-up to [DCS precise playback feasibility](dcs-playback-feasibility.md), focused on issue #2. No simulator experiment, mod installation, or runtime change was performed.

## Finding

**A current installed EFM API exists, but independent playback-aircraft ownership remains unproved.** Its documented continuous actuator returns forces and moments; it does not supply a continuous aircraft pose setter. The smallest useful experiment is therefore to establish whether an EFM actually runs for an unoccupied aircraft while the user flies another aircraft. Writing a trajectory controller before this check risks solving control for the user's aircraft only.

Issue #2 should remain open. Source inspection narrows the experiment; it does not establish impossibility or faithful layered playback.

## Direct evidence

The installed [autoupdate.cfg](<D:/DCS World/autoupdate.cfg>) reports DCS **2.9.29.27278**, timestamp `20260826-084519`. Unlike the previous review's third-party copy, the following evidence comes directly from this installation's bundled API:

- [wHumanCustomPhysicsAPI.h](<D:/DCS World/API/include/FM/wHumanCustomPhysicsAPI.h:46>) describes `ed_fm_simulate(double dt)` as a per-step callback whose results are subsequently collected as forces and moments. The force and moment signatures return their components by reference.
- [Current-state callback](<D:/DCS World/API/include/FM/wHumanCustomPhysicsAPI.h:192>) supplies acceleration, velocity, position, angular quantities, and orientation quaternion to the EFM by value. It is an observation/input callback, not a write interface into DCS's rigid-body state.
- [Balance callback](<D:/DCS World/API/include/FM/wHumanCustomPhysicsAPI.h:935>) can return velocity and attitude changes, but its documentation places it after airborne hot start. Its parameters contain no position output. No documented basis was found for using it as a continuously invoked pose actuator.
- The examined simulate/state/force/moment signatures contain no unit ID or per-aircraft context pointer. The supplied [ExternalFMTemplate](<D:/DCS World/API/ExternalFMTemplate/ED_FM_Template/ED_FM_Template.cpp:10>) keeps force, moment, velocity, fuel, and control state in file-scope variables. **Inference:** these examples do not demonstrate independent same-DLL instances for multiple aircraft. Neither their shape nor global state proves the engine cannot isolate instances by some other mechanism.

For reproducibility, the local header's SHA-256 is `55C5380E0A8D85403E6890F8FC7398E29FFBA21C726BAC2F99D85AD8B0FB0631`. Local file links require this installation; the older [public integration-header copy](https://github.com/RagnarDa/F-16Demo/blob/master/FlightModel/F_16Demo/include/FM/wHumanCustomPhysicsAPI.h) provides a portable comparison, not the authority for current-build claims.

## What primary web sources add

ED's [General Flight Model article, 2021-12-03](https://www.digitalcombatsimulator.com/es/news/2021-12-03/) describes separate development paths for AI and human flight models and explains why simply extending PFM/AFM to AI was undesirable. It describes planned GFM work, not a public third-party AI EFM registration interface. It must not be read as confirmation that every current AI aircraft still uses SFM, or that GFM shipped on its announced schedule.

The Community A-4E's own [entry.lua](https://github.com/heclak/community-a4e-c/blob/master/A-4E-C/entry.lua) loads its EFM and passes an FM table to `make_flyable`; its separate [aircraft definition](https://github.com/heclak/community-a4e-c/blob/master/A-4E-C/A-4E-C.lua) contains a simplified aerodynamic model. These demonstrate real mod integration, but do not demonstrate EFM callbacks running for an unoccupied playback aircraft. Mod availability alone cannot answer the ownership question.

The [acEFM maintainer's documentation](https://github.com/Zaretto/acEFM) describes mapping pilot commands received through `ed_fm_set_command` to JSBSim properties and exposing a runtime property inspector. This is a plausible development aid for controlled inputs. Its documented standalone JSBSim test harness explicitly tests outside the DCS bridge. Passing such tests would not establish independent aircraft control inside DCS. Nor does a writable JSBSim property establish that changing it teleports DCS's aircraft.

## Two hypotheses to discriminate

1. **Single-process EFM route:** a custom aircraft's EFM continues running when it is AI/unoccupied and can independently supply forces while the user occupies another aircraft. Unconfirmed. An AI aircraft following its normal route is not evidence for this hypothesis.
2. **Separate local-client route:** a second actual DCS client occupies the playback aircraft, receives synthetic controls or runs its EFM, and shares the mission with the user's client. Conceptually this separates control ownership, but client coexistence, account/module requirements, resource cost, synchronization, and physical behavior are untested. A dedicated server running without graphics does not itself demonstrate a controllable human aircraft or multiple EFM instances. This remains a fallback experiment, not an established architecture.

Neither hypothesis supplies exact trajectory reproduction automatically. With forces or stick inputs, tracking a position-and-attitude timeline becomes a feedback-control problem. That is an engineering inference from the actuator type. Fidelity, disturbance response, contact, and wake remain separate measured gates.

## Smallest discriminating experiment

Use an isolated test mod and mission, not modifications to a paid module or the main installation. Record the build, mod revision, callback log, and mission observations.

1. **Positive control:** occupy the test mod as the player. Log callback counts, accumulated simulation `dt`, supplied world position, and supplied quaternion. Confirm `ed_fm_simulate` is repeatedly called. After a fixed simulation interval, add one small, bounded, distinctive roll-moment pulse to its otherwise functioning model and measure the response. A DLL-load log alone is insufficient.
2. **Ownership test:** restart with the same mod as the only unoccupied AI aircraft and the user in a stock aircraft. Repeat the pulse and logging. Correlate callback positions with the test aircraft's separately observed position. Confirm the user retains normal control. Callback activity from the user's aircraft must not be mistaken for the target.
3. **Interpretation:** if the positive control works but the AI run has no repeated EFM callbacks, this tested configuration fails the single-process EFM route. If callbacks exist without a target-correlated motion response, independent actuation remains unproved. If both occur, the gate passes for one target only.
4. **Only after a pass:** repeat with two same-type test aircraft at clearly separated starting positions and different intended pulse times. Establish separate state and actuation before writing full playback. A shared callback stream without identifiable ownership does not pass.
5. **Fallback after failure:** test a second occupied local client only if a supported client setup is available. First prove a synthetic roll input affects only that client’s aircraft and is observed by the user's client. Then assess deployment cost and synchronization before implementing trajectory tracking.

Once ownership passes, use the synthetic roll/turn/loop timeline and independent telemetry described in the earlier report. Do not infer collision or wake preservation from a successful pulse. No runtime results exist yet, and none of the proposed steps is a completed validation.
