"""Terrain v2, third part (decision 40; docs/redesign/art_bible.md "Foliage and decor"): the small ground cover the
room view scatters over a room's meadows, beds, marsh and rock (TopdownFoliage): tall grass tufts, ferns, wild flowers,
pebbles and mossy stones, mushrooms and lingzhi, reeds and cattail stubs, and the litter under trees (leaves, maple
leaves, plum and peach petals, pine needles, bamboo leaves).

Each piece is a small sprite standing on its foot (the bottom row's middle), up to 16 x 16, lit from the north-west,
with a small `SHADOW` to its south-east like a decal's, and no outline: it is ground cover, not a prop. A piece that
stirs (grass, flowers, reeds) names the row above which it sways; the room view shifts that part a pixel east and back
on a slow clock, each piece at its own phase.

The rules say where they grow: per paint mark (its biome), a share of cells that take one piece, the sets it is picked
from (weighted), low-frequency patches of dense tall grass, the reeds along a shore, and the litter round each tree.
The room view keeps paths, doorways, ways out, the spawn and every person's and thing's spot clear.
"""
from __future__ import annotations

import math

from canvas import Img, h01
from palette import DARKWOOD, FLOWER, GOLDR, GRASS2, LEAFFALL, MOSS2, PETAL, REED, ROCK2, SHADOW, alpha, c

import foliage as FL

G = GRASS2
M = MOSS2


def _shadow(s: Img, x: int, y: int, a: int = 80) -> None:
    if 0 <= x < s.w and 0 <= y < s.h and s.get(x, y)[3] == 0:
        s.put(x, y, alpha(SHADOW, a))


def _ground_shadow(s: Img) -> None:
    """The piece's small shadow on the ground to the south-east of its lowest pixels (as a decal's, 0.16-0.39)."""
    solid = {(x, y) for y in range(s.h) for x in range(s.w) if s.get(x, y)[3] == 255}
    for (x, y) in sorted(solid):
        if y >= s.h - 3:
            for dx, dy, a in ((1, 1, 96), (1, 0, 60), (2, 1, 56)):
                if (x + dx, y + dy) not in solid:
                    _shadow(s, x + dx, y + dy, a)


# ============================================================================================================ grass
def tuft(seed: int, w: int = 14, h: int = 16, n: int = 11, ramp=G, heads: bool = False) -> Img:
    """A clump of tall grass: blades fanning up from a dark heart, deep in their own shade at the foot, brighter as
    they rise and lit at their tips (bright on the west, a step darker leaning east), a small shadow at the foot.
    `heads`: some blades carry pale seed heads. w x h, the foot at the bottom row's middle."""
    s = Img(w, h)
    rx = (w - 1) / 2
    for j in range(3):                                             # the dark heart the blades rise from
        half = rx * (0.55 + 0.15 * j)
        for i in range(w):
            if abs(i - rx) <= half:
                s.put(i, h - 1 - j, ramp[1] if j == 0 else ramp[2])
    order = sorted(range(n), key=lambda b: h01(b, 9, seed))
    for b in order:
        f = b / max(1, n - 1) - 0.5
        lean = f * (w * 0.8) + (h01(b, 1, seed) - 0.5) * 2
        ln = int(h * (0.5 + 0.5 * h01(b, 2, seed)) * (1.0 - abs(f) * 0.5))
        curve = (h01(b, 3, seed) - 0.5) * 3 + f * 2
        for j in range(ln):
            t = j / max(1, ln - 1)
            x = round(rx + lean * t + curve * t * t)
            y = h - 2 - j
            k = 2 if t < 0.25 else 3 if t < 0.55 else 4 if t < 0.85 else 5
            if f > 0.15 and t > 0.3:
                k -= 1                                             # blades leaning east are in their own shade
            if t >= 0.85 and f < -0.1:
                k = 6 if h01(b, 4, seed) > 0.5 else 5
            s.put(x, y, ramp[k])
        if heads and b % 3 == 0 and ln > h * 0.6:
            tx, ty = round(rx + lean + curve), h - 2 - ln
            s.put(tx, ty, c("E8D890"))
            s.put(tx, ty - 1, c("F4E8B0"))
            s.put(tx + 1, ty, c("C8B870"))
    _ground_shadow(s)
    for i in range(w):                                             # its shadow on the ground to the south-east
        if s.get(i, h - 1)[3] == 255 and i + 2 < w:
            _shadow(s, i + 2, h - 1, 80)
    return s


