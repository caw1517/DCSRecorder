#include "native_step_hook.h"
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <thread>

namespace {
struct Aircraft {
    uintptr_t vptr=0;
    double position=0,velocity=0;
    bool pending=false;
    int native_calls=0,restores=0;
    double stabilator=0;
    double animation_dt=0;bool animation_update=false;
};
void integrate(void* object) {
    auto& aircraft=*static_cast<Aircraft*>(object);
    aircraft.position+=aircraft.velocity*.02;
    ++aircraft.native_calls;
    aircraft.stabilator=0.01; // Observed pattern: native step replaces SDK animation.
}
void restore_stabilator(const void* handle) {
    auto& aircraft=*reinterpret_cast<Aircraft*>(reinterpret_cast<uintptr_t>(handle)-8);
    aircraft.stabilator=0.6;
}
void animate(void* object,double dt,bool update) {
    auto& a=*static_cast<Aircraft*>(object);a.stabilator=0.01;
    a.animation_dt=dt;a.animation_update=update;
}
void animation(Aircraft& a,double dt,bool update) {
    reinterpret_cast<native_step_hook::Animation*>(a.vptr)[native_step_hook::animation_slot](&a,dt,update);
}
void restore_command(const void* handle) {
    auto& aircraft=*reinterpret_cast<Aircraft*>(reinterpret_cast<uintptr_t>(handle)-8);
    if(aircraft.pending) {
        aircraft.velocity=-12; aircraft.pending=false; ++aircraft.restores;
    }
}
void step(Aircraft& a) {
    const auto fn=reinterpret_cast<native_step_hook::Step*>(a.vptr)[native_step_hook::step_slot];
    fn(&a);
}
void require(bool condition,const char* message) { if(!condition)throw std::runtime_error(message); }
float rpm(void*,int,bool){return .7f;}
float thrust(void*,int){return .2f;}
float power(void* object,int engine) {
    return reinterpret_cast<native_step_hook::Scalar*>(static_cast<Aircraft*>(object)->vptr)[0xe0/8](object,engine);
}
void engine_integrate(void* object) {
    integrate(object);
    // Native physics may call an overridden getter; the table lock must be free.
    static_cast<Aircraft*>(object)->stabilator=power(object,1);
}
}
int main() {
    try {
        std::array<uintptr_t,native_step_hook::slots+1> original{};
        original.fill(reinterpret_cast<uintptr_t>(&integrate));
        original[0]=0x12345678; // RTTI locator must be copied intact.
        const auto table=reinterpret_cast<uintptr_t>(original.data()+1);
        Aircraft controlled{table},other{table};
        controlled.pending=true;
        // Simulate the observed ordering: command -> native nose projection ->
        // physics. Without the interception the 12 m/s lateral component is lost.
        controlled.velocity=0; step(controlled);
        require(controlled.position==0,"fixture did not reproduce overwritten velocity");
        const auto installed=native_step_hook::install(reinterpret_cast<uintptr_t>(&controlled),table,&integrate,&restore_command);
        require(std::string(installed)=="step_hook_installed","install failed");
        const auto clone=reinterpret_cast<uintptr_t*>(controlled.vptr);
        require(clone[-1]==original[0],"RTTI locator changed");
        for(size_t i=0;i<native_step_hook::slots;++i)
            if(i!=native_step_hook::step_slot)require(clone[i]==original[i+1],"unrelated slot changed");
        require(original[native_step_hook::step_slot+1]==reinterpret_cast<uintptr_t>(&integrate),"shared table changed");
        controlled.velocity=0; step(controlled);
        require(std::abs(controlled.position+.24)<1e-12 && controlled.native_calls==2 && controlled.restores==1,
            "recorded component not restored before native integration");
        controlled.velocity=0; step(controlled);
        require(controlled.restores==1,"stale command reused");
        other.pending=true; step(other);
        require(other.restores==0 && other.vptr==table,"other aircraft modified");
        controlled.pending=true;
        std::thread foreign([&]{step(controlled);}); foreign.join();
        require(controlled.restores==1,"override ran on a different thread");
        require(std::string(native_step_hook::restore(reinterpret_cast<uintptr_t>(&other)))=="step_hook_restore_owner_rejected","wrong owner allowed restore");
        require(std::string(native_step_hook::restore(reinterpret_cast<uintptr_t>(&controlled)))=="step_hook_restored","restore failed");
        require(controlled.vptr==table,"original table not restored");
        controlled.velocity=0; step(controlled);
        require(controlled.restores==1,"override survived release");
        require(std::string(native_step_hook::install(reinterpret_cast<uintptr_t>(&controlled),table+8,&integrate,&restore_command))=="step_hook_object_rejected","wrong table accepted");
        require(std::string(native_step_hook::install(reinterpret_cast<uintptr_t>(&controlled),table,&integrate,&restore_command))=="step_hook_installed","reinstall failed");
        controlled.vptr=table+8; // DCS destruction/replacement owns this now.
        require(std::string(native_step_hook::restore(reinterpret_cast<uintptr_t>(&controlled)))=="step_hook_already_replaced" && controlled.vptr==table+8,"replacement table overwritten");
        controlled.vptr=table;
        require(std::string(native_step_hook::install(reinterpret_cast<uintptr_t>(&controlled),table,&integrate,nullptr,&restore_stabilator))=="step_hook_installed","stabilator install failed");
        step(controlled);
        require(controlled.stabilator==0.6,"native animation erased recorded stabilator");
        std::thread foreign_after([&]{step(controlled);}); foreign_after.join();
        require(controlled.stabilator==0.01,"post-step override ran on foreign thread");
        step(controlled);require(controlled.stabilator==0.6,"post-step override stopped unexpectedly");
        native_step_hook::restore(reinterpret_cast<uintptr_t>(&controlled));
        step(controlled);require(controlled.stabilator==0.01,"post-step override survived restoration");
        original[native_step_hook::animation_slot+1]=reinterpret_cast<uintptr_t>(&animate);
        require(std::string(native_step_hook::install(reinterpret_cast<uintptr_t>(&controlled),table,&integrate,&restore_command,nullptr,&animate,&restore_stabilator))=="step_hook_installed","combined install failed");
        controlled.velocity=0;controlled.pending=true;const auto prior=controlled.position;
        step(controlled);animation(controlled,0.037,false);
        require(std::abs(controlled.position-prior+.24)<1e-12 && controlled.stabilator==0.6,"motion and surfaces did not coexist");
        require(controlled.animation_dt==0.037 && !controlled.animation_update,"animation ABI changed");
        animation(controlled,0.011,true);require(controlled.stabilator==0.6 && controlled.animation_update,"repeat animation lost surfaces");
        const auto combined=reinterpret_cast<uintptr_t*>(controlled.vptr);
        for(size_t i=0;i<native_step_hook::slots;++i)
            if(i!=native_step_hook::step_slot && i!=native_step_hook::animation_slot)require(combined[i]==original[i+1],"combined table changed another slot");
        animation(other,0.02,true);require(other.stabilator==0.01,"combined repair changed other aircraft");
        std::thread foreign_animation([&]{animation(controlled,0.02,true);});foreign_animation.join();
        require(controlled.stabilator==0.01,"combined repair ran on foreign thread");
        native_step_hook::restore(reinterpret_cast<uintptr_t>(&controlled));
        require(controlled.vptr==table,"combined table did not restore");
        animation(controlled,0.02,true);require(controlled.stabilator==0.01,"combined repair survived release");
        original[native_step_hook::step_slot+1]=reinterpret_cast<uintptr_t>(&engine_integrate);
        original[0xd8/8+1]=reinterpret_cast<uintptr_t>(&rpm);
        original[0xe0/8+1]=reinterpret_cast<uintptr_t>(&thrust);
        original[0xf0/8+1]=reinterpret_cast<uintptr_t>(&power);
        native_step_hook::Engine getters{&rpm,&thrust,&power};
        const auto object=reinterpret_cast<uintptr_t>(&controlled);
        require(std::string(native_step_hook::install(object,table,&engine_integrate,&restore_command,nullptr,&animate,&restore_stabilator,&getters))=="step_hook_installed","engine integration install");
        require(power(&controlled,1)==.2f,"engine baseline changed");
        hornet_engine::Values captured{.8,.7,.5,.4,.99,1.066,2.34,.98,.95,1.15};
        require(native_step_hook::publish_engine(object,captured),"engine publish");
        controlled.pending=true;controlled.velocity=0;
        const auto before_engine=controlled.position;step(controlled);
        require(std::abs(controlled.position-before_engine+.24)<1e-12 && controlled.stabilator==2.34f,"motion/getter reentry");
        animation(controlled,.02,true);require(controlled.stabilator==.6,"animation coexistence");
        require(power(&controlled,2)==1.15f && power(&other,1)==.2f,"independent engine/object scope");
        float foreign_value=0;std::thread sound([&]{foreign_value=power(&controlled,1);});sound.join();
        require(foreign_value==2.34f,"sound-thread read");
        const auto all=reinterpret_cast<uintptr_t*>(controlled.vptr);
        for(size_t i=0;i<native_step_hook::slots;++i)
            if(i!=native_step_hook::step_slot && i!=native_step_hook::animation_slot && i!=0xd8/8 && i!=0xe0/8)
                require(all[i]==original[i+1],"engine table changed unrelated slot");
        uint64_t lost=0;auto trace=native_step_hook::drain_engine(lost);require(!lost && !trace.empty(),"engine trace");
        require(std::string(native_step_hook::restore(object))=="step_hook_restored" && controlled.vptr==table,"all-four-slot restore");
        require(power(&controlled,1)==.2f,"engine override survived restore");
        std::cout<<"PASS: motion, animation and engine getter boundaries coexist, preserve ownership and restore together. Mock boundary test; DCS validation pending.\n";
    } catch(const std::exception& e) { std::cerr<<e.what()<<'\n';return 1; }
}
