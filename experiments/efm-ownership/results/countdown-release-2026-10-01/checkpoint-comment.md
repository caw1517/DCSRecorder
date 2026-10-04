## Wayfinder checkpoint — countdown control installed; live acceptance pending

Claimed **Release player and playback on one countdown clock** and inspected the parent contract plus the accepted [complete supported playback snapshot](https://github.com/caw1517/DCSRecorder/issues/21#issuecomment-5924345948).

Prepared a separate `HornetReleaseProbe` diagnostic. It keeps the first pose and supported state at replay time zero during inspection/countdown, commits one native release latch, restores initial recorded velocity at the next native callback, and samples motion/exterior/engine state from that callback-owned epoch. Smoke follows the published native replay time. A session-bound user hook dispatches player Active Pause release immediately after the native commit in the same hook callback, with mission acknowledgment and native epoch logs for comparison. Actual simulator/render ordering remains to be measured.

Eleven selected offline checks pass, including existing held/snapshot/updated-build callback regressions and new clock, mission, hook and real DLL ABI checks. Generated mission dependency, route, configuration, nested Lua and complete snapshot/smoke-schema checks pass. A preparation-only serialization defect was caught and corrected before installation; the retained `gear-package-v2` is the current package.

Installed **043-Hornet-Countdown-Release.miz**, its separate module and diagnostic hook with DCS closed. All 14 payload hashes match; 1,129 pre-existing files were verified unchanged. The input is the accepted 8.70-second gear-down take with recorded smoke ON.

Implementation and local evidence are in `experiments/efm-ownership/release-start/` and `experiments/efm-ownership/results/countdown-release-2026-10-01/`. These workspace changes are not yet a published source checkpoint. The package manifest and installation receipt are retained locally.

Next: one user-operated normal release run, followed by log analysis and visual/audio review. First movement, visible smoke onset, release synchronization, actual pause, repeated requests and live readiness refusal remain unaccepted. The task and its parent checklist stay open; no acceptance criterion is checked off from offline evidence alone.
