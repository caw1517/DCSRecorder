# AI ownership comparison: tested EFM route fails

DCS 2.9.29.27278, fresh log opened 2026-09-24 01:07:36 UTC. The user ran EFM-Probe-ai after restarting DCS. The log identifies the player aircraft as stock TF-51D; independent mission telemetry identifies both `Probe` and `Observer` from 0.1 through 23.7 mission seconds.

## Evidence and result

- `observer.txt` records both aircraft moving. The AI probe remained near 2,000 m while the player aircraft followed a separate trajectory. Thus the missing callbacks cannot be explained simply by an absent AI target.
- `callback-directory.json` records only the two prior player-test CSVs. No new callback file appeared during this AI run.
- No `OwnershipProbe.dll` load appears in the inspected DCS log; relevant startup, spawn and registration lines are retained in `dcs-excerpt.txt`.
- The preceding player control successfully loaded this same DLL, recorded repeated simulation/state callbacks, and showed an independently observed attitude response during its scheduled roll pulse. See `../player-2026-09-23-telemetry/`.

**Conclusion:** the tested registration does not execute the probe EFM for the unoccupied AI aircraft alongside a stock player aircraft. Reject this configuration as an independent playback actuator; do not invest in trajectory tracking or multiple-instance tests on this basis.

This does not prove that every possible mod or engine integration is incapable of independent playback. The probe still has damage-model/livery registration errors, so no physical-fidelity conclusions are justified. There is also no evidence that those errors caused the missing AI EFM execution; the result is scoped to the tested configuration.

## Next decision

The initially proposed separate-account client route was subsequently rejected by the user: one player and one account are hard requirements. Investigate whether a custom integration can attach independently driven physics to an unoccupied aircraft within that constraint. Generating or loading an EFM DLL alone does not establish that attachment. Overall feasibility remains open.
