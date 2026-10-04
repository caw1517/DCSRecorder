# Roll nose-direction investigation — 26 September 2026

Status: the user reports **“No jump. Worked great.”** The corrected live replay
passes the pose and motion checks and completes the full recording. The final
build is installed with temporary diagnostic logging removed.

## Verified outcome

The cause supported by the matched live comparison is an extra pitch rotation
in DCS's null-FM presentation path, applied on top of the recorded nose attitude.
Suppressing that contribution on the dedicated playback aircraft removed the
reported jump without changing the recording or commanded flight path.

Process 5832 contains four starts, including one complete 39.48-second run with
1,975 successful commands. The full third run's maximum nose discrepancy after
allowing either adjacent 20 ms controller sample is **0.0088 degrees**, compared
with **10.0662 degrees** before correction. The other captured runs also pass
the pose check; three are partial runs. Cached extra-pitch prediction is zero.
Without the adjacent-sample allowance, maximum cached-versus-command nose angle
is about 0.162 degrees, consistent with the remaining sample/extrapolation offset.

The existing motion regression check also passes: p95 position correction is
3.165 cm, maximum 3.731 cm, recorded velocity overwrite is zero, and all 4,577
samples in its existing comparison window confirm the pre-integration hook.
Native completion and `step_hook_restored` are present; the mission reports
`COMPLETE` at 46.300 seconds. Evidence is in `corrected-5832/`.

Temporary pose logging and its build option have been removed from active
source. The correction now applies by default to staged playback; the legacy
prototype targets remain unchanged. All 12 CTests pass after cleanup. The
captured-value boundary test still reproduces the old extra rotation in baseline
mode and verifies clearing, isolation and restoration in corrected mode.

After the user closed DCS, the final DLL was installed and hash-verified:
`8206cf4dc4b549b6f36edb771abe412f4ef2fe88b6f1e5c66d8a55c07f4b145d`.
`final-installation.json` records its rollback copy. Live validation used the
preceding instrumented correction build; the final build removes logging and
keeps the same correction. No additional live run of the final build is claimed.
This validates this roll and DCS build, not every maneuver or DCS version.

## Earlier installation and diagnosis

Installed after the user closed DCS, at 2026-09-27 00:23:19 UTC (26 September
local time). `pitch-test-installation.json` records the verified DLL hash,
rollback location and unchanged tape hash. Installed DLL SHA-256:
`5d954231c550dc6a8aec4feacd6c53af1ea7f0c8a682bf306be9ccd717d1c728`.

## Diagnostic follow-up

The user confirms a similar symptom in the earlier hard-coded roll tests.
The contemporaneous `../roll-video-review-2026-09-26/README.md` also records
unexplained pitch motion near inversion and recovery. This lowers the priority
of the recorded-flight sampler as a cause; it does not establish that both
reports have the same cause.

Read-only inspection of the saved native image identifies an additional
presentation path at DCS RVA `0x6d3870` (`Position(double)`, MovingObject table
slot `0x70`). It starts from the native basis but applies further local rotations
and extrapolation, then stores a cached pose at callback-handle `+0x217c` with
cache time `+0x4d68`. The existing controller reads the base pose at `+0x174`.
The two readbacks are not equivalent.

In that path, `+0x56cc` and `+0x56d4` contribute a rotation of the forward/right
axes. `+0x4db4`, `+0x22b4` and time `+0x5870` contribute an additional rotation
of the forward/up axes, using degrees-to-radians conversion. These are observed
operations; the semantic names of the internal fields are not yet established.
Do not assume they are angle of attack or write zeros to them without measurement.

Installed a temporary opt-in `DCS_POSE_DIAGNOSTICS` build in the existing staged
mod. It only reads these fields, cache times and poses before/after normal motion
commands. It performs no additional game-state writes or native calls. The
position-entry signature is checked before reading the extra fields. Logging
uses `DEBUG-nose-pose-<pid>.csv`; source is `pose_diagnostics.h` in the existing
worktree. Default builds leave this instrumentation disabled.

All 11 existing CTests pass. `diagnostic-installation.json` records the installed
SHA-256 and verified rollback DLL. The 39.48-second tape and mission are unchanged.
Live protocol: replay `DCSRecorder-Playback-d7a5d25a.miz` through completion and
report whether the nose jump remains. Capture the new diagnostic/native/log
files and run `analyze_presentation.py` to compare measured local rotation with
the extra fields. This is instrumentation, not a proposed fix. Remove the
temporary instrumentation after the causal test and final verification.

The diagnostic replay (process 18468) completed the full 39.48-second tape, and
the user again saw the jump. At elapsed 18.76 s, cached pose versus commanded
pose differs by 10.21123 degrees at the nose. The observed fields predict
10.07575 degrees of extra local pitch; measured local pitch is 10.21094 degrees.
The remaining approximately 0.135 degrees includes presentation extrapolation
and sampling alignment. Additional local yaw fields and the other rotation flag
are zero at this point. `diagnostic-18468/presentation-analysis.json` retains the
measurements and the run's raw logs remain local.

