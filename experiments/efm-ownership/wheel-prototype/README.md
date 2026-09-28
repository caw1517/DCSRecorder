# Wheel rotation and suspension capture prototype

Question: what raw exterior values encode stock Hornet wheel rotation and strut
compression during stopped, rolling and braking states, and how does rotation wrap?

This is a separate read-only mission on DCS 2.9.29.27468. Installed primary source
`Mods/aircraft/FA-18C/FM/config.lua` declares these mappings; preparation loads
the installed file and asserts them before packaging:

| State | Nose | Left main | Right main |
| --- | --- | --- | --- |
| Gear deployment | 0 | 5 | 3 |
| Compression | 1 | 6 | 4 |
| Wheel rotation | 101 | 103 | 102 |
| Wheel radius, metres | 0.26925 | 0.340 | 0.340 |

These definitions identify candidates, not measured ranges, rotation period,
direction, or renderer behavior. Do not assume a rotation period of one or
interpolate raw wrap crossings before measuring them. Gear deployment is already
accepted and is included as a control.

## Run

`python experiments/efm-ownership/wheel-prototype/prepare.py` builds into a fresh
`package/wheel-ready` directory from installed assets and the accepted clean
baseline. It retains the previously tested Caucasus hot-parking location with
one stock Blue Angels Hornet. No game assets are committed.

Load **DCSRecorder-Wheel-Diagnostic.miz**. No Active Pause. Select F10 → Wheel
diagnostic → Start taxi capture. Remain stopped for five seconds; release parking
brake, taxi slowly at about 5–10 knots, then brake to a full stop. Hold for five
seconds and repeat once. Stop taxi capture through F10 and leave DCS open. The
optional Mark braking command annotates a chosen instant but is not required.
Observe wheel/strut movement externally when practical. Stay on the ground.

The capture records actual mission time, world position/velocity, and the nine
raw arguments at 50 Hz. It never commands controls, writes arguments, or saves
to the normal flight library. A mission restart is required for another capture.
It stops on loss of the player, airborne state, nonfinite data, speed above
15 m/s or a three-minute time limit. Those are bounds of this low-speed diagnostic,
not proposed product limits.

`check_capture.lua` executes the packaged mission in a restricted fake simulator:
normal stop, duplicate starts, paused frames, missing player, invalid values,
airborne state, speed and duration limits. No control-command API is supplied.
The 2,000-row fixture checks capture mechanics only, not live wheel physics.

`analyze.py SAVED_LOG OUTPUT_JSON` requires one complete capture and reports
timing, stopped/rolling sample counts, raw ranges, changes and large raw steps.
It deliberately does not infer wheel rotation from velocity or unwrap values.
Live mapping and a separately tested replay are the next gates. Ground-motion
playback, contact, tire slip/damage and takeoff/landing remain distinct work.

See the [evidence checkpoint](../results/wheels-2026-09-28/README.md).

## Steering follow-up

The first live wheel capture completed and contains turns, but its nine channels
do not include steering. Past steering angles cannot be recovered from that log.
The user's request adds a separate `prepare.py --steering` variant, output
`package/wheel-steering-ready/DCSRecorder-Wheel-Steering-Diagnostic.miz`.
It uses protocol two and appends candidate argument 2 plus the already mapped
rudder channels 17/18. Argument 2 remains a probe candidate: the inspected
Hornet FM file does not explicitly identify a steering draw argument, and no
authoritative Hornet mapping was established by documentation lookup.

Start taxi capture with NWS enabled; hold center, taxi slowly through a left
turn, center, then right, center and stop. About five seconds per state and
5–10 knots is sufficient. Optional F10 left/center/right marks record the
user's visible steering observations. Stop capture and leave DCS open.
The variant has no control writes and needs no new module or hook.
The analyzer accepts both exact protocol/channel sets and preserves signed raw
values. Do not claim a steering direction/range until the new capture and visual
observation agree. The original wheel diagnostic remains installed unchanged.
