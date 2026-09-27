"""Draw the gauntlets on both hands in every registered avatar action (the action catalog, parts.json "_actions").

The gauntlet family had no avatar look (its appearance was "none"), so a gauntlet in the weapon slot drew bare fists.
This bake gives it one: weapon "gauntlets", one sheet per action and layer, frame for frame with the body.

Every frame is registered to the body's own hands, found in that frame and facing (no rig, no idle fallback):
- the hand is the body's skin past the wrist of the long-sleeved robe (the cardigan), clear of the trousers and
  shoes; where that skin meets the head, what any shirt covers is the neck or the robe's open collar;
- the forearm is the body the long sleeve covers and the sleeveless shirt leaves bare;
- the fist is redrawn over the hand's own pixels in steel, its shading and outline taken from the body's tones, so it
  keeps the hand's shape, knuckles and light, with a bronze rim at the wrist (seen under any sleeve); the cuff wraps
  the forearm next to the wrist (seen with bare arms): a steel plate closed by a second bronze band.

Layer order: each gauntlet pixel sits just over the body layer that draws that pixel of the hand, so it is hidden
wherever the bare hand is (behind the torso, under a wide sleeve, trousers, hair, the head or a held weapon) and the
cuff shows only where the forearm does (the sleeveless shirt). Layer "1" follows body layer "1" (z 10) at z 12;
layer "4" follows body layer "4", the generated jab's and lotus pose's fists (z 90), at z 92 and is an explicit
hidden entry where that body layer is hidden.

Art is drawn at native pixel scale 2 (one art pixel = 2x2 screen pixels). Deterministic.
Run from JadeRiver/: python3 tools/art/bake_gauntlets.py
"""
import json
import os
from collections import deque

import numpy as np
from PIL import Image

from bake_weapons import ART, ROOT, BRONZE, STEEL, to_art, to_screen

WEAPON_ID = "gauntlets"
LABEL = "Gauntlets"
CELL = 256
ART_CELL = CELL // 2
HEAD_Z = 100                         # body layers from here up are the head and face
ABOVE = 2                            # a gauntlet layer's z over the body layer it covers
LONG_SLEEVE = "cardigan"             # its sleeves end at the wrist
BARE_ARMS = "sleeveless"
# The steel ramp (outline, shadow, body, light, gleam) is the heavy sabre's; the trim is its bronze guard.
OUTLINE, SHADOW, BODY, LIGHT, GLEAM = [(*c, 255) for c in STEEL.values()]
TRIM = [(222, 168, 92, 255), (*BRONZE, 255), (120, 72, 38, 255)]
CUFF_DEPTH = 2                       # art px of forearm the cuff covers from the wrist
HAND_REACH = 7                       # art px: a bare patch reaching further from the robed body is an arm ending in a hand
HAND_LEN = 5                         # art px back from the fingertips that the fist covers on a bare arm
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))


def lum(px):
    return 0.299 * float(px[0]) + 0.587 * float(px[1]) + 0.114 * float(px[2])


def shift(m, dy, dx):
    out = np.zeros_like(m)
    h, w = m.shape
    out[max(0, dy):h + min(0, dy), max(0, dx):w + min(0, dx)] = m[max(0, -dy):h + min(0, -dy), max(0, -dx):w + min(0, -dx)]
    return out


def near(m, steps=N4):
    out = m.copy()
    for dy, dx in steps:
        out |= shift(m, dy, dx)
    return out


