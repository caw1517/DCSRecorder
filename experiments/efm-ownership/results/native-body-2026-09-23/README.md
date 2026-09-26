# Native body read: inconclusive

DCS PID 36232, 2026-09-23 local time. Samples through object time 24.32 seconds all report `rejected`; no position or velocity was accepted. Same-run mission/runtime mapping identifies Probe as 16777472 and the native type remains woAIPlane with Registered displacement 8.

The captured plane instruction signature matches the expected bytes. The generic rejection did not identify which remaining guard or read failed. It would be incorrect to infer that the flight-model member is absent or validated from this run.

Follow-up diagnostic retains every guard and records distinct rejection reasons plus the actual primary vtable RVA. Build and existing callback-contract tests pass; only another in-simulator run can identify the live rejection. No native state was written.
