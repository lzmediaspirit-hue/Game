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
  cloud_0..1    flight's cloud of qi under a flying body's feet (28 x 10), its lobes drifting between the frames
  lift_2x2      a lift's deck (a crane's basket, a trial's plank): planks in a frame of beams, a ring at each corner
  boards_0..1   rotten boards over a pit, a cell: whole, then split and sagging under a foot
T2 (the rows T1 left; topdown_mechanics.md):
  seal_gate     a sealed hatch across a flight's foot (32 x 26): a lacquered lattice gate between two posts, two paper seal
                strips crossed over it, each with its red seal
  driftwood     a drifting trunk three cells long (48 x 22): bleached grey wood, its grain and cracks, a branch stub and
                a knot of roots; two frames, bobbing a pixel at the waterline
  plank         floating planks two cells by one (32 x 20): three boards on a cross batten, nail heads; two frames
  drum          a festival drum set flat (32 x 32): its hide skin, the red lacquered barrel banded in gold, brass studs
  lily          a giant lotus leaf on the marsh (32 x 24): veins from its notched heart, its rim curled, drops of water
  bamboo        a bamboo culm bent over into a springboard (32 x 28): rooted at the left, arching to the right, its tip
                pressed to the ground under a tuft of leaves
  lantern       a great hanging lantern whose lid is a deck (32 x 52): an octagonal lid of dark lacquer rimmed in gold, the
                red paper body glowing under it, ribbed, a gold tassel; two frames, the glow breathing
  pit           a spike pit's cell where the boards gave way (16 x 16): the dark of the pit, bronze spikes in rows
  gap           a floor gone under rotten boards (16 x 16): the shadow of the floor below, broken board ends
  hole_water    a plank walk's cell gone into the pool (16 x 16): dark water, a ripple
  ice_0..1      ice glazed over a floor (16 x 16): a pale blue sheen, white streaks, a glint moving across
  wind_0..2     a curl of wind-blown snow and grit (12 x 5)
  ripple_0..1   the ring of water round a swimmer's chest (24 x 8)
