# FS Recorder reference

Researched 2026-09-23. Scope: the original FS Recorder for FSX, not similarly named modern products.

## Source and findings

The original author's website did not load during this research. The accessible primary document is Matthias Neusinger's **FS Recorder for FSX 2.1 manual**, copyright 2004–2011, preserved on a third-party host. Its provenance is the manual's title and copyright page; the host's generated summary is not evidence. [Manual](https://fr.scribd.com/document/49148441/FSX-Recorder-Manual)

- **The requested workflow is explicitly documented:** record A, play A as traffic while recording B, then play A+B while recording C. Multiple tracks can be played together or combined into one file. See *Combined use of Recording and Playback*.
- **Core captured state:** geographic position, pitch/bank/heading, three-axis velocity, and on-ground state. Optional channels include control surfaces, gear, flaps, throttles, engine state, lights, smoke, and tailhook. See *Recorded Data*.
- **Synchronization:** recording during playback inherits the playback time-code. See *About Synchronization*.
- **Precision limits:** shorter sampling intervals improve accuracy. Re-recording already playing traffic compounds interpolation error; preserve original flights separately. Not all aircraft state is captured, so resuming manual flight can misbehave. See *Recording Intervals*, *Combined use*, and *Stopping Playback*.

All four findings above: [FS Recorder 2.1 manual](https://fr.scribd.com/document/49148441/FSX-Recorder-Manual).

## Implications for our DCS investigation

These are design deductions, not claims of DCS support:

- The pivotal experiment is commanding a separate playback aircraft's position and orientation against a shared clock while the user retains control of another aircraft.
- A generated loop and roll trajectory can test that capability before a recorder exists.
- Preserve each original recorded flight and compose references to those originals. Do not repeatedly capture the visible playback to build the next layer.
- Separate movement fidelity from visual-state fidelity: matching a trajectory alone does not demonstrate landing gear, smoke, canopy, lights, control surfaces, or touchdown behavior.
- Define measurable position, angular, and timing error tolerances before claiming one-to-one playback. The reference product does not establish mathematical exactness or DCS feasibility.

No Git branch could be created: this working directory is not currently a Git repository.
