# Staged playback completion — 2026-09-26

The user reported “Reached and working” after being asked to let the full
recording complete and continue flying. Native and mission logs corroborate
completion for the third run in DCS process 13152, build 2.9.29.27468.

- F10 at 2.376s; actual release/native start at 5.801s.
- Native completion at 44.581s: exactly 38.78s of playback and 1,940 successful motion writes.
- Mission COMPLETE at 44.600s, 19 ms after native completion.
- Native physics-step hook restored; playback object destroyed.
- 199 player samples continue for 3.96s after completion; one final lead sample appears on the completion tick, with none on later ticks.
- First and last commanded positions match the tape at logged precision. Initial native position readback differs by 6.93 mm due to float precision; initial velocity matches at logged precision.

The earlier two runs demonstrated start/restart but were ended by the user before
tape completion. This third run establishes the tested full-flight start/end
lifecycle. It does not establish independent recording continuity, normal
pause/resume, other runtime IDs, longer takes, broader aircraft state fidelity,
or compatibility with other DCS builds. The companion app workflow remains open.

Raw snapshots stay local and ignored. summary.json records source hashes.
Test DLL SHA-256: 4fb9683ed816a7dcf30360fde8d8be32d7d0cfb2cf88ec1688e88ae42abe4e12.
