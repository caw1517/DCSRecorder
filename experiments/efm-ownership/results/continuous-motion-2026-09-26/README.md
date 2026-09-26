# Continuous motion matching result

DCS process 15412. User reported that the test worked like a charm.

The CSV records one capture, 1,901 successful commands, and one release at
43.02 s. Every successful command enabled motion matching. The last command
was at 43.00 s; no commands follow release and no failure status appears.
During the same 15–30 s comparison interval as the prior zero-wind run,
mean position correction remains 0.01820 m and mean attitude correction is
0.08461 degrees. `comparison.json` retains the measurements.

Independent mission telemetry continues to 49.7 s, providing approximately
6.7 s of post-release observation. The probe keeps moving and begins a
native turn after release. This verifies cessation of control and continued
object movement, but falls short of the protocol's ten-second observation
window. Do not label native recovery or aircraft physics fully validated.

Raw CSV, observer telemetry, summary, comparison and the tested DLL are
retained here. No video was supplied for this run. The successful result
supports progressing to the requested Hornet aircraft-compatibility test.
