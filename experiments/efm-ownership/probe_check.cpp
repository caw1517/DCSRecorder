#include <windows.h>
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <cstdint>
#include <cstddef>
#include <array>
#include <string>
#include "ed_object_access.h"
#include "native_identity.h"
struct IdentityLeft { virtual ~IdentityLeft() = default; int a = 0; };
struct IdentityRight { virtual ~IdentityRight() = default; int b = 0; };
struct IdentityDerived : IdentityLeft, IdentityRight {};
namespace {
uint64_t test_id=12345;
std::array<float,320> draw_args;
size_t draw_size=draw_args.size();
int argument_writes=0;
}
template<class T> T load(HMODULE dll,const char* name) {
    auto value = GetProcAddress(dll,name);
    if (!value) throw std::runtime_error(name);
    return reinterpret_cast<T>(value);
}
int main(int argc,char** argv) {
    if(argc!=2 && argc!=3) return 2;
    const bool owned_staged=argc==3 && std::string(argv[2])=="--owned-staged";
    if(argc==3 && !owned_staged)return 2;
    auto dll=LoadLibraryA(argv[1]);
    if(!dll) return 3;
    try {
        IdentityDerived identity;
        auto inspected=native_identity::inspect(static_cast<IdentityRight*>(&identity));
        bool saw_right=false;
        for(const auto& base:inspected.bases) if(base.name.find("IdentityRight")!=std::string::npos) saw_right=true;
        if(inspected.status!="ok" || inspected.name.find("IdentityDerived")==std::string::npos ||
            inspected.subobject_offset==0 || !saw_right) return 8;
        if(native_identity::inspect(nullptr).status=="ok") return 9;
        auto start=load<void(*)()>(dll,"ed_fm_hot_start_in_air");
        auto step=load<void(*)(double)>(dll,"ed_fm_simulate");
        auto moment=load<void(*)(double&,double&,double&)>(dll,"ed_fm_add_local_moment");
        auto release=load<void(*)()>(dll,"ed_fm_release");
        auto setup=load<PFN_ED_SETUP_OBJECT_API>(dll,"ed_setup_object_api");
        auto create=load<PFN_ED_ON_OBJECT_CREATE>(dll,"ed_on_object_create");
        auto simulate_object=load<PFN_ED_ON_OBJECT_SIMULATE>(dll,"ed_on_object_simulate");
        auto destroy=load<PFN_ED_ON_OBJECT_DESTROY>(dll,"ed_on_object_destroy");
        ed_object_api_entry api{};
        api.ed_get_object_id=[](ED_OBJECT_HANDLE)->uint64_t { return test_id; };
        api.ed_get_object_args=[](ED_OBJECT_HANDLE)->ed_object_args { return {draw_args.data(),draw_size}; };
        api.ed_set_single_arg=[](ED_OBJECT_HANDLE,int index,float value) {
            if(index<0 || static_cast<size_t>(index)>=draw_size) throw std::runtime_error("argument bounds");
            draw_args[index]=value; ++argument_writes;
        };
        setup(&api);
        uint64_t cookie=42;
        auto object=reinterpret_cast<ED_OBJECT_HANDLE>(&cookie);
        create(object,cookie);
        simulate_object(object,cookie,1.0);
        simulate_object(object,cookie,1.1);
        if(argument_writes!=0) throw std::runtime_error("appearance wrote to wrong object");
        test_id=16777472; draw_args.fill(0.75f); draw_size=100;
        simulate_object(object,cookie,1.2);
        if(argument_writes!=0) throw std::runtime_error("appearance wrote to incomplete argument view");
        draw_size=draw_args.size();
        simulate_object(object,cookie,1.3);
        const bool hornet=!owned_staged && std::string(argv[1]).find("Hornet")!=std::string::npos && std::string(argv[1]).find("Staged")==std::string::npos;
        if(hornet) {
            if(draw_args[21]!=0 || draw_args[88]!=0 || draw_args[190]!=0 || draw_args[193]!=0 || draw_args[210]!=0 || draw_args[212]!=0)
                throw std::runtime_error("Hornet speed brake or lights remain deployed/on");
            if(draw_args[0]!=0.75f || draw_args[183]!=0.75f || draw_args[309]!=0.75f)
                throw std::runtime_error("unrelated exterior state changed");
            // Simulate the engine changing an animation between callbacks.
            draw_args[21]=1; simulate_object(object,cookie,1.4);
            if(draw_args[21]!=0) throw std::runtime_error("speed brake not held stowed");
        } else if(argument_writes!=0) throw std::runtime_error("TF-51D appearance changed");
        destroy(object,cookie);
        if(cookie!=42) return 7;
        setup(nullptr);
        // Check reset and impulse at two step sizes, including non-aligned pulse boundaries.
        for(double dt : {0.01,0.037}) {
            start(); double impulse=0;
            for(int i=0;i<static_cast<int>(8/dt);++i) {
                step(dt); double x=0,y=0,z=0; moment(x,y,z);
                if(!std::isfinite(x) || x < 0 || x > 4000.00001) return 4;
                impulse+=x*dt;
            }
            if(std::abs(impulse-2000)>0.0001) return 5;
        }
        release();
        std::cout << "PASS: read-only RTTI on secondary base and null input, exports, lifecycle ABI with preserved cookie, bounded pulse and reset. Not a DCS runtime test.\n";
    } catch(const std::exception& e) { std::cerr<<e.what(); return 6; }
    FreeLibrary(dll);
}
