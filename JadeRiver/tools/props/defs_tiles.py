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


# ------------------------------------------------------------------ walls
@prop("wall_wood", 128, 160, repeat="x", **TILE)
def wall_wood(state, f):
    W, H = 128, 160
    T = Tiler(W, H)
    cv, xx, yy = T.cv, T.xx, T.yy
    full = np.ones((3 * H, 3 * W), bool)
    ty = yy % H
    nz = T.noise(16, seed_of("ww_pl"), 2)
    fine = T.noise(4, seed_of("ww_pf"), 1)
    # plaster panels
    v = 0.74 + (nz - 0.5) * 0.1 - np.clip((24 - ty) / 10.0, 0, 1) * 0.3 - np.where(fine > 0.86, 0.1, 0)
    ramp_fill(cv, full, PLASTER, v)
    # wainscot planks
    wain = (ty >= 106) & (ty <= 151)
    nzw = T.noise(8, seed_of("ww_wn"), 2)
    pl = (xx % W) // 8
    tint = T.field(np.tile((rng("ww_t").uniform(-0.1, 0.1, 16))[None, :].repeat(8, 1)[:, :W], (H, 1)))
    ramp_fill(cv, wain, WOOD, 0.46 + tint + (nzw - 0.5) * 0.2)
    cv.fill(wain & (xx % 8 == 7), WOOD[1])
    cv.fill(wain & (xx % 8 == 0), WOOD[4])
    cv.fill(wain & (ty == 106), WOOD[1])
    # skirting + mid rail + ceiling beam
    def hbeam(y0, y1, pal, base):
        m = (ty >= y0) & (ty <= y1)
        v = base + np.where(ty == y0, 0.25, 0) - np.where(ty == y1, 0.25, 0) + (T.noise(8, seed_of("hb", y0)) - 0.5) * 0.15
        ramp_fill(cv, m, pal, v)
    hbeam(0, 11, WOOD, 0.4)
    cv.fill((ty == 12) | (ty == 13), INK, 0.45)
    cv.fill((ty >= 3) & (ty <= 3) & (xx % 16 < 12), WOOD[2])
    hbeam(99, 105, LACQUER, 0.5)
    cv.fill((ty == 101) & ((xx % 32) < 30), GOLD[2])
    cv.fill((ty == 101) & ((xx % 8) == 3), GOLD[4])
    hbeam(152, 159, WOOD, 0.3)
    # posts (red lacquer) at x = 0 and 64 (wrapping)

    def posts(dx, dy):
        for px in (0, 64):
            m = m_rect(3 * W, 3 * H, dx + px - 3, dy + 12, dx + px + 3, dy + 159)
            shade(cv, m, LACQUER, mode="cyl", base=0.5, gain=1.0, clean=False)
            cap = m_rect(3 * W, 3 * H, dx + px - 4, dy + 12, dx + px + 4, dy + 15)
            cv.fill(cap, GOLD[3])
            cv.fill(top_edge(cap), GOLD[5])
            base = m_rect(3 * W, 3 * H, dx + px - 4, dy + 148, dx + px + 4, dy + 159)
            shade(cv, base, STONE, R=1, base=0.55, clean=False)
    T.rep(posts)
    # panel inner frame lines + faint cloud motif in plaster
    for x0 in (5, 69):
        fm = (xx % W >= x0 + 3) & (xx % W <= x0 + 52) & (ty >= 22) & (ty <= 92)
        cv.fill(border(fm), PLASTER[2])
        cv.fill(top_edge(fm) | left_edge(fm), PLASTER[1])
    return T.crop()


