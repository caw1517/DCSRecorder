#pragma once
#include <windows.h>
#include <filesystem>
#include <fstream>
#include <vector>
#include "native_identity.h"

// Capture executable/read-only sections only, never mutable .data, heap,
// accounts, or a whole-process dump. The installed executable is untouched.
inline void snapshot_static_image(const std::filesystem::path& log_folder,
                                  const wchar_t* module_name=nullptr) {
    const auto image=reinterpret_cast<uintptr_t>(GetModuleHandleW(module_name));
    IMAGE_DOS_HEADER dos{}; IMAGE_NT_HEADERS64 pe{};
    if (!native_identity::read(image,dos) || dos.e_magic!=IMAGE_DOS_SIGNATURE ||
        dos.e_lfanew<0 || !native_identity::read(image+dos.e_lfanew,pe) ||
        pe.Signature!=IMAGE_NT_SIGNATURE || pe.OptionalHeader.Magic!=IMAGE_NT_OPTIONAL_HDR64_MAGIC ||
        pe.FileHeader.NumberOfSections>64) return;
    const auto prefix=module_name ? "worldgeneral-static-" : "static-image-";
    const auto folder=log_folder/(prefix+std::to_string(GetCurrentProcessId()));
    std::error_code error;
    std::filesystem::create_directories(folder,error);
    if(error) return;
    std::ofstream manifest(folder/"sections.txt");
    manifest << "image_base " << std::hex << image << '\n';
    auto section_table=image+dos.e_lfanew+24+pe.FileHeader.SizeOfOptionalHeader;
    for(unsigned i=0;i<pe.FileHeader.NumberOfSections;++i) {
        IMAGE_SECTION_HEADER section{};
        if(!native_identity::read(section_table+i*sizeof(section),section)) continue;
        const std::string name(reinterpret_cast<const char*>(section.Name),
            strnlen(reinterpret_cast<const char*>(section.Name),8));
        if(name!=".text" && name!=".rdata" && name!=".pdata") continue;
        const auto size=section.Misc.VirtualSize;
        if(!size || size>64*1024*1024 || section.VirtualAddress>pe.OptionalHeader.SizeOfImage ||
            size>pe.OptionalHeader.SizeOfImage-section.VirtualAddress ||
            (section.Characteristics & IMAGE_SCN_MEM_WRITE)) {
            manifest << "skip " << name << '\n'; continue;
        }
        std::vector<char> bytes(size);
        SIZE_T read_size=0;
        if(!ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(image+section.VirtualAddress),
            bytes.data(),bytes.size(),&read_size) || read_size!=bytes.size()) {
            manifest << "unreadable " << name << '\n'; continue;
        }
        std::ofstream file(folder/(name.substr(1)+".bin"),std::ios::binary);
        file.write(bytes.data(),bytes.size());
        if(file) manifest << "section " << name << ' ' << section.VirtualAddress << ' ' << size << '\n';
    }
}
