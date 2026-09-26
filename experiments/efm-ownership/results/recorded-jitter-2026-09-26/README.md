# Recorded playback jitter: diagnosis and successful follow-up

## Follow-up result (26 September 2026)

The user ran the installed correction and reported **“SO much better.”** Session
45780 corroborates the improvement. All 1,940 pose commands and all 1,940
pre-physics motion restorations succeeded; release at 43.8 seconds reported
`step_hook_restored`. The same 7..42 second comparison window now has mean
position correction **1.883 cm**, p95 **3.230 cm**, maximum **3.891 cm**, versus
18.839 / 27.501 / 29.500 cm before. The velocity-overwrite metric is zero.

`check_jitter_trace.py <follow-up-trace> --assert-smooth --require-step-hook`
passes. `followup-summary.json` preserves the compact measurements; the raw
`native-motion-followup-45780.csv` is retained locally. The installed DLL SHA-256
is `8997882e816f388fd719a4492b318b09678677aaeb94007b53b9b167d1a1a473`.

This establishes a much smoother short recorded-flight baseline, supported by
both telemetry and user observation. It does not establish zero jitter, all
flight envelopes, physical-interaction fidelity, or other DCS builds. The dated
diagnosis and pre-test protocol below are retained as history.

User reported visible jitter in `C:/Users/w_can/Downloads/Jitter.mp4` after the
first actual flight replay. This 3.40-second 2560x1070 nominal-60-fps clip shows
close formation in a bank. `overview.jpg` is a contact sheet; it does not establish
frame-accurate correlation with the native telemetry.

## Baseline evidence

`native-motion.csv` copies session 8812 from the Hornet prototype. All 1940
commands succeeded. There are no missing 20 ms simulation callbacks. The
largest measured wall callback interval was 25.469 ms, maximum apply time 0.99 ms.
The saved flight itself is 1940 samples / 38.78 seconds; no pause was tested.

For consecutive commands in object time 7..42 seconds:

| Measurement | Mean | 95th percentile | Maximum |
| --- | ---: | ---: | ---: |
| Position correction before next command | 18.84 cm | 27.50 cm | 29.50 cm |
| Position error predicted from commanded velocity | 1.88 cm | 3.17 cm | 3.85 cm |
| Native velocity change from prior command | 9.51 m/s | 13.60 m/s | 13.67 m/s |
| Difference between native velocity and nose-aligned velocity | 0.114 m/s | 0.212 m/s | 0.212 m/s |

The earlier synthetic-roll session 39268 had position-correction mean 1.88 cm,
p95 3.19 cm, max 3.63 cm over the same object-time window. Its nose and velocity
were aligned; the real take contains several degrees of angle of attack.

The deterministic baseline check is RED:

```powershell
python experiments/efm-ownership/check_jitter_trace.py experiments/efm-ownership/results/recorded-jitter-2026-09-26/native-motion.csv --assert-smooth
```

Output: `FAIL: intertick position correction exceeds 6 cm (synthetic roll maximum was 3.63 cm)`.
This is a telemetry proxy for visible jitter, not a renderer-frame test. Three
hypotheses were considered: noisy capture, interpolation/derivative mismatch,
and a native update overwriting motion. Input integration and callback timing
support the third most strongly. Attitude correction also remains to be measured
after the change; eliminating all visible jitter is not yet established.

## Identified native behavior

Read-only disassembly found null-FM velocity reconstruction at DCS RVA
`0x6fa48b..0x6fa4c9`: scalar speed times aircraft forward basis is written to
complete-object `+0x25c..+0x264`. The controller calls this helper at `0x6fff17`.
The physics routine at `0x70fef0` subsequently integrates linear and angular
velocity. Its virtual dispatch at `0x675279` has a void, this-only call signature.

The jitter-session static snapshot verifies primary table RVA `0x1146200`,
physics slot byte offset `0xc70`, table length `0xdf0`, and current RTTI locator
pointers `0x133b650` and `0x133b770` at the two table boundaries. Older static
images had RTTI offsets 0x100 smaller; runtime guards use the current snapshot.

## Intervention awaiting DCS validation

Only `HornetRecordedProbe` enables the test. After the existing object-ID,
identity, null-FM, pose, altitude and motion guards pass, it gives this one
playback object a private copy of its primary virtual table, preserving the
RTTI locator and every slot except physics-step dispatch. Shared tables and
executable pages are untouched. Before the original physics step runs, the
wrapper restores the latest recorded linear and angular velocity, validated
again. It preserves the recorded nose attitude and all samples.

Each command can be consumed once, on the installing simulation thread only.
Missing commands cannot keep an old override running. Playback release, a failed
guard, and destruction disable it and restore the object's original table if
still owned. Destruction's own replacement table is never overwritten. The
private table storage stays alive for the DLL lifetime. Existing single-object,
single-player, calm-air and specific-DCS-build limits remain.

Eight CTests pass. The new mock-boundary test exercises the observed ordering
(motion command, velocity overwrite, native integration), table/RTTI copying,
unrelated-object isolation, once-only command consumption, thread rejection,
release and destruction ownership. It does not execute DCS's integrator. Python
recording/import/mission validation checks pass as well.

Next run the unchanged `EFM-Probe-Hornet-recorded-flight.miz`. Compare the new
`native-motion-<pid>.csv` using:

```powershell
python experiments/efm-ownership/check_jitter_trace.py <new-trace.csv> --assert-smooth --require-step-hook
```

Check `step_hook_installed`, increasing step-hook counters, actual restoration,
release, and visual smoothness. Native velocity may be rebuilt again after the
physics step, so the decisive metric is reduced position correction plus visual
confirmation, not the old `velocity_before` field alone. No post-change live run
has been made yet. The original telemetry must remain red; do not rewrite it.
