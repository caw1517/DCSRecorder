#include "policy.h"
#include "../recorded_path.h"
#include <iostream>
#include <limits>
#include <stdexcept>
void require(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
int main() {
    try {
        release_start::Clock clock;
        require(!clock.commit(true),"uninitialized release");
        recorded_path::Path path;recorded_path::Sample first,last;
        first.q=last.q={1,0,0,0};first.p={10,2000,30};first.v={140,0,0};first.brake=.7;
        first.exterior.fill(.4);first.engine.fill(.8);first.lights.fill(.6);first.canopy=.9;first.wheels.fill(.3);
        last=first;last.t=5;last.p[0]+=700;last.brake=0;last.engine.fill(.1);last.exterior.fill(0);
        path.samples={first,last};path.exact_start=true;
        path.has_exterior=path.has_engine=path.has_lights=path.has_canopy=path.has_wheels=true;
        for(double now:{0.,10.,30.,31.,32.,33.}) {
            require(clock.update(now) && clock.elapsed==0,"inspection/countdown advanced");
            const auto snapshot=path.at_sample(clock.elapsed);
            require(snapshot.p==first.p && path.motion_at(clock.elapsed).velocity[0]==140 && snapshot.engine==first.engine &&
                snapshot.exterior==first.exterior && snapshot.brake==first.brake,"snapshot changed during hold");
        }
        require(!clock.commit(false) && clock.commit(true) && !clock.commit(true),"readiness or duplicate release");
        require(clock.update(33.02) && clock.elapsed==0 && clock.playing(),"first callback not time zero");
        require(path.motion_at(clock.elapsed).velocity[0]==140,"initial velocity not restored");
        require(clock.update(34.02) && std::abs(clock.elapsed-1)<1e-12,"incorrect replay epoch");
        const auto pose=path.at(clock.elapsed);const auto state=path.at_sample(clock.elapsed);
        for(int frame=0;frame<1000;++frame)require(clock.update(34.02) && path.at(clock.elapsed)==pose &&
            path.at_sample(clock.elapsed).engine==state.engine,"paused clock advanced");
        require(clock.update(34.04) && std::abs(clock.elapsed-1.02)<1e-12,"pause caused catch-up");
        require(!clock.update(34.03) && !clock.commit(true),"reversed clock accepted");
        release_start::Clock invalid;
        require(!invalid.update(std::numeric_limits<double>::quiet_NaN()),"NaN clock accepted");
        release_start::Clock restart;require(restart.update(0) && restart.elapsed==0 && !restart.playing(),"restart reused epoch");
        std::cout<<"PASS: readiness, duplicate, shared first snapshot/motion/engine epoch, pause, reversal and restart\n";
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
