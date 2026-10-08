# Flight envelope: measured manoeuvres (7 October 2026)

Evidence for [Validate the single-aircraft flight envelope through takeoff and landing](https://github.com/caw1517/DCSRecorder/issues/7), following its [agreed plan](https://github.com/caw1517/DCSRecorder/issues/7#issuecomment-6047672241). Each take is replayed once with its DCS log kept and checked against the limits agreed in [#28](https://github.com/caw1517/DCSRecorder/issues/28): horizontal 0.10 m, vertical 0.05 m, attitude 0.5°, airborne velocity 2.0 m/s, state 1e-3. The only exclusion is the 67.1–74.2 s post-liftoff window ([#37](https://github.com/caw1517/DCSRecorder/issues/37)).

Raw logs and takes stay local (gitignored).

## Tools

- `analyze_run.py`: copied unchanged from `takeoff-landing-2026-10-04`, the phase-by-phase check.
- `analyze_envelope.py`: reuses `analyze_run.py`'s parsing and error model, and reports named replay-time windows from a JSON file.
- `windows-solo-demo.json`: the manoeuvre windows for the solo demo.

```
python analyze_run.py solo-demo-1 source/20261007T012523Z-0001.csv
python analyze_envelope.py solo-demo-1 source/20261007T012523Z-0001.csv windows-solo-demo.json
```

## Solo demo: `20261007T012523Z-0001` (883.5 s), run `solo-demo-1`

The user flew the Blue Angels solo demo as lead solo, including the dirty roll on takeoff. Replayed from hot parking to the parked hold with prepared mission `DCSRecorder-Authored-Playback-f0332a19.miz`, DCS PID 37468, session 21:59–22:17 UTC. 46,869 lead samples; the fitted sampling offset is 20 ms.

### By phase (`analyze_run.py`)

| Phase | Horizontal max | Vertical max | Attitude max | Velocity max |
|---|---|---|---|---|
| Held | 0.000 m | 0.000 m | 0.004° | 0.000 m/s |
| Taxi out and roll | 0.002 | 0.002 | 0.118 | 0.189 |
| Liftoff (−3/+5 s) | 0.193 | 0.008 | 0.158 | 0.268 |
| Airborne | 0.483 | 0.030 | 0.443 | 1.739 |
| Touchdown (−5/+3 s) | 0.016 | 0.010 | 0.124 | 0.516 |
| Rollout and taxi in | 0.024 | 0.001 | 0.075 | 0.128 |
| Parked (36.5 s, 0 m drift) | 0.000 | 0.000 | 0.000 | 0.000 |

All 330 horizontal exceedances fall inside 67.1–74.2 s (0.102–0.483 m). This reproduces the earlier run's 334 in the same window.

### By manoeuvre (`analyze_envelope.py`)

| Manoeuvre | Window | Horizontal | Vertical | Attitude | Velocity | Result |
|---|---|---|---|---|---|---|
| All airborne, excluding 67.1–74.2 s | 65.3–830.9 s | 0.100 | 0.030 | 0.443 | 1.739 | Pass (0.100 m at 67.08 s, at the limit just before the window) |
| Dirty roll on takeoff | 70.9–73.9 s | 0.483 | 0.015 | 0.025 | 0.588 | Inside #37 window |
| Inverted low pass | 395–414 s | 0.009 | 0.011 | 0.203 | 0.379 | Pass |
| 7.8 G turn at 415 kt | 468.7–488.7 s | 0.035 | 0.007 | 0.443 | 1.739 | Pass |
| Rolling series to 990 m | 630–643 s | 0.008 | 0.009 | 0.359 | 0.409 | Pass |
| Low passes, 55–70 m | 290–307 s | 0.011 | 0.013 | 0.396 | 0.373 | Pass |

During the dirty roll, attitude error is 0.025°. The drift is horizontal only.

### State

- Supported-state retention: 1,546,677 post-animation reads, max error 1e-12.
- The clock drift against model time is 0.0 ms.
- Wheel rotation (args 101–103) exceeds 1e-3 on 513 reads, all during rollout and taxi-in (831–872 s), with a maximum of 0.0022 revolution (0.8°). The [#28](https://github.com/caw1517/DCSRecorder/issues/28) circuit stayed within 3e-4. A rotation that fast cannot be resolved by interpolating 20 ms samples, so this is probably a measurement artifact. On 7 October 2026 the user accepted it as a known residual, listed as an exception in the envelope.
- DCS `inAir()` disagrees from the takeoff roll through rollout, as known in [#38](https://github.com/caw1517/DCSRecorder/issues/38). It is not a gated channel.

## Loop take: `20261008T172516Z-0001` (479.2 s), runs `loop-1/replay-1` to `replay-4`

Recorded by the user with the normal workflow from a hot ground start. Liftoff is at 79.86 s with no roll on takeoff. The take contains a Cuban 8 and a vertical climbing roll that reaches 90° pitch. It ends airborne.

Replayed four times in one DCS session (PID 51928, 17:38–18:11 UTC). `loop-1/dcs-playback.log` is split at each mission load into `replay-N/dcs-playback.log`. No replay reached the end of the take, because each was restarted before it finished:

- Replay 1 reached 471.1 s.
- Replays 2–4 reached 437–446 s.

Only replay 1 covers the vertical climbing roll, up to 471 s (the climb at 461.2–470.2 s, then three rolls). The user reported all replays as smooth and easy to fly formation on.

| Manoeuvre | Window | Horizontal | Vertical | Attitude | Velocity | Result |
|---|---|---|---|---|---|---|
| Post-liftoff window (+7.1 s) | 79.9–87.0 s | 0.014 | 0.001 | 0.006 | 0.126 | Pass, all four replays |
| Cuban 8 first vertical pull | 108.1–115.1 s | 0.011 | 0.005 | 0.001 | 0.578 | Pass, all four |
| Cuban 8 second vertical pull | 159.6–165.9 s | 0.013 | 0.006 | 0.001 | 0.645 | Pass, all four |
| Straight-down dive | 177.2–183.7 s | 0.010 | 0.008 | 0.001 | 0.520 | Pass, all four |
| Inverted pass at 709 m | 421.7–428.5 s | 0.010 | 0.012 | 0.004 | 0.556 | Pass, all four |
| Vertical climbing roll (to 471 s) | 461.2–476 s | 0.029 | 0.018 | 0.300 | 1.320 | Pass, replay 1 |
| All airborne | | 0.046 | 0.023 | 0.300 | 1.320 | Pass |

- **Ground and state:** taxi and takeoff roll are within 0.008 m. Wheel rotation is within 3e-4. Supported-state retention max error is 2e-13. Clock drift is 0.0 ms.
- **Post-liftoff drift (#37):** this take has no roll on takeoff, and its post-liftoff window passes at 0.014 m. That is consistent with the dirty roll driving the 0.48 m solo-demo drift.
- **Contact damage in replay 1:** the playback aircraft's life fell from 20 to 19 at mission time 348.54 s (replay 314.7 s), with the player 9.4 m centre to centre. It fell from 19 to 4 at 459.74 s (replay 425.9 s, the inverted pass), with the player 15.5 m away. No hit events are logged. The controller kept the recorded path through both, with pose within the limits. This is evidence for [#3](https://github.com/caw1517/DCSRecorder/issues/3), not an envelope failure. `analyze_run.py` reports it as `airborne life lost`. Replays 2–4 lost no life.

```
python analyze_run.py loop-1/replay-1 source/20261008T172516Z-0001.csv
python analyze_envelope.py loop-1/replay-1 source/20261008T172516Z-0001.csv windows-loop.json
```

Full output: `loop-1-results.txt` (local).
