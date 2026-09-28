// THROWAWAY: appearance replay on a separately registered Hornet.
// Optional guarded native timing variants; no pose/velocity or control writes.
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
#ifdef ENGINE_SOUND_TRACE
#include "../engine-prototype/sound_probe.h"
#endif
#ifdef ENGINE_SOUND_BOUNDARY
#include "../engine-prototype/sound_boundary.h"
#endif
#if defined(STATE_POSTSTEP) || defined(STATE_POSTANIMATION)
#include "../native_body.h"
#include "../native_step_hook.h"
#ifdef STATE_POSTANIMATION
#include "../native_animation_hook.h"
#endif
#endif

namespace {
#ifdef CANOPY_APPEARANCE_PROTOTYPE
constexpr std::array<int,1> channels{38};
constexpr const char* tape_header="DCS_CANOPY_PROTOTYPE_V1";
#elif defined(LIGHT_APPEARANCE_PROTOTYPE)
constexpr std::array<int,10> channels{0,3,5,88,190,191,192,193,210,212};
constexpr const char* tape_header="DCS_LIGHT_PROTOTYPE_V1";
#elif defined(ENGINE_APPEARANCE_PROTOTYPE)
constexpr std::array<int,4> channels{28,29,89,90};
constexpr const char* tape_header="DCS_ENGINE_PROTOTYPE_V1";
#else
constexpr std::array<int,14> channels{0,3,5,9,10,11,12,13,14,15,16,17,18,21};
constexpr const char* tape_header="DCS_EXTERIOR_PROTOTYPE_V1";
#endif
constexpr int elapsed_arg=998,status_arg=999;
using Values=std::array<float,channels.size()>;
struct Sample { double t; Values values; };
struct Object {
    uint64_t id=0,cookie=0,calls=0;
    double start=-1,last=-1;
    bool valid=false,previous=false;
#ifdef ENGINE_SOUND_BOUNDARY
    double next_sound_trace=-1;
#endif
    Values requested{};
#if defined(STATE_POSTSTEP) || defined(STATE_POSTANIMATION)
    bool hooked=false,pending=false;
    uint64_t repaired=0;
#endif
};
const ed_object_api_entry* api=nullptr;
std::mutex guard;
std::unordered_map<ED_OBJECT_HANDLE,Object> objects;
std::vector<Sample> tape;
std::ofstream trace,events;
#ifdef ENGINE_SOUND_BOUNDARY
std::ofstream sound_trace;
#endif
#if defined(STATE_POSTSTEP) || defined(STATE_POSTANIMATION)
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
#ifdef ENGINE_SOUND_BOUNDARY
    sound_trace.open(folder/"state-logs"/("sound-boundary-"+run+".jsonl"));
    sound_trace << std::setprecision(10);
#endif
    trace.open(folder/"state-logs"/("state-"+run+".csv"));
    events.open(folder/"state-logs"/("events-"+run+".csv"));
    if(!trace || !events)return;
#if defined(STATE_POSTSTEP) || defined(STATE_POSTANIMATION)
    post_trace.open(folder/"state-logs"/(
#ifdef STATE_POSTANIMATION
        "post-animation-"+run
#else
        "post-step-"+run
#endif
        +".csv"));
    if(!post_trace)return;
    post_trace << std::setprecision(10) << "id,call,arg,requested,before,after\n";
#endif
    trace << std::setprecision(10);
    events << std::setprecision(10) << "event,id,time,detail\n";
    trace << "id,call,time,elapsed,previous_dt,arg,previous_requested,before,requested,after\n";
    std::ifstream file(folder/"exterior-state.txt");
    std::string header;size_t count=0;
    if(!(file>>header>>count) || header!=tape_header || count<2 || count>10000) {
        events << "tape_rejected,0,0,header\n";events.flush();return;
    }
    for(int expected:channels) {int actual=-1;if(!(file>>actual) || actual!=expected)return;}
    for(size_t i=0;i<count;++i) {
        Sample row{};
        if(!(file>>row.t) || !std::isfinite(row.t) || (i==0 && row.t!=0))return;
        if(i && (!(row.t>tape.back().t) || row.t-tape.back().t>0.15))return;
        for(size_t c=0;c<channels.size();++c) {
            if(!(file>>row.values[c]) || !std::isfinite(row.values[c]) ||
               row.values[c] <
#if defined(ENGINE_APPEARANCE_PROTOTYPE) || defined(LIGHT_APPEARANCE_PROTOTYPE) || defined(CANOPY_APPEARANCE_PROTOTYPE)
               0.0f
#else
               ((c<3 || c==13)?0.0f:-1.0f)
#endif
               || row.values[c]>1.0f)return;
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
#ifdef LIGHT_APPEARANCE_PROTOTYPE
    // Preserve sampled strobe edges instead of inventing intermediate pulses.
    values[7]=(t>=b.t?b:a).values[7];
#endif
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
#if defined(STATE_POSTSTEP) || defined(STATE_POSTANIMATION)
void after_native_step(const void* pointer) {
    std::lock_guard<std::mutex> held(guard);
    auto handle=reinterpret_cast<ED_OBJECT_HANDLE>(const_cast<void*>(pointer));
    const auto found=objects.find(handle);if(found==objects.end())return;
    auto& object=found->second;
    if(!object.valid || !object.pending || !available(handle) || api->ed_get_object_id(handle)!=object.id)return;
    // The animation update may run more than once per SDK sample. Repair each
    // invocation until the next sample or lifecycle invalidation.
#ifndef STATE_POSTANIMATION
    object.pending=false;
#endif
    // Engine experiment repairs its four observed channels; exterior variant
    // retains the original two-stabilator comparison.
    bool ok=true;
#ifdef ENGINE_APPEARANCE_PROTOTYPE
    for(size_t i=0;i<channels.size();++i) {
#else
    for(size_t i: {size_t(9),size_t(10)}) {
#endif
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
#ifdef STATE_POSTANIMATION
    std::array<unsigned char,18> prologue{};
    if(!native_identity::read(image+0x6b6070,prologue) ||
       prologue!=std::array<unsigned char,18>{0x48,0x8b,0xc4,0x48,0x89,0x58,0x10,0x55,0x56,0x57,0x41,0x54,0x41,0x55,0x41,0x56,0x41,0x57})return "animation_entry_mismatch";
    std::array<unsigned char,15> callsite{};
    if(!native_identity::read(image+0x67529c,callsite) ||
       callsite!=std::array<unsigned char,15>{0x41,0xb0,1,0x0f,0x28,0xce,0x48,0x8b,1,0xff,0x90,0x10,0x0c,0,0})return "animation_callsite_mismatch";
    // This update calls the routine that writes draw arguments 15/16.
    std::array<unsigned char,5> writer_call{};
    if(!native_identity::read(image+0x6b73a7,writer_call) ||
       writer_call!=std::array<unsigned char,5>{0xe8,0x44,0x1f,0xfb,0xff})return "animation_writer_mismatch";
    return native_animation_hook::install(reinterpret_cast<uintptr_t>(handle)-8,image+0x1146200,
        reinterpret_cast<native_animation_hook::Step>(image+0x6b6070),nullptr,&after_native_step);
#else
    std::array<unsigned char,15> prologue{};
    if(!native_identity::read(image+0x70fef0,prologue) ||
       prologue!=std::array<unsigned char,15>{0x48,0x8b,0xc4,0x48,0x89,0x58,0x10,0x48,0x89,0x70,0x18,0x48,0x89,0x78,0x20})return "step_entry_mismatch";
    std::array<unsigned char,10> callsite{};
    if(!native_identity::read(image+0x675279,callsite) ||
       callsite!=std::array<unsigned char,10>{0xff,0x90,0x70,0x0c,0,0,0x48,0x8b,0x4b,0x58})return "step_callsite_mismatch";
    return native_step_hook::install(reinterpret_cast<uintptr_t>(handle)-8,image+0x1146200,
        reinterpret_cast<native_step_hook::Step>(image+0x70fef0),nullptr,&after_native_step);
#endif
}
void restore_after(ED_OBJECT_HANDLE handle,Object& object) {
    object.pending=false;
    if(object.hooked) {
#ifdef STATE_POSTANIMATION
        const auto result=native_animation_hook::restore(reinterpret_cast<uintptr_t>(handle)-8);
        event(result,object,object.last,"post_animation");
#else
        const auto result=native_step_hook::restore(reinterpret_cast<uintptr_t>(handle)-8);
        event(result,object,object.last,"post_step");
#endif
        object.hooked=false;
    }
}
#endif
}
extern "C" __declspec(dllexport) void ed_setup_object_api(const ed_object_api_entry* entry) {
    std::lock_guard<std::mutex> held(guard);api=entry;initialize();
#ifdef ENGINE_SOUND_TRACE
    engine_sound_probe::lifecycle("sdk_setup",0);
#endif
}
extern "C" __declspec(dllexport) void ed_on_object_create(ED_OBJECT_HANDLE handle,uint64_t& cookie) {
    std::lock_guard<std::mutex> held(guard);initialize();
    cookie=++serial;
    Object object;object.cookie=cookie;
    object.valid=handle && loaded && available(handle);
    if(object.valid) {object.id=api->ed_get_object_id(handle);object.valid=object.id!=0;}
    objects[handle]=object;event(object.valid?"create":"create_rejected",object,0,loaded?"sdk":"tape");
#ifdef ENGINE_SOUND_TRACE
    engine_sound_probe::lifecycle(object.valid?"object_create":"object_rejected",object.id);
#endif
}
extern "C" __declspec(dllexport) void ed_on_object_simulate(ED_OBJECT_HANDLE handle,uint64_t& cookie,double time) {
    std::lock_guard<std::mutex> held(guard);
    const auto found=objects.find(handle);if(found==objects.end())return;
    auto& object=found->second;
#if defined(STATE_POSTSTEP) || defined(STATE_POSTANIMATION)
    if(!object.valid) {restore_after(handle,object);return;}
#endif
    if(!object.valid || object.cookie!=cookie || !available(handle) || api->ed_get_object_id(handle)!=object.id)return;
    if(!std::isfinite(time) || (object.last>=0 && time<object.last)) {
        object.valid=false;api->ed_set_single_arg(handle,status_arg,0.75f);event("clock_rejected",object,time,"stopped");return;
    }
    if(object.start<0) {object.start=time;event("start",object,time,"sdk_only");}
#ifdef ENGINE_SOUND_BOUNDARY
    if(sound_trace && time>=object.next_sound_trace) {
        sound_boundary::sample(sound_trace,handle,object.id,time);
        object.next_sound_trace=time+1;
    }
#endif
#if defined(STATE_POSTSTEP) || defined(STATE_POSTANIMATION)
    if(!object.hooked) {
        const auto status=install_after(handle);
#ifdef STATE_POSTANIMATION
        object.hooked=std::string(status)=="animation_hook_installed";
#else
        object.hooked=std::string(status)=="step_hook_installed";
#endif
        event(status,object,time,"stabilator_timing");
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
#if defined(STATE_POSTSTEP) || defined(STATE_POSTANIMATION)
    object.pending=matches;
    if(!object.valid)restore_after(handle,object);
#endif
}
extern "C" __declspec(dllexport) void ed_on_object_destroy(ED_OBJECT_HANDLE handle,uint64_t& cookie) {
    std::lock_guard<std::mutex> held(guard);
    const auto found=objects.find(handle);
    if(found!=objects.end()) {
#if defined(STATE_POSTSTEP) || defined(STATE_POSTANIMATION)
        restore_after(handle,found->second);
#endif
        event("destroy",found->second,found->second.last,"finished");
#ifdef ENGINE_SOUND_TRACE
        engine_sound_probe::lifecycle("object_destroy",found->second.id);
#endif
        objects.erase(found);
    }
}
static_assert(std::is_same_v<decltype(&ed_setup_object_api),PFN_ED_SETUP_OBJECT_API>);
static_assert(std::is_same_v<decltype(&ed_on_object_create),PFN_ED_ON_OBJECT_CREATE>);
static_assert(std::is_same_v<decltype(&ed_on_object_simulate),PFN_ED_ON_OBJECT_SIMULATE>);
static_assert(std::is_same_v<decltype(&ed_on_object_destroy),PFN_ED_ON_OBJECT_DESTROY>);
