# Full-flight duration: offline long-take check (6 October 2026)

This is the offline half of [Verify full-flight duration and accept the parking-to-parking workflow](https://github.com/caw1517/DCSRecorder/issues/34). It ran before any long live flight. On 6 October 2026 the user decided that **takes have no upper length limit**. Minimum length, finite-data, continuity, ownership and compatibility checks remain.

## What changed

| Stage | Before | Now |
|---|---|---|
| Recording sink (`companion/recording_sink.lua`) | Abandoned a take after 20,000 rows (about 400 s). Kept every row in memory and re-read the whole file twice at Stop. | No row limit. Each flushed 50-row block is verified through a second read handle, so memory stays flat. At Stop only the size and footer are rechecked. The startup storage check exercises the same write, flush, seek and block-read sequence, so a DCS file-API difference fails before recording. |
| Reader (`recorded_flight.py`) | Accepted 5 to 300 s. | Accepts at least 5 s. Pre-contact (version < 8) takes keep 300 s, because their airborne controller is unchanged. |
| Surface controller (`recorded_path.h`, `object_probe.cpp`, `staged_playback.h`) | Refused more than 100,000 samples or more than 300 s. Replay clock was seconds/1000 on arg 996, which goes above 1 after 1000 s. Byte-at-a-time fingerprint. Evidence logs flushed on every tick. | No upper sample or length limit. Arg 996 is seconds/100000 (mission config `replay_scale`). Block-read fingerprint, identical to the preparation fingerprint. Per-tick evidence logs flush at most once a second. |
| Companion library (`library.py`) | Re-read every take on every refresh. | Validates each unchanged file once per session; the footer is read from the file tail. |

Rebuilt and pinned:
- `HornetSurfaceProbe.dll`: `49a6be2b…`. Normal; see `surface-start-2026-10-03/controller/manifest.json`.
- `HornetSurfaceFaultProbe.dll`: `bed422da…`. Developer only.

## Checks

- **C++ and Lua suite:** `ctest -C Release` passes 51/51. This includes:
  - the new `surface_long_tape_check`;
  - `release_mission_lifecycle` with a new `long_parked` case: a 1800 s ground take, a smoke switch at 1500 s, no completion timeout, replay clock below 1, parked ending.
- **Companion suite:** `python -m unittest discover -s companion` gives the same results as before the change. The 10 errors are pre-existing legacy practice-mission tests that need DCS 2.9.29.

The end-to-end check is `check_long_take.py`, with raw results in `offline-check.json`. It uses two takes per length:

- **sink:** the real recording sink saves a continuously moving contact take.
- **circuit:** the accepted 248.7 s parking-to-parking circuit with its hot parked start held longer. It is prepared against its own authored scene (lineage revision `7da72749…`) and keeps its eligible parked ending.

| | 30 min sink | 30 min circuit | 60 min sink | 60 min circuit |
|---|---|---|---|---|
| Samples | 90,001 | 90,001 | 180,001 | 180,001 |
| Take / tape size | 28.0 / 23.7 MB | – / 50.0 MB | 56.6 / 47.9 MB | – / 100.0 MB |
| Sink save (whole fixture) | 26.5 s | | 34.6 s | |
| Full authored preparation | | 47.4 s | | 46.1 s |
| Controller tape load | 3.3 s | 4.7 s | 3.5 s | 4.5 s |
| Replay step cost, first minute / last minute | 1.35 / 1.27 ms | 1.74 / 1.73 ms | 1.70 / 1.76 ms | 3.19 / 1.27 ms |
| Release-clock error over the take | 2.3e-13 s | 2.3e-13 s | 4.5e-13 s | 4.5e-13 s |

Reading the table:
- Per-step replay cost does not grow with replay time; lookup is a binary search.
- Python reading is linear. Untraced, it takes 3.5 s at 30 minutes and 6.9 s at 60 minutes, with a transient peak of about 0.5 GB and 1 GB. It happens once per take per companion session, plus during preparation.
- The timings above were measured with allocation tracing on a busy machine, so they are upper bounds.

## Still live-only

- DCS log history and the recorder's per-row 150 ms capture timing gates over a 20 to 30 minute take.
- DCS's own file methods for the sink's block verification. The startup storage check would fail first.
- The 4 to 5 s tape load at object creation, against the mission's 10 s readiness timeout.
- Evidence-log volume: about 1 GB per 30 minutes of probe logs plus the mission log.
- Simulator frame time across the whole flight.
