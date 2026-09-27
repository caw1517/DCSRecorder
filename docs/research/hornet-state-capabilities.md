# Hornet capture and playback capability matrix

Inspected 27 September 2026 UTC for [Complete single-aircraft visual and engine-state fidelity](https://github.com/caw1517/DCSRecorder/issues/6).
Source baseline: `ee3b1d34cdba660b17f5ce3ae67310cdd73f9c5a`.
Installed DCS: `2.9.29.27468`, verified in `D:/DCS World/autoupdate.cfg`.
The matrix began as an interface inspection. A subsequent
[live stock-aircraft capture](../../experiments/efm-ownership/results/exterior-state-2026-09-27/README.md)
confirmed readable responses for the selected exterior channels. The subsequent
[isolated stabilator replay](../../experiments/efm-ownership/results/stabilator-animation-2026-09-27/README.md)
passed visual review and retained-trace checks. The matrix below describes the
recording/playback implementation and its validation status. The integrated
exterior controller has now passed the user's synchronized visual comparison.
See the [integrated result](../../experiments/efm-ownership/results/exterior-integration-2026-09-27/README.md).

## Result

Legacy version-one recordings carry motion and speed brake only and remain
unchanged. Version-two recordings add the thirteen gear/flap/control-surface
channels under `hornet-exterior-v1`, on the same sample clock. The integrated
controller and companion path pass offline tests and the user visually accepted
combined motion/surface playback. Integrated numerical and lifecycle evidence
remains to be reviewed. RPM fields remain empty, and lights/smoke/engine state are not captured.

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
| Gear | Live capture confirmed arguments 0 (nose), 5 (left), 3 (right). | Isolated SDK replay visually accepted. | Version-two combined motion/state playback visually accepted by the user; integrated numerical/lifecycle checks remain. Animated deployment does not prove ground contact. |
| Gear compression / wheels | FM configuration identifies compression 1/6/4 and rotation 101/103/102 in nose/left/right order. | Same candidate argument route. | Not recorded/replayed. Rotation wrap and contact behavior need separate handling; do not interpolate wrapped rotations naively. |
| Canopy opening / closing | Explicitly requested by the user; no validated Hornet exterior mapping established in this inspection. | Candidate argument route, pending mapping and live test. | Not captured/replayed. Include the initial canopy position and transitions; opening animation does not establish jettison or internal cockpit-system replay. |
| Leading-edge flaps | Channels 13/14 respond in live capture; descriptor labels right/left. | Isolated replay visually accepted. | Version-two combined motion/state playback visually accepted by the user; integrated numerical/lifecycle checks remain. |
| Trailing-edge flaps | Channels 9/10 respond in live capture, including negative values during roll. | Isolated replay visually accepted; signed state preserved. | Version-two combined motion/state playback visually accepted by the user; integrated numerical/lifecycle checks remain. |
| Ailerons / stabilators / rudders | Live capture confirms channels 11/12, 15/16, 17/18 respond with coupled signed motion. | Isolated surfaces visually accepted; post-animation stabilator retention verified numerically. | Version-two combined motion/state playback visually accepted by the user; integrated numerical/lifecycle checks remain. |
| Exterior lights | Descriptor identifies formation 88; navigation 190/191/192; strobe 193; landing/taxi 210; refuel 212. | Existing adapter writes every listed channel to zero on each invocation. | Off-only behavior. Capture brightness and transitions; validate strobe phase and actual illumination independently of immediate readback. |
| Demonstration smoke | Hornet descriptor lists selectable `INV-SMOKE-*` stores. This establishes configuration availability, not an emitter-state capture API. | No verified emitter setter found in inspected object SDK. | Unsupported in current pipeline. Determine actual source loadout, color, emitter enable and timing; do not confuse gun smoke with demonstration smoke. |
| Engine RPM, left/right | Installed `Scripts/Export.lua` documents `LoGetEngineInfo().RPM.left/right` as percentages. `API/Sim_ControlAPI.md` also exposes it through `Export` in GUI hooks. | Object SDK has no RPM setter. Ordinary EFM callbacks expose RPM-related parameters, but their execution on this unoccupied object is not established. | Separate read-only engine diagnostic prepared and installed; live API availability and mission/Export clock/identity alignment pending. Production capture remains unchanged; playback actuator unproven. |
| Nozzle opening | Hornet descriptor explicitly labels argument 89 nozzle; adjacent 90 is unlabeled. | Candidate animation writes. | Not recorded/replayed. Verify both engines' mappings and ranges; nozzle pose is not an afterburner-state measurement. |
| Afterburner appearance | Descriptor supplies per-engine effect texture/configuration, not measured on/off or intensity data. No verified captured channel established here. | No verified effect-state writer on the playback object. | Unsupported in current pipeline. Establish independent per-engine capture and actuation; do not derive afterburner from trajectory or a guessed RPM threshold. |
| Engine / afterburner sound | No sound-state capture exists. Export RPM/temperature/fuel flow may be useful measurements, not a sound recording. | No sound-state writer in inspected object SDK. EFM sound/power parameters are a separate interface with unproven ownership here. | Unsupported. Needs a separate audible comparison with matched camera/listener geometry; animation success cannot close this row. |

## Primary evidence

Repository files (relative links resolve at this report's revision):

- [Mission sampler](../../experiments/efm-ownership/record_flight_mission.lua): one callback samples pose, velocity, brake and thirteen exterior arguments; RPM fields remain empty.
- [Durable sink](../../companion/recording_sink.lua): version-one and version-two CSV columns, including the two RPM placeholders.
- [Converter](../../experiments/efm-ownership/recorded_flight.py): exact version/profile/column checks; version two adds signed exterior values to native samples.
- [Native tape reader](../../experiments/efm-ownership/recorded_path.h): `DCSREC_PLAYBACK_V1`/`V2`, `Sample` and `Path::load`.
- [Appearance adapter](../../experiments/efm-ownership/hornet_appearance.h): identity/bounds guards, light suppression, brake and exterior argument write/readback.
- [Staged packager](../../experiments/efm-ownership/prepare_staged_playback.py): explicit type/livery/build restrictions and source-copy preservation.
- [AI ownership experiment](../../experiments/efm-ownership/results/ai-2026-09-23/README.md) and [object lifecycle experiment](../../experiments/efm-ownership/results/object-lifecycle-2026-09-23/README.md): historical evidence on DCS 2.9.29.27278 separates ordinary EFM execution from object callbacks. It is not fresh engine-state validation on the current build.

Installed primary sources, retained locally rather than copied into the repository:

- `D:/DCS World/API/include/ed_object_access.h`: complete `ed_object_api_entry` interface, including array size and per-argument setters.
- `D:/DCS World/CoreMods/aircraft/FA-18C/FA-18C_hornet.lua`: `net_animation` (around line 797), `ColdStartDefaultControls` (around 1173), `lights_data` (around 1120), `engines_nozzles` (around 583), smoke-store declarations (around 420).
- `D:/DCS World/Mods/aircraft/FA-18C/FM/config.lua`: gear argument mappings around lines 89, 140 and 191.
- `D:/DCS World/Scripts/Export.lua`: `LoGetEngineInfo` documentation around line 462; RPM, temperature and fuel consumption fields. This runs in a different context from mission scripting.
- `D:/DCS World/API/Sim_ControlAPI.md`: LuaExport API in GUI hooks, including engine info, model time and ownship identity/position. This permits a separate read-only diagnostic without changing Export.lua.
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

## Recording contract (version-two exterior subset implemented)

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
that writes both stabilators. The separate post-animation experiment then
[passed live](../../experiments/efm-ownership/results/stabilator-animation-2026-09-27/README.md):
the user accepted the appearance and both channels retained the requested values
in later mission reads. Interrupted destruction released ownership correctly;
automatic completion/hold remains for the integrated test.
The parent visual/engine-state ticket remains open. The user selected exterior
animation first; the version-two exterior subset of the recording contract is
implemented and visually accepted in combined playback. Engine capture remains
unimplemented. The
[read-only diagnostic prototype](../../experiments/efm-ownership/state-prototype/README.md)
collects the stock-aircraft observations needed before playback implementation.

## Confirmed remaining exterior scope

The surface group is integrated with the recording clock and visually accepted. Preserve these user-requested requirements for subsequent
groups: suspension compression and wheel spin (ground/touchdown tests), separate
left/right nozzle motion with engine/afterburner appearance and sound, canopy
state, demonstration-smoke emitter/color/timing, and exterior-light state and
brightness. Suspension visuals must agree with contact physics; wheel rotation
needs wrap-aware treatment. Lights have argument-driven state/brightness in the
installed descriptor, while smoke also requires an emitter/effect path. These
are in-scope work, not all proven animation writes and not removed by doing the
stabilator repair first.

## Engine observation checkpoint

After acceptance of the fresh application gear workflow, prepared the separate
[engine diagnostic](../../experiments/efm-ownership/engine-prototype/README.md).
It samples candidate nozzle/control arguments and mission identity/time/position,
then measures left/right RPM, temperature and fuel flow through a GUI hook with
its own Export timestamps and identity. Log delivery does not imply simultaneous
sampling; the analyzer reports actual delays and positional separation and flags
unavailable data. No channel is declared an afterburner measurement based on RPM
or nozzle position alone.

The installed mission and hook pass offline capture/alignment checks with
synthetic data, including independent engines, pause/stop, unavailable API,
wrong ownship, delayed samples and missing/duplicate rows. Installed DCS mission
validators pass; eight protected existing files match their pre-install hashes.
Live capture, left/right nozzle mapping, effects and audible comparison remain
pending. The production recording schema and accepted playback actuator are
unchanged.
