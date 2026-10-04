## Completion — complete recorded airborne snapshot accepted

The user completed both live controls on DCS 2.9.30.28536, Hornet/Blue Angels, Caucasus, zero wind. They accepted the brake-extended hold (everything looked great except absent held smoke) and the gear-down first-visible/30-second hold with **“Looked great.”** They explicitly allow smoke to remain invisible while held if it appears when playback resumes. The recorded initial smoke state and initial ON command are retained; release emission is required by [Release player and playback on one countdown clock](https://github.com/caw1517/DCSRecorder/issues/22).

### Checklist evidence

- **Complete time-zero snapshot:** two immutable normal version-seven captures contain original pose/release velocity, all 33 supported appearance channels, six native engine consumer values and measured white-smoke state. The held controller initializes from the first sample, refuses incomplete native groups, holds the replay clock at zero and reapplies state after native animation. No synthetic combination of gear/brake was substituted for captured state.
- **First visibility and held inspection:** user accepted both distinct non-default initial configurations (brake 1.0/gear up, then brake 0/gear down, with nonzero lights/surfaces). Both runs have 302 mission observations from time 0 through 30.02 s, one lead identity, zero sampled pose/orientation drift, zero lead velocity, zero replay-clock advancement and exact original position at mission-log precision. First-visible visual evidence is the user's live review, not frame-by-frame video.
- **Retention and limits:** brake run has 52,635 post-animation rows; gear run 52,074, each spanning all 33 appearance channels with zero source difference at log precision. All 69,058 and 68,327 valid engine getter overrides respectively match the first sample across six channels. Later appearance observations have no drift and maximum source differences 4.02e-10 / 3.42e-10. Native position readback has expected float rounding (maxima 0.013499 / 0.021691 m), without corresponding mission drift. Both runs have one create/destroy and the existing guarded destruction status. These are measured bounds, not newly agreed product tolerances.

### Reproducible implementation/evidence handoff

Local working-tree paths (not claimed as newly published commits):
- `experiments/efm-ownership/held-start/`: package builder, mission, validated installer/switch, analyzer and offline fixtures.
- `experiments/efm-ownership/object_probe.cpp`: complete held-state refusal and shared post-animation brake retention.
- `experiments/efm-ownership/results/snapshot-2026-09-30/README.md`, `brake-summary.json`, `gear-summary.json`: complete evidence index, measurements, user-review scope and hashes. Exact raw logs, source captures and package/install receipts are retained locally.

Reproduce with `python experiments/efm-ownership/held-start/analyze.py <brake-live-complete or gear-live folder> --manifest <matching brake-package or gear-package>/manifest.json` beneath that result directory. Six relevant rebuilt offline checks also pass; live evidence above is the acceptance basis.

Installed diagnostic DLL SHA-256: `b4f79b38d4582db0b6621f52063cf8c15a2bc329900b03e58b81ba197fbd7dbe`. Brake source SHA-256: `f958b20b80f5166e3768623aee82868dee6ebe84f786c484625bd676c374ec0b`. Gear source SHA-256: `e9154d5f1bb953694ecf918a96ea4fa2cacba99d9b69eb24cc76b7bf90301bfd`.

### Boundaries retained

This closes the bounded airborne snapshot implementation step. Countdown/release, hot-ground/contact/first movement, parked completion, changing-state fidelity, ground illumination and restart retain their ordered tasks. Smoke invisibility while held is explicitly accepted; a velocity-based explanation is unproven. Smoke ON at release remains unverified.

Full cockpit/internal engine restoration and refueling-probe geometry are unavailable. These two starts do not independently demonstrate non-default canopy, afterburner flames, compressed/steered wheels or every light state; their actual recorded values are present and retained. Earlier changing-channel acceptance remains prior evidence. Preserve the historical changing-brake residual **0.010002** (2,016 of 4,762 later reads) for [Verify exterior-state retention and ground light illumination](https://github.com/caw1517/DCSRecorder/issues/30), with countdown/release and endpoint coverage in their owning tasks. The current hold does not establish its removal during motion.

The separate snapshot module remains installed with the gear-down take. The accepted normal companion runtime was not replaced. Reopen this task if subsequent integration invalidates its result.
