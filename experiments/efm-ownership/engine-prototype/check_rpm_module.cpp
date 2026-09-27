// Exercise the actual packaged DLL's rejection path through the installed SDK ABI.
#include <windows.h>
#include <cstdint>
#include <cstddef>
#include "ed_object_access.h"
#include <array>
#include <filesystem>
#include <iostream>
#include <stdexcept>
int main(int argc,char** argv) {
    try {
        auto require=[](bool ok,const char* why){if(!ok)throw std::runtime_error(why);};
        require(argc==2,"provide packaged DLL path with recorded-rpm.txt beside it");
        const auto dll=std::filesystem::absolute(argv[1]);
        auto module=LoadLibraryW(dll.c_str());require(module!=nullptr,"DLL load failed");
        auto setup=reinterpret_cast<PFN_ED_SETUP_OBJECT_API>(GetProcAddress(module,"ed_setup_object_api"));
        auto create=reinterpret_cast<PFN_ED_ON_OBJECT_CREATE>(GetProcAddress(module,"ed_on_object_create"));
        auto simulate=reinterpret_cast<PFN_ED_ON_OBJECT_SIMULATE>(GetProcAddress(module,"ed_on_object_simulate"));
        auto destroy=reinterpret_cast<PFN_ED_ON_OBJECT_DESTROY>(GetProcAddress(module,"ed_on_object_destroy"));
        require(setup && create && simulate && destroy,"SDK export missing");
        static std::array<float,1000> args{};args.fill(0.333f);
        static int writes=0;static bool invalid=false;
        auto object=reinterpret_cast<ED_OBJECT_HANDLE>(0x1234);
        ed_object_api_entry api{};
        api.ed_get_object_id=[](ED_OBJECT_HANDLE)->uint64_t{return 42;};
        api.ed_get_object_args=[](ED_OBJECT_HANDLE)->ed_object_args{return {args.data(),args.size()};};
        api.ed_set_single_arg=[](ED_OBJECT_HANDLE h,int c,float value){
            if(h!=reinterpret_cast<ED_OBJECT_HANDLE>(0x1234) || c!=999){invalid=true;return;}
            args[c]=value;++writes;
        };
        setup(&api);uint64_t cookie=0;create(object,cookie);
        require(cookie!=0,"missing lifecycle cookie");
        auto wrong=cookie+1;simulate(object,wrong,10);require(writes==0,"wrong cookie accepted");
        simulate(object,cookie,10);
        require(writes==1 && args[999]==0.75f,"non-DCS object was not rejected");
        for(size_t i=0;i<999;++i)require(args[i]==0.333f,"unrelated argument written");
        simulate(object,cookie,11);require(writes==1,"rejected object kept writing");
        destroy(object,cookie);simulate(object,cookie,12);
        require(writes==1 && !invalid,"post-destroy or out-of-scope write");
        FreeLibrary(module);
        std::cout<<"PASS: packaged RPM DLL loads tape and rejects non-DCS object before native/appearance writes\n";
        return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
