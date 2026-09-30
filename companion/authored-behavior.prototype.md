# Authored mission behavior — decision prototype

Status: conflict-refusal policy approved in discussion; structural control prepared; live preservation and replacement evidence pending. This is the remaining decision blocker for [Complete Hornet mission setup and hot-start parking-to-parking playback](https://github.com/caw1517/DCSRecorder/issues/11), tracked by [Define compatibility with authored triggers and aircraft tasks](https://github.com/caw1517/DCSRecorder/issues/19).

The user agreed to refusal with an explanation when a selected aircraft's authored commands conflict with playback, while noting that simple recording missions need not contain custom AI tasks. Ordinary waypoint geometry is not automatically a conflict: the selected aircraft's authored start must be retained, and the playback path comes from the take. Executable AI tasks, controller actions, state changes and lifecycle commands need explicit classification. No authored route or action is silently discarded.

## Proposed ownership and compatibility matrix

These are proposed preparation rules, not an implemented general detector. The narrow source/prepared fixture below exercises known behavior only.

| Authored content | Proposed rule | Evidence or outstanding gate |
| --- | --- | --- |
| Unrelated aircraft, vehicles, scenery, route/task data | Preserve identifiers, membership, settings and behavior | Structural equality in controlled fixture; live control pending |
| Briefing, locale dictionaries, resource scripts/media | Preserve bytes and references; resolve localization for review | Prior identity probe proved dictionary indirection; new fixture preserves dictionary/resource bytes |
| Known read-only selected unit/group references | Preserve stable source IDs/names; verify same-object semantics through staging and completion | Native numeric references and script lookups exercised by forthcoming control; real playback lifecycle still unimplemented |
| Known timed flags and background triggers | Preserve; no whole-mission pause implied | Timed trigger and resource-script counters in live fixture |
| Selected aircraft movement/controller/state tasks | Refuse when incompatible or unclassified; identify exact trigger/task and target | User approved refusal. Default route geometry alone is not evidence of conflicting executable behavior |
| Selected aircraft activate/deactivate/destroy/respawn | Refuse; playback owns release, removal and parked completion | Local API maps deactivation to destruction; lifecycle integration evidence remains required |
| Unknown/dynamic scripts or references | Refuse automatic compatibility approval until bounded review or a supported adapter establishes the contract | String scanning cannot prove script behavior or dynamically constructed identifiers |
| Temporary stand-in/replacement | Unsupported unless lifecycle and reference/event semantics are separately demonstrated; prefer one real object | Replacement experiment pending; same name cannot establish same runtime object |
| Known recorder-name/resource/flag collisions | Allocate unused identifiers without changing authored ones | Fixture deliberately occupies DCSR_PROBE_1_READY; preparation chooses DCSR_PROBE_2_READY |
| Re-preparation | Always derive from immutable authored source and same profile; no accumulated additions | Two preparations produce byte-identical fixture archives; generated input explicitly refused |

For production, use separate namespaces for unit/group IDs, trigger indices, flags, resource keys/files, Lua globals, menus and callbacks. Enumerate all supported categories and references; allocate within demonstrated DCS limits. A random prefix alone is not evidence against unknown dynamic scripts. Record every owned addition in an external preparation record and validate its content; a copied embedded manifest is not trusted identity. Verify complete source and compiled trigger tables, locale maps and resource bytes. Restart/failure cleanup removes only owned resources and cannot cancel authored callbacks.

Preserving a trigger does not freeze its meaning: a parked aircraft remains alive; an airborne-ending take removes the playback aircraft. Read-only existence/position conditions may therefore observe different outcomes in a different take. Show these lifecycle consequences during review. Cached object references, unit type/category queries, event handlers and group task indices need particular care when converting stock aircraft to a playback entry or considering replacement. Structural preservation is necessary but not sufficient for equivalent behavior.

## Review shown to the user

Show the selected aircraft and revision, preserved categories, every deliberate recorder-owned addition, unsupported/unclassified behavior, and conflicts by authored trigger/task name with affected aircraft. A conflict refuses preparation and explains the needed source change or alternative aircraft choice. Do not offer a blanket override of an incompatible command. Preserve the original mission and earlier takes. A new revision needs the already-agreed association review; confirmed identical revisions reuse their mapping.

[Interactive decision model](authored-behavior.prototype.html) provides preservation, task-conflict, object-replacement, known-collision and unknown-script scenarios. It is simulated behavior, not a general mission inspector. The collision name shown is illustrative and not a production namespace guarantee. Browser visual automation is not claimed.

## Code/source evidence

Source baseline: accepted recorder checkpoint 705baec; installed DCS 2.9.29.27468.

| Source | Finding |
| --- | --- |
| `experiments/efm-ownership/make_recording_mission.lua:8,24–25` | Deletes donor Probe and overwrites trigger 1 |
| `experiments/efm-ownership/make_staged_playback_mission.lua:17–40,49–59` | Assumes two single-unit groups; changes identity/type/route/activation and overwrites triggers 1 and 3 |
| `companion/library.py:157–167,200` | Preparation starts from a fixed donor |
| `prepare_staged_playback.py:73–74` | Copies non-mission archive members, but that does not repair rewritten mission behavior |
| DCS `MissionEditor/modules/me_mission.lua:4602–4611` | Editor regenerates compiled trigger tables from source trigrules |
| DCS `MissionEditor/modules/me_trigrules.lua:4193–4214` | Invalid references may be pruned on editor save |
| DCS `MissionEditor/modules/me_predicates.lua:518–525,584–618` | Unit/group trigger references use numeric IDs |
| DCS `MissionEditor/modules/me_trigrules.lua:4170–4189` | Task reorder repairs group/task-index references |
| DCS `Scripts/dictionary.lua:604–619,830–834` | Resource keys map to locale archive filenames; allocator advances maxDictId |
| DCS `Scripts/ScriptingSystem.lua:61–74` | Group deactivation calls destroy; AI state and activation are runtime actions |

Vendor source stays local. Source inspection does not establish replacement event behavior, arbitrary-script equivalence or complete DCS compatibility.

## Bounded source/prepared control

`authored-behavior-fixtures.prototype.py` reads serialized mission data without executing it and creates two disposable archives from the earlier stock-Hornet fixture. It is a known-fixture generator, not a general safe preparation implementation. There is no custom playback aircraft, native override or actual recording in these controls.

- **030-Behavior-Source:** player Hornet, selected stock AI Hornet and unrelated stock AI Hornet; preserved route/task structures; a known attached authored resource script; named authored flags; a timed native unit/group-alive trigger; localized briefing text.
- **031-Behavior-Prepared:** same content plus one appended startup trigger/resource and an isolated flag. Deliberately occupied authored flag retains value 73; native reference trigger sets its flag to 17 after five seconds. Both source and prepared log at roughly 2, 12 and 22 seconds, including IDs, cached-reference existence, counter and unrelated aircraft motion.

Structural comparison removes only declared owned additions and the resource-counter increment, then compares the complete mission tree. It also compares all existing member bytes; only `mission` and the DEFAULT resource map change. Authored script/dictionary bytes remain equal. Re-preparing from the same immutable source gives byte-identical ZIP bytes. See `authored-behavior-structural.prototype.json`.

Live protocol: load each archive from Mission → My Missions, click Fly, wait about 25 seconds for the completion message, then pause. The user operates DCS; the agent reads the log. Compare counts, flag transitions, resolved unit/group references, cached handles and unrelated movement across runs. These results will establish only the demonstrated append-only control behavior. Follow with an editor save/reload and a separate replacement-object probe as needed; never infer actual playback preservation from these stock controls.

## Still needed before resolution

Live source/prepared comparison, editor round-trip reference/resource preservation, and a bounded object-lifetime check or explicit unsupported replacement boundary. Final matrix must distinguish measured behavior from source-derived expectations and unsupported cases. The user's conflict-refusal preference is settled; no repeated approval is required. Broader production preservation, real-object staging, runtime mission verification, ground physics and full-flight acceptance remain owned by the ground milestone and related evidence issues.
