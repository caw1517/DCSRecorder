# EFM ownership diagnostic

**Current status (26 September 2026):** recorded Hornet playback with pre-physics
motion restoration is accepted visually by the user and measured in process
45780. Finish one-aircraft playback before layering; voice recording is deferred.
See the [overview](../../README.md), [roadmap](../../docs/ROADMAP.md), and
[recorded-flight notes](../../docs/research/dcs-recorded-flight-prototype.md).
The dated instructions below retain experiment history, not the current next test.

This experiment began by testing whether DCS calls a custom EFM for an AI aircraft while the player occupies a separate stock aircraft. It now includes a guarded native motion prototype and an initial recorded-flight pipeline.

## Next live test: record a real Hornet flight (2026-09-26)

The synthetic Hornet turn/roll tests are complete enough to proceed to capture.
Use `EFM-Probe-Hornet-record.miz` and its F10 Start/Stop controls to record a
short stock-Hornet flight. See [the recording protocol](../../docs/research/dcs-recorded-flight-prototype.md)
for installation, validation, import and current limits. The installed synthetic
roll DLL remains in place until a real take is available to import. The sections
below retain earlier experiment history.

## Current working baseline (2026-09-25)

2026-09-26: continuous motion matching passed the live control/release
check, with user-reported smooth motion. See the
[result](results/continuous-motion-2026-09-26/README.md) for limits.
The next separate test is the [Hornet prototype](../../docs/research/dcs-hornet-prototype.md):
nominal 400 KIAS, Blue Angels livery, run 95 seconds. The TF-51D installation
is retained for comparison. Later route and roll tests are not yet prepared.

Use `EFM-Probe-climbing-turn-formation-zero-wind.miz` with the installed
motion-matching DLL. The user accepted zero-wind missions after a large
visual improvement, supported by an 87.16% reduction in mean position
correction. Mission generation now sets all three wind speeds and ground
turbulence to zero and uses static weather. Wind compensation is deferred.
See [the result](results/zero-wind-2026-09-25/README.md) for measurements
and remaining validation. The next revision matches motion throughout
5–43 s, followed by cessation of control; live validation remains pending.
Run the mission for 55–60 seconds. See the
[continuous-motion protocol](../../docs/research/dcs-continuous-motion-experiment.md).
The lifecycle sections below retain earlier experiment history.

## Current revision: startup-loaded object lifecycle probe

The original player control passed and AI EFM comparison failed; evidence is retained under `results/`. The current revision additionally uses `load_immediately = true` and the installed SDK's `ed_setup_object_api` / `ed_on_object_*` callbacks. These callbacks are read-only and write separate `objects-*.csv` logs beside the EFM logs. The mission observer appends the unit's ID to each row for correlation.

**Next run:** start a fresh DCS process and run `EFM-Probe-ai` for 15 simulation seconds. Check startup DLL load, API setup, target-correlated object simulation callbacks, and EFM callbacks as separate outcomes. Object lifecycle success alone does not establish force/pose control. See `docs/research/dcs-installed-native-attachment.md` for evidence and interpretation. The existing EFM pulse would still run if DCS invokes that interface.

The first lifecycle run received 970 simulation callbacks, but its native object ID differed from the mission ID. The installed read-only `Scripts/Hooks/ownership-id-map.lua` now logs the documented mission-to-runtime-ID mapping for EFM-Probe missions. A fresh five-second AI run is sufficient to correlate IDs. Compare logs from the same run; runtime IDs are not assumed stable across runs.

**Identity check completed:** same-process logs map Probe mission ID 9001 to callback runtime ID 16777472; the stock player has a different runtime ID. See `results/object-identity-2026-09-23/`. No further identity run is needed. Physics/pose access remains the next unresolved gate.

**Current next diagnostic:** `native_identity.h` reads bounded MSVC x64 type metadata on the first object simulation callback and writes `native-types-*.txt`. Run the AI mission for five seconds after restarting DCS. This determines the native class/base hierarchy to guide the physics-bridge investigation; it does not write aircraft state or call private physics functions. The mission/runtime-ID hook remains useful for correlating this new type record.