def shrublet(seed: int) -> Img:
    """A low ground shrub a body walks through: a small mound of leaf puffs, lit north-west, dark at its foot."""
    s = Img(16, 11)
    FL.puff_mass(s, [(8, 6, 7, 4.5), (4, 7, 3.5, 3), (12, 7, 3.5, 3)], FL.LEAF, 300 + seed, 2.8, 2.8, lo=1, hi=5)
    _ground_shadow(s)
    return s


def tuft_low(seed: int) -> Img:
    """A low crowded tuft: many short blades, a dark heart."""
    return tuft(seed, 14, 9, 10)


def fern(seed: int) -> Img:
    """A small fern: fronds arching out from a dark heart, pinnae lit on their upper side."""
    s = Img(14, 10)
    for k in range(5):
        ang = -math.pi + (k + 0.5) / 5 * math.pi + (h01(k, 1, seed) - 0.5) * 0.3
        ln = 5 + int(h01(k, 2, seed) * 3)
        for q in range(ln):
            t = q / ln
            x = round(7 + math.cos(ang) * q * 1.1)
            y = round(9 + math.sin(ang) * q * 0.9 + t * t * 3)
            s.put(x, y, M[3])
            if q > 1 and q % 2 == 0:
                s.put(x, y - 1, M[5] if math.cos(ang) < 0.2 else M[4])
                s.put(x + (1 if math.cos(ang) > 0 else -1), y, M[2])
    s.put(7, 9, M[1])
    _ground_shadow(s)
    return s


# ============================================================================================================ flowers
def flower(col: tuple, seed: int, h: int = 13) -> Img:
    """A wild flower on a thin stem with leaves: a five-pixel bloom and its petals' tips, lit on the north-west and
    shaded south-east, its heart gold; a bud beside it."""
    s = Img(9, h)
    x = 4
    top = 3 + int(h01(1, 1, seed) * 2)
    bend = 1 if h01(2, 2, seed) > 0.5 else 0
    for y in range(top + 1, h):
        s.put(x + (bend if y < top + 4 else 0), y, G[3] if y < h - 4 else G[2])
    for dx, dy, k in ((-1, -4, 4), (-2, -5, 5), (1, -3, 3), (2, -4, 3), (-1, -2, 3)):
        s.put(x + dx, h + dy, G[k])
    dark = mixc(col, SHADOW, 0.45)
    lit = mixc(col, FL.SUN, 0.4)
    bx = x + bend
    for dx, dy, cc in ((0, -2, lit), (-1, -1, lit), (1, -1, col), (-2, 0, col), (2, 0, dark), (-1, 1, col), (1, 1, dark),
                       (0, 2, dark), (0, -1, col), (-1, 0, col), (1, 0, col), (0, 1, dark)):
        s.put(bx + dx, top + dy, cc)
    s.put(bx, top, GOLDR[2] if col != FLOWER[1] else FLOWER[4])
    s.put(x - 2, top + 4, mixc(col, SHADOW, 0.2))                  # a bud
    s.put(x - 2, top + 5, G[3])
    _ground_shadow(s)
    return s


def mixc(a: tuple, b: tuple, k: float) -> tuple:
    return tuple(round(a[i] + (b[i] - a[i]) * k) for i in range(3)) + (255,)


def flower_cluster(cols: list, seed: int) -> Img:
    """Three or four wild flowers of the meadow grown together among a few blades."""
    s = Img(16, 15)
    base = tuft(seed + 40, 16, 8, 7)
    s.paste(base, 0, 7)
    for k, col in enumerate(cols):
        f = flower(col, seed + k, 11 + (k % 2) * 3)
        s.paste(f, k * 4 + int(h01(k, 5, seed) * 2) - 1, 15 - f.h)
    return s


# ============================================================================================================ stones, mushrooms
def pebbles(seed: int, n: int = 3, big: bool = False) -> Img:
    """Pebbles or a stone: lit on the north-west, dark on the south-east, each with its shadow."""
    s = Img(12, 8)
    for k in range(n):
        w = (6 if big else 3) + int(h01(k, 1, seed) * (3 if big else 2))
        h = max(2, w - 1 - int(h01(k, 2, seed) * 2))
        x = 1 + int(h01(k, 3, seed) * (10 - w))
        y = 7 - h - int(h01(k, 4, seed) * (6 - h))
        b = 3 + int(h01(k, 5, seed) * 2)
        for j in range(h):
            for i in range(w):
                if i in (0, w - 1) and j in (0, h - 1) and w > 2:
                    continue
                col = ROCK2[b]
                if i == 0 or j == 0:
                    col = ROCK2[min(6, b + 1)]
                if i == w - 1 or j == h - 1:
                    col = ROCK2[b - 1]
                s.put(x + i, y + j, col)
        if big:
            s.put(x + 1, y, M[4])
            s.put(x + 2, y, M[5])
            s.put(x + 1, y + 1, M[3])
    _ground_shadow(s)
    return s


