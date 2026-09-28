# Smoke actuator accepted; native player smoke state observed

The user completed **DCSRecorder-Smoke-Control-Test.miz** and confirmed that smoke
turned on/off and visually worked. The retained log contains the expected seven
requests: initial OFF, then three ON/OFF pairs. Requests occurred at native elapsed
times 0.08, 3.08, 8.08, 13.08, 18.08, 23.08 and 28.08 seconds, within the test's
100 ms polling interval. No command error was logged; native playback and mission
completion finished normally. Raw log and analysis remain local and ignored.

This validates the white generator on SMK station 10 plus the mission-controller
`SMOKE_ON_OFF` command for the supported moving playback aircraft. It establishes
visible synthetic actuation, not capture/replay of the player's smoke state.

## Read-only native observation

Supported build: DCS **2.9.29.27468**, stock Hornet with `{INV-SMOKE-WHITE}` on
station 10. Static-code inspection and bounded `ReadProcessMemory` observation
identified per-station emitter-enabled state. No setter, injected code, process
write, or unknown native function was used by the external inspection.

Cockpit command IDs repeat across devices. The confirmed device is
`avCockpitMechanics_F18`, device 7; its command 3019 reaches `whPayload` with
zero-based station index 9. An earlier command-handler candidate belonged to the
lights subsystem and was discarded after RTTI inspection.

The independently traced `SMOKE_ON_OFF` implementation accesses the shared
IwoLA smoke state: a vector of 32-byte station entries, each with an enabled byte
at +24, and a separate aggregate enabled flag. Player and station RTTI, vector
bounds, the smoke store classification, and instruction bytes were checked
against the running game. The prototype reads only the identified station and
aggregate flags, without turning a cockpit switch or menu marker into smoke data.

The user then ran **DCSRecorder-Smoke-Diagnostic.miz** while the external monitor
observed the player. The mission capture finished normally with 183 exterior
frames. The independent monitor retained **3,302 samples over 167.203 seconds**,
with a maximum observed wall-clock gap of 63 ms and zero disagreements between
the two enabled flags:

| UTC on 2026-09-28 | Station 10 | Aggregate |
| --- | --- | --- |
| 01:11:22.578457, initial sample | OFF | OFF |
| 01:12:12.150917 | ON | ON |
| 01:12:20.814687 | OFF | OFF |

Only one ON/OFF cycle was observed. The ON and OFF menu markers occurred 3.366
and 2.416 seconds before the corresponding native transitions. They therefore
cannot serve as exact transition timestamps or establish visual latency. The
monitor measured state independently of these markers. This evidence supports
the native emitter-state channel, but does not establish simulation-clock
synchronization, other colors, other aircraft, or emission during depletion or
damage. The fourth store-classification byte is retained as an observed value;
it is not asserted to be a color mapping.

## Next capture boundary

`smoke-prototype/native_capture.cpp` supplies a separate read-only Lua helper
with instruction, RTTI, station-layout and state guards. It retains no aircraft
object between calls. The diagnostic GUI hook reads only during a new matching
white-smoke mission capture, records start/finish simulation timestamps and
stable Export identity, and stops on unavailable state, delay, clock, sequence
or identity errors. Mission and Export unit IDs are retained separately.

The helper builds in Release; its Lua ABI and 12 offline lifecycle/failure
scenarios pass. Its instruction signatures match the live executable. After
the user closed DCS, two additive diagnostic files were installed and verified;
353 existing scripts, missions, recordings and module artifacts retained their
hashes. The subsequent live in-process run passed with **76 paired samples over
15.005 seconds**, maximum gap 208 ms, and maximum mission-to-native delay 12 ms.
No model-clock advancement was observed within each native read. Export identity
remained stable and both flags agreed throughout. Native model-time transitions
were OFF at 5.140, ON at 8.945 and OFF at 16.143 seconds; capture ended normally.
The markers were at 8.475 and 15.724, again distinct from actual measured changes.

The paired-log analyzer passes the live run and offline missing-END, native-error,
invalid-state, delayed-clock and missing-sample checks. The next step is recording
contract and mission integration; the production recording schema and accepted
playback module have not yet been changed at this checkpoint.
