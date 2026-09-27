// Lifecycle and guarded native-motion experiment using the ED object callbacks.
#include <windows.h>
#include <cstdint>
#include <cstddef>
#include "ed_object_access.h"
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <mutex>
#include <string>
#include <type_traits>
#include <unordered_map>
#include "native_identity.h"
#include "static_image_snapshot.h"
#include "native_body.h"
#include "native_motion.h"
#ifdef HORNET_STAGED_PROTOTYPE
#include "native_presentation_pitch.h"
#endif
#include "turn_path.h"
#ifdef HORNET_RECORDED_PROTOTYPE
#include "recorded_path.h"
#ifdef HORNET_STAGED_PROTOTYPE
#include "staged_playback.h"
#endif
namespace playback_path=recorded_path;
#elif defined(HORNET_ROLL_PROTOTYPE)
#include "hornet_roll_path.h"
namespace playback_path=hornet_roll_path;
#else
namespace playback_path=turn_path;
#endif
#ifdef HORNET_PROTOTYPE
#include "hornet_appearance.h"
#endif

namespace {
const ed_object_api_entry* api = nullptr;
std::mutex lock;
std::ofstream log_file;
std::ofstream identity_file;
std::ofstream body_file;
std::ofstream motion_file;
#ifdef HORNET_STAGED_PROTOTYPE
std::ofstream exterior_file;
#endif
struct Observation {
    uint64_t calls = 0; double next_log = 0; bool motion_attempted=false, motion_active=false;
    double start_time=0, last_time=0, last_x=0, last_z=0, measured_speed=145; playback_path::Path path;
#ifdef HORNET_RECORDED_PROTOTYPE
    bool step_hook=false, step_pending=false;
#ifdef HORNET_STAGED_PROTOTYPE
    uint64_t runtime_id=0,token=0;
    bool terminal=false;
    bool exterior_pending=false,exterior_finished=false;
    double exterior_elapsed=0;
    uint64_t exterior_applied=0;
    hornet_exterior::Values exterior{};
#endif
    uint64_t step_calls=0,step_applied=0;
    const char* step_status="step_hook_inactive";
    turn_path::Motion step_motion{};
#ifdef HORNET_STAGED_PROTOTYPE
    native_presentation_pitch::State presentation;
#endif
#endif
};
std::unordered_map<ED_OBJECT_HANDLE, Observation> observed;

#ifdef HORNET_RECORDED_PROTOTYPE
#ifdef HORNET_STAGED_PROTOTYPE
void after_native_animation(const void* handle) {
    std::lock_guard<std::mutex> guard(lock);
    const auto sdk_handle=reinterpret_cast<ED_OBJECT_HANDLE>(const_cast<void*>(handle));
    const auto found=observed.find(sdk_handle);if(found==observed.end())return;
    auto& state=found->second;
    if(!state.motion_active || !state.exterior_pending || !state.path.has_exterior ||
       !api || !api->ed_get_object_id || api->ed_get_object_id(sdk_handle)!=state.runtime_id)return;
    const auto view=api->ed_get_object_args(sdk_handle);
    if(!view.data || view.size<=18) {state.motion_active=false;return;}
    std::array<float,13> before{};
    for(size_t i=0;i<before.size();++i)before[i]=view.data[hornet_exterior::channels[i]];
    const bool applied=hornet_appearance::apply_exterior(api,sdk_handle,state.runtime_id,state.exterior);
    const auto after=api->ed_get_object_args(sdk_handle);
    if(applied) {
        ++state.exterior_applied;
        for(size_t i=0;i<before.size();++i)exterior_file << state.runtime_id << ',' << state.calls << ','
            << state.exterior_elapsed << ',' << hornet_exterior::channels[i] << ',' << state.exterior[i]
            << ',' << before[i] << ',' << after.data[hornet_exterior::channels[i]] << '\n';
        exterior_file.flush();
    }
    if(!applied || !exterior_file) {
        state.motion_active=false;state.exterior_pending=false;
        staged_playback::publish(api,sdk_handle,state.token,staged_playback::failed);
    } else if(state.exterior_finished) {
        // Completion is visible to Lua only after the final surface sample too.
        if(staged_playback::publish(api,sdk_handle,state.token,staged_playback::complete)) {
            state.terminal=true;
            log_file << "staged_exterior_complete," << state.runtime_id << ",0," << state.start_time+state.exterior_elapsed << ',' << state.calls << ",1\n";
            log_file.flush();
        }
        else state.motion_active=false;
    }
}
#endif
void before_native_step(const void* handle) {
    std::lock_guard<std::mutex> guard(lock);
    const auto sdk_handle=reinterpret_cast<ED_OBJECT_HANDLE>(const_cast<void*>(handle));
    const auto it=observed.find(sdk_handle);
    if(it==observed.end()) return;
    auto& state=it->second;
    ++state.step_calls;
    if(!state.motion_active || !state.step_pending) return;
    state.step_pending=false; // A missing SDK callback cannot leave a stale override running.
    native_body::Sample sample{};
    const auto id=api && api->ed_get_object_id ? api->ed_get_object_id(sdk_handle) : 0;
#ifdef HORNET_STAGED_PROTOTYPE
    const uint64_t expected_id=state.runtime_id;
#else
    const uint64_t expected_id=16777472;
#endif
    if(!expected_id || id!=expected_id || std::strcmp(native_body::sample(handle,sample),"object_position_candidate")
#ifndef HORNET_STAGED_PROTOTYPE
       || sample.position[1]<1000 || sample.position[1]>5000
#endif
       ) state.step_status="step_state_rejected";
    else {
        state.step_status=native_velocity::validate(handle,state.step_motion);
        if(std::strcmp(state.step_status,"valid")==0)
            state.step_status=native_velocity::write_validated(handle,state.step_motion);
    }
#ifdef HORNET_STAGED_PROTOTYPE
    if(std::strcmp(state.step_status,"called")==0) {
        state.step_status=native_presentation_pitch::layout_valid() ?
            native_presentation_pitch::clear_validated(handle,state.presentation) : "presentation_layout_mismatch";
    }
#endif
    if(std::strcmp(state.step_status,"called")==0) ++state.step_applied;
    else state.motion_active=false;
}
const char* install_native_step(const void* handle,bool exterior=false) {
    const auto image=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    uintptr_t locator=0,next_locator=0;
    // RTTI boundaries establish the complete primary table's exact length.
    if(!native_identity::read(image+0x11461f8,locator) || locator!=image+0x133b650 ||
       !native_identity::read(image+0x1146ff0,next_locator) || next_locator!=image+0x133b770)
        return "step_table_boundary_mismatch";
    std::array<unsigned char,15> prologue{};
    if(!native_identity::read(image+0x70fef0,prologue) ||
       prologue!=std::array<unsigned char,15>{0x48,0x8b,0xc4,0x48,0x89,0x58,0x10,0x48,0x89,0x70,0x18,0x48,0x89,0x78,0x20})
        return "step_entry_mismatch";
    std::array<unsigned char,10> callsite{};
    if(!native_identity::read(image+0x675279,callsite) ||
       callsite!=std::array<unsigned char,10>{0xff,0x90,0x70,0x0c,0,0,0x48,0x8b,0x4b,0x58})
        return "step_callsite_mismatch";
#ifdef HORNET_STAGED_PROTOTYPE
    if(exterior) {
        std::array<unsigned char,18> entry{};
        std::array<unsigned char,15> dispatch{};
        std::array<unsigned char,5> writer{};
        if(!native_identity::read(image+0x6b6070,entry) || entry!=std::array<unsigned char,18>{0x48,0x8b,0xc4,0x48,0x89,0x58,0x10,0x55,0x56,0x57,0x41,0x54,0x41,0x55,0x41,0x56,0x41,0x57} ||
           !native_identity::read(image+0x67529c,dispatch) || dispatch!=std::array<unsigned char,15>{0x41,0xb0,1,0x0f,0x28,0xce,0x48,0x8b,1,0xff,0x90,0x10,0x0c,0,0} ||
           !native_identity::read(image+0x6b73a7,writer) || writer!=std::array<unsigned char,5>{0xe8,0x44,0x1f,0xfb,0xff})return "animation_layout_mismatch";
        return native_step_hook::install(reinterpret_cast<uintptr_t>(handle)-8,image+0x1146200,
            reinterpret_cast<native_step_hook::Step>(image+0x70fef0),&before_native_step,nullptr,
            reinterpret_cast<native_step_hook::Animation>(image+0x6b6070),&after_native_animation);
    }
#endif
    return native_step_hook::install(reinterpret_cast<uintptr_t>(handle)-8,image+0x1146200,
        reinterpret_cast<native_step_hook::Step>(image+0x70fef0),&before_native_step);
}
void stop_native_step(const void* handle,Observation& state) {
    state.step_pending=false;
#ifdef HORNET_STAGED_PROTOTYPE
    state.exterior_pending=false;
    const auto presentation_status=native_presentation_pitch::restore(handle,state.presentation);
    if(state.presentation.active) {
        state.step_status=presentation_status;state.motion_active=false;
        if(log_file.is_open())log_file << "presentation_restore_error," << presentation_status << '\n';
    }
#endif
    if(!state.step_hook) return;
    state.step_status=native_step_hook::restore(reinterpret_cast<uintptr_t>(handle)-8);
    state.step_hook=native_step_hook::recognizes(reinterpret_cast<uintptr_t>(handle)-8,
        native_step_hook::table(),reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))+0x1146200);
}
#endif

