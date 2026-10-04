#pragma once
#include "turn_path.h"
#include "hornet_exterior.h"
#include "hornet_engine.h"
#include "hornet_lights.h"
#include "hornet_canopy.h"
#include "hornet_wheels.h"
#ifdef HORNET_GROUND_PROTOTYPE
#include "ground-start/tape_gate.h"
#endif
#include <filesystem>
#include <fstream>
#include <string>

// Recorded world-space samples. Translation aligns the first sample to the
// captured aircraft; axes and recorded heading remain in the original frame.
namespace recorded_path {
using turn_path::Pose;
using turn_path::Motion;
using Quaternion=std::array<double,4>; // w,x,y,z; matrix columns are F,U,R
inline double dot(const Quaternion& a,const Quaternion& b) {
    double d=0;for(int i=0;i<4;++i)d+=a[i]*b[i];return d;
}
inline Quaternion slerp(Quaternion a,Quaternion b,double u) {
    double d=dot(a,b);if(d<0) {for(auto& v:b)v=-v;d=-d;}
    double x=1-u,y=u;
    // Use spherical interpolation except for nearly identical samples; a wider
    // linear fallback introduces angular-rate ripple in fast recorded rolls.
    if(d<0.9999995) {const double angle=std::acos(std::clamp(d,-1.0,1.0));
        x=std::sin((1-u)*angle)/std::sin(angle);y=std::sin(u*angle)/std::sin(angle);}
    Quaternion q{};for(int i=0;i<4;++i)q[i]=a[i]*x+b[i]*y;
    const double n=std::sqrt(dot(q,q));for(auto& v:q)v/=n;return q;
}
inline Pose basis(const Quaternion& q) {
    const double w=q[0],x=q[1],y=q[2],z=q[3];Pose p{};
    p[0]=1-2*(y*y+z*z);p[1]=2*(x*y+w*z);p[2]=2*(x*z-w*y);
    p[4]=2*(x*y-w*z);p[5]=1-2*(x*x+z*z);p[6]=2*(y*z+w*x);
    p[8]=2*(x*z+w*y);p[9]=2*(y*z-w*x);p[10]=1-2*(x*x+y*y);p[15]=1;return p;
}
inline Quaternion quaternion(const Pose& p) {
    double m[3][3]{};for(int i=0;i<3;++i)for(int j=0;j<3;++j)m[i][j]=p[j*4+i];
    const double trace=m[0][0]+m[1][1]+m[2][2];Quaternion q{};
    if(trace>0) {const double s=2*std::sqrt(1+trace);q={s/4,(m[2][1]-m[1][2])/s,(m[0][2]-m[2][0])/s,(m[1][0]-m[0][1])/s};}
    else {int i=0;for(int j=1;j<3;++j)if(m[j][j]>m[i][i])i=j;
        const int j=(i+1)%3,k=(i+2)%3;const double s=2*std::sqrt(1+m[i][i]-m[j][j]-m[k][k]);
        q[0]=(m[k][j]-m[j][k])/s;q[i+1]=s/4;q[j+1]=(m[i][j]+m[j][i])/s;q[k+1]=(m[i][k]+m[k][i])/s;}
    const double n=std::sqrt(dot(q,q));for(auto& v:q)v/=n;return q;
}
struct Sample { double t=0;std::array<double,3> p{},v{};Quaternion q{};double brake=0,canopy=0;bool ground=false;hornet_exterior::Values exterior{};hornet_engine::Values engine{};hornet_lights::Values lights{};hornet_wheels::Values wheels{}; };
struct Path {
    std::vector<Sample> samples;
    std::array<double,3> translation{};
    Quaternion initial_q{1,0,0,0};
    bool exact_start=false;
    bool has_exterior=false,has_engine=false,has_lights=false,has_canopy=false,has_wheels=false,has_contact=false;
    double duration() const { return samples.empty()?0:samples.back().t; }
    const char* load(const std::filesystem::path& filename) {
#ifdef HORNET_GROUND_PROTOTYPE
        if(!ground_trial::tape_allowed(filename))return "ground_tape_not_authorized";
#endif
        samples.clear();has_contact=false;has_exterior=false;has_engine=false;has_lights=false;has_canopy=false;has_wheels=false;exact_start=false;translation={};std::ifstream f(filename);std::string header;size_t n=0;
        if(!(f>>header>>n) || (header!="DCSREC_PLAYBACK_V1" && header!="DCSREC_PLAYBACK_V2" && header!="DCSREC_PLAYBACK_V3" && header!="DCSREC_PLAYBACK_V4" && header!="DCSREC_PLAYBACK_V5" && header!="DCSREC_PLAYBACK_V6"
#ifdef HORNET_SURFACE_PROTOTYPE
            && header!="DCSREC_PLAYBACK_V7"
#endif
            ) || n<2 || n>100000) return "recording_header_rejected";
        // V7 adds one source contact flag per sample: 1 grounded, 0 airborne.
        const bool contact=header=="DCSREC_PLAYBACK_V7";
        const bool wheels=header=="DCSREC_PLAYBACK_V6" || contact;
        const bool canopy=header=="DCSREC_PLAYBACK_V5" || wheels;
        const bool lights=header=="DCSREC_PLAYBACK_V4" || canopy;
        const bool engine=header=="DCSREC_PLAYBACK_V3" || lights;
        const bool exterior=header=="DCSREC_PLAYBACK_V2" || engine;
        if(exterior) {std::string profile;if(!(f>>profile) || profile!=hornet_exterior::profile)return "recording_profile_rejected";}
        if(engine) {std::string profile;if(!(f>>profile) || profile!=hornet_engine::profile)return "recording_engine_profile_rejected";}
        if(lights) {std::string profile;if(!(f>>profile) || profile!=hornet_lights::profile)return "recording_light_profile_rejected";}
        if(canopy) {std::string profile;if(!(f>>profile) || profile!=hornet_canopy::profile)return "recording_canopy_profile_rejected";}
        if(wheels) {std::string profile;if(!(f>>profile) || profile!=hornet_wheels::profile)return "recording_wheel_profile_rejected";}
        if(contact) {std::string profile;if(!(f>>profile) || profile!="hornet-contact-v1")return "recording_contact_profile_rejected";}
        std::vector<Sample> loaded;loaded.reserve(n);
        for(size_t i=0;i<n;++i) {
            Sample s;f>>s.t;for(auto& v:s.p)f>>v;for(auto& v:s.q)f>>v;for(auto& v:s.v)f>>v;f>>s.brake;
            if(exterior) {for(auto& v:s.exterior)f>>v;if(!f || !hornet_exterior::valid(s.exterior))return "recording_exterior_rejected";}
            if(engine) {for(auto& v:s.engine)f>>v;if(!f || !hornet_engine::valid(s.engine))return "recording_engine_rejected";}
            if(lights) {for(auto& v:s.lights)f>>v;if(!f || !hornet_lights::valid(s.lights))return "recording_lights_rejected";}
            if(canopy) {f>>s.canopy;if(!f || !hornet_canopy::valid(s.canopy))return "recording_canopy_rejected";}
            if(wheels) {for(auto& v:s.wheels)f>>v;if(!f || !hornet_wheels::valid(s.wheels))return "recording_wheels_rejected";}
            if(contact) {double g=-1;f>>g;if(!f || (g!=0 && g!=1))return "recording_contact_rejected";s.ground=g==1;}
            if(!f || !std::isfinite(s.t) || !std::isfinite(s.brake))return "recording_sample_rejected";
            for(double v:s.p)if(!std::isfinite(v))return "recording_sample_rejected";
            for(double v:s.q)if(!std::isfinite(v))return "recording_sample_rejected";
            double speed2=0;for(double v:s.v) {if(!std::isfinite(v))return "recording_sample_rejected";speed2+=v*v;}
#ifdef HORNET_GROUND_PROTOTYPE
            if(!ground_trial::speed_allowed(speed2) ||
#else
            // Recorded speed is never limited; samples need only be finite.
            (void)speed2;
            if(
#endif
               std::abs(dot(s.q,s.q)-1)>0.001 || s.brake<0 || s.brake>1)return "recording_limits_rejected";
            if(i==0 && s.t!=0)return "recording_clock_rejected";
            if(i) {
                const auto& prev=loaded.back();const double dt=s.t-prev.t;
                if(!(dt>0 && dt<=0.15))return "recording_clock_rejected";
                double d=dot(prev.q,s.q);if(d<0) {for(auto& v:s.q)v=-v;d=-d;}
                double error2=0;for(int k=0;k<3;++k)error2+=std::pow(s.p[k]-prev.p[k]-dt*(s.v[k]+prev.v[k])/2,2);
                if(error2>std::pow(std::max(0.5,dt*8),2))return "recording_discontinuity_rejected";
            }
            loaded.push_back(s);
        }
        std::string extra;if(f>>extra)return "recording_trailing_data_rejected";
        if(loaded.back().t<5 || loaded.back().t>300)return "recording_duration_rejected";
        samples=std::move(loaded);has_exterior=exterior;has_engine=engine;has_lights=lights;has_canopy=canopy;has_wheels=wheels;has_contact=contact;initial_q=samples.front().q;return "recording_loaded";
    }
    bool initialize_exact(const Pose& initial) {
        if(samples.empty())return false;
        double distance2=0;
        for(int k=0;k<3;++k)distance2+=std::pow(initial[12+k]-samples.front().p[k],2);
        if(!std::isfinite(distance2) || distance2>100)return false;
        const auto captured_q=quaternion(initial);
        const double angle=2*std::acos(std::clamp(std::abs(dot(captured_q,samples.front().q)),0.0,1.0));
        if(!std::isfinite(angle) || angle>0.35)return false;
        translation={};initial_q=samples.front().q;exact_start=true;return true;
    }
    bool initialize(const Pose& initial,double /*measured_speed*/) {
        exact_start=false;
        if(samples.empty())return false;
        initial_q=quaternion(initial);
        if(2*std::acos(std::clamp(std::abs(dot(initial_q,samples.front().q)),0.0,1.0))>0.35)return false;
        for(int k=0;k<3;++k)translation[k]=initial[12+k]-samples.front().p[k];
        return true;
    }
    Sample at_sample(double t) const {
        t=std::clamp(t,0.0,duration());
        auto it=std::upper_bound(samples.begin(),samples.end(),t,[](double t,const Sample& s){return t<s.t;});
        const size_t i=std::clamp<size_t>(it-samples.begin(),1,samples.size()-1)-1;
        const auto& a=samples[i];const auto& b=samples[i+1];const double dt=b.t-a.t,u=(t-a.t)/dt;
        Sample s;s.t=t;s.q=slerp(a.q,b.q,u);s.brake=a.brake+(b.brake-a.brake)*u;
        if(has_exterior)for(size_t k=0;k<s.exterior.size();++k)s.exterior[k]=a.exterior[k]+(b.exterior[k]-a.exterior[k])*u;
        if(has_engine)for(size_t k=0;k<s.engine.size();++k)s.engine[k]=a.engine[k]+(b.engine[k]-a.engine[k])*u;
        if(has_lights) {
            for(size_t k=0;k<s.lights.size();++k)s.lights[k]=a.lights[k]+(b.lights[k]-a.lights[k])*u;
            s.lights[4]=(t>=b.t?b:a).lights[4]; // Preserve the sampled strobe edge.
        }
        if(has_wheels)s.wheels=hornet_wheels::interpolate(a.wheels,b.wheels,u);
        if(has_canopy)s.canopy=a.canopy+(b.canopy-a.canopy)*u;
        for(int k=0;k<3;++k)s.p[k]=(2*u*u*u-3*u*u+1)*a.p[k]+(u*u*u-2*u*u+u)*dt*a.v[k]+
            (-2*u*u*u+3*u*u)*b.p[k]+(u*u*u-u*u)*dt*b.v[k];
        return s;
    }
    Pose at(double t) const {
        auto s=at_sample(t);
        // Two-second attitude acquisition; afterward the recorded attitude is exact.
        if(!exact_start && t<2)s.q=slerp(initial_q,s.q,turn_path::smooth(t/2));
        auto p=basis(s.q);for(int k=0;k<3;++k)p[12+k]=s.p[k]+translation[k];return p;
    }
    Motion motion_at(double t) const {
        t=std::clamp(t,0.0,duration());const double lo=std::max(0.0,t-0.001),hi=std::min(duration(),t+0.001);
        auto motion=turn_path::motion_between(at(lo),at(hi),at(t),hi-lo);
        if(exact_start && t==0)for(int k=0;k<3;++k)motion.velocity[k]=static_cast<float>(samples.front().v[k]);
        return motion;
    }
    float brake_at(double t) const {return static_cast<float>(at_sample(t).brake);}
    // Contact of the sample at or before t; airborne-only tapes are never grounded.
    bool ground_at(double t) const {
        if(!has_contact || samples.empty())return false;
        t=std::clamp(t,0.0,duration());
        auto it=std::upper_bound(samples.begin(),samples.end(),t,[](double t,const Sample& s){return t<s.t;});
        return (it==samples.begin()?samples.front():*(it-1)).ground;
    }
};
}
