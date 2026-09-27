// THROWAWAY: baseline -> recorded core/fan RPM and power -> original getter, stock DCS audio.
#include <windows.h>
#include <cstdint>
#include <cstddef>
#include "ed_object_access.h"
#include "parameter_hook.h"
#include "sound_boundary.h"
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <algorithm>
#include <type_traits>
#ifdef ENGINE_COMBINED
#include "../native_body.h"
#endif

namespace {
struct Row {double t;parameter_hook::Values values;
#ifdef ENGINE_COMBINED
    std::array<float,4> appearance{};
#endif
};
std::vector<Row> tape;
std::ofstream events,trace;
const ed_object_api_entry* api=nullptr;
ED_OBJECT_HANDLE owned=nullptr;
uint64_t id=0,cookie_value=0,serial=0;
double start=-1,last=-1;
bool initialized=false,loaded=false,hooked=false,failed=false;
std::mutex guard;
#ifdef ENGINE_COMBINED
constexpr std::array<int,4> appearance_channels{28,29,89,90};
std::ofstream appearance_trace;
std::array<float,4> appearance_values{};
double appearance_time=-1;
uint64_t animation_calls=0;
#endif
void event(const char* value,double t) {events << std::setprecision(12) << value << ',' << id << ',' << t << '\n';events.flush();}
void initialize() {
    if(initialized)return;initialized=true;
    HMODULE module=nullptr;wchar_t path[32768]{};
    if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
        reinterpret_cast<LPCWSTR>(&initialize),&module) || !GetModuleFileNameW(module,path,32768))return;
    const auto folder=std::filesystem::path(path).parent_path();
    std::error_code error;std::filesystem::create_directories(folder/"parameter-logs",error);if(error)return;
    const auto run=std::to_string(GetCurrentProcessId())+"-"+std::to_string(GetTickCount64());
    events.open(folder/"parameter-logs"/("events-"+run+".csv"));
    trace.open(folder/"parameter-logs"/("calls-"+run+".csv"));
#ifdef ENGINE_COMBINED
    appearance_trace.open(folder/"parameter-logs"/("appearance-"+run+".csv"));
    appearance_trace << std::setprecision(12) << "id,time,recorded_time,stage,arg,requested,before,after\n";
    if(!appearance_trace)return;
