# Jade River creature art toolkit

Deterministic Python tools that draw creature sprite sheets that satisfy
`docs/art-contracts.md`. You describe a creature as articulated vector parts
(ellipses, limbs, polygons, ASCII stamps) with hand-picked colour ramps. The toolkit
rasterises the parts at native art resolution, cel-shades each one from the upper-left
light, outlines the silhouette, upscales ×2 with nearest neighbour, and writes the sheet
and the manifest entry.

```
tools/art/
  pixel.py               toolkit (Canvas, materials, primitives, FX, sheets, review)
  build_creatures.py     CLI: build + check + review sheets
  creatures/<id>.py      one module per creature: SPEC + draw(cv, action, frame)
art/creatures/<id>.png   output sheets (cell*6 square, RGBA)
data/creature_art.json   manifest (merged, keys sorted, 2-space indent)
```

Requirements: Python 3.10+, Pillow, numpy. No randomness. A rebuild produces
byte-identical PNGs and JSON.

## Quick start

```bash
python3 tools/art/build_creatures.py                      # build every creature
python3 tools/art/build_creatures.py wild_boarlet         # build one (or several)
python3 tools/art/build_creatures.py wild_boarlet --no-write \
        --frames idle:0,windup:2,attack:2                 # review only + close-up
```

Each run prints the sheet size and any **contract warnings**, and exits with status 1
if a check fails. It writes these review images to the review folder (`--review DIR`;
the default is the session scratchpad `art_review/`):

| file | what it is for |
|---|---|
| `<id>.png` | every frame at 2× zoom on the dark `#0A2027` and earthy `#8a7a58` backgrounds, with a ground line and a red tick under `hit_frame` |
| `all_creatures.png` | every built creature at in-game 1× size (readability check) |
| `creatures_lineup.png` | idle frame 0 of each creature beside the player, standing on one ground line (scale check) |
| `<id>_frames.png` | `--frames` close-up at 8× for pixel-level inspection (add `--hollow` to preview a Hollow variant) |

Open the review images and actually look at them (both backgrounds, 1× and zoomed)
before you call a creature done.

## Contract recap (see `docs/art-contracts.md`)

* 1 art px = 2×2 screen px. Canvas side = `cell // 2` art px: 64 for cell 128 (small and
  normal creatures), 96 for cell 192 (large creatures and elites), 128 for cell 256 (bosses).
* Right-facing only. Rows: `idle 4f`, `walk 6f`, `windup 3f` (the held tell), `attack 4f`
  (damage on `hit_frame`), `hurt 2f`, `death 5f`. Unused columns stay transparent.
* Anchor = ground contact between the feet, normally `[cell/2, cell - cell/8]`.
  Flying creatures anchor at the body centre and set `"flying": true`.
* Keep at least 2 art px of empty margin on every side of every frame.

## Concepts

### Canvas and coordinates

`Canvas` is one frame at art resolution. `x` increases to the right and `y` increases
downwards. The pixel `(i, j)` has its centre at `(i + .5, j + .5)`: a shape centred on
`.5` gets an odd pixel width, a shape centred on `.0` gets an even width.

* `cv.gx, cv.gy`: the anchor in art px. `gy` is the ground line.
* `cv.ground` = `gy - 1.5`: the centre of the last row that feet may fill. End feet
  and limb tips here. The outline pass adds row `gy - 1`, which is the lowest opaque row.
* `cv.opacity`: stepped frame opacity for death fades (for example 0.6, then 0.3).
* `cv.snap_ground = True`: `finish()` shifts the frame by whole pixels so that its
  lowest body pixel lands on the ground row. Use it for tumbling or lying poses.
* `cv.hollow = True`: renders the Hollow variant (see below).

### Materials (colour ramps)

A `Material` has four tones, `light / base / shadow / deep`, plus an `outline` colour
and an optional `accent`. Pick them by hand with `px.material(name, light, base,
shadow, deep, outline=...)` for final art. `px.ramp(base)` auto-builds a hue-shifted
ramp for blocking. `mat.step(1)` returns the same ramp one tone darker, which suits
seams and creases drawn as decals. `px.flat(colour)` is a single-colour material.
`px.ELEMENTS[...]` holds starter ramps for each element, and `BONE`, `HORN`,
`FLESH_PINK`, `DUST` and `WATER_FX` are common extras.

Shade by hue-shifting: lights move toward warm ochre or pale gold, and shadows move
toward cool blue-green or violet-grey. Never shade by darkening to black alone. The
outline is a very dark, slightly tinted version of the region (`#071015` ink family).
The contract asks for "4–8 purposeful colours per sprite". This toolkit reads that as
**4–8 material ramps per creature** (each ramp has 4 tones), plus 1–2 accent colours.
Reuse ramps across parts and never add near-duplicate colours. The four example
creatures use 20–51 unique colours per frame, while the composited player sprite has
about 200.

