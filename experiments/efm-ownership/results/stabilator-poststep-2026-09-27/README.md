# Post-physics timing failed; later animation boundary prepared

The user supplied `Stabilator.mp4` (10.72 seconds, 2560x1070) showing continued
stabilator jitter during the pitch phase. Consecutive extracted frames corroborate
the report; no angular accuracy is inferred from the video.

The preserved DCS log and `state-11404-270008281.csv` contain two interrupted
mission runs, ending at elapsed 35.14 and 54.24 seconds. Both installed the hook
and released ownership on destruction (`step_hook_already_replaced`: DCS had
already replaced the object's table). Neither reached sequence completion.
Raw logs, video derivatives and binary analysis outputs remain local/ignored.

All 8,942 post-step rows have identical requested, before and after values. The
physics callback therefore repairs nothing at this boundary. Later mission reads
still disagree. `check_retention.py` now separates mission restarts (whose IDs and
elapsed clocks repeat) and defaults to the last run. It rejects mismatched run
counts instead of silently combining samples.

Reproduction from the repo root:

```powershell
python experiments/efm-ownership/state-prototype/check_retention.py `
  experiments/efm-ownership/results/stabilator-poststep-2026-09-27/state-11404-270008281.csv `
  experiments/efm-ownership/results/stabilator-poststep-2026-09-27/dcs.log `
  --assert-stabilators
```

Run 2 of 2 fails for both stabilators. Immediate maximum error is zero. Mission
mean absolute errors are 0.117818 (15) and 0.116476 (16), with p95 errors 0.471516
and 0.431309 in normalized argument units. During pitch, requested ranges are
approximately -0.907..+0.590 and -0.909..+0.590; observed ranges remain
+0.004..+0.093 for both. This rules out the previous timing change as a fix.

## Installed-build evidence

Read-only analysis of the existing PID 11404 static-image snapshot, DCS build
2.9.29.27468, establishes the following order (addresses are image-relative):

1. Dispatch at `0x675279` calls primary-vtable slot `0xc70` (physics step).
2. Dispatch at `0x6752a5` subsequently calls slot `0xc10`, target `0x6b6070`,
   forwarding `this`, a double timestep in XMM1 and a Boolean in R8B.
3. This later update calls `0x6692f0` at `0x6b73a7`. That routine loads the draw
   argument array through object offset `0x750` and writes float offsets `0x3c`
   and `0x40` (arguments 15/16), including in its null-FM path. For example,
   writes at `0x66a4b2` and `0x66a4d5` derive the two values from native controls.

This explains a concrete later overwrite path. It does not prove that no other
writer runs afterward; live telemetry and rendering are still required.

## Next controlled experiment

`HornetStateAnimationProbe` uses a separate typed per-object shadow table at
slot `0xc10`. It forwards all original arguments, runs the original update, then
reapplies only stabilators 15/16 via the SDK. It repeats on each animation call
while the latest captured sample is valid. Identity/null-FM, owner-thread,
table-boundary, entry-prologue, dispatch-callsite and nested-writer-call guards
reject an incompatible object or build. Executable pages/shared tables are not
modified. This remains an isolated, build-specific diagnostic prototype.

`state_animation_check --reproduce-early-boundary` fails with
`later animation erased post-physics stabilator write`. The new boundary passes
the same overwrite sequence, timestep/Boolean forwarding, repeated callbacks,
other-object/thread isolation, table preservation and restoration. All 14 CTests
pass. The built SDK baseline also passes all 2,612 real captured samples and
interpolation/lifecycle guards; the animation DLL rejects a fake object before
surface or native writes. These are offline checks, not live acceptance.

The package `package/exterior-state-postanimation` contains the same source tape,
route and clock. The new `DCSRecorder-Hornet-State-PostAnimation` module and
`DCSRecorder-Stabilator-Animation.miz` were installed directly in Saved Games.
All ten files match the package manifest. Accepted motion DLL/tape hashes remain
unchanged. DCS was running, so a full restart is required to load the new module.

Restart DCS, run **DCSRecorder-Stabilator-Animation**, use the existing F10 start
and F2 lead view, and watch pitch around 36–51 seconds. Let the 130.55-second
sequence and eight-second endpoint hold finish. Collect `post-animation-*.csv`,
`state-*.csv`, events and DCS log, then compare later reads and visual motion.
The bug and visual/engine-state ticket remain open until that live result passes.
