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
| Character | ~38 art px from sole to crown (40 with a top knot), feet on the anchor: about 2.4 tiles. The real character (§13) is the reference |
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
| `tools/art/topdown/tiles.py` | tops, faces, stairs, water, transitions, overlays (rims, contact and cast shade, face ends, stair cheeks) by their Phase 3 names, drawn by `terrain2.py` |
| `tools/art/topdown/terrain2.py` | Terrain v2 (§14): the macro patterns, face patterns, positional grass overlays, tint masks, decals, water frames and shore overlays |
| `tools/art/topdown/props.py` | the prop kit and its footprints, origins, animation frames and floor shadows |
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
| `12_foes_x3.png` | the foe sheet at ×3: crab, rat and boarlet, five drawn facings, every action |
| `13_fight_hud.png`, `14_fight_x4.png` | a fight with two crabs, a rat and a boarlet, under the HUD and ×4 round the player |
| `15_water_frames_x2.png` | the water's four frames round the pond and the pier |

## 13. The character (decision 32)

The body in the top-down world is the game's own character, redrawn for this view:

- **Same person.** The side view's big-headed build, faces, hair styles, clothes and colours, dyes and weapons, read
  from the same data (`data/parts.json` and the save's outfit). The villagers are drawn the same way.
- **The build.** `tools/art/topdown/build_character.py` builds it, from a posed doll ray-cast at 1 art px per pixel.
  The redesign plan's "As built: Phase 3, third part" has the full pipeline.
- **Layer sets.** It is drawn in sets (the body, hair, each garment slot, each weapon family), each built on its own.
  `docs/redesign/phase3/character/HOWTO.md` says how to add one.

| Rule | Value |
|---|---|
| Camera | orthographic, 22° above the ground: lower than the world's oblique, as ¾ sprites are drawn, so the face shows |
| Size | 0.92 art px per unit: about 38 art px from sole to crown, 40 with a top knot |
| Light | the world's sun, upper left and a little in front (§3); four lit steps of each ramp, the deepest kept for contact shade |
| Outline | 1 px, ink-teal `0E1A1E` on the shaded side and `26363A` on the lit side (§4); an edge over the figure itself takes its material's own deep tone, not ink |
| Colour | the side view's ramps: skin, blue eyes, the hair's six colours, the disciple tunic's navy and gold, the trousers' teal, the weapons' jade steel and gold; the dyes are the side view's own |
| Facings | S, SE, E, NE, N drawn; SW, W, NW mirrored. The side rows turn a little toward the camera, the head in E a little more |
| Motion | a cut leaves a smear of pale jade light on its hit frame (no ink round it); hair and cloth trail the motion |

Check a new layer against it the way §11 checks a tile:

- it is cast from the same poses as the body;
- it is reviewed in every action, facing and dye in `tests/topdown_figure_gallery.tscn`'s sheets, and against the
  body in `docs/redesign/phase3/character/`;
- `data_validation`'s layer contract is green.

## 14. Terrain v2 (decision 40)

Decision 40 asks for terrain that looks closer to Alabaster Dawn in Jade River's own xianxia world. The work comes in
three parts: the tiles (this section, built), then runtime light, then denser foliage and decor. **This section is the
contract for the other two parts.** Where it differs from §1–§7, it replaces them for the ground, edges, faces, water
and buildings. The props and the character keep their own rules (§4, §8, §13), except where §14.2 says so.

Before and after, in the game: `docs/redesign/terrain_v2/` (§14.10).

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
  across (11–22 px, an 8 × 8 site grid in a 128 px pattern), so a 38 px body stands on two or three of them.
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
