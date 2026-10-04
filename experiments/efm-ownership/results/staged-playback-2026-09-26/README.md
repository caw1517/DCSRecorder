# Staged recorded-playback live runs — 2026-09-26

The user reported both tests worked, then clarified that they restarted/exited
while the lead was still flying. These are successful start/restart runs, not
completed playback acceptance tests. DCS build: 2.9.29.27468.

- Run 1: F10 at 10.438s; native start at 13.801s; mission acknowledged at 13.820s. Captured 31.96s of the required 38.78s. All 1599 motion writes returned called.
- Run 2: F10 at 3.198s; native start at 6.801s; mission acknowledged at 6.820s. Captured 33.06s of the required 38.78s. All 1654 motion writes returned called.

Both runs held the player stationary before release at logged precision.
First commanded position matched the original recording, and native float
readback differed by about 6.93 mm; initial velocity matched at logged precision.
The fingerprint/status handshake reached NATIVE_STARTED in both lifecycles.
Neither mission FAILED nor COMPLETE was logged; neither native staged_complete
was logged. The object was destroyed when the user ended each run.

Next live check: let the recording finish, observe Playback complete and lead
removal, then continue flying for at least ten seconds. Mission pause/resume and
independent recording continuity remain separate unverified checks. No broader
state fidelity or compatibility claim is made.

Raw snapshots stay local and ignored. summary.json records hashes and metrics.
DCS.log also contains repeated third-party Volanta export errors; these are not
staged-controller failure events and were not changed during this task.
