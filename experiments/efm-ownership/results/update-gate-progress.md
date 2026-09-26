Prepared and installed a per-aircraft update-suppression diagnostic, following the user's FS Recorder/slew suggestion. Live result pending.

A [first-person FSX implementation report](https://www.fsdeveloper.com/forum/threads/smooth-ai-movement-the-old-favorite.17374/) describes smooth relative motion through slew-rate control. This does not establish FS Recorder's implementation. DCS's object API has no equivalent, documented setOnOff is limited to ground/naval groups, and the probe's null AIAerodyneFM member prevents using its setFreeze export.

Static tracing instead identified complete woAIPlane+0x4fea as an early-return gate in two native routines: RVA 0x6fbf60 and pose integrator 0x70fef0. Original semantics are unknown. The diagnostic changes only this per-object byte during 15–30 s, preserving the previous roll-only test otherwise, then restores it. Exact branch signatures, identity, ID, initial value, altitude and readback are guarded; restoration is also attempted on abort/destruction. No executable patching or global freeze.

The log now measures whether pose stays unchanged between commands and confirms gate restoration. If callbacks cease, ending the mission discards the object; no unsynchronized recovery write is attempted. Successful suppression alone would not prove smooth rendering because continuous velocity/interpolation may still be necessary.

Build, both CTests, and synthetic interval-attribution/reset checks pass. Prior DLL preserved. New SHA-256 D142E080BA5CBC222D48357F3E0D423FF6618075DDAC9474581607DD3A346C48. Local protocol: docs/research/dcs-update-gate-experiment.md. Awaiting the same formation mission for 55 s, especially close formation during 15–30 s and restoration at 30 s. Decision remains open.
