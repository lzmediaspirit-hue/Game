# Jade River icon generator

Deterministic Python (Pillow + numpy) generator for every game icon. It draws
crisp pixel art on a low-resolution art canvas, upscales ×2 with nearest
neighbour (native pixel scale 2, see `docs/art-contracts.md`) and writes:

- `art/icons/<family>/<id>.png` (RGBA, transparent background)
- `data/icon_manifest.json`: `{"<id>": "res://art/icons/<family>/<id>.png"}`
  with sorted keys and 2-space indent
- optional contact sheets for review

```sh
python3 tools/icons/build_icons.py                        # all icons + manifest
python3 tools/icons/build_icons.py --review-dir /tmp/rev  # + contact sheets (1x and x2)
python3 tools/icons/build_icons.py --only pills           # one family / group / id substring
```

`--only` writes just the matching PNGs. It does not touch the manifest and does
not remove stale files. A full run removes PNGs in `art/icons/` that are no
longer registered. Running the script twice gives byte-identical output: there
is no randomness, no timestamps and no PNG metadata.

## Families and sizes

| family (folder) | art px | screen px | contents |
|---|---|---|---|
| `items` | 32 | 64 | herbs, minerals, beast parts, fish, misc, tools, talismans, food, pills, qi jades |
| `equipment` | 32 | 64 | weapons (6 families × 5 grades), armour, cape, soul talisman, gourds |
| `techniques` | 32 | 64 | round element emblem + motion mark (secret arts: gold rim + studs) |
| `hud` | 16 | 32 | pale-gold glyph with ink outline |
| `status` | 12 | 24 | colour-keyed glyphs |
| `markers` | 12 | 24 | map / quest markers |

## Layout

```
pix.py          Canvas, mask shapes, shading modes, part separation, outline, glow
palette.py      contract tokens, shared ramps R[...], grade material sets GRADES
shapes.py       reusable shape builders (leaf, drop, flame, taper curves, sparkle...)
glyphs.py       small ASCII marks (pill effect marks)
asciiart.py     colour-keyed ASCII sprites (status, markers)
registry.py     register(family, id, fn, group) / FAMILY_SIZE
families/       one module per family; importing families/ registers everything
build_icons.py  renders, validates size + edge clipping, writes PNGs, manifest, sheets
```

## Drawing model (pix.py)

- `c = Canvas(32)` creates an art canvas. Mask builders (`c.ellipse`, `c.poly`,
  `c.seg`, `c.arc`, `c.rect`, `c.diag`...) return boolean masks. Continuous
  shapes sample pixel centres, so `poly([(2, 2), (10, 2), (10, 10), (2, 10)])`
  covers pixels 2..9.
- `c.put(mask, ramp, mode, base=2, sep=False)` paints a mask with a colour
  ramp (dark to light). The mode picks one ramp level per pixel, with light
  always from the upper left:
  - `flat`: every pixel uses `base`.
  - `bevel`: lit top-left edge, shaded bottom-right edge.
  - `ray`: bands by distance to the lit and shadow edges. Use it for most shapes.
  - `sphere`: round objects.
  - `vgrad`, `hgrad`, `dgrad`, `across`: gradients.
  - `sep=True` draws a 1-px dark separation line where the new part overlaps
    earlier parts.
  - `only_on=True` paints decals only on pixels that are already painted.
- Every painted pixel remembers its material's outline colour. `c.outline()`
  then adds the automatic 1-art-px, 4-connected, hue-tinted dark outline.
  `c.glow(col, (a1, a2))` adds stepped glow bands outside the outline. The
  glow is not blurred. Use it only for Mystic, soul and qi-charged objects.
- Ramps in `palette.R` are hue-shifted: shadows drift to blue-green, lights to
  warm gold. Colour choices start from the contract tokens.

## Adding an icon

1. Pick the family module in `families/` (or create one and import it in
   `families/__init__.py`).
2. Write a function that returns a finished canvas:

   ```python
   def lotus_seed():
       c = Canvas(32)
       pod = c.ellipse(16, 18, 10, 8)
       c.put(pod, R['jade'], 'sphere')
       for (x, y) in ((12, 16), (18, 15), (15, 21)):
           c.put(c.circle(x, y, 1.6), R['wax'], 'sphere', sep=True)
       c.outline()
       return c

   register('items', 'lotus_seed', lotus_seed, 'herbs')
   ```

   Use the family's shared template where one exists, then pass the new
   species or grade as parameters:
   - pills: add a row to `PILLS` in `pills.py` with the grade, effect mark
     and pill ramp.
   - weapons: `weapons.GRADE_WORDS` × `BUILDERS`.
   - armour: `CLOTH` grade table.
   - fish: `fish(...)` parameters.
   - beast parts: `feather`, `scale_shape`, `hide`, `fang`, `vial`, `pouch`.
   - techniques: `emblem(element)` + `mark(...)`.
   - HUD glyphs: add an ASCII block to `hud.G`.
   - status icons and markers: add an ASCII block, using `asciiart.KEY`
     colours.
3. Keep artwork inside the canvas with a 1-px margin for the outline. The
   build prints `WARNING <id>: artwork touches the canvas edge` if you don't.
4. Run the build with `--review-dir` and check the contact sheet at 1x (the
   game size) and at x2 on the dark-teal slot background. Check that the
   silhouette is bold, the object reads at 48 px, there are no stray single
   pixels and the look is consistent with its neighbours.
5. Commit the script change, the PNGs and `data/icon_manifest.json` together.

## Style rules (from docs/art-contracts.md)

- One bold object, at most one supporting symbol. Upper-left light. 1-art-px
  dark outline. No blur and no anti-aliasing (only glow bands use stepped alpha).
- Pills are read by three things: the vessel silhouette, the pill shape and
  the effect mark on the label. Grade changes the vessel form and trim, never
  only the colour:
  - Common: squat jar with bronze trim.
  - Earth: pear-shaped bottle with jade trims.
  - Heaven: meiping vase with silver bands and a cloud lid.
  - Mystic: violet vessel with a gold foot, lid and finial, plus a glow.
- Equipment grades:
  - Plain: wood, hemp and straw.
  - Common: iron grey.
  - Earth: green jadeiron with a jade inlay.
  - Heaven: pale-blue cloudsteel with cloud engravings.
  - Mystic: violet mistjade with gold and a faint glow.
- Borders and rarity frames are added by the UI. Icons show only the object.
