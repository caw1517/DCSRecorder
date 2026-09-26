# Native motion matching

Prepared 2026-09-25, DCS 2.9.29.27278. Live test pending.

Live update: [two-run result](../../experiments/efm-ownership/results/motion-matching-2026-09-25/README.md).
User reports improvement with residual jitter. Matched-interval attitude
correction averaged 0.08566 degrees; native rates were still changed
between commands. Roughly 14 cm position corrections align strongly with
the inherited mission wind. The setter's storage layout is verified, but
interpreting its input as authoritative ground velocity was incomplete:
native integration appears to add wind. A zero-wind control is the next
discriminator. Neither run reached controller release.

The [zero-wind control](dcs-zero-wind-control.md) reduced mean position
correction by 87.16%, with a user-reported massive visual improvement.
The user accepted zero-wind missions as the working constraint; wind
compensation is deferred. Angular correction remained essentially unchanged.

The update-gate test successfully stopped native motion, but the user
reported worse visible jitter. Holding the pose between callbacks forced
approximately 2.1 m position corrections every 20 ms. This test removes
update suppression and supplies motion consistent with the desired path.

The user's [FSDeveloper reference](https://www.fsdeveloper.com/forum/threads/smooth-ai-movement-the-old-favorite.17374/)
describes a velocity-driven slew approach. That motivates preserving motion
between updates; this DCS experiment is not an implementation of FSX slew,
nor proof of FS Recorder's internal technique.

## Native contract

WorldGeneral exports MovingObject::VectorVelocity(const osg::Vec3f&), RVA
0x69310. Disassembly shows that it computes the vector magnitude into
receiver+0x250 and stores XYZ at receiver+0x254. The getter at 0x69390
returns receiver+0x254. For this callback subobject, these correspond to
complete woAIPlane+0x258 (scalar) and +0x25c (vector). The setter is called
with the same verified MovingObject handle used by ForcePosition.

Local angular rates at complete+0x1e8 were established in the roll test.
The three integration loads at 0x712408/0x712411/0x712435 confirm the layout.
Native convention is dF=wz*U-wy*R and dU=wx*R-wz*F.

Native integration has additional branches and may recompute these values.
In particular, exposing a velocity setter does not prove it is authoritative
for this aircraft's entire motion path or for rendering. Immediate readback
and the next callback are logged separately to test that distinction.

## Intervention

Same formation mission, speed, trajectory and pose-command cadence.

- 5–15 s: original pose commands only.
- 15–30 s: after each pose command, set world velocity and all three local
  angular rates from numerical derivatives of the commanded path.
- 30–43 s: pose commands only again.
- After 43 s: cease control.

The update gate is never used. The previous roll-zero intervention is
replaced by angular rates matching the commanded attitude. This tests
coherent motion state as a whole; it does not isolate linear versus angular
contributions, which may need a subsequent comparison.

The derivative uses a 1 ms central interval, shortened at either endpoint
so velocity does not collapse to zero at release. Axis convention tests
independently cover heading, pitch and roll. Full-path checks verify
velocity and angular-rate predictions one 20 ms step ahead across several
starting headings, including the separate-axis attitude excursion.

Existing identity, ID, build, altitude, finite-pose and displacement guards
remain. Additional guards check the velocity export RVA, entry/getter
signatures, three angular-field load signatures, readable finite existing
state, desired speed 70–210 m/s and desired angular components within
1 rad/s. Writes require exact float-vector readback. Failure stops control.

## Feedback

CSV adds motion_matched; velocity before/after/command; angular command.
The analyzer compares pre-command position and attitude errors during the
three phases, attributing each interval to the previous command. It also
measures how much native rates and velocity changed after our last write.
Multiple mission runs in one process are analyzed separately.

Predictions: smaller corrections support motion-state mismatch; large
renewed rate/velocity changes support native control overwriting our state;
smaller corrections without visual improvement motivate a rendering or
interpolation investigation. Exact root cause and visible fix remain open.

Run EFM-Probe-climbing-turn-formation.miz for 55 s, watch close formation
especially at 15 s and 30 s. Offline build and both CTests pass, including
the added motion prediction checks. These do not validate live smoothness,
aerodynamic fidelity, wake behavior or collisions.

Installed DLL SHA-256:
6722E4E3C82243DC9852DCDAB5278F7B5FF7E85EFFC40A730C8D911A47F90591.
The prior update-gate DLL was preserved with its result artifacts. A
synthetic analysis check also passed for phase attribution and mission reset.
