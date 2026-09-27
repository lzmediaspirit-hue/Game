# Alabaster Dawn · the top-down 2.5D world and its movement

Research for the Jade River top-down redesign (`docs/redesign_top_down_plan.md`). The subject is Alabaster Dawn, the
second game by Radical Fish Games (Hamburg), the makers of CrossCode. The brief asks for two technical breakdowns, deep
enough to rebuild the core systems: **(A)** its top-down 2.5D graphics system and **(B)** its movement.

Researched 27 September 2026.

## How to read this page

Every statement carries one of three labels:

| Label | Meaning |
|---|---|
| **Confirmed** | Stated by Radical Fish (blog, press kit, Steam page, a developer reply) or by several independent hands-on sources that agree. A citation follows each one. |
| **Inferred** | Not stated for Alabaster Dawn, but it follows from footage and player reports, or from CrossCode, whose engine Alabaster Dawn is built on. The lineage is cited. |
| **Speculation** | A reasoned guess that nothing verifies. It is kept only where a rebuild needs a number, and it is always named as a guess. |

**Source access.** The research environment's network policy refused direct page loads for every site involved
(radicalfishgames.com, Steam, wikis, press, forums). The claims below come from search-engine extracts of the cited
pages. Each claim is linked to the page the extract came from, but no page was read in full. Before any number here
becomes a hard requirement, someone should open the page and check it (§7 lists what to check). Where a search found
nothing, this page says so.

**Status of the game (Confirmed).**
- The first public demo came out on Steam on 18 September 2025 ([S3], [S14]).
- Early Access began on Steam (PC) on 7 May 2026 ([S10], [S5]). EA 0.1.0 runs to about the middle of Chapter 2:
  roughly 5–10 hours, or about 20% of the planned game, plus a roguelite mode, *Somu's Dream* ([S6], [S7], [S10]).
- Eight major updates are planned before 1.0 ([S6]). The studio expects Early Access to last at least two years
  ([S10]). Update 0.2.0 brings a collaboration with SHADE Protocol ([S9]).
- A console release is planned but not dated ([S12], [S13]).
- The game was not crowdfunded. No Kickstarter or backer updates exist for Alabaster Dawn; the only Kickstarter
  connection is SHADE Protocol's own campaign ([S9]).

---

## 1. Executive summary

- **It is CrossCode's model, re-rendered.** The engine grew out of CrossCode's heavily modified impact.js HTML5 engine.
  It was rewritten from JavaScript to TypeScript and moved from canvas2D to **WebGL, so that it can draw 3D**
  (Confirmed: [S11], [S12], [C4], [C13]). The world is still 2D ground coordinates plus a height `z` (Inferred from
  CrossCode [C1]).
- **Pixel art, a 3D camera.** Environments look like 3D geometry textured with pixel art, with sprites billboarded on
  top. The camera is a top-down ¾ view with a "subtle 3D perspective" (Confirmed as the studio's description: [S2],
  [S12]). The 3D construction itself is a community reading of the footage ([S16]), so it is Inferred.
- **Low internal resolution.** The game renders at 640×360, doubles to 1280×720 and then scales to the screen. Pixels
  are not perfect because the game rotates and skews things (community-reported, with a developer answer about adding
  scaling options: [S16], [S17]). This is Inferred-strong: several matching reports, but no official technical post.
- **Height is the level design.** Cliffs, ledges and stacked platforms carry the traversal and the puzzles. There is no
  jump button: you **jump automatically off ledges**. Dash just before an edge and you get a **long jump**. Holding Dash
  charges a **sprint**, and the sprint auto-jumps too (Confirmed by guides and previews: [S20], [S21], [S22], [S23]).
  CrossCode set the rule and the studio explained why ([C2]).
- **Combat and movement share the Dash button.**
  - Dash while moving is a directional dodge. Dash while standing still is a **backhop**. Both cost **stamina** and
    both open with a short invulnerable window ([S21], [S22]).
  - A timed **parry** stuns the attacker and reflects the projectiles marked for it ([S21]).
  - Players complain that a standing sprint starts with a backhop, and that jumping toward a ledge sometimes hops
    backward instead ([S19], [S24]).
- **Reading height is still the weak point.** Players say terrain height is hard to judge, as it was in CrossCode. The
  developers answer that the new perspective camera is meant to help, and players agree it does, in part ([S18]).
- **What transfers to Jade River.** Nearly all the *simulation* model: ground plane plus `z`, height levels, a nav
  graph with jump and drop edges, the shadow on the ground, sorting by the foot's ground `y`, and auto-hop. Jade
  River's `MovementSolver` / `ZoneGeometry` already use the same (x, depth, altitude) model. What does not transfer
  cheaply is the WebGL 3D environment construction. Jade River should reach the look with 2D tiles in Godot's
  Compatibility renderer (§6).

