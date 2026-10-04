#include "policy.h"
#include "../recorded_path.h"
#include <iostream>
#include <limits>
#include <stdexcept>
void require(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
int main() {
    try {
        recorded_path::Path path;
        recorded_path::Sample first,last;
        first.q=last.q={1,0,0,0};first.p={10,2000,30};first.v={140,0,0};first.brake=.7;
        first.exterior.fill(.4);first.engine.fill(.8);first.lights.fill(.6);
        first.canopy=.9;first.wheels.fill(.3);
        last=first;last.t=5;last.p[0]+=700;last.brake=0;
        last.exterior.fill(0);last.engine.fill(.1);last.lights.fill(0);
        last.canopy=0;last.wheels.fill(0);
        path.samples={first,last};path.exact_start=true;
        path.has_exterior=path.has_engine=path.has_lights=path.has_canopy=path.has_wheels=true;
        const auto pose=path.at(0);
        for(double now:{10.,10.01,40.,100.}) {
            const auto t=held_start::replay_time(now,10);
            require(t==0 && path.at(t)==pose && path.brake_at(t)==float(.7),"held snapshot advanced");
            const auto snapshot=path.at_sample(t);
            require(snapshot.exterior==first.exterior && snapshot.engine==first.engine &&
                snapshot.lights==first.lights && snapshot.canopy==first.canopy &&
                snapshot.wheels==first.wheels,"held channel group advanced or defaulted");
        }
        require(path.motion_at(0).velocity[0]==140,"recorded release velocity was erased");
        require(held_start::stationary(turn_path::Motion{}),"stationary hold rejected");
        require(!held_start::stationary(path.motion_at(0)),"moving hold accepted");
        turn_path::Motion turn{};turn.angular[0]=.001f;
        require(!held_start::stationary(turn),"rotating hold accepted");
        require(held_start::replay_time(9,10)<0,"reversed clock accepted");
        require(held_start::replay_time(std::numeric_limits<double>::quiet_NaN(),10)<0,"NaN clock accepted");
        std::cout<<"PASS: stationary hold preserves first pose/brake and original release velocity; invalid clocks/motion refused\n";
    } catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
