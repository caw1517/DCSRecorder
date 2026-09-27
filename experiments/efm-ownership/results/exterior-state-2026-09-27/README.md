# Stock Hornet exterior-state capture

DCS 2.9.29.27468; diagnostic session 27 September 2026 UTC (26 September local).
The user reports completing the diagnostic. The log was preserved before rotation.
This is capture evidence, not a playback or independently reviewed video result.

## Integrity

- One stock `FA-18C_hornet` take with explicit `user_stop` and matching footer.
- 2,612 consecutive rows; every argument value finite; no missing rows.
- Mission time 7.861 through 138.411: 130.550 seconds between first/last samples.
- Every sample interval is 0.050 seconds within floating-point precision.
- All six markers appear: roll, pitch, rudder, gear, flaps, speedbrake.
- Preserved log SHA-256: `5ae7e7cfccb3b5e3495a44b97eb413a6e0be677fd5adf731ec935773b7f21983`.

## Measured responses

Ranges below are observed extrema, not validated full channel limits or angular units.
Channel meanings come from the installed descriptor; telemetry alone does not
independently establish left/right visual semantics.

| Marked segment | Samples | Relevant observed channels | Result |
| --- | ---: | --- | --- |
| Baseline | 410 | 9/10, 13/14, 15/16 | Small continuous adjustments even before marked input. Preserve initial values instead of assuming every surface is neutral. |
| Roll | 301 | 11: -0.294 to 0.482; 12: -0.268 to 0.529 | Ailerons respond, with coupled flap/elevator/rudder changes. Flap channels 9/10 also become negative (-0.170/-0.236). |
| Pitch | 315 | 15/16: approximately -0.981 to 0.596 | Both elevator channels respond across negative and positive values. |
| Rudder | 438 | 17/18: approximately -0.492 to 0.809 | Both rudder channels respond across negative and positive values. |
| Gear | 458 | 0/3/5: 0 to 1, starting and ending at 0 | All three gear-deployment channels complete extension and retraction. This does not test contact/compression. |
| Flaps | 433 | 9/10: 0.287 to 0.958; 13/14: 0.326 to 0.534 | Both candidate flap pairs respond. Ailerons droop to approximately -0.914 and rudders diverge. AUTO/HALF/FULL switch positions were not independently logged. |
| Speed brake | 257 | 21: 0 to 1, starting and ending at 0 | Existing reference channel completes extension and retraction. |

Arguments 28/29 also vary during the flap and speed-brake segments. Their meaning
is not established; do not label or replay them as a guessed control. Gear
compression arguments remain constant during this airborne test. No wheel,
ground-contact, engine, lighting or smoke conclusion follows from this capture.

## Consequences for the next prototype

Capture and replay individual surface values together at each timestamp. Do not
reconstruct surfaces from the pilot's control or flap-switch position. Signed
values must survive, including on trailing-edge flaps; a blanket 0..1 clamp would
discard observed motion. The first sample must include nonzero scheduled surface
values. Observed extrema are not appropriate hard limits for future recordings.

Next evidence is an isolated writer on the custom playback aircraft, comparing
requested values, immediate readback, next-step readback and visible response.
The existing diagnostic has no pose/velocity stream and therefore cannot serve
as a synchronized full-flight recording. A later recording integration must
capture motion and exterior state on the same clock. The fidelity ticket stays open.

## Reproduce analysis

```powershell
python experiments/efm-ownership/state-prototype/analyze.py experiments/efm-ownership/results/exterior-state-2026-09-27/dcs.log experiments/efm-ownership/results/exterior-state-2026-09-27
```

The local log and extracted CSV are ignored by Git. `summary.json` contains only
derived timing/range statistics; this report preserves the useful conclusions.
