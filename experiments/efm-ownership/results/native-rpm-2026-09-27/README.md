# Recorded native core RPM test — consumed, partial audible response

Question: does substituting the recorded core RPM in the native aircraft getter
reach DCS's normal sound renderer, and does audible engine pitch follow it?
This continues [Complete single-aircraft visual and engine-state fidelity](https://github.com/caw1517/DCSRecorder/issues/6).
The user wants recorded parameters with DCS-derived sound. The earlier sample
and beep diagnostics did not establish audible playback and are set aside.

## Evidence and scope

Retained analysis of the pinned DCS 2.9.29.27468 build identifies a primary
woAIPlane virtual getter at slot 0xd8, implemented by DCS RVA 0x66d160. It takes
an engine index and a core/fan selector. The installed Sound.dll at RVA 0x13d430
prepares a core-RPM request for each engine and calls that slot. The ordinary
EFM callback previously observed zero calls; this is a different boundary.
These observations motivate the test; live caller traces remain required.

The latest complete capture supplies 979 left/right RPM samples over 48.899 s,
with each engine ranging from 69.2935% to 99.9716%. Extraction retains the Export
sample timestamps and divides percentage by 100. This is a candidate native
core-RPM mapping, not an established full engine-state conversion. The recording
has overlapping military/afterburner RPM, so RPM alone does not identify AB.

The isolated module copies the original aircraft descriptor with only its type
renamed. It contains no custom sounder, SDEF or wave assets. The experiment
changes only engine 1/2 core-RPM getter returns. It calls the original getter
first and records both values. Fan RPM, thrust, AB state, physical engine state,
captured nozzle/flame appearance and recorded trajectory are not restored.
The lead follows an ordinary AI route. This is not integrated flight playback.

An owned per-aircraft virtual table retains all other slots and its RTTI locator.
Identity, table extent, engine count and instruction checks fail closed on an
unknown build. The original table is restored at the end or on stop/destruction;
a table already replaced by another owner is not overwritten. A failed restore
does not count as successful completion. This remains private, build-specific
prototype access, not a portable engine API.

## Offline checks and installation

- `native_rpm_boundary`: original values, distinct engine returns, core-only
  substitution, unchanged fan/other indices/other aircraft, sound-thread reads,
  invalid value rejection, call observations and table restoration passed.
- `native_rpm_mission`: completion, manual stop, native guard failure, missing
  handshake, stalled clock timeout and one-shot activation passed.
- `rpm_module_check`: the actual packaged DLL loaded the real tape and rejected
  a non-DCS object before native/appearance writes, then stopped writing.
- `check_rpm_package.py`: every RPM value and timestamp matches the source;
  original descriptor preserved; no custom sounds; all package hashes and the
  installed Sound.dll call-site guard passed.
- All 12 existing read guards matched the retained DCS/WorldGeneral snapshots.
  Runtime guards must still pass in the live process.
- Release build and the existing mission loader/route/configuration checks passed.

Local package: `package/native-rpm-ready`. Installed with DCS closed:
**10 file hashes verified; 72 protected file hashes unchanged**. Existing
recordings, hooks and prior diagnostic/accepted modules remain available.
Generated assets, logs and proprietary analysis images are not committed.

## Live procedure and decision

1. Start DCS and load **DCSRecorder-Native-RPM-Playback.miz**.
2. F10 > **Native RPM playback** > **Start recorded RPM test**; F2 to the lead.
3. Listen for pitch changes across the labeled idle/military portions. There
   are 3 seconds original RPM, the captured sequence, then 3 seconds restored.
4. Let the lead disappear after about 55 seconds and report the audible result.
   Preserve the DCS session logs for collection.

Logs are in Saved Games/DCS/Mods/aircraft/DCSRecorder-Hornet-Native-RPM/bin/rpm-logs.
`events-*.csv` records phase transitions and restoration; `calls-*.csv` records
caller module/RVA, engine, selector, original/returned values and override status.
`drain_time` is when the SDK drains buffered calls, not their exact call time.
The mission emits `DCS_RPM_MISSION` BEGIN/END lines into dcs.log.

If Sound.dll consumes the recorded values but sound still stays idle-like, that
rejects core RPM alone as a sufficient explanation; investigate other native
inputs next. If no Sound.dll calls reach the getter, the audio consumer path
remains unresolved. A pitch change supports this RPM path, but does not validate
afterburner sound or full engine-state fidelity.

## Live result

The user reports: sounds changed a little, no afterburner, and the result was
less aggressive than the actual aircraft at those power settings. **Core RPM
alone is insufficient for the required sound fidelity.** This is partial audible
response, not acceptance of engine sound or afterburner playback.

Saved this run's `dcs.log`, `calls-46668-338942953.csv` and
`events-46668-338942953.csv` under the ignored `live-run/` directory. Mission
completion is recorded at 59.276 s after activation at 4.326 s. The hook restored
at 56.226 s, before destruction at 59.266 s; no overflow/rejection event appears.

`analyze_rpm_live.py <calls.csv> <events.csv> <recorded-rpm.txt> <summary.json>`
passes on the retained run. It found 63,228 getter observations, including 33,735
from Sound.dll. All **24,450 overridden Sound.dll core-RPM calls** matched the
recorded interpolation to within **5.78e-8** normalized RPM, using the observed
20 ms publication-to-drain delay. The test checks that delay against the logged
SDK steps; drain timestamps remain distinct from precise call timestamps.

| Sound consumer return address | Input | Live observation |
| --- | --- | --- |
| Sound.dll + 0x134c65 | Engine 1/2 core RPM | 2,445 replay calls per engine; 0.692940–0.999716 returned |
| Sound.dll + 0x134c92 | Engine 1/2 fan RPM | 2,595 calls per engine; original 0–0.379916 forwarded |
| Sound.dll + 0x13dcc3 | Engine 1/2 core RPM | 9,780 replay calls per engine; recorded values returned |
| Sound.dll + 0x130d3f | Engine index 0 | Original zero forwarded; not evidence that engines 1/2 stopped |

The exported `Sound::JetEngineSounder::update` starts at Sound.dll RVA 0x134be0.
Its disassembly independently places the observed core and fan calls in that
routine. It also reads aircraft slots 0xf0 and 0xe0, as well as another parameter
at 0xf8. In this AI aircraft's retained vtable, 0xf0 forwards to 0xe0; it is not
evidence of a separate afterburner boolean. The routine uses the fan result in
several subsequent pitch/gain calculations, falling back to core RPM in some
places only when fan RPM equals zero. It also uses the thrust-related result in
gain calculations. Raw disassembly remains local.

This confirms the recording reached actual native sound consumers. It rules out
missing RPM delivery as the explanation for this run's weak response. The fan
and power inputs still describe the independently simulated playback aircraft;
they do not describe the original recorded power setting. They are the next
inputs to investigate, without claiming either is the sole cause. Exact
afterburner gating and the real aircraft's fan/thrust mapping remain unverified.

Next: establish a capture path for the real aircraft's native fan and power/AB
inputs, then replay measured values through validated getters. The original
capture contains RPM, temperature, fuel flow and appearance, but no established
fan-RPM/thrust channels. Do not invent those values from RPM or treat a visible
flame argument as a calibrated thrust value. No replacement module or mission
was installed while collecting and analyzing this result.
