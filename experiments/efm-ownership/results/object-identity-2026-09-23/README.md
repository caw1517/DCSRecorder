# Confirmed callbacks for the unoccupied probe

Same-run evidence from DCS process 9296; DCS log opened 2026-09-24 03:03:09 UTC. The live log was captured after the user reported completion, so this is a snapshot and need not include a final destruction event.

The read-only Sim Control hook initially reported zero runtime IDs before spawn, then reported:

| Aircraft | Mission ID | Runtime ID |
| --- | --- | --- |
| Probe | 9001 | 16777472 |
| Stock player / Observer | 2 | 16777728 |

The object callback CSV from this same process records creation and repeated simulation callbacks for runtime ID **16777472**. Sampled rows reach 9.9 seconds and callback count 496. Independent mission telemetry observes both Probe and Observer through 9.9 seconds. Thus the object-callback target is the unoccupied probe, not the player's aircraft.

**Established:** the startup-loaded module receives per-object simulation callbacks for its unoccupied aircraft while another stock aircraft is player-occupied, within one player/account.

**Not established:** ordinary EFM execution for the AI aircraft, applying forces to it, modifying its physical pose, suppressing or coordinating its native AI physics, or faithful recorded-flight playback. The published object API still exposes IDs and visual arguments, not force/pose control. The known damage-model errors also preclude physical-fidelity claims.

Retained evidence: objects.csv and dcs-excerpt.txt. Next investigation is the bridge from this identified opaque object handle to a validated physics/pose interface; another logging-only simulator run is not needed to establish identity.
