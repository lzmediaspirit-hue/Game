# Technique FX sheets

Deterministic pixel-art effect animations for the 24 technique forms (`docs/technique_plan.md` §3.2), one sheet per
form under `art/fx/`, described by `data/fx_art.json` (decision 23 of `docs/roadmap_master_ui.md`).

```
tools/art/fx/
  fxpix.py      palette-index canvas: distance-field strokes, arcs, polygons, dots, ghosts, dithers (no anti-aliasing)
  elements.py   the eleven elements: a palette each and the flourishes that make one read as itself on any form
  forms.py      the 24 form drawers and FORMS, each form's sheet spec (cell, anchor, frames, fps, impact, span, at, size)
  build_fx.py   renders every form x band x element, writes the sheets, the manifest and the review sheets
```

```bash
python3 tools/art/fx/build_fx.py                  # every form -> art/fx/*.png, data/fx_art.json
python3 tools/art/fx/build_fx.py strike wave      # some forms
python3 tools/art/fx/build_fx.py --review DIR     # + review sheets (docs/mockups/fx keeps a copy)
python3 tools/art/fx/build_fx.py --verify         # a fresh build is byte-identical to the files on disk
```

Requirements: Python 3.10+, Pillow, numpy. No randomness (`px_hash` gives scatter its variety), no timestamps, PNGs
without metadata. Godot's `--import` writes the `.import` files.

## The sheet

A form is drawn at art resolution and upscaled x2 with nearest neighbour (`docs/art-contracts.md`). Columns are
frames; rows are `band * 11 + element` in `elements.ELEMENTS` order (water, wood, fire, earth, metal, wind, thunder,
soul, formless, space, time), the three bands standing for the vfx tiers 1–2, 3–4 and 5–7 (thicker strokes, more
particles, extra layers). A thrown form (arc, volley, seeker, return) also has `<form>_bolt.png`, a four-frame loop
of its projectile.

The manifest entry the game reads (`FxLayer.play_form`, `World._cast_form`), in screen px:

| field | meaning |
|---|---|
| `cell`, `anchor` | the frame, and the point of it placed on the effect's anchor |
| `frames`, `fps`, `impact` | the animation, and the frame that lands on the pose's hit frame |
| `span` | the length the sprite represents (an arc's reach, a ring's diameter, a tile's width) |
| `at` | `chest` (the caster's hand height), `feet`, `target` (the foe's feet), `target_chest` |
| `size` | `band` (1x, 1.5x, 2x by band; `fit` keeps it inside a strike's reach), `reach` (snapped down to the hitbox), `stretch` (a line drawn to the exact reach), `tile` (repeated across it), `travel` (crosses it over its life) |

## Drawing a form

`draw(cv, f, n, band, el)` paints frame `f` of `n` on an index canvas: `INK` rim, `DEEP` / `BASE` / `LIGHT` / `GLINT`
ramp, a white `CORE`, the element's `ACCENT` and a half-transparent `HAZE`. Strokes are distance fields with a width
that tapers from head to tail (`stroke_arc`, `stroke_seg`, `stroke_poly`), the bands of the cross-section painted
from the rim in; `smear` lays the swept sector under a fast stroke; `star` is a radial flash. The element's touches
come from `elements.py`: `dress_edge` along a stroke's outer edge, `fling` and `ring_burst` for particles thrown off
it, `ground_ripple` for the mark on the ground, `particle` for one flourish; Time's ghost of the frame before is
added by the build. Keep the impact frame the strongest, fade from the tail, and give every element something of its
own on the form.

Review with `--review` and look at `forms_band2_2x.png` (every form × element), the `strip_<form>.png` motion strips
and `bolts_2x.png` before calling a form done; the in-game look is `--cast=<technique>:<t>` (docs/mockups/fx).

## The top-down sheets (decision 38)

The top-down world draws its combat from sheets of its own: every form, every weapon family's moves, the impact marks,
the shared marks and the dust, on the ground plane of the world's ¾ view in five drawn directions (the west three
mirror). **The look rule:** the feel follows the reference game, the look stays wuxia (sword-light, qi trails, ink
strokes, jade and gold qi, the elements' Dao images, palm prints, sword formations, calligraphic marks).

```
tools/art/fx/
  plane.py             the ground plane: forward, side and height projected for each drawn direction (DIRS, MIRROR)
  wuxia.py             the wuxia marks: brush strokes, palm prints, talismans, jian of qi, lotus, petals, ripples, stones,
                       and each element's motif
  topdown_forms.py     the 24 forms redrawn on the ground plane, and TD_FORMS (canvas, anchor, frames, fps, impact, span,
                       at, layer, dirs, size, bolt)
  topdown_melee.py     the families' smears (MOVES x DIRS), the shared marks (COMMON), impacts (WEIGHTS) and dust (DUST)
  build_fx_topdown.py  renders them all at art resolution into art/fx/topdown/ and data/fx_topdown.json
```

```bash
python3 tools/art/fx/build_fx_topdown.py                        # every sheet (about a minute on four cores)
python3 tools/art/fx/build_fx_topdown.py --only form_strike_e   # some sheets
python3 tools/art/fx/build_fx_topdown.py --check                # two builds in memory, byte-identical, equal to disk
python3 tools/art/fx/build_fx_topdown.py --review DIR           # strips: docs/redesign/phase5/combat/
```

A drawer works in the effect's own frame: `pl.pt(f, l, h)` is forward, right and up from the anchor (a point on the
floor); `pl.arc` tips an arc's plane (a rising cut, an overhead chop). The floor is not squashed (a floor circle is a
circle, as the tiles are square); heights go straight up. Sheets are cropped to what they draw; the manifest gives each
sheet's cell and anchor. The game plays them through `TopdownFx` (`scripts/topdown/topdown_fx.gd`), timed and weighed
by `data/combat_feel.json` (`tools/data/combat_feel.py`).
