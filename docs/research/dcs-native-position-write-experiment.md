# Native position propagation and one-shot experiment

2026-09-25, installed DCS 2.9.29.27278. Findings are build-specific binary observations, not a supported SDK contract.

## Trace

The woAIPlane Registered/MovingObject subobject vtable at DCS RVA `0x1146ff8`, slot `0xb8`, contains a thunk at `0xcbf475`. It jumps through IAT `0x10f1720` to WorldGeneral's named `MovingObject::ChangePos(const wPosition3<float>&)` export, RVA `0x68940`.

A startup-only snapshot of WorldGeneral from process 34908, base `0x7ff8d6780000`, exposed its loaded code without running a mission. Only static code/read-only sections were captured. Full snapshots remain local and ignored.

ChangePos copies the input's 12 meaningful floats from four padded rows into a temporary pose, replaces nonfinite components with zero, calls `viObjectNode::ChangePos` via WorldGeneral IAT RVA `0x1e0060`, and conditionally refreshes spatial-query state. The target resolves to edObjects RVA `0xed00` using that process's loaded edObjects base. viObjectNode delegates to viObjectShape and viObject, then walks child nodes and invokes/invalidate updates. The base viObject method notifies a spatial structure; it does not copy the supplied pose into the MovingObject's current pose. Therefore calling ChangePos with a different temporary pose is not sufficient evidence of changing the authoritative pose.

`MovingObject::ForcePosition(const wPosition3<double>&)` at WorldGeneral RVA `0x68d50` supplies the missing write step. Machine code shows RCX as MovingObject `this` and RDX as the pose pointer. It copies input translation offsets `0x60/68/70` into receiver `+0x1c8/1d0/1d8`, converts all 12 meaningful doubles to floats in receiver pose `+0x174`, refreshes a time field at `+0x260`, then dispatches virtual slot `0xb8` with that updated float pose. These receiver-relative offsets become complete woAIPlane position `+0x1ac` and precise translation `+0x1d0` because the receiver begins at complete-object +8.

Evidence: [ChangePos](../../experiments/native-interface-inspection/WorldGeneral-ChangePos.txt), [ForcePosition](../../experiments/native-interface-inspection/WorldGeneral-ForcePosition.txt), and installed edObjects exports/disassembly. The probe does not use direct coordinate memory writes. No claim is made that ForcePosition synchronizes an independent flight model, changes velocity, prevents AI correction, or guarantees collision/wake behavior.

## Prepared experiment

At the first object callback at 5.0–5.2 seconds, attempt exactly one ForcePosition call adding 20 metres to world X. Copy the existing orientation and precise translation; change only X in the local argument. Preserve the original float orientation values by exact conversion to doubles. No repeated forcing or restoration to a stale pose occurs. Ending the mission discards the test aircraft.

Eligibility requires the dedicated probe runtime ID 16777472, prior successful null-path position guards, altitude between 1000 and 5000 metres, exact export RVA and entry bytes, readable pose, finite orthonormal basis within tolerance, and agreement between float and double translation within 0.1 metre. Any failed check records a rejection and ends the attempt. The DLL reports status plus before/after positions in `native-motion-<pid>.csv`; ordinary native and mission telemetry continues.

The DLL builds and existing callback-contract tests pass. Those tests do not execute the private function or prove thread safety; the first simulator run is the integration test. The prepared motion DLL has not been installed or run yet.

## Interpretation

- Guard rejection: no call; investigate the named guard.
- Immediate +20 m native displacement and independent mission displacement: position-change propagation demonstrated.
- Immediate displacement followed by return toward the unchanged baseline: later updates overwrite/correct the move.
- No mission displacement despite immediate native change: sampling or a separate authoritative representation remains unresolved.
- A surviving displacement is only a one-shot position change, not recorded-flight playback, attitude/velocity control, or physical fidelity.

Compare the previous deterministic mission run as a baseline, but use the immediate same-run before/after pair to establish what the call itself did. Longer divergence may include AI response and is not purely the applied displacement.

## Result

The test ran successfully in process 47372. Both immediate native readings and independent mission telemetry show exactly +20 m world X at five seconds. The pre-call Probe trajectory matches baseline exactly; the displacement survives later updates and gradually decreases to 15.23 m by time 13 seconds, consistent with AI correction. See [evidence and limits](../../experiments/efm-ownership/results/position-shift-2026-09-25/README.md). The earlier statement that the motion DLL had not run is superseded by this result. A bounded position-control primitive is demonstrated; faithful playback and physical fidelity remain unproven.
