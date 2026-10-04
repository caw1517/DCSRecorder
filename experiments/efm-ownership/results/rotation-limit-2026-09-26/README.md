# Rejected strong-turn recordings — 26 September 2026

The user reported two recordings marked Unsupported after max-G turns, followed
by an accepted simple left turn. Reproduced through the companion's actual
`Library.entries()` validation path against the saved recordings.

Both rejected recordings raise `Take rotation exceeds conservative playback rate
limit`. This is the configured prototype envelope, not an automatic-save failure.
No playback limits or controller behavior were changed during this diagnosis.

| Take | Duration | Peak total rotation | First rate rejection | Minimum altitude |
| --- | ---: | ---: | ---: | ---: |
| 20260927T005525Z-0001.csv | 80.92 s | 153.76 deg/s | 1.56 s | 572.47 m |
| 20260927T005915Z-0001.csv | 69.38 s | 105.81 deg/s | 1.96 s | 530.47 m |
| 20260927T010126Z-0002.csv | 23.40 s | 32.98 deg/s | none | 1826.90 m |

The rate limit is 0.9 rad/s (51.566 deg/s). At the peaks and initial crossings,
rotation is predominantly roll. The validator does not test G-load directly.
Both rejected takes also cross the separate 1000 m minimum altitude, although
the rate rejection happens first and masks that later reason. All three takes
remain within the current 70–260 m/s speed guard.

Each file has an explicit user_stop footer with a matching sample count. The
analysis found no time gaps or position/velocity discontinuities using the
existing converter's thresholds. These checks do not establish playback support
for the stronger maneuvers. `analysis.json` records the measured values.

Rotation/altitude bounds are also enforced in native playback, so expanding
support requires coordinated validation of converter and controller behavior,
followed by live tests of the broader envelope. The accepted pitch correction
remains installed; neither rejected take reached playback. Preserve the narrow
current envelope until that work is explicitly undertaken and verified.
