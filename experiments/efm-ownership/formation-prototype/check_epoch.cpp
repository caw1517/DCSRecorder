// Shared formation epoch: two aircraft committed in one hook callback share the
// hook's model time as time zero. One aircraft's first callback after the
// commit is delayed by several frames and it is then stepped at 10 Hz (as DCS
// stepped a damaged aircraft); at every tick both are stepped, their replay
// times are exactly equal. The solo commit, kept for single-aircraft playback,
// is shown to lag in the same schedule.
#include "../release-start/policy.h"
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
using release_start::Clock;
namespace {
void require(bool ok,const std::string& why){if(!ok)throw std::runtime_error(why);}
double frame(int k){return 30+k*.02;} // 50 Hz model time
}
int main() {
    try {
        Clock lead,wing,solo_lead,solo_wing;
        for(int k=0;k<=150;++k)for(auto* c:{&lead,&wing,&solo_lead,&solo_wing})
            require(c->update(frame(k)) && c->elapsed==0 && !c->playing(),"held clock advanced");
        const double epoch=frame(150);
        // One hook callback commits both aircraft on the same epoch.
        require(lead.commit(true,epoch) && wing.commit(true,epoch),"shared commit refused");
        require(!lead.commit(true,epoch),"duplicate commit");
        require(solo_lead.commit(true) && solo_wing.commit(true),"solo commit refused");

        const int delay=5;  // wing's first post-commit callback lands 5 frames late
        int shared_ticks=0;
        for(int k=151;k<=151+2000;++k) {
            const double now=frame(k);
            lead.update(now);solo_lead.update(now);
            // After the delay the wing is stepped at 10 Hz for 10 s, then at 50 Hz.
            const bool wing_steps=k>=150+delay && (k>=150+delay+500 || (k-150-delay)%5==0);
            if(!wing_steps)continue;
            wing.update(now);solo_wing.update(now);
            require(wing.playing() && lead.playing(),"aircraft not playing");
            require(wing.elapsed==lead.elapsed,"replay times differ at model time "+std::to_string(now)+": "+
                std::to_string(lead.elapsed)+" vs "+std::to_string(wing.elapsed));
            require(wing.elapsed==now-epoch,"replay time not measured from the shared epoch");
            if(k==150+delay) {
                require(wing.elapsed>.099 && wing.elapsed<.101,"late first callback did not start at its shared replay time");
                require(solo_wing.elapsed==0 && solo_lead.elapsed>.079,"solo schedule did not show the lag it replaces");
            }
            ++shared_ticks;
        }
        require(shared_ticks>1000,"too few shared ticks");
        require(solo_lead.elapsed-solo_wing.elapsed>.079,"solo clocks did not keep the late aircraft behind");

        // An object stepped just before the hook's frame waits for the epoch.
        Clock early;
        require(early.update(32.94) && early.commit(true,33.0),"epoch ahead of last callback refused");
        require(early.update(32.98) && !early.playing() && early.elapsed==0,"played before the shared epoch");
        require(early.update(33.0) && early.playing() && early.elapsed==0,"callback on the epoch is not time zero");
        require(early.update(33.02) && early.elapsed==33.02-33.0,"replay time after epoch");

        // Refusals: not ready, never stepped, invalid or distant epoch.
        Clock fresh;require(!fresh.commit(true,0),"commit before any callback");
        Clock held;held.update(40);
        require(!held.commit(false,40),"unready commit accepted");
        require(!held.commit(true,std::numeric_limits<double>::quiet_NaN()),"NaN epoch accepted");
        require(!held.commit(true,-1),"negative epoch accepted");
        require(!held.commit(true,40+Clock::epoch_window+.01) && !held.commit(true,40-Clock::epoch_window-.01),"distant epoch accepted");
        require(held.phase==Clock::Phase::held,"refused commit changed phase");
        require(held.commit(true,40.05),"epoch inside the window refused");

        // A mission restart gets a fresh clock and a fresh epoch.
        Clock restarted;require(restarted.update(0) && !restarted.playing() && !restarted.shared,"restart reused epoch");
        require(restarted.commit(true,.02) && restarted.update(.04) && std::abs(restarted.elapsed-.02)<1e-12,"fresh epoch");
        std::cout<<"PASS: one shared epoch; a first callback delayed "<<delay<<" frames and 10 Hz stepping keep exactly equal replay times over "
                 <<shared_ticks<<" shared ticks; the solo commit's lag is shown; refusals and restart\n";
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