---

## 2. Graphics breakdown (scope A)

### 2.1 Camera projection, angle and implied depth

- **Confirmed.**
  - The studio describes "a unique 2.5D art style combining pixelart with a subtle 3D perspective" ([S2], [S12]).
  - Previews call it "top-down 2.5D presentation … clearly reminiscent of CrossCode" ([S14]).
  - The move to "32-bit graphics" is described as a visual overhaul over CrossCode ([S14]).
- **Inferred (footage, community).** Environments are 3D geometry with pixel-art textures, and characters and many
  props are billboarded sprites ([S16]). Players read "a 2.5D game that's trying to look more 2D" ([S29]). The camera
  moves "fluidly" in set pieces and boss fights ([S14], [S15], [S29]). From that:
  - the camera is a fixed-pitch, near-orthographic view looking down at roughly the classic ¾ angle;
  - it adds slight perspective, visible as vertical faces that foreshorten and parallax a little as the camera moves;
  - it keeps floor tiles close to square on screen.
- **CrossCode lineage.** CrossCode is pure 2D canvas: an oblique projection in which floor tops draw as squares and
  vertical faces draw at full height below them. A point `(x, y, z)` lands on screen at `(x, y − z)` ([C1] gives the
  x/y ground, z height coordinates). The screen formula is Inferred from the map format ([C6]) and from how the game
  draws.
- **Speculation.** The exact pitch and field of view are unknown. The subtle-perspective look can be approximated by an
  orthographic camera pitched about 30–45° with a small FOV, or, in pure 2D, by a slight vertical parallax on tall
  faces. Nothing public gives the numbers.

### 2.2 Height and elevation

- **CrossCode (Confirmed, from the map format [C6]).**
  - A map has `levels`, each with a `height`. `masterLevel` is the index of the ground level.
  - Each tile layer has a `type` (`Background` or `Collision`) and a `level`, the height level it describes. Map size
    is counted in 16×16 tiles.
  - Entities carry a `level` index as well as x/y.
  - Collision is therefore a stack of per-level 2D collision tile grids, not a free 3D mesh.
- **CrossCode tooling (Confirmed [C7]).** The editor had a *height map* tool that paints heights and generates cliffs
  and rivers automatically, alongside auto-tiles.
- **Alabaster Dawn (Inferred).** Traversal climbs ledges, crosses broken bridges and hops between river platforms
  ([S26]), so it keeps discrete height levels with cliff faces between them. With WebGL 3D, the renderer probably
  extrudes those levels into geometry, but no source says how the data is stored.
- **Speculation.** Level heights in CrossCode seem to come in 16-px multiples, since the map format counts in 16-px
  tiles ([C6]). The exact step used by either game was not found.

### 2.3 Depth sorting and occlusion

- **Not found.** No official note on sort rules for either game.
- **Inferred (CrossCode lineage and standard practice with this data model).**
  - Entities sort by the ground-plane `y` of their feet, not by screen `y`. An entity standing on a raised level still
    sorts by its ground `y`, and gets a bias that puts it in front of the cliff face below it.
  - Tiles belonging to a level's wall faces sort with the level's southern edge.
  - Overhangs (tree crowns, roof eaves) sit on a layer drawn above everything.
  - With real 3D geometry, Alabaster Dawn can let the depth buffer do most of this ([S16]); billboards then need
    alpha-tested depth writes.
- **Occlusion when walking behind objects.** Footage and reports do not document a silhouette or outline effect for
  Alabaster Dawn (**not found**). Jade River already has one (`scripts/occlusion_outline.gd`).

### 2.4 Tilemap architecture

- **Confirmed (CrossCode):**
  - 16×16 px tiles ([C6]);
  - background and collision layers per level ([C6]);
  - auto-tiles and a height-map generator in the editor ([C7]);
  - maps stored as JSON and loaded asynchronously per map ([C4], [C5] via the extract);
  - a community map editor that reads and writes the format ([C10]), and a mod that shows the collision maps
    ([C11]).
- **Alabaster Dawn (Inferred).** Rooms are big screens joined at their edges ("large areas until the map shifts at the
  edge": [S15]), so the room model survives. The move to 3D suggests floor tops and wall faces are now separate
  meshes built from the level data. Tile size is **not published**.
- **Wall faces and floor tops.** In the CrossCode model, a raised level's top is drawn in the level's own layer, and
  its south face fills the rows beneath it, as many rows as the level is tall. Faces are auto-tiled from the height map
  ([C7]).

### 2.5 Sprites and animation

- **Confirmed.**
  - Previews single out "silky smooth" animation and "unparalleled pixelwork and animation" ([S14], [S2]).
  - Players can use eight weapons with their own combo trees, two per element across four elements ([S22], [S25]),
    so the character has many attack sets.
- **CrossCode (secondary).** Lea's sheets are drawn per action for up to 8 directions ([C12], from a search extract of
  the sprite archive). Entities can mirror with `flipX` ([C10] issue tracker). The usual count is 5 drawn directions
  mirrored to 8, but that count is **not verified**.
