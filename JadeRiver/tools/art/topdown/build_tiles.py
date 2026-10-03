"""Top-down redesign, Phase 3 (docs/redesign/art_bible.md): build the prototype room's terrain atlas, prop kit,
manifest and Godot TileSet, and optionally the sheets' review images. The foes have their own build (decision 43:
tools/art/topdown/build_foes.py, art/topdown/foes/ and data/topdown/foes.json).

Writes (1 art px = 1 px of the 640x360 world viewport, nearest neighbour, no metadata, byte-identical on every build):
  art/topdown/proto_tiles.png      the terrain atlas (tops, faces, stairs, water frames, overlays, auto-tile sets)
  art/topdown/proto_props.png      the prop kit, its animation frames and the props' floor shadows
  art/topdown/proto_tiles.tres     a Godot TileSet over the atlas: terrain sets for paths and shores, animated water,
                                   and every tile's name as custom data
  data/topdown/proto_tileset.json  the manifest the room view reads: tiles, props, the paint table (which
                                   tops, faces and auto-tile sets each mark draws) and the auto-tile tables
With --review it also renders into docs/redesign/phase3/ the tile sheet and the prop kit at x4, and into docs/redesign/terrain_v2/ the Terrain v2 tile sheet at x4 (art bible §14).
With --review-sand-snow it renders decision 44's sand and snow sheet at x4 into docs/redesign/feedback/sand_snow/ (art
bible "Sand and snow").
The room itself is reviewed in the game: tools/dev/capture/capture.tscn -- phase3.

Usage: python3 tools/art/topdown/build_tiles.py [--review] [--check]
  --check  builds twice in memory and fails unless both builds are byte-identical
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

from PIL import Image  # noqa: E402

import atlas  # noqa: E402
import props  # noqa: E402
import sheet as SH  # noqa: E402
from canvas import T  # noqa: E402

TILES_PNG = "art/topdown/proto_tiles.png"
PROPS_PNG = "art/topdown/proto_props.png"
TRES = "art/topdown/proto_tiles.tres"
MANIFEST = "data/topdown/proto_tileset.json"
REVIEW = ROOT / "docs/redesign/phase3"

# The paint letters of the `topdown` room format, as the room view reads them (TopdownTerrain): the tops a mark draws
# (a fixed pick per cell), its face kind, `grass` for a mark that creeps over a path's edge, `under` for a path or
# paving that grass creeps over (the corner-matched set it takes, art bible §6), `face_below` for the face rows under
# the first (picked by column), and `keep_face` for a mark whose face stays its own over water (a pier's pilings, a
# grassy bank's soil; the rest take the granite embankment). `b` is a planted bed: flowers on a dressed-stone planter;
# `m` a wet meadow of the Reed Marsh, puddles in its grass.
# Terrain v2 (art bible "Terrain v2") adds what the room view draws the mark with: `macro`, the material pattern its
# base tile comes from (by the cell's place in it); `decals`, [set, share of cells] in order, picked by a hash of the
# cell; `tone`, whether the sun and shade patches lie on it. `top` stays the mark's Phase 3 tiles (the TileSet's).
# Decision 44 (art bible "Sand and snow") adds `a` sand, `n` fresh snow and `k` packed snow, and what creeps over what
# on one level: `creep`, the material whose overlay a mark lays over its neighbours (sand, snow); `takes`, the materials
# that may creep over it, in the order they are laid; `wet`, damp where it touches the water (the `wet` tint); `beach`,
# the water by it shows the sand through its shallows. Grass creeps over sand as over a path (`under`); sand over dirt
# and paving; packed snow over grass, dirt, paving, granite and rock with its own pixels; fresh snow over all of those
# and over packed snow.
PAINT = {
    "g": {"top": ["grass_a", "grass_b", "grass_a", "grass_c", "grass_d"], "face": "earth", "grass": True, "keep_face": True,
          "macro": "grass", "decals": [["flowers", 0.05], ["grass", 0.5]], "tone": True, "takes": ["snowpack", "snow"]},
    "f": {"top": ["grass_flowers"], "face": "earth", "grass": True, "keep_face": True,
          "macro": "grass", "decals": [["flowers", 0.72], ["grass", 0.2]], "tone": True, "takes": ["snowpack", "snow"]},
    "b": {"top": ["grass_flowers", "grass_d", "grass_a", "grass_flowers", "grass_c"], "face": "stone", "grass": True,
          "macro": "grass", "decals": [["flowers", 0.8]], "tone": True, "takes": ["snowpack", "snow"]},
    "d": {"top": ["dirt", "dirt_b"], "face": "earth", "under": "grass_dirt",
          "macro": "dirt", "decals": [["dirt", 0.45]], "tone": True, "takes": ["sand", "snowpack", "snow"]},
    "p": {"top": ["paving_a", "paving_b", "paving_a", "paving_c", "paving_b", "paving_a", "paving_d"], "face": "pave",
          "under": "grass_paving", "macro": "pave", "decals": [["pave_hole", 0.012], ["pave", 0.3]],
          "takes": ["sand", "snowpack", "snow"]},
    "s": {"top": ["stone_top", "stone_top", "stone_top_b"], "face": "stone", "macro": "stone", "decals": [["stone", 0.2]],
          "takes": ["snowpack", "snow"]},
    "w": {"top": ["wood", "wood_b"], "face": "wood", "keep_face": True, "macro": "wood", "decals": [["wood", 0.05]]},
    "r": {"top": ["rock", "rock_b"], "face": "rock", "macro": "rock", "decals": [["rock", 0.6]], "tone": True,
          "takes": ["snowpack", "snow"]},
    "t": {"top": ["roof_top", "roof_top_b"], "face": "roof",
          "face_below": ["plaster_face_window", "roof_face", "roof_face"], "macro": "roof", "decals": [["roof", 0.06]]},
    "l": {"top": ["wall_top"], "face": "wall", "macro": "wall"},
    "m": {"top": ["marsh_a", "grass_a", "marsh_b", "grass_c"], "face": "earth", "grass": True, "keep_face": True,
          "macro": "grass", "decals": [["marsh", 0.16], ["grass", 0.45]], "tone": True, "takes": ["snowpack", "snow"]},
    "a": {"top": ["sand_a", "sand_b", "sand_a", "sand_c"], "face": "sand", "keep_face": True, "under": "grass_sand",
          "macro": "sand", "decals": [["sand", 0.3]], "tone": True, "creep": "sand", "wet": True, "beach": True},
    "n": {"top": ["snow_a", "snow_b"], "face": "snow", "macro": "snow", "decals": [["snow", 0.2]], "creep": "snow"},
    "k": {"top": ["snowpack_a", "snowpack_b"], "face": "snow", "macro": "snowpack", "decals": [["snowpack", 0.28]],
          "creep": "snowpack", "takes": ["snow"]},
    # R2 (tools/art/topdown/flood.py): floors under shallow water a body wades through, `flood` the water laid over
    # them (v2.flood, per corner case: a corner floods where every cell round it is flooded or open water). `q` the
    # Drowned Shrine's flagstones, its granite embankment where it drops into a deep pool; `h` a river's sandy bed, a
    # beach where it runs into the deep water.
    "q": {"top": ["paving_a", "paving_b", "paving_c"], "face": "pave", "macro": "pave", "decals": [["pave", 0.22]],
          "flood": True},
    "h": {"top": ["sand_a", "sand_b", "sand_c"], "face": "sand", "keep_face": True, "macro": "sand",
          "decals": [["sand", 0.2]], "flood": True},
}

# Terrain sets of the TileSet (art bible §6).
GROUND_TERRAINS = ["grass", "dirt", "paving"]


def build_all() -> dict:
    """Every output as bytes, keyed by its path under the project root."""
    sheet, at, auto, v2 = atlas.build()
    psheet, pat = props.build()
    manifest = {
        "schema_version": 2,
        "tile": T,
        "tiles": at,
        "props": pat,
        "atlas": {"tiles": "res://" + TILES_PNG, "props": "res://" + PROPS_PNG},
        "paint": PAINT,
        "bank_face": "bank",
        "tileset": "res://" + TRES,
        "v2": v2,
        "autotile": {
            "grass_dirt": {"mode": "corners", "key": "TL TR BL BR, 1 = grass", "rule": "a path cell's corner is grass "
                           "when any cell sharing that corner on the same level is grass", "tiles": auto["grass_dirt"]},
            "grass_paving": {"mode": "corners", "key": "TL TR BL BR, 1 = grass", "rule": "as grass_dirt",
                             "tiles": auto["grass_paving"]},
            "grass_sand": {"mode": "corners", "key": "TL TR BL BR, 1 = grass", "rule": "as grass_dirt (decision 44; "
                           "not in the TileSet, whose terrain sets keep dirt and paving)", "tiles": auto["grass_sand"]},
            "shore": {"mode": "sides", "key": "bit 1 N, 2 E, 4 S, 8 W = the neighbour is not water",
                      "frame_ms": 250, "tiles": auto["shore"]},
        },
        "overlays": {"rim_w": "top whose west neighbour is lower", "rim_e": "top whose east neighbour is lower",
                     "rim_n": "top whose north neighbour is lower", "ao_n": "floor at the foot of a face",
                     "shade_w": "floor whose west neighbour is higher", "end_w": "a face's west end, turning a corner",
                     "end_e": "a face's east end, turning a corner", "cheek_w": "the west cheek of a flight of stairs",
                     "cheek_e": "the east cheek of a flight of stairs", "face_ao": "the foot of a face that meets a floor"},
    }
    return {
        TILES_PNG: SH.png_bytes(sheet.img),
        PROPS_PNG: SH.png_bytes(psheet.img),
        TRES: tileset_tres(at, auto).encode(),
        MANIFEST: (json.dumps(manifest, indent=1, sort_keys=True) + "\n").encode(),
    }


def tileset_tres(at: dict, auto: dict) -> str:
    """A Godot 4.5 TileSet over the atlas (the text format ResourceSaver writes).
    Terrain set 0 matches corners: grass, dirt, paving (the path transitions and the plain tops).
    Terrain set 1 matches sides: water. A shore tile's side is water where the neighbour is water, and unset (empty)
    where it is land, so painting the water layer with terrains picks the shore by itself.
    Water tiles are 4-frame animations (250 ms), the frames side by side in the atlas. Custom data 0 holds each tile's
    name as the manifest spells it."""
    lines = ['[gd_resource type="TileSet" load_steps=3 format=3]', "",
             '[ext_resource type="Texture2D" path="res://%s" id="1_tiles"]' % TILES_PNG, "",
             '[sub_resource type="TileSetAtlasSource" id="TileSetAtlasSource_tiles"]',
             'texture = ExtResource("1_tiles")']
    ground = {}
    for set_name in ("grass_dirt", "grass_paving"):
        under = 1 if set_name == "grass_dirt" else 2
        for key, name in auto[set_name].items():
            corners = [0 if ch == "1" else under for ch in key]
            centre = 0 if key == "1111" else under
            ground[name] = (centre, corners, 0.05 if key in ("1111", "0000") else 1.0)
    for name in ("grass_a", "grass_b", "grass_c", "grass_d", "grass_flowers"):
        ground[name] = (0, [0, 0, 0, 0], {"grass_flowers": 0.15, "grass_d": 0.3, "grass_c": 0.5}.get(name, 1.0))
    for name in ("dirt", "dirt_b"):
        ground[name] = (1, [1, 1, 1, 1], 1.0)
    for name in ("paving_a", "paving_b", "paving_c", "paving_d"):
        ground[name] = (2, [2, 2, 2, 2], 0.3 if name == "paving_d" else 1.0)
    anim_frames = set()
    shores = {}
    for sides, names in auto["shore"].items():
        shores[names[0]] = int(sides)
        anim_frames.update(names[1:])
    shores["water_0"] = -1
    anim_frames.update(["water_1", "water_2", "water_3"])
    corner_bits = ("top_left_corner", "top_right_corner", "bottom_left_corner", "bottom_right_corner")
    side_bits = ((1, "top_side"), (2, "right_side"), (4, "bottom_side"), (8, "left_side"))
    # The Phase 3 contract tiles only (rows 0-6); the Terrain v2 sets are layers the room view composes.
    cells = sorted(((v[1] // T, v[0] // T), n) for n, v in at.items() if n not in anim_frames and v[1] // T < atlas.CONTRACT_ROWS)
    for (cy, cx), name in cells:
        p = "%d:%d" % (cx, cy)
        if name in shores:
            for f in range(4):
                lines.append("%s/animation_frame_%d/duration = 0.25" % (p, f))
        lines.append("%s/0 = 0" % p)
        if name in ground:
            centre, corners, prob = ground[name]
            lines += ["%s/0/terrain_set = 0" % p, "%s/0/terrain = %d" % (p, centre)]
            if prob != 1.0:
                lines.append("%s/0/probability = %s" % (p, prob))
            for bit, v in zip(corner_bits, corners):
                lines.append("%s/0/terrains_peering_bit/%s = %d" % (p, bit, v))
        elif name in shores and shores[name] >= 0:
            sides = shores[name]
            lines += ["%s/0/terrain_set = 1" % p, "%s/0/terrain = 0" % p]
            for bit, side in side_bits:
                if not sides & bit:
                    lines.append("%s/0/terrains_peering_bit/%s = 0" % (p, side))
        lines.append('%s/0/custom_data_0 = "%s"' % (p, name))
    lines += ["", "[resource]",
              "terrain_set_0/mode = 1"]
    colors = ["Color(0.35, 0.65, 0.3, 1)", "Color(0.7, 0.55, 0.35, 1)", "Color(0.6, 0.57, 0.52, 1)"]
    for k, n in enumerate(GROUND_TERRAINS):
        lines += ['terrain_set_0/terrain_%d/name = "%s"' % (k, n), "terrain_set_0/terrain_%d/color = %s" % (k, colors[k])]
    lines += ["terrain_set_1/mode = 2", 'terrain_set_1/terrain_0/name = "water"',
              "terrain_set_1/terrain_0/color = Color(0.17, 0.62, 0.56, 1)",
              'custom_data_layer_0/name = "name"', "custom_data_layer_0/type = 4",
              'sources/0 = SubResource("TileSetAtlasSource_tiles")', ""]
    return "\n".join(lines)


# ============================================================================================================ review
def review(outputs: dict) -> None:
    """The sheets for review: every tile at x4, named and grouped; the prop kit at x4."""
    from PIL import ImageDraw, ImageFont
    REVIEW.mkdir(parents=True, exist_ok=True)
    sheet = Image.open(io.BytesIO(outputs[TILES_PNG])).convert("RGBA")
    psheet = Image.open(io.BytesIO(outputs[PROPS_PNG])).convert("RGBA")
    man = json.loads(outputs[MANIFEST])
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        head = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    except OSError:
        font = head = ImageFont.load_default()

    # 1. The tile sheet at x4, grouped and named.
    groups = [("Tops", [n for n, _ in atlas.TOPS]), ("Faces (first row under a lip, then the rows below)", [n for n, _ in atlas.FACES]),
              ("Water frames 0-3 and light overlays (on grey)", ["water_0", "water_1", "water_2", "water_3"] + atlas.OVERLAYS),
              ("Grass over dirt: corners TL TR BL BR, 1 = grass", list(man["autotile"]["grass_dirt"]["tiles"].values())),
              ("Grass over paving", list(man["autotile"]["grass_paving"]["tiles"].values())),
              ("Shore: bit 1 N, 2 E, 4 S, 8 W = land (frame 0 of 4)", [v[0] for v in man["autotile"]["shore"]["tiles"].values()])]
    per_row, cell_w, cell_h = 10, 112, 88
    height = 16
    for _, names in groups:
        height += 28 + ((len(names) + per_row - 1) // per_row) * cell_h
    ts = Image.new("RGBA", (per_row * cell_w + 16, height), (22, 30, 34, 255))
    d = ImageDraw.Draw(ts)
    y = 8
    for title, names in groups:
        d.text((8, y), title, font=head, fill=(232, 225, 207, 255))
        y += 28
        for k, n in enumerate(names):
            x0, y0 = 8 + (k % per_row) * cell_w, y + (k // per_row) * cell_h
            r = man["tiles"][n]
            img = sheet.crop((r[0], r[1], r[0] + r[2], r[1] + r[3]))
            bg = Image.new("RGBA", (64, r[3] * 4), (128, 128, 128, 255))
            bg.alpha_composite(img.resize((64, r[3] * 4), Image.NEAREST))
            ts.alpha_composite(bg, (x0, y0))
            d.text((x0, y0 + 67), n, font=font, fill=(175, 201, 209, 255))
        y += ((len(names) + per_row - 1) // per_row) * cell_h
    ts.save(REVIEW / "04_tile_sheet_x4.png")

    # 2. The prop kit (frames and shadows) at x4.
    pk = Image.new("RGBA", psheet.size, (22, 30, 34, 255))
    pk.alpha_composite(psheet)
    pk.resize((psheet.width * 4, psheet.height * 4), Image.NEAREST).save(REVIEW / "05_props_x4.png")

    print("review images in", REVIEW.relative_to(ROOT))
    review_v2(sheet, man, font, head)


def review_v2(sheet, man: dict, font, head) -> None:
    """Terrain v2's tile sheet at x4 (docs/redesign/terrain_v2/10_tile_sheet_x4.png): each material's macro pattern
    whole, the face patterns (first row, then the two body rows), grass over a path in a few corner cases as the room
    view lays them (the path's pattern under the positional overlay), the tint masks in their colours over the meadow,
    the decals on their ground, and the water: its four frames, a shore case in its four frames, the corner foam and
    the pilings' ripples."""
    v2, tiles = man["v2"], man["tiles"]
    z = 4

    def crop(name: str) -> Image.Image:
        r = tiles[name]
        return sheet.crop((r[0], r[1], r[0] + r[2], r[1] + r[3]))

    def grid(names: list, w: int, base=None, tint=None) -> Image.Image:
        """Tiles laid w to a row (over `base` tiles, the same count, where given), at 1 px."""
        h = (len(names) + w - 1) // w
        img = Image.new("RGBA", (w * T, h * T), (0, 0, 0, 0))
        for i, n in enumerate(names):
            t = crop(n)
            if tint is not None:
                t = Image.composite(Image.new("RGBA", t.size, tuple(round(c * 255) for c in tint[:3]) + (255,)), Image.new("RGBA", t.size, (0, 0, 0, 0)), t)
                t.putalpha(t.getchannel("A").point(lambda a: round(a * tint[3])))
            if base is not None:
                img.alpha_composite(crop(base[i]), ((i % w) * T, (i // w) * T))
            img.alpha_composite(t, ((i % w) * T, (i // w) * T))
        return img

    sections: list = []
    m = v2["macro"]
    sections.append(("Macro patterns: each material one pattern, cut into its tiles (grass, dirt, granite, rock, planks, "
                     "roof, wall cap; the paving 8 x 8)", [grid(m[k]["tiles"], m[k]["w"]) for k in
                                                           ("grass", "dirt", "stone", "rock", "wood", "roof", "wall", "pave")]))
    sections.append(("Faces: the first row with its lip, then two body rows that repeat downward (rock, earth, granite, "
                     "paving wall, embankment, pier, courtyard wall)",
                     [grid(v2["faces"][k]["top"] + v2["faces"][k]["body"], 4) for k in atlas.FACE_KINDS]))
    dirt, pave, grass = m["dirt"]["tiles"], m["pave"]["tiles"], m["grass"]["tiles"]
    cases = ["1100", "0011", "1010", "0101", "1000", "0111"]
    sections.append(("Grass over a path, as the room view lays it: the path's own pattern under the grass overlay of "
                     "each corner case and place (TL TR BL BR, 1 = grass): " + ", ".join(cases),
                     [grid(v2["over"][c], 4, dirt if i % 2 == 0 else [pave[(k // 4) * 8 + k % 4] for k in range(16)])
                      for i, c in enumerate(cases)]))
    sections.append(("Sun and shade patches and the water's depth: one set of tint masks drawn in each tint's colour "
                     "(case 1111, 1000, 0110 over the meadow; depth over the water)",
                     [grid(v2["tint_mask"][c], 4, grass, v2["tint"][k]) for c, k in (("1111", "sun"), ("1000", "sun"),
                                                                                       ("0110", "shade"), ("1111", "shade"))]
                     + [grid(v2["tint_mask"][c], 4, v2["water"]["macro"]["frames"][0], v2["tint"][k])
                        for c, k in (("1110", "deep"), ("1111", "deeper"))]))
    ground = {"grass": grass[0], "flowers": grass[1], "dirt": dirt[0], "pave": pave[0], "pave_hole": pave[9],
              "stone": m["stone"]["tiles"][0],
              "rock": m["rock"]["tiles"][0], "marsh": grass[2], "wood": m["wood"]["tiles"][0], "roof": m["roof"]["tiles"][0]}
    sections.append(("Decals on their ground: " + ", ".join(v2["decals"]),
                     [grid(names, len(names), [ground[k]] * len(names)) for k, names in v2["decals"].items()]))
    wf = v2["water"]["macro"]["frames"]
    w0 = wf[0]
    sections.append(("Water: the pattern's four frames; a shore with land to the north and west (09), to the south "
                     "(04) and to the east (02), each in its four frames; the corner foam; the pilings' ripples",
                     [grid(w0, 4), grid(wf[1], 4), grid(wf[2], 4), grid(wf[3], 4)]
                     + [grid(v2["water"]["shore"][s], 4, [w0[5]] * 4) for s in ("09", "04", "02")]
                     + [grid([v2["water"]["corner"][c][0] for c in ("nw", "ne", "sw", "se")], 4, [w0[6]] * 4),
                        grid(v2["water"]["ripple"], 4, [w0[1]] * 4)]))
    path = ROOT / "docs/redesign/terrain_v2"
    path.mkdir(parents=True, exist_ok=True)
    _section_sheet(sections, z, font).save(path / "10_tile_sheet_x4.png")


def review_sand_snow(outputs: dict) -> None:
    """Decision 44's sheet at x4 (docs/redesign/feedback/sand_snow/11_tile_sheet_x4.png): the sand, fresh and packed
    snow patterns whole; their faces (the first row, then the two body rows); the decals on their ground; sand over a
    path and paving, grass over sand, snow over the meadow, granite, paving, rock and packed snow, and packed snow over
    the meadow and rock, in a few corner cases as the room view lays them (the ground's own pattern under the positional overlay); the damp tint on
    the sand by the water; the sandy shore in its four frames beside the river's own."""
    from PIL import ImageFont
    sheet = Image.open(io.BytesIO(outputs[TILES_PNG])).convert("RGBA")
    man = json.loads(outputs[MANIFEST])
    v2, tiles = man["v2"], man["tiles"]
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except OSError:
        font = ImageFont.load_default()
    z = 4

    def crop(name: str) -> Image.Image:
        r = tiles[name]
        return sheet.crop((r[0], r[1], r[0] + r[2], r[1] + r[3]))

    def grid(layers: list, w: int) -> Image.Image:
        """Cells laid w to a row, each a stack of layers ([name] or [name, rgba tint])."""
        h = (len(layers) + w - 1) // w
        img = Image.new("RGBA", (w * T, h * T), (0, 0, 0, 0))
        for i, stack in enumerate(layers):
            for layer in stack:
                layer = [layer] if isinstance(layer, str) else layer
                t = crop(layer[0])
                if len(layer) > 1:
                    col = layer[1]
                    t = Image.composite(Image.new("RGBA", t.size, tuple(round(c * 255) for c in col[:3]) + (255,)),
                                        Image.new("RGBA", t.size, (0, 0, 0, 0)), t)
                    t.putalpha(t.getchannel("A").point(lambda a, k=col[3]: round(a * k)))
                img.alpha_composite(t, ((i % w) * T, (i // w) * T))
        return img

    m = v2["macro"]
    cases = ["1010", "1100", "1000"]
    sections = []
    sections.append(("Patterns: sand, fresh snow, packed snow (each 4 x 4 tiles, periodic)",
                     [grid([[n] for n in m[k]["tiles"]], 4) for k in ("sand", "snow", "snowpack")]))
    sections.append(("Faces: the sand's beach and bank; the snow's lip over the karst cliff (first row, then the body rows)",
                     [grid([[n] for n in v2["faces"][k]["top"] + v2["faces"][k]["body"]], 4) for k in ("sand", "snow")]))
    sections.append(("Decals on their ground: " + ", ".join(("sand", "snow", "snowpack")),
                     [grid([[[m[k]["tiles"][i % 16]], [n]] for i, n in enumerate(v2["decals"][k])], len(v2["decals"][k]))
                      for k in ("sand", "snow", "snowpack")]))

    def over(ground: str, kind: str, key: str) -> Image.Image:
        """A 4 x 4 block of `ground` under the overlay of `kind` ('grass' or a creeping material) for a corner case."""
        base = m[ground]["tiles"] if ground != "pave" else [m["pave"]["tiles"][(k // 4) * 8 + k % 4] for k in range(16)]
        names = v2["over"][key] if kind == "grass" else v2["creep"][kind][key]
        return grid([[[base[k]], [names[k]]] for k in range(16)], 4)

    sections.append(("Sand creeping over a path and over paving; grass over sand (corner cases " + ", ".join(cases) + ")",
                     [over("dirt", "sand", c) for c in cases] + [over("pave", "sand", c) for c in cases[:1]]
                     + [over("sand", "grass", c) for c in cases]))
    sections.append(("Snow creeping over the meadow, granite, paving, rock and packed snow; packed snow over the meadow and rock",
                     [over("grass", "snow", c) for c in cases] + [over(g, "snow", "1010") for g in ("stone", "pave", "rock", "snowpack")]
                     + [over("grass", "snowpack", "1010"), over("rock", "snowpack", "1100")]))
    wet = v2["tint"]["wet"]
    sections.append(("The damp sand by the water (corner cases 0011, 0001, 1111 of the wet tint over the sand)",
                     [grid([[[m["sand"]["tiles"][k]], [v2["tint_mask"][c][k], wet]] for k in range(16)], 4) for c in ("0011", "0001", "1111")]))
    w0 = v2["water"]["macro"]["frames"]
    sections.append(("The shore by sand in its four frames (land to the north, the west, the south) beside the river's own (north)",
                     [grid([[[w0[f][5]], [v2["water"]["beach"][s][f]]] for f in range(4)], 4) for s in ("01", "08", "04")]
                     + [grid([[[w0[f][5]], [v2["water"]["shore"]["01"][f]]] for f in range(4)], 4)]))
    path = ROOT / "docs/redesign/feedback/sand_snow"
    path.mkdir(parents=True, exist_ok=True)
    _section_sheet(sections, z, font).save(path / "11_tile_sheet_x4.png")
    print("sand and snow sheet in", (path / "11_tile_sheet_x4.png").relative_to(ROOT))


def _section_sheet(sections: list, z: int, font) -> Image.Image:
    """A review sheet: each section's title over its images at x`z` (each on grey), laid in rows 1800 px wide."""
    from PIL import ImageDraw
    width, pad = 1800, 12
    rows = []
    for title, imgs in sections:
        line, x, lh, placed = [], pad, 0, []
        for im in imgs:
            w, h = im.width * z, im.height * z
            if x + w > width - pad and line:
                placed.append((line, lh))
                line, x, lh = [], pad, 0
            line.append((im, x))
            x += w + pad
            lh = max(lh, h)
        placed.append((line, lh))
        rows.append((title, placed))
    height = pad + sum(26 + sum(lh + pad for _, lh in placed) for _, placed in rows)
    out = Image.new("RGBA", (width, height), (22, 30, 34, 255))
    d = ImageDraw.Draw(out)
    y = pad
    for title, placed in rows:
        d.text((pad, y), title, font=font, fill=(232, 225, 207, 255))
        y += 26
        for line, lh in placed:
            for im, x in line:
                bg = Image.new("RGBA", im.size, (128, 128, 128, 255))
                bg.alpha_composite(im)
                out.alpha_composite(bg.resize((im.width * z, im.height * z), Image.NEAREST), (x, y))
            y += lh + pad
    return out


def main(argv: list[str]) -> int:
    outputs = build_all()
    if "--check" in argv:
        again = build_all()
        bad = [p for p in outputs if outputs[p] != again[p]]
        for p in bad:
            print("NOT deterministic:", p)
        if bad:
            return 1
    for path, data in outputs.items():
        out = ROOT / path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        print("%-34s %8d bytes  sha1 %s" % (path, len(data), hashlib.sha1(data).hexdigest()[:12]))
    if "--review" in argv:
        review(outputs)
    if "--review-sand-snow" in argv:
        review_sand_snow(outputs)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