void open_log() {
    if (log_file.is_open()) return;
    HMODULE module = nullptr;
    if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS |
        GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
        reinterpret_cast<LPCWSTR>(&open_log), &module)) return;
    wchar_t path[32768]{};
    if (!GetModuleFileNameW(module, path, 32768)) return;
    auto folder = std::filesystem::path(path).parent_path() / "probe-logs";
    std::error_code error;
    std::filesystem::create_directories(folder, error);
    if (error) return;
    log_file.open(folder / ("objects-" + std::to_string(GetCurrentProcessId()) +
        "-" + std::to_string(GetTickCount64()) + ".csv"));
    log_file << "event,object_id,cookie,object_time,simulate_calls,api_available\n";
    log_file << std::setprecision(12);
    body_file.open(folder / ("native-body-" + std::to_string(GetCurrentProcessId()) + ".csv"));
    body_file << "object_id,object_time,status,x,y,z,vx,vy,vz\n" << std::setprecision(12);
    motion_file.open(folder / ("native-motion-" + std::to_string(GetCurrentProcessId()) + ".csv"));
    motion_file << "object_id,object_time,status";
    for(const char* prefix:{"command","actual","before"}) for(int i=0;i<16;++i) motion_file << ',' << prefix << i;
    motion_file << ",wall_seconds,apply_ms,roll_neutralized";
    for(const char* prefix:{"rates_before","rates_after"}) for(int i=0;i<3;++i) motion_file << ',' << prefix << i;
    motion_file << ",updates_suppressed,gate_status,motion_matched";
    for(const char* prefix:{"velocity_before","velocity_after","velocity_command","angular_command"})
        for(int i=0;i<3;++i) motion_file << ',' << prefix << i;
    motion_file << ",step_hook_calls,step_hook_applied,step_hook_status\n" << std::setprecision(12);
