#include "recorded_path.h"
#include <iostream>
#include <iomanip>
#include <stdexcept>
void require(bool ok,const char* message) {if(!ok)throw std::runtime_error(message);}
int main(int argc,char** argv) {
    using namespace recorded_path;
    // Quaternion round trips cover inverted and heading/pitch wrap regions.
    for(double h:{-3.1,0.4,3.1})for(double p:{-1.4,0.3,1.4})for(double b:{-3.14,0.0,3.14}) {
        const auto pose=turn_path::basis(h,p,b),back=basis(quaternion(pose));
        for(int k=0;k<12;++k)require(std::abs(pose[k]-back[k])<1e-12,"quaternion basis round trip");
    }
    const auto tape=std::filesystem::temp_directory_path()/"dcs-recorded-path-check.txt";
    { std::ofstream f(tape);f<<std::setprecision(16)<<"DCSREC_PLAYBACK_V1\n1501\n";
      for(int i=0;i<=1500;++i) {
        const double t=i*0.02,bank=-2*turn_path::pi*turn_path::smooth((t-5)/20);
        auto q=quaternion(turn_path::basis(0,0,bank));
        // Deliberate sign flips: q and -q describe the same physical orientation.
        if(i%2)for(auto& v:q)v=-v;
        f<<t<<' '<<1000+220*t<<" 2000 500 ";for(double v:q)f<<v<<' ';
        f<<"220 0 0 "<<turn_path::smooth((t-10)/5)<<'\n';
      }
    }
    Path path;require(std::string(path.load(tape))=="recording_loaded","valid tape load");
    auto initial=turn_path::basis(0,0,0);initial[12]=3000;initial[13]=2050;initial[14]=-200;
    require(path.initialize(initial,220),"alignment");
    double worst=0;
    for(int i=0;i<=3000;++i) {
        const double t=i*0.01;const auto p=path.at(t);const auto m=path.motion_at(t);
        require(std::abs(p[12]-(3000+220*t))<1e-8 && std::abs(p[13]-2050)<1e-8,"translated position");
        require(std::abs(m.velocity[0]-220)<0.001 && std::abs(m.velocity[1])<0.001,"matched velocity");
        const auto expected=turn_path::basis(0,0,-2*turn_path::pi*turn_path::smooth((t-5)/20));
        for(int k=0;k<12;++k)worst=std::max(worst,std::abs(p[k]-expected[k]));
        for(float rate:m.angular)require(std::isfinite(rate) && std::abs(rate)<0.9,"bounded roll rates");
    }
    require(worst<0.00002,"roll interpolation through inverted");
    require(path.brake_at(10)==0 && path.brake_at(20)==1,"recorded brake");
    auto wrong=turn_path::basis(1,0,0);wrong[13]=2050;require(!path.initialize(wrong,220),"reject heading mismatch");
    {std::ofstream f(tape);f<<"DCSREC_PLAYBACK_V1\n2\n0 0 2000 0 1 0 0 0 220 0 0 0\n6 1320 2000 0 1 0 0 0 220 0 0 0\n";}
    require(std::string(path.load(tape))=="recording_clock_rejected" && path.samples.empty(),"reject gapped tape and clear old data");
    std::filesystem::remove(tape);require(std::string(path.load(tape))=="recording_header_rejected","missing tape fails closed");
    std::cout<<"PASS: quaternion round trips, full roll through inverted, sign continuity, translated trajectory, velocity, brake, invalid tape guards\n";
    if(argc==2) {
        Path imported;require(std::string(imported.load(argv[1]))=="recording_loaded","converted tape load");
        auto initial=basis(imported.samples.front().q);
        for(int k=0;k<3;++k)initial[12+k]=imported.samples.front().p[k];
        require(imported.initialize(initial,220),"converted tape alignment");
        for(double t=0;t<imported.duration();t+=0.01) {
            const auto p=imported.at(t);const auto m=imported.motion_at(t);double speed2=0;
            for(double v:p)require(std::isfinite(v),"converted tape finite pose");
            for(float v:m.velocity)speed2+=v*v;
            require(speed2>=70*70 && speed2<=260*260,"interpolated tape speed guard");
            for(float v:m.angular)require(std::isfinite(v) && std::abs(v)<1,"interpolated tape angular guard");
            require(p[13]>=1000 && p[13]<=5000,"interpolated tape altitude guard");
        }
        std::cout<<"PASS: converted tape loaded and evaluated by native playback at 100 Hz\n";
    }
}
