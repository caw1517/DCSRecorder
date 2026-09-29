# Wheel and suspension checkpoint — 28 September 2026

Status: separate captured wheel/suspension/steering playback accepted visually
and numerically after post-animation correction. Normal wheel recording/playback
integration remains pending. Normal canopy integration
is accepted in its own evidence record.

The [prototype](../../wheel-prototype/README.md) samples deployment, compression
and rotation for all three gear assemblies, alongside position and velocity.
Installed Hornet FM definitions are checked during packaging. The parked hot
start reuses the live-verified canopy diagnostic location.

Checks passed installed aircraft dependency/route validation and six packaged
capture cases: normal, overspeed, airborne, lost aircraft, invalid arguments and
timeout. Duplicate starts and paused frames do not add samples. The analyzer
fixture contains 2,000 ordered samples with maximum 20 ms spacing; those synthetic
values do not establish live ranges or a rotation period.

Installed new mission:
`C:/Users/w_can/Saved Games/DCS/Missions/DCSRecorder-Wheel-Diagnostic.miz`.
SHA-256: `dd83429621fb38692a2507d10430c0096333ff300eea00887579c853cd38983f`.
All 527 protected script/module/recording hashes were unchanged. Installation
added no DLL or hook and required no DCS restart. Package, installation report,
raw assets and later captures remain local and ignored.

The user is asked for two slow taxi/brake-to-stop cycles, with initial/final
stationary holds and optional external observation. Next: preserve the log and
compare raw rotation changes with motion and compression responses. No wrap
period, unloaded compression endpoint or ground-physics playback was claimed at
that initial checkpoint.

## First live capture

The user completed the capture and also made turns, asking whether NWS can be
captured. Saved `capture.log` SHA-256:
`8e5439ce9c1045715526a0c7287eaff1fb4c4b5e967fe04ca60c210d728ae856`.
It has 1,259 ordered samples over 25.185 seconds, maximum 20 ms spacing and a
normal user stop. Speed spans approximately 0–4.3285 m/s; 346 samples are below
0.05 m/s and 866 above 0.5 m/s. A braking marker occurs at mission time 25.160.
All three deployment values remain 1.

| Raw channel | Observed range |
| --- | --- |
| Nose compression 1 | 0.709879–0.892081 |
| Left compression 6 | 0.817256–0.848840 |
| Right compression 4 | 0.817056–0.845824 |
| Nose rotation 101 | 0.000749–1 |
| Left rotation 103 | 0.000347–1 |
| Right rotation 102 | 0.000052–1 |

Rotation wraps are observed. A period-one hypothesis produces 37.7958, 30.0581
and 28.8950 signed turns (nose/left/right), with maximum unwrapped sample steps
0.06142/0.04922/0.04863. Using installed wheel radii, the nose distance is 63.941 m
versus a 63.804 m aircraft-center path. This supports the period-one hypothesis
for the measured low-speed run. Left/right paths differ; steering geometry and
slip are not resolved by this comparison. No higher-speed aliasing, reverse
rotation, unloaded compression endpoint or replay rendering is established.
Playback must preserve measurements rather than synthesize rotation from speed.

## Steering follow-up

The first capture omitted steering, so its turns cannot supply a recorded NWS
angle. A separate protocol-two capture adds unverified argument 2 and rudders
17/18, retaining all nine original channels. The new mission is
`DCSRecorder-Wheel-Steering-Diagnostic.miz`; SHA-256:
`38ebcdc892040a4491429da52d988b93902c3fa0faecc1eb001f1fa1ab115475`.
Installed mappings/routes, six packaged capture cases and the 2,000-sample
analyzer fixture passed. Rechecking the original mission/capture also passes.
All 527 protected script/module/recording hashes remain unchanged; no restart
is required. Both diagnostic missions remain available.

The user has instructions for centered/left/centered/right/centered slow taxi,
with optional visible-state markers and F2 observation. Steering mapping and
recorded wheel/suspension/steering playback remain pending.

## Captured steering and prepared playback

