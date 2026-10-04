# The side view's mechanics on the grid (T1, T2)

The top-down view is to replace the side view. Before the side view can go, every mechanic that only it has needs a
top-down version: a raft has to carry a body on the height grid, an updraft has to lift it, a set piece's foes have to
come in on the grid's floors. This page lists every such mechanic, says where it lives, which rooms and quests use it,
and whether the grid covers it. It ends with what is still to do, in order.

T1 built the machinery and laid the first rows. T2 laid the rows of every Act I room on the grid and built what T1 had
not: sealed hatches, swinging lanterns, boards that are the floor itself, spike pits, ice, wind, the swim and the
shallows' slow (the to-do's items 1 to 13, "T2" below).

The rule throughout: **the authorities keep their rules; the grid only says where things stand.** A raft rides the side
view's own mover function on the room's clock, a glide spends Combat's QI, a climb asks the World authority whether it
is open. The top-down side adds placement (spec rows, layout cells), the motor's response, and the drawing.

## How the grid carries the side view's traversal

| Part | File | What it does |
|---|---|---|
| Spec rows | `tools/content/rooms/spec.py` (`traverse`, `stage`), `engine.py` (`TRAVERSE_KEYS`, `stage_cells`) | A room's traversal, each piece named by its side-view id, in cells. T2: a raft's and a bounce's `look`, a crumble's `under` and `look`, and the `hatch`, `lantern`, `hazard`, `ice` and `wind` rows |
| Layout checks | `tools/data/topdown_rooms.py` `check_traverse` | A raft runs over open water clear of props, with landings at both ends; a lift rests on a floor; a climbable's foot is reached and its top is a level or more higher; a volume names a side-view volume of its kind; a stage cell is open, reached and off the lanes. T2: a hatch lies on a flight and names a sealed climbable; a lantern sweeps neither a prop nor a floor over its level, and somewhere on its sweep has a floor within a level beside it; boards that are the floor lie at their level and are reached |
| Model | `scripts/topdown/topdown_traverse.gd` (`TopdownTraverse`) | The rows in world units, read once from the layout and kept on the room (`TopdownRoom.traverse`). Queries: the deck under a point, the updraft round a body, the climbable a body may take, the boards' state, a current's push, a flood's water. T2: the shut hatch, the boards gone from a floor, the hazard volumes, the ice, the wind's push, a lantern's place on its arc |
| Motor | `scripts/topdown/topdown_motor.gd` | Floors include decks, whole boards and risen water. A body rides a deck, is pushed by a current, rises in an updraft, glides, flies, double-jumps, kicks off a wall, climbs, and bounces. T2: a shut hatch is a wall; boards gone from a floor drop it or open a hole; a body with Breath Control swims open water; the shallows slow the walk; ice keeps the speed; the wind pushes |
| Player | `scripts/topdown/topdown_player.gd` | Asks Combat for every art (glide, flight, Plunge, air dash) and announces each use (`art_used`, `mover_boarded`, `climb_started`/`climb_finished`) through `LocalAuthority.announce`, as the side view's solver does. T2: asks the World authority whether each hatch is open (`climbable_open`) and says why a shut one is; Breath Control and a Water Sphere's frozen ground reach the motor; a swimmer is drawn from the chest up |
| View | `scripts/topdown/topdown_traverse_view.gd` | Draws the rafts and lifts, the vine, rope, ladder and chain tiles, the spray, the boards, the flood's water, the glide's leaf and the flight's cloud. T2: the driftwood and the planks, the sealed hatches, the drum, the lotus leaf and the bent bamboo, the lanterns on their chains, the pit, the pool or the shadow under gone boards, the icicle shelves, the ice, the wind, the swimmer's ripple; a flood's water only over the floors it covers |
| World authority | `world_hazards.gd` `tick_hazard_volumes` | T2: on the grid a side-view hazard volume stands on its layout's `hazard` cells and strikes a body down in them, its numbers the side view's |
| Combat | `combat_flight.gd` `_air_distance` | T2: on the grid the air distance is the plane's speed, so Cloud Lung counts flight in any direction |
| Numbers | `tools/data/stats.py` → `data/movement.json` `topdown.traverse` | The side view's speeds scaled to the grid's jump (impulse 400 against the side view's 530). T2: `side_scale`, the swim's `swim_s`, `swim_factor` and `swim_out`, `shallow_factor`, `ice_traction`, `wind_edge` |
| Art | `tools/art/topdown/traverse.py`, `build_traverse.py` → `art/topdown/traverse.png`, `data/topdown/traverse_art.json` | Original pixel art, nearest neighbour, byte-identical builds; `--review` writes `topdown_mechanics/traverse_x4.png` (T2's sprites in its lower half) |

The grid's own queries never count a deck, an updraft or a climb: not `height_at`, not `find_path`, not the reach
checks, not auto-path. Each is an extra way to get somewhere, never the only way.

The body reuses existing top-down actions and adds no new body animation. A climb plays `work_hang`. A glide, a flight
and a raft ride use the idle and walk poses, with the leaf over the body or the cloud under its feet. T2's swim plays the
walk and the idle, the figure sunk and cut at the water's line (`TopdownFigure.draw`'s clip), a ring of water round it.

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
grid covers 39 of them: all 18 of traversal, 8 hazards, 9 events and 4 others. Every Act I room on the grid has its
rows. The four left are low gravity, the cracked slab, the Starsea crossing and gravity switches. Some parts are also
still missing: the mounts' art, the Cloudwing Cranes' sheets, no-flight volumes and the docks' routes. All of them are
in the to-do at the end.

"Rooms" counts the side-view rooms that use the mechanic. "On the grid" says what the grid does for them.

### Traversal (18)

| Mechanic | Side view | Rooms, quests | On the grid |
|---|---|---|---|
| Rafts and floating decks | `ZoneGeometry.mover_offset`, room `movers` | Grey Pools ×2, hermit's pond, Reed Shallows ×3 driftwood, Bend Shore ferry, Flooded Gate ×3 planks, Sky Ledges ledge | **Yes.** `raft` rows: the Grey Pools' two rafts and the hermit's raft. T2: the Reed Shallows' three driftwood logs along the bank (`look: "driftwood"`), Bend Shore's ferry between the ford's causeway and the shrine's steps, and the Flooded Gate's three planks across the sunk gate (`look: "plank"`). The Sky Ledges' ledge became terraces (R4) |
| Lifts | movers with a vertical path | Jade Entry Trial planks ×2, Quarry Rim crane (trigger) | **Yes.** T2: `lift` rows for the Jade trial's two planks, up to the second and third roofs' eaves, and the quarry's crane (mode `trigger`), from the yard to the bench |
| Swinging and circling lanterns | `mover_offset` swing and circle | Hall of Lanterns ×5 | **Yes (T2).** `lantern` rows: five decks over the rubble between the galleries. Two swinging lanterns and a circling one lead a level up from the gallery to the rest; a swinging one and a circling one lead from the rest toward the loft |
| Updrafts | `MovementSolver` updraft volumes | Falls Pool; Cliff Faces and Sky Ledges | **Yes.** The falls' spray lifts a glider to the spray ledge. The Crane Cliffs' updrafts became terraces and flights (R4) |
| Climbables (vine, ladder, rope, chain) | `MovementSolver` climbing, `WorldAuthority.climbable_open` | 151 rooms | **Yes.** `vine`/`ladder`/`rope`/`chain` rows: the Falls Pool's vine and rope. Converted rooms use stairs elsewhere. T2: the four rooms whose ladders are sealed lay a `hatch` over the stair |
| Falling Leaf Glide | `CombatFlight.glide`, `MovementSolver.glide` | Leaf on the Wind (qk3) | **Yes**, with the lesson played on the grid |
| Plunge | `CombatFlight.plunge` | Outer Trial (ch 1), Pavilion Rooftops | **Yes** (the motor's drop predates T1). The Outer Trial's objective is now checked on the grid |
| Water Skimming | `MovementSolver._water` | Skipping Stones | **Yes**, with the lesson played |
| Swallow Dart (air dash) | `MovementSolver.air_dash` | Swallow Dart (qk7) | **Yes**, along the stick, holding the height |
| Cloud Ladder Step (double jump) | `MovementSolver` | Cloud Ladder (qu6) | **Yes** |
| Wall-Step | `MovementSolver.wall_step` | Between Two Walls (ht4), Echo Cliffs shaft | **Yes.** T2: the Echo Cliffs' shaft between its two walls (raised a level, to five over the shaft's floor) climbs to the vultures' nest at its head, three levels up. The lesson's three kicks count on the grid |
| Breath Control (swimming) | `MovementSolver._water` (swim 30 s) | deep water in 7 rooms, the Drowned Grotto | **Yes (T2).** Open water is swum for 30 s at 0.6 of the pace, and the body climbs out onto a bank; out of breath, it sinks to its safe spot. The swimmer is the walk, cut at the water's line |
| Flight (Cloud Stride) | `CombatFlight` flight, the side solver | Wings of Cloud (ch 7, the gate to Act II) | **Yes.** Jump held as the body comes down takes off, held it climbs to its ceiling, Evade held lands; out of QI it falls; where refused, the hold glides. Wings of Cloud's "take to the air" counts on the grid |
| Mounts | `PetAuthority.mount_speed`, `ground_mounted`, climb step-down | Riding the Wind (cs1) | **The rules, yes:** the mount's pace, stepping down to climb and back on at the top, no Wall-Step. No rider art yet: it needs a new body animation, written up in the to-do. Act I's story needs no mount |
| Bounces (drum, lily pad, bent bamboo) | bounce volumes | Fairground, Whispering Bamboo, Grey Pools | **Yes.** T2: the Fairground's drum by the Cloud hall (up onto its roof), the bent culm at the east knoll's foot, the lotus leaf at the lily ledge's foot, each drawn by its `look` |
| Crumbling boards | crumble volumes | Tunnels ×6, Cloud Entry Trial, Forgotten Monastery ×2, Frozen Shrine ×3 | **Yes.** T2: boards that are the floor and open on a hole (the Tunnels' planks over their spike pits, the Cloud trial's plank walk over its pool), the monastery's rotten floors (dropping a level), and the Frozen Shrine's icicle shelves over the terrace |
| Timed routes (Cloud Steps, docks) | route objects, `route_finish` | Cliff Stair; 4 dock rooms | **Yes** for the Cloud Steps (the layout places the bell; `topdown_tutorial`). The docks have no layouts yet |
| Rooftop chases | chase objects | Gate Street, Stoneford market | **Yes**, by the layouts' routes. T2: both chases are played on the grid, the thief caught over the roofs |

### Hazards (10)

| Mechanic | Side view | Rooms | On the grid |
|---|---|---|---|
| Currents | current volumes | Flooded Gate ×2, Rapids Terraces | **Yes.** T2: the Flooded Gate's drain along the court's south rows, the flood's pull over the sunk gate, and the Rapids' white water. A body riding a deck is not pushed |
| Rising water | rising_water volumes, `ZoneGeometry.on_event` | Serpent's Shallows, Abbot's Sanctum (boss phases) | **Yes.** `flood` rows follow the side volume's own `rise` script through the World authority's boss-phase hook. T2: the Serpent's shallows (back down when it is beaten) and the Abbot's sanctum (back after its hold), a level deep |
| Deep water | water_deep volumes | 7 rooms | **Yes**: open water returns a walking body to its safe spot, and a flood moves the safe spot to dry floor |
| Shallow water's slow | water_shallow volumes (×`speed`) | 11 rooms | **Yes (T2):** every wading floor (the tile set's `flood` paints) at 0.7 of the pace, full pace on a Water Sphere's frozen ground |
| Spike pits | hazard volumes | Tunnels ×2 | **Yes (T2):** `hazard` rows under the planks; a body fallen into a pit is struck by the side volume's spikes |
| Ice | ice volumes (traction) | Frozen Shrine, Rimefrost ×2 | **Yes (T2)** for the Frozen Shrine's court and terrace (`ice` rows). Rimefrost is R6's |
| Wind volume | wind volumes | Windswept Ridge | **Yes (T2):** the ridge's `wind` row, beside its `wind_gust` hazard |
| Low gravity | low_gravity volumes | Orbit Ruins ×3 | **No** (no layouts yet) |
| Room hazards (strike, aura, gust, pool, flow: 16 kinds) | `WorldHazards`, `HazardRules` | 27 room uses | **Yes**, on the World authority: strikes fall on the grid's floors, auras find their shelters by placed objects, gusts drift the body, pools and flows take the layout's `areas` (T2: the Rapids' strand and white water) |
| Cracked slab | cracked blocks broken by a Plunge | Lower Pit | **No** |

### Room events and waves (10)

All covered by the one rule above, except the Starsea crossing:

- set pieces at rite circles (15 rooms, 10 on the grid);
- a room's own event (the Hollow Night on its layout cells);
- Trial Tower floors;
- the Grove's waves;
- spatial rifts;
- treasure births and first-fruit guardians;
- heart demons;
- the sect's raid;
- the pole trial's ground rule;
- **the Starsea crossing**: not covered; its rooms have no layouts.

### Other (5)

| Mechanic | On the grid |
|---|---|
| Teleport stones, transfer arrays | **Yes**: objects at the layout's cells (R4: a teleport lands in front of its stone) |
| No-flight rooms | **Yes**: `flight_allowed` reads the room. **No-flight volumes: no**, they are side-view rects |
| Sealed climbables | **Yes**: a climb row asks `climbable_open`, and T2's hatches seal the four rooms' stairs by the same rule |
| Cloud Lung's air distance | **Yes (T2)**: on the grid `CombatFlight._air_distance` counts the plane's speed (in the side view, x alone) |
| Gravity switches | **No** (the Orbit Ruins have no layouts) |

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

Pictures: `tools/dev/capture/capture.tscn -- traversal` writes `docs/architecture/topdown_mechanics/`:

- `01_raft_grey_pools.png`, plus the world view of each row under `world/`: the rafts, the vine, the glide over the
  spray, the updraft, the rope, flight;
- `rooms/cf_falls_pool.png`, the whole room;
- `traverse_x4.png`, the art sheet at four times (T2's sprites in its lower half).

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

## To do, in order

T2 did items 1 to 13 for the Act I rooms on the grid. What is left, in order:

1. ~~**Wings of Cloud**~~: Cloud Lung's air distance counts the plane's speed on the grid (T2). Left: the Cloudwing
   Cranes, its third objective, need top-down sheets (M2's monster batch).
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
14. **The Lower Pit's cracked slab** (R3's room, on the grid): cracked blocks a Plunge breaks open. It is the one
    mechanic of an Act I room left; it needs a row (a `crack` over the slab's cells, the side view's block id) and the
    Plunge's landing to open it.
15. **Act II and later, with their rooms**: no-flight volumes as grid rects, the Starsea crossing, low gravity and the
    Orbit Ruins' gravity switches, the docks' timed routes; Rimefrost's ice (R6's rooms) takes T2's `ice` rows.
16. **Presentation**: a flying pose (the flier stands on its cloud in the idle pose), and a flier keyed over tree crowns
    once it is above them. T2's own:
    - a swim stroke of its own, a new body movement under rule 4 (the swimmer now plays the walk, cut at the water's
      line);
    - a bounce that gives as it launches (the drum's skin, the culm's spring), and an open hatch's look (the gate is
      simply gone);
    - the lanterns' circle lies on the plane (the side view's circle stands upright).
17. **Edge cases T2 leaves**:
    - boards that come back while a body stands under them lift it onto them (the monastery's floors);
    - a spike pit opens only where its planks go (no open pit cells beside them);
    - the wind's edge factor reads a drop within `wind_edge` along the four axes only.
