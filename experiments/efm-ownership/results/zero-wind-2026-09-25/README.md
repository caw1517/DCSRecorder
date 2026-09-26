# Zero-wind motion matching: live result

DCS 2.9.29.27278, process 27236, one run through 34.64 simulation seconds.
All 1,483 pose commands returned `called`; 750 matched-motion intervals
cover the 15–30 s intervention. No failure status was logged. The run
ended before release at 43 s, so release remains unverified.

The user reported a massive visual improvement and explicitly accepted
requiring no wind in missions. Treat this as the working environment
constraint and defer wind compensation.

## Comparison with the windy motion-matching baseline

Same DLL and trajectory; the prepared mission changed only three wind
speeds. Metrics use the preceding command's intervention state and compare
the same 750 intervals against the first archived process-32136 run.

| Metric during matched motion | Windy | Zero wind |
| --- | ---: | ---: |
| Mean position correction | 0.14174 m | 0.01820 m |
| Maximum position correction | 0.17349 m | 0.03565 m |
| Mean attitude correction | 0.08566 degrees | 0.08567 degrees |
| Mean angular-rate change after our write | 0.07488 rad/s | 0.07489 rad/s |

Mean position correction fell 87.16%. Mean native displacement per second
minus previously written velocity changed from approximately
(2.52332, -0.00050, -6.49670) m/s to
(-0.01430, -0.00091, 0.03061) m/s. Removing wind eliminated most of the
systematic translational residual, while angular correction barely changed.
This controlled result strongly supports added wind as the source of the
earlier systematic position drift. It does not establish that every
remaining error has the same cause or that playback fidelity is complete.

Simulation callbacks stayed 20 ms apart. Maximum wall interval was 30.94 ms.
Source metrics and comparison are in `summary.json` and `comparison.json`;
raw observations are in `native-motion.csv` and `mission-telemetry.txt`.

## Video evidence and interpretation limits

User video: `C:/Users/w_can/Downloads/NoWind.mp4`, 17.46 seconds,
2560x1070 at nominal 60 fps. `contact.jpg` samples the clip at three-second
intervals and shows close cockpit formation through the banked maneuver.
Still frames do not quantify temporal jitter; the visual improvement is
the user's report, supported by the measured positional improvement.
Video time was not precisely aligned with mission time.

## Adopted scope

Use static weather with zero wind at all three mission layers and zero
ground turbulence for generated probe missions. Keep the successful
zero-wind mission installed. The generator now enforces those conditions;
the original windy mission and evidence remain available for comparison.
No controller/DLL changes are made in this step. Motion matching still
runs only during 15–30 s in the installed diagnostic. Continuous matching,
release, additional maneuvers, and physical interactions remain subsequent
validation work. Wind compensation is deferred under the accepted scope.
