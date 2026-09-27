# Hornet capture and playback capability matrix

Inspected 27 September 2026 UTC for [Complete single-aircraft visual and engine-state fidelity](https://github.com/caw1517/DCSRecorder/issues/6).
Source baseline: `ee3b1d34cdba660b17f5ce3ae67310cdd73f9c5a`.
Installed DCS: `2.9.29.27468`, verified in `D:/DCS World/autoupdate.cfg`.
The matrix began as an interface inspection. A subsequent
[live stock-aircraft capture](../../experiments/efm-ownership/results/exterior-state-2026-09-27/README.md)
confirmed readable responses for the selected exterior channels. No new playback fidelity result is claimed.

## Result

The present recording/playback pipeline carries motion and speed brake only.
The two RPM columns in the CSV are empty placeholders; conversion does not read
them into the native tape. Gear, flaps, surfaces, lights, smoke and engine state
cannot be recovered from those recordings. Preserve the originals.

The installed object SDK exposes bounded animation-array reads and individual
animation writes. This is a credible route for exterior animation. It exposes
no engine-state, sound or particle-emitter setter. An argument readback is not
proof that an effect renders, that sound follows it, or that ground physics changes.

## Capability matrix

“Candidate” means an installed interface or descriptor supports investigation;
it does not mean the channel has passed a live capture/playback comparison.
Argument numbers below are exterior model arguments, not cockpit controls.

| State | Capture evidence | Playback evidence | Current status / missing evidence |
| --- | --- | --- | --- |
| Type and livery | Mission recorder stores `getTypeName()` and mission livery. | Staged packager rejects types other than `FA-18C_hornet` and liveries other than `Blue Angels Jet Team`. | Supported bounded identity; no silent substitution. F-16/F-15 registrations remain unsupported. |
| Speed brake | Mission recorder reads argument 21 each sample. | Tape includes brake; `hornet_appearance::apply` writes 21 and checks immediate readback. | Existing implemented channel. Retain it as the control in new comparisons. |
| Gear | Hornet FM configuration identifies strut deployment arguments 0 (nose), 5 (left), 3 (right). Mission argument reads are the candidate capture route. | SDK can write individual arguments; these arguments are not currently written by the appearance adapter. | Not recorded/replayed. Verify extension direction, doors and transition timing; animated deployment does not prove ground contact. |
| Gear compression / wheels | FM configuration identifies compression 1/6/4 and rotation 101/103/102 in nose/left/right order. | Same candidate argument route. | Not recorded/replayed. Rotation wrap and contact behavior need separate handling; do not interpolate wrapped rotations naively. |
| Canopy opening / closing | Explicitly requested by the user; no validated Hornet exterior mapping established in this inspection. | Candidate argument route, pending mapping and live test. | Not captured/replayed. Include the initial canopy position and transitions; opening animation does not establish jettison or internal cockpit-system replay. |
| Leading-edge flaps | Hornet descriptor explicitly labels 13 right and 14 left. | Candidate argument writes. | Not recorded/replayed. Validate range and actual rendered response under stock flight-control scheduling. |
| Trailing-edge flaps | Descriptor's `ColdStartDefaultControls` labels keys 9/10 as flaps. | Candidate argument writes. | Not recorded/replayed. Controlled stock-aircraft observation must confirm left/right meaning, ranges and motion. |
| Ailerons / elevators / rudders | Descriptor's `ColdStartDefaultControls` identifies aileron keys 11/12, elevators 15/16, rudders 17/18. Aileron comments contain inconsistent bracketed numbers, so use keys as candidates and verify visually. | Candidate argument writes. | Not recorded/replayed. Verify sign, range, left/right meaning and coupled surface behavior; retain signed values. |
| Exterior lights | Descriptor identifies formation 88; navigation 190/191/192; strobe 193; landing/taxi 210; refuel 212. | Existing adapter writes every listed channel to zero on each invocation. | Off-only behavior. Capture brightness and transitions; validate strobe phase and actual illumination independently of immediate readback. |
| Demonstration smoke | Hornet descriptor lists selectable `INV-SMOKE-*` stores. This establishes configuration availability, not an emitter-state capture API. | No verified emitter setter found in inspected object SDK. | Unsupported in current pipeline. Determine actual source loadout, color, emitter enable and timing; do not confuse gun smoke with demonstration smoke. |
| Engine RPM, left/right | Installed `Scripts/Export.lua` documents `LoGetEngineInfo().RPM.left/right` as percentages. Current mission-only capture does not use it. | Object SDK has no RPM setter. Ordinary EFM callbacks expose RPM-related parameters, but their execution on this unoccupied object is not established. | Capture candidate in Export context; not wired or tested. Need clock/aircraft identity alignment with mission samples and an independently proven playback actuator. |
| Nozzle opening | Hornet descriptor explicitly labels argument 89 nozzle; adjacent 90 is unlabeled. | Candidate animation writes. | Not recorded/replayed. Verify both engines' mappings and ranges; nozzle pose is not an afterburner-state measurement. |
| Afterburner appearance | Descriptor supplies per-engine effect texture/configuration, not measured on/off or intensity data. No verified captured channel established here. | No verified effect-state writer on the playback object. | Unsupported in current pipeline. Establish independent per-engine capture and actuation; do not derive afterburner from trajectory or a guessed RPM threshold. |
| Engine / afterburner sound | No sound-state capture exists. Export RPM/temperature/fuel flow may be useful measurements, not a sound recording. | No sound-state writer in inspected object SDK. EFM sound/power parameters are a separate interface with unproven ownership here. | Unsupported. Needs a separate audible comparison with matched camera/listener geometry; animation success cannot close this row. |

## Primary evidence

Repository files (relative links resolve at this report's revision):

- [Mission sampler](../../experiments/efm-ownership/record_flight_mission.lua): `r.sample` reads pose, velocity and argument 21; emitted rows append two empty fields.
- [Durable sink](../../companion/recording_sink.lua): fixed version-one CSV columns, including the two RPM placeholders.
- [Converter](../../experiments/efm-ownership/recorded_flight.py): exact version/column checks; native samples contain only motion and brake.
- [Native tape reader](../../experiments/efm-ownership/recorded_path.h): `DCSREC_PLAYBACK_V1`, `Sample` and `Path::load`.
- [Appearance adapter](../../experiments/efm-ownership/hornet_appearance.h): identity/bounds guards, light suppression, argument write/readback.
- [Staged packager](../../experiments/efm-ownership/prepare_staged_playback.py): explicit type/livery/build restrictions and source-copy preservation.
- [AI ownership experiment](../../experiments/efm-ownership/results/ai-2026-09-23/README.md) and [object lifecycle experiment](../../experiments/efm-ownership/results/object-lifecycle-2026-09-23/README.md): historical evidence on DCS 2.9.29.27278 separates ordinary EFM execution from object callbacks. It is not fresh engine-state validation on the current build.

Installed primary sources, retained locally rather than copied into the repository:

- `D:/DCS World/API/include/ed_object_access.h`: complete `ed_object_api_entry` interface, including array size and per-argument setters.
- `D:/DCS World/CoreMods/aircraft/FA-18C/FA-18C_hornet.lua`: `net_animation` (around line 797), `ColdStartDefaultControls` (around 1173), `lights_data` (around 1120), `engines_nozzles` (around 583), smoke-store declarations (around 420).
- `D:/DCS World/Mods/aircraft/FA-18C/FM/config.lua`: gear argument mappings around lines 89, 140 and 191.
- `D:/DCS World/Scripts/Export.lua`: `LoGetEngineInfo` documentation around line 462; RPM, temperature and fuel consumption fields. This runs in a different context from mission scripting.
- `D:/DCS World/API/include/FM/wHumanCustomPhysicsAPI.h`: engine parameter documentation around line 392. Availability in this header is not evidence that this playback object's engine consumes these values.

## Proposed first experiment

The user selected gear/flaps/control surfaces first, keeping speed brake as a regression
control. Confirm the descriptor's candidate mappings by observing a stock
Hornet before writing them. Use one near-level airborne take,
within the existing speed envelope, with timestamped segments for each control
change. Include non-default supported state at the first sample. Confirm candidate
values against the stock aircraft's visible surface movement before replay.

For the replay, compare source values, requested writes, immediate readback,
next-step readback and external-view evidence at the same playback timestamps.
This distinguishes accepted writes from values overwritten later by DCS. Exercise
pause, countdown, first-frame activation, completion and restart. Retain motion
trace and hook-restoration checks; compare against the accepted motion baseline.
Record actual channel and timing errors before agreeing product tolerances.

Keep engine/afterburner/sound as a separate evidence gate. Gear animation does
not enable ground starts by itself; coordinate contact and initialization with
the existing ground-state and flight-envelope tickets.

## Proposed recording contract (not yet implemented or accepted)

- Preserve version-one source files byte for byte and retain legacy playback.
  Missing version-one channels mean **not captured**, never “off” or zero RPM.
- Use a new recording/native-tape version for added state, with an explicit
  aircraft profile, channel identifiers, ranges and interpolation rules. Unknown
  versions, unsupported profiles and invalid values fail clearly.
- Capture a full supported-state snapshot at the same sample time as initial
  pose; keep that state through staging and apply it on the shared playback clock.
- Interpolate validated continuous channels; hold discrete states until their
  recorded transition. Do not infer controls or engine state from motion.
- If Export capture is needed, prove identity and clock alignment with mission
  capture before combining streams. A failed channel is unavailable, not zero.
- Keep playback state mappings specific to tested aircraft/module variants.
  Reuse motion playback without claiming untested aircraft support.

## Live capture and remaining gate

The user completed the exterior diagnostic: 2,612 consecutive finite samples
over 130.55 seconds, all six control markers, 20 Hz cadence and explicit stop.
The [result](../../experiments/efm-ownership/results/exterior-state-2026-09-27/README.md)
supports readable gear/flap/surface/brake channels. Coupled motion and negative
flap values require per-channel recorded values, not reconstructed pilot inputs
or blanket 0..1 clamping. The matrix's playback-status columns remain unchanged.
An isolated SDK actuator has since been tested. The user found the other tested
exterior channels visually satisfactory, but stabilators flickered with almost
no travel. [Live evidence and the timing experiment](../../experiments/efm-ownership/results/exterior-playback-2026-09-27/README.md)
show exact immediate writes followed by overwritten stabilator values. Smaller
overwrites occur on some visually accepted channels too. These prototype results
do not change the production capability claims or establish effects/sound support.
The [post-physics comparison](../../experiments/efm-ownership/results/stabilator-poststep-2026-09-27/README.md)
also failed visibly and numerically. Installed-build analysis found a later update
that writes both stabilators. A separate post-animation experiment is installed;
its offline checks pass, with live retention/rendering still pending.
The parent visual/engine-state ticket remains open. The user selected exterior
animation first; the proposed recording contract remains a proposal. The
[read-only diagnostic prototype](../../experiments/efm-ownership/state-prototype/README.md)
collects the stock-aircraft observations needed before playback implementation.

## Confirmed remaining exterior scope

Fix stabilator retention first, then integrate the verified surface group with
the recording clock. Preserve these user-requested requirements for subsequent
groups: suspension compression and wheel spin (ground/touchdown tests), separate
left/right nozzle motion with engine/afterburner appearance and sound, canopy
state, demonstration-smoke emitter/color/timing, and exterior-light state and
brightness. Suspension visuals must agree with contact physics; wheel rotation
needs wrap-aware treatment. Lights have argument-driven state/brightness in the
installed descriptor, while smoke also requires an emitter/effect path. These
are in-scope work, not all proven animation writes and not removed by doing the
stabilator repair first.
