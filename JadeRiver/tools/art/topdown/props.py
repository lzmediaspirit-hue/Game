"""The prop kit for Riverside Square (art bible §8): drawn at art resolution, lit from the upper left, outlined.

Each prop is (draw, sprite w, h, footprint w, h in tiles, origin, solid, shadow). `origin` is the footprint's south-west
corner inside the sprite, which the Phase 1 loader puts on the floor the prop stands on; `shadow` is the floor shadow
the compositor lays under it, [dx, dy, rx, ry] of an ellipse from the footprint's south-west corner in art px (the
Phase 1 loader ignores it). The kinds the Phase 1 room places keep their footprints and origins' meaning.
"""
from __future__ import annotations

import tiles as tl
from canvas import Img, h01
from palette import (BAMBOO, BRONZER, DARKWOOD, DIRT, GOLDR, JADE, BJADE, LANTERN, LEAF, LOTUS, MIST, MOSS, PAD, PAPER,
                     PLASTER, RED, REED, ROOF, STONE, WATER, WOOD, alpha, c)


def _curl(s: Img, x: int, y: int, d: int) -> None:
    """An upturned roof-ridge end: a short hook rising outward, tipped in gold."""
    for k, (dx, dy) in enumerate(((0, 0), (1, -1), (2, -2), (2, -3), (1, -4))):
        s.put(x + d * dx, y + dy, ROOF[1] if k < 4 else GOLDR[2])
    s.put(x + d * 1, y - 2, ROOF[3])


def house(s: Img) -> None:
    """A river-town house, footprint 6 x 3 tiles, walls two levels high. The roof's top is the footprint raised by the
    walls: an even plane of grey tiles with a low crest along it, so it reads as a floor you can land on (decision
    29). Under it: a row of round tile ends, whitewashed walls in a dark timber frame, lattice windows, a red lacquer
    door between red columns, two paper lanterns, a granite plinth. Sprite 104 x 92; footprint's south-west corner
    at (4, 90)."""
    fx, fy = 4, 90
    R0 = fy - 32 - 48 - 2
    # Walls (y fy-32 .. fy), drawn from the face tiles so a house built on the height grid looks the same.
    for k in range(6):
        x = fx + k * 16
        kind = "door" if k in (2, 3) else "window" if k in (1, 4) else "plain"
        panel = tl.plaster_face(30 + k, kind)
        if kind == "door":
            panel = tl.plaster_face(30 + k, "plain")
        s.paste(panel, x, fy - 16)
        s.paste(tl.plaster_face(40 + k, "plain", False), x, fy - 32)
    # The door bay: red columns and a double door across the two middle bays.
    d0 = fx + 34
    s.rect(d0, fy - 28, 28, 25, RED[1])
    for x0 in (d0 + 3, d0 + 14):
        s.rect(x0, fy - 24, 11, 21, RED[3])
        s.vline(x0, fy - 24, 21, RED[4])
        for yy in (fy - 18, fy - 11):
            s.put(x0 + 8, yy, GOLDR[2])
    s.vline(d0 + 14, fy - 24, 21, RED[0])
    for cx in (d0 - 2, d0 + 28):
        s.rect(cx, fy - 30, 3, 27, RED[2])
        s.vline(cx, fy - 30, 27, RED[4])
        s.vline(cx + 2, fy - 30, 27, RED[1])
    s.rect(d0 + 8, fy - 29, 12, 4, DARKWOOD[1])            # the name board: gold frame, no writing
    s.rect(d0 + 9, fy - 28, 10, 2, GOLDR[1])
    s.hline(d0 + 1, fy - 3, 26, STONE[5])                  # the threshold
    # The lattice windows on the side bays of the upper panels are left plain; windows sit on the lower row.
    # The eave's shadow on the wall.
    for i in range(fx, fx + 96):
        for r, a in enumerate((150, 110, 70, 35)):
            s.blend(i, fy - 32 + r, c("0B2A30"), a)
    # Roof plane: 104 wide (4 px of overhang each side), 50 deep, tiles from the atlas's roof top.
    roof = tl.roof_top(9)
    for y in range(R0, fy - 30):
        for x in range(0, 104):
            col = roof.get(x % 16, (y - R0) % 16)
            s.put(x, y, col)
    # The north strip beyond the crest leans away: a step darker.
    ridge = R0 + 12
    for y in range(R0, ridge):
        for x in range(0, 104):
            s.blend(x, y, c("0B2A30"), 70)
    # Verges: a lit west edge, a shaded east edge.
    for y in range(R0, fy - 30):
        s.put(0, y, ROOF[6])
        s.put(1, y, ROOF[5])
        s.put(102, y, ROOF[2])
        s.put(103, y, ROOF[1])
    # The crest: a low ridge of stacked tiles with openwork, curled ends.
    s.rect(2, ridge - 2, 100, 1, ROOF[5])
    s.rect(2, ridge - 1, 100, 2, ROOF[3])
    s.rect(2, ridge + 1, 100, 1, ROOF[1])
    for x in range(6, 98, 8):
        s.put(x, ridge - 1, ROOF[1])
        s.put(x + 1, ridge - 1, ROOF[1])
    s.rect(50, ridge - 4, 4, 3, JADE)                      # a jade pearl at the crest's middle
    s.put(51, ridge - 4, BJADE)
    _curl(s, 2, ridge - 2, -1)
    _curl(s, 101, ridge - 2, 1)
    # The eave's front: a lit verge and round tile ends (the same drawing as the eave face tile).
    eave = tl.eave_face(16)
    for x in range(0, 104):
        for r in range(6):
            s.put(x, fy - 30 + r, eave.get(x % 16, r))
    s.outline()


