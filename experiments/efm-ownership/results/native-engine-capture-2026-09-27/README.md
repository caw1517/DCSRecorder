# Native player engine capture — first live check pending

Follow-up to [Complete single-aircraft visual and engine-state fidelity](https://github.com/caw1517/DCSRecorder/issues/6).
Recorded core RPM reached DCS's sound renderer but produced only a slight change;
fan and power inputs still described the playback aircraft's own simulation.
This experiment establishes a capture path for the actual stock player Hornet.

## Access path and scope

The installed CockpitBase.dll exports `cockpit::c_LA()` returning `IwoLA*`.
Its implementation at RVA 0x3f2a30 obtains the current cockpit's human-aircraft
interface and calls its IwoLA accessor. Sound.dll's exported
`Sound::JetEngineSounder::init` accepts the same IwoLA interface; its update
routine calls core/fan RPM at slot 0xd8, and scalar engine values at 0xe0/0xf0.
This supplies an existing player-aircraft access path rather than a guessed
conversion from the test module's owned-aircraft handle.

`native_capture.cpp` exposes a tiny Lua helper that, per sample:

- Verifies the pinned cockpit accessor bytes and native sound callsite bytes.
- Resolves the current IwoLA pointer, checks MSVC RTTI, the interface's exact
  subobject offset, and that getter addresses are executable DCS.exe code.
- Reads engine 1/2 core RPM, fan RPM, thrust-slot 0xe0 and power-slot 0xf0 values.
- Rejects native exceptions, nonfinite values and a changed current aircraft.
- Returns the observed concrete class, interface offset, thread ID and getter
  RVAs with the values. It retains no aircraft pointer between calls.

The helper performs no aircraft writes, virtual-table replacement, sound-source
control, input commands or physical-engine adjustment. Private getter calls are
still build-specific and live behavior is unverified. Native scalar names are
provisional: 0xf0 forwards to 0xe0 on the earlier AI aircraft, which does not
prove its semantics on the player aircraft. Neither is labeled an AB boolean;
units, ranges and afterburner correlation must be measured.

`native_capture_hook.lua` runs alongside the existing engine diagnostic hook.
It is dormant until a matching stock-Hornet mission capture begins. Each mission
sample causes one native sample, alongside Export RPM, player ID, position and
start/end model timestamps. Player/type, sequence, clock or helper failures are
explicit and stop native capture. Existing Export RPM/temperature/fuel-flow and
mission appearance logs remain available for independent comparison.

New log prefix: `DCSENGINE_NATIVE,1`. DATA fields after that prefix are:
`DATA,take,sequence,start_time,end_time,export_id,x,y,z,export_rpm_left,export_rpm_right,`
followed by either `UNAVAILABLE,reason,...` or
`OK,concrete_class,interface_offset,thread_id,core1,fan1,thrust_e0_1,power_f0_1,`
`core2,fan2,thrust_e0_2,power_f0_2,rpm_getter_rva,thrust_getter_rva,power_getter_rva`.
BEGIN/END and explicit ERROR lines delimit each take. No missing value becomes zero.

## Checks and installation

- Release x64 DLL builds.
- CTest `native_engine_capture_lua` loads the actual DLL through installed
  `luae.exe`/`package.loadlib`, verifies its unavailable result outside DCS, then
  exercises hook value delivery, lazy loading, stopping and load/native/type/
  identity/clock failure paths with bounded fixtures. It does not validate live
  getters against the real player object.
- All 29 cockpit accessor bytes and four sound callsite guards match the
  installed binaries. The installer pins DCS 2.9.29.27468.
- Installed with DCS closed: two new files; **324 existing hashes unchanged**.
  Installation details remain in local `installation.json`.

New files under Saved Games/DCS:
`Scripts/DCSRecorderEngineCapture/NativeEngineCapture.dll` and
`Scripts/Hooks/dcs-recorder-native-engine-capture.lua`.
No Export.lua, existing hook, mission or aircraft module was replaced.

## First live check

1. Start DCS and open **DCSRecorder-Engine-State-Diagnostic.miz**.
2. F10 > **Engine state diagnostic** > **Start capture (4 minute maximum)**.
3. Keep power steady for about five seconds, then select **Stop capture**.
4. Report completion; preserve the session so its logs can be collected.

Before asking for another throttle sequence, require successful native rows,
consistent player/class/getter identity, plausible finite channel values and
agreement between Export RPM and native core RPM at their associated sample
times. If access is rejected, inspect the observed identity/error rather than
asking for a full sweep. A later successful sweep must include independent left
and right afterburner phases to establish per-engine separation. Native capture
does not establish playback mapping or audible afterburner fidelity.
