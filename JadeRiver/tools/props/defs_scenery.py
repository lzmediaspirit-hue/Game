"""Scenery props: trees, rocks, plants, fences, cliffs, bridges and docks, sect architecture,
village clutter, water/mist effects and interior furnishings.

Every sprite uses a few short hue-shifted material ramps (dark -> light) and `finish()`,
which outlines the silhouette and snaps the outline pixels to one dark ink per material,
so a sprite stays within roughly 4-10 purposeful colours. Light comes from the upper left.
"""
from __future__ import annotations

import math

import numpy as np

from palette import INK  # noqa: F401
from parts import lathe
from pixlib import (Canvas, bbox, border, bottom_edge, dilate, erode, grid, hexc, left_edge, m_curve, m_ellipse, m_line,
                    m_poly, m_rect, mix, outline, right_edge, rng, seed_of, shade, shift, top_edge, vnoise)
from registry import prop


def R(*hexes):
    return [hexc(h) for h in hexes]


# ------------------------------------------------------------------ short material ramps (dark -> light)
BARK = R("#2b1d16", "#4a3324", "#6f5037", "#977150")
BARK_GREY = R("#2c2b27", "#4a463d", "#6e675a", "#968d7b")
WILLOW = R("#1c4436", "#2b6146", "#428052", "#66a05d", "#9dc676")
PINE = R("#153630", "#214c3e", "#336547", "#4f8453", "#7ca864")
BAMBOO = R("#2a5431", "#3f743c", "#5e944a", "#8bbd5f", "#c3df8c")
BAMBOO_LEAF = R("#1d4230", "#2d5d3a", "#467c45", "#6da052")
BLOSSOM = R("#8e3656", "#cc5f80", "#f094ac", "#ffd3de")
PLUM_BARK = R("#1e1519", "#3a2a2c", "#5a4441", "#7d6459")
HOLLOW = R("#454f53", "#6f7b80", "#96a2a6", "#c1c9ca", "#e8ecea")
STONE = R("#2a3639", "#445457", "#667775", "#8e9d96", "#bac4b8")
STONE_W = R("#3f4442", "#666c67", "#8f948c", "#b9bcb1", "#dcdcd0")
MOSS = R("#28472b", "#3e6a31", "#62933f", "#99c25a")
LEAF = R("#173a2c", "#245238", "#3a6e42", "#5b8f4c", "#8ab45e")
GRASS = R("#1f4631", "#316640", "#4d8a4b", "#7cb05a", "#b6d57c")
WOOD = R("#2c1e14", "#523723", "#7a5535", "#a1784c", "#c79f6c")
WOOD_DRY = R("#3a3024", "#5f4f3a", "#877259", "#ae997b", "#d2c1a0")
LACQ = R("#3f1216", "#6f1f1f", "#9e3326", "#cc5436")
GOLD = R("#6b4417", "#a6752c", "#dcac46", "#f9df94")
JADE_TILE = R("#0c3134", "#18605b", "#279078", "#5cc9a8", "#aee9d0")
CLOUD_TILE = R("#1f2a33", "#34454f", "#566b75", "#8ba1a8")
WALL_W = R("#8f8a79", "#c9c3b0", "#ece6d3")
STRAW = R("#4d3a1a", "#7e6230", "#ae8d47", "#d8bc72", "#f2e2a8")
ROPE = R("#3e2c18", "#6b5030", "#9a7c4e", "#c8ae7c")
IRON = R("#1d2427", "#394549", "#5d6c6f", "#8c9a98")
CLOTH_J = R("#0d3a36", "#175c52", "#23836f", "#3fae8f", "#86d8b8")
CLOTH_C = R("#3b5064", "#6d8aa0", "#a7bfcd", "#dfe9ec", "#fbfdfa")
CLOTH_R = R("#4a1216", "#7a1f22", "#ad3129", "#d9523b", "#f08a5d")
SACK = R("#4b3b25", "#76603f", "#a08660", "#c8b089")
FISH = R("#39484f", "#6b7f86", "#a9babd", "#e2ebe8")
PAPER = R("#8a8067", "#bdb398", "#e3dcc5", "#faf6e8")
INKWASH = R("#2e3b44", "#56656c", "#8b979a")
WATER = R("#1c5560", "#2e8288", "#5fb7b0", "#b3e3da", "#f4fffb")
MIST = hexc("#eef4f2")
FLOWER = R("#e9e2c9", "#f6d25e", "#d86f93", "#9e7ad6")
WARM = R("#8a3c12", "#e07a2a", "#ffc25a", "#fff1bf")


def ink_of(r):
    return mix(r[0], INK, 0.5)


def finish(cv, *ramps, close_edges=True, skip=None, inks=None, cap=16):
    """Silhouette outline, snapped to one dark ink per material ramp, then near-duplicate shades are
    merged (cap_colours) so a sprite keeps a small purposeful palette."""
    if cap:
        cap_colours(cv, cap)
    out = outline(cv, close_edges=close_edges, skip=skip)
    ink = np.array(inks if inks is not None else [ink_of(r) for r in ramps], float)
    if len(ink) and out.any():
        cols = cv.rgb[out]
        d = ((cols[:, None, :] - ink[None, :, :]) ** 2).sum(-1)
        cv.rgb[out] = ink[d.argmin(1)]
    return cv


def cap_colours(cv, max_n=16, max_dist=34.0):
    """Merge near-duplicate opaque colours (rarer into commoner, closest pairs first) until at most
    max_n remain or the closest pair is further apart than max_dist. Deterministic; accents that are
    far from everything else are never merged."""
    solid = cv.a >= 0.999
    cols = np.round(cv.rgb[solid]).astype(int)
    if len(cols) == 0:
        return cv
    uniq, inv, counts = np.unique(cols, axis=0, return_inverse=True, return_counts=True)
    target = np.arange(len(uniq))
    alive = list(range(len(uniq)))
    counts = counts.astype(float)
    while len(alive) > max_n:
        a_ = np.array(alive)
        pts = uniq[a_].astype(float)
        d = np.sqrt(((pts[:, None, :] - pts[None, :, :]) ** 2).sum(-1))
        d[np.arange(len(a_)), np.arange(len(a_))] = 1e9
        i, j = np.unravel_index(np.argmin(d), d.shape)
        if d[i, j] > max_dist:
            break
        keep, drop = (a_[i], a_[j]) if counts[a_[i]] >= counts[a_[j]] else (a_[j], a_[i])
        target[target == drop] = keep
        counts[keep] += counts[drop]
        alive.remove(drop)
    cv.rgb[solid] = uniq[target[inv.ravel()]]
    return cv


def cshadow(cv, cx, gy, rx, ry=1.5, a=0.3):
    """Soft contact shadow on the ground line (translucent, drawn under the sprite)."""
    m = m_ellipse(cv.w, cv.h, cx, gy, rx, ry)
    cv.fill(m & (cv.a < 0.5), INK, a)


def flat(cv, m, c, a=1.0):
    cv.fill(m, c, a)


def idx_paint(cv, m, pal, v):
    """Paint a float ramp index field v (floored, clipped) into mask m."""
    idx = np.clip(np.floor(v), 0, len(pal) - 1).astype(int)
    cv.fill_idx(m, idx, pal)


def run_u(m):
    """Horizontal position of each pixel within its row run (0 left edge .. 1 right edge)."""
    h, w = m.shape
    u = np.zeros((h, w))
    for y in range(h):
        xs = np.nonzero(m[y])[0]
        if len(xs) == 0:
            continue
        runs = np.split(xs, np.nonzero(np.diff(xs) > 1)[0] + 1)
        for r in runs:
            u[y, r] = (r - r[0]) / max(1, r[-1] - r[0])
    return u


def depth_top(m):
    d = np.zeros(m.shape, float)
    for y in range(1, m.shape[0]):
        d[y] = np.where(m[y] & m[y - 1], d[y - 1] + 1, 0)
    return d


def thick_line(W, H, pts, w0, w1):
    """Tapering stroke along a polyline (w0 at the start, w1 at the end)."""
    m = np.zeros((H, W), bool)
    n = len(pts) - 1
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for s in range(steps + 1):
            t = s / max(1, steps)
            gt = (i + t) / n
            r = (w0 + (w1 - w0) * gt) / 2.0
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            m |= m_ellipse(W, H, x, y, max(0.5, r), max(0.5, r))
    return m


def bark(cv, m, pal=BARK, seed="bark", gain=1.0):
    """Cylindrical bark: lit left, grooves (vertical dark streaks) and a bright left rim."""
    W, H = cv.w, cv.h
    u = run_u(m)
    nz = vnoise(W, H, 2, seed_of(seed), 2)
    xx, yy = grid(W, H)
    groove = vnoise(W, H * 3, 2, seed_of(seed, "g"), 1)[::3] > 0.62
    v = (len(pal) - 0.01) * (0.95 - u * 0.85 * gain) - groove * 1.0 + (nz - 0.5) * 0.6
    idx_paint(cv, m, pal, v)
    cv.fill(left_edge(m) & ~top_edge(m), pal[-1])


def leaf_clump(cv, cx, cy, rx, ry, pal, seed, lvl=0.0, lit=0.0):
    """Leafy cluster: shaded ellipse with a bumpy rim, lit upper-left, leaf flecks."""
    W, H = cv.w, cv.h
    g = rng("clump", seed)
    xx, yy = grid(W, H)
    m = m_ellipse(W, H, cx, cy, rx, ry)
    for k in range(int(g.integers(4, 8))):
        a = g.uniform(math.pi, 2 * math.pi) if k % 2 == 0 else g.uniform(0, 2 * math.pi)
        m |= m_ellipse(W, H, cx + math.cos(a) * rx * 0.8, cy + math.sin(a) * ry * 0.8, rx * 0.42, ry * 0.42)
    n = len(pal)
    d = (xx - cx) / max(1, rx) + (yy - cy) / max(1, ry)
    v = (n - 1) * 0.5 + lvl - d * 0.9 + lit
    idx_paint(cv, m, pal, v)
    fl = m & erode(m) & (vnoise(W, H, 1.5, seed_of("fl", seed), 1) > 0.72)
    cv.fill(fl & (d < 0.2), pal[min(n - 1, int((n - 1) * 0.5 + lvl + 1.5 + lit))])
    cv.fill(fl & (d >= 0.2), pal[max(0, int((n - 1) * 0.5 + lvl - 1 + lit))])
    return m


# ================================================================== trees
@prop("willow_tree", 110, 150)
def willow_tree(state, f):
    W, H = 110, 150
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    g = rng("willow_tree")
    gy = 147
    cshadow(cv, 55, gy, 30, 2.2)
    n = len(WILLOW)
    cx, top = 57, 16
    # hanging curtains: back drapes first
    drapes = [(79, top + 18, 23, 66, -1.3, 1), (34, top + 20, 23, 64, -1.1, 2), (cx, top + 2, 36, 84, -0.6, 3),
              (41, top + 24, 21, 70, 0.2, 4), (72, top + 26, 19, 64, 0.4, 5)]

    def drape(dcx, dtop, dhw, ln0, lvl, sd):
        gg = rng("wdr", sd)
        cols = np.arange(W)
        t = np.abs(cols - dcx) / dhw
        inside = t < 1
        ttop = np.round(dtop + (1 - np.sqrt(np.clip(1 - t ** 2, 0, 1))) * dhw * 0.6)
        rnd = gg.random(W)
        ln = ln0 * np.sqrt(np.clip(1 - t ** 3, 0, 1)) * (0.72 + 0.4 * rnd)
        ln = np.where(rnd < 0.26, ln * 0.55, ln)
        bot = np.round(ttop + ln)
        m = inside[None, :] & (yy >= ttop[None, :]) & (yy <= bot[None, :])
        dd = (yy - ttop[None, :]) / np.maximum(1, ln)[None, :]
        rel = (cols - cx) / 45.0
        v = (n - 1) * 0.55 + lvl - rel[None, :] * 1.2 - dd * 1.7
        v = v - ((cols + sd) % 3 == 0)[None, :] * (dd > 0.18) * 1.0
        v = v + (dd < 0.06) * 1.2
        idx_paint(cv, m, WILLOW, v)
        # strand tips curl outward a pixel
        for x in np.nonzero(inside)[0]:
            b = int(bot[x])
            if 0 <= b + 1 < H and gg.random() < 0.5:
                sx = x + (1 if x > cx else -1)
                if 0 <= sx < W:
                    cv.put(sx, b + 1, WILLOW[max(0, int((n - 1) * 0.35 + lvl))])
        # leafy dome bumps on top
        k = -dhw * 0.85
        while k < dhw * 0.85:
            bx = int(round(dcx + k))
            if 0 <= bx < W:
                leaf_clump(cv, bx, int(ttop[bx]) + 2, 4.5, 3, WILLOW, ("wbump", sd, int(k)), lvl=lvl + 0.4,
                           lit=-(bx - cx) / 45.0)
            k += g.uniform(5, 7)

    for d in drapes[:3]:
        drape(*d)
    # trunk with root flare, fork and arms
    trunk = m_poly(W, H, [(44, gy), (68, gy), (62, gy - 5), (61, 118), (63, 96), (60, 80), (52, 80), (51, 100),
                          (49, 120), (49, gy - 5)])
    arms = [[(56, 84), (46, 62), (30, 44), (18, 38)], [(57, 84), (54, 58), (48, 34)], [(57, 84), (66, 60), (80, 38),
                                                                                         (92, 34)]]
    for a in arms:
        trunk |= thick_line(W, H, a, 6, 2)
    bark(cv, trunk, BARK, "willow_bark")
    cv.fill(m_rect(W, H, 44, gy - 1, 68, gy) & trunk, BARK[0])
    for d in drapes[3:]:
        drape(*d)
    finish(cv, WILLOW, BARK)
    return cv


