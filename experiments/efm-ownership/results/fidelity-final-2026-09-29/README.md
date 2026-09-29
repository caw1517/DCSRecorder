# Consolidated fidelity acceptance — 29 September 2026

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
