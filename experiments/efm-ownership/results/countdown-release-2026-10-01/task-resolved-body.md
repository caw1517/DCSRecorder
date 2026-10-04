## Outcome

Connect held staging to the three-second F10 countdown and one acknowledged release transition.

Step 3 of 15 in [Complete Hornet mission setup and hot-start parking-to-parking playback](https://github.com/caw1517/DCSRecorder/issues/11). Part of #11.

## Completion checklist

- [x] Keep replay time at zero throughout inspection and countdown; repeated requests cannot start another run.
- [x] Release the player and playback together; restore recorded initial velocity and drive motion, exterior state and engine sound from the same replay epoch.
- [x] Verify first rendered movement against the source and refuse release without readiness. Pause must not cause elapsed-wall-time catch-up.

- [x] For recorded smoke ON, verify visible emission begins when playback releases. The user explicitly permits smoke to remain invisible during held staging; command delivery alone does not establish emission.

## Starting evidence and boundaries

Use the airborne control first; repeat the contract on ground inputs in the following task.

## Working agreement

Work through the parent's execution checklist one task at a time. The agent prepares changes and inspects logs; the user performs required live DCS checks one concrete step at a time. Before work, claim the task and inspect existing artifacts and evidence. A prepared package or passing offline check alone does not complete a live acceptance requirement. Close with a completion comment linking implementation/evidence and the user review where required; then check off the matching parent entry. If integration invalidates an earlier result, reopen the affected task rather than retaining an unsupported checkmark.

## Agreed requirements

- [Choose visible staging and parked completion for playback aircraft](https://github.com/caw1517/DCSRecorder/issues/15)


