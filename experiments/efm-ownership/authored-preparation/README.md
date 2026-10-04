# Authored mission preparation

Work on [Prepare recording and playback copies from authored missions](https://github.com/caw1517/DCSRecorder/issues/24).
The preceding ground-staging task was already closed when this task was claimed.
The user selected a small dedicated test mission for live validation.

`companion/authored_missions.py` reads data-only serialized mission tables,
selects stock Hornets by IDs scoped to an exact immutable archive, and prepares
separate recording copies. It preserves source bytes in the package and all
non-mission archive member bytes in the generated copy. Role changes and appended
controls are listed in an external manifest. Removing those declared changes
must reconstruct the complete source table. Repeated preparation is deterministic.
This is not the persistent aircraft-association implementation for the next task.

Recording selects the authored unit name, isolates mission Lua globals and uses
the installed complete-state autosave protocol. The take's metadata includes
the source archive digest. The companion has source inspection and recording-copy
API/UI controls. Authored takes are explicitly barred from the legacy fixed-donor
playback path while authored playback is under validation.

Playback **structure conversion** is implemented and tested: a different source
Hornet becomes the player without changing its authored group except its skill;
the lead retains its source ID/name and uses the recorded first position and
velocity. Ordinary route geometry and unrelated scene data are retained. Native
module packaging, loaded reference/hook integration, companion playback UI and
live playback from a new authored take remain unfinished. Do not present the
structure-only function as a completed playback workflow.

The initial behavior subset supports native startup/once triggers using time,
flag, unit-alive and group-alive conditions, and flag/text/sound actions. Source
and compiled trigger forms must agree. Unknown script actions, compiled-only
code, selected-aircraft tasks and unsupported group conversions are refused,
with the original preserved. Broader behavior adapters and loaded-session
authorization belong to their later integration task. Unknown dynamic behavior
is not certified by text scanning.

The fixture is explicitly constructed as a new authored test scene from ordinary
stock-aircraft data: three named Hornets, a truck, a reference zone, a timed
message/flag/chime, two localization dictionaries and embedded audio. Names are
`Record Hornet`, `Wing Hornet`, and `Scene Witness`; no donor names are required.
The source deliberately occupies a recorder-like flag; preparation allocates the
next unused namespace. The accepted fixture version is `source-v2` with clean
pylons; the earlier uninstalled fixture/package is retained as preparation history.

## Checks and live progression

Run `python -m unittest test_authored_missions test_build_trial -v` from
`companion/`: 13 tests passed at the preparation checkpoint. The actual generated
capture script passes `check_capture.lua` under the installed DCS Lua runtime.
Installed aircraft dependency and route validators pass. The browser UI showed
all three authored aircraft through the new inspection control; screenshot
inspection found no selection-layout problem. The temporary server/tab were
closed after inspection. The real running companion was not restarted or replaced.

`Install-Fixture.ps1` is additive, requires DCS closed, checks the build and
installed recorder scripts, refuses overwrite and records hashes. The two
installed missions are `050-Authored-Scene.miz` and `051-Authored-Recording.miz`.
No hooks/native modules were installed or replaced.

First live step: load the **source** mission, click Fly and observe the authored
message and brief chime after twelve seconds. Then compare the recording copy,
capture a real short take, implement/package playback from its saved source,
and compare the prepared scene and chosen player's authored start in DCS.
Mission Editor save behavior and full source/prepared live comparison are still
pending. Keep the issue open until its completion checklist is evidenced.

## Source-v2 load failure and source-v3

The installed `050-Authored-Scene` failed to load in DCS (2026-10-03): the
Mission Editor stopped at terrain init with `TriggerZoneData.lua:440: bad
argument #1 to 'unpack'`. The fixture's reference zone lacked the `color`,
`hidden` and `heading` fields that the Mission Editor always saves and requires.
This was a fixture defect, not a preparation or DCS fault; the recording copy
inherited it. Log: `results/.../source-v2-load-failure/dcs.log`.

`check_me_zones.lua` loads and re-saves a mission's zones through the installed,
unmodified `Mission/TriggerZoneData.lua`; it reproduces the v2 failure and passes
source-v3 and recording-v3. `source-v3` differs from v2 only in those three zone
fields (all other members and mission data equal); recording-v3/repeat-v3 are
byte-identical. Installed additively as `052-Authored-Scene.miz` and
`053-Authored-Recording.miz` (`installation-v3.json`). 050/051 are superseded.

## Source-v3 load failure and source-v4

`052-Authored-Scene` got past the zones but then failed in the briefing screen
(`me_autobriefing.lua:293`, nil `path`). make_fixture had discarded the
baseline's l10n dictionary/mapResource tables while keeping the mission's
references to them: `ResKey_ImageBriefing_1` plus three `DictKey_`s. Log:
`results/.../source-v3-load-failure.log`.

`check_resources.py` mirrors `Scripts/dictionary.lua` getValueResource (locale,
then DEFAULT) and requires every referenced `ResKey_`/`DictKey_` to resolve, and
every resolved file to exist in the archive. The untouched baseline passes; v2/v3
fail. The fixture now merges the baseline DEFAULT/FR tables and keeps the
briefing image, and the truck carries the full ME-saved vehicle field set.
`Install-Fixture.ps1` runs both offline load checks before installing.
Installed as `054-Authored-Scene.miz` / `055-Authored-Recording.miz`
(`installation-v4.json`); 050–053 are superseded. These checks cover the two
failures seen, not every Mission Editor load path.

## Live results (2026-10-03)

- `054-Authored-Scene`: loaded; user saw the authored message and heard the
  chime. No script/GUI errors. Evidence: `results/.../source-v4-live/`.
- `055-Authored-Recording`: user confirmed the same message and chime as 054; real F10 Start/Stop take `20261003T174448Z-0001.csv`,
  1,132 rows (~22.6 s), `user_stop`, engine capture max delay 20 ms. Metadata:
  source `Record Hornet` / 12201, `authored_source_sha256` = 054 hash. Accepted by
  `recorded_flight.read`. The installed 054 source is unchanged.
  Evidence: `results/.../recording-v4-live/`.
- The archives DCS actually loaded keep aircraft names/IDs/pose/livery/skill, the
  truck, zones, weather, briefing and triggers. Dictionaries, resource maps and
  warehouses are semantically equal (re-formatted); image/audio bytes are
  identical. DCS adds Hornet defaults, re-serializes triggers and replaces
  `options` with the user's settings on every load; none of this is authored scene.
- The Mission Editor's trigger serialization (empty `events`/`custom`/
  `customStartup`) was refused by preparation; fixed, with a regression test.

