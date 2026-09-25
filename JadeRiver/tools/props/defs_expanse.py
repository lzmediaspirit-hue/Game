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


# ------------------------------------------------------------------ Phase D: the Sunscar Desert and the Tomb of Sunscar
from parts import blob_mask, herb_sparkle  # noqa: E402
from pixlib import bbox, border, dilate, ellipse_ring, rng, seed_of  # noqa: E402

DUNE = ramp("#5e3f2c", "#86603f", "#ab8454", "#c9a46c", "#dfbf88", "#f0d9a6")
SANDSTONE = ramp("#2b1a1d", "#4a2b27", "#6f4232", "#945d40", "#b57c52", "#cf9f6b", "#e6c38e")
BONE_SUN = ramp("#3b3a3c", "#65605a", "#948a7a", "#bdb39c", "#ddd5bd", "#f6f1e0")
CACTUS = ramp("#10302b", "#1a4838", "#276645", "#3f8550", "#6aa35d", "#a6c275", "#d8d9a0")
PALM_BARK = ramp("#24170f", "#3e2918", "#5d3f23", "#7d5a33", "#9c7746", "#bb9663")
PALM_LEAF = ramp("#0e2a22", "#17432d", "#255f35", "#3a7d3c", "#5e9c45", "#94bd5a", "#c9dc84")
DATE = ramp("#2e0f0a", "#5a1d10", "#8a3616", "#b95a22", "#e08a3a", "#f6c46a")
ROSEWOOD = ramp("#1a0d0f", "#321815", "#4f261d", "#6e3b27", "#8f5534", "#b0744a")
VERMILION = ramp("#3a1616", "#61251f", "#8a3a2a", "#ab5638", "#c67a52", "#dca27a")
MIRROR = ramp("#4a3a28", "#6f5a3c", "#978058", "#bba678", "#d8c89c", "#efe6c8", "#fffdf0")
EMBER = ramp("#7a1c10", "#b93a18", "#e8691e", "#ff9a30", "#ffc862", "#fff0b8")


def _spline(pts, step=0.5):
    """Catmull-Rom samples through pts, about `step` art px apart."""
    if len(pts) < 3:
        (x0, y0), (x1, y1) = pts[0], pts[-1]
        n = max(2, int(math.hypot(x1 - x0, y1 - y0) / step))
        return [(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n) for i in range(n + 1)]
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        seg = max(2, int(math.hypot(p2[0] - p1[0], p2[1] - p1[1]) / step))
        for s in range(seg):
            t = s / seg
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                                    + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in range(2)))
    out.append(tuple(pts[-1]))
    return out


def tube(W, H, pts, r0, r1=None):
    """Union of discs along a spline: a round limb, bone or stem whose radius runs from r0 to r1."""
    r1 = r0 if r1 is None else r1
    sp = _spline(pts)
    m = np.zeros((H, W), bool)
    for i, (x, y) in enumerate(sp):
        r = r0 + (r1 - r0) * i / max(1, len(sp) - 1)
        m |= m_ellipse(W, H, x, y, r, r)
    return m


