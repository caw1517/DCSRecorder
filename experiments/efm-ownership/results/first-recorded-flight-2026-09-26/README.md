# First successful live Hornet capture

Subsequent playback worked and its jitter was substantially reduced. See the
[accepted follow-up baseline](../recorded-jitter-2026-09-26/README.md). This file
preserves the initial capture/installation record.

The mission-owned recorder completed take 1 with 1940 sequenced samples and an
explicit user-stop footer. Extraction produced `take-1-ece58381f446ed81.csv`.
`recording-events.log` preserves only the relevant original timestamped events.

- Aircraft: FA-18C_hornet; livery: Blue Angels Jet Team; terrain: Caucasus.
- Simulation time 5.647–44.427: 38.78 seconds, sampled every 0.02 seconds.
- World speed: 221.785–227.677 m/s.
- MSL altitude: 1994.595–2105.420 m.
- Initial pitch: 1.999 degrees; initial attitude is within acquisition limits.
- Complete sequence and metadata, finite orthonormal pose, position/velocity
  consistency, speed/altitude/rate limits all pass `recorded_flight.read`.

The first/last DATA log timestamps span 38.778 seconds, with a maximum adjacent
wall-log gap of 0.033 seconds. The user confirmed they did not pause during this
take; the earlier question concerned the timing design. Continuous capture is
verified. Live pause validation is deferred at the user's preference.
No timing gaps were removed or repaired in the recording.

`package/first-recorded-flight` contains the matching prepared playback DLL,
tape, mission, metadata, original CSV and hash manifest. Installed DCS module
requirements, route timing, clean loadouts and light commands pass packaging
checks. The actual C++ path evaluator loaded this tape and checked interpolation
at 100 Hz against native speed, altitude and angular-rate limits. Live playback
of this take remains unverified.

The prior installed synthetic roll DLL/mission pair is preserved under
`synthetic-roll-rollback/` with its hashes. After the user closed DCS, the matching
recorded-flight DLL, tape and mission were installed and their hashes verified
against the prepared manifest (`installed-playback.json`). The completed CSV
was copied to Saved Games/DCS/DCSRecorder/recordings. This changes the Hornet
prototype's active path; restore the archived DLL to rerun the synthetic roll.
Playback acquires control around mission second 5 and releases around 43.78.
