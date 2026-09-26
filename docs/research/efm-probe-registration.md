# Isolated EFM probe aircraft registration

Inspected installed primary sources on 2026-09-23. This is a proposed registration, not a simulator-tested aircraft. No installed aircraft or Saved Games files were changed for this research.

## Recommendation

Register a new type, `DCSRecorder-EFM-Probe`, using the installed free TF-51D exterior and its complete AI aircraft descriptor, then bind only that new type to the probe DLL. Keep the original `TF-51D` available as the observer aircraft. Reference installed assets; do not copy or redistribute them. Begin airborne; ground handling is outside this diagnostic.

The stock descriptor is readable at [TF-51D.lua](<D:/DCS World/CoreMods/aircraft/TF-51D/TF-51D.lua>). It calls `add_aircraft` with the complete descriptor, including `SFM_Data`, mass, geometry, shape references and AI parameters. Its three mount calls use `current_mod_path`. This permits a private Lua environment to capture the descriptor without registering the stock type again. Lua `setfenv` use is evidenced in [MissionEditor.lua](<D:/DCS World/MissionEditor/MissionEditor.lua:48>). Availability during plugin loading still needs runtime verification.

The installed community [UH-60L entry.lua](<C:/Users/w_can/Saved Games/DCS/Mods/aircraft/uh60l/entry.lua>) demonstrates `declare_plugin`, `binaries`, `make_flyable(type, cockpit_path, FM, comm_path)`, and `plugin_done`. Its FM table puts plugin ID at index 1 and DLL basename at index 2. The official [TF-51D entry.lua](<D:/DCS World/Mods/aircraft/TF-51D/entry.lua>) independently demonstrates the same two-element FM binding.

## Candidate entry.lua

This is a grounded starting point, **not a claim that these are all runtime-required fields**. Use the actual DLL basename produced by the build. `Cockpit/Scripts` should initially contain the probe's own minimal cockpit scripts; cockpit compatibility is a separate bootstrap uncertainty.

```lua
local id = "DCSRecorder-EFM-Probe"
local root = current_mod_path
declare_plugin(id, {
    installed = true, dirName = root,
    displayName = "DCS Recorder EFM Probe",
    fileMenuName = id, version = "0.1", state = "installed",
    binaries = { "DCSRecorderProbe" },
})

local aircraft
local env = setmetatable({
    current_mod_path = "./CoreMods/aircraft/TF-51D",
    add_aircraft = function(value) aircraft = value end,
}, { __index = _G })
local chunk = assert(loadfile("./CoreMods/aircraft/TF-51D/TF-51D.lua"))
setfenv(chunk, env)
chunk()
assert(aircraft and aircraft.Name == "TF-51D", "Unexpected stock descriptor")
aircraft.Name = id
aircraft.DisplayName = "DCS Recorder EFM Probe"
aircraft.WorldID = WSTYPE_PLACEHOLDER
aircraft.attribute[4] = WSTYPE_PLACEHOLDER
aircraft.shape_table_data[1].index = WSTYPE_PLACEHOLDER
aircraft.shape_table_data[1].username = id
-- Preserve Shape and shape_table_data[1].file = "TF-51D".
add_aircraft(aircraft)

make_flyable(id, root .. "/Cockpit/Scripts/", { id, "DCSRecorderProbe" }, nil)
plugin_done()
```

Distinct type/world indexes prevent deliberately overriding the free stock aircraft. Shared model registration and whether a separate `shape_table_data[1].name` is needed are unverified. Any load error must be treated as registration failure, not evidence about EFM execution for AI.

## Cockpit limitation

Directly reusing TF-51D cockpit scripts is not a clean diagnostic. Its [device_init.lua](<D:/DCS World/Mods/aircraft/TF-51D/Cockpit/Scripts/device_init.lua>) instantiates `P51D::ccMainPanel51D`, `FM_Proxy`, engine, electrical and other compiled devices. The stock plugin also loads `TF51D` binary. Compatibility of those devices with an arbitrary EFM is not established.

The free Su-25T [device_init.lua](<D:/DCS World/Mods/aircraft/Su-25T/Cockpit/Scripts/device_init.lua>) only declares kneeboard support, but its [entry.lua](<D:/DCS World/Mods/aircraft/Su-25T/entry.lua>) uses `MAC_flyable` with a nil FM, not the proposed EFM binding. Therefore reusing that path is also an experiment, not a verified shortcut. A probe-owned minimal cockpit with external F2 observation avoids depending on the stock TF-51D systems, but still requires an in-simulator positive control to establish flyability.

## Mission starting point

The official [Caucasus TF-51 flight over town mission](<D:/DCS World/Mods/aircraft/TF-51D/Missions/QuickStart/Caucasus TF-51_flight over town.miz>) is a readable ZIP. Its `mission` member contains one USA player TF-51D, groupId/unitId 2, airborne at 2,000 m BARO and 138.88888888889 m/s; the archive also contains options, warehouses, theatre and localization. This establishes a local template without needing paid terrain.

For the player positive control, make a separate local archive and replace that unit's type with the probe type. For the AI trial, retain the stock player unit and add a separately named group and probe unit with fresh IDs, AI skill and a clear lateral position offset, updating both unit and route coordinates. Do not give both units `Player` skill. Preserve archive members unless intentionally changing them; parse and serialize the Lua mission table rather than broad text replacement. Verify the generated mission in the mission editor and simulator. This research only inspected the archive; it did not create or run missions.

The player and AI runs must use fresh process-level logs or explicit run identifiers. A loaded DLL or plugin declaration is not proof of `ed_fm_simulate` calls. Only a successful player callback control makes a missing AI callback result interpretable for this configuration.
