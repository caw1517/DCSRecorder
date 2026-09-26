# First actual recorded flight — 2026-09-26

## Latest result: live capture and smoother playback succeeded

The corrected mission recorded 1940 samples over 38.78 simulation seconds with
an exact 20 ms sample interval and a complete Stop marker. The real take passes
CSV validation, mission packaging and native playback interpolation checks.
See [the captured-flight evidence](../../experiments/efm-ownership/results/first-recorded-flight-2026-09-26/README.md).
The matching playback DLL, tape and mission are installed, with hashes verified
after DCS was closed. The first replay worked with visible jitter; the subsequent
pre-physics motion correction was accepted by the user and measured in process
45780 (mean position correction 1.883 cm, p95 3.230 cm). See the follow-up section
below. The next milestone is complete single-aircraft playback. The user confirmed
that this take contained no pause and deferred live pause testing.

## Capture correction history and recording procedure

The first live capture failed before any samples were saved: the GUI hook
received a frame before initialization and lacked the `a_do_script` bridge
assumed by the offline harness. Capture now runs inside the mission and writes
structured events through `env.info`. The corrected mission and inactive
compatibility hook are installed. The corrected capture path subsequently passed
its live test, followed by the successful playback and jitter follow-up below.
The recording mission uses only the stock Hornet. The synthetic roll DLL is now
archived with its matching mission in the live-capture evidence folder.
The original installation is documented in
`experiments/efm-ownership/results/recording-prototype-2026-09-26/`.
Failure evidence, the corrected installation hashes and regression checks are in
`experiments/efm-ownership/results/recording-bridge-failure-2026-09-26/`.

1. Start DCS fresh and load `EFM-Probe-Hornet-record.miz` from Saved Games/DCS/Missions.
2. Fly level at approximately 400 KIAS. Use the radio menu: F10 Other > DCS Recorder > Start recording.
3. Wait for the recording confirmation. Begin with five seconds straight and
   level, then use a 45–60 second gentle-turn take. Live pause testing is deferred.
4. For this first test, stay at 5000–9500 feet MSL and 300–400 KIAS. Avoid abrupt
   roll inputs; current native guards constrain the range of supported takes.
5. F10 > DCS Recorder > Stop recording. Wait for `Recording stopped: N samples
   written to DCS.log`. Stop explicitly before leaving the mission.
6. Leave DCS open and report completion. Extract completed takes from
   `C:/Users/w_can/Saved Games/DCS/Logs/dcs.log` with `extract_recording_log.py`
   into `C:/Users/w_can/Saved Games/DCS/DCSRecorder/recordings`. CSV files appear
   after extraction, not automatically during flight. Collect before restarting
   DCS because the simulator rotates its logs. Abandoned takes without END events
   are not exported.

The next step after receiving a real take is to inspect its clock, basis vectors,
velocity consistency and coverage, prepare a matching playback mission, archive
the installed synthetic DLL/mission pair, then install the recorded-flight pair
with DCS closed. The user then observes and flies alongside their own recording.

## Capture

`record_flight_mission.lua` is embedded in the dedicated mission. It samples via
`timer.scheduleFunction`, which uses simulation time, and writes versioned
BEGIN/DATA/END events through standard `env.info`. This API was exercised in the
earlier live synthetic tests. The old hook is replaced by a file with no callbacks;
it only logs the installed recorder version. No core scripting changes, unsafe
bridge configuration or Export.lua modification are required. The installed API
documentation's `a_do_script()` example did not establish its availability in the
isolated user hook; the live run disproved that earlier assumption.

The mission samples the actual player's world position, forward/up/right vectors,
world velocity and exterior speed-brake argument 21. Metadata includes the stock
aircraft type, assigned livery, terrain and unit name. Engine RPM fields are empty
in this mission-only capture revision; they mean unavailable, not zero RPM.
Throttle, afterburner state, engine animation and audio reproduction remain deferred.

The sampler requests 20 ms intervals and keeps actual simulation timestamps;
live cadence depends on the scheduler. Pause duplicates are omitted. F10 Stop
writes the take's sample count and completion marker. The extractor checks row
sequence and completion before emitting a CSV with an END footer. Missing rows
are rejected, repeated extraction is idempotent, and a partial final log line is
left for the next extraction attempt. Each Start creates an independent take.
Aircraft loss is marked and rejected by the playback importer. Explicit Stop is
required; this revision does not promise finalization when quitting mid-take.

## Validation and playback