@prop("wall_plaster", 128, 160, repeat="x", **TILE)
def wall_plaster(state, f):
    W, H = 128, 160
    T = Tiler(W, H)
    cv, xx, yy = T.cv, T.xx, T.yy
    full = np.ones((3 * H, 3 * W), bool)
    ty = yy % H
    nz = T.noise(32, seed_of("wp"), 2)
    v = 0.74 + (nz - 0.5) * 0.14 - np.clip((18 - ty) / 8.0, 0, 1) * 0.3 - np.clip((ty - 104) / 20.0, 0, 1) * 0.12
    ramp_fill(cv, full, PLASTER, v)
    # a few water stains, flakes and hairline cracks
    st = (T.noise(16, seed_of("wp_st"), 2) > 0.72) & (ty > 20) & (ty < 124)
    cv.fill(st, PLASTER[4])
    flake = (T.noise(4, seed_of("wp_fl"), 1) > 0.9) & (ty > 30) & (ty < 120) & (nz > 0.5)
    cv.fill(flake, PLASTER[2])
    cv.fill(shift(flake, 1, 1) & ~flake & (ty < 121), PLASTER[5])
    g = rng("wp_cr")
    cracks = []
    for _ in range(3):
        x, y = int(g.integers(0, W)), int(g.integers(30, 100))
        pts = [(x, y)]
        for _s in range(7):
            x += int(g.integers(-1, 2))
            y += 1
            pts.append((x, y))
        cracks.append(pts)

    def draw_cracks(dx, dy):
        for pts in cracks:
            cv.fill(m_line(3 * W, 3 * H, [(px + dx, py + dy) for px, py in pts]), PLASTER[2])
    T.rep(draw_cracks)
    # cornice
    cv.fill(ty <= 7, WOOD[2])
    cv.fill(ty <= 1, WOOD[1])
    cv.fill((ty == 2), WOOD[4])
    cv.fill((ty >= 8) & (ty <= 9), INK, 0.4)
    # painted dado band
    dado = (ty >= 124) & (ty <= 151)
    cv.fill(dado, CLOTH_JADE[2])
    cv.fill(dado & (ty >= 146), CLOTH_JADE[1])
    cv.fill(ty == 124, GOLD[2])
    cv.fill(ty == 125, CLOTH_JADE[0])
    cv.fill((ty == 127) & (xx % 12 < 6), CLOTH_JADE[3])
    # skirting stones
    sk = ty >= 152
    ramp_fill(cv, sk, STONE, 0.45 + (T.noise(8, seed_of("wp_sk")) - 0.5) * 0.3)
    cv.fill(ty == 152, STONE[5])
    cv.fill(sk & (xx % 32 == 0), STONE[1])
    return T.crop()


@prop("wall_stone", 128, 160, repeat="xy", **TILE)
def wall_stone(state, f):
    W, H = 128, 160
    T = Tiler(W, H)
    cv, xx, yy = T.cv, T.xx, T.yy
    full = np.ones((3 * H, 3 * W), bool)
    cv.fill(full, STONE_DARK[0])
    g = rng("wall_stone")
    rows = []
    y = 0
    while y < H:
        hgt = int(g.integers(14, 22))
        if H - y - hgt < 12:
            hgt = H - y
        rows.append((y, hgt))
        y += hgt
    blocks = []
    for (ry, rh) in rows:
        x = int(g.integers(0, 30))
        start = x
        while x < start + W:
            bw = int(g.integers(18, 44))
            if start + W - (x + bw) < 14:
                bw = start + W - x
            blocks.append((x, ry, bw, rh, int(g.integers(0, 1 << 30))))
            x += bw
    nz = T.noise(8, seed_of("ws_n"), 2)
    moss_n = T.noise(16, seed_of("ws_m"), 2)

    def draw(dx, dy):
        for (bx, by, bw, bh, sd) in blocks:
            m = m_rect(3 * W, 3 * H, dx + bx, dy + by, dx + bx + bw - 2, dy + by + bh - 2)
            gg = np.random.default_rng(sd)
            # chipped corners and a nibbled edge
            for (cx, cy, sx, sy) in ((bx, by, 1, 1), (bx + bw - 2, by, -1, 1), (bx, by + bh - 2, 1, -1),
                                     (bx + bw - 2, by + bh - 2, -1, -1)):
                k = int(gg.integers(1, 4))
                for i in range(k):
                    for j in range(k - i):
                        yy_, xx_ = dy + cy + sy * i, dx + cx + sx * j
                        if 0 <= yy_ < 3 * H and 0 <= xx_ < 3 * W:
                            m[yy_, xx_] = False
            nib = border(m) & (nz > 0.72)
            m &= ~nib
            shade(cv, m, STONE_DARK, R=3, strength=2.4, base=0.52 + gg.uniform(-0.1, 0.08), gain=1.4, noise=nz,
                  namp=0.35, clean=False)
    T.rep(draw)
    # moss creeping from mortar joints on upper faces
    mortar = cv.rgb[..., 0] < STONE_DARK[0][0] + 2
    mossm = dilate(mortar) & ~mortar & (moss_n > 0.62)
    cv.fill(mossm & shift(mortar, 0, -1), MOSS[1])
    cv.fill(mossm & shift(mortar, 0, 1), MOSS[2])
    # damp drips
    drip = (T.noise(4, seed_of("ws_d")) > 0.8) & (nz > 0.5)
    cv.fill(drip & ~mortar, STONE_DARK[1])
    return T.crop()


