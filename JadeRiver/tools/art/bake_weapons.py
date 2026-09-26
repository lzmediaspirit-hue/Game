"""Draw the v1.1 weapon families (S47) for every registered avatar action, pose-registered to the hand:

- heavy sabre (dao): the jian's own frames, blade broadened by one art pixel and reforged in dark steel, with a
  bronze guard, so every swing keeps its arc and smear;
- folding fan: redrawn along the short blade's grip and axis in every frame, open in the strikes (a ribbed paper
  wedge) and folded while carried;
- jade flute: a bamboo-jointed tube along the same grip, longer than the blade, with a red tassel.

The grip of each source frame comes from its colours: the gold guard, the brown or dark hilt and the jade blade.
Art is drawn at native pixel scale 2 (one art pixel = 2x2 screen pixels) and registered in data/parts.json under
weapon "sabre", "fan" and "flute", mirroring the source weapon's layers, z and hidden poses. Deterministic.
Run from JadeRiver/: python3 tools/art/bake_weapons.py
"""
import json
import math
import os

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ART = os.path.join(ROOT, "art")

# The source art's palette (jade blade ramp, gold guard, hilt browns and outlines).
BLADE = [(39, 56, 65), (70, 112, 117), (91, 166, 155), (160, 211, 193), (232, 242, 220)]
GOLD = [(209, 166, 77)]
HILT = [(43, 28, 29), (65, 30, 5), (29, 19, 30)]

# Dark steel for the sabre (outline, shadow, body, light, edge gleam) and a bronze guard.
STEEL = {(39, 56, 65): (28, 30, 36), (70, 112, 117): (78, 84, 94), (91, 166, 155): (128, 136, 146),
         (160, 211, 193): (186, 192, 198), (232, 242, 220): (236, 238, 240)}
BRONZE = (176, 112, 58)
OUTLINE = (24, 18, 22, 255)

FAN_PAPER = [(242, 232, 204, 255), (222, 208, 172, 255), (196, 178, 140, 255)]
FAN_RIB = (92, 58, 34, 255)
FAN_INK = (44, 110, 104, 255)
FLUTE = [(62, 96, 58, 255), (104, 150, 88, 255), (150, 196, 120, 255)]
FLUTE_NODE = (48, 70, 40, 255)
TASSEL = (176, 40, 44, 255)


def to_art(img):
    """Sample one art pixel from each 2x2 block."""
    a = np.array(img)
    return a[::2, ::2].copy()


def to_screen(art):
    return Image.fromarray(np.repeat(np.repeat(art, 2, axis=0), 2, axis=1), "RGBA")


def mask_of(art, colours):
    m = np.zeros(art.shape[:2], bool)
    for c in colours:
        m |= (art[:, :, 0] == c[0]) & (art[:, :, 1] == c[1]) & (art[:, :, 2] == c[2]) & (art[:, :, 3] > 0)
    return m


# ------------------------------------------------------------------ the heavy sabre (from the jian's pixels)
def sabre_frame(art):
    """Broaden the blade by one art pixel on every side and reforge the colours; the hilt and guard stay put."""
    out = art.copy()
    blade = mask_of(art, BLADE)
    if not blade.any():
        return out
    grown = blade.copy()
    grown[1:, :] |= blade[:-1, :]
    grown[:-1, :] |= blade[1:, :]
    grown[:, 1:] |= blade[:, :-1]
    grown[:, :-1] |= blade[:, 1:]
    solid = art[:, :, 3] > 0
    new = grown & ~solid
    # New body pixels take the steel's mid tone; the old ones map through the steel ramp.
    for src, dst in STEEL.items():
        m = mask_of(art, [src])
        out[m, :3] = dst
    out[new] = (*STEEL[(91, 166, 155)], 255)
    # A dark rim around the broadened blade.
    body = grown | solid
    rim = np.zeros_like(body)
    rim[1:, :] |= body[:-1, :]
    rim[:-1, :] |= body[1:, :]
    rim[:, 1:] |= body[:, :-1]
    rim[:, :-1] |= body[:, 1:]
    rim &= ~body
    near_blade = np.zeros_like(body)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            near_blade |= np.roll(np.roll(grown, dy, 0), dx, 1)
    out[rim & near_blade] = (*STEEL[(39, 56, 65)], 255)
    out[mask_of(art, GOLD), :3] = BRONZE
    return out


