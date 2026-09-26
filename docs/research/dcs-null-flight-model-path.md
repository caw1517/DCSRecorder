# Null flight-model member: allocation gate and alternate state path

2026-09-25, offline inspection of the previously captured DCS 2.9.29.27278 startup code. No private native calls or state writes were performed.

## Allocation gate

The routine beginning at DCS RVA `0x6cf420` preserves incoming RCX in RSI. At `0x6cf47e` it passes RSI+8 to `MovingObject::Type()`. The returned wsType is tested with `cmp word ptr [rax+4],0x20` at `0x6cf492`. If unequal, execution skips allocation. If equal, the routine allocates 0x8b0 bytes, calls `AIPlaneFM::AIPlaneFM()`, installs a derived vtable, and writes the result to `[rsi+0x2f98]` at `0x6cf4c8`. Later code calls AIPlaneFM::setN_obj and init when that member is nonnull.

The WorldGeneral import identification is corroborated by 12 adjacent resolved pointers matching its exports under a common inferred module base `0x7ff871490000`; it is not based solely on one address suffix. AIFM import names come from the existing resolved export index:

- IAT RVA `0x10ed370`: AIPlaneFM constructor.
- `0x10ed358`: AIPlaneFM::setN_obj.
- `0x10ed360`: AIPlaneFM::init.

This is a type-dependent allocation path, not evidence of a general missing registration option. The installed wsTypes.lua assigns MIG_29K the value 32, but the precise wsType field layout has not been established here. Identifying the tested field with that Lua constant is only a hypothesis; no descriptor changes are justified by it.

Evidence: [allocation disassembly](../../experiments/native-interface-inspection/DCS-aifm-allocation-gate.txt).

## Alternate branch

The previously RTTI-identified woAIPlane method at RVA `0x70fef0` loads the member at `0x70ffb4` and jumps to `0x7110ff` when it is null. That branch continues aircraft calculations rather than treating null as an error. Subject to additional branches, it uses a float triplet at complete-object offsets `0x1ac`, `0x1b0`, `0x1b4`, adding a scaled triplet from `0x17c..0x184`. These are position-like inputs, but their world-coordinate meaning and correspondence to mission observations require measurement.

Evidence: [null-member branch](../../experiments/native-interface-inspection/DCS-null-fm-state-path.txt). This is a bounded excerpt, not a complete account of the alternate update algorithm.

## Prepared measurement

The read-only probe retains its type, primary vtable, code signature, and memory-read checks. When the member is null, an additional instruction signature permits reading only the candidate float triplet. Rows are explicitly labelled `object_position_candidate`; velocity columns are blank. No body pointer is fabricated and no model is constructed or attached.

Build and callback-contract tests pass. These tests do not validate the candidate's meaning. Next live gate is comparing the candidate against mission position telemetry for the same runtime object, allowing for sample timing and float precision. Even a successful comparison would establish state access, not control or physical participation.

## Live result

The 2026-09-25 run established position correspondence: 130 accepted native samples, 128 overlapping comparisons, 0.02054 m RMS and 0.03381 m maximum difference after fitting a 20 ms native-sampling delay. The comparison against the occupied Observer remains over 1 km away. See [saved evidence and method](../../experiments/efm-ownership/results/object-position-2026-09-25/README.md). Position access is now validated for this build and configuration; control remains unproven.