@prop("pine_tree", 100, 150)
def pine_tree(state, f):
    W, H = 100, 150
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    g = rng("pine_tree")
    gy = 147
    cshadow(cv, 46, gy, 24, 2.0)
    spine = [(44, gy), (42, 124), (48, 100), (56, 80), (54, 58), (60, 36), (62, 18)]
    trunk = thick_line(W, H, spine, 10, 3)
    trunk |= m_poly(W, H, [(34, gy), (56, gy), (50, gy - 6), (40, gy - 6)])
    branches = [((46, 104), (16, 92), 1), ((53, 86), (82, 76), 1), ((55, 64), (22, 52), 1), ((57, 50), (84, 40), 1),
                ((60, 34), (34, 24), 1), ((61, 24), (78, 16), 1)]
    for (a, b, _) in branches:
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - 3)
        trunk |= thick_line(W, H, [a, mid, b], 4, 1.5)
    bark(cv, trunk, BARK, "pine_bark")
    # needle pads: flat cloud-like clusters, lit tops, dark undersides, needle strokes
    n = len(PINE)
    pads = [(16, 90, 17), (82, 74, 15), (22, 50, 16), (84, 38, 13), (34, 22, 13), (78, 14, 11), (62, 12, 12),
            (46, 70, 9), (68, 28, 9)]
    for i, (px, py, pw) in enumerate(sorted(pads, key=lambda p: -p[1])):
        pm = np.zeros((H, W), bool)
        for j in range(4):
            ox = (j - 1.5) * pw * 0.42 + g.uniform(-1, 1)
            pm |= m_ellipse(W, H, px + ox, py - (1.5 if j in (1, 2) else 0), pw * 0.36, pw * 0.2 + 1.2)
        pm &= yy <= py + pw * 0.16
        dtop = depth_top(pm)
        rel = (px - 50) / 40.0
        v = (n - 1) * 0.55 - rel * 0.7 - dtop * 0.45 + (dtop < 1) * 1.2
        needles = (xx + (yy * 2)) % 3 == 0
        v = v - (needles & (dtop >= 1) & (dtop < 3)) * 0.8
        idx_paint(cv, pm, PINE, v)
        cv.fill(bottom_edge(pm), PINE[0])
        cv.fill(top_edge(pm) & (xx < px + pw * 0.2), PINE[-1])
    finish(cv, PINE, BARK)
    return cv


@prop("bamboo_cluster", 70, 160)
def bamboo_cluster(state, f):
    W, H = 70, 160
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    g = rng("bamboo_cluster")
    gy = 157
    cshadow(cv, 35, gy, 24, 2.0)
    culms = [(30, 6, 5, -3), (42, 16, 4, 5), (22, 34, 4, -8), (52, 44, 3, 9), (36, 60, 3, 2), (14, 70, 3, -10),
             (58, 88, 3, 7)]
    n = len(BAMBOO)
    for i, (bx, top, wd, lean) in enumerate(culms):
        m = np.zeros((H, W), bool)
        for y in range(top, gy + 1):
            t = (y - top) / max(1, gy - top)
            x = bx + lean * (1 - t) ** 1.6
            x0 = int(round(x - wd / 2))
            m[y, max(0, x0):min(W, x0 + wd)] = True
        u = run_u(m)
        v = (n - 0.01) * (0.9 - u * 0.75) - (i >= 4) * 0.8
        idx_paint(cv, m, BAMBOO, v)
        off = int(g.integers(0, 12))
        ring = m & (((yy - top + off) % 13) == 0)
        cv.fill(ring, BAMBOO[0])
        cv.fill(shift(ring, 0, -1) & m & (u < 0.7), BAMBOO[-1])
        # leaf sprays along the upper culm
        for k in range(3 if i < 4 else 2):
            ly = top + int((gy - top) * g.uniform(0.02, 0.45))
            t = (ly - top) / max(1, gy - top)
            lx = bx + lean * (1 - t) ** 1.6
            side = -1 if (k + i) % 2 == 0 else 1
            twig_end = (lx + side * 5, ly - 3)
            cv.fill(m_line(W, H, [(lx, ly), twig_end]), BAMBOO_LEAF[1])
            for j in range(5):
                ang = 0.35 + j * 0.28 + g.uniform(-0.08, 0.08)
                ln = g.uniform(8, 12)
                ex = twig_end[0] + side * math.cos(ang) * ln
                ey = twig_end[1] + math.sin(ang) * ln
                mx = twig_end[0] + side * math.cos(ang - 0.25) * ln * 0.5
                my = twig_end[1] + math.sin(ang - 0.25) * ln * 0.5
                lm = m_curve(W, H, [twig_end, (mx, my), (ex, ey)])
                lm |= shift(m_curve(W, H, [(twig_end[0] + side, twig_end[1]), (mx, my + 0.6),
                                           ((mx + ex) / 2, (my + ey) / 2 + 0.3)]), 0, 0)
                cv.fill(lm, BAMBOO_LEAF[1 + (j % 3)])
                cv.fill(top_edge(lm) & ~shift(lm, 0, 1), BAMBOO_LEAF[min(3, 2 + (j % 2))])
    # young shoots and fallen leaves at the base
    for (sx, sh_) in ((24, 9), (47, 7)):
        shoot = m_poly(W, H, [(sx - 2, gy), (sx + 2, gy), (sx, gy - sh_)])
        cv.fill(shoot, WOOD_DRY[2])
        cv.fill(left_edge(shoot), WOOD_DRY[3])
    finish(cv, BAMBOO, BAMBOO_LEAF)
    return cv


@prop("plum_tree", 100, 130)
def plum_tree(state, f):
    W, H = 100, 130
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    g = rng("plum_tree")
    gy = 127
    cshadow(cv, 48, gy, 24, 2.0)
    # angular, zig-zag plum limbs
    limbs = [[(46, gy), (44, 108), (50, 92), (46, 78)], [(46, 80), (32, 66), (34, 52), (18, 40), (12, 26)],
             [(47, 80), (60, 62), (56, 48), (70, 34), (84, 26)], [(34, 54), (44, 40), (40, 24), (48, 12)],
             [(60, 62), (78, 58), (92, 48)], [(18, 40), (8, 44)], [(70, 34), (66, 18), (72, 8)],
             [(44, 40), (28, 30)]]
    wood = np.zeros((H, W), bool)
    widths = [8, 5, 5, 3, 3, 2, 2, 2]
    for lb, wd in zip(limbs, widths):
        wood |= thick_line(W, H, lb, wd, max(1, wd * 0.45))
    wood |= m_poly(W, H, [(38, gy), (56, gy), (50, gy - 5), (44, gy - 5)])
    bark(cv, wood, PLUM_BARK, "plum_bark")
    # blossoms: 5-petal clusters along the limbs (upper side), a few open flowers + buds
    n = len(BLOSSOM)
    pts = []
    for lb in limbs[1:]:
        for i in range(len(lb) - 1):
            (x0, y0), (x1, y1) = lb[i], lb[i + 1]
            for t in np.linspace(0, 1, 5):
                pts.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    for i, (px, py) in enumerate(pts):
        if g.random() < 0.72:
            bx = int(round(px + g.uniform(-3, 3)))
            by = int(round(py + g.uniform(-4, 1)))
            big = g.random() < 0.45
            if big:
                pm = m_rect(W, H, bx - 1, by, bx + 1, by) | m_rect(W, H, bx, by - 1, bx, by + 1)
                cv.fill(pm, BLOSSOM[2])
                cv.put(bx - 1, by, BLOSSOM[3])
                cv.put(bx, by - 1, BLOSSOM[3])
                cv.put(bx + 1, by + 1, BLOSSOM[1])
                cv.put(bx, by, GOLD[3])
            else:
                cv.put(bx, by, BLOSSOM[1 + int(g.integers(0, 3))])
                cv.put(bx + 1, by, BLOSSOM[1])
    # fallen petals
    for i in range(10):
        cv.put(int(g.integers(24, 76)), int(g.integers(gy - 1, gy + 1)), BLOSSOM[2])
    finish(cv, PLUM_BARK, BLOSSOM)
    return cv


@prop("dead_tree_grey", 90, 130)
def dead_tree_grey(state, f):
    W, H = 90, 130
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    g = rng("dead_tree_grey")
    gy = 127
    cshadow(cv, 44, gy, 22, 2.0, a=0.25)
    wood = np.zeros((H, W), bool)

    def limb(x0, y0, ang, ln, wd, depth):
        x1, y1 = x0 + math.cos(ang) * ln, y0 + math.sin(ang) * ln
        mx, my = (x0 + x1) / 2 + g.uniform(-3, 3), (y0 + y1) / 2 + g.uniform(-2, 2)
        nonlocal wood
        wood |= thick_line(W, H, [(x0, y0), (mx, my), (x1, y1)], wd, max(1, wd * 0.6))
        if depth > 0:
            for k in range(2):
                na = ang + (-0.55 if k == 0 else 0.5) + g.uniform(-0.25, 0.25)
                na = min(-0.2, max(-math.pi + 0.2, na))
                limb(x1, y1, na, ln * g.uniform(0.55, 0.72), max(1, wd * 0.6), depth - 1)

    wood |= m_poly(W, H, [(34, gy), (56, gy), (50, gy - 6), (48, 80), (42, 72), (40, 96), (38, gy - 6)])
    limb(45, 76, -1.95, 30, 6, 3)
    limb(46, 76, -1.1, 28, 5, 3)
    limb(42, 92, -2.7, 18, 3, 2)
    # hollow knot and cracks
    bark(cv, wood, HOLLOW, "dead_bark", gain=0.9)
    knot = m_ellipse(W, H, 46, 104, 2.5, 4)
    cv.fill(knot, HOLLOW[0])
    cv.fill(left_edge(knot), HOLLOW[1])
    for (x0, y0, x1, y1) in ((41, 118, 43, 108), (50, 100, 49, 88)):
        cv.fill(m_line(W, H, [(x0, y0), (x1, y1)]) & wood, HOLLOW[1])
    # grey wisps hanging from the limbs
    for (wx, wy) in ((24, 40), (70, 34), (58, 52)):
        cv.fill(m_line(W, H, [(wx, wy), (wx + 1, wy + 6), (wx, wy + 10)]), HOLLOW[3], 0.6)
    finish(cv, HOLLOW)
    return cv


