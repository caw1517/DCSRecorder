## Editor checks complete; runtime boundary observed, investigation still open

Published checkpoint [13a2514](https://github.com/caw1517/DCSRecorder/commit/13a25144cc8f7ac61d291668c144b1280efbfa5e) on `codex/prototype-mission-identity`:

- [Evidence and approved contract](https://github.com/caw1517/DCSRecorder/blob/13a2514/companion/mission-identity.prototype.md).
- [Additional editor observations](https://github.com/caw1517/DCSRecorder/blob/13a2514/companion/mission-identity-remaining-observations.prototype.json).
- [Sanitized runtime callback evidence](https://github.com/caw1517/DCSRecorder/blob/13a2514/companion/mission-identity-runtime-observations.prototype.log).

On DCS 2.9.29.27468, user-operated copy/paste produced a new group/unit with new IDs/names while all seven original aircraft records remained equal. Controlled four- and seven-aircraft inputs, each opened and saved in Mission Editor, retained the complete original four aircraft/group/route records exactly. Externally reversed group-container entries also survived a real editor save with all seven aircraft records equal. This establishes the bounded addition/order cases; it is not within-group leader reordering or implemented take preservation.

A separate temporary read-only GUI hook compared the named archive against an external frozen reference and read a description marker through `DCS.getCurrentMission()`. Normal Mission-menu load reported MATCH / ORIGINAL at load-begin, load-end and simulation-start. Replacing the disposable archive after load produced MISMATCH / ORIGINAL: the file changed while the loaded mission description did not. Quit to debrief followed by **Fly Again** again reported MISMATCH / ORIGINAL at all three callbacks, and its in-cockpit briefing visibly retained the original description. The named archive still contained the EDITED variant. This demonstrates that this restart path reused original content and that hashing the named file is insufficient proof of loaded content.

No recorder/playback approval gate was implemented or validated. There is still no verified production runtime load path. Preparation/activation hash verification remains a separate boundary; session-specific fail-closed authorization is an implementation requirement. The description marker is only an experiment discriminator, not a trust anchor or complete semantic digest.

Runtime checks remain incomplete: separate edited/repacked loads, Mission Editor test flight and missing-checker coverage. Capture failed repeatedly with `FrameArrived timed out`, including after the user brought DCS forward and the window was reacquired. Further UI input stopped. The disposable archive was restored to its valid SHA-256 (`ab60278387bee7dd37d2359cb3e95a5bbdb973cffed830f6ee332febcbc8b7bd`). The separate diagnostic hook and external reference were removed from Saved Games; other hooks were untouched. The running DCS process still needs a normal exit to unload callbacks already in memory.

Lua diagnostic syntax, Python fixture syntax, six observation records and staged whitespace checks passed. Raw missions remain local. Keep this decision open and retain its claim; user approval of the association policy remains complete. No map resolution or implementation acceptance is claimed.
