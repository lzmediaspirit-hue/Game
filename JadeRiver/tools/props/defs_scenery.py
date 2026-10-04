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


# ================================================================== fences, walls, cliffs (segments repeat along x)
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


# ================================================================== interior furnishings
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
