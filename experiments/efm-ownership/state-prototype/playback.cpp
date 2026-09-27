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
#ifdef STATE_POSTSTEP
#include "../native_body.h"
#include "../native_step_hook.h"
#endif

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
#ifdef STATE_POSTSTEP
    bool hooked=false,pending=false;
    uint64_t repaired=0;
#endif
};
const ed_object_api_entry* api=nullptr;
std::mutex guard;
std::unordered_map<ED_OBJECT_HANDLE,Object> objects;
std::vector<Sample> tape;
std::ofstream trace,events;
#ifdef STATE_POSTSTEP
std::ofstream post_trace;
#endif
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
#ifdef STATE_POSTSTEP
    post_trace.open(folder/"state-logs"/("post-step-"+run+".csv"));
    if(!post_trace)return;
    post_trace << std::setprecision(10) << "id,call,arg,requested,before,after\n";
#endif
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
#ifdef STATE_POSTSTEP
void after_native_step(const void* pointer) {
    std::lock_guard<std::mutex> held(guard);
    auto handle=reinterpret_cast<ED_OBJECT_HANDLE>(const_cast<void*>(pointer));
    const auto found=objects.find(handle);if(found==objects.end())return;
    auto& object=found->second;
    if(!object.valid || !object.pending || !available(handle) || api->ed_get_object_id(handle)!=object.id)return;
    object.pending=false;
    // Only repair the two failing stabilators; preserve the baseline on all others.
    bool ok=true;
    for(size_t i: {size_t(9),size_t(10)}) {
        const int c=channels[i];
        const float before=api->ed_get_object_args(handle).data[c];
        api->ed_set_single_arg(handle,c,object.requested[i]);
        const float after=api->ed_get_object_args(handle).data[c];
        ok=ok && std::isfinite(after) && std::abs(after-object.requested[i])<0.00001f;
        post_trace << object.id << ',' << object.calls << ',' << c << ',' << object.requested[i] << ',' << before << ',' << after << '\n';
    }
    post_trace.flush();++object.repaired;
    if(!ok || !post_trace) {object.valid=false;api->ed_set_single_arg(handle,status_arg,0.75f);event("post_step_failed",object,object.last,"stopped");}
}
const char* install_after(ED_OBJECT_HANDLE handle) {
    native_body::Sample sample{};
    if(std::string(native_body::sample(handle,sample))!="object_position_candidate")return "post_step_identity_or_null_fm_rejected";
    const auto image=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    uintptr_t locator=0,next_locator=0;
    if(!native_identity::read(image+0x11461f8,locator) || locator!=image+0x133b650 ||
       !native_identity::read(image+0x1146ff0,next_locator) || next_locator!=image+0x133b770)return "step_table_boundary_mismatch";
    std::array<unsigned char,15> prologue{};
    if(!native_identity::read(image+0x70fef0,prologue) ||
       prologue!=std::array<unsigned char,15>{0x48,0x8b,0xc4,0x48,0x89,0x58,0x10,0x48,0x89,0x70,0x18,0x48,0x89,0x78,0x20})return "step_entry_mismatch";
    std::array<unsigned char,10> callsite{};
    if(!native_identity::read(image+0x675279,callsite) ||
       callsite!=std::array<unsigned char,10>{0xff,0x90,0x70,0x0c,0,0,0x48,0x8b,0x4b,0x58})return "step_callsite_mismatch";
    return native_step_hook::install(reinterpret_cast<uintptr_t>(handle)-8,image+0x1146200,
        reinterpret_cast<native_step_hook::Step>(image+0x70fef0),nullptr,&after_native_step);
}
void restore_after(ED_OBJECT_HANDLE handle,Object& object) {
    object.pending=false;
    if(object.hooked) {
        const auto result=native_step_hook::restore(reinterpret_cast<uintptr_t>(handle)-8);
        event(result,object,object.last,"post_step");
        object.hooked=false;
    }
}
#endif
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
#ifdef STATE_POSTSTEP
    if(!object.valid) {restore_after(handle,object);return;}
#endif
    if(!object.valid || object.cookie!=cookie || !available(handle) || api->ed_get_object_id(handle)!=object.id)return;
    if(!std::isfinite(time) || (object.last>=0 && time<object.last)) {
        object.valid=false;api->ed_set_single_arg(handle,status_arg,0.75f);event("clock_rejected",object,time,"stopped");return;
    }
    if(object.start<0) {object.start=time;event("start",object,time,"sdk_only");}
#ifdef STATE_POSTSTEP
    if(!object.hooked) {
        const auto status=install_after(handle);
        object.hooked=std::string(status)=="step_hook_installed";
        event(status,object,time,"post_step_stabilators");
        if(!object.hooked) {object.valid=false;api->ed_set_single_arg(handle,status_arg,0.75f);return;}
    }
    if(time-object.start>1 && object.repaired==0) {
        object.valid=false;event("post_step_not_called",object,time,"stopped");
        restore_after(handle,object);api->ed_set_single_arg(handle,status_arg,0.75f);return;
    }
#endif
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
#ifdef STATE_POSTSTEP
    object.pending=matches;
    if(!object.valid)restore_after(handle,object);
#endif
}
extern "C" __declspec(dllexport) void ed_on_object_destroy(ED_OBJECT_HANDLE handle,uint64_t& cookie) {
    std::lock_guard<std::mutex> held(guard);
    const auto found=objects.find(handle);
    if(found!=objects.end()) {
#ifdef STATE_POSTSTEP
        restore_after(handle,found->second);
#endif
        event("destroy",found->second,found->second.last,"finished");objects.erase(found);
    }
}
static_assert(std::is_same_v<decltype(&ed_setup_object_api),PFN_ED_SETUP_OBJECT_API>);
static_assert(std::is_same_v<decltype(&ed_on_object_create),PFN_ED_ON_OBJECT_CREATE>);
static_assert(std::is_same_v<decltype(&ed_on_object_simulate),PFN_ED_ON_OBJECT_SIMULATE>);
static_assert(std::is_same_v<decltype(&ed_on_object_destroy),PFN_ED_ON_OBJECT_DESTROY>);
