"""Act II (Azure Expanse) props: sky-ships moored at the Cloudgate docks, herders' felt yurts on the
Thunderhorn Plains, lightning-split storm menhirs and the Nine Peaks Alliance banner. Same
conventions as the other defs modules: short hue-shifted ramps, light from the upper left, dark
outline, deterministic noise."""
from __future__ import annotations

import math

import numpy as np

from palette import *  # noqa: F401,F403
from parts import grass_tuft, ground_shadow, lantern, plank_h, plank_v, rock, rope_band, smoke
from pixlib import (Canvas, bottom_edge, erode, glow, grid, hexc, left_edge, m_ellipse, m_line, m_poly, m_rect,
                    outline, right_edge, shade, shift, sparkle, top_edge, vnoise)
from registry import prop

SAIL = ramp("#4a4232", "#7a6e55", "#a89a7a", "#cfc2a0", "#ece2c4", "#fbf5e2")
FELT = ramp("#4b4234", "#776952", "#a39578", "#c7b99a", "#e2d6b8", "#f5eedb")
QI_MIST = ramp("#1b5a6e", "#2f86a0", "#58b6cc", "#94dbe6", "#d6f6fa")
RUNE = ramp("#0f3d63", "#1f6fa8", "#48a8e8", "#8fd8ff", "#e6f8ff")


