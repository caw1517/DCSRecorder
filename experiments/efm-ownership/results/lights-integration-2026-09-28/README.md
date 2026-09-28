# Normal lights workflow: installed, live validation pending

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
