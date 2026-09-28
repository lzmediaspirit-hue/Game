"""Terrain v2 (decision 40; docs/redesign/art_bible.md "Terrain v2"): the ground, edges, faces, water and roofs drawn
the Alabaster Dawn way, in Jade River's own materials.

What breaks the 16 px grid:
  - **Macro sets.** Every ground material is one pattern of 4 x 4 tiles (8 x 8 for the paving), periodic, cut into its
    tiles. The room view picks a cell's tile by its place in the pattern (x mod 4, y mod 4), so neighbours always join
    seamlessly and a flagstone or a plank runs across tile edges. The patterns hold only fine detail, never a blob
    big enough to be seen repeating: the large and middle scales come from the next two layers.
  - **Tone patches.** Two corner-matched sets of translucent tints (warm sun, cool shade), laid by a low-frequency
    noise over the room's corners (TopdownTerrain), with soft stepped edges pinned to the tile edges' midpoints.
  - **Decals.** Small transparent tiles scattered by a hash of the cell, per material: clumps and tufts of grass,
    flowers, clover, pebbles, stones, fallen leaves, petals, cracks, moss, weeds, puddles.
  - **Positional transitions.** Grass over a path or paving is an overlay per corner case *and* place in the grass
    pattern: its grass is the pattern's own pixels there and its edge follows noise periodic in 64 px, so an edge
    never repeats every 16 px (no sawtooth) and meets its neighbours exactly. Blades overhang the edge and a soft
    two-step shadow falls on the path below and to the east of it.
Faces are 64 px patterns too: a first row with the lip (4 tiles) and two body rows (4 tiles each) that repeat downward,
so a cliff shows rock mass across tiles rather than one repeated block.

The water: a 64 px pattern in four frames (swells, a shimmering caustic net, glints), a static corner-matched depth
tint (deeper and bluer away from land), and per shore case an animated overlay: the bed showing through the shallows,
the bank's shadow on the water where the land stands between it and the sun, the foam line breathing at the waterline
and a ripple leaving the shore.

Nothing here uses a random generator: every value comes from a coordinate hash, so the build is byte-identical.
"""
from __future__ import annotations

import math

from canvas import T, Img, h01
from palette import (AO_STEPS, BED2, DIRT2, EARTH2, FLOWER, FOAM2, GOLDR, GRASS2, LEAFFALL, MOSS2, PAVE2, PETAL,
                     PGOLD, PLASTER2, RED2, REED, ROCK2, ROOF2, SHADOW, SHADOW_A, STONE2, SUN, TIMBER2, TONE_A, TONE_SHADE,
                     TONE_SUN, WATER2, WOOD2, alpha)

M = 4          # a macro pattern is M x M tiles
P = M * T      # 64 px


# ============================================================================================================ noise
def _smooth(t: float) -> float:
    return t * t * (3.0 - 2.0 * t)


