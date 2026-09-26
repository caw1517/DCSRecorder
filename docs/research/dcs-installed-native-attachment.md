# Installed native attachment investigation

Inspected DCS 2.9.29.27278 on 2026-09-23. One player and one account remain hard requirements. No internal physics functions were invoked and no simulator binary was patched.

## Concrete new candidate: object lifecycle callbacks

The installed [ed_object_access.h](<D:/DCS World/API/include/ed_object_access.h>) declares four callbacks:

- `ed_setup_object_api(const ed_object_api_entry*)`: receives the object API after the module is loaded.
- `ed_on_object_create(ED_OBJECT_HANDLE, uint64_t&)`: documented for object types declared by the module.
- `ed_on_object_simulate(ED_OBJECT_HANDLE, uint64_t&, double)`: documented per-object simulation callback.
- `ed_on_object_destroy(ED_OBJECT_HANDLE, uint64_t&)`: documented before destruction.

Unlike the EFM callbacks examined earlier, these include an opaque per-object handle and a cookie. The API table provides object ID, visual-argument reading, and visual-argument writing. **It provides no position or force setter.** Therefore lifecycle success would establish a point of execution associated with an object, not physics authority.

The installed [SouthAtlanticAssets entry.lua](<D:/DCS World/CoreMods/tech/SouthAtlanticAssets/entry.lua:13>) combines `binaries` with `load_immediately = true`; the Supercarrier entry also uses immediate loading. This supplies a concrete alternative to the previous lazy-loaded probe registration. It does not prove the callback API applies to our aircraft.

## Prepared experiment

The existing probe now sets `load_immediately = true` and exports the four object callbacks. `object_probe.cpp` logs setup, creation, sampled simulation and destruction with the API-provided object ID. It leaves the cookie and object state untouched. The mission observer now appends `Unit:getID()` to each telemetry row. The existing EFM pulse code is retained so any change in EFM execution is also detectable.

The DLL was compiled for x64. CTest passed its original EFM pulse checks and new mock object-API invocation/cookie-preservation checks. Compile-time assertions match callback signatures to the installed header. Export inspection confirms all four callbacks and `ed_fm_simulate`. These checks are not runtime evidence.

Installed DLL SHA-256: `5213503864A71AFAF1A07355ABF4D54855BFFCCDE271B600E0F4EF92CFF8B50E`.

Run `EFM-Probe-ai` from a fresh DCS process for at least 15 simulation seconds. Interpret evidence separately:

1. **DLL loaded:** check dcs.log for OwnershipProbe.dll. This only validates startup loading.
2. **API setup:** check `objects-<process>-<tick>.csv` in the mod's `bin/probe-logs` directory. Setup alone does not identify an aircraft.
3. **Target lifecycle:** require repeated object callbacks with an ID matching the independently observed Probe. If no IDs match, investigate the identifier namespace before claiming attachment.
4. **EFM execution:** independently check for fresh `callbacks-*.csv` state/simulate rows. An object callback is not an EFM callback.
5. **Physics control:** remains unresolved unless target-correlated forces/attitude response are actually demonstrated. Read-only lifecycle logging cannot establish it.

Runtime follow-up: the startup-loaded module received object callbacks. A subsequent same-process ID-mapping check confirmed that the callback ID belongs to the unoccupied Probe (mission ID 9001 -> runtime ID 16777472), while the stock player maps to 16777728. The callback stream reaches 496 calls at its sampled 9.9-second row. See [identity evidence](../../experiments/efm-ownership/results/object-identity-2026-09-23/README.md). This establishes target-associated execution, not a force/pose interface or ordinary AI EFM execution.

## Internal exported symbols: leads, not callable contracts

Read-only `dumpbin /exports` snapshots are stored under `experiments/native-interface-inspection/`. Relevant names include:

- AIFM.dll: `EagleFM::AIFM::AIPlaneFM::setControlVector`, `AIAerodyneFM::setPositionState`, and `AIAerodyneFM::getDynamicBody`.
- FMBase.dll: `EagleFM::DynamicBody::addForce_l`, `addForce_w`, `addMoment_l`, and `addMoment_w`.

These establish named native operations in this build, not a public mod interface or that any given aircraft uses them. The shipped API does not provide the required class declarations, object ownership rules, or conversion from `Registered*` to these physics objects. Symbol presence is insufficient to infer object layout or safely invoke a member function. No guessed casts, memory writes, or function calls were made.

If lifecycle callbacks work, the next investigation is the specific bridge between the identified aircraft and its physics object, including update timing and interaction with native AI. Dynamic EFM compilation remains downstream of that bridge.
