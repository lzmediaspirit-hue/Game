# The side view's mechanics on the grid (T1)

The top-down view is to replace the side view. Before the side view can go, every mechanic that only it has needs a
top-down version: a raft has to carry a body on the height grid, an updraft has to lift it, a set piece's foes have to
come in on the grid's floors. This page lists every such mechanic, says where it lives, which rooms and quests use it,
and whether the grid covers it. It ends with what is still to do, in order.

The rule throughout: **the authorities keep their rules; the grid only says where things stand.** A raft rides the side
view's own mover function on the room's clock, a glide spends Combat's QI, a climb asks the World authority whether it
is open. The top-down side adds placement (spec rows, layout cells), the motor's response, and the drawing.

## How the grid carries the side view's traversal

| Part | File | What it does |
|---|---|---|
| Spec rows | `tools/content/rooms/spec.py` (`traverse`, `stage`), `engine.py` (`TRAVERSE_KEYS`, `stage_cells`) | A room's traversal, each piece named by its side-view id, in cells |
| Layout checks | `tools/data/topdown_rooms.py` `check_traverse` | A raft runs over open water clear of props, with landings at both ends; a lift rests on a floor; a climbable's foot is reached and its top is a level or more higher; a volume names a side-view volume of its kind; a stage cell is open, reached and off the lanes |
| Model | `scripts/topdown/topdown_traverse.gd` (`TopdownTraverse`) | The rows in world units, read once from the layout and kept on the room (`TopdownRoom.traverse`). Queries: the deck under a point, the updraft round a body, the climbable a body may take, the boards' state, a current's push, a flood's water |
| Motor | `scripts/topdown/topdown_motor.gd` | Floors include decks, whole boards and risen water. A body rides a deck, is pushed by a current, rises in an updraft, glides, flies, double-jumps, kicks off a wall, climbs, and bounces |
| Player | `scripts/topdown/topdown_player.gd` | Asks Combat for every art (glide, flight, Plunge, air dash) and announces each use (`art_used`, `mover_boarded`, `climb_started`/`climb_finished`) through `LocalAuthority.announce`, as the side view's solver does |
| View | `scripts/topdown/topdown_traverse_view.gd` | Draws the rafts and lifts, the vine, rope, ladder and chain tiles, the spray, the boards, the flood's water, the glide's leaf and the flight's cloud |
| Numbers | `tools/data/stats.py` → `data/movement.json` `topdown.traverse` | The side view's speeds scaled to the grid's jump (impulse 400 against the side view's 530) |
| Art | `tools/art/topdown/traverse.py`, `build_traverse.py` → `art/topdown/traverse.png`, `data/topdown/traverse_art.json` | Original pixel art, nearest neighbour, byte-identical builds; `--review` writes `topdown_mechanics/traverse_x4.png` |

The grid's own queries never count a deck, an updraft or a climb: not `height_at`, not `find_path`, not the reach
checks, not auto-path. Each is an extra way to get somewhere, never the only way.

The body reuses existing top-down actions and adds no new body animation. A climb plays `work_hang`. A glide, a flight
and a raft ride use the idle and walk poses, with the leaf over the body or the cloud under its feet.

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

43 side-view-only mechanics in four groups: traversal 18, hazards 10, room events and waves 10, other 5. The grid now
covers 31 of them: 16 traversal, 4 hazards, 9 events and 2 others, and one more (sealed climbables) partly. Five of
the 31 (lifts, bounces, crumbling boards, currents, floods) are done in the engine, the motor and the tests but still
wait for their rooms' rows. The gaps are listed below and again in the to-do at the end.

"Rooms" counts the side-view rooms that use the mechanic. "On the grid" is how many of those have a layout today
(86 of 168 rooms do).

### Traversal (18)

| Mechanic | Side view | Rooms, quests | On the grid |
|---|---|---|---|
| Rafts and floating decks | `ZoneGeometry.mover_offset`, room `movers` | Grey Pools ×2, hermit's pond, Reed Shallows ×3 driftwood, Bend Shore ferry, Flooded Gate ×3 planks, Sky Ledges ledge (10 rooms on the grid) | **Yes.** `raft` rows: the Grey Pools' two rafts and the hermit's raft. The Sky Ledges' ledge became terraces (R4). Reed Shallows, Bend Shore and the Flooded Gate still need rows |
| Lifts | movers with a vertical path | Jade Entry Trial planks ×2, Quarry Rim crane (trigger) | **Engine, motor, view and test.** `lift` rows. The rooms' rows are still to do |
| Swinging and circling lanterns | `mover_offset` swing and circle | Hall of Lanterns ×5 | **No** |
| Updrafts | `MovementSolver` updraft volumes | Falls Pool; Cliff Faces and Sky Ledges | **Yes.** The falls' spray lifts a glider to the spray ledge. The Crane Cliffs' updrafts became terraces and flights (R4) |
| Climbables (vine, ladder, rope, chain) | `MovementSolver` climbing, `WorldAuthority.climbable_open` | 151 rooms (68 on the grid) | **Yes.** `vine`/`ladder`/`rope`/`chain` rows: the Falls Pool's vine and rope. Converted rooms use stairs elsewhere. Four rooms' sealed ladders are open stairs (to-do 1) |
| Falling Leaf Glide | `CombatFlight.glide`, `MovementSolver.glide` | Leaf on the Wind (qk3) | **Yes**, with the lesson played on the grid |
| Plunge | `CombatFlight.plunge` | Outer Trial (ch 1), Pavilion Rooftops | **Yes** (the motor's drop predates T1). The Outer Trial's objective is now checked on the grid |
| Water Skimming | `MovementSolver._water` | Skipping Stones | **Yes**, with the lesson played |
| Swallow Dart (air dash) | `MovementSolver.air_dash` | Swallow Dart (qk7) | **Yes**, along the stick, holding the height |
| Cloud Ladder Step (double jump) | `MovementSolver` | Cloud Ladder (qu6) | **Yes** |
| Wall-Step | `MovementSolver.wall_step` | Between Two Walls (ht4), Echo Cliffs shaft | **The art, yes** (a kick off a face pushed into). The Echo Cliffs' shaft is still to do |
| Breath Control (swimming) | `MovementSolver._water` (swim 30 s) | deep water in 7 rooms | **No.** On the grid deep water returns the body to its safe spot |
| Flight (Cloud Stride) | `CombatFlight` flight, the side solver | Wings of Cloud (ch 7, the gate to Act II) | **Yes.** Jump held as the body comes down takes off, held it climbs to its ceiling, Evade held lands; out of QI it falls; where refused, the hold glides. Wings of Cloud's "take to the air" counts on the grid |
| Mounts | `PetAuthority.mount_speed`, `ground_mounted`, climb step-down | Riding the Wind (cs1) | **The rules, yes:** the mount's pace, stepping down to climb and back on at the top, no Wall-Step. No rider art yet |
| Bounces (drum, lily pad, bent bamboo) | bounce volumes | Fairground, Whispering Bamboo, Grey Pools | **Engine, motor and test.** `bounce` rows. The rooms' rows are still to do |
| Crumbling boards | crumble volumes | Tunnels ×6, Cloud Entry Trial, Forgotten Monastery, Frozen Shrine | **Engine, motor, view and test.** `crumble` rows. The rooms' rows are still to do |
| Timed routes (Cloud Steps, docks) | route objects, `route_finish` | Cliff Stair; 4 dock rooms | **Yes** for the Cloud Steps (the layout places the bell; `topdown_tutorial`). The docks have no layouts yet |
| Rooftop chases | chase objects | Gate Street, Stoneford market | **Yes**, by the layouts' routes. No top-down check yet |

### Hazards (10)

| Mechanic | Side view | Rooms | On the grid |
|---|---|---|---|
| Currents | current volumes | Flooded Gate ×2, Rapids Terraces | **Engine, motor and test.** `current` rows. The rooms' rows are still to do |
| Rising water | rising_water volumes, `ZoneGeometry.on_event` | Serpent's Shallows, Abbot's Sanctum (boss phases) | **Engine, motor, view and test.** `flood` rows follow the side volume's own `rise` script through the World authority's boss-phase hook. The rooms' rows are still to do |
| Deep water | water_deep volumes | 7 rooms | **Yes**: open water returns a walking body to its safe spot, and a flood moves the safe spot to dry floor |
| Shallow water's slow | water_shallow volumes (×`speed`) | 11 rooms | **No**: R2's wading floors are walked at full pace |
| Spike pits | hazard volumes | Tunnels ×2 | **No** |
| Ice | ice volumes (traction) | Frozen Shrine (on the grid), Rimefrost ×2 | **No** |
| Wind volume | wind volumes | Windswept Ridge (on the grid) | **No** (its `wind_gust` hazard's drift is covered) |
| Low gravity | low_gravity volumes | Orbit Ruins ×3 | **No** (no layouts yet) |
| Room hazards (strike, aura, gust, pool, flow: 16 kinds) | `WorldHazards`, `HazardRules` | 27 room uses | **Yes**, on the World authority: strikes fall on the grid's floors, auras find their shelters by placed objects, gusts drift the body, pools take the layout's `areas`. Gap: the Rapids' current hazard has no `areas` |
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
| Sealed climbables | **Partly**: a climb row asks `climbable_open`, but four rooms' sealed ladders are open stairs on the grid |
| Cloud Lung's air distance | **No**: `CombatFlight._air_distance` counts `velocity.x`, so flying north or south counts nothing |
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

Rows a room has no use for yet (the lift, the boards, the current, the flood) are laid on the Falls Pool's grid by the
test itself.

Pictures: `tools/dev/capture/capture.tscn -- traversal` writes `docs/architecture/topdown_mechanics/`:

- `01_raft_grey_pools.png`, plus the world view of each row under `world/`: the rafts, the vine, the glide over the
  spray, the updraft, the rope, flight;
- `rooms/cf_falls_pool.png`, the whole room;
- `traverse_x4.png`, the art sheet at four times.

## To do, in order

Story order first, then the systems no story room needs yet. A "row" is a line in a room's spec; each room's owner
adds it, and `check_traverse` holds it to the grid.

1. **Sealed ladders as open stairs** (prologue to chapter 3): Old Ma's storeroom, the fisher's loft, the Jade and
   Cloud libraries' upper floors. The side view gates them through `climbable_open`. Give each a `ladder` row under
   its side id in place of the stair, or gate the stair itself.
2. **Reed Shallows' driftwood ×3 and Bend Shore's ferry**: `raft` rows.
3. **Bounces**: `bounce` rows for the Fairground's drum, the Whispering Bamboo's bent bamboo and the Grey Pools' pad.
4. **The Entry Trials and the quarry**: `lift` rows for the Jade trial's planks and the Quarry Rim's crane (mode
   `trigger`), a `crumble` row for the Cloud trial's ledge. Then review the lift and boards art in place and capture
   them.
5. **The Tunnels**: six `crumble` rows. The spike pits need a hazard area on the grid (an `areas` kind that
   `HazardRules` reads, or a traversal `hazard` kind).
6. **The Drowned Shrine and the gorge** (chapter 5):
   - the Flooded Gate's planks (`raft` ×3) and currents (`current` ×2);
   - the Hall of Lanterns' swinging and circling lanterns (a `swing`/`circle` row: `mover_offset` already computes
     them, the rows and a deck that moves on its arc are missing);
   - floods for Serpent's Shallows and the Abbot's Sanctum (`flood`, named by the side volume's id);
   - the Rapids' current (`current`) and its hazard's `areas`.
7. **The Echo Cliffs' shaft** (Between Two Walls, ht4): two facing walls on the grid to kick up between, and its
   three-kick objective played on the grid.
8. **Wings of Cloud's other objectives** (chapter 7): the art and the first objective are done, and the Cliff Faces
   are on the grid (R4). The Cloudwing Cranes need top-down sheets (M-batches). `_air_distance` should count the
   plane's speed on the grid.
9. **The peaks' leftovers**: the Frozen Shrine's and the Forgotten Monastery's crumbling floors (`crumble` rows), the
   Frozen Shrine's ice and the Windswept Ridge's wind volume (motor rules: the side view's traction and the wind's push).
10. **Breath Control**: swimming deep water for its 30 s on the grid instead of the reset.
11. **Shallow water's slow** on wading floors.
12. **Mounts' art**: a rider on its mount, every facing. AGENTS.md rule 4: the body first.
13. **Rooftop chases**: a top-down check of the thief's run at Gate Street and the Stoneford market.
14. **Act II and later, with their rooms**: no-flight volumes as grid rects, the Starsea crossing, low gravity and the
    Orbit Ruins' gravity switches, the docks' timed routes, the Lower Pit's cracked slab broken by a Plunge.
15. **Presentation**: a flying pose (the flier stands on its cloud in the idle pose), and a flier keyed over tree crowns
    once it is above them.
