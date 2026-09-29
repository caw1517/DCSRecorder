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
remains to be reviewed. Version-three capture now adds measured native engine
parameters and nozzle/flame state. The isolated combined sound/appearance test
and automatic completion are accepted by the user. The new normal recording and
recorded-motion integration passes offline checks and the user successfully
recorded and replayed the 31.98-second **Test** flight through the app, reaching
automatic completion. See the [engine workflow record](../../experiments/efm-ownership/results/engine-workflow-2026-09-27/README.md).
Version-four recording and white-smoke playback are now accepted through the
normal app workflow. A minor stock-versus-playback sound bass/impact difference
remains an observation to investigate, not a diagnosed parameter or mixer fault.

### Remaining before closing this issue

- Exterior lights: refuel activation and ground illumination remain unverified.
  The user's normal lights-off workflow is accepted, with the formation startup
  overwrite corrected in post-animation traces. Older recordings retain off-only behavior.
- Wheel rotation and suspension compression: capture/replay with rotation wrap
  handling, and coordinate visible ground-state validation with ground-start,
  flight-envelope and physics work. Gear deployment alone is already accepted.
- Close the remaining numerical evidence review and run a combined regression
  as the new channels are added; preserve accepted motion, engines, surfaces,
  smoke, initial state, lifecycle behavior and legacy recording compatibility.