def willow(s: Img) -> None:
    """A river willow, footprint 1 x 1: a leaning trunk and a crown of hanging strands lit from the upper left.
    48 x 64; the trunk base's footprint corner at (16, 62)."""
    for j in range(30, 62):
        lean = (62 - j) // 8
        x = 21 + lean
        s.rect(x, j, 6, 1, WOOD[2])
        s.put(x, j, WOOD[4])
        s.put(x + 1, j, WOOD[3])
        s.put(x + 5, j, DARKWOOD[1])
    s.rect(18, 60, 12, 2, WOOD[1])
    s.put(18, 60, WOOD[3])
    blobs = ((24, 16, 17, 12), (11, 24, 10, 8), (37, 23, 10, 8), (24, 27, 14, 9))
    for cx, cy, rx, ry in blobs:
        s.ellipse(cx, cy, rx, ry, LEAF[3], (LEAF[4], LEAF[2]))
    for i in range(3, 46):
        if h01(i, 0, 21) < 0.55:
            ln = 10 + int(h01(i, 1, 21) * 20)
            start = 18 + int(h01(i, 2, 21) * 8)
            for j in range(start, min(58, start + ln)):
                col = LEAF[3] if (j + i) % 4 else LEAF[4]
                if i > 30:
                    col = LEAF[2] if (j + i) % 4 else LEAF[3]
                s.put(i, j, col)
            s.put(i, min(58, start + ln), LEAF[5] if i < 30 else LEAF[3])
    for k in range(40):
        x, y = 8 + int(h01(k, 7, 22) * 30), 5 + int(h01(k, 8, 22) * 18)
        if (x - 24) + (y - 16) < 6:
            s.put(x, y, LEAF[5] if k % 3 else LEAF[6])
    s.outline()


def lantern(s: Img) -> None:
    """A granite garden lantern, footprint 1 x 1: plinth, post, a lamp chamber glowing warm, a cap with upturned
    corners, a jade finial. 16 x 32; base corner at (0, 30)."""
    s.rect(2, 27, 12, 3, STONE[3])
    s.hline(2, 27, 12, STONE[5])
    s.rect(5, 19, 6, 8, STONE[3])
    s.vline(5, 19, 8, STONE[5])
    s.vline(10, 19, 8, STONE[2])
    s.rect(3, 17, 10, 2, STONE[4])
    s.rect(4, 11, 8, 6, STONE[3])
    s.rect(6, 12, 4, 4, LANTERN[4])
    s.rect(7, 13, 2, 2, LANTERN[5])
    s.vline(4, 11, 6, STONE[5])
    s.rect(1, 9, 14, 2, ROOF[3])
    s.hline(1, 9, 14, ROOF[5])
    s.put(0, 8, ROOF[3])
    s.put(15, 8, ROOF[2])
    s.rect(4, 6, 8, 3, ROOF[4])
    s.hline(4, 6, 8, ROOF[5])
    s.rect(7, 3, 2, 3, JADE)
    s.put(7, 3, BJADE)
    s.outline()