- **Alabaster Dawn directions.** No source states them (**not found**). The footage (Inferred) shows free analog
  movement, with Juno's sprite turning through diagonals.
- **Frame timing.** **Not found** for either game.

### 2.6 Shadows and height in the air

- **Inferred.**
  - A soft ground shadow sits under characters on the surface below them and stays there during a jump. It is the
    main cue for height in the air in CrossCode-style games, and players still find heights hard to read ([S18]),
    which fits a design that leans on that cue.
  - With 3D geometry, environment shadows can be real (shadow-mapped) or baked. Which one is **not found**.

### 2.7 Lighting, VFX, parallax and post-processing

- **Confirmed.**
  - There are "modern rendering techniques" and camera work in intense scenes ([S14], [S29]).
  - The New Year 2025 post shows nature returning to barren ground as the corruption is banished: a world-state
    change drawn in the environment ([S8]).
  - A known dithering problem appears on AMD GPUs with Mesa OpenGL drivers, which implies an ordered-dither pass in
    the post chain ([S28] and Steam reports via the same search).
- **Not found:** light types, day and night, bloom, colour grading.
- **Speculation.** A pixel-art game at 640×360 usually runs light, bloom and fog at the internal resolution, and
  quantises or dithers them to keep them in the pixel grid. The dithering report fits that.

### 2.8 Engine and its evolution from CrossCode

- **Confirmed.**
  - CrossCode is 100% HTML5 with regular JavaScript on canvas2D, built on impact.js. The team rewrote the physics
    (including 3D collision) and the renderer "until almost every nook and cranny was changed" ([C4], [C13], [C14]).
  - Entities are built by composition ([C5]).
  - Collision and rendering run on separate data structures ([C4]).
- **Confirmed (Alabaster Dawn).**
  - The codebase is the CrossCode engine rewritten in TypeScript "to simplify ports for consoles".
  - It is still HTML5, but on **WebGL "to support 3D graphics"** ([S11], [S12]).
  - It renders through native OpenGL on PC. System requirements are modest: 2 GB RAM, 2 GB disk ([S28]).
- **Performance (secondary).** Players report good results on Steam Deck and a need for high TDP on some handhelds to
  hold 50–60 fps ([S28]).

### 2.9 Pixel-perfect rendering, scaling, sub-pixels and the camera

- **Inferred-strong (community reports with a developer reply).**
  - Internal 640×360, doubled to 1280×720 and then scaled, so multiples of 720p look best ([S16], [S17]).
  - The game "rotates and skews things a lot", so pixels are not strictly perfect ([S17]).
  - The developers were looking at adding scaling options and a 640×360 low-resolution mode ([S17]).
- **Speculation.**
  - Entities move at sub-pixel precision and are drawn rounded to the internal pixel grid.
  - The camera is smoothed in world space and snapped to the internal grid.

---

## 3. Movement breakdown (scope B)

### 3.1 Base locomotion

- **CrossCode (Confirmed [C1]).**
  - Each moving entity has `accelDir`, `maxVel` (default 300), `friction` (default 1.0, on the ground) and
    `airFriction` (default 0.2, in the air).
  - Acceleration each frame is `accelDir × maxVel × 10 × friction × accelSpeed × tick`.
  - Physics moves only the ground coordinates (x, y); height is handled separately.
  - Ground control is five times air control.
- **Alabaster Dawn.**
  - Analog, free-direction movement on stick or keyboard ([S20], [S21]).
  - One review calls it "a bit slippery", above all on platforming over rocks ([S23]). That reading fits CrossCode's
    friction model with momentum carried into jumps.
  - Speeds and acceleration are **not published**.
- **Speculation.** If Alabaster Dawn keeps CrossCode's defaults, top speed is about 300 units per second in its own
  units, but the unit scale is unknown.

### 3.2 Vertical movement: jumping, auto-jump and falling

- **CrossCode, the rule (Confirmed [C2]).** There is no jump button. Walking toward an edge falls off it or jumps to
  another platform, and walking toward a low wall jumps up it ([C3]). The developers give three reasons:
  1. level design built on layers of height;
  2. auto-jump "jumping at the last possible moment in front of the gap", with speed changes in the air to adjust the
     distance;
  3. jumps are low, so there is little height to control.

  The admitted downside: to drop instead of jump, you approach the edge more slowly ([C2]).
