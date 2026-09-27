#include "../native_step_hook.h"
#include "../native_animation_hook.h"
#include <iostream>
#include <stdexcept>
#include <thread>

namespace {
struct Aircraft { uintptr_t table; double stabilator=0; double dt=0; bool update=false; int calls=0; };
void physics(void*) {}
void animate(void* pointer,double dt,bool update) {
    auto& a=*static_cast<Aircraft*>(pointer);
    a.dt=dt;a.update=update;++a.calls;a.stabilator=0.01;
}
void repair(const void* handle) {
    reinterpret_cast<Aircraft*>(reinterpret_cast<uintptr_t>(handle)-8)->stabilator=0.6;
}
void cycle(Aircraft& a,double dt=0.02,bool update=true) {
    reinterpret_cast<native_step_hook::Step*>(a.table)[native_step_hook::step_slot](&a);
    reinterpret_cast<native_animation_hook::Step*>(a.table)[native_animation_hook::step_slot](&a,dt,update);
}
void require(bool good,const char* reason) {if(!good)throw std::runtime_error(reason);}
}
int main(int argc,char**) {
    try {
        std::array<uintptr_t,native_animation_hook::slots+1> original{};
        original[0]=0x12345678;
        original[native_step_hook::step_slot+1]=reinterpret_cast<uintptr_t>(&physics);
        original[native_animation_hook::step_slot+1]=reinterpret_cast<uintptr_t>(&animate);
        const auto table=reinterpret_cast<uintptr_t>(original.data()+1);
        Aircraft a{table},other{table};
        const auto object=reinterpret_cast<uintptr_t>(&a);
        require(std::string(native_step_hook::install(object,table,&physics,nullptr,&repair))=="step_hook_installed","early install failed");
        cycle(a);
        if(argc>1)require(a.stabilator==0.6,"FAIL: later animation erased post-physics stabilator write");
        require(a.stabilator==0.01,"fixture failed to reproduce live overwrite ordering");
        native_step_hook::restore(object);
        require(std::string(native_animation_hook::install(object,table,&animate,nullptr,&repair))=="animation_hook_installed","animation install failed");
        const auto clone=reinterpret_cast<uintptr_t*>(a.table);
        require(clone[-1]==original[0],"RTTI locator changed");
        for(size_t i=0;i<native_animation_hook::slots;++i)
            if(i!=native_animation_hook::step_slot)require(clone[i]==original[i+1],"unrelated slot changed");
        require(original[native_animation_hook::step_slot+1]==reinterpret_cast<uintptr_t>(&animate),"shared table changed");
        cycle(a,0.037,false);
        require(a.stabilator==0.6 && a.dt==0.037 && !a.update && a.calls==2,"animation argument forwarding or repair failed");
        cycle(a,0.014,true);
        require(a.stabilator==0.6 && a.dt==0.014 && a.update && a.calls==3,"repeated animation repair failed");
        cycle(other);require(other.stabilator==0.01 && other.table==table,"other aircraft changed");
        std::thread foreign([&]{cycle(a);});foreign.join();
        require(a.stabilator==0.01,"foreign-thread repair allowed");
        cycle(a);require(a.stabilator==0.6,"owner repair failed");
        require(std::string(native_animation_hook::restore(reinterpret_cast<uintptr_t>(&other)))=="animation_hook_restore_owner_rejected","wrong-owner restore allowed");
        require(std::string(native_animation_hook::restore(object))=="animation_hook_restored" && a.table==table,"restore failed");
        cycle(a);require(a.stabilator==0.01,"repair survived release");
        require(std::string(native_animation_hook::install(object,table+8,&animate,nullptr,&repair))=="animation_hook_object_rejected","wrong table accepted");
        require(std::string(native_animation_hook::install(object,table,&animate,nullptr,&repair))=="animation_hook_installed","reinstall failed");
        a.table=table+8;
        require(std::string(native_animation_hook::restore(object))=="animation_hook_already_replaced" && a.table==table+8,"replacement table overwritten");
        std::cout<<"PASS: SDK -> physics -> animation overwrite regression; arguments, repeated calls, ownership and restore verified. DCS validation pending.\n";
    } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
