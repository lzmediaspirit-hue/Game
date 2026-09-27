#!/usr/bin/env python3
"""Paint the Jade River Valley world map: art/ui/maps/valley_map.png and one vignette per region.

    python3 tools/ui/build_valley_map.py                 # -> art/ui/maps/valley_map.png, valley_<region>.png, review sheets
    python3 tools/ui/build_valley_map.py --no-write      # review sheets only (scratchpad art_review/valley_map*.png)

The map is a painted pixel landscape of the whole valley seen from above at an angle: the Jade River winding from
Crane Falls in the north-east down through the towns and out through Whitewater Gorge in the west, the northern range
with Summit Ridge, Mist Peak, Crane Cliffs and Cleansing Peak, the Cloud Sect on its pinnacle, the Jade Sect Academy
on its hill above Stoneford, the Reed Marsh in the south-east, the quarry and the hideout in the south. Every region
of data/zones.json has its landmark drawn where its `map` position lies, so the map page can put its nodes straight on
top (the map rect is MAP_RECT, in art px; the page scales it x2).

Authored at art pixels (640 x 320) and saved x2 nearest, like every other piece of the game's art (tools/ui/README.md).
Gradients are ordered-dithered between flat ramp steps; mist and glows are stepped, never blurred. Deterministic:
every random choice is seeded from a stable string, so a rebuild is byte-identical.

Vignettes (art/ui/maps/valley_<region>.png, 256 x 144) are crops of the painting around each landmark, at the same
scale, for the map page's side card.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

sys.dont_write_bytecode = True  # keep the repo free of __pycache__

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "props"))

from pixlib import Canvas, hexc, m_ellipse, m_poly, m_rect, ramp, rng, save_png, shift, erode, dilate  # noqa: E402
from palette import (LEAF, LEAF_BLUE, STONE, STONE_WARM, STONE_DARK, ROOF, LACQUER, WOOD, GOLD,  # noqa: E402
                     THATCH, MUD, CLOTH_WHITE, SAND, PLASTER, PATINA, ROOF_GREY, INK)

DEFAULT_REVIEW = "/tmp/claude-0/-home-user-Game/13461237-7857-505a-bd3b-55d18a20fe2c/scratchpad/art_review"
OUT_DIR = os.path.join(ROOT, "art", "ui", "maps")
SCALE = 2
W, H = 640, 320                      # art px; 1280 x 640 on screen
MAP_RECT = (24, 34, 424, 276)        # x, y, w, h (art px): where a region's `map` [0..1] position lands
VIG_W, VIG_H = 128, 72               # vignette crop (art px); 256 x 144 on screen

# ---------------------------------------------------------------- local ramps (dark -> light)
SKY = ramp("#a6bcc2", "#bfcfcf", "#d6ded4", "#e8e9d8", "#f4efdb")
FAR = ramp("#5f7f8c", "#76959e", "#8dabae", "#a6bfbd", "#bfd1cb")           # far peaks in haze
ROCK = ramp("#1f2c30", "#33454a", "#4c6265", "#68807f", "#88a098", "#abbcb0", "#cbd5c6")
CLIFF = ramp("#2b3538", "#414f50", "#5b6c69", "#778a83", "#98a89d", "#b8c3b4", "#d3d9cb")
SNOW = ramp("#a9bfc6", "#cad9da", "#e6eeeb", "#f7f9f4")
GRASS = ramp("#2c4d2c", "#3b6a33", "#4f8a3c", "#69a54a", "#8cbd5c", "#b0d072")
FOREST = ramp("#0f2620", "#163a2c", "#1f5036", "#2c6a42", "#3f874d", "#5ea45c", "#86bd70")
BAMBOO = ramp("#24512a", "#37743a", "#4f9a48", "#6fb85a", "#98d070", "#c8e59a")
DEAD = ramp("#5c6a66", "#8a9590", "#b7bfb6")
MARSH = ramp("#3d4f43", "#546a55", "#6d8266", "#8a9a7d", "#a6ae93", "#c2c4a8")
MARSH_WATER = ramp("#2a4142", "#3d5a59", "#557572", "#75938f", "#98b1ab")
RIVER = ramp("#0b2f38", "#11474f", "#186266", "#237d78", "#369b8b", "#5dbba5", "#98dcc9", "#d2f2e8")
LAKE = ramp("#0f3237", "#164a4c", "#1e6361", "#2c7f77", "#48998c")
FOAM = ramp("#9fd6cf", "#cdeee6", "#f2fbf7")
QUARRY = ramp("#5a4630", "#7a603e", "#9a7c4e", "#b89760", "#d3b478", "#e8cf98")
ROAD = ramp("#7a6543", "#98805a", "#b49b6d", "#cdb684")
WALL = ramp("#8a8474", "#a8a28f", "#c6c0aa", "#e0dbc6")
GLOW = hexc("#ffd27a")
LANTERN = hexc("#ffb347")
WINDOW = hexc("#ffcf6e")
CLOUD = ramp("#b7c6c9", "#cfdadb", "#e4ebe9", "#f4f7f3", "#fdfdf8")
MIST = hexc("#e9eee3")
SAIL = ramp("#8f7d5b", "#b8a67d", "#d9c99c")
HULL = ramp("#2c1c12", "#4a3120", "#6b4a2d")

_B4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], float) / 16.0 + 1 / 32.0
_YY, _XX = np.mgrid[0:H, 0:W]
_BAYER = np.tile(_B4, (H // 4 + 1, W // 4 + 1))[:H, :W]
_NOISE = {}


# ---------------------------------------------------------------- helpers
def dq(v, n, sharp=1.0):
    """Ordered-dither a continuous ramp index field v (0..n-1) into integers."""
    fl = np.floor(v)
    fr = v - fl
    if sharp != 1.0:
        fr = np.clip((fr - 0.5) * sharp + 0.5, 0.0, 1.0)
    return np.clip((fl + (fr > _BAYER)).astype(int), 0, n - 1)


def paint(cv, m, pal, v, sharp=1.0):
    """Fill mask m from ramp pal (dark -> light) by the 0..1 field v, dithered."""
    if not m.any():
        return
    idx = dq(np.clip(v, 0, 1) * (len(pal) - 1), len(pal), sharp)
    cv.fill_idx(m, idx, pal)


def flat(cv, m, c, a=1.0):
    if m.any():
        cv.fill(m, c, a)


def noise(cell, seed, octaves=1):
    """2D value noise in [0,1] over the whole canvas (cached by its arguments)."""
    key = (cell, str(seed), octaves)
    if key in _NOISE:
        return _NOISE[key]
    g = rng("map-noise", seed)
    out = np.zeros((H, W))
    amp, norm, c = 1.0, 0.0, float(cell)
    for _ in range(octaves):
        gw = int(math.ceil(W / c)) + 2
        gh = int(math.ceil(H / c)) + 2
        gv = g.random((gh, gw))
        fx, fy = _XX / c, _YY / c
        x0, y0 = np.floor(fx).astype(int), np.floor(fy).astype(int)
        tx, ty = fx - x0, fy - y0
        tx = tx * tx * (3 - 2 * tx)
        ty = ty * ty * (3 - 2 * ty)
        v = (gv[y0, x0] * (1 - tx) * (1 - ty) + gv[y0, x0 + 1] * tx * (1 - ty)
             + gv[y0 + 1, x0] * (1 - tx) * ty + gv[y0 + 1, x0 + 1] * tx * ty)
        out += amp * v
        norm += amp
        amp *= 0.5
        c /= 2.0
    _NOISE[key] = out / norm
    return _NOISE[key]


def catmull(pts, per=1.5):
    """Catmull-Rom through pts -> dense list of (x, y)."""
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        seg = max(2, int(math.hypot(p2[0] - p1[0], p2[1] - p1[1]) * per))
        for s in range(seg):
            t = s / seg
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(tuple(pts[-1]))
    return out


def band(pts, widths):
    """A mask along a dense polyline with a per-point width (interpolated along the list)."""
    im = Image.new("1", (W, H), 0)
    d = ImageDraw.Draw(im)
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        t = i / max(1, n - 1)
        k = t * (len(widths) - 1)
        k0 = int(math.floor(k))
        k1 = min(len(widths) - 1, k0 + 1)
        w = widths[k0] + (widths[k1] - widths[k0]) * (k - k0)
        r = w / 2.0
        d.ellipse([x - r, y - r, x + r, y + r], fill=1)
    return np.array(im, bool)


def gauss(cx, cy, sx, sy, amp=1.0, p=2.0):
    return amp * np.exp(-((np.abs(_XX - cx) / sx) ** p + (np.abs(_YY - cy) / sy) ** p))


def m_circle(cx, cy, r):
    return m_ellipse(W, H, cx, cy, r, r)


def light_field(hmap, kx=1.0, ky=0.6):
    """Shade from the upper left for a height map: >0 lit, <0 shadow."""
    gx = np.zeros_like(hmap)
    gy = np.zeros_like(hmap)
    gx[:, 1:-1] = (hmap[:, 2:] - hmap[:, :-2]) * 0.5
    gy[1:-1, :] = (hmap[2:, :] - hmap[:-2, :]) * 0.5
    return -gx * kx - gy * ky


def patchy(cv, m, col, a, cell, seed, cover=0.5):
    """Translucent col over m, but only where a noise field is above 1 - cover, in three alpha steps: wisps of mist
    instead of a flat sheet. The wisps thin out toward the mask's top and bottom, so no edge of the mask shows."""
    if not m.any():
        return
    ys = np.nonzero(m.any(1))[0]
    y0, y1 = ys.min(), ys.max()
    env = np.sin(np.pi * np.clip((_YY - y0) / max(1, y1 - y0), 0, 1)) ** 0.6
    n2 = noise(cell, ("patchy", seed), 2) * env
    for k, s in ((0.0, 0.45), (0.12, 0.35), (0.24, 0.2)):
        cv.light(m & (n2 > 1 - cover + k), col, a * s)


