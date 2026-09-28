"""The terrain tiles: floor tops, wall faces, stairs, water frames, auto-tile transitions and light overlays.

Each function returns a 16 x 16 `Img`. Tops tile seamlessly with themselves (their noise repeats every 16 px);
faces tile sideways and, below their first row, downwards. The rules they follow are in docs/redesign/art_bible.md.
"""
from __future__ import annotations

from canvas import T, Img, h01, tile, vnoise
from palette import (BAMBOO, CLEAR, DARKWOOD, DIRT, EARTH, FOAM, GOLDR, GRASS, LOTUS, MOSS, PAD, PAPER, PAVE,
                     PGOLD, PLASTER, RED, ROCK, ROOF, SHADE, STONE, WARM_RIM, WATER, WOOD, alpha)


def _k(v: float, cuts: tuple, base: int) -> int:
    """Quantise a noise value into a ramp index: each cut passed adds one step."""
    return base + sum(1 for c in cuts if v > c)


# ============================================================================================================ tops
def grass(seed: int, kind: str = "plain") -> Img:
    """A sunlit meadow: soft clumps two ramp steps apart, blade tufts with a lit tip and a shaded root, and on some
    variants small blossoms or clover. Kinds: plain, lush (more tufts), flowers, clover."""
    t = tile()
    for j in range(T):
        for i in range(T):
            n = 0.6 * vnoise(i, j, seed, 8) + 0.4 * vnoise(i, j, seed + 7, 4)
            k = _k(n, (0.36, 0.62), 2)
            g = h01(i, j, seed + 3)
            if g < 0.07:
                k -= 1
            elif g > 0.93:
                k += 1
            t.put(i, j, GRASS[k])
    tufts = 9 if kind == "lush" else 6
    for n in range(tufts):
        x, y = int(h01(n, 1, seed) * T), int(h01(n, 2, seed) * T)
        shape = int(h01(n, 3, seed) * 3)
        pts = [((0, 0), 5), ((0, 1), 4), ((1, 1), 2)] if shape == 0 else \
              [((0, 0), 5), ((2, 0), 5), ((1, 1), 4), ((0, 1), 4), ((2, 1), 3), ((1, 2), 1)] if shape == 1 else \
              [((1, 0), 6), ((0, 1), 5), ((1, 1), 4), ((2, 1), 4), ((1, 2), 2)]
        for (dx, dy), k in pts:
            t.put((x + dx) % T, (y + dy) % T, GRASS[k])
    if kind == "flowers":
        for n in range(4):
            x, y = 1 + int(h01(n, 5, seed) * 13), 1 + int(h01(n, 6, seed) * 13)
            petal = [PAPER, PGOLD, LOTUS[3], PAPER][n]
            for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
                t.put(x + dx, y + dy, petal)
            t.put(x, y, GOLDR[2] if n != 1 else LOTUS[1])
            t.put(x + 1, y + 1, GRASS[1])
    if kind == "clover":
        for n in range(3):
            x, y = 2 + int(h01(n, 8, seed) * 11), 2 + int(h01(n, 9, seed) * 11)
            for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1), (-1, 1), (1, -1)):
                t.put(x + dx, y + dy, GRASS[3] if (dx + dy) % 2 else GRASS[4])
            t.put(x, y, GRASS[5])
            t.put(x + 1, y + 2, GRASS[1])
    return t


