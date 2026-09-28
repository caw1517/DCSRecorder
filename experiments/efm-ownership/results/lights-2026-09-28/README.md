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
Live recorded-light playback was pending at installation; the subsequent result
is recorded below.

## Accepted visual playback, with one numerical startup discrepancy

On 28 September the user completed the playback mission and reported:
**"Complete and everything looked and worked well."** This accepts the visible
position/navigation, formation, strobe and landing/taxi sequence. No repeat of
the same isolated test is required.

The preserved PID 31184 trace contains **3,762 SDK calls** and **3,758 later
mission samples**, all for object 16777472. The sequence starts at mission time
3.55, completes at 70.77 (67.22 seconds of tape), holds its endpoint for eight
seconds, then destroys the test aircraft at 78.77. Mission cleanup reports
`END,complete`. The 20 ms difference from the capture duration is the interval
between capture BEGIN and its first DATA sample, not a missing tape sample.
All installed asset hashes still match the checked package.

Every immediate SDK write matches its requested value. Later mission reads for
navigation 190/191/192, strobe 193 and landing/taxi 210 match within 5e-10
(serialization precision). Refuel 212 stays zero and is still unexercised.
The elapsed-argument rounding is at most 3.724 microseconds.

**Formation-light startup overwrite remains an integration requirement.**
Argument 88 differs in 25 later samples, at elapsed 3.76..4.24 seconds, during
the first all-off hold: requested zero, observed values rise from 0.222 to one.
The next SDK callbacks independently see the same overwrite before restoring
zero. This rules out a simple transition-clock mismatch; the exact later DCS
writer is not yet identified. The remaining formation samples match. Gear
deployment has a smaller native drift of about 0.00502, consistent with the
separate SDK-only surface experiment; do not claim exact full-channel retention.

The retained-trace command is deterministic and intentionally fails until the
formation discrepancy is addressed in a new run:

```text
python experiments/efm-ownership/lights-prototype/check_retention.py <state.csv> <dcs.log> <retention.json> --assert-lights
3762 SDK calls; 3758 later reads; light mismatches: [88]
FAIL: light values changed after SDK write: [88]
```

Raw evidence and derived JSON remain ignored under `playback-accepted/`:

- `dcs.log`: SHA-256 `ebc3a8f577277a70225fbe2a3c5884576ad20a1ad2e13899a20a0d99e00770bf`.
- `state-31184-2221937.csv`: SHA-256 `fbc6924d899fed9a36d228451272b9fb107ebd3aaa13f904ca558dbabe71fe28`.
- `events-31184-2221937.csv`: SHA-256 `9ad81ce5beaace9a4fc0c2400c93cebe4663fbe6a39ededfa197ecf05f742c83`.

Next, carry measured lights through normal capture, storage and playback with
legacy compatibility and the existing common playback clock. Address the
formation startup overwrite at the shared animation boundary and validate
retention there; that boundary is a candidate, not yet a proven light repair.
Canopy, wheels/suspension, refuel activation, ground illumination and combined
regression remain open V1 work. The active fidelity issue stays open.
