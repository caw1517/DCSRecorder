# Takeoff and landing playback, 4 October 2026

Evidence for [Validate takeoff and landing playback and agree measured tolerances](https://github.com/caw1517/DCSRecorder/issues/28). Raw logs and traces stay local (`live-1` … `live-9`, `source/`, `tape/`). They are git-ignored.

## Source take

- Take `20261004T200936Z-0001`, from authored scene `TAKEOFF_LANDING_TEST.miz`.
- Length 248.7 s, 12,436 samples, of which 3,003 grounded.
- Liftoff at 31.46 s at 87.2 m/s. Touchdown at 220.12 s at 72.6 m/s, sink 3.46 m/s.
- No bounce, no damage. The parked ending is eligible (2.58 s tail).

## Runs

| Run | Controller change | Result |
| --- | --- | --- |
| 1 | Speed limits removed | Pinned to the runway for 1.35 s after liftoff, up to 3.8 m low, then a jump |
| 2 | Tape pose restored before every native step | Liftoff within 8 cm; destroyed at the first grounded sample |
| 3–6 | Experiments: gear post state, 0.5 m/s sink limit, `SetImmortal`, EFM damage/suspension callbacks | Still destroyed (`pilot dead`, `crash`); no EFM callback called. The object is a `woAIPlane` |
| 7 | Read-only AI phase log (research #36) | AI mode 51 on the ground, then 2, then 4. Ground flag `+0x26D3` is 1 on the ground and clears about 4 s after liftoff |
| 8 | Hold `+0x26D3`=1 on grounded samples | Touchdown survived. Rollout at 25 native steps/s and 10 SDK ticks/s, up to 15.8 m overshoot (stutter) |
| 9 | Also hold AI mode 51, and restore extra native steps | User: "Looked great". 50 steps/s in every phase, rollout jitter at taxi level, PARKED at 248.70 s |

The run 3–6 experiments were removed afterwards. The committed controller keeps only these changes:
- no speed limits;
- pose restored before every step, including extra steps;
- ground flag and taxi-mode hold;
- the read-only AI phase log.

Run 10 used the cleaned build (`27dfc6ba…`). User: "everything looked great". PARKED at 248.70 s, held 28.8 s.

## Measured against the source (run 10)

`analyze_run.py live-10`. Pose and velocity are compared at replay + 20 ms, the fitted sampling offset.

| Phase | Horizontal | Vertical | Attitude | Velocity |
| --- | --- | --- | --- | --- |
| Held (after 0.2 s load transient) | 0.000 m | 0.000 m | 0.004° | 0 |
| Taxi out and roll | 0.002 m | 0.001 m | 0.078° | 0.136 m/s |
| Liftoff (−3/+5 s) | 0.027 m | 0.002 m | 0.113° | 0.126 m/s |
| Airborne | 0.033 m | 0.016 m | 0.225° | 1.525 m/s (p95 0.580) |
| Touchdown (−5/+3 s) | 0.008 m | 0.012 m | 0.094° | 0.655 m/s |
| Rollout and taxi in | 0.007 m | 0.003 m | 0.067° | 0.124 m/s |
| Parked | drift 0.000 m | | | |

All values are maximums.

- **Timing:** the replay clock drifted 0 ms against model time. Smoke switched within one tick.
- **State:** 523,875 post-animation reads were within 1e-13 of the request. Against the source, everything is within 1e-4, except:
  - wheel rotation, within 3e-4;
  - the strobe, on sample-boundary edges.
- **Contact:**
  - Ground clearance is within 3 mm of the source, and airborne within 0.19 m.
  - Life 20/20, no crash.
  - DCS `inAir()` is wrong from 28.94 s to the end. This is recorded as fog on the map, not gated.

## Agreed acceptance limits (user, 4 October 2026)

These apply to every phase, and to final acceptance and later regressions. `analyze_run.py` checks them.

| Channel | Limit |
| --- | --- |
| Position | horizontal 0.10 m, vertical 0.05 m |
| Attitude | 0.5° |
| Velocity | 0.25 m/s grounded; 2.0 m/s airborne, liftoff and touchdown |
| Replay timing | within one tick (20 ms) |
| Supported state | retention 1e-6; against source 1e-3 (strobe excepted at sample edges) |
| Ground contact | clearance within 0.01 m of source; life unchanged; no crash |
| Parked drift | 1 mm |
| Excluded | the first 0.2 s after mission load (load transient) |

**Parked eligibility** (`parked_state.py`, profile `hornet-parked-endpoint-v1`):
- final tail ≥ 2.0 s;
- speed ≤ 0.1 m/s;
- displacement ≤ 0.05 m;
- heading ≤ 0.2°;
- both engine cores ≥ 0.5;
- life unchanged and grounded.

The thresholds come from the stopped behaviour in two ground takes: speed < 0.042 m/s within 0.5 s of stopping, displacement ≤ 0.024 m, heading ≤ 0.011°, idle core 0.65–0.70.

## Airborne-only takes

Every take with contact data (version 8 or later) now plays on the surface controller, even if it never touches the ground. So no take has speed limits. Older takes without contact data keep the approved airborne controller. A live airborne regression run is pending.

## Scripts

- `analyze_run.py <run>`: source against playback by phase, with the agreed-limits verdict.

- `analyze_transition.py <run> [from to]`: playback-against-source height at common replay times, from lead `SAMPLE` rows.
- `analyze_smoothness.py <run>`: rendered-pose step-to-step smoothness by phase, from `ground-pose-*.csv`. Its "err" column is one step of motion, not playback error.
