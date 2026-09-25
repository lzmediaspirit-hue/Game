"""Draw the Act II avatar hats for every registered avatar action, pose-registered to the head:

* "guan"   - a small jade-and-gold hair crown with a hairpin, worn by Nine Peaks Alliance officials
             and sect elders of the Expanse.
* "weimao" - a black lacquered bamboo hat with a gauze veil that hangs to the shoulders, worn by
             travellers who would rather not be known (brokers, the Grey Pilgrim).

Same method as bake_straw_hat.py: the head position of each frame comes from the headband layer,
which sits on the forehead in every action and facing. Drawn at native pixel scale 2 and registered
in data/parts.json. Deterministic. Run from JadeRiver/: python3 tools/art/bake_act2_hats.py
The combo clips are then baked with tools/bake_hat_cape_combos.gd.
"""
import json
import os
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ART = os.path.join(ROOT, "art")

INK = (22, 26, 34, 255)


def _outline(px, ink=INK, skip=()):
    solid = {k for k, v in px.items() if v[3] == 255}
    out = {}
    for (x, y) in solid:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in px and n not in skip:
                out[n] = ink
    px.update(out)
    return px


def guan_pixels():
    """A crown of jade plates bound in gold, pinned through with a long gold hairpin.
    Origin: top centre of the head; right-facing (the pin's head is on the right)."""
    JADE_D, JADE, JADE_L = (18, 94, 86, 255), (44, 158, 143, 255), (138, 230, 204, 255)
    GOLD_D, GOLD, GOLD_L = (120, 82, 30, 255), (214, 166, 62, 255), (255, 226, 150, 255)
    px = {}
    # crown body: a rounded cap over the topknot
    for y in range(-5, 1):
        half = 3 if y > -4 else 2
        for x in range(-half, half + 1):
            c = JADE_L if x < -1 else (JADE if x < 2 else JADE_D)
            if y == 0:
                c = GOLD_D if x > 0 else GOLD
            px[(x, y)] = c
    px[(-1, -6)] = GOLD_L
    px[(0, -6)] = GOLD
    px[(1, -6)] = GOLD_D
    # gold band across the crown
    for x in range(-3, 4):
        px[(x, -2)] = GOLD_L if x < 0 else GOLD
    _outline(px)
    # the hairpin, drawn over the outline so it reads through
    for x in range(-7, 8):
        px[(x, -3)] = GOLD_L if x < 0 else GOLD
    px[(8, -3)] = GOLD_L
    px[(8, -4)] = JADE_L
    px[(9, -3)] = JADE
    px[(8, -2)] = JADE_D
    px[(-8, -3)] = GOLD_D
    return px


def weimao_pixels():
    """Black lacquered bamboo hat, a red cord, and a veil of pale gauze to below the chin.
    Origin: the brim centre; right-facing."""
    BLACK, DARK, MID, SHEEN = (24, 26, 32, 255), (40, 44, 54, 255), (62, 68, 82, 255), (104, 112, 128, 255)
    CORD = (164, 46, 42, 255)
    VEIL, VEIL_D, VEIL_EDGE = (226, 232, 236, 130), (190, 200, 208, 140), (240, 244, 246, 175)
    px = {}
    # low crown
    for y in range(-5, 1):
        half = int(round((y + 7) * 0.9))
        for x in range(-half, half + 1):
            t = (x + half) / max(1, 2 * half)
            px[(x, y)] = SHEEN if t < 0.25 else (MID if t < 0.6 else DARK)
    for x in range(-5, 6):
        px[(x, -1)] = CORD
    # wide flat brim
    for x in range(-12, 13):
        px[(x, 1)] = MID if x < -3 else (DARK if x < 6 else BLACK)
    _outline(px)
    # the veil hangs from the brim edge: a sheer curtain with folds (not outlined)
    for x in range(-12, 13):
        drop = 15 + (1 if x % 4 == 0 else 0) - (1 if x % 5 == 2 else 0) - (2 if abs(x) == 12 else 0)
        for y in range(2, drop):
            c = VEIL_D if (x % 3 == 0) else VEIL
            if y == drop - 1:
                c = VEIL_EDGE
            if (x, y) not in px:
                px[(x, y)] = c
    return px


HATS = {
    "guan": {"label": "Jade crown", "pixels": guan_pixels(), "dy": -3, "dx": -1},
    "weimao": {"label": "Veiled hat", "pixels": weimao_pixels(), "dy": 1, "dx": 0},
}


def anchor_for(cell_img):
    a = cell_img.getchannel("A")
    box = a.getbbox()
    if box is None:
        return None
    x0, y0, x1, y1 = box
    return ((x0 + x1) // 2, y0)


def draw_hat(cell_img, anchor, mirror, pixels, dy, dx=0):
    cx, top = anchor
    bx = cx // 2 + (-dx if mirror else dx)
    by = (top + dy) // 2
    for (x, y), c in pixels.items():
        xx = bx + (-x if mirror else x)
        yy = by + y
        if 0 <= xx * 2 < cell_img.width and 0 <= yy * 2 < cell_img.height:
            for sx in range(2):
                for sy in range(2):
                    cell_img.putpixel((xx * 2 + sx, yy * 2 + sy), c)


def bake(parts, hat_id, spec):
    band = parts["hat"]["headband"]["layers"][0]["animations"]
    layer = {"section": "1", "z": 125.0, "animations": {}}
    made = 0
    for action in parts["_actions"]:
        src = band.get(action)
        if src is None or src.get("hidden"):
            layer["animations"][action] = {"hidden": True, "reason": "No head in this pose"}
            continue
        cell = int(src.get("cell", 256))
        sheet = Image.open(os.path.join(ART, os.path.basename(src["sheets"][0]))).convert("RGBA")
        out = Image.new("RGBA", sheet.size, (0, 0, 0, 0))
        cols = sheet.width // cell
        for row in range(2):
            for col in range(cols):
                box = (col * cell, row * cell, (col + 1) * cell, (row + 1) * cell)
                anchor = anchor_for(sheet.crop(box))
                if anchor is None:
                    continue
                hat = Image.new("RGBA", (cell, cell), (0, 0, 0, 0))
                draw_hat(hat, anchor, row == 0, spec["pixels"], spec["dy"], spec.get("dx", 0))
                out.paste(hat, box[:2])
        name = "hat_%s_1_%s_0.png" % (hat_id, action)
        out.save(os.path.join(ART, name))
        layer["animations"][action] = {"cell": cell, "sheets": ["art_v12/" + name], "z": src.get("z", 125.0),
                                       "source": "generated:bake_act2_hats.py"}
        made += 1
    parts["hat"][hat_id] = {"label": spec["label"], "layers": [layer]}
    return made


def main():
    parts_path = os.path.join(ROOT, "data", "parts.json")
    parts = json.load(open(parts_path))
    for hat_id, spec in HATS.items():
        print("HAT %s:" % hat_id, bake(parts, hat_id, spec), "sheets")
    with open(parts_path, "w") as f:
        json.dump(parts, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
