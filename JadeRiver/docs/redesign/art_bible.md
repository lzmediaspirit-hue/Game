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
  darkens the floor at its foot (`ao_n`, 4 px). A prop casts a soft oval to its south-east (the manifest's `shadow`).
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

## 7. Water and foliage animation

- **Water.** Four frames at 250 ms; this is the Phase 1 view's clock. The body is still, jade-teal, with slow swells
  two steps apart. A few ripple dashes cycle, each a quarter-cycle apart: absent, then short and dim, then full with a
  pale glint, then short and shifted a pixel east. That gives a shimmer that drifts, without a conveyor-belt look.
  Foam at the shore breathes on the same clock. `03_square_water.gif` shows it.
- **Foliage (next step).** Willow strands and bamboo leaf sprays sway 1 px on a slow 4-frame loop (400–600 ms a
  frame), with different phases per prop so a grove never moves in lockstep. Grass does not animate; a player walking
  through tall grass parts it (Phase 6 FX). Lotus flowers bob 1 px on the water's clock.
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
  in it is never tinted.
- **Life.** Something small and deliberate on each prop: water in the barrel, a red seal on the rice sack, an ember in
  the incense burner, papers on the notice board, a jade finial on the stone lantern.
- **Colour.** Built things are wood, granite, plaster and grey tile. Red lacquer and gold are kept for doors, posts
  and lanterns.

The kit so far: house, storehouse, willow, stone lantern, red lantern post, barrel, crates (standable), notice
board, reeds, boat, bamboo, lotus, incense burner, shrub.

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
| `tools/art/topdown/tiles.py` | tops, faces, stairs, water, transitions, overlays |
| `tools/art/topdown/props.py` | the prop kit and its footprints, origins and shadows |
| `tools/art/topdown/atlas.py` | the atlas layout |
| `tools/art/topdown/compose.py` | the reference renderer: auto-tile rules and light overlays in code |
| `art/topdown/proto_tiles.png` | the atlas: 32 × 7 cells |
| `art/topdown/proto_props.png` | the prop kit |
| `art/topdown/proto_tiles.tres` | a Godot TileSet: terrain set 0 (corners: grass, dirt, paving), terrain set 1 (sides: water), 4-frame water animations, each tile's name in custom data 0 |
| `data/topdown/proto_tileset.json` | the manifest, schema 2, which the room view reads for everything it draws: `atlas` (the sheets' files), `tiles`, `props` (with `top`, the levels of a standable top: house and storehouse 2, crates 1), `body`, `foes`, `paint` (a mark's tops, face kind and `keep_face`) and `bank_face`, as in Phases 1–2; plus `autotile`, `overlays` and `tileset` for what comes next |

**Determinism.** Noise comes from a coordinate hash, and the PNGs are written without metadata. `--check` builds
twice in memory and fails unless every output is byte-identical. `data_validation` checks the result:

- every tile the Phase 1 loader draws exists;
- every tile and prop lies inside its sheet;
- the house keeps its footprint;
- the TileSet loads with its two terrain sets, every tile named where the manifest puts it, and 17 animated water
  tiles.

**What the room view uses today.** Without code changes, `topdown_world.gd` (Phases 1–2) draws with the new art,
because it reads everything from the manifest. It uses:

- each paint mark's first two tops, and its faces;
- the four water frames and the stairs;
- the redrawn props, whose roofs and crate lids are standable tops.

It does not yet draw:

- the path and shore auto-tiles;
- the rims, `ao_n`, `shade_w` and face end rims (it draws its own 1 px side rim);
- the prop shadows;
- the further top variants.

`compose.py` does all of these. It is the spec for the loader work: either a small patch to `top_tile` / `WaterView`
once Phase 2 has landed, or the move to `TileMapLayer`s on `proto_tiles.tres` in Phase 4.
`07_ingame_square.png` shows the loader today, and `01_square_mock_*.png` shows the target.

## 11. Checklist for a new tile or prop

- It uses the palette ramps, or a new ramp added to `palette.py` with its Style A tie.
- It is lit from the upper left. Faces are at most 0.65× their top's value, with a lip and a contact line.
- Tops tile with themselves, and faces tile sideways and downward.
- A prop has a footprint, an origin, `solid` and a `shadow`, and an outline except on water.
- It is built by the script, never painted by hand into the PNG. `--check` passes and `data_validation` is green.
- It is reviewed in `--review`'s images at ×1 and ×2, next to the character.

## 12. Review images (`docs/redesign/phase3/`)

| File | What |
|---|---|
| `01_square_mock_640x360.png`, `01_square_mock_x2.png` | Riverside Square at the game's spawn camera, with every rule of this page (the target), and the proposed dressing (bamboo, lotus, red lanterns, incense, shrubs) |
| `02_square_whole_room.png` | the whole 48 × 30 room |
| `03_square_water.gif` | the four water frames |
| `04_tile_sheet_x4.png` | every tile at ×4, named and grouped |
| `05_props_x4.png` | the prop kit at ×4 |
| `06_height_levels_test.png` | levels −½ to 4 with a body on each, in colour and in grey, at ×2 |
| `07_ingame_square.png` | the room view (with the Phase 2 fight) drawing the new art in the game |

## 13. The character (decision 32)

The body in the top-down world is the game's own character, redrawn for this view:

- **Same person.** The side view's big-headed build, faces, hair styles, clothes and colours, dyes and weapons, read
  from the same data (`data/parts.json` and the save's outfit). The villagers are drawn the same way.
- **The build.** `tools/art/topdown/build_character.py` builds it, from a posed doll ray-cast at 1 art px per pixel.
  The redesign plan's "As built: Phase 3, second part" has the full pipeline.

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
