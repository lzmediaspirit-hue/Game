"""Top-down redesign, Phase 3 (docs/redesign/art_bible.md): build the prototype room's terrain atlas, prop kit, foes,
manifest and Godot TileSet, and optionally the sheets' review images.

Writes (1 art px = 1 px of the 640x360 world viewport, nearest neighbour, no metadata, byte-identical on every build):
  art/topdown/proto_tiles.png      the terrain atlas (tops, faces, stairs, water frames, overlays, auto-tile sets)
  art/topdown/proto_props.png      the prop kit, its animation frames and the props' floor shadows
  art/topdown/foes.png             the foes in eight facings (tools/art/topdown/creatures.py)
  art/topdown/proto_tiles.tres     a Godot TileSet over the atlas: terrain sets for paths and shores, animated water,
                                   and every tile's name as custom data
  data/topdown/proto_tileset.json  the manifest the room view reads: tiles, props, foes, the paint table (which
                                   tops, faces and auto-tile sets each mark draws) and the auto-tile tables
With --review it also renders into docs/redesign/phase3/ the tile sheet and the prop kit at x4 and the foe sheet at x3.
The room itself is reviewed in the game: tools/dev/topdown_capture.tscn -- --phase3.

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
import creatures  # noqa: E402
import props  # noqa: E402
from canvas import T  # noqa: E402

TILES_PNG = "art/topdown/proto_tiles.png"
PROPS_PNG = "art/topdown/proto_props.png"
FOES_PNG = "art/topdown/foes.png"
TRES = "art/topdown/proto_tiles.tres"
MANIFEST = "data/topdown/proto_tileset.json"
REVIEW = ROOT / "docs/redesign/phase3"

# The paint letters of the `topdown` room format, as the room view reads them (TopdownTerrain): the tops a mark draws
# (a fixed pick per cell), its face kind, `grass` for a mark that creeps over a path's edge, `under` for a path or
# paving that grass creeps over (the corner-matched set it takes, art bible §6), `face_below` for the face rows under
# the first (picked by column), and `keep_face` for a mark whose face stays its own over water (a pier's pilings, a
# grassy bank's soil; the rest take the granite embankment). `b` is a planted bed: flowers on a dressed-stone planter;
# `m` a wet meadow of the Reed Marsh, puddles in its grass.
PAINT = {
    "g": {"top": ["grass_a", "grass_b", "grass_a", "grass_c", "grass_d"], "face": "earth", "grass": True, "keep_face": True},
    "f": {"top": ["grass_flowers"], "face": "earth", "grass": True, "keep_face": True},
    "b": {"top": ["grass_flowers", "grass_d", "grass_a", "grass_flowers", "grass_c"], "face": "stone", "grass": True},
    "d": {"top": ["dirt", "dirt_b"], "face": "earth", "under": "grass_dirt"},
    "p": {"top": ["paving_a", "paving_b", "paving_a", "paving_c", "paving_b", "paving_a", "paving_d"], "face": "pave",
          "under": "grass_paving"},
    "s": {"top": ["stone_top", "stone_top", "stone_top_b"], "face": "stone"},
    "w": {"top": ["wood", "wood_b"], "face": "wood", "keep_face": True},
    "r": {"top": ["rock", "rock_b"], "face": "rock"},
    "t": {"top": ["roof_top", "roof_top_b"], "face": "roof",
          "face_below": ["plaster_face_window", "roof_face", "roof_face"]},
    "l": {"top": ["wall_top"], "face": "wall"},
    "m": {"top": ["marsh_a", "grass_a", "marsh_b", "grass_c"], "face": "earth", "grass": True, "keep_face": True},
}

# Terrain sets of the TileSet (art bible §6).
GROUND_TERRAINS = ["grass", "dirt", "paving"]


def png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=False)
    return buf.getvalue()


def build_all() -> dict:
    """Every output as bytes, keyed by its path under the project root."""
    sheet, at, auto = atlas.build()
    psheet, pat = props.build()
    foes, foes_at = creatures.build()
    manifest = {
        "schema_version": 2,
        "tile": T,
        "tiles": at,
        "props": pat,
        "foes": foes_at,
        "atlas": {"tiles": "res://" + TILES_PNG, "props": "res://" + PROPS_PNG, "foes": "res://" + FOES_PNG},
        "paint": PAINT,
        "bank_face": "bank",
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
                     "shade_w": "floor whose west neighbour is higher", "end_w": "a face's west end, turning a corner",
                     "end_e": "a face's east end, turning a corner", "cheek_w": "the west cheek of a flight of stairs",
                     "cheek_e": "the east cheek of a flight of stairs"},
    }
    return {
        TILES_PNG: png_bytes(sheet.img),
        PROPS_PNG: png_bytes(psheet.img),
        FOES_PNG: png_bytes(foes.img),
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
def review(outputs: dict) -> None:
    """The sheets for review: every tile at x4, named and grouped; the prop kit at x4; the foes at x3."""
    from PIL import ImageDraw, ImageFont
    REVIEW.mkdir(parents=True, exist_ok=True)
    sheet = Image.open(io.BytesIO(outputs[TILES_PNG])).convert("RGBA")
    psheet = Image.open(io.BytesIO(outputs[PROPS_PNG])).convert("RGBA")
    foes = Image.open(io.BytesIO(outputs[FOES_PNG])).convert("RGBA")
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

    # 3. The foes at x3: a row per species and drawn facing, the actions along it, on a meadow tone, labelled.
    fm = man["foes"]
    cw, ch = fm["cell"]
    z, lw, th = 3, 230, 22
    cols = foes.width // cw
    out = Image.new("RGBA", (lw + cols * cw * z, th + foes.height * z), (22, 30, 34, 255))
    d = ImageDraw.Draw(out)
    x = lw
    for act, (n, _, _) in creatures.ACTIONS.items():   # the sheet's column order
        d.text((x + 4, 4), "%s (%d)" % (act, n), font=head, fill=(232, 225, 207, 255))
        x += n * cw * z
    for r in range(foes.height // ch):
        for c in range(cols):
            tone = (99, 150, 76, 255) if (r + c) % 2 else (92, 140, 70, 255)
            cell = Image.new("RGBA", (cw, ch), tone)
            cell.alpha_composite(foes.crop((c * cw, r * ch, (c + 1) * cw, (r + 1) * ch)))
            out.alpha_composite(cell.resize((cw * z, ch * z), Image.NEAREST), (lw + c * cw * z, th + r * ch * z))
        sp, facing = creatures.SPECIES[r // len(fm["dirs"])], fm["dirs"][r % len(fm["dirs"])]
        d.text((6, th + r * ch * z + ch * z // 2 - 8), "%s %s" % (sp.replace("_", " "), facing.upper()), font=head,
               fill=(232, 225, 207, 255))
    out.save(REVIEW / "12_foes_x3.png")
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
