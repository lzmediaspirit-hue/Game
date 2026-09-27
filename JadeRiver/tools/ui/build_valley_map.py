#!/usr/bin/env python3
"""Paint the Jade River Valley world map: art/ui/maps/valley_map.png and one close-up vignette per region.

    python3 tools/ui/build_valley_map.py                 # -> art/ui/maps/valley_map.png, valley_<region>.png, review sheets
    python3 tools/ui/build_valley_map.py --no-write      # review sheets only (scratchpad art_review/valley_map*.png)

The map is a painted pixel landscape of the whole valley seen from above at an angle in late-afternoon light: the Jade
River pouring off the cliffs at Crane Falls, winding west through Lotus Ferry, Willow Path, Stoneford, the Caravan
Road and Deepwater Bend, flooding the Drowned Shrine's bay and leaving through Whitewater Gorge; the northern range
(Summit Ridge, Mist Peak, Crane Cliffs, Cleansing Peak) behind layers of mist, the Cloud Sect on its pinnacle, the
Jade Sect Academy walled on its hill, paddies and terraces on the flats, bamboo, the Reed Marsh, the quarry, the
hideout, farms and a watermill between, and dark trees and a rooftop corner in the near foreground. Every region of
data/zones.json is an illustrated scene centred on its `map` position, so the map page puts its nodes straight on top
(the map rect is MAP_RECT, in art px; the page scales it x2). The same scene functions paint each region's vignette
at twice the scale for the page's side card.

Authored at art pixels (640 x 320) and saved x2 nearest, like every other piece of the game's art (tools/ui/README.md).
Gradients are ordered-dithered between flat ramp steps; mist and glows are stepped, never blurred. Deterministic:
every random choice is seeded from a stable string, so a rebuild is byte-identical.
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

from pixlib import Canvas, hexc, ramp, rng, save_png, shift, erode, dilate  # noqa: E402
from palette import (LEAF, LEAF_BLUE, STONE, STONE_WARM, STONE_DARK, ROOF, LACQUER, WOOD, GOLD,  # noqa: E402
                     THATCH, MUD, CLOTH_WHITE, SAND, PLASTER, PATINA, ROOF_GREY, INK)

DEFAULT_REVIEW = "/tmp/claude-0/-home-user-Game/13461237-7857-505a-bd3b-55d18a20fe2c/scratchpad/art_review"
OUT_DIR = os.path.join(ROOT, "art", "ui", "maps")
SCALE = 2
W, H = 640, 320                      # art px; 1280 x 640 on screen
MAP_RECT = (24, 34, 424, 276)        # x, y, w, h (art px): where a region's `map` [0..1] position lands
VIG_W, VIG_H = 128, 72               # vignette canvas (art px); 256 x 144 on screen, the scene at twice the map's scale

# ---------------------------------------------------------------- ramps (dark -> light)
SKY = ramp("#b3c6cc", "#c7d5d3", "#dbe1d3", "#ecead6", "#f6efd8", "#fbf3dc")
FAR = ramp("#5b7d8c", "#7395a0", "#8dabb0", "#a6c0bf", "#bfd2cb")
ROCK = ramp("#1f2c30", "#33454a", "#4c6265", "#68807f", "#88a098", "#abbcb0", "#cbd5c6")
CLIFF = ramp("#2b3538", "#414f50", "#5b6c69", "#778a83", "#98a89d", "#b8c3b4", "#d3d9cb")
SNOW = ramp("#a9bfc6", "#cad9da", "#e6eeeb", "#f7f9f4")
GRASS = ramp("#3b5f2f", "#4d7a36", "#629542", "#7bad50", "#98c25f", "#b9d472", "#d9e58f")
MEADOW = ramp("#3f6330", "#52803a", "#699a45", "#83b152", "#9cc35f", "#b7d274", "#d2df92")
FOREST = ramp("#0d221d", "#153629", "#1e4d34", "#2a6640", "#3c854c", "#5aa05c", "#c4d97e")
OLIVE = ramp("#1e3320", "#2b4a2a", "#3b6535", "#4f8140", "#699c4c", "#8bb85c", "#d6e08a")
PINE = ramp("#0f2a2a", "#163e3a", "#1f5549", "#2b6c58", "#3e8868", "#5ea67a", "#b7d894")
WILLOW = ramp("#1a3a30", "#245244", "#316b55", "#468a68", "#66a67e", "#8fc396", "#cfe4b0")
PLUM = ramp("#5a2a3a", "#8a3f56", "#b25f78", "#d3849a", "#e9a9bb", "#f5cbd6", "#fff0f3")
ORCHARD = ramp("#2e4a26", "#3f6532", "#548140", "#6c9c4e", "#8ab85e", "#a9cf72", "#e2e9a0")
BAMBOO = ramp("#24512a", "#37743a", "#4f9a48", "#6fb85a", "#98d070", "#c8e59a")
MARSH = ramp("#3d4f43", "#546a55", "#6d8266", "#8a9a7d", "#a6ae93", "#c2c4a8")
MARSH_WATER = ramp("#2a4142", "#3d5a59", "#557572", "#75938f", "#98b1ab")
RIVER = ramp("#0d3c46", "#135a63", "#1a7b80", "#279b96", "#42bcaf", "#72d8c6", "#a8ebdc", "#dcf8f0")
LAKE = ramp("#0f3237", "#164a4c", "#1e6361", "#2c7f77", "#48998c", "#7dbfaf")
FOAM = ramp("#9fd6cf", "#cdeee6", "#f2fbf7")
PADDY = ramp("#4f8c78", "#68a58c", "#86bea0", "#a4d2b4", "#c3e1c5")
RICE = ramp("#5c8f3a", "#76aa46", "#93c257", "#b0d46c")
LEVEE = ramp("#8c7a52", "#ad9868", "#c9b07c", "#e0cb95")
QUARRY = ramp("#5a4630", "#7a603e", "#9a7c4e", "#b89760", "#d3b478", "#e8cf98")
ROAD = ramp("#7a6543", "#98805a", "#b49b6d", "#cdb684", "#e0cf9e")
WALL = ramp("#8a8474", "#a8a28f", "#c6c0aa", "#e0dbc6")
ROOF_BLUE = ramp("#16303d", "#1e4553", "#285e6c", "#347a86", "#4a9aa3", "#74bfc0", "#a9dfd8")
AWNING_R = hexc("#b73a34")
AWNING_W = hexc("#efe2c6")
GLOW = hexc("#ffd27a")
LANTERN = hexc("#ffb347")
WINDOW = hexc("#ffcf6e")
CLOUD = ramp("#b7c6c9", "#cfdadb", "#e4ebe9", "#f4f7f3", "#fdfdf8")
MIST = hexc("#eef1e6")
SAIL = ramp("#8f7d5b", "#b8a67d", "#d9c99c")
HULL = ramp("#2c1c12", "#4a3120", "#6b4a2d")
DEAD = ramp("#5c6a66", "#8a9590", "#b7bfb6")
FIRE = ramp("#8c2a12", "#d0561c", "#f39a2c", "#ffd66a")
DARK_ROOF = ramp("#0a1a1f", "#0f262c", "#153439", "#1d4449", "#27575a")

_B4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], float) / 16.0 + 1 / 32.0


# ---------------------------------------------------------------- the painter: one canvas, its grids, masks and paints
class P:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.cv = Canvas(w, h)
        self.YY, self.XX = np.mgrid[0:h, 0:w]
        self.B = np.tile(_B4, (h // 4 + 1, w // 4 + 1))[:h, :w]
        self._noise = {}
        self.lanterns = []      # (x, y, big) for the water reflections
        self.water = np.zeros((h, w), bool)

    # masks
    def zeros(self):
        return np.zeros((self.h, self.w), bool)

    def all(self):
        return np.ones((self.h, self.w), bool)

    def ellipse(self, cx, cy, rx, ry):
        rx, ry = max(rx, 0.5), max(ry, 0.5)
        return ((self.XX + 0.5 - cx) / rx) ** 2 + ((self.YY + 0.5 - cy) / ry) ** 2 <= 1.0

    def circle(self, cx, cy, r):
        return self.ellipse(cx, cy, r, r)

    def rect(self, x0, y0, x1, y1):
        m = self.zeros()
        x0, x1 = max(0, int(round(x0))), min(self.w - 1, int(round(x1)))
        y0, y1 = max(0, int(round(y0))), min(self.h - 1, int(round(y1)))
        if x1 >= x0 and y1 >= y0:
            m[y0:y1 + 1, x0:x1 + 1] = True
        return m

    def poly(self, pts):
        im = Image.new("1", (self.w, self.h), 0)
        ImageDraw.Draw(im).polygon([(float(x), float(y)) for x, y in pts], fill=1, outline=1)
        return np.array(im, bool)

    def line(self, pts, width=1):
        im = Image.new("1", (self.w, self.h), 0)
        ImageDraw.Draw(im).line([(float(x), float(y)) for x, y in pts], fill=1, width=int(max(1, width)))
        return np.array(im, bool)

    def band(self, pts, widths):
        """A mask along a dense polyline with a per-point width (interpolated along the list)."""
        im = Image.new("1", (self.w, self.h), 0)
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

    def noise(self, cell, seed, octaves=1):
        key = (cell, str(seed), octaves)
        if key in self._noise:
            return self._noise[key]
        g = rng("map-noise", seed)
        out = np.zeros((self.h, self.w))
        amp, norm, c = 1.0, 0.0, float(cell)
        for _ in range(octaves):
            gw = int(math.ceil(self.w / c)) + 2
            gh = int(math.ceil(self.h / c)) + 2
            gv = g.random((gh, gw))
            fx, fy = self.XX / c, self.YY / c
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
        self._noise[key] = out / norm
        return self._noise[key]

    # paints
    def dq(self, v, n, sharp=1.0):
        fl = np.floor(v)
        fr = v - fl
        if sharp != 1.0:
            fr = np.clip((fr - 0.5) * sharp + 0.5, 0.0, 1.0)
        return np.clip((fl + (fr > self.B)).astype(int), 0, n - 1)

    def paint(self, m, pal, v, sharp=1.0):
        """Fill mask m from ramp pal (dark -> light) by the 0..1 field v, dithered."""
        if not m.any():
            return
        idx = self.dq(np.clip(v, 0, 1) * (len(pal) - 1), len(pal), sharp)
        self.cv.fill_idx(m, idx, pal)

    def flat(self, m, c, a=1.0):
        if m.any():
            self.cv.fill(m, c, a)

    def light(self, m, c, a):
        if m.any():
            self.cv.light(m, c, a)

    def put(self, x, y, c, a=1.0):
        self.cv.put(x, y, c, a)

    def px(self, x, y, c, a=1.0):
        self.cv.put(int(round(x)), int(round(y)), c, a)

    def image(self):
        return self.cv.image(scale=1, opaque=True)


def catmull(pts, per=1.5):
    """Catmull-Rom through pts -> dense list of (x, y)."""
    if len(pts) < 3:
        n = max(2, int(math.hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]) * per))
        return [(pts[0][0] + (pts[1][0] - pts[0][0]) * i / n, pts[0][1] + (pts[1][1] - pts[0][1]) * i / n) for i in range(n + 1)]
    Pp = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(Pp) - 2):
        p0, p1, p2, p3 = Pp[i - 1], Pp[i], Pp[i + 1], Pp[i + 2]
        seg = max(2, int(math.hypot(p2[0] - p1[0], p2[1] - p1[1]) * per))
        for s in range(seg):
            t = s / seg
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(tuple(pts[-1]))
    return out


def catmull_w(pts, per=1.5):
    """Catmull-Rom through (x, y, w) points -> dense (x, y, w), the width interpolated along each segment."""
    Pp = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(Pp) - 2):
        p0, p1, p2, p3 = Pp[i - 1], Pp[i], Pp[i + 1], Pp[i + 2]
        seg = max(2, int(math.hypot(p2[0] - p1[0], p2[1] - p1[1]) * per))
        for s in range(seg):
            t = s / seg
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y, p1[2] + (p2[2] - p1[2]) * t))
    out.append(tuple(pts[-1]))
    return out


def band_w(p, triples):
    im = Image.new("1", (p.w, p.h), 0)
    d = ImageDraw.Draw(im)
    for x, y, w in triples:
        r = w / 2.0
        d.ellipse([x - r, y - r, x + r, y + r], fill=1)
    return np.array(im, bool)


def gauss(p, cx, cy, sx, sy, amp=1.0, pw=2.0):
    return amp * np.exp(-((np.abs(p.XX - cx) / sx) ** pw + (np.abs(p.YY - cy) / sy) ** pw))


def light_field(hmap, kx=1.0, ky=0.6):
    gx = np.zeros_like(hmap)
    gy = np.zeros_like(hmap)
    gx[:, 1:-1] = (hmap[:, 2:] - hmap[:, :-2]) * 0.5
    gy[1:-1, :] = (hmap[2:, :] - hmap[:-2, :]) * 0.5
    return -gx * kx - gy * ky


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


# ---------------------------------------------------------------- trees: stamped crowns, lit from the upper left
_STAMPS = {}


def _tree_stamp(r):
    """Ramp indices for one crown of radius r (-1 outside): a lit upper-left, a shadowed lower-right, a warm top pixel."""
    key = round(r * 2) / 2
    if key in _STAMPS:
        return _STAMPS[key]
    n = int(math.ceil(key)) * 2 + 1
    c = n // 2
    yy, xx = np.mgrid[0:n, 0:n]
    inside = (xx - c) ** 2 + (yy - c) ** 2 <= key * key + 0.3
    d = ((xx - c) * 0.85 + (yy - c) * 1.0) / max(key, 1.0)
    v = np.clip(0.64 - d * 0.36, 0, 1)
    idx = np.where(inside, np.clip(np.floor(v * 6.0 + ((xx + yy) % 2) * 0.3), 0, 5), -1).astype(int)
    if key >= 2:
        idx[max(0, c - 1), max(0, c - 1)] = 6
    if key >= 3.5:
        idx[max(0, c - 2), c] = 6
    # an ink-dark rim on the lower right
    edge = inside & ~np.roll(np.roll(inside, -1, 0), -1, 1)
    idx[edge & (xx + yy > 2 * c)] = 0
    _STAMPS[key] = idx
    return idx


def tree(p, x, y, r, pal, shadow=True):
    idx = _tree_stamp(r)
    n = idx.shape[0]
    c = n // 2
    x0, y0 = int(round(x)) - c, int(round(y)) - c
    palA = np.array(pal, float)
    cv = p.cv
    for j in range(n):
        py = y0 + j
        if py < 0 or py >= p.h:
            continue
        row = idx[j]
        for i in range(n):
            k = row[i]
            if k < 0:
                continue
            px = x0 + i
            if 0 <= px < p.w:
                cv.rgb[py, px] = palA[min(k, len(pal) - 1)]
                cv.a[py, px] = 1.0
    if shadow:
        py = y0 + n
        if 0 <= py < p.h:
            for i in range(n):
                px = x0 + i
                if 0 <= px < p.w and idx[n - 1, i] >= 0:
                    cv.rgb[py, px] = cv.rgb[py, px] * 0.5 + palA[0] * 0.5


def clump(p, cx, cy, n, rmin, rmax, pal, seed, spread=1.0):
    """A clump of crowns round (cx, cy): individual rounded canopies, the back ones drawn first."""
    g = rng("clump", seed)
    pts = []
    for i in range(n):
        a = g.uniform(0, 2 * math.pi)
        d = g.uniform(0, 1) ** 0.6 * spread * rmax * 1.6
        pts.append((cx + math.cos(a) * d, cy + math.sin(a) * d * 0.6, g.uniform(rmin, rmax)))
    for x, y, r in sorted(pts, key=lambda t: t[1]):
        tree(p, x, y, r, pal)


def forest(p, m, pal, seed, density=0.5, rmin=1.5, rmax=3.0, near=0.0):
    """Fill a mask with crowns, back to front; crowns grow toward the near edge (bottom) when near > 0."""
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
        r = rs[o] * (1.0 + near * (ys[i] / p.h - 0.5))
        tree(p, xs[i], ys[i], max(1.0, r), pal)


def clumps_in(p, m, pal, seed, count, nmin=4, nmax=10, rmin=1.5, rmax=3.2, near=0.0):
    """Scatter clumps through a mask."""
    g = rng("clumps", seed)
    ys, xs = np.nonzero(m)
    if len(xs) == 0:
        return
    pick = g.integers(0, len(xs), count)
    order = np.argsort(ys[pick], kind="stable")
    for k, o in enumerate(order):
        i = pick[o]
        f = 1.0 + near * (ys[i] / p.h - 0.5)
        clump(p, xs[i], ys[i], int(g.integers(nmin, nmax + 1)), rmin * f, rmax * f, pal, (seed, k))


def bamboo_field(p, m, seed, s=1, density=0.7):
    g = rng("bamboo", seed)
    ys, xs = np.nonzero(m)
    if len(xs) == 0:
        return
    base = p.noise(6 * s, ("bamboo-base", seed))
    p.paint(m, BAMBOO, 0.12 + base * 0.3)
    n = int(len(xs) * density / (5.0 * s))
    pick = g.integers(0, len(xs), n)
    for i in sorted(pick, key=lambda i: ys[i]):
        x, y = int(xs[i]), int(ys[i])
        h = int(g.integers(4, 8)) * s
        for k in range(h):
            if 0 <= y - k < p.h and m[y - k, x]:
                p.put(x, y - k, BAMBOO[2 + (k * 3) // h] if k < h - 1 else BAMBOO[5])
                if s > 1 and x + 1 < p.w:
                    p.put(x + 1, y - k, BAMBOO[1 + (k * 3) // h], 0.9)
        if 0 <= y + 1 < p.h and m[y + 1, x]:
            p.put(x, y + 1, BAMBOO[0], 0.8)
        p.put(x + s, y - h + 2 * s, BAMBOO[4], 0.8)
        p.put(x - s, y - h + 3 * s, BAMBOO[3], 0.8)


def reeds(p, m, seed, s=1):
    g = rng("reeds", seed)
    ys, xs = np.nonzero(m)
    if len(xs) == 0:
        return
    n = len(xs) // (5 * s)
    pick = g.integers(0, len(xs), n)
    for i in pick:
        x, y = int(xs[i]), int(ys[i])
        h = int(g.integers(2, 5)) * s
        c = MARSH[3 + int(g.integers(0, 3))]
        for k in range(h):
            p.put(x, y - k, c, 0.9)
        p.put(x, y - h, hexc("#b9a97a"), 0.9)


def dead_tree(p, x, y, h, s=1):
    for k in range(h):
        p.put(x, y - k, DEAD[1 + (k % 2)])
        if s > 1:
            p.put(x + 1, y - k, DEAD[0])
    p.put(x - s, y - h * 0.5, DEAD[2])
    p.put(x + s, y - h * 0.66, DEAD[2])
    p.put(x + 2 * s, y - h * 0.8, DEAD[1])
    p.put(x - 2 * s, y - h * 0.7, DEAD[1])


# ---------------------------------------------------------------- landforms
def karst(p, cx, top, base, hw, seed, rock=ROCK, snow=None, crown=0.55, skirt=0.5, fade=0.0, pal_crown=FOREST):
    """A karst tower seen from above at an angle: a rounded cap, a lit left face, a shadowed right face, forest on
    the shoulders and round the foot; fade > 0 hazes it toward the sky (the far ranges)."""
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
    left = [(cx - prof[i], ys[i]) for i in range(len(ys))]
    right = [(cx + prof[i], ys[i]) for i in range(len(ys))][::-1]
    m = p.poly(left + right)
    if not m.any():
        return m
    depth = np.clip((p.YY - top) / h, 0, 1)
    xr = (p.XX - cx) / np.maximum(1.0, hw * (0.42 + 0.58 * depth ** 0.75))
    n2 = p.noise(4, ("karst-n", seed), 2)
    strata = ((p.YY + (n2 * 5).astype(int)) % 5 == 0)
    v = 0.66 - np.clip(xr, -1, 1) * 0.42 - depth * 0.3 + (n2 - 0.5) * 0.3
    p.paint(m, rock, v)
    p.flat(m & strata & (xr > 0.1), rock[1], 0.5)
    p.flat(m & strata & (xr <= 0.1), rock[3], 0.35)
    if snow is not None:
        sm = m & (depth < 0.2) & (n2 > 0.3)
        p.paint(sm, snow, 0.5 - np.clip(xr, -1, 1) * 0.4 + (n2 - 0.5) * 0.4)
    p.flat(m & ~shift(m, -1, 0), rock[0], 0.85)
    p.flat(dilate(m) & ~m, INK, 0.5)
    p.flat(m & ~shift(m, 1, 0) & ~shift(m, 0, 1), rock[-1], 0.5)
    p.flat(m & ~shift(m, 0, -1), rock[0], 0.7)
    if crown:
        shoulders = m & (depth > 0.16) & (depth < 0.45) & (n2 > 0.55) & (xr < 0.4)
        forest(p, shoulders, pal_crown, ("karst-crown", seed), density=crown, rmin=1.0, rmax=1.8)
        foot = m & (depth > 1 - skirt) & (n2 > 0.35)
        forest(p, foot, pal_crown, ("karst-foot", seed), density=crown * 1.1, rmin=1.2, rmax=2.2)
    if fade > 0:
        p.light(dilate(m), SKY[3], fade)
    return m


def cliff(p, m, seed, pal=CLIFF, lit=0.0, s=1):
    """Vertical rock strata inside a mask, a lit top edge and a dark foot."""
    n2 = p.noise(3 * s, ("cliff", seed), 2)
    stripes = ((p.YY + (n2 * 6).astype(int)) % (4 * s) == 0)
    p.paint(m, pal, 0.55 + (n2 - 0.5) * 0.5 + lit)
    p.flat(m & stripes, pal[1], 0.55)
    p.flat(m & ~shift(m, 0, 1), pal[-1], 0.45)
    p.flat(m & ~shift(m, 0, -1), pal[0], 0.7)
    p.flat(dilate(m) & ~m, INK, 0.35)


def hill(p, cx, cy, rx, ry, seed, pal=MEADOW, rocky=0.0):
    m = p.ellipse(cx, cy, rx, ry)
    n2 = p.noise(6, ("hill", seed))
    d = ((p.XX - cx) / rx) * 0.9 + ((p.YY - cy) / ry) * 0.8
    v = 0.62 - d * 0.36 + (n2 - 0.5) * 0.3
    p.paint(m, pal, v)
    if rocky:
        p.paint(m & (n2 > 1 - rocky), CLIFF, v)
    p.flat(m & ~shift(m, 0, -1), pal[0], 0.5)
    return m


# ---------------------------------------------------------------- fields
def paddies(p, cx, cy, cols, rows, cw, ch, seed, skew=0.35, s=1):
    """Flooded rice paddies: a grid of skewed plots reflecting the sky, levees between, rows of young rice."""
    g = rng("paddies", seed)
    cw, ch = cw * s, ch * s
    x0 = cx - cols * cw / 2
    y0 = cy - rows * ch / 2
    for r in range(rows):
        for c in range(cols):
            x = x0 + c * cw + (rows - r) * skew * ch
            y = y0 + r * ch
            m = p.poly([(x, y), (x + cw, y), (x + cw - skew * ch, y + ch), (x - skew * ch, y + ch)])
            flooded = g.random() < 0.6
            if flooded:
                p.paint(m, PADDY, 0.45 + (p.noise(5 * s, ("paddy", seed)) - 0.5) * 0.5 + ((p.XX - x) / cw) * 0.2)
                p.flat(m & (p.YY % (2 * s) == 0) & (p.XX % (3 * s) == 0), RICE[2], 0.7)
            else:
                p.paint(m, RICE, 0.35 + (p.noise(5 * s, ("rice", seed)) - 0.5) * 0.5)
                p.flat(m & (p.YY % (2 * s) == 0), RICE[0], 0.5)
            p.flat(m & ~shift(m, 0, 1), LEVEE[3], 0.9)
            p.flat(m & ~shift(m, 0, -1), LEVEE[0], 0.8)
            p.flat(m & ~shift(m, 1, 0), LEVEE[2], 0.7)


def terraces(p, cx, cy, n, w, seed, s=1, pal=RICE):
    """Stepped fields up a slope: curved strips, each with a lit riser."""
    for k in range(n):
        y = cy + (k - n / 2) * 4 * s
        ww = w * s * (0.75 + 0.25 * k / max(1, n - 1))
        m = p.poly([(cx - ww / 2, y), (cx + ww / 2, y - 2 * s), (cx + ww / 2, y + 1 * s), (cx - ww / 2, y + 3 * s)])
        p.paint(m, pal, 0.5 + (k % 3) * 0.15 + (p.noise(4 * s, ("terr", seed)) - 0.5) * 0.3)
        p.flat(m & ~shift(m, 0, 1), LEVEE[3], 0.9)
        p.flat(m & ~shift(m, 0, -1), STONE[2], 0.8)


def orchard(p, cx, cy, cols, rows, pitch, seed, s=1, pal=ORCHARD, r=1.6):
    g = rng("orchard", seed)
    for rr in range(rows):
        for c in range(cols):
            x = cx + (c - cols / 2 + 0.5) * pitch * s + (rr % 2) * pitch * s * 0.5
            y = cy + (rr - rows / 2 + 0.5) * pitch * s * 0.8
            tree(p, x + g.uniform(-0.5, 0.5), y + g.uniform(-0.5, 0.5), r * s, pal)


def meadow_flowers(p, m, seed, colours=(hexc("#f2d16b"), hexc("#f0f0e0"), hexc("#e59ab0"))):
    g = rng("flowers", seed)
    ys, xs = np.nonzero(m)
    if len(xs) == 0:
        return
    for i in g.integers(0, len(xs), len(xs) // 40):
        p.put(int(xs[i]), int(ys[i]), colours[int(g.integers(0, len(colours)))], 0.9)


# ---------------------------------------------------------------- water
def river_paint(p, water, seed, deep=None, s=1, glints=True):
    """Luminous water: turquoise with light bands, darker in the deep middle, pale shallows and glints by the banks."""
    wn = p.noise(4 * s, ("water", seed), 2)
    bands = p.noise(14 * s, ("bands", seed))
    streak = (bands > 0.55) & ((p.YY // s + (wn * 6).astype(int)) % 3 == 0)
    wv = 0.5 + (wn - 0.5) * 0.3
    p.paint(water, RIVER, wv)
    core = water
    for _ in range(3 * s):
        core = erode(core)
    p.paint(core, RIVER, wv - 0.16)
    if deep is not None:
        p.paint(water & deep, RIVER, wv - 0.28)
    shallow = water & ~erode(erode(water)) if s == 1 else water & ~erode(erode(erode(erode(water))))
    p.paint(shallow, RIVER, wv + 0.22)
    p.flat(water & streak, RIVER[6], 0.5)
    p.flat(core & streak, RIVER[5], 0.4)
    bank = dilate(water) & ~water
    p.flat(bank, SAND[3], 0.75)
    p.flat(shift(water, 0, -1) & ~water, FOREST[0], 0.5)
    if glints:
        glint = water & (shift(bank, 0, 1) | shift(bank, 1, 0)) & ((p.XX + p.YY) % 3 == 0)
        p.flat(glint, RIVER[7], 0.85)


def rapids(p, m, seed, s=1):
    wn = p.noise(3 * s, ("rapids", seed), 2)
    p.flat(m & (wn > 0.48), FOAM[1], 0.8)
    p.flat(m & (wn > 0.66), FOAM[2], 0.9)
    p.flat(m & (wn < 0.3), RIVER[2], 0.5)


def waterfall(p, x, y0, y1, w=3, seed=0, s=1, tiers=1):
    """A white fall from y0 to y1 in tiers, each with a ledge pool and spray."""
    n2 = p.noise(2 * s, ("falls", seed, x))
    step = (y1 - y0) / tiers
    for t in range(tiers):
        ya, yb = int(y0 + t * step), int(y0 + (t + 1) * step)
        xx = x + (t % 2) * 2 * s - s
        m = p.rect(xx - w // 2, ya, xx + w // 2, yb)
        v = 0.55 + (n2 - 0.5) * 0.9 + ((p.YY - ya) / max(1, yb - ya)) * 0.3
        p.paint(m, FOAM, v)
        p.flat(m & (p.YY % (3 * s) == (seed % 3)) & (n2 < 0.45), RIVER[5], 0.7)
        pool = p.ellipse(xx + 0.5, yb + 1.5 * s, (w + 3) * s * 0.9, 1.8 * s)
        p.paint(pool, RIVER, 0.7 + (n2 - 0.5) * 0.3)
        p.flat(pool & (n2 > 0.5), FOAM[0], 0.7)
        for k, a in ((5, 0.2), (3.5, 0.28), (2, 0.38)):
            p.light(p.ellipse(xx + 0.5, yb + 1.5 * s, k * 1.6 * s, k * 0.8 * s), MIST, a)


def lantern_reflections(p):
    """Warm streaks on the water under each lantern that stands near it."""
    for (x, y, big) in p.lanterns:
        x, y = int(round(x)), int(round(y))
        L = 9 if big else 6
        for k in range(1, L + 1):
            yy = y + k
            if 0 <= yy < p.h:
                for dx in (0, -1, 1) if big else (0,):
                    xx = x + dx
                    if 0 <= xx < p.w and p.water[yy, xx] and (yy + xx) % 2 == 0:
                        p.put(xx, yy, GLOW, 0.55 * (1 - k / (L + 1)))


# ---------------------------------------------------------------- structures
def roof_tiles(p, m, pal, lit_side="left", s=1):
    if not m.any():
        return
    ys, xs = np.nonzero(m)
    y0, y1 = ys.min(), ys.max()
    x0, x1 = xs.min(), xs.max()
    t = np.clip((p.YY - y0) / max(1, y1 - y0), 0, 1)
    xr = np.clip((p.XX - x0) / max(1, x1 - x0), 0, 1)
    v = 0.84 - t * 0.5 + (0.2 if lit_side == "left" else -0.2) * (0.5 - xr)
    v += np.where((p.YY // s) % 2 == 0, 0.07, -0.07)
    if s > 1:
        v += np.where((p.XX // s) % 2 == 0, 0.03, -0.03)
    p.paint(m, pal, v, sharp=1.5)
    p.flat(m & ~shift(m, 0, -1), pal[0])
    p.flat(m & ~shift(m, 0, 1), pal[-1], 0.7)


def hall(p, cx, by, w, wall_h, roof_h, roof=ROOF, wall=WALL, windows=2, eaves=2, ridge=True, s=1, lit=True):
    """A hall seen from in front and slightly above: walls with warm windows, a tiled roof with upturned eaves."""
    w, wall_h, roof_h, eaves = w * s, wall_h * s, roof_h * s, eaves * s
    x0, x1 = int(cx - w / 2), int(cx + w / 2)
    wy0 = by - wall_h
    wm = p.rect(x0, wy0, x1, by)
    p.paint(wm, wall, 0.55 + (0.5 - (p.XX - x0) / max(1, w)) * 0.3)
    p.flat(p.rect(x0, by, x1, by), STONE[2])
    p.flat(p.rect(x0, by + 1, x1 + 1, by + s), INK, 0.35)
    if windows > 0 and wall_h >= 3:
        step = (w - 2 * s) / (windows + 1)
        for i in range(windows):
            wx = int(x0 + s + step * (i + 1))
            wy = wy0 + max(1, wall_h // 2)
            c = WINDOW if lit else STONE[1]
            p.put(wx, wy, c)
            if s > 1:
                p.put(wx + 1, wy, c)
                p.put(wx, wy + 1, c)
                p.put(wx + 1, wy + 1, c)
            elif wall_h >= 5:
                p.put(wx, wy + 1, c)
    ry0 = wy0 - roof_h
    rm = p.poly([(x0 - eaves, wy0), (x0 + w * 0.22, ry0), (x1 - w * 0.22, ry0), (x1 + eaves, wy0)])
    roof_tiles(p, rm, roof, s=s)
    if ridge:
        p.flat(p.rect(int(x0 + w * 0.22), ry0, int(x1 - w * 0.22), ry0), roof[-1])
    p.put(x0 - eaves, wy0 - 1, roof[-2])
    p.put(x1 + eaves, wy0 - 1, roof[-2])
    if s > 1:
        p.put(x0 - eaves + 1, wy0 - 2, roof[-2])
        p.put(x1 + eaves - 1, wy0 - 2, roof[-2])
    return p.rect(x0 - eaves, ry0 - 1, x1 + eaves, by)


def pagoda(p, cx, by, tiers, w0, roof=ROOF, wall=LACQUER, tier_h=4, shrink=0.8, s=1):
    """A tiered pagoda: each tier a wall band under a roof wider than it, narrowing upward, a gold spire on top."""
    w = float(w0) * s
    y = by
    for i in range(tiers):
        x0, x1 = int(round(cx - w / 2)), int(round(cx + w / 2))
        wall_h = max(2, tier_h - 1) * s
        wm = p.rect(x0, y - wall_h, x1, y)
        p.paint(wm, wall, 0.5 + (0.5 - (p.XX - x0) / max(1, w)) * 0.4)
        if w >= 5 * s:
            p.put(int(cx), y - wall_h + s, WINDOW)
            if s > 1:
                p.put(int(cx) + 1, y - wall_h + s, WINDOW)
            if w >= 9 * s:
                p.put(int(cx) - 2 * s, y - wall_h + s, WINDOW)
                p.put(int(cx) + 2 * s, y - wall_h + s, WINDOW)
        ry = y - wall_h
        rm = p.poly([(x0 - 2 * s, ry), (x0 + w * 0.25, ry - 2 * s), (x1 - w * 0.25, ry - 2 * s), (x1 + 2 * s, ry)])
        roof_tiles(p, rm, roof, s=s)
        p.put(x0 - 2 * s, ry - 1, roof[-2])
        p.put(x1 + 2 * s, ry - 1, roof[-2])
        y = ry - 2 * s
        w *= shrink
    for k in range(3 * s):
        p.put(int(cx), y - k, GOLD[4 + (k == 3 * s - 1)])
    return p.rect(int(cx - w0 * s / 2) - 2 * s, y - 3 * s, int(cx + w0 * s / 2) + 2 * s, by)


def gate(p, cx, by, w, s=1, roof=ROOF):
    """A gatehouse: two lacquer posts, a dark opening and a tiled roof."""
    w = w * s
    x0, x1 = int(cx - w / 2), int(cx + w / 2)
    p.flat(p.rect(x0, by - 3 * s, x0 + s - 1, by), LACQUER[3])
    p.flat(p.rect(x1 - s + 1, by - 3 * s, x1, by), LACQUER[3])
    p.flat(p.rect(x0 + s, by - 3 * s, x1 - s, by), INK, 0.85)
    rm = p.poly([(x0 - 2 * s, by - 3 * s), (x0 + w * 0.2, by - 6 * s), (x1 - w * 0.2, by - 6 * s), (x1 + 2 * s, by - 3 * s)])
    roof_tiles(p, rm, roof, s=s)
    p.put(x0 - 2 * s, by - 3 * s - 1, roof[-2])
    p.put(x1 + 2 * s, by - 3 * s - 1, roof[-2])


def wall_line(p, pts, c_top, c_face, h=2):
    top = p.line(pts, 1)
    face = np.zeros_like(top)
    for k in range(1, h + 1):
        face |= shift(top, 0, k)
    p.flat(face & ~top, c_face)
    p.flat(top, c_top)


def fence(p, pts, s=1):
    m = p.line(pts, 1)
    p.flat(m, WOOD[4], 0.9)
    p.flat(m & ((p.XX + p.YY) % (3 * s) == 0), WOOD[1])
    p.flat(shift(m, 0, 1) & ((p.XX + p.YY) % (3 * s) == 0), WOOD[1], 0.8)


def awning(p, x, y, w, s=1):
    """A striped market awning with two posts."""
    for i in range(int(w * s)):
        c = AWNING_R if (i // s) % 2 == 0 else AWNING_W
        p.put(int(x + i), int(y), c)
        if s > 1:
            p.put(int(x + i), int(y) - 1, c)
    p.put(int(x), int(y) + s, WOOD[2])
    p.put(int(x + w * s - 1), int(y) + s, WOOD[2])


def stilt_hut(p, cx, by, w=6, s=1, lit=True):
    w = w * s
    x0, x1 = int(cx - w // 2), int(cx + w // 2)
    for px in (x0 + s, x1 - s):
        p.put(px, by, WOOD[1])
        p.put(px, by + s, WOOD[0])
    p.paint(p.rect(x0, by - 3 * s, x1, by - s), WOOD, 0.35 + (0.5 - (p.XX - x0) / max(1, w)) * 0.3)
    if lit:
        p.put(int(cx), by - 2 * s, WINDOW)
        if s > 1:
            p.put(int(cx) + 1, by - 2 * s, WINDOW)
    rm = p.poly([(x0 - s, by - 3 * s), (int(cx), by - 7 * s), (x1 + s, by - 3 * s)])
    p.paint(rm, THATCH, 0.7 - (p.YY - (by - 7 * s)) / (5.0 * s) * 0.4 + (0.5 - (p.XX - x0) / max(1, w)) * 0.3)
    p.flat(rm & ~shift(rm, 0, -1), THATCH[0], 0.7)


def boardwalk(p, pts, s=1):
    m = p.line(pts, s)
    p.flat(m, WOOD[3])
    p.flat(m & ((p.XX + p.YY) % (2 * s) == 0), WOOD[2])


def bridge_stone(p, x0, y0, x1, y1, s=1, pal=STONE_WARM):
    """A stone arch bridge between two banks: a lit walkway, a dark underside, arches on the water."""
    n = max(2, int(math.hypot(x1 - x0, y1 - y0)))
    for i in range(n + 1):
        t = i / n
        a = math.sin(t * math.pi) * 2.6 * s
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t - a
        for k in range(s + 1):
            p.px(x, y - k, pal[5] if k == s else pal[4])
        p.px(x, y + 1, pal[2])
        p.px(x, y + 2, pal[1] if 0.15 < t < 0.85 else pal[0])
        if 0.28 < t < 0.42 or 0.58 < t < 0.72:
            p.px(x, y + 3, INK, 0.8)
            if s > 1:
                p.px(x, y + 4, INK, 0.6)
    for (x, y) in ((x0, y0), (x1, y1)):
        for k in range(2 * s):
            p.px(x, y + 1 + k, pal[1])


def bridge_wood(p, x0, y0, x1, y1, s=1):
    n = max(2, int(math.hypot(x1 - x0, y1 - y0)))
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t - math.sin(t * math.pi) * 1.2 * s
        p.px(x, y, WOOD[4] if i % 2 else WOOD[3])
        p.px(x, y + 1, WOOD[1])
        if s > 1:
            p.px(x, y - 1, WOOD[5] if i % 2 else WOOD[4])
    for f in (0.15, 0.5, 0.85):
        x = x0 + (x1 - x0) * f
        y = y0 + (y1 - y0) * f - math.sin(f * math.pi) * 1.2 * s
        for k in range(1, 2 * s + 1):
            p.px(x, y - k, WOOD[2])
        p.px(x, y - 2 * s - 1, WOOD[5])


def rope_bridge(p, x0, y0, x1, y1, s=1):
    n = max(2, int(math.hypot(x1 - x0, y1 - y0)))
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t + math.sin(t * math.pi) * 3 * s
        p.px(x, y, WOOD[3] if i % 2 else WOOD[1])
        p.px(x, y - 2 * s, WOOD[5], 0.8)
    for (x, y) in ((x0, y0), (x1, y1)):
        for k in range(3 * s):
            p.px(x, y - k, WOOD[2])


def boat(p, x, y, sail=True, flip=False, s=1):
    hull = [(x - 3 * s, y), (x + 3 * s, y), (x + 2 * s, y + s), (x - 2 * s, y + s)]
    p.flat(p.poly(hull), HULL[1])
    p.px(x - 3 * s, y, HULL[2])
    p.px(x + 3 * s, y, HULL[2])
    if s > 1:
        p.flat(p.poly([(x - 2 * s, y - 1), (x + 2 * s, y - 1), (x + 2 * s, y), (x - 2 * s, y)]), HULL[2])
    if sail:
        sx = x + (s if flip else 0)
        for k in range(1, 5 * s):
            p.px(sx, y - k, WOOD[1])
        d = -1 if flip else 1
        sm = p.poly([(sx + d, y - s), (sx + d, y - 4 * s), (sx + 3 * s * d, y - 2 * s)])
        p.paint(sm, SAIL, 0.6 + (p.YY - (y - 4 * s)) / (4.0 * s) * 0.4)
    p.px(x - 4 * s, y + s, RIVER[6], 0.8)
    p.px(x + 4 * s, y + s, RIVER[6], 0.8)


def lantern(p, x, y, big=False, s=1):
    """A lit lantern: a warm core and a stepped glow; remembered for the water's reflections."""
    x, y = int(round(x)), int(round(y))
    r1, r2 = (3.4 if big else 2.5) * s, (1.9 if big else 1.4) * s
    p.light(p.circle(x + 0.5, y + 0.5, r1), GLOW, 0.16)
    p.light(p.circle(x + 0.5, y + 0.5, r2), GLOW, 0.3)
    p.put(x, y, LANTERN)
    if big or s > 1:
        p.put(x, y - 1, WINDOW)
    if s > 1:
        p.put(x + 1, y, LANTERN)
        p.put(x + 1, y - 1, WINDOW)
        p.put(x, y + 1, hexc("#c2472f"))
        p.put(x + 1, y + 1, hexc("#c2472f"))
    p.lanterns.append((x, y, big))


