# Stock-Hornet exterior-light diagnostic

Question: which measured exterior arguments encode light brightness, switches
and strobe pulses, and what actually appears on the stock aircraft?

This is a separate, disposable mission experiment on DCS 2.9.29.27468. It changes
only the stock player's light controls through installed mission-editor cockpit
actions. It does not install a DLL/hook, alter a recording, or test playback.
Generated game assets remain ignored under `../package/lights-diagnostic`.

Installed primary evidence:

- `CoreMods/aircraft/FA-18C/FA-18C_hornet.lua`, `lights_data`: formation 88,
  navigation 190/191/192, strobe 193 (declared 1.2-second period), landing/taxi
  210, refuel 212. Readbacks alone do not establish visible illumination.
- `Mods/aircraft/FA-18C/Cockpit/Scripts/devices.lua`, `command_defs.lua`,
  `clickabledata.lua` and input definitions identify the exterior-light master,
  position/formation dimmers, strobe DIM/OFF/BRT and landing/taxi controls.
  Device and command numbers are loaded from those installed definitions.
- `MissionEditor/modules/me_trigrules.lua` declares the cockpit action's device,
  command, value and plugin fields. The existing accepted light-off trigger uses
  this action path.

Run `python experiments/efm-ownership/lights-prototype/prepare.py` once with a
fresh output directory. It builds **DCSRecorder-Lights-Diagnostic.miz**, verifies
installed dependencies/routes and exercises the actual packaged startup,
phase triggers and capture lifecycle offline. Those checks establish script
behavior, not live light response or rendering.

Load the mission, keep its Active Pause enabled, lower landing gear and select
F10 > Lights diagnostic > Start automatic light sequence. F2 shows the one stock
jet. At 22:00, eleven phases run for roughly 75 seconds: all off, position dim,
position bright, position off, formation dim, formation bright, formation off,
strobe dim, strobe bright, landing/taxi on, all off. Each phase logs its request
and the actual cockpit-action callback time separately. The mission waits for
that callback before starting the hold interval. Gear channels 0/3/5 and light
channels 88/190/191/192/193/210/212 are sampled at 50 Hz. An explicit stop, lost
aircraft, invalid value, missing phase or 120-second limit ends capture and
requests light-off cleanup. Restart the mission for another sequence.

The user should observe whether the named lights change; no visual result is
assumed from the scheduled control setting. Refuel light is observed but not
commanded in this first sequence. Landing-light ground illumination, canopy,
wheel/suspension state and recorded-light playback require subsequent evidence.

After the run, preserve `Saved Games/DCS/Logs/dcs.log` in the ignored results
directory and run `analyze.py <saved-log> <analysis.json>`. The analyzer requires
one complete sequence, checks request/application timing and sample continuity,
and reports measured argument ranges and changes for each phase. Its offline
fixture passes with 3,213 samples, eleven phases and a 20 ms maximum sample gap;
fixture values do not establish a live light mapping.

The first live stock-aircraft sequence is now accepted; see the
[results](../results/lights-2026-09-28/README.md). `prepare_playback.py <log>
<new-output-directory>` builds a separate SDK-only playback module and nighttime
mission from a validated capture, using the built `HornetLightsProbe` and
`lights_playback_check` targets. Ten channels include gear deployment so the
landing light has the captured gear state. Strobe pulses use sample hold;
other values interpolate. The bounded fake-SDK fixture checks every real sample
and off-grid strobe values, while mission fixtures check cleanup/failure paths.
No native hook is installed by this variant. `install_playback.py <package>
<saved-games-directory>` checks that DCS is closed, validates the manifest and
copies only the new experiment, with protected-file hash comparison.

Load **DCSRecorder-Lights-Playback.miz**, choose F10 > Light playback > Start
captured light sequence, and select the playback lead in F2. Allow about 80
seconds until it is removed, then leave DCS open for log collection. Observe
all four groups independently; SDK write/readback success does not establish
retention or visual rendering. The accepted normal recording/playback flow
still has lights off until this experiment establishes the replay behavior.

The first playback run is now visually accepted with automatic completion.
`check_retention.py <state.csv> <dcs.log> <output.json> --assert-lights` compares
immediate SDK writes with later mission observations using the elapsed clock.
It reports a brief formation-light startup overwrite in the accepted run;
the other activated light channels retain their values. This numerical
requirement remains open for normal integration; see the results above.
