#include "rpm_hook.h"
#include <iostream>
#include <stdexcept>
#include <thread>
#include <limits>
struct Aircraft {uintptr_t table;float core[2]{0.7f,0.8f},fan[2]{0.4f,0.5f};};
float original(void* p,int engine,bool core) {
    auto&a=*static_cast<Aircraft*>(p);
    return engine>=1 && engine<=2?(core?a.core[engine-1]:a.fan[engine-1]):0.12f;
}
float call(Aircraft& a,int engine,bool core) {
    return reinterpret_cast<rpm_hook::Getter*>(a.table)[rpm_hook::slot](&a,engine,core);
}
void require(bool good,const char* why){if(!good)throw std::runtime_error(why);}
int main() {
    try {
        std::array<uintptr_t,rpm_hook::slots+1> entries{};entries[0]=0x12345678;
        entries[rpm_hook::slot+1]=reinterpret_cast<uintptr_t>(&original);
        const auto table=reinterpret_cast<uintptr_t>(entries.data()+1);
        Aircraft a{table},b{table};const auto object=reinterpret_cast<uintptr_t>(&a);
        require(std::string(rpm_hook::install(object,table,&original))=="rpm_hook_installed","install");
        auto clone=reinterpret_cast<uintptr_t*>(a.table);
        for(size_t i=0;i<rpm_hook::slots;++i)if(i!=rpm_hook::slot)require(clone[i]==entries[i+1],"other slot changed");
        require(clone[-1]==entries[0] && b.table==table,"RTTI or other object changed");
        require(call(a,1,true)==0.7f && call(a,2,true)==0.8f,"baseline not forwarded");
        require(rpm_hook::publish(object,true,0.9f,0.95f),"publish");
        require(call(a,1,true)==0.9f && call(a,2,true)==0.95f,"recorded core not returned");
        require(call(a,1,false)==0.4f && call(a,2,false)==0.5f && call(a,0,true)==0.12f && call(a,3,true)==0.12f,"unrecorded input changed");
        require(call(b,1,true)==0.7f,"other aircraft changed");
        float threaded=0;std::thread reader([&]{threaded=call(a,2,true);});reader.join();
        require(threaded==0.95f,"sound-thread read failed");
        require(!rpm_hook::publish(object,true,std::numeric_limits<float>::quiet_NaN(),0.9f),"NaN accepted");
        require(call(a,1,true)==0.7f,"bad input did not disable override");
        require(!rpm_hook::publish(reinterpret_cast<uintptr_t>(&b),true,0.2f,0.2f),"wrong owner accepted");
        uint64_t lost=0;auto observed=rpm_hook::drain(lost);
        require(lost==0 && observed.size()==10,"call observations missing");
        require(observed[2].original==0.7f && observed[2].returned==0.9f && observed[2].overridden,"original/returned trace incorrect");
        require(std::string(rpm_hook::restore(object))=="rpm_hook_restored" && a.table==table,"restore");
        require(call(a,1,true)==0.7f && rpm_hook::dispatch(&a,1,true)==0.7f,"stale dispatch changed value");
        require(std::string(rpm_hook::install(object,table,&original))=="rpm_hook_installed","reinstall");
        a.table=table+8;
        require(!rpm_hook::publish(object,true,0.8f,0.8f),"replacement table accepted");
        require(std::string(rpm_hook::restore(object))=="rpm_hook_already_replaced" && a.table==table+8,"replacement overwritten");
        require(std::string(rpm_hook::install(object,table,&original))=="rpm_object_rejected","bad table accepted");
        std::cout << "PASS: baseline/replay, core-only scope, caller observations, concurrent reads, invalid input and restoration\n";
    } catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
}
