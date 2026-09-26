# Aircraft physics bridge: targeted source check

Date: 2026-09-23. Scope: public, author-published source or shipped API examples connecting an object callback handle to a playback aircraft's physics or authoritative pose. One player/account remains required. This supplements the [native attachment investigation](dcs-installed-native-attachment.md); it does not repeat the lifecycle experiment.

## Result

No usable public class declaration or example for the required bridge was found in this bounded search. The installed object API deliberately forward-declares `Registered` and exposes its pointer as an opaque handle. It supplies ID and visual-argument functions, but no conversion to an aircraft, flight model, dynamic body, or pose writer. See the installed [ed_object_access.h](<D:/DCS World/API/include/ed_object_access.h>).

This is a missing interface, not evidence that native control is impossible. The confirmed object callbacks establish execution associated with our unoccupied probe; they do not establish physics ownership.

## Source checks

| Primary source | Finding | What it does not establish |
| --- | --- | --- |
| Installed [API directory](<D:/DCS World/API>) and [object header](<D:/DCS World/API/include/ed_object_access.h>) | The available include files cover object lifecycle/visual arguments, cockpit parameters, and the external human flight model. No `Registered`, `MovingObject`, `woPlane`, `woLA`, or `wAircraft` class definition occurs in the directory inventory. | A current C++ object layout or aircraft-to-flight-model accessor. |
| [A-29 author Luiz Renault's December 7, 2023 explanation](https://forum.dcs.world/topic/265017-a-29-super-tucano/page/34/) | The author reports constructing headers from DLL exports, implementing native avionics/FLIR, and revising headers after DCS changes. He explicitly describes the native implementation as closed source at that time. | Public reusable headers, nonplayer aircraft physics access, or a stable ABI. The report is historical precedent for native integration work, not an implementation we can use. |
| [A-29 author repository](https://github.com/luizrenault/a-29b-community) | Public module repository is available. The author's explanation distinguishes its public module from the closed native implementation. | Presence of a public module repository must not be treated as publication of the native bridge. No usable bridge was identified in the inspected sources. |

Exact-symbol/class searches included `cast_MovingObject`, `AIAerodyneFM`, `getDynamicBody`, `setPositionState`, `Registered.h`, `MovingObject.h`, `wAircraft.h`, `woMovingObject`, `woPlane`, and `woLA`, combined with DCS/Eagle Dynamics/GitHub qualifiers. Results were empty, unrelated, or crash stacks rather than class declarations. These are weak negative results: indexing gaps mean they cannot prove that no public implementation exists. No alleged SDK dump or leaked source was used.

## Candidate and exact gaps

The remaining concrete candidate is the installed native path already identified by exported names:

`ED_OBJECT_HANDLE / Registered* -> aircraft or MovingObject -> aircraft's actual flight model -> DynamicBody`

`AIAerodyneFM::setPositionState` is an alternative candidate endpoint if pose authority rather than force injection is required. These are investigation targets only. A force method on `DynamicBody` cannot be applied to `Registered*` merely because both pointers exist in the same process.

Before a mutation probe, establish all of the following from current-build evidence:

1. The actual dynamic type and any base-pointer adjustment for the callback handle.
2. A valid accessor or verified current-build ownership path from that object to its actual flight model; an exported base-class cast stub is insufficient.
3. The full argument layouts, calling contract, and lifetime of the returned object.
4. Whether simulation subsequently overwrites the proposed force/pose change, and which callback timing is appropriate.
5. Independent mission telemetry that can distinguish target movement from merely changing rendering arguments.

No stale published header was found that could even serve as a structural hint. Even if found later, a historical class declaration would need current-build validation; it would not by itself make a callable ABI. Offline examination of the installed exports and their call sites is the next evidence-producing step. There is currently no new source-backed simulator mutation test to ask the user to run.
