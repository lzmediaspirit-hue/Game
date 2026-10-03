"""T1 (docs/architecture/topdown_mechanics.md): the side view's traversal drawn for the height grid, at art resolution
(1 art px = 1 px of the 640x360 world view; a cell is 16 px, a level 16 px of face), lit from the upper left, outlined
as the prop kit is (art bible §4). Original pixel art, nearest neighbour; every build byte-identical (the coordinate
hash, never a random generator).

  raft_2x2      a log raft two cells square seen from above: five peeled logs lying east-west, lashed with cord at
                both ends and across the middle, a pole laid along it, the logs' cut ends and the waterline on its
                south face (32 x 38: the deck's 32 x 32 over 6 px of the logs' side and the wet line); two frames, the
                deck riding a pixel lower in the second (the raft bobs on the water's clock)
  vine_top / vine_mid / vine_foot      a climbing vine down a face, a cell wide: leaves spilling over the lip at the
                top, a tangle of stems with leaves on the face (16 px a level, tiled), roots and a leafy foot
  rope_top / rope_mid / rope_foot      a knotted rope: a stake and its knot at the lip, the twisted rope with a knot a
                level, a loose coil at the foot
  ladder_top / ladder_mid / ladder_foot   a wooden ladder leaned on the face: its rails over the lip, rungs every
                5 px, its feet on the floor
  chain_top / chain_mid / chain_foot   an iron chain: a ring bolted at the lip, links, the last links on the floor
  spray_0..3    the updraft's mist: a column of rising spray motes and a veil, one cell wide and three levels high (16 x
                48), its motes a quarter of their climb higher each frame
  glide_0..1    Falling Leaf Glide's leaf of qi spread over the body (26 x 10): a broad jade leaf, its veins lit, its
                edges fluttering between the frames
"""
from __future__ import annotations

from canvas import Img, h01
from palette import BJADE, DARKWOOD, DIRT, FOAM2, JADE, LEAF, MIST, MOSS, QI, STONE, WATER2, WOOD, alpha


def raft(s: Img, f: int = 0) -> None:
    """The log raft (see the module's docstring); frame `f` bobs the deck a pixel lower."""
    bob = 1 if f else 0
    logs = 5
    # The logs, each 6 px of round log: a lit crown, its body, the shadow where it meets the next.
    for k in range(logs):
        y0 = 1 + k * 6 + bob
        inset = (1 if k in (0, logs - 1) else 0) + int(h01(k, 1, 71) * 2)
        x0, x1 = inset, 32 - int(h01(k, 2, 71) * 2)
        for y in range(y0, y0 + 6):
            row = y - y0
            col = WOOD[5] if row == 0 else WOOD[4] if row == 1 else WOOD[3] if row < 4 else WOOD[2] if row == 4 else DARKWOOD[1]
            s.hline(x0, y, x1 - x0, col)
        # Bark seams and knots along the log, a hash a log so no two match.
        for x in range(x0 + 2, x1 - 2):
            r = h01(x, k, 72)
            if r < 0.12:
                s.put(x, y0 + 2, WOOD[2])
            elif r < 0.16:
                s.put(x, y0 + 3, DARKWOOD[2])
                s.put(x + 1, y0 + 3, DARKWOOD[2])
        # The cut ends: pale end grain with its rings.
        for x in (x0, x1 - 1):
            for y in range(y0 + 1, y0 + 5):
                s.put(x, y, WOOD[6] if y == y0 + 1 else WOOD[5])
            s.put(x, y0 + 2 + (1 if x == x0 else 0), WOOD[3])
    # Lashings: cord wound round every log at both ends and across the middle.
    for cx in (5, 16, 27):
        for y in range(1 + bob, logs * 6 + 1 + bob):
            s.put(cx, y, DIRT[5] if y % 3 else DIRT[3])
            s.put(cx + 1, y, DIRT[4] if y % 3 else DIRT[2])
    # The pole laid along the deck.
    for x in range(3, 30):
        s.put(x, 9 + bob, DARKWOOD[3] if x % 7 else DARKWOOD[2])
        s.put(x, 10 + bob, DARKWOOD[1])
    s.put(2, 9 + bob, DARKWOOD[4])
    # The south face: the last log's side in shade, then the waterline wet and foaming.
    base = logs * 6 + 1 + bob
    for x in range(1, 31):
        s.put(x, base, DARKWOOD[2])
        s.put(x, base + 1, DARKWOOD[1] if x % 5 else DARKWOOD[0])
    for x in range(0, 32):
        r = h01(x, f, 73)
        s.put(x, base + 2, FOAM2 if r < 0.35 else WATER2[6])
        if r < 0.2:
            s.put(x, base + 3, alpha(FOAM2, 160))
    s.outline()


