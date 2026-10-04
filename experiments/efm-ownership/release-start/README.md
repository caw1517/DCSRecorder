# Airborne countdown and release control

Implementation for [Release player and playback on one countdown clock](https://github.com/caw1517/DCSRecorder/issues/22).
Airborne live acceptance is complete; see the [measured evidence and user reviews](../results/countdown-release-2026-10-01/README.md).
This separate module builds on the accepted
gear-down snapshot; it does not change the installed normal companion module.

`HornetReleaseProbe` retains the first pose and all supported state with zero
motion until a matching, ready, single-use release request is committed. The
next native object callback establishes replay time zero and restores original
recorded velocity. Pose, brake, exterior state and engine consumer values sample
the same clock. Smoke follows the native replay-time argument. Global simulator
pause cannot age this clock using wall time. Airborne recording-reader guards
are unchanged; ground support is not claimed.

The F10 mission script owns the three-second countdown in mission time. A
separate user hook reads its session-bound request through the already-proven
DCS log-history bridge, checks the selected loaded mission fields and tape
fingerprint, and commits the native latch. It then dispatches the player's
Active Pause release immediately in the same hook callback, without waiting for
a periodic mission trigger scan. The mission logs acknowledgment; the native
controller separately logs its first replay epoch. Accepted live runs measured
1–7 ms from player release to the next native replay callback. User review
accepted the visible release; these are not identical callback timestamps or a
new general fidelity tolerance.

The hook rejects repeated requests, stale sessions, wrong object generations,
unready native snapshots and mismatched loaded fields. It operates only for the
named diagnostic mission. A missing hook causes a readiness timeout. Mission
failure removes the diagnostic lead and requests cleanup of its owned player
hold. A valid airborne recording ending removes the lead. No in-place replay or
parked completion is offered. Restart uses a fresh native object and session.

Loaded-field checks are bounded to this fixed diagnostic fixture. They are not
the complete authored-mission/session authorization implementation assigned to
later tasks. Do not manually toggle Active Pause during this control, because
the diagnostic owns that hold. Global pause testing is a separate live step.

## Files and checks

- `policy.h` and `bridge.h`: simulator clock and Lua/native request boundary.
- `mission.lua` and `hook.lua`: countdown, readiness, dispatch, acknowledgment,
  smoke, telemetry and failure handling.
- `prepare.py`: verifies the accepted snapshot package, checks its source against
  the exact native tape, and generates a separate module, mission and hook.
- `loaded_defaults.lua` and `prepare_defaults.lua`: resolve installed Hornet
  property/Link16 loading defaults during preparation so a strictly compared
  reference includes the same defaults DCS adds. Authored values are preserved.
- `check_loaded_defaults.lua`: runs the real hook/comparison against the installed
  loader's defaults and verifies that meaningful mission edits are still refused.
  Its optional fourth argument supplies the actual captured DCS-serialized
  mission; property-default tests alone do not cover the full load/save boundary.
- `prepare_reference.py` and `check_reference.py`: audit the captured serialization
  against this fixed diagnostic's prepared source, reject unreviewed changes and
  bind an exact runtime reference without replacing the source mission or tape.
- `Install-Control.ps1`: additive installation with hash checks, fixed allowed
  destinations, DCS-closed enforcement and existing-file preservation checks.
- `Update-Package.ps1`: backed-up, hash-verified replacement of the diagnostic
  mission/reference/hook after the retained v2/v3 readiness failure.
- `check.cpp`, `check_mission.lua`, `check_hook.lua`, `check_bridge.lua`: clock,
  readiness/refusal, pause, duplicate, failure, restart and real DLL ABI fixtures.
- `check_package.lua`: compiles nested generated scripts and validates the
  complete 33-channel initial state and typed smoke event schedule.

Build `HornetReleaseProbe` and `release_clock_check` with CMake/Visual Studio.
Run selected checks with:

```powershell
ctest --test-dir experiments/efm-ownership/build -C Release -R 'release_|snapshot_callback|held_|trial2930_callback' --output-on-failure
```

Prepare from the accepted snapshot package into a fresh output directory, then
run the installer with `-ValidateOnly` before actual installation. Keep the
manifest and installation receipt with the evidence. The installer never
overwrites previous diagnostic or normal-runtime files.

## Live evidence required

First perform one normal release from the accepted gear-down source. Observe
held/countdown pose and state, first movement, smoke-ON emission, engine sound,
and the short airborne recording's completion. Retain the full DCS log plus
the new module's native motion, appearance, engine and lifecycle logs before
another run. Compare the request, commit, player acknowledgment, native epoch,
first restored velocity and initial movement against the source recording.

Subsequent one-at-a-time checks cover repeated start, global pause during
countdown and playback, and live readiness refusal. User observation establishes
rendered smoke/first-visible behavior; command delivery alone is insufficient.
Do not close the task or check off its parent until the required live evidence
has been reviewed.
