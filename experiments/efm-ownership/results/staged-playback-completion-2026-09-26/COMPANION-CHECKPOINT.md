# Companion workflow implementation checkpoint - 26 September 2026

Source: C:/Users/w_can/.codex/worktrees/airborne-staging/DCS_Recorder/companion/
Branch: codex/airborne-staging (new integration/companion source remains local).

Implemented and installed a separate automatic-save GUI hook, a loopback browser
flight library, immutable recording data with rename sidecars, strict validation,
practice mission generation, and staged playback package generation/activation.
The save hook reads the proven mission log protocol without a GUI-to-mission
bridge. Explicitly stopped takes become timestamped CSV files; incomplete takes
stay .partial and are never offered for playback. New practice metadata records
the supported build and actual weather speeds. Completed files no longer depend
on retaining the DCS log.

Verification: 7 companion tests and all 11 native CTests pass. An isolated full
workflow generated a practice mission, simulated its recording controls with the
installed Lua runtime, validated two completed captures, generated playback and
verified the previous tape backup. In the actual UI, selection and naming worked
without altering source recording bytes, and Create practice mission succeeded.
The library refresh was fixed to preserve unchanged rows/focus.

Installed hook SHA-256:
1206476f3498c05ecbd28a09a2a3b424e554a241cc99d7709dfa53869fcd57c6

Actual practice mission:
C:/Users/w_can/Saved Games/DCS/Missions/DCSRecorder-Practice-8e9f5ddf.miz

Launcher:
C:/Users/w_can/Saved Games/DCS/DCSRecorder/Start-DCSRecorder.ps1

Next live check: start DCS fresh, record 20-30 seconds in the generated practice
mission, explicitly Stop through F10, and wait for the new timestamped flight to
appear in the app before exiting DCS. Then validate/select it, close DCS, generate
its playback mission, and test playback. Hook persistence and a new take through
the app are not yet live-verified. The issue remains open for these checks,
real pause/resume, longer/repeated takes and frame-rate coverage.