def mushrooms(seed: int, cap=None, n: int = 3) -> Img:
    """A little ring of mushrooms: pale stalks, caps lit on the north-west with a dark gill line under them."""
    cap = cap or [c("5A3A2A"), c("8A5A38"), c("B8845A"), c("DDB080")]
    s = Img(12, 8)
    for k in range(n):
        x = 2 + int(h01(k, 1, seed) * 8)
        y = 7 - int(h01(k, 2, seed) * 2)
        s.put(x, y, c("E8DCC0"))
        s.put(x, y - 1, c("D0C4A8"))
        for dx, k2 in ((-2, 1), (-1, 2), (0, 2), (1, 1), (2, 0)):
            s.put(x + dx, y - 2, cap[k2])
        for dx, k2 in ((-1, 3), (0, 3), (1, 2)):
            s.put(x + dx, y - 3, cap[k2])
        s.put(x - 1, y - 3, cap[3])
    _ground_shadow(s)
    return s


def lingzhi(seed: int) -> Img:
    """Lingzhi, the immortals' mushroom: two glossy red-brown fans on short stalks, their rims pale gold."""
    s = Img(12, 9)
    for k, (x, y, r) in enumerate(((4, 5, 3.2), (8, 6, 2.6))):
        for j in range(-2, 2):
            for i in range(-4, 5):
                if (i / r) ** 2 + (j / (r * 0.55)) ** 2 <= 1.0:
                    col = c("7A2A1A") if j > -1 else c("A8402A")
                    if (i / r) ** 2 + (j / (r * 0.55)) ** 2 > 0.6:
                        col = c("E8B860") if j <= -1 and i < 1 else c("5A1A12")
                    s.put(x + i, y + j, col)
        s.put(x - 1, y - 1, c("F0D0A0"))
        s.put(x, y + 2, c("5A1A12"))
        s.put(x, y + 3, c("7A2A1A"))
    _ground_shadow(s)
    return s


# ============================================================================================================ marsh
def reed_small(seed: int) -> Img:
    """A few young reeds: thin stems, lit tips, a seed head on one."""
    s = Img(10, 14)
    for k in range(4):
        x = 2 + k * 2 + int(h01(k, 1, seed) * 2)
        top = 1 + int(h01(k, 2, seed) * 6)
        for y in range(top, 14):
            s.put(x + (1 if y < top + 3 and k % 2 else 0), y, REED[4] if y < top + 2 else REED[3] if y < 10 else REED[2])
        if k == 1:
            s.put(x + 1, top - 1, DARKWOOD[3])
            s.put(x + 1, top, DARKWOOD[4])
    _ground_shadow(s)
    return s


def cattail_stub(seed: int) -> Img:
    """A cattail's brown velvet head on its stem, and the blades round its foot."""
    s = Img(8, 14)
    s.rect(3, 2, 2, 5, DARKWOOD[3])
    s.vline(3, 2, 5, DARKWOOD[4])
    s.put(3, 1, REED[4])
    for y in range(7, 14):
        s.put(4, y, REED[3])
    for x, top in ((1, 8), (6, 7), (2, 10)):
        for y in range(top, 14):
            s.put(x, y, G[3] if y < 11 else G[2])
        s.put(x, top, G[5])
    _ground_shadow(s)
    return s


def iris(seed: int) -> Img:
    """A blue water iris among sword leaves."""
    s = Img(8, 13)
    for x, top in ((2, 4), (5, 3), (3, 6)):
        for y in range(top, 13):
            s.put(x, y, G[4] if y < top + 2 else G[3])
    blue = FLOWER[3]
    for dx, dy, col in ((0, 0, blue), (-1, 1, blue), (1, 1, mixc(blue, SHADOW, 0.4)), (0, 2, mixc(blue, SHADOW, 0.3)),
                        (0, -1, mixc(blue, FL.SUN, 0.4))):
        s.put(4 + dx, 2 + dy, col)
    s.put(4, 2, GOLDR[3])
    _ground_shadow(s)
    return s