Prepared `DCS_SUPPRESS_PRESENTATION_PITCH`, an opt-in staged-DLL test which clears
only the measured pitch and pitch-rate contribution immediately before the
existing native integration call. Runtime instruction signatures, existing
identity/null-FM/object/thread/altitude guards and finite field bounds apply.
The helper verifies both writes and restores the last overridden values on
release if DCS has not already supplied newer values. It does not write the
cached pose, sampled recording, base orientation, yaw contribution or mission.
Existing motion restoration remains enabled. No executable DCS pages change.

The new boundary test uses the captured pitch/rate values and the observed
presentation calculation, invokes the actual clearing/restoration helper on
owned test memory, and verifies unrelated bytes, wrong-object rejection,
repeated clearing, restoration, and preservation of newer engine state.
`presentation_pitch_check --baseline` exits 1 with an extra 10.0757 degrees;
`presentation_pitch_check` passes. All 12 CTests pass. This test models the native
presentation boundary; it does not execute DCS's private presentation routine
or establish a visual fix. The same mission must still pass the captured-trace
check and user observation after installing the correction.

The user reports a short nose-direction change during a roll, around a quarter
roll, and confirms it occurs at the same point on repeated playbacks. The local
clip is `C:/Users/w_can/Downloads/NosePitch.mp4` (about 3.42 seconds). Decoded
contact sheets are retained here. The clip does not include a playback-clock
overlay, so its exact correspondence to a telemetry timestamp is unconfirmed.

## Inputs

- Saved take: `C:/Users/w_can/Saved Games/DCS/DCSRecorder/recordings/20260926T224052Z-0001.csv`.
  1,975 samples, 39.48 seconds, 20 ms spacing, DCS 2.9.29.27468.
- Captured `dcs.log`, `native-motion-15596.csv` and `objects-15596-256648734.csv`.
  Four starts of the same installed playback package are present.
- The third run completes the full take; the other runs end earlier.

## Measurements

`analyze_trace.py` measures controller correction against its native pose
readback. After the first 0.2 seconds, maximum basis correction is approximately
0.00249 degrees across the four runs. This readback alone misses the discrepancy
below and is insufficient as a visual-fidelity acceptance check.

`check_continuity.py` measures sample spacing and angular steps:

- Source and controller samples have 20 ms spacing. Largest forward-axis step
  is approximately 0.16235 degrees; largest up-axis step is 0.53532 degrees.
- Mission samples have the same spacing, but their maximum forward-axis step
  is about 0.37890 degrees.
- Comparing mission `Unit:getPosition()` axes against controller axes finds a
  forward-axis discrepancy of 10.20218 degrees at playback elapsed 18.759 seconds
  in every run. The recording's bank at about this time is 129.85 degrees.

The reusable captured-trace check allows either neighboring native sample to
avoid mistaking callback order for the orientation discrepancy:

```powershell
& 'C:\Users\w_can\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' experiments/efm-ownership/results/nose-pitch-2026-09-26/check_pose_boundary.py
```

Observed output, exit code 1:

```text
FAIL run 1: nose discrepancy 10.0662 deg at 18.759s, aligned position difference 3.8524m; +/-20ms allowed
FAIL run 2: nose discrepancy 10.0662 deg at 18.759s, aligned position difference 3.8524m; +/-20ms allowed
FAIL run 3: nose discrepancy 10.0662 deg at 18.759s, aligned position difference 3.8524m; +/-20ms allowed
FAIL run 4: nose discrepancy 10.0662 deg at 18.759s, aligned position difference 3.8524m; +/-20ms allowed
```

The one-degree assertion is a diagnostic threshold, not an approved product
tolerance. The position difference is reported at the rounded matching timestamp;
callback order and physics integration can affect it. This is a read-only replay
of captured evidence, not an unattended DCS replay or rendered-pixel test.

## What remains to establish

The repeatable orientation discrepancy gives a useful failure signal at the
controller/mission-API boundary. It does not yet prove that this is the precise
jump visible in the clip or that interpolation is responsible. No missing source
sample or large commanded angular step was found by the measurements above.

Next, align a visible playback clock with the nose movement, then trace the
orientation between the native pose write and mission/render readback. Preserve
this recording and matched baseline while changing one variable at a time.
Any fix must pass both the boundary check on newly captured traces and the
original close-formation visual replay. Do not accept the native write/readback
check alone as proof of correct rendered attitude.

The clip, recordings and game logs are local evidence, not source-publication
artifacts. No new source, game asset or recording was published by this work.
