# Canopy diagnostic checkpoint — 28 September 2026

Status: offline checked and installed; live capture and visual review pending.

The [separate canopy prototype](../../canopy-prototype/README.md) investigates
installed exterior argument 38 with a parked stock Hornet OPEN/HOLD/CLOSE
sequence. Partial holds are included in both directions. No endpoint or live
mapping is accepted yet, and recorded-canopy playback has not been implemented.

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

The user is asked to stay parked at idle with the parking brake set, run the
automatic F10 sequence without Active Pause, observe in F2 for about one minute,
and leave DCS open for log collection. Next: preserve the log, compare applied
phases with measured ranges and visible behavior, then prepare a separate
captured-canopy playback experiment if the evidence supports the mapping.