# ---------------------------------------------------------------- the regions
def load_regions():
    z = json.load(open(os.path.join(ROOT, "data", "zones.json")))
    zone = [e for e in z.get("entries", z) if e["id"] == "jade_river_valley"][0]
    out = {}
    for r in zone["regions"]:
        if r.get("hidden"):
            continue
        mx, my = r["map"]
        out[r["id"]] = (MAP_RECT[0] + mx * MAP_RECT[2], MAP_RECT[1] + my * MAP_RECT[3], r["name"])
    return out


# ---------------------------------------------------------------- trees (stamped, so a forest of thousands is cheap)
_STAMPS = {}


def _tree_stamp(r):
    """Ramp indices for one crown of radius r (-1 outside): lit upper left, dark lower right, a lit top pixel."""
    key = round(r * 2) / 2
    if key in _STAMPS:
        return _STAMPS[key]
    n = int(math.ceil(key)) * 2 + 1
    c = n // 2
    yy, xx = np.mgrid[0:n, 0:n]
    inside = (xx - c) ** 2 + (yy - c) ** 2 <= key * key + 0.3
    d = ((xx - c) * 0.8 + (yy - c) * 1.0) / max(key, 1.0)
    v = np.clip(0.62 - d * 0.34, 0, 1)
    idx = np.where(inside, np.clip(np.floor(v * 6.0 + (np.indices((n, n)).sum(0) % 2) * 0.35), 0, 5), -1).astype(int)
    if key >= 2:
        idx[c - 1, c - 1] = 6
    _STAMPS[key] = idx
    return idx


def tree(cv, x, y, r, pal, shadow=True):
    idx = _tree_stamp(r)
    n = idx.shape[0]
    c = n // 2
    x0, y0 = int(round(x)) - c, int(round(y)) - c
    palA = np.array(pal, float)
    for j in range(n):
        py = y0 + j
        if py < 0 or py >= H:
            continue
        row = idx[j]
        for i in range(n):
            k = row[i]
            if k < 0:
                continue
            px = x0 + i
            if 0 <= px < W:
                cv.rgb[py, px] = palA[min(k, len(pal) - 1)]
                cv.a[py, px] = 1.0
    if shadow:
        py = y0 + n
        if 0 <= py < H:
            for i in range(n):
                px = x0 + i
                if 0 <= px < W and idx[n - 1, i] >= 0:
                    cv.rgb[py, px] = cv.rgb[py, px] * 0.55 + palA[0] * 0.45


def forest(cv, m, pal, seed, density=0.5, rmin=1.5, rmax=3.0):
    """Fill a region mask with crowns, far to near (top to bottom)."""
    g = rng("forest", seed)
    ys, xs = np.nonzero(m)
    if len(xs) == 0:
        return
    n = int(len(xs) * density / 6.0)
    pick = g.integers(0, len(xs), n)
    rs = g.uniform(rmin, rmax, n)
    order = np.argsort(ys[pick] * 4 + (xs[pick] % 4), kind="stable")
    for o in order:
        i = pick[o]
        tree(cv, xs[i], ys[i], rs[o], pal)


