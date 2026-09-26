# Native type diagnostic before physics access

The object lifecycle and mission/runtime-ID mapping are already established. The remaining bridge is from the opaque `Registered*` callback handle to the actual aircraft physics interface.

Targeted public-source research found no usable class headers or working aircraft-to-physics accessor. Additional export inspection of DCS.exe, Inter.dll, Transport.dll, edCore.dll and Scripting.dll did not establish such an accessor. Existing `Registered::cast_MovingObject` exports are virtual base methods; calling a named base implementation directly is not evidence of correct dynamic dispatch or object adjustment. No private member function has been invoked.

## Prepared read-only diagnostic

`experiments/efm-ownership/native_identity.h` reads the MSVC x64 runtime type metadata associated with the object supplied by DCS. Layouts are grounded in the installed Visual Studio `include/rttidata.h` and `crt/src/vcruntime/rtti.cpp`. It reads through `ReadProcessMemory` on the current process, validates the image and relative offsets, bounds class counts and names, and reports failures instead of dereferencing guessed object layouts. No object fields other than the vtable pointer are inspected; class metadata does not confer permission or knowledge to mutate private members.

The probe logs its result once, on the first simulation callback for each object, in `bin/probe-logs/native-types-<process>-<tick>.txt`. It records runtime object ID, module, dynamic class, subobject displacement and base-class metadata. It does not call internal DCS functions, apply forces, or patch code. Ordinary lifecycle logs and ID mapping continue unchanged.

Standalone checks pass for a known derived class accessed through a secondary base pointer, discovery of that base, rejection of null input, and all prior EFM/lifecycle checks. They validate the inspector on this compiler's ABI, not on the target DCS object.

## Next run and interpretation

Run EFM-Probe-ai for five simulation seconds from a fresh DCS process. Correlate the new native-type record with the same run's mission/runtime-ID map and callback log. A readable dynamic class/base hierarchy will guide current-build accessor analysis. Missing or unsupported metadata is a diagnostic failure, not a physics impossibility result.

Even a successful type read does not establish an aircraft-to-flight-model accessor, safe member layout, a compatible setter, or control over AI update ordering. Those must be evidenced before a force/pose experiment.

## Runtime result

The diagnostic succeeded: same-run evidence identifies the unoccupied Probe as `woAIPlane` in DCS.exe, with `Registered`/`MovingObject` at offset 8 from the complete object. The inheritance chain includes woAILA, woPlane, woLA and woLABase. No physics-object base was reported; an owned member or other bridge remains to be found. See [retained evidence](../../experiments/efm-ownership/results/native-type-2026-09-23/README.md). No further type-identification run is needed.
