#pragma once
#include "engine-prototype/sound_boundary.h"
namespace engine_native_layout {
inline bool valid() {
    const auto image=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    const auto world=reinterpret_cast<uintptr_t>(GetModuleHandleW(L"WorldGeneral.dll"));
    const auto sound=reinterpret_cast<uintptr_t>(GetModuleHandleW(L"Sound.dll"));
    return sound && sound_boundary::layout_matches(image,world) &&
        sound_boundary::matches(sound+0x13d430,std::array<unsigned char,18>{0x48,0x8b,0x4b,0x40,0x41,0xb0,1,0x8b,0xd7,0x48,0x8b,1,0xff,0x90,0xd8,0,0,0}) &&
        sound_boundary::matches(image+0x60f110,std::array<unsigned char,10>{0x48,0x8b,1,0x48,0xff,0xa0,0xe0,0,0,0}) &&
        sound_boundary::matches(image+0x66d1c0,std::array<unsigned char,14>{0x85,0xd2,0x7e,0x21,0x0f,0xb6,0x81,0x11,8,0,0,0x3b,0xd0,0x7f}) &&
        sound_boundary::matches(sound+0x134cbb,std::array<unsigned char,6>{0xff,0x90,0xe0,0,0,0}) &&
        sound_boundary::matches(sound+0x134ca5,std::array<unsigned char,6>{0xff,0x90,0xf0,0,0,0});
}
}
