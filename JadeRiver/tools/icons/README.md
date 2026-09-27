# Jade River icon generator

Deterministic Python (Pillow + numpy) generator for every game icon. Icons are being moved from the legacy style
(32 art px drawn with hand-placed pixels, exported ×2) to **Style A, "HD pixel"** (64 art px, shown 1:1), one family
module at a time. The style study that chose it is `docs/mockups/icon_study/`. The build writes:

- `art/icons/<folder>/<id>.png` (RGBA, transparent background). A legacy icon holds its art at 2 screen px per art px
  (64 px for items, equipment and techniques, 32 for HUD glyphs, 24 for status icons and markers). An HD icon is its
  art at 1:1 (64, or 32 for a HUD glyph), plus the native renders of the same drawing its folder asks for,
  `<id>@48.png` and `<id>@32.png` (`registry.VARIANTS`).
- `data/icon_manifest.json`: `{"<id>": "res://art/icons/<folder>/<id>.png"}`, sorted, 2-space indent. An HD icon
  also lists every render as `"<id>@<art px>"` (its 1:1 PNG too, as `<id>@64`), which is how the game knows an HD
  icon from a legacy one and which sizes it can draw crisply (`SpriteCache.icon_renders`).
- optional review sheets.

```sh
python3 tools/icons/build_icons.py                                   # all icons + manifest
python3 tools/icons/build_icons.py --only pills --review-dir /tmp/r  # one family + its review sheets
python3 tools/icons/build_icons.py --only jade                       # ids containing 'jade'
python3 tools/icons/build_icons.py --preview-hd                      # look at unfinished HD families in the game
```

`--only` takes a family module (`pills`, `weapons`, `hud`), a folder (`items`) or a group (`talismans`) by name, else
a substring of the ids. It writes just the matching PNGs; it does not touch the manifest and does not remove stale
files. A full run removes PNGs in `art/icons/` that are no longer built. Running the script twice gives byte-identical
output: there is no randomness, no timestamps and no PNG metadata. `--preview-hd` builds every icon that has an HD
drawing as HD, whatever its family's `ART` says, so an unfinished family can be seen in the running game; never
commit its output (a plain build puts everything back).

## Families and sizes

