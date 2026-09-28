# Parked canopy diagnostic prototype

Question: does the installed stock Hornet expose its actual canopy position,
including partial holds, through exterior argument 38?

This separate mission precedes any recording-schema or playback changes.
Installed DCS 2.9.29.27468 maps exterior argument 38 to cockpit argument 181 in
`Mods/aircraft/FA-18C/Cockpit/Scripts/mainpanel_init.lua`
(`CreateSimpleConnectedGauge(38,181)`). The installed `clickabledata.lua`,
`command_defs.lua`, and keyboard bindings identify the mechanical device's
OPEN/HOLD/CLOSE commands. Device and command IDs are loaded from that build.
The diagnostic never commands canopy jettison.

## Run

Prepare with `python experiments/efm-ownership/canopy-prototype/prepare.py`.
It requires the existing accepted baseline mission, installed DCS assets, and
a fresh `package/canopy-ready` output directory. Generated game assets stay local.
The installed cold-start Caucasus mission supplies the parking location and
route; configuration changes that start to the installed hot-parking variant,
retaining one stock Hornet with the accepted clean Blue Angels configuration.

Load `DCSRecorder-Canopy-Diagnostic.miz`, keep throttle idle, set parking brake,
and stay parked. Do not use Active Pause. Select F10 → Canopy diagnostic →
Start automatic canopy sequence. Watch in F2 for about one minute:

1. Close fully and hold closed.
2. Open briefly and hold partially open.
3. Open fully and hold open.
4. Close briefly and hold partially closed.
5. Close fully and hold closed.

Do not operate canopy controls during the sequence. Leave DCS open for log
collection. The menu also provides Stop and release canopy control. Completion
and abort release both switch directions to HOLD. Abort does not forcibly close
the canopy. A second run requires restarting the mission.

## Evidence and boundaries

`capture.lua` samples argument 38 at 50 Hz on mission time, logging ordered
requests, applied phases, samples and completion under `DCSCANOPY,1,`.
Hold durations begin at actual application. Capture stops on loss of the player,
nonfinite arguments, airborne/moving aircraft, or bounded phase/run timeout.
`analyze.py LOG OUTPUT_JSON` summarizes the measured response per applied phase;
it does not infer rendered motion or assume endpoints before live observation.

`check_capture.lua` exercises the packaged mission's normal, user-abort,
missing-phase and moving-aircraft paths, including switch cleanup, command
restrictions, duplicate starts and ordered capture. Its constant-value fixture
verifies plumbing only; it is not evidence of canopy movement.

This experiment does not establish jettison, internal cockpit restoration,
ground dynamics, or ground-start recording/playback support. No normal flight
library, recording format, active playback tape, module or hook is changed.

See the [installation and live-evidence checkpoint](../results/canopy-2026-09-28/README.md).
