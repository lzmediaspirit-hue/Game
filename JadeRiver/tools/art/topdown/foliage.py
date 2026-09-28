"""Terrain v2, third part (decision 40; docs/redesign/art_bible.md "Terrain v2", "Foliage and decor"): the foliage
and garden kit, drawn at art resolution, lit from the north-west, outlined as every prop (art bible §4).

Big trees come in two sprites. The **trunk** (the prop's own `rect`: the bole and its main limbs, narrow) sorts with the
room at its footprint's south edge and blocks, as every solid prop. The **canopy** (`CANOPY`: the leaves and the outer
branches) is an overhang: the room view draws it just after its trunk, so it covers whoever walks under it and never a
roof or a body in front of it, and fades it out while the player (or a foe) is under it. A canopy never blocks. Its
floor shadow is the canopy's shade: the crown's clumps cast on the ground along the sun's direction (+0.45 h, +0.20 h),
lumpy and dappled, in the world's one `SHADOW` (0.41 in the body, 0.25 at the rim and in the sun flecks).

Everything else is one sprite: bushes, hedges, fences, rocks, a fallen log, stumps, a wayside shrine and potted plants
(solid), and the walk-through plants (tall grass, cattails, ferns, lotus pads). Plants that stir (the willow's strands,
the bamboo's sprays, tall grass, cattails) hold four frames; the room view plays each from its own phase.

Leaf masses are sculpted, not painted: a crown is a set of clumps (ellipsoids) drawn back to front, each pixel lit by
its clump's normal against the sun, broken into small leaves (a jittered cell pattern, each leaf a step lighter or
darker and lit on its own north-west side), with a dark crease where a nearer clump overlaps one behind it and a lit
lip along a nearer clump's top. Nothing here uses a random generator: every value comes from a coordinate hash.
"""
from __future__ import annotations

import math

import terrain2 as T2
from canvas import Img, h01
from palette import (BAMBOO, BARK, BRONZER, DARKWOOD, GOLDR, JADE, BJADE, LANTERN, LEAF, LOTUS, MIST, MOSS, PAD, PINE,
                     REED, RED, ROCK, ROOF, STONE, WATER, WOOD, alpha, c, ramp)

SHADOW = T2.SHADOW
SUN = T2.SUN

# Blossom and autumn ramps for the flowering and turning trees, dark -> light, the dark ends leaning blue-violet and
# the light ends warm (the Terrain v2 hue rule).
PLUM = ramp("4A2A4E", "7E4A74", "B0628A", "D88AAE", "F0B8CE", "FBE0EA", "FFF6F8")     # plum blossom: white-pink
PEACH = ramp("4E1E40", "86305E", "C04C7C", "E47A9C", "F6A8BC", "FFD0DA", "FFF0F2")    # peach blossom: pink
MAPLE = ramp("3A1024", "6A1A26", "9C2A26", "C8452A", "E0703A", "F2A04E", "FFD27A")    # a maple turning
AZALEA = ramp("5A1030", "962040", "C8384E", "E8606A", "F89A90")
BOX = ramp("0A2426", "123A30", "1C5238", "2B6C3E", "448A48", "6CAA58", "A0CC7A")      # clipped box hedge
LIGHT = (-0.52, -0.66, 0.54)                                                          # the sun, NW and high


def _norm(v):
    n = math.sqrt(sum(a * a for a in v))
    return tuple(a / n for a in v)


LIGHT = _norm(LIGHT)


def mixc(a: tuple, b: tuple, k: float) -> tuple:
    return tuple(round(a[i] + (b[i] - a[i]) * k) for i in range(3)) + (a[3] if len(a) > 3 else 255,)


