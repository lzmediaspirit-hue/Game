"""Natural treasures (Part 5 economy): the Nine-Bough Jade Tree, the Evergreen Heart Tree, the rich
earth it is planted in, and the Mindwell Lotus. Same conventions as defs_scenery: short hue-shifted
ramps, light from the upper left, `finish()` for the ink outline."""
from __future__ import annotations

import math

import numpy as np

from palette import BRIGHT_JADE, PALE_GOLD, SOUL_VIOLET, WATER, hexc
from parts import herb_sparkle, motes
from pixlib import Canvas, dilate, grid, m_ellipse, m_line, m_poly, m_rect, outline, rng, sparkle, top_edge
from registry import prop
from defs_scenery import R, bark, cshadow, finish, leaf_clump, thick_line

JADE_BARK = R("#1f2825", "#3b4741", "#5b6a5f", "#83927f", "#b0bca4")
JADE_LEAF = R("#0c3a36", "#136058", "#1f8a78", "#3fb89a", "#86e0c4", "#d2fbea")
EVER = R("#0f2e22", "#1a4a31", "#2a6a3e", "#43894a", "#6fae5a")
EVER_BARK = R("#231812", "#3e2a1d", "#5f412b", "#86603d")
HEART = R("#4a0f16", "#8a1d22", "#c4322c", "#ec6a4a", "#ffc2a0")
EARTH = R("#1b120c", "#2f2016", "#4a3322", "#6a4a31")
PEBBLE = R("#2e3634", "#4d5956", "#75827c", "#a3aea5")
LOTUS = R("#4b3a78", "#7a62b4", "#b39ae0", "#e2d6fb", "#fbf7ff")
PAD = R("#0b2226", "#123a3a", "#1d5a4e", "#2f7d62", "#55a17a")


@prop("nine_bough_jade_tree", 120, 160, states=(("idle", 4, 5),))
def nine_bough_jade_tree(state, f):
    """An ancient silver-barked tree with nine boughs of jade leaves; jade motes drift up from it."""
    W, H = 120, 160
    cv = Canvas(W, H)
    g = rng("nine_bough_jade_tree")
    gy = 157
    cshadow(cv, 60, gy, 34, 2.4)
    spine = [(58, gy), (56, 132), (62, 112), (58, 92), (61, 74)]
    wood = thick_line(W, H, spine, 12, 6)
    wood |= m_poly(W, H, [(42, gy), (76, gy), (66, gy - 7), (50, gy - 7)])
    # nine boughs, alternating sides, climbing the trunk
    boughs = [(0.30, -1, 40, -0.35), (0.34, 1, 38, -0.30), (0.46, -1, 34, -0.62), (0.50, 1, 36, -0.55),
              (0.62, -1, 30, -0.85), (0.66, 1, 30, -0.80), (0.78, -1, 24, -1.10), (0.82, 1, 24, -1.05),
              (0.98, 0, 20, -1.57)]
    ends = []
    for (t, side, ln, ang) in boughs:
        y0 = gy - (gy - 74) * t
        x0 = 58 + (1 if side >= 0 else -1) * 2
        a = ang if side >= 0 else math.pi - ang
        a = -abs(math.sin(ang)) if side == 0 else a
        if side == 0:
            x1, y1 = 61, y0 - ln
        else:
            x1 = x0 + side * math.cos(abs(ang)) * ln
            y1 = y0 - math.sin(abs(ang)) * ln * 0.9
        mx, my = (x0 + x1) / 2 + g.uniform(-2, 2), (y0 + y1) / 2 - 3
        wood |= thick_line(W, H, [(x0, y0), (mx, my), (x1, y1)], 5, 2)
        ends.append((x1, y1))
    bark(cv, wood, JADE_BARK, "jade_bark", gain=0.9)
    # jade canopy: one clump per bough end, back ones first
    for i, (x, y) in sorted(enumerate(ends), key=lambda e: e[1][1]):
        leaf_clump(cv, x, y - 2, 13 + (i % 3), 8 + (i % 2), JADE_LEAF, "nb%d" % i, lvl=0.3, lit=0.2 if x < 60 else -0.3)
    # hanging jade drops that catch the light
    for i, (x, y) in enumerate(ends):
        px, py = int(round(x + (-3 if i % 2 else 3))), int(round(y + 6))
        cv.fill(m_rect(W, H, px, py, px, py + 1), JADE_LEAF[5 if (i + f) % 4 == 0 else 4])
    finish(cv, JADE_LEAF, JADE_BARK)
    motes(cv, 20, 8, 100, 90, f, 4, "nine_bough", count=9, pal=(BRIGHT_JADE, hexc("#d2fbea")))
    sx, sy = ends[(f * 2) % len(ends)]
    sparkle(cv, int(round(sx)), int(round(sy - 6)), 2, hexc("#fffbea"), BRIGHT_JADE, 0.9)
    return cv


