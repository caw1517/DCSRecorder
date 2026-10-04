# Held-start preparation and build-compatibility history

The installed DCS version is 2.9.30.28536. The native controller remains pinned
to its previously validated build. Package preparation refused the new build;
no held-start module was installed. Offline callback, held-state policy and
session authorization checks pass, but no live hold has been validated.

`installed-export-check.json` records changed WorldGeneral function addresses.
Updating those two addresses alone would not validate the native integration.

A separate stock-Hornet mission, `045-Build-Compatibility.miz`, and read-only
capture helper are prepared in the ignored `compatibility-package` directory.
The helper's non-DCS host refusal check passes. Hook checks pass for unrelated
missions, missing player, one-shot activation and stop cancellation. All three
files were installed with DCS closed on 2.9.30.28536 and their hashes verified;
the local installation receipt records the paths.
Raw executable sections must remain local in ignored directories.

## Captured and audited

DCS 2.9.30.28536, process 29516: the live capture reported all five modules and
fifteen sections. Section lengths and SHA-256 hashes are retained in
`compatibility-audit.json`; the filtered DCS log is `compatibility-capture.log`.
The temporary capture hook was moved out of Hooks after DCS closed, preserving
its verified bytes. The DLL and raw capture remain local.

Only 4 of the 33 inventoried byte guards match at their old addresses. Both
primary-vtable boundary checks fail there. The presentation pitch load now
references offset 0x4dcc rather than 0x4db4. Updating export addresses alone
would therefore be insufficient. No playback guards or offsets were changed.

The candidate map passes 33 static byte checks and 10 structural checks,
including the primary table boundary and physics/animation/engine slot targets.
This is evidence for a port, not live compatibility. DCS and WorldGeneral's
captured exception sections do not provide valid function bounds; no function
boundaries are inferred from those sections. Raw bytes are complete but their
exception tables are unusable for this purpose.

The next bounded check uses a separate `HornetLayoutProbe` module with normal
AI flight, no native method calls, no object writes and no hooks. It compares
native object identity, position, velocity, engine count and presentation fields
with mission-side telemetry before enabling any hold controller. The generated
mission passes installed DCS dependency, route and aircraft validators.

The actual diagnostic DLL passes non-DCS host refusal, zero SDK access, sample
throttling and destroyed-object isolation checks. Its packaged mission script
passes initialization, independent telemetry and twenty-second completion checks.
All nine new module/mission files were installed with DCS closed and verified
against package hashes. The temporary capture hook remains disabled. Live
object-layout evidence is pending from `046-Hornet-Layout-Check.miz`.

## Read-only layout passed; user chose the normal companion trial

The user completed the read-only aircraft run on build 2.9.30.28536. All 208
native samples passed the build/identity/read guards; the mission emitted 200
samples and completed normally. The probe had a null FM and two engines. The
observed callback phase difference was 20 ms: after interpolation at that offset,
position disagreement was at most 0.008795 m and velocity disagreement at most
0.010510 m/s. Unaligned position disagreement was about 4.5 m. This establishes
the read correspondence, not setter/hook or first-frame behavior. Full metrics
and raw-log hashes are in `layout-comparison.json`.

The user then requested a normal record-to-playback trial through the companion,
instead of the held-start test. The hold module remains uninstalled. A separate
`HornetWheelsTrial2930` controller and version-specific engine/smoke capture DLLs
were built. The native profile changes apply only to explicitly selected new-build
targets; the ordinary profile still uses its original addresses and build gate.
The cockpit accessor moved to 0x404ec0 with a changed RIP displacement, and three
smoke guard sites moved by 0x290; their full guard patterns were checked against
the retained capture before compiling the separate helpers.

Verification: 34 existing CTests passed before the companion steering; the added
held mission lifecycle check passed separately. All three new companion-trial
native CTests passed. Three new companion tests cover the new helpers, saved
capture metadata, playback packaging/activation, practice metadata and rejection
of unknown builds/legacy modules. The 37 legacy companion tests pass with the
installed-version read mocked to their old build fixture. Running those tests
unmodified on the actual updated install correctly hits ten old-build gate errors;
this is not a live compatibility result.

The installer verified 14 installed hashes and preserved 879 other files. Exact
backups of the previous autosave/capture scripts and settings are in the ignored
`companion-trial/backup` directory. Existing capture DLLs and playback modules
were preserved. Settings explicitly select `build_trial: 2.9.30.28536`. The
normal companion is running with a trial banner; its library API reports a
matching installed autosave hook. No new user flight has yet been recorded or
played back on this profile. Live end-to-end acceptance remains pending.

## First companion take: batched capture interrupted autosave

