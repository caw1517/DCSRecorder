#include "hornet_roll_path.h"
#include <iostream>
#include <stdexcept>
void require(bool ok,const char* message) { if(!ok) throw std::runtime_error(message); }
int main() {
    try {
        double worst_load_error=0,peak=0,max_rate=0;
        for(double heading:{-2.7,0.0,2.9}) {
            auto initial=turn_path::basis(heading,0.03,-0.08);
            initial[12]=-315000;initial[13]=2000;initial[14]=898000;
            hornet_roll_path::Path path;path.initialize(initial,225);
            const auto start=path.at(0);
            for(int k=0;k<16;++k) require(std::abs(start[k]-initial[k])<1e-8,"capture pose jump");
            const double entry=2+hornet_roll_data::pull_duration;
            require(std::abs(std::asin(path.at(entry)[1])*180/turn_path::pi-14)<0.001,"roll must begin at 14 degrees pitch");
            auto previous=start;
            double last_bank=0,total_bank=0;
            for(double t=0.02;t<hornet_roll_path::duration;t+=0.02) {
                const auto p=path.at(t),next=path.at(t+0.02);
                const auto motion=path.motion_at(t);
                double step=0,prediction=0,speed2=0;
                for(int k=0;k<3;++k) {
                    step+=std::pow(p[12+k]-previous[12+k],2);
                    prediction+=std::pow(p[12+k]+motion.velocity[k]*0.02-next[12+k],2);
                    speed2+=motion.velocity[k]*motion.velocity[k];
                    require(std::isfinite(motion.angular[k]) && std::abs(motion.angular[k])<1,"native angular rate bound");
                    max_rate=std::max(max_rate,std::abs(static_cast<double>(motion.angular[k])));
                    const double df=motion.angular[2]*p[4+k]-motion.angular[1]*p[8+k];
                    const double du=motion.angular[0]*p[8+k]-motion.angular[2]*p[k];
                    if(t+0.02<hornet_roll_path::duration) {
                        require(std::abs(p[k]+df*0.02-next[k])<0.0005,"forward motion prediction");
                        require(std::abs(p[4+k]+du*0.02-next[4+k])<0.0005,"up motion prediction");
                    }
                }
                require(step<100,"native step guard");
                require(speed2<260*260 && speed2>200*200,"native speed guard");
                if(t+0.02<hornet_roll_path::duration) require(prediction<0.025*0.025,"position prediction");
                require(p[13]>1000 && p[13]<5000,"native altitude guard");
                for(int row=0;row<3;++row) for(int col=0;col<3;++col) {
                    double dot=0;for(int k=0;k<3;++k) dot+=p[4*row+k]*p[4*col+k];
                    require(std::abs(dot-(row==col?1.0:0.0))<1e-9,"nonorthonormal pose");
                }
                if(t>2.05 && t<2+hornet_roll_data::maneuver_duration-0.05) {
                    // Independent acceleration from commanded positions, gravity removed.
                    const double h=0.04;const auto before=path.at(t-h),after=path.at(t+h);
                    double load=0,lateral=0,alignment=0;
                    for(int k=0;k<3;++k) {
                        const double force=(after[12+k]-2*p[12+k]+before[12+k])/(h*h)+(k==1?9.80665:0);
                        load+=force*p[4+k]/9.80665;lateral+=force*p[8+k]/9.80665;
                        alignment+=motion.velocity[k]*p[k];
                    }
                    const auto s=hornet_roll_path::sample(t-2);
                    worst_load_error=std::max(worst_load_error,std::abs(load-s.load));
                    require(std::abs(load-s.load)<0.008,"position-derived normal load differs from pull schedule");
                    require(std::abs(lateral)<0.008,"uncommanded lateral force");
                    require(alignment/std::sqrt(speed2)>0.999999,"nose differs from flight-path tangent");
                    require(std::abs(std::sqrt(speed2)-hornet_roll_path::speed(p[13]))<0.005,"400 KCAS speed schedule");
                }
                if(t>=2) {
                    peak=std::max(peak,std::asin(p[1])*180/turn_path::pi);
                    const double yaw=std::atan2(p[2],p[0]);
                    const double bank=std::atan2(p[4]*-std::sin(yaw)+p[6]*std::cos(yaw),p[5]/std::cos(std::asin(p[1])));
                    double delta=bank-last_bank;
                    while(delta>turn_path::pi) delta-=2*turn_path::pi;
                    while(delta<-turn_path::pi) delta+=2*turn_path::pi;
                    require(delta<1e-8,"roll reverses direction");
                    total_bank+=delta;last_bank=bank;
                }
                previous=p;
            }
            require(std::abs(total_bank+2*turn_path::pi)<1e-7,"roll must complete one full left revolution");
            require(std::abs(peak-30)<0.01,"peak nose-up must be 30 degrees");
            const auto end=path.at(hornet_roll_path::duration);
            require(std::abs(end[1])<1e-6 && std::abs(end[5]-1)<1e-8,"recovery must be wings level and nose level");
            for(double boundary:{2.0,entry,entry+hornet_roll_data::entry_duration,entry+hornet_roll_data::entry_duration+hornet_roll_data::middle_duration,2+hornet_roll_data::maneuver_duration}) {
                const auto left=path.motion_at(boundary-1e-5),right=path.motion_at(boundary+1e-5);
                for(int k=0;k<3;++k) require(std::abs(left.angular[k]-right.angular[k])<0.001 && std::abs(left.velocity[k]-right.velocity[k])<0.001,"segment boundary motion discontinuity");
            }
        }
        std::cout<<"PASS: 14-degree entry, 30-degree peak, full left roll, positive-g schedule, CAS speed, continuity, native guards, level recovery. Max load error="<<worst_load_error<<"g; max body rate="<<max_rate<<"rad/s; duration="<<hornet_roll_path::duration<<"s\n";
    } catch(const std::exception& e) { std::cerr<<e.what()<<'\n';return 1; }
}
