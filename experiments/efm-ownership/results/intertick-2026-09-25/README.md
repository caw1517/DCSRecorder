# Inter-update roll conflict measured

Run PID 44816, 2026-09-25. All 1901 commands executed from simulation time 5 through 43; 1900 intervals are exactly 20 ms. Analyze with `python experiments/efm-ownership/analyze_intertick.py experiments/efm-ownership/results/intertick-2026-09-25/native-motion.csv`.

Maximum per-axis orientation differences, computed with cross/dot atan2:

| Quantity | Mean | Maximum |
| --- | ---: | ---: |
| Pre-command vs current target | 0.8784 deg | 1.1931 deg |
| Immediate post-command vs target | 0.00000080 deg | 0.00000239 deg |
| Pre-command vs previous applied pose | 0.8765 deg | 1.0835 deg |
| Intended command-to-command change | 0.0936 deg | 0.2961 deg |

At model time 20 s, forward/up/right axes change by 0.1364/1.0810/1.0775 degrees between commands. At 40 s these changes are 0.0058/1.0758/1.0758 degrees. The dominant disturbance is therefore rotation around the forward axis (roll), not merely progress along the commanded yaw/pitch path. The controller repeatedly corrects this disturbance. It is a strong explanation for the observed wing chatter, but renderer timing has not been captured to correlate each visible jump.

Wall intervals average 20.000 ms, p95 22.875 ms, max 34.147 ms. ForcePosition application including guards averages 0.498 ms, max 1.985 ms. There are no missed simulation-time callbacks; these values do not rule out rendering stalls or prove the cause of every visible artifact.

Pre-command position error relative to the current target averages 0.1395 m and peaks at 0.2306 m. Position tracks much more closely than pre-command attitude. Existing after-call-only telemetry concealed the attitude conflict.

Next technical target: determine which rotational state or AI update advances roll between pose commands and whether it can be synchronized with the trajectory. Do not claim that zeroing an assumed angular-velocity field is correct; identify its semantics and update order first. No controller behavior was changed in this diagnostic run.
