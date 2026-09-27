# Staged recorded-playback integration

Issue: Make the single-aircraft record-to-replay workflow reliable. This is the
accepted native integration used by the local companion app. See the current
[validation record](../../docs/validation/workflow-2026-09-26.md) for workflow acceptance.

## Implemented for testing

- Separate custom aircraft `DCSRecorder-Hornet-Staged` and `HornetStagedProbe.dll`.
  Existing accepted Hornet aircraft/DLL/tape remain available unchanged.
- Active Pause holds the stock player; F10 requests a three-second countdown.
  Actual activation/release, including trigger delay, starts the integration.
- The controller binds to its SDK-created runtime object and begins its tape
  clock at the first eligible simulation callback after activation. It commands
  original world pose, measured initial velocity and recorded speed brake without
  the legacy translation or two-second attitude blend. Other exterior/engine
  channels retain existing limited support; complete initial state is not claimed.
- Existing native identity, build signatures, speed and ten-metre step
  limits remain. One custom object only; a second is rejected.
- SDK draw arguments 997/998 carry a 48-bit tape fingerprint; 999 carries running,
  completed or failed state. The controller checks view bounds and readback before
  claiming progress. These deliberately separate custom-aircraft arguments and
  their mission-side visibility were confirmed for start and completion in the live run on DCS 2.9.29.27468. Failure to obtain
  a matching start signal removes the aircraft with an explicit error.
- Mission completion follows the controller signal, removes only the playback
  aircraft, and leaves the mission and any independent recorder alone. Native
  completion applies the final tape sample and restores the physics-step hook.
- Packages target the locally evidenced DCS 2.9.29.27468 build. Content hashes bind
  the files and installation rejects a running simulator or existing destination.

## Verification

Thirteen CTests cover existing motion/callback regressions plus exact start,
status bounds/readback, tape mismatch detection, dynamic runtime identity,
delayed mission release, duplicate F10, controller errors/timeouts and completion
without stopping an independent recording in the mock lifecycle. Mock pause and
restart checks do not establish live behavior. Generated mission module, route,
clean-configuration and Lua syntax checks pass.

The live acceptance checks cover custom module registration, SDK status channel
visibility, late-activation identity, initialization correction, native start
clock versus mission release, continuous motion and completion/destruction.
Preserve DCS.log plus this mod's bin/probe-logs directory. Retain the first frame
and compare the native commanded pose/velocity with the original first sample;
a plausible formation view is not proof of exact initialization. The existing
jitter analyzer's fixed 7..42-second window is for the old automatic-start test;
use a start-relative window for this run. Do not compare a shifted maneuver segment.

## Live result: 26 September 2026

The user accepted full playback completion, corroborated by the third run in
DCS process 13152. Native playback ran from 5.801 to 44.581 seconds: the complete
38.78-second tape and 1,940 successful motion writes. The mission observed
COMPLETE at 44.600 seconds; the native physics hook restored and the playback
object was destroyed. Player telemetry continued for 3.96 seconds. One final
lead sample appeared on the completion tick; none appeared on later ticks.
First and last commanded positions matched the tape; initial native position
readback differed by 6.93 mm and initial velocity matched at logged precision.
Earlier runs demonstrated two successful starts but the user ended them early.

Local evidence: E:/Projects/DCS_Recorder/experiments/efm-ownership/results/staged-playback-completion-2026-09-26/README.md

The later app-managed 80.92-second hard-turn take completed all 4,047 samples.
The user also reports the remaining requested workflow checks passed. Broader
aircraft state, ground contact, layers and other DCS builds remain follow-up work.

## Prepare and install

Build from this checkout, then run prepare_staged_playback.py with the accepted
source CSV, a fresh output directory, --baseline pointing at the existing local
Hornet donor mission and --donor-mod pointing at its generated mod directory.
Local game assets and generated packages stay ignored and unpublished.

With DCS closed, Install-StagedPlayback.ps1 verifies hashes/build and installs only
the new mod and DCSRecorder-Staged-Playback.miz. It refuses to overwrite an existing
installation. A DCS restart is required to load the new module.

## Live run

1. Load DCSRecorder-Staged-Playback.miz and enter the stock Hornet cockpit.
2. Wait about ten seconds without manually toggling pause, then choose the
   communications menu F10 > DCS Recorder > Start playback.
3. After the countdown, expect the recorded lead roughly 150 feet ahead and a
   Playback running message. Fly alongside the full 38.78-second recording.
4. Expect Playback complete and the lead disappearing while your mission continues.
   If a failure message appears, preserve it and the logs; do not call this a pass.
5. Restart the mission and repeat with a longer wait. Separately test a normal
   simulator pause mid-playback before claiming pause behavior.

The companion app now provides automatic save, selection and preparation. The
user accepted the current airborne workflow; ground operations and full aircraft
state remain separate requirements. Altitude and angular-rate caps were removed
from the staged controller; the accepted nose-jump correction is retained.
