# Hot-ground source and staging validation

Work on [Prove hot-ground staging and first taxi movement](https://github.com/caw1517/DCSRecorder/issues/23).

First obtain a short real hot-start take using `047-Hornet-Hot-Ground-Capture.miz`.
The fixture reuses the tested stock Hornet hot-parking location at Kobuleti
(parking 15), Blue Angels livery, Caucasus, zero wind and DCS 2.9.30.28536.
It uses the installed complete v7 capture workflow; source CSVs remain unchanged.
No playback eligibility guards have been widened.

`contact.lua` wraps the existing mission sample function and records paired
`DCSGROUND,1` rows in DCS.log: take, row, exact motion timestamp, unit identity,
in-air flag, terrain elevation, aircraft-origin AGL, life, initial life and
surface type. Aircraft events are retained separately. Missing contact fields
fail the recording as incomplete rather than producing unsupported evidence.
Origin AGL is not wheel clearance; in-air state and animation are not by
themselves a proof of stable physical contact. Retain the full raw log and CSV
and inspect visible contact during subsequent playback.

`prepare_capture.py` retains both source archive hashes and original ground
placement, verifies the installed aircraft dependency and route validator,
checks installed lighting command definitions, and executes the actual packaged
recorder in `check_capture.lua`. This covers stream timestamp/row alignment,
duplicate callbacks, changing contact/damage, normal stop, and evidence failure.
These are offline checks, not simulator acceptance.

`Install-Capture.ps1 -PackageDirectory <package> -ValidateOnly` checks the mission
hash, simulator build and all five installed recorder dependencies. Installation
adds just the named mission with overwrite refused and writes a hash receipt.
DCS must be closed for installation.

## Live progression

The agent prepares and inspects evidence; the user operates DCS one check at a
time. First load the capture mission and verify the stock Hornet is parked with
engines running. Then capture a few seconds stationary, a short straight taxi at
walking speed, and a few seconds stationary after braking; stop with F10. Leave
DCS open for collection. The normal companion will still reject a ground take
for playback; the separate ground-control experiment must be implemented after
reviewing this source.

Use the real take for the separate held/release package. Remaining acceptance:
original pose and full initial snapshot, 30-second hold while surrounding mission
activity continues, three-second countdown, first taxi motion, stable contact
and no unexplained damage or state change, retained logs and user visual/audio
review. Coordinate contact results with the physics issue. Parked completion
and longer taxi/takeoff/landing support belong to later tasks. Keep this task
open until its actual live acceptance is established.