### Shading

Every primitive knows its surface normals: ellipses shade like spheres, limbs like
cylinders, and polygons like a distance-field dome. The toolkit takes the dot product
of the normal with `px.LIGHT` (upper-left, frontal) and quantises it with the
material's `thresholds` into the four tones. It then removes orphan pixels (a tone
pixel with no same-tone 4-neighbour). `shade=` remaps the four bands:

| shade | tones used | use for |
|---|---|---|
| `"full"` | light, base, shadow, deep | big forms (default) |
| `"soft"` | light, base, shadow | small parts, FX |
| `"nolight"` | base, shadow, deep | parts turned away |
| `"two"` | base, shadow | limbs, plates, small details |
| `"dark"` | shadow, deep | far-side limbs, which sell depth |
| `"flat"`, `"flatdark"`, `"flatlight"` or an int | a single tone | details |

`bulge` (below 1 is flatter, above 1 is rounder) scales the normals.

**One form, one highlight:** combine overlapping shapes with
`cv.draw_geom(cv.union(g1, g2, ...), MAT)`, where each `g` comes from
`cv.geom_ellipse / geom_limb / geom_polygon`. Otherwise each ellipse gets its own
highlight and the body looks lumpy.

### Primitives (all coordinates pass through the current transform)

```python
cv.ellipse(cx, cy, rx, ry, mat, angle=0, **kw)     # angle in degrees, CCW
cv.circle(cx, cy, r, mat, **kw)
cv.limb([(x, y), ...], radii, mat, **kw)           # rounded, tapered poly-line
cv.capsule(p0, p1, r0, mat, r1=None, **kw)
cv.polygon([(x, y), ...], mat, **kw)
cv.rect(x, y, w, h, mat, **kw)
cv.line(p0, p1, colour_or_mat, **kw)               # 1 px Bresenham
cv.pixel(x, y, colour) / cv.pixels([(x, y), ...], colour)
cv.stamp(["gk", "kk"], x, y, {"g": GLINT, "k": INK})   # ASCII pixel art, NN transformed
cv.eye(x, y, size=2, state="open"|"angry"|"squeeze"|"closed"|"dead", iris=None, hollow=False)
cv.fill(mask, mat, normals=None, **kw)             # any boolean mask
cv.draw_geom(geom, mat, **kw)                       # geom = (mask, nx, ny, nz)
cv.union(*geoms, weights=None) -> geom
cv.geom_ellipse(...), cv.geom_limb(...), cv.geom_polygon(...) -> geom
cv.mask_ellipse(...), cv.mask_limb(...), cv.mask_polygon(...) -> bool mask
cv.mask_of("part_name") -> bool mask of pixels owned by that part
```

Keyword arguments common to every primitive:

* `name=`: a part name, used by `clip=` and `mask_of()`. Name eye pixels `"eye"` so that
  Hollow mode can find them.
* `sep=True | "deep" | colour`: draws a 1 px separation line on the parts underneath,
  around the new part (a near leg over the body, a claw over the shell). `True` uses
  the new part's outline colour; `"deep"` uses the darkest tone of the part below.
* `decal=True`: paints only over existing pixels and **inherits their light band**.
  Spots, stripes, moss, seams and inner ears then follow the surface's shading. Pair it
  with `clip="part"`.
* `clip=`: a part name, a list of names, or a mask to restrict drawing to.
* `minus=`: one mask or a list of masks to cut out of the shape before shading (for
  example a flat shell bottom).
* `under=True`: draws only where the canvas is still empty. `erase=True`: cuts the
  shape out and leaves it transparent.

### Transforms

```python
with cv.xform(px.rotate(deg, pivot), px.translate(dx, dy), px.scale(sx, sy, pivot)):
    ...   # geometry is transformed BEFORE rasterising: crisp, no resampling
```

Angles are counter-clockwise on screen, so positive is nose-up for a right-facing
creature. Transforms nest like a scene graph. Also available: `px.flip_y(y)` (roll
onto the back while the head stays on its side), `px.flip_x(x)`, `cv.tp(point)`
(local point to canvas), `px.rot_pt`, `px.polar(p, deg, length)` (90 = up),
`px.lerp_pt`, and `px.ik2(root, target, l1, l2, bend)` (2-bone elbow or knee). Because
shading happens after the transform, a rotated or flipped part is still lit from the
upper left. `px.rotate_nn(img, deg, pivot)` rotates an existing raster with
nearest-neighbour sampling.

