# Spatial sound test failed audibly; diagnostic visibility corrected

THROWAWAY for [Complete single-aircraft visual and engine-state fidelity](https://github.com/caw1517/DCSRecorder/issues/6).

User verdict: idle sound throughout the 15-second test. Local `live.log` shows
the test module loaded, its Sounds directory registered and one sounder discovered.
Mission BEGIN is at 3.244 and END,complete at 18.244. Native actuator creation,
animation-hook installation and destruction are also recorded. Unlike the prior
two runs, this mission completed its intended duration and removal.

No `[DCS-SOUNDER-PROBE]` entries or `sounder.log` appeared. This is **not proof
that the Lua script never ran**. The original file logger made an invalid
assumption about the sounder environment.

## Reproduce with the actual loader

The retained read-only WorldGeneral runtime snapshot contains the embedded
Lua 5.1 `sounderImpl` chunk at RVA 0x1e13e0. A local copy was extracted from
`experiments/native-interface-inspection/snapshots/worldgeneral-static-34908`.
This is an earlier retained snapshot, not a fresh snapshot of the latest run;
its findings still need live corroboration. No installed binary was modified,
no analysis image was executed and no proprietary loader bytes are committed.

Run with the installed luae.exe:

```text
check_sounder_runtime.lua <local-sounderImpl.luac> <sounder_probe.lua>
```

The committed harness executes that real loader and its create/bind/set/process/
destroy functions with captured audio API calls. Result: both source paths are
created; four play calls alternate correctly and the terminal phase stops both.
The environment confirms `io == nil` and `log == nil`; it exposes a `print`
binding. Consequently our optional `io.open` block cannot create sounder.log.
Missing file output was an instrumentation limitation. The older standalone
script harness also passes, but had supplied a different environment and could
not expose this gap.

This checks loader compatibility and API dispatch, not actual source availability,
audio rendering, listener geometry, or which sounder the live aircraft selected.
Live idle-only audio remains the failure signal.

## Scoped live logging

Installed only `Scripts/Hooks/dcs-recorder-sounder-logging.lua` with DCS closed.
The hook requests ALL levels for SOUNDER, SOUND and ED_SOUND into separate
`dcs-recorder-sounder`, `dcs-recorder-sound`, and `dcs-recorder-ed-sound` outputs.
It does not replace normal dcs.log settings. The syntax follows the installed
`D:/DCS World/Config/ModelViewer/autoexec.lua` example. Its success/failure marker
uses `DCSRECORDER_SOUND_TRACE` in the normal log. Live visibility of the sounder's
print binding still requires verification; if it remains absent, don't infer
non-execution from that alone.

All 50 protected hashes are unchanged, including the sound test mission/script,
DLLs, existing hooks and recordings. Installation report is retained locally.
The source installer refuses different existing hook contents and a running DCS.
After diagnosis, remove only this named temporary hook with DCS closed; the
extra outputs are session logging, not permanent changes to DCS audio settings.

Repeat the **same DCSRecorder-Sound-Routing-Test.miz** after launching DCS:
F10 > Sound routing test > Start sound test, F2 to the lead, allow removal at
15 seconds. No audible correction was made. Collect the dedicated logs and
dcs.log before another launch. The goal is to expose script errors/source lookup
or confirm that a different renderer supplies the observed idle audio.

## Built-in engine audio path

Current installed Sound.dll exports native Hornet and F404 sound classes as well
as a generic jet-engine sounder. Read-only disassembly of JetEngineSounder::update
shows aircraft-interface calls at vtable slots 0xd8, 0xe0 and 0xf0 before its
mixing calculations. The retained DCS snapshot's woAIPlane vtable connects slot
0xd8 to a per-engine getter that uses either its AIFM member or its separate engine
array at +0x2fa0. Thus a separate internal engine-state path exists alongside the
motion and draw-argument controls. This is consistent with the user's earlier
afterburner observation, but it does not establish that run's actual engine state
or prove which renderer is active now. No native engine getter was invoked and
no private engine-state offset was written. Any later live inspection needs
current-build identity/signature validation before using these candidate layouts.
