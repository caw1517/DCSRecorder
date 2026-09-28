# Canopy diagnostic checkpoint — 28 September 2026

Status: stock-aircraft capture and separate recorded-canopy playback accepted
visually and numerically. Normal-workflow integration is prepared separately.

The [separate canopy prototype](../../canopy-prototype/README.md) investigates
installed exterior argument 38 with a parked stock Hornet OPEN/HOLD/CLOSE
sequence. Partial holds are included in both directions. The user reports:
“It's complete and everything seemed to have checked out great.”

Offline preparation passed clean-aircraft configuration, installed Hornet
dependencies and route validation. The packaged Lua harness passed normal,
abort, missing-phase and moving-aircraft cases. Its analyzer fixture contains
2,241 samples across ten phases with a maximum 20 ms gap. Fixture values are
constant and do not demonstrate actual canopy motion.

Installed as a new file:
`C:/Users/w_can/Saved Games/DCS/Missions/DCSRecorder-Canopy-Diagnostic.miz`.

- SHA-256: `5b043f1eb630a55690f9fe45f6cf118436120278a8a738bb1166ace532cad1db`.
- 478 protected file hashes remained unchanged during installation.
- No module/hook replacement or DCS restart was required.
- Raw logs, generated missions and installation manifests stay local and ignored.

## Live capture

The log was preserved locally as `capture.log` before further work. SHA-256:
`5eaa2ef0070c14239e7b5cd30f2cc0a6eb9f2f6929cdc29a3172157446ac9755`.
The analyzer passed 2,364 samples across ten applied phases, 47.28 seconds from
BEGIN to END, and a maximum 20 ms sample gap. END reports `complete`.
Request-to-application delays were 86–986 ms; the tape uses actual sampled time,
not requested control timing. Source values remain immutable.

| Observed phase | Exterior argument 38 |
| --- | --- |
| Closed, including initial state and final hold | 0 |
| Hold after partial opening | 0.391806871, steady |
| Fully open hold | 0.899999976, steady |
| Hold after partial closing | 0.801097870, steady |

Opening and closing transitions contain changing measured values. Together
with the user's external observation, this validates the bounded stock canopy
position mapping. Do not normalize fully open to 1 or infer jettison/cockpit
system restoration from this result.

## Separate playback candidate

`HornetCanopyProbe` reuses the isolated SDK appearance writer with a separate
one-channel tape/header/module. It writes argument 38 plus the existing
diagnostic elapsed/status arguments. Its fake-SDK check passed all 2,364 actual
samples, every interpolation midpoint, endpoint hold, and identity/cookie/bounds/
lifecycle/backward-clock guards. Mission checks passed installed dependencies,
both aircraft routes, clean configuration, and completion/failure/timeout/stop.

The generated `DCSRecorder-Canopy-Playback.miz` replays 47.26 seconds between
first and last samples, then holds the final state for eight seconds and removes
the test lead. This isolates visible canopy playback on an ordinary airborne
route; it does not reproduce the diagnostic's parked motion or test ground
physics. No native hook is added. Later mission reads are logged independently
from immediate SDK readback to detect possible animation overwrites.

Package: ignored `package/canopy-playback`. After the user confirmed DCS was
closed, installation verified all ten installed file hashes and 1,639 protected
files unchanged. The new module is `DCSRecorder-Hornet-Canopy`, with
`DCSRecorder-Canopy-Playback.miz` in Saved Games/DCS/Missions. The installation
manifest remains local in the package.

## Accepted live playback

The user reports: “Complete and verified working well.” The accepted DCS log and
SDK/event traces were preserved under the ignored `playback-accepted/` directory
before further work. The single playback object (16777472, DCS process 30024)
loaded all 2,364 source samples, completed the sequence and eight-second endpoint
hold, then was destroyed normally. Mission END reports `complete`.

- 2,764 SDK calls: immediate error 0 and between-call overwrite error 0.
- 2,760 independent later mission reads: no canopy mismatches at 1e-5 tolerance;
  maximum difference approximately 5e-10 from text precision.
- The diagnostic elapsed-clock alignment differs by at most 1.862 microseconds.

This supports captured canopy position and transitions on the isolated playback
aircraft. It does not establish ground physics or internal canopy-system replay.
See the [normal integration checkpoint](../canopy-integration-2026-09-28/README.md)
for the next live gate.
