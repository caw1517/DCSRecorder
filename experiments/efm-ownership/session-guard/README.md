# Loaded-session authorization control

First implementation boundary for [Complete Hornet mission setup and hot-start
parking-to-parking playback](https://github.com/caw1517/DCSRecorder/issues/11).
This control uses one stock Hornet. It neither starts a recording nor activates
native playback. A successful diagnostic release displays a message only.

`companion/session_guard.lua` contains the closed-by-default, single-use gate.
The external hook arms each session with a fresh token, consumes only requests
from that session, and compares loaded data again at the release boundary.
Approvals must match the package, session and pending sequence and arrive within
one second of simulation time. Restart discards pending requests. Duplicate
requests and approvals cannot release twice. A missing checker or bridge cannot
release. Model time keeps actual simulator pause from consuming this deadline.

The integration control compares loaded theatre, weather, aircraft/scene tables,
authored trigger rules, date, start time, forced options and the **translated**
briefing description against an external generated reference. It does not read
the archive named by DCS to make this decision. The filename selects the
disposable fixture only. A description-only localization change therefore has
to fail even when the named file on disk matches the original.

This is a bounded identity check, not full mission authorization. Resource bytes,
other localized fields, mission options, executable trigger representation and
arbitrary script effects remain outside its coverage. Native playback must not
consume this diagnostic approval. Production support requires a complete
supported-content contract and the native release/hold boundary. No held staging,
ground contact or state-fidelity evidence is established by these files.

The bundled `D:/DCS World/API/Sim_ControlAPI.md` documents loaded mission access,
translated description access and `a_do_script` return values. The first live
run proved that `a_do_script` is absent from the user-hook context, while the
bounded loaded fields all matched. The corrected hook uses the existing
`net.dostring_in('mission', ...)` bridge to invoke `a_do_script` in its proper
context. The second live run reached `ready` in the mission, but the hook never
observed a scalar acknowledgment and requests expired. It now requires a
mission-emitted log acknowledgment containing the current package and fresh
session token. Both arming and answer results are observed through this path;
neither a bridge return nor transport success authorizes release. This follows
the context separation described in
[Eagle Dynamics' bridge announcement](https://forum.dcs.world/topic/376636-changes-to-the-behaviour-of-netdostring_in/).
The hook fails closed when the bridge is absent or denied. This control does not
change `autoexec.cfg`, scripting permissions or mission sandbox settings.

## Run and inspect

Run `D:/DCS World/bin/luae.exe experiments/efm-ownership/session-guard/check.lua E:/Projects/DCS_Recorder`
for mocked hook/gate regression checks.

Use `prepare.py INPUT.miz NEW_OUTPUT_DIRECTORY` with the known single-Hornet
identity fixture. Preparation reuses the bounded data-only prototype parser;
it is deliberately not a general authored-mission builder. It creates valid,
localized-edit and ZIP-repacked controls plus the external reference. Existing
outputs are refused. Run `Install-Control.ps1 -Package OUTPUT_DIRECTORY` with DCS
closed. It installs only new files, checks the DCS build and verifies six hashes.

First manual check, by itself:

1. Start DCS and load `030-Session-Guard-valid.miz` from Missions.
2. Click Fly, then open communications **F10 > DCS Recorder session check > Request guarded release**.
3. Report the displayed result and exit the mission. The stock aircraft is not held.

Inspect `DCSR_SESSION` and `DCSR_SESSION_CONTROL` entries in `Logs/dcs.log`.
Success requires a loaded-data match, a fresh session, one accepted answer and
one diagnostic release. A bridge error or mismatch is a useful failed control,
not permission to skip a comparison. After this passes, check localized edits,
file replacement while loaded, repacking, Fly Again, missing checker and stale
responses one at a time. Retain the earlier `MATCH / EDITED` counterexample.

With DCS closed, cleanup removes only the three installed control files under
`Scripts` and, optionally, the three disposable mission copies. Preserve existing
hooks, original missions and the local result package.
