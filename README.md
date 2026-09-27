# DCS Recorder

Record a flight, then fly alongside an aircraft playing it back in DCS World.
One player, one DCS account. Multiplayer is out of scope.

**Current milestone — 26 September 2026:** the first local single-aircraft
record-to-replay workflow is implemented and accepted. The companion provides a
flight library, validation, renaming, and generated practice/playback missions.
F10 Stop saves completed recordings automatically. Fast-roll playback and the
repeatable nose-jump correction have passed live user checks.

This is a build-specific local prototype, not a portable end-user release or
complete ground-to-ground aircraft-state replay. Finish one-aircraft fidelity
before adding layers. [Current roadmap](docs/ROADMAP.md).

## Use the local workflow

See [companion setup and use](companion/README.md). After the development setup:

1. Generate a practice mission with DCS closed, then load it in DCS.
2. Begin airborne and nearly level. Use F10 Start recording, fly, then F10 Stop.
3. Confirm the timestamped take appears in the companion flight library.
4. Select the take, optionally rename it, close DCS and generate playback.
5. Load the generated mission. Active Pause holds the player until F10 starts a
   three-second countdown. Playback starts at the original recorded pose with
   the player nominally 150 feet behind.
6. Playback completion removes the lead; the mission continues. Restart to replay.

Original recordings remain unchanged. Incomplete recordings stay separate. Only
the most recently selected tape is active; old missions reject a mismatched tape.
The automatic-save hook reads DCS log history and retains completed files outside
DCS logs, so routine log rotation does not erase saved flights.

## How playback works

About 50 times per simulation second, the recorder samples position, orientation,
velocity, time, aircraft/livery identity and speed brake. These are measurements
of the flight actually flown, including its speed changes. Playback follows the
measured path; it does not guess pilot controls or recreate Hornet aerodynamics.

A separate custom aircraft references locally installed Hornet assets. Documented
object callbacks and guarded, build-specific native access command its pose and
motion. A per-object physics-step override restores recorded velocity and rotation
before native integration. The stock player aircraft remains independent.
Ordinary player EFM callbacks were not the viable control route for the unoccupied
playback object. Other aircraft need validated registration and state mappings.

The staged controller applies the first recorded sample without the old attitude
acquisition blend or translation. It also suppresses an extra native presentation
pitch contribution that caused the repeatable nose jump. Interpolation preserves
attitude through inverted flight; fast rolls use spherical interpolation.

## What has been verified

- Automatic save, library selection/renaming, mission generation and full playback.
- F10 staging/countdown, original first-sample pose/velocity, completion and restart.
- Accepted 38.78-second baseline retained in local evidence; later 39.48-second
  app capture saved successfully and its nose-jump correction passed live review.
- The latest 80.92-second hard-turn take completed all 4,047 native motion writes;
  the hook restored at completion. The user reported it worked great.
- The user reports the remaining requested repeated/longer-take, live pause/resume
  and frame-rate checks passed. Exact settings were not supplied; this is manual
  acceptance, not separately reconstructed telemetry for every condition.
- 13 native CTests and 10 companion tests pass. Offline tests include 180-degree/s
  rolls and a modeled 7.5-G, 350-knot turn. Synthetic numerical precision does not
  establish real simulator loads, terrain contact or rendered accuracy.

See the [validation record](docs/validation/workflow-2026-09-26.md) for evidence
and limits. Smooth motion is not a claim of complete collision, wake or ground physics.

## Current support and follow-up work

DCS **2.9.29.27468**, F/A-18C, Blue Angels Jet Team livery, Caucasus and zero wind.
Recordings currently span 5–300 seconds and 70–260 m/s, starting within ten degrees
of level. The staged playback path has no altitude floor/ceiling or angular-rate
cap. Build, ownership, finite-data, orientation and continuity checks remain.
There is no G-load rejection. Low-altitude numeric acceptance is not terrain-contact
validation; the latest real hard-turn take reached roughly 572 m MSL.

Stationary ground starts, taxi, takeoff, landing/rollout, custom aircraft placement,
gear/flaps, smoke, engine/afterburner appearance and sound remain required follow-up
work. A full demonstration must eventually work from ground start to landing,
including low passes and hard maneuvers. Current speed/duration bounds are prototype
limitations, not the final product requirement. Layers and synchronized lead-call
voice remain deferred. No complete cockpit-system reconstruction is claimed.

## Build and checks

Windows development setup: Visual Studio 2022, CMake, Python 3 and the installed
DCS SDK/tools. The companion uses Python's standard library.

```powershell
cmake -S experiments/efm-ownership -B experiments/efm-ownership/build -G "Visual Studio 17 2022" -A x64 -DDCS_ROOT="D:/DCS World"
cmake --build experiments/efm-ownership/build --config Release
ctest --test-dir experiments/efm-ownership/build -C Release --output-on-failure
python -m unittest discover -s companion -v
```

The companion library tests require the local accepted recording fixture; set
`DCSREC_TEST_BASELINE` to its path on another development machine. Mission packaging
also requires the locally generated donor mission/mod and DCS tools. A fresh clone
contains no game assets or sample user recordings. Portable setup is follow-up work.

Only authored source, documentation and compact evidence summaries are published.
Generated missions, binaries, game assets, raw logs, recordings, native image dumps
and user media remain local. Historical experiment notes describe their dated
results; this README and the roadmap describe current status.
