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
missions remain local and ignored. Remaining work: analyze repeated transitions,
find an actual emitter control for playback, validate appearance/color/timing,
then extend the recording contract with measured state and loadout metadata.

`analyze.py <dcs.log> <analysis.json>` validates and reconstructs sparse snapshots.
The first capture did not identify a clear smoke-state argument. The separate
`prepare_control.py` builds **DCSRecorder-Smoke-Control-Test.miz** from the accepted
Test playback mission and checks the active tape hash. It adds white smoke only
to the lead and requests three five-second bursts via the installed mission
command `SMOKE_ON_OFF`. Start via the ordinary F10 playback menu. This synthetic
sequence tests visible actuation independently from smoke-state capture; it does
not turn the user's visible-state markers into purported recorded smoke data.
