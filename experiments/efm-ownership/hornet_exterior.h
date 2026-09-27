#pragma once
#include <array>
#include <cmath>
#include <cstdint>
#include <cstddef>

namespace hornet_exterior {
inline constexpr const char* profile="hornet-exterior-v1";
inline constexpr std::array<int,13> channels{0,3,5,9,10,11,12,13,14,15,16,17,18};
using Values=std::array<double,channels.size()>;
inline bool valid(const Values& values) {
    for(size_t i=0;i<values.size();++i)
        if(!std::isfinite(values[i]) || values[i]<(i<3?0:-1) || values[i]>1)return false;
    return true;
}
}
