"""The prop kit (art bible §8), for Riverside Square, the tutorial's rooms and chapter 2's sects and marsh: drawn at art
resolution, lit from the upper left, outlined.

Each prop is (draw, sprite w, h, footprint w, h in tiles, origin, solid, shadow). `origin` is the footprint's south-west
corner inside the sprite, which the room view puts on the floor the prop stands on; `shadow` is its floor shadow,
[dx, dy, rx, ry] of an ellipse from the footprint's south-west corner in art px, drawn into the sheet as its own sprite
(`shadow_rect`, placed at `shadow_at` from that corner) that the room view lays on the floor under the prop. Animated
props (`ANIM`) hold their frames side by side. The kinds the Phase 1 room places keep their footprints and origins.
"""
from __future__ import annotations

import falls as FA
import foliage as FL
import furnish as FU
import terrain2 as T2
import tiles as tl
from canvas import Img, h01
from palette import (BAMBOO, BARK, BRONZER, CLOUD, DARKWOOD, DIRT, GOLDR, HOLLOW, JADE, BJADE, LANTERN, LEAF, LOTUS,
                     MIST, MOSS, PAD, PAPER, PINE, PLASTER, RED, REED, ROCK, ROOF, SHADE, STONE, WATER, WOOD, alpha, c)


def _curl(s: Img, x: int, y: int, d: int) -> None:
    """An upturned roof-ridge end: a short hook rising outward, tipped in gold."""
    for k, (dx, dy) in enumerate(((0, 0), (1, -1), (2, -2), (2, -3), (1, -4))):
        s.put(x + d * dx, y + dy, ROOF[1] if k < 4 else GOLDR[2])
    s.put(x + d * 1, y - 2, ROOF[3])


def house(s: Img, tw: int = 6, store: bool = False, hall: bool = False) -> None:
    """A river-town house, footprint tw x 3 tiles, walls two levels high. The roof's top is the footprint raised by the
    walls: an even plane of grey tiles with a low crest along it, so it reads as a floor you can land on (decision
    29; the manifest's `top` makes it one). Under it: a row of round tile ends, whitewashed walls in a dark timber
    frame, lattice windows beside the door bay, a granite plinth. A house has a red lacquer door between red columns
    and two paper lanterns; a storehouse (`store`) has barred timber doors and high vents. A sect hall (`hall`) fronts
    the house with a red colonnade, one column at every bay, gilt bracket ends under the eave, a dressed granite plinth
    and a gold-framed jade name board (art bible §9: the sects' red halls). Sprite tw*16+8 x 92; the footprint's
    south-west corner at (4, 90)."""
    fx, fy = 4, 90
    W = tw * 16 + 8
    R0 = fy - 32 - 48 - 2
    left, right = tw // 2 - 1, tw // 2
    # Walls (y fy-32 .. fy), drawn from the face tiles so a house built on the height grid looks the same.
    for k in range(tw):
        x = fx + k * 16
        kind = "window" if (k in (left - 1, right + 1) and not store) else "plain"
        s.paste(tl.plaster_face(30 + k, kind), x, fy - 16)
        s.paste(tl.plaster_face(40 + k, "plain", False), x, fy - 32)
        if store and k not in (left, right):
            for i in range(0, 6, 2):                           # a high vent
                s.rect(x + 5 + i, fy - 23, 1, 3, DARKWOOD[1])
    # The door bay across the two middle bays.
    d0 = fx + left * 16 + 2
    leaf = (RED[1], RED[3], RED[4], RED[0]) if not store else (DARKWOOD[1], WOOD[3], WOOD[4], DARKWOOD[0])
    s.rect(d0, fy - 28, 28, 25, leaf[0])
    for x0 in (d0 + 3, d0 + 14):
        s.rect(x0, fy - 24, 11, 21, leaf[1])
        s.vline(x0, fy - 24, 21, leaf[2])
        for yy in (fy - 18, fy - 11):
            s.put(x0 + 8, yy, GOLDR[2] if not store else DARKWOOD[1])
    s.vline(d0 + 14, fy - 24, 21, leaf[3])
    if store:
        s.rect(d0 + 3, fy - 15, 22, 2, DARKWOOD[2])            # the bar across the doors
        s.hline(d0 + 3, fy - 15, 22, WOOD[5])
    else:
        for cx in (d0 - 2, d0 + 28):                           # red columns
            s.rect(cx, fy - 30, 3, 27, RED[2])
            s.vline(cx, fy - 30, 27, RED[4])
            s.vline(cx + 2, fy - 30, 27, RED[1])
        s.rect(d0 + 8, fy - 29, 12, 4, DARKWOOD[1])            # the name board: gold frame, no writing
        s.rect(d0 + 9, fy - 28, 10, 2, GOLDR[1])
        for lx in (d0 - 7, d0 + 32):                           # paper lanterns under the eave
            s.vline(lx + 1, fy - 28, 2, DARKWOOD[1])
            s.ellipse(lx + 1.5, fy - 23, 2.6, 3.2, LANTERN[2], (LANTERN[4], LANTERN[0]))
            s.put(lx + 1, fy - 24, LANTERN[5])
            s.put(lx + 1, fy - 19, GOLDR[2])
    if hall:
        s.rect(fx, fy - 3, tw * 16, 3, STONE[3])               # the dressed plinth the colonnade stands on
        s.hline(fx, fy - 3, tw * 16, STONE[5])
        s.hline(fx, fy - 1, tw * 16, STONE[2])
        for k in range(tw + 1):                                # a red column at every bay, gilt bracket ends over it
            if k in (left, right + 1):
                continue
            cx = min(max(fx + k * 16 - 1, fx), fx + tw * 16 - 3)
            s.rect(cx, fy - 30, 3, 27, RED[2])
            s.vline(cx, fy - 30, 27, RED[4])
            s.vline(cx + 2, fy - 30, 27, RED[1])
            s.rect(cx, fy - 31, 3, 1, GOLDR[2])
        s.rect(d0 + 5, fy - 23, 18, 6, GOLDR[1])               # the name board over the door: jade in a gold frame
        s.rect(d0 + 6, fy - 22, 16, 4, JADE)
        s.hline(d0 + 6, fy - 22, 16, BJADE)
        s.hline(d0 + 5, fy - 23, 18, GOLDR[3])
        for x in (d0 + 9, d0 + 13, d0 + 17):                   # three gilt characters, unreadable at this size
            s.rect(x, fy - 21, 2, 2, GOLDR[2])
    s.hline(d0 + 1, fy - 3, 26, STONE[5])                      # the threshold
    _roof(s, W, R0, fy, store)
    s.outline()


