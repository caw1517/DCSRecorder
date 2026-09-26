# Native aircraft attachment: public implementation search

Date: 2026-09-23. Scope: a playback aircraft alongside the user's aircraft in one DCS process, with one player/account. This is a bounded search for concrete source implementations, not a feasibility verdict or an exhaustive code audit.

## Result

No examined public implementation supplies a callable mechanism to attach an EFM to a nonplayer aircraft or set its authoritative flight state. The strongest native-world-access lead is the Community A-4E's ship lookup, but its implementation is deliberately absent from the public source. Loading native code is demonstrated by other projects; aircraft ownership is a separate unresolved interface.

## Concrete source leads

| Source | Exact code/path and observation | Relevance and limit |
| --- | --- | --- |
| Community A-4E | [`A-4E-C/ExternalFM/FM/ShipFinder.h`](https://github.com/Community-A-4E/community-a4e-c/blob/master/A-4E-C/ExternalFM/FM/ShipFinder.h), lines 9–32: conditional include of `Avionics/ShipFinder.h`; `getShips()` calls `findShips()` if available, otherwise returns `nullptr`. The author says the implementation is intentionally hidden. | Concrete evidence of a native world-object read feature, but the public wrapper provides neither implementation nor an aircraft mutation/attachment interface. The author's comment about their reason for withholding code is not a legal conclusion by this project. |
| Community A-4E | [`A-4E-C/ExternalFM/FM/optional_headers`](https://github.com/Community-A-4E/community-a4e-c/blob/master/A-4E-C/ExternalFM/FM/optional_headers) is a symbolic link to the developer's local `Scooter_Hacks` directory. | Confirms that the optional implementation is outside the checked source tree, rather than a missing nearby include we can use. |
| Community A-4E | [`A-4E-C/entry.lua`](https://github.com/Community-A-4E/community-a4e-c/blob/master/A-4E-C/entry.lua), lines 5–25 and 88–102: registers `Scooter` through `binaries`, constructs an FM table, and passes it to `make_flyable`. | This is the ordinary player-flyable registration pattern. It offers no separate nonplayer EFM registration in this file and does not overcome our existing negative AI test. |
| OpenKneeboard | [Author's internals documentation](https://openkneeboard.com/internals/), `src/dcs-hook`: `OpenKneeboardDCSExt.lua` loads `OpenKneeboard_LuaAPI.cpp/.dll` and uses normal DCS Lua APIs to observe events, forwarding messages to the DLL. | A working native Lua extension loading pattern. It does not establish access to aircraft physics. |

## Shipped object-lifecycle API lead

The separate local inspection of `API/include/ed_object_access.h` should remain the next candidate to test. In particular, the existence of per-object create/simulate/destroy callbacks is different from an EFM callback attached to the player's flight model. This public-source search did **not** establish the plugin declaration or aircraft-type binding that invokes those callbacks. Nor did it find an implementation converting the opaque handle into an aircraft physics controller.

Exact-symbol searches included `ed_on_object_create`, `ed_on_object_simulate`, `ed_setup_object_api`, `ed_object_api`, `wHumanCustomPhysics`, and combinations of `WorldModule` with `declare_plugin`. These returned no relevant indexed public source examples. Absence from web search is weak negative evidence: it does not prove the callbacks are unusable or that another source repository contains no example.

The next useful experiment is therefore a lifecycle-only probe with an explicitly evidenced registration path: log whether an unoccupied aircraft receives create/simulate callbacks and correlate its object ID against mission telemetry. Success would demonstrate native attachment, but would **not** yet demonstrate position, attitude, velocity, or force control. Loading a DLL alone is not a pass.

## Search limits

Examined author-owned A-4E source directories, its registration file and native ship lookup wrapper, plus OpenKneeboard's own architecture documentation. GitHub raw access succeeded for the registration and ship wrapper; the cockpit native wrapper fetch and GitHub recursive tree endpoint were unavailable through the browsing tools, so neither is represented as audited. No code was injected, simulator binary modified, or claim made about a working physics hook.
