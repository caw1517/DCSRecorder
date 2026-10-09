#pragma once
#include <cmath>

// One shot, simulator-time clock. The bridge only commits a latch. A solo
// commit lets the first subsequent object callback own time zero. A formation
// commit carries the shared epoch (the hook's model time at the commit), so
// every aircraft's replay time is now - epoch even when its first callback
// after the commit lands frames later.
namespace release_start {
struct Clock {
    // The hook only commits when its model time is this close to the
    // aircraft's last callback; the bridge enforces the same window.
    static constexpr double epoch_window=.1;
    enum class Phase { held, committed, playing, failed } phase=Phase::held;
    double last=-1, epoch=0, elapsed=0;
    bool shared=false;
    bool commit(bool ready) {
        if(!ready || phase!=Phase::held || last<0)return false;
        phase=Phase::committed;return true;
    }
    bool commit(bool ready,double shared_epoch) {
        if(!std::isfinite(shared_epoch) || shared_epoch<0 || std::abs(shared_epoch-last)>epoch_window)return false;
        if(!commit(ready))return false;
        epoch=shared_epoch;shared=true;return true;
    }
    bool update(double now) {
        if(!std::isfinite(now) || now<0 || now<last || phase==Phase::failed) {
            phase=Phase::failed;return false;
        }
        last=now;
        // A shared epoch waits for model time to reach it; it never moves.
        if(phase==Phase::committed && (!shared || now>=epoch)) {if(!shared)epoch=now;phase=Phase::playing;}
        elapsed=phase==Phase::playing?now-epoch:0;
        return true;
    }
    bool playing() const {return phase==Phase::playing;}
};
}
