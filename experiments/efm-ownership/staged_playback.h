#pragma once
#include <cstdint>
#include <cstddef>
#include <filesystem>
#include <fstream>
#include "ed_object_access.h"

// Experimental transport on this dedicated custom aircraft only. Never write
// outside the SDK argument view. Live mission-side visibility is a test gate.
namespace staged_playback {
inline constexpr int token_high_arg=997,token_low_arg=998,status_arg=999;
inline constexpr float running=0.25f,complete=0.5f,failed=0.75f;
// Surface controller only: a grounded ending held at its final pose and state.
inline constexpr float parked=0.375f;
inline uint64_t fingerprint(const std::filesystem::path& path) {
    std::ifstream file(path,std::ios::binary);
    if(!file)return 0;
    uint64_t value=14695981039346656037ull;
    char c;while(file.get(c)) {value^=static_cast<unsigned char>(c);value*=1099511628211ull;}
    return file.bad()?0:value;
}
inline float high(uint64_t value) {return static_cast<float>((value>>40)&0xffffff)/16777216.0f;}
inline float low(uint64_t value) {return static_cast<float>(value&0xffffff)/16777216.0f;}
inline bool available(const ed_object_api_entry* api,ED_OBJECT_HANDLE handle) {
    if(!api || !api->ed_get_object_args || !api->ed_set_single_arg)return false;
    const auto args=api->ed_get_object_args(handle);
    return args.data && args.size>status_arg;
}
inline bool publish(const ed_object_api_entry* api,ED_OBJECT_HANDLE handle,uint64_t token,float status) {
    if(!token || !available(api,handle))return false;
    api->ed_set_single_arg(handle,token_high_arg,high(token));
    api->ed_set_single_arg(handle,token_low_arg,low(token));
    api->ed_set_single_arg(handle,status_arg,status);
    const auto args=api->ed_get_object_args(handle);
    return args.data && args.size>status_arg && args.data[token_high_arg]==high(token) &&
        args.data[token_low_arg]==low(token) && args.data[status_arg]==status;
}
}
