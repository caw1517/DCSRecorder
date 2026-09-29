// Exercise the real wheel repair callback and native dispatcher against the
// overwrite values observed in the saved live trace. Not a renderer substitute.
#include "../state-prototype/playback.cpp"
#include <iostream>
#include <stdexcept>

namespace {
struct Aircraft { uintptr_t table; std::array<float,1000> args{}; int calls=0; };
Aircraft* fixture=nullptr;
void require(bool ok,const char* why) {if(!ok)throw std::runtime_error(why);}
void animate(void* pointer,double,bool) {
    auto& a=*static_cast<Aircraft*>(pointer);++a.calls;
    for(int c:{0,5,3})a.args[c]=.994979978f;
    for(int c:{101,103,102})a.args[c]=0;
    a.args[2]-=.015060067f;
}
}
int main(int argc,char**) {
    try {
        std::array<uintptr_t,native_animation_hook::slots+1> original{};
        original[native_animation_hook::step_slot+1]=reinterpret_cast<uintptr_t>(&animate);
        const auto table=reinterpret_cast<uintptr_t>(original.data()+1);
        Aircraft aircraft{table};fixture=&aircraft;
        const auto pointer=reinterpret_cast<uintptr_t>(&aircraft);
        auto handle=reinterpret_cast<ED_OBJECT_HANDLE>(pointer+8);
        ed_object_api_entry sdk{};
        sdk.ed_get_object_id=[](ED_OBJECT_HANDLE){return uint64_t(42);};
        sdk.ed_get_object_args=[](ED_OBJECT_HANDLE)->ed_object_args{return {fixture->args.data(),fixture->args.size()};};
        sdk.ed_set_single_arg=[](ED_OBJECT_HANDLE,int c,float v){fixture->args.at(c)=v;};
        api=&sdk;
        Object state;state.id=42;state.valid=true;state.pending=true;
        state.requested={1,1,1,.75f,.84f,.83f,.3f,.6f,.9f,-.7f};
        objects[handle]=state;
        const auto logfile=std::filesystem::temp_directory_path()/("wheel-repair-check-"+std::to_string(GetCurrentProcessId())+".csv");
        post_trace.open(logfile);
        for(size_t i=0;i<channels.size();++i)aircraft.args[channels[i]]=state.requested[i];
        if(argc==1)require(std::string(native_animation_hook::install(pointer,table,&animate,nullptr,&after_native_step))=="animation_hook_installed","hook install failed");
        for(int repeat=0;repeat<3;++repeat) {
            reinterpret_cast<native_animation_hook::Step*>(aircraft.table)[native_animation_hook::step_slot](&aircraft,.02,true);
            for(size_t i=0;i<channels.size();++i)require(aircraft.args[channels[i]]==state.requested[i],"FAIL: later animation erased a requested wheel state");
        }
        require(objects[handle].repaired==3 && aircraft.calls==3,"repair dispatch count mismatch");
        objects[handle].pending=false;
        reinterpret_cast<native_animation_hook::Step*>(aircraft.table)[native_animation_hook::step_slot](&aircraft,.02,true);
        require(aircraft.args[101]==0 && objects[handle].repaired==3,"inactive repair wrote values");
        require(std::string(native_animation_hook::restore(pointer))=="animation_hook_restored" && aircraft.table==table,"restore failed");
        post_trace.close();std::filesystem::remove(logfile);
        std::cout<<"PASS: real wheel callback survives repeated native animation overwrites; pending guard and hook restore\n";
    } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