def dirt(seed: int) -> Img:
    """A packed-earth path: warm ochre with worn lighter patches, small pebbles lit from the upper left and a few
    fine cracks."""
    t = tile()
    for j in range(T):
        for i in range(T):
            n = 0.6 * vnoise(i, j, seed, 8) + 0.4 * vnoise(i, j, seed + 5, 4)
            k = _k(n, (0.34, 0.66), 2)
            if h01(i, j, seed + 1) < 0.08:
                k += 1 if n > 0.5 else -1
            t.put(i, j, DIRT[k])
    for n in range(5):
        x, y = int(h01(n, 1, seed) * T), int(h01(n, 2, seed) * T)
        big = h01(n, 3, seed) < 0.4
        t.put(x, y, DIRT[5])
        if big:
            t.put((x + 1) % T, y, DIRT[4])
        t.put((x + (2 if big else 1)) % T, (y + 1) % T, DIRT[1])
    x, y = int(h01(9, 1, seed) * 12), int(h01(9, 2, seed) * 12)
    for d in range(4):
        t.put((x + d) % T, (y + (d // 2)) % T, DIRT[1])
    return t


def paving(seed: int, kind: str = "a") -> Img:
    """Town flagstones. One cell holds one big slab (kind b), two long slabs laid east-west (a), two laid north-south
    (c) or two long slabs with moss in the joint (m); the loader mixes kinds per cell, so the square reads as laid
    stone at a large, calm scale rather than a brick grid. Each slab has its own warm tint, a lit top and west edge, a
    soft shaded foot and a little wear; joints sit two steps under the stone."""
    t = tile()
    split = {"a": "h", "m": "h", "b": None, "c": "v"}[kind]
    for j in range(T):
        for i in range(T):
            if split == "h":
                slab, sx, sy, w, hgt = j // 8, i, j % 8, T, 8
            elif split == "v":
                slab, sx, sy, w, hgt = i // 8, i % 8, j, 8, T
            else:
                slab, sx, sy, w, hgt = 0, i, j, T, T
            base = 3 if h01(slab, 1, seed) < 0.45 else 4
            if sx == 0 or sy == 0:
                col = PAVE[2]
                if kind == "m" and h01(i, j, seed + 11) < 0.45:
                    col = MOSS[3] if h01(i, j, seed + 12) < 0.7 else MOSS[4]
            elif sy == 1 or sx == 1:
                col = PAVE[base + 1] if (sy == 1) else PAVE[base] if base == 4 else PAVE[base + 1]
            elif sy == hgt - 1 or sx == w - 1:
                col = PAVE[base - 1]
            else:
                col = PAVE[base]
                v = h01(i, j, seed + slab * 7)
                if v < 0.06:
                    col = PAVE[base - 1]
                elif v > 0.96:
                    col = PAVE[base + 1]
            t.put(i, j, col)
    return t


def stone_top(seed: int, cracked: bool = False) -> Img:
    """Dressed granite slabs, 16 x 8, offset by 8 on alternate courses: the promenade, terrace caps and stair
    landings. Cooler and a step lighter than the town paving so a built edge stands out from the square."""
    t = tile()
    for j in range(T):
        course, sy = j // 8, j % 8
        for i in range(T):
            sx = (i + course * 8) % 16
            base = 5 if h01(course, (i + course * 8) // 16, seed) > 0.7 else 4
            if sx == 0 or sy == 0:
                col = STONE[3]
            elif sy == 1 or sx == 1:
                col = STONE[base + 1]
            elif sy == 7:
                col = STONE[base - 1]
            else:
                col = STONE[base] if h01(i, j, seed) > 0.08 else STONE[base - 1]
            t.put(i, j, col)
    if cracked:
        x, y = 5, 3
        for d in range(3):
            t.put(x + d, y + d // 2, STONE[2])
    return t


def rock_top(seed: int) -> Img:
    """The top of a karst cliff: pale weathered limestone in lumps, cracks, and moss gathered in the hollows."""
    t = tile()
    for j in range(T):
        for i in range(T):
            n = vnoise(i, j, seed, 4)
            m = vnoise(i, j, seed + 3, 8)
            if m > 0.62:
                col = MOSS[4] if n > 0.5 else MOSS[3]
                if h01(i, j, seed) > 0.9:
                    col = MOSS[5]
            else:
                col = ROCK[_k(n, (0.3, 0.55, 0.78), 2)]
            t.put(i, j, col)
    for n in range(3):
        x, y = int(h01(n, 4, seed) * T), int(h01(n, 5, seed) * T)
        for d in range(3):
            t.put((x + d) % T, (y + d % 2) % T, ROCK[1])
    return t


def wood_deck(seed: int) -> Img:
    """Pier planks running east-west (across the way you walk out), 4 px each: a lit top edge, grain, staggered end
    joints, nail heads, and a dark gap onto the water below."""
    t = tile()
    for j in range(T):
        p, k = j // 4, j % 4
        joint = int(h01(p, 0, seed) * 12) + 2
        for i in range(T):
            if k == 3:
                col = DARKWOOD[1]
            elif k == 0:
                col = WOOD[5]
            else:
                col = WOOD[4] if (h01(i // 3, j, seed + p) > 0.3) else WOOD[3]
            if i == joint and k != 3:
                col = DARKWOOD[2]
            if k in (1, 2) and h01(i, p, seed + 9) < 0.06:
                col = WOOD[2]
            t.put(i, j, col)
        if k == 1:
            t.put((joint + 2) % T, j, DARKWOOD[0])
            t.put((joint - 2) % T, j, DARKWOOD[0])
    return t


def roof_top(seed: int) -> Img:
    """Grey fired roof tiles seen from above: ribs of round cover tiles running down the slope (lit on their west
    side, a highlight down their crown) between channel tiles in shade, each cover tile lapping the next every 4 px.
    It is an even, bright plane with a clear grain, so a roof reads as a floor you can land on (decision 29)."""
    t = tile()
    for j in range(T):
        row = j % 4
        for i in range(T):
            col4 = i % 4
            col = (ROOF[5], ROOF[5], ROOF[4], ROOF[2])[col4]
            if row == 0 and col4 < 2:
                col = ROOF[6]
            elif row == 3 and col4 < 3:
                col = ROOF[4] if col4 < 2 else ROOF[3]
            if h01(i, j, seed) < 0.02:
                col = MOSS[3]
            t.put(i, j, col)
    return t


def wall_top(seed: int) -> Img:
    """The grey-tiled cap of a whitewashed courtyard wall seen from above: a ridge of tiles along the middle, cover
    tiles running off it to both sides."""
    t = tile()
    for j in range(T):
        for i in range(T):
            if j in (7, 8):
                col = ROOF[5] if j == 7 else ROOF[3]
                if i % 4 == 0:
                    col = ROOF[2]
            else:
                col4 = i % 4
                col = (ROOF[5], ROOF[4], ROOF[2], ROOF[3])[col4]
                if j in (6, 9):
                    col = ROOF[1]
                elif (j < 7 and j % 3 == 0) or (j > 8 and j % 3 == 2):
                    col = ROOF[3] if col4 < 2 else ROOF[2]
            if h01(i, j, seed) < 0.03:
                col = MOSS[3]
            t.put(i, j, col)
    return t


# =========================================================================================================== faces
# A face is the south side of a raised level, one tile row per level. Faces sit two to three ramp steps under their
# top, lean cool, and open with a lit lip (the top's front edge) over a dark contact line (art bible §5).

def _lip(t: Img, top: list, rows: int = 2, drip=None, seed: int = 0) -> int:
    """The top's front edge: its lit rim and body, then a hanging fringe (grass, moss) and a dark line under it.
    Returns the first face row below the lip."""
    for i in range(T):
        t.put(i, 0, top[6] if len(top) > 6 else top[-1])
        for r in range(1, rows):
            t.put(i, r, top[4])
    y = rows
    if drip is not None:
        for i in range(T):
            d = int(h01(i, 0, seed + 40) ** 2 * 5)
            for r in range(d):
                t.put(i, y + r, drip[3] if r < d - 1 else drip[2])
    return y


def earth_face(seed: int, first: bool) -> Img:
    """The bank of a grass terrace: packed soil in strata, stones set in it, roots, and on the first row the grass
    lip hanging over the edge."""
    t = tile()
    for j in range(T):
        for i in range(T):
            n = vnoise(i, j, seed, 8, 4)
            k = _k(n, (0.45, 0.8), 1)
            if (j + int(h01(i // 4, 0, seed) * 3)) % 6 == 0:
                k = 1
            t.put(i, j, EARTH[k])
    for n in range(3):
        x, y = int(h01(n, 1, seed) * 13), 3 + int(h01(n, 2, seed) * 10)
        t.rect(x, y, 3, 2, EARTH[4])
        t.put(x, y, EARTH[5])
        t.put(x + 1, y, EARTH[5])
        t.put(x + 2, y + 1, EARTH[2])
    if first:
        y = _lip(t, GRASS, 2, GRASS, seed)
        for i in range(T):
            d = int(h01(i, 0, seed + 40) ** 2 * 5)
            t.put(i, y + d, EARTH[0])
            t.put(i, y + d + 1, EARTH[1])
    else:
        x = int(h01(7, 7, seed) * 12) + 2
        for r in range(5):
            t.put(x + (r % 2), r, EARTH[0])
    return t


def stone_face(seed: int, first: bool, top=STONE) -> Img:
    """A dressed retaining wall: ashlar courses 4 px high (3 of block, 1 of mortar), blocks 8 wide, offset by 4 on
    alternate courses; each block lit along its top, shaded at its right end; moss in a few joints."""
    t = tile()
    for j in range(T):
        course, r = j // 4, j % 4
        for i in range(T):
            sx = (i + (course % 2) * 4) % 8
            blk = (i + (course % 2) * 4) // 8
            base = 3 if h01(blk, course, seed) > 0.75 else 2
            if r == 3 or sx == 7:
                col = STONE[0] if r == 3 else STONE[1]
                if h01(i, j, seed + 3) < 0.12:
                    col = MOSS[2]
            elif r == 0:
                col = STONE[base + 1]
            elif sx == 6:
                col = STONE[base - 1]
            else:
                col = STONE[base] if h01(i, j, seed) > 0.1 else STONE[base - 1]
            t.put(i, j, col)
    if first:
        _lip(t, top, 2)
        t.hline(0, 2, T, STONE[0])
        for i in range(T):
            if h01(i, 3, seed) < 0.25:
                t.put(i, 3, MOSS[3])
    return t


def rock_face(seed: int, first: bool) -> Img:
    """A karst cliff: vertical pillars of limestone split by fissures, each pillar lit on its west side and shaded on
    its east; ledges across it now and then; on the first row the mossy top hangs over."""
    t = tile()
    cuts = [0, 5, 9, 13]
    for i in range(T):
        ci = max(k for k, c in enumerate(cuts) if c <= i)
        x0 = cuts[ci]
        x1 = cuts[ci + 1] if ci + 1 < len(cuts) else T
        for j in range(T):
            n = vnoise(i, j, seed + ci, 4, 8)
            base = 2 if n > 0.5 else 1
            if i == x0:
                col = ROCK[0]
            elif i == x0 + 1:
                col = ROCK[base + 2]
            elif i == x1 - 1:
                col = ROCK[base - 1]
            else:
                col = ROCK[base + (1 if n > 0.7 else 0)]
            if (j + ci * 5) % 11 == 0 and i != x0:
                col = ROCK[0]
            elif (j + ci * 5) % 11 == 1 and i != x0:
                col = ROCK[3]
            t.put(i, j, col)
    for n in range(2):
        x, y = int(h01(n, 1, seed) * 14), int(h01(n, 2, seed) * 14)
        t.put(x, y, MOSS[3])
        t.put(x + 1, y, MOSS[4])
        t.put(x, y + 1, MOSS[2])
    if first:
        y = _lip(t, ROCK, 2, MOSS, seed)
        for i in range(T):
            d = int(h01(i, 0, seed + 40) ** 2 * 5)
            t.put(i, y + d, ROCK[0])
    return t


def bank_face(seed: int, first: bool) -> Img:
    """The river embankment over water (the loader shows its top 8 px): a granite curb, the dark wet blocks below it,
    and a band of algae at the waterline."""
    t = tile()
    for j in range(T):
        course, r = j // 4, j % 4
        for i in range(T):
            sx = (i + (course % 2) * 6) % 12
            if r == 3 or sx == 11:
                col = STONE[0]
            elif r == 0:
                col = STONE[3]
            else:
                col = STONE[2] if h01(i, j, seed) > 0.12 else STONE[1]
            wet = j % 8
            if wet >= 5:
                col = MOSS[2] if (h01(i, j, seed + 1) < 0.5 and r != 3) else STONE[1]
            if wet == 7:
                col = MOSS[1] if h01(i, 0, seed + 2) < 0.6 else WATER[1]
            t.put(i, j, col)
    if first:
        _lip(t, STONE, 2)
        t.hline(0, 2, T, STONE[0])
    return t


def wood_face(seed: int, first: bool) -> Img:
    """A pier's side over the water: the deck's lit edge and the plank ends under it, then pilings with a lit west
    side, a cross brace, and the dark water in the pier's shadow between them."""
    t = tile()
    for j in range(T):
        for i in range(T):
            t.put(i, j, WATER[1] if j % 8 < 6 else WATER[2])
    for px in (2, 11):
        for j in range(T):
            t.put(px, j, WOOD[4])
            t.put(px + 1, j, WOOD[3])
            t.put(px + 2, j, WOOD[2])
        t.put(px + 1, 7, DARKWOOD[1])
    for i in range(T):
        t.put(i, 6, WOOD[2] if i % 5 else DARKWOOD[1])
    if first:
        for i in range(T):
            t.put(i, 0, WOOD[5])
            t.put(i, 1, WOOD[3] if i % 4 else DARKWOOD[1])
            t.put(i, 2, WOOD[2] if i % 4 else DARKWOOD[1])
            t.put(i, 3, DARKWOOD[1])
            t.put(i, 4, WATER[0])
    return t


def eave_face(seed: int) -> Img:
    """The front of a tiled roof, the first face row under a roof top: the lit verge, round tile ends every 4 px with
    drip tiles between, then the white wall in the eave's shadow (the next rows are `plaster_face`)."""
    t = tile()
    for i in range(T):
        t.put(i, 0, ROOF[6])
        t.put(i, 1, ROOF[4])
        c4 = i % 4
        t.put(i, 2, ROOF[5] if c4 == 1 else ROOF[3] if c4 in (0, 2) else ROOF[1])
        t.put(i, 3, ROOF[4] if c4 in (0, 1, 2) else ROOF[1])
        t.put(i, 4, ROOF[2] if c4 in (0, 2) else ROOF[3] if c4 == 1 else ROOF[1])
        t.put(i, 5, ROOF[1] if c4 != 3 else ROOF[0])
    for j in range(6, T):
        for i in range(T):
            col = PLASTER[2] if j < 9 else PLASTER[3]
            if j == 6:
                col = PLASTER[0]
            t.put(i, j, col)
    for j in range(6, T):
        t.put(0, j, DARKWOOD[2])
        t.put(1, j, DARKWOOD[3])
    t.hline(0, 12, T, DARKWOOD[2])
    return t


def plaster_face(seed: int, kind: str = "plain", plinth: bool = True) -> Img:
    """A whitewashed wall panel in a dark timber frame (kind plain), with a lattice window (window), or a red lacquer
    door with gold studs (door)."""
    t = tile()
    for j in range(T):
        for i in range(T):
            col = PLASTER[3] if h01(i // 2, j // 3, seed) > 0.15 else PLASTER[2]
            if plinth and j >= 13:
                col = STONE[3] if j == 13 else STONE[2]
            t.put(i, j, col)
    for j in range(13 if plinth else T):
        t.put(0, j, DARKWOOD[2])
        t.put(1, j, DARKWOOD[3])
    if plinth:
        t.hline(0, 13, T, STONE[4])
    if kind == "window":
        t.rect(4, 2, 9, 8, DARKWOOD[1])
        for j in range(3, 9):
            for i in range(5, 12):
                if (i + j) % 3:
                    t.put(i, j, PGOLD if j < 5 else GOLDR[2])
        t.hline(4, 10, 9, PLASTER[0])
    elif kind == "door":
        t.rect(2, 1, 13, 12, RED[1])
        for x0 in (3, 9):
            t.rect(x0, 2, 5, 11, RED[3])
            t.vline(x0, 2, 11, RED[4])
            t.put(x0 + 4, 6, GOLDR[2])
            t.put(x0 + 4, 9, GOLDR[2])
        t.vline(8, 2, 11, RED[0])
        t.hline(2, 13, 13, STONE[5])
    return t


def wall_face(seed: int, first: bool) -> Img:
    """A whitewashed courtyard wall: on the first row the grey cap's lit verge and round tile ends, then lime plaster
    with faint streaks and a damp, darker foot."""
    t = tile()
    for j in range(T):
        for i in range(T):
            col = PLASTER[4] if h01(i // 3, j // 5, seed) > 0.2 else PLASTER[3]
            if h01(i, 0, seed + 5) < 0.15 and j > 6:
                col = PLASTER[2]
            if j >= 14:
                col = PLASTER[2] if j == 14 else PLASTER[1]
            t.put(i, j, col)
    if first:
        for i in range(T):
            c4 = i % 4
            t.put(i, 0, ROOF[6])
            t.put(i, 1, ROOF[5] if c4 == 1 else ROOF[3] if c4 != 3 else ROOF[1])
            t.put(i, 2, ROOF[4] if c4 != 3 else ROOF[1])
            t.put(i, 3, ROOF[1])
            t.put(i, 4, PLASTER[0])
            t.put(i, 5, PLASTER[2])
    return t


def stairs() -> Img:
    """Two granite steps (the loader draws the top 8 px, one step, per 8 px of rise): the lit nosing, the tread, the
    shadow under the nosing, and the riser."""
    t = tile()
    for s in range(2):
        y = s * 8
        for i in range(T):
            t.put(i, y, STONE[6])
            t.put(i, y + 1, STONE[5])
            t.put(i, y + 2, STONE[5] if h01(i, y, 3) > 0.1 else STONE[4])
            t.put(i, y + 3, STONE[4])
            t.put(i, y + 4, STONE[4])
            t.put(i, y + 5, STONE[1])
            t.put(i, y + 6, STONE[3])
            t.put(i, y + 7, STONE[2])
    return t


# =========================================================================================================== water
def water(frame: int, sides: int = 0) -> Img:
    """The Jade River, one of four frames (250 ms each). The body is still jade-teal with slow darker swells; small
    ripple dashes brighten, peak with a pale glint and fade in turn, each a quarter-cycle apart, and drift a pixel east
    as they fade. `sides` holds the land around the cell (bit 1 N, 2 E, 4 S, 8 W): a foam line breathes at the
    waterline and the water beside a bank lies in its shade (art bible §7)."""
    t = tile()
    for j in range(T):
        for i in range(T):
            n = vnoise(i, j, 70, 8, 4)
            t.put(i, j, WATER[3] if n > 0.42 else WATER[2])
    for d in range(4):
        x0, y0 = int(h01(d, 1, 71) * T), int(h01(d, 2, 71) * T)
        ln = 3 + int(h01(d, 3, 71) * 3)
        ph = (frame + d) % 4
        if ph == 0:
            continue
        x0 += 1 if ph == 3 else 0
        n = {1: ln - 2, 2: ln, 3: ln - 1}[ph]
        for k in range(n):
            col = WATER[5] if ph != 2 else (WATER[7] if k == 1 else WATER[6] if k < 3 else WATER[5])
            if ph == 3:
                col = WATER[4]
            t.put((x0 + k) % T, y0, col)
        t.put((x0 + 1) % T, (y0 + 1) % T, WATER[1] if ph == 2 else WATER[2])
    if sides:
        _shore(t, frame, sides)
    return t


def _shore(t: Img, frame: int, sides: int) -> None:
    breathe = (0, 1, 1, 0)[frame]
    # The waterline sits where each side shows on screen: under the bank face (row 0), on the land's top edge to the
    # south (row 7, since the water is drawn 8 px low), and on the tile's edge to either side.
    if sides & 1:
        for i in range(T):
            for r in range(1, 5):
                t.blend(i, r, SHADE, (110, 80, 50, 25)[r - 1])
            t.put(i, 0, FOAM if h01(i, frame, 80) > 0.55 else WATER[6])
            if breathe and h01(i, 5, 80) > 0.6:
                t.put(i, 1, WATER[6])
    if sides & 4:
        for i in range(T):
            t.put(i, 5, WATER[4] if h01(i, frame, 81) > 0.5 else WATER[3])
            t.put(i, 6, WATER[5])
            t.put(i, 7, FOAM if h01(i, frame, 82) > 0.5 else WATER[6])
            if breathe and h01(i, 6, 82) > 0.55:
                t.put(i, 5, WATER[6])
            for r in range(8, T):
                t.put(i, r, WATER[4])
    for bit, xs in ((8, (0, 1, 2)), (2, (15, 14, 13))):
        if not sides & bit:
            continue
        for j in range(T):
            if sides & 4 and j > 7:
                continue
            t.put(xs[0], j, FOAM if h01(j, frame + bit, 83) > 0.6 else WATER[6])
            t.put(xs[1], j, WATER[5] if (breathe or h01(j, 1, 83) > 0.5) else WATER[4])
            t.put(xs[2], j, WATER[4] if h01(j, 2, 83) > 0.4 else t.get(xs[2], j))


# ===================================================================================================== transitions
CORNER_KEYS = [(tl, tr, bl, br) for tl in (0, 1) for tr in (0, 1) for bl in (0, 1) for br in (0, 1)]


def corner_name(corners: tuple) -> str:
    return "".join(str(v) for v in corners)


def blend_corners(over: Img, under: Img, corners: tuple, seed: int, over_ramp: list, under_ramp: list) -> Img:
    """A corner-matched transition tile (art bible §6): `over` (grass) covers the corners marked 1 and `under` (a path
    or paving) shows at the corners marked 0. The edge follows the bilinear blend of the four corners, roughened by
    noise that vanishes wherever a tile edge has one material at both ends, so neighbours always meet cleanly. The
    grass edge gets a lit fringe on its sunny side and throws a 1 px shade onto the ground to its lower right."""
    tl, tr, bl, br = corners

    def cover(i: int, j: int) -> bool:
        u, v = min(max((i + 0.5) / T, 0.0), 1.0), min(max((j + 0.5) / T, 0.0), 1.0)
        f = (tl * (1 - u) + tr * u) * (1 - v) + (bl * (1 - u) + br * u) * v
        top, bot, left, right = abs(tl - tr), abs(bl - br), abs(tl - bl), abs(tr - br)
        # Noise fades to nothing along an edge whose two corners agree.
        amp = min(1.0, (top * (1 - v) + bot * v + left * (1 - u) + right * u) * 2.0) * 0.4
        n = (vnoise(i, j, seed, 4) - 0.5) * 2.0 * amp
        return f + n > 0.5

    t = tile()
    for j in range(T):
        for i in range(T):
            if cover(i, j):
                col = over.get(i, j)
                if not cover(i - 1, j) or not cover(i, j - 1):
                    col = over_ramp[5]
                elif not cover(i + 1, j) or not cover(i, j + 1):
                    col = over_ramp[2]
            else:
                col = under.get(i, j)
                if cover(i - 1, j) or cover(i, j - 1):
                    col = under_ramp[1]
            t.put(i, j, col)
    return t


# ======================================================================================================== overlays
def overlay(kind: str) -> Img:
    """Translucent light tiles the room view lays over tops, faces and stairs (art bible §5):
    rim_w / rim_e / rim_n: the edge of a top whose west / east / north neighbour is lower (lit, shaded, the drop behind);
    ao_n: contact shade at the foot of a face, on the floor right under it;
    shade_w: the shadow a higher west neighbour casts on this floor (light from the upper left);
    end_w / end_e: a face's end where it turns a corner, lit at the west end and shaded at the east;
    cheek_w / cheek_e: the granite cheeks of a flight of stairs, lit on the west and shaded on the east."""
    t = tile()
    if kind in ("end_w", "end_e", "cheek_w", "cheek_e"):
        cols = {"end_w": ((0, WARM_RIM, 70),), "end_e": ((15, SHADE, 120),),
                "cheek_w": ((0, WARM_RIM, 90), (1, WARM_RIM, 30)), "cheek_e": ((15, SHADE, 150), (14, SHADE, 60))}[kind]
        for x, col, a in cols:
            for j in range(T):
                t.put(x, j, alpha(col, a))
        return t
    if kind == "rim_w":
        for j in range(T):
            t.put(0, j, alpha(WARM_RIM, 150))
            t.put(1, j, alpha(WARM_RIM, 50))
    elif kind == "rim_e":
        for j in range(T):
            t.put(15, j, alpha(SHADE, 150))
            t.put(14, j, alpha(SHADE, 60))
    elif kind == "rim_n":
        for i in range(T):
            t.put(i, 0, alpha(SHADE, 170))
            t.put(i, 1, alpha(WARM_RIM, 70))
    elif kind == "ao_n":
        for i in range(T):
            for r, a in enumerate((120, 80, 45, 20)):
                t.put(i, r, alpha(SHADE, a))
    elif kind == "shade_w":
        for j in range(T):
            for c, a in enumerate((110, 90, 70, 45, 20)):
                if c == 4 and (j % 2):
                    continue
                t.put(c, j, alpha(SHADE, a))
    return t


def composite(base: Img, over: Img) -> Img:
    out = Img(base.w, base.h)
    out.img.alpha_composite(base.img)
    out.img.alpha_composite(over.img)
    return out


__all__ = ["grass", "dirt", "paving", "stone_top", "rock_top", "wood_deck", "roof_top", "wall_top", "earth_face",
           "stone_face", "rock_face", "bank_face", "wood_face", "eave_face", "plaster_face", "wall_face", "stairs",
           "water", "blend_corners", "overlay", "CORNER_KEYS", "corner_name", "composite", "CLEAR", "BAMBOO", "PAD"]