# ------------------------------------------------------------------ floors
@prop("floor_wood", 128, 64, repeat="xy", **TILE)
def floor_wood(state, f):
    W, H = 128, 64
    T = Tiler(W, H)
    cv, xx, yy = T.cv, T.xx, T.yy
    g = rng("floor_wood")
    nz = T.noise(8, seed_of("fw_n"), 2)
    grain = T.noise(4, seed_of("fw_g"), 1)
    rows = [(r * 8, int(g.integers(0, W))) for r in range(H // 8)]

    def draw(dx, dy):
        for (ry, jx) in rows:
            joints = sorted({jx % W, (jx + int(g.integers(40, 80))) % W})
            segs = []
            for i, j in enumerate(joints):
                nxt = joints[(i + 1) % len(joints)] + (W if i + 1 == len(joints) else 0)
                segs.append((j, nxt))
            for (x0, x1) in segs:
                t = np.random.default_rng(seed_of("fwp", ry, x0)).uniform(-0.12, 0.12)
                m = m_rect(3 * W, 3 * H, dx + x0, dy + ry, dx + x1 - 1, dy + ry + 7)
                v = 0.52 + t + (nz - 0.5) * 0.04
                sub = m & (yy == dy + ry)
                v = v + np.where(sub, 0.22, 0)
                ramp_fill(cv, m, WOOD, v)
                gl = m & ((yy == dy + ry + 3) | (yy == dy + ry + 5)) & (T.noise(8, seed_of("fwl", ry, x0)) > 0.55)
                cv.fill(gl, WOOD[3])
                cv.fill(m & (yy == dy + ry + 7), WOOD[1])
                cv.fill(m & (xx == dx + x0), WOOD[1])
                cv.fill(m & (xx == dx + x0 + 1) & (yy > dy + ry), WOOD[4])
                for nxp in (x0 + 2, x1 - 3):
                    cv.put(dx + nxp, dy + ry + 2, WOOD[2])
                    cv.put(dx + nxp, dy + ry + 5, WOOD[2])
    T.rep(draw)
    return T.crop()


@prop("floor_stone", 128, 64, repeat="xy", **TILE)
def floor_stone(state, f):
    W, H = 128, 64
    T = Tiler(W, H)
    cv, xx, yy = T.cv, T.xx, T.yy
    cv.fill(np.ones((3 * H, 3 * W), bool), STONE[1])
    g = rng("floor_stone")
    nz = T.noise(8, seed_of("fs_n"), 2)
    blocks = []
    for r in range(4):
        ry = r * 16
        x = int(g.integers(0, 32))
        start = x
        while x < start + W:
            bw = int(g.integers(22, 40))
            if start + W - (x + bw) < 18:
                bw = start + W - x
            blocks.append((x, ry, bw, 16, int(g.integers(0, 1 << 30))))
            x += bw

    def draw(dx, dy):
        for (bx, by, bw, bh, sd) in blocks:
            m = m_rect(3 * W, 3 * H, dx + bx + 1, dy + by + 1, dx + bx + bw - 1, dy + by + bh - 1)
            for (cx, cy) in ((bx + 1, by + 1), (bx + bw - 1, by + 1), (bx + 1, by + bh - 1), (bx + bw - 1, by + bh - 1)):
                if 0 <= dy + cy < 3 * H and 0 <= dx + cx < 3 * W:
                    m[dy + cy, dx + cx] = False
            gg = np.random.default_rng(sd)
            shade(cv, m, STONE, R=2, strength=2.0, base=0.55 + gg.uniform(-0.1, 0.08), gain=1.2, noise=nz,
                  namp=0.25, clean=False)
    T.rep(draw)
    mortar = cv.rgb[..., 0] == STONE[1][0]
    moss = mortar & (T.noise(8, seed_of("fs_m"), 2) > 0.6)
    cv.fill(moss, MOSS[2])
    cv.fill(moss & (T.noise(2, seed_of("fs_m2")) > 0.6), MOSS[3])
    return T.crop()


@prop("floor_earth", 128, 64, repeat="xy", **TILE)
def floor_earth(state, f):
    W, H = 128, 64
    T = Tiler(W, H)
    cv, xx, yy = T.cv, T.xx, T.yy
    full = np.ones((3 * H, 3 * W), bool)
    nz = T.noise(32, seed_of("fe"), 2)
    nz2 = T.noise(4, seed_of("fe2"), 1)
    v = 0.5 + (nz - 0.5) * 0.14 + np.where(nz2 > 0.7, 0.12, 0) - np.where(nz2 < 0.28, 0.12, 0)
    ramp_fill(cv, full, EARTH, v)
    g = rng("fe_peb")
    pebbles = [(int(g.integers(0, W)), int(g.integers(0, H)), int(g.integers(0, 3))) for _ in range(34)]

    def draw(dx, dy):
        for (px, py, k) in pebbles:
            if k == 0:
                m = m_rect(3 * W, 3 * H, dx + px, dy + py, dx + px + 1, dy + py)
                cv.fill(m, STONE[4])
                cv.put(dx + px, dy + py + 1, EARTH[1])
                cv.put(dx + px + 1, dy + py + 1, EARTH[1])
            elif k == 1:
                cv.put(dx + px, dy + py, EARTH[5])
                cv.put(dx + px + 1, dy + py + 1, EARTH[1])
            else:
                m = m_line(3 * W, 3 * H, [(dx + px, dy + py), (dx + px + 3, dy + py + 1), (dx + px + 5, dy + py + 1)])
                cv.fill(m, EARTH[1])
    T.rep(draw)
    # a few straw bits
    straw = (T.noise(2, seed_of("fe_s")) > 0.86) & (nz > 0.5)
    cv.fill(straw & (xx % 3 != 0), STRAW[3])
    return T.crop()


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


@prop("shallow_water", 128, 64, states=(("idle", 4, 5),), repeat="xy", **TILE)
def shallow_water(state, f):
    return water_frame(f, shallow=True)


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


@prop("hanging_lantern", 12, 24, kind="tile", ground=0, anchor=(6, 0))
def hanging_lantern(state, f):
    W, H = 12, 24
    cv = Canvas(W, H)
    cv.fill(m_rect(W, H, 6, 0, 6, 4), INK)
    cv.fill(m_rect(W, H, 4, 4, 8, 5), GOLD[3])
    lantern(cv, 6, 5, 8, 11, lit=True, cord=0)
    cv.fill(m_rect(W, H, 4, 16, 8, 16), GOLD[3])
    cv.fill(m_rect(W, H, 5, 17, 7, 17), GOLD[4])
    for x in (5, 6, 7):
        cv.fill(m_rect(W, H, x, 18, x, 21 + (x == 6)), CLOTH_RED[4] if x != 6 else CLOTH_RED[3])
    outline(cv)
    glow(cv, 6, 10.5, 6, 7, hexc("#ffb060"), steps=((1.0, 0.14), (0.7, 0.18)), m_limit=~cv.solid)
    return cv
