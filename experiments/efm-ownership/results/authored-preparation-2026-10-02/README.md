# Authored preparation checkpoint — live comparison pending

Implementation and current scope: [preparation notes](../../authored-preparation/README.md).

- Current source: `source-v2/050-Authored-Scene.miz`.
- Source SHA-256: `f72d54f032e3532d61e25d31205a7e6192aae2ff94a3a3273f7f6acaa315c398`.
- Recording copy: `recording-v2/prepared.miz`, installed as `051-Authored-Recording.miz`.
- Prepared SHA-256: `78676654116fd64d90a2b27ba417d9003234f6e7251dac151c09989c9a879f66`.
- `repeat-v2/prepared.miz` is byte-identical to the first preparation.
- Nine original non-mission members remain byte-identical, including both locale
  dictionaries, resource maps and chime files. Removing the declared role change
  and startup trigger restores the entire authored mission structure.
- Namespace `DCSR_AUTHORED_2` avoids the authored `DCSR_AUTHORED_1_READY` flag.
- `installation.json` verifies the two new Saved Games mission files. DCS closure
  was checked; an initially lingering background process caused no writes.

The source is an explicitly constructed new test scene chosen by the user, not
an attempt to recover an authored source from a generated recording mission.
Earlier `050-Authored-Scene.miz`, `recording-package` and `repeat-package` are
superseded uninstalled fixture versions. The source-v2 fixture specifies the
existing tested clean Hornet pylon configuration.

No live acceptance is claimed yet. Native playback packaging and UI integration
are pending the new source capture. The task remains open.
