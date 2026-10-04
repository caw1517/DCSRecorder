# Real-object held-start control (bounded airborne hold accepted)

The separate `HornetHeldProbe` target fixes replay time to zero, commands strictly
zero linear/angular motion, and holds the original first-sample pose and supported
state. Initial recorded velocity remains in the tape for later release work.
Only this hold-only target accepts zero native velocity; the recording reader
and all other controllers retain their previous speed guards. Speed-brake
argument 21 is reapplied at the same post-animation boundary as other channels.
No release transition, countdown or parked completion is implemented here.

The planned airborne control keeps the player in Active Pause, shows the real
playback aircraft from startup, and observes thirty seconds while an unrelated
stock witness aircraft continues flying. It records identity, pose, motion,
appearance, engine reads and replay clock. A ninety-second cleanup bound removes
the diagnostic lead. Ground staging, smoke onset before the first mission tick,
audio/visual first-frame behavior and normal failure cleanup still require live
evidence. This is not production staging or acceptance.

The DLL builds and its policy/owned-object callback checks pass. The callback
harness now accepts an explicit owned-staged mode instead of inferring this new
DLL's policy incorrectly from its filename. Existing test behavior is retained.

The initial build block on 2.9.30.28536 led to static and read-only live layout
checks. A separate compile-time profile now supports preparing the isolated
hold diagnostic on that exact build, with all byte/identity/ownership guards
retained. Its package validators and offline contracts pass. The user elected
to test normal record-to-playback through a separate companion trial first.
The separate hold module is now installed after the accepted companion trial;
the bounded airborne live hold is now accepted. See the installation checkpoint in the
[held-start evidence record](../results/held-start-2026-09-30/README.md).
Read [the compatibility capture protocol](../build-compatibility/README.md).

The user completed the 30-second observation and confirmed a perfectly still
lead, moving scene witness and steady engine sound. The
[live evidence](../results/held-staging-2026-09-30/README.md) and `analyze.py`
retain the measured result. Complete first-frame snapshot, release, ground and
parked-completion acceptance remain separate tasks.

`Install-Control.ps1` validates the exact package/build and installs only new
module/mission paths with DCS closed. It refuses existing destinations, verifies
all installed hashes and checks existing runtime/user files remain unchanged.
Use `-ValidateOnly` to inspect an uninstalled package without copying files.