The user completed the steering mission. Saved `steering-capture.log` SHA-256:
`103c3659a30a76ac37a452b8836e3f4a0f65ae392ade7ae42a94e5689418f15f`.
Protocol two contains 2,462 ordered samples over 49.244 seconds, maximum 20 ms
spacing, normal user stop, and speed approximately 0–4.2475 m/s. There are 508
stopped and 1,904 rolling samples by the analyzer's thresholds. All three gear
deployment values stay at 1; all compression and rotation channels change.

The user placed left/centered/right markers at mission times
18.722/30.618/34.746. Argument 2 is near zero at those individual instants:
markers precede the changing steering segments, so they are not exact transition
timestamps. Within the following left interval it reaches +0.726780, remains
approximately zero throughout the centered interval, and reaches -0.735133 in
the following right interval. It ends within 0.000001 of zero. Rudders 17/18 have
distinct traces, including opposed nonzero stationary values. These measurements
support argument 2 as the steering candidate; separate visual confirmation and
replay retention/rendering remain pending. No degree conversion is inferred.

Period-one short-arc analysis finds 194 total wheel wraps and maximum sample
steps 0.07133/0.05507/0.04748 (nose/left/right). Estimated circumferential travel
is 130.902/125.688/121.753 m versus a 126.110 m aircraft-center path. Turning and
slip are not resolved here. This experiment is restricted to the measured slow
taxi; reverse and high-speed phase aliasing remain unverified.

`prepare_playback.py` packages ten captured channels: deployment 0/5/3,
compression 1/6/4, rotation 101/103/102 and steering 2. Rudders are diagnostic
comparators only. Every raw sample is preserved; signed steering/compression
interpolate linearly, while rotation interpolates across the short period-one
arc. Stationary phase-one holds and exact endpoints remain unchanged. The first
offline run caught phase-one holds normalizing to zero between samples; the
corrected build passes all 2,462 real samples, every midpoint, 194 wrap crossings,
final holds and SDK identity/cookie/bounds/lifecycle/clock checks. Mission checks
cover F10 start/release, telemetry, completion/removal, failure, timeout and stop.
Installed dependency, route and configuration checks also pass.

Installed a new `DCSRecorder-Hornet-Wheels` module with `HornetWheelProbe.dll`
and `DCSRecorder-Wheel-Playback.miz` while DCS was already closed. Ten installed
file hashes passed verification; all 1,817 protected existing file hashes stayed
unchanged. Mission SHA-256:
`a755344a281f3e80024592bea18fb832e8722b00882c22bf78d9e378abc187da`.
Local package: `package/wheel-playback-checked`; the earlier failed package is
preserved separately and was not installed. Source capture hash is unchanged.

The new test uses SDK appearance writes on an ordinary airborne route, with
49.22 seconds of captured animations and an eight-second final hold. It contains
no native timing hook, trajectory controller or cockpit control commands. The
airborne setting exposes the lowered wheels for observation; it does not validate
taxi-path playback, ground contact or suspension physics. Native traces plus
independent mission reads will distinguish immediate writes from retained values.
The user has playback instructions. Normal recording/schema integration waits
for the separate animation result.

## SDK-only playback diagnosis — 29 September

User report: NWS seemed to work, but little strut/main-gear movement or tire spin
was visible. Saved local evidence is under `playback-2026-09-29/`. Two attempts
share process 18072 and reuse object ID 16777472; analysis separates them at
mission BEGIN and SDK call-counter reset, rather than mixing their clocks.
The saved first attempt reaches the tape endpoint but ends before the final
eight-second hold/removal; the second saved snapshot is partial. Neither has
the normal mission completion marker. These traces diagnose appearance, not
lifecycle acceptance.

`check_retention.py run1.csv run1.log retention1.json --allow-incomplete
--assert-wheels` reports **2,697 SDK calls / 2,692 later reads** and fails on
0/5/3/101/103/102/2. The same command on the second attempt reports
**1,045 SDK calls / 1,040 later reads** and the same failing channel set.
`--allow-incomplete` explicitly records `complete: false`; strict completion
validation remains the default.

