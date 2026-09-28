# Wheel and suspension checkpoint — 28 September 2026

Status: separate read-only taxi diagnostic checked and installed; live capture
pending. Normal canopy integration is accepted in its own evidence record.

The [prototype](../../wheel-prototype/README.md) samples deployment, compression
and rotation for all three gear assemblies, alongside position and velocity.
Installed Hornet FM definitions are checked during packaging. The parked hot
start reuses the live-verified canopy diagnostic location.

Checks passed installed aircraft dependency/route validation and six packaged
capture cases: normal, overspeed, airborne, lost aircraft, invalid arguments and
timeout. Duplicate starts and paused frames do not add samples. The analyzer
fixture contains 2,000 ordered samples with maximum 20 ms spacing; those synthetic
values do not establish live ranges or a rotation period.

Installed new mission:
`C:/Users/w_can/Saved Games/DCS/Missions/DCSRecorder-Wheel-Diagnostic.miz`.
SHA-256: `dd83429621fb38692a2507d10430c0096333ff300eea00887579c853cd38983f`.
All 527 protected script/module/recording hashes were unchanged. Installation
added no DLL or hook and required no DCS restart. Package, installation report,
raw assets and later captures remain local and ignored.

The user is asked for two slow taxi/brake-to-stop cycles, with initial/final
stationary holds and optional external observation. Next: preserve the log and
compare raw rotation changes with motion and compression responses. No wrap
period, unloaded compression endpoint or ground-physics playback is claimed yet.
