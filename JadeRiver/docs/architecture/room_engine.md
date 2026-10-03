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
   cave biome's `rubble` turns the earth floor beside a wall to rock, where its ferns and rocks grow.
2. Places the props written out (or `pins["props"]`, the whole hand-placed list).
3. The ways: door paths, cuts through the bands for a north or south way.
4. Resolves the anchors. A raised shape that will get a flight counts as reached here; the checks hold the result.
5. `stairs="auto"`: a flight under a cut wherever it climbs a level edge, as wide as the path, and one up onto every
   raised shape something stands on (or every terrace band three rows deep), on its south face at the column nearest
   what stands on it, two rows a level, its foot on the ground below.
6. The foes' spawns.
7. The props a rule lays, then the flora. Each band's edges are cut into strips by habitat: a meadow's back (trees
   among bushes) and its lip, a cliff's foot, a road's verges (no tree on its shoulder), the water's bank, shallows
   and open water. Each strip is cut into stretches whose ends wander, one piece tried in each in the order of a hash
   of the seed and the cell (a Poisson disc kept even along the edge, never a fence-straight row). A piece fits where
   the foliage kit's rules hold (its ground, off kept-clear cells, ways' lanes and stairs, its canopy hiding no thing
   or way), stands on one level, keeps its kind's spacing, and cuts nothing off.
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
- The capture set `room_engine` (`tools/dev/capture/shots.gd`, `E1_VIEWS`): each converted room under the HUD, the world
  alone at x2, and whole, into `docs/architecture/room_engine/` (a batch's views under its own folder: `r1/`). The set
  keeps the body whole (`keep_whole`, which also never leaves it wounded), so a foe the room spawns does not lay it down.

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
4. A vista goes into `topdown_life.VISTAS` (until E3 owns the living world). A biome the zone needs goes into
   `biomes.py`.
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
- The side view's movers (the Grey Pools' rafts, the hermit's raft), the falls' updraft and the vines have no
  top-down counterpart; Leaf on the Wind's glide is the side view's.
- A set piece's waves are called to the side view's points, read as world units on the grid: the summit is 28 rows
  deep and the Pilgrim Stairs 72 cells wide so that Heaven's Cleansing's and the Iron Body trial's points land on open
  ground. Converting their points is the engine's work, not a room's.

**The frontier now:**
- Bend Shore's ways west (Whitewater Gorge), to the Serpent's Shallows and to the Drowned Shrine;
- the Falls Pool's misty path to the Hidden Vale;
- the sects' halls and abodes;
- the Trial Tower;
- the Quarry Road;
- the Beast Grove;
- the County Hall;
- Gu's Warehouse.

The story's next quest past chapter 4, The Shrine Surfaces (the Drowned Shrine), is past the gate.

## The rooms left, and the pace

125 side-view rooms remain, by zone (`region`); the struck ones are done:

- **Reed Marsh and its neighbours** (R1, all done: "The road east: chapter 4" above):
  - `reed_marsh`: ~~`rm_grey_pools`~~, ~~`rm_sunken_causeway`~~, ~~`rm_hermit_stilt_house`~~;
  - `greyreed_hamlet`: ~~`gh_hamlet_square`~~;
  - `bamboo_grove`: ~~`bg_whispering_bamboo`~~, ~~`bg_thicket_heart`~~;
  - `crane_falls`: ~~`cf_falls_pool`~~, ~~`cf_behind_falls`~~;
  - `cleansing_peak`: ~~`cp_pilgrim_stairs`~~, ~~`cp_cleansing_summit`~~. Chapter 4's path.
- **Deepwater and the gorge:**
  - `deepwater_bend`: `dw_serpents_shallows`;
  - `drowned_shrine`: `ds_flooded_gate`, `ds_hall_of_lanterns`, `ds_scripture_well`, `ds_abbots_sanctum`,
    `ds_drowned_grotto`;
  - `whitewater_gorge`: `wg_gorge_mouth`, `wg_rapids_terraces`, `wg_echo_cliffs`, `wg_waterfall_cave`.
- **Stoneford and the sects' insides:**
  - `stoneford`: `sf_beast_grove`, `sf_county_hall`, `sf_trial_tower`;
  - `stonewall_quarry`: `sq_quarry_rim`, `sq_lower_pit`, `sq_collapsed_tunnel`;
  - `jade_sect`: `ja_alchemy_hall`, `ja_library`, `ja_retreat`, `ja_cave_abode`;
  - `cloud_sect`: `cm_cloud_library`, `cm_herb_terraces`, `cm_retreat`, `cm_cave_abode`.
- **The peaks:**
  - `crane_cliffs`: `cc_cliff_faces`, `cc_sky_ledges`;
  - `mist_peak`: `mp_misty_slopes`, `mp_forgotten_monastery`, `mp_ascension_gate`;
  - `summit_ridge`: `sr_windswept_ridge`, `sr_frozen_shrine`;
  - `hidden_vale`: `hv_vale_gate`, `hv_sect_grounds`, `hv_back_mountain`;
  - `unmapped`: `hg_hidden_grotto`.
- **The story's own rooms:**
  - `story`: `si_gus_warehouse`, `si_presence_trial`, `si_sect_war`, `si_siege`, `si_trial_of_reflections`;
  - `tidebreak_front`: `si_tide_battle`, `tf_drone_hive`, `tf_greyfall_breach`, `tf_hollow_wake`,
    `tf_tidebreak_bastion`.
- **Act II and after:**
  - `cloudgate_port` (6);
  - `thunderhorn_plains`, `rimefrost_heights`, `mirrorwater_lake` (4, 4, 5);
  - `nine_peaks` (5);
  - `gale_canyons`, `ironroot_hold` (4, 3);
  - `sunscar_desert`, `tomb_of_sunscar` (4, 4);
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