# ------------------------------------------------------------------ sky-ship
@prop("sky_ship", 192, 112, states=(("idle", 4, 4),))
def sky_ship(state, f):
    """A cultivator's junk that sails the sky roads: batten sails, a stern hall, a painted eye at the
    bow and a cushion of Qi mist under the keel. Two mooring ropes tie it to posts on the ground."""
    W, H = 192, 112
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    bob = (0, -1, -1, 0)[f % 4]
    gy = 109
    # mooring posts and ropes (drawn first, the hull covers the rope ends)
    for px in (36, 156):
        ground_shadow(cv, px, gy, 6, 1.2)
        plank_v(cv, px - 2, 94, px + 1, gy, WOOD, grain=False, seed=("mp", px))
        cv.fill(m_rect(W, H, px - 3, 93, px + 2, 94), IRON[3])
    for (x0, x1) in ((37, 52), (155, 142)):
        cv.fill(m_line(W, H, [(x0, 95), ((x0 + x1) / 2, 88 + bob), (x1, 78 + bob)], 1), ROPE[3])
    # Qi cushion under the keel: three soft lobes that drift a pixel each frame
    for i, (cx, rx) in enumerate(((70, 22), (100, 26), (132, 20))):
        dx = ((f + i) % 4) - 1.5
        lobe = m_ellipse(W, H, cx + dx, 90, rx, 5) & ~m_ellipse(W, H, cx + dx, 96, rx - 4, 3)
        cv.fill(lobe, QI_MIST[2], 0.55)
        cv.fill(lobe & (yy <= 87), QI_MIST[3], 0.6)
    y0 = 58 + bob
    # hull: a junk with a high stern castle (left) and a lifted bow (right)
    top = []
    bot = []
    for x in range(12, 184):
        t = (x - 12) / 171.0
        ty = y0 - 12 * max(0.0, (0.2 - t) / 0.2) ** 1.2 - 8 * max(0.0, (t - 0.84) / 0.16) ** 1.4
        by = y0 + 22 - 8 * max(0.0, (0.14 - t) / 0.14) ** 1.3 - 14 * max(0.0, (t - 0.78) / 0.22) ** 1.5
        top.append((x, ty))
        bot.append((x, by))
    hull = m_poly(W, H, top + list(reversed(bot)))
    nz = vnoise(W, H, 4, 913, 2)
    shade(cv, hull, WOOD, contour=True, R=2, base=0.42, gain=1.1, noise=nz, namp=0.2)
    for k in (5, 10, 15):   # strakes
        seam = m_poly(W, H, [(x, y + k) for x, y in top] + [(x, y + k + 0.8) for x, y in reversed(top)])
        cv.fill(seam & hull & erode(hull), WOOD[1])
    # lacquered band under the gunwale and the gunwale rail
    band = m_poly(W, H, [(x, y + 1.5) for x, y in top] + [(x, y + 4.5) for x, y in reversed(top)]) & hull
    shade(cv, band, LACQUER, R=1, base=0.5, gain=0.8)
    cv.fill(band & ((xx % 12) == 0), GOLD[4])
    rail = m_poly(W, H, [(x, y - 1) for x, y in top] + [(x, y + 1.2) for x, y in reversed(top)])
    shade(cv, rail, WOOD, R=1, base=0.7, gain=0.8)
    cv.fill(top_edge(rail), WOOD[6])
    # the painted eye on the bow
    ex, ey = 170, int(y0 + 6)
    cv.fill(m_ellipse(W, H, ex, ey, 3.5, 2.5), PAPER_R[5])
    cv.fill(m_ellipse(W, H, ex + 0.5, ey, 1.5, 1.5), INK)
    cv.put(ex, ey - 1, PAPER_R[5])
    # stern hall on the castle: posts, a lit window and a curled roof
    hy = int(y0 - 12)
    hall = m_rect(W, H, 22, hy - 12, 50, hy)
    shade(cv, hall, LACQUER, contour=True, R=1, base=0.45, gain=0.7)
    for wx in (26, 34, 42):
        cv.fill(m_rect(W, H, wx, hy - 9, wx + 4, hy - 4), GLAZE_AMBER[5])
        cv.fill(m_rect(W, H, wx + 2, hy - 9, wx + 2, hy - 4), LACQUER[1])
    roof = m_poly(W, H, [(16, hy - 11), (22, hy - 17), (50, hy - 17), (56, hy - 11), (54, hy - 12), (36, hy - 14), (18, hy - 12)])
    roof |= m_rect(W, H, 20, hy - 20, 52, hy - 16)
    roof |= m_poly(W, H, [(24, hy - 20), (36, hy - 25), (48, hy - 20)])
    shade(cv, roof, ROOF, contour=True, R=2, base=0.5, gain=1.2, top=0.2)
    cv.fill(top_edge(roof), ROOF[6])
    cv.fill(m_rect(W, H, 35, hy - 27, 36, hy - 25), GOLD[5])
    # masts and batten sails (main and fore), the battens bow a little in the wind
    for (mx, mtop, sx0, sx1, st, sb) in ((86, 6, 62, 104, 10, int(y0 - 3)), (132, 18, 114, 146, 22, int(y0 - 5))):
        plank_v(cv, mx - 1, mtop, mx + 1, int(y0), WOOD, grain=False, seed=("mast", mx))
        pts = [(sx0 + 3, st), (sx1 - 1, st + 2), (sx1 + 2, sb), (sx0 - 2, sb)]
        sail = m_poly(W, H, pts)
        bow_f = np.clip((xx - sx0) / max(1, sx1 - sx0), 0, 1)
        shade(cv, sail, SAIL, contour=True, R=2, base=0.5, gain=1.1, bias=-(bow_f - 0.4) * 0.25)
        for by in range(st + 6, sb, 7):
            batten = m_line(W, H, [(sx0 - 1, by), ((sx0 + sx1) / 2, by + 1.5), (sx1 + 1, by)], 1) & sail
            cv.fill(batten, WOOD[2])
            cv.fill(shift(batten, 0, 1) & sail & ~batten, SAIL[5])
        cv.fill(m_line(W, H, [(mx, mtop), (sx1 + 2, sb)], 1) & ~sail, ROPE[2])
        # pennant at the masthead
        pen = m_poly(W, H, [(mx + 1, mtop), (mx + 10 + (f % 2), mtop + 2), (mx + 1, mtop + 4)])
        cv.fill(pen, CLOTH_BLUE[4])
        cv.fill(bottom_edge(pen), CLOTH_BLUE[2])
    # lanterns at stern and bow
    lantern(cv, 14, int(y0 - 10), 4, 5, lit=True, flick=f, cord=2)
    lantern(cv, 180, int(y0 - 6), 4, 5, lit=True, flick=f + 1, cord=2)
    outline(cv)
    glow(cv, 16, int(y0 - 6), 6, 6, hexc("#ffb060"), steps=((1.0, 0.14),))
    glow(cv, 182, int(y0 - 2), 6, 6, hexc("#ffb060"), steps=((1.0, 0.14),))
    glow(cv, 100, 92, 70, 10, QI_CYAN, steps=((1.0, 0.08), (0.7, 0.07)))
    return cv


