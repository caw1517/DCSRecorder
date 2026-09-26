#pragma once
#include "turn_path.h"
#include "hornet_roll_data.h"

namespace hornet_roll_path {
using turn_path::Pose;
using turn_path::Motion;
using turn_path::basis;
using turn_path::smooth;
constexpr double duration=2+hornet_roll_data::sample_duration;
inline double speed(double h) {
    const double temperature=288.15-0.0065*h;
    const double pressure=101325*std::pow(temperature/288.15,9.80665/(287.05287*0.0065));
    constexpr double vc=400*1852.0/3600;
    const double qc=101325*(std::pow(1+vc*vc/(5*1.4*287.05287*288.15),3.5)-1);
    return std::sqrt(1.4*287.05287*temperature*5*(std::pow(1+qc/pressure,2.0/7)-1));
}
inline std::array<double,3> velocity(const hornet_roll_data::Sample& s) {
    const double v=s.speed,cp=std::cos(s.pitch);
    return {v*cp*std::cos(s.heading),v*std::sin(s.pitch),v*cp*std::sin(s.heading)};
}
inline hornet_roll_data::Sample sample(double t) {
    using namespace hornet_roll_data;
    t=std::clamp(t,0.0,sample_duration);
    auto i=std::min<size_t>(static_cast<size_t>(t/0.02),samples.size()-2);
    const auto& a=samples[i];const auto& b=samples[i+1];
    const double span=b.t-a.t,u=std::clamp((t-a.t)/span,0.0,1.0);
    auto mix=[u](double a,double b) { return a+(b-a)*u; };
    const auto va=velocity(a),vb=velocity(b);
    auto hermite=[=](double a,double b,double da,double db) {
        return (2*u*u*u-3*u*u+1)*a+(u*u*u-2*u*u+u)*span*da+(-2*u*u*u+3*u*u)*b+(u*u*u-u*u)*span*db;
    };
    return {t,mix(a.pitch,b.pitch),mix(a.heading,b.heading),
        hermite(a.x,b.x,va[0],vb[0]),hermite(a.height,b.height,va[1],vb[1]),hermite(a.z,b.z,va[2],vb[2]),
        mix(a.speed,b.speed),mix(a.bank,b.bank),mix(a.load,b.load)};
}
struct Path {
    double heading=0,pitch=0,bank=0,initial_speed=0,settle_distance=0;
    std::array<double,3> origin{};
    void initialize(const Pose& initial,double measured_speed) {
        heading=std::atan2(initial[2],initial[0]);pitch=std::asin(std::clamp(initial[1],-1.0,1.0));
        bank=std::atan2(initial[4]*-std::sin(heading)+initial[6]*std::cos(heading),initial[5]/std::cos(pitch));
        origin={initial[12],initial[13],initial[14]};
        initial_speed=std::clamp(measured_speed,80.0,turn_path::initial_speed_max);
        settle_distance=initial_speed+speed(2000);
    }
    Pose at(double t) const {
        t=std::clamp(t,0.0,duration);
        double x=0,y=0,z=0;Pose p;
        if(t<2) {
            const double u=t/2,integral=u*u*u*u*(2.5+u*(-3+u));
            x=initial_speed*t+(speed(2000)-initial_speed)*2*integral;
            p=basis(heading,pitch*(1-smooth(u)),bank*(1-smooth(u)));
        } else {
            const auto s=sample(t-2);
            p=basis(heading+s.heading,s.pitch,s.bank);
            x=settle_distance+s.x;y=s.height-2000;z=s.z;
        }
        p[12]=origin[0]+x*std::cos(heading)-z*std::sin(heading);
        p[13]=origin[1]+y;
        p[14]=origin[2]+x*std::sin(heading)+z*std::cos(heading);
        return p;
    }
    Motion motion_at(double t) const {
        t=std::clamp(t,0.0,duration);
        const double lo=std::max(0.0,t-0.001),hi=std::min(duration,t+0.001);
        return turn_path::motion_between(at(lo),at(hi),at(t),hi-lo);
    }
};
}
