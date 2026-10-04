"""Emit a compile-time profile for the explicit new-build trials only."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
p=json.loads((HERE/'candidate_profile.json').read_text())
lines=['// Generated from candidate_profile.json after static and read-only live checks.',
       '// This profile is enabled only for explicit new-build trial targets.',
       '#pragma once','#include <array>','#include <cstdint>','namespace native_build {']
for module,func in [('dcs','dcs'),('worldgeneral','world')]:
    lines += [f'constexpr uintptr_t {func}(uintptr_t legacy) {{','#ifdef DCSR_BUILD_2930','    switch(legacy) {']
    lines += [f'    case {old}: return {new};' for old,new in p[module].items()]
    lines += ['    default: return 0; // Unknown address fails the caller\'s byte guard.','    }','#else','    return legacy;','#endif','}']
lines += ['#ifdef DCSR_BUILD_2930',f'inline constexpr uintptr_t pitch_offset={p["presentation_pitch_member"]};',
          'inline constexpr unsigned char pitch_displacement_low=0xcc;',
          'inline constexpr std::array<unsigned char,5> animation_writer={0xe8,0xc4,0x1d,0xfb,0xff};',
          '#else','inline constexpr uintptr_t pitch_offset=0x4db4;',
          'inline constexpr unsigned char pitch_displacement_low=0xb4;',
          'inline constexpr std::array<unsigned char,5> animation_writer={0xe8,0x44,0x1f,0xfb,0xff};','#endif','}']
(HERE.parent/'native_build.h').write_text('\n'.join(lines)+'\n')