def vine(s: Img, part: str) -> None:
    """A tile of the vine down a face: `top` (leaves over the lip), `mid` (stems and leaves, tiles a level), `foot`."""
    stems = (4, 8, 11)
    for i, sx in enumerate(stems):
        for y in range(16):
            x = sx + (1 if (y + i * 3) % 8 < 4 else 0)
            if part == "top" and y < 4 - i:
                continue
            s.put(x, y, MOSS[1] if i == 1 else MOSS[2])
            s.put(x + 1, y, MOSS[0])
    # Leaves: little three-pixel blades in pairs, lit on their upper left.
    n = 9 if part == "top" else 6
    for k in range(n):
        lx = 1 + int(h01(k, ord(part[0]), 74) * 13)
        ly = int(h01(k, 3, 74 + len(part)) * 14) + (0 if part != "top" else -2)
        if part == "top":
            ly = min(ly, 9)
        for dx, dy, c in ((0, 0, LEAF[5]), (1, 0, LEAF[4]), (1, 1, LEAF[3]), (2, 1, LEAF[2])):
            s.put(lx + dx, ly + dy, c)
    if part == "top":   # a fringe of leaves spilling over the lip
        for x in range(0, 16):
            if h01(x, 5, 75) < 0.7:
                s.put(x, 0, LEAF[6] if x % 3 == 0 else LEAF[5])
                s.put(x, 1, LEAF[4])
    if part == "foot":  # roots into the floor and a leafy clump
        for x in range(2, 14):
            if h01(x, 6, 76) < 0.6:
                s.put(x, 15, LEAF[3])
                s.put(x, 14, LEAF[4] if x % 2 else MOSS[3])
        for x in (4, 9, 12):
            s.put(x, 13, DIRT[2])
    s.outline()


