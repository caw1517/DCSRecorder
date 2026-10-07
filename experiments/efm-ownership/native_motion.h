#pragma once
#include "native_body.h"
#include "native_velocity.h"
#include <cstring>

// Bounded trajectory experiment. Only the dedicated probe
// object is eligible, and the caller enforces the narrow experiment time window.
namespace native_motion {
// DCS 2.9.29.27278: RVA 0x712408..0x712541 integrates these local
// rates as dForward = wz*up - wy*right, dUp = wx*right - wz*forward.
// Complete woAIPlane +0x1e8 is therefore local roll rate, in radians/s.
inline bool read_rates(const void* handle, std::array<float,3>& rates) {
    return native_identity::read(reinterpret_cast<uintptr_t>(handle)-8+0x1e8,rates);
}
inline const char* apply(const void* handle, uint32_t object_id,
                         native_body::Sample& before, native_body::Sample& after,
                         const std::array<double,16>* commanded, std::array<double,16>* captured=nullptr,
                         bool neutralize_roll=false,const turn_path::Motion* motion=nullptr, uint64_t expected_id=16777472,
                         bool ground=false) {
    if(!expected_id || object_id!=expected_id) return "wrong_object_id";
    if(std::strcmp(native_body::sample(handle,before),"object_position_candidate")!=0)
        return "state_guard_rejected";
#ifndef HORNET_STAGED_PROTOTYPE
    if(before.position[1]<1000 || before.position[1]>5000) return "altitude_guard_rejected";
#endif
    const auto module=GetModuleHandleW(L"WorldGeneral.dll");
    const auto entry=GetProcAddress(module,"?ForcePosition@MovingObject@@UEAAXAEBV?$wPosition3@N@@@Z");
    if(!module || reinterpret_cast<uintptr_t>(entry)!=reinterpret_cast<uintptr_t>(module)+native_build::world(0x68d50))
        return "export_mismatch";
    std::array<unsigned char,10> bytes{};
    if(!native_identity::read(reinterpret_cast<uintptr_t>(entry),bytes) ||
       bytes!=std::array<unsigned char,10>{0x48,0x89,0x5c,0x24,0x08,0x57,0x48,0x83,0xec,0x20})
        return "entry_signature_mismatch";
    // MovingObject starts at the callback handle. Pose basis rows are padded
    // float4s at +0x174; ForcePosition consumes padded double4s.
    std::array<float,16> current{};
    std::array<double,3> precise{};
    const auto object=reinterpret_cast<uintptr_t>(handle);
    if(!native_identity::read(object+0x174,current) ||
       !native_identity::read(object+0x1c8,precise)) return "pose_unreadable";
    alignas(16) std::array<double,16> pose{};
    for(int row=0;row<3;++row) {
        double norm=0;
        for(int axis=0;axis<3;++axis) {
            const double v=current[row*4+axis];
            if(!std::isfinite(v)) return "invalid_basis";
            pose[row*4+axis]=v; norm+=v*v;
        }
        if(std::abs(norm-1)>0.02) return "invalid_basis";
        for(int previous=0;previous<row;++previous) {
            double dot=0;
            for(int axis=0;axis<3;++axis) dot+=pose[row*4+axis]*pose[previous*4+axis];
            if(std::abs(dot)>0.02) return "invalid_basis";
        }
    }
    for(int axis=0;axis<3;++axis) {
        if(!std::isfinite(precise[axis]) || std::abs(precise[axis]-before.position[axis])>0.1)
            return "position_representations_disagree";
        pose[12+axis]=precise[axis];
    }
    pose[15]=1;
    if(captured) { *captured=pose; return "captured"; }
    if(!commanded) return "missing_command";
    for(double v:*commanded) if(!std::isfinite(v)) return "nonfinite_command";
    double distance2=0;
    for(int i=0;i<3;++i) distance2+=std::pow((*commanded)[12+i]-pose[12+i],2);
#ifdef HORNET_SURFACE_PROTOTYPE
    // For about 2.6 s after liftoff, DCS's taxiing AI pulls the aircraft straight
    // down to the runway before every step; the tape pose is restored each time.
    // The gap equals the height climbed: 9.1 m on the accepted circuit, over 10 m
    // on a steeper climb (6 October 2026). Allow only that pattern: native pose
    // directly below the command, within a bounded height.
    const double horizontal2=std::pow((*commanded)[12]-pose[12],2)+std::pow((*commanded)[14]-pose[14],2);
    const double below=(*commanded)[13]-pose[13];
    if(distance2>100 && !(horizontal2<=100 && below>0 && below<=150)) return "command_step_too_large";
#else
    if(distance2>100) return "command_step_too_large";
#endif
    if(motion) {
        const auto validation=native_velocity::validate(handle,*motion,ground);
        if(std::strcmp(validation,"valid")!=0) return validation;
    }
    if(neutralize_roll) {
        const auto image=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
        std::array<unsigned char,9> instruction{};
        std::array<float,3> rates{};
        if(!native_identity::read(image+native_build::dcs(0x712435),instruction) ||
           instruction!=std::array<unsigned char,9>{0xf3,0x45,0x0f,0x10,0x9e,0xe8,0x01,0,0})
            return "roll_signature_mismatch";
        if(!read_rates(handle,rates)) return "rates_unreadable";
        for(float v:rates) if(!std::isfinite(v) || std::abs(v)>10) return "rates_guard_rejected";
    }
    pose=*commanded;
    using ForcePosition=void(*)(const void*,const double*);
    reinterpret_cast<ForcePosition>(entry)(handle,pose.data());
    if(motion) {
        const auto result=native_velocity::write_validated(handle,*motion);
        if(std::strcmp(result,"called")!=0) return result;
    } else if(neutralize_roll) {
        // Single-variable diagnostic, not the final playback controller.
        // No executable patching; only this guarded probe object's roll state.
        const float zero=0;
        SIZE_T written=0;
        if(!WriteProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(object-8+0x1e8),
                               &zero,sizeof(zero),&written) || written!=sizeof(zero))
            return "roll_write_failed";
        std::array<float,3> rates{};
        if(!read_rates(handle,rates) || rates[0]!=0) return "roll_write_unconfirmed";
    }
    if(std::strcmp(native_body::sample(handle,after),"object_position_candidate")!=0)
        return "called_after_read_rejected";
    return "called";
}
}
