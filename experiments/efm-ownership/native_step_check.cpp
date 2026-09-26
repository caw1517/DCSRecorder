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
};
void integrate(void* object) {
    auto& aircraft=*static_cast<Aircraft*>(object);
    aircraft.position+=aircraft.velocity*.02;
    ++aircraft.native_calls;
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
        std::cout<<"PASS: per-object dispatch restores lost velocity before integration, preserves native calls/RTTI/other slots, consumes commands once, rejects foreign threads, restores ownership. Mock boundary test; DCS validation pending.\n";
    } catch(const std::exception& e) { std::cerr<<e.what()<<'\n';return 1; }
}