def hanging_lantern(p, x, y, s=1, size=3):
    """A big hanging lantern (the foreground kind): a cord, a red-gold body, a glow."""
    sz = size * s
    for k in range(3 * s):
        p.put(x, y - sz - k, INK)
    body = p.ellipse(x + 0.5, y + 0.5, sz * 0.8, sz)
    p.light(p.ellipse(x + 0.5, y + 0.5, sz * 2.2, sz * 2.2), GLOW, 0.14)
    p.light(p.ellipse(x + 0.5, y + 0.5, sz * 1.5, sz * 1.5), GLOW, 0.24)
    p.paint(body, ramp("#8c2a12", "#d0561c", "#f39a2c", "#ffd66a", "#fff1c0"), 0.55 + (0.5 - (p.XX - x) / (sz * 1.6)) * 0.4 - ((p.YY - y) / (sz * 2)) * 0.3)
    p.flat(body & ~shift(body, 0, -1), hexc("#6a1d0e"), 0.8)
    for k in range(1, 2 * s + 1):
        p.put(x, y + sz + k, GOLD[4])
    p.lanterns.append((x, y + sz, True))


def campfire(p, x, y, s=1):
    p.light(p.circle(x + 0.5, y + 0.5, 4 * s), FIRE[2], 0.18)
    p.light(p.circle(x + 0.5, y + 0.5, 2.2 * s), FIRE[2], 0.3)
    p.put(x, y, FIRE[3])
    p.put(x, y - 1, FIRE[2])
    p.put(x - 1, y, FIRE[1])
    p.put(x + 1, y, FIRE[1])
    if s > 1:
        p.put(x, y - 2, FIRE[2])
        p.put(x + 1, y - 1, FIRE[3])
    p.put(x - 2 * s, y + 1, WOOD[1])
    p.put(x + 2 * s, y + 1, WOOD[1])


