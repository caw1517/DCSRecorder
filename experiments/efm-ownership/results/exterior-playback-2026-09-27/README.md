# Exterior actuator: stabilator overwrite reproduced

DCS 2.9.29.27468, process 44256; separate exterior SDK experiment.
The user found gear, flaps, ailerons, rudders and speed brake visually satisfactory,
but reported both stabilators flickering with almost no visible travel. That is
visual acceptance for those observed channels, not a full-fidelity measurement.

## Reproduction

Preserved local artifacts: `dcs.log`, `state-44256-268908328.csv`, and
`events-44256-268908328.csv`. The snapshot contains 6,797 native callbacks through
135.92 elapsed seconds. Native `sequence_complete` is present; the snapshot ends
during the final hold without a mission END or destruction event. Do not infer a
completed lifecycle test from this snapshot.

```powershell
python experiments/efm-ownership/state-prototype/check_retention.py experiments/efm-ownership/results/exterior-playback-2026-09-27/state-44256-268908328.csv experiments/efm-ownership/results/exterior-playback-2026-09-27/dcs.log --assert-stabilators
```

Result: `FAIL: stabilator values do not survive to mission observation: 15, 16`.
The comparator matches mission-reported playback time to a native callback within
1 ms; the actual playback callback interval is 20 ms. The 0.01 normalized-unit
p95 check is a diagnostic threshold, not an agreed product fidelity tolerance.

| Channel | Immediate write error | Next-callback mean absolute error | Mission mean absolute error | Mission p95 error |
| --- | ---: | ---: | ---: | ---: |
| 15 | 0 | 0.112297 | 0.112254 | 0.601646 |
| 16 | 0 | 0.111757 | 0.111722 | 0.596708 |

During the pitch segment, matched requests span -0.907..+0.590 and
-0.909..+0.590, while mission observations span only +0.004..+0.093 on both.
This independently supports the reported near-stationary stabilators.
All immediate channel readbacks exactly match requests. Other channels show
smaller later differences: for example leading-edge flaps differ by about 0.01
normalized units and ailerons have p95 differences of about 0.02. The visually
accepted channels are therefore not proven numerically exact.

## Hypotheses and intervention

1. Native animation overwrites SDK writes between callbacks. Prediction: a later
   write phase restores the requested stabilator motion. The immediate/next/
   mission data strongly supports the overwrite mechanism, but does not identify
   the final rendering phase.
2. Additional model channels compete with 15/16. Prediction: correct retained
   argument values still fail visible review. Not excluded until a retained-value
   run is visually inspected.
3. Clock misalignment creates an apparent error. The comparator's callback-clock
   match and independent next-callback evidence argue against this explanation.

The existing native-step fixture was extended to reproduce a native update
replacing a recorded stabilator value. It first failed with
`native animation erased recorded stabilator`; optional after-step delivery made
it pass. Existing before-step motion behavior, foreign-thread suppression and
ownership restoration also pass. All 13 CTests passed after rebuilding.

This is a testable intervention, not a verified DCS fix. The separately registered
`DCSRecorder-Hornet-State-PostStep` writes the same tape through the same SDK, then
reapplies only 15/16 after the guarded native step. It verifies current-build
signatures, object identity and the known null-FM route; rejection stops the test.
It logs the before/after values at that additional phase, and restores the shadow
table on destruction or failure. It does not change aircraft pose or velocity.

The new mission is `DCSRecorder-Exterior-State-Stabilator.miz`, installed directly
in Saved Games/DCS/Missions. All ten installed files match its manifest. The
accepted installed playback module remains unchanged; after regression building,
its byte-identical DLL was restored as the companion's prepared packaging input.
The experimental regression build is retained separately in the ignored build
directory. No new main-recorder schema or production state playback is shipped.

## Live gate

Restart DCS, run the stabilator comparison, use the same F10 start and F2 lead
view, and inspect the pitch phase around 36-51 seconds. Re-run the retention
comparator on the new trace and check `post-step-*.csv` and hook-restoration events.
Visible improvement, retained values and successful restoration are all required.
If a later native animation update still wins, this timing intervention is not
the fix and the ownership investigation continues.
