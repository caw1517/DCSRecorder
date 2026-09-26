# Hornet right-level-left test

Prepared and installed 2026-09-26; the user responded "Excellent!" after this
test, then authorized the roll prototype. This is stage 2
of the user's requested sequence. Stage 1's approved mission and DLL remain
in `experiments/efm-ownership/results/hornet-validated-2026-09-26/`.

The two-turn DLL, mission, manifest and path source were preserved in
`experiments/efm-ownership/results/hornet-right-level-left-2026-09-26/`
before preparing the roll. The currently installed DLL now uses the roll
profile; restore this archived DLL with its mission for the two-turn test.

Open `EFM-Probe-Hornet-right-level-left-400KIAS.miz` and run 110 seconds.
Both jets retain the clean configuration, Blue Angels livery, exterior
lights off and calm weather. Playback speed brake remains stowed.
Nominal 400 KIAS uses the established 225.02157 m/s world-speed target.
Each turn preserves the approved six-second roll-in, three-second roll-out
and steady 2.5 g geometric path (66.42-degree bank). Actual aerodynamic
load and exact indicated airspeed are not established by this controller.

| Mission seconds | Playback segment |
| --- | --- |
| 0–5 | Native flight before capture |
| 5–7 | Settle onto controlled path |
| 7–42.96 | 180-degree right turn |
| 42.96–52.96 | Ten seconds straight and level |
| 52.96–88.92 | 180-degree left turn |
| 88.92–94.92 | Straight, wings level, original heading |
| After 94.92 | Release motion control; observe through 110 seconds |

The path sums one positive and one delayed negative turn-angle function.
Each eased heading-rate function integrates to 180 degrees. Continuous
horizontal integration spans both turns and the middle segment; position
is never reset between segments. Bank follows signed curvature, so the
second turn mirrors the first. Cosmetic defaults continue after motion release.

All four CTests passed, including both callback contracts and trajectory
profiles. The Hornet checks cover intermediate and final heading, bank sign
reversal, position-derived 2.5 g in both turns, no rotation or altitude change
during the straight segment, transition continuity, tangent alignment,
motion prediction, and native speed/step bounds over the full path.
Packaging checks for module requirements, datalinks, route timing, clean
loadouts, lights-off trigger and Lua syntax passed. Installed hashes match
the package. These checks do not replace a live flight.

DLL SHA-256: `8ACDC44B9061B28B6F3926D85FBE7EB8855165122246467DDD8FA6DF13ADD1A8`.
Mission SHA-256: `35ED69F8D5A4988106282EF33B33992C060ED09B1A9B7B03A97B1FF29E033074`.

The Hornet path remains compiled into the DLL; the old single-turn mission
alone will not select its previous path with the new DLL installed. Restore
the archived baseline DLL and mission together if that comparison is needed.
TF-51D installed files are unchanged. Engine-state/audio playback, recording,
layering and the requested aerobatic roll remain separate future tests.

For the live check, evaluate the right-turn rollout into straight flight,
the left-turn entry and the final rollout for jumps, drift or wrong bank
direction. Preserve the Hornet object/motion logs and mission telemetry
after the run before declaring this stage validated.
