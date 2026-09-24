"""Draw the straw douli hat (Plain Straw Hat / Bamboo Hat appearance, and many NPCs)
for every registered avatar action, pose-registered to the head.

The head position of each frame comes from the existing headband layer, which
already sits on the forehead in every action, facing and combo clip. The hat is
drawn at native pixel scale 2 (one art pixel = 2x2 screen pixels) and registered in
data/parts.json as hat "straw". Deterministic.
Run from JadeRiver/: python3 tools/art/bake_straw_hat.py
"""
import json
import os
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ART = os.path.join(ROOT, "art")

OUT = (58, 40, 20, 255)
DARK = (107, 79, 36, 255)
MID = (170, 132, 70, 255)
LIGHT = (214, 176, 104, 255)
PALE = (240, 214, 150, 255)
BAND = (44, 110, 104, 255)


def hat_pixels():
    """Return {(x, y): colour} in art pixels, origin at the brim centre, right-facing."""
    px = {}
    # Cone: rows from apex (y=-7) to brim (y=0).
    for y in range(-7, 1):
        half = int(round((y + 8) * 1.05))
        for x in range(-half, half + 1):
            t = (x + half) / max(1, 2 * half)
            c = LIGHT if t < 0.35 else (MID if t < 0.75 else DARK)
            if (x + y) % 3 == 0 and y > -6:
                c = MID if c == LIGHT else DARK
            px[(x, y)] = c
    px[(0, -8)] = PALE
    px[(-1, -7)] = PALE
    # Cloth band just above the brim.
    for x in range(-5, 6):
        px[(x, -1)] = BAND
    # Brim: wide, slightly drooping at the tips.
    for x in range(-13, 14):
        yy = 1 if abs(x) < 11 else 2
        for y in range(1, yy + 1):
            c = LIGHT if x < -4 else (MID if x < 6 else DARK)
            if y == yy:
                c = DARK
            px[(x, y)] = c
    # Outline around the whole silhouette.
    solid = set(px)
    out = {}
    for (x, y) in solid:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in solid:
                out[n] = OUT
    px.update(out)
    return px


HAT = hat_pixels()


def anchor_for(cell_img):
    a = cell_img.getchannel("A")
    box = a.getbbox()
    if box is None:
        return None
    x0, y0, x1, y1 = box
    return ((x0 + x1) // 2, y0)


def draw_hat(cell_img, anchor, mirror):
    cx, top = anchor
    # Brim a little above the band's top, centred on the head.
    bx = cx // 2
    by = (top + 6) // 2
    for (x, y), c in HAT.items():
        xx = bx + (-x if mirror else x)
        yy = by + y
        if 0 <= xx * 2 < cell_img.width and 0 <= yy * 2 < cell_img.height:
            for sx in range(2):
                for sy in range(2):
                    cell_img.putpixel((xx * 2 + sx, yy * 2 + sy), c)


def main():
    parts_path = os.path.join(ROOT, "data", "parts.json")
    parts = json.load(open(parts_path))
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
                frame = sheet.crop(box)
                anchor = anchor_for(frame)
                if anchor is None:
                    continue
                hat = Image.new("RGBA", (cell, cell), (0, 0, 0, 0))
                draw_hat(hat, anchor, mirror=(row == 0))
                out.paste(hat, box[:2])
        name = "hat_straw_1_%s_0.png" % action
        out.save(os.path.join(ART, name))
        layer["animations"][action] = {"cell": cell, "sheets": ["art_v12/" + name], "z": src.get("z", 125.0),
                                       "source": "generated:bake_straw_hat.py"}
        made += 1
    parts["hat"]["straw"] = {"label": "Straw douli", "layers": [layer]}
    with open(parts_path, "w") as f:
        json.dump(parts, f, indent=2)
    print("STRAW_HAT:", made, "sheets")


if __name__ == "__main__":
    main()
