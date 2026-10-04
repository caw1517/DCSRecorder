# Resume: Prepare recording and playback copies from authored missions

Continuation snapshot requested by the user on 2 October 2026.
Task: https://github.com/caw1517/DCSRecorder/issues/24 (open, claimed by caw1517).
Parent: https://github.com/caw1517/DCSRecorder/issues/11.

## Workspace is required

Resume in `E:/Projects/DCS_Recorder` on this machine. Branch:
`codex/hornet-state-capabilities`; HEAD:
`705baec3c480b90a4318663fad2876e91dd59327`.
Implementation and evidence for several subsequent tasks are **uncommitted**.
A fresh clone of the branch does not contain this work. The working tree has
many changes from earlier tasks: do not reset, clean, overwrite or commit them
indiscriminately. GitHub contains the progress record, not all source/raw files.

Read root AGENTS.md (or the supplied workspace instructions),
`docs/agents/issue-tracker.md`, `docs/agents/domain.md`, `CONTEXT.md`, this task's
body/comments, and `experiments/efm-ownership/authored-preparation/README.md`.
The user invoked Wayfinder; its file is
`C:/Users/w_can/.agents/skills/wayfinder/SKILL.md`.
The parent explicitly authorizes implementation. This is step 5 of 15; the four
preceding tasks are closed. Continue this claimed task, not a new frontier task.

## Exact next live step

The last instruction to the user was:

> Load **050-Authored-Scene**, click **Fly**, and wait about 15 seconds. Tell me
> whether you see the authored-scene message and hear the brief chime.

**No result has been reported for that check.** Do not infer success from this
handoff request. If the user brings the result into the next chat, record it and
continue. Otherwise resume with this one concrete step. The message/chime is
authored to run after 12 seconds. This is the source baseline, not a recording
or playback run. The user operates DCS; the agent prepares files and examines
logs. Give one live step at a time, not the whole checklist at once.

## Installed and retained artifacts

Saved Games root: `C:/Users/w_can/Saved Games/DCS`.

| Installed mission | SHA-256 |
| --- | --- |
| `Missions/050-Authored-Scene.miz` | `f72d54f032e3532d61e25d31205a7e6192aae2ff94a3a3273f7f6acaa315c398` |
| `Missions/051-Authored-Recording.miz` | `78676654116fd64d90a2b27ba417d9003234f6e7251dac151c09989c9a879f66` |

Both hashes were rechecked for this handoff. DCS was not running at that check;
verify again when needed. Do not reinstall them: the additive installer refuses
existing files. No native modules or hooks were changed for this task.

Evidence root: `experiments/efm-ownership/results/authored-preparation-2026-10-02/`.
Current files are `source-v2/050-Authored-Scene.miz`, `source-v2/mission.lua`,
`recording-v2/{source.miz,prepared.miz,mission.lua,manifest.json}`,
`repeat-v2/` and `installation.json`. Earlier unversioned fixture/recording-package
directories are superseded and were never installed. Source-v2 has the tested
clean-pylon loadout. Repeat-v2 produces identical prepared ZIP bytes.

The user explicitly chose a **small dedicated test mission**. It contains three
stock airborne Hornets: `Record Hornet` (ID 12201), `Wing Hornet` (12202),
`Scene Witness` (12203); a truck, reference zone, timed message/flag/chime,
DEFAULT/FR dictionaries and embedded audio. All nine original non-mission archive
members are byte-identical in the recording copy. The recorder uses namespace
`DCSR_AUTHORED_2`, avoiding the authored `DCSR_AUTHORED_1_READY` flag.

## Implemented versus unfinished

Implemented:

- `companion/mission_data.py`: promoted data-only Lua table parser/serializer.
- `companion/authored_missions.py`: source inspection, scoped aircraft selection,
  immutable-source recording preparation, deterministic packaging, declared
  changes and complete structural/archive preservation checks. Conservative
  supported native trigger subset; refuse unknown scripts/compiled code and
  selected-aircraft task conflicts. Not a general behavior-compatibility engine.
- Recording uses the authored unit name, isolated Lua globals, current complete
  capture/autosave protocol and `authored_source_sha256` metadata.
- `playback_entries(...)` builds/tests **mission structure only**: distinct player
  Hornet, preserved authored player group except skill, source-derived lead
  initial position/velocity, original names/IDs and appended release controls.
- Companion `library.py`, `app.py`, `index.html`: source inspection and recording
  copy API/UI. Authored takes are blocked from the legacy fixed-donor playback
  path, which would lose the authored scene.
- `companion/test_authored_missions.py`: ten contracts; existing build-profile
  tests add three. Fixture generator, capture check and installer are under
  `experiments/efm-ownership/authored-preparation/`.

