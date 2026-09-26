#include "turn_path.h"
#include <iostream>
#include <stdexcept>
void require(bool condition,const char* message) { if(!condition) throw std::runtime_error(message); }
int main() {
    try {
        // Independent axis rotations lock down the native rate sign/order.
        const double h=1e-5;
        const auto level=turn_path::basis(0,0,0);
        const auto yaw_rate=turn_path::motion_between(turn_path::basis(-h,0,0),turn_path::basis(h,0,0),level,2*h);
        const auto pitch_rate=turn_path::motion_between(turn_path::basis(0,-h,0),turn_path::basis(0,h,0),level,2*h);
        const auto roll_rate=turn_path::motion_between(turn_path::basis(0,0,-h),turn_path::basis(0,0,h),level,2*h);
        require(std::abs(yaw_rate.angular[1]+1)<1e-6,"heading rate native sign");
        require(std::abs(pitch_rate.angular[2]-1)<1e-6,"pitch rate native axis");
        require(std::abs(roll_rate.angular[0]-1)<1e-6,"roll rate native axis");
        for(double heading:{-2.7,0.0,2.9}) {
            auto initial=turn_path::basis(heading,0.03,-0.08);
            initial[12]=-315000; initial[13]=2000; initial[14]=898000;
            turn_path::Path path; path.initialize(initial,145);
            const auto start=path.at(0),end=path.at(turn_path::turn_end);
            const auto speed_before=path.at(10-0.001),speed_after=path.at(10+0.001);
            require(std::abs(std::hypot(speed_after[12]-speed_before[12],speed_after[14]-speed_before[14])/0.002-turn_path::target_speed)<0.01,"formation speed differs from profile");
            for(int i=0;i<16;++i) require(std::abs(start[i]-initial[i])<1e-8,"initial pose jump");
#ifdef HORNET_PROTOTYPE
            require(std::abs(end[13]-initial[13])<1e-8,"Hornet turn must retain altitude");
            const auto first_end=path.at(turn_path::first_turn_end);
            require(std::abs(first_end[0]*std::cos(heading)+first_end[2]*std::sin(heading)+1)<1e-8,"right turn must change heading by 180 degrees");
            require(std::abs(end[0]*std::cos(heading)+end[2]*std::sin(heading)-1)<1e-8,"left turn must restore original heading");
            // Infer centripetal acceleration from position, independently of bank/rate commands.
            for(double segment_start:{2.0,turn_path::second_turn_start}) {
            const double middle=segment_start+turn_path::turn_duration/2, interval=0.2;
            const auto a=path.at(middle-interval),b=path.at(middle),c=path.at(middle+interval);
            const double ax=(c[12]-2*b[12]+a[12])/(interval*interval);
            const double az=(c[14]-2*b[14]+a[14])/(interval*interval);
            require(std::abs(std::sqrt(1+(ax*ax+az*az)/(9.80665*9.80665))-2.5)<0.002,"position-derived load must be 2.5g");
            require(std::abs(1/b[5]-2.5)<1e-8,"bank must match 2.5g coordinated turn");
            const double signed_bank=std::atan2(b[4]*-std::sin(path.yaw(middle))+b[6]*std::cos(path.yaw(middle)),b[5]);
            require((segment_start==2 ? signed_bank : -signed_bank)>1,"turn bank must reverse direction");
            for(double t:{segment_start,segment_start+turn_path::roll_in_time,segment_start+turn_path::turn_duration-turn_path::roll_out_time,segment_start+turn_path::turn_duration}) {
                const auto l=path.motion_at(t-1e-5),r=path.motion_at(t+1e-5);
                for(int k=0;k<3;++k) require(std::abs(l.angular[k]-r.angular[k])<0.001,"roll transition rate discontinuity");
            }
            }
            for(double t=turn_path::first_turn_end;t<=turn_path::second_turn_start;t+=0.1) {
                const auto p=path.at(t);
                const auto m=path.motion_at(t);
                require(std::abs(p[5]-1)<1e-8 && std::abs(p[13]-initial[13])<1e-8,"middle segment must be wings-level at constant altitude");
                for(float v:m.angular) require(std::abs(v)<1e-5,"middle segment must not rotate");
                require(std::abs(p[12]-first_end[12]-(t-turn_path::first_turn_end)*turn_path::target_speed*first_end[0])<0.001 &&
                        std::abs(p[14]-first_end[14]-(t-turn_path::first_turn_end)*turn_path::target_speed*first_end[2])<0.001,"middle segment must translate in a straight line");
            }
#else
            require(std::abs(end[13]-initial[13]-100)<1e-8,"climb must be 100 m");
            require(std::abs(end[0]*std::cos(heading)+end[2]*std::sin(heading))<1e-8,"heading must turn 90 degrees");
#endif
            require(std::abs(end[1])<1e-8 && std::abs(end[5]-1)<1e-8,"turn must end level");
            auto previous=start;
            for(int i=1;i<=static_cast<int>(std::lround(turn_path::duration/turn_path::dt));++i) {
                const double t=i*turn_path::dt; const auto p=path.at(t);
                const auto motion=path.motion_at(t);
                for(float v:motion.angular) require(std::isfinite(v) && std::abs(v)<1,"angular rate out of bounds");
                require(std::hypot(motion.velocity[0],motion.velocity[2])>std::min(145.0,turn_path::target_speed)-0.1,"motion must continue through settling and release");
                double speed2=0; for(float v:motion.velocity) speed2+=v*v;
                require(speed2<turn_path::max_speed*turn_path::max_speed,"motion exceeds native speed guard");
                if(t+turn_path::dt<=turn_path::duration) {
                    const auto next=path.at(t+turn_path::dt);
                    double prediction_error=0;
                    for(int k=0;k<3;++k) {
                        prediction_error+=std::pow(p[12+k]+motion.velocity[k]*turn_path::dt-next[12+k],2);
                        const double df=motion.angular[2]*p[4+k]-motion.angular[1]*p[8+k];
                        const double du=motion.angular[0]*p[8+k]-motion.angular[2]*p[k];
                        require(std::abs(p[k]+df*turn_path::dt-next[k])<0.0004,"forward-rate prediction mismatch");
                        require(std::abs(p[4+k]+du*turn_path::dt-next[4+k])<0.0004,"up-rate prediction mismatch");
                    }
                    require(std::sqrt(prediction_error)<0.025,"velocity prediction mismatch");
                }
                double step=0;
                for(int k=0;k<3;++k) step+=std::pow(p[12+k]-previous[12+k],2);
                require(step<100,"path discontinuity exceeds native 10m guard");
                for(int row=0;row<3;++row) for(int col=0;col<3;++col) {
                    double dot=0; for(int k=0;k<3;++k) dot+=p[4*row+k]*p[4*col+k];
                    require(std::abs(dot-(row==col ? 1.0:0.0))<1e-9,"nonorthonormal pose");
                }
                if(t>2.01 && t<turn_path::turn_end-0.01) {
                    const auto before=path.at(t-0.001),after=path.at(t+0.001);
                    double length=0,dot=0;
                    for(int k=0;k<3;++k) { double d=after[12+k]-before[12+k]; length+=d*d; dot+=d*p[k]; }
                    require(dot/std::sqrt(length)>0.99999,"turn orientation differs from path tangent");
                }
                previous=p;
            }
            const auto release=path.at(turn_path::duration);
            require(std::abs(release[1])<1e-8 && std::abs(release[5]-1)<1e-8,"release must be level");
        }
        std::cout<<"PASS: profile heading/altitude, initial continuity, tangent alignment, motion prediction, orthonormal poses and level release. Duration="<<turn_path::duration<<"s\n";
    } catch(const std::exception& e) { std::cerr<<e.what(); return 1; }
}
