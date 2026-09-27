# First engine observation: mission data retained, Export gate failed

The user completed the diagnostic. The retained `first-live.log` contains 1,745
mission samples over 87.2 seconds, all seven phase markers, and explicit user-stop
footers. The mission-side data is useful. No Export engine values were captured:
every sample failed the hook's `ownship_identity_mismatch` assertion before
`LoGetEngineInfo` was called.

The first hook required both `LoGetSelfData().Name == FA-18C_hornet` and
`UnitName == Observer`, but did not log the returned fields. The trace therefore
cannot distinguish absent ownship data, a different type name, or a missing /
different unit name. None is asserted as the established runtime cause.

## Retained observations

Mission argument ranges, with transitions included in each marked phase:

| Phase | Samples | Argument 89 | Argument 90 | Argument 28 | Argument 29 |
| --- | ---: | --- | --- | --- | --- |
| Baseline | 247 | 0..0.743 | 0..0.743 | 0 | 0 |
| Both idle | 322 | 0.443..0.732 | 0.443..0.732 | 0 | 0 |
| Both military | 291 | 0.095..0.633 | 0.095..0.633 | 0 | 0 |
| Left afterburner | 231 | 0.172..0.204 | 0.294..1 | 0 | 0..1 |
| Right afterburner | 211 | 0.205..1 | 0.086..1 | 0..0.985 | 0..1 |
| Both afterburner | 174 | 1 | 0.170..1 | 0.987..1 | 0..0.937 |
| Both dry | 269 | 0.007..1 | 0.006..1 | 0..1 | 0..1 |

These suggest left-side candidates 90/29 and right-side candidates 89/28, based
on marked control changes. They are not independent visual identification or a
proven afterburner-state API. Markers precede manual throttle movement, so phase
ranges include response delay and transitions. Arguments 38/39/40/41 remain zero.
No audible comparison or playback actuation is established.

## Feedback loop and observation correction

Running `engine-prototype/analyze.py` on the retained log fails the alignment
screen: 1,745 mission samples, zero Export samples, identity errors on every row.
The analyzer now retains mission-only ranges even when Export samples are absent.

The corrected read-only hook logs observed ownship data type, numeric ID, aircraft
type and unit name on the first sample and whenever that tuple changes. It retains
available engine measurements beside the observed identity instead of throwing
them away for an unexpected/missing name. Unavailable names are empty CSV fields;
they are never replaced with the expected names. The analyzer still rejects
identity mismatch or missing identity and does not declare alignment verified.
Absent self-data/position or engine numbers remain explicit unavailable records.

Offline packaged-mission checks pass for normal capture, wrong unit name, missing
unit name, missing ownship table, unavailable engine API and delayed readings.
Wrong/missing names now retain all 121 synthetic engine samples with their raw
identity while still failing alignment. Missing self-data/API stays unavailable.
The original live capture still fails; this correction cannot recover unmeasured
engine data or establish the actual DCS identity layout without another sample.

After the user closed DCS, backed up the exact original diagnostic hook and
installed the corrected hook. Both installed diagnostic files match their
manifest, and the eight protected existing files remain unchanged. Local package,
backup and manifests are under `package/engine-diagnostic`; raw logs and summaries
remain local.

Next is only a short baseline capture (about ten seconds) in the same mission
after restarting DCS. Inspect the actual identity and engine feed before asking
for another full throttle sequence. The broader fidelity ticket remains open.

## Short live recheck: engine feed and timing verified

The subsequent `identity-check-live.log` contains 441 paired samples over 22.0
seconds with matching user-stop footers and no unavailable Export readings.
The original name comparison was invalid for this setup: Export reports aircraft
type `FA-18C_hornet`, unit name `New callsign`, and ID `16777472`; mission capture
identifies `Observer` with ID `2`. The corrected hook retained these actual values.

Export timestamps are 1..12 ms after their triggering mission sample. Comparing
positions at those unequal instants gives up to 2.916 m separation, as expected
for a moving aircraft. Interpolating the mission trajectory to each actual Export
time yields 440 in-range comparisons with maximum error 0.000947 m. The final
Export sample is beyond the last mission timestamp and is not extrapolated.
The Export read clock has no measurable advance at its reported precision.

Both engine feeds are finite and nonzero:

| Measurement | Left observed range | Right observed range |
| --- | --- | --- |
| RPM (%) | 84.953..100.029 | 84.953..100.029 |
| Temperature (C) | 510.010..860.270 | 514.524..862.270 |
| Fuel flow (kg/s) | 0.3994..1.2631 | 0.3994..1.2631 |

The analyzer now uses stable observed Export identity, correct aircraft type,
timely readings and a matching time-interpolated trajectory for the bounded
single-player diagnostic. It retains both sets of names/IDs without assuming
numeric equality. Its screening requires near-full trajectory overlap and at
most 1 m residual; this is not a general multiplayer/object-identity solution or
an agreed product tolerance. The live recheck passes. Wrong aircraft type,
100 m trajectory mismatch, stale readings and missing samples still fail, as
does the first capture with no engine data. Missing unit-name text alone does
not discard otherwise verified diagnostic observations.

Only analysis code changed for this result; the installed observation hook is
already correct. Next repeat the marked throttle phases in the same mission
without reinstalling or restarting DCS. Independent left/right engine transitions
and effects/nozzle correlation remain to be measured together. No playback engine
actuator, afterburner-state semantics or sound fidelity is claimed yet.
