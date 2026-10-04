#pragma once
// [DEBUG-nose] Read-only observation of the DCS presentation-pose boundary.
// Temporary, opt-in, staged prototype only. Offsets are from the inspected
// DCS 2.9.29.27468 Position(double) path; names do not assert field semantics.
#include "native_identity.h"
#include <filesystem>
#include <fstream>
#include <iomanip>
namespace pose_diagnostics {
inline std::ofstream file;
inline void open(const std::filesystem::path& folder) {
    file.open(folder / ("DEBUG-nose-pose-"+std::to_string(GetCurrentProcessId())+".csv"));
    file << "object_id,object_time,phase,read_ok,cache_time,pose_time,rotation_time,"
            "field_4db4,field_22b4,field_56cc,field_56d4,field_21f4,field_21f8,field_21fc,field_2200";
    for(const char* prefix:{"native","cached"})for(int i=0;i<16;++i)file << ',' << prefix << i;
    file << '\n' << std::setprecision(12);
}
inline void write(const void* handle,uint64_t id,double time,const char* phase) {
    if(!file.is_open())return;
    const auto image=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    std::array<unsigned char,8> signature{};
    if(!native_identity::read(image+0x6d3870,signature) ||
       signature!=std::array<unsigned char,8>{0xf2,0x0f,0x11,0x4c,0x24,0x10,0x55,0x56})return;
    const auto p=reinterpret_cast<uintptr_t>(handle);
    double cache_time=0,pose_time=0,rotation_time=0;
    std::array<float,7> fields{};unsigned char flag=0;
    std::array<float,16> native{},cached{};
    bool ok=native_identity::read(p+0x4d68,cache_time) &&
        native_identity::read(p+0x260,pose_time) && native_identity::read(p+0x5870,rotation_time) &&
        native_identity::read(p+0x21f4,flag) && native_identity::read(p+0x174,native) &&
        native_identity::read(p+0x217c,cached);
    const std::array<uintptr_t,7> offsets{0x4db4,0x22b4,0x56cc,0x56d4,0x21f8,0x21fc,0x2200};
    for(size_t i=0;i<fields.size();++i)ok=native_identity::read(p+offsets[i],fields[i]) && ok;
    file << id << ',' << time << ',' << phase << ',' << ok;
    if(ok) {
        file << ',' << cache_time << ',' << pose_time << ',' << rotation_time;
        for(size_t i=0;i<4;++i)file << ',' << fields[i];
        file << ',' << static_cast<unsigned>(flag);
        for(size_t i=4;i<fields.size();++i)file << ',' << fields[i];
        for(float v:native)file << ',' << v;
        for(float v:cached)file << ',' << v;
    }
    file << '\n';file.flush();
}
}
