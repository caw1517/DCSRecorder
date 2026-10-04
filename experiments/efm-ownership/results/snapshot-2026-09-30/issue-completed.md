## Outcome

Prepare and retain the original pose and complete supported exterior/engine state before the first inspectable frame.

Step 2 of 15 in [Complete Hornet mission setup and hot-start parking-to-parking playback](https://github.com/caw1517/DCSRecorder/issues/11). Part of #11.

## Completion checklist

- [x] Capture/reconstruct a complete time-zero snapshot including supported gear, flaps/surfaces, canopy, brake, smoke, lights and observable engine/afterburner state.
- [x] Verify first visibility and held inspection with non-default initial channels: no default-state flash, relocation, acquisition blend or state drift.
- [x] Measure retained state after native animation, document unavailable channels and preserve the historical speed-brake residual for the later fidelity check.

## Starting evidence and boundaries

Appearance and sound do not establish restoration of all cockpit systems or internal engine state.

## Working agreement

Work through the parent's execution checklist one task at a time. The agent prepares changes and inspects logs; the user performs required live DCS checks one concrete step at a time. Before work, claim the task and inspect existing artifacts and evidence. A prepared package or passing offline check alone does not complete a live acceptance requirement. Close with a completion comment linking implementation/evidence and the user review where required; then check off the matching parent entry. If integration invalidates an earlier result, reopen the affected task rather than retaining an unsupported checkmark.

## Agreed requirements

- [Choose visible staging and parked completion for playback aircraft](https://github.com/caw1517/DCSRecorder/issues/15)
- [Agree on parking-to-parking validation and acceptance](https://github.com/caw1517/DCSRecorder/issues/17)

## Accepted result

[Completion evidence and user review](https://github.com/caw1517/DCSRecorder/issues/21#issuecomment-5924345948). The user permits smoke to be invisible while held; recorded smoke ON must render on release, verified by the following countdown/release task. This closes the bounded airborne snapshot step; later ground/release/fidelity requirements remain open.

