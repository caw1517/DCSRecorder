Prepared and installed a motion-matching experiment. Live result pending.

The previous update gate is no longer used. Native aircraft motion runs throughout. During 15–30 s only, each pose command is followed by world velocity and local angular rates calculated from the trajectory. Before/after that interval the controller sends pose commands only. Same 105 m/s formation mission and 43 s release remain.

WorldGeneral::MovingObject::VectorVelocity(Vec3f const&) at RVA 0x69310 was traced: it writes scalar magnitude at receiver+0x250 and XYZ at +0x254, with the getter corroborating that layout. Angular layout/convention is established by the three native integration loads. Additional build signatures, finite-state/rate/speed bounds, and exact write readback guard the experiment. DCS may overwrite the state, so this is not a claim of authoritative slew control.

New logs include commanded and before/after linear/angular motion. The analyzer measures next-command pose errors and changes to the last written rates, splitting repeated mission runs. Offline tests pass for ABI, path geometry, independent axis conventions and next-step motion prediction; a synthetic analysis test covers phase attribution/reset.

The user's [FSDeveloper reference](https://www.fsdeveloper.com/forum/threads/smooth-ai-movement-the-old-favorite.17374/) remains the conceptual reference for movement between corrections. Its FSX slew interface is not available through DCS's object API.

Installed SHA-256: 6722E4E3C82243DC9852DCDAB5278F7B5FF7E85EFFC40A730C8D911A47F90591. Prior DLL preserved. Protocol: docs/research/dcs-motion-matching-experiment.md. Next live check is 55 s of close formation, especially 15–30 s. Keeping the feasibility decision open.
