# Recorded native core RPM test — live result pending

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
afterburner sound or full engine-state fidelity. No live verdict exists yet.
