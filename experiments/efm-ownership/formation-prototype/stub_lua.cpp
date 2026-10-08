// Test-only lua.dll: the four C API calls the release bridge resolves, over a
// fixed argument list. Never installed; it lets a harness call the real bridge.
#include <cstddef>
#include <string>
#include <vector>

struct lua_State {
    struct Value {int type;std::string text;double number;};
    std::vector<Value> arguments;
    std::string result;
};
extern "C" {
__declspec(dllexport) int lua_type(lua_State* L,int index) {
    return index>=1 && index<=static_cast<int>(L->arguments.size())?L->arguments[index-1].type:-1;
}
__declspec(dllexport) const char* lua_tolstring(lua_State* L,int index,size_t* length) {
    const auto& value=L->arguments.at(index-1);
    if(length)*length=value.text.size();
    return value.text.c_str();
}
__declspec(dllexport) double lua_tonumber(lua_State* L,int index) {return L->arguments.at(index-1).number;}
__declspec(dllexport) void lua_pushlstring(lua_State* L,const char* text,size_t length) {L->result.assign(text,length);}
}
