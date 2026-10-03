"""Terrain v2, third part (decision 40; docs/redesign/art_bible.md "Foliage and decor"): build the ground-cover sheet
the room view scatters (tools/art/topdown/decor.py) and its manifest, and optionally the review sheet.

Writes (1 art px = 1 px of the 640x360 world viewport, nearest neighbour, no metadata, byte-identical on every build):
  art/topdown/decor.png        every piece of ground cover, packed in rows
  data/topdown/decor.json      the manifest TopdownFoliage reads: each piece's rect, foot and sway row, the sets, the
                               biomes (per paint mark), the litter round trees and the keep-clear rings
With --review it renders docs/redesign/terrain_v2/foliage/decor_x4.png (every piece at x4 on its ground) and
docs/redesign/terrain_v2/foliage/props_x3.png (the foliage props, each tree's trunk, canopy and shade together).
The foliage props themselves are built with the prop kit (tools/art/topdown/build_tiles.py, through props.py).

Usage: python3 tools/art/topdown/build_decor.py [--review] [--check]
  --check  builds twice in memory and fails unless both builds are byte-identical and the files on disk are current
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))

from PIL import Image  # noqa: E402

import decor  # noqa: E402
import sheet as SH  # noqa: E402
from canvas import Img  # noqa: E402

SHEET = "art/topdown/decor.png"
MANIFEST = "data/topdown/decor.json"
SHEET_W = 128


def build_all() -> dict:
    items = decor.sprites()
    at, height = SH.pack([(spr.w, spr.h) for spr, _ in items.values()], SHEET_W)
    sheet = Img(SHEET_W, height)
    table = {}
    for (name, (spr, sway)), (px, py) in zip(items.items(), at):
        sheet.paste(spr, px, py)
        table[name] = {"rect": [px, py, spr.w, spr.h], "foot": [spr.w // 2, spr.h - 1], "sway": sway}
    for s, names in decor.SETS.items():
        for n in names:
            assert n in table, (s, n)
    manifest = {"schema_version": 1, "sheet": "res://" + SHEET, "sprites": table, "sets": decor.SETS,
                "biomes": decor.BIOMES, "litter": decor.LITTER, "clear": decor.CLEAR}
    return {SHEET: SH.png_bytes(sheet.img), MANIFEST: (json.dumps(manifest, indent=1, sort_keys=True) + "\n").encode()}


def review(outputs: dict) -> None:
    import foliage as FL
    import props as P
    import terrain2 as T2
    out_dir = ROOT / "docs/redesign/terrain_v2/foliage"
    out_dir.mkdir(parents=True, exist_ok=True)
    grass = T2.grass_macro()

    def ground(w: int, h: int) -> Image.Image:
        g = Image.new("RGBA", (w, h))
        for yy in range(0, h, 64):
            for xx in range(0, w, 64):
                g.alpha_composite(grass.img, (xx, yy))
        return g

    # 1. Every piece of ground cover on the meadow, x4.
    man = json.loads(outputs[MANIFEST])
    sheet = Image.open(io.BytesIO(outputs[SHEET])).convert("RGBA")
    names = list(man["sprites"])
    cols = 12
    rows = (len(names) + cols - 1) // cols
    img = ground(cols * 20, rows * 20)
    for i, n in enumerate(names):
        r = man["sprites"][n]["rect"]
        spr = sheet.crop((r[0], r[1], r[0] + r[2], r[1] + r[3]))
        img.alpha_composite(spr, ((i % cols) * 20 + 10 - r[2] // 2, (i // cols) * 20 + 18 - r[3]))
    img.resize((img.width * 4, img.height * 4), Image.NEAREST).save(out_dir / "decor_x4.png")

    # 2. The foliage props: a tree's trunk, canopy and shade together, the rest with their floor shadows, x3.
    cells = []
    for k, (draw, w, h, fw, fh, origin, solid, shadow) in FL.PROPS.items():
        tr = Img(w, h)
        draw(tr) if k in FL.STILL_TRUNK or k not in FL.ANIM else draw(tr, 0)
        can, at, cw = None, [0, 0], 0
        if k in FL.CANOPY:
            cd, cw, ch, at = FL.CANOPY[k]
            can = Img(cw, ch)
            cd(can, 0)
        left = max(origin[0], -at[0] if can else 0) + 6
        top = max(origin[1], -at[1] if can else 0) + 6
        pw = left + max(w - origin[0], (cw + at[0]) if can else 0) + 40
        panel = ground(pw, top + 34)
        sh = FL.shadow_of(k) if k in FL.SHADOWS else (P.shadow_sprite(*shadow) if shadow else None)
        if sh:
            panel.alpha_composite(sh[0].img, (left + sh[1][0], top + sh[1][1]))
        panel.alpha_composite(tr.img, (left - origin[0], top - origin[1]))
        if can:
            panel.alpha_composite(can.img, (left + at[0], top + at[1]))
        cells.append(panel)
    width = 1500
    rows_, line, lw = [], [], 0
    for cimg in cells:
        if lw + cimg.width > width and line:
            rows_.append(line)
            line, lw = [], 0
        line.append(cimg)
        lw += cimg.width + 4
    rows_.append(line)
    H = sum(max(c.height for c in r) + 4 for r in rows_)
    out = Image.new("RGBA", (width, H), (20, 26, 30, 255))
    yy = 0
    for r in rows_:
        hh = max(c.height for c in r)
        xx = 0
        for cimg in r:
            out.alpha_composite(cimg, (xx, yy + hh - cimg.height))
            xx += cimg.width + 4
        yy += hh + 4
    out.resize((out.width * 2, out.height * 2), Image.NEAREST).save(out_dir / "props_x2.png")
    print("review images in", out_dir.relative_to(ROOT))


def main(argv: list) -> int:
    return SH.run(argv, build_all, "tools/art/topdown/build_decor.py", review)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
