# Engine-state observation prototype

THROWAWAY for [Complete single-aircraft visual and engine-state fidelity](https://github.com/caw1517/DCSRecorder/issues/6).
Question: which independent left/right engine measurements and nozzle arguments
can be captured, and do the mission and Export observations identify the same
aircraft at sufficiently close times? Playback actuation is the following gate.
The artifact is a DCS diagnostic mission because a simulated UI cannot answer
this installed-runtime question.

## Installed primary evidence

- `D:/DCS World/API/Sim_ControlAPI.md`, LuaExport API section: GUI hooks expose
  `Export.LoGetEngineInfo`, `LoGetSelfData`, `LoGetPlayerPlaneId`, and
  `LoGetModelTime`. Separate user hooks coexist through `DCS.setUserCallbacks`.
- `D:/DCS World/Scripts/Export.lua`, engine-info documentation: RPM percent,
  temperature Celsius, and fuel consumption kg/s, independently left/right.
- `D:/DCS World/CoreMods/aircraft/FA-18C/FA-18C_hornet.lua`, `net_animation`:
  argument 89 is labelled nozzle; 90 is adjacent but unlabelled. Pilot control
  arguments 395/396/397/398/420 are listed without individual semantics.

These are interface candidates, not live engine-capture validation. No afterburner
state is inferred from RPM, temperature, fuel flow, nozzle position or trajectory.

## Run in DCS

1. Restart DCS after installing the separate diagnostic hook.
2. Load **DCSRecorder-Engine-State-Diagnostic.miz** directly from Missions.
3. F10 > **Engine state diagnostic** > **Start capture**.
4. Under **Mark next throttle change**, choose each phase before moving throttles:
   baseline, both idle, both military (maximum dry), left afterburner with right
   dry, right afterburner with left dry, both afterburner, then both dry.
   Hold each briefly, allowing engine response, while maintaining controlled
   airborne flight. Markers only label observations; they never move controls.
5. Observe each nozzle, visible afterburner flame, and engine sound separately.
   External-view video with sound is useful for mapping the measurements.
6. F10 > **Stop capture**, then retain this session for collection before another
   DCS launch rotates the log. This does not create a flight-library recording.

The mission stops after four minutes or aircraft loss/change. It reads candidate
arguments 28/29/38/39/40/41/89/90/395/396/397/398/420 at 20 Hz, with position,
mission time, identity, initial snapshot, phase markers and explicit stop count.
Most arguments are deliberately unnamed; a finite zero is not proof of support.

The GUI hook reacts only to this diagnostic's `DCSENGINE_MISSION,1` messages in
the documented log-history API. For each sample it records both Export read
timestamps, ownship type/name/ID/position and six engine measurements under
`DCSENGINE_EXPORT,1`. Missing API data is explicitly unavailable, never zero.
No changes to Export.lua, the autosave hook, playback modules, source takes or
production schemas are needed. The hook performs no control/engine/native writes.

## Timing and identity gate

Log delivery is not simultaneous sampling. Analyze actual mission-versus-Export
delay, read duration, ID pairs and position separation before integration. The
analyzer rejects incomplete, missing, duplicate and unavailable samples. Its
preliminary timing screen is -20..100 ms delivery offset and 0..20 ms Export read
span, with correct aircraft type and stable observed Export identity. The live
recheck established different names/IDs across APIs; equality is not required.
The single-player diagnostic instead requires near-full time-interpolated
trajectory overlap with at most 1 m residual. These are diagnostic screening
bounds, not general object-identity proof or product accuracy tolerances.
Both raw and time-matched position differences are reported; no extrapolation
beyond the mission trace is used. Restarted takes remain separate in the summary.

```powershell
python experiments/efm-ownership/engine-prototype/analyze.py <dcs.log> <summary.json>
```

The output reports measured per-phase ranges, never an inferred afterburner state
or a sound-fidelity result. Sound requires its own later playback comparison with
matched camera/listener geometry. No playback actuator is established here.

## Prepare and install

Use a fresh output folder; generated missions and installed assets stay local.

```powershell
python experiments/efm-ownership/engine-prototype/prepare.py experiments/efm-ownership/package/engine-diagnostic
python experiments/efm-ownership/engine-prototype/install.py experiments/efm-ownership/package/engine-diagnostic "C:/Users/w_can/Saved Games/DCS"
```

Packaging pins DCS 2.9.29.27468 and uses the installed module, route and clean-jet
validators. Installation requires DCS closed, refuses different existing files,
checks both file hashes and verifies accepted DLLs/tapes, Export.lua and autosave
remain unchanged. To remove this diagnostic, close DCS and remove only its two
named installed files (mission and `Scripts/Hooks/dcs-recorder-engine-diagnostic.lua`).

`check_capture.lua` is an offline smoke harness for the actual packaged mission
and hook. It checks independent synthetic left/right readings, initial state,
pause and stop, plus unavailable API, wrong ownship and delayed-reading modes.
It does not validate actual DCS Export availability or visual mappings. Run with
the installed luae.exe, passing this directory, the generated `mission` file,
an output log path, and optionally `unavailable`, `identity`, `missing_name`,
`missing_self` or `stale`.

## Prepared checkpoint — 27 September 2026

Installed both diagnostic files directly in Saved Games with matching manifest
hashes. All eight protected existing files (accepted DLLs/tapes, Export.lua and
autosave hook) are unchanged. Source is on the existing
`codex/hornet-state-capabilities` prototype branch. Generated artifacts and the
installation manifest are local under `package/engine-diagnostic`.

Installed mission validators pass. The packaged-script smoke run produced 121
paired samples over six seconds with a known 4 ms synthetic delivery delay;
separate left/right values are retained. Unavailable engine data, wrong ownship,
one-second delivery delay, missing rows and duplicates are rejected by the
analysis gate. These are offline checks only. Live observation remains pending.

## First live result and corrected observation hook

The [first capture](../results/engine-capture-2026-09-27/README.md) retained 1,745
mission samples and all phase markers, but the original identity assertion
rejected every Export reading before measuring engines. It did not record which
identity field differed, so the actual runtime cause remains unknown.

The installed correction records actual identities (empty fields for unavailable
names) and retains available measurements even if the name differs. The analyzer
still flags uncertain identity; raw observations do not imply verified alignment.
It also summarizes mission channels when Export readings are absent.

Next run only a ten-second baseline capture after restarting DCS. Check identity
and engine-feed availability before repeating the full throttle sequence.

That recheck subsequently passed: 441 paired samples, 1..12 ms delivery offset,
and less than 1 mm time-matched position error. Actual Export identity is
`FA-18C_hornet` / `New callsign` / `16777472`, versus mission `Observer` / `2`.
Both engines return RPM, temperature and fuel flow. See the linked result for
ranges and limits. The next live action is the full marked throttle sequence;
the installed hook needs no further change or DCS restart for that capture.

## Isolated engine appearance playback

The full marked capture subsequently passed: 979 paired samples over 48.9 seconds,
with independent engine flow and argument changes. See the retained result above.
The separate module `DCSRecorder-Hornet-Engine-Appearance` now replays captured
arguments 28/29/89/90 after the guarded native animation update. This is a test of
nozzle/flame appearance. RPM and sound are not actuated; do not accept sound
fidelity merely because a nozzle moves. The subsequent live run accepted nozzle
and flame rendering and confirmed retention numerically; sound remained idle-like.
A normal AI route is used instead of replaying captured motion.

Restart DCS, load **DCSRecorder-Engine-Appearance-Playback.miz**, and use F10 >
**Engine appearance playback** > **Start captured engine sequence**. F2 selects
the test lead. Follow the phase messages; note each nozzle, flame and sound.
Allow approximately 57 seconds for playback and the hold, until the lead is
removed. Retain the DCS session for log collection.

`prepare_playback.py <capture.log> <new-output-folder>` validates and selects the
last complete marked take by its BEGIN occurrence. It never joins reused take
IDs. `install_playback.py <package> <Saved-Games-DCS>` installs only the separate
module and mission after hash checks, requires DCS closed and preserves existing
different files. Source captures stay immutable. Generated packages remain local.

The two engine DLL targets share the existing bounded exterior actuator source
with an explicit four-channel compile-time variant. The SDK-only target exercises
the tape offline; the installed variant adds the pinned-build post-animation
boundary. Existing exterior channels/header/timing selection retain their own
variant. Logs live under the new module's `bin/state-logs`; mission reads use
`DCSENGINE_PLAYBACK`. `check_playback_mission.lua` checks the mission lifecycle.

## Read-only sound callback probe

The [live appearance result](../results/engine-playback-2026-09-27/README.md)
accepts nozzle/flame animations but leaves sound unresolved. Prepare with
`prepare_playback.py <capture.log> <new-output-folder> --sound-probe` and install
with the same installer. It selects the separate module
`DCSRecorder-Hornet-Engine-Sound-Probe` and **DCSRecorder-Engine-Sound-Probe.miz**.
Use the same F10 menu above; let the lead disappear after about 57 seconds.

`HornetEngineSoundProbe` adds an observation wrapper around `ed_fm_get_param`.
It forwards every original value unchanged. The module's `bin/sound-logs` holds
first calls by index and counts at SDK/object lifecycle boundaries, including a
ready marker even when no parameter calls arrive. A missing file is inconclusive.
Counts are module scoped and do not identify the caller as an audio consumer.
This gate asks whether ordinary engine parameters are queried for this setup;
it neither replays RPM nor fixes sound. `engine_sound_check <DLL>` verifies exact
forwarding for 66 calls over 22 indices. Fixture traces are not installed.

The [live getter probe](../results/engine-sound-2026-09-27/README.md) returned
zero calls despite confirmed object lifecycle and 41.8 seconds of playback.
Do not attempt sound actuation through that unused callback in this setup.

## Sounder routing experiment

`prepare_playback.py <capture.log> <new-output-folder> --sounder-probe` selects a
new `DCSRecorder-Hornet-Sounder-Test` module and **DCSRecorder-Sound-Routing-Test.miz**.
Set `--saved-games` if the target installation differs from the default; it
determines this module's sounder log path. Install with `install_playback.py`.

F10 > **Sound routing test** > **Start sound test**, then F2. This deliberately
synthetic pattern plays a stock engine sample for three seconds, an afterburner
sample for three seconds, repeats once, then goes silent. The lead disappears
after 15 seconds. It tests direct world-audio control, not recording fidelity.
It does not follow the concurrent nozzle/flame sequence. The unique sounder
references installed samples without copying them and logs load/source/phase
events. `check_sounder.lua` and `check_sounder_mission.lua`, each with the matching
script path as its argument, validate dispatch and lifecycle offline. Audible
rendering/source lookup still require the live test.

The [15-second live test](../results/sound-routing-2026-09-27/README.md) completed
but remained idle-like. DCS discovered the script; execution was not observable.
The actual retained DCS loader, exercised offline by `check_sounder_runtime.lua`,
reveals that sounders have no `io` or `log` globals. Missing sounder.log therefore
does not prove missing execution. It accepts our source and dispatches all four
phases through captured audio calls, which is not a live audio acceptance result.

`install_sounder_logging.py <Saved-Games-DCS> <report.json>` installs a separate
temporary hook enabling dedicated SOUNDER/SOUND/ED_SOUND log outputs. It requires
DCS closed and preserves existing test files. The repeat completed but the
dedicated logs still contain no script messages, and audio remained idle.
Remove only `Scripts/Hooks/dcs-recorder-sounder-logging.lua` once diagnosis ends.

The isolated sound-test DLL now includes `sound_boundary.h`, a read-only observer
of sounder selection/instance presence and the internal engine getter path. It
writes `state-logs/sound-boundary-*.jsonl` once per second, with RTTI/vtable and
instruction guards. It never invokes private getters or writes engine fields.
An instance reference alone does not prove script updates or audible output.
`check_sound_layout.py <DCS-analysis-image> <WorldGeneral-analysis-image>` verifies
the guarded instructions against retained local snapshots; `sound_read_boundary`
checks bounded reads/decoding. Current-build validation still happens live.

`install_sound_boundary.py <new-DLL> <original-package> <Saved-Games-DCS> <new-backup-folder>`
checks the installed DLL against its original manifest, backs it up, then replaces
only that diagnostic DLL with DCS closed. It was installed successfully; 57
protected hashes were unchanged. The live run confirmed the custom sounder name,
Lua instance presence and wrapper binding throughout all 15 samples; its native
sounder is PlaneSounder_V2 with two AustereEngine_TurboFan objects. Instance
presence does not by itself establish script updates or audible rendering.

The logging gap was traced to a filter error: installed edCore's `log.ALL=255`
excludes `log.TRACE=256`, the level used by a retained SOUNDER Lua logging bridge.
The corrected hook includes TRACE explicitly and writes a TRACE self-check marker
in each output. `check_sounder_logging.lua <edCore.dll> <hook.lua>` failed against
the previous mask and passes against the correction using native constants.
The installer can replace the exact prior hook with `--previous-report` and keeps
a backup. Installed with 50 protected hashes unchanged. Repeat the same mission
to collect script diagnostics; no audible fix or new throttle capture is claimed.

The TRACE-visible live run subsequently confirmed both source handles and all
five intended phase timestamps, while the user still heard idle throughout.
Script registration/update dispatch is no longer the unverified boundary.

`prepare_playback.py <capture.log> <new-package> --audibility-probe` prepares
**DCSRecorder-Sound-Audibility-Test.miz**, a separate module/DLL/sounder. Its phases
are stock engine, generated quiet control beeps, stock afterburner, an explicitly
defined afterburner source, and test sources off (three seconds each). The
generated assets follow installed `Doc/Sounds/example.sdef`; no stock wave data
is copied. Logs include source-playing state and the engine parameters delivered
to the sounder. The mission displays phase labels and removes the lead at 15 s.
The existing installer installs this additive variant with DCS closed.

Run `check_sounder_runtime.lua <local-loader> <audibility_probe.lua> --audibility`
and `check_sounder_mission.lua <audibility_mission.lua> --audibility` for the
offline dispatch/lifecycle checks. See the [live diagnosis](../results/sound-routing-2026-09-27/README.md)
for interpretation, limitations and installed status. Listening remains required.

The comparison subsequently reported sources playing in their intended phases,
but the user heard no beeps and was uncertain about a later sound. Audibility is
not accepted. Live sound inputs did expose independently evolving core RPM and
thrust for both engines. The user reaffirmed **parameter recording/replay with
DCS-derived audio**; further sample-routing diagnostics are set aside. Recorded
RPM exists in the original capture, but has not been driven through the native
engine interface. Investigate that interface while retaining DCS's normal sound
renderer; do not build a production sample mixer from these diagnostic scripts.

## Recorded RPM through the native getter (live result pending)

`prepare_playback.py <capture.log> <new-package> --rpm-probe` prepares the separate
**DCSRecorder-Native-RPM-Playback.miz** and **DCSRecorder-Hornet-Native-RPM** module.
The stock aircraft descriptor and DCS sound renderer remain in use. There are
no custom sound scripts, sound definitions or wave assets in this module.

F10 > **Native RPM playback** > **Start recorded RPM test**, then F2 to the lead.
It forwards original RPM for 3 seconds, returns the captured left/right core RPM
for 48.899 seconds, restores the original getter for 3 seconds, then removes the
lead. The candidate conversion is Export RPM percentage divided by 100. That
mapping and audible behavior still require live validation. Fan RPM, thrust,
afterburner state, physical engine simulation, captured appearance and recorded
motion are not replayed by this bounded test; the lead follows its AI route.

`rpm_hook.h` replaces only one aircraft's core-RPM virtual getter using an owned
copy of its table; all other slots and unsupported getter arguments forward to
their original functions. Version, identity, table and instruction guards must
pass before installation. This is private access for DCS 2.9.29.27468 only.
`rpm_playback.cpp` records native caller module/address, engine index, core/fan
selection, original and returned values under `bin/rpm-logs`. `drain_time` is the
SDK clock when buffered calls are written, not the exact native call timestamp.
Lifecycle events record baseline/replay/restoration. Native sound consumption
and the user's listening result must be assessed separately.

Checks: CTest `native_rpm_boundary` and `native_rpm_mission`;
`rpm_module_check <packaged-DLL>` for actual DLL rejection of a non-DCS object;
`check_rpm_package.py <package> <capture>` for capture equality, stock descriptor,
hashes and the installed Sound.dll call-site guard. The existing
`check_sound_layout.py` checks the remaining guards against retained snapshots.
These checks do not establish audible fidelity. See the
[native RPM test record](../results/native-rpm-2026-09-27/README.md).
