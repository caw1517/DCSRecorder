# Wheel and suspension checkpoint — 28 September 2026

Status: first live taxi capture saved and analyzed; steering follow-up checked
and installed. Recorded-wheel playback remains pending. Normal canopy integration
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