# ------------------------------------------------------------------ the fan and flute (redrawn along the grip)
def grip_of(art):
    """(hand, tip) of the held weapon in art pixels, or None when too little of it shows."""
    blade = np.argwhere(mask_of(art, BLADE))
    guard = np.argwhere(mask_of(art, GOLD))
    hilt = np.argwhere(mask_of(art, HILT[:2]))
    if len(blade) + len(guard) < 3:
        return None
    g = guard.mean(0) if len(guard) else (hilt.mean(0) if len(hilt) else blade.mean(0))
    d = ((blade - g) ** 2).sum(1) if len(blade) else np.array([0.0])
    tip = blade[int(d.argmax())].astype(float) if len(blade) else g + np.array([0.0, 4.0])
    if len(hilt):
        dh = ((hilt - tip) ** 2).sum(1)
        hand = hilt[int(dh.argmax())].astype(float)
    else:
        hand = g - (tip - g) * 0.25
    if np.hypot(*(tip - hand)) < 2.0:
        return None
    return hand, tip


def _paint(art, pts, colour):
    h, w = art.shape[:2]
    for (y, x) in pts:
        if 0 <= y < h and 0 <= x < w:
            art[y, x] = colour


def _outline(art, solid):
    h, w = art.shape[:2]
    rim = np.zeros_like(solid)
    rim[1:, :] |= solid[:-1, :]
    rim[:-1, :] |= solid[1:, :]
    rim[:, 1:] |= solid[:, :-1]
    rim[:, :-1] |= solid[:, 1:]
    rim &= ~solid
    art[rim] = OUTLINE


def stroke(out, solid, start, end, half, colour_of):
    """Fill every art pixel within `half` of the segment start-end; colour_of(s, side) picks the colour from the
    distance along the segment (0..1) and the signed side (-1 upper .. 1 lower)."""
    h, w = out.shape[:2]
    d = end - start
    L2 = float((d ** 2).sum()) or 1.0
    n = np.array([-d[1], d[0]]) / math.sqrt(L2)
    y0, y1 = int(max(0, min(start[0], end[0]) - half - 2)), int(min(h, max(start[0], end[0]) + half + 3))
    x0, x1 = int(max(0, min(start[1], end[1]) - half - 2)), int(min(w, max(start[1], end[1]) + half + 3))
    for y in range(y0, y1):
        for x in range(x0, x1):
            p = np.array([y, x], float)
            t = float(np.clip(((p - start) * d).sum() / L2, 0.0, 1.0))
            q = start + d * t
            off = float(((p - q) * n).sum())
            if np.hypot(*(p - q)) <= half + 0.01:
                out[y, x] = colour_of(t, off / max(half, 0.5))
                solid[y, x] = True


def fan_frame(art, open_fan):
    """A folding fan pivoting in the hand, spread toward where the blade pointed."""
    g = grip_of(art)
    out = np.zeros_like(art)
    if g is None:
        return out
    hand, tip = g
    v = tip - hand
    length = np.hypot(*v)
    if not open_fan:
        # Folded: a slim paper-and-rib stick in the hand, its guards darker at the pivot.
        u = v / length
        solid = np.zeros(art.shape[:2], bool)
        end = hand + u * max(7.0, length)
        stroke(out, solid, hand - u * 0.5, end, 1.0,
               lambda t, side: FAN_RIB if t < 0.22 or t > 0.93 else (FAN_PAPER[0] if side < 0 else FAN_PAPER[2]))
        _outline(out, solid)
        hy, hx = int(round(hand[0])), int(round(hand[1]))
        _paint(out, [(hy, hx)], (209, 166, 77, 255))
        return out
    base = math.atan2(v[0], v[1])
    radius = max(5.0, length * 1.15)
    spread = math.radians(42 if open_fan else 6)
    h, w = art.shape[:2]
    solid = np.zeros((h, w), bool)
    y0, y1 = int(max(0, hand[0] - radius - 2)), int(min(h, hand[0] + radius + 3))
    x0, x1 = int(max(0, hand[1] - radius - 2)), int(min(w, hand[1] + radius + 3))
    for y in range(y0, y1):
        for x in range(x0, x1):
            dy, dx = y - hand[0], x - hand[1]
            r = math.hypot(dy, dx)
            if r > radius or r < 0.5:
                continue
            ang = math.atan2(dy, dx) - base
            ang = (ang + math.pi) % (2 * math.pi) - math.pi
            if abs(ang) > spread:
                continue
            solid[y, x] = True
            if not open_fan:
                out[y, x] = FAN_RIB if r < radius * 0.35 else FAN_PAPER[1 if (y + x) % 2 else 2]
                continue
            if r < radius * 0.38:
                out[y, x] = FAN_RIB            # the ribs gather into the handle
            else:
                t = (ang + spread) / (2 * spread)
                rib = abs((t * 6.0) - round(t * 6.0)) < 0.09
                shade = 0 if t < 0.45 else (1 if t < 0.8 else 2)
                c = FAN_PAPER[shade]
                if rib:
                    c = FAN_PAPER[2]
                if r > radius * 0.8 and 0.3 < t < 0.7:
                    c = FAN_INK                # a band of ink near the edge
                out[y, x] = c
    if solid.any():
        _outline(out, solid)
        hy, hx = int(round(hand[0])), int(round(hand[1]))
        _paint(out, [(hy, hx)], (209, 166, 77, 255))  # the brass rivet
    return out


