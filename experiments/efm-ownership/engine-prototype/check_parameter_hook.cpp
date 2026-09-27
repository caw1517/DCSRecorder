#include "parameter_hook.h"
#include <iostream>
#include <stdexcept>
#include <thread>
#include <limits>
struct Aircraft {uintptr_t table;parameter_hook::Values values{.7f,.4f,.2f,.8f,.5f,.3f};};
float rpm(void* p,int engine,bool core) {
    auto&a=*static_cast<Aircraft*>(p);
    return engine>=1&&engine<=2?a.values[(engine-1)*3+(core?0:1)]:.12f;
}
float thrust(void* p,int engine) {
    auto&a=*static_cast<Aircraft*>(p);return engine>=1&&engine<=2?a.values[(engine-1)*3+2]:0;
}
float power(void* p,int engine) {
    const auto table=static_cast<Aircraft*>(p)->table;
    return reinterpret_cast<parameter_hook::Thrust*>(table)[parameter_hook::thrust_slot](p,engine);
}
float read(Aircraft& a,int engine,int channel) {
    if(channel<2)return reinterpret_cast<parameter_hook::Getter*>(a.table)[parameter_hook::slot](&a,engine,channel==0);
    return reinterpret_cast<parameter_hook::Thrust*>(a.table)[channel==2?parameter_hook::thrust_slot:parameter_hook::power_slot](&a,engine);
}
void require(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
int main() {
    try {
        std::array<uintptr_t,parameter_hook::slots+1> entries{};entries[0]=0x12345678;
        entries[parameter_hook::slot+1]=reinterpret_cast<uintptr_t>(&rpm);
        entries[parameter_hook::thrust_slot+1]=reinterpret_cast<uintptr_t>(&thrust);
        entries[parameter_hook::power_slot+1]=reinterpret_cast<uintptr_t>(&power);
        auto table=reinterpret_cast<uintptr_t>(entries.data()+1);
        Aircraft a{table},b{table};auto object=reinterpret_cast<uintptr_t>(&a);
        require(std::string(parameter_hook::install(object,table,&rpm,&thrust,&power))=="parameter_hook_installed","install");
        for(size_t i=0;i<parameter_hook::slots;++i)
            if(i!=parameter_hook::slot&&i!=parameter_hook::thrust_slot)
                require(reinterpret_cast<uintptr_t*>(a.table)[i]==entries[i+1],"unrelated slot changed");
        require(reinterpret_cast<uintptr_t*>(a.table)[-1]==entries[0],"RTTI changed");
        for(int e=1;e<=2;++e)for(int c=0;c<4;++c)require(read(a,e,c)==a.values[(e-1)*3+(c==3?2:c)],"baseline");
        parameter_hook::Values captured{.99f,1.066f,2.34f,.98f,.95f,1.15f};
        require(parameter_hook::publish(object,true,captured),"publish");
        for(int e=1;e<=2;++e)for(int c=0;c<4;++c)require(read(a,e,c)==captured[(e-1)*3+(c==3?2:c)],"channel mapping or clamping");
        require(read(a,0,0)==.12f && read(a,3,2)==0 && b.table==table && read(b,1,2)==.2f,"scope");
        float threaded=0;std::thread t([&]{threaded=read(a,1,3);});t.join();require(threaded==2.34f,"sound thread");
        uint64_t lost=0;auto calls=parameter_hook::drain(lost);
        require(!lost && calls.size()==19,"trace count");
        require(calls[10].channel==2 && calls[10].original==.2f && calls[10].returned==2.34f,"thrust observation");
        captured[2]=std::numeric_limits<float>::quiet_NaN();require(!parameter_hook::publish(object,true,captured),"NaN accepted");
        require(read(a,1,3)==.2f,"bad data kept override");
        require(std::string(parameter_hook::restore(object))=="parameter_hook_restored"&&a.table==table,"restore");
        require(parameter_hook::dispatch_thrust(&a,1)==.2f,"stale dispatch");
        require(std::string(parameter_hook::install(object,table,&rpm,&thrust,&power))=="parameter_hook_installed","reinstall");
        a.table=table+8;require(!parameter_hook::publish(object,true),"changed table");
        require(std::string(parameter_hook::restore(object))=="parameter_hook_already_replaced"&&a.table==table+8,"third-party table overwritten");
        std::cout<<"PASS: six measured channels, values above one, forwarded F0 power, independent engines, baseline/restore, thread reads and scope\n";
    }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
}
