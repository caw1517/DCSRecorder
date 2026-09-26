# Dynamic EFM generation for one-player layered playback

Research date: 2026-09-23. Constraint: one player and one account; an architecture requiring another account is excluded. This is an assessment, not a new simulator result.

## Answer

An application can generate a flight-model DLL containing a recorded input timeline. It could instead compile one playback-capable DLL once and supply the timeline as data. Neither arrangement, by itself, establishes that DCS will execute that DLL for an unoccupied playback aircraft while the user flies another aircraft. That execution/ownership boundary is the unresolved gate.

This distinction follows from our direct [AI comparison](../../experiments/efm-ownership/results/ai-2026-09-23/README.md): the target spawned and moved for 23.7 seconds, but the tested registration produced no new callback file or observed DLL load. The same DLL had passed the [player positive control](../../experiments/efm-ownership/results/player-2026-09-23-telemetry/README.md). The result rejects that configuration, not all possible integrations.

## What the primary sources establish

- The [acEFM maintainer's repository](https://github.com/Zaretto/acEFM) documents a single EFM DLL configured by external XML and a runtime property inspector. It also maps incoming pilot commands to flight-model properties. This demonstrates that configurable and externally influenced EFM logic is practical. It does **not** demonstrate an unoccupied aircraft using that EFM alongside the player. Its standalone scripted tests explicitly run outside the DCS bridge.
- The AH-6J EFM demo's own [entry.lua](https://github.com/CrudeCoder1/Helicopter-EFM-Demo/blob/main/entry.lua) declares the `AH6J` binary and supplies its EFM configuration to `make_flyable`. This is another real registration example, but contains no demonstrated independent AI EFM scheduler. The project's [README](https://github.com/CrudeCoder1/Helicopter-EFM-Demo) includes both EFM development and AI speed changes; coexistence in a mod is not evidence that AI executes the EFM.
- The [Basic EFM template author's release](https://forum.dcs.world/topic/345975-basic-efm-template-mod-source-code/) provides source and a prebuilt DLL intended for adaptation. Its [earlier integration instructions](https://forum.dcs.world/topic/268698-wip-custom-flight-model-mod-version-7-source-code/page/2/) likewise register a binary through `make_flyable`. Generating a new DLL is supported by these examples; turning it into another independently simulated body is not demonstrated there.

A targeted search of these author-owned implementations and DCS forum material found no primary example establishing custom EFM callbacks for an unoccupied AI aircraft alongside a different player aircraft. This is a bounded negative search result, not proof that an undocumented or alternative integration cannot exist.

## Two meanings of injection

1. **Generate/install an aircraft mod:** compile the DLL, package it, register it with the normal mod entry, then let DCS load it. This changes the code available to DCS. Our failed ownership test remains applicable until a different registration or lifecycle is shown to execute it for the playback aircraft.
2. **Modify the running engine's behavior:** introduce an integration that schedules another flight-model instance and routes its output to a particular aircraft. This could address the missing mechanism in principle, but is a separate engine-integration investigation. Merely loading a DLL or invoking its functions in a helper application does not demonstrate that DCS consumes its output for that target. No working mechanism was established or implemented in this research.

Engineering inference: embedding recorded controls also cannot guarantee the recorded trajectory. Reproduction depends on the same initial state, physics, environment, timing, and relevant system state. A replacement template EFM is not automatically the flight model of the aircraft originally recorded. Exact playback therefore still needs measured trajectory error and potentially feedback or an independently validated pose actuator.

## Concrete next gate

Before writing a per-flight compiler or recorder, identify one specific, evidence-backed candidate for binding custom physics or pose output to a nonplayer aircraft in the same simulation. Inspect registration and lifecycle interfaces first; require an actual candidate entry point or reproducible example before asking for another simulator run.

For any candidate, reuse the bounded moment-pulse experiment: one stock player aircraft, one unoccupied target, distinct target-correlated callback state, and independent mission telemetry. Passing requires repeated callbacks and the target's scheduled response while the player's controls continue working. A DLL load, standalone test, or ordinary AI waypoint motion is insufficient. A candidate that only works while occupying the target fails this requirement.

If no candidate survives that inspection, report the current one-player actuator gate as unresolved. Preserve the dynamic-EFM idea as a possible implementation of playback logic once ownership exists; do not represent it as having solved ownership. Multiple playback aircraft, trajectory fidelity, contact, and wake remain subsequent gates.
