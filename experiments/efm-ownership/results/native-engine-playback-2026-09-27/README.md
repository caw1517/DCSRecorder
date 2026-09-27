# Measured native engine playback — installed, live result pending

Continues [Complete single-aircraft visual and engine-state fidelity](https://github.com/caw1517/DCSRecorder/issues/6)
after native core RPM alone reached the sound renderer but sounded weak and did
not reproduce afterburner. The full player capture supplies the missing fan and
power inputs; this test keeps DCS's stock aircraft sound renderer.

## Input and actuator

The latest complete native take has 2,039 samples over 101.905 seconds. The source
is immutable at `../native-engine-capture-2026-09-27/full-live/dcs.log`. Select its
latest mission BEGIN occurrence; mission restart reused take ID 1.

`parameter_tape.py` writes `DCS_NATIVE_ENGINE_PROBE_V1`: count, then rows of
relative native sample time, core1, fan1, thrust1, core2, fan2, thrust2. Values
are measured getter returns, unscaled. Fan values reach 1.065868 and power reaches
2.341144; both survive above 1.0. The prototype accepts finite RPM/fan in 0–1.2
and power in 0–4; these are bounded test limits, not universal engine limits.

Both native player power getters, slots E0 and F0, returned equal values on every
captured sample. The playback aircraft's pinned F0 implementation at DCS RVA
0x60f110 tail-forwards to E0. `parameter_hook.h` therefore replaces only the RPM
slot D8 and power slot E0 in one aircraft's owned table copy; F0 stays unchanged.
Preparation rejects a capture where E0/F0 differ. Runtime checks verify the F0
forwarder, original slot pointers, native thrust getter, aircraft identity, table
extent, engine count and sound callsites before installing the override.

Each getter calls its original function first, then returns the recorded value
only for engine indices 1/2 during the replay window. Other aircraft, other table
slots and engine indices remain untouched. Logs record caller module/RVA,
engine, channel (0 core, 1 fan, 2 power), override status, original and returned
values. Calls through both Sound.dll power consumers can be distinguished by
caller address. `drain_time` remains the SDK drain clock, not exact call time.

The module forwards original parameters for three seconds, interpolates the full
captured sequence, restores the original table for three seconds and removes the
lead. Manual stop/destruction restores the table too. The mission stops on a
guard error, missing handshake or timeout. A third-party table is not overwritten.

This changes outward-facing engine parameters, not internal engine physics.
The lead follows an ordinary AI route. Captured motion and accepted nozzle/flame
actuation are not integrated in this sound test. There are no custom sounders,
SDEF files, waves, synthetic throttle plateaus or phase-derived power values.
Labels reflect the original markers; transitions remain exactly as captured.
Power normalization and the exact native afterburner gate are still unproven.

## Checks and package

- Release DLL build passed.
- `native_parameter_boundary` passed: all six channels, distinct engines,
  fan/power above 1.0, unchanged F0 forwarding, original-value observations,
  concurrent reads, invalid input rejection and restoration/scope.
- `native_parameter_mission` passed completion, manual stop, guard failure,
  handshake and stalled-clock timeouts. The shared original RPM mission check
  also passed after adding the parameter variant.
- The actual packaged DLL passed the existing `rpm_module_check` fake SDK test:
  it loaded the measured tape and rejected a non-DCS object before native or
  appearance writes. This does not test real DCS identity/getters.
- `check_parameter_package.py` verified every sample/time/channel against the
  source, captured E0/F0 equality, retention above 1.0, stock descriptor, hashes
  and the five controller instruction guards against retained/current binaries.
- Existing mission loader, routes and aircraft configuration checks passed.

Local package: `package/native-engine-test`. New module:
**DCSRecorder-Hornet-Native-Engine**, DLL **HornetNativeEngineProbe.dll**, mission
**DCSRecorder-Native-Engine-Playback.miz**. Installation is additive and requires
DCS closed; prior tests, recordings and the native capture helper are protected.
After the user closed DCS, installation passed: 10 installed hashes verified and
88 protected files unchanged. The local package's `installation.json` retains
the exact installed and protected hashes. The live result is pending.

## Live procedure after installation

Load **DCSRecorder-Native-Engine-Playback.miz**, then F10 > **Native engine
playback** > **Start recorded engine test**. F2 to the lead. Listen for power
response and afterburner changes through the recorded transitions, then let the
lead disappear after about 108 seconds. Retain the session for log collection.

Require native consumption of core, fan and both forwarded power requests before
interpreting the listening result. Parameter delivery, audible strength/AB,
visible appearance and integrated flight playback remain distinct checks. This
test is installed, not a demonstrated sound fix.
