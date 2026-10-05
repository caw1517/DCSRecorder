# Endings, failures and restart for ground playback, 4 October 2026

Evidence for [Verify endings, failures and restart for ground playback](https://github.com/caw1517/DCSRecorder/issues/31). Raw logs, takes and probe traces stay local; they are git-ignored. DCS 2.9.30.28536, Caucasus, Hornet/Blue Angels, zero wind.

## Inputs

All inputs are real recorded takes.

| Take | Scene | Use |
| --- | --- | --- |
| `20261004T033450Z-0001` (26.6 s taxi, eligible parked end) | Issue11-Parking_Test, played in V2 (lead 2, player 4) | Restart, pause, parked hold, faults, package mismatch |
| `20261004T234817Z-0001` (16.1 s taxi, F10 Stop at 7.3 m/s, smoke on from 13.3 s) | Issue11-Parking_Test_V2 | Moving-ground ending |
| `20261004T224643Z-0001` (21.9 s airborne, from takeoff/landing task) | TESTmiz | Airborne-ending regression |

Packages are in `packages/` (manifests only). `fault-controller/` is the diagnostic surface build with `HORNET_FAULT_INJECTION`, sha `f60b9135…`. Normal packages keep the accepted surface controller, sha `27dfc6ba…`.

## Changes

- **Removal:** recorder-owned smoke is switched off (`SMOKE_REMOVED`) before the aircraft is destroyed (`AIRCRAFT_REMOVED`). This applies to completion, a not-parked ending and every failure.
- **Notices:** they no longer say "Release test" or "Exit normally". Endings and failures now say the aircraft was removed and the mission continues.
- **In-mission restart (defect found in live-1):** after Left Shift+R, DCS reloads `…\Temp\DCS\tempMission.miz`. The hook selected its mission by file name only, so it never started a session and the mission failed closed with `identity_unverified`. Full DCS restarts (task 7) never exercised this.
  - The hook now also accepts DCS's temporary copy, but only when the loaded mission matches the approved reference exactly (`SELECTED_BY_CONTENT`).
  - Any other name, or an edited temporary copy, is still refused (`NOT_SELECTED`).
- **Fault injection (diagnostic packages only):** `prepare_playback.py --fault-injection` builds a separate package.
  - It uses the fault controller and adds an F10 submenu: remove playback aircraft, native clock failure, native state failure.
  - The hook forwards native faults to bridge commands `fault_clock` and `fault_state`.
  - Those commands arm a non-finite replay clock or a failed exterior write, so the real native failure paths run.
- **Offline coverage:**
  - `check_mission.lua`: smoke-on removal, diagnostic faults, and no fault menu outside diagnostic packages.
  - `check_authored_hook.lua`: temporary-copy restart, accepted when exact and refused when edited.
  - `check_bridge.lua`: fault commands refused without an owned object.
  - `test_library.py`: damaged files are refused, each with its own reason, apart from F10-stopped takes.
  - ctest passes 50/50, including the fault build.

## Live runs (user performed; agent read logs)

| Run | Steps | Result |
| --- | --- | --- |
| live-1 | Restart (Shift+R) from countdown | **Blocked**: no hook session after reload, `FAILED,identity_unverified`, aircraft removed, hold cleaned. This led to the hook fix |
| live-2 | Restart from countdown; release, pause during taxi, restart from ground playing; release, parked, pause during parked hold, restart from parked | Every reload: `SELECTED_BY_CONTENT`, a new session and native generation (1→2→3→4), back to READY with one held aircraft. No leftover request, smoke or sound. Pause: model time stopped and resumed together with replay, step mismatch ≤ one 20 ms tick. PARKED at replay 26.640 s, 409 samples, drift 0.000 m through the pause. User: smooth, stayed put |
| live-3 | Fault package: native state failure while held; restart from failed; clock failure during taxi; restart; remove aircraft during taxi | State: `fault_state_injected` → `exterior_write_failed` (next tick) → `step_hook_restored`, `FAILED,native_readiness_lost`, `AIRCRAFT_REMOVED`, `HOLD_CLEANED`, later Start → `START_REFUSED,failed`. Clock: `fault_clock_injected` → `release_clock_invalid` (next tick) → hook restored, removed. Missing: `FAILED,missing_aircraft`. Every restart returned to READY. User: nothing left behind, kept flying |
| live-4 | Installed tape altered by 1 mm at one sample (fingerprint mismatch) | First frame: `FAILED,native_readiness_lost`, aircraft removed. Bridge `REFUSED,object_or_package`. `HOLD_CLEANED`, Start refused. Original tape restored afterwards |
| live-5 | Moving-ground ending | Smoke on at replay 13.360 s (recorded 13.345 s). At 16.1 s: `SMOKE_REMOVED`, `AIRCRAFT_REMOVED`, `COMPLETE,not_parked`. User: notice matched, smoke and sound stopped |
| live-6 | Airborne-ending regression | `AIRCRAFT_REMOVED`, `COMPLETE` at 21.9 s. Smoke had already been switched off at 14.6 s as recorded. User: notice matched, nothing left behind |

## Input refusal

Before staging, a take is refused if any of these hold. Each case gives its own reason in the library.

- No footer: "Recording is incomplete".
- A truncated row.
- The footer row count differs from the rows present.
- The footer reason is aircraft loss or error.
- It was not stopped with F10 Stop.
- The recording sink keeps unfinished or error takes as `.partial`; they are never listed.

A take deliberately stopped with F10 Stop is valid at any point, including mid-taxi (live-5) and in the air (live-6). It plays and ends with removal. There is no content checksum beyond the footer count and the tape fingerprint.

## Not covered here

- The legacy 5–300 s duration guard remains in both readers. Full-flight duration belongs to [Verify full-flight duration and accept the parking-to-parking workflow](https://github.com/caw1517/DCSRecorder/issues/34).
- The wall-clock timestamps in `dcs.log` are buffered. Pause and continuity checks use model and replay time.
