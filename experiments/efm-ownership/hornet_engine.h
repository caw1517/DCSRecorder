#pragma once
#include <array>
#include <cmath>
namespace hornet_engine {
inline constexpr const char* profile="hornet-native-engine-v1";
inline constexpr std::array<int,4> channels{28,29,89,90};
// Tape order: four appearance arguments, then core/fan/power for each engine.
using Values=std::array<double,10>;
using Parameters=std::array<float,6>;
inline bool valid(const Values& values) {
    for(size_t i=0;i<values.size();++i) {
        const double maximum=i<4?1.0:((i-4)%3==2?4.0:1.2);
        if(!std::isfinite(values[i]) || values[i]<0 || values[i]>maximum)return false;
    }
    return true;
}
inline Parameters parameters(const Values& values) {
    Parameters result{};for(size_t i=0;i<6;++i)result[i]=static_cast<float>(values[i+4]);return result;
}
}
