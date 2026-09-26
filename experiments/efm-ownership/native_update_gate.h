#pragma once
#include "native_body.h"
#include <cstring>

// Experimental per-object gate, not an identified/public freeze API.
// In this exact DCS build, complete+0x4fea gates both RVA 0x6fbf60
// and the pose integrator at 0x70fef0. Preserve its initial value.
namespace native_update_gate {
struct Lease { bool active=false; unsigned char original=0; };
inline const char* set(const void* handle, uint32_t id, bool enabled, Lease& lease) {
    if(!enabled && !lease.active) return "inactive";
    if(id!=16777472) return "gate_wrong_id";
    native_body::Sample sample{};
    if(std::strcmp(native_body::sample(handle,sample),"object_position_candidate")!=0)
        return "gate_identity_rejected";
    const auto image=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    const std::array<unsigned char,13> physics{0x80,0xb9,0xea,0x4f,0,0,0,0x0f,0x85,0x9d,0x3b,0,0};
    const std::array<unsigned char,13> control{0x80,0xb9,0xea,0x4f,0,0,0,0x0f,0x85,0x7b,0x4a,0,0};
    std::array<unsigned char,13> bytes{};
    if(!native_identity::read(image+0x70ff62,bytes) || bytes!=physics ||
       !native_identity::read(image+0x6fbfd9,bytes) || bytes!=control)
        return "gate_signature_rejected";
    const auto address=reinterpret_cast<uintptr_t>(handle)-8+0x4fea;
    unsigned char current=0;
    if(!native_identity::read(address,current)) return "gate_unreadable";
    if(enabled && !lease.active) {
        if(current!=0 || sample.position[1]<1000 || sample.position[1]>5000)
            return "gate_initial_state_rejected";
        lease.original=current;
    }
    const unsigned char desired=enabled ? 1 : lease.original;
    SIZE_T written=0;
    // Mark ownership before the write so a partial/uncertain outcome still
    // attempts restoration through the abort path on this live object.
    lease.active=true;
    if(!WriteProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(address),&desired,1,&written) || written!=1)
        return "gate_write_failed";
    if(!native_identity::read(address,current) || current!=desired) return "gate_readback_failed";
    lease.active=enabled;
    return enabled ? "suppressed" : "restored";
}
}