#ifdef HORNET_STAGED_PROTOTYPE
    exterior_file.open(folder/("exterior-"+std::to_string(GetCurrentProcessId())+".csv"));
    exterior_file << "id,call,elapsed,arg,requested,before,after\n" << std::setprecision(12);
#endif
}
void record(const char* event, ED_OBJECT_HANDLE handle, uint64_t cookie,
            double time, uint64_t calls) {
    open_log();
    if (!log_file) return;
    const auto id = handle && api && api->ed_get_object_id ? api->ed_get_object_id(handle) : 0;
    log_file << event << ',' << id << ',' << cookie << ',' << time << ',' << calls << ','
             << (api != nullptr) << '\n';
    log_file.flush();
}
void record_identity(ED_OBJECT_HANDLE handle) {
    if (!identity_file.is_open()) {
        HMODULE module=nullptr;
        if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS |
            GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
            reinterpret_cast<LPCWSTR>(&record_identity), &module)) return;
        wchar_t path[32768]{};
        if (!GetModuleFileNameW(module,path,32768)) return;
        auto folder=std::filesystem::path(path).parent_path()/"probe-logs";
        // open_log has already created this directory.
        identity_file.open(folder/("native-types-"+std::to_string(GetCurrentProcessId())+"-"+
            std::to_string(GetTickCount64())+".txt"));
    }
    if (!identity_file) return;
    const auto result=native_identity::inspect(handle);
    const auto id=handle && api && api->ed_get_object_id ? api->ed_get_object_id(handle) : 0;
    identity_file << "object_id=" << id << " status=" << result.status
        << " module=" << result.module << " type=" << result.name
        << " subobject_offset=" << result.subobject_offset << '\n';
    if(result.status=="ok" && result.module=="DCS.exe") {
        uintptr_t primary=0;
        if(native_identity::read(reinterpret_cast<uintptr_t>(handle)-result.subobject_offset,primary))
            identity_file << "  primary_vtable_rva=0x" << std::hex
                << primary-reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr)) << std::dec << '\n';
    }
    for (const auto& base : result.bases)
        identity_file << "  base=" << base.name << " member=" << base.member
            << " vbtable=" << base.vbtable << " vbdisp=" << base.vbdisp
            << " attributes=" << base.attributes << '\n';
    identity_file.flush();
}
}

