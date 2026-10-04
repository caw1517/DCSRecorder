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

The live check of the cleaned build is pending.

## Scripts

- `analyze_transition.py <run> [from to]`: playback-against-source height at common replay times, from lead `SAMPLE` rows.
- `analyze_smoothness.py <run>`: rendered-pose step-to-step smoothness by phase, from `ground-pose-*.csv`. Its "err" column is one step of motion, not playback error.
