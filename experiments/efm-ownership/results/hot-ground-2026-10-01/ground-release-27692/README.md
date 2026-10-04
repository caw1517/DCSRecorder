# Accepted short ground hold and first taxi release

User review: "Stationary and unchanged" at inspection, then "Worked and
everythign looked good" after countdown/release. See resolution.md for the
scoped result and measured limitations. summary.json retains phase measurements;
state-summary.json checks requested versus retained changing state. Raw native
and mission logs are in raw/. No video/audio capture was made; user review is
the visual acceptance evidence.

Implementation remains local and uncommitted in experiments/efm-ownership:
ground-start/contact.lua, source_evidence.py, tape_gate.h, prepare_playback.py,
recorded_flight.py, recorded_path.h, native_velocity.h, object_probe.cpp.
Ground-start CMake and check_path.cpp preserve the evidence-bound speed guard.
ground-start/check_held_pose.py runs the live boundary regression check.

Results in results/hot-ground-2026-10-01 retain the original source, source-contact
trace, failed capture diagnosis, readiness failure, failed height hold, accepted
held-pose-27692, ground-release-package-v3 and its update receipt. The latter
identifies the installed DLL and 13 unchanged payload files. Trace instrumentation
remains confined to the experimental ground build for subsequent ground evidence;
it is not a production feature or general release package.

Important analysis distinction: summary.json's nearest-source-row state maximum
is dominated by sampled strobe-edge hold at floating-point boundaries. It is not
a retention error. check_state.py instead pairs each mission sample with the
controller's requested channels for that tick and verifies post-animation and
mission-visible retention; all 32,703 comparisons pass. The one-sample edge timing
residual itself is retained for subsequent numerical agreement, not erased.

The trace grouping by replay_time==0 includes the first running frame, which
correctly uses recorded tiny initial velocity. The countdown-only mission rows
show precisely zero movement and replay time. Native post-step motion is up to
one 20 ms integration step ahead of the command. This is recorded as a measured
residual, not silently adopted as an acceptance threshold.
