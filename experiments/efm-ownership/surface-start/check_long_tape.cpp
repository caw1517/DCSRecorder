// Offline full-flight duration check for the surface reader: loads a V7 tape of
// any length, checks the controller's fingerprint against the preparation one,
// replays the whole take on the release clock and reports whether the per-step
// cost grows with replay time.
// Usage: surface_long_tape_check <tape> <expected fingerprint, hex> [minimum seconds]
#include "recorded_path.h"
#include "release-start/policy.h"
#include "staged_playback.h"
#include <chrono>
#include <iostream>
#include <stdexcept>
void require(bool v,const char* reason){if(!v)throw std::runtime_error(reason);}
using clock_type=std::chrono::steady_clock;
double seconds_since(clock_type::time_point start){return std::chrono::duration<double>(clock_type::now()-start).count();}
int main(int argc,char** argv) {
    try {
        require(argc==3 || argc==4,"need a tape and its expected fingerprint");
        const double minimum=argc==4?std::stod(argv[3]):0;
        auto start=clock_type::now();
        recorded_path::Path path;
        require(std::string(path.load(argv[1]))=="recording_loaded","tape refused");
        const double load=seconds_since(start);
        require(path.duration()>=minimum,"tape shorter than requested");
        require(path.has_contact && path.has_wheels && path.has_canopy && path.has_lights && path.has_engine,"incomplete snapshot");
        start=clock_type::now();
        const auto token=staged_playback::fingerprint(argv[1]);
        const double hash=seconds_since(start);
        require(token==std::stoull(argv[2],nullptr,16),"fingerprint differs from preparation");
        auto initial=recorded_path::basis(path.samples.front().q);
        for(int k=0;k<3;++k)initial[12+k]=path.samples.front().p[k];
        require(path.initialize_exact(initial),"exact initialization");
        // The release clock at 50 Hz simulator time, from a nonzero mission time.
        release_start::Clock clock;
        require(clock.update(600) && clock.commit(true),"release");
        const double mission=600;const size_t steps=static_cast<size_t>(path.duration()/0.02);
        double first_minute=0,last_minute=0,worst_error=0;size_t per_minute=3000,grounded=0;
        for(size_t i=0;i<=steps+1;++i) {
            const auto before=clock_type::now();
            require(clock.update(mission+i*0.02),"clock");
            const double t=clock.elapsed;
            const auto m=path.motion_at(t);const auto s=path.at_sample(t);grounded+=path.ground_at(t);
            const double cost=seconds_since(before);
            for(float v:m.velocity)require(std::isfinite(v),"nonfinite velocity");
            // Replay time from a large mission clock stays exact to well under a tick.
            worst_error=std::max(worst_error,std::abs(t-i*0.02));
            require(std::abs(s.t-std::min(t,path.duration()))<1e-9,"sample time drift");
            if(i<per_minute)first_minute+=cost;
            if(i+per_minute>steps)last_minute+=cost;
        }
        require(std::abs(clock.elapsed-(steps+1)*0.02)<1e-6,"release clock drift");
        std::cout<<"PASS: "<<path.samples.size()<<" samples, "<<path.duration()<<" s, "<<grounded<<" grounded steps; load "<<load
                 <<" s; fingerprint "<<hash<<" s; first-minute step cost "<<first_minute*1000<<" ms, last-minute "<<last_minute*1000
                 <<" ms; clock error "<<worst_error<<" s\n";
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