def tent(p, cx, by, w=6, s=1):
    w = w * s
    m = p.poly([(cx - w / 2, by), (cx, by - 4 * s), (cx + w / 2, by)])
    p.paint(m, ramp("#4a3a2a", "#6f5a40", "#96805e", "#b9a37c"), 0.6 + (0.5 - (p.XX - cx + w / 2) / w) * 0.5)
    p.flat(m & ~shift(m, 0, -1), hexc("#2c2118"), 0.8)
    p.put(int(cx), by - 4 * s, WOOD[5])


def watchtower(p, cx, by, s=1):
    for dx in (-2 * s, 2 * s):
        for k in range(7 * s):
            p.put(int(cx + dx), by - k, WOOD[1 + (k % 2)])
    p.flat(p.rect(cx - 3 * s, by - 8 * s, cx + 3 * s, by - 7 * s), WOOD[3])
    rm = p.poly([(cx - 4 * s, by - 8 * s), (cx, by - 11 * s), (cx + 4 * s, by - 8 * s)])
    p.paint(rm, THATCH, 0.6 - (p.YY - (by - 11 * s)) / (3.0 * s) * 0.3)
    lantern(p, cx, by - 9 * s + 1, s=s)


def cart(p, x, y, s=1):
    for k in range(4 * s):
        p.put(int(x + k), int(y), WOOD[4] if k < 3 * s else WOOD[2])
    p.put(int(x), int(y) + s, WOOD[1])
    p.put(int(x + 3 * s), int(y) + s, WOOD[1])
    p.put(int(x + s), int(y) - s, hexc("#c9b58a"))
    p.put(int(x + 2 * s), int(y) - s, hexc("#c9b58a"))
    # the ox
    p.put(int(x - 2 * s), int(y), hexc("#5a4030"))
    p.put(int(x - 3 * s), int(y), hexc("#7a5a44"))
    p.put(int(x - 3 * s), int(y) - s, hexc("#7a5a44"))


