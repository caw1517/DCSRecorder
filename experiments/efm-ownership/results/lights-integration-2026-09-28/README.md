# Normal lights workflow: usual configuration accepted

Carries the accepted isolated light capture/replay through normal recording,
automatic save, library validation and generated staged playback. Version-five
recordings declare `hornet-lights-v1` and carry arguments 88, 190/191/192, 193,
210 and 212 on the mission motion clock. Native engine capture retains its own
validated time association; measured white smoke remains optional. Versions
one through four keep their original columns, meanings and module selection.

The new native tape version four appends seven light values to the existing
motion/surface/engine row. Strobe 193 uses sample hold; continuous brightness
interpolates. Initial and endpoint states are retained. Invalid profiles,
columns, clocks, nonfinite/out-of-range lights or incomplete captures fail
validation. The library labels new flights with `+ lights`.

`DCSRecorder-Hornet-Lights-Staged` / `HornetLightsStagedProbe` is a separate
module. It uses the existing common playback clock and shared owned animation
boundary to reapply lights after native animation. Legacy off defaults no longer
erase recorded lights. This is the proposed correction for the brief formation
startup overwrite found in the isolated SDK experiment; live retained values
must still demonstrate that the boundary is late enough. No new independent
native interception table is introduced.

Validation: **27 companion tests pass**, including actual Lua save-hook/native
sampler fixtures with and without smoke, packaged mission capture, invalid
light rejection, unchanged source recordings, old versions and generated
native tape/module selection. **Seven native/lifecycle checks pass** for tape
geometry/contracts, callback identity guards, staged mission lifecycle, the
existing animation boundary and engine boundary/lifecycle. The native contract
checks light interpolation, sample-held strobe edges, endpoint state, reapplying
after a simulated formation overwrite, preserving lights through defaults and
rejecting invalid values/short arrays/wrong identity before writes. This does
not substitute for a live DCS timing test.

Installed eleven checked files while DCS was closed. The prior save hook and
settings are backed up in the ignored package; **591 protected files are
unchanged**. Existing playback modules, tapes and recordings are preserved.
The companion was launched with the updated settings and responds successfully;
existing smoke/engine/surface recordings still appear as supported.

Installed practice mission: **DCSRecorder-Practice-Lights-fc92497a.miz**.
The user has been asked to record a fresh short light sequence through the
normal F10 Start/Stop workflow, then leave DCS open. Next: validate the saved
flight, prepare its normal playback while DCS is closed, and check both visible
behavior and later light telemetry (especially the initial formation OFF
interval). Refuel activation and ground illumination remain unverified; canopy,
wheel/suspension work and combined regression remain later V1 gates.

## First normal capture and requested playback

Saved **20260928T154136Z-0001.csv** passes library and native conversion checks:
**5,366 samples / 107.30 seconds**, maximum 20 ms sample gap, SHA-256
`6f99d36c5f16a27c9fa785dcab934d672dd71c66ebbf283b22fea69ad5240dc3`.
The app labels it **Motion + surfaces + engines + smoke + lights**. Smoke is
initially OFF, ON at 67.766 seconds, and OFF at 104.344 seconds.

All seven light channels are zero throughout. A comparison of every mission
protocol row with the saved CSV confirms the values were preserved by automatic
save. The user clarified that they mainly exercised other controls, normally
use this light configuration, and want to accept playback if it matches. Honor
that requested comparison; do not require another changing-light capture merely
because this take is intentionally lights-off. The earlier isolated changing-
light sequence remains visually accepted. Broader untested light behavior must
not be inferred from this take.

Prepared and activated **DCSRecorder-Playback-3b3b1520.miz** with DCS closed.
The exact source recording is unchanged, the installed controller matches the
checked package, and the native tape hashes verify. Installed dependency, route,
clean-loadout and native geometry evaluation checks pass. The normal library
activation path preserves other modules/recordings and creates a new mission.
Raw capture, summary and activation record are local under ignored
`capture-first/`; the prepared package is ignored under `package/lights-real-first`.

The user has been asked to run the full flight through completion and watch
particularly for unwanted startup lights. This take is useful numerical coverage
for the prior formation OFF-state overwrite. Live playback/retention is pending;
no visual or numerical pass is claimed yet.

## Normal playback accepted

The user reports **"Approved and working"** after the requested lights-off
comparison. Preserve that acceptance; no repeat of this take is required.
The log contains **two complete runs**, each starting at mission time 7.82 and
completing at 115.12, reproducing the full 107.30 seconds. Native completion,
safe hook ownership release and aircraft destruction are logged twice.

Across both runs, all **75,124 post-animation light rows** match their recorded
OFF values exactly. Formation 88 is overwritten by native animation 50 times
(25 per run); every one is corrected to zero at the shared animation boundary.
This corroborates the user's successful visual result and directly exercises
the earlier startup defect. Recorded white-smoke OFF/ON/OFF executes on both
runs, with maximum command delay **15.999299 ms**. Source recording bytes remain
unchanged. This establishes the requested normal workflow with the user's usual
lights-off configuration; changing lights retain their prior isolated acceptance.

An evidence limitation was found and fixed: the generated runtime mission config
did not forward the exterior/light telemetry flags, so this accepted mission has
native post-animation readings but no independent later mission light readings.
The packager now forwards both flags. A regression executes the actual packaged
config, fails before that correction, and passes afterward; all 27 companion
tests pass. Future generated missions gain these diagnostic measurements. The
accepted mission and installed native controller were not changed for this fix.
Do not claim independent later-read retention for these two runs.

Raw evidence remains ignored under `playback-accepted/`, including the copied
native logs, `light-native-summary.json` and `verification.json`:

- `dcs.log`: SHA-256 `32c519e596274b95f45d1744dbd46575159ba73182a15b1aee557f57888b823c`.
- `exterior-16216.csv`: SHA-256 `9c8ebb2800653720067b7bfe019bc67b33d9f5d8fd2b603715a5c5e85a2e6966`.
- `objects-16216-4022343.csv`: SHA-256 `e54dd935fecd13f7cca5f727e70df0a8f4be9abd44e2e9fd2b929a45eba3f301`.

Next state group: canopy position/transitions, then wheel rotation and suspension.
Refuel activation, landing-light ground illumination and broader combined evidence
remain unverified; they do not reopen this accepted usual-configuration test.
