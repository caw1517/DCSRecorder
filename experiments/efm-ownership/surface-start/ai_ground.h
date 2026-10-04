#pragma once
#include <windows.h>
#include <cstdint>
#include "native_identity.h"
// woAIPlane (DCS 2.9.30.28536) keeps byte +0x26D3 of the complete object (SDK
// handle - 8) at 1 through taxi and the takeoff roll; it clears about 4 s after
// liftoff. With it clear, the AI's legacy flag crash path destroys the aircraft at
// the first ground contact after flight (takeoff-landing live-2..7, research #36).
// Grounded tape samples hold it at 1, as the AI itself does on the ground.
namespace surface_ai {
inline constexpr uintptr_t ground_flag=0x26d3;
// Returns -1 unreadable/unconfirmed, 0 already set, 1 written and confirmed.
inline int hold_ground_flag(const void* sdk_handle) {
    const auto address=reinterpret_cast<uintptr_t>(sdk_handle)-8+ground_flag;
    uint8_t value=0;
    if(!native_identity::read(address,value) || value>1)return -1;
    if(value==1)return 0;
    const uint8_t one=1;SIZE_T written=0;
    if(!WriteProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(address),&one,1,&written) || written!=1)return -1;
    return native_identity::read(address,value) && value==1 ? 1 : -1;
}
}
namespace surface_ai {
// AI mode int +0x7F4: 51 through taxi and the takeoff roll (live-7). Grounded
// samples after flight were left in mode 4 and DCS halved the object's update
// rate (live-8). Returns -1 unreadable/unconfirmed, 0 already 51, 1 written.
inline constexpr uintptr_t mode=0x7f4;
inline constexpr int32_t taxi_mode=51;
inline int hold_taxi_mode(const void* sdk_handle) {
    const auto address=reinterpret_cast<uintptr_t>(sdk_handle)-8+mode;
    int32_t value=0;
    if(!native_identity::read(address,value) || value<0 || value>0x44)return -1;
    if(value==taxi_mode)return 0;
    SIZE_T written=0;
    if(!WriteProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(address),&taxi_mode,sizeof taxi_mode,&written) || written!=sizeof taxi_mode)return -1;
    return native_identity::read(address,value) && value==taxi_mode ? 1 : -1;
}
}
