# Engine recording and motion playback integration — installed, live test pending

Continues [Complete single-aircraft visual and engine-state fidelity](https://github.com/caw1517/DCSRecorder/issues/6).
The user accepted the combined nozzle/flame/sound test and subsequently confirmed
automatic completion as verified. This step moves that accepted mechanism into
the normal recorder, flight library and recorded-motion playback path.

## Data and capture

`DCSREC,3` retains the existing motion/brake columns and `hornet-exterior-v1`
surface profile, then adds four appearance arguments (28/29/89/90), native sample
time and eight measured engine getter values (core, fan, E0 thrust, F0 power for
each engine). The additional profile is `hornet-native-engine-v1`. Legacy RPM
placeholder columns remain for schema compatibility; engine values have explicit
new columns and are never estimated from those placeholders.

The mission samples motion, surfaces and engine appearance together. The save
hook consumes that row and uses the previously validated read-only native helper
to append player engine state. It checks stock Hornet/runtime identity, stable
native class/offset/thread/getter identity, native/Export core RPM agreement,
position association within 0.5 m of velocity-based alignment, sampling delay
0–50 ms and read span at most 20 ms. Native capture failures retain `.partial`;
the library never treats those files as completed takes.

Native timestamps remain in the immutable source CSV. Conversion verifies finite
values, bounded sample gaps, known build/profile and exact E0/F0 equality, then
interpolates core/fan/power at each motion timestamp. Identical readings consumed
within one GUI frame are one native observation; conflicting values at the same
timestamp fail. The initial endpoint may be held across the measured delay
(at most 50 ms); no separate-stream time rebasing is used. Appearance retains
the mission sample timing. Fan and power values above one are preserved.

`DCSREC_PLAYBACK_V3` contains the motion sample, thirteen surface values and ten
engine values (four appearance then six native parameters). Versions one/two
remain readable and select their existing modules. The library distinguishes
**Motion only**, **Motion + surfaces**, and **Motion + surfaces + engines**.

## Playback boundary

New module **DCSRecorder-Hornet-Engine-Staged**, DLL **HornetEngineStagedProbe.dll**.
The existing exact-start, F10/countdown, fingerprint and completion workflow is
retained. One owned table combines pre-integration motion, post-animation surface
and engine-appearance repair, and the native RPM/power getters. F0 remains the
guarded original E0 forwarder. The table and presentation correction restore on
stop/destruction, preserving other aircraft and unrelated slots. Complete status
is published after final motion and appearance delivery. No synthetic three-second
baseline/tail is inserted into normal recorded-flight playback.

Native sound derives from recorded parameters; no sound samples or custom sounders
are installed. Surface and engine-appearance logs share the playback elapsed time;
native getter traces include SDK drain time, caller, channel, original and returned
values. Internal physical engine simulation, ground operations, lights, smoke,
canopy and broader aircraft support remain outside this integration.

## Verification and installation

- Release controller build passed.
- Nineteen companion tests passed, including v1/v2 compatibility, real generated
  mission sandbox capture, v3 sink/helper fixture, missing/late/wrong-player or
  mismatched-power rejection, shared GUI-frame timestamps, library labeling,
  source preservation, native tape loading and v3 package activation.
- Five native/mission tests passed: recorded geometry, shared motion/animation/
  engine boundary (including native getter re-entry and all-slot restoration),
  staged contract/lifecycle and the integrated DLL's SDK callback contract.
- The installed mission validators passed new practice/playback generation.
- Engine instruction guards match the retained pinned DCS image and installed
  Sound.dll. The installed capture helper hash matches its checked build.
- Installation verified 11 hashes and 2,576 protected files unchanged. Previous
  autosave hook and settings are backed up under local
  `package/engine-workflow-install/backup`; the detailed manifest and installation
  report remain beside them. Existing recordings and accepted modules are intact.
- The companion restarted at `http://127.0.0.1:46543/`; its library endpoint reports
  the updated save hook installed and the two existing recordings still available.

Prepared live mission: **DCSRecorder-Practice-Engine-be1a3cc9.miz** in Saved Games
Missions. This is a new ordinary recording mission, not a prerecorded engine demo.
No synthetic fixture recording was installed into the user's flight library and
the new controller starts without an active tape until the app generates one.

## Next live check

Record a fresh short airborne take in the new mission, starting nearly level,
with a turn and brief idle/military/afterburner changes. Use F10 Stop, confirm
**Motion + surfaces + engines** in the library, close DCS, then generate playback
through the companion. Replay with the normal F10 start and compare trajectory,
surfaces, nozzle/flame and sound together. Save the capture and playback traces.
Actual integrated in-DCS capture/replay remains unverified at this checkpoint.
