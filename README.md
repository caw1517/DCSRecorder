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

## Supported envelope

| | Demonstrated | Evidence |
|---|---|---|
| Build, theatre, wind | DCS 2.9.30.28536, Caucasus, zero wind (earlier evidence on 2.9.29.27468) | |
| Aircraft | F/A-18C; Blue Angels and VFA-64 liveries recorded | [#33](https://github.com/caw1517/DCSRecorder/issues/33) |
| Starts and endings | Hot parking with engines running, or airborne. Parked completion with engines running, or removal at other endings | [#27](https://github.com/caw1517/DCSRecorder/issues/27), [#31](https://github.com/caw1517/DCSRecorder/issues/31) |
| Ground phases | Taxi, takeoff roll, liftoff, touchdown, rollout, taxi back to parking | [#28](https://github.com/caw1517/DCSRecorder/issues/28), [#34](https://github.com/caw1517/DCSRecorder/issues/34) |
| Duration | 883.5 s live. 30 and 60 min offline. No upper limit | [#34](https://github.com/caw1517/DCSRecorder/issues/34) |
| Speed | 0 to 488 kt | [envelope results](experiments/efm-ownership/results/envelope-2026-10-07/README.md) |
| Load factor | 7.8 G at 415 kt, averaged over 0.5 s | same |
| Low flight | 41 m (135 ft) above the runway; inverted passes at 55–70 m | same |
| Inverted | 18 s continuous inverted pass | same |
| Rolls | Dirty roll on takeoff, rolling series, about 205°/s | same |
| Vertical | Cuban 8 (loops through ±90° pitch), straight-down dive, vertical climbing roll | same |
| Lighting | Landing/taxi light illuminates the ramp (user comparison at dusk) | [#27](https://github.com/caw1517/DCSRecorder/issues/27) |

Every phase and manoeuvre above meets the limits agreed in [#28](https://github.com/caw1517/DCSRecorder/issues/28): horizontal 0.10 m, vertical 0.05 m, attitude 0.5°, velocity 0.25 m/s on the ground and 2.0 m/s in the air, timing one tick, state 1e-3. Known exceptions:

- **Post-liftoff drift:** up to 0.48 m horizontal for about 7 s after liftoff when a roll is flown right after takeoff. A normal takeoff stays within 0.014 m. Tracked in [#37](https://github.com/caw1517/DCSRecorder/issues/37).
- **Rollout wheel rotation:** up to 0.0022 revolution against the 1e-3 limit, probably a measurement artifact. Accepted by the user.
- **In-air report:** DCS `inAir()` disagrees with the recording on the ground. Tracked in [#38](https://github.com/caw1517/DCSRecorder/issues/38).
- **Collision:** contact from the player damages the playback aircraft, which keeps its recorded path. Policy is under [#3](https://github.com/caw1517/DCSRecorder/issues/3).

Anything outside this table is **not demonstrated**, not refused. There are no altitude, speed, G or rate caps. Other theatres, wind, other aircraft types and other DCS builds have not been tested.

Layers and synchronized lead-call voice remain deferred. No complete cockpit-system reconstruction is claimed.

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