def bamboo_field(cv, m, seed, density=0.7):
    """Bamboo seen from above at an angle: dense pale-green culms with lit tops."""
    g = rng("bamboo", seed)
    ys, xs = np.nonzero(m)
    if len(xs) == 0:
        return
    base = noise(6, "bamboo-base")
    paint(cv, m, BAMBOO, 0.12 + base * 0.3)
    n = int(len(xs) * density / 5.0)
    pick = g.integers(0, len(xs), n)
    for i in sorted(pick, key=lambda i: ys[i]):
        x, y = int(xs[i]), int(ys[i])
        h = int(g.integers(4, 8))
        for k in range(h):
            if 0 <= y - k < H and m[y - k, x]:
                cv.put(x, y - k, BAMBOO[2 + (k * 3) // h] if k < h - 1 else BAMBOO[5])
        if 0 <= y + 1 < H and m[y + 1, x]:
            cv.put(x, y + 1, BAMBOO[0], 0.8)
        cv.put(x + 1, y - h + 2, BAMBOO[4], 0.8)
        cv.put(x - 1, y - h + 3, BAMBOO[3], 0.8)


def reeds(cv, m, seed):
    g = rng("reeds", seed)
    ys, xs = np.nonzero(m)
    if len(xs) == 0:
        return
    n = len(xs) // 5
    pick = g.integers(0, len(xs), n)
    for i in pick:
        x, y = int(xs[i]), int(ys[i])
        h = int(g.integers(2, 5))
        c = MARSH[3 + int(g.integers(0, 3))]
        for k in range(h):
            cv.put(x, y - k, c, 0.9)
        cv.put(x, y - h, hexc("#b9a97a"), 0.9)


# ---------------------------------------------------------------- landforms
def karst(cv, cx, top, base, hw, seed, rock=ROCK, snow=None, crown=0.55, tilt=0.0, skirt=0.5):
    """A karst tower seen from above at an angle: a rounded cap, a lit left face, a shadowed right face; forest on
    the cap's shoulders and round the foot. The base spreads wider than the cap."""
    h = max(4, base - top)
    ys = np.arange(top, base + 1)
    t = np.clip((ys - top) / h, 0, 1)
    g = rng("karst", seed)
    bumps = g.uniform(-0.12, 0.12, 4)
    prof = hw * (0.42 + 0.58 * t ** 0.75)
    prof *= 1 + bumps[0] * np.sin(ys * 0.5) + bumps[1] * np.sin(ys * 0.23 + 1)
    cap = max(2, int(hw * 0.45))
    k = np.arange(min(cap, len(prof)))
    prof[:len(k)] = np.sqrt(np.clip(1 - ((cap - k) / cap) ** 2, 0, 1)) * hw * 0.44 + 0.5
    left = [(cx - prof[i] + tilt * t[i] * hw, ys[i]) for i in range(len(ys))]
    right = [(cx + prof[i] + tilt * t[i] * hw, ys[i]) for i in range(len(ys))][::-1]
    m = m_poly(W, H, left + right)
    if not m.any():
        return m
    depth = np.clip((_YY - top) / h, 0, 1)
    ctr = cx + tilt * depth * hw
    xr = (_XX - ctr) / np.maximum(1.0, hw * (0.42 + 0.58 * depth ** 0.75))
    n2 = noise(4, ("karst-n", seed), 2)
    strata = ((_YY + (n2 * 5).astype(int)) % 5 == 0)
    v = 0.66 - np.clip(xr, -1, 1) * 0.42 - depth * 0.3 + (n2 - 0.5) * 0.3
    paint(cv, m, rock, v)
    flat(cv, m & strata & (xr > 0.1), rock[1], 0.5)
    flat(cv, m & strata & (xr <= 0.1), rock[3], 0.35)
    if snow is not None:
        sm = m & (depth < 0.2) & (n2 > 0.3)
        paint(cv, sm, snow, 0.5 - np.clip(xr, -1, 1) * 0.4 + (n2 - 0.5) * 0.4)
    # an ink line round the silhouette (heavier on the shadow side), the lit left rim pale
    edge = m & ~shift(m, -1, 0)
    flat(cv, edge, rock[0], 0.85)
    flat(cv, dilate(m) & ~m, INK, 0.5)
    rim = m & ~shift(m, 1, 0) & ~shift(m, 0, 1)
    flat(cv, rim, rock[-1], 0.5)
    bottom = m & ~shift(m, 0, -1)
    flat(cv, bottom, rock[0], 0.7)
    if crown:
        shoulders = m & (depth > 0.16) & (depth < 0.45) & (n2 > 0.55) & (xr < 0.4)
        forest(cv, shoulders, FOREST, ("karst-crown", seed), density=crown, rmin=1.0, rmax=1.8)
        foot = m & (depth > 1 - skirt) & (n2 > 0.35)
        forest(cv, foot, FOREST, ("karst-foot", seed), density=crown * 1.1, rmin=1.2, rmax=2.2)
    return m


def cliff_face(cv, m, seed, pal=CLIFF, lit=0.0):
    """Vertical rock strata inside a mask."""
    n2 = noise(3, ("cliff", seed), 2)
    stripes = ((_YY + (n2 * 6).astype(int)) % 4 == 0)
    v = 0.55 + (n2 - 0.5) * 0.5 + lit
    paint(cv, m, pal, v)
    flat(cv, m & stripes, pal[1], 0.55)
    flat(cv, m & ~shift(m, 0, 1), pal[-1], 0.45)
    flat(cv, m & ~shift(m, 0, -1), pal[0], 0.7)


def river_cliffs(cv, water, side_m, seed):
    """Low cliffs where the river cuts a bank: strata on the far bank inside side_m."""
    m = dilate(dilate(dilate(water))) & ~water & side_m
    cliff_face(cv, m, seed, pal=CLIFF)


# ---------------------------------------------------------------- structures
def roof_tiles(cv, m, pal, lit_side="left"):
    """A tiled roof surface in a mask: rows of tiles, the ridge lit, the eave dark."""
    if not m.any():
        return
    ys, xs = np.nonzero(m)
    y0, y1 = ys.min(), ys.max()
    x0, x1 = xs.min(), xs.max()
    t = np.clip((_YY - y0) / max(1, y1 - y0), 0, 1)
    xr = np.clip((_XX - x0) / max(1, x1 - x0), 0, 1)
    v = 0.82 - t * 0.5 + (0.18 if lit_side == "left" else -0.18) * (0.5 - xr)
    v += np.where(_YY % 2 == 0, 0.07, -0.07)
    paint(cv, m, pal, v, sharp=1.5)
    e = m & ~shift(m, 0, -1)
    flat(cv, e, pal[0])
    top = m & ~shift(m, 0, 1)
    flat(cv, top, pal[-1], 0.7)


def hall(cv, cx, by, w, wall_h, roof_h, roof=ROOF, wall=WALL, windows=2, eaves=2, ridge=True):
    """A hall seen from in front and slightly above: walls with warm windows, a tiled roof with upturned eaves."""
    x0, x1 = int(cx - w / 2), int(cx + w / 2)
    wy0 = by - wall_h
    wm = m_rect(W, H, x0, wy0, x1, by)
    paint(cv, wm, wall, 0.55 + (0.5 - (_XX - x0) / max(1, w)) * 0.3)
    flat(cv, m_rect(W, H, x0, by, x1, by), STONE[2])
    flat(cv, m_rect(W, H, x0, by + 1, x1 + 1, by + 1), INK, 0.35)
    if windows > 0 and wall_h >= 3:
        step = (w - 2) / (windows + 1)
        for i in range(windows):
            wx = int(x0 + 1 + step * (i + 1))
            cv.put(wx, wy0 + max(1, wall_h // 2), WINDOW)
            if wall_h >= 5:
                cv.put(wx, wy0 + max(1, wall_h // 2) + 1, WINDOW)
    ry0 = wy0 - roof_h
    rm = m_poly(W, H, [(x0 - eaves, wy0), (x0 + w * 0.22, ry0), (x1 - w * 0.22, ry0), (x1 + eaves, wy0)])
    roof_tiles(cv, rm, roof)
    if ridge:
        flat(cv, m_rect(W, H, int(x0 + w * 0.22), ry0, int(x1 - w * 0.22), ry0), roof[-1])
    cv.put(x0 - eaves, wy0 - 1, roof[-2])
    cv.put(x1 + eaves, wy0 - 1, roof[-2])
    return m_rect(W, H, x0 - eaves, ry0 - 1, x1 + eaves, by)


def pagoda(cv, cx, by, tiers, w0, roof=ROOF, wall=LACQUER, tier_h=4, shrink=0.78):
    """A tiered pagoda: each tier a wall band under a roof wider than it, narrowing upward, a gold spire on top."""
    w = float(w0)
    y = by
    for i in range(tiers):
        x0, x1 = int(round(cx - w / 2)), int(round(cx + w / 2))
        wall_h = max(2, tier_h - 1)
        wm = m_rect(W, H, x0, y - wall_h, x1, y)
        paint(cv, wm, wall, 0.5 + (0.5 - (_XX - x0) / max(1, w)) * 0.4)
        if w >= 5:
            cv.put(int(cx), y - wall_h + 1, WINDOW)
            if w >= 9:
                cv.put(int(cx) - 2, y - wall_h + 1, WINDOW)
                cv.put(int(cx) + 2, y - wall_h + 1, WINDOW)
        ry = y - wall_h
        rm = m_poly(W, H, [(x0 - 2, ry), (x0 + w * 0.25, ry - 2), (x1 - w * 0.25, ry - 2), (x1 + 2, ry)])
        roof_tiles(cv, rm, roof)
        cv.put(x0 - 2, ry - 1, roof[-2])
        cv.put(x1 + 2, ry - 1, roof[-2])
        y = ry - 2
        w *= shrink
    for k in range(3):
        cv.put(int(cx), y - k, GOLD[4 + (k == 2)])
    return m_rect(W, H, int(cx - w0 / 2) - 2, y - 3, int(cx + w0 / 2) + 2, by)


def wall_line(cv, pts, c_top, c_face, h=2):
    """A wall along a polyline: a lit top and a shaded face below it."""
    pts = [(int(round(x)), int(round(y))) for x, y in pts]
    im = Image.new("1", (W, H), 0)
    ImageDraw.Draw(im).line(pts, fill=1, width=1)
    top = np.array(im, bool)
    face = np.zeros_like(top)
    for k in range(1, h + 1):
        face |= shift(top, 0, k)
    flat(cv, face & ~top, c_face)
    flat(cv, top, c_top)


def stilt_hut(cv, cx, by, w=6, lit=True):
    """A hut on stilts over the marsh: posts, a dark floor, a thatch roof."""
    x0, x1 = int(cx - w // 2), int(cx + w // 2)
    for px in (x0 + 1, x1 - 1):
        cv.put(px, by, WOOD[1])
        cv.put(px, by + 1, WOOD[0])
    paint(cv, m_rect(W, H, x0, by - 3, x1, by - 1), WOOD, 0.35 + (0.5 - (_XX - x0) / max(1, w)) * 0.3)
    if lit:
        cv.put(int(cx), by - 2, WINDOW)
    rm = m_poly(W, H, [(x0 - 1, by - 3), (int(cx), by - 7), (x1 + 1, by - 3)])
    paint(cv, rm, THATCH, 0.7 - (_YY - (by - 7)) / 5.0 * 0.4 + (0.5 - (_XX - x0) / max(1, w)) * 0.3)


def bridge(cv, x0, x1, y, rise=3, pal=STONE_WARM):
    """A stone arch bridge across the river from x0 to x1 at river level y."""
    n = x1 - x0
    for i in range(n + 1):
        t = i / max(1, n)
        a = math.sin(t * math.pi) * rise
        px = x0 + i
        py = int(round(y - a))
        cv.put(px, py, pal[5])
        cv.put(px, py + 1, pal[3])
        cv.put(px, py + 2, pal[1] if 0.15 < t < 0.85 else pal[2])
    for px in (x0, x1):
        cv.put(px, y + 1, pal[1])
        cv.put(px, y + 2, pal[0])


def boat(cv, x, y, sail=True, flip=False):
    hull = [(x - 3, y), (x + 3, y), (x + 2, y + 1), (x - 2, y + 1)]
    flat(cv, m_poly(W, H, hull), HULL[1])
    cv.put(x - 3, y, HULL[2])
    cv.put(x + 3, y, HULL[2])
    if sail:
        sx = x + (1 if flip else 0)
        for k in range(1, 5):
            cv.put(sx, y - k, WOOD[1])
        sm = m_poly(W, H, [(sx + (1 if not flip else -1), y - 1), (sx + (1 if not flip else -1), y - 4), (sx + (3 if not flip else -3), y - 2)])
        paint(cv, sm, SAIL, 0.6 + (_YY - (y - 4)) / 4.0 * 0.4)
    cv.put(x - 4, y + 1, RIVER[6], 0.8)
    cv.put(x + 4, y + 1, RIVER[6], 0.8)


def lantern(cv, x, y, big=False):
    """A lit lantern: a warm core and a stepped glow."""
    cv.light(m_circle(x + 0.5, y + 0.5, 3.4 if big else 2.5), GLOW, 0.16)
    cv.light(m_circle(x + 0.5, y + 0.5, 1.9 if big else 1.4), GLOW, 0.3)
    cv.put(x, y, LANTERN)
    if big:
        cv.put(x, y - 1, WINDOW)


def waterfall(cv, x, y0, y1, w=3, seed=0):
    """A white fall from y0 to y1, mist at its foot."""
    m = m_rect(W, H, x - w // 2, y0, x + w // 2, y1)
    n2 = noise(2, ("falls", seed, x))
    v = 0.55 + (n2 - 0.5) * 0.9 + ((_YY - y0) / max(1, y1 - y0)) * 0.3
    paint(cv, m, FOAM, v)
    flat(cv, m & (_YY % 3 == (seed % 3)) & (n2 < 0.45), RIVER[5], 0.7)
    for k, a in ((5, 0.22), (3.5, 0.3), (2, 0.4)):
        cv.light(m_ellipse(W, H, x + 0.5, y1 + 1.5, k * 1.6, k * 0.8), MIST, a)


def cloud_puff(cv, cx, cy, rx, ry, seed, pal=CLOUD):
    g = rng("cloud", seed)
    m = np.zeros((H, W), bool)
    for _ in range(int(3 + rx // 4)):
        ox, oy = g.uniform(-rx * 0.7, rx * 0.7), g.uniform(-ry * 0.5, ry * 0.3)
        m |= m_ellipse(W, H, cx + ox, cy + oy, g.uniform(rx * 0.35, rx * 0.6), g.uniform(ry * 0.5, ry * 0.9))
    m |= m_ellipse(W, H, cx, cy + ry * 0.3, rx, ry * 0.55)
    d = ((_XX - cx) / rx) * 0.5 + ((_YY - cy) / ry) * 0.9
    paint(cv, m, pal, 0.75 - d * 0.5)
    e = m & ~shift(m, 0, -1)
    flat(cv, e, pal[0], 0.7)
    return m


def dock(cv, x0, y, length, pal=WOOD):
    for i in range(length):
        cv.put(x0 + i, y, pal[3] if i % 3 else pal[2])
    for px in (x0 + 1, x0 + length - 2):
        cv.put(px, y + 1, pal[0])


def road(cv, pts, w=2, pal=ROAD):
    m = band(catmull(pts), [w, w])
    n2 = noise(3, "road")
    paint(cv, m, pal, 0.45 + (n2 - 0.5) * 0.5)
    return m


def stones(cv, m, seed, pal=STONE, density=0.5):
    g = rng("stones", seed)
    ys, xs = np.nonzero(m)
    if len(xs) == 0:
        return
    n = int(len(xs) * density / 8.0)
    for i in g.integers(0, len(xs), n):
        x, y = int(xs[i]), int(ys[i])
        cv.put(x, y, pal[4])
        cv.put(x + 1, y, pal[2])
        cv.put(x, y + 1, pal[1], 0.8)


def crane(cv, x, y):
    cv.put(x, y, CLOTH_WHITE[5])
    cv.put(x - 1, y + 1, CLOTH_WHITE[4])
    cv.put(x + 1, y + 1, CLOTH_WHITE[4])
    cv.put(x - 2, y + 1, CLOTH_WHITE[3], 0.7)
    cv.put(x + 2, y + 1, CLOTH_WHITE[3], 0.7)


# ---------------------------------------------------------------- the painting
def paint_map(regions):
    cv = Canvas(W, H)
    R = {k: (v[0], v[1]) for k, v in regions.items()}
    all_m = np.ones((H, W), bool)

    # ---- sky and the far ranges (the top of the picture is the far north)
    sky_v = np.clip(_YY / 64.0, 0, 1)
    paint(cv, all_m, SKY, 1 - sky_v * 0.85)
    far_prof = noise(26, "far-peaks", 2)[0]
    for k in range(3):
        base_y = 46 + k * 11
        pts = [(x, base_y - 12 - far_prof[(x * (k + 2) + k * 90) % W] * (30 - k * 7) - 7 * math.sin(x * 0.041 + k * 1.3)) for x in range(W)]
        m = m_poly(W, H, [(0, base_y + 40)] + pts + [(W - 1, base_y + 40)])
        v = 0.3 + k * 0.28
        paint(cv, m, FAR, v + (noise(9, ("far", k)) - 0.5) * 0.25)
        flat(cv, m & ~shift(m, 0, 1), FAR[-1], 0.5)
        flat(cv, m & ~shift(m, -1, 0), FAR[0], 0.35)
    patchy(cv, m_rect(W, H, 0, 40, W - 1, 78), MIST, 0.6, 22, "far-mist", cover=0.55)

    # ---- the valley floor: a height field for the ground light, forest with grass clearings
    hmap = np.zeros((H, W))
    hmap += gauss(R["jade_sect"][0], R["jade_sect"][1] + 6, 46, 24, 14.0)         # the Academy's hill
    hmap += gauss(R["stonewall_quarry"][0], R["stonewall_quarry"][1], 40, 18, 5.0)
    hmap += gauss(R["mudwater_hideout"][0] - 10, R["mudwater_hideout"][1] - 2, 36, 16, 6.0)
    hmap += gauss(R["bamboo_grove"][0] + 20, R["bamboo_grove"][1], 40, 30, 4.0)
    hmap += gauss(540, 200, 90, 60, 8.0)
    hmap += gauss(560, 300, 110, 40, 8.0)
    hmap += gauss(60, 250, 40, 40, 7.0)
    hmap -= gauss(R["reed_marsh"][0] + 10, R["reed_marsh"][1] + 8, 60, 34, 6.0)   # the marsh is low
    hmap += noise(30, "ground-h", 3) * 6.0
    L = np.clip(light_field(hmap), -1.6, 1.6)
    base_n = noise(12, "ground", 3)
    edge_n = noise(24, "floor-edge", 2)[0]
    floor = _YY > (58 + edge_n * 14)[None, :]
    paint(cv, floor, FOREST, 0.28 + base_n * 0.36 + L * 0.14)
    # grass clearings: round the towns and the river's middle reach, and where the noise opens
    clear = noise(22, "clearings", 2)
    open_f = clear + gauss(R["stoneford"][0] + 20, R["stoneford"][1] + 4, 120, 40, 0.35) - np.clip((_YY - 210) / 120.0, 0, 0.6)
    open_m = floor & (open_f > 0.62)
    paint(cv, open_m, GRASS, 0.42 + base_n * 0.35 + L * 0.16)
    # a soft edge: the rim of each clearing is the darker grass, and a dithered fringe of it lies outside
    flat(cv, open_m & ~erode(open_m), GRASS[1], 0.7)
    fringe = floor & ~open_m & (open_f > 0.56) & (_BAYER < (open_f - 0.56) / 0.06)
    flat(cv, fringe, GRASS[1], 0.8)
    fmask = floor & ~open_m
    # atmospheric haze: the far floor pales toward the range
    for y1, a in ((150, 0.08), (130, 0.1), (112, 0.12), (96, 0.16), (84, 0.2)):
        cv.light(floor & (_YY < y1), MIST, a)
    # bushes and lone trees on the meadows, so they are not flat
    forest(cv, open_m & (_YY > 100), GRASS, "meadow-bushes", density=0.05, rmin=1.0, rmax=1.6)
    forest(cv, open_m & (_YY > 100) & (clear > 0.7), FOREST, "meadow-trees", density=0.05, rmin=1.5, rmax=2.4)

    # ---- the northern range: the towers back to front (higher y = nearer)
    sx, sy = R["summit_ridge"]
    karst(cv, sx - 30, sy - 6, sy + 48, 22, 11, snow=SNOW)
    karst(cv, sx + 6, sy - 18, sy + 54, 26, 12, snow=SNOW)
    karst(cv, sx + 34, sy - 2, sy + 46, 16, 13, snow=SNOW)
    mx, my = R["mist_peak"]
    karst(cv, mx - 20, my + 6, my + 46, 15, 21)
    karst(cv, mx + 2, my - 12, my + 50, 19, 22, snow=SNOW)
    cx_, cy_ = R["crane_cliffs"]
    karst(cv, cx_ - 24, cy_ - 2, cy_ + 42, 22, 31, rock=CLIFF, crown=0.3)
    karst(cv, cx_ + 8, cy_ - 16, cy_ + 44, 26, 32, rock=CLIFF, crown=0.45)
    karst(cv, cx_ + 34, cy_ + 6, cy_ + 40, 14, 33)
    karst(cv, 40, 100, 152, 24, 41, rock=CLIFF)
    karst(cv, 8, 112, 160, 18, 42, rock=CLIFF)
    px_, py_ = R["cleansing_peak"]
    karst(cv, px_ - 22, py_ + 10, py_ + 52, 17, 51)
    karst(cv, px_ + 2, py_ - 18, py_ + 54, 19, 52, snow=SNOW)
    karst(cv, 502, 42, 124, 32, 61, snow=SNOW)
    karst(cv, 550, 60, 134, 26, 62)
    karst(cv, 598, 36, 128, 34, 63, snow=SNOW)
    karst(cv, 634, 66, 134, 22, 64)
    hv_x, hv_y = R["hidden_vale"]
    karst(cv, hv_x - 28, hv_y - 2, hv_y + 40, 20, 71)
    karst(cv, hv_x + 30, hv_y - 12, hv_y + 42, 22, 72)
    cs_x, cs_y = R["cloud_sect"]
    karst(cv, cs_x - 16, cs_y + 8, cs_y + 46, 13, 81)
    karst(cv, cs_x + 2, cs_y - 24, cs_y + 48, 15, 82)
    karst(cv, cs_x + 24, cs_y + 4, cs_y + 44, 12, 83)
    # mid-ground towers that give the valley its verticals
    karst(cv, 300, 118, 150, 12, 101)
    karst(cv, 470, 136, 176, 16, 102)
    karst(cv, 520, 160, 206, 20, 103)
    karst(cv, 600, 176, 230, 26, 104)
    karst(cv, 560, 236, 284, 30, 105)
    karst(cv, 630, 250, 300, 24, 106)
    karst(cv, 30, 222, 262, 16, 107)
    karst(cv, 70, 262, 300, 22, 108)
    karst(cv, 260, 276, 316, 22, 109)
    karst(cv, 400, 262, 306, 20, 110)
    karst(cv, 150, 284, 318, 18, 111)

    # ---- the river: from the falls in the north-east, west through the valley, out through the gorge
    cf = R["crane_falls"]
    rv = [(cf[0] + 2, cf[1] + 12), (cf[0] + 14, cf[1] + 30), (cf[0] + 6, cf[1] + 50), (R["lotus_ferry"][0] + 8, R["lotus_ferry"][1] - 6),
          (R["willow_path"][0] + 4, R["willow_path"][1] + 5), (R["stoneford"][0] + 10, R["stoneford"][1] + 3),
          (R["caravan_road"][0] + 4, R["caravan_road"][1] - 4), (R["deepwater_bend"][0] + 8, R["deepwater_bend"][1] + 6),
          (R["deepwater_bend"][0] - 14, R["deepwater_bend"][1] - 6), (R["whitewater_gorge"][0] + 6, R["whitewater_gorge"][1] + 12),
          (R["whitewater_gorge"][0] - 8, R["whitewater_gorge"][1] - 10), (34, 100), (10, 84)]
    rpts = catmull(rv, 2.0)
    widths = [5, 7, 9, 12, 13, 13, 13, 15, 13, 8, 6, 5, 5]
    river_m = band(rpts, widths)
    ds = R["drowned_shrine"]
    lake_m = m_ellipse(W, H, ds[0] + 2, ds[1] + 3, 25, 13) | band(catmull([(R["deepwater_bend"][0] + 2, R["deepwater_bend"][1] + 8), (ds[0] + 10, ds[1] - 6)]), [8, 10])
    water = river_m | lake_m
    # cliffs on the far banks of the middle reach and the bend; sand on the near banks
    river_cliffs(cv, river_m, m_rect(W, H, int(R["caravan_road"][0] - 30), 0, int(R["stoneford"][0] - 6), int(R["stoneford"][1] - 1)), "n-bank")
    river_cliffs(cv, river_m, m_rect(W, H, int(R["deepwater_bend"][0] - 30), int(R["deepwater_bend"][1] - 40), int(R["deepwater_bend"][0] - 4), int(R["deepwater_bend"][1] - 4)), "bend-cliff")
    bank = dilate(water) & ~water
    flat(cv, bank & (_YY > 0), SAND[3], 0.7)
    flat(cv, shift(water, 0, -1) & ~water, FOREST[0], 0.55)
    wn = noise(4, "water", 2)
    flow = ((_XX * 0.9 + _YY * 0.35 + (wn * 8)) % 7 < 1.6)
    wv = 0.56 + (wn - 0.5) * 0.35 - np.clip((_YY - 100) / 300.0, 0, 1) * 0.08
    paint(cv, water, RIVER, wv)
    flat(cv, water & flow, RIVER[6], 0.45)
    core = erode(erode(erode(water)))
    paint(cv, core, RIVER, wv - 0.16)
    flat(cv, core & flow, RIVER[5], 0.45)
    glint = water & shift(bank, 0, 1) & ((_XX + _YY) % 3 == 0)
    flat(cv, glint, RIVER[7], 0.85)
    paint(cv, lake_m, LAKE, 0.5 + (wn - 0.5) * 0.25)
    flat(cv, lake_m & flow, LAKE[4], 0.35)
    wg = R["whitewater_gorge"]
    gorge_m = water & (_XX < wg[0] + 22) & (_YY < wg[1] + 26)
    flat(cv, gorge_m & (wn > 0.5), FOAM[1], 0.8)
    flat(cv, gorge_m & (wn > 0.68), FOAM[2], 0.9)

    # ---- the falls at Crane Falls: the river's source pours off the cliffs
    karst(cv, cf[0] - 10, cf[1] - 26, cf[1] + 6, 14, 121, rock=CLIFF, crown=0.4, skirt=0.2)
    karst(cv, cf[0] + 18, cf[1] - 22, cf[1] + 8, 12, 122, rock=CLIFF, crown=0.4, skirt=0.2)
    waterfall(cv, int(cf[0] + 1), int(cf[1] - 10), int(cf[1] + 10), w=4, seed=1)
    waterfall(cv, int(cf[0] + 9), int(cf[1] - 5), int(cf[1] + 10), w=2, seed=2)
    pool = m_ellipse(W, H, cf[0] + 3, cf[1] + 13, 9, 4)
    paint(cv, pool, RIVER, 0.6 + (wn - 0.5) * 0.3)
    flat(cv, pool & (wn > 0.55), FOAM[0], 0.6)

    # ---- Bamboo Grove: a pale bamboo sea east of the river
    bg = R["bamboo_grove"]
    bam_m = (m_ellipse(W, H, bg[0] + 6, bg[1] + 4, 34, 22) | m_ellipse(W, H, bg[0] + 34, bg[1] - 6, 26, 18)) & ~dilate(water) & floor
    bamboo_field(cv, bam_m, "grove")

    # ---- Reed Marsh and Greyreed Hamlet: grey pools, reed beds, stilt houses
    rm = R["reed_marsh"]
    marsh_m = (m_ellipse(W, H, rm[0] + 6, rm[1] + 10, 58, 30) | m_ellipse(W, H, rm[0] + 40, rm[1] + 24, 40, 20)) & floor & ~water
    mn = noise(7, "marsh", 2)
    paint(cv, marsh_m, MARSH, 0.3 + mn * 0.5)
    pools = marsh_m & (mn < 0.42)
    paint(cv, pools, MARSH_WATER, 0.4 + (wn - 0.5) * 0.3)
    flat(cv, pools & flow, MARSH_WATER[4], 0.5)
    flat(cv, pools & ~shift(pools, 0, 1), MARSH_WATER[0], 0.6)
    reeds(cv, marsh_m & (mn > 0.44) & (mn < 0.72) & ((_XX * 3 + _YY) % 4 == 0), "reeds")
    stones(cv, band(catmull([(rm[0] - 24, rm[1] - 6), (rm[0] + 4, rm[1] + 2), (rm[0] + 30, rm[1] + 14)]), [2, 2]) & marsh_m, "causeway", pal=STONE, density=2.2)
    gd = rng("dead-trees")
    for i in range(7):     # bleached dead trees standing in the pools
        x = int(rm[0] - 30 + gd.integers(0, 70))
        y = int(rm[1] - 8 + gd.integers(0, 30))
        if marsh_m[y, x]:
            for k in range(int(gd.integers(4, 7))):
                cv.put(x, y - k, DEAD[1 + (k % 2)])
            cv.put(x - 1, y - 3, DEAD[2])
            cv.put(x + 1, y - 4, DEAD[2])
            cv.put(x + 2, y - 5, DEAD[1])

    # ---- Stonewall Quarry: a terraced sandstone pit
    sq = R["stonewall_quarry"]
    pit = m_ellipse(W, H, sq[0], sq[1] + 2, 26, 12)
    for k in range(4):
        t = m_ellipse(W, H, sq[0] + k * 1.5, sq[1] + 2 + k * 1.2, 26 - k * 5.5, 12 - k * 2.6)
        paint(cv, t, QUARRY, 0.75 - k * 0.14 + (noise(3, ("q", k)) - 0.5) * 0.25)
        flat(cv, t & ~shift(t, 0, -1), QUARRY[0], 0.7)
        flat(cv, t & ~shift(t, 0, 1), QUARRY[5], 0.5)
    stones(cv, pit & (noise(3, "q-stones") > 0.6), "quarry-rocks", pal=STONE_WARM, density=1.2)
    # the quarry's cut wall, with a crane
    cliff_face(cv, m_poly(W, H, [(sq[0] - 26, sq[1] - 4), (sq[0] + 26, sq[1] - 4), (sq[0] + 22, sq[1] - 9), (sq[0] - 20, sq[1] - 10)]), "quarry-wall", pal=QUARRY, lit=0.1)
    for k in range(6):
        cv.put(int(sq[0] + 8 + k), int(sq[1] - 12 + k), WOOD[3])
    for k in range(4):
        cv.put(int(sq[0] + 8), int(sq[1] - 12 + k), WOOD[2])

    # ---- roads
    cr = R["caravan_road"]
    st = R["stoneford"]
    road(cv, [(R["mudwater_hideout"][0] + 6, R["mudwater_hideout"][1] - 10), (cr[0] - 12, cr[1] + 8), (cr[0] + 12, cr[1] + 9), (st[0] - 12, st[1] + 8), (st[0] + 2, st[1] + 6)], w=2)
    road(cv, [(st[0] + 8, st[1] + 6), (R["willow_path"][0] - 10, R["willow_path"][1] + 10), (R["willow_path"][0] + 14, R["willow_path"][1] + 9), (R["lotus_ferry"][0] - 6, R["lotus_ferry"][1] + 6)], w=2)
    road(cv, [(st[0] - 2, st[1] - 4), (st[0] - 10, st[1] - 16), (R["jade_sect"][0] + 2, R["jade_sect"][1] + 14)], w=1)
    road(cv, [(st[0] + 8, st[1] - 8), (sq[0] + 2, sq[1] - 12)], w=1)
    road(cv, [(R["lotus_ferry"][0] + 6, R["lotus_ferry"][1] + 8), (rm[0] - 30, rm[1] - 10)], w=1)
    road(cv, [(cf[0] + 14, cf[1] + 16), (cf[0] - 6, cf[1] - 2), (px_ + 4, py_ + 24)], w=1)
    # paddies on the flats by Willow Path and Lotus Ferry
    gp = rng("paddies")
    for i in range(6):
        x = int(R["willow_path"][0] - 30 + i * 12 + gp.integers(-2, 3))
        y = int(R["willow_path"][1] + 12 + (i % 2) * 6 + gp.integers(-1, 2))
        pm = m_poly(W, H, [(x, y), (x + 9, y - 1), (x + 11, y + 4), (x + 2, y + 5)]) & ~water
        paint(cv, pm, GRASS, 0.7 + (i % 3) * 0.1)
        flat(cv, pm & (_YY % 2 == 0), GRASS[2], 0.6)
        flat(cv, pm & ~shift(pm, 0, 1), SAND[2], 0.7)

    # ---- forests of the near valley: crowns wherever the floor is wooded, avoiding water, marsh, bamboo and the pit
    fm = fmask & ~dilate(dilate(water)) & ~marsh_m & ~bam_m & ~dilate(pit) & (_YY > 104)
    forest(cv, fm & (base_n > 0.3), FOREST, "valley-forest", density=0.34, rmin=1.5, rmax=3.0)
    # dark near-edge woods
    forest(cv, floor & (_YY > H - 26) & (base_n > 0.2), FOREST, "near-woods", density=0.5, rmin=2.0, rmax=3.5)

    # ---- willows along Willow Path: drooping crowns on the north bank
    wp = R["willow_path"]
    gw = rng("willows")
    for i in range(7):
        x = int(wp[0] - 26 + i * 8 + gw.integers(-2, 3))
        y = int(wp[1] - 4 + gw.integers(-3, 3) - (i % 2) * 4)
        tree(cv, x, y, 3.2, LEAF_BLUE)
        for k in range(3):
            cv.put(x - 2 + k * 2, y + 3 + (k % 2), LEAF_BLUE[3], 0.9)
            cv.put(x - 2 + k * 2, y + 4 + (k % 2), LEAF_BLUE[2], 0.8)

    # ---- the Academy's hill: a lit lawn with terraces, woods round its skirt
    js = R["jade_sect"]
    hill_m = m_ellipse(W, H, js[0], js[1] + 8, 42, 22)
    paint(cv, hill_m & ~water, GRASS, 0.55 + (0.5 - (_XX - js[0]) / 84.0) * 0.5 - ((_YY - js[1]) / 44.0) * 0.4 + (base_n - 0.5) * 0.25)
    forest(cv, (hill_m & ~erode(erode(erode(erode(hill_m))))) & ~water, FOREST, "academy-woods", density=1.0, rmin=1.4, rmax=2.6)

    # ---- Mudwater Hideout: a log stockade under a cliff with a cave mouth
    mh = R["mudwater_hideout"]
    cliff = m_ellipse(W, H, mh[0] - 8, mh[1] - 12, 30, 10) & (_YY > mh[1] - 16)
    cliff_face(cv, cliff, "mud-cliff", pal=MUD)
    cv.fill(m_rect(W, H, int(mh[0] - 5), int(mh[1] - 9), int(mh[0] - 1), int(mh[1] - 4)), INK)
    cv.fill(m_rect(W, H, int(mh[0] - 4), int(mh[1] - 10), int(mh[0] - 2), int(mh[1] - 10)), INK)
    wall_line(cv, [(mh[0] - 16, mh[1] + 2), (mh[0] - 12, mh[1] + 8), (mh[0] + 12, mh[1] + 8), (mh[0] + 16, mh[1] + 1)], WOOD[5], WOOD[2], h=3)
    for k in range(-14, 15, 3):
        cv.put(int(mh[0] + k), int(mh[1] + 7 + (0 if abs(k) < 12 else -2)), WOOD[6])
    hall(cv, mh[0] + 1, mh[1] + 3, 10, 3, 3, roof=THATCH, wall=WOOD, windows=1, eaves=1)
    lantern(cv, int(mh[0] - 6), int(mh[1] + 5))

    # ---- Stoneford: a town straddling a ford: a stone bridge, halls with lit windows, a gate
    hall(cv, st[0] - 12, st[1] - 5, 10, 4, 3, roof=ROOF_GREY, wall=WALL, windows=2)
    hall(cv, st[0] - 2, st[1] - 7, 8, 3, 3, roof=ROOF_GREY, wall=WALL, windows=1)
    hall(cv, st[0] + 8, st[1] - 4, 12, 4, 4, roof=ROOF, wall=WALL, windows=3)
    hall(cv, st[0] - 14, st[1] + 14, 10, 4, 3, roof=ROOF_GREY, wall=WALL, windows=2)
    hall(cv, st[0] + 12, st[1] + 15, 10, 4, 3, roof=ROOF_GREY, wall=WALL, windows=2)
    pagoda(cv, st[0] - 2, st[1] + 16, 2, 7, roof=ROOF, wall=LACQUER, tier_h=3)
    bridge(cv, int(st[0] - 4), int(st[0] + 12), int(st[1] + 4), rise=3)
    stones(cv, water & m_rect(W, H, int(st[0] + 14), int(st[1] - 2), int(st[0] + 22), int(st[1] + 8)) & ((_XX + _YY) % 3 == 0), "ford", pal=STONE, density=3.0)
    for lx, ly in ((st[0] - 8, st[1] - 1), (st[0] + 3, st[1] - 1), (st[0] - 6, st[1] + 17), (st[0] + 9, st[1] + 18), (st[0] + 18, st[1] + 1)):
        lantern(cv, int(lx), int(ly))

    # ---- Jade Sect Academy: a walled academy on its hill: gate, terraces, halls and the pagoda
    wall_line(cv, [(js[0] - 30, js[1] + 10), (js[0] - 22, js[1] + 16), (js[0] + 20, js[1] + 16), (js[0] + 30, js[1] + 8)], WALL[3], WALL[0], h=2)
    wall_line(cv, [(js[0] - 30, js[1] + 10), (js[0] - 26, js[1] - 8), (js[0] - 8, js[1] - 16)], WALL[3], WALL[0], h=2)
    wall_line(cv, [(js[0] + 30, js[1] + 8), (js[0] + 26, js[1] - 8), (js[0] + 8, js[1] - 16)], WALL[3], WALL[0], h=2)
    for k in range(3):   # the herb terraces on the lit west slope
        tm = m_poly(W, H, [(js[0] - 26 + k, js[1] + 2 + k * 4), (js[0] - 8, js[1] + 4 + k * 4), (js[0] - 8, js[1] + 6 + k * 4), (js[0] - 26 + k, js[1] + 4 + k * 4)])
        paint(cv, tm, GRASS, 0.75 - k * 0.1)
        flat(cv, tm & ~shift(tm, 0, -1), STONE[3], 0.8)
    hall(cv, js[0] - 14, js[1] - 4, 12, 4, 4, roof=ROOF, wall=WALL, windows=2)
    hall(cv, js[0] + 14, js[1] - 2, 14, 4, 4, roof=ROOF, wall=WALL, windows=3)
    hall(cv, js[0] + 2, js[1] + 12, 14, 4, 4, roof=ROOF, wall=WALL, windows=3)
    pagoda(cv, js[0], js[1] - 4, 4, 13, roof=ROOF, wall=LACQUER, tier_h=4)
    hall(cv, js[0], js[1] + 20, 8, 3, 3, roof=ROOF, wall=LACQUER, windows=0, eaves=2)
    for lx, ly in ((js[0] - 5, js[1] + 20), (js[0] + 5, js[1] + 20), (js[0] - 20, js[1] - 1), (js[0] + 20, js[1] + 1), (js[0] + 8, js[1] + 13), (js[0] - 6, js[1] + 13)):
        lantern(cv, int(lx), int(ly))
    karst(cv, js[0] - 36, js[1] - 44, js[1] - 8, 10, 91, crown=0.4)
    hall(cv, js[0] - 36, js[1] - 42, 5, 2, 2, roof=ROOF, wall=WOOD, windows=0, eaves=1)

    # ---- Lotus Ferry: a fishing village on the south bank: docks, boats, lotus pads
    lf = R["lotus_ferry"]
    hall(cv, lf[0] - 10, lf[1] + 4, 8, 3, 3, roof=THATCH, wall=WOOD, windows=1)
    hall(cv, lf[0] + 2, lf[1] + 7, 9, 3, 3, roof=THATCH, wall=WOOD, windows=1)
    hall(cv, lf[0] + 14, lf[1] + 4, 8, 3, 3, roof=THATCH, wall=WOOD, windows=1)
    hall(cv, lf[0] - 2, lf[1] + 15, 10, 3, 3, roof=ROOF_GREY, wall=WALL, windows=2)
    dock(cv, int(lf[0] - 4), int(lf[1] - 2), 9)
    dock(cv, int(lf[0] + 8), int(lf[1] - 3), 7)
    boat(cv, int(lf[0] + 2), int(lf[1] - 6), sail=True)
    boat(cv, int(lf[0] + 20), int(lf[1] - 10), sail=False)
    gl = rng("lotus")
    for i in range(14):
        x = int(lf[0] - 20 + gl.integers(0, 40))
        y = int(lf[1] - 12 + gl.integers(0, 8))
        if water[y, x]:
            cv.put(x, y, LEAF[4])
            if i % 4 == 0:
                cv.put(x, y - 1, hexc("#f2b8c6"))
    for lx, ly in ((lf[0] - 6, lf[1] + 5), (lf[0] + 8, lf[1] + 6), (lf[0] - 4, lf[1] - 3), (lf[0] + 14, lf[1] - 4)):
        lantern(cv, int(lx), int(ly))

    # ---- Greyreed Hamlet: stilt huts at the marsh's edge; the hermit's house alone in the marsh
    gh = R["greyreed_hamlet"]
    stilt_hut(cv, gh[0] - 8, gh[1] + 2)
    stilt_hut(cv, gh[0] + 2, gh[1] + 6)
    stilt_hut(cv, gh[0] + 10, gh[1] - 2)
    lantern(cv, int(gh[0] + 2), int(gh[1] + 1))
    stilt_hut(cv, rm[0] - 6, rm[1] + 6, w=5)

    # ---- Caravan Road: a cart and a way-shrine on the road
    hall(cv, cr[0] - 4, cr[1] + 5, 5, 2, 2, roof=ROOF_GREY, wall=STONE, windows=0, eaves=1)
    for k in range(4):
        cv.put(int(cr[0] + 6 + k), int(cr[1] + 8), WOOD[4] if k < 3 else WOOD[2])
    cv.put(int(cr[0] + 6), int(cr[1] + 9), WOOD[1])
    cv.put(int(cr[0] + 9), int(cr[1] + 9), WOOD[1])
    cv.put(int(cr[0] + 7), int(cr[1] + 7), hexc("#c9b58a"))
    cv.put(int(cr[0] + 8), int(cr[1] + 7), hexc("#c9b58a"))
    lantern(cv, int(cr[0] - 4), int(cr[1] + 4))

    # ---- Deepwater Bend: the wide dark water, a fisher's shelter and the serpent's shallows
    db = R["deepwater_bend"]
    paint(cv, water & m_ellipse(W, H, db[0] + 2, db[1] + 2, 18, 12), RIVER, wv - 0.24)
    boat(cv, int(db[0] + 4), int(db[1] - 1), sail=False)
    hall(cv, db[0] - 8, db[1] + 14, 6, 2, 2, roof=THATCH, wall=WOOD, windows=1, eaves=1)
    for r_ in (3, 6):
        ring = m_circle(db[0] + 10.5, db[1] + 4.5, r_) & ~m_circle(db[0] + 10.5, db[1] + 4.5, r_ - 1) & water
        flat(cv, ring & ((_XX + _YY) % 2 == 0), RIVER[6], 0.7)

    # ---- the Drowned Shrine: a sunken temple in the flooded bay, its roofs and a lantern above the water
    ruin = m_rect(W, H, int(ds[0] - 10), int(ds[1] - 1), int(ds[0] + 10), int(ds[1] + 4)) & lake_m
    paint(cv, ruin, STONE_DARK, 0.5 + (wn - 0.5) * 0.3)
    hall(cv, ds[0] - 9, ds[1] + 2, 6, 1, 3, roof=PATINA, wall=STONE_DARK, windows=0, eaves=1)
    hall(cv, ds[0] + 9, ds[1] + 2, 6, 1, 3, roof=PATINA, wall=STONE_DARK, windows=0, eaves=1)
    hall(cv, ds[0], ds[1], 14, 2, 5, roof=PATINA, wall=STONE_DARK, windows=1, eaves=2)
    pagoda(cv, ds[0], ds[1] - 6, 1, 6, roof=PATINA, wall=STONE_DARK, tier_h=3)
    for px in (ds[0] - 15, ds[0] + 15):
        cv.put(int(px), int(ds[1] + 3), STONE[3])
        cv.put(int(px), int(ds[1] + 2), STONE[4])
        cv.put(int(px), int(ds[1] + 1), STONE[5])
    lantern(cv, int(ds[0]), int(ds[1] - 10), big=True)
    lantern(cv, int(ds[0] - 15), int(ds[1]))
    lantern(cv, int(ds[0] + 15), int(ds[1]))
    for i in range(10):
        x = int(ds[0] - 20 + gl.integers(0, 40))
        y = int(ds[1] - 8 + gl.integers(0, 16))
        if lake_m[y, x]:
            cv.put(x, y, LEAF[4], 0.9)
    reeds(cv, (dilate(dilate(lake_m)) & ~lake_m) & ((_XX * 5 + _YY * 3) % 7 == 0), "shrine-reeds")

    # ---- Whitewater Gorge: cliffs either side of the white water
    wg_l = m_poly(W, H, [(wg[0] - 30, wg[1] - 24), (wg[0] - 6, wg[1] - 14), (wg[0] - 2, wg[1] + 10), (wg[0] - 22, wg[1] + 22), (wg[0] - 40, wg[1] + 6)]) & ~water
    wg_r = m_poly(W, H, [(wg[0] + 4, wg[1] - 26), (wg[0] + 26, wg[1] - 16), (wg[0] + 30, wg[1] + 8), (wg[0] + 12, wg[1] + 20), (wg[0] + 8, wg[1] + 2)]) & ~water & ~dilate(water)
    cliff_face(cv, wg_l & (_YY > 118), "gorge-l", pal=CLIFF, lit=0.12)
    cliff_face(cv, wg_r & (_YY > 118), "gorge-r", pal=CLIFF, lit=-0.15)
    forest(cv, (wg_l | wg_r) & (noise(4, "gorge-trees") > 0.6) & (_YY > 118), FOREST, "gorge-trees", density=0.5, rmin=1.0, rmax=1.8)
    waterfall(cv, int(wg[0] + 10), int(wg[1] - 14), int(wg[1] - 2), w=2, seed=3)

    # ---- Crane Cliffs: cranes over the cliff
    for dx, dy in ((-6, -10), (4, -14), (12, -6), (-14, 0)):
        crane(cv, int(cx_ + dx), int(cy_ + dy))

    # ---- Cleansing Peak: the pilgrim stair up the pinnacle to a summit shrine
    for k in range(14):
        sx_ = int(px_ + 2 - k * 0.6 + (2 if k % 4 == 0 else 0))
        cv.put(sx_, int(py_ + 22 - k * 2.4), STONE[5], 0.9)
        cv.put(sx_ + 1, int(py_ + 22 - k * 2.4), STONE[3], 0.9)
    hall(cv, px_ + 2, py_ - 12, 6, 2, 3, roof=ROOF, wall=PLASTER, windows=1, eaves=1)
    lantern(cv, int(px_ + 2), int(py_ - 9))
    lantern(cv, int(px_ - 2), int(py_ + 10))

    # ---- Mist Peak and Summit Ridge: the frozen shrine on the ridge, a monastery ruin on the slopes
    hall(cv, sx + 4, sy + 6, 6, 2, 3, roof=SNOW, wall=STONE, windows=0, eaves=1)
    hall(cv, mx + 6, my + 24, 8, 3, 3, roof=ROOF_GREY, wall=STONE_DARK, windows=0, eaves=1)

    # ---- the Cloud Sect Monastery: white halls on the pinnacle's shoulder, clouds round its waist
    ledge = m_poly(W, H, [(cs_x - 16, cs_y - 4), (cs_x + 18, cs_y - 6), (cs_x + 20, cs_y - 1), (cs_x - 18, cs_y + 1)])
    paint(cv, ledge, ROCK, 0.7 - (_XX - cs_x) / 40.0)
    hall(cv, cs_x - 8, cs_y - 6, 12, 4, 4, roof=ROOF, wall=PLASTER, windows=2)
    hall(cv, cs_x + 10, cs_y - 4, 10, 3, 3, roof=ROOF, wall=PLASTER, windows=2)
    pagoda(cv, cs_x + 1, cs_y - 11, 4, 11, roof=ROOF, wall=PLASTER, tier_h=3)
    lantern(cv, int(cs_x - 2), int(cs_y - 7))
    lantern(cv, int(cs_x + 10), int(cs_y - 5))
    for k in range(8):   # the cliff stair down from the ledge
        cv.put(int(cs_x - 12 + k), int(cs_y + 1 + k * 2), STONE[5], 0.9)
        cv.put(int(cs_x - 11 + k), int(cs_y + 1 + k * 2), STONE[3], 0.9)
    cloud_puff(cv, cs_x - 18, cs_y + 12, 18, 7, "cs-cloud-1")
    cloud_puff(cv, cs_x + 18, cs_y + 16, 16, 6, "cs-cloud-2")
    cloud_puff(cv, cs_x + 2, cs_y + 22, 14, 5, "cs-cloud-3")

    # ---- Hidden Vale: the player's own sect grounds in a fold behind the ridge, pale and quiet
    vale = m_ellipse(W, H, hv_x + 2, hv_y + 14, 22, 9)
    paint(cv, vale, GRASS, 0.5 + (base_n - 0.5) * 0.3 - (_YY - hv_y - 6) / 30.0)
    flat(cv, vale & ~erode(vale), GRASS[1], 0.7)
    forest(cv, vale & ~erode(erode(erode(vale))), FOREST, "vale-woods", density=0.8, rmin=1.2, rmax=2.0)
    hall(cv, hv_x - 2, hv_y + 14, 9, 3, 3, roof=ROOF, wall=WALL, windows=2)
    hall(cv, hv_x + 10, hv_y + 18, 6, 2, 2, roof=ROOF, wall=WALL, windows=1, eaves=1)
    wall_line(cv, [(hv_x - 14, hv_y + 20), (hv_x - 6, hv_y + 23), (hv_x + 14, hv_y + 23), (hv_x + 20, hv_y + 18)], WALL[3], WALL[0], h=1)
    lantern(cv, int(hv_x - 2), int(hv_y + 15))
    patchy(cv, m_ellipse(W, H, hv_x + 4, hv_y + 4, 30, 9), MIST, 0.45, 12, "vale-mist", cover=0.55)

    # ---- Crane Falls: the pool's pavilion where the falls are listened to
    hall(cv, cf[0] + 14, cf[1] + 14, 6, 2, 3, roof=ROOF, wall=LACQUER, windows=0, eaves=1)
    lantern(cv, int(cf[0] + 14), int(cf[1] + 13))
    crane(cv, int(cf[0] - 6), int(cf[1] + 4))

    # ---- boats on the main river
    boat(cv, int(R["willow_path"][0] - 6), int(R["willow_path"][1] + 2), sail=True, flip=True)
    boat(cv, int(cr[0] - 8), int(cr[1] - 5), sail=False)

    # ---- mist: wisps at the feet of the range, over the marsh and the gorge; the near edge darkens
    patchy(cv, m_rect(W, H, 0, 78, W - 1, 118), CLOUD[2], 0.42, 16, "range-mist", cover=0.45)
    patchy(cv, m_ellipse(W, H, rm[0] + 20, rm[1] + 18, 70, 22), MIST, 0.4, 16, "marsh-mist", cover=0.5)
    patchy(cv, m_ellipse(W, H, wg[0] - 4, wg[1] + 2, 30, 18), MIST, 0.45, 12, "gorge-mist", cover=0.5)
    near = m_rect(W, H, 0, H - 44, W - 1, H - 1)
    t = np.clip((_YY - (H - 44)) / 44.0, 0, 1)
    for step, a in ((0.2, 0.08), (0.45, 0.1), (0.7, 0.12), (0.92, 0.14)):
        cv.fill(near & (t >= step), INK, a)
    return cv


# ---------------------------------------------------------------- output
def vignette(img, regions, rid):
    x, y, _ = regions[rid]
    x0 = int(min(max(0, x - VIG_W / 2), W - VIG_W))
    y0 = int(min(max(0, y - VIG_H / 2 + 2), H - VIG_H))
    return img.crop((x0, y0, x0 + VIG_W, y0 + VIG_H))


def review_sheet(img, regions, path):
    """The painting at 2x with each region's anchor marked, and at 1x under it, for the eye."""
    from PIL import ImageFont
    big = img.resize((W * 2, H * 2), Image.NEAREST).convert("RGB")
    d = ImageDraw.Draw(big)
    try:
        font = ImageFont.truetype(os.path.join(ROOT, "art", "fonts", "SourceSerif4.ttf"), 14)
    except Exception:
        font = ImageFont.load_default()
    for rid, (x, y, name) in regions.items():
        X, Y = x * 2, y * 2
        d.ellipse([X - 5, Y - 5, X + 5, Y + 5], outline=(255, 230, 161), width=2)
        d.text((X + 8, Y - 8), name, fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    sheet = Image.new("RGB", (W * 2, H * 2 + H + 8), (10, 32, 39))
    sheet.paste(big, (0, 0))
    sheet.paste(img.convert("RGB"), (0, H * 2 + 8))
    sheet.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--review", default=DEFAULT_REVIEW)
    args = ap.parse_args()
    regions = load_regions()
    cv = paint_map(regions)
    img = cv.image(scale=1, opaque=True)
    os.makedirs(args.review, exist_ok=True)
    review_sheet(img, regions, os.path.join(args.review, "valley_map_review.png"))
    img.resize((W * SCALE, H * SCALE), Image.NEAREST).save(os.path.join(args.review, "valley_map_x2.png"))
    if args.no_write:
        print("review only:", args.review)
        return
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "valley_map.png")
    save_png(img.resize((W * SCALE, H * SCALE), Image.NEAREST), out)
    print(os.path.relpath(out, ROOT), "%dx%d" % (W * SCALE, H * SCALE))
    for rid in regions:
        v = vignette(img, regions, rid)
        p = os.path.join(OUT_DIR, "valley_%s.png" % rid)
        save_png(v.resize((VIG_W * SCALE, VIG_H * SCALE), Image.NEAREST), p)
    print("%d vignettes %dx%d" % (len(regions), VIG_W * SCALE, VIG_H * SCALE))


if __name__ == "__main__":
    main()