extern "C" __declspec(dllexport) void ed_setup_object_api(const ed_object_api_entry* value) {
    std::lock_guard<std::mutex> guard(lock);
    api = value;
    record("setup", nullptr, 0, 0, 0);
#ifndef HORNET_STAGED_PROTOTYPE
    // Only run in DCS itself; standalone contract tests never capture their host.
    static bool captured=false;
    wchar_t host_path[32768]{};
    if (!captured && value && GetModuleFileNameW(nullptr,host_path,32768) &&
        _wcsicmp(std::filesystem::path(host_path).filename().c_str(),L"DCS.exe")==0) {
        captured=true;
        HMODULE module=nullptr;
        wchar_t path[32768]{};
        if(GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS |
            GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
            reinterpret_cast<LPCWSTR>(&open_log),&module) && GetModuleFileNameW(module,path,32768)) {
            snapshot_static_image(std::filesystem::path(path).parent_path()/"probe-logs");
            snapshot_static_image(std::filesystem::path(path).parent_path()/"probe-logs",L"WorldGeneral.dll");
        }
    }
#endif
}
extern "C" __declspec(dllexport) void ed_on_object_create(ED_OBJECT_HANDLE handle, uint64_t& cookie) {
    std::lock_guard<std::mutex> guard(lock);
#ifdef HORNET_STAGED_PROTOTYPE
    // Only one registered playback object can own the per-object native hook.
    const bool another_object=!observed.empty();
#endif
    observed[handle] = {};
#ifdef HORNET_STAGED_PROTOTYPE
    auto& created=observed[handle];
    created.runtime_id=api && api->ed_get_object_id ? api->ed_get_object_id(handle) : 0;
    if(another_object || !created.runtime_id)created.motion_attempted=true;
#endif
    record("create", handle, cookie, 0, 0);
#ifdef HORNET_RECORDED_PROTOTYPE
    HMODULE module=nullptr;wchar_t path[32768]{};
    if(GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
        reinterpret_cast<LPCWSTR>(&open_log),&module) && GetModuleFileNameW(module,path,32768)) {
        const char* status=observed[handle].path.load(std::filesystem::path(path).parent_path()/"recorded-flight.txt");
        record(status,handle,cookie,0,0);
#ifdef HORNET_STAGED_PROTOTYPE
        observed[handle].token=staged_playback::fingerprint(std::filesystem::path(path).parent_path()/"recorded-flight.txt");
        if(!observed[handle].token)observed[handle].motion_attempted=true;
#endif
        if(std::string(status)!="recording_loaded")observed[handle].motion_attempted=true;
    } else observed[handle].motion_attempted=true;