| folder | legacy art px (PNG) | HD art px (PNG, renders) | contents |
|---|---|---|---|
| `items` | 32 (64) | 64 (64, @32) | herbs, minerals, beast parts, fish, misc, tools, talismans, food, pills, qi jades... |
| `equipment` | 32 (64) | 64 (64, @32) | weapons, armour, cape, soul talisman, gourds |
| `techniques` | 32 (64) | 64 (64, @48, @32) | composed emblem: element disc + form mark (with the family's weapon inset) + grade or kind rim + path stamp (converted: `ART = 64`) |
| `hud` | 16 (32) | 32 (32) | pale-gold glyph with ink outline (converted: `ART = 32`) |
| `status` | 12 (24) | – | colour-keyed glyphs |
| `markers` | 12 (24) | – | map / quest markers |

Where the game shows them (`scripts/presentation/sprite_cache.gd` `draw_icon`, which never draws an icon at a
fractional scale; the `ui_suite` in `tests/rules_tests.gd` checks every page):

| Place | Box | HD icon | Legacy icon |
|---|---|---|---|
| Page slot, `Page.SLOT` (76, inset 6) | 64 | 64 at 1:1 | 32 art px at 2x |
| Small slot, `Page.SLOT_SMALL` (44, inset 6): list rows | 32 | its @32 | 32 art px at 1x |
| HUD technique ring (radius 33) | 48 / 64 | its @48 | 32 art px at 2x (64: the emblem sits just inside the gold bezel; 1x is lost in the ring) |
| HUD item rings (radius 26: quick use, treasures, weapon swap; the draught ring) | 32 | its @32 | 32 art px at 1x |
| HUD button rings / attack ring | 32 / 64 | HUD glyph 1:1 / 2x | 16 art px at 2x / 4x |
| Status row on the HUD / over enemies | 24 / 12 | – | 12 art px at 2x / 1x |

A family converts whole (a page never mixes the two styles within one family). Until it does, its legacy icons show
at the whole-number scales above: the same 64 px in the page slot, so the two styles sit side by side at one size.

## Layout

```
pix.py          Canvas (legacy): mask shapes, shading modes, part separation, outline, glow
                HD mode: SCanvas (icon-space masks at any scale), Frame (diagonal objects), 7-level BANDS,
                PixelPainter (part / cylinder / decal / line / sparkle; texture, rim-light and outline passes)
palette.py      contract tokens, shared ramps R[...], GRADES (plain .. sphere); Mat / mat7 / M (7-step materials),
                KINDS and KIND (material kinds), TEX (a kind's texture), kit(grade) (the HD grade kit)
shapes.py       reusable shape builders (leaf, drop, flame, taper curves, sparkle...); they work on SCanvas too
glyphs.py       small ASCII marks (pill effect marks)
asciiart.py     colour-keyed ASCII sprites (status, markers)
registry.py     register(family, id, fn, group), hd(id, draw), FAMILY_SIZE, HD_SIZE, VARIANTS
families/       one module per family; importing families/ registers everything. Each declares ART.
build_icons.py  renders, validates size + edge clipping, writes PNGs, the manifest, review sheets
review.py       review sheets (the 76 px slot, the HUD rings), drawn with the game's kit art and fonts
study/          the style study that chose Style A (Style B's painter and the study sheets)
```

## HD drawing model (Style A)

An HD icon is a function `draw(p)` that paints in **icon space**: 64 × 64 for items, equipment and techniques, 32 × 32
for HUD glyphs, the object inside a 4-px margin (a glow may use it). `p` is a `pix.PixelPainter`; the build calls the
same function at 64 (1:1), 48 and 32, so describe shapes with continuous coordinates, never per-pixel steps.

- `c = p.c` is an `SCanvas`: `c.circle`, `c.ellipse`, `c.poly`, `c.seg`, `c.polyline`, `c.box` (continuous),
  `c.rect` (whole pixels), `c.arc`, `c.ring`, `c.rrect`, `c.diamond`, `c.leaf`, `c.taper` all take icon-space
  coordinates. `pix.Frame(p0, angle)` lays out diagonal objects (blades, handles, scrolls): `fr.prof(c, [(t, halfwidth), ...])`
  is a symmetric profile along it, `fr.P(t, w)` a point, `fr.along(c)` the (t, w) field.
- `p.part(mask, mat, mode, base=0, sep=True, tex=None, rim=True, spec=None)` paints a part with a 7-step material:
  modes `flat`, `bevel`, `ray`, `ray_soft`, `sphere` (`cx`, `cy`, `rx`, `ry` in icon space), `vgrad`/`hgrad`/`dgrad`,
  `field`. `sep` draws the material's dark line where it overlaps earlier parts; `tex` adds a pixel texture (`wood`
  and `cloth` along `axis`, `metal`, `glass`, `jade`, `paper`, `clay`); `rim=False` keeps the rim light off.
  `p.cylinder(fr, mask, halfwidth, mat, ridge=False)` shades a handle, a scroll or a bell across the frame, lit side
  first; `ridge=True` gives a blade its lit face, ridge and shade face.
- `p.decal(mask, mat, lv)` recolours painted pixels with level `3 + lv` of a material (or a colour); `p.line(pts, mat,
  lv, w)` is a decal stroke; `p.sparkle(x, y, arm)` a glint; `p.glow(colour, strength)` asks for the grade glow.
- `p.image()` runs the finishing passes: the cool rim light on the lower-right edge (by material kind), the selective
  outline (the local dark tone, near-ink beside a bright body pixel) and the stepped glow bands.
