#pragma once
#include "native_identity.h"
#include <array>
#include <mutex>

// Experimental, single-object shadow table. The shared DCS table and executable
// pages are never modified. All slots and the RTTI locator are preserved except
// the verified void animation_update(this, double dt, bool update) slot. Storage lasts for the DLL lifetime.
namespace native_animation_hook {
inline constexpr size_t slots=0xdf0/sizeof(uintptr_t);
inline constexpr size_t step_slot=0xc10/sizeof(uintptr_t);
using Step=void(*)(void*,double,bool);
using Before=void(*)(const void*);
inline std::mutex mutex;
inline std::array<uintptr_t,slots+1> shadow{};
inline uintptr_t owner=0,original_table=0;
inline Step original_step=nullptr;
inline Before before_step=nullptr;
inline Before after_step=nullptr;
inline DWORD owner_thread=0;
inline uintptr_t table() { return reinterpret_cast<uintptr_t>(shadow.data()+1); }

inline bool recognizes(uintptr_t object,uintptr_t candidate,uintptr_t original) {
    std::lock_guard<std::mutex> guard(mutex);
    return owner==object && candidate==table() && original_table==original;
}
inline void dispatch(void* object,double dt,bool update) {
    Step next=nullptr; Before before=nullptr;
    {
        std::lock_guard<std::mutex> guard(mutex);
        next=original_step;
        if(owner==reinterpret_cast<uintptr_t>(object) && owner_thread==GetCurrentThreadId())
            before=before_step;
    }
    // Do not hold the hook lock across DCS or SDK callbacks.
    if(before) before(reinterpret_cast<const void*>(reinterpret_cast<uintptr_t>(object)+8));
    if(next) next(object,dt,update);
    // Native work can destroy/replace ownership; reacquire before post-animation work.
    Before after=nullptr;
    {
        std::lock_guard<std::mutex> guard(mutex);
        if(owner==reinterpret_cast<uintptr_t>(object) && owner_thread==GetCurrentThreadId())
            after=after_step;
    }
    if(after) after(reinterpret_cast<const void*>(reinterpret_cast<uintptr_t>(object)+8));
}
inline bool writable_pointer(uintptr_t address) {
    MEMORY_BASIC_INFORMATION region{};
    return address%alignof(uintptr_t)==0 && VirtualQuery(reinterpret_cast<void*>(address),&region,sizeof(region)) &&
        region.State==MEM_COMMIT && !(region.Protect&(PAGE_GUARD|PAGE_NOACCESS)) &&
        (region.Protect&(PAGE_READWRITE|PAGE_WRITECOPY|PAGE_EXECUTE_READWRITE|PAGE_EXECUTE_WRITECOPY)) &&
        address+sizeof(uintptr_t)<=reinterpret_cast<uintptr_t>(region.BaseAddress)+region.RegionSize;
}
// Caller verifies aircraft identity, runtime ID, null FM, and this DCS build's
// table boundary, animation entry, and callsite bytes before installation.
inline const char* install(uintptr_t object,uintptr_t expected_table,Step expected_step,Before before,Before after=nullptr) {
    std::lock_guard<std::mutex> guard(mutex);
    if(owner) return "animation_hook_busy";
    uintptr_t current=0;
    if(!object || (!before && !after) || !expected_step || !writable_pointer(object) ||
       !native_identity::read(object,current) || current!=expected_table)
        return "animation_hook_object_rejected";
    std::array<uintptr_t,slots+1> copy{};
    if(!native_identity::read(expected_table-sizeof(uintptr_t),copy) ||
       copy[step_slot+1]!=reinterpret_cast<uintptr_t>(expected_step)) return "animation_hook_table_rejected";
    shadow=copy;
    shadow[step_slot+1]=reinterpret_cast<uintptr_t>(&dispatch);
    original_step=expected_step; before_step=before; after_step=after; original_table=expected_table;
    owner_thread=GetCurrentThreadId(); owner=object;
    const auto prior=InterlockedCompareExchangePointer(reinterpret_cast<void* volatile*>(object),
        reinterpret_cast<void*>(table()),reinterpret_cast<void*>(expected_table));
    if(reinterpret_cast<uintptr_t>(prior)!=expected_table) {
        owner=0; before_step=nullptr; after_step=nullptr; return "animation_hook_install_raced";
    }
    return "animation_hook_installed";
}
inline const char* restore(uintptr_t object) {
    std::lock_guard<std::mutex> guard(mutex);
    if(!owner) return "animation_hook_inactive";
    if(owner!=object || owner_thread!=GetCurrentThreadId()) return "animation_hook_restore_owner_rejected";
    before_step=nullptr;
    after_step=nullptr;
    if(!writable_pointer(object)) return "animation_hook_restore_unwritable";
    const auto prior=InterlockedCompareExchangePointer(reinterpret_cast<void* volatile*>(object),
        reinterpret_cast<void*>(original_table),reinterpret_cast<void*>(table()));
    // Destruction can replace the vptr before the SDK destroy callback. Never
    // overwrite a table we do not own; the shadow then has no live owner.
    owner=0;
    return reinterpret_cast<uintptr_t>(prior)==table() ? "animation_hook_restored" : "animation_hook_already_replaced";
}
}
