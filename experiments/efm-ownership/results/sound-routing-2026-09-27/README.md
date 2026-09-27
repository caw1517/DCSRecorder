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

## Live boundary result and TRACE-filter correction

The next run completed at model time 4.298–19.298; local evidence is in
`boundary-live-run/`. All 15 boundary samples passed the live identity and layout
guards. Every sample reports:

- Selected name: `Aircraft/Planes/DCSRecorderSounderTest`.
- Lua instance reference present, wrapper bound to this aircraft.
- Native sounder: `Sound::PlaneSounder_V2` in Sound.dll.
- No AIFM member; two `EagleFM::AustereFM::Propulsion::AustereEngine_TurboFan`
  objects in FMBase.dll.

This rules out an absent descriptor name or missing Lua instance in this run.
It does not yet establish script updates or source playback. The user reported
completion, without a new audible verdict on this diagnostic run.

The aggregate RPM field was zero, but it is **not** either per-engine getter.
Captured getter instructions show core RPM is a ratio of float fields at +0x7c
and +0x48; fan RPM is a ratio at +0x80 and +0x50. The diagnostic deliberately left
those nontrivial getters uninterpreted, so it captured neither actual ratio.
Do not label both engines stopped from the aggregate value or infer their thrust.

Further read-only inspection found a SOUNDER logging bridge in the retained
WorldGeneral snapshot (RVA 0x37180) forwarding a Lua string at level 0x100.
Loading the **installed** edCore.dll's `ED_luaopen_log` into installed luae.exe
reveals `ALL=255`, `TRACE=256`: the previous hook's ALL filter excluded TRACE.
The earlier logging probe was therefore incomplete, despite successfully loading.

`check_sounder_logging.lua <edCore.dll> <sounder_logging_hook.lua>` loads those
native constants, captures the hook's output configuration and checks INFO/TRACE
coverage. Before the correction it failed with
`SOUNDER: TRACE excluded by output mask 255`; after the correction it passes.
The hook now uses mask 511 and emits `[DCSRECORDER-TRACE-CHECK]` at TRACE into
each dedicated output. This test checks the filter contract, not live audio or
the native bridge's execution. An attempted standalone native logging session
did not create output files; it is not counted as end-to-end logging validation.

With DCS closed, the installer replaced only the temporary logging hook after
verifying its old hash against its prior installation report and saving a backup.
All 50 protected hashes are unchanged; the diagnostic DLL, sound script and test
mission remain identical to the boundary run. The installer now accepts
`--previous-report <prior-installation.json>` for this explicitly verified update.

Next live step: run **DCSRecorder-Sound-Routing-Test.miz**, F10 > Sound routing
test > Start sound test, F2 to the lead, and allow removal after 15 seconds.
Collect the dedicated logs. Require the TRACE startup marker before interpreting
missing script messages. Inspect script load/source/phase/error messages to
distinguish an update/parameter failure from an audio-source/rendering failure.
No sound correction is claimed and no new throttle capture is needed.

## TRACE-visible live result

The following run completed at model time 4.494–19.494. Logs and native traces
are preserved locally in `trace-visible-run/`, with a machine-checked summary.
The dedicated SOUNDER output now records actual script execution:

- `[DCS-SOUNDER-PROBE] loaded` and host creation for `MAIN_16777472`.
- Source handles 492 (engine) and 493 (afterburner).
- Engine at elapsed 0, afterburner at 3, engine at 6, afterburner at 9, silence
  at 12 seconds. All five timestamps match their intended boundaries.
- No invalid-host-parameter, backward-clock, or unavailable-source diagnostic.

This confirms script loading and phase dispatch in the live run. Source handles
and play requests still do not establish audible rendering. The user reported
completion and subsequently confirmed **still idle throughout**. This is now a
confirmed live discrepancy between successful script phase dispatch and the
audible result. No installed files were changed during collection.

The hook's startup self-check marker is absent from the retained dedicated log;
its open time is later than the hook's success message. The reason for losing
that marker is not established. Actual script TRACE messages provide direct
positive evidence that the corrected filter works during this mission. Do not
treat a missing startup marker alone as failure when later TRACE messages exist.

With sound still idle, investigate sample definitions/attenuation,
listener routing, and actual source playback state. Installed
`Doc/Sounds/example.sdef` documents silent/peak/inner/outer radii and direction
cones; the stock sample definitions themselves are inside the installed sound
archive and were not inspected. The installed sound list confirms the referenced
wave names, which is not the same as confirming their rendered output.

## Separate audibility comparison installed

`DCSRecorder-Sound-Audibility-Test.miz` and its separately registered
`DCSRecorder-Hornet-Audibility-Test` module use a unique `HornetEngineAudibilityProbe`
DLL and `DCSRecorderAudibilityTest` sounder. This preserves the previous sound
test for comparison. The same spatial-host update and phase-only playback calls
are retained. Four three-second source phases are followed by three seconds with
all test sources stopped; the lead is removed at 15 seconds:

1. Stock engine source from the earlier test.
2. An original, generated control tone: two gently faded 660 Hz beeps per second,
   mono 48 kHz/16-bit, peak 0.15 before the same 0.4 runtime gain.
3. Stock afterburner definition from the earlier test.
4. The documented stock afterburner **wave name**, referenced by a new, uniquely
   named definition with explicit gain, no directional attenuation or silent
   radius, 100 m inner radius and 4 km outer radius. No stock audio was copied.

The mission labels each phase on screen. The script logs `isSourcePlaying` for
each source once per model second, host position, and the supplied per-engine
core/fan RPM, thrust and flame parameters. Backend playing state alone will still
not establish audibility. These are DCS's sound-input parameters, not a new
recording or engine-state actuator.

Predictions, in priority order:

- Stock source definition/attenuation problem: the tone and explicitly defined
  afterburner are audible while the stock afterburner is not.
- Stock wave unavailable/unsuitable: the generated tone is audible but both
  afterburner variants fail. This still needs source/error evidence to distinguish
  availability from a quiet sample.
- General spatial routing or source-lifecycle problem: the tone is also inaudible.
  Playing-state and host-position logs then guide the next distinction.

Validation: the separately built DLL rejects the fake DCS object before native
writes; the actual retained sounder loader dispatches all four sources and
terminal stops in the offline harness; mission single-start, manual-stop and
completion checks pass. Generated tone format and amplitude bounds were checked.
The package passed installed DCS mission dependency, route-timing and aircraft
configuration checks. These do not establish live audibility.

Installed with DCS closed: 14 manifest hashes verified, 60 protected hashes
unchanged. Generated package and installation report are local under
`package/sound-audibility-ready/`. Use F10 > **Sound audibility test** > **Start
sound test**, then F2 to the lead. Report whether the control beeps and either
afterburner phase were audible. No general playback sound fix is claimed yet.
