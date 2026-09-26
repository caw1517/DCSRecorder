# Aircraft update-suppression experiment

Prepared 2026-09-25. DCS 2.9.29.27278 only. Live result pending.

Live update: [result note](../../experiments/efm-ownership/results/update-gate-2026-09-25/README.md).
Suppression succeeded (750 intervals with zero sampled intertick motion),
and restoration at 30 s succeeded. User reported worse middle-interval
jitter. The path now requires roughly 2.1 m corrections every 20 ms.
Reject freeze plus ForcePosition alone as the smooth playback solution;
continuous motion/interpolation remains necessary. The sections below
preserve the original experiment protocol.

## FSX lead

The user's recollection led to a relevant first-person implementation report:
[B21's FSDeveloper thread](https://www.fsdeveloper.com/forum/threads/smooth-ai-movement-the-old-favorite.17374/).
The author reported smoother relative motion by controlling slew velocities
instead of repeatedly setting absolute position, including a 100-aircraft
trial. This does not establish FS Recorder's internal implementation.

DCS's [official Controller documentation](https://www.digitalcombatsimulator.com/en/support/faq/1267/)
restricts setOnOff to ground/naval groups. The installed object API has no
freeze or slew method. AIFM exports setFreeze, but our probe's AIAerodyneFM
member is null; calling that function on this object would be invalid.

## Build-specific candidate

The captured DCS .text shows a byte at complete woAIPlane +0x4fea:

- Constructor initializes it to zero at RVA 0x6cd4ac.
- RVA 0x6fbfd9 tests it; nonzero skips to the epilogue at 0x700a61 of
  the routine beginning 0x6fbf60.
- RVA 0x70ff62 tests it; nonzero skips to 0x713b0c in the pose integration
  routine beginning 0x70fef0.

Its original name and complete semantics are unknown. Do not describe it
as a supported freeze API or claim it disables every subsystem. A scan for
the literal displacement found only these three object references; other
forms of access may exist. No executable code is patched.

The scheduler at RVA 0x675230 invokes vtable +0xc70 (0x70fef0), then
separately invokes +0xc10 (0x6b6070) and advances its scheduled time. This
supports continuing object activity when the first routine returns early,
but the plugin callback's continued delivery still needs live verification.

## One-variable comparison

Keep the existing roll-rate A/B test, trajectory and mission unchanged.
Add only this byte intervention for the same 15–30 s window. This allows
comparison with the prior roll-only run at matching mission times.

- Enable only after a successful pose command on the identified probe.
- Verify both exact 13-byte branch signatures, identity, null FM, runtime
  ID, initial gate value zero, altitude, successful write and readback.
- Save the original byte; restore at 30 s, release, abort, or destruction
  while the object remains valid. Log restoration outcome.
- Stop control if an update or gate operation fails. No mutation of other
  aircraft, global clocks, binaries, mission settings or graphics settings.

CSV adds updates_suppressed and gate_status. Existing pre/post pose and
rate logging remains. analyze_intertick.py compares each pre-command pose
to the last applied pose, attributing the interval to the previous gate
state. Under successful suppression, position and attitude should remain
unchanged between commands. This differs from smooth continuous motion:
the renderer might still need matching velocity/interpolation information.

If callbacks cease, the aircraft may stop at the start of the intervention;
ending/restarting the mission discards that object. Do not attempt an
unsynchronized background-thread write to recover it. That outcome would
reject using this gate with the present callback architecture.

## Live procedure

Fly EFM-Probe-climbing-turn-formation.miz for 55 seconds. Check close
formation during 15–30 s, then look for a change when normal updates return
at 30 s. If useful, repeat farther away in F2. Keep the current graphics
settings. The first run is sufficient to establish whether callbacks,
pose control and restoration survive suppression.

Offline checks validate build/ABI/trajectory and analysis attribution only;
they cannot establish live suppression, display smoothness, collisions or
wake behavior. The feasibility decision remains open.

Build and both CTests passed; synthetic analysis checks cover gate-boundary
attribution and mission reset. Installed DLL SHA-256:
D142E080BA5CBC222D48357F3E0D423FF6618075DDAC9474581607DD3A346C48.
Previous roll-only DLL preserved in the roll-ab-2026-09-25 result folder.
