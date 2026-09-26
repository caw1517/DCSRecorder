# Aircraft position correspondence established

DCS PID 41496, 2026-09-25. All 130 native samples from object time 0 to 13.1 seconds passed the guarded candidate-position read. Same-run hook mapping identifies Probe mission ID 9001 as runtime ID 16777472; Observer is runtime ID 16777728. Runtime class and primary vtable match the previous woAIPlane observations.

Reproduce with `python experiments/efm-ownership/compare_position.py experiments/efm-ownership/results/object-position-2026-09-25`.

The comparison linearly interpolates independent mission telemetry at each native sample time, excluding samples outside the telemetry interval. It tests delays from -100 to +100 ms in 1 ms steps. A positive delay means native timestamp t corresponds to mission timestamp t-delay.

| Comparison | Pairs | RMS difference | Maximum difference |
| --- | ---: | ---: | ---: |
| Probe, identical timestamps | 128 | 2.9182 m | 2.9533 m |
| Probe, native time minus 20 ms | 128 | 0.02054 m | 0.03381 m |
| Observer, same 20 ms adjustment | 128 | 1025.76 m | 1053.92 m |

The best fitted delay is 20 ms, consistent with a simulation-step sampling offset, but this does not establish callback ordering independently. Residual differences are consistent with float precision at these world coordinates plus interpolation; they are not a measured simulator error. The delay is fitted on this same run, not independently calibrated.

Conclusion: the float triplet at complete woAIPlane +0x1ac corresponds to the tested aircraft's world position. This establishes build-specific read access alongside the occupied player using one account. It does not establish velocity, attitude, writable authoritative state, motion control, collision/wake response, or faithful playback. No aircraft state was written.

Next gate: trace how DCS commits and propagates position/orientation changes and which update overwrites them, before designing a bounded control experiment. Repeating this read-only test unchanged is unnecessary.
