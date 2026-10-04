Claimed **Prepare recording and playback copies from authored missions** after verifying the preceding ground-staging task is closed. The user selected a small dedicated mission for live validation.

Implemented source inspection and separate recording-copy preparation in the companion. The selected stock Hornet keeps its authored name; original scene tables, localization and archive resources are preserved. The preparation manifest declares role/control changes, and removing them must reconstruct the entire source mission table. Generated copies, changed sources, ambiguous IDs, selected-aircraft task conflicts, unknown script actions and unexplained compiled triggers are refused.

The recording fixture contains three stock Hornets, a truck, a reference zone, localized briefing, and a timed message/flag/embedded chime. Repeated preparation produces byte-identical archives; all nine original non-mission archive members remain byte-identical. The recorder namespace avoids an intentionally occupied authored flag.

Playback structure conversion is implemented and tested with a separately selected player Hornet retaining its authored start. Native playback packaging, loaded reference/hook integration, companion playback UI and real source-to-playback validation remain unfinished. Authored takes are explicitly blocked from the old fixed-donor builder to prevent losing their scene.

Thirteen offline tests pass, including existing build-profile regressions. The actual generated recorder passes its Lua capture-contract check; installed dependency/route checks pass. Browser inspection confirms the new source/aircraft selection controls. These are preparation results, not live acceptance.

With DCS fully closed, installed only **050-Authored-Scene.miz** and **051-Authored-Recording.miz**, using add-only copies and verified hashes. First user step is to run the source and observe its authored message/chime, followed by comparison/capture in the recording copy. The task and parent remain open.

Local implementation: `companion/authored_missions.py`, `companion/mission_data.py`, companion API/UI additions and `experiments/efm-ownership/authored-preparation/`. Evidence, preserved source, repeat packages and receipt: `experiments/efm-ownership/results/authored-preparation-2026-10-02/`. Changes are uncommitted and artifacts remain local.
