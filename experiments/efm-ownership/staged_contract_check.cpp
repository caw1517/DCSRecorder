#include "recorded_path.h"
#include "staged_playback.h"
#include "hornet_appearance.h"
#include <iostream>
#include <iomanip>
#include <stdexcept>
using recorded_path::Path;
void require(bool good,const char* message) {if(!good)throw std::runtime_error(message);}
namespace {std::array<float,1000> args{};size_t view_size=1000;int writes=0;uint64_t id=987654;}
int main() {
    const auto file=std::filesystem::temp_directory_path()/"dcs-staged-contract-check.txt";
    try {
        auto recorded=turn_path::basis(0,0.03,0.05);
        const auto q=recorded_path::quaternion(recorded);
        {std::ofstream out(file);out<<std::setprecision(16)<<"DCSREC_PLAYBACK_V1\n301\n";
         for(int i=0;i<=300;++i) {const double t=i*0.02;
             out<<t<<' '<<1000+220*t<<" 2000 500 ";for(double v:q)out<<v<<' ';
             out<<"220 0 0 0.4\n";}}
        Path path;require(std::string(path.load(file))=="recording_loaded","load");
        auto spawn=turn_path::basis(0,0,0);spawn[12]=1000.05;spawn[13]=1997.62;spawn[14]=500.04;
        require(path.initialize_exact(spawn),"bounded spawn correction");
        const auto first=path.at(0);
        for(int k=0;k<12;++k)require(std::abs(first[k]-recorded[k])<1e-12,"exact attitude without acquisition blend");
        require(first[12]==1000 && first[13]==2000 && first[14]==500,"no capture-relative translation");
        require(path.motion_at(0).velocity==std::array<float,3>{220,0,0},"initial measured velocity");
        require(std::abs(path.brake_at(0)-0.4f)<1e-6,"initial supported exterior state");
        for(double t=0;t<=6;t+=0.007) {
            require(std::abs(path.at(t)[12]-(1000+220*t))<1e-8,"recorded world path");
            require(std::abs(path.motion_at(t).velocity[0]-220)<0.001,"continuous recorded velocity");
        }
        auto too_far=spawn;too_far[12]+=11;require(!path.initialize_exact(too_far),"retain ten-metre correction guard");
        auto wrong_heading=turn_path::basis(1,0,0);wrong_heading[12]=1000;wrong_heading[13]=2000;wrong_heading[14]=500;
        require(!path.initialize_exact(wrong_heading),"retain heading guard");
        require(path.initialize(spawn,220) && !path.exact_start,"legacy translated mode still explicit");
        require(std::abs(path.at(0)[13]-spawn[13])<1e-8,"legacy regression");
        const auto fingerprint=staged_playback::fingerprint(file);
        require(fingerprint!=0,"tape fingerprint");
        {std::ofstream out(file,std::ios::app);out<<"\n";}
        require(staged_playback::fingerprint(file)!=fingerprint,"mismatched tape changes handshake");
        ed_object_api_entry api{};
        api.ed_get_object_id=[](ED_OBJECT_HANDLE){return id;};
        api.ed_get_object_args=[](ED_OBJECT_HANDLE)->ed_object_args{return {args.data(),view_size};};
        api.ed_set_single_arg=[](ED_OBJECT_HANDLE,int n,float value){require(n>=0 && size_t(n)<view_size,"argument write bounds");args[n]=value;++writes;};
        auto handle=reinterpret_cast<ED_OBJECT_HANDLE>(&id);
        view_size=999;require(!staged_playback::publish(&api,handle,fingerprint,staged_playback::running) && writes==0,"missing status channel fails before writes");
        view_size=1000;
        for(float status:{staged_playback::running,staged_playback::complete,staged_playback::failed})
            require(staged_playback::publish(&api,handle,fingerprint,status),"status readback");
        require(args[0]==0 && args[21]==0,"status transport leaves aircraft animation arguments alone");
        require(std::string(hornet_appearance::apply(&api,handle,0.4f,id))=="recorded_brake_verified","late-activation runtime ID accepted explicitly");
        const int before=writes;require(std::string(hornet_appearance::apply(&api,handle,0.4f,id+1))=="wrong_object" && writes==before,"different runtime ID rejected");
        std::filesystem::remove(file);
        std::cout<<"PASS: exact pose/velocity/brake, original world path, bounded correction, legacy regression, tape fingerprint, status bounds/readback and explicit runtime identity. Not a live DCS handshake test.\n";
    }catch(const std::exception& e){std::filesystem::remove(file);std::cerr<<e.what()<<'\n';return 1;}
}
