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
span, with matching numeric IDs and ownship type/name. These are diagnostic
screening bounds, not agreed product accuracy tolerances. Position separation is
reported without pretending a moving aircraft should occupy an identical point
at two different timestamps. Restarted takes remain separate in the summary.

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
an output log path, and optionally `unavailable`, `identity` or `stale`.

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
