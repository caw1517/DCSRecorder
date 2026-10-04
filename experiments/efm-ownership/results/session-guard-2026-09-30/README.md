# Loaded-session control: prepared, awaiting DCS

Implementation started after the user approved the handoff for
[Complete Hornet mission setup and hot-start parking-to-parking playback](https://github.com/caw1517/DCSRecorder/issues/11).

The session gate and additive control hook are implemented. Six mocked
hook/mission cases pass: valid release, missing bridge, changed loaded description
at the same filename, changed aircraft placement, expired response and restart.
Additional assertions cover missing checker, package/sequence mismatch,
duplicate request/approval, nonfinite response clock and exact table-key types.
These execute the actual module and hook with mocked DCS APIs.

The generated embedded mission script also passes initialization, missing-checker
refusal and matching-session release under the bundled Lua runtime. A temporary
test harness initially contained an incorrectly escaped newline; correcting that
harness produced the pass without changing the mission script. The repacked
control has identical ZIP entries; the edited control changes only the dictionary.
The source archive is read only. `git diff --check` passes.

Installation completed with DCS closed on build 2.9.29.27468. Six installed hashes
were verified. New files only: a separate hook, module, external expected data,
and valid/edited/repacked missions. Existing hooks, modules, missions and
`autoexec.cfg` were not replaced. Local `installation.json` records paths/hashes.

## First live run and bridge correction

The user reported **Release blocked: unverified**. The 30 September log shows
the hook and mission script initialized, then at 04:00:01 UTC the bounded loaded
fields matched. The user-hook context had `a_do_script=nil`; approval delivery
therefore never armed the mission gate. This is a bridge failure, not a mission
comparison failure. The gate correctly stayed closed.

The regression command in the control README was extended to model separate
hook and mission contexts. Before the fix it failed with the user's exact
`Release blocked: unverified` symptom. Routing through the existing
`net.dostring_in('mission', 'return tostring(a_do_script(...))')` bridge fixes that
mocked case. The expanded suite also refuses missing/denied bridges and transport
success without a gate acknowledgment. No configuration or sandbox changes.

## Second live run: mission reached, acknowledgment absent

At 22:13:25 UTC on 30 September the loaded fields matched. The mission reached
`ready`, logged its request at 22:13:52.611, then expired to `refused` at
22:13:53.661. The hook never logged `ARMED`, `ANSWER` or a callback error.
Thus the call reached the mission but the expected return acknowledgment did
not reach the hook. The user reported **Refused**. Relevant lines are retained
in `second-live.log`; unrelated third-party errors are excluded.

The regression suite reproduced `dropped_return: refused` when the actual
bridge wrapper executes its target but drops the result. The hook now consumes
fresh package/session-bound mission log acknowledgments and reports answer
delivery separately from acceptance. Twelve integration cases pass, including
dropped returns at either bridge layer and refusal when the mission
acknowledgment itself is absent. The timeout remains one simulation second.

## Third live run: valid diagnostic release passes

The user reported **released**. The 30 September log confirms a new session,
matching loaded fields, mission-emitted arming acknowledgment, one request,
one diagnostic release and `ANSWER_ACK ... accepted=true`. Request and release
were logged at 22:19:46.271 and 22:19:46.272 UTC respectively. The mission reached
`phase=released`. Relevant evidence is retained in `valid-release.log`.

This establishes the bounded valid-mission bridge/gate path on the pinned build.
Changed-content refusal, repacking, disk replacement, restart and missing-checker
controls still require live evidence. Next is `031-Session-Guard-edited.miz`:
request guarded release and expect refusal due to the translated briefing change.
The installed edited fixture hash matches the generated manifest.

## Fourth live run: localized edit refused

The user reported **refused**. The new session's comparison returned
`false:localized_description:value`. At 22:21:56.838 UTC the checker sent
`allowed=false` for the matching request; the mission acknowledged `false` and
entered `phase=refused`. There was no release in this session. This was an
explicit content refusal, not a timeout. Evidence: `edited-refusal.log`.

Next is `032-Session-Guard-repacked.miz`: identical archive entries with different
ZIP packaging should release. Its installed hash matches the manifest. No DCS
process restart or installed-file change is required for this control.

## Fifth live run: repacked control releases

The user reported **released**. Session `1790807044_3_358565` matched the loaded
fields, received a fresh mission acknowledgment and released once at
22:24:23.800 UTC. The checker recorded `allowed=true` and `accepted=true`.
Evidence: `repacked-release.log`. ZIP packaging changes alone do not prevent
release in this bounded control.

Next: prepare a separate `033-Session-Guard-DiskSwap.miz` from the edited control.
Load it and pause before requesting release; replace only this disposable file
with the frozen valid archive while the edited content remains loaded. The
expected result is still refusal for the loaded translated briefing. Preserve
all three existing controls and source archives. No disk replacement has yet
occurred as part of this step.

## Sixth live run: disk replacement cannot approve loaded edited content

The user loaded the disposable edited copy and paused before requesting release.
The log confirmed session `1790807175_4_488690`, a translated-description mismatch
and a ready gate. At 22:26:56.977 UTC, only `033-Session-Guard-DiskSwap.miz` was
replaced with the frozen valid archive. Its SHA-256 was verified as
`000e997795699cf19a03b225e270804ad58fc1f8ca6ca9c53e0c457ad1e15c97` before the
request and again after refusal. The edited bytes are preserved locally.

After unpausing without reloading, the user reported **refused**. At
22:27:49.063 UTC, the same session received `allowed=false` with reason
`localized_description:value`, acknowledged `accepted=false`, and entered
`phase=refused`. There was no release. The decision correctly followed the
loaded edited content despite the valid named archive on disk. Evidence:
`disk-swap-before-request.log`, `disk-swap-refusal.log` and local `disk-swap.json`.

Next: exit to debrief and choose **Fly Again**. Inspect the initial gate state
before any request: it must start fresh rather than retaining the refused state
or releasing automatically. Observe whether DCS reuses edited loaded content or
loads the valid disk content; subsequent authorization must match that result.
The disposable disk file deliberately remains valid for this restart control.

## Fly Again: fresh session, cached edited content

The user reported **ready** after Fly Again. At 22:30:05.874 UTC a new session
`1790807406_5_719874` began, received its own arming acknowledgment and entered
`phase=ready`. No request or automatic release appeared. The comparison still
returned `false:localized_description:value`: this restart retained edited
content despite the valid named file on disk. Evidence: `restart-ready.log`.
The user then requested release and reported **refused**. At 22:31:27.475 UTC
the new session received `allowed=false` for `localized_description:value`,
acknowledged `accepted=false` and returned to refused without releasing.
Evidence: `restart-refusal.log`. The old refusal was not retained as initial
state; the new request was checked independently against the cached loaded edit.

Next is the missing-checker control. Temporarily move only the verified
diagnostic hook outside `Scripts/Hooks`, preserve its bytes and record the move.
After a full process restart, load the valid mission and request release:
expected `Release blocked: unverified`, with mission initialization but no
checker installation, arming or release. Restore the hook after retaining
evidence, before any subsequent checker-dependent experiment.

## Missing checker: release remains blocked

After a full process restart, the user reported **blocked** when requesting
release in the valid control. The new log contains mission initialization and
`phase=unverified`, with no checker installation, arming, request or release.
The active hook file was absent and its preserved copy retained the verified
hash. Evidence: `missing-checker.log` and local `missing-checker.json`.
Log timestamps 00:10–00:11 UTC on 1 October correspond to the afternoon of
30 September in the user's Pacific timezone.

The identical checker hook has now been restored on disk. It will load after
the next full DCS restart. The user subsequently closed DCS.

Build attribution: the missing-checker log identifies DCS 2.9.30.28536, newer
than the initial installation check. Version headers were not retained for
every earlier control excerpt, so those runs must not all be attributed to the
old build. Native compatibility with the new build remains unverified.

The bounded control matrix now has live evidence for valid release, changed
briefing refusal, repacking, loaded-content/disk-file divergence, fresh Fly Again
state and missing-checker refusal. This does not establish general mission
identity, hostile-tamper resistance, other DCS builds or native authorization.

This establishes neither full mission identity nor native release authorization.
Read the [control scope and protocol](../../session-guard/README.md). Real-aircraft
held staging, common clock integration, complete state holds and ground behavior
remain implementation work. All implementation/acceptance issues remain open.
