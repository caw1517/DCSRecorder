# One-shot position change propagated

DCS PID 47372, 2026-09-25. Installed probe SHA-256 `CCE944D957F19E66302E6CEBD26F7992FEA9B11B0B619F8105460F7DE0E10E5B`. One motion row records `called` at object time 5.0. Runtime mapping identifies Probe as 16777472 and Observer as 16777728.

The immediate native before/after pair changed X from -315219.4375 to -315199.4375, exactly +20 m. Y and Z were unchanged. Independent mission telemetry at time 5.0 likewise differs from the previous unmodified run by exactly +20 m in X and zero in Y, Z, and the three logged up-vector components.

The Probe mission telemetry matches the unmodified baseline exactly in all six logged position/up-vector components through time 4.9. After the call, it does not snap back. The X difference evolves as follows:

| Mission time | X difference from baseline |
| ---: | ---: |
| 5.0 s | 20.000000 m |
| 6.0 s | 19.975559 m |
| 8.0 s | 19.390335 m |
| 10.0 s | 18.056947 m |
| 12.0 s | 16.236102 m |
| 13.0 s | 15.228898 m |

Attitude begins diverging after the call. The gradual correction is consistent with an AI route-following response, not an immediate overwrite; the controller's intent was not instrumented. Baseline overlap ends at 13.1 seconds. The shifted run continues to about 24 seconds, but no baseline comparison is claimed beyond the overlap. The player-controlled Observer differs between runs and is not a deterministic baseline.

Conclusion: one guarded native ForcePosition call can move this unoccupied aircraft while the user occupies another aircraft in the same DCS instance. The changed position propagates to independent mission telemetry and persists across subsequent updates. This establishes a bounded position-control primitive, not faithful trajectory playback, independent attitude/velocity control, collision/wake fidelity, or compatibility across builds.

Evidence: native-motion.csv, native-body.csv, native-types.txt, dcs-excerpt.txt, and baseline-comparison.json. Baseline: ../object-position-2026-09-25/dcs-excerpt.txt. Comparison matches Probe rows at identical mission timestamps and subtracts baseline XYZ/up-vector from this run's values.

Next experiment: a short time-based trajectory with bounded repeated pose updates, measured tracking error, and a defined release point. That must test whether AI correction can be managed without corrupting velocity or attitude. Physics validation remains a separate gate.