# ------------------------------------------------------------------ herder's yurt
@prop("herder_yurt", 88, 64)
def herder_yurt(state, f):
    """A round felt yurt of the plains herders: lattice wall, domed roof bound with rope, a patterned
    band, a red door with brass studs and a thread of smoke from the crown ring."""
    W, H = 88, 64
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 61
    ground_shadow(cv, 44, gy, 40, 1.8)
    wall = m_rect(W, H, 8, 34, 79, gy - 1)
    shade(cv, wall, FELT, contour=True, mode="cyl", R=2, base=0.45, gain=1.0)
    # faint lattice seen through the felt
    lat = wall & (((xx + yy) % 8 == 0) | ((xx - yy) % 8 == 0)) & (yy > 38)
    cv.fill(lat & (xx < 50), FELT[2], 0.3)
    dome = m_ellipse(W, H, 44, 36, 40, 25) & (yy <= 36)
    shade(cv, dome, FELT, contour=True, R=3, base=0.55, gain=1.2, top=0.2)
    # patterned band where roof meets wall
    band = m_rect(W, H, 7, 33, 80, 37)
    cv.fill(band, CLOTH_BLUE[2])
    cv.fill(band & (yy == 33), CLOTH_BLUE[4])
    cv.fill(band & (yy == 35) & ((xx % 6) < 3), CLOTH_RED[4])
    cv.fill(band & (yy == 35) & ((xx % 6) >= 3), GOLD[4])
    # roof ropes radiating from the crown ring
    for ang in (-60, -30, 0, 30, 60):
        a = math.radians(ang)
        x1 = 44 + math.sin(a) * 38
        cv.fill(m_line(W, H, [(44 + math.sin(a) * 5, 14), (x1, 33)], 1) & dome, ROPE[2])
    rope_band(cv, 9, 78, 46, ROPE)
    # crown ring
    crown = m_ellipse(W, H, 44, 12, 7, 2.5)
    shade(cv, crown, WOOD, contour=True, R=1, base=0.55)
    cv.fill(m_ellipse(W, H, 44, 11.5, 4, 1.2), WOOD[0])
    # door
    door = m_rect(W, H, 38, 42, 50, gy - 1)
    shade(cv, door, LACQUER, contour=True, R=1, base=0.55, gain=0.8)
    cv.fill(m_rect(W, H, 44, 43, 44, gy - 2), LACQUER[1])
    for sy in (46, 52, 57):
        cv.put(40, sy, GOLD[5])
        cv.put(48, sy, GOLD[5])
    cv.fill(m_rect(W, H, 36, 40, 52, 41), WOOD[4])
    outline(cv)
    smoke(cv, 44, 9, f, 1, height=10, seed="yurt", count=2, drift=1.5, size=1.2, alpha=0.5)
    return cv


# ------------------------------------------------------------------ storm menhir
@prop("storm_menhir", 32, 80, states=(("idle", 4, 5),))
def storm_menhir(state, f):
    """A standing stone split top to bottom by an old strike; runes along the crack still hold the
    lightning, and every few breaths an arc jumps between the halves."""
    W, H = 32, 80
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 77
    ground_shadow(cv, 16, gy, 14, 1.6)
    left = m_poly(W, H, [(5, gy), (6, 24), (9, 10), (14, 5), (15, 20), (13, 40), (15, 58), (14, gy)])
    right = m_poly(W, H, [(17, gy), (18, 58), (16, 40), (18, 20), (19, 8), (23, 14), (26, 30), (27, gy)])
    nz = vnoise(W, H, 3, 4417, 2)
    shade(cv, left, STONE_DARK, contour=True, R=2, base=0.55, gain=1.3, noise=nz, namp=0.3)
    shade(cv, right, STONE_DARK, contour=True, R=2, base=0.4, gain=1.1, noise=nz, namp=0.3)
    cv.fill(left_edge(left) & (yy < gy - 2), STONE[4])
    # runes on both faces
    lit = (f % 4) in (1, 2)
    for i, ry in enumerate(range(22, 70, 9)):
        for (rx, m) in ((10 if i % 2 else 9, left), (22 if i % 2 else 21, right)):
            # a trigram: three short bars, the broken ones split in the middle
            glyph = np.zeros((H, W), bool)
            for k in range(3):
                bar = m_rect(W, H, rx - 1, ry + k * 2, rx + 1, ry + k * 2)
                if (i + k) % 2:
                    bar &= ~m_rect(W, H, rx, ry + k * 2, rx, ry + k * 2)
                glyph |= bar
            glyph &= erode(m)
            cv.fill(glyph, RUNE[3] if lit else RUNE[2])
    # rubble and grass at the foot
    for i, (rx, rr) in enumerate(((4, 3), (28, 3.5), (21, 2))):
        rock(cv, rx, gy, rr, rr * 0.8, ("menhir", i), pal=STONE, R=1, facets=1)
    grass_tuft(cv, 9, gy, "mh_g1", h=4, n=3)
    grass_tuft(cv, 25, gy, "mh_g2", h=3, n=2)
    outline(cv)
    # the arc across the split
    if f % 4 == 2:
        arc = m_line(W, H, [(14, 18), (17, 22), (15, 27), (18, 31), (16, 36)], 1)
        cv.fill(arc, RUNE[4])
        sparkle(cv, 16, 18, 2, hexc("#ffffff"), RUNE[3], 0.9)
    glow(cv, 16, 40, 10, 28, RUNE[2], steps=((1.0, 0.06 + (0.06 if lit else 0.0)),))
    return cv


