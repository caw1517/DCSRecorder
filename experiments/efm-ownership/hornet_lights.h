#pragma once
#include <array>
#include <cmath>
namespace hornet_lights {
inline constexpr const char* profile="hornet-lights-v1";
inline constexpr std::array<int,7> channels{88,190,191,192,193,210,212};
using Values=std::array<double,7>;
inline bool valid(const Values& values) {
    for(double v:values)if(!std::isfinite(v) || v<0 || v>1)return false;
    return true;
}
}
