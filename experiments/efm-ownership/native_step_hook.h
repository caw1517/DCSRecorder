#pragma once
#include "native_identity.h"
#include <array>
#include <mutex>
#include <unordered_map>
#include <vector>
#include <intrin.h>
#include "hornet_engine.h"

// Experimental shadow table shared by every owned object of one aircraft type.
// The shared DCS table and executable pages are never modified. All slots and
// the RTTI locator are preserved except the verified physics step, optional
// animation and optional engine getter slots. Each owner restores only its own
// vptr; the first owner fixes the table and callbacks until the last one leaves.
// Storage lasts for the DLL lifetime.
namespace native_step_hook {
inline constexpr size_t slots=0xdf0/sizeof(uintptr_t);
inline constexpr size_t step_slot=0xc70/sizeof(uintptr_t);
inline constexpr size_t animation_slot=0xc10/sizeof(uintptr_t);
using Step=void(*)(void*);
using Animation=void(*)(void*,double,bool);
using Before=void(*)(const void*);
using RPM=float(*)(void*,int,bool);
using Scalar=float(*)(void*,int);
struct Engine {RPM rpm;Scalar thrust,power;};
struct EngineCall {uintptr_t caller;int engine,channel;bool overridden;float original,returned;};
// Per-object state: the owning simulation thread and its engine consumer values.
struct Owner {
    DWORD thread=0;
    bool engine_active=false;
    hornet_engine::Parameters engine_values{};
    std::vector<EngineCall> engine_calls;
    uint64_t engine_dropped=0;
};
inline std::mutex mutex;
inline std::array<uintptr_t,slots+1> shadow{};
inline std::unordered_map<uintptr_t,Owner> owners;
inline uintptr_t original_table=0;
inline Step original_step=nullptr;
inline Before before_step=nullptr;
inline Before after_step=nullptr;
inline Animation original_animation=nullptr;
inline Before after_animation=nullptr;
inline Engine engine_getters{};
inline bool engine_hooked=false;
// Owner state for `object` when called on its simulation thread; caller holds `mutex`.
inline Owner* on_thread(uintptr_t object) {
    const auto it=owners.find(object);
    return it!=owners.end() && it->second.thread==GetCurrentThreadId()?&it->second:nullptr;
}
inline uintptr_t table() { return reinterpret_cast<uintptr_t>(shadow.data()+1); }

inline bool recognizes(uintptr_t object,uintptr_t candidate,uintptr_t original) {
    std::lock_guard<std::mutex> guard(mutex);
    return owners.count(object) && candidate==table() && original_table==original;
}
inline void dispatch(void* object) {
    Step next=nullptr; Before before=nullptr;
    {
        std::lock_guard<std::mutex> guard(mutex);
        next=original_step;
        if(on_thread(reinterpret_cast<uintptr_t>(object)))before=before_step;
    }
    // Do not hold the hook lock across DCS or SDK callbacks.
    if(before) before(reinterpret_cast<const void*>(reinterpret_cast<uintptr_t>(object)+8));
    if(next) next(object);
    // Native work can destroy/replace ownership; reacquire before post-step work.
    Before after=nullptr;
    {
        std::lock_guard<std::mutex> guard(mutex);
        if(on_thread(reinterpret_cast<uintptr_t>(object)))after=after_step;
    }
    if(after) after(reinterpret_cast<const void*>(reinterpret_cast<uintptr_t>(object)+8));
}
inline void dispatch_animation(void* object,double dt,bool update) {
    Animation next=nullptr;
    { std::lock_guard<std::mutex> guard(mutex);next=original_animation; }
    if(next)next(object,dt,update);
    Before after=nullptr;
    {
        std::lock_guard<std::mutex> guard(mutex);
        if(on_thread(reinterpret_cast<uintptr_t>(object)))after=after_animation;
    }
    if(after)after(reinterpret_cast<const void*>(reinterpret_cast<uintptr_t>(object)+8));
}
inline bool writable_pointer(uintptr_t address) {
    MEMORY_BASIC_INFORMATION region{};
    return address%alignof(uintptr_t)==0 && VirtualQuery(reinterpret_cast<void*>(address),&region,sizeof(region)) &&
        region.State==MEM_COMMIT && !(region.Protect&(PAGE_GUARD|PAGE_NOACCESS)) &&
        (region.Protect&(PAGE_READWRITE|PAGE_WRITECOPY|PAGE_EXECUTE_READWRITE|PAGE_EXECUTE_WRITECOPY)) &&
        address+sizeof(uintptr_t)<=reinterpret_cast<uintptr_t>(region.BaseAddress)+region.RegionSize;
}
inline float engine_read(void* object,int engine,int channel,uintptr_t caller) {
    Engine originals{};float requested=0;bool replace=false,owned=false;
    const auto key=reinterpret_cast<uintptr_t>(object);
    {
        std::lock_guard<std::mutex> guard(mutex);
        originals=engine_getters;
        const auto it=owners.find(key);owned=it!=owners.end();
        replace=owned && it->second.engine_active && engine>=1 && engine<=2;
        if(replace)requested=it->second.engine_values[(engine-1)*3+channel];
    }
    const float actual=channel==2?(originals.thrust?originals.thrust(object,engine):0):
        (originals.rpm?originals.rpm(object,engine,channel==0):0);
    const float result=replace?requested:actual;
    if(owned) {
        std::lock_guard<std::mutex> guard(mutex);
        const auto it=owners.find(key);
        if(it!=owners.end()) {
            if(it->second.engine_calls.size()<8192)it->second.engine_calls.push_back({caller,engine,channel,replace,actual,result});
            else ++it->second.engine_dropped;
        }
    }
    return result;
}
__declspec(noinline) inline float dispatch_rpm(void* object,int engine,bool core) {
    return engine_read(object,engine,core?0:1,reinterpret_cast<uintptr_t>(_ReturnAddress()));
}
__declspec(noinline) inline float dispatch_thrust(void* object,int engine) {
    return engine_read(object,engine,2,reinterpret_cast<uintptr_t>(_ReturnAddress()));
}
inline bool publish_engine(uintptr_t object,const hornet_engine::Values& values) {
    std::lock_guard<std::mutex> guard(mutex);uintptr_t current=0;
    const auto it=owners.find(object);
    if(it==owners.end())return false;
    auto& owner=it->second;
    if(owner.thread!=GetCurrentThreadId() || !engine_getters.rpm ||
       !hornet_engine::valid(values) || !native_identity::read(object,current) || current!=table()) {
        owner.engine_active=false;return false;
    }
    owner.engine_values=hornet_engine::parameters(values);owner.engine_active=true;return true;
}
// One owner's engine getter trace since its last drain.
inline std::vector<EngineCall> drain_engine(uintptr_t object,uint64_t& lost) {
    std::lock_guard<std::mutex> guard(mutex);std::vector<EngineCall> result;lost=0;
    const auto it=owners.find(object);
    if(it!=owners.end()) {result.swap(it->second.engine_calls);lost=it->second.engine_dropped;it->second.engine_dropped=0;}
    return result;
}
// Every owner's trace together.
inline std::vector<EngineCall> drain_engine(uint64_t& lost) {
    std::lock_guard<std::mutex> guard(mutex);std::vector<EngineCall> result;lost=0;
    for(auto& entry:owners) {
        auto& owner=entry.second;
        result.insert(result.end(),owner.engine_calls.begin(),owner.engine_calls.end());
        owner.engine_calls.clear();lost+=owner.engine_dropped;owner.engine_dropped=0;
    }
    return result;
}
// Caller first verifies aircraft identity, runtime ID, null FM, altitude, motion
// bounds, and this DCS build's table boundary, integrator, and callsite bytes.
inline const char* install(uintptr_t object,uintptr_t expected_table,Step expected_step,Before before,Before after=nullptr,
                           Animation animation=nullptr,Before animation_after=nullptr,const Engine* engine=nullptr) {
    std::lock_guard<std::mutex> guard(mutex);
    if(owners.count(object)) return "step_hook_busy";
    uintptr_t current=0;
    if(!object || (!before && !after) || !expected_step || !writable_pointer(object) ||
       !native_identity::read(object,current) || current!=expected_table)
        return "step_hook_object_rejected";
    if(!owners.empty()) {
        // Later owners join the table the first owner built. A different layout,
        // callback set or getter set is refused, never rebuilt under live owners.
        const Engine none{};const auto& wanted=engine?*engine:none;
        if(expected_table!=original_table || expected_step!=original_step || before!=before_step || after!=after_step ||
           animation!=original_animation || animation_after!=after_animation || bool(engine)!=engine_hooked ||
           wanted.rpm!=engine_getters.rpm || wanted.thrust!=engine_getters.thrust || wanted.power!=engine_getters.power)
            return "step_hook_config_conflict";
    } else {
        std::array<uintptr_t,slots+1> copy{};
        if(!native_identity::read(expected_table-sizeof(uintptr_t),copy) ||
           copy[step_slot+1]!=reinterpret_cast<uintptr_t>(expected_step)) return "step_hook_table_rejected";
        if(bool(animation)!=bool(animation_after) ||
           (animation && copy[animation_slot+1]!=reinterpret_cast<uintptr_t>(animation)))return "animation_hook_table_rejected";
        if(engine && (!engine->rpm || !engine->thrust || !engine->power || !animation ||
           copy[0xd8/8+1]!=reinterpret_cast<uintptr_t>(engine->rpm) ||
           copy[0xe0/8+1]!=reinterpret_cast<uintptr_t>(engine->thrust) ||
           copy[0xf0/8+1]!=reinterpret_cast<uintptr_t>(engine->power)))return "engine_hook_table_rejected";
        shadow=copy;
        shadow[step_slot+1]=reinterpret_cast<uintptr_t>(&dispatch);
        if(animation)shadow[animation_slot+1]=reinterpret_cast<uintptr_t>(&dispatch_animation);
        engine_getters=engine?*engine:Engine{};engine_hooked=bool(engine);
        if(engine) {
            shadow[0xd8/8+1]=reinterpret_cast<uintptr_t>(&dispatch_rpm);
            shadow[0xe0/8+1]=reinterpret_cast<uintptr_t>(&dispatch_thrust);
        }
        original_animation=animation;after_animation=animation_after;
        original_step=expected_step; before_step=before; after_step=after; original_table=expected_table;
    }
    owners[object].thread=GetCurrentThreadId();
    const auto prior=InterlockedCompareExchangePointer(reinterpret_cast<void* volatile*>(object),
        reinterpret_cast<void*>(table()),reinterpret_cast<void*>(expected_table));
    if(reinterpret_cast<uintptr_t>(prior)!=expected_table) {
        owners.erase(object);return "step_hook_install_raced";
    }
    return "step_hook_installed";
}
inline const char* restore(uintptr_t object) {
    std::lock_guard<std::mutex> guard(mutex);
    if(owners.empty()) return "step_hook_inactive";
    const auto it=owners.find(object);
    if(it==owners.end() || it->second.thread!=GetCurrentThreadId()) return "step_hook_restore_owner_rejected";
    // Leaving the owner set stops this object's callbacks and engine override.
    owners.erase(it);
    if(!writable_pointer(object)) return "step_hook_restore_unwritable";
    const auto prior=InterlockedCompareExchangePointer(reinterpret_cast<void* volatile*>(object),
        reinterpret_cast<void*>(original_table),reinterpret_cast<void*>(table()));
    // Destruction can replace the vptr before the SDK destroy callback. Never
    // overwrite a table we do not own; the shadow then has no live owner.
    return reinterpret_cast<uintptr_t>(prior)==table() ? "step_hook_restored" : "step_hook_already_replaced";
}
}