# ------------------------------------------------------------------ Nine Peaks Alliance banner
@prop("banner_alliance", 24, 64)
def banner_alliance(state, f):
    """The Nine Peaks Alliance standard: deep navy silk, gold trim and a three-summit mark that stands
    for the nine peaks."""
    W, H = 24, 64
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    navy = ramp("#0b1226", "#16213f", "#223260", "#2f4580", "#4460a0", "#6a86bf")
    ground_shadow(cv, 12, 62, 8, 1.3)
    plank_h(cv, 6, 57, 17, 61, STONE, grain=False)
    plank_v(cv, 11, 3, 12, 57, LACQUER, grain=False)
    cv.fill(m_rect(W, H, 10, 1, 13, 2), GOLD[4])
    plank_h(cv, 3, 5, 20, 6, LACQUER, grain=False, base=0.6)
    pts_l = [(4 + math.sin(y * 0.25) * 0.8, y) for y in range(7, 48)]
    pts_r = [(19 + math.sin(y * 0.25 + 0.6) * 0.8, y) for y in range(47, 6, -1)]
    ban = m_poly(W, H, pts_l + [(4, 50), (11.5, 45), (19, 50)] + pts_r)
    shade(cv, ban, navy, contour=True, mode="cyl", base=0.55, gain=0.9, bias=np.sin(yy * 0.25) * 0.12)
    cv.fill(ban & ((xx == 5) | (xx == 18)) & (yy < 46), GOLD[3])
    cv.fill(ban & (yy == 8), GOLD[4])
    # three summits, the middle one tallest, over a ring of nine dots
    peaks = m_poly(W, H, [(6, 24), (9, 17), (11, 20), (12, 13), (14, 20), (15, 17), (18, 24)])
    cv.fill(peaks, GOLD[4])
    cv.fill(left_edge(peaks), GOLD[6])
    for k in range(9):
        a = math.pi * (0.1 + 0.8 * k / 8.0)
        cv.put(int(round(12 - math.cos(a) * 5)), int(round(30 + math.sin(a) * 3)), GOLD[5])
    for k in range(2):
        cv.fill(m_rect(W, H, 9, 36 + k * 4, 14, 36 + k * 4), GOLD[3])
    for tx in (3, 20):
        cv.fill(m_rect(W, H, tx, 7, tx, 11), CLOTH_BLUE[4])
        cv.put(tx, 12, GOLD[4])
    outline(cv)
    return cv


# ------------------------------------------------------------------ Phase B: Rimefrost and Mirrorwater
from defs_nature import HERB_STATES, cut_stems  # noqa: E402

FROST_PETAL = ramp("#5b6f9a", "#8fa6cf", "#bfd2ef", "#e4eefb", "#ffffff")
ICE = ramp("#2c4c6e", "#4a78a2", "#7fb0d6", "#b8dcf2", "#e8f7ff")


