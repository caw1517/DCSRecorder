#pragma once
#include "native_identity.h"
#include <array>
#include <cmath>
#ifdef HORNET_RECORDED_PROTOTYPE
#include "native_step_hook.h"
#endif

// Build-specific, read-only probe. No native getter/setter is invoked.
namespace native_body {
struct Sample { double position[3]{}, velocity[3]{}; };
inline const char* sample(const void* handle, Sample& out) {
    const auto identity=native_identity::inspect(handle);
    if(identity.status!="ok" || identity.module!="DCS.exe" ||
       identity.name!=".?AVwoAIPlane@@" || identity.subobject_offset!=8) return "identity_mismatch";
    const auto image=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    const auto aifm=reinterpret_cast<uintptr_t>(GetModuleHandleW(L"AIFM.dll"));
    // Verified instruction loading the plane's FM member and the body getter.
    std::array<unsigned char,7> plane{};
    std::array<unsigned char,5> getter{};
    if(!aifm) return "aifm_not_loaded";
    if(!native_identity::read(image+0x7105f7,plane) ||
       plane!=std::array<unsigned char,7>{0x49,0x8b,0x8e,0x98,0x2f,0,0}) return "plane_signature_mismatch";
    if(
       !native_identity::read(aifm+0xa2070,getter) ||
       getter!=std::array<unsigned char,5>{0x48,0x8b,0x41,0x20,0xc3}) return "body_signature_mismatch";
    const auto complete=reinterpret_cast<uintptr_t>(handle)-identity.subobject_offset;
    uintptr_t vtable=0,fm=0,body=0;
    if(!native_identity::read(complete,vtable)) return "vtable_unreadable";
    if(vtable!=image+0x1146200
#ifdef HORNET_RECORDED_PROTOTYPE
       && !native_step_hook::recognizes(complete,vtable,image+0x1146200)
#endif
       ) return "vtable_mismatch";
    if(!native_identity::read(complete+0x2f98,fm)) return "fm_unreadable";
    if(!fm) {
        // Null-member branch at RVA 0x7110ff reads this float triplet.
        // Its position meaning remains a hypothesis until mission comparison.
        std::array<unsigned char,9> instruction{};
        if(!native_identity::read(image+0x711152,instruction) ||
           instruction!=std::array<unsigned char,9>{0xf3,0x41,0x0f,0x58,0x86,0xac,0x01,0,0})
            return "object_position_signature_mismatch";
        float candidate[3]{};
        if(!native_identity::read(complete+0x1ac,candidate)) return "object_position_unreadable";
        for(int i=0;i<3;++i) {
            if(!std::isfinite(candidate[i])) return "object_position_nonfinite";
            out.position[i]=candidate[i];
        }
        return "object_position_candidate";
    }
    if(!native_identity::read(fm+0x20,body)) return "body_unreadable";
    if(!body) return "body_null";
    if(!native_identity::read(body+0x28,out.position)) return "position_unreadable";
    if(!native_identity::read(body+0x40,out.velocity)) return "velocity_unreadable";
    for(int i=0;i<3;++i)
        if(!std::isfinite(out.position[i]) || !std::isfinite(out.velocity[i])) return "nonfinite_state";
    return "read";
}
}