- All ten channels have zero immediate readback error.
- Every later rotation read is zero, while requested wheel phases vary. This is
  a real lost-rotation signal, not merely the equivalent phase-one/zero endpoint.
- Gear deployment changes from requested 1 to approximately 0.994979978.
- Steering differs by up to 0.015060068; the user's visual impression is recorded
  without claiming exact numerical retention.
- Compression 1/6/4 matches every later first-run read within 0.0000000005.
  Source main-strut excursions are only about 4–5% of normalized channel range;
  numerical retention does not prove that the subtle movement was visible.

Ranked explanations: a later native animation writer explains lost rotation and
altered steering/gear; a model/channel mismatch remains a rendering alternative;
small captured motion explains subtle suspension but cannot explain wheels
being reset to zero. The comparison changes only write timing. It does not
amplify suspension or generate wheel motion from velocity.

Prepared `DCSRecorder-Hornet-Wheels-Animation` / `HornetWheelAnimationProbe.dll`
and `DCSRecorder-Wheel-Animation-Playback.miz` in `package/wheel-animation-ready`.
It reuses the previously checked build-specific per-object animation hook and
reapplies the same ten values after the native animation update. The tape bytes
are identical to the SDK-only package. Existing SDK-only and accepted normal
modules stay intact.

The focused regression uses the actual repair callback and animation dispatcher
with the overwrite pattern observed in the live trace. Running
`wheel_animation_check.exe --without-repair` fails with “later animation erased
a requested wheel state”; the corrected default passes repeated updates,
inactive-pending guard and hook restoration. The built timing DLL rejects a
non-DCS object before appearance/native writes. The unchanged SDK variant still
passes all 2,462 samples, midpoints, 194 wraps and endpoint/lifecycle guards.
The new mission passes installed dependency/route/configuration and F10 checks.
Live after-update retention/rendering is still pending; the saved original
repro remains red, as expected until a new DCS run supplies corrected evidence.

After the user closed DCS, installed the separate timing module/mission: ten
installed hashes verified, all 1,865 protected existing hashes unchanged.
Mission SHA-256:
`70b580cf545fc579162b37cc3565e135145913d20d630f0b661c6e5d9bf1a5aa`.
Both variants share tape SHA-256:
`902a4d99238c40e86ee80ec589160d6e2aa4fafd4e0d7dee086130b0c913953b`.
The user has instructions to inspect the wheels/NWS and wait for lead removal.

## Post-animation playback accepted — 29 September

The user reports everything looked visually correct, including suspension
movement during braking and turning. There is no dedicated suspension phase:
this test reproduces the real strut movement in the saved taxi, without an
artificial extension/compression sequence. Wheel rotation and NWS are accepted
within that same isolated appearance test.

Saved evidence: `playback-animation-accepted-2026-09-29/`, process 45112,
object 16777472. Strict `check_retention.py ... --assert-wheels` passes:
2,862 SDK calls and 2,858 independent later mission reads, with no mismatched
channel among all ten. The mission completed normally after 49.22 seconds of
capture plus the eight-second endpoint hold; playback object destruction is
logged. All 28,620 post-animation channel readbacks have zero error.

The post-animation trace directly confirms the cause: DCS changes each gear
deployment and wheel-rotation channel on all 2,862 updates, and steering on 634
updates; the callback repairs them before the independent mission reads.
Compression is already retained and needs no correction in this run. The
original SDK-only saved repro remains a failing comparison; the same retention
check passes against this new live run.

Cleanup reports `animation_hook_already_replaced`: the destructor had changed
the object's table, so guarded cleanup releases ownership without overwriting
that replacement. It does not claim a literal `animation_hook_restored` event.
All ten installed package hashes still match, and the original steering capture
SHA-256 remains unchanged.

This accepts recorded low-speed wheel, steering and suspension **appearance**
on the isolated test lead. Normal app/schema integration is next. High-speed
rotation sampling, reverse motion, unloaded/airborne strut capture, real ground
placement/contact and takeoff/landing remain distinct validation work. The
fidelity issue remains open for integration and the other remaining groups.
