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

The repeat also sounded idle. The hook reported success at 20:33:43 UTC;
mission BEGIN/END are 7.244/22.244 (the complete 15 seconds). SOUNDER and SOUND
outputs contain only open/close markers; ED_SOUND adds only its peak-calculation
startup message. There are still no script diagnostics. These logs and the
native actuator traces are preserved locally in `scoped-logging-run/`.
This rules out the hook failing to load, but still does not prove script
non-execution. Repeating this logging setup alone is not a useful next test.

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

## Installed read-only aircraft boundary diagnostic

The isolated sound-test DLL now writes `bin/state-logs/sound-boundary-*.jsonl`
once per model second. It observes the aircraft descriptor's sounder name,
whether its Lua sounder reference exists, whether its wrapper points back to the
aircraft, the native sounder's RTTI identity, the FM-member presence, engine count,
aggregate RPM field, and each engine's core/fan getter identity. Only complete
trivial float getters are interpreted as direct field reads; complex getters
remain uninterpreted. No private function is invoked, and no engine field is
written. Pointer addresses are omitted from the trace.

The primary vtable (or this DLL's owned animation clone), secondary RTTI and
twelve instruction signatures must match before reading the candidate layout.
All reads use ReadProcessMemory on the current process. This adds observation
to the existing appearance test; its four animation writes remain as before.

Validation: the new DLL builds; `sound_read_boundary` passes its bounded-string,
getter-decoder and invalid-handle checks; `check_sound_layout.py` matches all
twelve guards against the retained analysis images. The engine playback fixture
with `--expect-native-rejection` confirms the actual new DLL writes an
`identity_rejected` observation and rejects the fake object before appearance
writes. An initial invocation of the general motion `probe_check` was inapplicable:
that fixture requires lights/speed-brake behavior this isolated module does not
implement. The appropriate engine fixture above passed. None of these offline
checks demonstrates live sound or current-run script execution.

With DCS closed, `install_sound_boundary.py` replaced only
`HornetEngineSounderProbe.dll`, after checking its previous installation hash and
backing it up under local `boundary-installation/`. All 57 protected hashes are
unchanged, including the mission, Lua sound script, captured tape, recording hooks,
recordings, and accepted playback modules. The extra logging hook remains
temporary and should be removed when the investigation ends.

Next live step: launch **DCSRecorder-Sound-Routing-Test.miz**, F10 > Sound routing
test > Start sound test, F2 to the lead, and allow its removal after 15 seconds.
No sound correction is claimed. An empty/different descriptor name identifies a
registration/selection problem; a matching name with no Lua reference identifies
an initialization gap; a reference establishes an instance, but does not prove
onUpdate dispatch or audible rendering. The native identity and engine reads
also provide evidence for the separate internal-engine route. Inspect that
trace before deciding the next intervention.
