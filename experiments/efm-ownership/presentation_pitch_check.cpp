#include "native_presentation_pitch.h"
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