- Materials: `M('iron')` is palette ramp `iron` extended to seven steps (`mat7`: a deeper shadow and a specular), with
  its kind from `KIND` (`metal`); `M('starlight', 'silk')` overrides the kind; `mat7(Ramp([...]))` makes one from any
  ramp. `kit(grade)` is a grade's kit: `blade`, `guard`, `grip`, `wrap`, `gem`, `tassel`, `cloth`, `metal2` and
  `glow`, Plain to Sphere. The grade rim and the soft grade halo are drawn by the UI slot, never baked in.

Worked examples, the first HD drawings (from the study): `weapons.jian_hd` (a template on the grade kits) and
`handbell_hd`, `armour.robe_hd`, `pills.make_pill_hd` (vessel + label + mark + pill), `herbs.star_lotus_hd`,
`minerals.driftglass_hd`, `beast_parts.jade_scale_hd`, `workshop.manual_hd`, `techniques.disc_hd` / `mark_hd`
(the domed disc, the mark with its keyline and the shadow under it), `hud.jian_hd` / `cultivate_hd`.

## How to convert a family

One agent per family module (`families/<name>.py`). Only the manifest is shared, and a full build regenerates it.

1. **Keep the legacy code** until the whole family is drawn. Write each HD drawing next to its legacy function, in the
   module's `HD (Style A)` section at the end, and attach it with `hd('<id>', draw)` (or `@hd('<id>')`). Build the
   family's templates first (the vessels, the emblem, the weapon builders on `kit(grade)`), then drive them from the
   module's existing tables (`PILLS`, `GRADE_WORDS`, `CLOTH`, `TECHS`...), so every icon gets a drawing from one loop
   and only the one-offs are written by hand.
2. **Describe once, in icon space** (64, or 32 for HUD glyphs): continuous shapes, `Frame` profiles and materials, no
   per-pixel steps, no size-specific branches. The same function must hold up at 48 and at 32.
3. **Review loop**, as often as needed:
   `python3 tools/icons/build_icons.py --only <family> --review-dir <dir>` renders the HD drawings even before the
   flip, into the sheets only. Look at `icons_<family>_p*.png` (every icon in the 76 px slot at 1:1, then what the game
   draws at 48 or in the technique ring, and at 32) and its `_x2`, and at `icons_<family>_context.png` (a Bag grid,
   the HUD rings the family appears in). Fix every `WARNING <id>@<px>: artwork touches the canvas edge`. To see it in
   the game, build with `--preview-hd`, then `godot --import`, and screenshot a valley_run checkpoint (never commit a
   preview build).
4. **The checklist** (from the study): one bold object; the silhouette reads at 48 and at 32; light from the top left
   with the rim light on the shadow edge; the outline rule (dark local tone inside, near-ink only beside bright
   pixels); no stray single pixels; palette materials only (`M`, `mat7` of palette ramps, `kit`); nothing clipped at
   the canvas edge; a grade changes form and trim, never colour alone; the same weight as the families already
   converted beside it.
5. **Flip**: when every icon in the module has an HD drawing, set `ART = 64` (`ART = 32` for `hud`). The build then
   refuses a missing drawing, so a family cannot flip half-drawn. Delete the module's legacy functions and tables that
   nothing uses any more.
6. **Build and commit together**: a full `python3 tools/icons/build_icons.py` (the other families must not change:
   compare their PNG hashes), `godot --headless --path . --import`, and commit the module, the PNGs with their
   `.import` files and `data/icon_manifest.json` in one commit, after the user approves the family's sheet. The next
   family that shares a page starts only then.

## Legacy drawing model (pix.py Canvas)

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

1. Pick the family module in `families/` (or create one, declare its `ART` and import it in
   `families/__init__.py`).
