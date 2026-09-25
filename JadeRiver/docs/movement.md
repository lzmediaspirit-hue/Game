# World movement

How the body moves through Jade River's rooms, what it can stand on, and what every room gives
the jump to do. Numbers come from `scripts/simulation/movement_solver.gd` and `tools/data/stats.py`.
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
| Wind Blink | Secret art, learned at Spirit Awakening 5. Dodge in the air: a 120-unit blink along the facing with a small lift. 10 s cooldown (`combat.wind_blink_cooldown_s`) | 120 across |
| Flight | Cloud Stride 1. Jump again at the top of a double jump to take off; QI drains while aloft | ceiling **340**, climb 220/s |
| Breath Control | Secret art, learned at Qi Unfurling 3. Lets you go down into flooded places (the Drowned Grotto) | — |

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

**Events.** The movement authority announces `jumped`, `landed` (with the fall height), `wall_kicked`,
`art_used`, `climb_started`, `climb_finished` and `fell_out`. `art_used` advances guided-quest objectives
named after the art.

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
| `JUMP_TWO` | 176 | Out of reach of one jump; Cloud Ladder Step lands on it (peak 202) |
| `FLIGHT_LEDGE` | 300 | Out of reach of the double jump; only fliers land on it (ceiling 340) |

## The room audit

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
- Wall-Step kicks off the Old Ma store's facade in Lotus Ferry, only once per time in the air, and
  not where there is no wall;
- every field, town and dungeon has something to climb.

`data_validation` checks that every ledge chest sits on a surface at its `alt`, and that every
portal and object is reachable.
