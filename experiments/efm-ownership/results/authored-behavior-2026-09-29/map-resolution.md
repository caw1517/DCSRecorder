## Destination

A reliable single-player flight recorder: record a flight, replay it as another aircraft while flying alongside, then build layered formations. **Complete one-aircraft fidelity before layers.** One player and one DCS account; multiplayer is out of scope.

## Notes

- Current ground-operations scope is canonical in [Complete Hornet mission setup and hot-start parking-to-parking playback](https://github.com/caw1517/DCSRecorder/issues/11). The current wayfinding destination is an agreed implementation route and acceptance contract for that scope. Consult wayfinder, grilling and domain-modeling; use prototype for the designated decision tickets. Charting and decision resolution do not close implementation/evidence gates.
- Find open work through native sub-issues and native blockers. Within the current ground milestone, select the first open, unblocked, unassigned decision ticket in child order. V2, layered playback and voice tickets remain deferred regardless of technical unblock status. Existing claims are retained.


- The accepted state-fidelity source is on [codex/hornet-state-capabilities](https://github.com/caw1517/DCSRecorder/tree/codex/hornet-state-capabilities), checkpoint 705baec. [Current roadmap](https://github.com/caw1517/DCSRecorder/blob/codex/hornet-state-capabilities/docs/ROADMAP.md); [final fidelity acceptance](https://github.com/caw1517/DCSRecorder/blob/705baec/experiments/efm-ownership/results/fidelity-final-2026-09-29/README.md). Generated game assets, recordings, raw logs and media remain local.
- The first airborne app workflow is accepted: automatic save, library/rename/validation, generated missions, Active Pause/F10/countdown, original recorded pose/velocity and nominal 150 ft player trail. The accepted airborne implementation removes the lead at completion and leaves the mission running; the agreed ground milestone replaces that endpoint with a parked hold. Restart replays.
- Latest live hard-turn take: 80.92 seconds, 4,047 successful motion writes, hook restoration confirmed. User accepted the roll correction and expanded playback and reports all requested workflow checks passed.
- Supported configuration: DCS 2.9.29.27468, Hornet/Blue Angels, Caucasus, zero wind, nearly-level airborne start, 5â€“300 seconds and 70â€“260 m/s. Staged playback no longer applies altitude/rate caps or the old acquisition blend/translation. Private native access remains build-specific.
- Full demonstrations from hot parking through flight and back to hot parking, including low passes and hard turns, remain the destination. Engine/afterburner fidelity is now accepted within the documented Hornet scope. Ground operations remain required follow-up work.
- Movement reproduces measured flight. Full exterior/engine state, collision, wake and ground-contact fidelity remain distinct requirements.

## Decisions so far

- [Determine whether DCS can drive a playback aircraft along an exact flight trajectory](https://github.com/caw1517/DCSRecorder/issues/2): demonstrated custom playback alongside the independent player; real recorded motion replaced synthetic paths.
- [Agree on a measurable synthetic-flight proof of concept](https://github.com/caw1517/DCSRecorder/issues/4): selected and executed the single-aircraft path. Freeze-plus-position was rejected; motion matching and a pre-integration override improved continuity.
- [Make the single-aircraft record-to-replay workflow reliable](https://github.com/caw1517/DCSRecorder/issues/5): implemented, published and accepted for the agreed airborne scope; see its resolution and validation record. Ground/state/portable-distribution work remains separate.
- Keep zero wind for the current baseline. Preserve original recordings and placement. Layering and synchronized voice remain deferred.

- [Complete single-aircraft visual and engine-state fidelity](https://github.com/caw1517/DCSRecorder/issues/6#issuecomment-5899531351): accepted tested Hornet V1 capture/playback and combined visual/audio fidelity; numerical limits and follow-ups are recorded in the resolution.

- [Choose Mission Editor integration for authored recording and playback missions](https://github.com/caw1517/DCSRecorder/issues/14#issuecomment-5900259507): Mission Editor authoring with companion-prepared copies, saved mission revisions, explicit changed-scene review and stable aircraft association; added aircraft preserve compatible existing takes.

- [Choose a concise aircraft registration and compatibility strategy](https://github.com/caw1517/DCSRecorder/issues/16#issuecomment-5900823132): stock-aircraft authoring and one playback entry per supported aircraft; recording versions do not multiply entries; preserve a restorable legacy setup and originals, with verified migration and rollback before cleanup.

- [Choose visible staging and parked completion for playback aircraft](https://github.com/caw1517/DCSRecorder/issues/15#issuecomment-5901002592): real-aircraft held staging first, a running surrounding mission, shared countdown release, hot parked completion, removal at other valid endings, and full-restart recovery; simulator experiments remain required.

- [Agree on parking-to-parking validation and acceptance](https://github.com/caw1517/DCSRecorder/issues/17#issuecomment-5901172540): real recorded flights, a 20–30-minute full-flight acceptance target, measured fidelity plus user review, and parked completion at the user's chosen stopping location; implementation and live evidence remain open.

- [Prove mission identity and edit detection across Mission Editor saves](https://github.com/caw1517/DCSRecorder/issues/18#issuecomment-5903365767): companion-owned revision/aircraft associations with once-per-revision confirmation; live checks show filename hashes cannot certify loaded content, so session-bound verification and fail-closed release remain implementation gates.

- [Define compatibility with authored triggers and aircraft tasks](https://github.com/caw1517/DCSRecorder/issues/19#issuecomment-5903606814): preserve supported authored behavior with isolated recorder additions; refuse conflicts/unknown behavior and require evidence for object replacement, whose cached references broke in live controls.

## Not yet specified

- Product-wide path/attitude/timing tolerances, using actual close-formation evidence.
- Recorded-path versus physical disturbance behavior after impacts or wake encounters.

- Per-aircraft channel availability, model/livery registration and support beyond the current Hornet.
- Duration/performance beyond the current ground acceptance target, and compatibility across DCS updates.
- Voice onset, latency/drift, pauses and any offset/restart controls. No perfect-sync guarantee is established.

## Out of scope

Multiplayer, another pilot/account, layers before one-aircraft fidelity, and microphone audio implementation during the present milestone.

For the current ground-operations milestone, additional aircraft types, layers, synchronized voice, deliberate relocation of recorded paths and free taxi/flight during staging are deferred. Startup/shutdown are V2. Existing [Improve playback engine sound depth (V2)](https://github.com/caw1517/DCSRecorder/issues/12) and [Add multicolor demonstration smoke (V2)](https://github.com/caw1517/DCSRecorder/issues/13) remain V2; V1 uses white smoke. The overall map still includes later layered playback after the single-aircraft gates.





