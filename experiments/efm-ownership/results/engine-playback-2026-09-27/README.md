# Isolated engine appearance accepted; sound unresolved

THROWAWAY evidence for [Complete single-aircraft visual and engine-state fidelity](https://github.com/caw1517/DCSRecorder/issues/6), DCS 2.9.29.27468.

The user reported: "The animations all looked correct, but the sound did not
follow at all. It seemed like it just played the idle sounds the whole time."
Accept the isolated nozzle/flame rendering. Sound fidelity fails this observation;
the appearance experiment only writes arguments 28/29/89/90, not engine sound.
No engine appearance integration with recorded motion is claimed yet.

Retained local evidence: `live.log`, `state-13932-332403078.csv`,
`post-animation-13932-332403078.csv`, `events-13932-332403078.csv` and
`summary.json`. There are 2,501 native frames through elapsed 50.0 seconds and
999 later mission observations. All four channels match requested values exactly
immediately after the write; later mission maximum error is 5.000000414e-10
(printed-value precision). The 48.9-second sequence completed, but the session
ended during the eight-second hold. Automatic removal is not established by
this run; the log has no mission END. Destruction was observed at exit.

## Next question: are ordinary engine parameters queried?

Installed primary sources:

- `D:/DCS World/API/include/FM/wHumanCustomPhysicsAPI.h`: engine block zero is
  APU, block one the leftmost engine, block two the next engine. Engine-one
  related RPM/core RPM/thrust are indices 101/103/105; sound/power gain is 128.
- `D:/DCS World/API/ExternalFMTemplate/ED_FM_Template/ED_FM_Template.cpp`:
  the bundled `ed_fm_get_param` returns throttle-derived engine-one parameters
  and defaults other parameters to zero. Our ordinary getter was uninstrumented.

The SDK declarations do not prove this unoccupied playback object calls the
getter. Earlier ordinary-callback evidence concerns a different test/build.
Do not try to fix sound by returning captured RPM until reachability is measured.

The separate `HornetEngineSoundProbe` forwards the sample getter unchanged and
logs first calls per index plus cumulative counts at object setup/create/destroy.
The ready marker and lifecycle rows distinguish zero queries from a missing or
unloaded logger. Logs go to its own `bin/sound-logs`. Counts are module scoped;
even observed queries do not establish that the caller is the audio engine.
The accepted four-channel animation and normal AI route remain the experiment.

Offline validation: 66 getter calls across 22 indices forward unchanged and
produce first-call rows; the native actuator rejects fake non-DCS identity before
writes, with ready/setup/create/destroy rows. Mission completion, failure,
timeout and stop checks pass, as do installed dependency/route/configuration
validators. Ten installed hashes match; 23 protected existing files are unchanged.
Fixture logs stay in the local package and are excluded from installation.
All prototype targets rebuild and the 15 existing CTests pass.

Run **DCSRecorder-Engine-Sound-Probe.miz** after restarting DCS. F10 >
**Engine appearance playback** > **Start captured engine sequence**, then F2.
Let the lead disappear after about 57 seconds and retain the session for collection.
This is an observation probe; no audible correction is expected. Live result pending.
