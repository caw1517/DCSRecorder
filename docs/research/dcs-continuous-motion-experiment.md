# Continuous motion matching and release

Prepared 2026-09-25 for DCS 2.9.29.27278. Live result pending.

2026-09-26 update: [live result](../../experiments/efm-ownership/results/continuous-motion-2026-09-26/README.md)
records 1,901 successful matched commands and release at 43.02 s. User
reports success. Observer telemetry ends at 49.7 s, short of the intended
ten seconds after release. The next separate experiment is the
[Hornet prototype](dcs-hornet-prototype.md).

## Change

Following the successful zero-wind control and the user's acceptance of
calm missions, apply matching linear velocity and local angular rates on
every controlled callback. Previously they were supplied only during
15–30 s; pose commands were supplied throughout. The only controller
change is to extend motion matching to the entire controlled interval.

Use the existing `EFM-Probe-climbing-turn-formation-zero-wind.miz` unchanged.
The 105 m/s formation trajectory, altitude, native-update behavior, object
and build guards, logging and release logic remain as before. No freeze
gate is used. No wind compensation is introduced.

## Live procedure

Start a fresh DCS process after installing the new DLL. Fly the zero-wind
formation mission for at least 55 simulation seconds, preferably 60.

- 0–5 s: native movement before capture.
- 5–7 s: capture and smoothly settle onto the controlled path.
- 7–37 s: 90-degree climbing turn, gaining 100 m.
- 37–43 s: separate pitch and roll excursions on the final heading.
- First callback after the 38-second controlled path (approximately mission
  time 43 s): log `released`, stop pose and motion writes, and observe
  native movement for at least another 10 seconds.

Watch for a jump at capture, sustained jitter through the turn, the small
pitch/roll movements near the end, and any stop, jump or instability at
release. Changes at 15 s and 30 s are no longer intentionally introduced.

Release means cessation of our writes. It does not guarantee recovery to
a physically correct flight model; the probe's null-FM setup is unchanged.
This experiment does not validate wake, collision or ground behavior.

## Evidence to collect

Preserve the new `native-motion-<PID>.csv` and same-run mission observer
telemetry. Verify one capture, successful commands with `motion_matched=1`
throughout, one release, no failed command, and no commanded rows after
release. Require independent observer samples beyond 53 s to establish
post-release observation. A run that ends early cannot pass the release
check, even if the controlled movement looks smooth.

Run `analyze_intertick.py` and compare the same 15–30 s segment with the
previous zero-wind result (mean position correction 0.01820 m and attitude
correction 0.08567 degrees). The analyzer's `matched` bucket now spans the
whole controlled flight, so its overall mean is not a direct comparison
to the old 15-second matched bucket. Assess capture, turn, final excursions
and release separately when reviewing the live result.

## Offline validation and rollback

Release build succeeded. Both existing CTests passed: callback contracts
and climbing-turn geometry/motion prediction. These validate the offline
contracts and generated path; they do not run the DCS native actuator or
establish live release behavior.

New DLL SHA-256:
`43511CE164D35A94678227007A0508A6C010FE36DB7FE1079906806F6512B3BD`.

The previous tested DLL is retained at
`experiments/efm-ownership/results/zero-wind-2026-09-25/OwnershipProbe-motion-window.dll`
with SHA-256
`6722E4E3C82243DC9852DCDAB5278F7B5FF7E85EFFC40A730C8D911A47F90591`.
Restore only with DCS closed if a rollback is needed.
