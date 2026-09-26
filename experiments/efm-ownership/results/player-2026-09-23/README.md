# First player-occupied run

Installed DCS build: 2.9.29.27278. User flew EFM-Probe-player and reported coasting with a slow right roll.

The retained callback log contains 3,476 simulate calls and 3,476 state calls over 20.856 accumulated simulation seconds. The orientation is unchanged through the last pre-pulse sample at 4.974 seconds. At 5.028 seconds the logged roll moment is 4,000 N*m and the quaternion begins changing; pulse output is zero again at 5.514 seconds. This supports successful execution of the player aircraft's EFM and a state response consistent with the diagnostic pulse.

The independent mission observer produced no rows, so this run is not a complete independently measured control. The generator was changed to include a mission-start trigger and its editable trigrules representation, plus a visible telemetry-active message. That correction remains runtime-unverified.

The DCS log also reports a corrupt damage model for the renamed aircraft. Therefore this probe must not be used to claim collision/damage fidelity. It is an airborne callback-ownership diagnostic only.

No AI-target run has been observed. No conclusion about non-player EFM execution is available yet.
