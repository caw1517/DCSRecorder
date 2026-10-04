#pragma once
#include "native_body.h"
#include "turn_path.h"
#ifdef HORNET_GROUND_PROTOTYPE
#include "ground-start/tape_gate.h"
#endif
#ifdef HORNET_RELEASE_PROTOTYPE
#include "held-start/policy.h"
#endif
#ifdef HORNET_HELD_PROTOTYPE
#include "held-start/policy.h"
#endif

namespace native_velocity {
inline bool read(const void* handle,std::array<float,3>& value) {
    return native_identity::read(reinterpret_cast<uintptr_t>(handle)+0x254,value);
}
inline const char* validate(const void* handle,const turn_path::Motion& motion,bool ground=false) {
    const auto module=GetModuleHandleW(L"WorldGeneral.dll");
    const auto base=reinterpret_cast<uintptr_t>(module);
    const auto entry=GetProcAddress(module,"?VectorVelocity@MovingObject@@UEAAAEBVVec3f@osg@@AEBV23@@Z");
    if(!module || reinterpret_cast<uintptr_t>(entry)!=base+native_build::world(0x69310)) return "velocity_export_mismatch";
    std::array<unsigned char,10> bytes{};
    if(!native_identity::read(base+native_build::world(0x69310),bytes) ||
       bytes!=std::array<unsigned char,10>{0x48,0x89,0x5c,0x24,0x08,0x57,0x48,0x83,0xec,0x20})
        return "velocity_entry_mismatch";
    std::array<unsigned char,8> getter{};
    if(!native_identity::read(base+native_build::world(0x69390),getter) ||
       getter!=std::array<unsigned char,8>{0x48,0x8d,0x81,0x54,0x02,0,0,0xc3})
        return "velocity_layout_mismatch";
    const auto image=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    for(const auto& site:std::array<std::pair<uintptr_t,std::array<unsigned char,9>>,3>{{
        {0x712408,{0xf3,0x45,0x0f,0x10,0xa6,0xf0,0x01,0,0}},
        {0x712411,{0xf3,0x41,0x0f,0x10,0xae,0xec,0x01,0,0}},
        {0x712435,{0xf3,0x45,0x0f,0x10,0x9e,0xe8,0x01,0,0}}}}) {
        std::array<unsigned char,9> instruction{};
        if(!native_identity::read(image+native_build::dcs(site.first),instruction) || instruction!=site.second)
            return "angular_layout_mismatch";
    }
    std::array<float,3> current{},rates{};
    if(!read(handle,current) || !native_identity::read(reinterpret_cast<uintptr_t>(handle)+0x1e0,rates))
        return "motion_state_unreadable";
    double speed2=0;
    for(int i=0;i<3;++i) {
        if(!std::isfinite(current[i]) || std::abs(current[i])>400 ||
           !std::isfinite(rates[i]) ||
           !std::isfinite(motion.velocity[i]) || !std::isfinite(motion.angular[i])
#ifndef HORNET_STAGED_PROTOTYPE
           || std::abs(rates[i])>10 || std::abs(motion.angular[i])>1
#endif
           ) return "motion_state_guard_rejected";
        speed2+=motion.velocity[i]*motion.velocity[i];
    }
#ifdef HORNET_GROUND_PROTOTYPE
    // Separate, fingerprint-bound experiment. Normal airborne guards are unchanged.
    if(!ground_trial::speed_allowed(speed2))return "ground_velocity_rejected";
#elif defined(HORNET_HELD_PROTOTYPE)
    // Only this separately built hold-only controller can command zero motion.
    // It cannot replay low-speed tapes or release into flight.
    if(!held_start::stationary(motion)) return "held_motion_rejected";
#elif defined(HORNET_SURFACE_PROTOTYPE)
    // Grounded tape samples (source in_air=0) may be stationary or slow. Airborne
    // samples keep the release rule: zero hold motion or the airborne range.
    if(ground ? speed2>turn_path::max_speed*turn_path::max_speed :
       (!held_start::stationary(motion) &&
        (speed2<70*70 || speed2>turn_path::max_speed*turn_path::max_speed)))return "velocity_speed_rejected";
#elif defined(HORNET_RELEASE_PROTOTYPE)
    // Only this separate release control accepts zero hold motion or the
    // existing airborne speed range. Recording-reader guards stay intact.
    if(!held_start::stationary(motion) &&
       (speed2<70*70 || speed2>turn_path::max_speed*turn_path::max_speed))return "velocity_speed_rejected";
#else
    if(speed2<70*70 || speed2>turn_path::max_speed*turn_path::max_speed) return "velocity_speed_rejected";
#endif
    return "valid";
}
// Only after native_motion::apply's identity, pose and motion guards pass.
inline const char* write_validated(const void* handle,const turn_path::Motion& motion) {
    const auto entry=GetProcAddress(GetModuleHandleW(L"WorldGeneral.dll"),
        "?VectorVelocity@MovingObject@@UEAAAEBVVec3f@osg@@AEBV23@@Z");
    using Setter=const void*(*)(const void*,const float*);
    reinterpret_cast<Setter>(entry)(handle,motion.velocity.data());
    SIZE_T written=0;
    if(!WriteProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(reinterpret_cast<uintptr_t>(handle)+0x1e0),
        motion.angular.data(),sizeof(motion.angular),&written) || written!=sizeof(motion.angular))
        return "angular_write_failed";
    std::array<float,3> v{},w{};
    if(!read(handle,v) || !native_identity::read(reinterpret_cast<uintptr_t>(handle)+0x1e0,w) ||
       v!=motion.velocity || w!=motion.angular) return "motion_write_unconfirmed";
    return "called";
}
}
