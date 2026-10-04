## Live validation checkpoint — draft decision remains open

DCS window access recovered. On build 2.9.29.27468, live Mission Editor operations were performed on disposable scratch copies only: Save As, save, unit/group rename, four-to-seven aircraft additions, highest-ID deletion followed by save and recreation elsewhere, and explicit reopen/save. No flight, installed-hook change, original-mission edit or production implementation was performed.

Observed:

- Initial Save As retained four unit/group IDs and names. Arbitrary mission-root and aircraft UUID fields disappeared; a root ZIP marker disappeared; the nested `DCSRecorderProbe/identity.json` survived every observed save.
- Renaming retained numeric IDs. Adding three Hornets retained the original IDs, names and authored positions, creating units 10115–10117/groups 10105–10107.
- The four-to-seven sequence also changed existing aircraft configuration: radio channel 305→124, removal of `hardpoint_racks=true`, addition of `payload.ammo_type=1`, and empty waypoint properties. The sequence included selection/centering, so causes were not isolated. This is evidence for count-independent candidate correspondence, not proof that existing configurations remained compatible or that take preservation is implemented.
- After deleting the highest-ID aircraft and saving, its replacement reused unit ID 10117, group ID 10107, unit name `Aerial-3-1` and group name `Aerial-3`. Old and replacement aircraft data differed only in unit/group/first-waypoint coordinates. IDs and names are therefore demonstrably insufficient identity proof.
- A resave with no object placement retained the aircraft inventory while changing `currentKey` and failure-entry IDs. Explicit reopen/save retained all seven IDs/names but added `radioSet` to the replacement group. These differences remain reported; no blanket normalization rule is justified.

Published evidence at commit `93840dc` on `codex/prototype-mission-identity`:

- [Updated observations, proposed contract and remaining protocol](https://github.com/caw1517/DCSRecorder/blob/93840dc/companion/mission-identity.prototype.md).
- [Compact machine-readable observations with archive hashes and changed paths](https://github.com/caw1517/DCSRecorder/blob/93840dc/companion/mission-identity-observations.prototype.json).
- [Interactive association-policy prototype](https://github.com/caw1517/DCSRecorder/blob/93840dc/companion/mission-identity.prototype.html).

The user-facing proposal is **one authored mission containing seven jets**, with per-aircraft takes and companion-managed revision/generated-copy history. It does not require seven separately maintained authored missions. Simultaneous playback layers remain deferred. Proposed policy remains confirmation of the intended aircraft once per changed revision, with repeat use of that exact approved revision retaining the mapping. Incompatible authored starts/configurations refuse preparation; immutable saved scenes offer recovery.

Remaining: live copy/paste and reorder coverage, an isolated compatible-only additions case, user review of the policy/prototype, and the supported generated-file load-verification boundary. Automated Ctrl chords did not reach DCS as intended, so no live copy result is claimed. This fixture uses airborne starts, not ground playback. Runtime verification is unimplemented/unproven; a file hash does not certify the exact bytes DCS consumed or later script-driven changes. HTML visual automation remains unverified because browser URL policy rejected its local-file preview.

All archived stages were parsed successfully as data; the sanitized observation JSON was generated from those archives, and the staged diff check passed. Raw `.miz` files and detailed snapshots remain local. Keep this ticket open and retain its claim; no resolution or map decision has been added.
