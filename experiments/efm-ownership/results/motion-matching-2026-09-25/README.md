# Motion matching: live results

Process 32136, two runs ending at 39.16 s and 41.88 s. All 1,709 and 1,845
pose commands returned called, including 750 motion-matched commands per
run. Neither run reached controller release after 43 s. User reports
definite improvement, with some jitter remaining; no exact visual phase
timestamps were supplied.

## Matched interval, 15–30 s

Both runs yielded identical summary measurements for the matched interval:

- Mean pre-command attitude correction: 0.08566 degrees, max 0.11295.
- Mean pre-command position correction: 0.14174 m, max 0.17349.
- Mean change to our last written angular-rate vector: 0.07488 rad/s.
- Mean change to our last written velocity vector: 0.01269 m/s.

For the same times in the original PID 44816 pose-only run, mean attitude
correction was 1.07567 degrees. That is about a 92% reduction in this metric.
This comparison is to original pose-only control, not a claim of 92%
additional improvement over the intervening roll-only test. Normal native
movement continued throughout this experiment; the freeze gate was unused.

At 20 s, DCS changed local roll/pitch angular rates by approximately
-0.05669/-0.04404 rad/s after the preceding write. At 25 s those changes
were -0.05464/-0.05820 rad/s. Thus residual competing angular motion is
still measured; visible jitter need not be attributed wholly to rendering.

Run 1 wall callback spacing maxed at 28.70 ms. Run 2 included one interval
of 359.23 ms; its cause was not established. Both retain 20 ms simulation
spacing. This isolated wall delay does not explain identical recurring
motion corrections across runs.

## Wind hypothesis

Read the installed formation .miz, not just its generator: at 2,000 m it
specifies 7 m/s, direction 291 degrees. Ground wind is 5 m/s at 291 degrees;
8,000 m wind is 10 m/s at 298 degrees. These were inherited from the donor
mission and were not removed when the probe mission was generated.

Mean native displacement per second minus the velocity written at the
preceding callback, over the 750 matched intervals in run 1:

    measured residual XYZ: (2.52332, -0.00050, -6.49670) m/s
    7 m/s at 291 degrees:  (2.50858,  0.00000, -6.53506) m/s

The vectors differ by only 0.04110 m/s. The mean before-minus-command
position residual is (0.04915, -0.000003, -0.13251) m. Both direction and
magnitude strongly support wind being added during native integration.
This remains an inference: no live atmosphere API value was captured,
and float position quantization/integration affect the measurement.

The velocity setter's XYZ storage and magnitude update remain established;
the earlier description of its inputs as authoritative world ground
velocity was incomplete for this null-FM integration path. Setting those
components to the desired ground-track derivative did not cancel drift.

## Next discriminator

Use a zero-wind copy of the same mission with the current DLL to isolate
the position drift, then add measured wind compensation if confirmed.
Separately address the angular-rate changes that DCS regenerates after
each write. Do not simply restore whole-aircraft freezing or hide the
remaining error behind a general camera explanation.

Source artifacts: native-motion.csv, mission-telemetry.txt, summary.json,
wind-comparison.json. No new DLL, mission, or graphics changes were made
during this result analysis. Feasibility remains open.