# ================================================================== rocks
def boulder(cv, cx, by, rx, ry, pal, seed, facets=3, rough=0.14, moss=None, moss_amt=0.0):
    W, H = cv.w, cv.h
    xx, yy = grid(W, H)
    g = rng("bld", seed)
    cy = by - ry + 1
    th = np.arctan2((yy - cy) / ry, (xx - cx) / rx)
    r = np.ones_like(th)
    for k in range(2, 6):
        r += rough / (k - 1) * g.uniform(-1, 1) * np.cos(k * th + g.uniform(0, 6.283))
    m = (((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= r * r) & (yy <= by)
    rid = np.zeros((H, W), int)
    for i in range(facets):
        px = cx + g.uniform(-rx * 0.4, rx * 0.4)
        py = cy + g.uniform(-ry * 0.4, ry * 0.3)
        ang = g.uniform(0, math.pi)
        rid = rid * 2 + (((xx - px) * math.sin(ang) - (yy - py) * math.cos(ang)) > 0)
    n = len(pal)
    v = np.zeros((H, W))
    for rv in np.unique(rid[m]):
        reg = m & (rid == rv)
        ys, xs = np.nonzero(reg)
        v[reg] = (n - 1) * 0.5 - (xs.mean() - cx) / rx * 1.4 - (ys.mean() - cy) / ry * 1.2 + g.uniform(-0.3, 0.3)
    dt = depth_top(m)
    v = v + (dt < 1) * 1.0
    idx_paint(cv, m, pal, v + 0.5)
    cv.fill(bottom_edge(m), pal[0])
    cv.fill(left_edge(m) & (dt > 0), pal[-2])
    # pits and glints
    for _ in range(int(rx * ry / 18)):
        px, py = int(g.integers(int(cx - rx * 0.7), int(cx + rx * 0.7))), int(g.integers(int(cy - ry * 0.6), by - 1))
        if 0 < px < W - 1 and 0 < py < H - 1 and erode(m)[py, px]:
            cv.put(px, py, pal[max(0, int(v[py, px] + 0.5) - 1)])
    if moss is not None and moss_amt > 0:
        nz = vnoise(W, H, 4, seed_of("bm", seed), 2)
        band = m & (dt <= 1 + nz * 4 * moss_amt) & (nz > 1 - moss_amt)
        mi = np.where(dt[band] < 1, len(moss) - 1, np.where(dt[band] < 3, len(moss) - 2, 1))
        cv.rgb[band] = np.array(moss, float)[mi]
        cv.a[band] = 1.0
        drip = band & ~shift(band, 0, -1)
        cv.fill(drip & (nz > 0.8), moss[0])
    return m


@prop("rock_small", 32, 20)
def rock_small(state, f):
    cv = Canvas(32, 20)
    cshadow(cv, 16, 17, 14, 1.4)
    boulder(cv, 15, 17, 12, 8, STONE, "rock_small", facets=3)
    boulder(cv, 25, 17, 5, 4, STONE, "rock_small2", facets=2)
    finish(cv, STONE)
    return cv


@prop("rock_large", 70, 45)
def rock_large(state, f):
    cv = Canvas(70, 45)
    W, H = 70, 45
    cshadow(cv, 35, 42, 32, 2)
    boulder(cv, 30, 42, 25, 20, STONE, "rock_large", facets=4, moss=MOSS, moss_amt=0.35)
    boulder(cv, 54, 42, 13, 11, STONE, "rock_large2", facets=3)
    boulder(cv, 12, 42, 7, 5, STONE, "rock_large3", facets=2)
    g = rng("rl_crack")
    xx, yy = grid(W, H)
    for (x0, y0) in ((24, 26), (38, 30)):
        pts = [(x0, y0)]
        for _ in range(5):
            x0 += int(g.integers(-1, 2))
            y0 += 1
            pts.append((x0, y0))
        cv.fill(m_line(W, H, pts) & (cv.a > 0), STONE[1])
    finish(cv, STONE, MOSS)
    return cv


@prop("boulder_moss", 60, 50)
def boulder_moss(state, f):
    W, H = 60, 50
    cv = Canvas(W, H)
    cshadow(cv, 30, 47, 28, 2)
    boulder(cv, 30, 47, 25, 22, STONE, "boulder_moss", facets=3, rough=0.1, moss=MOSS, moss_amt=0.8)
    # ferns at the foot
    g = rng("bm_fern")
    for (fx, side) in ((8, -1), (12, 1), (50, 1), (46, -1), (30, -1)):
        pts = [(fx, 46)]
        for s in range(1, 8):
            pts.append((fx + side * s * 0.9, 46 - math.sin(s / 7 * 2.4) * 7))
        cv.fill(m_line(W, H, [(round(x), round(y)) for x, y in pts]), MOSS[1])
        for (px, py) in pts[1:-1:2]:
            cv.fill(m_ellipse(W, H, px, py - 1, 1.3, 0.9), MOSS[2 + int(g.integers(0, 2))])
    finish(cv, STONE, MOSS)
    return cv


@prop("scholar_rock", 50, 90)
def scholar_rock(state, f):
    """Taihu scholar stone: tall, twisting, pierced by holes, on a carved wooden stand."""
    W, H = 50, 90
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    g = rng("scholar_rock")
    cshadow(cv, 25, 87, 16, 1.5)
    # carved wooden stand
    stand = m_poly(W, H, [(11, 80), (39, 80), (37, 84), (39, 87), (11, 87), (13, 84)])
    idx_paint(cv, stand, WOOD, 2.2 - (yy - 80) / 4.0 + (xx < 20) * 0.8)
    cv.fill(m_rect(W, H, 10, 79, 40, 79), WOOD[3])
    for fx in (14, 35):
        cv.fill(m_rect(W, H, fx, 85, fx + 1, 87), WOOD[0])
    # eroded silhouette: wandering centre, pinched necks, flaring lobes
    ys = np.arange(H)
    c = 25 + 5 * np.sin(ys / 11.0 + 0.8) + 2.5 * np.sin(ys / 4.3)
    w = 6.5 + 4.2 * np.sin(ys / 7.5 + 1.7) ** 2 + 2.0 * np.sin(ys / 3.1)
    w = np.clip(w, 3.0, 12.0)
    edge = vnoise(W, H, 2, seed_of("sre"), 2)
    body = (np.abs(xx - c[:, None]) < w[:, None] + (edge - 0.5) * 3) & (yy >= 5) & (yy <= 78)
    body &= ~((yy < 10) & (np.abs(xx - c[:, None]) > (yy - 4) * 1.4))
    holes = [(c[62] - 1, 62, 2.6, 4.0), (c[46] + 2, 46, 2.4, 3.2), (c[30] - 2, 31, 2.8, 3.6), (c[18] + 1, 18, 1.8, 2.6),
             (c[70] + 4, 71, 1.4, 2.0), (c[38] - 5, 38, 1.2, 1.8)]
    hole_m = np.zeros((H, W), bool)
    for (hx, hy, rx, ry) in holes:
        hole_m |= m_ellipse(W, H, hx, hy, rx, ry)
    hole_m &= erode(erode(body))
    n = len(STONE)
    u = run_u(body)
    nz = vnoise(W, H, 2, seed_of("sr"), 2)
    v = (n - 0.01) * (0.92 - u * 0.8) + (nz - 0.5) * 0.9
    idx_paint(cv, body, STONE, v)
    cv.fill(top_edge(body) & (u < 0.6), STONE[-1])
    cv.erase(hole_m)
    rim = dilate(hole_m) & ~hole_m & body
    cv.fill(rim & shift(hole_m, 0, 1), STONE[0])
    cv.fill(rim & shift(hole_m, 1, 0), STONE[1])
    cv.fill(rim & shift(hole_m, 0, -1), STONE[3])
    for _ in range(18):
        px, py = int(g.integers(12, 38)), int(g.integers(8, 76))
        if erode(body)[py, px] and not dilate(hole_m)[py, px]:
            cv.put(px, py, STONE[1])
            cv.put(px + 1, py + 1, STONE[3])
    finish(cv, STONE, WOOD)
    return cv


# ================================================================== small plants
@prop("bush", 40, 25)
def bush(state, f):
    W, H = 40, 25
    cv = Canvas(W, H)
    cshadow(cv, 20, 22, 18, 1.5)
    g = rng("bush")
    clumps = [(10, 16, 8, 6, -0.4), (30, 16, 8, 6, -0.4), (20, 11, 10, 8, 0.3), (14, 18, 7, 5, 0.0), (27, 18, 7, 5, 0.0)]
    for i, (cx, cy, rx, ry, lvl) in enumerate(clumps):
        leaf_clump(cv, cx, cy, rx, ry, LEAF, ("bush", i), lvl=lvl, lit=-(cx - 20) / 30.0)
    cv.erase(grid(W, H)[1] > 22)
    for (bx, by) in ((12, 10), (24, 7), (31, 12), (18, 15)):
        cv.put(bx, by, FLOWER[0])
    finish(cv, LEAF)
    return cv


@prop("tall_grass", 32, 24, states=(("idle", 2, 3),))
def tall_grass(state, f):
    W, H = 32, 24
    cv = Canvas(W, H)
    g = rng("tall_grass")
    gy = 21
    blades = []
    for i in range(14):
        bx = 3 + i * 1.9 + g.uniform(-0.8, 0.8)
        ht = g.uniform(9, 20)
        lean = g.uniform(-4, 4) + (bx - 16) * 0.2
        blades.append((bx, ht, lean, i))
    blades.sort(key=lambda b: -b[1])
    sway = (1.4 if f == 1 else 0.0)
    for (bx, ht, lean, i) in blades:
        tipx = bx + lean + sway * (ht / 20)
        pts = [(bx, gy), (bx + (tipx - bx) * 0.3, gy - ht * 0.55), (tipx, gy - ht)]
        m = m_curve(W, H, pts)
        c = GRASS[1 + (i % 3)]
        cv.fill(m, c)
        tip = m & (grid(W, H)[1] <= gy - ht + 2)
        cv.fill(tip, GRASS[3 + (i % 2)])
    for (bx, ht) in ((9, 21), (22, 19)):
        tipx = bx + sway
        cv.fill(m_line(W, H, [(bx, gy), (tipx, gy - ht)]), STRAW[2])
        head = m_rect(W, H, int(round(tipx)) - 1, gy - ht - 3, int(round(tipx)), gy - ht)
        cv.fill(head, STRAW[3])
        cv.put(int(round(tipx)) - 1, gy - ht - 3, STRAW[4])
    cv.fill(m_rect(W, H, 2, gy, 29, gy + 1), GRASS[0])
    finish(cv, GRASS, STRAW)
    return cv


@prop("flowers_wild", 32, 12, ground=1, decal=True)
def flowers_wild(state, f):
    W, H = 32, 12
    cv = Canvas(W, H)
    g = rng("flowers_wild")
    # low leaf rosettes
    for i in range(9):
        cx, cy = g.uniform(3, 29), g.uniform(7, 10)
        for k in range(3):
            ang = -2.6 + k * 1.1 + g.uniform(-0.2, 0.2)
            ex, ey = cx + math.cos(ang) * 3.5, cy + math.sin(ang) * 1.6
            cv.fill(m_line(W, H, [(round(cx), round(cy)), (round(ex), round(ey))]), GRASS[1 + (k % 3)])
    # flowers on short stems
    cols = [FLOWER[0], FLOWER[1], FLOWER[2], FLOWER[3], FLOWER[0], FLOWER[2]]
    for i in range(11):
        fx, fy = int(g.integers(3, 29)), int(g.integers(2, 8))
        cv.fill(m_line(W, H, [(fx, fy + 1), (fx, fy + 3)]), GRASS[2])
        c = cols[i % len(cols)]
        for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1)):
            cv.put(fx + dx, fy + dy, c)
        cv.put(fx, fy, FLOWER[1] if c != FLOWER[1] else FLOWER[0])
    finish(cv, GRASS, inks=[ink_of(GRASS)])
    return cv


# ================================================================== fences, walls, cliffs (segments repeat along x)
def wood_rail(cv, x0, x1, y0, y1, pal, seed):
    W, H = cv.w, cv.h
    m = m_rect(W, H, x0, y0, x1, y1)
    xx, yy = grid(W, H)
    v = np.where(yy == y0, len(pal) - 1, np.where(yy == y1, 0.5, len(pal) * 0.55))
    idx_paint(cv, m, pal, v)
    gr = m & (yy > y0) & (yy < y1) & (vnoise(W, H * 4, 3, seed_of(seed), 1)[::4] > 0.66)
    cv.fill(gr, pal[1])
    return m


def wood_post(cv, x0, x1, top, bottom, pal, cap="round"):
    W, H = cv.w, cv.h
    m = m_rect(W, H, x0, top, x1, bottom)
    if cap == "point":
        m &= ~(m_rect(W, H, x0, top, x0, top) | m_rect(W, H, x1, top, x1, top))
    elif cap == "round":
        m[top, x0] = m[top, x1] = False
    u = run_u(m)
    idx_paint(cv, m, pal, (len(pal) - 0.01) * (0.9 - u * 0.75))
    cv.fill(top_edge(m), pal[-1])
    return m


@prop("fence_wood", 80, 28, repeat="x")
def fence_wood(state, f):
    W, H = 80, 28
    cv = Canvas(W, H)
    gy = 25
    xx, yy = grid(W, H)
    for px in (10, 30, 50, 70):
        wood_post(cv, px - 2, px + 1, 3, gy, WOOD_DRY, cap="point")
    for (y0, y1) in ((8, 10), (16, 18)):
        wood_rail(cv, 0, W - 1, y0, y1, WOOD_DRY, ("fw", y0))
    for px in (10, 30, 50, 70):
        for ry in (9, 17):
            cv.put(px - 1, ry, IRON[1])
    # a knot, a split and grass at the posts
    cv.fill(m_line(W, H, [(36, 17), (42, 17)]), WOOD_DRY[1])
    for px in (10, 30, 50, 70):
        for k, dx in enumerate((-3, -2, 2, 3)):
            cv.fill(m_line(W, H, [(px + dx, gy), (px + dx + (1 if dx > 0 else -1), gy - 2 - k % 2)]), GRASS[2 + k % 2])
    finish(cv, WOOD_DRY, GRASS, close_edges=False)
    return cv


@prop("bamboo_fence", 80, 32, repeat="x")
def bamboo_fence(state, f):
    W, H = 80, 32
    cv = Canvas(W, H)
    gy = 29
    xx, yy = grid(W, H)
    n = len(BAMBOO)
    tops = [3, 5, 4, 6, 3, 5, 7, 4, 5, 3, 6, 4, 5, 3, 6, 5, 4, 6, 3, 5]
    for i in range(20):
        x0 = i * 4
        top = tops[i]
        m = m_rect(W, H, x0, top, x0 + 2, gy)
        m[top, x0] = False  # slanted cut
        u = run_u(m)
        idx_paint(cv, m, BAMBOO, (n - 0.01) * (0.85 - u * 0.7) - (i % 3 == 1) * 0.6)
        cv.put(x0 + 1, top, BAMBOO[-1])
        cv.put(x0 + 2, top, BAMBOO[1])
        for ny in (top + 6 + i % 3, top + 16 + i % 2):
            if ny < gy - 1:
                cv.fill(m_rect(W, H, x0, ny, x0 + 2, ny), BAMBOO[0])
                cv.put(x0, ny + 1, BAMBOO[-1])
    # split-bamboo rails with rope lashings
    for ry in (10, 21):
        rail = m_rect(W, H, 0, ry, W - 1, ry + 2)
        idx_paint(cv, rail, BAMBOO, np.where(yy == ry, n - 1, np.where(yy == ry + 2, 1, 2.5)))
        for lx in range(5 + (ry % 2) * 8, W, 16):
            tie = m_rect(W, H, lx, ry - 1, lx + 1, ry + 3)
            cv.fill(tie, ROPE[0])
            cv.put(lx, ry, ROPE[2])
            cv.put(lx + 1, ry + 2, ROPE[1])
    finish(cv, BAMBOO, ROPE, close_edges=False)
    return cv


@prop("stone_wall_low", 96, 28, repeat="x")
def stone_wall_low(state, f):
    W, H = 96, 28
    cv = Canvas(W, H)
    gy = 25
    xx, yy = grid(W, H)
    g = rng("stone_wall_low")
    n = len(STONE_W)
    courses = [(10, 16, [14, 11, 16, 9, 13, 15, 18]), (17, 25, [9, 17, 12, 15, 10, 20, 13])]
    for ci, (y0, y1, widths) in enumerate(courses):
        x = (ci * 7) % W
        for bi, bw in enumerate(widths):
            m = np.zeros((H, W), bool)
            for dx in range(bw - 1):
                m[y0 + 1:y1 + 1, (x + dx) % W] = True
            m[y0 + 1, x % W] = False
            m[y0 + 1, (x + bw - 2) % W] = False
            lvl = g.uniform(-0.6, 0.6)
            v = (n - 1) * 0.5 + lvl - (yy - y0) / (y1 - y0) * 1.0 + ((xx - x) % W < 2) * 0.8
            idx_paint(cv, m, STONE_W, v)
            cv.fill(m & (yy == y0 + 1) & ((xx - x) % W < bw - 3), STONE_W[-1])
            x += bw
    # coping slabs on top
    x = 3
    for bi, bw in enumerate([20, 26, 22, 28]):
        m = np.zeros((H, W), bool)
        for dx in range(bw - 1):
            m[5:10, (x + dx) % W] = True
        idx_paint(cv, m, STONE_W, (n - 1) * 0.55 + (yy == 5) * 1.5 - (yy >= 9) * 1.2)
        x += bw
    # joints (mortar gaps) and moss
    nz = vnoise(W, H, 4, seed_of("swl_moss"), 1, wrap=True)
    moss = (cv.a > 0) & ((yy == 5) | (yy == 6)) & (nz > 0.62)
    cv.fill(moss, MOSS[2])
    cv.fill(moss & (yy == 5), MOSS[3])
    drip = (cv.a > 0) & (yy > 6) & (yy < 14) & shift(moss, 0, 1) & (nz > 0.7)
    cv.fill(drip, MOSS[1])
    for gx in range(4, W, 12):
        cv.fill(m_line(W, H, [(gx, gy), (gx - 1, gy - 3)]), GRASS[2])
        cv.fill(m_line(W, H, [(gx + 2, gy), (gx + 3, gy - 2)]), GRASS[3])
    finish(cv, STONE_W, MOSS, close_edges=False)
    return cv


