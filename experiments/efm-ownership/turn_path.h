#pragma once
#include <array>
#include <algorithm>
#include <cmath>
#include <vector>

namespace turn_path {
constexpr double pi=3.14159265358979323846, dt=0.02;
#ifdef HORNET_PROTOTYPE
// Approximate 400 KIAS using 400 KCAS at 2050 m in ISA, calm air.
// Check the player's actual HUD indication in the simulator.
constexpr double target_speed=225.0215739890135, max_speed=260, initial_speed_max=260;
constexpr double load_factor=2.5, roll_in_time=6.0, roll_out_time=3.0;
const double turn_rate=9.80665*std::sqrt(load_factor*load_factor-1)/target_speed;
const double turn_duration=pi/turn_rate+(roll_in_time+roll_out_time)/2;
constexpr double straight_duration=10;
const double first_turn_end=2+turn_duration, second_turn_start=first_turn_end+straight_duration;
const double turn_end=second_turn_start+turn_duration, duration=turn_end+6;
#else
constexpr double target_speed=105, turn_duration=30, max_speed=210, initial_speed_max=200;
const double turn_end=2+turn_duration, duration=turn_end+6;
#endif
using Pose=std::array<double,16>;
struct Motion { std::array<float,3> velocity{}, angular{}; };
inline Motion motion_between(const Pose& a,const Pose& b,const Pose& current,double interval) {
    Motion m;
    double wx=0,wy=0,wz=0;
    for(int k=0;k<3;++k) {
        m.velocity[k]=static_cast<float>((b[12+k]-a[12+k])/interval);
        const double df=(b[k]-a[k])/interval,du=(b[4+k]-a[4+k])/interval;
        // DCS local convention: dF=wz*U-wy*R; dU=wx*R-wz*F.
        wx+=du*current[8+k]; wy-=df*current[8+k]; wz+=df*current[4+k];
    }
    m.angular={static_cast<float>(wx),static_cast<float>(wy),static_cast<float>(wz)};
    return m;
}
inline double smooth(double u) { u=std::clamp(u,0.0,1.0); return u*u*u*(10+u*(-15+6*u)); }
inline double slope(double u) { if(u<=0 || u>=1) return 0; return 30*u*u*(1-u)*(1-u); }
inline Pose basis(double heading,double pitch,double bank) {
    Pose p{};
    const double c=std::cos(heading),s=std::sin(heading),cp=std::cos(pitch),sp=std::sin(pitch);
    const std::array<double,3> f{cp*c,sp,cp*s},u{-sp*c,cp,-sp*s},r{-s,0,c};
    for(int i=0;i<3;++i) {
        p[i]=f[i]; p[4+i]=u[i]*std::cos(bank)+r[i]*std::sin(bank);
        p[8+i]=r[i]*std::cos(bank)-u[i]*std::sin(bank);
    }
    p[15]=1; return p;
}
struct Path {
    double heading=0,pitch=0,bank=0,speed=target_speed,initial_speed=target_speed;
    std::array<double,3> origin{};
    std::vector<std::array<double,2>> horizontal;
#ifdef HORNET_PROTOTYPE
    // Integral of quintic easing; each ramp contributes half its duration.
    static double integral(double u) { u=std::clamp(u,0.0,1.0); return u*u*u*u*(2.5+u*(-3+u)); }
    static double segment_rate(double t) {
        if(t<=0 || t>=turn_duration) return 0;
        if(t<roll_in_time) return turn_rate*smooth(t/roll_in_time);
        if(t>turn_duration-roll_out_time) return turn_rate*(1-smooth((t-turn_duration+roll_out_time)/roll_out_time));
        return turn_rate;
    }
    static double segment_yaw(double t) {
        t=std::clamp(t,0.0,turn_duration);
        double area;
        if(t<roll_in_time) area=roll_in_time*integral(t/roll_in_time);
        else if(t<=turn_duration-roll_out_time) area=t-roll_in_time/2;
        else { const double u=(t-turn_duration+roll_out_time)/roll_out_time;
            area=turn_duration-roll_out_time-roll_in_time/2+roll_out_time*(u-integral(u)); }
        return turn_rate*area;
    }
    double rate(double t) const { return segment_rate(t-2)-segment_rate(t-second_turn_start); }
    double yaw(double t) const { return heading+segment_yaw(t-2)-segment_yaw(t-second_turn_start); }
#else
    double yaw(double t) const { return heading+pi/2*smooth((t-2)/turn_duration); }
#endif
    double horizontal_speed(double t) const { return initial_speed+(speed-initial_speed)*smooth(t/2); }
    void initialize(const Pose& initial,double measured_speed) {
        heading=std::atan2(initial[2],initial[0]); pitch=std::asin(std::clamp(initial[1],-1.0,1.0));
        bank=std::atan2(initial[4]*-std::sin(heading)+initial[6]*std::cos(heading),initial[5]/std::cos(pitch));
        initial_speed=std::clamp(measured_speed,80.0,initial_speed_max);
        speed=target_speed;
        origin={initial[12],initial[13],initial[14]}; horizontal.clear(); horizontal.push_back({0,0});
        for(int i=1;i<=static_cast<int>(std::ceil(duration/dt));++i) {
            auto p=horizontal.back(); const auto h=yaw((i-0.5)*dt);
            const double step=horizontal_speed((i-0.5)*dt)*dt;
            p[0]+=step*std::cos(h); p[1]+=step*std::sin(h); horizontal.push_back(p);
        }
    }
    Pose at(double t) const {
        t=std::clamp(t,0.0,duration);
#ifdef HORNET_PROTOTYPE
        double elevation=0;
        double roll=std::atan2(speed*rate(t),9.80665);
        if(t<2) { elevation=pitch*(1-smooth(t/2)); roll=bank*(1-smooth(t/2)); }
#else
        const double u=(t-2)/turn_duration;
        double elevation=std::atan2(100*slope(u)/turn_duration,speed);
        double roll=std::atan2(speed*(pi/2)*slope(u)/turn_duration,9.80665);
        if(t<2) { elevation=pitch*(1-smooth(t/2)); roll=bank*(1-smooth(t/2)); }
        if(t>turn_end) { const double a=(t-turn_end)/6; const double envelope=std::pow(std::sin(pi*a),2);
            elevation=5*pi/180*std::sin(4*pi*a)*envelope;
            roll=10*pi/180*std::sin(2*pi*a)*envelope;
        }
#endif
        Pose p=basis(yaw(t),elevation,roll);
        const double index=t/dt; const auto i=std::min<size_t>(static_cast<size_t>(index),horizontal.size()-2);
        const double f=std::clamp(index-i,0.0,1.0);
        p[12]=origin[0]+horizontal[i][0]*(1-f)+horizontal[i+1][0]*f;
        p[14]=origin[2]+horizontal[i][1]*(1-f)+horizontal[i+1][1]*f;
#ifdef HORNET_PROTOTYPE
        p[13]=origin[1];
#else
        p[13]=origin[1]+100*smooth(u);
#endif
        return p;
    }
    Motion motion_at(double t) const {
        t=std::clamp(t,0.0,duration);
        const double lo=std::max(0.0,t-0.001),hi=std::min(duration,t+0.001);
        return motion_between(at(lo),at(hi),at(t),hi-lo);
    }
};
}
