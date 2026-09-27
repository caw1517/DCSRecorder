#pragma once
// THROWAWAY, read-only evidence for the pinned build. Never invokes native methods.
#include "../native_identity.h"
#include "../native_animation_hook.h"
#include <array>
#include <cmath>
#include <cstring>
#include <iomanip>
#include <ostream>

namespace sound_boundary {
template<size_t N> bool matches(uintptr_t address,const std::array<unsigned char,N>& expected) {
    std::array<unsigned char,N> actual{};
    return native_identity::read(address,actual) && actual==expected;
}
inline bool layout_matches(uintptr_t image,uintptr_t world) {
    // Instructions establishing descriptor, string, native sounder, Lua reference,
    // engine count, FM member and per-engine array. Fail closed on a changed build.
    return image && world &&
        matches(image+0x641492,std::array<unsigned char,7>{0x48,0x8b,0x98,0xd8,2,0,0}) &&
        matches(image+0x6414a2,std::array<unsigned char,8>{0x48,0x83,0xbb,0x50,0x0c,0,0,0}) &&
        matches(image+0x6414b4,std::array<unsigned char,12>{0x48,0x8d,0xbb,0x40,0x0c,0,0,0x48,0x83,0x7f,0x18,0x0f}) &&
        matches(image+0x6099af,std::array<unsigned char,7>{0x48,0x8b,0x89,0x28,0x28,0,0}) &&
        matches(image+0x6099d1,std::array<unsigned char,7>{0x48,0x89,0x83,0x18,0x28,0,0}) &&
        matches(world+0x6a9ff,std::array<unsigned char,8>{0x48,0x83,0xb9,0x80,2,0,0,0}) &&
        matches(world+0x6aa44,std::array<unsigned char,7>{0x48,0x89,0x83,0x80,2,0,0}) &&
        matches(image+0x66d164,std::array<unsigned char,7>{0x0f,0xb6,0x81,0x11,8,0,0}) &&
        matches(image+0x66d174,std::array<unsigned char,7>{0x48,0x8b,0x81,0x98,0x2f,0,0}) &&
        matches(image+0x66d180,std::array<unsigned char,7>{0x48,0x8b,0x89,0xa0,0x2f,0,0}) &&
        matches(image+0x66d197,std::array<unsigned char,11>{0x48,0xff,0x60,0x68,0x48,0xff,0xa0,0x88,0,0,0}) &&
        matches(image+0x66d1b3,std::array<unsigned char,9>{0xf3,0x0f,0x10,0x81,0xa8,0x2f,0,0,0xc3});
}
inline bool name_at(uintptr_t address,std::string& name) {
    // The descriptor uses a 32-byte string with inline capacity 15.
    uint64_t size=0,capacity=0;
    if(!native_identity::read(address+16,size) || !native_identity::read(address+24,capacity) ||
       size>160 || capacity<size) return false;
    if(capacity>15 && !native_identity::read(address,address))return false;
    std::string result;
    for(size_t i=0;i<=size;++i) {
        unsigned char c=0;if(!native_identity::read(address+i,c))return false;
        if(i==size) {if(c)return false;break;}
        if(c<32 || c>126)return false;
        result+=static_cast<char>(c);
    }
    name=result;return true;
}
inline int direct_float_offset(const std::array<unsigned char,16>& code) {
    // Decode only an entire trivial getter: movss xmm0,[rcx+positive displacement]; ret.
    if(code[0]!=0xf3 || code[1]!=0x0f || code[2]!=0x10)return -1;
    if(code[3]==0x41 && code[5]==0xc3 && code[4]<128)return code[4];
    int32_t offset=-1;
    if(code[3]==0x81 && code[8]==0xc3)std::memcpy(&offset,code.data()+4,4);
    return offset>=0 && offset<=0x1000?offset:-1;
}
inline void getter(std::ostream& out,uintptr_t engine,uintptr_t table,size_t slot) {
    uintptr_t fn=0;std::array<unsigned char,16> code{};
    if(!native_identity::read(table+slot,fn) || !native_identity::read(fn,code)) {
        out << "{\"status\":\"unreadable\"}";return;
    }
    MEMORY_BASIC_INFORMATION region{};
    if(!VirtualQuery(reinterpret_cast<void*>(fn),&region,sizeof(region)) || region.Type!=MEM_IMAGE) {
        out << "{\"status\":\"not_image\"}";return;
    }
    char path[32768]{};
    GetModuleFileNameA(static_cast<HMODULE>(region.AllocationBase),path,sizeof(path));
    std::string module=path;module=module.substr(module.find_last_of("/\\")+1);
    out << "{\"module\":" << std::quoted(module) << ",\"rva\":"
        << fn-reinterpret_cast<uintptr_t>(region.AllocationBase) << ",\"prefix\":\"";
    for(auto c:code)out << std::hex << std::setw(2) << std::setfill('0') << unsigned(c);
    out << std::dec << std::setfill(' ') << "\"";
    const int offset=direct_float_offset(code);float value=0;
    if(offset>=0 && native_identity::read(engine+offset,value) && std::isfinite(value))
        out << ",\"direct_float\":" << value;
    // Complex getters remain uninterpreted. Reading their code is not invoking them.
    out << '}';
}
inline void sample(std::ostream& out,const void* handle,uint64_t id,double time) {
    out << "{\"id\":" << id << ",\"time\":" << time;
    const auto identity=native_identity::inspect(handle);
    const auto image=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    const auto world=reinterpret_cast<uintptr_t>(GetModuleHandleW(L"WorldGeneral.dll"));
    const auto complete=reinterpret_cast<uintptr_t>(handle)-identity.subobject_offset;
    uintptr_t table=0;
    if(identity.status!="ok" || identity.module!="DCS.exe" || identity.name!=".?AVwoAIPlane@@" ||
       identity.subobject_offset!=8 || !native_identity::read(complete,table) ||
       (table!=image+0x1146200 && !native_animation_hook::recognizes(complete,table,image+0x1146200))) {
        out << ",\"status\":\"identity_rejected\"}\n";out.flush();return;
    }
    if(!layout_matches(image,world)) {
        out << ",\"status\":\"layout_rejected\"}\n";out.flush();return;
    }
    uintptr_t descriptor=0,native=0,wrapper=0,bound=0,reference=0,fm=0,engines=0;
    unsigned char count=0;float aggregate=0;std::string name;
    const bool read=native_identity::read(complete+0x2d8,descriptor) && descriptor &&
        name_at(descriptor+0xc40,name) && native_identity::read(complete+0x2818,native) &&
        native_identity::read(complete+0x2828,wrapper) &&
        native_identity::read(reinterpret_cast<uintptr_t>(handle)+0x280,reference) &&
        native_identity::read(complete+0x811,count) && count<=8 &&
        native_identity::read(complete+0x2f98,fm) && native_identity::read(complete+0x2fa0,engines) &&
        native_identity::read(complete+0x2fa8,aggregate);
    if(!read) {out << ",\"status\":\"fields_unreadable\"}\n";out.flush();return;}
    if(wrapper)native_identity::read(wrapper,bound);
    const auto sound=native_identity::inspect(reinterpret_cast<void*>(native));
    out << ",\"status\":\"read\",\"sounder_name\":" << std::quoted(name)
        << ",\"lua_reference_present\":" << (reference?"true":"false")
        << ",\"wrapper_bound\":" << (bound==complete?"true":"false")
        << ",\"native_type\":" << std::quoted(sound.name)
        << ",\"native_module\":" << std::quoted(sound.module)
        << ",\"native_identity_status\":" << std::quoted(sound.status)
        << ",\"fm_present\":" << (fm?"true":"false")
        << ",\"engine_count\":" << unsigned(count) << ",\"aggregate_rpm\":";
    if(std::isfinite(aggregate))out << aggregate;else out << "null";
    out << ",\"engines\":[";
    for(unsigned i=0;i<count;++i) {
        if(i)out << ',';
        uintptr_t engine=0,vtable=0;
        if(!engines || !native_identity::read(engines+i*sizeof(uintptr_t),engine) || !engine ||
           !native_identity::read(engine,vtable)) {out << "null";continue;}
        const auto info=native_identity::inspect(reinterpret_cast<void*>(engine));
        out << "{\"type\":" << std::quoted(info.name) << ",\"module\":" << std::quoted(info.module)
            << ",\"core\":";getter(out,engine,vtable,0x68);
        out << ",\"fan\":";getter(out,engine,vtable,0x88);out << '}';
    }
    out << "]}\n";out.flush();
}
}