def _roof(s: Img, W: int, R0: int, fy: int, store: bool) -> None:
    """A river-town roof in dark glazed tile (Terrain v2, art bible "Terrain v2" buildings), W wide from row R0 to the
    eave at fy - 30: rows of round cover tiles (each a small glazed cylinder, a glint down its sunlit west flank) between
    shaded channels, the courses lapping every 4 px; the courses, the ridge and the eave sweep up toward both ends (a
    few px, the curve of a Jade River roof) while the plane itself stays even, a floor you can land on (decision 29).
    The far strip beyond the ridge faces the north-west sun, a step lighter; the verges are lit west and shaded east;
    the heavy ridge has openwork, curled ends tipped in gold and, on a house, a jade pearl; under the eave's round
    tile ends the dark soffit and a deep blue-violet shadow band lie on the wall."""
    ridge = R0 + 12
    eave_y = fy - 30

    def sweep(x: int) -> int:
        u = abs(x + 0.5 - W / 2) / (W / 2)
        return int(u ** 3 * 3.6)

    for i in range(4, W - 4):                                  # the eave's shadow on the wall, under the soffit
        for r, a in enumerate((180, 130, 85, 45, 20)):
            s.blend(i, fy - 24 + r, T2.SHADOW, a)
    for x in range(W):
        lift = sweep(x)
        for y in range(R0 - lift, eave_y - lift):
            yy = y + lift - R0
            c4, row = x % 4, (yy - 12) % 6
            far = y + lift < ridge
            k = (4, 4, 3, 1)[c4]
            if c4 == 0 and row in (2, 3):
                k = 6                                          # the glaze's glint down a cover tile's sunlit flank
            if row == 5 and c4 < 3:
                k += 1                                         # a tile's lower lip, lit
            elif row == 0:
                k = max(0, k - 2) if c4 < 3 else 0             # the shadow under the lap
            if not far and yy > (eave_y - R0) * 2 // 3 and c4 == 3:
                k = 0
            if far:
                k = min(6, k + 1)
            if x < 2:
                k = 6 - x
            elif x >= W - 2:
                k = 2 - (x - (W - 2))
            col = T2.ROOF2[k]
            if T2.hp(x // 4, yy // 4, 7, 256, 256) < 0.06 and c4 < 3:
                col = T2.mix(col, T2.SUN, 0.12)
            s.put(x, y, col)
        # the ridge: stacked ridge tiles, a lit top, openwork, a dark underside
        ry = ridge - lift
        if 2 <= x < W - 2:
            for r, k in ((-3, 6), (-2, 5), (-1, 3), (0, 3), (1, 1)):
                s.put(x, ry + r, T2.ROOF2[k])
        if 6 <= x < W - 6 and (x - 6) % 8 in (0, 1):
            s.put(x, ry - 1, T2.ROOF2[1])
        # the eave: round tile ends along the swept line, the dark soffit under them
        ey = eave_y - lift
        eave = T2.eave_face(16)
        for r in range(6):
            s.put(x, ey + r, eave.get(x % 16, r))
        for r in range(lift):
            s.put(x, ey + 6 + r, T2.ROOF2[0])
    if not store:
        s.rect(W // 2 - 2, ridge - 6, 4, 3, JADE)              # a jade pearl at the ridge's middle
        s.put(W // 2 - 1, ridge - 6, BJADE)
        s.put(W // 2 + 1, ridge - 4, JADE)
    _curl(s, 2, ridge - 2 - sweep(2), -1)
    _curl(s, W - 3, ridge - 2 - sweep(W - 3), 1)


def storehouse(s: Img) -> None:
    house(s, 4, True)


def hall(s: Img) -> None:
    house(s, 8, hall=True)


def willow(s: Img, f: int = 0) -> None:
    """A river willow, footprint 1 x 1: a leaning trunk and a crown of hanging strands lit from the upper left. The
    strands' lower halves sway a pixel east and back over four frames (art bible §7). 48 x 64; the trunk base's
    footprint corner at (16, 62)."""
    sway = SWAY[f]
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
                s.put(i + (sway if j > start + ln // 2 else 0), j, col)
            s.put(i + sway, min(58, start + ln), LEAF[5] if i < 30 else LEAF[3])
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


def lantern_red(s: Img, f: int = 0) -> None:
    """A red lacquer post with a bracket and a round paper lantern, footprint 1 x 1. 16 x 40; base corner (0, 38).
    Decision 43: four frames of the lantern swinging on its cord in the wind (still, a pixel east, still, a pixel west;
    the room view turns them on the wind's clock), its tassel trailing a frame behind."""
    d = (0, 1, 0, -1)[f]
    s.rect(3, 35, 8, 3, STONE[3])
    s.hline(3, 35, 8, STONE[5])
    s.rect(5, 4, 3, 31, RED[2])
    s.vline(5, 4, 31, RED[4])
    s.vline(7, 4, 31, RED[1])
    s.rect(4, 3, 5, 2, GOLDR[2])
    s.rect(7, 7, 7, 2, DARKWOOD[2])
    s.hline(7, 7, 7, DARKWOOD[4])
    s.put(12, 9, DARKWOOD[1])
    s.put(12 + d, 10, DARKWOOD[1])
    s.ellipse(12.5 + d, 16, 3.6, 4.6, LANTERN[2], (LANTERN[4], LANTERN[0]))
    s.rect(11 + d, 14, 2, 3, LANTERN[5])
    s.hline(10 + d, 11, 5, GOLDR[1])
    s.hline(10 + d, 20, 5, GOLDR[1])
    t = (0, 1, 1, -1)[f] if f else 0
    s.vline(12 + d, 21, 2, GOLDR[2])
    s.put(12 + d + t, 23, GOLDR[2])
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
    """Two lashed crates, footprint 2 x 1, one level high: their lids are a floor you can jump onto (the manifest's
    `top`). Lids of east-west planks seen from above, fronts with a frame and a diagonal brace, a rope over both, a
    merchant's red seal. 32 x 34; base corner (0, 32)."""
    for bx in (0, 16):
        for j in range(16):                                    # the lid: the footprint raised one level
            for i in range(16):
                k = j % 4
                col = WOOD[5] if k == 0 else WOOD[4] if k < 3 else WOOD[2]
                if i == 0 or j == 0:
                    col = WOOD[6]
                elif i == 15:
                    col = WOOD[3]
                s.put(bx + i, j, col)
        for j in range(16, 32):                                # the front
            for i in range(16):
                col = WOOD[3]
                if i in (0, 1) or j in (17, 18):
                    col = WOOD[4]
                elif i in (14, 15) or j in (30, 31):
                    col = WOOD[2]
                s.put(bx + i, j, col)
        for k in range(11):                                    # the brace
            s.put(bx + 3 + k, 29 - k, WOOD[5])
            s.put(bx + 3 + k, 28 - k, WOOD[2])
        s.hline(bx, 16, 16, DARKWOOD[1])
    s.vline(16, 0, 32, DARKWOOD[1])
    for j in range(0, 32):                                     # the rope
        s.put(22, j, DIRT[5] if j % 3 else DIRT[3])
    s.rect(3, 4, 5, 4, RED[3])
    s.hline(3, 4, 5, RED[4])
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


def reeds(s: Img, grey: bool = False) -> None:
    """Reeds and cattails at the water's edge (walk through), 16 x 20; base corner (0, 18). `grey`: reeds the
    Hollowing has drained (the marsh's grey patches), ash-grey and brittle, their heads bare."""
    ramp, head = (HOLLOW[1:], HOLLOW[1:]) if grey else (REED, DARKWOOD)
    for k in range(7):
        x = 1 + k * 2 + int(h01(k, 0, 31) * 2)
        top = 3 + int(h01(k, 1, 31) * 8)
        bend = (1 if h01(k, 2, 31) > 0.6 else 0) + (1 if grey and k % 3 == 1 else 0)
        for y in range(top, 19):
            s.put(x + (bend if y < top + 3 else 0), y, ramp[4] if y < top + 2 else ramp[3] if y < 12 else ramp[2])
        if k % 2 == 0:
            s.rect(x + bend, top - 3, 1, 3, head[3])
            s.put(x + bend, top - 3, head[4])
    s.outline()


def grey_reeds(s: Img) -> None:
    reeds(s, True)


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


def bamboo(s: Img, f: int = 0) -> None:
    """A bamboo clump, footprint 1 x 1: five culms with lit west sides and pale nodes under a crown of leaf sprays,
    each spray a mass lit on its upper-left and fringed with spear leaves. The crown and the culms' upper halves sway a
    pixel east and back over four frames (art bible §7). 32 x 64; footprint corner at (8, 62)."""
    sway = SWAY[f]
    culms = ((10, 14, 2), (13, 8, 3), (17, 10, 2), (20, 16, 3), (23, 20, 2))
    for x, top, w in culms:
        for y in range(top, 62):
            bend = sway if y < 36 else 0
            s.put(x + bend, y, BAMBOO[4])
            for d in range(1, w):
                s.put(x + bend + d, y, BAMBOO[3] if d < w - 1 else BAMBOO[2])
        for y in range(top + 5 + (x % 3), 60, 8):
            bend = sway if y < 36 else 0
            s.hline(x + bend, y, w, BAMBOO[5])
            s.hline(x + bend, y + 1, w, BAMBOO[1])
    sprays = ((12, 12, 9, 7), (21, 9, 9, 7), (16, 20, 11, 6), (7, 24, 6, 5), (26, 22, 6, 5))
    for cx, cy, rx, ry in sprays:
        s.ellipse(cx + sway, cy, rx, ry, BAMBOO[2], (BAMBOO[3], BAMBOO[1]))
    for k in range(70):
        x, y = 2 + int(h01(k, 1, 41) * 28) + sway, 2 + int(h01(k, 2, 41) * 28)
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


def lotus(s: Img, f: int = 0) -> None:
    """Lotus pads with a flower and a bud, floating on the river (walk-through, footprint 2 x 1). The flower and the bud
    bob a pixel on the water's clock (art bible §7). 32 x 16; the corner at (0, 16), on the water's surface."""
    bob = -SWAY[f]
    pads = ((6, 9, 5, 3), (16, 6, 6, 3.4), (26, 11, 4.5, 2.6), (13, 13, 3.6, 2.2))
    for cx, cy, rx, ry in pads:
        s.ellipse(cx, cy + 1, rx, ry, alpha(WATER[1], 255))
        s.ellipse(cx, cy, rx, ry, PAD[3], (PAD[4], PAD[2]))
        s.put(int(cx) + 1, int(cy), WATER[3])
        s.put(int(cx) + 2, int(cy), WATER[3])
        s.put(int(cx), int(cy) - 1, PAD[5])
    fx, fy = 16, 4 + bob
    s.ellipse(fx, fy + 1, 3.4, 2.2, LOTUS[1])
    for dx, dy, k in ((-2, 0, 2), (2, 0, 2), (-1, -1, 3), (1, -1, 3), (0, -2, 4), (0, 0, 2)):
        s.put(fx + dx, fy + dy, LOTUS[k])
    s.put(fx, fy, GOLDR[3])
    s.put(26, 7 + bob, LOTUS[2])
    s.put(26, 8 + bob, LOTUS[1])
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


def pine(s: Img) -> None:
    """A sect-garden mountain pine, footprint 1 x 1: a straight red-brown trunk with shallow bark fissures, branches
    holding three flat tiers of needles out to the sides (the top tier widest, the lower ones offset west and east),
    each tier lit along its upper-left rim, needled on its face and dark underneath. 40 x 64; the trunk's footprint
    corner at (12, 62)."""
    for j in range(16, 62):
        x = 17 + (1 if j < 36 else 0)
        s.rect(x, j, 5, 1, BARK[2])
        s.put(x, j, BARK[4])
        s.put(x + 1, j, BARK[3])
        s.put(x + 4, j, BARK[1])
        if h01(j, 0, 61) < 0.22:
            s.put(x + 2, j, BARK[1])
    s.rect(14, 60, 11, 2, BARK[1])
    s.put(14, 60, BARK[3])
    for (x0, y0), (x1, y1) in (((18, 30), (10, 25)), ((21, 38), (30, 34)), ((19, 20), (13, 13))):
        n = max(abs(x1 - x0), abs(y1 - y0))
        for k in range(n + 1):
            s.put(x0 + (x1 - x0) * k // n, y0 + (y1 - y0) * k // n, BARK[2])
            s.put(x0 + (x1 - x0) * k // n, y0 + (y1 - y0) * k // n + 1, BARK[1])
    for cx, cy, rx, ry in ((20, 11, 17, 6), (11, 24, 9, 5), (29, 33, 9, 4.5)):
        s.ellipse(cx, cy + 1.5, rx, ry, PINE[1])                   # the tier's shaded underside
        s.ellipse(cx, cy, rx, ry, PINE[3], (PINE[5], PINE[2]))
        for k in range(int(rx * ry * 0.9)):                        # needle tufts: lit toward the sun, dark away
            x, y = int(cx - rx + h01(k, 1, int(cx * 7 + cy)) * rx * 2), int(cy - ry + h01(k, 2, int(cx * 7 + cy)) * ry * 2)
            if s.get(x, y)[3] == 0:
                continue
            lit = (x - cx) / rx + (y - cy) / ry < -0.3
            s.put(x, y, PINE[4] if lit else PINE[2])
            s.put(x + 1, y, PINE[5] if lit and k % 3 == 0 else PINE[3])
        for i in range(int(cx - rx) + 2, int(cx + rx) - 1):        # the sunlit crown line
            for j in range(int(cy - ry), int(cy)):
                if s.get(i, j)[3] and not s.get(i, j - 1)[3]:
                    s.put(i, j, PINE[6] if (i - cx) < 0 else PINE[5])
                    break
    s.outline()


def weapon_rack(s: Img) -> None:
    """A Weapon Hall's rack in dark wood, footprint 2 x 1: two posts, a top rail and a foot rail holding (west to
    east) a spear with a red tassel, a jian with a gilt guard, a broad dao and a staff, their steel lit from the upper
    left. 32 x 40; base corner (0, 38)."""
    s.rect(0, 30, 32, 8, DARKWOOD[2])                              # the foot box: its lid, then its front
    s.hline(0, 30, 32, DARKWOOD[4])
    s.rect(0, 33, 32, 5, DARKWOOD[1])
    s.hline(0, 33, 32, DARKWOOD[3])
    for x in (1, 28):                                              # posts
        s.rect(x, 4, 3, 30, DARKWOOD[2])
        s.vline(x, 4, 30, DARKWOOD[4])
        s.rect(x - 1, 2, 5, 2, GOLDR[1])
    s.rect(1, 8, 30, 2, DARKWOOD[3])                               # the top rail, lit on its upper edge
    s.hline(1, 8, 30, WOOD[4])
    # The spear: a long shaft, a leaf blade and a red tassel under it.
    s.vline(7, 5, 27, WOOD[3])
    s.vline(8, 5, 27, WOOD[2])
    s.rect(7, 0, 2, 5, STONE[5])
    s.put(7, 0, STONE[6])
    s.rect(6, 5, 4, 3, RED[3])
    s.put(6, 5, RED[5])
    # The jian: a straight double-edged blade, a gilt guard, a dark grip and pommel.
    s.vline(13, 2, 20, STONE[6])
    s.vline(14, 2, 20, STONE[4])
    s.rect(11, 22, 6, 2, GOLDR[2])
    s.hline(11, 22, 6, GOLDR[3])
    s.rect(13, 24, 2, 6, DARKWOOD[1])
    s.rect(12, 29, 4, 1, GOLDR[1])
    # The dao: a broad single-edged blade curving back at its tip.
    for j in range(4, 21):
        w = 3 if j > 6 else 2
        s.rect(19, j, w, 1, STONE[4])
        s.put(19, j, STONE[6])
        s.put(19 + w - 1, j, STONE[3])
    s.put(21, 3, STONE[5])
    s.rect(18, 21, 5, 2, BRONZER[3])
    s.rect(20, 23, 2, 7, RED[1])
    # The staff: plain wood, iron-shod ends.
    s.vline(25, 1, 30, WOOD[4])
    s.vline(26, 1, 30, WOOD[2])
    s.rect(25, 1, 2, 2, STONE[3])
    s.rect(1, 25, 30, 2, DARKWOOD[3])                              # the lower rail over the weapons' feet
    s.hline(1, 25, 30, WOOD[4])
    s.outline()


def banner(s: Img, cloud: bool = False, f: int = 0) -> None:
    """A sect banner on a tall lacquered pole, footprint 1 x 1: a stone socket, the pole, a gilt finial and cross-arm,
    and the long silk hanging from it in the sect's colours: the Jade Sect's jade with a gold ring, the Cloud Sect's
    white with a sky-blue cloud scroll. It stirs a pixel at its tail over four frames. 16 x 60; base corner (0, 58)."""
    s.rect(3, 54, 10, 4, STONE[3])
    s.hline(3, 54, 10, STONE[5])
    s.rect(5, 6, 2, 49, RED[2] if not cloud else DARKWOOD[3])
    s.vline(5, 6, 49, RED[4] if not cloud else WOOD[4])
    s.rect(4, 3, 4, 3, GOLDR[2])
    s.put(5, 2, GOLDR[3])
    s.rect(5, 7, 9, 2, GOLDR[1])
    s.hline(5, 7, 9, GOLDR[3])
    silk = (JADE, BJADE, c("15514F")) if not cloud else (CLOUD[3], CLOUD[4], CLOUD[1])
    for j in range(9, 40):
        tail = SWAY[f] if j > 30 else 0
        s.rect(7 + tail, j, 6, 1, silk[0])
        s.put(7 + tail, j, silk[1])
        s.put(12 + tail, j, silk[2])
    for k in range(3):                                             # the swallow-tail end
        s.put(8 + k, 40 + k, silk[0])
        s.put(12 - k, 40 + k, silk[0])
    if not cloud:
        for dx, dy in ((0, -2), (1, -2), (2, -1), (2, 0), (2, 1), (1, 2), (0, 2), (-1, 1), (-1, 0), (-1, -1)):
            s.put(9 + dx, 18 + dy, GOLDR[2])
        s.hline(8, 28, 4, GOLDR[1])
    else:
        for x, y in ((8, 17), (9, 16), (10, 16), (11, 17), (10, 18), (9, 19), (10, 20), (11, 20), (8, 25), (9, 24), (10, 25)):
            s.put(x, y, CLOUD[0])
    s.outline()


def banner_jade(s: Img, f: int = 0) -> None:
    banner(s, False, f)


def banner_cloud(s: Img, f: int = 0) -> None:
    banner(s, True, f)


def post(s: Img) -> None:
    """A training stump, footprint 1 x 1: a timber post driven into the ground and cut flat, scarred where the blows
    land, bound with straw rope at striking height. 16 x 30; base corner (0, 28)."""
    s.ellipse(8, 27, 6, 2.5, DARKWOOD[1])
    s.rect(3, 6, 10, 21, WOOD[3])
    s.rect(3, 6, 2, 21, WOOD[5])
    s.rect(11, 6, 2, 21, WOOD[2])
    s.ellipse(8, 6, 5, 2.2, WOOD[5], (WOOD[6], WOOD[3]))           # the cut top, its rings
    s.put(8, 6, WOOD[3])
    s.put(6, 6, WOOD[4])
    for y in (12, 15, 18):                                         # the straw binding
        s.hline(3, y, 10, DIRT[5])
        s.hline(3, y + 1, 10, DIRT[3])
    for y in (9, 22):                                              # blade scars
        s.put(6, y, WOOD[1])
        s.put(7, y + 1, WOOD[1])
    s.outline()


def dead_tree(s: Img) -> None:
    """A tree the grey has drained (the Hollowing in the marsh), footprint 1 x 1: a split trunk and bare, crooked
    branches in cold ash grey with dark cracks, a few last leaves hanging grey. 40 x 56; base corner (12, 54)."""
    for j in range(22, 54):
        lean = (54 - j) // 10
        x = 17 - lean
        s.rect(x, j, 5, 1, HOLLOW[2])
        s.put(x, j, HOLLOW[4])
        s.put(x + 1, j, HOLLOW[3])
        s.put(x + 4, j, HOLLOW[1])
        if h01(j, 1, 71) < 0.25:
            s.put(x + 2, j, HOLLOW[0])
    s.rect(13, 52, 12, 2, HOLLOW[1])
    s.put(13, 52, HOLLOW[3])
    for (x0, y0), (x1, y1) in (((16, 26), (5, 12)), ((18, 24), (30, 8)), ((17, 34), (32, 26)), ((15, 30), (7, 24)),
                               ((24, 16), (27, 5)), ((9, 17), (4, 4)), ((28, 28), (35, 22))):
        n = max(abs(x1 - x0), abs(y1 - y0))
        for k in range(n + 1):
            x, y = x0 + (x1 - x0) * k // n, y0 + (y1 - y0) * k // n
            s.put(x, y, HOLLOW[3] if k < n * 0.6 else HOLLOW[4])
            if k < n * 0.5:
                s.put(x + 1, y, HOLLOW[1])
    for k in range(9):                                             # the last leaves, drained
        x, y = 4 + int(h01(k, 3, 72) * 32), 6 + int(h01(k, 4, 72) * 20)
        if s.get(x, y)[3] or s.get(x, y - 1)[3]:
            s.put(x, y + 1, HOLLOW[4])
            s.put(x, y + 2, HOLLOW[3])
    s.outline()


def boulder(s: Img) -> None:
    """A karst boulder, footprint 1 x 1: pale limestone in two lumps lit from the upper left, a fissure between them,
    moss gathered in its top hollows. 24 x 22; base corner (4, 20)."""
    s.ellipse(12, 13, 10, 7.5, ROCK[3], (ROCK[5], ROCK[1]))
    s.ellipse(8, 10, 6, 5, ROCK[4], (ROCK[6], ROCK[2]))
    s.ellipse(16, 17, 6, 3, ROCK[2])
    for k in range(6):
        x, y = 5 + int(h01(k, 1, 81) * 12), 5 + int(h01(k, 2, 81) * 5)
        if s.get(x, y)[3]:
            s.put(x, y, MOSS[4] if k % 2 else MOSS[3])
            s.put(x + 1, y, MOSS[3])
    for j in range(8, 18):                                         # the fissure
        s.put(13 + (j % 3 == 0), j, ROCK[1])
    s.outline()


# kind: (draw, w, h, footprint w, h, origin, solid, shadow [dx, dy, rx, ry])
PROPS = {
    "house": (house, 104, 92, 6, 3, [4, 90], True, [100, -8, 8, 10]),
    "storehouse": (storehouse, 72, 92, 4, 3, [4, 90], True, [68, -8, 8, 10]),
    "willow": (willow, 48, 64, 1, 1, [16, 62], True, [12, -2, 16, 6]),
    "lantern": (lantern, 16, 32, 1, 1, [0, 30], True, [10, -2, 6, 3]),
    "barrel": (barrel, 16, 20, 1, 1, [0, 18], True, [10, -2, 6, 3]),
    "crates": (crates, 32, 34, 2, 1, [0, 32], True, [31, -4, 5, 6]),
    "notice": (notice, 32, 32, 2, 1, [0, 30], True, [20, -2, 11, 3]),
    "reeds": (reeds, 16, 20, 1, 1, [0, 18], False, None),
    "boat": (boat, 48, 20, 3, 1, [0, 18], False, None),
    "bamboo": (bamboo, 32, 64, 1, 1, [8, 62], True, [14, -2, 12, 5]),
    "lotus": (lotus, 32, 16, 2, 1, [0, 16], False, None),
    "lantern_red": (lantern_red, 16, 40, 1, 1, [0, 38], True, [10, -2, 6, 3]),
    "incense": (incense, 16, 28, 1, 1, [0, 26], True, [10, -2, 6, 3]),
    "shrub": (shrub, 20, 18, 1, 1, [2, 16], True, [12, -2, 8, 3]),
    # Chapter 2's stretch (the sects and the Reed Marsh; docs/redesign_top_down_plan.md "As built: Phase 4, second part").
    "hall": (hall, 136, 92, 8, 3, [4, 90], True, [132, -8, 8, 10]),
    "pine": (pine, 40, 64, 1, 1, [12, 62], True, [14, -2, 14, 5]),
    "weapon_rack": (weapon_rack, 32, 40, 2, 1, [0, 38], True, [22, -2, 12, 3]),
    "banner_jade": (banner_jade, 16, 60, 1, 1, [0, 58], True, [10, -2, 6, 3]),
    "banner_cloud": (banner_cloud, 16, 60, 1, 1, [0, 58], True, [10, -2, 6, 3]),
    "post": (post, 16, 30, 1, 1, [0, 28], True, [10, -2, 6, 3]),
    "dead_tree": (dead_tree, 40, 56, 1, 1, [12, 54], True, [14, -2, 12, 4]),
    "boulder": (boulder, 24, 22, 1, 1, [4, 20], True, [12, -2, 9, 3]),
    "grey_reeds": (grey_reeds, 16, 20, 1, 1, [0, 18], False, None),
}
# Terrain v2's third part, the foliage and garden kit (tools/art/topdown/foliage.py; art bible "Foliage and decor").
PROPS.update(FL.PROPS)
# Decision 43, the living world: the huts', shop's and halls' furnishings and the stations villagers work at
# (tools/art/topdown/furnish.py; art bible §14.13).
PROPS.update(FU.PROPS)
# R2: the waterfall of Whitewater Gorge (tools/art/topdown/falls.py).
PROPS.update(FA.PROPS)


# Props whose top is a floor you stand on, in levels over their ground (decision 29; TopdownRoom reads `top`).
TOPS = {"house": 2, "storehouse": 2, "crates": 1, "hall": 2}

# Animated props (art bible §7): frames side by side from `rect`, and each frame's time. Plants sway on a slow loop
# (the room view starts each prop at its own phase, so a grove never moves in lockstep); lotus flowers bob on the
# water's 250 ms clock; a banner's tail stirs.
ANIM = {"bamboo": (4, 500), "willow": (4, 600), "lotus": (4, 250), "banner_jade": (4, 450), "banner_cloud": (4, 450),
        "lantern_red": (4, 700)}   # decision 43: the paper lantern swings on the wind
ANIM.update({k: v for k, v in FL.ANIM.items() if k not in FL.STILL_TRUNK})
ANIM.update(FU.ANIM)
ANIM.update(FA.ANIM)
SWAY = (0, 1, 1, 0)
SHEET_W = 512


def shadow_sprite(dx: int, dy: int, rx: float, ry: float) -> tuple[Img, list]:
    """A prop's floor shadow (art bible §3, "Terrain v2" light): a translucent ellipse of the world's one shadow colour
    (blue-violet) centred (dx, dy) from the footprint's south-west corner, denser in its core (two stepped rings, no
    blur). Returns the sprite and its top-left corner from that footprint corner; the room view lays it on the floor the
    prop stands on, never on a body."""
    x0, x1 = int(dx - rx) - 1, int(dx + rx) + 2
    y0, y1 = int(dy - ry) - 1, int(dy + ry) + 2
    s = Img(x1 - x0, y1 - y0)
    for j in range(y0, y1):
        for i in range(x0, x1):
            u, v = (i + 0.5 - dx) / rx, (j + 0.5 - dy) / ry
            d = u * u + v * v
            if d <= 1.0:
                s.put(i - x0, j - y0, alpha(T2.SHADOW, 64 if d > 0.5 else T2.SHADOW_A))
    return s, [x0, y0]


def build() -> tuple[Img, dict]:
    """The prop kit: every prop (its animation frames side by side) and every prop shadow, packed in rows."""
    sprites = []   # (kind, what, img)
    for kind, (draw, w, h, fw, fh, origin, solid, shadow) in PROPS.items():
        n = ANIM.get(kind, (1, 0))[0]
        spr = Img(w * n, h)
        for f in range(n):
            one = Img(w, h)
            draw(one, f) if n > 1 else draw(one)
            spr.paste(one, f * w, 0)
        sprites.append((kind, "prop", spr))
    for kind, entry in PROPS.items():
        if kind in FL.SHADOWS:
            sprites.append((kind, "shadow", FL.shadow_of(kind)[0]))
        elif entry[7]:
            sprites.append((kind, "shadow", shadow_sprite(*entry[7])[0]))
    # A tree's canopy (the overhang the room view lays over its trunk), its frames side by side on the trunk's clock.
    for kind, (draw, w, h, at) in FL.CANOPY.items():
        n = FL.ANIM.get(kind, (1, 0))[0]
        spr = Img(w * n, h)
        for f in range(n):
            one = Img(w, h)
            draw(one, f)
            spr.paste(one, f * w, 0)
        sprites.append((kind, "canopy", spr))
    places, x, y, row_h = [], 0, 0, 0
    for kind, what, spr in sprites:
        if x + spr.w > SHEET_W:
            x, y, row_h = 0, y + row_h, 0
        places.append((kind, what, spr, x, y))
        x, row_h = x + spr.w, max(row_h, spr.h)
    sheet = Img(SHEET_W, y + row_h)
    at: dict = {}
    for kind, what, spr, x, y in places:
        sheet.paste(spr, x, y)
        draw, w, h, fw, fh, origin, solid, shadow = PROPS[kind]
        if what == "shadow":
            at[kind]["shadow"] = shadow
            at[kind]["shadow_rect"] = [x, y, spr.w, spr.h]
            at[kind]["shadow_at"] = FL.shadow_of(kind)[1] if kind in FL.SHADOWS else shadow_sprite(*shadow)[1]
            continue
        if what == "canopy":
            cdraw, cw, ch, cat = FL.CANOPY[kind]
            one = Img(cw, ch)
            cdraw(one, 0)
            n, ms = FL.ANIM.get(kind, (1, 0))
            at[kind]["canopy"] = {"rect": [x, y, cw, ch], "at": cat, "box": FL.fade_box(one), "frames": n, "frame_ms": ms}
            continue
        entry = {"rect": [x, y, w, h], "footprint": [fw, fh], "origin": origin, "solid": solid}
        if kind in ANIM:
            entry["frames"], entry["frame_ms"] = ANIM[kind]
        if kind in TOPS:
            entry["top"] = TOPS[kind]
        if kind in FL.PROPS:
            entry["foliage"] = True
        if kind in FL.LITTER:
            entry["litter"] = FL.LITTER[kind]
        at[kind] = entry
    return sheet, at
