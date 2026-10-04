## Resolution — live hot-ground hold and first taxi release demonstrated

The user completed the real short-ground trial and accepted the visual result: “Stationary and unchanged” during inspection, then “Worked and everythign looked good” after countdown and taxi playback.

The source was an actual 19.8-second, 991-sample hot-start Hornet recording, with paired ground-contact evidence at every source timestamp. The experiment remains restricted to this measured take and the tested Hornet/Caucasus/zero-wind configuration. General low-speed eligibility was not enabled.

| Phase | Measured result |
| --- | --- |
| Held inspection | More than 30 seconds observed; after startup, original XYZ retained, zero velocity and replay time, all 33 supported appearance channels retained; independent scene aircraft continued moving. |
| Countdown | Exactly 3.000 seconds; 150 telemetry samples retained original XYZ, zero velocity/replay time and initial supported state. |
| Release | Player acknowledgment followed the request by 1 ms; first native running observation was 17 ms later at replay time zero. Held-to-first-playing displacement was 0.00000142 m. |
| Taxi | Complete short take reached completion. All 992 playback contact samples were grounded with full health. Maximum adjacent displacement was 0.05642 m. |
| State retention | 32,703 changing-channel comparisons matched native requested state after animation and in mission sampling, within logging precision. |

Implementation fixes validated in this session: numeric normalization of the live unit identifier in contact capture; exact reference repair for the three witness-route values serialized by DCS; and ground-only pose restoration at the guarded pre-integration boundary. The six selected offline checks pass, and the repaired bridge also passes the captured loaded-mission check and its six refusal controls. Full raw evidence, source backups, analysis scripts and installed-package receipts are preserved locally; implementation and raw artifacts have not been committed or uploaded.

Measured limits remain explicit. Initial native startup substeps through 0.10 seconds showed a 0.02202 m height transient and a temporary attitude-component difference. The stable held attitude-component residual was 0.00005931. Moving position was up to 0.05641 m ahead of the command after native integration, with vertical error below 0.000892 m. Sampled strobe edges can select the preceding source row for one 20 ms sample at floating-point boundaries. These measurements are not agreed product tolerances or claims of exact rendered orientation.

This resolves the narrow held-staging/countdown/first-taxi trial. [Record and replay short taxi flights with stable ground contact](https://github.com/caw1517/DCSRecorder/issues/27) and [Agree measured tolerances and verify full-flight duration support](https://github.com/caw1517/DCSRecorder/issues/32) retain their broader validation and numerical-agreement work. Parked completion, illumination, takeoff/landing and general physics acceptance remain unverified. This experimental mission still removes the aircraft at completion.
