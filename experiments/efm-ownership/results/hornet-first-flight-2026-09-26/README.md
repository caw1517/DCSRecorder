# First successful Hornet flight

User reports that playback worked well, with three appearance problems:
removable pylons remained, exterior lights were on, and the speed brake
looked deployed. The user requested a faster roll-in and a level 2.5 g
180-degree turn for the next refinement.

Archived from DCS process 9096 before installing that refinement:

- `native-motion.csv`: capture at 5.0 s, 3,651 successful motion commands,
  release at 78.02 s, no rejected commands in this capture.
- `mission-telemetry.txt`: independent pose and air-data samples. Probe
  calculated CAS ranged 399.224–401.246 knots over seconds 10–70. This is
  atmosphere-derived CAS, not the player's indicated airspeed.
- `HornetProbe-first-flight.dll` and `first-flight.miz`: prior installed
  artifacts retained for comparison/recovery.

The old flight establishes the basic Hornet representation/motion path.
It does not validate the later clean configuration, animation writes or
2.5 g path. Those need their own flight.
