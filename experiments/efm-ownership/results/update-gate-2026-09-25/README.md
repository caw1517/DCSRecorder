# Update suppression: live result

Process 23980, one run, 1,526 successful commands from 5 to 35.5 s.
No command or gate failures. Suppression was recorded on 750 commands;
the gate was restored at 30 s. The run ended before the 43 s controller
release, so release is not validated here.

## Result

For all 750 intervals beginning with suppression enabled, the recorded
position and attitude before the next command equal the previous applied
pose exactly: zero intertick translation and zero basis-axis angle change.
This establishes successful suppression at the measured callback boundary.
The callbacks continued every 20 ms of simulation time.

However, the path continues advancing at 105 m/s. Each subsequent command
therefore corrects approximately 2.1 m of position error rather than the
roughly 0.14 m mean correction seen in the earlier roll-only interval.
The pose-command error after application remains tiny (maximum axis error
under 0.000003 degrees). Mean wall callback spacing was 20.0 ms, maximum
25.01 ms; there is no observed callback stall matching the reported effect.

The user reported that jitter arguably became worse during the middle.
The supplied Test.mp4 is 17.87 seconds at nominal 60 fps, 2560x1070. Sampled
frames show close cockpit formation through the banked turn. contact.png
and sequence-4s/9s/14s.png preserve sampled frames for inspection. Video
time has not been aligned precisely to mission time; still-frame inspection
does not establish a quantitative jitter frequency or amplitude.

## Interpretation and decision

The gate removed the competing native motion, but also stopped forward
motion between commands. The resulting sampled trajectory holds then
jumps, which is consistent with the user's visual regression. The renderer's
exact interpolation behavior remains unmeasured, so do not claim it renders
each raw 2.1 m step directly or that this explains every visual artifact.

Reject **freeze plus repeated ForcePosition alone** as the smooth playback
solution. Retain the gate only as experimental evidence of per-object
motion suppression. Do not extend this intervention to the whole flight.
Next technical direction is consistent linear/angular velocity or an
appropriate interpolation path that moves the aircraft between pose
corrections. This is the continuous-motion part of the FSX slew analogy;
freezing alone did not provide it.

Source artifacts: native-motion.csv, mission-telemetry.txt, summary.json.
Original user video: C:/Users/w_can/Downloads/Test.mp4 (not copied).
The installed DLL still contains this diagnostic; no further DLL changes
or simulator settings changes were made during analysis.
