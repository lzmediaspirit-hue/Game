"""Decision 43, the living world (docs/redesign/art_bible.md §14.13): build the sheet of the room's small moving things
(tools/art/topdown/life.py) and the vista strips, with their manifest, and optionally the review sheets.

Writes (1 art px = 1 px of the 640x360 world viewport, nearest neighbour, no metadata, byte-identical on every build):
  art/topdown/life.png          critters, rings, puffs, tools and wall hangings, packed in rows
  art/topdown/vista.png         the vista strips (each tiles across), one under the other
  data/topdown/life_art.json    the manifest TopdownLife reads: each sprite's rect, frame count and size, and its foot
                                (a critter's feet, a tool's grip, a hanging's top-left), and each vista layer's rect
With --review it renders docs/redesign/feedback/living_world/sheet_x4.png (every sprite at x4 on grass and water) and
vistas_x2.png (the vista layers as the room view stacks them).

Usage: python3 tools/art/topdown/build_life.py [--review] [--check]
  --check  builds twice in memory and fails unless both builds are byte-identical and the files on disk are current
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

from PIL import Image  # noqa: E402

import life as L  # noqa: E402
from canvas import Img  # noqa: E402

SHEET = "art/topdown/life.png"
VISTA = "art/topdown/vista.png"
MANIFEST = "data/topdown/life_art.json"
SHEET_W = 256


def sprites() -> list:
    """(name, frames, foot) for every sprite of the sheet: a critter's action, a ring, a puff, a tool, a hanging. The
    foot is where the sprite stands (a critter's feet on the ground, bottom middle), a tool's grip, a hanging's top-left."""
    out = []
    sp = L.sparrow()
    for act in ("stand", "peck", "hop", "fly"):
        out.append(("sparrow_" + act, sp[act], None))
    for col in ("white", "gold", "blue", "coral"):
        out.append(("butterfly_" + col, L.butterfly(col), "mid"))
    out.append(("dragonfly", L.dragonfly(), "mid"))
    out.append(("fish", L.fish(), "mid"))
    out.append(("ring", L.rings(), "mid"))
    fr = L.frog()
    out.append(("frog_sit", fr["sit"], None))
    out.append(("frog_leap", fr["leap"], None))
    for brown in (False, True):
        hn = L.hen(brown)
        for act in ("stand", "peck", "walk", "flap"):
            out.append(("hen%s_%s" % ("_brown" if brown else "", act), hn[act], None))
    ct = L.cat()
    for act in ("sit", "walk", "sleep"):
        out.append(("cat_" + act, ct[act], None))
    dg = L.dog()
    for act in ("lie", "sit", "trot"):
        out.append(("dog_" + act, dg[act], None))
    for k, r in enumerate((1.5, 2.5, 3.5, 4.5)):
        out.append(("puff_%d" % k, [L.puff(r)], "mid"))
    # Decision 44: a tool in hand is the figure's own tool layer (tools/art/topdown/figure/sets/tool.py); only the loads
    # set down at a spot are drawn from this sheet.
    be = L.pole_end()
    out.append(("pole_back", [be[0]], [5, 1]))
    out.append(("pole_front", [be[1]], [5, 1]))
    out.append(("laundry_basket", [L.laundry_basket()], None))
    for name, fn in (("window", L.window), ("nets", L.nets), ("herbs", L.herbs), ("scroll", L.scroll),
                     ("plaque", L.plaque), ("shelf", L.shelf), ("drying_fish", L.drying_fish),
                     ("ribbon_banner", L.ribbon_banner)):
        out.append(("hang_" + name, [fn()], [0, 0]))
    return out


def vistas() -> list:
    """(name, strip) for every vista layer, far to near within each kind."""
    pk = L.peaks()
    hl = L.hills()
    mh = L.marsh_horizon()
    rv = L.river_on()
    return [("peaks_far", pk[0]), ("peaks_mid", pk[1]), ("cloud_sea", pk[2]), ("hills_far", hl[0]), ("hills_near", hl[1]),
            ("marsh_trees", mh[0]), ("marsh_reeds", mh[1]), ("river_bank", rv[0])]


def build_all() -> dict:
    items = sprites()
    places, x, y, row_h = [], 0, 0, 0
    for name, frames, foot in items:
        cell = L.strip(frames) if len(frames) > 1 else frames[0]
        if x + cell.w > SHEET_W:
            x, y, row_h = 0, y + row_h + 1, 0
        places.append((name, frames, foot, cell, x, y))
        x, row_h = x + cell.w + 1, max(row_h, cell.h)
    sheet = Img(SHEET_W, y + row_h)
    table = {}
    for name, frames, foot, cell, px, py in places:
        sheet.paste(cell, px, py)
        fw = cell.w // len(frames)
        if foot is None:
            ft = [fw // 2, cell.h - 1]
        elif foot == "mid":
            ft = [fw // 2, cell.h // 2]
        else:
            ft = list(foot)
        table[name] = {"rect": [px, py, cell.w, cell.h], "frames": len(frames), "size": [fw, cell.h], "foot": ft}
    vs = vistas()
    vw = max(v.w for _, v in vs)
    vimg = Img(vw, sum(v.h for _, v in vs))
    vtable = {}
    yy = 0
    for name, v in vs:
        vimg.paste(v, 0, yy)
        vtable[name] = [0, yy, v.w, v.h]
        yy += v.h
    manifest = {"schema_version": 1, "sheet": "res://" + SHEET, "vista_sheet": "res://" + VISTA, "sprites": table,
                "vistas": vtable}
    out = {}
    for path, img in ((SHEET, sheet), (VISTA, vimg)):
        buf = io.BytesIO()
        img.img.save(buf, format="PNG", optimize=False)
        out[path] = buf.getvalue()
    out[MANIFEST] = (json.dumps(manifest, indent=1, sort_keys=True) + "\n").encode()
    return out


def review(outputs: dict) -> None:
    import terrain2 as T2
    out_dir = ROOT / "docs/redesign/feedback/living_world"
    out_dir.mkdir(parents=True, exist_ok=True)
    man = json.loads(outputs[MANIFEST])
    sheet = Image.open(io.BytesIO(outputs[SHEET])).convert("RGBA")
    grass = T2.grass_macro()
    names = list(man["sprites"])
    cols = 6
    cw, ch = 40, 24
    rows = (len(names) + cols - 1) // cols
    img = Image.new("RGBA", (cols * cw, rows * ch))
    for yy in range(0, img.height, 64):
        for xx in range(0, img.width, 64):
            img.alpha_composite(grass.img, (xx, yy))
    water = (30, 119, 102, 255)
    for i, n in enumerate(names):
        r = man["sprites"][n]["rect"]
        spr = sheet.crop((r[0], r[1], r[0] + r[2], r[1] + r[3]))
        bx, by = (i % cols) * cw, (i // cols) * ch
        if n.startswith(("fish", "ring", "dragonfly")):
            Image.Image.paste(img, Image.new("RGBA", (cw, ch), water), (bx, by))
        if n.startswith("hang_"):
            Image.Image.paste(img, Image.new("RGBA", (cw, ch), (184, 176, 174, 255)), (bx, by))
        if spr.width > cw - 2:
            spr = spr.crop((0, 0, cw - 2, spr.height))
        img.alpha_composite(spr, (bx + 1, by + ch - 1 - spr.height))
    img.resize((img.width * 4, img.height * 4), Image.NEAREST).save(out_dir / "sheet_x4.png")
    vs = Image.open(io.BytesIO(outputs[VISTA])).convert("RGBA")
    v = Image.new("RGBA", (vs.width, vs.height), (10, 32, 39, 255))
    v.alpha_composite(vs)
    v.resize((v.width * 2, v.height * 2), Image.NEAREST).save(out_dir / "vistas_x2.png")
    print("review images in", out_dir.relative_to(ROOT))


def main(argv: list) -> int:
    outputs = build_all()
    if "--check" in argv:
        again = build_all()
        bad = [p for p in outputs if outputs[p] != again[p]]
        stale = [p for p in outputs if not (ROOT / p).exists() or (ROOT / p).read_bytes() != outputs[p]]
        for p in bad:
            print("NOT deterministic:", p)
        for p in stale:
            print("stale (run tools/art/topdown/build_life.py):", p)
        return 1 if bad or stale else 0
    for path, data in outputs.items():
        out = ROOT / path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        print("%-28s %8d bytes  sha1 %s" % (path, len(data), hashlib.sha1(data).hexdigest()[:12]))
    if "--review" in argv:
        review(outputs)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
