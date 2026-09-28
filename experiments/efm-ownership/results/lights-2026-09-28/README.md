# V1 scope and first light observation mission

The user explicitly limits **V1 smoke to white only** and defers multicolor smoke
and richer engine sound depth/bass/impact to **V2**. They no longer block current
V1 fidelity acceptance. Both have separate backlog tickets linked to the map:

- [Improve playback engine sound depth (V2)](https://github.com/caw1517/DCSRecorder/issues/12).
- [Add multicolor demonstration smoke (V2)](https://github.com/caw1517/DCSRecorder/issues/13).

The active group is exterior lights, followed by the remaining canopy and
wheel/suspension animation work and combined validation. The existing accepted
motion, surfaces, engine/nozzle/flame behavior and white-smoke workflow remain.

Prepared and installed **DCSRecorder-Lights-Diagnostic.miz**. It contains one
stock Hornet at night, with Active Pause holding position. The user lowers gear
and starts an automatic eleven-phase light sequence from F10, observing from F2.
Installed cockpit device/command definitions supply the light controls. The
probe records actual command callback times and selected exterior/gear arguments
at 50 Hz, separately from desired settings. No native helper is introduced.

Installed DCS dependency and route validators pass. The packaged script harness
passes startup, installed command IDs, all phases, sample ordering, duplicate
start, completion, explicit stop/cleanup and missing-phase timeout checks. Only
the new mission was copied; **117 protected file hashes are unchanged**. No
restart is needed to load a new mission. Live observation remains pending;
argument values and actual rendering are not yet declared a validated light
mapping at that checkpoint. Refuel activation and landing-light ground
illumination need further checks. Logs/generated assets remain local and ignored.

## Accepted stock response

The user completed the sequence and confirmed: **"All listed above worked
well"**, referring to position/navigation, formation, flashing strobes and
landing/taxi. Saved `live-first.log` has SHA-256
`6f297144b2b1dc85cd250d7bda0eb2a416fc20510885fb8bec1038bf1bcd2afd`.
Analysis passes: **3,362 samples**, **67.24 model seconds**, eleven applied
phases and **20 ms maximum sample gap**. Control-trigger delivery is measured
separately from the sample clock (81..981 ms in this run).

- Navigation arguments 190/191/192 and formation 88 show about 0.275 at DIM
  and 0.914 at BRIGHT, returning to zero when off. These are measured values,
  not assumed equality with the commanded 0.3/1 dimmer settings.
- Strobe 193 pulses between zero and peaks of 0.586 (DIM) / 0.895 (BRIGHT).
- Landing/taxi 210 averages 0.985 in its ON phase with gear deployed.
- Refuel 212 remains zero; it was not activated by this sequence.

## Isolated recorded-light replay

Prepared and installed **DCSRecorder-Lights-Playback.miz** and a separately
registered **DCSRecorder-Hornet-Lights** module. It replays the actual ten-channel
gear/light capture at night on an ordinary AI route. It does not replay this
diagnostic's flight motion or replace the accepted motion/engine module.
Strobe samples use a hold between samples; other channels interpolate.
This first experiment uses only the object SDK, without native timing hooks.
Mission-side samples and native write/readback traces will establish retention;
user observation must establish visible rendering.

The built DLL passes all 3,362 captured samples, off-grid strobe holds,
interpolation, completion and identity/cookie/bounds/lifecycle/clock guards.
Mission checks pass F10 start, release, completion/removal, writer failure,
missing handshake and explicit stop. Installed dependency, route and clean
configuration checks pass. Existing surface and engine SDK variants also pass
their 2,612- and 979-sample fixtures after the shared experiment extension.
Installation verifies ten asset hashes and **1,482 protected files unchanged**.
Live recorded-light playback remains pending.
