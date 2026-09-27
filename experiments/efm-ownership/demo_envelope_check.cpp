#include "recorded_path.h"
#include <iostream>
#include <iomanip>
#include <stdexcept>
void require(bool value,const char* message) {if(!value){std::cerr<<"FAIL: "<<message<<std::endl;throw std::runtime_error(message);}}
int main() {
    using namespace recorded_path;
    const auto file=std::filesystem::temp_directory_path()/"dcs-demo-envelope-check.txt";
    constexpr double speed=350*0.5144444444444444, g=9.80665, load=7.5;
    const double rate=g*std::sqrt(load*load-1)/speed, radius=speed/rate;
    double worst_position=0,worst_basis=0,worst_velocity=0,worst_rate=0;
    for(bool turn:{false,true})for(double height:{-50.0,0.0,76.2,152.4,6000.0}) {
        auto reference=[&](double t) {
            const double heading=turn?rate*t:0;
            auto pose=turn_path::basis(heading,0,turn?std::acos(1/load):turn_path::pi*t);
            pose[12]=1000+(turn?radius*std::sin(heading):speed*t);
            pose[13]=height;pose[14]=500+(turn?radius*(1-std::cos(heading)):0);
            return pose;
        };
        {std::ofstream f(file);f<<std::setprecision(17)<<"DCSREC_PLAYBACK_V1\n301\n";
            for(int i=0;i<=300;++i) {
                const double t=i*.02;const auto p=reference(t);auto q=quaternion(p);
                if(i%2)for(auto& x:q)x=-x;
                f<<t<<' '<<p[12]<<' '<<p[13]<<' '<<p[14]<<' ';
                for(auto x:q)f<<x<<' ';
                f<<speed*std::cos(turn?rate*t:0)<<" 0 "<<speed*std::sin(turn?rate*t:0)<<" 0\n";
            }
        }
        Path path;require(std::string(path.load(file))=="recording_loaded","demo tape must load");
        require(path.initialize_exact(reference(0)),"exact demo start");
        for(int i=0;i<=6000;++i) {
            const double t=i*.001;const auto p=path.at(t),expected=reference(t);const auto m=path.motion_at(t);
            for(int k=0;k<3;++k)worst_position=std::max(worst_position,std::abs(p[12+k]-expected[12+k]));
            for(int k=0;k<12;++k)worst_basis=std::max(worst_basis,std::abs(p[k]-expected[k]));
            const double heading=turn?rate*t:0;
            worst_velocity=std::max(worst_velocity,std::abs(m.velocity[0]-speed*std::cos(heading)));
            worst_velocity=std::max(worst_velocity,std::abs(m.velocity[2]-speed*std::sin(heading)));
            double angular2=0;for(float v:m.angular){require(std::isfinite(v),"finite demo angular rate");angular2+=v*v;}
            worst_rate=std::max(worst_rate,std::abs(std::sqrt(angular2)-(turn?rate:turn_path::pi)));
        }
    }
    std::filesystem::remove(file);
    std::cerr<<"Measured position="<<worst_position<<", basis="<<worst_basis<<", velocity="<<worst_velocity<<", rate="<<worst_rate<<std::endl;
    require(worst_position<.000001,"demo path position precision");
    require(worst_basis<.000001,"demo path orientation precision");
    // Finite difference at the endpoints is one-sided (1 ms).
    require(worst_velocity<.04,"demo path velocity precision");
    require(worst_rate<.00002,"demo angular rate precision");
    std::cout<<"PASS: 180 deg/s rolls and modeled 7.5 G / 350 knot turns; altitude retained; max position="
        <<worst_position<<" m, basis="<<worst_basis<<", velocity="<<worst_velocity<<" m/s, angular="<<worst_rate<<" rad/s\n";
}