#endif
}
extern "C" __declspec(dllexport) void ed_on_object_simulate(ED_OBJECT_HANDLE handle, uint64_t& cookie, double time) {
    std::lock_guard<std::mutex> guard(lock);
    const auto found=observed.find(handle);
    if(found==observed.end())return;
    auto& state = found->second;
    ++state.calls;
    if (state.calls == 1) record_identity(handle);
    const auto motion_id=handle && api && api->ed_get_object_id ? api->ed_get_object_id(handle) : 0;
#ifdef HORNET_STAGED_PROTOTYPE
    native_body::Sample identity_sample{};
    const bool owned=motion_id && motion_id==state.runtime_id &&
        std::strcmp(native_body::sample(handle,identity_sample),"object_position_candidate")==0;
    if(!owned || state.terminal || (state.motion_attempted && !state.motion_active)) {
        stop_native_step(handle,state);
        if(!state.terminal) {
            if(!owned && (state.calls==1 || state.motion_active))record("staged_identity_rejected",handle,cookie,time,state.calls);
            state.motion_active=false;state.motion_attempted=true;
            if(motion_id && motion_id==state.runtime_id)staged_playback::publish(api,handle,state.token,staged_playback::failed);
        }
        return;
    }
    if(!staged_playback::available(api,handle)) {
        state.motion_attempted=true;
        record("staged_status_arguments_unavailable",handle,cookie,time,state.calls);
        return;
    }
    if(state.path.has_exterior && state.motion_active && time-state.start_time>1 && state.exterior_applied==0) {
        state.motion_active=false;stop_native_step(handle,state);
        staged_playback::publish(api,handle,state.token,staged_playback::failed);
        record("exterior_callback_missing",handle,cookie,time,state.calls);return;
    }
#endif
#ifdef HORNET_RECORDED_PROTOTYPE
    if(!state.motion_active && state.step_hook) stop_native_step(handle,state);
#endif
#ifdef HORNET_PROTOTYPE
    // Cosmetic defaults also apply before capture and after motion release.
    // No direct native-memory writes: this uses the documented object SDK.
    float speedbrake=0;
#ifdef HORNET_RECORDED_PROTOTYPE
    if(state.motion_active)speedbrake=state.path.brake_at(time-state.start_time);
#endif
#ifdef HORNET_STAGED_PROTOTYPE
    if(!state.motion_attempted && !state.path.samples.empty())speedbrake=state.path.brake_at(0);
    if(state.path.has_exterior) {
        state.exterior_elapsed=state.motion_active?time-state.start_time:0;
        state.exterior=state.path.at_sample(state.exterior_elapsed).exterior;
        api->ed_set_single_arg(handle,996,static_cast<float>(state.exterior_elapsed/1000));
        state.exterior_pending=hornet_appearance::apply_exterior(api,handle,state.runtime_id,state.exterior);
        if(!state.exterior_pending) {
            state.motion_attempted=true;state.motion_active=false;stop_native_step(handle,state);
            staged_playback::publish(api,handle,state.token,staged_playback::failed);
            record("exterior_write_failed",handle,cookie,time,state.calls);return;
        }
    }
    const auto appearance_status=hornet_appearance::apply(api,handle,speedbrake,state.runtime_id);
    if(std::strcmp(appearance_status,"off_verified") && std::strcmp(appearance_status,"recorded_brake_verified")) {
        state.motion_attempted=true;state.motion_active=false;stop_native_step(handle,state);
        staged_playback::publish(api,handle,state.token,staged_playback::failed);
        record(appearance_status,handle,cookie,time,state.calls);return;
    }
#else
    const auto appearance_status=hornet_appearance::apply(api,handle,speedbrake);
#endif
    if(state.calls==1 || time>=state.next_log)
        record(appearance_status,handle,cookie,time,state.calls);
#endif
#ifndef HORNET_STAGED_PROTOTYPE
    if(time<5) {
        native_body::Sample reading{};
        if(std::string(native_body::sample(handle,reading))=="object_position_candidate") {
            if(state.last_time>0 && time>state.last_time)
                state.measured_speed=std::hypot(reading.position[0]-state.last_x,reading.position[2]-state.last_z)/(time-state.last_time);
            state.last_time=time; state.last_x=reading.position[0]; state.last_z=reading.position[2];
        }
    }
#endif
#ifdef HORNET_STAGED_PROTOTYPE
    if(!state.motion_attempted) {
#else
    if(!state.motion_attempted && time>=5.0) {
#endif
        state.motion_attempted=true;
        native_body::Sample before{},after{}; turn_path::Pose initial{};
#ifdef HORNET_STAGED_PROTOTYPE
        const auto status=native_motion::apply(handle,motion_id,before,after,nullptr,&initial,false,nullptr,state.runtime_id);
#else
        const auto status=time<=5.2 ? native_motion::apply(handle,motion_id,before,after,nullptr,&initial) : "missed_window";
#endif
        state.motion_active=std::string(status)=="captured";
        if(state.motion_active) {
#ifdef HORNET_RECORDED_PROTOTYPE
#ifdef HORNET_STAGED_PROTOTYPE
            state.motion_active=state.path.initialize_exact(initial);
#else
            state.motion_active=state.path.initialize(initial,state.measured_speed);
#endif
            if(!state.motion_active)record("recording_alignment_rejected",handle,cookie,time,state.calls);
#else
            state.path.initialize(initial,state.measured_speed);
#endif
            state.start_time=time;
        }
        motion_file << motion_id << ',' << time << ',' << status;
        for(int i=0;i<72;++i) motion_file << ',';
        motion_file << '\n'; motion_file.flush();
    }
    if(state.motion_active) {
        const double elapsed=time-state.start_time;
#ifdef HORNET_RECORDED_PROTOTYPE
#ifdef HORNET_STAGED_PROTOTYPE
        const bool release=false; // Apply the endpoint before reporting completion.
        const bool finished=elapsed>=state.path.duration();
#else
        const bool release=elapsed>state.path.duration();
#endif
#else
        const bool release=elapsed>playback_path::duration;
#endif
        const auto target=state.path.at(elapsed);
        const auto target_motion=state.path.motion_at(elapsed);
        std::array<float,16> pre_command{};
        const bool pre_ok=native_identity::read(reinterpret_cast<uintptr_t>(handle)+0x174,pre_command);
        std::array<float,3> rates_before{},rates_after{};
        const bool rates_before_ok=native_motion::read_rates(handle,rates_before);
        std::array<float,3> velocity_before{},velocity_after{};
        const bool velocity_before_ok=native_velocity::read(handle,velocity_before);
        // Calm-air baseline: match motion throughout the controlled path.
        // At release, stop both pose and motion writes and observe native recovery.
        const bool match_motion=!release;
        const bool neutralize_roll=false;
        LARGE_INTEGER clock_frequency{},apply_start{},apply_end{};
        QueryPerformanceFrequency(&clock_frequency);
        QueryPerformanceCounter(&apply_start);
        native_body::Sample before{},after{};
#ifdef HORNET_STAGED_PROTOTYPE
        const auto status=elapsed<0 ? "staged_clock_reversed" : native_motion::apply(handle,motion_id,before,after,&target,nullptr,false,&target_motion,state.runtime_id);
#else
        const auto status=release ? "released" : native_motion::apply(handle,motion_id,before,after,&target,nullptr,false,match_motion ? &target_motion : nullptr);
#endif
#ifdef HORNET_RECORDED_PROTOTYPE
        if(!release && std::strcmp(status,"called")==0) {
            if(!state.step_hook) {
#ifdef HORNET_STAGED_PROTOTYPE
                state.step_status=install_native_step(handle,state.path.has_exterior);
#else
                state.step_status=install_native_step(handle);
#endif
                state.step_hook=std::strcmp(state.step_status,"step_hook_installed")==0;
                record(state.step_status,handle,cookie,time,state.calls);
            }
            if(state.step_hook) { state.step_motion=target_motion; state.step_pending=true; }
            else state.motion_active=false;
        } else stop_native_step(handle,state);
#endif
        QueryPerformanceCounter(&apply_end);
        const bool rates_after_ok=native_motion::read_rates(handle,rates_after);
        const bool velocity_after_ok=native_velocity::read(handle,velocity_after);
        std::array<float,16> actual{};
        const bool actual_ok=native_identity::read(reinterpret_cast<uintptr_t>(handle)+0x174,actual);
        motion_file << motion_id << ',' << time << ',' << status;
        for(double v:target) motion_file << ',' << v;
        for(float v:actual) { motion_file << ','; if(actual_ok) motion_file << v; }
        for(float v:pre_command) { motion_file << ','; if(pre_ok) motion_file << v; }
        motion_file << ',' << static_cast<double>(apply_start.QuadPart)/clock_frequency.QuadPart
                    << ',' << 1000.0*(apply_end.QuadPart-apply_start.QuadPart)/clock_frequency.QuadPart
                    << ',' << neutralize_roll;
        for(float v:rates_before) { motion_file << ','; if(rates_before_ok) motion_file << v; }
        for(float v:rates_after) { motion_file << ','; if(rates_after_ok) motion_file << v; }
        motion_file << ",0,inactive," << match_motion;
        for(float v:velocity_before) { motion_file << ','; if(velocity_before_ok) motion_file << v; }
        for(float v:velocity_after) { motion_file << ','; if(velocity_after_ok) motion_file << v; }
        for(float v:target_motion.velocity) motion_file << ',' << v;
        for(float v:target_motion.angular) motion_file << ',' << v;
#ifdef HORNET_RECORDED_PROTOTYPE
        motion_file << ',' << state.step_calls << ',' << state.step_applied << ',' << state.step_status;
#else
        motion_file << ",0,0,inactive";
#endif
        motion_file << '\n'; motion_file.flush();
        if(release || std::string(status)!="called") state.motion_active=false;
#ifdef HORNET_STAGED_PROTOTYPE
        if(state.motion_active) {
            state.exterior_finished=finished && state.path.has_exterior;
            const auto phase=finished && !state.path.has_exterior?staged_playback::complete:staged_playback::running;
            if(!staged_playback::publish(api,handle,state.token,phase)) {
                record("staged_status_readback_failed",handle,cookie,time,state.calls);
                state.motion_active=false;
            } else if(finished && !state.path.has_exterior) {
                state.terminal=true;state.motion_active=false;
                record("staged_complete",handle,cookie,time,state.calls);
            } else if(elapsed==0)record("staged_started",handle,cookie,time,state.calls);
        }
        if(!state.motion_active) {
            stop_native_step(handle,state);
            if(!state.terminal)staged_playback::publish(api,handle,state.token,staged_playback::failed);
        }
#endif
    }
    if (state.calls == 1 || time >= state.next_log) {
        record("simulate", handle, cookie, time, state.calls);
        native_body::Sample body{};
        const auto status=native_body::sample(handle,body);
        const bool valid=std::string(status)=="read";
        const bool position_only=std::string(status)=="object_position_candidate";
        const auto id=handle && api && api->ed_get_object_id ? api->ed_get_object_id(handle) : 0;
        body_file << id << ',' << time << ',' << status;
        if(valid || position_only) {
            for(double v:body.position) body_file << ',' << v;
            if(valid) for(double v:body.velocity) body_file << ',' << v;
            else body_file << ",,,";
        } else body_file << ",,,,,,";
        body_file << '\n';
        body_file.flush();
        state.next_log = time + 0.1;
    }
}
extern "C" __declspec(dllexport) void ed_on_object_destroy(ED_OBJECT_HANDLE handle, uint64_t& cookie) {
    std::lock_guard<std::mutex> guard(lock);
    const auto it = observed.find(handle);
#ifdef HORNET_RECORDED_PROTOTYPE
    if(it!=observed.end()) {
        stop_native_step(handle,it->second);
        record(it->second.step_status,handle,cookie,0,it->second.calls);
    }
#endif
    record("destroy", handle, cookie, 0, it == observed.end() ? 0 : it->second.calls);
    observed.erase(handle);
}
static_assert(std::is_same_v<decltype(&ed_setup_object_api), PFN_ED_SETUP_OBJECT_API>);
static_assert(std::is_same_v<decltype(&ed_on_object_create), PFN_ED_ON_OBJECT_CREATE>);
static_assert(std::is_same_v<decltype(&ed_on_object_simulate), PFN_ED_ON_OBJECT_SIMULATE>);
static_assert(std::is_same_v<decltype(&ed_on_object_destroy), PFN_ED_ON_OBJECT_DESTROY>);
