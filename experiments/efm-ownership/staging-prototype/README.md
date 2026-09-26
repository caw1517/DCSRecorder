# Airborne staging feasibility prototype

Question: can an occupied stock Hornet wait at a fixed airborne position, accept F10 Start, run a short countdown, and be released approximately 150 feet behind a second aircraft without losing independent player control?

**Status: first live stock-Hornet staging run accepted on 26 September 2026. Recorded-playback integration and exact initial state remain unverified.** The user selected this investigation in the confirmed workflow discussion. It preserves F10 start rather than substituting automatic start or asking the player to circle back.

## Evidence behind the experiment

- Installed `Config/Input/UiLayer/keyboard/default.lua` maps `iCommandActivePauseOnOff` to Active Pause.
- Installed Hornet training missions, including `1 FA-18C Basic Training – Controls Check.miz` and `3 FA-18C Basic A2A Training – Radar, AMRAAMs and BVR Combat.miz`, call `a_set_command(816)` at startup and later toggle it again. These are local primary evidence of the command, not proof of this prototype's complete behavior.
- Installed `API/Sim_ControlAPI.md` documents full simulation pause, but pausing simulation alone does not establish a working F10/countdown path. This experiment uses the training command instead.
- Existing recorded playback acquires at 5 seconds, translates its path and blends attitude for 2 seconds. That controller is not used here. Its fixed acquisition, runtime ID assumptions and restart behavior must be revisited before integration.
- The installed executable and current DCS log identify **2.9.29.27468**. The map still names 2.9.29.27278; do not use that old number as a verified current compatibility gate. Generated manifest records the actual installed version.

## What the mission does

It contains two **stock** FA-18C Hornets in calm air, using the original position and horizontal heading of the accepted recording's first sample. It requests Active Pause at startup. The player is nominally 45.72 metres (150 feet) behind a late-activated reference lead, at the same altitude and initial speed. The reference lead is absent until release, so this isolates the player's staging mechanism; it does not test holding a visible playback aircraft.

F10 Start requests a 3-second simulation-time countdown. A one-shot mission trigger activates the lead, toggles Active Pause, and logs release. Ten simulation seconds later the lead is removed. The player aircraft and mission continue. Duplicate F10 Start requests cannot toggle pause again. No DLLs, hooks, Export.lua, game files, or installed recordings are changed.

The command is a **toggle**, not a verified set-to-held API. Startup pause state, manually toggling pause, using the normal pause key, mission restarts and interrupted countdowns need live observation. If the countdown cannot run in Active Pause, that is a useful failed result; do not silently add wall-clock timing or call it a success. Expected release geometry comes from authored spawn positions; actual positions must come from telemetry.

## Build

From PowerShell, pass the existing local donor mission and accepted playback tape:

```powershell
./Prepare-Staging.ps1 -Baseline '<local Hornet prototype .miz>' -Tape '<accepted recorded-flight.txt>'
```

Default output: `../package/staging-prototype/DCSRecorder-Staging-Prototype.miz`. Existing mission outputs are preserved; choose a fresh `-OutputDirectory` for another build. Local installed DCS assets are used only in generated ignored output, never committed.

Preparation checks Lua syntax, installed mission module requirements, both routes, clean loadouts and the existing lights-off trigger. These checks do not simulate Active Pause or prove timing/geometry in DCS.

## Live run

1. Load `DCSRecorder-Staging-Prototype.miz` and enter the cockpit. Do not manually toggle either pause mode during the measurement.
2. Wait about 10 real seconds. The aircraft should remain in place. Through the communications menu choose **F10 > DCS Recorder staging test > Show staging status**, then **Start staged flight (3-second countdown)**.
3. Observe whether 3-2-1 runs while held, whether the reference lead appears about 150 feet ahead, and whether normal controls return. Fly a gentle turn after release to check independent control.
4. Verify the lead disappears after about 10 simulation seconds while your aircraft and mission continue. Exit normally.
5. Preserve `Saved Games/DCS/Logs/dcs.log` before another session rotates it. Run `Read-StagingResult.ps1 -LogFile '<preserved log>'` to measure hold drift, countdown, initial separation, movement after release, and continued samples after lead removal.
6. Repeat after a mission restart with a longer wait. A stuck menu, clock or countdown is a failed capability check; exit normally and retain the log.

No universal flight fidelity tolerance is selected here. Inspect actual drift and release separation before deciding suitability. This experiment contains no active recording, so independent recording completion is not validated.

## Decision after the run

If staging works, integrate it with an explicit recorded-playback start clock and exact initial pose/state, and revalidate the custom aircraft's activation/runtime identity and native motion guards. A passing stock-aircraft experiment alone cannot close the workflow or exact-start ticket. If it fails, retain the evidence and investigate the remaining pause/control bridge without changing the user's F10 requirement.

## Accepted live staging result — 26 September 2026

The user reported **"Complete and working"**. Telemetry from DCS **2.9.29.27468** corroborates the first stock-Hornet staging run:

| Observation | Result |
| --- | --- |
| Held player position drift | 0.000 m across 691 samples, at logged precision |
| Initial player/lead separation | 45.714467 m; target 45.72 m / 150 ft |
| Countdown | 3.000 s to release request |
| Additional mission-trigger delay | 0.450 s before actual release |
| Lead removal | Exactly 10 simulation seconds after release |
| Player telemetry after lead removal | 267 samples; mission continued |

**Decision:** Active Pause, F10 countdown and late activation are a demonstrated candidate for the next recorded-playback integration experiment. Anchor the playback clock to actual release/activation, not the countdown deadline.

**Remaining limitation:** the stock lead spawned approximately 2.383 m below the recorded starting altitude. Its level attitude and zero vertical velocity also do not reproduce the recorded initial state. Native-controller integration must restore the exact first-sample pose, velocity and supported aircraft state before advancing playback.

Only one staging run is established. Longer waits, mission restarts, multiple frame rates, recorded-controller synchronization and independent recording continuation still need validation. The full workflow and exact-start tickets remain open. Raw logs and recordings remain local.