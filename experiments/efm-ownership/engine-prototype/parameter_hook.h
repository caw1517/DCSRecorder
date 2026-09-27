#pragma once
// THROWAWAY: measured core/fan RPM and thrust, through one aircraft's getters.
#include "../native_animation_hook.h"
#include <intrin.h>
#include <vector>
#include <cmath>

namespace parameter_hook {
using Getter=float(*)(void*,int,bool);
using Thrust=float(*)(void*,int);
constexpr size_t slot=0xd8/8,thrust_slot=0xe0/8,power_slot=0xf0/8,slots=native_animation_hook::slots;
using Values=std::array<float,6>; // core1, fan1, thrust1, core2, fan2, thrust2
struct Call {uintptr_t caller;int engine,channel;bool overridden;float original,returned;};
inline std::mutex mutex;
inline std::array<uintptr_t,slots+1> shadow{};
inline uintptr_t owner=0,original_table=0;
inline Getter original=nullptr;
inline Thrust original_thrust=nullptr;
inline DWORD owner_thread=0;
inline bool active=false;
inline Values requested{};
inline std::vector<Call> calls;
inline uint64_t dropped=0;
using Animation=native_animation_hook::Step;
using AfterAnimation=native_animation_hook::Before;
inline Animation original_animation=nullptr;
inline AfterAnimation after_animation=nullptr;
inline uintptr_t table(){return reinterpret_cast<uintptr_t>(shadow.data()+1);}
inline bool valid(const Values& values) {
    for(size_t i=0;i<values.size();++i)
        if(!std::isfinite(values[i]) || values[i]<0 || values[i]>(i%3==2?4.0f:1.2f))return false;
    return true;
}
inline float run(void* object,int engine,int channel,bool core,uintptr_t caller) {
    Getter next=nullptr;Thrust thrust=nullptr;bool owned=false,replace=false;float value=0;
    {
        std::lock_guard<std::mutex> held(mutex);
        next=original;thrust=original_thrust;owned=owner==reinterpret_cast<uintptr_t>(object) && owner!=0;
        replace=owned && active && engine>=1 && engine<=2;
        if(replace)value=requested[(engine-1)*3+channel];
    }
    // Original thrust reads the native engine directly. The separate F0 getter
    // is an unchanged, guarded tail-forwarder to E0, so both consumers reach us.
    const float actual=channel==2?(thrust?thrust(object,engine):0):(next?next(object,engine,core):0);
    const float result=replace?value:actual;
    if(owned) {
        std::lock_guard<std::mutex> held(mutex);
        if(owner==reinterpret_cast<uintptr_t>(object)) {
            if(calls.size()<8192)calls.push_back({caller,engine,channel,replace,actual,result});
            else ++dropped;
        }
    }
    return result;
}
__declspec(noinline) inline float dispatch(void* object,int engine,bool core) {
    return run(object,engine,core?0:1,core,reinterpret_cast<uintptr_t>(_ReturnAddress()));
}
__declspec(noinline) inline float dispatch_thrust(void* object,int engine) {
    return run(object,engine,2,false,reinterpret_cast<uintptr_t>(_ReturnAddress()));
}
inline void dispatch_animation(void* object,double dt,bool update) {
    Animation next=nullptr;
    {std::lock_guard<std::mutex> held(mutex);next=original_animation;}
    if(next)next(object,dt,update);
    AfterAnimation after=nullptr;
    {
        std::lock_guard<std::mutex> held(mutex);
        uintptr_t current=0;
        if(active && owner==reinterpret_cast<uintptr_t>(object) && owner_thread==GetCurrentThreadId() &&
           native_identity::read(owner,current) && current==table())after=after_animation;
    }
    if(after)after(reinterpret_cast<const void*>(reinterpret_cast<uintptr_t>(object)+8));
}
inline const char* install(uintptr_t object,uintptr_t expected_table,Getter getter,Thrust thrust,Thrust power,
                          Animation animation=nullptr,AfterAnimation after=nullptr) {
    std::lock_guard<std::mutex> held(mutex);
    if(owner)return "parameter_hook_busy";
    uintptr_t current=0;
    if(!object || !getter || !thrust || !power || bool(animation)!=bool(after) || !native_animation_hook::writable_pointer(object) ||
       !native_identity::read(object,current) || current!=expected_table)return "parameter_object_rejected";
    std::array<uintptr_t,slots+1> copy{};
    if(!native_identity::read(expected_table-sizeof(uintptr_t),copy) ||
       copy[slot+1]!=reinterpret_cast<uintptr_t>(getter) ||
       copy[thrust_slot+1]!=reinterpret_cast<uintptr_t>(thrust) ||
       copy[power_slot+1]!=reinterpret_cast<uintptr_t>(power) ||
       (animation && copy[native_animation_hook::step_slot+1]!=reinterpret_cast<uintptr_t>(animation)))return "parameter_table_rejected";
    shadow=copy;shadow[slot+1]=reinterpret_cast<uintptr_t>(&dispatch);
    shadow[thrust_slot+1]=reinterpret_cast<uintptr_t>(&dispatch_thrust);
    original_animation=animation;after_animation=after;
    if(animation)shadow[native_animation_hook::step_slot+1]=reinterpret_cast<uintptr_t>(&dispatch_animation);
    original=getter;original_thrust=thrust;original_table=expected_table;owner_thread=GetCurrentThreadId();
    active=false;owner=object;calls.clear();dropped=0;
    const auto previous=InterlockedCompareExchangePointer(reinterpret_cast<void* volatile*>(object),
        reinterpret_cast<void*>(table()),reinterpret_cast<void*>(expected_table));
    if(reinterpret_cast<uintptr_t>(previous)!=expected_table){owner=0;return "parameter_install_raced";}
    return "parameter_hook_installed";
}
inline bool publish(uintptr_t object,bool enabled,const Values& values={}) {
    std::lock_guard<std::mutex> held(mutex);
    if(!owner || owner!=object || owner_thread!=GetCurrentThreadId())return false;
    uintptr_t current=0;
    if(!native_identity::read(object,current) || current!=table()) {active=false;return false;}
    if(enabled && !valid(values)){active=false;return false;}
    requested=values;active=enabled;return true;
}
inline std::vector<Call> drain(uint64_t& lost) {
    std::lock_guard<std::mutex> held(mutex);
    std::vector<Call> result;result.swap(calls);lost=dropped;dropped=0;return result;
}
inline const char* restore(uintptr_t object) {
    std::lock_guard<std::mutex> held(mutex);
    if(!owner)return "parameter_hook_inactive";
    if(owner!=object)return "parameter_restore_owner_rejected";
    active=false;
    if(owner_thread!=GetCurrentThreadId())return "parameter_restore_thread_rejected";
    if(!native_animation_hook::writable_pointer(object))return "parameter_restore_unwritable";
    const auto previous=InterlockedCompareExchangePointer(reinterpret_cast<void* volatile*>(object),
        reinterpret_cast<void*>(original_table),reinterpret_cast<void*>(table()));
    owner=0;
    return reinterpret_cast<uintptr_t>(previous)==table()?"parameter_hook_restored":"parameter_hook_already_replaced";
}
}
