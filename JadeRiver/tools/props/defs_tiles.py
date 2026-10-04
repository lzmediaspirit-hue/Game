"""Interior wall/floor tiles, water tiles, window and hanging lantern (art/tiles/).

Repeating tiles are painted on a 3x3 replicated canvas and the centre is cropped,
so every edge wraps seamlessly (walls wrap horizontally, floors/water both ways).
"""
from __future__ import annotations

import math

import numpy as np

from palette import *  # noqa: F401,F403
from parts import blob_mask, lantern, moss_top
from pixlib import (Canvas, border, bottom_edge, dilate, erode, glow, grid, left_edge, m_ellipse, m_line, m_poly,
                    m_rect, mix, outline, right_edge, rng, seed_of, shade, shade_idx, shift, top_edge, vnoise)
from registry import prop


class Tiler:
    """Draw once per 3x3 replica so the cropped centre tile wraps."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.cv = Canvas(3 * w, 3 * h)
        xx, yy = grid(3 * w, 3 * h)
        self.xx, self.yy = xx, yy

    def rep(self, fn):
        for dy in (0, self.h, 2 * self.h):
            for dx in (0, self.w, 2 * self.w):
                fn(dx, dy)

    def field(self, a):
        return np.tile(a, (3, 3))

    def noise(self, cell, seed, octaves=1):
        return self.field(vnoise(self.w, self.h, cell, seed, octaves, wrap=True))

    def crop(self):
        out = Canvas(self.w, self.h)
        out.rgb = self.cv.rgb[self.h:2 * self.h, self.w:2 * self.w].copy()
        out.a = self.cv.a[self.h:2 * self.h, self.w:2 * self.w].copy()
        return out


def ramp_fill(cv, m, pal, v):
    n = len(pal)
    idx = np.clip((v * n).astype(int), 0, n - 1)
    cv.fill_idx(m, idx, pal)


TILE = dict(kind="tile", anchor=(0, 0), ground=0, opaque=True)


# ------------------------------------------------------------------ water
def water_frame(f, shallow=False):
    W, H = 128, 64
    T = Tiler(W, H)
    cv, xx, yy = T.cv, T.xx, T.yy
    full = np.ones((3 * H, 3 * W), bool)
    X = (xx % W) / W
    Y = (yy % H) / H
    ph = f / 4.0 * 2 * math.pi
    w1 = np.sin(2 * math.pi * (1 * X + 8 * Y) - ph)
    w2 = np.sin(2 * math.pi * (-2 * X + 5 * Y) - ph + 1.3)
    nz = T.noise(16, seed_of("wat", shallow), 2)
    field = 0.5 + 0.18 * w1 + 0.12 * w2 + (nz - 0.5) * 0.5
    if shallow:
        # sand bed seen through a thin teal film, organic caustic network, sparse crests
        pal = [hexc("#2f6f69"), hexc("#3f8079"), hexc("#529287"), hexc("#68a597"), hexc("#86b9a6"), hexc("#a9d2bd")]
        sand = T.noise(16, seed_of("sand"), 2)
        v = 0.42 + (sand - 0.5) * 0.5 + 0.08 * w1
        ramp_fill(cv, full, pal, v)
        g = rng("caustic")
        pts = [(g.uniform(0, W), g.uniform(0, H), g.uniform(0, 6.283)) for _ in range(26)]
        X0, Y0 = (xx % W).astype(float), (yy % H).astype(float)
        d1 = np.full(X0.shape, 1e9)
        d2 = np.full(X0.shape, 1e9)
        for (px, py, pp) in pts:
            px += math.cos(ph + pp) * 1.5
            py += math.sin(ph + pp) * 1.0
            for ox in (-W, 0, W):
                for oy in (-H, 0, H):
                    d = np.sqrt(((X0 - px - ox) * 0.8) ** 2 + ((Y0 - py - oy) * 1.6) ** 2)
                    d2 = np.where(d < d1, d1, np.minimum(d2, d))
                    d1 = np.minimum(d1, d)
        caus = (d2 - d1) < 1.1
        cv.fill(caus, pal[4])
        cv.fill(caus & (sand > 0.55), pal[5])
        pebble = (T.noise(4, seed_of("pebb")) > 0.83)
        cv.fill(pebble, hexc("#5e7f78"))
        cv.fill(pebble & ~shift(pebble, 0, 1), hexc("#8fb0a2"))
        crest = (w1 > 0.95) & (T.noise(8, seed_of("crs", 1)) > 0.62)
        cv.fill(crest, hexc("#d4efe2"))
    else:
        v = np.clip(field, 0, 1) * 0.62 + 0.14
        ramp_fill(cv, full, WATER, v)
        crest = (w1 > 0.86) & (T.noise(8, seed_of("crs", 0)) > 0.48)
        crest2 = (w1 > 0.95) & (T.noise(8, seed_of("crs", 2)) > 0.62)
        cv.fill(crest, WATER[6])
        cv.fill(crest2, WATER[7])
        cv.fill(shift(crest, 0, 1) & ~crest, WATER[2])
        # twinkling glints (loop over 4 frames)
        g = rng("glint")
        glints = [(int(g.integers(0, W)), int(g.integers(0, H)), int(g.integers(0, 4))) for _ in range(10)]

        def draw(dx, dy):
            for (gx, gy, p) in glints:
                k = (f + p) % 4
                ln = [1, 3, 2, 0][k]
                if ln:
                    cv.fill(m_rect(3 * W, 3 * H, dx + gx, dy + gy, dx + gx + ln - 1, dy + gy), WATER[7])
        T.rep(draw)
    return T.crop()


@prop("water", 128, 64, states=(("idle", 4, 5),), repeat="xy", **TILE)
def water(state, f):
    return water_frame(f)


# ------------------------------------------------------------------ window, hanging lantern
@prop("window", 32, 32, kind="tile", ground=0)
def window(state, f):
    W, H = 32, 32
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    fr = m_rect(W, H, 2, 2, 29, 28)
    shade(cv, fr, LACQUER, contour=True, R=1, base=0.45)
    inner = m_rect(W, H, 5, 5, 26, 25)
    cv.fill(inner, hexc("#f7d58e"))
    cv.fill(inner & (yy >= 12), hexc("#f0c070"))
    cv.fill(inner & (yy >= 19), hexc("#e3a75a"))
    # "cracked ice" + border lattice
    lat = inner & ((((xx - 5) % 5 == 0) & ((yy - 5) % 10 < 6)) | (((yy - 5) % 5 == 0) & ((xx - 5) % 10 >= 4)))
    lat |= border(inner) | border(m_rect(W, H, 11, 11, 20, 19))
    cv.fill(lat, LACQUER[1])
    cv.fill(m_rect(W, H, 12, 12, 19, 18), hexc("#fbe6b0"))
    cv.fill(top_edge(fr) | left_edge(fr), LACQUER[5])
    sill = m_rect(W, H, 0, 28, 31, 30)
    shade(cv, sill, WOOD, contour=True, R=1, base=0.6)
    cv.fill(m_rect(W, H, 1, 28, 30, 28), WOOD[6])
    outline(cv)
    glow(cv, 15.5, 15, 16, 16, hexc("#ffc070"), steps=((1.0, 0.1),), m_limit=~cv.solid)
    return cv

