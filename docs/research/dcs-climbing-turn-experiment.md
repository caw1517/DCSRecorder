# Climbing-turn pose-control proof of concept

Prepared 2026-09-25 after a successful single +20 m position change. This test commands pose through the previously exercised native ForcePosition entry; it does not drive aerodynamic control inputs or write velocity.

## Sequence

Use EFM-Probe-climbing-turn.miz, one occupied stock TF-51D plus the unoccupied probe. Run unpaused for 55 seconds.

- Before 5 s: observe normal motion and estimate horizontal speed from consecutive position samples.
- 5–7 s: capture the current pose, continue forward, and smoothly settle the starting pitch/roll to level.
- 7–37 s: smooth 90-degree heading change with a 100 m climb. Horizontal speed is fixed from the measured initial speed, bounded to 80–200 m/s. Heading and altitude use quintic easing; pitch follows the path tangent and bank follows the nominal turn rate. This is a geometrically constructed path, not a physical flight-model calculation.
- 37–43 s: hold the new heading/altitude while applying small, separate-frequency pitch and roll excursions, bounded by 5 and 10 degrees. This deliberately tests attitude separately from the path tangent.
- After 43 s: cease all commands and observe AI recovery for at least 10 seconds.

The trajectory is evaluated against elapsed simulation time, not callback count. A precomputed 20 ms horizontal integration table is interpolated; orientation and altitude are evaluated analytically. The first command preserves the measured starting pose. A failed native guard or command displacement above 10 m aborts further control for that object. The experiment never retries after failure or release. Existing runtime-ID, class, vtable, signature, altitude, finite-state and pose-consistency guards remain.

## Measurement

native-motion-PID.csv records command and immediate actual float pose as 16 padded matrix values each, on every commanded callback, plus capture/release/abort status. Matrix rows are forward, up, right, translation. The independently logged TURN_OBSERVER rows contain mission time, XYZ, all three orientation vectors and reported world velocity for both aircraft. OWNERSHIP_OBSERVER and runtime-ID mapping remain for continuity with prior experiments.

Compare commanded XYZ and orientation with independent telemetry while allowing measured callback timing offset. Report full orientation error from the basis, heading change, height gain, and release behavior. Compare reported velocity with the commanded position derivative: pose tracking can succeed while velocity is inconsistent. Do not interpret visual success alone as all-axis control or physical fidelity.

## Verification and limits

Both CTests pass: existing callback/EFM contracts and new climbing-turn geometry checks. Geometry checks span several starting headings and verify initial continuity, 90-degree endpoint heading, 100 m climb, bounded position steps, tangent alignment during the climbing turn, orthonormal orientation throughout, and level release. These are offline checks, not live tracking results.

Installed DLL SHA-256: E75F68C03E50B675993C2F1F9A4E4FD09978B1C344AB00040823DBE7EAEBEC18. The DLL applies this sequence to the eligible probe, so historical missions using that same probe will also invoke the new controller; use the separately named mission for its expanded telemetry. No simulator result is claimed yet.

## Formation speed revision

After the user reported being unable to catch the lead at maximum throttle, the controller was rebuilt with a 105 m/s horizontal target (about 204 knots groundspeed). It eases from measured initial speed during the two-second settling phase. The formation mission starts both aircraft and their routes at 105 m/s, with the same 100 m aft / 60 m left player position. This supersedes the measured-speed target and DLL hash above. Both contract and geometry tests pass, including a numerical path-speed check. Turn duration, 100 m climb and release timing remain unchanged. The slower live run is pending.
