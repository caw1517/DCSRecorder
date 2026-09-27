# Exterior-state observation prototype

THROWAWAY diagnostic for [Complete single-aircraft visual and engine-state fidelity](https://github.com/caw1517/DCSRecorder/issues/6).
Question: do the installed Hornet descriptor's candidate arguments actually follow
the stock aircraft's gear, flaps and control surfaces, with the expected ranges
and left/right meaning? See the [capability matrix](../../../docs/research/hornet-state-capabilities.md).

The user selected this group first. This prototype observes one stock player
Hornet; it does not command aircraft state, modify the accepted playback module,
write production recordings or establish replay fidelity. An HTML simulation
cannot answer the DCS runtime question, so the artifact is a diagnostic mission.

## Prepare

From the repository root, with Python 3 and the existing local baseline package:

```powershell
python experiments/efm-ownership/state-prototype/prepare.py experiments/efm-ownership/package/state-diagnostic
```

Use a fresh output directory each time. Generated mission content and installed
DCS assets stay local. The builder uses the existing mission/route/configuration
validators and refuses a different installed DCS build.

The user subsequently requested direct placement of generated missions in
`Saved Games/DCS/Missions`. After preparing a mission, copy it there without
overwriting an existing different mission. The builder itself still only packages.

## One live observation

1. Load `DCSRecorder-Exterior-State-Diagnostic.miz` from the generated output
   folder using DCS's mission file picker. It starts airborne; slow to a suitable
   gear/flap operating speed before changing configuration.
2. F10 > Exterior state diagnostic > Start capture. Fly nearly level for a few
   seconds to establish baseline.
3. Under **Mark next control change**, select **gear**, then lower/raise the
   gear. Select **flaps**, then exercise AUTO/HALF/FULL. Hold each state for a few
   seconds. Use external view to confirm the response.
4. Mark and exercise **pitch**, **roll**, **rudder** and **speedbrake** in separate
   segments. Use modest inputs and return to neutral between changes. Markers
   only label observations; they never move the controls.
5. Stop capture. Note any visual response that differs from the control change.
   Retain external-view video if practical so numeric channels can be compared
   with actual movement.
6. Preserve `Saved Games/DCS/Logs/dcs.log` before another DCS session. The unique
   prefix `DCSSTATE_LOG,1,` separates these samples from production recordings.

The diagnostic samples arguments 0-30 at 20 Hz for up to four minutes. Each row
contains take, row number, mission time, selected segment and argument values.
BEGIN/CHANNELS/MARK/END records retain identity, channel order, segment timing
and termination reason. Unsupported/nonfinite values stop capture explicitly.

## Interpretation

Candidate gear deployment: 0/5/3; flaps: 9/10 and 13/14; ailerons: 11/12;
elevators: 15/16; rudders: 17/18; speed brake: 21. These are candidates for live
verification, not a validated replay profile. Other arguments are deliberately
unnamed observations. Coupled surfaces may move together even when only one
pilot control changes; record that rather than attributing every change to a
single control.

Next, compare verified source channels against an isolated playback writer's
requested values, immediate and next-step readbacks, and visible behavior.
Initial-state alignment, pause/restart, motion and hook restoration remain gates.
Do not close the fidelity ticket on the basis of this capture-only diagnostic.

## Completed observation

The [first live result](../results/exterior-state-2026-09-27/README.md) contains
2,612 complete samples across all marked control groups. `analyze.py <log> <output>`
checks the single-take protocol and produces a CSV plus per-segment ranges.
It does not infer visual identity, full valid limits or playback support.

## Isolated playback actuator

`playback.cpp` builds as `HornetStateProbe.dll` and registers through the copied
local Hornet descriptor as `DCSRecorder-Hornet-State`. It uses the documented
object SDK to write only arguments 0/3/5, 9-18 and 21, plus the existing-style
elapsed/status transport on 998/999. It has no private native-memory access,
motion controller or step hook. The unoccupied aircraft follows a normal AI route.
The ordinary sample EFM is linked for the same registration structure as the
existing prototype; ordinary EFM execution is not assumed for this object.

The captured state sequence is linear-interpolated on its own clock. It retains
signed surface values and initializes every selected channel on the first
callback. Gear/brake are bounded to 0..1; the other selected arguments use a
provisional -1..1 diagnostic bound. Invalid tapes are rejected rather than clamped.
This is a bounded actuator experiment, not the production recording schema.

Preparation, using the retained local capture:

```powershell
cmake --build experiments/efm-ownership/build --config Release --target HornetStateProbe state_playback_check
python experiments/efm-ownership/state-prototype/prepare_playback.py experiments/efm-ownership/results/exterior-state-2026-09-27/dcs.log experiments/efm-ownership/package/state-playback
```

Use a fresh package folder for subsequent preparations. The prepared mod directory
is copied into `Saved Games/DCS/Mods/aircraft`; the mission is copied directly into
`Saved Games/DCS/Missions`. Refuse overwriting an unrelated existing destination.
The current installation has been verified against the package manifest.

### Run the installed playback test

1. Restart DCS to load the new module, then load
   **DCSRecorder-Exterior-State-Playback** from Missions.
2. The player starts in Active Pause. Use **F10 > Exterior state playback >
   Start captured surface sequence**. This spawns the lead and releases the player.
   Do not toggle Active Pause manually before this start.
3. Press **F2** to select the test lead. Watch its exterior surfaces while the
   screen identifies the current segment: baseline, roll, pitch, rudder, gear,
   flaps, speed brake. The lead's attitude/path will not match the capture flight;
   the surface sequence is the subject of this test.
4. The sequence takes 130.55 seconds. The final state is held for eight seconds,
   then the lead is removed. A failed handshake or write reports an error instead.
   **Stop and remove test aircraft** aborts; restarting the mission repeats it.
5. Report whether the surfaces move smoothly, whether they snap back or flicker,
   and whether gear/brake extend and retract. Keep DCS open for log collection.

### Evidence and verification

- `bin/state-logs/state-<process>-<run>.csv` in the installed test module records
  each requested value, immediate readback, next callback's pre-write value,
  previous request and callback interval. The pre-write comparison measures
  retention between callbacks, not a proven post-render sample.
- `events-*.csv` records creation, start, completion, rejection and destruction.
- `DCS.log` records mission-context reads under `DCSSTATE_PLAYBACK`, providing a
  second observation phase. This also does not replace visual inspection.
- The separate offline `state_playback_check` loads an isolated copy of the real
  DLL beside the captured tape. It passed all 2,612 source samples, signed values,
  midpoint interpolation, endpoint and identity/cookie/bounds/lifecycle/clock
  guards. Its fake SDK deliberately overwrites arguments before callbacks, so
  this is not evidence of DCS retaining the values.
- The prepared mission passed installed module-dependency, route and aircraft
  configuration checks. The accepted staged DLL and motion tape hashes were
  checked unchanged after installing this separate experiment.

Live write retention and visible rendering remain unverified. If DCS overwrites
the channels between callbacks, investigate the ownership/timing evidence before
adding these channels to the main recorder or declaring the exterior group done.

## Stabilator timing comparison

The [first actuator result](../results/exterior-playback-2026-09-27/README.md)
reproduced a severe overwrite of stabilators 15/16. Other tested channels were
visually accepted, with smaller measured later differences. The result is not a
completed exterior-fidelity milestone.

`prepare_playback.py ... --post-step` packages the separate
`HornetStatePostStepProbe.dll` / `DCSRecorder-Hornet-State-PostStep` module. Unlike
the baseline SDK-only experiment, it uses the existing build-guarded per-object
native-step interception, with an optional after-step callback. Only stabilators
15/16 receive this additional write; the tape, clock, AI route and other channels
are unchanged. Post-step telemetry goes to `post-step-*.csv`, and hook restoration
is recorded in `events-*.csv`. A missing callback, mismatched identity/build,
failed write or reversed clock fails the experiment. Live success remains pending.

Run **DCSRecorder-Exterior-State-Stabilator** after restarting DCS. Use the same
F10 start and F2 view; watch the **pitch** segment roughly 36-51 seconds after start.
Let the lead disappear at completion, then leave DCS open for collection.

`check_retention.py <native-trace> <DCS.log> --assert-stabilators` compares the
later reads against actual requested values. Its red baseline is preserved in
the result folder. Passing this numeric diagnostic must be accompanied by visual
review and a successful hook-restoration event before calling the repair complete.

### Current test: after the native animation update

The post-physics test above **failed live**: the stabilators still jittered.
[Video/trace findings and installed-build call order](../results/stabilator-poststep-2026-09-27/README.md)
identify a later update that writes both channels.

`prepare_playback.py ... --post-animation` builds the package for the separate
`DCSRecorder-Hornet-State-PostAnimation` registration. Restart DCS and run
**DCSRecorder-Stabilator-Animation** from Missions, with the same F10/F2 flow.
Only the stabilator timing changes. `post-animation-*.csv` records values at the
new boundary; other trace files retain their format. The subsequent
[live result passed](../results/stabilator-animation-2026-09-27/README.md): the user
accepted the appearance and both stabilators retained the requested values through
later mission reads. The run stopped before completion/hold; interrupted cleanup
was observed. Integration with normal recording and motion playback is next.

The retention comparator defaults to the last complete set of trace rows for a
mission run, including interrupted runs. Use `--run 1` for the first. Native and
mission run counts must match; elapsed-clock collisions are never merged.
