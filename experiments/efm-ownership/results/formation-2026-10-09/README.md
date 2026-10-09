# Formation prototype live check (9 October 2026)

Evidence for [Let each playback aircraft own its recorded flight](https://github.com/caw1517/DCSRecorder/issues/39).
Setup: DCS 2.9.30.28536, Caucasus, zero wind, scene `Diamond.miz` (`3e7fa9b6…`), three stock Hornets.

| Position | Unit | Take | Duration | Tape key |
|---|---|---|---|---|
| Blue Angel #1 - Lead | 1 | `20261009T013519Z-0001.csv` | 250.1 s | `6356c9946115a9f7` |
| Blue Angel #2 | 2 | `20261009T195651Z-0001.csv` | 54.9 s | `a0becfded99e7e21` |
| Blue Angel #3 (player) | 5 | — | — | — |

Both takes were flown solo from the same scene revision and ended with F10 Stop. The package is
`package/` (`formation-prototype-v1`, controller `HornetFormationProbe.dll`, installed under
`DCSRecorder-Hornet-Formation`). The payload, raw `dcs.log` and probe logs stay local.

## Results

Every run assigned the takes correctly: unit 1 got runtime 16777728 and `position-1.txt`, and unit 2
got runtime 16777984 and `position-2.txt`. Both aircraft were ready together, both were committed in
the same hook callback as the player release, and both started replay time zero on the same frame.

| Run | Removal | Survivor after removal | Survivor ending |
|---|---|---|---|
| 1 | None commanded. #2 collided with #1 while taxiing, 7.6 s after release | #1 kept `called`, but DCS stepped it every 0.1 s instead of 0.02 s from about 1 s later. #1 was itself destroyed 26 s later | Collision damage (see below) |
| 2 | Native abort of #2 at +3.3 s | #1: 74.6 s, all `called`, maximum gap 0.02 s | Mission restarted early |
| 3 | Native abort of #1 at +3.0 s | #2: 37.6 s, all `called`, maximum gap 0.02 s | Exited early |
| 4 | F10 *Destroy* of #1 at +1.45 s | #2: model 8.78 → 62.28 s, 3,110 of 3,110 `called`, maximum gap 0.02 s | Own ending, exact: 7.36 + 54.92 = 62.28 s, then `COMPLETE` |

The user reported that everything looked good visually.

## Findings

- **Isolation holds.** Removing one aircraft, by native abort, by mission `Unit:destroy()` or by
  collision, never interrupted the other's native motion or failed it. Each removal restored only
  that aircraft's hook. When DCS had already replaced the vptr at destroy, the controller left it
  alone (`step_hook_already_replaced`), as designed. A hook abort sent to an already destroyed
  aircraft is refused with `REFUSED,object_or_package`, which is harmless.
- **Takes recorded without seeing each other can collide.** Take 2 was flown with #1's spot empty,
  so on playback #2 taxied into #1. Recording against a playing formation
  ([issue 41](https://github.com/caw1517/DCSRecorder/issues/41)) is what prevents this.
- **A damaged playback aircraft may be stepped at 10 Hz.** After the collision, DCS called #1's object
  simulation every 0.1 s instead of every 0.02 s. This qualifies the
  [physics decision](https://github.com/caw1517/DCSRecorder/issues/3) that a damaged aircraft keeps
  its path: it keeps the path, but its motion may visibly coarsen. This run does not show it was visible.
- The hold before assignment worked. Both aircraft captured their spawn pose on the first callback and
  were assigned in the hook's first frame (`ASSIGN` at model time 0). Readiness followed when the
  player's slot finished loading.
