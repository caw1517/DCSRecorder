#pragma once
// Read-only MSVC x64 RTTI inspection. Layouts follow the installed MSVC
// rttidata.h and CRT rtti.cpp. No private DCS methods or member offsets are used.
#include <windows.h>
#include <cstdint>
#include <string>
#include <vector>
#include "native_build.h"

namespace native_identity {
struct Base { std::string name; int32_t member, vbtable, vbdisp; uint32_t attributes; };
struct Result {
    std::string status = "unreadable_vtable", module, name;
    uint32_t subobject_offset = 0;
    std::vector<Base> bases;
};
template<class T> bool read(uintptr_t address, T& value) {
    SIZE_T count = 0;
    return address && ReadProcessMemory(GetCurrentProcess(), reinterpret_cast<const void*>(address),
        &value, sizeof(value), &count) && count == sizeof(value);
}
struct Locator { uint32_t signature, offset, construction; int32_t type, hierarchy, self; };
struct Hierarchy { uint32_t signature, attributes, count; int32_t array; };
struct BaseDescriptor {
    int32_t type; uint32_t contained;
    int32_t member, vbtable, vbdisp;
    uint32_t attributes;
};
static_assert(sizeof(Locator) == 24 && sizeof(Hierarchy) == 16 && sizeof(BaseDescriptor) == 24);

inline Result inspect(const void* object) {
    Result out;
    uintptr_t vtable = 0, locator_address = 0;
    if (!read(reinterpret_cast<uintptr_t>(object), vtable) || vtable < sizeof(uintptr_t) ||
        !read(vtable-sizeof(uintptr_t), locator_address)) return out;
    MEMORY_BASIC_INFORMATION region{};
    if (!VirtualQuery(reinterpret_cast<void*>(locator_address), &region, sizeof(region)) ||
        region.Type != MEM_IMAGE) { out.status="locator_not_in_image"; return out; }
    const auto image = reinterpret_cast<uintptr_t>(region.AllocationBase);
    IMAGE_DOS_HEADER dos{}; IMAGE_NT_HEADERS64 pe{};
    if (!read(image,dos) || dos.e_magic != IMAGE_DOS_SIGNATURE || dos.e_lfanew < 0 ||
        !read(image+dos.e_lfanew,pe) || pe.Signature != IMAGE_NT_SIGNATURE ||
        pe.OptionalHeader.Magic != IMAGE_NT_OPTIONAL_HDR64_MAGIC) {
        out.status="invalid_image"; return out;
    }
    const auto size = pe.OptionalHeader.SizeOfImage;
    auto within=[&](uintptr_t address,size_t length) {
        return address >= image && length <= size && address-image <= size-length;
    };
    auto rva=[&](int32_t offset,size_t length)->uintptr_t {
        return offset > 0 && within(image+static_cast<uint32_t>(offset),length)
            ? image+static_cast<uint32_t>(offset) : 0;
    };
    Locator locator{};
    if (!within(locator_address,sizeof(locator)) || !read(locator_address,locator) ||
        locator.signature != 1 || rva(locator.self,sizeof(locator)) != locator_address) {
        out.status="unsupported_locator"; return out;
    }
    auto type_name=[&](int32_t offset) {
        std::string name;
        auto address=rva(offset,17); // TypeDescriptor: two pointers, then name.
        if (!address) return name;
        for (size_t i=0; i<256; ++i) {
            char c=0;
            if (!within(address+16+i,1) || !read(address+16+i,c)) return std::string{};
            if (!c) return name;
            if (static_cast<unsigned char>(c)<32 || static_cast<unsigned char>(c)>126) return std::string{};
            name+=c;
        }
        return std::string{};
    };
    out.name=type_name(locator.type);
    out.subobject_offset=locator.offset;
    char module_path[32768]{};
    if (GetModuleFileNameA(reinterpret_cast<HMODULE>(image),module_path,sizeof(module_path))) {
        out.module=module_path;
        out.module=out.module.substr(out.module.find_last_of("/\\")+1);
    }
    Hierarchy hierarchy{};
    if (out.name.empty() || !read(rva(locator.hierarchy,sizeof(hierarchy)),hierarchy) ||
        hierarchy.count==0 || hierarchy.count>128) { out.status="invalid_hierarchy"; return out; }
    auto array=rva(hierarchy.array,hierarchy.count*sizeof(int32_t));
    if (!array) { out.status="invalid_base_array"; return out; }
    for (uint32_t i=0; i<hierarchy.count; ++i) {
        int32_t offset=0; BaseDescriptor base{};
        if (!read(array+i*sizeof(offset),offset) || !read(rva(offset,sizeof(base)),base)) {
            out.status="unreadable_base"; return out;
        }
        auto name=type_name(base.type);
        if (name.empty()) { out.status="invalid_base_name"; return out; }
        out.bases.push_back({name,base.member,base.vbtable,base.vbdisp,base.attributes});
    }
    out.status="ok";
    return out;
}
}
