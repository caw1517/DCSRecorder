// Generated from candidate_profile.json after static and read-only live checks.
// This profile is enabled only for explicit new-build trial targets.
#pragma once
#include <array>
#include <cstdint>
namespace native_build {
constexpr uintptr_t dcs(uintptr_t legacy) {
#ifdef DCSR_BUILD_2930
    switch(legacy) {
    case 0x7105f7: return 0x711e17;
    case 0x711152: return 0x712972;
    case 0x1146200: return 0x1149210;
    case 0x712408: return 0x713c28;
    case 0x712411: return 0x713c31;
    case 0x712435: return 0x713c55;
    case 0x6d41eb: return 0x6d4a0b;
    case 0x6d41f6: return 0x6d4a16;
    case 0x11461f8: return 0x1149208;
    case 0x133b650: return 0x133e7d0;
    case 0x1146ff0: return 0x114a000;
    case 0x133b770: return 0x133e8f0;
    case 0x70fef0: return 0x711710;
    case 0x675279: return 0x675529;
    case 0x66d160: return 0x66d3f0;
    case 0x66d1c0: return 0x66d450;
    case 0x60f110: return 0x60f240;
    case 0x6b6070: return 0x6b6480;
    case 0x67529c: return 0x67554c;
    case 0x6b73a7: return 0x6b77b7;
    case 0x641492: return 0x641702;
    case 0x6414a2: return 0x641712;
    case 0x6414b4: return 0x641724;
    case 0x6099af: return 0x609adf;
    case 0x6099d1: return 0x609b01;
    case 0x66d164: return 0x66d3f4;
    case 0x66d174: return 0x66d404;
    case 0x66d180: return 0x66d410;
    case 0x66d197: return 0x66d427;
    case 0x66d1b3: return 0x66d443;
    case 0x65a1a3: return 0x65a433;
    case 0x65a1f6: return 0x65a486;
    case 0x65eae8: return 0x65ed78;
    default: return 0; // Unknown address fails the caller's byte guard.
    }
#else
    return legacy;
#endif
}
constexpr uintptr_t world(uintptr_t legacy) {
#ifdef DCSR_BUILD_2930
    switch(legacy) {
    case 0x68d50: return 0x685e0;
    case 0x69310: return 0x68b90;
    case 0x69390: return 0x68c10;
    case 0x6a9ff: return 0x6a27f;
    case 0x6aa44: return 0x6a2c4;
    default: return 0; // Unknown address fails the caller's byte guard.
    }
#else
    return legacy;
#endif
}
#ifdef DCSR_BUILD_2930
inline constexpr uintptr_t pitch_offset=0x4dcc;
inline constexpr unsigned char pitch_displacement_low=0xcc;
inline constexpr std::array<unsigned char,5> animation_writer={0xe8,0xc4,0x1d,0xfb,0xff};
#else
inline constexpr uintptr_t pitch_offset=0x4db4;
inline constexpr unsigned char pitch_displacement_low=0xb4;
inline constexpr std::array<unsigned char,5> animation_writer={0xe8,0x44,0x1f,0xfb,0xff};
#endif
}
