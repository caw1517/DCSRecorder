// Read-only object-layout diagnostic. Never installs hooks or calls native methods.
#include <windows.h>
#include <cstddef>
#include <cstdint>
#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <mutex>
#include <unordered_map>
#include "ed_object_access.h"
#include "../native_identity.h"
#include "layout_guards.h"

namespace {
const ed_object_api_entry* api=nullptr;
std::mutex mutex;
std::ofstream output;
std::unordered_map<ED_OBJECT_HANDLE,double> next_sample;
void open_log() {
    if(output.is_open())return;
    HMODULE self=nullptr;wchar_t path[32768]{};
    if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
        reinterpret_cast<LPCWSTR>(&open_log),&self) || !GetModuleFileNameW(self,path,32768))return;
    auto folder=std::filesystem::path(path).parent_path()/"layout-logs";
    std::filesystem::create_directories(folder);
    output.open(folder/("layout-"+std::to_string(GetCurrentProcessId())+"-"+std::to_string(GetTickCount64())+".jsonl"));
    output<<std::setprecision(12);
}
void sample(ED_OBJECT_HANDLE handle,double time) {
    open_log();
    if(!output)return;
    auto emit=[&](const char* status){output<<"{\"time\":"<<time<<",\"status\":"<<std::quoted(status)<<"}\n";output.flush();};
    if(!layout_guards::valid()){emit("build_guard_refused");return;}
    const auto identity=native_identity::inspect(handle);
    if(identity.status!="ok" || identity.module!="DCS.exe" || identity.name!=".?AVwoAIPlane@@" || identity.subobject_offset!=8) {
        output<<"{\"time\":"<<time<<",\"status\":\"identity_refused\",\"type\":"<<std::quoted(identity.name)
              <<",\"offset\":"<<identity.subobject_offset<<"}\n";output.flush();return;
    }
    const auto p=reinterpret_cast<uintptr_t>(handle),object=p-8;
    const auto image=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    uintptr_t table=0,fm=0;unsigned char engines=0;
    float coarse[3]{},velocity[3]{},rates[3]{},pitch=0,pitch_rate=0;
    double precise[3]{};
    if(!native_identity::read(object,table) || table!=image+0x1149210 ||
       !native_identity::read(object+0x2f98,fm) || !native_identity::read(object+0x811,engines) ||
       !native_identity::read(object+0x1ac,coarse) || !native_identity::read(p+0x1c8,precise) ||
       !native_identity::read(p+0x254,velocity) || !native_identity::read(p+0x1e0,rates) ||
       !native_identity::read(p+0x4dcc,pitch) || !native_identity::read(p+0x22b4,pitch_rate)) {
        emit("field_read_refused");return;
    }
    bool finite=std::isfinite(pitch)&&std::isfinite(pitch_rate);
    for(int i=0;i<3;++i)finite=finite&&std::isfinite(coarse[i])&&std::isfinite(precise[i])&&std::isfinite(velocity[i])&&std::isfinite(rates[i]);
    if(!finite){emit("nonfinite_fields");return;}
    const auto id=api&&api->ed_get_object_id?api->ed_get_object_id(handle):0;
    output<<"{\"time\":"<<time<<",\"status\":\"read\",\"id\":"<<id<<",\"fm_present\":"<<(fm?"true":"false")
          <<",\"engine_count\":"<<unsigned(engines)<<",\"pitch\":"<<pitch<<",\"pitch_rate\":"<<pitch_rate;
    auto array=[&](const char* name,const auto& values){output<<",\""<<name<<"\":[";for(int i=0;i<3;++i){if(i)output<<',';output<<values[i];}output<<']';};
    array("position",precise);array("coarse_position",coarse);array("velocity",velocity);array("angular",rates);
    output<<"}\n";output.flush();
}
}
extern "C" __declspec(dllexport) void ed_setup_object_api(const ed_object_api_entry* value) {
    std::lock_guard<std::mutex> guard(mutex);api=value;
}
extern "C" __declspec(dllexport) void ed_on_object_create(ED_OBJECT_HANDLE handle,uint64_t&) {
    std::lock_guard<std::mutex> guard(mutex);next_sample[handle]=0;
}
extern "C" __declspec(dllexport) void ed_on_object_simulate(ED_OBJECT_HANDLE handle,uint64_t&,double time) {
    std::lock_guard<std::mutex> guard(mutex);
    auto it=next_sample.find(handle);
    if(it==next_sample.end() || !std::isfinite(time) || time<it->second)return;
    it->second=time+0.1;
    try{sample(handle,time);}catch(...){/* Observational failure must not affect the mission. */}
}
extern "C" __declspec(dllexport) void ed_on_object_destroy(ED_OBJECT_HANDLE handle,uint64_t&) {
    std::lock_guard<std::mutex> guard(mutex);next_sample.erase(handle);
    if(output){output<<"{\"status\":\"destroyed\"}\n";output.flush();}
}