def lantern_red(s: Img) -> None:
    """A red lacquer post with a bracket and a round paper lantern, footprint 1 x 1. 16 x 40; base corner (0, 38)."""
    s.rect(3, 35, 8, 3, STONE[3])
    s.hline(3, 35, 8, STONE[5])
    s.rect(5, 4, 3, 31, RED[2])
    s.vline(5, 4, 31, RED[4])
    s.vline(7, 4, 31, RED[1])
    s.rect(4, 3, 5, 2, GOLDR[2])
    s.rect(7, 7, 7, 2, DARKWOOD[2])
    s.hline(7, 7, 7, DARKWOOD[4])
    s.vline(12, 9, 2, DARKWOOD[1])
    s.ellipse(12.5, 16, 3.6, 4.6, LANTERN[2], (LANTERN[4], LANTERN[0]))
    s.rect(11, 14, 2, 3, LANTERN[5])
    s.hline(10, 11, 5, GOLDR[1])
    s.hline(10, 20, 5, GOLDR[1])
    s.vline(12, 21, 3, GOLDR[2])
    s.outline()


def barrel(s: Img) -> None:
    """A water barrel with bronze hoops, footprint 1 x 1. 16 x 20; base corner (0, 18)."""
    s.ellipse(8, 14, 6, 4, WOOD[2])
    s.rect(2, 7, 12, 8, WOOD[3])
    s.rect(2, 7, 2, 8, WOOD[4])
    s.rect(12, 7, 2, 8, WOOD[2])
    for x in (6, 9):
        s.vline(x, 8, 7, WOOD[2])
    s.ellipse(8, 7, 6, 2.6, WOOD[4])
    s.ellipse(8, 7.3, 4.4, 1.6, WATER[3])
    s.put(6, 7, WATER[6])
    for y in (9, 14):
        s.hline(2, y, 12, BRONZER[3])
        s.put(3, y, BRONZER[5])
    s.outline()


