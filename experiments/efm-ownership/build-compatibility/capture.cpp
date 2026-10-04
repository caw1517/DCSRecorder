// Read-only build evidence: no native method calls, object writes or hooks.
#include "../static_image_snapshot.h"
#include <sstream>
struct lua_State;
using Push=void(*)(lua_State*,const char*,size_t);
namespace {
std::string capture() {
    wchar_t host[32768]{};
    if(!GetModuleFileNameW(nullptr,host,32768) ||
       _wcsicmp(std::filesystem::path(host).filename().c_str(),L"DCS.exe"))
        return "UNAVAILABLE,not_dcs";
    HMODULE self=nullptr;wchar_t path[32768]{};
    if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
        reinterpret_cast<LPCWSTR>(&capture),&self) || !GetModuleFileNameW(self,path,32768))return "UNAVAILABLE,self_path";
    const auto root=std::filesystem::path(path).parent_path()/("evidence-"+std::to_string(GetCurrentProcessId()));
    if(std::filesystem::exists(root))return "UNAVAILABLE,evidence_already_exists";
    std::filesystem::create_directories(root);
    const std::pair<const wchar_t*,const char*> modules[]={
        {nullptr,"dcs"},{L"WorldGeneral.dll","worldgeneral"},{L"Sound.dll","sound"},
        {L"AIFM.dll","aifm"},{L"CockpitBase.dll","cockpit"}};
    for(const auto& module:modules) {
        if(!GetModuleHandleW(module.first))return std::string("UNAVAILABLE,module_missing,")+module.second;
        const auto folder=root/module.second;
        std::filesystem::create_directory(folder);
        snapshot_static_image(folder,module.first);
        const auto result=folder/((module.first?"worldgeneral-static-":"static-image-")+std::to_string(GetCurrentProcessId()));
        std::ifstream manifest(result/"sections.txt");std::string line;unsigned sections=0;
        while(std::getline(manifest,line)) {
            if(line.rfind("section ",0)==0)++sections;
            if(line.rfind("skip ",0)==0 || line.rfind("unreadable ",0)==0)return std::string("UNAVAILABLE,partial,")+module.second;
        }
        if(sections!=3)return std::string("UNAVAILABLE,section_count,")+module.second;
    }
    return "CAPTURED,modules=5,read_only_sections=15";
}
}
extern "C" __declspec(dllexport) int dcs_build_capture(lua_State* state) {
    auto lua=GetModuleHandleW(L"lua.dll");
    auto push=reinterpret_cast<Push>(lua?GetProcAddress(lua,"lua_pushlstring"):nullptr);
    if(!push)return 0;
    std::string result;
    try { result=capture(); } catch(...) {result="UNAVAILABLE,capture_exception";}
    push(state,result.data(),result.size());return 1;
}
