# Zero-wind control for motion matching

Prepared and tested 2026-09-25. DCS 2.9.29.27278.

Live result: [zero-wind comparison](../../experiments/efm-ownership/results/zero-wind-2026-09-25/README.md).
Mean matched-phase position correction fell from 14.17 cm to 1.82 cm
(87.16%); angular correction remained approximately 0.08567 degrees.
The user reported a massive visual improvement and accepted zero wind as
a mission requirement. Wind compensation is deferred. Generated probe
missions now enforce static weather, zero wind in all three layers and
zero ground turbulence. The installed DLL is unchanged. The run ended at
34.64 s, before controller release. The sections below retain the original
comparison procedure and predictions.

The prior motion-matching runs improved visible jitter, while requiring
mean position corrections of 0.14174 m during 15–30 s. The measured
intertick drift closely matched the mission's 7 m/s wind at 2,000 m.
See [the baseline results](../../experiments/efm-ownership/results/motion-matching-2026-09-25/README.md).

This control isolates that existing wind hypothesis. It is not a jitter
fix or evidence that all remaining motion error comes from wind.

## Prepared comparison

`experiments/efm-ownership/prepare_zero_wind.ps1` copies the actual installed
`EFM-Probe-climbing-turn-formation.miz`, changing only the static wind
speeds at ground, 2,000 m and 8,000 m from 5/7/10 m/s to zero. Directions,
other weather, aircraft, triggers, options and trajectory remain identical.
The output is `EFM-Probe-climbing-turn-formation-zero-wind.miz`.

Verification executed successfully with the installed Lua interpreter:

    PASS: mission tables differ only in three wind speeds (5/7/10 -> 0/0/0).

The packaging script additionally verifies every archive member's
uncompressed contents and confirms the original mission's hash is unchanged.
The verification record is `experiments/efm-ownership/package/zero-wind-verification.json`.

The installed motion-matching DLL was checked, with SHA-256
`6722E4E3C82243DC9852DCDAB5278F7B5FF7E85EFFC40A730C8D911A47F90591`.
No DLL changes are part of this control.

## Live feedback loop

Open the zero-wind mission in DCS and fly for at least 55 simulation seconds.
Observe close formation during 15–30 s and continue past release at 43 s;
neither of the previous two runs reached release. Note whether jitter
changes around 15 s and 30 s. Keep the previous graphics and camera settings.

After the run, preserve the new native-motion CSV and mission telemetry,
then run `analyze_intertick.py <new-csv>` and compare the matched phase with
the baseline's 0.14174 m mean position and 0.08566 degree mean attitude
corrections. Compare intertick displacement against the previous written
velocity as in the baseline wind analysis.

Predictions:

1. If added wind explains the position drift, zero wind should substantially
   reduce the position corrections and remove the approximately
   (2.52, 0, -6.50) m/s residual. Native angular-rate changes can remain.
2. If native translational integration creates the residual independently
   of wind, comparable systematic drift should remain in this control.
3. If measured corrections fall but visible jitter remains, the residual
   angular motion and rendering/timing need separate discriminating tests.

Do not infer a visual fix solely from telemetry. DCS flight and the user's
formation observation are the current human-in-the-loop discriminator;
offline mission checks establish experiment isolation, not live smoothness.
Keep wind compensation and further angular interventions out of this run.
