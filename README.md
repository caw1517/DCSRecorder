# DCS Recorder

Record a flight, then fly alongside an aircraft playing it back in DCS World.
The project is for one player using one DCS account. Multiplayer is out of scope.

**Current milestone (26 September 2026):** a real, short F/A-18C flight has been
recorded and played back while the user flies another aircraft. The user reports
the latest jitter correction is “SO much better.” This is a working experimental
airborne prototype, not a finished recorder or a guarantee of complete physics.

**Priority:** finish reliable, faithful playback of **one aircraft** before
building layered playback. Synchronized microphone/lead calls are a future
feature, not part of the current implementation.

## How it works, in ordinary language

Think of the recording as a very detailed flight diary. About 50 times a second,
we write down where the aircraft is, which way it points, how it is moving, and
the simulation time. We also save aircraft/livery information and speed-brake
position. These are measurements of the flight actually flown, so real speed
bleed and recovery are already in the recording.

For playback, a custom mod supplies another aircraft. Our controller places it
on the recorded path and gives it the matching movement and rotation. DCS keeps
moving it between our updates. Smooth transitions between saved samples let the
aircraft follow a continuous path. The human pilot still flies their own normal
aircraft independently.

The first control experiments used paths we invented: straight flight, turns,
right/level/left combinations and a loaded roll. They helped us solve control
before adding recording. We then replaced that invented path with a real take.
Playback does not need to guess the original throttle or aerodynamic forces to
reproduce the measured movement. Engine appearance and sound are separate work.

The mod registers a separate playback aircraft using a locally prepared aircraft
definition and references to the installed Hornet model/textures/livery. Your
stock flyable Hornet and its normal flight model remain separate. Although the
early experiment used the external-flight-model (EFM) SDK, ordinary player EFM
callbacks did not run for the unoccupied playback object. Its demonstrated motion
comes from our recorded-path controller and native integration, not a newly
written Hornet aerodynamic model. Other aircraft require their own validated
registration, appearance/state mappings and compatibility checks.

A companion app to select takes and generate missions is a proposed workflow;
today's local preparation tools are its starting point. DCS still needs the mod
to execute playback. Exact original starting position plus matching aircraft
state, including a ground start after engines are running, is a requirement still
to implement. See the roadmap for the current acquisition/placement limitations.

The main obstacle was that DCS was also changing the playback aircraft's motion.
Stopping all native movement caused jumps. Letting it move with the recorded
speed and rotation worked better, but DCS still redirected velocity along the
nose. A real aircraft can point slightly above its actual direction of travel.
We now restore the recorded movement just before DCS advances this one aircraft.
That preserves both its attitude and its flight path.

## What is demonstrated

- Independent player and playback aircraft in a single DCS process/account.
- TF-51D synthetic-path experiments and subsequent F/A-18C testing.
- Calm-air turns, right/level/left paths, and a synthetic loaded left roll.
- A completed 38.78-second real Hornet take containing 1,940 samples.
- Smooth real-flight playback reported by the user after the latest correction.
- In the comparison window, average position correction fell from 18.84 cm to
  1.88 cm; the 95th percentile fell from 27.50 cm to 3.23 cm. This measures the
  adjustment needed each update, not absolute world-position or rendered accuracy.
- All 1,940 pre-physics restorations succeeded in the follow-up run, and the
  original update route was restored when playback finished.
- Clean Hornet configuration, exterior lights off, and speed-brake capture/playback.

## Current boundaries

The usable recording/playback path is one custom F/A-18C representation, Blue
Angels Jet Team livery, Caucasus, calm air, and a specific installed DCS build.
This does not yet support arbitrary aircraft or liveries. Flight import currently
accepts 5–300 seconds, altitude 1,000–5,000 m and speed 70–260 m/s, with conservative
rotation limits and a near-level beginning. Those are prototype guards, not the
planned final flight envelope. Playback starts after five mission seconds, blends
initial attitude for two seconds, and translates the take to the capture position.
Exact geographic placement is therefore not established.

Recording uses F10 Start/Stop and writes to DCS's normal log; local tools extract
and validate a completed take and prepare a playback mission. Explicit Stop and
collection before log rotation are necessary today. This workflow needs to become
simple and robust. Pause handling uses simulation time and has offline coverage,
but the user's real take did not include a pause; live validation is outstanding.

The control method combines documented object callbacks with build-specific
native interfaces and a per-object override. It is **not** a general supported
playback API. Compatibility across DCS updates is a significant product risk.
Collision/damage, wake generation/reception and ground contact remain independent
requirements. Good airborne motion does not prove them. Engine effects/sound,
smoke, gear, flaps and other animation fidelity also need work.

See [the roadmap](docs/ROADMAP.md) and [GitHub project map](https://github.com/caw1517/DCSRecorder/issues/1).

## Source and validation

Implementation and tests live in [experiments/efm-ownership](experiments/efm-ownership).
The name reflects the original experiment; the current unoccupied-aircraft route
does not run a normal player EFM to reproduce the recorded flight.

On the development Windows machine, with Visual Studio 2022, CMake and the
locally installed DCS SDK:

```powershell
cmake -S experiments/efm-ownership -B experiments/efm-ownership/build -G "Visual Studio 17 2022" -A x64 -DDCS_ROOT="D:/DCS World"
cmake --build experiments/efm-ownership/build --config Release
ctest --test-dir experiments/efm-ownership/build -C Release --output-on-failure
python experiments/efm-ownership/check_recorded_flight.py
```

Eight CTests cover callback contracts, paths, recorded interpolation and the
native-step boundary. Python/Lua integration checks additionally require the
locally generated donor mission package and installed DCS tools. A fresh clone
does not include those assets; portable setup is remaining roadmap work.
Do not install an arbitrary DLL with a mismatched mission/profile.

Only authored source, documentation and compact evidence summaries are tracked.
SDK code, game models, generated missions/packages, executable snapshots,
disassembly, raw logs and media stay on the development machine. No distributable
end-user release has been published. Older research notes describe their dated
experiments; this README and the roadmap describe current status.