#endif
    events << "event,id,time\n";
    trace << std::setprecision(12) << "id,drain_time,caller_module,caller_rva,engine,channel,overridden,original,returned\n";
    std::ifstream file(folder/"recorded-engine.txt");std::string header;size_t count=0;
    if(!(file>>header>>count) || header!=
#ifdef ENGINE_COMBINED
       "DCS_ENGINE_COMBINED_V1"
#else
       "DCS_NATIVE_ENGINE_PROBE_V1"
#endif
       || count<2 || count>10000)return;
    for(size_t i=0;i<count;++i) {
        Row row{};
        if(!(file>>row.t))return;
        for(auto& value:row.values)if(!(file>>value))return;
#ifdef ENGINE_COMBINED
        for(auto& value:row.appearance)
            if(!(file>>value) || !std::isfinite(value) || value<0 || value>1)return;
#endif
        if(!std::isfinite(row.t) || !parameter_hook::valid(row.values) ||
           (i==0 && row.t!=0) || (i && (row.t<=tape.back().t || row.t-tape.back().t>0.15)))return;
        tape.push_back(row);
    }
    std::string extra;if(file>>extra || tape.back().t>240 || !events || !trace)return;
    loaded=true;event("tape_loaded",tape.back().t);
}
Row at(double t) {
    t=std::clamp(t,0.0,tape.back().t);
    auto it=std::upper_bound(tape.begin(),tape.end(),t,[](double a,const Row& b){return a<b.t;});
    size_t i=std::clamp<size_t>(it-tape.begin(),1,tape.size()-1)-1;
    const auto&a=tape[i];const auto&b=tape[i+1];const double u=(t-a.t)/(b.t-a.t);
    Row result{t,{}};
    for(size_t c=0;c<6;++c)result.values[c]=float(a.values[c]+u*(b.values[c]-a.values[c]));
#ifdef ENGINE_COMBINED
    for(size_t c=0;c<4;++c)result.appearance[c]=float(a.appearance[c]+u*(b.appearance[c]-a.appearance[c]));
#endif
    return result;
}
void drain(double t) {
    uint64_t lost=0;
    for(const auto&call:parameter_hook::drain(lost)) {
        MEMORY_BASIC_INFORMATION region{};std::string name="unknown";uintptr_t rva=0;
        if(VirtualQuery(reinterpret_cast<void*>(call.caller),&region,sizeof(region)) && region.Type==MEM_IMAGE) {
            char path[32768]{};
            GetModuleFileNameA(static_cast<HMODULE>(region.AllocationBase),path,sizeof(path));
            name=std::filesystem::path(path).filename().string();rva=call.caller-reinterpret_cast<uintptr_t>(region.AllocationBase);
        }
        trace << id << ',' << t << ',' << name << ',' << rva << ',' << call.engine << ',' << call.channel << ','
            << call.overridden << ',' << call.original << ',' << call.returned << '\n';
    }
    trace.flush();if(lost)event("trace_overflow",t);
}
bool available(ED_OBJECT_HANDLE h) {
    if(!api || !api->ed_get_object_id || !api->ed_get_object_args || !api->ed_set_single_arg)return false;
    auto view=api->ed_get_object_args(h);return view.data && view.size>999;
}
#ifdef ENGINE_COMBINED
bool restore(double t);
bool write_appearance(const char* stage) {
    bool ok=true;
    for(size_t c=0;c<appearance_channels.size();++c) {
        const int arg=appearance_channels[c];
        const float before=api->ed_get_object_args(owned).data[arg];
        api->ed_set_single_arg(owned,arg,appearance_values[c]);
        const auto view=api->ed_get_object_args(owned);
        if(!view.data || view.size<=999)return false;
        const float after=view.data[arg];
        ok=ok && std::isfinite(after) && std::abs(after-appearance_values[c])<.00001f;
        appearance_trace << id << ',' << appearance_time << ',' << appearance_time-start-3 << ','
            << stage << ',' << arg << ',' << appearance_values[c] << ',' << before << ',' << after << '\n';
    }
    appearance_trace.flush();return ok && bool(appearance_trace);
}
void after_animation(const void* pointer) {
    std::lock_guard<std::mutex> held(guard);
    if(pointer!=owned || failed || !hooked || !available(owned) || api->ed_get_object_id(owned)!=id)return;
    ++animation_calls;
    if(!write_appearance("post_animation")) {
        failed=true;event("appearance_write_failed",appearance_time);restore(appearance_time);
        if(available(owned))api->ed_set_single_arg(owned,999,.75f);
    }
}
#endif
const char* install(ED_OBJECT_HANDLE h) {
    const auto identity=native_identity::inspect(h);
    if(identity.status!="ok" || identity.module!="DCS.exe" || identity.name!=".?AVwoAIPlane@@" || identity.subobject_offset!=8)return "identity_rejected";
    const auto image=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    const auto world=reinterpret_cast<uintptr_t>(GetModuleHandleW(L"WorldGeneral.dll"));
    const auto sound=reinterpret_cast<uintptr_t>(GetModuleHandleW(L"Sound.dll"));
    if(!sound_boundary::layout_matches(image,world) || !sound ||
       !sound_boundary::matches(sound+0x13d430,std::array<unsigned char,18>{0x48,0x8b,0x4b,0x40,0x41,0xb0,1,0x8b,0xd7,0x48,0x8b,1,0xff,0x90,0xd8,0,0,0}))return "build_guard_rejected";
    uintptr_t locator=0,next=0;unsigned char count=0;
    const auto object=reinterpret_cast<uintptr_t>(h)-8;
    if(!native_identity::read(image+0x11461f8,locator) || locator!=image+0x133b650 ||
       !native_identity::read(image+0x1146ff0,next) || next!=image+0x133b770 ||
       !native_identity::read(object+0x811,count) || count!=2)return "table_or_engine_count_rejected";
    if(!sound_boundary::matches(image+0x60f110,std::array<unsigned char,10>{0x48,0x8b,1,0x48,0xff,0xa0,0xe0,0,0,0}) ||
       !sound_boundary::matches(image+0x66d1c0,std::array<unsigned char,14>{0x85,0xd2,0x7e,0x21,0x0f,0xb6,0x81,0x11,8,0,0,0x3b,0xd0,0x7f}) ||
       !sound_boundary::matches(sound+0x134cbb,std::array<unsigned char,6>{0xff,0x90,0xe0,0,0,0}) ||
       !sound_boundary::matches(sound+0x134ca5,std::array<unsigned char,6>{0xff,0x90,0xf0,0,0,0}))return "power_guard_rejected";
#ifdef ENGINE_COMBINED
    native_body::Sample body{};
    if(std::string(native_body::sample(h,body))!="object_position_candidate")return "animation_identity_or_null_fm_rejected";
    if(!sound_boundary::matches(image+0x6b6070,std::array<unsigned char,18>{0x48,0x8b,0xc4,0x48,0x89,0x58,0x10,0x55,0x56,0x57,0x41,0x54,0x41,0x55,0x41,0x56,0x41,0x57}) ||
       !sound_boundary::matches(image+0x67529c,std::array<unsigned char,15>{0x41,0xb0,1,0x0f,0x28,0xce,0x48,0x8b,1,0xff,0x90,0x10,0x0c,0,0}) ||
       !sound_boundary::matches(image+0x6b73a7,std::array<unsigned char,5>{0xe8,0x44,0x1f,0xfb,0xff}))return "animation_guard_rejected";
#endif
    return parameter_hook::install(object,image+0x1146200,reinterpret_cast<parameter_hook::Getter>(image+0x66d160),
        reinterpret_cast<parameter_hook::Thrust>(image+0x66d1c0),reinterpret_cast<parameter_hook::Thrust>(image+0x60f110)
#ifdef ENGINE_COMBINED
        ,reinterpret_cast<parameter_hook::Animation>(image+0x6b6070),&after_animation
#endif
        );
}
bool restore(double t) {
    if(hooked){
        const std::string result=parameter_hook::restore(reinterpret_cast<uintptr_t>(owned)-8);
        event(result.c_str(),t);
        hooked=result!="parameter_hook_restored" && result!="parameter_hook_already_replaced" && result!="parameter_hook_inactive";
    }
    drain(t);
    return !hooked;
}
}
extern "C" __declspec(dllexport) void ed_setup_object_api(const ed_object_api_entry* entry) {
    std::lock_guard<std::mutex> held(guard);api=entry;initialize();
}
extern "C" __declspec(dllexport) void ed_on_object_create(ED_OBJECT_HANDLE h,uint64_t& cookie) {
    std::lock_guard<std::mutex> held(guard);initialize();cookie=++serial;
    if(owned || !h || !loaded || !available(h) || !api->ed_get_object_id(h)){event("create_rejected",0);return;}
    owned=h;id=api->ed_get_object_id(h);cookie_value=cookie;start=last=-1;failed=false;event("create",0);
#ifdef ENGINE_COMBINED
    animation_calls=0;appearance_time=-1;
#endif
}
extern "C" __declspec(dllexport) void ed_on_object_simulate(ED_OBJECT_HANDLE h,uint64_t& cookie,double time) {
    std::lock_guard<std::mutex> held(guard);
    if(h!=owned || cookie!=cookie_value || !h)return;
    if(failed)return;
    if(!available(h) || api->ed_get_object_id(h)!=id || !std::isfinite(time) || (last>=0 && time<last)) {
        failed=true;restore(last);event("lifecycle_or_clock_rejected",last);
        if(available(h) && api->ed_get_object_id(h)==id)api->ed_set_single_arg(h,999,0.75f);
        return;
    }
    if(start<0) {
        start=time;const char* result=install(h);event(result,time);
        hooked=std::string(result)=="parameter_hook_installed";
        if(!hooked){failed=true;api->ed_set_single_arg(h,999,0.75f);return;}
        event("baseline_begin",time);
    }
    const double elapsed=time-start;const bool replay=elapsed>=3 && elapsed<3+tape.back().t;
    if(hooked) {
        const auto row=at(elapsed-3);
#ifdef ENGINE_COMBINED
        appearance_values=row.appearance;appearance_time=time;
        if(replay && ((!animation_calls && elapsed>4) || !write_appearance("sdk"))) {
            failed=true;event("appearance_or_animation_failed",time);restore(time);
            api->ed_set_single_arg(h,999,.75f);return;
        }
#endif
        if(!parameter_hook::publish(reinterpret_cast<uintptr_t>(h)-8,replay,row.values)) {
            failed=true;restore(time);api->ed_set_single_arg(h,999,0.75f);return;
        }
        if(elapsed>=3 && last-start<3)event("recorded_parameters_begin",time);
        if(elapsed>=3+tape.back().t){
            if(!restore(time)){failed=true;api->ed_set_single_arg(h,999,0.75f);return;}
            event("original_getter_restored",time);
        }
    }
    drain(time);
    if(!trace || !events){failed=true;restore(time);api->ed_set_single_arg(h,999,0.75f);return;}
    api->ed_set_single_arg(h,998,static_cast<float>(elapsed/1000));
    api->ed_set_single_arg(h,999,hooked?0.25f:0.5f);last=time;
}
extern "C" __declspec(dllexport) void ed_on_object_destroy(ED_OBJECT_HANDLE h,uint64_t& cookie) {
    std::lock_guard<std::mutex> held(guard);
    if(h==owned && cookie==cookie_value){restore(last);event("destroy",last);owned=nullptr;id=0;}
}
static_assert(std::is_same_v<decltype(&ed_setup_object_api),PFN_ED_SETUP_OBJECT_API>);
static_assert(std::is_same_v<decltype(&ed_on_object_create),PFN_ED_ON_OBJECT_CREATE>);
static_assert(std::is_same_v<decltype(&ed_on_object_simulate),PFN_ED_ON_OBJECT_SIMULATE>);
static_assert(std::is_same_v<decltype(&ed_on_object_destroy),PFN_ED_ON_OBJECT_DESTROY>);
