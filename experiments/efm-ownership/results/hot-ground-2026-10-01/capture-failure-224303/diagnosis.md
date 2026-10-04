# Ground capture automatic-stop diagnosis

The first actual capture ended with `invalid_sample,0` immediately after
`DCSGROUND,1,ERROR,...,ground_evidence_unavailable`. The incomplete CSV has no
sample rows and must not be used as a playback source.

The read-only live sensor probe reported `Unit:getID()` as type `string`, value
`1`. In-air was boolean false; health and initial health were 20; aircraft-origin
height was 46.843018461231 m; terrain height was 45.010047912598 m; surface type
was numeric 5. All sensor calls succeeded. Executing the original sensor block
in the same live probe failed its numeric validation on the unconverted ID.

Regression: changed the packaged-recorder fixture to return the observed string
ID. Running `check_capture.lua` against the original `capture-package/mission.lua`
fails the first-row assertion, reproducing the automatic stop. The original
fixture's numeric ID had hidden the actual DCS boundary.

Fix: normalize the unit ID with `tonumber`, then require a finite positive
integer. Other sensor requirements remain strict. Validate all seven fields by
index so a missing field cannot terminate `ipairs` and hide later missing data.
The same regression passes against the rebuilt `capture-package-v2/mission.lua`,
along with duplicate callbacks, changing contact/damage values, stop and invalid
sensor refusal. Installed-aircraft, route and light-command checks pass too.
No diagnostic logging is added to the repaired capture mission. The temporary
sensor mission and its raw log remain isolated diagnosis evidence.

This fixes the reproduced input-type defect. A new user recording is still
required; it is not a live capture or ground-playback acceptance result. No
low-speed playback guards were changed. The original failed mission, partial
CSV and logs are retained. The sink's stale RECORDING status after an incomplete
take is a separate observed display issue, not the cause of this automatic stop.
