#pragma once
#include "native_identity.h"
#include <array>
#include <cmath>

// Build-specific staged recorded playback. The recorded basis already
// contains nose attitude; the null-FM presentation path adds these two fields.
// Caller owns the guarded aircraft and simulation thread, and invokes this
// immediately before native integration, after the normal controller update.
namespace native_presentation_pitch {
constexpr uintptr_t pitch_offset=native_build::pitch_offset,rate_offset=0x22b4;
struct State { uintptr_t owner=0;float pitch=0,rate=0;bool active=false; };
inline bool put(uintptr_t p,float value) {
    SIZE_T written=0;
    return WriteProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(p),&value,sizeof(value),&written)
        && written==sizeof(value);
}
inline bool read_pair(uintptr_t p,float& pitch,float& rate) {
    return native_identity::read(p+pitch_offset,pitch) && native_identity::read(p+rate_offset,rate);
}
inline bool layout_valid() {
    const auto image=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    std::array<unsigned char,8> a{},b{};
    return native_identity::read(image+native_build::dcs(0x6d41eb),a) &&
        a==std::array<unsigned char,8>{0xf3,0x0f,0x10,0x8e,native_build::pitch_displacement_low,0x4d,0,0} &&
        native_identity::read(image+native_build::dcs(0x6d41f6),b) &&
        b==std::array<unsigned char,8>{0xf3,0x0f,0x10,0x86,0xb4,0x22,0,0};
}
inline const char* clear_validated(const void* handle,State& state) {
    const auto p=reinterpret_cast<uintptr_t>(handle);
    if(!p || (state.active && state.owner!=p))return "presentation_owner_rejected";
    float pitch=0,rate=0;
    if(!read_pair(p,pitch,rate) || !std::isfinite(pitch) || !std::isfinite(rate) ||
       std::abs(pitch)>45 || std::abs(rate)>2000)return "presentation_fields_rejected";
    if(!put(p+pitch_offset,0) || !put(p+rate_offset,0)) {
        const bool restored_pitch=put(p+pitch_offset,pitch);
        const bool restored_rate=put(p+rate_offset,rate);
        return restored_pitch && restored_rate ? "presentation_write_failed" : "presentation_rollback_failed";
    }
    float check_pitch=1,check_rate=1;
    if(!read_pair(p,check_pitch,check_rate) || check_pitch!=0 || check_rate!=0) {
        const bool restored_pitch=put(p+pitch_offset,pitch);
        const bool restored_rate=put(p+rate_offset,rate);
        return restored_pitch && restored_rate ? "presentation_readback_failed" : "presentation_rollback_failed";
    }
    if(!state.active || pitch!=0 || rate!=0) {state.pitch=pitch;state.rate=rate;}
    state.owner=p;state.active=true;return "called";
}
inline const char* restore(const void* handle,State& state) {
    if(!state.active)return "presentation_inactive";
    const auto p=reinterpret_cast<uintptr_t>(handle);
    if(p!=state.owner)return "presentation_restore_owner_rejected";
    float pitch=0,rate=0;
    if(!read_pair(p,pitch,rate))return "presentation_restore_unreadable";
    // If DCS has already replaced either field, preserve its newer state.
    if(pitch!=0 || rate!=0) {state={};return "presentation_already_replaced";}
    if(!put(p+pitch_offset,state.pitch) || !put(p+rate_offset,state.rate))return "presentation_restore_failed";
    if(!read_pair(p,pitch,rate) || pitch!=state.pitch || rate!=state.rate)return "presentation_restore_unconfirmed";
    state={};return "presentation_restored";
}
}
