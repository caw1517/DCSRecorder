# Smoke observation prototype

Question: which observable state tracks the stock Hornet's actual demonstration
smoke, with the correct mission loadout fitted?

The installed `CoreMods/aircraft/FA-18C/FA-18C_hornet.lua` defines dedicated SMK
station 10 with `{INV-SMOKE-WHITE}` and five other colors. The user highlighted
this mission requirement. The existing clean-aircraft generator clears all stores;
future integration must explicitly preserve the smoke station and color on both
the recording and playback aircraft. A command or marker alone is not proof of
emission. Installed input definitions expose **Smoke Device - ON/OFF** on
`CPT_MECHANICS`; it is not assumed to be the generic Export smoke command.

Run `python experiments/efm-ownership/smoke-prototype/prepare.py` with access to the
pinned DCS installation. It creates a separate stock-player mission with white
smoke fitted, checks installed mission requirements/routes and exercises the
embedded diagnostic offline. No module, GUI hook or production schema changes.

Prepared and installed `DCSRecorder-Smoke-Diagnostic.miz` in Saved Games Missions.
Installed dependency/route validation, clean-station checks, and the packaged
capture harness pass. Installation verified the mission hash and five protected
recording/playback file hashes unchanged. Details remain in local
`package/smoke-diagnostic/manifest.json` and `installation.json`. Only a new mission
was installed, so no DCS restart is needed. The first live observation is complete;
see the [capture and next actuator test](../results/smoke-capture-2026-09-27/README.md).

In the mission, start F10 **Smoke diagnostic** capture. Observe smoke externally,
toggle the aircraft's smoke control, and mark the actual visible OFF/ON states,
holding each for five seconds: OFF, ON, OFF, ON, OFF. Stop capture and retain the
DCS session for collection. Markers only label human observations. At 5 Hz, the
probe records a complete initial exterior-argument snapshot (0–999), followed by
changed values and per-frame counts. The two-minute limit bounds collection.
Unchanged/unimplemented arguments do not establish effect state. A channel that
correlates with smoke remains a candidate until a separate replay renders smoke.

This is a diagnostic, not a flight-library recording. Raw logs and generated
missions remain local and ignored. White-smoke actuation and an initial native
state observation are now documented in the [smoke result](../results/smoke-control-2026-09-27/README.md).
Remaining work: verify simulation-clock capture, preserve loadout/color, then
integrate measured state with the flight library and validate recorded playback.

`analyze.py <dcs.log> <analysis.json>` validates and reconstructs sparse snapshots.
The first capture did not identify a clear smoke-state argument. The separate
`prepare_control.py` builds **DCSRecorder-Smoke-Control-Test.miz** from the accepted
Test playback mission and checks the active tape hash. It adds white smoke only
to the lead and requests three five-second bursts via the installed mission
command `SMOKE_ON_OFF`. Start via the ordinary F10 playback menu. This synthetic
sequence tests visible actuation independently from smoke-state capture; it does
not turn the user's visible-state markers into purported recorded smoke data.

## Native capture diagnostic

`NativeSmokeCapture` is a separate read-only helper pinned to DCS 2.9.29.27468.
It checks instruction bytes, current-player RTTI, station 10's smoke-generator
classification, vector layout and boolean state. The native emitter-enabled
flag is read directly; no smoke setter is called. Unsupported states return
`UNAVAILABLE`, never an invented OFF value. No aircraft object is retained.

Build the target in Release, then run the CTest `native_smoke_capture_lua`.
`install_native_capture.py <Saved Games/DCS> <report.json> --check-only` checks
the DLL ABI, hook fixtures and additive installation paths without writing game
files. Remove `--check-only` after closing DCS to add the DLL and GUI hook.
Existing files with different contents are not overwritten, and the installer
checks protected scripts, recordings, missions and module hashes.

The hook stays dormant until a new F10 smoke diagnostic capture. Each mission
FRAME prompts a read with its own Export start/finish model times; it rejects
delivery delays over 250 ms and native calls spanning over 100 ms of simulation
time. Native rows include both flags and the raw fourth store-classification
byte. This byte is not yet a verified color mapping. Markers remain independent
human labels. The probe uses the existing diagnostic's 5 Hz rate, not the
production recorder's sampling contract. After installation, run a short
OFF/ON/OFF sequence and stop capture to verify the live in-process boundary.

`analyze_native_capture.py <dcs.log> <analysis.json>` checks paired sequence
counts, clean completion, clock alignment, stable Export identity, classification
and agreement between the two smoke flags. It reports measured transitions and
human markers separately. An error or missing native capture fails validation.
