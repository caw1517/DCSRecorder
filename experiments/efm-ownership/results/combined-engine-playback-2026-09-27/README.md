# Combined engine sound and appearance — installed, live result pending

Continues [Complete single-aircraft visual and engine-state fidelity](https://github.com/caw1517/DCSRecorder/issues/6).
The user accepted the measured native core/fan/power sound test. Earlier, the
four-channel nozzle/flame appearance test was accepted separately. This test
combines those paths before adding recorded motion or the application workflow.

## Same source and clock

Source: the immutable local
`../native-engine-capture-2026-09-27/full-live/dcs.log`, latest mission BEGIN
occurrence. It supplies 2,039 native samples spanning 101.905 seconds.
`combined_tape.py` preserves the six measured native channels, including values
above one and the verified equality between the captured E0/F0 power getters.

The new `DCS_ENGINE_COMBINED_V1` tape contains relative time, core1/fan1/power1,
core2/fan2/power2, then draw arguments 28/29/89/90. Visual samples are interpolated
at the native samples' absolute model times before sharing the native origin of
8.029 seconds. They are not independently rebased or associated by sequence
number. The final appearance value is held for the last 10 ms because native
capture extends 10 ms past the last mission sample. Preparation rejects gaps over
150 ms or endpoint holds over 50 ms. These are bounded experiment checks.

At runtime all ten channels interpolate on one SDK clock: three seconds of
original state, the captured sequence, then three seconds with original getters
and animation before lead removal. The stock sound renderer derives the audio;
there are no custom sound samples or audio scripts.

## Shared ownership and appearance timing

The combined target uses the parameter controller with `ENGINE_COMBINED`.
One per-aircraft table copy replaces the D8 RPM, E0 power and C10 animation slots.
The original F0 power forwarder is unchanged. The combined boundary restores all
three slots together on completion, manual stop or destruction. Original native
animation always runs first; the callback then reapplies the recorded four draw
arguments on the owning thread. Other objects and unrelated slots stay original.

The proven animation prologue/callsite/writer guards and null-FM identity checks
join the native sound/build guards. Missing animation callbacks or rejected
appearance writes stop the test. Nozzle/flame writes run only during the recorded
interval. No recorded pose, velocity or internal physical engine state is written;
the lead follows an ordinary route.

Native calls/events and SDK/post-animation appearance values are logged under
the new module's `bin/parameter-logs`. `analyze_combined_live.py <calls> <events>
<tape> <appearance> <summary.json>` checks both delivery paths, shared timestamps
and restoration. It does not establish perceptual synchronization or visible
rendering; those require the user to watch and listen.

## Checks

- Release DLL and combined boundary fixture built successfully.
- Five CTests passed: combined boundary/mission, existing parameter
  boundary/mission and the earlier RPM mission.
- The combined boundary exercises native animation calling the power getter,
  repeated post-animation repair, argument forwarding, inactive baseline,
  independent aircraft, foreign-thread exclusion and completion/manual restore.
- The packaged DLL loaded its tape and rejected a non-DCS object before native or
  appearance writes through the SDK ABI fixture.
- `check_parameter_package.py` independently compared all six engine channels
  and all four aligned appearance channels to the capture; it verified stock
  descriptors, package hashes, above-one values and eight instruction guards.
- Installed DCS mission dependency, route timing and aircraft configuration
  validators passed.

## Package and live procedure

Local package: `package/combined-engine-test`. Module:
**DCSRecorder-Hornet-Engine-Combined**, DLL **HornetEngineCombinedProbe.dll**,
mission **DCSRecorder-Engine-Combined-Playback.miz**.
After the user closed DCS, installation verified all 10 installed hashes and
99 protected files unchanged, including the accepted native-engine and appearance
tests, capture helper and existing recordings. Exact hashes are retained in the
local package's `installation.json`.

Load the mission, use **F10 > Combined engine playback > Start combined engine
test**, then F2 to the lead. Watch both nozzles/flames and listen through the
recorded changes. Let the lead disappear after approximately 108 seconds.
Combined rendering/audio and subsequent recorded-motion integration remain open.
