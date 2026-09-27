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

Ground starts, taxi, takeoff, landing, full-demo duration, full exterior/engine
state and afterburner effects/sound remain required follow-up work. The remaining
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

New practice missions record gear, flaps and control surfaces with motion and
speed brake in version-two CSVs (`hornet-exterior-v1`). The native tape preserves
each signed channel and interpolates it on the motion clock. This integrated
path is installed for live comparison; its isolated stabilator timing already
passed visual and numeric review. Suspension/wheels, canopy, smoke, lights and
engine/nozzle/effects/sound remain outside this captured group.

Older version-one takes remain readable and unchanged. Their library detail says
that exterior surfaces were not recorded. They use `DCSRecorder-Hornet-Staged`;
version-two takes use the separate `DCSRecorder-Hornet-State-Staged` controller.
Install that module and the updated autosave hook before recording version two,
then restart DCS. Old practice missions still generate valid version-one takes.
The companion must run from this updated checkout, not an older worktree.

The packager verifies the installed controller against its corresponding build
artifact. Build `HornetStateStagedProbe` for the new integration; replacing the
accepted `HornetStagedProbe` artifact would require its own controller deployment.

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
