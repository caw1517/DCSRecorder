# Airborne held staging accepted — 30 September 2026

Outcome for [Prove visible airborne held staging](https://github.com/caw1517/DCSRecorder/issues/20):
the single real playback aircraft remained visibly held while the surrounding
mission ran. The user reported that the scene witness flew away and the lead
"sat there perfectly still the whole time," and separately confirmed steady
engine sound without unexpected changes.

## Configuration and evidence

DCS 2.9.30.28536, Hornet/Blue Angels, Caucasus, zero wind; diagnostic mission
`040-Hornet-Held-Start.miz`, module `DCSRecorder-Hornet-Held-Test`, PID 26264.
The package uses the first sample of the retained 95.18-second version-seven
take captured on 2.9.29.27468. This run validates that sample's bounded hold on
the installed newer build, not the remainder of that recorded flight.

The mission completed its observation at model time 30.020. The user exited
normally afterward. Raw mission/native logs, installed tape, diagnostic DLL and
mission are retained under ignored `raw/`; [summary.json](summary.json) records
their SHA-256 hashes and the computed measurements. Reproduce the analysis with
`python experiments/efm-ownership/held-start/analyze.py experiments/efm-ownership/results/held-staging-2026-09-30`.
The analyzer consumes the retained snapshot without modifying it.

| Observation | Result |
| --- | --- |
| Mission samples | 301 per aircraft, from 0.020 through 30.020 seconds |
| Lead identity | One mission ID (9001), one native object ID (16777472); these are different ID namespaces |
| Lead/player position drift | Zero in the sampled mission telemetry |
| Lead orientation, velocity and clock | Constant sampled orientation, zero velocity, replay time zero and held status 0.125 throughout |
| Original position | Mission telemetry equals the first tape position at logged precision |
| Independent witness | Moved 3,696.33 metres during the observation |
| Native motion | 1,699 successful matched writes through time 33.960; 1,698 pre-physics applications at the last logged write |
| Native position readback | Maximum 0.015851 m source difference in the float-valued native position; no corresponding mission-telemetry drift |
| Supported appearance | 56,067 post-animation records over 33 channels, all at replay time zero; requested and retained values match the tape at logged precision |
| Mission appearance | No temporal drift; maximum source difference 4.61e-10 at mission-log precision |
| Engine parameters | 73,530 valid-engine overrides across core/fan/power for both engines match the first sample at logged precision |
| Other engine queries | 1,698 engine-index-zero queries passed through unchanged, as required by the existing engine-index guard |
| User review | Lead perfectly still; witness flew away; engine sound steady |

There was one native create and one destroy event. On destruction the hook
reported `step_hook_already_replaced`, the code path that declines to overwrite
an object table already replaced during destruction. This is not a claim that
all restart/failure cleanup paths have been demonstrated. The mission emitted
no DCSR_HELD failure. Unrelated installed-hook errors remain visible in the
retained full DCS log; no changes were made to those integrations.

## Limits and next work

This accepts the hold-only experiment and the current task. No stand-in was
needed. There is no captured video/audio artifact or frame-by-frame first-visible
analysis; visual/audio acceptance is the user's live observation. These measured
values do not establish product-wide tolerances.

The complete initial-snapshot task remains open, including non-default channel
coverage and the first inspectable frame. Countdown/release, ground staging,
changing-state speed-brake retention, parked completion, actual ground light
illumination and restart/failure acceptance retain their later tasks. In
particular, this take's zero initial speed brake does not validate a changing
or nonzero brake hold. The diagnostic remains installed and is separate from
the accepted normal companion workflow.
