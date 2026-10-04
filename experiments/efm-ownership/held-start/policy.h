#pragma once
#include "../turn_path.h"

// Isolated hold-only experiment. No release transition and no tape resampling
// against elapsed mission time. Airborne tape-reader guards remain unchanged.
namespace held_start {
inline double replay_time(double now, double epoch) {
    return std::isfinite(now) && std::isfinite(epoch) && now>=epoch ? 0.0 : -1.0;
}
inline bool stationary(const turn_path::Motion& motion) {
    return motion.velocity==std::array<float,3>{} && motion.angular==std::array<float,3>{};
}
inline constexpr float status=0.125f;
}
