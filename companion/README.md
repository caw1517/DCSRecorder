# DCS Recorder companion (local first version)

This local browser interface manages a flight library, display names, validation,
and ready-to-fly practice/playback missions. It binds only to 127.0.0.1. Recordings
and game assets stay on the machine. The current app runs from this checkout with
Python 3; it is not yet a portable desktop distribution.

## Supported scope

DCS 2.9.29.27468, stock F/A-18C, Blue Angels Jet Team livery, Caucasus, zero wind,
airborne recordings of 5 to 300 seconds and 70 to 260 m/s. Initial attitude must
be within 10 degrees of level. Staged playback no longer imposes an altitude
floor/ceiling or angular-rate cap; the final hard-turn take passed live review.
Finite-data, continuity, orientation, ownership and build checks remain.

Ground starts, taxi, takeoff, landing, full-demo duration and remaining exterior
state remain required follow-up work. The user accepted integrated engine sound
and nozzle/flame playback. White-smoke capture and actuation passed separately;
version-four automatic capture and recorded white-smoke playback passed with a
52.92-second take. A small bass/impact difference between stock and playback
engine sound is deferred to V2. V1 smoke is explicitly white only; multicolor
smoke is also a V2 feature. The remaining
airborne speed restriction still excludes stationary/taxi portions. The accepted
hard-turn replay does not establish terrain contact or 250-500 ft AGL flight.

## Setup and launch

Run Setup-Companion.ps1 with Python, BaselineMission, DonorMod and AcceptedRecording
paths, optionally SavedGames and DcsRoot. DCS must be closed. Setup installs the
separate dcs-recorder-autosave.lua hook, copies the accepted baseline without
changing its source, writes local settings and creates
Saved Games/DCS/DCSRecorder/Start-DCSRecorder.ps1. The staged playback module must
already be installed from the accepted integration test. Launch that PowerShell
script to open the app in the default browser; launching twice reuses the app.

Alternatively: python companion/app.py --settings <companion-settings.json>.
No core DCS scripting changes, mission sandbox changes or Export.lua changes are
made. Setup refuses to silently replace a different existing save hook.

## Recording and playback

With the engine workflow installed (`engine_capture` enabled in local settings),
new `DCSRecorder-Practice-Engine-*` missions save version-three CSVs: motion,
brake, thirteen signed surface/gear channels, four nozzle/flame arguments, and
the native core/fan/thrust/power readings for both engines with their sample time.
The read-only helper is pinned to the current DCS build. Capture verifies player
identity, timing, position association, Export RPM agreement and equal E0/F0
power getters. Failed native capture retains an incomplete file with a save error.
No Export.lua or DCS core file changes are required.

Conversion preserves the raw source and aligns native values to the motion clock;
the separate **DCSRecorder-Hornet-Engine-Staged** controller drives recorded motion,
surface/nozzle/flame appearance and the stock native sound inputs together. Values
above one survive unchanged. Lights, canopy and suspension/wheels remain outside
this group. The normal engine workflow passed the user's visual/audio review.

With `smoke_capture` enabled, new **DCSRecorder-Practice-Smoke-*** missions fit the
verified white generator on SMK station 10 and save version-four CSVs. Metadata
retains its CLSID/station and smoke profile; each row adds `smoke_time,smoke_on`.
The read-only native helper observes the actual emitter flag. Missing/unavailable
state fails the take instead of inventing OFF. Other colors and aircraft are
rejected until verified. Older recordings remain readable and gain no smoke data.

Version-four takes are labeled **Motion + surfaces + engines + smoke**. Conversion
retains measured transition times without interpolation. The initial state uses
the first read, at most 50 ms after the initial motion sample. A transition after
the final motion sample is outside playback duration. The mission embeds the
validated smoke events and generator; the accepted native controller continues
to consume an unchanged version-three motion/surface/engine tape. Thus no new
native motion implementation or playback DLL is required. The tape fingerprint
binds that motion/engine data; smoke events are self-contained in each generated
mission, so missions with identical motion but different smoke retain their own
smoke sequence. Source CSV and generated mission hashes are retained in the package.

The mission applies `SMOKE_ON_OFF` after the native handshake and reads native
elapsed time at 20 ms intervals. It initializes the recorded smoke state, sends
only changes, does not replay obsolete bursts after a delayed frame, and removes
the lead on command or clock failure. Completion still removes only the lead.
The command request clock is observable in `DCS_PLAYBACK_SMOKE` logs; this does
not establish a renderer latency bound.

`install_smoke_workflow.py prepare <new-output> --settings <settings>` checks the
known version-three hook and both installed native readers, stages a version-four
save hook/capture Lua/settings update and a validated smoke practice mission.
`install_smoke_workflow.py install <output>` requires DCS closed, backs up replaced
files and verifies protected hashes. Restart DCS and the companion afterward.

Older version-one takes remain readable and unchanged. Their library detail says
that exterior surfaces were not recorded. They use `DCSRecorder-Hornet-Staged`;
version-two takes use the separate `DCSRecorder-Hornet-State-Staged` controller.
Install that module and the updated autosave hook before recording version two,
then restart DCS. Old practice missions still generate valid version-one takes.
The companion must run from this updated checkout, not an older worktree.