def flute_frame(art):
    """A jade-green bamboo flute in the hand, a little longer than the blade, with a red tassel at the hand end."""
    g = grip_of(art)
    out = np.zeros_like(art)
    if g is None:
        return out
    hand, tip = g
    v = tip - hand
    length = np.hypot(*v)
    u = v / length
    n = np.array([-u[1], u[0]])
    start = hand - u * 1.5
    end = hand + u * max(6.0, length * 1.35)
    h, w = art.shape[:2]
    solid = np.zeros((h, w), bool)
    span = float(np.hypot(*(end - start)))

    def colour(t, side):
        if int(t * span) % 5 == 4:
            return FLUTE_NODE                  # a bamboo joint
        return FLUTE[2] if side < -0.2 else (FLUTE[1] if side < 0.5 else FLUTE[0])
    stroke(out, solid, start, end, 1.0, colour)
    # Finger holes: dark dots along the upper side, toward the far end.
    for f in (0.55, 0.68, 0.81):
        q = start + (end - start) * f
        _paint(out, [(int(round(q[0])), int(round(q[1])))], (30, 40, 26, 255))
    if solid.any():
        _outline(out, solid)
    # The tassel hangs from the hand end.
    ty, tx = int(round(start[0])), int(round(start[1]))
    _paint(out, [(ty + 1, tx), (ty + 2, tx), (ty + 3, tx), (ty + 3, tx - 1), (ty + 3, tx + 1)], TASSEL)
    return out


OPEN_ACTIONS = {"attack", "punch", "punch_1", "punch_2", "punch_3", "swing", "swing_1", "swing_2", "swing_3",
                "thrust_1", "thrust_2", "thrust_3", "bow"}


def bake(parts, weapon_id, source_id, label, frame_fn):
    src_item = parts["weapon"][source_id]
    layers = []
    made = 0
    for li, layer in enumerate(src_item["layers"]):
        new_layer = {k: v for k, v in layer.items() if k != "animations"}
        new_layer["animations"] = {}
        for action, anim in layer["animations"].items():
            if anim.get("hidden") or not anim.get("sheets"):
                new_layer["animations"][action] = dict(anim)
                continue
            cell = int(anim.get("cell", 256))
            sheets = []
            for si, sheet_path in enumerate(anim["sheets"]):
                sheet = Image.open(os.path.join(ART, os.path.basename(sheet_path))).convert("RGBA")
                out = Image.new("RGBA", sheet.size, (0, 0, 0, 0))
                for row in range(sheet.height // cell):
                    for col in range(sheet.width // cell):
                        box = (col * cell, row * cell, (col + 1) * cell, (row + 1) * cell)
                        art = to_art(sheet.crop(box))
                        if not (art[:, :, 3] > 0).any():
                            continue
                        new = frame_fn(art, action)
                        out.paste(to_screen(new), box[:2])
                base = os.path.basename(sheet_path).replace("weapon_%s_" % source_id, "weapon_%s_" % weapon_id)
                out.save(os.path.join(ART, base), optimize=True)
                sheets.append("art_v12/" + base)
                made += 1
            entry = dict(anim)
            entry["sheets"] = sheets
            entry["source"] = "generated:bake_weapons.py from " + source_id
            entry.pop("rig", None)
            new_layer["animations"][action] = entry
        layers.append(new_layer)
    parts["weapon"][weapon_id] = {"label": label, "layers": layers}
    parts["_attack_by_weapon"][weapon_id] = parts["_attack_by_weapon"].get(source_id, "attack")
    return made


def main():
    parts_path = os.path.join(ROOT, "data", "parts.json")
    parts = json.load(open(parts_path))
    n = bake(parts, "sabre", "sword", "Heavy sabre", lambda art, action: sabre_frame(art))
    n += bake(parts, "fan", "dagger", "Iron fan", lambda art, action: fan_frame(art, action in OPEN_ACTIONS))
    n += bake(parts, "flute", "dagger", "Jade flute", lambda art, action: flute_frame(art))
    with open(parts_path, "w") as f:
        json.dump(parts, f, indent=2)
    print("WEAPONS:", n, "sheets")


if __name__ == "__main__":
    main()
