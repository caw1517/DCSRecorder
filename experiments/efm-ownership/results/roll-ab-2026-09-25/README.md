# Live roll-rate A/B results — 2026-09-25

Process 32276, six mission starts. Captured native-motion.csv and filtered
mission-telemetry.txt while DCS was still running. Windows directory metadata
reported the open CSV as zero bytes, but reading/copying it retrieved the
flushed records. Runs ended at 26.06, 36.28, 31.32, 32.14, 36.72 and 16.08 s.
No run reached controller release at 43 s; do not claim release validation.
Every attempted pose command returned called; no intervention guard failed.

User observation: close to the lead, jitter remained throughout. With the
player flown away and viewing the lead in **F2**, the middle of the turn
looked perfectly smooth, then jitter returned near the end. Exact observed
transition timestamps were not supplied.

## Matching-time comparison

Compare the prior PID 44816 run and current run 2 for intervals beginning
at 15–29.98 s (750 intervals each):

| Measurement | Previous baseline | Roll rate cleared |
|---|---:|---:|
| Mean absolute roll change between commands | 1.07186 degrees | 0.06427 degrees |
| Mean maximum basis-axis change | 1.07782 degrees | 0.09530 degrees |
| Mean forward-axis change | 0.13075 degrees | 0.07307 degrees |
| Mean pre-command position error | 0.13899 m | 0.13913 m |

The roll change fell approximately 94.0%. Writing zero was verified, but
the next callback again observed roughly -0.05609 rad/s. DCS therefore
reintroduces angular motion between callbacks. After the intervention
ends at 30 s, roll disturbance builds back toward 1.075 degrees per tick.
This supports a causal contribution from native roll integration, without
proving that it explains every component of rendered jitter.

## Distance comparison

Mean player-to-lead separation during the available 15–30 s samples was
80.6, 25.6, 1724.1, 35.9, 25.2 and 987.9 m across the six runs.
Run 3 has fewer observer samples during this interval, so those are means
of available pairs only. Native logs preserve the full controlled interval
in runs 2–5.

Comparing each later run to run 1 at their common logged simulation times
found **zero numeric difference** in all recorded position and orientation
components before/after the command and in commanded pose (1,054 shared
samples each, except run 6 with 555). Aircraft separation did not change
those sampled lead states. This does not establish what happened at
render time, between samples, or in other native state.

Remaining hypotheses: residual angular/position corrections become visible
near the player; rendering/interpolation uses additional motion state;
distance from the player affects an unmeasured update/display path. The
F2 observation prevents simply attributing the difference to cockpit view.
No evidence here establishes wake turbulence as the cause.

summary.json contains per-run phase measurements; comparison.json contains
the matching-time baseline and distance comparison. Next investigation:
make commanded pose and native motion state consistent and distinguish
the remaining native corrections from presentation behavior. Keep the
playback feasibility decision open; this remains a pose-control probe.
