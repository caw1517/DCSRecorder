#pragma once
#include <cstdint>
#include <cstddef>
#include "ed_object_access.h"

namespace hornet_appearance {
// Prototype defaults, not recorded-flight animation playback. SDK callbacks
// are scoped to our declared aircraft; retain the single-object experiment ID.
// Hornet lights: installed FA-18C descriptor. Speed brake: exterior argument 21.
constexpr int off_arguments[]={21,88,190,191,192,193,210,212};
inline const char* apply(const ed_object_api_entry* api,ED_OBJECT_HANDLE handle,float speedbrake=0) {
    if(!handle || !api || !api->ed_get_object_id || !api->ed_get_object_args || !api->ed_set_single_arg)
        return "api_unavailable";
    if(api->ed_get_object_id(handle)!=16777472) return "wrong_object";
    const auto args=api->ed_get_object_args(handle);
    if(!args.data || args.size<=212) return "arguments_unavailable";
    if(!(speedbrake>=0 && speedbrake<=1)) return "animation_rejected";
    for(int index:off_arguments) api->ed_set_single_arg(handle,index,index==21?speedbrake:0.0f);
    const auto after=api->ed_get_object_args(handle);
    if(!after.data || after.size<=212) return "readback_unavailable";
    for(int index:off_arguments) if(after.data[index]!=(index==21?speedbrake:0.0f)) return "readback_mismatch";
    return speedbrake==0?"off_verified":"recorded_brake_verified";
}
}
