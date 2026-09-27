# Missing gear in application playback

The available application take did not capture gear. This is a legacy-capture
workflow failure, not evidence of a new exterior-controller rendering failure.
Fresh live capture and replay remain to be checked by the user.

## Evidence

- The latest take, `20260927T035232Z-0001.csv`, contains 1,835 samples over
  36.68 seconds in `DCSREC,1`. It has no gear or other exterior-state columns.
  SHA256: `4937c819f8165b86bbd72c60527502f681598f79f187849f327791035f85b1f9`.
- Package `e40abf40ce0b4f0f9253112f93b470aa` preserves those source bytes,
  selects `DCSRecorder-Hornet-Staged`, correctly reports exterior unavailable,
  and matches the installed legacy tape.
- The only installed `DCSRecorder-Practice-*` mission before investigation,
  `DCSRecorder-Practice-8e9f5ddf.miz`, embeds the version-one recorder and predates
  the exterior integration. The separate prepared integrated capture mission
  embeds version two. This explains the different capabilities; the retained
  playback log does not independently identify which capture mission was flown.
- The installed autosave hook matches current source. Running the actual old
  mission's embedded recorder in the simulated-aircraft harness reproduces the
  missing gear fields. Current app generation produces version-two fields.

Original recording, old mission, playback mission/tape and live log are preserved
locally. `live-dcs.log` is the live evidence; `dcs.log` is harness output. Raw
assets and simulated captures remain local.

## Reproduction and correction

Run `python experiments/efm-ownership/results/application-gear-2026-09-27/check_gear_capture.py <recording.csv>`.
The original take and old mission's simulated capture fail:

```text
DCSREC,1: 1835 samples
AssertionError: Recorded gear deployment unavailable: missing arg_0
```

This checks necessary recorded gear evidence, not DCS rendering. Missing values
cannot be reconstructed. The old take stays unchanged and supports motion replay.

The app now labels legacy takes **Motion only**, names the missing gear/flaps/
control surfaces, and explains how to record them. That notice also appears after
generating legacy playback. New takes show **Motion + surfaces**. New practice
filenames include `Exterior`; their briefing names the captured group and the app
says to load the exact new file. Existing missions are preserved.

## Validation and next live check

All 14 companion tests pass. The new integration test exercises actual app
practice generation, packaged Lua capture with simulated gear deployment,
extraction, library validation and playback conversion. All three gear channels
survive unchanged into the exterior native tape, which passes the native reader.
The legacy-notice test covers selection and generation without changing source
bytes. Existing sink tests cover both recording versions and signed state.

With DCS closed, generated `DCSRecorder-Practice-Exterior-c4d03e7f.miz` directly in
Saved Games/DCS/Missions and started the current companion at its existing local
address. Its API labels the affected take Motion only and confirms the hook
matches. Separately exercising the installed mission's embedded recorder passes
the gear checker with all three simulated ranges approximately 0.006667..1.
Source bytes still match the original hash. No DLL or active playback tape changed.

Next: fly that exact new practice mission, record gear deployment/retraction
while airborne, and F10 Stop. Confirm **Motion + surfaces** in the library.
Close DCS, generate playback, compare gear visually and retain runtime logs.
That fresh live result is pending. The broader visual/engine-state ticket stays
open; engine-state expansion waits until this workflow is accepted.