def sand_heap(cv, cx, by, rx, ry, seed, rough=0.12, contour=True):
    """A drift of desert sand resting on row `by`, lit from the upper left, with a few wind ripples."""
    W, H = cv.w, cv.h
    m = blob_mask(W, H, cx, by, rx, ry, ("heap", seed), rough, flat_base=by)
    if not m.any():
        return m
    nz = vnoise(W, H, 3, seed_of("heapn", seed), 2)
    shade(cv, m, DUNE, contour=contour, contour_c=DUNE[2], R=2, strength=1.6, base=0.62, gain=1.1, noise=nz,
          namp=0.2, top=0.1)
    g = rng("ripple", seed)
    x0, y0, x1, y1 = bbox(m)
    for _ in range(max(1, (x1 - x0) // 9)):
        rx0 = int(g.integers(x0 + 1, max(x0 + 2, x1 - 3)))
        ry0 = int(g.integers(y0 + 2, max(y0 + 3, y1)))
        rip = m_line(W, H, [(rx0, ry0), (rx0 + 2, ry0 - 1), (rx0 + 4, ry0)]) & erode(m)
        cv.fill(rip, DUNE[2])
        cv.fill(shift(rip, 0, -1) & erode(m) & ~rip, DUNE[5])
    return m


def sand_drift(cv, by, profile, seed, contour=True):
    """A long drift of sand along row `by` whose height follows profile [(x, h), ...]; ends at h=0
    inside the frame so the drift never gets cut off at the sprite edge."""
    W, H = cv.w, cv.h
    yy = grid(W, H)[1]
    nz1 = vnoise(W, 1, 4, seed_of("drift1", seed), 1)[0]
    top = np.interp(np.arange(W), [p[0] for p in profile], [p[1] for p in profile])
    top = np.where(top > 0.5, top + (nz1 - 0.5) * 1.6, top)
    m = (yy <= by) & (yy >= by - top[None, :] + 0.5)
    nz = vnoise(W, H, 3, seed_of("driftn", seed), 2)
    shade(cv, m, DUNE, contour=contour, contour_c=DUNE[2], R=2, strength=1.6, base=0.62, gain=1.1, noise=nz,
          namp=0.2, top=0.1)
    g = rng("drift_rip", seed)
    x0, y0, x1, y1 = bbox(m)
    for _ in range(max(1, (x1 - x0) // 8)):
        rx0 = int(g.integers(x0 + 1, max(x0 + 2, x1 - 3)))
        ry0 = int(g.integers(y0 + 2, max(y0 + 3, y1)))
        rip = m_line(W, H, [(rx0, ry0), (rx0 + 2, ry0 - 1), (rx0 + 4, ry0)]) & erode(m)
        cv.fill(rip, DUNE[2])
        cv.fill(shift(rip, 0, -1) & erode(m) & ~rip, DUNE[5])
    return m


def _idx_fill(cv, m, pal, v):
    """Fill mask m with pal[round(v)] (v: float array or scalar of ramp indices)."""
    v = np.broadcast_to(np.asarray(v, float), m.shape)
    cv.fill_idx(m, np.clip(np.round(v), 0, len(pal) - 1), pal)


# ------------------------------------------------------------------ date palm
def _frond(cv, x0, y0, side, a0, L, g, sway, tone, pal=PALM_LEAF):
    """One pinnate frond: a rachis that arches out and droops, combed with leaflets hanging below it."""
    W, H = cv.w, cv.h
    top = len(pal) - 1
    n = int(L * 2)
    x, y = float(x0), float(y0)
    pts = []
    for i in range(n + 1):
        s = i / n
        a = a0 + g * s ** 1.4
        pts.append((x + sway * s * s, y, a, s))
        x += side * math.cos(a) * 0.5
        y += math.sin(a) * 0.5
    fc = Canvas(W, H)
    for k, (px, py, a, s) in enumerate(pts[::2]):
        if s < 0.08:
            continue
        ll = 0.6 + 4.2 * math.sin(math.pi * min(1.0, 0.12 + s * 0.92)) ** 0.9
        ll *= (1.0, 0.6)[k % 2]
        # lower leaflets comb down toward the tip, upper ones are short and catch the light
        b = a + 1.0
        dx, dy = side * math.cos(b), math.sin(b) + 0.6
        nn = math.hypot(dx, dy)
        fc.fill(m_line(W, H, [(px, py), (px + dx / nn * ll, py + dy / nn * ll)]),
                pal[max(0, tone - 1)] if k % 4 == 0 else pal[tone])
        b = a - 0.8
        fc.fill(m_line(W, H, [(px, py), (px + side * math.cos(b) * ll * 0.35, py + math.sin(b) * ll * 0.35)]),
                pal[min(top, tone + 1)])
    rach = m_line(W, H, [(p[0], p[1]) for p in pts[::2]])
    fc.fill(rach, pal[min(top, tone + 2)])
    m = fc.solid
    under = cv.solid & ~m
    touch = m & (shift(under, 1, 0) | shift(under, -1, 0) | shift(under, 0, 1) | shift(under, 0, -1)) & ~rach
    fc.fill(touch, pal[max(0, tone - 2)])
    cv.paste(fc)
    return m


@prop("palm_tree", 64, 96, states=(("idle", 3, 4),), ground=3)
def palm_tree(state, f):
    """A date palm of the Oasis of Bones: a leaning ringed trunk, a crown of drooping fronds and a
    heavy cluster of dates. The fronds sway a pixel or two in the desert wind."""
    W, H = 64, 96
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 93
    ground_shadow(cv, 30, gy, 17, 1.8)
    sw = (0.0, 1.0, -1.0)[f % 3]
    crown = (34.0, 26.0)
    # fronds behind the trunk top (the lower, shaded ones)
    for (side, a0, L, g, tone) in ((1, 0.35, 20, 1.2, 1), (-1, 0.4, 20, 1.2, 2), (1, -0.8, 18, 2.2, 1)):
        _frond(cv, crown[0], crown[1] + 1, side, a0, L, g, sw * 1.2, tone)
    # trunk: a quadratic curve from the root to the crown, leaning right
    P0, P1, P2 = (28.0, float(gy)), (25.0, 58.0), (crown[0], crown[1] + 2)
    rows = {}
    for i in range(600):
        t = i / 599
        x = (1 - t) ** 2 * P0[0] + 2 * (1 - t) * t * P1[0] + t * t * P2[0]
        y = (1 - t) ** 2 * P0[1] + 2 * (1 - t) * t * P1[1] + t * t * P2[1]
        rows.setdefault(int(round(y)), (x, t))
    trunk = np.zeros((H, W), bool)
    ring = np.zeros((H, W), bool)
    ring_hi = np.zeros((H, W), bool)
    for y, (x, t) in rows.items():
        hw = 3.4 - 1.2 * t + 3.0 * max(0.0, 1 - t / 0.07) ** 2
        r = (gy - y) % 4 == 1 and t > 0.05
        if r:
            hw += 0.6
        a, b = int(round(x - hw)), int(round(x + hw))
        trunk[y, a:b + 1] = True
        if r:
            ring[y, a:b + 1] = True
        if (gy - y) % 4 == 0 and t > 0.05:
            ring_hi[y, a:int(round(x)) + 1] = True
    shade(cv, trunk, PALM_BARK, mode="cyl", base=0.5, gain=1.2, ao=-0.1)
    cxrow = np.array([rows.get(y, (0, 0))[0] for y in range(H)])[:, None]
    cv.fill(ring & (xx >= cxrow - 1), PALM_BARK[1])
    cv.fill(ring & (xx < cxrow - 1), PALM_BARK[2])
    cv.fill(ring_hi & trunk & ~ring & (xx < cxrow), PALM_BARK[5])
    # roots and a little sand heaped around them
    for (rx, ry, dx) in ((23, gy, -3), (33, gy, 3)):
        cv.fill(m_line(W, H, [(rx, ry - 2), (rx + dx, ry)]), PALM_BARK[2])
    sand_heap(cv, 23, gy, 5, 2.5, "palm_sand_l", rough=0.2)
    sand_heap(cv, 34, gy, 4.5, 2, "palm_sand_r", rough=0.2)
    # dead frond skirt under the crown
    for (sx, ex, ln, c) in ((31, 29, 9, PALM_BARK[3]), (33, 32, 11, FOLIAGE_DRY[3]), (38, 40, 10, PALM_BARK[2]),
                            (36, 37, 12, FOLIAGE_DRY[2])):
        cv.fill(m_line(W, H, [(sx, crown[1] + 2), (ex, crown[1] + 2 + ln)]), c)
    # crown knob of old frond bases
    knob = m_ellipse(W, H, crown[0], crown[1] + 1, 4.5, 3)
    shade(cv, knob, PALM_BARK, contour=True, R=2, base=0.55, gain=1.0)
    # the date cluster hanging from the crown, on the right where the fronds leave a gap
    g = rng("dates")
    cv.fill(m_line(W, H, [(36, crown[1] + 2), (39, crown[1] + 5)]), STRAW[4])
    for _ in range(16):
        dx, dy = int(g.integers(-2, 4)), int(g.integers(0, 7))
        px, py = 39 + dx, crown[1] + 5 + dy - abs(dx - 1) // 2
        cv.fill(m_rect(W, H, px, py, px + 1, py + 1), DATE[2])
        cv.put(px, py, DATE[4])
        cv.put(px + 1, py + 1, DATE[1])
    # the upper and side fronds in front
    for (side, a0, L, g2, tone) in ((1, -0.3, 27, 2.0, 2), (-1, -0.25, 28, 2.0, 3), (1, -1.05, 22, 2.4, 3),
                                    (-1, -1.1, 22, 2.4, 4), (-1, 0.6, 14, 0.9, 3)):
        _frond(cv, crown[0], crown[1], side, a0, L, g2, sw * (0.6 + L / 22), tone)
    outline(cv)
    return cv


# ------------------------------------------------------------------ desert cactus
@prop("dune_cactus", 36, 48, ground=2)
def dune_cactus(state, f):
    """A columnar desert cactus with two upturned arms: deep ribs, pale spines, one red bud, and a
    sun-bleached lit flank."""
    W, H = 36, 48
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 45
    ground_shadow(cv, 18, gy, 13, 1.6)
    n = len(CACTUS)
    spine_c = (hexc("#efe8c6"), hexc("#b9b893"))

    def ribbed(m, cx, cyl):
        rel = np.round(xx - cx).astype(int)
        groove = (rel % 3 == 1) & erode(m)
        ridge = (rel % 3 == 0) & erode(m)
        shade(cv, m, CACTUS, contour=True, mode="cyl" if cyl else "bevel", R=3, base=0.52, gain=1.4, top=0.18,
              bias=np.where(groove, -1.5 / n, 0.0) + np.where(ridge, 0.6 / n, 0.0))
        return ridge

    # arms first (behind the column): the left one low and short, the right one high
    for pts, r, cx, y0, y1 in (([(16, 31), (9, 31), (7, 27), (7, 17)], 2.9, 7, 16, 29),
                                ([(20, 24), (27, 24), (29, 20), (29, 10)], 2.6, 29, 9, 22)):
        arm = tube(W, H, pts, r)
        up = arm & (yy <= y1)
        ribbed(arm & ~up, cx, False)
        ribbed(up, cx, True)
        for y in range(y0 + 2, y1, 5):
            cv.put(cx - 1 + (y // 5) % 2 * 2, y, spine_c[(y // 5) % 2])
    main = tube(W, H, [(18, 7), (18, gy)], 4.6) & (yy <= gy)
    ribbed(main, 18, True)
    # sun-bleached lit flank and crown
    cv.fill(left_edge(main) & (yy > 8) & (yy < gy - 4), CACTUS[6])
    cv.fill(shift(left_edge(main), 1, 0) & main & (yy > 10) & (yy < gy - 6) & ((yy % 4) == 0), CACTUS[6])
    cv.fill(top_edge(main) & (xx < 19), CACTUS[6])
    # pale spines in small tufts along the ridges
    for (x0, y0) in ((15, 12), (18, 9), (21, 15), (15, 22), (18, 19), (21, 26), (15, 33), (18, 29), (21, 37),
                     (18, 39)):
        cv.put(x0, y0, spine_c[0] if x0 < 20 else spine_c[1])
    # a single red bud on the right arm
    bud = m_ellipse(W, H, 29.5, 7.5, 1.6, 2.0)
    shade(cv, bud, CLOTH_RED, contour=True, mode="sphere", base=0.6, gain=1.0)
    cv.put(29, 6, CLOTH_RED[5])
    sand_heap(cv, 13, gy, 5, 3, "cactus_sand_l", rough=0.2)
    sand_heap(cv, 23, gy, 4.5, 2.2, "cactus_sand_r", rough=0.2)
    outline(cv)
    # two spines poking past the silhouette on the shaded side
    for (x, y) in ((23, 18), (23, 33)):
        if not cv.solid[y, x - 1]:
            continue
        cv.put(x, y, spine_c[1])
    return cv


# ------------------------------------------------------------------ bleached ribcage
@prop("bleached_ribcage", 112, 64, ground=3)
def bleached_ribcage(state, f):
    """The half-buried rib cage and spine of an enormous ancient beast, bleached bone-white, its ribs
    arching over the sand like the beams of a ruined hall. It frames the Oasis of Bones."""
    W, H = 112, 64
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 61
    ground_shadow(cv, 56, gy, 54, 2.0)
    spine_pts = [(5, 54), (14, 32), (34, 15), (60, 11), (84, 16), (100, 32), (106, 54)]
    sp = _spline(spine_pts)

    def spine_y(x):
        return min(sp, key=lambda p: abs(p[0] - x))[1]

    nz = vnoise(W, H, 3, seed_of("ribn"), 2)
    ribs = [(23, 1.0, 0.0), (37, 1.1, 0.8), (51, 1.15, -0.6), (65, 1.1, 0.5), (79, 0.95, -0.4)]

    def rib(sx, sc, wob, far, broken=False):
        sy = spine_y(sx) + 1
        dx, dy = (6, -2) if far else (0, 0)
        bot = gy - 1 if not far else gy - 5
        pts = [(sx + dx, sy + dy), (sx - 7 * sc + dx, sy + 6 + dy), (sx - 11 * sc + wob + dx, sy + 17 + dy),
               (sx - 10 * sc - wob + dx, bot - 8), (sx - 6 * sc + dx, bot)]
        m = tube(W, H, pts, 2.1 if far else 2.7, 1.2 if far else 1.7)
        if broken:
            m &= yy < sy + 22 + (xx % 3 == 0)
        shade(cv, m, BONE_SUN, contour=True, R=2, base=0.27 if far else 0.62, gain=1.0 if far else 1.3,
              noise=nz, namp=0.25)
        return m

    for sx, sc, wob in ribs:
        rib(sx, sc, wob, True)
    # the spine: a chain of vertebrae with backward-raked spurs, tallest over the shoulders
    spine = tube(W, H, spine_pts, 3.3, 2.0)
    shade(cv, spine, BONE_SUN, contour=True, R=2, base=0.6, gain=1.3, noise=nz, namp=0.2)
    for i, (px, py) in enumerate(sp[6::15]):
        if not 8 < px < 104:
            continue
        cv.fill(m_rect(W, H, px + 1, py - 2, px + 1, py + 2) & erode(spine), BONE_SUN[2])
        ln = 3 + 4 * math.exp(-((px - 44) / 30.0) ** 2) + (i % 2)
        spur = m_poly(W, H, [(px - 1, py - 2), (px + 1 + ln * 0.45, py - 2 - ln), (px + 2, py - 2)])
        shade(cv, spur, BONE_SUN, R=1, base=0.65, gain=1.0)
    for k, (sx, sc, wob) in enumerate(ribs):
        rib(sx, sc, wob, False, broken=(k == 3))
    # the broken rib's lower half lies in the sand in front
    frag = tube(W, H, [(54, gy - 1), (58, gy - 3), (63, gy - 4), (67, gy - 3)], 1.7, 1.3)
    shade(cv, frag, BONE_SUN, contour=True, R=2, base=0.62, gain=1.2)
    # sand drifted against the bones and burying both ends of the spine
    sand_drift(cv, gy, [(1, 0), (3, 7), (8, 13), (14, 15), (20, 10), (25, 5), (31, 3), (38, 5), (44, 3), (50, 2),
                        (58, 2), (64, 3), (72, 4), (80, 3), (86, 6), (92, 12), (98, 16), (104, 13), (108, 6),
                        (110, 0)], "ribs")
    outline(cv)
    return cv


# ------------------------------------------------------------------ ember cactus (herb node)
@prop("ember_cactus_patch", 28, 24, states=HERB_STATES)
def ember_cactus_patch(state, f):
    """A squat barrel cactus whose crown flower glows ember-orange with the sunlight it has stored."""
    W, H = 28, 24
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 21
    ground_shadow(cv, 14, gy, 12, 1.4)
    n = len(CACTUS)

    def barrel(cx, cy, rx, ry, cut=None):
        m = m_ellipse(W, H, cx, cy, rx, ry) & (yy <= gy - 1)
        if cut is not None:
            m &= yy >= cut
        t = np.clip((xx - cx) / rx, -0.99, 0.99)
        k = np.arcsin(t) * 4.2
        groove = np.abs(k - np.round(k)) < 0.18
        shade(cv, m, CACTUS, contour=True, mode="sphere", base=0.55, gain=1.3,
              bias=np.where(groove & erode(m), -1.4 / n, 0.0))
        return m

    barrel(21, 18.5, 3.5, 3.2)
    ball = barrel(13, 14.5, 7.5, 7.0)
    for (x, y) in ((9, 11), (12, 10), (16, 11), (8, 16), (18, 15), (13, 18), (21, 16)):
        if ball[y, x] or (abs(x - 21) < 3 and abs(y - 17) < 3):
            cv.put(x, y, hexc("#f5eed2") if x < 15 else hexc("#c9c79c"))
    if state == "ready":
        # a rosette of pointed petals, deep red at the base and burning brighter toward the heart
        cx, cy = 13, 8
        cv.fill(m_ellipse(W, H, cx, cy, 4.0, 1.8), EMBER[1])
        for k, ang in enumerate((-165, -128, -90, -52, -15)):
            a = math.radians(ang)
            ln = 5.6 if k % 2 == 0 else 5.0
            ux, uy = math.cos(a), math.sin(a)
            tip = (cx + ux * ln, cy + uy * ln * 0.85)
            pm = m_poly(W, H, [(cx - uy * 1.8, cy + ux * 1.8), tip, (cx + uy * 1.8, cy - ux * 1.8)])
            cv.fill(pm, EMBER[2] if k % 2 else EMBER[3])
            cv.fill(pm & m_ellipse(W, H, cx, cy, 2.2, 1.6), EMBER[1])
            cv.put(round(tip[0]), round(tip[1]), EMBER[4])
        heart = m_ellipse(W, H, cx, cy - 0.5, 1.6, 1.2)
        cv.fill(heart, EMBER[5])
        cv.put(cx - 1, cy - 1, WHITE_HOT)
    else:
        # the cut stub of the flower stalk, its fresh face pale
        cv.fill(m_rect(W, H, 12, 6, 14, 8), CACTUS[3])
        cv.put(14, 7, CACTUS[2])
        cv.fill(m_rect(W, H, 12, 6, 14, 6), hexc("#d6d69c"))
        cv.put(14, 6, hexc("#a9b276"))
    sand_heap(cv, 14, gy, 11, 2.4, "ember_sand", rough=0.2)
    outline(cv)
    if state == "ready":
        pulse = (0.08, 0.14, 0.11)[f % 3]
        glow(cv, 13, 6, 7, 5, EMBER[3], steps=((1.0, pulse),))
        herb_sparkle(cv, f, [(8, 3), (18, 4), (13, 2)], c1=hexc("#ffcf7a"))
    return cv


# ------------------------------------------------------------------ Tomb of Sunscar: shared bits
TOMB_STONE = ramp("#1f1a1d", "#352d2e", "#4f4442", "#6b5d57", "#8a7a6e", "#ab9a88", "#cbbba3")
TOMB_DARK = ramp("#050607", "#0a0c0e", "#111316", "#1a1a1c", "#252120")


def _weather(cv, m, seed, pal, cell=3, chip=0.72, bands=7):
    """Sandstone weathering on mask m: wind-cut bedding lines, pits, and chipped silhouette pixels."""
    W, H = cv.w, cv.h
    xx, yy = grid(W, H)
    nz = vnoise(W, H, cell, seed_of("weather", seed), 2)
    inner = erode(m)
    bed = inner & ((yy % bands) == 3) & (nz > 0.45)
    for c_hi, c_lo in zip(pal[1:], pal[:-1]):
        sel = bed & np.all(np.abs(cv.rgb - np.array(c_hi, float)) < 0.5, axis=-1)
        cv.fill(sel, c_lo)
    g = rng("pits", seed)
    x0, y0, x1, y1 = bbox(m)
    for _ in range(max(1, (x1 - x0) * (y1 - y0) // 120)):
        px, py = int(g.integers(x0, x1 + 1)), int(g.integers(y0, y1 + 1))
        if inner[py, px]:
            cv.put(px, py, pal[1])
    chips = border(m) & (nz > chip) & ~(yy >= y1 - 1)
    cv.erase(chips)
    return chips


def _sun(cv, cx, cy, r_disc, r_long, r_short, rays=16, pal=GOLD, ry_scale=1.0, width=0.11):
    """A gold sun: wedge rays alternating long and short behind a domed disc with an engraved ring
    (small suns, r_disc < 4, get plain bright rays and no ring so they stay crisp)."""
    W, H = cv.w, cv.h
    xx, yy = grid(W, H)
    ray_m = np.zeros((H, W), bool)
    for k in range(rays):
        a = 2 * math.pi * k / rays - math.pi / 2
        rl = r_long if k % 2 == 0 else r_short
        pts = [(cx + math.cos(a - width) * r_disc * 0.9, cy + math.sin(a - width) * r_disc * 0.9 * ry_scale),
               (cx + math.cos(a) * rl, cy + math.sin(a) * rl * ry_scale),
               (cx + math.cos(a + width) * r_disc * 0.9, cy + math.sin(a + width) * r_disc * 0.9 * ry_scale)]
        ray_m |= m_poly(W, H, pts)
    ang = np.arctan2((yy - cy) / ry_scale, xx - cx)
    lit = -np.cos(ang + math.pi * 0.75)          # rays facing the upper left catch the light
    disc = m_ellipse(W, H, cx, cy, r_disc, r_disc * ry_scale)
    if r_disc < 4:
        cv.fill(ray_m & (lit > -0.2), pal[4])
        cv.fill(ray_m & (lit <= -0.2), pal[3])
        shade(cv, disc, pal, mode="sphere", base=0.7, gain=1.0)
        cv.fill(bottom_edge(disc), pal[2])
        return ray_m | disc
    shade(cv, ray_m, pal, contour=True, R=1, base=0.55, gain=0.6, bias=lit * 0.18)
    shade(cv, disc, pal, contour=True, mode="sphere", base=0.6, gain=1.1)
    ring = ellipse_ring(W, H, cx, cy, r_disc * 0.68, r_disc * 0.68 * ry_scale)
    cv.fill(ring & (xx + yy < cx + cy), pal[2])
    cv.fill(ring & (xx + yy >= cx + cy), pal[1])
    cv.fill(shift(ring, 1, 1) & disc & ~ring & ~m_ellipse(W, H, cx, cy, r_disc * 0.5, r_disc * 0.5 * ry_scale),
            pal[len(pal) - 2])
    boss = m_ellipse(W, H, cx, cy, max(1.0, r_disc * 0.28), max(1.0, r_disc * 0.28 * ry_scale))
    cv.fill(boss, pal[len(pal) - 2])
    cv.fill(boss & (xx + yy < cx + cy - 0.5), pal[-1])
    cv.fill(bottom_edge(boss) | right_edge(boss), pal[3])
    return ray_m | disc


# ------------------------------------------------------------------ sand king statue
@prop("sand_king_statue", 48, 88, ground=3)
def sand_king_statue(state, f):
    """A wind-worn sandstone king of the old desert realm: tall crown, braided beard, a sun sceptre in
    his right hand, the left arm broken away at the shoulder and lying in the sand heaped at his feet.
    They stand in pairs down the Hall of Sand Kings."""
    W, H = 48, 88
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 85
    ground_shadow(cv, 24, gy, 21, 1.8)
    nz = vnoise(W, H, 3, seed_of("king"), 2)
    P = SANDSTONE

    def part(m, base=0.58, gain=1.3, R=2, mode="bevel", contour=True):
        shade(cv, m, P, contour=contour, mode=mode, R=R, strength=2.2, base=base, gain=gain, noise=nz, namp=0.22)
        return m

    # plinth: cornice, die with a recessed panel, footing
    die = part(m_rect(W, H, 9, 71, 38, 84), base=0.5, gain=1.0)
    cv.fill(m_rect(W, H, 13, 74, 34, 74), P[2])
    cv.fill(m_rect(W, H, 13, 75, 13, 81), P[2])
    cv.fill(m_rect(W, H, 14, 81, 34, 81) | m_rect(W, H, 34, 75, 34, 80), P[4])
    cv.fill(m_rect(W, H, 14, 75, 33, 80), P[3])
    part(m_rect(W, H, 7, 68, 40, 70), base=0.6, R=1, gain=1.0)
    cv.fill(m_rect(W, H, 7, 68, 40, 68), P[5])
    # feet under the hem
    for tx in (19, 29):
        part(m_ellipse(W, H, tx, 67, 3, 1.5) & (yy <= 67), base=0.5, R=1)
    # the body: shoulders, torso and long robe shaded as one rounded mass
    body = m_poly(W, H, [(13, 30), (17, 25), (31, 25), (35, 30), (34, 41), (36, 66), (12, 66), (14, 41)])
    part(body, mode="cyl", base=0.58, gain=1.4)
    for (x0, x1, y0) in ((17, 14, 45), (19, 18, 46), (30, 32, 45), (32, 35, 47)):
        fold = m_line(W, H, [(x0, y0), (x1, 65)]) & erode(body)
        cv.fill(fold, P[2] if x0 < 24 else P[1])
        if x0 < 24:
            cv.fill(shift(fold, -1, 0) & erode(body) & ~fold, P[5])
    belt = m_rect(W, H, 14, 40, 34, 42)
    part(belt, mode="cyl", base=0.6, R=1, gain=1.2)
    cv.fill(top_edge(belt) & (xx < 30), P[5])
    apron = m_poly(W, H, [(21, 43), (27, 43), (28, 65), (20, 65)])
    part(apron, mode="cyl", base=0.66, R=1, gain=0.9)
    for y in (49, 56):
        cv.fill(m_rect(W, H, 21, y, 27, y) & erode(apron), P[2])
    cv.fill(m_ellipse(W, H, 24, 60.5, 1.5, 1.5) & apron, P[2])
    buckle = m_ellipse(W, H, 24, 41, 2.2, 2.0)
    part(buckle, base=0.72, R=1)
    cv.put(23, 40, GOLD[4])
    # broken left arm (viewer's right): a stump ending in a jagged, paler break
    stump = m_poly(W, H, [(31, 26), (35, 28), (37, 32), (37, 36), (36, 37), (35, 35), (34, 37), (33, 35), (32, 36)])
    part(stump, base=0.42, gain=1.1)
    brk = stump & (yy >= 35)
    cv.fill(brk, P[5])
    cv.fill(brk & (xx % 2 == 0) & (yy == 36), P[3])
    # head: a worn face over a long spade beard
    face = m_ellipse(W, H, 24, 16, 4.8, 5.6)
    part(face, base=0.66, gain=1.2, R=2)
    cv.fill(m_rect(W, H, 21, 15, 22, 15) | m_rect(W, H, 26, 15, 27, 15), P[1])   # worn eye hollows
    cv.put(21, 16, P[3])
    cv.put(26, 16, P[3])
    cv.fill(m_rect(W, H, 21, 14, 22, 14), P[5])                                  # lit brow
    cv.fill(m_rect(W, H, 24, 15, 24, 17), P[5])                                  # eroded nose
    cv.put(25, 17, P[2])
    beard = m_poly(W, H, [(20, 19), (28, 19), (28, 23), (25.5, 28.5), (22.5, 28.5), (20, 23)])
    part(beard, mode="cyl", base=0.5, R=1, gain=1.3)
    cv.fill(m_line(W, H, [(22, 21), (23, 27)]) & erode(beard), P[2])
    cv.fill(m_line(W, H, [(26, 21), (25, 27)]) & erode(beard), P[1])
    cv.fill(m_rect(W, H, 21, 19, 27, 19), P[4])                                  # moustache
    cv.fill(m_rect(W, H, 23, 20, 25, 20), P[1])                                  # mouth
    # the tall flared crown: band, three points and a sun boss with a trace of old gilding
    crown = m_poly(W, H, [(17, 9), (15.5, 4), (18, 2), (20, 5), (22, 4), (24, 1), (26, 4), (28, 5), (30, 2),
                          (32.5, 4), (31, 9)])
    part(crown, mode="cyl", base=0.62, R=1, gain=1.3)
    band = m_rect(W, H, 17, 8, 31, 10)
    part(band, mode="cyl", base=0.55, R=1, gain=1.3)
    cv.fill(m_rect(W, H, 17, 8, 29, 8), P[5])
    boss = m_ellipse(W, H, 24, 5, 1.6, 1.6)
    cv.fill(boss, GOLD[3])
    cv.put(23, 4, GOLD[5])
    cv.fill(m_rect(W, H, 20, 9, 20, 9) | m_rect(W, H, 24, 9, 24, 9), GOLD[3])
    # right arm (viewer's left): a wide sleeve draping to the hand that grips the sceptre
    sleeve = m_poly(W, H, [(13, 29), (18, 27), (19, 38), (17, 46), (10, 49), (8, 46), (11, 35)])
    part(sleeve, base=0.62, gain=1.3)
    cv.fill(m_line(W, H, [(15, 32), (13, 44)]) & erode(sleeve), P[3])
    staff = m_rect(W, H, 8, 16, 9, 67)
    part(staff, base=0.55, R=1, mode="cyl")
    ring = m_ellipse(W, H, 8.5, 12.5, 3, 3) & ~m_ellipse(W, H, 8.5, 12.5, 1.2, 1.2)
    ring |= m_poly(W, H, [(8, 10), (8.5, 6), (9, 10)])
    part(ring, base=0.62, R=1)
    cv.put(7, 11, GOLD[4])
    cv.put(10, 14, GOLD[2])
    hand = m_ellipse(W, H, 9.5, 45, 2.4, 2.0)
    part(hand, base=0.64, R=1, mode="sphere")
    cv.put(10, 46, P[2])
    statue = cv.solid.copy() & (yy < 68)
    _weather(cv, statue, "king", P, chip=0.8, bands=9)
    cv.fill(m_line(W, H, [(29, 30), (30, 34), (29, 37), (31, 40)]) & erode(body), P[1])
    cv.fill(m_line(W, H, [(31, 71), (30, 74), (32, 77)]) & erode(die), P[1])
    # sand heaped against the plinth, the lost forearm half-buried on the right
    sand_heap(cv, 12, gy, 11, 8, "king_l", rough=0.18)
    arm = tube(W, H, [(33, gy - 4), (38, gy - 5), (42, gy - 3)], 1.9, 1.5)
    part(arm, base=0.58, R=1)
    cv.fill(m_ellipse(W, H, 42.5, gy - 3, 1.5, 1.5), P[4])
    sand_heap(cv, 36, gy, 9, 3.5, "king_r", rough=0.2)
    outline(cv)
    return cv


# ------------------------------------------------------------------ bronze mirror
@prop("bronze_mirror", 44, 64, states=(("idle", 4, 4),), ground=3)
def bronze_mirror(state, f):
    """A great polished bronze mirror of the Mirror Crypt, cradled in a carved rosewood stand. Its rim
    has gone green with verdigris; a pale glint slides across the face."""
    W, H = 44, 64
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 61
    cx, cy, r = 22, 27, 16
    ground_shadow(cv, cx, gy, 19, 1.6)
    # stand: footing with cloud-scroll feet, a stepped block, the post and the cradle arms
    for fx in (7, 36):
        foot = m_ellipse(W, H, fx, gy - 1, 3.5, 2.5) & (yy <= gy)
        shade(cv, foot, ROSEWOOD, contour=True, R=1, base=0.5, gain=1.0)
        cv.put(fx - 1, gy - 2, ROSEWOOD[1])
    plinth = m_rect(W, H, 7, 54, 36, 58)
    shade(cv, plinth, ROSEWOOD, contour=True, R=1, base=0.5, gain=1.2)
    cv.fill(m_rect(W, H, 7, 54, 36, 54), ROSEWOOD[4])
    cv.fill(m_rect(W, H, 10, 56, 33, 56) & ((xx % 4) == 1), GOLD[2])
    step = m_rect(W, H, 12, 50, 31, 53)
    shade(cv, step, ROSEWOOD, contour=True, R=1, base=0.55, gain=1.2)
    cv.fill(m_rect(W, H, 12, 50, 31, 50), ROSEWOOD[5])
    post = m_rect(W, H, 19, 42, 24, 49)
    shade(cv, post, ROSEWOOD, contour=True, mode="cyl", base=0.55, gain=1.0)
    for sgn in (-1, 1):
        arm = tube(W, H, [(cx + sgn * 2, 46), (cx + sgn * 12, 43), (cx + sgn * 17, 34), (cx + sgn * 18, 22),
                          (cx + sgn * 16, 17)], 1.8, 1.3)
        shade(cv, arm, ROSEWOOD, contour=True, R=1, base=0.55 if sgn < 0 else 0.4, gain=1.1)
        knob = m_ellipse(W, H, cx + sgn * 16, 15.5, 1.8, 2.2)
        shade(cv, knob, GOLD, contour=True, mode="sphere", base=0.55, gain=1.0)
    # the disc: a bronze rim eaten by verdigris around a polished face
    disc = m_ellipse(W, H, cx, cy, r, r)
    face = m_ellipse(W, H, cx, cy, r - 3, r - 3)
    rim = disc & ~face
    nz = vnoise(W, H, 3, seed_of("mirror_vg"), 2)
    shade(cv, rim, BRONZE, contour=True, mode="sphere", base=0.45, gain=1.2, noise=nz, namp=0.2)
    cv.fill(ellipse_ring(W, H, cx, cy, r, r) & (xx + yy < cx + cy - 8), BRONZE[5])
    cv.fill(ellipse_ring(W, H, cx, cy, r - 3, r - 3) & (xx + yy < cx + cy), BRONZE[1])
    cv.fill(ellipse_ring(W, H, cx, cy, r - 3, r - 3) & (xx + yy >= cx + cy), BRONZE[5])
    vg = rim & (nz + (yy - cy) / (2.5 * r) > 0.62)
    cv.fill(vg, VERDIGRIS[2])
    cv.fill(vg & (nz > 0.66), VERDIGRIS[3])
    cv.fill(vg & shift(~vg, 0, -1) & (nz > 0.6), VERDIGRIS[4])
    u = ((xx - cx) + (yy - cy)) / (r - 3)
    shade(cv, face, MIRROR, mode="flat", base=0.52, gain=0.0, bias=-u * 0.28, clean=False)
    # a soft cloudy reflection of the crypt in the lower half
    cv.fill(face & (u > 0.45) & (nz > 0.6), MIRROR[1])
    # the travelling glint: a pale diagonal band with a thinner echo
    pos = (-0.85, -0.3, 0.25, 0.8)[f % 4]
    v = ((xx - cx) - (yy - cy)) / (r - 3)
    band = face & (np.abs(u - pos) * (r - 3) < 1.1)
    echo = face & (np.abs(u - pos - 0.3) * (r - 3) < 0.6)
    cv.fill(echo, MIRROR[5])
    cv.fill(band, MIRROR[6])
    cv.fill(band & (np.abs(v) > 0.75), MIRROR[5])
    # finial on the top of the disc
    fin = m_poly(W, H, [(cx - 3, 12), (cx, 7), (cx + 3, 12)]) | m_ellipse(W, H, cx, 11.5, 3, 1.4)
    shade(cv, fin, GOLD, contour=True, R=1, base=0.6, gain=1.0)
    outline(cv)
    gx = int(round(cx + (pos * (r - 3)) / 2 - 3))
    gy2 = int(round(cy + (pos * (r - 3)) / 2 - 3 + 6))
    if f % 4 in (1, 2):
        sparkle(cv, gx, gy2 - 6, 1, WHITE_HOT, MIRROR[5], 0.9)
    return cv


# ------------------------------------------------------------------ sun throne
@prop("sun_throne", 96, 88, ground=3)
def sun_throne(state, f):
    """The Tomb King's empty throne: a massive sandstone seat on a three-stepped dais, a gold sun disc
    rayed behind the backrest, faded vermilion cloth over the seat and jade set into the stone."""
    W, H = 96, 88
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 85
    cx = 48
    P = SANDSTONE
    nz = vnoise(W, H, 3, seed_of("throne"), 2)
    ground_shadow(cv, cx, gy, 46, 2.0)

    def block(m, base=0.55, gain=1.2, R=2, mode="bevel", contour=True):
        shade(cv, m, P, contour=contour, mode=mode, R=R, strength=2.0, base=base, gain=gain, noise=nz, namp=0.2)
        return m

    def jade(x, y, big=False):
        d = m_poly(W, H, [(x, y - 2), (x + 2, y), (x, y + 2), (x - 2, y)]) if big else m_rect(W, H, x - 1, y - 1, x, y)
        cv.fill(d, JADE_R[3])
        cv.fill(top_edge(d) | left_edge(d), JADE_R[5])
        cv.fill(bottom_edge(d) & right_edge(d), JADE_R[1])

    # the sun behind the throne
    _sun(cv, cx, 23, 11, 21, 16, rays=12, width=0.22)
    # backrest slab with a stepped crest, a carved inner border and jade inlay
    back = m_rect(W, H, 31, 31, 64, 60) | m_rect(W, H, 36, 28, 59, 31)
    block(back, base=0.5, gain=1.1)
    cv.fill(m_rect(W, H, 31, 31, 35, 31) | m_rect(W, H, 36, 28, 59, 28) | m_rect(W, H, 60, 31, 64, 31), P[5])
    inner = m_rect(W, H, 36, 34, 59, 50)
    cv.fill(border(inner), P[2])
    cv.fill(left_edge(inner) | top_edge(inner), P[1])
    cv.fill(erode(inner), P[3])
    for jx in range(39, 58, 4):
        jade(jx, 36)
    jade(48, 43, big=True)
    # armrests: massive blocks with a scroll carved on the front
    for (x0, x1) in ((20, 33), (62, 75)):
        arm = m_rect(W, H, x0, 44, x1, 61)
        block(arm, base=0.58 if x0 < cx else 0.45, gain=1.2)
        cv.fill(m_rect(W, H, x0, 44, x1, 45), P[5] if x0 < cx else P[4])
        scroll = ellipse_ring(W, H, (x0 + x1) / 2, 51, 3.5, 3.5) | m_rect(W, H, (x0 + x1) // 2, 51, (x0 + x1) // 2 + 1, 51)
        cv.fill(scroll, P[2])
        jade((x0 + x1) // 2 + 1, 58)
    # seat and the faded vermilion cloth laid over it, hanging to a point with a gold tassel
    seat = m_rect(W, H, 34, 49, 61, 61)
    block(seat, base=0.45, gain=1.0)
    cv.fill(m_rect(W, H, 34, 49, 61, 52), P[4])
    cv.fill(m_rect(W, H, 34, 49, 61, 49), P[5])
    cv.fill(m_rect(W, H, 34, 53, 61, 53), P[1])
    cloth_top = m_rect(W, H, 38, 49, 57, 52)
    cloth = m_poly(W, H, [(38, 53), (57, 53), (57, 58), (52, 59), (47.5, 61), (43, 59), (38, 58)])
    cv.fill(cloth_top, VERMILION[4])
    cv.fill(top_edge(cloth_top) | left_edge(cloth_top), VERMILION[5])
    shade(cv, cloth, VERMILION, mode="cyl", base=0.72, gain=0.9, noise=nz, namp=0.15)
    cv.fill(cloth & (yy == 53), VERMILION[5])
    for (fx0, fx1) in ((43, 44), (52, 51)):
        cv.fill(m_line(W, H, [(fx0, 55), (fx1, 58)]) & erode(cloth), VERMILION[2])
    hem = bottom_edge(cloth)
    cv.fill(hem, GOLD[3])
    cv.fill(hem & ((xx % 3) == 0), GOLD[5])
    cv.fill(left_edge(cloth) | right_edge(cloth), VERMILION[1])
    cv.fill(m_rect(W, H, 47, 60, 48, 61), GOLD[4])
    cv.put(47, 60, GOLD[6])
    # the three-stepped dais
    for (x0, x1, y0, y1) in ((18, 77, 62, 68), (10, 85, 69, 76), (2, 93, 77, gy)):
        step = m_rect(W, H, x0, y0, x1, y1)
        block(step, base=0.45, gain=1.0, R=1)
        cv.fill(m_rect(W, H, x0, y0, x1, y0 + 1), P[5])
        cv.fill(m_rect(W, H, x0, y0, x0, y1), P[4])
        for jx in range(x0 + 8, x1 - 4, 12):
            cv.fill(m_rect(W, H, jx + 5, y0 + 2, jx + 5, y1), P[2])
            jade(jx, (y0 + y1) // 2 + 1)
    _weather(cv, cv.solid & ~cloth & (yy > 27), "throne", P, chip=0.85, bands=8)
    # sand drifted onto the lower steps
    sand_heap(cv, 8, gy, 7, 6, "throne_l", rough=0.2)
    sand_heap(cv, 87, gy, 8, 9, "throne_r", rough=0.2)
    sand_heap(cv, 78, 76, 5, 2.5, "throne_s", rough=0.2)
    outline(cv)
    return cv


# ------------------------------------------------------------------ tomb gate
@prop("tomb_gate", 120, 112, states=(("sealed", 3, 3), ("open", 1, 0)), ground=4)
def tomb_gate(state, f):
    """The sealed gate of the Tomb of Sunscar: two huge studded bronze doors in a sandstone frame, the
    whole half-buried by the dunes. A round sun-seal locks them, ringed by an engraved band of the old
    script that glows faintly while the seal holds. Open, the doors stand swung inward on darkness and
    the first stairs down."""
    W, H = 120, 112
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 107
    cx = 60
    P = SANDSTONE
    nz = vnoise(W, H, 3, seed_of("gate"), 2)
    ground_shadow(cv, cx, gy, 58, 2.2)

    def block(m, base=0.55, gain=1.2, R=2, mode="bevel", contour=True):
        shade(cv, m, P, contour=contour, mode=mode, R=R, strength=2.0, base=base, gain=gain, noise=nz, namp=0.2)
        return m

    # door recess
    dx0, dx1, dy0 = 25, 94, 32
    recess = m_rect(W, H, 21, 28, 98, gy)
    cv.fill(recess, P[1])
    if state == "open":
        dark = m_rect(W, H, dx0, dy0, dx1, gy)
        edge = np.minimum(np.minimum(xx - dx0, dx1 - xx), (yy - dy0) * 1.5)
        _idx_fill(cv, dark, TOMB_DARK, np.clip(4 - edge / 3.0, 0, 4))
        # the first stairs down into the tomb, each nosing a little dimmer
        for k, sy in enumerate((gy - 1, gy - 6, gy - 10, gy - 13, gy - 15)):
            inset = 12 + k * 5
            cv.fill(m_rect(W, H, dx0 + inset, sy, dx1 - inset, sy), (P[3], P[2], P[1], TOMB_DARK[4], TOMB_DARK[3])[k])
            cv.fill(m_rect(W, H, dx0 + inset, sy + 1, dx1 - inset, sy + 1) & (yy < gy), TOMB_DARK[2])
        # the leaves swung inward, foreshortened against the jambs
        for sgn, xj in ((-1, dx0), (1, dx1)):
            leaf = m_poly(W, H, [(xj, dy0), (xj - sgn * 9, dy0 + 5), (xj - sgn * 9, gy - 8), (xj, gy)])
            shade(cv, leaf, BRONZE, contour=True, R=1, base=0.28 if sgn < 0 else 0.2, gain=0.8, noise=nz, namp=0.2)
            cv.fill(m_line(W, H, [(xj - sgn * 9, dy0 + 5), (xj - sgn * 9, gy - 8)]), BRONZE[4 if sgn < 0 else 3])
            for k in range(4):
                sy = dy0 + 12 + k * 17
                cv.put(xj - sgn * 4, sy + (1 if sgn else 0), BRONZE[5])
            half = m_ellipse(W, H, xj - sgn * 9, 62, 2.5, 10) & (sgn * (xx - (xj - sgn * 9)) <= 0)
            cv.fill(half, GOLD[2])
            cv.fill(half & ((yy % 3) == 0), GOLD[4])
    else:
        # two bronze leaves: a raised border, rows of domed studs and green runs of verdigris
        for (x0, x1) in ((dx0, cx - 1), (cx, dx1)):
            leaf = m_rect(W, H, x0, dy0, x1, gy)
            shade(cv, leaf, BRONZE, contour=True, R=2, base=0.64 if x0 < cx else 0.5, gain=1.1, noise=nz,
                  namp=0.06)
            frame = border(m_rect(W, H, x0 + 2, dy0 + 2, x1 - 2, gy + 4)) & leaf
            cv.fill(frame & ((xx == x0 + 2) | (yy == dy0 + 2)), BRONZE[5])
            cv.fill(frame & ~((xx == x0 + 2) | (yy == dy0 + 2)), BRONZE[1])
            for sy in (40, 50, 76, 86, 96):
                for sx in (x0 + 8, x0 + 17, x0 + 26):
                    if abs(sx - cx) < 16 and abs(sy - 62) < 16:
                        continue
                    stud = m_ellipse(W, H, sx, sy, 1.8, 1.6)
                    cv.fill(stud, BRONZE[4])
                    cv.put(sx - 1, sy - 1, BRONZE[6])
                    cv.fill(bottom_edge(stud) | right_edge(stud), BRONZE[1])
                    run = m_rect(W, H, sx, sy + 2, sx, sy + 3 + (sx * 7 + sy) % 5) & leaf
                    cv.fill(run, VERDIGRIS[2])
        # verdigris gathers low on the leaves where the sand keeps them damp at night
        vn = vnoise(W, H, 4, seed_of("gate_vg"), 2)
        vv = vn + (yy - 76) / 70.0
        vg = m_rect(W, H, dx0 + 1, dy0, dx1 - 1, gy) & (vv > 0.86) & ~dilate(m_rect(W, H, cx - 1, dy0, cx, gy))
        cv.fill(vg, VERDIGRIS[1])
        cv.fill(vg & (vv > 0.97), VERDIGRIS[2])
        cv.fill(m_rect(W, H, cx - 1, dy0, cx, gy), BRONZE[0])
        cv.fill(m_rect(W, H, cx + 1, dy0, cx + 1, gy), BRONZE[3])
        # the sun seal: an engraved script ring round a gold sun
        sr = 14
        ringm = m_ellipse(W, H, cx, 62, sr, sr) & ~m_ellipse(W, H, cx, 62, sr - 4, sr - 4)
        shade(cv, ringm, BRONZE, contour=True, mode="sphere", base=0.35, gain=1.0)
        cv.fill(ellipse_ring(W, H, cx, 62, sr, sr) & (xx + yy < cx + 62), BRONZE[5])
        glyph_c = (GOLD[3], GOLD[5], GOLD[4])[f % 3]
        for k in range(20):
            a = 2 * math.pi * k / 20
            gx, gy2 = cx + math.cos(a) * (sr - 2), 62 + math.sin(a) * (sr - 2)
            ta = (-math.sin(a), math.cos(a))
            if k % 3 == 0:
                pts = [(gx - ta[0], gy2 - ta[1]), (gx + ta[0], gy2 + ta[1])]
            elif k % 3 == 1:
                pts = [(gx - math.cos(a) * 0.8, gy2 - math.sin(a) * 0.8), (gx + math.cos(a), gy2 + math.sin(a))]
            else:
                pts = [(gx, gy2)]
            cv.fill(m_line(W, H, pts) & ringm, glyph_c)
        _sun(cv, cx, 62, 6, 10, 8.5, rays=12, width=0.2)
    # the sandstone frame: pillars with capitals, a carved lintel, a stepped cornice and a sun relief
    for (x0, x1) in ((3, 21), (98, 116)):
        pil = m_rect(W, H, x0, 30, x1, gy)
        block(pil, base=0.58 if x0 < cx else 0.45)
        cv.fill(m_rect(W, H, x0, 30, x0, gy), P[5] if x0 < cx else P[4])
        for sy in range(40, gy, 11):
            cv.fill(m_rect(W, H, x0 + 1, sy, x1 - 1, sy) & ~m_rect(W, H, x0 + 1, sy, x0 + 1, sy), P[2])
        panel = m_rect(W, H, x0 + 5, 38, x1 - 5, 90)
        cv.fill(erode(panel), P[3] if x0 < cx else P[2])
        cv.fill(left_edge(panel) | top_edge(panel), P[1])
        cv.fill((right_edge(panel) | bottom_edge(panel)) & ~(left_edge(panel) | top_edge(panel)), P[5] if x0 < cx else P[4])
        g = rng("gate_script", x0)
        for gy3 in range(41, 87, 6):      # a column of the old script down each pillar
            k = int(g.integers(0, 4))
            gm = m_rect(W, H, x0 + 7, gy3, x1 - 7, gy3)
            gm |= m_rect(W, H, x0 + 7 + k, gy3 + 1, x0 + 7 + k, gy3 + 3)
            gm |= m_rect(W, H, x1 - 7 - (k + 1) % 3, gy3 + 2, x1 - 7, gy3 + 2)
            cv.fill(gm & erode(panel), P[1])
        cap = m_rect(W, H, x0 - 2, 26, x1 + 2, 30)
        block(cap, base=0.6, R=1)
        cv.fill(m_rect(W, H, x0 - 2, 26, x1 + 2, 26), P[5])
    lintel = m_rect(W, H, 4, 12, 115, 26)
    block(lintel, base=0.55)
    cv.fill(m_rect(W, H, 8, 15, 111, 15) | m_rect(W, H, 8, 23, 111, 23), P[2])
    for tx in range(10, 110, 6):
        if abs(tx - cx) > 12:
            cv.fill(m_rect(W, H, tx, 18, tx + 2, 20) & ~m_rect(W, H, tx + 1, 19, tx + 1, 19), P[2])
    cornice = m_rect(W, H, 1, 6, 118, 11) | m_rect(W, H, 44, 2, 75, 6)
    block(cornice, base=0.62, R=1)
    cv.fill(m_rect(W, H, 1, 6, 43, 6) | m_rect(W, H, 76, 6, 118, 6) | m_rect(W, H, 44, 2, 75, 2), P[6])
    cv.fill(m_rect(W, H, 1, 11, 118, 11), P[2])
    _sun(cv, cx, 17, 5, 10, 8, rays=12, width=0.24)
    _weather(cv, cv.solid & ~recess, "gate", P, chip=0.84, bands=9)
    # dunes drifted against the gate, lower in the middle where the way in is
    mid = 7 if state == "sealed" else 4
    sand_drift(cv, gy, [(1, 0), (4, 12), (9, 24), (16, 30), (24, 26), (32, 16), (42, 10), (52, mid + 1), (60, mid),
                        (70, mid + 1), (80, 10), (88, 16), (96, 23), (104, 27), (111, 22), (115, 11), (118, 0)],
               "gate")
    outline(cv)
    if state == "sealed":
        a = (0.08, 0.16, 0.12)[f % 3]
        glow(cv, cx, 62, 18, 18, PALE_GOLD, steps=((1.0, a * 0.6), (0.72, a)))
    return cv


# ------------------------------------------------------------------ sarcophagus
@prop("sarcophagus", 72, 40, ground=2)
def sarcophagus(state, f):
    """A stone sarcophagus of the Tomb of Sunscar: a carved lid with a gold sun and gold trim, panelled
    sides, and a little sand blown across the lid."""
    W, H = 72, 40
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 37
    P = TOMB_STONE
    nz = vnoise(W, H, 3, seed_of("sarc"), 2)
    ground_shadow(cv, 36, gy, 35, 1.6)

    def block(m, base=0.55, gain=1.1, R=1, contour=True):
        shade(cv, m, P, contour=contour, R=R, strength=2.0, base=base, gain=gain, noise=nz, namp=0.18)
        return m

    # footing and the chest with two recessed panels and a sun medallion
    block(m_rect(W, H, 4, 33, 67, 36), base=0.45)
    cv.fill(m_rect(W, H, 4, 33, 67, 33), P[4])
    block(m_rect(W, H, 6, 20, 65, 32), base=0.5)
    for (x0, x1) in ((10, 28), (43, 61)):
        pan = m_rect(W, H, x0, 23, x1, 30)
        cv.fill(erode(pan), P[2])
        cv.fill(top_edge(pan) | left_edge(pan), P[1])
        cv.fill((bottom_edge(pan) | right_edge(pan)) & ~(top_edge(pan) | left_edge(pan)), P[4])
        mid = (x0 + x1) // 2
        lz = m_poly(W, H, [(mid - 5, 26.5), (mid, 24), (mid + 5, 26.5), (mid, 29)])
        cv.fill(border(lz), P[1])
        cv.fill(top_edge(lz) & (xx < mid), P[0])
        cv.put(mid, 26, GOLD[3])
    cv.fill(m_rect(W, H, 6, 21, 65, 21) | m_rect(W, H, 6, 31, 65, 31), GOLD[2])
    cv.fill(m_rect(W, H, 6, 21, 65, 21) & ((xx % 4) == 0), GOLD[4])
    _sun(cv, 35.5, 26, 3, 5.5, 4.5, rays=8, width=0.3)
    # lid: a thick edge band with gold trim and a gently domed top carved with a sun
    block(m_rect(W, H, 3, 14, 68, 19), base=0.58)
    cv.fill(m_rect(W, H, 3, 14, 68, 14), P[5])
    cv.fill(m_rect(W, H, 3, 17, 68, 17), GOLD[3])
    cv.fill(m_rect(W, H, 3, 17, 68, 17) & ((xx % 3) == 0), GOLD[5])
    top = m_poly(W, H, [(4, 13), (7, 4), (64, 4), (67, 13)])
    shade(cv, top, P, contour=True, mode="flat", base=0.78, gain=0.0, noise=nz, namp=0.12,
          bias=-np.clip((yy - 5) / 8.0, 0, 1) * 0.3)
    cv.fill(top_edge(top), P[6])
    trim = m_poly(W, H, [(8, 12), (11, 6.5), (60, 7), (63, 12)])
    cv.fill(border(trim) & ~bottom_edge(trim), GOLD[3])
    cv.fill(top_edge(trim), GOLD[5])
    _sun(cv, 35.5, 9.5, 2.8, 6, 4.5, rays=12, width=0.26, ry_scale=0.55)
    _weather(cv, cv.solid, "sarc", P, chip=0.88, bands=6)
    # sand blown across the lid's right end and heaped at the corners
    sand_heap(cv, 58, 13, 8, 3.5, "sarc_lid", rough=0.2)
    sand_heap(cv, 8, gy, 5, 4, "sarc_l", rough=0.2)
    sand_heap(cv, 63, gy, 6, 5, "sarc_r", rough=0.2)
    outline(cv)
    return cv


# ------------------------------------------------------------------ Skyport Wreck, Skydock yards and the Trial Hall
# The Skyport Wreck on the Starsea shore (an ancient sky-port broken apart, now a pirates' nest), the
# navigator's and shipwright's yards at the Cloudgate Skydock, and the Nine Peaks Alliance's Trial Hall.
from parts import motes  # noqa: E402
from pixlib import m_curve  # noqa: E402

STARGLASS = ramp("#221f3d", "#343461", "#4d5690", "#7185bd", "#a5c6e2", "#e3f6fb")
INDIGO = ramp("#0b0a20", "#161339", "#221e55", "#312b73", "#463f93", "#6760b4")
RUST = ramp("#1f100c", "#3b1d13", "#5d2d18", "#80411f", "#a35a2b", "#c27a40")
SHORE = ramp("#3a3236", "#5a4f4e", "#7d6f63", "#a08f78", "#bfae90", "#d9caac", "#ede2c8")
SAIL_OLD = ramp("#3a342b", "#5e5645", "#857a62", "#aa9e80", "#c9bd9c", "#e2d8b9")
STARLIGHT = ramp("#140d2e", "#261a56", "#3d2f88", "#5d4fb8", "#8f84dd", "#c9c3f6", "#f6f4ff")


def _rot(ox, oy, a):
    """Point transform: local (u, v) rotated clockwise on screen by a (radians), then moved to (ox, oy)."""
    ca, sa = math.cos(a), math.sin(a)
    return lambda u, v: (ox + u * ca - v * sa, oy + u * sa + v * ca)


def _shard(cv, x, by, h, w=2, lean=0.0, pal=STARGLASS):
    """One star-crystal shard standing on row `by`: a pointed prism lit on its left facet."""
    W, H = cv.w, cv.h
    m = m_poly(W, H, [(x - w / 2, by), (x + lean - 0.3, by - h), (x + lean + 0.3, by - h), (x + w / 2, by)])
    xx = grid(W, H)[0]
    mid = x + lean * 0.5
    cv.fill(m & (xx < mid), pal[4])
    cv.fill(m & (xx >= mid), pal[2])
    cv.fill(bottom_edge(m), pal[1])
    cv.put(round(x + lean), by - h + 1, pal[5])
    return m


def _crust(cv, m, seed, cover=0.5, pal=STARGLASS, spacing=5):
    """Barnacle-like star-crystal crust on mask m: little clumps of faceted crystal, each a dark
    rounded foot with two or three pale points lit from the upper left."""
    W, H = cv.w, cv.h
    nz = vnoise(W, H, 5, seed_of("crust", seed), 2)
    area = m & erode(m) & (nz > 1.0 - cover)
    g = rng("crustclump", seed)
    for y in range(1, H - 2, spacing - 1):
        for x in range(1, W - 2, spacing):
            px = x + int(g.integers(0, spacing - 1))
            py = y + int(g.integers(0, 2))
            if px + 2 >= W or py + 2 >= H or not area[py, px] or g.random() < 0.25:
                continue
            w = 3 if g.random() < 0.6 else 2
            foot = m_rect(W, H, px - 1, py, px - 2 + w, py + 1) & m
            cv.fill(foot, pal[1])
            cv.fill(foot & shift(foot, 1, 0) & ~shift(foot, 0, -1), pal[2])
            cv.put(px - 1, py, pal[3])
            cv.put(px, py - 1 if m[max(0, py - 1), px] else py, pal[5] if g.random() < 0.4 else pal[4])
            if w == 3:
                cv.put(px + 1, py, pal[3])
    return area


def _chunk(cv, pts, seed, pal=STONE, base=0.55, gain=1.2):
    """A broken block of dressed skyport masonry: flat faces, lit upper-left edge."""
    W, H = cv.w, cv.h
    m = m_poly(W, H, pts)
    nz = vnoise(W, H, 3, seed_of("chunk", seed), 1)
    shade(cv, m, pal, contour=True, R=2, strength=2.0, base=base, gain=gain, noise=nz, namp=0.12)
    cv.fill(top_edge(m) & ~right_edge(m), pal[min(len(pal) - 1, 5)])
    return m


def _rubble(cv, cx, by, rx, ry, seed, pal=STONE, n=None, shards=2):
    """A heap of skyport rubble on row `by`: a mound of pale shore grit with broken masonry blocks and
    boulders half-buried in it and a few star-crystal shards poking out."""
    W, H = cv.w, cv.h
    yy = grid(W, H)[1]
    g = rng("rubble", seed)
    bed = blob_mask(W, H, cx, by, rx, ry, ("rub", seed), 0.14, flat_base=by)
    nz = vnoise(W, H, 3, seed_of("rubn", seed), 2)

    def grit(m):
        shade(cv, m, SHORE, contour=True, contour_c=SHORE[2], R=2, strength=1.6, base=0.55, gain=1.1, noise=nz,
              namp=0.25, top=0.1)

    grit(bed)
    cols = bed.any(axis=0)
    surf = np.where(cols, np.argmax(bed, axis=0), by)
    n = n or max(2, int(rx / 4))
    items = []
    for i in range(n):
        px = cx - rx * 0.8 + 1.6 * rx * (i + g.uniform(0.25, 0.75)) / n
        sy = surf[int(np.clip(round(px), 0, W - 1))]
        sz = g.uniform(2.4, 3.8) * min(1.0, 0.55 + ry / 14)
        py = min(by - sz * 0.4, sy + sz * g.uniform(0.0, 0.5))
        items.append((py, px, sz, g.random(), g.uniform(-0.7, 0.7), g.uniform(1.1, 1.8)))
    for k, (py, px, sz, kind, ang, asp) in enumerate(sorted(items)):
        if kind < 0.4:
            rock(cv, px, int(round(min(by, py + sz * 0.7))), sz * 1.1, sz * 0.85, ("rubrock", seed, k), pal=pal, R=1,
                 facets=1, base=0.5)
        else:
            hw, hh = sz * asp * 0.9, sz * 0.75
            ca, sa = math.cos(ang), math.sin(ang)
            pts = [(px + u * ca - v * sa, min(by, py + u * sa + v * ca)) for (u, v) in
                   ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))]
            _chunk(cv, pts, ("rubchunk", seed, k), pal=pal, base=0.52)
    # grit washed back over the feet of the blocks
    front = bed & (yy >= by - max(1.5, ry * 0.3) + (nz - 0.5) * 3)
    grit(front)
    for k in range(shards):
        sx = cx + g.uniform(-rx * 0.7, rx * 0.7)
        _shard(cv, round(sx), int(surf[int(np.clip(round(sx), 0, W - 1))]) + 2, int(g.integers(3, 6)), 2,
               g.uniform(-1.2, 1.2))
    return bed


# ------------------------------------------------------------------ Starsea pirate banner
@prop("pirate_banner", 24, 64)
def pirate_banner(state, f):
    """The banner of the Starsea pirates: deep indigo cloth with a pale comet streaking over a watching
    eye, hung from a salvaged spar and torn ragged at the hem."""
    W, H = 24, 64
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ground_shadow(cv, 12, 62, 8, 1.3)
    plank_h(cv, 6, 57, 17, 61, STONE_DARK, grain=False)
    plank_v(cv, 11, 3, 12, 57, WOOD, grain=False)
    cv.fill(m_poly(W, H, [(10, 3), (11.5, -0.5), (13, 3)]), IRON[4])
    cv.fill(m_rect(W, H, 12, 1, 12, 2), IRON[2])
    plank_h(cv, 3, 5, 20, 6, WOOD, grain=False, base=0.6)
    pts_l = [(4 + math.sin(y * 0.25) * 0.8, y) for y in range(7, 47)]
    pts_r = [(19 + math.sin(y * 0.25 + 0.6) * 0.8, y) for y in range(46, 6, -1)]
    hem = [(4, 50), (5.5, 54), (7, 49), (8.5, 52), (10, 48.5), (11.5, 56), (13, 50), (14.5, 53), (16, 48),
           (17.5, 51), (19, 47)]
    ban = m_poly(W, H, pts_l + hem + pts_r)
    shade(cv, ban, INDIGO, contour=True, mode="cyl", base=0.55, gain=0.9, bias=np.sin(yy * 0.25) * 0.12)
    # frayed pale border and a torn hole near the hem
    cv.fill(ban & ((xx == 5) | (xx == 18)) & (yy < 45) & ((yy % 7) != 3), BONE[2])
    cv.fill(ban & (yy == 8), BONE[3])
    # the emblem: a comet diving over a wide-open eye, three streaks of tail fading out behind it
    hx, hy = 8.5, 20.5
    d = np.hypot(xx - hx, yy - hy)
    for (x0, y0, x1, y1) in ((9, 19, 17, 10), (7, 18, 12, 11), (11, 21, 18, 15)):
        ln = m_line(W, H, [(x0, y0), (x1, y1)]) & ban
        cv.fill(ln, BONE[2])
        cv.fill(ln & (d < 7), BONE[3])
        cv.fill(ln & (d < 4), BONE[4])
    head = m_ellipse(W, H, hx, hy, 2.0, 2.0)
    cv.fill(head, BONE[4])
    cv.fill(m_rect(W, H, 7, 20, 9, 20) | m_rect(W, H, 8, 19, 8, 21), WHITE_HOT)
    eye = m_poly(W, H, [(5, 28), (8, 25), (11.5, 24.2), (15, 25), (18, 28), (15, 31), (11.5, 31.8), (8, 31)])
    cv.fill(eye, BONE[4])
    cv.fill(bottom_edge(eye) | (right_edge(eye) & (yy > 27)), BONE[2])
    iris = m_ellipse(W, H, 11.5, 28, 2.4, 2.4) & eye
    cv.fill(iris, INDIGO[1])
    cv.put(11, 28, INDIGO[0])
    cv.put(12, 28, INDIGO[0])
    cv.put(10, 27, BONE[4])
    for (sx, sy) in ((8, 36), (11, 38), (15, 36)):
        cv.put(sx, sy, BONE[3])
    cv.erase(m_rect(W, H, 14, 42, 15, 43) | m_rect(W, H, 15, 44, 15, 44))
    # frayed rope ends hanging from the spar
    for tx in (3, 20):
        cv.fill(m_rect(W, H, tx, 7, tx, 12), ROPE[3])
        cv.put(tx, 13, ROPE[2])
        cv.put(tx, 9, ROPE[1])
    cv.fill(m_rect(W, H, 10, 5, 13, 6), ROPE[2])
    cv.fill(m_rect(W, H, 10, 5, 13, 6) & ((xx - yy) % 3 == 0), ROPE[4])
    outline(cv)
    return cv


# ------------------------------------------------------------------ Starsea anchor
def _chain(cv, pts, pal=IRON, start=0, step=3.0):
    """A heavy chain along a spline: links alternate face-on ovals (with a dark eye) and edge-on bars."""
    W, H = cv.w, cv.h
    sp = _spline(pts, 0.5)
    acc, links, last = step, [], sp[0]
    for p in sp:
        acc += math.hypot(p[0] - last[0], p[1] - last[1])
        last = p
        if acc >= step:
            links.append(p)
            acc = 0.0
    for i, (x, y) in enumerate(links):
        j = min(len(links) - 1, i + 1)
        dx, dy = links[j][0] - links[max(0, i - 1)][0], links[j][1] - links[max(0, i - 1)][1]
        n = math.hypot(dx, dy) or 1.0
        ux, uy = dx / n, dy / n
        if (i + start) % 2 == 0:
            m = tube(W, H, [(x - ux * 1.7, y - uy * 1.7), (x + ux * 1.7, y + uy * 1.7)], 1.6)
            cv.fill(m, pal[3])
            cv.fill(m & ~shift(m, -1, -1), pal[2])
            cv.fill(m & ~shift(m, 1, 1), pal[5])
            cv.put(round(x), round(y), pal[0])
        else:
            m = m_line(W, H, [(x - ux * 2.2, y - uy * 2.2), (x + ux * 2.2, y + uy * 2.2)])
            cv.fill(m, pal[2])


@prop("starsea_anchor", 44, 48, ground=3)
def starsea_anchor(state, f):
    """A huge old iron anchor from the skyport's moorings, fallen and half-sunk in the rubble: rust
    blooming on the iron, a crust of star-crystal on the buried crown, and a length of heavy chain
    run out from the ring."""
    W, H = 44, 48
    cv = Canvas(W, H)
    yy = grid(W, H)[1]
    gy = 45
    ground_shadow(cv, 22, gy, 21, 1.6)
    P = _rot(19.0, 41.0, math.radians(15))
    nz = vnoise(W, H, 3, seed_of("anchor"), 2)
    rn = vnoise(W, H, 4, seed_of("anchor_rust"), 2)

    def iron(m, base=0.5, gain=1.3, R=2):
        shade(cv, m, IRON, contour=True, R=R, strength=2.2, base=base, gain=gain, noise=nz, namp=0.15)
        rust = m & erode(m) & (rn > 0.62)
        lit = m & ~shift(m, 1, 1)
        cv.fill(rust & ~lit, RUST[2])
        cv.fill(rust & lit, RUST[4])
        cv.fill(rust & (rn > 0.72) & ~lit, RUST[3])
        return m

    # stock (behind the shank), shank, ring
    iron(tube(W, H, [P(-9, -29.5), P(9, -29.5)], 1.4), base=0.5, R=1)
    for u in (-9.5, 9.5):
        iron(m_ellipse(W, H, *P(u, -29.5), 2.3, 2.3), base=0.6, R=1)
    iron(tube(W, H, [P(0, -33), P(0, -3)], 2.2, 3.1), base=0.58)
    rc = P(0, -37.5)
    ring = m_ellipse(W, H, rc[0], rc[1], 4.3, 4.3) & ~m_ellipse(W, H, rc[0], rc[1], 2.1, 2.1)
    iron(ring, base=0.6, R=1)
    # arms and broad spade flukes
    for s in (-1, 1):
        arm = tube(W, H, [P(0, -1), P(s * 6.5, 0), P(s * 11, -3.5), P(s * 13, -8.5)], 2.6, 1.9)
        iron(arm, base=0.6 if s < 0 else 0.42)
        fl = m_poly(W, H, [P(s * 9.5, -5.5), P(s * 13, -15.5), P(s * 17.5, -7), P(s * 13.5, -4)])
        iron(fl, base=0.62 if s < 0 else 0.42, R=1)
    iron(m_ellipse(W, H, *P(0, -1), 3.4, 3.4), base=0.5, R=1)
    _crust(cv, cv.solid & (yy > 30), "anchor", 0.3)
    # rubble drifted over the crown, the chain run out from the ring and down over it
    _rubble(cv, 19, gy, 16, 11, "anchor_l", n=5, shards=2)
    _chain(cv, [(rc[0] + 1.5, rc[1] + 3.5), (37, 14), (40.5, 25), (40, 36), (36, gy - 1), (29, gy)], step=3.4)
    _rubble(cv, 39, gy, 4.5, 3, "anchor_r", n=1, shards=0)
    outline(cv)
    return cv


# ------------------------------------------------------------------ star-sight stone
@prop("star_sight_stone", 36, 56, states=(("idle", 1, 0), ("active", 4, 5)), ground=3)
def star_sight_stone(state, f):
    """A weathered standing stone of the navigators, its face engraved with the sky-road constellations
    and a bronze sighting ring set on its crown. Wakened, the engraved stars shine pale jade."""
    W, H = 36, 56
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 53
    on = state == "active"
    ground_shadow(cv, 18, gy, 16, 1.6)
    # the slab: a tapering monolith with a chipped crown
    st = m_poly(W, H, [(8, gy), (9, 30), (10, 20), (12, 16), (16, 14), (21, 14.5), (25, 17), (26, 24), (27, 36),
                       (28, gy)])
    nz = vnoise(W, H, 3, seed_of("sightstone"), 2)
    shade(cv, st, STONE, contour=True, R=3, strength=2.2, base=0.55, gain=1.3, noise=nz, namp=0.2, ao=0.1)
    cv.fill(left_edge(st) & (yy > 18) & (yy < gy - 2), STONE[5])
    # constellations: star pits joined by fine engraved lines
    consts = [[(13, 21), (16, 19), (19, 22), (22, 20)],
              [(12, 29), (15, 31), (14, 35), (18, 34), (21, 37), (24, 34)],
              [(14, 42), (18, 44), (22, 42), (19, 47)]]
    big = {(16, 19), (18, 34), (18, 44)}
    face = erode(st)
    for ci, stars in enumerate(consts):
        lit = on and (f % 4 != (ci + 1) % 4)
        peak = on and (f % 4 == ci % 4)
        ln = m_line(W, H, stars) & face
        cv.fill(ln, (JADE_R[4] if peak else JADE_R[3]) if lit else STONE[2])
        if not on:
            cv.fill(shift(ln, 1, 1) & face & ~ln, STONE[4])
        for (sx, sy) in stars:
            pit = m_rect(W, H, sx, sy, sx, sy)
            if (sx, sy) in big:
                pit |= m_rect(W, H, sx - 1, sy, sx + 1, sy) | m_rect(W, H, sx, sy - 1, sx, sy + 1)
            if lit:
                cv.fill(pit, JADE_R[5])
                cv.put(sx, sy, JADE_R[6] if peak or (sx, sy) in big else JADE_R[5])
            else:
                cv.fill(pit, STONE[1])
                cv.fill(shift(pit, 1, 1) & face & ~pit, STONE[5])
    # lichen low on the weather side and a few chips
    moss_c = st & (nz > 0.62) & (yy > 44) & ~dilate(m_rect(W, H, 10, 40, 25, 49))
    cv.fill(moss_c, MOSS[2])
    cv.fill(moss_c & shift(~moss_c, 0, -1), MOSS[3])
    # the bronze sighting ring, held in a fork on a short post, with fine cross-wires
    rcx, rcy, rr = 17.5, 6.5, 6.0
    hole = m_ellipse(W, H, rcx, rcy, rr - 1.6, rr - 1.6)
    post = m_rect(W, H, 17, 12, 18, 15)
    shade(cv, post, BRONZE, contour=True, mode="cyl", base=0.55, gain=1.0)
    cv.fill(m_rect(W, H, 15, 14, 20, 15), BRONZE[3])
    cv.fill(m_rect(W, H, 15, 14, 19, 14), BRONZE[5])
    ringm = m_ellipse(W, H, rcx, rcy, rr, rr) & ~hole
    shade(cv, ringm, BRONZE, contour=False, mode="sphere", base=0.62, gain=1.2)
    cv.fill(ringm & ~shift(ringm, 1, 1) & (xx + yy < rcx + rcy), GOLD[5])
    cv.fill(ringm & ~shift(ringm, -1, -1) & (xx + yy > rcx + rcy), BRONZE[1])
    wires = (m_rect(W, H, rcx - rr, 6, rcx + rr, 6) | m_rect(W, H, 17, rcy - rr, 17, rcy + rr)) & hole
    cv.fill(wires, BRONZE[2])
    cv.put(17, 6, GOLD[5])
    for sx in (11, 23):
        cv.put(sx, 6, BRONZE[4])
    # rubble and tufts at the foot
    rock(cv, 7, gy, 3.5, 2.8, "sight_r1", pal=STONE, R=1, facets=1)
    rock(cv, 29, gy, 3, 2.4, "sight_r2", pal=STONE, R=1, facets=1)
    grass_tuft(cv, 11, gy, "sight_g1", h=4, n=3)
    grass_tuft(cv, 25, gy, "sight_g2", h=3, n=2)
    outline(cv, skip=hole & ~cv.solid)
    if on:
        a = (0.08, 0.12, 0.1, 0.14)[f % 4]
        glow(cv, 18, 33, 12, 18, BRIGHT_JADE, steps=((1.0, a * 0.6), (0.65, a)))
        motes(cv, 9, 8, 27, 46, f, 4, "sight_m", count=6, pal=(BRIGHT_JADE, JADE_R[6]))
    return cv


# ------------------------------------------------------------------ Trial Hall: pressure pillar
_PILLAR_GLYPHS = ((".#.", "#.#", ".#.", "...", "###"), ("#.#", ".#.", "#.#", "...", "#.#"),
                  ("###", "...", ".#.", "...", "###"), (".#.", "###", ".#.", "#.#", "#.#"),
                  ("#.#", "###", "#.#", "...", ".#."), ("###", "#.#", "...", ".#.", ".#."))

@prop("pressure_pillar", 28, 96, states=(("idle", 1, 0), ("active", 4, 6)), ground=3)
def pressure_pillar(state, f):
    """A tall pillar of the Trial Hall carved with two bands of pressure runes. While the Presence Trial
    runs, the runes pulse violet-white, the brightest glyph climbing the shaft."""
    W, H = 28, 96
    cv = Canvas(W, H)
    gy = 93
    on = state == "active"
    ground_shadow(cv, 14, gy, 13, 1.6)
    nz = vnoise(W, H, 3, seed_of("pillar"), 2)

    def block(m, base=0.55, gain=1.2, R=2, mode="bevel"):
        shade(cv, m, STONE, contour=True, mode=mode, R=R, strength=2.0, base=base, gain=gain, noise=nz, namp=0.18)
        return m

    # stepped plinth
    block(m_rect(W, H, 2, 88, 25, gy), base=0.5, R=1)
    cv.fill(m_rect(W, H, 2, 88, 25, 88), STONE[5])
    block(m_rect(W, H, 4, 83, 23, 87), base=0.55, R=1)
    cv.fill(m_rect(W, H, 4, 83, 23, 83), STONE[5])
    # shaft
    block(m_rect(W, H, 6, 16, 21, 82), mode="cyl", base=0.55, gain=1.1)
    # bronze collars
    for (y0, y1) in ((16, 18), (79, 81)):
        band = m_rect(W, H, 5, y0, 22, y1)
        shade(cv, band, BRONZE, contour=True, mode="cyl", base=0.55, gain=1.2)
        cv.fill(m_rect(W, H, 5, y0, 22, y0), BRONZE[5])
    # capital: a flared cap with a peaked top
    cap = m_poly(W, H, [(6, 15), (3, 11), (3, 9), (24, 9), (24, 11), (21, 15)])
    block(cap, base=0.58, R=1)
    cv.fill(m_rect(W, H, 3, 9, 24, 9), STONE[6])
    top = m_poly(W, H, [(5, 8), (9, 4), (18, 4), (22, 8)])
    block(top, base=0.6, R=1)
    cv.fill(m_poly(W, H, [(12, 4), (13.5, 0), (15, 4)]), BRONZE[4])
    cv.put(13, 1, BRONZE[6])
    # two recessed rune bands
    pulse = (0, 1, 2, 3)[f % 4]
    for bx in (8, 15):
        chan = m_rect(W, H, bx, 21, bx + 4, 77)
        cv.fill(chan, STONE[1] if not on else VIOLET[1])
        cv.fill(left_edge(chan) | top_edge(chan), STONE[0] if not on else VIOLET[0])
        cv.fill(right_edge(chan) & ~top_edge(chan), STONE[3])
        g = rng("pillar_runes", bx)
        for k, gy2 in enumerate(range(23, 75, 7)):
            rows = _PILLAR_GLYPHS[int(g.integers(0, len(_PILLAR_GLYPHS)))]
            glyph = np.zeros((H, W), bool)
            for r, row in enumerate(rows):
                for c, ch in enumerate(row):
                    if ch == "#":
                        glyph[gy2 + r, bx + 1 + c] = True
            if on:
                lvl = (k + (bx == 15) * 3 + 2 * pulse) % 8
                c = VIOLET[6] if lvl < 1 else (VIOLET[5] if lvl < 3 else VIOLET[4])
                cv.fill(glyph, c)
                if lvl < 1:
                    cv.put(bx + 2, gy2 + 2, WHITE_HOT)
            else:
                cv.fill(glyph, STONE[3])
    outline(cv)
    if on:
        a = (0.1, 0.14, 0.12, 0.16)[f % 4]
        glow(cv, 13.5, 49, 11, 34, VIOLET[5], steps=((1.0, a * 0.5), (0.7, a * 0.7), (0.45, a)))
        motes(cv, 5, 12, 22, 80, f, 4, "pillar_m", count=6, pal=(VIOLET[5], WHITE_HOT))
    return cv


# ------------------------------------------------------------------ Trial Hall: elder's seat
@prop("trial_seat", 48, 72, ground=3)
def trial_seat(state, f):
    """A high stone seat of the Trial Hall, one of nine set in a ring: a tall back crowned with three
    peaks and carved with the Alliance's mountain mark, a jade stone set above the summit."""
    W, H = 48, 72
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 69
    cx = 24
    P = STONE
    nz = vnoise(W, H, 3, seed_of("trialseat"), 2)
    ground_shadow(cv, cx, gy, 23, 1.8)

    def block(m, base=0.55, gain=1.2, R=2, mode="bevel"):
        shade(cv, m, P, contour=True, mode=mode, R=R, strength=2.0, base=base, gain=gain, noise=nz, namp=0.12)
        return m

    # tall back with a three-peak crest
    back = m_poly(W, H, [(12, 48), (12, 13), (15, 8), (18.5, 12), (24, 2), (29.5, 12), (33, 8), (36, 13), (36, 48)])
    block(back, base=0.55, gain=1.1)
    cv.fill(m_line(W, H, [(12, 13), (15, 8), (18, 11)]) | m_line(W, H, [(19, 11), (24, 2)]), P[6])
    # carved panel: the mountain mark in relief with jade in the summit
    panel = m_rect(W, H, 16, 17, 32, 40)
    cv.fill(erode(panel), P[3])
    cv.fill(top_edge(panel) | left_edge(panel), P[1])
    cv.fill((right_edge(panel) | bottom_edge(panel)) & ~(top_edge(panel) | left_edge(panel)), P[5])
    # three summits in relief, each with a lit west face and a shaded east face
    for (ax, ay, hw) in ((19.5, 28, 3.5), (28.5, 28, 3.5), (24, 23, 5.5)):
        pk = m_poly(W, H, [(ax - hw, 36), (ax, ay), (ax + hw, 36)])
        cv.fill(pk & (xx < ax), P[5])
        cv.fill(pk & (xx >= ax), P[3])
        cv.fill(left_edge(pk) & (xx < ax), P[6])
        cv.fill(right_edge(pk) & (xx > ax), P[2])
    cv.fill(m_rect(W, H, 23, 23, 24, 24), P[6])
    cv.fill(m_rect(W, H, 18, 37, 30, 37), P[2])
    for x in (19, 21, 23, 25, 27, 29):
        cv.put(x, 38, P[4] if x < 24 else P[2])
    jade = m_poly(W, H, [(24, 18), (26, 20), (24, 22), (22, 20)])
    cv.fill(jade, JADE_R[3])
    cv.fill(top_edge(jade) | left_edge(jade), JADE_R[5])
    cv.fill(bottom_edge(jade) & right_edge(jade), JADE_R[1])
    cv.put(23, 19, JADE_R[6])
    # armrests: blocks with a cloud scroll on the front
    for (x0, x1) in ((6, 13), (35, 42)):
        arm = m_rect(W, H, x0, 38, x1, 57)
        block(arm, base=0.6 if x0 < cx else 0.45, gain=1.1)
        cv.fill(m_rect(W, H, x0, 38, x1, 39), P[5] if x0 < cx else P[4])
        sc = ellipse_ring(W, H, (x0 + x1) / 2, 47, 2.5, 2.5)
        cv.fill(sc & (xx + yy < (x0 + x1) / 2 + 47), P[2])
        cv.fill(sc & (xx + yy >= (x0 + x1) / 2 + 47), P[4])
        cv.put((x0 + x1) // 2, 47, P[2])
    # seat with a navy cushion
    seat = m_rect(W, H, 12, 45, 36, 57)
    block(seat, base=0.45, gain=1.0)
    cv.fill(m_rect(W, H, 12, 45, 36, 46), P[4])
    navy = ramp("#0b1226", "#16213f", "#223260", "#2f4580", "#4460a0", "#6a86bf")
    cush = m_poly(W, H, [(13, 44), (35, 44), (35, 48), (13, 48)])
    shade(cv, cush, navy, contour=True, R=1, base=0.6, gain=1.0)
    cv.fill(m_rect(W, H, 14, 44, 34, 44), navy[5])
    cv.fill(m_rect(W, H, 13, 48, 35, 48) & ((xx % 3) == 0), GOLD[3])
    # two-step dais
    for (x0, x1, y0, y1) in ((4, 43, 58, 63), (1, 46, 64, gy)):
        step = m_rect(W, H, x0, y0, x1, y1)
        block(step, base=0.5, gain=1.0, R=1)
        cv.fill(m_rect(W, H, x0, y0, x1, y0), P[5])
        cv.fill(m_rect(W, H, x0, y0, x0, y1), P[4])
        for jx in range(x0 + 9, x1 - 3, 10):
            cv.fill(m_rect(W, H, jx, y0 + 1, jx, y1), P[2])
    outline(cv)
    return cv


# ------------------------------------------------------------------ navigator's yard: armillary sphere
def _view3d(yaw, elev):
    """World (x right, y down, z toward the viewer) -> view rotation: turn about the vertical axis by
    yaw, then tip toward the viewer by elev so near points sit lower on screen."""
    cy_, sy_ = math.cos(yaw), math.sin(yaw)
    ce, se = math.cos(elev), math.sin(elev)
    ry = np.array([[cy_, 0, sy_], [0, 1, 0], [-sy_, 0, cy_]])
    rx = np.array([[1, 0, 0], [0, ce, se], [0, -se, ce]])
    return rx @ ry


def _ring_pts(u, v, r, n=180, c=(0.0, 0.0, 0.0)):
    """Sample a 3D circle of radius r spanned by the unit vectors u, v around centre c."""
    s = np.linspace(0, 2 * math.pi, n, endpoint=False)
    u, v, c = np.asarray(u, float), np.asarray(v, float), np.asarray(c, float)
    return c[None, :] + r * (np.cos(s)[:, None] * u[None, :] + np.sin(s)[:, None] * v[None, :])


class _ZBuf:
    """A tiny depth buffer for drawing interlocking rings: each pixel keeps the nearest sample's
    palette, ramp index and depth."""

    def __init__(self, W, H):
        self.W, self.H = W, H
        self.z = np.full((H, W), -1e9)
        self.v = np.zeros((H, W))
        self.pal = np.full((H, W), -1, int)
        self.pals = []

    def splat(self, pts, view, cx, cy, pal, rad=0.8, lit=0.5, gain=1.2, scale=1.0):
        pid = len(self.pals)
        self.pals.append(pal)
        P = pts @ view.T
        rr = int(math.ceil(rad))
        R = np.max(np.linalg.norm(P, axis=1)) or 1.0
        for (x, y, z) in P:
            sx, sy = cx + x, cy + y
            val = lit + gain * (0.35 * z / R - 0.18 * (x + y) / R)
            for dy in range(-rr, rr + 1):
                for dx in range(-rr, rr + 1):
                    px, py = int(round(sx + dx)), int(round(sy + dy))
                    if not (0 <= px < self.W and 0 <= py < self.H):
                        continue
                    if (px - sx) ** 2 + (py - sy) ** 2 > rad * rad + 0.25:
                        continue
                    if z > self.z[py, px]:
                        self.z[py, px] = z
                        self.v[py, px] = val
                        self.pal[py, px] = pid

    def paint(self, cv):
        for pid, pal in enumerate(self.pals):
            m = self.pal == pid
            if m.any():
                cv.fill_idx(m, np.clip(np.floor(self.v * len(pal)), 0, len(pal) - 1), pal)
        return self.pal >= 0


@prop("armillary_sphere", 40, 64, states=(("idle", 4, 3),), ground=3)
def armillary_sphere(state, f):
    """A bronze armillary sphere of the navigators on a stone plinth: a fixed meridian ring and horizon
    ring on curved legs, a gilt ring that turns slowly about the tilted polar axis, and a small jade
    star held at the heart of it all."""
    W, H = 40, 64
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 61
    cx, cy, r = 20, 22, 14.5
    ground_shadow(cv, cx, gy, 17, 1.6)
    nz = vnoise(W, H, 3, seed_of("armillary"), 2)
    # plinth: a stepped stone block with a carved band
    for (x0, x1, y0, y1) in ((6, 33, 53, gy), (10, 29, 46, 52)):
        blk = m_rect(W, H, x0, y0, x1, y1)
        shade(cv, blk, STONE, contour=True, R=1, base=0.5, gain=1.1, noise=nz, namp=0.15)
        cv.fill(m_rect(W, H, x0, y0, x1, y0), STONE[5])
        cv.fill(m_rect(W, H, x0, y0, x0, y1), STONE[4])
    cv.fill(m_rect(W, H, 9, 57, 30, 57) & ((xx % 3) != 0), STONE[2])
    # the column and two curved legs up to the horizon ring
    col = m_rect(W, H, 18, 36, 21, 45)
    shade(cv, col, BRONZE, contour=True, mode="cyl", base=0.55, gain=1.1)
    cv.fill(m_rect(W, H, 16, 44, 23, 45), BRONZE[3])
    cv.fill(m_rect(W, H, 16, 44, 22, 44), BRONZE[5])
    for s in (-1, 1):
        leg = tube(W, H, [(cx + s * 7, 45), (cx + s * 12.5, 40), (cx + s * 15, 32), (cx + s * 14.8, 24)], 1.3, 1.0)
        shade(cv, leg, BRONZE, contour=True, R=1, base=0.55 if s < 0 else 0.4, gain=1.1)
    # the rings, drawn through a depth buffer so they pass in front of and behind each other
    view = _view3d(math.radians(32), math.radians(14))
    a = math.radians(28)
    pole = np.array([math.sin(a), -math.cos(a), 0.0])
    w = np.array([math.cos(a), math.sin(a), 0.0])
    phi = math.radians(45 * (f % 4))
    zb = _ZBuf(W, H)
    zb.splat(_ring_pts((1, 0, 0), (0, 1, 0), r), view, cx, cy, BRONZE, rad=1.1, lit=0.55)          # meridian
    zb.splat(_ring_pts((1, 0, 0), (0, 0, 1), r + 0.5), view, cx, cy, BRONZE, rad=1.0, lit=0.5)     # horizon
    zb.splat(_ring_pts(pole, w * math.cos(phi) + np.array([0, 0, 1.0]) * math.sin(phi), r - 6.5), view, cx, cy,
             GOLD, rad=0.8, lit=0.62, gain=1.4)                                                      # turning ring
    axis = np.array([pole * t for t in np.linspace(-(r + 2.5), r + 2.5, 80)])
    zb.splat(axis, view, cx, cy, BRONZE, rad=0.5, lit=0.5)
    rings = zb.paint(cv)
    # meridian graduations
    for k in range(12):
        s = 2 * math.pi * k / 12
        p = (np.array([math.cos(s), math.sin(s), 0.0]) * r) @ view.T
        px, py = int(round(cx + p[0])), int(round(cy + p[1]))
        if rings[py, px] and zb.pal[py, px] == 0:
            cv.put(px, py, BRONZE[1] if k % 3 else GOLD[5])
    # the jade star at the heart
    sm = (m_rect(W, H, cx - 3, cy, cx + 3, cy) | m_rect(W, H, cx, cy - 3, cx, cy + 3)
          | m_rect(W, H, cx - 1, cy - 1, cx + 1, cy + 1))
    cv.fill(dilate(sm) & ~rings, JADE_R[1])
    cv.fill(sm, JADE_R[4])
    cv.fill(sm & (xx + yy < cx + cy), JADE_R[5])
    cv.fill(m_rect(W, H, cx - 1, cy - 1, cx, cy), JADE_R[6])
    cv.put(cx - 1, cy - 1, WHITE_HOT)
    # the pole caps
    for t in (-1, 1):
        p = (pole * t * (r + 2.5)) @ view.T
        cap = m_ellipse(W, H, cx + p[0], cy + p[1], 1.3, 1.3)
        cv.fill(cap, GOLD[4] if t > 0 else BRONZE[3])
    hole = m_ellipse(W, H, cx, cy, r - 1.5, r - 1.5) & ~cv.solid
    outline(cv, skip=hole)
    glow(cv, cx, cy, 6, 6, BRIGHT_JADE, steps=((1.0, 0.07), (0.6, 0.1)))
    return cv


# ------------------------------------------------------------------ Skyport Wreck: star ballista
@prop("star_ballista", 64, 48, ground=3)
def star_ballista(state, f):
    """A heavy deck crossbow salvaged by the Starsea pirates: a red-lacquered prod on a long weathered
    stock that swivels on a bronze drum, a winch at the breech, a rune burned into the stock, and a
    bronze bolt tipped with star-iron laid in the groove."""
    W, H = 64, 48
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 45
    ground_shadow(cv, 32, gy, 24, 1.8)
    nz = vnoise(W, H, 3, seed_of("ballista"), 2)
    # timber deck block and the bronze swivel drum
    deck = m_rect(W, H, 14, 41, 50, gy)
    shade(cv, deck, WOOD, contour=True, R=1, base=0.45, gain=1.0, noise=nz, namp=0.15)
    cv.fill(m_rect(W, H, 14, 41, 50, 41), WOOD[4])
    for bx in (22, 32, 42):
        cv.fill(m_rect(W, H, bx, 42, bx, gy), WOOD[1])
    for bx in (14, 49):
        cv.fill(m_rect(W, H, bx, 41, bx + 1, 43), IRON[3])
        cv.put(bx, 41, IRON[5])
    drum = m_rect(W, H, 25, 35, 38, 40)
    shade(cv, drum, BRONZE, contour=True, mode="cyl", base=0.5, gain=1.2)
    cv.fill(m_rect(W, H, 25, 40, 38, 40), BRONZE[1])
    top = m_rect(W, H, 23, 34, 40, 35)
    shade(cv, top, BRONZE, contour=True, R=1, base=0.6, gain=0.8)
    cv.fill(m_rect(W, H, 23, 34, 40, 34), GOLD[5])
    # the yoke cheeks and trunnion
    yoke = m_poly(W, H, [(27, 35), (28.5, 25), (34.5, 25), (36, 35)])
    shade(cv, yoke, BRONZE, contour=True, R=1, base=0.45, gain=1.2)
    cv.fill(left_edge(yoke), BRONZE[5])
    # the stock: a long weathered beam rising toward the prod
    x0, y0, x1, y1 = 6.0, 33.0, 55.0, 19.0
    slope = (y1 - y0) / (x1 - x0)

    def sy(x):
        return y0 + (x - x0) * slope

    stock = m_poly(W, H, [(x0, y0 - 2), (x1, y1 - 2), (x1, y1 + 1.5), (x0 + 3, y0 + 2.5), (x0, y0 + 2.5)])
    shade(cv, stock, WOOD_GREY, contour=True, R=1, base=0.55, gain=1.3)
    for gx in (12, 26, 40):
        cv.fill(m_line(W, H, [(gx, sy(gx)), (gx + 5, sy(gx + 5))]) & erode(stock), WOOD_GREY[2])
    for bxx in (10, 45, 53):
        band = stock & (np.abs(xx - bxx) <= 0.6)
        cv.fill(band, GOLD[4])
        cv.fill(band & shift(~stock, 0, 1), BRONZE[2])
    cv.fill(m_ellipse(W, H, 31.5, sy(31.5) + 0.5, 1.4, 1.4), GOLD[5])
    cv.put(32, int(round(sy(31.5) + 1)), BRONZE[2])
    # rune burned into the breech
    ry0 = int(round(sy(15)))
    rune = (m_rect(W, H, 14, ry0, 16, ry0) | m_rect(W, H, 15, ry0 - 1, 15, ry0 + 1)
            | m_rect(W, H, 14, ry0 + 2, 14, ry0 + 2) | m_rect(W, H, 16, ry0 + 2, 16, ry0 + 2))
    cv.fill(dilate(rune) & stock, WOOD_GREY[1])
    cv.fill(rune & stock, RUNE[3])
    cv.put(15, ry0, RUNE[4])
    # winch at the breech: a spoked wheel with a crank
    wc = (10, 39)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        bar = m_line(W, H, [wc, (wc[0] + math.cos(a) * 5, wc[1] + math.sin(a) * 5)], 1)
        cv.fill(bar, WOOD[5] if k in (2, 3) else WOOD[3])
    hub = m_ellipse(W, H, *wc, 2.2, 2.2)
    shade(cv, hub, GOLD, contour=True, mode="sphere", base=0.5, gain=1.2)
    cv.put(wc[0], wc[1], BRONZE[1])
    # the prod: a lacquered recurve bow set crosswise at the head, drawn back and spanned
    bx, by = 47.0, sy(47)
    tips = []
    for s in (-1, 1):
        pts = [(bx, by), (bx - 1.5, by + s * 7), (bx - 4.5, by + s * 13), (bx - 6.0, by + s * 15.5),
               (bx - 5.2, by + s * 17)]
        limb = tube(W, H, pts, 2.2, 0.9)
        shade(cv, limb, LACQUER, contour=True, R=1, base=0.55 if s < 0 else 0.4, gain=1.2)
        cv.fill(m_ellipse(W, H, pts[-1][0], pts[-1][1], 1.2, 1.2), GOLD[4])
        tips.append(pts[-2])
    cv.fill(m_rect(W, H, int(bx) - 1, int(by) - 2, int(bx) + 1, int(by) + 2), GOLD[3])
    cv.fill(m_rect(W, H, int(bx) - 1, int(by) - 2, int(bx) - 1, int(by) + 1), GOLD[5])
    nut = (23.0, sy(23) - 2)
    for t in tips:
        cv.fill(m_line(W, H, [t, nut]), ROPE[4])
    cv.fill(m_rect(W, H, 21, int(nut[1]) - 1, 24, int(nut[1]) + 1), GOLD[3])
    # the bolt: a bronze shaft with vanes and a long four-pointed star-iron head
    bs, be = (24.0, sy(24) - 3), (57.0, sy(57) - 3)
    shaft = m_line(W, H, [bs, be])
    cv.fill(shift(shaft, 0, 1) & ~shaft, BRONZE[1])
    cv.fill(shaft, BRONZE[5])
    vane = m_poly(W, H, [(25, sy(25) - 3), (29, sy(29) - 3), (24, sy(24) - 6.5)])
    cv.fill(vane, GOLD[4])
    cv.fill(bottom_edge(vane) | right_edge(vane), BRONZE[3])
    hx, hy = 58.5, sy(58.5) - 3
    ux, uy = math.cos(math.atan(slope)), math.sin(math.atan(slope))
    head = m_poly(W, H, [(hx - ux * 2, hy - uy * 2), (hx + uy * 2.6, hy - ux * 2.6), (hx + ux * 5, hy + uy * 5),
                         (hx - uy * 2.6, hy + ux * 2.6)])
    cv.fill(head, STORMSTEEL[3])
    cv.fill(head & (yy < hy - 0.2), STORMSTEEL[4])
    cv.fill(head & (yy > hy + 1.2), STORMSTEEL[2])
    cv.put(int(round(hx + 1)), int(round(hy - 1)), STORMSTEEL[5])
    outline(cv)
    glow(cv, 15, ry0 + 0.5, 3.5, 3, RUNE[3], steps=((1.0, 0.12),))
    sparkle(cv, int(round(hx + 1)), int(round(hy - 1)), 1, WHITE_HOT, STORMSTEEL[4], 0.7)
    return cv


# ------------------------------------------------------------------ navigator's yard: star chart table
@prop("star_chart_table", 64, 44, ground=3)
def star_chart_table(state, f):
    """The navigator's work table: a star chart spread flat under four bronze weights, dotted with the
    sky-road constellations, beside a brass sighting compass, an ink stone and a brush."""
    W, H = 64, 44
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 41
    ground_shadow(cv, 32, gy, 30, 1.8)
    nz = vnoise(W, H, 3, seed_of("charttable"), 2)
    P = ROSEWOOD
    # back legs, apron, front legs with scrolled feet and a stretcher
    for lx in (12, 49):
        shade(cv, m_rect(W, H, lx, 24, lx + 2, gy - 5), P, contour=True, mode="cyl", base=0.3, gain=0.8)
    shade(cv, m_rect(W, H, 8, 33, 55, 34), P, contour=True, R=1, base=0.45, gain=1.0)
    for lx, s in ((5, -1), (55, 1)):
        leg = m_rect(W, H, lx, 23, lx + 3, gy - 1)
        shade(cv, leg, P, contour=True, mode="cyl", base=0.55, gain=1.1)
        foot = m_ellipse(W, H, lx + 1.5 + s * 1.2, gy - 0.5, 2.8, 1.6) & (yy <= gy)
        shade(cv, foot, P, contour=True, R=1, base=0.5, gain=1.0)
    apron = m_rect(W, H, 5, 22, 58, 25)
    shade(cv, apron, P, contour=True, R=1, base=0.45, gain=1.0)
    for k, ax in enumerate(range(12, 54, 8)):
        sc = ellipse_ring(W, H, ax, 23.5, 1.6, 1.2)
        cv.fill(sc & apron, P[1] if k % 2 else P[4])
    for cxx in (5, 58):
        cv.fill(m_rect(W, H, cxx - (cxx > 30), 22, cxx + (cxx < 30), 23), GOLD[3])
    # the table top: front edge and the top surface seen from a little above
    edge = m_rect(W, H, 2, 18, 61, 21)
    shade(cv, edge, P, contour=True, R=1, base=0.55, gain=1.0)
    cv.fill(m_rect(W, H, 2, 18, 61, 18), P[5])
    surf = m_poly(W, H, [(5, 7), (58, 7), (61, 17), (2, 17)])
    shade(cv, surf, P, mode="flat", base=0.62, gain=0.0, noise=nz, namp=0.12,
          bias=np.clip((yy - 7) / 10.0, 0, 1) * 0.12)
    cv.fill(top_edge(surf), P[2])
    # the star chart: pale paper laid across the top and hanging over the front edge to a rolled end
    chart = m_poly(W, H, [(15, 8), (46, 8), (48, 17), (13, 17)])
    drape = m_rect(W, H, 14, 17, 47, 24)
    shade(cv, chart, PAPER_R, mode="flat", base=0.72, gain=0.0, noise=nz, namp=0.1,
          bias=-np.clip((xx - 13) / 36.0, 0, 1) * 0.1)
    shade(cv, drape, PAPER_R, mode="flat", base=0.6, gain=0.0, noise=nz, namp=0.1,
          bias=-np.clip((xx - 13) / 36.0, 0, 1) * 0.1)
    cv.fill(left_edge(chart) | top_edge(chart), PAPER_R[5])
    cv.fill(m_rect(W, H, 14, 17, 47, 17), PAPER_R[5])
    cv.fill(right_edge(drape), PAPER_R[2])
    roll = m_rect(W, H, 13, 24, 48, 26)
    shade(cv, roll, PAPER_R, mode="cylh", base=0.6, gain=1.0)
    for ex in (12, 49):
        cv.fill(m_rect(W, H, ex, 24, ex, 26), LACQUER[3])
        cv.put(ex, 24, LACQUER[5])
    paper = chart | drape
    circ = ((ellipse_ring(W, H, 30.5, 12.5, 12, 3.6) & chart & (yy < 16))
            | (ellipse_ring(W, H, 30.5, 23, 11, 4.5) & drape & (yy > 18)))
    cv.fill(circ, PAPER_R[3])
    ink = hexc("#23304f")
    for stars in ([(17, 10), (20, 9), (23, 11), (21, 14)], [(27, 13), (30, 11), (33, 12), (36, 10)],
                  [(39, 15), (42, 12), (44, 14)], [(40, 9), (43, 10)],
                  [(17, 19), (20, 21), (19, 23)], [(24, 18), (27, 20), (31, 19), (33, 22)],
                  [(37, 20), (40, 18), (44, 21)]):
        cv.fill(m_line(W, H, stars) & paper, PAPER_R[1])
        for (sx, sy_) in stars:
            cv.put(sx, sy_, ink)
    for (sx, sy_) in ((30, 11), (27, 20)):
        cv.put(sx, sy_, CLOTH_RED[4])
    cv.put(42, 12, GOLD[3])
    cv.put(40, 18, GOLD[3])
    # bronze weights on the corners
    for (wx, wy) in ((14, 7), (44, 7), (12, 15), (46, 15)):
        wm = m_rect(W, H, wx, wy, wx + 2, wy + 1)
        cv.fill(wm, BRONZE[3])
        cv.fill(m_rect(W, H, wx, wy, wx + 1, wy), BRONZE[5])
        cv.put(wx + 2, wy + 1, BRONZE[1])
    # ink stone with its pool of ink, and a brush beside it
    stone = m_rect(W, H, 4, 10, 10, 14)
    shade(cv, stone, STONE_DARK, contour=True, R=1, base=0.45, gain=1.0)
    cv.fill(m_rect(W, H, 4, 10, 10, 10) | m_rect(W, H, 4, 10, 4, 14), STONE_DARK[5])
    cv.fill(m_rect(W, H, 6, 11, 8, 12), INK)
    cv.put(6, 11, STONE_DARK[3])
    cv.fill(m_line(W, H, [(4, 16), (10, 15)]), STRAW[4])
    cv.fill(m_rect(W, H, 11, 15, 12, 15), INK)
    # the brass sighting compass: a round dial with a needle under a standing sight-arc
    dial = m_ellipse(W, H, 54, 12, 4.5, 2)
    shade(cv, dial, GOLD, contour=True, R=1, base=0.6, gain=0.9)
    cv.fill(m_ellipse(W, H, 54, 12, 3, 1), PAPER_R[4])
    cv.fill(m_rect(W, H, 55, 12, 56, 12), CLOTH_RED[3])
    cv.fill(m_rect(W, H, 52, 12, 53, 12), IRON[2])
    arc = ellipse_ring(W, H, 54, 11, 4, 5) & (yy <= 11)
    shade(cv, arc, GOLD, contour=False, R=1, base=0.6, gain=1.0)
    cv.fill(arc & (xx < 54), GOLD[6])
    cv.fill(m_rect(W, H, 53, 5, 55, 5), GOLD[4])
    cv.put(54, 4, GOLD[6])
    outline(cv, skip=m_ellipse(W, H, 54, 10, 3, 4) & (yy < 11) & ~cv.solid)
    return cv


# ------------------------------------------------------------------ Skyport Wreck: broken mast
@prop("broken_mast", 56, 128, states=(("idle", 4, 4),), ground=3)
def broken_mast(state, f):
    """A snapped sky-junk mast still standing in the wreck rubble: one yard hangs askew across it, the
    batten sail below torn to strips that stir in the wind off the Starsea, rigging lines trailing."""
    W, H = 56, 128
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 125
    ground_shadow(cv, 28, gy, 26, 2.0)
    ph = 2 * math.pi * (f % 4) / 4
    # a stay from the masthead to the ground on the right (behind everything)
    cv.fill(m_line(W, H, [(30, 16), (53, gy - 6)]), ROPE[2])
    # the mast: a tall round spar leaning a little, snapped off at the top along a ragged slant
    mast = tube(W, H, [(27, gy - 4), (28, 60), (29.5, 8)], 3.3, 2.7)
    keep = mast & (yy >= 15 + (xx - 26) * -0.9 + ((xx * 7) % 3 - 1))
    shade(cv, keep, WOOD, contour=True, mode="cyl", base=0.5, gain=1.2)
    brk = keep & ~shift(keep, 0, 1)
    cv.fill(brk | (shift(brk, 0, 1) & keep & (xx < 29)), WOOD[5])
    for (sx, sy0, sy1) in ((31, 6, 11), (30, 9, 12), (27, 12, 16), (32, 10, 12)):
        sp = m_rect(W, H, sx, sy0, sx, sy1)
        cv.fill(sp, WOOD[5] if sx < 31 else WOOD[4])
        cv.put(sx, sy1, WOOD[2])
    for by in (48, 86, 104):
        band = keep & (yy >= by) & (yy <= by + 1)
        cv.fill(band, IRON[3])
        cv.fill(band & (yy == by) & (xx < 28), IRON[5])
    # the yard, hanging askew and lashed where it crosses the mast
    ya, yb = (5.0, 32.0), (52.0, 25.0)

    def yard_y(x):
        return ya[1] + (x - ya[0]) * (yb[1] - ya[1]) / (yb[0] - ya[0])

    # the sail: a header band under the yard, torn below into flat ragged strips that sway
    strips = ((6, 14, 60, 0.0, (2, -3, 1)), (15, 22, 47, 1.2, (-2, 2, 0)), (23, 30, 76, 2.3, (1, -2, 3)),
              (31, 37, 55, 3.1, (-3, 1, -1)), (38, 45, 68, 4.4, (2, 0, -3)), (46, 51, 41, 5.3, (-1, 2, 0)))
    header = m_poly(W, H, [(6, yard_y(6) + 1), (51, yard_y(51) + 1), (51, yard_y(51) + 7), (6, yard_y(6) + 7)])
    shade(cv, header, SAIL_OLD, contour=True, R=1, base=0.55, gain=0.9)
    for i, (x0, x1, bot, p, rag) in enumerate(strips):
        top = yard_y((x0 + x1) / 2) + 6
        L = bot - top
        sway = math.sin(ph + p) * 1.7
        pts_l, pts_r = [], []
        for k in range(0, int(L) + 1, 2):
            t = k / L
            dx = sway * t * t
            pts_l.append((x0 + dx + 0.6 * t, top + k))
            pts_r.append((x1 + dx - 0.9 * t, top + k))
        w = x1 - x0
        cut = [(x1 + sway - 0.9, bot + rag[2]), (x0 + w * 0.66 + sway, bot + rag[1]), (x0 + w * 0.33 + sway, bot + 2),
               (x0 + sway + 0.6, bot + rag[0])]
        strip = m_poly(W, H, pts_l + [cut[3], cut[2], cut[1], cut[0]] + list(reversed(pts_r)))
        rel = (xx - (x0 + sway * np.clip((yy - top) / L, 0, 1) ** 2)) / max(1, w)
        shade(cv, strip, SAIL_OLD, contour=True, mode="flat", base=0.6 - 0.05 * (i % 2), gain=0.0,
              bias=-(rel - 0.3) * 0.28)
        cv.fill(left_edge(strip) & (yy > top + 1), SAIL_OLD[4])
        for by in range(int(top) + 5, int(bot) - 3, 9):
            cv.fill(strip & (yy == by), WOOD[2])
    cv.fill(m_line(W, H, [(6, yard_y(6) + 7), (51, yard_y(51) + 7)]) & header, SAIL_OLD[2])
    yard = tube(W, H, [ya, yb], 1.4)
    shade(cv, yard, WOOD, contour=True, R=1, base=0.55, gain=1.2)
    for ex in (ya, yb):
        cv.fill(m_ellipse(W, H, ex[0], ex[1], 1.4, 1.4), IRON[3])
    lash = dilate(yard) & dilate(keep) & (np.abs(xx - 28.5) < 3)
    cv.fill(lash, ROPE[2])
    cv.fill(lash & ((xx - yy) % 3 == 0), ROPE[4])
    # rigging: a loose line swinging from the yard's low end, another trailing to the rubble
    sw = math.sin(ph) * 1.5
    cv.fill(m_curve(W, H, [(5, 33), (3 + sw * 0.5, 55), (4 + sw, 76), (6 + sw, 84)]), ROPE[3])
    cv.fill(m_curve(W, H, [(51, 27), (53, 50), (52 + sw * 0.4, 70), (50, 88)]), ROPE[2])
    # the rubble it stands in
    _rubble(cv, 28, gy, 25, 12, "mast", n=7, shards=3)
    rope_coil = ellipse_ring(W, H, 12, gy - 3, 4, 1.6) | ellipse_ring(W, H, 12, gy - 4, 3, 1.2)
    cv.fill(rope_coil, ROPE[3])
    cv.fill(rope_coil & (xx < 12) & (yy < gy - 3), ROPE[5])
    outline(cv)
    return cv


# ------------------------------------------------------------------ Cloudgate Skydock: the player's cloud skiff
@prop("cloud_skiff", 128, 72, states=(("idle", 4, 4),), ground=5)
def cloud_skiff(state, f):
    """The player's own small sky-vessel, moored at the Cloudgate Skydock: a low jade-banded hull with
    a painted eye, a woven-mat canopy over the stern, one batten sail, a long steering oar, a ward
    lantern hung from a crook at the bow, and a cushion of Qi mist under the keel."""
    W, H = 128, 72
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    bob = (0, -1, -1, 0)[f % 4]
    gy = 66
    # mooring post at the bow and its line
    ground_shadow(cv, 121, gy, 5, 1.2)
    plank_v(cv, 119, 53, 122, gy, WOOD, grain=False, seed="skiff_post")
    cv.fill(m_rect(W, H, 118, 52, 123, 53), IRON[3])
    cv.fill(m_curve(W, H, [(120, 54), (116, 51 + bob), (111, 46 + bob)]), ROPE[3])
    # the Qi cushion under the keel
    for i, (cx, rx) in enumerate(((48, 16), (70, 19), (92, 14))):
        dx = ((f + i) % 4) - 1.5
        lobe = m_ellipse(W, H, cx + dx, 56, rx, 4) & ~m_ellipse(W, H, cx + dx, 61, rx - 4, 2.5)
        cv.fill(lobe, QI_MIST[2], 0.55)
        cv.fill(lobe & (yy <= 54), QI_MIST[3], 0.6)
    y0 = 39 + bob
    # the steering oar, run out over the stern (drawn before the hull so the loom tucks behind it)
    oar = tube(W, H, [(26, y0 - 4), (15, y0 + 6), (9, y0 + 12)], 1.0)
    shade(cv, oar, WOOD, contour=True, R=1, base=0.55, gain=1.0)
    blade = m_poly(W, H, [(11, y0 + 9), (5, y0 + 12), (3, y0 + 17), (7, y0 + 16), (11, y0 + 12)])
    shade(cv, blade, WOOD, contour=True, R=1, base=0.5, gain=1.0)
    cv.fill(m_line(W, H, [(26, y0 - 4), (29, y0 - 7)]), WOOD[4])
    # hull
    top, bot = [], []
    for x in range(18, 119):
        t = (x - 18) / 100.0
        ty = y0 - 5 * max(0.0, (0.18 - t) / 0.18) ** 1.3 - 8 * max(0.0, (t - 0.8) / 0.2) ** 1.4
        by = y0 + 11 - 6 * max(0.0, (0.16 - t) / 0.16) ** 1.3 - 10 * max(0.0, (t - 0.7) / 0.3) ** 1.5
        top.append((x, ty))
        bot.append((x, by))
    hull = m_poly(W, H, top + list(reversed(bot)))
    nz = vnoise(W, H, 4, seed_of("skiff"), 2)
    shade(cv, hull, WOOD, contour=True, R=2, base=0.45, gain=1.1, noise=nz, namp=0.2)
    for k in (5, 8):
        seam = m_poly(W, H, [(x, y + k) for x, y in top] + [(x, y + k + 0.8) for x, y in reversed(top)])
        cv.fill(seam & hull & erode(hull), WOOD[1])
    band = m_poly(W, H, [(x, y + 1.5) for x, y in top] + [(x, y + 3.8) for x, y in reversed(top)]) & hull
    shade(cv, band, ROOF, R=1, base=0.5, gain=0.8)
    cv.fill(band & ((xx % 10) == 0), GOLD[4])
    rail = m_poly(W, H, [(x, y - 1) for x, y in top] + [(x, y + 1.2) for x, y in reversed(top)])
    shade(cv, rail, WOOD, R=1, base=0.7, gain=0.8)
    cv.fill(top_edge(rail), WOOD[6])
    # the painted eye on the bow
    ex, ey = 103, int(y0 + 5)
    cv.fill(m_ellipse(W, H, ex, ey, 3, 1.6) & hull, PAPER_R[5])
    cv.fill(m_ellipse(W, H, ex + 0.5, ey, 1.1, 1.1) & hull, INK)
    cv.put(ex, ey - 1, PAPER_R[5])
    # woven-mat canopy over the stern
    can = m_ellipse(W, H, 38, y0 - 2, 12, 8) & (yy <= y0 - 2)
    shade(cv, can, THATCH, contour=True, R=2, base=0.55, gain=1.2, top=0.2)
    cv.fill(can & erode(can) & ((xx % 4) == 0), THATCH[2])
    cv.fill(can & erode(can) & (((xx + yy) % 4) == 1) & ((xx % 4) != 0), THATCH[4])
    cv.fill(m_rect(W, H, 26, y0 - 3, 50, y0 - 2), WOOD[2])
    # mast and the single batten sail
    mx, mtop = 72, 3
    plank_v(cv, mx - 1, mtop, mx + 1, int(y0), WOOD, grain=False, seed="skiff_mast")
    sx0, sx1, st, sb = 56, 90, 6, int(y0 - 4)
    sail = m_poly(W, H, [(sx0 + 3, st), (sx1 - 1, st + 2), (sx1 + 2, sb), (sx0 - 1, sb)])
    bow_f = np.clip((xx - sx0) / max(1, sx1 - sx0), 0, 1)
    shade(cv, sail, SAIL, contour=True, R=2, base=0.5, gain=1.1, bias=-(bow_f - 0.4) * 0.25)
    for by in range(st + 5, sb, 6):
        batten = m_line(W, H, [(sx0 - 1, by), ((sx0 + sx1) / 2, by + 1), (sx1 + 1, by)], 1) & sail
        cv.fill(batten, WOOD[2])
        cv.fill(shift(batten, 0, 1) & sail & ~batten, SAIL[5])
    cv.fill(m_line(W, H, [(mx, mtop), (112, int(y0 - 7))]) & ~sail, ROPE[2])
    pen = m_poly(W, H, [(mx + 1, mtop), (mx + 9 + (f % 2), mtop + 1 + (f % 2)), (mx + 1, mtop + 3)])
    cv.fill(pen, CLOTH_JADE[4])
    cv.fill(bottom_edge(pen), CLOTH_JADE[2])
    # the ward lantern on its crook at the bow
    crook = m_curve(W, H, [(113, int(y0 - 7)), (115, int(y0 - 16)), (118, int(y0 - 20)), (122, int(y0 - 20))])
    cv.fill(crook | shift(crook, 1, 0), WOOD[3])
    cv.fill(crook, WOOD[5])
    lx, ly = 122, int(y0 - 19)
    cv.fill(m_rect(W, H, lx, ly, lx, ly + 1), INK)
    body = m_poly(W, H, [(lx - 2, ly + 3), (lx + 2, ly + 3), (lx + 3, ly + 5), (lx + 2, ly + 8), (lx - 2, ly + 8),
                         (lx - 3, ly + 5)])
    cv.fill(body, JADE_R[5])
    cv.fill(m_rect(W, H, lx - 1, ly + 4, lx, ly + 6), JADE_R[6])
    cv.fill(m_rect(W, H, lx - 2, ly + 2, lx + 2, ly + 2) | m_rect(W, H, lx - 2, ly + 9, lx + 2, ly + 9), BRONZE[4])
    cv.fill(m_rect(W, H, lx + 1, ly + 3, lx + 1, ly + 8), BRONZE[2])
    tal = m_rect(W, H, lx, ly + 10, lx + 1, ly + 14)
    cv.fill(tal, STRAW[5])
    cv.fill(tal & (yy % 2 == 0) & (xx == lx), CLOTH_RED[3])
    outline(cv)
    a = (0.14, 0.18, 0.15, 0.2)[f % 4]
    glow(cv, lx, ly + 5, 7, 7, BRIGHT_JADE, steps=((1.0, a * 0.6), (0.6, a)))
    glow(cv, 70, 57, 44, 7, QI_CYAN, steps=((1.0, 0.08), (0.7, 0.07)))
    return cv


# ------------------------------------------------------------------ Skyport Wreck: the broken hull
FADED_LACQUER = ramp("#2a1516", "#462320", "#63342a", "#80493a", "#9a604b", "#b47b62")
FADED_ROOF = ramp("#141e22", "#1f3033", "#2d4544", "#3f5b56", "#577468", "#77917f")
WRECK_WOOD = ramp("#161310", "#28221c", "#3b3329", "#524737", "#6b5e49", "#877860", "#a5967a")


@prop("wreck_hull", 200, 96, ground=4)
def wreck_hull(state, f):
    """The broken hull of an ancient sky-junk lying tilted on the Starsea shore, its bow heaved up on a
    bank of rubble: planks gone amidships so the ribs show through, the stern castle crushed under
    its own roof, a crust of star-crystal grown over the keel like barnacles, and a torn batten
    sail dragged over the side."""
    W, H = 200, 96
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 91
    ground_shadow(cv, 100, gy, 96, 2.2)
    a = math.radians(-10.0)
    ox, oy = 11.0, 78.0
    P = _rot(ox, oy, a)
    ca, sa = math.cos(a), math.sin(a)
    U = (xx - ox) * ca + (yy - oy) * sa
    V = -(xx - ox) * sa + (yy - oy) * ca
    L = 180.0

    def top_v(u):
        t = np.clip(np.asarray(u, float) / L, 0, 1)
        return -12 * np.maximum(0.0, (0.2 - t) / 0.2) ** 1.2 - 9 * np.maximum(0.0, (t - 0.84) / 0.16) ** 1.4

    def bot_v(u):
        t = np.clip(np.asarray(u, float) / L, 0, 1)
        return 24 - 8 * np.maximum(0.0, (0.14 - t) / 0.14) ** 1.3 - 14 * np.maximum(0.0, (t - 0.78) / 0.22) ** 1.5

    nz = vnoise(W, H, 4, seed_of("wreck"), 2)
    nz2 = vnoise(W, H, 2, seed_of("wreck2"), 2)
    TV, BV = top_v(U), bot_v(U)
    g = rng("wreck")
    # the bank of rubble the bow has ridden up onto (behind the hull)
    _rubble(cv, 170, gy, 29, 28, "wreck_bank", n=9, shards=2)
    # a broken mast stump, leaning with the hull
    stump = tube(W, H, [P(80, -2), P(79, -36)], 2.8, 2.2)
    stump &= ~(V < -33 + ((xx * 5) % 3) + (U - 79) * 0.8)
    shade(cv, stump, WRECK_WOOD, contour=True, mode="cyl", base=0.55, gain=1.2)
    cv.fill(stump & ~shift(stump, 0, 1) & (V < -29), WRECK_WOOD[6])
    # hull
    top = [P(u, float(top_v(u))) for u in np.arange(0, L + 0.5, 1.0)]
    bot = [P(u, float(bot_v(u))) for u in np.arange(0, L + 0.5, 1.0)]
    hull = m_poly(W, H, top + list(reversed(bot))) & (yy <= gy)
    shade(cv, hull, WRECK_WOOD, contour=True, R=2, base=0.5, gain=1.1, noise=nz, namp=0.22)
    depth = V - TV
    seam = hull & erode(hull) & (np.mod(depth, 5.0) < 0.9) & (depth > 4)
    cv.fill(seam, WRECK_WOOD[1])
    k = np.floor(depth / 5.0)
    butt = hull & erode(hull) & (np.mod(U + k * 23.0, 31.0) < 0.9) & (depth > 4) & ~seam
    cv.fill(butt, WRECK_WOOD[2])
    # faded lacquer band peeling off below the gunwale, with a few gold studs left
    band = hull & (depth >= 1.5) & (depth < 4.5)
    peel = band & (nz2 > 0.62)
    shade(cv, band & ~peel, FADED_LACQUER, R=1, base=0.5, gain=0.8)
    cv.fill(band & ~peel & (np.mod(U, 12.0) < 1.0) & (nz > 0.45), GOLD[3])
    rail = hull & (depth < 1.5)
    cv.fill(rail, WRECK_WOOD[4])
    cv.fill(rail & ~shift(hull, 0, 1), WRECK_WOOD[6])
    # the breach amidships: planks torn away strake by strake, ribs and the far side showing through
    ends_l = 66 + np.array([int(g.integers(-4, 7)) for _ in range(8)])
    ends_r = 118 + np.array([int(g.integers(-7, 5)) for _ in range(8)])
    ki = np.clip(k.astype(int), 0, 7)
    breach = hull & (depth > 1.5) & (V < BV - 3) & (U > ends_l[ki]) & (U < ends_r[ki])
    breach &= ~(rail)
    inner = breach & erode(breach)
    dv = np.clip((V - TV) / np.maximum(1.0, BV - TV), 0, 1)
    _idx_fill(cv, breach, WOOD, 1.6 - dv * 1.6)
    cv.fill(breach & (np.mod(depth, 5.0) < 0.9), WOOD[0])
    for i, ru in enumerate((71, 79, 86, 95, 102, 111)):
        cu = ru - (dv * dv) * 3.0
        rib = breach & (U >= cu) & (U < cu + 2.2)
        if i in (2, 4):
            rib &= depth < (9 if i == 2 else 13) + ((xx * 3) % 2)
        cv.fill(rib, WOOD[3])
        cv.fill(rib & (U < cu + 0.9), WOOD[4])
        cv.fill(rib & (V > BV - 7), WOOD[2])
    beam = breach & (depth >= 3) & (depth < 5)
    cv.fill(beam, WOOD[2])
    cv.fill(beam & (depth < 3.9), WOOD[3])
    ragged = breach & ~inner
    cv.fill(ragged & (U < 92), WRECK_WOOD[5])
    cv.fill(ragged & (U >= 92), WRECK_WOOD[1])
    # a dangling plank end at the breach
    dang = m_poly(W, H, [P(111, 9), P(115, 9), P(113, 19), P(110, 18)])
    shade(cv, dang, WRECK_WOOD, contour=True, R=1, base=0.5, gain=1.0)
    # star-crystal crust grown over the keel and along the lower planks
    low = hull & ~breach & (V > BV - 10 - (nz - 0.5) * 8)
    _crust(cv, low, "wreck_crust", 0.8, spacing=4)
    # the faded painted eye on the bow
    ec = P(170, 3)
    cv.fill(m_ellipse(W, H, ec[0], ec[1], 3.5, 2.3) & hull, PAPER_R[3])
    cv.fill(m_ellipse(W, H, ec[0] + 0.5, ec[1], 1.4, 1.4) & hull, WRECK_WOOD[0])
    cv.fill(m_ellipse(W, H, ec[0], ec[1], 3.5, 2.3) & hull & (nz2 > 0.6), WRECK_WOOD[3])
    # the crushed stern castle: stubs of lacquered wall, and the roof snapped at the ridge and caved in
    for pts in ([P(1, -12), P(10, -10.5), P(10, -20), P(5, -22.5), P(1, -21)],
                [P(24, -8.5), P(33, -6), P(33, -13), P(28, -15), P(24, -14)]):
        wall = m_poly(W, H, pts)
        shade(cv, wall, FADED_LACQUER, contour=True, R=1, base=0.45, gain=0.8, noise=nz, namp=0.2)
    win = m_poly(W, H, [P(3, -13.5), P(8, -12.5), P(8, -17), P(3, -18)])
    cv.fill(win, INK)
    cv.fill(win & (np.mod(U, 2.5) < 1.0), FADED_LACQUER[2])
    post = tube(W, H, [P(33, -8), P(35, -26)], 1.1)
    post &= ~(V < -24 + ((xx * 3) % 2))
    shade(cv, post, FADED_LACQUER, contour=True, mode="cyl", base=0.55, gain=1.0)
    pu, pv = 17.0, -10.5
    halves = []
    for side, r in ((-1, math.radians(26)), (1, math.radians(-20))):
        body = [(0, 1.5), (0, -8.5), (side * 13, -8.5), (side * 15, -5), (side * 20.5, 0), (side * 17.5, 0.5),
                (side * 8, -0.8)]
        pts = [P(pu + x * math.cos(r) - y * math.sin(r), pv + x * math.sin(r) + y * math.cos(r)) for (x, y) in body]
        half = m_poly(W, H, pts)
        ru_ = (U - pu) * math.cos(r) + (V - pv) * math.sin(r)
        rv_ = -(U - pu) * math.sin(r) + (V - pv) * math.cos(r)
        half &= ~((np.abs(ru_) < 2.5) & (np.mod(rv_ * 1.7, 3.0) < 1.2))
        shade(cv, half, FADED_ROOF, contour=True, R=2, base=0.5 if side < 0 else 0.42, gain=1.2)
        cv.fill(half & erode(half) & (np.mod(ru_, 3.0) < 1.0), FADED_ROOF[2])
        ridge = half & (rv_ < -7.2)
        cv.fill(ridge, FADED_ROOF[4])
        cv.fill(ridge & ~shift(half, 0, 1), FADED_ROOF[5])
        holes = half & erode(erode(half)) & (nz2 > 0.78)
        cv.fill(dilate(holes) & half & erode(half), FADED_ROOF[1])
        cv.fill(holes, INK)
        halves.append(half)
    for (tu, tv) in ((40, -1.5), (47, -1.5)):
        tp = P(tu, tv)
        cv.fill(m_rect(W, H, tp[0], tp[1], tp[0] + 1, tp[1]), FADED_ROOF[3])
        cv.put(tp[0], tp[1], FADED_ROOF[5])
    # the torn batten sail dragged over the side from its fallen yard, hanging in ragged tongues
    su0, su1 = 124, 162
    hem = [(124, 12), (127, 17), (130, 13), (134, 19), (138, 14), (141, 15), (145, 21), (149, 15), (153, 17),
           (157, 13), (160, 16), (162, 11)]

    def hem_v(u):
        return float(np.interp(u, [q[0] for q in hem], [q[1] for q in hem]))

    sail_pts = [P(u, float(top_v(u)) - 2.5) for u in range(su0, su1 + 1)] + \
               [P(u, float(top_v(u)) + hem_v(u)) for u in range(su1, su0 - 1, -1)]
    sail = m_poly(W, H, sail_pts)
    fold_u = np.mod(U - su0, 7.0)
    shade(cv, sail, SAIL, contour=True, contour_c=SAIL[1], mode="flat", base=0.66, gain=0.0,
          bias=-np.clip((U - su0) / (su1 - su0), 0, 1) * 0.2 - np.clip(depth / 18.0, 0, 1) * 0.2
          + np.where(fold_u < 2.5, 0.08, 0.0) - np.where(fold_u > 5.5, 0.12, 0.0))
    cv.fill(sail & (depth < 0), SAIL[5])
    for bv in (5, 11):
        bat = sail & (np.abs(depth - bv - np.sin((U - su0) * 0.45) * 0.8) < 0.6)
        cv.fill(bat, WOOD[2])
    cv.fill(bottom_edge(sail), SAIL[1])
    yard = tube(W, H, [P(118, -3.5), P(166, -8.5), P(176, -13)], 1.4)
    shade(cv, yard, WRECK_WOOD, contour=True, R=1, base=0.6, gain=1.2)
    # shore rubble and grit drifted against the hull, burying the keel
    for (cx, rx, ry, sd) in ((22, 24, 9, "wreck_s"), (70, 22, 6, "wreck_m"), (116, 20, 7, "wreck_m2"),
                             (150, 16, 8, "wreck_b")):
        _rubble(cv, cx, gy, rx, ry, sd, n=max(3, rx // 6), shards=0)
    for (sx, h, ln) in ((8, 8, -1.5), (11, 5, 1.0), (96, 6, -1.0), (133, 8, 1.5), (136, 5, -0.5)):
        _shard(cv, sx, gy - 1, h, 3, ln)
    outline(cv)
    return cv


# ------------------------------------------------------------------ Cloudgate Skydock: shipwright's slip
NEW_WOOD = ramp("#2a1c10", "#4a3219", "#6e4d26", "#946c38", "#b88e4f", "#d6b06e", "#ecd29a")
BAMBOO_POLE = ramp("#23240f", "#3e3f19", "#5f5d27", "#827d37", "#a79f4f", "#c9c274", "#e2dca0")


@prop("shipyard_slip", 176, 96, ground=4)
def shipyard_slip(state, f):
    """The shipwright's slip at the Cloudgate Skydock: a small sky-vessel in frame on a timber slipway,
    keel laid, bare ribs up and the first strakes pinned on, with bamboo scaffolding, a mallet, a coil
    of rope and a stack of formation plates waiting by the bow."""
    W, H = 176, 96
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 91
    ground_shadow(cv, 88, gy, 86, 2.2)
    nz = vnoise(W, H, 3, seed_of("slip"), 2)

    def slip_y(x):
        return 81.0 + (x - 4) * 3.0 / 168.0

    # scaffold poles behind the hull (far side)
    for px in (62, 110):
        plank_v(cv, px, 30, px + 1, int(slip_y(px)) - 1, BAMBOO_POLE, grain=False, base=0.4)
    # slipway: a long sloping timber on trestle posts, with sleeper ends along it
    for px in (10, 40, 70, 100, 130, 160):
        top = int(slip_y(px)) + 3
        post = m_rect(W, H, px - 1, top, px + 1, gy)
        shade(cv, post, WOOD, contour=True, mode="cyl", base=0.45, gain=1.0)
        cv.fill(m_line(W, H, [(px - 6, gy), (px, top + 2)]) | m_line(W, H, [(px + 6, gy), (px, top + 2)]), WOOD[2])
    rail = m_poly(W, H, [(4, slip_y(4)), (172, slip_y(172)), (172, slip_y(172) + 3), (4, slip_y(4) + 3)])
    shade(cv, rail, WOOD, contour=True, R=1, base=0.5, gain=1.1, noise=nz, namp=0.15)
    cv.fill(top_edge(rail), WOOD[5])
    for sx in range(8, 172, 9):
        cv.fill(m_rect(W, H, sx, int(slip_y(sx)) + 1, sx + 1, int(slip_y(sx)) + 2), WOOD[1])
    # the vessel in frame: a rockered bottom rising into a raked sternpost and a tall curved stem
    k0, k1 = 30.0, 146.0

    def bot_y(x):
        t = (x - k0) / (k1 - k0)
        return slip_y(x) - 7.0 - 10.0 * max(0.0, (0.2 - t) / 0.2) ** 1.6 - 18.0 * max(0.0, (t - 0.72) / 0.28) ** 1.7

    def top_y(x):
        t = (x - k0) / (k1 - k0)
        return 50.0 - 10.0 * max(0.0, (0.22 - t) / 0.22) ** 1.3 - 13.0 * max(0.0, (t - 0.78) / 0.22) ** 1.4

    # keel blocks and the keel
    for bx in range(46, 124, 15):
        by = int(slip_y(bx)) - 1
        shade(cv, m_rect(W, H, bx - 2, by - 4, bx + 2, by), WOOD, contour=True, R=1, base=0.4, gain=1.0)
    keel = m_poly(W, H, [(40, bot_y(40) - 1), (128, bot_y(128) - 1), (128, bot_y(128) + 2), (40, bot_y(40) + 2)])
    # frames: ribs from the bottom curve up past the sheer, their heads standing proud
    frames = np.zeros((H, W), bool)
    fxs = list(range(int(k0) + 5, int(k1) - 3, 7))
    for fx in fxs:
        t = (fx - k0) / (k1 - k0)
        flare = (t - 0.5) * 5.0
        by_, ty_ = bot_y(fx), top_y(fx) - 3
        frames |= tube(W, H, [(fx, by_), (fx + flare * 0.25, by_ - (by_ - ty_) * 0.4), (fx + flare, ty_)], 0.9)
    shade(cv, frames, NEW_WOOD, contour=True, R=1, base=0.5, gain=1.2)
    cv.fill(left_edge(frames), NEW_WOOD[5])
    stern = tube(W, H, [(k0 + 8, bot_y(k0 + 8)), (k0 + 1, bot_y(k0 + 1) - 2), (k0 - 5, top_y(k0) - 6)], 1.7, 1.3)
    stem = tube(W, H, [(k1 - 10, bot_y(k1 - 10)), (k1 - 3, bot_y(k1 - 3) - 3), (k1 + 2, top_y(k1) - 2),
                       (k1 + 3, top_y(k1) - 10)], 1.9, 1.4)
    for part in (keel, stern, stem):
        shade(cv, part, NEW_WOOD, contour=True, R=1, base=0.55, gain=1.2)
    cv.fill(left_edge(stern) | left_edge(stem), NEW_WOOD[5])
    # bent ribbands holding the frames fair: the sheer and one lower down
    for frac, c in ((0.0, NEW_WOOD[5]), (0.45, NEW_WOOD[4])):
        pts = [(x, top_y(x) + (bot_y(x) - top_y(x)) * frac) for x in np.arange(k0 - 3, k1 + 2.5, 2.0)]
        rb = m_line(W, H, pts)
        cv.fill(shift(rb, 0, 1) & ~rb, NEW_WOOD[1])
        cv.fill(rb, c)
    # the first strakes pinned on low along the bottom, each plank ending at its own frame
    g = rng("slip_strakes")
    for s_ in range(3):
        x0 = fxs[1 + s_ + int(g.integers(0, 2))]
        x1 = fxs[-2 - s_ * 2 - int(g.integers(0, 2))]
        up = [(x, bot_y(x) - 1.5 - s_ * 3.2) for x in np.arange(x0, x1 + 0.5, 1.0)]
        dn = [(x, bot_y(x) + 0.8 - s_ * 3.2) for x in np.arange(x1, x0 - 0.5, -1.0)]
        pl = m_poly(W, H, up + dn)
        shade(cv, pl, NEW_WOOD, contour=True, R=1, base=0.62 - s_ * 0.05, gain=1.0)
        cv.fill(top_edge(pl), NEW_WOOD[6])
        for fx in fxs:
            if x0 < fx < x1:
                cv.put(fx, int(round(bot_y(fx) - 0.5 - s_ * 3.2)), NEW_WOOD[1])
    # bamboo scaffolding in front: two poles, a ledger with a plank walk, lashings
    for px in (20, 156):
        plank_v(cv, px, 24, px + 1, gy, BAMBOO_POLE, grain=False, base=0.6)
        for ny in range(30, gy, 9):
            cv.put(px + 1, ny, BAMBOO_POLE[1])
    walk = m_rect(W, H, 12, 55, 44, 57)
    shade(cv, walk, WOOD, contour=True, R=1, base=0.55, gain=1.0)
    cv.fill(m_rect(W, H, 12, 55, 44, 55), WOOD[5])
    plank_v(cv, 42, 55, 43, int(slip_y(42)) - 1, BAMBOO_POLE, grain=False, base=0.5)
    cv.fill(m_line(W, H, [(140, 42), (157, 42)]), BAMBOO_POLE[4])
    for (lx, ly) in ((20, 55), (156, 42), (42, 55)):
        lash = m_rect(W, H, lx - 1, ly - 1, lx + 2, ly + 1)
        cv.fill(lash, ROPE[2])
        cv.fill(lash & ((xx - yy) % 3 == 0), ROPE[4])
    # spare planks stacked under the walk, a big wooden mallet lying in front, a coil of rope
    for k in range(3):
        pl = m_rect(W, H, 26 + k, gy - 1 - k * 2, 52 - k * 2, gy - k * 2)
        shade(cv, pl, NEW_WOOD, contour=True, R=1, base=0.55 - k * 0.03, gain=1.0)
        cv.fill(top_edge(pl), NEW_WOOD[5])
    handle = m_line(W, H, [(72, gy - 1), (85, gy - 4)])
    cv.fill(shift(handle, 0, 1) & ~handle, WOOD[2])
    cv.fill(handle, WOOD[5])
    head = m_poly(W, H, [(84, gy - 8), (90, gy - 8), (91, gy), (85, gy)])
    shade(cv, head, WOOD, contour=True, R=1, base=0.62, gain=1.1)
    cv.fill(m_rect(W, H, 84, gy - 6, 90, gy - 6) | m_rect(W, H, 85, gy - 2, 91, gy - 2), IRON[4])
    coil = (ellipse_ring(W, H, 9, gy - 2, 5, 1.8) | ellipse_ring(W, H, 9, gy - 3, 3.6, 1.3)
            | ellipse_ring(W, H, 9, gy - 4, 2.4, 0.9))
    cv.fill(coil, ROPE[3])
    cv.fill(coil & (xx < 9) & (yy <= gy - 3), ROPE[5])
    cv.fill(m_line(W, H, [(14, gy - 2), (18, gy - 1), (23, gy)]), ROPE[3])
    # formation plates stacked by the bow, the top one engraved with a ring of array lines
    for k in range(3):
        y0 = gy - k * 2
        x0 = 156 + (k % 2)
        pl = m_rect(W, H, x0, y0 - 1, x0 + 13, y0)
        cv.fill(pl, BRONZE[3] if k % 2 else BRONZE[2])
        cv.fill(top_edge(pl), BRONZE[5] if k % 2 else BRONZE[4])
    top_pl = m_poly(W, H, [(158, gy - 9), (168, gy - 9), (170, gy - 6), (156, gy - 6)])
    shade(cv, top_pl, BRONZE, contour=True, R=1, base=0.55, gain=0.8)
    cv.fill(ellipse_ring(W, H, 163, gy - 7.5, 4, 1.2) & top_pl, JADE_R[4])
    cv.put(163, gy - 8, JADE_R[6])
    leaning = m_poly(W, H, [(171, gy), (174, gy), (171, gy - 13), (168.5, gy - 12)])
    shade(cv, leaning, BRONZE, contour=True, R=1, base=0.5, gain=1.0)
    cv.fill(m_line(W, H, [(171, gy - 3), (170, gy - 9)]), JADE_R[4])
    outline(cv)
    glow(cv, 163, gy - 7.5, 6, 3, BRIGHT_JADE, steps=((1.0, 0.1),))
    return cv


# ------------------------------------------------------------------ Starsea Launch cradle
@prop("launch_ring", 112, 128, states=(("idle", 1, 0), ("active", 4, 4)), ground=4)
def launch_ring(state, f):
    """The Starsea Launch: two tall arms of stone and bronze cradle a great open bronze ring tipped
    back to face the sky, rune lamps set all round it. Wakened, the lamps burn white and the ring
    fills with a slow swirl of star light."""
    W, H = 112, 128
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 123
    on = state == "active"
    cx, cy, rx, ry = 55.5, 56.0, 43.0, 30.4
    ground_shadow(cv, cx, gy, 54, 2.2)
    nz = vnoise(W, H, 3, seed_of("launch"), 2)

    def stone(m, base=0.55, gain=1.1, R=2):
        shade(cv, m, STONE, contour=True, R=R, strength=2.0, base=base, gain=gain, noise=nz, namp=0.07)
        return m

    # the dais: two broad steps with a rune circle inlaid in the upper one
    for (x0, x1, y0, y1) in ((2, 109, 117, gy), (14, 97, 110, 116)):
        stone(m_rect(W, H, x0, y0, x1, y1), base=0.5, R=1)
        cv.fill(m_rect(W, H, x0, y0, x1, y0), STONE[5])
        cv.fill(m_rect(W, H, x0, y0, x0, y1), STONE[4])
        for jx in range(x0 + 12, x1 - 4, 14):
            cv.fill(m_rect(W, H, jx, y0 + 1, jx, y1), STONE[2])
    inlay = ellipse_ring(W, H, cx, 113, 22, 2)
    cv.fill(inlay & (yy >= 111), STARLIGHT[3] if on else STONE[2])
    # the arms: stone pedestals, bronze claws rising past the pivots
    for s in (-1, 1):
        px = cx + s * (rx + 4)
        ped = m_poly(W, H, [(px - 9, 110), (px + 9, 110), (px + 7, 86), (px + 5, 80), (px - 5, 80), (px - 7, 86)])
        stone(ped, base=0.6 if s < 0 else 0.45)
        cv.fill(m_rect(W, H, px - 7, 86, px + 7, 87), STONE[2])
        cv.fill(m_rect(W, H, px - 5, 80, px + 5, 80), STONE[5])
        g_ = rng("launch_ped", s)
        for gy2 in (90, 97):
            rows = _PILLAR_GLYPHS[int(g_.integers(0, len(_PILLAR_GLYPHS)))]
            for r_, row in enumerate(rows):
                for c_, ch in enumerate(row):
                    if ch == "#":
                        cv.put(int(px) - 1 + c_, gy2 + r_, STARLIGHT[5] if on else STONE[2])
        arm = tube(W, H, [(px, 81), (px + s * 3, 70), (px + s * 1.5, cy), (px - s * 2, 38), (px - s * 7, 26),
                          (px - s * 10, 22)], 4.0, 1.8)
        shade(cv, arm, BRONZE, contour=True, R=2, base=0.58 if s < 0 else 0.42, gain=1.2)
        cv.fill(left_edge(arm) & (yy > 30), BRONZE[5] if s < 0 else BRONZE[3])
        for by in (72, 44):
            band = arm & (np.abs(yy - by) <= 0.6)
            cv.fill(band, GOLD[4])
        tip = m_ellipse(W, H, px - s * 10.5, 21.5, 1.8, 1.8)
        shade(cv, tip, GOLD, contour=True, mode="sphere", base=0.6, gain=1.0)
    # the ring, tipped back: outer and inner rims, the far half showing its inner face,
    # the near half showing its outer face
    outer = m_ellipse(W, H, cx, cy, rx, ry)
    inner = m_ellipse(W, H, cx, cy, rx - 7, ry - 6)
    band = outer & ~inner
    ap = inner & m_ellipse(W, H, cx, cy + 4, rx - 7, ry - 6)
    inner_face = inner & ~ap
    outer_face = m_ellipse(W, H, cx, cy + 4, rx, ry) & ~outer & (yy > cy)
    if on:
        # the swirl of star light in the opening, turning slowly
        dxn = (xx - cx) / (rx - 7)
        dyn = (yy - cy - 2) / (ry - 6)
        r = np.sqrt(dxn * dxn + dyn * dyn)
        th = np.arctan2(dyn, dxn)
        phase = f / 4.0 * (2 * math.pi / 3)
        spiral = np.mod((th - phase) * 3 / (2 * math.pi) + r * 1.6, 1.0)
        _idx_fill(cv, ap, STARLIGHT, 1.0 + (1 - r) * 0.8)
        arms_ = ap & (spiral < 0.36) & (r > 0.12)
        cv.fill(arms_, STARLIGHT[3])
        cv.fill(arms_ & (spiral < 0.18) & (r > 0.2), STARLIGHT[4])
        cv.fill(arms_ & (spiral < 0.07) & (r > 0.35), STARLIGHT[5])
        cv.fill(ap & (r < 0.14), STARLIGHT[5])
        cv.fill(ap & (r < 0.07), WHITE_HOT)
        # stars drawn in along the arms toward the heart, each looping back out to the rim
        g_ = rng("launch_stars")
        for i in range(18):
            a0, off = g_.uniform(0, 2 * math.pi), g_.uniform(0, 1)
            t = (off + f / 4.0) % 1.0
            r0 = 0.95 - 0.7 * t
            a1 = a0 + t * (2 * math.pi / 3)
            sx_, sy_ = int(round(cx + math.cos(a1) * r0 * (rx - 7))), int(round(cy + 2 + math.sin(a1) * r0 * (ry - 6)))
            if 0 <= sx_ < W and 0 <= sy_ < H and ap[sy_, sx_]:
                cv.put(sx_, sy_, STARLIGHT[6] if i % 3 else WHITE_HOT)
    shade(cv, outer_face, BRONZE, contour=True, R=1, base=0.4, gain=1.0)
    cv.fill(outer_face & ~shift(outer_face, 0, 1), BRONZE[1])
    shade(cv, inner_face, BRONZE, R=1, base=0.28, gain=0.8)
    shade(cv, band, BRONZE, contour=False, mode="sphere", base=0.6, gain=1.3, noise=nz, namp=0.1)
    cv.fill(ellipse_ring(W, H, cx, cy, rx, ry) & (xx + yy * 1.4 < cx + cy * 1.4 - 10), GOLD[5])
    cv.fill(ellipse_ring(W, H, cx, cy, rx - 7, ry - 6) & (yy > cy + 4), BRONZE[5])
    mid = ellipse_ring(W, H, cx, cy, rx - 3.5, ry - 3)
    cv.fill(mid & band & ((xx + yy) % 5 == 0), BRONZE[2])
    # rune lamps round the ring, chasing each other when the ring wakes
    lamps = []
    for k in range(14):
        a = 2 * math.pi * k / 14 - math.pi / 2
        lx, ly = cx + math.cos(a) * (rx - 3.5), cy + math.sin(a) * (ry - 3)
        lamps.append((int(round(lx)), int(round(ly))))
        hous = m_rect(W, H, round(lx) - 1, round(ly) - 1, round(lx) + 1, round(ly) + 1)
        cv.fill(hous, BRONZE[1])
        if on:
            hot = (k - f * 3.5) % 14 < 3.5
            core = m_rect(W, H, round(lx) - 1, round(ly) - 1, round(lx), round(ly))
            cv.fill(core, STARLIGHT[6] if hot else STARLIGHT[5])
            if hot:
                cv.put(round(lx) - 1, round(ly) - 1, WHITE_HOT)
        else:
            cv.fill(m_rect(W, H, round(lx) - 1, round(ly) - 1, round(lx), round(ly)), STARLIGHT[2])
            cv.put(round(lx) - 1, round(ly) - 1, STARLIGHT[3])
    # pivot bosses where the arms take the ring
    for s in (-1, 1):
        hx = cx + s * (rx + 1)
        boss = m_ellipse(W, H, hx, cy, 4.2, 4.2)
        shade(cv, boss, GOLD, contour=True, mode="sphere", base=0.55, gain=1.1)
        cv.fill(m_ellipse(W, H, hx, cy, 1.4, 1.4), BRONZE[1])
    hole = ap & ~cv.solid
    outline(cv, skip=hole)
    if on:
        a = (0.1, 0.13, 0.11, 0.14)[f % 4]
        glow(cv, cx, cy + 2, rx - 4, ry - 3, STARLIGHT[5], steps=((1.0, a * 0.6), (0.7, a), (0.4, a)))
        for (lx, ly) in lamps:
            cv.light(m_ellipse(W, H, lx - 0.5, ly - 0.5, 2.5, 2.5) & ~cv.solid, STARLIGHT[5], 0.25)
        motes(cv, 20, 4, 92, 60, f, 4, "launch_m", count=10, pal=(STARLIGHT[5], WHITE_HOT))
    return cv
