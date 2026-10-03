# The room engine (E1)

Audit 45 §6.1, phase 3. A room on the height grid is written as a short spec, not as a function of coordinates. The
engine compiles the spec to the same `Layout` that `tools/data/topdown_rooms.py` always wrote, and from it to
`data/topdown/<room>.json`. The game reads nothing new.

| File | What it holds |
|---|---|
| `tools/content/rooms/spec.py` | `room(id, **keys)`, the spec's constructor, and the format (its docstring) |
| `tools/content/rooms/engine.py` | the compiler: `Build(spec).run()` returns the `Layout` |
| `tools/content/rooms/biomes.py` | the looks a generated room draws from: ground, stair paint, flora pools by role, density |
| `tools/content/rooms/specs/<zone>.py` | the rooms, one module a zone, each listing its `ROOMS`; `specs/__init__.py` lists the zones |
| `tools/content/rooms/build.py` | the command line: build, `--show`, `--new` |
| `tools/content/rooms/test_engine.py` | the engine's own checks, the runners' `room_engine` gate |
| `tools/data/topdown_rooms.py` | the `Layout` DSL, the `Grid` walking rules, the checks, the build loop, the parity with the game |

## The spec

A real room, the Caravan Road (`specs/caravan_road.py`), 20 lines:

```python
CR_CARAVAN_ROAD = room(
    "cr_caravan_road", size=(72, 30), biome="valley_road",
    bands=[("ridge", 0, 3, dict(level=3, paint="r", wall=True)),       # strata from the north, the room's width
           ("hillside", 3, 6, dict(level=1)),
           ("road", 12, 4, dict(paint="d", walk=True)),                 # the main walk: verges, ways, foes
           ("meadow", 16, 8, dict(level=0)),
           ("creek", 25, 5, dict(water=True, wavy=True))],              # a shore that is never a ruled line
    features=[("outcrop", (27, 4, 8, 3), dict(level=2, paint="r")),     # shapes over the bands, in order
              ("cart_east", (42, 9, 6, 3), dict(paint="d")),
              ("cart_west", (14, 16, 7, 3), dict(paint="d"))],
    stairs="auto",                                                      # up the cut, and onto the outcrop
    ways={"east": ("e", "road"), "west": ("w", "road"), "hideout": ("n", 56, dict(cut=3))},
    spawn="east",
    anchors={"crate_7": "outcrop@29", "crate_8": "outcrop@32", "herb_1": "hillside@6", "ore_2": "ridge.s1@51",
             "jar_3": "verge.s@8", "crate_4": "cart_east@44", "jar_5": "verge.s@45", "crate_6": "verge.n@64",
             "sign_cr": "road.n@60", "npc_peddler_shao": "cart_west@17"},
    props=[("crates", 15, 17), ("barrel", 19, 18), ("crates", 45, 10), ("barrel", 47, 9)],   # the broken carts' loads
    flora={"hillside": dict(density=0.42)},
    ground={"sand": ["creek.bank"]},
    foes="auto")
```

The keys (the full list is `spec.py`'s docstring):

- **Shape.** `size`; `base` and `level` (the ground under everything; `"~"` is water); `walls` for an interior;
  `bands` (full-width strata, laid first, in order); `features` (shapes laid over them, in order: a rect, a
  `shape="round"` cavern or pond, `rise=(from, to)` for a flight); a band or a feature may be `walk`, `wall`, `water`
  or `wavy`.
- **Ways.** `("e", row)`, `("w", row)`, `("n", col)`, `("s", col)`: an edge way, a band's name for its middle; on an
  interior's wall the doorway is cut. `cut=3` cuts a path from the walk to a north or south edge (a gorge through a
  wall). `("door", name)` opens into a named building prop; `path=row | (row, paint) | "auto"` lays its path. A dict
  `{at, dir, arrive, span}` is a way anywhere.
- **Things.** `anchors` give every NPC and object of the side-view room a cell or an anchor:

  | Anchor | Resolves to |
  |---|---|
  | `"road@34"` | a band at a column, its middle row first |
  | `"road.n@60"`, `"road.s"`, `.n2`, `.s2` | the row north or south of a band or a feature (two rows off) |
  | `"den.back@12"`, `"den.front"` | a shape's own first or last row, column by column |
  | `"knoll.top"`, `"knoll@x"` | a feature's middle, or any of its cells |
  | `"verge"`, `"verge.s@40"` | within three rows of the walk band |
  | `"walk.n@68"` | the row along the walk |
  | `"bank"`, `"water"` | land beside the water; the water by the land (a fishing spot) |
  | `"wall_foot"` | the two rows under a `wall` band |
  | `"door:hut"`, `"near:herb_1"` | in front of a building's door; two to four cells from another anchor |
  | `"auto"` | by the object's type (`engine.AUTO_BY_TYPE`: a herb on the verge, an ore at a cliff's foot, a fishing spot on the water) |

  Each anchor is ranked: a cell a body reaches by auto-path from every way in, off every lane, prop and stair, two
  cells from every other anchor, three from a way, nearest the column asked, then the most room round it, then a hash
  of the room's seed.
- **Dressing.** `props` placed as written (named ones a door opens into), or a rule `{kind, along, every, row}`;
  `flora` (each band's pool, or the biome's for its role: `wall`, `ground`, `walk`, `water`, and a density); `ground`
  (`sand`, `snow`, `snowpack` over rects or `"band.bank"`).
- **Foes.** `"auto"`, or one entry per side-view spawn: its cells, `"auto"`, or `"auto:<anchor>"` (the archers on a
  tower's top). Each point lands at the column its side-view point stands at across the room, on the verges, clear of
  ways (4), shrines (3), objects (2), each other (3), stairs and lanes.
- **The rest.** `spawn` (a cell or a way's id), `event`, `routes`, `areas` (a hazard's areas in cells: the tunnels'
  poison mist).

## What the engine does

`engine.Build.run()`, in order:

1. Lays the ground: the base, an interior's walls and doorways, the bands, the features, the stairs written out. A
   cave biome's `rubble` turns the earth floor beside a wall to rock, where its ferns and rocks grow. A water band's
   `rapids` breaks its stream with boulders (R2, below).
2. Places the props written out (or `pins["props"]`, the whole hand-placed list).
3. The ways: door paths, cuts through the bands for a north or south way.
4. Resolves the anchors. A raised shape that will get a flight counts as reached here (its cells still at its level);
   the checks hold the result.
5. `stairs="auto"`: a flight under a cut wherever it climbs a level edge, as wide as the path, and one up onto every
   raised shape something stands on (or every terrace band three rows deep), on its south face at the column nearest
   what stands on it, two rows a level, its foot on the ground below. R2: off the walks where it can, its foot level
   with its landing where it can (see below).
6. The foes' spawns.
7. The props a rule lays, then the flora. Each band's edges are cut into strips by habitat: a meadow's back (trees
   among bushes) and its lip, a cliff's foot, a road's verges (no tree on its shoulder), the water's bank, shallows
   and open water. Each strip is cut into stretches whose ends wander, one piece tried in each in the order of a hash
   of the seed and the cell (a Poisson disc kept even along the edge, never a fence-straight row). A piece fits where
   the foliage kit's rules hold (its ground, off kept-clear cells, ways' lanes and stairs, its canopy hiding no thing
   or way), stands on one level, keeps its kind's spacing, and cuts nothing off. A shape laid again under one name
   (`rubble`, `rubble_2`) takes the pool its name is given; a floor under shallow water grows reeds (R2).
8. The sand and snow, then the spawn, places, ways, spawns, event, routes and areas onto the layout.