def rock_face(cv, m, pal, seed, flute=5, ledges=6, moss=None):
    """Fluted cliff rock: vertical light/dark columns, strata, ledges with moss, cracks."""
    W, H = cv.w, cv.h
    xx, yy = grid(W, H)
    g = rng("rockface", seed)
    n = len(pal)
    col = vnoise(W * 4, H, flute * 4, seed_of(seed, "fl"), 2)[:, ::4]
    u = run_u(m)
    dt = depth_top(m)
    v = (n - 1) * 0.5 + (col - 0.5) * 2.4 + (0.5 - u) * 1.3 + (dt < 2) * 1.0
    idx_paint(cv, m, pal, v)
    edge = (col > np.roll(col, 1, axis=1) + 0.02) & m & ~left_edge(m)
    cv.fill(edge & (col > 0.55), pal[-1])
    strata = m & ((yy + (col * 4).astype(int)) % 12 == 0) & (vnoise(W, H, 8, seed_of(seed, "st"), 1) > 0.45) & (dt > 3)
    cv.fill(strata, pal[1])
    for _ in range(ledges):
        ys, xs = np.nonzero(m & (dt > 8) & (u > 0.1) & (u < 0.9))
        if not len(xs):
            break
        i = int(g.integers(0, len(xs)))
        ly, lx = int(ys[i]), int(xs[i])
        ln = int(g.integers(6, 16))
        seg = m_rect(W, H, lx, ly, lx + ln, ly) & m
        cv.fill(seg, pal[-1])
        cv.fill(shift(seg, 0, 1) & m, pal[0])
        if moss is not None:
            tuft = m_rect(W, H, lx + 1, ly - 1, lx + ln - 2, ly - 1) & (vnoise(W, H, 2, seed_of(seed, lx), 1) > 0.4)
            cv.fill(tuft, moss[2])
            cv.fill(tuft & (xx % 3 == 0), moss[3])
    return m


