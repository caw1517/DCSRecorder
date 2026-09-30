# Authored mission behavior — decision prototype

Status: **decision resolved; conflict-refusal policy approved in discussion and bounded live controls complete. Production integration remains open.** This resolves [Define compatibility with authored triggers and aircraft tasks](https://github.com/caw1517/DCSRecorder/issues/19), the final planning blocker for [Complete Hornet mission setup and hot-start parking-to-parking playback](https://github.com/caw1517/DCSRecorder/issues/11).

The user agreed to refusal with an explanation when a selected aircraft's authored commands conflict with playback, while noting that simple recording missions need not contain custom AI tasks. Ordinary waypoint geometry is not automatically a conflict: the selected aircraft's authored start must be retained, and the playback path comes from the take. Executable AI tasks, controller actions, state changes and lifecycle commands need explicit classification. No authored route or action is silently discarded.

## Selected ownership and compatibility matrix

These are preparation requirements, not an implemented general detector. The narrow source/prepared fixture below exercises known behavior only. Unsupported cases must refuse automatic preparation; successful fixture results cannot be generalized to arbitrary scripts or real playback integration.

| Authored content | Selected rule | Evidence or outstanding gate |
| --- | --- | --- |
| Unrelated aircraft, vehicles, scenery, route/task data | Preserve identifiers, membership, settings and behavior | Complete source/prepared fixture structure preserved; unrelated aircraft samples matched live. Other object/task categories require integration coverage |
| Briefing, locale dictionaries, resource scripts/media | Preserve bytes and references; resolve localization for review | Prior identity probe proved dictionary indirection; new fixture preserves dictionary/resource bytes |
| Known read-only selected unit/group references | Preserve stable source IDs/names; verify same-object semantics through staging and completion | Native numeric references, script lookups and cached handles passed stock controls; real playback lifecycle still unimplemented |
| Known timed flags and background triggers | Preserve; no whole-mission pause implied | Timed trigger and resource-script counters in live fixture |
| Selected aircraft movement/controller/state tasks | Refuse when incompatible or unclassified; identify exact trigger/task and target | User approved refusal. Default route geometry alone is not evidence of conflicting executable behavior |
| Selected aircraft activate/deactivate/destroy/respawn | Refuse; playback owns release, removal and parked completion | Local API maps deactivation to destruction; lifecycle integration evidence remains required |
| Unknown/dynamic scripts or references | Refuse automatic compatibility approval until bounded review or a supported adapter establishes the contract | String scanning cannot prove script behavior or dynamically constructed identifiers |
| Temporary stand-in/replacement | Unsupported unless lifecycle and reference/event semantics are separately demonstrated; prefer one real object | Replacement invalidated cached unit/group references despite the same unit name and reported unit ID |
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

Live protocol: load each archive from Mission → My Missions, click Fly, wait about 25 seconds for the completion message, then pause. The user operates DCS; the agent reads the log. Compare counts, flag transitions, resolved unit/group references, cached handles and unrelated movement across runs. An editor Save As/reload and separate replacement-object probe were also completed. Never infer actual playback preservation from these stock controls.

## Live observations

The user flew source 030 and prepared 031 for about 25 seconds each. Both produced three authored script samples: selected unit 10302, selected group 10202 and unrelated unit 10303 remained present; cached selected unit/group references remained alive. The occupied authored flag stayed 73, and the native timed unit/group-alive trigger changed its flag from 0 to 17 by sample 2. All three logged sample payloads, including unrelated aircraft coordinates, matched exactly between these runs. The prepared copy additionally logged its separately allocated DCSR_PROBE_2_READY flag, with authored flag 73 intact. This is observed append-only fixture behavior, not actual playback or arbitrary-script equivalence. See `authored-behavior-runtime.prototype.log`.

Mission Editor observations: clicking Save on an unedited copy left the bytes unchanged, so that run is not serialization evidence. A subsequent Save As to 032-Behavior-Editor-Saved changed the archive hash. Source trigrules, numeric references and both script resources survived; resource-map values stayed equal. Compiled trigger 2 changed whitespace; the editor added custom/event trigger tables and an empty dictionary entry, advanced currentKey, and removed Radio fields from the two AI aircraft. Full aircraft-inventory equality is therefore false, and these configuration changes are reported rather than normalized away. All three runtime sample payloads still exactly matched the source, including flags, cached-reference validity and unrelated coordinates. See `authored-behavior-editor.prototype.json`. These results establish the exercised behavior, not unchanged semantics of every mission field.

Replacement observations: fixture 033 destroys only its disposable selected stock-AI group at eight seconds and recreates a same-name group. The requested replacement group/unit IDs were 10402/10502; DCS reported group 10402 and unit 10302 (the original unit ID). Immediately after destroy, cached handles still reported alive; after recreation the cached unit became invalid, and subsequent samples showed both cached unit/group handles invalid. Fresh name lookup found the replacement. Numeric event IDs 15 and 18 were logged for unit 10302; this probe does not infer a complete event sequence or promise destruction generates a particular death event. The existing once-only authored flag remained 17 and unrelated motion matched the earlier samples. A matching name or numeric ID therefore cannot preserve retained object references. This is a stock replacement observation, not proof that a production visual/audio stand-in can meet the lifecycle contract.

## Decision and implementation handoff

Preserve supported authored behavior and isolate recorder-owned additions. Only remap references whose complete supported structure and semantics can be validated; no remapping is approved for opaque scripts, cached runtime objects or unclassified task references. A conflict points to its trigger/task and target and refuses preparation. The user approved this refusal policy; the model and controls were discussed and live DCS steps were performed by the user. A hands-on HTML review is not claimed.

Current donor-specific builders must not be applied unchanged to arbitrary missions. Production work must cover stock-to-playback type conversion, selected-aircraft tasks and group membership, real-object staging/release/completion, source/compiled-trigger agreement, all locales/resources, collision-free allocations and exact re-preparation from saved source. Pair complete structural comparisons with live behavior checks; unexpected editor changes remain reviewable differences. Mission-load authorization remains independently gated by the mission-identity decision. Ground physics, complete state synchronization and full-flight acceptance remain open under the ground milestone and related evidence issues.

The controls require no installed hook or native modification. Only disposable missions were added; raw archives remain local. The current mission's diagnostic timers stop after their bounded samples; their callbacks disappear on mission exit. No production recorder changes or broad compatibility guarantee are made.
