# Complete supported initial snapshot — accepted airborne control

Work for [Initialize the complete supported playback snapshot](https://github.com/caw1517/DCSRecorder/issues/21).
The bounded airborne snapshot control is accepted after both brake-extended and
gear-down first-visibility/held tests. The final section supersedes the progress
checkpoints below. Release and ground acceptance remain separate tasks.

## Prepared changes

- `object_probe.cpp` retains the sampled brake at the shared post-animation
  boundary for staged playback as well as the held diagnostic. Held startup
  refuses native tapes missing any supported appearance/engine group.
- The hold mission tries initialization during mission startup, retries when
  native readiness is absent, and logs the initial smoke command time. Readiness
  does not establish rendered smoke onset. It can check all 33 appearance
  channels against the first recorded sample on every held observation.
- `held-start/prepare.py --snapshot` uses a separate module and mission, requires
  all captured groups, and refuses a test source without initially deployed
  gear, extended brake, smoke ON and nonzero lights. This test-specific coverage
  requirement does not redefine valid ordinary recordings. Original pose,
  velocity and every recorded channel remain source-derived.
- The snapshot installer accepts only its fixed additive module/mission paths.
  No new playback controller has been installed yet.

The historical accepted changing-brake residual remains **0.010002** over
2,016 of 4,762 later reads. The source repair does not establish its live removal;
changing-brake, countdown and endpoint measurements still need evidence.

## Offline checks

Rebuilt `HornetHeldProbe`, `HornetWheelsTrial2930` and their relevant checks with
Visual Studio. All five selected CTest checks pass: held callback, complete
initial-state hold policy, mission lifecycle, presentation boundary and updated
build playback callback. The lifecycle fixture covers immediate and delayed
readiness, smoke once, incorrect snapshot state, missing aircraft, timeout and
controller mismatch/failure. The policy fixture uses non-default groups and
different later samples; it verifies that none advance during a hold.

The fresh hold package from the retained accepted recording passes installed
dependency, route and configuration checks. The snapshot mode correctly refuses
that recording's default initial brake before creating a package. This is not a
positive live non-default snapshot test. New hold DLL SHA-256:
`c4e9349c25d71c6186cb0cb4eae2f8d6ea748f2de845f07ae73b4af12b0eb871`.

## Next live step: acquire a suitable source

The old accepted final take has no nonzero-brake sample within the current
near-level staging limits; the closest bank is about 32 degrees. The latest
accepted updated-build take's closest sample is about 21 degrees. Neither was
edited to invent a level pose or non-default state.

Installed **041-Hornet-Snapshot-Capture.miz** after the user confirmed DCS closed.
It derives from the current complete version-seven practice mission and uses
the installed normal recorder. The mission starts at 105 m/s and turns on the
stock Hornet's exterior lights. The user controls gear, brake, smoke and flight,
then records 8–10 seconds starting nearly level with those states already set.
Keep canopy closed in flight. The original mission and installed controllers
were not replaced; installation used an exclusive new-file copy and verified its
SHA-256 `2e2b220726f27fd60f2375ac32ec136acef0406408b179f77e0dabdcbad66074`.
The package/receipt are retained locally under ignored `capture-package-v2/`.
Source configuration, installed dependencies/routes and the five initial light
commands were checked. The ordinary configuration validator requires lights OFF;
the dedicated capture fixture verifies the deliberate ON commands against the
installed Hornet definitions and both mission trigger representations.

After capture: inspect the actual first sample and save result, prepare/install
the separate snapshot hold, inspect first visibility and 30-second retention,
then retain native/mission logs and the user's visual/audio review. Observe
default flashes, relocation, pose blend, smoke onset and sound changes. Initial
startup samples are now logged before readiness too; do not discard failures as
warmup or claim native readiness proves the first rendered frame.

## Supported state and remaining coverage

Snapshot data comprises pose and recorded release velocity, gear/flaps/control
surfaces, brake, seven exterior-light arguments, canopy, seven wheel/strut/steering
arguments, nozzle/flame appearance, six native engine consumer values and the
measured white-smoke state. Native engine/smoke capture has its documented timing
alignment; it is not proof of perfectly simultaneous internal-system capture.
An airborne closed canopy and uncompressed wheels do not exercise non-default
canopy or ground wheel/strut initialization. Those still need appropriate source
and live coverage; their previous changing-state acceptance is only prior evidence.

Full cockpit systems, internal engine restoration and refueling-probe geometry
are not captured. Actual ground illumination/contact, countdown/release, parked
completion and restart retain their later acceptance tasks. Consult the existing
[capability matrix](../../../../docs/research/hornet-state-capabilities.md).

## Fresh sources received and brake snapshot installed

The user completed two normal recordings on the current DCS build:

- `20261001T033031Z-0001.csv`: 436 samples / 8.70 seconds, gear fully down,
  smoke ON and lights nonzero. Brake argument 21 is zero throughout despite the
  requested control input. Retained under `capture-gear-smoke-lights/`; this take
  is useful gear-state evidence but cannot validate a nonzero initial brake.
- `20261001T033224Z-0002.csv`: 317 samples / 6.32 seconds, gear up, brake 1.0
  throughout, smoke ON and nonzero navigation/formation lights. Initial pitch is
  3.319 degrees and up-axis tilt 4.823 degrees, within existing staging guards.
  Retained under `capture-brake/` with its first sample and source hash.

The test coverage gate now accepts **gear down OR brake extended**, together
with measured smoke ON/nonzero lights and every supported recording group.
These are two independent real captured configurations; no synthetic combined
state was invented, and no reason for the first take's zero brake is asserted.
This supersedes the earlier requirement to exercise both simultaneously.

Added a distinct `HornetSnapshotProbe` DLL identity so DCS cannot satisfy this
module's request with the already installed earlier hold controller. Six offline
checks pass, including the new DLL callback contract. The brake source's actual
package passed dependency/route/configuration checks and manifest validation.

After the user confirmed DCS closed, the additive installer installed all eleven
verified files for `DCSRecorder-Hornet-Snapshot-Test` and
**042-Hornet-Snapshot-Hold.miz**, and verified 1,103 existing files unchanged.
The original source and accepted normal runtime remain intact. The installation
receipt, mission and exact tape are under `brake-package/`. The new mission uses
the actual first sample and checks all 33 appearance channels during its hold.

Next: user observes the first visible frame and thirty-second hold, leaving
Active Pause unchanged, then exits normally. Preserve the resulting native and
mission logs before any repeat. Check brake, smoke onset, visual flash, relocation,
drift and engine sound. Live acceptance remains pending; this installation is
not completion of the snapshot task.

## Brake hold measured; held-smoke exception accepted

The user reviewed the brake snapshot and reported that everything looked great
except no smoke was visible. Both the saved take and the logged startup command
establish smoke ON; the command ran at mission time 0.000000. Its return does not
prove particle emission. The user then explicitly accepted no visible smoke
while held, provided it appears when playback resumes. That supersedes the
first-frame smoke-rendering requirement for held staging only. No cause (including
velocity-dependent emission) has been established. Release must still verify ON
emission and its transition timing in the next clock/release task.

Final logs after DCS closed are retained in `brake-live-complete/raw/`, with the
user's observation and requirement change in `review.json`. Reproduce the audit:

```
python experiments/efm-ownership/held-start/analyze.py experiments/efm-ownership/results/snapshot-2026-09-30/brake-live-complete --manifest experiments/efm-ownership/results/snapshot-2026-09-30/brake-package/manifest.json
```

The audit establishes 302 mission observations from 0 through 30.02 seconds,
zero sampled lead/player position drift, unchanged lead orientation, zero lead
velocity, replay time zero, and a moving witness (4,391.85 m displacement).
All 52,635 post-animation observations across 33 appearance channels match the
tape at logged precision, including the held nonzero brake (1.0). Later mission
reads have no drift and a maximum source difference of 4.02e-10. All 69,058 valid
engine overrides across the six channels match the tape; 1,594 engine-index-zero
queries pass through. The 1,595 native pose writes have maximum float position
rounding of 0.013499 m, with no corresponding mission-pose drift. One create and
one destroy were logged, with the previously observed guarded destruction status.
These are bounded measurements, not new product-wide tolerances or changing-brake
acceptance. The historical changing-brake residual is still preserved.

The smoke evidence checker went red for the user's no-smoke report. It now
reports **DEFERRED**, not rendered success, under the explicit revised criterion.
No smoke workaround was installed and no speculative cause was treated as proven.

Prepared the gear-down snapshot from the first real take. After DCS was closed,
`held-start/Switch-Snapshot.ps1` verified the existing diagnostic against its
previous manifest, backed up its three changing files, and replaced only tape,
metadata and mission. The controller DLL is identical. Package validators pass;
the switch receipt and previous files are retained in `gear-package/`.
**042-Hornet-Snapshot-Hold.miz now runs the gear-down take**, with zero recorded
brake, matching lights/surfaces/engine state and recorded smoke ON. The next live
check is its first visibility and 30-second hold. The task remains open.

## Gear-down hold accepted; snapshot task complete

The user reported **“Looked great”** after the requested first-visible gear-down
and 30-second hold check. Logs for PID 10496 are retained in `gear-live/raw/`,
with the exact user review and its scope in `gear-live/review.json`.
The same analyzer, using `gear-package/manifest.json`, verifies the installed
mission, native DLL and tape against the prepared manifest before reporting.

| Measurement | Brake hold | Gear-down hold |
| --- | --- | --- |
| Mission observation window | 0–30.02 s, 302 samples | 0–30.02 s, 302 samples |
| Sampled pose/orientation drift | 0 | 0 |
| Playback clock / lead velocity | 0 / 0 | 0 / 0 |
| Appearance observations after animation | 52,635 across 33 channels | 52,074 across 33 channels |
| Maximum post-animation difference | 0 at logged precision | 0 at logged precision |
| Later mission appearance drift | 0 | 0 |
| Maximum later appearance source difference | 4.02e-10 | 3.42e-10 |
| Matching valid engine getter overrides | 69,058 across six channels | 68,327 across six channels |
| Native float position rounding maximum | 0.013499 m | 0.021691 m |
| Mission pose difference from original first sample | 0 at logged precision | 0 at logged precision |
| Object create / destroy | 1 / 1 | 1 / 1 |

Both runs start from actual recorded complete version-seven snapshots, preserve
the original world pose and saved release velocity, hold replay time at zero,
and retain the complete supported recorded appearance/observable-engine state.
Both use non-default lights and distinct non-default gear/brake/surface states.
User review supplies the first-visible visual evidence; there is no frame-by-frame
video audit. The motion/wheel/engine values are not inferred from appearance.

This completes **Initialize the complete supported playback snapshot** for the
current bounded airborne implementation step, with the explicitly accepted
held-smoke exception. First-visible state, held inspection and post-animation
retention are now supported by live evidence, not just package/offline checks.
No normal companion module was replaced. The isolated snapshot module remains
installed with the gear-down take for subsequent integration work.

Remaining work is owned by the later tasks: one countdown/release clock (including
restored velocity and smoke-ON emission), hot-ground initial state/contact and
first movement, changing-state/endpoint retention, ground illumination, restart,
measured product tolerances and complete workflow acceptance. Non-default canopy,
afterburner flames, wheel compression/steering and every possible light state
were not separately exercised at startup in these two runs; their recorded
values were nevertheless present and retained. Earlier changing-channel evidence
is not relabeled as new initial-state evidence. Full cockpit/internal engine
restoration and refueling-probe geometry remain unavailable. The historical
0.010002 changing-brake residual is preserved for the later fidelity check.
