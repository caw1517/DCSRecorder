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
#include <chrono>
#include <map>
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
#ifdef HORNET_SURFACE_PROTOTYPE
#include "surface-start/ai_ground.h"
#endif
#ifdef HORNET_STAGED_PROTOTYPE
#include "staged_playback.h"
#ifdef HORNET_RELEASE_PROTOTYPE
#include "release-start/policy.h"
#include <sstream>
#endif
#include "engine_native_layout.h"
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
// The bound ground trial and the general surface controller share read-only
// ground pose tracing.
#if defined(HORNET_GROUND_PROTOTYPE) || defined(HORNET_SURFACE_PROTOTYPE)
#define HORNET_GROUND_TRACE
#endif

namespace {
const ed_object_api_entry* api = nullptr;
std::mutex lock;
std::ofstream log_file;
std::ofstream identity_file;
std::ofstream body_file;
std::ofstream motion_file;
#ifdef HORNET_GROUND_TRACE
std::ofstream ground_pose_file;
std::ofstream ai_phase_file; // read-only woAIPlane phase fields (research #36)
#endif
#ifdef HORNET_STAGED_PROTOTYPE
std::ofstream exterior_file,engine_file;
#endif
// Evidence logs flush every tick, so the last tick before a failure is on disk
// while DCS is still running.
#ifdef HORNET_FORMATION_PROTOTYPE
// Formation: several aircraft write traces on the sim thread while the player
// records, and a 150 ms stall fails the take. Traces flush about once a second
// per file instead of every row (the stream still flushes when closed).
void flush_trace(std::ofstream& file) {
    static std::map<const std::ofstream*,std::chrono::steady_clock::time_point> last;
    const auto now=std::chrono::steady_clock::now();
    auto& at=last[&file];
    if(now-at>=std::chrono::seconds(1)) {file.flush();at=now;}
}
#else
void flush_trace(std::ofstream& file) {file.flush();}
#endif
struct Observation {
    uint64_t calls = 0; double next_log = 0; bool motion_attempted=false, motion_active=false;
    double start_time=0, last_time=0, last_x=0, last_z=0, measured_speed=145; playback_path::Path path;
#ifdef HORNET_RECORDED_PROTOTYPE
    bool step_hook=false, step_pending=false;
#ifdef HORNET_STAGED_PROTOTYPE
    uint64_t runtime_id=0,token=0;
    bool terminal=false;
#ifdef HORNET_RELEASE_PROTOTYPE
    release_start::Clock clock;
    uint64_t generation=0;
#endif
#ifdef HORNET_FORMATION_PROTOTYPE
    // Formation: the control hook assigns this aircraft's take by runtime ID.
    // Until then the spawn pose is held with zero motion.
    bool assigned=false,hold_captured=false;
    double hold_since=-1;
    std::array<double,16> hold_pose{};
#endif
    // Surface controller: the take ended on a grounded sample. Ownership, ground
    // pose restoration and the final supported state continue until destroy.
    bool parked=false;
    bool ground_flag_logged=false,taxi_mode_logged=false;
    int steps_since_sdk=0;uint64_t extra_restores=0;double native_step_dt=0.02,last_sdk_elapsed=0;
    bool exterior_pending=false,exterior_finished=false;
#ifdef HORNET_FAULT_INJECTION
    // Diagnostic build only: armed by the bridge to exercise runtime failure cleanup.
    bool fault_clock=false,fault_state=false;
#endif
    double exterior_elapsed=0;
    float snapshot_brake=0;
    uint64_t exterior_applied=0;
    hornet_exterior::Values exterior{};
    hornet_engine::Values engine{};
    hornet_lights::Values lights{};
    hornet_wheels::Values wheels{};
    double canopy=0;
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
#ifdef HORNET_FORMATION_PROTOTYPE
// Every take this module may play, from bin/takes/*.txt, by tape fingerprint.
// Reloaded when the first object of a new mission is created.
struct Take {std::filesystem::path file;playback_path::Path path;};
std::unordered_map<uint64_t,Take> takes;
#endif
#ifdef HORNET_RELEASE_PROTOTYPE
uint64_t release_generation=0;
#endif

#ifdef HORNET_RECORDED_PROTOTYPE
#ifdef HORNET_STAGED_PROTOTYPE
void drain_engine(const void* handle,Observation& state,double time) {
    if(!state.path.has_engine)return;
    uint64_t lost=0;
    for(const auto& call:native_step_hook::drain_engine(reinterpret_cast<uintptr_t>(handle)-8,lost)) {
        MEMORY_BASIC_INFORMATION region{};std::string module="unknown";uintptr_t rva=0;
        if(VirtualQuery(reinterpret_cast<void*>(call.caller),&region,sizeof(region)) && region.Type==MEM_IMAGE) {
            char path[32768]{};GetModuleFileNameA(static_cast<HMODULE>(region.AllocationBase),path,sizeof(path));
            module=std::filesystem::path(path).filename().string();rva=call.caller-reinterpret_cast<uintptr_t>(region.AllocationBase);
        }
        engine_file << state.runtime_id << ',' << time << ',' <<
#ifdef HORNET_RELEASE_PROTOTYPE
            state.exterior_elapsed <<
#elif defined(HORNET_HELD_PROTOTYPE)
            held_start::replay_time(time,state.start_time) <<
#else
            time-state.start_time <<
#endif
            ',' << module << ',' << rva << ','
            << call.engine << ',' << call.channel << ',' << call.overridden << ',' << call.original << ',' << call.returned << '\n';
    }
    flush_trace(engine_file);
    if(lost || !engine_file) {state.motion_active=false;log_file << "engine_trace_failed," << state.runtime_id << ',' << time << '\n';log_file.flush();}
}
#ifdef HORNET_GROUND_TRACE
// Read-only boundary evidence: distinguish native integration from animation
// or later pose replacement. No extra pose/velocity writes are performed.
void record(const char* event, ED_OBJECT_HANDLE handle, uint64_t cookie,double time, uint64_t calls);
void trace_ground_pose(const char* phase,const void* handle,const Observation& state) {
    if(state.path.samples.empty() || !ground_pose_file)return;
    std::array<float,16> pose{};std::array<double,3> precise{};
    const auto object=reinterpret_cast<uintptr_t>(handle);
    const bool readable=native_identity::read(object+0x174,pose) && native_identity::read(object+0x1c8,precise);
    const auto target=state.path.at_sample(state.clock.elapsed);
    ground_pose_file<<phase<<','<<state.runtime_id<<','<<state.calls<<','<<state.step_calls<<','
        <<state.clock.last<<','<<state.clock.elapsed<<','<<readable;
    for(double v:target.p)ground_pose_file<<','<<v;
    for(double v:precise)ground_pose_file<<','<<v;
    for(int k=0;k<3;++k)ground_pose_file<<','<<pose[12+k];
    ground_pose_file<<'\n';flush_trace(ground_pose_file);
    // Offsets from the woAIPlane complete object (SDK handle - 8), DCS 2.9.30 static
    // reading in docs/research/dcs-ai-plane-ground-phase.md. Guarded reads only.
    if(ai_phase_file) {
        const auto complete=object-8;
        int32_t mode=0;double height=0;float y=0;uint8_t b7cb=0,b26d3=0,b5591=0,gate=0;uint64_t q5568=0;
        const bool ok=native_identity::read(complete+0x7f4,mode) && native_identity::read(complete+0x248,height) &&
            native_identity::read(complete+0x1b0,y) && native_identity::read(complete+0x7cb,b7cb) &&
            native_identity::read(complete+0x26d3,b26d3) && native_identity::read(complete+0x5568,q5568) &&
            native_identity::read(complete+0x5591,b5591) && native_identity::read(complete+0x5002,gate);
        ai_phase_file<<phase<<','<<state.calls<<','<<state.step_calls<<','<<state.clock.last<<','<<state.clock.elapsed<<','
            <<state.path.ground_at(state.clock.elapsed)<<','<<ok<<','<<mode<<','<<height<<','<<y<<','<<int(b7cb)<<','
            <<int(b26d3)<<','<<q5568<<','<<int(b5591)<<','<<int(gate)<<'\n';
        flush_trace(ai_phase_file);
    }
}
void after_ground_native_step(const void* handle) {
    std::lock_guard<std::mutex> guard(lock);
    const auto key=reinterpret_cast<ED_OBJECT_HANDLE>(const_cast<void*>(handle));
    const auto it=observed.find(key);
    if(it!=observed.end() && it->second.motion_active)trace_ground_pose("after_step",handle,it->second);
}
#endif
void after_native_animation(const void* handle) {
    std::lock_guard<std::mutex> guard(lock);
    const auto sdk_handle=reinterpret_cast<ED_OBJECT_HANDLE>(const_cast<void*>(handle));
    const auto found=observed.find(sdk_handle);if(found==observed.end())return;
    auto& state=found->second;
    if(!state.motion_active || !state.exterior_pending || !state.path.has_exterior ||
       !api || !api->ed_get_object_id || api->ed_get_object_id(sdk_handle)!=state.runtime_id)return;
#ifdef HORNET_GROUND_TRACE
    trace_ground_pose("after_animation",handle,state);
#endif
    const auto view=api->ed_get_object_args(sdk_handle);
    if(!view.data || view.size<=18) {state.motion_active=false;return;}
    std::array<float,13> before{};
    for(size_t i=0;i<before.size();++i)before[i]=view.data[hornet_exterior::channels[i]];
    bool applied=hornet_appearance::apply_exterior(api,sdk_handle,state.runtime_id,state.exterior);
    // Include legacy brake at the same post-animation boundary as other state.
    const auto brake_view=api->ed_get_object_args(sdk_handle);
    if(!brake_view.data || brake_view.size<=21)applied=false;
    else {
        const float before_brake=brake_view.data[21];
        const auto status=hornet_appearance::apply(api,sdk_handle,state.snapshot_brake,state.runtime_id,state.path.has_lights);
        applied=(!std::strcmp(status,"off_verified") || !std::strcmp(status,"recorded_brake_verified")) && applied;
        const auto after_brake=api->ed_get_object_args(sdk_handle);
        if(!after_brake.data || after_brake.size<=21)applied=false;
        else exterior_file << state.runtime_id << ',' << state.calls << ',' << state.exterior_elapsed
            << ",21," << state.snapshot_brake << ',' << before_brake << ',' << after_brake.data[21] << '\n';
    }
    if(state.path.has_wheels) {
        const auto wheel_before=api->ed_get_object_args(sdk_handle);
        hornet_wheels::Values before_wheels{};
        if(!wheel_before.data || wheel_before.size<=103)applied=false;
        else {
            for(size_t i=0;i<before_wheels.size();++i)before_wheels[i]=wheel_before.data[hornet_wheels::channels[i]];
            applied=hornet_appearance::apply_wheels(api,sdk_handle,state.runtime_id,state.wheels) && applied;
            const auto wheel_after=api->ed_get_object_args(sdk_handle);
            if(!wheel_after.data || wheel_after.size<=103)applied=false;
            else for(size_t i=0;i<before_wheels.size();++i)exterior_file << state.runtime_id << ',' << state.calls << ','
                << state.exterior_elapsed << ',' << hornet_wheels::channels[i] << ',' << state.wheels[i]
                << ',' << before_wheels[i] << ',' << wheel_after.data[hornet_wheels::channels[i]] << '\n';
        }
    }
    if(state.path.has_canopy) {
        const auto canopy_before=api->ed_get_object_args(sdk_handle);
        if(!canopy_before.data || canopy_before.size<=hornet_canopy::channel)applied=false;
        else {
            const float before_canopy=canopy_before.data[hornet_canopy::channel];
            applied=hornet_appearance::apply_canopy(api,sdk_handle,state.runtime_id,state.canopy) && applied;
            const auto canopy_after=api->ed_get_object_args(sdk_handle);
            if(!canopy_after.data || canopy_after.size<=hornet_canopy::channel)applied=false;
            else exterior_file << state.runtime_id << ',' << state.calls << ',' << state.exterior_elapsed
                << ',' << hornet_canopy::channel << ',' << state.canopy << ',' << before_canopy
                << ',' << canopy_after.data[hornet_canopy::channel] << '\n';
        }
    }
    if(state.path.has_lights) {
        const auto light_before=api->ed_get_object_args(sdk_handle);
        hornet_lights::Values before_lights{};
        if(!light_before.data || light_before.size<=212)applied=false;
        else {
            for(size_t i=0;i<before_lights.size();++i)before_lights[i]=light_before.data[hornet_lights::channels[i]];
            applied=hornet_appearance::apply_lights(api,sdk_handle,state.runtime_id,state.lights) && applied;
            const auto light_after=api->ed_get_object_args(sdk_handle);
            if(!light_after.data || light_after.size<=212)applied=false;
            else for(size_t i=0;i<before_lights.size();++i)exterior_file << state.runtime_id << ',' << state.calls << ','
                << state.exterior_elapsed << ',' << hornet_lights::channels[i] << ',' << state.lights[i]
                << ',' << before_lights[i] << ',' << light_after.data[hornet_lights::channels[i]] << '\n';
        }
    }
    if(state.path.has_engine) {
        const auto engine_before=api->ed_get_object_args(sdk_handle);
        std::array<float,4> before_engine{};
        if(!engine_before.data || engine_before.size<=90)applied=false;
        else {
            for(size_t i=0;i<4;++i)before_engine[i]=engine_before.data[hornet_engine::channels[i]];
            applied=hornet_appearance::apply_engine(api,sdk_handle,state.runtime_id,state.engine) && applied;
            const auto engine_after=api->ed_get_object_args(sdk_handle);
            if(!engine_after.data || engine_after.size<=90)applied=false;
            else for(size_t i=0;i<4;++i)exterior_file << state.runtime_id << ',' << state.calls << ','
                << state.exterior_elapsed << ',' << hornet_engine::channels[i] << ',' << state.engine[i]
                << ',' << before_engine[i] << ',' << engine_after.data[hornet_engine::channels[i]] << '\n';
        }
    }
    const auto after=api->ed_get_object_args(sdk_handle);
    if(applied) {
        ++state.exterior_applied;
        for(size_t i=0;i<before.size();++i)exterior_file << state.runtime_id << ',' << state.calls << ','
            << state.exterior_elapsed << ',' << hornet_exterior::channels[i] << ',' << state.exterior[i]
            << ',' << before[i] << ',' << after.data[hornet_exterior::channels[i]] << '\n';
        flush_trace(exterior_file);
    }
    if(!applied || !exterior_file) {
        state.motion_active=false;state.exterior_pending=false;
        staged_playback::publish(api,sdk_handle,state.token,staged_playback::failed);
    }
#ifdef HORNET_HELD_PROTOTYPE
    else if(!staged_playback::publish(api,sdk_handle,state.token,held_start::status)) {
        state.motion_active=false;state.exterior_pending=false;
    }
#endif
#ifdef HORNET_RELEASE_PROTOTYPE
    else if(!state.clock.playing()) {
        if(!staged_playback::publish(api,sdk_handle,state.token,held_start::status))state.motion_active=false;
    }
#endif
#ifdef HORNET_SURFACE_PROTOTYPE
    else if(state.parked) {
        if(!staged_playback::publish(api,sdk_handle,state.token,staged_playback::parked))state.motion_active=false;
    }
#endif
    else if(state.exterior_finished) {
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
#ifdef HORNET_SURFACE_PROTOTYPE
// Tape motion at replay time t; zero while held or parked.
turn_path::Motion surface_motion(const Observation& state,double t) {
    return state.clock.playing() && !state.parked?state.path.motion_at(t):turn_path::Motion{};
}
// After touchdown DCS ran 2-3 native steps per SDK tick (takeoff-landing live-8);
// only the first was restored. Extra steps in the same tick restore the tape at
// the replay time they represent, from the previous interval's step length.
void restore_extra_step(const void* handle,Observation& state) {
    if(!state.clock.playing() || state.steps_since_sdk<2 || state.steps_since_sdk>5)return;
    const auto id=api && api->ed_get_object_id ? api->ed_get_object_id(reinterpret_cast<ED_OBJECT_HANDLE>(const_cast<void*>(handle))) : 0;
    if(!id || id!=state.runtime_id)return;
    const double t=std::min(state.clock.elapsed+(state.steps_since_sdk-1)*state.native_step_dt,state.path.duration());
    const auto target=state.path.at(t);
    auto motion=surface_motion(state,t);
    native_body::Sample before{},after{};
    const char* status=native_motion::apply(handle,id,before,after,&target,nullptr,false,&motion,state.runtime_id,true);
    if(std::strcmp(status,"called")==0) {++state.extra_restores;trace_ground_pose("before_extra_step_restored",handle,state);}
    else {
        const auto sdk_handle=reinterpret_cast<ED_OBJECT_HANDLE>(const_cast<void*>(handle));
        state.step_status=status;state.motion_active=false;record(status,sdk_handle,0,state.clock.last,state.calls);
        staged_playback::publish(api,sdk_handle,state.token,staged_playback::failed);
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
#ifdef HORNET_SURFACE_PROTOTYPE
    if(state.motion_active) {
        ++state.steps_since_sdk;
        if(!state.step_pending) {restore_extra_step(handle,state);return;}
    }
#endif
    if(!state.motion_active || !state.step_pending) return;
#ifdef HORNET_GROUND_TRACE
    trace_ground_pose("before_step",handle,state);
#endif
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
#ifdef HORNET_GROUND_TRACE
        // Live traces show the native ground correction replaces pose after the
        // SDK command and before this integration boundary, and keeps doing so on
        // airborne samples after liftoff (the takeoff take stayed pinned to the
        // runway for 1.35 s). Surface takes therefore restore before every step.
        const bool ground=true;
        if(ground) {
            // Restore the same guarded tape sample here; consume only this SDK tick's work.
            const auto target=state.path.at(state.clock.elapsed);
            native_body::Sample before{},after{};
            state.step_status=native_motion::apply(handle,id,before,after,&target,nullptr,
                                                   false,&state.step_motion,state.runtime_id,true);
#ifdef HORNET_SURFACE_PROTOTYPE
            if(state.path.ground_at(state.clock.elapsed)) {
                const int flag=surface_ai::hold_ground_flag(handle);
                if(flag<0)state.step_status="ground_flag_unconfirmed";
                else if(flag>0 && !state.ground_flag_logged){state.ground_flag_logged=true;record("ground_flag_set",reinterpret_cast<ED_OBJECT_HANDLE>(const_cast<void*>(handle)),0,state.clock.elapsed,state.calls);}
                const int mode=surface_ai::hold_taxi_mode(handle);
                if(mode<0)state.step_status="taxi_mode_unconfirmed";
                else if(mode>0 && !state.taxi_mode_logged){state.taxi_mode_logged=true;record("taxi_mode_set",reinterpret_cast<ED_OBJECT_HANDLE>(const_cast<void*>(handle)),0,state.clock.elapsed,state.calls);}
            }
#endif
            if(std::strcmp(state.step_status,"called")==0)
                trace_ground_pose("before_step_restored",handle,state);
        } else {
            state.step_status=native_velocity::validate(handle,state.step_motion);
            if(std::strcmp(state.step_status,"valid")==0)
                state.step_status=native_velocity::write_validated(handle,state.step_motion);
        }
#else
        state.step_status=native_velocity::validate(handle,state.step_motion);
        if(std::strcmp(state.step_status,"valid")==0)
            state.step_status=native_velocity::write_validated(handle,state.step_motion);
#endif
    }
#ifdef HORNET_STAGED_PROTOTYPE
    if(std::strcmp(state.step_status,"called")==0) {
        state.step_status=native_presentation_pitch::layout_valid() ?
            native_presentation_pitch::clear_validated(handle,state.presentation) : "presentation_layout_mismatch";
    }
#endif
    if(std::strcmp(state.step_status,"called")==0) ++state.step_applied;
    else {
        state.motion_active=false;
#ifdef HORNET_GROUND_TRACE
        record(state.step_status,sdk_handle,0,state.clock.last,state.calls);
        staged_playback::publish(api,sdk_handle,state.token,staged_playback::failed);
#endif
    }
}
const char* install_native_step(const void* handle,bool exterior=false,bool engine=false) {
    const auto image=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    uintptr_t locator=0,next_locator=0;
    // RTTI boundaries establish the complete primary table's exact length.
    if(!native_identity::read(image+native_build::dcs(0x11461f8),locator) || locator!=image+native_build::dcs(0x133b650) ||
       !native_identity::read(image+native_build::dcs(0x1146ff0),next_locator) || next_locator!=image+native_build::dcs(0x133b770))
        return "step_table_boundary_mismatch";
    std::array<unsigned char,15> prologue{};
    if(!native_identity::read(image+native_build::dcs(0x70fef0),prologue) ||
       prologue!=std::array<unsigned char,15>{0x48,0x8b,0xc4,0x48,0x89,0x58,0x10,0x48,0x89,0x70,0x18,0x48,0x89,0x78,0x20})
        return "step_entry_mismatch";
    std::array<unsigned char,10> callsite{};
    if(!native_identity::read(image+native_build::dcs(0x675279),callsite) ||
       callsite!=std::array<unsigned char,10>{0xff,0x90,0x70,0x0c,0,0,0x48,0x8b,0x4b,0x58})
        return "step_callsite_mismatch";
#ifdef HORNET_STAGED_PROTOTYPE
    native_step_hook::Engine getters{};
    if(engine) {
        unsigned char count=0;
        if(!engine_native_layout::valid() || !native_identity::read(reinterpret_cast<uintptr_t>(handle)-8+0x811,count) || count!=2)
            return "engine_layout_rejected";
        getters={reinterpret_cast<native_step_hook::RPM>(image+native_build::dcs(0x66d160)),reinterpret_cast<native_step_hook::Scalar>(image+native_build::dcs(0x66d1c0)),reinterpret_cast<native_step_hook::Scalar>(image+native_build::dcs(0x60f110))};
    }
    if(exterior) {
        std::array<unsigned char,18> entry{};
        std::array<unsigned char,15> dispatch{};
        std::array<unsigned char,5> writer{};
        if(!native_identity::read(image+native_build::dcs(0x6b6070),entry) || entry!=std::array<unsigned char,18>{0x48,0x8b,0xc4,0x48,0x89,0x58,0x10,0x55,0x56,0x57,0x41,0x54,0x41,0x55,0x41,0x56,0x41,0x57} ||
           !native_identity::read(image+native_build::dcs(0x67529c),dispatch) || dispatch!=std::array<unsigned char,15>{0x41,0xb0,1,0x0f,0x28,0xce,0x48,0x8b,1,0xff,0x90,0x10,0x0c,0,0} ||
           !native_identity::read(image+native_build::dcs(0x6b73a7),writer) || writer!=native_build::animation_writer)return "animation_layout_mismatch";
        return native_step_hook::install(reinterpret_cast<uintptr_t>(handle)-8,image+native_build::dcs(0x1146200),
            reinterpret_cast<native_step_hook::Step>(image+native_build::dcs(0x70fef0)),&before_native_step,
#ifdef HORNET_GROUND_TRACE
            &after_ground_native_step,
#else
            nullptr,
#endif
            reinterpret_cast<native_step_hook::Animation>(image+native_build::dcs(0x6b6070)),&after_native_animation,engine?&getters:nullptr);
    }
#endif
    return native_step_hook::install(reinterpret_cast<uintptr_t>(handle)-8,image+native_build::dcs(0x1146200),
        reinterpret_cast<native_step_hook::Step>(image+native_build::dcs(0x70fef0)),&before_native_step);
}
void stop_native_step(const void* handle,Observation& state) {
    state.step_pending=false;
#ifdef HORNET_STAGED_PROTOTYPE
    state.exterior_pending=false;
    drain_engine(handle,state,state.start_time+state.exterior_elapsed);
    const auto presentation_status=native_presentation_pitch::restore(handle,state.presentation);
    if(state.presentation.active) {
        state.step_status=presentation_status;state.motion_active=false;
        if(log_file.is_open())log_file << "presentation_restore_error," << presentation_status << '\n';
    }
#endif
    if(!state.step_hook) return;
    state.step_status=native_step_hook::restore(reinterpret_cast<uintptr_t>(handle)-8);
    state.step_hook=native_step_hook::recognizes(reinterpret_cast<uintptr_t>(handle)-8,
        native_step_hook::table(),reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))+native_build::dcs(0x1146200));
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
#ifdef HORNET_GROUND_TRACE
    ground_pose_file.open(folder/("ground-pose-"+std::to_string(GetCurrentProcessId())+".csv"));
    ground_pose_file<<"phase,id,call,step,model_time,replay_time,readable,target_x,target_y,target_z,precise_x,precise_y,precise_z,float_x,float_y,float_z\n"<<std::setprecision(15);
    ai_phase_file.open(folder/("ai-phase-"+std::to_string(GetCurrentProcessId())+".csv"));
    ai_phase_file<<"phase,call,step,model_time,replay_time,tape_ground,readable,mode_7f4,height_248,pos_y_1b0,b_7cb,b_26d3,q_5568,b_5591,gate_5002\n"<<std::setprecision(15);
#endif
#ifdef HORNET_STAGED_PROTOTYPE
    exterior_file.open(folder/("exterior-"+std::to_string(GetCurrentProcessId())+".csv"));
    exterior_file << "id,call,elapsed,arg,requested,before,after\n" << std::setprecision(12);
    engine_file.open(folder/("engine-"+std::to_string(GetCurrentProcessId())+".csv"));
    engine_file << "id,time,elapsed,caller_module,caller_rva,engine,channel,overridden,original,returned\n" << std::setprecision(12);
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

#ifdef HORNET_FORMATION_PROTOTYPE
void load_takes() {
    takes.clear();
    HMODULE module=nullptr;wchar_t path[32768]{};
    if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
        reinterpret_cast<LPCWSTR>(&open_log),&module) || !GetModuleFileNameW(module,path,32768))return;
    const auto folder=std::filesystem::path(path).parent_path()/"takes";
    std::error_code error;std::vector<uint64_t> duplicates;
    for(const auto& entry:std::filesystem::directory_iterator(folder,error)) {
        if(!entry.is_regular_file() || entry.path().extension()!=".txt")continue;
        Take take{entry.path(),{}};
        const char* status=take.path.load(take.file);
        const auto token=staged_playback::fingerprint(take.file);
        open_log();
        log_file<<"formation_take,"<<take.file.filename().string()<<','<<std::hex<<token<<std::dec<<','<<status<<'\n';
        const auto& p=take.path;
        if(std::string(status)!="recording_loaded" || !token ||
           !p.has_exterior || !p.has_engine || !p.has_lights || !p.has_canopy || !p.has_wheels)continue;
        // Two takes on one 48-bit bridge key cannot be told apart; refuse both.
        bool clash=false;
        for(const auto& [other,unused]:takes)
            if(staged_playback::high(other)==staged_playback::high(token) && staged_playback::low(other)==staged_playback::low(token))clash=true;
        if(clash)duplicates.push_back(token);
        else takes.emplace(token,std::move(take));
    }
    for(const auto token:duplicates)
        for(auto it=takes.begin();it!=takes.end();)
            it=staged_playback::high(it->first)==staged_playback::high(token) && staged_playback::low(it->first)==staged_playback::low(token)?takes.erase(it):std::next(it);
    log_file<<"formation_takes_loaded,"<<takes.size()<<','<<duplicates.size()<<'\n';log_file.flush();
}
// Formation aircraft wait for the hook's assignment at their spawn pose. Ten
// seconds of model time without one fails this aircraft alone.
void hold_unassigned(ED_OBJECT_HANDLE handle,Observation& state,uint64_t motion_id,uint64_t cookie,double time) {
    native_body::Sample before{},after{};
    if(!state.hold_captured) {
        const auto status=native_motion::apply(handle,motion_id,before,after,nullptr,&state.hold_pose,false,nullptr,state.runtime_id);
        state.hold_captured=std::strcmp(status,"captured")==0;state.hold_since=time;
        record(state.hold_captured?"formation_hold_captured":status,handle,cookie,time,state.calls);
        if(!state.hold_captured)state.motion_attempted=true;
        return;
    }
    if(time-state.hold_since>10) {
        state.motion_attempted=true;record("formation_assignment_timeout",handle,cookie,time,state.calls);return;
    }
    const turn_path::Motion still{};
    const auto status=native_motion::apply(handle,motion_id,before,after,&state.hold_pose,nullptr,false,&still,state.runtime_id);
    if(std::strcmp(status,"called")) {state.motion_attempted=true;record(status,handle,cookie,time,state.calls);}
}
// Bridge: give the object with this runtime ID the take with this bridge key.
std::string assign_take(double high,double low,double runtime_id) {
    const Take* take=nullptr;uint64_t token=0;
    for(const auto& [key,value]:takes)
        if(high==staged_playback::high(key) && low==staged_playback::low(key)) {take=&value;token=key;}
    if(!take)return "REFUSED,take_unavailable";
    std::pair<const ED_OBJECT_HANDLE,Observation>* target=nullptr;
    for(auto& entry:observed) {
        if(entry.second.assigned && entry.second.token==token)return "REFUSED,take_already_assigned";
        if(static_cast<double>(entry.second.runtime_id)==runtime_id)target=&entry;
    }
    if(!target)return "REFUSED,object_unavailable";
    auto& state=target->second;
    if(state.assigned)return "REFUSED,object_already_assigned";
    if(state.motion_attempted || state.terminal)return "REFUSED,object_failed";
    state.path=take->path;state.token=token;state.assigned=true;
    open_log();
    log_file<<"formation_assigned,"<<state.runtime_id<<','<<std::hex<<token<<std::dec<<','<<take->file.filename().string()
            <<','<<state.generation<<'\n';log_file.flush();
    std::ostringstream result;result<<"ASSIGNED,"<<state.generation<<','<<state.runtime_id;
    return result.str();
}
#endif
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
#if defined(HORNET_STAGED_PROTOTYPE) && !defined(HORNET_FORMATION_PROTOTYPE)
    // Only one registered playback object can own the per-object native hook.
    const bool another_object=!observed.empty();
#endif
#ifdef HORNET_FORMATION_PROTOTYPE
    if(observed.empty())load_takes();
#endif
    observed[handle] = {};
#ifdef HORNET_RELEASE_PROTOTYPE
    observed[handle].generation=++release_generation;
#endif
#ifdef HORNET_STAGED_PROTOTYPE
    auto& created=observed[handle];
    created.runtime_id=api && api->ed_get_object_id ? api->ed_get_object_id(handle) : 0;
#ifdef HORNET_FORMATION_PROTOTYPE
    if(!created.runtime_id)created.motion_attempted=true;
#else
    if(another_object || !created.runtime_id)created.motion_attempted=true;
#endif
#endif
    record("create", handle, cookie, 0, 0);
#if defined(HORNET_RECORDED_PROTOTYPE) && !defined(HORNET_FORMATION_PROTOTYPE)
    HMODULE module=nullptr;wchar_t path[32768]{};
    if(GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
        reinterpret_cast<LPCWSTR>(&open_log),&module) && GetModuleFileNameW(module,path,32768)) {
        const char* status=observed[handle].path.load(std::filesystem::path(path).parent_path()/"recorded-flight.txt");
        record(status,handle,cookie,0,0);
#if defined(HORNET_STAGED_PROTOTYPE) && !defined(HORNET_ENGINE_STAGED_PROTOTYPE)
        if(observed[handle].path.has_engine)observed[handle].motion_attempted=true;
#endif
#ifdef HORNET_STAGED_PROTOTYPE
        observed[handle].token=staged_playback::fingerprint(std::filesystem::path(path).parent_path()/"recorded-flight.txt");
        if(!observed[handle].token)observed[handle].motion_attempted=true;
#endif
        if(std::string(status)!="recording_loaded")observed[handle].motion_attempted=true;
#if defined(HORNET_HELD_PROTOTYPE) || defined(HORNET_RELEASE_PROTOTYPE)
        const auto& loaded=observed[handle].path;
        if(!loaded.has_exterior || !loaded.has_engine || !loaded.has_lights ||
           !loaded.has_canopy || !loaded.has_wheels) {
            observed[handle].motion_attempted=true;
            record("held_snapshot_incomplete",handle,cookie,0,0);
        }
#endif
    } else observed[handle].motion_attempted=true;
