# DCS playback and physical interaction

Research date: 2026-09-23. [Investigation ticket #3](https://github.com/caw1517/DCSRecorder/issues/3). Status: source investigation only; no current-build simulator experiment. Mods and a local headless backend are eligible, but the product remains exclusively solo. A visual ghost alone does not meet the requirement.

## What the primary sources establish

Eagle Dynamics describes its external flight model (EFM) interface as retaining DCS rigid-body physics and contact modeling, with non-contact forces and moments supplied by the EFM developer. This makes a force-driven custom aircraft a plausible physics-preserving candidate; it does not establish independent non-player EFM instances, arbitrary pose control, or accurate trajectory following. [ED flight-model definitions](https://www.digitalcombatsimulator.com/it/support/faq/general/)

ED's Ka-50 documentation describes ground/object contact points, landing-gear dynamics, and damage affecting physical properties. This is evidence for that aircraft's modeled interaction, not a blanket guarantee for every aircraft or playback representation. [ED Black Shark 2 description](https://www.digitalcombatsimulator.com/en/products/helicopters/black_shark_2/?SHOWALL_1=1)

ED developer Yo-Yo explains that wake response depends on how a flight model samples local air velocity and applies it to airframe elements. Third-party flight models do not automatically obtain equally realistic wake response merely by using EFM. The post addresses **receiving** wake; it does not certify that a custom replay object **generates** the correct wake. [ED developer explanation, September 2019](https://forum.dcs.world/topic/207466-wake-turbulence/page/4/)

The author of Basic EFM Template supplies source and a DLL example with forces, controls, gear, and basic damage. Its installation uses `make_flyable`; it does not demonstrate many autonomous EFM playback aircraft. The author identifies the installed `DCSWorld/API` directory as the original ED template location. [Template author's repository](https://github.com/IGServal/DCS-Basic-EFM-Template)

ED announced an AI flight-model upgrade as work in progress in December 2021. That announcement must not be treated as proof that every current AI aircraft uses the same physics. [ED GFM announcement](https://www.digitalcombatsimulator.com/en/news/newsletters/a134f231fe8269e1c78dd6d0dd8c3c9d/)

## Eligibility matrix

The verdicts below are engineering assessments from the cited evidence, not runtime results.

| Candidate | Collision and ground contact | Wake generation / reception | Precise recorded motion | Eligibility |
| --- | --- | --- | --- | --- |
| Normal aircraft driven through controls | Native aircraft mechanisms retained in principle; verify selected aircraft and controller mode | Verify both directions on selected type | Requires a controller; new disturbances can cause trajectory error | Eligible experiment, no fidelity guarantee |
| Custom EFM driven by forces/moments | ED documents shared rigid-body/contact foundation; implementation and assets still matter | Reception depends on aerodynamic implementation; generation unproven here | Closed-loop force tracking plausible; disturbance response competes with exact tracking | Eligible research candidate; non-player instancing is a gate |
| Repeatedly imposing position/orientation on an aircraft | Contact or damage events might occur, but overrides could erase physical response; untested | Neither direction established for this method | Could follow desired pose if an applicable interface exists; no such interface established here | Conditional; cannot pass on appearance alone |
| Moving scripted visual object or ghost | No supporting evidence of aircraft-grade contact behavior | Neither direction established | Rendering a path would not establish physical participation | Ineligible unless interaction is separately demonstrated |
| Local headless/server backend with synthetic input | Hosting choice alone supplies no missing aircraft capability | Same unresolved aircraft/method questions | Same control and synchronization questions | Possible transport/hosting option, not a physics solution by itself |

## Exactness versus interaction

Engineering inference: a prescribed position at time T and a physically caused displacement away from that position cannot both determine the same aircraft state at that instant. A system can preserve physical participation while choosing how strongly to correct back to the recording, or it can stop playback after a collision. Those policies have materially different behavior.

For a useful experiment, keep these questions separate:

1. Does the playback aircraft collide with and damage the player's aircraft?
2. Does the playback aircraft itself respond or sustain damage, and does replay stop or override it?
3. Does playback generate a wake that measurably affects the player?
4. Does playback respond to another aircraft's wake, or intentionally stay on its recorded path?
5. During taxi, takeoff, touchdown, and landing rollout, are contact forces and gear behavior active and stable?

## Runtime evidence needed to resolve the ticket

- Select one aircraft and one candidate backend; record DCS build, mission options, aircraft/mod versions, and wake settings.
- Compare a native control run with playback under the same conditions.
- Measure position/angular/time error through a generated roll and loop before and after a deliberate disturbance.
- Test near-miss versus deliberate contact; capture damage/events and resulting motion for both aircraft.
- Cross a playback-generated wake and compare player angular rates with a no-source baseline; separately test disturbance reception by playback.
- Test ground contact and a repeatable touchdown, looking for penetration, bouncing, unstable correction, and damage suppression.
- Verify two playback aircraft plus the independently controlled player before declaring layered feasibility.

The source review narrows the candidates but does **not** resolve ticket #3. Current installation/API inspection and simulator measurements remain necessary.
