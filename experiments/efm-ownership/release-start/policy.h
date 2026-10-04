#pragma once
#include <cmath>

// One shot, simulator-time clock. The bridge only commits a latch; the first
// subsequent object callback owns time zero for every playback channel.
namespace release_start {
struct Clock {
    enum class Phase { held, committed, playing, failed } phase=Phase::held;
    double last=-1, epoch=0, elapsed=0;
    bool commit(bool ready) {
        if(!ready || phase!=Phase::held || last<0)return false;
        phase=Phase::committed;return true;
    }
    bool update(double now) {
        if(!std::isfinite(now) || now<0 || now<last || phase==Phase::failed) {
            phase=Phase::failed;return false;
        }
        last=now;
        if(phase==Phase::committed) {epoch=now;phase=Phase::playing;}
        elapsed=phase==Phase::playing?now-epoch:0;
        return true;
    }
    bool playing() const {return phase==Phase::playing;}
};
}
