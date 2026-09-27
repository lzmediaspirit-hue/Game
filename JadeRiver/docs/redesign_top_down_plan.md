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

### Phase 2 · Combat, AI and interaction on the plane (M)

- Directional hit test and auto-aim cone, 2D knockback, enemy steering and flanking, the ally follow rule, context
  reach on the plane, and doors on any side.
- **Tests:**
  - `rules_tests` combat cases for arcs and boxes at 8 facings;
  - enemy nav across levels (it waits beneath targets it cannot reach);
  - `contract_tests` unchanged.

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
   glide, flight) need a button.
2. **Art facings:** 5 drawn (8 facings), or stop at 3 drawn (4 facings)? Recommended: 3 first, 5 for locomotion
   later.
3. **Character height:** ~38 art px (recommended) or keep ~50 (bigger on a phone, but less world on screen)?
4. **Home courtyard:** build it (recommended) or keep systems in towns only?
5. **Release strategy:** convert Act I and ship it as a slice, or convert everything before release?
