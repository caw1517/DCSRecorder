# Installed AIFM getter and DynamicBody contracts

Inspected 2026-09-23. This is offline evidence from the installed primary binaries, not a supported SDK contract or a simulator test. No functions were invoked and no running aircraft state was changed.

## Build identity and evidence

Both images are x64 PE32+, preferred base `0x180000000`. All addresses below are RVAs unless explicitly called object offsets. ASLR means the displayed preferred addresses are not live addresses.

| Binary | PE timestamp | SHA-256 |
| --- | --- | --- |
| `D:/DCS World/bin/AIFM.dll` | `6A896035` | `CBAB55CF488EDDA7D3EF4E5C86C276AEC48789878C7EF260168961AD5AAD4FE8` |
| `D:/DCS World/bin/FMBase.dll` | `6A895CC9` | `E657830312AF8FCD1EECCA790403EA5791DD59A7060FD1D6DC6AC0BE31090FE6` |

Sources: [AIFM exports](../../experiments/native-interface-inspection/AIFM-exports.txt), [FMBase exports](../../experiments/native-interface-inspection/FMBase-exports.txt), [bounded AIFM disassembly](../../experiments/native-interface-inspection/AIFM-getters-setPositionState-disasm.txt), [bounded FMBase disassembly](../../experiments/native-interface-inspection/FMBase-body-contract-disasm.txt), and [AIFM import excerpt](../../experiments/native-interface-inspection/AIFM-FMBase-imports-excerpt.txt). Generated with MSVC `dumpbin` 14.42.34444.0 `/exports`, `/headers`, `/imports`, and `/disasm /range:0xSTART,0xEND`. Hashes obtained with `Get-FileHash`.

## Getter findings

High confidence for this exact binary pair:

| Export | RVA | Observed behavior |
| --- | --- | --- |
| `AIAerodyneFM::getDynamicBody() const` | `A2070` | `mov rax,[rcx+20h]; ret`. Returns the pointer stored at AIAerodyneFM object offset `0x20`; export declares a const DynamicBody pointer. |
| `AIAerodyneFM::getPosition() const` | `A2240` | Loads that pointer and copies 24 bytes at DynamicBody offset `0x28` to caller output. Three doubles; no callee calls or object writes. |
| `DynamicBody::getPosition() const` | `55580` | Returns address `this+0x28`, consistent with exported const vector reference and the preceding copy getter. |
| `DynamicBody::getVelocity_w() const` | `55840` | Returns address `this+0x40`, exported const vector reference. |
| `AIAerodyneFM::getYaw() const` | `A2510` | Calls `DynamicBody::getDynamicState`, reads float at returned state offset `0x18`, converts to double. |
| `AIAerodyneFM::getPitch() const` | `A21D0` | Same, state offset `0x1C`. |
| `AIAerodyneFM::getRoll() const` | `A2280` | Same, state offset `0x20`. |

For the vector value-return getter, machine code directly establishes `RCX=this`, `RDX=caller output buffer`, and `RAX=that output buffer` on return. Do not substitute a pointer-return signature for a value-return signature. Reference-return getters return an internal address in RAX. These observations do not establish source-compatible C++ declarations or ownership/lifetime guarantees.

The yaw/pitch/roll functions use AIFM IAT slot `EF070`, which is the fifteenth entry (zero-based index 14) of its FMBase imports and names `getDynamicState`. That function at FMBase RVA `73810` constructs the output state and obtains angles from the representation at body offset `0x18`. It also calls the local-rotation-speed getter. Therefore angle getters are not as narrowly side-effect-free as the position getter: the downstream cache behavior has not been fully audited. Angle units and Euler conventions have not been established here. [Sources: bounded disassembly and import excerpt above.]

## Setter findings: broader than position assignment

`AIAerodyneFM::setPositionState` at RVA `A2CD0` takes two const `Vector<3,double>&` arguments and three floats, as encoded in the export. The implementation:

1. Obtains a `DynamicState` through `getDynamicState`.
2. Replaces state bytes `0x00..0x17` with the first vector (position).
3. Replaces state bytes `0x40..0x57` with the second vector (world velocity, cross-checked against DynamicBody::init and getVelocity_w).
4. Writes its three float arguments to state `0x18`, `0x1C`, `0x20` (yaw, pitch, roll by the getters).
5. Calls FMBase `DynamicBody::init` via IAT `EF080`.

`DynamicBody::init` at RVA `74130` is not a narrow position setter. Its complete bounded body clears object bytes `0x364..0x369`, writes position, calls an orientation conversion routine, writes velocity, computes world rotation speed from the state's local rotation speed, copies state `0x28..0x3F` into body `0xE0..0xF7`, and copies several other fields and a flag at body `0x110`. The inspected getDynamicState implementation initializes state `0x28..0x3F` to zero and does not replace it before returning. Thus this setter path also zeros body `0xE0..0xF7`; the semantic name of that field is not established here. Orientation computation can also refresh caches. It does not justify describing setPositionState as preserving all unrelated physical state. [Source: both bounded disassembly files.]

## Moment interface

`DynamicBody::addMoment_l` at RVA `71670` accepts a const three-double vector reference. After helper calls it adds the resulting three doubles to body offsets `0xC8`, `0xD0`, and `0xD8`. `resetMoment` at RVA `559D0` zeros exactly those three doubles. This establishes an accumulation buffer, not an instantaneous attitude setter. Helper semantics and force integration ordering are not fully traced. The `_l` suffix and the corresponding `_w` export suggest local/world conventions, but axes, units, limits, accumulation reset timing, and observable response require independent validation. [Source: FMBase exports and bounded disassembly.]

## What this permits next

Once the aircraft-to-AIAerodyneFM association is independently established, a read-only diagnostic can compare body position and velocity against mission telemetry. Position is the best first check because the getter is only pointer reads and a 24-byte copy. Reject null or unreadable pointers and any build mismatch; do not assume that any plausible pointer at an aircraft offset is an AIAerodyneFM.

This note does not establish the woAIPlane member containing its flight model, the validity of a pointer in a live callback, control over a playback aircraft, compatibility across updates, thread safety, or whether the AI's own next update would overwrite a change. Those remain separate proof obligations. No writes or setter calls are proposed by these results alone.
