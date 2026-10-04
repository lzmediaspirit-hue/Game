# The side view's mechanics on the grid (T1, T2, T3)

The top-down view is to replace the side view. Before the side view can go, every mechanic that only it has needs a
top-down version: a raft has to carry a body on the height grid, an updraft has to lift it, a set piece's foes have to
come in on the grid's floors. This page lists every such mechanic, says where it lives, which rooms and quests use it,
and whether the grid covers it. It ends with what is still to do, in order.

T1 built the machinery and laid the first rows. T2 laid the rows of every Act I room on the grid and built what T1 had
not: sealed hatches, swinging lanterns, boards that are the floor itself, spike pits, ice, wind, the swim and the
shallows' slow (the to-do's items 1 to 13, "T2" below). T3 did the rest of the to-do from Act I's last item on: the
Lower Pit's cracked slab, Rimefrost's ice, no-flight volumes, low gravity and its jade switches, the Starsea's docks,
the late zones' light, T2's presentation leftovers and edge cases ("T3" below).

**Status (S12a): the side view is gone.** Its world, its player and its solver are deleted, and every room plays on the
grid. What it left the grid still reads: a room's side-view `volumes` (a flood's script, an ice's traction, a wind's
push: `TopdownTraverse.from_layout`), its `climbables` (`TopdownPlayer`), its `bounds` (the side points a room event and
an old save are mapped across: `TopdownRoom.grid_event`), and the side geometry `tools/data/topdown_rooms.py` builds the
layouts from. `MovementSolver` keeps only the arts Combat starts on a body (air dash, Plunge, glide) and the numbers the
brains read; `LocalAuthority` only announces a body's events; `ZoneGeometry` is the stand-in ground under the grid and
the rafts' clock. The events only the side view's solver emitted (`jumped`, `landed`, `fell_out`, `volume_entered`,
`volume_left`) were dormant in the event contract after S12a; **S12c** announces each from the grid's motor again, with
what waited on them (the paths above, the remount, a fall out of a room and its fortune, the water's step), and the
fame greeting and the shallows' dodge rule besides (below, "S12c: what the side view carried"). Below, "the side
view's" names where a number or a rule came from.

The rule throughout: **the authorities keep their rules; the grid only says where things stand.** A raft rides the side
view's own mover function on the room's clock, a glide spends Combat's QI, a climb asks the World authority whether it
is open. The top-down side adds placement (spec rows, layout cells), the motor's response, and the drawing.

## How the grid carries the side view's traversal

| Part | File | What it does |
|---|---|---|
| Spec rows | `tools/content/rooms/spec.py` (`traverse`, `stage`), `engine.py` (`TRAVERSE_KEYS`, `stage_cells`) | A room's traversal, each piece named by its side-view id, in cells. T2: a raft's and a bounce's `look`, a crumble's `under` and `look`, and the `hatch`, `lantern`, `hazard`, `ice` and `wind` rows. T3: the `crack`, `no_flight` and `low_gravity` rows |
| Layout checks | `tools/data/topdown_rooms.py` `check_traverse` | A raft runs over open water clear of props, with landings at both ends; a lift rests on a floor; a climbable's foot is reached and its top is a level or more higher; a volume names a side-view volume of its kind; a stage cell is open, reached and off the lanes. T2: a hatch lies on a flight and names a sealed climbable; a lantern sweeps neither a prop nor a floor over its level, and somewhere on its sweep has a floor within a level beside it; boards that are the floor lie at their level and are reached. T3: a crack names a cracked block and lies a jump's height over one floor, off the stairs, beside a floor reached on foot; a pit's open spikes are floor, nothing stands on them and no way sets a body down there; a circling lantern's sweep is checked at its deck's height as it goes round upright |
| Model | `scripts/topdown/topdown_traverse.gd` (`TopdownTraverse`) | The rows in world units, read once from the layout and kept on the room (`TopdownRoom.traverse`). Queries: the deck under a point, the updraft round a body, the climbable a body may take, the boards' state, a current's push, a flood's water. T2: the shut hatch, the boards gone from a floor, the hazard volumes, the ice, the wind's push, a lantern's place on its arc. T3: the whole slab over a point and what it seals, a pit's open spikes, the no-flight volume over a point, the pull of gravity there and the jade switches that set it, a circling lantern's height, boards held gone over a body |
| Motor | `scripts/topdown/topdown_motor.gd` | Floors include decks, whole boards and risen water. A body rides a deck, is pushed by a current, rises in an updraft, glides, flies, double-jumps, kicks off a wall, climbs, and bounces. T2: a shut hatch is a wall; boards gone from a floor drop it or open a hole; a body with Breath Control swims open water; the shallows slow the walk; ice keeps the speed; the wind pushes. T3: a slab is a floor until a Plunge breaks it and falls on through; low gravity lightens the fall; the swim strokes (`stroked`); boards stay gone over a body under them; the wind looks for a drop along eight ways; no safe spot on a pit's spikes |
| Player | `scripts/topdown/topdown_player.gd` | Asks Combat for every art (glide, flight, Plunge, air dash) and announces each use (`art_used`, `mover_boarded`, `climb_started`/`climb_finished`) through `LocalAuthority.announce`, as the side view's solver does. T2: asks the World authority whether each hatch is open (`climbable_open`) and says why a shut one is; Breath Control and a Water Sphere's frozen ground reach the motor; a swimmer is drawn from the chest up. T3: the swimmer's walk frames run once through on the stroke's pull and hold the rest frame through its glide; the world answers a stroke with its wake and a broken slab with dust and a jolt |
| View | `scripts/topdown/topdown_traverse_view.gd` | Draws the rafts and lifts, the vine, rope, ladder and chain tiles, the spray, the boards, the flood's water, the glide's leaf and the flight's cloud. T2: the driftwood and the planks, the sealed hatches, the drum, the lotus leaf and the bent bamboo, the lanterns on their chains, the pit, the pool or the shadow under gone boards, the icicle shelves, the ice, the wind, the swimmer's ripple; a flood's water only over the floors it covers. T3: the cracked slab and its rubble, a pit's open spikes, the light air's motes (a ring of them while it is off), the bounces giving, an open hatch's gate, the circling lanterns upright, the ice ending raggedly; the stroke's wake is the world's `FxView` |
| World authority | `world_hazards.gd` `tick_hazard_volumes`; T3: `world_objects.gd`, `world_starsea.gd` | T2: on the grid a side-view hazard volume stands on its layout's `hazard` cells and strikes a body down in them, its numbers the side view's. T3: and a body standing on a pit's open spikes; a thing under a whole slab is not shown (`object_visible`); a jade switch sets its layout's low gravity (`toggle_gravity`); the prototype's gate holds a Starsea dock as it holds a way (`set_sail`) |
| Combat | `combat_flight.gd` `_air_distance`, `flight_allowed` | T2: on the grid the air distance is the plane's speed, so Cloud Lung counts flight in any direction. T3: on the grid flight is refused over a layout's `no_flight` cells (the stand-in geometry has none of the side view's volumes) |
| Light | `scripts/topdown/topdown_light.gd` | T3: the tomb's halls and the Clan Hearth's cavern lamp-lit (`ROOM_AREAS` for a room under rock whose backdrop is the outdoors'); the sky-sea and star-field zones starlit (`STARLIT`, the story's night whatever the clock); the star lanterns' starlight, the braziers' and the cook fire's flames |
| Numbers | `tools/data/stats.py` → `data/movement.json` `topdown.traverse` | The side view's speeds scaled to the grid's jump (impulse 400 against the side view's 530). T2: `side_scale`, the swim's `swim_s`, `swim_factor` and `swim_out`, `shallow_factor`, `ice_traction`, `wind_edge`. T3: `swim_stroke_s`, `swim_surge` |
| Art | `tools/art/topdown/traverse.py`, `build_traverse.py` → `art/topdown/traverse.png`, `data/topdown/traverse_art.json` | Original pixel art, nearest neighbour, byte-identical builds; `--review` writes `topdown_mechanics/traverse_x4.png` (T2's sprites in its middle, T3's at the foot) |

The grid's own queries never count a deck, an updraft or a climb: not `height_at`, not `find_path`, not the reach
checks, not auto-path. Each is an extra way to get somewhere, never the only way.

The body reuses existing top-down actions and adds no new body animation. A climb plays `work_hang`. A glide, a flight
and a raft ride use the idle and walk poses, with the leaf over the body or the cloud under its feet. T2's swim plays the
walk and the idle, the figure sunk and cut at the water's line (`TopdownFigure.draw`'s clip), a ring of water round it.
T3 gives the swim its stroke from the same frames: the walk's cycle runs once through on each pull and holds its rest
frame through the glide.

## T2: how the rooms' rows work

- **Sealed hatches** (`hatch`). The four rooms whose sealed ladders the grid had made open stairs keep the stairs (the
  grid's queries still walk them) and lay a hatch over each flight, named by the side view's climbable. The player asks
  the World authority's `climbable_open` as the room is entered and every half second. While it refuses, the flight's
  cells are a wall to the motor, a lattice gate with crossed paper seals stands at its foot, and a push into it shows
  the climbable's own locked text. Old Ma's storeroom and the Fisher's Hut's loft open with The Runaway Kite; the
  libraries' first gallery opens at Outer Disciple and the second at Inner Disciple. A motor with no character behind it
  (the route tour) finds them open.
- **Boards that are the floor** (`crumble` with `under`). They are the grid's own floor at the boards' level, so
  auto-path and the reach checks walk them. A foot that stays `break_s` sends them, and for `return_s` the motor's floor
  there is `under`: a level lower (the monastery's rotten floors, onto the terrace and the court), or a hole, `water`
  (the Cloud trial's plank walk, into the cliff pool) or a `pit` (the Tunnels' planks over their spike pits). A body in
  a hole is back on its last safe spot, as in water; a pit takes it without a splash. T1's boards over a lower floor
  stay as they were (the Frozen Shrine's icicle shelves, drawn as ice with `look: "ice"`).
- **Hazard volumes** (`hazard`). The Tunnels' spike pits name the side view's hazard volumes. The World authority
  strikes a body down in their cells (under their floor: fallen into the pit) with the volume's own damage and bleed.
- **Lanterns** (`lantern`). A deck at its level hung over the floor, moved by the side view's own `swing` or `circle`
  mover on the room's clock: a swing east and west along its arc, a circle on the plane round from its rest. It rides
  as a lift's deck does, and boards a body standing level with it as it sweeps in under its feet (the Hall of Lanterns'
  gallery edge). It is drawn as a great lantern on its chain, its lid the deck.
- **Ice and wind** (`ice`, `wind`). The side view's volumes on cells, their numbers its own scaled by `side_scale`. On
  ice the speed eases toward the stick at its traction, so the body slides on and slides to a stop. The wind pushes a
  standing body, strong for `strong_s` of its cycle and a breeze the rest, harder within `wind_edge` of a drop.
- **Breath Control** (the motor's `swim`). With the art the bank no longer stops the walk: the body steps off into open
  water and swims it at `swim_factor` of the pace for `swim_s` (30) seconds, its feet on the water's surface, and climbs
  out onto a bank up to `swim_out` over it. Out of breath it sinks and is back on its last safe spot. Every open water
  on the grid is swum (the side view's deep water); a flood's and a hole's water are not. Without the art T1's rule
  stands.
- **The shallows' slow.** A floor under shallow water (a paint the tile set marks `flood`) is waded at `shallow_factor`
  (0.7) of the pace, unless a Water Sphere has frozen the ground (`ActorState.frozen_ground`).
- **Floods.** A side-view rise row whose `to` is no higher than the volume's resting top takes the water back down from
  where it stands (the Serpent's, when it is beaten). The water is drawn only over the floors under it. The dry floor a
  flooded body is sent to lies within a level of its last safe spot where there is one, never on a pillar's top.

## T3: Act II onward, and what T2 left

- **The cracked slab** (`crack`). The Lower Pit's slab is a row over four cells by two of the pit's floor, a level up
  (the side view's block of 40, a jump's height). The motor stands a body on it and stops a walk at its foot; a plain
  landing holds it. A Plunge coming down on it breaks it for the visit (the side view's `break_surface`) and falls on
  through: the body lands on the floor under it, plunging still, and strikes there. While the slab stands, what lies
  under it is sealed: the World authority does not show the spirit stone shards (`object_visible`), so they are neither
  drawn nor offered. The layout puts the shards under the slab (a pin), where the side view's slab sealed them.
- **Rimefrost's ice** (`ice`). Frostpine Climb's high trail before the way east, and the west of Rimefrost Summit's
  plateau, the side view's two ice volumes (traction 420, scaled). On open ground a sheet's glaze stops a few pixels
  short of its edge cells, by a hash of each, so it ends raggedly (the Frozen Shrine's court too).
- **No-flight.** No side-view room has a `no_flight` volume; the side view refuses flight by room (`no_flight`: the
  Windbridge, the Tide Battle, the Leviathan's Maw, the Inverted Hall, the two crossings) and by type (interiors, sect
  grounds, dungeons). On the grid `flight_allowed` reads the same room and type. Its volume test asked the side view's
  geometry with the grid's coordinates; on the grid it now asks the layout's `no_flight` rows, so a volume a side-view
  room gains has its counterpart in a row. The feedback is the side view's: the hold glides instead, and a flight carried
  into a no-flight cell is ended by Combat's tick (`flight_ended`, `no_flight`) and the body comes down.
- **Low gravity** (`low_gravity`). A row names a side-view `low_gravity` volume and takes its share of the pull (0.45),
  its jade switch and whether it is inverted; tied to a switch it starts off, as the side view's. While it is live the
  motor applies that share to the fall and never to the jump, so a standing jump climbs 1/0.45 as high (104 units, past
  three levels) and hangs longer. The World authority's `toggle_gravity` (the switch's own call) sets the layout's rows as
  it sets the side view's geometry. The view's motes rise off the floor while it is live, a faint ring of them lies along
  its edge while it is off. The Orbit Ruins' four volumes are rows: the Tumbling Stair's over the middle of the room, the
  Orbit Garden's over its east, and the Inverted Hall's two, its west half and its east half. Each spans its side
  volume's run east to west and the room's whole depth, under the switch in its ring. In the Inverted Hall, with the east
  switch turned, a standing jump at the high gallery's foot climbs onto it, as the side view's does (its flight of stairs
  is the grid's own way up besides).
- **The Starsea's docks.** A dock (`starsea_dock`: the Shipwrights' Yard, the Broken Pier, the Launch, the Arrival Quay)
  sets sail with its own call. The prototype's gate (decision 41) now holds a dock as it holds a way: while the route's
  crossing deck or its far port has no layout, `set_sail` refuses with "The road beyond is still being drawn." and the
  side view is never entered. With both laid out the voyage plays on the grid: the crossing's event runs for the
  vessel's time (its foes come aboard at the layout's event cells, `grid_event`), and `voyage_arrive` makes port at the
  far pier. R9 laid both crossings out, so all four routes sail on the grid; on the crossing's deck the star-water
  streams west past the hull (`VoyageView`), the vessel under way. The sky-ships' ferries (the Skydock's, the Alliance
  Gate's, the lake's, the skiffs) are the side view's doors
  that a body presses up into: on the grid they are ways at their gangways, walked into or taken with the context button
  under the door's label. That is the whole of the side view's boarding; it has no boarding moment beyond it.
- **The late zones' light.** The Tomb of Sunscar's halls and the Clan Hearth's cavern are lamp-lit at any hour (the
  hearth's backdrop is the Hold's outdoors, so it has a room entry, `ROOM_AREAS`). The sky-sea zones (R8) and the star
  field's (R9) lie under the side view's night skies: on the grid they are the story's night whatever the clock says
  (`STARLIT`). Lanternfall's star lanterns burn with a pale starlight; the tomb's and the Hold's braziers and the herders'
  cook fire light their pools. Past the Lantern Star Field (the Citadel, the Orbit Ruins, the Ashen Reach, the Nebula
  Deep, the Starsea's crossings: `STAR_VOID`) an island's brink falls into the starry void, not the sea of cloud: the
  vista under the cliff is dark indigo bands with a nebula's haze across and stars on a lattice that slides slower than
  the room, some twinkling; the Starsea's water round a crossing's deck has the same stars glinting in it. The rooms' own
  water there (the nebula's, the Starsea's) is star-water: an indigo wash over the river's paint, stars glinting in it
  (`StarWaterView`). The Wardens' lamps and caged stars, the Ashborn pyres and the Lantern Heart's wick pillars and flame
  basins give their light.
- **The Leviathan's lagoon.** The side view's Nebula Leviathan is a flier (`flying`), and no water volume holds it: its
  fight is on the Maw's ground. On the grid a flier goes straight over water, so the Leviathan crosses its lagoon as it
  likes, surfacing on the shoal where it spawns. Its swim's look is its sheet's: decision 44's rule plays a foe sheet's
  `swim` row wherever the foe is over water, as the marsh leech's does, so the Leviathan swims once its sheet (the late
  monster batch) has that row.
- **No-flight rooms past the Field.** The Inverted Hall, the Leviathan's Maw and the two crossings refuse flight by room,
  as the side view does; the hold glides.
- **Presentation.** The swim's stroke: a pull every 0.9 s while the swimmer moves, the walk's frames once through and the
  pace surging 15 % on it, then a glide on the walk's rest frame; each pull leaves a ring spreading on the water. A
  bounce gives as it launches a body: the drum's skin pressed in, the lotus leaf pushed into the wet, the culm bowed,
  then each springs back past its rest (three frames each). An open hatch keeps its gate, the leaves folded back against
  the posts and the seals torn. The circling lanterns go round upright, as the side view's: east and west along the
  plane and up and down twice their radius, their lid carrying a rider up and round.
- **T2's edge cases.** Boards that were the floor do not come back over a body still standing under them (they would
  lift it onto them); they come back once it has stepped out. The Tunnels' pits open beside their planks, a row of spikes
  north and south of the track (the side view's pit lies round its planks): a body standing on the spikes is struck by
  the pit's own hazard, the planks over the rest keep a body on them clear, and no safe spot is ever on the spikes. The
  wind looks for a drop along the diagonals too.

## S12c: what the side view carried

S12a's deletion left a few features that lived only in the side view's player and solver silent on the grid. S12c
restores each; no event of the contract is dormant now (`tools/data/contract.py` `DORMANT` is empty).

**The movement events.** `TopdownPlayer._announce` puts on the body's state, for `LocalAuthority.announce`, what the
side view's solver did:

| Event | When on the grid | Payload | Who listens |
|---|---|---|---|
| `jumped` | the motor's jump, and the Cloud Ladder Step's second | `jumps` (1, 2) | polled: the world view plays the push-off from the motor's own event |
| `landed` | the motor comes down on a floor (a bounce's and a Plunge's landings too) | `surface` (the Paths Above ledge it came down on, else `grid`), `fall_height`, `plunge` | the Achievement authority (the paths above), the Pet authority (a mount's remount) |
| `fell_out` | the body is back on its last safe spot out of open water or off a brink | `cause` (`water`, `brink`), `recovered_to` | main.gd (the short fade), Combat (the fall's 5%), the cue (the "fell" text), Relations (the Fortune check), the world view (the camera there at once) |
| `volume_entered`, `volume_left` | the side view's volumes the body is in change | `volume`, `kind` | the cue (the water's step into `water_deep` or `rising_water`) |

**The paths above (S43).** The six rows of `data/paths_above.json` are keyed by side-view surfaces with `later` (an
optional ledge only a later movement art reaches). Each is now a raised shape of its room's spec named for that surface
(a feature, or a named prop's top): the room engine marks it on the layout (`above`: `{rect, level, art}`), lays no
flight onto it, grows nothing on it, and places what stood on the surface on it without a walk to it. The
landing on it finds it (`TopdownRoom.ledge_at`). All six map:

| Row | Art | On the grid |
|---|---|---|
| `wp_west:pine_top` | double jump | the rock pillar, two levels over the meadow, three rows clear of the rock band (no crates or step up to it) |
| `sf_artisan_row:workshop_chimney` | double jump | the roof of the house the gear was lost on, two levels up (its crates gone) |
| `bg_whispering_bamboo:bamboo_top` | double jump | a stand of culms cut level, two levels over the grove (the east knoll keeps its bent culm) |
| `ds_flooded_gate:ledge_mv_1` | double jump | the north-east ledge, two levels over the walk (its flight gone) |
| `cf_behind_falls:shaft_top` | Wall-Step | three levels up at the head of a shaft two wide between rock five high (the lotus has a shelf of its own) |
| `rm_sunken_causeway:broken_pillar` | Wall-Step | a stump three levels up in a ring of standing pillars five high, the gap below it a shaft two wide |

`tools/data/topdown_rooms.py` `check_above` holds each layout to it: every `later` surface has its ledge, of its art; no
walk reaches it from any way in (nor the double jump a Wall-Step ledge); its art does, from a floor walked to beside it
(the double jump two levels, from the motor's numbers; Wall-Step three, between two faces higher than the ledge within
two cells either side, the Echo Cliffs' rule); what stood on the surface stands on it. The reach checks of the engine,
the places, `room_sweep` and the chapter suites leave a thing on a ledge to its art.

**Falling out of a room.** The side view's rule 6 recovered a body that fell below the room's void altitude (250 under
its lowest surface) or sank in deep water, to its last safe spot, with `fell_out`. On the grid:

- **A brink** is the south edge of a room whose vista is a drop (the sea of cloud, or past the Lantern Star Field the
  starry void): 51 rooms, 2,774 columns (not over water, not a way's lane). `TopdownRoom.brink_at` says a point past it
  has no floor, as deep as the vista shows; the motor treats it as open (no wall, no face to kick off), so a body walks,
  jumps, glides, is blown (the wind's edge factor counts the drop) or knocked off it. Under `TopdownRoom.void_z` it is out
  of the room. A flier over the void holds its height; coming down, it falls out too.
- **Open water** (the side view's deep water): a body without Breath Control (or out of breath) sinks and is out. A pit
  under gone boards is not: its floor holds the body (the side view's pit had one), and the spikes strike as before.
- The body is back on its last safe spot (`TopdownMotor`: never within 24 of a brink, the side view's margin from an
  open edge), and `reset` carries the cause; `fell_out` follows. The fall's Fortune check may draw the Hidden Cave, the
  only way into `hg_hidden_grotto`, whose way up leaves the body where it fell.
- No new pose: a fall plays the jump's falling frame (character art is on hold, AGENTS.md rule 10).

**Volumes.** `TopdownMotor.volumes` (and `TopdownTraverse.volumes_at`) name the side view's volumes a body is in, at the
side view's heights: open water (`water_deep`, id `water`) and a risen flood (`rising_water`, its side-view id) at or
under the surface (a skimmer on it too, not a jump over it, nor a deck); a wading floor (`water_shallow`, `shallows`)
underfoot; a current, ice, a hazard, boards and a bounce within 20 of their floor; an updraft to its top; the wind, a
no-flight volume and a live low-gravity volume at any height. A new room starts afresh.

**The shallows' dodge.** The side view refused a dodge in shallow water. On the grid a body that wades a floor under
shallow water (`TopdownMotor.wading`, mirrored to `ActorState.wading`) is refused (`in_water`); a Water Sphere's frozen
ground is no water, and the dodge goes. `ZoneGeometry` lost its last volume query.

**The fame greeting** (S49): from Noted, as a town is entered, the nearest person in view within 900 of the body greets
the name in its tier's words for four seconds (`TopdownWorld.fame_greeting`; world.gd's alone until S12c).

## One rule for a room event's points

A room event (a set piece, a trial, a rift, a raid) used to bring side-view points in several ways: R2's
`TopdownRoom.grid_event` in `QuestAuthority.start_set_piece`, R3's `WorldRoomEvents.side_points` and
`TopdownRoom.from_side` in the tower and the Grove, and R4's `nearest_standable` in `SectAuthority.start_defence`.
These are now one helper behind one call. `WorldRoomEvents.start_event` asks `TopdownRoom.grid_event(ev, player,
side_bounds)` on the grid, and the side view is untouched. The helper takes the first of these that applies:

1. The event's points are already the grid's: the room's own event (`on_grid`, set by `merge_def`), or a rift or
   guardian made from where things stand (`on_plane`). They are used as they are.
2. The layout stages the event (the spec's `stage`, keyed by the event's id): its cells, dealt point for point
   (Heaven's Cleansing on the summit's south rim).
3. The layout has event cells (the spec's `event`): they are used group by group (the Riverbreath Trial at the
   Scripture Well).
4. Otherwise each side-view point is mapped across the room as it lies across the side view's bounds, a cell and a
   half in from the edges, then moved to the nearest open cell. An open cell is one a body stands on, off the stairs,
   three cells or more from a way, and reached on foot from the player. Two points never share a cell.

Callers covered: set pieces (`start_set_piece`), Trial Tower floors (`world_tower.gd`), the Grove's waves
(`world_nests.gd`), spatial rifts, treasure births and first-fruit guardians (`CalendarAuthority`), heart demons
(`grid_points`), sect and mine events, and the sect's raid (`start_defence`). The pole trial's ground rule also holds
on the grid: a pole's top is off the ground, the court's floor is not.

## Inventory

43 side-view-only mechanics in four groups: traversal 18, hazards 10, room events and waves 10, other 5. After T2 the
grid covered 39 of them: all 18 of traversal, 8 hazards, 9 events and 4 others. T3 covers the four T2 left: the cracked
slab, low gravity and its jade switches (the machinery and the Orbit Ruins' four rows), and the Starsea crossing (the
docks gated while a crossing or its port has no layout, played on the grid now that both crossings are laid). No-flight
volumes and the docks' routes have their grid parts too. Every side-view-only mechanic now has a top-down version. What
is left is art, in the to-do at the end: the mounts' rider pose and sheets, a flying pose, and the late foes' swim rows
(M2 drew the Cloudwing Cranes).

"Rooms" counts the side-view rooms that use the mechanic. "On the grid" says what the grid does for them.

### Traversal (18)

| Mechanic | Side view | Rooms, quests | On the grid |
|---|---|---|---|
| Rafts and floating decks | `ZoneGeometry.mover_offset`, room `movers` | Grey Pools ×2, hermit's pond, Reed Shallows ×3 driftwood, Bend Shore ferry, Flooded Gate ×3 planks, Sky Ledges ledge | **Yes.** `raft` rows: the Grey Pools' two rafts and the hermit's raft. T2: the Reed Shallows' three driftwood logs along the bank (`look: "driftwood"`), Bend Shore's ferry between the ford's causeway and the shrine's steps, and the Flooded Gate's three planks across the sunk gate (`look: "plank"`). The Sky Ledges' ledge became terraces (R4) |
| Lifts | movers with a vertical path | Jade Entry Trial planks ×2, Quarry Rim crane (trigger) | **Yes.** T2: `lift` rows for the Jade trial's two planks, up to the second and third roofs' eaves, and the quarry's crane (mode `trigger`), from the yard to the bench |
| Swinging and circling lanterns | `mover_offset` swing and circle | Hall of Lanterns ×5 | **Yes (T2).** `lantern` rows: five decks over the rubble between the galleries. Two swinging lanterns and a circling one lead a level up from the gallery to the rest; a swinging one and a circling one lead from the rest toward the loft. T3: the circling ones go round upright, as the side view's, carrying a rider up and round |
| Updrafts | `MovementSolver` updraft volumes | Falls Pool; Cliff Faces and Sky Ledges | **Yes.** The falls' spray lifts a glider to the spray ledge. The Crane Cliffs' updrafts became terraces and flights (R4) |
| Climbables (vine, ladder, rope, chain) | `MovementSolver` climbing, `WorldAuthority.climbable_open` | 151 rooms | **Yes.** `vine`/`ladder`/`rope`/`chain` rows: the Falls Pool's vine and rope. Converted rooms use stairs elsewhere. T2: the four rooms whose ladders are sealed lay a `hatch` over the stair |
| Falling Leaf Glide | `CombatFlight.glide`, `MovementSolver.glide` | Leaf on the Wind (qk3) | **Yes**, with the lesson played on the grid |
| Plunge | `CombatFlight.plunge` | Outer Trial (ch 1), Pavilion Rooftops | **Yes** (the motor's drop predates T1). The Outer Trial's objective is now checked on the grid |
| Water Skimming | `MovementSolver._water` | Skipping Stones | **Yes**, with the lesson played |
| Swallow Dart (air dash) | `MovementSolver.air_dash` | Swallow Dart (qk7) | **Yes**, along the stick, holding the height |
| Cloud Ladder Step (double jump) | `MovementSolver` | Cloud Ladder (qu6) | **Yes** |
| Wall-Step | `MovementSolver.wall_step` | Between Two Walls (ht4), Echo Cliffs shaft | **Yes.** T2: the Echo Cliffs' shaft between its two walls (raised a level, to five over the shaft's floor) climbs to the vultures' nest at its head, three levels up. The lesson's three kicks count on the grid |
| Breath Control (swimming) | `MovementSolver._water` (swim 30 s) | deep water in 7 rooms, the Drowned Grotto | **Yes (T2).** Open water is swum for 30 s at 0.6 of the pace, and the body climbs out onto a bank; out of breath, it sinks to its safe spot. The swimmer is the walk, cut at the water's line. T3: its stroke, a pull and a glide, each pull's wake on the water |
| Flight (Cloud Stride) | `CombatFlight` flight, the side solver | Wings of Cloud (ch 7, the gate to Act II) | **Yes.** Jump held as the body comes down takes off, held it climbs to its ceiling, Evade held lands; out of QI it falls; where refused, the hold glides. Wings of Cloud's "take to the air" counts on the grid |
| Mounts | `PetAuthority.mount_speed`, `ground_mounted`, climb step-down | Riding the Wind (cs1) | **The rules, yes:** the mount's pace, stepping down to climb and back on at the top, no Wall-Step. No rider art yet: it needs a new body animation, written up in the to-do. Act I's story needs no mount |
| Bounces (drum, lily pad, bent bamboo) | bounce volumes | Fairground, Whispering Bamboo, Grey Pools | **Yes.** T2: the Fairground's drum by the Cloud hall (up onto its roof), the bent culm at the east knoll's foot, the lotus leaf at the lily ledge's foot, each drawn by its `look`. T3: each gives as it launches a body |
| Crumbling boards | crumble volumes | Tunnels ×6, Cloud Entry Trial, Forgotten Monastery ×2, Frozen Shrine ×3 | **Yes.** T2: boards that are the floor and open on a hole (the Tunnels' planks over their spike pits, the Cloud trial's plank walk over its pool), the monastery's rotten floors (dropping a level), and the Frozen Shrine's icicle shelves over the terrace. T3: boards that were the floor never come back over a body under them |
| Timed routes (Cloud Steps, docks) | route objects, `route_finish`; the docks' `set_sail` and the voyage's time | Cliff Stair; 4 dock rooms | **Yes** for the Cloud Steps (the layout places the bell; `topdown_tutorial`). T3: the four docks are on the grid (R6's yard, R8's three); each sets sail with its own call, held by the prototype's gate while its crossing or its port has no layout, the voyage timed by the vessel |
| Rooftop chases | chase objects | Gate Street, Stoneford market | **Yes**, by the layouts' routes. T2: both chases are played on the grid, the thief caught over the roofs |

### Hazards (10)

| Mechanic | Side view | Rooms | On the grid |
|---|---|---|---|
| Currents | current volumes | Flooded Gate ×2, Rapids Terraces | **Yes.** T2: the Flooded Gate's drain along the court's south rows, the flood's pull over the sunk gate, and the Rapids' white water. A body riding a deck is not pushed |
| Rising water | rising_water volumes, `ZoneGeometry.on_event` | Serpent's Shallows, Abbot's Sanctum (boss phases) | **Yes.** `flood` rows follow the side volume's own `rise` script through the World authority's boss-phase hook. T2: the Serpent's shallows (back down when it is beaten) and the Abbot's sanctum (back after its hold), a level deep |
| Deep water | water_deep volumes | 7 rooms | **Yes**: open water returns a walking body to its safe spot, and a flood moves the safe spot to dry floor |
| Shallow water's slow | water_shallow volumes (×`speed`) | 11 rooms | **Yes (T2):** every wading floor (the tile set's `flood` paints) at 0.7 of the pace, full pace on a Water Sphere's frozen ground |
| Spike pits | hazard volumes | Tunnels ×2 | **Yes (T2):** `hazard` rows under the planks; a body fallen into a pit is struck by the side volume's spikes. T3: the pits open beside their planks, their spikes striking a body standing on them |
| Ice | ice volumes (traction) | Frozen Shrine, Rimefrost ×2 | **Yes (T2)** for the Frozen Shrine's court and terrace (`ice` rows). **T3:** Frostpine Climb's high trail and Rimefrost Summit's plateau |
| Wind volume | wind volumes | Windswept Ridge | **Yes (T2):** the ridge's `wind` row, beside its `wind_gust` hazard |
| Low gravity | low_gravity volumes | Orbit Ruins ×3 | **Yes (T3):** `low_gravity` rows, the side volume's share of the fall while its jade switch holds it; the jump climbs 1/0.45 as high. The Tumbling Stair's, the Orbit Garden's and the Inverted Hall's two are rows; the hall's high gallery is climbed in the light air |
| Room hazards (strike, aura, gust, pool, flow: 16 kinds) | `WorldHazards`, `HazardRules` | 27 room uses | **Yes**, on the World authority: strikes fall on the grid's floors, auras find their shelters by placed objects, gusts drift the body, pools and flows take the layout's `areas` (T2: the Rapids' strand and white water) |
| Cracked slab | cracked blocks broken by a Plunge | Lower Pit | **Yes (T3):** a `crack` row a level over the pit's floor, the shards sealed under it; a Plunge breaks it for the visit and strikes on the floor below |

### Room events and waves (10)

All covered by the one rule above:

- set pieces at rite circles (15 rooms, 10 on the grid);
- a room's own event (the Hollow Night on its layout cells);
- Trial Tower floors;
- the Grove's waves;
- spatial rifts;
- treasure births and first-fruit guardians;
- heart demons;
- the sect's raid;
- the pole trial's ground rule;
- **the Starsea crossing** (T3): the docks set sail into the crossing's own room, its event's foes on the deck's event
  cells, port made at its end; held by the prototype's gate while the deck or the port has no layout.

### Other (5)

| Mechanic | On the grid |
|---|---|
| Teleport stones, transfer arrays | **Yes**: objects at the layout's cells (R4: a teleport lands in front of its stone) |
| No-flight rooms | **Yes**: `flight_allowed` reads the room and its type (R9's Inverted Hall, Leviathan's Maw and crossings among them). **No-flight volumes (T3)**: `no_flight` rows (no side-view room has one yet), the same feedback (the hold glides, a flight comes down) |
| Sealed climbables | **Yes**: a climb row asks `climbable_open`, and T2's hatches seal the four rooms' stairs by the same rule |
| Cloud Lung's air distance | **Yes (T2)**: on the grid `CombatFlight._air_distance` counts the plane's speed (in the side view, x alone) |
| Gravity switches | **Yes (T3)**: `toggle_gravity` sets the layout's `low_gravity` rows tied to the switch, as it sets the side view's volumes; the Orbit Ruins' four switches are turned on the grid with their own interact |

## Tested

`tests/topdown_traversal.tscn` (in `tests/suites.txt`, after `topdown_peaks`; `-- --only=<part>` runs one part) plays
each mechanic through a live `TopdownWorld`, its motor stepped frame by frame:

1. set pieces, the summit's stage, the Scripture Well's cells, a Trial Tower floor, a point past a smaller room's edge,
   the pole trial, a rift, the sect's raid;
2. the three rafts boarded, carried and left without a splash;
3. Leaf on the Wind: the vine, the glide over the spray, the updraft to the ledge, handed in;
4. the rope up and down, a jump off it, a sealed rope shut;
5. Skipping Stones handed in;
6. Swallow Dart's and the Cloud Ladder's objectives;
7. Wall-Step and a bounce;
8. a lift up the Falls Pool's cliff, and rotten boards over the water;
9. a current, and a flood raised by a boss's phase;
10. flight and Wings of Cloud's objective;
11. a mount;
12. the Plunge off the Pavilion Rooftops, counted by the Outer Trial.

T1's lift, boards, current and flood are laid on the Falls Pool's grid by the test itself. T2's parts play the rooms'
own rows:

13. Cloud Lung: a flight north counts as one east does;
14. the hatches: Old Ma's storeroom and the Fisher's Hut shut before The Runaway Kite and open after it, and each
    library's galleries by rank;
15. the Reed Shallows' three driftwood logs and Bend Shore's ferry, ridden end to end;
16. the drum, the bent culm and the lotus leaf: a body bounces off each onto the floor above;
17. the Jade trial's two lifts and the quarry's crane carry their rider up; the Cloud trial's planks give way into the
    pool under a body that stays, hold under a sprint, and the bell is rung from its ledge;
18. the Tunnels: a sprint crosses a pit's planks; a stop sends a plank down, the spikes strike, and the plank comes back;
19. the Flooded Gate's plank and drain; the Hall of Lanterns' lantern, boarded from the gallery and ridden along its
    arc; the Serpent's and the Abbot's floods, raised and lowered; the Rapids' areas and current;
20. Between Two Walls: three Wall-Step kicks up the Echo Cliffs' shaft onto the nest, counted;
21. the Frozen Shrine's ice and an icicle shelf, the monastery's rotten floor, the ridge's wind;
22. Breath Control: the bank stops a body without it; with it the body swims, climbs out, and sinks after thirty
    seconds;
23. the shallows' slow, and frozen ground's full pace;
24. the rooftop chases at Gate Street and the Stoneford market, played and won.

T3's parts (the low gravity's floor and a no-flight volume are laid on the Falls Pool by the test itself, as T1's lift):

25. the Lower Pit's cracked slab: the shards sealed and hidden under it, a walk stopped at its foot, a hop that holds it,
    a Plunge from over it breaking it and striking on the floor below, the shards shown and taken, the slab whole again
    on the next visit;
26. Frostpine Climb's and Rimefrost Summit's ice, the side view's traction: a sprint let go slides on;
27. no-flight: the Windbridge, Old Ma's store (an interior), the Tunnels (a dungeon), the Inverted Hall, the Leviathan's
    Maw and the Starsea crossing refuse it and the hold glides; a flight into a no_flight volume ends there
    (`flight_ended`, `no_flight`) and comes down, and the hold glides inside it;
28. low gravity: off until its switch is turned through `toggle_gravity`, then a standing jump climbs 1/0.45 as high and
    hangs longer; turned again, gravity is back;
29. the Starsea's four docks: the yard's refused by the prototype's gate with R9's rooms stood off the grid
    (`tests/lib/off_grid.gd`); all four sailed, the crossing's foes aboard on the deck's floors, port made; the yard's
    chart table and slipway open their pages from the grid;
30. the late zones' light: the tomb and the Clan Hearth lamp-lit at noon, the sky-sea zones at the story's night, every
    star lantern on the Arrival Quay lit;
31. R8's two played by shortcut: the Jellyfish Shallows waded at 0.7 of the pace, and Spirit Sense's pulse showing the
    Smugglers' Cove's crack;
32. the swim's stroke: two or three pulls in two seconds, each with its wake; the pull runs the walk's frames, the glide
    holds its rest frame;
33. the drum's skin at rest, pressed, springing back, at rest, as it launches a body;
34. the Hall of Lanterns' circling lantern goes round upright (one row on the plane, its deck up twice its radius) and
    carries its rider up;
35. the monastery's rotten floor stays gone over the body under it past its time, and comes back once it steps out;
36. the Tunnels' pits lie open a row either side of the planks: the spikes strike a body standing on them, the planks
    do not;
37. on the Windswept Ridge the wind pushes its edge factor's harder by a drop on a diagonal;
38. a flier three levels up is drawn as far south as it is high (over the crowns below it), at its feet again landed;
39. the star field's end (R9's rooms): the Orbit Ruins' four low-gravity rows, each off under its own switch; the
    Inverted Hall's east switch turned with its own interact, a standing jump at the high gallery's foot falling back in
    the heavy air and climbing onto it in the light, then heavy again; the Leviathan flying over its lagoon's water to its
    shoal; the star field starlit at noon and past its edge, the Lantern Heart lamp-lit; the Citadel Gate's Warden lamps
    and caged stars lit; the Tumbling Stair's brink over the void; the Nebula Verge's star-water; the crossing's streaks
    and star-water; the Falls Pool's water still the river's.

S12c's parts:

40. a jump and the Cloud Ladder Step's second announced, the landing with its fall's height; on the ox, off it to climb
    the rope, a jump off the face lands and the rider is back on;
41. the Paths Above: each of the six rows entered, landed on by its own art (four double jumps, two Wall-Step climbs up
    their shafts), announced on its ledge and found for the account;
42. off the Cliff Faces' brink to the void and back on the last safe spot with `fell_out` (5% of max HP, the "fell"
    text); with a full meter and the fortune stream seeded, the fall draws the Hidden Cave, the grotto's chest waits, and
    its way up leaves the body where it fell; a jump into the Willow Path's pond: the deep water entered, sunk, back on
    the bank with `fell_out`, the water left, the water's step its cue;
43. the Flooded Gate's shallows and drain entered and left; no dodge in the shallows, on frozen ground and dry ground it
    goes;
44. the fame greeting: unknown, nobody; Noted to Legendary, one of the village's people in each tier's words.

Pictures: `tools/dev/capture/capture.tscn -- traversal` writes `docs/architecture/topdown_mechanics/`:

- `01_raft_grey_pools.png`, plus the world view of each row under `world/`: the rafts, the vine, the glide over the
  spray, the updraft, the rope, flight;
- `rooms/cf_falls_pool.png`, the whole room;
- `traverse_x4.png`, the art sheet at four times (T2's sprites in its middle, T3's at its foot: the bounces' three
  frames, the open gate, the slab, its rubble, the spikes, the wake and the motes).

T2's set, `capture.tscn -- traversal_t2`, writes `docs/architecture/topdown_mechanics/t2/`, each row's world at x2 in
its own room:

- the hatches (Old Ma's storeroom, the Jade library's second gallery);
- the driftwood and the ferry;
- the drum, the bent culm and the lotus leaf;
- the Jade trial's lift and the quarry's crane;
- the Cloud trial's planks giving way, and gone into the pool;
- the Tunnels' spike pit, the Flooded Gate's plank and the lanterns;
- the Abbot's flood and the Wall-Step shaft;
- the court's ice, an icicle shelf, the monastery's rotten floor, the wind;
- the swim in the Drowned Grotto's pool, and the wade through the Scripture Well's flooded floor.

T3's set, `capture.tscn -- traversal_t3`, writes `docs/architecture/topdown_mechanics/t3/`, each row's world at x2 in
its own room:

- `01_cracked_slab_whole`, `02_cracked_slab_broken`: the Lower Pit's slab, then its rubble after the Plunge, the shards
  showing;
- `03_ice_frostpine_climb`, `04_ice_rimefrost_summit`: a slide on each sheet;
- `05_open_spikes_tunnels`: the pits' spikes beside the planks;
- `06_hatch_open_old_ma_store`: the storeroom's gate open after The Runaway Kite;
- `07_lantern_round_upright`: the Hall of Lanterns, the circling lanterns up their round;
- `08_swim_wake_drowned_grotto`: a stroke's wake behind the swimmer;
- `09_star_lanterns_arrival_quay`, `10_tomb_lamplit`, `11_clan_hearth_lamplit`: the late zones' light;
- `12_low_gravity_inverted_hall`: the east switch turned, the light air's motes over the hall's east half under the
  high gallery;
- `13_void_tumbling_stair`: the island's brink over the starry void;
- `14_star_water_nebula_verge`: the nebula's star-water;
- `15_crossing_deck_starsea`: the crossing's deck in the Starsea, its water streaming past;
- `16_warden_lamps_citadel_gate`: the Citadel Gate's Warden lamps lit at the story's night.

S12c's set, `capture.tscn -- s12c`, writes `docs/architecture/topdown_mechanics/s12c/world/`: each of the six paths
above at x2 with the body at its foot (the pine top, the workshop roof, the bamboo top, the Flooded Gate's ledge, the
shaft top behind the falls, the broken pillar), and the Herb Terraces' second bed at the head of its flight and the
Rapids Terraces' middle flight between its boulders.

## To do, in order

T2 did items 1 to 13 for the Act I rooms on the grid, T3 items 14 to 17 from Act II on. Every mechanic is on the grid;
what is left is art, in order: the mounts' rider pose and sheets (item 12), a flying pose (item 16), and the late foes'
swim rows (item 18).

1. ~~**Wings of Cloud**~~: Cloud Lung's air distance counts the plane's speed on the grid (T2). The Cloudwing Cranes,
   its third objective, have their top-down sheets (M2's monster batch).
2. ~~**Sealed ladders as open stairs**~~: hatches over the four rooms' flights (T2).
3. ~~**Reed Shallows' driftwood and Bend Shore's ferry**~~: `raft` rows (T2).
4. ~~**Bounces**~~: the drum, the bent culm and the lotus leaf (T2).
5. ~~**The Entry Trials and the quarry**~~: the Jade trial's lifts, the crane, the Cloud trial's planks (T2).
6. ~~**The Tunnels**~~: six flush `crumble` rows over two `hazard` pits (T2).
7. ~~**The Drowned Shrine and the gorge**~~: the planks, the currents, the lanterns, the two floods, the Rapids' current
   and its hazard's `areas` (T2).
8. ~~**The Echo Cliffs' shaft**~~: Between Two Walls played on the grid (T2).
9. ~~**The peaks' leftovers**~~: the icicles, the monastery's floors, the Frozen Shrine's ice, the ridge's wind (T2).
10. ~~**Breath Control**~~: the swim (T2).
11. ~~**Shallow water's slow**~~ (T2).
12. **Mounts' art**, written up (T2), not done. The rider needs a new body movement: sitting astride, the legs apart
    and bent at the knee, the hands on the reins or the mane, the body rocking with the mount's gait. AGENTS.md rule 4
    and rule 2 apply in full:
    - the pose drawn first on the unclothed body, in every drawn facing (5, mirrored to 8), and reviewed;
    - then matching frames on every body, hair, shirt, pants, shoes and weapon layer, in every dye (or an explicit
      hidden entry where a layer is absent: a weapon stowed);
    - the action added to the catalog;
    - the gallery inspected.

    Each mount species also needs a top-down sheet walking in every facing with a saddle and a rider's seat
    (the monster engine's `quadruped` plan, as M-batches draw foes); the riverstone ox is the first. The motor and the
    rules are done (T1): the pace, stepping down to climb and back on at the top, no Wall-Step. Act I's story needs
    none: the Mount slot opens at the Beast Hall, and Riding the Wind (cs1) is Cloud Stride's lesson. It belongs with
    the mount's first sheet, as a batch of its own.
13. ~~**Rooftop chases**~~: both played on the grid (T2).
14. ~~**The Lower Pit's cracked slab**~~: a `crack` row, a Plunge breaks it and strikes below, the shards sealed under
    it until then (T3).
15. ~~**Act II and later, with their rooms**~~ (T3): no-flight volumes (`no_flight` rows; the rooms and types refuse
    flight as the side view's), the Starsea's docks (gated while a crossing or a port has no layout, played once both
    are), low gravity and its jade switches (`low_gravity` rows, `toggle_gravity`), Rimefrost's ice, the late zones'
    light; the star field's (R9): the Orbit Ruins' four low-gravity rows, the crossings' moving water, the void, star-water
    and the late props' light.
16. **Presentation.** T2's own (T3): ~~a swim stroke~~ (a pull and a glide on the walk's own frames, each pull's wake),
    ~~a bounce that gives~~, ~~an open hatch's look~~, ~~the lanterns' circle upright~~. From T1: ~~a flier keyed over
    tree crowns once it is above them~~ (T3: three levels over its floor it sorts as far south as it is high). Left: a
    flying pose (the flier stands on its cloud in the idle pose); it is a new body movement under AGENTS.md rule 4.
17. ~~**Edge cases T2 leaves**~~ (T3): returning boards wait for the body under them; the pits open beside their planks;
    the wind looks along eight ways.
18. **The late foes' swim** (art, the late monster batch). The Nebula Leviathan is the side view's flier and crosses its
    lagoon on the grid (T3), drawn as a stand-in. Its sheet should have a `swim` row, so decision 44's rule plays it
    over the water, as the marsh leech's does. No mechanic waits on it.
19. ~~**What the side view carried**~~ (S12c): the jumps, landings, falls out of a room and volumes announced, the paths
    above art-gated, the Hidden Cave drawn again, the shallows' dodge rule, the fame greeting. The only gap is art (a
    falling pose; the jump's falling frame stands in), on hold with all character art (AGENTS.md rule 10).
