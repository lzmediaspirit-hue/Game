"""Top-down redesign, Phase 3 (docs/redesign/art_bible.md): build the prototype room's terrain atlas, prop kit, manifest
and Godot TileSet, and optionally the style review images.

Writes (1 art px = 1 px of the 640x360 world viewport, nearest neighbour, no metadata, byte-identical on every build):
  art/topdown/proto_tiles.png      the terrain atlas (tops, faces, stairs, water frames, overlays, auto-tile sets)
  art/topdown/proto_props.png      the prop kit
  art/topdown/placeholder_body.png the Phase 1 placeholder body (unchanged; drawn by tools/art/build_topdown_proto.py)
  art/topdown/proto_tiles.tres     a Godot TileSet over the atlas: terrain sets for paths and shores, animated water,
                                   and every tile's name as custom data
  data/topdown/proto_tileset.json  the manifest the Phase 1 loader reads (tiles, props, body), plus the auto-tile
                                   tables and the paint table for the loaders to come
With --review it also renders docs/redesign/phase3/: the Riverside Square mock at 640x360 and x2, the whole room, the
tile sheet at x4, the prop kit at x4 and the height-levels readability test.

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
import compose  # noqa: E402
import props  # noqa: E402
from canvas import T  # noqa: E402

TILES_PNG = "art/topdown/proto_tiles.png"
PROPS_PNG = "art/topdown/proto_props.png"
BODY_PNG = "art/topdown/placeholder_body.png"
TRES = "art/topdown/proto_tiles.tres"
MANIFEST = "data/topdown/proto_tileset.json"
REVIEW = ROOT / "docs/redesign/phase3"

# The paint letters of the `topdown` room format: the tops a letter draws (a fixed per-cell pick) and its face kind.
PAINT = {letter: {"tops": compose.TOPS[letter], "face": compose.FACE_OF[letter]} for letter in compose.TOPS}

# Terrain sets of the TileSet (art bible §6).
GROUND_TERRAINS = ["grass", "dirt", "paving"]


def png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=False)
    return buf.getvalue()


def build_all() -> dict:
    """Every output as bytes, keyed by its path under the project root."""
    import build_topdown_proto as proto   # the placeholder body stays where Phase 1 drew it
    sheet, at, auto = atlas.build()
    psheet, pat = props.build()
    body, body_at = proto.build_body()
    manifest = {
        "schema_version": 2,
        "tile": T,
        "tiles": at,
        "props": pat,
        "body": body_at,
        "paint": PAINT,
        "tileset": "res://" + TRES,
        "autotile": {
            "grass_dirt": {"mode": "corners", "key": "TL TR BL BR, 1 = grass", "rule": "a path cell's corner is grass "
                           "when any cell sharing that corner on the same level is grass", "tiles": auto["grass_dirt"]},
            "grass_paving": {"mode": "corners", "key": "TL TR BL BR, 1 = grass", "rule": "as grass_dirt",
                             "tiles": auto["grass_paving"]},
            "shore": {"mode": "sides", "key": "bit 1 N, 2 E, 4 S, 8 W = the neighbour is not water",
                      "frame_ms": 250, "tiles": auto["shore"]},
        },
        "overlays": {"rim_w": "top whose west neighbour is lower", "rim_e": "top whose east neighbour is lower",
                     "rim_n": "top whose north neighbour is lower", "ao_n": "floor at the foot of a face",
                     "shade_w": "floor whose west neighbour is higher"},
    }
    return {
        TILES_PNG: png_bytes(sheet.img),
        PROPS_PNG: png_bytes(psheet.img),
        BODY_PNG: png_bytes(body.img),
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
    cells = sorted(((v[1] // T, v[0] // T), n) for n, v in at.items() if n not in anim_frames)
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
DRESSING = ([dict(kind="bamboo", x=x, y=y) for x, y in ((2, 9), (3, 10), (26, 10), (44, 8), (45, 9))]
            + [dict(kind="lotus", x=x, y=y) for x, y in ((8, 26), (13, 28), (28, 27), (40, 25), (42, 28))]
            + [dict(kind="lantern_red", x=17, y=21), dict(kind="lantern_red", x=21, y=21), dict(kind="incense", x=24, y=13),
               dict(kind="shrub", x=11, y=17), dict(kind="shrub", x=33, y=13), dict(kind="shrub", x=22, y=6)])

HEIGHT_TEST = {
    # 30 x 18: a rock cliff (levels 4 and 3), a grass terrace (2), a stone terrace (1), the square (0) with a house whose
    # roof is level 2 and a courtyard wall at level 1, the promenade, the river and a pier.
    "levels": [
        "444444444444333333333333333333",
        "444444444444333333333333333333",
        "444444444444333333333333333333",
        "222222222222222222222222222222",
        "222222222222222222222222222222",
        "222222222222222222222222222222",
        "222222222222222222222222222222",
        "111111111111111111111111111111",
        "111111111111111111111111111111",
        "111111111111111111111111111111",
        "000222222000000000000000000000",
        "000222222000000000000000000000",
        "000222222000111111110000000000",
        "000000000000000000000000000000",
        "000000000000000000000000000000",
        "~~~~~~~~~~~~~~~~~~~~~~00~~~~~~",
        "~~~~~~~~~~~~~~~~~~~~~~00~~~~~~",
        "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~",
    ],
    "paint": [
        "rrrrrrrrrrrrrrrrrrrrrrrrrrrrrr",
        "rrrrrrrrrrrrrrrrrrrrrrrrrrrrrr",
        "rrrrrrrrrrrrrrrrrrrrrrrrrrrrrr",
        "ggggggggggfggggggggdddgggggggg",
        "gggfggggggggggggggddddgggfgggg",
        "gggggggggggggfgggggdddgggggggg",
        "ggggggggggggggggggggddgggggggg",
        "ssssssssssssssssssssssssssssss",
        "ssssssssssssssssssssssssssssss",
        "ssssssssssssssssssssssssssssss",
        "pppttttttppppppppppppppppppppp",
        "pppttttttppppppppppppppppppppp",
        "pppttttttpppllllllllpppppppppp",
        "pppppppppppppppppppppppppppppp",
        "ssssssssssssssssssssssssssssss",
        "~~~~~~~~~~~~~~~~~~~~~~ww~~~~~~",
        "~~~~~~~~~~~~~~~~~~~~~~ww~~~~~~",
        "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~",
    ],
    "stairs": [{"x": 14, "y": 7, "w": 2, "h": 2, "from": 1, "to": 2}, {"x": 25, "y": 10, "w": 2, "h": 2, "from": 0, "to": 1}],
    "props": [{"kind": "lantern", "x": 13, "y": 8}, {"kind": "lantern", "x": 16, "y": 8}, {"kind": "bamboo", "x": 1, "y": 6},
              {"kind": "willow", "x": 26, "y": 5}, {"kind": "lotus", "x": 5, "y": 16}, {"kind": "reeds", "x": 18, "y": 15},
              {"kind": "lantern_red", "x": 21, "y": 14}, {"kind": "barrel", "x": 10, "y": 12}],
}
HEIGHT_BODIES = [(11.5, 13.6, "s", "idle", 0), (9.5, 8.6, "e", "idle", 0), (6.5, 5.6, "s", "idle", 0),
                 (5.5, 11.2, "s", "idle", 0), (16.0, 12.6, "w", "idle", 0), (22.9, 16.4, "n", "idle", 0),
                 (4.5, 1.8, "s", "idle", 0)]


def review(outputs: dict) -> None:
    from PIL import ImageDraw, ImageFont, ImageOps
    REVIEW.mkdir(parents=True, exist_ok=True)
    sheet = Image.open(io.BytesIO(outputs[TILES_PNG])).convert("RGBA")
    psheet = Image.open(io.BytesIO(outputs[PROPS_PNG])).convert("RGBA")
    body = Image.open(io.BytesIO(outputs[BODY_PNG])).convert("RGBA")
    man = json.loads(outputs[MANIFEST])
    from canvas import Img
    A = compose.Atlas(Img.wrap(sheet), man["tiles"], {k: v["tiles"] for k, v in man["autotile"].items()},
                      Img.wrap(psheet), man["props"])
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        head = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    except OSError:
        font = head = ImageFont.load_default()

    # 1. Riverside Square at the game's camera on the spawn, with the proposed dressing.
    room = json.loads((ROOT / "data/topdown/td_proto_square.json").read_text())
    sp = room.get("spawn", [22, 18])
    bodies = [(sp[0] + 0.5, sp[1] + 0.6, "s", "idle", 0)]
    full = compose.render(room, A, 0, bodies, DRESSING, body, man["body"]).img
    cx = min(max((sp[0] + 0.5) * T, 320), full.width - 320)
    cy = min(max((sp[1] + 0.5) * T - 12, 180), full.height - 180)
    view = full.crop((int(cx) - 320, int(cy) - 180, int(cx) + 320, int(cy) + 180))
    view.save(REVIEW / "01_square_mock_640x360.png")
    view.resize((1280, 720), Image.NEAREST).save(REVIEW / "01_square_mock_x2.png")
    full.save(REVIEW / "02_square_whole_room.png")
    frames = [compose.render(room, A, f, bodies, DRESSING, body, man["body"]).img.crop(
        (int(cx) - 320, int(cy) - 180, int(cx) + 320, int(cy) + 180)).resize((1280, 720), Image.NEAREST) for f in range(4)]
    frames[0].save(REVIEW / "03_square_water.gif", save_all=True, append_images=frames[1:], duration=250, loop=0)

    # 2. The tile sheet at x4, grouped and named.
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
    pk = Image.new("RGBA", psheet.size, (22, 30, 34, 255))
    pk.alpha_composite(psheet)
    pk.resize((psheet.width * 4, psheet.height * 4), Image.NEAREST).save(REVIEW / "05_props_x4.png")

    # 3. The height-levels readability test, in colour and by value alone, at x2.
    hi = compose.render(HEIGHT_TEST, A, 0, HEIGHT_BODIES, None, body, man["body"], pad=5 * T).img
    hi = hi.crop((0, 16, hi.width, hi.height))
    grey = ImageOps.grayscale(hi.convert("RGB")).convert("RGBA")
    both = Image.new("RGBA", (hi.width * 2 + 8, hi.height), (10, 32, 39, 255))
    both.alpha_composite(hi, (0, 0))
    both.alpha_composite(grey, (hi.width + 8, 0))
    both = both.resize((both.width * 2, both.height * 2), Image.NEAREST)
    dd = ImageDraw.Draw(both)
    marks = [("L4 cliff top", 7, -3.2), ("L3 cliff top", 18, -2.2), ("L2 grass terrace", 10, 1.6), ("L1 stone terrace", 20, 5.4),
             ("L2 roof", 4, 7.2), ("L1 wall", 13, 10.2), ("L0 square", 20, 11.4), ("L0 pier", 24, 14.8), ("water", 26, 16.2)]
    for text, tx, ty in marks:
        x, yv = (hi.width + 8 + tx * T) * 2, int((ty * T + 5 * T - 16) * 2)
        dd.text((x + 1, yv + 1), text, font=head, fill=(7, 16, 21, 255))
        dd.text((x, yv), text, font=head, fill=(255, 230, 161, 255))
    both.save(REVIEW / "06_height_levels_test.png")
    print("review images in", REVIEW.relative_to(ROOT))


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
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