### Outline, layers, FX

`cv.finish()` outlines the body silhouette. Each outline pixel takes the `outline`
colour of the material it touches (priority below > right > left > above). The
outline uses 4-connectivity, so corners stay round.

FX go on separate layers. `fx = cv.layer(above=True, outline=True)` is outlined on
its own, so FX never merge into the body outline. Helpers:

* `px.dust(fx, x, y, t, size, direction)`: ground puff; `t` is its life from 0 to 1.
* `px.splash(fx, x, y, t, size)`: water crown and droplets.
* `px.impact(fx, x, y, size)`: 4-ray hit spark. Put it on a layer with `outline=False`.
* `px.speed_lines(fx, x, y, length, count, spacing, direction)`: use
  `layer(above=False)` to keep the lines behind the body.
* `px.glow_ring(fx, cx, cy, r, colour, thickness, inner)`: Qi charge ring.

### Pose tables

```python
DEFAULTS = dict(bx=0, by=0, head=0, eye="open", ...)
POSE = px.poses(DEFAULTS, {"idle": [ {...} x4 ], "walk": [ x6 ], "windup": [ x3 ],
                           "attack": [ x4 ], "hurt": [ x2 ], "death": [ x5 ]})
p = POSE(action, frame)   # SimpleNamespace, frame dict merged over DEFAULTS
```

`px.poses` refuses a table whose frame counts differ from the contract.

### Sheets, checks, manifest, review

`build_creature(mod_or_id)` renders every frame, assembles the sheet
(`assemble_sheet`), checks the contract (`check_frames`), and writes the PNG with
`save_png`, which writes no metadata. It merges the manifest with `update_manifest` and
returns `(sheet, warnings, frames)`. The checks are:

* every frame keeps the 2 px margin;
* non-flying creatures put their lowest body pixel (FX excluded) exactly on `gy - 1`,
  except for frames listed in `SPEC["airborne"]`, for example
  `[["attack", 0], ["attack", 1]]` for a leaping bite;
* no stray pixels.

Review helpers: `contact_sheet(ids, out_path, zoom=4)`, `lineup(ids, out_path,
reference=None)` and `frame_strip(id, [(action, frame), ...], out_path, zoom=8,
hollow=False)`.

## How to add a creature

1. **Copy the closest example** in `creatures/` and rename it `<id>.py`:

   | example | use it as a starting point for |
   |---|---|
   | `reedtail_rat` | small quadrupeds and lunge biters |
   | `wild_boarlet` | chunky quadrupeds and chargers, with a dust tell |
   | `mudshell_crab` | 3/4 front view, many legs, claws |
   | `old_snapper` | large elites, `px.ik2` arms, big windups, splash FX |

2. **Fill in `SPEC`**: `id` (must equal the file name), `cell` (128, 192 or 256),
   `anchor` (normally `[cell/2, cell*7/8]`), `flying`, `hit_frame` (0–3) and optionally
   `airborne`.

3. **Pick the palette**: one `px.material` per part family (body, belly or underside,
   limbs, accents, eyes). Start from the element family:

   | element | hues |
   |---|---|
   | water | teal / blue (`#2C9E8F`, `#32BED1`), shadows toward deep teal `#15514F` |
   | earth | ochre / brown / stone grey (`#9A6A35`, `#c9985a`); shadows violet-brown |
   | wood | greens (`#5f9a45` … `#23443a`), lights toward yellow-green |
   | fire | orange / red (`#f08a3a`, `#c24a32`), lights toward pale gold `#FFE6A1` |
   | wind | white / pale blue (`#dcecf2`, `#AFC9D1`), shadows toward slate blue |
   | thunder | deep blue `#3552a8` with a yellow accent `#ffd84a` |
   | soul | violet `#9B78D1` family |
   | hollow | grey-white `#87949A` family, empty white eyes (use `cv.hollow`) |

   The element can be an accent rather than the whole body: the mud crab carries
   **teal claw tips** for Water. Keep 4–8 colours and make sure the creature reads on
   both review backgrounds.

4. **Block the silhouette in idle frame 0 first**, back to front: far limbs (`"dark"`),
   tail, body (`union`), near limbs, head group, ears, eyes. Keep all geometry relative
   to a body centre `C` computed from `cv.gx`, `cv.ground` and the pose offsets. Check
   the size against the player (about 50 art px tall) in `creatures_lineup.png`.

   | creature | height in art px |
   |---|---|
   | crab | 14–18 |
   | rat | about 14 |
   | boarlet | about 22 |
   | tortoise | about 30 |
   | elite turtle | about 38–40 |
   | ape or golem | 50–56 |
   | boss | up to 110 |

