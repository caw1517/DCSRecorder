# Second-client ownership feasibility

**Scope update:** the user subsequently ruled out separate accounts. The separate-account experiment below is historical research and is no longer an eligible route. One player and one DCS/Eagle Dynamics account are hard requirements. The prepared two-client mission has not been run and is not the next recommended step.

Researched 2026-09-23. Documentation research only; no clients launched and no authentication or simulator settings changed.

## Finding

A second **occupied, rendered DCS client** is a plausible next ownership experiment after the player/AI EFM comparison. Running two occupied clients on this machine is not yet established. A dedicated server plus one client does not establish two independently occupied aircraft.

Evidence is mixed in age and authority: an ED staff answer in 2018 called for separate accounts and machines; an ED beta tester described a successful same-machine, two-aircraft client test in 2023. The latter supports trying a normal isolated-profile launch, but supplies neither a supported setup recipe nor account details. No current official guarantee of two simultaneous rendered clients on one PC was found. Sources and their limits follow.

## Primary evidence

| Question | Evidence | Consequence |
| --- | --- | --- |
| Does a write-folder switch exist? | ED Team member Rik documents `-w` as selecting a write folder, allowing multiple **server** instances from one install. Separate server game and HTTP ports are required. [DCS Server Control, March 2019](https://forum.dcs.world/topic/199586-dcs-server-control/) | Separate profiles are a documented server isolation mechanism. Extending that to two occupied clients remains an experiment. |
| What do server switches mean? | The same ED post defines `--server` as starting server mode with the first configured mission; `--norender` disables 3D rendering; `--webgui` enables web control with normal rendering. | None documents a synthetic player or headless cockpit ownership. Use normal rendered clients for the ownership experiment. |
| Are two accounts needed? | BIGNEWY, ED Team, answered a request to join one host twice using one account: two clients require another account and machine. Same-network use should work. [April 2018 answer](https://forum.dcs.world/topic/176832-logging-into-a-multiplayer-site-with-two-usernames/) | Plan on distinct legitimate ED accounts. This old answer does not establish the present same-PC limit. Do not treat profile names or callsigns as account identities. |
| Has someone actually run occupied clients on one machine? | uboats, identified as an ED Beta Tester, reported running two clients on the same machine, one hosting, and described datalink messages between the host and client JF-17s. [October 2023 firsthand report](https://forum.dcs.world/topic/335804-fixed-jf17-p2p-datalink-not-working/?comment=5322190&do=findComment) | Direct evidence that this configuration existed for that tester. It does not specify commands, accounts, or support status, and does not verify this installed build. |
| Are purchased modules shared across accounts? | BIGNEWY states that modules belong to the purchasing account and cannot be used on a different login. [February 2021 staff answer](https://forum.dcs.world/topic/262415-two-accounts-same-pc/) | Do not assume the user's purchased aircraft transfer to the helper login. |
| Can the test avoid paid modules? | ED's current download page includes the Caucasus terrain, Su-25T, and TF-51D in free DCS World. [DCS World download](https://www.digitalcombatsimulator.com/en/downloads/world/) | Use Caucasus, a stock TF-51D observer, and the existing local EFM probe, subject to verifying that probe's dependencies. |

The current ED download page describes the dedicated server as web-controlled software without textures, sounds, or GUI features, and limits its activation-free terrains to server use. It does not promise a player flight-model owner. That modern description supersedes the 2019 post's outdated terrain-purchase discussion; only the latter's command explanations are used above. [Current ED download description](https://www.digitalcombatsimulator.com/en/downloads/world/)

No documented UCID override is needed or justified. Distinct real logins, independently occupied slots, and separate profile logs are the test inputs. Do not fabricate identity, copy authentication caches between profiles, or use same-account server allowances as evidence for two flying clients.

## Smallest proposed experiment

This is an experiment design, not a claim of tested support.

1. Create an isolated helper Saved Games profile containing only the probe mod and minimal windowed graphics settings. Preserve the main profile. Do not copy saved credentials or paid-module dependencies into it.
2. Launch normal DCS with `-w DCS.EFMProbeClient` as a candidate helper invocation. Use the installation's actual executable path. Keep rendering enabled and omit `--server` and `--norender`. Confirm that the new profile receives its own log; a successful menu alone does not prove two simultaneous clients.
3. Log the helper in through normal UI using a second ED account. If the normal client rejects simultaneous launch or authentication, record the error and stop that route; a second physical machine with another account is the staff-described fallback.
4. In the main rendered client, create a private multiplayer mission with two **Client** slots: stock TF-51D for the user, EFM probe for the helper. The main client also hosts, so no third server process is necessary. Join the helper to the host; keep the same installed build and probe files at both ends.
5. Occupy the stock slot in the main client and the probe slot in the helper. Run at least 15 seconds after the probe starts, long enough to include its existing five-second pulse. Keep both aircraft and the mission active.
6. Collect separate process/profile logs and mission telemetry. Require fresh helper EFM callbacks, the expected pulse, and observer-side evidence that the probe changed attitude while the main aircraft remained occupied. Preserve start times and profile/process identity to avoid reusing positive-control logs.

**Pass:** two simultaneous occupied aircraft, fresh helper EFM callbacks, and a pulse observed independently in the main mission. This demonstrates networked ownership/actuation only; trajectory accuracy, synchronization, physical interactions, and resource cost remain unproven.

**Fail or blocked:** the second client cannot launch or authenticate normally; the probe cannot be occupied; callbacks are absent; or the remote observer does not see the expected actuation. Record which gate failed rather than calling all playback impossible.

The first test should not depend on minimizing the helper, background rendering changes, or automated slot selection. Those add variables; test background operation and sustained performance only after ownership passes.

## Community material and remaining uncertainty

Community reports of multiple dedicated servers and server/client pairs are not evidence for two occupied clients. No community workaround for identity, authentication, or executable restrictions is part of this proposal. The beta-tester report above is a firsthand experiment report, explicitly weaker than an official support promise.

Open questions are whether the installed build admits two normal clients under distinct logins on this PC, whether the custom probe loads and replicates correctly over multiplayer, and whether the machine sustains both clients. A positive result would still introduce local multiplayer infrastructure into a product whose user-facing goal is single-player layered playback; that architectural cost remains to be assessed.
