# Ground hold with repaired readiness bridge

The user completed inspection and reported that the playback Hornet looked
stationary and unchanged. Both mission starts reached READY and
INSPECTION_COMPLETE. The reference serialization repair therefore passed this
live readiness check. No release was requested.

The read-only boundary trace retained here shows replay time fixed at zero,
unchanged horizontal coordinates, and a height offset increasing to 0.109632271 m.
The offset is already present at before_step and unchanged at after_step and
after_animation. Immediate SDK native-motion results match the target. This
localizes replacement between the SDK pose command and the integration hook;
the exact internal native writer has not been identified. The visual review
does not establish recorded-pose retention.

`check_held_pose.py raw/ground-pose-26844.csv` fails: 13,105 held post-step rows
outside 0.00001 m, two sessions, 229.52 seconds covered. The zero-model-time
startup substeps are excluded from that assertion. This is a real captured
regression signal; six passing offline tests cannot establish live repair.

The prepared ground-only change reapplies the same target pose and motion in
before_step, once per pending SDK command, using the existing native_motion
identity, build, object-layout, pose, step-distance and motion checks. It also
publishes failure if that step fails. Existing integration and animation are
still called. Other controller builds retain their prior velocity-only behavior.
Read-only trace stays enabled to test post-step and post-animation retention.

Next: install only the changed ground DLL after DCS closes, restart the same
mission, and inspect another 30-second hold. Countdown/release and all task
acceptance remain pending. Contact, damage, state, and user review must accompany
any successful position check; holding a commanded pose is not proof of physics.
