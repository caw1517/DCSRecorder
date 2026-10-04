# Countdown release — airborne control accepted

Work on [Release player and playback on one countdown clock](https://github.com/caw1517/DCSRecorder/issues/22).
The airborne task is complete. Normal release, visible smoke, countdown pause,
playback pause, duplicate requests and loaded-readiness refusal have live
evidence below. The predecessor's accepted held snapshot remains the input.
Implementation and evidence remain local workspace changes, not a published
source checkpoint. Ground staging belongs to the next task.

The preparation and failure sections below retain the chronology; their pending
status statements describe those earlier checkpoints, not the current result.

The separate `HornetReleaseProbe` controller and its Lua bridge implement a
one-shot release latch, native callback-owned replay epoch, restored initial
recorded velocity and one clock for supported state channels. The user hook
dispatches player release immediately after native commit in the same callback.
Native and mission telemetry retain the actual ordering for live evaluation.

All 11 selected offline checks pass: the five new release checks plus existing
held, snapshot and updated-build callback checks. The generated mission passes
nested Lua compilation, complete initial-channel/smoke-schema validation,
installed-aircraft dependency, route and configuration checks. The installer
validates all 14 payload files. These results do not establish rendered behavior
or simulator callback ordering.

## Prepared source and package

- Accepted gear-down take: `20261001T033031Z-0001.csv`, 436 samples, 8.70 seconds.
- Native tape SHA-256:
  `c33122b8c4029d6da65bc20d505608d3cc431c3289374e08ef3a01733447621b`.
- Initial smoke ON, gear down, nonzero lights; supported channels and original
  pose/velocity are source-derived. The user permits invisible smoke while held;
  visible emission on release remains required.
- Module: `DCSRecorder-Hornet-Release-Test`.
- Mission: `043-Hornet-Countdown-Release.miz`.
- Current package: `gear-package-v5/`, with manifest and payload; its installed
  update receipt is `reference-update-v5/receipt.json`. Earlier packages remain
  available as pre-fix reproducers.
- The earlier `gear-package/` is superseded and must not be installed: generated
  nested-script review caught a smoke-event list serialization error. The builder
  now validates nested scripts and the generated smoke schema before packaging.

The proposed release clock uses simulator time, not wall time. Actual pause,
duplicate-request and readiness-refusal checks remain live acceptance gates,
alongside first movement, smoke emission and sound. The issue and its parent
checklist remain open.

See [control design and checks](../../release-start/README.md).

## Installation verified

With DCS closed, the additive installer installed all 14 payload files and
verified 1,129 pre-existing runtime/user files unchanged. The receipt is retained
in `gear-package-v2/installation.json`. The new mission, native module and
`DCSRecorderReleaseControl` user hook are ready for the first normal release run.
The accepted snapshot and normal companion installation were preserved.

## First live attempt: readiness timeout

The user reported a failed message. Retained PID 16376 logs show
`FAILED,bridge_or_native_readiness_timeout` after 10.02 model seconds, followed
by `HOLD_CLEANED`. No countdown or release request occurred. The native controller
continued successful zero-motion/initial-state holds through the timeout, with
502 object callbacks in the second loaded run. The hook logged startup, but no
bridge readiness acknowledgment. This establishes a pre-countdown integration
failure, not a released-flight or smoke result.

Raw logs are retained under `readiness-failure-16376/raw/`. The existing offline
fixtures do not reproduce the missing live readiness acknowledgment. Their mocked
native replies and loaded mission state are insufficient to identify the cause;
passing them is not treated as a fix. The original hook omitted the exact native
reply, model/native clock comparison and loaded-field difference from its log.

A hook-only diagnostic update now reports those boundary results on readiness
state changes with `[DEBUG-release-readiness]`, and records mission arm
acknowledgment. It does not relax readiness or change the native controller,
mission, tape, countdown or release policy. The hook lifecycle fixture still
passes. Next live step: load the same mission, click Fly and wait for Ready or
the failure message; no playback request is needed to diagnose this gate.

## Exact cause reproduced and preparation corrected

The targeted PID 24804 run reported:

```text
state=loaded_mismatch:coalition[blue][country][1][plane][group][1][units][1][AddPropAircraft][VoiceCallsignLabel]:unexpected
model=0.000000000 native=READY,1,0,0
```

The native controller was ready and its clock matched. DCS's mission loader
adds missing Hornet property and Link16 defaults, while the prepared reference
compared the original incomplete table. Strict comparison then withheld arming
until the ten-second timeout. This was a preparation defect. No flight release
or rendered-smoke result was obtained. Logs are retained under
`readiness-failure-24804/raw/`.

`check_loaded_defaults.lua` reproduces the exact unexpected voice-callsign
failure through the real hook and comparison function using installed Hornet
default resolvers and `me_paramFM.setupOnLoad`. The pre-fix package fails with
the same field path as the live log. The corrected package passes the same
check. Reproduce with:

```powershell
& 'D:/DCS World/bin/luae.exe' experiments/efm-ownership/release-start/check_loaded_defaults.lua E:/Projects/DCS_Recorder experiments/efm-ownership/results/countdown-release-2026-10-01/gear-package-v4 'D:/DCS World'
```

Substitute `gear-package-v2` to reproduce the retained failure. Preparation now
materializes installed Hornet property/Link16 defaults into both the generated
mission and expected data. Existing authored values are preserved. Strict
comparison is unchanged: changed positions, callsigns, extra properties,
additional aircraft and modified triggers are all refused by the regression.
The manifest records hashes of the installed default-resolution sources.

The five release CTest checks and all generated-package checks pass. Temporary
`[DEBUG-release-readiness]` instrumentation has been removed from active source;
normal state-change diagnostics retain the useful readiness reason. Preserved
failed-run logs and the previous-hook backup intentionally retain historical
diagnostic text.

After DCS closed, the updater backed up and replaced three diagnostic files:
the mission, expected reference and user hook. All 14 installed package hashes
match v4; the other 11 files, including native DLL and exact tape, are unchanged.
The normal release observation is next. Live readiness, release timing, first
movement, smoke emission and pause/refusal acceptance remain open.

## Full DCS serialization captured; reference corrected

The next PID 36760 run again timed out before countdown. Its first mismatch was
`coalition[blue][country][1][plane][group][1][units][1][heading]:value`, with
`model=0` and `native=READY,1,0,0`. The property-only loader fixture did not cover
the complete DCS load/save boundary and therefore did not prove live readiness.

The actual `tempMission.miz` named by this run's DCS loader was preserved before
exit under `readiness-failure-36760/raw/loaded-tempMission.miz`. Comparing every
checked field revealed all 13 changes together: six heading/psi values rounded
by approximately 2.0e-13 radians, two empty player radio-label maps added, three
empty cartridge containers omitted and two non-player radio tables omitted.
`loaded-differences.json` records the complete guarded-field comparison. The
captured archive also contains DCS exporter changes outside those guarded fields;
it is evidence, not a replacement installed mission.

Running the real hook against this captured serialization reproduces the exact
heading mismatch with v4. `prepare_reference.py` validates each observed change
against the original prepared mission, then generates the expected reference
from those reviewed loaded fields. It refuses unreviewed changes. The 1e-12
angle bound applies only to this reference-preparation audit; the installed
runtime comparison remains exact, and this is not a playback fidelity tolerance.
The original mission, native tape, source pose and recorded velocities are not
changed. Empty-cartridge omission is accepted only when there are no authored
points; radio omission is restricted to the diagnostic's non-player units.

The real-hook regression now passes against the captured serialization using
v5. Seven additional negative controls reject changed position, larger heading
changes, player radio frequencies, lost nonempty cartridge data, triggers,
unknown fields and callsigns. Existing real-hook controls also reject added
aircraft. These checks resolve the reproduced comparison defect, not live release
acceptance.

Reproduce the complete boundary test:

```powershell
& 'D:/DCS World/bin/luae.exe' experiments/efm-ownership/release-start/check_loaded_defaults.lua E:/Projects/DCS_Recorder experiments/efm-ownership/results/countdown-release-2026-10-01/gear-package-v5 'D:/DCS World' experiments/efm-ownership/results/countdown-release-2026-10-01/readiness-failure-36760/raw/loaded-mission.lua
```

Substitute v4 for the retained red case. The reference audit is independently
tested by `check_reference.py` with the v4 directory and captured MIZ as its two
arguments. Full provenance and reviewed differences are in v5's
`normalization-report.json` and manifest.

With DCS closed, only `Scripts/DCSRecorderReleaseControl/expected.lua` was backed
up and replaced. All 14 installed package hashes match v5; the other 13 files
are unchanged. The next step is the normal live countdown/release observation.
The issue remains open.

## Normal release succeeded with visible smoke

The v5 live run (PID 30864) completed. User review: “Okay, it seems to work
great.” Asked specifically whether smoke visibly emitted when the countdown
released playback, the user confirmed: “Yes, smoke was visible at release”.

`release-success-30864/raw/` preserves the completed DCS/native logs, installed
payload and package manifest. All 14 installed hashes match v5.
`release-success-30864/measure.py` produces `analysis.json` from this evidence.
There is one countdown, request, player release, native epoch and completion;
no failure event. The countdown spans exactly 3.000 simulator seconds.
Player release is at 16.653; native replay zero is at 16.660, a measured 7 ms
callback separation. This is not a claim of identical callback timestamps.

Across 832 held/countdown samples per aircraft, both player and playback have
zero position drift, and playback remains at replay zero. All 833 held native
motion writes command zero velocity. At the release epoch, commanded position
and velocity match the recorded first sample exactly at logged precision.
All 1,269 motion writes report matching readback; 41,877 exterior writes have
zero requested/readback difference. Engine and exterior replay logs span zero
through 8.70 seconds, and all 55,620 valid-engine reads are overridden.
These measurements establish native command/readback behavior; the user's
observation supplies the visible smoke evidence.

Normal release and visible smoke are now evidenced. Live pause, repeated-start
and readiness-refusal acceptance remain open. Next concrete check: pause the
simulator during the three-second countdown, wait, then resume; countdown must
finish its remaining simulator time rather than catch up to wall time.

## Countdown pause passed

User reported “Worked” after the requested countdown-pause run. PID 19800 logs
and native evidence are preserved in `countdown-pause-19800/raw/`; its
`measure.py` produces `analysis.json`. All 14 installed hashes still match v5.

The countdown lasts 3.000 simulator seconds across 5.548 wall seconds. A 2.580
wall-second gap between countdown samples advances simulator time only 0.020
seconds, with playback time zero on both sides. Native writes show the same
gap and model-time increment. Player and playback have zero position drift
across 352 held/countdown samples each. One request, release, native epoch and
completion occur, with no failure; player/native release separation is 5 ms.
This supports live countdown-pause acceptance without wall-time catch-up.

A separate 0.852 wall-second gap occurs during playback with only 0.020 seconds
of native time advance. Its cause is not established by the logs, so it is not
claimed as the deliberate playback-pause check. Next: a deliberate regular
simulator pause during playback, followed by repeated-start and readiness-refusal
checks. The issue remains open.

## Playback pause passed

User reported “Looked good” after the deliberate pause during playback.
PID 22980 evidence is retained under `playback-pause-22980/raw/`; `measure.py`
reproduces `analysis.json`. All 14 installed hashes still match v5.

Across a 3.083 wall-second gap, adjacent mission samples advance replay from
0.860 to 0.880 seconds, one normal 20 ms step. Native callback logs independently
show the same 20 ms advance across a 3.082 wall-second gap. Commanded position
advances 2.532 m, consistent with that single step at the recorded speed, rather
than advancing for the elapsed wall time. All native motion writes report
matching readback. The 8.70-second recording completes once across 12.412 wall
seconds, without failure or another release.

Both countdown-pause and playback-pause checks now have live evidence and user
review. Next: invoke Start again during countdown and playback to verify the
one-shot release boundary. Live readiness refusal remains outstanding.

## Final gates and airborne acceptance

User reported “Complete” after invoking Start during countdown and playback.
PID 41868 logs explicitly record `START_REFUSED,countdown` and
`START_REFUSED,playing`, with exactly one countdown/request/player release/native
commit/native epoch. No failure or second run occurs. The mission was exited
before this take completed; completed normal runs are preserved separately.
`repeated-start-41868/analysis.json` records that scope accurately.

Readiness refusal does not need another live run: the retained PID 36760 failure
demonstrates the required negative boundary. A loaded heading/reference mismatch
withheld arming, all 502 native writes commanded zero velocity, all 501 playback
samples stayed at replay zero and the same position, and no release request,
commit or epoch occurred. Failure destroyed the playback object and cleaned the
owned player hold. v4 and accepted v5 have identical mission, hook, guard, DLL
and tape hashes; the only changed payload is the audited expected reference.
`measure-final-gates.py` verifies this applicability and writes
`readiness-refusal-analysis.json`. This is live loaded-readiness refusal, not an
injected native-unready test; other refusal branches have offline coverage.

Final verification: all 11 selected release/held/snapshot/build callback checks
pass, and the real-hook fixture accepts captured DCS serialization while refusing
position, callsign, unknown-property, additional-aircraft and trigger edits.
All 14 installed payload hashes match v5. No further simulator installation
changes were needed for acceptance.

The airborne contract is accepted for the recorded 8.70-second gear-down Hornet
control on DCS 2.9.30.28536: held zero-time snapshot; one countdown/release;
original first position/velocity; shared replay clock for supported state;
visible recorded-ON smoke; no wall-time catch-up; duplicate and readiness refusal.
Observed player/native callback separation is 1–7 ms across successful runs,
not exact callback simultaneity or a newly agreed product tolerance. Full cockpit
restoration, production authored-session authorization, ground behavior and longer
flight acceptance remain with their existing tasks.