def pn(x: float, y: float, seed: int, cell: int, px: int = P, py: int = P) -> float:
    """Value noise in [0, 1) on a lattice of `cell` px, periodic in px x py (multiples of `cell`)."""
    nx, ny = max(1, px // cell), max(1, py // cell)
    fx, fy = x / cell, y / cell
    x0, y0 = math.floor(fx), math.floor(fy)
    tx, ty = _smooth(fx - x0), _smooth(fy - y0)

    def g(a: int, b: int) -> float:
        return h01(a % nx, b % ny, seed)

    top = g(x0, y0) * (1 - tx) + g(x0 + 1, y0) * tx
    bot = g(x0, y0 + 1) * (1 - tx) + g(x0 + 1, y0 + 1) * tx
    return top * (1 - ty) + bot * ty


def pnxy(x: float, y: float, seed: int, cx: int, cy: int, px: int = P, py: int = P) -> float:
    """Value noise on a cx x cy lattice (stretched), periodic in px x py."""
    return pn(x * cy / cx, y, seed, cy, px * cy // cx, py)


def fbm(x: float, y: float, seed: int, cells=(16, 8, 4), weights=(0.55, 0.3, 0.15), px: int = P, py: int = P) -> float:
    return sum(w * pn(x, y, seed + 17 * k, c, px, py) for k, (c, w) in enumerate(zip(cells, weights)))


def hp(x: int, y: int, seed: int, px: int = P, py: int = P) -> float:
    """A hash of a pixel, periodic in px x py."""
    return h01(x % px, y % py, seed)


def cells(seed: int, nx: int, ny: int, px: int, py: int, jitter: float = 0.85) -> list:
    """A periodic Voronoi partition of px x py with one jittered site per nx x ny block. Per pixel [y][x]: (nearest
    site, its distance, the second site, its distance, the third distance, the second site's offset from the first as
    (dx, dy)) so a caller can draw joints (d2 - d1 small), worn corners (d3 - d1 small) and which way an edge faces."""
    cw, ch = px / nx, py / ny
    sites = [((a + 0.5 + (h01(a, b, seed) - 0.5) * jitter) * cw, (b + 0.5 + (h01(a, b, seed + 1) - 0.5) * jitter) * ch)
             for b in range(ny) for a in range(nx)]
    out = []
    for y in range(py):
        row = []
        for x in range(px):
            a0, b0 = int(x // cw), int(y // ch)
            cand = []
            for db in (-2, -1, 0, 1, 2):
                for da in (-2, -1, 0, 1, 2):
                    a, b = a0 + da, b0 + db
                    idx = (b % ny) * nx + (a % nx)
                    sx = sites[idx][0] + (a - a % nx) * cw
                    sy = sites[idx][1] + (b - b % ny) * ch
                    cand.append((math.hypot(x + 0.5 - sx, y + 0.5 - sy), idx, sx, sy))
            cand.sort()
            (d1, i1, x1, y1), (d2, i2, x2, y2), (d3, _, _, _) = cand[0], cand[1], cand[2]
            row.append((i1, d1, i2, d2, d3, (x2 - x1, y2 - y1)))
        out.append(row)
    return out


def cut(img: Img, w: int = M, h: int = M) -> list:
    """The w x h tiles of a pattern, row-major."""
    out = []
    for ty in range(h):
        for tx in range(w):
            t = Img(T, T)
            t.img.alpha_composite(img.img.crop((tx * T, ty * T, tx * T + T, ty * T + T)))
            out.append(t)
    return out


def _q(v: float, cuts: tuple, base: int) -> int:
    return base + sum(1 for c in cuts if v > c)


def _clamp(k: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, k))


def mix(a: tuple, b: tuple, k: float) -> tuple:
    return (round(a[0] + (b[0] - a[0]) * k), round(a[1] + (b[1] - a[1]) * k), round(a[2] + (b[2] - a[2]) * k), 255)


def faces_nw(off: tuple) -> float:
    """How much an edge whose far side lies `off` away faces the north-west sun (+1) or turns from it (-1)."""
    n = math.hypot(off[0], off[1]) or 1.0
    return -(off[0] + off[1]) / (n * 1.4142)


# ============================================================================================================ grass
# Grass tufts, drawn from their root up: 'H' a bright tip (6), 'h' a lit tip (5), 'd' the blade in its own shade (3),
# 'D' its foot (2), 's' the shadow at its root (1), '.' leaves the ground. Rows top to bottom; the root is the bottom row's middle.
TUFTS = [
    ["h.h", "dhd", "DsD"],
    [".h.", "hdh", "d.d", "DsD"],
    ["h...h", "d.h.d", "DdhdD", ".DsD."],
    [".h..", "hd.h", "d.hd", "DssD"],
    ["h", "d", "s"],
    ["..h.h..", "h.d.d.h", "dhd.dhd", "Dd.s.dD", ".Ds.sD."],
    [".H.", "hdh", "dsd"],
    [".h.h.", "hdhdh", "ddhdd", "DdsdD", ".DsD."],
]


def stamp_tuft(img: Img, x: int, y: int, shape: int, ramp=GRASS2, wrap: int = 0, bright: bool = False) -> None:
    """A tuft with its root at (x, y); `wrap` > 0 wraps coordinates (a periodic pattern)."""
    rows = TUFTS[shape]
    h, w = len(rows), len(rows[0])
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == ".":
                continue
            k = {"H": 6, "h": 5, "d": 3, "D": 2, "s": 1}[ch]
            if bright and ch == "h":
                k = 6 if (i + j) % 3 == 0 else 5
            X, Y = x - w // 2 + i, y - (h - 1) + j
            if wrap:
                X, Y = X % wrap, Y % wrap
            img.put(X, Y, ramp[k])


def grass_macro(seed: int = 101, ramp=GRASS2) -> Img:
    """The meadow's base, 64 x 64 and periodic: a clean, saturated sunlit green (step 4) under crisp tufts of blades,
    about eight to a tile, each a few lit tips over blades in their own shade and a dark root (TUFTS), with a scatter
    of single blades between them. No blob larger than a tuft, so the period never shows; clumps, flowers and the
    light's large patches are the decals and tones laid over it."""
    img = Img(P, P, ramp[4])
    for gy in range(P // 4):
        for gx in range(P // 4):
            if h01(gx, gy, seed + 1) < 0.55:
                continue
            x = gx * 4 + int(h01(gx, gy, seed + 2) * 4)
            y = gy * 4 + int(h01(gx, gy, seed + 3) * 4)
            img.put(x % P, y % P, ramp[5])
            img.put(x % P, (y + 1) % P, ramp[3])
    for gy in range(P // 8):
        for gx in range(P // 8):
            for b in range(2):
                s = seed + 13 * b
                if b and h01(gx, gy, s + 4) < 0.35:
                    continue
                x = gx * 8 + int(h01(gx, gy, s + 5) * 8)
                y = gy * 8 + int(h01(gx, gy, s + 6) * 8)
                r = h01(gx, gy, s + 7)
                shape = 0 if r < 0.16 else 1 if r < 0.32 else 2 if r < 0.48 else 3 if r < 0.62 else 7 if r < 0.76 else 5 if r < 0.88 else 6
                stamp_tuft(img, x, y, shape, ramp, P)
    return img


# ============================================================================================================ tones
CORNER_KEYS = [(a, b, c, d) for a in (0, 1) for b in (0, 1) for c in (0, 1) for d in (0, 1)]


def key(corners: tuple) -> str:
    return "".join(str(v) for v in corners)


def corner_field(corners: tuple, i: float, j: float) -> float:
    """The bilinear blend of a tile's four corners (TL TR BL BR) at pixel (i, j), clamped to the tile."""
    tl, tr, bl, br = corners
    u, v = min(max((i + 0.5) / T, 0.0), 1.0), min(max((j + 0.5) / T, 0.0), 1.0)
    return (tl * (1 - u) + tr * u) * (1 - v) + (bl * (1 - u) + br * u) * v


TINT_STEPS = (255, 200, 140, 72)   # a tint mask's alpha, inside the patch and its three softening steps


def tint_mask(corners: tuple, pos: tuple, seed: int = 400) -> Img:
    """A corner-matched tint patch as a white mask, per corner case and place in a 64 px pattern (like the grass
    overlay): it covers the corners marked 1, its edge follows noise periodic in 64 px (so it wanders several pixels and
    meets every neighbour exactly), softened in three alpha steps. The room view draws it with a colour (the tints in
    the manifest's `v2.tint`: the sun and shade patches over the ground, the depth over the water), so one set of
    shapes serves every tint."""
    ox, oy = pos[0] * T, pos[1] * T
    t = Img(T, T)
    for j in range(T):
        for i in range(T):
            n = fbm(ox + i, oy + j, seed, (16, 8), (0.65, 0.35))
            f = corner_field(corners, i, j) + (n - 0.5) * 0.9
            k = 0 if f > 0.68 else 1 if f > 0.58 else 2 if f > 0.48 else 3 if f > 0.38 else 4
            if k < 4:
                t.put(i, j, (255, 255, 255, TINT_STEPS[k]))
    return t


def tint_colour(col: tuple, a: int) -> list:
    """A tint's colour for the manifest: [r, g, b, a] in 0-1, three decimals."""
    return [round(col[0] / 255, 3), round(col[1] / 255, 3), round(col[2] / 255, 3), round(a / 255, 3)]


TINTS = {"sun": tint_colour(TONE_SUN, TONE_A[0]), "shade": tint_colour(TONE_SHADE, TONE_A[1]),
         "deep": tint_colour(WATER2[0], 80), "deeper": tint_colour(WATER2[0], 72)}


# ====================================================================================================== transitions
def grass_over(corners: tuple, pos: tuple, gmac: Img, seed: int = 500, ramp=GRASS2) -> Img:
    """Grass over a path or paving (art bible "Terrain v2", edges): the grass pattern's own pixels where the corner
    field and noise periodic in 64 px say grass, with its edge lit where it faces the sun (north and west), in shade
    where it faces away, blade tips poking up on the sunny side and hanging over on the shaded one, and a two-step
    blue-violet shadow on the ground below and east of it. Transparent elsewhere, so it lies over any path."""
    ox, oy = pos[0] * T, pos[1] * T
    R = range(-3, T + 3)
    cov = {}
    for j in R:
        for i in R:
            n = fbm(ox + i, oy + j, seed, (16, 8, 4), (0.5, 0.32, 0.18))
            cov[(i, j)] = corner_field(corners, i, j) + 0.62 * (n - 0.5) > 0.5
    blade: dict = {}
    for j in R:
        for i in R:
            if not cov[(i, j)]:
                continue
            X, Y = ox + i, oy + j
            if not cov.get((i, j - 1), True):          # the sunny north edge: tips poke up, lit
                hsh = hp(X, Y, seed + 1)
                if hsh < 0.5:
                    blade[(i, j - 1)] = 5
                    if hsh < 0.16 and not cov.get((i, j - 2), True):
                        blade[(i, j - 1)] = 4
                        blade[(i, j - 2)] = 6
            if not cov.get((i, j + 1), True):          # the shaded south edge: tips hang over
                hsh = hp(X, Y, seed + 2)
                if hsh < 0.42:
                    blade[(i, j + 1)] = 3
                    if hsh < 0.14 and not cov.get((i, j + 2), True):
                        blade[(i, j + 2)] = 2
            if not cov.get((i - 1, j), True) and hp(X, Y, seed + 3) < 0.3:
                blade.setdefault((i - 1, j), 5)
            if not cov.get((i + 1, j), True) and hp(X, Y, seed + 4) < 0.3:
                blade.setdefault((i + 1, j), 3)

    def solid(i: int, j: int) -> bool:
        return cov.get((i, j), False) or (i, j) in blade

    t = Img(T, T)
    for j in range(T):
        for i in range(T):
            if cov[(i, j)]:
                col = gmac.get((ox + i) % P, (oy + j) % P)
                if not cov[(i, j - 1)] or not cov[(i - 1, j)]:
                    col = ramp[5]
                elif not cov[(i, j + 1)]:
                    col = ramp[2]
                elif not cov[(i + 1, j)] or not cov[(i + 1, j + 1)]:
                    col = ramp[3]
                t.put(i, j, col)
            elif (i, j) in blade:
                t.put(i, j, ramp[blade[(i, j)]])
            else:
                a = 0
                if solid(i, j - 1):
                    a = 112
                elif solid(i, j - 2):
                    a = 56
                if solid(i - 1, j) or solid(i - 1, j - 1):
                    a = max(a, 72)
                if a:
                    t.put(i, j, alpha(SHADOW, a))
    return t


# =========================================================================================================== decals
# Each decal is a 16 x 16 transparent tile; its marks stay a pixel inside the tile so nothing is cut at an edge. They
# are lit from the north-west and throw a small blue-violet shadow to the south-east.

def _shadow_px(t: Img, x: int, y: int, a: int = 80) -> None:
    if 0 <= x < T and 0 <= y < T and t.get(x, y)[3] == 0:
        t.put(x, y, alpha(SHADOW, a))


def _blob(t: Img, cx: float, cy: float, rx: float, ry: float, seed: int, fill, rim_lit, rim_dark, wob: float = 0.35,
          shadow: bool = True) -> list:
    """An irregular blob lit from the north-west: returns its pixels."""
    pts = []
    for j in range(T):
        for i in range(T):
            dx, dy = (i + 0.5 - cx) / rx, (j + 0.5 - cy) / ry
            r = math.hypot(dx, dy)
            ang = math.atan2(dy, dx)
            lim = 1.0 + wob * (h01(int((ang + 3.2) * 2.2), 0, seed) - 0.5)
            if r <= lim and 1 <= i < T - 1 and 1 <= j < T - 1:
                pts.append((i, j))
    ps = set(pts)
    for (i, j) in pts:
        col = fill(i, j)
        if (i - 1, j) not in ps or (i, j - 1) not in ps:
            col = rim_lit
        elif (i + 1, j) not in ps or (i, j + 1) not in ps:
            col = rim_dark
        t.put(i, j, col)
    if shadow:
        for (i, j) in pts:
            for dx, dy, a in ((1, 1, 90), (0, 1, 70), (1, 0, 50)):
                if (i + dx, j + dy) not in ps:
                    _shadow_px(t, i + dx, j + dy, a)
    return pts


def d_clump(seed: int, ramp=GRASS2) -> Img:
    """A clump of lush grass about a tile across: five to eight tufts crowded together (their blades in their own
    shade, bright tips catching the sun), rising a little from a darker core, and its shadow on the lawn to the SE."""
    t = Img(T, T)
    rx, ry = 3.5 + h01(1, 1, seed) * 2.0, 2.0 + h01(1, 2, seed) * 1.2
    cx, cy = 2.5 + rx + h01(1, 3, seed) * (10 - 2 * rx), 4 + ry + h01(1, 4, seed) * (8 - 2 * ry)
    for j in range(T):
        for i in range(T):
            if ((i + 0.5 - cx) / rx) ** 2 + ((j + 0.5 - cy) / ry) ** 2 <= 0.8:
                t.put(i, j, ramp[3])
    n = 5 + int(h01(1, 5, seed) * 4)
    spots = sorted(((cx + (h01(k, 6, seed) - 0.5) * 2 * rx, cy + (h01(k, 7, seed) - 0.3) * 1.6 * ry, k) for k in range(n)),
                   key=lambda q: q[1])
    for x, y, k in spots:
        shape = (0, 1, 2, 3, 6, 5)[int(h01(k, 8, seed) * 6)]
        rows = TUFTS[shape]
        x = min(max(int(x), len(rows[0]) // 2 + 1), T - 2 - len(rows[0]) // 2)
        y = min(max(int(y), len(rows)), T - 3)
        stamp_tuft(t, x, y, shape, ramp, 0, True)
    cast_shadow(t, ((1, 1, 100), (0, 1, 84), (1, 0, 40), (2, 1, 44), (1, 2, 36)))
    return t


def cast_shadow(t: Img, taps: tuple) -> None:
    """The small shadow a decal's marks cast on the ground to the south-east: each transparent pixel takes the darkest
    of the taps (dx, dy, alpha) that reach it from a solid pixel."""
    solid = {(i, j) for j in range(T) for i in range(T) if t.get(i, j)[3] == 255}
    shade: dict = {}
    for (i, j) in solid:
        for dx, dy, a in taps:
            p = (i + dx, j + dy)
            if p not in solid and 0 <= p[0] < T and 0 <= p[1] < T and t.get(*p)[3] == 0:
                shade[p] = max(shade.get(p, 0), a)
    for (i, j), a in sorted(shade.items()):
        t.put(i, j, alpha(SHADOW, a))


def d_tuft(seed: int, ramp=GRASS2) -> Img:
    """A tall tuft: three to five blades fanning up from one root, lit tips, a dark root and a small shadow."""
    t = Img(T, T)
    rx, ry = 4 + int(h01(2, 1, seed) * 8), 9 + int(h01(2, 2, seed) * 4)
    n = 3 + int(h01(2, 3, seed) * 3)
    for b in range(n):
        lean = (b - (n - 1) / 2) * (0.5 + h01(b, 4, seed) * 0.4)
        ln = 4 + int(h01(b, 5, seed) * 4)
        for s in range(ln):
            x = round(rx + lean * s / 2)
            y = ry - s
            c = ramp[2] if s == 0 else ramp[3] if s < ln // 2 else ramp[4] if s < ln - 1 else ramp[5 + (h01(b, 6, seed) > 0.6)]
            if 1 <= x < T - 1 and 1 <= y < T - 1:
                t.put(x, y, c)
    for dx in range(0, 4):
        _shadow_px(t, rx + dx, ry + 1, 90 - dx * 15)
    _shadow_px(t, rx + 1, ry, 70)
    return t


def d_flowers(seed: int, cols: list, n: int = 3) -> Img:
    """A few wild flowers: a four-petal bloom or a tight bud on a dark leaf, lit from the north-west."""
    t = Img(T, T)
    placed = []
    for k in range(n * 3):
        if len(placed) >= n:
            break
        x, y = 2 + int(h01(k, 1, seed) * 11), 2 + int(h01(k, 2, seed) * 10)
        if any(abs(x - a) < 4 and abs(y - b) < 4 for a, b in placed):
            continue
        placed.append((x, y))
        col = cols[int(h01(k, 3, seed) * len(cols))]
        dark = mix(col, SHADOW, 0.45)
        t.put(x, y + 1, GRASS2[2])
        t.put(x - 1, y + 1, GRASS2[3])
        if h01(k, 4, seed) < 0.7:
            t.put(x, y - 1, mix(col, SUN, 0.35))
            t.put(x - 1, y, col)
            t.put(x + 1, y, dark)
            t.put(x, y + 1, dark)
            t.put(x, y, GOLDR[2] if col != FLOWER[1] else FLOWER[4])
        else:
            t.put(x, y, col)
            t.put(x + 1, y, dark)
        _shadow_px(t, x + 1, y + 2, 70)
        _shadow_px(t, x + 2, y + 1, 50)
    return t


def d_clover(seed: int) -> Img:
    t = Img(T, T)
    for k in range(2 + int(h01(3, 1, seed) * 2)):
        x, y = 3 + int(h01(k, 2, seed) * 9), 3 + int(h01(k, 3, seed) * 9)
        for dx, dy, c in ((0, 0, 5), (1, 0, 4), (-1, 1, 4), (0, 1, 3), (1, 1, 3), (0, -1, 5)):
            if 1 <= x + dx < T - 1 and 1 <= y + dy < T - 1:
                t.put(x + dx, y + dy, GRASS2[c])
        _shadow_px(t, x + 2, y + 1, 60)
        _shadow_px(t, x + 1, y + 2, 70)
    return t


def d_stones(seed: int, n: int, ramp=ROCK2, big: bool = False) -> Img:
    """Pebbles or stones: lit on the north-west, dark on the south-east, each with its shadow."""
    t = Img(T, T)
    for k in range(n):
        w = (3 if big else 2) + int(h01(k, 1, seed) * (3 if big else 2))
        h = max(2, w - 1 - int(h01(k, 2, seed) * 2))
        x, y = 2 + int(h01(k, 3, seed) * (12 - w)), 2 + int(h01(k, 4, seed) * (12 - h))
        base = 3 + int(h01(k, 5, seed) * 2)
        for j in range(h):
            for i in range(w):
                if (i in (0, w - 1)) and (j in (0, h - 1)) and w > 2:
                    continue
                c = ramp[base]
                if i == 0 or j == 0:
                    c = ramp[min(6, base + 1)]
                if i == w - 1 or j == h - 1:
                    c = ramp[base - 1]
                if (i, j) == (1, 0) or (i, j) == (0, 1) and w > 3:
                    c = ramp[min(6, base + 2)]
                t.put(x + i, y + j, c)
        for i in range(1, w + 1):
            _shadow_px(t, x + i, y + h, 90)
        _shadow_px(t, x + w, y + h - 1, 60)
    return t


def d_leaves(seed: int, n: int = 3, cols=LEAFFALL) -> Img:
    """Fallen leaves: small slivers lying at an angle, lit edge up, each with a hint of shadow."""
    t = Img(T, T)
    for k in range(n):
        x, y = 2 + int(h01(k, 1, seed) * 11), 2 + int(h01(k, 2, seed) * 11)
        c = int(h01(k, 3, seed) * (len(cols) - 1))
        horiz = h01(k, 4, seed) < 0.5
        pts = [(0, 0), (1, 0), (2, 1)] if horiz else [(0, 0), (1, 1), (1, 2)]
        for m, (dx, dy) in enumerate(pts):
            t.put(x + dx, y + dy, cols[c + (1 if m == 0 else 0)])
        _shadow_px(t, x + pts[-1][0] + 1, y + pts[-1][1] + 1, 70)
        _shadow_px(t, x + 1, y + 2 if horiz else y + 3, 50)
    return t


def d_petals(seed: int) -> Img:
    t = Img(T, T)
    for k in range(5 + int(h01(4, 1, seed) * 4)):
        x, y = 1 + int(h01(k, 2, seed) * 14), 1 + int(h01(k, 3, seed) * 14)
        t.put(x, y, PETAL[int(h01(k, 4, seed) * 3)])
    return t


def d_crack(seed: int, ramp, n: int = 1) -> Img:
    """A fine crack: a dark hairline running across at a slant, stepping down now and then (never back up), its lower
    lip catching the light; with n = 2 a short branch leaves it."""
    t = Img(T, T)
    x, y = 2 + int(h01(0, 1, seed) * 4), 3 + int(h01(0, 2, seed) * 7)
    path = []
    for s in range(6 + int(h01(0, 3, seed) * 5)):
        if not (1 <= x < T - 1 and 1 <= y < T - 2):
            break
        path.append((x, y))
        x += 1
        if h01(s, 4, seed) < 0.4:
            y += 1
    if n > 1 and len(path) > 4:
        bx, by = path[len(path) // 2]
        for s in range(3):
            path.append((bx + s // 2, by + 1 + s))
    for (px, py) in path:
        t.put(px, py, ramp[1])
    for (px, py) in path:
        if t.get(px, py + 1)[3] == 0:
            t.put(px, py + 1, alpha(ramp[5], 140))
    return t


def d_moss(seed: int, ramp=MOSS2, n: int = 2) -> Img:
    """Moss cushions: small soft blobs, lit rim, darker core speckle."""
    t = Img(T, T)
    for k in range(n):
        rx, ry = 1.8 + h01(k, 1, seed) * 1.8, 1.4 + h01(k, 2, seed) * 1.2
        cx, cy = 3 + rx + h01(k, 3, seed) * (10 - 2 * rx), 3 + ry + h01(k, 4, seed) * (10 - 2 * ry)
        _blob(t, cx, cy, rx, ry, seed + k, lambda i, j: ramp[3] if h01(i, j, seed) > 0.25 else ramp[2], ramp[4], ramp[2],
              0.5, True)
    return t


def d_weed(seed: int) -> Img:
    """A weed pushing up through a joint or the path: a few short blades."""
    return d_tuft(seed + 900, GRASS2)


def d_puddle(seed: int) -> Img:
    """Standing water in a hollow of the marsh meadow: a dark far bank, the sky's glint on its near side, a lit lip
    of grass holding it, reed stubble."""
    t = Img(T, T)
    rx, ry = 4.5 + h01(5, 1, seed) * 2, 2.6 + h01(5, 2, seed) * 1.4
    cx, cy = 1.5 + rx + h01(5, 3, seed) * (13 - 2 * rx), 2 + ry + h01(5, 4, seed) * (11 - 2 * ry)
    pts = set()
    for j in range(1, T - 2):
        for i in range(1, T - 1):
            ang = math.atan2(j + 0.5 - cy, i + 0.5 - cx)
            if ((i + 0.5 - cx) / rx) ** 2 + ((j + 0.5 - cy) / ry) ** 2 <= 1.0 + 0.4 * (h01(int((ang + 3.2) * 2.5), 1, seed) - 0.5):
                pts.add((i, j))
    for (i, j) in pts:
        col = WATER2[4]
        if (i, j - 1) not in pts:
            col = WATER2[2]
        elif (i, j - 2) not in pts:
            col = WATER2[3]
        elif (i, j + 1) not in pts or (i, j + 2) not in pts:
            col = WATER2[5]
        if col == WATER2[4] and h01(i, j, seed + 3) < 0.15:
            col = WATER2[6]
        t.put(i, j, col)
    for (i, j) in pts:
        if (i, j + 1) not in pts:
            t.put(i, j + 1, GRASS2[5])
        if (i - 1, j) not in pts and t.get(i - 1, j)[3] == 0:
            t.put(i - 1, j, GRASS2[3])
    gl = sorted(pts)[len(pts) // 2]
    t.put(gl[0], gl[1], WATER2[7])
    for k in range(2):
        x, y = int(cx + (k * 2 - 1) * rx * 0.9), int(cy - ry)
        if 1 <= x < T - 1 and 2 <= y < T:
            t.put(x, y - 1, REED[4])
            t.put(x, y, REED[3])
    return t


def d_hole(seed: int, ramp=PAVE2) -> Img:
    """A missing flagstone: a hollow a stone wide, sunk under the paving (its north wall in shadow, the paving's lit lip
    along its south edge), soil in it and grass grown up through it."""
    t = Img(T, T)
    rx, ry = 4.5 + h01(7, 1, seed) * 1.5, 3.5 + h01(7, 2, seed) * 1.0
    cx, cy = 7.5 + (h01(7, 3, seed) - 0.5) * 2, 7.5 + (h01(7, 4, seed) - 0.5) * 2
    pts = set()
    for j in range(1, T - 1):
        for i in range(1, T - 1):
            ang = math.atan2(j + 0.5 - cy, i + 0.5 - cx)
            # a polygon, not an oval: the radius follows a few straight-ish facets
            lim = 1.0 + 0.25 * (h01(int((ang + 3.2) * 0.95), 2, seed) - 0.5)
            if ((i + 0.5 - cx) / rx) ** 2 + ((j + 0.5 - cy) / ry) ** 2 <= lim:
                pts.add((i, j))
    for (i, j) in pts:
        col = DIRT2[2] if h01(i, j, seed) > 0.25 else DIRT2[1]
        if (i, j - 1) not in pts or (i, j - 2) not in pts:
            col = mix(DIRT2[1], SHADOW, 0.45)
        elif (i - 1, j) not in pts:
            col = mix(DIRT2[2], SHADOW, 0.25)
        t.put(i, j, col)
    for (i, j) in sorted(pts):
        if (i, j - 1) not in pts or (i, j - 2) not in pts or (i - 1, j) not in pts:
            continue
        if h01(i, j, seed + 1) < 0.4:
            t.put(i, j, GRASS2[4] if h01(i, j, seed + 2) < 0.6 else GRASS2[5])
            if (i, j + 1) in pts:
                t.put(i, j + 1, GRASS2[3])
    for (i, j) in pts:
        if (i, j + 1) not in pts and t.get(i, j + 1)[3] == 0:
            t.put(i, j + 1, ramp[5])
        if (i + 1, j) not in pts and t.get(i + 1, j)[3] == 0:
            t.put(i + 1, j, ramp[5])
        if (i, j - 1) not in pts and t.get(i, j - 1)[3] == 0:
            t.put(i, j - 1, ramp[2])
    return t


def d_twig(seed: int) -> Img:
    t = Img(T, T)
    x, y = 3 + int(h01(6, 1, seed) * 6), 4 + int(h01(6, 2, seed) * 8)
    for s in range(6):
        t.put(x + s, y + (s // 3), WOOD2[3] if s % 2 else WOOD2[4])
        _shadow_px(t, x + s, y + (s // 3) + 1, 70)
    t.put(x + 3, y - 1, WOOD2[4])
    return t


def decals() -> dict:
    """The decal sets, {set: [Img]}, in a fixed order."""
    ramp_flowers = [[FLOWER[0], FLOWER[0], FLOWER[1]], [FLOWER[1]], [FLOWER[2], FLOWER[0]], [FLOWER[3]], [FLOWER[4], FLOWER[1]],
                    [FLOWER[2], FLOWER[3], FLOWER[0]]]
    return {
        "grass": [d_clump(10), d_clump(11), d_clump(12), d_clump(13), d_clump(15), d_clump(16), d_tuft(20), d_tuft(21),
                  d_tuft(22), d_tuft(23),
                  d_clover(30), d_clover(31), d_stones(40, 2), d_leaves(50, 2), d_leaves(51, 3),
                  d_flowers(60, [FLOWER[0]], 2), d_flowers(61, [FLOWER[1]], 1), d_petals(70), d_clump(14)],
        "flowers": [d_flowers(80 + k, cols, 3 + k % 2) for k, cols in enumerate(ramp_flowers)],
        "dirt": [d_stones(100, 1, ROCK2, True), d_stones(101, 2, ROCK2, True), d_stones(102, 3), d_stones(103, 4, DIRT2),
                 d_crack(104, DIRT2), d_crack(105, DIRT2, 2), d_leaves(106, 2), d_twig(107), d_weed(108), d_weed(109),
                 d_stones(110, 2, DIRT2)],
        "pave": [d_moss(120, MOSS2, 1), d_moss(121, MOSS2, 2), d_moss(122, MOSS2, 1), d_leaves(123, 2), d_leaves(124, 3),
                 d_petals(125), d_crack(126, PAVE2), d_crack(127, PAVE2, 2), d_weed(128), d_weed(129), d_stones(130, 2, PAVE2)],
        "pave_hole": [d_hole(131), d_hole(132)],
        "stone": [d_moss(140, MOSS2, 1), d_moss(141, MOSS2, 2), d_crack(142, STONE2), d_crack(143, STONE2, 2),
                  d_leaves(144, 2), d_weed(145)],
        "rock": [d_moss(160, MOSS2, 2), d_moss(161, MOSS2, 3), d_moss(162, MOSS2, 1), d_tuft(163), d_tuft(164),
                 d_stones(165, 2, ROCK2), d_crack(166, ROCK2), d_crack(167, ROCK2, 2), d_clump(168, MOSS2),
                 d_clump(169, MOSS2), d_moss(170, MOSS2, 3), d_tuft(171)],
        "marsh": [d_puddle(180), d_puddle(181), d_puddle(182), d_puddle(183), d_tuft(184), d_tuft(185), d_clump(186)],
        "wood": [d_leaves(200, 2), d_leaves(201, 1)],
        "roof": [d_moss(210, MOSS2, 1), d_moss(211, MOSS2, 2), d_leaves(212, 1)],
    }


# ============================================================================================================ dirt
def dirt_macro(seed: int = 201) -> Img:
    """A packed-earth path, 64 x 64: warm ochre with fine mottling at 2-4 px (no blob large enough to repeat),
    pebbles lit from the north-west, and a few fine cracks."""
    img = Img(P, P)
    for y in range(P):
        for x in range(P):
            n = fbm(x, y, seed, (8, 4, 2), (0.3, 0.4, 0.3))
            k = 4 if n > 0.62 else 3
            h = hp(x, y, seed + 1)
            if h < 0.06:
                k -= 1
            elif h > 0.965:
                k += 1
            img.put(x, y, DIRT2[k])
    for gy in range(8):
        for gx in range(8):
            if h01(gx, gy, seed + 2) < 0.45:
                continue
            x, y = gx * 8 + int(h01(gx, gy, seed + 3) * 7), gy * 8 + int(h01(gx, gy, seed + 4) * 7)
            big = h01(gx, gy, seed + 5) < 0.35
            img.put(x % P, y % P, DIRT2[5])
            if big:
                img.put((x + 1) % P, y % P, DIRT2[4])
                img.put(x % P, (y + 1) % P, DIRT2[4])
                img.put((x + 1) % P, (y + 1) % P, DIRT2[2])
                img.put((x + 2) % P, (y + 1) % P, DIRT2[1])
            else:
                img.put((x + 1) % P, (y + 1) % P, DIRT2[1])
    return img


# ========================================================================================================== paving
PAVE_P = 128   # the paving's pattern is 8 x 8 tiles: its flagstones are too distinct to repeat every 64 px


def paving_macro(seed: int = 301, ramp=PAVE2) -> Img:
    """Irregular town flagstones (the scholar-garden 'cracked ice' laying), 128 x 128: warm grey-beige polygons about a
    tile across (11-22 px), each with its own tone and a faint warmer or cooler cast, a lit north-west rim and a
    shaded south-east one (worn and rounded at the corners), a little grain, and now and then a crack; the joints
    crisp and dark, with moss and a blade or two of grass growing in some. (A missing stone is a decal, so it never
    repeats with the pattern.)"""
    S = PAVE_P
    vc = cells(seed, 8, 8, S, S, 0.8)
    img = Img(S, S)
    tint = {}
    for y in range(S):
        for x in range(S):
            i1, d1, i2, d2, d3, off = vc[y][x]
            if i1 not in tint:
                r = h01(i1, 0, seed + 3)
                tint[i1] = (3 if r < 0.07 else 5 if r > 0.74 else 4, h01(i1, 1, seed + 3))
            base, cast = tint[i1]
            e = d2 - d1
            e3 = d3 - d1
            f = faces_nw(off)
            if e < 1.0 or e3 < 1.5:
                col = mix(ramp[1], ramp[2], 0.5) if f > -0.2 else ramp[1]
                m = fbm(x, y, seed + 7, (16, 8), (0.6, 0.4), S, S)
                if m > 0.6 and hp(x, y, seed + 8, S, S) < 0.75:
                    col = MOSS2[3] if hp(x, y, seed + 9, S, S) < 0.55 else MOSS2[4] if hp(x, y, seed + 10, S, S) < 0.7 else GRASS2[5]
            else:
                k = base
                if e < 2.0 or e3 < 3.0:
                    # the stone's rim facing the joint: lit where it faces the north-west sun, shaded where it turns away
                    k = base + 1 if f > 0.25 else base - 1 if f < -0.25 else base
                col = ramp[_clamp(k, 1, 6)]
                if cast > 0.8:
                    col = mix(col, DIRT2[k if k < 6 else 5], 0.14)       # a warmer, sandier stone
                elif cast < 0.12:
                    col = mix(col, STONE2[_clamp(k, 1, 6)], 0.2)         # a cooler, bluer stone
                g = hp(x, y, seed + 11, S, S)
                if g < 0.05:
                    col = ramp[_clamp(k - 1, 1, 6)]
                elif g > 0.975:
                    col = ramp[_clamp(k + 1, 1, 6)]
            img.put(x, y, col)
    # A crack across a few stones.
    for n, site in enumerate((5, 23, 38, 51)):
        pts = [(x, y) for y in range(S) for x in range(S) if vc[y][x][0] == site and vc[y][x][3] - vc[y][x][1] > 2.5]
        if not pts:
            continue
        x, y = pts[len(pts) // 3]
        for st in range(8):
            if vc[y % S][x % S][0] != site or vc[y % S][x % S][3] - vc[y % S][x % S][1] < 2.0:
                break
            img.put(x % S, y % S, ramp[1])
            img.put(x % S, (y + 1) % S, ramp[5])
            x += 1
            y += 1 if h01(st, n, seed + 14) < 0.4 else 0
    return img


# ===================================================================================================== other tops
def stone_macro(seed: int = 401, ramp=STONE2) -> Img:
    """Dressed granite slabs (the promenade, terrace caps, stair landings), 64 x 64: big slabs a tile deep and 16-40 px
    long in staggered courses, pale and even (a floor, never mistaken for the coursed wall under it), a thin joint a
    step darker with its lower lip catching the light, a little grain, a worn corner or a chip now and then, moss in a
    few joints."""
    img = Img(P, P)
    for c in range(P // 16):
        x0 = int(h01(c, 0, seed) * 24)
        bounds = []
        x = x0
        while x < x0 + P:
            ln = min(16 + int(h01(x, c, seed + 1) * 24), x0 + P - x)
            if x0 + P - (x + ln) < 12:
                ln = x0 + P - x
            bounds.append((x, ln))
            x += ln
        for b, (bx, ln) in enumerate(bounds):
            r = h01(b, c, seed + 2)
            base = 5 if r > 0.8 else 4
            for dy in range(16):
                for dx in range(ln):
                    X, Y = (bx + dx) % P, c * 16 + dy
                    if dy == 15 or dx == ln - 1:
                        col = ramp[2]
                        if hp(X, Y, seed + 3) < 0.14:
                            col = MOSS2[3]
                    elif dy == 0 or dx == 0:
                        col = ramp[min(6, base + 1)]
                    elif dy == 14 or dx == ln - 2:
                        col = ramp[base - 1] if hp(X, Y, seed + 6) < 0.7 else ramp[base]
                    else:
                        g = hp(X, Y, seed + 4)
                        col = ramp[base] if g > 0.05 else ramp[base - 1]
                        if g > 0.985:
                            col = ramp[min(6, base + 1)]
                    if (dx in (0, 1, ln - 2)) and (dy in (0, 1, 14)) and h01(b, c, seed + 5) < 0.3:
                        col = ramp[base - 1]     # a worn corner
                    img.put(X, Y, col)
    return img


def rock_macro(seed: int = 501) -> Img:
    """The top of a karst cliff, 64 x 64: pale weathered limestone, an even warm grey with fine grain, soft lumps a
    step lighter on their sunny side, short hairline cracks (dark, their lower lip lit) and rain pits. Moss, tufts,
    pebbles and bigger cracks are decals, so the pattern itself never shows its period."""
    img = Img(P, P)
    for y in range(P):
        for x in range(P):
            n = fbm(x, y, seed, (8, 4, 2), (0.45, 0.35, 0.2))
            s = fbm(x + 1, y + 1, seed, (8, 4, 2), (0.45, 0.35, 0.2)) - fbm(x - 1, y - 1, seed, (8, 4, 2), (0.45, 0.35, 0.2))
            k = 4
            if s > 0.1 or n > 0.74:
                k = 5
            elif s < -0.12:
                k = 3
            g = hp(x, y, seed + 1)
            if g < 0.04:
                k -= 1
            elif g > 0.975:
                k = 6
            img.put(x, y, ROCK2[k])
    for n in range(9):
        x, y = int(h01(n, 1, seed + 2) * P), int(h01(n, 2, seed + 2) * P)
        for s in range(3 + int(h01(n, 3, seed + 2) * 4)):
            img.put((x + s) % P, y % P, ROCK2[2])
            img.put((x + s) % P, (y + 1) % P, ROCK2[5])
            if h01(s, n, seed + 3) < 0.35:
                y += 1
    for n in range(12):
        x, y = int(h01(n, 5, seed + 2) * P), int(h01(n, 6, seed + 2) * P)
        img.put(x, y, ROCK2[2])
        img.put((x + 1) % P, (y + 1) % P, ROCK2[5])
    return img


def wood_macro(seed: int = 601) -> Img:
    """Pier and floor planks running east-west, 4 px each, 64 x 64: a lit top edge, grain, planks 18-44 px long with
    staggered butt joints, nail heads at the joints, a dark gap under each."""
    img = Img(P, P)
    for p in range(P // 4):
        x0 = int(h01(p, 0, seed) * 30)
        x = x0
        joints = []
        while x < x0 + P:
            joints.append(x % P)
            x += 18 + int(h01(x, p, seed + 1) * 26)
        tint = [h01(k, p, seed + 2) for k in range(len(joints))]
        for dy in range(4):
            for X in range(P):
                Y = p * 4 + dy
                k = sum(1 for jx in joints if (X - jx) % P < (X - joints[0]) % P + 1) % len(joints)
                t = tint[k]
                base = 4 if t > 0.25 else 3
                if dy == 3:
                    col = WOOD2[1]
                elif dy == 0:
                    col = WOOD2[base + 1]
                else:
                    col = WOOD2[base] if hp(X // 3, Y, seed + 3) > 0.28 else WOOD2[base - 1]
                if X in joints and dy != 3:
                    col = WOOD2[1]
                if dy == 1 and any((X - jx) % P in (1, P - 2) for jx in joints):
                    col = WOOD2[0] if dy == 1 else col
                img.put(X, Y, col)
    return img


def roof_macro(seed: int = 701) -> Img:
    """Dark glazed roof tiles seen from above, 64 x 64: ribs of round cover tiles (4 px) running down the slope, each a
    small cylinder (a glaze highlight down its sunlit west flank, the crown, the shaded east flank) between channel
    tiles in shade; each course laps the next every 4 px with a shadow under the lap and a lit rim; a moss speck and
    a slightly paler tile here and there. An even plane, so it still reads as a floor (decision 29)."""
    img = Img(P, P)
    for y in range(P):
        row = y % 4
        for x in range(P):
            c4 = x % 4
            col = (ROOF2[5], ROOF2[4], ROOF2[3], ROOF2[1])[c4]
            if row == 3:
                col = (ROOF2[3], ROOF2[3], ROOF2[2], ROOF2[0])[c4]
            elif row == 0 and c4 < 3:
                col = (ROOF2[6], ROOF2[5], ROOF2[4])[c4]
            if hp(x // 4, y // 4, seed) < 0.07 and c4 < 3:
                col = mix(col, SUN, 0.12)
            if hp(x, y, seed + 1) < 0.012 and c4 < 3:
                col = MOSS2[3]
            img.put(x, y, col)
    return img


def wall_top_row(seed: int = 801) -> Img:
    """A courtyard wall's cap seen from above, 64 x 16: a ridge of tiles along the middle, cover tiles running off it
    to both sides in dark glaze."""
    img = Img(P, T)
    for j in range(T):
        for i in range(P):
            c4 = i % 4
            if j in (7, 8):
                col = ROOF2[5] if j == 7 else ROOF2[3]
                if c4 == 0:
                    col = ROOF2[2]
            else:
                col = (ROOF2[5], ROOF2[4], ROOF2[2], ROOF2[3])[c4]
                if j in (6, 9):
                    col = ROOF2[1]
                elif (j < 7 and j % 3 == 0) or (j > 8 and j % 3 == 2):
                    col = ROOF2[3] if c4 < 2 else ROOF2[2]
                if j == 0 or j == 15:
                    col = ROOF2[1]
            if hp(i, j, seed, P, T) < 0.02:
                col = MOSS2[3]
            img.put(i, j, col)
    return img


# =========================================================================================================== faces
# A face is the south side of a raised level, one tile row per level. Each material's face is a 64 x 48 pattern:
# the first row (its lip at the top) and two body rows that repeat downward; the texture is periodic in 32 rows, so
# the first row runs into the first body row and the body rows into each other.

FH = 32   # the face texture's vertical period


def _face_pattern(tex: Img) -> Img:
    """Lay a 64 x 32 face texture into the 64 x 48 face pattern (first row, body a, body b)."""
    out = Img(P, 48)
    for y in range(48):
        for x in range(P):
            out.put(x, y, tex.get(x, y % FH))
    return out


def face_tiles(pat: Img) -> tuple[list, list]:
    """(the first row's 4 tiles, the body's 8 tiles: body a then body b)."""
    return cut(Img.wrap(pat.img.crop((0, 0, P, T))), M, 1), cut(Img.wrap(pat.img.crop((0, T, P, 48))), M, 2)


def rock_face_tex(seed: int = 901) -> Img:
    """Karst rock mass, 64 x 32: rain-fluted columns 6-12 px wide whose fissures wander a pixel either way down the
    face, each shaded like a rough prism (a bright west edge catching the sun, a lit flank, the body, a shaded east
    flank); now and then a deep dark recess; a crack breaks a column into blocks whose tops are sunlit ledges (moss on
    some, dripping a few pixels); faint bedding lines run across the whole face; blocks jut out a step lighter or sit
    back a step darker."""
    tex = Img(P, FH)
    x0s = []
    x = 0
    while x < P:
        w = 6 + int(h01(x, 0, seed) * 7)
        if P - (x + w) < 6:
            w = P - x
        x0s.append(x)
        x += w
    n = len(x0s)
    brk = {c: int(h01(c, 1, seed + 1) * FH) if h01(c, 2, seed + 1) < 0.75 else -99 for c in range(n)}
    beds = [int(h01(0, k, seed + 11) * 6) + k * 14 for k in range(2)]
    for y in range(FH):
        bx = [x0s[c] + (0 if c == 0 else int(round((pn(c * 5, y, seed + 3, 8, P, FH) - 0.5) * 3))) for c in range(n)]
        for X in range(P):
            c = max(k for k in range(n) if bx[k] <= X)
            u = X - bx[c]
            w = (bx[c + 1] if c + 1 < n else P) - bx[c]
            b = brk[c]
            since = (y - b) % FH if b >= 0 else 99
            blk = 0 if b < 0 or y >= b else 1
            r = h01(c, blk, seed + 2)
            base = 2 if r > 0.7 else 1
            deep = h01(c, 7, seed + 4) < 0.12
            if u == 0:
                col = ROCK2[0]
            elif deep and u < w - 1:
                col = ROCK2[0] if u < w - 2 else ROCK2[1]
            elif since == 0:
                col = ROCK2[1] if u < w - 2 else ROCK2[0]
            elif since in (1, 2):
                col = ROCK2[min(6, base + 4 - since)] if u < w - 2 else ROCK2[base + 1]
                if since == 1 and fbm(X, y, seed + 5, (16, 8), (0.6, 0.4), P, FH) > 0.6:
                    col = MOSS2[4] if hp(X, y, seed + 6, P, FH) < 0.7 else MOSS2[5]
            else:
                k = base + (3 if u == 1 else 2 if u == 2 else 1 if u == 3 else -1 if u >= w - 2 else 0)
                if since == FH - 1 or (b >= 0 and (b - y) % FH == 1):
                    k -= 1
                if y in beds and hp(X, y, seed + 12, P, FH) < 0.7 and 1 < u < w - 2:
                    k -= 1
                if 3 < u < w - 2 and hp(X, y // 4, seed + 8, P, FH) < 0.12:
                    k -= 1
                col = ROCK2[_clamp(k, 0, 5)]
            tex.put(X, y, col)
    # moss drips under the mossy ledges
    for y in range(FH):
        for x in range(P):
            if tex.get(x, y) in (MOSS2[4], MOSS2[5]) and hp(x, y, seed + 9, P, FH) < 0.4:
                for d in range(1, 2 + int(hp(x, y, seed + 10, P, FH) * 3)):
                    if tex.get(x, (y + d) % FH) not in (MOSS2[4], MOSS2[5], ROCK2[0]):
                        tex.put(x, (y + d) % FH, MOSS2[2] if d > 1 else MOSS2[3])
    return tex


def earth_face_tex(seed: int = 911) -> Img:
    """A soil bank, 64 x 32: strata that wave a little, thin darker partings, stones set in it (lit north-west, a
    shadow under), a root now and then."""
    tex = Img(P, FH)
    for y in range(FH):
        for x in range(P):
            w = pn(x, y, seed, 16, P, FH) * 3 + pn(x, y, seed + 13, 8, P, FH) * 2
            band = int((y + w) // 5)
            k = 3 if band % 3 == 0 else 2
            if (y + w) % 5 < 0.9:
                k = 1
            g = hp(x, y, seed + 1, P, FH)
            if g < 0.08:
                k -= 1
            elif g > 0.95:
                k += 1
            tex.put(x, y, EARTH2[_clamp(k, 0, 5)])
    for gy in range(FH // 8):
        for gx in range(P // 16):
            if h01(gx, gy, seed + 2) < 0.45:
                continue
            rx, ry = 1.6 + h01(gx, gy, seed + 3) * 1.6, 1.2 + h01(gx, gy, seed + 4) * 0.9
            cx = gx * 16 + 3 + h01(gx, gy, seed + 5) * 10
            cy = gy * 8 + 2 + h01(gx, gy, seed + 6) * 4
            for j in range(-3, 4):
                for i in range(-4, 5):
                    dx, dy = (i + 0.5) / rx, (j + 0.5) / ry
                    d = dx * dx + dy * dy
                    X, Y = int(cx + i) % P, int(cy + j) % FH
                    if d <= 1.0:
                        c = ROCK2[4]
                        if dx + dy < -0.6:
                            c = ROCK2[5]
                        elif dx + dy > 0.7:
                            c = ROCK2[2]
                        tex.put(X, Y, c)
                    elif d <= 1.9 and dy > 0.3:
                        tex.put(X, Y, EARTH2[0])
    for n in range(3):
        x = int(h01(n, 7, seed) * P)
        y = int(h01(n, 8, seed) * FH)
        for s in range(5):
            tex.put((x + (s % 3 == 2)) % P, (y + s) % FH, EARTH2[1])
    return tex


def ashlar_tex(seed: int, ramp=STONE2, course: int = 8, wet: bool = False) -> Img:
    """Dressed stone courses, 64 x 32: blocks 10-26 px long, lit along the top and west, shaded at the foot and east,
    grain, a paler or darker block now and then, moss in a few joints (more near the foot)."""
    tex = Img(P, FH)
    for c in range(FH // course):
        x0 = int(h01(c, 0, seed) * 16)
        x = x0
        b = 0
        while x < x0 + P:
            ln = min(10 + int(h01(x, c, seed + 1) * 16), x0 + P - x)
            r = h01(b, c, seed + 2)
            base = 3 if r > 0.8 else 1 if r < 0.15 else 2
            for dy in range(course):
                for dx in range(ln):
                    X, Y = (x + dx) % P, c * course + dy
                    if dy == course - 1 or dx == ln - 1:
                        col = ramp[0]
                        if hp(X, Y, seed + 3, P, FH) < (0.3 if c == FH // course - 1 else 0.12):
                            col = MOSS2[2]
                    elif dy == 0:
                        col = ramp[min(6, base + 2)] if dx < ln - 2 else ramp[base + 1]
                    elif dx == 0:
                        col = ramp[base + 1]
                    elif dy == course - 2 or dx == ln - 2:
                        col = ramp[base - 1]
                    else:
                        col = ramp[base] if hp(X, Y, seed + 4, P, FH) > 0.08 else ramp[base - 1]
                    tex.put(X, Y, col)
            x += ln
            b += 1
    if wet:
        for y in range(FH):
            for x in range(P):
                k = max(0.0, (y % T - 2) / 13.0)
                tex.blend(x, y, WATER2[1], int(90 * k))
    return tex


def _drip(img: Img, top: list, drape: list, seed: int, depth: int = 5, vines: bool = True, rows: int = 2,
          bare: float = 0.0) -> None:
    """The lip over a face's first row: the top's lit rim and front edge (`rows` px, the rim at the top's brightest
    step), then grass or moss (`drape`) overhanging the edge by 1-`depth` px in soft clumps (its crown lit, its
    underside in shade) with blade tips hanging from it, a few vines with leaves, and the contact shadow under it all.
    `bare`: the share of the edge where the rock shows with no drape."""
    hang = []
    for x in range(P):
        n = fbm(x, 0, seed, (16, 8, 4), (0.5, 0.3, 0.2), P, 16)
        n = min(1.0, max(0.0, (n - 0.28) / 0.44))
        d = 0 if n < bare else 1 + int((n - bare) / max(0.01, 1.0 - bare) * depth)
        hang.append(min(depth + 1, d))
    for x in range(P):
        rim = mix(top[6] if len(top) > 6 else top[-1], SUN, 0.35)
        img.put(x, 0, rim if hp(x, 0, seed + 5, P, 16) > 0.18 else top[6])
        for r in range(1, rows):
            img.put(x, r, top[5] if r == 1 else top[4])
        d = hang[x]
        for r in range(d):
            y = rows + r
            c = drape[5] if r == 0 else drape[4] if r < d - 2 else drape[3] if r < d - 1 else drape[2]
            if hang[(x - 1) % P] < r + 1 and r > 0:
                c = drape[4]              # the lit west side of a hanging clump
            elif hang[(x + 1) % P] < r + 1 and r > 0:
                c = drape[2]              # its shaded east side
            img.put(x, y, c)
        tip = d
        if d > 0 and hp(x, 2, seed + 2, P, 16) < 0.3:
            img.put(x, rows + d, drape[2])
            tip = d + 1
        y = rows + tip
        img.blend(x, y, SHADOW, 160)
        img.blend(x, y + 1, SHADOW, 90)
        img.blend(x, y + 2, SHADOW, 35)
        img.blend((x + 1) % P, y, SHADOW, 40)
    if vines:
        for x in range(P):
            if hp(x, 3, seed + 3, P, 16) > 0.045 or hang[x] < 3:
                continue
            ln = 7 + int(hp(x, 4, seed + 3, P, 16) * 6)
            y0 = rows + hang[x]
            for s in range(min(ln, T - y0 - 1)):
                vx = (x + (1 if (s // 5) % 2 else 0)) % P
                img.put(vx, y0 + s, drape[3] if s % 2 else drape[2])
                if s % 3 == 1:
                    lx = (vx - 1) % P if (s // 3) % 2 else (vx + 1) % P
                    img.put(lx, y0 + s, drape[5] if (s // 3) % 2 else drape[4])
                img.blend((vx + 1) % P, y0 + s + 1, SHADOW, 80)


def rock_faces(seed: int = 901) -> tuple[list, list]:
    pat = _face_pattern(rock_face_tex(seed))
    _drip(pat, ROCK2, MOSS2, seed + 50, 6, True, 2, 0.12)
    return face_tiles(pat)


def earth_faces(seed: int = 911) -> tuple[list, list]:
    pat = _face_pattern(earth_face_tex(seed))
    _drip(pat, GRASS2, GRASS2, seed + 50, 6, True)
    # roots hanging from under the grass
    for x in range(P):
        if hp(x, 5, seed + 60, P, 16) < 0.06:
            for s in range(3 + int(hp(x, 6, seed + 60, P, 16) * 5)):
                pat.put((x + (s % 4 == 3)) % P, 7 + s, EARTH2[1])
    return face_tiles(pat)


def stone_faces(seed: int = 921, top=STONE2) -> tuple[list, list]:
    """A dressed retaining wall: ashlar under a coping stone (the top's rim, the coping's lit upper face and its front,
    a dark line where the coping overhangs), moss specks on the coping."""
    pat = _face_pattern(ashlar_tex(seed, STONE2))
    for x in range(P):
        pat.put(x, 0, mix(top[6], SUN, 0.3))
        pat.put(x, 1, top[5])
        pat.put(x, 2, STONE2[4] if hp(x, 0, seed + 1, P, 16) > 0.1 else STONE2[3])
        pat.put(x, 3, STONE2[3])
        pat.put(x, 4, STONE2[0])
        pat.blend(x, 5, SHADOW, 110)
        pat.blend(x, 6, SHADOW, 50)
        if hp(x, 2, seed + 2, P, 16) < 0.08:
            pat.put(x, 2, MOSS2[4])
            pat.put(x, 3, MOSS2[3])
        if x % 21 == 0:
            pat.put(x, 2, STONE2[1])
            pat.put(x, 3, STONE2[1])
    return face_tiles(pat)


def bank_faces(seed: int = 931) -> tuple[list, list]:
    """The river embankment over water (the room view shows its top 8 px): a granite curb, a course of wet dark blocks,
    and algae at the waterline."""
    pat = _face_pattern(ashlar_tex(seed, STONE2, 8, True))
    for x in range(P):
        pat.put(x, 0, STONE2[6])
        pat.put(x, 1, STONE2[5])
        pat.put(x, 2, STONE2[3])
        pat.put(x, 3, STONE2[0])
        a = hp(x, 6, seed + 1, P, 16)
        pat.put(x, 6, MOSS2[2] if a < 0.5 else MOSS2[1])
        pat.put(x, 7, MOSS2[1] if a < 0.3 else WATER2[1])
    return face_tiles(pat)


def wood_faces(seed: int = 941) -> tuple[list, list]:
    """A pier's side over the water: the deck's lit edge and the plank ends under it, a dark beam, then pilings (lit
    west, shaded east) with a cross brace, in the dark water of the pier's shadow; the waterline ripples round them."""
    pat = Img(P, 48)
    for y in range(48):
        for x in range(P):
            pat.put(x, y, WATER2[1] if (y % 16) < 6 else WATER2[2])
    for y in range(48):
        for px0 in range(2, P, 16):
            for k, c in enumerate((WOOD2[4], WOOD2[3], WOOD2[2], WOOD2[1])):
                pat.put(px0 + k, y, c)
            if px0 % 32 == 2:
                pat.put(px0 + 9, y, WOOD2[3])
                pat.put(px0 + 10, y, WOOD2[2])
    for x in range(P):
        for y in (6, 22, 38):
            pat.put(x, y, WOOD2[2] if x % 7 else WOOD2[1])
    for x in range(P):
        pat.put(x, 0, WOOD2[6])
        pat.put(x, 1, WOOD2[4] if x % 5 else WOOD2[1])
        pat.put(x, 2, WOOD2[3] if x % 5 else WOOD2[1])
        pat.put(x, 3, WOOD2[1])
        pat.put(x, 4, WATER2[0])
        pat.blend(x, 5, SHADOW, 60)
        if (x % 16) in (1, 6):
            pat.put(x, 7, WATER2[4])
    return face_tiles(pat)


def wall_faces(seed: int = 951) -> tuple[list, list]:
    """A whitewashed courtyard wall: on the first row the dark glazed cap (its lit verge, round tile ends with a glaze
    glint, a dark drip line), the cap's shadow on the plaster; below, lime plaster with faint streaks and a damp
    foot."""
    tex = Img(P, FH)
    for y in range(FH):
        for x in range(P):
            col = PLASTER2[4] if hp(x // 3, y // 6, seed, P, FH) > 0.22 else PLASTER2[3]
            if hp(x, 0, seed + 5, P, 1) < 0.12 and (y % 16) > 5:
                col = PLASTER2[3]
            if (y % 16) >= 13:
                col = PLASTER2[2] if (y % 16) == 13 else PLASTER2[1]
            tex.put(x, y, col)
    pat = _face_pattern(tex)
    for x in range(P):
        c4 = x % 4
        pat.put(x, 0, ROOF2[6])
        pat.put(x, 1, (ROOF2[5], ROOF2[6], ROOF2[4], ROOF2[1])[c4])
        pat.put(x, 2, (ROOF2[4], ROOF2[4], ROOF2[3], ROOF2[1])[c4])
        pat.put(x, 3, ROOF2[1] if c4 != 3 else ROOF2[0])
        pat.put(x, 4, ROOF2[0])
        for r, a in enumerate((140, 95, 55, 25)):
            pat.blend(x, 5 + r, SHADOW, a)
    return face_tiles(pat)


def eave_face(seed: int = 961) -> Img:
    """The front of a tiled roof, the first face row under a roof top: the lit verge, round tile ends every 4 px in
    dark glaze (a glint on each), drip tiles between, the dark under-eave, then the white wall in the eave's deep
    shadow and a timber rail."""
    t = Img(T, T)
    for i in range(T):
        c4 = i % 4
        t.put(i, 0, ROOF2[6])
        t.put(i, 1, ROOF2[4])
        t.put(i, 2, (ROOF2[4], ROOF2[6], ROOF2[3], ROOF2[1])[c4])
        t.put(i, 3, (ROOF2[3], ROOF2[4], ROOF2[2], ROOF2[1])[c4])
        t.put(i, 4, (ROOF2[2], ROOF2[2], ROOF2[1], ROOF2[0])[c4])
        t.put(i, 5, ROOF2[0])
    for j in range(6, T):
        for i in range(T):
            col = PLASTER2[3] if j < 12 else PLASTER2[4]
            t.put(i, j, col)
        for i in range(T):
            a = (170, 130, 95, 60, 30, 0, 0, 0, 0, 0)[j - 6]
            if a:
                t.blend(i, j, SHADOW, a)
    for j in range(6, T):
        t.put(0, j, TIMBER2[2])
        t.put(1, j, TIMBER2[3])
        t.blend(0, j, SHADOW, 60 if j < 10 else 0)
    t.hline(0, 12, T, TIMBER2[2])
    t.hline(0, 13, T, TIMBER2[1])
    return t


def plaster_face(seed: int, kind: str = "plain", plinth: bool = True) -> Img:
    """A whitewashed wall panel in a dark timber frame (plain), with a lattice window glowing warm (window), or a red
    lacquer door with gold studs (door); a granite plinth at the foot."""
    t = Img(T, T)
    for j in range(T):
        for i in range(T):
            col = PLASTER2[4] if h01(i // 2, j // 3, seed) > 0.18 else PLASTER2[3]
            if plinth and j >= 13:
                col = STONE2[4] if j == 13 else STONE2[2] if j == 14 else STONE2[1]
            t.put(i, j, col)
    for j in range(13 if plinth else T):
        t.put(0, j, TIMBER2[2])
        t.put(1, j, TIMBER2[4])
        t.put(2, j, PLASTER2[2])
    if plinth:
        t.hline(0, 13, T, STONE2[5])
    if kind == "window":
        t.rect(4, 2, 9, 8, TIMBER2[1])
        t.hline(4, 2, 9, TIMBER2[3])
        for j in range(3, 9):
            for i in range(5, 12):
                if (i + j) % 3:
                    t.put(i, j, PGOLD if j < 5 else GOLDR[2] if j < 7 else GOLDR[1])
        t.hline(4, 10, 9, PLASTER2[1])
        t.hline(5, 11, 8, PLASTER2[2])
    elif kind == "door":
        t.rect(2, 1, 13, 12, RED2[1])
        for x0 in (3, 9):
            t.rect(x0, 2, 5, 11, RED2[3])
            t.vline(x0, 2, 11, RED2[4])
            t.vline(x0 + 4, 2, 11, RED2[2])
            t.put(x0 + 3, 6, GOLDR[3])
            t.put(x0 + 3, 9, GOLDR[3])
        t.vline(8, 2, 11, RED2[0])
        t.hline(2, 13, 13, STONE2[5])
    return t


# ========================================================================================================== stairs
def stairs() -> Img:
    """Two granite steps (the room view draws the top 8 px, one step, per 8 px of rise): the nosing lit bright, the
    tread worn a little paler in the middle, the dark shadow under the nosing, the riser with a bounce of light at
    its foot."""
    t = Img(T, T)
    for s in range(2):
        y = s * 8
        for i in range(T):
            worn = 4 <= i <= 11
            t.put(i, y, STONE2[6])
            t.put(i, y + 1, STONE2[5] if not worn else mix(STONE2[5], SUN, 0.1))
            t.put(i, y + 2, STONE2[5] if h01(i, y, 3) > 0.12 else STONE2[4])
            t.put(i, y + 3, STONE2[4])
            t.put(i, y + 4, STONE2[1])
            t.put(i, y + 5, STONE2[2])
            t.put(i, y + 6, STONE2[2] if h01(i, y, 4) > 0.2 else STONE2[3])
            t.put(i, y + 7, STONE2[3])
        for i in (0, 15):
            if h01(i, y, 5) < 0.7:
                t.put(i, y + 2, MOSS2[3])
    return t


# =========================================================================================================== water
def water_macro(frame: int, seed: int = 1001) -> Img:
    """The Jade River's body, one of four frames (250 ms), 64 x 64: a calm jade body (its depth is the room's tint over
    it) and ripples: short lit crests, each with the shadow of its trough under it, on a jittered grid, each
    swelling, peaking with a pale glint, drifting a pixel east and fading in turn (a quarter-cycle apart), and a few
    glints that twinkle a frame at a time. No crest repeats the frame before, so the surface drifts, never pulses."""
    img = Img(P, P, WATER2[3])
    for y in range(P):
        for x in range(P):
            if hp(x, y, seed + 1) < 0.012:
                img.put(x, y, WATER2[2])
    for gy in range(P // 8):
        for gx in range(P // 16):
            if h01(gx, gy, seed + 3) < 0.15:
                continue
            x0 = gx * 16 + int(h01(gx, gy, seed + 4) * 12)
            y0 = gy * 8 + int(h01(gx, gy, seed + 5) * 6)
            ln = 3 + int(h01(gx, gy, seed + 6) * 4)
            ph = (frame + int(h01(gx, gy, seed + 7) * 4)) % 4
            if ph == 3:
                continue
            n, dx = {0: (ln - 2, 0), 1: (ln, 0), 2: (ln - 1, 1)}[ph]
            for k in range(max(1, n)):
                X = (x0 + dx + k) % P
                col = WATER2[4]
                if ph == 1 and k == n // 2:
                    col = WATER2[6]
                elif ph == 1:
                    col = WATER2[5] if 0 < k < n - 1 else WATER2[4]
                img.put(X, y0 % P, col)
                if 0 < k < n:
                    img.put(X, (y0 + 1) % P, WATER2[2])
    for n in range(6):
        x = int(h01(n, frame, seed + 8) * P)
        y = int(h01(n, frame + 9, seed + 8) * P)
        img.put(x, y, WATER2[7])
        img.put((x + 1) % P, y, WATER2[5])
    return img


def shore_fx(sides: int, frame: int, seed: int = 1101) -> Img:
    """The shore of a water cell with land on `sides` (bit 1 N, 2 E, 4 S, 8 W), one of four frames, as an overlay:
    - the waterline sits where each side shows on screen: under the bank face (row 0), on the land's top edge to the
      south (row 7, as the water is drawn 8 px low) and on the tile's edge to either side;
    - land to the north or west stands between the water and the sun: its shadow lies on the water;
    - to the south and east the shallows are sunlit and show the bed, fading into the jade;
    - foam breathes at the waterline and a ripple leaves the shore, a pixel further each frame."""
    t = Img(T, T)
    breathe = (0, 1, 1, 0)[frame]
    ripple = (0, 2, 3, 4)[frame]

    def over(x: int, y: int, col, a: int) -> None:
        if not (0 <= x < T and 0 <= y < T):
            return
        cur = t.get(x, y)
        if cur[3] == 0:
            t.put(x, y, alpha(col, a))
        elif a >= cur[3]:
            t.put(x, y, alpha(col, a))

    # distance to each land side's waterline, per pixel
    lines = []
    if sides & 1:
        lines.append(("n", lambda i, j: j))
    if sides & 4:
        lines.append(("s", lambda i, j: 7 - j))
    if sides & 8:
        lines.append(("w", lambda i, j: i))
    if sides & 2:
        lines.append(("e", lambda i, j: 15 - i))
    for j in range(T):
        for i in range(T):
            if sides & 4 and j > 7:
                t.put(i, j, BED2[3] if hp(i, j, seed, T, T) > 0.2 else BED2[2])
                continue
            for side, dist in lines:
                d = dist(i, j)
                if d < 0:
                    continue
                if side in ("n", "w"):
                    a = (120, 90, 60, 30, 12)[d] if d < 5 else 0
                    if a:
                        over(i, j, SHADOW, a)
                else:
                    if d < 6:
                        bed = BED2[3] if hp(i + 3 * frame * 0, j, seed + 1, T, T) > 0.25 else BED2[2]
                        if hp(i, j, seed + 2, T, T) > 0.9:
                            bed = BED2[4]
                        over(i, j, mix(bed, WATER2[4], (d / 6.0) * 0.5), (230, 200, 160, 110, 70, 35)[d])
    for side, dist in lines:
        for j in range(T):
            for i in range(T):
                if sides & 4 and j > 7:
                    continue
                d = dist(i, j)
                if d == 0:
                    if hp(i, j, seed + 3 + frame, T, T) > 0.45:
                        t.put(i, j, FOAM2)
                    else:
                        t.put(i, j, alpha(WATER2[6], 230))
                elif d == 1:
                    if (breathe and hp(i, j, seed + 4, T, T) > 0.55) or hp(i, j, seed + 5 + frame, T, T) > 0.85:
                        t.put(i, j, alpha(FOAM2, 170))
                elif ripple and d == ripple + 1:
                    if hp(i, j, seed + 6, T, T) > 0.35:
                        over(i, j, WATER2[6], (0, 150, 110, 60)[frame])
    return t


def inner_corner(corner: str, frame: int, seed: int = 1201) -> Img:
    """Foam and a patch of shallows where land touches a water cell only at a corner (ne, nw, se, sw)."""
    t = Img(T, T)
    cx, cy = {"ne": (15.5, 0.0), "nw": (0.0, 0.0), "se": (15.5, 7.5), "sw": (0.0, 7.5)}[corner]
    for j in range(T):
        for i in range(T):
            d = math.hypot(i + 0.5 - cx, (j + 0.5 - cy) * 1.2)
            if d < 1.6:
                t.put(i, j, FOAM2 if hp(i, j, seed + frame, T, T) > 0.3 else WATER2[6])
            elif d < 2.8 and ((frame in (1, 2) and hp(i, j, seed + 1, T, T) > 0.4) or hp(i, j, seed + 2 + frame, T, T) > 0.85):
                t.put(i, j, alpha(FOAM2, 190))
            elif d < 4.2 and corner[0] == "s":
                t.put(i, j, alpha(mix(BED2[3], WATER2[4], 0.4), 120))
            elif d < 4.2:
                t.put(i, j, alpha(SHADOW, 60))
    return t


def post_ripple(frame: int) -> Img:
    """Rings spreading from a pier's two pilings where they stand in the water (under the pier's face)."""
    t = Img(T, T)
    r = 1.5 + frame * 1.1
    a = (230, 190, 140, 80)[frame]
    for cx in (3.5, 11.5):
        for j in range(0, 6):
            for i in range(T):
                d = math.hypot((i + 0.5 - cx) / 1.0, (j + 0.2) * 2.0)
                if abs(d - r) < 0.6:
                    t.put(i, j, alpha(FOAM2 if frame < 2 else WATER2[6], a))
    return t


# ======================================================================================================== overlays
def overlay(kind: str) -> Img:
    """Translucent light tiles the room view lays over tops, faces and stairs (art bible §5 and "Terrain v2"), in the
    sun's warm light and the shadow's blue-violet:
    rim_w / rim_e / rim_n: the edge of a top whose west / east / north neighbour is lower (lit, shaded, the drop);
    ao_n: ambient occlusion on the floor at the foot of a face; face_ao: the same at the bottom of the face itself;
    shade_w: the shadow a higher west neighbour casts on this floor (light from the north-west);
    end_w / end_e: a face's end where it turns a corner, lit at the west end and shaded at the east;
    cheek_w / cheek_e: the cheeks of a flight of stairs, lit on the west and shaded on the east."""
    t = Img(T, T)
    if kind in ("end_w", "end_e", "cheek_w", "cheek_e"):
        cols = {"end_w": ((0, SUN, 110), (1, SUN, 40)), "end_e": ((15, SHADOW, 150), (14, SHADOW, 70), (13, SHADOW, 25)),
                "cheek_w": ((0, SUN, 130), (1, SUN, 50)), "cheek_e": ((15, SHADOW, 170), (14, SHADOW, 90), (13, SHADOW, 35))}[kind]
        for x, col, a in cols:
            for j in range(T):
                t.put(x, j, alpha(col, a))
        return t
    if kind == "rim_w":
        for j in range(T):
            t.put(0, j, alpha(SUN, 170))
            t.put(1, j, alpha(SUN, 60))
    elif kind == "rim_e":
        for j in range(T):
            t.put(15, j, alpha(SHADOW, 150))
            t.put(14, j, alpha(SHADOW, 70))
            t.put(13, j, alpha(SHADOW, 25))
    elif kind == "rim_n":
        for i in range(T):
            t.put(i, 0, alpha(SHADOW, 160))
            t.put(i, 1, alpha(SUN, 90))
    elif kind == "ao_n":
        for i in range(T):
            for r, a in enumerate(AO_STEPS + (12,)):
                t.put(i, r, alpha(SHADOW, a))
    elif kind == "face_ao":
        for i in range(T):
            for r, a in enumerate(AO_STEPS):
                t.put(i, T - 1 - r, alpha(SHADOW, a))
    elif kind == "shade_w":
        for j in range(T):
            for c, a in enumerate((116, 100, 84, 64, 42, 20)):
                t.put(c, j, alpha(SHADOW, a))
    return t
