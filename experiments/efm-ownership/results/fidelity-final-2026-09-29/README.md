# Consolidated fidelity acceptance — 29 September 2026

**Accepted and resolved for the documented Hornet V1 scope.** The user completed
the final combined playback and reported that everything looked good. Final
delivery, lifecycle evidence and numerical limitations are recorded below.

The user requested one combined finish for
[Complete single-aircraft visual and engine-state fidelity](https://github.com/caw1517/DCSRecorder/issues/6).
They explicitly chose to check landing/taxi **ground illumination with ground
operations**, alongside [the ground-flight envelope](https://github.com/caw1517/DCSRecorder/issues/7).
This moves the rendering check, not a claim that it already passes.

## Numerical evidence review completed

[Reproducible audit](../../audit_integrated_fidelity.py) compares native tape
interpolation with requested appearance, SDK readback, native engine consumers,
motion commands, and available later mission reads. It separates mission
restarts and treats engine log timestamps as buffer-drain times: ordinary getter
calls consume the previous published sample. The destruction drain may also
contain endpoint calls. This does not measure audible onset or mixer latency.

Both original CSV files regenerate their activated tapes byte-for-byte. Original
CSV hashes are unchanged. The auditor rejects deliberately corrupted engine
output and missing appearance delivery in temporary copies.

| Evidence | Latest normal wheels take | Earlier normal afterburner take |
| --- | --- | --- |
| Source | `20260929T205005Z-0001.csv` | `20260928T002655Z-0001.csv` |
| Duration | 32.20 s | 31.98 s |
| Native motion/appearance updates | 1,612 | 1,601 |
| Sound.dll getter calls checked | 41,886 | 41,600 |
| DCS.exe engine getter calls checked | 28,843 | 27,338 |
| Maximum engine error after float conversion | < 5.1e-13 | < 5.1e-12 |
| Tape vs motion-command position | 0 at log precision | < 1e-12 m |
| Maximum SDK position rounding | 0.034563 m | 0.034624 m |
| Velocity command/readback difference | 0 | 0 |

The SDK returns float32 positions; the observed position difference matches that
conversion at the recorded world coordinates. It is not a newly agreed
product-wide tolerance. Basis components match tape interpolation within
5.1e-13; SDK readbacks match float conversion within log precision.

All six engine channels are present. The earlier take spans core RPM about
0.694–1.0004, fan RPM 0.379–1.0276 and power 0.151–1.8693, including afterburner.
Unsupported engine-index-zero queries pass through unchanged. Appearance
requests and readbacks match all channels present in each tape. The latest run
also has 1,613 independent playing/completion reads per group for surfaces/brake,
lights, canopy and wheels; maximum error is < 5e-10. The older mission did not
emit the later exterior telemetry, so no such evidence is claimed there.

Detailed derived summaries: [latest combined audit](wheels-audit.json) and
[earlier engine audit](engine-audit.json). Raw traces remain in the local accepted
evidence folders referenced by the preceding workflow records.

## Combined regression and final live pass

- All 37 companion tests pass, including legacy schemas, new channel plumbing,
  immutable sources, activation and rollback.
- Seven native checks pass: recorded geometry, native step boundary, staging
  contract, mission lifecycle, wheel animation boundary, integrated wheels
  callback and combined engine boundary.
- The final mission passes installed module/route checks and an executed
  sequence fixture covering startup, phase ordering, early stop, cleanup and
  one-shot behavior. The source mission configuration is checked before editing;
  the final fixture checks aircraft/livery/pylons and the new commands.

Installed **DCSRecorder-Final-Fidelity-Capture.miz**, SHA-256
`987fb4cff2c1dcfa3685d6376fed7c8434131cebdc46090f6abad8ab23c5b6b5`.
Only a new mission file is installed; the normal capture/module/tape are intact.
This evening flight uses the actual version-seven recorder. The 90-second
sequence starts on normal F10 recording and commands lights plus refueling probe
controls; the user flies and follows gear/brake/smoke/power prompts. Stopping
recording cleans up automated switches. It does not stop recording on the user's
behalf or fabricate sample values.

Remaining closure evidence: inspect this fresh capture, replay it through the
normal integrated module in matching evening lighting, audit delivery and obtain
the user's combined visual/audio verdict. Refuel argument 212 has previously
been zero; its activation/rendering still needs evidence. Probe geometry itself
is not currently in the supported animation profile; verify whether it is needed
for the light to render correctly before claiming this gap closed. The existing
changing canopy/taxi-wheel tests remain accepted and are not repeated in flight.

The issue remains open pending that final pass. Exact stationary starts, contact,
high-speed/reverse wheel sampling and ground illumination remain under the
ground work. White smoke is V1; sound depth and other smoke colors remain V2.

## Final combined capture received

The user completed `20260929T212400Z-0001.csv`: 4,760 samples over 95.18 seconds,
119.42–165.50 m/s, valid normal version-seven metadata and explicit user stop.
Source SHA-256 is
`9c0378dd228c7577e3c6576342d027ebd5763779c2506c180c6070838cc217b9`.
The saved log includes all nine sequence phases and cleanup. All 242,760 mission
fields are preserved in the saved recording, including the sample times and
all appearance channels. Native helper values additionally pass the production
alignment/identity/range checks during conversion.

The recording exercises gear 0–1, brake 0–1, signed control surfaces, both flames
0–0.6114, nozzle motion, native power to 1.4015, four white-smoke transitions,
dim/bright navigation/formation, strobes and landing/taxi light. Refuel argument
212 now measures the intended sequence: zero before extension, 0.322331 during
ON, zero with master OFF, 0.322331 after master ON, then zero after retraction.
This establishes nonzero refuel capture, not yet its playback rendering.
Canopy, compression and steering remain at their measured airborne states.

Prepared `package/final-fidelity-playback` using the normal integrated wheel
controller and source-preserving converter. The playback mission has the same
19:00 time and date as capture. Installed DCS dependency/route/configuration
checks pass, as do native tape evaluation at 100 Hz and the actual-tape wheel
interpolation/endpoint/SDK checks. The user has been asked to close DCS before
activation; live combined playback remains pending. The source CSV and capture
log are safely retained locally under `capture/`; its derived
[summary](capture/summary.json) records ranges and phase coverage.

After the user confirmed DCS closed, the normal activation path installed
**DCSRecorder-Playback-591abac7.miz**, generation
`591abac7c4854203bdc8ee597e3d9b6b`. The prior tape and metadata are backed up.
The two active tape files match the checked package; all 4,104 protected existing
module, hook and recording files retain their hashes. The original recording
hash is unchanged. The user has the final playback instructions. Visual/audio
acceptance, live delivery audit and issue closure remain pending.

## Final combined playback accepted

The user completed **DCSRecorder-Playback-591abac7.miz** and reported, “everything
looks good,” in response to the combined visual/audio review including the
refueling-light sequence. Process 34564 traces and the DCS log are retained under
local `playback-accepted/`. The original recording hash remains unchanged.

The [final audit](final-audit.json) establishes:

- 4,761 native motion/appearance updates through the tape endpoint. Motion
  commands match the recorded path; float32 SDK position rounding peaks at
  0.034757 m, and velocity readback matches the command.
- All added appearance channels retain their delivered values. There are 4,762
  later mission observations for each surface, lights, canopy and wheel group;
  their maximum error is about 5e-10. This includes changing refuel argument 212.
- All six engine channels match measured tape values within float/log precision
  on 123,760 Sound.dll and 89,504 DCS.exe consumer calls.
- All five smoke states (initial OFF plus four transitions) are delivered in
  order. Maximum command delay from the captured event is approximately 18 ms.
- Native completion at 103.001 s, mission completion at 103.020 s, removal of the
  lead and guarded destruction cleanup (`step_hook_already_replaced`).

Two numerical qualifications are retained explicitly. Fifty strobe samples
occur at tape boundaries whose native elapsed log rounds to that boundary. The
sample-hold result is the immediately preceding sample, consistent with a native
double just before the edge; the trace cannot determine that side exactly.
The auditor permits that alternative only within 1e-10 s of a boundary and still
rejects corrupted values. Later mission observations match the delivered strobe
values. This does not claim sub-frame strobe timing.

The legacy speed-brake channel is written before native animation, unlike the
new appearance channels. In this changing-brake run, 2,016 of 4,762 later reads
differ from the tape, with maximum absolute difference **0.010002 on the 0–1
scale**. Earlier audit takes had a stationary brake and did not expose this.
The auditor now reports this residual separately rather than declaring exact
readback or silently relaxing the other checks. The user accepted its appearance;
the numerical residual is carried into
[exact synchronized-state work](https://github.com/caw1517/DCSRecorder/issues/11).
No production tolerance is inferred, and no runtime code changed after the
accepted flight.

This resolves the bounded capture/playback capability question: versioned,
immutable Hornet recordings reproduce the tested appearance groups and measured
native engine state with user-accepted sound/visuals. Probe extension geometry is
not a supported captured channel; the final verdict accepts the refuel-light
comparison without establishing probe-motion fidelity. Broader aircraft types,
full cockpit systems, arbitrary ground initialization, ground physics and
product-wide numerical tolerances are not established here. Ground illumination
remains explicitly assigned to ground operations; sound depth and multicolor
smoke remain V2. The next map ticket is exact starting position and synchronized
state.