The first new-build take started at 2026-10-01 02:16:36 UTC. Autosave failed
after 2,919 rows (58.36 seconds), reporting an engine observation more than
50 ms after its motion row. The mission continued to user Stop at 6,091 rows.
Only one of the three retained partials came from this trial. The partial and
full DCS log are preserved locally in ignored `companion-trial/failed-recording`.
Native observations after the failure were not captured and cannot be recovered
from the motion log. The take remains incomplete.

The log shows a short delivery burst around the failure. An integrated Lua
regression reproduced the same failure with four motion rows consumed in one
frame. New trial practice missions now explicitly declare `frame-batch-v1`:
the initial engine/smoke observation remains bounded to 50 ms; subsequent
observation lag and native clock gaps are bounded to 150 ms. Every motion row
and actual native timestamp is retained. Existing engine interpolation and
measured smoke transition timestamps are preserved. Identity and position
association checks remain active. Undeclared recordings retain the 50 ms
policy; unknown timing profiles and mismatched builds are rejected.

All three new batching regressions, three build-trial tests and 37 legacy
companion tests passed (legacy installed-version lookup uses its old fixture).
The three Lua updates were installed with exact backups; hashes verified all
893 protected files unchanged. The companion restarted and its library API
confirmed the installed hook matches. A fresh live record-to-playback run is
still required; these offline results do not establish live acceptance.

## Companion update accepted live — 30 September 2026

The user completed a fresh recording and playback on DCS 2.9.30.28536 and
accepted the update. They reported fluid playback, working gear, spoilers and
smoke, and smooth, easy formation flying. This accepts the normal airborne
companion workflow on the updated build; held staging and parking-to-parking
acceptance remain separate unfinished work.

The saved recording `20261001T023512Z-0001.csv` passes the recording validator:
2,863 samples over 57.24 seconds, version 7 with all current capture channels,
the new build and `frame-batch-v1` timing metadata. Its SHA-256 is
`1eaf682fd8aefd669c8bb1b3968357fd4ab777e3539fb9bb16030adc541f50b7`.
Maximum engine and smoke observation lag was 34 ms in this successful take;
it does not itself exercise the relaxed midflight timing bound.

The playback log identifies the new trial DLL and reports `NATIVE_STARTED`
at mission time 6.820 and `COMPLETE` at 64.080. Smoke ON/OFF events were applied
at playback times 36.800 and 40.140 seconds for recorded times 36.783 and
40.124 seconds. The recording, playback log snapshot and installed tape metadata
are preserved locally under ignored `companion-trial/accepted-flight`.
Visual smoothness and gear/spoiler behavior are user acceptance evidence;
these checks do not constitute a new numerical audit of every state channel.

## Held-staging task claimed and control installed — 30 September 2026

[Prove visible airborne held staging](https://github.com/caw1517/DCSRecorder/issues/20)
is the first implementation task under the parking-to-parking milestone. The
user closed DCS normally before installation. The installed build still matches
the package's exact 2.9.30.28536 profile.

The four held callback, initial-state policy, mission-lifecycle and presentation
boundary checks passed. The packaged DLL matches the tested Release DLL at
SHA-256 `23df85f99addea68d379bb646540cc5e04f63ce4fcc966dc18bc1d6b9c653d72`.
All eleven manifest file hashes passed, along with the installed DCS dependency,
three-aircraft route and aircraft-configuration validators.

The additive `held-start/Install-Control.ps1` installed eleven files: the
separate `DCSRecorder-Hornet-Held-Test` module and
`040-Hornet-Held-Start.miz` in Saved Games/DCS/Missions. Installation verified
every new hash and 1,074 existing runtime/user files unchanged. No existing
module, companion setting, capture hook or recording was replaced. The exact
local receipt is `package/held-installation.json`.

Next live check: open the mission and click Fly. Leave the automatically
requested Active Pause unchanged. Observe the real lead for thirty seconds
while the stock witness continues flying, then exit normally on the observation
completion message. Retain DCSR_HELD mission telemetry and the module's
probe-logs, plus the user's drift/flicker/sound observations. A FAILED notice is
a failed check: exit and inspect the evidence before another attempt.

Live held staging remains unverified. This diagnostic has no release/countdown,
ground staging or parked completion; it does not close any of those later tasks.

## Subsequent live hold accepted

The user completed the observation and confirmed the lead stayed perfectly
still while the witness flew away, with steady engine sound. The
[bounded held-staging evidence](../held-staging-2026-09-30/README.md) records
301 mission samples over 30 seconds with zero sampled pose drift and replay
time held at zero. This supersedes the pending status above for the hold-only
control; the complete snapshot/release and ground tasks remain open.