`topdown_rooms.build()` then calls `LIFE.dress` (an interior's furnishings) and `LIFE.extend` (the vista), and runs
the checks it always ran. **Deterministic:** the seed is the room's id (`seed_of`), and every choice is a `lib.pix.h01`
hash of it and a cell, never Python's `random`.

## Pins: the hand's last word

Every generated value can be pinned in the spec. A tweak never goes into the JSON.

| Pin | Effect |
|---|---|
| `pins={"herb_1": (33, 16)}` | an anchor's cell |
| `"spawn"`, `"stairs"`, `"foes"` | the spawn, the flights, the foes' cells |
| `"props"` | the whole ordered prop list, hand-placed (the migrated rooms) |
| `"flora"` | the scatter, hand-placed |
| `"add": [(kind, x, y)]` | more pieces after the scatter |
| `"drop": [(x, y)]` | a scattered piece taken out where it covers the cell |

## The checks

- `python3 tools/data/topdown_rooms.py --check` (or `tools/content/rooms/build.py --check`): every layout current; each
  checked as it is built (every thing placed and reached, the foliage kit's rules, the furnishings); with `GODOT` set,
  the grid's parity with the game's own, cell for cell. Without `--check` it writes.
- `python3 tools/content/rooms/test_engine.py` (the runners' `room_engine` gate):
  - every spec compiles the same twice, and to its file byte for byte;
  - the scatter is seeded by the room's id;
  - every anchor kind resolves on a sample room as its rule says;
  - the pins hold;
  - in every room the engine lays out, auto-path (no running jump) reaches every thing and way from every way in.
- `places.py --check`, `room_lint.py`, `sect_walks.py --check`, `build_data.py --check`: unchanged, and green.
- `tests/topdown_chapter3.tscn`: chapter 3 played on the grid through the six new rooms (see below).
- `tests/topdown_chapter4.tscn`: chapter 4 played on the grid along the road east, and the rooms beside it (R1, below).
- `tests/topdown_drowned_shrine.tscn`: R2's ten rooms played on the grid (below).
- `tests/topdown_story_rooms.tscn`: R5's ten rooms, the story's events in them played on the grid (below).
- `tests/topdown_act2_start.tscn`: Act I crossed into Act II and chapter 11 played on the grid, then on through R6's
  nineteen rooms (below).
- `tests/topdown_sunscar.tscn`: R7's twenty rooms, chapters 13 and 14 and the Tomb King played on the grid (below).
- The capture set `room_engine` (`tools/dev/capture/shots.gd`, `E1_VIEWS`): each converted room under the HUD, the world
  alone at x2, and whole, into `docs/architecture/room_engine/` (a batch's views under its own folder: `r1/`, `r2/`; a
  view under a folder keeps its x2 copy and its whole room in that folder's `world/` and `rooms/`). The set keeps the
  body whole (`keep_whole`, which also never leaves it wounded), so a foe the room spawns does not lay it down.

## The migration (the round trip)

The 27 world layouts were re-expressed as specs (`lotus_ferry`, `willow_path`, `stoneford`, `jade_sect`,
`cloud_sect`, `reed_marsh`, and `shared.py` for the Entry Trials' yard and the Weapon Halls). All 27 compile to their
old files byte for byte, and `topdown_rooms.py` lost every hand function: 1,871 lines to 646.

- **From the engine:** the terrain (bands, features, stairs), the ways, the interiors' doorways, the door paths, the
  sand and the snow.
- **Pinned in all 27 (`pins["props"]`):** the props and foliage. They were placed by hand, piece by piece, framing
  each room, and no rule reproduces them. The anchors and the foes' cells are written as cells.
- The village at night is `variant(LF_VILLAGE, ...)`: the same terrain and props, cut at x 48 (a piece past the east
  edge is left out, as `green()` did).

## Converting a side-view room

1. `python3 tools/content/rooms/build.py --new <room>` prints a first spec:
   - a size from the side view's screens (24 + 16 a screen wide);
   - a cliff, a terrace, a road and a stream;
   - a way for every portal;
   - an anchor for every object, at the column its side-view position stands at;
   - `foes="auto"`.

   Paste it into the zone's module (a new zone goes into `specs/__init__.py`'s `ZONES`). Shape it, in 10 to 20 lines:
   - choose the biome;
   - lay out the bands and features the place needs;
   - give each anchor its spot;
   - hint the foes that live somewhere special (`"auto:tower_w"`).
2. `python3 tools/content/rooms/build.py --show <room>` draws it in text: the map, the levels, every anchor's cell and
   what the engine decided. A spec error names the anchor or way that failed.
3. `python3 tools/data/topdown_rooms.py` writes it and runs every check; `python3 tools/content/rooms/test_engine.py`
   walks it.
4. A vista goes into `topdown_life.VISTAS`. A biome the zone needs goes into `biomes.py`. The room's people are specs of
   the NPC engine (E3, `npc_engine.md`): a person's work there is `place(room, work=...)` in their spec, its spots by
   anchors (`"by:stove"`, `"water_edge"`); a person new to the room is placed by the engine itself
   (`place(room, anchor=...)`), its object and anchor added for you.
5. Add its views to `E1_VIEWS`, then run
   `xvfb-run ... capture.tscn -- room_engine --out-root=<scratch>` and **look at every picture**:
   - paths that read;
   - edges framed by flora;
   - nothing that blocks a walk;
   - nothing floating;
   - no ruled line where nature would not draw one.

   Fix what looks wrong in the spec: a band's `wavy`, a feature's `shape="round"`, a density, an anchor, a pin.
6. The layout's file opens the gate: a top-down character walks in. The tests of the prototype's frontier follow it
   by themselves since R1; none names a gated way or a converted chapter:
   - `topdown_tutorial` walks to the nearest way off the grid from the Marsh Edge (a breadth-first search over the ways
     open to it) and checks its gate there; the story's quests on the grid past chapter 3 stand done as they come, to
     the first one played past the gate; the Trial Tower's door is a gate while the tower has no layout;
   - `topdown_chapter3` and `topdown_chapter4` end on every way out of their rooms: gated exactly when its room has no
     layout;
   - `rules_tests`' prototype checks hold every way into a room without a layout to the gate, show the view's barrier
     and the walked-into plate at the first such way, and stand the story done to the first quest past the gate.

   A batch that converts rooms touches none of them. A quest that should end the prototype names its room
   (`target_room`), as The Shrine Surfaces now does.

## The first rooms: chapter 3

The six rooms past the Fairground on the main story's path, now on the grid. Chapter 3 plays there end to end:
- Bandits on the Road;
- The Caravan Road's key;
- the Mudwater Hideout to Big Toad Tan;
- Gu's Cargo.

| Room | Spec lines | Pictures (`docs/architecture/room_engine/`) |
|---|---|---|
| `cr_caravan_road` | 20 | `01_caravan_road_turnoff`, `02_caravan_road_west`, `rooms/cr_caravan_road` |
| `mh_stockade` | 23 | `05_stockade_yard`, `rooms/mh_stockade` |
| `mh_tunnels` | 19 | `06_tunnels_cavern`, `rooms/mh_tunnels` |
| `mh_loot_cave` | 18 | `07_loot_cave_hoard`, `rooms/mh_loot_cave` |
| `mh_boss_den` | 15 | `08_boss_den`, `rooms/mh_boss_den` |
| `dw_bend_shore` | 23 | `03_bend_shore_bay`, `04_bend_shore_steps`, `rooms/dw_bend_shore` |

Each picture also has an x2 copy under `world/`.

**Still to do in these rooms.** Their foes have no top-down art yet: the bandits, hounds, archers, Lieutenant Kuai,
Big Toad Tan, the carp and the crabs. The view draws its stand-ins; drawing them is E2's work. The side view's
crumbling boards in the tunnels have no top-down counterpart.

**The frontier then** (E1): Bend Shore's ways west, to the Serpent's Shallows and to the Drowned Shrine; the Marsh
Edge's way east; the sects' halls and abodes; the Trial Tower; the Quarry Road; the Beast Grove; the County Hall; Gu's
Warehouse. Toward Cleansing Peak was past the gate. R1 opened the Marsh Edge's way east (below).

## The road east: chapter 4 (R1)

The ten rooms on the main story's path past the Marsh Edge, now on the grid: the road east through the Reed Marsh, the
Bamboo Grove and Crane Falls up Cleansing Peak, and the three rooms beside it. Chapter 4 plays there end to end:
- Toward Cleansing Peak: from the mentor's peak along the road to the Pilgrim Stairs, three Stone Guardians;
- The Rite: Heaven's Cleansing passed in the summit's rite circle.

Beside the road, `topdown_chapter4` also plays Greyreed Hamlet's Grey Roofs (the grey lanterns cleansed on the hall's
and the granary's roofs, reached up a crate stack, as the Fisher's Hut's roof is) and Cleansing the Well, takes Lu's
journal page behind the falls, and visits the hermit.

| Room | Spec lines | Biome | Pictures (`docs/architecture/room_engine/r1/`) |
|---|---|---|---|
| `rm_grey_pools` | 21 | `grey_marsh` | `01_grey_pools_jetty`, `02_grey_pools_hamlet_way`, `rooms/rm_grey_pools` |
| `rm_sunken_causeway` | 20 | `reed_marsh` | `03_sunken_causeway`, `rooms/rm_sunken_causeway` |
| `rm_hermit_stilt_house` | 17 | `reed_marsh` | `04_hermit_stilt_house`, `rooms/rm_hermit_stilt_house` |
| `gh_hamlet_square` | 17 | `grey_marsh` | `05_hamlet_square`, `rooms/gh_hamlet_square` |
| `bg_whispering_bamboo` | 19 | `bamboo` | `06_whispering_bamboo`, `rooms/bg_whispering_bamboo` |
| `bg_thicket_heart` | 22 | `bamboo` | `07_thicket_heart`, `rooms/bg_thicket_heart` |
| `cf_falls_pool` | 23 | `falls` | `08_falls_pool`, `rooms/cf_falls_pool` |
| `cf_behind_falls` | 13 | `cave` | `09_behind_falls`, `rooms/cf_behind_falls` |
| `cp_pilgrim_stairs` | 16 | `mountain` | `10_pilgrim_stairs_foot`, `11_pilgrim_stairs_landing`, `rooms/cp_pilgrim_stairs` |
| `cp_cleansing_summit` | 16 | `mountain` | `12_cleansing_summit`, `rooms/cp_cleansing_summit` |

The capture's x2 copies of the world alone match the pictures under the HUD here and are not kept. The specs:
`specs/reed_marsh.py` (after the Marsh Edge), `greyreed_hamlet.py`, `bamboo_grove.py`, `crane_falls.py`,
`cleansing_peak.py`.

**Biomes and an engine rule.**
- Five biomes: `reed_marsh` (willows, reeds, cattails, lotus), `grey_marsh` (dead trees, grey reeds, stumps and logs
  where the Hollowing drank the marsh), `bamboo`, `falls` (pines and maples, mossy rocks, ferns), `mountain` (pines on
  the ledges, bare rock).
- Two knobs a biome may set: `tree_share`, the share of trees where trees grow (0.6), and `tree_gap`, how far apart its
  trees stand (5 cells). The grove's bamboo stands at 0.8 and 3. Every other room compiles byte for byte as before.

**How the side view's verticality came down.** A raised surface became a level: the canopy decks are wooden platforms
on stilts with their ladders, the lily ledge and the knolls round rocks with steps, the pilgrims' landings granite
terraces between three flights, the hermit's deck a level-2 floor over his pond. A rope bridge or a raft became a
boardwalk or stepping stones across the water; the hamlet's roofs are reached up crate stacks. The terraces' and banks'
lips wander (`wavy`), each laid over the one below it, with the stair landings fixed as features.

**Still to do in these rooms.**
- Foes with no top-down art yet (the view draws stand-ins; E2's work): the bamboo monkey, the green viper, the
  thornback boar, the Stone Guardian, and the wild pets ember fox and jade crane chick. The greyfin, the hollowed
  boarlet and the marsh leech have theirs.
- ~~The side view's movers (the Grey Pools' rafts, the hermit's raft), the falls' updraft and the vines have no
  top-down counterpart; Leaf on the Wind's glide is the side view's.~~ T1: `traverse` rows, and the lesson played on
  the grid (`docs/architecture/topdown_mechanics.md`).
- ~~A set piece's waves are called to the side view's points, read as world units on the grid.~~ T1: one rule sets
  every room event's points on the grid (`TopdownRoom.grid_event`, from `WorldRoomEvents.start_event`); the summit's
  guardians come to its `stage` cells (`docs/architecture/topdown_mechanics.md`).

**The frontier now** (R2 opened Bend Shore's three ways, below):
- ~~the Echo Cliffs' way west (Crane Cliffs);~~
- ~~the Falls Pool's misty path to the Hidden Vale;~~
- ~~the sects' halls and abodes;~~
- ~~the Trial Tower;~~
- ~~the Quarry Road;~~
- ~~the Beast Grove;~~
- ~~the County Hall;~~
- Gu's Warehouse.

The struck ways opened with the third batch (R3, below) and the peaks (R4, below).

The story's next quest past chapter 4, The Shrine Surfaces (the Drowned Shrine), is past the gate.

## The third batch (R3): Stoneford's insides, the quarry, the sects' halls

Fourteen rooms around the Fairground and the two sects, laid out from the side view. Every way into them is open now:
- the sects' halls and abodes;
- the Trial Tower;
- the Quarry Road;
- the Beast Grove;
- the County Hall.

With R2 the story plays on past chapter 4: chapter 5 in the Drowned Shrine, and chapter 6's Quiet Before the Storm on the
Rapids Terraces. Its next quest past the gate is chapter 7's Wings of Cloud, at the Cliff Faces past the Echo Cliffs'
way west.

## The Drowned Shrine and Whitewater Gorge (R2)

The ten rooms south and west of Bend Shore, now on the grid. Bend Shore's three gated ways lead onto them: the ford
south to the Serpent's Shallows, the steps down into the Drowned Shrine, and the road west into Whitewater Gorge.
`tests/topdown_drowned_shrine` plays them (below).

| Room | Spec lines | Pictures (`docs/architecture/room_engine/r2/`) |
|---|---|---|
| `dw_serpents_shallows` | 18 | `06_serpents_shallows`, `rooms/dw_serpents_shallows` |
| `ds_flooded_gate` | 20 | `01_flooded_gate_court`, `rooms/ds_flooded_gate` |
| `ds_hall_of_lanterns` | 21 | `02_hall_of_lanterns`, `rooms/ds_hall_of_lanterns` |
| `ds_scripture_well` | 22 | `03_scripture_well`, `rooms/ds_scripture_well` |
| `ds_abbots_sanctum` | 20 | `04_abbots_sanctum`, `rooms/ds_abbots_sanctum` |
| `ds_drowned_grotto` | 16 | `05_drowned_grotto`, `rooms/ds_drowned_grotto` |
| `wg_gorge_mouth` | 19 | `07_gorge_mouth_bridge`, `rooms/wg_gorge_mouth` |
| `wg_rapids_terraces` | 19 | `08_rapids_terraces_falls`, `rooms/wg_rapids_terraces` |
| `wg_echo_cliffs` | 20 | `09_echo_cliffs`, `rooms/wg_echo_cliffs` |
| `wg_waterfall_cave` | 16 | `10_waterfall_cave`, `rooms/wg_waterfall_cave` |

`world/` keeps the x2 copies of the four views that show the new looks: `01`, `02`, `06` and `08`.

**The looks** (`biomes.py`, R2's block). Later zones reuse them:
- `drowned_shrine`: dressed granite walls (`walls=dict(paint="s")`) round flagstone halls. The spec module's helpers
  lay the rest:
  - granite pillars a cell each, some broken low;
  - rubble heaps of rock, thick with ferns and mossy stones;
  - silt drifted over the flagstones along the water's edge (sand creeps over paving);
  - stone and paper lanterns along the dry walks.

  No trees grow under the river. The rooms are lamp-lit (the side view's `cave` backdrop).
- `gorge`: grey rock walls with a wavering foot, pines on the ledges, mossy boulders and ferns, the river white over
  its stones.
- `grotto`: a cave's rock round wet sand and shallows.

**Floors under shallow water** (paint `q` flagstones, `h` a river's pebbled bed). A body walks them and wades: they are
floors to the grid, and their steps are the water's (`sound.py`). Their look:
- each draws its own floor, then the water's overlay (`tools/art/topdown/flood.py`, the manifest's `v2.flood`): clear
  blue-green water, the floor showing through, a lit ripple now and then;
- a corner floods where every cell round it is a flooded floor or open water, so the water's edge wanders through the
  flooded cells along dry floor, lit on its sunny side, a damp line beyond it (`TopdownTerrain`);
- cattails grow in them; nothing else does.

**The waterfall** (`tools/art/topdown/falls.py`, the prop `waterfall`): a fall three cells wide over a cliff four levels
high, on the water's clock. It stands on the water at the cliff's foot (Whitewater Gorge's stream, the Rapids Terraces'
pool, the Waterfall Cave's cleft).

**Engine rules** (`engine.py`):
- `rapids` on a water band: rocks of a cell or two in its open water, three apart, a boulder on each. The water's shore
  foam round them makes the river white. No one reaches them.
- A flight stands off the walks where it can, and with its foot level with its landing where it can. Auto-path's
  steering cannot cross a flight from its side: it stalls on the cheek (`rules_tests`' route tour found it). Where no
  spot is free, as for the Stockade's towers over their yard, the old choice stands. Every older room is unchanged.
- A raised shape counts as reached for its anchors only where it is still at its level. A cliff laid over a terrace's
  edge is no part of the terrace.
- A shape laid again under one name (`rubble`, `rubble_2`) takes its name's flora.
- A floor under shallow water is a band of reeds (the `shallow` habitat).
- Bands are laid in order, so a terrace laid a row into the cliff above it, with the cliff laid after it `wavy`, gives a
  wandering foot with no pit between them (`whitewater_gorge.py`'s `CLIFF_FOOT`).

**Set pieces on the grid.** A rite circle's set piece (the Riverbreath Trial at the Scripture Well) brings side-view
spawn points. `TopdownRoom.grid_event` gives them the layout's own cells for the room's event (the spec's `event`), or
else the nearest spot a body stands on. (T1: `WorldRoomEvents.start_event` asks it for every room event on the grid,
one rule for all of them (`docs/architecture/topdown_mechanics.md`).)

**The suite** (`tests/topdown_drowned_shrine`, 44 checks):
- each room is entered through its ways, built by the view, and walked by auto-path from every way in;
- the Riverbed Serpent is defeated in its shallows;
- chapter 5's shrine plays through: The Shrine Surfaces, Lu's Handwriting, The Riverbreath Trial (its drowned rise on
  the grid's floor), the flooded shaft to the Grotto, The Drowned Abbot (his four bells rung) and the Sanctum's stair
  back up;
- the gorge is walked: the Waterfall Cave behind the falls and back, and the Echo Cliffs' way west stays gated.

**Still to do.**
- Their foes have no top-down art yet: the Riverbed Serpent, the Drowned Acolyte, the Paper Talisman Ghost, the Drowned
  Abbot, the Rogue Cultivator, the Gorge Bandit Adept, the Rapids Lizard, the Boulder Serpent and the Mist Vulture. The
  view draws its stand-ins; drawing them is E2's work.
- The side view's moving parts have no top-down counterpart:
  - the Flooded Gate's drifting planks;
  - the swinging lanterns;
  - the currents' push;
  - the rising water of the Serpent's and the Abbot's floods;
  - the Drowned Grotto's swim (it is wading water here).

  T1: the planks, the currents and the floods are `raft`, `current` and `flood` rows now, waiting in these rooms'
  specs; the lanterns and the swim are still to do (`docs/architecture/topdown_mechanics.md`).
| Room | Spec lines | Pictures (`docs/architecture/room_engine/r3/`) |
|---|---|---|
| `ja_alchemy_hall` | 13 | `09_alchemy_hall`, `rooms/ja_alchemy_hall` |
| `ja_library` | 15 | `10_library`, `rooms/ja_library` |
| `ja_retreat` | 12 | `11_retreat`, `rooms/ja_retreat` |
| `ja_cave_abode` | 17 | `12_cave_abode`, `rooms/ja_cave_abode` |
| `cm_cloud_library` | 16 | `13_cloud_library`, `rooms/cm_cloud_library` |
| `cm_retreat` | 12 | `14_cloud_retreat`, `rooms/cm_retreat` |
| `cm_herb_terraces` | 20 | `15_cloud_herb_terraces`, `16_cloud_terraces_upper`, `rooms/cm_herb_terraces` |
| `cm_cave_abode` | 17 | `17_cloud_cave_abode`, `rooms/cm_cave_abode` |
| `sf_county_hall` | 11 | `18_county_hall`, `rooms/sf_county_hall` |
| `sf_trial_tower` | 13 | `19_trial_tower`, `rooms/sf_trial_tower` |
| `sf_beast_grove` | 14 | `20_beast_grove`, `rooms/sf_beast_grove` |
| `sq_quarry_rim` | 21 | `21_quarry_rim`, `22_quarry_scaffold`, `rooms/sq_quarry_rim` |
| `sq_lower_pit` | 22 | `23_lower_pit`, `24_pit_tunnel_mouth`, `rooms/sq_lower_pit` |
| `sq_collapsed_tunnel` | 19 | `25_collapsed_tunnel`, `rooms/sq_collapsed_tunnel` |

The quarry is a new zone module, `specs/stonewall_quarry.py`; the others went into their zones' modules.

**The looks.**
- *A sect's hall* is an interior with taller walls (`walls=dict(high=4)`, a library's 6), so what stands on a loft or a
  gallery stays inside them, and a raised floor of boards or flagstones for what the hall is for:
  - the Alchemy Hall's furnace dais and its recipe loft;
  - the libraries' two galleries, a level apart, up flights of boards;
  - the retreats' meditation dais;
  - the County Hall's dais and the Trial Tower's guardians' dais over its sand arena.
- *New furnishings* (`tools/art/topdown/furnish.py`):
  - `scroll_shelf`: a library's pigeonholes of scrolls and bound books;
  - `apothecary`: an alchemist's chest of little drawers, jars on top;
  - `screen`: a folding screen painted with a landscape;
  - `desk`: a scholar's writing desk.

  With the kit's lanterns, banners, mats, incense, stoves and potted plants, and the back walls' hangings
  (`topdown_life.HANGINGS`: plaques, windows, scrolls, herbs), they furnish the halls.
- *Stair cheeks.* Each hall's flight stands between two cheeks a level over its head: the scaffold's ladder at the
  Quarry Rim too, whose flights are pinned.
  - Why: auto-path's grid (`TopdownRoute.step_rise`) lets a body step off a flight's side where the floor beside it is
    a step (8) from the flight's floor at the cell's middle.
  - The motor tests its foot box's corners, a little higher or lower up the slope, and stops there.
  - A two-row flight's last row is exactly a step off the floor at its foot and its head. Without cheeks, a body
    walking off a flight sideways stalled: `rules_tests`' steering tour lost the recipe shelf and the upper gallery.
  - The engine's own flights (`stairs="auto"`) still have open sides. A fix in the route's rule would fit every room;
    it belongs to the route and its Python twin (`topdown_rooms.Grid`), not to a batch of rooms.
- *A cave's low front.* A cave room's rock stands four levels high. Drawn in the 3/4 view, the rock south of the floor
  hides the four rows behind it. The abodes and the collapsed tunnel lay a `front` feature of level-1 rock under their
  caverns first, so the cave reads as an interior with a low sill and nothing on its floor is hidden.
- *Biomes* (`biomes.py`):
  - `sect_terraces`: the Cloud Herb Terraces' plum, pine and hedges over the cloud sea;
  - `quarry`: cut rock, stumps and pines;
  - `bamboo_clearing`: the Grove's bamboo round a mossy clearing.

  Vistas for the terraces, the grove and the quarry are in `topdown_life.VISTAS`.

**The places.** Three new rows in `tools/data/places.py`:
- `ja_furnace`: the Alchemy Hall's furnace, alchemy, earned, for the Jade Sect;
- `ja_abode_garden` and `cm_abode_garden`: each Cave Abode's two beds, the herb garden, earned.

Each stands where auto-path reaches it from every way in.

**The trials on the grid.** The Trial Tower's floors and the Grove's waves were written in the side view's coordinates
(`world_tower.gd`, `data/beast_arena.json`).
- ~~`WorldRoomEvents.side_points` maps them through `TopdownRoom.from_side`~~ (T1: `TopdownRoom.grid_event`, one
  rule for every room event): across the room as across the side view, a cell and a half in from the edges, onto the
  nearest open floor.
- The side view gets them unchanged.

**Tested in** `tests/topdown_sect_halls.tscn`:
- every room walked into through its ways, and out and back through each;
- auto-path reaching every thing;
- every page a thing opens;
- the three places;
- a tower floor and a guardian floor fought on the grid;
- the Grove's trial begun with a spirit beast;
- Stone and Sweat's copper and beetles at the Quarry Rim.

**Still to do.** Several foes of these rooms have no top-down sheets yet, and the view draws stand-ins:
- the quarry's: `stone_tortoise`, `ironclaw_mole`, `riverstone_ox`;
- the Grove's waves: `mud_hound`, `tide_crab`;
- most of the tower's 28 species.

Some side-view props have no top-down counterpart:
- the guardian lions;
- the quarry's crane lift (a side-only mover; T1: a `lift` row with mode `trigger`, waiting in the spec).

~~Some waves still spawn at the side view's points, read as world units on the grid: the spatial rift's waves and the
set pieces' waves.~~ T1: every room event's points are set on the grid by one rule (`TopdownRoom.grid_event`); a
rift's foes come either side of the player on the grid's floors (`docs/architecture/topdown_mechanics.md`).

## The peaks (R4)

The eleven rooms of the peaks, now on the grid: the Crane Cliffs, Mist Peak, Summit Ridge, the Hidden Vale and the
Hidden Grotto. Their high-mountain, mist and snow looks are the ones Act II's Rimefrost Heights will reuse.
`topdown_peaks` plays them by test shortcuts, a top-down character at Heaven Glimpse 3 set down on the Cliff Faces:
- the climb room by room through their ways, with no gate on the way: the Cliff Faces, the Sky Ledges, the Misty
  Slopes, the Forgotten Monastery, the Windswept Ridge, the Frozen Shrine and the Ascension Gate;
- Above the Mist's Stormwing Hawks on the Sky Ledges;
- A Wider Sky, meditated by the heaven insight stone;
- the monastery's hidden cellar, shown by Spirit Sense and taken to the hidden stair;
- Beyond the Valley to the Frozen Shrine, and Lu's journal page there;
- The Ascension Gate: the Gate Guardian on the summit's arena, and Act I's end;
- the Hidden Vale's teleport stone, a founded sect's raid on the Sect Grounds, the Back Mountain opened by the sect's
  level, and the Grotto's rope up to Behind the Falls.

In each room it checks the walks and the view as `topdown_chapter3` does. The route tour in `rules_tests`
(`topdown_suite._route_rooms`) walks the eleven rooms too, every leg arriving.

| Room | Spec lines | Biome | Pictures (`docs/architecture/room_engine/r4/`) |
|---|---|---|---|
| `cc_cliff_faces` | 18 | `mountain` | `01_cliff_faces_crags`, `02_cliff_faces_brink`, `rooms/cc_cliff_faces` |
| `cc_sky_ledges` | 18 | `mountain` | `03_sky_ledges_climb`, `04_sky_ledges_summit`, `rooms/cc_sky_ledges` |
| `mp_misty_slopes` | 23 | `mist_peak` | `05_misty_slopes_mere`, `06_misty_slopes_knoll`, `rooms/mp_misty_slopes` |
| `mp_forgotten_monastery` | 29 | `mist_peak` | `07_monastery_hall`, `08_monastery_garden`, `rooms/mp_forgotten_monastery` |
| `mp_ascension_gate` | 15 | `snowfield` | `09_ascension_gate`, `rooms/mp_ascension_gate` |
| `sr_windswept_ridge` | 19 | `snowfield` | `10_windswept_ridge`, `rooms/sr_windswept_ridge` |
| `sr_frozen_shrine` | 18 | `snowfield` | `11_frozen_shrine_court`, `rooms/sr_frozen_shrine` |
| `hv_vale_gate` | 15 | `hidden_vale` | `12_vale_gate`, `rooms/hv_vale_gate` |
| `hv_sect_grounds` | 25 | `hidden_vale` | `13_sect_grounds`, `rooms/hv_sect_grounds` |
| `hv_back_mountain` | 17 | `hidden_vale` | `14_back_mountain_spring`, `rooms/hv_back_mountain` |
| `hg_hidden_grotto` | 12 | `cave` | `15_hidden_grotto`, `rooms/hg_hidden_grotto` |

The line counts take in the anchors; the longest rooms are the ones with the most things (the monastery has 19). As
R1's, the capture's x2 copies of the world alone are not kept. The specs: `specs/crane_cliffs.py`, `mist_peak.py`,
`summit_ridge.py`, `hidden_vale.py`, `unmapped.py`.

**The looks.**
- Three biomes. `mist_peak` has pines and grey dead trees, ferns and mossy stones, and the mist lies over the slopes'
  wet hollows (paint `m`, TopdownAtmosphere's mist). `snowfield` is the snow line. `hidden_vale` is a sheltered sect
  valley of blossom, maples, camphor, pines and bamboo, with willows and lotus on its water.
- The Crane Cliffs take R1's `mountain`.
- **The snow line.** A biome may set the `ground` a spec that names none takes. `snowfield`'s is fresh snow over every
  cell (`"*"`) and packed snow on the walks and their cuts (`"walk"`), never on a flight of stairs. Paving is never
  snowed, so a court or an arena reads swept.
- **Mountains.** The Cliff Faces' trail runs under a level-6 cliff, crane ledges and crags rising north up it. The
  rooms that end in clouds fall in a wavy step to a brink over the `cloud_sea` vista.
- A raised thing is placed at least its level in rows from the north edge. The view draws a top `level` rows up, and a
  chest on a level-5 crag in row 3 would stand above the room's picture.
- Water lies beside ground at level 0 (the Back Mountain's spring pool), so a pool's bank is one level and never a pit.

**Engine rules.** None of them changes a room built before. Every older spec, R2's and R3's too, compiles to its file
byte for byte, and `test_engine` holds it.
- `wavy="s"` (or `"n"`) wanders one edge only, such as a terrace's lip under a cliff laid before it.
- `flights=[col, ...]` on a band or a feature: stairs "auto" climbs it at each column, a feature too with nothing on
  it. Such a flight:
  - ends at the walk below rather than on it, near the column first, then anywhere on the terrace; one that comes down
    onto the walk comes next, and one that runs across it last;
  - has clear cheeks: the ground beside it is no higher than its foot, so it never climbs in a notch of the shape;
  - has its cheeks closed by boulders (a biome's `cheek`) wherever the ground beside it is open at its foot's level, off
    the walks, the lanes and the anchors. Auto-path's plan reads a step's middle and the motor the body's corners, so
    a body sent along a flight's step from the side is left wedged against it (`rules_tests`' route tour found it).
    Closed cheeks keep every way off the steps' sides. The monastery's and the Ascension Gate's grand stairs are such
    flights too.
  - has its foot flush with the ground it leads to where a column within ten has one, as R2's flights do: a foot a
    step lower leaves a dark lip under its last row.
- A feature with no `level` of its own is paint and gets no flight. A walk is never climbed onto either.
- `shape="ruin"`: a ruined building's walls round its rect, broken by a hash of the seed. About one piece in five is
  gone and one in five is fallen a level. The corners always stand, so two walls never touch only diagonally, which
  the game's route crosses and the Grid's does not. A doorway of four cells is left on its `door` side. Its region is
  the floor inside, which anchors stand on and plants grow on.
- The ground cases above: `"*"` and `"walk"` as `ground` names, and a biome's `ground`.

**Shared rules for the view and the systems.**
- **Raised stone reads as raised** (`TopdownTerrain._lit_blocks`). A small raised block is one of at most 12 cells of
  one level, standing two levels or more over the ground round it: a pillar, a plinth, a stretch of ruined wall. Its
  top takes a lit tint (`LIT`) and its face a lighter sky tint (`FACE_LIT`). Over its cast shadow it reads as a lit
  stone, not a dark square sunk into the paving. This also fixes R1's Cleansing Summit pillars; their two pictures
  are retaken under `r1/`.
- **The sect's raid on the grid** (`SectAuthority.start_defence`). The defence's points are the side view's, and one
  stands past the room's east edge. On the grid each comes in on the open floor inside the room. (T1: by the one rule
  for every room event, `TopdownRoom.grid_event`: mapped across the room, they land at cells (7, 22), (32, 22) and
  (54, 23) (`docs/architecture/topdown_mechanics.md`).)
- **Places.** The Vale Gate's teleport stone, the Sect Grounds' storehouse and shrine, and the Frozen Shrine are rows
  of `places.py`. There are 30 places now.
- **One frontier check.** `rules_tests`' prototype check teleported to the Hidden Vale's stone to show a stone past the
  gate. The stone is on the grid now, so the check takes the first stone in a room with no layout.

**How the side view's verticality came down.**
- The cloud and rock ledges, at 100 to 900 units, are terraces stepping north, a flight up each.
- The monastery's roofs and boards are its paved upper terrace, ruined walls, a raised floor and a gallery of boards.
- The ring of cloud platforms round the Gate Guardian is four low plinths on the arena.
- The tree-branch routes are tors on the ridge's crest.
- The hidden stair and cellar are ways into the retaining wall's face.
- The Grotto's rope is a way up the cleft in its west wall.

**Still to do in these rooms.**
- Foes with no top-down art yet (the view draws stand-ins; E2's work): the cliff ape, Cloudpeak Roc, Cloudwing Crane,
  the Gate Guardian, Hollow Stag, Jade Sentinel, Mirror Wisp, Mist Wolf, the rogue treasure adept, Stormwing Hawk and
  Weeping Lantern.
- Some of the side view has no top-down counterpart: the crumbling boards and icicles, the updrafts, the ridge's wind
  and Wings of Cloud's flight.
- The sect's buildings are drawn as the side view's facades at half size once raised, as every thing is. Their slots
  line the Sect Grounds' two paved walks, and the big ones overlap when they stand side by side.

**The frontier now** (R4, with R2's and R3's rooms on the grid):
- Gu's Warehouse (Stoneford's Artisan Row);
- the Ascension Gate's way up to the Azure Expanse (Act II's Cloudgate Port).

Every other way out of a room on the grid leads to a room on the grid. The climb is whole on foot: Bend Shore, up
Whitewater Gorge to the Echo Cliffs, west onto the Cliff Faces and up to the Ascension Gate. The Hidden Vale is reached
from the Falls Pool and by its teleport stone. `topdown_peaks` still sets its body down on the Cliff Faces, so it plays
the peaks alone. Chapter 7's rooms are on the grid now, and Act I ends there at the Ascension Gate. Its first quest,
Wings of Cloud, still asks for the side view's flight (above).

R6 opened the Ascension Gate's way up (below).

## The story's rooms and the Tidebreak Front (R5)

The ten rooms the story keeps for its own events, and the Tidebreak Front's, now on the grid: five instanced story
rooms (`specs/story.py`) and the Front's five (`specs/tidebreak_front.py`, the Tide battle among them). Each is laid out
for its event: an arena with clear fighting ground, a wall with its gate for the siege, the Gate's line for the war, the
trials' own shapes. `tests/topdown_story_rooms` plays every event in them (below). Gu's Warehouse was the last way off
the grid in Act I; its door on Artisan Row is open now.

| Room | Spec lines | Biome | Pictures (`docs/architecture/room_engine/r5/`) |
|---|---|---|---|
| `si_gus_warehouse` | 22 | (an interior) | `01_gus_warehouse`, `02_warehouse_strongroom`, `rooms/si_gus_warehouse` |
| `si_trial_of_reflections` | 16 | `mountain` | `03_trial_of_reflections`, `rooms/si_trial_of_reflections` |
| `si_presence_trial` | 16 | `mountain` | `04_presence_trial`, `rooms/si_presence_trial` |
| `si_siege` | 30 | `valley_road` | `05_siege_gate`, `06_siege_field`, `rooms/si_siege` |
| `si_sect_war` | 29 | `mountain` | `07_sect_war_gate`, `08_sect_war_junk`, `rooms/si_sect_war` |
| `tf_tidebreak_bastion` | 28 | `bastion` | `09_tidebreak_bastion`, `rooms/tf_tidebreak_bastion` |
| `si_tide_battle` | 17 | `bastion` | `10_tide_battle`, `rooms/si_tide_battle` |
| `tf_greyfall_breach` | 27 | `tidebreak` | `11_greyfall_breach`, `rooms/tf_greyfall_breach` |
| `tf_hollow_wake` | 21 | `tidebreak` | `12_hollow_wake`, `rooms/tf_hollow_wake` |
| `tf_drone_hive` | 17 | `tidebreak` | `13_drone_hive`, `rooms/tf_drone_hive` |

The line counts take in the props written out; the siege's camp and the Bastion's yard are the longest. As R1's and
R4's, the capture's x2 copies of the world alone are not kept.

**The rooms.**
- *Gu's Warehouse*: a flagstone store under lamplight, the goods in stacks a body can climb (crates) between aisles
  where the bandits keep watch. A loft of boards runs along the north wall from the west stair to the east one, the
  catwalk between them the side view's stealth route under the roof. Gu's strongbox stands on the strongroom's dais
  at the east loft's end, a level higher again. Gu holds his office in the east, on a floor of boards.
- *The Trial of Reflections*: an octagon of granite on Elder Hu's peak, every line of it mirrored about the bronze
  mirror on its dais: two granite ledges a step up, the same flight up each, the lanterns and censers in pairs. The
  Reflection waits where the player's mirror image would stand, across from the way in.
- *The Presence Trial*: the Nine Peaks' court above the Trial Hall. Nine seats look down on a circle of paving in a
  horseshoe open to the south, each on a plinth too high to climb. The ninth, empty, is the highest, between its two
  pressure pillars. The phantoms come from the court's west, east and south, and the ninth Presence rises before the
  ninth seat.
- *The Siege of Two Sects*: the wall across the valley with its gate on the road, a tower each side of the gate and
  one at each end, flights up to the wall-walk from the camp. The sects' camp is south of it, the valley the Hollow
  turned grey north of it. The boarlets come out of the grey, and the Behemoth stands on the road before the gate.
- *The Sect War at the Alliance Gate*: the comet sails' junk run aground along the pass's north edge, its deck a long
  hull two levels over the rock, gangways down from it. The forecourt lies between it and the Alliance's line, a
  granite parapet a step high with its gap on the road. The Gate's two great pillars stand behind it, the way out
  south. The pirates and the turncoats come down the gangways, and Comet Captain Rao drops from the rail between them.
- *The Tidebreak Bastion*: the Wardens' yard of flagstones under the great wall and its towers, the granite road from
  the skiff dock over the cloud sea to the east gate between two more towers. The lantern's cage stands on its dais,
  star lanterns line the road, and the great bell hangs on its own dais.
- *The Tide Breaks*: the wall's outer terrace. The great lantern burns on a dais against the wall in the middle. A
  barricade of crates and barrels crosses the terrace each side of it, a gap where the road runs: the lines the
  Wardens hold. The Tide comes from both ends, up over the rim.
- *The Greyfall Breach*: the Bastion's outer wall across the grey, broken in the middle. The Wardens' road comes in
  along the wall's south side, turns north through the breach and runs east through the grey. The wall steps down at
  the breach's ragged edges. Shen Lian holds the gap, the warning bell beside it on the Wardens' side, and the stand's
  waves come out of the grey north of the wall.
- *The Hollow Wake*: the scar the Tide left, a trough of drained rock between two low rises, the track along its
  floor, grey pools standing in it, three outcrops climbing from the rises. Lu's journal page lies on its rack by the
  first pool.
- *The Drone Hive*: the Hollow's hive mound in two tiers thick with hives, the chests on its crown. The track skirts it
  to the south and runs east to where the dark thins into the nebula.

**The looks.**
- Two biomes (`biomes.py`, R5's block):
  - `tidebreak`: the grey fields, bare rock the Tide has drunk, dead trees and grey reeds, stumps and logs;
  - `bastion`: a Wardens' fortress of granite and flagstones, little growing but weeds and fallen stones.
- Three props (`tools/art/topdown/furnish.py`, R5's block; the prop sheet rebuilt by `build_tiles.py`):
  - `trial_seat`: a granite throne of the Nine Peaks, a jade stone in its crown and a lilac cushion;
  - `bronze_mirror`: the side view's mirror in its curved frame on a pedestal, a jade mist in its face;
  - `drone_hive`: a cone of grey papery stone in scalloped courses, its cells glowing violet.
- Vistas (`topdown_life.VISTAS`): peaks behind the trials, the Gate, the siege and the grey fields, and the cloud sea
  under the brinks of the peaks and the Tidebreak Front.
- **A wall that must read as one runs east and west.** In the 3/4 view only a south face shows. A wall running north
  and south is its top alone, a strip of stone on the ground (the first drafts of the siege and the Breach). So the
  siege's wall, the Alliance's line and the Breach's outer wall cross their rooms east to west, and their events come
  from the north. The Tide battle's lines must cross a terrace the Tide reaches from both ends, so they are built of
  crates and barrels, which stand up from the ground.
- The specs' helpers (`specs/story.py`): `octagon()`, a floor of rects laid one over another so a trial's arena stays
  exactly symmetric (a round shape wears with the room's seed), and `stair_with_cheeks()`, R3's flight between cheeks.
- R4's rule holds: a raised thing stands at least its level in rows from the north edge. Gu's strongbox is on the
  strongroom's dais at row 3, level 3.
- The Breach's two outcrops are climbed by R4's `flights`, their cheeks closed by boulders. With R2's open-sided
  flight, `rules_tests`' route tour stalled coming down from the north one's crate.

**An engine rule.** A layout's `event` gives the cells of the room's own event (`TopdownRoom.merge_def`), or of a set
piece begun in it (`TopdownRoom.grid_event`). The checks compared them with the room's own event only. The Greyfall
Breach has none: its stand is the set piece its bell begins. Now, for a room with no event of its own, `check` holds
the layout's cells to that set piece's room event (`topdown_rooms.set_piece_event`). Every older room is unchanged.

**The events on the grid.** Every event in these rooms spawns on the layout's own cells:
- the Reflection, the Behemoth and the siege's boarlets;
- the war's pirates, turncoats and captain;
- the phantoms and the ninth Presence;
- the Tide's drones and wyrmlings;
- the Greyfall stand's waves.

The tide battle's lantern drains within 180 units of the great lantern and relights within 120 of it. On the grid
these are its place's plane distance, about six and four cells.

**Tested in** `tests/topdown_story_rooms.tscn` (69 checks), by test shortcuts along the story:
- every room is entered on the grid, built by the view and walked by auto-path from every way in;
- The Heart Trial: the heart demons come with the Reflection on the arena's open ground, and the Reflection is
  defeated;
- Gu's Warehouse: the strongbox opened on the strongroom, Gu held off until he flees with his ledger dropped;
- The Siege: the Behemoth and the boarlets come out of the grey north of the wall, at the room's cells;
- The Gate Holds: the pirates, the turncoats and Rao come at their cells, and Rao falls;
- The Presence Trial: the phantoms come, and the ninth Presence rises before its seat;
- The Tide Breaks: the bell rung, the drones come at both ends, the lantern relit by a Warden beside it and drained by
  a foe near it, then held;
- the grey fields walked east to the Drone Hive and back:
  - Lu's journal page taken in the Wake;
  - the chest on the hive's crown;
  - Greyfall's stand rung and held beside Shen Lian, its waves out of the grey at the room's cells.

The ways to rooms with no layout are gated: the Alliance Gate, the Citadel's skiff and the Nebula Deep.

**Still to do in these rooms.**
- Foes with no top-down sheets yet (the view draws stand-ins; E2's work): Elder Gu, the Hollow Behemoth, the starsea
  pirate, the Nine Peaks disciple, the pirate captain, the presence phantom, the ninth Presence, the hollow drone and
  the hollowed wyrmling. The Reflection and the heart demons draw the player's own figure, as the side view does. The
  Mudwater bandit, the gorge bandit adept (Gu's hired blades) and the hollowed boarlet have their sheets (M1).
- The Reflection's heart demons come at the side view's points, mapped across the arena onto open ground by T1's
  `TopdownRoom.grid_points`. Every other event here keeps its own cells, the layout's `event` (T1's third rule); none
  needs a `stage`.
- Mechanics with no top-down counterpart yet:
  - The side view's stealth route over the rafters is the catwalk loft here. Whether Concealment hides a body up there
    from the floor's bandits is the side view's rule, not the grid's.
  - The Tidebreak Front's backdrop is the side view's night sky, but the grid's light follows the clock there (no
    area in `TopdownLight.AREAS` for `tidebreak_front` or `nine_peaks`). The siege's `valley_dusk` and the warehouse's
    interior keep their hours.
- Some side-view decor has no top-down counterpart: the star ballista, the sky ship's sails, the pirate and the
  alliance banners (the sects' jade and cloud banners stand in), the paifang's roof.

**The frontier now** (R5): Gu's Warehouse is on the grid. In Act I the gate stands only at the Ascension Gate's way
up to the Azure Expanse (Act II). From the Marsh Edge no way off the grid is in walking reach any more. So
`topdown_tutorial`'s gate check now sets the walk down at the first such way in a room on the grid that is not an
instance, by the layouts' names (the Ascension Gate's), and checks its gate there. While one is in reach it still
walks to the nearest. Past it, the Sect War's and the Presence Trial's ways back lead to the Nine Peaks'
rooms, the Bastion's skiff to the Citadel, and the Drone Hive's way east to the Nebula Deep. Those rooms have no
layout, so the four ways are gated. The Tidebreak Front's own rooms join each other on the grid.

## Act II's first zones (R6): Cloudgate Port, the Thunderhorn Plains, Rimefrost Heights, Mirrorwater Lake

The nineteen rooms of Act II's first two chapters, now on the grid: Cloudgate Port (6), the Thunderhorn Plains (4),
Rimefrost Heights (4) and Mirrorwater Lake (5). The Ascension Gate's way up opens onto the Arrival Terrace, so Act I and
Act II join on foot.

`tests/topdown_act2_start` plays them, a top-down character carried by test shortcuts to the Ascension Gate with Act I
done (Heaven Glimpse 3, a sturdy body):
- **the crossing:** up through the gate onto the Arrival Terrace's dais, back down to the summit, and up again, on the
  grid both ways;
- **chapter 11, played through:**
  - Through the Gate: the toll warden at the gate's foot;
  - A Sky Full of Toll Roads: the Factor in the market, the broker in the inn;
  - Storm in the Blood: the town gate east is sealed till the quest is under way, then four jades attuned, six Spark
    Weasels on the Verge (the plains' lightning strikes on the grid) and the shards;
  - Horns for the Furnace: three thunderhorns hunted on the Flats, past the Herders' Camp, the horns taken to the
    alchemist in the Condensing Hall off the Skydock;
  - Sage;
- **on through chapter 12's rooms:**
  - the Lightning Scar's way east opens to a Sage, up the three rooms of Rimefrost to the summit and into the hermit's
    ice cave (its hidden way found);
  - the Skydock's lake ferry to the Reedless Shore, along the lake through the Mirror Shallows (Toad's Hollow off
    them) and the Sentinel Causeway to the Lake Shrine, its bronze mirror looked into;
- **the frontier:** the Nine Peaks ferry is the prototype's gate exactly while Nine Peaks has no layout. With R7's
  rooms it is open, and the test rides it to the Alliance Gate and back.

In every room it checks the walks and the view as `topdown_chapter3` does: 63 checks. `rules_tests`' route tour walks
the nineteen rooms too.

| Room | Spec lines | Biome | Pictures (`docs/architecture/room_engine/r6/`) |
|---|---|---|---|
| `ae_landing` | 21 | `sky_port` | `01_arrival_terrace_gate`, `02_arrival_terrace_rim`, `rooms/ae_landing` |
| `ae_port_market` | 29 | `sky_port` | `03_port_market_street`, `04_port_market_gate`, `rooms/ae_port_market` |
| `ae_wayfarers_inn` | 9 | (an interior) | `05_wayfarers_inn` |
| `ae_skydock` | 22 | `sky_port` | `06_skydock_berths`, `rooms/ae_skydock` |
| `ae_condensing_hall` | 13 | (an interior) | `07_condensing_hall` |
| `ae_shipyard` | 18 | `sky_port` | `08_shipyard_slip`, `rooms/ae_shipyard` |
| `tp_stormgrass_verge` | 20 | `storm_plains` | `09_stormgrass_verge`, `rooms/tp_stormgrass_verge` |
| `tp_herders_camp` | 19 | `storm_plains` | `10_herders_camp`, `rooms/tp_herders_camp` |
| `tp_thunderhorn_flats` | 21 | `storm_plains` | `11_thunderhorn_flats_pool`, `rooms/tp_thunderhorn_flats` |
| `tp_lightning_scar` | 24 | `storm_plains` | `12_lightning_scar`, `rooms/tp_lightning_scar` |
| `rf_frostpine_climb` | 23 | `snowfield` | `14_frostpine_climb`, `15_frostpine_climb_high`, `rooms/rf_frostpine_climb` |
| `rf_snow_ape_ledges` | 17 | `snowfield` | `16_snow_ape_ledges`, `rooms/rf_snow_ape_ledges` |
| `rf_rimefrost_summit` | 19 | `snowfield` | `17_rimefrost_summit`, `18_rimefrost_summit_rim`, `rooms/rf_rimefrost_summit` |
| `rf_hermits_ice_cave` | 12 | `snowfield` | `19_hermits_ice_cave` |
| `ml_reedless_shore` | 23 | `mirror_lake` | `20_reedless_shore_ferry`, `21_reedless_shore_mirror`, `rooms/ml_reedless_shore` |
| `ml_mirror_shallows` | 24 | `mirror_lake` | `22_mirror_shallows`, `rooms/ml_mirror_shallows` |
| `ml_sentinel_causeway` | 28 | `mirror_lake` | `23_sentinel_causeway`, `rooms/ml_sentinel_causeway` |
| `ml_lake_shrine` | 17 | `mirror_lake` | `24_lake_shrine`, `rooms/ml_lake_shrine` |
| `ml_toads_hollow` | 18 | `mirror_lake` | `25_toads_hollow`, `rooms/ml_toads_hollow` |

The specs: `specs/cloudgate_port.py`, `thunderhorn_plains.py`, `rimefrost_heights.py`, `mirrorwater_lake.py`. As R4's,
the x2 copies of the world alone are not kept, and an interior's whole room is its view.

**The looks.** Later zones reuse them: Nine Peaks and the Skyport Wreck the port's, the Gale Canyons the plains', the
Starsea the airships.
- **A sky port** (`sky_port`): a town of paving and dressed granite on a floating island, under its crags.
  - The island's south rim falls away into the `cloud_sea` vista. The airships berth there, hanging past the room's
    edge over the clouds, each gangway at the end of a pier and the way aboard.
  - Paved terraces and streets, lawns of azaleas and hedges in them with no tree (a canopy would hang over the walk),
    pines and plum on the rim.
  - Warehouses and houses (the kit's), the hawkers' stalls under the Alliance's white and sky awnings, the gate's
    archway on its dais between two stone lions, banners and lanterns.
  - The town gate east is two gatehouses of plastered wall over the street.
- **Open plains** (`storm_plains`): wide grass under a low rocky ridge, few trees (a biome's `tree_share` 0.3), dead
  trees the lightning killed, boulders and storm-split menhirs.
  - The herders' trail runs east to west.
  - The herds' trails are wavy strips of trampled earth braided across the grass (three rows deep, so a wander never
    breaks one).
  - Outcrops a level over the rise carry the side view's ledge chests.
  - The herders' camp: yurts, a cook fire, haystacks, the fenced plots.
  - The Lightning Scar: a burnt swathe with a floor of fused rock at its heart.
- **Snowy heights:** R4's `snowfield`, fresh snow over every cell and the walks packed.
  - Frostpine Climb's trail climbs three tiers, a flight between each, its landings fixed as features. Flights rise
    north, so a climb eastward zigzags up them.
  - Ice-glazed boulders (`ice_rock`) stand along the trails.
  - The summit stands over the `cloud_sea`, the hermit's cave in a cleft of its crags.
  - The ice cave is a cave room with a low front, its floor packed snow and its rock snowed.
- **A mirror lake** (`mirror_lake`): wide still water, the north shore's willows and maples on its bank, and lotus pads
  and floating lotus lanterns on it. The Reedless Shore has no reeds or cattails.
  - **Reflections:** the water mirrors what stands on its north shore (engine rule, below).
  - A pale strand where it meets the land (`lake.bank`'s sand), willow islets.
  - The Mirror Shallows are R2's wading floor (`h`).
  - The Sentinel Causeway is a granite causeway across open water: bastions with stone lanterns, plank bridges out to
    the islets.
  - The Lake Shrine is a round island, a hall on its granite plaza, the archway before the mirror's altar.
  - Toad's Hollow is a sunken basin walled in rock and willows round the toad's pool.

**New props** (`tools/art/topdown/furnish.py`, R6's block; the sheet rebuilt with `build_tiles.py`):
- `sky_ship`: a junk-built airship, its sprite hanging 48 px under its footprint (the room's last row) over the clouds;
  a still sprite, as four frames of it would outgrow the 512 px sheet;
- `market_stall`, `paifang` (an archway walked under: its footprint blocks nothing), `counter`, `stone_lion`,
  `armillary`;
- `herders_yurt` (the herders' felt yurt; R7's `yurt` is the desert keeper's), `haystack`, `cook_fire` (its flames
  flicker), `menhir`;
- `ice_rock`;
- `lotus_lantern` (it floats and bobs);
- `mirror_<kind>` and `mirror_<kind>_1`: the reflections of `tree_willow`, `tree_maple`, `tree_pine`, `tree_plum` and
  `lantern`. Each is drawn from the thing's own art, flipped about its foot and squashed to 0.55. Every other pixel is
  left out so the water's ripple shows through, and the rest is darkened toward the deep water.

**Engine rules.** None of them changes a room built before; every older spec compiles to its file byte for byte.
- **Mirror** (`mirror=True` on a water band or feature). Each tree or stone lantern on the water's edge, or one row
  back, gets its reflection laid on the water below its foot: `mirror_<kind>`, or `mirror_<kind>_1` a cell out with
  its first cell under the bank. It is laid only where the water runs on under the whole of it (the trunk's three
  columns at the foot, the crown's five further out) and nothing else stands at its foot. It blocks nothing. A
  lake's waterside trees are pinned (`pins["add"]`) where the composition wants a reflection.
- **A shaped region as ground:** a wavy or round band or feature named in `ground` gives its own cells, not its rect.

**Flights and the route tour.** The first full run's route tour (`rules_tests`) lost three legs. In each, an open-sided
flight stood on or beside a walk, and auto-path's steering sent the body along a step from its side, where it wedged.
- Every raised shape in R6's rooms is now climbed by R4's `flights=[col]`: the flight ends at the ground below, and its
  cheeks are closed by boulders.
- Frostpine Climb's hand-laid flights have their trails moved off their sides (`wavy="s"`) and boulders at their
  cheeks.
- The lake's bluff stands two levels over its knolls, so no hop takes a body onto it.
- The Snow Ape Ledges' trail wanders on its south edge only (`wavy="s"`). Its north edge had cut a row into the slope
  under the west shelf's flight, leaving the flight's foot a step low over a dark slot.

A scratch walk of every leg (from the spawn and each way in, to every thing and way) found the same wedge on 16 of
them. After the change, the final walk of all 784 legs over the nineteen rooms arrives on every one.

**Set pieces and the side view's mechanics on the grid.**
- The plains' lightning strikes a body on the grid, and flight (T1) takes off over the port and the plains as anywhere.
- The side view's ropes, vines, ladders and rope bridges up to its ledges and cloud platforms are flights and raised
  outcrops here. T1's `traverse` rows (`docs/architecture/topdown_mechanics.md`) were not needed.
- The Thousand-Eye Toad's arena has no special terrain; it is fought on the hollow's open turf.
- Still with no top-down counterpart (`topdown_mechanics.md` lists them as still to do):
  - the slippery ice of Frostpine Climb and Rimefrost Summit (`volumes` of kind `ice`, their traction);
  - the Shipwrights' Yard's Starsea dock and its timed route (the skiff is the dock's object, sailed by its page);
  - the sky-ships' crossings: the ferries are ways at their gangways, as the side view's doors were.

**Still to do in these rooms.**
- Foes with no top-down art yet (the view draws stand-ins; E2's work): the Spark Weasel, the Stormgrass Stag, the
  Thunderhorn Rhino, the Frost Lynx, the Snow Ape, the Azure Carp Dragonet, the River Sentinel and the Thousand-Eye
  Toad.
- The water's reflections are props, and they do not move with the ripple. A mirror the water draws would be the
  terrain's (TopdownTerrain).

**The frontier now** (R6, with R5 and R7): Act I has no way off the grid left. Gu's Warehouse (R5) and the Ascension
Gate's way up (R6) are both open. With Nine Peaks laid out (R7), the Skydock's ferry to the Alliance Gate is open too,
and `topdown_act2_start` rides it over and back. Every way out of R6's rooms now leads to a room on the grid. The story
walks on foot from the valley through the Lake Shrine, and on by the ferry to Nine Peaks and the Tomb of Sunscar.

## Nine Peaks to the Tomb of Sunscar (R7)

The twenty rooms of Act II's chapters 13 and 14, now on the grid: Nine Peaks, the Gale Canyons, Ironroot Hold, the
Sunscar Desert and the Tomb of Sunscar. `topdown_sunscar` plays them by test shortcuts, a top-down character at Sage 2
set down off the sky-ship at the Alliance Gate, then walked room by room through their ways:
- Nine Seats: the envoy heard in the Hall of Nine, an Alliance seat taken, handed in to Elder Zhong; the Auction
  Pavilion's door and its block (the auction's page); the Trial Hall off the Presence Terrace and back;
- The Canyon Toll: the tollkeeper at the Canyon Mouth, six veiled brigands broken in the canyons, over the Windbridge to
  the Hold Gate;
- Ironroot Blood: the warden's spar won in the Hold Gate's yard, the Matriarch at the Clan Hearth's fire, the
  iron-root tablets honoured in the Ancestor Hall behind the forge's door;
- Glass and Bone (Sage 3): down the desert road over the Glass Dunes and the Scorpion Flats to the Oasis of Bones, six
  sandstorm scorpions, the bone-reader, the oasis's teleport stone;
- The Sealed Gate: dune worms fought on the Worm Sea for the sun seal's shards, down the portal into the Sealed Gate,
  the bronze doors shut until the lock is fitted and read (Insight 80), then open;
- Sovereign, and The Tomb King: through the Hall of Sand Kings to the Mirror Crypt (Lu's page), the Tomb King risen on
  his throne hall's sand floor and defeated there, the sun seal taken up and kept from the Grey Pilgrim, the old stair
  out to the Worm Sea, handed in at the oasis.

In each room it checks the walks and the view as `topdown_peaks` does: 57 checks.

| Room | Spec lines | Biome | Pictures (`docs/architecture/room_engine/r7/`) |
|---|---|---|---|
| `np_alliance_gate` | 21 | `sect_terraces` | `01_alliance_gate_dock`, `02_alliance_gate_lions`, `rooms/np_alliance_gate` |
| `np_hall_of_nine` | 24 | `sect_terraces` | `03_hall_of_nine`, `rooms/np_hall_of_nine` |
| `np_auction_pavilion` | 13 | (interior) | `04_auction_pavilion`, `rooms/np_auction_pavilion` |
| `np_presence_terrace` | 21 | `sect_terraces` | `05_presence_terrace`, `rooms/np_presence_terrace` |
| `np_trial_hall` | 16 | (interior) | `06_trial_hall`, `rooms/np_trial_hall` |
| `gc_canyon_mouth` | 18 | `canyon` | `07_canyon_mouth_toll`, `08_canyon_mouth_mesa`, `rooms/gc_canyon_mouth` |
| `gc_kite_winds` | 19 | `canyon` | `09_kite_winds`, `rooms/gc_kite_winds` |
| `gc_harpy_roosts` | 20 | `canyon` | `10_harpy_roosts`, `rooms/gc_harpy_roosts` |
| `gc_windbridge` | 24 | `canyon` | `11_windbridge`, `rooms/gc_windbridge` |
| `ir_hold_gate` | 23 | `iron_hold` | `12_hold_gate`, `rooms/ir_hold_gate` |
| `ir_clan_hearth` | 15 | `iron_hold` | `13_clan_hearth`, `rooms/ir_clan_hearth` |
| `ir_ancestor_hall` | 12 | (interior) | `14_ancestor_hall`, `rooms/ir_ancestor_hall` |
| `sd_glass_dunes` | 16 | `desert` | `15_glass_dunes`, `rooms/sd_glass_dunes` |
| `sd_scorpion_flats` | 17 | `desert` | `16_scorpion_flats`, `rooms/sd_scorpion_flats` |
| `sd_oasis_of_bones` | 20 | `desert` | `17_oasis_of_bones`, `rooms/sd_oasis_of_bones` |
| `sd_worm_sea` | 20 | `desert` | `18_worm_sea_tomb_door`, `rooms/sd_worm_sea` |
| `ts_sealed_gate` | 17 | `tomb` | `19_sealed_gate`, `rooms/ts_sealed_gate` |
| `ts_hall_of_sand_kings` | 21 | `tomb` | `20_hall_of_sand_kings`, `rooms/ts_hall_of_sand_kings` |
| `ts_mirror_crypt` | 19 | `tomb` | `21_mirror_crypt`, `rooms/ts_mirror_crypt` |
| `ts_throne` | 17 | `tomb` | `22_throne_of_the_tomb_king`, `rooms/ts_throne` |

As R4's, the capture's x2 copies of the world alone are not kept. The specs: `specs/nine_peaks.py`, `gale_canyons.py`,
`ironroot_hold.py`, `sunscar_desert.py`, `tomb_of_sunscar.py`.

**The looks.**
- **Nine Peaks** takes R3's `sect_terraces`: paved courts on granite terraces under the crags, pines, plum and maples,
  the cloud sea under the brinks. The Hall of Nine stands on a granite platform with a grand stair; the Presence
  Terrace's champions spar on a round terrace of dressed granite the road crosses; guardian lions and the Alliance's
  banners at the gates. The sky-ship's dock is a pier out over a bay cut back in the brink, its way off the south edge,
  where the cloud sea's vista draws the gangway down into the haze.
- **`canyon`** (the Gale Canyons). The earth paint's face carries a grass lip, which no red canyon has, so every ledge,
  mesa, pinnacle and wall is decision 44's sand: its faces are layered banks that read as sandstone. Only the room's
  lowest floor is red earth (`earth` over `lowest`, below), the trail a sandy wash across it, or trodden red earth
  where it runs on a shelf (`SHELF_GROUND`). Hoodoos, banded boulders, wind-killed grey trees and dry scrub; prayer
  flags on the wind; plank steps with sandstone at their cheeks. The south rim is humps a level up that stop a row
  short of the room's edge (a raised cell on the south edge leaves the void past the room under its lip).
- **`desert`** (the Sunscar): sand over everything, the caravan track trodden red earth, dunes with a crest a level
  higher toward the wind (`dunes()`), cactus, scrub, bleached ribs. The Oasis of Bones keeps a ring of grass round its
  pool out of the sand (`-green`, below): palms, reeds, the keeper's yurt. The Worm Sea's portal is a block of dressed
  stone set in a mound of sand, its door sunk a level into it, sand kings and braziers either side.
- **`iron_hold`**: the clan's grey rock, the iron-root trees' roots breaking out of it, pines, rubble by the walls. The
  Hold Gate is the gatehouse (a hall) at the cliff's foot, its door the way into the Clan Hearth: a cavern with the
  longhouse, the forge's house (its door the Ancestor Hall), the anvil, forges and braziers round the hearth.
- **`tomb`**: flagstone halls inside walls of cut sandstone (walls of sand paint), sand drifted in through the cracks,
  pillars (some crumbled), sand kings, sarcophagi, bronze mirrors, braziers, and the spike traps' pressure plates in the
  aisles (the side view's `spike_traps` strike near the body wherever it walks; the plates are their tell). The
  throne hall's floor is sand round the Tomb King's sun throne. Raised floors are paving, whose faces are blue-grey
  ashlar.
- **The prop kit** (`tools/art/topdown/arid.py`, joined to the sheet in `furnish.py`'s R7 block, built with
  `build_tiles.py`): a sandstone boulder, a hoodoo, prayer flags (four frames), a date palm, columnar cactus, dry scrub
  (walk-through), a ribcage, a yurt, an anvil, an iron brazier (four frames), the iron-root roots, a sarcophagus, a sand
  king's statue, a bronze mirror, a spike plate (flat, walk-through), the sun throne and a guardian lion. None is of
  the foliage kit, so the sand laid after the scatter runs under each.

**Engine rules** (`engine.py`, additive: every room before them compiles byte for byte, and `test_engine` holds it):
- a `ground` paint `earth`: bare earth (`d`) over meadow, flowers, marsh or sand, never under a plant of the foliage kit
  nor on paving, granite, rock or planks;
- a `ground` name `lowest`: the room's lowest floor off the walks and their cuts;
- a `ground` name `-name`: a band's or a feature's own cells kept out of that paint.

**Places.** Eight new rows in `places.py`, 41 places in all: the Alliance Gate's teleport stone and shrine, the Canyon
Shrine, the Hold Gate's shrine, the Clan Forge's anvil (smithing), the Scorpion Flats' and the oasis's shrines and the
Oasis of Bones' teleport stone.

**How the side view's verticality came down.** The canyons' rock ledges and cloud ledges are mesas, shelves and
pinnacles with plank stairs; the Windbridge spans a chasm on timber trestles three levels over a river that falls in
at the chasm's head; the Hold's decks are a timber watch tower; the tomb's ledges are galleries and alcoves a level or
two up. Every rope, vine and ladder of these rooms reached a ledge or a branch route and none is sealed, so each is a
flight of stairs or gone.

**Still to do in these rooms.**
- Foes with no top-down sheets yet (the view draws stand-ins; M-batches): the wind kite, canyon brigand, canyon harpy,
  sandstorm scorpion, dune worm, terracotta warden and the Tomb King; and the spar opponents, the alliance champion
  and Warden Tie Shan.
- Mechanics: none of the twenty rooms has a mover, a volume or a sealed climbable, so T1's rows have nothing to carry
  here. Their hazards are the World authority's and play on the grid: the canyons' wind gusts, the sandstorm, the
  scorching heat, the spike traps, and the quicksand, whose pull takes the Worm Sea's three `areas`.
- Light: the rooms' backdrops (`nine_peaks`, `gale_canyon`, `quarry`, `sunscar`, `sunscar_tomb`) have no TopdownLight
  area, so the cavern and the tomb follow the day's clock as the outdoors does. A lamplit area for them is game code,
  outside a room batch.
- Terrain: the kit has no red-rock or dressed-sandstone paint of its own. The canyons' walls and the tomb's are sand,
  and its raised paving faces blue-grey. A paint with its own warm faces would suit both.
- A capture spot must be open floor: a spot on a flight's cheek drew an empty world.
- Auto-path's route tour (`rules_tests`' topdown suite) found two things the pictures did not. First, a flight run
  down across the road holds the body at its cheek, so the Scorpion Flats' outcrop stops two rows short of the track.
  Second, every drop off a ledge turns the body back on landing (the steering aims at the drop's cell from the air),
  and more than two turns back on one leg fail. So the Windbridge's crag stands two levels over the shelf with its
  stair the one way up, and the crate lies on the shelf's lip rather than down in the chasm. A scan of every R7 flight
  against the walks (none crosses one now) and the tour over the twenty rooms (107 legs, none lost, none past one turn
  back but the Alliance Gate's ferry-to-east leg at two) back it.
- The world map: these are the first places outside the valley, and the map opened on a place showed the zone you
  stand in, not the place's. `map_page.gd`'s setup now opens the named place's own zone (`places_tests`).

**The frontier now** (R7): Nine Peaks' sky-ship back to Cloudgate Port was gated while the Skydock had no layout;
with R6's rooms it is open. The Alliance Gate's war gong and the Trial Hall's circle belong to chapters 15 and 16, whose events are R5's
story rooms (`si_sect_war`, `si_presence_trial`). Every other way out of an R7 room leads to a room on the grid. With
these rooms laid out, the Sect War's and the Presence Trial's ways back to the Alliance Gate (gated in R5's frontier
above) open; `topdown_story_rooms` checks them against `has_layout`, so it follows.

## The rooms left, and the pace

41 side-view rooms remain, by zone (`region`); the struck ones are done:

- **Reed Marsh and its neighbours** (R1, all done: "The road east: chapter 4" above):
  - `reed_marsh`: ~~`rm_grey_pools`~~, ~~`rm_sunken_causeway`~~, ~~`rm_hermit_stilt_house`~~;
  - `greyreed_hamlet`: ~~`gh_hamlet_square`~~;
  - `bamboo_grove`: ~~`bg_whispering_bamboo`~~, ~~`bg_thicket_heart`~~;
  - `crane_falls`: ~~`cf_falls_pool`~~, ~~`cf_behind_falls`~~;
  - `cleansing_peak`: ~~`cp_pilgrim_stairs`~~, ~~`cp_cleansing_summit`~~. Chapter 4's path.
- **Deepwater and the gorge:**
  - ~~`deepwater_bend`: `dw_serpents_shallows`~~ (R2);
  - ~~`drowned_shrine`: `ds_flooded_gate`, `ds_hall_of_lanterns`, `ds_scripture_well`, `ds_abbots_sanctum`,
    `ds_drowned_grotto`~~ (R2);
  - ~~`whitewater_gorge`: `wg_gorge_mouth`, `wg_rapids_terraces`, `wg_echo_cliffs`, `wg_waterfall_cave`~~ (R2).
- **Stoneford and the sects' insides** (R3, all done: "The third batch" above):
  - `stoneford`: ~~`sf_beast_grove`~~, ~~`sf_county_hall`~~, ~~`sf_trial_tower`~~;
  - `stonewall_quarry`: ~~`sq_quarry_rim`~~, ~~`sq_lower_pit`~~, ~~`sq_collapsed_tunnel`~~;
  - `jade_sect`: ~~`ja_alchemy_hall`~~, ~~`ja_library`~~, ~~`ja_retreat`~~, ~~`ja_cave_abode`~~;
  - `cloud_sect`: ~~`cm_cloud_library`~~, ~~`cm_herb_terraces`~~, ~~`cm_retreat`~~, ~~`cm_cave_abode`~~.
- **The peaks** (R4, all done: "The peaks (R4)" above):
  - `crane_cliffs`: ~~`cc_cliff_faces`~~, ~~`cc_sky_ledges`~~;
  - `mist_peak`: ~~`mp_misty_slopes`~~, ~~`mp_forgotten_monastery`~~, ~~`mp_ascension_gate`~~;
  - `summit_ridge`: ~~`sr_windswept_ridge`~~, ~~`sr_frozen_shrine`~~;
  - `hidden_vale`: ~~`hv_vale_gate`~~, ~~`hv_sect_grounds`~~, ~~`hv_back_mountain`~~;
  - `unmapped`: ~~`hg_hidden_grotto`~~.
- **The story's own rooms** (R5, all done: "The story's rooms and the Tidebreak Front (R5)" above):
  - `story`: ~~`si_gus_warehouse`~~, ~~`si_presence_trial`~~, ~~`si_sect_war`~~, ~~`si_siege`~~,
    ~~`si_trial_of_reflections`~~;
  - `tidebreak_front`: ~~`si_tide_battle`~~, ~~`tf_drone_hive`~~, ~~`tf_greyfall_breach`~~, ~~`tf_hollow_wake`~~,
    ~~`tf_tidebreak_bastion`~~.
- **Act II and after** (R6 the first four: "Act II's first zones (R6)" above; R7 the next five: "Nine Peaks to the
  Tomb of Sunscar (R7)" above):
  - `cloudgate_port`: ~~`ae_landing`~~, ~~`ae_port_market`~~, ~~`ae_wayfarers_inn`~~, ~~`ae_skydock`~~,
    ~~`ae_condensing_hall`~~, ~~`ae_shipyard`~~;
  - `thunderhorn_plains`: ~~`tp_stormgrass_verge`~~, ~~`tp_herders_camp`~~, ~~`tp_thunderhorn_flats`~~,
    ~~`tp_lightning_scar`~~;
  - `rimefrost_heights`: ~~`rf_frostpine_climb`~~, ~~`rf_snow_ape_ledges`~~, ~~`rf_rimefrost_summit`~~,
    ~~`rf_hermits_ice_cave`~~;
  - `mirrorwater_lake`: ~~`ml_reedless_shore`~~, ~~`ml_mirror_shallows`~~, ~~`ml_sentinel_causeway`~~,
    ~~`ml_lake_shrine`~~, ~~`ml_toads_hollow`~~;
  - ~~`nine_peaks` (5)~~ (R7);
  - ~~`gale_canyons`, `ironroot_hold` (4, 3)~~ (R7);
  - ~~`sunscar_desert`, `tomb_of_sunscar` (4, 4)~~ (R7);
  - `skyport_wreck` (4);
  - `lanternfall_harbor`, `drifting_shoals`, `blackmast_haven` (4, 4, 4);
  - `wyrmnest_isles` (4);
  - `warden_citadel`, `orbit_ruins`, `ashen_reach` (4, 4, 4);
  - `nebula_deep`, `lantern_heart` (4, 3);
  - `starsea`, `lantern_crossing` (1, 1).

**The pace.** Once a zone's look is settled, a spec takes 10 to 15 minutes:
- writing it from `--new`;
- `--show`;
- one capture run (about 90 seconds for a set's rows);
- a look and a tweak.

That is about **4 to 6 specs an hour per agent**. The six rooms here took about two hours, with the engine's caves,
round shapes and wavy shores built alongside them.

A zone needing a new biome costs an hour more: snow, desert, ship decks, a sect's courtyards. So does a new mechanic:
- crumbling floors;
- the boss arenas' special terrain;
- the Hollow Night's kind of event spawns.

The 135 rooms come to about 30 agent-hours: about 7 hours for five agents in parallel by zone. Each agent should:
- own whole zones;
- convert along the story's path, so the frontier tests move once per batch;
- run the full suite once at the end of a batch.
