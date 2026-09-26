# Hornet mission-load failure: missing relative datalink files

The user reported loading apparently frozen at Terrain Generation Init 97,
`caucasus.ng5`. The latest log shows terrain initialization completing,
followed by a GUI Lua error at `me_datalinks.lua:259`: attempted call to
missing `getDefault`, from `setDefault` -> `setupOnLoad` -> `fixDatalink`.
The simulation had not reached aircraft control. See `datalink-error.txt`.

The copied Hornet descriptor retained `datalinks.Link16 =
"Datalinks\\Link16.lua"`. The editor resolves this relative to the
descriptor's registered `_file`, which now points to the custom mod.
Packaging had included the descriptor but omitted this relative dependency.
Missing script resolution left an empty descriptor with no `getDefault`.

`verify_hornet_datalink.lua` loads the installed `me_datalinks.lua` and runs
its actual `setDefault` function, with unrelated UI/editor services stubbed.
It reproduced the same exception at line 259 against the installed broken
package. Adding the installed Hornet's Datalinks directory (AddProp.lua,
Link16.lua, Link16.dlg) made the test pass: it creates the actual defaults
for the mission unit and resolves the dialog. The regression is now part
of packaging and passed against the repaired installed mod as well.

Only those three missing local support files were installed. DLL and
mission hashes remain unchanged. No DCS core scripts, terrain, licensing
configuration or graphics settings were changed. Full GUI mission loading
and Hornet flight remain pending the user's retry.

## Subsequent route-timing validation error

The next load progressed to mission validation and reported both Observer
and Probe: `Route has no waypoints with locked time!` (user screenshot
`Screen_260926_090745.jpg`). The Hornet mission generator had incorrectly
set `ETA_locked=false` on every waypoint while changing speed. The prior
formation mission correctly anchored its first waypoint at ETA zero.

`verify_hornet_routes.lua` extracts and executes the installed editor's
route-timing validator against the serialized mission, adding only the
waypoint indices supplied by DCS during import. It reproduced both exact
messages before the fix. The generator now locks only the first waypoint
to ETA zero and calculates subsequent unlocked ETAs from distance and the
profile's speed. Downstream speeds remain locked. Both routes pass.

The route check now runs during packaging, together with module-ID, Lua
syntax and datalink-default checks. All passed before reinstalling the
mission. The DLL, aircraft, livery, weather and controlled flight path are
unchanged. Full simulator loading still needs the user's retry.
