# F/A-18C aircraft and livery prototype

The current test is the [positive-g left roll](dcs-hornet-left-roll.md).
The single-turn profile documented below is the preserved, user-validated
baseline. Its archived DLL must accompany its mission to reproduce that test;
the currently installed Hornet DLL runs the roll path.

Prepared 2026-09-26. DCS 2.9.29.27278. First Hornet flight succeeded;
the user confirmed the clean exterior and steady 2.5 g turn worked well.
The user confirmed the revised six-second roll-in worked great. The installed
mission, DLL and latest motion log are preserved in
`experiments/efm-ownership/results/hornet-validated-2026-09-26/`.

The user reported successful flight with unwanted pylons, exterior lights
and a deployed playback speed brake. Prior-flight evidence is archived in
`experiments/efm-ownership/results/hornet-first-flight-2026-09-26/`.
The new mission explicitly removes all five removable pylons on both jets,
initializes the player's four exterior-light controls off, and holds the
playback aircraft's speed brake and exterior-light arguments at zero using
the documented object SDK. The user confirmed these exterior changes worked well.

The SDK writes apply only in the Hornet build, only to the experiment's
runtime object ID, and only with a complete argument view. Readback status
is recorded in the object log. `HORNET_APPEARANCE` mission telemetry samples
both aircraft's speed brake, lights and removable-pylon arguments.
The user confirmed the stowed speed brake on this cloned Hornet;
argument 21 is held at zero. Light and removable
pylon mappings come from the installed Hornet descriptor. These cosmetic
defaults continue after motion release, so release tests motion ownership.

Future recorded-flight playback must capture and replay the source jet's
speed-brake state, along with its aircraft and livery. Holding it stowed is
a temporary prototype default, not the eventual recording behavior.

Loading-screen repair: [missing datalink dependency](../../experiments/efm-ownership/results/hornet-load-2026-09-26/README.md).
The prototype now packages the stock relative Datalinks directory alongside
its copied descriptor. The actual editor default-initialization call
reproduced the reported Lua exception before the fix and passes after it.
The subsequent successful flight confirms this mission-load repair.

The next load exposed an all-unlocked-route timing error. Both routes now
anchor their first waypoint at ETA zero and calculate later ETAs from the
Hornet speed. Packaging runs the installed DCS route-timing validator;
both original errors were reproduced and both corrected routes pass.

Module-load repair: the first mission incorrectly used `FA-18C` as its
required plugin ID. DCS declares the installed player module as `F/A-18C`;
the loader looks up dependency values in the enabled/registered plugin
tables. Corrected both dependency key and value to `F/A-18C`. Packaging now
runs `verify_hornet_requirements.lua`, which extracts the installed loader
predicate and official plugin ID. It reproduced the rejection before the
fix and passed afterward, assuming the user's confirmed enabled module.
This regression checks metadata, not live entitlement or registration.
Archive comparison confirmed that only this dependency entry changed.
The repaired mission was reinstalled; no DLL or aircraft registration
changes were needed. The subsequent flight successfully loaded the mission.

## User-requested sequence

Test these separately, evaluating each result before preparing the next:

1. F/A-18C appearance and livery, nominal 400 KIAS. Now refining appearance
   and replacing the first climbing turn with a level 2.5 g 180-degree turn.
2. A more complex route, such as right turn, level segment, left turn.
3. The user's requested roll: 400 KIAS; gradual pull to 1.8 g; begin a
   gradual left roll at 14 degrees nose up; retain the requested load
   through the roll; pitch peaks near 30 degrees; ease roll and pull as
   the aircraft returns wings-up and level.

Item 1 is user-validated. Item 2 is prepared and installed; live validation is pending. Item 3 is the user's proposed maneuver profile,
not independently verified Blue Angels procedure. Before implementing it,
resolve the geometric versus aerodynamic load interpretation and verify
that the requested pitch, bank, speed and load history are consistent.
Direct pose/motion control does not prove a real 1.8 g aerodynamic load.

## Representation and scope

The player flies the normal installed `FA-18C_hornet` module. Playback uses
the separate `DCSRecorder-Hornet-Probe` type, derived locally from the
installed Hornet aircraft descriptor and base builder. It references the
installed `fa-18c` exterior, preserves the Hornet descriptor's shape and
airframe parameters, and binds the existing experimental EFM/object plugin
to the new type. It does not bind or copy the licensed player flight model
or cockpit, and it does not change the stock Hornet registration.

Both mission units specify the installed **Blue Angels Jet Team** livery.
The stock livery ZIP is copied into the custom type's local livery lookup
directory. Generated ED-derived descriptors and assets stay under ignored
`package/`; they are local experimental assets, not distribution content.

This tests a Hornet playback representation, not controlling an ordinary
stock AI Hornet or retaining its full aerodynamic flight model. The native
actuator still requires the verified null-FM path. If the new registration
takes a different path, guards must reject it rather than relaxing them.
Automatic aircraft/livery recording and selection remain future work;
the eventual recording must identify the source aircraft and livery.

The original TF-51D mod and installed DLL are preserved. The Hornet uses a
separate plugin directory and `HornetProbe.dll`, compiled from shared code
with the Hornet speed/turn profile. Existing runtime-ID and native-signature
guards remain. Maximum allowed commanded speed is 260 m/s for this profile;
the 10 m per-command displacement guard is unchanged.

## Speed and maneuver

The user specified **400 KIAS**, not 400 knots of world speed. The mission
sets calm static weather, 15 C sea-level temperature and 760 mmHg QNH.
A subsonic compressible pitot relation converts 400 KCAS at the midpoint
altitude of 2,050 m in ISA to 225.02157 m/s (437.41 KTAS). CAS is used as a
nominal proxy for IAS; aircraft instrument/position error and DCS atmosphere
implementation mean the HUD reading still needs live verification.

