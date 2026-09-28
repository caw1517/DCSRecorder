// Execute the built DLL against a bounded fake SDK, using the actual captured tape.
#include <windows.h>
#include <cstdint>
#include <cstddef>
#include "ed_object_access.h"
#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
namespace {
#ifdef WHEEL_APPEARANCE_PROTOTYPE
constexpr size_t channel_count=10;
constexpr const char* tape_header="DCS_WHEEL_PROTOTYPE_V1";
#elif defined(CANOPY_APPEARANCE_PROTOTYPE)
constexpr size_t channel_count=1;
constexpr const char* tape_header="DCS_CANOPY_PROTOTYPE_V1";
#elif defined(LIGHT_APPEARANCE_PROTOTYPE)
constexpr size_t channel_count=10;
constexpr const char* tape_header="DCS_LIGHT_PROTOTYPE_V1";
#elif defined(ENGINE_APPEARANCE_PROTOTYPE)
constexpr size_t channel_count=4;
constexpr const char* tape_header="DCS_ENGINE_PROTOTYPE_V1";
#else
constexpr size_t channel_count=14;
constexpr const char* tape_header="DCS_EXTERIOR_PROTOTYPE_V1";
#endif
std::array<float,1000> args{};
size_t view_size=args.size();
uint64_t id=42;
int writes=0;
bool invalid_write=false;
auto object=reinterpret_cast<ED_OBJECT_HANDLE>(0x1234);
void require(bool condition,const char* message) {if(!condition)throw std::runtime_error(message);}
}
int main(int argc,char** argv) {
    try {
        require(argc==2 || (argc==3 && std::string(argv[2])=="--expect-native-rejection"),"provide isolated DLL path with exterior-state.txt beside it");
        const auto dll=std::filesystem::absolute(argv[1]);
        std::ifstream file(dll.parent_path()/"exterior-state.txt");
        std::string header;size_t count=0;file>>header>>count;
        require(header==tape_header && count>1,"missing tape");
        std::array<int,channel_count> channels{};for(auto& c:channels)file>>c;
        struct Row {double t;std::array<float,channel_count> values;};std::vector<Row> rows(count);
        for(auto& row:rows) {file>>row.t;for(auto& v:row.values)file>>v;}
        require(bool(file),"invalid tape");
        const auto module=LoadLibraryW(dll.c_str());require(module!=nullptr,"DLL load failed");
        const auto setup=reinterpret_cast<PFN_ED_SETUP_OBJECT_API>(GetProcAddress(module,"ed_setup_object_api"));
        const auto create=reinterpret_cast<PFN_ED_ON_OBJECT_CREATE>(GetProcAddress(module,"ed_on_object_create"));
        const auto simulate=reinterpret_cast<PFN_ED_ON_OBJECT_SIMULATE>(GetProcAddress(module,"ed_on_object_simulate"));
        const auto destroy=reinterpret_cast<PFN_ED_ON_OBJECT_DESTROY>(GetProcAddress(module,"ed_on_object_destroy"));
        require(setup && create && simulate && destroy,"callback export missing");
        ed_object_api_entry api{};
        api.ed_get_object_id=[](ED_OBJECT_HANDLE){return id;};
        api.ed_get_object_args=[](ED_OBJECT_HANDLE)->ed_object_args{return {args.data(),view_size};};
        api.ed_set_single_arg=[](ED_OBJECT_HANDLE h,int c,float value){
            if(h!=object || c<0 || size_t(c)>=view_size) {invalid_write=true;return;}
            const bool allowed=
#ifdef WHEEL_APPEARANCE_PROTOTYPE
                (c>=0 && c<=6) || (c>=101 && c<=103) || c==998 || c==999;
#elif defined(CANOPY_APPEARANCE_PROTOTYPE)
                c==38 || c==998 || c==999;
#elif defined(LIGHT_APPEARANCE_PROTOTYPE)
                c==0 || c==3 || c==5 || c==88 || (c>=190 && c<=193) || c==210 || c==212 || c==998 || c==999;
#elif defined(ENGINE_APPEARANCE_PROTOTYPE)
                c==28 || c==29 || c==89 || c==90 || c==998 || c==999;
#else
                c==0 || c==3 || c==5 || (c>=9 && c<=18) || c==21 || c==998 || c==999;
#endif
            if(!allowed)invalid_write=true;
            args[c]=value;++writes;
        };
        setup(&api);uint64_t cookie=0;create(object,cookie);
        require(cookie!=0,"creation failed");
        if(argc==3) {
            args.fill(0.333f);simulate(object,cookie,10);
            require(args[999]==0.75f,"native variant did not reject fake DCS object");
            for(int c:channels)require(args[c]==0.333f,"native guard failed after writing surfaces");
            const auto before=writes;simulate(object,cookie,11);
            require(writes==before,"rejected native variant kept writing");
            destroy(object,cookie);FreeLibrary(module);
            std::cout << "PASS: post-step DLL rejects non-DCS identity before surface/native writes\n";
            return 0;
        }
        // Every real sample survives, including signed flap/surface values.
        for(const auto& row:rows) {
            args.fill(0.333f); // Simulate native animation overwriting the previous values.
            simulate(object,cookie,10+row.t);
            for(size_t i=0;i<channels.size();++i)require(std::abs(args[channels[i]]-row.values[i])<0.00001f,"captured value mismatch");
        }
        require(args[999]==0.5f,"endpoint not marked complete");
        require(args[100]==0.333f,"unrelated channel changed");
        auto before=writes;id=43;simulate(object,cookie,200);require(writes==before,"wrong identity written");id=42;
        uint64_t wrong_cookie=cookie+1;simulate(object,wrong_cookie,200);require(writes==before,"wrong cookie written");
        view_size=30;simulate(object,cookie,200);require(writes==before,"short view written");view_size=args.size();
        destroy(object,cookie);simulate(object,cookie,200);require(writes==before,"destroyed object written");
        create(object,cookie);simulate(object,cookie,10);simulate(object,cookie,10+(rows[1].t-rows[0].t)/2);
        for(size_t i=0;i<channels.size();++i)require(std::abs(args[channels[i]]-(rows[0].values[i]+rows[1].values[i])/2)<0.00001f,"interpolation mismatch");
#ifdef WHEEL_APPEARANCE_PROTOTYPE
        destroy(object,cookie);create(object,cookie);simulate(object,cookie,0);
        size_t wraps=0;
        for(size_t i=0;i+1<rows.size();++i) {
            simulate(object,cookie,(rows[i].t+rows[i+1].t)/2);
            for(size_t c=0;c<channels.size();++c) {
                const double a=rows[i].values[c],b=rows[i+1].values[c],actual=args[channels[c]];
                if(c>=6 && c<=8) {
                    // Circular distances to each endpoint must be equal and half
                    // the short source arc. The long-way midpoint fails this.
                    auto distance=[](double x,double y){double d=std::abs(x-y);return std::min(d,1.0-d);};
                    require(actual>=0 && actual<=1,"wheel phase out of range");
                    require(std::abs(distance(actual,a)-distance(a,b)/2)<0.00001 &&
                        std::abs(distance(actual,b)-distance(a,b)/2)<0.00001,"wheel wrap midpoint mismatch");
                    if(std::abs(a-b)>.5)++wraps;
                } else require(std::abs(actual-(a+b)/2)<0.00001,"compression/steering midpoint mismatch");
            }
        }
        require(wraps>0,"fixture must exercise rotation wraps");
        simulate(object,cookie,rows.back().t+8);
        for(size_t c=0;c<channels.size();++c)require(args[channels[c]]==rows.back().values[c],"wheel endpoint hold mismatch");
        require(args[999]==.5f,"wheel final hold status");
        std::cout<<"PASS: "<<wraps<<" captured wrap crossings; every midpoint and final hold\n";
        destroy(object,cookie);create(object,cookie);simulate(object,cookie,10);
#endif
#ifdef CANOPY_APPEARANCE_PROTOTYPE
        // Exercise changing values between every pair of real canopy samples.
        destroy(object,cookie);create(object,cookie);simulate(object,cookie,0);
        for(size_t i=0;i+1<rows.size();++i) {
            simulate(object,cookie,(rows[i].t+rows[i+1].t)/2);
            require(std::abs(args[38]-(rows[i].values[0]+rows[i+1].values[0])/2)<0.00001f,"canopy midpoint mismatch");
        }
        simulate(object,cookie,rows.back().t+8);
        require(std::abs(args[38]-rows.back().values[0])<0.00001f && args[999]==0.5f,"canopy final hold mismatch");
        destroy(object,cookie);create(object,cookie);simulate(object,cookie,10);
#endif
#ifdef LIGHT_APPEARANCE_PROTOTYPE
        // Check both sides of every real strobe edge on a fresh lifecycle.
        destroy(object,cookie);create(object,cookie);simulate(object,cookie,0);
        for(size_t i=0;i+1<rows.size();++i) {
            simulate(object,cookie,(rows[i].t+rows[i+1].t)/2);
            require(std::abs(args[193]-rows[i].values[7])<0.00001f,"strobe edge interpolated");
        }
        destroy(object,cookie);create(object,cookie);simulate(object,cookie,10);
#endif
        simulate(object,cookie,9);require(args[999]==0.75f,"backward clock not rejected");
        before=writes;simulate(object,cookie,11);require(writes==before,"rejected object kept writing");
        destroy(object,cookie);require(!invalid_write,"out-of-scope SDK write");
        FreeLibrary(module);
        std::cout << "PASS: " << count << " real samples, signed values, interpolation, endpoint, identity/cookie/bounds/lifecycle/clock guards\n";
        return 0;
    } catch(const std::exception& error) {std::cerr<<error.what()<<'\n';return 1;}
}
