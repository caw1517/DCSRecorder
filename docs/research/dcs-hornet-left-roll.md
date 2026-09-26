# Hornet equal-altitude left-roll prototype

Updated 2026-09-26, DCS 2.9.29.27278. The user confirmed the first roll
worked visually but corrected two requirements: 400 knots is an initial
speed, and the whole maneuver must return to its pre-pull altitude. They
explicitly selected the altitude before the pull-up rather than the
altitude at 14 degrees nose-up. The revised flight is awaiting live validation.

Open `EFM-Probe-Hornet-left-roll-400KIAS.miz` and run 75 seconds.
Clean exterior, lights off, speed brake stowed and calm weather remain.

## Revised behavior

- Initial nominal 400 KIAS, represented by 400 KCAS in ISA at 2000 m.
- Smooth four-second pull ramp from 1 g to 1.8 g; begin the left roll at
  14 degrees nose-up, reaching a peak near 30 degrees.
- Remain loaded through the roll. Ease from 1.8 to 1 g during the last
  six seconds while roll rate eases to zero.
- Recover wings/nose level at the pre-pull altitude and original heading,
  offset left. Speed remains a continuous integrated state throughout.

The reference solution climbs about 1204 m, descends with a minimum pitch
of -32.71 degrees, and returns to its initial altitude within 0.001 m in
the numerical test. Forward displacement is about 8.35 km and left offset
1.48 km. Initial CAS is 400 knots; minimum is about 257.7 and recovery CAS
about 376.6 knots. These are provisional model outputs, not measurements
or calibrated predictions of the actual Hornet. There is no endpoint height
snap, forced speed recovery, or hidden energy injection to close the path.

| Mission seconds | Segment |
| --- | --- |
| 0–5 | Native flight |
| 5–7 | Settle onto controlled path |
| 7–11 | Smooth pull from 1 to 1.8 g |
| 11–15.78 | Continue to 14 degrees nose-up |
| 15.78–48.72 | Loaded left roll and descending recovery |
| 48.72–54.72 | Ease roll and pull to wings/nose level |
| 54.72–60.72 | Straight, level flight under the same thrust/drag model |
| After 60.72 | Release motion control; observe through 75 seconds |

## Fixed-throttle approximation and limits

The playback object's native engine/flight model is still not providing
this maneuver. Holding throttle does not mean literally constant thrust
on a real turbofan. For this prototype we approximate it with constant
modeled thrust, set once to balance the initial level-flight drag, and
integrate speed from gravity and a parabolic drag polar:

```
q         = 0.5*rho*V*V
CL        = n*m*g/(q*S)
D         = q*S*(CD0 + k*CL*CL)
T         = D at initial 400 KCAS, 2000 m, n=1  (constant thereafter)
V_dot     = (T-D)/m - g*sin(gamma)
gamma_dot = g/V * (n*cos(phi) - cos(gamma))
psi_dot   = g*n*sin(phi)/(V*cos(gamma))
```

The [NASA drag equation](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/drag-equation/)
and [induced-drag relation](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/induced-drag-coefficient/)
support the model form, not the numerical calibration. Mass estimate is
11382 kg descriptor empty mass plus 3500 kg mission fuel; reference area
37 m2 and span 11.43 m come from installed Hornet descriptors. Fuel burn
and exact clean-pylon mass corrections are omitted. CD0=0.0172 and span
efficiency 0.8 are explicit provisional assumptions. Thrust is about 18.70 kN.
The speed behavior must eventually be validated against recorded Hornet
flight, not treated as licensed player-FM behavior or official Blue Angels
procedure. RPM, throttle display, afterburner and audio remain independent
future work; this change does not command the native engine.

The model aligns the nose to the path tangent (zero AoA/sideslip). Normal
load is specific force along the aircraft up axis, not total acceleration
magnitude. The flight-path equation is the zero-AoA/sideslip simplification
of equation 13 in [NASA's flight-path dynamics reference](https://ntrs.nasa.gov/api/citations/20160000934/downloads/20160000934.pdf).
CAS is only an approximate stand-in for instrument IAS. The reference path
is translated to the captured position; capture-height offsets introduce
a small atmosphere mismatch. The player's HUD and `HORNET_AIR` telemetry
remain live checks.

## Solver and checks

`solve_roll.py` solves four variables: entry, middle and exit durations,
and the bank angle at the exit segment boundary. It targets 30-degree peak
pitch, zero final pitch, initial altitude and initial heading. Bank follows
monotone cubic Hermite segments with continuous roll rate; no reversal or
extra revolution is introduced. The solved roll takes about 38.93 seconds.

The generated `hornet_roll_data.h` now includes speed as an independent
state and covers six seconds beyond roll completion. `hornet_roll_path.h`
uses that speed for endpoint velocity interpolation instead of calculating
a constant-CAS speed from height. It retains pose continuity and matching
native velocity/angular-rate commands.

All five CTests passed. The roll test independently differentiates positions
and checks normal/lateral force plus constant-thrust axial force balance,
initial speed, substantial speed bleed and recovery with remaining drag loss,
altitude/heading closure, left displacement, full monotone left rotation,
14/30-degree pitch targets, motion prediction and native guards. Numerical
max normal-load error is 0.0000513 g; axial-force acceleration error is
0.000102 m/s2. Minimum speed is 154.2 m/s and maximum body-axis rate 0.427
rad/s. The native 70–260 m/s, 1000–5000 m and 10 m step guards are unchanged.
Packaging checks for dependencies, datalinks, route timing, clean loadouts,
light initialization and Lua syntax also pass. Live visual validation remains.

Prior constant-CAS roll artifacts and source are preserved in
`experiments/efm-ownership/results/hornet-roll-constant-cas-2026-09-26/`.
Previous turn tests also retain their archived matching DLL/mission pairs.
The path is compiled into the DLL, so an old mission alone cannot restore
its old profile.

DLL SHA-256: `04643E4F205A4A13ABDAB82117688FCA221FAEE25EAB98C0CBE1487879DA9B76`.
Mission SHA-256: `BE9E8D7095A60A70F35A580FDCFFAA9FAB84BC8ABB21C63B634DF26EC4F94082`.

## Subsequent video feedback

The user supplied `Roll.mp4`: overall roll worked, with a small perceived
pitch movement near inversion/descending recovery and an unexpected
engine/afterburner appearance. See the
[video evidence review](../../experiments/efm-ownership/results/roll-video-review-2026-09-26/README.md).
The specific pitch cause remains unconfirmed; small between-command
corrections were measured. Engine state/effects/audio synchronization is
recorded as deferred work. No speculative motion or engine fix was installed.
