#include "hornet_roll_path.h"
#include <iostream>
#include <stdexcept>
void require(bool ok,const char* message) { if(!ok) throw std::runtime_error(message); }
int main() {
    try {
        double worst_load_error=0,peak=0,max_rate=0,worst_energy_error=0,min_speed=1000;
        for(double heading:{-2.7,0.0,2.9}) {
            auto initial=turn_path::basis(heading,0.03,-0.08);
            initial[12]=-315000;initial[13]=2000;initial[14]=898000;
            hornet_roll_path::Path path;path.initialize(initial,225);
            const auto start=path.at(0);
            for(int k=0;k<16;++k) require(std::abs(start[k]-initial[k])<1e-8,"capture pose jump");
            const auto initial_motion=path.motion_at(2);
            double entry_speed2=0;for(float v:initial_motion.velocity) entry_speed2+=v*v;
            require(std::abs(std::sqrt(entry_speed2)-hornet_roll_path::speed(2000))<0.001,"maneuver must start at nominal 400 KCAS");
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
                require(speed2<260*260 && speed2>70*70,"native speed guard");
                min_speed=std::min(min_speed,std::sqrt(speed2));
                if(t+0.02<hornet_roll_path::duration) require(prediction<0.025*0.025,"position prediction");
                require(p[13]>1000 && p[13]<5000,"native altitude guard");
                for(int row=0;row<3;++row) for(int col=0;col<3;++col) {
                    double dot=0;for(int k=0;k<3;++k) dot+=p[4*row+k]*p[4*col+k];
                    require(std::abs(dot-(row==col?1.0:0.0))<1e-9,"nonorthonormal pose");
                }
                if(t>2.05 && t<hornet_roll_path::duration-0.05) {
                    // Independent acceleration from commanded positions, gravity removed.
                    const double h=0.04;const auto before=path.at(t-h),after=path.at(t+h);
                    double load=0,lateral=0,alignment=0,axial_force=0;
                    for(int k=0;k<3;++k) {
                        const double force=(after[12+k]-2*p[12+k]+before[12+k])/(h*h)+(k==1?9.80665:0);
                        load+=force*p[4+k]/9.80665;lateral+=force*p[8+k]/9.80665;
                        axial_force+=force*p[k];
                        alignment+=motion.velocity[k]*p[k];
                    }
                    const auto s=hornet_roll_path::sample(t-2);
                    worst_load_error=std::max(worst_load_error,std::abs(load-s.load));
                    require(std::abs(load-s.load)<0.008,"position-derived normal load differs from pull schedule");
                    require(std::abs(lateral)<0.008,"uncommanded lateral force");
                    require(alignment/std::sqrt(speed2)>0.999999,"nose differs from flight-path tangent");
                    // Independent fixed-thrust drag balance. Detect a speed hold,
                    // endpoint reset, or unexplained energy added during recovery.
                    using namespace hornet_roll_data;
                    const double temperature=288.15-0.0065*p[13];
                    const double pressure=101325*std::pow(temperature/288.15,9.80665/(287.05287*0.0065));
                    const double q=0.5*pressure/(287.05287*temperature)*speed2;
                    const double cl=s.load*mass*9.80665/(q*area);
                    const double expected=thrust_acceleration-q*area*(cd0+induced_factor*cl*cl)/mass;
                    worst_energy_error=std::max(worst_energy_error,std::abs(axial_force-expected));
                    require(std::abs(axial_force-expected)<0.008,"fixed-thrust energy balance violated");
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
            const auto recovered=path.at(2+hornet_roll_data::maneuver_duration);
            require(std::abs(recovered[13]-initial[13])<0.001 && std::abs(end[13]-initial[13])<0.001,"must return to pre-pull altitude without a height snap");
            require(std::abs(recovered[0]*std::cos(heading)+recovered[2]*std::sin(heading)-1)<1e-8,"must regain entry heading");
            require((recovered[12]-initial[12])*-std::sin(heading)+(recovered[14]-initial[14])*std::cos(heading)<-1,"roll should finish offset left");
            const auto end_motion=path.motion_at(2+hornet_roll_data::maneuver_duration);
            double end_speed=0;for(float v:end_motion.velocity) end_speed+=v*v;end_speed=std::sqrt(end_speed);
            require(min_speed<hornet_roll_path::speed(2000)-30 && end_speed>min_speed+30 && end_speed<hornet_roll_path::speed(2000),"speed must bleed, recover, and retain drag loss");
            for(double boundary:{2.0,entry,entry+hornet_roll_data::entry_duration,entry+hornet_roll_data::entry_duration+hornet_roll_data::middle_duration,2+hornet_roll_data::maneuver_duration-6,2+hornet_roll_data::maneuver_duration}) {
                const auto left=path.motion_at(boundary-1e-5),right=path.motion_at(boundary+1e-5);
                for(int k=0;k<3;++k) require(std::abs(left.angular[k]-right.angular[k])<0.001 && std::abs(left.velocity[k]-right.velocity[k])<0.001,"segment boundary motion discontinuity");
            }
        }
        std::cout<<"PASS: initial 400 KCAS, 14-degree entry, 30-degree peak, full left roll, positive-g schedule, fixed-thrust energy, same altitude/heading recovery, left offset, continuity and native guards. Max load error="<<worst_load_error<<"g; max energy error="<<worst_energy_error<<"m/s2; min speed="<<min_speed<<"m/s; max body rate="<<max_rate<<"rad/s; duration="<<hornet_roll_path::duration<<"s\n";
    } catch(const std::exception& e) { std::cerr<<e.what()<<'\n';return 1; }
}
