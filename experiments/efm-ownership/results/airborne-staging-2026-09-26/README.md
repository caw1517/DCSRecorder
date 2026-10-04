# Accepted stock-aircraft staging experiment

The user reported **"Complete and working"** on 26 September 2026. The preserved
DCS 2.9.29.27468 log supports the first stock-Hornet staging run. This establishes
a staging candidate, not complete recorded playback or exact initial state.

| Observation | Result |
| --- | --- |
| F10 Start | Mission time 10.351 s |
| Three-second countdown finished | 13.351 s |
| Actual release | 13.801 s |
| Maximum held player position drift | 0.000 m across 691 samples, at logged precision |
| First simultaneous player/lead separation | 45.714467 m; target 45.72 m / 150 ft |
| Lead removal | 23.801 s, ten seconds after release |
| Player samples after removal | 267 |

The one-shot trigger added **0.450 s** after the countdown. The eventual playback
clock must use the actual release/activation handshake, not the countdown deadline.
The player remained stationary through that delay.

The reference lead's first position was (-315220.500000, 1992.211426, 897667.562500)
metres versus recorded (-315220.506096, 1994.594527, 897667.565803): about **2.383 m
lower**. The stock spawn was level with zero vertical velocity, so recorded attitude
and velocity were not reproduced. Native-controller initialization remains required.

The user confirmed the visible behavior. Telemetry contains one staging run only;
longer waits, mission restarts and multiple frame rates remain unverified. No
independent recording ran during this experiment. The full workflow and exact-start
tickets remain open.

Decision: use Active Pause, F10 countdown and late activation as the demonstrated
candidate for the next recorded-playback integration experiment.

Evidence: local `dcs-staging.log` and `summary.json`. Snapshot SHA-256:
`E510139A54DF960D1791BAB867FCBBCF0B18F5EEF68A30F9DE776018642C8A20`.
The source prototype is preserved on `codex/airborne-staging`, commit `7a4b01a`.
The running simulator held its log open; analysis used a preserved shared-read
snapshot, leaving the simulator's log unchanged. Raw logs remain local.