# ============================================================================================================ litter
def litter(cols: list, seed: int, n: int = 4, shape: str = "leaf") -> Img:
    """What falls under a tree: small leaves lying at an angle (lit edge up), petals, needles; flat, with a hint of
    shadow."""
    s = Img(14, 8)
    for k in range(n):
        x, y = 1 + int(h01(k, 1, seed) * 11), 1 + int(h01(k, 2, seed) * 5)
        col = cols[int(h01(k, 3, seed) * (len(cols) - 1))]
        lit = cols[min(len(cols) - 1, int(h01(k, 3, seed) * (len(cols) - 1)) + 1)]
        if shape == "petal":
            s.put(x, y, lit)
            if h01(k, 4, seed) < 0.5:
                s.put(x + 1, y, col)
        elif shape == "needle":
            for q in range(3):
                s.put(x + q, y + (q // 2), col)
            if k == 0:
                s.rect(x + 4, y, 2, 3, DARKWOOD[3])                  # a cone
                s.put(x + 4, y, DARKWOOD[4])
        elif shape == "star":
            for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
                s.put(x + dx, y + dy, col if (dx, dy) != (-1, 0) and (dx, dy) != (0, -1) else lit)
        elif shape == "long":
            for q in range(4):
                s.put(x + q, y + (1 if q > 1 else 0), lit if q == 0 else col)
        else:
            horiz = h01(k, 4, seed) < 0.5
            pts = [(0, 0), (1, 0), (2, 1)] if horiz else [(0, 0), (1, 1), (1, 2)]
            for m, (dx, dy) in enumerate(pts):
                s.put(x + dx, y + dy, lit if m == 0 else col)
    for y in range(s.h):
        for x in range(s.w):
            if s.get(x, y)[3] == 255 and s.get(x + 1, y + 1)[3] == 0:
                _shadow(s, x + 1, y + 1, 56)
    return s


# ============================================================================================================ the kit
LEAF_LITTER = [c("6B5A1E"), c("8A7A2A"), LEAFFALL[1], LEAFFALL[2], c("5A7A32")]
MAPLE_LITTER = [FL.MAPLE[2], FL.MAPLE[3], FL.MAPLE[4], FL.MAPLE[5]]
PLUM_LITTER = [PETAL[1], PETAL[2], c("FFF6F8")]
PEACH_LITTER = [FL.PEACH[3], FL.PEACH[4], FL.PEACH[5]]
PINE_LITTER = [c("6A4A2A"), c("8A6232"), c("A87A40")]
BAMBOO_LITTER = [c("8A8A3A"), c("A8A24A"), c("C4BC62")]


def sprites() -> dict:
    """Every piece, {name: (Img, sway row or 0)}, in a fixed order."""
    out = {}
    for k in range(5):
        out["tuft_%d" % k] = (tuft(10 + k, 14 if k % 2 else 12, 14 + (k % 3), 9 + k % 3, heads=k == 4), 8)
    for k in range(2):
        out["shrublet_%d" % k] = (shrublet(20 + k), 0)
    for k in range(3):
        out["tuft_low_%d" % k] = (tuft_low(30 + k), 0)
    for k in range(2):
        out["fern_%d" % k] = (fern(40 + k), 0)
    names = ("white", "gold", "pink", "blue", "coral")
    for k, n in enumerate(names):
        out["flower_" + n] = (flower(FLOWER[k], 50 + k), 5)
    for k, cols in enumerate(([FLOWER[0], FLOWER[1], FLOWER[0]], [FLOWER[2], FLOWER[0], FLOWER[3]], [FLOWER[4], FLOWER[1]],
                              [FLOWER[3], FLOWER[3], FLOWER[0]])):
        out["flowers_%d" % k] = (flower_cluster(cols, 60 + k * 7), 6)
    for k in range(3):
        out["pebbles_%d" % k] = (pebbles(80 + k, 3 - k % 2), 0)
    for k in range(2):
        out["stone_%d" % k] = (pebbles(90 + k, 1, True), 0)
    out["mushrooms_0"] = (mushrooms(100), 0)
    out["mushrooms_1"] = (mushrooms(101, [c("6A2A1A"), c("A8402A"), c("D86A4A"), c("F0E0D0")], 2), 0)
    out["lingzhi"] = (lingzhi(102), 0)
    for k in range(2):
        out["reeds_%d" % k] = (reed_small(110 + k), 8)
    out["cattail"] = (cattail_stub(120), 7)
    out["iris"] = (iris(121), 6)
    out["moss_0"] = (fern(130), 0)
    for k, (name, cols, shape) in enumerate((("leaves", LEAF_LITTER, "leaf"), ("maple", MAPLE_LITTER, "star"),
                                             ("plum", PLUM_LITTER, "petal"), ("peach", PEACH_LITTER, "petal"),
                                             ("pine", PINE_LITTER, "needle"), ("bamboo", BAMBOO_LITTER, "long"))):
        for q in range(2):
            out["litter_%s_%d" % (name, q)] = (litter(cols, 140 + k * 10 + q, 4 + q * 2 if shape != "petal" else 6 + q * 3, shape), 0)
    return out


# The sets a biome picks from, {set: [names]}.
SETS = {
    "grass_tall": ["tuft_0", "tuft_1", "tuft_2", "tuft_3", "tuft_4"],
    "shrublets": ["shrublet_0", "shrublet_1"],
    "grass_low": ["tuft_low_0", "tuft_low_1", "tuft_low_2"],
    "ferns": ["fern_0", "fern_1"],
    "flowers": ["flower_white", "flower_gold", "flower_pink", "flower_blue", "flower_coral", "flowers_0", "flowers_1",
                "flowers_2", "flowers_3"],
    "stones": ["pebbles_0", "pebbles_1", "pebbles_2", "stone_0", "stone_1"],
    "mushrooms": ["mushrooms_0", "mushrooms_1", "lingzhi"],
    "reeds": ["reeds_0", "reeds_1", "cattail", "iris"],
    "moss": ["moss_0", "fern_1", "stone_0", "stone_1"],
    "litter_leaves": ["litter_leaves_0", "litter_leaves_1"],
    "litter_maple": ["litter_maple_0", "litter_maple_1"],
    "litter_plum": ["litter_plum_0", "litter_plum_1"],
    "litter_peach": ["litter_peach_0", "litter_peach_1"],
    "litter_pine": ["litter_pine_0", "litter_pine_1"],
    "litter_bamboo": ["litter_bamboo_0", "litter_bamboo_1"],
}

# Per paint mark: `share` of its cells take a piece, picked from `sets` ([set, weight]); `patch`: where a low-frequency
# noise of the cell (`scale` cells) is over `above`, a patch of dense tall grass, up to `count` pieces a cell;
# `shore`: a cell by the water takes reeds at this share. Marks not listed (paths, paving, granite, planks, roofs,
# walls, snow) take none.
BIOMES = {
    "g": {"share": 0.34, "sets": [["grass_tall", 5], ["grass_low", 2], ["flowers", 2.5], ["stones", 1], ["ferns", 1],
                                  ["shrublets", 1], ["mushrooms", 0.35]],
          "patch": {"scale": 4.2, "above": 0.63, "count": 3, "set": "grass_tall"}, "shore": 0.6},
    "f": {"share": 0.62, "sets": [["flowers", 6], ["grass_tall", 2], ["grass_low", 1]],
          "patch": {"scale": 4.2, "above": 0.7, "count": 2, "set": "grass_tall"}, "shore": 0.4},
    "b": {"share": 0.75, "sets": [["flowers", 1]]},
    "m": {"share": 0.42, "sets": [["reeds", 3], ["grass_tall", 3], ["grass_low", 2], ["flowers", 0.5]],
          "patch": {"scale": 3.6, "above": 0.6, "count": 3, "set": "grass_tall"}, "shore": 0.75},
    "r": {"share": 0.26, "sets": [["moss", 3], ["stones", 2], ["grass_low", 1], ["ferns", 1]]},
    # Decision 44: sand takes a few pebbles and a tuft of dune grass here and there, and reeds at the waterline. Snow
    # (`n`, `k`) takes none: nothing grows through it (its own decals are the stalks that show).
    "a": {"share": 0.1, "sets": [["stones", 3], ["grass_low", 1]], "shore": 0.3},
}
# The litter round a tree: cells within `radius` cells of its footprint take its litter at `share` (before the biome's
# own pick).
LITTER = {"radius": 2.6, "share": 0.55}
# The keep-clear rules (TopdownFoliage): rings of cells round each kind of spot that take no piece.
CLEAR = {"spawn": 1, "place": 1, "portal": 1, "foe": 0}
