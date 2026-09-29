// Converted recording -> native clock/interpolation -> bounded SDK appearance.
#include "../recorded_path.h"
#include "../hornet_appearance.h"
#include <iostream>
#include <limits>
#include <stdexcept>
namespace {
std::array<float,1000> args{};
size_t size=args.size();uint64_t identity=42;int writes=0;
void require(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
}
int main(int argc,char** argv) {
    try {
        require(argc==2,"provide converted wheel tape");
        recorded_path::Path path;
        require(std::string(path.load(argv[1]))=="recording_loaded" && path.has_wheels,"wheel tape rejected");
        ed_object_api_entry api{};auto handle=reinterpret_cast<ED_OBJECT_HANDLE>(0x1234);
        api.ed_get_object_id=[](ED_OBJECT_HANDLE){return identity;};
        api.ed_get_object_args=[](ED_OBJECT_HANDLE)->ed_object_args{return {args.data(),size};};
        api.ed_set_single_arg=[](ED_OBJECT_HANDLE,int c,float v){
            require(std::find(hornet_wheels::channels.begin(),hornet_wheels::channels.end(),c)!=hornet_wheels::channels.end(),"unrelated write");
            require(size_t(c)<size,"out of bounds write");args[c]=v;++writes;
        };
        for(size_t i=0;i<path.samples.size();++i) {
            const auto& a=path.samples[i];
            require(path.at_sample(a.t).wheels==a.wheels,"source sample changed");
            args.fill(.123f);
            require(hornet_appearance::apply_wheels(&api,handle,42,a.wheels),"SDK wheel write failed");
            for(size_t c=0;c<a.wheels.size();++c)require(args[hornet_wheels::channels[c]]==float(a.wheels[c]),"wrong readback");
            require(args[38]==.123f && args[0]==.123f,"changed canopy/deployment");
            if(i+1<path.samples.size()) {
                const auto& b=path.samples[i+1];auto mid=path.at_sample((a.t+b.t)/2).wheels;
                for(size_t c=0;c<mid.size();++c) {
                    if(c>=3 && c<=5) {
                        auto distance=[](double x,double y){double d=std::abs(x-y);return std::min(d,1.0-d);};
                        require(std::abs(distance(mid[c],a.wheels[c])-distance(a.wheels[c],b.wheels[c])/2)<1e-8 &&
                            std::abs(distance(mid[c],b.wheels[c])-distance(a.wheels[c],b.wheels[c])/2)<1e-8,"wrong wrap midpoint");
                    } else require(std::abs(mid[c]-(a.wheels[c]+b.wheels[c])/2)<1e-8,"wrong linear midpoint");
                }
            }
        }
        require(path.at_sample(-1).wheels==path.samples.front().wheels,"initial hold changed");
        require(path.at_sample(path.duration()+8).wheels==path.samples.back().wheels,"endpoint hold changed");
        auto valid=path.samples.front().wheels;int prior=writes;
        identity=43;require(!hornet_appearance::apply_wheels(&api,handle,42,valid),"wrong identity accepted");identity=42;
        size=103;require(!hornet_appearance::apply_wheels(&api,handle,42,valid),"short view accepted");size=args.size();
        for(size_t c=0;c<valid.size();++c)for(double bad:{-1.1,1.1,std::numeric_limits<double>::quiet_NaN(),std::numeric_limits<double>::infinity()}) {
            auto values=valid;values[c]=bad;require(!hornet_appearance::apply_wheels(&api,handle,42,values),"bad channel accepted");
        }
        auto bad=valid;bad[0]=-.01;require(!hornet_appearance::apply_wheels(&api,handle,42,bad),"negative strut accepted");
        require(!hornet_appearance::apply_wheels(&api,nullptr,42,valid),"null handle accepted");
        require(writes==prior,"rejected state wrote values");
        require(std::string(path.load("missing-wheel-tape.txt"))!="recording_loaded" && !path.has_wheels && path.samples.empty(),"stale wheels retained");
        std::cout<<"PASS: converted wheel samples/wrap midpoints, initial/final holds, SDK bounds/identity/value guards\n";
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