`recorded_flight.py` accepts complete version-1 CSV recordings. It validates
metadata, finite samples, orthonormal/right-handed bases, increasing clocks,
gaps no larger than 150 ms, 5–300 second duration, position/velocity consistency,
1000–5000 m altitude, 70–260 m/s world speed, speed brake 0–1 and conservative
angular speed below 0.9 rad/s. Orientations become sign-continuous quaternions.

`recorded_path.h` independently validates the generated tape on load. It uses
quaternion SLERP for attitude, cubic Hermite position interpolation using saved
world velocities, and derives matching native linear/angular motion from that
interpolated path. It does not synthesize thrust, drag, lift or speed schedules.
The saved trajectory therefore includes real speed bleed, recovery, AoA and
sideslip. Speed brake follows the recording; exterior lights remain off.

At mission time about five seconds, the controller captures the playback
aircraft, translates the recorded trajectory to that position, and blends
attitude for two seconds. The world axes and heading are preserved. After those
two seconds, orientation follows the recorded samples directly. The native
lead-in spawns five seconds behind the first recorded point at recorded speed;
the small capture translation means exact geographical placement is not yet
guaranteed. Initial attitude mismatch over 20 degrees is rejected. There is no
Euler-angle interpolation and no special case at inverted.

Native object identity, build/signature, altitude, speed, angular-rate and
10 m command-step guards remain enabled. Playback ends by releasing native
control; behavior after release is not part of recorded-flight fidelity.
Only one playback aircraft is supported. Multiple recordings/layers, generic
aircraft registration, exact absolute placement and engine fidelity remain open.
The first package supports the Blue Angels Jet Team Hornet livery; a different
recorded type or unregistered livery is rejected instead of silently substituted.

## Reproduce preparation and checks

Run from `E:/Projects/DCS_Recorder` with the available Python runtime:

```powershell
cmake --build experiments/efm-ownership/build --config Release
ctest --test-dir experiments/efm-ownership/build -C Release --output-on-failure
python experiments/efm-ownership/check_recorded_flight.py
python experiments/efm-ownership/prepare_recording.py
python experiments/efm-ownership/extract_recording_log.py <dcs.log> <recordings-folder>
python experiments/efm-ownership/prepare_recorded_playback.py <completed-take.csv> <output-folder>
```

Preparation writes local artifacts only. The playback output contains the
mission, `HornetProbe.dll` built from the separate `HornetRecordedProbe` target,
`recorded-flight.txt`, metadata, original CSV and a hash manifest. Install the
DLL and tape together into the Hornet prototype's `bin` folder only after
archiving its current matching DLL/mission pair. The plugin loads `HornetProbe`
by name; restarting DCS is required when switching profiles. Old synthetic
missions require their matching synthetic DLL to reproduce their original tests.

Eight CTests cover the existing TF-51D/Hornet callback contracts and synthetic
paths plus recorded playback geometry: full rotation through inverted,
quaternion sign changes, translation, matching velocity, speed brake and invalid
tape rejection. Python/Lua integration tests run the actual serialized mission
startup in a sandbox without a GUI bridge, create multiple takes, exercise 6000
paused frames and completion, reject missing log samples and malformed takes,
check that the compatibility hook needs no initialized simulator, package playback, and load
the converter's output with the actual C++ path evaluator at 100 Hz. Packaging
checks use the installed DCS module and route validators and cockpit light IDs.
These checks establish offline behavior; they do not establish successful live
capture, sampling performance, runtime ID or visible playback accuracy.

## First live replay and jitter follow-up (2026-09-26)

The first completed take contains 1940 samples across 38.78 seconds. The user
reported that replay worked but had jitter absent in synthetic paths. Native
telemetry shows 18.84 cm mean position correction versus 1.88 cm for the synthetic
roll. DCS's null-FM controller reprojects velocity onto the nose, losing the real
recording's angle-of-attack component between playback commands.

The recorded-flight DLL now contains a guarded, per-object pre-physics-step
restoration test using a private virtual-table copy. It restores recorded linear
and angular motion before calling the original integrator. It does not alter
attitude, sample data, shared tables or executable pages. An eighth CTest checks
the dispatch/ownership boundary in a mock fixture. The follow-up live run (45780)
passed all 1,940 restorations and restored the original update route on release.
Mean position correction fell to 1.883 cm, p95 3.230 cm, max 3.891 cm; the velocity
overwrite metric is zero. The user reported "SO much better." This is the new
accepted short-flight baseline, not proof of complete playback fidelity. Evidence,
limitations and the comparison command are in
`experiments/efm-ownership/results/recorded-jitter-2026-09-26/README.md`.
