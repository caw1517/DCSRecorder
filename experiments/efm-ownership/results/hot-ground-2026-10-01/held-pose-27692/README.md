# Live ground hold after pre-step pose restoration

The user reached INSPECTION_COMPLETE and explicitly reported: "Stationary and
unchanged." Readiness succeeded. This capture covers 63.42 model seconds; the
mission continued running and the scene witness moved about 8.87 km.

The real post-step position check passes over 3,168 samples from model time
0.10 s, with no measured precise-position error. Mission samples from 0.12 to
63.42 s likewise match recorded XYZ exactly, velocity is zero, and all 33
supported appearance channels match within the log's numeric precision.
Both engine 1 and 2 native read overrides retain their recorded initial values.
The unoverridden reads are Sound.dll requests for engine index 0, outside the
two validated engine indices; they return zero.

All 3,171 waiting contact samples report grounded, life 20/20, surface 5. Once
settled, origin height above terrain is 1.8329908674 m, as recorded. Replay time
remains zero. No countdown or taxi release is included in this evidence.

Limits retained explicitly: initial 0.00-0.10 s native startup substeps precede
regular SDK updates, with up to 0.022016304 m height difference and a temporary
basis-component difference of 0.011078810. The steady mission-visible basis
differs from source by at most 0.00005931021 per component; exact orientation
retention is not claimed. Full-run extrema and raw evidence remain available.
The user reported no visible movement or state change. This successful sustained
hold allows the next countdown/taxi diagnostic; overall issue acceptance remains
open pending release, review, and assessment of these residual startup limits.
