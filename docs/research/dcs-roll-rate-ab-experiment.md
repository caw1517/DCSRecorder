# Roll-rate A/B diagnostic

Prepared 2026-09-25 for DCS 2.9.29.27278. Live result pending.

Update: six live runs were analyzed in
[the result note](../../experiments/efm-ownership/results/roll-ab-2026-09-25/README.md).
Matching-time mean roll disturbance fell about 94%, from 1.07186 to
0.06427 degrees. Close-range visible jitter remains. Recorded lead poses
matched across runs despite large differences in player separation.
The user observed the smooth distant interval in F2. Release was not tested
because all runs ended before 43 s. The following sections describe the
original experiment setup.

The previous run (PID 44816) measured a mean 0.8765 degree attitude change
between commands, versus 0.0936 degree mean intended command step. Near 40 s,
the forward axis changed only 0.0058 degrees while up/right changed about
1.0758 degrees. This suggests competing roll integration. It does not yet
prove the correspondence to rendered wing jitter.

## Static evidence

In the captured DCS image, the null-flight-model update at RVA
0x712408..0x712541 reads float angular rates from complete woAIPlane
+0x1e8/+0x1ec/+0x1f0 and applies:

    dForward = (wz * up - wy * right) * dt
    dUp      = (wx * right - wz * forward) * dt

It then normalizes the basis. Thus +0x1e8 is local roll rate. Independently,
WorldGeneral's exported MovingObject::VectorAngular at RVA 0x305b0 returns
receiver+0x1e0; this equals complete+0x1e8 for the verified +8 callback
subobject. The other roll rotation block at RVA 0x712b69 is conditional and
has not been established as the live airborne branch.

Cached Euler fields also exist: complete+0x2118 is atan2(-forward.z,forward.x)
wrapped positive; +0x2120 is atan2(-right.y,up.y); +0x2128 is pitch. These
are not modified in this experiment. Stale caches, AI recomputing rates,
and renderer interpolation remain alternatives to a persistent roll rate.

## Intervention and predictions

Use the existing EFM-Probe-climbing-turn-formation.miz for 55 seconds.
The trajectory, speed and formation placement are unchanged.

- 5–15 s: pose commands only, baseline.
- 15–30 s: after each successful pose command, write zero to only the probe's
  local roll-rate float and verify readback.
- 30–43 s: pose commands only again.
- After 43 s: all commands cease.

This is a single-variable diagnostic, not a finished controller. The write
requires all existing object/type/build/altitude/pose guards, plus an exact
signature for the roll-rate load at RVA 0x712435 and finite angular rates
within 10 rad/s. Failure aborts control. It does not patch executable code.
Only the dedicated probe runtime ID is eligible.

If the existing rate persists into integration, roll disturbance should fall
in the middle interval. If AI replaces it before integration, the next
callback can show a renewed rate and unchanged disturbance. A reduced
numeric disturbance without visible improvement would point toward another
rendering or timing cause. No live conclusion is claimed yet.

## Measurement

native-motion now appends roll_neutralized and three angular rates before
and after each command. analyze_intertick.py groups interval measurements
by the intervention at the *previous* callback, avoiding an off-by-one
at the on/off boundaries. Compare against the saved unmodified run at
matching mission times as well: the three phases have different commanded
bank angles, so their aggregate means alone cannot establish causality.

Build and both existing CTests passed. The actual competing native update
requires DCS; offline geometry/ABI checks do not verify the jitter fix.

Installed DLL SHA-256:
79A80B3DD80FF24C33A02125C2404D437BC8520997B1081D1FE426A7F60BD637.
The previous DLL is preserved beside the intertick baseline results.
The analysis was checked against a synthetic one-degree roll and a phase
boundary, and still reproduces the previous baseline metrics.
