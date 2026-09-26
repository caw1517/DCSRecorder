# First live capture failure and mission-owned replacement

The first user flight produced no recording directory or saved take. The live
log (`live-errors.txt`) identified two failures in the installed GUI hook:

- `onSimulationFrame` preceded timer initialization: line 49 compared a number
  with nil. Reproduced by invoking a frame before `onSimulationStart`.
- After initialization, `a_do_script` was unavailable in the isolated user hook.
  Reproduced by removing the bridge from the fake host. The original harness
  incorrectly supplied it and always invoked startup before frames.

The failed hook, harness and installed mission are retained here. Both failures
were reproduced before the change; the precise log errors made speculative
ranked hypotheses unnecessary. The old harness command was:

```powershell
& 'D:/DCS World/bin/luae.exe' experiments/efm-ownership/check_recording.lua E:/Projects/DCS_Recorder/experiments/efm-ownership E:/Projects/DCS_Recorder/experiments/efm-ownership/package/recording-check E:/Projects/DCS_Recorder/experiments/efm-ownership/package/recording/mission before_start
```

It failed with `attempt to compare number with nil`. The `no_bridge` variant
failed its recording assertions after the hook reported bridge unavailable.
The archived files represent that revision; the active harness is now different.

The fix removes this cross-environment dependency. The mission owns sampling
and emits versioned BEGIN/DATA/END events through `env.info`; Python extracts
complete sequenced takes afterward. Simulation-time scheduling excludes pauses.
An inactive compatibility hook replaces the failed one. Explicit F10 Stop is
required, and the confirmation includes a sample count. RPM telemetry is deferred
and left blank. The log transport is a prototype mechanism, not a final product
storage design.

`check_recorded_flight.py` passes the corrected packaged mission through a
restricted fake mission environment without a GUI bridge, tests 6000 frames with
frozen simulation time, two complete takes and one abandoned take, missing-row
rejection, idempotent extraction, CSV validation, mission packaging and native
playback evaluation. The replacement hook also loads with no initialized
simulator. Output is in `fixed-checks.txt`.

The corrected mission/hook were installed and hashes verified while DCS was
still running. Restart is necessary to retire the old in-memory hook. No DLL was
changed. A 10–15 second live capture retry with a pause remains necessary before
claiming live success or preparing playback from a real take.