def crates(s: Img) -> None:
    """Crates and a rice sack, footprint 2 x 1. 32 x 30; base corner (0, 28)."""
    def box(bx: int, by: int, w: int, h: int) -> None:
        s.rect(bx, by, w, 4, WOOD[4])                 # the lid, seen from above
        s.hline(bx, by, w, WOOD[5])
        s.rect(bx, by + 4, w, h - 4, WOOD[3])          # the front
        s.vline(bx, by + 4, h - 4, WOOD[4])
        s.vline(bx + w - 1, by + 4, h - 4, WOOD[2])
        s.hline(bx, by + 4, w, DARKWOOD[2])
        for k in range(h - 6):
            s.put(bx + 1 + k * (w - 3) // max(1, h - 7), by + 5 + k, WOOD[2])
    box(1, 13, 15, 15)
    box(10, 2, 13, 12)
    s.ellipse(24, 21, 6, 7, DIRT[5], (DIRT[6], DIRT[3]))      # a rice sack, tied at the neck
    s.rect(22, 13, 4, 2, DIRT[4])
    s.hline(21, 15, 6, DIRT[2])
    s.rect(22, 21, 4, 3, RED[3])                             # its red seal
    s.outline()


def notice(s: Img) -> None:
    """A notice board under a little tiled roof on red posts, footprint 2 x 1. 32 x 32; base corner (0, 30)."""
    for x in (4, 26):
        s.rect(x, 6, 2, 24, RED[2])
        s.vline(x, 6, 24, RED[4])
    s.rect(1, 3, 30, 3, ROOF[3])
    s.hline(1, 3, 30, ROOF[5])
    s.hline(1, 5, 30, ROOF[1])
    s.put(0, 2, ROOF[3])
    s.put(31, 2, ROOF[2])
    s.rect(6, 7, 20, 14, WOOD[2])
    s.hline(6, 7, 20, WOOD[4])
    for k, (px_, py_) in enumerate(((8, 9), (15, 8), (20, 12), (9, 15))):
        s.rect(px_, py_, 5, 6 if k != 3 else 4, PAPER)
        s.hline(px_, py_, 5, c("FFFBEF"))
        s.rect(px_ + 1, py_ + 2, 3, 1, STONE[2])
        if k == 1:
            s.rect(px_ + 3, py_ + 4, 1, 1, RED[3])
    s.outline()


def reeds(s: Img) -> None:
    """Reeds and cattails at the water's edge (walk through), 16 x 20; base corner (0, 18)."""
    for k in range(7):
        x = 1 + k * 2 + int(h01(k, 0, 31) * 2)
        top = 3 + int(h01(k, 1, 31) * 8)
        bend = 1 if h01(k, 2, 31) > 0.6 else 0
        for y in range(top, 19):
            s.put(x + (bend if y < top + 3 else 0), y, REED[4] if y < top + 2 else REED[3] if y < 12 else REED[2])
        if k % 2 == 0:
            s.rect(x + bend, top - 3, 1, 3, DARKWOOD[3])
            s.put(x + bend, top - 3, DARKWOOD[4])
    s.outline()


def boat(s: Img) -> None:
    """A moored river sampan under a woven bamboo canopy, 48 x 20; keel corner (0, 18)."""
    for j in range(7, 16):
        inset = max(0, abs(j - 11) - 1) * 2
        s.hline(2 + inset, j, 44 - inset * 2, WOOD[2] if j > 11 else WOOD[3])
    s.hline(3, 8, 42, WOOD[5])
    s.hline(4, 9, 40, WOOD[4])
    s.rect(6, 10, 36, 2, DARKWOOD[2])
    for y in range(1, 9):
        s.hline(15, y, 18, DIRT[5] if (y % 2) else DIRT[4])
    s.hline(15, 1, 18, DIRT[6])
    for x in range(16, 33, 3):
        s.vline(x, 2, 6, DIRT[3])
    s.hline(4, 16, 40, WATER[6])
    s.hline(8, 17, 32, WATER[5])
    s.outline()


def bamboo(s: Img) -> None:
    """A bamboo clump, footprint 1 x 1: five culms with lit west sides and pale nodes under a crown of leaf sprays,
    each spray a mass lit on its upper-left and fringed with spear leaves. 32 x 64; footprint corner at (8, 62)."""
    culms = ((10, 14, 2), (13, 8, 3), (17, 10, 2), (20, 16, 3), (23, 20, 2))
    for x, top, w in culms:
        for y in range(top, 62):
            s.put(x, y, BAMBOO[4])
            for d in range(1, w):
                s.put(x + d, y, BAMBOO[3] if d < w - 1 else BAMBOO[2])
        for y in range(top + 5 + (x % 3), 60, 8):
            s.hline(x, y, w, BAMBOO[5])
            s.hline(x, y + 1, w, BAMBOO[1])
    sprays = ((12, 12, 9, 7), (21, 9, 9, 7), (16, 20, 11, 6), (7, 24, 6, 5), (26, 22, 6, 5))
    for cx, cy, rx, ry in sprays:
        s.ellipse(cx, cy, rx, ry, BAMBOO[2], (BAMBOO[3], BAMBOO[1]))
    for k in range(70):
        x, y = 2 + int(h01(k, 1, 41) * 28), 2 + int(h01(k, 2, 41) * 28)
        if s.get(x, y)[3] == 0 and s.get(x, y + 2)[3] == 0 and s.get(x - 2, y)[3] == 0:
            continue
        d = 1 if h01(k, 3, 41) > 0.5 else -1
        lit = (x - 16) + (y - 14) < 4
        for n in range(4):
            s.put(x + d * n, y + n // 2, (BAMBOO[4] if lit else BAMBOO[3]) if n < 2 else (BAMBOO[3] if lit else BAMBOO[2]))
        if lit:
            s.put(x, y, BAMBOO[5])
    s.rect(8, 60, 18, 2, DARKWOOD[2])
    s.outline()


def lotus(s: Img) -> None:
    """Lotus pads with a flower and a bud, floating on the river (walk-through, footprint 2 x 1). 32 x 16; the corner
    at (0, 16), on the water's surface."""
    pads = ((6, 9, 5, 3), (16, 6, 6, 3.4), (26, 11, 4.5, 2.6), (13, 13, 3.6, 2.2))
    for cx, cy, rx, ry in pads:
        s.ellipse(cx, cy + 1, rx, ry, alpha(WATER[1], 255))
        s.ellipse(cx, cy, rx, ry, PAD[3], (PAD[4], PAD[2]))
        s.put(int(cx) + 1, int(cy), WATER[3])
        s.put(int(cx) + 2, int(cy), WATER[3])
        s.put(int(cx), int(cy) - 1, PAD[5])
    fx, fy = 16, 4
    s.ellipse(fx, fy + 1, 3.4, 2.2, LOTUS[1])
    for dx, dy, k in ((-2, 0, 2), (2, 0, 2), (-1, -1, 3), (1, -1, 3), (0, -2, 4), (0, 0, 2)):
        s.put(fx + dx, fy + dy, LOTUS[k])
    s.put(fx, fy, GOLDR[3])
    s.put(26, 7, LOTUS[2])
    s.put(26, 8, LOTUS[1])
    s.put(26, 9, PAD[2])


def incense(s: Img) -> None:
    """A bronze incense burner on three feet with a wisp of smoke, footprint 1 x 1. 16 x 28; corner (0, 26)."""
    for x in (3, 7, 11):
        s.rect(x, 23, 2, 3, BRONZER[2])
    s.ellipse(8, 19, 6, 4.5, BRONZER[3], (BRONZER[5], BRONZER[1]))
    s.hline(2, 16, 12, BRONZER[4])
    s.rect(1, 14, 3, 2, BRONZER[3])
    s.rect(12, 14, 3, 2, BRONZER[2])
    s.ellipse(8, 14.5, 5, 1.6, BRONZER[1])
    s.rect(7, 11, 1, 4, RED[3])
    s.put(7, 10, LANTERN[4])
    for k, (x, y) in enumerate(((8, 8), (9, 7), (9, 6), (8, 5), (7, 4), (7, 3), (8, 2))):
        s.put(x, y, alpha(MIST, 200 - k * 20))
    s.outline(0, 9, 16, 19)


def shrub(s: Img) -> None:
    """A flowering shrub, footprint 1 x 1: leaf clumps lit from the upper left, pink and white blossoms. 20 x 18;
    corner (2, 16)."""
    s.ellipse(10, 10, 8.5, 6.5, LEAF[2], (LEAF[3], LEAF[1]))
    for cx, cy, r in ((7, 8, 3.5), (12, 7, 3.5), (15, 11, 3), (6, 12, 3), (10, 12, 3)):
        s.ellipse(cx, cy, r, r * 0.8, LEAF[3], (LEAF[5], LEAF[2]))
    for k in range(8):
        x, y = 4 + int(h01(k, 1, 51) * 12), 5 + int(h01(k, 2, 51) * 8)
        s.put(x, y, LOTUS[3] if k % 2 else PAPER)
        s.put(x + 1, y + 1, LEAF[1])
    s.outline()


# kind: (draw, w, h, footprint w, h, origin, solid, shadow [dx, dy, rx, ry])
PROPS = {
    "house": (house, 104, 92, 6, 3, [4, 90], True, [100, -8, 8, 10]),
    "willow": (willow, 48, 64, 1, 1, [16, 62], True, [12, -2, 16, 6]),
    "lantern": (lantern, 16, 32, 1, 1, [0, 30], True, [10, -2, 6, 3]),
    "barrel": (barrel, 16, 20, 1, 1, [0, 18], True, [10, -2, 6, 3]),
    "crates": (crates, 32, 30, 2, 1, [0, 28], True, [20, -2, 12, 4]),
    "notice": (notice, 32, 32, 2, 1, [0, 30], True, [20, -2, 11, 3]),
    "reeds": (reeds, 16, 20, 1, 1, [0, 18], False, None),
    "boat": (boat, 48, 20, 3, 1, [0, 18], False, None),
    "bamboo": (bamboo, 32, 64, 1, 1, [8, 62], True, [14, -2, 12, 5]),
    "lotus": (lotus, 32, 16, 2, 1, [0, 16], False, None),
    "lantern_red": (lantern_red, 16, 40, 1, 1, [0, 38], True, [10, -2, 6, 3]),
    "incense": (incense, 16, 28, 1, 1, [0, 26], True, [10, -2, 6, 3]),
    "shrub": (shrub, 20, 18, 1, 1, [2, 16], True, [12, -2, 8, 3]),
}


def build() -> tuple[Img, dict]:
    sheet = Img(256, 192)
    at, x, y, row_h = {}, 0, 0, 0
    for kind, (draw, w, h, fw, fh, origin, solid, shadow) in PROPS.items():
        if x + w > sheet.w:
            x, y, row_h = 0, y + row_h, 0
        spr = Img(w, h)
        draw(spr)
        sheet.paste(spr, x, y)
        entry = {"rect": [x, y, w, h], "footprint": [fw, fh], "origin": origin, "solid": solid}
        if shadow:
            entry["shadow"] = shadow
        at[kind] = entry
        x, row_h = x + w, max(row_h, h)
    assert y + row_h <= sheet.h, "props overflow the sheet"
    return sheet, at
