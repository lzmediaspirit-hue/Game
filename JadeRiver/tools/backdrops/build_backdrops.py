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
}
ORDER = ["valley_day", "valley_dusk", "valley_night", "marsh", "bamboo", "quarry", "mist_peak", "gorge", "cave",
         "sect_jade", "sect_cloud", "interior", "storm_plains", "sky_port", "rimefrost", "mirror_lake", "gale_canyon", "nine_peaks",
         "sunscar", "sunscar_tomb"]


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
