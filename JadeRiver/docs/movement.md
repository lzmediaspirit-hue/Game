# World movement

How the body moves through Jade River's rooms, what it can stand on, and what every room gives
the jump to do. Numbers live in `data/movement.json` (built by `tools/data/stats.py`); the solver's constants
in `scripts/simulation/movement_solver.gd` must match it, and `data_validation` checks that they do.
The rules test `movement_suite` (`tests/rules_tests.gd`) runs the real solver against the built rooms,
so this document and the game can't drift apart silently.

## The mechanics

The rules follow Build Prompt v2 S43. The numbers are constants in `MovementSolver`, and the traversal
suite in `tests/rules_tests.gd` checks each one.

| Move | How | Reach |
|---|---|---|
| Walk | Across the ground strip and onto anything whose height meets the feet (stairs, ramps) | — |
| Jump | `JUMP_IMPULSE` 530 against `GRAVITY` 1150. Height is fixed and never scales with stats or gear. Coyote time 0.10 s after walking off an edge; a press up to 0.12 s before landing is buffered and fires on landing | peak **122** units |
| Cloud Ladder Step (double jump) | Learned from the guided quest *Cloud Ladder* at Qi Unfurling 6, usable from acceptance. A second jump in the air at impulse 430, once per airtime | **+80** from where it is used; about **202** from the ground |
| Drop through | Joystick toward the camera (≥ 0.7, sideways < 0.3) + Jump, on a platform only: never the ground or a block | — |
| Ledge mantle | Automatic. Falling while pushing toward a top 0–24 units up and within 16 across pulls you onto it | +24 |
| Climb | Ladders, ropes, vines and chains (`climbables` in room data). Hold toward the ladder's end for 0.3 s (up at its foot, down at its top) or use the Climb context. 160 units/s, stop anywhere; Jump lets go sideways; a hit knocks you off | the climbable's top |
| Wall-Step | Learned from the guided quest *Between Two Walls* (Echo Cliffs, Heart Tempering 4), usable from acceptance. In the air, pushing into a wall face within 12 units: vertical speed 450 (+88) and 90 units away from the wall. Three kicks per airtime | shafts 60–160 wide |
| Air attack | One hit, no combo, +10 % damage; horizontal speed stays at ×0.8 (ground attacks ×0.3) | — |
| Plunge | Learned in the *Outer Trial* (Bone Forging 4). Joystick toward the camera + Attack in the air: straight down at 900. The landing strikes everything within 60 for 120 % damage and a 0.5 s stun, and breaks jars and cracked floors. 4 s cooldown | — |
| Dodge Dash | Bone Forging 5. Evade tap on the ground: 140 units, 0.25 s invulnerable, 2.5 s cooldown. No dodging in shallow water | 140 |
| Falling Leaf Glide | Learned in *Leaf on the Wind* (Falls Pool, Qi Kindling 3). Hold Jump while falling, from the take-off press or after a second press: the fall is capped at 120/s and drift is ×1.1. 2 QI a second. Works where flight is refused | about **300** flat from an apex jump, 1.5 s aloft |
| Swallow Dart | Learned in *Swallow Dart* (the library's first floor, Qi Kindling 7). Evade tap in the air: 140 units while the height is held for 0.25 s. Once per airtime; shares the dodge's cooldown | 140 across |
| Water Skimming | Learned in the hermit's *Skipping Stones* (Qi Unfurling 8). Sprint onto deep water and keep running; stopping for 0.5 s sinks you | any deep water |
| Wind Blink | Secret art, learned at Spirit Awakening 5. When Swallow Dart is spent or unknown, an Evade tap in the air blinks 120 along the facing with a small lift. 10 s cooldown (`combat.wind_blink_cooldown_s`) | 120 across |
| Flight | Cloud Stride 1. Hold Jump as you start to fall (it replaces the glide where flight is allowed and QI is above 10 %). Hold Jump to rise, hold Evade to descend, neither to hold height; tap Evade to dash. Refused indoors, on sect grounds, in dungeons and in `no_flight` volumes | ceiling **340**, climb 220/s |
| Breath Control | Secret art, learned at Qi Unfurling 3. Lets you go down into flooded places (the Drowned Grotto) and swim deep water for 30 s at ×0.6 | — |

**Edges.** Each surface edge is `open` (walk off and fall), `closed` (blocks walking) or `wall` (closed, and a
wall face). Platforms close their back (north) edge by default, so walking into the screen off a roof no
longer drops you below the world. Their front and side edges stay open. Ground surfaces are closed all
round.

**Blocks.** `blocks` in room data are solid boxes with a walkable top, open all round:
- Standard tops are 40, 60, 80 or 110.
- An actor more than 8 below the top slides along the block. One that falls onto the top lands on it.
- A 60 block is jumped over at walk speed.
- Block sides are wall faces for Wall-Step.
- The top is drawn with a lit lip.

**Falls.** A fall below the room's void altitude (by default 250 under its lowest surface) returns you to the
last safe position, which is recorded after 0.3 s standing at least 24 units from an open edge. The fall
costs 5 % of max HP (never below 1), except in the Prologue, towns and safe rooms.

**Controls.** A portal needs a 0.3 s press-up hold with little sideways input, because a plain press up walks
into depth. The Attack button offers Climb or Enter only while no enemy is aggroed on you within 400. In a
fight, a separate Context button appears at (1165, 500).

**Events.** The movement authority announces `jumped`, `landed` (with the fall height and whether it was a
Plunge), `wall_kicked`, `art_used`, `climb_started`, `climb_finished`, `fell_out`, `mover_boarded`,
`volume_entered` and `volume_left`. `art_used` advances guided-quest objectives named after the art
(`plunge`, `glide`, `air_dash`, `double_jump`, `water_skimming`, `wall_step`, `drop_through`, `mantle`).
The first time an art is learned, a toast gives its name and a one-line how-to.

### Volumes and movers

`volumes` in room data are rectangles on the plane with an altitude range (`alt: [low, high]`):

| Volume | Effect | Where |
|---|---|---|
| `water_shallow` | Walking ×0.7; no sprint and no dodge. Every `shallows` area makes one | Reed Shallows, Bend Shore, the Drowned Shrine |
| `water_deep` | A body standing in it sinks 40 over 1 s and is returned to the last safe spot. Breath Control swims for 30 s at ×0.6; Water Skimming runs across while sprinting. No safe spot is ever recorded in it | the hermit's pond |
| `current` | Pushes a body standing in it along `push` | Flooded Gate (80 west) |
| `updraft` | While falling, gliding or flying, vertical speed eases toward +220 | Falls Pool spray, Cliff Faces |
| `wind` | Pushes along `push` on a 4 s cycle: strong for 1.5 s, a breeze (×0.3) the rest, ×1.5 within 48 of an open edge | Windswept Ridge |
| `bounce` | Landing on it launches at 700 (apex about 213) | the Fairground drum |
| `crumble` | Its surface gives way 0.8 s after a foot lands and returns 5 s later | Mudwater Tunnels' rotten boards |
| `rising_water` | Deep water whose top follows a script keyed to an event (`rise`: event, match, to, over_s, hold_s, back_to) | Serpent's Shallows: at half health the serpent floods the shallows to 30 for 14 s |
| `hazard` | Status and damage each pulse while inside | — (S17 hazards cover the current rooms) |
| `no_flight` | Flight refused; glide still works | — (room types cover sect grounds and dungeons) |

`movers` carry a surface or block along `path` (offsets `[dx, depth, altitude]`) at `speed`, waiting `wait_s`
at each end, in `loop`, `pingpong` or `trigger` mode. The position is a pure function of the room clock
(`ZoneGeometry.time`, advanced by the World authority each tick), so replays match. Riders move with the
mover's change of offset before their own step. The hermit's raft crosses the pond this way. A surface with
`cracked: true` breaks under a Plunge and stays broken for the visit.

### Camera, combat on tiers, monsters and allies

**Camera** (S43 rule 13). Room data may give `camera {bounds: [x0, y0, x1, y1], look_ahead}`; the old
`y_min`/`y_max` still work. The default vertical range is 180–600, so high tiers stay in view while the floor
never scrolls off.
- The camera leads by a quarter of the body's velocity.
- Vertically it follows the surface underfoot, not the jump arc, settling in about 0.4 s after a landing.
- A fall of more than one tier (100) is followed down.
- Standing still for 0.5 s near an open edge above a drop of more than 150 looks down 60.

**Heights in a fight** (rule 10):
- Blows reach −30 to +60 of the attacker's height; Qi and Soul techniques reach −10 to +80. From the ground
  you cannot strike someone standing on an 88 roof, but you can catch them mid-jump.
- Flying monsters hover about 48 up, inside a grounded fighter's reach.
- Shots pass through platform decks but stop at blocks and building walls, whoever fired them.

**Monsters** (rule 11). Every species has `movement {jump, climb, fly, drop}` in `enemies.json`: humans,
duelists and leapers jump at 530, plain melee beasts hop at 430, and heavy beasts cannot jump.
- Each room builds a navigation graph once per movement profile: nodes are surfaces and block tops; edges
  are walk, jump (rise up to 85 % of the species' apex, gaps to 160), drop and climb. The graph is the same
  on every build.
- A melee monster whose target stands on another surface walks to the edge's take-off point and hops along
  the path.
- One that cannot reach its target (no path, or the target is more than 60 above its surface) waits beneath
  it. After 2 s it takes half damage from that target; after 6 s it goes home, healing 10 % a second.
- Archers, imps and apes shoot or throw from where they stand. Flyers ignore the graph and sink or climb
  toward the height they hunt at.
- Archers, imps, frogs, toads and vultures start on raised tiers where the room has them (walkers only on
  tiers of 100 or less).

**Allies** (rule 12):
- Pets and companions walk on surfaces and follow along the graph (pets carry `movement` in `pets.json`).
- An ally more than 480 away, or unable to reach its owner's surface for 2 s, blinks to the owner in a puff
  of mist.

**Landing ring and minimap.** While airborne within 200 above a surface, a jade ring marks where you will
land. The minimap draws blocks as small squares, climbables as vertical lines and movers as dashed lines.

### Surfaces

Every surface has a `kind`, which decides how it is drawn, and a `stratum`, which decides how it
collides.

- **ground** (stratum ground): the walk strip. Terraces are grounds with a `base` (a raised wall).
- **roof**: every building made with `Room.building()`. The roof is a platform. `ZoneLayout` gives it a
  solid body, so the facade below is a wall you can't walk through, and one Wall-Step can kick off it.
- **stairs, ramp**: grounds that climb. Ladders are climbables, not surfaces (see Climb above).
- **rock_ledge, branch, cloud, balcony, dock, deck**: one-way platforms drawn as rock shelves, garden
  decks, cloud banks, timber balconies on posts, and ship planking.
- **support**: the top of a solid prop. Any scenery block no taller than 80 units, or flagged
  `standable`, gets a support top, so a jump lands on crates, barrels, tables, low walls, carts,
  sarcophagi, boulders and training poles instead of sliding off them.

Objects placed on a platform carry `alt`, the platform's height, because interaction needs the
body within 48 units of the object's altitude. Chests on ledges and air pockets rely on this.

### Heights used by the world builder

`tools/data/world.py` places platforms at heights chosen from the reach table:

| Constant | Height | Meaning |
|---|---|---|
| `JUMP_ONE` | 100 | One jump lands on it (peak 122); the highest required rise before the double jump (S43) |
| `JUMP_TWO` | 176 | Out of reach of one jump; Cloud Ladder Step lands on it (peak 202). The verticality pass snaps natural ledges to 200 |
| `FLIGHT_LEDGE` | 300 | Out of reach of the double jump; only fliers land on it (ceiling 340) |

The v2 grid (Part 8) is built tiers at 88, 176 and 264, natural ledges at 100, 200 and 300, and blocks at 40, 60,
80 and 110. Surfaces reached by ladder, rope, stairs or mover may use other heights.

## The room verticality catalogue (v2, S43 rule 14)

Build Prompt v2 gives every valley room a row in its Part 8 room verticality catalogue: the tiers, the named
pieces and what is up there. Three steps build it, in this order, after the rooms are authored:

1. **`tools/data/catalogue.py`** shapes rooms to their rows by hand:
   - **Lotus Ferry and the Prologue:**
     - the lofts at 88, with ladders sealed until The Runaway Kite;
     - Home Lane's crates, well and fence, and Aunt Ping's ladle on a roof;
     - the roof chain and the watchtower;
     - the docks' boat deck and mast lookout;
     - Old Ma's shelves and storeroom;
     - the stilt decks and drifting rafts of the Reed Shallows.
   - **Willow Path, Stoneford and the sects:**
     - willow branches at 100, a fallen log, and a pine top at 240 (a chest, later: double jump);
     - the merchant's cart;
     - Market Street's awnings and bell tower, and a shard in the gutter;
     - Artisan Row's scaffolds at 90 and 180 with a ladder between them, and a chimney top at 330 (the tinkerer's gear, later: double jump);
     - Stoneford Gate's walltop at 160, reached by stone steps;
     - the Entry Trials: Jade's roof climb over two moving planks, and Cloud's ropes and crumbling ledge;
     - the Sword Court's plum-blossom poles and Wall-Step pillar pair;
     - Elder Sung's peaks and rope bridge;
     - both libraries' floors at 120 and 240, their ladders sealed by rank.
   - **Fields, dungeons and secret places:**
     - Quarry Rim's scaffolds and crane lift;
     - Lower Pit's rim and a cracked slab that a Plunge breaks to reach the shard beneath;
     - the Grey Pools' rafts over deep water, a moored raft with a chest, and a lily pad that bounces to an optional ledge;
     - the Sunken Causeway's 120 gaps and a broken pillar at 300 (jars, later: Wall-Step);
     - Whispering Bamboo's bamboo at 90 and 180, a bent bamboo that throws you to 233, and a chest at 330 (later: double jump);
     - Caravan Road's cliff ledge and rope bridge;
     - Gorge Mouth's bridge;
     - the Boss Den's wine shelves;
     - the Abbot's four bell ledges;
     - Behind the Falls' Wall-Step shaft (walls 120 apart) up to a chest at 520.
   A room shaped completely is marked `vertical: "authored"`, and the passes below leave it alone.
2. **`movement_pass()`** (described below) gives the rooms that still have nothing vertical their generated ledges and decks.
3. **`tools/data/verticality.py`** brings every other room to the rules:
   - heights snap to the standard grid (natural 100s, built 88s);
   - landings grow to at least 80 × 60;
   - wide fields, paths and towns get a raised route of chained tiers across 40% of the width. Where
     roofs or ledges are too far apart to jump, it hangs a **rope bridge** between them;
   - a room whose raised tiers are all one height gets a higher ledge beside one of them;
   - reward ledges out of the band's reach become **later** ledges for a named art;
   - every required tier gets a second way up (a ladder, rope or vine, a step block, or a step ledge);
   - 30% of breakables and a third of gathering nodes move onto tiers, and chests go to the highest tier.

The Sect Grounds are marked `vertical: "grows"`. Their roofs come with the sect's buildings, so the route rule does not apply to them.

### Room lint and reach contract

`tools/data/room_lint.py` checks every built room. It runs first in `tools/run_tests.sh` and fails the run
if any room fails. It checks:

- **tiers:** two tiers above the ground, and a raised route across 40% of the room;
- **raised:** at least 30% of breakables and a third of gathering nodes sit on tiers;
- **chests:** every chest is on the highest tier or an optional ledge;
- **ways:** every required tier has two ways up (jumps, climbables, stairs, movers, a bridge walked onto
  from the tier it joins, a moving plank stepped onto from a tier at its height);
- **landings:** at least 80 wide and 60 deep;
- **heights:**
  - built tiers use 88s and natural ones 100s;
  - blocks are 40, 60, 80 or 110 high, unless they are bounce pads;
  - blocks over 110 are walls.
- **reach:** everything required is reachable with the arts of the room's lowest realm.
- **later ledges:** each one is more than 122 above everything reachable (more than 202 once the band has
  the double jump), and still within its own art's reach.

Today all 122 rooms pass.

### Paths Above

Every later ledge (a surface or block with `later`) is a row in `data/paths_above.json`. The row gives the room,
the art it needs, its height and what is up there.

- **Finding a ledge.** Landing on one records it in the account (`paths_above`), emits
  `path_above_found` and shows a toast.
- **Codex tab.** The Paths Above tab lists every row as one of:
  - found, with its reward;
  - "your arts reach it now";
  - "out of reach for now".
- **World map.** A faint wind glyph beside a region, and a line under the room's name, mark a ledge whose
  art you have learned but whose top you have not stood on yet.

### New kit pieces

- **Rope bridge:** sways, and is walked onto from either end.
- **Walltop:** crenellated stone.
- **Chimney and stone pillar:** a brick or stone column with a small top; its faces are walls for Wall-Step.
- **Scaffold and stilt deck:** planks lashed to posts.
- **Awning:** striped cloth.
- **Bamboo:** slats lashed on two stalks, or a single pole.
- **Causeway:** a stone slab.
- **Cracked slab:** a block that a Plunge breaks.
- **Blocks:** logs, rubble, lily pads and bent bamboo.

World totals after v2:

- 142 rock ledges, 116 tree branches, 78 balconies, 43 roofs, 21 rope bridges, 15 bamboo pieces, 12 cloud banks,
  7 scaffolds, 6 stilt decks, 5 causeway sections, 5 decks, 4 branches, 3 awnings, 3 rafts, 2 board floors,
  1 chimney and 1 walltop;
- 58 blocks;
- 352 climbables: 137 ladders, 117 ropes and 98 vines;
- 8 movers and 20 volumes;
- 6 Paths Above ledges.

## The room audit (v1.1)

### Before

Of the 121 rooms, **79 were flat**: nothing to stand on but the ground strip. The double jump had
nothing to do outside towns with roofs. Low props (crates, barrels, tables) blocked the walk but
had no tops to stand on. Wall-Step, Wind Blink, Breath Control and Appraisal Eye were named in the
design but never granted or implemented. Lotus Heart Breathing was granted but did nothing.

### What changed

`movement_pass()` runs after every room is authored:

1. **Standable props.** A crate, barrel, sack pile, hay bale, small rock, table, low wall, bed,
   counter, large rock, mossy boulder, broken cart, sarcophagus, icicle rock, storage chest or piece of
   driftwood on the play layer, inside the walk strip and clear of portals, spawns and objects,
   becomes a solid block with a top. Its width comes from the art; its top height comes from
   `STANDABLE`.
2. **Fields, paths, dungeons, secrets and boss arenas** with nothing vertical get a 110 ledge and a
   220 ledge in clear stretches of the back row. The high ledge carries a chest from the zone's loot
   table, except in boss arenas, where the ledges are room to dodge.
3. **Outdoor fields and paths from level 37**, where Cloud Stride is in reach, get a cloud bank at
   320 with a chest only a flier can land beside.
4. **Towns, sect grounds and rest stops** with nothing to climb get a pair of timber decks (110
   and 220) under a lantern string.
5. **One-screen halls and interiors** get a loft on the back wall where the wall is clear.

`movement_extras()` places platforms by hand where the automatic pass finds no clear back row:

- terraces at the Skydock landing;
- the scaffold over the new hull at the shipyard;
- the fairground decks;
- the oasis rocks;
- the ledges behind the falls, in the collapsed tunnel and in the waterfall cave;
- the wall-walks and broken ramparts of the sect war and the siege;
- the summit rocks;
- the Starsea quarterdeck;
- plum-blossom poles in the home sect's yard;
- a rock shelf at the Vale Gate;
- two shelves on each elder's peak;
- a shelf in each cave abode.

It also adds the **Drowned Grotto**, a secret room below the Scripture Well:

- the way down needs Breath Control;
- the room is filled with `deep_water`, which drains breath until you reach an air pocket;
- it holds drowned acolytes and mist lotus;
- a chest waits on a ledge above the water.

### After

**122 rooms; 7 flat**, all by design:

| Room | Why it stays flat |
|---|---|
| Fisher's hut, Lu's boat | The first interior and the home boat: one screen, all furniture |
| Condensing Hall, Falls Pool, Lake Shrine | Insight rooms: a place to sit, not to climb |
| Presence Trial, Trial of Reflections | Story trials fought on a bare floor on purpose |

Totals across the world:

- 42 roofs;
- 136 rock ledges;
- 33 balconies and decks;
- 12 cloud banks;
- 9 garden branches;
- 3 docks and ship decks;
- 2 stair runs and a ladder;
- 30 standable props;
- 68 generated ledges and 24 decks and lofts.

The test asserts that no more than 3 fields, towns or dungeons are left flat.

## Tests

`movement_suite` in `tests/rules_tests.gd` checks:

- a single jump peaks at 122;
- the Thunderhorn Flats have a 110 ledge, a 220 ledge and a cloud bank;
- driving the real solver, one jump lands on the 110 ledge, one jump does not reach the 220 ledge,
  a double jump does, and the chest waits there;
- the cloud bank is beyond a double jump;
- a crate in the Skydock shipyard has a top a jump lands on;
- `paths_above_suite`: every Paths Above row names a real later ledge; the Lower Pit slab is a cracked block
  that blocks until a Plunge breaks it; the Jade trial's two planks move; both library floors are sealed by
  rank; landing on a later ledge finds it once and saves it with the account;
- Wall-Step kicks off the Old Ma store's facade in Lotus Ferry, only once per time in the air, and
  not where there is no wall;
- every field, town and dungeon has something to climb.

`data_validation` checks that every ledge chest sits on a surface at its `alt`, and that every
portal and object is reachable.
