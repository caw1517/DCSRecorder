#pragma once
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#ifndef DCSR_GROUND_TAPE_TOKEN
#error The ground experiment must be built for one reviewed tape fingerprint
#endif
namespace ground_trial {
inline bool speed_allowed(double squared) {return std::isfinite(squared) && squared>=0 && squared<=25;}
inline bool tape_allowed(const std::filesystem::path& path) {
    std::ifstream stream(path,std::ios::binary);
    if(!stream)return false;
    uint64_t hash=14695981039346656037ull;char c;
    while(stream.get(c)){hash^=static_cast<unsigned char>(c);hash*=1099511628211ull;}
    return !stream.bad() && hash==static_cast<uint64_t>(DCSR_GROUND_TAPE_TOKEN);
}
}
