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
mapping. Refuel activation and landing-light ground illumination need further
checks. Logs/generated assets remain local and ignored.
