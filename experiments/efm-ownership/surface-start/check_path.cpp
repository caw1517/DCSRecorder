// Offline checks for the contact-driven surface reader against a real V7 tape.
#include "recorded_path.h"
#include "release-start/policy.h"
#include <iostream>
#include <sstream>
#include <stdexcept>
void require(bool v,const char* reason){if(!v)throw std::runtime_error(reason);}
// Rewrite the contact flag (last value) of one sample row and reload.
std::string altered(const std::filesystem::path& source,size_t row,const std::string& flag) {
    std::ifstream in(source);std::ostringstream out;std::string line;size_t index=0;
    while(std::getline(in,line)) {
        // Header, count and six profile lines precede the samples.
        if(index>=8 && index-8==row)line=line.substr(0,line.find_last_of(' ')+1)+flag;
        out<<line<<'\n';++index;
    }
    auto path=source;path+=".altered";std::ofstream(path)<<out.str();
    recorded_path::Path p;const std::string status=p.load(path);std::filesystem::remove(path);return status;
}
int main(int argc,char** argv) {
    try {
        require(argc==2,"need a converted V7 tape");
        recorded_path::Path path;
#ifdef HORNET_SURFACE_PROTOTYPE
        require(std::string(path.load(argv[1]))=="recording_loaded","surface tape refused");
        require(path.has_contact && path.has_wheels && path.has_canopy && path.has_lights && path.has_engine,"incomplete snapshot");
        size_t grounded=0;for(const auto& s:path.samples)grounded+=s.ground;
        require(grounded>0,"no grounded samples");
        require(path.ground_at(0)==path.samples.front().ground && path.ground_at(path.duration())==path.samples.back().ground,"endpoint contact");
        auto initial=recorded_path::basis(path.samples.front().q);
        for(int k=0;k<3;++k)initial[12+k]=path.samples.front().p[k];
        require(path.initialize_exact(initial),"exact initialization");
        release_start::Clock clock;
        for(int i=0;i<=200;++i){require(clock.update(i*.02),"held clock");require(clock.elapsed==0,"advanced before release");}
        for(double t=0;t<=path.duration();t+=.01) {
            const auto m=path.motion_at(t);double speed2=0;
            for(float v:m.velocity){require(std::isfinite(v),"nonfinite interpolated velocity");speed2+=v*v;}
            require(path.ground_at(t) ? speed2<=260.0*260 : speed2>=70.0*70 && speed2<=260.0*260,"interpolated velocity outside contact envelope");
        }
        // A slow sample declared airborne keeps the airborne minimum.
        size_t slow=0;while(slow<path.samples.size()) {double s2=0;for(double v:path.samples[slow].v)s2+=v*v;if(s2<70*70)break;++slow;}
        require(slow<path.samples.size(),"take has no slow sample");
        require(altered(argv[1],slow,"0")=="recording_limits_rejected","slow airborne sample accepted");
        require(altered(argv[1],slow,"2")=="recording_contact_rejected","invalid contact flag accepted");
        std::cout<<"PASS: real V7 tape, "<<grounded<<"/"<<path.samples.size()<<" grounded samples, zero held clock, contact envelope and refusals\n";
#else
        require(std::string(path.load(argv[1]))=="recording_header_rejected","non-surface reader accepted a V7 tape");
        std::cout<<"PASS: non-surface reader refuses V7 tapes\n";
#endif
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