@prop("cliff_face", 160, 180)
def cliff_face(state, f):
    W, H = 160, 180
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    g = rng("cliff_face")
    gy = 177
    ys = np.arange(H)
    jl = (vnoise(1, H, 6, seed_of("cfl"), 2)[:, 0] - 0.5) * 12
    jr = (vnoise(1, H, 6, seed_of("cfr"), 2)[:, 0] - 0.5) * 12
    left = 12 + jl - np.clip((ys - 150) / 27.0, 0, 1) * 8
    right = 148 + jr + np.clip((ys - 150) / 27.0, 0, 1) * 8
    crest = 10 + (vnoise(W, 1, 12, seed_of("cfc"), 2)[0] - 0.5) * 8
    m = (xx >= left[:, None]) & (xx <= right[:, None]) & (yy >= crest[None, :]) & (yy <= gy)
    cshadow(cv, 80, gy, 72, 2)
    rock_face(cv, m, STONE, "cliff_face", flute=6, ledges=9, moss=MOSS)
    # grassy crest with overhanging turf and a few shrubs
    top = m & (depth_top(m) < 3)
    cv.fill(top, MOSS[2])
    cv.fill(top_edge(m), MOSS[3])
    cv.fill(top & (depth_top(m) == 2) & (vnoise(W, H, 2, seed_of("cft"), 1) > 0.5), MOSS[1])
    for (bx, br) in ((30, 5), (72, 4), (118, 6)):
        leaf_clump(cv, bx, int(crest[bx]) - 1, br, br * 0.7, LEAF, ("cfb", bx), lvl=0.2)
    # hanging vines
    for vx in (22, 26, 96, 101, 138):
        y0 = int(crest[vx]) + 2
        ln = int(g.integers(20, 55))
        pts = [(vx, y0), (vx + 1, y0 + ln * 0.5), (vx, y0 + ln)]
        vm = m_curve(W, H, pts)
        cv.fill(vm, LEAF[2])
        for k in range(y0 + 3, y0 + ln, 4):
            cv.put(vx - 1 + (k // 4) % 3, k, LEAF[3])
    # dark cave crack
    crack = m_poly(W, H, [(70, 120), (78, 118), (80, 150), (74, gy - 4), (68, gy - 4), (72, 150)])
    cv.fill(crack & m, STONE[0])
    cv.fill(left_edge(crack) & m, STONE[1])
    finish(cv, STONE, LEAF)
    return cv


@prop("cliff_ledge", 128, 48)
def cliff_ledge(state, f):
    W, H = 128, 48
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    top = 9
    under = 12 + 34 * (1 - (np.abs(np.arange(W) - 60) / 62.0) ** 1.6)
    under += (vnoise(W, 1, 5, seed_of("cle"), 2)[0] - 0.5) * 8
    left = 3 + (vnoise(1, H, 4, seed_of("cll"), 1)[:, 0] - 0.5) * 4
    right = 124 + (vnoise(1, H, 4, seed_of("clr"), 1)[:, 0] - 0.5) * 4
    m = (yy >= top) & (yy <= np.minimum(under, 46)[None, :]) & (xx >= left[:, None]) & (xx <= right[:, None])
    rock_face(cv, m, STONE, "cliff_ledge", flute=4, ledges=3, moss=MOSS)
    lip = m & (yy <= top + 2)
    cv.fill(lip, MOSS[2])
    cv.fill(lip & (yy == top), MOSS[3])
    cv.fill(lip & (yy == top + 2) & (vnoise(W, H, 2, seed_of("clm"), 1) > 0.45), MOSS[1])
    for gx in range(6, 122, 7):
        cv.fill(m_line(W, H, [(gx, top), (gx + 1, top - 2)]), GRASS[3])
    # roots dangling below
    for rx in (30, 58, 88):
        ln = 6 + rx % 5
        cv.fill(m_line(W, H, [(rx, int(under[rx]) - 2), (rx + 1, int(under[rx]) + ln)]), BARK[2])
    finish(cv, STONE, MOSS)
    return cv


# ================================================================== bridge, dock, mooring
@prop("wooden_bridge", 160, 45, ground=2)
def wooden_bridge(state, f):
    W, H = 160, 45
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 43
    deck_y = 18
    n = len(WOOD)
    # trestle legs and cross braces under the deck (behind)
    for lx in (14, 58, 102, 146):
        leg = m_rect(W, H, lx - 2, deck_y + 4, lx + 1, gy)
        idx_paint(cv, leg, WOOD, (n - 0.01) * (0.8 - run_u(leg) * 0.6) - (yy > gy - 5) * 1.5)
    for (a, b) in ((14, 58), (58, 102), (102, 146)):
        cv.fill(m_line(W, H, [(a, deck_y + 6), (b, gy - 6)], 2), WOOD[1])
        cv.fill(m_line(W, H, [(b, deck_y + 6), (a, gy - 6)], 2), WOOD[1])
    # deck beam with plank ends
    deck = m_rect(W, H, 2, deck_y, W - 3, deck_y + 4)
    idx_paint(cv, deck, WOOD, np.where(yy == deck_y, n - 1, np.where(yy == deck_y + 4, 0.5, 2.6)))
    cv.fill(deck & (yy > deck_y) & (yy < deck_y + 4) & (xx % 6 == 0), WOOD[1])
    cv.fill(deck & (yy == deck_y + 1) & (xx % 6 == 1), WOOD[4])
    # railing: posts, top rail and middle rail
    for px in range(6, W - 4, 16):
        wood_post(cv, px - 1, px + 1, 5, deck_y - 1, WOOD, cap="round")
        cv.put(px, 4, WOOD[4])
    wood_rail(cv, 4, W - 5, 7, 8, WOOD, "br_top")
    wood_rail(cv, 4, W - 5, 12, 12, WOOD, "br_mid")
    # iron straps at the joints
    for px in range(6, W - 4, 16):
        cv.put(px, 12, IRON[2])
    finish(cv, WOOD)
    # waterline marks on the legs (not outlined)
    for lx in (14, 58, 102, 146):
        cv.fill(m_rect(W, H, lx - 6, gy - 1, lx + 5, gy - 1) & ~cv.solid, WATER[3], 0.7)
    return cv


@prop("dock_planks", 128, 20, ground=0, repeat="x", decal=True)
def dock_planks(state, f):
    W, H = 128, 20
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    g = rng("dock_planks")
    n = len(WOOD_DRY)
    for i in range(16):
        x0 = i * 8
        y0 = int(g.integers(0, 2))
        y1 = H - 1 - int(g.integers(0, 2))
        if i == 11:  # a missing board shows the stringers and water beneath
            cv.fill(m_rect(W, H, x0, 1, x0 + 6, H - 2), WATER[1])
            cv.fill(m_rect(W, H, x0, 4, x0 + 6, 5) | m_rect(W, H, x0, 14, x0 + 6, 15), WOOD[1])
            cv.fill(m_rect(W, H, x0, 7, x0 + 3, 7), WATER[2])
            continue
        m = m_rect(W, H, x0, y0, x0 + 6, y1)
        lvl = g.uniform(-0.7, 0.5)
        v = (n - 1) * 0.55 + lvl + (xx == x0) * 1.0 - (xx == x0 + 6) * 1.0
        gr = vnoise(W * 3, H, 2, seed_of("dpg", i), 1)[:, ::3] > 0.64
        v = v - gr * 0.9
        idx_paint(cv, m, WOOD_DRY, v)
        cv.fill(m & ((yy == 4) | (yy == 15)) & ((xx - x0 == 2) | (xx - x0 == 4)), IRON[1])
        cv.fill(m & ((yy == y0) | (yy == y1)), WOOD_DRY[1])
    finish(cv, WOOD_DRY, close_edges=False)
    return cv


@prop("mooring_post", 12, 36)
def mooring_post(state, f):
    W, H = 12, 36
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 33
    cshadow(cv, 6, gy, 5, 1.2)
    post = m_rect(W, H, 3, 4, 8, gy)
    post[4, 3] = post[4, 8] = False
    u = run_u(post)
    idx_paint(cv, post, WOOD, (len(WOOD) - 0.01) * (0.85 - u * 0.75) - (yy > gy - 7) * 1.4)
    cv.fill(top_edge(post), WOOD[4])
    cv.fill(m_rect(W, H, 3, 7, 8, 7), IRON[2])
    cv.fill(m_rect(W, H, 3, 8, 8, 8), IRON[1])
    # rope coil wrapped under the cap, loose end trailing
    for k, ry in enumerate((11, 13, 15)):
        coil = m_rect(W, H, 2, ry, 9, ry + 1)
        cv.fill(coil, ROPE[2])
        cv.fill(coil & (yy == ry) & (xx % 2 == k % 2), ROPE[3])
        cv.fill(coil & (yy == ry + 1) & (xx > 6), ROPE[1])
    cv.fill(m_line(W, H, [(9, 16), (10, 20), (9, 24)]), ROPE[2])
    # algae line at the waterline
    cv.fill(m_rect(W, H, 3, gy - 6, 8, gy - 5), MOSS[1])
    cv.fill(m_rect(W, H, 3, gy - 6, 5, gy - 6), MOSS[2])
    finish(cv, WOOD, ROPE)
    return cv


# ================================================================== sect architecture
JADE_TILE6 = R("#0a2a2d", "#135650", "#1f7b6c", "#2e9c83", "#5cc9a8", "#aee9d0")
STONE_P = R("#48504c", "#6c746d", "#949a90", "#bcbfb2", "#e0e0d2")
GOLD_ACC = R("#7a4f1c", "#d6a443", "#f7dc8e")


def glazed_roof(cv, x0, x1, y_ridge, y_eave, seed, pal=JADE_TILE6, curl=3, thick=3):
    """Glazed-tile roof (side view) using the shared roof helper, then snap its gold tips to GOLD_ACC."""
    from parts import roof_side
    before = cv.solid.copy()
    m = roof_side(cv, x0, x1, y_ridge, y_eave, seed, pal=pal, curl=curl, thick=thick, finials=True)
    new = cv.solid & ~before
    # the helper's gold tips / ridge accents use the global gold ramp: snap them to our accent
    gold_like = new & (cv.rgb[..., 0] > cv.rgb[..., 2] + 40)
    cv.rgb[gold_like] = GOLD_ACC[1]
    return m


def brackets(cv, x0, x1, y, pal=JADE_TILE6, acc=GOLD_ACC):
    """Dougong bracket row under the eaves: alternating jade/gold blocks."""
    W, H = cv.w, cv.h
    for i, x in enumerate(range(x0, x1 - 1, 4)):
        b = m_rect(W, H, x, y, x + 2, y + 2)
        cv.fill(b, pal[2] if i % 2 == 0 else acc[1])
        cv.put(x, y, pal[4] if i % 2 == 0 else acc[2])
        cv.fill(m_rect(W, H, x + 1, y + 3, x + 1, y + 3), pal[0])


def lacquer_pillar(cv, x0, x1, top, bottom):
    W, H = cv.w, cv.h
    m = m_rect(W, H, x0, top, x1, bottom)
    u = run_u(m)
    idx_paint(cv, m, LACQ, (len(LACQ) - 0.01) * (0.9 - u * 0.8))
    cv.fill(m_rect(W, H, x0, top, x1, top + 1), GOLD_ACC[1])
    return m


@prop("paifang_gate", 150, 130)
def paifang_gate(state, f):
    W, H = 150, 130
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 127
    cshadow(cv, 75, gy, 70, 2)
    # stone drum bases and lacquer pillars
    for px in (20, 52, 98, 130):
        lacquer_pillar(cv, px - 3, px + 2, 38, 116)
        base = m_rect(W, H, px - 7, 112, px + 6, gy)
        idx_paint(cv, base, STONE_P, 2.5 - (yy - 112) / 8.0 + (xx < px - 3) * 1.0)
        cv.fill(m_rect(W, H, px - 7, 112, px + 6, 112), STONE_P[4])
        drum = m_ellipse(W, H, px - 0.5, 107, 5.5, 5.5)
        idx_paint(cv, drum, STONE_P, 2.2 - ((xx - px) + (yy - 107)) / 5.0)
        cv.fill(m_rect(W, H, px - 7, 120, px + 6, 120), STONE_P[1])
    # architraves: central two tiers, side one tier (red with jade band + gold studs)
    for (x0, x1, y0) in ((49, 101, 44), (49, 101, 62), (17, 55, 64), (95, 133, 64)):
        beam = m_rect(W, H, x0, y0, x1, y0 + 4)
        cv.fill(beam, LACQ[2])
        cv.fill(m_rect(W, H, x0, y0, x1, y0), LACQ[3])
        cv.fill(m_rect(W, H, x0, y0 + 4, x1, y0 + 4), LACQ[0])
        band = m_rect(W, H, x0 + 2, y0 + 2, x1 - 2, y0 + 2)
        cv.fill(band, JADE_TILE6[3])
        cv.fill(band & (xx % 4 == 0), GOLD_ACC[2])
    # central name plaque between the beams
    pl = m_rect(W, H, 62, 49, 88, 61)
    cv.fill(pl, GOLD_ACC[1])
    cv.fill(m_rect(W, H, 64, 51, 86, 59), JADE_TILE6[1])
    cv.fill(top_edge(pl) | left_edge(pl), GOLD_ACC[2])
    for gx in (68, 75, 82):  # three stylised glyphs
        cv.fill(m_rect(W, H, gx - 1, 53, gx + 1, 53) | m_rect(W, H, gx, 52, gx, 58) | m_rect(W, H, gx - 2, 56, gx + 2, 56),
                GOLD_ACC[2])
    # side-bay lattice panels
    for (x0, x1) in ((25, 47), (103, 125)):
        pan = m_rect(W, H, x0, 69, x1, 74)
        cv.fill(pan, JADE_TILE6[1])
        cv.fill(pan & ((xx + yy) % 4 == 0), JADE_TILE6[3])
    # roofs: side bays low, centre raised and grander, with bracket rows
    brackets(cv, 14, 56, 57)
    brackets(cv, 94, 136, 57)
    brackets(cv, 44, 106, 38)
    glazed_roof(cv, 3, 59, 42, 57, "pf_l", curl=3)
    glazed_roof(cv, 91, 147, 42, 57, "pf_r", curl=3)
    glazed_roof(cv, 30, 120, 12, 36, "pf_c", curl=4, thick=3)
    # ridge pearl on the central roof
    pearl = m_ellipse(W, H, 75, 7, 2.5, 2.5)
    cv.fill(pearl, GOLD_ACC[1])
    cv.put(74, 6, GOLD_ACC[2])
    finish(cv, LACQ, JADE_TILE6, STONE_P)
    return cv


@prop("pagoda", 80, 180)
def pagoda(state, f):
    W, H = 80, 180
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 177
    cx = 40
    cshadow(cv, cx, gy, 34, 2)
    # stepped stone plinth
    for (hw, y0, y1) in ((34, 170, gy), (29, 164, 169)):
        st = m_rect(W, H, cx - hw, y0, cx + hw - 1, y1)
        idx_paint(cv, st, STONE_P, 2.4 - (yy - y0) / max(1, y1 - y0) * 1.5 + (xx < cx - hw + 3) * 1.0)
        cv.fill(m_rect(W, H, cx - hw, y0, cx + hw - 1, y0), STONE_P[4])
    y = 164
    tiers = 7
    for i in range(tiers):
        bw = 42 - i * 4.4
        bh = int(round(15 - i * 1.0))
        x0, x1 = int(round(cx - bw / 2)), int(round(cx + bw / 2)) - 1
        body = m_rect(W, H, x0, y - bh + 1, x1, y)
        idx_paint(cv, body, WALL_W, 1.5 + (xx < x0 + 3) * 1.0 - (yy <= y - bh + 2) * 1.0)
        for px in (x0, x1 - 1):
            cv.fill(m_rect(W, H, px, y - bh + 1, px + 1, y), LACQ[2])
        # arched door on the ground tier, round windows above
        if i == 0:
            door = m_rect(W, H, cx - 3, y - 9, cx + 2, y) & ~m_rect(W, H, cx - 3, y - 9, cx - 3, y - 9) & \
                ~m_rect(W, H, cx + 2, y - 9, cx + 2, y - 9)
            cv.fill(door, LACQ[0])
            cv.fill(m_rect(W, H, cx - 3, y - 8, cx - 3, y), LACQ[1])
        else:
            wm = m_ellipse(W, H, cx - 0.5, y - bh / 2 + 0.5, 2.2, 2.2)
            cv.fill(wm, JADE_TILE6[0])
            cv.fill(wm & (xx < cx), JADE_TILE6[1])
        # railing band on each tier
        cv.fill(m_rect(W, H, x0, y - 2, x1, y - 2), LACQ[1])
        # roof over the tier
        rw = bw + 14 - i * 0.6
        top = y - bh - 5
        glazed_roof(cv, int(round(cx - rw / 2)), int(round(cx + rw / 2)), top, y - bh + 2, ("pg", i), curl=2, thick=2)
        y = top - 1
    # spire: stacked gold rings and a pearl
    for k in range(6):
        ry = y - k * 2
        rw_ = 3 - (k % 2)
        cv.fill(m_rect(W, H, cx - rw_, ry - 1, cx + rw_ - 1, ry), GOLD_ACC[1])
        cv.put(cx - rw_, ry - 1, GOLD_ACC[2])
    cv.fill(m_rect(W, H, cx - 1, y - 18, cx, y - 12), GOLD_ACC[0])
    pearl = m_ellipse(W, H, cx - 0.5, y - 20, 1.8, 1.8)
    cv.fill(pearl, GOLD_ACC[1])
    cv.put(cx - 1, y - 21, GOLD_ACC[2])
    finish(cv, JADE_TILE6, LACQ, STONE_P)
    return cv


@prop("stone_steps", 100, 60)
def stone_steps(state, f):
    W, H = 100, 60
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 57
    cshadow(cv, 50, gy, 48, 2)
    n = len(STONE_P)
    steps = 8
    for k in range(steps):
        y1 = gy - k * 6
        y0 = y1 - 5
        inset = k * 1.5
        m = m_rect(W, H, int(12 + inset), y0, int(87 - inset), y1)
        v = np.where(yy == y0, n - 1, np.where(yy == y0 + 1, n - 2, 1.6 - (yy - y0) * 0.2))
        idx_paint(cv, m, STONE_P, v + (xx < 20 + inset) * 0.6)
        cv.fill(m & (yy == y1), STONE_P[0])
        # worn centre of each tread
        cv.fill(m & (yy == y0) & (np.abs(xx - 50) < 10 - k), STONE_P[3])
    # cheek walls with capped newel posts
    for side in (-1, 1):
        cx = 50 + side * 43
        wall = m_poly(W, H, [(cx - 5, gy), (cx + 4, gy), (cx + 4 - side * 0, gy - 44), (cx - 5, gy - 44)])
        idx_paint(cv, wall, STONE_P, 2.0 + (xx < cx - 2) * 1.2 - (yy > gy - 4) * 0.8)
        cv.fill(m_rect(W, H, cx - 5, gy - 44, cx + 4, gy - 44), STONE_P[4])
        cap = m_rect(W, H, cx - 6, gy - 48, cx + 5, gy - 45)
        idx_paint(cv, cap, STONE_P, np.where(yy == gy - 48, n - 1, 2.0))
        knob = m_ellipse(W, H, cx - 0.5, gy - 51, 3, 3)
        idx_paint(cv, knob, STONE_P, 2.4 - ((xx - cx) + (yy - (gy - 51))) / 3.0)
        # carved cloud panel
        cv.fill(m_rect(W, H, cx - 3, gy - 34, cx + 2, gy - 34) | m_rect(W, H, cx - 3, gy - 20, cx + 2, gy - 20), STONE_P[1])
        cv.fill(m_ellipse(W, H, cx - 0.5, gy - 27, 2, 2) & ~m_ellipse(W, H, cx - 0.5, gy - 27, 1, 1), STONE_P[1])
    # moss in the corners
    nz = vnoise(W, H, 3, seed_of("steps_moss"), 1)
    moss = (cv.a > 0) & (nz > 0.66) & ((np.abs(xx - 50) > 30) | (yy > gy - 8))
    cv.fill(moss, MOSS[2])
    cv.fill(moss & top_edge(cv.solid | moss), MOSS[3])
    finish(cv, STONE_P, MOSS)
    return cv


@prop("statue_guardian_lion", 40, 50)
def statue_guardian_lion(state, f):
    """Seated stone guardian lion facing right: big curled mane, open jaw, paw on an embroidered ball."""
    W, H = 40, 50
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 47
    cshadow(cv, 20, gy, 18, 1.5)
    n = len(STONE_P)
    plinth = m_rect(W, H, 4, 40, 35, gy)
    idx_paint(cv, plinth, STONE_P, 2.2 + (xx < 7) * 1.0 - (yy > 45) * 0.8)
    cv.fill(m_rect(W, H, 3, 39, 36, 39), STONE_P[4])
    cv.fill(m_rect(W, H, 8, 42, 31, 42) | m_rect(W, H, 8, 45, 31, 45), STONE_P[1])

    def part(m, cx, cy, r, bias=0.0):
        d = ((xx - cx) + (yy - cy)) / max(1.0, r)
        idx_paint(cv, m, STONE_P, (n - 1) * 0.55 - d * 1.1 + bias)

    # back leg / haunch and tail curl
    haunch = m_ellipse(W, H, 13, 32, 8, 7) & (yy <= 38)
    part(haunch, 13, 32, 8, -0.3)
    foot = m_ellipse(W, H, 11, 37, 5, 2) & (yy <= 38)
    part(foot, 11, 37, 5, -0.2)
    tail = m_ellipse(W, H, 5, 27, 3, 3) | m_ellipse(W, H, 6, 22, 2.5, 2.5)
    part(tail, 5, 25, 3)
    cv.fill(m_ellipse(W, H, 5, 27, 1.2, 1.2) | m_ellipse(W, H, 6, 22, 1, 1), STONE_P[1])
    # upright chest and straight front leg
    chest = m_ellipse(W, H, 22, 26, 6.5, 9) | m_rect(W, H, 24, 28, 28, 38)
    part(chest, 22, 26, 8, 0.2)
    cv.fill(m_rect(W, H, 27, 29, 28, 38), STONE_P[1])
    cv.fill(m_rect(W, H, 24, 37, 29, 38), STONE_P[3])
    # mane: ring of curls behind the head, each with a dark centre
    for (mx, my) in ((17, 9), (16, 14), (17, 19), (20, 22), (20, 5), (25, 4), (29, 5)):
        c = m_ellipse(W, H, mx, my, 3.2, 3.2)
        part(c, mx, my, 3.2, -0.2)
        cv.put(mx, my, STONE_P[0])
        cv.put(mx + 1, my, STONE_P[1])
    head = m_ellipse(W, H, 25, 12, 6.5, 6)
    part(head, 25, 12, 6.5, 0.4)
    muzzle = m_ellipse(W, H, 31, 15, 4, 3.4)
    part(muzzle, 31, 15, 4, 0.6)
    # face: heavy brow, bulging eye, open jaw with fang
    cv.fill(m_rect(W, H, 26, 8, 31, 8), STONE_P[4])
    cv.fill(m_rect(W, H, 27, 10, 29, 11), STONE_P[0])
    cv.put(28, 10, STONE_P[4])
    jaw = m_rect(W, H, 29, 17, 34, 18)
    cv.fill(jaw, STONE_P[0])
    cv.put(33, 17, STONE_P[4])
    cv.put(34, 13, STONE_P[1])
    # paw on an embroidered ball
    ball = m_ellipse(W, H, 32, 35, 4, 4)
    part(ball, 32, 35, 4, 0.3)
    cv.fill(ball & ((xx - yy) % 3 == 0) & ~top_edge(ball), STONE_P[1])
    paw = m_ellipse(W, H, 30, 31, 3, 1.8)
    part(paw, 30, 31, 3, 0.6)
    finish(cv, STONE_P)
    return cv


@prop("stone_lantern", 28, 55)
def stone_lantern(state, f):
    W, H = 28, 55
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 52
    cx = 14
    cshadow(cv, cx, gy, 12, 1.4)
    n = len(STONE_P)

    def block(x0, y0, x1, y1, top=True):
        m = m_rect(W, H, x0, y0, x1, y1)
        idx_paint(cv, m, STONE_P, 2.2 + (xx < x0 + 2) * 1.2 - (xx > x1 - 2) * 0.9 - (yy == y1) * 0.8)
        if top:
            cv.fill(m_rect(W, H, x0, y0, x1, y0), STONE_P[4])
        return m

    block(4, 47, 23, gy)            # base
    block(6, 44, 21, 46)
    block(11, 30, 16, 43)           # post
    cv.fill(m_rect(W, H, 11, 36, 16, 36), STONE_P[1])
    block(5, 27, 22, 29)            # platform
    box = block(7, 17, 20, 26, top=False)
    win = m_rect(W, H, 10, 19, 17, 24)
    cv.fill(win, WARM[2])
    cv.fill(m_rect(W, H, 10, 19, 17, 19) | m_rect(W, H, 10, 19, 10, 24), WARM[1])
    cv.fill(m_rect(W, H, 13, 20, 14, 23), WARM[3])
    cv.fill(m_rect(W, H, 13, 19, 14, 24) & (yy == 21), STONE_P[1])
    # roof cap with upturned corners
    roof = m_poly(W, H, [(1, 16), (4, 13), (11, 9), (17, 9), (24, 13), (27, 16), (25, 17), (2, 17)])
    idx_paint(cv, roof, STONE_P, np.where(yy <= 10, n - 1, 2.6 - (yy - 10) * 0.2 + (xx < 10) * 0.8))
    cv.fill(m_rect(W, H, 2, 17, 25, 17), STONE_P[0])
    cv.put(0, 15, STONE_P[3])
    cv.put(27, 15, STONE_P[3])
    fin = m_ellipse(W, H, 13.5, 6, 2.5, 3)
    idx_paint(cv, fin, STONE_P, 2.6 - ((xx - 13) + (yy - 6)) / 2.5)
    cv.fill(m_rect(W, H, 13, 1, 14, 3), STONE_P[3])
    finish(cv, STONE_P, WARM)
    # warm light spill (stepped, translucent)
    cv.light(m_ellipse(W, H, 13.5, 21.5, 10, 7) & ~cv.solid, WARM[2], 0.12)
    return cv


@prop("lantern_string", 128, 30, ground=0, anchor=(64, 0))
def lantern_string(state, f):
    """Festival lanterns on a sagging rope; anchored at the top centre (the rope line)."""
    W, H = 128, 30
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    rope_y = lambda x: 1 + 8 * (1 - ((x - 63.5) / 63.5) ** 2)  # noqa: E731
    pts = [(x, rope_y(x)) for x in range(0, W, 4)] + [(W - 1, rope_y(W - 1))]
    cv.fill(m_line(W, H, [(round(x), round(y)) for x, y in pts]), ROPE[1])
    lp = [(10, 5, 7, 0), (30, 6, 8, 1), (52, 7, 9, 0), (76, 7, 9, 2), (98, 6, 8, 0), (118, 5, 7, 1)]
    for (lx, lw, lh, kind) in lp:
        top = int(round(rope_y(lx))) + 1
        cv.fill(m_rect(W, H, lx, top, lx, top + 1), ROPE[0])
        y0 = top + 2
        body = m_ellipse(W, H, lx, y0 + lh / 2 + 0.5, lw / 2 + 0.4, lh / 2)
        body &= (yy > y0) & (yy < y0 + lh)
        pal = CLOTH_R if kind != 2 else CLOTH_J
        d = (xx - lx) / (lw / 2 + 0.5)
        idx_paint(cv, body, pal, (len(pal) - 1) * 0.6 - d * 1.4 + (np.abs(d) < 0.35) * 0.8)
        cv.fill(body & (yy == y0 + lh // 2) & (xx % 2 == 0), pal[1])
        cv.fill(m_rect(W, H, lx - lw // 2 + 1, y0, lx + lw // 2 - 1, y0), GOLD_ACC[1])
        cv.fill(m_rect(W, H, lx - lw // 2 + 1, y0 + lh, lx + lw // 2 - 1, y0 + lh), GOLD_ACC[1])
        cv.fill(m_rect(W, H, lx, y0 + lh + 1, lx, y0 + lh + 4), pal[3] if kind != 2 else GOLD_ACC[1])
        cv.put(lx, y0 + lh + 5, GOLD_ACC[2])
    finish(cv, CLOTH_R, ROPE, close_edges=False)
    return cv


def flag_pole(theme):
    W, H = 30, 110
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 107
    cloth = CLOTH_J if theme == "jade" else CLOTH_C
    trim = GOLD_ACC if theme == "jade" else R("#2f4f78", "#4f79a8", "#8fb4d8")
    cshadow(cv, 9, gy, 8, 1.4)
    # drum base with a clamp stone
    base = m_rect(W, H, 3, 99, 15, gy)
    idx_paint(cv, base, STONE_P, 2.2 + (xx < 6) * 1.2 - (yy > gy - 2) * 0.8)
    cv.fill(m_rect(W, H, 3, 99, 15, 99), STONE_P[4])
    cv.fill(m_rect(W, H, 2, 103, 16, 103), STONE_P[1])
    pole = m_rect(W, H, 8, 6, 10, 99)
    idx_paint(cv, pole, LACQ if theme == "jade" else WOOD, 2.8 - (xx - 8) * 1.0)
    tip = m_poly(W, H, [(9, 0), (11, 4), (10, 6), (8, 6), (7, 4)])
    cv.fill(tip, GOLD_ACC[1])
    cv.put(8, 3, GOLD_ACC[2])
    cv.fill(m_rect(W, H, 7, 7, 26, 8), WOOD[2])
    cv.fill(m_rect(W, H, 7, 7, 26, 7), WOOD[3])
    # long streaming banner with a swallowtail, waving edge
    wave = lambda y: 1.2 * math.sin(y * 0.22)  # noqa: E731
    left = [(12 + wave(y) * 0.3, y) for y in range(9, 74)]
    right = [(26 + wave(y + 3), y) for y in range(73, 8, -1)]
    ban = m_poly(W, H, left + [(12, 80), (19, 73), (26 + wave(76), 80)] + right)
    ph = np.sin(yy * 0.22)
    idx_paint(cv, ban, cloth, (len(cloth) - 1) * 0.55 + ph * 0.9 - (xx > 22) * 0.6)
    cv.fill(ban & ((xx == 13) | (xx == 14)), trim[1])
    cv.fill(ban & (yy == 10), trim[1])
    # emblem: sect sigil ring and three bars
    ring = m_ellipse(W, H, 19.5, 22, 4.5, 4.5) & ~m_ellipse(W, H, 19.5, 22, 3, 3)
    cv.fill(ring & ban, trim[2])
    if theme == "jade":
        cv.fill(m_ellipse(W, H, 19.5, 22, 1.5, 1.5), trim[1])
    else:
        cv.fill(m_rect(W, H, 18, 21, 21, 22), trim[1])
    for k in range(3):
        cv.fill(m_rect(W, H, 17, 34 + k * 7, 22, 35 + k * 7) & ban, trim[1])
    for tx in (12, 26):
        cv.fill(m_rect(W, H, tx, 9, tx, 13), CLOTH_R[2])
    finish(cv, cloth, STONE_P, LACQ)
    return cv


@prop("flag_pole_jade", 30, 110)
def flag_pole_jade(state, f):
    return flag_pole("jade")


@prop("flag_pole_cloud", 30, 110)
def flag_pole_cloud(state, f):
    return flag_pole("cloud")


# ================================================================== village clutter
def spoked_wheel(cv, cx, cy, r, pal=WOOD, broken=False):
    W, H = cv.w, cv.h
    xx, yy = grid(W, H)
    rim = m_ellipse(W, H, cx, cy, r, r) & ~m_ellipse(W, H, cx, cy, r - 2, r - 2)
    if broken:
        rim &= ~(((xx - cx) > 0) & ((yy - cy) < 0) & ((xx - cx) < r * 0.7))
    d = ((xx - cx) + (yy - cy)) / max(1, r)
    idx_paint(cv, rim, pal, (len(pal) - 1) * 0.55 - d * 1.2)
    for k in range(6):
        a = k * math.pi / 3 + 0.3
        if broken and k in (0, 5):
            continue
        cv.fill(m_line(W, H, [(round(cx), round(cy)), (round(cx + math.cos(a) * (r - 1.5)), round(cy + math.sin(a) * (r - 1.5)))]),
                pal[2])
    hub = m_ellipse(W, H, cx, cy, 1.8, 1.8)
    cv.fill(hub, IRON[2])
    cv.put(int(cx) - 1, int(cy) - 1, IRON[3])
    return rim


@prop("cart_broken", 80, 45)
def cart_broken(state, f):
    W, H = 80, 45
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 42
    cshadow(cv, 40, gy, 36, 2)
    # detached wheel lying on its side behind the bed
    flat_w = m_ellipse(W, H, 18, gy - 2, 11, 3) & ~m_ellipse(W, H, 18, gy - 2, 8, 1.6)
    idx_paint(cv, flat_w, WOOD, 2.6 - (yy - (gy - 5)) * 0.5)
    cv.fill(m_ellipse(W, H, 18, gy - 2, 1.5, 0.8), IRON[2])
    # shafts poking up to the right
    for dy in (0, 3):
        cv.fill(m_line(W, H, [(44, 22 + dy), (77, 5 + dy)], 2), WOOD[2])
        cv.fill(m_line(W, H, [(44, 21 + dy), (77, 4 + dy)], 1), WOOD[3])
    # tilted plank bed: low left corner on the ground, raised right on the intact wheel
    bed = m_poly(W, H, [(6, 33), (58, 20), (60, 27), (8, 40)])
    idx_paint(cv, bed, WOOD, 2.4 + (yy < 26) * 0.8)
    for k in range(5):
        x = 14 + k * 10
        cv.fill(m_line(W, H, [(x, 38 - k * 2.6), (x + 1, 31 - k * 2.6)]) & bed, WOOD[1])
    side = m_poly(W, H, [(6, 33), (58, 20), (58, 17), (6, 29)])
    idx_paint(cv, side, WOOD, 3.2 - (yy % 3 == 0) * 1.0)
    cv.fill(top_edge(side), WOOD[4])
    # splintered break at the left end
    for (x0, y0, x1, y1) in ((6, 29, 2, 26), (7, 31, 3, 32), (9, 30, 5, 28)):
        cv.fill(m_line(W, H, [(x0, y0), (x1, y1)]), WOOD[3])
    # intact spoked wheel
    spoked_wheel(cv, 50, 31, 10.5, WOOD)
    # spilled sack
    sack = m_poly(W, H, [(24, gy), (38, gy), (37, 35), (31, 32), (26, 34)])
    idx_paint(cv, sack, SACK, 2.4 - (xx - 26) / 10.0 - (yy - 34) / 8.0)
    cv.fill(m_rect(W, H, 30, 32, 32, 33), ROPE[1])
    for (gx, gy2) in ((40, gy), (42, gy - 1), (44, gy), (39, gy - 1), (46, gy)):
        cv.put(gx, gy2, STRAW[3])
    finish(cv, WOOD, SACK, IRON)
    return cv


@prop("barrel", 20, 26)
def barrel(state, f):
    W, H = 20, 26
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 23
    cshadow(cv, 10, gy, 9, 1.2)
    body = lathe(W, H, 9.5, [(4, 7), (13, 8.5), (gy, 7)])
    u = run_u(body)
    idx_paint(cv, body, WOOD, (len(WOOD) - 0.01) * (0.9 - u * 0.75))
    cv.fill(body & ((xx % 3) == 0) & (yy > 5), WOOD[1])
    for hy in (6, 12, 20):
        cv.fill(body & (yy == hy), IRON[1])
        cv.fill(body & (yy == hy) & (u < 0.4), IRON[3])
    lid = m_ellipse(W, H, 9.5, 4, 6.5, 1.6)
    cv.fill(lid, WOOD[3])
    cv.fill(lid & (yy == 5), WOOD[2])
    cv.fill(m_rect(W, H, 9, 3, 10, 4), WOOD[4])
    finish(cv, WOOD, IRON)
    return cv


def sack_shape(cv, cx, by, w, h, lvl, pal=SACK):
    W, H = cv.w, cv.h
    xx, yy = grid(W, H)
    m = m_ellipse(W, H, cx, by - h * 0.42, w / 2, h * 0.45) | m_rect(W, H, int(cx - w / 2 + 2), int(by - h * 0.4), int(cx + w / 2 - 2), by)
    m &= yy <= by
    neck = m_poly(W, H, [(cx - 2, by - h * 0.82), (cx + 2, by - h * 0.82), (cx + 1.5, by - h - 1), (cx - 1.5, by - h - 1)])
    m |= neck
    d = (xx - cx) / (w / 2) + (yy - (by - h * 0.5)) / h
    idx_paint(cv, m, pal, (len(pal) - 1) * 0.6 - d * 1.1 + lvl)
    weave = m & erode(m) & ((xx + yy) % 2 == 0) & (d > -0.2)
    cv.fill(weave & (d > 0.4), pal[0])
    cv.fill(m_rect(W, H, int(cx) - 2, int(by - h * 0.82), int(cx) + 1, int(by - h * 0.82)), ROPE[1])
    cv.fill(m_rect(W, H, int(cx) - 1, int(by - h) - 1, int(cx), int(by - h) - 1), pal[3])
    return m


@prop("sack_pile", 40, 22)
def sack_pile(state, f):
    W, H = 40, 22
    cv = Canvas(W, H)
    gy = 19
    cshadow(cv, 20, gy, 18, 1.4)
    sack_shape(cv, 11, gy, 16, 12, -0.2)
    sack_shape(cv, 28, gy, 17, 12, 0.0)
    sack_shape(cv, 20, gy - 7, 15, 11, 0.4)
    # spilled rice
    for (gx, gy2) in ((34, gy), (36, gy), (35, gy - 1), (3, gy), (5, gy)):
        cv.put(gx, gy2, PAPER[3])
    finish(cv, SACK, ROPE)
    return cv


@prop("hay_bale", 36, 24)
def hay_bale(state, f):
    W, H = 36, 24
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 21
    cshadow(cv, 18, gy, 17, 1.4)
    bale = m_rect(W, H, 3, 6, 32, gy)
    for (cx_, cy_) in ((3, 6), (32, 6), (3, gy), (32, gy)):
        bale[cy_, cx_] = False
    n = len(STRAW)
    st = vnoise(W * 3, H, 3, seed_of("hay"), 1)[:, ::3]
    v = (n - 1) * 0.55 - (xx - 3) / 29.0 * 1.2 + (yy < 8) * 1.2 + (st > 0.62) * 0.9 - (st < 0.32) * 0.9 - (yy > gy - 2) * 1.0
    idx_paint(cv, bale, STRAW, v)
    for bx in (11, 24):
        band = m_rect(W, H, bx, 6, bx + 1, gy)
        cv.fill(band, ROPE[1])
        cv.fill(band & (xx == bx), ROPE[2])
    g = rng("hay_bale")
    for i in range(12):
        x0 = int(g.integers(3, 33))
        y0 = 6 if i % 2 == 0 else int(g.integers(8, gy))
        ang = g.uniform(-2.6, -0.5)
        x1, y1 = x0 + math.cos(ang) * 3, y0 + math.sin(ang) * 3
        cv.fill(m_line(W, H, [(x0, y0), (round(x1), round(y1))]), STRAW[4] if i % 3 else STRAW[2])
    finish(cv, STRAW, ROPE)
    return cv


@prop("drying_rack_fish", 60, 45)
def drying_rack_fish(state, f):
    W, H = 60, 45
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 42
    cshadow(cv, 30, gy, 28, 1.6)
    for cx in (6, 54):  # crossed pole ends
        cv.fill(m_line(W, H, [(cx - 5, gy), (cx + 3, 3)], 2), WOOD_DRY[2])
        cv.fill(m_line(W, H, [(cx + 5, gy), (cx - 3, 3)], 2), WOOD_DRY[1])
        cv.fill(m_line(W, H, [(cx - 5, gy - 1), (cx + 3, 2)]), WOOD_DRY[3])
    for py in (6, 22):
        pole = m_rect(W, H, 2, py, 57, py + 1)
        cv.fill(pole, WOOD_DRY[2])
        cv.fill(top_edge(pole), WOOD_DRY[4])
    for cx in (6, 54):
        cv.fill(m_rect(W, H, cx - 1, 5, cx + 1, 8) | m_rect(W, H, cx - 1, 21, cx + 1, 24), ROPE[1])
    g = rng("fishrack")
    for row, py in enumerate((8, 24)):
        for i, fx in enumerate(range(13, 50, 6)):
            if (i + row) % 5 == 4:
                continue
            ln = int(g.integers(7, 10))
            cv.fill(m_rect(W, H, fx, py, fx, py + 1), ROPE[0])
            body = m_poly(W, H, [(fx - 1, py + 2), (fx + 1, py + 2), (fx + 2, py + ln - 2), (fx, py + ln + 1),
                                 (fx - 2, py + ln - 2)])
            tail = m_poly(W, H, [(fx - 2, py + 1), (fx + 2, py + 1), (fx, py + 3)])
            m = body | tail
            idx_paint(cv, m, FISH, 2.6 - (xx - fx + 1) * 0.7 - (row * 0.4))
            cv.put(fx - 1, py + ln - 2, FISH[0])
            cv.fill(m_rect(W, H, fx, py + 4, fx, py + ln - 3) & body, FISH[3])
    basket = lathe(W, H, 30, [(gy - 6, 8), (gy, 7)])
    idx_paint(cv, basket, STRAW, 2.6 - (xx - 22) / 8.0)
    cv.fill(basket & ((xx + yy) % 3 == 0), STRAW[1])
    finish(cv, WOOD_DRY, FISH, STRAW)
    return cv


# ================================================================== water & mist effects
@prop("waterfall", 80, 180, states=(("idle", 4, 8),))
def waterfall(state, f):
    """Looping waterfall: streaked sheet scrolling down (period 48 px = 4 frames x 12 px),
    lip curling over the top, churning foam and flat-alpha spray at the plunge."""
    W, H = 80, 180
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 176
    n = len(WATER)
    g = rng("waterfall")
    t = yy / float(H)
    wob_l = np.round(1.2 * np.sin(yy / 7.0) + 0.8 * np.sin(yy / 3.1 + 1.0))
    wob_r = np.round(1.2 * np.sin(yy / 6.3 + 2.0) + 0.8 * np.sin(yy / 2.7))
    left = 16 - 9 * t ** 1.6 + wob_l
    right = 64 + 9 * t ** 1.6 + wob_r
    sheet = (xx >= left) & (xx <= right) & (yy >= 6) & (yy <= gy - 6)
    phase = g.uniform(0, 2 * math.pi, W)
    amp = g.uniform(0.3, 1.0, W)
    gapcol = g.random(W) < 0.12
    s = np.sin(2 * math.pi * (yy - f * 12) / 48.0 + phase[None, :]) * amp[None, :]
    s2 = np.sin(2 * math.pi * (yy - f * 12) / 24.0 + phase[None, :] * 2.3)
    u = (xx - left) / np.maximum(1, right - left)
    v = (n - 1) * 0.45 + (s > 0.55) * 1.4 + (s2 > 0.8) * 0.8 - (u > 0.8) * 1.0 + (u < 0.12) * 0.8 \
        + (np.abs(u - 0.45) < 0.18) * 0.5 - (gapcol[None, :] & (s < 0.2)) * 1.2
    idx_paint(cv, sheet, WATER, v)
    edge = sheet & (left_edge(sheet) | right_edge(sheet))
    cv.fill(edge & (u > 0.5), WATER[0])
    cv.fill(edge & (u <= 0.5), WATER[3])
    # the lip where the river pours over
    lip = m_ellipse(W, H, 40, 8, 27, 4) & (yy <= 9)
    idx_paint(cv, lip, WATER, 2.5 + (yy < 6) * 1.5 - (xx > 58) * 0.8)
    cv.fill(top_edge(lip), WATER[4])
    for k in range(5):  # lip ripples travel outward
        rx = 16 + ((k * 11 + f * 3) % 48)
        cv.put(rx, 6, WATER[4])
        cv.put(rx + 1, 6, WATER[3])
    # plunge pool and churning foam
    pool = m_ellipse(W, H, 40, gy - 1, 38, 3.5) & (yy <= gy + 1)
    idx_paint(cv, pool, WATER, 1.5 + ((xx + f * 2) % 6 == 0) * 2)
    foam = np.zeros((H, W), bool)
    for k in range(9):
        fx = 12 + k * 7 + math.sin(f * math.pi / 2 + k) * 1.5
        fr = 5.5 + 1.5 * math.sin(f * math.pi / 2 + k * 1.7)
        foam |= m_ellipse(W, H, fx, gy - 7 + (k % 2), fr, fr * 0.8)
    foam &= yy <= gy
    d = ((yy - (gy - 10)) / 8.0)
    idx_paint(cv, foam, WATER, (n - 1) - np.clip(d, 0, 2) * 0.8)
    cv.fill(foam & bottom_edge(foam), WATER[2])
    finish(cv, WATER, inks=[mix(WATER[0], INK, 0.35)])
    # spray: flat-alpha puffs drifting up
    for k in range(6):
        t = ((k / 6.0) + f / 4.0) % 1.0
        px = 10 + k * 12 + math.sin(k * 2.1) * 3
        py = gy - 12 - t * 26
        r = 5 + t * 5
        a = 0.34 * (1 - t)
        m = m_ellipse(W, H, px, py, r, r * 0.7) & ~cv.solid
        cv.fill(m, MIST, a)
    return cv


@prop("mist_bank", 160, 40, states=(("idle", 3, 3),), ground=0, decal=True)
def mist_bank(state, f):
    """Low drifting mist: overlapping puffs breathing in a 3-frame loop, flat alpha steps,
    fading out toward both ends so banks can overlap freely."""
    W, H = 160, 40
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    g = rng("mist_bank")
    level = np.zeros((H, W))
    ph = 2 * math.pi * f / 3.0
    for k in range(11):
        bx = 12 + k * 13.6 + g.uniform(-3, 3)
        by = 26 + g.uniform(-4, 3)
        r = g.uniform(9, 15)
        p0 = g.uniform(0, 2 * math.pi)
        cx = bx + 2.5 * math.sin(ph + p0)
        cy = by + 1.0 * math.cos(ph + p0)
        rr = r * (1 + 0.08 * math.sin(ph + p0 * 1.3))
        d = ((xx - cx) / (rr * 1.5)) ** 2 + ((yy - cy) / rr) ** 2
        level = np.maximum(level, np.clip(1.2 - d, 0, 1))
    env = np.clip(np.minimum(xx, W - 1 - xx) / 26.0, 0, 1)
    level = level * env * np.clip((H - 1 - yy) / 4.0, 0, 1)
    steps = ((0.15, 0.14), (0.4, 0.24), (0.7, 0.34))
    for thr, a in steps:
        cv.fill(level > thr, MIST, a)
    cv.fill((level > 0.4) & (yy > 28), hexc("#d3e1e3"), 0.12)
    return cv


# ================================================================== interior furnishings
@prop("rug", 96, 24, ground=0, decal=True)
def rug(state, f):
    """Floor rug in slight perspective: red field, gold border, jade medallion, fringed ends."""
    W, H = 96, 24
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    outer = m_poly(W, H, [(9, 3), (86, 3), (91, 20), (4, 20)])
    inner = m_poly(W, H, [(13, 5), (82, 5), (86, 18), (9, 18)])
    field = m_poly(W, H, [(15, 6), (80, 6), (83, 17), (12, 17)])
    cv.fill(outer, GOLD_ACC[1])
    cv.fill(inner, CLOTH_R[1])
    cv.fill(field, CLOTH_R[2])
    cv.fill(outer & (yy == 3), GOLD_ACC[2])
    cv.fill(outer & ~inner & (yy >= 19), GOLD_ACC[0])
    # key-fret pattern on the border band
    cv.fill(inner & ~field & ((xx + yy) % 4 == 0), GOLD_ACC[1])
    # jade medallion + corner cloud motifs
    med = m_ellipse(W, H, 47.5, 11.5, 12, 4.5)
    cv.fill(med, GOLD_ACC[1])
    cv.fill(m_ellipse(W, H, 47.5, 11.5, 10.5, 3.5), CLOTH_J[2])
    cv.fill(m_ellipse(W, H, 47.5, 11.5, 6, 2), CLOTH_J[3])
    cv.fill(m_ellipse(W, H, 47.5, 11.5, 2.5, 1), GOLD_ACC[2])
    for (mx, my) in ((22, 8), (73, 8), (20, 15), (76, 15)):
        cv.fill(m_ellipse(W, H, mx, my, 2.5, 1.2) & ~m_ellipse(W, H, mx, my, 1.2, 0.5), GOLD_ACC[1])
    cv.fill(field & (yy == 6), CLOTH_R[3])
    # fringe tassels at the short ends
    for y in range(4, 20, 2):
        t = (y - 3) / 17.0
        lx = 9 - t * 5
        rx = 86 + t * 5
        cv.fill(m_line(W, H, [(round(lx) - 1, y), (round(lx) - 3, y)]), PAPER[2])
        cv.fill(m_line(W, H, [(round(rx) + 1, y), (round(rx) + 3, y)]), PAPER[2])
    finish(cv, CLOTH_R, GOLD_ACC, inks=[ink_of(CLOTH_R)])
    return cv


@prop("screen_folding", 60, 55)
def screen_folding(state, f):
    """Four-panel folding screen, zig-zag standing, ink-wash mountains painted across the panels."""
    W, H = 60, 55
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 52
    cshadow(cv, 30, gy, 28, 1.5)
    xs = [3, 17, 30, 44, 57]
    tops = [6, 4, 6, 4, 6]
    bots = [48, 50, 48, 50, 48]
    paint_art = np.zeros((H, W), bool)
    for i in range(4):
        x0, x1 = xs[i], xs[i + 1]
        panel = m_poly(W, H, [(x0, tops[i]), (x1, tops[i + 1]), (x1, bots[i + 1]), (x0, bots[i])])
        lit = i % 2 == 0
        cv.fill(panel, WOOD[1] if lit else WOOD[0])
        pane = m_poly(W, H, [(x0 + 2, tops[i] + 3), (x1 - 2, tops[i + 1] + 3), (x1 - 2, bots[i + 1] - 8),
                             (x0 + 2, bots[i] - 8)])
        cv.fill(pane, PAPER[3] if lit else PAPER[2])
        paint_art |= pane
        low = m_poly(W, H, [(x0 + 2, bots[i] - 6), (x1 - 2, bots[i + 1] - 6), (x1 - 2, bots[i + 1] - 2),
                            (x0 + 2, bots[i] - 2)])
        cv.fill(low, WOOD[2] if lit else WOOD[1])
        cv.fill(m_line(W, H, [(x0, tops[i]), (x1, tops[i + 1])]), WOOD[3] if lit else WOOD[2])
    # ink-wash mountains flowing across all panes
    ridge = 26 + 7 * np.sin(np.arange(W) / 6.5) + 4 * np.sin(np.arange(W) / 2.9 + 1)
    mtn = paint_art & (yy >= ridge[None, :])
    cv.fill(mtn, INKWASH[2])
    cv.fill(mtn & (yy >= ridge[None, :] + 4), INKWASH[1])
    cv.fill(paint_art & top_edge(mtn), INKWASH[0])
    cv.fill(paint_art & (yy >= 36) & (yy <= 37), INKWASH[2])
    for (bx, by) in ((12, 12), (38, 10)):
        cv.fill(m_ellipse(W, H, bx, by, 2, 2) & paint_art, CLOTH_R[2])
    # hinge studs and little feet
    for x in xs[1:-1]:
        for hy in (12, 30):
            cv.put(x, hy, GOLD_ACC[1])
    for x in xs:
        cv.fill(m_rect(W, H, x - 1, bots[xs.index(x)], x + 1, gy), WOOD[0])
    finish(cv, WOOD, PAPER, inks=[ink_of(WOOD)])
    return cv


@prop("scroll_rack", 48, 60)
def scroll_rack(state, f):
    W, H = 48, 60
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 57
    cshadow(cv, 24, gy, 22, 1.4)
    frame = m_rect(W, H, 3, 3, 44, gy)
    cv.fill(frame, WOOD[2])
    cv.fill(m_rect(W, H, 1, 1, 46, 4), WOOD[3])
    cv.fill(m_rect(W, H, 1, 1, 46, 1), WOOD[4])
    g = rng("scroll_rack")
    for r in range(4):
        for c in range(3):
            x0, y0 = 6 + c * 13, 7 + r * 12
            cell = m_rect(W, H, x0, y0, x0 + 10, y0 + 9)
            cv.fill(cell, WOOD[0])
            cv.fill(m_rect(W, H, x0, y0, x0 + 10, y0), WOOD[1])
            k = int(g.integers(0, 3))
            if k < 2:  # rolled scrolls seen end-on
                for j, (sx, sy) in enumerate(((x0 + 2, y0 + 7), (x0 + 6, y0 + 7), (x0 + 4, y0 + 4), (x0 + 8, y0 + 4))):
                    if j >= 2 + k * 2:
                        break
                    end = m_ellipse(W, H, sx + 0.5, sy, 1.8, 1.8)
                    cv.fill(end, PAPER[2])
                    cv.put(sx - 1, sy - 1, PAPER[3])
                    cv.put(sx, sy, [CLOTH_R[2], CLOTH_J[2], GOLD_ACC[1]][(j + r + c) % 3])
            else:  # scrolls lying lengthwise with coloured caps
                for j in range(2):
                    sy = y0 + 8 - j * 3
                    sc = m_rect(W, H, x0 + 1, sy - 1, x0 + 9, sy)
                    cv.fill(sc, PAPER[2])
                    cv.fill(m_rect(W, H, x0 + 1, sy - 1, x0 + 9, sy - 1), PAPER[3])
                    cv.fill(m_rect(W, H, x0 + 9, sy - 1, x0 + 9, sy), CLOTH_R[2] if j else CLOTH_J[2])
    # side posts and plinth
    for px in (2, 43):
        post = m_rect(W, H, px, 2, px + 2, gy)
        cv.fill(post, WOOD[2])
        cv.fill(left_edge(post), WOOD[3])
    cv.fill(m_rect(W, H, 2, gy - 1, 45, gy), WOOD[1])
    tag = m_rect(W, H, 20, 57 - 5, 22, 57 - 2)
    finish(cv, WOOD, PAPER, inks=[ink_of(WOOD)])
    return cv


@prop("altar", 60, 48)
def altar(state, f):
    """Ancestral altar table: everted ends, jade altar cloth, tablet, censer, candles and peaches."""
    W, H = 60, 48
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 45
    cshadow(cv, 30, gy, 28, 1.5)
    # ancestral tablet behind
    tab = m_rect(W, H, 26, 6, 33, 22)
    cv.fill(tab, LACQ[1])
    cv.fill(m_rect(W, H, 27, 8, 32, 20), GOLD_ACC[0])
    cv.fill(m_rect(W, H, 28, 9, 31, 19), LACQ[0])
    for gy_ in (11, 14, 17):
        cv.fill(m_rect(W, H, 29, gy_, 30, gy_), GOLD_ACC[2])
    cv.fill(m_rect(W, H, 25, 5, 34, 6), GOLD_ACC[1])
    # table top with everted (curled-up) ends
    top = m_rect(W, H, 4, 23, 55, 26)
    cv.fill(top, LACQ[2])
    cv.fill(m_rect(W, H, 4, 23, 55, 23), LACQ[3])
    for (ex, sgn) in ((3, -1), (56, 1)):
        curl = m_poly(W, H, [(ex, 23), (ex + sgn * 2, 20), (ex + sgn * 3, 20), (ex + sgn * 1, 26), (ex, 26)])
        cv.fill(curl, LACQ[2])
    cv.fill(m_rect(W, H, 4, 26, 55, 26), GOLD_ACC[1])
    # legs and apron
    for lx in (7, 50):
        leg = m_rect(W, H, lx, 27, lx + 2, gy)
        cv.fill(leg, LACQ[1])
        cv.fill(left_edge(leg), LACQ[2])
        cv.fill(m_rect(W, H, lx - 1, gy - 1, lx + 3, gy), LACQ[0])
    # hanging jade altar cloth with gold embroidery
    cloth = m_poly(W, H, [(14, 27), (45, 27), (44, 40), (29.5, 43), (15, 40)])
    idx_paint(cv, cloth, CLOTH_J, 2.6 + (xx < 24) * 0.8 - (yy > 36) * 0.9)
    cv.fill(cloth & (yy == 29), GOLD_ACC[1])
    ring = m_ellipse(W, H, 29.5, 34, 4, 3) & ~m_ellipse(W, H, 29.5, 34, 2.5, 1.6)
    cv.fill(ring, GOLD_ACC[1])
    cv.put(29, 34, GOLD_ACC[2])
    # bronze censer, candles, peaches
    cen = m_ellipse(W, H, 29.5, 21, 5, 2.5) & (yy <= 22)
    cv.fill(cen, GOLD_ACC[0])
    cv.fill(cen & (yy <= 19), GOLD_ACC[1])
    cv.fill(m_rect(W, H, 26, 22, 26, 22) | m_rect(W, H, 33, 22, 33, 22), GOLD_ACC[0])
    for sx in (28, 30, 31):
        cv.fill(m_rect(W, H, sx, 13 + (sx % 2), sx, 18), WOOD[2])
        cv.put(sx, 13 + (sx % 2), WARM[2])
    for cx in (9, 50):
        cv.fill(m_rect(W, H, cx, 15, cx + 1, 22), CLOTH_R[3])
        cv.fill(m_rect(W, H, cx - 1, 22, cx + 2, 22), GOLD_ACC[1])
        cv.put(cx, 13, WARM[2])
        cv.put(cx, 14, WARM[3])
    plate = m_ellipse(W, H, 18, 22, 4, 1)
    cv.fill(plate, PAPER[2])
    for (px, py) in ((16, 20), (19, 20), (17.5, 18)):
        pe = m_ellipse(W, H, px, py, 1.6, 1.6)
        cv.fill(pe, CLOTH_R[3])
        cv.put(int(px) - 1, int(py) - 1, CLOTH_R[4])
    finish(cv, LACQ, CLOTH_J, GOLD_ACC)
    # incense wisps (translucent)
    for (sx, h0) in ((28, 13), (31, 12)):
        for k in range(8):
            wx, wy = sx + round(math.sin(k * 0.9 + sx) * 1.2), h0 - 1 - k
            if 0 <= wy < H and cv.a[wy, wx] == 0:
                cv.put(wx, wy, PAPER[3], 0.5 if k < 4 else 0.3)
    for cx in (9, 50):
        cv.light(m_ellipse(W, H, cx + 0.5, 13, 3, 3) & ~cv.solid, WARM[2], 0.18)
    return cv


@prop("cushion", 24, 8, ground=1)
def cushion(state, f):
    W, H = 24, 8
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    cshadow(cv, 12, 6, 11, 1.0)
    body = m_ellipse(W, H, 11.5, 4, 10.5, 3.2) & (yy <= 6)
    d = (xx - 11.5) / 10.5 + (yy - 4) / 3.0
    idx_paint(cv, body, CLOTH_J, 2.4 - d * 1.2)
    for k in range(-3, 4):
        cv.put(round(11.5 + k * 2.6), 5, CLOTH_J[1])
    cv.fill(m_ellipse(W, H, 11.5, 3, 1.2, 0.6), GOLD_ACC[1])
    cv.put(11, 2, GOLD_ACC[2])
    finish(cv, CLOTH_J, inks=[ink_of(CLOTH_J)])
    return cv


@prop("bookcase", 55, 75)
def bookcase(state, f):
    W, H = 55, 75
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 72
    cshadow(cv, 27, gy, 26, 1.4)
    back = m_rect(W, H, 4, 4, 50, gy)
    cv.fill(back, WOOD[0])
    g = rng("bookcase")
    shelves = (20, 36, 52, 68)
    covers = [CLOTH_C[1], CLOTH_J[1], CLOTH_R[1], WOOD_DRY[2], CLOTH_C[0]]
    for si, sy in enumerate(shelves):
        x = 6
        while x < 47:
            k = int(g.integers(0, 4))
            if k == 0 and x < 38:  # stack of thread-bound books lying flat
                n_b = int(g.integers(3, 6))
                for j in range(n_b):
                    by = sy - 1 - j * 2
                    bk = m_rect(W, H, x, by - 1, x + 8, by)
                    cv.fill(bk, covers[(j + si) % len(covers)])
                    cv.fill(m_rect(W, H, x, by, x + 8, by), PAPER[2])
                    cv.put(x + 8, by - 1, PAPER[3])
                x += 11
            elif k == 1:  # upright volumes
                for j in range(int(g.integers(2, 4))):
                    hgt = int(g.integers(8, 12))
                    bk = m_rect(W, H, x + j * 3, sy - hgt, x + j * 3 + 2, sy - 1)
                    c = covers[(j + x) % len(covers)]
                    cv.fill(bk, c)
                    cv.fill(left_edge(bk), PAPER[2])
                    cv.put(x + j * 3 + 1, sy - hgt + 2, GOLD_ACC[1])
                x += 10
            elif k == 2 and x < 42:  # small vase
                v = lathe(W, H, x + 2.5, [(sy - 9, 1), (sy - 7, 1), (sy - 5, 2.5), (sy - 1, 2)])
                idx_paint(cv, v, CLOTH_C, 3.2 - (xx - x) * 0.6)
                x += 7
            else:  # lidded box
                bx = m_rect(W, H, x, sy - 5, x + 6, sy - 1)
                cv.fill(bx, LACQ[2])
                cv.fill(m_rect(W, H, x, sy - 5, x + 6, sy - 5), LACQ[3])
                cv.put(x + 3, sy - 3, GOLD_ACC[1])
                x += 8
    for sy in shelves:
        sh_ = m_rect(W, H, 4, sy, 50, sy + 1)
        cv.fill(sh_, WOOD[2])
        cv.fill(top_edge(sh_), WOOD[3])
    for px in (2, 50):
        post = m_rect(W, H, px, 1, px + 2, gy)
        cv.fill(post, WOOD[2])
        cv.fill(left_edge(post), WOOD[3])
    top = m_rect(W, H, 1, 1, 53, 3)
    cv.fill(top, WOOD[2])
    cv.fill(m_rect(W, H, 1, 1, 53, 1), WOOD[4])
    finish(cv, WOOD, PAPER, inks=[ink_of(WOOD)])
    return cv


@prop("lamp_oil", 12, 20)
def lamp_oil(state, f):
    """Bronze oil lamp on a slim stand with a small flame and a stepped glow."""
    W, H = 12, 20
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 18
    cshadow(cv, 6, gy, 4, 0.8)
    base = m_ellipse(W, H, 5.5, gy - 1, 4, 1.4) & (yy <= gy)
    cv.fill(base, GOLD_ACC[0])
    cv.fill(base & (yy < gy - 1), GOLD_ACC[1])
    cv.fill(m_rect(W, H, 5, 8, 6, gy - 2), GOLD_ACC[0])
    cv.fill(m_rect(W, H, 5, 8, 5, gy - 2), GOLD_ACC[1])
    cv.fill(m_rect(W, H, 4, 12, 7, 12), GOLD_ACC[1])
    dish = m_ellipse(W, H, 5.5, 7, 4, 1.6) & (yy >= 6)
    cv.fill(dish, GOLD_ACC[0])
    cv.fill(dish & (yy == 6), GOLD_ACC[2])
    fl = m_poly(W, H, [(5, 6), (7, 6), (6.5, 3), (6, 1), (5, 3)])
    cv.fill(fl, WARM[2])
    cv.fill(m_rect(W, H, 6, 3, 6, 5), WARM[3])
    finish(cv, GOLD_ACC, inks=[ink_of(GOLD_ACC)])
    for s_, a in ((5.0, 0.1), (3.2, 0.16)):
        cv.light(m_ellipse(W, H, 6, 4, s_, s_) & ~cv.solid, WARM[2], a)
    return cv


@prop("weapon_rack_full", 55, 50)
def weapon_rack_full(state, f):
    """Practice-hall rack: wooden swords, staffs, a tasselled spear, a guandao and a training dao."""
    W, H = 55, 50
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 47
    cshadow(cv, 27, gy, 26, 1.5)
    # back frame
    for px in (3, 49):
        post = m_rect(W, H, px, 6, px + 2, gy)
        idx_paint(cv, post, WOOD, 3.4 - (xx - px) * 1.1)
        cv.fill(m_rect(W, H, px - 1, 4, px + 3, 5), WOOD[3])
    rail = m_rect(W, H, 3, 12, 51, 14)
    cv.fill(rail, WOOD[2])
    cv.fill(top_edge(rail), WOOD[3])
    beam = m_rect(W, H, 2, 42, 52, 45)
    cv.fill(beam, WOOD[1])
    cv.fill(top_edge(beam), WOOD[3])
    # weapons: (x, top, kind)
    for (x, top, kind) in ((9, 3, "spear"), (15, 8, "wsword"), (20, 2, "staff"), (26, 7, "guandao"), (33, 10, "wsword"),
                           (38, 4, "staff"), (44, 9, "dao")):
        if kind in ("staff", "spear", "guandao"):
            shaft = m_rect(W, H, x, top + (5 if kind != "staff" else 0), x + 1, 43)
            cv.fill(shaft, WOOD[3])
            cv.fill(m_rect(W, H, x + 1, top, x + 1, 43) & shaft, WOOD[2])
            if kind == "staff":
                cv.fill(m_rect(W, H, x, top, x + 1, top + 2) | m_rect(W, H, x, 38, x + 1, 40), IRON[2])
            if kind == "spear":
                blade = m_poly(W, H, [(x + 0.5, top - 3), (x + 2.5, top + 1), (x + 1.5, top + 5), (x - 0.5, top + 5), (x - 1.5, top + 1)])
                cv.fill(blade, IRON[2])
                cv.fill(m_line(W, H, [(x, top - 1), (x, top + 4)]), IRON[3])
                tas = m_poly(W, H, [(x - 1, top + 5), (x + 2, top + 5), (x + 3, top + 9), (x + 0.5, top + 8), (x - 2, top + 9)])
                cv.fill(tas, CLOTH_R[2])
                cv.fill(left_edge(tas), CLOTH_R[3])
            if kind == "guandao":
                blade = m_poly(W, H, [(x + 1, top - 2), (x + 5, top + 1), (x + 4, top + 8), (x + 1, top + 6)])
                cv.fill(blade, IRON[2])
                cv.fill(m_line(W, H, [(x + 2, top), (x + 4, top + 6)]), IRON[3])
                cv.fill(m_rect(W, H, x - 1, top + 6, x + 2, top + 7), GOLD_ACC[1])
        elif kind == "wsword":  # wooden practice jian
            bl = m_rect(W, H, x, top + 6, x + 1, 42)
            bl[42, x] = bl[42, x + 1] = True
            cv.fill(bl, WOOD_DRY[3])
            cv.fill(m_rect(W, H, x + 1, top + 6, x + 1, 42), WOOD_DRY[2])
            cv.fill(m_rect(W, H, x - 1, top + 5, x + 2, top + 5), WOOD[1])
            cv.fill(m_rect(W, H, x, top, x + 1, top + 4), ROPE[1])
            cv.put(x, top, WOOD[2])
        elif kind == "dao":  # broad sabre with a curved back, hilt up
            bl = m_poly(W, H, [(x, top + 6), (x + 3, top + 6), (x + 4, 36), (x + 2, 41), (x, 40)])
            cv.fill(bl, IRON[2])
            cv.fill(left_edge(bl), IRON[3])
            cv.fill(m_rect(W, H, x - 1, top + 5, x + 4, top + 5), GOLD_ACC[1])
            cv.fill(m_rect(W, H, x + 1, top, x + 2, top + 4), CLOTH_R[1])
            cv.put(x + 1, top, GOLD_ACC[1])
    # rest pegs in front of the weapons
    for px in (9, 15, 20, 26, 33, 38, 44):
        cv.fill(m_rect(W, H, px - 1, 13, px + 2, 13), WOOD[4])
    finish(cv, WOOD, IRON, CLOTH_R)
    return cv
