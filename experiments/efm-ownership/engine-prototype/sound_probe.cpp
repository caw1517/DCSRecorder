// THROWAWAY: measure whether DCS requests ordinary EFM parameters for this object.
// Always return the bundled sample's exact value. No sound or engine state writes.
#include <windows.h>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <map>
#include <mutex>
#include <string>
#include "sound_probe.h"
extern "C" double engine_sample_get_param(unsigned index);
namespace {
struct Count { uint64_t calls=0;double first=0,last=0; };
std::mutex guard;
std::ofstream parameter_log;
std::map<unsigned,Count> counters;
uint64_t total=0;
bool initialized=false;
void initialize() {
    if(initialized)return;initialized=true;
    HMODULE module=nullptr;wchar_t path[32768]{};
    if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
        reinterpret_cast<LPCWSTR>(&initialize),&module) || !GetModuleFileNameW(module,path,32768))return;
    auto directory=std::filesystem::path(path).parent_path()/"sound-logs";
    std::error_code error;std::filesystem::create_directories(directory,error);if(error)return;
    parameter_log.open(directory/("parameters-"+std::to_string(GetCurrentProcessId())+"-"+std::to_string(GetTickCount64())+".csv"));
    parameter_log<<std::setprecision(17)<<"event,object_id,total_calls,index,index_calls,first,last\n";
    parameter_log<<"[SOUND-PARAM-PROBE]ready,0,0,,,,\n";parameter_log.flush();
}
}
namespace engine_sound_probe {
void lifecycle(const char* event,uint64_t id) {
    std::lock_guard<std::mutex> lock(guard);initialize();
    parameter_log<<event<<','<<id<<','<<total<<",,,,\n";
    for(const auto& pair:counters)parameter_log<<"parameter_summary,"<<id<<','<<total<<','<<pair.first<<','
        <<pair.second.calls<<','<<pair.second.first<<','<<pair.second.last<<'\n';
    parameter_log.flush();
}
}
extern "C" __declspec(dllexport) double ed_fm_get_param(unsigned index) {
    const double result=engine_sample_get_param(index);
    std::lock_guard<std::mutex> lock(guard);initialize();++total;
    auto& count=counters[index];++count.calls;if(count.calls==1)count.first=result;count.last=result;
    if(count.calls==1) {parameter_log<<"parameter_first,0,"<<total<<','<<index<<",1,"<<result<<','<<result<<'\n';parameter_log.flush();}
    return result;
}
