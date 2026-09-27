#include "parameter_hook.h"
#include <iostream>
#include <stdexcept>
#include <thread>
struct Aircraft {uintptr_t table;float flame=0,observed_power=0;double dt=0;bool update=false;int repairs=0;};
void require(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
float rpm(void*,int,bool){return .7f;}
float thrust(void*,int){return .2f;}
float power(void* p,int engine) {
    return reinterpret_cast<parameter_hook::Thrust*>(static_cast<Aircraft*>(p)->table)[parameter_hook::thrust_slot](p,engine);
}
void animate(void* p,double dt,bool update) {
    auto&a=*static_cast<Aircraft*>(p);a.dt=dt;a.update=update;a.flame=0;
    // Exercise getter re-entry from native animation: no hook mutex may be held.
    a.observed_power=power(p,1);
}
void repair(const void* handle) {
    auto&a=*reinterpret_cast<Aircraft*>(reinterpret_cast<uintptr_t>(handle)-8);
    require(a.flame==0,"repair ran before original animation");a.flame=.8f;++a.repairs;
}
void cycle(Aircraft& a) {
    reinterpret_cast<parameter_hook::Animation*>(a.table)[native_animation_hook::step_slot](&a,.031,false);
}
int main() {
    try {
        std::array<uintptr_t,parameter_hook::slots+1> entries{};entries[0]=0x1234;
        entries[parameter_hook::slot+1]=reinterpret_cast<uintptr_t>(&rpm);
        entries[parameter_hook::thrust_slot+1]=reinterpret_cast<uintptr_t>(&thrust);
        entries[parameter_hook::power_slot+1]=reinterpret_cast<uintptr_t>(&power);
        entries[native_animation_hook::step_slot+1]=reinterpret_cast<uintptr_t>(&animate);
        auto table=reinterpret_cast<uintptr_t>(entries.data()+1);
        Aircraft a{table},other{table};const auto object=reinterpret_cast<uintptr_t>(&a);
        auto install=[&]{return std::string(parameter_hook::install(object,table,&rpm,&thrust,&power,&animate,&repair));};
        require(install()=="parameter_hook_installed","install");
        auto clone=reinterpret_cast<uintptr_t*>(a.table);
        require(clone[-1]==entries[0],"RTTI changed");
        for(size_t i=0;i<parameter_hook::slots;++i)
            if(i!=parameter_hook::slot && i!=parameter_hook::thrust_slot && i!=native_animation_hook::step_slot)
                require(clone[i]==entries[i+1],"unrelated slot changed");
        cycle(a);require(a.flame==0 && !a.repairs && a.observed_power==.2f,"baseline modified");
        require(parameter_hook::publish(object,true,{.99f,1.06f,2.34f,.98f,.95f,1.15f}),"publish");
        cycle(a);cycle(a);
        require(a.flame==.8f && a.repairs==2 && a.observed_power==2.34f && a.dt==.031 && !a.update,"combined delivery");
        cycle(other);require(other.flame==0 && !other.repairs && other.observed_power==.2f && other.table==table,"scope");
        std::thread foreign([&]{cycle(a);});foreign.join();
        require(a.flame==0 && a.repairs==2 && a.observed_power==2.34f,"foreign animation repair");
        require(parameter_hook::publish(object,false),"disable");
        cycle(a);require(a.flame==0 && a.repairs==2 && a.observed_power==.2f,"disable failed");
        require(std::string(parameter_hook::restore(object))=="parameter_hook_restored" && a.table==table,"restore");
        cycle(a);require(a.repairs==2,"post-restore repair");
        require(install()=="parameter_hook_installed","reinstall");
        require(parameter_hook::publish(object,true,{.99f,1.06f,2.34f,.98f,.95f,1.15f}),"publish again");
        require(std::string(parameter_hook::restore(object))=="parameter_hook_restored","manual stop restore");
        cycle(a);require(a.repairs==2 && a.observed_power==.2f,"manual stop left hooks");
        require(install()=="parameter_hook_installed","third install");
        parameter_hook::publish(object,true,{.99f,1.06f,2.34f,.98f,.95f,1.15f});
        a.table=table;
        parameter_hook::dispatch_animation(&a,.02,true);
        require(a.repairs==2,"repair after table replacement");
        require(std::string(parameter_hook::restore(object))=="parameter_hook_already_replaced" && a.table==table,"replacement restore");
        std::cout<<"PASS: combined getter/animation table, native re-entry, post-animation order, baseline, scope, thread and restoration\n";
    }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
}