# ============================================================================================================ leaves
def leaf_mass(s: Img, clumps: list, rmp: list, seed: int, leaf: float = 4.0, wob: float = 0.3, grain: str = "leaf",
              flat: float = 0.0, lo: int = 1, hi: int = 5, bias: float = 0.0, spec: bool = True, dx: int = 0,
              whole: float = 0.45) -> dict:
    """Clumps [(cx, cy, rx, ry)] drawn back (smallest cy) to front. Each pixel is lit by a blend of its clump's normal
    and the whole mass's (`whole`: the crown reads as one lit form, its clumps as the bumps on it), darkened toward the
    mass's underside, and broken into leaves: `grain` "leaf" is a jittered cell pattern of small scales, each lit on
    its north-west crescent with a dark gap along its south-east edge; "needle" short horizontal strokes. Quantised to
    ramp steps lo..hi, the ramp's next step for sparse glints. `flat` flattens the normal (a pine's pads), `bias`
    brightens, `dx` shifts the whole mass (a sway frame). Returns {(x, y): step} of what it drew."""
    W, H = s.w, s.h
    owner: dict = {}
    lam: dict = {}
    order = sorted(range(len(clumps)), key=lambda i: (clumps[i][1], clumps[i][0]))
    # The whole mass as one ellipse, for the form's light.
    gx0 = min(c[0] - c[2] for c in clumps) + dx
    gx1 = max(c[0] + c[2] for c in clumps) + dx
    gy0 = min(c[1] - c[3] for c in clumps)
    gy1 = max(c[1] + c[3] for c in clumps)
    gcx, gcy, grx, gry = (gx0 + gx1) / 2, (gy0 + gy1) / 2, max(1.0, (gx1 - gx0) / 2), max(1.0, (gy1 - gy0) / 2)
    for rank, i in enumerate(order):
        cx, cy, rx, ry = clumps[i][:4]
        cx += dx
        for y in range(int(cy - ry - 3), int(cy + ry + 4)):
            for x in range(int(cx - rx - 3), int(cx + rx + 4)):
                if not (0 <= x < W and 0 <= y < H):
                    continue
                u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
                d = math.hypot(u, v)
                ang = math.atan2(v, u)
                nb = max(5, int(rx * 0.9))
                a = (ang + math.pi) / (2 * math.pi) * nb
                k0 = int(a)
                t = a - k0
                bump = (h01(k0 % nb, i, seed) * (1 - t) + h01((k0 + 1) % nb, i, seed) * t) - 0.5
                if d > 1.0 + wob * bump:
                    continue
                nz = math.sqrt(max(0.0, 1.0 - min(1.0, d * d)))
                n = _norm((u * (1 - flat), v * (1 - flat), max(nz + flat, 0.05)))
                gu, gv = (x + 0.5 - gcx) / grx, (y + 0.5 - gcy) / gry
                gd = min(1.0, gu * gu + gv * gv)
                g = _norm((gu, gv, max(0.05, math.sqrt(1.0 - gd))))
                lc = n[0] * LIGHT[0] + n[1] * LIGHT[1] + n[2] * LIGHT[2]
                lg = g[0] * LIGHT[0] + g[1] * LIGHT[1] + g[2] * LIGHT[2]
                owner[(x, y)] = rank
                lam[(x, y)] = lc * (1 - whole) + lg * whole
    if not owner:
        return {}
    steps: dict = {}
    y0 = min(p[1] for p in owner)
    hgt = max(1, max(p[1] for p in owner) - y0)
    for (x, y), r in owner.items():
        if grain == "needle":
            q = x - dx + (y * 2) % 3
            off = (h01(q // 3, y // 2, seed + 7) - 0.5) * 0.3
            edge = 0.12 if q % 3 == 0 else (-0.1 if q % 3 == 2 else 0.0)
        else:
            d1, d2, bx, by, best = 99.0, 99.0, 0.0, 0.0, (0, 0)
            cx0, cy0 = int((x - dx) / leaf), int(y / leaf)
            for j in (cy0 - 1, cy0, cy0 + 1):
                for i in (cx0 - 1, cx0, cx0 + 1):
                    sx = (i + 0.15 + 0.7 * h01(i, j, seed + 3)) * leaf
                    sy = (j + 0.15 + 0.7 * h01(i, j, seed + 4)) * leaf
                    dd = math.sqrt((x - dx + 0.5 - sx) ** 2 + ((y + 0.5 - sy) * 1.25) ** 2)
                    if dd < d1:
                        d2 = d1
                        d1, best, bx, by = dd, (i, j), sx, sy
                    elif dd < d2:
                        d2 = dd
            off = (h01(best[0], best[1], seed + 5) - 0.5) * 0.16
            ux, uy = (x - dx + 0.5 - bx) / leaf, (y + 0.5 - by) / leaf
            edge = -(ux * 0.9 + uy * 1.1) * 0.5                       # the scale's lit north-west crescent
            if d2 - d1 < 0.9 and ux + uy > -0.1:
                edge -= 0.22                                           # the dark gap along its south-east edge
        ao = 0.28 * min(1.0, max(0.0, (y - y0) / hgt)) ** 1.5          # the crown's underside lies in its own shade
        val = 0.44 + 0.6 * (lam[(x, y)] - 0.3) + off + edge + bias - ao
        k = lo + int(max(0.0, min(0.999, val)) * (hi - lo + 1))
        steps[(x, y)] = max(lo, min(hi, k))
    # A dark crease where a nearer clump overlaps one behind it; a lit lip along a nearer clump's top; the shaded rim.
    out = dict(steps)
    for (x, y), r in owner.items():
        below = owner.get((x, y + 1))
        above = owner.get((x, y - 1))
        if below is not None and below > r and lam[(x, y + 1)] > -0.2:
            out[(x, y)] = max(0, steps[(x, y)] - 2)
        elif above is not None and above < r and lam[(x, y)] > 0.1:
            out[(x, y)] = min(hi, steps[(x, y)] + 1)
        elif (x, y + 1) not in owner or (x + 1, y) not in owner:
            out[(x, y)] = max(0, steps[(x, y)] - 1)
    for (x, y), k in out.items():
        col = rmp[k]
        if spec and k == hi and h01(x - dx, y, seed + 9) < 0.22 and len(rmp) > hi + 1:
            col = rmp[hi + 1]
        s.put(x, y, col)
    return out


def puff_mass(s: Img, shape: list, rmp: list, seed: int, r: float = 5.5, spacing: float = 5.0, lo: int = 1,
              hi: int = 5, dx: int = 0, whole: float = 0.6, bias: float = 0.0, flatten: float = 0.8,
              spec: bool = True) -> dict:
    """A crown built of leaf puffs: the shape (a union of ellipses [(cx, cy, rx, ry)]) is filled with small leaf
    clusters on a jittered grid, each a little sphere (radius about r, flattened by `flatten`), drawn back to front.
    Each pixel is lit by its puff's own normal blended with its place in the whole crown (`whole`: the upper-left of
    the crown catches the sun, its lower right and underside lie in shade), so the puffs read as the bumps on one
    lit form. A puff's rim darkens on its south-east side where it lies over the one behind, and brightens along its
    sunlit north-west edge. Quantised to ramp steps lo..hi, with sparse glints in the next step. Returns {(x, y): step}."""
    def inside(x: float, y: float, grow: float = 0.0) -> bool:
        return any(((x - cx - dx) / (rx + grow)) ** 2 + ((y - cy) / (ry + grow)) ** 2 <= 1.0 for cx, cy, rx, ry in shape)
    gx0 = min(c[0] - c[2] for c in shape) + dx
    gx1 = max(c[0] + c[2] for c in shape) + dx
    gy0 = min(c[1] - c[3] for c in shape)
    gy1 = max(c[1] + c[3] for c in shape)
    gcx, gcy, grx, gry = (gx0 + gx1) / 2, (gy0 + gy1) / 2, max(1.0, (gx1 - gx0) / 2), max(1.0, (gy1 - gy0) / 2)
    puffs = []
    rows = int((gy1 - gy0) / (spacing * 0.8)) + 3
    cols = int((gx1 - gx0) / spacing) + 3
    for j in range(rows):
        for i in range(cols):
            px = gx0 - spacing + (i + (0.5 if j % 2 else 0.0) + (h01(i, j, seed) - 0.5) * 0.7) * spacing
            py = gy0 - spacing * 0.5 + (j + (h01(i, j, seed + 1) - 0.5) * 0.6) * spacing * 0.8
            if not inside(px, py):
                continue
            pr = r * (0.8 + 0.4 * h01(i, j, seed + 2))
            puffs.append((py, px, pr, i, j))
    puffs.sort()
    owner: dict = {}
    val: dict = {}
    for rank, (py, px, pr, i, j) in enumerate(puffs):
        ry = pr * flatten
        for y in range(int(py - ry - 1), int(py + ry + 2)):
            for x in range(int(px - pr - 1), int(px + pr + 2)):
                if not (0 <= x < s.w and 0 <= y < s.h):
                    continue
                u, v = (x + 0.5 - px) / pr, (y + 0.5 - py) / ry
                d2 = u * u + v * v
                wobble = 0.18 * (h01(x, y, seed + 3) - 0.5)
                if d2 > 1.0 + wobble:
                    continue
                n = _norm((u, v, math.sqrt(max(0.02, 1.0 - min(1.0, d2)))))
                gu, gv = (x + 0.5 - gcx) / grx, (y + 0.5 - gcy) / gry
                g = _norm((gu, gv, math.sqrt(max(0.05, 1.0 - min(1.0, gu * gu + gv * gv)))))
                lc = n[0] * LIGHT[0] + n[1] * LIGHT[1] + n[2] * LIGHT[2]
                lg = g[0] * LIGHT[0] + g[1] * LIGHT[1] + g[2] * LIGHT[2]
                lam = lc * (1 - whole) + lg * whole
                ao = 0.26 * min(1.0, max(0.0, (y - gy0) / (gy1 - gy0))) ** 1.6
                v0 = 0.46 + 0.62 * (lam - 0.3) + bias - ao + (h01(i, j, seed + 4) - 0.5) * 0.1
                if d2 > 0.62 and u + v > 0.35:
                    v0 -= 0.2                                          # the puff's shaded south-east rim
                elif d2 > 0.5 and u + v < -0.6:
                    v0 += 0.12                                         # its sunlit north-west edge
                owner[(x, y)] = rank
                val[(x, y)] = v0
    out: dict = {}
    for (x, y), v0 in val.items():
        k = lo + int(max(0.0, min(0.999, v0)) * (hi - lo + 1))
        out[(x, y)] = max(lo, min(hi, k))
    for (x, y), k in out.items():
        col = rmp[k]
        if spec and k == hi and h01(x - dx, y, seed + 9) < 0.25 and len(rmp) > hi + 1:
            col = rmp[hi + 1]
        s.put(x, y, col)
    return out


def blossoms(s: Img, spots: list, rmp: list, seed: int, n: int, stem: list = None) -> None:
    """Blossom clusters over a mass: small five-pixel flowers and buds, lit north-west, a gold eye now and then."""
    k = 0
    for q in range(n * 4):
        if k >= n or not spots:
            break
        x, y = spots[int(h01(q, 1, seed) * len(spots))]
        if s.get(x, y)[3] == 0:
            continue
        k += 1
        big = h01(q, 2, seed) < 0.55
        if big:
            for ddx, ddy, st in ((0, -1, 5), (-1, 0, 4), (1, 0, 3), (0, 1, 3), (0, 0, 6)):
                s.put(x + ddx, y + ddy, rmp[min(len(rmp) - 1, st)])
            if h01(q, 3, seed) < 0.4:
                s.put(x, y, GOLDR[3])
        else:
            s.put(x, y, rmp[5])
            s.put(x + 1, y, rmp[3])


# ============================================================================================================ wood
def trunk(s: Img, x: float, base: int, top: int, w0: float, w1: float, rmp=BARK, lean: float = 0.0, seed: int = 0,
          flare: int = 2, bend=None) -> None:
    """A tapered bole from `base` up to `top`, its centre at x (+ lean per px up, + bend(t)), lit on the west side
    with a warm rim, shaded east, bark fissures running up it, a root flare at its foot."""
    n = len(rmp)
    for y in range(top, base):
        t = (base - y) / max(1, base - top)
        w = max(1, round(w0 + (w1 - w0) * t + (flare * (1 - min(1.0, (base - y) / 4.0)) if flare else 0)))
        cx = x + lean * (base - y) + (bend(t) if bend else 0.0)
        x0 = round(cx - w / 2)
        for i in range(w):
            k = 2
            if i == 0:
                k = 4 if w > 2 else 3
            elif i == 1 and w > 4:
                k = 3
            elif i == w - 1:
                k = 0 if w > 3 else 1
            elif i >= w - 2 and w > 5:
                k = 1
            if 0 < i < w - 1 and h01(i + x0, y // 3, seed) < 0.16:
                k = max(0, k - 1)
            if 0 < i < w - 2 and h01(i + x0, y // 5, seed + 1) < 0.07:
                k = min(n - 1, k + 1)
            s.put(x0 + i, y, rmp[min(n - 1, k)])


def limb(s: Img, pts: list, w0: float, w1: float, rmp=BARK) -> None:
    """A branch along a polyline, tapering from w0 to w1, lit on its upper-left edge and dark underneath."""
    segs = list(zip(pts, pts[1:]))
    total = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segs) or 1.0
    acc = 0.0
    n = len(rmp)
    for (ax, ay), (bx, by) in segs:
        L = math.hypot(bx - ax, by - ay)
        steps = max(1, int(L * 2))
        for k in range(steps + 1):
            t = k / steps
            x, y = ax + (bx - ax) * t, ay + (by - ay) * t
            w = w0 + (w1 - w0) * ((acc + L * t) / total)
            r = max(0.5, w / 2)
            for j in range(int(y - r - 1), int(y + r + 2)):
                for i in range(int(x - r - 1), int(x + r + 2)):
                    du, dv = i + 0.5 - x, j + 0.5 - y
                    if du * du + dv * dv > r * r + 0.25:
                        continue
                    kk = 2
                    if du + dv < -r * 0.5:
                        kk = 3 if r > 1 else 3
                    elif du + dv > r * 0.5:
                        kk = 1
                    s.put(i, j, rmp[min(n - 1, kk)])
        acc += L


def _trim_box(pix) -> list:
    xs = [p[0] for p in pix]
    ys = [p[1] for p in pix]
    return [min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1]


def opaque_box(s: Img) -> list:
    pix = [(x, y) for y in range(s.h) for x in range(s.w) if s.get(x, y)[3] > 0]
    return _trim_box(pix) if pix else [0, 0, 0, 0]


# ============================================================================================================ trees
# A tree: `trunk_*` draws the bole and main limbs (the prop's sprite, which sorts and blocks), `crown_*` the canopy
# (its own sprite, laid over the trunk at CANOPY's offset). Sprite sizes and anchors are in TREES below; `base` is the
# trunk's foot in the trunk sprite and in the canopy sprite (their shared ground line).

def _camphor_clumps(W: int, base: int) -> list:
    cx = W / 2
    top = base - 94
    return [(cx - 4, top + 18, 22, 15), (cx + 14, top + 20, 18, 13), (cx - 22, top + 28, 16, 12),
            (cx + 26, top + 32, 15, 12), (cx - 8, top + 34, 24, 15), (cx + 10, top + 40, 20, 14),
            (cx - 28, top + 44, 14, 11), (cx + 30, top + 48, 13, 10), (cx - 12, top + 52, 19, 12),
            (cx + 12, top + 56, 17, 11), (cx - 30, top + 56, 10, 8), (cx + 1, top + 62, 14, 9)]


def trunk_camphor(s: Img, f: int = 0, ribbons: bool = False) -> None:
    """A village camphor's bole: thick, a little crooked, its two main limbs forking into the crown. 28 x 72; the
    foot's footprint corner at (6, 70)."""
    base = 70
    trunk(s, 14, base, 30, 11, 7, BARK, 0.0, 11, 4, lambda t: math.sin(t * 2.4) * 1.5)
    limb(s, [(13, 36), (9, 26), (5, 14), (3, 6)], 5, 2)
    limb(s, [(15, 34), (19, 24), (23, 12), (24, 4)], 5, 2)
    limb(s, [(14, 32), (14, 18), (13, 2)], 4, 2)
    if ribbons:
        # a red cloth band tied round the bole, its knot and tails on the lit side
        for y in (48, 49, 50):
            for x in range(9, 20):
                if s.get(x, y)[3]:
                    s.put(x, y, RED[3] if y == 48 else RED[2] if y == 49 else RED[1])
        s.put(8, 49, RED[4])
        s.put(8, 50, RED[3])
        s.put(7, 51, RED[3])
        s.put(8, 52, RED[2])
    s.outline()


def crown_camphor(s: Img, f: int = 0, ribbons: bool = False) -> None:
    """A camphor's crown: a broad dome of round leaf clumps, dark glossy green, over thin outer branches. 96 x 80,
    over the trunk at CANOPY's offset; `ribbons` hangs red prayer ribbons and wooden wish tablets from its lower
    branches (the village's wishing tree)."""
    W, base = s.w, 104
    cl = _camphor_clumps(W, base)
    # outer branches showing in the gaps
    for pts in (((48, 70), (30, 58), (18, 50)), ((48, 68), (66, 56), (80, 50)), ((47, 64), (44, 44)), ((50, 62), (58, 40))):
        limb(s, list(pts), 2.5, 1)
    puff_mass(s, cl, LEAF, 101 + (7 if ribbons else 0), 5.5, 5.2, lo=1, hi=5)
    if ribbons:
        for k, (x, y, n) in enumerate(((22, 60, 9), (33, 66, 11), (58, 66, 10), (70, 62, 8), (44, 70, 7), (78, 56, 6))):
            sway = 1 if f in (1, 2) and k % 2 == 0 else 0
            for j in range(n):
                xx = x + (sway if j > n // 2 else 0)
                s.put(xx, y + j, RED[3] if j % 3 else RED[4])
                s.put(xx + 1, y + j, RED[2] if j < n - 1 else RED[1])
            if k % 2:
                s.rect(x - 1, y + n, 4, 5, WOOD[4])                     # a wooden wish tablet
                s.hline(x - 1, y + n, 4, WOOD[5])
                s.put(x, y + n + 2, RED[2])
                s.put(x + 2, y + n + 3, RED[2])
    s.outline()


def trunk_ribbons(s: Img, f: int = 0) -> None:
    trunk_camphor(s, f, True)


def crown_ribbons(s: Img, f: int = 0) -> None:
    crown_camphor(s, f, True)


def trunk_maple(s: Img, f: int = 0) -> None:
    """A maple's bole: slimmer and smoother than the camphor's, grey-brown, forking low. 24 x 64; corner (4, 62)."""
    base = 62
    trunk(s, 12, base, 30, 6, 4, DARKWOOD[:1] + BARK[1:], 0.04, 21, 2)
    limb(s, [(12, 36), (7, 24), (4, 10)], 4, 1.5)
    limb(s, [(13, 34), (18, 22), (21, 8)], 4, 1.5)
    s.outline()


def crown_maple(s: Img, f: int = 0) -> None:
    """A maple turning: a rounded crown of red and orange leaves, golden where the sun catches it. 80 x 76."""
    W, base = s.w, 96
    cx, top = W / 2, base - 90
    cl = [(cx - 6, top + 16, 18, 12), (cx + 12, top + 20, 16, 12), (cx - 20, top + 28, 15, 11), (cx + 22, top + 32, 14, 11),
          (cx - 4, top + 34, 21, 13), (cx + 8, top + 44, 18, 12), (cx - 22, top + 44, 13, 10), (cx + 24, top + 46, 11, 9),
          (cx - 8, top + 52, 16, 10)]
    for pts in (((40, 66), (26, 52)), ((40, 64), (56, 50)), ((40, 60), (40, 40))):
        limb(s, list(pts), 2.2, 1)
    puff_mass(s, cl, MAPLE, 131, 4.5, 4.4, lo=1, hi=5)
    s.outline()


def trunk_plum(s: Img, f: int = 0) -> None:
    """A plum's bole: dark, gnarled and leaning, the old tree of scholars' gardens, its limbs zig-zagging up. 36 x 60;
    corner (8, 58)."""
    base = 58
    trunk(s, 16, base, 26, 7, 4, DARKWOOD, 0.12, 31, 2, lambda t: math.sin(t * 5.0) * 2.0)
    limb(s, [(18, 30), (12, 22), (14, 14), (7, 6)], 4, 1.2, DARKWOOD)
    limb(s, [(20, 28), (27, 22), (26, 12), (32, 4)], 4, 1.2, DARKWOOD)
    s.outline()


def crown_plum(s: Img, f: int = 0, rmp=None, seed: int = 141) -> None:
    """A plum in blossom: dark zig-zag branches carrying loose clouds of white-pink flowers, the sky showing between
    them, a few young leaves. 80 x 72."""
    rmp = rmp or PLUM
    W, base = s.w, 90
    cx, top = W / 2, base - 84
    for pts in (((36, 60), (24, 48), (26, 38), (14, 28)), ((40, 58), (52, 48), (50, 36), (64, 26)),
                ((38, 56), (40, 40), (34, 28), (38, 14)), ((26, 40), (12, 40)), ((52, 44), (68, 44))):
        limb(s, list(pts), 2.6, 1, DARKWOOD)
    cl = [(cx - 18, top + 20, 10, 7), (cx + 12, top + 14, 10, 7), (cx - 28, top + 36, 9, 6), (cx + 26, top + 30, 10, 6),
          (cx - 4, top + 28, 9, 7), (cx + 12, top + 44, 10, 6), (cx - 14, top + 48, 11, 6), (cx + 29, top + 45, 7, 5),
          (cx - 2, top + 8, 7, 5), (cx + 2, top + 54, 8, 5)]
    drawn = puff_mass(s, cl, rmp, seed, 3.4, 4.2, lo=2, hi=5, whole=0.55)
    for pts in (((38, 56), (40, 40), (34, 28)), ((40, 58), (52, 48))):
        limb(s, list(pts), 2.2, 1.2, DARKWOOD)
    spots = sorted(drawn)
    blossoms(s, spots, rmp, seed + 13, 26)
    for q in range(10):                                            # a few young leaves
        x, y = spots[int(h01(q, 21, seed) * len(spots))]
        if s.get(x, y)[3]:
            s.put(x, y, LEAF[4])
            s.put(x + 1, y + 1, LEAF[3])
    s.outline()


def trunk_peach(s: Img, f: int = 0) -> None:
    """A peach's bole: short, reddish, forking into three. 28 x 52; corner (6, 50)."""
    base = 50
    trunk(s, 13, base, 26, 6, 4, BARK, -0.05, 41, 2)
    limb(s, [(12, 30), (6, 20), (3, 10)], 3.5, 1.2)
    limb(s, [(14, 28), (20, 18), (24, 8)], 3.5, 1.2)
    limb(s, [(13, 28), (14, 12)], 3, 1.2)
    s.outline()


def crown_peach(s: Img, f: int = 0) -> None:
    """A peach in blossom: a rounder, denser crown than the plum's, deep pink flowers over fresh leaves. 72 x 64."""
    W, base = s.w, 80
    cx, top = W / 2, base - 76
    for pts in (((34, 54), (22, 42)), ((36, 54), (50, 42)), ((35, 50), (35, 32))):
        limb(s, list(pts), 2.4, 1)
    cl = [(cx - 8, top + 16, 15, 10), (cx + 10, top + 18, 13, 10), (cx - 20, top + 28, 12, 9), (cx + 22, top + 30, 11, 9),
          (cx, top + 30, 17, 11), (cx - 12, top + 40, 14, 9), (cx + 14, top + 42, 13, 9), (cx, top + 48, 11, 7)]
    drawn = puff_mass(s, cl, PEACH, 151, 3.8, 4.0, lo=2, hi=5)
    spots = sorted(drawn)
    for q in range(40):                                            # the leaves under the flowers
        x, y = spots[int(h01(q, 3, 151) * len(spots))]
        if s.get(x, y)[3] and drawn.get((x, y), 5) <= 3:
            s.put(x, y, LEAF[3])
            s.put(x + 1, y, LEAF[2])
    blossoms(s, spots, PEACH, 157, 30)
    s.outline()


def trunk_pine(s: Img, f: int = 0) -> None:
    """A great mountain pine's bole: straight, red-brown, scaled bark, bare to half its height. 24 x 96; corner
    (6, 94)."""
    base = 94
    trunk(s, 12, base, 8, 7, 3, BARK, 0.0, 51, 3, lambda t: math.sin(t * 3.1) * 1.2)
    limb(s, [(12, 58), (5, 52), (1, 50)], 3, 1.5)
    limb(s, [(13, 44), (19, 38), (23, 36)], 3, 1.5)
    s.outline()


def crown_pine(s: Img, f: int = 0) -> None:
    """A great pine's crown: four flat pads of needles held out on crooked limbs, the "cloud pine" of the sect
    gardens, each pad a crowd of needle tufts lit along its upper-left and dark beneath, the lowest widest and to the
    west. 88 x 104."""
    W = s.w
    cx = W / 2
    for pts in (((44, 100), (44, 66), (30, 62), (14, 60)), ((44, 70), (46, 52), (64, 48), (76, 46)),
                ((45, 52), (43, 36), (30, 32)), ((43, 38), (46, 22), (56, 18)), ((46, 24), (45, 8))):
        limb(s, list(pts), 3.4, 1.4)
    pads = [[(cx - 22, 60, 17, 6.5), (cx - 8, 58, 13, 6), (cx - 33, 63, 9, 4.5)],
            [(cx + 18, 46, 16, 6), (cx + 4, 44, 11, 5), (cx + 30, 49, 9, 4.5)],
            [(cx - 12, 31, 15, 5.5), (cx + 2, 29, 10, 5)],
            [(cx + 7, 17, 12, 5), (cx - 3, 13, 9, 4.5), (cx + 2, 7, 6, 3.5)]]
    for k, pad in enumerate(pads):
        for (x, y, rx, ry) in pad:                                 # the pad's shaded underside
            s.ellipse(x + 1, y + 2.5, rx, ry * 0.9, PINE[1])
        puff_mass(s, pad, PINE, 161 + k * 5, 3.4, 3.4, lo=1, hi=5, whole=0.5, flatten=0.62, bias=0.06)
    s.outline()


def trunk_willow(s: Img, f: int = 0) -> None:
    """A great river willow's bole: leaning, thick and furrowed, forking under the crown. 28 x 60; corner (6, 58)."""
    base = 58
    trunk(s, 13, base, 18, 10, 6, WOOD, 0.08, 61, 4, lambda t: math.sin(t * 2.0) * 1.5)
    limb(s, [(15, 22), (9, 12), (4, 4)], 4, 1.5)
    limb(s, [(17, 22), (22, 12), (25, 4)], 4, 1.5)
    s.outline()


def crown_willow(s: Img, f: int = 0) -> None:
    """A great willow's crown: a soft dome of fine leaves and a curtain of leafy strands hanging from it toward the
    ground, the ground showing between them, lit on the west and shaded east; their lower halves sway a pixel east
    and back over four frames. 92 x 88."""
    sw = SWAY[f]
    W = s.w
    cx, top = W / 2, 4
    cl = [(cx - 4, top + 14, 21, 11), (cx + 16, top + 18, 17, 10), (cx - 22, top + 20, 16, 10), (cx + 2, top + 24, 24, 11),
          (cx - 32, top + 29, 11, 7), (cx + 32, top + 28, 11, 7)]
    drawn = puff_mass(s, cl, LEAF, 171, 3.6, 3.8, lo=1, hi=5)
    s.outline()
    low = {}
    for (x, y) in drawn:
        low[x] = max(low.get(x, -1), y)
    xs = sorted(low)
    x = xs[0] + 1
    while x < xs[-1]:
        # a strand every 2-3 px: a chain of paired leaves hanging from the crown's lower edge, darker than the meadow
        # so it reads against it, lit on the west of the crown
        y0 = low.get(x, 0) - 3
        ln = 24 + int(h01(x, 2, 173) * 30) - int(abs(x - cx) * 0.3)
        t = (x - xs[0]) / max(1, xs[-1] - xs[0])
        lit = t < 0.42
        for j in range(ln):
            y = y0 + j
            if y >= s.h - 6:
                break
            xx = x + (sw if j > ln // 2 else 0) + (1 if (j // 6) % 2 and j > 6 else 0)
            k = (3 if lit else 2) if (j + x) % 4 else (4 if lit else 3)
            if j >= ln - 3:
                k = 4 if lit else 3
            s.put(xx, y, LEAF[k])
            s.put(xx + 1, y, LEAF[max(0, k - 2)])                 # the strand's shaded east side
        x += 2 + int(h01(x, 5, 173) * 2)


# The grove's culms: (x at the foot, top y, width, lean per px up) in the trunk sprite.
CULMS = ((10, 30, 2, -0.16), (13, 14, 3, -0.1), (16, 22, 2, -0.06), (19, 6, 3, -0.03), (22, 18, 2, 0.0),
         (25, 4, 3, 0.03), (28, 16, 2, 0.06), (31, 8, 3, 0.1), (34, 26, 2, 0.14), (37, 20, 2, 0.18), (21, 40, 2, -0.12))
BAMBOO_AT = (18, 14)   # trunk sprite (x, y) + this = the same point in the canopy sprite


def trunk_bamboo(s: Img, f: int = 0) -> None:
    """A bamboo grove's culms: eleven poles of three ages rising from one clump and fanning out as they climb, lit west,
    pale-ringed at their nodes, their tops swaying a pixel over four frames. 48 x 112; the clump's footprint corner
    (8, 110), 2 x 1."""
    sw = SWAY[f]
    for k, (x, top, w, lean) in enumerate(CULMS):
        rmp = BAMBOO if k % 4 else [BAMBOO[0], BAMBOO[1], REED[2], REED[3], REED[4], REED[4]]
        for y in range(top, 110):
            off = round(lean * (110 - y)) + (sw if y < 48 else 0)
            s.put(x + off, y, rmp[4])
            for d in range(1, w):
                s.put(x + off + d, y, rmp[3] if d < w - 1 else rmp[2])
        for y in range(top + 4 + (x % 5), 106, 10):
            off = round(lean * (110 - y)) + (sw if y < 48 else 0)
            s.hline(x + off, y, w, rmp[5])
            s.hline(x + off, y + 1, w, rmp[1])
    s.rect(8, 107, 32, 3, DARKWOOD[2])
    s.hline(8, 107, 32, DARKWOOD[4])
    for x, y in ((7, 108), (40, 108), (12, 106), (35, 106)):          # shoots at the clump's foot
        s.put(x, y, BAMBOO[4])
        s.put(x, y - 1, BAMBOO[5])
    s.outline()


def _spray(s: Img, x: float, y: float, d: int, seed: int, n: int, lit_side: bool) -> None:
    """A bamboo spray's fringe: n spear leaves hanging from a twig, down and out on the `d` side."""
    for q in range(n):
        ang = (0.45 + 0.8 * h01(q, 1, seed)) * (1 if d > 0 else -1)
        ln = 5 + int(h01(q, 2, seed) * 4)
        sx, sy = x + d * q * 1.6, y + (q % 3) - 1
        for m in range(ln):
            px = round(sx + math.sin(ang) * m)
            py = round(sy + math.cos(abs(ang)) * m * 0.9)
            k = (4 if lit_side else 3) if m < ln // 2 else (3 if lit_side else 2)
            if m == 0:
                k = 5 if lit_side else 3
            s.put(px, py, BAMBOO[k])
            if 1 <= m < ln - 2:
                s.put(px + (1 if d > 0 else -1), py, BAMBOO[max(1, k - 1)])


def crown_bamboo(s: Img, f: int = 0) -> None:
    """A bamboo grove's crown: a spray of leaves at each culm's top, hanging down and out along its lean, each a small
    mass of leaves lit on its upper-left and fringed with spear leaves, the sky showing between them; they sway with
    the culms. 84 x 76."""
    sw = SWAY[f]
    ax, ay = BAMBOO_AT
    sprays = []
    for k, (x, top, w, lean) in enumerate(CULMS):
        tx = x + round(lean * (110 - top)) + ax
        ty = top + ay
        d = -1 if lean < 0 else 1
        sprays.append((k, tx + d * 4, ty + 6, d))
        if k % 2 == 0:
            sprays.append((k + 20, tx + d * 9, ty + 16, d))
    masses = [(x + sw, y, 6.5 + (k % 3), 4.2) for k, x, y, d in sprays]
    puff_mass(s, masses, BAMBOO, 181, 2.6, 3.0, lo=1, hi=4, whole=0.55, flatten=0.75)
    for k, x, y, d in sprays:
        _spray(s, x + sw + d * 3, y + 1, d, 190 + k, 4 + k % 3, x < 44)
    s.outline()


# ============================================================================================================ bushes
def bush(s: Img, f: int = 0, flowers=None, seed: int = 201) -> None:
    """A round garden bush, footprint 1 x 1: a mound of leaf puffs lit from the upper left, dark at its foot, a little
    wider than its tile. 30 x 26; corner (7, 24)."""
    cl = [(15, 11, 11, 8), (8, 15, 7, 6), (22, 15, 7, 6), (15, 17, 11, 6)]
    drawn = puff_mass(s, cl, LEAF, seed, 3.6, 3.6, lo=1, hi=5)
    if flowers:
        blossoms(s, sorted(k for k, v in drawn.items() if v >= 2), flowers, seed + 3, 12)
    s.outline()


def bush_azalea(s: Img, f: int = 0) -> None:
    """A flowering azalea, footprint 1 x 1: a mound of small dark leaves covered in crimson-pink flowers."""
    bush(s, f, AZALEA + [c("FFD8D0")], 211)


def bush_wide(s: Img, f: int = 0) -> None:
    """A wide shrub, footprint 2 x 1: several leaf mounds run together, lit from the upper left. 46 x 30; corner (7, 28)."""
    cl = [(14, 13, 10, 8), (27, 11, 12, 9), (37, 16, 8, 7), (9, 19, 7, 6), (23, 20, 13, 7), (36, 21, 8, 6)]
    puff_mass(s, cl, LEAF, 221, 3.8, 3.8, lo=1, hi=5)
    s.outline()


def hedge(s: Img, n: int) -> None:
    """A clipped hedge n tiles long (E-W), waist-high: a row of box shrubs grown into one, a sunlit top and a leafy
    front falling into shade at its foot. (16 n + 6) x 26; corner (3, 24)."""
    W = n * 16 + 6
    cl = []
    for k in range(n * 2):
        x = 6 + k * 8 + (h01(k, 1, 231 + n) - 0.5) * 2
        cl.append((x, 11 + (h01(k, 2, 231) - 0.5) * 2, 6.5, 7))
        cl.append((x + 3, 16, 6.5, 6.5))
    cl = [(min(max(x, 7), W - 7), y, rx, ry) for x, y, rx, ry in cl]
    puff_mass(s, cl, BOX, 231 + n, 3.0, 3.2, lo=1, hi=5, whole=0.7)
    s.outline()


def fence(s: Img, n: int) -> None:
    """A split-bamboo and timber rail fence running E-W, n tiles long: posts at every tile with a cap, two rails, lashing,
    lit from the upper left. 16 n x 22; corner (0, 20)."""
    W = n * 16
    for k in range(n + 1):
        x = min(k * 16, W - 3)
        s.rect(x, 4, 3, 16, WOOD[3])
        s.vline(x, 4, 16, WOOD[5])
        s.vline(x + 2, 4, 16, WOOD[1])
        s.rect(x, 3, 3, 1, WOOD[6])
        s.put(x + 1, 19, DARKWOOD[1])
    for y in (7, 13):
        for x in range(1, W - 1):
            if s.get(x, y)[3] and s.get(x, y)[:3] in (WOOD[3][:3], WOOD[5][:3], WOOD[1][:3]):
                continue
            s.put(x, y, BAMBOO[4] if (x // 5) % 2 else REED[4])
            s.put(x, y + 1, BAMBOO[2] if (x // 5) % 2 else REED[2])
        for k in range(n + 1):                                   # the lashing
            x = min(k * 16, W - 3)
            s.put(x + 1, y, DARKWOOD[3])
            s.put(x + 1, y + 1, DARKWOOD[2])
    s.outline()


# ============================================================================================================ stone and wood
def rock_mossy(s: Img, f: int = 0) -> None:
    """A big karst rock half sunk in the ground, footprint 2 x 1: two limestone lumps lit from the upper left, a fissure
    between them, moss cushions on its sunlit top and ferns at its foot. 36 x 28; corner (2, 26)."""
    s.ellipse(15, 16, 13, 10, ROCK[3], (ROCK[5], ROCK[1]))
    s.ellipse(25, 18, 10, 8, ROCK[3], (ROCK[4], ROCK[1]))
    s.ellipse(12, 12, 8, 6, ROCK[4], (ROCK[6], ROCK[2]))
    for j in range(10, 25):
        s.put(21 + (j % 4 == 0), j, ROCK[1])
    for x in range(3, 34):                                       # the foot, darker where it meets the ground
        for y in range(18, 27):
            if s.get(x, y)[3] and not s.get(x, y + 2)[3]:
                s.put(x, y, ROCK[1] if s.get(x, y)[:3] != ROCK[1][:3] else ROCK[0])
    leaf_mass(s, [(11, 7, 6, 3), (19, 9, 4, 2.5), (27, 12, 4, 2.2)], MOSS, 241, 2.0, 0.6, lo=2, hi=5)
    for x, y in ((4, 24), (31, 25), (33, 23)):                      # ferns at the foot
        for k in range(3):
            s.put(x + k, y - k // 2, MOSS[4] if k == 0 else MOSS[3])
    s.outline()


def rock_small(s: Img, f: int = 0) -> None:
    """A small mossy stone, footprint 1 x 1. 18 x 16; corner (1, 14)."""
    s.ellipse(9, 9, 7.5, 5.5, ROCK[3], (ROCK[5], ROCK[1]))
    s.ellipse(7, 7, 4, 3, ROCK[4], (ROCK[6], ROCK[3]))
    leaf_mass(s, [(8, 5, 4, 2)], MOSS, 251, 2.0, 0.6, lo=2, hi=5)
    s.outline()


def log(s: Img, f: int = 0) -> None:
    """A fallen trunk, footprint 2 x 1: bark lit on its upper side, the cut end showing its rings to the west, moss and
    a shelf fungus on it. 36 x 18; corner (2, 16)."""
    for x in range(6, 34):
        for y in range(4, 15):
            k = 4 if y == 4 else 3 if y < 7 else 2 if y < 11 else 1
            if h01(x // 2, y, 261) < 0.14:
                k = max(0, k - 1)
            s.put(x, y, BARK[k])
    s.ellipse(6, 9.5, 4, 5.5, WOOD[4], (WOOD[6], WOOD[2]))       # the cut end
    s.ellipse(6, 9.5, 2, 3, WOOD[3])
    s.put(6, 9, WOOD[2])
    leaf_mass(s, [(18, 4, 6, 2.2), (28, 5, 4, 2)], MOSS, 263, 2.0, 0.6, lo=2, hi=5)
    for x, y in ((24, 10), (25, 10), (26, 10), (25, 11)):          # a shelf fungus
        s.put(x, y, WOOD[5])
    s.outline()


def stump(s: Img, f: int = 0) -> None:
    """A tree stump, footprint 1 x 1: roots spreading, a sawn top with rings, lit from the upper left. 20 x 16; corner
    (2, 14)."""
    s.rect(4, 5, 12, 8, BARK[2])
    s.vline(4, 5, 8, BARK[4])
    s.vline(15, 5, 8, BARK[1])
    for x, y in ((2, 12), (3, 11), (16, 12), (17, 13), (9, 13)):
        s.put(x, y, BARK[2])
    s.ellipse(10, 5, 6, 2.6, WOOD[5], (WOOD[6], WOOD[3]))
    s.ellipse(10, 5, 3, 1.3, WOOD[4])
    s.put(10, 5, WOOD[3])
    leaf_mass(s, [(6, 11, 3, 1.6)], MOSS, 271, 2.0, 0.5, lo=2, hi=4)
    s.outline()


def shrine_small(s: Img, f: int = 0) -> None:
    """A wayside earth-god shrine, footprint 1 x 1: a little house of red lacquer on a granite plinth under a grey tile
    roof with curled ridge ends, a gilt tablet in its dark doorway, two peaches and a glowing incense stick on the
    ledge before it. 24 x 32; corner (4, 30)."""
    s.rect(2, 25, 20, 5, STONE[3])                               # the plinth
    s.hline(2, 25, 20, STONE[5])
    s.hline(2, 29, 20, STONE[1])
    s.vline(21, 26, 3, STONE[2])
    s.rect(5, 13, 14, 12, RED[2])                                # the lacquered house
    s.vline(5, 13, 12, RED[4])
    s.vline(18, 13, 12, RED[1])
    s.rect(8, 15, 8, 10, DARKWOOD[0])                            # its doorway
    s.rect(10, 16, 4, 6, GOLDR[1])
    s.rect(11, 17, 2, 4, GOLDR[2])
    s.put(11, 17, GOLDR[4])
    s.hline(4, 24, 16, STONE[4])                                 # the ledge, the offerings on it
    for x in (6, 16):
        s.put(x, 23, c("F4A080"))
        s.put(x + 1, 23, c("E07060"))
        s.put(x, 22, LEAF[4])
    s.put(12, 23, BRONZER[3])
    s.put(11, 23, BRONZER[4])
    s.put(12, 21, RED[3])
    s.put(12, 20, LANTERN[4])
    for k, (x, y) in enumerate(((12, 19), (13, 18), (13, 17), (12, 16))):
        s.put(x, y, alpha(MIST, 190 - k * 40))
    s.rect(1, 9, 22, 4, ROOF[3])                                 # the roof: eave, courses, ridge
    s.hline(1, 9, 22, ROOF[5])
    s.hline(1, 12, 22, ROOF[1])
    for x in range(2, 22, 3):
        s.vline(x, 10, 2, ROOF[2])
    s.rect(4, 6, 16, 3, ROOF[4])
    s.hline(4, 6, 16, ROOF[5])
    s.hline(3, 5, 18, ROOF[2])
    s.put(2, 4, GOLDR[2])
    s.put(21, 4, GOLDR[2])
    s.put(3, 5, ROOF[1])
    s.put(20, 5, ROOF[1])
    s.rect(11, 3, 2, 2, JADE)
    s.put(11, 3, BJADE)
    s.outline()


def pot_bonsai(s: Img, f: int = 0) -> None:
    """A glazed jar with a little pine trained in it, footprint 1 x 1 (a courtyard's or a hall's). 18 x 26; corner
    (1, 24)."""
    s.ellipse(9, 19, 6.5, 5, JADE, (BJADE, c("15514F")))
    s.rect(4, 13, 10, 3, c("15514F"))
    s.hline(4, 13, 10, BJADE)
    s.ellipse(9, 13.5, 4.5, 1.2, DARKWOOD[2])
    limb(s, [(9, 13), (7, 9), (10, 6), (12, 4)], 2, 1, BARK)
    leaf_mass(s, [(6, 7, 5, 2.4), (13, 4, 4.5, 2.2), (10, 2, 3, 1.6)], PINE, 281, 1.8, 0.3, "needle", 0.5, 2, 5)
    s.outline()


def pot_orchid(s: Img, f: int = 0) -> None:
    """A blue-and-white porcelain pot of orchids, footprint 1 x 1: arching leaves, two sprays of pale flowers. 18 x 24;
    corner (1, 22)."""
    s.ellipse(9, 18, 6, 4.5, c("E8EEF0"), (c("FFFFFF"), c("A8B8C8")))
    for x in (6, 9, 12):
        s.put(x, 18, c("3A5AA0"))
        s.put(x, 19, c("3A5AA0"))
    s.hline(4, 14, 10, c("C8D4DC"))
    for pts in (((9, 14), (4, 8), (2, 10)), ((9, 14), (13, 7), (16, 9)), ((9, 14), (8, 6))):
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            for k in range(8):
                t = k / 7
                s.put(round(ax + (bx - ax) * t), round(ay + (by - ay) * t), LEAF[3] if k % 2 else LEAF[4])
    for x, y in ((6, 4), (8, 3), (10, 3), (12, 4), (5, 6)):
        s.put(x, y, c("F8F0F8"))
        s.put(x + 1, y + 1, LOTUS[2])
    s.outline()


# ============================================================================================================ walk-through plants
def tall_grass(s: Img, f: int = 0) -> None:
    """A patch of tall grass, footprint 2 x 1, walk-through: three rows of crowded blades up to 20 px (the back row in
    shade, the front row lit), pale seed heads on a few, the tips stirring a pixel east and back over four frames.
    36 x 26; corner (2, 24)."""
    sw = SWAY[f]
    g = T2.GRASS2
    for row, (y0, n, dk) in enumerate(((19, 14, 0), (21, 14, 1), (23, 12, 1))):
        for k in range(n):
            x = 3 + int(h01(k, 1 + row * 7, 291) * 30)
            edge = min(x - 3, 33 - x)
            ln = 9 + int(h01(k, 2 + row * 7, 291) * 11) - max(0, 5 - edge) - row * 2
            lean = (h01(k, 3 + row * 7, 291) - 0.5) * 0.6 + (x - 18) * 0.02
            for j in range(ln):
                t = j / max(1, ln - 1)
                y = y0 - j
                xx = x + round(lean * j) + (sw if t > 0.5 else 0)
                kk = (1 if t < 0.2 else 2 if t < 0.45 else 3 if t < 0.8 else 4) + dk
                if lean > 0.15 and t > 0.4:
                    kk -= 1
                s.put(xx, y, g[max(1, min(6, kk))])
            if k % 4 == 0 and row < 2:
                tx = x + round(lean * ln) + sw
                s.put(tx, y0 - ln, c("E8DC98"))
                s.put(tx, y0 - ln - 1, c("F6ECC0"))
    for x in range(3, 34):
        if s.get(x, 23)[3]:
            s.put(x, 24, alpha(SHADOW, 90))
    s.outline()


def cattails(s: Img, f: int = 0) -> None:
    """Cattails at the water's edge, footprint 1 x 1, walk-through: long thin blades arching out from the clump like a
    fountain (lit on the west, shaded east) and three stems carrying brown velvet heads above them, swaying over four
    frames. 26 x 36; corner (5, 34)."""
    sw = SWAY[f]
    cx = 13
    for k in range(9):                                           # the blades, fanning out and bending over
        side = (k - 4) / 4.0
        ln = 16 + int(h01(k, 1, 301) * 10) - int(abs(side) * 4)
        for j in range(ln):
            t = j / ln
            x = cx + round(side * (1 + 11 * t * t)) + (sw if t > 0.5 else 0)
            y = 34 - round(j * (1.0 - 0.35 * t * abs(side)))
            kk = 3 if t < 0.6 else 4
            if side > 0.1:
                kk -= 1
            s.put(x, y, REED[max(1, min(4, kk))] if k % 2 else T2.GRASS2[max(2, min(5, kk + 1))])
    for k, (dx, top) in enumerate(((-6, 7), (0, 2), (6, 10))):
        x = cx + dx
        for y in range(top, 34):
            lean = round(dx * (34 - y) / 60.0)
            s.put(cx + round(dx * 0.3) + lean + (sw if y < 18 else 0), y, REED[4] if y < top + 6 else REED[3])
        hx = cx + round(dx * 0.3) + round(dx * (34 - top) / 60.0) + sw
        s.rect(hx, top - 6, 2, 6, DARKWOOD[3])
        s.vline(hx, top - 6, 6, DARKWOOD[4])
        s.put(hx, top - 7, REED[4])
        s.put(hx, top - 8, REED[4])
    s.outline()


def ferns(s: Img, f: int = 0) -> None:
    """A clump of ferns, footprint 1 x 1, walk-through: nine fronds arching out from a dark heart, each a rib with its
    leaflets lit on the upper side. 28 x 18; corner (6, 16)."""
    for k in range(9):
        ang = math.pi * (1.05 + 0.9 * k / 8) + (h01(k, 1, 311) - 0.5) * 0.2
        ln = 9 + int(h01(k, 2, 311) * 5) - (3 if 2 < k < 6 else 0)
        for q in range(ln):
            t = q / ln
            x = round(14 + math.cos(ang) * q * 1.2)
            y = round(15 + math.sin(ang) * q * 1.25 + t * t * 3.0)
            s.put(x, y, MOSS[3])
            if q > 1 and q % 2 == 0 and q < ln - 1:
                lit = math.cos(ang) < 0.3
                s.put(x, y - 1, MOSS[5] if lit else MOSS[4])
                s.put(x + (1 if math.cos(ang) > 0 else -1), y + 1, MOSS[2])
            if q == ln - 1:
                s.put(x, y, MOSS[4])
    s.put(14, 15, MOSS[1])
    s.put(13, 15, MOSS[1])
    s.outline()


def lotus_pads(s: Img, f: int = 0) -> None:
    """Lotus pads without a flower, on the water (walk-through, footprint 2 x 1). 32 x 16; corner (0, 16)."""
    pads = ((7, 8, 5.5, 3.2), (18, 11, 6, 3.4), (27, 6, 4.2, 2.4), (13, 4, 3.4, 2))
    for cx, cy, rx, ry in pads:
        s.ellipse(cx, cy + 1, rx, ry, alpha(WATER[1], 255))
        s.ellipse(cx, cy, rx, ry, PAD[3], (PAD[4], PAD[2]))
        s.put(int(cx) + 1, int(cy), WATER[3])
        s.put(int(cx) + 2, int(cy), WATER[3])
        s.put(int(cx), int(cy) - 1, PAD[5])



# kind: (draw, w, h, footprint w, h, origin, solid, shadow [dx, dy, rx, ry]) as props.PROPS
PROPS = {
    "tree_camphor": (trunk_camphor, 28, 72, 1, 1, [6, 70], True, [34, 2, 34, 18]),
    "tree_ribbons": (trunk_ribbons, 28, 72, 1, 1, [6, 70], True, [34, 2, 34, 18]),
    "tree_maple": (trunk_maple, 24, 64, 1, 1, [4, 62], True, [30, 0, 30, 16]),
    "tree_plum": (trunk_plum, 36, 60, 1, 1, [8, 58], True, [28, 0, 28, 14]),
    "tree_peach": (trunk_peach, 28, 52, 1, 1, [6, 50], True, [24, 0, 26, 13]),
    "tree_pine": (trunk_pine, 24, 96, 1, 1, [6, 94], True, [36, 4, 34, 16]),
    "tree_willow": (trunk_willow, 28, 60, 1, 1, [6, 58], True, [30, 0, 34, 16]),
    "bamboo_grove": (trunk_bamboo, 48, 112, 2, 1, [8, 110], True, [40, 0, 34, 14]),
    "bush": (bush, 30, 26, 1, 1, [7, 24], True, [12, -1, 12, 5]),
    "bush_azalea": (bush_azalea, 30, 26, 1, 1, [7, 24], True, [12, -1, 12, 5]),
    "bush_wide": (bush_wide, 46, 30, 2, 1, [7, 28], True, [20, -1, 20, 5]),
    "hedge_2": (lambda s: hedge(s, 2), 38, 26, 2, 1, [3, 24], True, [19, 0, 18, 4]),
    "hedge_3": (lambda s: hedge(s, 3), 54, 26, 3, 1, [3, 24], True, [27, 0, 26, 4]),
    "hedge_4": (lambda s: hedge(s, 4), 70, 26, 4, 1, [3, 24], True, [35, 0, 34, 4]),
    "fence_2": (lambda s: fence(s, 2), 32, 22, 2, 1, [0, 20], True, [18, -1, 15, 2]),
    "fence_3": (lambda s: fence(s, 3), 48, 22, 3, 1, [0, 20], True, [26, -1, 23, 2]),
    "fence_4": (lambda s: fence(s, 4), 64, 22, 4, 1, [0, 20], True, [34, -1, 31, 2]),
    "rock_mossy": (rock_mossy, 36, 28, 2, 1, [2, 26], True, [20, -1, 16, 4]),
    "rock_small": (rock_small, 18, 16, 1, 1, [1, 14], True, [10, -1, 7, 3]),
    "log": (log, 36, 18, 2, 1, [2, 16], True, [20, 0, 16, 3]),
    "stump": (stump, 20, 16, 1, 1, [2, 14], True, [10, -1, 8, 3]),
    "shrine_small": (shrine_small, 24, 32, 1, 1, [4, 30], True, [11, -2, 10, 3]),
    "pot_bonsai": (pot_bonsai, 18, 26, 1, 1, [1, 24], True, [9, -2, 7, 3]),
    "pot_orchid": (pot_orchid, 18, 24, 1, 1, [1, 22], True, [9, -2, 7, 3]),
    "tall_grass": (tall_grass, 36, 26, 2, 1, [2, 24], False, None),
    "cattails": (cattails, 26, 36, 1, 1, [5, 34], False, None),
    "ferns": (ferns, 28, 18, 1, 1, [6, 16], False, None),
    "lotus_pads": (lotus_pads, 32, 16, 2, 1, [0, 16], False, None),
}

# Canopies (overhangs): kind -> (draw, w, h, at [x, y] of the sprite's top-left from the footprint's south-west corner,
# clumps for its shade (in the canopy sprite), the height of the crown's middle over the ground in art px).
CANOPY = {
    "tree_camphor": (crown_camphor, 96, 80, [-40, -102]),
    "tree_ribbons": (crown_ribbons, 96, 92, [-40, -102]),
    "tree_maple": (crown_maple, 80, 76, [-32, -94]),
    "tree_plum": (crown_plum, 80, 72, [-30, -88]),
    "tree_peach": (crown_peach, 72, 64, [-28, -78]),
    "tree_pine": (crown_pine, 88, 104, [-38, -116]),
    "tree_willow": (crown_willow, 92, 88, [-38, -98]),
    "bamboo_grove": (crown_bamboo, 84, 76, [-26, -124]),
}

# Animated: frames side by side (props.ANIM's rule). A canopy sways with its trunk's clock.
ANIM = {"tree_willow": (4, 600), "bamboo_grove": (4, 500), "tree_ribbons": (4, 700), "tall_grass": (4, 550),
        "cattails": (4, 500)}
# Trunks that hold still while their canopy sways: they are drawn once (only the canopy's frames move).
STILL_TRUNK = {"tree_willow", "tree_ribbons"}


SWAY = (0, 1, 1, 0)


def canopy_shade(kind: str) -> tuple:
    """A tree's floor shadow: its crown's shade on the ground (art bible "Terrain v2" light). The crown's silhouette,
    squashed to the ground round the trunk's row, is moved along the sun's direction by the crown's height over the
    ground (+0.45 h, +0.20 h): 0.41 of `SHADOW` in its body, 0.25 on a 2 px rim and in a few flecks of sun let through
    the leaves. Returns (sprite, its top-left from the footprint's south-west corner), as props.shadow_sprite does."""
    draw, w, h, fw, fh, origin, solid, shadow = PROPS[kind]
    cd, cw, ch, at = CANOPY[kind]
    can = Img(cw, ch)
    cd(can, 0)
    bx, by, bw, bh = opaque_box(can)
    ccy = at[1] + by + bh * 0.55                  # the crown's middle, from the footprint's corner (y up is negative)
    hc = -ccy - fh * 8                            # its height over the trunk's row
    gcy = -fh * 8                                 # the trunk's row, where the crown's ground footprint is centred
    sx0, sy0 = 0.45 * hc, 0.2 * hc
    squash = 0.62
    xs = [at[0] + bx + sx0 - 2, at[0] + bx + bw + sx0 + 2]
    ys = [gcy + (at[1] + by - ccy) * squash + sy0 - 2, gcy + (at[1] + by + bh - ccy) * squash + sy0 + 2]
    x0, y0 = int(math.floor(xs[0])), int(math.floor(ys[0]))
    W, H = int(math.ceil(xs[1])) - x0, int(math.ceil(ys[1])) - y0
    # The crown's mask without its thin parts (a willow's strands, a limb): only pixels well inside the leaves.
    solid = set()
    for y in range(ch):
        for x in range(cw):
            if can.get(x, y)[3] and sum(1 for a in range(-2, 3) for b in range(-2, 3) if can.get(x + a, y + b)[3]) >= 23:
                solid.add((x, y))
    thick = {(x + a, y + b) for (x, y) in solid for a in range(-2, 3) for b in range(-2, 3) if abs(a) + abs(b) <= 3}
    # The trunk's shadow: each pixel of the bole below the crown cast from its height over the foot.
    trunk_img = Img(w, h)
    draw(trunk_img)
    tr = []
    for y in range(h):
        for x in range(w):
            if trunk_img.get(x, y)[3] and trunk_img.get(x, y)[:3] != (14, 26, 30):
                hh = origin[1] - y
                tr.append((x - origin[0] + 0.45 * hh, gcy + 0.2 * hh + (y - origin[1]) * 0.0))
    if tr:
        x0 = min(x0, int(min(p[0] for p in tr)) - 1)
        y0 = min(y0, int(min(p[1] for p in tr)) - 1)
        W = max(x0 + W, int(max(p[0] for p in tr)) + 2) - x0
        H = max(y0 + H, int(max(p[1] for p in tr)) + 2) - y0
    inside = set()
    for j in range(H):
        for i in range(W):
            gx, gy = x0 + i + 0.5 - sx0, y0 + j + 0.5 - sy0
            cx = gx - at[0]
            cy = (ccy + (gy - gcy) / squash) - at[1]
            if (int(cx), int(cy)) in thick and 0 <= cx and 0 <= cy:
                inside.add((i, j))
    for (px, py) in tr:
        for a in (0, 1):
            inside.add((int(px) - x0 + a, int(py) - y0))
    out = Img(W, H)
    for (i, j) in inside:
        rim = any((i + a, j + b) not in inside for a in (-2, -1, 0, 1, 2) for b in (-2, -1, 0, 1, 2) if abs(a) + abs(b) <= 2)
        fleck = T2.pn(i + x0, j + y0, 777, 4, 4096, 4096) > 0.74 and h01(i // 2, j // 2, 778) < 0.7
        out.put(i, j, alpha(SHADOW, 64 if rim or fleck else T2.SHADOW_A))
    return out, [x0, y0]


SHADOWS = {kind: canopy_shade for kind in CANOPY}


def shadow_of(kind: str) -> tuple:
    return SHADOWS[kind](kind)


def fade_box(canopy: Img) -> list:
    """The part of a canopy that hides whoever walks under it: its leaves' bounding box less a margin of 4 px (the
    thin rim of leaves over a body's head does not fade it), [x, y, w, h] in the canopy sprite."""
    x, y, w, h = opaque_box(canopy)
    return [x + 4, y + 4, max(1, w - 8), max(1, h - 8)]


# What falls from each tree onto the ground round it: the scatter's litter set there (TopdownFoliage).
LITTER = {"tree_camphor": "litter_leaves", "tree_ribbons": "litter_leaves", "tree_maple": "litter_maple",
          "tree_plum": "litter_plum", "tree_peach": "litter_peach", "tree_pine": "litter_pine",
          "tree_willow": "litter_leaves", "bamboo_grove": "litter_bamboo",
          "dead_tree": "blight"}   # round a tree the Hollowing has drained, nothing grows
