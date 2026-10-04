from pathlib import Path
root=Path(r'C:\Users\w_can\.codex\worktrees\airborne-staging\DCS_Recorder\experiments\efm-ownership')
header=r'''#pragma once
#include "native_identity.h"
#include <array>
#include <cmath>

// Build-specific staged-playback experiment. The recorded basis already
// contains nose attitude; the null-FM presentation path adds these two fields.
// Caller owns the guarded aircraft and simulation thread, and invokes this
// immediately before native integration, after the normal controller update.
namespace native_presentation_pitch {
constexpr uintptr_t pitch_offset=0x4db4,rate_offset=0x22b4;
struct State { uintptr_t owner=0;float pitch=0,rate=0;bool active=false; };
inline bool put(uintptr_t p,float value) {
    SIZE_T written=0;
    return WriteProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(p),&value,sizeof(value),&written)
        && written==sizeof(value);
}
inline bool read_pair(uintptr_t p,float& pitch,float& rate) {
    return native_identity::read(p+pitch_offset,pitch) && native_identity::read(p+rate_offset,rate);
}
inline bool layout_valid() {
    const auto image=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    std::array<unsigned char,8> a{},b{};
    return native_identity::read(image+0x6d41eb,a) &&
        a==std::array<unsigned char,8>{0xf3,0x0f,0x10,0x8e,0xb4,0x4d,0,0} &&
        native_identity::read(image+0x6d41f6,b) &&
        b==std::array<unsigned char,8>{0xf3,0x0f,0x10,0x86,0xb4,0x22,0,0};
}
inline const char* clear_validated(const void* handle,State& state) {
    const auto p=reinterpret_cast<uintptr_t>(handle);
    if(!p || (state.active && state.owner!=p))return "presentation_owner_rejected";
    float pitch=0,rate=0;
    if(!read_pair(p,pitch,rate) || !std::isfinite(pitch) || !std::isfinite(rate) ||
       std::abs(pitch)>45 || std::abs(rate)>2000)return "presentation_fields_rejected";
    if(!put(p+pitch_offset,0) || !put(p+rate_offset,0)) {
        const bool restored_pitch=put(p+pitch_offset,pitch);
        const bool restored_rate=put(p+rate_offset,rate);
        return restored_pitch && restored_rate ? "presentation_write_failed" : "presentation_rollback_failed";
    }
    float check_pitch=1,check_rate=1;
    if(!read_pair(p,check_pitch,check_rate) || check_pitch!=0 || check_rate!=0) {
        const bool restored_pitch=put(p+pitch_offset,pitch);
        const bool restored_rate=put(p+rate_offset,rate);
        return restored_pitch && restored_rate ? "presentation_readback_failed" : "presentation_rollback_failed";
    }
    if(!state.active || pitch!=0 || rate!=0) {state.pitch=pitch;state.rate=rate;}
    state.owner=p;state.active=true;return "called";
}
inline const char* restore(const void* handle,State& state) {
    if(!state.active)return "presentation_inactive";
    const auto p=reinterpret_cast<uintptr_t>(handle);
    if(p!=state.owner)return "presentation_restore_owner_rejected";
    float pitch=0,rate=0;
    if(!read_pair(p,pitch,rate))return "presentation_restore_unreadable";
    // If DCS has already replaced either field, preserve its newer state.
    if(pitch!=0 || rate!=0) {state={};return "presentation_already_replaced";}
    if(!put(p+pitch_offset,state.pitch) || !put(p+rate_offset,state.rate))return "presentation_restore_failed";
    if(!read_pair(p,pitch,rate) || pitch!=state.pitch || rate!=state.rate)return "presentation_restore_unconfirmed";
    state={};return "presentation_restored";
}
}
'''
test=r'''#include "native_presentation_pitch.h"
#include <iostream>
#include <cstring>
#include <stdexcept>
#include <vector>
void require(bool b,const char* message){if(!b)throw std::runtime_error(message);}
int main(int argc,char** argv) {
    try {
        std::vector<unsigned char> object(0x6000,0x5a),other(0x6000,0x5a);
        auto address=reinterpret_cast<uintptr_t>(object.data());
        constexpr float observed_pitch=10.0304031372f,observed_rate=2.26721763611f;
        native_presentation_pitch::put(address+native_presentation_pitch::pitch_offset,observed_pitch);
        native_presentation_pitch::put(address+native_presentation_pitch::rate_offset,observed_rate);
        const auto original=object;
        native_presentation_pitch::State state;
        const bool baseline=argc>1 && std::string(argv[1])=="--baseline";
        if(!baseline)require(std::string(native_presentation_pitch::clear_validated(object.data(),state))=="called","clear failed");
        float pitch=0,rate=0;
        require(native_presentation_pitch::read_pair(address,pitch,rate),"read failed");
        // Observed native presentation boundary: extra local pitch is applied
        // after the recorded basis and extrapolated from the controller time.
        const double additional_degrees=pitch+0.02*rate;
        if(std::abs(additional_degrees)>0.001) {
            std::cout << "FAIL: presentation adds " << additional_degrees << " degrees to the recorded nose attitude\n";
            return 1;
        }
        for(size_t i=0;i<object.size();++i) {
            if((i>=0x4db4 && i<0x4db8)||(i>=0x22b4 && i<0x22b8))continue;
            require(object[i]==original[i],"unrelated state changed");
        }
        require(std::string(native_presentation_pitch::clear_validated(other.data(),state))=="presentation_owner_rejected","wrong owner accepted");
        require(std::string(native_presentation_pitch::clear_validated(object.data(),state))=="called","repeated clear failed");
        require(std::string(native_presentation_pitch::restore(object.data(),state))=="presentation_restored","restore failed");
        require(object==original,"original fields not restored");
        require(std::string(native_presentation_pitch::clear_validated(object.data(),state))=="called","second clear failed");
        native_presentation_pitch::put(address+native_presentation_pitch::pitch_offset,4);
        require(std::string(native_presentation_pitch::restore(object.data(),state))=="presentation_already_replaced","newer engine state overwritten");
        require(!state.active,"restore retained ownership");
        std::cout << "PASS: extra presentation pitch removed; other state, ownership, repeated clear, restore and newer engine values preserved\n";
        return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
'''
assert not (root/'native_presentation_pitch.h').exists()
text=(root/'object_probe.cpp').read_text()
changes=[('#include "native_motion.h"','#include "native_motion.h"\n#ifdef DCS_SUPPRESS_PRESENTATION_PITCH\n#include "native_presentation_pitch.h"\n#endif'),
('    turn_path::Motion step_motion{};','    turn_path::Motion step_motion{};\n#ifdef DCS_SUPPRESS_PRESENTATION_PITCH\n    native_presentation_pitch::State presentation;\n#endif'),
('    if(std::strcmp(state.step_status,"called")==0) ++state.step_applied;',
'''#ifdef DCS_SUPPRESS_PRESENTATION_PITCH
    if(std::strcmp(state.step_status,"called")==0) {
        state.step_status=native_presentation_pitch::layout_valid() ?
            native_presentation_pitch::clear_validated(handle,state.presentation) : "presentation_layout_mismatch";
    }
#endif
    if(std::strcmp(state.step_status,"called")==0) ++state.step_applied;'''),
('    state.step_pending=false;\n    if(!state.step_hook) return;',
'''    state.step_pending=false;
#ifdef DCS_SUPPRESS_PRESENTATION_PITCH
    const auto presentation_status=native_presentation_pitch::restore(handle,state.presentation);
    if(state.presentation.active) {
        state.step_status=presentation_status;state.motion_active=false;
        if(log_file.is_open())log_file << "[DEBUG-nose]," << presentation_status << '\\n';
    }
#endif
    if(!state.step_hook) return;''')]
for old,new in changes:
    assert text.count(old)==1,repr(old)
    text=text.replace(old,new)
cmake=(root/'CMakeLists.txt').read_text()
cmake+='''
# Controlled test: suppress only the additional null-FM presentation pitch.
option(DCS_SUPPRESS_PRESENTATION_PITCH "Suppress extra staged presentation pitch" OFF)
if(DCS_SUPPRESS_PRESENTATION_PITCH)
  target_compile_definitions(HornetStagedProbe PRIVATE DCS_SUPPRESS_PRESENTATION_PITCH)
endif()
add_executable(presentation_pitch_check presentation_pitch_check.cpp)
target_compile_features(presentation_pitch_check PRIVATE cxx_std_17)
target_compile_definitions(presentation_pitch_check PRIVATE NOMINMAX)
add_test(NAME presentation_pitch_boundary COMMAND presentation_pitch_check)
'''
(root/'native_presentation_pitch.h').write_text(header)
(root/'presentation_pitch_check.cpp').write_text(test)
(root/'object_probe.cpp').write_text(text)
(root/'CMakeLists.txt').write_text(cmake)
print('Added guarded pre-step presentation-pitch test with rollback and a captured-value boundary check.')
