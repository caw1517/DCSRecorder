# Player control with independent telemetry

The corrected mission-start observer ran successfully. Retained evidence is in `callbacks.csv` and `observer.txt` beside this report.

- The EFM recorded 1,329 simulate calls and 1,329 state calls over 7.974 simulation seconds, ending in a release event.
- Independent mission telemetry identifies the aircraft as `Probe` and samples through 7.9 seconds.
- The observer up vector remains (0, 1, 0) at 4.9 and 5.0 seconds. It starts changing at 5.1 seconds, during the programmed 5.0–5.5 second roll pulse, and reaches (0.069383, 0.997537, 0.010279) at 7.9 seconds, approximately 4.0 degrees from vertical.
- Positions follow the same trajectory in the callback and mission-observer records. Their sampling times differ; this is an ownership/response check, not a position-error benchmark.

The player-occupied positive control now has both callback evidence and an independently observed attitude response consistent with the diagnostic pulse. Although shorter than the requested 15 seconds, the run covers the complete pulse and its aftermath. No further player-control repeat is needed for the ownership comparison.

Next: restart DCS and run EFM-Probe-ai. Confirm independent observer rows for both Probe and Observer. Check for fresh EFM callbacks after that restart. Missing callbacks are meaningful only if the AI target actually spawned and was observed. The known probe damage-model errors still preclude physical-fidelity conclusions.
