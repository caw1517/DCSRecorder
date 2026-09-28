#pragma once
#include <cmath>

namespace hornet_canopy {
constexpr const char* profile="hornet-canopy-v1";
constexpr int channel=38;
inline bool valid(double value) {return std::isfinite(value) && value>=0 && value<=1;}
}
