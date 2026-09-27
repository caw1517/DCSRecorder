# Stabilator animation timing: live pass

The user tested **DCSRecorder-Stabilator-Animation** and reported: “Much better,
everything looked great.” This accepts the visible stabilator behavior in the
isolated exterior-state test on DCS 2.9.29.27468.

The retained PID 26500 traces corroborate that review:

- 5,659 native callbacks over 113.16 seconds; 2,262 later mission observations.
- All 11,318 post-animation channel rows show a native overwrite before repair
  and an exact match with the requested value after repair.
- Both stabilators have zero immediate and next-callback error. Later mission
  errors round to zero at six decimal places (CSV serialization precision).
- During pitch, argument 15 follows approximately -0.907..+0.590 and argument 16
  -0.909..+0.590. The observed ranges now match, unlike the failed earlier tests.
- `animation_hook_installed` is followed by `animation_hook_already_replaced`
  and `destroy` at mission time 115.99. DCS had replaced the object table before
  destruction; the wrapper released its ownership without overwriting that table.

The retained-trace assertion passes:

```powershell
python experiments/efm-ownership/state-prototype/check_retention.py `
  experiments/efm-ownership/results/stabilator-animation-2026-09-27/state-26500-271411265.csv `
  experiments/efm-ownership/results/stabilator-animation-2026-09-27/dcs.log `
  --assert-stabilators
```

The source snapshot, native/mission traces and derived JSON stay local and ignored.
The experiment source is commit `2a29a96`. The key finding is that replay must
apply these values after the native animation update, which runs after physics.
The earlier post-physics boundary was insufficient.

## Scope of acceptance and next step

The stabilator jitter repair is verified visually and numerically for this run.
Other tested surfaces were visually accepted by the user, but smaller numerical
overwrites persist on some of them. Do not claim exact full-channel retention.

This run ended before the 130.55-second sequence completion and final eight-second
hold. Interrupted destruction is observed; automatic end-of-sequence cleanup
still needs coverage in the integrated test. No extra repeat of this isolated
mission is required before preparing that test.

The next implementation step is to carry the exterior channels through normal
recording, storage and staged playback with one source clock and initial snapshot.
Keep old recordings readable without inventing missing state. Combine motion and
animation interception under one per-object table owner: the two isolated wrappers
both replace that table and cannot simply be installed independently on the same
aircraft. Verify the combined motion/appearance lifecycle before deployment.

Suspension, wheel spin, canopy, smoke, lights, separate nozzles, afterburner effects
and sound remain later state groups. The visual/engine-state issue stays open.