The library labels version-three takes **Motion + surfaces + engines**. Version-two
takes remain **Motion + surfaces** and do not gain engine state by regeneration.
Version-one takes remain **Motion only**: gear, flaps and control surfaces
were not captured and cannot be recovered by regenerating playback. Choose
Create practice mission and load that exact new `DCSRecorder-Practice-Exterior-*`
mission to record surfaces, or the new **DCSRecorder-Practice-Engine-*** mission
to include engines. Updating the
app does not update scripts embedded in existing practice missions.

The packager verifies the installed controller against its corresponding build
artifact. Build `HornetStateStagedProbe` for the new integration; replacing the
accepted `HornetStagedProbe` artifact would require its own controller deployment.
For engines, build `HornetEngineStagedProbe`; preserve the existing installed
controllers. `install_engine_workflow.py prepare <new-output> --settings <settings>`
prepares the migration from the known version-two hook. After checks pass,
`install_engine_workflow.py install <output>` requires DCS closed, verifies source
and destination hashes, backs up the hook/settings, installs the separate module
and capture Lua, and enables new practice missions. The previously validated
`NativeEngineCapture.dll` must already be installed and match the build artifact.
Restart the companion after migration to load its new code and settings.

1. With DCS closed, choose Create practice mission in the app.
2. Start DCS and load the generated DCSRecorder-Practice mission. Begin nearly
   level, then F10 > DCS Recorder > Start recording. Fly the maneuver being tested.
3. F10 > Stop recording. Confirm the new timestamped take appears in the library
   before closing DCS. The DCS hook saves automatically; the app need not be open.
4. Choose a take, optionally rename it, close DCS, then Generate playback mission.
5. Load the generated DCSRecorder-Playback mission. F10 starts a countdown and the
   complete recording. The lead disappears at completion; restart to replay.

Only the latest selected tape is active in the staged module. Older generated
missions contain a recording fingerprint and reject a mismatched tape with an
explicit message. Regenerate a mission to activate a different recording. The app
checks the DCS build and process state, verifies the installed DLL against the
prepared DLL, keeps a copy of the previous tape and restores it on activation
failure. Each generated mission/package gets its own ID; original recordings are
never edited. Names are separate sidecar files.

## Persistence contract

The mission emits the established BEGIN/DATA/END recording protocol into DCS.log.
A separate GUI hook consumes the documented DCS.getLogHistory API on every frame
without using the failed GUI-to-mission bridge or opening the active log file. It writes each take to a timestamped .partial file, checks
row order and sample count, flushes and closes it, and renames it to .csv only for
an explicit user_stop. DCS supplies complete log messages. Aircraft loss, missing
samples, log-history reset and abandoned takes remain incomplete and cannot be
selected for playback. Completed CSV files survive DCS log rotation.

Saving follows delivery of the Stop message through DCS log history. Confirm the library entry before
exiting DCS; immediate forced termination before the END event is consumed cannot
be promised durable. Hook write errors are logged under DCS_RECORDER_SAVE. A .partial
file is retained for inspection, not silently repaired into a completed flight.

New practice recordings carry capture-build and weather metadata. Only the exact
accepted legacy baseline hash may omit those fields. Unsupported recordings stay
visible with a reason; incomplete .partial files are counted separately.

## Verification and acceptance

Canopy capture is implemented in the separately staged canopy workflow. New
canopy-enabled practice missions save version-six recordings and the library
adds `+ canopy`, selecting a separate canopy-capable controller. Initial position
and transitions preserve measured argument 38 on the common playback clock.
Older recordings keep their existing behavior. Isolated changing-canopy replay
is accepted visually and numerically; the normal closed-canopy workflow is also
accepted, with matching native/later telemetry and automatic completion. See the
[canopy integration checkpoint](../experiments/efm-ownership/results/canopy-integration-2026-09-28/README.md).

Light capture is available with the installed lights workflow. New practice
missions save version-five flights containing measured exterior brightness and
strobe state, with optional measured white smoke. The library adds `+ lights`
and selects a separate lights-capable playback module. Older recordings remain
unchanged and retain their original playback module. The integrated light path
passes offline checks and the user accepted normal lights-off capture/playback.
Two completed runs confirm the formation-light startup overwrite is corrected
in native post-animation traces. Independent later mission telemetry is enabled
for future generated missions; it was absent from those accepted runs.
See the [integration checkpoint](../experiments/efm-ownership/results/lights-integration-2026-09-28/README.md).

Run python -m unittest discover -s companion -v. Tests cover unchanged source
bytes on rename, incomplete/error takes, build/weather validation, path rejection,
running-DCS and unsupported-build guards, rollback after partial activation, and
the Lua sink's complete messages, repeated IDs, duplicate END, missing rows,
aircraft loss, abandonment and history reset. A regression reproduces the GUI
environment refusing active-log reads and checks that completed takes still save. Real installed Lua/module/route/configuration
validators also passed practice and playback generation in an isolated directory;
two generated practice captures passed library validation.

The staged controller and app-managed hard-turn take passed live completion.
The user confirmed the remaining requested repeated/longer-take, pause/resume,
restart and frame-rate checks passed. These are manual acceptance results; no
specific extra durations or frame-rate settings were supplied. See the
[validation record](../docs/validation/workflow-2026-09-26.md) for measured evidence
and the boundary between current support and follow-up work.

Live automatic-save result: 1,975 samples / 39.48 seconds, saved 9 ms after Stop, byte-for-byte verification passed, and no unfinished file remained. Both earlier failed captures were recovered. The hook now checks storage on startup, reads DCS log history, accepts void-success file operations, and verifies complete saved bytes before publication.
