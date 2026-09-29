# Art bible · the top-down world

This page sets how the top-down world of Jade River is drawn: terrain, height levels, water, plants, buildings and
props. It serves Phase 3 of `docs/redesign_top_down_plan.md` and decision 31 in `docs/roadmap_master_ui.md` §6.
Characters follow `docs/art-contracts.md` and `AGENTS.md`; this page gives their scale against the tiles and, in §13, how
the real character (decision 32) is drawn for this view.

**The brief (decision 31).** The world should look close to Alabaster Dawn's: bright, detailed ¾ top-down pixel art.
Height levels read at a glance, wall faces stand apart from floor tops, shading is soft, tiles are lush and props are
lively. The theme stays xianxia and Jade River's own: river towns, terraces, pagodas, lotus, mist, jade, bamboo, grey
tile roofs and red lacquer.

**Inspiration only.** Every tile, prop and name here is drawn and named for Jade River. Nothing is traced, sampled,
recoloured or rebuilt from another game's tiles or sprites. The reference game sets a *quality bar* and a
*readability goal*. Where this page describes "the style", it describes our own rules.

Built by `tools/art/topdown/build_tiles.py`. The style review images are in `docs/redesign/phase3/` (§12).

**Terrain v2 (decision 40, §14)** redraws the ground, edges, faces, water and buildings closer to Alabaster Dawn. For
those, §14 replaces the ramps (§2), the shade colour (§3) and the water's look (§7). It is also the contract the
runtime light and the foliage work follow.

---

## 1. The look in one paragraph

A sunny river town seen from a high, slightly tilted view. Floors are bright and warm, and every raised level has a
clearly darker, cooler face under it. A thin sunlit lip sits on top of each face, and a soft teal shade lies at its
foot. The ground is full of small detail at the 1–3 px scale: blades, pebbles, stone joints with moss, tile ribs.
Nothing is noisy at the 16 px scale. Large areas stay calm, so characters and interactables always stand out. Colour
comes from the materials (jade water, green meadows, warm stone, grey tiles), not from lighting effects. The saturated
accents (red lacquer, lantern gold, lotus pink) are rare and mark places of interest.

## 2. Palette

*Terrain v2: the tiles now use the `*2` ramps and the blue-violet shadow of §14.3 and §14.2. The ramps below remain
the props' ramps.*

The ramps live in `tools/art/topdown/palette.py`. Terrain ramps have seven steps, dark → light: 0 is the deepest shade
(cracks, the underside of a lip), 3 is the base, 5 the sunlit side and 6 the specular rim. As `docs/art-contracts.md`
requires, shadows shift toward blue-green and highlights toward warm gold. Nothing is shaded with pure black or white.

| Material | Ramp (0 → 6) | Tied to | Where |
|---|---|---|---|
| Grass | `123A27 1D5634 2C743C 448F43 63AA4C 8FC65C C4E484` | Style A `leaf`, warmed at the top | meadows, terrace tops, lips |
| Path earth | `3B281B 5A3E28 7A5A38 9A774B B79463 D2B282 E8D3A6` | between `clay` and `straw` | dirt paths |
| Town paving | `2B2825 46403A 625A51 80766A 9E9383 BCB19D D9D0BC` | Style A `warmstone` | squares and lanes |
| Granite | `1A2226 2A353B 405058 5E6F76 83949A AAB8B9 D0DAD6` | Style A `stone` | terrace walls, the promenade, stairs |
| Karst rock | `1C2427 2E3A3D 455354 5F6E6C 7F8C86 A5AEA3 CBD0C0` | local (blue-grey limestone) | cliffs |
| Bank soil | `261811 3E271B 583A27 745035 916A47 AE875E C9A77C` | local | earth faces |
| Moss | `15321F … C8DC8A` | Style A `moss` | joints, cliff tops, damp stone |
| River | `0A2A2E 0F3E41 15544F 1D6C61 2A8876 4CA992 8BD5BC D6F5E6` | Style A `jade`, pushed toward river night | all water |
| Roof tile | `141A1F 222B32 323E46 46545C 5E6D74 7D8C90 A3B0B0` | local (fired grey clay) | roofs, wall caps |
| Plaster | `6E685B … F6F1E3` | Style A `paper` | whitewashed walls |
| Timber | `24150B … E2BF8A`, dark `1A1009 … 90683D` | Style A `wood`, `darkwood` | piers, frames, crates |
| Red lacquer | `35101A 641B26 962A2F C23D37 DE5A45 F2866A` | Style A `red` | doors, columns, posts |
| Lantern | `7A2418 … FFF0B0` | Style A `fire`, softened | lit lanterns |
| Bamboo, leaf, lotus pad, lotus | Style A `bamboo`, local, local, `lotuspink` | | plants |
| Shade | `0B2A30` at 8–65% | river night | every cast shadow and contact shade |

**Value plan.** Floors sit in the upper middle of the value range. The river is the darkest large field, and faces
sit between the two. Measured on the atlas as the mean luminance of the face body against its top:

| Top → face | Ratio |
|---|---|
| grass → earth bank | 0.56 |
| rock → cliff | 0.60 |
| granite → retaining wall | 0.43 |

**Rule: a face is at most 0.65× its top's luminance.** Buildings are the exception, since white walls are brighter
than grey roofs. There, the eave's dark band of tile ends and the shadow it casts on the wall carry the edge (§5).

**Accent budget.** Red, gold and pink cover under about 3% of a screen. They mark doors, lanterns, notices, flowers:
places the player should look.

## 3. Light

*Terrain v2: the sun is unchanged. Every shade the tiles and the prop floor shadows cast is now the blue-violet
`SHADOW` `#241F4F`, with the alphas in §14.2.*

- **One sun, high in the upper left (north-west).** It is the same light as the icons and creatures
  (`docs/art-contracts.md`).
- **Tops** take full light, and their west and north edges catch a warm rim.
- **South faces** are turned away from the sun. They take the shaded half of their ramp: darker and cooler than any
  top.
- **Cast shade** falls to the lower right. A raised cell shades the floor east of it (`shade_w`, 5 px, fading). A face
  darkens the floor at its foot (`ao_n`, 4 px). A prop casts a soft oval to its south-east (the manifest's `shadow`,
  drawn into the prop sheet as a sprite of its own and laid on the floor the prop stands on, §8).
- **Soft shading without blur.** Every gradient is a few ramp steps in clusters, or a stepped translucent teal. There
  is no dithering noise, no anti-aliasing and no filtering. Scaling is nearest neighbour only.

## 4. Outlines

*Decision 42: the character's outline is now a tint of the material it bounds, not flat ink, with a lighter line where
a part overlaps the body (§13). Props keep the rules below.*

- **Terrain has no outlines.** Edges come from value: the lit lip over a dark contact line, and joints two steps under
  the stone.
- **Props and characters** get a 1 px outline. It is ink-teal `0E1A1E` on the shaded (lower-right) side and a softer
  `26363A` on the lit (upper-left) side (`Img.outline`). So props pop off the ground without looking stickered on.
- **Things on the water are not outlined** (lotus pads). A darker water ring under the pad does the job.
- **No outline inside a silhouette.** Inner forms separate by value.

## 5. Grid, scale and height levels

| Item | Rule |
|---|---|
| Tile | 16 × 16 art px |
| World view | 640 × 360 art px (40 × 22.5 tiles), shown ×2 at 1280 × 720 |
| Level | 1 level = 16 art px = one tile row of face |
| Water | half a level (8 px) under the ground, so a one-tile gap still shows water |
| Character | ~46 art px from sole to crown (48 with a top knot), feet on the anchor: about 2.9 tiles (decision 43: 1.2 times the 38 px it was first drawn at). The real character (§13) is the reference, and §13's scale rule says what follows its size |
| Doors | 2 tiles wide in the wall, 24–28 px tall. A body is about 20 px across and its foot box 19 × 10 world units (9.5 × 5 art px), so it fits through every way a tile wide or more, and reads as fitting a door's two tiles |
| Props | footprint in whole tiles; sprite height free |

**What makes a height readable.** Every raised edge carries all six of these cues:

1. **The lip.** The top's front edge is repeated as the face's first 2 px: a 1 px rim at ramp 6, then the top body. On
   grass and moss tops, a fringe hangs 0–4 px over the face.
2. **The contact line.** A 1 px ramp-0 line runs right under the lip, where the top's overhang throws its shade.
3. **The face.** It is at least two ramp steps under its top and cooler, and each material has its own texture:
   courses for walls, vertical fissures for cliffs, strata for banks, pilings for piers. Faces tile downward, one row
   per level, so a cliff's height can be counted in rows.
4. **The foot.** `ao_n` darkens the floor 4 px under a face. Every raised block shades the floor to its east
   (`shade_w`).
5. **The side rims.** Where a top's west neighbour is lower, a warm 1 px rim runs along it. Where the east neighbour
   is lower, a 1 px shade runs along it. Where the north neighbour is lower, a dark 1 px drop line sits under a warm
   inner line. A face's west end gets a thin lit edge and its east end a shaded one.
6. **The body's shadow.** It stays on the surface underneath during a jump. This is the Phase 1 view's blob shadow.

**Cliff edges.** Rock tops are pale and mossy. Their faces are karst pillars, lit on the west side of each pillar, with
a darker fissure on the east side. A level-3 cliff shows three rows: `rock_face_top`, then `rock_face` twice.

