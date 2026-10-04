#include "recorded_path.h"
#include "held-start/policy.h"
#include "release-start/policy.h"
#include <iostream>
#include <stdexcept>
void require(bool v,const char* reason){if(!v)throw std::runtime_error(reason);}
int main(int argc,char** argv) {
    try {
        require(argc==2,"need the actual converted tape");
        recorded_path::Path path;
#ifdef HORNET_GROUND_PROTOTYPE
        require(std::string(path.load(argv[1]))=="recording_loaded","reviewed ground tape refused");
        require(path.samples.size()==991 && path.duration()>19.79 && path.duration()<19.81,"wrong real take");
        auto initial=recorded_path::basis(path.samples.front().q);
        for(int k=0;k<3;++k)initial[12+k]=path.samples.front().p[k];
        require(path.initialize_exact(initial),"exact initialization");
        release_start::Clock clock;
        for(int i=0;i<=1650;++i){require(clock.update(i*.02),"held/countdown clock");require(clock.elapsed==0,"advanced before release");}
        require(clock.commit(true),"commit");require(clock.update(33.02),"release");require(clock.elapsed==0,"first epoch");
        auto motion=path.motion_at(0);
        for(int k=0;k<3;++k)require(motion.velocity[k]==static_cast<float>(path.samples.front().v[k]),"original initial velocity lost");
        for(double t=0;t<=path.duration();t+=.01) {
            const auto m=path.motion_at(t);double speed2=0;
            for(float v:m.velocity){require(std::isfinite(v),"nonfinite interpolated velocity");speed2+=v*v;}
            require(ground_trial::speed_allowed(speed2),"interpolated velocity outside ground envelope");
        }
        require(!ground_trial::speed_allowed(25.01),"excessive speed accepted");
        auto altered=std::filesystem::path(argv[1]);altered+=".changed";
        {std::ifstream src(argv[1],std::ios::binary);std::ofstream dst(altered,std::ios::binary);dst<<src.rdbuf()<<' ';}
        require(std::string(path.load(altered))=="ground_tape_not_authorized","changed tape accepted");
        std::filesystem::remove(altered);
        std::cout<<"PASS: real ground tape, 33-second zero clock, original release velocity, bounded interpolation and changed-tape refusal\n";
#else
        require(std::string(path.load(argv[1]))=="recording_limits_rejected","normal airborne reader accepted ground");
        std::cout<<"PASS: normal native airborne reader still refuses ground\n";
#endif
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
