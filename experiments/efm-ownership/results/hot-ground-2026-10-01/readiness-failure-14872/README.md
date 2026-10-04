# Ground readiness failure and separate pose-retention finding

The first ground playback run reported `bridge_or_native_readiness_timeout`.
The native controller reported READY, replay time stayed zero and all supported
initial appearance channels passed. The loaded-field bridge rejected the stock
witness aircraft's second route point because DCS serialized x, y and ETA to
14 significant digits. No other guarded field differed.

`check_loaded.lua` executes the real installed bridge against the retained
`loaded-tempMission.miz` serialization. It reproduces the exact route-y mismatch
with the original package. `prepare_reference.py` admits only the three reviewed
paths, each exactly equal to its original value formatted to 14 significant
digits. The corrected reference passes; six negative controls still reject
modified aircraft positions, witness route, ETA, aircraft count, trigger and
weather. Runtime comparison is still exact. The mission, tape and source pose
are not altered by this reference repair.

Separately, mission telemetry reported playback height about 0.099 m above the
recorded initial height by ten seconds, despite repeated immediate native pose
writes matching the commanded height. The aircraft remained grounded and healthy
in the sampled data, but this does not meet or prove exact held placement.
No hold, countdown or release acceptance is claimed.

The updated ground-only DLL adds read-only `ground-pose-<pid>.csv` samples at
SDK entry, immediately before/after the existing native integration hook and
after native animation. Each row includes commanded and precise/float native
positions. This distinguishes where pose replacement occurs without bypassing
native ground behavior or adding motion writes. It is diagnostic instrumentation,
not a repair or proof of physical contact. The six selected native checks pass.

Next live step: reload the same ground mission, click Fly, and remain held for
the 30-second inspection. Do not request release. Preserve the boundary trace,
native logs, mission/contact telemetry and user observation before deciding the
pose-retention repair. The task and parent checklist remain open.
