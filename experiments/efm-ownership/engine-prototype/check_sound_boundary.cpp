// Boundary checks only; this does not test DCS audio rendering.
#include "sound_boundary.h"
#include <iostream>
#include <sstream>
#include <stdexcept>

void require(bool value) {if(!value)throw std::runtime_error("sound boundary check failed");}
int main() {
    using namespace sound_boundary;
    std::array<unsigned char,16> code{0xf3,0x0f,0x10,0x81,0x20,1,0,0,0xc3};
    require(direct_float_offset(code)==0x120);
    code[8]=0x90;require(direct_float_offset(code)==-1);
    code={0xf3,0x0f,0x10,0x41,0x20,0xc3};require(direct_float_offset(code)==0x20);
    code[4]=0xff;require(direct_float_offset(code)==-1);
    code={0xf3,0x0f,0x10,0x81,0xff,0xff,0xff,0x7f,0xc3};require(direct_float_offset(code)==-1);
    struct String {std::array<char,16> data{};uint64_t size=0,capacity=15;} storage;
    std::string name="unchanged";
    require(name_at(reinterpret_cast<uintptr_t>(&storage),name) && name.empty());
    std::memcpy(storage.data.data(),"short",6);storage.size=5;
    require(name_at(reinterpret_cast<uintptr_t>(&storage),name) && name=="short");
    const std::string long_name="Aircraft/Planes/DCSRecorderSounderTest";
    const auto pointer=long_name.c_str();std::memcpy(storage.data.data(),&pointer,sizeof(pointer));
    storage.size=storage.capacity=long_name.size();
    require(name_at(reinterpret_cast<uintptr_t>(&storage),name) && name==long_name);
    storage.size=161;require(!name_at(reinterpret_cast<uintptr_t>(&storage),name));
    require(!name_at(0,name));
    require(!layout_matches(0,0));
    std::ostringstream output;sample(output,nullptr,1,0);
    require(output.str().find("identity_rejected")!=std::string::npos);
    std::cout << "PASS: bounded strings, getter decoding and invalid-handle rejection; no audio claim\n";
}
