"""Review sheets for the top-down character (docs/redesign/phase3/character/), drawn from the built sheets and manifest
the way the game's TopdownFigure composites them (sections by z, one rect per frame from the feet, W/SW/NW mirrored),
so they show what ships.

  01_body.png              the unclothed body: every action (rows) in S, SE, E, NE, N (column groups)
  02_outfit_<facing>.png   the starting outfit per facing: every action, each combo row with its weapon family
  03_weapon_<name>.png     each weapon drawn (every weapon set's items) in every action and facing
  04_hair.png              the six styles in the six colours, in the five facings
  05_dyes.png              the starting tunic and trousers in every dye, S, E and N
  06_villagers.png         the tutorial's villagers in their own outfits, S and E (missing layers listed)
  08_mirrored.png          the eight facings of the walk, the west three mirrored
  09_wardrobe.png          every shirt, trousers, shoes, hat and cape drawn, idle and mid-walk in the five facings
"""
from __future__ import annotations

import io
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs/redesign/phase3/character"
MANIFEST = "data/topdown/character.json"
SET_DIR = "data/topdown/character/"
BG = (72, 92, 84, 255)
CELL = (56, 64)          # a frame's crop round the feet: 56 wide, 64 tall
FEET = (28, 54)          # the feet in that crop
TUTORIAL_NPCS = ["aunt_ping", "lu_boatman", "little_dou", "old_ma", "granny_liu", "shen_lian_npc", "uncle_guo",
                 "fisher_wen", "washer_mei"]
ACTION_WEAPON = {"punch": "gauntlets", "swing": "sword", "thrust": "spear"}


def _font(size=12, bold=False):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if bold else ""), size)
    except OSError:
        return ImageFont.load_default()


class Figures:
    """Composites figures from the build's outputs, as TopdownFigure does in the game."""

    def __init__(self, outputs: dict):
        self.man = json.loads(outputs[MANIFEST])
        # the items of every set built for this index's action catalogue (TopdownFigure.manifest does the same)
        self.man["items"] = {}
        for p in sorted(outputs):
            if p.startswith(SET_DIR) and p.endswith(".json"):
                s = json.loads(outputs[p])
                if s["catalog"] == self.man["catalog"]:
                    for cat, its in s["items"].items():
                        self.man["items"].setdefault(cat, {}).update(its)
        self.sheets = {}
        for p, data in outputs.items():
            if p.endswith(".png"):
                self.sheets["res://" + p] = Image.open(io.BytesIO(data)).convert("RGBA")

    def layers(self, outfit: dict) -> tuple:
        out, missing = [], []
        for cat in ("body", "shoes", "pants", "shirt", "hair", "weapon", "hat", "cape"):
            name = str(outfit.get(cat, "none"))
            if name in ("none", ""):
                continue
            item = self.man["items"].get(cat, {}).get(name)
            if item is None:
                missing.append("%s:%s" % (cat, name))
                continue
            sheets = item["sheets"]
            key = "none"
            if cat == "hair":
                key = str(int(outfit.get("hair_color", 0)))
            elif cat in ("shirt", "pants"):
                key = str(outfit.get(cat + "_dye", "none"))
            if key not in sheets:
                key = "none" if "none" in sheets else sorted(sheets)[0]
            for sec in item["sections"]:
                out.append((sec["z"], self.sheets[sheets[key]], sec["rects"]))
        out.sort(key=lambda t: t[0])
        return out, missing

    def frame_of(self, action: str, row: str, i: int) -> tuple:
        a = self.man["actions"].get(action) or self.man["actions"][self.man["aliases"][action]]
        mirror = row in self.man["mirror"]
        drawn = self.man["mirror"].get(row, row)
        if "facing" in a:
            drawn, mirror = a["facing"], False
        return a["start"][drawn] + min(max(i, 0), a["frames"] - 1), mirror

    def draw(self, canvas: Image.Image, feet: tuple, layers: list, action: str, row: str, i: int) -> None:
        idx, mirror = self.frame_of(action, row, i)
        k = idx * 6
        for _z, sheet, r in layers:
            x, y, w, h, ox, oy = r[k:k + 6]
            if w == 0:
                continue
            piece = sheet.crop((x, y, x + w, y + h))
            if mirror:
                piece = piece.transpose(Image.FLIP_LEFT_RIGHT)
                ox = -ox - w
            canvas.alpha_composite(piece, (feet[0] + ox, feet[1] + oy))

    def cell(self, outfit: dict, action: str, row: str, i: int, bg=BG) -> Image.Image:
        im = Image.new("RGBA", CELL, bg or (0, 0, 0, 0))
        layers, _ = self.layers(outfit)
        self.draw(im, FEET, layers, action, row, i)
        return im


