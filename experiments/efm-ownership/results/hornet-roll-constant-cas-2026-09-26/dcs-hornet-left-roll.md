# Hornet positive-g left-roll prototype

Prepared 2026-09-26, DCS 2.9.29.27278. Live validation pending. The user
authorized stage 3 after the single-turn and right-level-left experiments.
Open `EFM-Probe-Hornet-left-roll-400KIAS.miz` and run 65 seconds.

## Requested maneuver and selected interpretation

The user requested nominal 400 KIAS, gradually building to 1.8 g, starting a
left roll at 14 degrees nose-up, maintaining the pull through the roll with
pitch peaking near 30 degrees, then gradually easing roll and pull to a
wings-up, level recovery. This is a geometric interpretation of that request,
not an independently verified Blue Angels maneuver or flight model.

The model uses zero angle of attack/sideslip, aligning the aircraft nose
with its path tangent. It treats 1.8 g as normal specific force along the
aircraft's up axis, with gravity accounted for. Engine thrust, drag, energy
limits, real Hornet trim/AoA and engine sounds are not simulated by this
controller. Axial acceleration supplies the prescribed airspeed schedule.

For flight-path angle gamma, heading psi, bank phi, speed V and normal
load n, the solver integrates:

```
gamma_dot = g/V * (n*cos(phi) - cos(gamma))
psi_dot   = g*n*sin(phi)/(V*cos(gamma))
x_dot     = V*cos(gamma)*cos(psi)
h_dot     = V*sin(gamma)
z_dot     = V*cos(gamma)*sin(psi)
```

The flight-path equation is the zero-sideslip, zero-AoA simplification of
equation 13 in [NASA, Stall Recovery Guidance Algorithms Based on
Constrained Control Approaches](https://ntrs.nasa.gov/api/citations/20160000934/downloads/20160000934.pdf).
Its use here is our geometric modeling choice, not a validation of this
maneuver by that source.

V follows 400 KCAS in ISA, using the compressible pitot relation already
documented in the Hornet prototype. IAS remains approximate. The reference
path starts at 2000 m and is translated to the actual captured position;
captured altitude differences introduce a small CAS offset. The previous
flight captured near 1981 m. Mission atmosphere-derived CAS telemetry and
the player's HUD remain the live checks. Speed rises from about 224.5 to
241.4 m/s as the path climbs, within the existing 260 m/s native guard.

## Profile and timing

| Mission seconds | Segment |
| --- | --- |
| 0–5 | Native flight |
| 5–7 | Settle onto the controlled path |
| 7–11 | Smooth ramp from 1 g to 1.8 g |
| 11–15.93 | Continue pull to 14 degrees nose-up |
| 15.93–35.04 | Left roll, holding 1.8 g normal load |
| 35.04–41.04 | Final 60 degrees of roll, easing normal load to 1 g |
| 41.04–47.04 | Wings/nose level, straight flight |
| After 47.04 | Motion release; observe through 65 seconds |

The left roll lasts 25.111 seconds. Its bank angle passes 0, -60, -300 and
-360 degrees through monotone cubic Hermite segments. Entry takes 9.708 s,
the middle portion 9.403 s and recovery 6 s. Roll rate is continuous,
starts at zero and eases back to zero. The early/middle durations were
solved for a 30-degree peak and zero final pitch. The final six-second load
taper implements the requested easing off the pull during recovery.

This solution ends approximately 1595 m higher and 11.58 degrees left of
its initial heading. Pitch briefly reaches -2.59 degrees before returning
to level. Neither original altitude nor original heading was a requested
endpoint constraint. These outcomes were disclosed while preparing the test.

## Implementation and verification

`experiments/efm-ownership/solve_roll.py` performs the offline RK4 solve and
generates `hornet_roll_data.h`; its report is under `package/hornet-roll/`.
The SDK source is not needed for the solver. The generated reference data
is baked at 50 Hz. `hornet_roll_path.h` interpolates position with endpoint
velocities and reconstructs orthonormal attitude from pitch/heading/bank;
the existing native controller supplies matching motion every callback.
Initial capture remains continuous. The roll build uses
`HORNET_ROLL_PROTOTYPE`; the existing two-turn path and its tests remain.

Five CTests passed. The new roll test independently differentiates position
to check normal and lateral specific force, unwraps bank through a full
left revolution, and checks pitch targets, reference CAS, tangent alignment,
segment continuity, motion prediction, orthonormal poses and native
speed/altitude/step guards at three world headings. Maximum measured normal
load error was 0.0000843 g; maximum body-axis angular component was 0.567
rad/s. These are numerical path checks, not live aerodynamic measurements.
Module dependency, datalink, route, clean-loadout, player-light trigger and
Lua syntax packaging checks passed.

Mission: `EFM-Probe-Hornet-left-roll-400KIAS.miz`.
DLL SHA-256: `16F6C7CC931D875BF9A1D0917AACF38B8B4025ECF2BCE5B3722C995BF724472F`.
Mission SHA-256: `3B501F969EEFDB45C03B3EDB07B68EB3102A034838D7D8ECC0BCA4D5CA7F8B80`.

Preserved prior two-turn artifacts are in
`experiments/efm-ownership/results/hornet-right-level-left-2026-09-26/`.
Profiles are compiled into the DLL: replaying a previous mission alone
does not restore its old maneuver. Use the archived matching DLL and mission.

For live validation, inspect roll direction, entry pacing, inverted motion,
peak pitch, and smooth recovery. Keep the clean exterior, lights-off and
stowed speed-brake checks. Record feedback and preserve motion/mission logs
before declaring success. This does not implement recording, layered playback,
engine-state reproduction or sound synchronization.