- **Alabaster Dawn (Confirmed by guides and previews).**
  - The jump fires automatically at the edge, and its distance comes from your speed ([S23], [S24]).
  - **Dash just before an edge gives a long jump** ([S20], [S25]).
  - **Hold Dash after a dash to charge a sprint.** Sprinting auto-jumps off ledges. Releasing Dash while moving enters
    *Divine Sprint*, which is faster still and also auto-jumps ([S21], [S22]).
  - **Aiming during a jump slows time** for ranged shots ([S25]).
- **Climbing (Confirmed [S26]).** Walkthroughs say "use the ledges to climb up": stepped ledges and jumps up low
  faces.
- **Falling between levels (Inferred).** Walking off a higher level onto a lower one falls with gravity. The shadow
  shows the landing. Reaching water or a pit resets you to a safe spot, as in CrossCode ([S19] mentions falling into
  water when a backhop fires on a small platform).
- **When a jump is possible (Inferred from [C2], [C3]).**
  - Up: only onto a face whose top is within the low jump height.
  - Across: only when moving into an open edge at speed.
  - Down: any open edge.

### 3.3 Collision

- **CrossCode (Confirmed [C6], [C3]).**
  - Per-level collision tile layers.
  - A per-level navigation map linked across levels by marked jump points: the NavMap starts from ground-level nodes,
    then links upper levels through "arrow symbols".
  - Dynamic entities slip past each other rather than block ([C1] extract).
- **Hitbox shape and corner sliding.** **Not found.**
- **Inferred.**
  - The collision box is small and set at the feet, a few pixels deep.
  - Movement resolves against tile collision with axis separation, which slides you along walls.
  - Corners are rounded or nudged, as usual for top-down action games.

### 3.4 Dash, dodge and traversal abilities

- **Alabaster Dawn (Confirmed [S21], [S22]).**
  - Dash while moving is a quick directional dodge. Dash with no input is a backward step, the **backhop**.
  - Both cost **stamina** and open with a short invulnerable window.
  - Holding Dash leads into sprint and Divine Sprint (§3.2).
  - Pressing Dash at an edge gives the long jump ([S20]).
- **CrossCode for comparison (Confirmed, community wiki [C8], [C9]).**
  - Three consecutive dashes, then a pause.
  - Short i-frames at the start of each dash; a **perfect dodge** gives about 2 s of invulnerability.
  - Dash-cancel: an attack cancels a dash and a dash cancels an attack.
  - The speedrun trick *jump-attack-dash-cancel* stretches jumps.
- **Traversal abilities.** Alabaster Dawn's puzzles use elemental "Vein weaving" to break walls, and shots at flowers
  to open paths ([S26]). A full list of traversal abilities is **not found** in the extracts.

### 3.5 How combat and movement interact

- **Confirmed.**
  - Heavy and charged attacks lock you into their animations ([S21]).
  - A three-hit combo ends in a finisher that hits twice ([S20]).
  - A parry stuns and opens a counter window. Projectiles marked with red arrows can be reflected, and parries fill
    the break meter faster ([S21]).
  - Switching element switches weapon, even mid-combo ([S22]).
  - Combat Arts sit on top of the weapon trees; Divine Arts are finishers ([S22]).
- **Not found:** how much movement is kept during attacks, knockback distances and the exact i-frame lengths.
- **Inferred from CrossCode's cancels ([C9]).** Dashing out of a light attack is probably allowed. Heavy strings are
  not cancellable ([S21]).

### 3.6 Game feel

- **Confirmed.** Controls are "snappy, intuitive" ([S25]). The parry window is "forgiving" ([S23], [S25]).
- **Not found.** Input buffer windows, coyote time and landing feedback.
- **Inferred.**
  - Auto-jump fires at the last possible moment at the edge ([C2]), which does the job of coyote time: you never
    leave the ground too early.
  - Landing shows as dust plus the shadow meeting the feet.

### 3.7 What changed from CrossCode

| Area | CrossCode | Alabaster Dawn | Label |
|---|---|---|---|
| Engine | JS on impact.js, canvas2D ([C13]) | TypeScript rewrite, WebGL 3D ([S11], [S12]) | Confirmed |
| Look | Flat oblique 16-px pixel art | 3D geometry with pixel textures and billboards, subtle perspective ([S2], [S16]) | Confirmed (studio wording) / Inferred (method) |
| Resolution | Low internal resolution, integer scaled | 640×360 → 1280×720 → screen ([S17]) | Inferred-strong |
| Dodge | Three dashes, perfect dodge ([C8]) | Stamina dodge, backhop, long jump, charged sprint ([S21], [S22]) | Confirmed |
| Defence | Guard and shield ([C9]) | Parry with projectile reflection and a break meter ([S21]) | Confirmed |
| Weapons | One melee and ranged kit, with elements | Eight weapons, two per element, switched with the element ([S22]) | Confirmed |
| Height reading | A known complaint | Same complaint; the perspective camera is meant to help ([S18]) | Confirmed |

