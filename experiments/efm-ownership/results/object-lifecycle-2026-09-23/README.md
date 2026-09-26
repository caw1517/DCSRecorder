# Startup-loaded object callback result

Fresh DCS log: 2026-09-24 02:57:43 UTC. Installed probe SHA-256 matches the prepared lifecycle revision (5213503864A71AFAF1A07355ABF4D54855BFFCCDE271B600E0F4EF92CFF8B50E).

- DCS loaded OwnershipProbe.dll at startup.
- The probe received API setup, one object-create event, 970 simulation callbacks and one destroy event for object ID 16777472. Sampled callback times reach 19.32 seconds (189 sampled simulation rows).
- Independent mission telemetry observed Probe (mission ID 9001) and Observer (mission ID 2) through 19.3 seconds.
- No new ordinary EFM callback CSV was produced. Startup loading therefore enabled the documented object callback route, but did not establish EFM execution for the AI aircraft.

This is positive evidence for object lifecycle execution alongside a stock player. Target identity is not yet independently confirmed: the SDK ID and mission ID differ. The Sim Control API documents an explicit mission-to-runtime-ID mapping; the next diagnostic uses that rather than guessing a conversion. No pose or force control has been demonstrated.

Evidence: objects.csv and dcs-excerpt.txt. Next probe: hooks/ownership-id-map.lua, a read-only mapping logger restricted to EFM-Probe missions. A fresh short AI mission run is sufficient; compare its runtime ID with the newly generated object-callback ID, not with a prior process's ID.