def components(m):
    """8-connected components of a mask, each a boolean mask, in scan order."""
    seen = np.zeros_like(m)
    out = []
    for y, x in zip(*np.nonzero(m)):
        if seen[y, x]:
            continue
        comp = np.zeros_like(m)
        queue = deque([(y, x)])
        seen[y, x] = True
        while queue:
            cy, cx = queue.popleft()
            comp[cy, cx] = True
            for dy, dx in N8:
                ny, nx = cy + dy, cx + dx
                if 0 <= ny < m.shape[0] and 0 <= nx < m.shape[1] and m[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    queue.append((ny, nx))
        out.append(comp)
    return out


class Sheets:
    """Art-pixel frames of the registered layers (row 0 faces left, row 1 right)."""

    def __init__(self, parts):
        self.parts = parts
        self.images = {}

    def frame(self, sheet, row, col):
        if sheet not in self.images:
            self.images[sheet] = to_art(Image.open(os.path.join(ART, os.path.basename(sheet))).convert("RGBA"))
        a = self.images[sheet]
        n = max(1, a.shape[1] // ART_CELL)
        return a[row * ART_CELL:(row + 1) * ART_CELL, (col % n) * ART_CELL:(col % n + 1) * ART_CELL]

    def layers(self, category, item, action):
        """(section, z, animation) of each drawn layer, bottom first."""
        out = []
        for layer in self.parts[category][item]["layers"]:
            anim = layer["animations"][action]
            if not anim.get("hidden") and anim.get("sheets"):
                assert int(anim.get("cell", CELL)) == CELL, (category, item, action)
                out.append((layer["section"], float(anim.get("z", layer["z"])), anim))
        return sorted(out, key=lambda e: e[1])

    def alpha(self, category, item, action, row, col):
        m = np.zeros((ART_CELL, ART_CELL), bool)
        for _, _, anim in self.layers(category, item, action):
            m |= self.frame(anim["sheets"][0], row, col)[:, :, 3] > 0
        return m


def body_of(s, action, row, col):
    """The body's colour below the head, which body layer (index into `under`) draws each pixel, and the head."""
    colour = np.zeros((ART_CELL, ART_CELL, 4), np.uint8)
    source = np.full((ART_CELL, ART_CELL), -1, np.int32)
    head = np.zeros((ART_CELL, ART_CELL), bool)
    under = []
    for section, z, anim in s.layers("body", "light", action):
        f = s.frame(anim["sheets"][0], row, col)
        m = f[:, :, 3] > 0
        if z >= HEAD_Z:
            head |= m
            continue
        colour[m] = f[m]
        source[m] = len(under)
        under.append((section, z))
    source[head] = -1
    return colour, source, head, under


def hands_of(s, action, row, col):
    """The body, its hands (at most two masks, largest first) and its forearm mask in one frame."""
    colour, source, head, under = body_of(s, action, row, col)
    body = source >= 0
    lower = np.zeros_like(body)
    for category in ("pants", "shoes"):
        for item in s.parts[category]:
            lower |= s.alpha(category, item, action, row, col)
    sleeve = s.alpha("shirt", LONG_SLEEVE, action, row, col)
    bare = body & ~lower & ~sleeve
    forearm = body & ~lower & sleeve & ~s.alpha("shirt", BARE_ARMS, action, row, col)
    skin = np.array([[lum(px) >= 60 for px in line] for line in colour]) & bare
    robed = np.zeros_like(head)                        # skin some shirt covers: the collar and chest, not a hand
    for item in s.parts["shirt"]:
        robed |= s.alpha("shirt", item, action, row, col)
    hands = []
    for comp in components(bare):
        if (comp & skin).sum() < 2:
            continue                                  # an outline sliver between two garments
        if (near(comp) & head).any():
            comp = comp & ~robed                      # the neck and the robe's open collar under the chin
            if (comp & skin).sum() < 2:
                continue
        hands.append(comp)
    hands.sort(key=lambda m: -int(m.sum()))
    fists = [fist_of(comp, forearm, body) for comp in hands[:2]]
    return colour, source, under, [f for f, _ in fists], [a for _, a in fists]


def fist_of(comp, forearm, body):
    """(fist, arm): a bare patch the size of a hand is the fist and the covered forearm is its arm. Where the robe
    leaves the whole arm bare (the long sleeve's own art in some bow, swing and thrust frames), the patch reaches
    more than HAND_REACH px from the robed body: the fist is its last HAND_LEN px, counted along the arm from where
    it leaves the body, and the rest of the patch is arm."""
    region = comp | forearm
    root = comp & near(body & ~region)               # where the bare patch leaves the robed torso
    if not root.any():
        return comp, forearm
    dist = np.full(comp.shape, -1, np.int32)
    dist[root] = 0
    queue = deque(zip(*np.nonzero(root)))
    while queue:
        y, x = queue.popleft()
        for dy, dx in N4:
            ny, nx = y + dy, x + dx
            if 0 <= ny < comp.shape[0] and 0 <= nx < comp.shape[1] and region[ny, nx] and dist[ny, nx] < 0:
                dist[ny, nx] = dist[y, x] + 1
                queue.append((ny, nx))
    reach = dist[comp].max()
    if reach <= HAND_REACH:
        return comp, forearm
    fist = comp & (dist >= reach - HAND_LEN)
    return fist, (forearm | comp) & ~fist


def cuff_of(hand, forearm):
    """Forearm pixels by their step distance from the wrist (1 = touching the hand), up to CUFF_DEPTH."""
    depth = np.zeros(hand.shape, np.int32)
    ring = hand
    for d in range(1, CUFF_DEPTH + 1):
        ring = near(ring) & forearm & (depth == 0) & ~hand
        depth[ring] = d
    return depth


def steel(px, light_side):
    """The steel tone for a body pixel: the body's outline stays an outline, its skin tones become steel tones one
    step darker on the side away from the light (below the hand's middle)."""
    v = lum(px)
    if v < 60:
        return OUTLINE
    if v >= 230:
        return GLEAM
    if v >= 195:
        return LIGHT if light_side else BODY
    if v >= 150:
        return BODY if light_side else SHADOW
    return SHADOW


def trim(px):
    v = lum(px)
    return OUTLINE if v < 60 else (TRIM[0] if v >= 195 else (TRIM[1] if v >= 150 else TRIM[2]))


def gauntlet_frame(s, action, row, col):
    """The gauntlets' art in this frame, split by the body layer each pixel covers: {body section: art}."""
    colour, source, under, hands, arms = hands_of(s, action, row, col)
    art = np.zeros_like(colour)
    for hand, forearm in zip(hands, arms):
        ys, _ = np.nonzero(hand)
        cy = ys.mean()
        wrist = hand & near(forearm)                 # the fist's rim where the sleeve or cuff ends
        for y, x in zip(*np.nonzero(hand)):
            art[y, x] = trim(colour[y, x]) if wrist[y, x] else steel(colour[y, x], y < cy)
        depth = cuff_of(hand, forearm)
        for y, x in zip(*np.nonzero(depth)):
            d, v = depth[y, x], lum(colour[y, x])
            if v < 60:
                art[y, x] = OUTLINE
            elif d == CUFF_DEPTH:
                art[y, x] = trim(colour[y, x])
            else:
                art[y, x] = steel(colour[y, x], True)
    split = {}
    for i, (section, _) in enumerate(under):
        part = np.zeros_like(art)
        m = source == i
        part[m] = art[m]
        split[section] = part
    return split, len(hands)


def main():
    parts_path = os.path.join(ROOT, "data", "parts.json")
    parts = json.load(open(parts_path))
    s = Sheets(parts)
    below_head = [(l["section"], float(l["z"])) for l in parts["body"]["light"]["layers"] if float(l["z"]) < HEAD_Z]
    layers = {section: {"section": section, "z": z + ABOVE, "animations": {}} for section, z in below_head}
    report = []
    made = 0
    for action in sorted(parts["_actions"]):
        frames = int(parts["_actions"][action]["frames"])
        sheets = {section: np.zeros((ART_CELL * 2, frames * ART_CELL, 4), np.uint8) for section, _ in below_head}
        counts = []
        for row in (0, 1):
            for col in range(frames):
                split, n = gauntlet_frame(s, action, row, col)
                for section, art in split.items():
                    sheets[section][row * ART_CELL:(row + 1) * ART_CELL, col * ART_CELL:(col + 1) * ART_CELL] = art
                counts.append(str(n))
        for section, _ in below_head:
            anims = layers[section]["animations"]
            body_anim = next(l for l in parts["body"]["light"]["layers"] if l["section"] == section)["animations"][action]
            if body_anim.get("hidden") or not sheets[section][:, :, 3].any():
                anims[action] = {"hidden": True, "reason": "The body draws no hand on this layer in this pose"}
                continue
            name = "weapon_%s_%s_%s_0.png" % (WEAPON_ID, section, action)
            to_screen(sheets[section]).save(os.path.join(ART, name), optimize=True)
            anims[action] = {"cell": float(CELL), "sheets": ["art_v12/" + name], "z": layers[section]["z"],
                             "source": "generated:bake_gauntlets.py over body light layer " + section,
                             "fallback": None}
            made += 1
        report.append("%-9s %s | %s" % (action, "".join(counts[:frames]), "".join(counts[frames:])))
    # hand_rig marks art drawn per pose here: tests/bake_combos.gd leaves it alone rather than re-rig it as a held weapon.
    parts["weapon"][WEAPON_ID] = {"label": LABEL, "hand_rig": "tools/art/bake_gauntlets.py",
                                  "layers": [layers[section] for section, _ in below_head]}
    parts["_attack_by_weapon"][WEAPON_ID] = "punch"
    with open(parts_path, "w") as f:
        json.dump(parts, f, indent=2)
    print("GAUNTLETS: %d sheets; hands per frame (facing left | facing right):" % made)
    print("\n".join(report))


if __name__ == "__main__":
    main()
