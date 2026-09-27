// THROWAWAY: SDK-only appearance replay on a separately registered Hornet.
// No pose/velocity writes, physical-control commands, or private native access.
#include <windows.h>
#include <cstdint>
#include <cstddef>
#include "ed_object_access.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <mutex>
#include <string>
#include <type_traits>
#include <unordered_map>
#include <vector>

namespace {
constexpr std::array<int,14> channels{0,3,5,9,10,11,12,13,14,15,16,17,18,21};
constexpr int elapsed_arg=998,status_arg=999;
using Values=std::array<float,channels.size()>;
struct Sample { double t; Values values; };
struct Object {
    uint64_t id=0,cookie=0,calls=0;
    double start=-1,last=-1;
    bool valid=false,previous=false;
    Values requested{};
};
const ed_object_api_entry* api=nullptr;
std::mutex guard;
std::unordered_map<ED_OBJECT_HANDLE,Object> objects;
std::vector<Sample> tape;
std::ofstream trace,events;
bool initialized=false,loaded=false;
uint64_t serial=0;

void initialize() {
    if(initialized)return;
    initialized=true;
    HMODULE module=nullptr;
    if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
        reinterpret_cast<LPCWSTR>(&initialize),&module))return;
    wchar_t path[32768]{};
    if(!GetModuleFileNameW(module,path,32768))return;
    const auto folder=std::filesystem::path(path).parent_path();
    std::error_code error;
    std::filesystem::create_directories(folder/"state-logs",error);
    if(error)return;
    const auto run=std::to_string(GetCurrentProcessId())+"-"+std::to_string(GetTickCount64());
    trace.open(folder/"state-logs"/("state-"+run+".csv"));
    events.open(folder/"state-logs"/("events-"+run+".csv"));
    if(!trace || !events)return;
    trace << std::setprecision(10);
    events << std::setprecision(10) << "event,id,time,detail\n";
    trace << "id,call,time,elapsed,previous_dt,arg,previous_requested,before,requested,after\n";
    std::ifstream file(folder/"exterior-state.txt");
    std::string header;size_t count=0;
    if(!(file>>header>>count) || header!="DCS_EXTERIOR_PROTOTYPE_V1" || count<2 || count>10000) {
        events << "tape_rejected,0,0,header\n";events.flush();return;
    }
    for(int expected:channels) {int actual=-1;if(!(file>>actual) || actual!=expected)return;}
    for(size_t i=0;i<count;++i) {
        Sample row{};
        if(!(file>>row.t) || !std::isfinite(row.t) || (i==0 && row.t!=0))return;
        if(i && (!(row.t>tape.back().t) || row.t-tape.back().t>0.15))return;
        for(size_t c=0;c<channels.size();++c) {
            if(!(file>>row.values[c]) || !std::isfinite(row.values[c]) ||
               row.values[c] < ((c<3 || c==13)?0.0f:-1.0f) || row.values[c]>1.0f)return;
        }
        tape.push_back(row);
    }
    std::string extra;if(file>>extra)return;
    if(tape.back().t<=0 || tape.back().t>240)return;
    loaded=true;events << "tape_loaded,0,0," << tape.size() << '\n';events.flush();
}
Values at(double t) {
    t=std::clamp(t,0.0,tape.back().t);
    const auto it=std::upper_bound(tape.begin(),tape.end(),t,[](double a,const Sample& b){return a<b.t;});
    const auto index=std::clamp<size_t>(it-tape.begin(),1,tape.size()-1)-1;
    const auto& a=tape[index];const auto& b=tape[index+1];
    const double u=(t-a.t)/(b.t-a.t);
    Values values{};
    for(size_t i=0;i<values.size();++i)values[i]=static_cast<float>(a.values[i]+u*(b.values[i]-a.values[i]));
    return values;
}
bool available(ED_OBJECT_HANDLE handle) {
    if(!api || !api->ed_get_object_id || !api->ed_get_object_args || !api->ed_set_single_arg)return false;
    const auto args=api->ed_get_object_args(handle);
    return args.data && args.size>status_arg;
}
void event(const char* name,const Object& object,double t,const char* detail) {
    if(events) {events << name << ',' << object.id << ',' << t << ',' << detail << '\n';events.flush();}
}
}
extern "C" __declspec(dllexport) void ed_setup_object_api(const ed_object_api_entry* entry) {
    std::lock_guard<std::mutex> held(guard);api=entry;initialize();
}
extern "C" __declspec(dllexport) void ed_on_object_create(ED_OBJECT_HANDLE handle,uint64_t& cookie) {
    std::lock_guard<std::mutex> held(guard);initialize();
    cookie=++serial;
    Object object;object.cookie=cookie;
    object.valid=handle && loaded && available(handle);
    if(object.valid) {object.id=api->ed_get_object_id(handle);object.valid=object.id!=0;}
    objects[handle]=object;event(object.valid?"create":"create_rejected",object,0,loaded?"sdk":"tape");
}
extern "C" __declspec(dllexport) void ed_on_object_simulate(ED_OBJECT_HANDLE handle,uint64_t& cookie,double time) {
    std::lock_guard<std::mutex> held(guard);
    const auto found=objects.find(handle);if(found==objects.end())return;
    auto& object=found->second;
    if(!object.valid || object.cookie!=cookie || !available(handle) || api->ed_get_object_id(handle)!=object.id)return;
    if(!std::isfinite(time) || (object.last>=0 && time<object.last)) {
        object.valid=false;api->ed_set_single_arg(handle,status_arg,0.75f);event("clock_rejected",object,time,"stopped");return;
    }
    if(object.start<0) {object.start=time;event("start",object,time,"sdk_only");}
    const double elapsed=time-object.start;
    const auto values=at(elapsed);
    const auto before_view=api->ed_get_object_args(handle);
    Values before{};
    for(size_t i=0;i<channels.size();++i)before[i]=before_view.data[channels[i]];
    for(size_t i=0;i<channels.size();++i)api->ed_set_single_arg(handle,channels[i],values[i]);
    const auto after_view=api->ed_get_object_args(handle);
    if(!after_view.data || after_view.size<=status_arg) {object.valid=false;event("view_lost",object,time,"stopped");return;}
    bool matches=true;++object.calls;
    for(size_t i=0;i<channels.size();++i) {
        const auto actual=after_view.data[channels[i]];
        matches=matches && std::isfinite(actual) && std::abs(actual-values[i])<0.00001f;
        trace << object.id << ',' << object.calls << ',' << time << ',' << elapsed << ',';
        if(object.previous)trace << time-object.last;
        trace << ',' << channels[i] << ',';
        if(object.previous)trace << object.requested[i];
        trace << ',' << before[i] << ',' << values[i] << ',' << actual << '\n';
    }
    trace.flush();
    if(!trace)matches=false;
    api->ed_set_single_arg(handle,elapsed_arg,static_cast<float>(elapsed/1000.0));
    api->ed_set_single_arg(handle,status_arg,matches?(elapsed>=tape.back().t?0.5f:0.25f):0.75f);
    if(!matches) {object.valid=false;event("write_rejected",object,time,"stopped");}
    if(object.last>=0 && object.last-object.start<tape.back().t && elapsed>=tape.back().t)event("sequence_complete",object,time,"holding_endpoint");
    object.requested=values;object.previous=true;object.last=time;
}
extern "C" __declspec(dllexport) void ed_on_object_destroy(ED_OBJECT_HANDLE handle,uint64_t& cookie) {
    std::lock_guard<std::mutex> held(guard);
    const auto found=objects.find(handle);
    if(found!=objects.end()) {event("destroy",found->second,found->second.last,"finished");objects.erase(found);}
}
static_assert(std::is_same_v<decltype(&ed_setup_object_api),PFN_ED_SETUP_OBJECT_API>);
static_assert(std::is_same_v<decltype(&ed_on_object_create),PFN_ED_ON_OBJECT_CREATE>);
static_assert(std::is_same_v<decltype(&ed_on_object_simulate),PFN_ED_ON_OBJECT_SIMULATE>);
static_assert(std::is_same_v<decltype(&ed_on_object_destroy),PFN_ED_ON_OBJECT_DESTROY>);