---

## 4. Diagrams and pseudo-code

### 4.1 Coordinates and projection (CrossCode model; Jade River already uses it)

```
 ground plane (x, y)            screen
   y ↓                           screen_x = x
                                 screen_y = y − z          (1:1 oblique: a top is a square, a face is its height)
   ┌────────┐  top of level 2 (z = 64) drawn 64 px higher
   │ LEVEL2 │
   ├────────┤  ← south edge of the level-2 footprint (ground y = y1)
   │  face  │  64 px of wall face drawn from screen y1−64 to y1
   └────────┘
   ░░░░░░░░░░  level 0 floor
```

Jade River: `scripts/player.gd:509` draws at `Vector2(plane.x, plane.y − altitude)`. That is this projection exactly.

### 4.2 Depth sort

```
sort_key(actor):
    base = actor.ground_y                     # the feet's y on the ground plane, never screen y
    for level in levels_under(actor):         # every raised footprint the actor stands on or above
        if actor.z >= level.top - EPS and level.footprint.contains(actor.ground_xy):
            base = max(base, level.south_edge_y + 1)    # draw after this level's own face
    return base

sort_key(static prop)      = prop.footprint.south_edge_y
sort_key(wall-face tile)   = the level's south_edge_y at that column
sort_key(overhang)         = +∞  (canopy and eaves layer, over everything, fades when the player is under it)
```

Ties go to z (the higher draws later). This is what `ZoneGeometry.render_depth()` does today.

### 4.3 Height levels as data

```
room.height_grid (1 char per 16-art-px tile; digit = level; '.' = void; '~' = water):

  2222222000
  2222222000       level 2 = z 64, level 1 = z 32, level 0 = z 0
  1111222000
  1111111000
  0000000000

compile():
  for each level L > 0: merge its cells into maximal rectangles → WalkSurface(rect, height = L·32)
  edges: a side is 'wall' where the neighbour is higher, 'open' where it is lower (a fall or hop), 'closed' where the
         two cells are the same level but a fence or prop blocks
  faces: for each column, rows south of a level-L cell whose neighbour is lower get (L − neighbour) face tiles
```

### 4.4 Jump, auto-hop and fall

```
each physics step (120 Hz):
    if on_surface:
        wish = stick · speed_for(stick)          # analog; tiptoe below 0.6 deflection
        next = pos + wish·dt
        edge = surface.edge_crossed(pos, next)
        if edge == WALL:
            if face_top − z <= STEP: step up            # stairs and ramps
            elif jump_pressed and face_top − z <= JUMP_REACH: jump
            else: slide along the wall (drop the normal component)
        elif edge == OPEN:
            if speed >= 0.7·max and landing_exists(next, dir, reach(speed)):  # auto-hop (the CrossCode rule)
                start_jump(HOP_IMPULSE)
            elif coyote_left > 0: stay on the edge for coyote time
            else: start_fall()                   # a slow walk off a ledge just drops
    else:
        vz -= g·dt;  z += vz·dt;  pos += air_control(wish)·dt
        land on the highest surface under pos with top <= z (and >= z − vz·dt)
        mantle if a top lies within MANTLE_RISE above and pushing into it
    shadow.draw_at(ground_y_of(surface_under(pos)))    # the shadow never jumps
```

---

## 5. How to recreate it, step by step

1. **Data model.** Positions are `(x, y, z)`: ground plane plus height. Rooms store a height grid of discrete levels
   (§4.3) plus hand-placed extra surfaces (bridges, decks) for places the grid cannot express, such as walking
   *under* a bridge.
2. **Compile collision** per level into rectangles with edge types (wall, open, closed). Keep collision separate from
   rendering, as CrossCode does ([C4]).
