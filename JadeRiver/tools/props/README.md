# Prop, building and tile generators

Deterministic Python (3.11 + Pillow + numpy) pixel-art generators for world props,
interactables, village buildings, interior tiles and water tiles.

```
python3 tools/props/build_props.py            # everything -> art/props, art/tiles, data/prop_art.json
python3 tools/props/build_props.py --only well,shrine   # quick iteration (no manifest write)
```

Contact sheets are written to `--review-dir` (default: the session scratchpad `art_review/`).
Re-running produces byte-identical PNGs and JSON.

## Layout

| File | Purpose |
|---|---|
| `pixlib.py` | Canvas, crisp masks (rect/ellipse/poly/line/curve), seeded value noise, bevel/cylinder/sphere cluster shading with ramps, despeckle, hue-aware outlines, stepped (no-blur) glow |
| `palette.py` | Contract tokens + hue-shifted material ramps (stone, moss, lacquer, wood, roof, gold, jade, water, ...) |
| `parts.py` | Reusable parts: faceted rocks, moss, grass, planks, glazed roofs, lanterns, flames, smoke, motes, vessels |
| `registry.py` | `@prop(id, w, h, states=..., ground=..., kind=..., repeat=...)` registration |
| `defs_*.py` | One draw function per prop: `draw(state, frame) -> Canvas` in art pixels |
| `build_props.py` | Renders sheets (x2 nearest), writes manifest + contact sheets |

## Conventions

* Sizes are art pixels; every sheet is saved at native scale 2.
* One column per frame; states are consecutive columns (`col`, `frames`, `fps`).
* Anchor = bottom centre on the ground-contact line. `ground` (art px, default 2) is the
  room left below that line for the contact shadow, so e.g. `shrine` 40x56 has
  `anchor [40, 108]` in its 80x112 frame. Boats/stilt houses anchor on the waterline.
* Light from the upper left, dark hue-shifted outlines, no anti-aliasing or blur
  (glows and smoke use a few flat alpha steps).

## Manifest (`data/prop_art.json`)

```json
"shrine": {"file": "res://art/props/shrine.png", "frame": [80, 112], "anchor": [40, 108],
           "states": {"idle": {"col": 0, "frames": 1}, "active": {"col": 1, "frames": 4, "fps": 6}}}
```

Optional keys:

* `"tile": true` - tiles (`art/tiles/`) plus the vertical `ladder`/`rope` strips.
  `"repeat": "x" | "y" | "xy"` tells how the image wraps seamlessly. Repeating tiles
  use `anchor [0, 0]` (top-left); `hanging_lantern` anchors at its hook (top centre).
  Walls wrap horizontally, floors and water wrap both ways, water/shallow_water have
  4 looping frames.
* `"decal": true` - flat ground decals drawn under actors (`rite_circle`, `grey_patch`,
  `hollow_puddle`, `fishing_ripple`).
* `"building": true, "roof_split": f` - village buildings. `f` is the fraction of the
  image height (from the top) that is roof; the engine uses that band as a walkable
  rooftop and draws the facade below it.

## Adding a prop

```python
@prop("my_prop", 32, 24, states=(("idle", 1, 0), ("active", 4, 6)))
def my_prop(state, f):
    cv = Canvas(32, 24)
    ...            # shade(cv, mask, RAMP, ...), parts.rock(...), etc.
    outline(cv)    # silhouette outline, then glows/smoke on top
    return cv
```

Seed every random choice from a string (`rng("my_prop", ...)`, `vnoise(..., seed_of(...))`)
so output stays deterministic.
