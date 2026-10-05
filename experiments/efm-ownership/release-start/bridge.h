// Included only by object_probe.cpp's separate release-control target.
struct lua_State;
extern "C" __declspec(dllexport) int dcs_release_control(lua_State* lua_state) {
    const auto lua=GetModuleHandleW(L"lua.dll");
    using Push=void(*)(lua_State*,const char*,size_t);
    using Text=const char*(*)(lua_State*,int,size_t*);
    using Number=double(*)(lua_State*,int);
    using Type=int(*)(lua_State*,int);
    const auto push=reinterpret_cast<Push>(lua?GetProcAddress(lua,"lua_pushlstring"):nullptr);
    const auto text=reinterpret_cast<Text>(lua?GetProcAddress(lua,"lua_tolstring"):nullptr);
    const auto number=reinterpret_cast<Number>(lua?GetProcAddress(lua,"lua_tonumber"):nullptr);
    const auto type=reinterpret_cast<Type>(lua?GetProcAddress(lua,"lua_type"):nullptr);
    if(!push || !text || !number || !type)return 0;
    std::string reply="REFUSED,arguments";
    try {
        std::lock_guard<std::mutex> guard(lock);
        const char* raw=type(lua_state,1)==4?text(lua_state,1,nullptr):nullptr;
        if(raw && type(lua_state,2)==3 && type(lua_state,3)==3 && type(lua_state,4)==3) {
            const std::string command=raw;
            const double high=number(lua_state,2),low=number(lua_state,3),generation=number(lua_state,4);
            reply="REFUSED,object_or_package";
            if(observed.size()==1) {
                auto& entry=*observed.begin();auto& state=entry.second;
                if(state.token && high==staged_playback::high(state.token) && low==staged_playback::low(state.token) &&
                   (command=="inspect" || generation==static_cast<double>(state.generation))) {
                    const bool ready=state.motion_active && !state.terminal && state.step_hook && state.step_applied>0 &&
                        state.exterior_pending && state.exterior_applied>0 && state.clock.phase==release_start::Clock::Phase::held;
                    std::ostringstream result;result<<std::setprecision(17);
                    if(command=="inspect") {
                        result<<(ready?"READY":"WAIT")<<','<<state.generation<<','<<state.clock.last<<','<<state.clock.elapsed;
                    } else if(command=="commit" && state.clock.commit(ready)) {
                        result<<"COMMITTED,"<<state.generation<<','<<state.clock.last;
                        log_file<<"release_committed,"<<state.runtime_id<<','<<state.generation<<','<<state.clock.last<<','<<state.calls<<",1\n";
                        log_file.flush();
                    } else if(command=="abort") {
                        state.clock.phase=release_start::Clock::Phase::failed;
                        state.motion_active=false;state.motion_attempted=true;stop_native_step(entry.first,state);
                        staged_playback::publish(api,entry.first,state.token,staged_playback::failed);
                        result<<"ABORTED,"<<state.generation;
#ifdef HORNET_FAULT_INJECTION
                    } else if((command=="fault_clock" || command=="fault_state") && !state.terminal) {
                        (command=="fault_clock"?state.fault_clock:state.fault_state)=true;
                        log_file<<command<<"_injected,"<<state.runtime_id<<','<<state.generation<<','<<state.clock.last<<','<<state.calls<<",1\n";
                        log_file.flush();
                        result<<"FAULT_ARMED,"<<state.generation<<','<<command;
#endif
                    } else result<<"REFUSED,not_ready_or_consumed";
                    reply=result.str();
                }
            }
        }
    } catch(...) {reply="REFUSED,bridge_exception";}
    push(lua_state,reply.data(),reply.size());return 1;
}
