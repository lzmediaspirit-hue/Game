# Art contracts for new Jade River drawings

These contracts let generated pixel art plug into the engine without code changes.
All new art follows Part 9 of the build prompt: uniform crisp pixels, cluster cel
shading, dark-hued 1–2 px outlines, light from the upper left, no blur, no
anti-aliasing, no non-integer scaling. Keep the existing character art untouched.

## Shared rules

- Every new raster is authored at **native pixel scale 2**: draw on a low-resolution
  canvas, then upscale ×2 with nearest neighbour before saving. One art pixel is
  therefore a 2×2 block on screen, exactly like the character sheets
  (`art/body_*`, 256 px cells, ~50 art px tall figures).
- PNG, RGBA, transparent background, no colour profile, no JPEG.
- Palette tokens (start here; add local hues that harmonise):
  ink `#071015`, river night `#0A2027`, deep teal `#0D3035`, jade shadow `#15514F`,
  jade `#2C9E8F`, bright jade `#67D6BD`, aged bronze `#9A6A35`, warm gold `#E5B84C`,
  pale gold `#FFE6A1`, paper `#E8E1CF`, mist blue `#AFC9D1`, warning red `#E45858`,
  Qi cyan `#32BED1`, soul violet `#9B78D1`, Hollow grey `#87949A`.
- Shade by hue-shifting: shadows toward blue-green, highlights toward warm jade or
  pale gold. Never shade by pure black/white only. 4–8 purposeful colours per sprite.
- Hollow creatures: grey-white body (`#87949A` family), empty white eyes (no pupil),
  same silhouette as their living variant.
- Generators live in `tools/art/` (Python 3 + Pillow + numpy) and are deterministic:
  running them again produces byte-identical output.

## Creatures — `art/creatures/<id>.png` + `data/creature_art.json`

- One sheet per creature, **right-facing only** (the engine mirrors for left).
- Square cells. `cell` (screen px) is 128 (64 art px) for small/normal creatures,
  192 (96 art px) for large creatures and elites, 256 (128 art px) for bosses.
- Rows are actions in this fixed order, columns are frames (max 6 columns):

  | Row | Action | Frames | fps | Loop | Notes |
  |---|---|---|---|---|---|
  | 0 | idle | 4 | 6 | yes | breathing / bobbing |
  | 1 | walk | 6 | 10 | yes | flying creatures: wing-flap cycle |
  | 2 | windup | 3 | 8 | no (hold last) | the readable attack tell (rear back, claw raised, glow) |
  | 3 | attack | 4 | 12 | no | strike; `hit_frame` is the frame where damage lands |
  | 4 | hurt | 2 | 10 | no | recoil, eyes squeezed |
  | 5 | death | 5 | 10 | no | collapse; last frame lying still or fading |

- Sheet size = `cell*6` × `cell*6`; unused columns are transparent.
- Anchor = the ground contact point (between the feet) at `anchor` in screen px inside
  the cell, normally `[cell/2, cell - cell/8]`. Flying creatures anchor at the body
  centre and set `"flying": true` (the engine draws them above a ground shadow).
- The body must fit inside the cell in every frame with at least 2 art px margin.
- Scale reference: the player is ~50 art px (≈100 screen px) tall. A crab is
  ~14–18 art px tall, a boarlet ~22, a tortoise ~30, an ape or golem ~50–56, bosses
  up to ~110 art px.
- Manifest entry:

```json
"mudshell_crab": {"file": "res://art/creatures/mudshell_crab.png", "cell": 128,
  "anchor": [64, 112], "flying": false, "hit_frame": 2,
  "actions": {"idle": {"row": 0, "frames": 4, "fps": 6, "loop": true},
              "walk": {"row": 1, "frames": 6, "fps": 10, "loop": true},
              "windup": {"row": 2, "frames": 3, "fps": 8, "loop": false},
              "attack": {"row": 3, "frames": 4, "fps": 12, "loop": false},
              "hurt": {"row": 4, "frames": 2, "fps": 10, "loop": false},
              "death": {"row": 5, "frames": 5, "fps": 10, "loop": false}}}
```

## Item, technique and status icons — `art/icons/<family>/<id>.png` + `data/icon_manifest.json`

- Items and techniques: 64×64 screen px (32 art px ×2). One bold object, at most one
  supporting symbol, 1 art px dark outline, readable at 48 px.
- HUD glyphs: 32×32 (16 art px ×2), pale gold `#E5B84C`/`#FFE6A1` glyph with ink
  outline, drawn to sit inside the dark HUD circles.
- Status icons: 24×24 (12 art px ×2).
- Pills are recognised by vessel silhouette + pill shape + effect mark
  (heart = healing, spiral = QI, eye = soul, bone = body temper, arrows = conversion,
  gate = breakthrough, knot = consolidation, lamp = comprehension, leaf = antidote,
  flame = burst). Grade changes the vessel trim, never only colour.
- Equipment grades: Plain (wood/grey/hemp), Common (iron grey), Earth (jadeiron green
  trim), Heaven (cloudsteel pale blue), Mystic (mistjade violet). Border pattern is added
  by the UI; icons show only the object.
- Manifest: `{"<id>": "res://art/icons/<family>/<id>.png", ...}`.

## Props and interactables — `art/props/<id>.png` + `data/prop_art.json`

- Drawn at native scale 2, anchored at bottom centre (the ground contact).
- States are separate columns in one sheet (e.g. herb patch `ready`, `depleted`),
  each state one frame unless animated; animated states list their frames.
- Manifest entry:
  `"shrine": {"file": "res://art/props/shrine.png", "frame": [96, 128], "anchor": [48, 124],
  "states": {"idle": {"col": 0, "frames": 1}, "active": {"col": 1, "frames": 4, "fps": 6}}}`
  where `frame` is one frame's size in screen px and columns advance left→right
  (an animated state occupies `frames` consecutive columns starting at `col`).

## UI kit — `art/ui/<asset>__<state>.png` + `data/ui_assets.json`

- Nine-slice frames with margins from Part 9.4 (major window 256×256 margins 24,
  minor panel 128×128 margins 12, slot 64×64 margins 8, selected slot glow 72×72
  margins 12, primary button 192×64 margins 16/14, secondary button 160×56 margins
  14/12, tab 128×48 margins 16/10, toast 256×64 margins 20/12, bar shell 256×32
  margins 10/8).
- States as separate files: `normal`, `pressed`, `selected`, `disabled`.
- Manifest entry: `"major_window": {"normal": "res://art/ui/major_window__normal.png",
  "margins": [24, 24, 24, 24]}`.