The user explicitly chose **white smoke only for V1** and deferred both
[sound depth refinement](https://github.com/caw1517/DCSRecorder/issues/12) and
[multicolor smoke](https://github.com/caw1517/DCSRecorder/issues/13) to **V2**.
Neither blocks this V1 issue. Depletion/damage behavior remains unverified and
must not be inferred from the accepted ordinary smoke cycle. Ground dynamics,
broader aircraft registrations and layered playback retain their separate gates.

Exterior lights have passed the user's normal-workflow review. The separate
[nighttime light diagnostic](../../experiments/efm-ownership/lights-prototype/README.md)
passed stock-aircraft observation: the user saw all four tested light groups
respond, and 3,362 samples cover eleven phases at 50 Hz. A separate SDK-only
captured-light playback mission is visually accepted and completed normally.
Later reads confirm navigation/strobe/landing values; formation has a measured
half-second startup overwrite to address during integration. Refuel activation
and landing-light ground illumination are not yet established. See the
[light evidence checkpoint](../../experiments/efm-ownership/results/lights-2026-09-28/README.md).
The [normal version-five integration](../../experiments/efm-ownership/results/lights-integration-2026-09-28/README.md)
is now installed after 27 companion tests and seven native/lifecycle checks.
It records lights with optional white smoke, uses the common native playback
clock, and reapplies lights at the existing shared animation boundary. The user
accepted normal lights-off playback; two full runs show all 75,124 post-animation
light values matching, including correction of 50 native formation overwrites.
Independent later mission light telemetry was absent due to omitted config
flags; that packaging omission is corrected and regression-tested for future
missions. Canopy is now accepted. A separate parked
[canopy diagnostic](../../experiments/efm-ownership/canopy-prototype/README.md)
has passed stock-aircraft capture and visual review: 2,364 samples confirm
exterior argument 38 from closed (0) through steady partial holds to fully open
(about 0.9). The separate captured-canopy playback is visually accepted, with
2,760 later mission reads matching and no between-call overwrites. Normal
integration also passed the user's ordinary closed-canopy app run: 363 native
updates and 804 later mission reads match, with normal completion. Wheel rotation
and suspension compression are next. See the
[canopy evidence](../../experiments/efm-ownership/results/canopy-2026-09-28/README.md).

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
| Gear compression / wheels | Compression 1/6/4 and rotation 101/103/102 respond in taxi captures; the normal airborne take records zero compression and stationary phase one. Period-one interpolation passes all real samples and 194 wraps. | Isolated changing playback and normal version-seven app workflow accepted. Normal playback has 1,612 matching native updates and 1,613 matching playing/completion reads, with user visual acceptance and normal removal. | Pre-release raw wheel phase zero differs from recorded one at the equivalent rotation endpoint. Arbitrary initial ground states, reverse/high-speed rotation and contact remain pending. See [isolated evidence](../../experiments/efm-ownership/results/wheels-2026-09-28/README.md) and [normal integration](../../experiments/efm-ownership/results/wheels-integration-2026-09-29/README.md). |
| Nose-wheel steering | Argument 2 reaches +0.726780 after the left marker, near zero during center, and -0.735133 after right; 17/18 are rudder comparators. | Accepted visually/numerically in the isolated changing test and normal version-seven airborne app run (centered steering). | Markers precede movement; no angle is inferred from trajectory or converted to degrees. Ground-path playback remains separate. |
| Canopy opening / closing | Installed gauge connects exterior 38 to cockpit 181. Accepted parked capture measures closed 0, fully open about 0.9, transitions and stable partial holds. | Isolated changing-canopy replay accepted; 2,760 later reads match. Normal closed-canopy workflow accepted; 363 native updates and 804 later reads match with completion. | Version-six capture and tape-version-five playback accepted within the demonstrated scope. Initial position and transitions are preserved; opening animation does not establish jettison or internal cockpit-system replay. |
| Leading-edge flaps | Channels 13/14 respond in live capture; descriptor labels right/left. | Isolated replay visually accepted. | Version-two combined motion/state playback visually accepted by the user; integrated numerical/lifecycle checks remain. |
| Trailing-edge flaps | Channels 9/10 respond in live capture, including negative values during roll. | Isolated replay visually accepted; signed state preserved. | Version-two combined motion/state playback visually accepted by the user; integrated numerical/lifecycle checks remain. |
| Ailerons / stabilators / rudders | Live capture confirms channels 11/12, 15/16, 17/18 respond with coupled signed motion. | Isolated surfaces visually accepted; post-animation stabilator retention verified numerically. | Version-two combined motion/state playback visually accepted by the user; integrated numerical/lifecycle checks remain. |
| Exterior lights | Live marked capture and user observation confirm formation 88; navigation 190/191/192; pulsing strobe 193; landing/taxi 210. Refuel 212 remains unexercised. | Isolated changing-light replay accepted. Normal lights-off replay accepted across two full runs; all post-animation light values match, including repaired formation startup overwrites. | Normal version-five workflow accepted for the user's usual configuration. Independent later mission reads were absent; forwarding is now fixed for future missions. Refuel activation and ground illumination remain unverified. |
| Demonstration smoke | Dedicated SMK station 10 carries `INV-SMOKE-*`. Native flag capture passed in a version-four app flight: 2,647 samples / 52.92 seconds, 0..12 ms capture delay, OFF/ON/OFF and white-generator metadata preserved. | User accepted recorded white-smoke playback. Requests followed recorded ON/OFF by at most 14 ms and the mission completed normally. | Normal capture/library/playback accepted for white smoke. Other colors are unverified. See the [accepted actuator and capture investigation](../../experiments/efm-ownership/results/smoke-control-2026-09-27/README.md). |
| Engine RPM, left/right | Read-only native helper captures core/fan RPM and both power getters with player/timing checks. Core RPM agrees with Export. | Guarded per-object native getters deliver the measured values to DCS consumers. | Combined sound/appearance and normal version-three capture/playback accepted. Full integrated trace audit remains distinct from visual/audio acceptance. |
| Nozzle opening | Marked live capture supports left argument 90 and right 89. | Post-animation writes share the native sound playback clock. | Combined sound/visual test and normal recorded-motion integration accepted. |
| Afterburner appearance | Independent marked phases support left argument 29 and right 28. | Recorded values are reapplied after animation on the common clock. | Combined test and normal recorded-motion integration accepted; no guessed RPM threshold. |
| Engine / afterburner sound | Native core/fan/thrust/power values are measured; values above one retained. | Stock DCS renderer consumes overridden native getters. Core RPM alone was insufficient. | Power-dependent sound accepted in normal playback; no custom audio samples. User notes slightly less bass/impact than stock/player aircraft. Cause unconfirmed; matched-listener comparison pending as a minor refinement. |

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

The [first live engine diagnostic](../../experiments/efm-ownership/results/engine-capture-2026-09-27/README.md)
retained 1,745 mission samples and all phase markers. Arguments 89/90 respond
asymmetrically, and 28/29 respond in afterburner-marked phases; their exact visual
semantics remain candidates. Every Export reading was rejected by an identity
assertion before engine measurement. The corrected observation hook is installed:
it records actual identity fields and available engine values, while the analyzer
continues to flag unverified identity. A short baseline recheck is next; RPM,
temperature, fuel-flow availability and clock alignment are not yet live-verified.

The subsequent short recheck verified all six engine readings in 441 paired
samples. Export names/IDs differ from mission identity in this setup, but the
time-matched trajectories agree within 0.947 mm across 440 in-range comparisons;
Export timestamps follow by 1..12 ms. The bounded diagnostic association screen
now uses actual type, stable Export identity and time-matched trajectory instead
of name/ID equality. Independent throttle transitions still need a full combined
capture before playback-actuator work; this verifies the engine feed, not engine
effects or sound reproduction.

The full marked repeat then passed with 979 paired samples over 48.9 seconds.
Independent left/right fuel-flow responses support candidate left 90/29 and
right 89/28 nozzle/effect pairs. A separate four-channel post-animation actuator
and **DCSRecorder-Engine-Appearance-Playback.miz** are installed for live comparison.
The subsequent [live playback result](../../experiments/efm-ownership/results/engine-playback-2026-09-27/README.md)
accepts nozzle/flame rendering, with all four immediate readbacks exact and later
mission errors below 5.1e-10. Sound remained idle-like. A separate read-only
parameter-call probe is installed to measure ordinary EFM getter reachability;
no sound actuator is established. Recorded-motion integration remains pending.

The [live callback result](../../experiments/efm-ownership/results/engine-sound-2026-09-27/README.md)
subsequently found zero getter queries during 41.8 seconds despite verified load,
creation and destruction. The next experiment explicitly registers a separate
spatial sounder and alternates installed engine/afterburner samples for 12 seconds,
then silence/removal. This tests a different control interface and deliberately
does not claim synchronization with the appearance tape or faithful engine mixing.
