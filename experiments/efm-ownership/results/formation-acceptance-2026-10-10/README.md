# Formation acceptance run: two jets plus player (10–11 October 2026)

This is evidence for [Build and accept the two-jets-plus-player formation workflow](https://github.com/caw1517/DCSRecorder/issues/45), against the contract in [Agree on two-jets-plus-player formation acceptance](https://github.com/caw1517/DCSRecorder/issues/42#issuecomment-6090692478).

Baseline: DCS 2.9.30.28536, Hornet, Caucasus, zero wind, authored scene `Diamond.miz` (saved revision `3e7fa9b6…`). Formation `BA_Diamond`. The user flew every take, parking to parking. Raw logs and takes are kept locally in this folder (`refly-2-v3/`, `record-3-v2/`, `takes/`) and are not committed.

## Build sequence

| Version | Made from | Take | Rows | Played against | Notes |
|---|---|---|---|---|---|
| v1 | Lead solo | `20261010T211026Z-0003` | — | — | Started from a solo take with an association |
| v2 | #2 against v1 | `20261010T220514Z-0001` | 43,031 | Lead | Epoch 22.901 s. Lead `ended@858.179` |
| v3 | #3 against v2 | `20261011T003030Z-0003` | 43,645 | Lead, #2 | Epoch 19.495 s. Lead `ended@858.165`, #2 `ended@860.605`. 0 hitches |
| v4 (offered) | #2 re-fly against v3 | `20261011T005737Z-0001` | 43,054 | Lead, #3 | Epoch 25.256 s. Lead `ended@858.164`. 0 hitches. Offer: base v3 |

## Gates

1. **Shared timing: pass.**
   - Each release logged one epoch, and every committed aircraft stored it. A restart created a fresh epoch: four releases in one session had epochs 36.816, 33.602, 19.495 and 20.153 s.
   - On every shared tick, the playback aircraft had exactly equal replay times: 35,390, 33,890, 17,844, 43,722, 2,863 and 43,106 ticks across the runs, with 0.0 s difference on all of them.
   - Each formation take's first sample is at its epoch (22.901, 19.495 and 25.256 s).
   - The offline delayed-callback check `formation_shared_epoch` passes.
2. **Per-aircraft fidelity: pass on the re-fly run** (`refly-2-v3`, `analyze_formation.py`). Each playback aircraft is compared with its own take using the #28 method and limits (fitted sampling offset 20 ms). Worst values:

   | Aircraft | Horizontal (m) | Vertical (m) | Attitude (°) | Velocity (m/s) |
   |---|---|---|---|---|
   | Lead | 0.074 (airborne) | 0.009 | 0.345 | 0.846 (air), 0.132 (ground) |
   | #3 | 0.068 (airborne) | 0.011 | 0.368 | 0.901 (air), 0.127 (ground) |

   Pair separation is measured, not gated. Across 42,908 shared samples, Lead and #3 reproduce their recorded spacing (minimum 7.06 m) to within 0.029 m at worst and 0.007 m at the 95th percentile. Run 3 cannot be compared this way, because its `dcs.log` was overwritten when DCS restarted. Its controller traces are kept.
3. **Preservation: pass.**
   - The sha256 of all four takes is unchanged since they were bound.
   - v1–v3 are write-once, and each file's modification time equals its creation time.
   - The saved scene, and the user's `Diamond.miz`, still match revision `3e7fa9b6…`.
   - Every prepared copy passed the structural comparison with the source. The only removals were declared: take-less #3 was left out of the v1 copies.
4. **Per-aircraft state: pass.** Exterior writes were compared with each aircraft's own take: 2.35 M in the first #3 attempt, 2.86 M in #3 run 3, and 2.84 M in the re-fly. Every write matches, except the 0→1 wrap of wheel-spin args 101–103, which is an artifact of the comparison and appears on both aircraft. The user's visual and audio review is still to come.
5. **Isolation and restart: partly verified.**
   - **Restart:** run 1 of #3 was restarted without Stop. A fresh epoch followed, the take stayed incomplete (`new take`), and no version was offered. There were no mutes to keep.
   - **Not-ready dropped alone (offline):** covered by `check_hook.lua` (`commit_refused`) and `check_mission.lua` (`one_never_ready`).
   - **Destroy while recording:** still to do.
6. **Performance: partly verified.** No motion-write gap over 0.02 s for either aircraft on any run. The user reported freezes on early runs. The fixes were batched trace flushing (`c1068e9`), removing the user's failing Volanta export, and tolerating capture hitches (`b0c753b`, `e9e5ba3`). The last two takes recorded 0 hitches. The user's report of no felt stutter is still to come.
7. **Versions: partly verified.**
   - The offered v4 names base v3. Its derived flags show #3 *not flown against* #2′ (recorded later), #2′ flown against Lead and #3, and the solo Lead not flown against either.
   - Mute, declined offer and Make version from this take: still to do.

## Issues found and fixed during the run

- **Gear doors opened on the Lead** (`e31e9ed`). The AI finished its authored route and switched to landing. Prepared copies now add an endless orbit at the last waypoint.
- **Lead pilot ejected after contact damage** (`afe3de9`). Playback aircraft are now immortal, by user decision.
- **Freeze-lost takes** (`c1068e9`, `b0c753b`, `e9e5ba3`). The strict rule was first kept by user decision, then replaced by a counted hitch tolerance capped at 1 s.
- **Ambiguous take-to-copy binding** (`5edd884`), a UI button left disabled (`393c17b`), and the missing Sync count (`94d22dc`).
- **Not fixed: an immortal #2 still ejected on landing.** No emergency mode was logged. Tracked in [Keep playback pilots in the cockpit through landing](https://github.com/caw1517/DCSRecorder/issues/46). It does not block acceptance.