def rope(s: Img, part: str) -> None:
    """A tile of the knotted rope: `top` (a stake driven at the lip, the rope's knot), `mid`, `foot` (a loose coil)."""
    cx = 7
    if part == "top":
        s.rect(cx - 1, 0, 3, 5, WOOD[4])
        s.vline(cx - 1, 0, 5, WOOD[5])
        s.vline(cx + 1, 0, 5, WOOD[2])
        s.hline(cx - 2, 4, 5, DIRT[4])
    top = 5 if part == "top" else 0
    end = 10 if part == "foot" else 16
    for y in range(top, end):
        twist = (y // 2) % 2
        s.put(cx, y, DIRT[5] if twist else DIRT[4])
        s.put(cx + 1, y, DIRT[3] if twist else DIRT[2])
    if part == "mid":   # a knot a level
        s.rect(cx - 1, 7, 4, 3, DIRT[4])
        s.hline(cx - 1, 7, 3, DIRT[6])
        s.hline(cx - 1, 9, 4, DIRT[2])
    if part == "foot":  # the coil lying on the floor
        for x in range(2, 14):
            s.put(x, 11, DIRT[5] if x % 2 else DIRT[4])
            s.put(x, 12, DIRT[3])
            s.put(x, 13, DIRT[4] if x % 3 else DIRT[2])
        s.put(1, 12, DIRT[4])
        s.put(14, 12, DIRT[3])
    s.outline()


def ladder(s: Img, part: str) -> None:
    """A tile of the wooden ladder leaned on the face: `top` (the rails' tips over the lip), `mid` (rungs), `foot`."""
    for x, lit in ((2, True), (12, False)):
        for y in range(16):
            s.put(x, y, WOOD[5] if lit else WOOD[4])
            s.put(x + 1, y, WOOD[3] if lit else WOOD[2])
    for y in range(2 if part != "top" else 4, 16, 5):
        s.hline(4, y, 8, WOOD[4])
        s.hline(4, y + 1, 8, DARKWOOD[2])
    if part == "top":
        for x in (2, 12):
            s.put(x, 0, WOOD[6])
    if part == "foot":
        for x in (1, 2, 3, 11, 12, 13):
            s.put(x, 15, DARKWOOD[1])
    s.outline()


def chain(s: Img, part: str) -> None:
    """A tile of the iron chain: `top` (a ring bolted at the lip), `mid` (links, a level), `foot` (links on the floor)."""
    cx = 6
    if part == "top":
        s.rect(cx - 1, 0, 5, 3, STONE[2])
        s.put(cx + 1, 1, STONE[5])
    start = 3 if part == "top" else 0
    end = 11 if part == "foot" else 16
    for i, y in enumerate(range(start, end, 4)):
        if i % 2 == 0:  # a link seen face on: a ring
            s.rect(cx, y, 4, 4, STONE[3])
            s.rect(cx + 1, y + 1, 2, 2, (0, 0, 0, 0))
            s.put(cx, y, STONE[5])
        else:           # a link edge on: a bar
            s.rect(cx + 1, y, 2, 4, STONE[4])
            s.put(cx + 2, y + 3, STONE[2])
    if part == "foot":
        for x in range(1, 13, 3):
            s.rect(x, 12, 3, 2, STONE[3])
            s.put(x, 12, STONE[5])
    s.outline()


def spray(s: Img, f: int) -> None:
    """The updraft's column of rising spray in frame `f` (16 x 48)."""
    for y in range(48):
        k = y / 47.0
        for x in range(16):
            edge = min(x, 15 - x)
            veil = h01(x, (y + f * 3) // 3, 77)
            if edge > 1 and veil < 0.22 * (0.4 + k):
                s.put(x, y, alpha(MIST, 60 + int(50 * k)))
    for m in range(14):
        x = 2 + int(h01(m, 1, 78) * 12)
        y = int((h01(m, 2, 78) * 48 - f * 4 - m * 3) % 48)
        s.put(x, y, alpha(FOAM2, 220))
        if m % 3 == 0:
            s.put(x, y + 1, alpha(WATER2[7], 170))


def glide(s: Img, f: int) -> None:
    """The leaf of qi spread over a gliding body (26 x 10): a broad jade leaf, veins lit, its tips fluttering."""
    w, h = 26, 10
    cx = w / 2.0
    for y in range(h):
        for x in range(w):
            u = (x + 0.5 - cx) / cx
            lift = (1.0 if f and abs(u) > 0.7 else 0.0)           # the tips flutter up in the second frame
            top = 1.0 + 4.5 * (u * u) - lift                        # a canopy: high over the body, its tips down
            bottom = top + 1.2 + 3.4 * (1.0 - u * u)
            if top <= y + 0.5 <= bottom:
                rim = y + 0.5 - top < 1.0 or bottom - (y + 0.5) < 1.0
                col = BJADE if rim and (u < 0 or y + 0.5 - top < 1.0) else JADE if rim else QI if abs(u) < 0.06 else JADE
                s.put(x, y, alpha(col, 235 if rim else 175))
    for x in range(4, w - 4, 3):   # the veins across it, lit
        u = (x + 0.5 - cx) / cx
        s.put(x, int(1.0 + 4.5 * u * u + 1.8 * (1.0 - u * u)), alpha(BJADE, 230))


SPRITES = {
    "raft_2x2": (32, 38, 2, raft),
    "vine_top": (16, 16, 0, lambda s: vine(s, "top")), "vine_mid": (16, 16, 0, lambda s: vine(s, "mid")),
    "vine_foot": (16, 16, 0, lambda s: vine(s, "foot")),
    "rope_top": (16, 16, 0, lambda s: rope(s, "top")), "rope_mid": (16, 16, 0, lambda s: rope(s, "mid")),
    "rope_foot": (16, 16, 0, lambda s: rope(s, "foot")),
    "ladder_top": (16, 16, 0, lambda s: ladder(s, "top")), "ladder_mid": (16, 16, 0, lambda s: ladder(s, "mid")),
    "ladder_foot": (16, 16, 0, lambda s: ladder(s, "foot")),
    "chain_top": (16, 16, 0, lambda s: chain(s, "top")), "chain_mid": (16, 16, 0, lambda s: chain(s, "mid")),
    "chain_foot": (16, 16, 0, lambda s: chain(s, "foot")),
    "spray": (16, 48, 4, spray),
    "glide": (26, 10, 2, glide),
}


def sprites() -> dict:
    """Every sprite: name -> (Img, frames). Animated ones hold their frames side by side."""
    out = {}
    for name, (w, h, frames, draw) in SPRITES.items():
        n = max(1, frames)
        img = Img(w * n, h)
        for f in range(n):
            one = Img(w, h)
            if frames:
                draw(one, f)
            else:
                draw(one)
            img.paste(one, f * w, 0)
        out[name] = (img, n, w)
    return out
