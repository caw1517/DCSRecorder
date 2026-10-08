// Loads the real formation controller with two playback objects and two takes,
// then drives its bridge: each runtime ID gets exactly the take it is assigned,
// and every command addresses only the aircraft owning that take.
// Usage: formation_assign_check <HornetFormationProbe.dll> <stub lua.dll> <take.txt>
#include <windows.h>
#include <cstdint>
#include <cstddef>
#include <array>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
#include "ed_object_access.h"
#include "../staged_playback.h"

struct lua_State {
    struct Value {int type;std::string text;double number;};
    std::vector<Value> arguments;
    std::string result;
};
namespace {
std::array<float,1024> lead_args{},wing_args{};
uint64_t lead_cookie=1,wing_cookie=2;
const auto lead=reinterpret_cast<ED_OBJECT_HANDLE>(&lead_cookie);
const auto wing=reinterpret_cast<ED_OBJECT_HANDLE>(&wing_cookie);
void require(bool condition,const std::string& message) {if(!condition)throw std::runtime_error(message);}
template<class T> T load(HMODULE dll,const char* name) {
    const auto value=GetProcAddress(dll,name);
    require(value!=nullptr,name);
    return reinterpret_cast<T>(value);
}
}
int main(int argc,char** argv) {
    if(argc!=4)return 2;
    namespace fs=std::filesystem;
    const fs::path dll_path=fs::absolute(argv[1]),tape=argv[3];
    const auto folder=fs::temp_directory_path()/("formation-assign-"+std::to_string(GetCurrentProcessId()));
    try {
        // A private module copy with its own bin/takes, so build outputs stay clean.
        fs::create_directories(folder/"takes");
        fs::copy_file(dll_path,folder/dll_path.filename());
        fs::copy_file(tape,folder/"takes/lead.txt");
        fs::copy_file(tape,folder/"takes/wing.txt");
        {std::ofstream extra(folder/"takes/wing.txt",std::ios::app);extra<<'\n';}
        fs::copy_file(tape,folder/"takes/lead-duplicate-name.bin"); // not a .txt: ignored
        const auto lead_token=staged_playback::fingerprint(folder/"takes/lead.txt");
        const auto wing_token=staged_playback::fingerprint(folder/"takes/wing.txt");
        require(lead_token && wing_token && lead_token!=wing_token,"distinct takes");

        require(LoadLibraryW(fs::absolute(argv[2]).c_str())!=nullptr,"stub lua.dll");
        const auto dll=LoadLibraryW((folder/dll_path.filename()).c_str());
        require(dll!=nullptr,"controller");
        const auto setup=load<PFN_ED_SETUP_OBJECT_API>(dll,"ed_setup_object_api");
        const auto create=load<PFN_ED_ON_OBJECT_CREATE>(dll,"ed_on_object_create");
        const auto destroy=load<PFN_ED_ON_OBJECT_DESTROY>(dll,"ed_on_object_destroy");
        const auto control=load<int(*)(lua_State*)>(dll,"dcs_release_control");
        ed_object_api_entry api{};
        api.ed_get_object_id=[](ED_OBJECT_HANDLE h)->uint64_t {return h==lead?16777472:h==wing?16777728:0;};
        api.ed_get_object_args=[](ED_OBJECT_HANDLE h)->ed_object_args {
            auto& args=h==lead?lead_args:wing_args;return {args.data(),args.size()};
        };
        api.ed_set_single_arg=[](ED_OBJECT_HANDLE h,int i,float v) {(h==lead?lead_args:wing_args).at(i)=v;};
        setup(&api);
        auto call=[&](const char* command,uint64_t token,double third) {
            lua_State L;
            L.arguments={{4,command,0},{3,"",staged_playback::high(token)},{3,"",staged_playback::low(token)},{3,"",third}};
            control(&L);return L.result;
        };
        require(call("assign",lead_token,16777472)=="REFUSED,object_or_package","assign before any object");
        create(lead,lead_cookie);create(wing,wing_cookie);

        require(call("inspect",lead_token,0)=="REFUSED,object_or_package","unassigned take answered");
        require(call("assign",lead_token,99)=="REFUSED,object_unavailable","unknown runtime ID");
        require(call("assign",0x123456789abcull,16777472)=="REFUSED,take_unavailable","unknown take");
        const auto lead_reply=call("assign",lead_token,16777472);
        require(lead_reply.rfind("ASSIGNED,",0)==0 && lead_reply.find(",16777472")!=std::string::npos,"lead assign: "+lead_reply);
        require(call("assign",lead_token,16777728)=="REFUSED,take_already_assigned","one take on two aircraft");
        require(call("assign",wing_token,16777472)=="REFUSED,object_already_assigned","reassigned aircraft");
        const auto wing_reply=call("assign",wing_token,16777728);
        require(wing_reply.rfind("ASSIGNED,",0)==0 && wing_reply.find(",16777728")!=std::string::npos,"wing assign: "+wing_reply);

        // Before any simulation neither is ready; each take reaches its own aircraft.
        const auto lead_generation=std::stoull(lead_reply.substr(9));
        const auto wing_generation=std::stoull(wing_reply.substr(9));
        require(lead_generation!=wing_generation,"per-aircraft generations");
        require(call("inspect",lead_token,0).rfind("WAIT,"+std::to_string(lead_generation)+",",0)==0,"lead inspect");
        require(call("inspect",wing_token,0).rfind("WAIT,"+std::to_string(wing_generation)+",",0)==0,"wing inspect");
        require(call("commit",lead_token,lead_generation)=="REFUSED,not_ready_or_consumed","unready commit");
        require(call("abort",lead_token,wing_generation)=="REFUSED,object_or_package","abort with the other's generation");

        // Aborting one aircraft fails only that aircraft.
        require(call("abort",lead_token,lead_generation)=="ABORTED,"+std::to_string(lead_generation),"lead abort");
        require(call("inspect",wing_token,0).rfind("WAIT,"+std::to_string(wing_generation)+",",0)==0,"wing survived lead abort");
        destroy(lead,lead_cookie);
        require(call("inspect",lead_token,0)=="REFUSED,object_or_package","destroyed aircraft still answered");
        require(call("inspect",wing_token,0).rfind("WAIT,",0)==0,"wing survived lead destruction");
        destroy(wing,wing_cookie);
        FreeLibrary(dll);
        std::error_code ignored;fs::remove_all(folder,ignored);
        std::cout<<"PASS: two aircraft of one module each take only their assigned recorded flight; refusals and per-aircraft abort/destroy isolate them. Offline bridge test; DCS validation pending.\n";
    } catch(const std::exception& e) {
        std::cerr<<e.what()<<'\n';std::error_code ignored;fs::remove_all(folder,ignored);return 1;
    }
}