## Authored playback package (playback-v1)

`prepare_playback.py <take> <source.miz> <lead id> <player id> <out>` builds an
airborne authored playback from a real take and its exact source:

- Module `DCSRecorder-Hornet-Authored-Test` / `HornetAuthoredProbe.dll`: the
  accepted gear-package-v5 module files and **same DLL bytes**, under a distinct
  name (as ground-start did) so no loaded DLL instance is shared.
- Mission from `authored_missions.playback_entries`: declared role edits only
  (lead type + recorded first pose rounded to 12 significant digits; player skill),
  `restored_structure_equals_source`, all other archive members byte-identical.
- Hook `DCSRecorderAuthoredControl`: release-start/hook.lua with names and the
  namespace substituted. Its exact `expected.lua` comes from `loaded_reference.py`,
  a model of DCS's load-time rewrite that reproduces both real loaded archives
  (054 and 055) exactly; runtime comparison stays exact.
- `check_authored_hook.lua`: arms against the predicted loaded mission; refuses
  position/trigger/aircraft/weather edits, other missions and no native readiness.
- `Install-Playback.ps1`: additive, hash-verified, DCS closed, no overwrite.

## Companion integration and close-out

The companion lists authored takes, finds the exact source by hash (saved
recording packages, then Missions), offers the other stock Hornets as the player,
and builds with `prepare_playback.build`. `Library.install_authored` replaces only
per-take files (tape, metadata, expected.lua, hook) after a backup; shared module
files must match. Live (`results/.../companion-live/`): the companion installed
only the new mission and hook; readiness armed at once, release and completion
were clean, and the load model matched the sixth real load exactly.
Tests: `companion/test_authored_playback.py`.
