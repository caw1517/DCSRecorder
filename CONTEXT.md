# Recorded Flight Playback

Single-player flight recording and layered playback in DCS World.

## Language

**Recorded flight**:
A time-based record of one aircraft's flight, intended to reproduce its movement and attitude during playback.

**Playback aircraft**:
An aircraft reproducing a recorded flight while the user can fly alongside it, including aerobatics, takeoff, and landing.
_Avoid_: AI pilot (which implies independent flying decisions).

**Layered playback**:
Playing previously recorded flights together while flying and recording another aircraft, allowing a formation to be built one flight at a time.

**Formation**:
A saved, named set of recorded flights that play together on one clock, starting at the shared countdown release. Each recorded flight in a formation is flown from a different aircraft association. A formation belongs to one authored mission and plays in its revisions, so the mission can still be edited. Building a formation never alters its recorded flights, and a recorded flight can belong to several formations.
_Avoid_: layer set, stack.

**Formation version**:
One immutable state of a formation, mapping each aircraft association to one recorded flight. Re-flying or adding a position creates the next version, numbered in creation order and naming the version it was based on; earlier versions remain. A version can be based on any earlier version, not only the latest.

**Flown against**:
The record carried by a recorded flight made while a formation version played: that version, the takes that played, the positions muted or not ready, and any aircraft lost during the take. Within a version, each position shows which of the version's other takes it actually played against. Any other take, whether muted, not ready or recorded later (including a re-fly), is *not flown against* for that position. These flags are read from the takes' records, never stored on the version.
_Avoid_: layered over, on top of.

**Muted position**:
A position left out of one recording session by choice in the companion; its aircraft is not placed in the prepared mission. Muting never changes the formation.

**Flight library**:
The user's collection of saved recorded flights, available to name and select for playback.

**Playback mission**:
A ready-to-fly mission prepared for a selected recorded flight, containing its playback aircraft and an aircraft for the user to fly alongside it.

**Authored mission**:
A mission the user prepares in DCS Mission Editor, including aircraft starting positions and the surrounding scenery, objects and visual references.

**Mission revision**:
A saved version of an authored mission and its scene. A recorded flight retains its association with the mission revision used for recording, even when the authored mission is edited later.

**Aircraft association**:
The companion's lasting record that an aircraft in one mission revision is the same aircraft in another, confirmed by the user once per changed revision. Editor IDs, names, counts and order only suggest it. A recorded flight belongs to one aircraft association and can play in any revision where that aircraft is confirmed, by default the revision it was recorded in.
_Avoid_: unit ID (an editor detail that can be reused by a different aircraft).

**Held staging**:
The period before playback begins when aircraft are visible at their starting positions and the user can inspect the scene from their held position. The surrounding mission continues to run.

**Parked completion**:
The end of a parking-to-parking playback when the aircraft remains at the user's chosen final stopping position on the ground with engines running and its supported final recorded state held. The position need not be a designated parking slot.
