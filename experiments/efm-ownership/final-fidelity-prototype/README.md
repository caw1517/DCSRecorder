# Final combined fidelity capture

One ordinary saved flight for the remaining refueling-light evidence and final
integrated visual/audio check. Flight, engine and smoke samples come from the
normal recorder and native helpers. Cockpit lights/probe controls change on a
90-second sequence; flight, gear, brake, smoke and throttle stay under user control.

Prepare with the bundled Python and installed Lua runtime:

```powershell
python experiments/efm-ownership/final-fidelity-prototype/prepare.py `
  'C:/Users/w_can/Saved Games/DCS/Missions/DCSRecorder-Practice-Wheels-d46c24a8.miz' `
  experiments/efm-ownership/package/final-fidelity-capture-checked 'D:/DCS World'
```

The output folder must not already exist. Installation is a separate verified
copy to a new mission filename. No restart is needed for this mission-only copy.

Load **DCSRecorder-Final-Fidelity-Capture.miz**. Fly nearly level, start normal
F10 recording, follow the prompts, and stop recording at the final prompt. Leave
DCS open for collection. Keep Active Pause off during recording. Keep gear/probe
speed within the briefing and stay within the supported airborne recording bounds.

Controls come from the installed Hornet `devices.lua`, `command_defs.lua` and
`Input/FA-18C/joystick/default.lua` (ProbeControlSw EXTEND=1, RETRACT=0).
The stock aircraft descriptor associates refuel lighting with argument 212.
Automatic control does not establish successful activation: inspect the capture.

The resulting playback must use matching mission time (19:00) for the light
comparison; normal recordings do not yet store mission time-of-day. Preserve the
saved CSV and configure the separate generated playback mission accordingly.
The [acceptance record](../results/fidelity-final-2026-09-29/README.md) distinguishes
completed numerical/regression evidence from the pending live verdict.
