# Mission identity and edit detection — decision prototype

Status: **association policy approved by the user; core live Mission Editor round trips observed; remaining evidence gates open**.
This is evidence for [Prove mission identity and edit detection across Mission Editor saves](https://github.com/caw1517/DCSRecorder/issues/18), a child of [Complete single-aircraft playback, then add layered flights](https://github.com/caw1517/DCSRecorder/issues/1). It does not implement the authored-mission workflow or close the ground milestone.

User review: after the explanation of one authored mission with per-aircraft recordings, immutable saved scenes, and confirmation once per changed revision, the user answered **“Sure, I trust your guidance on this.”** This approves the proposed association/recovery policy through the live discussion. No further approval of that same policy is required. It does not turn simulated cases or unobserved simulator behavior into evidence, and does not imply a hands-on review of the HTML.

Open `mission-identity.prototype.html` directly in a browser. It is a self-contained, in-memory simulation of the proposed decision. Every aircraft operation and load check in the page is simulated, not a claim about observed DCS behavior.

## Question

How can the companion retain an aircraft association across edited missions without treating an editor ID, name, array position, aircraft count, or copied marker as proof that an aircraft survived? What can it actually verify about the generated mission loaded by DCS?

## Evidence collected

Installed build: **2.9.29.27468**. Local source inspection, an archive-only control and live Mission Editor saves were completed on September 29, 2026. The data probe parsed an existing local practice mission without executing mission Lua, made a four-stock-Hornet scratch fixture, and repacked the fixture with different ZIP ordering/compression. The archive SHA-256 changed; parsed mission-table and aircraft-inventory hashes stayed equal.

The ZIP-only control establishes the distinction between archive bytes and parsed content. The separate live observations below establish bounded editor behavior, including user-operated copy/paste.

Window access recovered after the user brought DCS forward. Editor actions used disposable scratch missions: `000-Identity-Probe-20260929.miz`, then Save As to `1000-Identity-Probe-20260929.miz`, plus the controlled fixtures below. Each saved stage was copied into local evidence before further changes. No original authored mission or production code was changed. Subsequent runtime diagnostics used a separate temporary read-only hook and a single stock Hornet derivative. No recording/playback or ground fidelity was tested. Browser automation rejected the local `file:` preview under its URL policy; JavaScript syntax was checked, but automated visual browser QA is unverified.

### Observed live editor behavior

The compact [observation record](mission-identity-observations.prototype.json) includes exact archive/content hashes, per-stage IDs/names, marker survival and changed data paths. Raw mission archives and full snapshots remain local under `experiments/efm-ownership/results/mission-identity-2026-09-29/`.

| Operation | Observed result | Implication |
| --- | --- | --- |
| Open four-aircraft fixture; Save As | Unit IDs 10111–10114 and group IDs 10101–10104 retained, along with names. Custom mission-root and unit UUID fields removed. Root ZIP marker removed; `DCSRecorderProbe/identity.json` retained. | Editor IDs help locate candidates. Custom fields are not durable; a preserved archive manifest still cannot prove aircraft continuity. |
| Save without placing/editing an object | Aircraft inventory equal. Archive and parsed mission hashes changed; `currentKey` and failure-entry `id` fields changed. An attempted Ctrl+S selected the add-ship tool, but no placement occurred and the saved coalition inventory did not change. | Exact archive equality is stricter than aircraft equality; do not classify the whole mission by its aircraft alone. This was not a completely input-free control. |
| Rename original unit/group 3 | Both names gained `r`; numeric IDs retained. The save also added `dynSpawnTemplate=false` and removed empty waypoint properties. | Rename does not require a new aircraft association; unexpected non-name changes must still be reported. |
| Add three Hornets, growing four to seven | Original IDs, names and authored positions retained. New units 10115–10117, groups 10105–10107. Existing unit 10111 radio channel changed 305→124; unit 10113 lost `hardpoint_racks=true` and gained `payload.ammo_type=1`; empty waypoint properties changed. | Demonstrates count-independent candidate correspondence, **not** unchanged configuration or end-to-end take compatibility. The sequence included selection/centering; the cause of each extra change was not isolated. No normalization rule is inferred. |
| Delete highest-ID aircraft; save; create replacement elsewhere; save | The replacement reused unit ID 10117, group ID 10107, unit name `Aerial-3-1` and group name `Aerial-3`. Comparing old/replacement data showed only unit/group/first-waypoint coordinates changed. | Matching IDs and names do not establish continuity. A moved replacement must not inherit the old take automatically. |
| Explicitly reopen the replacement mission and save | Seven aircraft and all IDs/names retained; replacement group gained `radioSet`, and `currentKey` changed. Nested marker still present. | Reopen/save is observed, but full semantic equality cannot be claimed. |

The initial live four-to-seven case contains additional configuration differences. A second controlled comparison below isolates additions and ordering. The association workflow remains a prototype policy, not a working implementation. All snapshots use single-aircraft groups; within-group ordering and leader effects were not exercised and must remain significant rather than normalized away.

### Remaining editor checks completed

The [additional observation record](mission-identity-remaining-observations.prototype.json) contains archive hashes, stored group orders and comparison paths. `mission-identity-fixtures.prototype.py` derives controlled fixtures from the already-saved seven-aircraft scene; this construction is separate from the subsequent real editor saves.

- **Actual copy/paste:** the user performed Ctrl+C/Ctrl+V and saved the disposable mission because injected Control chords did not reach DCS correctly. The archive contained eight aircraft. The copy had unit ID 10118, group ID 10108, unit name `Aerial-4-1`, and group name `Aerial-4`. All seven existing aircraft, including their group settings and routes, compared equal to the pre-copy snapshot. This is observed editor behavior, not a simulated copy.
- **Controlled compatible additions:** two fixtures contained the same original four aircraft, with one fixture also containing three more. Both were opened and saved in Mission Editor without selecting or editing an aircraft. Every original aircraft's complete parsed unit, group settings and route data remained equal across the saved four- and seven-aircraft outputs. Both outputs also retained their corresponding input aircraft inventories exactly. This isolates content compatibility; it does not implement take association or prove that every interactive editor operation is free of incidental changes.
- **Group reorder round trip:** a controlled fixture reversed the seven numeric group-array entries while preserving group/unit IDs and all aircraft content. Mission Editor loaded and saved that order unchanged. The complete aircraft inventory compared equal to the normally ordered saved fixture, while the array order was reversed. Therefore an array index cannot be a durable aircraft locator. This is an externally arranged group order followed by a real editor round trip, not an in-editor drag/reorder gesture or a within-group leader reorder.

### Source-derived findings

Paths below are under the locally installed `D:/DCS World`. Vendor source is not copied into this repository.

| Behavior | Evidence | Implication |
| --- | --- | --- |
| Aircraft serialization creates explicit-field group and unit tables | `MissionEditor/modules/me_mission.lua:3921`, `:3982`, `:4031` | Arbitrary custom unit/group UUID fields are not a durable mechanism. |
| Mission-root serialization also constructs an explicit table | `me_mission.lua:4511` | Do not rely on arbitrary mission-root fields surviving. |
| Rename updates names and name indexes | `me_mission.lua:5886`, `:5903` | Numeric IDs are useful correspondence hints during rename, not identity proof. |
| Copy recursively clones a group then replaces names and IDs | `MissionEditor/modules/me_copy_paste.lua:281`, `:317` | Copying can duplicate custom in-memory markers; names/IDs change by policy. |
| Load resets maximum IDs; rebuilds them from surviving objects; normal save reloads | `me_mission.lua:2313`, `:3389`, `:3438`, `:4899`; new IDs at `:5759`, `:9615`, `:9645` | Deleting the highest-ID objects, saving and creating new ones can reuse IDs. |
| Save As reaches the same serialization path | `MissionEditor/modules/me_menubar.lua:756`; `me_toolbar.lua:748`; `me_mission.lua:4809`, `:4823` | A new filename does not imply new aircraft or a new lineage. |
| Dedicated non-`l10n` archive members are tracked for repacking | `Scripts/dictionary.lua:537`, `:573`, `:622` | A nested manifest may survive saves; it still cannot certify per-aircraft edit history. |
| Root-level resources move under `l10n/DEFAULT`; unmapped resources have different preservation rules | `Scripts/dictionary.lua:555`, `:575`, `:607` | Test root and nested markers separately; never infer survival from a ZIP-only copy. |
| Hook API exposes mission filename and load callbacks | `API/Sim_ControlAPI.html:158`, `:545`; `Scripts/Hooks/webGUI.lua:274` | A host-side check is a candidate, not yet demonstrated to check the exact bytes consumed by every load path. |

Current recorder evidence: `library.py` hashes generated package files before activation. `prepare_staged_playback.py` derives the tape token from `recorded-flight.txt`. `make_staged_playback_mission.lua` embeds that token. None of these establishes authored-mission lineage or detects arbitrary changes to the generated mission at load. `recording_sink.lua` captures `source_unit_id` for native-state association; that is not historical mission provenance.

## Approved association policy and verification requirements

### Companion-owned lineage and association history

- Store a random lineage identifier and persistent aircraft-association identifiers in a companion registry. Keep immutable source and prepared `.miz` bytes, their hashes, the selected unit locator, and the mapping approved for each revision. A take points to those immutable records and the actual selected recording aircraft.
- A filename, Save As, archive marker, numeric ID or name is a hint, not sufficient proof of lineage or aircraft continuity. Joining a newly imported revision to an existing lineage is explicit. A copied manifest may offer a candidate lineage but cannot authorize the join.
- A byte-identical already-known mission can reuse its recorded mapping. For a different source revision, show the scene changes and candidate aircraft. **Require confirmation once for that revision before using an earlier take**, even when IDs and names match. Reusing that exact approved revision does not ask again. Repacking may be explained as content-identical, but remains a newly reviewed archive in this conservative first contract.
- Candidate discovery is independent of aircraft count and list position. Show all relevant candidates with location, type, livery, payload, unit/group IDs and names; never silently pick the first match. Duplicate locators, missing aircraft and ambiguous candidates block automatic preparation.
- A deliberate new association is a new revision-specific record. It does not rewrite the take's original source/prepared revision or claim that an indistinguishable recreated unit is historically the same entity. Even a retained marker cannot distinguish a copied replacement if the original was deleted. Snapshot comparison cannot recover unobserved edit history.
- If the entire resulting archive is byte-identical to a previously approved snapshot, no file-based comparison can detect the intervening delete/recreate history. Reuse in that case means reuse of the same approved scene content, not proof of uninterrupted editor-entity existence. The simulated reused-ID scenario represents a newly imported archive with matching aircraft fields; it must not be read as a detector for identical bytes.
- Removing an aircraft does not free its companion association identifier for automatic reuse. Restoring the saved scene is always available. Re-association requires explicit selection and compatibility checks; review cannot override an incompatible authored start or aircraft configuration.
- Four to seven aircraft requires no reassignment of the original four. Review the three additions, confirm the recorded aircraft in the new revision, and retain earlier mappings and snapshots. Added aircraft remain ordinary aircraft; no simultaneous playback capacity is implied.
- Legacy recordings retain their existing compatibility path and missing-provenance status. An editor ID in an old recording does not supply a source revision, prepared revision or lineage. Do not fabricate any of them.

### Meaningful comparison, separate from byte hashes

Store both exact archive hashes and a versioned semantic projection. Parse mission files as data, never execute their Lua to inspect them. Reject unsupported input forms rather than evaluating them.

Treat map/table serialization order separately from ordered behavior. Aircraft/group container reorderings may be compared by validated unique locators; route waypoint order, action order and task order remain significant. Group membership and leader changes are meaningful even when they result from a reorder. Duplicate IDs/names must be surfaced. Localization/resource indirection must be resolved before claiming textual equality. Unknown fields or resource changes are reported as unclassified, never silently ignored as safe.

For a recorded aircraft, compare type, coalition/country, livery, payload and aircraft properties, authored location/altitude/heading, start mode, airfield/parking/carrier attachment and relevant group/start settings. Establish numeric tolerances only from observed round trips; until then, unexplained differences require review or refusal, not a guessed tolerance. Unsupported terrain/weather/build/configuration and changed recorded-aircraft authored placement refuse preparation. Selected-aircraft task/trigger compatibility remains governed by [Define compatibility with authored triggers and aircraft tasks](https://github.com/caw1517/DCSRecorder/issues/19).

Scene review covers added/removed/moved other aircraft and objects, player position, resources, time/weather, scripts, triggers and other mission settings. Review does not certify arbitrary script safety or collision clearance. Keep preservation checking separate from association checking: unselected mission contents must still survive preparation.

The recorded first pose belongs to the take, separately from the authored spawn. Beginning recording after taxi does not make the two positions equal. Neither newer-scene selection nor aircraft re-association translates the measured path.

### Generated-file verification boundaries

1. At preparation, hash the actual source snapshot, compare its semantic projection with the saved revision, validate the explicit mapping, and create an immutable generated copy. Record its exact archive hash in an external preparation record along with take identity and build/profile information. The expected hash must not be derived from an editable manifest inside the file it is verifying.
2. Before activation, verify the package against that record, as the present code already does for its generated files.
3. Investigate a trusted companion/GUI-hook check at mission load. It must identify and read the intended generated archive, compare exact bytes, and tie the result to this load session and take. Missing checker, missing record, unreadable archive or mismatch must leave recording/playback unverified and refuse start. The native/mission handshake needs a session-specific approval before release; the current tape token alone does not implement that gate.
4. A read of `getMissionFilename()` proves only what was read from that path at that moment. It is not proof of which bytes DCS consumed. The installed API documents a filename and load/start callbacks but supplies no byte-consumption or atomic verification guarantee. Test callback timing, temporary Mission Editor test-flight files, restart, replacement during load and old approvals before declaring a supported load path. Until then, runtime checking is **unproven**, with **no verified runtime load path**. The existing preparation/activation hash check is the current verified boundary; it must not be presented as runtime mission verification.
5. A valid initial archive hash does not detect or authorize later script-driven world changes, dynamic spawn/movement, native mods or changes after verification. A missing/removed in-mission checker cannot report its own absence; enforcement must be outside the editable copy. No universal edit detection or hostile tamper resistance is promised.

Recovery text: **“This mission copy changed, or its identity could not be verified. Open the authored mission in Mission Editor, save it, and generate a new recording/playback copy in DCS Recorder. You can also use the scene saved with this take. The recorded flight has not been changed.”**

## Live round-trip protocol and remaining checks

Use only scratch copies generated by `mission-identity-probe.prototype.py`. Never overwrite an authored original. Keep the before/after archives and a short observation log; snapshot each output with the probe. For each step record DCS build, operation, output filename, unit/group IDs and names, configuration/placement differences, marker survival and resource inventory.

| Step | Action | Evidence status |
| --- | --- | --- |
| Baseline | Generate four-aircraft fixture from a local existing practice mission | Completed, synthetic fixture |
| ZIP control | Repack without running Mission Editor | Completed; archive changed, parsed mission/inventory unchanged |
| Open/save | Open fixture in Mission Editor and Save As to a fresh file | Observed; snapshot 03 |
| Re-save | Save, explicitly reopen and save again | Observed; snapshots 04 and 09, extra fields changed as documented above |
| Rename | Rename one unit and its group; preserve a separate evidence copy | Observed; snapshot 05 |
| Add | Add three aircraft and compare original starts/configurations | Initial UI sequence changed extra fields; controlled fixtures and real saves 14–15 retained all original aircraft data exactly |
| Reorder | Change container order and round-trip through the editor | Observed for externally reversed group entries, snapshot 16; all aircraft data equal. Within-group leader/route/task order remains meaningful, not ignored |
| Duplicate | Copy/paste a group and save | Observed with user-operated shortcut, snapshot 13; copy received new IDs/names and original seven aircraft remained equal |
| Delete/recreate | Remove highest-ID aircraft, save/reload, create a replacement; compare IDs | Observed; snapshots 07–08 confirm ID/name reuse |
| Preservation | Compare custom unit/root fields and root/nested archive resources after editor saves | Observed; nested marker retained through snapshot 09, custom fields/root marker lost on first Save As |
| Runtime | Observe a valid generated load, edited copy, archive repack, missing checker, restart and Mission Editor test flight | Normal load, post-load replacement and Fly Again observed below. Separate edited/repacked loads, missing checker and editor test flight remain pending; production load verifier is not implemented |

Example commands (use an available Python 3 executable):

```text
python companion/mission-identity-probe.prototype.py seed INPUT.miz SCRATCH.miz --output seed.json
python companion/mission-identity-probe.prototype.py snapshot BEFORE.miz AFTER.miz --output roundtrip.json
python companion/mission-identity-probe.prototype.py repack INPUT.miz REPACKED.miz --output repack.json
```

`seed` and `repack` refuse to overwrite a destination archive. The parser supports only the serialized Lua data subset needed for this bounded probe; it is not a production parser. The scratch fixture removes the old recorder triggers and adds unknown-field/resource sentinels solely for preservation experiments. Do not fly it. Raw `.miz` files, vendor sources and full mission snapshots stay local.

## Runtime observations in progress

The separate `mission-identity-load-hook.prototype.lua` compares the bytes at `DCS.getMissionFilename()` with an external reference captured at hook startup. It also reads the description marker from `DCS.getCurrentMission()`. This is a read-only diagnostic, not recorder authorization or enforcement. Sanitized callback lines are in `mission-identity-runtime-observations.prototype.log`.

- Normal Mission-menu load: load-begin, load-end and simulation-start reported `MATCH / ORIGINAL` for the frozen valid copy.
- Replaced that disposable archive with the edited variant after load: the frame diagnostic reported `MISMATCH / ORIGINAL`. The named file changed while the loaded description remained original.
- Quit to debrief and selected **Fly Again** with the edited archive still at that filename: all three new load callbacks reported `MISMATCH / ORIGINAL`, and the new in-cockpit briefing visibly showed the original description. This observed restart path reused original mission content; it did not load the replacement description from the named archive.

These observations disprove treating a path-byte comparison as sufficient evidence of loaded content. They do not prove every mission field is retained or that every restart path behaves identically. The description marker is a deliberately bounded discriminator, not a semantic digest or trust anchor. There is still no verified production runtime approval path.

Capture then failed repeatedly with `FrameArrived timed out`, including after the user brought DCS forward and the window was reacquired. Further UI input stopped. The disposable `020` archive was restored to the frozen valid bytes. The task's separate diagnostic hook and external reference were removed from Saved Games; existing hooks were untouched. The already-running DCS process still needs a normal exit to unload callbacks. Raw evidence archives remain local. The optional startup-script log was not observed, so no mission-script execution assertion is based on it.

## Resolution gate

The user's policy approval is complete. Copy/paste, group-container reorder and controlled compatible-additions evidence are complete within the stated bounds. Do not close the decision ticket yet: the runtime investigation still lacks a separate edited/repacked load, the Mission Editor test-flight path and missing-checker coverage. Resume those bounded probes after capture recovers, without requesting the same policy approval again. Reinstall the separate diagnostic only for the next experiment and remove it afterward. Implementation and full-flight evidence gates remain open independently of this decision.