The relation uses `qc = p0*((1+0.2*(Vc/a0)^2)^3.5-1)` and
`V = sqrt(gamma*R*T)*sqrt(5*((1+qc/p)^(2/7)-1))`. Source:
[NASA, Measurement of Aircraft Speed and Altitude](https://ntrs.nasa.gov/api/citations/19800015804/downloads/19800015804.pdf).
Mission observer rows `HORNET_AIR` additionally calculate CAS from measured
temperature, pressure and wind-relative velocity; these are not HUD IAS.
Row fields: aircraft name, time, temperature K, pressure Pa, airspeed m/s,
calculated CAS knots, wind X/Y/Z m/s. Missing atmosphere telemetry is not
evidence of zero error. The prior flight's measured CAS was 399.224–401.246
knots during mission seconds 10–70; this is not an instrument IAS reading.

The revised path uses `n=2.5`, bank `acos(1/n)` = 66.42 degrees,
and steady heading rate `g*sqrt(n*n-1)/V`. Quintic heading-rate ramps last
six seconds on entry and three seconds on exit. Integrating the ramps
and steady segment gives exactly 180 degrees in 35.961 seconds. Bank follows the instantaneous curvature.
The controller imposes a geometric path; this does not establish the
playback aircraft's aerodynamic load or an official Blue Angels profile.

- 0–5 s: native movement before capture.
- 5–7 s: settle onto the controlled path.
- 7–13 s: smooth roll-in to the right.
- 13–39.96 s: steady 2.5 g geometric level turn.
- 39.96–42.96 s: smooth roll-out, ending 180 degrees from the initial heading.
- 42.96–48.96 s: wings-level straight flight.
- First callback after 48.96 s: release; observe through at least 65 s.

Start 100 m aft and 60 m left of playback, as before. Both aircraft use
the selected Hornet livery, 3,500 kg internal fuel and no external weapons.
Stations 2, 3, 5, 7 and 8 specify `<CLEAN>`; an empty payload by itself leaves
these removable pylons installed. The stock player light trigger runs once
after one second, using installed device 8, commands 3001–3004, value zero.

## Build, package and verification

Build with `cmake --build experiments/efm-ownership/build --config Release`.
Run the four CTests, then run `prepare_hornet.py` with the available Python
runtime. It uses the user's installed donor mission/descriptors/livery,
generates the plugin and mission, and checks Lua syntax. The new files are
under `experiments/efm-ownership/package/hornet-prototype/`.

Four CTests passed for both DLL callback contracts and both trajectory
profiles, including position-derived 2.5 g, 180-degree heading change,
transition continuity, motion prediction, native rate convention, speed
and step bounds. Callback checks verify cosmetic writes are scoped,
bounds-checked, repeated after an engine-state change, and absent in the
TF-51D build. Packaging checks installed loader dependencies, datalink and
route validation, clean loadouts, the timed light trigger against installed
cockpit IDs, and Lua syntax. These
checks cannot establish DCS registration, appearance, livery loading,
indicated speed, object ownership or live native actuation.

DLL SHA-256: `7CA81DD728FB53B99FBC840C7158D0B21AC227B0CD20572C26F1CCF6410C05B3`.
The generated manifest records mission and DLL hashes.

## Live check

Restart DCS and open `EFM-Probe-Hornet-400KIAS-zero-wind.miz`. Fly for
65 seconds, using the player Hornet HUD to check airspeed while matching
the playback aircraft. Confirm all removable pylons are gone, exterior
lights stay off, and the playback speed brake stays stowed. Evaluate the
gentler six-second roll-in, steady turn, roll-out and release. Fresh Hornet logs are written under the
new mod's `bin/probe-logs/`; the existing hook still recognizes the mission
name and maps mission IDs to runtime IDs.

If startup or spawning fails, retain `dcs.log` and inspect registration
before any control changes. The first Hornet playback succeeded; this
six-second roll-in refinement is now confirmed by the user.

## Latest feedback and deferred playback requirements

The three-second entry felt too fast. The user requested a middle ground
between the original gentle curve and this entry, preserving the praised
steady pull. A six-second entry approximately halves peak bank rate from
52.73 to 26.37 degrees/second (the original 65-second climbing curve peaked
at about 2.46 degrees/second). Exit remains three seconds. The path integral
is adjusted to preserve the full 180-degree heading change and 2.5 g plateau.
Prior artifacts and logs are in
`experiments/efm-ownership/results/hornet-clean-turn-2026-09-26/`.

The user observed a steady 82% engine/throttle display in the exterior view.
The present object controller supplies pose, velocity, angular rates and
selected exterior arguments; it does not replay recorded engine state.
The source of that display and its relationship to sound are not established.
Do not claim an animation argument alone drives native engine audio.

Deferred requirement: capture and synchronize per-engine state (distinguishing
throttle command, RPM and afterburner), visible nozzle/flame effects, and
engine sound with the recorded-flight timeline. The user's acceptance case
is four layered flights entering afterburner together during a demo:
movement, visuals and audible engine transitions must agree. Validate what
DCS exposes and what the custom playback representation can reproduce
before promising fidelity. Keep this separate from current turn tuning.

The required layering loop is: record flight one; play it while flying and
recording flight two; play both while recording flight three; repeat.
Existing tracks must retain independent aircraft/livery/animation/engine
state on a shared timeline, without re-recording existing playback aircraft.
Multi-aircraft targeting, synchronization, persistence and performance remain
unimplemented; the current single-object prototype does not establish an
unlimited aircraft count. After this turn refinement, the staged path and
roll tests remain next, followed by recording/layering and engine-state
feasibility work as distinct milestones.