def load_built() -> dict:
    """The built index, sets and sheets as build_character.build_all returns them, read back from disk."""
    out = {MANIFEST: (ROOT / MANIFEST).read_bytes()}
    for p in sorted((ROOT / SET_DIR).glob("*.json")):
        out[SET_DIR + p.name] = p.read_bytes()
    for p in sorted((ROOT / "art/topdown/character").glob("*.png")):
        out["art/topdown/character/" + p.name] = p.read_bytes()
    return out


def starting(**kw) -> dict:
    o = {"body": "light", "hair": "topknot", "hair_color": 0, "shirt": "disciple", "pants": "loose", "shoes": "slippers",
         "weapon": "none", "hat": "none", "cape": "none"}
    o.update(kw)
    return o


def _grid(F: Figures, rows: list, dirs: list, scale: int, title: str, label_w: int = 150) -> Image.Image:
    """rows: [(label, outfit, action)]; columns: every frame of the action in each facing of `dirs`."""
    acts = F.man["actions"]
    per_dir = max(acts[a]["frames"] for _, _, a in rows)
    cw, ch = CELL
    W = label_w + len(dirs) * (per_dir * cw * scale + 12)
    H = 40 + len(rows) * (ch * scale + 6) + 24
    sheet = Image.new("RGBA", (W, H), (22, 30, 34, 255))
    d = ImageDraw.Draw(sheet)
    d.text((10, 8), title, font=_font(16, True), fill=(232, 225, 207, 255))
    for c, dr in enumerate(dirs):
        d.text((label_w + c * (per_dir * cw * scale + 12), 26), dr.upper(), font=_font(12, True), fill=(175, 201, 209, 255))
    y = 44
    for label, outfit, action in rows:
        d.text((10, y + 8), label, font=_font(12), fill=(232, 225, 207, 255))
        a = acts[action]
        d.text((10, y + 24), "%d f @ %g fps%s" % (a["frames"], a["fps"], "" if a["hit"] < 0 else ", hit %d" % a["hit"]),
               font=_font(10), fill=(140, 160, 160, 255))
        for c, dr in enumerate(dirs):
            x0 = label_w + c * (per_dir * cw * scale + 12)
            if "facing" in a and dr != a["facing"]:
                d.text((x0 + 4, y + 8), "-> %s" % a["facing"].upper(), font=_font(11), fill=(120, 140, 140, 255))
                continue
            for i in range(a["frames"]):
                cell = F.cell(outfit, action, dr, i).resize((cw * scale, ch * scale), Image.NEAREST)
                if a["hit"] == i:
                    ImageDraw.Draw(cell).rectangle((0, ch * scale - 3, cw * scale - 1, ch * scale - 1), fill=(229, 88, 88, 255))
                sheet.alpha_composite(cell, (x0 + i * cw * scale, y))
        y += ch * scale + 6
    return sheet


def _weapon_for(action: str) -> str:
    for k, w in ACTION_WEAPON.items():
        if action.startswith(k):
            return w
    return "sword"


