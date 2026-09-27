#pragma once
// THROWAWAY: one aircraft's outward-facing core-RPM getter, not its engine physics.
#include "../native_animation_hook.h"
#include <intrin.h>
#include <vector>
#include <cmath>

namespace rpm_hook {
using Getter=float(*)(void*,int,bool);
constexpr size_t slot=0xd8/sizeof(uintptr_t),slots=native_animation_hook::slots;
struct Call {uintptr_t caller;int engine;bool core,overridden;float original,returned;};
inline std::mutex mutex;
inline std::array<uintptr_t,slots+1> shadow{};
inline uintptr_t owner=0,original_table=0;
inline Getter original=nullptr;
inline DWORD owner_thread=0;
inline bool active=false;
inline std::array<float,2> requested{};
inline std::vector<Call> calls;
inline uint64_t dropped=0;
inline uintptr_t table(){return reinterpret_cast<uintptr_t>(shadow.data()+1);}

__declspec(noinline) inline float dispatch(void* object,int engine,bool core) {
    const auto caller=reinterpret_cast<uintptr_t>(_ReturnAddress());
    Getter next=nullptr;bool owned=false,replace=false;float value=0;
    {
        std::lock_guard<std::mutex> held(mutex);
        next=original;owned=owner==reinterpret_cast<uintptr_t>(object) && owner!=0;
        replace=owned && active && core && engine>=1 && engine<=2;
        if(replace)value=requested[engine-1];
    }
    // Never hold our lock across native code. Original arguments are preserved.
    const float actual=next?next(object,engine,core):0;
    const float result=replace?value:actual;
    if(owned) {
        std::lock_guard<std::mutex> held(mutex);
        if(owner==reinterpret_cast<uintptr_t>(object)) {
            if(calls.size()<4096)calls.push_back({caller,engine,core,replace,actual,result});
            else ++dropped;
        }
    }
    return result;
}
inline const char* install(uintptr_t object,uintptr_t expected_table,Getter getter) {
    std::lock_guard<std::mutex> held(mutex);
    if(owner)return "rpm_hook_busy";
    uintptr_t current=0;
    if(!object || !getter || !native_animation_hook::writable_pointer(object) ||
       !native_identity::read(object,current) || current!=expected_table)return "rpm_object_rejected";
    std::array<uintptr_t,slots+1> copy{};
    if(!native_identity::read(expected_table-sizeof(uintptr_t),copy) ||
       copy[slot+1]!=reinterpret_cast<uintptr_t>(getter))return "rpm_table_rejected";
    shadow=copy;shadow[slot+1]=reinterpret_cast<uintptr_t>(&dispatch);
    original=getter;original_table=expected_table;owner_thread=GetCurrentThreadId();
    active=false;owner=object;calls.clear();dropped=0;
    const auto previous=InterlockedCompareExchangePointer(reinterpret_cast<void* volatile*>(object),
        reinterpret_cast<void*>(table()),reinterpret_cast<void*>(expected_table));
    if(reinterpret_cast<uintptr_t>(previous)!=expected_table){owner=0;return "rpm_install_raced";}
    return "rpm_hook_installed";
}
inline bool publish(uintptr_t object,bool enabled,float left=0,float right=0) {
    std::lock_guard<std::mutex> held(mutex);
    if(!owner || owner!=object || owner_thread!=GetCurrentThreadId())return false;
    uintptr_t current=0;
    if(!native_identity::read(object,current) || current!=table()) {active=false;return false;}
    if(enabled && (!std::isfinite(left) || !std::isfinite(right) || left<0 || right<0 || left>1.1f || right>1.1f)) {
        active=false;return false;
    }
    requested={left,right};active=enabled;return true;
}
inline std::vector<Call> drain(uint64_t& lost) {
    std::lock_guard<std::mutex> held(mutex);
    std::vector<Call> result;result.swap(calls);lost=dropped;dropped=0;return result;
}
inline const char* restore(uintptr_t object) {
    std::lock_guard<std::mutex> held(mutex);
    if(!owner)return "rpm_hook_inactive";
    if(owner!=object)return "rpm_restore_owner_rejected";
    active=false;
    if(owner_thread!=GetCurrentThreadId())return "rpm_restore_thread_rejected";
    if(!native_animation_hook::writable_pointer(object))return "rpm_restore_unwritable";
    const auto previous=InterlockedCompareExchangePointer(reinterpret_cast<void* volatile*>(object),
        reinterpret_cast<void*>(original_table),reinterpret_cast<void*>(table()));
    owner=0;
    // Retain the original function for any dispatcher already in flight.
    return reinterpret_cast<uintptr_t>(previous)==table()?"rpm_hook_restored":"rpm_hook_already_replaced";
}
}
