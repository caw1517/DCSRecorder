# Formation prototype: each playback aircraft owns its recorded flight

Work on [Let each playback aircraft own its recorded flight](https://github.com/caw1517/DCSRecorder/issues/39),
following [the layered playback decision](https://github.com/caw1517/DCSRecorder/issues/9#issuecomment-6070620636).
This is a developer prototype, installed under its own developer-only type
(`DCSRecorder-Hornet-Formation`). The normal playback module is not touched.

## How an aircraft finds its take

One playback module entry per aircraft type still holds. The module carries
every formation take under `bin/takes/`. The control hook assigns each take to
its aircraft:

1. The hook reads each position's mission unit ID and resolves its native runtime
   ID with `DCS.getUnitProperty(id, DCS.UNIT_RUNTIME_ID)`. That ID was proven equal
   to the controller's `ed_get_object_id` in [native-type](../results/native-type-2026-09-23/README.md).
2. The hook calls the bridge with `assign`, the take's 48-bit tape key and that
   runtime ID. The controller gives that object exactly that take. It refuses an
   unknown take, an unknown object, a take that is already assigned, a second
   assignment to one aircraft, and two tapes that share one key.
3. Until its take is assigned, an aircraft is held at its spawn pose with zero
   motion. Ten seconds without an assignment fail that aircraft alone.
4. After assignment, each aircraft publishes its own tape key on args 997/998.
   The mission script checks that every aircraft flies the take it expected.

## Isolation

- `native_step_hook.h` keeps a per-object owner map. Every same-type owner shares
  one shadow table, built by the first owner. Each owner has its own callbacks,
  thread check, engine values and engine trace, and restores only its own vptr.
  A different table, callback set or getter set is refused while owners remain.
  With one object the behavior is unchanged, and `native_step_check` still passes.
- The bridge addresses aircraft by take key, so commands sent to one aircraft
  (inspect, commit, abort) never reach another.
- The mission script removes a failed or destroyed aircraft alone. The others
  keep playing, and the formation fails as a whole only when no aircraft is left
  before release.
- The hook commits every ready aircraft in one callback, and the player is
  released in that same callback.

## Shared epoch

Decided in [Release all playback aircraft on one shared clock](https://github.com/caw1517/DCSRecorder/issues/40#issuecomment-6090016306).
The hook passes its model time at the commit to every aircraft as a fifth
`commit` argument. Each aircraft's replay time is `now - epoch`, so an aircraft
whose first callback after the commit lands frames late starts at its shared
replay time instead of zero, and never runs behind. The bridge refuses an epoch
that is not finite or is more than 0.1 s from the aircraft's last callback (the
hook's own readiness window). The hook logs the epoch once (`COMMIT`); the
controller logs `formation_epoch` per aircraft and, at the first played callback,
`release_epoch` (the epoch) and `release_first_step` (that callback's model time).
Single-aircraft playback keeps its solo commit unchanged.

## Prepared formation copy and recording against it

Decided in [Record a new flight while a formation plays](https://github.com/caw1517/DCSRecorder/issues/41)
and [Store formations and their versions in the flight library](https://github.com/caw1517/DCSRecorder/issues/44).

- **Removal.** Every authored aircraft that is neither playing nor the player
  (muted, or without a take) is removed from the prepared copy
  (`authored_missions.remove_aircraft`). The edit is declared: preservation
  restores each changed aircraft container and compares the result with the source.
  Preparation is refused when anything left in the mission (a trigger, a task)
  still refers to a removed aircraft. The manifest lists the removed names.
- **Takes from earlier revisions.** A take can play in a newer revision if its own
  saved scene is given and its aircraft is authored identically there.
- **Recording.** With `record=`, the recorder is injected for the player's aircraft
  in formation mode (`record_script(..., formation=True)`). It has no F10 Start.
  At the release, the hook passes the epoch to the mission's `released()`, which
  begins the take with `formation_id`, `formation_version` and `formation_epoch`.
  The first sample is taken in that callback, so it is the held start. F10 Stop
  saves as usual. A take interrupted by a restart or exit stays incomplete.
- **Events.** An aircraft dropped before the release is `not_ready`. An aircraft
  that fails afterwards is `failed@<replay s>`, and one that reaches its ending is
  `ended@<replay s>`. The recorder logs them as `EVENT` lines. The save hook
  (`companion/recording_sink.lua`) writes them into the take's `formation_events`
  row when the take is saved.
- **Manifest.** The recording copy's manifest carries `association`, `lineage`,
  `prepared_sha256` and the `formation` block (version, takes played, muted).
  Take binding joins this with the take's own metadata
  (`formations.flown_against`).

## Offline checks (passing)

- `formation_shared_epoch` (`check_epoch.cpp`): two aircraft commit on one epoch.
  One aircraft's first callback is delayed five frames and it is then stepped at
  10 Hz; at every shared tick both replay times are exactly equal. The solo
  commit's lag in the same schedule is shown, along with refusals and restart.
- `formation_owner_isolation` (`check_owners.cpp`): two owners share one table,
  with separate callbacks, engine values and traces. Removing one leaves the
  other's override running, and a replaced vptr is never overwritten.
- `formation_take_assignment` (`check_assign.cpp`): the real
  `HornetFormationProbe.dll` with two objects and two takes. Its bridge runs
  through a test-only `lua.dll` stub. The check covers assignment by runtime ID,
  every refusal, routing by key, and that aborting or destroying one aircraft
  leaves the other.
- `formation_bridge_refusal`: the real Lua ABI, with no objects present.
- `test_prepare.py` packages the authored fixture scene with two positions. The
  second take is a relabelled copy, so this is packaging only. The generated
  mission passes the DCS validators, `check_mission.lua` (destroy, native abort and
  readiness timeouts each remove one aircraft) and `check_hook.lua`. It also builds
  recording copies: one playing aircraft, the take-less one removed, a muted
  position, and a plan that doesn't match. `check_mission.lua` runs its `single`
  mode for one playing aircraft, and its recording modes check the begin at the
  release and the not-ready, failed and ended events.
- `check_recorder.lua` runs the real injected recorder. In formation mode it has
  no F10 Start, takes its first sample at the release, logs events and stops. In
  solo mode, F10 Start and the first sample on the next frame are unchanged.
- `companion/test_formation_recording.py`: the save hook writes events into the
  saved take's metadata, a restart leaves it incomplete, and a malformed event
  fails the take.
- The full CTest suite and the companion tests still pass.

## Live check (Hornet, Caucasus, zero wind)

Takes: two short ground-start takes, flown from two different Hornets in one
unchanged scene. A third Hornet in the scene is the player's seat.

```
python prepare.py <scene.miz> <player unit id> <output dir> 080-Formation-Prototype.miz <take1.csv>=<unit id> <take2.csv>=<unit id>
powershell -File ../authored-preparation/Install-Playback.ps1 -PackageDirectory <output dir>
```

1. Fly the installed mission from the player's Hornet. The message *Player held.
   Waiting for every playback aircraft...* appears, then *Ready: <both names>*.
   Check that both jets sit at their own recorded start positions.
2. Open F10, then *DCS Recorder formation*, then *Start playback*. After the
   countdown, each jet follows its own recorded flight.
3. Once both are moving, open *Remove one aircraft (developer)* and choose
   *Native abort* for one jet. Only that jet is removed, and the other flies on.
4. Restart the mission, release again, and choose *Destroy* for the other jet.
5. Let the remaining jet reach its own ending.

Pass: in the native motion log, the surviving aircraft's motion stays `called`
with no gap around the removal, and it reaches its own ending. Logs are written
to `Mods/aircraft/DCSRecorder-Hornet-Formation/bin/probe-logs`, and `dcs.log`
lines carry the `DCSR_` prefixes.
