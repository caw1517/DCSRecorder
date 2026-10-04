# Mission edit, behavior and loaded-session enforcement — live evidence

Work on [Enforce mission edit, behavior and loaded-session compatibility](https://github.com/caw1517/DCSRecorder/issues/26).
DCS 2.9.30.28536, 4 October 2026 (UTC; evening of 3 October Pacific). The user operated DCS
one step at a time; the agent prepared files and inspected logs. Raw archives
and full logs stay local (`*.miz`, `*.log` are ignored); the lines below are excerpts.

Take `20261004T015146Z-0001` (SHA-256 `559faa0a…`), recorded in revision 1 of the
`060-Lineage-Four` lineage (scene `0c26613d…`). The user added one Hornet in
Mission Editor (task changed from CAP to Nothing; automatic EPLRS and option 35
kept), saved `061-Enforcement-Auto.miz`, confirmed Record Hornet in the companion
(revision 3, `0189c3a7…`), and generated playback with the new Hornet as player.
The companion listed both automatic actions as kept unchanged.

## Results

| Run | Setup | Result |
| --- | --- | --- |
| 1 | Valid prepared copy, first load model | **Refused (fail-closed)**: `loaded_mismatch:coalition[blue][country][1][plane][group][8][radioSet]:unexpected`, then `FAILED,identity_unverified`, recovery text shown, hold cleaned. A model gap, not a mission edit. |
| 2 | Same mission regenerated after the model fix (byte-identical, `9bed2817…`) | READY → COUNTDOWN → REQUEST/COMMIT/PLAYER_RELEASED (same ms) → NATIVE_RUNNING → COMPLETE. User: normal. |
| 3 | Briefing text edited in the installed copy (`4a3394d3…`), same name | **Refused**: `loaded_mismatch:localized_description:value`, `FAILED,identity_unverified`. |
| 4 | Valid bytes restored on disk while edited content loaded; **Fly Again** | **Refused**: new session, still `localized_description` mismatch. The named file hash matched the approved prepared copy while DCS used cached edited content. |
| 5 | Full DCS restart, valid copy | New session; READY → release → COMPLETE. |
| 6 | Release-check hook moved out of `Scripts/Hooks`, full restart | No hook/bridge lines; `FAILED,identity_unverified`, hold cleaned, later F10 Start → `START_REFUSED,failed`. Hook restored byte-identical (`89be5f77…`) with DCS closed. |

Every hook session logged its binding, e.g.
`START,1791081942_1,take=559faa0a…,prepared=9bed2817…,scene=0c26613d…`.

## Findings fixed during the run

- **EPLRS `groupId` is a datalink network number**, not the mission group ID
  (`me_action_db.lua` `getNewTblGroupIdForEPLRS`: first free 1–99 among airborne
  groups, else 0). The real save used 1. The classifier accepts an integer 0–99.
- **CAP task default set**: an automatic `EngageTargets` task plus options 17/18/19/21.
  It remains refused by name. Changing the task to Nothing in Mission Editor leaves
  only EPLRS and option 35.
- **Load-time `radioSet`**: `me_mission.lua` `fixRadio` sets `group.radioSet = group.radioSet or false`
  on load. A newly placed group is saved without it. `loaded_reference.py` now
  models that (plus `communication` defaulting to true; an unset frequency or
  modulation refuses preparation as unobserved). The six earlier real loads still
  match exactly.

## Boundaries

Bounded to the airborne authored profile, Caucasus, zero wind and one playback
aircraft. A ZIP-repack-only control was not repeated in this integrated run:
preparation is deterministic, and repacking was covered by the session-guard
control. Mission Editor test flights (`tempMission.miz`) are not a supported
playback path. No universal tamper detection or arbitrary-script certification is
claimed. Ground staging, taxi and parked completion remain later tasks.
