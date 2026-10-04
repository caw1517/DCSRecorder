# Automatic save failure and correction - 26 September 2026

User symptom: new flight did not appear after F10 Stop.

The captured log contains BEGIN, 2,301 sequential DATA rows and END,user_stop,2301.
The take lasts 46 seconds and passes the companion's current build, weather and
trajectory validation. Before recovery, check_missing_take.py failed with
"matching durable library entry: False". The exact complete take was restored as
20260926T221820Z-recovered.csv, named "Recovered flight - 46 seconds"; the check
then passed. Recovery is separate from fixing automatic saves.

## Reproduced cause

The unchanged sink successfully parsed the captured log outside DCS. The installed
Lua executable could open the active file externally. Live hook diagnostics then
confirmed both the frame callback and the failure inside the DCS GUI environment:

    [DEBUG-save-live] onSimulationFrame active
    [DEBUG-save-live] log_open_failed: can't open .../Logs/dcs.log for 'rb'

The sink previously returned silently on that refusal. The exact reason DCS's GUI
I/O layer refuses this active file was not established; no broader file-access
restriction is inferred.

## Correction and regression

The sink now calls DCS.getLogHistory on every simulation frame instead of opening
the active log file. This API is documented in the installed API/Sim_ControlAPI.md
and used by the shipped Scripts/Hooks/webGUI.lua. Existing explicit-stop,
sequence/count, incomplete-take and atomic publication checks are preserved.
History resets abandon incomplete takes. Errors are reported without repeated
log flooding. Temporary DEBUG instrumentation has been removed from the source.

The new regression test denies active-file reads. Before the fix it failed with
0 saved files instead of 2; after the fix it passes. All eight companion tests
pass. replay_history.lua delivered the original real capture in 100-message
batches with active-file reads denied; the corrected sink produced a CSV
byte-identical to the preserved complete take.

Corrected hook installation and a fresh live save are still required before
claiming the automatic-save path works inside DCS. Raw logs and recovered flight
copies remain local; this report contains no publication authorization.

The corrected hook is now installed and hash-verified. Fresh live save remains pending.
Installed SHA-256: 9D771C387353B16BBAD415D33FD4D47E9F5BDB12C3DF4DBC1DF044780066AE2D

## Second live failure: DCS file methods with no success return

The subsequent take produced a 240-byte header-only .partial. The live log showed
"bad argument #1 to 'assert' (value expected)" at the line that asserted write/flush
return values. File output itself had succeeded. The take still had 2,090 rows and
an explicit Stop in the log, so it was recovered as
20260926T223322Z-recovered.csv (41.78 seconds), validated, and named in the library.
The known header-only partial was preserved under recordings/incomplete after its
complete counterpart was recovered.

The new regression wraps file write/flush/close operations to succeed with no
return values. It failed before the fix with zero completed CSVs instead of two.
The corrected sink accepts void success, still rejects thrown/explicit errors,
and reads back the complete recording bytes before and after finalization.
The wrapper regression also covers void-success rename/remove behavior. All nine
companion tests pass.

A startup self-check now exercises actual storage write, flush, close, readback,
rename and cleanup before claiming readiness. The companion displays its status
instead of treating an installed hook as a working saver. In the real DCS startup
at 22:39:53 UTC, the self-check and log-history callback passed. save-status.txt
contains READY / Storage and DCS log history verified. A new live recording is
pending to verify the full Stop-to-library path.

## Verified automatic save

The next live run saved 1,975 samples over 39.48 seconds
automatically as 20260926T224052Z-0001.csv. END,user_stop was logged at 22:41:31.579 UTC;
Saved recording followed at 22:41:31.588 UTC (9 ms). The companion validator
accepts the flight. Its bytes exactly match independent extraction from the complete
event stream, and no top-level .partial remains. No manual recovery or copying
was used to create this automatically saved flight. See verified-automatic-save.json
for hashes. The two earlier failed captures remain recovered and preserved.
