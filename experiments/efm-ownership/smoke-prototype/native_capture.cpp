// Read-only, build-pinned smoke observation. No setter calls or retained objects.
#include "../native_identity.h"
#include "../native_capture_build.h"
#include <array>
#include <sstream>

struct lua_State;
namespace {
using Current=void*(*)();
using Push=void(*)(lua_State*,const char*,size_t);
bool current(Current fn,void*& out) {
    __try {out=fn();return true;} __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
template<size_t N> bool matches(uintptr_t address,const std::array<unsigned char,N>& expected) {
    std::array<unsigned char,N> actual{};
    return native_identity::read(address,actual) && actual==expected;
}
std::string sample() {
    const auto cockpit=GetModuleHandleW(L"CockpitBase.dll");
    if(!cockpit)return "UNAVAILABLE,no_cockpit";
    const auto base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    const auto fn=GetProcAddress(cockpit,"?c_LA@cockpit@@YAPEAVIwoLA@@XZ");
    const auto accessor=native_capture_build::accessor;
    // Smoke control iterates 32-byte station entries; byte +24 is emitter enabled.
    const std::array<unsigned char,40> entries={0x4c,0x8b,0x89,0x78,0x25,0,0,
        0x48,0x8b,0xf1,0x8b,0xca,0x48,0x8b,0x86,0x80,0x25,0,0,0x49,0x2b,0xc1,
        0x48,0xc1,0xf8,5,0x48,0x3b,0xc8,0x0f,0x83,7,3,0,0,0x8b,0xf9,0x48,0xc1,0xe7};
    const std::array<unsigned char,10> enabled_check={0x80,0x7f,0x18,0,0x0f,0x85,0xcd,2,0,0};
    const std::array<unsigned char,6> aggregate_write={0x88,0x83,0x40,0x23,0,0};
    if(reinterpret_cast<uintptr_t>(fn)!=reinterpret_cast<uintptr_t>(cockpit)+native_capture_build::cockpit_accessor ||
       !matches(reinterpret_cast<uintptr_t>(fn),accessor) || !matches(base+native_build::dcs(0x65a1a3),entries) ||
       !matches(base+native_build::dcs(0x65a1f6),enabled_check) || !matches(base+native_build::dcs(0x65eae8),aggregate_write))
        return "UNAVAILABLE,build_guard";
    void* object=nullptr;
    if(!current(reinterpret_cast<Current>(fn),object) || !object)return "UNAVAILABLE,no_player";
    const auto id=native_identity::inspect(object);
    if(id.status!="ok" || id.module!="DCS.exe" || id.name!=".?AVwHumanAircraft@@" || id.subobject_offset!=8)
        return "UNAVAILABLE,player_identity";
    bool interface_ok=false;
    for(const auto& b:id.bases)if(b.name==".?AVIwoLA@@" && b.member==8 && b.vbtable<0)interface_ok=true;
    if(!interface_ok)return "UNAVAILABLE,player_interface";
    const auto plane=reinterpret_cast<uintptr_t>(object);
    uintptr_t pylons=0,pylons_end=0,effects=0,effects_end=0,station=0;
    if(!native_identity::read(plane+0x4b0,pylons) || !native_identity::read(plane+0x4b8,pylons_end) ||
       !pylons || pylons_end<pylons || pylons_end-pylons!=10*sizeof(uintptr_t) ||
       !native_identity::read(pylons+9*sizeof(uintptr_t),station) || !station)
        return "UNAVAILABLE,station_layout";
    const auto store=native_identity::inspect(reinterpret_cast<void*>(station));
    std::array<unsigned char,4> classification{};
    if(store.status!="ok" || store.module!="DCS.exe" || store.name!=".?AVwoAIPilon@@" || store.subobject_offset!=0 ||
       !native_identity::read(station+0x2c8,classification) ||
       classification[0]!=4 || classification[1]!=15 || classification[2]!=50)
        return "UNAVAILABLE,no_smoke_generator";
    if(!native_identity::read(plane+0x2578,effects) || !native_identity::read(plane+0x2580,effects_end) ||
       !effects || effects_end<effects || effects_end-effects!=10*32)
        return "UNAVAILABLE,emitter_layout";
    unsigned char on=0,any=0;
    if(!native_identity::read(effects+9*32+24,on) || !native_identity::read(plane+0x2340,any) || on>1 || any>1)
        return "UNAVAILABLE,invalid_state";
    void* after=nullptr;
    if(!current(reinterpret_cast<Current>(fn),after) || after!=object)return "UNAVAILABLE,player_changed";
    uintptr_t current_pylons=0,current_effects=0,current_station=0;
    if(!native_identity::read(plane+0x4b0,current_pylons) || current_pylons!=pylons ||
       !native_identity::read(plane+0x2578,current_effects) || current_effects!=effects ||
       !native_identity::read(pylons+9*sizeof(uintptr_t),current_station) || current_station!=station)
        return "UNAVAILABLE,loadout_changed";
    std::ostringstream out;out<<"OK,10,"<<unsigned(on)<<','<<unsigned(any)<<','<<unsigned(classification[3]);
    return out.str();
}
}
extern "C" __declspec(dllexport) int dcs_native_smoke_sample(lua_State* state) {
    const auto lua=GetModuleHandleW(L"lua.dll");
    const auto push=reinterpret_cast<Push>(lua?GetProcAddress(lua,"lua_pushlstring"):nullptr);
    if(!push)return 0;
    std::string result;
    try{result=sample();}catch(...){result="UNAVAILABLE,helper_exception";}
    push(state,result.data(),result.size());return 1;
}
