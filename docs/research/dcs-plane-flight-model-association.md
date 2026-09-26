# Plane-to-flight-model association

Inspected 2026-09-23, installed DCS 2.9.29.27278. Offline decoding of a read-only startup snapshot establishes a build-specific member association; live state correspondence and control remain unproven.

The snapshot from PID 17076 captured only `.text`, `.rdata`, and `.pdata`. DCS image base was `0x7ff7c7970000`; AIFM base was `140704937541632`. Full binary snapshots stay in ignored local folders. The installed executable was not modified. Original DCS SHA-256: `09609a085f6bfd4a5215642878ba14fb0e6a8a0d0aad461d5b46c392f000ef41`.

The packed on-disk IAT does not correspond to the loaded callsites. Matching pointers in loaded `.rdata` against AIFM's named export addresses located the position getter at IAT RVA `0x10ed188` and setter at `0x10ed170`. The scan found 238 candidate call/jump references; only explicitly decoded sites are evidence. The captured `.pdata` does not form a valid runtime-function table, so the parser rejects it instead of claiming function boundaries.

## Evidence chain

- Loaded `.rdata` RVA `0x1146e70` points to code RVA `0x70fef0`. Walking backward to a validated MSVC complete-object locator identifies the primary vtable at `0x1146200`, subobject offset zero, type descriptor RVA `0x14d3730`. A bounded 128-byte read of that descriptor's name returned `.?AVwoAIPlane@@`.
- The method begins at `0x70fef0` and saves incoming `RCX` in `R14` at `0x70ff5f`. There are no subsequent writes to R14 in the decoded span through `0x710633`.
- At `0x7105f7`, `mov rcx,[r14+0x2f98]` supplies the receiver to `AIAerodyneFM::setPositionState`.
- At `0x71061a`, `mov rbx,[r14+0x2f98]`, followed by `mov rcx,rbx`, supplies the receiver to `AIAerodyneFM::getPosition` at `0x710628`.
- Therefore this build's complete `woAIPlane` object has its AIAerodyneFM pointer at `+0x2f98`. The earlier object callback gives its Registered subobject at `+8`, so this adjustment must precede the member read.
- A separate position getter path using member `+0x3e40` belongs to `woAIHelicopter`, established by its type descriptor. It must not be used for the plane.

See [bounded plane method disassembly](../../experiments/native-interface-inspection/DCS-plane-position-calls-disasm.txt), [resolved import index](../../experiments/native-interface-inspection/dcs-resolved-aifm-index.json), and [AIFM body getter contract](dcs-aifm-getter-contract.md).

## Next validation

The prepared native-body probe reads the complete plane's `+0x2f98` pointer, then the flight model's body pointer at `+0x20`, then position at body `+0x28` and velocity at `+0x40`. It requires exact runtime type, subobject displacement, primary vtable RVA, and two verified instruction signatures, and rejects unreadable or nonfinite samples. These guards are specific to this diagnostic build; they are not general compatibility support.

No private function is invoked and no aircraft state is written. `native-body-<pid>.csv` must be matched by object ID and time against independent mission telemetry before accepting the association in live simulation. Compilation and callback-contract CTest passed. The new diagnostic has not yet run in DCS; DCS must close before its DLL can be replaced.
