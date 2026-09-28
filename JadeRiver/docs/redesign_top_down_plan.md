# Redesign plan · Jade River in a top-down room world with height levels

This page plans the move from today's side-view 2.5D rooms to a **top-down ¾ room world with height levels**, in the
style studied in `docs/research/alabaster_dawn_2_5d.md`. The HUD and the in-game system pages stay; the user likes
them. The plan is written for this codebase and Godot 4.5.1 (GL Compatibility, 1280×720, touch first).

Everything drawn or named for the redesign is original to Jade River. Alabaster Dawn and CrossCode are references for
*systems*: the projection, height levels, sorting and auto-hop. Their art, names, layouts and characters are not
copied.

---

## 0. Where we start: the simulation is already top-down in disguise

Today's rooms look side-on, but the simulation already models a ground plane with a height:

| Piece | Today | What it means for the redesign |
|---|---|---|
| Position | `ActorState.plane` (x, depth y) + `altitude` | The same (x, y, z) model as CrossCode, where positions are ground x/y plus height z (research §2.1, [C1]) |
| Projection | `player.gd:509`: `position = Vector2(plane.x, plane.y − altitude)`, snapped to 2 px | Already the 1:1 oblique projection of a top-down ¾ view (research §4.1) |
| Sort | `ZoneGeometry.render_depth()`: `1500 + plane.y`, raised to `1502 + surface.bounds.end.y` when standing on a raised surface | Already the "sort by ground y, bias past the face below you" rule (research §4.2) |
| Collision | `WalkSurface` rects with a height, per-edge `open` / `closed` / `wall`, blocks, volumes, movers | Already per-height collision. A tile height grid can compile into these surfaces |
| Navigation | `ZoneGeometry.nav_graph()`: walk, jump, drop and climb edges per movement profile | CrossCode's multi-level NavMap idea (research [C3]) |
| Occlusion | `occlusion_outline.gd` | The silhouette effect when behind a face |
| Shadow | `shadow.gd`, landing ring | The height cue in the air |

What makes it side-view is the **room shape** and the **drawing**:

- rooms are 2–3 screens wide with a walk strip about 340 deep (`data/rooms/ae_landing.json`: `ground` rect
  `[0, 620, 2560, 340]`);
- a painted backdrop fills the rest of the screen;
- platforms are rooftops seen from the front;
- facing is ±1;
- sprites are drawn in profile.

The redesign widens the strip into a full floor, redraws everything, and makes facing a direction.

---

## 1. Target spec

### 1.1 Camera and projection