**Native type check completed:** the unoccupied probe is `woAIPlane` in DCS.exe, and the callback's Registered/MovingObject subobject is at offset 8 in this build. Evidence is in `results/native-type-2026-09-23/`. The next work is offline inspection of its flight-model ownership path; another type-check flight is unnecessary.

## Build and package

Requires the installed DCS SDK sample and Visual Studio 2022 C++ tools. No ED code or models are copied into source control; packaging uses the local free TF-51D mission and installed model references. Generated packages are local test artifacts, not for distribution.

```powershell
cmake -S experiments/efm-ownership -B experiments/efm-ownership/build -G "Visual Studio 17 2022" -A x64
cmake --build experiments/efm-ownership/build --config Release
ctest --test-dir experiments/efm-ownership/build -C Release --output-on-failure
./experiments/efm-ownership/package.ps1
```

Copy `package/DCSRecorder-EFM-Probe` into Saved Games/DCS/Mods/aircraft and the two packaged missions into Saved Games/DCS/Missions. The probe registers a new aircraft type; it does not replace TF-51D. Restart DCS after installation or DLL changes.

The package also includes `EFM-Probe-clients.miz`, a follow-up candidate with two **Client** slots: stock TF-51D `Observer` and custom `Probe`. Its slot structure and trigger syntax are checked; two-client runtime operation remains unverified. This mission requires both clients to occupy their respective slots. It must not be interpreted as the earlier AI test or as proof that a dedicated server provides an occupied pilot.

## Run in order

1. Fly `EFM-Probe-player.miz` for at least 15 simulation seconds, using F2 for the external view. This intentionally minimal cockpit has no normal aircraft systems. The sample flight model is not a faithful TF-51D flight model. Start airborne; do not use this mod for ground operations or normal flying.
2. Save that run's logs, then restart DCS to isolate the second run.
3. Fly `EFM-Probe-ai.miz` for at least 15 simulation seconds. The player is the stock TF-51D; the probe is an AI aircraft offset 1 km along world X.
4. Save both logs and compare the independently observed `Probe` trajectory with the EFM callback positions. Do not interpret the AI test if the player positive control fails.

## Evidence

- The DLL writes `bin/probe-logs/callbacks-<process>-<tick>.csv` inside the installed probe directory. Rows distinguish start events, repeated simulation callbacks, state callback counts, world position, quaternion, pulse and release. Time is accumulated EFM dt, not mission clock.
- The mission writes `OWNERSHIP_OBSERVER` rows to Saved Games/DCS/Logs/dcs.log at approximately 10 Hz, using normal mission logging. Position and the aircraft's up vector are sampled independently through `Unit:getPosition()`; no script sandbox changes are required.
- A positive 4000 N*m roll moment is added for a total of 0.5 seconds beginning at EFM time 5 seconds. The impulse is 2000 N*m*s; dt overlap handling prevents a boundary-crossing timestep from extending the pulse. Each EFM start resets the experiment.
- The standalone CTest loads the actual DLL and verifies exports, bounded roll moment, impulse at two different dt values, and restart reset. It does **not** demonstrate DCS loading, callbacks, flyability, or physical participation.

## Interpretation

- A registration error, failed positive control, absent observer rows, or target mismatch is **inconclusive**.
- Player callbacks and pulse response, followed by an observed AI probe with no callbacks in a fresh run, rejects this specific single-process EFM configuration.
- AI callbacks alone do not pass: callback positions must match the probe and the independent observations must show its pulse response.
- A pass establishes one aircraft only. Multiple-instance isolation, trajectory accuracy, collisions and wake are later gates.

To uninstall, close DCS and remove only the `DCSRecorder-EFM-Probe` mod directory and the two `EFM-Probe-*.miz` missions. Preserve any logs needed for the research record first.

Also remove the diagnostic `Scripts/Hooks/ownership-id-map.lua` and the optional `EFM-Probe-clients.miz` mission if installed. Other hooks are unrelated and should remain untouched.
