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