@prop("evergreen_heart_tree", 80, 120, states=(("idle", 1, 0), ("fruit", 4, 4)))
def evergreen_heart_tree(state, f):
    """A young evergreen with tiered needles; in season a crimson heart-shaped fruit glows under it."""
    W, H = 80, 120
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 117
    cshadow(cv, 40, gy, 20, 2.0)
    trunk = thick_line(W, H, [(40, gy), (39, 96), (41, 70)], 8, 4)
    trunk |= m_poly(W, H, [(32, gy), (48, gy), (44, gy - 4), (36, gy - 4)])
    bark(cv, trunk, EVER_BARK, "ever_bark")
    n = len(EVER)
    tiers = [(40, 92, 30, 9), (40, 76, 26, 9), (41, 60, 21, 8), (41, 45, 16, 8), (42, 31, 11, 7), (42, 19, 6, 6)]
    for i, (cx, cy, rx, ry) in enumerate(tiers):
        tm = m_poly(W, H, [(cx - rx, cy + ry * 0.5), (cx - rx * 0.4, cy - ry * 0.4), (cx, cy - ry * 1.2),
                           (cx + rx * 0.45, cy - ry * 0.4), (cx + rx, cy + ry * 0.5), (cx, cy + ry * 0.9)])
        tm |= m_ellipse(W, H, cx, cy + ry * 0.35, rx * 0.9, ry * 0.55)
        d = (xx - cx) / max(1, rx) + (yy - cy) / max(1, ry) * 0.7
        v = (n - 1) * 0.55 - d * 1.4 + (i * 0.1)
        needles = ((xx + yy * 2) % 4 == 0) & (yy > cy)
        v = v - needles * 0.9
        cv.fill_idx(tm, np.clip(np.floor(v), 0, n - 1).astype(int), EVER)
        cv.fill(top_edge(tm) & (xx < cx), EVER[-1])
    if state == "fruit":
        # the heart fruit hangs from the lowest tier
        hx, hy = 48, 100
        stem = m_line(W, H, [(hx - 1, 94), (hx, hy - 3)])
        cv.fill(stem, EVER_BARK[2])
        heart = m_ellipse(W, H, hx - 2, hy - 1, 2.6, 2.4) | m_ellipse(W, H, hx + 2, hy - 1, 2.6, 2.4)
        heart |= m_poly(W, H, [(hx - 4.6, hy), (hx + 4.6, hy), (hx, hy + 5)])
        cv.fill(heart, HEART[2])
        cv.fill(heart & (xx < hx) & (yy < hy), HEART[3])
        cv.fill(heart & (xx > hx + 1) & (yy > hy + 1), HEART[1])
        cv.put(hx - 2, hy - 2, HEART[4])
    finish(cv, EVER, EVER_BARK, HEART)
    if state == "fruit":
        pulse = (0.18, 0.30, 0.42, 0.30)[f % 4]
        ring = dilate(dilate(m_ellipse(W, H, 48, 100, 5, 5))) & (cv.a < 0.5)
        cv.fill(ring, HEART[3], pulse)
        sparkle(cv, 46 + (f % 2) * 4, 96 + (f // 2) * 2, 1, hexc("#fff4e0"), PALE_GOLD, 0.9)
    return cv


@prop("treasure_plot", 48, 16, ground=1)
def treasure_plot(state, f):
    """Rich dark earth ringed with river pebbles, waiting for a rare seed."""
    W, H = 48, 16
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    g = rng("treasure_plot")
    soil = m_ellipse(W, H, 24, 10, 19, 4.5)
    d = (xx - 24) / 19 + (yy - 10) / 4.5
    cv.fill_idx(soil, np.clip(np.floor(2.2 - d * 1.2), 0, 3).astype(int), EARTH)
    for k in range(9):
        cv.put(int(g.integers(10, 38)), int(g.integers(8, 13)), EARTH[3])
    # a ring of pebbles
    for k in range(14):
        a = k / 14 * math.tau
        px, py = 24 + math.cos(a) * 20, 10 + math.sin(a) * 5
        pm = m_ellipse(W, H, px, py, 2.2, 1.4)
        cv.fill(pm, PEBBLE[1 + (k % 3)])
        cv.put(int(round(px - 1)), int(round(py - 1)), PEBBLE[3])
    # a jade marker stone at the back
    stone = m_poly(W, H, [(21, 7), (27, 7), (26, 1), (22, 1)])
    cv.fill(stone, JADE_LEAF[2])
    cv.fill(stone & (xx < 23), JADE_LEAF[3])
    cv.put(24, 3, JADE_LEAF[5])
    finish(cv, EARTH, PEBBLE, JADE_LEAF)
    return cv


@prop("mindwell_lotus_patch", 32, 16, states=(("ready", 3, 5), ("depleted", 1, 0)), ground=3)
def mindwell_lotus_patch(state, f):
    """A pale violet lotus that opens over still water; soul-light rises from its heart."""
    W, H = 32, 16
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ring = m_ellipse(W, H, 16, 12.5, 15, 2.6)
    cv.fill(ring, WATER[3], 0.55)
    cv.fill(ring & (yy == 13) & ((xx % 5) < 2), WATER[6], 0.6)
    for (cx, cy, rx, ry) in ((8, 12.5, 6.5, 2.0), (24, 12.5, 6.0, 1.9), (16, 13.5, 4.5, 1.5)):
        pm = m_ellipse(W, H, cx, cy, rx, ry)
        cv.fill(pm, PAD[2])
        cv.fill(pm & (yy < cy), PAD[3])
        cv.fill(top_edge(pm), PAD[4])
    if state == "ready":
        petals = [((13, 11), (10, 5), (15, 9)), ((19, 11), (22, 5), (17, 9)), ((14, 11), (16, 2), (18, 11)),
                  ((12, 12), (8, 8), (14, 10)), ((20, 12), (24, 8), (18, 10))]
        cols = [LOTUS[2], LOTUS[2], LOTUS[3], LOTUS[1], LOTUS[1]]
        for pts, c in zip(petals, cols):
            cv.fill(m_poly(W, H, list(pts)), c)
        cv.fill(m_rect(W, H, 15, 8, 17, 9), LOTUS[4])
        cv.put(16, 2, LOTUS[4])
    else:
        cv.fill(m_rect(W, H, 16, 10, 16, 11), PAD[1])
    outline(cv, skip=ring & ~dilate(cv.solid, diag=True))
    if state == "ready":
        motes(cv, 10, 0, 22, 9, f, 3, "mindwell", count=4, pal=(SOUL_VIOLET, hexc("#ece0ff")))
        herb_sparkle(cv, f, [(16, 2), (11, 6), (21, 6)], c1=hexc("#c4aaee"), c2=hexc("#ffffff"))
    return cv
