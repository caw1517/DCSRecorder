// Two playback aircraft of one type share the shadow table but own their own
// motion callbacks, engine values, traces and restoration. Mock boundary test.
#include "../native_step_hook.h"
#include <iostream>
#include <stdexcept>
#include <string>
#include <thread>

namespace {
struct Aircraft {
    uintptr_t vptr=0;
    int native_calls=0,restores=0,animations=0;
    float power=0;
};
void require(bool condition,const char* message) {if(!condition)throw std::runtime_error(message);}
float rpm(void*,int,bool) {return .7f;}
float thrust(void*,int) {return .2f;}
float power(void* object,int engine) {
    return reinterpret_cast<native_step_hook::Scalar*>(static_cast<Aircraft*>(object)->vptr)[0xe0/8](object,engine);
}
void integrate(void* object) {
    auto& a=*static_cast<Aircraft*>(object);
    ++a.native_calls;a.power=power(object,1);
}
void animate(void* object,double,bool) {++static_cast<Aircraft*>(object)->animations;}
Aircraft& from(const void* handle) {return *reinterpret_cast<Aircraft*>(reinterpret_cast<uintptr_t>(handle)-8);}
void before(const void* handle) {++from(handle).restores;}
void other_before(const void* handle) {from(handle).restores+=100;}
void after_animation(const void*) {}
void step(Aircraft& a) {reinterpret_cast<native_step_hook::Step*>(a.vptr)[native_step_hook::step_slot](&a);}
hornet_engine::Values engine_state(double scale) {
    return {.8*scale,.7*scale,.5,.4,.99,1.066,2.34*scale,.98,.95,1.15};
}
}
int main() {
    try {
        std::array<uintptr_t,native_step_hook::slots+1> original{};
        original.fill(reinterpret_cast<uintptr_t>(&integrate));
        original[0]=0x12345678;
        original[native_step_hook::animation_slot+1]=reinterpret_cast<uintptr_t>(&animate);
        original[0xd8/8+1]=reinterpret_cast<uintptr_t>(&rpm);
        original[0xe0/8+1]=reinterpret_cast<uintptr_t>(&thrust);
        original[0xf0/8+1]=reinterpret_cast<uintptr_t>(&power);
        const auto table=reinterpret_cast<uintptr_t>(original.data()+1);
        native_step_hook::Engine getters{&rpm,&thrust,&power};
        Aircraft lead{table},wing{table},bystander{table};
        const auto a=reinterpret_cast<uintptr_t>(&lead),b=reinterpret_cast<uintptr_t>(&wing);
        auto install=[&](uintptr_t object,native_step_hook::Before callback) {
            return std::string(native_step_hook::install(object,table,&integrate,callback,nullptr,&animate,&after_animation,&getters));
        };
        require(install(a,&before)=="step_hook_installed","first owner");
        require(install(b,&before)=="step_hook_installed","second owner of the same type");
        require(lead.vptr==wing.vptr && lead.vptr==native_step_hook::table(),"owners share one shadow table");
        require(install(a,&before)=="step_hook_busy","double install");
        Aircraft third{table};
        require(std::string(native_step_hook::install(reinterpret_cast<uintptr_t>(&third),table,&integrate,&other_before,nullptr,
            &animate,&after_animation,&getters))=="step_hook_config_conflict","conflicting callbacks joined a live table");
        require(std::string(native_step_hook::install(reinterpret_cast<uintptr_t>(&third),table,&integrate,&before))==
            "step_hook_config_conflict","conflicting getter set joined a live table");
        require(third.vptr==table,"refused object changed");

        require(native_step_hook::publish_engine(a,engine_state(1)),"lead engine publish");
        require(native_step_hook::publish_engine(b,engine_state(.5)),"wing engine publish");
        step(lead);step(wing);step(bystander);
        require(lead.restores==1 && wing.restores==1 && bystander.restores==0,"each owner gets only its own callback");
        require(lead.power==2.34f && wing.power==1.17f && power(&bystander,1)==.2f,"per-object engine values");
        float foreign=0;std::thread sound([&]{foreign=power(&wing,1);});sound.join();
        require(foreign==1.17f,"sound-thread read uses the wing's values");
        std::thread foreign_step([&]{step(lead);});foreign_step.join();
        require(lead.restores==1,"callback ran on a foreign thread");

        uint64_t lost=0;
        const auto lead_trace=native_step_hook::drain_engine(a,lost);
        require(!lost && !lead_trace.empty(),"lead trace");
        const auto wing_trace=native_step_hook::drain_engine(b,lost);
        require(!lost && !wing_trace.empty(),"wing trace kept apart from the lead's");
        for(const auto& call:wing_trace)require(!call.overridden || call.returned!=2.34f,"lead value in wing trace");

        // Removing one aircraft leaves the other flying with its own state.
        require(std::string(native_step_hook::restore(a))=="step_hook_restored" && lead.vptr==table,"lead restore");
        require(std::string(native_step_hook::restore(a))=="step_hook_restore_owner_rejected","repeat restore");
        require(!native_step_hook::publish_engine(a,engine_state(1)),"removed owner republished");
        step(lead);step(wing);
        require(lead.restores==1 && wing.restores==2,"wing kept its callback after the lead left");
        require(lead.power==.2f && wing.power==1.17f,"engine override followed the wrong object");
        require(native_step_hook::recognizes(b,native_step_hook::table(),table) &&
                !native_step_hook::recognizes(a,native_step_hook::table(),table),"ownership recognition");

        // A replaced vptr (DCS destroyed the wing) is never overwritten.
        wing.vptr=table+8;
        require(std::string(native_step_hook::restore(b))=="step_hook_already_replaced" && wing.vptr==table+8,"replacement overwritten");
        wing.vptr=table;
        require(std::string(native_step_hook::restore(b))=="step_hook_inactive","no owners remain");
        // With no owners left the table may be rebuilt for a new configuration.
        require(std::string(native_step_hook::install(a,table,&integrate,&other_before))=="step_hook_installed","rebuild after last owner");
        step(lead);require(lead.restores==101,"rebuilt callback");
        require(std::string(native_step_hook::restore(a))=="step_hook_restored","final restore");
        std::cout<<"PASS: two owners share one shadow table with separate callbacks, engine values, traces and restoration. Mock boundary test; DCS validation pending.\n";
    } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