@prop("frost_lotus_patch", 28, 22, states=HERB_STATES)
def frost_lotus_patch(state, f):
    """A lotus that blooms in snow: a cup of ice-blue petals over frosted leaves on a snow mound."""
    W, H = 28, 22
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ground_shadow(cv, 14, 20, 12, 1.4)
    for (cx, cy, rx) in ((7, 17, 6), (21, 17, 6), (14, 18, 7)):
        leaf = m_ellipse(W, H, cx, cy, rx, 2.2)
        shade(cv, leaf, LEAF_BLUE, contour=True, R=1, base=0.5, gain=1.0)
        cv.fill(top_edge(leaf) & ((xx % 3) != 0), hexc("#e8f2f6"))
    mound = m_ellipse(W, H, 14, 20, 11, 2.0) & (yy >= 19)
    shade(cv, mound, ramp("#9fb3c8", "#c6d4e2", "#e3ebf2", "#f7fafc"), R=1, base=0.6, gain=0.6)
    if state == "ready":
        # outer petals first, then the inner cup; each petal is a pointed oval
        for k, (x0, x1, tip, ty) in enumerate(((5, 12, 6, 9), (16, 23, 22, 9), (8, 14, 10, 6), (14, 20, 18, 6),
                                               (11, 17, 14, 4))):
            pm = m_poly(W, H, [(x0, 16), ((x0 + tip) / 2 - 1, (16 + ty) / 2), (tip, ty), ((x1 + tip) / 2 + 1, (16 + ty) / 2), (x1, 16)])
            cv.fill(pm, FROST_PETAL[2 + (k % 2)] if k < 4 else FROST_PETAL[4])
            cv.fill(left_edge(pm), FROST_PETAL[4])
            cv.fill(right_edge(pm) & ~left_edge(pm), FROST_PETAL[1])
        cv.fill(m_rect(W, H, 13, 13, 15, 15), GOLD[5])
    else:
        cut_stems(cv, [(14, 16)], pal=LEAF_BLUE, h=2)
    outline(cv)
    if state == "ready":
        sparkle(cv, [8, 20, 14][f % 3], [8, 8, 3][f % 3], 1, hexc("#ffffff"), FROST_PETAL[3], 0.9)
        glow(cv, 14, 11, 9, 6, hexc("#bfe2ff"), steps=((1.0, 0.08),))
    return cv


@prop("icicle_rock", 56, 44)
def icicle_rock(state, f):
    """A boulder under a thick snow cap, hung with icicles along the cap's lip."""
    W, H = 56, 44
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 41
    ground_shadow(cv, 28, gy, 26, 1.8)
    m = rock(cv, 28, gy, 24, 16, "icicle_rock", pal=STONE, R=3, base=0.5, facets=3)
    cols = np.where(m.any(axis=0))[0]
    lip = {}
    for x in cols:
        ys = np.where(m[:, x])[0]
        d = 5 + (1 if (x * 7) % 5 < 2 else 0)
        lip[int(x)] = int(ys[0]) + d
        cap = m & (xx == x) & (yy < ys[0] + d)
        cv.fill(cap, hexc("#e4edf4") if x > 28 else hexc("#f4f8fb"))
        cv.fill(cap & (yy == ys[0] + d - 1), hexc("#b9c9d8"))
    cv.fill(top_edge(m), hexc("#ffffff"))
    for k, x in enumerate(range(int(cols.min()) + 4, int(cols.max()) - 3, 4)):
        y0 = lip.get(x, 20)
        ln = 3 + (k * 5) % 5
        ic = m_poly(W, H, [(x - 1, y0), (x + 1, y0), (x, y0 + ln)])
        cv.fill(ic, ICE[3])
        cv.put(x - 1, y0, ICE[4])
    outline(cv)
    return cv


@prop("lotus_lantern", 20, 16, states=(("idle", 4, 4),), ground=3)
def lotus_lantern(state, f):
    """A paper lotus lantern floating on the lake, its candle breathing light onto the water."""
    W, H = 20, 16
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ring = m_ellipse(W, H, 10, 13.5, 9, 1.8)
    cv.fill(ring, WATER[4], 0.5)
    base = m_ellipse(W, H, 10, 12, 7, 2)
    shade(cv, base, LEAF_BLUE, R=1, base=0.5, gain=0.8)
    for k, (x0, x1, tip) in enumerate(((4, 9, 6), (11, 16, 14), (7, 13, 10))):
        pm = m_poly(W, H, [(x0, 12), (tip, 4 + (k == 2) * -1), (x1, 12)])
        cv.fill(pm, hexc("#f4c7d6") if k != 2 else hexc("#fbe3ea"))
        cv.fill(left_edge(pm), hexc("#fff3f7"))
    outline(cv, skip=ring & ~cv.solid)
    flick = (0.16, 0.22, 0.18, 0.24)[f % 4]
    glow(cv, 10, 9, 7, 6, hexc("#ffd28a"), steps=((1.0, flick),))
    cv.fill(m_rect(W, H, 9 + (f % 2), 14, 11, 14) & ~cv.solid, hexc("#ffe6a8"), 0.5)
    return cv
