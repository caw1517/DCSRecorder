# DCS AI aircraft ground and air phases, and the crash on touchdown

Research date: 4 October 2026. Ticket: [#36](https://github.com/caw1517/DCSRecorder/issues/36), blocking [#28](https://github.com/caw1517/DCSRecorder/issues/28).
Build: DCS World **2.9.30.28536** (`D:/DCS World/autoupdate.cfg`). DCS was not launched for this note.

Evidence comes from three places:
- the progress comment on #28 and the uncommitted `takeoff-landing-2026-10-04/live-6` logs;
- the installed Mission Editor Lua and DLL export names;
- offline disassembly of the captured 2.9.30 `DCS.exe` `.text`/`.rdata`/`.pdata` image (`Saved Games/DCS/Scripts/DCSRecorderBuildCapture/evidence-29516`, taken by `experiments/efm-ownership/build-compatibility`).

Vendor bytes are not committed. All RVAs below apply only to this build and capture.

Trust labels:
- **[ED]** official Eagle Dynamics documentation or installed ED files;
- **[Wiki]** the Hoggit scripting wiki (community-maintained, close to ED's API);
- **[Bin]** our own static reading of the installed binaries. These are inferred names and semantics, not a supported contract;
- **[Community]** unverified forum posts.

## Summary

- **The playback aircraft is not a supported AI configuration.**
  - The Mission Editor offers `TakeOffGround`/`TakeOffGroundHot` ("From Ground Area") to planes only when the group has no AI. **[ED]** `MissionEditor/modules/me_route.lua`: the `plane_*_userOnly` lists are selected only when `getBotInGroup(group)` is false (lines ~140–175, ~2047–2062).
  - Our playback copy gives an AI (`skill='High'`) Hornet that start type, with `airdromeId` and parking removed (`companion/authored_missions.py` ~519–536).
  - No ED source describes how an AI plane behaves after a "ground area" start with a single route point.
- **Takeoff, landing and taxi are bound to an airfield and its ATC.**
  - The AI flight-model exports name each phase with an airfield argument: `AIPlaneFM::setTakeoff(wAirdrome*)`, `setLanding(wAirdrome*)` and `setTaxi(wAirdrome*, IRoute*, purpose)`. The landing classes are `LandingTangent`/`Slope`/`Exponent`/`Run`, plus `AIPlaneFMTakeoffControl`/`LandingControl`. **[Bin]** (`AIFM.dll` strings)
  - ATC gating is `woATC::canStartLanding`/`canStartTakeoff`/`controlTakeoffAndLanding`. **[Bin]** (`Flight.dll`)
  - Airplanes land only through a `Land` route point carrying `airdromeId`, at a friendly airbase. **[Wiki]** [Mission task](https://wiki.hoggitworld.com/view/DCS_task_mission)
  - The `Land` *task* (land at an arbitrary point) is for helicopters only. **[ED]** [Controller reference](https://www.digitalcombatsimulator.com/en/support/faq/1267/), and `me_action_db.lua` offers `ActionId.LAND` only to helicopters.
- **The crash path found in the binary bypasses damage.**
  - In 2.9.30, woAIPlane's control routine (vtable slot `+0xd58`, RVA `0x6fd5b0`) dispatches on a mode integer at complete object `+0x7F4`.
  - Mode `8` calls a routine that compares a stored height with the aircraft's own position and then calls a "crash at point" routine.
  - That routine emits `MovingObject::createCrashEvent` and `WorldManager::notifyDeath` directly, with no life or damage step. **[Bin]**
  - This fits the observation: life 20/20, then `pilot dead` and `crash` in one step, despite `SetImmortal`.
- **No ED source says that immortality covers terrain impact for AI.**
  - ED documents `SetImmortal` only as "Makes the unit/group immortal". **[ED]**
  - The wiki adds that nothing will be able to kill it. **[Wiki]** [setImmortal](https://wiki.hoggitworld.com/view/DCS_command_setImmortal)
  - Our run 5 shows that it does not stop this crash.

## 1. What decides the phase, and what triggers the crash

**Documented behavior:**
- AI takeoff and landing are route actions (`TakeOff*` and `Land` points) tied to an airbase. **[Wiki]** [Mission task](https://wiki.hoggitworld.com/view/DCS_task_mission)
- `S_EVENT_CRASH` "occurs when any aircraft crashes into the ground and is completely destroyed". **[Wiki]** [crash event](https://wiki.hoggitworld.com/view/DCS_event_crash)
- `S_EVENT_LAND` needs an airbase, FARP or ship plus slowing down; since 2.9.6, `runway_touch` marks the moment of contact. **[Wiki]** [land event](https://wiki.hoggitworld.com/view/DCS_event_land)
- ED's 9 October 2020 newsletter says the AI can make emergency landing decisions on land or water. That is a damage-driven behavior, not a controllable phase. **[ED]** [Newsletter](https://www.digitalcombatsimulator.com/en/news/newsletters/f8a8454be68a1d830bca796628fb704b)

**What the binary shows [Bin]:**
- **The playback object takes the legacy path.** Its `AIPlaneFM` member is null (see `docs/research/dcs-null-flight-model-path.md`), so the AIFM phase classes above are not the code running.
- **The legacy control routine** is woAIPlane vtable `+0xd58`, RVA `0x6fd5b0`. It is the 2.9.30 counterpart of the 2.9.29 routine `0x6fbf60` from `docs/research/dcs-update-gate-experiment.md`.
  - At `0x6fd629` it returns early when the byte at complete `+0x5002` is non-zero. That is the 2.9.29 `+0x4fea` update gate, shifted 0x18 as the pitch offset was.
  - The physics step (`+0xc70`, `0x711710`) tests the same byte at `0x711782`.
- **A mode integer at complete `+0x7F4` drives the routine.**
  - The main switch at `0x6ffcda` (index table `0x7022b4`, targets `0x702210`) has cases 1–5, 7–10, 0xC–0xF, 0x12/0x1B, 0x1C–0x22, 0x2E, 0x2F and 0x33–0x44.
  - The routine writes modes 8, 0x2E, 9 and 0xD in several places. For example, `0x6fdd50`/`0x6fdd5c` choose 0x2E (if currently 0x2F) or 8.
  - Mode names are unknown. A takeoff family around 0x2E/0x2F and a flight mode 8 is a hypothesis.
- **Crash path A (mode 8):**
  - Case 8 (`0x700547`) clears byte `+0x7CB` and calls `0x70c530`.
  - At `0x70ce98`–`0x70cec8` that routine compares the double at `+0x248` with the y component of the float position triplet at `+0x1AC` (`+0x1B0`) plus a constant (the `.rdata` double at `0x1101970`, which reads 1.0).
  - If `[+0x248] > y + 1.0`, it calls the crash routine with the position.
  - What `+0x248` holds is unproven. Terrain height alone does not fit: run 6 crashed with origin about 2.5 m above terrain.
- **Crash path B:**
  - `0x6fb470`, called from the same control routine at `0x701589`, may set mode 8.
  - It then calls the crash routine at `0x6fc37f` when four things are all false or zero: the MovingObject virtual `+0x230`, byte `+0x26D3`, qword `+0x5568` and byte `+0x5591`.
- **The crash routine** is `0x65ca60(this, const Vec3*)`, with 21 direct callers.
  - Its tail (`0x65d87c`–`0x65d8d9`) calls `MovingObject::IsFlag(0x100)` and two virtual calls.
  - It then calls `createCrashEvent` (IAT `0x10f4b48`) and `WorldManager::notifyDeath` (IAT `0x10f48a0`).
  - No life setter or immortality test appears on that tail. The full body, including the `pilot dead` emission point, has not been read.

**Why this fits the observations (inference):**
- **Takeoff pin.** The run 1 pin until about 4 m matches a ground/takeoff mode that clamps the pose until DCS's own liftoff condition. Restoring the tape pose before each step works around it (run 2).
- **Taxi.** Taxi and parked holds never leave that family, so the flight-mode check never runs.
- **Touchdown.** After liftoff the AI is presumably in mode 8. At the first grounded sample, path A or B fires within the same native step.

## 2. Landing waypoint/task and other Controller levers

- **Landing waypoint.** An airplane landing needs a `Land` point with `airdromeId`, and the airbase must be friendly. **[Wiki]** [Mission task](https://wiki.hoggitworld.com/view/DCS_task_mission)
  - In the Mission Editor, `Landing` is offered only as the last point or the only point (`plane_last_point`, `plane_one_point`). **[ED]** `me_route.lua`
  - So a playback copy would need at least two points: start, then `Land` at the recorded airfield.
  - Alternatively, a `Mission` task with that route could be set at runtime.
- **Point landing.** The `Land` task with a point is for helicopters only. **[ED]**
- **Landing option.** The only landing-related option is `LANDING_OPTIONS` (36): straight-in, force pair, restrict pair, overhead break. `ALLOW_LINE_UP_RW` (37) and `RTB_ON_BINGO` (6) also exist. **[ED]** `me_action_db.lua` ~572–666, 3470–3486
  - None of them changes ground-contact handling.
- **Commands available in 2.9.30.** `SetImmortal`, `SetInvisible`, `SetUnlimitedFuel`, `StopRoute`, `SwitchWaypoint` and `Start`, among others. **[Bin]** `WorldGeneral.dll` `AI::*::create`
  - None is documented to change phase or contact.
- **Does the phase advance under an external pose? Unknown.**
  - The control routine still runs every step and reads the restored pose (`+0x1AC`), so position-keyed transitions may advance. **[Bin]**
  - The landing logic is also gated by ATC (`woATC::canStartLanding`, `controlLanding`, `onTouchDown`). **[Bin]** It may command go-arounds when the recorded speed or path disagrees with its own approach plan.
  - Pair landings and go-arounds are long-standing AI landing complaints. **[Community]** e.g. [AI landing problem thread](https://forum.dcs.world/topic/103336-a-very-serious-ai-landing-problem-bug/)
- **Side effects of AI landing logic:**
  - ATC approach sequencing and radio calls;
  - rollout and taxi to parking under the AI's own steering;
  - engine shutdown, then possible removal.
  - MOOSE RAT despawns aircraft after `S_EVENT_LAND` or engine shutdown, and notes that large aircraft without suitable parking "despawn immediately upon touchdown". **[Community/tool doc]** [MOOSE RAT](https://flightcontrol-master.github.io/MOOSE_DOCS/Documentation/Functional.RAT.html)
  - The playback copy's recorded touchdown point, speed and rollout may conflict with all of these.

## 3. Immortality and invisibility

- **`SetImmortal`.** "Makes the unit/group immortal". **[ED]** The wiki adds "Nothing will be able to kill it. Nothing!" **[Wiki]**
  - Neither source lists collision or terrain impact.
  - ED's user manual describes the *player* option this way: "Enabling immortality will make it impossible to damage or destroy your aircraft." **[ED]** `Doc/DCS User Manual EN.pdf`
- **`SetInvisible`.** Only hides the group from enemy AI. **[ED]**
- **Run 5.** `SetImmortal` was logged and the aircraft still crashed. The crash path above emits events directly, which may explain it. **[Bin, inference]**
- **Community reports conflict:**
  - An immortal, pilotless AI aircraft is said to have "kept bouncing on and off the ground". **[Community]** [Forum](https://forum.dcs.world/topic/324858-is-it-correct-that-immortal-units-can-get-damaged/)
  - Another report says collision damage taken while immortal is applied once immortality is removed. **[Community]**

## 4. Native structures in this build [Bin]

All fields are offsets from the woAIPlane complete object (SDK handle − 8). They are unnamed and unverified live.

| Item | 2.9.30 location | Note |
| --- | --- | --- |
| Physics step | vtable `+0xc70` → `0x711710` | Already hooked by the shadow table |
| Control / AI logic | vtable `+0xd58` → `0x6fd5b0` | Contains the mode switch and both crash paths |
| Update gate | byte `+0x5002` | Gates both routines; was `+0x4fea` in 2.9.29, live-tested there |
| Mode | int `+0x7F4` | 8 calls `0x70c530`; 0x2E/0x2F/9/0xD also written |
| Height compared in path A | double `+0x248` | Crash if `> pos.y + 1.0` (constant inferred) |
| Position | float[3] `+0x1AC` | Matches the validated null-member position triplet |
| Crash routine | `0x65ca60` | `IsFlag(0x100)` → createCrashEvent → notifyDeath |
| Imports | `createCrashEvent` IAT `0x10f4b48`; `createKillEvent` `0x10f5be0` (caller `0xcb1e2b`); `notifyDeath` `0x10f48a0` | Resolved against the captured WorldGeneral base `0x7ffa99a30000` |

Method:
- Overlay the captured sections on the installed `DCS.exe` with `inspect_pe.py --analysis-image`.
- Resolve `.rdata` pointers against the on-disk `WorldGeneral.dll` export RVAs plus the captured module base.
- Scan `.text` for `FF 15` and `E8` callers, decode the MSVC two-level jump table, and read short `dumpbin /disasm` ranges.
- The on-disk `DCS.exe` uses a UPX-style loader. Its own import directory is the stub's, so the captured image is needed.
- `.pdata` bounds in the capture were unreliable. Function starts were taken from `int3` padding.

## 5. How other tools avoid it

- **DCS tracks** re-simulate the mission rather than placing aircraft. ED staff describe them as unreliable for long missions. **[ED staff]** BIGNEWY in [this thread](https://forum.dcs.world/topic/144561-track-replay-is-bugged/)
  - The claim that tracks record only control inputs, not positions, comes from a community post. **[Community]** [Forum](https://forum.dcs.world/topic/153206-unusable-record-flight)
- **Tacview** replays in its own 3D viewer, not inside DCS. **[Vendor]** [Tacview](https://www.tacview.net/product/about/en/)
- **MOOSE and MIST** use ordinary AI routes with `Land`+`airdromeId` (RAT), or respawn/teleport groups (MIST `teleportToPoint`). Neither drives a pose every frame, so neither meets the problem. **[Tool docs]** [MOOSE RAT](https://flightcontrol-master.github.io/MOOSE_DOCS/Documentation/Functional.RAT.html), [MIST teleportToPoint](https://wiki.hoggitworld.com/view/MIST_teleportToPoint)
- **No public tool or server mod** was found that keeps an externally posed AI plane alive through touchdown. Earlier repo research found no supported pose setter (`dcs-playback-feasibility.md`).

## Implications for playback (ranked)

**1. Read-only live diagnostic first (prerequisite for 2–4).**
- Using the existing guarded reads, log these each step from liftoff−2 s to the crash:
  - `+0x7F4`, `+0x248`, `+0x1B0`, `+0x7CB`, `+0x26D3`, `+0x5568`, `+0x5591` and `+0x5002`;
  - the result of the MovingObject `+0x230` virtual, read if a guarded call is accepted. Otherwise infer it.
- Capture a return-address stack on object destruction to see whether path A or B fires.
- Must prove: mode values during taxi, takeoff roll, airborne flight and touchdown; which branch kills; what `+0x248` is.

**2. Hold the per-object update gate (`+0x5002`) during grounded-after-flight samples.**
- The gate already exists as code, and its 2.9.29 form was live-tested on this object type. It skips the whole control routine, crash checks included.
- The physics integrator is skipped too. Pose is already restored before every step on grounded samples.
- The 2.9.29 test found worse jitter when pose came only from ForcePosition. The rollout must be rechecked visually and against velocity, wheel and animation consumers.
- Needs a 2.9.30 byte guard at `0x6fd629` and `0x711782`, and a lease restored on release or destruction.
- Must prove: touchdown and rollout survive with the gate on; no stale-state crash when the gate is released after stopping or at parking; sound and animation consumers unchanged.

**3. Keep or force the AI out of mode 8 at contact (write `+0x7F4`), or block crash path A only.**
- More targeted than option 2, but the meaning of each mode is unknown. Writing it could start ATC, taxi or takeoff logic.
- Must prove: the mode found by diagnostic 1 for taxi or takeoff roll accepts airborne-to-ground transitions; no pose clamp regressions; liftoff unchanged.

**4. A Landing waypoint in the playback copy.**
- Add a second route point, `Land` with the recorded field's `airdromeId`, keeping coalition friendly.
- This is the only documented way to give an AI plane a landing phase. It uses ED's own logic.
- Costs: approach and ATC behavior, go-around risk under external pose, the ground-start type (player-only for planes), and possible despawn after landing.
- Must prove: the AI reaches its landing or rollout mode by the recorded touchdown time while posed externally, with no go-around or ATC hold. Touchdown is then accepted at the recorded sink rate, and the aircraft is not removed before the parked ending.

**5. Patching the crash routine or the `createCrashEvent` IAT entry.**
- Event suppression alone would still leave `notifyDeath` and destruction.
- Code patching contradicts the current rule of never modifying executable pages (`native_step_hook.h`). Use only if 2–4 fail.

**6. Controller options or commands (`SetImmortal`, `SetInvisible`, landing options).**
- Already disproven for immortality (run 5). No other documented option touches contact.

## Limits

- This is static evidence from one capture. Mode names, the meaning of `+0x248`, the `xmm13` value on every path to `0x70ce9f`, and whether path A or B fires are all unverified live.
- Forum pages were read through a plain HTTP fetch. Staff status was taken from forum badges.
- This note does not establish behavior for stock AI starting from an airfield.
- The uncommitted run evidence (`takeoff-landing-2026-10-04`) was read from the main checkout.

## Live follow-up (4 October 2026)

Runs 7–10 and the airborne regression (`experiments/efm-ownership/results/takeoff-landing-2026-10-04/`, [#28](https://github.com/caw1517/DCSRecorder/issues/28)) settle part of the above:

- **Mode values (run 7).** The AI was in mode 51 (0x33) through taxi and the takeoff roll, then 2 from 52.96 s, then 4 from 139.52 s through touchdown. Mode 8 never occurred, so crash path A did not fire.
- **`+0x248`** held the terrain elevation, 43.0 m, throughout.
- **Path B matches.**
  - `+0x26D3` was 1 on the ground and cleared about 4 s after liftoff, at about 15 m.
  - `+0x5568` and `+0x5591` stayed zero.
  - The jet was destroyed at the first grounded sample.
- **The destroy stack** came from a deferred World.dll removal, so it does not name the path.
- **Ground flag (run 8).** Holding `+0x26D3` = 1 on grounded samples removed the crash. With the AI left in mode 4, DCS dropped the object to 25 native steps/s and 10 SDK ticks/s on the rollout, which caused visible stutter.
- **Taxi mode (runs 9–10).** Also holding mode 51 on grounded samples restored 50 steps/s. The user accepted the result.
  - Both writes are confirmed data writes. No code is patched.
  - The implementation is in `experiments/efm-ownership/surface-start/ai_ground.h`.
- **Still unknown:**
  - the meaning of the other mode values;
  - the MovingObject `+0x230` virtual on path B;
  - why `Unit:inAir()` stays 1 after touchdown (recorded as fog on [#11](https://github.com/caw1517/DCSRecorder/issues/11)).
