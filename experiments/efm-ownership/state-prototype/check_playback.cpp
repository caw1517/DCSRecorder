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
        require(header=="DCS_EXTERIOR_PROTOTYPE_V1" && count>1,"missing tape");
        std::array<int,14> channels{};for(auto& c:channels)file>>c;
        struct Row {double t;std::array<float,14> values;};std::vector<Row> rows(count);
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
            const bool allowed=c==0 || c==3 || c==5 || (c>=9 && c<=18) || c==21 || c==998 || c==999;
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
        create(object,cookie);simulate(object,cookie,10);simulate(object,cookie,10.025);
        for(size_t i=0;i<channels.size();++i)require(std::abs(args[channels[i]]-(rows[0].values[i]+rows[1].values[i])/2)<0.00001f,"interpolation mismatch");
        simulate(object,cookie,9);require(args[999]==0.75f,"backward clock not rejected");
        before=writes;simulate(object,cookie,11);require(writes==before,"rejected object kept writing");
        destroy(object,cookie);require(!invalid_write,"out-of-scope SDK write");
        FreeLibrary(module);
        std::cout << "PASS: " << count << " real samples, signed values, interpolation, endpoint, identity/cookie/bounds/lifecycle/clock guards\n";
        return 0;
    } catch(const std::exception& error) {std::cerr<<error.what()<<'\n';return 1;}
}
