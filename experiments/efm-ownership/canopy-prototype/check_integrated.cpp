// Exercise the converted tape and integrated SDK writer without a running DCS.
#include "../recorded_path.h"
#include "../hornet_appearance.h"
#include <iostream>
#include <limits>
#include <stdexcept>

namespace {
std::array<float,1000> args{};
size_t size=args.size();
uint64_t identity=42;
int writes=0;
void require(bool ok,const char* message) {if(!ok)throw std::runtime_error(message);}
}
int main(int argc,char** argv) {
    try {
        require(argc==2,"provide converted canopy tape");
        recorded_path::Path path;
        require(std::string(path.load(argv[1]))=="recording_loaded" && path.has_canopy,"canopy tape rejected");
        ed_object_api_entry api{};
        auto handle=reinterpret_cast<ED_OBJECT_HANDLE>(0x1234);
        api.ed_get_object_id=[](ED_OBJECT_HANDLE){return identity;};
        api.ed_get_object_args=[](ED_OBJECT_HANDLE)->ed_object_args{return {args.data(),size};};
        api.ed_set_single_arg=[](ED_OBJECT_HANDLE,int c,float v){require(c==38 && size>38,"out-of-scope write");args[c]=v;++writes;};
        for(size_t i=0;i<path.samples.size();++i) {
            const auto& row=path.samples[i];
            require(path.at_sample(row.t).canopy==row.canopy,"source sample changed");
            require(hornet_appearance::apply_canopy(&api,handle,42,row.canopy),"canopy write failed");
            require(args[38]==static_cast<float>(row.canopy),"wrong readback");
            if(i+1<path.samples.size()) {
                const auto& next=path.samples[i+1];
                require(std::abs(path.at_sample((row.t+next.t)/2).canopy-(row.canopy+next.canopy)/2)<1e-10,"midpoint mismatch");
            }
        }
        require(path.at_sample(-1).canopy==path.samples.front().canopy,"initial hold mismatch");
        require(path.at_sample(path.duration()+8).canopy==path.samples.back().canopy,"final hold mismatch");
        int prior=writes;
        identity=43;require(!hornet_appearance::apply_canopy(&api,handle,42,.4),"identity guard");identity=42;
        size=38;require(!hornet_appearance::apply_canopy(&api,handle,42,.4),"bounds guard");size=args.size();
        for(double bad:{-.1,1.1,std::numeric_limits<double>::quiet_NaN(),std::numeric_limits<double>::infinity()})
            require(!hornet_appearance::apply_canopy(&api,handle,42,bad),"invalid value guard");
        require(!hornet_appearance::apply_canopy(&api,nullptr,42,.4),"null handle guard");
        require(writes==prior,"rejected state wrote a value");
        require(std::string(path.load("missing-canopy-tape.txt"))!="recording_loaded" && !path.has_canopy && path.samples.empty(),"stale tape retained");
        std::cout<<"PASS: converted canopy samples/midpoints, initial/final holds, SDK identity/bounds/value guards\n";
        return 0;
    } catch(const std::exception& error) {std::cerr<<error.what()<<'\n';return 1;}
}