#endif
}
extern "C" __declspec(dllexport) void ed_on_object_simulate(ED_OBJECT_HANDLE handle, uint64_t& cookie, double time) {
    std::lock_guard<std::mutex> guard(lock);
    const auto found=observed.find(handle);
    if(found==observed.end())return;
    auto& state = found->second;
    ++state.calls;
#ifdef HORNET_GROUND_TRACE
    trace_ground_pose("sdk_entry",handle,state);
#endif
#ifdef HORNET_STAGED_PROTOTYPE
    drain_engine(handle,state,time);
#endif
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
#ifdef HORNET_FORMATION_PROTOTYPE
    if(!state.assigned) {hold_unassigned(handle,state,motion_id,cookie,time);return;}
#endif
    if(state.path.has_exterior && state.motion_active && time-state.start_time>1 && state.exterior_applied==0) {
        state.motion_active=false;stop_native_step(handle,state);
        staged_playback::publish(api,handle,state.token,staged_playback::failed);
        record("exterior_callback_missing",handle,cookie,time,state.calls);return;
    }
#ifdef HORNET_RELEASE_PROTOTYPE
    const bool was_playing=state.clock.playing();
#ifdef HORNET_FAULT_INJECTION
    if(!state.clock.update(state.fault_clock?std::nan(""):time)) {
#else
    if(!state.clock.update(time)) {
#endif
        state.motion_active=false;state.motion_attempted=true;stop_native_step(handle,state);
        staged_playback::publish(api,handle,state.token,staged_playback::failed);
        record("release_clock_invalid",handle,cookie,time,state.calls);return;
    }
    if(!was_playing && state.clock.playing()) {
        state.start_time=time;
        record("release_epoch",handle,cookie,state.clock.epoch,state.calls);
        // A late first callback starts at its shared replay time, not zero.
        if(state.clock.shared)record("release_first_step",handle,cookie,time,state.calls);
    }
#endif
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
#ifdef HORNET_HELD_PROTOTYPE
    speedbrake=state.path.brake_at(0);
#endif
#ifdef HORNET_RELEASE_PROTOTYPE
    speedbrake=state.path.brake_at(state.clock.elapsed);
#endif
    state.snapshot_brake=speedbrake;
    if(state.path.has_exterior) {
#ifdef HORNET_SURFACE_PROTOTYPE
        // Replay time stops at the end of the take; a parked hold repeats the final sample.
        state.exterior_elapsed=std::min(state.clock.elapsed,state.path.duration());
#elif defined(HORNET_RELEASE_PROTOTYPE)
        state.exterior_elapsed=state.clock.elapsed;
#elif defined(HORNET_HELD_PROTOTYPE)
        state.exterior_elapsed=0;
#else
        state.exterior_elapsed=state.motion_active?time-state.start_time:0;
#endif
        const auto sampled=state.path.at_sample(state.exterior_elapsed);
        state.exterior=sampled.exterior;state.engine=sampled.engine;state.lights=sampled.lights;state.canopy=sampled.canopy;state.wheels=sampled.wheels;
#ifdef HORNET_SURFACE_PROTOTYPE
        // Takes have no length limit: replay seconds/100000 stays below 1 for 27 hours.
        api->ed_set_single_arg(handle,996,static_cast<float>(state.exterior_elapsed/100000));
#else
        api->ed_set_single_arg(handle,996,static_cast<float>(state.exterior_elapsed/1000));
#endif
        state.exterior_pending=hornet_appearance::apply_exterior(api,handle,state.runtime_id,state.exterior);
        if(state.path.has_engine)state.exterior_pending=hornet_appearance::apply_engine(api,handle,state.runtime_id,state.engine) && state.exterior_pending;
        if(state.path.has_lights)state.exterior_pending=hornet_appearance::apply_lights(api,handle,state.runtime_id,state.lights) && state.exterior_pending;
        if(state.path.has_wheels)state.exterior_pending=hornet_appearance::apply_wheels(api,handle,state.runtime_id,state.wheels) && state.exterior_pending;
        if(state.path.has_canopy)state.exterior_pending=hornet_appearance::apply_canopy(api,handle,state.runtime_id,state.canopy) && state.exterior_pending;
#ifdef HORNET_FAULT_INJECTION
        if(state.fault_state)state.exterior_pending=false;
#endif
        if(!state.exterior_pending) {
            state.motion_attempted=true;state.motion_active=false;stop_native_step(handle,state);
            staged_playback::publish(api,handle,state.token,staged_playback::failed);
            record("exterior_write_failed",handle,cookie,time,state.calls);return;
        }
    }
    const auto appearance_status=hornet_appearance::apply(api,handle,speedbrake,state.runtime_id,state.path.has_lights);
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
        motion_file << '\n'; flush_trace(motion_file);
    }
    if(state.motion_active) {
#ifdef HORNET_RELEASE_PROTOTYPE
        const double elapsed=state.clock.elapsed;
#elif defined(HORNET_HELD_PROTOTYPE)
        const double elapsed=held_start::replay_time(time,state.start_time);
#else
        const double elapsed=time-state.start_time;
#endif
#ifdef HORNET_RECORDED_PROTOTYPE
#ifdef HORNET_STAGED_PROTOTYPE
        const bool release=false; // Apply the endpoint before reporting completion.
        const bool finished=elapsed>=state.path.duration();
#ifdef HORNET_SURFACE_PROTOTYPE
        if(finished && !state.parked && state.path.ground_at(state.path.duration())) {
            state.parked=true;
            record("staged_parked",handle,cookie,time,state.calls);
        }
#endif
#else
        const bool release=elapsed>state.path.duration();
#endif
#else
        const bool release=elapsed>playback_path::duration;
#endif
        const auto target=state.path.at(elapsed);
#ifdef HORNET_SURFACE_PROTOTYPE
        const bool ground=state.path.ground_at(elapsed);
#else
        const bool ground=false;
#endif
#ifdef HORNET_SURFACE_PROTOTYPE
        const auto target_motion=surface_motion(state,elapsed);
        // Native step length over the last SDK interval, for extra-step restores.
        if(state.steps_since_sdk>0 && elapsed>state.last_sdk_elapsed)
            state.native_step_dt=std::clamp((elapsed-state.last_sdk_elapsed)/state.steps_since_sdk,0.005,0.1);
        state.last_sdk_elapsed=elapsed;state.steps_since_sdk=0;
#elif defined(HORNET_RELEASE_PROTOTYPE)
        const auto target_motion=state.clock.playing()?state.path.motion_at(elapsed):turn_path::Motion{};
#elif defined(HORNET_HELD_PROTOTYPE)
        const turn_path::Motion target_motion{};
#else
        const auto target_motion=state.path.motion_at(elapsed);
#endif
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
        const auto status=elapsed<0 ? "staged_clock_reversed" : native_motion::apply(handle,motion_id,before,after,&target,nullptr,false,&target_motion,state.runtime_id,ground);
#else
        const auto status=release ? "released" : native_motion::apply(handle,motion_id,before,after,&target,nullptr,false,match_motion ? &target_motion : nullptr);
#endif
#ifdef HORNET_RECORDED_PROTOTYPE
        if(!release && std::strcmp(status,"called")==0) {
            if(!state.step_hook) {
#ifdef HORNET_STAGED_PROTOTYPE
                state.step_status=install_native_step(handle,state.path.has_exterior,state.path.has_engine);
#else
                state.step_status=install_native_step(handle);
#endif
                state.step_hook=std::strcmp(state.step_status,"step_hook_installed")==0;
                record(state.step_status,handle,cookie,time,state.calls);
            }
            if(state.step_hook) {
                state.step_motion=target_motion; state.step_pending=true;
#ifdef HORNET_STAGED_PROTOTYPE
                if(state.path.has_engine && !native_step_hook::publish_engine(reinterpret_cast<uintptr_t>(handle)-8,state.engine)) {
                    state.motion_active=false;record("engine_publish_failed",handle,cookie,time,state.calls);
                }
#endif
            }
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
        motion_file << '\n'; flush_trace(motion_file);
        if(release || std::string(status)!="called") state.motion_active=false;
#ifdef HORNET_STAGED_PROTOTYPE
        if(state.motion_active) {
            state.exterior_finished=finished && state.path.has_exterior;
#ifdef HORNET_SURFACE_PROTOTYPE
            const auto phase=state.parked?staged_playback::parked:state.clock.playing()?staged_playback::running:(state.exterior_applied>0?held_start::status:0.0f);
#elif defined(HORNET_RELEASE_PROTOTYPE)
            const auto phase=state.clock.playing()?staged_playback::running:(state.exterior_applied>0?held_start::status:0.0f);
#elif defined(HORNET_HELD_PROTOTYPE)
            const auto phase=state.exterior_applied>0?held_start::status:0.0f;
#else
            const auto phase=finished && !state.path.has_exterior?staged_playback::complete:staged_playback::running;
#endif
            if(!staged_playback::publish(api,handle,state.token,phase)) {
                record("staged_status_readback_failed",handle,cookie,time,state.calls);
                state.motion_active=false;
            } else if(finished && !state.path.has_exterior) {
                state.terminal=true;state.motion_active=false;
                record("staged_complete",handle,cookie,time,state.calls);
            } else if(time==state.start_time)record("staged_started",handle,cookie,time,state.calls);
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
        flush_trace(body_file);
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
#ifdef HORNET_GROUND_TRACE
    // Read-only: which native path destroyed the object (module+RVA per frame).
    if(ai_phase_file) {
        void* frames[48]{};const auto n=RtlCaptureStackBackTrace(0,48,frames,nullptr);
        ai_phase_file<<"destroy_stack";
        for(USHORT i=0;i<n;++i) {
            HMODULE m=nullptr;wchar_t name[MAX_PATH]{};
            GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                reinterpret_cast<LPCWSTR>(frames[i]),&m);
            if(m)GetModuleFileNameW(m,name,MAX_PATH);
            ai_phase_file<<','<<std::filesystem::path(name).filename().string()<<"+0x"<<std::hex<<(reinterpret_cast<uintptr_t>(frames[i])-reinterpret_cast<uintptr_t>(m))<<std::dec;
        }
        ai_phase_file<<'\n';flush_trace(ai_phase_file);
    }
#endif
    observed.erase(handle);
}
static_assert(std::is_same_v<decltype(&ed_setup_object_api), PFN_ED_SETUP_OBJECT_API>);
static_assert(std::is_same_v<decltype(&ed_on_object_create), PFN_ED_ON_OBJECT_CREATE>);
static_assert(std::is_same_v<decltype(&ed_on_object_simulate), PFN_ED_ON_OBJECT_SIMULATE>);
static_assert(std::is_same_v<decltype(&ed_on_object_destroy), PFN_ED_ON_OBJECT_DESTROY>);
#ifdef HORNET_RELEASE_PROTOTYPE
#include "release-start/bridge.h"
#endif
