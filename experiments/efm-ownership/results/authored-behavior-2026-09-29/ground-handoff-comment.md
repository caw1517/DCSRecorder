## Wayfinder handoff — planning blockers resolved; implementation remains open

The six decision prerequisites now have resolutions: Mission Editor integration, visible staging/parked completion, aircraft registration, acceptance, mission identity and authored behavior compatibility. Their decisions remain canonical in their linked tickets; this milestone is not completed by those closures.

The latest evidence and contract are in [Prove mission identity and edit detection across Mission Editor saves](https://github.com/caw1517/DCSRecorder/issues/18#issuecomment-5903365767) and [Define compatibility with authored triggers and aircraft tasks](https://github.com/caw1517/DCSRecorder/issues/19). The temporary identity hook was removed and DCS restarted without it. Authored-behavior controls require no installed hook; only disposable scratch missions remain.

Recommended implementation order:

1. Prove the risky integration boundaries in isolated controls: real-object hot-ground/airborne held staging with one clock and complete supported initial state; fresh loaded-session authorization with refusal when absent/stale/unverified. The filename-hash counterexample must remain in regression evidence. Do not widen advertised support based on a positive file hash.
2. Build authored-source preparation and companion association/revision review around those proven boundaries. Preserve supported mission content, report conflicts, allocate owned identifiers/resources, keep repeated preparation deterministic, and retain the existing accepted airborne/legacy path while migration is verified.
3. Integrate taxi/takeoff/landing/parked completion, stationary and duration support, exact supported state holds and failure/restart cleanup. Repair and measure the documented speed-brake retention gap. Coordinate ground-contact/flight-envelope evidence with their existing owner issues; do not merely remove guards.
4. Run the agreed complete parking-to-parking acceptance, including scene preservation, initial/countdown/first-motion state, endpoint holds, failure/restart/pause and the 20–30-minute target with user review. Registration migration and rollback retain their separate gate.

The user prefers agent-prepared files and log inspection with manual DCS steps, one check at a time. Continue that workflow. Layers, other aircraft types, voice, intentional flight relocation and startup/shutdown remain deferred. No production implementation or acceptance is claimed by this planning pass.
