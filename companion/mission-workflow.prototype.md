# Mission Editor integration — reviewed workflow

Throwaway design artifact for [Choose Mission Editor integration for authored recording and playback missions](https://github.com/caw1517/DCSRecorder/issues/14). The user accepted the workflow, saved-scene default and hard-stop policy on 29 September 2026. This artifact records the reviewed design; it is not implemented DCS capability. The issue resolution is the canonical decision record. Open `mission-workflow.prototype.html` directly for the in-memory walkthrough.

## Reviewed user workflow

1. In DCS Mission Editor, create an authored mission with ordinary stock Hornets at the intended positions. Add scenery, vehicles, visual references and other mission content normally. Save the `.miz`.
2. In the companion, choose that authored mission and the Hornet to record. Show unit names, positions and roles so the user can distinguish aircraft; do not require special names such as Observer or Probe. Prepare a separate recording mission. The original remains unchanged.
3. Fly that copy and save a take using the recording controls. Retain the exact prepared mission revision and aircraft association with the take. The first captured pose is authoritative for playback; it is distinct from the aircraft's authored spawn if recording starts later.
4. Select the take and a different Hornet from the mission to fly alongside it. Prepare a separate playback mission, using the scene saved with the take by default. The recorded aircraft becomes the playback aircraft in the output; the other selected Hornet becomes the player at its authored position. The companion should offer return-to-editor guidance if no second suitable aircraft exists, rather than inventing ground placement.
5. Load the prepared playback mission. The visible held staging/release/parked completion behavior is decided in the separate lifecycle ticket.

All output missions go into the user's Saved Games/DCS/Missions folder with new names. Placement and scene editing remain in DCS Mission Editor. Choosing roles and a take in the companion does not introduce an application-side map editor. Existing installed-build and DCS-closed preparation requirements remain until a separate implementation proves they can be relaxed.

## Reviewed mission association and edit contract

Retain an immutable source/prepared revision, preparation identifier and authored unit identity with each new take, in addition to the existing recorded aircraft, livery, terrain, runtime identity and first sample. Unit names alone are insufficient across deleted/recreated or unrelated missions. Exact identity persistence across Mission Editor resaves must be investigated before promising it. Legacy recordings without this association retain their existing workflow; do not invent provenance for them.

The user can explicitly choose a later authored revision instead of the saved scene. Compare its relevant mission content with the revision used to record, not only a whole-file archive hash: a hash can detect difference but cannot explain whether it matters.

| Change | Reviewed behavior |
| --- | --- |
| No change; use saved scene | Prepare at original recorded pose/path. |
| Move the recorded aircraft's authored start, change terrain or lose its reliable identity | Refuse the edited scene; offer the saved revision or restoring the association/placement. Do not translate the recorded path. |
| Move the other aircraft used as player | Show the change and allow a reviewed new playback copy at its new authored start. |
| Change scenery, reference objects, briefing, time or supported weather | Show relevant changes and require explicit choice of the new scene. Unsupported weather/build remains a refusal. Acknowledgment is not a collision or script-safety guarantee. |
| Change recorded aircraft type or recording-relevant configuration | Reject unsupported/incompatible changes; preserve captured identity and state. The exact supported configuration comparison must be explicit in implementation. |
| Edit source after preparing a recording copy | The take belongs to the copy actually flown, not the latest contents of the source path. |
| Edit a generated copy | Prefer editing the authored source and regenerating. Detectable generated-copy mismatches should refuse; reliable runtime detection after editor resaves remains unproven. Do not claim a universal tamper check. |

## Integration and preservation requirements

- Modify only selected aircraft roles and recorder-owned controls/resources. Preserve other aircraft and scene objects; multiple scene aircraft do not imply multiple playback recordings.
- Preserve briefing, localization, embedded resources, weather/time, coalition content and unrelated routes/tasks/triggers except explicitly reviewed incompatible settings.
- Allocate non-conflicting recorder names, unit/group identifiers, flags and trigger/resource entries. Do not assume trigger slots 1, 2 or 3 are available. Re-preparation must not duplicate controls.
- Define handling of authored triggers/tasks that refer to the selected recorded aircraft. Preserving text does not establish that a replacement aircraft has equivalent task/event behavior. Unsupported conflicts need an explanation rather than silent removal.
- Preserve mission dependencies; a prepared copy cannot guarantee third-party assets exist on another installation.
- Inspect before/after mission structure and archive member contents: unrelated content should be unchanged, with an explicit allowlist for intended selected-aircraft/recorder edits. Use fixtures with trucks, unrelated aircraft, triggers, briefing/resources and scene revisions, then verify in Mission Editor and DCS during implementation.
- Scoped validators must check the selected Hornets and recorder-owned controls, rather than requiring every airplane in the mission to match the donor configuration.

## Alternatives considered

**Direct editor-only setup:** Best fits the user's preferred authoring surface, but there is no implemented route in this repository. It needs a demonstrated way to bind a take, install mission controls and identify the selected aircraft. Do not infer that DCS forbids it merely because it is absent here. The user accepted companion preparation for this milestone; an editor extension or manual-script route is not required before proceeding.

**Companion preparation of authored missions (selected):** Reuses existing archive-copy/preparation structure and keeps the layout in Mission Editor. Adds the explicit mission/aircraft/take association currently missing. Costs a preparation step and a separate output file.

**Companion scene editor:** Excluded by the user's preference and unnecessary for this decision.

**Mutate the original mission in place or silently move recorded paths:** Rejected because they lose the stable source or violate the user's original-coordinate requirement.

## Facts checked in the current repository

- `companion/app.py:77` exposes fixed practice generation and playback by recording ID, with no authored mission selector.
- `companion/library.py:157` and `:200` use a fixed configured baseline for recording/playback. Archive copying at `:167` preserves non-mission entry contents; it does not prove scene preservation inside the rewritten mission table.
- `experiments/efm-ownership/make_recording_mission.lua` and `make_staged_playback_mission.lua` assume Observer/Probe names and overwrite known trigger slots. Playback also overwrites positions/routes/description.
- `record_flight_engine_mission.lua:34` records aircraft/livery/terrain and runtime source identity, not source mission revision. Tape fingerprints bind the tape to the controller, not the authored mission to the take.
- `verify_hornet_routes.lua:22` and `verify_hornet_configuration.lua` enforce donor-wide aircraft/trigger assumptions. Generalizing only the builder is insufficient.

## Expanding an authored mission

Adding three aircraft to a four-aircraft mission is a new scene revision, not a reason to discard earlier recordings. Keep existing aircraft associations and placements intact, select the expanded scene, review the additions and prepare a new copy. Old takes remain usable with their saved four-aircraft scene or a compatible expanded seven-aircraft scene. A newly added Hornet can be selected as the next recording subject or as the player's aircraft; those roles do not require multiple playback layers. The HTML illustrates the new-player case with one existing take.

Bind by persistent per-aircraft association within a mission lineage, not list position, total count, callsign alone or an unchecked reused DCS unit ID. Additions and reorderings must not reassign existing takes. If an aircraft is deleted/recreated or identity is ambiguous, require explicit re-association and compatibility checks rather than guessing. Exact reliable identity/diff mechanics need a bounded Mission Editor probe.

The old scene does not contain newly added aircraft. Selecting one therefore requires using the reviewed expanded scene. Added aircraft remain ordinary authored mission content unless selected for a role; they are not automatically parked placeholders or extra playback layers. Performance and future simultaneous-playback limits need measurement. No fixed four/six/seven-aircraft product cap is introduced by this workflow design.

## Resolution status

The user approved the three presented recommendations: companion preparation of Mission Editor-authored missions, immutable saved-scene replay by default with explicit changed-scene review, and refusal of moved recorded-aircraft placement rather than automatic path relocation. The four-to-seven expansion clarification follows those rules. Runtime mission-edit detection, identity continuity across editor saves, and selected-aircraft trigger/task compatibility still need their own evidence and decisions. Ground implementation and live simulator acceptance remain open.
