Prepared and installed a single-variable roll-rate A/B diagnostic; live result pending.

The null-FM update at DCS RVA 0x712408..0x712541 integrates local rates from complete woAIPlane +0x1e8/+0x1ec/+0x1f0 into its orientation. The roll interpretation is corroborated by WorldGeneral::MovingObject::VectorAngular returning receiver+0x1e0, equivalent to complete+0x1e8 for the verified callback subobject. The previously noticed roll rotation at 0x712b69 is a separate conditional branch and is not established as the airborne cause.

The same formation mission now runs pose-only control at 5–15 s, clears only local roll rate after each pose command at 15–30 s, then returns to pose-only at 30–43 s. All control releases afterward. Existing type/build/ID/altitude guards plus a new instruction signature and bounded finite-rate checks restrict the intervention. Before/after rates are recorded; analysis assigns each interval to its preceding command. Matching-time comparison with the previous baseline is needed because path bank varies between phases.

Predictions: reduced disturbance supports persistent roll integration; renewed rate with unchanged disturbance supports AI overwriting it before integration. Visible jitter must still be judged in cockpit. This does not establish a fix or physical playback fidelity.

Both CTests pass. The analyzer reproduces baseline numbers and passes a synthetic phase-boundary/one-degree rotation check. Prior DLL preserved; new installed SHA-256 79A80B3DD80FF24C33A02125C2404D437BC8520997B1081D1FE426A7F60BD637. Local evidence: docs/research/dcs-roll-rate-ab-experiment.md. Keeping this decision open pending live comparison.