| Item | Spec |
|---|---|
| Projection | 1:1 oblique ¾ top-down: `screen = (x, y − z)`. Floor tops draw as squares; a vertical face of height h takes h screen px. No 3D camera (research §6 on the cost of WebGL-style 3D) |
| Internal resolution | The world renders in a **640×360 SubViewport** (one art pixel = one viewport pixel), scaled ×2 into the 1280×720 canvas. `scenes/pixel_stage.tscn` already wraps the game in a SubViewport. The HUD and pages stay at 1280×720 on their own CanvasLayers, so their HD fonts are untouched |
| Device scaling | 1280×720 → device keeps `canvas_items` / `keep`. The world texture is integer-prescaled, then filtered once (sharp-bilinear) so non-integer phone ratios do not shimmer |
| Follow | Both axes. Look-ahead 0.2 × velocity. The camera tracks the **ground height underfoot**, not the jump arc (today's rule, `data/movement.json` `camera`). It snaps to the 640×360 grid after smoothing. Settle 0.3 s |
| Bounds | Per room, `camera.bounds` as today. A room smaller than the view is centred |
| View | 40 × 22.5 tiles on screen |

### 1.2 Tiles and height levels

| Item | Spec |
|---|---|
| Tile | **16 art px** (32 world units at today's scale of 2 units per art px). 1 world unit = 1 px of the 1280×720 canvas, as today, so all rule numbers keep their unit |
| Level step | **1 level = 16 art px = 32 units.** A face one level high is one tile row |
| Levels per room | 0–6 (z 0–192). Void and water are separate marks |
| Stairs and ramps | Surfaces with `rise` (they exist today). The step-up limit without a jump is 8 units |
| Bridges, decks, lofts | Extra `WalkSurface`s above lower floor (walk under a bridge). They stay hand-placed surfaces, not grid cells |
| Tile layers per room | `floor` (tops, per level), `faces` (generated from the height grid), `detail` (decals, grass tufts), `overhang` (canopies, eaves; drawn above actors and faded to 35% when the player is under them). Godot 4.5 `TileMapLayer` nodes, one set per level; terrain sets for auto-tiling |
| Collision source | The height grid compiles into `WalkSurface` rects with edge types (research §4.3). `MovementSolver` never reads tiles |

### 1.3 Depth sort

- One Y-sorted `Node2D` holds actors, props, NPCs, loot and wall-face strips. Every item's sort key is set
  explicitly, never taken from screen y:
  - an actor: its ground y, raised past the south edge of any level it stands on (today's `render_depth`);
  - a prop: the south edge of its footprint;
  - a face strip: the south edge of its level.
- Floors draw below the sorted layer; overhangs draw above it.
- The occlusion outline shows when an actor is covered by a face or overhang whose key is higher.
- Ties sort by z.

### 1.4 Characters and animation

| Item | Spec |
|---|---|
| Size | An adult is **~38 art px tall** (today ~50) in a **64×64 art px cell**, anchored at the feet. That is about 2.4 tiles, readable on a phone at 640×360. Creatures scale from the same reference: small 16–20, medium 24–32, large 48–64, bosses up to 96 art px |
| Directions | Movement is **8-way analog**. Art has **8 facings from 5 drawn** (S, SE, E, NE, N); SW, W and NW mirror, as the current sheets already mirror left from right. First milestone: **S, E, N drawn** (4 facings, diagonals take the nearer row with 20° hysteresis). SE and NE follow in Phase 5 |
| Facing-locked animations | Climb (N only), meditate (S only), fishing cast (the four cardinal facings). The other facings carry an explicit `hidden` or redirect entry, as `AGENTS.md` rule 2 requires, never a missing key |
| Layers | Body → shoes → pants → shirt → cape → hair → hat → weapon, as today (`avatar.gd`). Layer order changes per facing (cape and weapon go behind the body facing N), so `z` becomes a per-facing value in `data/parts.json` |
| Dyes | Palette-swap shader on indexed garment sheets, replacing baked dye PNGs (`art/dye/` is 24 MB). A dye is a palette row. Works in the Compatibility renderer |
| Weapons | A **reviewed attachment rig** per facing: hand anchor and angle per frame, plus weapon sprites in 8 rotations. `AGENTS.md` rule 1 allows a reviewed rig. `combo_rig.gd` / `equipment_rig.gd` are the base |

The animation catalogue (per `AGENTS.md`: every entry exists for every body, hair, shirt, pants, shoes and weapon
layer):

| Animation | Frames | fps | Loop | Notes |
|---|---|---|---|---|
| idle | 6 | 6 | yes | breathing; the weapon held low |
| walk | 8 | 10 | yes | tiptoe plays it at 0.6× |
| run (sprint) | 8 | 14 | yes | lean forward; dust at 2 and 6 |
| jump | 9 | 12 | no | takeoff 2, rise 2, apex 1, fall 2, land 2. Hops play takeoff → fall → land |
| dodge | 6 | 18 | no | a short qinggong step with afterimage FX; i-frames at 1–3 |
| punch_1–3, swing_1–3, thrust_1–3 | 5–6 each | 14–16 | no | the existing combo families, through `combo_rig.gd`; `hit_frame` per step |
| bow | 7 | 12 | no | draw, hold, release |
| cast | 6 | 12 | no | techniques; the hand-seal on 3 |
| guard | 2 | 6 | hold | |
| hurt | 2 | 10 | no | |
| knockdown | 5 | 10 | no | defeat and heavy knockback |
| climb | 4 | 8 | yes | N only |
| meditate | 4 | 4 | yes | S only |
| interact | 4 | 8 | no | gather, open, tend, pray |
| glide / fly | 4 | 8 | yes | Falling Leaf Glide and flight vessels |
| plunge | 3 | 12 | no | |

**Volume estimate.**

- **Body:** ~110 frames per facing, times 3 facings in the first milestone and 5 in the full set, minus the
  facing-locked animations. About **330 → 520 body frames**.
- **Equipment layers:** today 6 hair, 5 shirts, 5 trousers, 3 shoes, 6 hats, 3 capes, 12 weapons, redrawn on those
  frames.
- **Dyes:** go to palette swaps. **Weapons:** go to the rig, which leaves 12 × 8 rotation sprites plus the per-frame
  anchors.

### 1.5 Shadows and height cues

- A blob shadow is drawn on the surface under the actor at `(x, y − surface_height)`. It shrinks and fades by
  (z − surface) / 96.
- The jade landing ring shows while in the air within 200 of a surface (it exists).
- Level edges get a 1-art-px rim highlight on the top and a darker first face row.
- An optional **height assist** (Settings) tints each level's top edge with a level colour. This answers the
  height-reading complaint in research §1 and §6.
- Tall props cast baked shadows in the tile art, light from the upper left, as `docs/art-contracts.md` sets.

### 1.6 Movement numbers

Units are world units (1 art px = 2). Numbers live in `data/movement.json` and `MovementSolver`, checked by
`data_validation` as today.

| Move | Today | Top-down |
|---|---|---|
| Walk | `move_speed` stat, default 205 | `move_speed × 0.75` (default ~154 units/s ≈ 4.8 tiles/s) |
| Tiptoe | — | Stick ≤ 0.6: 45% speed. **Never auto-hops**: walks off an open edge as a drop |
| Acceleration | Instant | 0 → full in 0.08 s; stop in 0.06 s; in the air, control × 0.35 (CrossCode's ground/air friction ratio is 1.0 / 0.2, research [C1]) |
| Sprint | ×1.7 after 2 s of sideways movement | ×1.6 after 1.0 s at full deflection, or hold Dodge after a dodge |
| Gravity / jump | 1150 / 530, peak 122 | **1700 / 400, peak 47** (1.5 levels), airtime 0.47 s |
| Jump reach | 100 (JUMP_ONE) | **1 level (32)** up, with mantle 12 |
| Double jump (Cloud Ladder Step) | 430, +80 | **330, +32**, total ~79: reaches **2 levels** |
| Auto-hop | — | Moving ≥ 70% speed into an open edge with a landing within reach: hop at impulse 300 (peak 26, 0.35 s). Same-level reach is about 1.7 tiles walking and 2.7 sprinting, more when landing lower. No landing: drop |
| Long jump | — | Dodge pressed within 0.12 s of an open edge: dodge speed (~430/s) carried into the hop, ~4.5 tiles |
| Coyote / buffer | 0.10 / 0.12 s | same |
| Dodge | 140 units, 0.25 s i-frames, 2.5 s cooldown | **96 units** (3 tiles), i-frames 0.15 s from the start, cooldown from data (2.5 s). Standing still: a back-step of 48 |
| Wall-Step | Kick off a face, +88 | Kick off a face you push into, **+1 level**, 3 per airtime |
| Glide | fall ≤ 120/s | fall ≤ 60/s, drift ×1.1 |
| Flight | ceiling 340 | ceiling **5 levels (160)** above the take-off surface |
| Plunge | 900 down | same, landing ring radius 48 |
| Climb | 160/s | 96/s on ladders and vines set on faces |
| Heights grid | 88 built / 100 natural, blocks 40/60/80/110 | Levels of 32; blocks 16, 32, 48 (half, one and one and a half levels) |
| Attack movement | ground ×0.3 | ground ×0.3, plus a 12-unit lunge toward the target on each combo step |
| Knockback | per attack | a 2D vector away from the attacker, 40–120 units over 0.15 s. It may push off an open edge to a lower level, never into void in towns or safe rooms |
| Falls | void → last safe spot, 5% HP | same; a level drop costs nothing |

### 1.7 Touch controls

The HUD layout and its buttons stay (`hud.gd`). What each button does:

| Control | Touch | Keyboard |
|---|---|---|
| Move | Left floating joystick, 8-way analog; ≤ 0.6 is tiptoe | WASD / arrows; Alt walks slowly |
| Jump | Jump button: jump up, double jump, glide (hold), fly (as today) | Space |
| Dodge / Guard | Tap to dodge (standing: back-step), hold to guard; hold after a dodge to sprint | K |
| Attack / Context | Attack auto-aims at the nearest foe in a 120° cone of the stick direction, else faces the stick; the context word (talk, gather, open, enter) as today | J / F |
| Techniques | Skill slots, aimed like Attack; a drag on a slot aims by hand | 1–8 |
| Doors | Walk into the doorway. The 0.3 s press-up hold goes away, because "up" is now a real direction | — |
| Interact reach | 40 units on the plane and ±24 in height, instead of an x-range | — |

---

## 2. What survives, what is adapted, what is replaced

### 2.1 Survives unchanged

- **Architecture:** data → state → rules → authorities → presentation, `Game.submit(intent)` and `GameEvents`
  (`docs/architecture.md`).
- **Authorities:** account, achievement, calendar, companion, crafting, economy, enemy (stats and loot), field, game,
  inventory, mail, pet, post, progression, quest, relations, sect, training sect, workshop. `world_authority` keeps
  its rules; only positions move.
- **Rules:** combat numbers, progression, loot, herb, field, pet, post, stat, calendar, technique tree and hazard
  timing (`scripts/simulation/rules/`).
- **Data:** items, techniques, realms, quests and dialogue, NPC definitions, enemies' stats, loot tables, recipes,
  zones, teleport stones, moments, the event contract and strings. All the `tools/data/` modules except world
  geometry.
- **The HUD** (`hud.gd`, its buttons, bars, tracker and toasts) **and every page** in `scripts/ui/pages/`.
- **Idle systems:** seclusion, Keeping Post, idle tasks, expeditions, offline caps.
- **Techniques data:** `techniques.json`, their `vfx` blocks and tiers.
- **Moments:** `MomentView`; world anchors are positions, which stay valid.
- **Save service, unlocks and audio.**
- **Room ids, portal ids, object ids and NPC ids.** Keeping every id keeps quests, direction marks, teleport stones,
  Paths Above rows and saves pointing at real things.

### 2.2 Adapted

| Part | Change |
|---|---|
| `scripts/world.gd` | Builds TileMapLayers from the room's tile data, the Y-sorted actor layer and the overhang layer instead of `Terrain` strips and `backdrop.gd`. Hosts the 640×360 world SubViewport |
| Room loader, `ZoneGeometry.configure` | New input: a `topdown` block (height grid, tile paint, overhangs) compiled into surfaces, blocks and faces. The existing `surfaces` / `blocks` / `climbables` / `volumes` / `movers` stay valid for hand-placed pieces |
| `MovementSolver` | New numbers (§1.6); auto-hop, tiptoe drop, long jump, acceleration; wall-sliding along any wall edge in 2D; Wall-Step off any face |
| `player.gd`, `ActorState` | `facing` becomes an 8-way direction (`Vector2i` / index 0–7). `facing_x` (±1) stays for mirroring and for old saves |
| Combat hit test (`combat_authority.gd:392` `hit_test`, `target_for`) | The x-range in the facing direction becomes a box or arc rotated to the facing vector; the depth band becomes its width; the altitude band stays |
| Traversal and nav graph (`ZoneGeometry.nav_graph`) | Nodes are compiled level regions; edges are walk, jump-up, hop, drop and climb, as today. Within a region, A* on the tile grid avoids props |
| Enemy and ally AI (`enemy_brain.gd`, `ally_brain.gd`) | Steering in 2D within a region; surround and flank slots around the player; kiting for archers; the "can't reach you" rule stays |
| `autopilot.gd` (auto-hunt, auto-path) | Path over the new graph; the room-to-room route is unchanged |
| `fx_layer.gd` | Direction-aware slashes, lunges and knockback streaks; ground decals drawn on the floor layer; shake and tint as today |
| Camera | §1.1 |
| Minimap (`hud.gd` `_draw_minimap`) | Draws the compiled level map (tops in level shades, faces dark, water, doors) instead of the strip. The world map page is unchanged |
| `world_labels.gd` | Names over heads, sorted with their actor; the rule to keep off HUD rects stays |
| Portals and doors (`portal_view.gd`, `room_travel.gd`) | Edge portals can sit on any room side (N/S/E/W); doors sit in building fronts on the south face; the arrival spot sits inside the edge |
| NPC, enemy and object views | 4/8-facing sprites; creatures 2-facing (E, mirrored) at first, 4-facing for bosses and humanoids later |
| Hazard and volume views | Volumes draw as floor decals and particle columns, not strips |
| Room data format (`tools/data/world.py`, `catalogue*.py`, `verticality.py`) | Builders emit the `topdown` block: `size` in tiles, `height` rows, `paint` terrain ids, `overhang`, plus surfaces for bridges. A one-off converter drafts each side-view room (x kept; the depth strip widened; tiers 88/100 → levels 1–2, 176/200 → 2–3, 300 → 4–5) for hand finishing |
| `room_lint.py` | Tiers become levels: two levels above ground in fields; a raised route; two ways up each required level; landings ≥ 3×2 tiles; reach with the band's arts; later ledges out of reach |
| `room_sweep` | Walks 2D routes between every door and interactable with the real solver, including hops and drops |
| Visibility tests (`visual_checks.gd`, `data_validation` overlap and door checks) | New checks: no interactable more than 50% covered by a higher-keyed face without an outline; every door visible from its approach |
| `tutorial_order`, `valley_run`, `prologue_run` | Run on intents, so they mostly survive; the scripted positions change |
| `AGENTS.md` wording | "both facings" becomes "every facing in the catalogue". The rules themselves stay |

### 2.3 Replaced

- **Side-view room art:**
  - backdrops (`art/backdrops/`, `backdrop.gd`, `tools/backdrops/`);
  - environment strips (`art/environment/`);
  - terrain and surface drawing (`terrain.gd`, `surface.gd`);
  - front-on props and buildings (`art/props/`, the `wuxia-*` atlases), redrawn top-down;
  - floor tiles (`art/tiles/`, 20 files), replaced by 16-px terrain tilesets.
- **Platform physics tuned for side view:**
  - `platform_landing.gd` and the `zone_layout.gd` building footprints;
  - the side-view tests `landing_matrix`, `upward_landing`, `platform_contact(_visual)`, `obstacle_review`,
    `movement_v07`, `movement_visual_v07` and `movement_review_v09`, replaced by a `topdown_movement` suite and a
    visual gallery.
- **The character and equipment sprite set.**
  - Every body, hair, shirt, trousers, shoe, hat, cape and weapon layer is redrawn for the new facings and poses.
  - `AGENTS.md` rule 4 applies: each movement is drawn first on the unclothed body and approved, then clothed.
  - The current sheets come from LPC-based bodies (`data/LPC-CREDITS.txt`) and may be used only as a size reference.
    The new set is original.
- **Creature sheets** (`art/creatures/`, 68 sheets), redrawn in top-down ¾ at the new scale. The `creature_art.json`
  contract keeps its rows and actions.

---

## 3. Systems that could live in the world (item 4)

Decision 36's study, `docs/redesign/systems_as_places.md`, extends this section to every page. It adds research, a
verdict per system, a set for the prototype and a phased list, for the user to decide.

Rule for every row: **the place opens the same page**. The pages stay the way the user likes them. The place adds a
reason to walk there, a sight in the world, and on-screen state. Remote access stays wherever the idle loop needs it,
so a phone player is never forced to travel.

Many systems already have an in-world object that opens their page (`world_authority.gd:572-631`): `garden_bed`,
`alchemy_furnace`, `forge_anvil`, `cooking_pot`, `formation_table`, `notice_board`, `storage_chest`,
`fishing_spot`, `teleport_stone`, `chart_table`, `shipyard_slip`. What changes is how much space and presence they
get.

| System (page) | In the world | Pros | Cons | Recommendation |
|---|---|---|---|---|
| **Garden** (`garden`) | Real beds in a home courtyard; each bed shows its crop stage and ripeness glow; tap a bed to open the page on that bed | The idle state is visible at a glance; top-down suits plots | 14 beds × growth art; the page still has to list them all | **Yes**: in-world state; page unchanged; remote tending after the first harvest |
| **Furnace, forge, cooking** (`alchemy` / `forge` / `cooking`) | Station props that animate while a craft runs (smoke, sparks, steam) | Shows work in progress; a hub feels alive | Craft queues are account-wide; a station must not lock them | **Yes**: animate from craft state; the Crafts menu entry stays remote |
| **Keeping Post** (`posts`) | A planted post marker (banner and basket) at each herb patch, ore vein or fishing spot where a character is posted, showing its stock | Idle gathering becomes visible where it happens; players find posts by walking | The Roll-Call is account-wide and its page is the real tool; markers in many rooms cost draw calls | **Yes, as markers**. The Roll-Call page stays the way to manage posts |
| **Notice board** (`notice_board`) | Boards in towns with one paper per open bounty or county job; the count shows from afar | Draws players to towns; readable demand | None new; boards exist | **Yes**: papers from quest state |
| **Shops** (`shop`, via dialogue) | Market stalls with their wares on the counter and the keeper behind | Towns read as markets; stock is visible | Wares art per shop | **Yes** for town shops; the dialogue → shop flow stays |
| **Stash** (`storage`) | Storage chests exist; add one in the home courtyard and each sect | Natural in top-down | Remote storage is a convenience players expect in idle games | **Place + remote**: remote through the Pouches page after its unlock |
| **Home courtyard** (new room) | A small personal hub for garden beds, a furnace, a stash, a meditation mat, a pet nest and a notice slate; it grows with realm and sect level | Gives every system a home without crowding towns; perfect for top-down | One more room kind to build and lint; sect grounds already "grow" | **Yes**: one room per character, built from the Sect Grounds' growing-room code |
| **Arena and Tower** (`beast_arena`, `tower`) | The Trial Tower already has a room (`sf_trial_tower`). Floors become real arena rooms with a gate you walk through; the Beast Arena gets a ring | Combat already happens in the world; top-down arenas read well | Floor transitions need care for sweep and replay | **Yes** for floors as rooms; the page stays for the ladder, sweeps and rewards |
| **Fishing** (`fishing`) | Face water tiles and cast; the bobber and bite happen on the water; the page shows the catch and the fish log | Top-down water makes casting natural | Touch timing must stay as forgiving as the current page's minigame | **Partial**: the cast and bite in the world, the minigame stays on its page at first |
| **Seclusion** (`seclusion`) | Meditation spots and Qi springs with visible Qi mist by density | Teaches "Qi-rich places" by sight | Seclusion is offline; it must stay available anywhere safe | **Place improves the rate** (already via `qi_density`); the page stays |
| **Mail** (`mail`) | A courier post in towns, with a red flag when there is unread mail | Flavour | Mail is a reward inbox; forcing travel adds friction | **Flag only**; the page stays in the menu |
| **Auction** (`auction`) | The auction hall at the Nine Peaks, with a podium and bidders | A set piece | Rare use | **Yes**, as a place with its page; no remote |
| **Chess, guqin** | Pavilions | Flavour | Little | Already sites (`chess` opens from a site); keep |
| **Spirit animals** (`spirit_animals`) | Pets follow in the world (they do); a nest in the home courtyard shows eggs and resting pets | Visible roster | Crowding | **Yes**, in the home courtyard |

Pages that stay page-only: character, cultivation, techniques, bag, quests, map, codex, relations, fates, settings,
characters. These are about the self, not about places.

---

## 4. Migration phases

Sizes are rough and relative: **S** is days, **M** is 1–3 weeks, **L** is 1–2 months, **XL** is several months. Art
counts are what the phase has to draw.

### Phase 1 · Prototype room and controller (M)

- A `--topdown` preview flag and one greybox room: a Lotus Ferry street redrawn as a height grid with three levels,
  stairs, a bridge you walk under, a ladder, water and two doors.
- Build:
  - the height-grid compiler into `ZoneGeometry`;
  - the new `MovementSolver` numbers, auto-hop, tiptoe, long jump and 8-way facing;
  - the 640×360 SubViewport, Y-sort, overhang fade, shadow and the new camera;
  - touch controls on the existing HUD.
- The greybox uses flat-colour tiles and a placeholder body.
- **Tests:** a new `topdown_movement` suite in `rules_tests`:
  - jump up one level but not two; the double jump reaches two;
  - auto-hop only at speed, tiptoe drops;
  - coyote time and the buffer;
  - sliding along walls and corners;
  - walking under the bridge;
  - sort keys for on-top, behind and in-front cases;
  - the compiler's edge types.
- **Gate:** the user plays the room on a phone and approves the feel before any art starts.

### As built: Phase 1 (2026-09-27)

**How to open it.** Run with `--topdown-proto` (preview saves), or on the title screen tap the version line five
times within three seconds. From the title the prototype runs on its own saves (`user://topdown_proto_saves/`) with
a stand-in character, so the player's own saves are never touched. Back opens the menu; the menu's exit leaves the
prototype for the title and restores the player's saves. The side-view game is unchanged: nothing loads the new code
unless one of these two entries is used.

**The room: Riverside Square** (`data/topdown/td_proto_square.json`, 48 × 30 tiles):

- a level-1 terrace with grass, a dirt path, a willow and two stone lanterns, backed by a level-3 rock cliff;
- a flight of stairs from the paved square up to the terrace; the terrace's edge is a ledge to jump down anywhere;
- a house on the square with a lane behind it that you walk along behind the house (the silhouette shows you);
- a low stone wall one level high and two tiles deep that you jump onto, then walk along;
- the river bank, and a pier with a one-tile gap (a running jump) and a three-tile gap to a landing stage
  (dash, then Jump);
- barrels, crates, a notice board, lanterns, reeds and a moored boat.

**What was built.**

| Piece | File | Notes |
|---|---|---|
| Room format and loader | `scripts/topdown/topdown_room.gd` (`TopdownRoom`) | `levels` rows (digit = level, `~` water), `paint` rows, `stairs` rects, `props` with footprints from the tile set. Answers the floor height at a point, the solid cells and the sort key |
| Controller | `scripts/topdown/topdown_motor.gd` (`TopdownMotor`) | Pure simulation at 120 Hz on (x, depth y, z). Numbers from `movement.json` `topdown` |
| View | `scripts/topdown/topdown_world.gd` (`TopdownWorld`) | The 640×360 SubViewport shown ×2, floor and water under one Y-sorted layer, the silhouette, shadow, dust and splash, the camera |
| Player | `scripts/topdown/topdown_player.gd` | The HUD's player interface (joystick, Jump, Dodge, Attack, keyboard) over the motor, and the placeholder body |
| Art | `tools/art/build_topdown_proto.py` → `art/topdown/*.png`, `data/topdown/proto_tileset.json` | Deterministic and original, in Jade River's palette, 1 art px = 1 viewport px, nearest neighbour |
| Shell | `scripts/main.gd`, `scripts/shell/shell_screens.gd`, `scripts/hud.gd` | The two entries; the HUD's Dodge calls the prototype's dash; its minimap is off in the prototype (it draws side-view rooms) |

**Differences from the plan as written.**

- **The room is Riverside Square, not a Lotus Ferry street.** It has two walkable levels plus the cliff, stairs, a
  ledge, two gaps, a wall to jump onto, a building to walk behind, water and props. It has no bridge to walk under, no
  ladder and no doors yet. The user asked for this room.
- **Drawn tiles, not flat greybox colours.** The user asked for a tile set.
- **The motor reads the height grid itself.** It looks up cells and does not compile the grid into `WalkSurface`s for
  `ZoneGeometry`. That compiler, and the nav graph built on it, move to Phase 2, where enemy navigation needs them.
  `MovementSolver` and every side-view room are untouched.
- **The Jump button only (decision 28).** There is no auto-hop. The long jump is Jump pressed during a dash or up to
  0.12 s after it. The tiptoe band (stick ≤ 0.6 walks at 45%) is kept. Walking off any open edge drops.
- **Water.** Water is level −1, drawn half a level (8 art px) under the ground, so a one-tile gap still shows water.
  A walk stops at the bank; only a jump goes over water. A landing in water sinks for 0.5 s and returns the body to
  the last spot where its whole foot box stood on one floor.
- **Drawing.** Custom draw nodes stand in for `TileMapLayer`s: water, then the ground floor, then one Y-sorted layer
  holding one node per raised row, one per flight of stairs, one per prop, the shadow, the body and its dust. Each
  node's y is its explicit sort key, a multiple of 1/64 art px, and the node draws back to its screen row, so the
  offset is exact. The viewport snaps transforms and vertices to whole pixels.
- **Sort keys.** A raised row keys at its south edge. A flight of stairs keys at the flight's south edge. A prop keys
  at its footprint's south edge + 0.5. A body keys at its ground y, raised to its floor's south edge + 0.25 when it
  stands on or above a raised floor. Ties go to the higher body.
- **Collision.** The foot box is 16 × 10 units. A corner blocks on a prop, the room's edge, water (while walking), or a
  floor above the reach: 8 on the ground, 12 in the air (the mantle). The move is axis-separated and halves its step
  into a wall. A corner clipped by up to 10 units is nudged round when the stick points along the move. In the air, a
  body left inside a higher floor (the back of the foot box as it walks off a ledge) is pushed out the shorter way.
- **Camera.** It follows the ground underfoot, never the jump arc, and follows a fall down once the body drops below
  that ground. The look-ahead is 0.2 × velocity. It settles in 0.3 s (95%), is clamped to the room and snapped to
  whole art px.
- **Not yet built:** the double jump and the other movement arts, sprint, the overhang fade (this room has no
  overhangs), the height assist, and the landing ring. The combat dodge still owns its own i-frames and cooldown; the
  prototype's dash only records its 0.15 s of i-frames.
- **Authorities.** The real HUD sits on the stand-in character (HP, realm, tracker, pages), but the prototype does
  not run `Game.tick`. There is no combat, AI or position sync (Phase 2). Attack only lights its ring.
- **The character is a placeholder.** `art/topdown/placeholder_body.png` has 32 × 48 cells, feet at (16, 46), about
  38 art px tall. It has S, E and N rows, with W mirroring E, and idle 2, walk 4, jump 3 and dash 2 frames. The
  manifest marks it `"placeholder": true`. The layered body, hair, clothing and weapon set follows `AGENTS.md` in
  Phase 5.

**Measured** (`rules_tests` `topdown_suite` prints them; world units, 1 art px = 2, 1 tile = 1 level = 32):

| Move | Number |
|---|---|
| Walk | 154.0 units/s (4.8 tiles/s), 8-way analog; the diagonal is as fast |
| Tiptoe | stick ≤ 0.6: 69.3 units/s (45%) |
| Start / stop | full speed in 0.083 s; stop in 0.067 s over 4.0 units (2 art px), in 120 Hz steps |
| Air control | 35% of the ground's; no input keeps the momentum |
| Jump | impulse 400, gravity 1700: apex 47.1 units (1.47 levels), airtime 0.475 s |
| Running jump | 73.2 units (2.3 tiles): a one-tile gap is easy; two tiles is the limit |
| Reach | one level up (32) lands; two (64) do not; step-up without a jump 8; mantle 12 |
| Coyote | 0.10 s: Jump 0.083 s after walking off a ledge still jumps; at 0.2 s it does not |
| Buffer | 0.12 s: Jump 0.10 s before landing jumps on landing; 0.20 s before is dropped |
| Dash | 96 units at 430 units/s (0.22 s); standing still it is a back-step of 46.6; i-frames 0.15 s; cooldown 2.5 s (`dodge.cooldown_s`) |
| Long jump | Dodge, then Jump within the dash or 0.12 s after it: 142.5 units (4.5 tiles) at 300 units/s |
| Landing | squash pose 0.1 s, dust by the fall height, the land sound from a 12-unit fall up |
| Facing | 8-way vector; the drawn row (S, E, N, W = mirrored E) changes when the stick is 20° nearer another row |
| Frame | perf runner: the room mounts in 142–149 ms and runs at 6.8–6.9 ms a frame (34 sorted nodes) |

**Tests.** `rules_tests` `topdown_suite` has 35 checks:

- walk, tiptoe and the diagonal; acceleration and stopping;
- the apex, the airtime and the running jump;
- one level but not two; the stairs, and their side as a wall;
- falls; coyote time and the buffer;
- faces, sliding along them, and corner nudges;
- props at every height; the bank, the gaps, the splash and the reset; the long jump; the dash and the back-step;
- sort keys (behind a row, on it, in front of it, in the air, behind and in front of the house) on the 1/64 grid;
- facing hysteresis;
- in the real view: the room's pieces, 640×360 ×2, the silhouette behind the house, order in front of it, whole
  pixels for the body, shadow and camera while the motor moves in fractions, and a still camera through a jump.

`perf_tests` `_topdown` holds the mount under 0.3 s and the frame under 16.6 ms.

**Screenshots** (`tools/dev/topdown_capture.tscn` under `xvfb-run`, in `docs/redesign/phase1/`):

- `01_square.png`: the square under the HUD;
- `02_behind_house_strip.png` and `02_behind_house.png`: walking behind the house;
- `03_gap_strip.png`: the pier's one-tile gap;
- `04_long_jump_strip.png`: dash, then Jump over three tiles;
- `05_upper_level_strip.png` and `05_on_the_low_wall.png`: onto the low wall, the shadow on the floor below in the
  air, then standing on top.

### Phase 2 · Combat, AI and interaction on the plane (M)

- Directional hit test and auto-aim cone, 2D knockback, enemy steering and flanking, the ally follow rule, context
  reach on the plane, and doors on any side.
- **Tests:**
  - `rules_tests` combat cases for arcs and boxes at 8 facings;
  - enemy nav across levels (it waits beneath targets it cannot reach);
  - `contract_tests` unchanged.

### As built: Phase 2 (2026-09-27)

**What it is.** The prototype room now fights. With a character, `TopdownWorld` enters Riverside Square through the
World authority (`enter_grid_room`): a `RoomRuntime` whose `topdown` is the height grid. From then on the room runs on
the same authorities as every side-view room: Combat (damage, Might, techniques, hit-stop, knockback, i-frames),
Enemies (spawns, respawn memory, the S13 states), World (loot, pickup). The body's step goes first, then `Game.tick`.
The side-view game is unchanged; nothing loads the grid code unless the prototype is opened.

**Decisions 29 and 30 applied first.**

- The dash cooldown stays 2.5 s. It is Combat's dodge now, carried by the motor's dash (`moves: false`).
- Walking stops at the water's edge. `TopdownMotor.water_walk` makes the water's surface a floor at the bank's height.
  It is off by default, and the player turns it on only for a character who knows the Water Skimming art.
- Roofs are floors. A prop with a `top` in the tile set is a raised floor that many levels over its ground: the house
  and a new storehouse at 2, the crates at 1. It is a wall from below and a surface on top. A body on it sorts over the
  building (its footprint's south edge + 0.75). Walking off its edge falls with the normal landing.
  - The rooftop route: the terrace (level 1) → a jump onto the storehouse roof (level 2) → across it → off its edge to
    the square (a 64-unit drop).
  - A second way up from the square: the crates (a jump, one level), then the roof (a jump, one more).

**What was built.**

| Piece | File | Notes |
|---|---|---|
| Aim rules | `scripts/topdown/topdown_aim.gd` (`TopdownAim`) | The one source for hits and previews: the height band, soft lock and snap, the four forms and their containment tests |
| Hit test on the plane | `CombatAuthority.hit_test` | A view with an `aim` runs the range along the aim and the depth across it. Its `band` replaces the altitude overlap: the target's feet within [−12, +12] of the attacker's, or [−56, +12] for a strike from the air. Without an aim it is the side view's test exactly |
| Combat on the plane | `combat_authority.gd` | `basic_attack` / `use_technique` take `aim`, `aimed` and `dist`. `_target_on_plane` does the soft lock or snap. `_form_targets` gives a technique's foes by form. Shots fly along the aim at the thrower's feet and stop at a face 24 over them (`_aim_shot`, `_shot_view`, `_shot_stops`). A knockback pushes away from the attacker on the plane (`away`, `EnemyState.knock_dir`), the player's through the motor. `hold_for_hitstop` freezes the view |
| Foes on the grid | `scripts/simulation/ai/topdown_brain.gd` (`TopdownBrain`) | EnemyBrain keeps the wind-up, blow, recovery and stagger, and hands idle, patrol, aggro, flee and return to the grid. The shared rules are factored out of EnemyBrain: `sight`, `notices`, `gives_up`, `wind_up`, `chase_speed`. The chase goes straight when the line is clear, else along `TopdownRoom.find_path` (A* on 8-way cells: walk, stairs, drops, and a hop one level up for a jumper). A foe with no way waits beneath, and after 6 s goes home healing. Sight reaches one level up or down |
| Foes in the room | `data/topdown/td_proto_square.json` `spawns` | Crabs on the square, rats on the terrace (jumpers), boarlets on the square. The room's `loadout` fills the stand-in's empty slots with one technique per form |
| Views | `topdown_world.gd` | The foes' **PLACEHOLDER** figures sort with the room (`FoeView`). An overlay at the HUD's resolution follows the camera and holds: the effects layer (`FxLayer`: the forms from `art/fx/`, turned to the aim), the foes' labels and HP bars (`EnemyView` in label mode, placed by `WorldLabels` round the HUD), loot, and the aim (`AimView`). Camera shake uses `ShakeRig` |
| Shared effects | `FxLayer.cast` / `FxLayer.hit`, `scripts/presentation/combat_fx.gd` (`CombatFx`), `shake_rig.gd` | The effects layer draws a cast and a hit for both views. `cast` takes the aim: its forms, slashes and shots turn to it, with the body's `chest` height. `CombatFx` is the view's glue round them (the Heaven-grade first-hit shake, the heavy-blow shake, the sound, Miss/Immune/Evade) |
| Art as data (decision 31) | `data/topdown/proto_tileset.json` | The view reads its atlases' files (`atlas`), every tile, prop, body and foe rect, and which tiles each paint mark draws (`paint`) from the manifest. The Phase 3 art replaces sheets and rows, not code |
| Touch | `scripts/topdown/aim_gesture.gd` (`AimGesture`), `hud.gd` | Attack and technique touches read as a tap or an aim (see below) |
| Art | `tools/art/build_topdown_proto.py` | The storehouse. A 2-frame strike pose on the placeholder body. `art/topdown/placeholder_foes.png`: crab, rat and boarlet, east drawn and west mirrored, with idle, walk, wind-up, attack and hurt. The manifest marks it `"placeholder": true`; the full art is Phase 3/5 |

**Aiming (decision 30; research in `docs/research/alabaster_dawn_2_5d.md` §3.8).**

- **Tap** (let go within 0.18 s, inside 18 px): attack or cast at the soft lock. That is the nearest foe in a 120° cone
  round the stick, else the facing, within 160 units, on a compatible height. A faint ring marks it in a fight.
- **Hold or drag:** the aim shows on the ground from the feet:
  - an arrow for a blow;
  - a line for thrust, volley, wave and every shot;
  - a 90° cone for sweep, arc, strike and flurry;
  - a circle at a point for burst, rain and pillar, placed by the drag's length up to the reach;
  - a circle round the caster for domain and ward.

  It snaps to a foe within 15° of the drag (a gold ring). Release fires along it.
- **Cancel:** drag out, then back onto the button (within 40 px).
- **Other rules:**
  - A tap now attacks on release in the top-down room, so a touch can become an aim.
  - The side view is unchanged.
  - It works left-handed (the direction is read from the button's own centre), and nothing animates under Reduce
    motion.
  - No button was added, and nothing is drawn in the HUD's clear zone (the aim draws in the world).
- **Drag zones on Attack** were a proposal here:
  - a drag past 120 px = the combo's finisher step at once;
  - a drag down (toward the camera) in the air = Plunge;
  - a hold without a drag = guard / the stance technique.

  The user took it as decision 35; it is built (see "As built: Attack's drag moves" below).

**Measured.** From `rules_tests` `topdown_suite`, which prints them, and `perf_tests` `_topdown`:

| What | Number |
|---|---|
| Aimed blows | land in 8 of 8 directions, never behind; a tap turns to the nearest foe in the cone |
| Heights | a swing misses a foe a level up; a jump strike (z ≥ 20) hits it; a foe a level up cannot strike down |
| Shots | fly along the aim on the plane; a face one level up stops them |
| Knockback | about 50 units away from the attacker along the plane (60 knockback); hit-stop 0.05 s holds the fight |
| Roof | a jump from the terrace lands on the roof at z 64; walking off drops 64 to the square |
| Foes | a boarlet closes 150 → under 110 units in 1 s; past the 600 leash it goes home; under a roof it waits, then goes home at 6 s; a rat hops one level up to the terrace |
| Frame | perf runner, on a shared machine (load about 15 on 4 cores): the room mounts in 161–272 ms and walks at 6.9–7.3 ms a frame. With 22 foes fighting (15 added round the player, plus the room's 7), blows every 20 frames and a technique every 45 (up to 44 effects at once), a frame takes 7.8–13.5 ms against the 16.6 ms budget (10.1 ms in the final run) |

**Tests.** `rules_tests` `topdown_suite` has 35 Phase 1 checks and 27 new ones (62 in all):

- water and the Water Skimming gate;
- the roof from the terrace and from the crates, and the drop off it;
- the height band;
- aim shapes per form;
- tap / hold / drag / cancel / left-handed gestures;
- the room on the authorities, the loadout, the foes' views;
- the eight directions and the soft lock;
- heights for blows and for foes;
- shots along the plane and stopped by a face;
- the point circle;
- knockback on the plane and hit-stop;
- the dodge's i-frames and cooldown;
- the chase, the leash, waiting beneath a roof, a rat's hop;
- drops on the terrace and the equip popup;
- the HUD's aimed attack with its snap, an unsnapped drag, each technique's form and its cancel;
- the fight/rest ring.

**Screenshots** (`tools/dev/topdown_capture.tscn -- --phase2`, in `docs/redesign/phase2/`):

- `01_fight_three_foes.png`;
- `02_technique_strip.png` (a line: the rolling wave) and `02_technique.png` (a burst at its point);
- `03_rooftop_jump_strip.png`;
- `04_water_edge_strip.png`;
- `05_aimed_attack.png`;
- `06_aimed_technique.png`.

**Not yet built:**

- doors on any side;
- the ally follow rule;
- context reach on the plane;
- flanking slots;
- creature art in 4 facings;
- a knockback that avoids void in safe rooms (the prototype has no void);
- the position sync to saves (Phase 7).

### As built: Attack's drag moves (decision 35, 2026-09-28)

**What it is.** Three more moves on the Attack button in the top-down room, on top of the tap and the aimed drag,
which stay as built. Each uses rules the game already has. Numbers are in `data/movement.json` `topdown.aim`
(built by `tools/data/stats.py`).

| Move | The thumb | What it does | Rules it uses |
|---|---|---|---|
| **Finisher** | A drag past the finisher's line, then let go | The combo's last step at once, along the drag (it snaps as an aim does). Mid-chain it comes when the step under way ends, in place of the steps between. On the ground only: an air blow has no chain (S43) | The family's `combo` step: its multiplier, hit frame and duration |
| **Plunge** | In the air, a drag down (toward the camera) within 35° of straight down and past 48 px, then let go | The body drops straight down at 900, with no steering. The landing strikes for 120% within 60 and stuns for 0.5 s (not bosses), with a ring, dust and a jolt | The Plunge art (the `plunge` secret art, Bone Forging 4), its 4 s cooldown, `CombatAuthority._resolve_plunge` |
| **Guard** | Held still for 0.3 s (never leaving the 18 px dead circle) | The guard while the thumb stays down; letting go ends it and strikes nothing. With a counter-stance technique slotted and ready (`hold_stance`), the hold casts it instead | The family's `guard` cut (fists 30%) and `parry_s` window (0.15–0.25 s after the guard starts: a frontal blow in it is parried and staggers the foe); a stance's 2 s window turns a parry into a 200% counter |

**Where the lines sit.**

- **The finisher's line** is 120 px from the button's centre, as proposed. On the right-handed layout the button is
  115 px from the right and bottom edges, so a 120 px line would be out of reach there. Near an edge the line is
  pulled in so the band from it to the edge stays 48 px deep (`zone_px`): 67 px toward the right and the bottom. It
  never comes nearer than 66 px (the 18 px dead circle + 48), so the aimed drag keeps a 48 px band too. The
  left-handed layout mirrors it.
- **The Plunge's sector** is 55 px wide where it starts (48 px out) and 67 px deep to the bottom edge.
- **The guard's hold** is 0.3 s. The aim's preview still starts at 0.18 s, so a player can press, pause and still drag
  to aim. The Dodge/Guard button's hold (0.18 s) is unchanged and stays the quicker guard for parries.

**What shows.**

| Move armed | On the button | On the ground |
|---|---|---|
| Finisher | The finisher's line round the button (faint while aiming), lit gold once the drag crosses it; "Finisher" over the button | The aim's arrow turns gold and heavier, with the step's sweep at its head |
| Plunge | In the air, when the body can plunge, the sector under the button (faint), lit gold with a down chevron when the drag is in it; "Plunge" | The landing ring (60) on the floor straight under the body, joined to it by a dashed drop line |
| Guard | While held still, a jade ring fills toward the guard; guarding, the button is ringed jade (gold for a stance); "Guard" or "Stance" | A half ring at the feet on the guarded side, jade (gold in a stance), heavier while the parry window is open. It also shows for a guard held on the Dodge button |

- Under Reduce motion nothing pulses: the armed marks hold still.
- The words sit in the gap between the Attack ring and ring 1, outside the HUD's clear zone.
- The moves are live only while the button attacks: in a fight, or with nothing to talk to or gather at hand. While
  the button offers a context at rest, or during a harvest tap or a channel, a hold lets go as a tap.

**Poses.** The real character (Phase 3, third part) draws both moves:

- the guard, 2 frames held while guarding;
- the Plunge's tuck and dive while it drops;
- its impact frame, held for 0.25 s after it lands.

**Where it lives.**

- `AimGesture.move` reads the thumb, and `holding` says when a hold asks for the guard.
- `hud.gd` has `armed`, `_tick_hold`, `_release_aim` and `_draw_attack_moves`.
- `topdown_player.gd` has `finisher`, `plunge` / `plunge_ready`, `hold_guard` / `release_guard`, the plunge's impact
  and the poses.
- `TopdownMotor.plunge` drops the body.
- `CombatAuthority.basic_attack(…, finisher)` and its queue (`finisher_q`).
- `TopdownWorld` draws the ground marks and the impact.

The side view is unchanged.

**Measured** (`topdown_suite` prints them):

| What | Number |
|---|---|
| The finisher's line | 120 px up and left; 67 px right and down (right-handed; mirrored left-handed) |
| Every drag zone | at least 48 px deep in all 72 directions tested, both layouts |
| A finisher's pace | at most 5.1% more damage a second than its whole chain (the bell; the check allows 6%). Most families are at or under the chain's |
| Plunge | from 38–41 units up it lands in 2–3 frames (0.05 s) at 900 |
| Guard | a blow inside the parry window is parried and staggers the foe. After the window, a landed blow costs 0.70 of an open one: fists' 30% cut, measured over eight blows each way from a boarlet of the character's level, with its crits off |

**Tests.** `topdown_suite` goes from 62 to 75 checks:

- the zones on both layouts; each drag's reading; the hold, a drift, a refused guard;
- the motor's Plunge; the finisher's pace for every family;
- through the HUD in the room:
  - a finisher at once, and one queued mid-chain (steps 0 → 2);
  - a Plunge that lands, strikes and stuns, with its cooldown and the fallback poses;
  - a drag down without the art, which stays an air blow;
  - the guard: its parry, its cut, and its end;
  - the stance (Silkworm Riposte);
  - the figure's guard pose;
  - left-handed, a finisher and a cancel;
  - Reduce motion.

`rules_tests` runs `run_fight` again. A merge had dropped the call, so Phase 2's fight checks had not run since.

**Screenshots** (`tools/dev/topdown_capture.tscn -- --drag-moves`, in `docs/redesign/drag_moves/`):

- `01_finisher_armed.png`;
- `02_plunge_armed.png`;
- `03_plunge_impact.png`;
- `04_guard.png`.

**Not built.**

- The keyboard keeps J (tap) and K (hold to guard); no finisher or Plunge keys.
- The flute's held melody (S47) is still not on the top-down Attack button; the hold guards.

### Phase 3 · The art pipeline (L)

- `docs/art-contracts.md` v2 fixes the rules: the 16-px tile, the ¾ view, faces, overhangs, the character cell,
  facings and palette-swap dyes.
- Build:
  - tile generators in `tools/art/` (terrain sets for earth, grass, stone, wood, sand, snow; cliff faces; water
    edges);
  - a prop kit for the first region;
  - the unclothed body in S, E and N for the whole catalogue;
  - the attachment rig for weapons and hats.
- The compatibility gallery (`tests/animation_gallery`) shows every facing.
- **Tests:**
  - `Validate-Animations.ps1` and `animation_contract_tests.ps1` extended to facings and `hidden` entries;
  - a palette-swap check (every dye id has a palette row).
- **Gate:** the user approves the body and one outfit in all three facings before any other layer is drawn
  (`AGENTS.md` rule 4).

### As built: Phase 3, first part · art direction and the prototype terrain (2026-09-27)

- **The rules** are in `docs/redesign/art_bible.md` (decision 31). They cover:
  - the palette ramps and the value plan;
  - the light, the outlines, and the grid and scale;
  - the six height cues on every raised edge;
  - the auto-tile schemes, props, animation, and the xianxia motifs.
- **The build** is `tools/art/topdown/build_tiles.py`: deterministic, and `--check` proves it. It writes:
  - the atlas, the prop kit and the manifest (schema 2) that the room view reads, keeping every name, footprint, prop
    top and the Phase 2 schema;
  - a Godot TileSet, `art/topdown/proto_tiles.tres`, for the Phase 4 `TileMapLayer`s: paths match corners, the shore
    matches sides, the water animates.
- **`compose.py`** is the reference renderer of the rules. It renders the review images in `docs/redesign/phase3/`.
- **What waits.** The room view draws the new tops, faces, water and props. The path and shore auto-tiles, rims,
  contact shade and prop shadows wait for a loader patch after Phase 2, or for the Phase 4 move to `TileMapLayer`s.
- **Not started then:** the body in S/E/N, the weapon and hat rig, and the gallery by facing. The third part below
  builds them.

### As built: Phase 3, second part · the terrain in the game, the square redesigned, the first foes (2026-09-28)

Decisions 32–34: the art is approved, the mock's auto-tiles, rims and prop shadows go into the game now and the room
is adjusted to them, and the room gets its bamboo, lotus pond and lanterns.

**The terrain in the game.** `TopdownTerrain` (`scripts/topdown/topdown_terrain.gd`) holds the art bible's rules; the
room view (`topdown_world.gd`) draws what they pick. Phase 2's combat and collision are untouched.

| Rule | In the game |
|---|---|
| Path and paving auto-tiles | a path cell's corner is grass when grass on its own level touches it; the cell takes its corner-matched tile. Every top variant is drawn |
| Shore | each water cell takes its side-matched case (land N, E, S, W) in the water's four frames |
| Raised edges | rims where a neighbour drops away, contact shade at a face's foot, the cast shade of a higher west neighbour, a face's lit west end and shaded east end, the stairs' cheeks: all overlay tiles from the atlas, replacing the view's own 1 px rim |
| Prop shadows | a sprite of each prop's shadow in the prop sheet, cut to the cells of the level the prop stands on, so each floor draws its own piece and a body in it is never tinted |
| Plants | bamboo and willow sway, lotus bob, each at its own phase |

The paint table says what each mark takes part in (`grass`, `under`, `keep_face`, `face_below`; art bible §6). The
blob shadow is one function for the body, the foes and the review's stand-ins.

**Riverside Square redesigned** (`data/topdown/td_proto_square.json`):

- **The terrace.** A dirt path runs from the stairs' head east along the terrace to the edge above the storehouse (the
  rooftop route's jump), with a branch up to a shrine at the cliff's foot: an incense burner between two stone
  lanterns. Two rock outcrops step the cliff, with bamboo groves before them and a willow in the west.
- **The square.** Paving leads from the house door (between two red lantern posts), the storehouse door and the
  stairs' foot to the pier, between lawns that grass creeps over. A lotus pond with a granite curb lies in front of the
  house, a willow over it. The low wall is now a planted bed (a level up, stone faces, flowers, a shrub).
- **The river.** The promenade has a notch where the boat is moored. Grassy banks close both ends. Red lantern posts
  and stone lanterns stand at the pier's head.
- **Kept:** the storehouse and crates of the rooftop route, the house and its lane, the stairs, the pier's one-tile gap
  and the landing stages' three-tile gap, the spawn, the foes' spawn points (one crab moved two tiles west, off the pond's
  curb).
- **No expected number in `topdown_suite` changed**: every Phase 1–2 check passes on the new layout as written.

**The first foes** (`tools/art/topdown/creatures.py` → `art/topdown/foes.png`, art bible §8 "Foes"): the mud crab,
reed rat and boarlet, recognisably their side-view selves. Five facings are drawn (S, SE, E, NE, N); SW, W and NW
mirror. Each has idle 4, walk 4, wind-up 2, strike 3 (the hit on frame 1), hurt 2 and death 4. The placeholder foes and
their sheet are gone. `FoeView` faces a foe where it walks, else where it aims, with 12° of hysteresis (the motor's
row picking, shared), plays each action at its own rate, and holds a strike, a flinch and a death on their last frame.
The pebble imps are not drawn: they do not appear in the prototype room.

**The build and the review images.** `build_tiles.py --check` stays byte-identical over the tiles, props, foes,
TileSet and manifest. The Python reference renderer (`compose.py`) is gone: the game draws the rules now, so the room's
review images come from the game (`tools/dev/topdown_capture.tscn -- --phase3`), including the height-levels test on a
review room of its own (`data/topdown/td_review_heights.json`). The files are listed in the art bible's §12.

**Tests.**

- `rules_tests` `topdown_suite`: 8 new checks.
  - The terrain rules on a small room: corners from the same level only, shore cases, rims and shades, face kinds
    over water and face ends, and shadows cut to their level.
  - The square's routes: paved from both doors and the stairs to the pier; dirt from the stairs' head to the
    rooftop jump and the shrine.
  - The pond, bamboo, lotus and red lanterns; the view's shore cells and swaying plants.
  - The foes' eight facings, the mirrored rows and the held death.
- `data_validation` `topdown_art_suite`: prop frames and shadows lie inside their sheet, and every foe the room spawns
  has all six actions in five facings.

**Measured** (`perf_tests`): the room mounts in 104 ms and walks at 6.9 ms a frame, with 74 sorted nodes. With 22
foes fighting, a frame takes 9.1 ms.

### As built: Phase 3, third part · the real character (decision 32, 2026-09-28)

**What it is.** The prototype's body is now the game's own character, redrawn for the ¾ view. It keeps the side
view's big-headed build, faces, hair styles, clothes, colours, dyes and weapons, and reads them from the same data:
the names, dyes and hair colours in `data/parts.json`, and the outfit in the save. It replaces the placeholder body.
The villagers are drawn the same way.

**How it is drawn.** The build is `python3 tools/art/topdown/build_character.py [--only <set>] [--check] [--review]
[--list]`. It is deterministic, and `--check` builds twice and compares every byte.

- **A posed doll.** `tools/art/topdown/figure/` holds a small 3D doll:
  - a skeleton posed per frame in the figure's own frame (forward, right, up), with two-bone IK for the arms and legs;
  - solids (spheres, ellipsoids, tapered cones) ray-cast at 1 art px per pixel through an orthographic camera 22°
    above the ground;
  - 0.92 art px per unit, so the body is about 38 art px from sole to crown, 40 with a top knot.
- **Shading.** Each pixel takes a step of its material's five-step ramp from N·L against the upper-left light. The
  deepest step is kept for contact shade, under a nearer part. Orphan pixels are cleaned up.
- **Outlines.** 1 px, as the art bible's §4 sets: ink-teal `0E1A1E` on the shaded side and `26363A` on the lit side.
  Where an edge falls over the figure itself, it takes the material's own deep tone instead. A cut's smear has no ink.
- **One pose for every layer.** Every layer is cast from the same pose of the unclothed body, so each one stays
  registered to the body in every frame (`AGENTS.md` rules 1–4). The body is drawn first; clothes, hair and weapons
  go over it.

**Facings.** S, SE, E, NE and N are drawn; SW, W and NW mirror SE, E and NE. The motor picks one of the eight rows,
changing row only when the stick is 10° nearer another (§1.4 asked for 20° with four rows).

- The side and back-diagonal rows are turned a little toward the camera, as ¾ sprites are: E faces 14° south of
  east, NE 36° north of east, SE 48° south of east. In E the head turns a further 22°, so the face shows in three
  quarters, as on the side-view sprite.
- **What does not mirror cleanly.** In the west facings the crossed collar (left over right) and the weapon hand
  (right) swap sides, and the light comes from the upper right. The side view's left row mirrors its right the same
  way.
- **Depth.** A weapon pointed at the camera or away from it is drawn 1.6 times longer along the ground's depth than
  the doll's camera would show it. The world's own view keeps the ground's depth at full length, so a thrust to the
  south still reads as a reach.

**Bands and layer order.** Each item is cut into up to four sections by depth:

- back: behind the chest (the far arm, a tail behind the neck, a blade behind the back);
- mid: the trunk, legs and clothes;
- head: the body's head and neck, over the shirt's collar and under the hair;
- front: in front of the chest.

A section's z is its band's base (0, 100, 150, 200) plus the side view's category order: body 10, shoes 20,
trousers 30, shirt 40, hair 60, hat 65, weapon 70. An arm, a tail or a blade changes band as the pose moves it.

**The action catalogue** (`data/topdown/character.json` `actions`; frames per facing, 494 frames in all):

| Action | Frames | fps | Loop | Hit | Notes |
|---|---|---|---|---|---|
| idle | 4 | 4 | yes | | breathing; the weapon held low |
| walk | 8 | 10 | yes | | plays faster or slower with the speed |
| run | 8 | 14 | yes | | above 1.15 × the walk speed |
| jump | 5 | 10 | no | | takeoff, rise, apex, fall, land; the player picks the frame from the vertical speed |
| dash | 4 | 16 | no | | |
| dodge | 4 | 14 | no | | the back-step (a dash away from the facing) |
| hurt | 2 | 10 | no | | while Combat's flinch lasts |
| knockdown | 5 | 10 | no | | falls back and to its side; held on the last frame while wounded |
| punch_1–3 | 5 | 14, 13, 11 | no | 2 | lead jab, rear cross, rising uppercut (fists, gauntlets) |
| swing_1–3 | 6 | 14, 13, 11 | no | 2, 2, 3 | rising cut, return cut, heavy descending cut (jian); a smear of jade light on the hit frame and the next |
| thrust_1–3 | 5 | 14, 13, 11 | no | 2 | straight, low and high lunging thrust (spear, short blade) |
| cast | 5 | 12 | no | 2 | the hand seal, then both palms out |
| guard | 2 | 4 | yes | | held (decision 35's hold, and the Dodge button's) |
| plunge | 3 | 12 | no | 2 | tuck, dive, impact (decision 35's drag down) |
| meditate | 4 | 3 | yes | | faces S only; the other seven facings redirect to S |

- **Blows on Combat's clock.** A blow plays its own action, with its hit frame shown the moment the hit lands
  (`TopdownFigure.strike_frame`).
- **Techniques.** A technique plays its own pose. One with no pose of its own (or `meditate_burst`) plays the cast.
- **Aliases.** Side-view names still in the data are explicit redirects: `attack` → thrust_1, `swing` → swing_1,
  `punch` → punch_2, `bow` → cast, `meditate_burst` → cast.

**Layers drawn.** Every item below is drawn in every action and facing:

| Category | Items | Variants |
|---|---|---|
| body | light (the creator's one skin tone) | 1 |
| hair | the creator's six styles: short_knot, topknot, ponytail, high_pony, long_tied, flowing | the six hair colours |
| shirt | disciple (the start), vneck, cardigan, scholar, sleeveless | undyed and the ten dyes |
| pants | loose (the start), straight, cuffed, scholar, martial | undyed and the ten dyes |
| shoes | slippers (the start), boots, folded | 1 |
| hat | straw, headband, tied, guan, weimao | 1 |
| cape | solid, tattered | 1 |
| weapon | gauntlets (the starting training gauntlets), dagger (short blade), sword (jian), spear, staff | 1 |

- **Weapons outside their family's actions.** The jian thrusts, the spear swings, the gauntlets strike in every
  pose. The spear runs through both hands wherever the pose holds it two-handed. A meditating figure lays its weapon
  on the ground beside it.
- **Absent layers are explicit.** A section with nothing to draw in an action and facing has a `hidden` entry with
  its reason (for example, the body's back section when both arms are level with the chest). A frame with nothing
  to draw is an empty rect.

**Sheets.** Each item and dye or hair colour has one sheet: `art/topdown/character/<cat>_<item>[__<variant>].png`.

- Every frame of every section is trimmed and shelf-packed 512 px wide, and identical frames share a rect.
- Dyes and hair colours are baked sheets, as in the side view. All the variants of an item share one rect table.
- There are 162 sheets, about 7 MB. A figure in the starting outfit loads about 3 MB of textures.

**Layer sets (decision 37: the full set, drawn by agents in parallel).** The character is drawn in layer sets, each
built on its own into its own files. `docs/redesign/phase3/character/HOWTO.md` says how to add one.

- **A set** (`tools/art/topdown/figure/sets/<set>.py`) holds its looks as specs (a few numbers each) and colours:
  `body`, `hair`, `shirt`, `pants`, `shoes`, `hat`, `cape`, and one per weapon family (`weapon_gauntlets`,
  `weapon_short_blade`, `weapon_jian`, `weapon_spear`, `weapon_staff`).
- **A generator per layer kind** (`figure/kinds/`) casts a spec: `torso`, `legs`, `feet`, `head`, `back`, `hands`,
  `hair`, `blade` and `pole`. A family with a shape of its own gets its own generator.
- **The files.**
  - `--only <set>` builds one set in about ten seconds. It writes that set's manifest,
    `data/topdown/character/<set>.json`, and its sheets.
  - It also writes the index, `data/topdown/character.json`: the actions, facings, bands, dyes and hair colours, and
    a `catalog` signature of the action catalogue. Every set's build writes the same bytes there.
  - `TopdownFigure.manifest()` merges every set built for the index's catalogue. A stale set, built for another
    catalogue, is left out, and the contract names it. A new action therefore rebuilds every set, in a batch of its own.
- **Coverage.** Each item lists the game items that wear its look (`artifacts`), a manifest of which item ids have
  top-down layers. `data_validation` computes what the game's data can put on a character:
  - the creator's options;
  - every wearable in `data/artifacts.json`;
  - every NPC's outfit;
  - every weapon family's looks;
  - every action a family's combo or a technique plays, where a stand-in alias (`stand_ins`) counts as missing.

  Until `FULL_SET` is on (`figure/sets/__init__.py`), what is missing must be listed in `PENDING`. After that nothing
  may be missing. It prints the coverage on every run: 45 of 52 looks and actions today.
- **Villagers load their sheets on threads** (`TopdownFigure.wearing(o, true)`). A room full of new outfits enters
  without a hitch, and each villager appears once all its sheets are in.

**In the game.**

- `TopdownFigure` (`scripts/topdown/topdown_figure.gd`) composites the sections by z. For each section and frame it
  draws one rect `[x, y, w, h, ox, oy]`, where `(ox, oy)` is the offset from the feet; the west facings draw flipped.
- **The player** wears `InventoryAuthority.outfit_for` its character: the equipment and dyes from the save. It
  dresses again on `equipment_changed`.
- **The player's state picks the action:** wounded → knockdown; the Plunge → plunge, and its impact frame after
  landing; a blow or technique under way → its pose; hurt; the dash or back-step; in the air → jump; guarding →
  guard; landing → jump's last frame; meditating → meditate; moving → walk or run; else idle.
- **Villagers.** `TopdownFigure.for_npc` dresses an NPC in its own outfit, with unset pieces filled as the side
  view fills them. `TopdownPlaces.Person` draws them in every room on the grid (Phase 4's people), and
  `TopdownWorld.add_villager` stands one anywhere, for the prototype and the reviews:
  - at rest in the pose the room gives them (idle, or meditate), three-quarters toward the camera on the side the side
    view faces them (SE or SW), or in the row `add_villager` names;
  - turned to the player in the eight rows while the player is at their side (the context's focus: a talk, a gift, a
    shop), and back to their rest after;
  - walking the way a route moves them (the rooftop thief's chase).
- **What is not drawn is listed.** An outfit piece with no top-down layer goes in `TopdownFigure.missing`, and the
  figure draws without it.
- **Fading as one.** The i-frames' blink and the occlusion silhouette fade the figure as one image (a `CanvasGroup`).
  Faded layer by layer, the clothes would show the body through them.
- **The placeholder body is gone**, with its sheet and the tileset manifest's `body` entry. `build_topdown_proto.py`
  only runs `build_tiles.py` now. The game's review images (`topdown_capture.tscn -- --phase3`, the height test
  among them) draw the real character.

**What still needs top-down layers.** All nine villagers of the tutorial (Lotus Ferry) are fully drawn: aunt_ping,
lu_boatman, little_dou, old_ma, granny_liu, shen_lian_npc, uncle_guo, fisher_wen and washer_mei. So are 124 of the
125 NPCs, every creator option, and every garment, hat and cape look in the game's items. What is left is four
independent batches (HOWTO.md), 62 game items in all:

- **heavy_sabre:** the sabre, 10 items.
- **fan_and_brush:** the fan and the brush, 21 items.
- **flute_and_bell:** the flute and the bell, 21 items.
- **bow:** the bow, 10 items, and qiu_feng's. The bow's draw and release poses are still a stand-in alias to the
  cast, played by the bow family and 253 techniques. This batch changes the action catalogue, so it runs first or
  last and rebuilds every set.

A piece with no top-down layer goes in `TopdownFigure.missing`, and the figure draws without it.

**Tests.**

- **`data_validation` `topdown_character_suite`** holds the layer contract, as `Validate-Animations.ps1` does for the
  side view:
  - every action is in every item's sections in every drawn facing, or hidden with a reason;
  - a facing-locked action redirects every other facing;
  - each family has three distinct one-shot combo stages;
  - every dye and hair colour has its sheet;
  - every rect lies inside its sheet;
  - the names come from `parts.json`;
  - the early families' combos and every technique's pose play drawn actions;
  - the creator's looks and the early drops are drawn;
  - the hats and capes are held to the same contract.

  Like `animation_contract_tests.ps1`, it then shows the gate refusing eleven broken manifests, a stale set among
  them. `topdown_coverage` is the full set's gate (above).
- **`topdown_suite` `_figure`:**
  - the figure wears the save's outfit, and dresses again when the jian is equipped;
  - each state plays its action: idle, walk, the blow's own pose with its hit frame, the cast, the back-step, the
    knock-down, the jump;
  - all eight rows draw, and the west mirrors the east.

  The drag-move checks now use the figure's guard and plunge poses.
- **`tests/topdown_figure_gallery.tscn`** renders the compatibility gallery (it needs a renderer). There is one sheet
  per item and dye or hair colour, with every action in all eight facings, drawn by the game's own compositor over
  the starting outfit.

**Review sheets** (`docs/redesign/phase3/character/`, from `--review` and `tools/dev/topdown_capture.tscn --
--character`):

- `01_body.png`: the unclothed body;
- `02_outfit_<facing>.png`: the starting outfit, one sheet per facing;
- `03_weapon_<name>.png`: each weapon;
- `04_hair.png`: the hair styles;
- `05_dyes.png`: the dyes;
- `06_villagers.png`: the tutorial's villagers;
- `09_wardrobe.png`: every garment, hat and cape;
- `07_ingame_square.png` and its strips: in Riverside Square in the game;
- `08_mirrored.png`: the eight facings.

**Not built.**

- Palette-swap dyes (§1.4). Dyes are baked sheets, as in the side view.
- Thrust streaks. A thrust at the camera relies on the effects layer's line.

### Phase 4 · Room conversion by region (XL)

- The converter drafts every room, then each is finished by hand, one region at a time:
  1. Prologue and Lotus Ferry;
  2. Willow Path, Stoneford and the sects;
  3. the rest of Act I;
  4. Act II;
  5. Act III.
- Each region ships its tileset variant and props.
- `room_lint.py` gets its level rules; `room_sweep` gets 2D walking; `data_validation`'s reachability and overlap
  checks and the new visibility check run per region.
- **Tests:** per region:
  - lint green;
  - sweep green;
  - `tutorial_order` green (Prologue region);
  - `valley_run` sections for the region green;
  - `perf_tests`: room load < 0.3 s, a frame with fifteen foes at 60 fps.

### As built: Phase 4, first part · the real game on the grid, the tutorial rooms (2026-09-28)

Decision 36: the full game logic runs in the top-down world first. It is no longer a sandbox. A character made for
the top-down world plays the real game (its save, its quests, every authority) in every room that has a layout on
the height grid. The rooms without one stay side-view, and the view changes under the same HUD at the door between
them. The side-view game is unchanged for every side-view character.

**How to play it.**

- **The title screen's hidden entry** (five taps on the version line within three seconds) opens the top-down game on
  saves of its own (`user://topdown_saves/`). The player's saves are saved, set aside and restored on leaving it. The
  first time it makes a new character and starts the Prologue in the Fisher's Hut. After that it continues where the
  character was saved.
- **Settings → Controls → "Top-down world (new games)"** (off by default). While it is on, the next character made
  in the player's own saves is a top-down one.
- **Command-line flags.** `--topdown` makes a preview's characters top-down, and `--topdown-tutorial` opens the
  top-down game on the preview saves. `--topdown-proto` still opens Riverside Square, the Phase 1–2 prototype.

**One game, two views.**

| Piece | File | What it does |
|---|---|---|
| The character's view | `GameCharacter.view`, `AccountAuthority.create_character` | `"topdown"` for a character made for it (the create intent's `view`, or the Settings toggle). A new top-down character wakes at its first room's own spawn |
| Rooms on the grid | `WorldAuthority.grid_for`, `_runtime`, `load_room` | A top-down character enters a room with a layout as a `RoomRuntime` on the grid. The arrival is the portal's `arrive` cell, or a saved or shrine spot moved to the nearest floor (`TopdownRoom.nearest_standable`). A teleport lands in front of its stone. The spot is kept every tick and saved, as in the side view. The prototype square still keeps no spot |
| A room's definition | `TopdownRoom.merge_def` | Keeps every id and rule of the side-view room: NPCs, objects, portals and their requirements, spawns, events. From the layout it takes only the places: objects (their `alt` is the floor there), portals (`at`, `dir`, `arrive`, `radius_scale` from `span`), spawn points, the room event's cells and a thief's route. The strip's own keys (surfaces, scenery, backdrop camera…) are dropped. A stand-in ground over the whole room (`geometry_def`) answers every rule that asks the side view's geometry |
| Layouts | `tools/data/topdown_rooms.py` → `data/topdown/<room>.json` | A small drawing language (levels, paint, walls, stairs, props, doors and the paths to them). Every layout is checked as it is built: everything of its room is placed on a floor and reached on foot from every way in and from its spawn (walking, stairs, drops, a jump a level up, a running jump over a tile). `--check` proves the files are current, and `tools/run_tests.sh` runs it |
| The view | `TopdownWorld.live` | Main mounts it for a room on the grid and swaps it with `world.gd` when a room of the other kind is entered (`main._swap_world_view`), keeping the HUD, the pages and moments. On each room entered it rebuilds the floor, rows, stairs, props, foes and loot, and places the body where the World authority put it |
| People, things, ways | `TopdownPlaces` | Each person and thing is drawn twice. In the pixel viewport, sorted with the room (`Figure`): the villager in the top-down style (`Person`, Phase 3's third part), or the object's prop in `ObjectView`'s new "art" mode, the side view's own art at half size (2 world units per art px). On the overlay at the HUD's resolution are `NpcView`, `ObjectView` ("label" mode) and `PortalView` (label only): markers, barks, verb plates, a pickup's badge, a way's plate. A way is also a mark on the floor (`WayMark`): a lit threshold before a door, jade chevrons at an edge, grey while it is shut |
| Shared presentation | `WorldShared` (new) | What both views do the same way: the events' effects and sounds, the context button's offer and the focus it gives, the names over the world (`WorldLabels`), and asking for a way out. `world.gd`'s own copies were moved there |
| Ways walked into | `TopdownWorld._check_portals` | At a way (the World authority's `portal_near`) with the stick pushing out along its `dir`, the way is taken. An edge is walked out through, a building's door walked into northward, an interior's door southward. No hold is needed, because up is a real direction. The context button's "Enter" works too |
| Auto-path and auto-hunt | `Autopilot._toward_grid` | On the grid the autopilot follows `TopdownRoom.find_path`, pressing Jump where the path climbs a level. It walks into a way along its `dir`. Auto-hunt compares heights instead of surfaces and strikes at the soft lock |
| Minimap and direction mark | `HUD._draw_minimap` | A room on the grid is drawn as its level map (water, floors by level, walls and props dark). The ways, the gold direction mark, the people's markers and the foes use the same projection |
| Moments, weather, hazards | `MomentView`, `HazardView` | Both read view-neutral anchors (`feet()`, `view_center()`, `screen_center()`, `feet_on_screen()`, `fx_layer()`, `loot_parent()`), so moments, weather and hazards play in both views. A night room is tinted blue (`CanvasModulate`, the side view's night tint) |

**The rooms** (thirteen, the tutorial to the sect choice; `docs/tutorial_order.md`). Each keeps its side-view room's
content and connections, redesigned for the grid with height levels, paths to the doors and water edges:

- **Fisher's Hut:** a wooden floor inside plastered walls, the tea on the table, the loft up a stair, and the doorway
  in the front sill.
- **Lotus Ferry:**
  - Home Lane, with paths to the Fisher's Hut and Granny Liu's hut, and the West Gate;
  - the paved square, with Guo's stump and dummy, the shrine, the spring, the board and Old Ma's store;
  - the hall and the Ferry Inn, whose roofs the kite is caught on: crates, then the hall's roof, then a tile's jump;
  - the docks, the pier and Lu's boat, and the watch-tower (3 levels) with its bell up a long stair;
  - the East Gate, a terrace behind the houses, and the river.
- **Old Ma's Store:** the counter, the sandals' loft and the old net by the sacks.
- **Granny Liu's Herb Hut:** her table, the altar-shrine, and the herb loft with its jars and moss.
- **Lu's Boat:** the deck on the river, the gangway, the spring at the bow, and the cabin with the star mat on its
  roof.
- **Lotus Ferry at Night:** Home Lane and the square as by day, tinted for night, the villagers out, the Hollow
  things rising from the river.
- **Reed Shallows:** the flats under a grassy bank and rock ridge, the rats round the middle herbs, Old Snapper by the
  far herbs, the jetty and the river.
- **Willow Path East:** the road under willows, Old Pan's knoll, the meadow terrace and the stream.
- **Willow Path West:** the training ground, the pine ridge with the toads, the rock pillar with the chest on top
  (crates, a step, the pillar), the shrine, the Spirit Fruit tree and the lotus pond.
- **Stoneford Gate:** the town wall with the Quarry Road through it, the County Hall's door and the canal.
- **Market Street:** the stalls and the teleport stone, three roofs in a row for the rooftop thief, and the arch to the
  Beast Trial Grove.
- **Artisan Row:** the forge, Elder Gu's warehouse door, the roof with the tinkerer's gear, and the guild hall.
- **Fairground:** the recruiters on their stages, the Jade and Cloud trial halls and the Trial Tower (lanterns on their
  roofs), the sect roads north, Shen Lian's spar post, and the Caravan Road barred to the west.

**Tests.**

- **`topdown_tutorial`** (new, in `tools/run_tests.sh`, 473 checks) plays `tutorial_order`'s walk from a new
  top-down character, taking every quest on the real dialogue page. It keeps every one of `tutorial_order`'s
  invariants:
  - the HP bar before fights;
  - doors shown, on the grid by `TopdownRoom.entrance`: a building's doorway, or an interior's wall;
  - the hut's door open from waking;
  - quest talks closing;
  - the tracker never empty and leading to the real next place;
  - the first hour's pacing.
- It adds:
  - each room is on the grid exactly when it has a layout, and all thirteen are played on it;
  - each layout places every thing of its room and reaches it on foot from every way in;
  - every spot the walk stands at is reached on foot from where the room was entered;
  - the character's own view builds every room: a figure and a label for each person and thing, a mark and a plate
    for each way;
  - a save taken on the grid resumes there;
  - the bound view's context button offers a talk;
  - auto-path walks the body to the Trial Tower's doorway and in, and out through the Fairground's edge into Artisan
    Row.
- **`prologue_run` and `tutorial_order`** are view-neutral: they stand beside things with `stand_by`
  (`TopdownRoom.spot_near` on the grid), and at the hut's refuge and the boat's spring by their objects.
- **`perf_tests`:** a top-down character's Lotus Ferry loads and runs within budget.

**Screenshots** (`tools/dev/topdown_capture.tscn -- --phase4`, in `docs/redesign/phase4/`): every converted room under
the real HUD (01–15), and Lu's talk on the dialogue page over the grid (16).

**Not yet built, or different from the plan.**

- **The rooms are finished by hand in a generator.** No converter drafts them from the side-view strips.
- **The height grid is not compiled into `ZoneGeometry`.** The rules that ask the side view's geometry get a flat
  stand-in ground; heights, walls and water come from the grid (the motor, the foes, the loot, the tests).
- **The people are drawn in the top-down style** (Phase 3's third part), in eight rows. The layouts give them no
  rest facing of their own: each stands three-quarters toward the camera on the side the side view faces them. Their
  sheets load on threads (within a moment of the room: see the third part).
- **Rooms past the Fairground stay side-view:** the Entry Trial, the sect roads and everything after. A top-down
  character walks on into them and the view changes. (The second part, below, converts chapter 2's stretch.)
- **Terrain and decor.** The rooms draw by Phase 3's terrain rules (`TopdownTerrain`, rebuilt for each room entered):
  auto-tiled paths and shores, rims, shades and prop shadows. Their bamboo, lotus and lanterns are placed sparingly,
  and a room-by-room decor pass (decision 34) is still to come.
- Allies and pets on the plane, hazards and weather layered with the room, and respawn out of the camera's view were
  gaps here; the third part closes them.

### As built: Phase 4, second part · chapter 2's stretch: the trials, both sects' grounds and the Marsh Edge (2026-09-28)

The story's rooms from the sect choice to the first steps of chapter 2 are on the grid, for both sects a player can
join. A top-down disciple plays the Entry Trial, the sect's grounds, Strange Tracks and The Humming Token without
leaving the grid (`docs/tutorial_order.md` steps 10–14).

**The rooms** (fourteen, `tools/data/topdown_rooms.py`). Each keeps its side-view room's content, ids and connections.
The Fairground's sect roads leave north, so each sect's gate room is entered at its south edge, and each sect's halls
stand on terraces a level apart, as their side-view roofs rise.

| Room | On the grid |
|---|---|
| Entry Trial (Jade), `sf_trial_jade` | A walled yard behind the Jade trial hall. The climb to the bell goes over three roofs along the north wall: crates onto the first, a running jump to the second and up its ridge, another jump to the third, and up onto the bell tower. The Trial Puppet steps into a sand ring on a granite apron |
| Entry Trial (Cloud), `sf_trial_cloud` | The same yard under a cliff. The climb goes up two rock ledges, over a plank walk across the cliff pool, to the top ledge's bell |
| Gate Street, `ja_gate_street` | The road up from Stoneford between jade banners onto the plaza (steward, teleport stone, shrine). The Weapon Hall, the Alchemy Hall and the Library stand in a row on rising terraces, their roofs a hop apart (the rooftop thief's run from the crates, the chest on the Library's roof). The service dorm with its sleeping porch, the board and the deacon by the way east, a scholar's garden and pond, the mountain behind. The third chore spot, "the grey stain by the gate", is by the gate |
| Weapon Hall, `ja_weapon_hall` and `cm_weapon_hall` | One layout for both sects, with their own banners: weapon racks along the back wall, the master before them, the sparring ring a level up with its dummies, the smith and the anvil at the forge |
| Pavilion Rooftops, `ja_pavilion_rooftops` | The Jade training yard: dummies, the hall master, the sparring post in a sand ring, the courtyard pine in a raised bed with its herb pot. Three pavilions rise a level each to the Heaven Pavilion's roof, where the Retreat Rooms' door and a chest are. The rear stairs climb to the east terrace, where crates give a second way onto that roof |
| East Terrace, `ja_east_terrace` | The Mission Hall with its training stumps and the Temper drum, the formation elder, the physician, the arena master and his post, the abode terrace up its stairs against the cliff (a cave abode's door between lanterns), the Retreat Rooms |
| Herb Terraces, `ja_herb_terraces` | Three terraces on grassy banks, a garden bed and herbs on each and stairs between them, the gardener at their foot, and the stone stair up through the crags to the peak |
| Elder Hu's Peak, `ja_elder_hu_peak` | A meadow under the summit crags: Elder Hu by the Qi spring, the insight stone, the Heart Trial circle, the treasure plot, ledges stepping up to the Meditation Rock, the pagoda at his abode's door, the path back down |
| Cliff Stair, `cm_cliff_stair` | The Cloud Sect's lower court (steward, teleport stone, shrine, dorm and porch, board, deacon), the grand stair up to the landing, a ledge above it and the top ledge with the Cloud Library's cliff door. The Cloud Steps run from their stone to the bell on the top ledge |
| Sword Court, `cm_sword_court` | The Sword Hall's two wings (the Weapon Hall's door and the library's), the hall master and dummies, the plum-blossom poles (timber posts at stepped heights, a tile apart or side by side a level up), the sparring post, the Temper drum, the arena master, training stumps and the two sword pillars |
| Array Court, `cm_array_court` | The array dais a step up with the formation elder and a lantern at each corner, the physician, the furnace, the rope ledge, the Retreat Rooms, the garden beds and gardener, and the gorge path up to the peak |
| Elder Sung's Peak, `cm_elder_sung_peak` | The west ledge and peak, a rope bridge along a mountain tarn to the far peak where Elder Sung stands, the spring, stone, circle and plot on the meadow, his abode's pagoda |
| Marsh Edge, `rm_marsh_edge` | The path east from the Reed Shallows over wet meadow and two boardwalks, open water with stilt platforms up wooden stairs (the reed and net platforms where the frogs sit, the stilt hut, the lookout), low stilts on the meadow, the south pools with the fishing jetty, and the grey patches under drained reeds and dead trees |

**New art**, in the approved style and deterministic (`build_tiles.py --check`; `docs/redesign/art_bible.md` §6, §8):

- **Props:** `hall` (a sect hall, 8 × 3, its roof a floor two levels up), `pine`, `weapon_rack`, `banner_jade` and
  `banner_cloud` (their tails stir), `post`, `dead_tree`, `boulder`, `grey_reeds`.
- **Tiles:** paint `m`, a wet meadow with puddles, for the marsh.
- **Foes** in five drawn facings and three mirrored, with all six actions: the Trial Puppet, the reed frog, the marsh
  leech, the reed otter and the hollowed boarlet. The foe cell grows to 48 × 56 (feet at 24, 42) so the puppet stands a
  disciple's height; the first three foes are drawn as before.

**Logic.**

- A timed route (the Cloud Steps) finishes at its room's `route_finish` object, where the layout places it
  (`TopdownRoom.merge_def`).
- A sect role's quest leads a disciple to its own sect's grounds (`QuestAuthority.sect_room`). A Disciple's Chores and
  The Weapon Hall used to name the Jade Sect's rooms to a Cloud disciple, whose way there is shut; this held in both
  views. A chore spot set by the Cloud Sect's flag (`alt_flag`) now counts as the objective's place.
- `topdown_rooms.py` also checks that every way is reached by auto-path's own rules (no running jump over a gap), so the
  tracker's go button can cross every room.

**Tests.** `topdown_tutorial`, 777 checks (473 before it, and two for the real character's villagers):

- the Jade walk plays its trial, the sect's grounds and the Marsh Edge on the grid, then The Humming Token (five
  Hollowed Boarlets on the Marsh Edge, handed in on the peak), after which the tracker's Next is Mei Qing's Errand at
  Artisan Row;
- from the fair (a checkpoint kept as both recruiters are met), the Cloud Sect's stretch: its Entry Trial, Shen Lian's
  spar, the chores on the Cliff Stair, the Cloud Steps run on the grid to the bell, its Weapon Hall, Strange Tracks for
  Elder Sung on his far peak and The Humming Token. `tutorial_order`'s invariants hold after every step and over both
  stretches;
- every room of both stretches is played on the grid, its layout places and reaches everything, and every foe it spawns
  has its own figure.

`prologue_run` and `tutorial_order` take the sect's rooms and people from one table (`SECTS`), and `valley_run`'s
checkpoints use `prologue_run`'s shared `save_checkpoint` and `resume_checkpoint`. `perf_tests` adds the region's
line: the Marsh Edge enters in 75 ms and holds 11.6 ms a frame with 25 of its foes fighting (budgets 300 ms and
16.6 ms).

**Screenshots** (`tools/dev/topdown_capture.tscn -- --chapter2`): `docs/redesign/phase4/17`–`32`, each room under the
real HUD, with its foes where it has them.

**Not yet built, or different from the plan.**

- **The next rooms stay side-view:** the Grey Pools and on, and the sect rooms the stretch does not visit (libraries,
  the Alchemy Hall, cave abodes, retreats, the Cloud Herb Terraces). Their doors change the view.
- **No moving or crumbling platforms on the grid.** The Jade trial's moving planks and the Cloud trial's crumbling ledge
  are fixed; a running jump takes their place.
- **A rope bridge is a raised plank walk;** nothing walks under it (bridges stay hand-placed surfaces, §1.2).
- **The tutorial rooms' other foes** (the hollowed eel and minnow at night, Old Snapper, the mossback toad) have no
  top-down figure yet: they stand in with their side-view creature sheet at half size (the third part).

### As built: Phase 4, third part · the gaps closed (2026-09-28)

The known gaps of the first part are closed, and every other place where the grid still read the side view's x-only
or walk-strip rules was audited and fixed. The side view is unchanged except where noted.

**Allies and pets on the plane** (`AllyBrain`, `TopdownBrain`):

- The rules are the same (follow, fight the owner's nearest foe, retreat, sit while the owner meditates, blink when
  left behind or stuck for 2 s); on the grid only the steering is the grid's:
  - an ally comes into the room, and blinks, onto a free spot on its owner's floor, on the owner's side of any wall
    (`TopdownBrain.spot_by`);
  - it keeps behind its owner along the owner's facing on the plane, on the owner's floor (`follow_spot`);
  - it goes there, and closes on a foe, by the grid's path (`TopdownBrain.chase`): walking, stairs, drops, and a hop a
    level up for one that jumps, on the grid's gravity, as the player jumps. The floor underfoot carries it
    (`TopdownBrain.fall`);
  - with no way on foot (a landing stage over the water) it makes no headway, is stuck, and blinks after 2 s.
- **Height-compatible blows** (`AllyBrain.in_reach`): an ally strikes a foe within reach on the plane and on a height
  its blow reaches (`TopdownAim`); a foe's blow reaches an ally only on its own height (`_enemy_hits_allies` reads the
  ally's real height on the grid).
- **Their figures** (`TopdownPlaces.stand_in`, sorted, placed on their floor and shadowed there by the room's
  `FoeView`, their labels on the overlay):
  - a companion is a `TopdownPlaces.Person` in its own outfit (the top-down character's compositor, `TopdownFigure`,
    unchanged), turned to where it walks or aims in eight rows, walking, striking with its weapon's first strike,
    flinching and falling (`TopdownPlaces.pose`);
  - a spirit animal, or a foe the grid's foe sheet has no rows for (Old Snapper, the toads; they were drawn as the mud
    crab), is the side view's own creature sheet at half size (`EnemyView` in its new art mode: its action, facing,
    flash and an ally's blink).

**Hazards and weather layered with the room** (`HazardView`):

- Each part tied to a spot sorts with the room in the pixel viewport (`HazardView.Piece`, one node a part):
  - a flat part (a strike's ring, a scorch, rubble, a pool, a current, a shelter's ring, a boss's blast ring) sorts just
    over the floor it lies on and under whoever stands on it (`TopdownRoom.decal_key`);
  - an upright part (a falling rock, a bolt, springing spikes, dust) sorts at its spot's own key.

  A terrace or a wall in front hides them, and a body in front stands over them.
- The screen's washes and weather (rain, fog, snow, gust lines, the storm's flash, the chill, the Presence's edges)
  and the warning marks draw on the overlay, under the names, the aim and the effects, and under the HUD.
- The rings are drawn as the circles they strike (the side view flattens them into its strip).
- **Effects on the plane** (`WorldAuthority`): strikes fall all round the body on the plane, on floors inside the room,
  at their floor's height (they fell in the side view's strip, y 660–940); a strike reaches a body only within a level
  of its floor; pools and currents act on the floor they lie on, and a layout may give their `areas` in cells; a gust's
  drift carries the top-down body (`TopdownMotor.drift`, as `player.gd` walks with it). The heavens' bolt strikes a
  circle of its radius, its ring falling anywhere round the body. A foe's burning ground lies along its aim on its own
  floor and burns only there.

**Respawn out of view against the camera** (`RoomRuntime.out_of_view`, `TopdownRoom.view_rect`):

- A foe comes back only where no part of its figure is inside the camera's rect for the player's position (both axes,
  clamped to the room as the camera is, grown by the side view's margin: `respawn.offscreen_x` less half the view).
  Near a wall the camera shows 1280 units of the room, so a spot 768 across is in view; a spot 17 tiles straight south
  is out of it. The side view keeps its rule (700 across).
- On the grid a foe is never put on a point another foe stands on: all four of the Reed Shallows' rats had piled onto
  the one rat point out of the camera's view. The side view picks its points as before.
- The HUD's notice of a foe that saw you from off the screen asks the same.

**The people with the room** (`PageWarmer`): while a page script compiles on its loading thread every other load waits
for it, and the title asked for all sixty at once, so a room's people waited seconds for their sheets after launch.
The pages now warm one at a time (the next once the one before is in), and every sheet of a villager's outfit is asked
for as the room is populated (`TopdownPlaces.Person`; the side view's `NpcView.figure` too), so they wait at most for
the page in hand. The pages take about as long in all (7.0 s against 6.4 s headless).

**The audit: side-view rules the grid still used, all fixed.**

| Place | What it did on the grid | Now |
|---|---|---|
| Camera bounds | clamped to the floor's rect: a body on a ridge along the north edge was off the top of the screen | the room as drawn (`TopdownRoom.drawn_rect`), and never the body out of view (`camera_goal`) |
| Portal triggers | a 64 × 44 box scaled with the way's span, the same on both axes: an east edge of three tiles reached 3.6 tiles into the room, and a door on a terrace was taken from the square under its face | half the span along the edge or doorway and a tile across, turned with the way (`reach`), and only on its own floor |
| Pickups magnet | 60 up and down: a drop on a terrace was drawn in from the square below | half a level |
| Loot spill | a row along x: a drop could lie in a wall, the water, or over a ledge at the ledge's height | on the floor it falls on, else on the spot itself |
| Auto-path arrival | on the plane only: "there" under a terrace spot | also on the goal's floor |
| Auto-hunt | the nearest foe, reachable or not; loot only on the ground | only foes and drops there is a way to; the spot to strike from on the foe's own floor |
| Labels | nearest-first by the distance across | by the distance on the plane |
| Minimap | the direction mark only left or right; the player's arrow east or west | the mark on the frame's edge the way points; the arrow in eight ways |
| Enemy attacks | a ranged or close blow chosen by the distance across | by the distance on the plane |
| Off-screen notice | a foe 640 across | the camera's rect |
| Rare herb guardian | woke by the distance across; rose at the side view's y 840 (in the water on the grid) | by the approach on the plane; on the ground under the node |
| Spar partner, summoned adds, ambush | 160 across; adds clamped to y 640–940 | on a free spot of the floor near where they were meant to be (`TopdownRoom.place_near`) |
| Decals on a raised floor | 12 px up, so under the terrace's own row | `decal_key` |
| Loot's name | the distance to its lifted spot | to where it lies |

Checked and already right on the grid: the leash (600 from the spawn on the plane), noticing (sight on the plane, a
level up or down), the context button's reach (on the plane, 48 in height), the foes' patrol (round their spawn on
their floor).

**The walk's fights aim on the grid.** `prologue_run.fight` and `spar_with` now hand their blows the direction to the
target on the grid (`aim_at`), as the top-down view turns the body to the stick; the walk has no view, so its blows
used to keep the last aim and miss a foe behind.

**Tests.**

- `topdown_suite` goes from 87 to 117 checks:
  - the camera's rect: a ridge drawn over the top, the body kept in view there, a small room centred, out of view on
    both axes (a spot straight south the old rule saw);
  - flat marks on a terrace, things put in the water or on a level, the ways' turned reach, the minimap's mark;
  - a companion: coming in on the player's floor, drawn by its stand-in on its floor; following onto the terrace
    without a blink; blinking to the landing stage after 2 s; its reach and a foe's by height; a fight on one level;
    its figure in the top-down style, and stand-ins for a spirit animal and Old Snapper;
  - hazards: spots all round on floors, a strike by level, a gust's carry, the view's sorted rings and bolts and its
    overlay washes and marks, the parts freed with the room, the heavens' circle, burning ground by floor;
  - the audit's respawn by the wall, the off-screen notice, a door by floor, the pickup and spill by floor, auto-path's
    arrival, the labels' order, the attack choice, the guardian's wake, and a spar partner, adds and an ambush on
    floors.
- `topdown_tutorial` (777 to 786 checks) adds a room's people drawn while the pages still warm up, and every way's
  turned reach, in the chapter 2 rooms too.

**Not built.** Hazards and weather are layered and act on the plane, but no room on the grid has a hazard yet (the
tutorial's rooms have none); a layout gives pools and currents their `areas` when one does.

### Phase 5 · The animation layers (XL)

- Clothe the approved body, per `AGENTS.md` rules 1–4:
  - hair 6, shirts 5, trousers 5, shoes 3, hats 6, capes 3 in S/E/N for every catalogue entry;
  - then SE and NE for idle, walk, run, jump and dodge;
  - weapons through the rig (12 families, 8 rotations each);
  - creatures by region, bosses and humanoids with 4 facings.
- **Tests:** the animation contract tests and a human review of the gallery for every item, every facing and every
  dye.

### Phase 6 · Systems as places and polish (M)

- Build §3 in order:
  1. the home courtyard;
  2. the garden, station and post markers;
  3. notice papers and stalls;
  4. tower and arena rooms;
  5. fishing in the world.
- Add baked light tiles plus up to four `PointLight2D`s per room, a day tint (`CanvasModulate`) and the height-assist
  setting.
- **Tests:**
  - `quest_guidance_suite` still leads to every place;
  - the `overlap_suite` for new stations;
  - `perf_tests` with lights on.

### Phase 7 · Cutover and cleanup (S–M)

- Remove the side-view code paths, the backdrops and the old tests.
- Bump `MAP_REVISION` and add the save migration (§5).
- Rebuild both Android presets and profile on a low-end device.
- **Tests:** the whole `tools/run_tests.sh`, and `valley_run` from a new character to Greyfall.

During phases 1–5 a room carries `view: "topdown"` or stays side-view, so tests stay green while regions convert. A
player build ships only whole acts in the new view.

---

## 5. Risks

| Risk | Why | Answer |
|---|---|---|
| **Art volume** | About 170 rooms of tiles and props; 330–520 body frames; ~40 equipment items per facing; 68 creature sheets | Palette-swap dyes; a weapon rig; 3 facings first; creatures 2-facing first; region-by-region shipping; generators in `tools/art/` for tiles and faces |
| **Save compatibility** | `position {room, portal, x, y, surface, facing}` points at side-view geometry | Keep every room, portal and object id. On load, when `MAP_REVISION` is older, place the character at the saved portal's arrival spot (or the room's `spawn_point`) and map facing ±1 to E or W. Paths Above finds stay keyed by ledge id; renamed ledges get an alias table |
| **Mobile performance** | Y-sort over many nodes, several TileMapLayers per level, 2D lights in the Compatibility renderer | A 640×360 world viewport; static faces batched per level; props sort only when on screen; a light budget of ≤ 4 per room; `perf_tests` per region |
| **Height readability on a phone** | Players of the reference game still misread heights (research §1) | Rim highlights, face shading, shadow blobs, the landing ring and the height assist; lint rule: every required level edge has a visible face ≥ 1 tile |
| **Touch feel** | Auto-hop and a Jump button together can confuse | Auto-hop only at speed; tiptoe always drops; the first Prologue room teaches both |
| **Test churn** | Side-view movement suites and sweep assumptions | Replace them phase by phase (§4); never switch a region before its sweep and lint are green |
| **Dual code paths** | Side-view and top-down rooms side by side for months | One solver and one geometry; only the room data and the view differ; delete the side-view path at cutover |
| **Scope creep** | Redesigning systems while converting rooms | §3 waits for Phase 6; pages do not change |
| **Originality** | Reference-driven work drifts toward imitation | Original tiles, characters, names and layouts only; the reference game informs systems, not art |

---

## 6. Decisions for the user

1. **Auto-hop and a Jump button, or auto-jump only?** Recommended: both. The movement arts (double jump, Wall-Step,
   glide, flight) need a button. **Decided (2026-09-27, decision 28 in `docs/roadmap_master_ui.md` §6): keep a Jump
   button.** Touch keeps the joystick, Jump, Dodge/Guard and Attack as now. Auto-hop at speed and the dash-jump over
   gaps may stay as extras, but jumping is always on the button. Phase 1 builds the button jump and the dash-jump,
   and no auto-hop.
2. **Art facings:** 5 drawn (8 facings), or stop at 3 drawn (4 facings)? Recommended: 3 first, 5 for locomotion
   later.
3. **Character height:** ~38 art px (recommended) or keep ~50 (bigger on a phone, but less world on screen)?
4. **Home courtyard:** build it (recommended) or keep systems in towns only?
5. **Release strategy:** convert Act I and ship it as a slice, or convert everything before release?
6. **Movement review (decision 29, 2026-09-27):** the dash cooldown stays; water stops a walk (walking on it is the
   Water Skimming art's); roofs are floors you stand on and jump off. Built in Phase 2.
7. **Aiming (decision 30, 2026-09-27):** a tap soft-locks; held and dragged, Attack and techniques aim with a preview
   of their form on the ground and snap to a foe near the line; back on the button cancels. Built in Phase 2. The
   extra actions on drag zones of the Attack button became decision 35 and are built ("As built: Attack's drag
   moves").