def review(outputs: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    F = Figures(outputs)
    dirs = F.man["dirs"]
    acts = F.man["action_order"]
    body = {"body": "light"}
    _grid(F, [(a, body, a) for a in acts], dirs, 2, "The unclothed body: every action in S, SE, E, NE, N "
          "(the base every layer is drawn over; red bar = hit frame)").save(OUT / "01_body.png")
    for dr in dirs:
        rows = [("%s (%s)" % (a, _weapon_for(a)), starting(weapon=_weapon_for(a)), a) for a in acts]
        _grid(F, rows, [dr], 3, "Starting outfit, facing %s: topknot, disciple tunic, silk trousers, cloth shoes; "
              "fists and gauntlets punch, the jian swings, the spear thrusts" % dr.upper(), label_w=190).save(OUT / ("02_outfit_%s.png" % dr))
    for w in sorted(F.man["items"].get("weapon", {})):
        rows = [(a, starting(weapon=w), a) for a in acts]
        _grid(F, rows, dirs, 2, "Weapon: %s, every action and facing" % F.man["items"]["weapon"][w]["label"]).save(OUT / ("03_weapon_%s.png" % w))
    _hair(F)
    _dyes(F)
    _villagers(F)
    _mirrored(F)
    _wardrobe(F)
    print("review sheets in", OUT.relative_to(ROOT))


def _hair(F: Figures) -> None:
    styles = list(F.man["items"]["hair"])
    names = F.man["hair_colors"]
    dirs = F.man["dirs"]
    cw, ch = CELL
    s = 3
    W = 150 + len(names) * (len(dirs) * cw * s + 12)
    H = 40 + len(styles) * (ch * s + 6)
    im = Image.new("RGBA", (W, H), (22, 30, 34, 255))
    d = ImageDraw.Draw(im)
    d.text((10, 8), "Hair: the creator's six styles in its six colours, idle, S SE E NE N", font=_font(16, True),
           fill=(232, 225, 207, 255))
    for c, nm in enumerate(names):
        d.text((150 + c * (len(dirs) * cw * s + 12), 26), nm, font=_font(12, True), fill=(175, 201, 209, 255))
    for r, st in enumerate(styles):
        y = 44 + r * (ch * s + 6)
        d.text((10, y + 8), F.man["items"]["hair"][st]["label"], font=_font(12), fill=(232, 225, 207, 255))
        for c in range(len(names)):
            for k, dr in enumerate(dirs):
                cell = F.cell(starting(hair=st, hair_color=c), "idle", dr, 0).resize((cw * s, ch * s), Image.NEAREST)
                im.alpha_composite(cell, (150 + c * (len(dirs) * cw * s + 12) + k * cw * s, y))
    im.save(OUT / "04_hair.png")


def _dyes(F: Figures) -> None:
    dyes = F.man["dyes"]
    dirs = ["s", "e", "n"]
    cw, ch = CELL
    s = 3
    W = 120 + len(dyes) * (len(dirs) * cw * s + 10)
    H = 40 + 2 * (ch * s + 24)
    im = Image.new("RGBA", (W, H), (22, 30, 34, 255))
    d = ImageDraw.Draw(im)
    d.text((10, 8), "Dyes (the side view's, parts.json _dyes) on the disciple tunic and the silk trousers, S E N",
           font=_font(16, True), fill=(232, 225, 207, 255))
    for r, (label, key) in enumerate((("Tunic", "shirt_dye"), ("Trousers", "pants_dye"))):
        y = 44 + r * (ch * s + 24)
        d.text((10, y + 8), label, font=_font(12), fill=(232, 225, 207, 255))
        for c, dy in enumerate(dyes):
            x0 = 120 + c * (len(dirs) * cw * s + 10)
            d.text((x0, y - 14 if r == 0 else y + ch * s + 2), dy, font=_font(11), fill=(175, 201, 209, 255))
            for k, dr in enumerate(dirs):
                cell = F.cell(starting(**{key: dy}), "idle", dr, 0).resize((cw * s, ch * s), Image.NEAREST)
                im.alpha_composite(cell, (x0 + k * cw * s, y))
    im.save(OUT / "05_dyes.png")


def _villagers(F: Figures) -> None:
    npcs = {n["id"]: n for n in json.loads((ROOT / "data/npcs.json").read_text())["entries"]}
    fill = {"body": "light", "hair": "short_knot", "shirt": "disciple", "pants": "loose", "shoes": "slippers"}
    cw, ch = CELL
    s = 3
    dirs = ["s", "se", "e"]
    W = len(TUTORIAL_NPCS) * (len(dirs) * cw * s + 16) + 16
    H = 40 + ch * s + 80
    im = Image.new("RGBA", (W, H), (22, 30, 34, 255))
    d = ImageDraw.Draw(im)
    d.text((10, 8), "The tutorial's villagers (Lotus Ferry) in their own outfits, S SE E; below each, what has no "
           "top-down layer yet", font=_font(16, True), fill=(232, 225, 207, 255))
    for c, nid in enumerate(TUTORIAL_NPCS):
        o = dict(npcs[nid].get("outfit", {}))
        for k, v in fill.items():
            o.setdefault(k, v)
        x0 = 16 + c * (len(dirs) * cw * s + 16)
        for k, dr in enumerate(dirs):
            im.alpha_composite(F.cell(o, "idle", dr, 0).resize((cw * s, ch * s), Image.NEAREST), (x0 + k * cw * s, 40))
        _, missing = F.layers(o)
        d.text((x0, 44 + ch * s), npcs[nid].get("name", nid), font=_font(12, True), fill=(232, 225, 207, 255))
        d.text((x0, 60 + ch * s), ", ".join(missing) or "all drawn", font=_font(10), fill=(229, 160, 120, 255) if missing else (140, 200, 160, 255))
    im.save(OUT / "06_villagers.png")


def _wardrobe(F: Figures) -> None:
    rows = []
    for cat in ("shirt", "pants", "shoes", "hat", "cape"):
        for name in F.man["items"].get(cat, {}):
            rows.append(("%s: %s" % (cat, F.man["items"][cat][name]["label"]), starting(**{cat: name})))
    dirs = F.man["dirs"]
    cw, ch = CELL
    s = 3
    im = Image.new("RGBA", (200 + 2 * len(dirs) * cw * s + 20, 40 + len(rows) * (ch * s + 4)), (22, 30, 34, 255))
    d = ImageDraw.Draw(im)
    d.text((10, 8), "Every garment drawn, on the starting outfit: idle (left) and mid-walk (right), S SE E NE N",
           font=_font(16, True), fill=(232, 225, 207, 255))
    for r, (label, o) in enumerate(rows):
        y = 40 + r * (ch * s + 4)
        d.text((10, y + 8), label, font=_font(12), fill=(232, 225, 207, 255))
        for k, dr in enumerate(dirs):
            im.alpha_composite(F.cell(o, "idle", dr, 0).resize((cw * s, ch * s), Image.NEAREST), (200 + k * cw * s, y))
            im.alpha_composite(F.cell(o, "walk", dr, 2).resize((cw * s, ch * s), Image.NEAREST),
                               (220 + (len(dirs) + k) * cw * s, y))
    im.save(OUT / "09_wardrobe.png")


def _mirrored(F: Figures) -> None:
    rows = ["s", "se", "e", "ne", "n", "nw", "w", "sw"]
    cw, ch = CELL
    s = 3
    im = Image.new("RGBA", (40 + 8 * cw * s, 60 + len(rows) * ch * s), (22, 30, 34, 255))
    d = ImageDraw.Draw(im)
    d.text((10, 8), "Walk in the eight facings: S, SE, E, NE, N drawn; NW, W, SW mirror NE, E, SE", font=_font(16, True),
           fill=(232, 225, 207, 255))
    for r, row in enumerate(rows):
        d.text((6, 50 + r * ch * s + 20), row.upper(), font=_font(12, True), fill=(175, 201, 209, 255))
        for i in range(8):
            im.alpha_composite(F.cell(starting(weapon="sword"), "walk", row, i).resize((cw * s, ch * s), Image.NEAREST),
                               (40 + i * cw * s, 40 + r * ch * s))
    im.save(OUT / "08_mirrored.png")