**Standable roofs (decision 29).** A roof top is an even, bright plane of grey tile ribs, with no gradient that would
suggest a slope you slide off. It has a clean lit verge on the west, a shaded verge on the east, a low crest you walk
over, and a row of round tile ends as its lip. The house and storehouse props are drawn to these rules; their manifest `top` of 2
makes the roof a floor in the room view. The crates' lids read the same way at one level. So is a house built on the
height grid: paint `t` gives `roof_top`, and its faces are `roof_face_top` (eave, tile ends, the eave's shadow on the wall)
over `roof_face` / `plaster_face_window` / `plaster_face_door`.

**Height assist (later, Settings).** If a level still misreads on a phone, the plan's height assist tints each level's
top rim. The tiles leave room for it: the rim row is a single colour that the tint can take.

The readability test (`06_height_levels_test.png`) renders levels −½ to 4 with a body on each level, in colour and by
value alone. The levels must stay distinct in the grey half.

## 6. Auto-tiles

There are three systems, each chosen for what it has to join:

| What | Scheme | Tiles | Why |
|---|---|---|---|
| Grass over dirt, grass over paving (same level) | **Corner-matched** (Godot `TERRAIN_MODE_MATCH_CORNERS`, the 16-case "marching squares" set) | 16 per pair | Organic edges need only the four corners. 16 tiles instead of 47 for the same look, and every case is generated, so none is missing |
| Shore (water against anything that is not water) | **Side-matched** (`TERRAIN_MODE_MATCH_SIDES`) | 16 cases × 4 frames | The ¾ view puts the waterline in a different place on each side (below). A corner scheme would put it in the wrong place |
| Faces, lips, rims | **Generated from the height grid** (no terrain matching) | `*_face_top`, `*_face`, 5 overlays | A face depends on the level difference, not on neighbouring materials. The plan's compiler (§1.2 `faces`) places them |

**Why not the 47-tile blob?** It encodes sides and corners together. That is what a thin wall or fence needs, but our
walls are height levels whose edges come from the grid. For ground materials the corner set gives the same result with
a third of the tiles. The blob stays an option for fences and hedges when they come.

**The path rule.** A path cell's corner is grass when any cell sharing that corner is grass *on the same level*. Grass
creeps over the path's edge, and never across a level edge. A path should be at least 2 tiles wide. Each tile's edge
follows the blend of its four corners, roughened by noise. The noise fades to nothing on any tile edge whose two
corners agree, so neighbours always meet cleanly. The grass edge has a lit fringe on its sunny side and drops a 1 px
shade on the ground to its lower right.

**The shore rule.** Bits are 1 N, 2 E, 4 S, 8 W, set when that neighbour is not water. Because water is drawn 8 px
low:

- **north:** the waterline is at the tile's top row, right under the bank face. The water beside the bank lies in its
  shade;
- **south:** the waterline is at row 7, where the land's top edge covers the rest;
- **east and west:** the waterline is on the tile's edge.

A foam line breathes at the waterline over the four frames. In the TileSet, a shore tile's water sides are marked
water and its land sides are left empty. Painting the water layer with terrains picks every shore case by itself (this
was checked in Godot 4.5.1).

**In the game (decision 33).** `TopdownTerrain` (`scripts/topdown/topdown_terrain.gd`) applies these rules to a room's
height grid and paint, and the room view draws what it picks. The paint table in the manifest says what each mark takes
part in:

| Field | Meaning | Marks |
|---|---|---|
| `grass` | creeps over a path's edge on its own level | `g`, `f`, `b`, `m` |
| `under` | the corner-matched set grass creeps over it with | `d` (`grass_dirt`), `p` (`grass_paving`) |
| `keep_face` | keeps its own face over water instead of the granite embankment | `w` (pilings), `g`, `f` and `m` (a grassy bank's soil) |
| `face_below` | the face rows under the first, picked by column | `t` (plaster, a window every third bay) |

`b` is a planted bed: flowers on a dressed-stone planter a level up. The corner, shore, rim, face-end and shadow rules
are checked on a room made for them (`topdown_suite`, "topdown terrain").

## 7. Water and foliage animation

- **Water.** Four frames at 250 ms; this is the Phase 1 view's clock. The body is still, jade-teal, with slow swells
  two steps apart. A few ripple dashes cycle, each a quarter-cycle apart: absent, then short and dim, then full with a
  pale glint, then short and shifted a pixel east. That gives a shimmer that drifts, without a conveyor-belt look.
  Foam at the shore breathes on the same clock. `03_square_water.gif` shows it.
- **Foliage.** Willow strands and bamboo leaf sprays sway 1 px on a slow 4-frame loop (bamboo 500 ms a frame, willow
  600 ms): the crown and the culms' upper halves, the strands' lower halves. Each prop starts at its own phase (from its
  cell), so a grove never moves in lockstep. Grass does not animate; a player walking through tall grass parts it
  (Phase 6 FX). Lotus flowers and buds bob 1 px on the water's clock (250 ms); the pads stay still. The frames lie side
  by side in the prop sheet (the manifest's `frames` and `frame_ms`).
- **Mist (next step).** Morning mist is a translucent mist-blue band over water and low ground, drawn at art resolution
  and scrolled 1 px at a time. It is never blurred.
- **Lights.** Lanterns carry their glow in the sprite (lantern ramp 4–5). Real `PointLight2D`s come in Phase 6.

## 8. Props

- **Scale.** Props were built for the 38 px body and stay as they are for the 46 px one (decision 43): a lantern is 30 px
  (now about shoulder-high), a barrel 18, a door 25, bamboo 60, a willow 62.
- **Form.** Every prop shows its top surface and its south face in the same ¾ view as the terrain: a barrel shows its
  lid, a crate its lid and front, a bench its seat. Its south-west footprint corner stands on the floor (`origin` in the
  manifest), and it sorts by its footprint's south edge.
- **Light.** Props are lit from the upper left, with a 1 px outline (§4). A soft floor shadow is listed in the manifest
  (`shadow`: offset and radii from the footprint corner) and drawn on the floor, not in the sprite, so a body standing
  in it is never tinted. The build draws it as a sprite of its own in the prop sheet (`shadow_rect`, placed at
  `shadow_at` from the footprint corner). The room view cuts it to the cells of the level the prop stands on, so each
  floor draws its own piece: a shadow never spills down a face or onto the water.
- **Life.** Something small and deliberate on each prop: water in the barrel, a red seal on the rice sack, an ember in
  the incense burner, papers on the notice board, a jade finial on the stone lantern.
- **Colour.** Built things are wood, granite, plaster and grey tile. Red lacquer and gold are kept for doors, posts
  and lanterns.

The kit so far: house, storehouse, willow, stone lantern, red lantern post, barrel, crates (standable), notice
board, reeds, boat, bamboo, lotus, incense burner, shrub.

Terrain v2's third part adds the foliage and garden kit: big trees with canopies, bushes, hedges, fences, rocks, a
wayside shrine, potted plants and walk-through plants (§14.12).

Chapter 2's stretch (the sects and the Reed Marsh) adds:

| Prop | Footprint | What it is |
|---|---|---|
| `hall` | 8 × 3, roof a floor 2 levels up, door columns 3–4 | a sect hall: the house's walls and roof fronted by a red colonnade (a column at every bay, gilt bracket ends under the eave), a dressed granite plinth and a jade name board in a gold frame over the door (§9: the sects' red halls) |
| `pine` | 1 × 1 | a mountain pine: a straight red-brown trunk, three flat tiers of needles held out to the sides, each lit on its upper-left rim and dark underneath |
| `weapon_rack` | 2 × 1 | a Weapon Hall's dark-wood rack: a spear with a red tassel, a jian with a gilt guard, a broad dao and a staff |
| `banner_jade`, `banner_cloud` | 1 × 1 | a sect banner on a tall pole with a gilt finial: the Jade Sect's jade silk with a gold ring, the Cloud Sect's white silk with a sky-blue cloud scroll. The tail stirs a pixel over four frames (450 ms) |
| `post` | 1 × 1 | a training stump bound with straw rope |
| `dead_tree` | 1 × 1 | a tree the Hollowing has drained: bare, split, ash grey |
| `boulder` | 1 × 1 | a karst boulder with moss in its hollows |
| `grey_reeds` | 1 × 1, walk-through | the reeds drawn by `reeds` in the Hollowing's ash grey, their heads bare |

Two ramps join the palette for them: `PINE` and `BARK`, and `HOLLOW` (colour drained to a cold ash grey with a breath
of teal in its shade); `CLOUD` is the Cloud Sect's white and sky blue. The paint table gains `m`, a wet meadow of the
Reed Marsh: the meadow's own grass with small puddles kept off the tile's edges and reed stubble (`marsh_a`,
`marsh_b`), grass for the path rule, so paths blend into it as into any meadow.

### Foes

Decision 43 brought the foes up to the character's quality (§13): the same renderer, more frames drawn to the
principles of animation, a tell of its own for each species, and larger elites and bosses. Built by
`tools/art/topdown/build_foes.py` from `tools/art/topdown/creatures.py` (the catalogue and the sheets) and
`tools/art/topdown/creature/` (the renderer's foe side, `sculpt.py`; the timing, `motion.py`; the ramps, `mats.py`;
a module a species). Before and after, in the game, and every sheet at x3: `docs/redesign/feedback/monsters/`.

- **How they are drawn.** Each creature is a small sculpture in its own frame (ellipsoids, spheres and tapered limbs,
  each with a material and a group), posed per action and frame, and cast by the character's own rasteriser and
  renderer (`figure/raster.py`, `figure/render.py`), so a foe gets all of §13's rules:
  - 4 × 4 samples a pixel, thin parts (a leg, a tusk, a strand) held unbroken;
  - the seven-step ramps leaning toward the §14 sun and shadow, from each species' side-view colours;
  - the warm rim, the cool bounce and the contact shade;
  - the outline as a dark tint of the material it bounds, a step lighter on the lit side, with half-alpha stair
    corners;
  - the lighter inner line: where a part stands in front of another (a leg over the belly, a claw over the shell, the
    head over the shoulders), the pixel behind its edge takes the nearer part's core shadow. A foe is one cast, not
    bands, so the line is found by depth.
  Patterns are painted in the creature's own frame, so they stay on the body as it rolls over: the boarlet's stripes,
  the crab's pale patches and pale underside, the snapper's plates and moss, the toad's warts, the leech's rings, the
  minnow's scales. Eyes, nostrils, tusks' glints and teeth are marks on the surface where it shows. Loose drops, dust,
  splashes and motes are laid on after the outline and take none; light (a ring of Qi, a glint) lies over anything.
- **The camera.** A foe is seen from 35° above the ground, higher than the figure's 22°, so a back, a shell or a crest
  reads. The sculpture is tilted by the difference before it is cast, which is the same picture through the higher
  camera, with the sun in its place against the view.
- **Facings.** Five are drawn (S, SE, E, NE, N); SW, W and NW mirror SE, E and NE in the room view. As the figure's rows
  (§13), each is turned a little toward the camera so a face reads (SE 48°, E 14°, NE −36° on the ground, east 0 and
  south 90), and the front and back rows a little off the axis (S 80°, N −100°), so a beast facing the camera or
  walking away shows a flank and never reads as a capsule. A foe faces where it walks, else where it aims in a fight,
  and keeps its facing until another is 12° nearer.
- **Actions** (`creature/motion.py`), every species the same catalogue:

  | Action | Frames | fps | |
  |---|---|---|---|
  | idle | 6 | 7 | loops: a breath, a look about, a twitch of the ears or claws |
  | walk | 8 | 8–16, by the species' speed | loops: its gait (a trot, a scuttle, a hop, a creep, a swim) |
  | windup | 4 | by its shortest wind-up | the tell, held from its last frame until the blow |
  | attack | 6 | 20 | 0 the launch (stretched), 1 the hit (`hit_frame`, squashed on the impact), 2 the impact held, 3–4 the follow-through, 5 settling; holds |
  | hurt | 3 | 12 | the flinch (squashed, knocked back), the recoil, the recovery; holds |
  | death | 8 | 10 | a fall that suits it, or a coming apart into motes; holds while the view fades it out |

  The wind-up's rate comes from the data: its last frame (the tell) shows within 70% of the species' shortest
  `windup_s` (`enemies.json`), so the tell is always up before the blow (`data_validation` checks it). The blow lands
  when the attack starts (`EnemyBrain`), so its hit is frame 1, 50 ms in, and its follow-through plays before the
  recovery turns it back to idle. No timing in the fight changed.
- **Squash, stretch and follow-through.** A lunge stretches along the way it goes and squashes on the impact; a hop
  squashes as it crouches and lands; the recovery overshoots and settles; hair-like parts (strands, weed, ferns, tails)
  trail the motion.
- **Scale (decision 43).** The people grow 1.2× (about 46 px from sole to crown, §13), and the foes grow with them, so a
  crab still reads as a crab beside a person and a boarlet as a young boar:

  | | Size against its sculpture | About |
  |---|---|---|
  | The rule | a foe 1.2× its earlier size | the same share of a person as before |
  | Mud crab | 1.2 | 32 px across its legs |
  | Reed rat | 1.26 | 38 px long with its tail |
  | Wild boarlet, hollowed boarlet | 1.4 | 37 px long, 24 tall |
  | Reed frog | 1.42 | 21 px long sitting |
  | Marsh leech, reed otter | 1.44 | 32 and 41 px long |
  | Mossback toad | 1.56 | 28 px long |
  | Hollow minnow | 1.5 | 31 px with its wake |
  | **An elite** (any species with elite rows) | 1.2× its species | a head larger than its kin |
  | **Trial Puppet** (a trial) | 1.58 | 51 px tall: a sparring figure a head over a disciple |
  | **Old Snapper** (an elite by role) | 1.8, 1.5× its earlier size | 77 px from its tail to its crusher, 44 tall |
  | **Hollowed eel** (a story boss) | 1.44 | rising about 58 px out of the river |

  A foe's blob shadow grows with it (the manifest's `shadow`, an elite's its own). A new foe is sized against the
  46 px person the same way: a small beast (a frog, a toad, a crab) half to two thirds of a person's height across, a
  medium one (a boarlet, an otter) about four fifths of it long, an elite 1.2× its kin, a boss by its presence.
- **Elites.** An elite (`EnemyState.elite`, a story's elite or an early surprise) draws its species' elite sheet: 1.2×
  larger, its ramps darkened toward the §14 shadow, gold eyes, and Qi burning round it in pale gold (a ring hugging its
  outline, stronger toward its top and flickering frame by frame, a fainter ring standing off it, tongues licking up
  off its back and motes rising). Every beast that can be an elite on the grid has one: the crab, the rat, both
  boarlets, the frog, the leech, the otter and the toad. The Trial Puppet, Old Snapper, the minnow and the eel have
  none; Old Snapper wears the ring of Qi in its own colours as its boss presence.
- **Sheets.** A sheet a species (`art/topdown/foes/<species>.png`), and its elite's apart
  (`<species>_elite.png`): a row per drawn facing, the 35 frames of every action along it, in a cell of its own size
  (the union of its frames). Every sheet is under 4096 px a side (phones' texture limit; the largest, Old Snapper's, is
  3395 × 490); a room loads only its own species' sheets, and an elite's only where an elite stands. The index is
  `data/topdown/foes.json` (per species its sheet, cell, feet, shadow, label height and each action's frames, rate and
  loop; an elite's under `elite`), laid into the tile set as its `foes` (`TopdownRoom.load_room`). The room view
  (`TopdownWorld.FoeView`) still draws a foe with one call.
- **Recognisable from the side view.** The ramps come from each side-view sheet (`art/creatures/`), and each has its own
  tell:
  - the mud crab: a brown shell with pale patches and a raised brow, black eyes on stalks, jade-tipped claws held up
    at its sides. Like its side-view sheet it keeps its broad side to the camera, front or back, and scuttles sideways
    on alternating sets of three legs. **Tell:** it rears back on its legs and raises both claws high and wide open,
    eyes up. It slams them shut before it (the struck side's furthest) and drags them back; beaten, it flips onto its
    pale back, its legs curling;
  - the reed rat: a grey-brown coat with a paler belly, pink ears, nose and feet, red eyes, whiskers and a green reed
    tail in segments. It scurries in bounds. **Tell:** it rears up on its haunches, forepaws up, mouth open on its
    teeth, tail lashing high. It lunges to bite and shakes its head; beaten, it topples onto its side;
  - the boarlet: a warm brown hide with the pale stripes of its youth along its back and flanks (fading over the
    rump), a high shoulder, a bristle crest, a darker head with a long snout, a pink snout disc, small tusks and
    pointed ears. It trots on diagonal pairs. **Tell:** it lowers its head and paws the ground, scraping the near
    forehoof back twice in a spurt of dust, then crouches coiled with its crest up and its ears laid back. It charges,
    tosses its tusks up on the hit and skids; beaten, its forelegs buckle and it rolls onto its side.
- **Chapter 2's stretch:**
  - the Trial Puppet: a sparring figure of carved timber on brass ball joints, rope at the wrists, the sect's jade
    sash across its chest, a jade plate on its back, a jade tuft on its crown and carved slits for eyes. It sways on
    guard and marches with its fists up. **Tell:** it twists back, drawing its right palm to its hip while the left
    reaches out, and Qi gathers in a jade ring at the drawn palm. It steps in and drives the palm out, the ring bursting
    at the knuckles; beaten, its joints give: the head drops, the knees fold, it topples, and the jade on its crown goes
    dark;
  - the reed frog: leaf green with a gold stripe down each flank and darker spots, a pale belly and gold eyes set high.
    It goes in hops: a crouch, a stretched leap, the landing squashed. **Tell:** it crouches low, hind legs coiled, and
    its throat sac puffs up big and pale. It leaps at its prey, forefeet reaching; beaten, it flips onto its back;
  - the marsh leech: a flattened olive slug in soft rings, two ochre stripes and teal spots down its back, a paler belly
    and a round pink mouth. It creeps like an inchworm, a hump travelling down it. **Tell:** it rears its front half up
    in an S, the mouth opening wide on its ring of teeth. It lunges and latches, pulsing as it drinks; beaten, it writhes
    and sags flat;
  - the reed otter: a long, sleek brown body, darker paws, a pale muzzle, throat and chest, whiskers and a thick
    tapering tail. It runs in a bounding lope, its back arching and stretching. **Tell:** it sits up on its haunches
    (as its side-view sheet does), forepaws tucked, head up, teeth bared. It drops and lunges to bite; beaten, it curls
    up on its side;
  - the hollowed boarlet: the boarlet's own sculpture with its colour drunk out of it, ash grey with pale stripes, cold
    white eyes in a pale halo and three grey strands rising and curling from its back. Beaten, it falls and comes
    apart into grey motes.
- **The tutorial rooms' other foes:**
  - Old Snapper: an ancient snapping turtle, a high domed shell grown over with moss along three knobbed keels, dark
    green plates on its flanks, barnacles on the rim and river weed trailing behind; a khaki head with a pale hooked
    beak and amber eyes that glow, and on its right the great red crusher claw with dark tips. It breathes heavily,
    works the pincer and lumbers with its shell rocking. **Tell:** it rears its front up and raises the crusher high
    over its head, gaping, the pincer wide. It slams it down in a burst of water and mud, the whole shell jolting;
    struck, it pulls its head in; beaten, it rolls onto its plated plastron, its legs pawing slower and slower;
  - the mossback toad: a fat, warty toad in olive khaki with a mat of moss and three curled fiddlehead ferns on its
    back, golden eyes under heavy lids, a cream belly and throat sac. It hops heavily. **Tell:** it rocks back on its
    haunches, cheeks and throat bulging, lids narrowing, ferns standing up, its mouth opening on its dark maw. It lashes
    a long pink tongue, a glint at its tip on the hit, and reels it in; beaten, it flops onto its back, ferns drooping;
  - the hollow minnow and the hollowed eel, the night's Hollow things, in the hollowing look: colour drunk out, grey,
    empty white eyes, grey strands. The minnow flies (the game hovers it about 24 px over the ground), so it is drawn
    round its feet, swimming through the air with two grey strands trailing as its wake. **Tell:** it curls into a C,
    tail bent hard back, and gapes. It darts in straight as a needle; beaten, it turns belly-up and comes apart into
    mist. The eel rises in an S-curve out of the river, winding sideways too so it reads from every side, with a pale
    belly, a torn fin, strands curling off its back and shedding motes of mist, and a loop of its back breaking the
    surface beside it; foam rings its body, rings spread from it and a wake trails when it glides. **Tell:** it rears
    back high, the S drawn tight, its jaws gaping wide and its eyes flaring in their halo. It lunges head-down and snaps;
    beaten, it convulses and sinks until only the stain and the rings are left. The game hovers it 20 art px over the
    water and the view draws a foe's feet at its hover, so its water is drawn that far under its feet, where its shadow
    falls.
- **Not yet drawn:** every other creature (Phase 5 by region). A species not drawn yet (an ambush, a hunter or a
  summons can bring one onto the grid) stands in with its side-view sheet at half size (`TopdownPlaces.stand_in`), as
  spirit animals do. The pebble imps do not appear in the prototype room. A new species is a module in
  `creature/` and a row of `creatures.REGISTRY`, drawn in the whole catalogue with a tell of its own.

## 9. What makes it xianxia (and Jade River's)

- **The river is jade.** Water is the game's own colour. Jade appears again only as small accents: a lantern's finial,
  the pearl on a roof crest, the character's robe.
- **River-town architecture.** Whitewashed walls in dark timber frames, grey fired-tile roofs with rib patterns and
  round tile ends, crests with curled ends, red lacquer doors between red columns, courtyard walls with tiled caps,
  granite embankments and stairs, timber piers.
- **Terraced land.** Meadows and paddies step up the valley in levels. Grass lips hang over earth banks, and pale
  karst cliffs stand behind with moss in their hollows. The height system *is* the landscape.
- **Scholar's garden plants.** Willow over water, bamboo groves, lotus on still water, flowering shrubs, reeds.
- **Quiet ritual objects.** Stone lanterns, incense burners with a thread of smoke, notice boards under little roofs.
- **Mist and light.** Morning mist over the river (§7), and lantern glow at dusk (Phase 6 day tint).
- **Later regions** keep the rules and change the materials: red sect halls and multi-eave pagodas, snow on grey
  tiles, gold-roofed immortal palaces on cloud-sea cliffs.

## 10. Tile and prop pipeline

`python3 tools/art/topdown/build_tiles.py [--check] [--review]`. Running `tools/art/build_topdown_proto.py` runs the
same build.

| File | What |
|---|---|
| `tools/art/topdown/palette.py` | the ramps (§2) |
| `tools/art/topdown/canvas.py` | pixel helpers, a coordinate hash and periodic value noise (no RNG) |
| `tools/art/topdown/tiles.py` | tops, faces, stairs, water, transitions, overlays (rims, contact and cast shade, face ends, stair cheeks) by their Phase 3 names, drawn by `terrain2.py` |
| `tools/art/topdown/terrain2.py` | Terrain v2 (§14): the macro patterns, face patterns, positional grass overlays, tint masks, decals, water frames and shore overlays |
| `tools/art/topdown/props.py` | the prop kit and its footprints, origins, animation frames and floor shadows |
| `tools/art/topdown/foliage.py` | the foliage and garden kit (§14.12): trees with their canopies and crown shade, bushes, hedges, fences, rocks, walk-through plants; `props.py` adds it to the kit |
| `tools/art/topdown/decor.py`, `build_decor.py` | the ground cover the room view scatters and its rules (§14.12), into `art/topdown/decor.png` and `data/topdown/decor.json` (`--check`, `--review`) |
| `tools/art/topdown/creatures.py` | the foes in eight facings (§8, "Foes") |
| `tools/art/topdown/atlas.py` | the atlas layout |
| `art/topdown/proto_tiles.png` | the atlas, 32 cells wide: the Phase 3 tiles in rows 0–6, the Terrain v2 sets below |
| `art/topdown/proto_props.png` | the prop kit, its frames and the props' shadows |
| `art/topdown/foes.png` | the foes: a row per species and drawn facing, the actions along it |
| `art/topdown/proto_tiles.tres` | a Godot TileSet: terrain set 0 (corners: grass, dirt, paving), terrain set 1 (sides: water), 4-frame water animations, each tile's name in custom data 0 |
| `data/topdown/proto_tileset.json` | the manifest, schema 2, which the room view reads for everything it draws: `atlas` (the sheets' files), `tiles`, `props` (with `top`, the levels of a standable top: house and storehouse 2, crates 1; `frames` and `frame_ms`; `shadow_rect` and `shadow_at`), `body`, `foes` (`cell`, `foot`, `dirs`, `mirror`, and per species its `actions` and `shadow`), `paint` (§6) and `bank_face`; plus `autotile`, `overlays` and `tileset` |

**Determinism.** Noise comes from a coordinate hash, and the PNGs are written without metadata. `--check` builds
twice in memory and fails unless every output is byte-identical. `data_validation` checks the result:

- every tile the room view draws exists;
- every tile, prop frame and prop shadow lies inside its sheet;
- every foe the room spawns has all six actions in the five drawn facings, inside its sheet;
- the house keeps its footprint;
- the TileSet loads with its two terrain sets, every tile named where the manifest puts it, and 17 animated water
  tiles.

**The room view** (`scripts/topdown/topdown_world.gd`, with the rules in `topdown_terrain.gd`) draws every rule of
this page in the game (decision 33):

- tops by their paint, every variant, with paths and paving auto-tiled under grass on their own level;
- water in its shore case, frame by frame;
- on every top its rims, contact shade and cast shade, on every face its lit and shaded ends, and the stairs' cheeks;
- each prop's floor shadow, cut to the floor it stands on;
- animated plants, each at its own phase;
- the foes in their eight facings.

The move to `TileMapLayer`s on `proto_tiles.tres` stays for Phase 4. `01_square_mock_*.png` is the approved target,
`07_ingame_square.png` the loader before this work, and `08`–`15` the game after it.

## 11. Checklist for a new tile or prop

- It uses the palette ramps, or a new ramp added to `palette.py` with its Style A tie.
- It is lit from the upper left. Faces are at most 0.65× their top's value, with a lip and a contact line.
- Tops tile with themselves, and faces tile sideways and downward.
- A prop has a footprint, an origin, `solid` and a `shadow`, and an outline except on water.
- It is built by the script, never painted by hand into the PNG. `--check` passes and `data_validation` is green.
- It is reviewed in `--review`'s sheets at ×4, and in the room: `tools/dev/topdown_capture.tscn -- --phase3` draws it
  in the game.

## 12. Review images (`docs/redesign/phase3/`)

`build_tiles.py --review` draws the sheets (04, 05, 12). The game draws the rest:
`xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . res://tools/dev/topdown_capture.tscn -- --phase3`.

| File | What |
|---|---|
| `01_square_mock_640x360.png`, `01_square_mock_x2.png` | the approved mock (decision 32): Riverside Square at the spawn camera with every rule of this page and the proposed dressing |
| `02_square_whole_room.png`, `03_square_water.gif` | the approved mock's whole room and its four water frames |
| `04_tile_sheet_x4.png` | every tile at ×4, named and grouped |
| `05_props_x4.png` | the prop kit at ×4, with its animation frames and floor shadows |
| `06_height_levels_test.png` | levels −½ to 4 with a body on each (the review room `td_review_heights`), drawn by the game, in colour and by value alone, at ×2 |
| `07_ingame_square.png` | before: the room view with the new tiles and props, without auto-tiles, rims or shadows |
| `08_ingame_square_x2.png`, `09_ingame_square_hud.png` | after: the redesigned square in the game at the spawn camera, ×2, and under the HUD |
| `10_ingame_whole_room.png` | the whole 48 × 30 room in the game |
| `11_before_after.png` | the mock, the loader before, and the game after, one above the other |
| `12_foes_x3.png` | the Phase 3 foe sheet at ×3, before decision 43 (the foes' sheets since: `docs/redesign/feedback/monsters/sheets/`, §8 "Foes") |
| `13_fight_hud.png`, `14_fight_x4.png` | a fight with two crabs, a rat and a boarlet, under the HUD and ×4 round the player |
| `15_water_frames_x2.png` | the water's four frames round the pond and the pier |

## 13. The character (decision 32)

The body in the top-down world is the game's own character, redrawn for this view:

- **Same person.** The side view's big-headed build, faces, hair styles, clothes and colours, dyes and weapons, read
  from the same data (`data/parts.json` and the save's outfit). The villagers are drawn the same way.
- **The build.** `tools/art/topdown/build_character.py` builds it, from a posed doll ray-cast at 4 × 4 samples per art
  px and resolved into pixels (decision 42: "drawn better", option B of `docs/redesign/feedback/character_quality.md`;
  decision 43: 1.2 times bigger, "I think the player should look a little bigger"). The redesign plan's "As built: Phase 3, third part" has the full
  pipeline; `figure/raster.py` and `figure/render.py` hold the rules below.
- **Layer sets.** It is drawn in sets (the body, hair, each garment slot, each weapon family), each built on its own.
  `docs/redesign/phase3/character/HOWTO.md` says how to add one.

| Rule | Value |
|---|---|
| Camera | orthographic, 22° above the ground: lower than the world's oblique, as ¾ sprites are drawn, so the face shows |
| Size | 1.104 art px per unit (`geom.WORLD_SCALE`; decision 43, 1.2 times decision 42's 0.92): about 46 art px from sole to crown, 48 with a top knot. Every pixel is cast at that density, never scaled at runtime. The technique pictures keep the 38 px figure they were approved at: the poses a picture draws (105 frames) are cast again at 0.92 (`geom.PICTURE_SCALE`, the index's `pictures`) |
| Coverage | 4 × 4 samples a pixel. A pixel takes the material most of its samples hit (thin trim, pins and blades vote extra, so a gold collar or a belt holds an unbroken line), and is solid from half covered. A `thin` material (trim, a blade, a hilt) is solid from a quarter; a `line` material (a shaft, a bow's limbs, a string, a ripple, a stroke of ink, a smear seen edge on) from a quarter too, unless it is the fainter side of a line its neighbour holds, so a line about a pixel wide stays one pixel wide and unbroken |
| Light | the world's sun, upper left and a little in front (§3). Tones come from the mean light over a pixel's samples, so tone edges follow the form. Seven steps a ramp (`render.ramp7`: the side view's five plus a core shadow and a bright step), the dark end leaning toward the §14 shadow `#241F4F`, the light end toward the §14 sun `#FFE9A6`: five lit steps, the bright step only for materials allowed it (`hi`), the top step only as a sheen or a glint (`glossy`: hair, silk ribbon, gold, blades, plate) |
| Rim, bounce, contact | a warm rim (the colour 30% toward the sun, a step up) where a form's edge turns to the sun; a cool bounce toward the sky on a shaded edge facing down; a contact shade a step down under a nearer part and beside one (an arm on the trunk, one leg against the other). Bare steel and a cape trailing flat keep a faint rim, so they keep their colour |
| Outline | 1 px, a dark tint of the material it bounds (its deepest step toward ink-teal `0E1A1E`) on the shaded lower right, a step lighter on the lit upper left, never flat black. Where a part overlaps the body the edge is the part's own core shadow, lighter than the outer line (skin a step lighter still). Stair-steps: a half-alpha outline pixel where the true edge crosses a stair's inner corner, a softer one at a convex tip; no blur. Light (a smear, a ring of sound, a string) has no outline, only its own edge tone |
| Face | lit nearly flat (the skin keeps to the shadow and base steps, no rim across it; the neck in the jaw's shade). Eyes 3 px wide and 3 tall: a lash row, the white, the pupil and the iris, the iris and its lower light; the far eye in three quarters and the eye in profile narrower; a brow, a 2 px mouth, the nose's shade in three quarters, a touch of blush (the pictures' 38 px figure keeps decision 42's face: eyes 2 px wide, a 1 px mouth). Shut eyes (hurt, a fall, meditation) are the lash row. Hair and a band hat leave the eyes clear in every pose: their samples are cut from the eyes' box a pixel round (a row higher over shut eyes), so a fringe or a nod never covers them |
| Hair | broad locks (each a groove and a lit ridge) under a sheen ring broken lock by lock on the sunlit side, a darker crown; knots and ties wound in locks; each tail lock a groove and a lit strand. Loose locks at the temples and forelocks over the brow break the cap's round silhouette, so it never reads as a helmet, and frame the face |
| Cloth | folds hang from the belt and widen to the hem, gathers over the belt and pulls toward the chest's sides, a crease at the elbow and behind the knee, a zigzag over the ankle wrap: each a groove a step down with a lit ridge beside it on the sunlit west. Only the cloth folds: trim, belts and panels stay clean |
| Colour | the side view's ramps: skin, blue eyes, the hair's six colours, the disciple tunic's navy and gold, the trousers' teal, the weapons' jade steel and gold; the dyes are the side view's own |
| Facings | S, SE, E, NE, N drawn; SW, W, NW mirrored (their light then comes from the upper right). The side rows turn a little toward the camera, the head in E a little more |
| Motion | a cut leaves a smear of pale jade light on its hit frame (no ink round it); hair and cloth trail the motion |
| Cost | the same draw calls a figure (one a layer). At 46 px the 168 sheets hold 207 MB of RGBA8 (from 139 at 38 px; 512 px wide, the tallest 1,446 px, well under the 4,096 limit), the player's outfit 8.1 MB (from 5.4); the pictures' 105 frames a set are about a tenth of that. A full build of every set takes about 6 minutes on two cores (`--jobs 2`) |

**The scale rule (decision 43).** The people are drawn 1.2 times the 38 px they were (`TopdownRoom.PEOPLE`), and
what is sized against a person follows them; the world's measures do not (a tile, a level, the walk's 154 and the
sprint's 216 world units a second, the jumps and the tops a body stands on). Sized against a person:

| What | Before (38 px) | Now (46 px) | Where |
|---|---|---|---|
| Foot box (collision) | 16 × 10 | 19 × 10 world units (across only: the feet's depth, which the stairs' side steps and a top's landing are measured by, stays) | `movement.json` topdown `box` |
| The player's body for a blow on the grid | half width 14 | 17 | `CombatAuthority.body_half_width` |
| A body's height, its chest (effects) | 76, 40 | 92, 48 world units | `movement.json` topdown.combat |
| Talk and a person's context reach | 110 | 132 world units | `WorldAuthority.reach_of` |
| Marker, bark and a lifted plate over a villager | as the side view's | 16 world units higher | `TopdownPlaces.HEAD_LIFT` |
| The label over a person who fights (a companion, a bandit) | the side view's height | 16 world units higher | `FoeView.figure_top` |
| A staged scene's balloon and emote over a head | 88 | 104 world units | `SceneStage.HEAD` |
| Blob shadow half width, the player's / a villager's | 8 / 7 | 10 / 8 art px | `ShadowView`, `Person.BLOB_RX` |
| The body kept in view, the camera's framing | 16 × 44, feet 12 px low | 20 × 52, 14 px low | `TopdownRoom.BODY_PX`, `camera_for` |
| The labels' keep-clear box round the body | 28 × 64 | 34 × 77 screen px | `TopdownWorld.layout_labels` |
| A smear's and a form's hand, a cast's chest (FX sheets) | 14, 22 | 17, 26 art px | `tools/art/fx/topdown_melee.py`, `topdown_forms.py` |

The drawn weapons grow with the hands that hold them (they are cast from the same doll); a blow's reach, a technique's
range and every speed stay the game's measures. Doors, corridors and props keep their size: every way is at least a
tile (32 world units) wide, and the foot box is 19 across. The technique pictures and the HUD's companion chip keep the 38 px
figure (`picture` frames), so they stay framed as the user approved them.

Check a new layer against it the way §11 checks a tile:

- it is cast from the same poses as the body;
- each of its materials says how it resolves and takes the light (`render.MATS`, or its Look's `mats`): a part a pixel
  or two wide is `thin` or a `line`, or it breaks up or doubles;
- it is reviewed in every action, facing and dye in `tests/topdown_figure_gallery.tscn`'s sheets, and against the
  body in `docs/redesign/phase3/character/`;
- `data_validation`'s layer contract is green.

## 14. Terrain v2 (decision 40)

Decision 40 asks for terrain that looks closer to Alabaster Dawn in Jade River's own xianxia world. The work comes in
three parts: the tiles (this section, built), then runtime light, then denser foliage and decor. **This section is the
contract for the other two parts.** Where it differs from §1–§7, it replaces them for the ground, edges, faces, water
and buildings. The props and the character keep their own rules (§4, §8, §13), except where §14.2 says so.

Before and after, in the game: `docs/redesign/terrain_v2/` (§14.10). The third part, foliage and decor, is built
to §14.12; its before and after are in `docs/redesign/terrain_v2/foliage/`. The living world (decision 43) is §14.13.

### 14.1 The look

One sun stands high in the north-west. Every lit plane has a warm yellow edge, and every shadow is a cool,
translucent blue-violet. Nothing is shaded black or grey.

- **Ground.** The ground is rich and varied: meadows with clumps, tufts, clover and wild flowers; worn flagstones
  with moss in the joints; packed earth with pebbles.
- **Large patches of light.** Big patches of sun and cloud shade drift across the large areas.
- **Edges.** Grass hangs over the path in soft tufts and casts a two-step shadow on it.
- **Cliffs.** Cliffs are rock mass: fluted limestone columns under a bright lip, with moss and vines hanging over it
  and a dark foot where the face meets the ground.
- **Water.** Water is deep jade in the middle, lighter over a visible bed at the shore, with foam at every waterline
  and a slow shimmer of ripples and glints.
- **Roofs.** Roofs are dark glazed tile whose courses sweep up at the ends.

At a glance, nothing on a 40 × 22-tile screen repeats.

### 14.2 Light: the numbers the lighting and foliage parts must use

| What | Value |
|---|---|
| Sun | One light, high in the **north-west** (upper left on screen). Lit: tops, west-facing and north-facing edges. In shade: south faces, east flanks |
| Sun colour | `SUN` **`#FFE9A6`**, laid translucently on lit edges: a west rim is 0.67 then 0.24 (`rim_w`), a face's west end 0.43 then 0.16 (`end_w`), a stair's west cheek 0.51 then 0.20 |
| Shadow colour | `SHADOW` **`#241F4F`** (blue-violet), always translucent, never black or grey |
| Cast-shadow alpha | **0.41** (`SHADOW_A` 104/255) in the body, **0.25** (64/255) on a 2–3 px stepped edge. There is no blur and no dithering |
| Cast-shadow direction | Toward the lower right. A point at height *h* art px casts its shadow at **(+0.45 h, +0.20 h)** from its foot on screen. So a 16 px step shades about 7 px of floor east of it (`shade_w`) and 3–4 px south of its face |
| Ambient occlusion | At the foot of every face: **0.59, 0.41, 0.25, 0.12** over 4 px (`AO_STEPS`), then 0.05. It lies on the floor (`ao_n`) and on the face's own last row (`face_ao`) |
| East rims, face ends | 0.59, 0.27, 0.10 over 3 px (`rim_e`, `end_e`). A stair's east cheek: 0.67, 0.35, 0.14 |
| Cast shade of a higher west cell | 0.45 → 0.08 over 6 px (`shade_w`: 116, 100, 84, 64, 42, 20) |
| Grass edge on a path | 0.44 on the first px below the edge, then 0.22; 0.28 east of it |
| Eave on a wall | 0.71, 0.51, 0.33, 0.18, 0.08 over 5 px under the soffit |
| Sun patches | `#DDF27A` (yellow-green) at **0.08**, on meadows, earth and rock only |
| Shade patches | `#0E4A58` (blue-green) at **0.12**, on the same. The manifest's `v2.tint` holds the tint colours; the room view reads them there. *Changed in the polish pass: at 0.18 and 0.17, in yellow and blue-violet, they stained the grass khaki and the paving lavender and yellow. Paving and granite take no patches* |
| Water depth | `#0C1B33` at **0.31** from two cells from land, and 0.28 more from four cells |
| Stacking cap | Where a runtime shadow falls on baked shade (AO, rims, prop shadows, patches), the total darkening stays **at or under 0.6**. Do not stack a runtime shadow on a face: faces are shaded already |

**Baked into the tiles (done, do not redo):**

- the lips and rims;
- the contact AO under faces and at their foot;
- the cast shade of a higher west neighbour;
- the grass edges' shadows, and each decal's own small shadow;
- the face shading (lit west flanks, shaded east);
- the eave's shadow band;
- the sun and shade patches;
- the water's depth, foam, glints and ripples;
- each prop's floor shadow, a sprite in the prop sheet. It now uses `SHADOW`, 0.41 in the core and 0.25 at the rim.

**Left to runtime (the next parts):**

- **Cast shadows** from tall props and buildings:
  - trees, bamboo, lanterns, banners and halls, along the direction above;
  - on the floor they stand on, cut per level as the prop shadows are (`TopdownTerrain.shadow_pieces`);
  - never on a body or a face;
  - on water at 0.25 at most.
- **Colour grade.** The tiles are graded already. A day grade may lift highlights at most 4% toward `SUN` and push
  shadows at most 4% toward `SHADOW`. There is no global saturation boost over 5%. The night tint stays `#8FA0C8`.
- **Light sources.** Lanterns as `PointLight2D`, at most four a room (plan, Phase 6).
- **Particles** at art resolution, never blurred:
  - mist over water and low ground in `MIST` `#AFC9D1` at 0.15–0.30;
  - drifting petals (`PETAL`), pollen and fireflies (`SUN`), 1–2 px.

### 14.3 Ramps (`palette.py`, the `*2` ramps)

Seven steps each, dark → light. Each dark end leans blue-violet or teal and each light end warm yellow, so a lit plane
and its shade differ in hue as well as value.

| Ramp | Steps (0 → 6) | Use |
|---|---|---|
| `GRASS2` | `123040 144A40 1B6641 2B823D 45A03A 87C749 CBE86C` | a saturated meadow: base 4, tuft blades 3, their feet 2, tips 5, glints 6 |
| `DIRT2` | `35222E 5A3531 80523B A2704A BF8E5C D8AE77 EECB98` | paths |
| `PAVE2` | `2A2330 4A3F44 6D6057 8F8170 AD9E88 C8BAA0 E3D8BE` | warm grey-beige town flagstones, stones 4 (3–5), joints 1–2 |
| `STONE2` | `1A1E33 2A3249 43506A 63728A 8594A6 ADBAC6 DDE4E6` | dressed granite, blue-grey: promenades, terraces, stairs, walls |
| `ROCK2` | `1E1D33 2F3046 474A5C 62666C 82857F A7A794 CECAAE` | karst: lit planes warm, shade violet |
| `EARTH2` | `241B2B 3A2932 553A38 714F41 8E684D AA855F C5A47A` | soil banks |
| `MOSS2` | `13283A 1A3F3E 285B42 3F7845 63964A 90B656 C4D67E` | moss, drapes, vines |
| `WATER2` | `0C1B33 0F2C44 114350 155C5A 1E7766 2F9575 5DBB93 A9E6C9` | deep → glint (8 steps); body 3 |
| `BED2` | `2F4A45 4C6F5E 6F9377 95B28C BCCDA2` | the bed seen through the shallows |
| `ROOF2` | `14131F 1F2131 2B3044 3A4458 4F5C6E 6E7D8C 9BAAB1` | dark glazed roof tile |
| `PLASTER2`, `TIMBER2`, `WOOD2`, `RED2` | see `palette.py` | walls, frames, planks, lacquer |
| `LEAFFALL`, `PETAL`, `FLOWER` | see `palette.py` | fallen leaves, blossom, wild flowers (white, gold, pink, blue, coral) |

**Value plan.** Floors sit at 0.5–0.62 mean luminance and the water at 0.28. Faces follow the rule "at most 0.65×
their top". Measured on the atlas:

| Top | Face | Ratio |
|---|---|---|
| grass | earth | 0.61 |
| rock | cliff | 0.54 |
| granite | wall | 0.55 |
| paving | wall | 0.50 |

The ground under a character stays in steps 3–5 of its ramp, so the ink-outlined bodies read on every floor.

### 14.4 Breaking the 16 px grid

Every cell is drawn as **layers**. `TopdownTerrain.top_layers`, `face_layers` and `water_layers` each return
`[tile, colour]` pairs. The Phase 3 calls (`top`, `face`, `water`, `overlays`) keep their contract and name the
TileSet's tiles.

1. **Macro patterns.** Each material is one pattern cut into tiles: 4 × 4 tiles (64 px), or 8 × 8 (128 px) for the
   paving. A cell takes the tile at its place in the pattern, `tiles[(y mod h) × w + (x mod w)]`, so a flagstone, a
   plank or a clump runs across tile edges.
   - The patterns hold only detail at the tuft scale and below (blades, grain, joints). Anything big enough to be seen
     repeating comes from the next layers.
   - **Grass** is a clean, saturated green under crisp tufts of blades, about eight to a tile: lit tips over blades
     in their own shade, a darker foot and a dark root (`TUFTS` in `terrain2.py`). The clump decals are crowds of the
     same tufts.
2. **Decals.** Small transparent tiles, drawn over the base tile:
   - which cells take one: a hash of the cell (`h01(x, y, seed + 5)`) against the mark's `decals` shares, in order;
   - which decal: a second hash (`seed + 6`);
   - `seed` comes from the room's id.

   | Set | Decals |
   |---|---|
   | grass | clumps, tufts, clover, pebbles, fallen leaves, a few flowers, petals |
   | flowers | clusters of 3–4 wild flowers |
   | dirt | stones, pebbles, cracks, leaves, a twig, weeds |
   | pave | moss cushions, leaves, petals, cracks, weeds, loose pebbles |
   | stone | lichen, cracks, moss, weeds |
   | rock | moss, mossy clumps, tufts, pebbles, cracks |
   | marsh | puddles with reed stubble |
   | wood | leaves |
   | roof | moss, a leaf |

   Each decal stays a pixel inside its tile and throws its own small `SHADOW` to the south-east (0.16–0.39).
3. **Sun and shade patches.** A whisper, on meadows, earth and rock only (paving and granite take none).
   - A value noise over the room's corners, at 7 cells and 3 cells (`TONE_SUN` 0.58, `TONE_SHADE` 0.4), marks each
     corner sunny, shaded or neither.
   - It counts only where all four cells round the corner are tops of one level whose mark takes `tone`.
   - A cell draws the **tint mask** of its corner case and place: a white shape whose edge follows noise periodic in
     64 px, softened in three alpha steps. The mask is drawn in the tint's colour.
   - One set of masks serves the sun, the shade and the water's depth.
4. **Positional grass edges.** A path or paving cell with grass at a corner takes its own base (dirt or paving) under
   the **grass overlay** of its corner case and place. The overlay's grass is the grass pattern's own pixels, and its
   edge follows noise periodic in 64 px, so it meets the neighbouring grass exactly and never repeats every 16 px.
   - **Edge light.** On the sunny north and west sides of the grass, the edge is lit and blade tips poke up. On the
     south side it is in shade and the tips hang over.
   - **Shadow on the path.** 0.44 then 0.22 below the edge; 0.28 east of it.

### 14.5 Edges, faces and height

- **Faces** are 64 px patterns in three rows: the first row with its lip, then two body rows that repeat downward. A
  face takes its tile by column (`x mod 4`) and by row.
- **Rock (cliffs):**
  - fluted limestone columns 6–12 px wide, split by dark fissures that wander a pixel either way down the face;
  - each column is shaded like a prism: a bright west edge, a lit flank, the body, a shaded east flank;
  - cracks break the columns into blocks whose tops are sunlit ledges, some with moss dripping down;
  - faint bedding lines run across.
- **The lip.** Every raised edge opens with the top's rim at its brightest step, then the top's front edge. Grass or
  moss hangs over it by 1–7 px, in clumps lit on top and shaded underneath, with blade tips, a few leafy vines on
  cliffs and roots on banks. A contact shadow of 0.63, 0.35 and 0.14 lies under the drape.
- **The foot.** The last face row over a floor darkens its bottom 4 px (`face_ao`), and the floor in front takes `ao_n`.
  Over water there is no foot shade: the shore overlay shades the water under the bank instead.
- **Materials:**
  - earth banks: wavy soil strata, rounded stones lit from the north-west, roots;
  - stone and paving walls: ashlar courses under a coping stone with a dark overhang line, moss in the lower joints;
  - the river embankment: wet dark blocks and an algae line;
  - piers: pilings lit on the west in the pier's own shadow.
- **Granite tops** are big slabs a tile deep and 16–40 px long, in blue-grey granite with a lit top edge and thin
  joints a step down, so a terrace is crisp but never looks like the darker coursed wall under it.
- **Value range.** Cliff bodies sit in the dark steps (1–2) with lit flanks at 3–5, so a cliff is the deepest thing
  on land after the water; every lip's rim is its top's brightest step warmed a third of the way to `SUN`.

### 14.6 Water

Water keeps the four frames at 250 ms and is still drawn half a level low.

- **Body.** A calm jade body (`WATER2` 3). On it, ripples on a jittered grid: a lit crest over its trough's shadow. Each
  ripple swells, peaks with a glint, drifts a pixel east and fades, a quarter-cycle apart from its neighbours. A few
  glints twinkle one frame each.
- **Depth.** The tint two and four cells from land, counted over the eight neighbours. The room's edge does not count
  as land, so rivers run on past it.
- **Shore overlay**, per side case and frame:
  - the waterline where each side shows (as in §6);
  - north and west banks stand between the water and the sun, so their shadow lies on the water;
  - south and east shallows are sunlit and show the bed (`BED2`), fading out over 6 px;
  - foam breathes at the waterline, and a ripple line leaves the shore, a pixel further each frame.
- **Corners.** Foam and a patch of shallows where land touches a cell only at a corner.
- **Pilings.** Rings spread under a pier's pilings (a water cell under a `w` cell).

### 14.7 Paving and stairs

- **Town paving.** Irregular flagstones, the scholar-garden "cracked ice" laying, in warm grey-beige stone, about a tile
  across (11–22 px, an 8 × 8 site grid in a 128 px pattern), so a body stands on two or three of them.
  - Each stone has its own tone (a few a step lighter or darker, a few with a faint sandy or blue cast), a lit
    north-west rim, a shaded south-east one, worn rounded corners, grain, and a crack now and then.
  - The joints are crisp and dark (steps 1–2), with moss and a blade or two of grass in some.
  - No sun or shade patches lie on paving: the plaza reads as well kept and evenly lit.
  - Leaves, weeds and cracks are decals, so they never repeat with the pattern.
- **Stairs.** Treads with a bright nosing and a worn, paler middle; a dark line under each nosing; a riser with a
  bounce of light at its foot. The west cheek is lit and the east cheek shaded.

### 14.8 Buildings

- **Roofs on the grid (`t`).** Dark glazed cover tiles in 4 px ribs, each a small cylinder with a glint down its sunlit
  west flank, between shaded channels. It stays an even plane you can land on (decision 29).
- **Eaves** (`roof_face_top`): round tile ends with a glint each, a dark soffit, and the eave's 5 px blue-violet shadow
  on the plaster below. Timber rails and posts are lit on the west.
- **The house, storehouse and hall props** draw their roof the same way:
  - the courses lap every 6 px, with a lit lip over a shadow line;
  - the courses, the ridge and the eave sweep up toward both ends by up to 3 px, the curve of a Jade River roof, while
    the plane stays even;
  - the far strip beyond the ridge faces the sun, a step lighter;
  - the ridge is heavy, with openwork, curled ends tipped in gold and, on a house, a jade pearl;
  - the soffit shows under the swept corners.
- **Walls.** Plaster, timber frames, lattice windows glowing warm and red lacquer doors, all in the v2 ramps.

### 14.9 For the foliage and decor part

- **Density.** Raise ground density with decals: flat marks up to 14 px, inside the tile, lit from the north-west,
  with a 0.16–0.39 `SHADOW` to the south-east.
  - A new decal goes into a set in `terrain2.decals()`, and its share into the paint table (`build_tiles.py`
    `PAINT[mark]["decals"]`).
  - Anything taller than about 6 px, or anything a body walks behind, is a prop, with a footprint, an outline (§4) and
    a floor shadow.
- **Placement.** By a hash of the cell (`TopdownTerrain.h01` with the room's seed), never a random generator, so a room
  always looks the same.
  - Keep paths and doorways readable: no decal darker than step 2 and larger than 3 px on a path.
  - Leave the ground under the spots where people stand in steps 3–5 of its ramp.
- **Colours.** Ground cover takes `GRASS2`, `MOSS2`, `FLOWER`, `PETAL` and `LEAFFALL`. Trees and shrubs keep the prop
  ramps (`LEAF`, `PINE`, `BAMBOO`) under the same sun.

### 14.10 Pipeline and review

- **Where it is built.** `tools/art/topdown/terrain2.py` draws every v2 set, and `tiles.py` keeps the Phase 3 names on
  top of it. `atlas.py` lays out both: rows 0–6 hold the contract tiles, unchanged in place, and the v2 sets go below
  them.
- **The manifest** gains `v2`:

  | Key | What |
  |---|---|
  | `macro` | per material: `w`, `h` and `tiles` |
  | `faces` | per kind: `top` and `body` |
  | `over` | the grass overlays: 14 cases × 16 places |
  | `tint_mask` | 15 cases × 16 places |
  | `tint` | the tint colours |
  | `decals` | the decal sets |
  | `water` | `macro` frames, `shore`, `corner`, `ripple` |
  | `face_ao` | the foot shade |

  Each paint mark gains `macro`, `decals` and `tone`.
- **The TileSet** still covers the contract tiles only. The v2 sets are layers the room view composes.
- **The room view** draws the floor and the water in 16 × 12-cell chunks, so the renderer skips the chunks off screen
  and water chunks off screen skip their redraws.
- **Determinism.** `build_tiles.py --check` stays byte-identical.
- **Tests.**
  - `topdown_suite` ("terrain v2") checks the layers: the pattern by place, the positional overlay, faces by column
    with the foot shade over a floor and none over water, water's frames and shore, the depth and the patches, and
    every layer in the atlas.
  - `data_validation` checks that every tile the v2 sets name is in the atlas and that every mark's pattern, decals and
    tints exist.
- **Review images.** The tile sheet at ×4 is `docs/redesign/terrain_v2/10_tile_sheet_x4.png`. The before and after
  views, drawn by the game (`tools/dev/topdown_capture.tscn -- --terrain <before|after>`), are in
  `docs/redesign/terrain_v2/before/` and `after/`, and the side-by-side pairs are
  `docs/redesign/terrain_v2/0N_*_before_after.png`.

### 14.11 Runtime light (decision 40, the second part: built)

The runtime adds what depends on the room and the hour, over the tiles' baked light, to the numbers of §14.2. Every
colour, alpha, length and count is in one const block, `scripts/topdown/topdown_light.gd` (`TopdownLight`). Retune
there and nowhere else.

| Part | Where | What it does |
|---|---|---|
| Cast shadows | `TopdownShadows` | Baked once as the room is built, into one texture in ground px; never per frame |
| Grade, night, lights, cloud shade, particles | `TopdownAtmosphere` | One node in the world viewport, per room and per hour |
| The numbers | `TopdownLight` | The contract's colours, the areas, the hours, the lights, the particle caps |

**Cast shadows.**

- **Direction.** A point *h* px high falls at (+0.45 h, +0.20 h) (`SUN_STEP`).
- **What casts:**
  - tall props (`CASTS`: trees, bamboo, lanterns, banners, posts, racks, boulders): their sprite's silhouette, each
    pixel as high as it stands over the footprint's middle, laid along the sun's step;
  - houses, halls, storehouses and crate stacks: a block of their footprint up to their standable top;
  - the grid, from two levels up (`GRID_MIN_H` 32 px). A one-level step's shadow is the tiles' own (`shade_w`,
    `ao_n`).
- **Where it lands.** Each floor takes only what stands higher than it, cut per level like the props' floor shadows.
  A shadow falls down a drop, longer by the drop. It never lies on a face or on a body.
- **Alpha.** `SHADOW` at 0.41 in the body and 0.25 on a 2 px stepped edge (`SHADOW_RIM_PX`), with no blur and no
  dither. On the water it is 0.25 at most.
- **The stacking cap** (0.6 over baked shade):
  - the first px under a face takes nothing (`ao_n`'s 0.59);
  - the next px, and the `NEAR_PX` (4) east of a higher west cell (`shade_w`), take only the edge's 0.25;
  - so does a prop's own floor shadow.
- **By the hour.** Morning 0.85, evening 0.8, and 0.35 under the moon, of full strength.
- **Bodies.** The blob under a body (the player, villagers, foes) is `SHADOW` too, its rim 0.41 and its core 0.6 at
  the player's full strength.

**The grade** is one pass over the world viewport. The HUD, the names and the effects on the overlay stay ungraded.

- Lights go up to 4% toward `SUN`, darks up to 4% toward `SHADOW`, and saturation rises by 5% at most.
- The area comes from the room's backdrop:

  | Backdrop | Grade | Lights toward | Hours |
  |---|---|---|---|
  | `valley_day` (Lotus Ferry, Stoneford, the Willow Path) | sun 4%, shade 3%, saturation +5% | `SUN` | the clock's |
  | `marsh` (the Reed Marsh) | sun 4%, shade 4%, saturation −8% | `MIST` | the clock's |
  | `sect_jade` | sun 3%, shade 3%, saturation +4% | `SUN` | the clock's |
  | `sect_cloud`, `mist_peak` | sun 3–4%, shade 4%, saturation ±0 to −5% | `MIST` | the clock's |
  | `interior`, `cave` | sun 4%, shade 3% | `SUN` | always "lamplit" |
  | `valley_dusk` (Lu's Boat) | sun 4%, shade 4% | `SUN` | always "dusk" |
  | `valley_night`, or a room with `night` | shade 4%, saturation −10% | — | always the story's night |

- Outdoors the game's clock (`Clock.time_of_day`) turns morning, day, evening and night. Each phase cross-fades into
  the next over its last 4% of the day.
- In weather (a room with a `weather` region) rain and storms take the sun out of the grade and the air, and fog
  thickens the mist.

**Night and lights.**

- After dark the world is multiplied by the night tint `#8FA0C8` (morning and evening use a faint warm tint). Light
  pools lift it back toward their own colour: stone and red lanterns, embers (incense, shrines), fires (the cooking
  pot, the forge, the furnace), jade glows (Qi springs, teleport stones) and the warm doorways of houses and halls.
- The pools are stepped discs in three bands, with a 1 px checker where one band meets the next. They are baked once
  per room into one light map, when its lights first burn.
- Each flame glows a little over the night, with a flicker. A pale light round the player's feet keeps the body
  readable.
- **This differs from §14.2's `PointLight2D`s.** A room may have any number of lights, and the cost is still one quad
  a frame. In the Compatibility renderer, each `PointLight2D` draws every item it touches again.

**Cloud shade.** Big, soft, dithered shapes in the shade patches' tint (`#0E4A58`) at 0.08 glide east-south-east
over everything by day, about one per screen of room.

**Particles** are drawn at art resolution, 1–2 px, never blurred. At most 48 are on screen (`MAX_PARTICLES`), and each
kind has its own cap:

| Kind | Cap | When and where |
|---|---|---|
| pollen motes | 14 | in sunlight (`SUN`), fewer in the marsh and the peaks, none at night or in rain |
| fireflies | 12 | at night over grass (`SUN`) |
| leaves and petals | 8 | from willows and bamboo (leaves), flowering shrubs (`PETAL`) and dead trees (ash) in view |
| mist wisps | 12 | over water and the marsh's wet meadow (`MIST` at 0.15–0.30), most in the marsh and the morning |
| glints | 6 | on sunlit water |

**Settings.**

- **"Light and particles"** (Controls, on by default) turns off the grade, the clock's hours (outdoors stays at
  midday), the cloud shade and the particles on older phones. The cast shadows stay, and so does a night room's night.
- **Reduce motion** halves the particles.

**Cost.**

- The bake takes 5–8 ms a room on a desktop, headless. Lotus Ferry, the largest room, takes the most. The first room
  also cuts the props' silhouettes, which takes about 2 ms, once.
- The cloud shade is drawn by a shader, so nothing is built for it.
- Each frame, the Atmosphere's own work is under 0.1 ms of CPU.
- On the GPU, each frame adds:
  - one grade pass at 640 × 360;
  - at most 48 particles;
  - the clouds' quads;
  - after dark, one multiply quad.
- `perf_tests`' frame and load budgets hold, measured against the same runs without it.

**Tests.**

- `topdown_suite` ("topdown light"):
  - a block's shadow by height, with the body, the edge and the cap;
  - a one-level step casts nothing;
  - a prop's silhouette;
  - a shadow falling down a drop;
  - every area's grade within the contract at every hour.
- `topdown_tutorial` (invariant 11), for every room the view builds:
  - one bake, and none while it plays;
  - the particles under their caps by day and at night;
  - a night room lit by its lanterns.

**Review images.** Before and after, drawn by the game (`tools/dev/topdown_capture.tscn -- --light
--light-tag=<before|after>`), are in `docs/redesign/terrain_v2/light/`:

- the village square by day, at the evening and at the clock's night;
- the village at night;
- the Home Lane;
- Jade Gate Street;
- the Marsh Edge with its foes;
- the height-levels room whole.

**Left for later.** Window glows on the houses, and shadows moving with the hour. The sun stands where §14.2 puts
it all day.

### 14.12 Foliage and decor (the third part, built)

The rooms were sparse: a few small props on open ground. Alabaster Dawn's outdoor scenes are dense and layered, with
big trees whose crowns overhang the paths and shade them, bushes, tall grass, flowers, mossy rocks, reeds at the water
and leaves on the ground. This part closes that gap and keeps every path readable.

**Three layers.**

| Layer | What | How it is drawn |
|---|---|---|
| Big pieces | trees, a bamboo grove, bushes, hedges, fences, rocks, a log, a stump, a wayside shrine, potted plants, tall grass, cattails, ferns, lotus pads | props, hand-placed per room in `tools/data/topdown_rooms.py` (`Layout.green`) to frame paths and edges |
| Canopies | each tree's crown | an overhang sprite over its trunk (below) |
| Ground cover | tall grass tufts, low tufts, ferns, small shrubs, wild flowers, pebbles and mossy stones, mushrooms and lingzhi, reeds, cattails and irises, and the litter under trees | scattered by the room view (`TopdownFoliage`), drawn inside the floor's chunks |

**The kit** (`tools/art/topdown/foliage.py`, built into the prop sheet by `props.py`):

| Kind | Footprint | What it is |
|---|---|---|
| `tree_camphor` | 1 × 1 | a village camphor: a broad dome of glossy leaf puffs over a thick crooked bole |
| `tree_ribbons` | 1 × 1 | the same tree hung with red prayer ribbons and wooden wish tablets, a red cloth round its bole (the wishing tree) |
| `tree_willow` | 1 × 1 | a great willow: a soft dome and a curtain of leafy strands that sway |
| `tree_plum`, `tree_peach` | 1 × 1 | plum blossom (white-pink on dark zig-zag branches) and peach blossom (deep pink over fresh leaves) |
| `tree_maple` | 1 × 1 | a maple turning red and gold |
| `tree_pine` | 1 × 1 | a great "cloud pine": flat pads of needles held out on crooked limbs |
| `bamboo_grove` | 2 × 1 | eleven culms fanning out from one clump, a spray of leaves at each top; culms and sprays sway |
| `bush`, `bush_azalea`, `bush_wide` | 1 × 1, 1 × 1, 2 × 1 | mounds of leaf puffs; the azalea covered in crimson flowers |
| `hedge_2`, `hedge_3`, `hedge_4` | n × 1 | a clipped box hedge, a row of shrubs grown into one |
| `fence_2`, `fence_3`, `fence_4` | n × 1 | a split-bamboo and timber rail fence, running east–west |
| `rock_mossy`, `rock_small`, `log`, `stump` | 2 × 1, 1 × 1, 2 × 1, 1 × 1 | karst rocks with moss cushions, a fallen mossy trunk, a sawn stump |
| `shrine_small` | 1 × 1 | a wayside earth-god shrine: red lacquer under a tile roof, a gilt tablet, peaches and incense |
| `pot_bonsai`, `pot_orchid` | 1 × 1 | a jade-glazed jar with a trained pine; a blue-and-white pot of orchids (halls and decks) |
| `tall_grass`, `cattails`, `ferns`, `lotus_pads` | 2 × 1, 1 × 1, 1 × 1, 2 × 1 | walk-through; tall grass and cattails sway, cattails stand on land or in the shallows |

**How foliage is drawn.** Leaf masses are sculpted, not painted (`puff_mass`):

- A crown is a union of ellipses filled with small leaf puffs on a jittered grid, drawn back to front.
- Each pixel is lit by its puff's own normal blended with its place in the whole crown. So the crown reads as one form
  lit from the north-west, and its puffs as the bumps on it.
- The underside lies in its own shade. A puff's south-east rim darkens where it lies over the one behind, and its
  north-west edge catches the sun. The top step of the ramp is kept for sparse glints.
- Greens keep the prop ramps (`LEAF`, `PINE`, `BAMBOO`). The blossom and autumn ramps (`PLUM`, `PEACH`, `MAPLE`,
  `AZALEA`) lean blue-violet in their darks and warm in their lights, as §14.3's do.
- Everything is outlined as a prop (§4), and every value comes from a coordinate hash.

**Canopies.** A tree has two sprites:

- **The trunk** (the prop's `rect`): the bole and its main limbs, narrow. It sorts at its footprint's south edge and
  blocks, as every solid prop does.
- **The canopy** (the manifest's `canopy`: `rect`, `at` from the footprint's south-west corner, `box`, `frames`,
  `frame_ms`) is an overhang sorted just after its trunk (key + 1/64). So it covers whoever walks under it, north of
  the trunk, and never a roof, a face or a body in front of it.
- A canopy blocks nothing and never calls the silhouette. Instead it fades to **35%** (plan §1.2) over 0.25 s while
  the player, or a foe, stands under its `box` and behind its trunk, and fades back when they leave.
- A willow's, the ribbons' and the grove's canopies play their frames on their trunk's clock.

**Shade.** A tree's floor shadow is its crown's shade, baked into the prop sheet like every prop shadow:

- the crown's solid mask (thin strands and limbs left out), squashed onto the ground round the trunk's row;
- moved along §14.2's direction by the crown's height, (+0.45 h, +0.20 h);
- plus the trunk's own cast;
- in `SHADOW` at 0.41 in the body, and 0.25 on a 2 px rim and in flecks of sun let through the leaves;
- cut to the floor the tree stands on, as every prop shadow is.

**With the runtime light (§14.11):**

- A prop with a `canopy` already carries its whole cast shadow. `TopdownLight.CASTS` lists none of the foliage kit, so
  nothing is cast twice. The kit's small pieces keep their contact shadows.
- `TopdownShadows` notes every prop's floor shadow, a tree's crown shade included, and keeps the stacking cap under it.
- The ground cover is drawn with the floor chunks, so the runtime's ground shadows lie over it.
- The particles' falling leaves and petals still come from the older kinds (`willow`, `bamboo`, `shrub`). Adding the
  new trees as sources is a line in `TopdownLight`, left to the light's owner.

**Ground cover.** Built by `tools/art/topdown/build_decor.py` into `art/topdown/decor.png` and
`data/topdown/decor.json`:

- 46 pieces, each at most 16 × 16, standing on its foot, lit from the north-west, with a small `SHADOW` to its
  south-east like a decal's.
- No outline: it is ground cover, not a prop. This amends §14.9's "taller than about 6 px is a prop" for walk-through
  cover.
- A piece never rises above its cell's top edge, so it never pokes into the row behind it.
- Grass, flowers and reeds sway a pixel east and back on their upper part (0, 1, 1, 0 over four 0.65 s frames), each
  at its own phase. A shader on the chunks that hold them does this, with no redraw.

**Where the ground cover grows** (the manifest's `biomes`, by paint mark):

| Mark | Share | Sets | Also |
|---|---|---|---|
| `g` meadow | 0.34 | tall and low grass, flowers, stones, ferns, small shrubs, mushrooms and lingzhi | patches of dense tall grass (noise over 4.2 cells above 0.63, up to 3 pieces a cell); reeds on the shore (0.6) |
| `f` flowers | 0.62 | flowers, tall and low grass | patches; reeds on the shore |
| `b` bed | 0.75 | flowers | |
| `m` marsh | 0.42 | reeds, cattails and irises, tall and low grass, a few flowers | patches; reeds on the shore (0.75) |
| `r` rock | 0.26 | moss, ferns, stones, low grass | |

- **Litter.** Round each tree (2.6 cells), 0.55 of the cells take its litter first:
  - leaves under a camphor or a willow;
  - red leaves under a maple;
  - petals under a plum or a peach;
  - needles and a cone under a pine;
  - long leaves under bamboo.
- **Blight.** Round a dead tree nothing grows: the Hollowing has drained the ground.
- **Kept clear.** Paths, paving, granite, planks, roofs and walls take none. Neither do:
  - the water, a prop's footprint and the stairs, with the row at each stair's head and foot;
  - a ring of one cell round the spawn and round every person's and thing's spot;
  - each way out's lane, from its doorway or edge to where one arrives, as wide as its span, plus one;
  - the foes' spawn points.
- **Deterministic.** A hash of the room's id and the cell (`TopdownTerrain.h01`, `vnoise`); cached per room.

**Placement rules** (`topdown_rooms.py --check`, `check_foliage`):

- A plant stands on meadow, flowers, a bed, marsh or rock. A potted plant stands on any floor, a lotus pad on the
  water, and cattails on land or in the shallows.
- Nothing stands on a kept-clear cell, a staged scene's walk (from `data/scenes.json`) or another prop.
- A tree's canopy `box` never hides a person, a thing or a way's lane behind its trunk.
- The walkable graph and every reach check stay as before: trunks, bushes, hedges, fences and rocks block, and the
  rest never does.

**Readability.**

- A canopy fades when it would hide the player or a foe. Names, markers, pickups, rings and the aim draw on the
  overlay, above every canopy.
- The ground under a body stays in steps 3–5 of its ramp: ground cover is small, sparse on paths' edges and absent
  from spots and lanes.

**Performance.**

- The scatter runs once a room: about 10 ms for Lotus Ferry's 978 pieces, then it is cached.
- The pieces are drawn inside the existing floor chunks and raised rows, so there is no node per piece. Lotus Ferry
  has about 150 view nodes for 978 pieces and 13 canopies, and loads in 190 ms with the runtime light (`perf_tests`).
- Canopies are one node each, and only those in view are tested for the fade.

**Tests.**

- `topdown_foliage_suite` (run by `rules_tests`), on every room with a layout:
  - no ground cover on a path, the water, a prop, the stairs, the spawn, a spot or a way;
  - the outdoor rooms are covered, and the scatter is the same twice;
  - every trunk, bush, hedge, fence and rock blocks, and a body walking into a trunk stops;
  - canopies and walk-through plants block nothing;
  - the decor draws in the chunks, with the sway on the GPU;
  - canopies sort after their trunks, and a canopy fades under the player and comes back.
- `data_validation` (`foliage_art_suite`): every canopy, fade box and ground-cover piece is inside its sheet, and every
  set, biome, patch and litter names what exists.

**Review images** (`docs/redesign/terrain_v2/foliage/`):

- `before/` and `after/`: the Terrain v2 views, the Willow Path, the Herb Terraces, the Pavilion Rooftops, and two
  fights under the HUD. They are drawn by `tools/dev/topdown_capture.tscn -- --terrain foliage/<before|after>`, and the
  pairs are `NN_*_before_after.png`.
- `after/rooms/`: every room on the grid whole at 1 art px.
- `props_x2.png` and `decor_x4.png`: the kit and the ground cover (`build_decor.py --review`).

### 14.13 The living world (decision 43, built)

Decision 43 asks for a world that feels alive, in the spirit of Alabaster Dawn: critters, people at work, grass that
parts, smoke, banners, vistas and interiors. Everything here keeps §14's sun (high in the north-west, lit tops and west
flanks, blue-violet shade to the south-east), its ramps, the pixel grid and nearest-neighbour drawing. Nothing here is
traced from another game.

| Part | Where | What |
|---|---|---|
| The room's life | `scripts/topdown/topdown_life.gd` (`TopdownLife`) | the wind, critters, smoke and fire, the grass's pushes, an interior's wall and sun; every number in its const block |
| Work loops | `scripts/topdown/topdown_work.gd` (`TopdownWork`) | a person's loop between work spots, their tools, stopping for the player |
| Vistas | `scripts/topdown/topdown_vista.gd` (`TopdownVista`) | the land past a room's edge, under the room |
| The data | `tools/data/topdown_life.py` → `data/topdown/life.json` | loops, who works where, extras, animals, the area's critters, hangings, vistas; the furnishings (`dress`) |
| The art | `tools/art/topdown/life.py`, `furnish.py`; `build_life.py` → `art/topdown/life.png`, `vista.png`, `data/topdown/life_art.json` | critters, puffs, tools, hangings, vista strips; the furnishings in the prop sheet |

**One wind.** It blows toward the east-south-east, the way the cloud shade glides (`TopdownLife.WIND`). Its gust
(0..1) rises and falls on two slow waves. The grass's sway holds its lean in a gust; smoke drifts along it; the
banners, the laundry line and the red paper lanterns turn their frames on the wind's clock (`wind_frame`), faster in
a gust; the sea of cloud in a vista drifts with it. A red lantern's four frames swing it a pixel either way on its
cord, and its night flame (§14.11) swings with it.

**Critters.** Original sprites at art resolution, facing east (the view mirrors them), lit from the north-west. The
village animals and the frog carry the prop outline (§4) so they read on paving and grass; the insects, the fish's
shadow, the puffs and the rings have none.

| Kind | Where | What it does |
|---|---|---|
| Sparrows (13 × 9) | flocks of 2–4 on grass, paths and paving, by day | fly in from past the view's side and glide down, hop and peck; a body within 34 px (x1.5 under a runner) sends the flock up and away, and they are dropped once off screen |
| Butterflies (7 × 4, four colours) | round the flower beds, azaleas, blossom trees, orchids, by day | flutter on a loose loop, bobbing; flee up and away |
| Dragonflies (9 × 5) | over the water by the shore, by day | hover, dart; flee in a long dart |
| Fish (a shadow, 11 × 3) | under any water | glide and turn slowly, rise in a ring now and then, dart off in a ring from a body at the bank |
| Frogs (9 × 5) | at the water's edge (the marsh most) | sit, their throats puffing; leap into the water in a ring (more at night) |
| Hens, white and russet (12 × 11) | the village's, round their home | wander and peck; scatter flapping from a body, then settle |
| A cat (14 × 10) | the village, Granny Liu's hut, the market's row | asleep; wakes and sits as the player comes, walks off if they come close, goes back to sleep |
| A dog (16 × 9) | the docks, the market, the gate, the fair | lies; sits up and wags, trots to greet the player and sits, goes home |
| Fireflies | §14.11's particles at night | drift off from the player walking among them |

- **Cheap.** At most 24 critters (`MAX_CRITTERS`), plain records with no physics and no node each: the ones on the
  ground borrow one of 12 pooled sorted nodes (so a house or a tree hides them, and they never hide the player); the
  rest draw on three shared layers (the water, the floor for the shadows of things in the air, the air). They spawn
  inside the view from the room's area table (`life.json` `critters`, by backdrop) and its own animals, and are dropped
  once 56 px off screen (an animal once its home is 150 px off). A camera jump fills the new view at once.
- **The bodies** they notice are the player, the foes in view and the people walking about (a child at play scatters
  the hens).

**People at work.** Villagers and disciples work a short loop between two to four spots, a few character actions each
(`life.json` `loops`, the figures' own actions and weapons; no new animation):

| Loop | Poses | Held or set down | Cue |
|---|---|---|---|
| sweep | guard, idle; walks slowly | a broom that swishes | dust |
| carry | kneel, idle; walks | a shoulder pole with two baskets, set down at each spot | dust |
| laundry | kneel (wash), cast (hang), idle | a basket | splashes |
| fists, sword, staff, spear | the family's combo, guard, salute | the loop's weapon (a training sword, a staff, a spear) | |
| herbs, mend, grind | kneel, idle | | leaves |
| cook | brush_write (stirring), idle | | steam |
| chop | the heavy sabre's leaping chop | a chopper (the sabre) | chips on the blow |
| hammer | swing_3 at the anvil, kneel at the forge | | sparks on the blow, at the forge |
| fish | idle, cast | a rod, its line and a bobbing float | a ring on the recast |
| watch, read, sell, pray, write, play, meditate | idle and looking round, point, salute, brush_write, run, meditate | | |

- **The leash.** Every spot lies within 2.5 tiles of the person's own spot, on their floor, each leg walked with
  nothing in the way (checked as `life.json` is built). The World authority's talk reaches 110 units round the spot
  (132 on the grid, the people drawn 1.2 times bigger), so a player standing beside a worker can always talk to them. The name, the marker and the barks follow the figure.
- **For the player.** At the player's side (the context's offer, a talk) or with the player within 72 units, a worker
  stops, sets down what they carry and turns to the player; they take up the work again 1.2 s after the player leaves.
- **A quest waiting.** Someone whose marker calls (`QuestAuthority.marker_calls`) walks back to their first spot (their
  own) and works there without leaving it, so the marker and the talk are where the quest's tracker points.
- **Extras** with no part in the story work where a room has a job and no one to do it: a fisherman on the village's
  bank and one at the marsh, a woodcutter by the watch-tower, a sweeper in the Jade street, a pupil at sword forms in
  the Cloud court. They have no label and no talk, and stop for the player like the rest.
- **Tools** are small sprites drawn with the figure (behind it when it faces away): a broom, a shoulder pole seen side
  on or end on, a laundry basket, a rod drawn as a pixel line. They are placed by the figure's own frame bounds (the
  shoulder at 0.62 of its height, the hands at 0.42), so they follow a figure drawn at another size.

**Grass that parts.** The foliage's sway shader (§14.12) also takes the bodies in view (at most 8): the player, the foes
and the people walking. A piece whose foot is within 8 px of a body's feet leans away from it, 2 px and pressed down a
pixel close in, 1 px further out; under a walking body the outer ring rustles, under a runner the whole push shivers.
Each swaying part carries its own foot on the screen in its colour's red and green (modulo 256; the vertex's own
place gives the rest), so there is still no node and no redraw per piece. The walk-through plants (tall grass,
cattails, reeds) lean their upper part a pixel or two aside from a body among them. A slash over grass throws a few
cut blades.

**Smoke and fire.** Puffs are round, lit on their north-west rim and shaded on the south-east, a 1 px checker thinning
the rim, in four sizes, tinted and faded by the view:

- chimney smoke over most houses and storehouses (a hash of their place), a puff every 0.55 s, rising 11 px a second
  and drifting with the wind as it grows and thins (3–5 s);
- incense: a thread 14 px high from every burner, wayside shrine and shrine, swaying and bent by the wind;
- steam and sparks over the cook fire, the stoves and the furnaces; smoke and sparks at the forges;
- at most 40 puffs and 32 bits (sparks, chips, blades, drops) at once.

**Interiors.** The huts, the shop and the weapon halls are furnished to say who lives there (`furnish.py`):

- Aunt Ping's: a stove, a bed, a water jar, the day's fish, rice sacks; nets and drying fish on the wall;
- Granny Liu's: a cabinet of jars, a drying rack, a stove, a mortar, a bed, baskets of herbs; bundles of herbs and a
  scroll on the wall, and her cat by the shrine;
- Old Ma's store: two cabinets of goods, sacks, bolts of cloth, a water jar; a plaque over the counter;
- the weapon halls: a forge hearth and a quench jar, a meditation mat; the hall's plaque, scrolls and a silk hanging.

The back wall's hangings sort just after the wall's row, so the people in front cover them. A window lets the sun in: a
faint warm beam (`SUN` at 0.1, added) falls from it to a patch on the floor well into the room (the window's panes, its
lattice's bars left dark), and up to 18 dust motes turn in the beams. The stoves and the forges are fires (§14.11), so
the lamplit rooms glow warm round them.

**Vistas.** A room's layout names the edges the camera may look past and how far (`vista`, from `topdown_life.py`;
`TopdownRoom.shown_rect`). The vista draws under the room, over the backdrop, and only where no room is:

- **north** (hills, peaks, the marsh): a sky paling in bands toward the horizon, and ranges rising behind the room's
  ridge in layers that slide slower than the room as the camera pans (parallax 0.1–0.4): karst pillars past a sect
  (pines on the nearer crowns), the valley's hills, the marsh's line of trees and its reeds;
- **south**, the river going on under its far bank; or a **drop** (the sects and peaks): the edge falls away in two
  rows of the terrain's own rock face (its lip and moss), into a sea of cloud with karst peaks standing out of it, the
  cloud drifting on the wind; where a way leaves by that edge its stairs go on down into the haze;
- **all round** (Lu's boat): the river's own water tiles, deepened.

The strips are 320 px wide and tile across; the farther, the paler and bluer, as §14.1's light asks. The drifting cloud
shade (§14.11) passes over the vista too.

**Settings.** "Light and particles" off keeps the critters (halved), the work and the vistas and drops the smoke's
extras, the dust, the motes and the bits; Reduce motion halves them.

**Sound.** Every moment of life raises a cue (`TopdownLife.cue_raised(name, at)`, and the positional
`Audio.world_sound("life_" + name, at)` while in view, each name at most every 0.3 s, silent until the sound bank has
it); the people walking between their spots step as the sound's own walking villagers do: `sparrow_flee`, `fish_flee`,
`frog_leap`, `frog_plop`, `hen_flap`, `cat_wake`, `dog_bark`, and `work_<cue>` for each step begun (`work_sweep`,
`work_stir`, ...) with `work_chop_hit` and `work_hammer_hit` on the blows.

**Cost** (measured headless on the shared test machine; `perf_tests` and `topdown_life_suite`): the living world's own
work is 0.5-0.7 ms a frame in Lotus Ferry, the busiest room, and in the Marsh Edge's 25-foe fight; the whole frame
about a ms more than the same room without it. At most 24 critters, 40 puffs, 32 bits and 18 motes; a calm critter
steps one frame in three; a layer redraws only when its pixels change (the plan's "As built: the living world", the
numbers in `docs/CHANGELOG.md`).

**Tests.** `topdown_life_suite` (run by `rules_tests`): every loop of every room keeps to its leash on its floor for
two minutes and moves; a worker stops for the player and works on; a marker that calls brings its person home to stay;
the view fills with critters, a sparrow flees and is dropped off screen, a hen scatters and stays near home; pushed
hard, the pools hold; the grass parts round the player and a tall plant leans; the washing turns on the wind; an
interior hangs its wall and lets the sun in; a peak's camera looks past its edge by the pad and no further; a worker's
label follows them. `data_validation` (`life_art_suite`) checks the sheets and the data's names; `topdown_rooms.py
--check` checks the spots, the furnishings and that `life.json` is current.

**Review images** (`docs/redesign/feedback/living_world/`): `before/` and `after/` (the village, a sect, the marsh,
the peaks, the market, four interiors and two nights, under the HUD at the phone's 1280 × 720, drawn by
`tools/dev/topdown_capture.tscn -- --life --life-tag=<before|after>`), and `pairs/` (six of them side by side at the
art's own size); `detail/` (close-ups x4 of each thing, `-- --life --life-detail`); `sheet_x4.png` and
`vistas_x2.png` (`build_life.py --review`).

## 15. Combat effects (decision 38)

Every blow and technique of the top-down world is drawn by `tools/art/fx/build_fx_topdown.py` into `art/fx/topdown/`
(the plan's "As built: combat animation and feel"). The rules on this page hold for them, with these additions:

- **The look rule.** Only the feel comes from the reference game: timing, hit-stop, smears, readable impacts, camera
  kick, knockback. The look is wuxia:
  - sword-light crescents with a qi trail;
  - the brush's ink stroke with dry-brush breaks and a red seal;
  - palm prints for palms;
  - the bell's rings of sound, the fan's gust with lotus petals;
  - sword formations, a golden bell over a bagua, talisman seals, runes and trigrams;
  - calligraphic impact marks;
  - the elements' Dao images: water ripples, wind petals, thunder talismans, fire lotus, earth stone, metal sword-qi.

  Nothing sci-fi or generic-fantasy: no lasers, no energy grids, no glowing tech.
- **Colour.** A family's own qi takes this page's ramps:
  - jade from the river ramp;
  - gold from the lantern ramp;
  - ink and paper, with red lacquer for the seal;
  - wind teal with lotus pink;
  - bell bronze.

  A technique takes its element's palette (`tools/art/fx/elements.py`). Every effect keeps the ink rim of the FX
  library, so it reads on grass, paving and water alike.
- **Projection.** Effects lie on the floor of the ¾ view and rise straight up from it. A floor circle is a circle.
  Five directions are drawn (E, SE, S, NE, N); the west three mirror, as the body and the foes do.
- **Pixels.** Effects are drawn at art resolution (1 art px = 1 world px), nearest neighbour, with no blur. A wide
  technique is drawn at a whole scale (×2 or ×3).
- **Timing.** A smear is few and fast: a lead-in frame, one bright contact frame, a follow-through, then the qi thins
  from the tail. The contact frame lands on the blow's hit.
