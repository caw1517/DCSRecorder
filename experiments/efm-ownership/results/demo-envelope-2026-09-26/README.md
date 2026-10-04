# Demo envelope expansion — September 26, 2026

## Required outcome

The user's Blue Angels workflow must cover a complete flight: exact stationary
start, taxi, takeoff, low passes around 250–500 ft AGL, hard turns including the
requested 7.5-G / 350-knot maneuver, approach, touchdown and rollout. Artificial
altitude or G/rate restrictions are not product requirements. Capture and playback
must preserve the recorded movement rather than ask the pilot to soften it.
Afterburner appearance/sound and gear/contact state also require implementation
and evidence. These are necessary parts of one-aircraft completion, before layers.

## Implemented and installed in this step

- Removed altitude floor/ceiling and angular-rate rejection from CSV/tape loading.
- Removed altitude/rate caps from the active staged controller, including the
  pre-integration override. Legacy synthetic probe guards are unchanged.
- Retained finite-data, orientation-basis, timestamp, continuity, build, ownership,
  and native-layout validation and the accepted presentation-pitch correction.
- Tightened quaternion spherical interpolation: the prior linear fallback caused
  a small rate ripple in the 180 deg/s synthetic roll. Peak rate error changed
  from 0.000446924 to 0.00000520681 rad/s in that regression.
- Preserved both original rejected recordings. Both pass actual library validation,
  conversion, native evaluation at 100 Hz and mission generation checks.
- Installed controller SHA256
  2260f6a07bb04190d7f1224e012e33e2e43c09a1e9153435b366881d454dbb08.
  Verified rollback holds the prior accepted controller and active tape.
- Active live test: DCSRecorder-Playback-4bcc7985.miz, 80.92 seconds.
  Second test package is prepared but not active; its mission must be activated
  with its matching tape before use.

## Validation and limits of evidence

The library regression failed first for the old altitude/rate restrictions and
passes now. Native demo geometry covers fast 180 deg/s rolls and a modeled 7.5-G
level turn at 350 knots through recorded altitudes -50, 0, 76.2, 152.4 and 6000 m.
Those are MSL coordinate tests, not terrain/AGL or contact tests. The kinematic turn
fixture does not prove DCS loads, thrust, afterburner fidelity or real aircraft
performance. Synthetic maximum position error is 4.98e-9 m and basis component
error is 3.28e-15; neither is a claim about live rendered accuracy.

13 native CTest checks and 10 companion unittest checks pass. The native converted
recordings were evaluated in exact-start mode at 100 Hz. Both originals' hashes
were verified unchanged. The running companion was restarted and checked through
its actual /api/library endpoint. No code was committed or published.

Live validation remains pending. Replay the active take through Playback complete,
check for nose jumps, stutters, path errors, premature disappearance and controller
failure, then inspect the mission/native logs. Repeat with the second take.

## Remaining required implementation

- Ground staging at the recorded location and heading, zero-speed handling and
  synchronized initial state; the current 70–260 m/s airborne speed restriction
  still prevents stationary/taxi portions from being treated as supported.
- Capture/replay gear, flaps and supported exterior/engine states, including
  afterburner appearance/sound where available. Current schema contains pose,
  velocity and speed brake, not complete gear/engine state.
- Verify ground contact, taxi, liftoff, low passes, touchdown and rollout against
  real recordings, coordinating the physical-interaction investigation.
- Full-demo recording duration: the current 5–300 second prototype bound is not
  a final duration requirement. Longer-flight storage, timing and playback need
  evidence before claiming an entire demonstration works.

Relevant existing tickets:
- Validate the single-aircraft flight envelope through takeoff and landing:
  https://github.com/caw1517/DCSRecorder/issues/7
- Reproduce the exact starting position and synchronized aircraft state:
  https://github.com/caw1517/DCSRecorder/issues/11
- Aircraft-state fidelity: https://github.com/caw1517/DCSRecorder/issues/6
- Physical interactions: https://github.com/caw1517/DCSRecorder/issues/3

See verification.json and installation.json for package paths, source fingerprints,
installed mission, controller fingerprints and rollback location. Generated missions,
raw recordings and DCS assets remain local.
