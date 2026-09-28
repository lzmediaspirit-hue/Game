# Art bible · the top-down world

This page sets how the top-down world of Jade River is drawn: terrain, height levels, water, plants, buildings and
props. It serves Phase 3 of `docs/redesign_top_down_plan.md` and decision 31 in `docs/roadmap_master_ui.md` §6.
Characters follow `docs/art-contracts.md` and `AGENTS.md`; this page gives only their scale against the tiles.

**The brief (decision 31).** The world should look close to Alabaster Dawn's: bright, detailed ¾ top-down pixel art.
Height levels read at a glance, wall faces stand apart from floor tops, shading is soft, tiles are lush and props are
lively. The theme stays xianxia and Jade River's own: river towns, terraces, pagodas, lotus, mist, jade, bamboo, grey
tile roofs and red lacquer.

**Inspiration only.** Every tile, prop and name here is drawn and named for Jade River. Nothing is traced, sampled,
recoloured or rebuilt from another game's tiles or sprites. The reference game sets a *quality bar* and a
*readability goal*. Where this page describes "the style", it describes our own rules.

Built by `tools/art/topdown/build_tiles.py`. The style review images are in `docs/redesign/phase3/` (§12).

---

## 1. The look in one paragraph

A sunny river town seen from a high, slightly tilted view. Floors are bright and warm, and every raised level has a
clearly darker, cooler face under it. A thin sunlit lip sits on top of each face, and a soft teal shade lies at its
foot. The ground is full of small detail at the 1–3 px scale: blades, pebbles, stone joints with moss, tile ribs.
Nothing is noisy at the 16 px scale. Large areas stay calm, so characters and interactables always stand out. Colour
comes from the materials (jade water, green meadows, warm stone, grey tiles), not from lighting effects. The saturated
accents (red lacquer, lantern gold, lotus pink) are rare and mark places of interest.

## 2. Palette

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
| Character | ~38 art px tall in a 64 × 64 cell, feet on the cell's anchor: about 2.4 tiles. The placeholder body is the reference |
| Doors | 2 tiles wide in the wall, 24–28 px tall, so a 38 px body reads as fitting through |
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

- **Scale.** Props are built for the 38 px body. A lantern is 30 px (chest-high plus cap), a barrel 18, a door 25,
  bamboo 60, a willow 62.
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

Built by `tools/art/topdown/creatures.py` into `art/topdown/foes.png`, one row per species and drawn facing:

- **Facings.** Five are drawn (S, SE, E, NE, N); SW, W and NW mirror SE, E and NE in the room view. A foe faces where
  it walks, else where it aims in a fight, and keeps its facing until another is 12° nearer.
- **Actions.** The side view's catalogue (`data/creature_art.json`), each at its own rate:

  | Action | Frames | fps | |
  |---|---|---|---|
  | idle | 4 | 6 | loops |
  | walk | 4 | 10 | loops |
  | windup | 2 | 8 | holds its last frame |
  | attack | 3 | 12 | the strike on frame 1 (`hit_frame`); holds |
  | hurt | 2 | 10 | holds |
  | death | 4 | 8 | holds while the view fades it out |

- **Scale.** The crab and the rat are small (about 24 px across, and 30 px long with its tail); the boarlet is medium
  (about 28 px long), against the 38 px body. Each has a blob shadow of its own width.
- **How they are drawn.** Each creature is a small sculpture of ellipsoids in its own frame, posed per action and
  frame. It is seen from a camera to the south, 35° above the ground, and lit from the upper left like the props.
  Every pixel takes a step of its material's five-step ramp by its light. A part tucked behind a nearer part goes one
  step darker along the seam, so legs, claws and bodies separate by value, not by lines. Eyes, noses, tusks, the
  crab's pale shell patches and the boarlet's dust are marks placed on the surface. The sprite takes the prop outline.
  No randomness, so the build stays byte-identical.
- **Recognisable from the side view.** The ramps come from each side-view sheet (`art/creatures/`):
  - the mud crab: a brown shell with pale patches, black eye stalks, jade-tipped claws held up at its sides. Like
    its side-view sheet it keeps its broad side to the camera, front or back, and scuttles sideways; it strikes with
    the claw on the side it faces;
  - the reed rat: a grey-brown coat, pink ears and feet, red eyes, a green reed tail in segments;
  - the boarlet: a warm brown hide with pale stripes along its back, a bristle crest, a darker head, a pink snout and
    small tusks. It lowers its head and paws the ground in its wind-up.
- **Chapter 2's stretch** adds five, each from its side-view sheet:
  - the Trial Puppet: a sparring figure of carved timber on brass ball joints, the sect's jade sash across its chest,
    a jade plate on its back and a jade tuft on its crown. It walks with its fists up, draws its right fist back in the
    wind-up and drives it out with a ring of Qi at the knuckles. About 34 px tall, a little shorter than a disciple;
  - the reed frog: leaf green with a gold stripe down each flank, a pale belly and gold eyes set high. It hops as it
    goes, crouches in its wind-up and leaps;
  - the marsh leech: an olive slug in soft rings with teal spots and a round pink mouth. It creeps in a travelling
    ripple, rears in its wind-up and lunges, mouth first;
  - the reed otter: a sleek brown body, a pale muzzle and throat, whiskers and a thick tapering tail. It bounds, sits up
    on its haunches in its wind-up and lunges to bite;
  - the hollowed boarlet: the boarlet's own sculpture with its colour drunk out of it, ash grey with pale stripes,
    cold white eyes and three grey strands rising and curling from its back.

  The cell grows to 48 × 56 with the feet at (24, 42), so the puppet fits; the first three foes are drawn as before.
- **Not yet drawn:** every other creature (Phase 5 by region). The tutorial rooms' hollowed eel and minnow (the night),
  Old Snapper and the mossback toad still take the crab's figure, the view's fallback. The pebble imps do not appear
  in the prototype room.

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
| `tools/art/topdown/tiles.py` | tops, faces, stairs, water, transitions, overlays (rims, contact and cast shade, face ends, stair cheeks) |
| `tools/art/topdown/props.py` | the prop kit and its footprints, origins, animation frames and floor shadows |
| `tools/art/topdown/creatures.py` | the foes in eight facings (§8, "Foes") |
| `tools/art/topdown/atlas.py` | the atlas layout |
| `art/topdown/proto_tiles.png` | the atlas: 32 × 7 cells |
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
| `12_foes_x3.png` | the foe sheet at ×3: crab, rat and boarlet, five drawn facings, every action |
| `13_fight_hud.png`, `14_fight_x4.png` | a fight with two crabs, a rat and a boarlet, under the HUD and ×4 round the player |
| `15_water_frames_x2.png` | the water's four frames round the pond and the pier |
