# Ordinary EFM engine getter is not queried

THROWAWAY evidence for [Complete single-aircraft visual and engine-state fidelity](https://github.com/caw1517/DCSRecorder/issues/6), DCS 2.9.29.27468.

User verdict: "still idle sounds". This was expected for the forwarding-only
probe; the new result is zero engine-parameter calls during actual playback.

Local `parameters-35288-333268843.csv` contains ready, sdk_setup, object_create
and object_destroy rows, all with total_calls=0. The object ID is 16777472.
The DCS log confirms HornetEngineSoundProbe.dll loaded. Native actuator events
confirm 979 tape samples loaded, start at mission time 6.965, and 2,091 frames
through mission time 48.765 (elapsed 41.8 seconds), followed by destruction.
The user left before the 48.9-second sequence ended; no full-completion or
automatic-removal result is claimed. This is enough to reject the ordinary
getter as an active control path during the observed interval, not a universal
claim about all DCS objects/builds or the last seven seconds of this sequence.

Changing RPM/gain values returned by this unused callback cannot change this
observed playback. Audio remains unresolved. The earlier accepted nozzle/flame
result is preserved separately.

## Alternative sound path and bounded next experiment

Installed primary implementation evidence:

- `D:/DCS World/CoreMods/aircraft/A-10/A-10C.lua` explicitly selects an aircraft
  sound script using `sounderName`.
- The installed UH-60L mod's `Sounds/Sounders/Aircraft/Planes/UH-60L.lua`,
  `Aircraft/uh60l_Aircraft.lua` and `Tools.lua` demonstrate `onUpdate(params)`,
  a world-context ED_AudioAPI host, and position/orientation/velocity/timestamp
  updates. Its engine implementation controls source pitch/gain and looping.
  This is an installed mod example, not proof of Hornet compatibility.
- `D:/DCS World/Doc/Sounds/sdef_and_wave_list.txt` lists the stock
  `Aircrafts/FA-18/F404GE_RPM1` and `Aircrafts/FA-18/Afterburner` source names.
  `Doc/Sounds/example.sdef` documents source gain, pitch, position and distance.
  Stock sample contents are not copied or redistributed.

The next hypotheses, in order, are: an explicit custom sounder can control this
object's world audio; the sounder executes but source lookup fails; the cloned
aircraft never invokes the custom sounder. A tagged loaded/source/phase log and
a deliberately audible alternating pattern distinguish these cases. Missing
logs alone are inconclusive: inspect DCS sounder loading/errors as well.

`DCSRecorder-Hornet-Sounder-Test` explicitly registers a unique sounder. It uses
the installed engine sample for three seconds, afterburner for three seconds,
repeats once, then stops both. Pitch is 1 and gain 0.4. Position/orientation/
velocity/timestamp follow the sounder's supplied aircraft data. The mission
removes the lead after 15 seconds. Missing/nonfinite host data or a backward
clock stops sources. The animation tape is unchanged, so these deliberately
synthetic sounds are not synchronized to its nozzle/flame phases.

This is an audio-control experiment, not an engine-fidelity fix. Live registration,
source resolution, audible switching, spatial behavior and removal require DCS
observation. The script harness verifies four play calls, terminal silence,
invalid-data/clock handling and mission activation/removal. The new DLL builds
and rejects fake native identity; mission dependency/route/configuration checks
pass. No regular EFM getter changes or guessed RPM-to-afterburner threshold.

Prepared mission: **DCSRecorder-Sound-Routing-Test.miz**. F10 > **Sound routing
test** > **Start sound test**, then F2 to the lead. Listen for engine / afterburner
/ engine / afterburner / silence. Let it disappear at 15 seconds and retain the
session for collection. Its unique module writes `sounder.log` when sounder file
I/O is available and emits `[DCS-SOUNDER-PROBE]` messages through print as well.

After the user confirmed DCS closed, installed directly into Saved Games. All 11
installed hashes match the manifest; all 26 protected existing files are unchanged.
The live sounder result remains pending.