def haystack(p, x, y, s=1):
    m = p.ellipse(x + 0.5, y, 2.2 * s, 2.6 * s) & (p.YY <= y)
    p.paint(m, THATCH, 0.65 + (0.5 - (p.XX - x) / (4.0 * s)) * 0.5 - (p.YY - y + 2.6 * s) / (2.6 * s) * 0.3)
    p.flat(m & ~shift(m, 0, -1), THATCH[0], 0.7)


def farmstead(p, cx, by, s=1, seed=0):
    """Two thatch halls, a fence, a haystack and a lantern."""
    hall(p, cx - 6 * s, by, 9, 3, 3, roof=THATCH, wall=WOOD, windows=1, eaves=1, s=s)
    hall(p, cx + 6 * s, by - 3 * s, 7, 3, 3, roof=THATCH, wall=WOOD, windows=1, eaves=1, s=s)
    haystack(p, cx + 11 * s, by + 2 * s, s)
    fence(p, [(cx - 13 * s, by + 3 * s), (cx + 13 * s, by + 3 * s), (cx + 14 * s, by - 4 * s)], s)
    lantern(p, cx - 1, by - 1, s=s)


def watermill(p, cx, by, s=1):
    hall(p, cx, by, 9, 4, 3, roof=THATCH, wall=WOOD, windows=1, eaves=1, s=s)
    wx = cx + 6 * s
    wheel = p.circle(wx + 0.5, by - 1.5 * s, 3 * s)
    p.flat(wheel & ~erode(wheel), WOOD[2])
    p.flat(wheel & ~erode(wheel) & ((p.XX + p.YY) % (2 * s) == 0), WOOD[5])
    p.flat(p.line([(wx, by - 4.5 * s), (wx, by + 1.5 * s)], 1), WOOD[3])
    p.flat(p.line([(wx - 3 * s, by - 1.5 * s), (wx + 3 * s, by - 1.5 * s)], 1), WOOD[3])
    p.flat(p.rect(wx - 2 * s, by + s, wx + 3 * s, by + 2 * s), FOAM[1], 0.8)


def shrine(p, cx, by, s=1):
    """A wayside shrine: two lacquer posts and a lintel, a lantern before it."""
    for dx in (-2 * s, 2 * s):
        for k in range(4 * s):
            p.put(int(cx + dx), by - k, LACQUER[3])
    p.flat(p.rect(cx - 3 * s, by - 4 * s, cx + 3 * s, by - 4 * s), LACQUER[4])
    p.flat(p.rect(cx - 2 * s, by - 5 * s, cx + 2 * s, by - 5 * s), ROOF[2])
    lantern(p, cx, by - 1, s=s)


def stones(p, m, seed, pal=STONE, density=0.5, s=1):
    g = rng("stones", seed)
    ys, xs = np.nonzero(m)
    if len(xs) == 0:
        return
    n = int(len(xs) * density / 8.0)
    for i in g.integers(0, len(xs), n):
        x, y = int(xs[i]), int(ys[i])
        p.put(x, y, pal[4])
        p.put(x + s, y, pal[2])
        p.put(x, y + s, pal[1], 0.8)


def crane(p, x, y, s=1):
    p.put(x, y, CLOTH_WHITE[5])
    p.put(x - s, y + s, CLOTH_WHITE[4])
    p.put(x + s, y + s, CLOTH_WHITE[4])
    p.put(x - 2 * s, y + s, CLOTH_WHITE[3], 0.7)
    p.put(x + 2 * s, y + s, CLOTH_WHITE[3], 0.7)
    if s > 1:
        p.put(x, y + 1, CLOTH_WHITE[5])
        p.put(x - 1, y + 1, hexc("#e45858"))