2. In a family that has converted, write an HD drawing (above) and register it with both functions; in a legacy
   family, write a function that returns a finished canvas, and an HD drawing too if the family is being converted:

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
   - pills: add a row to `PILLS_HD` in `pills.py` with the kind (its vessel), grade, effect mark, pill
     material and mark ink.
   - weapons: `weapons.GRADE_WORDS` × `BUILDERS`.
   - armour: `CLOTH` grade table.
   - fish: `fish(...)` parameters.
   - beast parts (HD): a row in `PARTS_HD` (id, grade, aura colour, drawing) on the kind templates `hide_hd`,
     `scale_hd`, `fang_hd`, `feather_hd`, `vial_hd`, `pouch_hd`, `heap_hd`, `shard_hd`, `core_hd`; the grade's trim
     comes from `GRADE_HD`, the pet gear ladders from `PET_GEAR_HD` on the grade kits.
   - techniques (HD): a technique's row is read from `data/techniques.json`; give its id a form in `FORM_OF` (a secret
     art: a row in `SECRET_ARTS`). The composer `emblem(element, form, family, grade, kind, path)` draws it from the
     tables: `DISCS` (11 elements), `FORMS` (the plan's 24, each placing the family's `WEAPONS` inset), `RIMS` (13
     grades) and `KINDS` (secret, keystone, Dao, lost), `STAMPS` (5 paths); an art off the grammar takes a `HAND` mark.
   - HUD glyphs (HD): a `@glyph('<id>')` drawing in a 32 icon space on `face_hd` (the pale-gold face), `warm_hd`,
     `ink_hd` / `mark_hd` details and one `glint_hd`; a weapon on the `DIAG` frame with `shaft_hd`, `blade_hd` and
     `grip_hd`; a book, bust, arrow or chest from `book_hd`, `bust_hd`, `arrow_hd`, `chest_hd`.
   - status icons and markers: add an ASCII block, using `asciiart.KEY`
     colours.
3. Keep artwork inside the canvas with a 1-px margin for the outline. The
   build prints `WARNING <id>: artwork touches the canvas edge` if you don't.
4. Run the build with `--review-dir` and check the sheets at 1x (the game size) and at x2. Check that the
   silhouette is bold, the object reads at 48 px, there are no stray single
   pixels and the look is consistent with its neighbours.
5. Commit the script change, the PNGs (with their `.import` files) and `data/icon_manifest.json` together.

## Style rules (from docs/art-contracts.md)

- One bold object, at most one supporting symbol. Upper-left light. A dark outline (legacy: 1 art px of the
  material's dark; HD: the selective outline). No blur and no anti-aliasing (only glow bands use stepped alpha).
- Pills are read by three things: the vessel silhouette, the pill colour and the effect mark on the label. The
  vessel is the kind of pill and the grade its material and trim (`pills.VESSEL_OF`, `pills.PILL_GRADES`), never
  only the colour:
  - Jar: what heals and restores. Bottle (on a foot): taken at a breakthrough, a settling or a cleansing. Gourd: a
    draught that lifts you for a while. Box: remakes the body, a method or an animal. Paper wrap: loose pills.
  - Common: earthenware, bronze trim, a red cloth cap. Earth: porcelain, jade trims, a jade plug. Heaven: skyware,
    silver bands, a silver cloud lid. Mystic: mistjade, gold, a violet finial, ring handles, a glow. Sage: sand
    glaze, gold, an ember finial. Sovereign: driftglass, comet iron, a driftteal finial. Law: night steel with star
    dots, gold, starlight. Monarch: rose gold set with pearl.
- Equipment grades:
  - Plain: wood, hemp and straw.
  - Common: iron grey.
  - Earth: green jadeiron with a jade inlay.
  - Heaven: pale-blue cloudsteel with cloud engravings.
  - Mystic: violet mistjade with gold and a faint glow.
  - Spirit: storm-blue stormsteel with silver fittings and a lightning fuller.
  - Sage: sunsteel gold with jade fittings and desert-glass beads.
  - Sovereign: driftsteel (pale comet iron set with violet driftglass), starsilk.
  - Will: lanternsteel (night steel with a starlight edge and star dots), gold fittings.
  - Sphere: orchardsteel (dusk-violet steel), rose-gold fittings.
- Borders, rarity frames and the grade halo are added by the UI. Icons show only the object.