3. **Movement.** Use CrossCode-style acceleration and friction with lower air friction ([C1]). Add auto-hop at open
   edges when moving fast, and a plain drop when slow (this fixes CrossCode's admitted drop problem [C2]). Add a
   long jump on Dash at an edge ([S20]).
4. **Dodge.** A directional dodge while moving, a backhop from standstill, and i-frames at the start. Add stamina or a
   cooldown ([S21]).
5. **Rendering.**
   - Render at a low internal resolution (640×360) and integer-upscale ([S17]).
   - Floor tops draw at `y − z`.
   - Wall faces are auto-tiled from the height grid ([C7]).
   - Sort entities with §4.2. Draw an overhang layer for canopies.
   - Put a ground shadow under anything in the air.
6. **Navigation.** A nav graph per movement profile: per-level walk areas, plus jump-up, hop-across and drop edges
   ([C3]).
7. **Camera.** Follow in world space. Track the ground height, not the jump arc. Snap to the internal pixel grid.
   Add a little look-ahead.
8. **Readability.** Invest early in the height cues players still miss ([S18]):
   - face shading;
   - rim highlights on level edges;
   - shadow blobs;
   - a landing marker during jumps;
   - an optional height-outline assist.

---

## 6. Application to a 2D MMORPG-style mobile game (Jade River)

**Transfers well.**

- **The simulation model.**
  - Jade River's `ZoneGeometry` (surfaces with heights and edge types, blocks, volumes, movers) and `MovementSolver`
    already run in (x, depth, altitude).
  - The nav graph already has walk, jump, drop and climb edges (`ZoneGeometry.nav_graph`), which is CrossCode's
    NavMap idea ([C3]).
  - The rewrite is the room *shape* (a whole floor instead of a strip) and the numbers, not the physics.
- **Auto-hop on touch.** Fewer buttons suit a thumb. Use auto-hop across gaps and down levels, and keep a **Jump
  button** for jumping *up*, the double jump, the glide and flight, which Jade River's movement arts need
  (`docs/movement.md`).
- **Tiptoe to drop.** A light stick deflection walks slowly and drops off an edge instead of hopping. This is the
  analog answer to CrossCode's admitted problem ([C2]) and fits a virtual joystick.
- **Low internal resolution.** 640×360 matches Jade River's art contract: native pixel scale 2 on a 1280×720 canvas
  (`docs/art-contracts.md`). Rendering the world in a 640×360 SubViewport cuts fill-rate and texture memory on phones.
- **Multiplayer sync (future online).**
  - Height levels come from the room geometry, so the wire needs only `(x, y, z, vz, state, facing)` at 10–20 Hz.
  - Send jumps as events (start point, impulse, tick) so every client simulates the same arc with the shared solver.
    `ZoneGeometry` is already written to be "shared by the local simulation and a future authoritative zone server".
  - The server checks each landing against the same compiled surfaces.
  - Remote players draw about 100 ms behind with interpolation. Their shadows sit on the ground height at their
    interpolated position.

**Does not transfer.**

- **WebGL 3D environments** ([S11], [S16]). They mean a new art pipeline (models plus pixel textures) and a 3D camera.
  They cost more per frame than tiles on low-end Android in Godot's Compatibility renderer. Get the look in 2D:
  auto-tiled faces, baked light and a few 2D lights.
- **Rotation and skew of pixel art** ([S17]). It breaks the pixel grid. Avoid it except in short VFX.
- **Stamina-gated, parry-centred combat.** It is a design choice, not a render feature. Jade River keeps its guard,
  dodge cooldown and techniques. Parry-style timing can be added later as a technique.
- **Precise ledge platforming on a phone.** Reviewers find it slippery even with a pad ([S23], [S19]). On touch, widen
  landings (Jade River's lint already asks for 80×60), add a landing ring (Jade River has one), and snap auto-hops to
  the nearest valid landing.

---

## 7. Open questions and unverified claims

1. **Every claim above.** Direct page loads were refused by policy, so every claim rests on search-engine extracts of
   the cited pages. Priority checks: [S17] (the 640×360 pipeline and the developer reply), [S11]/[S12] (WebGL and
   TypeScript), [S21]/[S22] (dodge, sprint, stamina), [C6] (the level fields).
2. **Tile size.** Alabaster Dawn's tile size and level-height step are not published.
3. **Sprites.** The number of drawn directions (5 mirrored to 8, or 8) and the frame rates are unknown for both games.
4. **Sort and occlusion.** Is sorting done by the depth buffer or by 2D sort? Is there a silhouette when occluded?
5. **Numbers.** No speeds, acceleration, dodge distance, i-frames, jump arc or coyote time were found. The numbers in
   `docs/redesign_top_down_plan.md` are Jade River's own.
6. **Lighting.** Real-time or baked? Shadow maps? What exactly causes the Mesa dithering problem?
7. **Camera angle.** Is the 3D camera orthographic with pitch, or perspective with a narrow FOV?
8. **Assist options.** A player mentions assist options for terrain height ([S18]); what they do is unknown.
9. **Official devlogs.** A search for a devlog on movement or rendering found none. The official posts found are
   announcements, the demo, EA, the roadmap and the year-end posts ([S3]–[S9]).

---

## 8. Sources

Official (Radical Fish Games, Steam):

- [S1] Steam store page — https://store.steampowered.com/app/3110760/Alabaster_Dawn/
- [S2] Press kit — https://www.radicalfishgames.com/presskit/sheet.php?p=alabaster_dawn
- [S3] Public Demo Out Now — https://www.radicalfishgames.com/?p=7782
- [S4] Alabaster Dawn Demo Release — https://www.radicalfishgames.com/?p=7730
- [S5] Alabaster Dawn – Early Access out NOW! — https://www.radicalfishgames.com/?p=8041
- [S6] Alabaster Dawn Roadmap + Next Milestone — https://www.radicalfishgames.com/?p=8062
- [S7] 2025 Wrap-Up & Introducing a New Feature — https://www.radicalfishgames.com/?p=7879 (Steam mirror: https://store.steampowered.com/news/app/3110760/view/516355643791115755)
- [S8] Alabaster Dawn Update for the New Year of 2025 — https://www.radicalfishgames.com/?p=7606
- [S9] Alabaster Dawn x CrossCode x SHADE Protocol — https://www.radicalfishgames.com/?p=8106

Press and hands-on:

- [S10] Gematsu, EA date — https://www.gematsu.com/2026/04/alabaster-dawn-launches-in-early-access-on-may-7
- [S12] RPG Site, announcement — https://www.rpgsite.net/news/16135-radical-fish-games-announces-25d-pixel-art-action-rpg-alabaster-dawn-set-to-release-for-steam-early-access-in-2025
- [S13] RPGFan, announcement — https://www.rpgfan.com/2024/08/08/crosscode-dev-announces-alabaster-dawn/
- [S14] RPGFan hands-on (Sep 2025) — https://www.rpgfan.com/2025/09/18/alabaster-dawn-gorgeous-pixel-art-rpg/
- [S15] RPGFan hands-on (May 2026) — https://www.rpgfan.com/2026/05/04/alabaster-dawn-hands-on-preview/
- [S23] Console Creatures, demo preview — https://www.consolecreatures.com/alabaster-dawn-preview/
- [S25] Game8, EA review — https://game8.co/reviews/alabaster-dawn/alabaster-dawn-review-early-access
- [S27] GamingOnLinux, EA — https://www.gamingonlinux.com/2026/05/alabaster-dawn-from-the-developers-of-the-excellent-crosscode-is-now-in-early-access/

Community (secondary):

- [S11] Alabaster Dawn Wiki (wiki.gg) — https://alabasterdawn.wiki.gg/wiki/Alabaster_Dawn
- [S16] ResetEra, "pixel art in 3D" thread — https://www.resetera.com/threads/this-upcoming-game-alabaster-dawn-looks-like-the-perfect-representation-of-pixel-art-in-3d.1265787/
- [S17] Steam discussion, Integer Scale — https://steamcommunity.com/app/3110760/discussions/0/598532699953684850/
- [S18] Steam discussion, Terrain height — https://steamcommunity.com/app/3110760/discussions/0/4520010991998129169/
- [S19] Steam discussion, Early Play Feedback — https://steamcommunity.com/app/3110760/discussions/0/837250226423197983/
- [S20] Steam guide, Basic Guide and FAQ — https://steamcommunity.com/sharedfiles/filedetails/?id=3715211886
- [S21] GAMES.GG, Beginner Combat Guide — https://games.gg/alabaster-dawn/guides/alabaster-dawn-beginner-combat-guide/
- [S22] GAMES.GG, Combat Arts and Divine Arts — https://games.gg/alabaster-dawn/guides/alabaster-dawn-combat-arts-and-divine-arts/
- [S24] Medium, demo impressions — https://medium.com/@spencer2457/why-alabaster-dawn-is-not-just-crosscode-gone-fantasy-demo-impressions-5ae1d2e7b2c7
- [S26] Into Indie Games, Prologue walkthrough — https://intoindiegames.com/walkthroughs/alabaster-dawn-walkthrough-part-1-prologue/
- [S28] PCGameBenchmark, system requirements — https://www.pcgamebenchmark.com/alabaster-dawn-system-requirements
- [S29] InGameNews, 2.5D perspective — https://www.ingamenews.com/2026/05/alabaster-dawn-25d-action-rpg.html

CrossCode technical material (the lineage):

- [C1] Movement Physics of CrossCode — https://www.radicalfishgames.com/?p=72
- [C2] CrossQuestion: Why do we use auto jump in CrossCode? — https://www.radicalfishgames.com/?p=1168
- [C3] Path Finding in CrossCode — https://www.radicalfishgames.com/?p=498
- [C4] Architecture of CrossCode #1 – Overview — https://www.radicalfishgames.com/?p=277
- [C5] Optimizing an HTML5 game engine using composition over inheritance — https://www.radicalfishgames.com/?p=1725
- [C6] Map file layout (CrossCode Wiki) — https://crosscode.fandom.com/wiki/Map_file_layout
- [C7] CrossCode Dev Stream, Auto Tiles and Height Map (1/2, 2/2) — https://www.youtube.com/watch?v=kPlkhsNsXaw , https://www.youtube.com/watch?v=i-0H9ihQ5QM
- [C8] Dashing (CrossCode Wiki) — https://crosscode.fandom.com/wiki/Dashing
- [C9] Advanced Techniques (CrossCode Wiki) — https://crosscode.fandom.com/wiki/Advanced_Techniques
- [C10] crosscode-map-editor (CCDirectLink) — https://github.com/CCDirectLink/crosscode-map-editor
- [C11] CCCollision (CCDirectLink) — https://github.com/CCDirectLink/CCCollision
- [C12] The Spriters Resource, CrossCode Lea — https://www.spriters-resource.com/pc_computer/crosscode/asset/127065/
- [C13] CrossCode (Wikipedia) — https://en.wikipedia.org/wiki/CrossCode
- [C14] CrossCode (The Cutting Room Floor) — https://tcrf.net/CrossCode

[S1]: https://store.steampowered.com/app/3110760/Alabaster_Dawn/
[S2]: https://www.radicalfishgames.com/presskit/sheet.php?p=alabaster_dawn
[S3]: https://www.radicalfishgames.com/?p=7782
[S4]: https://www.radicalfishgames.com/?p=7730
[S5]: https://www.radicalfishgames.com/?p=8041
[S6]: https://www.radicalfishgames.com/?p=8062
[S7]: https://www.radicalfishgames.com/?p=7879
[S8]: https://www.radicalfishgames.com/?p=7606
[S9]: https://www.radicalfishgames.com/?p=8106
[S10]: https://www.gematsu.com/2026/04/alabaster-dawn-launches-in-early-access-on-may-7
[S11]: https://alabasterdawn.wiki.gg/wiki/Alabaster_Dawn
[S12]: https://www.rpgsite.net/news/16135-radical-fish-games-announces-25d-pixel-art-action-rpg-alabaster-dawn-set-to-release-for-steam-early-access-in-2025
[S13]: https://www.rpgfan.com/2024/08/08/crosscode-dev-announces-alabaster-dawn/
[S14]: https://www.rpgfan.com/2025/09/18/alabaster-dawn-gorgeous-pixel-art-rpg/
[S15]: https://www.rpgfan.com/2026/05/04/alabaster-dawn-hands-on-preview/
[S16]: https://www.resetera.com/threads/this-upcoming-game-alabaster-dawn-looks-like-the-perfect-representation-of-pixel-art-in-3d.1265787/
[S17]: https://steamcommunity.com/app/3110760/discussions/0/598532699953684850/
[S18]: https://steamcommunity.com/app/3110760/discussions/0/4520010991998129169/
[S19]: https://steamcommunity.com/app/3110760/discussions/0/837250226423197983/
[S20]: https://steamcommunity.com/sharedfiles/filedetails/?id=3715211886
[S21]: https://games.gg/alabaster-dawn/guides/alabaster-dawn-beginner-combat-guide/
[S22]: https://games.gg/alabaster-dawn/guides/alabaster-dawn-combat-arts-and-divine-arts/
[S23]: https://www.consolecreatures.com/alabaster-dawn-preview/
[S24]: https://medium.com/@spencer2457/why-alabaster-dawn-is-not-just-crosscode-gone-fantasy-demo-impressions-5ae1d2e7b2c7
[S25]: https://game8.co/reviews/alabaster-dawn/alabaster-dawn-review-early-access
[S26]: https://intoindiegames.com/walkthroughs/alabaster-dawn-walkthrough-part-1-prologue/
[S28]: https://www.pcgamebenchmark.com/alabaster-dawn-system-requirements
[S29]: https://www.ingamenews.com/2026/05/alabaster-dawn-25d-action-rpg.html
[C1]: https://www.radicalfishgames.com/?p=72
[C2]: https://www.radicalfishgames.com/?p=1168
[C3]: https://www.radicalfishgames.com/?p=498
[C4]: https://www.radicalfishgames.com/?p=277
[C5]: https://www.radicalfishgames.com/?p=1725
[C6]: https://crosscode.fandom.com/wiki/Map_file_layout
[C7]: https://www.youtube.com/watch?v=kPlkhsNsXaw
[C8]: https://crosscode.fandom.com/wiki/Dashing
[C9]: https://crosscode.fandom.com/wiki/Advanced_Techniques
[C10]: https://github.com/CCDirectLink/crosscode-map-editor
[C11]: https://github.com/CCDirectLink/CCCollision
[C12]: https://www.spriters-resource.com/pc_computer/crosscode/asset/127065/
[C13]: https://en.wikipedia.org/wiki/CrossCode
[C14]: https://tcrf.net/CrossCode