5. **Add details as decals**: spots, stripes, seams (`mat.step(1)`), inner ears,
   moss, belly. Use `sep=` only where two forms really overlap.

6. **Eyes last**. Stamp them (`cv.stamp` / `cv.eye`) with `name="eye"`. Give every eye
   a glint pixel at the upper left and keep a ring of body colour around it; it must
   not touch a separation line. Use expression states: `angry` (a brow slanting down
   toward the snout) for windup and attack, `squeeze` for hurt, `dead` (an X) for death.

7. **Write the pose table**, then look at the whole contact sheet:

   | action | what it should show |
   |---|---|
   | idle | breathing (0.3–0.7 px swell), 1 px bob, tail or ear or claw twitch; subtle, no drift |
   | walk | alternating legs (diagonal pairs or tripods), a 1 px bob on the passing frames, feet planted on contact frames |
   | windup | an obvious tell that grows over 3 frames and is **held** on the last one: rear back, crouch, raise the claw, lower the head, dust, glow, angry eyes |
   | attack | a fast strike; the biggest extension or contact is on `hit_frame`, with an `impact` spark, then a recovery frame |
   | hurt | recoil away from the hit (move left), squeezed eyes, ears or head back |
   | death | collapse (or flip over), then lie still or fade with `cv.opacity = 0.6`, then `0.3`; use `cv.snap_ground` for lying poses |

8. **Build, look and fix**: `python3 tools/art/build_creatures.py <id>`. Fix every
   warning, then work through the checklist below.

## Self-review checklist

- [ ] The silhouette is recognisable in solid black at 1×, with no mushy blobs.
- [ ] Idle frame 0 sits at the right scale beside the player (`creatures_lineup.png`).
- [ ] Light comes from the upper left everywhere, including flipped and rotated frames.
      Each big form has one highlight cluster.
- [ ] Colour clusters are deliberate: no noise, no 1 px speckles, no banding stripes
      across a form (for example a limb cylinder drawn *over* the body).
- [ ] The 1 px dark outline is everywhere. Separation lines appear only where forms
      overlap, and never touch an eye.
- [ ] The eyes are readable and expressive in every state; the glint sits top left.
- [ ] The feet are on the ground line in every non-airborne frame (the build checks this).
- [ ] The walk loops cleanly (frame 5 leads into frame 0) and the idle loops without drift.
- [ ] The windup tell is readable at 1× and held on its last frame. The hit frame is
      the moment of contact.
- [ ] The creature fits with a 2 px margin (FX included), with no stray pixels, no
      anti-aliasing and no semi-transparent pixels (except whole-frame stepped fades).
- [ ] It reads on both review backgrounds (`#0A2027` and `#8a7a58`).
- [ ] Two consecutive builds are byte-identical (no randomness; use `px.hash01` if you
      need variety).

## Lessons learned (common pitfalls)

* **Limbs drawn over the body make dark stripes.** A cylinder's shadow band lands
  inside the torso. Draw legs *before* the body and let the body hide the thighs. Draw
  a limb in front only when it really crosses the body (a pawing foreleg, a claw), and
  give it `sep=`.
* **Multiple ellipses give multiple highlights.** Use `cv.union(...)`.
* **Thin legs are mostly outline.** A 1 px leg with its outline reads as a dark
  hairline, and six of them look spidery. Use radii of at least 1.0 near the body,
  lighter leg ramps, and fan the lower segments outward at different angles.
* **Symmetric open pincers look like ears.** Keep the fixed finger in line with the
  palm and swing only the movable finger (see `old_snapper._claw`).
* **Long straight arms look like poles.** Solve the elbow with `px.ik2` and keep
  segment lengths close to the reach you need.
* **FX in front of legs look like socks.** Place dust behind the hoof it comes from,
  keep it small and lumpy, and outline it with its own darker tone (`DUST.outline`).
* **Mirroring vs rotating.** `rotate(180)` turns the creature to face left. To put it
  on its back while it keeps facing right, use `flip_y`.
* A flipped or rotated frame's lowest point is hard to predict, so set
  `cv.snap_ground = True`.

## Hollow variants

The contract gives Hollow creatures a grey-white body, empty white eyes and the same
silhouette as the living form. Use a thin wrapper module:

```python
# creatures/hollow_reedtail_rat.py
import reedtail_rat as base

SPEC = dict(base.SPEC, id="hollow_reedtail_rat")

def draw(cv, action, frame):
    cv.hollow = True          # grey-white ramps, parts named "eye" become empty white
    base.draw(cv, action, frame)
```

FX layers keep their colours. Preview a Hollow variant with
`build_creatures.py <base_id> --no-write --frames idle:0 --hollow`.