"""
from __future__ import annotations

import math

from canvas import Img, h01
from palette import (BAMBOO, BJADE, BRONZER, DARKWOOD, DIRT, FOAM2, GOLDR, HOLLOW, JADE, LANTERN, LEAF, MIST, MOSS, PAD,
                     PAPER, QI, RED, SNOW2, STONE, WATER2, WOOD, WOOD2, alpha)


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


def lift(s: Img) -> None:
    """A lift's deck two cells square (32 x 37): planks laid north-south in a frame of beams, an iron ring at each corner
    for its ropes, the frame's side and its shadow on its south face."""
    for x in range(1, 31):
        for y in range(1, 31):
            plank = (x - 1) // 5
            edge = (x - 1) % 5
            col = WOOD[4] if edge == 0 else WOOD[3] if edge < 4 else WOOD[2]
            if h01(x, y // 6 + plank * 7, 79) < 0.06:
                col = WOOD[1]
            s.put(x, y, col)
    for i in range(0, 32):   # the frame's beams round the deck
        for j in (0, 31):
            s.put(i, j, DARKWOOD[3] if j == 0 else DARKWOOD[2])
            s.put(j, i, DARKWOOD[3] if j == 0 else DARKWOOD[2])
    for x in range(1, 31):
        s.put(x, 1, WOOD[5])
    for cx, cy in ((2, 2), (29, 2), (2, 29), (29, 29)):
        s.rect(cx - 1, cy - 1, 3, 3, STONE[2])
        s.put(cx - 1, cy - 1, STONE[5])
        s.put(cx, cy, (0, 0, 0, 0))
    for y in range(32, 37):
        for x in range(0, 32):
            s.put(x, y, DARKWOOD[2] if y < 35 else DARKWOOD[1])
    s.outline()


def boards(s: Img, f: int) -> None:
    """Rotten boards over a pit, a cell (16 x 20): three warped planks on two sagging joists, nail heads, rot; in the
    second frame (stood on) split across the middle plank and sagging."""
    for k in range(3):
        y0 = 1 + k * 5
        sag = 1 if f and k == 1 else 0
        for x in range(0, 16):
            dip = sag if 4 < x < 12 else 0
            for y in range(y0 + dip, y0 + 4 + dip):
                r = h01(x, y + k * 17, 80)
                col = WOOD[4] if y == y0 + dip else WOOD[3] if r > 0.18 else WOOD[2]
                if r < 0.05:
                    col = MOSS[2]
                s.put(x, y, col)
            s.put(x, y0 + 4 + dip, DARKWOOD[1])
        s.put(2, y0 + 1, STONE[4])
        s.put(13, y0 + 1, STONE[4])
    if f:   # the split
        for y in range(6, 11):
            s.put(7 + (y % 2), y, DARKWOOD[0])
    for y in range(16, 20):   # the joists' ends and the dark of the pit under them
        s.put(3, y, DARKWOOD[2])
        s.put(12, y, DARKWOOD[2])
    s.outline()


def cloud(s: Img, f: int) -> None:
    """Flight's cloud of qi under the feet (28 x 10): a small heap of mist, lit on its upper left, its lobes drifting a
    pixel between the frames, a jade breath at its heart."""
    lobes = ((7, 5, 6.0, 3.6), (14, 4, 7.0, 4.2), (21, 5, 6.0, 3.6))
    for y in range(10):
        for x in range(28):
            inside = False
            lit = False
            for i, (cx, cy, rx, ry) in enumerate(lobes):
                dx = (x + 0.5 - cx - (1 if f and i != 1 else 0) * (1 if i == 2 else -1)) / rx
                dy = (y + 0.5 - cy) / ry
                d = dx * dx + dy * dy
                if d <= 1.0:
                    inside = True
                    lit = lit or (d > 0.45 and dx + dy < -0.4)
            if inside:
                core = abs(x + 0.5 - 14) < 5 and 4 <= y <= 6
                s.put(x, y, alpha(FOAM2, 235) if lit else alpha(QI, 150) if core else alpha(MIST, 215))
    s.outline()


# ------------------------------------------------------------------ T2: the rows T1 left (topdown_mechanics.md)
def seal_gate(s: Img) -> None:
    """A sealed hatch across a flight's foot (32 x 26): a lattice gate of dark lacquered slats between two posts, its top
    and bottom rails, and two paper seal strips crossed over it, a red seal stamped where they cross."""
    # The lattice: thin slats on a grid between the rails, the gaps dark.
    for y in range(5, 23):
        for x in range(3, 29):
            on = (x - 3) % 4 == 0 or (y - 5) % 4 == 0
            s.put(x, y, DARKWOOD[3] if on and (x + y) % 2 else DARKWOOD[2] if on else alpha(DARKWOOD[0], 200))
    for x in range(0, 32):   # the rails, lit on top
        s.put(x, 4, RED[4] if 2 < x < 29 else DARKWOOD[4])
        s.put(x, 5, RED[2])
        s.put(x, 22, RED[3])
        s.put(x, 23, RED[1])
    for x0 in (0, 29):       # the posts, capped
        for y in range(1, 26):
            s.put(x0, y, DARKWOOD[4] if x0 == 0 else DARKWOOD[3])
            s.put(x0 + 1, y, DARKWOOD[3])
            s.put(x0 + 2, y, DARKWOOD[2] if x0 == 0 else DARKWOOD[1])
        s.rect(x0 - (1 if x0 == 0 else 0), 0, 4, 2, GOLDR[2])
        s.put(x0, 0, GOLDR[3])
    # The two seal strips, crossed corner to corner: white paper, a shadow under each.
    for k in range(0, 24):
        y = 3 + k
        for x, dx in ((3 + k, 1), (28 - k, -1)):
            if 2 <= x <= 29 and y < 25:
                s.put(x, y, PAPER)
                s.put(x + dx, y, alpha(PAPER, 230))
                s.put(x, y + 1, DARKWOOD[1])
    # The seal where they cross: a red square with a pale glyph.
    s.rect(13, 11, 6, 6, RED[3])
    s.hline(13, 11, 6, RED[4])
    s.vline(13, 11, 6, RED[4])
    s.hline(14, 13, 4, PAPER)
    s.vline(15, 12, 4, PAPER)
    s.put(17, 15, PAPER)
    s.outline()


def driftwood(s: Img, f: int = 0) -> None:
    """A drifting trunk three cells long (48 x 22): bleached grey wood with its grain, a crack and a knot, a broken branch
    stub on its back and a knot of roots at its west end; the waterline under it, the trunk a pixel lower in frame 1."""
    bob = 1 if f else 0
    for x in range(4, 46):
        taper = 1 if x > 40 else 0
        for y in range(4 + taper + bob, 15 - taper + bob):
            row = y - 4 - bob
            col = HOLLOW[5] if row < 2 else HOLLOW[4] if row < 5 else HOLLOW[3] if row < 8 else HOLLOW[2]
            if h01(x, y // 2, 81) < 0.12:
                col = HOLLOW[2]
            s.put(x, y, col)
        if h01(x, 1, 82) < 0.35:   # the grain along it
            s.put(x, 7 + bob + int(h01(x, 2, 82) * 3), HOLLOW[3])
    for x in range(14, 24):        # a crack
        s.put(x, 9 + bob + (x % 3 == 0), HOLLOW[1])
    s.ellipse(31, 8 + bob, 2.2, 1.6, HOLLOW[2])   # a knot
    s.put(31, 8 + bob, HOLLOW[1])
    for y in range(0, 6):          # the branch stub, sticking up off its back
        s.put(26 + y // 3, 4 - y + bob + 2, HOLLOW[5] if y < 3 else HOLLOW[4])
        s.put(27 + y // 3, 4 - y + bob + 2, HOLLOW[3])
    for k, (dx, dy) in enumerate(((-3, -2), (-4, 1), (-3, 4), (-2, 6), (-4, 7))):   # roots at the west end
        for t in range(4):
            s.put(4 + dx + t, 9 + dy + bob, HOLLOW[3] if t else HOLLOW[2])
    for x in range(3, 46):         # the waterline: wet wood, then foam
        s.put(x, 15 + bob, HOLLOW[1])
        r = h01(x, f, 83)
        s.put(x, 16 + bob, FOAM2 if r < 0.4 else WATER2[6])
        if r < 0.2:
            s.put(x, 17 + bob, alpha(FOAM2, 150))
    s.outline()


def plank(s: Img, f: int = 0) -> None:
    """Floating planks two cells by one (32 x 20): three boards side by side on a cross batten, nail heads, wet ends; the
    waterline under them, a pixel lower in frame 1."""
    bob = 1 if f else 0
    for k in range(3):
        y0 = 1 + k * 5 + bob
        x0, x1 = 1 + int(h01(k, 1, 84) * 2), 31 - int(h01(k, 2, 84) * 2)
        for y in range(y0, y0 + 4):
            s.hline(x0, y, x1 - x0, WOOD2[5] if y == y0 else WOOD2[4] if y == y0 + 1 else WOOD2[3])
        s.hline(x0, y0 + 4, x1 - x0, WOOD2[1])
        for x in (x0, x1 - 1):
            s.vline(x, y0, 4, WOOD2[2])
    for y in range(1 + bob, 15 + bob):   # the batten across them
        s.put(15, y, WOOD2[2])
        s.put(16, y, WOOD2[3])
    for k in range(3):
        s.put(15, 2 + k * 5 + bob, STONE[5])
        s.put(16, 3 + k * 5 + bob, STONE[4])
    for x in range(0, 32):
        r = h01(x, f, 85)
        s.put(x, 16 + bob, FOAM2 if r < 0.4 else WATER2[6])
        if r < 0.18:
            s.put(x, 17 + bob, alpha(FOAM2, 150))
    s.outline()


def drum(s: Img) -> None:
    """A festival drum set flat on the ground (32 x 32): its pale hide skin, lit upper left, the red lacquered barrel's
    south side banded in gold under it, a ring of brass studs round the skin's rim, and a painted taiji at its heart."""
    cx, cy, rx, ry = 16.0, 12.0, 14.5, 10.5
    for y in range(12, 31):   # the barrel's side, south of the skin
        for x in range(2, 30):
            dx = (x + 0.5 - cx) / rx
            if dx * dx > 1.0:
                continue
            bottom = cy + ry * (1.0 - dx * dx) ** 0.5 + 8
            if y > bottom:
                continue
            col = RED[3] if dx < -0.3 else RED[2] if dx < 0.4 else RED[1]
            if abs(y - (bottom - 2)) < 1 or abs(y - (bottom - 6)) < 1:
                col = GOLDR[2] if dx < 0.2 else GOLDR[1]
            s.put(x, y, col)
    s.ellipse(cx, cy, rx, ry, PAPER, shade=(c_hide_lit, c_hide_dark))
    s.ellipse(cx, cy, rx - 2.5, ry - 2.0, c_hide)
    for k in range(18):       # the brass studs round the rim
        a = 2 * 3.14159 * k / 18
        x = int(round(cx + (rx - 1.2) * math.cos(a) - 0.5))
        y = int(round(cy + (ry - 1.0) * math.sin(a) - 0.5))
        s.put(x, y, GOLDR[3] if math.cos(a) + math.sin(a) < 0 else GOLDR[1])
    # The taiji painted on the skin.
    s.ellipse(cx, cy, 4.5, 3.5, RED[3])
    s.ellipse(cx + 1.5, cy - 1, 1.6, 1.2, PAPER)
    s.ellipse(cx - 1.5, cy + 1, 1.6, 1.2, RED[1])
    s.outline()


c_hide = (228, 214, 180, 255)
c_hide_lit = (246, 236, 208, 255)
c_hide_dark = (196, 176, 138, 255)


def lily(s: Img) -> None:
    """A giant lotus leaf lying on the marsh (32 x 24): its veins running out from the notched heart, the rim curled up
    and lit, a bead of water or two, its shadow on the wet ground."""
    cx, cy, rx, ry = 16.0, 11.0, 15.0, 10.0
    s.ellipse(cx + 1, cy + 2, rx, ry, alpha(WATER2[1], 140))   # the wet ground's shadow under it
    for y in range(24):
        for x in range(32):
            dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            d = dx * dx + dy * dy
            if d > 1.0:
                continue
            ang = math.atan2(dy, dx)
            if abs(ang - 1.2) < 0.18 and d > 0.05:   # the notch to the heart
                continue
            col = PAD[3] if d < 0.6 else PAD[4] if dx + dy < 0 else PAD[2]
            if d > 0.82:
                col = PAD[5] if dx + dy < 0 else PAD[1]
            spoke = (ang * 9.0 / math.pi) % 2.0
            if (spoke < 0.18 or spoke > 1.82) and d > 0.04:
                col = PAD[5] if dx + dy < 0 else PAD[4]
            s.put(x, y, col)
    s.put(int(cx), int(cy), PAD[1])
    for bx, by in ((9, 7), (21, 13)):   # water beads, lit
        s.put(bx, by, WATER2[7])
        s.put(bx + 1, by, FOAM2)
        s.put(bx, by + 1, WATER2[5])
    s.outline()


def bamboo(s: Img) -> None:
    """A bamboo culm bent over into a springboard (32 x 28): rooted in a clump at the left, it rises and arches to the right,
    its nodes banded, its tip pressed to the ground at the right under a tuft of leaves."""
    pts = []
    for k in range(60):
        t = k / 59.0
        x = 4 + 24 * t
        y = 24 - 20 * math.sin(math.pi * t) * (1.0 - 0.35 * t)
        pts.append((x, y))
    for i, (x, y) in enumerate(pts):
        node = i % 12 == 0 and 0 < i < 59
        for w in range(3):
            col = BAMBOO[4] if w == 0 else BAMBOO[3] if w == 1 else BAMBOO[2]
            if node:
                col = BAMBOO[5] if w == 0 else BAMBOO[1]
            s.put(int(x), int(y) + w, col)
    for k in range(9):   # the root clump: short shoots and a sheath
        x = 1 + k % 5
        s.put(x, 25 + k // 5, BAMBOO[2] if k % 2 else BAMBOO[1])
    s.rect(2, 22, 4, 4, BAMBOO[2])
    s.put(2, 22, BAMBOO[4])
    for k in range(10):  # the leaf tuft over the tip
        lx = 21 + int(h01(k, 1, 86) * 10)
        ly = 17 + int(h01(k, 2, 86) * 8)
        for dx, dy, col in ((0, 0, LEAF[5]), (1, 0, LEAF[4]), (2, 1, LEAF[3]), (3, 1, LEAF[2])):
            s.put(lx + dx - 2, ly + dy, col)
    s.outline()


def lantern(s: Img, f: int = 0) -> None:
    """A great hanging lantern whose lid is a deck a body stands on (32 x 52): the octagonal lid of dark lacquer seen from
    above, rimmed in gold, its iron ring at the heart where the chain holds it; under the lid's south rim the red paper
    body glowing, its ribs, and a gold tassel hanging below. Frame 1 breathes the glow brighter."""
    # The paper body under the lid (south of it on the screen), glowing.
    for y in range(28, 47):
        k = (y - 28) / 18.0
        half = 12.0 * math.sin(math.pi * (0.15 + 0.85 * k)) + 1.0
        for x in range(32):
            dx = (x + 0.5 - 16.0) / half
            if abs(dx) > 1.0:
                continue
            glow = 1.0 - abs(dx)
            col = LANTERN[3 + (1 if f and glow > 0.55 else 0)] if glow > 0.55 else LANTERN[2] if glow > 0.2 else LANTERN[1]
            if (y - 28) % 5 == 0:
                col = LANTERN[0]   # a rib
            s.put(x, y, col)
    s.rect(14, 46, 4, 2, GOLDR[2])   # the bottom cap and the tassel
    for y in range(48, 52):
        s.put(15, y, GOLDR[3] if y % 2 else GOLDR[1])
        s.put(16, y, GOLDR[2])
    # The lid: an octagon of dark lacquer over the deck's two cells, its rim in gold, lit upper left.
    for y in range(2, 30):
        for x in range(1, 31):
            dx, dy = abs(x + 0.5 - 16.0), abs(y + 0.5 - 16.0)
            if dx > 14.5 or dy > 13.5 or dx + dy > 21.0:
                continue
            rim = dx > 12.5 or dy > 11.5 or dx + dy > 19.0
            lit = (x + y) < 30
            col = (GOLDR[3] if lit else GOLDR[1]) if rim else (RED[1] if lit else RED[0])
            if not rim and (x + 2 * y) % 9 == 0:
                col = RED[2]
            s.put(x, y, col)
    for y in range(30, 32):   # the lid's south edge, its thickness
        for x in range(6, 26):
            s.put(x, y, GOLDR[1] if y == 30 else DARKWOOD[1])
    s.ellipse(16, 16, 2.6, 2.2, STONE[2])   # the iron ring at its heart
    s.put(15, 15, STONE[5])
    s.put(16, 16, RED[0])
    s.outline()


def pit(s: Img) -> None:
    """A spike pit's cell where the boards gave way (16 x 16): the pit's dark, bronze spikes standing in rows, their tips
    lit."""
    s.rect(0, 0, 16, 16, DARKWOOD[0])
    for y in range(0, 4):
        s.hline(0, y, 16, (24, 16, 12, 255) if y < 2 else DARKWOOD[1])
    for k, (x, y) in enumerate(((2, 6), (7, 5), (12, 6), (4, 11), (9, 10), (14, 11))):
        s.put(x, y, BRONZER[5])
        s.put(x, y + 1, BRONZER[4])
        s.put(x - 1, y + 2, BRONZER[3])
        s.put(x, y + 2, BRONZER[4])
        s.put(x + 1, y + 2, BRONZER[2])
        s.hline(x - 1, y + 3, 3, BRONZER[1])


def gap(s: Img) -> None:
    """A floor gone under rotten boards (16 x 16): the shadow of the floor a level below and broken board ends along the
    north edge."""
    s.rect(0, 0, 16, 16, alpha(DARKWOOD[0], 230))
    for x in range(16):
        n = int(h01(x, 1, 87) * 4)
        for y in range(n):
            s.put(x, y, WOOD[2] if y == n - 1 else WOOD[3])
    for x in range(1, 15, 3):
        s.put(x, 12, alpha(DARKWOOD[2], 200))


def hole_water(s: Img) -> None:
    """A plank walk's cell gone into the pool (16 x 16): dark water, a ripple across it, broken plank ends at its north
    edge."""
    s.rect(0, 0, 16, 16, WATER2[2])
    for x in range(16):
        s.put(x, 7 + (x // 4) % 2, WATER2[4] if x % 5 else WATER2[6])
        if h01(x, 3, 88) < 0.5:
            s.put(x, 0, WOOD2[2])
            s.put(x, 1, WOOD2[1])


def ice(s: Img, f: int = 0) -> None:
    """Ice glazed over a floor (16 x 16): a pale blue sheen, streaks of white along the grain of the cold, and a glint
    that moves along a streak between the frames."""
    for y in range(16):
        for x in range(16):
            s.put(x, y, alpha(SNOW2[5], 70))
    for k in range(3):
        y0 = 2 + k * 5
        for x in range(1 + k, 14):
            if h01(x, k, 89) < 0.7:
                s.put(x, y0 + (x // 5) % 2, alpha(SNOW2[6], 150))
    gx = 4 + f * 6
    s.put(gx, 3, alpha(SNOW2[6], 240))
    s.put(gx + 1, 3, alpha((255, 255, 255, 255), 240))
    s.put(gx, 2, alpha(SNOW2[6], 180))


def wind(s: Img, f: int = 0) -> None:
    """A curl of wind-blown snow and grit (12 x 5), drawn trailing to the east (the view mirrors it for a wind the other
    way): a line of motes that curls up at its head; its length grows between the frames."""
    n = 6 + f * 2
    for k in range(n):
        x = 11 - k
        y = 3 if k > 2 else 3 - (2 - k)
        if x >= 0:
            s.put(x, y, alpha(SNOW2[6], 230 - k * 18))


def ripple(s: Img, f: int = 0) -> None:
    """The ring of water round a swimmer's chest (24 x 8): a broken ellipse of foam, wider in frame 1."""
    rx, ry = 10.0 + f, 2.6 + f * 0.4
    for k in range(40):
        a = 2 * math.pi * k / 40
        x, y = 12 + rx * math.cos(a), 4 + ry * math.sin(a)
        if h01(k, f, 90) < 0.75:
            s.put(int(x), int(y), alpha(FOAM2, 220 if math.sin(a) > 0 else 150))


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
    "cloud": (28, 10, 2, cloud),
    "lift_2x2": (32, 37, 0, lift),
    "boards": (16, 20, 2, boards),
    # T2
    "seal_gate": (32, 26, 0, seal_gate),
    "driftwood": (48, 22, 2, driftwood),
    "plank": (32, 20, 2, plank),
    "drum": (32, 32, 0, drum),
    "lily": (32, 24, 0, lily),
    "bamboo": (32, 28, 0, bamboo),
    "lantern": (32, 52, 2, lantern),
    "pit": (16, 16, 0, pit),
    "gap": (16, 16, 0, gap),
    "hole_water": (16, 16, 0, hole_water),
    "ice": (16, 16, 2, ice),
    "wind": (12, 5, 3, wind),
    "ripple": (24, 8, 2, ripple),
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
