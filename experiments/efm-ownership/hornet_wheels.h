#pragma once
#include <array>
#include <cmath>

namespace hornet_wheels {
constexpr const char* profile="hornet-wheels-v1";
constexpr std::array<int,7> channels{1,6,4,101,103,102,2};
using Values=std::array<double,7>;
inline bool valid(const Values& values) {
    for(size_t i=0;i<values.size();++i)
        if(!std::isfinite(values[i]) || values[i]<(i==6?-1.0:0.0) || values[i]>1)return false;
    return true;
}
inline Values interpolate(const Values& a,const Values& b,double u) {
    Values result{};
    for(size_t i=0;i<result.size();++i) {
        if(u<=1e-9 || a[i]==b[i])result[i]=a[i];
        else if(u>=1-1e-9)result[i]=b[i];
        else if(i>=3 && i<=5) {
            // Observed period-one wheel phase. High-speed/reverse sampling
            // remains a separate validation gate; never derive phase from speed.
            double delta=b[i]-a[i];delta-=std::round(delta);
            double phase=a[i]+u*delta;result[i]=phase-std::floor(phase);
        } else result[i]=a[i]+u*(b[i]-a[i]);
    }
    return result;
}
}
