# Installed DCS API inspection

Inspected 2026-09-23, read-only. No simulator experiment was run and no simulator files were changed.

## Build and available evidence

The local installation at `D:/DCS World` reports version **2.9.29.27278**, timestamp `20260826-084519`, in [autoupdate.cfg](<D:/DCS World/autoupdate.cfg>). This is the installed build, not a claim about the latest release.

The installation includes an EFM template and headers under `API/ExternalFMTemplate` and `API/include/FM`. This removes the earlier uncertainty about access to a local SDK sample; it does not establish that the sample works for AI aircraft.

## Findings

- [Export.lua](<D:/DCS World/Scripts/Export.lua:844>) documents a camera pose setter, followed by `LoSetCommand(command, value)` at line 854 and joystick pitch/roll/rudder/throttle commands. The documented command signature has no aircraft identifier. It does not establish independent targeting of a playback aircraft.
- [Sim_ControlAPI.md](<D:/DCS World/API/Sim_ControlAPI.md:418>) documents changing the local player's slot and forcing an existing player into a slot. These are slot operations, not documented creation of a synthetic pilot or per-aircraft control channels.
- [wHumanCustomPhysicsAPI.h](<D:/DCS World/API/include/FM/wHumanCustomPhysicsAPI.h:47>) describes simulation outputs as forces and moments. `ed_fm_set_current_state` receives state; it is not a pose setter. The balance callback at line 936 is documented after an airborne hot start, not as a continuous pose-control interface.
- [demosceneEnvironment.lua](<D:/DCS World/Scripts/DemoScenes/demosceneEnvironment.lua:98>) really does expose position and orientation setters through `ED_demosceneAPI`. Its use in [encyclopediaScene.lua](<D:/DCS World/Scripts/DemoScenes/encyclopediaScene.lua:1>) establishes a display-scene application, not a physically participating mission aircraft. This search result must not be mistaken for an aircraft actuator.

## Consequence for the map

Installed-source inspection improves the evidence, but does not resolve independent playback control. The next discriminating experiment should establish **which aircraft actually executes an EFM** before investing in a trajectory controller:

1. Instrument a minimal EFM sample with callback counters and a diagnostic force pulse.
2. Establish a positive control with that aircraft occupied by the local player.
3. Run the same aircraft type as AI while the player occupies a separate stock aircraft. Compare callbacks and observed motion; a normal AI flight is not a pass.
4. If callbacks and actuation are demonstrated, repeat with two instances and verify independent state.

These are proposed experiment steps, not executed tests or agreed fidelity tolerances. Failure with one sample would reject that setup, not prove all DCS integration routes impossible. A server/client approach remains a separate candidate requiring its own ownership and resource checks.
