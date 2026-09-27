# Missing gear in application playback

The available application take did not capture gear. This is a legacy-capture
workflow failure, not evidence of a new exterior-controller rendering failure.
Fresh live capture and replay were subsequently accepted by the user; see below.

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

## Fresh live workflow accepted

The user reports: "All worked well!" This accepts the fresh capture/application
playback check for the missing-gear workflow.

The new take `20260927T185539Z-0001.csv` has 2,272 version-two samples over
45.42 seconds with `hornet-exterior-v1`. All three gear channels span 0..1.
Package `02d1df4d5c7a4f4aa30d5b3beb30d26e` selects the exterior controller and
preserves source bytes (SHA256
`a7941c02c33c9a3a116db332e0c0cc9198267b2aef2aa049f41eab06b7b4246e`).

The retained native exterior trace contains 27,404 post-animation writes through
42.14 seconds. Each gear channel reaches both 0 and 1. Across all captured
surfaces, maximum requested-versus-immediate-post-write difference is about
1e-14 in the serialized trace. This corroborates actuation; visual acceptance
comes from the user. This snapshot has no later mission exterior observations
and ends before the 45.42-second endpoint, so it does not establish automatic
completion/removal or restart. Raw evidence remains local.

The missing-gear workflow is accepted. The broader ticket stays open for the
remaining lifecycle evidence and suspension/wheels, canopy, smoke, lights,
separate nozzles, afterburner effects and sound. Engine-state work can resume.
