# Roll video feedback: pitch motion and engine appearance

2026-09-26. User supplied `C:/Users/w_can/Downloads/Roll.mp4` (17.59 s)
and reported a small pitch movement near inversion and as the roll descends
and levels. They also reported unexpected afterburner/exterior engine state
while the intended throttle was well back. They requested noting the engine
mismatch for later work. This review changes no mission or installed DLL.

## Evidence reviewed

- Source identity and metadata: `evidence.json`.
- `overview.jpg`: one-second frame samples; `inverted-contact.jpg` and
  `recovery-contact.jpg`: quarter-second samples around video seconds 7–12
  and 12–17. Source video remains in Downloads.
- `native-motion.csv`: snapshot of process 39268's live log, containing
  four captures/runs. Some runs stop before the maneuver completes; these
  are not complete release-validation runs.
- `intertick.json`: output of the existing reproducible analyzer:
  `python experiments/efm-ownership/analyze_intertick.py experiments/efm-ownership/results/roll-video-review-2026-09-26/native-motion.csv`.

The clip is a following cockpit view. Both the player aircraft and camera
move, so relative image motion alone cannot establish the playback object's
world-space pitch. Bright exhaust is visible near the start and fades later;
it is consistent with the user's engine-visual report. No synchronized
engine/afterburner-state telemetry was captured, so visual flame/glow is not
proof of an actual native throttle or RPM value.

## Motion findings and limits

Across the snapshot, immediately-after-command orientation error is at most
about 0.0000024 degrees. Before the next command, maximum basis-axis error
is about 0.244 degrees; maximum pitch component error is about 0.148 degrees.
Near the commanded inverted point (mission time about 30.74 s), the pitch
correction reaches about 0.097 degrees in a +/-2-second window. This shows
small between-update corrections exist, but does not identify them as the
cause of the user's visible twitch.

After the initial settling interval, the sampled commanded pitch has only
the planned maximum and minimum (mission times about 24.62 and 36.00 s);
no additional pitch reversal was found in the complete descent samples.
There is no evidence here for an extra commanded pitch reversal at inversion.
This does not rule out perceptible changes in angular acceleration or
rendered interpolation. One run includes a long wall-time interruption;
without exact video-to-run alignment, it cannot be attributed to the clip.

A deterministic reproduction of the specific visible twitch is not yet
established. The telemetry analyzer measures correction magnitudes, not a
proven visual-defect pass/fail condition. Therefore no speculative controller
or roll-curve fix was applied. Next diagnostic should align a known run's
video timestamps with commanded/pre-command/post-command pitch and compare
a fixed external camera with the following cockpit view. Candidate factors
to distinguish are curve pacing/acceleration, between-update native motion,
and player/camera-relative motion. None is assigned as the cause yet.

## Deferred engine-state requirement

The offline constant-thrust calculation supplies target motion only; it
does not command the playback object's native engine state. Current exterior
controls hold speed brake/lights, not throttle, RPM, nozzles, exhaust effects
or sound. Thus matching path/speed does not establish engine-state fidelity.

Record throttle command and per-engine RPM/afterburner state separately.
Playback must synchronize those states with nozzle/flame effects and audio.
Acceptance case: recorded non-afterburning flight remains non-afterburning;
recorded burner transitions occur at the same timeline positions across
layered playback aircraft. Test sound separately; an animation setter alone
must not be assumed to drive engine audio.

Real recorded paths will remove the synthetic speed/roll prediction, but
will not automatically solve playback timing, native corrections, engine
appearance or sound. Preserve this clip as a comparison for recorded-flight
playback rather than treating synthetic geometry as the confirmed cause.
