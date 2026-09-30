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
  10_actions_<facing>.png  the action batch (the bow's): every combat move and family's own action with the weapon
                           that plays it, per facing
  11_gestures.png          the story's gestures (salute, kneel, point, startle) on the player and the scenes' people
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figure.actions import OWN  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs/redesign/phase3/character"
MANIFEST = "data/topdown/character.json"
SET_DIR = "data/topdown/character/"
BG = (72, 92, 84, 255)
CELL = (68, 76)          # a frame's crop round the feet: 68 wide, 76 tall (decision 43: the 46 px figure)
FEET = (34, 62)          # the feet in that crop
TUTORIAL_NPCS = ["aunt_ping", "lu_boatman", "little_dou", "old_ma", "granny_liu", "shen_lian_npc", "uncle_guo",
                 "fisher_wen", "washer_mei"]
ACTION_WEAPON = {"punch": "gauntlets", "swing": "sword", "thrust": "spear"}
# The look each family wears (weapon_families.json `appearance`), for the actions that are a family's own
# (figure/actions.py OWN): the review draws each with the weapon that plays it.
FAMILY_LOOK = {"heavy_sabre": "sabre", "bow": "bow", "flute": "flute", "bell": "bell", "fan": "fan", "brush": "brush"}
BATCH = ["charge_hold", "dash_slash", "air_strike", "parry_deflect", "two_hand_swing_1", "two_hand_swing_2",
         "two_hand_swing_3", "bow_draw", "flute_play", "bell_toll", "fan_throw", "brush_write"]
GESTURES = ["salute", "kneel", "point", "startle"]
GESTURE_NPCS = ["recruiter_qing_lan", "recruiter_mo_yun", "qiu_feng", "lu_boatman", "granny_liu", "little_dou"]


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
        wear = []
        for cat in ("body", "shoes", "pants", "shirt", "hair", "weapon", "hat", "cape", "tool"):
            v = outfit.get(cat, "none")
            wear += [(cat, str(n)) for n in (v if isinstance(v, list) else [v])]   # a worker's tools are a list
        for cat, name in wear:
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
    if action in OWN:
        return FAMILY_LOOK[OWN[action]]
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
    _batch(F)
    _gestures(F)
    _work(F)
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


def _batch(F: Figures) -> None:
    """The action batch, per facing: each combat move and family's own action with the weapon that plays it (every
    weapon in every action is in 03_weapon_<name>.png)."""
    for dr in F.man["dirs"]:
        rows = [("%s (%s)" % (a, _weapon_for(a)), starting(weapon=_weapon_for(a)), a) for a in BATCH if a in F.man["actions"]]
        _grid(F, rows, [dr], 3, "The action batch, facing %s: the combat moves and each family's own action with the weapon "
              "that plays it (red bar = hit frame)" % dr.upper(), label_w=210).save(OUT / ("10_actions_%s.png" % dr))


def _gestures(F: Figures) -> None:
    """The story's gestures on the player (with a jian) and on the people the scenes pose (their own outfits)."""
    npcs = {n["id"]: n for n in json.loads((ROOT / "data/npcs.json").read_text())["entries"]}
    fill = {"body": "light", "hair": "short_knot", "shirt": "disciple", "pants": "loose", "shoes": "slippers"}
    rows = []
    for g in GESTURES:
        if g not in F.man["actions"]:
            continue
        rows.append(("%s (player, jian)" % g, starting(weapon="sword"), g))
        for nid in GESTURE_NPCS:
            o = dict(npcs[nid].get("outfit", {}))
            for k, v in fill.items():
                o.setdefault(k, v)
            rows.append(("%s (%s)" % (g, nid), o, g))
    _grid(F, rows, F.man["dirs"], 2, "The story's gestures (decision 39): salute, kneel, point, startle, on the player and "
          "the scenes' people in their own outfits", label_w=220).save(OUT / "11_gestures.png")


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


# ------------------------------------------------------------------ decision 44: the work and place poses
WORK_DIR = ROOT / "docs/redesign/feedback/work_poses"
ALL_ROWS = ["s", "se", "e", "ne", "n", "nw", "w", "sw"]


def _tools_of(F: Figures, action: str) -> list:
    """The tools drawn in a work action (the tool set's `actions`)."""
    return sorted(n for n, it in F.man["items"].get("tool", {}).items() if action in it.get("actions", []))


def _loop_people(action: str) -> list:
    """(label, outfit) of the people whose work loop plays `action` (data/topdown/life.json), in their own outfits with
    their loop's tools."""
    life = json.loads((ROOT / "data/topdown/life.json").read_text())
    npcs = {n["id"]: n for n in json.loads((ROOT / "data/npcs.json").read_text())["entries"]}
    fill = {"body": "light", "hair": "short_knot", "shirt": "disciple", "pants": "loose", "shoes": "slippers"}
    out, seen = [], set()
    for rid in sorted(life["rooms"]):
        r = life["rooms"][rid]
        who = [(oid.replace("npc_", ""), w["loop"], None) for oid, w in sorted(r.get("work", {}).items())]
        who += [(e["id"], e["loop"], e["outfit"]) for e in r.get("extras", [])]
        for nid, loop_id, outfit in who:
            lp = life["loops"][loop_id]
            steps = list(lp.get("at", [])) + [st for v in lp.get("steps", {}).values() for st in v]
            if action not in [st[0] for st in steps] + [lp.get("walk", "walk")] or nid in seen:
                continue
            seen.add(nid)
            o = dict(outfit) if outfit else dict(npcs.get(nid, {}).get("outfit", {}))
            for k, v in fill.items():
                o.setdefault(k, v)
            o["tool"] = list(lp.get("tools", []))
            out.append(("%s (%s)" % (nid, loop_id), o))
    return out[:4]


def _variants(F: Figures, action: str) -> list:
    """(label, outfit) rows for one action: the unclothed body, then the starting outfit (holding the action's tool, and
    a jian for a place's pose) in every hair style and colour, every shirt, trousers, shoe, hat and cape look, every dye
    on the tunic and the trousers, a weapon of every family (put away in a work action), and the people who do it."""
    tools = _tools_of(F, action)
    tool = tools[:1]
    base = starting(tool=tool, weapon="sword" if action in F.man.get("action_order", []) and
                    F.man["actions"][action].get("place") else "none")
    rows = [("body (unclothed)", {"body": "light", "tool": tool})]
    items = F.man["items"]
    for st in items["hair"]:
        rows.append(("hair %s" % st, dict(base, hair=st)))
    for c in range(1, len(F.man["hair_colors"])):
        rows.append(("hair colour %s" % F.man["hair_colors"][c], dict(base, hair_color=c)))
    for cat in ("shirt", "pants", "shoes", "hat", "cape"):
        for name in items.get(cat, {}):
            if cat in ("shirt", "pants", "shoes") and name == base.get(cat):
                continue
            rows.append(("%s %s" % (cat, name), dict(base, **{cat: name})))
    for dy in F.man["dyes"][1:]:
        rows.append(("tunic dye %s" % dy, dict(base, shirt_dye=dy)))
    for dy in F.man["dyes"][1:]:
        rows.append(("trousers dye %s" % dy, dict(base, pants_dye=dy)))
    for w in sorted(items.get("weapon", {})):
        rows.append(("weapon %s%s" % (w, " (put away)" if F.man["actions"][action].get("stow") else ""), dict(base, weapon=w)))
    for t in tools[1:]:
        rows.append(("tool %s" % t, dict(base, tool=[t])))
    rows += _loop_people(action)
    return rows


def work_sheets(F: Figures, out_dir: Path = WORK_DIR) -> list:
    """One sheet per work and place action for docs/redesign/feedback/work_poses/: every frame in all eight facings
    (NW, W and SW mirrored), a row per variant (_variants), composited as the game does; a red bar under the hit."""
    out_dir.mkdir(parents=True, exist_ok=True)
    acts = F.man["actions"]
    made = []
    cw, ch = CELL
    for a in F.man["action_order"]:
        if not (acts[a].get("work") or acts[a].get("place")):
            continue
        rows = _variants(F, a)
        n = acts[a]["frames"]
        label_w = 190
        W = label_w + len(ALL_ROWS) * (n * cw + 10)
        H = 46 + len(rows) * (ch + 2)
        im = Image.new("RGBA", (W, H), (22, 30, 34, 255))
        d = ImageDraw.Draw(im)
        d.text((10, 6), "%s: %s, %d frames at %g fps%s; tools %s; every facing (NW, W, SW mirrored), hair, look and dye"
               % (a, acts[a]["label"], n, acts[a]["fps"], "" if acts[a]["hit"] < 0 else ", contact frame %d (red bar)" % acts[a]["hit"],
                  ", ".join(_tools_of(F, a)) or "none (the weapon as its lines say)"), font=_font(13, True), fill=(232, 225, 207, 255))
        for c, dr in enumerate(ALL_ROWS):
            d.text((label_w + c * (n * cw + 10), 28), dr.upper(), font=_font(12, True), fill=(175, 201, 209, 255))
        for r, (label, o) in enumerate(rows):
            y = 46 + r * (ch + 2)
            d.text((6, y + 30), label[:30], font=_font(11), fill=(232, 225, 207, 255))
            layers, _ = F.layers(o)
            for c, dr in enumerate(ALL_ROWS):
                for i in range(n):
                    cell = Image.new("RGBA", CELL, BG if (i % 2 == 0) else (66, 86, 78, 255))
                    F.draw(cell, FEET, layers, a, dr, i)
                    if acts[a]["hit"] == i:
                        ImageDraw.Draw(cell).rectangle((0, ch - 2, cw - 1, ch - 1), fill=(229, 88, 88, 255))
                    im.alpha_composite(cell, (label_w + c * (n * cw + 10) + i * cw, y))
        p = out_dir / ("action_%s.png" % a)
        im.save(p, optimize=True)
        made.append(p)
    return made


def _work(F: Figures) -> None:
    """Decision 44 in the phase 3 set: each work action with its tool on a villager, and the place poses on the player
    with a jian, in the five drawn facings."""
    acts = F.man["actions"]
    villager = {"body": "light", "hair": "short_knot", "shirt": "vneck", "pants": "cuffed", "shoes": "folded",
                "hat": "straw", "shirt_dye": "earth"}
    rows = []
    for a in F.man["action_order"]:
        if acts[a].get("work"):
            for t in _tools_of(F, a):
                rows.append(("%s (%s)" % (a, t), dict(villager, tool=[t]), a))
        elif acts[a].get("place"):
            rows.append(("%s (player, jian)" % a, starting(weapon="sword"), a))
    if rows:
        _grid(F, rows, F.man["dirs"], 2, "Decision 44: the villagers' work (each tool in the hands, the weapon put away) and "
              "the player's place poses, S SE E NE N (red bar = contact frame)", label_w=220).save(OUT / "12_work.png")


if __name__ == "__main__":
    # python3 tools/art/topdown/review_character.py --work: the per-action sheets of docs/redesign/feedback/work_poses/
    if "--work" in sys.argv:
        for p in work_sheets(Figures(load_built())):
            print("wrote", p.relative_to(ROOT))
