#!/usr/bin/env python3
"""Layered parallax sky panoramas for Jade River.

Writes art/backdrops/<id>_<n>.png (layer n, drawn back to front) and data/backdrops.json.

    python3 tools/backdrops/build_backdrops.py                 # everything
    python3 tools/backdrops/build_backdrops.py --only valley_day,cave --no-write   # preview only

Engine contract (data/backdrops.json):
  * every layer is 1280 px wide and tiles seamlessly left-right (repeat-x);
  * it is drawn with its bottom edge at screen y `bottom` (camera at default height) and
    scrolls horizontally by `parallax` x camera x (0 = fixed sky);
  * layer 0 is an opaque 1280x720 sky/gradient, later layers have transparent tops.

Art is authored at native pixel scale 2 (640 art px wide, upscaled x2 nearest). Every
x-dependent function (noise, shapes, placements) is periodic over 640 art px, so tiles
wrap exactly. Gradients use 4x4 ordered dithering between flat bands; mist uses a few
flat alpha steps. No blur, no anti-aliasing. Output is deterministic (byte-identical
on re-run): all randomness is seeded from stable strings.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

sys.dont_write_bytecode = True  # keep the repo free of __pycache__

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "props"))

from pixlib import Canvas, hexc, m_line, m_poly, save_png, seed_of  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DEFAULT_REVIEW = "/tmp/claude-0/-home-user-Game/13461237-7857-505a-bd3b-55d18a20fe2c/scratchpad/art_bd"
SCALE = 2
W = 640            # art px per tile (1280 screen px)
SKY_H = 360        # art px (720 screen px)


# =============================================================== colour + noise utilities
def C(h):
    return hexc(h) if isinstance(h, str) else tuple(h)


def R(*hexes):
    return [C(h) for h in hexes]


def mixc(a, b, t):
    a, b = C(a), C(b)
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def lerp_stops(stops, t):
    """stops: [(pos, colour), ...] ascending; returns colour at t (piecewise linear)."""
    if t <= stops[0][0]:
        return C(stops[0][1])
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        if t <= p1:
            return mixc(c0, c1, (t - p0) / max(1e-9, p1 - p0))
    return C(stops[-1][1])


def hazed(ramp, haze, t):
    return [mixc(c, haze, t) for c in ramp]


def rng(*parts):
    return np.random.default_rng(seed_of(*parts))


_B4 = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) + 0.5) / 16.0
_GRIDS = {}


def grids(h):
    """(yy, xx, bayer) for an h x W canvas (cached)."""
    if h not in _GRIDS:
        yy, xx = np.mgrid[0:h, 0:W]
        B = np.tile(_B4, (h // 4 + 1, W // 4 + 1))[:h, :W]
        _GRIDS[h] = (yy, xx, B)
    return _GRIDS[h]


def dq(v, B, n=None, sharp=1.0):
    """Ordered-dither a continuous index field v into integers.

    sharp > 1 narrows the dithered transition between neighbouring bands."""
    fl = np.floor(v)
    fr = v - fl
    if sharp != 1.0:
        fr = np.clip((fr - 0.5) * sharp + 0.5, 0.0, 1.0)
    idx = (fl + (fr > B)).astype(int)
    if n is not None:
        idx = np.clip(idx, 0, n - 1)
    return idx


def pn1(seed, cell, octaves=1, n=W):
    """Periodic 1D value noise in [0,1] (period n)."""
    x = np.arange(n, dtype=float)
    g = rng("pn1", seed)
    out = np.zeros(n)
    amp, norm, c = 1.0, 0.0, float(cell)
    for _ in range(octaves):
        k = max(1, int(round(n / c)))
        vals = g.random(k)
        f = x / (n / k)
        i0 = np.floor(f).astype(int)
        t = f - i0
        t = t * t * (3 - 2 * t)
        out += amp * (vals[i0 % k] * (1 - t) + vals[(i0 + 1) % k] * t)
        norm += amp
        amp *= 0.5
        c /= 2.0
    return out / norm


def pn2(h, seed, cx, cy=None, octaves=1):
    """2D value noise in [0,1], periodic in x over W, anisotropic cells (cx, cy)."""
    cy = cy or cx
    yy, xx, _ = grids(h)
    g = rng("pn2", seed)
    out = np.zeros((h, W))
    amp, norm = 1.0, 0.0
    for _ in range(octaves):
        kx = max(1, int(round(W / cx)))
        sx = W / kx
        ky = int(math.ceil(h / cy)) + 2
        gv = g.random((ky, kx))
        fx = xx / sx
        fy = yy / cy
        x0 = np.floor(fx).astype(int)
        y0 = np.floor(fy).astype(int)
        tx = fx - x0
        ty = fy - y0
        tx = tx * tx * (3 - 2 * tx)
        ty = ty * ty * (3 - 2 * ty)
        x1 = (x0 + 1) % kx
        x0 = x0 % kx
        y1 = y0 + 1
        v = (gv[y0, x0] * (1 - tx) * (1 - ty) + gv[y0, x1] * tx * (1 - ty)
             + gv[y1, x0] * (1 - tx) * ty + gv[y1, x1] * tx * ty)
        out += amp * v
        norm += amp
        amp *= 0.5
        cx /= 2.0
        cy /= 2.0
    return out / norm


# =============================================================== wrapped shapes
def xx_all(h):
    return grids(h)[1]


def wdx(x, cx):
    """Signed periodic distance x - cx in (-W/2, W/2]."""
    return (np.asarray(x, float) - cx + W / 2.0) % W - W / 2.0


def wpoly(h, pts):
    m = np.zeros((h, W), bool)
    for off in (-W, 0, W):
        m |= m_poly(W, h, [(x + off, y) for x, y in pts])
    return m


def wline(h, pts, width=1):
    m = np.zeros((h, W), bool)
    for off in (-W, 0, W):
        m |= m_line(W, h, [(x + off, y) for x, y in pts], width)
    return m


def wellipse(h, cx, cy, rx, ry):
    yy, xx, _ = grids(h)
    return (wdx(xx, cx) / max(rx, 0.5)) ** 2 + ((yy - cy) / max(ry, 0.5)) ** 2 <= 1.0


def wrect(h, x0, y0, x1, y1):
    """Inclusive rectangle, x wraps."""
    yy, xx, _ = grids(h)
    w = x1 - x0
    return (((xx - x0) % W) <= w) & (yy >= y0) & (yy <= y1)


def sh(m, dx, dy):
    """Shift mask: wraps in x, clears in y."""
    o = np.roll(m, dx, 1)
    if dy > 0:
        o = np.vstack([np.zeros((dy, W), bool), o[:-dy]])
    elif dy < 0:
        o = np.vstack([o[-dy:], np.zeros((-dy, W), bool)])
    return o


def top_rim(m):
    return m & ~sh(m, 0, 1)


def bot_rim(m):
    return m & ~sh(m, 0, -1)


def left_rim(m):
    return m & ~sh(m, 1, 0)


def right_rim(m):
    return m & ~sh(m, -1, 0)


def despeck(m):
    """Remove isolated single pixels / 1px spurs from a mask, fill 1px pinholes."""
    n = sh(m, 1, 0).astype(int) + sh(m, -1, 0) + sh(m, 0, 1) + sh(m, 0, -1)
    m = m & (n >= 2)
    n = sh(m, 1, 0).astype(int) + sh(m, -1, 0) + sh(m, 0, 1) + sh(m, 0, -1)
    return m | (n >= 3)


# =============================================================== painting primitives
def paint(cv, m, ramp, v, sharp=1.0):
    """Dither-quantise index field v (float, ramp index) into mask m."""
    if not m.any():
        return
    _, _, B = grids(cv.h)
    idx = dq(v, B, len(ramp), sharp)
    cv.fill_idx(m, idx, ramp)


def flat(cv, m, c, a=1.0):
    cv.fill(m, C(c), a)


def put(cv, x, y, c, a=1.0):
    cv.put(int(x) % W, int(y), C(c), a)


def haze_fade(cv, m, haze, t, steps=4, sharp=1.6):
    """Mix painted pixels toward `haze` by t in [0,1] using a few dithered flat steps."""
    _, _, B = grids(cv.h)
    q = dq(np.clip(t, 0, 1) * steps, B, steps + 1, sharp) / float(steps)
    mm = m & (q > 0)
    hz = np.array(C(haze), float)
    cv.rgb[mm] = cv.rgb[mm] * (1 - q[mm, None]) + hz * q[mm, None]


def stamp(cv, spr, x0, y0, pal, base=0, clip=None):
    """Paste an index sprite (-1 = empty, else offset from `base`) with x wrapping."""
    h, w = spr.shape
    ys = np.arange(y0, y0 + h)
    ok = (ys >= 0) & (ys < cv.h)
    if not ok.any():
        return
    sub = spr[ok]
    ys = ys[ok]
    xs = np.arange(x0, x0 + w) % W
    Y, X = np.meshgrid(ys, xs, indexing="ij")
    m = sub >= 0
    if clip is not None:
        m &= clip[Y, X]
    if not m.any():
        return
    pal = np.array(pal, float)
    cv.rgb[Y[m], X[m]] = pal[np.clip(sub[m] + base, 0, len(pal) - 1)]
    cv.a[Y[m], X[m]] = 1.0


_CROWNS = {}
EMPTY = -100


def crown_sprite(r, squash=0.85):
    """Round tree crown as ramp offsets: 0 body, +1 upper-left light, +2 top-left glint,
    -1 lower-right shade and base row; EMPTY outside."""
    key = (r, squash)
    if key in _CROWNS:
        return _CROWNS[key]
    s = int(math.ceil(r))
    yy, xx = np.mgrid[-s:s + 1, -s:s + 1]
    ry = max(0.8, r * squash)
    inside = (xx / (r + 0.35)) ** 2 + (yy / (ry + 0.35)) ** 2 <= 1.0
    spr = np.full(inside.shape, EMPTY)
    spr[inside] = 0
    d = (xx / (r + 0.35)) + (yy / (ry + 0.35))
    spr[inside & (d < -0.55)] = 1
    spr[inside & (d < -1.0)] = 2
    below = np.vstack([inside[1:], np.zeros((1, inside.shape[1]), bool)])
    spr[inside & ((d > 0.55) | ~below)] = -1
    _CROWNS[key] = spr
    return spr


def stamp_crown(cv, spr, cx, cy, pal, base, clip=None):
    """Stamp an offset sprite centred on (cx, cy); x wraps."""
    h, w = spr.shape
    sy, sx = h // 2, w // 2
    ys = np.arange(cy - sy, cy - sy + h)
    ok = (ys >= 0) & (ys < cv.h)
    if not ok.any():
        return
    sub = spr[ok]
    ys = ys[ok]
    xs = np.arange(cx - sx, cx - sx + w) % W
    Y, X = np.meshgrid(ys, xs, indexing="ij")
    m = sub > EMPTY
    if clip is not None:
        m &= clip[Y, X]
    if not m.any():
        return
    pal = np.array(pal, float)
    cv.rgb[Y[m], X[m]] = pal[np.clip(sub[m] + base, 0, len(pal) - 1)]
    cv.a[Y[m], X[m]] = 1.0


E_ = EMPTY
SHRUBS = [
    np.array([[E_, 1, 0, E_], [0, 0, -1, -1]]),
    np.array([[E_, 1, 1, E_, E_], [1, 0, 0, 0, E_], [0, 0, -1, -1, -1]]),
    np.array([[E_, E_, 1, 0, E_, E_], [E_, 1, 0, 0, 0, E_], [1, 0, 0, -1, -1, -1]]),
]


# =============================================================== sky elements
def sky_layer(stops, h=SKY_H, bands=18, sharp=2.2):
    cv = Canvas(W, h)
    yy, _, B = grids(h)
    ramp = [lerp_stops(stops, i / (bands - 1)) for i in range(bands)]
    v = yy / (h - 1) * (bands - 1)
    paint(cv, np.ones((h, W), bool), ramp, v, sharp)
    return cv


def cloud(cv, cx, cy, length, thick, seed, pal, flat_bottom=True, tail=True):
    """Stylised cumulus: overlapping puffs, lit upper-left rims, flat shaded base.

    pal = (shade, body, light, glint)."""
    g = rng("cloud", seed)
    n = max(2, int(length / max(3.0, thick * 0.9)))
    puffs = []
    for i in range(n):
        t = i / (n - 1) - 0.5
        r = thick * (1.0 - abs(t) * 1.1) * g.uniform(0.75, 1.1) + 1.5
        px = cx + t * length + g.uniform(-2, 2)
        py = cy - r * 0.55 + g.uniform(-1, 1)
        puffs.append((px, py, r))
    # back row first (higher puffs), front row later
    puffs.sort(key=lambda p: p[1])
    base_y = cy + thick * 0.25
    total = np.zeros((cv.h, W), bool)
    for (px, py, r) in puffs:
        m = wellipse(cv.h, px, py, r * 1.35, r)
        if flat_bottom:
            m &= grids(cv.h)[0] <= base_y
        if not m.any():
            continue
        flat(cv, m, pal[1])
        rim = m & ~sh(m, 1, 1)
        flat(cv, rim & ~sh(m, 0, 1), pal[2])
        flat(cv, rim & ~sh(m, 1, 0) & ~top_rim(m), pal[2])
        flat(cv, top_rim(m) & (wdx(grids(cv.h)[1], px) < -r * 0.3), pal[3])
        flat(cv, (m & ~sh(m, -1, -1)) & ~top_rim(m), pal[0])
        total |= m
    flat(cv, bot_rim(total), pal[0])
    if tail:
        yy, xx, _ = grids(cv.h)
        for k, side in enumerate((-1, 1)):
            ln = length * g.uniform(0.25, 0.45)
            x0 = cx + side * length * 0.45
            y = int(round(base_y)) - k
            seg = (np.abs(wdx(xx, x0 + side * ln / 2)) <= ln / 2) & (yy == y)
            flat(cv, seg, pal[1])
            flat(cv, seg & sh(seg, 0, 0) & (np.abs(wdx(xx, x0 + side * ln / 2)) > ln / 2 - 3), pal[0])
    return total


def streak(cv, cx, y, length, pal, seed, rows=2):
    """Long thin horizontal cloud streak (ink-wash style)."""
    yy, xx, _ = grids(cv.h)
    g = rng("streak", seed)
    m = np.zeros((cv.h, W), bool)
    for r in range(rows):
        ln = length * (1.0 - r * 0.35) * g.uniform(0.8, 1.0)
        off = g.uniform(-length * 0.15, length * 0.15)
        m |= (np.abs(wdx(xx, cx + off)) <= ln / 2) & (yy == y + r)
    flat(cv, m, pal[1])
    flat(cv, top_rim(m) & (wdx(xx, cx) < 0), pal[2])
    flat(cv, bot_rim(m) & (wdx(xx, cx) > -length * 0.2), pal[0])
    return m


def stars(cv, seed, count, y0, y1, pal, twinkle=6):
    g = rng("stars", seed)
    yy, _, _ = grids(cv.h)
    for i in range(count):
        x = int(g.integers(0, W))
        y = int(g.integers(y0, y1))
        # sparser toward the horizon
        if g.random() < (y - y0) / max(1, y1 - y0) * 0.8:
            continue
        c = pal[int(g.integers(0, len(pal) - 1))]
        put(cv, x, y, c)
        if i % twinkle == 0:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                put(cv, (x + dx) % W, y + dy, pal[0])
            put(cv, x, y, pal[-1])


def disc(cv, cx, cy, r, pal, halo=None, halo_steps=((2.6, 0.10), (1.9, 0.16), (1.45, 0.24)), crescent=0.0):
    """Sun / moon disc with stepped halo. pal = (shade, body, light)."""
    if halo is not None:
        for s, a in halo_steps:
            m = wellipse(cv.h, cx, cy, r * s, r * s)
            flat(cv, m, halo, a)
    m = wellipse(cv.h, cx, cy, r, r)
    flat(cv, m, pal[1])
    yy, xx, _ = grids(cv.h)
    d = wdx(xx, cx) / r + (yy - cy) / r
    flat(cv, m & (d > 0.75), pal[0])
    flat(cv, m & (d < -0.8), pal[2])
    if crescent:
        cut = wellipse(cv.h, cx + r * crescent, cy - r * 0.25, r * 0.95, r * 0.95)
        return m, cut
    return m, None


# =============================================================== landforms
def karst_profile(cx, top, base, hw, p=3.0, skirt=1.9, skirt_h=0.3, seed=0, rough=1.2, asym=0.0):
    """Top y of a tower peak per column: rounded dome, steep sides, flared foot.

    asym > 0 widens the left flank and narrows the right one (summit leans right)."""
    dx = wdx(np.arange(W), cx)
    hws = np.where(dx < 0, hw * (1 + asym), hw * (1 - asym))
    t = np.abs(dx) / hws
    core = np.where(t < 1, top + (base - top) * np.clip(t, 0, 1) ** p, np.inf)
    ts = np.abs(dx) / (hws * skirt)
    sk_top = base - (base - top) * skirt_h
    sk = np.where(ts < 1, sk_top + (base - sk_top) * np.clip(ts, 0, 1) ** 1.5, np.inf)
    prof = np.minimum(core, sk)
    if rough:
        prof = prof + (pn1(("kr", seed), 10, 2) - 0.5) * 2 * rough
    return np.round(prof), dx


def gen_peaks(seed, n, top_lo, top_hi, hw_lo, hw_hi, jitter=0.35):
    """Spread n peaks around the tile with varied size; tallest first (drawn behind)."""
    g = rng("peaks", seed)
    out = []
    step = W / n
    for i in range(n):
        cx = (i + 0.5 + g.uniform(-jitter, jitter)) * step
        top = g.uniform(top_lo, top_hi)
        hw = g.uniform(hw_lo, hw_hi)
        out.append((cx, top, hw))
    out.sort(key=lambda p: p[1])
    return out


def row_u(mask, dx):
    """Horizontal position (0 = left edge, 1 = right edge) of each pixel inside its row run."""
    dxx = np.broadcast_to(dx[None, :], mask.shape)
    left = np.where(mask, dxx, np.inf).min(axis=1)
    right = np.where(mask, dxx, -np.inf).max(axis=1)
    span = np.maximum(right - left, 1.0)
    return np.clip((dxx - left[:, None]) / span[:, None], 0, 1)


def karst_peak(cv, cx, top, hw, ramp, seed, base=None, p=None, skirt=None, skirt_h=None, gain=1.25, mid=None,
               rough=1.0, trees=None, tree_frac=0.4, ledges=0.5, rim=True, dark_edge=True, sharp=3.5,
               shoulder=0.6, crevice=1.0, asym=None):
    """One karst tower in cel bands (lit left face, shadowed right), crevices and ledge shrubs."""
    h = cv.h
    base = h + 2 if base is None else base
    yy, xx, B = grids(h)
    g = rng("kp", seed)
    p = p or g.uniform(2.0, 3.4)
    skirt = skirt or g.uniform(1.4, 2.0)
    skirt_h = g.uniform(0.18, 0.4) if skirt_h is None else skirt_h
    asym = g.uniform(-0.3, 0.3) if asym is None else asym
    prof, dx = karst_profile(cx, top, base, hw, p, skirt, skirt_h, seed, rough, asym)
    if g.random() < shoulder:
        side = -1 if g.random() < 0.5 else 1
        sc = cx + side * hw * g.uniform(0.55, 0.9)
        st = top + (base - top) * g.uniform(0.25, 0.5)
        p2, _ = karst_profile(sc, st, base, hw * g.uniform(0.45, 0.7), 2.4, 1.4, 0.2, (seed, "sh"), rough)
        prof = np.minimum(prof, p2)
    m = yy >= prof[None, :]
    m &= np.abs(dx)[None, :] < hw * 3
    if not m.any():
        return m, prof
    u = row_u(m, dx)
    n = len(ramp)
    mid = (n - 1) * 0.5 if mid is None else mid
    depth = yy - prof[None, :]
    v = mid + (0.5 - u) * 2 * gain
    v = v + np.clip(2.0 - depth * 0.5, 0, 2.0) * 0.45
    if crevice:
        st = pn2(h, ("cun", seed), 2.5, 16, 2)
        v = v - ((st > 0.66) & (u > 0.3)) * 1.2 * crevice
        v = v + ((st < 0.2) & (u < 0.5) & (depth > 3)) * 0.9 * crevice
    paint(cv, m, ramp, v, sharp=sharp)
    if rim:
        flat(cv, left_rim(m) & (depth > 1), ramp[-1])
        flat(cv, top_rim(m) & (u < 0.55), ramp[-1])
    if dark_edge:
        flat(cv, right_rim(m) & (depth > 0) & (u > 0.5), ramp[0])
    if trees is not None:
        lim = top + (base - top) * tree_frac
        x = cx - hw * 1.6
        while x < cx + hw * 1.6:
            xi = int(x) % W
            near_top = (prof[xi] - top) / max(1.0, base - top)
            if prof[xi] < lim and m[min(h - 1, max(0, int(prof[xi]) + 1)), xi] and g.random() < 0.9 - near_top * 1.5:
                k = int(g.integers(0, 3))
                stamp_crown(cv, SHRUBS[k], xi, int(prof[xi]) + (k > 0), trees, 2 if g.random() < 0.5 else 1)
            x += g.uniform(2.0, 3.5)
        # a few ledges: short horizontal runs of shrubs across the face
        for _ in range(int(ledges * hw / 6)):
            ly = int(g.uniform(top + (base - top) * 0.15, lim + (base - lim) * 0.35))
            if not (0 <= ly < h):
                continue
            row = np.nonzero(m[ly] & (depth[ly] > 4))[0]
            if len(row) < 6:
                continue
            x0 = int(g.choice(row))
            for j in range(int(g.integers(2, 5))):
                xj = (x0 + j * 3 + int(g.integers(0, 2))) % W
                if m[ly, xj] and depth[ly, xj] > 3:
                    stamp_crown(cv, SHRUBS[int(g.integers(0, 2))], xj, ly + int(g.integers(-1, 2)), trees,
                                1 if u[ly, xj] < 0.5 else 0)
    return m, prof


def hill_profile(y0, amp, seed, cell=160, octaves=3, bumps=0.0):
    n = pn1(("hill", seed), cell, octaves)
    prof = y0 - (n - 0.5) * 2 * amp
    if bumps:
        prof = prof - (pn1(("hb", seed), 6, 1) - 0.5) * bumps
    return np.round(prof)


def hill_row(cv, prof, ramp, seed, gain=1.3, mid=None, rim=True, top_rows=2, mask_extra=None, sharp=3.0, fall=0.8):
    """Fill everything below `prof`, cel-lit by slope (upper-left light)."""
    h = cv.h
    yy, xx, B = grids(h)
    m = yy >= prof[None, :]
    if mask_extra is not None:
        m &= mask_extra
    n = len(ramp)
    mid = (n - 1) * 0.45 if mid is None else mid
    slope = (np.roll(prof, -3) - np.roll(prof, 3)) / 6.0
    light = np.clip(-slope * 1.4, -1, 1)
    v = mid + light[None, :] * gain
    depth = yy - prof[None, :]
    v = v + np.clip(top_rows - depth, 0, top_rows) * 0.5
    v = v - np.clip(depth / max(1.0, h - prof.min()), 0, 1) * fall
    paint(cv, m, ramp, v, sharp=sharp)
    if rim:
        flat(cv, top_rim(m) & (light[None, :] > -0.2), ramp[min(n - 1, int(mid) + 2)])
    return m


def treeline(cv, prof, pal, seed, r=2.5, fill=None, gain=1.0, spacing=1.55, var=1, below=None, rvar=0.3,
             conifer=0.0, light_by_slope=True, rows=0, row_gap=None, row_density=0.55):
    """A forest edge: a row of round crowns riding `prof`, flat cel-lit body beneath.

    pal dark->light; the body uses index `fill` (default one below the crown base)."""
    h = cv.h
    yy, xx, B = grids(h)
    g = rng("treeline", seed)
    n = len(pal)
    cb = (n - 1) // 2
    fill = max(0, cb - 1) if fill is None else fill
    body = yy >= (prof[None, :] + int(r * 0.5))
    if below is not None:
        body &= yy <= below[None, :]
    slope = (np.roll(prof, -4) - np.roll(prof, 4)) / 8.0
    lit = np.clip(-slope * 1.5, -1, 1) if light_by_slope else np.zeros(W)
    v = fill + 0.5 + lit[None, :] * gain * 0.8 - np.clip((yy - prof[None, :]) / 40.0, 0, 1) * 0.9
    paint(cv, body, pal, v, sharp=3.0)
    x = g.uniform(0, r)
    while x < W:
        xi = int(x) % W
        rr = max(1.0, round((r * (1 + g.uniform(-rvar, rvar))) * 2) / 2)
        cy = int(prof[xi] + g.integers(-1, 2))
        b = cb + int(g.integers(-var, var + 1)) + (1 if lit[xi] > 0.3 else 0) - (1 if lit[xi] < -0.4 else 0)
        if conifer and g.random() < conifer:
            cone(cv, xi, cy + int(rr), int(rr * 3.2), int(rr + 0.5), pal, b)
        else:
            stamp_crown(cv, crown_sprite(rr, 0.85), xi, cy, pal, b, clip=(yy <= below[None, :]) if below is not None else None)
        x += rr * spacing + g.uniform(-0.3, 0.6)
    # interior rows of crowns (forest texture inside big hills), clipped to the body
    gap = row_gap or r * 2.6
    for k in range(1, rows + 1):
        sub = prof + k * gap + np.round((pn1(("tlr", seed, k), 20, 2) - 0.5) * 4)
        x = g.uniform(0, r * 2)
        while x < W:
            xi = int(x) % W
            cy = int(sub[xi])
            if 0 <= cy < h and body[cy, xi] and g.random() < row_density:
                b = cb - 1 + int(g.integers(-1, 2)) + (1 if lit[xi] > 0.3 else 0) - (k > 2)
                stamp_crown(cv, crown_sprite(r, 0.85), xi, cy, pal, b, clip=body)
            x += r * spacing * 1.2 + g.uniform(-0.3, 1.0)
    return body


def cone(cv, x, by, ht, hw, pal, b):
    """Small conifer: stacked triangle, lit left edge."""
    h = cv.h
    m = wpoly(h, [(x - hw - 0.5, by), (x + hw + 0.5, by), (x + 0.5, by - ht), (x - 0.5, by - ht)])
    yy, xx, _ = grids(h)
    d = wdx(xx, x)
    n = len(pal)
    flat(cv, m, pal[max(0, min(n - 1, b))])
    flat(cv, m & (d < 0), pal[max(0, min(n - 1, b + 1))])
    flat(cv, m & (d > 0.5), pal[max(0, min(n - 1, b - 1))])
    # tier notches
    for k in range(1, 4):
        ty = int(by - ht * k / 4)
        flat(cv, m & (yy == ty) & (np.abs(d) > 0.5), pal[max(0, b - 1)])


def forest(cv, region, prof, pal, seed, r=2.0, step=None, ao=0.02, var=1, base=None, clip_up=None, density=1.0):
    """Stack rows of round crowns over `region` (top rows poke above `prof`)."""
    h = cv.h
    g = rng("forest", seed)
    step = step or max(2, int(round(r * 1.25)))
    spr = crown_sprite(r)
    top = int(max(0, prof.min() - 1))
    clip = region | (sh(region, 0, -int(math.ceil(r))) if clip_up is None else clip_up)
    base = (len(pal) - 1) // 2 if base is None else base
    ys = list(range(top, h + int(r), step))
    for ri, y in enumerate(ys):
        off = (ri % 2) * r * 0.9
        x = g.uniform(0, r) + off
        while x < W + off:
            xi = int(x) % W
            jy = y + int(g.integers(-1, 2))
            if 0 <= jy < h and region[jy, xi] and g.random() < density:
                b = base + int(g.integers(-var, var + 1)) - int(ao * (jy - prof[xi]))
                if jy - prof[xi] < r:
                    b = max(b, base)
                stamp_crown(cv, spr, xi, jy, pal, b, clip=clip)
            x += r * 1.7 + g.uniform(-0.4, 0.6)


def mist_band(cv, y, thick, seed, col, alphas=(0.22, 0.38, 0.55), amp=3.0, cell=80, taper=0.55, gaps=0.18):
    """Horizontal translucent mist bank with wavy edges and flat alpha steps (densest in the core)."""
    h = cv.h
    yy, xx, _ = grids(h)
    n_top = pn1(("mt", seed), cell, 2)
    n_bot = pn1(("mb", seed), cell, 2)
    n_len = pn1(("ml", seed), cell * 2, 1)
    level = np.zeros((h, W), int)
    L = len(alphas)
    for k in range(L):
        s = 1.0 - k * taper / max(1, L - 1) if L > 1 else 1.0
        ends = np.clip((n_len - gaps - k * 0.1) / 0.22, 0, 1) ** 0.7  # bands thin out to nothing at their ends
        half = thick * 0.5 * s * ends[None, :]
        t = y - half + (n_top[None, :] - 0.5) * 2 * amp * ends[None, :]
        b = y + half * 0.6 + (n_bot[None, :] - 0.5) * 2 * amp * 0.5 * ends[None, :]
        gate = (ends > 0.05)[None, :]
        level[(yy >= np.round(t)) & (yy <= np.round(b)) & gate & (b - t >= 0.5)] = k + 1
    for k in range(L):
        flat(cv, level == k + 1, col, alphas[k])
    return level > 0


def base_fade(cv, y0, y1, haze, steps=4, sharp=5.0, m=None):
    """Fade everything painted between rows y0..y1 toward `haze` (flat dithered bands); solid below y1."""
    yy, _, _ = grids(cv.h)
    t = np.clip((yy - y0) / max(1.0, (y1 - y0)), 0, 1)
    mm = (cv.a > 0) if m is None else m
    haze_fade(cv, mm, haze, t, steps=steps, sharp=sharp)


def light_shafts(cv, specs, col, slope=0.55, fade_y=None, alphas=(0.10, 0.16)):
    """Diagonal light shafts: specs [(cx, width), ...], leaning right as they go down."""
    h = cv.h
    yy, xx, _ = grids(h)
    for (cx, w) in specs:
        d = np.abs(wdx(xx - yy * slope, cx))
        for k, a in enumerate(alphas):
            m = d <= w * (1.0 - k * 0.45) / 2
            if fade_y is not None:
                m &= yy <= fade_y - k * 10
            flat(cv, m, col, a)


# =============================================================== water
def river(cv, ytop, ybot, pal, seed, bank=None, glint=None, reflect=None, reflect_rows=3, ripples=0.28):
    """Horizontal river surface between per-column ytop/ybot.

    pal dark->light (>= 5); bank = far-bank edge colour; reflect = colour of mirrored far bank."""
    h = cv.h
    yy, xx, B = grids(h)
    ytop = np.round(ytop)
    ybot = np.round(ybot)
    m = (yy >= ytop[None, :]) & (yy <= ybot[None, :])
    depth = (yy - ytop[None, :]) / np.maximum(1, (ybot - ytop))[None, :]
    n = len(pal)
    v = (n - 1) * 0.62 - depth * (n - 1) * 0.35
    rip = pn2(h, ("rip", seed), 22, 1.6, 2)
    v = v + (rip > 0.64) * 1.0 - (rip < 0.3) * 0.8
    paint(cv, m, pal, v, sharp=3.0)
    d0 = yy - ytop[None, :]
    if reflect is not None:
        rr = m & (d0 <= reflect_rows - 1 + np.round(pn1(("rr", seed), 12, 1) * 2)[None, :])
        flat(cv, rr, reflect)
        # broken lower edge of the reflection
        flat(cv, rr & sh(~rr & m, 0, -1) & (rip > 0.55), pal[max(0, n - 3)])
    if bank is not None:
        flat(cv, top_rim(m), bank)
    if glint is not None:
        gl = m & (rip > 0.8 - ripples * 0.2) & (d0 > reflect_rows + 1)
        gl &= pn2(h, ("gl", seed), 40, 6, 1) > 0.55
        flat(cv, gl, glint)
    return m


def reflections(cv, water, xs, ytop, pal, seed, length=10):
    """Broken vertical reflections (lanterns / moon) on a water mask."""
    g = rng("refl", seed)
    for x in xs:
        xi = int(x) % W
        y0 = int(ytop[xi]) + 1
        for k in range(length):
            if g.random() < 0.72:
                w = 1 + (k % 3 == 1) + (k < 2)
                for dx in range(-(w // 2), w - w // 2):
                    xx = (xi + dx + (k % 2)) % W
                    if y0 + k < cv.h and water[y0 + k, xx]:
                        put(cv, xx, y0 + k, pal[0] if k > length * 0.55 else pal[1])


# =============================================================== small structures
def pagoda(cv, cx, by, tiers, w0, pal, windows=None, shrink=0.75, body_h=2, spire=3):
    """Tiny tiered pagoda silhouette standing on (cx, by). pal = (dark, mid, light)."""
    h = cv.h
    y = by
    bw = w0
    allm = np.zeros((h, W), bool)
    lights = []
    for i in range(tiers):
        half = bw / 2.0
        body = wrect(h, int(round(cx - half)), y - body_h + 1, int(round(cx + half)), y)
        roof = wrect(h, int(round(cx - half - 2)), y - body_h, int(round(cx + half + 2)), y - body_h)
        tips = (wrect(h, int(round(cx - half - 3)), y - body_h - 1, int(round(cx - half - 3)), y - body_h - 1)
                | wrect(h, int(round(cx + half + 3)), y - body_h - 1, int(round(cx + half + 3)), y - body_h - 1))
        cap = wrect(h, int(round(cx - half - 1)), y - body_h - 1, int(round(cx + half + 1)), y - body_h - 1)
        flat(cv, body, pal[1])
        flat(cv, body & left_rim(body), pal[2])
        flat(cv, roof | tips | cap, pal[0])
        flat(cv, cap & left_rim(cap), pal[2])
        allm |= body | roof | tips | cap
        lights.append((int(round(cx)), y - body_h + 1))
        y -= body_h + 2
        bw = max(2.0, bw * shrink + 0.5)
    sp = wrect(h, int(round(cx)), y - spire + 2, int(round(cx)), y + 1)
    flat(cv, sp, pal[0])
    allm |= sp
    if windows is not None:
        for (lx, ly) in lights:
            put(cv, lx % W, ly, windows)
    return allm


def hall(cv, x0, by, w, wall_h, roof_h, roof_pal, wall_pal, post_col=None, lit=None, tiers=1, seed=0):
    """Small side-view temple hall: glazed roof with upturned eaves over a white/wood wall."""
    h = cv.h
    yy, xx, _ = grids(h)
    x1 = x0 + w - 1
    wall = wrect(h, x0 + 2, by - wall_h + 1, x1 - 2, by)
    flat(cv, wall, wall_pal[1])
    flat(cv, left_rim(wall), wall_pal[2])
    flat(cv, wrect(h, x0 + 2, by - wall_h + 1, x1 - 2, by - wall_h + 1), wall_pal[0])  # eave shadow
    if post_col is not None:
        for px in range(x0 + 3, x1 - 1, max(3, (w - 4) // 4)):
            flat(cv, wrect(h, px, by - wall_h + 2, px, by), post_col)
    if lit is not None:
        for px in range(x0 + 5, x1 - 3, max(4, (w - 4) // 3)):
            flat(cv, wrect(h, px, by - wall_h + 3, px + 1, by - 2), lit)
    top = by - wall_h
    for t in range(tiers):
        rw = w + 4 - t * (w // 3)
        cxr = x0 + w / 2.0
        ry0 = top - roof_h + 1
        pts = [(cxr - rw / 2 - 1, top - 1), (cxr - rw / 2 + roof_h * 0.9, ry0), (cxr + rw / 2 - roof_h * 0.9, ry0),
               (cxr + rw / 2 + 1, top - 1), (cxr + rw / 2 - 1, top), (cxr - rw / 2 + 1, top)]
        roof = wpoly(h, pts)
        flat(cv, roof, roof_pal[1])
        flat(cv, top_rim(roof), roof_pal[2])
        flat(cv, bot_rim(roof), roof_pal[0])
        flat(cv, top_rim(roof) & (wdx(xx, cxr) < -rw * 0.1), roof_pal[3])
        # upturned eave tips
        for sx in (-1, 1):
            tx = int(round(cxr + sx * (rw / 2 + 1)))
            put(cv, tx % W, top - 2, roof_pal[0])
        # ridge
        flat(cv, wrect(h, int(cxr - rw / 2 + roof_h), ry0 - 1, int(cxr + rw / 2 - roof_h), ry0 - 1), roof_pal[0])
        if t < tiers - 1:
            ww = rw - roof_h * 2 - 4
            sub = wrect(h, int(cxr - ww / 2), ry0 - 3, int(cxr + ww / 2), ry0 - 1)
            flat(cv, sub, wall_pal[1])
            flat(cv, left_rim(sub), wall_pal[2])
            top = ry0 - 3
    return


# =============================================================== trees for near layers
def willow(cv, x, by, height, spread, fr, tr, seed, lean=0.0):
    """Weeping willow: leaning trunk and arms under overlapping drapes of hanging strands.

    Each drape has a bumpy leafy dome on top and a ragged curtain of 1px strands whose
    ends thin out (gaps show the scene behind). fr = frond ramp dark->light (>= 6),
    tr = trunk ramp (>= 4)."""
    h = cv.h
    yy, xx, B = grids(h)
    g = rng("willow", seed)
    n = len(fr)
    fork_y = by - height * 0.42
    fx = x + lean * height * 0.14
    cx = fx + lean * 4
    top = by - height
    # trunk with root flare, bark streaks and two main arms
    pts = [(x - 5, by), (x + 5, by), (x + 3, by - 3), (x + 2.5 + lean * 3, by - height * 0.2), (fx + 2.5, fork_y),
           (fx - 2.5, fork_y), (x - 2 + lean * 2, by - height * 0.2), (x - 3, by - 3)]
    trunk = wpoly(h, pts)
    for sgn in (-1, 1):
        ex, ey = cx + sgn * spread * 0.55, top + height * 0.22
        trunk |= wline(h, [(fx + sgn, fork_y), ((fx + ex) / 2, fork_y - height * 0.12), (ex, ey)], 3)
    u = row_u(trunk, wdx(np.arange(W), x))
    bark = pn2(h, ("bark", seed), 2, 9, 1)
    v = (len(tr) - 1) * (0.95 - u * 0.95) - (bark > 0.65) * 1.0
    paint(cv, trunk, tr, v, sharp=3)
    flat(cv, left_rim(trunk) & (yy > fork_y), tr[-1])
    flat(cv, right_rim(trunk), tr[0])
    # drapes back to front: (centre offset, top offset, half width, curtain length, level)
    drapes = [(0.45, 0.10, 0.55, 0.55, -1.6), (-0.5, 0.14, 0.5, 0.52, -1.2), (0.0, 0.0, 0.62, 0.5, -0.6),
              (-0.28, 0.2, 0.45, 0.5, 0.2), (0.34, 0.24, 0.42, 0.46, 0.4)]
    cols = np.arange(W)
    for di, (ox, oy, ohw, oln, lvl) in enumerate(drapes):
        dcx = cx + ox * spread
        dhw = ohw * spread * g.uniform(0.9, 1.1)
        dtop = top + oy * height
        d = wdx(cols, dcx)
        t = np.abs(d) / dhw
        inside = t < 1
        ttop = np.round(dtop + (1 - np.sqrt(np.clip(1 - t ** 2, 0, 1))) * dhw * 0.55)
        rnd = rng("wd", seed, di).random(W)
        ln = oln * height * np.sqrt(np.clip(1 - t ** 3, 0, 1)) * (0.7 + 0.45 * rnd)
        ln = np.where(rnd < 0.18, ln * 0.55, ln)
        bot = np.round(ttop + ln)
        m = inside[None, :] & (yy >= ttop[None, :]) & (yy <= bot[None, :]) & (yy < by - 1)
        rel = (cols - cx + W / 2) % W - W / 2
        dd = (yy - ttop[None, :]) / np.maximum(1, ln)[None, :]
        vv = (n - 1) * 0.55 + lvl - (rel / spread)[None, :] * 1.3 - dd * 1.8
        vv = vv - ((cols + di * 2) % 3 == 0)[None, :] * (dd > 0.2) * 1.0
        vv = vv + (dd < 0.07) * 1.2
        paint(cv, m, fr, vv, sharp=3)
        flat(cv, bot_rim(m), fr[max(0, int((n - 1) * 0.3 + lvl))])
        # leafy dome bumps along the drape top
        k = -dhw * 0.85
        while k < dhw * 0.85:
            bx = int(round(dcx + k)) % W
            b = int(round((n - 1) * 0.6 + lvl - ((bx - cx + W / 2) % W - W / 2) / spread * 1.3))
            stamp_crown(cv, crown_sprite(2.5, 0.65), bx, int(ttop[bx]) + 1, fr, b)
            k += g.uniform(3.0, 4.5)
    return


def bush(cv, cx, by, w, ht, pal, seed, r=2.5):
    """Low mound of round leaf clusters."""
    g = rng("bush", seed)
    pts = []
    for i in range(int(w / (r * 1.3)) + 1):
        t = i / max(1, int(w / (r * 1.3))) - 0.5
        py = by - ht * (1 - (2 * t) ** 2) ** 0.5 + r * 0.6
        pts.append((cx + t * w, py))
    for rowk in range(2):
        for (px, py) in pts:
            y = py + rowk * r * 1.2
            if y > by:
                continue
            rel = (px - cx) / (w / 2)
            b = int(round((len(pal) - 1) * 0.5 - rel * 0.8 - rowk * 0.8 + g.uniform(-0.4, 0.4)))
            stamp_crown(cv, crown_sprite(r, 0.8), int(round(px + g.uniform(-1, 1))), int(round(y)), pal, b)


def reeds(cv, x0, x1, by, seed, pal, heads=None, count=None, hmin=12, hmax=34):
    """Reed blades rising from `by` between x0..x1 (wrapping). pal dark->light."""
    h = cv.h
    g = rng("reeds", seed)
    count = count or int((x1 - x0) / 1.6)
    for i in range(count):
        bx = g.uniform(x0, x1)
        ht = g.uniform(hmin, hmax)
        lean = g.uniform(-4, 4)
        pts = [(bx, by), (bx + lean * 0.3, by - ht * 0.55), (bx + lean, by - ht)]
        c = pal[int(g.integers(1, len(pal)))]
        m = wline(h, [(round(px), round(py)) for px, py in pts])
        flat(cv, m, c)
        if heads is not None and g.random() < 0.12:
            hx, hy = round(bx + lean * 0.8), round(by - ht * 0.8)
            flat(cv, wrect(h, hx, hy, hx + 1, hy + 3), heads[0])
            put(cv, hx % W, hy, heads[1])
    return


def ground_bank(cv, y, seed, ramp, amp=2.5, tufts=None):
    h = cv.h
    yy, xx, _ = grids(h)
    prof = np.round(y + (pn1(("gb", seed), 40, 2) - 0.5) * 2 * amp)
    m = yy >= prof[None, :]
    depth = yy - prof[None, :]
    v = (len(ramp) - 1) - np.clip(depth / 3.0, 0, len(ramp) - 1)
    paint(cv, m, ramp, v, sharp=1.8)
    if tufts is not None:
        g = rng("tufts", seed)
        for i in range(int(W / 5)):
            tx = g.uniform(0, W)
            ty = prof[int(tx) % W]
            for k in range(3):
                lx = tx + (k - 1) * 1.2
                ht = g.uniform(2, 5)
                flat(cv, wline(h, [(round(lx), ty), (round(lx + (k - 1) * 1.5), round(ty - ht))]), tufts[k % len(tufts)])
    return m, prof


# =============================================================== more primitives
def overcast(cv, y_base, seed, pal, lobe=12.0, depth=6.0, top_dark=40):
    """Overcast cloud deck hanging from the top: scalloped lobes with light rims.

    pal = (dark, body, rim)."""
    h = cv.h
    yy, xx, B = grids(h)
    g = rng("overcast", seed)
    edge = np.full(W, float(y_base))
    x = 0.0
    while x < W:
        r = lobe * g.uniform(0.6, 1.4)
        d = depth * g.uniform(0.5, 1.2)
        t = np.abs(wdx(np.arange(W), x + r)) / r
        edge = np.maximum(edge, np.where(t < 1, y_base + d * np.sqrt(np.clip(1 - t ** 2, 0, 1)), -1))
        x += r * g.uniform(1.1, 1.7)
    edge = np.round(edge)
    m = yy <= edge[None, :]
    v = 1.0 + np.clip((edge[None, :] - yy) / max(1, top_dark), 0, 1) * -1.2
    paint(cv, m, pal[:2], v + 0.3, sharp=4)
    flat(cv, bot_rim(m), pal[2])
    flat(cv, sh(bot_rim(m), 0, -1) & m & (pn2(h, ("oc", seed), 8, 2, 1) > 0.55), pal[2])
    return m


def reed_bed(cv, prof, pal, seed, tips=0.55, tip_h=5, heads=None):
    """Flat marsh reed mass below `prof`: vertical stroke texture, sunlit tips, seed heads."""
    h = cv.h
    yy, xx, B = grids(h)
    g = rng("reedbed", seed)
    n = len(pal)
    m = yy >= prof[None, :]
    st = pn2(h, ("rb", seed), 1.5, 10, 1)
    depth = yy - prof[None, :]
    v = (n - 1) * 0.5 + (st > 0.62) * 1.0 - (st < 0.3) * 1.0 + (depth < 2) * 1.0 - np.clip(depth / 30.0, 0, 1) * 1.2
    paint(cv, m, pal, v, sharp=3)
    for x in range(W):
        if g.random() < tips:
            ln = int(g.integers(1, tip_h + 1))
            y0 = int(prof[x])
            c = pal[min(n - 1, int((n - 1) * 0.5) + int(g.integers(0, 2)))]
            for k in range(1, ln + 1):
                if 0 <= y0 - k < h:
                    put(cv, x, y0 - k, c)
            if heads is not None and g.random() < 0.08 and y0 - ln - 2 >= 0:
                put(cv, x, y0 - ln - 1, heads[0])
                put(cv, x, y0 - ln - 2, heads[1])
    return m


def stilt_house(cv, x, water_y, w, pal, roof, lit=None, seed=0):
    """Silhouetted stilt hut over water. pal = (dark, mid, light), roof = (dark, mid, light)."""
    h = cv.h
    yy, xx, _ = grids(h)
    floor_y = water_y - int(6 + w * 0.14)
    bh = int(w * 0.32)
    rh = int(w * 0.36)
    x0 = int(x - w / 2)
    x1 = int(x + w / 2)
    for sx in range(x0 + 1, x1 + 1, max(4, w // 5)):
        flat(cv, wrect(h, sx, floor_y, sx, water_y + 1), pal[0])
    flat(cv, wline(h, [(x0 + 1, floor_y + 2), (x1 - 1, water_y - 1)]), pal[0])
    flat(cv, wline(h, [(x1 - 1, floor_y + 2), (x0 + 1, water_y - 1)]), pal[0])
    deck = wrect(h, x0 - 3, floor_y - 1, x1 + 3, floor_y)
    flat(cv, deck, pal[1])
    flat(cv, top_rim(deck), pal[2])
    body = wrect(h, x0 + 2, floor_y - bh, x1 - 2, floor_y - 2)
    flat(cv, body, pal[1])
    flat(cv, left_rim(body), pal[2])
    flat(cv, body & ((xx - x0) % 4 == 0), pal[0])
    flat(cv, wrect(h, x0 + 2, floor_y - bh, x1 - 2, floor_y - bh + 1), pal[0])
    win = wrect(h, int(x) - 2, floor_y - bh + 3, int(x) + 1, floor_y - 4)
    flat(cv, win, lit if lit is not None else pal[0])
    rb = floor_y - bh + 1
    rt = rb - rh
    rm = wpoly(h, [(x0 - 5, rb), (x0 + w * 0.12, rt + 2), (x - 1, rt), (x + 1, rt), (x1 - w * 0.12, rt + 2), (x1 + 5, rb),
                   (x1 + 4, rb + 1), (x0 - 4, rb + 1)])
    flat(cv, rm, roof[1])
    flat(cv, top_rim(rm) | (left_rim(rm) & (wdx(xx, x) < 0)), roof[2])
    flat(cv, bot_rim(rm), roof[0])
    st = pn2(h, ("thatch", seed), 1.5, 6, 1)
    flat(cv, rm & (st > 0.66) & ~top_rim(rm) & ~bot_rim(rm), roof[0])
    return floor_y


def dead_tree(cv, x, by, height, pal, seed, lean=0.0, spread=1.0, width=3):
    """Bare branching snag: recursive tapering limbs, light on the left edge. pal dark->light (>= 3)."""
    h = cv.h
    g = rng("dead", seed)
    limbs = np.zeros((h, W), bool)
    lit = np.zeros((h, W), bool)

    def limb(x0, y0, ang, ln, wdt, depth):
        x1 = x0 + math.cos(ang) * ln
        y1 = y0 + math.sin(ang) * ln
        mx = (x0 + x1) / 2 + g.uniform(-2, 2)
        my = (y0 + y1) / 2 + g.uniform(-1, 1)
        pts = [(x0, y0), (mx, my), (x1, y1)]
        mm = wline(h, pts, max(1, int(round(wdt))))
        nonlocal limbs, lit
        limbs |= mm
        lit |= left_rim(mm)
        if depth > 0 and ln > 4:
            nb = 2 if g.random() < 0.7 else 3
            for k in range(nb):
                na = ang + g.uniform(-0.7, 0.7) * spread + (k - (nb - 1) / 2) * 0.55 * spread
                na = min(-0.25, max(-math.pi + 0.25, na))
                limb(x1, y1, na, ln * g.uniform(0.55, 0.75), wdt * 0.62, depth - 1)

    trunk_top = (x + lean * height * 0.3, by - height * 0.45)
    tm = wpoly(h, [(x - width, by), (x + width, by), (trunk_top[0] + width * 0.5, trunk_top[1]),
                   (trunk_top[0] - width * 0.5, trunk_top[1])])
    limbs |= tm
    lit |= left_rim(tm)
    for k in range(3):
        limb(trunk_top[0], trunk_top[1], -math.pi / 2 + (k - 1) * 0.6 * spread + g.uniform(-0.2, 0.2),
             height * g.uniform(0.28, 0.4), width * 0.9, 3)
    flat(cv, limbs, pal[1])
    flat(cv, lit & limbs, pal[2])
    flat(cv, right_rim(limbs) & ~lit, pal[0])
    return limbs


def pool(cv, cx, cy, rx, ry, pal, seed):
    """Still pool among reeds: dark reflected-bank band on top, pale sky streaks. pal (dark, mid, light)."""
    h = cv.h
    yy, xx, _ = grids(h)
    d = wdx(xx, cx)
    edge = rx * (0.75 + 0.25 * pn1(("pool", seed), 16, 2))
    m = (np.abs(d) <= edge[None, :] * np.sqrt(np.clip(1 - ((yy - cy) / (ry + 0.5)) ** 2, 0, 1))) & (np.abs(yy - cy) <= ry)
    flat(cv, m, pal[1])
    flat(cv, m & ~sh(m, 0, 1), pal[0])
    flat(cv, m & ~sh(m, 0, 2) & (pn2(h, ("pt", seed), 3, 2, 1) > 0.45), pal[0])
    ln = m & sh(m, 0, 2) & (pn2(h, ("pl", seed), 9, 1.5, 1) > 0.52)
    flat(cv, ln, pal[2])
    return m


def bamboo(cv, x, top, by, wdt, pal, seed, lean=0.0, node_gap=14, leaves=None, leaf_n=4):
    """One bamboo culm: cylindrical shading, node rings, optional leaf sprays. pal dark->light (>= 5)."""
    h = cv.h
    yy, xx, B = grids(h)
    g = rng("bamboo", seed)
    n = len(pal)
    xs_top = x + lean
    t = np.clip((yy - top) / max(1, by - top), 0, 1)
    cxr = xs_top + (x - xs_top) * t
    d = (xx - cxr + W / 2) % W - W / 2
    m = (np.abs(d + 0.5) <= wdt / 2) & (yy >= top) & (yy <= by)
    u = (d + wdt / 2) / max(1, wdt)
    v = (n - 1) * (0.85 - u * 0.75)
    paint(cv, m, pal, v, sharp=4)
    off = int(g.integers(0, node_gap))
    ring = m & (((yy - top + off) % node_gap) == 0)
    flat(cv, ring, pal[0])
    flat(cv, sh(ring, 0, -1) & m & (u < 0.6), pal[min(n - 1, n - 1)])
    if leaves is not None:
        for k in range(leaf_n):
            ly = top + (by - top) * g.uniform(0.02, 0.55)
            lx = xs_top + (x - xs_top) * ((ly - top) / max(1, by - top))
            side = -1 if g.random() < 0.5 else 1
            leaf_spray(cv, lx + side * wdt * 0.5, ly, side, leaves, (seed, k), size=g.uniform(0.8, 1.3) * max(5, wdt * 2.2))
    return m


def leaf_spray(cv, x, y, side, pal, seed, size=8.0):
    """Drooping fan of slender bamboo leaves from a twig. pal dark->light (>= 4)."""
    h = cv.h
    g = rng("spray", seed)
    tw_end = (x + side * size * 0.5, y - size * 0.15)
    flat(cv, wline(h, [(x, y), tw_end]), pal[1])
    for k in range(int(g.integers(3, 6))):
        ang = (0.15 + k * 0.3 + g.uniform(-0.1, 0.1))
        ln = size * g.uniform(0.6, 1.0)
        bx, by_ = tw_end[0] - side * k * 1.2, tw_end[1] + k * 0.5
        ex = bx + side * math.cos(ang) * ln
        ey = by_ + math.sin(ang) * ln * 0.8
        mx = (bx + ex) / 2
        my = (by_ + ey) / 2 - 0.5
        lm = wpoly(h, [(bx, by_), (mx, my - 1), (ex, ey), (mx, my + 1)])
        c = pal[2 + (k % 2)] if k < 3 else pal[1]
        flat(cv, lm, c)
        flat(cv, top_rim(lm), pal[min(len(pal) - 1, 3 + (k % 2))])


def pine(cv, x, by, height, pal, tr, seed, lean=0.3, pads=6, pad_w=10.0):
    """Chinese pine: leaning trunk, horizontal branches ending in flat needle pads (lit tops)."""
    h = cv.h
    yy, xx, B = grids(h)
    g = rng("pine", seed)
    n = len(pal)
    pts = [(x, by), (x + lean * height * 0.25 + g.uniform(-2, 2), by - height * 0.45),
           (x + lean * height * 0.45, by - height * 0.8), (x + lean * height * 0.4 + g.uniform(-3, 3), by - height)]
    trunk = np.zeros((h, W), bool)
    for i in range(len(pts) - 1):
        wdt = max(1, int(round(4 - i * 1.1)))
        trunk |= wline(h, [pts[i], pts[i + 1]], wdt + 1)
    trunk |= wpoly(h, [(x - 4, by), (x + 4, by), (x + 1, by - 5), (x - 1, by - 5)])
    ends = []
    for k in range(pads):
        t = 0.35 + 0.6 * k / max(1, pads - 1)
        i = min(len(pts) - 2, int(t * (len(pts) - 1)))
        f = t * (len(pts) - 1) - i
        px = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f
        py = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f
        side = -1 if k % 2 == 0 else 1
        ln = height * g.uniform(0.18, 0.34) * (1.1 - t * 0.5)
        ex, ey = px + side * ln, py - ln * g.uniform(0.05, 0.3)
        trunk |= wline(h, [(px, py), ((px + ex) / 2, py - 1), (ex, ey)], 2 if t < 0.7 else 1)
        ends.append((ex, ey, pad_w * (1.15 - t * 0.4) * g.uniform(0.8, 1.15)))
        ends.append(((px + ex) / 2, py - 2, pad_w * 0.6 * g.uniform(0.8, 1.2)))
    ends.append((pts[-1][0], pts[-1][1], pad_w * 0.8))
    u = row_u(trunk, wdx(np.arange(W), x))
    paint(cv, trunk, tr, (len(tr) - 1) * (0.9 - u * 0.8), sharp=3)
    flat(cv, left_rim(trunk) & (yy > by - height * 0.6), tr[-1])
    for (ex, ey, pw) in sorted(ends, key=lambda e: e[1]):
        pm = np.zeros((h, W), bool)
        for j in range(3):
            pm |= wellipse(h, ex + (j - 1) * pw * 0.45 + g.uniform(-1, 1), ey - (1 if j == 1 else 0), pw * 0.45,
                           pw * 0.22 + 0.8)
        pm &= yy <= ey + pw * 0.15
        rel = (ex - x) / max(1.0, height * 0.4)
        needles = pn2(h, ("needle", seed), 1.5, 3, 1)
        dtop = depth_in(pm)
        v = (n - 1) * 0.5 - rel * 0.6 + (dtop < 1.5) * 1.3 - (needles > 0.6) * 0.7
        paint(cv, pm, pal, v, sharp=3)
        flat(cv, bot_rim(pm), pal[0])
        flat(cv, top_rim(pm) & (wdx(xx, ex) < pw * 0.1), pal[-1])
    return trunk


def depth_in(m):
    """Rows from the top edge of each vertical run of m (0 at the top)."""
    d = np.zeros(m.shape, float)
    for y in range(1, m.shape[0]):
        d[y] = np.where(m[y] & m[y - 1], d[y - 1] + 1, 0)
    return d


def rock_blob(cv, cx, by, rx, ry, ramp, seed, facets=4, rough=0.18, moss=None):
    """Chunky faceted boulder sitting on `by` (wrap aware)."""
    h = cv.h
    yy, xx, B = grids(h)
    g = rng("rockb", seed)
    d = wdx(xx, cx)
    cy = by - ry + 1
    th = np.arctan2((yy - cy) / ry, d / rx)
    r = np.ones_like(th)
    for k in range(2, 6):
        r += rough / (k - 1) * g.uniform(-1, 1) * np.cos(k * th + g.uniform(0, 6.283))
    m = ((d / rx) ** 2 + ((yy - cy) / ry) ** 2 <= r * r) & (yy <= by)
    if not m.any():
        return m
    # facet planes: split by random lines through the blob, each region gets a tilt
    rid = np.zeros((h, W), int)
    for i in range(facets):
        px = g.uniform(-rx * 0.5, rx * 0.5)
        py = cy + g.uniform(-ry * 0.5, ry * 0.4)
        ang = g.uniform(0, math.pi)
        rid = rid * 2 + (((d - px) * math.sin(ang) - (yy - py) * math.cos(ang)) > 0)
    n = len(ramp)
    v = np.zeros((h, W))
    for rv in np.unique(rid[m]):
        reg = m & (rid == rv)
        ys, xs = np.nonzero(reg)
        dxm = wdx(xs, cx).mean() / rx
        dym = (ys.mean() - cy) / ry
        v[reg] = (n - 1) * 0.55 - dxm * 1.6 - dym * 1.3 + g.uniform(-0.4, 0.4)
    depth = depth_in(m)
    v = v + (depth < 1) * 1.2
    paint(cv, m, ramp, v, sharp=4)
    flat(cv, bot_rim(m), ramp[0])
    flat(cv, right_rim(m) & ~top_rim(m), ramp[0])
    flat(cv, left_rim(m) & (depth > 0), ramp[min(n - 1, n - 2)])
    if moss is not None:
        mm = m & (depth < 2 + (pn2(h, ("rbm", seed), 4, 4, 1) > 0.5) * 2) & (pn2(h, ("rbm2", seed), 6, 6, 1) > 0.4)
        flat(cv, mm, moss[0])
        flat(cv, mm & top_rim(m), moss[1])
    return m


# =============================================================== scene: Jade River valley
def karst_ranks(far, P, key, ranks):
    """Draw ranks of karst towers back to front. ranks: list of dicts(peaks, ramp, trees, fade(y0,y1), haze)."""
    for ri, rk in enumerate(ranks):
        for i, spec in enumerate(rk["peaks"]):
            cx, top, hw = spec[:3]
            karst_peak(far, cx, top, hw, rk["ramp"], (key, ri, i), trees=rk.get("trees"), gain=rk.get("gain", 1.25),
                       crevice=rk.get("crevice", 1.0), rim=rk.get("rim", True), dark_edge=rk.get("dark", True),
                       ledges=rk.get("ledges", 0.5), shoulder=rk.get("shoulder", 0.6))
        if rk.get("fade"):
            y0, y1 = rk["fade"]
            base_fade(far, y0, y1, rk["haze"], steps=rk.get("steps", 4))
        if rk.get("mist"):
            my, mt, ma = rk["mist"]
            mist_band(far, my, mt, (key, "mist", ri), P["mist"], alphas=ma, amp=3)


def valley(mode):
    """valley_day / valley_dusk / valley_night share geography; mode picks palettes + extras."""
    P = VALLEY_PAL[mode]
    layers = []
    # ---------------- sky (layer 0)
    sky = sky_layer(P["sky"])
    cp = P["cloud"]
    if mode == "night":
        stars(sky, "vn", 520, 0, 230, R("#2f5a68", "#6f9aa6", "#bcd8dc", "#ffffff"))
        disc(sky, 470, 70, 12, R("#c9cfb8", "#eeeedb", "#fffdf0"), halo=C("#5f94a0"),
             halo_steps=((3.2, 0.07), (2.2, 0.11), (1.5, 0.18)))
        for i, (cx, y, ln) in enumerate(((140, 128, 150), (420, 98, 90), (560, 150, 170), (300, 176, 130),
                                         (40, 196, 120))):
            streak(sky, cx, y, ln, cp, ("vns", i), rows=2)
    else:
        if mode == "day":
            disc(sky, 470, 150, 10, R("#f7e7b4", "#fff3cc", "#fffbea"), halo=C("#fff2c4"),
                 halo_steps=((3.8, 0.10), (2.6, 0.13), (1.7, 0.2)))
        else:
            disc(sky, 430, 200, 16, R("#ffb26a", "#ffcf86", "#ffe8b0"), halo=C("#ffc27a"),
                 halo_steps=((4.2, 0.09), (2.9, 0.13), (1.9, 0.19)))
        for i, (cx, cy, ln, th) in enumerate(((80, 64, 96, 8), (268, 40, 64, 6), (560, 58, 84, 7), (380, 96, 70, 6))):
            cloud(sky, cx, cy, ln, th, ("vc", i), cp)
        for i, (cx, y, ln) in enumerate(((330, 176, 190), (40, 196, 150), (520, 214, 170), (210, 228, 130),
                                         (150, 132, 110), (600, 146, 90))):
            streak(sky, cx, y, ln, cp, ("vs", i), rows=2)
    layers.append((sky, 0.0, 720))

    # ---------------- far (layer 1): ranks of ink karst towers dissolving into river mist
    fh = 170
    far = Canvas(W, fh)
    yy, _, _ = grids(fh)
    ridge = hill_profile(60, 12, "vridge", cell=80, octaves=3)
    hill_row(far, ridge, P["ridge"], "vridge", gain=0.8, rim=True, sharp=4)
    karst_ranks(far, P, "vk", [
        dict(peaks=gen_peaks("vk0", 9, 0, 36, 22, 38), ramp=P["far_back"], trees=P["far_back_tr"], gain=1.0,
             crevice=0.6, ledges=0.3, fade=(50, 112), haze=P["haze_far"], steps=3, mist=(98, 14, (0.18, 0.3, 0.45))),
        dict(peaks=gen_peaks("vk1", 8, 30, 62, 18, 32), ramp=P["far_mid"], trees=P["far_mid_tr"], gain=1.15,
             crevice=0.8, ledges=0.4, fade=(80, 132), haze=P["haze_far"], steps=3, mist=(118, 12, (0.18, 0.32, 0.48))),
        dict(peaks=gen_peaks("vk2", 6, 66, 96, 20, 34), ramp=P["far_front"], trees=P["far_trees"], gain=1.3,
             ledges=0.5, fade=(110, 150), haze=P["haze_far"], steps=4, mist=(138, 12, (0.22, 0.4, 0.58))),
    ])
    flat(far, yy >= 150, P["haze_far"])
    layers.append((far, 0.08, 560))

    # ---------------- mid (layer 2): forested hills, pagodas, the winding Jade River
    mh = 180
    mid = Canvas(W, mh)
    yy, _, _ = grids(mh)
    cols = np.arange(W)
    hb1 = hill_profile(82, 16, "vhb1", cell=213.34, octaves=3)
    treeline(mid, hb1, P["hill_back"], "vhb1", r=2.0, gain=1.2, rows=2, row_density=0.4)
    for i, px in enumerate((150, 452)):
        pagoda(mid, px, int(hb1[px]) + 1, 5 if i == 0 else 4, 7, P["pagoda"], windows=P.get("window"))
    hb2 = np.maximum(hill_profile(100, 9, "vhb2", cell=128, octaves=2), hb1 + 8)
    treeline(mid, hb2, P["hill_back2"], "vhb2", r=2.0, gain=1.2)
    yy_m = grids(mh)[0]
    haze_fade(mid, mid.a > 0, P["haze_mid"], np.clip((yy_m - 100) / 20.0, 0, 1) * 0.5, steps=2, sharp=5)
    mist_band(mid, 104, 8, "vmm1", P["mist"], alphas=(0.16, 0.28, 0.42), amp=3, gaps=0.5)
    wind = np.sin(cols / W * 2 * math.pi + 0.6) * 0.6 + np.sin(cols / W * 4 * math.pi + 2.1) * 0.4
    r_top = np.round(114 + wind * 3 + (pn1("vrt", 32, 2) - 0.5) * 2)
    r_bot = r_top + 12 + np.round((wind + 1) * 5)
    water = river(mid, r_top, r_bot, P["river"], "vriver", bank=P["bank"], glint=P["glint"],
                  reflect=P["reflect"], reflect_rows=2)
    shore = np.round(r_bot + 1)
    hill_row(mid, shore, P["meadow"], "vshore", gain=0.5, top_rows=1, rim=True)
    # two big wooded hills per tile hide the river so it winds in and out of view
    fr_prof = hill_profile(150, 6, "vfh", cell=80, octaves=2)
    for (hx, hy, hw) in ((40, 104, 70), (330, 112, 58)):
        tt = np.abs(wdx(cols, hx)) / hw
        fr_prof = np.minimum(fr_prof, np.where(tt < 1, hy + (150 - hy) * tt ** 1.8, np.inf))
    fr_prof = np.round(fr_prof)
    treeline(mid, fr_prof, P["hill_front"], "vfh", r=3.0, gain=1.2, conifer=0.06, rows=5)
    fr2 = np.maximum(hill_profile(160, 6, "vfh2", cell=80, octaves=2), fr_prof + 12)
    treeline(mid, fr2, P["hill_front2"], "vfh2", r=3.0, gain=0.9)
    if P.get("lanterns") is not None:
        g = rng("vlan")
        lx_list = []
        for i in range(60):
            lx = int(g.integers(0, W))
            ly = int(r_top[lx]) - 1
            if 0 < ly < mh and mid.a[ly, lx] > 0 and fr_prof[lx] > ly + 3 and all(abs(lx - o) > 7 for o in lx_list):
                put(mid, lx, ly, P["lanterns"][1])
                put(mid, lx, ly - 1, P["lanterns"][0])
                lx_list.append(lx)
            if len(lx_list) >= 12:
                break
        reflections(mid, water, lx_list, r_top, R(P["lanterns"][0], P["lanterns"][1]), "vref",
                    length=9 if mode == "night" else 6)
    if mode == "night":
        reflections(mid, water, [470, 471, 472], r_top, R("#6f9a9c", "#cfe0d8"), "moonref", length=16)
    mist_band(mid, 146, 8, "vmm2", P["mist"], alphas=(0.12, 0.2), amp=3, gaps=0.62)
    layers.append((mid, 0.18, 620))

    # ---------------- near (layer 3): willow tree line and reeds on the bank
    nh = 200
    near = Canvas(W, nh)
    gy = 142
    bush(near, 150, gy + 2, 40, 12, P["willow"], "vbush1", r=3)
    bush(near, 395, gy + 2, 30, 9, P["willow"], "vbush2", r=3)
    for i, (tx, ht, sp, ln) in enumerate(((70, 112, 42, 0.25), (302, 88, 32, -0.3), (500, 118, 46, 0.1))):
        willow(near, tx, gy + 2, ht, sp, P["willow"], P["trunk"], ("vw", i), lean=ln)
    m, prof = ground_bank(near, gy, "vbank", P["ground"], amp=2.0, tufts=P["reeds"][2:])
    for i, (x0, x1) in enumerate(((118, 200), (228, 268), (350, 440), (560, 620))):
        reeds(near, x0, x1, gy + 3, ("vr", i), P["reeds"], heads=P["cattail"], hmin=10, hmax=34)
    layers.append((near, 0.32, 720))
    return dict(sky=P["sky"][0][1], horizon=P["horizon"], layers=layers)


VALLEY_PAL = {
    "day": dict(
        sky=[(0.0, "#7fb0c2"), (0.24, "#9cc2cd"), (0.44, "#bdd5d3"), (0.58, "#dddfbf"), (0.68, "#f1e3b2"),
             (0.8, "#eee6c8"), (1.0, "#dfe6d6")],
        horizon="#f1e3b2",
        cloud=R("#bccfd2", "#e1eae4", "#f6f5e8", "#fffbea"),
        ridge=R("#9fb8c4", "#a9c0ca", "#b3c7cf", "#bfcfd3"),
        far_back=R("#6d8a9e", "#7894a6", "#86a0b0", "#96adba", "#a8bcc6", "#bccbd0"),
        far_back_tr=R("#5f7c86", "#68868c", "#739092", "#809a98", "#8ea69e"),
        far_mid=R("#4f6d84", "#5a788d", "#678498", "#7690a2", "#8aa2b1", "#a4b8c3"),
        far_mid_tr=R("#44636c", "#4d6d72", "#587878", "#66847f", "#779086"),
        far_front=R("#34516a", "#3f5d74", "#4c6a80", "#5c798c", "#71899b", "#8ea3b0"),
        far_trees=R("#28454e", "#305154", "#3b5f5c", "#4a6f64", "#5d826c"),
        haze_far="#d9e2d7", mist="#eef2e8", haze_mid="#c9d9ca",
        hill_back=R("#4e7d70", "#5b8b77", "#69987e", "#7ca685", "#93b791"),
        hill_back2=R("#44736a", "#507f70", "#5e8d76", "#6f9c7d", "#86ae88"),
        pagoda=R("#35504e", "#4d6862", "#83998f"),
        river=R("#2a6b68", "#35817a", "#46998d", "#5db1a0", "#86cbb6", "#b9e4d2"),
        bank="#35574c", reflect="#3f7466", glint="#e8f6ea",
        meadow=R("#3d6a4e", "#4a7a53", "#5b8c58", "#72a05f", "#94b86c"),
        hill_front=R("#1d4135", "#24503d", "#2e5f45", "#3b704d", "#4e8456", "#6a9a60", "#8db46c"),
        hill_front2=R("#183a31", "#1f4638", "#28553f", "#336447", "#43774f", "#5a8c58", "#78a462"),
        willow=R("#16382f", "#1d4738", "#285941", "#366d4a", "#4a8454", "#679c5e", "#8fba6c"),
        trunk=R("#1b1f1c", "#2a2d27", "#3c3c32", "#55503f", "#6d6550"),
        ground=R("#142620", "#1b3228", "#233f2f", "#2d4d35", "#3a5e3c", "#4c7444"),
        reeds=R("#1a3629", "#284c34", "#386241", "#50804d", "#74a05b"),
        cattail=R("#4a3322", "#7a5634"),
    ),
    "dusk": dict(
        sky=[(0.0, "#2e2d58"), (0.2, "#4a3f72"), (0.38, "#7a5584"), (0.52, "#b86a82"), (0.62, "#e48a78"),
             (0.7, "#f6b070"), (0.76, "#ffd08a"), (0.86, "#f2b98e"), (1.0, "#c9909a")],
        horizon="#ffd08a",
        cloud=R("#7a5480", "#c07a8a", "#f4a67e", "#ffd49a"),
        ridge=R("#a07898", "#ad82a0", "#bb8ea6", "#c89aa8"),
        far_back=R("#4f3f6a", "#584672", "#634f7a", "#705984", "#80648c", "#b07c90"),
        far_back_tr=R("#3e335a", "#463a62", "#4f416a", "#584872", "#63507a"),
        far_mid=R("#372d52", "#3f345a", "#4a3d64", "#57476e", "#685278", "#a87488"),
        far_mid_tr=R("#2c2446", "#332a4e", "#3b3056", "#44375e", "#4e3f66"),
        far_front=R("#2b2446", "#362d52", "#43385e", "#524469", "#665174", "#b27a86"),
        far_trees=R("#1f1a34", "#28213e", "#312948", "#3c3252", "#4a3c5c"),
        haze_far="#e8a88c", mist="#f7c49c", haze_mid="#c98c8c",
        hill_back=R("#372f50", "#433a5a", "#524664", "#62526e", "#7a6278"),
        hill_back2=R("#2e2946", "#383150", "#443b5a", "#534664", "#68566e"),
        pagoda=R("#1f1a30", "#302842", "#6a4f66"),
        window="#ffcf6a",
        river=R("#3a3158", "#5a4570", "#8a5a7c", "#c07482", "#ec9a78", "#ffd08a"),
        bank="#2a2440", reflect="#3e3456", glint="#ffe6b0",
        meadow=R("#262a3c", "#2f3346", "#3a3c50", "#4a4658", "#5e5260"),
        hill_front=R("#171a2a", "#1e2234", "#272a3e", "#323448", "#413f52", "#554a5c", "#70586a"),
        hill_front2=R("#131624", "#191c2e", "#212538", "#2b2f42", "#383a4c", "#4a4556", "#624e62"),
        willow=R("#101221", "#161a2a", "#1e2334", "#282e3e", "#363a4a", "#4a4656", "#6e5460"),
        trunk=R("#0d0e18", "#161621", "#201f2b", "#2e2a36", "#433642"),
        ground=R("#0d0e18", "#131422", "#1a1b2a", "#232333", "#2e2b3a", "#3c3444"),
        reeds=R("#121424", "#1a1e30", "#242839", "#333444", "#4b4250"),
        cattail=R("#241a24", "#4a3036"),
        lanterns=R("#ff9a4a", "#ffe08a"),
    ),
    "night": dict(
        sky=[(0.0, "#040b14"), (0.3, "#081a24"), (0.55, "#0b2530"), (0.72, "#123440"), (0.82, "#184250"),
             (1.0, "#123844")],
        horizon="#184250",
        cloud=R("#0a2230", "#12303e", "#2d5a66", "#5a8890"),
        ridge=R("#143440", "#173a46", "#1a404c", "#1e4652"),
        far_back=R("#0f2a36", "#12303c", "#163642", "#1a3c48", "#20444f", "#2a5058"),
        far_back_tr=R("#0c2430", "#0f2a34", "#123038", "#16363c", "#1a3c40"),
        far_mid=R("#0b222c", "#0e2832", "#122f38", "#16363f", "#1d4048", "#2c545c"),
        far_mid_tr=R("#081c24", "#0b2229", "#0e282e", "#123034", "#16373a"),
        far_front=R("#071820", "#0a1f28", "#0e2730", "#133039", "#1a3b43", "#2d5a60"),
        far_trees=R("#05131a", "#08191f", "#0c2025", "#10282b", "#153031"),
        haze_far="#19404c", mist="#3f7480", haze_mid="#143640",
        hill_back=R("#0a2126", "#0e292c", "#123032", "#173838", "#1f4440"),
        hill_back2=R("#081c21", "#0c2427", "#102c2e", "#153434", "#1c3e3c"),
        pagoda=R("#04101a", "#0a1c22", "#23444a"),
        window="#ffcf6a",
        river=R("#06181f", "#0a2029", "#0e2a34", "#14363f", "#1f4a52", "#3c7478"),
        bank="#071a1e", reflect="#0a2226", glint="#6fa6a8",
        meadow=R("#06161a", "#091d20", "#0d2426", "#112c2c", "#173432"),
        hill_front=R("#040f12", "#061519", "#091c1f", "#0d2426", "#122d2e", "#193836", "#24463f"),
        hill_front2=R("#030c0f", "#051216", "#08181b", "#0b1f22", "#10272a", "#153030", "#1e3c38"),
        willow=R("#030c0f", "#051216", "#08191c", "#0c2123", "#112a2a", "#173434", "#244644"),
        trunk=R("#02080a", "#050f12", "#091719", "#0e1f20", "#16292a"),
        ground=R("#02090b", "#040e11", "#071416", "#0a1b1c", "#0f2323", "#152c2a"),
        reeds=R("#030b0e", "#061316", "#0a1b1d", "#0f2525", "#173131"),
        cattail=R("#0a0e10", "#1a2020"),
        lanterns=R("#e5b84c", "#ffe6a1"),
    ),
}


# =============================================================== scene: grey marsh
def marsh():
    layers = []
    sky = sky_layer([(0.0, "#6d7d7a"), (0.25, "#86958f"), (0.5, "#a2afa6"), (0.66, "#bcc6b8"), (0.76, "#c9d0c0"),
                     (1.0, "#b7c1b3")])
    overcast(sky, 84, "mo2", R("#8a9892", "#97a49d", "#aab6ac"), lobe=26, depth=16, top_dark=60)
    overcast(sky, 30, "mo1", R("#5f6f6d", "#71807c", "#8a978f"), lobe=20, depth=14, top_dark=40)
    for i, (cx, y, ln) in enumerate(((100, 150, 200), (380, 166, 170), (560, 138, 120), (250, 190, 150),
                                     (480, 206, 190))):
        streak(sky, cx, y, ln, R("#9ba79f", "#b2bcb1", "#cad1c4"), ("ms", i), rows=2)
    layers.append((sky, 0.0, 720))

    far = Canvas(W, 170)
    yy, _, _ = grids(170)
    hill_row(far, hill_profile(98, 9, "mfh", cell=213.34, octaves=3), R("#8e9c95", "#97a49c", "#a1ada4", "#acb7ad"),
             "mfh", gain=0.8, sharp=4)
    tl = hill_profile(114, 4, "mft", cell=64, octaves=2)
    treeline(far, tl, R("#7a8a83", "#84938b", "#8e9c93", "#98a59b", "#a5b0a5"), "mft", r=1.5, gain=0.8)
    for i, (tx, ht) in enumerate(((60, 26), (236, 20), (410, 30), (560, 18))):
        dead_tree(far, tx, int(tl[tx]) + 2, ht, R("#6f7d78", "#7f8c86", "#95a09a"), ("mfd", i), width=1.2)
    base_fade(far, 112, 150, "#bcc5b9", steps=4)
    flat(far, yy >= 150, "#bcc5b9")
    mist_band(far, 128, 14, "mfm", "#d3d9cc", alphas=(0.22, 0.4, 0.58), amp=3)
    layers.append((far, 0.08, 560))

    mid = Canvas(W, 180)
    yy, _, _ = grids(180)
    cols = np.arange(W)
    reed_bed(mid, hill_profile(86, 3, "mrb0", cell=40, octaves=2), R("#6c7e74", "#76887d", "#829286", "#8f9e90",
                                                                      "#9fac9c"), "mrb0", tips=0.4, tip_h=3)
    base_fade(mid, 84, 100, "#b3bdb0", steps=3)
    r_top = np.round(97 + (pn1("mrt", 64, 2) - 0.5) * 4)
    r_bot = np.round(r_top + 15 + (pn1("mrbt", 80, 2) - 0.5) * 6)
    water = river(mid, r_top, r_bot, R("#42605a", "#4e7068", "#5d8077", "#709388", "#8aa89b", "#b3c7ba"), "mriver",
                  bank="#4b5e55", glint="#dfe6da", reflect="#627a70", reflect_rows=2)
    for i, (hx, hw) in enumerate(((118, 26), (438, 32))):
        wy = int(r_top[hx]) + 9
        stilt_house(mid, hx, wy, hw, R("#28332f", "#3a4742", "#56645d"), R("#34352b", "#4d4c3c", "#6c6951"),
                    lit="#b9a36a" if i == 0 else None, seed=("msh", i))
        for sx in range(int(hx - hw / 2) + 1, int(hx + hw / 2), 5):
            for k in range(2, 7, 2):
                put(mid, sx, wy + k, "#324440")
    bed = np.round(r_bot + 2 + (pn1("mnb", 32, 3) - 0.5) * 10)
    reed_bed(mid, bed, R("#304a3e", "#3b5747", "#48654f", "#567358", "#678363", "#7c966f"), "mrb1", tips=0.6,
             tip_h=6, heads=R("#4b4031", "#6d5c45"))
    for i, (px, py, rx, ry) in enumerate(((80, 140, 34, 2), (262, 150, 46, 3), (470, 136, 30, 2), (590, 156, 24, 2))):
        pool(mid, px, py, rx, ry, R("#34463f", "#8fa299", "#c3cfc4"), ("mp", i))
    bed2 = np.round(166 + (pn1("mnb2", 40, 2) - 0.5) * 8)
    reed_bed(mid, bed2, R("#26392f", "#2f4538", "#3a5341", "#46614a", "#557053"), "mrb2", tips=0.6, tip_h=7)
    hn = pn2(180, "mhollow", 80, 6, 2)
    hollow = (mid.a > 0) & (yy > r_bot[None, :] + 3)
    haze_fade(mid, hollow, "#8f9b9e", np.clip((hn - 0.5) * 3.0, 0, 0.5), steps=2, sharp=2.5)
    mist_band(mid, 118, 8, "mmm", "#d8ded2", alphas=(0.16, 0.28, 0.4), amp=3, gaps=0.3)
    layers.append((mid, 0.18, 620))

    near = Canvas(W, 200)
    yy, _, _ = grids(200)
    dead_tree(near, 206, 152, 118, R("#4b5559", "#8f9ba0", "#c9d1d2"), "mnd", lean=0.25, spread=1.1, width=4)
    dead_tree(near, 540, 152, 70, R("#3e4a4b", "#6f7c80", "#a9b4b6"), "mnd2", lean=-0.3, spread=0.9, width=3)
    for i, px in enumerate((372, 384, 60)):
        post_m = wrect(200, px, 124 + i * 4, px + 2, 156)
        flat(near, post_m, "#3a3f38")
        flat(near, left_rim(post_m), "#5f645a")
        flat(near, wrect(200, px, 124 + i * 4, px + 2, 124 + i * 4), "#6a6e62")
    flat(near, wline(200, [(373, 132), (378, 136), (385, 136)]), "#7d7458")
    m, prof = ground_bank(near, 150, "mbank", R("#1c2622", "#232e29", "#2b3730", "#344138", "#3f4c41", "#4c5a4c"),
                          amp=2.5, tufts=R("#40584a", "#50694f", "#62795a"))
    for i, (px, py, rx) in enumerate(((120, 172, 40), (300, 184, 60), (470, 168, 36))):
        pool(near, px, py, rx, 3, R("#1d2a27", "#6c7c76", "#aab7af"), ("mnp", i))
    for i, (x0, x1) in enumerate(((0, 70), (96, 170), (238, 330), (420, 520), (575, 640))):
        reeds(near, x0, x1, 153, ("mr", i), R("#1f3027", "#2b3f33", "#37503e", "#476249", "#5b7555", "#72896a"),
              heads=R("#4a3a2c", "#6b5640"), hmin=16, hmax=66)
    layers.append((near, 0.32, 720))
    return dict(sky="#6d7d7a", horizon="#c9d0c0", layers=layers)


# =============================================================== scene: bamboo grove
def bamboo_grove():
    layers = []
    sky = sky_layer([(0.0, "#94b89a"), (0.3, "#b3cfac"), (0.55, "#d3e2bf"), (0.72, "#ebedcc"), (1.0, "#dde7cb")])
    disc(sky, 96, 40, 14, R("#f4f2d0", "#fbf8df", "#fffdf0"), halo=C("#f6f3cf"),
         halo_steps=((6.0, 0.08), (4.2, 0.1), (2.8, 0.14), (1.8, 0.2)))
    layers.append((sky, 0.0, 720))

    # far: pale stalks dissolving into mist (top above the screen)
    fh = 300
    far = Canvas(W, fh)
    yy, _, _ = grids(fh)
    g = rng("bfar")
    pal_far = R("#90b08d", "#9dbb98", "#a9c4a2", "#b6ceae", "#c4d8bb")
    for i in range(46):
        x = (i + g.uniform(-0.4, 0.4)) * W / 46
        bamboo(far, x, -2, 290, int(g.integers(2, 4)), pal_far, ("bf", i), lean=g.uniform(-6, 6), node_gap=16,
               leaves=R("#88a986", "#94b491", "#a2bf9c", "#b2cbab"), leaf_n=3)
    base_fade(far, 150, 262, "#dce6cb", steps=4)
    flat(far, yy >= 262, "#dce6cb")
    mist_band(far, 210, 30, "bfm", "#eef1dc", alphas=(0.2, 0.36, 0.52), amp=5)
    layers.append((far, 0.08, 560))

    # mid: the grove, a glimpse of the river, light shafts
    mh = 310
    mid = Canvas(W, mh)
    yy, _, _ = grids(mh)
    cols = np.arange(W)
    r_top = np.round(236 + (pn1("brt", 80, 2) - 0.5) * 4)
    r_bot = np.round(r_top + 12 + (pn1("brb", 64, 2) - 0.5) * 4)
    river(mid, r_top, r_bot, R("#3f7f72", "#4c937f", "#5da88e", "#76bc9f", "#9fd4b8", "#d3eed8"), "briver",
          bank="#4a6d52", glint="#f0f8e6", reflect="#6c9c78", reflect_rows=3)
    bank = np.round(r_bot + 1 + (pn1("bbk", 40, 2) - 0.5) * 3)
    hill_row(mid, bank, R("#35533a", "#406343", "#4e744c", "#5f8656", "#779a62"), "bbank", gain=0.5, top_rows=1)
    pal_mid = R("#3f6c43", "#4c7f4d", "#5d9258", "#72a566", "#8db878", "#abcc90")
    lv_mid = R("#3a6641", "#47784a", "#588b54", "#6d9e60", "#87b270")
    g = rng("bmid")
    for i in range(18):
        x = (i + g.uniform(-0.35, 0.35)) * W / 18
        base_y = int(bank[int(x) % W]) + int(g.integers(2, 8))
        bamboo(mid, x, -2, base_y, int(g.integers(4, 6)), pal_mid, ("bm", i), lean=g.uniform(-8, 8), node_gap=20,
               leaves=lv_mid, leaf_n=4)
    for i in range(10):
        fern_x = g.uniform(0, W)
        bush(mid, fern_x, int(bank[int(fern_x) % W]) + 10, g.uniform(14, 26), g.uniform(4, 7), lv_mid, ("bmb", i), r=2)
    light_shafts(mid, [(60, 30), (230, 18), (330, 40), (520, 24)], "#fff4c6", slope=0.45, fade_y=250,
                 alphas=(0.07, 0.1))
    mist_band(mid, 226, 10, "bmm", "#eef2dc", alphas=(0.16, 0.28), amp=3, gaps=0.35)
    layers.append((mid, 0.18, 620))

    # near: thick dark culms framing the view, ferns on the ground
    nh = 360
    near = Canvas(W, nh)
    yy, _, _ = grids(nh)
    m, prof = ground_bank(near, 306, "bnbank", R("#16241a", "#1c2d20", "#233826", "#2c442d", "#375236", "#44623f"),
                          amp=3, tufts=R("#2e4c33", "#3b5f3d", "#4c7447"))
    pal_near = R("#1c3622", "#23432a", "#2c5232", "#37623b", "#467546", "#5c8b53", "#7aa466")
    lv_near = R("#1a3321", "#22412a", "#2d5233", "#3a643d", "#4d7a4a")
    for i, (x, wdt, ln) in enumerate(((22, 9, -4), (40, 7, 3), (196, 10, 5), (330, 8, -3), (452, 11, 6),
                                      (470, 7, -2), (600, 9, 4))):
        bamboo(near, x, -2, int(prof[x % W]) + 4, wdt, pal_near, ("bn", i), lean=ln, node_gap=34, leaves=lv_near,
               leaf_n=3)
    for i in range(8):
        fx = g.uniform(0, W)
        bush(near, fx, int(prof[int(fx) % W]) + 4, g.uniform(20, 34), g.uniform(6, 10), lv_near, ("bnb", i), r=2.5)
    layers.append((near, 0.32, 720))
    return dict(sky="#94b89a", horizon="#ebedcc", layers=layers)


# =============================================================== more primitives (rock, cloud sea, water)
def terraces(cv, prof, ramp, seed, step=12, bench=2, strata=None, marks=True, bench_ramp=None, base_y=None,
             wobble=4):
    """Quarry benches below `prof`: lit bench tops, shaded cut faces with tool marks and strata."""
    h = cv.h
    yy, xx, B = grids(h)
    g = rng("terr", seed)
    n = len(ramp)
    m = yy >= prof[None, :]
    wob = np.round((pn1(("tw", seed), 40, 2) - 0.5) * wobble)
    rel = yy - (prof.min() if base_y is None else base_y) - wob[None, :]
    k = np.floor(rel / step)
    ph = rel - k * step
    v = (n - 1) * 0.62 - ph / step * 1.8
    band_shift = pn1(("tb", seed), 64, 1)
    v = v + (((k + (band_shift[None, :] > 0.6)) % 3) == 1) * -0.6
    if marks:
        tm = ((xx + (k * 3).astype(int)) % 5 == 0) & (ph > bench + 1) & (pn2(h, ("tm", seed), 3, 6, 1) > 0.45)
        v = v - tm * 0.9
    paint(cv, m, ramp, v, sharp=4)
    bp = bench_ramp or ramp
    top = m & (ph < bench)
    flat(cv, top, bp[-2])
    flat(cv, top & (ph < 1), bp[-1])
    flat(cv, m & (np.abs(ph - bench) < 0.5), ramp[1])
    gravel = top & (pn2(h, ("gr", seed), 2, 2, 1) > 0.7)
    flat(cv, gravel, bp[-3])
    if strata is not None:
        sm = m & (ph > bench + 2) & ((ph.astype(int) % 4) == 0) & (pn2(h, ("st", seed), 20, 2, 1) > 0.55)
        flat(cv, sm, strata)
    flat(cv, top_rim(m), bp[-1])
    return m


def cloud_sea(cv, prof, pal, seed, r=7.0, rows=2, spacing=1.35):
    """Billowing sea of cloud: big lit puffs riding `prof`, soft banded body below."""
    return treeline(cv, prof, pal, ("cs", seed), r=r, gain=0.6, spacing=spacing, var=0, rvar=0.35, rows=rows,
                    row_gap=r * 1.6, row_density=0.5, light_by_slope=False)


def waterfall_bd(cv, x, top, bottom, w, pal, seed, foam=True):
    """Static backdrop waterfall: streaked falling sheet, foam and spray at the foot. pal dark->light (>= 4)."""
    h = cv.h
    yy, xx, B = grids(h)
    d = wdx(xx, x)
    widen = (yy - top) / max(1, bottom - top) * 2.0
    edge = (pn2(h, ("wfe", seed), 3, 6, 1) - 0.5) * 2
    m = (np.abs(d) <= w / 2 + widen + edge) & (yy >= top) & (yy <= bottom)
    st = pn2(h, ("wfs", seed), 1.5, 22, 2)
    n = len(pal)
    v = (n - 1) * 0.6 + (st > 0.6) * 1.2 - (st < 0.3) * 1.0 - (d > w * 0.25) * 0.7
    paint(cv, m, pal, v, sharp=3)
    flat(cv, top_rim(m), pal[-1])
    if foam:
        for k in range(7):
            fx = x + (k - 3) * (w * 0.35 + 2)
            fr_ = w * 0.35 + 3 - abs(k - 3) * 0.6
            fm = wellipse(h, fx, bottom - 1 - (k % 2), fr_ * 1.3, fr_ * 0.8) & (yy <= bottom + 2)
            flat(cv, fm, pal[-2])
            flat(cv, fm & ~sh(fm, 1, 1), pal[-1])
        mist_band(cv, bottom - 6, 14, ("wfm", seed), pal[-1], alphas=(0.14, 0.24, 0.34), amp=2, cell=40, gaps=0.0)
    return m


def white_water(cv, ytop, ybot, pal, seed):
    """Rapids: dark water with streaming white foam streaks. pal dark->light (>= 5)."""
    h = cv.h
    yy, xx, B = grids(h)
    m = (yy >= ytop[None, :]) & (yy <= ybot[None, :])
    fs = pn2(h, ("ww", seed), 28, 2.5, 2)
    fs2 = pn2(h, ("ww2", seed), 60, 8, 1)
    n = len(pal)
    depth = (yy - ytop[None, :]) / np.maximum(1, ybot - ytop)[None, :]
    v = (n - 1) * 0.35 + (fs > 0.58) * 1.3 + (fs > 0.7) * 1.2 + (fs2 > 0.6) * 0.8 - depth * 0.8
    paint(cv, m, pal, v, sharp=3)
    flat(cv, top_rim(m), pal[-1])
    return m


def spire(cv, cx, top, hw, ramp, seed, snow=None, base=None, rough=2.2, gain=1.4, trees=None):
    """Sharp granite spire (Huangshan style): conical, jagged, lit left face, snow/frost on lit ridges."""
    g = rng("spire", seed)
    m, prof = karst_peak(cv, cx, top, hw, ramp, ("sp", seed), base=base, p=g.uniform(1.35, 2.0),
                         skirt=g.uniform(1.3, 1.8), skirt_h=g.uniform(0.15, 0.3), gain=gain, rough=rough,
                         trees=trees, tree_frac=0.5, ledges=0.35, shoulder=0.8, crevice=1.2,
                         asym=g.uniform(-0.25, 0.25))
    if snow is not None:
        h = cv.h
        yy, xx, B = grids(h)
        depth = yy - prof[None, :]
        u = row_u(m, wdx(np.arange(W), cx))
        sn = m & (depth < 3 + (pn2(h, ("sn", seed), 2, 5, 1) > 0.5) * 3) & (u < 0.55) & (yy < top + (h - top) * 0.45)
        flat(cv, sn, snow[0])
        flat(cv, sn & (depth < 1.5), snow[1])
    return m, prof


def cloud_bank(cv, base_y, seed, pal, r_lo=8.0, r_hi=16.0, rows=3, row_gap=12, amp=6.0, clip=None, crease=True,
               skip=None, sub=True, fill_below=False):
    """Sea of cumulus. Each row is one mass below the envelope of its puff tops (no seams between
    puffs): bright rim along the tops, light/mid bands going down, creases dropping from the
    notches where puffs meet, lit left halves. Upper rows are drawn first. pal dark->light (>= 5)."""
    h = cv.h
    yy, xx, B = grids(h)
    g = rng("cbank", seed)
    n = len(pal)
    base_n = pn1(("cbn", seed), 80, 2)
    cols = np.arange(W)
    for k in range(rows):
        by = base_y + k * row_gap
        env = np.full(W, np.inf)
        owner = np.full(W, -1)
        uu = np.zeros(W)
        x = g.uniform(0, r_hi)
        i = 0
        puffs = []
        while x < W + r_hi * 0.5:
            r = g.uniform(r_lo, r_hi) * (1.0 + 0.12 * k)
            cy = by + (base_n[int(x) % W] - 0.5) * 2 * amp + g.uniform(-r * 0.25, r * 0.25)
            if skip is None or not skip(x, k):
                puffs.append((x, cy, r))
                if sub and r > 6:
                    for j in range(int(g.integers(1, 3))):
                        sr = r * g.uniform(0.4, 0.6)
                        puffs.append((x + g.uniform(-r * 0.7, r * 0.4), cy - r * g.uniform(0.45, 0.7), sr))
            x += r * g.uniform(1.2, 1.9)
        low = np.full(W, -np.inf)
        for (px, cy, r) in puffs:
            rx, ry = r * 1.3, r * 0.8
            d = wdx(cols, px)
            t = np.clip(1 - (d / rx) ** 2, 0, 1)
            inside = np.abs(d) < rx
            top = np.where(inside, cy - ry * np.sqrt(t), np.inf)
            bot = np.where(inside, cy + (ry * 0.6 + row_gap) * t, -np.inf)
            low = np.maximum(low, bot)
            better = top < env
            env = np.where(better, top, env)
            owner = np.where(better, i, owner)
            uu = np.where(better, (d / rx + 1) / 2, uu)
            i += 1
        env = np.round(np.minimum(env, h + 5))
        # close narrow notches in the underside so rows overlap without pinholes
        kw = int(r_lo * 1.5)
        lo2 = np.where(np.isfinite(low), low, -1e6)
        mx = np.max([np.roll(lo2, j) for j in range(-kw, kw + 1)], axis=0)
        cl = np.min([np.roll(mx, j) for j in range(-kw, kw + 1)], axis=0)
        low = np.where(cl > -1e5, np.maximum(lo2, cl), low)
        if fill_below and k == rows - 1:
            low = np.where(np.isfinite(env) & (env < h), h, low)
        m = (yy >= env[None, :]) & (yy <= np.round(low)[None, :])
        if clip is not None:
            m &= clip
        dep = yy - env[None, :]
        u = uu[None, :]
        v = (n - 1) - (dep >= 1) * 0.9 - (dep >= 4) * 0.9 - (dep >= 10) * 0.7 - (dep >= 18) * 0.6 \
            + ((u < 0.35) & (dep < 7)) * 0.6 - ((u > 0.66) & (dep < 9)) * 0.8
        paint(cv, m, pal, v, sharp=4)
        if crease:
            seam = owner != np.roll(owner, 1)
            notch = seam & (env >= np.roll(env, 1))
            for xi in np.nonzero(notch)[0]:
                ln = int(g.integers(3, 8))
                for dy in range(ln):
                    yv = int(env[xi]) + dy
                    xv = (xi + (dy // 3)) % W
                    if 0 <= yv < h and m[yv, xv]:
                        cv.rgb[yv, xv] = pal[max(0, n - 4)]
        flat(cv, top_rim(m) & (u < 0.62), pal[-1])
    return


def cliff_face(cv, m, ramp, seed, flute=6.0, ledges=0.5, shrub=None, gain=1.2, strata=None):
    """Fluted vertical rock face inside mask m: vertical light/dark columns, ledges with shrubs."""
    h = cv.h
    yy, xx, B = grids(h)
    g = rng("cliff", seed)
    n = len(ramp)
    f1 = pn1(("cf1", seed), flute, 2)
    f2 = pn2(h, ("cf2", seed), flute * 0.6, 28, 2)
    col = np.clip((f1[None, :] - 0.5) * 3.0 + (f2 - 0.5) * 1.5, -1.2, 1.2)
    edge_l = np.diff(np.concatenate([[f1[-1]], f1])) > 0.02
    v = (n - 1) * 0.5 + col * gain
    depth = depth_in(m)
    v = v + np.clip(2 - depth, 0, 2) * 0.6
    paint(cv, m, ramp, v, sharp=3)
    flat(cv, m & edge_l[None, :] & (f2 > 0.45) & (depth > 2), ramp[min(n - 1, int(n * 0.75))])
    if strata is not None:
        sm = m & ((yy + np.round(f1 * 6)[None, :].astype(int)) % 11 == 0) & (pn2(h, ("cs", seed), 10, 2, 1) > 0.5)
        flat(cv, sm & (depth > 3), strata)
    # ledges: short horizontal lit strips with a shadow line under and a few shrubs
    ys, xs = np.nonzero(m & (depth > 6))
    if len(xs):
        for i in g.choice(len(xs), size=min(len(xs), int(ledges * len(xs) / 900) + 1), replace=False):
            ly, lx = int(ys[i]), int(xs[i])
            ln = int(g.integers(5, 14))
            seg = wrect(h, lx, ly, lx + ln, ly) & m
            flat(cv, seg, ramp[-1])
            flat(cv, sh(seg, 0, 1) & m, ramp[0])
            if shrub is not None:
                for j in range(int(g.integers(1, 4))):
                    stamp_crown(cv, SHRUBS[int(g.integers(0, 3))], lx + int(g.integers(0, ln + 1)), ly - 1, shrub,
                                int(g.integers(1, 3)))
    return m


def wall_mass(h, x0, x1, top, seed, jag=4.0, round_r=10.0, crest_amp=6.0, taper=0.0):
    """Mask of a canyon wall block spanning x0..x1 (wrapping) with a jagged crest and jagged vertical sides."""
    yy, xx, _ = grids(h)
    cw = (x1 - x0) % W
    cx = x0 + cw / 2.0
    d = wdx(xx, cx)
    jl = (pn2(h, ("wmj", seed), 6, 14, 2) - 0.5) * 2 * jag
    jr = (pn2(h, ("wmr", seed), 6, 14, 2) - 0.5) * 2 * jag
    tp = taper * np.clip(1 - yy / float(h), 0, 1)
    inside = (d >= -cw / 2 + jl + tp) & (d <= cw / 2 + jr - tp)
    crest = top + (pn1(("wmc", seed), 16, 3) - 0.5) * 2 * crest_amp
    edge_d = np.maximum(0, np.abs(wdx(np.arange(W), cx)) - (cw / 2 - round_r)) / round_r
    crest = crest + np.clip(edge_d, 0, 1.5) ** 2 * round_r * 1.2
    return inside & (yy >= np.round(crest)[None, :])


# =============================================================== scene: quarry
def quarry():
    layers = []
    sky = sky_layer([(0.0, "#9b9e8c"), (0.3, "#b7b395"), (0.55, "#d4c79e"), (0.7, "#e7d6a6"), (1.0, "#dbcb9f")])
    disc(sky, 520, 64, 11, R("#f4e2b0", "#fbefc6", "#fffbea"), halo=C("#f3e3b2"),
         halo_steps=((4.2, 0.08), (2.9, 0.12), (1.8, 0.18)))
    for i, (cx, y, ln) in enumerate(((120, 110, 180), (360, 140, 220), (560, 176, 160), (220, 200, 200),
                                     (40, 226, 140), (460, 236, 180))):
        streak(sky, cx, y, ln, R("#c9b98f", "#dccb9e", "#ece0b8"), ("qs", i), rows=2)
    layers.append((sky, 0.0, 720))

    far = Canvas(W, 170)
    yy, _, _ = grids(170)
    hill_row(far, hill_profile(74, 16, "qfh1", cell=213.34, octaves=3), R("#a39a80", "#aca287", "#b5aa8e", "#c0b597"),
             "qfh1", gain=0.9, sharp=4)
    hill_row(far, hill_profile(98, 10, "qfh2", cell=160, octaves=3), R("#91876f", "#9a8f76", "#a4987d", "#afa287"),
             "qfh2", gain=1.0, sharp=4)
    rt = np.round(116 + (pn1("qrt", 80, 2) - 0.5) * 2)
    river(far, rt, rt + 3, R("#6f9887", "#7ba594", "#89b3a0", "#9fc4b0", "#c8e0cc", "#f2f6e2"), "qriver",
          glint="#fbfbee", ripples=0.6)
    hill_row(far, np.maximum(hill_profile(128, 7, "qfh3", cell=128, octaves=2), rt + 4), R("#877b63", "#90846a",
                                                                                            "#9b8e72", "#a6987c"),
             "qfh3", gain=1.0, sharp=4)
    base_fade(far, 118, 150, "#d8c8a0", steps=3)
    flat(far, yy >= 150, "#d8c8a0")
    mist_band(far, 104, 14, "qfm", "#ead9ae", alphas=(0.18, 0.3, 0.44), amp=3)
    layers.append((far, 0.08, 560))

    mh = 180
    mid = Canvas(W, mh)
    yy, xx, _ = grids(mh)
    cols = np.arange(W)
    rockr = R("#4c3f33", "#5f4f3f", "#74614b", "#8a7457", "#a08865", "#b89f7a", "#cfb892")
    ochre = R("#5e452e", "#765536", "#8e6840", "#a67c4c", "#bb915c", "#cea871", "#dfc08d")
    bench = R("#8c7a5c", "#a89270", "#c4ad86", "#d9c49c", "#ebdab4", "#f5ead0")
    crest = hill_profile(34, 8, "qcrest", cell=64, octaves=3)
    nat = yy >= crest[None, :]
    cliff_face(mid, nat, rockr, "qcliff", flute=5, ledges=0.6, shrub=R("#3f4a2c", "#55603a", "#6c7747", "#86905a"),
               strata="#6b5a45")
    treeline(mid, crest, R("#3c4630", "#4a563a", "#5a6644", "#6c7850", "#838c60"), "qscrub", r=1.5, gain=0.8,
             below=crest + 3)
    base = 30
    step = 12
    for (pc, pw) in ((170, 118), (470, 104)):
        d = np.abs(wdx(cols, pc))
        kk = np.floor(np.clip(pw - d, 0, None) / 12.0)
        pit_prof = np.where(d < pw, base + step * kk, np.inf)
        pit_prof = np.minimum(pit_prof, mh + 5)
        cut = (d < pw)[None, :] & (yy < pit_prof[None, :]) & (yy >= crest[None, :] - 6)
        mid.erase(cut)
        region = (d < pw)[None, :] & (yy >= pit_prof[None, :])
        terr = Canvas(W, mh)
        terraces(terr, np.where(d < pw, pit_prof, mh + 5), ochre, ("qter", pc), step=step, bench=2, strata="#8c8578",
                 bench_ramp=bench, base_y=base, wobble=0)
        mid.rgb[region] = terr.rgb[region]
        mid.a[region] = terr.a[region]
        # the cut edge against the natural rock
        edge = region & ~sh(region, 1, 0) | region & ~sh(region, -1, 0)
        flat(mid, edge & (yy > crest[None, :] + 1), rockr[1])
    # scaffolds and ladders on the benches
    for i, (sx, lvl, sh_) in enumerate(((120, 3, 34), (206, 5, 22), (430, 2, 40), (512, 4, 26))):
        sy = base + step * lvl + 3
        for px in (sx, sx + 8):
            flat(mid, wrect(mh, px, sy, px, sy + sh_), "#4a3622")
        for ry in range(sy + 2, sy + sh_, 6):
            flat(mid, wrect(mh, sx, ry, sx + 8, ry), "#6b5234")
        flat(mid, wrect(mh, sx - 2, sy, sx + 10, sy), "#8a6a44")
        lx = sx + 14
        flat(mid, wrect(mh, lx, sy - 2, lx, sy + sh_) | wrect(mh, lx + 3, sy - 2, lx + 3, sy + sh_), "#5a4228")
        for ry in range(sy, sy + sh_, 3):
            flat(mid, wrect(mh, lx, ry, lx + 3, ry), "#7d6040")
    g = rng("qblocks")
    for i in range(22):
        pc, pw = ((170, 118), (470, 104))[i % 2]
        bx = int(pc + g.uniform(-pw * 0.9, pw * 0.9)) % W
        lvl = int(np.floor(max(0, pw - abs(wdx(bx, pc))) / 12.0))
        by = base + step * lvl - 1
        if 0 < by < mh - 2 and mid.a[by + 2, bx] > 0:
            blk = wrect(mh, bx, by - 3, bx + 4, by)
            flat(mid, blk, "#b8ab94")
            flat(mid, top_rim(blk), "#ded3bd")
            flat(mid, right_rim(blk), "#7f7462")
    mist_band(mid, 70, 14, "qmm1", "#ead8aa", alphas=(0.14, 0.24, 0.34), amp=4, gaps=0.35)
    mist_band(mid, 150, 22, "qmm2", "#e6d2a2", alphas=(0.2, 0.34, 0.48), amp=4, gaps=0.1)
    layers.append((mid, 0.18, 620))

    near = Canvas(W, 200)
    yy, _, _ = grids(200)
    cx0, gy = 250, 152
    wood = R("#2e2014", "#4a3420", "#6a4c2e", "#8c6a42")
    for (a, b) in (((cx0 - 16, gy), (cx0, gy - 70)), ((cx0 + 12, gy), (cx0, gy - 70)), ((cx0, gy - 66), (cx0 + 58, gy - 96))):
        flat(near, wline(200, [a, b], 3), wood[1])
        flat(near, wline(200, [(a[0] - 1, a[1]), (b[0] - 1, b[1])], 1), wood[3])
    flat(near, wline(200, [(cx0 - 12, gy - 20), (cx0 + 9, gy - 20)], 2), wood[2])
    flat(near, wrect(200, cx0 + 56, gy - 96, cx0 + 56, gy - 58), "#1c140c")
    blk = wrect(200, cx0 + 50, gy - 58, cx0 + 62, gy - 48)
    flat(near, blk, "#9d9380")
    flat(near, top_rim(blk) | left_rim(blk), "#c7bda8")
    flat(near, bot_rim(blk) | right_rim(blk), "#6a6152")
    stone = R("#3b332b", "#4f463b", "#665b4d", "#807260", "#9b8b74", "#b7a68b", "#d0c0a2")
    for i, (bx, rx, ry) in enumerate(((40, 24, 16), (78, 14, 9), (160, 18, 12), (350, 30, 20), (400, 16, 10),
                                      (520, 22, 14), (600, 26, 18))):
        rock_blob(near, bx, gy + 4, rx, ry, stone, ("qnr", i), facets=4)
    for i, (bx, by) in enumerate(((450, gy), (462, gy), (456, gy - 8), (300, gy))):
        b2 = wrect(200, bx, by - 7, bx + 10, by)
        flat(near, b2, "#a39884")
        flat(near, top_rim(b2), "#d0c5ae")
        flat(near, right_rim(b2) | bot_rim(b2), "#5f5648")
        flat(near, left_rim(b2), "#bcb29c")
    m, prof = ground_bank(near, gy + 2, "qbank", R("#3a2f22", "#4a3c2b", "#5c4b35", "#6e5a40", "#83704f", "#9a8561"),
                          amp=1.5, tufts=R("#6d6a45", "#807b52", "#948d5e"))
    layers.append((near, 0.32, 720))
    return dict(sky="#9b9e8c", horizon="#e7d6a6", layers=layers)


# =============================================================== scene: mist peaks above a sea of cloud
def mist_peak():
    layers = []
    sky = sky_layer([(0.0, "#3a6795"), (0.3, "#6b98bf"), (0.55, "#a6c5dc"), (0.72, "#d6e5ef"), (0.85, "#eef4f7"),
                     (1.0, "#e4edf2")])
    for i, (cx, y, ln) in enumerate(((90, 60, 170), (330, 40, 120), (520, 84, 200), (250, 110, 150), (600, 130, 110))):
        streak(sky, cx, y, ln, R("#8fb2cf", "#c9dcea", "#f2f8fb"), ("mps", i), rows=2)
    layers.append((sky, 0.0, 720))

    fh = 220
    far = Canvas(W, fh)
    yy, _, _ = grids(fh)
    back = R("#7894b0", "#849fb9", "#92acc3", "#a2b9cd", "#b8c9d8", "#d4dfe9")
    for i, (cx, top, hw) in enumerate(gen_peaks("mpb", 7, 36, 86, 24, 38)):
        karst_peak(far, cx, top, hw, back, ("mpb", i), p=rng("mpbp", i).uniform(1.5, 2.3), rough=2.0, gain=1.1,
                   crevice=1.2, shoulder=0.8)
    base_fade(far, 110, 176, "#e8f0f5", steps=3)
    front = R("#2f4a68", "#3b5776", "#4a6684", "#5d7893", "#7a91a8", "#a3b6c6")
    for i, (cx, top, hw) in enumerate(gen_peaks("mpf", 5, 6, 56, 24, 36)):
        spire(far, cx, top, hw, front, ("mpf", i), snow=R("#d6e3ee", "#f4f9fc"),
              trees=R("#1f3b44", "#294a50", "#34585a", "#42685f", "#547966"))
    base_fade(far, 134, 192, "#eef4f7", steps=4)
    cloud_bank(far, 178, "mpcb0", R("#9db5ca", "#b8cadb", "#d0dde8", "#e6eef4", "#f6f9fb", "#ffffff"), r_lo=5, r_hi=12,
               rows=2, row_gap=12, amp=5, fill_below=True)
    layers.append((far, 0.08, 560))

    mh = 180
    mid = Canvas(W, mh)
    yy, _, _ = grids(mh)
    cols = np.arange(W)
    rock = R("#243a50", "#2e4760", "#3a556e", "#4a667e", "#62798f", "#8497aa", "#b0bfcc")
    pine_c = R("#16302e", "#1d3d38", "#264b42", "#305a4b", "#3d6b54", "#51805f")
    m1, p1 = karst_peak(mid, 118, 38, 40, rock, "mpm1", p=3.4, skirt=1.5, skirt_h=0.3, rough=1.2, trees=pine_c,
                        shoulder=0.0, asym=0.1)
    m2, p2 = spire(mid, 480, 30, 30, rock, "mpm2", snow=R("#cfdde8", "#f2f7fa"), trees=pine_c, rough=1.4)
    sx = 118
    top_y = int(p1[sx % W])
    hall(mid, sx - 17, top_y + 4, 34, 7, 6, R("#1a262e", "#283843", "#465a66", "#6d8391"),
         R("#8e8e86", "#d9d6cc", "#f1eee6"), post_col="#7a2e28", tiers=2)
    stair = wline(mh, [(sx + 18, top_y + 4), (sx + 30, top_y + 28)], 2)
    flat(mid, stair & (mid.a > 0), "#c9ccc6")
    # a break in the cloud sea looking down on the valley and the Jade River
    gap_c, gap_w = 300, 84
    val = Canvas(W, mh)
    flat(val, yy >= 0, "#a9bfcd")
    vp = np.round(112 + (pn1("mpv", 20, 2) - 0.5) * 8)
    hill_row(val, vp, R("#2c4a4c", "#35574f", "#3f6455", "#4b725c"), "mpv", gain=0.8, rim=False)
    treeline(val, vp, R("#1f3a38", "#284841", "#31554a", "#3c6352", "#4a735c"), "mpvt", r=1.5, rows=3)
    rv_top = np.round(132 + np.sin(cols / W * 9 * math.pi + 1.0) * 4)
    rv = (yy >= rv_top[None, :]) & (yy <= rv_top[None, :] + 2)
    flat(val, rv, "#34a893")
    flat(val, rv & top_rim(rv), "#8ae2c9")
    flat(val, rv & (pn2(mh, "mprg", 6, 1, 1) > 0.7), "#e6fbf0")
    base_fade(val, 100, 126, "#b7cbd9", steps=3, m=(yy < 126))
    mist_band(val, 122, 6, "mpvm", "#dfe9f0", alphas=(0.2, 0.34), amp=2, gaps=0.2)
    win = wellipse(mh, gap_c, 130, gap_w, 34) & (pn2(mh, "mpwin", 12, 8, 2) > 0.2)
    mid.rgb[win] = val.rgb[win]
    mid.a[win] = 1.0
    pal_c = R("#8ea7be", "#a8bdd1", "#c2d3e1", "#dae6ef", "#eef4f8", "#ffffff")
    cloud_bank(mid, 98, "mpcb1", pal_c, r_lo=7, r_hi=16, rows=3, row_gap=16, amp=6,
               skip=lambda x, k: abs(wdx(x, gap_c)) < gap_w * (1.0 - 0.3 * k))
    cloud_bank(mid, 158, "mpcb1b", pal_c, r_lo=9, r_hi=18, rows=1, row_gap=14, amp=5, fill_below=True)
    layers.append((mid, 0.18, 620))

    near = Canvas(W, 200)
    yy, _, _ = grids(200)
    rockn = R("#16263a", "#1e3048", "#283d56", "#344b64", "#465e75", "#627a8e")
    for i, (cx, top, hw) in enumerate(((70, 40, 26), (420, 70, 22))):
        m, p = spire(near, cx, top, hw, rockn, ("mpn", i), trees=pine_c, rough=1.2, gain=1.2)
        pine(near, cx + 4, int(p[(cx + 4) % W]) + 2, 34 - i * 8, pine_c, R("#2a2420", "#3d342c", "#554739", "#6e5d49"),
             ("mpnp", i), lean=0.5 if i == 0 else -0.4, pads=5, pad_w=11)
    cloud_bank(near, 146, "mpcb2", R("#9db4c8", "#b5c8d8", "#cddbe6", "#e2ebf2", "#f3f7fa", "#ffffff"), r_lo=10, r_hi=24,
               rows=2, row_gap=22, amp=8, fill_below=True)
    layers.append((near, 0.32, 720))
    return dict(sky="#3a6795", horizon="#eef4f7", layers=layers)


# =============================================================== scene: gorge
def gorge():
    layers = []
    sky = sky_layer([(0.0, "#78a9bf"), (0.35, "#9dc3cd"), (0.6, "#c5dbd6"), (0.8, "#dfe8da"), (1.0, "#d5e0d4")])
    for i, (cx, cy, ln, th) in enumerate(((120, 50, 70, 6), (420, 30, 60, 5), (560, 90, 80, 6))):
        cloud(sky, cx, cy, ln, th, ("gc", i), R("#b8cdd2", "#dfe9e6", "#f6f7ee", "#ffffff"))
    layers.append((sky, 0.0, 720))

    fh = 250
    far = Canvas(W, fh)
    yy, _, _ = grids(fh)
    back_wall = yy >= hill_profile(56, 12, "gbw", cell=80, octaves=3)[None, :]
    cliff_face(far, back_wall, R("#8aa3a0", "#93aca8", "#9eb5b0", "#aabfb8", "#b8cbc2"), "gbw", flute=8, ledges=0.2,
               gain=0.8)
    wall = R("#5e7774", "#69827e", "#768e89", "#869c95", "#99aea5", "#b3c4ba")
    shrub = R("#3f5d52", "#4a6a5b", "#567864", "#63866d", "#779878")
    walls = [(-40, 150, 14), (190, 300, 26), (340, 560, 8)]
    for i, (x0, x1, top) in enumerate(walls):
        wm = wall_mass(fh, x0 % W, x1 % W, top, ("gfw", i), jag=3, round_r=12, crest_amp=5)
        cliff_face(far, wm, wall, ("gfwf", i), flute=5, ledges=0.7, shrub=shrub, strata="#566e6a")
        crest = np.where(wm.any(axis=0), np.argmax(wm, axis=0), fh + 5).astype(float)
        treeline(far, crest, shrub, ("gfwt", i), r=1.5, below=crest + 3)
    wf = R("#a3c3c4", "#c0d8d6", "#dcebe8", "#f2f9f6", "#ffffff")
    waterfall_bd(far, 246, 24, 226, 10, wf, "gwf1")
    waterfall_bd(far, 470, 12, 226, 6, wf, "gwf2")
    base_fade(far, 150, 232, "#cfe0da", steps=4)
    ww = np.round(230 + (pn1("gww", 40, 2) - 0.5) * 3)
    white_water(far, ww, np.full(W, fh - 1.0), R("#2f6c68", "#3f8580", "#5aa39a", "#9fd2c6", "#e0f4ec", "#ffffff"),
                "gfw")
    layers.append((far, 0.08, 560))

    mh = 240
    mid = Canvas(W, mh)
    yy, _, _ = grids(mh)
    wall2 = R("#1d302e", "#253b38", "#304945", "#3d5953", "#4d6b63", "#66827a", "#86a096")
    tr2 = R("#142820", "#1a3528", "#224330", "#2c5239", "#386344")
    for i, (x0, x1, top) in enumerate(((-110, 146, 4), (404, 540, 16))):
        wm = wall_mass(mh, x0 % W, x1 % W, top, ("gmw", i), jag=5, round_r=16, crest_amp=6)
        cliff_face(mid, wm, wall2, ("gmwf", i), flute=6, ledges=0.8, shrub=tr2, strata="#2c4440", gain=1.3)
        crest = np.where(wm.any(axis=0), np.argmax(wm, axis=0), mh + 5).astype(float)
        treeline(mid, crest, tr2, ("gmwt", i), r=2.0, below=crest + 4)
    pine(mid, 128, 30, 40, R("#10261f", "#163226", "#1f402d", "#2a4f35", "#375f3d", "#4a7346"),
         R("#1c1714", "#2c241e", "#3e3329", "#524336"), "gmp", lean=0.8, pads=5, pad_w=10)
    waterfall_bd(mid, 470, 24, 214, 8, R("#8ab4b4", "#b4d4d2", "#d6ebe7", "#f0f9f5", "#ffffff"), "gwf3")
    rt = np.round(212 + (pn1("gmr", 32, 2) - 0.5) * 4)
    white_water(mid, rt, np.full(W, mh - 1.0), R("#1f5552", "#2c6b66", "#46908a", "#8bc8bc", "#d6f0e8", "#ffffff"),
                "gmw")
    for i, bx in enumerate((200, 262, 330, 372)):
        rock_blob(mid, bx, int(rt[bx]) + 10, 9 + i % 3 * 3, 6 + i % 2 * 2, wall2, ("gmr", i), facets=3)
        foam = wellipse(mh, bx - 2, int(rt[bx]) + 10, 13, 2) & (yy >= int(rt[bx]) + 8)
        flat(mid, foam & ~(mid.a > 0) | foam & (yy >= int(rt[bx]) + 10), "#e8f6f0")
    mist_band(mid, 208, 14, "gmm", "#e6f1ec", alphas=(0.18, 0.3, 0.44), amp=3, gaps=0.2)
    layers.append((mid, 0.18, 620))

    near = Canvas(W, 200)
    yy, _, _ = grids(200)
    dark = R("#0f1c1c", "#152524", "#1c302e", "#253c39", "#314a45", "#435d55")
    ww = np.round(150 + (pn1("gnw", 40, 2) - 0.5) * 4)
    white_water(near, ww, np.full(W, 199.0), R("#123a38", "#1d4f4b", "#34736c", "#76b3a8", "#cfeee4", "#ffffff"), "gnw")
    for i, (bx, rx, ry) in enumerate(((50, 46, 44), (150, 22, 14), (380, 30, 20), (560, 50, 50))):
        rock_blob(near, bx, 190, rx, ry, dark, ("gnr", i), facets=4, moss=R("#2c4a33", "#3f6443"))
        foam = wellipse(200, bx, 186, rx + 7, 3) & (near.a == 0) & (yy >= 184)
        flat(near, foam, "#e3f3ec")
    pine(near, 548, 146, 60, R("#10261f", "#163226", "#1f402d", "#2a4f35", "#375f3d", "#4a7346"),
         R("#1c1714", "#2c241e", "#3e3329", "#524336"), "gnp", lean=-0.6, pads=5, pad_w=12)
    for i in range(12):
        vx = 22 + i * 6
        ln = 16 + (i * 7) % 22
        flat(near, wline(200, [(vx, 152), (vx + 1, 152 + ln * 0.5), (vx, 152 + ln)]), "#2f5236" if i % 2 else "#3d6a42")
    layers.append((near, 0.32, 720))
    return dict(sky="#78a9bf", horizon="#dfe8da", layers=layers)


# =============================================================== cave, sect and interior primitives
def spikes(base, seed, n, len_lo, len_hi, w_lo, w_hi, sign=1, curve=1.3, noise=2.0):
    """Profile of a ceiling (sign=+1: spikes hang down from `base`) or floor (sign=-1: spikes rise)."""
    g = rng("spk", seed)
    cols = np.arange(W)
    prof = np.full(W, float(base)) + (pn1(("spkn", seed), 16, 2) - 0.5) * 2 * noise * sign
    for i in range(n):
        cx = g.uniform(0, W)
        ln = g.uniform(len_lo, len_hi)
        w = g.uniform(w_lo, w_hi)
        t = np.abs(wdx(cols, cx)) / w
        c = ln * np.clip(1 - t, 0, 1) ** curve
        prof = prof + sign * np.maximum(0, c - np.maximum(0, (prof - base) * sign))
    return np.round(prof)


def rock_mass(cv, m, ramp, seed, gain=1.3, crevice=0.8, rim=True):
    """Shade an arbitrary rock mask: lit left of each row run, vertical crevices, lit upper rims."""
    h = cv.h
    yy, xx, B = grids(h)
    n = len(ramp)
    u = row_u_local(m)
    v = (n - 1) * 0.5 + (0.5 - u) * 2 * gain
    st = pn2(h, ("rmc", seed), 2.5, 14, 2)
    v = v - ((st > 0.66) & (u > 0.3)) * crevice - ((st < 0.2) & (u < 0.5)) * -0.6 * crevice
    paint(cv, m, ramp, v, sharp=3.5)
    if rim:
        flat(cv, top_rim(m) & (u < 0.6), ramp[-1])
        flat(cv, left_rim(m) & ~top_rim(m), ramp[min(n - 1, n - 2)])
        flat(cv, right_rim(m) | bot_rim(m), ramp[0])
    return m


def row_u_local(m):
    """Like row_u but per contiguous run in each row (wraps in x)."""
    h, w = m.shape
    u = np.zeros((h, w))
    for y in range(h):
        row = m[y]
        if not row.any():
            continue
        if row.all():
            u[y] = 0.5
            continue
        start = int(np.argmin(row))  # a gap column: runs never wrap past it
        r = np.roll(row, -start)
        idx = np.nonzero(np.diff(np.concatenate([[0], r.astype(int), [0]])))[0]
        uu = np.zeros(w)
        for a, b in zip(idx[::2], idx[1::2]):
            uu[a:b] = (np.arange(a, b) - a) / max(1, b - a - 1)
        u[y] = np.roll(uu, start)
    return u


def crystal(cv, x, by, size, pal, seed, glow_c=None, lean=0.0):
    """Cluster of glowing jade crystal prisms rising from (x, by). pal dark->light (>= 5)."""
    h = cv.h
    yy, xx, B = grids(h)
    g = rng("crys", seed)
    n = len(pal)
    if glow_c is not None:
        for s_, a in ((1.5, 0.08), (1.05, 0.12)):
            flat(cv, wellipse(h, x, by - size * 0.45, size * s_, size * s_ * 0.75), glow_c, a)
    shards = []
    for k in range(int(g.integers(3, 6))):
        ang = lean + g.uniform(-0.6, 0.6) + (k - 2) * 0.18
        ln = size * g.uniform(0.55, 1.1) * (1.1 if k == 2 else 1.0)
        wd = max(1.5, size * g.uniform(0.14, 0.24))
        bx = x + g.uniform(-size * 0.35, size * 0.35)
        shards.append((ang, ln, wd, bx))
    shards.sort(key=lambda s_: -s_[1])
    for (ang, ln, wd, bx) in shards:
        ux, uy = math.sin(ang), -math.cos(ang)
        px, py = -uy, ux
        tipx, tipy = bx + ux * ln, by + uy * ln
        shx, shy = bx + ux * (ln - wd * 1.6), by + uy * (ln - wd * 1.6)
        pts = [(bx - px * wd, by - py * wd), (shx - px * wd, shy - py * wd), (tipx, tipy), (shx + px * wd, shy + py * wd),
               (bx + px * wd, by + py * wd)]
        sm = wpoly(h, pts)
        mid_line = wline(h, [(bx, by), (tipx, tipy)])
        left = sm & ((wdx(xx, bx) * uy - (yy - by) * ux) > 0)
        flat(cv, sm, pal[2])
        flat(cv, left, pal[3])
        flat(cv, mid_line & sm, pal[4])
        flat(cv, right_rim(sm), pal[1])
        flat(cv, top_rim(sm) & left, pal[-1])
        put(cv, int(round(tipx)), int(round(tipy)), pal[-1])
    return


def masonry(cv, m, pal, seed, course=4, joint=7):
    """Dressed-stone wall inside mask m: courses with staggered joints, lit top edge. pal dark->light (>= 4)."""
    h = cv.h
    yy, xx, B = grids(h)
    n = len(pal)
    nz = pn2(h, ("mas", seed), 4, 4, 1)
    v = (n - 1) * 0.55 + (nz - 0.5) * 1.0
    paint(cv, m, pal, v, sharp=3)
    row = (yy // course)
    flat(cv, m & (yy % course == 0), pal[1])
    flat(cv, m & (((xx + (row % 2) * (joint // 2)) % joint) == 0) & (yy % course != 0), pal[1])
    flat(cv, m & (yy % course == 1) & (((xx + (row % 2) * (joint // 2)) % joint) == 1), pal[-1])
    flat(cv, top_rim(m), pal[-1])
    flat(cv, sh(top_rim(m), 0, 1) & m, pal[-2])
    return m


def stairs(cv, x0, y0, x1, y1, pal, width=6):
    """Straight flight of steps from (x0, y0) (bottom) to (x1, y1) (top). pal (dark, mid, light)."""
    h = cv.h
    n_steps = max(1, int(abs(y0 - y1) / 2))
    for i in range(n_steps + 1):
        t = i / n_steps
        cx = x0 + (x1 - x0) * t
        cy = int(round(y0 + (y1 - y0) * t))
        tread = wrect(h, int(round(cx - width / 2)), cy, int(round(cx + width / 2)), cy)
        riser = wrect(h, int(round(cx - width / 2)), cy + 1, int(round(cx + width / 2)), cy + 1)
        flat(cv, riser, pal[1])
        flat(cv, tread, pal[2])
    for sgn in (-1, 1):
        flat(cv, wline(h, [(x0 + sgn * (width / 2 + 1), y0 + 1), (x1 + sgn * (width / 2 + 1), y1)], 1), pal[0])


def balustrade(cv, y, pal, seed, post_gap=24, rail_h=9):
    """White-stone balustrade running along row y (top rail at y - rail_h). pal dark->light (>= 4)."""
    h = cv.h
    yy, xx, B = grids(h)
    top = y - rail_h
    rail = (yy >= top) & (yy <= top + 1)
    base = (yy >= y - 1) & (yy <= y)
    flat(cv, base, pal[1])
    flat(cv, top_rim(base), pal[2])
    for x in range(0, W, post_gap):
        p_ = wrect(h, x, top - 2, x + 3, y)
        flat(cv, p_, pal[2])
        flat(cv, left_rim(p_), pal[3])
        flat(cv, right_rim(p_), pal[0])
        flat(cv, wrect(h, x - 1, top - 3, x + 4, top - 2), pal[3])
        for bx in range(x + 6, x + post_gap - 3, 4):
            b = wrect(h, bx, top + 2, bx + 1, y - 2)
            flat(cv, b, pal[1])
            put(cv, bx, top + 2, pal[3])
    flat(cv, rail, pal[2])
    flat(cv, top_rim(rail), pal[3])
    flat(cv, bot_rim(rail), pal[0])


def arch_bridge(cv, cx, y, span, pal, rise=10, deck=3):
    """Stone arch bridge over water: deck at row y, arch opening beneath. pal dark->light (>= 4)."""
    h = cv.h
    yy, xx, B = grids(h)
    d = wdx(xx, cx)
    body = (np.abs(d) <= span / 2) & (yy >= y) & (yy <= y + rise + deck)
    body |= (np.abs(d) <= span / 2 + 4) & (yy >= y + rise * 0.5) & (yy <= y + rise + deck) & (np.abs(d) > span / 2)
    d1 = wdx(np.arange(W), cx)
    hump = np.round(y - 3 * np.cos(np.clip(d1 / (span / 2), -1, 1) * math.pi / 2))
    body |= (np.abs(d) <= span / 2) & (yy >= hump[None, :]) & (yy < y)
    opening = ((d / (span * 0.36)) ** 2 + ((yy - (y + rise + deck)) / (rise + 0.5)) ** 2) <= 1.0
    body &= ~opening
    flat(cv, body, pal[2])
    flat(cv, top_rim(body), pal[3])
    flat(cv, body & ~sh(body, 0, 1) & sh(opening, 0, 1), pal[0])
    flat(cv, body & sh(opening, -1, 0), pal[1])
    rail = (np.abs(d) <= span / 2) & (yy == hump[None, :] - 2)
    flat(cv, rail, pal[1])
    for px in range(int(cx - span / 2), int(cx + span / 2) + 1, 5):
        put(cv, px, int(hump[px % W]) - 1, pal[1])
    return body


# =============================================================== scene: jade crystal cave
def cave():
    layers = []
    sky = sky_layer([(0.0, "#020708"), (0.3, "#061518"), (0.52, "#0b2527"), (0.62, "#0e2c2d"), (0.8, "#081a1c"),
                     (1.0, "#040d0f")], bands=14)
    g = rng("cavesky")
    for i in range(70):
        x, y = int(g.integers(0, W)), int(g.integers(120, 260))
        put(sky, x, y, "#1f5a55" if i % 3 else "#2c8a7c")
    layers.append((sky, 0.0, 720))

    H = 360
    far = Canvas(W, H)
    yy, _, _ = grids(H)
    ramp_f = R("#0b2123", "#0f2a2b", "#133333", "#183c3b", "#1e4644", "#27524e")
    ceil = spikes(34, "cfc", 34, 10, 70, 5, 14, sign=1)
    rock_mass(far, yy <= ceil[None, :], ramp_f, "cfc", gain=1.0)
    floor = spikes(318, "cff", 26, 8, 60, 5, 14, sign=-1)
    rock_mass(far, yy >= floor[None, :], ramp_f, "cff", gain=1.0)
    for i, (px, pw) in enumerate(((120, 14), (430, 18))):
        col = wall_mass(H, px - pw, px + pw, 0, ("cfcol", i), jag=2, round_r=2, crest_amp=0)
        waist = (np.abs(wdx(xx_all(H), px)) > pw * (0.55 + 0.45 * np.abs((yy - 180) / 180.0))) & (yy > 60) & (yy < 300)
        rock_mass(far, col & ~waist, ramp_f, ("cfcol", i), gain=1.0)
    for i in range(10):
        cx = int(g.integers(0, W))
        crystal(far, cx, int(floor[cx]) + 2, int(g.integers(5, 9)), R("#0e3a36", "#155048", "#1f6a5c", "#2c8a76",
                                                                        "#48a892", "#7ccfb8"), ("cfx", i),
                glow_c="#2c9e8f")
    haze_fade(far, far.a > 0, "#123634", np.full((H, W), 0.4), steps=2, sharp=1)
    layers.append((far, 0.06, 720))

    mid = Canvas(W, H)
    ramp_m = R("#061314", "#091b1c", "#0d2425", "#122e2e", "#183939", "#204544", "#2c5654")
    ceil = spikes(18, "cmc", 16, 20, 110, 7, 18, sign=1)
    rock_mass(mid, yy <= ceil[None, :], ramp_m, "cmc", gain=1.2)
    for i in range(6):
        cx = int(g.integers(0, W))
        tip = int(ceil[cx])
        for k in range(3):
            put(mid, cx, tip + 2 + k * 4, "#3fb5a0" if k == 0 else "#1f6a5c")
    floor = spikes(300, "cmf", 14, 10, 70, 8, 20, sign=-1)
    rock_mass(mid, yy >= floor[None, :], ramp_m, "cmf", gain=1.2)
    st = np.round(322 + (pn1("cms", 40, 2) - 0.5) * 4)
    river(mid, st, np.full(W, H - 1.0), R("#0c3a36", "#135048", "#1f6a5c", "#2c9e8f", "#67d6bd", "#c7f7e8"), "cmriver",
          bank="#07191a", glint="#d2fbea", reflect="#0e2d2c", reflect_rows=2)
    for i, cx in enumerate((60, 150, 250, 330, 410, 520, 590)):
        crystal(mid, cx, int(floor[cx]) + 3, int(g.integers(8, 15)), R("#0f4a44", "#17645a", "#23846f", "#2c9e8f",
                                                                        "#67d6bd", "#c7f7e8"), ("cmx", i),
                glow_c="#32bed1" if i % 3 == 0 else "#2c9e8f", lean=g.uniform(-0.3, 0.3))
    layers.append((mid, 0.16, 720))

    near = Canvas(W, H)
    ramp_n = R("#020809", "#040d0e", "#061314", "#0a1b1c", "#0f2425", "#153031")
    ceil = spikes(4, "cnc", 7, 30, 120, 10, 26, sign=1)
    rock_mass(near, yy <= ceil[None, :], ramp_n, "cnc", gain=1.0)
    floor = spikes(350, "cnf", 8, 10, 60, 12, 26, sign=-1)
    rock_mass(near, yy >= floor[None, :], ramp_n, "cnf", gain=1.0)
    for i, cx in enumerate((40, 300, 470)):
        crystal(near, cx, int(floor[cx]) + 4, 20 + i * 3, R("#11574f", "#1a7466", "#2c9e8f", "#48b9a0", "#8ae6cc",
                                                            "#e3fff4"), ("cnx", i), glow_c="#67d6bd", lean=0.2 - i * 0.2)
    layers.append((near, 0.3, 720))
    return dict(sky="#020708", horizon="#0e2c2d", layers=layers)


# =============================================================== scene: Jade sect on its terraces
def sect_complex(cv, cx, base_y, levels, seed, roof, wall, stone, post="#8a2f28", lit=None, width=150):
    """Terraced sect compound: stone retaining walls stepping up, halls on each level, a central stair."""
    h = cv.h
    yy, xx, _ = grids(h)
    g = rng("sect", seed)
    y = base_y
    w = width
    tops = []
    for k in range(levels):
        wall_h = 9 if k else 11
        tw = wrect(h, int(cx - w / 2), y - wall_h + 1, int(cx + w / 2), y)
        masonry(cv, tw, stone, (seed, k), course=3, joint=6)
        tops.append((y - wall_h, w))
        y = y - wall_h
        w = w * g.uniform(0.62, 0.74)
    # halls (top level first so lower terraces' halls overlap nothing above them)
    for k, (ty, tw_) in enumerate(tops):
        if k == len(tops) - 1:
            hw = int(tw_ * 0.7)
            hall(cv, int(cx - hw / 2), ty, hw, 10, 8, roof, wall, post_col=post, lit=lit, tiers=2)
        else:
            nxt = tops[k + 1][1]
            for side in (-1, 1):
                space = (tw_ - nxt) / 2
                if space < 12:
                    continue
                hw = int(min(28, space - 2))
                hx = int(cx + side * (nxt / 2 + space / 2) - hw / 2)
                hall(cv, hx, ty, hw, 7, 6, roof, wall, post_col=post, lit=lit, tiers=1)
    # central stair up the terraces
    stairs(cv, cx, base_y, cx, tops[-1][0] + 1, stone[1:4], width=7)
    return tops


def sect_jade():
    layers = []
    sky = sky_layer([(0.0, "#86b3b8"), (0.3, "#a7cac3"), (0.55, "#d6ddbd"), (0.68, "#f1e2ae"), (0.8, "#efe6c6"),
                     (1.0, "#e2e6d0")])
    disc(sky, 150, 132, 10, R("#f7e7b4", "#fff3cc", "#fffbea"), halo=C("#fff2c4"),
         halo_steps=((4.0, 0.09), (2.7, 0.13), (1.7, 0.2)))
    for i, (cx, cy, ln, th) in enumerate(((420, 60, 90, 7), (600, 100, 60, 5), (260, 40, 70, 6))):
        cloud(sky, cx, cy, ln, th, ("sjc", i), R("#bcd2cf", "#e3ece2", "#f8f6e6", "#fffbea"))
    for i, (cx, y, ln) in enumerate(((320, 170, 190), (80, 196, 150), (520, 214, 170))):
        streak(sky, cx, y, ln, R("#c2d4cc", "#e6ebdc", "#fbf6e2"), ("sjs", i), rows=2)
    layers.append((sky, 0.0, 720))

    far = Canvas(W, 170)
    yy, _, _ = grids(170)
    hill_row(far, hill_profile(52, 20, "sjr", cell=160, octaves=3), R("#9ab4bf", "#a4bcc6", "#afc5cc", "#bcced3"),
             "sjr", gain=0.9, sharp=4)
    ink = R("#3a5670", "#46637b", "#547186", "#668192", "#7e96a4", "#9fb2bc")
    for i, (cx, top, hw) in enumerate(gen_peaks("sjp", 6, 20, 70, 34, 56)):
        karst_peak(far, cx, top, hw, ink, ("sjp", i), p=rng("sjpp", i).uniform(1.4, 2.0), rough=2.2, gain=1.2,
                   trees=R("#2e4a50", "#375657", "#43635e", "#517066", "#62806f"), tree_frac=0.5, ledges=0.5)
    base_fade(far, 92, 150, "#dfe5d6", steps=4)
    flat(far, yy >= 150, "#dfe5d6")
    mist_band(far, 124, 16, "sjfm", "#f2f1e2", alphas=(0.22, 0.4, 0.58), amp=4)
    layers.append((far, 0.08, 560))

    mh = 220
    mid = Canvas(W, mh)
    yy, _, _ = grids(mh)
    cols = np.arange(W)
    rockg = R("#2c463f", "#36544a", "#436254", "#52725f", "#66856c", "#80997c", "#a2b594")
    forest_c = R("#1e4034", "#264e3d", "#305d45", "#3c6d4e", "#4d8058", "#679663", "#88ae70")
    prof_all = np.full(W, np.inf)
    for i, (hx, top, hw) in enumerate(((196, 26, 74), (262, 70, 48), (500, 70, 60), (610, 110, 40))):
        m_, p_ = karst_peak(mid, hx, top, hw, rockg, ("sjm", i), p=1.9, skirt=1.7, skirt_h=0.4, rough=2.0, gain=1.2,
                            shoulder=0.9, trees=forest_c, tree_frac=0.6, ledges=1.0, base=mh + 30)
        prof_all = np.minimum(prof_all, p_)
    fprof = np.round(np.minimum(np.maximum(prof_all + 16 + (pn1("sjf", 40, 3) - 0.5) * 30, prof_all + 4), mh + 5))
    treeline(mid, fprof, forest_c, "sjh", r=2.5, gain=1.1, rows=7, conifer=0.18)
    roof = R("#0f3538", "#1f6c66", "#2e8a7f", "#67d6bd")
    wallc = R("#8f8a78", "#e2dccb", "#f5f0e2")
    stone = R("#6c6a5e", "#8d8a7c", "#aaa697", "#c6c1b0", "#e0dbc9")
    sect_complex(mid, 196, 199, 5, "sj1", roof, wallc, stone, width=176)
    sect_complex(mid, 500, 199, 3, "sj2", roof, wallc, stone, width=104)
    pagoda(mid, 612, int(prof_all[612]) + 3, 5, 9, R("#1f4a44", "#2e6b60", "#5fae99"))
    for y0, t_, sd in ((96, 8, "sjm1"), (136, 10, "sjm2")):
        mist_band(mid, y0, t_, sd, "#f4f1e0", alphas=(0.16, 0.28, 0.4), amp=4, gaps=0.45)
    rt = np.round(200 + (pn1("sjrt", 64, 2) - 0.5) * 2)
    river(mid, rt, np.full(W, mh - 1.0), R("#2a6b68", "#35817a", "#46998d", "#5db1a0", "#86cbb6", "#b9e4d2"),
          "sjriver", bank="#35574c", glint="#e8f6ea", reflect="#3f7466", reflect_rows=2)
    arch_bridge(mid, 352, int(rt[352]) - 5, 44, R("#6c6a5e", "#9a968a", "#c6c1b0", "#e6e1d0"), rise=7)
    layers.append((mid, 0.18, 620))

    near = Canvas(W, 200)
    yy, _, _ = grids(200)
    pine_c = R("#15322a", "#1c4033", "#254f3c", "#305f45", "#3e714f", "#52855b")
    trunk = R("#231c17", "#352a21", "#4a3b2d", "#62503c")
    pine(near, 60, 160, 118, pine_c, trunk, "sjnp1", lean=0.6, pads=7, pad_w=16)
    pine(near, 470, 160, 92, pine_c, trunk, "sjnp2", lean=-0.5, pads=6, pad_w=14)
    for i, (bx, rx, ry) in enumerate(((150, 20, 12), (560, 26, 16))):
        rock_blob(near, bx, 162, rx, ry, R("#3b4543", "#4e5a57", "#65716c", "#7f8a83", "#9ba49b", "#b8bfb4"), ("sjr", i),
                  moss=R("#3d6b45", "#5a8a55"))
    m, prof = ground_bank(near, 160, "sjbank", R("#1c2a24", "#23342b", "#2b3f33", "#35493b", "#415843", "#50694d"),
                          amp=1.5, tufts=R("#3e6a48", "#4d7c52", "#62905e"))
    balustrade(near, 176, R("#7f7c70", "#b6b2a4", "#d8d4c6", "#f0ede2"), "sjbal", post_gap=32, rail_h=12)
    layers.append((near, 0.32, 720))
    return dict(sky="#86b3b8", horizon="#f1e2ae", layers=layers)


# =============================================================== scene: cloud sect monastery on a cliff
def sect_cloud():
    layers = []
    sky = sky_layer([(0.0, "#5f91bd"), (0.3, "#8db3d3"), (0.55, "#c3d8e8"), (0.72, "#e4eef4"), (1.0, "#eef4f7")])
    for i, (cx, y, ln) in enumerate(((150, 50, 160), (420, 80, 200), (580, 34, 110), (300, 130, 140))):
        streak(sky, cx, y, ln, R("#a9c6de", "#d6e5f0", "#f6fafc"), ("scs", i), rows=2)
    layers.append((sky, 0.0, 720))

    fh = 220
    far = Canvas(W, fh)
    yy, _, _ = grids(fh)
    back = R("#8ba5bf", "#96aec6", "#a3b9ce", "#b3c5d7", "#c6d4e1", "#dde6ee")
    for i, (cx, top, hw) in enumerate(gen_peaks("scb", 7, 40, 100, 24, 40)):
        karst_peak(far, cx, top, hw, back, ("scb", i), p=rng("scbp", i).uniform(1.6, 2.6), rough=1.8, gain=1.0,
                   crevice=0.8)
    base_fade(far, 120, 186, "#eef4f7", steps=3)
    cloud_bank(far, 184, "sccb0", R("#a8bfd2", "#c0d1df", "#d6e2eb", "#e9f0f5", "#f7fafc", "#ffffff"), r_lo=5, r_hi=12,
               rows=2, row_gap=12, amp=5, fill_below=True)
    layers.append((far, 0.08, 560))

    mh = 260
    mid = Canvas(W, mh)
    yy, xx, _ = grids(mh)
    cols = np.arange(W)
    stone = R("#5d6670", "#707a83", "#848e96", "#99a2a8", "#b0b7bb", "#c9ced0", "#e2e5e4")
    cliff = wall_mass(mh, 100, 340, 22, "scc", jag=9, round_r=40, crest_amp=16, taper=46)
    cliff |= wall_mass(mh, 462, 568, 70, "scc2", jag=7, round_r=26, crest_amp=10, taper=22)
    cliff_face(mid, cliff, stone, "sccf", flute=6, ledges=0.5, shrub=R("#2b4a44", "#355a50", "#41695a", "#4f7864",
                                                                        "#62896f"), strata="#6d767e", gain=1.1)
    crest = np.where(cliff.any(axis=0), np.argmax(cliff, axis=0), mh + 5).astype(float)
    pine_c = R("#1a352f", "#21433a", "#2a5244", "#34614d", "#437257", "#568663")
    trunk = R("#2a2420", "#3d342c", "#554739", "#6e5d49")
    roof = R("#1c262b", "#2c3a42", "#465860", "#6f8791")
    wallc = R("#8c8a82", "#e4e1d8", "#f7f5ee")
    # halls on ledges cut into the cliff, joined by zig-zag stairs
    spots = [(150, 58, 34), (262, 88, 40), (180, 128, 44), (290, 160, 30)]
    for i, (hx, hy, hw) in enumerate(spots):
        ledge = wrect(mh, hx - 4, hy + 1, hx + hw + 4, hy + 3)
        flat(mid, ledge, stone[4])
        flat(mid, top_rim(ledge), stone[6])
        flat(mid, bot_rim(ledge), stone[1])
        hall(mid, hx, hy, hw, 9, 7, roof, wallc, post_col="#6b2a26", tiers=2 if i in (0, 2) else 1)
    for (a, b) in ((spots[0], spots[1]), (spots[1], spots[2]), (spots[2], spots[3])):
        lower, upper = (a, b) if a[1] > b[1] else (b, a)
        stairs(mid, lower[0] + 4, lower[1] + 2, upper[0] + upper[2] - 4, upper[1] + 2, (stone[1], stone[3], stone[5]),
               width=5)
    pagoda(mid, 515, int(crest[515]) + 2, 5, 10, R("#2c3a42", "#d9d6cc", "#f4f2ea"), windows="#6b2a26")
    for i, (px, pl) in enumerate(((122, 0.9), (318, -0.8))):
        pine(mid, px, int(crest[px % W]) + 3, 30, pine_c, trunk, ("scp", i), lean=pl, pads=4, pad_w=9)
    # river far below, glimpsed through the cloud break
    gap_c, gap_w = 400, 60
    val = Canvas(W, mh)
    flat(val, yy >= 0, "#a9c1d2")
    vp = np.round(206 + (pn1("scv", 20, 2) - 0.5) * 8)
    treeline(val, vp, R("#223e3e", "#2a4b47", "#335850", "#3e6658", "#4c7662"), "scvt", r=1.5, rows=3)
    rv_top = np.round(224 + np.sin(cols / W * 8 * math.pi) * 3)
    rv = (yy >= rv_top[None, :]) & (yy <= rv_top[None, :] + 2)
    flat(val, rv, "#34a893")
    flat(val, rv & top_rim(rv), "#8ae2c9")
    base_fade(val, 196, 216, "#b9cddb", steps=3, m=(yy < 216))
    win = wellipse(mh, gap_c, 222, gap_w, 26) & (pn2(mh, "scwin", 12, 8, 2) > 0.2) & (mid.a == 0)
    mid.rgb[win] = val.rgb[win]
    mid.a[win] = 1.0
    pal_c = R("#9fb6ca", "#b7c9d9", "#cedbe6", "#e3ebf2", "#f3f7fa", "#ffffff")
    cloud_bank(mid, 196, "sccb1", pal_c, r_lo=8, r_hi=16, rows=3, row_gap=16, amp=6,
               skip=lambda x, k: abs(wdx(x, gap_c)) < gap_w * (1.0 - 0.3 * k))
    cloud_bank(mid, 248, "sccb1b", pal_c, r_lo=9, r_hi=18, rows=1, row_gap=14, amp=4, fill_below=True)
    mist_band(mid, 120, 12, "scmm", "#f2f6f9", alphas=(0.16, 0.28, 0.4), amp=4, gaps=0.35)
    layers.append((mid, 0.18, 620))

    near = Canvas(W, 200)
    yy, _, _ = grids(200)
    rockn = R("#3c4550", "#4e5862", "#636d76", "#7a848b", "#949ca1", "#b2b8bb")
    m, p = karst_peak(near, 560, 78, 40, rockn, "scnr", p=3.0, skirt=1.4, rough=1.5, trees=pine_c, shoulder=0.0)
    pine(near, 552, int(p[552]) + 2, 62, pine_c, trunk, "scnp", lean=-0.7, pads=6, pad_w=14)
    cloud_bank(near, 150, "sccb2", R("#a6bccf", "#bccede", "#d2dfe9", "#e6eef4", "#f5f9fb", "#ffffff"), r_lo=10,
               r_hi=24, rows=1, row_gap=22, amp=8, skip=lambda x, k: abs(wdx(x, 180)) < 150)
    dl = wdx(grids(200)[1], 180)
    ledge = (yy >= 151) & (np.abs(dl) < 150 - np.clip(yy - 151, 0, None) ** 1.35 * 0.9
                           - (pn2(200, "scl", 4, 8, 2) - 0.5) * 10)
    rock_mass(near, ledge, R("#4c5660", "#606a73", "#77818a", "#8f989e", "#aab1b5", "#c8cdcf"), "scledge", gain=1.1)
    bal = Canvas(W, 200)
    balustrade(bal, 150, R("#8a8f94", "#c4c8c9", "#e2e4e2", "#f8f8f4"), "scbal", post_gap=28, rail_h=12)
    keep = (bal.a > 0) & (np.abs(dl) < 140)
    near.rgb[keep] = bal.rgb[keep]
    near.a[keep] = 1.0
    cloud_bank(near, 176, "sccb3", R("#a6bccf", "#bccede", "#d2dfe9", "#e6eef4", "#f5f9fb", "#ffffff"), r_lo=10,
               r_hi=22, rows=1, row_gap=20, amp=6, fill_below=True)
    layers.append((near, 0.32, 720))
    return dict(sky="#5f91bd", horizon="#e4eef4", layers=layers)


# =============================================================== scene: interior
# =============================================================== Azure Expanse (Act II)
def floating_island(cv, cx, top, hw, depth, grass, rock, seed, trees=None, fall=None):
    """An island adrift in the sky: a grassy crown over a jagged rock root tapering down."""
    h = cv.h
    yy, xx, _ = grids(h)
    g = rng("isle", seed)
    d = wdx(xx, cx)
    crown = (np.abs(d) <= hw) & (yy >= top) & (yy <= top + 4 + (pn2(h, ("isc", seed), 6, 2, 1) * 2).astype(int))
    # the root: a lumpy downward wedge
    t = np.clip(1.0 - np.abs(d) / max(1.0, hw), 0, 1)
    bottom = top + 3 + depth * (t ** 0.8) * (0.75 + 0.5 * pn2(h, ("isr", seed), 5, 3, 1))
    root = (np.abs(d) <= hw) & (yy > top + 2) & (yy <= bottom)
    v = 2.6 - (yy - top) / max(1.0, depth) * 2.2 - np.clip(d / max(1.0, hw), -1, 1) * 0.8
    paint(cv, root, rock, v, sharp=2.0)
    flat(cv, left_rim(root) & (yy > top + 3), rock[-1])
    paint(cv, crown, grass, np.full((h, W), 2.2) - np.clip(d / max(1.0, hw), -1, 1), sharp=2.0)
    flat(cv, top_rim(crown), grass[-1])
    if trees is not None:
        for k in range(max(1, int(hw // 9))):
            tx = cx - hw + 5 + g.uniform(0, 2 * hw - 10)
            cone(cv, tx, top + 1, int(g.uniform(7, 13)), int(g.uniform(3, 5)), trees, g.uniform(0, 1))
    if fall is not None:  # a thin waterfall spilling off the island's lip, blown to mist as it drops
        fx = int(cx + hw * 0.55)
        ln = depth + 34
        for k in range(6):
            y0, y1 = top + 2 + ln * k / 6.0, top + 2 + ln * (k + 1) / 6.0
            fm = (np.abs(wdx(xx, fx) + k * 0.4) <= (0.6 if k < 3 else 1.2)) & (yy > y0) & (yy <= y1)
            a = 0.95 - k * 0.15
            flat(cv, fm, fall[0], a)
            flat(cv, fm & ((yy + fx) % 5 < 2), fall[1], a * 0.8)
    return root | crown


def storm_plains():
    layers = []
    sky = sky_layer([(0.0, "#1c2440"), (0.22, "#2f3d66"), (0.45, "#56709c"), (0.66, "#9db5d0"), (0.82, "#dde8ef"),
                     (1.0, "#eef2ea")])
    overcast(sky, 40, "spo", R("#1a1f34", "#2c3656", "#6e82aa"), lobe=16, depth=10, top_dark=36)
    for i, (cx, y, ln) in enumerate(((120, 96, 150), (420, 118, 190), (560, 150, 120))):
        streak(sky, cx, y, ln, R("#8095b8", "#b4c6dc", "#e8f0f6"), ("sps", i), rows=2)
    # a far lightning fork dropping out of the cloud deck
    bolt = wline(SKY_H, [(468, 48), (462, 70), (472, 84), (464, 108), (470, 126)], 1)
    flat(sky, bolt, "#f4fbff")
    flat(sky, sh(bolt, 1, 0) & ~bolt, "#9cc4ff", 0.7)
    layers.append((sky, 0.0, 720))

    fh = 220
    far = Canvas(W, fh)
    grass_f = R("#4d6a7a", "#5e7d86", "#6f8f92", "#86a3a2")
    rock_f = R("#3e4a66", "#4c5a78", "#5e6c8a", "#76849e", "#94a2b6")
    for i, (cx, top, hw, dp) in enumerate(((80, 40, 30, 46), (260, 70, 18, 30), (410, 30, 40, 60), (580, 84, 16, 24))):
        floating_island(far, cx, top, hw, dp, grass_f, rock_f, ("spf", i),
                        fall=(C("#dbe8f2"), C("#ffffff")) if i in (0, 2) else None)
    cloud_bank(far, 186, "spcb0", R("#8ea3bd", "#aebfd2", "#c9d6e3", "#e2eaf1", "#f4f8fa", "#ffffff"), r_lo=5, r_hi=12,
               rows=2, row_gap=10, amp=5, fill_below=True)
    layers.append((far, 0.08, 560))

    mh = 180
    mid = Canvas(W, mh)
    # the open plain: long low swells of storm-bleached grass running to the horizon
    prof = hill_profile(104, 7, "spm", cell=220, octaves=2)
    hill_row(mid, prof, R("#3f5a4a", "#4c6a50", "#5d7c56", "#71905e", "#8ba46a", "#a9bc7c"), "spm", gain=0.35, fall=2.2,
             sharp=2.0)
    for k, (y, th) in enumerate(((122, 3), (138, 4), (158, 5))):   # wind-combed bands in the grass
        mist_band(mid, y, th, ("spg", k), "#9fb878", alphas=(0.14, 0.22), amp=2, cell=120, gaps=0.3)
    g = rng("spm_trees")
    for k in range(9):   # lone wind-bent trees and a few copses
        x = int(g.uniform(0, W))
        for j in range(int(g.integers(1, 4))):
            tx = x + j * 5
            cone(mid, tx, int(prof[tx % W]) + 1, int(g.uniform(6, 11)), 2, R("#1f3530", "#2a4438", "#365440", "#46664a"), 1)
    # standing stones on the plain, split by old lightning
    for i, x in enumerate((140, 372, 530)):
        by = int(prof[x % W]) + 2
        stone = wpoly(mh, [(x - 4, by), (x - 3, by - 16 - i * 3), (x + 1, by - 19 - i * 3), (x + 4, by)])
        paint(mid, stone, R("#2c3446", "#3c465c", "#56617a", "#7a86a0"), np.full((mh, W), 2.0), sharp=2)
        flat(mid, left_rim(stone), "#8c98b2")
    layers.append((mid, 0.18, 620))

    near = Canvas(W, 200)
    prof2 = hill_profile(150, 6, "spn", cell=160, octaves=2)
    hill_row(near, prof2, R("#243a2c", "#2e4832", "#3a583a", "#4a6a42", "#5e7e4c", "#76925a"), "spn", gain=0.4, sharp=2.0)
    reeds(near, 0, W, 158, "spnr", R("#4a6a42", "#6a8a52", "#94ae6a"), count=140, hmin=5, hmax=13)
    layers.append((near, 0.32, 720))
    return dict(sky="#1c2440", horizon="#eef2ea", layers=layers)


def sky_port():
    layers = []
    sky = sky_layer([(0.0, "#2b5e8e"), (0.3, "#4f86b4"), (0.55, "#8fb9d8"), (0.75, "#cfe2ee"), (0.9, "#f1f6f7"),
                     (1.0, "#fdf6e6")])
    for i, (cx, y, ln) in enumerate(((80, 70, 180), (300, 40, 140), (520, 96, 210))):
        streak(sky, cx, y, ln, R("#9bbfdc", "#cfe2ee", "#ffffff"), ("sks", i), rows=2)
    disc(sky, 520, 70, 13, R("#f2d9a0", "#fff6d8", "#fffbeb"), halo="#fff2c8")
    layers.append((sky, 0.0, 720))

    fh = 220
    far = Canvas(W, fh)
    grass_f = R("#5a7f84", "#6c9290", "#83a79e", "#a3c2b2")
    rock_f = R("#4a5a78", "#5a6c8a", "#6e809c", "#8a9bb2", "#a9b7c8")
    for i, (cx, top, hw, dp) in enumerate(((40, 60, 26, 40), (200, 90, 20, 30), (360, 50, 34, 52), (520, 76, 22, 34))):
        floating_island(far, cx, top, hw, dp, grass_f, rock_f, ("skf", i), fall=(C("#e4eef5"), C("#ffffff")) if i == 2 else None)
        if i in (0, 2):
            pagoda(far, cx, top + 1, 3 if i == 2 else 2, 12 if i == 2 else 9, R("#243a4a", "#2f4c5c", "#3d6070", "#5a7e8a"),
                   windows="#ffd98a")
    cloud_bank(far, 178, "skcb0", R("#a3bcd2", "#bfd1e1", "#d6e3ee", "#e9f1f6", "#f7fafc", "#ffffff"), r_lo=5, r_hi=12,
               rows=2, row_gap=10, amp=5, fill_below=True)
    layers.append((far, 0.08, 560))

    mh = 180
    mid = Canvas(W, mh)
    # the port's own island: a broad rock shelf with halls, masts and a moored sky-ship
    shelf = floating_island(mid, 320, 70, 250, 70, R("#4c6a5c", "#5a7c64", "#6e906e", "#8aa87e"),
                            R("#344058", "#425070", "#56648a", "#7482a2", "#98a6bf"), "skm")
    for k, (x, tiers) in enumerate(((150, 2), (260, 1), (420, 2), (520, 1))):
        hall(mid, x - 20, 71, 40, 8, 7, R("#1d2c3a", "#2a3e50", "#43607a", "#6a8aa4"), R("#8c8a82", "#d8d4c8", "#f0ece2"),
             post_col="#7a2e28", tiers=tiers, lit="#ffd98a", seed=k)
    # a sky-ship at the dock: hull, mast and a furled sail
    hull = wpoly(mh, [(330, 64), (382, 64), (374, 72), (338, 72)])
    paint(mid, hull, R("#3a2618", "#553824", "#76502f", "#9c6c3f"), np.full((mh, W), 2.0), sharp=2)
    mast = wline(mh, [(356, 64), (356, 36)], 1)
    flat(mid, mast, "#5a3a24")
    sail = wpoly(mh, [(357, 38), (372, 44), (357, 58)])
    paint(mid, sail, R("#b8b0a0", "#d8d0c0", "#f0ead8"), np.full((mh, W), 2.0), sharp=2)
    cloud_bank(mid, 150, "skcb1", R("#98b2c9", "#b2c6d8", "#cddbe6", "#e3ecf2", "#f4f8fa", "#ffffff"), r_lo=8, r_hi=18,
               rows=2, row_gap=16, amp=6, fill_below=True)
    layers.append((mid, 0.18, 620))

    near = Canvas(W, 200)
    cloud_bank(near, 150, "skcb2", R("#a9c0d4", "#c0d2e1", "#d6e3ed", "#e8f0f5", "#f6f9fb", "#ffffff"), r_lo=10, r_hi=22,
               rows=2, row_gap=20, amp=8, fill_below=True)
    layers.append((near, 0.32, 720))
    return dict(sky="#2b5e8e", horizon="#fdf6e6", layers=layers)


def rimefrost():
    """Rimefrost Heights: snow spires under a pale winter sky, frozen pines and deep drifts."""
    layers = []
    sky = sky_layer([(0.0, "#8aa2bd"), (0.3, "#a9bdd2"), (0.55, "#c9d7e4"), (0.75, "#e2eaf1"), (0.9, "#f1f5f8"),
                     (1.0, "#e9eff4")])
    overcast(sky, 36, "rfo", R("#7d92ad", "#91a6be", "#a9bbcf"), lobe=22, depth=12, top_dark=30)
    for i, (cx, y, ln) in enumerate(((140, 90, 160), (430, 70, 190), (560, 120, 120))):
        streak(sky, cx, y, ln, R("#b4c5d6", "#d4dfe9", "#f4f8fb"), ("rfs", i), rows=2)
    layers.append((sky, 0.0, 720))

    fh = 220
    far = Canvas(W, fh)
    back = R("#8ea3bb", "#9db1c6", "#afc0d2", "#c3d1de", "#d9e3ec", "#eef3f8")
    for i, (cx, top, hw) in enumerate(gen_peaks("rfb", 7, 30, 80, 26, 40)):
        karst_peak(far, cx, top, hw, back, ("rfb", i), p=rng("rfbp", i).uniform(1.4, 2.0), rough=2.2, gain=1.2,
                   crevice=1.0, shoulder=0.8)
    base_fade(far, 100, 170, "#eef3f7", steps=3)
    front = R("#4e6680", "#5d7690", "#7189a1", "#8aa0b5", "#a9bccd", "#d2dde8")
    snow = R("#dbe6ef", "#f7fbfd")
    for i, (cx, top, hw) in enumerate(gen_peaks("rff", 5, 10, 60, 26, 38)):
        spire(far, cx, top, hw, front, ("rff", i), snow=snow)
    base_fade(far, 130, 190, "#f1f5f8", steps=4)
    cloud_bank(far, 180, "rfcb0", R("#b3c3d3", "#c7d4e0", "#d9e3ec", "#e9f0f5", "#f7fafc", "#ffffff"), r_lo=5, r_hi=12,
               rows=2, row_gap=10, amp=5, fill_below=True)
    layers.append((far, 0.08, 560))

    mh = 180
    mid = Canvas(W, mh)
    snow_r = R("#9fb2c6", "#b6c6d6", "#cad7e3", "#dde6ee", "#edf2f7", "#fbfdfe")
    prof = hill_profile(92, 14, "rfm", cell=150, octaves=3)
    hill_row(mid, prof, snow_r, "rfm", gain=0.45, fall=1.6, sharp=2.0)
    frost_pine = R("#2a4546", "#355451", "#46655f", "#5f7d77", "#c9d8e0", "#f2f7fa")   # dark needles, snow on the pads
    trunk = R("#2c2622", "#3f362e", "#56493c", "#6e5e4c")
    g = rng("rfm_trees")
    for k in range(10):
        x = int(g.uniform(0, W))
        pine(mid, x, int(prof[x % W]) + 2, int(g.uniform(18, 30)), frost_pine, trunk, ("rfp", k),
             lean=g.uniform(-0.4, 0.4), pads=4, pad_w=7)
    mist_band(mid, 120, 8, "rfmm", "#eef3f7", alphas=(0.2, 0.34), amp=3, gaps=0.25)
    layers.append((mid, 0.18, 620))

    near = Canvas(W, 200)
    prof2 = hill_profile(146, 8, "rfn", cell=110, octaves=2)
    hill_row(near, prof2, R("#8ea3b8", "#a6b8ca", "#bccbd9", "#d2dde7", "#e6edf3", "#f8fbfd"), "rfn", gain=0.5, sharp=2.0)
    for k, x in enumerate((90, 330, 560)):
        pine(near, x, int(prof2[x % W]) + 3, 40 - k * 6, frost_pine, trunk, ("rfnp", k), lean=0.4 if k % 2 else -0.3,
             pads=5, pad_w=11)
    layers.append((near, 0.32, 720))
    return dict(sky="#8aa2bd", horizon="#e9eff4", layers=layers)


def mirror_lake():
    """Mirrorwater Lake: a lake so still it doubles the floating peaks, lotus in the shallows."""
    layers = []
    sky = sky_layer([(0.0, "#5d6fa8"), (0.28, "#8a92c2"), (0.5, "#b8b6d6"), (0.68, "#dcd2e2"), (0.84, "#f1e6e4"),
                     (1.0, "#f6ece2")])
    for i, (cx, y, ln) in enumerate(((110, 70, 180), (380, 50, 150), (560, 100, 170))):
        streak(sky, cx, y, ln, R("#a7a7cf", "#d2cde3", "#faf4f0"), ("mls", i), rows=2)
    disc(sky, 470, 90, 10, R("#e6c9c9", "#f6e4dc", "#fff7ef"), halo="#f6e2dc")
    layers.append((sky, 0.0, 720))

    fh = 220
    far = Canvas(W, fh)
    water_y = 142
    peaks = R("#5c6690", "#6c769e", "#8088ae", "#989fbf", "#b4b8d0", "#d4d4e2")
    for i, (cx, top, hw) in enumerate(gen_peaks("mlp", 5, 30, 80, 22, 34)):
        spire(far, cx, top, hw, peaks, ("mlp", i), base=water_y, snow=R("#dcdbe8", "#f4f2f8"))
    for i, (cx, top, hw, dp) in enumerate(((90, 26, 22, 30), (330, 16, 30, 40), (540, 34, 18, 26))):
        floating_island(far, cx, top, hw, dp, R("#5c7c78", "#6e8e86", "#87a698", "#a8c2b0"),
                        R("#4b557c", "#5b6690", "#707ba4", "#8c95b8", "#aab1cc"), ("mli", i))
    base_fade(far, 110, water_y, "#e9dfe6", steps=3)
    # the mirror: everything above the waterline, flipped into the lake, cooler and a touch darker
    yy, xx, _ = grids(fh)
    lake = yy >= water_y
    src = np.clip(2 * water_y - 1 - yy, 0, fh - 1)
    ref_rgb = far.rgb[src, xx]
    ref_a = far.a[src, xx]
    tint = np.array(C("#7f8fb4"), float)
    base_c = np.array(C("#c9cbe0"), float)
    col = ref_rgb * ref_a[..., None] + base_c * (1 - ref_a[..., None])
    col = col * 0.72 + tint * 0.28
    rip = pn2(fh, "mlrip", 30, 1.2, 2)
    col = col * (1.0 - (rip > 0.72)[..., None] * 0.08) + (rip < 0.18)[..., None] * 18.0
    far.rgb[lake] = np.clip(col[lake], 0, 255)
    far.a[lake] = 1.0
    flat(far, lake & (yy == water_y), "#f3eef4")
    gl = lake & (pn2(fh, "mlgl", 44, 5, 1) > 0.78) & (yy > water_y + 3)
    flat(far, gl, "#fbf7f8", 0.8)
    layers.append((far, 0.08, 560))

    mh = 180
    mid = Canvas(W, mh)
    yy, _, _ = grids(mh)
    # a stone causeway across the shallows with its lanterns, and lotus beds
    shore = np.round(118 + (pn1("mls", 90, 2) - 0.5) * 4)
    water = river(mid, shore, np.full(W, mh - 1.0), R("#56638f", "#6a78a0", "#8290b4", "#9eaac6", "#bcc4d8", "#dde1ec"),
                  "mlw", bank="#e7e6f0", glint="#fbf8fb", reflect="#7a86ad", reflect_rows=2, ripples=0.2)
    cw = wrect(mh, 0, 110, W - 1, 116)
    paint(mid, cw, R("#4c5270", "#62698a", "#8189a6", "#a4abc2"), np.full((mh, W), 2.2), sharp=2)
    flat(mid, top_rim(cw), "#c8cbd9")
    for x in range(20, W, 64):
        post_m = wrect(mh, x, 100, x + 2, 110)
        flat(mid, post_m, "#3e4462")
        flat(mid, wrect(mh, x - 1, 97, x + 3, 100), "#e8b86a")
        flat(mid, wrect(mh, x, 98, x + 2, 99), "#fff0c0")
    for i, (px, py, rx) in enumerate(((70, 140, 40), (300, 152, 54), (520, 136, 36))):
        pool(mid, px, py, rx, 3, R("#2f5a4c", "#3f7460", "#5d9477"), ("mlpad", i))
        g = rng("mllotus", i)
        for k in range(4):
            lx, ly = int(px + g.uniform(-rx * 0.8, rx * 0.8)), int(py + g.uniform(-2, 1))
            flat(mid, wellipse(mh, lx, ly - 2, 2, 1.5), "#e89ab4")
            put(mid, lx, ly - 3, "#fbd6e2")
    layers.append((mid, 0.18, 620))

    near = Canvas(W, 200)
    for i, (x0, x1) in enumerate(((0, 60), (140, 230), (400, 470), (560, 640))):
        reeds(near, x0, x1, 170, ("mlr", i), R("#233a3c", "#2e4a48", "#3b5b55", "#4c6d62", "#628270"),
              heads=R("#4a3a2c", "#6b5640"), hmin=14, hmax=48)
    layers.append((near, 0.32, 720))
    return dict(sky="#5d6fa8", horizon="#f6ece2", layers=layers)

def gale_canyon():
    """Gale Canyons: wind-carved sandstone walls and arches under a racing sky, a rope bridge, kites."""
    layers = []
    sky = sky_layer([(0.0, "#3f78b0"), (0.3, "#6c9ccb"), (0.55, "#a9c7e0"), (0.75, "#e0e6e0"), (0.9, "#f3e6cf"),
                     (1.0, "#efd9b6")])
    for i, (cx, y, ln) in enumerate(((60, 40, 220), (300, 66, 200), (520, 30, 240), (200, 100, 180), (450, 120, 160))):
        streak(sky, cx, y, ln, R("#9ebcd8", "#d6e4ef", "#ffffff"), ("gks", i), rows=2)
    layers.append((sky, 0.0, 720))

    fh = 240
    far = Canvas(W, fh)
    yy, _, _ = grids(fh)
    back = R("#c49a78", "#cda585", "#d6b193", "#dfbea3", "#e8ccb5")
    back_wall = yy >= hill_profile(70, 14, "gkb", cell=90, octaves=3)[None, :]
    cliff_face(far, back_wall, back, "gkb", flute=7, ledges=0.2, gain=0.8)
    base_fade(far, 90, 200, "#f1dcc0", steps=4)
    wall = R("#8a4f34", "#a2603e", "#b87449", "#cc8c5a", "#dca574", "#ecc596")
    for i, (x0, x1, top) in enumerate(((-30, 120, 30), (210, 330, 46), (420, 560, 22))):
        wm = wall_mass(fh, x0 % W, x1 % W, top, ("gkw", i), jag=3, round_r=12, crest_amp=4)
        cliff_face(far, wm, wall, ("gkwf", i), flute=5, ledges=0.5, strata="#7d4630")
    # a natural arch between the first two walls
    arch = wellipse(fh, 170, 104, 64, 36) & ~wellipse(fh, 170, 112, 46, 30) & (yy < 112)
    cliff_face(far, arch, wall, "gkarch", flute=4, ledges=0.0, strata="#7d4630")
    base_fade(far, 160, 236, "#efd6b6", steps=4)
    layers.append((far, 0.08, 560))

    mh = 220
    mid = Canvas(W, mh)
    yy, _, _ = grids(mh)
    wall2 = R("#4a2418", "#5e2f1f", "#743b27", "#8c4c31", "#a8623f", "#c47e55", "#dca173")
    for i, (x0, x1, top) in enumerate(((-120, 140, 10), (390, 560, 24))):
        wm = wall_mass(mh, x0 % W, x1 % W, top, ("gkm", i), jag=5, round_r=16, crest_amp=6)
        cliff_face(mid, wm, wall2, ("gkmf", i), flute=6, ledges=0.7, strata="#4a2418", gain=1.3)
    # the rope bridge slung between the two walls, planks and hand-ropes sagging in the middle
    x0, x1, yb = 140, 390, 70
    pts = [(x0 + (x1 - x0) * t / 40.0, yb + 26 * math.sin(math.pi * t / 40.0)) for t in range(41)]
    deck = wline(mh, pts, 2)
    flat(mid, deck, "#6e4a2c")
    for k in range(0, 41, 2):
        px, py = pts[k]
        flat(mid, wrect(mh, int(px), int(py), int(px), int(py) + 2), "#9a7048")
    rope = wline(mh, [(x, y - 8) for x, y in pts], 1)
    flat(mid, rope, "#c9a877")
    for k in range(0, 41, 5):
        px, py = pts[k]
        flat(mid, wline(mh, [(px, py - 8), (px, py)], 1), "#b8956a")
    # kites riding the wind above the canyon
    for i, (kx, ky) in enumerate(((250, 20), (470, 8), (60, 34))):
        kite = wpoly(mh, [(kx, ky - 6), (kx + 5, ky), (kx, ky + 7), (kx - 5, ky)])
        flat(mid, kite, "#c6313a" if i % 2 == 0 else "#e0b440")
        flat(mid, left_rim(kite), "#f4d88a")
        flat(mid, wline(mh, [(kx, ky + 7), (kx - 6, ky + 14), (kx - 2, ky + 20), (kx - 9, ky + 28)], 1), "#f4e6c8")
    mist_band(mid, 150, 10, "gkmm", "#f3dcc0", alphas=(0.18, 0.3), amp=3, gaps=0.25)
    layers.append((mid, 0.18, 620))

    near = Canvas(W, 200)
    dark = R("#2e150e", "#3d1d13", "#4f2819", "#633421", "#7a432c", "#945939")
    for i, (bx, rx, ry) in enumerate(((60, 44, 40), (330, 26, 16), (560, 40, 44))):
        rock_blob(near, bx, 196, rx, ry, dark, ("gkn", i), facets=4)
    layers.append((near, 0.32, 720))
    return dict(sky="#3f78b0", horizon="#efd9b6", layers=layers)


def nine_peaks():
    """Nine Peaks: the Alliance seat, nine spires crowned with halls and bridges in a gold afternoon."""
    layers = []
    sky = sky_layer([(0.0, "#2f5c94"), (0.3, "#5f89ba"), (0.55, "#a8c0d8"), (0.75, "#eadbc6"), (0.9, "#f7e2bd"),
                     (1.0, "#f4d7a8")])
    for i, (cx, y, ln) in enumerate(((100, 60, 170), (360, 38, 160), (560, 84, 200))):
        streak(sky, cx, y, ln, R("#b7c8dc", "#f0e4d4", "#fffaf0"), ("nps", i), rows=2)
    disc(sky, 120, 100, 12, R("#f0c880", "#fbe2a8", "#fff6d8"), halo="#f8e0b0")
    layers.append((sky, 0.0, 720))

    fh = 230
    far = Canvas(W, fh)
    back = R("#7d8fb0", "#8b9cbb", "#9dacc6", "#b2bfd3", "#cbd4e1", "#e3e8ef")
    for i, (cx, top, hw) in enumerate(gen_peaks("npb", 6, 40, 90, 22, 34)):
        karst_peak(far, cx, top, hw, back, ("npb", i), p=rng("npbp", i).uniform(1.6, 2.4), rough=1.6, gain=1.1)
    base_fade(far, 110, 180, "#f2e4cc", steps=3)
    spire_r = R("#39465f", "#465573", "#58688a", "#6f80a0", "#8c9cb8", "#b4c0d2")
    roof = R("#1d2c3a", "#2a3e50", "#43607a", "#6a8aa4")
    wallc = R("#8c8a82", "#d8d4c8", "#f0ece2")
    peaks = [(40, 30, 16), (110, 12, 18), (185, 40, 15), (250, 6, 20), (320, 34, 16), (390, 18, 18), (455, 44, 14),
             (520, 10, 19), (590, 36, 16)]
    tops = []
    for i, (cx, top, hw) in enumerate(peaks):
        m, prof = spire(far, cx, top, hw, spire_r, ("npf", i), trees=R("#223a3a", "#2c4a46", "#385a52", "#476b5d"))
        ty = int(prof[cx % W])
        tops.append((cx, ty))
        if i % 2 == 0:
            pagoda(far, cx, ty + 1, 3, 10, roof, windows="#ffd98a")
        else:
            hall(far, cx - 10, ty + 2, 20, 5, 5, roof, wallc, post_col="#7a2e28", tiers=1, lit="#ffd98a", seed=i)
    for (ax, ay), (bx, by) in zip(tops[:-1], tops[1:]):
        if abs(bx - ax) < 90:
            mid_y = max(ay, by) + 12
            flat(far, wline(fh, [(ax + 4, ay + 6), ((ax + bx) / 2, mid_y), (bx - 4, by + 6)], 1), "#6a5a44")
    cloud_bank(far, 186, "npcb0", R("#b9c4d2", "#cdd5df", "#e0e5ec", "#efe9e2", "#f9f3ea", "#ffffff"), r_lo=5, r_hi=12,
               rows=2, row_gap=10, amp=5, fill_below=True)
    layers.append((far, 0.08, 560))

    mh = 180
    mid = Canvas(W, mh)
    cloud_bank(mid, 130, "npcb1", R("#aab6c6", "#c3ccd9", "#d9dfe7", "#ece9e4", "#f8f3ec", "#ffffff"), r_lo=8, r_hi=18,
               rows=2, row_gap=16, amp=6, fill_below=True)
    layers.append((mid, 0.18, 620))
    near = Canvas(W, 200)
    cloud_bank(near, 150, "npcb2", R("#b6c1cf", "#cbd3de", "#dee4eb", "#eeebe6", "#f9f5ef", "#ffffff"), r_lo=10, r_hi=22,
               rows=2, row_gap=20, amp=8, fill_below=True)
    layers.append((near, 0.32, 720))
    return dict(sky="#2f5c94", horizon="#f4d7a8", layers=layers)


# =============================================================== Sunscar Desert (Act II)
def dune(cv, cx, top, base, wl, wr, ramp, seed, shade=2, lean=None, fb=None, ripples=0.0, rim=True, edge=True):
    """One transverse dune, wind from the left: a long S-curved windward face and a straight, steep slip face
    on the right. The brink curves from the crest down and back toward the viewer; everything right of it is
    slip face in hue-shifted shadow, darkest along the brink and warmed by reflected light toward the foot.

    ramp dark->light: the first `shade` tones are shadow, the rest sunlit sand. Returns (mask, lit)."""
    h = cv.h
    yy, xx, B = grids(h)
    g = rng("dune", seed)
    n = len(ramp)
    dx = wdx(np.arange(W), cx)
    hgt = max(1.0, base - top)
    tl = np.clip(-dx / wl, 0, 1)
    tr = np.clip(dx / wr, 0, 1)
    prof = np.where(dx < 0, base - hgt * (0.5 + 0.5 * np.cos(np.pi * tl)), base - hgt * (1 - tr) ** 1.25)
    inside = (dx > -wl) & (dx < wr)
    prof = np.where(inside, np.round(prof), np.inf)
    m = (yy >= prof[None, :]) & (yy <= base)
    if not m.any():
        return m, np.zeros_like(m)
    lean = g.uniform(0.1, 0.28) if lean is None else lean
    fb = g.uniform(0.3, 0.9) if fb is None else fb
    rel = np.clip((yy - top) / hgt, 0, 1)
    d2 = wdx(xx, cx)
    brink = -wl * lean * rel ** 0.8 + (wl * lean + wr * fb) * rel ** 3
    shadow = m & (d2 > brink)
    lit = m & ~shadow
    v_top, v_foot = n - 1 - 0.2, shade + 1.0
    v = v_top - rel ** 0.8 * (v_top - v_foot)
    v = v + (lit & sh(shadow, -3, 0) & (rel < 0.85)) * 0.8          # the brink catches the most light
    if ripples:
        pf = np.where(inside, prof, base)[None, :]
        ph = yy - 0.55 * pf + (pn2(h, ("drp", seed), 12, 3, 1) - 0.5) * 3.0
        rip = lit & (np.floor(ph) % 4 == 0) & (yy - pf >= 2) & (rel > 0.12) & ~sh(shadow, -3, 0)
        rip &= pn2(h, ("drg", seed), 16, 2, 1) > 1.0 - ripples
        v = v - rip * 0.9
    vs = 0.2 + np.clip((d2 - brink) / (0.3 * wr + 3), 0, 1) * 0.75 + rel * 0.35
    paint(cv, m, ramp, np.where(shadow, np.minimum(vs, shade - 0.01), v), sharp=4)
    if rim:
        flat(cv, top_rim(m) & lit, ramp[-1])
        flat(cv, lit & sh(shadow, -1, 0) & (rel < 0.9), ramp[-1])
    if edge:
        flat(cv, shadow & sh(lit, 1, 0) & (rel < 0.6), ramp[0])
    return m, lit


def dune_row(cv, base_y, seed, ramp, n, top_lo, top_hi, w_lo, w_hi, shade=2, ripples=0.0, amp=1.5, edge=True,
             lean=None):
    """A rank of dunes standing on a gently rolling sand flat at base_y, filled down to the canvas foot.
    Returns (ground profile, sunlit mask, crests [(x, y)])."""
    h = cv.h
    yy, _, _ = grids(h)
    g = rng("drow", seed)
    ground = hill_profile(base_y, amp, ("drg", seed), cell=120, octaves=2)
    gm = yy >= ground[None, :]
    flat(cv, gm, ramp[shade + 1])
    flat(cv, top_rim(gm), ramp[min(len(ramp) - 1, shade + 2)])
    lit = np.zeros((h, W), bool)
    crests = []
    for i, (cx, top, hw) in enumerate(gen_peaks(("drow", seed), n, top_lo, top_hi, w_lo, w_hi)):
        m, l = dune(cv, cx, top, base_y + 2, hw * g.uniform(1.1, 1.6), hw * g.uniform(0.4, 0.6), ramp, (seed, i),
                    shade=shade, ripples=ripples, edge=edge, lean=lean)
        lit |= l
        col = m[:, int(round(cx)) % W]
        crests.append((cx, int(np.argmax(col)) if col.any() else top))
    return ground, lit, crests


def heat_shimmer(cv, y, rows, seed, col, alphas=(0.32, 0.18), cell=28, density=0.55):
    """Mirage shimmer: a stack of broken 1px haze lines whose dashes waver from row to row (densest in the core)."""
    h = cv.h
    base = pn1(("hsh", seed), cell, 2)
    fine = pn1(("hsf", seed), 5, 1)
    ph = rng("hsp", seed).uniform(0, 6.28)
    for r in range(rows):
        yr = y + r
        if not 0 <= yr < h:
            continue
        k = abs(r - (rows - 1) / 2.0) / max(1.0, rows / 2.0)
        s = np.roll(base, int(round(math.sin(r * 1.7 + ph) * 5))) * 0.7 + np.roll(fine, r * 3) * 0.3
        m = np.zeros((h, W), bool)
        m[yr] = s > (1.0 - density) + k * 0.22
        flat(cv, m, col, alphas[r % len(alphas)])


def spindrift(cv, x, y, length, col, seed, rise=0.06, alphas=(0.7, 0.45, 0.22)):
    """Sand smoking off a dune crest: a thin wisp trailing downwind (right), fraying and fading."""
    h = cv.h
    yy, xx, _ = grids(h)
    t = wdx(xx, x) / float(length)
    ph = rng("spd", seed).uniform(0, 6.28)
    cy = y - t * length * rise + np.sin(t * 6 + ph) * 0.8 + t ** 2 * 3
    thick = 2.4 * (1 - t) + 0.6
    m = (t >= 0) & (t <= 1) & (np.abs(yy - cy) <= thick / 2 + 0.01)
    m &= pn2(h, ("spb", seed), 6, 1.5, 1) > 0.25 + t * 0.4
    L = len(alphas)
    for k, a in enumerate(alphas):
        flat(cv, m & (t >= k / L) & (t < (k + 1) / L), col, a)


def glass_glints(cv, region, count, seed, core, arm, big_every=3):
    """Sun-glints of desert glass spread over `region`: one bright pixel each, every few with a tiny cross."""
    g = rng("glint", seed)
    ys, xs = np.nonzero(region)
    for i in range(count):
        sel = (xs >= i * W / count + 4) & (xs < (i + 1) * W / count - 4)
        if not sel.any():
            continue
        j = int(g.choice(np.nonzero(sel)[0]))
        x, y = int(xs[j]), int(ys[j])
        if i % big_every == 0:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                put(cv, x + dx, y + dy, arm)
        put(cv, x, y, core)


def mesa(cv, cx, top, base, hw, ramp, seed, cap_h=5, cliff=0.5, flare=1.9, grooves=3, waist=0.0, tafoni=3):
    """Wind-carved sandstone mesa: an overhanging caprock over a sheer cliff band of uneven strata, scored by
    wind grooves and pocked with tafoni hollows, then a gullied talus apron flaring to the foot. waist > 0
    pinches the cliff band into a pedestal-rock stem. Lit from the left. ramp dark->light (>= 6)."""
    h = cv.h
    yy, xx, B = grids(h)
    g = rng("mesa", seed)
    n = len(ramp)
    hgt = max(1.0, base - top)
    ry = yy - top
    rel = np.clip(ry / hgt, 0, 1)
    tal = np.clip((rel - cliff) / max(0.05, 1 - cliff), 0, 1)
    half = hw * (1 + (flare - 1) * tal ** 1.5)
    if waist:
        half = half * (1 - waist * np.exp(-((rel - cliff * 0.75) / (cliff * 0.4)) ** 2))
    groove = np.zeros((h, W))
    for gy in g.uniform(0.25, 0.9, grooves):
        groove += 1.6 * np.exp(-((ry - gy * cliff * hgt) / 1.3) ** 2)
    capm = ry < cap_h
    under = (ry >= cap_h) & (ry < cap_h + 2)
    half = half - groove - under * 1.3 + capm * 1.2
    d = wdx(xx, cx)
    amp = 1.2 + tal * 2.5
    jl = (pn2(h, ("mjl", seed), 3, 5, 2) - 0.5) * 2 * amp
    jr = (pn2(h, ("mjr", seed), 3, 5, 2) - 0.5) * 2 * amp
    dcol = np.abs(wdx(np.arange(W), cx))
    crest = top + np.round((pn1(("mtop", seed), 10, 2) - 0.5) * 1.6) + np.clip(dcol - (hw + 1.2 - 2.5), 0, 3) ** 1.3
    m = (d >= -half + jl) & (d <= half + jr) & (yy >= crest[None, :]) & (yy <= base)
    m = despeck(m)
    u = row_u_local(m)
    # uneven strata: bands 2-6 px thick, each with its own tone offset
    bounds = np.cumsum(g.integers(2, 7, 40))
    offs = g.choice([0.55, -0.25, 0.3, -0.55, 0.1, 0.45, -0.1], 41)
    wob = np.round((pn1(("mst", seed), 60, 2) - 0.5) * 3)[None, :]
    strata = offs[np.searchsorted(bounds, np.clip(ry + wob, 0, None))]
    gully = (pn2(h, ("mgl", seed), 2, 9, 1) - 0.5) * 2
    v = (n - 1) * 0.5 + (0.5 - u) * 2.4
    flute = (pn1(("mfl", seed), 7, 2) - 0.5)[None, :] * 1.0
    v = v + np.where(tal > 0, 0.45 + gully * 0.9 - (0.5 - u) * 0.8, strata + flute)
    v = v - under * 1.6 - groove * 0.6 + capm * 0.7
    paint(cv, m, ramp, v, sharp=3.5)
    flat(cv, top_rim(m) & (u < 0.85), ramp[-1])
    flat(cv, left_rim(m) & ~top_rim(m) & ~under & (tal < 0.6), ramp[-2])
    flat(cv, right_rim(m) & ~top_rim(m), ramp[0])
    for k in range(tafoni):                                         # wind-scooped hollows in the cliff band
        ty = top + cap_h + 3 + g.uniform(0, max(1.0, cliff * hgt - cap_h - 5))
        tx = cx + g.uniform(-0.6, 0.5) * hw
        rx, ryy = g.uniform(1.6, 3.4), g.uniform(1.2, 2.4)
        hol = wellipse(h, tx, ty, rx, ryy) & m & ~sh(~m, 1, 0) & ~sh(~m, -1, 0)
        flat(cv, hol, ramp[1])
        flat(cv, hol & ~sh(hol, 0, 1) | hol & ~sh(hol, 1, 0), ramp[0])
        flat(cv, sh(bot_rim(hol), 0, 1) & m & ~hol, ramp[-2])
    return m


def tomb_gate(cv, cx, by, w, ht, pal, door, tiers=3):
    """Squat stepped portal: a battered gate block under a corbelled, stepped crown, a stepped doorway and a
    sun boss above it. by = its buried foot. pal dark->light (>= 4)."""
    h = cv.h
    yy, xx, _ = grids(h)
    d = wdx(xx, cx) + 0.5
    ad = np.abs(d)
    body_h = int(ht * 0.6)
    yb = by - body_h
    rel = np.clip((yy - yb) / max(1, body_h), 0, 1)
    body = (ad <= w / 2.0 - 2.0 * (1 - rel)) & (yy >= yb) & (yy <= by)
    th = max(2, int((ht - body_h) / tiers))
    crown = np.zeros((h, W), bool)
    rims = np.zeros((h, W), bool)
    for k in range(tiers):
        y1 = yb - 1 - k * th
        tk = (ad <= w / 2.0 - 3 - k * w * 0.12) & (yy <= y1) & (yy > y1 - th)
        crown |= tk
        rims |= top_rim(tk)
    notch = (np.abs(d - w * 0.16) < 2.5) & (yy <= yb - th * (tiers - 1))   # a fallen block in the top tier
    crown &= ~notch
    rims &= crown
    m = body | crown
    flat(cv, m, pal[2])
    flat(cv, m & (d < -w * 0.34), pal[3])                          # sunlit return of the left pylon
    flat(cv, rims | top_rim(body), pal[3])
    flat(cv, (bot_rim(crown) & ~body) | (sh(top_rim(body), 0, 1) & body), pal[1])
    flat(cv, right_rim(m), pal[0])
    for sx in (-1, 1):                                             # pilasters flanking the door
        flat(cv, body & (np.abs(d - sx * w * 0.25) < 1.0) & (yy > yb + 2), pal[1])
    dw = w * 0.17
    yd = yb + 6
    dm = ((ad <= dw) & (yy >= yd)) | ((ad <= dw - 2) & (yy >= yd - 2)) | ((ad <= dw - 4) & (yy >= yd - 4))
    dm &= yy <= by
    flat(cv, dm, door)
    flat(cv, dm & sh(~dm, -1, 0) & (d > 0), pal[1])                # the right jamb catches a little light
    boss = wellipse(h, cx, yb - 1 - th * (tiers - 0.5), 1.6, 1.3) & crown
    flat(cv, boss, pal[3])
    return m


def sunscar():
    """Sunscar Desert: dune seas under a merciless white sun, a wind-carved mesa and a sand-buried tomb gate."""
    layers = []
    haze = "#f2dcc4"
    sky = sky_layer([(0.0, "#a9bccb"), (0.16, "#c2cfd6"), (0.3, "#dde1da"), (0.38, "#eee8d6"), (0.44, "#f8ebca"),
                     (0.52, "#f6dfb6"), (0.7, "#f1d4a6"), (1.0, "#ecc998")])
    yy, xx, _ = grids(SKY_H)
    sx, sy, sr = 190, 64, 25
    for s_, a in ((6.2, 0.04), (4.8, 0.05), (3.6, 0.07), (2.6, 0.1), (1.85, 0.15), (1.35, 0.24)):
        flat(sky, wellipse(SKY_H, sx, sy, sr * s_, sr * s_), "#fff8e4", a)
    sm = wellipse(SKY_H, sx, sy, sr, sr)
    flat(sky, sm, "#fffbee")
    ring = sm & ~(sh(sm, 1, 0) & sh(sm, -1, 0) & sh(sm, 0, 1) & sh(sm, 0, -1))
    dd = wdx(xx, sx) + (yy - sy)
    flat(sky, sm & ~wellipse(SKY_H, sx - 1, sy - 1, sr - 1, sr - 1) & (dd > 4), "#fff0c4")
    flat(sky, ring & (dd > -12), "#ffe29a")
    flat(sky, ring & (dd < -20), "#ffffff")
    for i, (cx, y, ln) in enumerate(((420, 40, 170), (40, 96, 150), (330, 120, 230), (560, 132, 190), (130, 140, 160))):
        streak(sky, cx, y, ln, R("#e2cdb6", "#eee0cc", "#fbf3e4") if i < 2 else R("#e8cdb0", "#f1dcc2", "#f9ead6"),
               ("sss", i), rows=2)
    layers.append((sky, 0.0, 720))

    # ---------------- far: ranks of long dune ridges receding from warm ochre into dusty violet
    fh = 200
    far = Canvas(W, fh)
    yy, _, _ = grids(fh)
    ranks = [
        (70, R("#b39fb4", "#bea9b8", "#ccb8bd", "#d7c4c2", "#e2d1c8"), 7, 50, 62, 34, 58),
        (82, R("#ad8fa2", "#b99aa7", "#ccaca9", "#d9bcae", "#e5cab4"), 6, 62, 72, 36, 60),
        (95, R("#a8808b", "#b88e92", "#cfa496", "#dcb59c", "#e8c5a5", "#f0d3b1"), 6, 72, 84, 38, 64),
    ]
    for k, (by, ramp, n, tlo, thi, wlo, whi) in enumerate(ranks):
        dune_row(far, by, ("sfr", k), ramp, n, tlo, thi, wlo, whi, shade=2, amp=1.2, edge=False)
        base_fade(far, by - 7, by + 5, haze, steps=3)
        heat_shimmer(far, by - 3, 5, ("sfh", k), "#efe8dc" if k == 0 else haze, alphas=(0.4, 0.22))
    base_fade(far, 100, 130, haze, steps=3)
    layers.append((far, 0.08, 560))

    # ---------------- mid: a hazed sand plain with the buried tomb gate, the mesa and a pedestal rock, dunes
    mh = 200
    mid = Canvas(W, mh)
    yy, _, _ = grids(mh)
    plain = R("#b8989f", "#c6a6a6", "#d6b8a8", "#e2c6ad", "#ebd2b6")
    dune_row(mid, 72, "smp", plain, 5, 64, 70, 30, 50, shade=2, amp=1.0, edge=False)
    base_fade(mid, 64, 88, haze, steps=3)
    gate_x = 520
    tomb_gate(mid, gate_x, 80, 46, 34, R("#8f7385", "#a08292", "#b4959e", "#c8aaa8"), "#6e5669")
    drift = R("#bf9ea2", "#cbaba8", "#dbbfab", "#e5cbb0", "#edd5b8")
    dune(mid, gate_x - 8, 70, 82, 44, 30, drift, "sgd0", shade=2, lean=0.08, fb=0.6, edge=False)
    dune(mid, gate_x + 32, 73, 82, 20, 12, drift, "sgd1", shade=2, edge=False)
    base_fade(mid, 74, 90, haze, steps=3, m=(mid.a > 0) & (yy >= 74))
    heat_shimmer(mid, 75, 6, "smh0", haze, alphas=(0.36, 0.2))
    dune_row(mid, 90, "smp2", hazed(plain, haze, 0.45), 4, 83, 87, 60, 90, shade=2, amp=1.0, edge=False)
    base_fade(mid, 86, 100, haze, steps=3, m=(mid.a > 0) & (yy >= 84))
    rock = hazed(R("#6c4150", "#814b55", "#9a5a5a", "#b36c5f", "#c98466", "#da9e74", "#e8b889"), haze, 0.15)
    bench = mesa(mid, 150, 52, 114, 24, hazed(rock, haze, 0.15), "sbench", cap_h=4, cliff=0.35, flare=1.8, grooves=1,
                 tafoni=0)
    mm = mesa(mid, 100, 30, 114, 42, rock, "smesa", cap_h=6, cliff=0.42, flare=1.6, grooves=3, tafoni=0)
    pm = mesa(mid, 268, 62, 114, 8, rock, "sped", cap_h=5, cliff=0.62, flare=2.3, grooves=1, waist=0.42, tafoni=0)
    haze_fade(mid, mm | pm | bench, haze, np.clip((yy - 66) / 44.0, 0, 1) * 0.5, steps=4, sharp=5)
    heat_shimmer(mid, 98, 5, "smh1", haze, alphas=(0.3, 0.16))
    mdr = R("#b98b8e", "#c79a93", "#dbab8e", "#e5ba93", "#eec99c", "#f6d9ab")
    ground, lit, crests = dune_row(mid, 118, "smd", mdr, 5, 94, 106, 40, 70, shade=2, ripples=0.35)
    for i, (x, y) in enumerate(sorted(crests, key=lambda c: c[1])[:2]):
        spindrift(mid, x + 1, y - 1, 64, "#fff4e0", ("smsp", i))
    glass_glints(mid, lit & (yy < 114) & (yy > 104), 3, "smgl", "#ffffff", "#c4eedd")
    mist_band(mid, 110, 4, "smds", "#f8e6c6", alphas=(0.18, 0.3), amp=2, cell=120, gaps=0.35)
    layers.append((mid, 0.18, 620))

    # ---------------- near: big calm dunes, faded to low contrast where the room's sand meets them
    near = Canvas(W, 200)
    yy, _, _ = grids(200)
    ndr = R("#cfa08f", "#d8ab95", "#e3b893", "#ebc499", "#f2d0a3", "#f8ddb3")
    ground, lit, crests = dune_row(near, 120, "snd", ndr, 3, 70, 90, 90, 130, shade=2, ripples=0.5)
    glass_glints(near, lit & (yy < 100), 4, "sngl", "#ffffff", "#c4eedd", big_every=2)
    for i, (x, y) in enumerate(crests[:2]):
        spindrift(near, x + 1, y - 1, 96, "#fff6e4", ("snsp", i))
    base_fade(near, 96, 130, "#e7c498", steps=3)
    layers.append((near, 0.32, 720))
    return dict(sky="#a9bccb", horizon="#f8ebca", layers=layers)


# =============================================================== Tomb of Sunscar (Act II interior)
_FIGS = {
    "walk": ["..rr..", "..rrr.", ".rrr..", ".rrrr.", ".rr..r", ".rrr..", ".r.r..", "r...r."],
    "staff": ["..rr.g", "..rrrg", ".rrr.g", ".rrrrg", ".rr..g", ".rrr.g", ".r.r.g", "r...rg"],
    "disc": [".ggg..", "ggggg.", ".ggg..", "..r...", "..rr..", "..rrr.", ".rrr..", ".rrrr.", ".rr..r", ".rrr..",
             ".r.r..", "r...r."],
    "jar": ["..gg..", ".gggg.", "..rr..", "..rrr.", ".rrr..", ".rrrr.", ".rr..r", ".rrr..", ".r.r..", "r...r."],
}


def ashlar(cv, m, pal, seed, course=8, joint=20):
    """Dressed sandstone blocks in flat tones: staggered courses, each block its own shade, dark mortar and a
    lit top arris. pal dark->light (>= 5); W must be a multiple of `joint` so the courses tile."""
    h = cv.h
    yy, xx, _ = grids(h)
    g = rng("ashlar", seed)
    n = len(pal)
    row = yy // course
    off = (row * (joint // 2 + 3)) % joint
    ncols = W // joint
    tone = g.choice([1, 2, 2, 2, 3, 3, 3, 4], size=(h // course + 2, ncols))
    bx = (xx + off) % W
    idx = tone[row, bx // joint]
    idx = np.where(yy % course == 1, np.minimum(idx + 1, n - 1), idx)
    idx = np.where((yy % course == 0) | (bx % joint == 0), 0, idx)
    chip = (pn2(h, ("ashc", seed), 2, 2, 1) > 0.8) & (idx > 0)
    idx = np.where(chip, np.maximum(idx - 1, 1), idx)
    cv.fill_idx(m, idx, pal)
    return m


def relief_frieze(cv, y0, y1, band, red, gold, seed, group=80, clip=None, fade=0.78):
    """Carved relief band y0..y1: processions of small figures walking toward sun discs, in faded vermilion and
    gold, chipped by age. band = (dark, mid, light). Pattern repeats every `group` px (640 / group integral)."""
    h = cv.h
    yy, xx, _ = grids(h)
    m = (yy >= y0) & (yy <= y1)
    if clip is not None:
        m &= clip
    flat(cv, m, band[1])
    flat(cv, top_rim(m), band[2])
    flat(cv, m & ((yy == y0 + 1) | (yy == y1 - 1)), band[0])
    flat(cv, bot_rim(m), band[0])
    chip = pn2(h, ("frc", seed), 3, 2, 1) > 0.7
    art = np.zeros((h, W), bool)
    gart = np.zeros((h, W), bool)
    foot = y1 - 2
    kinds = ("staff", "walk", "disc", "walk", "jar")
    for gx in range(0, W, group):
        for k, kind in enumerate(kinds):
            spr = _FIGS[kind]
            fx = gx + 4 + k * 11
            for r, row in enumerate(spr):
                for c, ch in enumerate(row):
                    y = foot - len(spr) + 1 + r
                    if ch != "." and y0 + 2 <= y <= y1 - 2:
                        (gart if ch == "g" else art)[y, (fx + c) % W] = True
        sx, sy = gx + group - 14, (y0 + y1) / 2.0
        gart |= wellipse(h, sx, sy, 2.6, 2.6)
        for a in range(8):
            ang = a * math.pi / 4
            gart[int(round(sy + math.sin(ang) * 4.6)), int(round(sx + math.cos(ang) * 4.6)) % W] = True
    flat(cv, art & m & ~chip, red, fade)
    flat(cv, gart & m & ~chip, gold, fade)
    flat(cv, m & chip & (pn2(h, ("frc2", seed), 1.5, 1.5, 1) > 0.8), band[0])
    return m


def tomb_pillar(cv, cx, top, by, hw, ramp, seed, courses=14, band=None):
    """Massive square sandstone pillar: stepped capital and plinth, sunlit left return, block courses, chipped
    arrises, optional painted band = (y0, y1, red, gold). ramp dark->light."""
    h = cv.h
    yy, xx, B = grids(h)
    n = len(ramp)
    d = wdx(xx, cx) + 0.5
    ad = np.abs(d)
    chip = pn2(h, ("tpc", seed), 2, 3, 1) > 0.8
    shaft = (ad <= hw - chip) & (yy >= top) & (yy <= by)
    cap = ((ad <= hw + 4) & (yy >= top) & (yy < top + 3)) | ((ad <= hw + 2) & (yy >= top + 3) & (yy < top + 6))
    plinth = ((ad <= hw + 4) & (yy > by - 4) & (yy <= by)) | ((ad <= hw + 2) & (yy > by - 7) & (yy <= by - 4))
    m = shaft | cap | plinth
    rel = np.clip((d + hw + 4) / (2 * hw + 8), 0, 1)
    v = (n - 1) * 0.5 - (rel - 0.5) * 1.6 + (d < -hw * 0.5) * 1.0
    joints = shaft & ((yy - top) % courses == 0) & (yy > top + 6) & (yy < by - 7)
    v = v - joints * 1.3 + (sh(joints, 0, 1) & shaft) * 0.6
    paint(cv, m, ramp, v, sharp=6)
    for part in (cap, plinth):
        flat(cv, top_rim(part) & (d < hw * 0.6), ramp[-1])
        flat(cv, bot_rim(part), ramp[0])
    flat(cv, right_rim(m), ramp[0])
    flat(cv, left_rim(shaft) & ~cap & ~plinth, ramp[-2])
    if band is not None:
        y0, y1, red, gold = band
        bm = shaft & (yy >= y0) & (yy <= y1)
        flat(cv, bm, red, 0.8)
        flat(cv, bm & ((yy == y0) | (yy == y1)), gold, 0.8)
        boss = wellipse(h, cx + hw * 0.15, (y0 + y1) / 2.0, 2.2, 2.2)
        flat(cv, boss & bm & ~chip, gold, 0.85)
        flat(cv, bm & (d < -hw * 0.5), ramp[-2], 0.35)
    return m


def brazier(cv, x, by, pal, flame, glow):
    """Bronze fire bowl on a tripod with a small flame and a stepped warm glow. pal (dark, mid, light),
    flame (deep, mid, core); by = foot row."""
    h = cv.h
    for (rx, ry, a) in ((15, 11, 0.06), (10, 7.5, 0.1), (6, 4.5, 0.16)):
        flat(cv, wellipse(h, x, by - 11, rx, ry), glow, a)
    legs = wline(h, [(x - 3, by), (x - 1, by - 6)]) | wline(h, [(x + 3, by), (x + 1, by - 6)])
    legs |= wrect(h, x, by - 6, x, by - 3)
    flat(cv, legs, pal[0])
    bowl = wrect(h, x - 3, by - 8, x + 3, by - 7) | wrect(h, x - 4, by - 9, x + 4, by - 9)
    flat(cv, bowl, pal[1])
    flat(cv, wrect(h, x - 4, by - 9, x + 1, by - 9), pal[2])
    for (fx, fy, c) in ((-2, 10, 0), (-1, 10, 1), (0, 10, 2), (1, 10, 1), (2, 10, 0), (-1, 11, 1), (0, 11, 2),
                        (1, 11, 0), (0, 12, 1), (-1, 13, 0), (0, 14, 0)):
        put(cv, x + fx, by - fy, flame[c])


def sand_fall(cv, x, y0, pal, seed, width=1, below=150):
    """Thin stream of sand pouring from a ceiling crack: a broken dotted thread that frays near the floor,
    with a small cone of sand where it lands on whatever is already painted below row `below`.
    pal (dark, mid, light)."""
    h = cv.h
    yy, xx, _ = grids(h)
    colm = cv.a[below:, int(x) % W] > 0
    y1 = below + int(np.argmax(colm)) - 1 if colm.any() else h - 4
    d = wdx(xx, x)
    t = (yy - y0) / max(1.0, y1 - y0)
    m = (d >= -(width // 2)) & (d <= (width - 1) // 2 + (t > 0.75)) & (yy >= y0) & (yy <= y1)
    m &= pn2(h, ("sfl", seed), 1, 4, 1) > 0.22 + np.clip(t - 0.6, 0, 1) * 0.6
    flat(cv, m, pal[1])
    flat(cv, m & ((yy + x) % 5 < 2), pal[2])
    g = rng("sfsp", seed)
    for k in range(10):
        put(cv, x + g.integers(-3, 4), y1 - g.integers(0, 6), pal[1], 0.7)
    cone = wpoly(h, [(x - 7, y1 + 3), (x - 1, y1), (x + 1, y1), (x + 7, y1 + 3)])
    flat(cv, cone, pal[1])
    flat(cv, cone & (d < 0), pal[2])
    flat(cv, top_rim(cone) & (d <= 1), pal[2])


def light_field(h, pools=(), beams=(), ambient=None):
    """Light strength per pixel: elliptical pools [(x, y, rx, ry, s)], slanted beams
    [(cx, slope, half_width, s, y0, y1)] that lean right going down like light_shafts, and an optional
    horizontal ambient band (y0, y1, s) with soft 12px edges."""
    yy, xx, _ = grids(h)
    lit = np.zeros((h, W))
    if ambient is not None:
        a0, a1, s_ = ambient
        lit = s_ * np.clip((yy - a0) / 12.0, 0, 1) * np.clip((a1 - yy) / 12.0, 0, 1)
    for (lx, ly, rx, ry, s_) in pools:
        dd = np.sqrt((wdx(xx, lx) / rx) ** 2 + ((yy - ly) / ry) ** 2)
        lit = np.maximum(lit, s_ * np.clip(1 - dd, 0, 1))
    for (cx, slope, r, s_, y0, y1) in beams:
        dd = np.abs(wdx(xx - yy * slope, cx)) / r
        ends = np.clip((yy - y0) / 12.0, 0, 1) * np.clip((y1 - yy) / 40.0, 0, 1)
        lit = np.maximum(lit, s_ * np.clip(1 - dd, 0, 1) ** 0.7 * ends)
    return lit


def dim(cv, lit, dark, base=0.6, top=90, top_t=0.95, floor=None, steps=4):
    """Sink the painted layer toward `dark` by (base - lit): darkness gathering over the top `top` rows and,
    optionally, toward the floor (y0, y1, t). Flat dithered steps."""
    yy, xx, _ = grids(cv.h)
    t = np.clip(base - lit, 0, 1)
    t = np.maximum(t, np.clip(1 - yy / float(top), 0, 1) * top_t)
    if floor is not None:
        f0, f1, ft = floor
        t = np.maximum(t, np.clip((yy - f0) / max(1.0, f1 - f0), 0, 1) * ft)
    haze_fade(cv, cv.a > 0, dark, t, steps=steps, sharp=6.0)


def sunscar_tomb():
    """Tomb of Sunscar: a dim sandstone burial palace, painted friezes, braziers, a shaft of dusty sun, sand falls."""
    layers = []
    dark = "#0b0706"
    sky = sky_layer([(0.0, "#0a0605"), (0.3, "#150d09"), (0.5, "#20140d"), (0.66, "#1a100b"), (1.0, "#0c0807")],
                    bands=14, sharp=2.0)
    layers.append((sky, 0.0, 720))

    H = 360
    shaft_x, crack_y, slope = 330, 22, 0.32
    red, gold = "#a8402c", "#d0a650"
    fire = (R("#3a2414", "#6a4222", "#a06a34"), R("#e05a20", "#ffa640", "#fff0b8"), "#ff9a40")
    # ---------------- far: the back wall of the hall, friezes, stepped niches, braziers and a far colonnade
    far = Canvas(W, H)
    yy, xx, _ = grids(H)
    wallr = R("#3a2519", "#4a301f", "#5a3b25", "#6b472c", "#7d5534", "#90643d")
    floor_y = 232
    ashlar(far, yy <= floor_y, wallr, "stw", course=8, joint=20)
    corn = R("#3a2519", "#5a3b25", "#7d5534", "#9a6c42")
    for k in range(3):
        band_k = (yy >= 38 + k * 3) & (yy < 41 + k * 3)
        flat(far, band_k, corn[1 + (k == 1)])
        flat(far, top_rim(band_k), corn[3 - (k > 0)])
        flat(far, bot_rim(band_k), corn[0])
    fr_band = R("#5e3c22", "#7e5634", "#9a6e44")
    relief_frieze(far, 50, 66, fr_band, red, gold, "stf0", group=80, fade=0.85)
    relief_frieze(far, 158, 166, fr_band, red, gold, "stf1", group=40, fade=0.7)
    niches = [53.33 + i * 213.33 for i in range(3)]
    for i, nx in enumerate(niches):
        dn = np.abs(wdx(xx, nx) + 0.5)
        niche = ((dn <= 13) & (yy >= 104)) | ((dn <= 9) & (yy >= 99)) | ((dn <= 5) & (yy >= 94))
        niche &= yy <= 150
        flat(far, niche, "#1a100b")
        flat(far, niche & (wdx(xx, nx) < -6), "#120b08")
        flat(far, left_rim(niche), "#0c0806")
        flat(far, right_rim(niche) | top_rim(niche) & (wdx(xx, nx) > 0), wallr[3])
        sill = (dn <= 16) & (yy >= 151) & (yy <= 153)
        flat(far, sill, wallr[4])
        flat(far, top_rim(sill), wallr[5])
        flat(far, bot_rim(sill), wallr[0])
        relief_frieze(far, 100, 118, fr_band, red, gold, ("stp", i), group=80, fade=0.85,
                      clip=np.abs(wdx(xx, nx + 106.67)) <= 30)
    flat(far, yy > floor_y, "#1c120c")
    flat(far, yy == floor_y + 1, "#3a2618")
    colr = R("#24170f", "#2e1d13", "#3a2518", "#4a301e", "#5c3c25", "#70492c")
    for i in range(6):
        tomb_pillar(far, i * 106.67, 38, floor_y + 4, 7, colr, ("stfp", i), courses=12)
    lit = light_field(H, pools=[(nx, 134, 72, 60, 0.75) for nx in niches], ambient=(44, 200, 0.25))
    dim(far, lit, dark, base=0.75, top=120, top_t=1.0, floor=(190, 232, 0.75))
    for nx in niches:
        brazier(far, int(round(nx)), 150, *fire)
    layers.append((far, 0.06, 720))

    # ---------------- mid: great pillars, the cracked lintel, the sun shaft and sand pouring through
    mid = Canvas(W, H)
    pilr = R("#1c120c", "#2a1b12", "#3a2618", "#4c321f", "#5f3f27", "#744f30", "#8c6139")
    beam = yy <= 24 + np.round((pn1("stbm", 30, 2) - 0.5) * 2)[None, :]
    ashlar(mid, beam, R("#1a110b", "#24170f", "#301f14", "#3e291a", "#4a321f"), "stbm", course=6, joint=40)
    flat(mid, bot_rim(beam), "#5a3a22")
    for i, px in enumerate((150, 520)):
        tomb_pillar(mid, px, 24, 262, 17, pilr, ("stmp", i), courses=16, band=(112, 124, "#7a3024", "#a8823a"))
    sandr = R("#3a2618", "#48321d", "#5e4226", "#7a5832")
    dune_row(mid, 262, "stsd", sandr, 4, 238, 248, 30, 60, shade=1, amp=1.0, edge=False, lean=0.0)
    lit_sand = R("#7a5430", "#a87840", "#d4a45a")
    sand_fall(mid, shaft_x + 2, crack_y + 4, lit_sand, "stsf0")
    for i, fx in enumerate((236, 604)):
        sand_fall(mid, fx, 25, R("#3c2716", "#5a3c22", "#7a5634"), ("stsf", i))
    beam_c = shaft_x - crack_y * slope + 2
    pool_x = beam_c + 246 * slope
    lit = light_field(H, pools=[(pool_x, 246, 46, 18, 0.65)], beams=[(beam_c, slope, 30, 0.5, crack_y, 250)])
    dim(mid, lit, dark, base=0.5, top=80, top_t=1.0, floor=(236, 262, 0.75))
    shaft = Canvas(W, H)
    light_shafts(shaft, [(beam_c, 18)], "#ffdc98", slope=slope, fade_y=240, alphas=(0.07, 0.12))
    light_shafts(shaft, [(beam_c, 7)], "#fff0c8", slope=slope, fade_y=210, alphas=(0.08,))
    fan = (np.abs(wdx(xx - yy * slope, beam_c)) <= 2.5 + (yy - crack_y) * 0.09) & (yy >= crack_y)
    shaft.a[~fan] = 0.0                                              # the shaft fans out from the crack
    mid.paste(shaft)
    flat(mid, wellipse(H, pool_x, 247, 26, 4) & (mid.a > 0), "#ffd890", 0.14)
    crack = wline(H, [(shaft_x + 3, 0), (shaft_x - 1, 8), (shaft_x + 4, 15), (shaft_x + 1, crack_y + 3)], 2)
    crack &= yy <= crack_y + 2
    flat(mid, (sh(crack, 1, 0) | sh(crack, -1, 0)) & ~crack & beam, "#b07a3c")
    flat(mid, crack, "#fff3cf")
    flat(mid, crack & (yy < 8), "#ffffff")
    g = rng("stmote")
    for k in range(46):
        y = int(g.uniform(crack_y + 6, 226))
        x = int(beam_c + y * slope + g.uniform(-8, 8)) % W
        if fan[y, x]:
            put(mid, x, y, "#fff4d2", 0.6 if k % 3 else 1.0)
    layers.append((mid, 0.16, 720))

    # ---------------- near: a dark framing pillar, the heavy lintel and a calm drift of sand on the floor
    near = Canvas(W, H)
    nr = R("#070504", "#0c0806", "#120c08", "#19110b", "#22170f")
    nb = yy <= 12 + np.round((pn1("stnb", 40, 2) - 0.5) * 2)[None, :]
    flat(near, nb, nr[1])
    flat(near, bot_rim(nb), nr[3])
    tomb_pillar(near, 40, 12, 330, 22, nr, "stnp", courses=20)
    dune_row(near, 312, "stnd", R("#120c08", "#150e09", "#1d140c", "#261a10"), 3, 290, 300, 60, 100, shade=1, amp=1.0,
             edge=False, lean=0.0)
    layers.append((near, 0.3, 720))
    return dict(sky="#0a0605", horizon="#20140d", layers=layers)


# =============================================================== Skyport Wreck and the open Starsea (Act II)
def sky_band(seed, y0, amp, width, k=(1, 2), cell=90.0):
    """Centre row and half-width per column of a band winding across the sky (periodic over W)."""
    cols = np.arange(W)
    ph = rng("skb", seed).uniform(0, 2 * math.pi, 2)
    cy = y0 + amp * (0.62 * np.sin(cols / W * 2 * math.pi * k[0] + ph[0])
                     + 0.38 * np.sin(cols / W * 2 * math.pi * k[1] + ph[1]))
    hw = width * (0.6 + 0.8 * pn1(("skw", seed), cell, 2))
    return cy, hw


def star_river(cv, seed, y0, amp, width, glow, pal, alphas=(0.05, 0.08, 0.12), density=0.7, k=(1, 2), twinkles=7):
    """The Jade River across the night: a milky way winding over the sky. Stepped translucent glow, fullest in
    clumped star clouds and split by a dark rift, crowded with small stars toward its core.
    pal = star colours dim->bright (the last one is the twinkle core)."""
    h = cv.h
    yy = grids(h)[0]
    cy, hw = sky_band(("sr", seed), y0, amp, width, k)
    d = (yy - cy[None, :]) / hw[None, :]
    ad = np.abs(d)
    clump = pn2(h, ("src", seed), 40, 12, 2)
    fib = pn2(h, ("srf", seed), 80, 3, 2)
    level = np.zeros((h, W), int)
    for i in range(len(alphas)):
        reach = (1.0 - i * 0.3) * (0.62 + 0.7 * clump) + (fib - 0.5) * 0.3
        level[despeck(ad < reach)] = i + 1
    rc = 0.22 * np.sin(np.arange(W) / W * 6 * math.pi + 1.3)
    rift = (np.abs(d - rc[None, :]) < 0.12 + (fib - 0.5) * 0.25) & (pn2(h, ("srr", seed), 60, 8, 1) > 0.4)
    rift = despeck(rift & (level > 1))
    level = np.where(rift, level - 1, level)
    for i, a in enumerate(alphas):
        flat(cv, level == i + 1, glow, a)
    g = rng("srs", seed)
    n = len(pal) - 1
    for i in range(int(W * 1.3 * density)):
        x = int(g.integers(0, W))
        o = g.normal(0, 0.42)
        y = int(round(cy[x] + o * hw[x]))
        if abs(o) > 1.0 or not 0 <= y < h or rift[y, x]:
            continue
        b = (1.0 - abs(o)) * (0.4 + 0.9 * clump[y, x]) * (n - 1) + g.uniform(-1.4, 0.2)
        put(cv, x, y, pal[int(np.clip(round(b), 0, n - 1))])
    for i in range(twinkles):
        x = int((i + g.uniform(0.2, 0.8)) * W / twinkles)
        y = int(round(cy[x] + g.normal(0, 0.3) * hw[x]))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            put(cv, x + dx, y + dy, pal[n - 2])
        put(cv, x, y, pal[-1])
    return cy, hw


def nebula(cv, seed, y0, amp, width, col, alphas=(0.05, 0.08, 0.12), k=(1, 3), cell=70.0, gaps=0.25):
    """A drifting nebula: a broad band of flat translucent steps frayed into long wisps along its flow and
    thinning to nothing along part of its length."""
    h = cv.h
    yy = grids(h)[0]
    cy, hw = sky_band(("nb", seed), y0, amp, width, k, cell=cell * 2)
    d = np.abs(yy - cy[None, :]) / hw[None, :]
    ends = np.clip((pn1(("nbe", seed), 200, 2) - gaps) / 0.3, 0, 1)
    wisp = pn2(h, ("nbw", seed), cell, 3, 2)
    blob = pn2(h, ("nbb", seed), 36, 14, 2)
    m_all = np.zeros((h, W), bool)
    for i, a in enumerate(alphas):
        reach = ends[None, :] * ((1.0 - i * 0.3) * (0.55 + 0.7 * blob) + (wisp - 0.5) * 0.8)
        m = despeck(d < reach)
        flat(cv, m, col, a)
        m_all |= m
    return m_all


def shard_isle(cv, cx, top, hw, depth, ramp, seed, tilt=0.0, spurs=2, rim=None, cap=None):
    """A shattered isle of the old sky-port adrift: a tilted top slab with a fracture step over an angular
    underside broken into facets and a spur or two. Lit from the upper left: sunlit facets on the left, shade
    on the right. ramp dark->light (>= 6); rim = warm edge light; cap = (dark, light) old paving on top.
    Returns (mask, top row per column)."""
    h = cv.h
    yy, xx, _ = grids(h)
    g = rng("shard", seed)
    cols = np.arange(W)
    d = wdx(cols, cx)
    inside = np.abs(d) <= hw
    tp = top + tilt * d
    sx = g.uniform(-0.5, 0.5) * hw
    tp = tp + np.where(d > sx, 1, 0) * g.choice([-2, 2])
    tp = tp + np.clip(np.abs(d) - (hw - 4), 0, None) * g.uniform(0.5, 1.2)
    tp = np.round(tp + (pn1(("sht", seed), 4, 1) > 0.72) * 1.0)
    # angular underside: a polyline through random vertices down to an off-centre point
    nv = int(g.integers(4, 7))
    tipx = g.uniform(-0.3, 0.3) * hw
    vx = np.sort(np.concatenate([[-hw, hw, tipx], g.uniform(-hw * 0.9, hw * 0.9, nv)]))
    vy = []
    for x_ in vx:
        t = 1 - abs(x_ - tipx) / (hw + abs(tipx))
        vy.append(3 + depth * (t ** 1.2) * (1.0 if x_ == tipx else g.uniform(0.55, 0.95)))
    vy[0] = vy[-1] = 2.0
    ub = top + tilt * d + np.interp(d, vx, vy)
    for _ in range(spurs):
        px_ = g.uniform(-0.5, 0.5) * hw
        ub = ub + g.uniform(0.2, 0.45) * depth * np.clip(1 - np.abs(d - px_) / g.uniform(1.5, 3.0), 0, 1)
    ub = np.round(ub + (pn1(("shj", seed), 3, 1) - 0.5) * 2.0)
    m = inside[None, :] & (yy >= tp[None, :]) & (yy <= ub[None, :])
    m = despeck(m)
    if not m.any():
        return m, tp
    n = len(ramp)
    # facets: the slope of the underside segment under each column decides light (left-facing) or shade
    slope = np.gradient(np.interp(d, vx, vy))
    face = np.clip(-slope * 1.2, -1, 1)
    dep = yy - tp[None, :]
    rel = np.clip(dep / max(1.0, depth), 0, 1)
    u = row_u_local(m)
    st = pn2(h, ("shc", seed), 2.5, 8, 2)
    v = (n - 1) * 0.58 + (0.5 - u) * 1.8 - face[None, :] * 1.3 * (rel > 0.15) - rel * 1.8
    v = v - ((st > 0.7) & (rel > 0.15)) * 1.0 + (dep < 3) * 0.9
    paint(cv, m, ramp, v, sharp=4)
    # fracture lines running down across the facets, lit along their upper-left lip
    inner = m & sh(m, 1, 0) & sh(m, -1, 0) & (dep > 3)
    for _ in range(max(1, int(hw // 14))):
        fx = cx + g.uniform(-0.6, 0.4) * hw
        fy = top + g.uniform(3, 6)
        fl = wline(h, [(fx, fy), (fx + g.uniform(2, 6), fy + depth * 0.35), (fx + g.uniform(-2, 8), fy + depth * 0.7)])
        flat(cv, fl & inner, ramp[1])
        flat(cv, sh(fl, -1, 0) & inner & ~fl, ramp[-3])
    flat(cv, right_rim(m) | bot_rim(m), ramp[0])
    flat(cv, left_rim(m) & (dep > 1) & (rel < 0.7), ramp[-2])
    flat(cv, top_rim(m) & (u < 0.85), ramp[-1] if rim is None else rim)
    if cap is not None:
        pave = sh(top_rim(m), 0, 1) & m
        flat(cv, pave, cap[1])
        flat(cv, pave & (((xx + int(cx)) % 5) == 0), cap[0])
    return m, tp


def snapped_beam(cv, x0, y0, x1, y1, pal, width=2):
    """A timber beam from (x0, y0) snapped off at (x1, y1): lit top edge, dark underside, splintered end."""
    h = cv.h
    m = wline(h, [(x0, y0), (x1, y1)], width)
    flat(cv, m, pal[1])
    flat(cv, bot_rim(m), pal[0])
    flat(cv, top_rim(m), pal[2])
    sx = 1 if x1 >= x0 else -1
    put(cv, x1 + sx, y1 - 1, pal[2])
    put(cv, x1 + 2 * sx, y1 - 1, pal[1])
    put(cv, x1 + sx, y1 + width - 1, pal[0])
    return m


def sag_pts(x0, y0, x1, y1, sag, n=None):
    """Points along a rope or chain slung from (x0, y0) to (x1, y1), sagging `sag` px at its middle."""
    n = n or max(3, int(abs(x1 - x0) / 3) + 2)
    return [(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t + sag * 4 * t * (1 - t)) for t in np.linspace(0, 1, n)]


def dangle_pts(x0, y0, ln, sway=2.0, n=None):
    """Points along a broken chain hanging `ln` px from (x0, y0), its free end swaying sideways."""
    n = n or max(3, int(ln / 2))
    return [(x0 + sway * math.sin(t * 2.2) * t, y0 + ln * t) for t in np.linspace(0, 1, n)]


def chain(cv, pts, pal, heavy=False):
    """Iron chain along a polyline. Light: 1 px, links alternating lit and dark. Heavy: open 3 px rings (lit
    side, dark side, hole showing through) joined by dark edge-on links. pal = (dark, mid, light)."""
    P = []
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        n = max(1, int(math.ceil(max(abs(xb - xa), abs(yb - ya)))))
        for i in range(n):
            p = (int(round(xa + (xb - xa) * i / n)), int(round(ya + (yb - ya) * i / n)))
            if not P or P[-1] != p:
                P.append(p)
    for i, (x, y) in enumerate(P):
        if not heavy:
            put(cv, x, y, pal[2] if (i // 2) % 2 == 0 else pal[0])
            continue
        j0, j1 = max(0, i - 2), min(len(P) - 1, i + 2)
        ox, oy = (1, 0) if abs(P[j1][1] - P[j0][1]) >= abs(P[j1][0] - P[j0][0]) else (0, 1)
        k = i % 6
        if k < 4:
            put(cv, x - ox, y - oy, pal[2])
            put(cv, x + ox, y + oy, pal[0])
            if k in (0, 3):
                put(cv, x, y, pal[1])
        else:
            put(cv, x, y, pal[0])
    return P


def lantern(cv, x, y, pal, glow=None, cord=None):
    """Hanging paper lantern with its top at (x, y): a 2x3 warm body lit on the left, dark caps and a stepped
    glow. pal = (cap, body, lit)."""
    h = cv.h
    if glow is not None:
        for r, a in ((6.0, 0.06), (4.0, 0.12)):
            flat(cv, wellipse(h, x + 0.5, y + 2.5, r, r * 0.85), glow, a)
    if cord is not None:
        put(cv, x, y - 1, cord)
    flat(cv, wrect(h, x, y + 1, x + 1, y + 3), pal[1])
    flat(cv, wrect(h, x, y + 1, x, y + 2), pal[2])
    flat(cv, wrect(h, x, y, x + 1, y), pal[0])
    put(cv, x, y + 4, pal[0])


def rope_line(cv, pts, col, pennants=None, every=7, seed=0):
    """A sagging rope along pts, optionally strung with little triangular pennants."""
    h = cv.h
    m = wline(h, [(round(x), round(y)) for x, y in pts], 1)
    flat(cv, m, col)
    if pennants is not None:
        g = rng("pen", seed)
        ys, xs = np.nonzero(m)
        if not len(xs):
            return m
        order = np.argsort(wdx(xs, pts[0][0]))
        for j, k in enumerate(order[::every][1:-1]):
            x, y = int(xs[k]), int(ys[k])
            c = pennants[(j + int(g.integers(0, 2))) % len(pennants)]
            flat(cv, wrect(h, x, y + 1, x + 2, y + 1), c)
            flat(cv, wrect(h, x, y + 2, x + 1, y + 2), c)
            put(cv, x, y + 3, c)
    return m


EYE = [".XXX.", "XX.XX", ".XXX."]   # the Starsea pirates' watching eye


def war_banner(cv, x, by, ht, pole, cloth, emblem, seed, bl=30, bw=10, wave=1.4, trim=None, sign=None):
    """A tall pole with a spear finial and a long tattered banner streaming right: waving, swallow-tailed, torn,
    a pale trim along its top edge and the watching-eye emblem (or another `sign`, rows of 'X') near the hoist.
    pole = (dark, mid, light); cloth dark->light (4)."""
    h = cv.h
    yy, xx, _ = grids(h)
    g = rng("banner", seed)
    pm = wrect(h, x, by - ht, x + 1, by)
    flat(cv, pm, pole[1])
    flat(cv, wrect(h, x, by - ht, x, by), pole[2])
    flat(cv, wrect(h, x - 1, by - ht - 1, x + 2, by - ht - 1), pole[0])
    flat(cv, wrect(h, x, by - ht - 4, x + 1, by - ht - 2), pole[2])
    put(cv, x, by - ht - 5, pole[2])
    put(cv, x + 1, by - ht - 3, pole[1])
    top = by - ht + 1
    ph = g.uniform(0, 6.28)
    u = wdx(xx, x + 2)
    tt = np.clip(u / bl, 0, 1)
    off = wave * np.sin(u * 0.3 + ph) * tt + tt * 4.0
    hh = bw * (1 - 0.35 * tt)
    rag = (pn1(("bnr", seed), 2, 1) > 0.6)[None, :] * (1.0 + (pn1(("bnr2", seed), 2, 1) > 0.8)[None, :])
    m = (u >= 0) & (u <= bl) & (yy >= top + off) & (yy <= top + off + hh - rag * (tt > 0.25))
    tail = u > bl - 7
    m &= ~(tail & (np.abs(yy - (top + off + hh / 2)) < (u - (bl - 7)) * 0.6))
    hx = x + 2 + bl * g.uniform(0.5, 0.7)
    m &= ~wellipse(h, hx, top + 4 + wave * 0.5 + 2.0, 1.5, 1.2)
    m = despeck(m)
    light = np.cos(u * 0.3 + ph)
    idx = np.where(light > 0.4, 2, np.where(light < -0.5, 0, 1))
    cv.fill_idx(m, idx, cloth)
    flat(cv, top_rim(m) & (light > -0.3), cloth[3])
    flat(cv, bot_rim(m), cloth[0])
    if trim is not None:
        flat(cv, top_rim(m) & (tt < 0.8) & (((xx + int(x)) % 6) != 3), trim)
    flat(cv, m & (u < 1), cloth[0])
    sign = EYE if sign is None else sign
    sy = int(round(top + 1 + (bw - len(sign)) / 2.0))
    for r_, row in enumerate(sign):
        for c_, ch in enumerate(row):
            px_, py_ = x + 4 + c_, sy + r_
            if ch == "X" and m[py_ % h, px_ % W]:
                put(cv, px_, py_, emblem)
    return m


def broken_pier(cv, x0, x1, top, by, pal, seed, course=9, joint=32, brk=(8, 8), slope=(1.4, 1.4), notches=2,
                rim=None, dark=None):
    """A broken pier of the old port: dressed stone courses under a paved top, both ends torn away in jagged
    diagonal breaks with a block or two knocked out, lit left faces, shaded right return. pal dark->light
    (>= 6). Returns (mask, crest row per column)."""
    h = cv.h
    yy, xx, _ = grids(h)
    g = rng("pier", seed)
    cw = (x1 - x0) % W
    cx = x0 + cw / 2.0
    d = wdx(xx, cx)
    dc = wdx(np.arange(W), cx)
    crest = np.full(W, float(top))
    crest = crest + np.clip(-dc - (cw / 2 - brk[0]), 0, None) * slope[0]
    crest = crest + np.clip(dc - (cw / 2 - brk[1]), 0, None) * slope[1]
    for _ in range(notches):
        nx = g.uniform(-0.4, 0.4) * cw
        nw = g.uniform(3, 7)
        crest = crest + np.where(np.abs(dc - nx) < nw, g.choice([course // 2, course]), 0)
    crest = np.round(crest + (pn1(("prc", seed), 3, 1) - 0.5) * 1.2 * (1 + (np.abs(dc) > cw / 2 - max(brk)) * 2))
    jl = (pn2(h, ("prl", seed), 3, 8, 2) - 0.5) * 4
    jr = (pn2(h, ("prr", seed), 3, 8, 2) - 0.5) * 4
    m = (d >= -cw / 2 + jl) & (d <= cw / 2 + jr) & (yy >= crest[None, :]) & (yy <= by)
    m = despeck(m)
    ashlar(cv, m, pal[:5], ("pas", seed), course=course, joint=joint)
    u = row_u_local(m)
    dep = depth_in(m)
    if dark is not None:
        haze_fade(cv, m & (u > 0.5), dark, np.clip((u - 0.5) * 2.0, 0, 0.6), steps=3, sharp=4)
    deck = m & (yy <= top + 2) & (dep < 3)
    flat(cv, deck, pal[4])
    flat(cv, deck & (dep < 1), pal[5])
    flat(cv, deck & ((xx % 7) == 0) & (dep >= 1), pal[2])
    flat(cv, left_rim(m) & ~deck, pal[4])
    flat(cv, right_rim(m) & ~deck, pal[0])
    flat(cv, top_rim(m) & (u < 0.9), pal[-1] if rim is None else rim)
    return m, crest


def cloud_floor(cv, y0, y1, seed, pal, rows=8, r0=3.0, r1=14.0, stretch=2.4, persp=1.6, bottom=None):
    """A floor of cloud receding to the horizon: rows of long low swells that grow and spread apart toward the
    viewer. Each row fills down to `bottom`, so nearer rows ride over the bodies of farther ones: bright crest,
    banded body sinking into the trough under the next row. pal dark->light (>= 5). Returns mask."""
    h = cv.h
    yy = grids(h)[0]
    g = rng("cfloor", seed)
    n = len(pal)
    bottom = h if bottom is None else bottom
    cols = np.arange(W)
    total = np.zeros((h, W), bool)
    for k in range(rows):
        t = (k / max(1, rows - 1)) ** persp
        base = y0 + (y1 - y0) * t
        r = r0 + (r1 - r0) * t
        env = np.full(W, np.inf)
        uu = np.zeros(W)
        x = g.uniform(0, r * stretch)
        while x < W + r * stretch * 0.5:
            rr = r * g.uniform(0.7, 1.3)
            rx, ry = rr * stretch, rr * 0.6
            cy = base + g.uniform(-0.35, 0.35) * r
            dd = wdx(cols, x)
            q = np.clip(1 - (dd / rx) ** 2, 0, 1)
            tp = np.where(np.abs(dd) < rx, cy - ry * np.sqrt(q), np.inf)
            better = tp < env
            env = np.where(better, tp, env)
            uu = np.where(better, (dd / rx + 1) / 2, uu)
            x += rx * g.uniform(1.0, 1.5)
        env = np.round(np.minimum(env, bottom))
        m = (yy >= env[None, :]) & (yy <= bottom)
        dep = (yy - env[None, :]) / max(1.0, r * 0.45)
        u = uu[None, :]
        v = (n - 1) - (dep >= 0.6) * 1.0 - (dep >= 1.5) * 1.0 - (dep >= 2.6) * 0.9 - (dep >= 4.0) * 0.9 \
            + ((u < 0.35) & (dep < 1.6)) * 0.6 - ((u > 0.7) & (dep < 2.2)) * 0.7
        paint(cv, m, pal, v, sharp=4)
        flat(cv, top_rim(m) & (u < 0.62), pal[-1])
        total |= m
    return total


def luminous_sea(cv, y, seed, pal, ranks, fill=True):
    """Nearer reaches of the Starsea: ranks of cumulus rows that grow toward the viewer, the last one filled to
    the canvas foot. ranks = [(r_lo, r_hi, gap, amp), ...] far to near."""
    for i, (rl, rh, gap, amp) in enumerate(ranks):
        cloud_bank(cv, y, (seed, i), pal, r_lo=rl, r_hi=rh, rows=1, row_gap=gap, amp=amp,
                   fill_below=fill and i == len(ranks) - 1)
        y += gap


def sea_ribbon(cv, y, seed, col, core=None, thick=3.0, amp=2.0, alphas=(0.16, 0.26), cell=160.0, gaps=0.3,
               clip=None):
    """A slow nebula current lying on the Starsea: a long wavy translucent band that thins to nothing at its
    ends, with a brighter thread along its core."""
    h = cv.h
    yy = grids(h)[0]
    cols = np.arange(W)
    ph = rng("srb", seed).uniform(0, 6.283)
    yc = y + (pn1(("srb", seed), cell, 2) - 0.5) * 2 * amp + np.sin(cols / W * 4 * math.pi + ph) * amp * 0.6
    ends = np.clip((pn1(("sre", seed), cell * 1.5, 1) - gaps) / 0.25, 0, 1)
    clip = np.ones((h, W), bool) if clip is None else clip
    for i, a in enumerate(alphas):
        hw = thick * (1 - i * 0.45) * ends
        m = (np.abs(yy - yc[None, :]) <= hw[None, :]) & (hw[None, :] >= 0.5) & clip
        flat(cv, m, col, a)
    if core is not None:
        m = (np.round(yc)[None, :] == yy) & (ends[None, :] > 0.55) & clip & (pn2(h, ("srt", seed), 14, 4, 1) > 0.4)
        flat(cv, m, core, 0.35)


def sea_glints(cv, region, seed, count, pal, big_every=4, specks=0, speck_c=None):
    """Stars caught in the cloud-sea: glints over `region`, every few with a small cross, plus dim specks.
    pal = (arm, core)."""
    g = rng("sglint", seed)
    ys, xs = np.nonzero(region)
    if not len(xs):
        return
    for i in range(specks):
        j = int(g.integers(0, len(xs)))
        put(cv, int(xs[j]), int(ys[j]), speck_c, 0.7)
    for i in range(count):
        j = int(g.integers(0, len(xs)))
        x, y = int(xs[j]), int(ys[j])
        if i % big_every == 0:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                put(cv, x + dx, y + dy, pal[0])
        put(cv, x, y, pal[1])


def tilted_dock(cv, cx, by, ang, tiers, w0, pal, deck, window=None, span=(12, 14), shrink=0.74, body_h=4):
    """A pagoda on its pier platform, tipped by ang radians (clockwise) about the deck top at (cx, by). Built from
    rotated polygons so the edges stay crisp. pal = pagoda (dark, mid, light); deck = (dark, mid, light).
    Returns the local->canvas mapping."""
    h = cv.h
    c, s_ = math.cos(ang), math.sin(ang)

    def G(u, v):
        return cx + c * u - s_ * v, by + s_ * u + c * v

    def poly(pts):
        return wpoly(h, [G(u, v) for u, v in pts])

    for pu in range(-span[0] + 2, span[1] - 1, 6):
        flat(cv, wline(h, [G(pu, 2), G(pu, 6)], 1), deck[0])
    flat(cv, wline(h, [G(-span[0] + 3, 2), G(-3, 9)], 1), deck[0])
    flat(cv, wline(h, [G(span[1] - 3, 2), G(3, 9)], 1), deck[0])
    dm = poly([(-span[0], -0.5), (span[1], -0.5), (span[1], 1.5), (-span[0], 1.5)])
    flat(cv, dm, deck[1])
    flat(cv, top_rim(dm), deck[2])
    flat(cv, bot_rim(dm), deck[0])
    for pu in range(-span[0], span[1] + 1, 4):
        put(cv, *G(pu, -1.5), deck[1])
    flat(cv, wline(h, [G(-span[0], -2.5), G(-span[0] + 8, -2.5)], 1), deck[1])
    flat(cv, wline(h, [G(span[1] - 6, -2.5), G(span[1], -2.5)], 1), deck[1])
    y = -1.0
    bw = float(w0)
    for _ in range(tiers):
        hw_ = bw / 2.0
        body = poly([(-hw_, y - body_h + 0.5), (hw_, y - body_h + 0.5), (hw_, y + 0.5), (-hw_, y + 0.5)])
        flat(cv, body, pal[1])
        flat(cv, left_rim(body), pal[2])
        roof = poly([(-hw_ - 3.5, y - body_h + 1), (hw_ + 3.5, y - body_h + 1), (hw_ + 1.5, y - body_h - 1.5),
                     (-hw_ - 1.5, y - body_h - 1.5)])
        flat(cv, roof, pal[0])
        flat(cv, top_rim(roof) & ~right_rim(roof), pal[2])
        for sx in (-1, 1):
            put(cv, *G(sx * (hw_ + 4), y - body_h), pal[0])
        if window is not None:
            put(cv, *G(0, y - 1), window)
            put(cv, *G(0, y - 2), window)
        y -= body_h + 2
        bw = max(2.0, bw * shrink + 0.5)
    flat(cv, wline(h, [G(0, y + 1), G(0, y - 3)], 1), pal[0])
    return G


def sky_junk(cv, px, py):
    """The colossal wreck of a sky junk: a broken-backed hull (bow half nose-down, stern half reared up) split
    open over exposed ribs, a snapped main mast with a torn batten sail, a stern castle, mooring chains and
    pirate lanterns. Drawn in ship-local coordinates (u along the keel, v down) placed per half around the
    keel point of the break at (px, py)."""
    h = cv.h
    yy, xx, _ = grids(h)
    hull_r = R("#191224", "#22192e", "#2d2138", "#3a2b43", "#4b374e", "#5f4558", "#7c5662")
    wale = R("#130d1c", "#352640", "#6e4a5a")
    lit_rim = "#c47a7a"
    hold = R("#0c0913", "#140f1d")
    rib = R("#1c1428", "#3c2c40", "#744e5a")
    sail = R("#2a1422", "#43182a", "#5e2232", "#7c2e38", "#9a4240")
    sail_rim = "#e08a6a"
    lan = R("#2a1a1a", "#ff8a3a", "#ffd07a")
    glow = "#ff9a4a"
    chn = R("#140e1e", "#34283e", "#6a5670")

    def sheer(u):
        u = np.asarray(u, float)
        return np.where(u < 0, -14 * (np.clip(-u, 0, 170) / 170.0) ** 1.8,
                        np.where(u < 96, -24 * (np.clip(u, 0, 96) / 96.0) ** 1.6, -24 - (u - 96) * 0.16))

    def keel(u):
        u = np.asarray(u, float)
        return 40 - 22 * (np.clip(-u, 0, 170) / 170.0) ** 2.2 - 26 * (np.clip(u, 0, 170) / 170.0) ** 2.4

    halves = {-1: (-0.07, (-20.0, 40.0)), 1: (-0.13, (20.0, 40.0))}

    def frame(side):
        ang, pl = halves[side]
        c, s = math.cos(ang), math.sin(ang)
        dx = wdx(xx, px)
        dy = yy - py
        return pl[0] + c * dx + s * dy, pl[1] - s * dx + c * dy

    def G(side, u, v):
        ang, pl = halves[side]
        c, s = math.cos(ang), math.sin(ang)
        du, dv = u - pl[0], v - pl[1]
        return px + c * du - s * dv, py + s * du + c * dv

    def poly(side, pts):
        return wpoly(h, [G(side, u, v) for u, v in pts])

    hull_all = np.zeros((h, W), bool)
    for side in (-1, 1):
        u, v = frame(side)
        jag = (pn2(h, ("sjb", side), 3, 4, 2) - 0.5) * 9
        bow_end = -172 + np.clip(v + 14, 0, None) * 0.35
        stern_end = 170 - np.clip(v + 44, 0, None) * 0.3
        body = (v >= sheer(u)) & (v <= keel(u)) & (u >= bow_end) & (u <= stern_end)
        body &= (u <= -22 + jag) if side < 0 else (u >= 18 + jag)
        body = despeck(body)
        rel = v - sheer(u)
        n = len(hull_r)
        plank = pn2(h, ("sjp", side), 26, 5, 1)
        vv = (n - 1) * 0.66 - np.clip(rel / 36.0, 0, 1) * 3.0 + (plank - 0.5) * 0.8
        paint(cv, body, hull_r, vv, sharp=5)
        seam = body & (np.floor(rel) % 5 == 4) & (rel > 11) & ~((rel >= 20) & (rel < 24))
        flat(cv, seam, hull_r[1])
        butt = body & (np.floor(u + np.floor(rel / 5) * 11) % 26 == 0) & (rel > 11)
        flat(cv, butt, hull_r[1])
        wl = body & (rel >= 6) & (rel < 10)
        flat(cv, wl, wale[1])
        flat(cv, wl & (rel < 7), wale[2])
        flat(cv, wl & (rel >= 9), wale[0])
        wl2 = body & (rel >= 20) & (rel < 23)
        flat(cv, wl2, wale[1])
        flat(cv, wl2 & (rel < 21), wale[2])
        flat(cv, wl2 & (rel >= 22), wale[0])
        flat(cv, body & (rel >= 1) & (rel < 3), hull_r[4])
        flat(cv, top_rim(body), lit_rim)
        # gun / oar ports along the wale, a few with lamplight inside
        g = rng("sjport", side)
        for k, pu in enumerate(np.arange(-150 if side < 0 else 34, -34 if side < 0 else 150, 13)):
            x, y = G(side, pu, sheer(pu) + 13)
            pm = wrect(h, int(round(x)), int(round(y)), int(round(x)) + 1, int(round(y)) + 1) & body
            lit = g.random() < 0.3
            flat(cv, pm, "#ff9a4a" if lit else hold[0])
            if lit:
                put(cv, int(round(x)), int(round(y)), "#ffd07a")
        # torn planking near the break shows the dark hold and its ribs
        tear_c = -34 if side < 0 else 32
        torn = body & (np.abs(u - tear_c) < 12 + (pn2(h, ("sjt", side), 4, 6, 2) - 0.5) * 14) & (rel > 3)
        torn = despeck(torn)
        flat(cv, torn, hold[1])
        rb = torn & ((np.floor(u) % 7) < 2)
        flat(cv, rb, rib[1])
        flat(cv, rb & ((np.floor(u) % 7) < 1), rib[2])
        flat(cv, top_rim(torn), hold[0])
        flat(cv, sh(top_rim(torn), 0, -1) & body & ~torn, rib[2])
        hull_all |= body
    # the stern castle on the poop deck: dark walls, lit stern-gallery windows, an upswept pavilion roof
    s = 1
    wall = poly(s, [(106, sheer(106) + 1), (106, -46), (158, -46), (158, sheer(158) + 1)])
    flat(cv, wall, hull_r[2])
    flat(cv, left_rim(wall), hull_r[4])
    for k in range(6):
        wu = 110 + k * 8
        wm = poly(s, [(wu, -42), (wu + 4, -42), (wu + 4, -38), (wu, -38)])
        flat(cv, wm, "#ff9a4a")
        flat(cv, wm & ~sh(wm, 0, 1), "#ffd07a")
        flat(cv, poly(s, [(wu + 6, -45), (wu + 7, -45), (wu + 7, sheer(wu + 6) + 1), (wu + 6, sheer(wu + 6) + 1)]),
             hull_r[1])
    roof = poly(s, [(93, -53), (97, -50), (104, -48), (160, -48), (167, -50), (171, -53), (165, -53), (154, -58),
                    (110, -58), (99, -53)])
    su2 = frame(1)[0]
    flat(cv, roof, "#2a1e38")
    flat(cv, roof & (np.floor(su2) % 3 == 0) & ~top_rim(roof), "#1c1428")
    flat(cv, top_rim(roof), "#7a5468")
    flat(cv, bot_rim(roof), "#110c1a")
    ridge = poly(s, [(108, -58.5), (156, -58.5), (157, -61), (154, -60), (110, -60), (107, -61)])
    flat(cv, ridge, "#160f20")
    hull_all |= wall | roof
    # rudder: its stock drops through the overhanging stern to a holed blade under the counter
    rud = poly(s, [(128, keel(134) - 6), (146, keel(146) - 6), (150, keel(146) + 14), (130, keel(134) + 10)])
    flat(cv, rud, hull_r[2])
    flat(cv, left_rim(rud), hull_r[4])
    flat(cv, right_rim(rud) | bot_rim(rud), hull_r[0])
    for hu, hv in ((134, 3), (141, 3), (134, 9), (141, 9)):
        x, y = G(s, hu, keel(138) + hv)
        flat(cv, wrect(h, int(round(x)), int(round(y)), int(round(x)) + 1, int(round(y))) & rud, hull_r[0])
    # ribs across the open break, from the keel toward the missing deck, snapped at uneven heights
    g = rng("sjribs")
    for k, u0 in enumerate(range(-24, 22, 6)):
        f = (u0 + 24) / 46.0
        side = -1 if f < 0.5 else 1
        top_v = sheer(u0) + g.uniform(-6, 14)
        x0, y0 = G(side, u0, keel(u0) + 2)
        x1, y1 = G(side, u0 + g.uniform(-2, 2), top_v)
        rm = wline(h, [(x0, y0), (x1, y1)], 2)
        flat(cv, rm, rib[1])
        flat(cv, left_rim(rm), rib[2])
        flat(cv, right_rim(rm), rib[0])
        put(cv, x1, y1 - 1, rib[2])
    for (ua, va, ub, vb) in ((-26, 20, 6, 21), (-26, 8, -8, 9)):
        xa, ya = G(-1, ua, va)
        xb, yb = G(1, ub, vb)
        sm = wline(h, [(xa, ya), (xb, yb)], 1)
        flat(cv, sm, rib[1])
        flat(cv, top_rim(sm), rib[2])
    # masts: the main mast snapped high, a foremast stump, a mizzen stump on the stern castle
    masts = {}
    for name, side, u0, base_v, top_v, w_ in (("main", 1, 44, None, -168, 3), ("fore", -1, -112, None, -86, 2),
                                             ("mizzen", 1, 140, -57, -92, 2)):
        bv = sheer(u0) + 2 if base_v is None else base_v
        xb_, yb_ = G(side, u0, bv)
        xt, yt = G(side, u0 - 2, top_v)
        mm = wline(h, [(xb_, yb_), (xt, yt)], w_)
        flat(cv, mm, hull_r[2])
        flat(cv, left_rim(mm), hull_r[5])
        flat(cv, right_rim(mm), hull_r[0])
        put(cv, xt, yt - 1, hull_r[5])                     # the snapped top: a jagged splinter
        put(cv, xt + 1, yt - 2, hull_r[4])
        put(cv, xt - 1, yt, hull_r[3])
        masts[name] = (xt, yt)
    # the torn batten sail on the main mast: yard raked up toward the bow, battens fanning down to a level foot
    # and poking past the luff; the fore corner torn away, one panel ripped open and hanging in strips
    su, sv = frame(1)
    mast_u, foot_v, nb = 43.0, -76.0, 5
    yard = -142.0 - (mast_u - su) * 0.36
    t = np.clip((sv - yard) / np.maximum(1.0, foot_v - yard), 0, 1)
    luff = -20.0 - 8.0 * t - 5.0 * np.sin(t * math.pi)
    outline = (sv >= yard) & (sv <= foot_v) & (su <= mast_u) & (su >= luff)
    pan = t * nb
    k_pan = np.floor(pan)
    fpan = pan - k_pan
    rag = (pn2(h, ("sjsr", 0), 1.5, 4, 1) - 0.5) * 6
    tear = (su < luff + 36 * (t - 0.58) / 0.42 + rag) & (t > 0.58)
    edge = luff + (mast_u - luff) * 0.52 + rag * 1.5
    tear |= (k_pan == 2) & (su < edge)
    tear |= (pn2(h, ("sjsh", 0), 6, 5, 2) > 0.78) & (k_pan == 1) & (su > luff + 4)
    strip_len = pn1(("sjsl", 0), 3, 1)
    strips = (k_pan == 2) & (su < edge) & (su > luff + 2) & ((np.floor(su) % 4) < 2) & \
             (fpan < 0.15 + strip_len[None, :] * 0.6)
    cloth = despeck(outline & (~tear | strips))
    vs = 3.5 - fpan * 2.2 + np.clip((10 - su) / 40.0, -1, 1) * 0.5 - t * 0.5
    paint(cv, cloth, sail, vs, sharp=5)
    flat(cv, left_rim(cloth) & ~strips, sail_rim)
    flat(cv, top_rim(cloth) & (fpan > 0.1), sail[3])
    flat(cv, bot_rim(cloth) & strips, sail[0])
    for k in range(nb + 1):
        fr = k / float(nb)
        lu = -20.0 - 8.0 * fr - 5.0 * math.sin(fr * math.pi)
        v_m = -142.0 + (foot_v + 142.0) * fr
        v_l = (-142.0 - (mast_u - lu) * 0.36) * (1 - fr) + foot_v * fr
        end_u = lu - 3
        if k == 3:                     # a batten snapped at the rip, its fore end drooping
            xa, ya = G(1, mast_u, v_m)
            xb, yb = G(1, lu + 18, v_m + (v_l - v_m) * (mast_u - lu - 18) / (mast_u - lu))
            flat(cv, wline(h, [(xa, ya), (xb, yb)], 1), "#1e1220")
            flat(cv, wline(h, [(xb, yb), (xb - 5, yb + 8)], 1), "#1e1220")
            continue
        xa, ya = G(1, mast_u, v_m)
        xb, yb = G(1, end_u, v_l + (v_l - v_m) * 3 / (mast_u - lu))
        bm = wline(h, [(xa, ya), (xb, yb)], 2 if k == 0 else 1)
        flat(cv, bm, "#1e1220")
        put(cv, xb, yb, "#8a5250")
    # rigging, a string of lanterns from the foremast stump to the main mast
    fx, fy = masts["fore"]
    mx, my = masts["main"]
    zx, zy = masts["mizzen"]
    pts = sag_pts(fx + 1, fy + 4, mx + 1, my + 44, 22)
    rope_line(cv, pts, "#3a2838")
    rope_line(cv, sag_pts(mx + 2, my + 3, zx + 1, zy + 1, 14), "#3a2838")
    rope_line(cv, sag_pts(mx + 2, my + 3, mx + 60, my + 110, 6), "#2e2030")
    for j in (3, 7, 11, 15):
        if j < len(pts) - 1:
            lantern(cv, int(round(pts[j][0])), int(round(pts[j][1])) + 1, lan, glow=glow)
    # a ragged pirate pennant on the mizzen stump
    war_banner(cv, int(round(zx)) - 1, int(round(zy)) + 20, 18, R("#140e18", "#2a1e26", "#5a4038"),
               R("#141232", "#1e1c46", "#2a285c", "#3e3c7c"), "#e0d4b8", "sjflag", bl=18, bw=7, wave=1.0,
               trim="#b8a888")
    # lanterns hung from the stern-castle eaves, at the bow and at the break
    for uu in (98, 166):
        x, y = G(1, uu, -48)
        lantern(cv, int(round(x)), int(round(y)) + 1, lan, glow=glow, cord=hull_r[1])
    xb_, yb_ = G(-1, -154, sheer(-154) + 1)
    x, y = G(-1, -156, -30)
    flat(cv, wline(h, [(xb_, yb_), (x, y)], 1), hull_r[3])
    flat(cv, wline(h, [(x, y), (x + 4, y)], 1), hull_r[3])
    lantern(cv, int(round(x)) + 4, int(round(y)) + 1, lan, glow=glow, cord=hull_r[3])
    # the bow eye
    x, y = G(-1, -150, -3)
    flat(cv, wellipse(h, x, y, 3.2, 2.2), "#6a2830")
    flat(cv, wellipse(h, x, y, 2.2, 1.3), "#d8c8b0")
    flat(cv, wellipse(h, x + 0.5, y, 0.9, 1.2), "#140e18")
    # mooring chains: taut to the sea from the bow and the stern, broken ones dangling from the hull
    xa, ya = G(-1, -162, 8)
    chain(cv, sag_pts(xa, ya, xa - 56, ya + 70, 5), chn, heavy=True)
    xa, ya = G(-1, -96, 30)
    chain(cv, dangle_pts(xa, ya, 30, sway=-3), chn, heavy=True)
    xa, ya = G(1, 152, 8)
    chain(cv, sag_pts(xa, ya, xa + 64, ya + 84, 8), chn, heavy=True)
    xa, ya = G(1, 96, 18)
    chain(cv, dangle_pts(xa, ya, 34, sway=3), chn, heavy=True)
    return hull_all


def skyport_wreck():
    """Skyport Wreck: the broken sky-port on the Starsea shore at dusk. Shattered isles trailing chains and snapped
    piers, a colossal wrecked junk lit by pirate lanterns, banners on the torn port rim, and the Jade River
    running overhead as a river of stars."""
    layers = []
    stops = [(0.0, "#0f0e29"), (0.12, "#181840"), (0.24, "#24214f"), (0.34, "#362a5e"), (0.42, "#4f3368"),
             (0.48, "#6c3b6e"), (0.53, "#8e4772"), (0.57, "#b25a74"), (0.6, "#d27476"), (0.62, "#ea9479"),
             (0.635, "#f8b580"), (0.65, "#ffd293"), (0.7, "#ffe0ad"), (1.0, "#f6c9a0")]
    sky = sky_layer(stops, bands=28, sharp=2.4)
    stars(sky, "swst", 360, 0, 170, R("#34346c", "#5e5e9a", "#a4a6d4", "#ffffff"), twinkle=9)
    star_river(sky, "swjr", 64, 24, 14, "#62dc92", R("#2e5c5a", "#3c806c", "#5aac84", "#96dcaa", "#dcf8e2",
                                                     "#ffffff"), density=0.6)
    for i, (cx, y, ln) in enumerate(((120, 178, 150), (400, 192, 210), (590, 204, 120), (260, 210, 150),
                                     (470, 162, 90))):
        streak(sky, cx, y, ln, R("#f4a47e", "#8a4670", "#c06478"), ("sws", i), rows=2)
    layers.append((sky, 0.0, 720))

    # ---------------- far: shattered isles of the old port adrift above the horizon, chains and snapped piers
    fh = 220
    far = Canvas(W, fh)
    yy = grids(fh)[0]
    rock = R("#1e1838", "#281f46", "#322752", "#3e2f5e", "#4b386a", "#5c4476", "#725283")
    rim_c = "#e0968e"
    wood = R("#241a32", "#3e2e46", "#6a4c5a")
    chn = R("#221a36", "#3a2e4e", "#6a5878")
    dock_pal = R("#18122a", "#2a2040", "#5a4668")
    dock_deck = R("#18122a", "#342840", "#8a6068")
    horizon_haze = "#e8a08c"
    isles = [(70, 40, 34, 44, -0.06, 2), (205, 104, 15, 20, 0.1, 1), (334, 20, 28, 38, 0.05, 2),
             (520, 62, 40, 50, -0.08, 2), (408, 128, 12, 14, 0.14, 1), (152, 62, 5, 8, 0.2, 0),
             (262, 30, 5, 7, 0.1, 0), (612, 110, 7, 10, -0.15, 0)]
    for i, (cx, top, hw, dp, tilt, sp) in enumerate(isles):
        hz = np.clip((top - 20) / 130.0, 0, 1)
        behind = lerp_stops(stops, (top + 60 + dp * 0.5) / (SKY_H - 1.0))    # the sky at the isle's height
        ramp = hazed(rock, behind, 0.22 + hz * 0.18)
        m, tp = shard_isle(far, cx, top, hw, dp, ramp, ("swi", i), tilt=tilt, spurs=sp,
                           rim=mixc(rim_c, behind, 0.15 + hz * 0.3),
                           cap=hazed(R("#2a2040", "#8a6480"), behind, 0.2 + hz * 0.3) if hw > 10 else None)
        if hw > 10:
            g = rng("swchain", i)
            for _ in range(2):
                ax = cx + g.uniform(-0.55, 0.55) * hw
                col = m[:, int(ax) % W]
                ay = int(np.nonzero(col)[0].max()) if col.any() else top + dp // 2
                chain(far, dangle_pts(ax, ay, g.uniform(10, 26), sway=g.uniform(-3, 3)), hazed(chn, behind, 0.25))
    # snapped pier beams jutting off the big isles, a chain hanging from one or two
    for j, (x0, y0, x1, y1) in enumerate(((40, 42, 24, 45), (304, 22, 284, 27), (362, 24, 384, 19), (360, 30, 374, 34),
                                          (556, 60, 578, 55), (190, 104, 180, 107))):
        snapped_beam(far, x0, y0, x1, y1, wood, width=2)
        if j in (0, 2, 4):
            chain(far, dangle_pts(x1, y1 + 2, 9 + j, sway=1.5), chn)
    # two pagoda docks hanging half off their rocks
    for j, (px, py, ang, tiers, flip) in enumerate(((104, 36, 0.26, 3, 1), (484, 60, -0.3, 3, -1))):
        G = tilted_dock(far, px, py, ang, tiers, 11, dock_pal, dock_deck, window="#ffcf7a",
                        span=(6, 16) if flip > 0 else (16, 6))
        ex, ey = G(15 * flip, 2)
        chain(far, dangle_pts(ex, ey, 14 + j * 4, sway=flip * 1.0), chn)
        lx, ly = G(10 * flip, 1)
        lantern(far, int(round(lx)), int(round(ly)) + 1, R("#2a1a1a", "#ff8a3a", "#ffd07a"), glow="#ff9a4a")
    base_fade(far, 124, 172, horizon_haze, steps=4)
    sea = R("#9c6690", "#b87896", "#d48e98", "#eaa898", "#f8c29e", "#ffdcb4")
    cloud_floor(far, 170, 212, "swsea", sea, rows=9, r0=1.6, r1=5.5, stretch=2.8)
    base_fade(far, 166, 180, "#ffd6a4", steps=3, m=(far.a > 0) & (yy >= 166))
    sea_m = (far.a > 0) & (yy > 176)
    sea_ribbon(far, 180, "swr1", "#a070e0", core="#e0c8ff", thick=1.4, amp=1.5, clip=sea_m, alphas=(0.2, 0.3))
    sea_ribbon(far, 188, "swr2", "#40c8c0", core="#c8fff0", thick=1.8, amp=2, clip=sea_m, gaps=0.35,
               alphas=(0.2, 0.3))
    sea_glints(far, sea_m, "swfg", 26, R("#fff0d8", "#ffffff"), specks=60, speck_c="#fff4e4")
    layers.append((far, 0.08, 560))

    # ---------------- mid: the colossal wreck of a sky junk, broken-backed, lanterns lit by the pirates in it
    mh = 260
    mid = Canvas(W, mh)
    yy, _, _ = grids(mh)
    sky_junk(mid, 330, 200)
    sea_mid = R("#34286a", "#40307a", "#503a88", "#644694", "#80549c", "#b06ca2", "#f8b8ac")
    sea_cv = Canvas(W, mh)
    luminous_sea(sea_cv, 206, "swsea_m", sea_mid, [(6, 12, 12, 4), (8, 16, 14, 5), (10, 20, 16, 6)])
    haze_fade(sea_cv, sea_cv.a > 0, "#e89aa4", np.clip((222 - yy) / 26.0, 0, 1) * 0.55, steps=3, sharp=5)
    mid.paste(sea_cv)
    sm = (mid.a > 0) & (yy > 206)
    sea_ribbon(mid, 214, "swrm1", "#9a66e8", core="#e8d4ff", thick=4.0, amp=4, clip=sm, alphas=(0.12, 0.2, 0.28))
    sea_ribbon(mid, 234, "swrm2", "#3cc4c0", core="#d0fff4", thick=5.0, amp=4, clip=sm, gaps=0.4,
               alphas=(0.12, 0.2, 0.28))
    sea_glints(mid, sm, "swmg", 26, R("#ffe8d0", "#ffffff"), specks=90, speck_c="#fff0e8")
    layers.append((mid, 0.18, 620))

    # ---------------- near: the rim of the broken port, jagged piers, banners and rope lines over the sea
    nh = 200
    near = Canvas(W, nh)
    yy, _, _ = grids(nh)
    stone = R("#130f22", "#1b152c", "#231b36", "#2c2240", "#3a2d4e", "#54405e")
    nd = "#0c0918"
    rim_n = "#a86a7a"
    p1, c1 = broken_pier(near, 560, 150, 104, nh + 2, stone, "swp1", brk=(10, 16), slope=(1.2, 2.2), rim=rim_n, dark=nd)
    p2, _ = broken_pier(near, 262, 300, 80, nh + 2, stone, "swp2", brk=(8, 10), slope=(2.6, 2.0), notches=1,
                         rim=rim_n, dark=nd)
    arch = (wellipse(nh, 322, 108, 30, 26) & ~wellipse(nh, 322, 114, 22, 22) & (yy < 108)
            & (xx_all(nh) >= 296) & (xx_all(nh) < 330 + (pn1("swarch", 3, 1) * 4).astype(int)[None, :]))
    arch = despeck(arch & ~p2)
    ashlar(near, arch, stone[:5], "swarch", course=9, joint=32)
    flat(near, top_rim(arch), rim_n)
    flat(near, bot_rim(arch) | right_rim(arch), stone[0])
    p3, _ = broken_pier(near, 438, 522, 116, nh + 2, stone, "swp3", brk=(14, 8), slope=(1.6, 1.4), rim=rim_n, dark=nd)
    p2 |= arch
    # stone bollards on the quay, a snapped mooring rope, a chain hanging off the broken end
    for bx in (70, 88, 470):
        col = near.a[:, bx % W] > 0
        by = int(np.argmax(col)) if col.any() else 150
        bm = wrect(nh, bx - 1, by - 4, bx + 2, by - 1) | wrect(nh, bx - 2, by - 5, bx + 3, by - 5)
        flat(near, bm, stone[3])
        flat(near, left_rim(bm), stone[5])
        flat(near, right_rim(bm), stone[0])
        flat(near, top_rim(bm), rim_n)
    rope_line(near, [(71, c1[71] - 3), (60, c1[60] + 2), (52, c1[52] + 12), (48, c1[48] + 24)], "#4a3440")
    chain(near, dangle_pts(150, int(c1[146]) + 6, 30, sway=-2), R("#0e0a18", "#2a2036", "#5a4a64"), heavy=True)
    pole = R("#140e18", "#2a1e26", "#5a4038")
    cloth = R("#161436", "#221f4c", "#302d66", "#46448a")
    bans = []
    for i, (bx, ht) in enumerate(((36, 70), (112, 56), (282, 74), (484, 54))):
        col = near.a[:, bx % W] > 0
        by = int(np.argmax(col)) if col.any() else 150
        war_banner(near, bx, by + 1, ht, pole, cloth, "#ece2c8", ("swb", i), bl=30 if i % 2 == 0 else 24,
                   bw=10 if i % 2 == 0 else 8, trim="#c8b894")
        bans.append((bx, by - ht + 10))
    rope = "#4a3440"
    pen = R("#86283a", "#e8d6bc", "#2e2c66")
    rope_line(near, sag_pts(bans[0][0] + 1, bans[0][1], bans[1][0], bans[1][1] + 6, 10), rope, pennants=pen, seed=1)
    rp = sag_pts(bans[1][0] + 1, bans[1][1] + 6, bans[2][0], bans[2][1], 26)
    rope_line(near, rp, rope)
    lantern(near, int(rp[len(rp) // 2][0]), int(rp[len(rp) // 2][1]) + 1, R("#2a1a1a", "#ff8a3a", "#ffd07a"),
            glow="#ff9a4a")
    rp = sag_pts(bans[2][0] + 1, bans[2][1] + 4, bans[3][0], bans[3][1] + 8, 20)
    rope_line(near, rp, rope, pennants=pen, seed=3)
    sea_near = R("#221a50", "#2c2060", "#382870", "#46307e", "#583a88", "#7a4c94", "#e098a8")
    luminous_sea(near, 148, "swsea_n", sea_near, [(10, 20, 16, 6), (12, 24, 18, 7), (14, 26, 18, 7)])
    sn = (near.a > 0) & (yy > 160) & ~p1 & ~p2 & ~p3
    sea_glints(near, sn, "swng", 10, R("#ffe8d0", "#ffffff"), specks=24, speck_c="#fff0e8")
    layers.append((near, 0.32, 720))
    return dict(sky="#0f0e29", horizon="#ffd293", layers=layers)


def ringed_body(cv, cx, cy, r, pal, bands, ring, tilt=-0.22, rx=2.1, ry=0.34, halo=None, seed=0):
    """A great ringed star-body: a pale banded disc lit from the upper left with a crescent of shade on the lower
    right, and a thin tilted ring (with a dark division) whose far arc passes behind the disc and near arc in
    front, casting a thin shadow across it. pal = (shade, body, light); bands = (dark, light);
    ring = (dark, mid, light)."""
    h = cv.h
    yy, xx, _ = grids(h)
    dx = wdx(xx, cx)
    dy = yy - cy
    c, s_ = math.cos(tilt), math.sin(tilt)
    ru = c * dx + s_ * dy
    rv = -s_ * dx + c * dy
    e = np.sqrt((ru / (r * rx)) ** 2 + (rv / (r * ry)) ** 2)
    ring_m = (e <= 1.0) & (e >= 0.74)
    div = (e >= 0.86) & (e < 0.9)
    disc_m = dx ** 2 + dy ** 2 <= r * r
    if halo is not None:
        for sc, a in ((1.9, 0.04), (1.45, 0.07), (1.18, 0.1)):
            flat(cv, (dx ** 2 + dy ** 2 <= (r * sc) ** 2), halo, a)

    def draw_ring(m):
        flat(cv, m, ring[1])
        flat(cv, m & (ru < -r * 0.9), ring[2])
        flat(cv, m & (ru > r * 1.3), ring[0])
        flat(cv, m & div, ring[0])

    draw_ring(ring_m & (rv < 0) & ~disc_m)
    # the disc: latitude bands parallel to the ring, lit upper left, shade crescent lower right
    wob = (pn2(h, ("rbw", seed), 10, 3, 1) - 0.5) * 0.12
    lat = rv / r + wob
    bidx = np.floor(lat * 5.5)
    v = np.full((h, W), 1.0)
    v = v + np.where(bidx % 3 == 0, -0.55, np.where(bidx % 3 == 1, 0.35, 0.0))
    lit = (dx + dy * 1.1) / r
    v = v - np.clip(lit, 0, None) * 0.9 + np.clip(-lit - 0.35, 0, None) * 1.2
    ramp = [C(pal[0]), C(bands[0]), C(pal[1]), C(bands[1]), C(pal[2])]
    paint(cv, disc_m, ramp, v + 1.0, sharp=9)
    cres = disc_m & ~((wdx(xx, cx - r * 0.3) ** 2 + (yy - cy + r * 0.28) ** 2) <= (r * 1.02) ** 2)
    flat(cv, cres, pal[0])
    flat(cv, cres & ~sh(cres, 1, 1) & ~sh(cres, -1, -1), mixc(pal[0], "#000000", 0.25))
    # the ring's shadow on the disc, just below its near arc
    shadow = disc_m & (np.abs(rv - r * ry * 0.95) < 1.2) & (np.abs(ru) < r) & ~cres
    flat(cv, shadow, bands[0], 0.8)
    draw_ring(ring_m & (rv >= 0))
    return disc_m | ring_m


def lantern_field(cv, cx, cy, w, ht, seed, pal, glow, count=26):
    """A far-off shoal of lantern-lights low on the horizon: warm specks scattered in a flat drift, a few brighter
    with tiny crosses, over a faint stepped glow. pal = (dim, mid, bright)."""
    h = cv.h
    g = rng("lfield", seed)
    for (sc, a) in ((1.0, 0.05), (0.66, 0.07), (0.38, 0.09)):
        flat(cv, wellipse(h, cx, cy, w * sc, ht * sc * 1.4), glow, a)
    for i in range(count):
        x = cx + g.normal(0, w * 0.38)
        y = cy + g.normal(0, ht * 0.35) - abs(x - cx) / max(1.0, w) * ht * 0.2
        k = int(g.integers(0, 3)) if i % 7 else 2
        put(cv, x, y, pal[k])
        if i % 7 == 0:
            for dx, dy in ((1, 0), (-1, 0), (0, -1)):
                put(cv, x + dx, y + dy, pal[0])


def islet_shrine(cv, cx, top, hw, base, ramp, seed, shrine, window, lan=None, glow=None, tiers=2, w0=9,
                 pine_pal=None, trunk=None):
    """A lonely rock islet standing out of the Starsea: a craggy stack with a shoulder, a small pagoda shrine with
    a lit window on its crown, a lantern on a pole beside it and perhaps a wind-bent pine. shrine = pagoda
    (dark, mid, light). Returns (mask, profile)."""
    m, prof = karst_peak(cv, cx, top, hw, ramp, ("isl", seed), base=base, p=1.9, skirt=1.6, skirt_h=0.3,
                         rough=1.8, gain=1.3, crevice=1.2, shoulder=1.0, ledges=0.4, asym=0.2)
    sx = int(cx - hw * 0.12)
    ty = int(prof[sx % W])
    pagoda(cv, sx, ty + 1, tiers, w0, shrine, windows=window)
    if pine_pal is not None:
        px_ = int(cx + hw * 0.32)
        pine(cv, px_, int(prof[px_ % W]) + 2, int(hw * 0.9), pine_pal, trunk, ("islp", seed), lean=0.6, pads=3,
             pad_w=hw * 0.35)
    if lan is not None:
        lx = sx - int(w0 / 2) - 4
        ly = int(prof[lx % W])
        flat(cv, wrect(cv.h, lx, ly - 9, lx, ly), shrine[0])
        flat(cv, wrect(cv.h, lx, ly - 9, lx + 2, ly - 9), shrine[0])
        lantern(cv, lx + 2, ly - 8, lan, glow=glow)
    return m, prof


def starsea():
    """The open Starsea on a voyage: an indigo void full of stars and nebulae, a veiled ringed star-body, the Jade
    River as a band of stars, luminous cloud reefs drifting at every depth, lonely shrine islets, and far on the
    horizon the warm glimmer of the Lantern Star Field."""
    layers = []
    stops = [(0.0, "#07061a"), (0.15, "#0c0a26"), (0.3, "#130f33"), (0.42, "#1b1542"), (0.52, "#241c50"),
             (0.58, "#2e245e"), (0.62, "#3a326c"), (0.645, "#4a4a80"), (0.66, "#5e6a96"), (0.7, "#7488a8"),
             (1.0, "#56689a")]
    sky = sky_layer(stops, bands=26, sharp=2.4)
    stars(sky, "ssst", 700, 0, 226, R("#2c2c60", "#56589a", "#9a9ed0", "#d8dcf4", "#ffffff"), twinkle=8)
    nv = nebula(sky, "ssn_v", 110, 30, 28, "#a060f0", alphas=(0.06, 0.09, 0.13), k=(1, 2), cell=80, gaps=0.2)
    nt = nebula(sky, "ssn_t", 170, 18, 20, "#30d0c8", alphas=(0.06, 0.09, 0.12), k=(1, 3), cell=90, gaps=0.25)
    nr = nebula(sky, "ssn_r", 204, 8, 11, "#f06a9a", alphas=(0.06, 0.09, 0.12), k=(2, 3), cell=70, gaps=0.35)
    g = rng("ssnst")
    for m_, cols_ in ((nv, R("#8a6ad0", "#c8b0f4")), (nt, R("#4ab8b4", "#b8f4ec")), (nr, R("#c06a94", "#f8c0d4"))):
        ys, xs = np.nonzero(m_)
        for i in range(min(len(xs), 160)):
            j = int(g.integers(0, len(xs)))
            put(sky, xs[j], ys[j], cols_[0] if i % 4 else cols_[1])
    star_river(sky, "ssjr", 70, 30, 15, "#62dc92", R("#2a5250", "#387462", "#56a07c", "#92d8a6", "#daf8e0",
                                                     "#ffffff"), alphas=(0.06, 0.1, 0.15), density=0.75)
    ringed_body(sky, 468, 92, 30, R("#6a6698", "#c4c0de", "#f2f0fa"), R("#9c96c2", "#dcd8ee"),
                R("#7a70a8", "#b8b0d8", "#ece8f8"), tilt=-0.24, halo="#8a84c8", seed="ssrb")
    # veiled: a drift of nebula dust and thin cloud streaks across the body's lower half
    veil = nebula(Canvas(W, SKY_H), "ssveil", 104, 5, 8, "#000000", alphas=(1.0,), k=(1, 2), cell=50, gaps=0.0)
    vx = np.abs(wdx(xx_all(SKY_H), 470))
    flat(sky, veil & (vx < 80), "#221a4c", 0.5)
    flat(sky, veil & (vx < 60) & (pn2(SKY_H, "ssveil2", 30, 3, 1) > 0.5), "#221a4c", 0.35)
    for i, (cx, y, ln) in enumerate(((452, 108, 96), (494, 118, 72), (300, 196, 150))):
        streak(sky, cx, y, ln, R("#221a4c", "#40387a", "#8a86c0"), ("sss", i), rows=2)
    lantern_field(sky, 196, 224, 40, 5, "sslf", R("#a0582c", "#ffa84a", "#ffe6a0"), "#ff9a4a", count=34)
    layers.append((sky, 0.0, 720))

    # ---------------- far: the Starsea's horizon, lonely islets with lamp-lit shrines, glints on the cloud floor
    fh = 220
    far = Canvas(W, fh)
    yy = grids(fh)[0]
    isl = R("#1c1a3c", "#242248", "#2e2c56", "#3a3a64", "#4a4c74", "#606a8a")
    roof = R("#141230", "#221f44", "#3c3a62", "#5a5a82")
    lan = R("#2a1a1a", "#ff8a3a", "#ffd07a")
    haze = "#5e6a96"
    for i, (cx, top, hw) in enumerate(((290, 140, 9), (520, 150, 7), (590, 162, 5))):
        ramp = hazed(isl, haze, 0.25 + i * 0.12)
        if i < 2:
            islet_shrine(far, cx, top, hw, 184, ramp, ("ssfi", i), hazed(roof[:3], haze, 0.25), "#ffc070",
                         lan=lan if i == 0 else None, glow="#ff9a4a", tiers=2 if i == 0 else 1, w0=6 if i == 0 else 5)
        else:
            karst_peak(far, cx, top, hw, ramp, ("ssfr", i), base=184, p=2.0, rough=1.0, shoulder=0.0)
    base_fade(far, 150, 182, "#6a7aa4", steps=3)
    sea_f = R("#2a2a64", "#343a78", "#40508a", "#56689e", "#7e9cb8", "#c0e4e0")
    cloud_floor(far, 174, 214, "sssea", sea_f, rows=9, r0=1.6, r1=5.5, stretch=2.8)
    base_fade(far, 170, 180, "#7890b4", steps=3, m=(far.a > 0) & (yy >= 170))
    fm = (far.a > 0) & (yy > 178)
    sea_ribbon(far, 186, "ssr1", "#a070f0", thick=1.6, amp=2.5, clip=fm, alphas=(0.16, 0.24))
    sea_ribbon(far, 198, "ssr2", "#3ed8cc", thick=2.2, amp=3, clip=fm, gaps=0.35, alphas=(0.16, 0.24))
    sea_glints(far, fm, "ssfg", 30, R("#cfe8ff", "#ffffff"), specks=80, speck_c="#e8f4ff")
    layers.append((far, 0.08, 560))

    # ---------------- mid: cloud reefs drifting on the sea, a lonely shrine islet with its lanterns
    mh = 220
    mid = Canvas(W, mh)
    yy, _, _ = grids(mh)
    isl_m = R("#141230", "#1c1a3e", "#26244c", "#32325c", "#42446c", "#5a6284", "#7a86a0")
    night_pine = R("#0a1220", "#0e1828", "#132032", "#1a2a3c", "#223646", "#2e4652")
    islet_shrine(mid, 120, 118, 24, 200, isl_m, "ssmi", R("#100e26", "#1e1c3c", "#4a4a72"), "#ffc070", lan=lan,
                 glow="#ff9a4a", tiers=3, w0=10, pine_pal=night_pine,
                 trunk=R("#141220", "#1e1a2a", "#2c2636", "#3c3444"))
    reef = R("#1c1848", "#24225c", "#2c3070", "#36407e", "#42568e", "#5476a4", "#b4e6dc")
    deep = R("#140f3c", "#181546", "#1c1b50", "#21215a", "#272964", "#2f346e", "#46588a")
    luminous_sea(mid, 176, "sssea_m", deep, [(5, 10, 10, 3), (6, 12, 12, 4), (8, 14, 14, 4), (9, 16, 16, 4)])
    for i, (cx, w, b, rows, r0, r1) in enumerate(((330, 64, 176, 3, 6, 11), (548, 40, 180, 2, 5, 9),
                                                  (36, 34, 184, 2, 5, 8), (214, 30, 196, 2, 7, 11),
                                                  (440, 52, 206, 2, 8, 13))):
        cloud_bank(mid, b - rows * 9, ("ssreef", i), reef, r_lo=r0, r_hi=r1, rows=rows, row_gap=9, amp=3,
                   skip=lambda x, k, cx=cx, w=w, rows=rows: abs(wdx(x, cx)) > w * (0.45 + 0.55 * (k + 1) / rows))
    for i, (cx, y, ln) in enumerate(((420, 170, 110), (600, 178, 80), (180, 186, 90))):
        streak(mid, cx, y, ln, R("#2c3470", "#5a7aa8", "#b0dcdc"), ("ssms", i), rows=2)
    sm = (mid.a > 0) & (yy > 150)
    sea_ribbon(mid, 190, "ssrm1", "#a070f0", core="#e8d4ff", thick=3.0, amp=4, clip=sm, alphas=(0.14, 0.22, 0.3))
    sea_ribbon(mid, 208, "ssrm2", "#3ed8cc", core="#d0fff4", thick=4.0, amp=5, clip=sm, gaps=0.4,
               alphas=(0.14, 0.22, 0.3))
    sea_glints(mid, sm, "ssmg", 30, R("#cfe8ff", "#ffffff"), specks=110, speck_c="#e8f4ff")
    layers.append((mid, 0.18, 620))

    # ---------------- near: a heavy swell of cloud reef for the deck to ride, spray streaming off its crests
    nh = 200
    near = Canvas(W, nh)
    yy, _, _ = grids(nh)
    reef_n = R("#140f3a", "#1a164c", "#211f5e", "#292c70", "#343e82", "#465a96", "#a8e4dc")
    deep_n = R("#0f0b30", "#130f3a", "#171444", "#1c1a4e", "#222258", "#2a2c64", "#48608e")
    luminous_sea(near, 148, "sssea_n", deep_n, [(12, 22, 12, 5), (14, 24, 14, 6), (16, 28, 16, 6)])
    for i, (cx, w, b) in enumerate(((120, 84, 164), (452, 64, 170))):
        cloud_bank(near, b - 30, ("ssnreef", i), reef_n, r_lo=10, r_hi=18, rows=2, row_gap=14, amp=4,
                   skip=lambda x, k, cx=cx, w=w: abs(wdx(x, cx)) > w * (0.6 + 0.4 * k))
    # spray streaming off the reef summits and low streamers: the wind of the voyage
    wisp = R("#3c4c86", "#7ea6c4", "#d0f2ec")
    for i, (cx, ln) in enumerate(((104, 120), (452, 96), (300, 70))):
        col = near.a[:, cx % W] > 0
        y0 = int(np.argmax(col)) if col.any() else 150
        streak(near, cx + ln * 0.5 - 4, y0 + 1, ln, wisp, ("ssw", i), rows=2)
    sn = (near.a > 0) & (yy > 130)
    sea_glints(near, sn, "ssng", 16, R("#cfe8ff", "#ffffff"), specks=60, speck_c="#e8f4ff")
    layers.append((near, 0.32, 720))
    return dict(sky="#07061a", horizon="#5e6a96", layers=layers)


# =============================================================== the Lantern Star Field (Act III)
LS_STAR = R("#f6c667", "#ffe4a0", "#fff5d6", "#ffffff")              # a fallen star: deep, body, core, white
LS_CAGE = R("#22150c", "#4a301a", "#76502a", "#aa7838", "#e4b460")   # old bronze: shadow .. gleam
LS_VERD = "#4d8676"                                                  # verdigris on the old bronze
LS_GLOW = "#ffd889"
LS_STARS = R("#2c2c60", "#56589a", "#9a9ed0", "#d8dcf4", "#ffffff")
JADE_STARS = R("#2a5250", "#387462", "#56a07c", "#92d8a6", "#daf8e0", "#ffffff")


def ring_px(m):
    """The 4-connected inner boundary of a mask: a clean 1 px outline."""
    return m & ~(sh(m, 1, 0) & sh(m, -1, 0) & sh(m, 0, 1) & sh(m, 0, -1))


def under_stars(cv, seed, count, y0, y1, pal, twinkle=8):
    """Stars under the field's glow line (the sea here is sky): sparse near the glow at y0, fuller toward y1."""
    g = rng("ustars", seed)
    for i in range(count):
        x = int(g.integers(0, W))
        y = int(g.integers(y0, y1))
        if g.random() < (y1 - y) / max(1, y1 - y0) * 0.85:
            continue
        put(cv, x, y, pal[int(g.integers(0, len(pal) - 1))])
        if i % twinkle == 0:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                put(cv, (x + dx) % W, y + dy, pal[0])
            put(cv, x, y, pal[-1])


def field_sky(stops, seed, glow_y, up=520, down=260, pal=None, bands=28):
    """The night of the Lantern Star Field: a gradient that brightens toward a glow line and sinks again below it
    (there is no ground: the islands float in sky all the way down), stars above and below the glow."""
    pal = LS_STARS if pal is None else pal
    sky = sky_layer(stops, bands=bands, sharp=2.4)
    stars(sky, (seed, "up"), up, 0, glow_y, pal, twinkle=8)
    under_stars(sky, (seed, "dn"), down, glow_y, SKY_H, pal, twinkle=9)
    return sky


def sky_at(stops, cv, bottom, y):
    """The sky colour behind row y of a layer drawn with its foot at screen row `bottom` (camera at rest)."""
    return lerp_stops(stops, (bottom / SCALE - cv.h + y) / (SKY_H - 1.0))


def lantern_star(cv, cx, cy, r, seed, lit=1.0, cage=None, star=None, glow=None, halo=1.0, rays=1.0, hang=None,
                 tether=None, sag=4.0, broken=0.0, ember=None, verd=LS_VERD):
    """A lantern star: a fallen star held in an old bronze cage, burning pale gold. A round cage of meridian ribs and
    latitude hoops (seen a little from below, so the near arcs ride high), a domed crown with its hanging ring and a
    finial spike beneath; the ribs catch the star on their inner faces, the rim is dark bronze flecked with
    verdigris; a stepped halo and thin cross rays spill out. lit in [0, 1] dims the star (0: gone out, an empty cage
    with an optional `ember` haze). hang = (x, y) the crown chain rises to; tether = (x, y) the mooring chain from
    the finial falls to; broken tears a wedge of ribs away. Returns the cage mask."""
    h = cv.h
    cage = LS_CAGE if cage is None else cage
    star = LS_STAR if star is None else star
    glow = LS_GLOW if glow is None else glow
    cx, cy, r = int(round(cx)), int(round(cy)), float(r)
    yy, xx, _ = grids(h)
    dx = wdx(xx, cx)
    dy = (yy - cy).astype(float)
    rr = np.sqrt(dx * dx + dy * dy)
    g = rng("lstar", seed)
    chn = R(cage[0], cage[2], cage[3])
    cap_h = max(1, int(round(r * 0.2)))
    ring_r = max(1.0, float(round(r * 0.13)))
    top = cy - int(round(r)) - cap_h
    fin = max(2, int(round(r * 0.4)))
    if hang is not None:
        chain(cv, [(cx, top - 2 * ring_r), (hang[0], hang[1])], chn, heavy=r >= 12)
    if tether is not None:
        chain(cv, sag_pts(cx, cy + r + fin, tether[0], tether[1], sag), chn, heavy=r >= 12)
    if lit > 0 and halo > 0:
        for s_, a in ((3.6, 0.035), (2.6, 0.06), (1.9, 0.09), (1.4, 0.13)):
            flat(cv, rr <= r * s_, glow, a * halo * lit)
    disc_m = rr <= r + 0.3
    inside = rr <= r - 0.7
    shell = ring_px(disc_m)
    ribs = np.zeros((h, W), bool)
    back = np.zeros((h, W), bool)
    if r >= 4:
        ribs |= (dx == 0) & inside
        for f in ((0.45, 0.8) if r >= 9 else (0.58,)):
            ribs |= ring_px((dx / (r * f + 0.3)) ** 2 + (dy / (r + 0.3)) ** 2 <= 1.0) & inside
        for lat in ((-0.5, 0.0, 0.5) if r >= 9 else (0.0,)):
            yc = cy + lat * r
            rx = r * math.sqrt(1 - lat * lat)
            ry = max(0.8, rx * 0.26)
            e = ring_px((dx / (rx + 0.3)) ** 2 + ((yy - yc) / (ry + 0.3)) ** 2 <= 1.0) & inside
            ribs |= e & (yy <= yc)
            back |= e & (yy > yc)
    if broken:
        ang = np.arctan2(dy, dx)
        a0 = g.uniform(-math.pi, math.pi)
        gap = np.abs((ang - a0 + math.pi) % (2 * math.pi) - math.pi) < broken * math.pi
        gap &= pn2(h, ("lsb", seed), 2, 2, 1) > 0.25
        ribs &= ~gap
        back &= ~gap
        shell &= ~(gap & (pn2(h, ("lsb2", seed), 3, 3, 1) > 0.4))
    flat(cv, back, cage[1])
    if lit > 0:
        flat(cv, inside, star[0], 0.45 * lit)
        flat(cv, rr <= r * 0.62, star[1], 0.5 * lit)
        spark = (np.sqrt(np.abs(dx)) + np.sqrt(np.abs(dy))) <= math.sqrt(max(1.0, r * 0.8 * lit))
        flat(cv, spark & inside, star[1])
        flat(cv, rr <= max(1.0, r * 0.3 * lit), star[2])
        flat(cv, rr <= max(0.5, r * 0.14 * lit), star[3])
        L = r * 2.6 * rays * lit
        for ln, a in ((L, 0.3), (L * 0.62, 0.5), (L * 0.36, 0.85)):
            m = ((dy == 0) & (np.abs(dx) <= ln)) | ((dx == 0) & (np.abs(dy) <= ln))
            flat(cv, m & ~ribs & ~shell & ~inside, star[2], a)
    elif ember is not None:
        flat(cv, inside, ember, 0.4)
    # rib colours: the near ribs stand dark against the star, catching its light only where they cross the core;
    # the far arcs behind the star are lit full on
    if lit > 0:
        flat(cv, back, cage[3], 0.6 * lit)
    ri = np.full((h, W), 1) + ((rr < r * 0.3) & (lit > 0.6)) * 2 + ((rr >= r * 0.3) & (rr < r * 0.62) & (lit > 0.3))
    cv.fill_idx(ribs, ri, cage)
    s_ = dx + dy
    flat(cv, shell, cage[2] if lit > 0.3 else cage[1])
    flat(cv, shell & (s_ < -r * 0.5), cage[3 + (lit > 0.5) * (r < 9)] if lit > 0 else cage[2])
    flat(cv, shell & (s_ > r * 0.6), cage[0])
    if lit > 0 and r >= 6:
        flat(cv, ring_px(inside) & ~ribs & (s_ > r * 0.2), cage[4], 0.7 * lit)   # the rim's inner lip, star-lit
    if r >= 7 and verd is not None:
        flat(cv, (ribs | shell) & (pn2(h, ("lsv", seed), 3, 3, 1) > 0.76), verd)
    cap = wellipse(h, cx, cy - r + 1, r * 0.34 + 1, cap_h + 1) & (yy <= cy - r + 1)
    flat(cv, cap, cage[2])
    flat(cv, cap & (dx < 0), cage[3])
    flat(cv, top_rim(cap) & (dx <= 0), cage[4] if lit > 0.5 else cage[3])
    flat(cv, right_rim(cap), cage[0])
    rm = ring_px(dx ** 2 + (yy - (top - ring_r)) ** 2 <= (ring_r + 0.3) ** 2)
    flat(cv, rm, cage[2])
    fw = max(1, int(round(r * 0.14)))
    finm = wpoly(h, [(cx - fw - 0.5, cy + r - 1), (cx + fw + 0.5, cy + r - 1), (cx + 0.5, cy + r + fin),
                     (cx - 0.5, cy + r + fin)])
    flat(cv, finm, cage[1])
    flat(cv, finm & (dx < 0), cage[3])
    return disc_m | cap | finm | rm


def field_isle(cv, cx, top, hw, depth, ramp, seed, warm, cool, haze=None, tilt=0.0, spurs=2, cap=None,
               under=0.45):
    """An island of the Lantern Star Field adrift over the lower sky: a slab with a faceted, spurred underside, its
    upper rim warmed by the lantern star above and its underside washed by the cool light of the nebulae below.
    Returns (mask, top row per column)."""
    m, tp = shard_isle(cv, cx, top, hw, depth, ramp, seed, tilt=tilt, spurs=spurs, rim=warm, cap=cap)
    if not m.any():
        return m, tp
    yy = grids(cv.h)[0]
    rel = np.clip((yy - tp[None, :]) / max(1.0, depth), 0, 1)
    if haze is not None:
        haze_fade(cv, m, haze, np.clip((rel - 0.3) / 0.7, 0, 1) * under, steps=3, sharp=4)
    flat(cv, bot_rim(m) & (rel > 0.25), cool)
    return m, tp


def roof_house(cv, x0, by, w, wall_h, roof_h, roof, wall, win=None, eave=2):
    """A harbour house in side view: a plastered wall with lamplit windows under a tiled roof (ribbed tile courses,
    lit tile ends along the eave, a dark ridge with upturned tips). roof = (dark, mid, light), wall = (dark, mid,
    light), win = (glow, bright). Returns its mask."""
    h = cv.h
    yy, xx, _ = grids(h)
    x1 = x0 + w - 1
    wall_m = wrect(h, x0, by - wall_h + 1, x1, by)
    flat(cv, wall_m, wall[1])
    flat(cv, left_rim(wall_m), wall[2])
    flat(cv, right_rim(wall_m), wall[0])
    flat(cv, wrect(h, x0, by - wall_h + 1, x1, by - wall_h + 1), wall[0])
    if win is not None:
        n = max(1, (w - 2) // 7)
        for k in range(n):
            wx = x0 + int(round((k + 0.5) * w / n)) - 1
            flat(cv, wrect(h, wx, by - wall_h + 3, wx + 1, max(by - wall_h + 3, by - 2)), win[0])
            put(cv, wx, by - wall_h + 3, win[1])
    ty = by - wall_h
    rm = wpoly(h, [(x0 - eave - 0.5, ty + 0.5), (x0 - eave + roof_h * 0.7, ty - roof_h + 0.5),
                   (x1 + eave - roof_h * 0.7, ty - roof_h + 0.5), (x1 + eave + 0.5, ty + 0.5)])
    flat(cv, rm, roof[1])
    flat(cv, rm & (xx % 2 == 0), roof[0])
    flat(cv, top_rim(rm), roof[2])
    flat(cv, bot_rim(rm) & (xx % 2 == 1), roof[2])
    ridge = wrect(h, int(round(x0 - eave + roof_h * 0.7)) - 1, ty - roof_h, int(round(x1 + eave - roof_h * 0.7)) + 1,
                  ty - roof_h)
    flat(cv, ridge, roof[0])
    for x_ in (x0 - eave - 1, x1 + eave + 1):
        put(cv, x_, ty - 1, roof[0])
    for x_ in (int(round(x0 - eave + roof_h * 0.7)) - 2, int(round(x1 + eave - roof_h * 0.7)) + 2):
        put(cv, x_, ty - roof_h - 1, roof[0])
    return wall_m | rm | ridge


def pier(cv, x0, x1, y, pal, posts=R("#1a1024", "#2c1c30"), drop=9, lamps=(), lan=None, glow=None):
    """A timber pier run out along row y from x0 to x1: a planked deck with a lit top edge and dark underside, posts
    and knee braces dropping beneath, and lantern posts at `lamps` x positions. pal = (dark, mid, light)."""
    h = cv.h
    xa, xb = min(x0, x1), max(x0, x1)
    deck = wrect(h, xa, y, xb, y + 1)
    for px in range(int(xa) + 3, int(xb), 8):
        flat(cv, wrect(h, px, y + 2, px, y + drop), posts[1])
        flat(cv, wline(h, [(px + 1, y + 2), (px + 4, y + 5)], 1), posts[0])
    flat(cv, deck, pal[1])
    flat(cv, top_rim(deck), pal[2])
    flat(cv, deck & (xx_all(h) % 4 == 0) & ~top_rim(deck), pal[0])
    for lx in lamps:
        flat(cv, wrect(h, lx, y - 9, lx, y - 1), pal[0])
        flat(cv, wrect(h, lx, y - 9, lx + 2, y - 9), pal[0])
        if lan is not None:
            lantern(cv, lx + 2, y - 8, lan, glow=glow)
    return deck


def junk(cv, x, wl, ln, seed, hull, sail, face=1, set_sails=True, lit=None, rig="#3a2a38", patch=None):
    """A sky-junk at its mooring, side view, its bow toward `face`: a deep hull whose sheer sweeps up to a high stern
    castle and a raked bow, a painted wale, two masts with batten sails (set, or reefed down to their booms), and a
    lamplit stern gallery. (x, wl) = midship at deck level. hull = (dark, mid, light), sail = (dark, mid, light);
    patch = colours of the pirates' patches sewn over torn sailcloth, their leeches ragged."""
    h = cv.h
    yy, xx, _ = grids(h)
    g = rng("junk", seed)

    def P(u, v):
        return x + face * u, wl + v

    L = ln / 2.0
    pts = [(-L, -ln * 0.2), (-L + ln * 0.05, -ln * 0.2), (-L + ln * 0.08, -ln * 0.06), (-ln * 0.2, 0.0),
           (ln * 0.25, 0.0), (L, -ln * 0.13), (L - ln * 0.06, ln * 0.02), (ln * 0.25, ln * 0.13), (-ln * 0.2, ln * 0.14),
           (-L + ln * 0.04, ln * 0.06)]
    hm = wpoly(h, [P(u, v) for u, v in pts])
    top_v = wl - ln * 0.2
    rel = np.clip((yy - wl) / max(1.0, ln * 0.14), -1, 1)
    paint(cv, hm, hull, 1.6 - rel * 1.2, sharp=4)
    wale = hm & (np.abs(yy - (wl + ln * 0.035)) < 0.6)
    flat(cv, wale, hull[0])
    flat(cv, top_rim(hm), hull[2])
    flat(cv, bot_rim(hm), hull[0])
    # stern castle with a lamplit gallery
    cu0, cu1 = -L + ln * 0.05, -L + ln * 0.3
    castle = wpoly(h, [P(cu0 + 1, -ln * 0.2 - ln * 0.08), P(cu1 - 1, -ln * 0.2 - ln * 0.08), P(cu1 - 1, -ln * 0.2),
                       P(cu0 + 1, -ln * 0.2)])
    flat(cv, castle, hull[1])
    flat(cv, top_rim(castle), hull[2])
    roof_m = wpoly(h, [P(cu0 - 1, -ln * 0.28), P(cu1 + 1, -ln * 0.28), P(cu1 - 1, -ln * 0.31), P(cu0 + 1, -ln * 0.31)])
    flat(cv, roof_m, hull[0])
    if lit is not None:
        for k in range(3):
            u = cu0 + 2 + k * (cu1 - cu0 - 3) / 3.0
            px_, py_ = P(u, -ln * 0.24)
            flat(cv, wrect(h, int(round(px_)), int(round(py_)), int(round(px_)), int(round(py_)) + 1), lit[0])
            put(cv, px_, py_, lit[1])
    # masts and sails
    for k, (mu, mh_, sw) in enumerate(((ln * 0.02, ln * 0.85, ln * 0.34), (ln * 0.3, ln * 0.62, ln * 0.24))):
        bx, by_ = P(mu, 0)
        tx, ty = P(mu, -mh_)
        flat(cv, wline(h, [(bx, by_), (tx, ty)], 1), hull[0])
        if set_sails:
            # a batten sail hung aft of the mast: a raked yard, battens fanning to a curved leech
            y0s, y1s = ty + 2, by_ - ln * 0.08
            sm = np.zeros((h, W), bool)
            for yv in range(int(y0s), int(y1s) + 1):
                t = (yv - y0s) / max(1.0, y1s - y0s)
                wv = sw * (0.55 + 0.45 * math.sin(t * math.pi * 0.9 + 0.2))
                if face > 0:
                    sm |= wrect(h, int(round(bx - wv)), yv, int(round(bx)) - 1, yv)
                else:
                    sm |= wrect(h, int(round(bx)) + 1, yv, int(round(bx + wv)), yv)
            if patch is not None:
                lee = left_rim(sm) if face > 0 else right_rim(sm)
                rag = lee & (pn2(h, ("jrag", seed, k), 1.5, 2, 1) > 0.55)
                sm &= ~rag & ~(sh(rag, face, 0) & (pn2(h, ("jrg2", seed, k), 2, 2, 1) > 0.6))
            flat(cv, sm, sail[1])
            flat(cv, sm & ((yy - int(y0s)) % 4 == 0), sail[0])
            flat(cv, (left_rim(sm) if face > 0 else right_rim(sm)), sail[2])
            flat(cv, top_rim(sm), sail[2])
            if patch is not None:
                for j in range(3):
                    pw, ph_ = int(g.integers(3, 7)), int(g.integers(3, 6))
                    px0 = int(round(bx - face * g.uniform(3, sw * 0.8))) - (pw if face > 0 else 0)
                    py0 = int(g.uniform(y0s + 2, max(y0s + 3, y1s - ph_)))
                    pm = wrect(h, px0, py0, px0 + pw, py0 + ph_) & sm
                    flat(cv, pm, patch[j % len(patch)])
                    flat(cv, ring_px(pm) & ((xx + yy) % 2 == 0), sail[0])
        else:
            for j in range(3):
                flat(cv, wline(h, [(bx, by_ - ln * 0.1 - j), (bx - face * sw * 0.8, by_ - ln * 0.1 - j)], 1),
                     sail[j % 2])
        # stays to the bow and stern
        flat(cv, wline(h, [(tx, ty), P(L, -ln * 0.13)], 1), rig, 0.8)
        if k == 0:
            flat(cv, wline(h, [(tx, ty), P(-L + ln * 0.05, -ln * 0.28)], 1), rig, 0.8)
    return hm


def lantern_harbor():
    """Lanternfall Harbor: a harbour town on a floating island at night under its great lantern star, tiled roofs
    and lamplit windows, piers strung with lanterns and sky-junks at their moorings; the field's islands and their
    lantern stars drift off into the violet dark above and below, the Jade River a ribbon of stars overhead."""
    layers = []
    stops = [(0.0, "#08071e"), (0.16, "#0e0c2c"), (0.3, "#16123a"), (0.42, "#221a4a"), (0.5, "#2e2258"),
             (0.56, "#402a62"), (0.6, "#563468"), (0.635, "#744268"), (0.66, "#98566a"), (0.672, "#b4706e"),
             (0.686, "#96566a"), (0.71, "#683e66"), (0.76, "#3e2e5c"), (0.86, "#221a48"), (1.0, "#110e30")]
    glow_y = 242
    sky = field_sky(stops, "lh", glow_y, up=520, down=240)
    nebula(sky, "lhn_v", 116, 22, 20, "#8a58e0", alphas=(0.05, 0.08, 0.11), k=(1, 2), cell=80, gaps=0.2)
    lo_v = nebula(sky, "lhn_lo", 300, 16, 26, "#7a4ad0", alphas=(0.05, 0.08, 0.11), k=(1, 3), cell=90, gaps=0.2)
    lo_t = nebula(sky, "lhn_lt", 330, 10, 18, "#30b8c0", alphas=(0.05, 0.08, 0.1), k=(2, 3), cell=70, gaps=0.3)
    g = rng("lhnst")
    for m_, cols_ in ((lo_v, R("#8a6ad0", "#c8b0f4")), (lo_t, R("#4ab8b4", "#b8f4ec"))):
        ys, xs = np.nonzero(m_)
        for i in range(min(len(xs), 120)):
            j = int(g.integers(0, len(xs)))
            put(sky, xs[j], ys[j], cols_[0] if i % 4 else cols_[1])
    star_river(sky, "lhjr", 58, 22, 12, "#62dc92", JADE_STARS, alphas=(0.04, 0.07, 0.1), density=0.55)
    for i, (cx, y, ln) in enumerate(((150, 206, 170), (430, 222, 210), (600, 196, 110))):
        streak(sky, cx, y, ln, R("#e0a07a", "#7a4a6e", "#b8726e"), ("lhs", i), rows=2)
    for i, (cx, cy, w) in enumerate(((90, 236, 30), (340, 246, 44), (520, 232, 22))):
        lantern_field(sky, cx, cy, w, 4, ("lhlf", i), R("#a0582c", "#ffa84a", "#ffe6a0"), "#ff9a4a", count=18)
    layers.append((sky, 0.0, 720))

    # ---------------- far: the field's islands adrift at every height, each under its own lantern star
    fh = 220
    far = Canvas(W, fh)
    yy = grids(fh)[0]
    rock = R("#1a1434", "#221a40", "#2c224c", "#382a58", "#463464", "#584074")
    isles = [(40, 112, 24, 32, -0.05), (132, 150, 13, 16, 0.08), (250, 92, 30, 38, 0.04), (360, 158, 12, 14, -0.1),
             (452, 118, 22, 28, 0.06), (560, 170, 10, 12, 0.1), (196, 184, 7, 8, 0.0), (600, 76, 16, 20, -0.06),
             (318, 44, 9, 12, 0.05), (512, 52, 7, 9, -0.08), (100, 40, 6, 8, 0.1), (416, 196, 6, 7, 0.0)]
    for i, (cx, top, hw, dp, tilt) in enumerate(isles):
        behind = sky_at(stops, far, 560, top + dp * 0.5)
        hz = np.clip(abs(top + 60 - glow_y) / 130.0, 0, 1)
        ramp = hazed(rock, behind, 0.3 + (1 - hz) * 0.3)
        m, tp = field_isle(far, cx, top, hw, dp, ramp, ("lhfi", i), mixc("#ffc878", behind, 0.35),
                           mixc("#8a70c8", behind, 0.4), tilt=tilt, spurs=1 + (hw > 15))
        if hw >= 12:
            for k in range(int(hw // 8)):
                hx = int(cx - hw * 0.62 + k * 8 + 2)
                roof_house(far, hx, int(tp[hx % W]) + 1, 5, 3, 2, hazed(R("#140f2c", "#241c40", "#6a5070"), behind, 0.3),
                           hazed(R("#3a3050", "#5a4c68", "#7a6a80"), behind, 0.3), win=("#e8a050", "#ffd890"), eave=1)
        side = 1 if i % 2 else -1
        sx, sy = cx + side * hw * 0.3, top - 14 - hw * 0.4
        lantern_star(far, sx, sy, 2.2 + hw * 0.07, ("lhfs", i), halo=0.8, rays=0.8,
                     tether=(cx - side * hw * 0.2, top), sag=3.0 + hw * 0.1)
    layers.append((far, 0.08, 560))

    # ---------------- mid: the harbour island, its town, piers and junks, the great lantern star above
    mh = 300
    mid = Canvas(W, mh)
    yy, xx, _ = grids(mh)
    icx, itop, ihw = 300, 204, 178
    rock_m = R("#140f2a", "#1c1534", "#251c40", "#30244c", "#3e2e58", "#503a66", "#664a74")
    isle, itp = field_isle(mid, icx, itop, ihw, 74, rock_m, "lhmi", "#f0b870", "#7a62c0", haze="#3a2c64", spurs=3,
                           cap=R("#3a2a3a", "#8a6a5a"))
    roof = R("#161430", "#262448", "#5a5478")
    roof_w = R("#2a1a1a", "#3e2620", "#8a5238")
    wall = R("#4a3a48", "#7a6670", "#a8948e")
    win = ("#f0a050", "#ffe0a0")
    lan = R("#2a1a1a", "#ff8a3a", "#ffd07a")
    stone = R("#241c34", "#302642", "#3e3250", "#524464", "#6c5a78")
    gy = int(itp[icx % W])
    # the town climbs two terraces of dressed stone to the harbour hall
    terr = [(icx - 118, icx + 128, gy - 13), (icx - 58, icx + 62, gy - 27)]
    for k, (xa, xb, ty) in enumerate(terr):
        tm = wrect(mh, xa, ty, xb, gy if k == 0 else terr[0][2])
        masonry(mid, tm, stone, ("lhter", k), course=3, joint=7)
        flat(mid, top_rim(tm), "#b08a6a")
        for lx in range(xa + 6, xb - 4, 22):
            lantern(mid, lx, ty + 3, lan)
    stairs(mid, icx - 86, gy, icx - 72, terr[0][2] + 1, (stone[0], stone[2], stone[4]), width=5)
    stairs(mid, icx + 20, terr[0][2], icx + 30, terr[1][2] + 1, (stone[0], stone[2], stone[4]), width=5)
    hall(mid, icx - 28, terr[1][2], 56, 10, 8, R("#161430", "#262448", "#5a5478", "#8a86a8"),
         R("#6a5660", "#a8948e", "#cbb8ac"), post_col="#7a2e28", lit="#f0a050", tiers=2)
    g = rng("lhtown")
    for xa, xb in ((terr[1][0] + 2, icx - 34), (icx + 34, terr[1][1] - 4)):
        x = xa
        while x < xb - 10:
            w = int(g.integers(12, 17))
            roof_house(mid, int(x), terr[1][2], w, 6, 4, roof, wall, win=win)
            x += w + 4
    x = terr[0][0] + 4
    while x < terr[0][1] - 12:
        w = int(g.integers(14, 22))
        if not (terr[1][0] - 6 < x + w / 2 < terr[1][1] + 6):
            roof_house(mid, int(x), terr[0][2], w, int(g.integers(6, 9)), int(g.integers(4, 6)),
                       roof if g.random() < 0.6 else roof_w, wall, win=win)
        x += w + int(g.integers(4, 7))
    pagoda(mid, icx + 104, terr[0][2], 4, 12, R("#161430", "#3a3456", "#7a7098"), windows="#ffd890")
    # the waterfront row, with lanes left open up to the stairs
    x = icx - ihw + 10
    while x < icx + ihw - 14:
        w = int(g.integers(12, 20))
        if abs(x + w / 2 - (icx - 80)) > 16 and abs(x + w / 2 - (icx + 24)) > 14:
            roof_house(mid, int(x), int(itp[int(x + w / 2) % W]) - 1, w, int(g.integers(5, 7)), int(g.integers(3, 5)),
                       roof_w if g.random() < 0.5 else roof, wall, win=win)
        x += w + int(g.integers(2, 6))
    # piers run out from both ends of the island, lanterns on their posts, junks at the moorings
    lx0, rx0 = icx - ihw + 4, icx + ihw - 4
    ly, ry = int(itp[lx0 % W]) + 2, int(itp[rx0 % W]) + 3
    pier(mid, lx0 - 70, lx0, ly, R("#241620", "#4a3028", "#8a6040"), lamps=(lx0 - 64, lx0 - 38, lx0 - 12), lan=lan,
         glow="#ff9a4a")
    pier(mid, rx0, rx0 + 84, ry, R("#241620", "#4a3028", "#8a6040"), lamps=(rx0 + 18, rx0 + 46, rx0 + 76), lan=lan,
         glow="#ff9a4a")
    hullp = R("#1c1224", "#3a2632", "#7a5048")
    junk(mid, lx0 - 40, ly - 3, 58, "lhj1", hullp, R("#5a2a2e", "#8a3e36", "#c8704a"), face=-1, lit=win)
    junk(mid, rx0 + 52, ry - 2, 50, "lhj2", hullp, R("#3a3a5a", "#6a6a86", "#b0b0c0"), face=1, set_sails=False, lit=win)
    # strings of lanterns across the town's lanes
    for (xa, xb, s_) in ((icx - 120, icx - 40, 8), (icx + 30, icx + 110, 7)):
        ya, yb = int(itp[xa % W]) - 18, int(itp[xb % W]) - 18
        pts = sag_pts(xa, ya, xb, yb, s_)
        rope_line(mid, pts, "#3a2838")
        for j in range(3, len(pts) - 2, 5):
            lantern(mid, int(round(pts[j][0])), int(round(pts[j][1])) + 1, lan)
    # the great lantern star, moored to the island by two heavy chains
    lantern_star(mid, icx - 20, 78, 22, "lhgreat", hang=None, tether=(icx - 110, int(itp[(icx - 110) % W]) - 4),
                 sag=14, rays=1.2)
    chain(mid, sag_pts(icx - 20, 78 + 22 + 9, icx + 70, int(itp[(icx + 70) % W]) - 6, 16), R("#22150c", "#76502a",
                                                                                              "#aa7838"), heavy=True)
    layers.append((mid, 0.18, 620))

    # ---------------- near: mooring posts, a lantern rope and the lamplit swell of nebula below the quay
    nh = 200
    near = Canvas(W, nh)
    yy, _, _ = grids(nh)
    sea_n = R("#130e34", "#191242", "#21184e", "#2c1f5a", "#3c2a66", "#5a3c72", "#c08a86")
    luminous_sea(near, 150, "lhsea_n", sea_n, [(10, 20, 14, 5), (12, 24, 16, 6), (14, 26, 18, 6)])
    sn = (near.a > 0)
    sea_ribbon(near, 174, "lhrn1", "#9a66e8", core="#e8d4ff", thick=4.0, amp=4, clip=sn, alphas=(0.1, 0.18, 0.26))
    sea_glints(near, sn, "lhng", 12, R("#ffe8d0", "#ffffff"), specks=40, speck_c="#fff0e8")
    post = R("#120c1c", "#22182c", "#3e2c3c", "#8a6040")
    tops = []
    for i, (px, top) in enumerate(((70, 96), (330, 110), (560, 90))):
        pm = wrect(nh, px - 3, top, px + 3, nh)
        flat(near, pm, post[1])
        flat(near, left_rim(pm), post[2])
        flat(near, right_rim(pm), post[0])
        capm = wrect(nh, px - 4, top - 3, px + 4, top - 1)
        flat(near, capm, LS_CAGE[2])
        flat(near, top_rim(capm), LS_CAGE[4])
        flat(near, bot_rim(capm), LS_CAGE[0])
        for yb in (top + 12, top + 30):
            band = wrect(nh, px - 3, yb, px + 3, yb + 1)
            flat(near, band, LS_CAGE[1])
            flat(near, band & left_rim(band), LS_CAGE[3])
        tops.append((px, top))
    for (ax, ay), (bx, by) in ((tops[0], tops[1]), (tops[1], tops[2])):
        pts = sag_pts(ax + 4, ay + 4, bx - 4, by + 4, 22)
        rope_line(near, pts, "#2e2030", pennants=R("#86283a", "#e8d6bc", "#2e2c66"), every=9, seed=ax)
        for j in range(6, len(pts) - 4, 14):
            lantern(near, int(round(pts[j][0])), int(round(pts[j][1])) + 1, lan, glow="#ff9a4a")
    layers.append((near, 0.32, 720))
    return dict(sky="#08071e", horizon="#d89470", layers=layers)


def min_runs(on, n):
    """Drop the runs of True shorter than n from a periodic 1-D mask."""
    if on.all() or not on.any():
        return on.copy()
    start = int(np.argmin(on))
    r = np.roll(on, -start).copy()
    idx = np.nonzero(np.diff(np.concatenate([[0], r.astype(int), [0]])))[0]
    for a, b in zip(idx[::2], idx[1::2]):
        if b - a < n:
            r[a:b] = False
    return np.roll(r, start)


def star_shoal(cv, y, seed, col, rim, thick=6.0, amp=2.0, alphas=(0.12, 0.2, 0.3), cell=120.0, gaps=0.3, glints=0,
               glint_pal=None, clip=None):
    """A shoal of starlight: shallow light pooled flat between the islets, seen nearly edge on. A lens of stepped
    translucent layers deepest in its middle and thinning to nothing at its ends, a bright broken waterline along its
    top, ripple dashes across it and a scatter of glints. Returns its mask."""
    h = cv.h
    yy, xx, _ = grids(h)
    cols = np.arange(W)
    ph = rng("shl", seed).uniform(0, 6.283)
    yc = y + (pn1(("shl", seed), cell, 2) - 0.5) * 2 * amp + np.sin(cols / W * 2 * math.pi + ph) * amp * 0.5
    ends = np.clip((pn1(("she", seed), cell * 1.5, 2) - gaps) / 0.25, 0, 1)
    ends = np.where(min_runs(ends * thick >= 1.2, 28), ends, 0.0)
    clip = np.ones((h, W), bool) if clip is None else clip
    total = np.zeros((h, W), bool)
    for i, a in enumerate(alphas):
        hw = thick * (1 - i * 0.3) * ends
        m = (yy >= np.round(yc - hw * 0.35)[None, :]) & (yy <= np.round(yc + hw)[None, :]) & (hw[None, :] >= 0.8)
        m = despeck(m) & clip
        flat(cv, m, col, a)
        total |= m
    wl = top_rim(total) & (pn2(h, ("shw", seed), 10, 2, 1) > 0.28)
    flat(cv, wl, rim, 0.75)
    rip = total & ~top_rim(total) & ((yy - np.round(yc)[None, :]).astype(int) % 4 == 1)
    rip &= pn2(h, ("shr", seed), 6, 1.2, 2) > 0.7
    flat(cv, rip, rim, 0.3)
    if glints and glint_pal is not None:
        sea_glints(cv, total, ("shg", seed), glints, glint_pal, big_every=5, specks=glints * 3, speck_c=glint_pal[0])
    return total


def star_jelly(cv, x, y, s, col, seed, glow=None, tent=4, drift=0.0):
    """A jellyfish of starlight adrift over the shoals: a translucent bell with a lit crown, a glowing heart and a
    scalloped hem, trailing tendrils that sway and fray to dots, in a stepped halo. col = (deep, body, light, core)."""
    h = cv.h
    yy, xx, _ = grids(h)
    g = rng("jelly", seed)
    x, y = int(round(x)), int(round(y))
    if glow is not None:
        for s_, a in ((2.8, 0.04), (1.9, 0.07), (1.3, 0.11)):
            flat(cv, wellipse(h, x, y - s * 0.3, s * s_, s * s_ * 0.85), glow, a)
    for k in range(tent):
        tx = x - s * 0.75 + (k + 0.5) * (1.5 * s) / tent
        ln = s * g.uniform(1.8, 3.2)
        ph = g.uniform(0, 6.28)
        n = max(2, int(ln))
        for j in range(n):
            t = j / (n - 1.0)
            if t > 0.55 and j % 2:
                continue
            px_ = tx + math.sin(j * 0.5 + ph) * (0.4 + t * 1.3) + drift * t * ln
            put(cv, px_, y + 1 + j, col[1] if t < 0.35 else col[0], 0.95 - t * 0.55)
    bell = wellipse(h, x, y, s, s * 0.85) & (yy <= y)
    flat(cv, bell, col[1], 0.8)
    d = wdx(xx, x)
    flat(cv, bell & (d < -s * 0.2) & ((yy - y) < -s * 0.35), col[2], 0.8)
    flat(cv, top_rim(bell) & (d < s * 0.4), col[2])
    hem = bot_rim(bell)
    flat(cv, hem, col[0], 0.9)
    flat(cv, hem & (xx % 2 == 0), col[2])
    heart = wellipse(h, x - 0.5, y - s * 0.35, max(0.8, s * 0.28), max(0.8, s * 0.22))
    flat(cv, heart, col[3])
    return bell


def lantern_ribbon(cv, seed, y0, amp, width, alphas=(0.04, 0.06, 0.09), density=0.45, k=(1, 2), twinkles=5):
    """The Jade River where it runs faint through the far nebula of the star field: a thin jade star-river."""
    return star_river(cv, seed, y0, amp, width, "#62dc92", JADE_STARS, alphas=alphas, density=density, k=k,
                      twinkles=twinkles)


def star_shoals():
    """The Drifting Shoals: shallow shoals of starlight pooled between low drifting islets, jellyfish of light
    glittering over them, pale cyan and violet under a clear star field; the Jade River winds faint through the
    nebula far below."""
    layers = []
    stops = [(0.0, "#0a0c2c"), (0.18, "#111740"), (0.34, "#1a2454"), (0.46, "#26366a"), (0.55, "#384e80"),
             (0.61, "#506c98"), (0.645, "#6c90b0"), (0.665, "#8cb8c8"), (0.68, "#6c94ba"), (0.7, "#4e62a0"),
             (0.74, "#363c80"), (0.82, "#242866"), (1.0, "#101234")]
    glow_y = 240
    sky = field_sky(stops, "sh", glow_y, up=560, down=280)
    nv = nebula(sky, "shn_v", 96, 26, 26, "#a878f0", alphas=(0.05, 0.08, 0.11), k=(1, 2), cell=80, gaps=0.2)
    nt = nebula(sky, "shn_t", 168, 14, 16, "#50d8e0", alphas=(0.05, 0.08, 0.1), k=(1, 3), cell=90, gaps=0.3)
    nl = nebula(sky, "shn_lo", 304, 18, 26, "#6a5cd0", alphas=(0.04, 0.06, 0.08), k=(1, 2), cell=80, gaps=0.15)
    g = rng("shnst")
    for m_, cols_ in ((nv, R("#9a7ae0", "#d8c4fa")), (nt, R("#5ac8d0", "#c8f8f4")), (nl, R("#8a72d8", "#d0c0f8"))):
        ys, xs = np.nonzero(m_)
        for i in range(min(len(xs), 150)):
            j = int(g.integers(0, len(xs)))
            put(sky, xs[j], ys[j], cols_[0] if i % 4 else cols_[1])
    lantern_ribbon(sky, "shjr", 280, 12, 11, alphas=(0.06, 0.09, 0.13), density=0.7)
    for i, (cx, y, ln) in enumerate(((120, 214, 200), (420, 226, 170), (560, 206, 120))):
        streak(sky, cx, y, ln, R("#6a86b8", "#9ec8d8", "#e0f6f4"), ("shs", i), rows=2)
    layers.append((sky, 0.0, 720))

    # ---------------- far: low islets strung along the glow, lantern stars over them, the far shoals shining between
    fh = 220
    far = Canvas(W, fh)
    yy = grids(fh)[0]
    rock = R("#1c2046", "#242a54", "#2e3662", "#3a4472", "#4a5680", "#5e6e92")
    isles = [(30, 168, 30, 10), (120, 176, 18, 7), (212, 164, 40, 12), (330, 180, 22, 8), (420, 170, 34, 10),
             (530, 176, 26, 9), (600, 186, 12, 5), (270, 110, 12, 12), (480, 90, 16, 16), (80, 70, 10, 10)]
    for i, (cx, top, hw, dp) in enumerate(isles):
        behind = sky_at(stops, far, 560, top + dp * 0.5)
        ramp = hazed(rock, behind, 0.35 + 0.25 * (top > 150))
        m, tp = field_isle(far, cx, top, hw, dp, ramp, ("shfi", i), mixc("#e0f4ff", behind, 0.35),
                           mixc("#8ac8e8", behind, 0.35), tilt=0.0, spurs=1)
        if i % 2 == 0 or top < 150:
            side = 1 if i % 3 else -1
            lantern_star(far, cx + side * hw * 0.25, top - 12 - hw * 0.25, 2.2 + hw * 0.05, ("shfs", i), halo=0.8,
                         rays=0.7, tether=(cx - side * hw * 0.2, top), sag=3.0)
    for k, (y, th, c) in enumerate(((182, 3.5, "#9ae0f0"), (197, 5.0, "#b8a0f8"))):
        star_shoal(far, y, ("shf", k), c, "#f0ffff", thick=th, amp=1.5, alphas=(0.16, 0.28), gaps=0.3, glints=14,
                   glint_pal=R("#d8f8ff", "#ffffff"))
    layers.append((far, 0.08, 560))

    # ---------------- mid: broad low islets with crystal tufts, the shoals pooled round their feet, jellies adrift
    mh = 240
    mid = Canvas(W, mh)
    yy, xx, _ = grids(mh)
    rock_m = R("#131638", "#1a1e46", "#222854", "#2c3462", "#384272", "#4a5886", "#62769c")
    crys = R("#1e4a6a", "#2a6a8a", "#3a8eaa", "#5ab4c8", "#9ae0e8", "#e0fcff")
    stars_x = []
    for i, (cx, top, hw, dp) in enumerate(((110, 160, 70, 40), (380, 170, 88, 46), (590, 150, 36, 30))):
        m, tp = field_isle(mid, cx, top, hw, dp, rock_m, ("shmi", i), "#bce8ff", "#7ab8e0", haze="#2a3a78", spurs=2,
                           cap=R("#26305a", "#4a6a8a"))
        g = rng("shcrys", i)
        for k in range(int(hw // 14)):
            tx = int(cx - hw * 0.8 + g.uniform(0, hw * 1.6))
            crystal(mid, tx, int(tp[tx % W]) + 1, int(g.integers(3, 7)), crys, ("shcr", i, k), glow_c="#5ac8e0",
                    lean=g.uniform(-0.4, 0.4))
        if i != 2:
            sx = cx + (22 if i == 0 else -30)
            lantern_star(mid, sx, top - 58 - i * 8, 7 + i, ("shms", i), tether=(cx - 10 + i * 36, top), sag=6)
            stars_x.append(sx)
    shoals = np.zeros((mh, W), bool)
    for k, (y, th, c, a) in enumerate(((184, 6.0, "#8ad8f0", (0.14, 0.24, 0.34)), (208, 9.0, "#b8a0f8", (0.12, 0.22, 0.3)))):
        shoals |= star_shoal(mid, y, ("shm", k), c, "#f4ffff", thick=th, amp=2.5, alphas=a, gaps=0.3, glints=18,
                             glint_pal=R("#d8f8ff", "#ffffff"))
    # the lantern stars laid on the shallows as broken golden streaks
    for sx in stars_x:
        col = shoals[:, int(sx) % W]
        if not col.any():
            continue
        y0 = int(np.argmax(col))
        for k in range(16):
            if k % 3 == 2:
                continue
            wd = 2 if k < 6 else 1
            flat(mid, wrect(mh, int(sx) - wd // 2 + (k % 2), y0 + k, int(sx) + wd // 2 + (k % 2), y0 + k) & shoals,
                 "#ffe0a0", 0.75 - k * 0.04)
    jel = [R("#2a6a9a", "#5ac0e0", "#b0f0f8", "#ffffff"), R("#5a3aa0", "#9a78e8", "#d8c8ff", "#ffffff"),
           R("#8a3a8a", "#d078c8", "#f8c8f0", "#ffffff")]
    glows = ("#6ad0f0", "#a888f8", "#e890e0")
    g = rng("shjel")
    for i in range(11):
        x = (i + g.uniform(0.1, 0.9)) * W / 11
        y = g.uniform(70, 158)
        k = int(g.integers(0, 3))
        star_jelly(mid, x, y, g.uniform(3.0, 5.5), jel[k], ("shj", i), glow=glows[k], tent=3, drift=g.uniform(-0.2, 0.2))
    layers.append((mid, 0.18, 620))

    # ---------------- near: the shoal at the viewer's feet, deep and glittering, and big slow jellies over it
    nh = 200
    near = Canvas(W, nh)
    yy, _, _ = grids(nh)
    crys_n = R("#18405e", "#22607e", "#3284a0", "#50aac0", "#90dae4", "#e0fcff")
    rock_n = R("#0c0e2a", "#121538", "#191d46", "#212754", "#2c3462", "#3c4876", "#566890")
    for i, (cx, top, hw, dp) in enumerate(((520, 150, 74, 44), (40, 172, 40, 30))):
        m, tp = field_isle(near, cx, top, hw, dp, rock_n, ("shni", i), "#a8e0ff", "#6aa8d8", haze="#1c2660", spurs=2,
                           cap=R("#1c2450", "#3a5a80"))
        g = rng("shncr", i)
        for k in range(int(hw // 10)):
            tx = int(cx - hw * 0.8 + g.uniform(0, hw * 1.6))
            crystal(near, tx, int(tp[tx % W]) + 1, int(g.integers(4, 10)), crys_n, ("shncx", i, k), glow_c="#5ac8e0",
                    lean=g.uniform(-0.4, 0.4))
    for k, (y, th, c, a) in enumerate(((166, 10.0, "#7ad0ec", (0.14, 0.24, 0.34)), (190, 14.0, "#a890f0", (0.16, 0.26, 0.36)))):
        star_shoal(near, y, ("shn", k), c, "#f4ffff", thick=th, amp=4, alphas=a, gaps=0.3 + k * 0.08, glints=16,
                   glint_pal=R("#d8f8ff", "#ffffff"), cell=200.0)
    for i, (x, y, s, k) in enumerate(((90, 70, 9, 0), (300, 40, 7, 1), (520, 84, 11, 2), (410, 116, 5, 0))):
        star_jelly(near, x, y, s, jel[k], ("shnj", i), glow=glows[k], tent=5, drift=0.15 * (1 if i % 2 else -1))
    layers.append((near, 0.32, 720))
    return dict(sky="#0a0c2c", horizon="#8cb8c8", layers=layers)


def nest(cv, cx, by, w, ht, pal, seed, eggs=None, egg_n=3):
    """A great round nest: a deep bowl woven of whole branches, a thick rim bristling with sticks and pale eggs
    showing over it. by = the bowl's foot. pal = twigs (dark, mid, light, pale); eggs = (shade, body, light, speck)."""
    h = cv.h
    yy, xx, _ = grids(h)
    g = rng("nest", seed)
    rim_y = by - ht
    d = wdx(xx, cx)
    if eggs is not None:
        for k in range(egg_n):
            ex = cx + (k - (egg_n - 1) / 2.0) * w * 0.24 + g.uniform(-1, 1)
            er = w * g.uniform(0.09, 0.12)
            ey = rim_y - er * 0.6
            em = wellipse(h, ex, ey, er, er * 1.3)
            de = wdx(xx, ex)
            flat(cv, em, eggs[1])
            flat(cv, em & (de + (yy - ey) * 0.6 < -er * 0.3), eggs[2])
            flat(cv, em & (de + (yy - ey) * 0.4 > er * 0.45), eggs[0])
            flat(cv, em & (pn2(h, ("egs", seed, k), 1.5, 1.5, 1) > 0.78), eggs[3])
    bowl = wellipse(h, cx, rim_y, w / 2.0, ht) & (yy >= rim_y)
    rim = wellipse(h, cx, rim_y, w / 2.0 + 1, max(2.0, ht * 0.3))
    m = bowl | rim
    u = np.clip((d + w / 2.0) / max(1.0, w), 0, 1)
    weave = (((xx + yy) % 5 == 0).astype(float) - ((xx - 2 * yy) % 7 == 0).astype(float))
    v = 1.6 + (0.5 - u) * 1.6 + weave * 0.9 - np.clip((yy - rim_y) / max(1.0, ht), 0, 1) * 0.8
    v = v + rim * 0.7
    paint(cv, m, pal, v, sharp=3)
    flat(cv, top_rim(rim) & (u < 0.7), pal[3])
    flat(cv, bot_rim(m), pal[0])
    for k in range(int(w / 2.5)):
        a = g.uniform(0, 2 * math.pi)
        sx0 = cx + math.cos(a) * w * 0.5
        sy0 = rim_y + math.sin(a) * ht * 0.3
        ln = g.uniform(2, 5 + w * 0.06)
        ang = a + g.uniform(-0.6, 0.6)
        sx1, sy1 = sx0 + math.cos(ang) * ln, sy0 + math.sin(ang) * ln * 0.6 - g.uniform(0, 2)
        flat(cv, wline(h, [(sx0, sy0), (sx1, sy1)], 1), pal[int(g.integers(0, 3))])
    return m


def smoke_plume(cv, x, y, ht, col, seed, width=6.0, lean=0.35, alphas=(0.08, 0.14, 0.2)):
    """Smoke climbing from a lamp or a fire at (x, y): a chain of billows that swell and bend downwind as they rise,
    each alpha step one flat union of lobes (so overlaps never double up), frayed edges, thinning out at the top."""
    h = cv.h
    yy, xx, _ = grids(h)
    g = rng("smk", seed)
    n = max(3, int(ht / (width * 0.4)))
    lobes = []
    for k in range(n):
        t = k / (n - 1.0)
        r = width * (0.35 + t * 1.1) * g.uniform(0.8, 1.2)
        lobes.append((x + lean * ht * t ** 1.4 + g.uniform(-1.5, 1.5) * (1 + t * 3), y - ht * t, r, t))
    fray = pn2(h, ("smkf", seed), 4, 3, 2)
    for i, a in enumerate(alphas):
        m = np.zeros((h, W), bool)
        for (lx, ly, r, t) in lobes:
            s_ = (1.0 - i * 0.28) * (1.0 - t ** 3 * 0.6)
            if s_ * r < 0.8:
                continue
            m |= wellipse(h, lx, ly, r * 1.25 * s_, r * s_)
        m &= fray > 0.12 + i * 0.1
        flat(cv, despeck(m), col, a)


def wyrm(cv, x, y, ln, pal, seed, face=1, amp=3.0):
    """A wyrm on the wing, far off: a long serpent body rippling in a slow wave and tapering to a finned tail, a
    horned head, and two bat wings raised from the shoulders on splayed finger bones with scalloped trailing edges.
    (x, y) = the head, the body trails away from `face`. pal = (body, rim light, wing membrane)."""
    h = cv.h
    g = rng("wyrm", seed)
    ph = g.uniform(0, 6.28)
    n = int(ln)
    pts = [(x - face * t, y + amp * math.sin(t / ln * 2.2 * math.pi + ph) * min(1.0, t / (ln * 0.25)))
           for t in range(n)]
    body = np.zeros((h, W), bool)
    for i in range(n - 1):
        f = i / float(n)
        wd = 4 if f < 0.12 else (3 if f < 0.4 else (2 if f < 0.72 else 1))
        body |= wline(h, [pts[i], pts[i + 1]], wd)
    tx, ty = pts[-1]
    body |= wpoly(h, [(tx, ty), (tx - face * 4, ty - 3), (tx - face * 5, ty + 2)])
    hx, hy = pts[0]
    head = wpoly(h, [(hx - face * 1, hy - 2.5), (hx + face * 6, hy - 1), (hx + face * 6, hy + 1), (hx - face * 1, hy + 2.5)])
    horns = wline(h, [(hx, hy - 2), (hx - face * 4, hy - 6)], 1) | wline(h, [(hx + face * 2, hy - 2), (hx - face * 1, hy - 6)], 1)
    sx, sy = pts[int(ln * 0.22)]
    for k, (reach, lift, col) in enumerate(((ln * 0.5, ln * 0.42, pal[2]), (ln * 0.34, ln * 0.3, pal[0]))):
        wx_ = sx - face * k * 3
        tips = [(wx_ - face * reach * 0.12, sy - lift), (wx_ - face * reach * 0.55, sy - lift * 0.82),
                (wx_ - face * reach, sy - lift * 0.42)]
        wing = wpoly(h, [(wx_ + face * 1, sy)] + tips + [(wx_ - face * reach * 0.62, sy - lift * 0.1),
                                                         (wx_ - face * reach * 0.3, sy + 1)])
        notch = np.zeros((h, W), bool)
        for j in range(2):
            ax, ay = tips[j]
            bx, by = tips[j + 1]
            notch |= wellipse(h, (ax + bx) / 2 - face * reach * 0.05, (ay + by) / 2 + reach * 0.14, reach * 0.1,
                              reach * 0.1)
        wing &= ~notch
        flat(cv, wing, col)
        for tp in tips:
            flat(cv, wline(h, [(wx_, sy), tp], 1) & wing, pal[0])
        flat(cv, top_rim(wing), pal[1])
    flat(cv, body | head | horns, pal[0])
    flat(cv, top_rim(head) | (top_rim(body) & (np.abs(wdx(xx_all(h), x)) < ln * 0.3)), pal[1])
    return body


def crag(cv, cx, top, hw, base, ramp, seed, **kw):
    """A karst crag standing on an island's back: karst_peak cut off at row `base` (it would run to the canvas foot).
    Returns (mask, profile)."""
    h = cv.h
    yy = grids(h)[0]
    tmp = Canvas(W, h)
    m, prof = karst_peak(tmp, cx, top, hw, ramp, seed, base=base + 2, **kw)
    tmp.a[yy > base] = 0.0
    cv.paste(tmp)
    return m & (yy <= base), prof


def cliff_isle(cv, cx, top, hw, base, root, ramp, seed, p=1.7, root_ramp=None, cool=None, trees=None):
    """A tall cliff island adrift: a steep tower of rock rising off a short skirt, its foot broken off into a jagged
    root hanging into the sky below, the underside washed by the nebula's cool light. Returns (mask, profile)."""
    h = cv.h
    yy = grids(h)[0]
    tmp = Canvas(W, h)
    m, prof = karst_peak(tmp, cx, top, hw, ramp, ("cis", seed), base=base, p=p, skirt=1.35, skirt_h=0.12, rough=1.6,
                         gain=1.2, crevice=1.1, shoulder=0.6, ledges=0.6, trees=trees, tree_frac=0.35, asym=0.0)
    tmp.a[yy > base] = 0.0
    m &= yy <= base
    rr = root_ramp or ramp
    rm, _ = shard_isle(tmp, cx, base - 1, hw * 1.3, root, rr, ("cir", seed), spurs=2)
    rm &= ~m
    if cool is not None:
        flat(tmp, bot_rim(rm) & (yy > base + 2), cool)
    cv.paste(tmp)
    return m | rm, prof


def blackmast_haven():
    """Blackmast Haven: the pirates' haven wedged among black rock islands, masts and rigging crowding the cove,
    patched sails, the wreck of a lantern cage jammed in the rocks, smoky red-orange lamps and banners of the
    watching eye; the Jade River shows faintly through the smoke overhead."""
    layers = []
    stops = [(0.0, "#08060e"), (0.18, "#0e0a18"), (0.34, "#171020"), (0.46, "#221428"), (0.55, "#34182a"),
             (0.61, "#4e1e2a"), (0.645, "#72302c"), (0.665, "#9a4a30"), (0.68, "#7a3a2e"), (0.71, "#4a2230"),
             (0.77, "#2a1628"), (0.87, "#170e1e"), (1.0, "#0c0812")]
    glow_y = 240
    sky = field_sky(stops, "bm", glow_y, up=300, down=140, pal=R("#2a2438", "#4e4460", "#8a7e98", "#d0c8d8",
                                                                 "#ffffff"))
    lantern_ribbon(sky, "bmjr", 54, 18, 11, alphas=(0.03, 0.05, 0.07), density=0.35)
    for i, (y, a) in enumerate(((150, 0.08), (196, 0.1), (226, 0.12))):
        nebula(sky, ("bmsm", i), y, 12, 18 + i * 4, "#5a3a3a", alphas=(a * 0.6, a), k=(1, 2), cell=60, gaps=0.15)
    nebula(sky, "bmn_lo", 300, 18, 24, "#5a2a5a", alphas=(0.05, 0.08, 0.1), k=(1, 3), cell=80, gaps=0.2)
    for i, (cx, y, ln) in enumerate(((100, 226, 190), (380, 234, 230), (560, 214, 140))):
        streak(sky, cx, y, ln, R("#c0603a", "#4a2230", "#8a3a30"), ("bms", i), rows=2)
    layers.append((sky, 0.0, 720))

    # ---------------- far: black rock pinnacles in the smoke, far masts, the red eyes of lamps
    fh = 220
    far = Canvas(W, fh)
    yy = grids(fh)[0]
    rock = R("#0e0a12", "#141018", "#1c1620", "#261c28", "#322432", "#402c3a")
    lamp = R("#3a1810", "#e0582a", "#ffb060")
    for i, (x, top, ln) in enumerate(((60, 120, 50), (86, 132, 40), (300, 110, 56), (330, 128, 44), (520, 124, 48))):
        behind = sky_at(stops, far, 560, top)
        c = mixc("#1a1218", behind, 0.35)
        flat(far, wline(fh, [(x, top), (x, top + ln)], 1), c)
        flat(far, wline(fh, [(x - 8, top + 6), (x + 7, top + 5)], 1), c)
        flat(far, wline(fh, [(x - 6, top + 18), (x + 6, top + 17)], 1), c)
        put(far, x + 3, top + 20, lamp[1])
    for i, (cx, top, hw, dp) in enumerate(((30, 120, 26, 60), (190, 100, 20, 70), (250, 140, 16, 40), (410, 116, 24, 64),
                                         (470, 150, 14, 34), (600, 104, 18, 60))):
        behind = sky_at(stops, far, 560, top + dp * 0.4)
        ramp = hazed(rock, behind, 0.3)
        crag(far, cx + hw * 0.2, top - 26 - i % 3 * 8, hw * 0.45, top + 3, ramp, ("bmfp", i), p=1.3, rough=2.4,
             shoulder=0.9, crevice=1.0)
        m, tp = field_isle(far, cx, top, hw, dp, ramp, ("bmfi", i), mixc("#e06a3a", behind, 0.4),
                           mixc("#7a3a5a", behind, 0.4), tilt=0.05 * (1 if i % 2 else -1), spurs=3)
        lx = int(cx - hw * 0.5)
        lantern(far, lx, int(tp[lx % W]) - 5, lamp, glow="#e05a2a")
    lantern_star(far, 250, 64, 4, "bmfs0", lit=0.45, halo=0.6, rays=0.5, tether=(254, 140), sag=6)
    for i, (y, a) in enumerate(((150, 0.14), (176, 0.18))):
        mist_band(far, y, 10, ("bmfm", i), "#5a3438", alphas=(a * 0.6, a), amp=4, cell=90, gaps=0.2)
    layers.append((far, 0.08, 560))

    # ---------------- mid: the haven: rock islands wedged close, ships moored in the cove, lamps, the broken cage
    mh = 260
    mid = Canvas(W, mh)
    yy, xx, _ = grids(mh)
    rock_m = R("#0a070c", "#110c14", "#18111c", "#221824", "#2e202e", "#3c2a38", "#4e3844")
    warm = "#d8643a"
    cool = "#6a3a62"
    lamp_m = R("#3a1810", "#f0602a", "#ffc070")
    isl = []
    # the lamplight of the haven pooling red in its own smoke
    for (gx, gy, rx, ry) in ((200, 140, 90, 50), (440, 150, 80, 44), (40, 150, 50, 30)):
        for s_, a in ((1.0, 0.04), (0.66, 0.06), (0.38, 0.08)):
            flat(mid, wellipse(mh, gx, gy, rx * s_, ry * s_), "#e0602a", a)
    # a forest of bare masts behind the rocks: the rest of the fleet lying in the lee
    mast_c = R("#140c12", "#2a1a1e", "#6a3a2c")
    for i, (x, top, bot) in enumerate(((20, 60, 150), (132, 44, 150), (152, 70, 150), (368, 64, 176), (470, 50, 150),
                                       (604, 70, 140))):
        flat(mid, wline(mh, [(x, top), (x, bot)], 1), mast_c[1])
        for j, (yo, ln) in enumerate(((6, 9), (22, 7), (40, 5))):
            if top + yo < bot - 10:
                flat(mid, wline(mh, [(x - ln, top + yo + 1), (x + ln, top + yo - 1)], 1), mast_c[1])
                put(mid, x - ln, top + yo + 1, mast_c[2])
        rope_line(mid, [(x, top), (x - 26, bot - 10)], mast_c[0])
        rope_line(mid, [(x, top), (x + 22, bot - 16)], mast_c[0])
        flat(mid, wrect(mh, x, top - 2, x, top - 1), mast_c[2])
    for i, (x, y, ht) in enumerate(((96, 138, 80), (330, 172, 70), (590, 122, 76))):
        smoke_plume(mid, x, y, ht, "#5a3434", ("bmsp", i), width=8, lean=0.5, alphas=(0.07, 0.11, 0.15))
    # the wreck of a lantern cage, fallen and sunk half into the rock of the big isle, its star long gone: stove-in
    # ribs, bent spokes, a snapped mooring chain
    wx, wy, wr = 548, 136, 20
    chain(mid, dangle_pts(wx - 3, wy - wr - 6, 20, sway=-3), R("#140c10", "#4a301a", "#8a5a2c"), heavy=True)
    lantern_star(mid, wx, wy, wr, "bmwreck", lit=0.0, ember="#5a2418", broken=0.42, verd=LS_VERD)
    g = rng("bmspoke")
    for k in range(5):
        a0 = g.uniform(-2.6, -0.6)
        x0, y0 = wx + math.cos(a0) * wr, wy + math.sin(a0) * wr
        a1 = a0 + g.uniform(-0.8, 0.8)
        ln_ = g.uniform(4, 9)
        flat(mid, wline(mh, [(x0, y0), (x0 + math.cos(a1) * ln_, y0 + math.sin(a1) * ln_)], 1), LS_CAGE[2])
    for i, (cx, top, hw, dp) in enumerate(((70, 150, 72, 80), (330, 176, 44, 60), (520, 140, 80, 90))):
        pk, pp = crag(mid, cx - hw * 0.25, top - 60 + i * 14, hw * 0.4, top + 4, rock_m, ("bmmp", i), p=1.25, rough=2.6,
                      shoulder=1.0, crevice=1.2, gain=1.1)
        flat(mid, left_rim(pk) & (yy < top), warm, 0.6)
        m, tp = field_isle(mid, cx, top, hw, dp, rock_m, ("bmmi", i), warm, cool, haze="#2a1824", spurs=3)
        isl.append((cx, top, hw, tp))
    crag(mid, 570, 122, 10, 142, rock_m, "bmwr", p=1.4, rough=2.0, shoulder=0.0)
    crag(mid, 526, 130, 7, 142, rock_m, "bmwr2", p=1.6, rough=2.0, shoulder=0.0)
    # ships moored in the cove between the islands: patched sails, lamps, rigging to the rocks
    hullp = R("#0e0a10", "#241820", "#4e3432")
    sails = R("#2a1a1a", "#4a2a26", "#7a4436")
    patch = R("#5e3a2a", "#3a2a24", "#6a2a2a")
    junk(mid, 214, 150, 64, "bmj1", hullp, sails, face=1, lit=("#e0602a", "#ffb060"), patch=patch)
    junk(mid, 420, 162, 54, "bmj2", hullp, R("#221a20", "#3e2e2e", "#6a5040"), face=-1, lit=("#e0602a", "#ffb060"),
         patch=patch)
    junk(mid, 300, 128, 40, "bmj3", hullp, sails, face=1, set_sails=False, lit=("#e0602a", "#ffb060"))
    # rigging and lamp lines strung from the masts to the rocks
    for (a, b, s_) in (((214, 96), (140, 118), 6), ((214, 96), (312, 100), 10), ((420, 116), (500, 100), 6),
                       ((300, 100), (420, 116), 8)):
        pts = sag_pts(a[0], a[1], b[0], b[1], s_)
        rope_line(mid, pts, "#2a1c24")
        for j in range(4, len(pts) - 3, 9):
            lantern(mid, int(round(pts[j][0])), int(round(pts[j][1])) + 1, lamp_m, glow="#e05a2a")
    # plank walks and lamps on the rocks
    for cx, top, hw, tp in isl:
        for k in range(2):
            lx = int(cx - hw * 0.6 + k * hw * 0.9)
            ly = int(tp[lx % W])
            flat(mid, wrect(mh, lx, ly - 10, lx, ly), "#1a1016")
            flat(mid, wrect(mh, lx, ly - 10, lx + 2, ly - 10), "#1a1016")
            lantern(mid, lx + 2, ly - 9, lamp_m, glow="#e05a2a")
    pier(mid, 118, 160, 152, R("#140c10", "#2e1e1e", "#6a4432"), posts=R("#0c080c", "#1a1016"), drop=10)
    pier(mid, 452, 484, 162, R("#140c10", "#2e1e1e", "#6a4432"), posts=R("#0c080c", "#1a1016"), drop=10)
    pole = R("#140e18", "#2a1e26", "#5a4038")
    cloth = R("#161436", "#221f4c", "#302d66", "#46448a")
    for i, (bx, ht) in enumerate(((40, 56), (500, 66))):
        col = mid.a[:, bx % W] > 0
        by = int(np.argmax(col)) if col.any() else 150
        war_banner(mid, bx, by + 1, ht, pole, cloth, "#ece2c8", ("bmb", i), bl=24, bw=8, trim="#c8b894")
    for i, (y, a) in enumerate(((104, 0.1), (140, 0.14))):
        mist_band(mid, y, 12, ("bmmm", i), "#6a3a38", alphas=(a * 0.6, a), amp=5, cell=70, gaps=0.3)
    layers.append((mid, 0.18, 620))

    # ---------------- near: a black rock landing at the viewer's feet, planks run out over the drop, lamps, smoke
    nh = 200
    near = Canvas(W, nh)
    yy, xx, _ = grids(nh)
    rock_n = R("#08050a", "#0e0a10", "#150e16", "#1e141e", "#2a1c28", "#3a2632")
    mist_band(near, 150, 18, "bmnm0", "#5a2e2e", alphas=(0.08, 0.14, 0.2), amp=6, cell=90, gaps=0.15)
    prof = np.full(W, np.inf)
    for i, (px, top, hw) in enumerate(((60, 104, 70), (8, 84, 26), (570, 136, 44))):
        pr, _ = karst_profile(px, top, 206, hw, p=3.4, skirt=1.3, skirt_h=0.25, seed=("bmnp", i), rough=2.4)
        prof = np.minimum(prof, pr)
    rm = despeck(yy >= prof[None, :])
    rock_mass(near, rm, rock_n, "bmnrm", gain=1.1, crevice=0.8)
    lit_edge = top_rim(rm) | (right_rim(rm) & (yy < prof[None, :] + 30))
    flat(near, lit_edge & (pn2(nh, "bmne", 3, 3, 1) > 0.3), "#7a3428")
    deck_y = int(prof[96]) + 1
    for bx in (136, 164, 192):
        flat(near, wline(nh, [(bx, deck_y + 2), (bx - 30, deck_y + 30)], 1), "#140c10")
    pier(near, 92, 226, deck_y, R("#0e080c", "#22161a", "#5a3a2e"), posts=R("#08060a", "#140c10"), drop=14,
         lamps=(140, 204), lan=lamp_m, glow="#e05a2a")
    flat(near, wrect(nh, 222, deck_y - 44, 223, deck_y), "#1a1016")
    flat(near, wrect(nh, 219, deck_y - 44, 226, deck_y - 44), "#1a1016")
    lantern(near, 219, deck_y - 43, lamp_m, glow="#e05a2a")
    for i, (bx, ht) in enumerate(((36, 64),)):
        col = near.a[:, bx % W] > 0
        by = int(np.argmax(col)) if col.any() else 150
        war_banner(near, bx, by + 1, ht, pole, cloth, "#ece2c8", ("bmnb", i), bl=30, bw=10, trim="#c8b894")
    rope_line(near, sag_pts(223, deck_y - 42, 560, int(prof[560]) - 6, 30), "#1e1418",
              pennants=R("#86283a", "#e8d6bc", "#2e2c66"), every=8, seed=5)
    smoke_plume(near, 40, int(prof[40]) - 2, 90, "#3a2226", "bmnsp", width=10, lean=0.6, alphas=(0.06, 0.1, 0.14))
    mist_band(near, 186, 16, "bmnm", "#4a2a2c", alphas=(0.12, 0.2, 0.28), amp=5, cell=80, gaps=0.1)
    layers.append((near, 0.32, 720))
    return dict(sky="#08060e", horizon="#9a4a30", layers=layers)


def wyrmnest_isles():
    """Wyrmnest Isles: tall cliff islands of pale eggshell rock under a violet-teal nebula sky, great round nests of
    whole branches on their crowns and ledges, pale eggs in them, lantern stars moored above; the Jade River runs
    through the teal nebula."""
    layers = []
    stops = [(0.0, "#0a0a26"), (0.16, "#120f36"), (0.3, "#1c1648"), (0.42, "#26205a"), (0.52, "#2c3068"),
             (0.6, "#2e4a74"), (0.645, "#3a6a80"), (0.67, "#5a8e8e"), (0.69, "#46707e"), (0.72, "#34466e"),
             (0.78, "#2a2c5e"), (0.88, "#1a1a44"), (1.0, "#0e0e2c")]
    glow_y = 241
    sky = field_sky(stops, "wn", glow_y, up=520, down=260)
    nv = nebula(sky, "wnn_v", 84, 30, 34, "#b070f0", alphas=(0.06, 0.09, 0.13, 0.16), k=(1, 2), cell=90, gaps=0.1)
    nt = nebula(sky, "wnn_t", 150, 22, 28, "#30d0c0", alphas=(0.05, 0.08, 0.12, 0.15), k=(1, 3), cell=80, gaps=0.15)
    nl = nebula(sky, "wnn_lo", 296, 18, 26, "#8a58d8", alphas=(0.05, 0.08, 0.11), k=(2, 3), cell=70, gaps=0.2)
    g = rng("wnnst")
    for m_, cols_ in ((nv, R("#a680e0", "#e0ccfa")), (nt, R("#48c0b4", "#c0f8ee")), (nl, R("#8a70d0", "#d4c0f4"))):
        ys, xs = np.nonzero(m_)
        for i in range(min(len(xs), 170)):
            j = int(g.integers(0, len(xs)))
            put(sky, xs[j], ys[j], cols_[0] if i % 4 else cols_[1])
    lantern_ribbon(sky, "wnjr", 150, 20, 11, alphas=(0.05, 0.08, 0.11), density=0.55)
    for i, (x, y, ln, face) in enumerate(((196, 58, 46, 1), (470, 104, 34, -1), (590, 44, 24, -1))):
        wyrm(sky, x, y, ln, R("#0a0818", "#8a7cc4", "#161230"), ("wnw", i), face=face, amp=3.0)
    layers.append((sky, 0.0, 720))

    # ---------------- far: pale cliff islands at every height, nests on their crowns, lantern stars over them
    fh = 220
    far = Canvas(W, fh)
    yy = grids(fh)[0]
    shell = R("#4a4870", "#5c5a80", "#726e92", "#8e88a6", "#aaa2b8", "#c6bec8", "#ddd6d6")
    twig = R("#2a2030", "#3e3040", "#5a4650", "#8a7a78")
    for i, (cx, top, hw, base, root) in enumerate(((40, 80, 14, 150, 30), (150, 110, 10, 168, 20), (260, 60, 16, 140, 34),
                                                   (380, 96, 12, 160, 24), (480, 70, 15, 150, 30), (580, 118, 10, 170, 18))):
        behind = sky_at(stops, far, 560, (top + base) * 0.5)
        ramp = hazed(shell, behind, 0.42)
        m, prof = cliff_isle(far, cx, top, hw, base, root, ramp, ("wnf", i), root_ramp=hazed(shell[:5], behind, 0.5),
                             cool=mixc("#60d0c0", behind, 0.4))
        ty = int(prof[int(cx) % W])
        nest(far, cx, ty + 2, hw * 1.2, max(2.0, hw * 0.3), hazed(twig, behind, 0.4), ("wnfn", i))
        lantern_star(far, cx + 6, ty - 18, 2.6, ("wnfs", i), halo=0.8, rays=0.7, tether=(cx + 2, ty - 2), sag=2)
    layers.append((far, 0.08, 560))

    # ---------------- mid: great cliff islands with nests on crown and ledge, eggs pale as the rock
    mh = 280
    mid = Canvas(W, mh)
    yy, xx, _ = grids(mh)
    shell_m = R("#3e3a64", "#524c76", "#6a6488", "#86809c", "#a49cb2", "#c2bac6", "#ddd4d4", "#f0eae2")
    twig_m = R("#221a26", "#3a2c34", "#5a4642", "#8a7462")
    eggs = R("#9a90a8", "#e8e2dc", "#fbf8f2", "#8a7a96")
    for i, (cx, top, hw, base, root) in enumerate(((120, 60, 34, 200, 60), (400, 90, 28, 214, 46), (560, 130, 18, 220, 30))):
        m, prof = cliff_isle(mid, cx, top, hw, base, root, shell_m, ("wnm", i), root_ramp=shell_m[:6], cool="#58c8b8")
        ty = int(prof[int(cx) % W])
        nest(mid, cx, ty + 6, hw * 1.5, max(5.0, hw * 0.46), twig_m, ("wnmn", i), eggs=eggs, egg_n=3 if hw > 20 else 2)
        # a ledge nest partway down the cliff, hugging its shaded flank
        ly = int(top + (base - top) * 0.55)
        xs = np.nonzero(m[ly])[0]
        if len(xs):
            lx = int(round(cx + wdx(xs, cx).max())) - int(hw * 0.2)
            nest(mid, lx, ly, hw * 0.8, max(4.0, hw * 0.34), twig_m, ("wnml", i), eggs=eggs, egg_n=2)
        lantern_star(mid, cx - hw * 0.2, ty - 44 - i * 6, 8 - i, ("wnms", i), tether=(cx - hw * 0.5, ty + 2), sag=5)
    layers.append((mid, 0.18, 620))

    # ---------------- near: a cliff crown at the viewer's feet with its nest, shell shards, the nebula below
    nh = 200
    near = Canvas(W, nh)
    yy, xx, _ = grids(nh)
    shell_n = R("#15142e", "#1c1a3a", "#252248", "#302c58", "#3e3868", "#524a7a", "#6e6690", "#9a90a8")
    mist_band(near, 172, 22, "wnnm", "#6a58c0", alphas=(0.06, 0.1, 0.14), amp=6, cell=100, gaps=0.1)
    g = rng("wnshard")
    for i, (px, top, hw) in enumerate(((70, 84, 44), (560, 124, 30))):
        m, prof = karst_peak(near, px, top, hw, shell_n, ("wnnp", i), p=2.2, skirt=1.5, skirt_h=0.25, rough=1.5,
                             gain=1.1, crevice=1.0, shoulder=0.6, ledges=0.5, asym=0.1)
        flat(near, bot_rim(m), "#58c8b8")
        for k in range(5):
            sx = int(px + g.uniform(-hw * 0.8, hw * 0.8))
            sy = int(prof[sx % W]) + int(g.integers(0, 2))
            sm = wpoly(nh, [(sx - 2, sy), (sx + 1, sy - 2), (sx + 3, sy)])
            flat(near, sm, "#b8b0b4")
            flat(near, right_rim(sm), "#6a6280")
        if i == 0:
            nest(near, px + 4, int(prof[(px + 4) % W]) + 12, 66, 22, R("#120e18", "#221a26", "#3a2e36", "#6a584e"),
                 "wnnn", eggs=R("#6a6280", "#b8b0b4", "#dcd6d0", "#5a4e68"), egg_n=3)
    layers.append((near, 0.32, 720))
    return dict(sky="#0a0a26", horizon="#5a8e8e", layers=layers)


def obs_dome(cv, cx, by, r, pal, stone, slit="#0a0e1c", scope=True):
    """An observatory dome of bronze on a white stone drum: a ribbed hemisphere lit from the upper left, its shutter
    slit open with a telescope's barrel raised through it, a finial on the crown. pal = bronze dark->gleam (5);
    stone = drum (dark, mid, light). by = foot of the drum. Returns its mask."""
    h = cv.h
    yy, xx, _ = grids(h)
    d = wdx(xx, cx)
    dh = max(2, int(round(r * 0.45)))
    drum = (np.abs(d) <= r + 1) & (yy > by - dh) & (yy <= by)
    flat(cv, drum, stone[1])
    flat(cv, drum & (d < -r * 0.5), stone[2])
    flat(cv, drum & (d > r * 0.55), stone[0])
    flat(cv, top_rim(drum), pal[3])
    flat(cv, drum & (yy == by - dh + 2) & (np.abs(d) <= r), pal[1])
    for wx in np.arange(-r * 0.6, r * 0.61, max(3.0, r * 0.4)):
        flat(cv, drum & (np.abs(d - wx) < 0.6) & (yy > by - dh + 3) & (yy < by - 1), stone[0])
    cy = by - dh
    dome = wellipse(h, cx, cy, r, r) & (yy <= cy)
    dy = (yy - cy) / r
    lt = d / r * 0.8 + dy * 0.9
    v = 2.6 - lt * 1.6
    rib = np.zeros((h, W), bool)
    for f in (0.35, 0.7):
        rib |= ring_px(((d / (r * f + 0.3)) ** 2 + ((yy - cy) / (r + 0.3)) ** 2) <= 1.0)
    rib &= dome
    paint(cv, dome, pal, v, sharp=4)
    flat(cv, rib, pal[1])
    flat(cv, rib & (d < 0) & (dy > -0.7), pal[2])
    flat(cv, top_rim(dome) & (d < r * 0.3), pal[4])
    flat(cv, right_rim(dome), pal[0])
    sl = dome & (np.abs(d - r * 0.18) <= max(1.0, r * 0.1)) & (yy >= cy - r)
    flat(cv, sl, slit)
    if scope:
        x0, y0 = cx + r * 0.18, cy - r * 0.35
        x1, y1 = cx + r * 0.95, cy - r * 1.2
        bar = wline(h, [(x0, y0), (x1, y1)], max(2, int(round(r * 0.18))))
        flat(cv, bar, pal[2])
        flat(cv, top_rim(bar), pal[4])
        flat(cv, bot_rim(bar), pal[0])
        put(cv, x1 + 1, y1 - 1, pal[4])
    fin = wrect(h, int(cx), cy - r - 3, int(cx), cy - r)
    flat(cv, fin, pal[1])
    put(cv, cx, cy - r - 4, pal[4])
    return drum | dome


def lantern_mast(cv, x, by, ht, seed, r=4.0, pal=None, lit=1.0, arm=0):
    """A bronze lantern mast: a slender post on a stepped foot, collared, a crook at its head from which a lantern
    star hangs (arm > 0: an arm reaching that far to the right). pal = bronze dark->gleam."""
    h = cv.h
    pal = LS_CAGE if pal is None else pal
    top = by - ht
    post = wrect(h, x, top, x, by)
    flat(cv, post, pal[1])
    flat(cv, wrect(h, x - 1, by - 2, x + 1, by), pal[2])
    flat(cv, wrect(h, x - 1, top + ht // 3, x + 1, top + ht // 3), pal[3])
    if arm:
        flat(cv, wrect(h, x, top, x + arm, top), pal[2])
        put(cv, x + arm, top + 1, pal[1])
        return lantern_star(cv, x + arm, top + r + 5, r, seed, lit=lit, hang=(x + arm, top))
    put(cv, x, top - 1, pal[3])
    return lantern_star(cv, x, top - r - 5, r, seed, lit=lit)


def warden_citadel():
    """The Star Warden Citadel: a citadel of white stone and bronze on its island, observatory domes with their
    telescopes raised, lantern stars hung in orderly rows along its walls and far avenues of them receding into the
    blue; stately, cool blue and gold, the Jade River bright overhead."""
    layers = []
    stops = [(0.0, "#060c24"), (0.18, "#0b1633"), (0.34, "#132446"), (0.46, "#1c345a"), (0.55, "#294a6e"),
             (0.61, "#3a6284"), (0.645, "#5a7c94"), (0.665, "#9c9e8c"), (0.68, "#74889a"), (0.71, "#48648a"),
             (0.77, "#2c4068"), (0.87, "#18264a"), (1.0, "#0c142e")]
    glow_y = 240
    sky = field_sky(stops, "wc", glow_y, up=560, down=240, pal=R("#24345e", "#4a6090", "#90a8d0", "#d8e4f4", "#ffffff"))
    star_river(sky, "wcjr", 62, 26, 14, "#62dc92", JADE_STARS, alphas=(0.05, 0.08, 0.12), density=0.7)
    nebula(sky, "wcn_b", 150, 18, 22, "#4a80d0", alphas=(0.05, 0.08, 0.1), k=(1, 2), cell=90, gaps=0.2)
    nebula(sky, "wcn_lo", 300, 16, 26, "#3a60b0", alphas=(0.05, 0.08, 0.1), k=(1, 3), cell=80, gaps=0.2)
    for i, (cx, y, ln) in enumerate(((140, 214, 190), (430, 224, 220), (600, 204, 120))):
        streak(sky, cx, y, ln, R("#5a7a9a", "#a8b4b0", "#f0e8c8"), ("wcs", i), rows=2)
    layers.append((sky, 0.0, 720))

    # ---------------- far: avenues of lantern stars in rows, receding, and far towers of the Wardens on their isles
    fh = 220
    far = Canvas(W, fh)
    yy = grids(fh)[0]
    rock = R("#16223e", "#1c2a4a", "#243458", "#2e4066", "#3a4e74", "#4a6084")
    white = R("#5a6a86", "#7a8aa2", "#9aa8bc", "#bcc6d2")
    for i, (cx, top, hw, dp) in enumerate(((60, 150, 30, 20), (230, 166, 24, 16), (420, 146, 36, 22), (570, 170, 20, 14))):
        behind = sky_at(stops, far, 560, top)
        ramp = hazed(rock, behind, 0.35)
        wh = hazed(white, behind, 0.35)
        for k, (ox, th, w_) in enumerate(((-0.35, 26, 5), (0.1, 40, 6), (0.45, 20, 4))):
            tx = int(cx + ox * hw)
            tm = wrect(fh, tx - w_ // 2, top - th, tx + w_ // 2, top)
            flat(far, tm, wh[1])
            flat(far, left_rim(tm), wh[3])
            flat(far, right_rim(tm), wh[0])
            dm = wellipse(fh, tx, top - th, w_ / 2 + 1, w_ / 2 + 1) & (yy <= top - th)
            flat(far, dm, mixc("#a8783a", behind, 0.35))
            put(far, tx, top - th - w_ // 2 - 2, mixc("#e4b460", behind, 0.3))
        field_isle(far, cx, top, hw, dp, ramp, ("wcfi", i), mixc("#f0d8a0", behind, 0.35), mixc("#6a9ad0", behind, 0.35),
                   spurs=1)
    for row, (y, gap, r, off, a) in enumerate(((58, 64, 2.6, 10, 1.0), (92, 45.714, 2.2, 30, 0.9),
                                              (118, 32, 1.8, 4, 0.75))):
        behind = sky_at(stops, far, 560, y)
        flat(far, (yy == y - int(r) - 5) & (xx_all(fh) % 2 == 0), mixc("#8a6a3a", behind, 0.5))
        for j in range(int(round(W / gap))):
            x = off + j * gap
            lantern_star(far, x, y, r, ("wcfr", row, j), lit=a, halo=0.7, rays=0.6, hang=(x, y - int(r) - 5), verd=None)
    layers.append((far, 0.08, 560))

    # ---------------- mid: the citadel of white stone and bronze, observatory domes, rows of lantern masts
    mh = 300
    mid = Canvas(W, mh)
    yy, xx, _ = grids(mh)
    rock_m = R("#0e1830", "#14203c", "#1c2a4a", "#263658", "#324468", "#40567a", "#546a8c")
    stone = R("#56627a", "#6c788e", "#8490a4", "#9ea8ba", "#bcc4d0", "#dce0e6")
    bronze = LS_CAGE
    icx, itop, ihw = 330, 218, 212
    isle, itp = field_isle(mid, icx, itop, ihw, 70, rock_m, "wcmi", "#f0d8a0", "#6a9ad0", haze="#1c2c56", spurs=3,
                           cap=R("#3a4460", "#9aa4b8"))
    gy = int(itp[icx % W])
    # the curtain wall with its bronze coping and a gate
    wall = wrect(mh, icx - 170, gy - 30, icx + 170, gy)
    ashlar(mid, wall, stone[:5], "wcwall", course=7, joint=32)
    haze_fade(mid, wall, "#26344e", np.clip((yy - gy + 26) / 30.0, 0, 1) * 0.45, steps=3, sharp=4)
    flat(mid, wrect(mh, icx - 172, gy - 33, icx + 172, gy - 31), bronze[2])
    flat(mid, wrect(mh, icx - 172, gy - 33, icx + 172, gy - 33), bronze[4])
    flat(mid, wrect(mh, icx - 172, gy - 31, icx + 172, gy - 31), bronze[0])
    for x in range(icx - 166, icx + 170, 12):
        flat(mid, wrect(mh, x, gy - 37, x + 5, gy - 34), stone[3])
        flat(mid, wrect(mh, x, gy - 37, x + 5, gy - 37), stone[5])
    gate = (np.abs(wdx(xx, icx)) <= 9) & (yy >= gy - 20) & (yy <= gy)
    gate |= wellipse(mh, icx, gy - 20, 9, 7) & (yy < gy - 20)
    flat(mid, gate, "#1a2238")
    flat(mid, gate & (np.abs(wdx(xx, icx)) <= 7) & (yy > gy - 18), "#f0c070", 0.35)
    flat(mid, ring_px(gate) & (yy < gy - 18), bronze[3])
    # towers with domes: the great observatory keep at the heart, lesser towers at the wall's ends
    for k, (tx, tw, th, dr) in enumerate(((icx, 44, 96, 24), (icx - 150, 26, 60, 13), (icx + 150, 26, 60, 13),
                                          (icx - 80, 20, 44, 0), (icx + 80, 20, 44, 0))):
        tm = wrect(mh, tx - tw // 2, gy - th, tx + tw // 2, gy - 2)
        ashlar(mid, tm, stone[:5], ("wct", k), course=7, joint=32)
        flat(mid, left_rim(tm), stone[5])
        flat(mid, right_rim(tm), stone[0])
        haze_fade(mid, tm & (wdx(xx, tx) > tw * 0.2), "#3a4a6a", np.full((mh, W), 0.35), steps=2, sharp=4)
        for wy_ in range(gy - th + 10, gy - 36, 16):
            wm = wrect(mh, tx - 1, wy_, tx + 1, wy_ + 5)
            flat(mid, wm, "#f4c878")
            flat(mid, top_rim(wm), "#fff0c0")
        band = wrect(mh, tx - tw // 2 - 1, gy - th - 3, tx + tw // 2 + 1, gy - th)
        flat(mid, band, bronze[2])
        flat(mid, top_rim(band), bronze[4])
        if dr:
            obs_dome(mid, tx, gy - th - 3, dr, bronze, stone[1:4], scope=k == 0 or k == 2)
        else:
            roof = wpoly(mh, [(tx - tw // 2 - 3, gy - th - 3), (tx + tw // 2 + 3, gy - th - 3), (tx, gy - th - 14)])
            flat(mid, roof, bronze[2])
            flat(mid, roof & (wdx(xx, tx) < 0), bronze[3])
            flat(mid, top_rim(roof) & (wdx(xx, tx) < 0), bronze[4])
            flat(mid, right_rim(roof), bronze[0])
    # halls behind the wall with bronze roofs
    for k, (hx, hw_) in enumerate(((icx - 128, 36), (icx + 92, 36))):
        hall(mid, hx, gy - 37, hw_, 7, 7, R("#4a301a", "#8a5a2c", "#c08a44", "#f0c070"), stone[2:5],
             post_col="#7a2e28", lit="#f4c878", tiers=1)
    # the lantern masts along the wall top, all at one height, and a higher row on the towers
    for k, x in enumerate(range(icx - 160, icx + 161, 40)):
        if abs(x - icx) < 30:
            continue
        lantern_mast(mid, x, gy - 37, 34, ("wcmm", k), r=5.0)
    for k, x in enumerate((icx - 150, icx + 150)):
        chain(mid, sag_pts(x, gy - 60 - 32, icx, gy - 96 - 34, 18), R("#22150c", "#76502a", "#aa7838"))
        pts = sag_pts(x, gy - 60 - 32, icx, gy - 96 - 34, 18)
        for j in range(8, len(pts) - 6, 14):
            lantern_star(mid, pts[j][0], pts[j][1] + 7, 3.5, ("wcch", k, j), hang=(pts[j][0], pts[j][1]))
    # the great lantern star of the Wardens above the keep
    lantern_star(mid, icx, 44, 16, "wcgreat", hang=None, tether=(icx, gy - 96 - 48), sag=0.5)
    layers.append((mid, 0.18, 620))

    # ---------------- near: the white terrace, balustrade and bronze lantern posts over the blue drop
    nh = 200
    near = Canvas(W, nh)
    yy, xx, _ = grids(nh)
    mist_band(near, 150, 24, "wcnm", "#6a90c8", alphas=(0.05, 0.08, 0.12), amp=5, cell=100, gaps=0.1)
    terr = yy >= 164
    ashlar(near, terr, R("#1c2436", "#242e42", "#2c374e", "#36425a", "#424e68"), "wcnt", course=10, joint=64)
    flat(near, wrect(nh, 0, 164, W - 1, 165), "#8a94a8")
    haze_fade(near, terr, "#0c1426", np.clip((yy - 168) / 32.0, 0, 1) * 0.6, steps=3, sharp=4)
    balustrade(near, 164, R("#5a6478", "#8a94a6", "#b8c0cc", "#e4e8ec"), "wcnb", post_gap=32, rail_h=12)
    for k, x in enumerate(range(48, W, 160)):
        lantern_mast(near, x, 163, 70, ("wcnl", k), r=6.0, arm=10)
    layers.append((near, 0.32, 720))
    return dict(sky="#060c24", horizon="#9c9e8c", layers=layers)


def orbit_ring(cv, cx, cy, rx, ry, tilt, width, ramp, seed, arcs=((0.0, 2 * math.pi),), part="all", joint=0.22):
    """Broken stone ring segments orbiting (cx, cy): pieces of a tilted ellipse `width` px thick, dressed in blocks
    with dark joints, lit on their upper edge. part = 'back' (the far half, drawn before the core), 'front' or 'all'.
    arcs = [(t0, t1), ...] parameter ranges that survive. ramp dark->light (>= 4). Returns the mask."""
    h = cv.h
    yy, xx, _ = grids(h)
    dx = wdx(xx, cx)
    dy = yy - cy
    c, s_ = math.cos(tilt), math.sin(tilt)
    u = c * dx + s_ * dy
    v = -s_ * dx + c * dy
    e = np.sqrt((u / rx) ** 2 + (v / ry) ** 2)
    t = np.arctan2(v / ry, u / rx) % (2 * math.pi)
    band = np.abs(e - 1.0) * min(rx, ry) <= width / 2.0
    sel = np.zeros((h, W), bool)
    for (t0, t1) in arcs:
        sel |= (t >= t0 % (2 * math.pi)) & (t <= t0 % (2 * math.pi) + (t1 - t0)) if t1 - t0 < 2 * math.pi else True
        if t0 % (2 * math.pi) + (t1 - t0) > 2 * math.pi:
            sel |= t <= (t0 + (t1 - t0)) % (2 * math.pi)
    m = band & sel
    if part == "back":
        m &= v < 0
    elif part == "front":
        m &= v >= 0
    m = despeck(m)
    n = len(ramp)
    rel = (e - 1.0) * min(rx, ry) / max(1.0, width)
    val = (n - 1) * 0.55 - rel * 2.4 + (v < 0) * -0.6
    paint(cv, m, ramp, val, sharp=4)
    blocks = ((t / joint) % 1.0) < (1.2 / max(8.0, rx))
    flat(cv, m & blocks, ramp[0])
    flat(cv, top_rim(m), ramp[-1])
    flat(cv, bot_rim(m), ramp[0])
    return m


def orbit_path(cv, cx, cy, rx, ry, tilt, col, a=0.35, dash=5):
    """A faint dotted orbit traced around (cx, cy)."""
    n = int(2 * math.pi * max(rx, ry) / 2)
    c, s_ = math.cos(tilt), math.sin(tilt)
    for i in range(n):
        if (i // dash) % 2:
            continue
        t = 2 * math.pi * i / n
        u, v = rx * math.cos(t), ry * math.sin(t)
        put(cv, cx + c * u - s_ * v, cy + s_ * u + c * v, col, a)


def orbit_ruins():
    """The Orbit Ruins: ancient ruins broken loose and circling a dim dead core, broken stone rings and boulders
    in slow orbits, a tumbling stair and fallen colonnades on drifting rock; muted violet and slate, the Jade River
    a faint thread through the far nebula."""
    layers = []
    stops = [(0.0, "#0b0a15"), (0.2, "#13111e"), (0.36, "#1b1929"), (0.48, "#242236"), (0.57, "#2e2b42"),
             (0.63, "#3a354e"), (0.66, "#48405a"), (0.68, "#3e3850"), (0.72, "#302c42"), (0.8, "#221f32"),
             (1.0, "#100e1a")]
    glow_y = 240
    sky = field_sky(stops, "or", glow_y, up=460, down=220, pal=R("#26243a", "#48445e", "#8a86a0", "#d0cce0",
                                                                 "#ffffff"))
    nebula(sky, "orn_v", 110, 24, 26, "#7a68a8", alphas=(0.04, 0.07, 0.1), k=(1, 2), cell=80, gaps=0.2)
    nebula(sky, "orn_lo", 296, 18, 28, "#5a5a88", alphas=(0.04, 0.07, 0.09), k=(1, 3), cell=70, gaps=0.2)
    lantern_ribbon(sky, "orjr", 292, 12, 10, alphas=(0.05, 0.08, 0.1), density=0.5)
    layers.append((sky, 0.0, 720))

    # ---------------- far: the dim core and its orbits: broken rings, boulders riding them
    fh = 220
    far = Canvas(W, fh)
    yy, xx, _ = grids(fh)
    ccx, ccy, cr = 330, 104, 30
    ring_r = R("#2a283a", "#343248", "#403c56", "#4c4864", "#5c5874")
    for (rx, ry, tilt, wd, arcs, sd) in ((96, 22, -0.12, 5, ((0.3, 2.2), (2.6, 4.4), (4.9, 6.0)), "o1"),
                                         (140, 34, 0.08, 4, ((0.9, 2.9), (3.5, 5.6)), "o2")):
        orbit_path(far, ccx, ccy, rx, ry, tilt, "#7a7098", a=0.3)
        orbit_ring(far, ccx, ccy, rx, ry, tilt, wd, ring_r, ("orf", sd), arcs=arcs, part="back")
    for s_, a in ((2.4, 0.03), (1.8, 0.05), (1.35, 0.08)):
        flat(far, wellipse(fh, ccx, ccy, cr * s_, cr * s_), "#8a74b8", a)
    core = wellipse(fh, ccx, ccy, cr, cr)
    d = wdx(xx, ccx) / cr + (yy - ccy) / cr
    paint(far, core, R("#141220", "#1c1a2c", "#26223a", "#322c48", "#433a5c"), 2.0 - d * 1.2 + (pn2(fh, "orcore", 8, 6, 2) - 0.5) * 1.2, sharp=3)
    flat(far, ring_px(core) & (d < -0.3), "#9a88c8")
    flat(far, ring_px(core) & (d > 0.5), "#5a4a7a", 0.6)
    for (rx, ry, tilt, wd, arcs, sd) in ((96, 22, -0.12, 5, ((0.3, 2.2), (2.6, 4.4), (4.9, 6.0)), "o1"),
                                         (140, 34, 0.08, 4, ((0.9, 2.9), (3.5, 5.6)), "o2")):
        orbit_ring(far, ccx, ccy, rx, ry, tilt, wd, ring_r, ("orf", sd), arcs=arcs, part="front")
    g = rng("orfb")
    boul = R("#221f30", "#2c283c", "#383248", "#463e56", "#564c68")
    for k in range(9):
        rx, ry, tilt = ((96, 22, -0.12), (140, 34, 0.08), (190, 48, -0.05))[k % 3]
        t = g.uniform(0, 2 * math.pi)
        u, v = rx * math.cos(t), ry * math.sin(t)
        bx = ccx + math.cos(tilt) * u - math.sin(tilt) * v
        by = ccy + math.sin(tilt) * u + math.cos(tilt) * v
        if v < 0 and abs(bx - ccx) < cr and abs(by - ccy) < cr:
            continue
        rs = g.uniform(2.5, 5.5)
        rock_blob(far, bx, by + rs, rs * 1.2, rs, boul, ("orfbb", k), facets=3)
    orbit_path(far, ccx, ccy, 190, 48, -0.05, "#6a6088", a=0.22)
    for i, (cx, top, hw, dp) in enumerate(((60, 150, 26, 22), (560, 140, 30, 26), (180, 176, 14, 12))):
        behind = sky_at(stops, far, 560, top)
        field_isle(far, cx, top, hw, dp, hazed(R("#1a1826", "#222030", "#2c283c", "#383248", "#463e56", "#564c68"),
                                                behind, 0.35), ("orfi", i), mixc("#b0a0d0", behind, 0.4),
                   mixc("#6a6a9a", behind, 0.4), spurs=2)
        lantern_star(far, cx + hw * 0.3, top - 20, 2.4, ("orfs", i), lit=0.7, halo=0.7, rays=0.6,
                     tether=(cx, top), sag=3)
        for c_ in range(2):
            px_ = int(cx - hw * 0.4 + c_ * hw * 0.6)
            cm = wrect(fh, px_, top - 12 + c_ * 4, px_ + 3, top)
            flat(far, cm, mixc("#5a5470", behind, 0.35))
            flat(far, left_rim(cm), mixc("#8a84a0", behind, 0.35))
    layers.append((far, 0.08, 560))

    # ---------------- mid: the ruins adrift: a great broken ring gate, a fallen colonnade, the tumbling stair
    mh = 280
    mid = Canvas(W, mh)
    yy, xx, _ = grids(mh)
    rock_m = R("#110f1a", "#181524", "#201c2e", "#2a2538", "#363044", "#443c52", "#564c64")
    slate = R("#2a2a3a", "#3a3a4c", "#4c4c60", "#606074", "#76768a", "#9090a2")
    # the ring gate on its isle, broken through at its crown, a chunk of it floating free
    gcx, gcy, gr = 150, 124, 50
    m1, tp1 = field_isle(mid, gcx, 188, 64, 50, rock_m, "ormi1", "#b8a8d8", "#6a6aa8", haze="#221e36", spurs=2)
    for s_, a in ((1.0, 0.04), (0.8, 0.06), (0.6, 0.08)):
        flat(mid, wellipse(mh, gcx, gcy, (gr - 9) * s_, (gr - 9) * s_) & (yy <= int(tp1[gcx % W])), "#9a80e0", a)
    ring = wellipse(mh, gcx, gcy, gr, gr) & ~wellipse(mh, gcx, gcy, gr - 9, gr - 9)
    ang = np.arctan2(yy - gcy, wdx(xx, gcx))
    ring &= ~((ang > -1.95) & (ang < -1.35))
    ring &= yy <= int(tp1[gcx % W]) + 1
    ashlar(mid, ring, slate[:5], "orring", course=5, joint=10)
    flat(mid, ring & (wdx(xx, gcx) + (yy - gcy) > gr * 0.4), slate[1])
    flat(mid, ring_px(ring) & (wdx(xx, gcx) + (yy - gcy) < 0), slate[5])
    inner = ring & sh(~ring, 0, -1) & (yy > gcy)
    flat(mid, inner, slate[4])
    rune = ring & (np.abs(np.hypot(wdx(xx, gcx), yy - gcy) - (gr - 4.5)) < 0.6) & ((np.floor(ang * 9) % 3) == 0)
    flat(mid, rune, "#9a8ad0")
    chunk = wpoly(mh, [(gcx - 16, gcy - gr - 16), (gcx - 4, gcy - gr - 20), (gcx + 6, gcy - gr - 12),
                       (gcx - 4, gcy - gr - 6), (gcx - 14, gcy - gr - 8)])
    ashlar(mid, chunk, slate[:5], "orchunk", course=5, joint=10)
    flat(mid, top_rim(chunk), slate[5])
    orbit_path(mid, gcx, gcy, gr + 22, 14, -0.2, "#8a80b0", a=0.3)
    g = rng("ormb")
    for k in range(5):
        t = k / 5.0 * 2 * math.pi + 0.4
        u, v = (gr + 22) * math.cos(t), 14 * math.sin(t)
        bx, by = gcx + math.cos(-0.2) * u - math.sin(-0.2) * v, gcy + math.sin(-0.2) * u + math.cos(-0.2) * v
        rs = g.uniform(3, 6)
        rock_blob(mid, bx, by + rs, rs * 1.2, rs, rock_m, ("ormbb", k), facets=3)
    # the fallen colonnade on its isle: broken columns, a tilted architrave floating over them
    m2, tp2 = field_isle(mid, 450, 196, 84, 58, rock_m, "ormi2", "#b8a8d8", "#6a6aa8", haze="#221e36", spurs=3,
                         cap=R("#2a2838", "#6a6680"))
    g = rng("orcol")
    for k, (px_, ht) in enumerate(((396, 62), (424, 38), (452, 76), (480, 24), (508, 54))):
        by = int(tp2[px_ % W]) + 1
        cm = tomb_pillar(mid, px_, by - ht, by, 5, slate, ("orp", k), courses=9)
        brk = cm & (yy < by - ht + 4) & (pn2(mh, ("orbrk", k), 2, 2, 1) > 0.45)
        mid.a[brk] = 0.0
    arch = wpoly(mh, [(392, 104), (470, 92), (471, 98), (393, 110)])
    ashlar(mid, arch, slate[:5], "orarch", course=3, joint=16)
    flat(mid, top_rim(arch), slate[5])
    flat(mid, bot_rim(arch), slate[0])
    for k, (dx_, dy_) in enumerate(((-6, -8), (8, -14), (40, -4))):
        rock_blob(mid, 470 + dx_, 92 + dy_, 3, 2.5, slate, ("orfr", k), facets=2)
    # the tumbling stair: a flight of steps on a tilted slab, drifting
    slab = wpoly(mh, [(246, 76), (294, 50), (298, 56), (250, 84)])
    rock_mass(mid, slab, rock_m, "orslab", gain=1.0)
    for k in range(9):
        sx, sy = 250 + k * 5, 74 - k * 2.8
        st = wrect(mh, int(sx), int(sy) - 3, int(sx) + 4, int(sy))
        flat(mid, st, slate[3])
        flat(mid, top_rim(st), slate[5])
        flat(mid, right_rim(st), slate[1])
    orbit_path(mid, 450, 130, 120, 26, 0.06, "#8a80b0", a=0.25)
    lantern_star(mid, 560, 60, 7, "orms0", tether=(512, int(tp2[512 % W])), sag=8)
    lantern_star(mid, 96, 40, 6, "orms1", lit=0.0, ember="#4a4070", tether=(120, int(tp1[120 % W])), sag=10)
    layers.append((mid, 0.18, 620))

    # ---------------- near: boulders and a column drum drifting close, an orbit sweeping past, mist below
    nh = 200
    near = Canvas(W, nh)
    yy, xx, _ = grids(nh)
    mist_band(near, 176, 26, "ornm", "#5a5288", alphas=(0.05, 0.08, 0.12), amp=6, cell=100, gaps=0.1)
    orbit_path(near, 320, 150, 360, 40, -0.04, "#9a90c0", a=0.3, dash=8)
    rock_n = R("#0a0910", "#100e18", "#161420", "#1e1a2a", "#282236", "#342c44")
    for k, (bx, by, rx, ry) in enumerate(((250, 130, 14, 11), (560, 186, 30, 24), (420, 96, 9, 7), (610, 120, 8, 6))):
        m = rock_blob(near, bx, by, rx, ry, rock_n, ("ornb", k), facets=5, rough=0.24)
        flat(near, top_rim(m) & (wdx(xx, bx) < rx * 0.3), "#8a7cb0")
        flat(near, bot_rim(m), "#4a4880")
    # a slab of dressed wall broken loose, adrift close by, its blocks still coursed
    wall_n = wpoly(nh, [(10, 150), (60, 138), (112, 146), (120, 160), (104, 176), (116, 196), (30, 204), (0, 186)])
    wall_n &= ~(wellipse(nh, 64, 136, 10, 6) | wellipse(nh, 112, 170, 6, 8))
    ashlar(near, wall_n, R("#141220", "#1c1a2a", "#242236", "#2e2c42", "#3a384e"), "ornw", course=8, joint=16)
    flat(near, top_rim(wall_n), "#8a7cb0")
    flat(near, bot_rim(wall_n) | right_rim(wall_n), "#0a0910")
    flat(near, sh(bot_rim(wall_n), 0, 0) & (yy > 180), "#4a4880")
    drum = wellipse(nh, 350, 150, 10, 5)
    drum |= wrect(nh, 340, 150, 360, 162)
    drum_b = wellipse(nh, 350, 162, 10, 5)
    flat(near, drum | drum_b, slate[2])
    flat(near, wellipse(nh, 350, 150, 10, 5), slate[4])
    flat(near, ring_px(wellipse(nh, 350, 150, 10, 5)), slate[5])
    flat(near, (drum | drum_b) & (wdx(xx, 350) > 5), slate[1])
    for fx in range(343, 358, 3):
        flat(near, wrect(nh, fx, 154, fx, 163), slate[1])
    layers.append((near, 0.32, 720))
    return dict(sky="#0b0a15", horizon="#48405a", layers=layers)


def pyre(cv, x, by, w, ht, seed, logs=R("#140a08", "#2a140c", "#4a2412"), flame=R("#a01c0c", "#e8501a", "#ffb040",
                                                                                   "#fff0b0"), glow="#ff6a20", sparks=12):
    """A war pyre: logs stacked crosswise into a squat tower, their ends glowing, flames in ragged tongues climbing
    from it (deep red rims, orange body, yellow-white hearts), a stepped glow and sparks flying up."""
    h = cv.h
    yy, xx, _ = grids(h)
    g = rng("pyre", seed)
    for s_, a in ((2.2, 0.04), (1.6, 0.07), (1.15, 0.1)):
        flat(cv, wellipse(h, x, by - ht * 0.45, w * s_, ht * s_ * 0.75), glow, a)
    lh = max(2, int(ht * 0.12))
    stack = np.zeros((h, W), bool)
    for k in range(int(ht * 0.45 / lh)):
        yk = by - k * lh
        wk = w * (1 - k * 0.1)
        lm = wrect(h, int(x - wk / 2), yk - lh + 1, int(x + wk / 2), yk)
        flat(cv, lm, logs[1 + (k % 2)])
        flat(cv, top_rim(lm), logs[2])
        flat(cv, bot_rim(lm), logs[0])
        if k % 2 == 0:
            for ex in (int(x - wk / 2), int(x + wk / 2)):
                put(cv, ex, yk - lh // 2, flame[1])
        stack |= lm
    ftop = by - int(ht * 0.45) + 1
    for k in range(7):
        fx = x + (k - 3) * w * 0.14 + g.uniform(-1, 1)
        fh_ = ht * g.uniform(0.45, 0.9) * (1 - abs(k - 3) * 0.12)
        fw = w * g.uniform(0.1, 0.16)
        lean = g.uniform(-0.3, 0.5)
        tongue = wpoly(h, [(fx - fw, ftop + 2), (fx + fw, ftop + 2), (fx + fw * 0.3 + lean * fh_ * 0.4, ftop - fh_ * 0.6),
                           (fx + lean * fh_ * 0.5, ftop - fh_), (fx - fw * 0.4 + lean * fh_ * 0.2, ftop - fh_ * 0.5)])
        flat(cv, tongue, flame[0])
        core = tongue & ~ring_px(tongue)
        flat(cv, core, flame[1])
        flat(cv, core & (yy > ftop - fh_ * 0.45) & ~ring_px(core), flame[2])
    flat(cv, wellipse(h, x, ftop, w * 0.25, 2) , flame[3])
    for k in range(sparks):
        put(cv, x + g.normal(0, w * 0.4), ftop - ht * 0.6 - g.uniform(0, ht * 1.2), flame[2 + (k % 2)],
            0.9 if k % 3 else 0.6)


def ash_fall(cv, seed, count, y0, y1, pal, streak=True, big=0):
    """Ash falling on the wind: grey flakes drifting down and to the right, each a speck trailing a fainter one;
    `big` of them are 2 px flakes."""
    g = rng("ash", seed)
    for i in range(count):
        x = int(g.integers(0, W))
        y = int(g.integers(y0, y1))
        c = pal[int(g.integers(0, len(pal)))]
        if i < big:
            flat(cv, wrect(cv.h, x, y, x + 1, y), c)
            put(cv, x, y + 1, c, 0.7)
            if streak:
                put(cv, x - 2, y - 1, c, 0.35)
            continue
        put(cv, x, y, c, 0.9)
        if streak and i % 2 == 0:
            put(cv, x - 1, y - 1, c, 0.4)


def ashen_reach():
    """The Ashen Reach: ash plains on a scorched island chain under a smouldering red-orange sky, the Ashborn's war
    pyres burning on the far isles, banners, palisades and burnt trees, ash falling everywhere; the Jade River shows
    faint and green through the smoke overhead."""
    layers = []
    stops = [(0.0, "#140606"), (0.16, "#200a08"), (0.3, "#300f0a"), (0.42, "#46150c"), (0.52, "#621c0e"),
             (0.59, "#842a10"), (0.635, "#aa4014"), (0.66, "#d05c1c"), (0.675, "#e47a2a"), (0.69, "#c45820"),
             (0.72, "#883216"), (0.78, "#541c10"), (0.88, "#2e0e0a"), (1.0, "#170706")]
    glow_y = 243
    sky = sky_layer(stops, bands=28, sharp=2.4)
    stars(sky, "arst", 140, 0, 150, R("#3a1a18", "#6a3a30", "#b08070", "#f0d0c0"), twinkle=9)
    lantern_ribbon(sky, "arjr", 56, 20, 11, alphas=(0.04, 0.06, 0.08), density=0.35)
    for i, (y, a) in enumerate(((110, 0.08), (160, 0.1), (200, 0.12))):
        nebula(sky, ("arsm", i), y, 14, 22 + i * 4, "#2a0e0a", alphas=(a * 0.6, a), k=(1, 2), cell=60, gaps=0.1)
    nebula(sky, "arn_lo", 296, 18, 26, "#3a0e0a", alphas=(0.08, 0.12, 0.16), k=(1, 3), cell=80, gaps=0.1)
    for i, (cx, y, ln) in enumerate(((110, 226, 200), (390, 236, 240), (570, 214, 150), (260, 200, 120))):
        streak(sky, cx, y, ln, R("#6a2210", "#b8481a", "#f0943a"), ("ars", i), rows=2)
    ash_fall(sky, "arsky", 420, 0, SKY_H, R("#5a3a34", "#7a5a52", "#a08478", "#c8b0a0"))
    for i in range(30):
        g = rng("arem", i)
        put(sky, int(g.integers(0, W)), int(g.integers(150, 300)), "#ff9a3a" if i % 3 else "#ffd070", 0.8)
    layers.append((sky, 0.0, 720))

    # ---------------- far: the scorched island chain along the glow, pyres burning on it, smoke leaning off
    fh = 220
    far = Canvas(W, fh)
    yy = grids(fh)[0]
    rock = R("#1a0a08", "#240e0a", "#30140c", "#3e1a0e", "#4e2210", "#602c14")
    chain_isles = [(30, 168, 40, 16), (140, 176, 30, 12), (250, 162, 48, 18), (370, 178, 26, 10), (470, 166, 44, 16),
                   (590, 174, 30, 12), (320, 120, 14, 14), (540, 106, 12, 12)]
    for i, (cx, top, hw, dp) in enumerate(chain_isles):
        behind = sky_at(stops, far, 560, top)
        ramp = hazed(rock, behind, 0.3)
        m, tp = field_isle(far, cx, top, hw, dp, ramp, ("arfi", i), mixc("#ff8a3a", behind, 0.3),
                           mixc("#8a2a1a", behind, 0.35), spurs=2)
        if i in (6, 7):
            lantern_star(far, cx, top - 16, 2.4, ("arfs", i), lit=0.5, halo=0.6, rays=0.5, tether=(cx - 3, top), sag=2,
                         glow="#ffa050")
        if i in (0, 2, 4, 5):
            px_ = int(cx + hw * 0.2)
            smoke_plume(far, px_ + 2, int(tp[px_ % W]) - 6, 70, "#2a100c", ("arfsp", i), width=6, lean=0.7,
                        alphas=(0.1, 0.16, 0.22))
            pyre(far, px_, int(tp[px_ % W]), 6, 12, ("arfp", i), glow="#ff7a2a", sparks=5)
        for k in range(int(hw // 10)):
            sx = int(cx - hw * 0.7 + k * 10)
            flat(far, wrect(fh, sx, int(tp[sx % W]) - 3, sx, int(tp[sx % W])), mixc("#140806", behind, 0.2))
    layers.append((far, 0.08, 560))

    # ---------------- mid: an ash plain on its scorched isle: dunes of ash, burnt trees, the palisade, Kharn's pyre
    mh = 260
    mid = Canvas(W, mh)
    yy, xx, _ = grids(mh)
    rock_m = R("#100606", "#180a08", "#220e0a", "#2e140c", "#3c1a0e", "#4c2212", "#5e2c16")
    icx, itop, ihw = 320, 196, 250
    ash = R("#1a100e", "#261814", "#34201a", "#442a20", "#5a3626", "#7a4a2e", "#b06a38")
    tmp = Canvas(W, mh)
    dune_row(tmp, itop + 2, "ard", ash, 7, itop - 16, itop - 7, 40, 70, shade=2, ripples=0.3, amp=1.0)
    tmp.a[(np.abs(wdx(xx, icx)) >= ihw - 14) | (yy > itop + 3)] = 0.0
    mid.paste(tmp)
    isle, itp = field_isle(mid, icx, itop, ihw, 56, rock_m, "armi", "#ff7a30", "#7a2a1a", haze="#2a0c08", spurs=4,
                           cap=R("#2a1c1c", "#5a4038"))
    # the Ashborn palisade: sharpened stakes along the plain, a gate gap
    for x in range(icx - 200, icx - 40, 4):
        top = itop - 14 - int((pn1("arpal", 3, 1)[x % W]) * 4)
        st = wpoly(mh, [(x - 1, itop + 1), (x + 1.5, itop + 1), (x + 1.5, top + 2), (x + 0.25, top), (x - 1, top + 2)])
        flat(mid, st, "#1a0c08")
        flat(mid, left_rim(st), "#8a3a1a")
    flat(mid, wrect(mh, icx - 200, itop - 8, icx - 40, itop - 7), "#2a140c")
    # burnt trees on the plain
    for k, (tx, th) in enumerate(((icx + 40, 36), (icx + 170, 44), (icx - 220, 30))):
        dead_tree(mid, tx, itop, th, R("#0e0606", "#1c0e0a", "#6a2a14"), ("ardt", k), lean=0.2, spread=0.9, width=2)
    # the war banners of the Ashborn
    flame_sign = [".X.", "XXX", "X.X"]
    pole = R("#140806", "#2a140c", "#6a3a1e")
    cloth = R("#2a0806", "#4a0e0a", "#7a1a10", "#a82a16")
    for k, (bx, ht) in enumerate(((icx - 196, 60), (icx - 44, 60), (icx + 110, 50))):
        war_banner(mid, bx, itop + 1, ht, pole, cloth, "#f0a040", ("arb", k), bl=26, bw=9, trim="#c07030",
                   sign=flame_sign)
    # Kharn's pyre, the great one, at the heart of the plain, and over it a captured lantern star hung from a
    # gallows of charred beams, chained down to feed the fire
    px_ = icx - 120
    smoke_plume(mid, px_ + 4, itop - 60, 150, "#241008", "argsp", width=14, lean=0.5, alphas=(0.08, 0.13, 0.18))
    for bx in (px_ - 34, px_ + 34):
        beam = wline(mh, [(bx, itop), (px_ + (bx - px_) * 0.3, itop - 112)], 2)
        flat(mid, beam, "#140806")
        flat(mid, left_rim(beam), "#7a3418")
    flat(mid, wrect(mh, px_ - 16, itop - 114, px_ + 16, itop - 112), "#140806")
    flat(mid, wrect(mh, px_ - 16, itop - 114, px_ + 16, itop - 114), "#8a3a1a")
    lantern_star(mid, px_, itop - 94, 9, "arcapt", hang=(px_, itop - 112), star=R("#e8803a", "#ffc070", "#ffe8b8",
                                                                                 "#ffffff"), glow="#ffa050", rays=0.8)
    for sx in (-1, 1):
        chain(mid, sag_pts(px_ + sx * 3, itop - 84, px_ + sx * 22, itop - 20, 4), R("#140806", "#4a2412", "#8a4a22"))
    pyre(mid, px_, itop - 2, 26, 50, "argp", sparks=24)
    ash_fall(mid, "armid", 140, 0, mh, R("#6a4a42", "#8a6a5e", "#b09888"), big=20)
    layers.append((mid, 0.18, 620))

    # ---------------- near: drifts of ash at the viewer's feet, charred stakes, embers, flakes falling close
    nh = 200
    near = Canvas(W, nh)
    yy, xx, _ = grids(nh)
    ash_n = R("#0e0808", "#150c0a", "#1e120e", "#2a1812", "#3a2016", "#562c1a", "#a0502a")
    ground, lit, crests = dune_row(near, 156, "arnd", ash_n, 7, 118, 144, 44, 80, shade=2, ripples=0.5, amp=2.0)
    g = rng("arstake")
    for k in range(7):
        x = int(g.uniform(0, W))
        by = int(ground[x]) + 2
        ht = int(g.uniform(14, 30))
        lean = g.uniform(-4, 4)
        st = wpoly(nh, [(x - 1.5, by), (x + 1.5, by), (x + 1 + lean, by - ht + 3), (x + lean, by - ht), (x - 1 + lean, by - ht + 3)])
        flat(near, st, "#0e0606")
        flat(near, left_rim(st), "#7a2e14")
        put(near, x + lean, by - ht, "#ff8a3a")
    for i in range(24):
        g = rng("arnem", i)
        x, y = int(g.integers(0, W)), int(g.integers(20, 190))
        put(near, x, y, "#ffb050" if i % 3 else "#fff0a0")
        if i % 4 == 0:
            put(near, x - 1, y + 1, "#ff6a20", 0.6)
    ash_fall(near, "arnear", 90, 0, nh, R("#7a5a52", "#a08478", "#c8b0a0"), big=40)
    layers.append((near, 0.32, 720))
    return dict(sky="#140606", horizon="#e47a2a", layers=layers)


WARDEN_STAR = ["..X..", ".XXX.", "XXXXX", ".XXX.", "..X.."]   # the Star Wardens' sign


def rampart(cv, x0, x1, top, by, pal, seed, merlon=6, gap=4, rim=None):
    """A fortress wall from x0 to x1 (wrapping): dressed courses, a crenellated parapet (merlons and embrasures),
    a wall-walk shadow line and arrow slits. pal dark->light (>= 5). Returns its mask."""
    h = cv.h
    yy, xx, _ = grids(h)
    cw = (x1 - x0) % W
    body = wrect(h, x0, top, x0 + cw, by)
    rel = (xx - x0) % W
    crenel = wrect(h, x0, top - 5, x0 + cw, top - 1) & ((rel % (merlon + gap)) < merlon)
    m = body | crenel
    ashlar(cv, m, pal[:5], ("ramp", seed), course=6, joint=32)
    flat(cv, top_rim(m), pal[-1] if rim is None else rim)
    flat(cv, body & (yy == top + 1), pal[0])
    slit = body & ((rel % 24) == 12) & (yy > top + 4) & (yy < top + 9)
    flat(cv, slit, pal[0])
    return m


def tidebreak_front():
    """The Tidebreak Front: the Star Wardens' fortress wall strung along a chain of islands, facing the Hollow Tide
    as it creeps in on the horizon, a grey-violet wall that drains the colour from all it touches under a sickly
    violet glow, the lanterns in its path gone dark; a few lanterns still lit on the ramparts, the Jade River bright
    above."""
    layers = []
    stops = [(0.0, "#070a20"), (0.2, "#0c1230"), (0.36, "#141a40"), (0.48, "#1d214e"), (0.56, "#282856"),
             (0.61, "#38325e"), (0.645, "#56466c"), (0.665, "#7a5c88"), (0.68, "#6a5a76"), (0.71, "#4e4a5c"),
             (0.77, "#38364a"), (0.87, "#242230"), (1.0, "#131218")]
    glow_y = 240
    sky = sky_layer(stops, bands=28, sharp=2.4)
    stars(sky, "tfup", 520, 0, glow_y, LS_STARS, twinkle=8)
    under_stars(sky, "tfdn", 120, glow_y, SKY_H, R("#34323c", "#4e4c56", "#76747e", "#a4a2aa", "#c8c6cc"))
    star_river(sky, "tfjr", 58, 22, 13, "#62dc92", JADE_STARS, alphas=(0.05, 0.08, 0.12), density=0.7)
    nebula(sky, "tfn_v", 170, 16, 24, "#8a50c8", alphas=(0.05, 0.08, 0.11), k=(1, 2), cell=80, gaps=0.15)
    mist_band(sky, glow_y + 6, 44, "tfglow", "#a060e0", alphas=(0.05, 0.07, 0.1), amp=4, cell=120, gaps=0.0)
    nebula(sky, "tfn_lo", 296, 16, 30, "#5a5668", alphas=(0.06, 0.1, 0.14), k=(1, 3), cell=70, gaps=0.1)
    layers.append((sky, 0.0, 720))

    # ---------------- far: the Hollow Tide on the horizon, a grey wall swallowing the islands and their lanterns
    fh = 220
    far = Canvas(W, fh)
    yy, xx, _ = grids(fh)
    rock = R("#1a1c34", "#222440", "#2c2e4c", "#383a5a", "#464868", "#58587a")
    for i, (cx, top, hw, dp, lit) in enumerate(((50, 100, 24, 22, 0.0), (180, 60, 18, 18, 0.9), (300, 106, 28, 24, 0.0),
                                               (430, 50, 20, 18, 0.8), (560, 98, 24, 20, 0.0), (250, 26, 10, 10, 1.0))):
        behind = sky_at(stops, far, 560, top)
        grey = 0.25 if lit else 0.55
        ramp = hazed(rock, mixc(behind, "#5a5866", 0.5 if not lit else 0.0), grey)
        field_isle(far, cx, top, hw, dp, ramp, ("tffi", i), mixc("#e0c8ff", behind, 0.4), mixc("#9a7ac8", behind, 0.4),
                   spurs=2)
        lantern_star(far, cx + 4, top - 16 - hw * 0.3, 2.4 + hw * 0.05, ("tffs", i), lit=lit, ember="#6a6278",
                     halo=0.7, rays=0.6, tether=(cx, top), sag=3)
    tide = R("#1c1a24", "#24212d", "#2c2936", "#353140", "#403b4c", "#4e485a", "#9c78c8")
    mist_band(far, 102, 36, "tfglow_f", "#b070f0", alphas=(0.035, 0.05, 0.07), amp=5, cell=100, gaps=0.0)
    cloud_bank(far, 112, "tftide", tide, r_lo=8, r_hi=18, rows=4, row_gap=14, amp=7, fill_below=True)
    tm = far.a > 0.99
    flat(far, tm & (yy < 150) & (pn2(fh, "tfsick", 30, 8, 2) > 0.45), "#8a50c0", 0.14)
    flat(far, top_rim(tm) & (yy > 80), "#c890ff", 0.7)
    haze_fade(far, tm, "#26232e", np.clip((yy - 130) / 60.0, 0, 1) * 0.6, steps=3, sharp=4)
    for i, (cx, y, ln) in enumerate(((90, 100, 110), (330, 108, 140), (520, 96, 90), (220, 122, 80))):
        streak(far, cx, y, ln, R("#4a4456", "#6c6676", "#b890e8"), ("tfts", i), rows=2)
    layers.append((far, 0.08, 560))

    # ---------------- mid: the wall line on its chain of islands, towers, a few lanterns still lit
    mh = 280
    mid = Canvas(W, mh)
    yy, xx, _ = grids(mh)
    rock_m = R("#0e1024", "#141630", "#1c1e3c", "#262848", "#303456", "#3e4266", "#505478")
    stone = R("#262a40", "#30344c", "#3c4058", "#4a4e66", "#5c6078", "#7a7e96")
    isles = [(60, 242, 70, 34), (250, 246, 60, 30), (440, 240, 72, 36), (600, 244, 40, 28)]
    tops = []
    for i, (cx, top, hw, dp) in enumerate(isles):
        m, tp = field_isle(mid, cx, top, hw, dp, rock_m, ("tfmi", i), "#e0c890", "#8a6ac0", haze="#1c1a36", spurs=2)
        tops.append(tp)
    tp_all = np.minimum.reduce(tops)
    # the wall: continuous along the islands, bridging the gaps between them on arches
    wall_top, wall_by = 192, 246
    wm = rampart(mid, 0, W - 1, wall_top, wall_by, stone, "tfw", rim="#8a88a8")
    haze_fade(mid, wm, "#0e0e1c", np.clip((yy - wall_top - 10) / 50.0, 0, 1) * 0.5, steps=3, sharp=4)
    for gx in (152, 346, 526):
        arch = wellipse(mh, gx, wall_by, 24, 30)
        mid.a[arch & wm & (yy > wall_top + 12)] = 0.0
        flat(mid, ring_px(arch) & (yy > wall_top + 10) & (yy < wall_by), stone[5])
    # towers with bronze caps, lantern stars on some, dark cages on others
    for k, (tx, lit) in enumerate(((40, 1.0), (250, 0.0), (440, 1.0), (620, 0.0))):
        tw, th = 22, 58
        tm = wrect(mh, tx - tw // 2, wall_top - th + 20, tx + tw // 2, wall_by)
        ashlar(mid, tm, stone[:5], ("tft", k), course=5, joint=16)
        flat(mid, left_rim(tm), stone[4])
        flat(mid, right_rim(tm), stone[0])
        ttop = wall_top - th + 20
        cren = wrect(mh, tx - tw // 2 - 2, ttop - 5, tx + tw // 2 + 2, ttop) & ((xx % 6) < 4)
        flat(mid, cren, stone[3])
        flat(mid, top_rim(cren), "#8a88a8")
        roof = wpoly(mh, [(tx - tw // 2 - 1, ttop - 5), (tx + tw // 2 + 1, ttop - 5), (tx, ttop - 22)])
        flat(mid, roof, LS_CAGE[2])
        flat(mid, roof & (wdx(xx, tx) < 0), LS_CAGE[3])
        flat(mid, right_rim(roof), LS_CAGE[0])
        for wy_ in (ttop + 8, ttop + 20):
            flat(mid, wrect(mh, tx - 1, wy_, tx + 1, wy_ + 4), "#f4c070" if lit else "#1a1a2a")
        lantern_star(mid, tx + 2, ttop - 46, 7, ("tfms", k), lit=lit, ember="#5a5470", hang=None,
                     tether=(tx, ttop - 22), sag=1)
    # the lamps still burning on the ramparts, and a Warden banner
    lan = R("#2a1a1a", "#ff9a3a", "#ffd890")
    for k, lx in enumerate((96, 120, 300, 480, 504)):
        flat(mid, wrect(mh, lx, wall_top - 14, lx, wall_top - 5), "#141628")
        flat(mid, wrect(mh, lx, wall_top - 14, lx + 2, wall_top - 14), "#141628")
        lantern(mid, lx + 2, wall_top - 13, lan, glow="#ffb050")
    for k, bx in enumerate((200, 390, 560)):
        war_banner(mid, bx, wall_top - 5, 40, R("#141628", "#2a2c40", "#8a88a8"), R("#10224a", "#1a3470", "#2a4a94",
                                                                                   "#4a6ab8"), "#f0c870", ("tfb", k),
                   bl=18, bw=8, trim="#e8c880", sign=WARDEN_STAR if k == 1 else [".X.", "XXX", ".X."])
    layers.append((mid, 0.18, 620))

    # ---------------- near: the parapet the defenders stand behind, a lamp post, the grey murk below
    nh = 200
    near = Canvas(W, nh)
    yy, xx, _ = grids(nh)
    mist_band(near, 150, 30, "tfnm", "#5a5468", alphas=(0.06, 0.1, 0.14), amp=6, cell=100, gaps=0.05)
    stone_n = R("#12141f", "#181a28", "#1e2132", "#262a3e", "#30344a", "#4a4e66")
    par = rampart(near, 0, W - 1, 168, nh, stone_n, "tfnp", merlon=14, gap=8, rim="#6a6888")
    haze_fade(near, par, "#0a0a12", np.clip((yy - 172) / 30.0, 0, 1) * 0.5, steps=3, sharp=4)
    for k, lx in enumerate((110, 430)):
        flat(near, wrect(nh, lx, 110, lx + 1, 163), "#0e0f1a")
        flat(near, wrect(nh, lx - 1, 108, lx + 12, 109), "#0e0f1a")
        lantern(near, lx + 10, 110, lan, glow="#ffb050")
        flat(near, wellipse(nh, lx + 11, 113, 30, 22), "#ffb050", 0.04)
    war_banner(near, 250, 164, 70, R("#0e0f1a", "#22243a", "#6a6888"), R("#0c1a3a", "#142a5c", "#223e80", "#3a5aa4"),
               "#f0c870", "tfnb", bl=30, bw=11, trim="#e8c880", sign=WARDEN_STAR)
    layers.append((near, 0.32, 720))
    return dict(sky="#070a20", horizon="#7a5c88", layers=layers)


def nebula_cloud(cv, cx, cy, rx, ry, col, seed, alphas=(0.05, 0.08, 0.11, 0.14), rim=None):
    """A huge soft cloud of nebula: a lumpy blob of flat translucent steps, frayed at its edges into wisps; an
    optional lit rim along its upper edge."""
    h = cv.h
    yy, xx, _ = grids(h)
    d = np.sqrt((wdx(xx, cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    lump = pn2(h, ("nbl", seed), rx * 0.5, ry * 0.6, 2)
    wisp = pn2(h, ("nbwp", seed), rx * 0.9, 4, 2)
    total = np.zeros((h, W), bool)
    for i, a in enumerate(alphas):
        reach = (1.0 - i * 0.2) * (0.7 + 0.6 * lump) + (wisp - 0.5) * 0.35
        m = despeck(d < reach)
        flat(cv, m, col, a)
        total |= m
    if rim is not None:
        flat(cv, top_rim(total) & (pn2(h, ("nbr", seed), 8, 2, 1) > 0.4), rim, 0.35)
    return total


def star_coral(cv, x, by, ht, pal, tip, seed, spread=1.0, glow=None):
    """A star-coral: a branching colony rising from (x, by), limbs forking and curling upward, every tip swelling
    into a glowing bulb. pal = branch (dark, mid, light); tip = (body, core)."""
    h = cv.h
    g = rng("coral", seed)
    limbs = np.zeros((h, W), bool)
    tips = []

    def limb(x0, y0, ang, ln, wdt, depth):
        x1 = x0 + math.cos(ang) * ln
        y1 = y0 + math.sin(ang) * ln
        mx = (x0 + x1) / 2 + math.cos(ang + 1.57) * ln * 0.15 * g.uniform(-1, 1)
        my = (y0 + y1) / 2
        nonlocal limbs
        limbs |= wline(h, [(x0, y0), (mx, my), (x1, y1)], max(1, int(round(wdt))))
        if depth > 0 and ln > 3:
            for k in range(2 if g.random() < 0.75 else 3):
                na = ang + (k - 0.5) * 0.7 * spread + g.uniform(-0.25, 0.25)
                na = min(-0.35, max(-math.pi + 0.35, na))
                limb(x1, y1, na, ln * g.uniform(0.6, 0.8), wdt * 0.7, depth - 1)
        else:
            tips.append((x1, y1))

    stems = 3 if ht > 30 else 2
    for k in range(stems):
        a0 = -math.pi / 2 + (k - (stems - 1) / 2.0) * 0.45 * spread + g.uniform(-0.12, 0.12)
        limb(x + (k - (stems - 1) / 2.0) * 1.5, by, a0, ht * g.uniform(0.26, 0.34), max(1.5, ht * 0.055), 3)
    flat(cv, limbs, pal[1])
    flat(cv, left_rim(limbs), pal[2])
    flat(cv, right_rim(limbs), pal[0])
    for (tx, ty) in tips:
        if glow is not None:
            flat(cv, wellipse(h, tx, ty, 4, 4), glow, 0.12)
        flat(cv, wellipse(h, tx, ty, 1.6, 1.6), tip[0])
        put(cv, tx - 0.5, ty - 0.5, tip[1])
    return limbs


def nebula_deep():
    """The Nebula Deep: the field thins into open nebula, huge soft clouds of deep teal and magenta at every depth,
    floating reefs of star-coral glowing at their tips, a last lantern star or two adrift; the Jade River winds
    right through the clouds. Very quiet, very deep."""
    layers = []
    stops = [(0.0, "#030d14"), (0.2, "#06161f"), (0.36, "#0a2230"), (0.48, "#0e2c3c"), (0.56, "#123646"),
             (0.62, "#1c3c4e"), (0.66, "#2e3a56"), (0.69, "#4a2e56"), (0.72, "#40244c"), (0.8, "#281634"),
             (0.9, "#170c22"), (1.0, "#0b0612")]
    sky = field_sky(stops, "nd", 240, up=560, down=300, pal=R("#1c3440", "#3a5a6a", "#80a8b8", "#d0ecf0", "#ffffff"))
    for i, (cx, cy, rx, ry, col) in enumerate(((120, 90, 150, 60, "#20a8a8"), (430, 150, 190, 70, "#c03a98"),
                                               (620, 60, 120, 44, "#2ab0b0"), (300, 250, 200, 60, "#a0308a"),
                                               (60, 300, 150, 50, "#20888c"))):
        nebula_cloud(sky, cx, cy, rx, ry, col, ("ndsk", i), alphas=(0.04, 0.06, 0.08, 0.1, 0.12))
    star_river(sky, "ndjr", 196, 36, 13, "#62dc92", JADE_STARS, alphas=(0.05, 0.08, 0.12), density=0.75, k=(1, 3))
    g = rng("ndst")
    for i in range(160):
        put(sky, int(g.integers(0, W)), int(g.integers(0, SKY_H)), "#f0c8f0" if i % 3 else "#c8fff4", 0.7)
    layers.append((sky, 0.0, 720))

    # ---------------- far: the great soft clouds, coral reefs far off on their rocks, one far lantern star
    fh = 220
    far = Canvas(W, fh)
    yy, xx, _ = grids(fh)
    for i, (cx, cy, rx, ry, col, rim) in enumerate(((80, 150, 110, 40, "#1a7a80", "#6ae0d8"), (330, 120, 130, 36, "#8a2a78", "#f080d0"),
                                                    (560, 160, 120, 44, "#1c6a78", "#6ad0d8"))):
        nebula_cloud(far, cx, cy, rx, ry, col, ("ndf", i), alphas=(0.06, 0.1, 0.14, 0.18), rim=rim)
    rock = R("#0c1a24", "#12222e", "#1a2c3a", "#243848", "#304656")
    for i, (cx, top, hw, ht) in enumerate(((140, 128, 10, 30), (410, 110, 12, 36), (600, 140, 8, 24))):
        behind = sky_at(stops, far, 560, top)
        field_isle(far, cx, top, hw, 10, hazed(rock + [C("#3e5664")], behind, 0.35), ("ndfi", i),
                   mixc("#80f0e0", behind, 0.4), mixc("#f080d0", behind, 0.4), spurs=1)
        for k in range(2):
            star_coral(far, cx - hw * 0.4 + k * hw * 0.8, top + 1, ht * (0.8 + k * 0.3), hazed(R("#3a1a48", "#6a2a70",
                                                                                                    "#a04a98"), behind, 0.4),
                       R(mixc("#ff8ad8", behind, 0.3), "#ffe0f4"), ("ndfc", i, k), spread=1.1)
    lantern_star(far, 250, 60, 3.0, "ndfs", halo=0.7, rays=0.7, tether=(262, 96), sag=6)
    layers.append((far, 0.08, 560))

    # ---------------- mid: reefs of star-coral drifting on their rocks, glowing tips, clouds pouring between
    mh = 260
    mid = Canvas(W, mh)
    yy, xx, _ = grids(mh)
    nebula_cloud(mid, 320, 200, 260, 40, "#1a6a74", "ndmc0", alphas=(0.05, 0.08, 0.11, 0.14), rim="#8af0e8")
    rock_m = R("#08121a", "#0c1822", "#12202c", "#1a2a38", "#243646", "#304456", "#40586a")
    corals = (R("#3a1040", "#7a2478", "#c04ab0"), R("#0e3a44", "#1a6a70", "#3aaaa8"))
    tips = (R("#ff7ad0", "#fff0fa"), R("#6af0e0", "#f0fffc"))
    glows = ("#ff6ac8", "#5ae8d8")
    for i, (cx, top, hw, dp) in enumerate(((90, 170, 44, 34), (330, 150, 58, 40), (540, 180, 40, 30))):
        m, tp = field_isle(mid, cx, top, hw, dp, rock_m, ("ndmi", i), "#9af0e8", "#e070c0", haze="#16203a", spurs=2)
        g = rng("ndmcor", i)
        for k in range(3 + i % 2):
            px_ = int(cx - hw * 0.7 + (k + 0.5) * hw * 1.4 / (3 + i % 2))
            c = (i + k) % 2
            star_coral(mid, px_, int(tp[px_ % W]) + 1, g.uniform(40, 70), corals[c], tips[c], ("ndmco", i, k),
                       spread=g.uniform(0.9, 1.3), glow=glows[c])
    lantern_star(mid, 212, 40, 8, "ndms", tether=(300, int(150)), sag=12)
    nebula_cloud(mid, 180, 236, 220, 30, "#6a2064", "ndmc1", alphas=(0.06, 0.1, 0.14), rim="#f090d8")
    g = rng("ndmote")
    for i in range(60):
        put(mid, int(g.integers(0, W)), int(g.integers(20, 240)), "#9af8ec" if i % 2 else "#ffb0e8", 0.8)
    layers.append((mid, 0.18, 620))

    # ---------------- near: great coral fronds close by, nebula billowing up from below, drifting motes
    nh = 200
    near = Canvas(W, nh)
    yy, xx, _ = grids(nh)
    for i, (cx, cy, rx, ry, col) in enumerate(((140, 196, 220, 40, "#12505a"), (500, 200, 200, 44, "#5a1a58"))):
        nebula_cloud(near, cx, cy, rx, ry, col, ("ndnc", i), alphas=(0.08, 0.13, 0.18, 0.24),
                     rim="#7ae8e0" if i == 0 else "#f07ad0")
    rock_n = R("#050a10", "#08101a", "#0c1622", "#121e2c", "#1a2838", "#243446")
    for i, (cx, top, hw, dp) in enumerate(((50, 150, 50, 40), (590, 164, 36, 30))):
        m, tp = field_isle(near, cx, top, hw, dp, rock_n, ("ndni", i), "#7ae8e0", "#d060b0", haze="#0e1628", spurs=2)
        for k in range(2):
            px_ = int(cx - hw * 0.4 + k * hw * 0.7)
            c = (i + k) % 2
            star_coral(near, px_, int(tp[px_ % W]) + 1, 110 - k * 30 - i * 20, R("#10081a", "#241030", "#4a2050") if c == 0
                       else R("#061a20", "#0c2c34", "#1a4a50"), tips[c], ("ndnco", i, k), spread=1.2, glow=glows[c])
    g = rng("ndnmote")
    for i in range(30):
        x, y = int(g.integers(0, W)), int(g.integers(10, 190))
        put(near, x, y, "#c8fff4" if i % 2 else "#ffd0f0")
        if i % 5 == 0:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                put(near, x + dx, y + dy, "#6ae0d8" if i % 2 else "#e070c0", 0.6)
    layers.append((near, 0.32, 720))
    return dict(sky="#030d14", horizon="#4a2e56", layers=layers)


def lattice_ribs(cv, bay, foot, apex, width, pal, seed, off=0.0, pointed=1.35, hoops=(), lit_side=0.0, rivets=True,
                 overlap=True, inner=None):
    """The bronze lattice of the colossal lantern: pairs of ribs rising from feet `bay` px apart and curving over to
    meet at pointed apexes, the arches overlapping by half a bay so their ribs cross into a lattice; horizontal
    hoops at rows `hoops`; lit on the edge facing the heart, riveted. pal = bronze dark->gleam (5). Returns mask."""
    h = cv.h
    yy, xx, _ = grids(h)
    m = np.zeros((h, W), bool)
    n = int(round(W / bay)) * (2 if overlap else 1)
    for i in range(n):
        x0 = off + i * bay / (2.0 if overlap else 1.0)
        ax = x0 + bay / 2.0
        for side in (-1, 1):
            fx = x0 if side < 0 else x0 + bay
            pts = []
            for t in np.linspace(0, 1, 40):
                px_ = fx + (ax - fx) * (1 - math.cos(t * math.pi / 2)) ** pointed
                py_ = foot - (foot - apex) * math.sin(t * math.pi / 2)
                pts.append((px_, py_))
            m |= wline(h, pts, width)
    for (hy, hw_) in hoops:
        m |= (yy >= hy) & (yy < hy + hw_)
    m = despeck(m)
    flat(cv, m, pal[1])
    flat(cv, top_rim(m), pal[3])
    flat(cv, left_rim(m) & ~top_rim(m), pal[2])
    flat(cv, bot_rim(m) | right_rim(m), pal[0])
    if lit_side:
        flat(cv, top_rim(m) & (pn2(h, ("lrl", seed), 6, 3, 1) > 0.4), pal[4], lit_side)
    if inner is not None:   # the underside of each arch, facing the heart, catches its light
        flat(cv, bot_rim(m) & (yy < foot - 30), inner)
        flat(cv, sh(bot_rim(m), 0, -1) & m & (yy < foot - 60), pal[3])
    if rivets:
        riv = m & ~top_rim(m) & ~bot_rim(m) & ((xx + yy * 3) % 9 == 0) & (pn2(h, ("lrr", seed), 3, 3, 1) > 0.5)
        flat(cv, riv, pal[3])
    return m


def lantern_heart():
    """The Lantern Heart, inside the colossal lantern: molten gold-white light pouring from the star at its heart,
    bronze lattice ribs curving overhead in tier on tier, sparks drifting up to the open vent in the crown where
    the night shows through, and the Jade River running across it."""
    layers = []
    H = 360
    yy, xx, _ = grids(H)
    # ---------------- sky: the vent open to the night, its bronze rim, and the molten light below
    sky = Canvas(W, H)
    vent = 58
    night = sky_layer([(0.0, "#070818"), (0.12, "#0c0e28"), (0.17, "#15163a"), (1.0, "#15163a")], h=H, bands=10)
    sky.rgb[:] = night.rgb
    sky.a[:] = 1.0
    stars(sky, "lhtst", 220, 0, vent, LS_STARS, twinkle=7)
    star_river(sky, "lhtjr", 26, 8, 9, "#62dc92", JADE_STARS, alphas=(0.07, 0.11, 0.16), density=0.9, twinkles=6)
    heat = R("#3a1204", "#5a2006", "#823408", "#ac500e", "#d07018", "#ee9428", "#ffb846", "#ffcc64", "#ffdc86")
    dxh = wdx(xx, 320) / 330.0
    dyh = (yy - 196) / 190.0
    rr = np.sqrt(dxh ** 2 + dyh ** 2)
    v = (len(heat) - 1) * np.clip(1.05 - rr * 1.05, 0, 1) ** 1.25
    body = yy >= vent
    paint(sky, body, heat, v, sharp=2.4)
    rim = (yy >= vent - 3) & (yy <= vent + 9)
    flat(sky, rim, LS_CAGE[1])
    flat(sky, yy == vent - 3, LS_CAGE[3])
    flat(sky, yy == vent + 9, LS_CAGE[4])
    flat(sky, rim & (yy == vent + 1) & ((xx % 12) < 7), LS_CAGE[2])
    flat(sky, rim & (yy == vent + 5), LS_CAGE[0])
    flat(sky, rim & (yy >= vent + 6) & (yy <= vent + 8) & ((xx % 6) == 0), LS_CAGE[3])
    # the fallen star itself, blazing at the heart
    cx, cy = 320, 204
    for s_, a in ((80, 0.08), (56, 0.12), (40, 0.16)):
        flat(sky, wellipse(H, cx, cy, s_, s_) & body, "#ffeab0", a)
    dcx, dcy = wdx(xx, cx), yy - cy
    spark = (np.sqrt(np.abs(dcx)) + np.sqrt(np.abs(dcy))) <= math.sqrt(30)
    flat(sky, spark, "#fff4d0")
    flat(sky, wellipse(H, cx, cy, 11, 11), "#fffdf4")
    flat(sky, wellipse(H, cx, cy, 6, 6), "#ffffff")
    for ln, a in ((150, 0.25), (100, 0.4), (54, 0.7)):
        flat(sky, (((dcy == 0) & (np.abs(dcx) <= ln)) | ((dcx == 0) & (np.abs(dcy) <= ln * 0.9))) & body, "#ffffff", a)
    lantern_star(sky, cx, cy, 30, "lhtheart", halo=0.0, rays=1.8, star=R("#ffe6a0", "#fff4d0", "#fffcf0", "#ffffff"),
                 cage=R("#3a1c08", "#6a3810", "#9a5a1c", "#d08a30", "#ffd070"))
    g = rng("lhtsp")
    for i in range(140):
        x, y = int(g.integers(0, W)), int(g.integers(vent + 12, H))
        put(sky, x, y, "#fff4c8" if i % 3 else "#ffb040", 0.8)
    layers.append((sky, 0.0, 720))

    # ---------------- far: the far wall's lattice, fine ribs crossing, hoops, glowing in the light
    far = Canvas(W, H)
    far_pal = R("#5a2c0e", "#8a4a18", "#b86e28", "#e09a44", "#ffd07a")
    lattice_ribs(far, 80, H + 4, vent + 10, 2, far_pal, "lhtf", off=0, pointed=1.2,
                 hoops=((vent + 8, 3), (150, 2), (262, 2)), lit_side=0.7, rivets=False)
    haze_fade(far, far.a > 0, "#ffd88a", np.clip(1.0 - rr * 1.6, 0, 1) * 0.7, steps=4, sharp=3)
    layers.append((far, 0.06, 720))

    # ---------------- mid: heavier ribs curving overhead, chains of small lanterns, sparks rising
    mid = Canvas(W, H)
    mid_pal = R("#2a1206", "#4a2410", "#7a3e18", "#b0662a", "#f0b050")
    lattice_ribs(mid, 213.333, H + 10, 24, 4, mid_pal, "lhtm", off=40, pointed=1.5, hoops=((104, 3),), lit_side=0.8,
                 rivets=False, inner="#ffc060")
    for i, x in enumerate((60, 273, 486)):
        pts = dangle_pts(x, 100, 70 + (i % 2) * 30, sway=2.0)
        chain(mid, pts, R("#2a1206", "#7a3e18", "#f0b050"))
        lx, ly = pts[-1]
        lantern_star(mid, lx, ly + 7, 5, ("lhtml", i), hang=(lx, ly), halo=0.6, rays=0.5)
    g = rng("lhtms")
    for i in range(70):
        x, y = int(g.integers(0, W)), int(g.integers(20, 340))
        put(mid, x, y, "#fff0b0" if i % 2 else "#ffa040")
        if i % 7 == 0:
            put(mid, x - 1, y + 1, "#ff8a2a", 0.6)
            put(mid, x - 2, y + 2, "#ff8a2a", 0.3)
    layers.append((mid, 0.16, 720))

    # ---------------- near: massive ribs framing the view, the bronze grate floor over the glow beneath
    near = Canvas(W, H)
    near_pal = R("#120804", "#20100a", "#3a1c0c", "#6a3616", "#c0782a")
    lattice_ribs(near, 320, H + 30, -4, 9, near_pal, "lhtn", off=-150, pointed=1.9, lit_side=0.9, rivets=False,
                 overlap=False, inner="#ffb040")
    grate = (yy >= 330)
    flat(near, grate, near_pal[1])
    holes = grate & (yy >= 334) & ((xx % 12) >= 4) & ((xx % 12) <= 9) & (((yy - 334) % 9) >= 4) & (((yy - 334) % 9) <= 6)
    flat(near, holes, "#c05a18")
    flat(near, holes & ((yy - 334) % 9 == 4), "#ffa040")
    haze_fade(near, holes, "#20100a", np.clip((yy - 334) / 26.0, 0, 1) * 0.6, steps=3, sharp=4)
    flat(near, grate & (yy == 330), near_pal[4])
    flat(near, grate & (yy == 331), near_pal[3])
    g = rng("lhtns")
    for i in range(36):
        x, y = int(g.integers(0, W)), int(g.integers(40, 320))
        flat(near, wrect(H, x, y, x + 1, y), "#fff4c0" if i % 2 else "#ffb04a")
        put(near, x - 1, y + 1, "#ff8a2a", 0.5)
    layers.append((near, 0.3, 720))
    return dict(sky="#070818", horizon="#ffb846", layers=layers)


def interior():
    sky = sky_layer([(0.0, "#120c09"), (0.25, "#1d140e"), (0.5, "#2c1e14"), (0.62, "#35241a"), (0.8, "#261a12"),
                     (1.0, "#150e0a")], bands=14, sharp=2.0)
    return dict(sky="#120c09", horizon="#35241a", layers=[(sky, 0.0, 720)])


# =============================================================== registry
SCENES = {
    "valley_day": lambda: valley("day"),
    "valley_dusk": lambda: valley("dusk"),
    "valley_night": lambda: valley("night"),
    "marsh": marsh,
    "bamboo": bamboo_grove,
    "quarry": quarry,
    "mist_peak": mist_peak,
    "gorge": gorge,
    "cave": cave,
    "sect_jade": sect_jade,
    "sect_cloud": sect_cloud,
    "interior": interior,
    "storm_plains": storm_plains,
    "sky_port": sky_port,
    "rimefrost": rimefrost,
    "mirror_lake": mirror_lake,
    "gale_canyon": gale_canyon,
    "nine_peaks": nine_peaks,
    "sunscar": sunscar,
    "sunscar_tomb": sunscar_tomb,
    "skyport_wreck": skyport_wreck,
    "starsea": starsea,
    "lantern_harbor": lantern_harbor,
    "star_shoals": star_shoals,
    "blackmast_haven": blackmast_haven,
    "wyrmnest_isles": wyrmnest_isles,
    "warden_citadel": warden_citadel,
    "orbit_ruins": orbit_ruins,
    "ashen_reach": ashen_reach,
    "tidebreak_front": tidebreak_front,
    "nebula_deep": nebula_deep,
    "lantern_heart": lantern_heart,
}
ORDER = ["valley_day", "valley_dusk", "valley_night", "marsh", "bamboo", "quarry", "mist_peak", "gorge", "cave",
         "sect_jade", "sect_cloud", "interior", "storm_plains", "sky_port", "rimefrost", "mirror_lake", "gale_canyon", "nine_peaks",
         "sunscar", "sunscar_tomb", "skyport_wreck", "starsea", "lantern_harbor", "star_shoals", "blackmast_haven",
         "wyrmnest_isles", "warden_citadel", "orbit_ruins", "ashen_reach", "tidebreak_front", "nebula_deep",
         "lantern_heart"]


def hexs(c):
    c = C(c)
    return "#%02X%02X%02X" % tuple(int(round(v)) for v in c)


def export(cv):
    return cv.to_rgba(SCALE)


def compose(layers, cam_x=0.0, cam_y=0.0):
    """Render what the engine shows on a 1280x720 screen (for review)."""
    out = Image.new("RGBA", (1280, 720), (0, 0, 0, 255))
    for arr, par, bottom in layers:
        im = Image.fromarray(arr, "RGBA")
        lw, lh = im.size
        off = int(round(-cam_x * par)) % lw
        y = bottom - lh
        x = off - lw
        while x < 1280:
            out.alpha_composite(im, (x, y)) if y >= 0 else out.alpha_composite(im.crop((0, -y, lw, lh)), (x, 0))
            x += lw
    return out


def seam_error(arr):
    """Colour jump across the wrap seam vs. the largest ordinary neighbouring-column jumps."""
    a = arr.astype(int)
    d = np.abs(np.roll(a, -1, 1) - a).mean(axis=(0, 2))  # d[j] = |col j+1 - col j|, d[-1] = the seam
    return d[-1], np.percentile(d[:-1], 99.5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--review-dir", default=DEFAULT_REVIEW)
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()
    only = [s for s in args.only.split(",") if s]
    ids = [i for i in ORDER if i in SCENES and (not only or i in only)]
    out_dir = os.path.join(ROOT, "art", "backdrops")
    os.makedirs(args.review_dir, exist_ok=True)
    if not args.no_write:
        os.makedirs(out_dir, exist_ok=True)
    manifest = {"schema_version": 1}
    previews = []
    total = 0
    for bid in ids:
        scene = SCENES[bid]()
        entry = {"sky": hexs(scene["sky"]), "horizon": hexs(scene["horizon"]), "layers": []}
        rendered = []
        for n, (cv, par, bottom) in enumerate(scene["layers"]):
            assert cv.w == W, (bid, n, cv.w)
            arr = export(cv)
            if n == 0:
                assert arr[..., 3].min() == 255, (bid, "layer 0 must be opaque")
            s, t = seam_error(arr)
            assert s <= t * 1.5 + 0.5, (bid, n, "seam", s, t)
            fname = f"{bid}_{n}.png"
            path = os.path.join(out_dir, fname)
            if not args.no_write:
                save_png(Image.fromarray(arr, "RGBA"), path)
                total += os.path.getsize(path)
            entry["layers"].append({"file": f"res://art/backdrops/{fname}", "parallax": par, "bottom": bottom})
            rendered.append((arr, par, bottom))
        manifest[bid] = entry
        previews.append((bid, rendered))
        compose(rendered, 0).convert("RGB").save(os.path.join(args.review_dir, f"bd_{bid}.png"))
        compose(rendered, 2300).convert("RGB").save(os.path.join(args.review_dir, f"bd_{bid}_scrolled.png"))
    if not only and not args.no_write:
        with open(os.path.join(ROOT, "data", "backdrops.json"), "w") as fh:
            json.dump(manifest, fh, indent=2)
            fh.write("\n")
    # contact sheet: 3 columns of half-size previews
    cols = 3
    tw, th = 640, 360
    rows = (len(previews) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (tw + 12) + 12, rows * (th + 28) + 12), (24, 30, 34))
    d = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for i, (bid, rendered) in enumerate(previews):
        im = compose(rendered, 0).convert("RGB").resize((tw, th), Image.NEAREST)
        x = 12 + (i % cols) * (tw + 12)
        y = 12 + (i // cols) * (th + 28)
        d.text((x, y), f"{bid}  ({len(rendered)} layers)", fill=(230, 225, 207), font=font)
        sheet.paste(im, (x, y + 14))
    sheet.save(os.path.join(args.review_dir, "backdrops_contact.png"))
    print(f"built {len(previews)} backdrops, {total / 1e6:.2f} MB written")


if __name__ == "__main__":
    main()