def cloud_puff(p, cx, cy, rx, ry, seed, pal=CLOUD):
    g = rng("cloud", seed)
    m = p.zeros()
    for _ in range(int(3 + rx // 4)):
        ox, oy = g.uniform(-rx * 0.7, rx * 0.7), g.uniform(-ry * 0.5, ry * 0.3)
        m |= p.ellipse(cx + ox, cy + oy, g.uniform(rx * 0.35, rx * 0.6), g.uniform(ry * 0.5, ry * 0.9))
    m |= p.ellipse(cx, cy + ry * 0.3, rx, ry * 0.55)
    d = ((p.XX - cx) / rx) * 0.5 + ((p.YY - cy) / ry) * 0.9
    p.paint(m, pal, 0.75 - d * 0.5)
    p.flat(m & ~shift(m, 0, -1), pal[0], 0.7)
    return m


def patchy(p, m, col, a, cell, seed, cover=0.5):
    """Wisps of mist over m: translucent col where a noise field is high, thinning toward the mask's top and bottom."""
    if not m.any():
        return
    ys = np.nonzero(m.any(1))[0]
    y0, y1 = ys.min(), ys.max()
    env = np.sin(np.pi * np.clip((p.YY - y0) / max(1, y1 - y0), 0, 1)) ** 0.6
    n2 = p.noise(cell, ("patchy", seed), 2) * env
    for k, sa in ((0.0, 0.45), (0.12, 0.35), (0.24, 0.2)):
        p.light(m & (n2 > 1 - cover + k), col, a * sa)


def road(p, pts, w=2, pal=ROAD, per=1.5):
    m = p.band(catmull(pts, per), [w, w])
    n2 = p.noise(3, "road")
    p.paint(m, pal, 0.5 + (n2 - 0.5) * 0.5)
    p.flat(m & ~shift(m, 0, -1), pal[0], 0.5)
    return m


def dock(p, x0, y, length, s=1, pal=WOOD, vertical=False):
    for i in range(length * s):
        if vertical:
            p.put(x0, y - i, pal[3] if (i // s) % 3 else pal[2])
            if s > 1:
                p.put(x0 + 1, y - i, pal[2] if (i // s) % 3 else pal[1])
        else:
            p.put(x0 + i, y, pal[3] if (i // s) % 3 else pal[2])
            if s > 1:
                p.put(x0 + i, y + 1, pal[2] if (i // s) % 3 else pal[1])
    if vertical:
        p.put(x0, y - length * s, pal[0])
        p.put(x0 + s, y - length * s + 2 * s, pal[0])
    else:
        for px in (x0 + s, x0 + length * s - 2 * s):
            p.put(px, y + s + (s - 1), pal[0])


def lotus(p, water, cx, cy, rx, ry, seed, n=14):
    g = rng("lotus", seed)
    for i in range(n):
        x = int(cx + g.uniform(-rx, rx))
        y = int(cy + g.uniform(-ry, ry))
        if 0 <= x < p.w and 0 <= y < p.h and water[y, x]:
            p.put(x, y, LEAF[4])
            if i % 4 == 0:
                p.put(x, y - 1, hexc("#f2b8c6"))


# ---------------------------------------------------------------- the scenes: one per region, centred on its anchor
# Each takes the painter, the anchor (cx, cy), the scale s (1 on the map, 2 in the vignette) and the water mask.

def sc_stoneford(p, cx, cy, s, water):
    """A river town round its stone bridge: rows of blue-tiled roofs on both banks, market awnings, lanterns."""
    cob = p.ellipse(cx, cy + 9 * s, 26 * s, 8 * s) & ~water
    p.paint(cob, ramp("#6f6a5a", "#8a8474", "#a8a28f", "#c6c0aa"), 0.55 + (p.noise(3 * s, "cobbles") - 0.5) * 0.5)
    cob2 = p.ellipse(cx - 4 * s, cy - 11 * s, 18 * s, 6 * s) & ~water
    p.paint(cob2, ramp("#6f6a5a", "#8a8474", "#a8a28f", "#c6c0aa"), 0.5 + (p.noise(3 * s, "cobbles") - 0.5) * 0.5)
    # the north bank: the county hall, houses, a gate tower
    hall(p, cx - 16 * s, cy - 12 * s, 10, 4, 4, roof=ROOF_BLUE, windows=2, s=s)
    hall(p, cx - 5 * s, cy - 14 * s, 9, 3, 3, roof=ROOF_GREY, windows=2, s=s)
    hall(p, cx + 6 * s, cy - 12 * s, 12, 4, 4, roof=ROOF_BLUE, windows=3, s=s)
    hall(p, cx + 17 * s, cy - 10 * s, 8, 3, 3, roof=ROOF_GREY, windows=1, s=s)
    pagoda(p, cx - 10 * s, cy - 6 * s, 2, 7, roof=ROOF_BLUE, wall=LACQUER, tier_h=3, s=s)
    gate(p, cx + 1 * s, cy - 8 * s, 7, s=s, roof=ROOF_BLUE)
    # the bridge over the river, from the north bank down to the south
    bridge_stone(p, cx - 1 * s, cy - 8 * s, cx + 4 * s, cy + 8 * s, s=s)
    # the ford: stepping stones east of the bridge
    stones(p, water & p.rect(cx + 8 * s, cy - 6 * s, cx + 18 * s, cy + 6 * s) & ((p.XX + p.YY) % (3 * s) == 0), "ford", pal=STONE, density=3.0, s=s)
    # the south bank: the market street
    hall(p, cx - 18 * s, cy + 12 * s, 10, 4, 3, roof=ROOF_GREY, windows=2, s=s)
    hall(p, cx - 8 * s, cy + 14 * s, 9, 4, 4, roof=ROOF_BLUE, windows=2, s=s)
    hall(p, cx + 4 * s, cy + 15 * s, 11, 4, 4, roof=ROOF, windows=3, s=s)
    hall(p, cx + 15 * s, cy + 13 * s, 9, 3, 3, roof=ROOF_GREY, windows=2, s=s)
    hall(p, cx + 24 * s, cy + 10 * s, 7, 3, 3, roof=ROOF_BLUE, windows=1, s=s)
    hall(p, cx - 2 * s, cy + 22 * s, 8, 3, 3, roof=ROOF_GREY, windows=1, s=s)
    hall(p, cx + 10 * s, cy + 23 * s, 9, 3, 3, roof=ROOF_BLUE, windows=2, s=s)
    for i, ax in enumerate((cx - 12 * s, cx - 4 * s, cx + 8 * s, cx + 18 * s)):
        awning(p, ax, cy + 7 * s + (i % 2) * s, 5, s)
    for lx, ly in ((cx - 12, cy - 9), (cx + 10, cy - 9), (cx - 3, cy + 6), (cx + 6, cy + 6), (cx - 14, cy + 15), (cx + 20, cy + 15), (cx + 3, cy + 18), (cx - 6, cy + 24), (cx + 16, cy + 24), (cx + 26, cy - 8)):
        lantern(p, cx + (lx - cx) * s, cy + (ly - cy) * s, s=s)
    clump(p, cx + 26 * s, cy - 16 * s, 3, 1.5 * s, 2.2 * s, PINE, "sf-pines")
    clump(p, cx - 24 * s, cy + 18 * s, 3, 1.5 * s, 2.4 * s, OLIVE, "sf-trees")


def sc_lotus_ferry(p, cx, cy, s, water):
    """A fishing village on the south bank: thatch huts, two docks, boats, nets drying, lotus pads."""
    hall(p, cx - 12 * s, cy + 6 * s, 8, 3, 3, roof=THATCH, wall=WOOD, windows=1, s=s)
    hall(p, cx - 2 * s, cy + 9 * s, 9, 3, 3, roof=THATCH, wall=WOOD, windows=1, s=s)
    hall(p, cx + 9 * s, cy + 6 * s, 8, 3, 3, roof=THATCH, wall=WOOD, windows=1, s=s)
    hall(p, cx + 18 * s, cy + 10 * s, 7, 3, 3, roof=THATCH, wall=WOOD, windows=1, s=s)
    hall(p, cx - 4 * s, cy + 17 * s, 10, 3, 3, roof=ROOF_GREY, wall=WALL, windows=2, s=s)
    hall(p, cx + 8 * s, cy + 18 * s, 8, 3, 3, roof=THATCH, wall=WOOD, windows=1, s=s)
    dock(p, cx - 6 * s, cy - 1 * s, 8, s=s, vertical=True)
    dock(p, cx + 6 * s, cy - 2 * s, 6, s=s, vertical=True)
    boat(p, cx - 2 * s, cy - 8 * s, sail=True, s=s)
    boat(p, cx + 12 * s, cy - 11 * s, sail=False, s=s)
    boat(p, cx + 22 * s, cy - 5 * s, sail=True, flip=True, s=s)
    lotus(p, water, cx - 14 * s, cy - 8 * s, 10 * s, 5 * s, "lf-lotus", n=16)
    # nets drying on posts
    for k in range(3):
        x = cx + 14 * s + k * 3 * s
        for j in range(3 * s):
            p.put(x, cy + 2 * s - j, WOOD[2])
        p.flat(p.line([(x, cy - 1 * s), (x + 3 * s, cy - 1 * s)], 1), hexc("#8fa090"), 0.8)
    for lx, ly in ((cx - 8, cy + 7), (cx + 6, cy + 8), (cx - 6, cy - 6), (cx + 6, cy - 6), (cx + 2, cy + 18), (cx + 20, cy + 11)):
        lantern(p, cx + (lx - cx) * s, cy + (ly - cy) * s, s=s)
    clump(p, cx + 24 * s, cy + 18 * s, 4, 1.6 * s, 2.6 * s, OLIVE, "lf-trees")


def sc_willow_path(p, cx, cy, s, water):
    """Willows along the river road, a wooden footbridge, a way-shrine."""
    g = rng("willows")
    for i in range(6):
        x = cx - 22 * s + i * 8 * s + g.integers(-2, 3) * s
        y = cy + 4 * s + g.integers(-2, 3) * s - (i % 2) * 3 * s
        tree(p, x, y, 3.2 * s, WILLOW)
        for k in range(3):
            p.put(int(x - 2 * s + k * 2 * s), int(y + 3 * s + (k % 2) * s), WILLOW[3], 0.9)
            p.put(int(x - 2 * s + k * 2 * s), int(y + 4 * s + (k % 2) * s), WILLOW[2], 0.8)
    for i in range(3):
        x = cx - 14 * s + i * 12 * s
        y = cy - 13 * s + (i % 2) * 2 * s
        tree(p, x, y, 2.8 * s, WILLOW)
    bridge_wood(p, cx + 2 * s, cy - 11 * s, cx + 6 * s, cy + 1 * s, s=s)
    shrine(p, cx - 6 * s, cy + 9 * s, s=s)
    boat(p, cx - 12 * s, cy - 6 * s, sail=True, flip=True, s=s)
    lantern(p, cx + 8 * s, cy + 3 * s, s=s)
    lantern(p, cx + 4 * s, cy - 12 * s, s=s)


def sc_caravan_road(p, cx, cy, s, water):
    """The road along the south bank: a cart and its ox, a milestone, a farm and its orchard."""
    cart(p, cx - 2 * s, cy + 1 * s, s)
    p.put(int(cx + 6 * s), int(cy + 1 * s), STONE[5])
    p.put(int(cx + 6 * s), int(cy), STONE[4])
    farmstead(p, cx + 16 * s, cy + 12 * s, s, "cr-farm")
    orchard(p, cx - 12 * s, cy + 12 * s, 4, 2, 4, "cr-orchard", s=s)
    stones(p, p.ellipse(cx - 18 * s, cy - 4 * s, 6 * s, 2 * s), "cr-stones", pal=STONE, density=2.5, s=s)
    lantern(p, cx + 7 * s, cy - 1 * s, s=s)
    boat(p, cx - 10 * s, cy - 10 * s, sail=False, s=s)


def sc_deepwater_bend(p, cx, cy, s, water):
    """The wide dark water where the river turns: the serpent's rings, a fisher's shelter, reeds."""
    deep = p.ellipse(cx + 2 * s, cy + 2 * s, 16 * s, 10 * s) & water
    p.paint(deep, RIVER, 0.22 + (p.noise(4 * s, "deep") - 0.5) * 0.2)
    for r_ in (3, 6, 9):
        ring = p.circle(cx + 8.5 * s, cy + 3.5 * s, r_ * s) & ~p.circle(cx + 8.5 * s, cy + 3.5 * s, r_ * s - 1) & water
        p.flat(ring & ((p.XX + p.YY) % 2 == 0), RIVER[6], 0.7)
    boat(p, cx - 6 * s, cy - 2 * s, sail=False, s=s)
    hall(p, cx - 12 * s, cy + 14 * s, 7, 2, 3, roof=THATCH, wall=WOOD, windows=1, eaves=1, s=s)
    dock(p, cx - 8 * s, cy + 11 * s, 5, s=s, vertical=True)
    reeds(p, (dilate(dilate(water)) & ~water) & p.rect(cx - 20 * s, cy + 4 * s, cx + 24 * s, cy + 18 * s) & ((p.XX * 5 + p.YY * 3) % (5 * s) == 0), "bend-reeds", s)
    lantern(p, cx - 12 * s, cy + 13 * s, s=s)


def sc_drowned_shrine(p, cx, cy, s, water):
    """A sunken temple in the flooded bay: three roofs and a pagoda top above the water, pillars, lanterns, lotus."""
    ruin = p.rect(cx - 12 * s, cy - 1 * s, cx + 12 * s, cy + 5 * s) & water
    p.paint(ruin, STONE_DARK, 0.5 + (p.noise(4 * s, "ruin") - 0.5) * 0.3)
    hall(p, cx - 11 * s, cy + 3 * s, 7, 1, 3, roof=PATINA, wall=STONE_DARK, windows=0, eaves=1, s=s)
    hall(p, cx + 11 * s, cy + 3 * s, 7, 1, 3, roof=PATINA, wall=STONE_DARK, windows=0, eaves=1, s=s)
    hall(p, cx, cy + 1 * s, 16, 2, 5, roof=PATINA, wall=STONE_DARK, windows=1, eaves=2, s=s)
    pagoda(p, cx, cy - 6 * s, 1, 7, roof=PATINA, wall=STONE_DARK, tier_h=3, s=s)
    for px in (cx - 17 * s, cx + 17 * s, cx - 6 * s, cx + 6 * s):
        for k in range(3 * s):
            p.put(int(px), int(cy + 4 * s - k), STONE[3 + (k % 2)])
    lantern(p, cx, cy - 11 * s, big=True, s=s)
    lantern(p, cx - 17 * s, cy + 1 * s, s=s)
    lantern(p, cx + 17 * s, cy + 1 * s, s=s)
    lotus(p, water, cx, cy + 4 * s, 22 * s, 9 * s, "ds-lotus", n=14)
    reeds(p, (dilate(dilate(water)) & ~water) & ((p.XX * 5 + p.YY * 3) % (7 * s) == 0), "shrine-reeds", s)
    boardwalk(p, [(cx + 8 * s, cy - 14 * s), (cx + 2 * s, cy - 9 * s)], s)


def sc_whitewater_gorge(p, cx, cy, s, water):
    """The gorge: cliffs either side of the white water, a rope bridge across, a fall from the east wall."""
    wl = p.poly([(cx - 34 * s, cy - 26 * s), (cx - 8 * s, cy - 16 * s), (cx - 4 * s, cy + 10 * s), (cx - 24 * s, cy + 24 * s), (cx - 44 * s, cy + 8 * s)]) & ~water
    wr = p.poly([(cx + 6 * s, cy - 28 * s), (cx + 30 * s, cy - 18 * s), (cx + 34 * s, cy + 10 * s), (cx + 14 * s, cy + 22 * s), (cx + 9 * s, cy + 2 * s)]) & ~water & ~dilate(water)
    cliff(p, wl, "gorge-l", pal=CLIFF, lit=0.12, s=s)
    cliff(p, wr, "gorge-r", pal=CLIFF, lit=-0.15, s=s)
    forest(p, (wl | wr) & (p.noise(4 * s, "gorge-trees") > 0.6), PINE, "gorge-trees", density=0.5, rmin=1.0 * s, rmax=1.8 * s)
    rapids(p, water & p.ellipse(cx, cy, 30 * s, 30 * s), "gorge", s)
    waterfall(p, int(cx + 12 * s), int(cy - 16 * s), int(cy - 4 * s), w=2 * s, seed=3, s=s, tiers=1)
    p.flat(p.rect(cx + 10 * s, cy - 20 * s, cx + 14 * s, cy - 17 * s), INK, 0.85)      # the waterfall cave's mouth
    rope_bridge(p, cx - 8 * s, cy - 2 * s, cx + 8 * s, cy - 6 * s, s=s)


def sc_crane_cliffs(p, cx, cy, s, water):
    """Sheer cliffs with ledges, cranes wheeling, a hermit's hut on a ledge."""
    for i, (dx, dy) in enumerate(((-8, -12), (6, -16), (14, -6), (-16, 0), (2, 4))):
        crane(p, int(cx + dx * s), int(cy + dy * s), s)
    ledge = p.poly([(cx - 10 * s, cy + 6 * s), (cx + 8 * s, cy + 4 * s), (cx + 10 * s, cy + 8 * s), (cx - 10 * s, cy + 9 * s)])
    p.paint(ledge, CLIFF, 0.75 - (p.XX - cx) / (30.0 * s))
    hall(p, cx - 2 * s, cy + 5 * s, 6, 2, 2, roof=THATCH, wall=WOOD, windows=1, eaves=1, s=s)
    lantern(p, cx + 3 * s, cy + 5 * s, s=s)
    for k in range(6):
        p.put(int(cx - 12 * s + k * 2 * s), int(cy + 12 * s + k * s), STONE[5], 0.9)


def sc_mist_peak(p, cx, cy, s, water):
    """The tower's shoulder in mist; the forgotten monastery's ruin on the slope."""
    hall(p, cx + 4 * s, cy + 24 * s, 9, 3, 3, roof=ROOF_GREY, wall=STONE_DARK, windows=0, eaves=1, s=s, lit=False)
    hall(p, cx - 6 * s, cy + 27 * s, 6, 2, 2, roof=ROOF_GREY, wall=STONE_DARK, windows=0, eaves=1, s=s, lit=False)
    p.flat(p.rect(cx + 8 * s, cy + 21 * s, cx + 9 * s, cy + 23 * s), INK, 0.6)       # a broken roof
    patchy(p, p.ellipse(cx, cy + 4 * s, 26 * s, 8 * s), MIST, 0.6, 12 * s, "mp-mist", cover=0.6)
    lantern(p, cx + 1 * s, cy + 24 * s, s=s)


def sc_summit_ridge(p, cx, cy, s, water):
    """The frozen shrine on the snowy ridge, wind streaks."""
    hall(p, cx + 4 * s, cy + 8 * s, 7, 2, 3, roof=SNOW, wall=STONE, windows=0, eaves=1, s=s, lit=False)
    lantern(p, cx + 1 * s, cy + 7 * s, s=s)
    lantern(p, cx + 8 * s, cy + 7 * s, s=s)
    for k in range(4):
        p.flat(p.line([(cx - 16 * s + k * 3 * s, cy - 6 * s + k * 3 * s), (cx - 6 * s + k * 3 * s, cy - 7 * s + k * 3 * s)], 1), SNOW[3], 0.6)


def sc_cleansing_peak(p, cx, cy, s, water):
    """The pilgrim stair switchbacking up the pinnacle to the summit shrine, lanterns along it, a gate at its foot."""
    pts = [(cx + 6 * s, cy + 24 * s), (cx - 4 * s, cy + 16 * s), (cx + 5 * s, cy + 8 * s), (cx - 3 * s, cy + 1 * s), (cx + 2 * s, cy - 6 * s)]
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        n = int(max(abs(x1 - x0), abs(y1 - y0)))
        for k in range(n + 1):
            t = k / max(1, n)
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            if k % 2 == 0:
                p.px(x, y, STONE[5], 0.9)
                p.px(x + 1, y, STONE[3], 0.9)
    for (x, y) in pts[1:-1]:
        lantern(p, x, y - 1, s=s)
    hall(p, cx + 2 * s, cy - 8 * s, 7, 2, 3, roof=ROOF, wall=PLASTER, windows=1, eaves=1, s=s)
    lantern(p, cx + 2 * s, cy - 12 * s, s=s)
    gate(p, cx + 6 * s, cy + 26 * s, 5, s=s)


def sc_cloud_sect(p, cx, cy, s, water):
    """White halls on the pinnacle's ledge, a pagoda, clouds round its waist, a stair down."""
    ledge = p.poly([(cx - 18 * s, cy - 4 * s), (cx + 20 * s, cy - 6 * s), (cx + 22 * s, cy - 1 * s), (cx - 20 * s, cy + 1 * s)])
    p.paint(ledge, ROCK, 0.7 - (p.XX - cx) / (40.0 * s))
    hall(p, cx - 9 * s, cy - 6 * s, 12, 4, 4, roof=ROOF, wall=PLASTER, windows=2, s=s)
    hall(p, cx + 11 * s, cy - 4 * s, 10, 3, 3, roof=ROOF, wall=PLASTER, windows=2, s=s)
    hall(p, cx + 2 * s, cy - 14 * s, 8, 3, 3, roof=ROOF, wall=PLASTER, windows=1, s=s)
    pagoda(p, cx + 1 * s, cy - 11 * s, 4, 11, roof=ROOF, wall=PLASTER, tier_h=3, s=s)
    lantern(p, cx - 2 * s, cy - 7 * s, s=s)
    lantern(p, cx + 10 * s, cy - 5 * s, s=s)
    lantern(p, cx + 16 * s, cy - 8 * s, s=s)
    for k in range(8):
        p.put(int(cx - 12 * s + k * s), int(cy + 1 * s + k * 2 * s), STONE[5], 0.9)
        p.put(int(cx - 11 * s + k * s), int(cy + 1 * s + k * 2 * s), STONE[3], 0.9)
    cloud_puff(p, cx - 14 * s, cy + 10 * s, 12 * s, 5 * s, "cs-cloud-1")
    cloud_puff(p, cx + 16 * s, cy + 13 * s, 11 * s, 4 * s, "cs-cloud-2")
    cloud_puff(p, cx + 2 * s, cy + 18 * s, 9 * s, 4 * s, "cs-cloud-3")


def sc_crane_falls(p, cx, cy, s, water):
    """The river's source: a fall in three tiers off the cliffs into the pool, spray, a pavilion, cranes."""
    karst(p, cx - 12 * s, cy - 30 * s, cy + 4 * s, 14 * s, 121, rock=CLIFF, crown=0.4, skirt=0.2)
    karst(p, cx + 16 * s, cy - 26 * s, cy + 6 * s, 12 * s, 122, rock=CLIFF, crown=0.4, skirt=0.2)
    waterfall(p, int(cx + 1 * s), int(cy - 22 * s), int(cy + 8 * s), w=4 * s, seed=1, s=s, tiers=3)
    waterfall(p, int(cx + 9 * s), int(cy - 8 * s), int(cy + 8 * s), w=2 * s, seed=2, s=s, tiers=1)
    pool = p.ellipse(cx + 3 * s, cy + 12 * s, 11 * s, 4.5 * s)
    p.paint(pool, RIVER, 0.62 + (p.noise(4 * s, "pool") - 0.5) * 0.3)
    p.flat(pool & (p.noise(3 * s, "pool-foam") > 0.55), FOAM[0], 0.6)
    for k, a in ((8, 0.14), (5, 0.2)):
        p.light(p.ellipse(cx + 2 * s, cy + 8 * s, k * s, k * 0.6 * s), MIST, a)
    hall(p, cx + 15 * s, cy + 14 * s, 7, 2, 3, roof=ROOF, wall=LACQUER, windows=0, eaves=1, s=s)
    lantern(p, cx + 15 * s, cy + 13 * s, s=s)
    lantern(p, cx + 19 * s, cy + 15 * s, s=s)
    crane(p, int(cx - 7 * s), int(cy + 3 * s), s)
    crane(p, int(cx - 11 * s), int(cy - 2 * s), s)
    stones(p, p.ellipse(cx - 6 * s, cy + 15 * s, 6 * s, 2 * s), "cf-stones", pal=STONE, density=2.5, s=s)


def sc_bamboo_grove(p, cx, cy, s, water):
    """A bamboo sea with a glade at its heart: a small pavilion, ember-pepper bushes, a boar trail."""
    m = (p.ellipse(cx + 4 * s, cy + 4 * s, 34 * s, 22 * s) | p.ellipse(cx + 32 * s, cy - 6 * s, 26 * s, 18 * s)) & ~dilate(water)
    glade = p.ellipse(cx + 2 * s, cy + 2 * s, 8 * s, 4 * s)
    bamboo_field(p, m & ~glade, "grove", s)
    p.paint(glade, MEADOW, 0.6 + (p.noise(4 * s, "glade") - 0.5) * 0.3)
    hall(p, cx + 2 * s, cy + 2 * s, 5, 2, 2, roof=ROOF, wall=WOOD, windows=0, eaves=1, s=s)
    lantern(p, cx + 2 * s, cy + 1 * s, s=s)
    g = rng("peppers")
    for i in range(6):
        x = int(cx - 6 * s + g.integers(0, 16) * s)
        y = int(cy - 1 * s + g.integers(0, 6) * s)
        p.put(x, y, hexc("#d4402a"))
        p.put(x + 1, y + 1, hexc("#8a2a1c"), 0.8)
    road(p, [(cx - 12 * s, cy + 16 * s), (cx, cy + 6 * s), (cx + 14 * s, cy - 8 * s)], w=1, pal=ramp("#5a4a30", "#7a6640", "#9c8756", "#b8a26e"))


def sc_reed_marsh(p, cx, cy, s, water):
    """Grey pools and reed beds, dead trees, the hermit's stilt house, a causeway of stones."""
    m = (p.ellipse(cx + 8 * s, cy + 10 * s, 60 * s, 30 * s) | p.ellipse(cx + 44 * s, cy + 26 * s, 40 * s, 20 * s)) & ~water
    mn = p.noise(7 * s, "marsh", 2)
    p.paint(m, MARSH, 0.3 + mn * 0.5)
    fringe = m
    for k in range(3 * s):     # the marsh's edge frays into the meadow
        fringe = dilate(fringe)
        p.flat(fringe & ~m & ~water & (p.B < 0.7 - k / (3.0 * s) * 0.6), MARSH[2], 0.9)
    pools = m & (mn < 0.42)
    p.paint(pools, MARSH_WATER, 0.4 + (p.noise(4 * s, "mw") - 0.5) * 0.3)
    p.flat(pools & ~shift(pools, 0, 1), MARSH_WATER[0], 0.6)
    p.flat(pools & (p.noise(10 * s, "mw-b") > 0.6) & ((p.YY // s) % 3 == 0), MARSH_WATER[4], 0.5)
    reeds(p, m & (mn > 0.44) & (mn < 0.72) & ((p.XX * 3 + p.YY) % (4 * s) == 0), "reeds", s)
    stones(p, p.band(catmull([(cx - 26 * s, cy - 8 * s), (cx + 2 * s, cy + 1 * s), (cx + 26 * s, cy + 14 * s)]), [2 * s, 2 * s]) & m, "causeway", pal=STONE, density=2.2, s=s)
    g = rng("dead-trees")
    for i in range(8):
        x = int(cx - 30 * s + g.integers(0, 70) * s)
        y = int(cy - 8 * s + g.integers(0, 30) * s)
        if 0 <= x < p.w and 0 <= y < p.h and m[y, x]:
            dead_tree(p, x, y, int(g.integers(4, 7)) * s, s)
    stilt_hut(p, cx - 10 * s, cy + 8 * s, w=6, s=s)
    lantern(p, cx - 10 * s, cy + 7 * s, s=s)
    patchy(p, p.ellipse(cx + 20 * s, cy + 18 * s, 60 * s, 18 * s), MIST, 0.4, 14 * s, "marsh-mist", cover=0.5)


def sc_greyreed_hamlet(p, cx, cy, s, water):
    """Stilt huts at the marsh's edge joined by boardwalks, nets and lanterns."""
    boardwalk(p, [(cx - 12 * s, cy + 4 * s), (cx + 2 * s, cy + 8 * s), (cx + 14 * s, cy + 2 * s)], s)
    boardwalk(p, [(cx + 2 * s, cy + 8 * s), (cx + 4 * s, cy - 6 * s)], s)
    stilt_hut(p, cx - 10 * s, cy + 2 * s, s=s)
    stilt_hut(p, cx + 3 * s, cy + 7 * s, s=s)
    stilt_hut(p, cx + 12 * s, cy - 1 * s, s=s)
    stilt_hut(p, cx + 2 * s, cy - 8 * s, w=5, s=s)
    stilt_hut(p, cx - 8 * s, cy - 8 * s, w=5, s=s)
    for k in range(2):
        x = cx + 16 * s + k * 3 * s
        for j in range(3 * s):
            p.put(x, cy + 8 * s - j, WOOD[2])
        p.flat(p.line([(x, cy + 5 * s), (x + 3 * s, cy + 5 * s)], 1), hexc("#8fa090"), 0.8)
    for lx, ly in ((cx + 3, cy + 6), (cx - 10, cy + 1), (cx + 12, cy - 2)):
        lantern(p, cx + (lx - cx) * s, cy + (ly - cy) * s, s=s)


def sc_stonewall_quarry(p, cx, cy, s, water):
    """A terraced sandstone pit: the cut wall with a tunnel mouth, a crane, ore carts, the foreman's hut."""
    pit = p.ellipse(cx, cy + 2 * s, 30 * s, 14 * s)
    for k in range(4):
        t = p.ellipse(cx + k * 1.5 * s, cy + 2 * s + k * 1.4 * s, (30 - k * 6.5) * s, (14 - k * 3) * s)
        p.paint(t, QUARRY, 0.75 - k * 0.14 + (p.noise(3 * s, ("q", k)) - 0.5) * 0.25)
        p.flat(t & ~shift(t, 0, -1), QUARRY[0], 0.7)
        p.flat(t & ~shift(t, 0, 1), QUARRY[5], 0.5)
    stones(p, pit & (p.noise(3 * s, "q-stones") > 0.6), "quarry-rocks", pal=STONE_WARM, density=1.2, s=s)
    cliff(p, p.poly([(cx - 30 * s, cy - 6 * s), (cx + 30 * s, cy - 6 * s), (cx + 26 * s, cy - 12 * s), (cx - 24 * s, cy - 13 * s)]), "quarry-wall", pal=QUARRY, lit=0.1, s=s)
    p.flat(p.rect(cx + 6 * s, cy - 11 * s, cx + 9 * s, cy - 7 * s), INK, 0.85)       # the collapsed tunnel's mouth
    for k in range(7 * s):
        p.put(int(cx + 10 * s + k), int(cy - 14 * s + k), WOOD[3])
    for k in range(5 * s):
        p.put(int(cx + 10 * s), int(cy - 14 * s + k), WOOD[2])
    p.put(int(cx + 16 * s), int(cy - 7 * s), STONE_WARM[2])
    cart(p, cx - 8 * s, cy + 6 * s, s)
    cart(p, cx + 4 * s, cy + 9 * s, s)
    hall(p, cx - 24 * s, cy - 8 * s, 7, 3, 3, roof=THATCH, wall=WOOD, windows=1, eaves=1, s=s)
    lantern(p, cx - 24 * s, cy - 9 * s, s=s)
    lantern(p, cx + 2 * s, cy + 3 * s, s=s)


def sc_mudwater_hideout(p, cx, cy, s, water):
    """A bandit stockade under a cliff with a cave mouth: log walls, tents, a watchtower, a campfire."""
    cl = p.ellipse(cx - 8 * s, cy - 12 * s, 30 * s, 10 * s) & (p.YY > cy - 16 * s)
    cliff(p, cl, "mud-cliff", pal=MUD, s=s)
    p.flat(p.rect(cx - 5 * s, cy - 9 * s, cx - 1 * s, cy - 4 * s), INK, 0.9)
    p.flat(p.rect(cx - 4 * s, cy - 10 * s, cx - 2 * s, cy - 10 * s), INK, 0.9)
    yard = p.poly([(cx - 16 * s, cy + 2 * s), (cx + 16 * s, cy + 1 * s), (cx + 12 * s, cy + 9 * s), (cx - 12 * s, cy + 9 * s)])
    p.paint(yard, MUD, 0.55 + (p.noise(3 * s, "yard") - 0.5) * 0.4)
    wall_line(p, [(cx - 16 * s, cy + 2 * s), (cx - 12 * s, cy + 9 * s), (cx + 12 * s, cy + 9 * s), (cx + 16 * s, cy + 1 * s)], WOOD[5], WOOD[2], h=3 * s)
    for k in range(-14, 15, 3):
        p.put(int(cx + k * s), int(cy + 8 * s + (0 if abs(k) < 12 else -2 * s)), WOOD[6])
    hall(p, cx + 2 * s, cy + 3 * s, 10, 3, 3, roof=THATCH, wall=WOOD, windows=1, eaves=1, s=s)
    tent(p, cx - 9 * s, cy + 6 * s, 6, s)
    tent(p, cx + 12 * s, cy + 6 * s, 5, s)
    campfire(p, int(cx - 2 * s), int(cy + 7 * s), s)
    watchtower(p, cx + 18 * s, cy + 2 * s, s)
    lantern(p, cx - 6 * s, cy + 3 * s, s=s)


def sc_jade_sect(p, cx, cy, s, water):
    """The Academy walled on its hill: gate towers, courtyards, halls, a tall pagoda, terraces down the west slope."""
    lawn = p.poly([(cx - 30 * s, cy + 12 * s), (cx - 27 * s, cy - 8 * s), (cx - 8 * s, cy - 18 * s), (cx + 8 * s, cy - 18 * s), (cx + 28 * s, cy - 8 * s), (cx + 31 * s, cy + 10 * s), (cx + 20 * s, cy + 18 * s), (cx - 22 * s, cy + 18 * s)])
    p.paint(lawn, MEADOW, 0.6 + (0.5 - (p.XX - cx) / (60.0 * s)) * 0.4 - ((p.YY - cy) / (40.0 * s)) * 0.3 + (p.noise(4 * s, "lawn") - 0.5) * 0.2)
    court = p.poly([(cx - 12 * s, cy + 12 * s), (cx - 12 * s, cy + 2 * s), (cx + 14 * s, cy + 2 * s), (cx + 14 * s, cy + 12 * s)])
    p.paint(court, ramp("#8a8474", "#a8a28f", "#c6c0aa", "#e0dbc6"), 0.6 + (p.noise(3 * s, "court") - 0.5) * 0.3)
    pond = p.ellipse(cx + 8 * s, cy + 8 * s, 4 * s, 2 * s)
    p.paint(pond, LAKE, 0.7)
    p.put(int(cx + 7 * s), int(cy + 8 * s), LEAF[4])
    terraces(p, cx - 24 * s, cy + 4 * s, 4, 12, "js-terr", s)
    wall_line(p, [(cx - 30 * s, cy + 12 * s), (cx - 22 * s, cy + 18 * s), (cx + 20 * s, cy + 18 * s), (cx + 31 * s, cy + 10 * s)], WALL[3], WALL[0], h=2 * s)
    wall_line(p, [(cx - 30 * s, cy + 12 * s), (cx - 27 * s, cy - 8 * s), (cx - 8 * s, cy - 18 * s)], WALL[3], WALL[0], h=2 * s)
    wall_line(p, [(cx + 31 * s, cy + 10 * s), (cx + 28 * s, cy - 8 * s), (cx + 8 * s, cy - 18 * s)], WALL[3], WALL[0], h=2 * s)
    hall(p, cx - 15 * s, cy - 4 * s, 12, 4, 4, roof=ROOF, wall=WALL, windows=2, s=s)
    hall(p, cx + 16 * s, cy - 2 * s, 14, 4, 4, roof=ROOF, wall=WALL, windows=3, s=s)
    hall(p, cx, cy - 12 * s, 10, 4, 4, roof=ROOF_BLUE, wall=WALL, windows=2, s=s)
    hall(p, cx - 6 * s, cy + 14 * s, 10, 4, 4, roof=ROOF, wall=WALL, windows=2, s=s)
    hall(p, cx + 20 * s, cy + 12 * s, 9, 3, 3, roof=ROOF_GREY, wall=WALL, windows=2, s=s)
    hall(p, cx - 22 * s, cy + 12 * s, 8, 3, 3, roof=ROOF_GREY, wall=WALL, windows=1, s=s)
    pagoda(p, cx + 1 * s, cy + 1 * s, 5, 14, roof=ROOF, wall=LACQUER, tier_h=4, s=s)
    gate(p, cx, cy + 21 * s, 9, s=s)
    pagoda(p, cx - 26 * s, cy - 6 * s, 2, 6, roof=ROOF, wall=LACQUER, tier_h=3, s=s)
    pagoda(p, cx + 27 * s, cy - 6 * s, 2, 6, roof=ROOF, wall=LACQUER, tier_h=3, s=s)
    for lx, ly in ((cx - 5, cy + 21), (cx + 5, cy + 21), (cx - 20, cy - 1), (cx + 20, cy + 1), (cx + 10, cy + 13), (cx - 8, cy + 15), (cx - 2, cy - 9), (cx + 24, cy + 13), (cx - 24, cy + 13)):
        lantern(p, cx + (lx - cx) * s, cy + (ly - cy) * s, s=s)
    clump(p, cx + 8 * s, cy + 8 * s, 2, 1.4 * s, 1.8 * s, PINE, "js-pine")
    clump(p, cx - 8 * s, cy + 5 * s, 2, 1.2 * s, 1.6 * s, PLUM, "js-plum")
    # Elder Hu's peak behind the Academy: a small tower with a pavilion
    karst(p, cx - 38 * s, cy - 46 * s, cy - 10 * s, 10 * s, 91, crown=0.4)
    hall(p, cx - 38 * s, cy - 44 * s, 5, 2, 2, roof=ROOF, wall=WOOD, windows=0, eaves=1, s=s)
    lantern(p, cx - 38 * s, cy - 45 * s, s=s)


def sc_hidden_vale(p, cx, cy, s, water):
    """A fold behind the ridge: the sect's own grounds, a gate, a plum orchard, mist and a stream."""
    vale = p.ellipse(cx + 2 * s, cy + 14 * s, 24 * s, 10 * s)
    p.paint(vale, MEADOW, 0.5 + (p.noise(4 * s, "vale") - 0.5) * 0.3 - (p.YY - cy - 6 * s) / (30.0 * s))
    p.flat(vale & ~erode(vale), MEADOW[1], 0.7)
    stream = p.band(catmull([(cx - 22 * s, cy + 8 * s), (cx - 8 * s, cy + 14 * s), (cx + 6 * s, cy + 22 * s)]), [2 * s, 2 * s])
    p.paint(stream, RIVER, 0.7)
    orchard(p, cx + 12 * s, cy + 10 * s, 3, 2, 4, "hv-plum", s=s, pal=PLUM, r=1.6)
    hall(p, cx - 4 * s, cy + 14 * s, 10, 3, 3, roof=ROOF, wall=WALL, windows=2, s=s)
    hall(p, cx + 8 * s, cy + 18 * s, 7, 2, 2, roof=ROOF, wall=WALL, windows=1, eaves=1, s=s)
    wall_line(p, [(cx - 16 * s, cy + 20 * s), (cx - 6 * s, cy + 23 * s), (cx + 14 * s, cy + 23 * s), (cx + 20 * s, cy + 18 * s)], WALL[3], WALL[0], h=1 * s)
    gate(p, cx - 12 * s, cy + 22 * s, 5, s=s)
    lantern(p, cx - 4 * s, cy + 15 * s, s=s)
    lantern(p, cx - 12 * s, cy + 20 * s, s=s)
    patchy(p, p.ellipse(cx + 4 * s, cy + 4 * s, 30 * s, 9 * s), MIST, 0.45, 12 * s, "vale-mist", cover=0.55)


SCENES = {
    "stoneford": sc_stoneford, "lotus_ferry": sc_lotus_ferry, "willow_path": sc_willow_path, "caravan_road": sc_caravan_road,
    "deepwater_bend": sc_deepwater_bend, "drowned_shrine": sc_drowned_shrine, "whitewater_gorge": sc_whitewater_gorge,
    "crane_cliffs": sc_crane_cliffs, "mist_peak": sc_mist_peak, "summit_ridge": sc_summit_ridge, "cleansing_peak": sc_cleansing_peak,
    "cloud_sect": sc_cloud_sect, "crane_falls": sc_crane_falls, "bamboo_grove": sc_bamboo_grove, "reed_marsh": sc_reed_marsh,
    "greyreed_hamlet": sc_greyreed_hamlet, "stonewall_quarry": sc_stonewall_quarry, "mudwater_hideout": sc_mudwater_hideout,
    "jade_sect": sc_jade_sect, "hidden_vale": sc_hidden_vale,
}


# ---------------------------------------------------------------- the painting
def paint_map(regions):
    p = P(W, H)
    R = {k: (v[0], v[1]) for k, v in regions.items()}
    XX, YY = p.XX, p.YY

    # ---- sky: warm at the horizon, cooler above; the far ranges fade into it
    sky_v = np.clip(YY / 66.0, 0, 1)
    p.paint(p.all(), SKY, 1 - sky_v * 0.95)
    far_prof = p.noise(26, "far-peaks", 2)[0]
    for k in range(3):
        base_y = 44 + k * 12
        pts = [(x, base_y - 12 - far_prof[(x * (k + 2) + k * 90) % W] * (32 - k * 7) - 7 * math.sin(x * 0.041 + k * 1.3)) for x in range(W)]
        m = p.poly([(0, base_y + 40)] + pts + [(W - 1, base_y + 40)])
        p.paint(m, FAR, 0.35 + k * 0.28 + (p.noise(9, ("far", k)) - 0.5) * 0.25)
        p.flat(m & ~shift(m, 0, 1), FAR[-1], 0.5)
        p.flat(m & ~shift(m, -1, 0), FAR[0], 0.35)
        p.light(m, SKY[4], 0.38 - k * 0.13)
        patchy(p, p.rect(0, base_y - 4, W - 1, base_y + 16), MIST, 0.6, 22, ("far-mist", k), cover=0.55)

    # ---- the valley floor: a height field for the ground light, meadow with wooded and rocky ground by noise
    hmap = np.zeros((H, W))
    hmap += gauss(p, R["jade_sect"][0], R["jade_sect"][1] + 6, 46, 24, 14.0)
    hmap += gauss(p, R["stonewall_quarry"][0], R["stonewall_quarry"][1], 40, 18, 5.0)
    hmap += gauss(p, R["mudwater_hideout"][0] - 10, R["mudwater_hideout"][1] - 2, 36, 16, 6.0)
    hmap += gauss(p, R["bamboo_grove"][0] + 20, R["bamboo_grove"][1], 40, 30, 4.0)
    hmap += gauss(p, 540, 250, 60, 40, 10.0)
    hmap += gauss(p, 300, 268, 40, 16, 6.0)
    hmap += gauss(p, 60, 262, 40, 40, 7.0)
    hmap -= gauss(p, R["reed_marsh"][0] + 10, R["reed_marsh"][1] + 8, 60, 34, 6.0)
    hmap += p.noise(30, "ground-h", 3) * 6.0
    L = np.clip(light_field(hmap), -1.6, 1.6)
    base_n = p.noise(12, "ground", 3)
    edge_n = p.noise(24, "floor-edge", 2)[0]
    floor = YY > (56 + edge_n * 14)[None, :]
    p.paint(floor, MEADOW, 0.38 + base_n * 0.36 + L * 0.16)
    # woods by a broad noise, thicker at the sides and the near edge; clearings keep the towns and fields open
    wood_n = p.noise(26, "woods", 3)
    wood_f = wood_n + np.clip((YY - 200) / 140.0, 0, 0.5) * 0.5 - gauss(p, R["stoneford"][0] + 30, R["stoneford"][1] + 8, 130, 40, 0.5)
    woods = floor & (wood_f > 0.5)
    p.paint(woods, OLIVE, 0.28 + base_n * 0.3 + L * 0.14)
    p.flat(woods & ~erode(woods), OLIVE[1], 0.6)
    # the meadow's own grain: tufts and a few flowers
    p.flat(floor & ~woods & ((XX * 7 + YY * 3) % 11 == 0) & (base_n > 0.4), MEADOW[1], 0.5)
    p.flat(floor & ~woods & ((XX * 3 + YY * 5) % 13 == 0), MEADOW[5], 0.5)
    meadow_flowers(p, floor & ~woods & (base_n > 0.6) & (YY > 120), "flowers")
    # atmospheric haze: the far floor pales toward the range
    for y1, a in ((160, 0.07), (136, 0.09), (116, 0.12), (98, 0.16), (84, 0.22)):
        p.light(floor & (YY < y1), SKY[3], a)

    # ---- the northern range: towers back to front, mist between the ranks
    sx, sy = R["summit_ridge"]
    karst(p, sx - 30, sy - 6, sy + 48, 22, 11, snow=SNOW, fade=0.12)
    karst(p, sx + 6, sy - 18, sy + 54, 26, 12, snow=SNOW, fade=0.1)
    karst(p, sx + 34, sy - 2, sy + 46, 16, 13, snow=SNOW, fade=0.12)
    mx, my = R["mist_peak"]
    karst(p, mx - 20, my + 6, my + 46, 15, 21, fade=0.06)
    karst(p, mx + 2, my - 12, my + 50, 19, 22, snow=SNOW, fade=0.06)
    cx_, cy_ = R["crane_cliffs"]
    karst(p, cx_ - 24, cy_ - 2, cy_ + 42, 22, 31, rock=CLIFF, crown=0.3)
    karst(p, cx_ + 8, cy_ - 16, cy_ + 44, 26, 32, rock=CLIFF, crown=0.45)
    karst(p, cx_ + 34, cy_ + 6, cy_ + 40, 14, 33)
    px_, py_ = R["cleansing_peak"]
    karst(p, px_ - 22, py_ + 10, py_ + 52, 17, 51, fade=0.05)
    karst(p, px_ + 2, py_ - 18, py_ + 54, 19, 52, snow=SNOW, fade=0.05)
    karst(p, 502, 42, 124, 32, 61, snow=SNOW, fade=0.1)
    karst(p, 550, 60, 134, 26, 62, fade=0.06)
    karst(p, 598, 36, 128, 34, 63, snow=SNOW, fade=0.1)
    karst(p, 634, 66, 134, 22, 64)
    hv_x, hv_y = R["hidden_vale"]
    karst(p, hv_x - 28, hv_y - 2, hv_y + 40, 20, 71)
    karst(p, hv_x + 30, hv_y - 12, hv_y + 42, 22, 72)
    cs_x, cs_y = R["cloud_sect"]
    karst(p, cs_x - 16, cs_y + 8, cs_y + 46, 13, 81)
    karst(p, cs_x + 2, cs_y - 24, cs_y + 48, 15, 82)
    karst(p, cs_x + 26, cs_y + 2, cs_y + 44, 13, 83)
    patchy(p, p.rect(0, 70, W - 1, 112), CLOUD[3], 0.5, 18, "range-mist", cover=0.5)
    # mid-ground towers that give the valley its verticals
    karst(p, 300, 118, 150, 12, 101)
    karst(p, 470, 136, 176, 16, 102)
    karst(p, 520, 160, 206, 20, 103)
    karst(p, 600, 176, 230, 26, 104)
    karst(p, 30, 222, 262, 16, 107)
    karst(p, 178, 256, 292, 12, 112)
    karst(p, 330, 286, 318, 16, 113)
    karst(p, 452, 262, 306, 20, 110)

    # ---- the water: the river from the falls to the gorge, the shrine's bay, a tributary from the range, a mill stream
    cf = R["crane_falls"]
    lf, wp, st, cr, db, ds, wg = R["lotus_ferry"], R["willow_path"], R["stoneford"], R["caravan_road"], R["deepwater_bend"], R["drowned_shrine"], R["whitewater_gorge"]
    rv = [(cf[0] + 3, cf[1] + 12, 6), (cf[0] + 14, cf[1] + 30, 9), (cf[0] + 6, cf[1] + 50, 12), (lf[0] + 10, lf[1] - 10, 15), (lf[0] - 4, lf[1] - 6, 17),
          (wp[0] + 4, wp[1] - 5, 17), (st[0] + 14, st[1] - 3, 18), (st[0], st[1], 18), (cr[0] + 10, cr[1] - 7, 19), (cr[0] - 14, cr[1] - 10, 21),
          (db[0] + 6, db[1] + 2, 24), (db[0] - 12, db[1] - 6, 18), (wg[0] + 8, wg[1] + 12, 11), (wg[0] - 6, wg[1] - 8, 8), (44, 112, 7), (26, 104, 6)]
    river_m = band_w(p, catmull_w(rv, 2.0))
    lake_m = p.ellipse(ds[0] + 2, ds[1] + 3, 27, 14) | band_w(p, catmull_w([(db[0] + 2, db[1] + 8, 9), (ds[0] + 12, ds[1] - 6, 11)]))
    trib = band_w(p, catmull_w([(cs_x + 30, cs_y + 22, 3), (cs_x + 18, cs_y + 38, 4), (cs_x + 2, cs_y + 52, 5), (st[0] + 12, st[1] - 12, 5), (st[0] + 8, st[1] - 4, 6)]))
    mill = band_w(p, catmull_w([(228, 322, 3), (222, 300, 3), (216, 274, 3), (208, 244, 3), (200, 222, 3), (cr[0] + 8, cr[1] - 2, 4)]))
    water = river_m | lake_m | trib | mill
    p.water = water
    # cliffs where the river cuts a bank
    for m_, seed in ((p.rect(cr[0] - 30, 0, st[0] - 8, st[1] - 2), "n-bank"), (p.rect(db[0] - 34, db[1] - 44, db[0] - 2, db[1] - 6), "bend-cliff"),
                     (p.rect(lf[0] + 8, lf[1] - 60, lf[0] + 34, lf[1] - 14), "east-bank")):
        cm = dilate(dilate(dilate(water))) & ~water & m_
        cliff(p, cm, seed, pal=CLIFF)
    river_paint(p, water, "main", deep=p.ellipse(db[0] + 2, db[1] + 2, 18, 12))
    p.paint(lake_m & ~dilate(river_m), LAKE, 0.5 + (p.noise(4, "lake") - 0.5) * 0.25)
    p.flat(lake_m & (p.noise(10, "lake-b") > 0.6) & (YY % 3 == 0), LAKE[5], 0.4)
    rapids(p, river_m & p.ellipse(wg[0] - 2, wg[1] - 2, 26, 30), "gorge-rapids")
    rapids(p, trib & (YY < cs_y + 34), "trib-rapids")
    # the gorge's mouth: the cliffs the river leaves through stand in front of it
    karst(p, 40, 98, 152, 24, 41, rock=CLIFF)
    karst(p, 8, 110, 160, 18, 42, rock=CLIFF)
    # small falls where the river's cliffs drop into it
    waterfall(p, int(st[0] - 22), int(st[1] - 16), int(st[1] - 8), w=2, seed=11, tiers=1)
    waterfall(p, int(db[0] - 20), int(db[1] - 22), int(db[1] - 12), w=2, seed=12, tiers=1)
    waterfall(p, int(lf[0] + 22), int(lf[1] - 36), int(lf[1] - 26), w=2, seed=13, tiers=1)
    # the second fall: off the range into the tributary's head
    waterfall(p, int(cs_x + 30), int(cs_y + 8), int(cs_y + 20), w=3, seed=7, tiers=2)

    # ---- fields: paddies on the flats south of the river, terraces on the slopes, orchards, bamboo stands
    paddies(p, st[0] + 42, st[1] + 22, 5, 2, 9, 5, "paddy-a", skew=0.4)
    paddies(p, lf[0] - 4, lf[1] + 30, 4, 2, 8, 5, "paddy-b", skew=0.3)
    paddies(p, cr[0] + 42, cr[1] + 22, 3, 2, 8, 5, "paddy-c", skew=0.3)
    paddies(p, 468, 232, 4, 2, 8, 5, "paddy-d", skew=0.35)
    terraces(p, 300, 262, 5, 26, "terr-a")
    terraces(p, 545, 280, 4, 22, "terr-b")
    orchard(p, 330, 246, 5, 2, 4, "orch-a")
    orchard(p, 590, 226, 4, 2, 4, "orch-b", pal=PLUM)
    for (bx, by, rx, ry) in ((470, 200, 16, 9), (600, 300, 18, 8), (140, 272, 14, 8), (372, 292, 12, 7)):
        bamboo_field(p, p.ellipse(bx, by, rx, ry) & ~dilate(water), ("stand", bx))
    # rocky slopes at the range's feet and scree
    scree = floor & (YY > 100) & (YY < 150) & (p.noise(8, "scree") > 0.66) & ~water
    p.paint(scree, CLIFF, 0.5 + (base_n - 0.5) * 0.4)
    stones(p, scree, "scree-stones", pal=CLIFF, density=1.0)

    # ---- roads: the river road, the hill roads, the mountain paths (the page's routes follow these)
    mh, sq, bg, gh, rm = R["mudwater_hideout"], R["stonewall_quarry"], R["bamboo_grove"], R["greyreed_hamlet"], R["reed_marsh"]
    road(p, [(mh[0] + 4, mh[1] - 8), (mh[0] + 14, mh[1] - 18), (cr[0], cr[1] + 3), (cr[0] + 24, cr[1] - 2), (st[0] - 10, st[1] + 8), (st[0] + 4, st[1] + 9),
             (wp[0] - 10, wp[1] + 6), (wp[0] + 14, wp[1] + 6), (lf[0] - 6, lf[1] + 4), (lf[0] + 14, lf[1] + 12), (rm[0] - 22, rm[1] - 6)], w=2)
    road(p, [(st[0] - 1, st[1] - 9), (st[0] - 8, st[1] - 20), (R["jade_sect"][0] - 4, R["jade_sect"][1] + 26), (R["jade_sect"][0], R["jade_sect"][1] + 21)], w=2)
    road(p, [(st[0] + 6, st[1] - 9), (st[0] + 18, st[1] - 20), (cs_x + 6, cs_y + 46), (cs_x + 4, cs_y + 30), (cs_x - 12, cs_y + 2)], w=1)
    road(p, [(st[0] + 6, st[1] + 10), (sq[0] - 2, sq[1] - 14), (sq[0] - 20, sq[1] - 4)], w=1)
    road(p, [(rm[0] - 22, rm[1] - 6), (rm[0] + 2, rm[1] + 1), (gh[0] - 12, gh[1] + 4)], w=1)
    road(p, [(rm[0] - 10, rm[1] - 14), (bg[0] - 12, bg[1] + 16), (bg[0], bg[1] + 6), (cf[0] + 14, cf[1] + 18), (cf[0] + 8, cf[1] + 4)], w=1)
    road(p, [(cf[0] + 16, cf[1] + 16), (cf[0] + 26, cf[1] - 2), (hv_x - 14, hv_y + 22)], w=1)
    road(p, [(cf[0] - 8, cf[1] + 14), (px_ - 6, py_ + 34), (px_ + 6, py_ + 26)], w=1)
    road(p, [(cr[0] - 12, cr[1] + 2), (db[0] + 4, db[1] + 12), (db[0] - 8, db[1] + 12)], w=1)
    road(p, [(db[0] - 10, db[1] - 6), (wg[0] + 14, wg[1] + 14), (wg[0] + 10, wg[1] - 2)], w=1)
    road(p, [(wg[0] - 6, wg[1] - 22), (cx_ - 2, cy_ + 20), (cx_ + 4, cy_ + 12)], w=1)
    road(p, [(cx_ + 14, cy_ - 2), (mx - 12, my + 20), (mx + 2, my + 26)], w=1)
    road(p, [(mx + 10, my + 18), (sx - 10, sy + 20), (sx + 2, sy + 10)], w=1)
    road(p, [(300, 250), (296, 226), (st[0] + 30, st[1] + 9)], w=1)                       # the farm track to the terraces
    road(p, [(214, 262), (206, 244), (200, 228), (cr[0] + 8, cr[1] + 4)], w=1)             # the mill track
    bridge_wood(p, cs_x + 2, cs_y + 46, cs_x + 8, cs_y + 46, s=1)                           # over the tributary, on the Cloud Sect path
    bridge_wood(p, 213, 268, 220, 268, s=1)                                                # over the mill stream
    bridge_stone(p, 205, 224, 211, 224, s=1)

    # ---- woods: clumps of crowns through the wooded ground and along the near edge, larger toward the viewer
    forbid = dilate(dilate(water)) | scree
    for rid, (x, y) in R.items():
        forbid |= p.ellipse(x, y, 30, 20)
    for (fx, fy, frx, fry) in ((306, 280, 22, 10), (480, 246, 22, 10), (556, 296, 20, 9), (540, 254, 32, 14), (208, 258, 12, 8), (334, 232, 8, 6), (452, 246, 8, 6),
                               (st[0] + 42, st[1] + 22, 28, 9), (lf[0] - 4, lf[1] + 30, 22, 9), (cr[0] + 42, cr[1] + 22, 16, 8), (468, 232, 20, 8),
                               (300, 262, 18, 12), (545, 280, 16, 10), (330, 246, 12, 6), (590, 226, 10, 6)):
        forbid |= p.ellipse(fx, fy, frx, fry)
    wood_fill = woods & ~forbid & (YY > 96)
    forest(p, wood_fill & (wood_n > 0.6), FOREST, "wood-dense", density=0.5, rmin=1.5, rmax=3.0, near=0.9)
    forest(p, wood_fill & (wood_n <= 0.6), OLIVE, "wood-open", density=0.42, rmin=1.4, rmax=2.8, near=0.9)
    clumps_in(p, wood_fill, OLIVE, "wood-clumps", 160, nmin=4, nmax=9, rmin=1.6, rmax=3.2, near=0.9)
    clumps_in(p, floor & ~woods & ~forbid & (YY > 120) & (base_n > 0.5), OLIVE, "meadow-clumps", 110, nmin=2, nmax=6, rmin=1.4, rmax=2.6, near=0.8)
    clumps_in(p, floor & (YY > 108) & (YY < 150) & ~forbid & (p.noise(6, "pines") > 0.55), PINE, "pines", 50, nmin=2, nmax=5, rmin=1.2, rmax=2.2)

    # ---- secondary scenery: farms, a watermill, a shrine, a pagoda on a hill, a hermit's hut
    farmstead(p, 306, 284, 1, "farm-a")
    farmstead(p, 480, 250, 1, "farm-b")
    farmstead(p, 556, 300, 1, "farm-c")
    watermill(p, 208, 262)
    shrine(p, 334, 232)
    shrine(p, 452, 246)
    hill(p, 540, 254, 30, 13, "pagoda-hill", pal=MEADOW)
    forest(p, p.ellipse(540, 258, 28, 11) & ~p.ellipse(540, 252, 14, 6), OLIVE, "pagoda-hill-trees", density=0.8, rmin=1.4, rmax=2.4)
    pagoda(p, 540, 250, 5, 12, roof=ROOF_BLUE, wall=LACQUER, tier_h=4)
    lantern(p, 536, 251)
    lantern(p, 544, 251)
    hall(p, 62, 262, 7, 2, 3, roof=THATCH, wall=WOOD, windows=1, eaves=1)
    lantern(p, 62, 261)

    # ---- the regions' scenes, far to near
    for rid in sorted(R, key=lambda k: R[k][1]):
        SCENES[rid](p, R[rid][0], R[rid][1], 1, water)

    # ---- light on the water, mist on the marsh and the gorge
    lantern_reflections(p)
    patchy(p, p.ellipse(wg[0] - 4, wg[1] + 2, 30, 18), MIST, 0.45, 12, "gorge-mist", cover=0.5)
    patchy(p, p.ellipse(db[0] - 20, db[1] - 30, 40, 12), MIST, 0.35, 12, "bend-mist", cover=0.45)

    # ---- the near foreground: dark crowns along the bottom, a rooftop corner with hanging lanterns at the left,
    #      a great tree at the right
    near_m = p.rect(0, H - 30, W - 1, H - 1) & ~p.rect(0, 0, 130, H - 1)
    forest(p, near_m & (p.noise(8, "near") > 0.3), FOREST, "near-woods", density=0.7, rmin=3.0, rmax=5.5)
    # a rooftop corner in the near left: the ridge, rows of dark tiles, the upturned eave, a beam with lanterns
    roofm = p.poly([(0, 272), (96, 264), (112, 276), (100, 292), (0, 298)])
    roof_tiles(p, roofm, DARK_ROOF)
    rows = roofm & ((YY - (XX // 12)) % 4 == 0)
    p.flat(rows, DARK_ROOF[0], 0.7)
    cols = roofm & ((XX + (YY // 3)) % 7 == 0)
    p.flat(cols, DARK_ROOF[3], 0.35)
    p.flat(p.line([(0, 272), (96, 264)], 1), DARK_ROOF[4])
    p.flat(p.line([(96, 264), (112, 276)], 1), DARK_ROOF[4])
    p.flat(roofm & ~shift(roofm, 0, 1), DARK_ROOF[4], 0.5)
    for k, (x, y) in enumerate(((112, 276), (114, 273), (116, 271), (118, 270))):
        p.put(x, y, DARK_ROOF[4])
        p.put(x, y + 1, DARK_ROOF[2])
    p.flat(p.rect(0, 298, 100, H - 1), INK, 0.75)
    p.flat(p.line([(0, 299), (100, 293)], 1), WOOD[2])
    for k in range(4, 100, 9):
        p.put(k, 300 - k // 17, WOOD[3])
    hanging_lantern(p, 34, 286, size=4)
    hanging_lantern(p, 74, 284, size=4)
    hanging_lantern(p, 14, 292, size=3)
    for (x, y, r) in ((610, 296, 14.0), (582, 306, 11.0), (632, 312, 10.0), (560, 316, 8.0)):
        tree(p, x, y, r, FOREST)
    p.flat(p.circle(612, 318, 10), INK, 0.5)
    hanging_lantern(p, 604, 270, size=4)
    # the picture darkens toward its near edge and corners
    t = np.clip((YY - (H - 52)) / 52.0, 0, 1)
    for step, a in ((0.2, 0.06), (0.45, 0.08), (0.7, 0.1), (0.92, 0.12)):
        p.flat(p.all() & (t >= step), INK, a)
    return p


# ---------------------------------------------------------------- the vignettes: each scene painted at twice the scale
BACKDROP = {
    "stoneford": ("river", 0), "lotus_ferry": ("river", -9), "willow_path": ("river", -8), "caravan_road": ("river", -9),
    "deepwater_bend": ("river", 2), "drowned_shrine": ("bay", 2), "whitewater_gorge": ("gorge", 0), "crane_cliffs": ("peak", 0),
    "mist_peak": ("peak", 0), "summit_ridge": ("snow", 0), "cleansing_peak": ("peak", 0), "cloud_sect": ("peak", 0),
    "crane_falls": ("falls", 0), "bamboo_grove": ("meadow", 0), "reed_marsh": ("marsh", 0), "greyreed_hamlet": ("marsh", 0),
    "stonewall_quarry": ("meadow", 0), "mudwater_hideout": ("meadow", 0), "jade_sect": ("hill", 0), "hidden_vale": ("hill", 0),
}


def paint_vignette(rid):
    """One region's close-up: a backdrop of its kind of ground, then its scene at scale 2 round the canvas centre."""
    s = 2
    p = P(VIG_W, VIG_H)
    kind, dy = BACKDROP[rid]
    cx, cy = VIG_W / 2, VIG_H / 2 - dy * s * 0.5
    XX, YY = p.XX, p.YY
    n = p.noise(10, ("vig", rid), 3)
    water = p.zeros()
    if kind in ("peak", "snow", "falls"):
        p.paint(p.all(), SKY, 0.85 - YY / VIG_H * 0.5)
        far = p.poly([(0, 40), (20, 22), (44, 34), (70, 14), (96, 30), (128, 18), (128, 72), (0, 72)])
        p.paint(far, FAR, 0.5 + (n - 0.5) * 0.3)
        p.light(far, SKY[4], 0.35)
        body = p.poly([(0, 72), (0, 34), (30, 20), (60, 28), (90, 16), (128, 30), (128, 72)])
        p.paint(body, ROCK if kind != "snow" else CLIFF, 0.55 - (XX - 64) / 200.0 + (n - 0.5) * 0.4 - (YY - 30) / 120.0)
        p.flat(body & ((YY + (n * 6).astype(int)) % 6 == 0), ROCK[1], 0.5)
        if kind == "snow":
            p.paint(body & (YY < 34) & (n > 0.35), SNOW, 0.5 + (n - 0.5) * 0.5)
        forest(p, body & (YY > 40) & (n > 0.5), PINE, ("vig-pines", rid), density=0.5, rmin=2.0, rmax=3.5)
        patchy(p, p.rect(0, 30, 127, 60), MIST, 0.5, 20, ("vig-mist", rid), cover=0.5)
        if kind == "falls":
            water = p.ellipse(70, 60, 44, 12)
            river_paint(p, water, ("vig-water", rid), s=s)
    elif kind == "gorge":
        p.paint(p.all(), CLIFF, 0.5 + (n - 0.5) * 0.4)
        water = p.band(catmull([(56, -4), (62, 30), (70, 76)]), [22, 26, 30])
        river_paint(p, water, ("vig-water", rid), s=s)
    elif kind == "bay":
        p.paint(p.all(), MEADOW, 0.45 + (n - 0.5) * 0.4)
        forest(p, (n > 0.55) & (YY < 20), OLIVE, ("vig-woods", rid), density=0.6, rmin=2.0, rmax=3.5)
        water = p.ellipse(64, 46, 62, 30)
        river_paint(p, water, ("vig-water", rid), s=s)
        p.paint(water, LAKE, 0.5 + (n - 0.5) * 0.25)
    elif kind == "marsh":
        p.paint(p.all(), MARSH, 0.35 + n * 0.5)
        pools = n < 0.42
        p.paint(pools, MARSH_WATER, 0.4 + (n - 0.5) * 0.3)
        p.flat(pools & ~shift(pools, 0, 1), MARSH_WATER[0], 0.6)
        reeds(p, (n > 0.44) & (n < 0.7) & ((XX * 3 + YY) % 8 == 0), ("vig-reeds", rid), s)
        water = pools
    else:
        p.paint(p.all(), MEADOW, 0.42 + (n - 0.5) * 0.4)
        woods = n > 0.58
        p.paint(woods, OLIVE, 0.35 + (n - 0.5) * 0.3)
        clumps_in(p, woods, OLIVE, ("vig-clumps", rid), 10, nmin=3, nmax=7, rmin=2.2, rmax=4.0)
        if kind == "river":
            yc = cy + dy * s
            water = p.band(catmull([(-4, yc - 6), (40, yc + 2), (90, yc - 2), (132, yc + 4)]), [26, 28, 28, 26])
            river_paint(p, water, ("vig-water", rid), s=s)
    p.water = water
    SCENES[rid](p, cx, cy, s, water)
    lantern_reflections(p)
    t = np.clip((YY - 52) / 20.0, 0, 1)
    for step, a in ((0.3, 0.06), (0.7, 0.08)):
        p.flat(p.all() & (t >= step), INK, a)
    return p.image()


# ---------------------------------------------------------------- output
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
    img = paint_map(regions).image()
    os.makedirs(args.review, exist_ok=True)
    review_sheet(img, regions, os.path.join(args.review, "valley_map_review.png"))
    img.resize((W * SCALE, H * SCALE), Image.NEAREST).save(os.path.join(args.review, "valley_map_x2.png"))
    vigs = {rid: paint_vignette(rid) for rid in regions}
    sheet = Image.new("RGB", (4 * (VIG_W * 2 + 8), 5 * (VIG_H * 2 + 8)), (10, 32, 39))
    for i, rid in enumerate(regions):
        sheet.paste(vigs[rid].resize((VIG_W * 2, VIG_H * 2), Image.NEAREST), ((i % 4) * (VIG_W * 2 + 8), (i // 4) * (VIG_H * 2 + 8)))
    sheet.save(os.path.join(args.review, "valley_vignettes.png"))
    if args.no_write:
        print("review only:", args.review)
        return
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "valley_map.png")
    save_png(img.resize((W * SCALE, H * SCALE), Image.NEAREST), out)
    print(os.path.relpath(out, ROOT), "%dx%d" % (W * SCALE, H * SCALE))
    for rid in regions:
        save_png(vigs[rid].resize((VIG_W * SCALE, VIG_H * SCALE), Image.NEAREST), os.path.join(OUT_DIR, "valley_%s.png" % rid))
    print("%d vignettes %dx%d" % (len(regions), VIG_W * SCALE, VIG_H * SCALE))


if __name__ == "__main__":
    main()
