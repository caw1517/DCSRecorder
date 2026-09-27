# Combined engine sound and appearance — live appearance and sound accepted

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
The first combined rendering/audio result is accepted below; recorded-motion
integration and normal completion of the combined controller remain open.

## First live result

The user reported: “That seemed to have worked great, both visually and audibly.”
This accepts combined engine sound, nozzle movement and flame appearance for the
observed test on the pinned Hornet/DCS build.

The source session and native/appearance traces are copied into local `live/`.
Delivery checks pass through 101.820 seconds of the 101.905-second tape:

- 132,366 Sound.dll overrides consumed all six engine channels and both power
  callsites. Across all callers, 225,094 overrides matched the tape within
  1.20e-7, subject to the final-drain timing qualification below.
- 40,736 appearance records cover SDK and post-animation writes. Every stage and
  channel has 5,092 observations, matching the shared clock and interpolated tape
  within 5.81e-8. No missing-channel or delivery-gap check failed.
- Native baseline values forwarded unchanged; no trace-overflow, guard-failure
  or appearance-write-failure event appeared.

The session stopped at model time 109.794, 85 ms before the recorded interval's
end and before its three-second original-state tail. DCS logged `Dispatcher Stop`
and application shutdown; the mission did not log `END,complete`. The destroy
callback reported `parameter_hook_already_replaced`: DCS had already replaced
the object's table, so the controller left it untouched. This demonstrates that
teardown path, **not** normal in-place restoration or automatic lead removal.
Normal completion remains to be observed in a later combined/integrated run.

The strict analyzer correctly rejects this as a completed run. Explicit
`--allow-teardown` validates observed delivery and marks normal completion
unverified. Destruction drains remaining getter calls at the last SDK timestamp:
113 final override rows have ambiguous timing between the last two published
samples. They match one of those two values within the stated tolerance; they do
not establish an exact per-call timestamp. Earlier drains retain the verified
20 ms publication-to-drain relationship. The previous complete sound-only run
still passes the strict analyzer after this reporting extension.

Decision: carry forward the combined measured-parameter sound and captured
nozzle/flame path. Next integrate these channels with recorded motion and the
normal recorder/library workflow, preserving the current take and accepted test.
The broader fidelity ticket stays open for those integration checks.
