# First smoke observation and actuator test

Stock Hornet, white generator on mission station 10, DCS 2.9.29.27468.
The local `dcs.log` contains one complete take: 170 frames, 33.8 seconds between
first/last samples, uniform 0.2-second spacing. All argument chunks and the full
0–999 initial snapshot are present. Visible-state markers: ON at mission time
9.966, OFF at 27.938; explicit user stop. Only one labeled ON/OFF cycle was observed,
so this is not evidence of repeated transition correlation.

The sparse-log analyzer reconstructs all samples and rejects missing argument
chunks, frames and completion records. Thirty arguments changed. No clear binary
smoke signal appeared: the only changing channels with at most three values,
420 and 502, changed together near 31.748, after the OFF marker, and did not
separate ON/OFF windows. Other channels separated the sampled windows but varied
continuously (including known flaps/stabilators), so they are not a smoke mapping.
This bounds the finding to the sampled exterior arguments; it does not prove that
no native or cockpit smoke-state interface exists. Raw log and analysis JSON stay
local and ignored.

Installed primary sources provide an independent actuator candidate:
`MissionEditor/modules/me_action_db.lua` declares `SMOKE_ON_OFF` with boolean
`value`; WorldGeneral exports `SwitchSMOKE_ON_OFF` and its MovingObject command.
The existing Engine-Staged aircraft descriptor includes station 10's white store.

Prepared and installed **DCSRecorder-Smoke-Control-Test.miz** as a separate copy of
the accepted Test playback mission. Only the lead gains the white generator.
The existing motion/engine tape and native module remain unchanged. An additional
mission script sends `SMOKE_ON_OFF` through the lead's controller using its native
playback elapsed-time argument 996: ON at 3/13/23 seconds; OFF at 8/18/28 seconds,
with an initial OFF request. This is a synthetic actuator test, not recorded smoke
replay. A command returning without error does not establish visible emission.

Checks pass for targeting, timeline transitions, duplicate suppression, completion,
installed mission dependencies, route timing and saved Lua trigger syntax. The
installed mission hash matches the prepared artifact; six protected files are
unchanged. Local package/installation reports are under `package/smoke-control`.
Live rendered smoke remains pending. No new aircraft module or hook is installed,
so this test requires no restart. Use ordinary F10 playback start and report
whether smoke emerges from the lead and stops at the displayed requests.
