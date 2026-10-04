// THROWAWAY read-only Lua helper. No hooks, aircraft writes or retained objects.
#include "../native_identity.h"
#include "../native_capture_build.h"
#include <array>
#include <cmath>
#include <iomanip>
#include <sstream>

struct lua_State;
namespace {
using Current=void*(*)();
using RPM=float(*)(void*,int,bool);
using Scalar=float(*)(void*,int);
using Push=void(*)(lua_State*,const char*,size_t);
// Keep SEH leaves separate from C++ objects requiring stack unwinding.
bool current(Current fn,void*& object) {
    __try {object=fn();return true;} __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
bool values(void* object,RPM rpm,Scalar thrust,Scalar power,std::array<float,8>& out) {
    __try {
        for(int engine=1;engine<=2;++engine) {
            const int i=(engine-1)*4;
            out[i]=rpm(object,engine,true);out[i+1]=rpm(object,engine,false);
            out[i+2]=thrust(object,engine);out[i+3]=power(object,engine);
        }
        return true;
    } __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
bool executable(uintptr_t fn,HMODULE image) {
    MEMORY_BASIC_INFORMATION m{};
    return fn && VirtualQuery(reinterpret_cast<void*>(fn),&m,sizeof(m)) &&
        m.Type==MEM_IMAGE && m.AllocationBase==image &&
        (m.Protect&(PAGE_EXECUTE|PAGE_EXECUTE_READ|PAGE_EXECUTE_READWRITE|PAGE_EXECUTE_WRITECOPY));
}
std::string sample() {
    const auto cockpit=GetModuleHandleW(L"CockpitBase.dll");
    const auto sound=GetModuleHandleW(L"Sound.dll");
    if(!cockpit || !sound)return "UNAVAILABLE,modules_not_loaded";
    const auto fn=GetProcAddress(cockpit,"?c_LA@cockpit@@YAPEAVIwoLA@@XZ");
    const auto base=reinterpret_cast<uintptr_t>(cockpit);
    // Pinned c_LA implementation: current cockpit's IwHumanPlane -> IwoLA.
    const auto expected=native_capture_build::accessor;
    std::array<unsigned char,29> actual{};
    if(reinterpret_cast<uintptr_t>(fn)!=base+native_capture_build::cockpit_accessor ||
       !native_identity::read(base+native_capture_build::cockpit_accessor,actual) || actual!=expected)return "UNAVAILABLE,cockpit_build_guard";
    // Sound::JetEngineSounder::update receives IwoLA and invokes these slots.
    const std::array<unsigned char,6> call_rpm={0xff,0x90,0xd8,0,0,0};
    const std::array<unsigned char,6> call_thrust={0xff,0x90,0xe0,0,0,0};
    const std::array<unsigned char,6> call_power={0xff,0x90,0xf0,0,0,0};
    std::array<unsigned char,6> code{};
    const auto sb=reinterpret_cast<uintptr_t>(sound);
    if(!native_identity::read(sb+0x134c5f,code) || code!=call_rpm ||
       !native_identity::read(sb+0x134c8c,code) || code!=call_rpm ||
       !native_identity::read(sb+0x134cbb,code) || code!=call_thrust ||
       !native_identity::read(sb+0x134ca5,code) || code!=call_power)return "UNAVAILABLE,sound_build_guard";
    void* object=nullptr;
    if(!current(reinterpret_cast<Current>(fn),object) || !object)return "UNAVAILABLE,no_current_aircraft";
    const auto identity=native_identity::inspect(object);
    bool interface_matches=false;
    for(const auto& b:identity.bases)
        if(b.name==".?AVIwoLA@@" && b.member==identity.subobject_offset && b.vbtable<0)interface_matches=true;
    const std::string observed=identity.name+","+std::to_string(identity.subobject_offset);
    if(identity.status!="ok" || identity.module!="DCS.exe" || !interface_matches)
        return "UNAVAILABLE,aircraft_interface,"+identity.status+","+observed;
    uintptr_t table=0,rpm=0,thrust=0,power=0;
    const auto image=GetModuleHandleW(nullptr);
    if(!native_identity::read(reinterpret_cast<uintptr_t>(object),table) ||
       !native_identity::read(table+0xd8,rpm) || !native_identity::read(table+0xe0,thrust) ||
       !native_identity::read(table+0xf0,power) || !executable(rpm,image) ||
       !executable(thrust,image) || !executable(power,image))return "UNAVAILABLE,getter_identity,"+observed;
    std::array<float,8> out{};
    if(!values(object,reinterpret_cast<RPM>(rpm),reinterpret_cast<Scalar>(thrust),reinterpret_cast<Scalar>(power),out))
        return "UNAVAILABLE,getter_exception,"+observed;
    void* after=nullptr;
    if(!current(reinterpret_cast<Current>(fn),after) || after!=object)return "UNAVAILABLE,aircraft_changed";
    for(float value:out)if(!std::isfinite(value))return "UNAVAILABLE,nonfinite_value,"+observed;
    std::ostringstream row;row<<std::setprecision(12)<<"OK,"<<observed<<','<<GetCurrentThreadId();
    for(float value:out)row<<','<<value;
    const auto ib=reinterpret_cast<uintptr_t>(image);
    row<<','<<rpm-ib<<','<<thrust-ib<<','<<power-ib;
    return row.str();
}
}
extern "C" __declspec(dllexport) int dcs_native_engine_sample(lua_State* state) {
    const auto lua=GetModuleHandleW(L"lua.dll");
    const auto push=reinterpret_cast<Push>(lua?GetProcAddress(lua,"lua_pushlstring"):nullptr);
    if(!push)return 0;
    std::string result;
    try {result=sample();}catch(...){result="UNAVAILABLE,helper_exception";}
    push(state,result.data(),result.size());return 1;
}