Still required, in practical order:

1. Receive/source-baseline live result; inspect relevant DCS errors if any.
2. Run `051-Authored-Recording` and compare the same briefing/message/chime and
   surrounding scene; capture a real short, nearly level airborne take through
   F10 Start/Stop. Confirm autosave, source-name/hash metadata and intact source.
3. Finish authored native playback packaging, reference/hook integration and the
   companion's take/player selection and activation path. Select `Wing Hornet`
   as the player, retaining its authored start. Do not call the legacy builder.
4. Run actual authored playback, retain logs and compare source/prepared scene,
   chosen player placement, controls and lifecycle behavior with user review.
5. Exercise Mission Editor save/round-trip and relevant refusals; retain structural
   and runtime comparisons. Repeat from the immutable source without accumulating
   additions. Do not claim arbitrary script equivalence or persistent identity.
6. Close only after this task's four acceptance items have live/structural evidence;
   post a resolution and update the parent's corresponding checkbox/pointer.

The recording-copy UI was inspected in a temporary localhost server with a
scratch Saved Games directory; that server and browser tab are closed. The user's
real companion was **not restarted or replaced**. Its settings are at
`C:/Users/w_can/Saved Games/DCS/DCSRecorder/companion-settings.json`.
Do not assume the running companion has reloaded these source changes.

## Checks already passed and how to rerun

These passed at the checkpoint; rerun after relevant changes, not merely to
repeat completed work. PowerShell, starting from `E:/Projects/DCS_Recorder`:

```powershell
$py = 'C:/Users/w_can/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$lua = 'D:/DCS World/bin/luae.exe'
$evidence = 'experiments/efm-ownership/results/authored-preparation-2026-10-02'

# 10 new authored-copy contracts and 3 existing build-profile checks.
& $py -m unittest discover -s companion -p test_authored_missions.py -v
& $py -m unittest discover -s companion -p test_build_trial.py -v

# Actual generated recorder: name selection, metadata, globals, Start/Stop protocol.
& $lua experiments/efm-ownership/authored-preparation/check_capture.lua "$evidence/recording-v2/mission.lua"

# Installed DCS dependency and route validators for the source fixture.
& $lua experiments/efm-ownership/verify_hornet_requirements.lua "$evidence/source-v2/mission.lua" 'D:/DCS World/Mods/aircraft/FA-18C/entry.lua' 'D:/DCS World/MissionEditor/modules/me_mission.lua'
& $lua experiments/efm-ownership/verify_hornet_routes.lua "$evidence/source-v2/mission.lua" 'D:/DCS World/MissionEditor/modules/me_route.lua' 3

& $py -m py_compile companion/authored_missions.py companion/mission_data.py companion/library.py companion/app.py
git diff --check
```

The companion JavaScript passed `node --check` and source/aircraft inspection
passed a real browser check. A generated script snapshot is in `ui-script.js`;
regenerate it from current `companion/index.html` before using it to validate
new UI edits. The old donor-specific configuration validator assumes fixed
light-off triggers and is not an authored-scene validator.

## Runtime and preservation notes

- DCS is pinned to `2.9.30.28536`, installed at `D:/DCS World`.
- Current take eligibility remains airborne; the prior hot-ground experiment
  only accepts its specifically evidenced take. Do not widen low-speed guards.
- Main log: `C:/Users/w_can/Saved Games/DCS/Logs/dcs.log`.
- Saved CSVs: `C:/Users/w_can/Saved Games/DCS/DCSRecorder/recordings/`.
- Actual loaded archive, when needed:
  `C:/Users/w_can/AppData/Local/Temp/DCS/tempMission.miz`.
  Preserve logs/archive before another mission replaces them.
- Accepted release integration: `experiments/efm-ownership/release-start/` and
  `results/countdown-release-2026-10-01/gear-package-v5/`. The prior controller is
  donor/name-specific: adapt it, do not copy its wholesale mission rewrites.
  Loaded Hornet defaults and DCS serialization previously caused real readiness
  failures. Retained red/green checks and captured loaded mission are in that
  evidence directory; do not weaken the runtime comparison to suppress failures.
- Ground work lives in `ground-start/` and `results/hot-ground-2026-10-01/`.
  Its completion evidence is on the preceding task; no need to repeat it here.
- DCS must be fully closed for installation. A lingering DCS.exe without a
  window previously needed the user to end it. Do not kill DCS automatically.
  Saved Games writes and GitHub CLI access require tool sandbox escalation.
- Unknown scripts/behavior and persistent cross-revision association remain
  separate gates. Current source hash + selected ID is only scoped to one exact
  archive and must not be represented as durable per-aircraft identity.
