"""Breakables, containers, crafting stations and training equipment."""
from __future__ import annotations

import math

import numpy as np

from palette import *  # noqa: F401,F403
from parts import (blob_mask, flame, grass_tuft, ground_shadow, lantern, lathe, moss_top, motes, plank_h, plank_v,
                   post, rock, rope_band, roof_side, smoke, soil_mound, sparks, vessel, wisp)
from pixlib import (Canvas, bbox, border, bottom_edge, dilate, erode, glow, grid, hexc, left_edge, m_curve,
                    m_ellipse, m_line, m_poly, m_rect, mix, outline, right_edge, rng, seed_of, shade, shift, sparkle,
                    top_edge, vnoise)
from registry import prop
from defs_structures import stone_block


def shards(cv, spots, pal, seed):
    g = rng("shards", seed)
    for i, (x, y) in enumerate(spots):
        wdt = int(g.integers(2, 4))
        hgt = int(g.integers(1, 3))
        pts = [(x, y), (x + wdt, y), (x + wdt - 1, y - hgt), (x + int(g.integers(0, 2)), y - hgt - 1)]
        m = m_poly(cv.w, cv.h, pts)
        cv.fill(m, pal[3 if i % 2 else 4])
        cv.fill(bottom_edge(m), pal[1])
        cv.put(x + 1, y - hgt, pal[-1])


# ------------------------------------------------------------------ jars & crates
@prop("jar", 16, 20, states=(("intact", 1, 0), ("broken", 1, 0)))
def jar(state, f):
    W, H = 16, 20
    cv = Canvas(W, H)
    ground_shadow(cv, 8, 18, 7, 1.3)
    prof = [(3, 3.5), (4, 3.5), (5, 3), (6, 5), (8, 6.8), (10, 7), (13, 6), (15, 4.8), (17, 3.8)]
    if state == "intact":
        m = vessel(cv, 7.5, prof, POTTERY, base=0.55)
        xx, yy = grid(W, H)
        # dark glaze on the shoulder with drips
        glz = m & ((yy <= 9) | ((yy <= 11) & (xx % 3 == 1)) | ((yy <= 12) & (xx == 5)))
        idx = np.where(yy <= 7, 3, 2)
        cv.fill_idx(glz, idx, GLAZE_AMBER)
        cv.fill(glz & (xx <= 5) & (yy <= 8), GLAZE_AMBER[4])
        cv.fill(glz & (xx == 4) & (yy == 7), GLAZE_AMBER[5])
        cv.fill(m & (yy == 13) & (xx % 2 == 0), POTTERY[2])
        # cloth cover tied with cord
        cloth = m_poly(W, H, [(3, 4), (12, 4), (13, 6), (11, 5), (8, 6), (5, 5), (2, 6)]) | m_ellipse(W, H, 7.5, 3, 4, 1.8)
        shade(cv, cloth, PAPER_R, R=1, base=0.5, gain=1.2)
        rope_band(cv, 4, 11, 5)
        cv.put(12, 6, ROPE[3])
        cv.put(12, 7, ROPE[2])
    else:
        prof2 = [(11, 6.6), (14, 6.2), (16, 5), (17, 4)]
        m = vessel(cv, 7.5, prof2, POTTERY, base=0.5)
        xx, yy = grid(W, H)
        jag = m & (yy <= 12) & ((xx * 7 + 3) % 5 < 2)
        cv.erase(jag)
        cv.fill(top_edge(cv.solid & m) , POTTERY[1])
        cv.fill(m_ellipse(W, H, 7.5, 11.5, 4.5, 1) & cv.solid, POTTERY[0])
        shards(cv, [(0, 17), (12, 17), (13, 15)], POTTERY, "jar")
        cv.fill(m_rect(W, H, 3, 17, 12, 17) & ~cv.solid, STRAW[3])
    outline(cv)
    return cv


@prop("wine_jar", 18, 22, states=(("intact", 1, 0), ("broken", 1, 0)))
def wine_jar(state, f):
    W, H = 18, 22
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ground_shadow(cv, 9, 20, 8, 1.3)
    prof = [(4, 3.5), (5, 3.5), (6, 4.5), (8, 6.5), (11, 7.6), (14, 7.6), (17, 6.2), (19, 4.5)]
    if state == "intact":
        m = vessel(cv, 9, prof, GLAZE_DARK, base=0.55, gain=1.3)
        # red cloth cap
        cap = m_ellipse(W, H, 9, 4, 5.5, 2.4) | m_poly(W, H, [(3, 4), (15, 4), (15, 7), (13, 6), (9, 7), (5, 6), (3, 7)])
        shade(cv, cap, CLOTH_RED, R=1, base=0.55, gain=1.2)
        rope_band(cv, 5, 13, 6)
        # red paper label (diamond) with brush mark
        lab = m_poly(W, H, [(9, 9), (13, 13), (9, 17), (5, 13)])
        cv.fill(lab, CLOTH_RED[4])
        cv.fill(border(lab), CLOTH_RED[2])
        cv.fill(m_rect(W, H, 8, 12, 10, 12) | m_rect(W, H, 9, 11, 9, 15) | m_rect(W, H, 8, 14, 10, 14), INK)
        cv.put(6, 12, CLOTH_RED[5])
    else:
        prof2 = [(13, 7.4), (14, 7.6), (17, 6.2), (19, 4.5)]
        m = vessel(cv, 9, prof2, GLAZE_DARK, base=0.5)
        jag = m & (yy <= 14) & ((xx * 5 + 1) % 4 < 2)
        cv.erase(jag)
        cv.fill(m_ellipse(W, H, 9, 14, 5.5, 1) & cv.solid, WINE[1])
        # wine puddle
        pud = m_ellipse(W, H, 9, 19.5, 9, 1.6) & ~cv.solid
        cv.fill(pud, WINE[2])
        cv.fill(pud & (yy == 19) & (xx % 4 == 1), WINE[3])
        shards(cv, [(0, 19), (14, 18), (2, 17)], GLAZE_DARK, "wj")
        cv.fill(m_poly(W, H, [(13, 16), (16, 15), (15, 17)]), CLOTH_RED[4])
    outline(cv)
    return cv


@prop("crate", 22, 20, states=(("intact", 1, 0), ("broken", 1, 0)))
def crate(state, f):
    W, H = 22, 20
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ground_shadow(cv, 11, 18, 11, 1.3)
    if state == "intact":
        # body planks
        for i, y0 in enumerate((3, 8, 13)):
            plank_h(cv, 2, y0, 19, y0 + 4, WOOD, seed=("cr", i), base=0.5 - 0.04 * i)
        # frame
        for (x0, x1) in ((1, 3), (18, 20)):
            plank_v(cv, x0, 2, x1, 17, WOOD, seed=("crf", x0), base=0.62, grain=False)
        plank_h(cv, 1, 2, 20, 3, WOOD, seed="crt", base=0.65, grain=False)
        plank_h(cv, 1, 16, 20, 17, WOOD, seed="crb", base=0.45, grain=False)
        # diagonal brace
        br = m_line(W, H, [(4, 15), (17, 4)], 1) | m_line(W, H, [(4, 14), (16, 4)])
        cv.fill(br, WOOD[4])
        cv.fill(m_line(W, H, [(5, 15), (17, 5)]) & ~br, WOOD[1])
        # nails
        for (nx, ny) in ((2, 3), (19, 3), (2, 16), (19, 16)):
            cv.put(nx, ny, IRON[5])
    else:
        planks = [((1, 15), (12, 17), (12, 15), (1, 13)), ((8, 17), (20, 14), (21, 16), (9, 18)),
                  ((3, 12), (10, 8), (11, 10), (4, 14)), ((12, 11), (19, 11), (19, 13), (12, 13))]
        for i, pts in enumerate(planks):
            pm = m_poly(W, H, list(pts))
            shade(cv, pm, WOOD, contour=True, R=1, base=0.5 + 0.05 * (i % 2))
        cv.fill(m_poly(W, H, [(14, 10), (15, 7), (16, 10)]), WOOD[5])
        cv.put(6, 11, IRON[5])
        cv.put(17, 12, IRON[5])
        cv.fill(m_rect(W, H, 3, 17, 7, 17) & ~cv.solid, STRAW[3])
    outline(cv)
    return cv


# ------------------------------------------------------------------ chests
def chest_body(cv, x0, x1, y0, y1, pal, trim, seed):
    body = m_rect(cv.w, cv.h, x0, y0, x1, y1)
    shade(cv, body, pal, contour=True, R=1, base=0.5, gain=1.2)
    return body


@prop("chest", 26, 20, states=(("closed", 1, 0), ("open", 1, 0)))
def chest(state, f):
    W, H = 26, 20
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ground_shadow(cv, 13, 18, 12, 1.3)
    body = m_rect(W, H, 2, 9, 23, 17)
    shade(cv, body, LACQUER, contour=True, R=1, base=0.5, gain=1.1)
    cv.fill(m_rect(W, H, 3, 16, 22, 16), LACQUER[1])
    if state == "closed":
        lid = m_rect(W, H, 2, 4, 23, 9) & ~m_rect(W, H, 2, 4, 2, 4) & ~m_rect(W, H, 23, 4, 23, 4)
        shade(cv, lid, LACQUER, contour=True, R=1, base=0.6, gain=1.2, top=0.3)
        cv.fill(m_rect(W, H, 2, 9, 23, 9), GOLD[2])
        cv.fill(m_rect(W, H, 3, 5, 22, 5), LACQUER[5])
    else:
        # lid swung back: dark underside visible
        lid = m_rect(W, H, 3, 0, 22, 5)
        shade(cv, lid, LACQUER, contour=True, R=1, base=0.3, gain=0.8)
        cv.fill(m_rect(W, H, 4, 1, 21, 4), LACQUER[1])
        inside = m_rect(W, H, 3, 6, 22, 9)
        cv.fill(inside, INK)
        cv.fill(m_rect(W, H, 4, 8, 21, 9), GOLD[3])
        for (cx, cy) in ((6, 7), (9, 8), (13, 7), (17, 8), (20, 7), (11, 7)):
            cv.put(cx, cy, GOLD[5])
            cv.put(cx + 1, cy, GOLD[4])
        cv.fill(m_rect(W, H, 2, 9, 23, 9), GOLD[2])
    # gold corner fittings & lock
    for (cx0, cx1) in ((2, 4), (21, 23)):
        cv.fill(m_rect(W, H, cx0, 10, cx1, 11) | m_rect(W, H, cx0, 15, cx1, 17), GOLD[3])
        cv.put(cx0, 10, GOLD[5])
    cv.fill(m_rect(W, H, 11, 9, 14, 13), GOLD[3])
    cv.fill(m_rect(W, H, 11, 9, 14, 9), GOLD[5])
    cv.fill(m_rect(W, H, 12, 11, 13, 12), GOLD[1])
    cv.fill(m_rect(W, H, 3, 12, 22, 12) & ~m_rect(W, H, 11, 9, 14, 13), GOLD[2])
    outline(cv)
    if state == "open":
        glow(cv, 13, 7, 9, 4, PALE_GOLD, steps=((1.0, 0.18), (0.6, 0.22)))
        sparkle(cv, 16, 4, 1, WHITE_HOT, PALE_GOLD)
    return cv


@prop("storage_chest", 30, 22)
def storage_chest(state, f):
    W, H = 30, 22
    cv = Canvas(W, H)
    ground_shadow(cv, 15, 20, 14, 1.3)
    for i, y0 in enumerate((8, 13)):
        plank_h(cv, 2, y0, 27, y0 + 4, WOOD, seed=("sc", i), base=0.48)
    lid = m_rect(W, H, 1, 3, 28, 8) & ~m_rect(W, H, 1, 3, 1, 3) & ~m_rect(W, H, 28, 3, 28, 3)
    shade(cv, lid, WOOD, contour=True, R=1, base=0.6, gain=1.2, top=0.3)
    cv.fill(m_rect(W, H, 2, 4, 27, 4), WOOD[5])
    plank_h(cv, 2, 17, 27, 19, WOOD, seed="scb", base=0.4, grain=False)
    # bronze bands
    for bx in (5, 14, 23):
        band = m_rect(W, H, bx, 3, bx + 2, 19)
        shade(cv, band, BRONZE, contour=True, mode="cyl", base=0.55)
        for ry in (5, 10, 15, 18):
            cv.put(bx + 1, ry, BRONZE[6])
    # lock plate + handles
    cv.fill(m_rect(W, H, 13, 7, 17, 11), BRONZE[4])
    cv.fill(m_rect(W, H, 14, 9, 16, 10), INK)
    cv.put(13, 7, BRONZE[6])
    for hx in (1, 28):
        cv.fill(m_rect(W, H, hx, 11, hx, 13), IRON[4])
    outline(cv)
    return cv


# ------------------------------------------------------------------ crafting stations
@prop("cooking_pot", 28, 26, states=(("idle", 1, 0), ("steam", 4, 6)))
def cooking_pot(state, f):
    W, H = 28, 26
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    on = state == "steam"
    ground_shadow(cv, 14, 24, 13, 1.4)
    # hearth stones
    for i, (x, rx, ry) in enumerate(((5, 4, 3), (23, 4, 3.2), (14, 3.5, 2))):
        rock(cv, x, 23, rx, ry, ("cp_st", i), pal=STONE, R=1, facets=1, base=0.5)
    # firewood
    for pts in (((7, 22), (20, 20)), ((8, 20), (21, 22))):
        lm = m_line(W, H, list(pts), 2)
        shade(cv, lm, WOOD, R=1, base=0.45)
    if on:
        flame(cv, 11, 20, 5, f, width=4)
        flame(cv, 16, 20, 6, (f + 2) % 4, width=4)
        flame(cv, 14, 21, 4, (f + 1) % 4, width=3)
    else:
        for (ex, ey) in ((12, 20), (15, 21), (17, 20)):
            cv.put(ex, ey, FIRE[1])
    # iron pot
    prof = [(7, 9.5), (8, 10.5), (10, 11), (13, 10.5), (15, 9), (17, 6.5), (18, 4)]
    pot = vessel(cv, 14, prof, IRON, base=0.55, gain=1.3)
    cv.fill(m_rect(W, H, 3, 7, 24, 8), IRON[4])
    cv.fill(m_rect(W, H, 3, 7, 24, 7), IRON[6])
    # handles
    for hx in (2, 25):
        cv.fill(m_rect(W, H, hx, 9, hx, 11), IRON[3])
    # soup surface
    cv.fill(m_rect(W, H, 5, 6, 22, 6), hexc("#8a6a3a") if on else hexc("#5a4a30"))
    cv.fill(m_rect(W, H, 8, 6, 12, 6), hexc("#c09a58") if on else hexc("#6d5a3a"))
    outline(cv)
    if on:
        glow(cv, 14, 21, 9, 4, FIRE[3], steps=((1.0, 0.15), (0.6, 0.2)))
        smoke(cv, 10, 5, f, 4, height=10, seed=1, pal=SMOKE, count=3, size=1.8, alpha=0.7, drift=1.5)
        smoke(cv, 18, 5, (f + 2) % 4, 4, height=10, seed=2, pal=SMOKE, count=3, size=1.8, alpha=0.7, drift=1.5)
    return cv


@prop("alchemy_furnace", 32, 40, states=(("idle", 1, 0), ("lit", 4, 6)))
def alchemy_furnace(state, f):
    W, H = 32, 40
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    on = state == "lit"
    ground_shadow(cv, 16, 38, 15, 1.5)
    # three legs
    for lx in (7, 15, 23):
        leg = m_poly(W, H, [(lx, 30), (lx + 3, 30), (lx + 2 + (1 if lx > 16 else 0), 37), (lx + (0 if lx > 16 else -1), 37)])
        shade(cv, leg, BRONZE, contour=True, mode="cyl", base=0.5)
        cv.fill(m_rect(W, H, lx - 1, 36, lx + 3, 37) & ~m_rect(W, H, lx, 36, lx + 2, 36), BRONZE[3])
    # belly
    prof = [(14, 9), (16, 12), (20, 13.5), (25, 13.5), (29, 11.5), (31, 8)]
    belly = vessel(cv, 16, prof, BRONZE, base=0.55, gain=1.3)
    # patina patches
    pat = belly & (vnoise(W, H, 2, 77, 2) > 0.7) & erode(belly) & (yy > 21)
    cv.fill(pat, PATINA[3])
    cv.fill(pat & ~shift(pat, 0, 1), PATINA[4])
    # decorative band + taotie mask
    cv.fill(belly & (yy == 18), BRONZE[2])
    cv.fill(belly & (yy == 19) & (xx % 3 == 0), BRONZE[6])
    # fire window
    win = m_ellipse(W, H, 16, 25, 4, 3)
    if on:
        cv.fill(win, FIRE[2])
        cv.fill(m_ellipse(W, H, 16, 26, 2.5, 1.8), FIRE[4])
        cv.fill(m_rect(W, H, 15, 26, 17, 26), FIRE[5])
        cv.fill(win & ((xx % 2) == 0) & (yy < 27), BRONZE[1])
    else:
        cv.fill(win, BRONZE[0])
        cv.fill(win & ((xx % 2) == 0), BRONZE[1])
        cv.put(15, 27, FIRE[1])
    # neck + lid
    neck = m_rect(W, H, 9, 11, 22, 14)
    shade(cv, neck, BRONZE, contour=True, mode="cyl", base=0.45)
    lid = lathe(W, H, 16, [(5, 3), (7, 7), (9, 10), (10, 11)])
    shade(cv, lid, BRONZE, contour=True, mode="cyl", base=0.6, gain=1.2, top=0.2)
    knob = m_ellipse(W, H, 16, 3.5, 2, 1.8)
    shade(cv, knob, GOLD, mode="sphere", base=0.55)
    # ears (handles)
    for ex, sgn in ((4, -1), (27, 1)):
        ear = m_rect(W, H, min(ex, ex + sgn * 2), 9, max(ex, ex + sgn * 2), 15) & ~m_rect(W, H, min(ex, ex + sgn * 2) + 1 - (sgn < 0), 11, max(ex, ex + sgn * 2) - (sgn > 0) , 13)
        shade(cv, ear, BRONZE, contour=True, R=1, base=0.55)
    outline(cv)
    if on:
        glow(cv, 16, 26, 10, 7, FIRE[3], steps=((1.0, 0.14), (0.6, 0.2)))
        smoke(cv, 16, 1, f, 4, height=8, seed=3, pal=(JADE_R[2], JADE_R[3], JADE_R[4], JADE_R[5], JADE_R[6]),
              count=2, size=1.2, alpha=0.7)
        motes(cv, 9, 0, 23, 9, f, 4, "furn", count=4, pal=(BRIGHT_JADE, PALE_GOLD))
    return cv


@prop("forge_anvil", 40, 32, states=(("idle", 1, 0), ("sparks", 4, 8)))
def forge_anvil(state, f):
    W, H = 40, 32
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    on = state == "sparks"
    ground_shadow(cv, 20, 30, 18, 1.5)
    # wooden stump
    stump = lathe(W, H, 20, [(19, 8), (27, 8.5), (29, 10)])
    shade(cv, stump, WOOD, contour=True, mode="cyl", base=0.5)
    cv.fill(m_rect(W, H, 12, 19, 27, 19), WOOD[5])
    for gx in (15, 19, 23):
        cv.fill(stump & (xx == gx) & (yy > 20) & (yy < 28), WOOD[2])
    # anvil
    anv = m_poly(W, H, [(5, 10), (10, 9), (31, 9), (35, 10), (31, 12), (27, 13), (25, 16), (27, 18), (13, 18),
                        (15, 16), (13, 13), (9, 12)])
    shade(cv, anv, IRON, contour=True, R=2, base=0.5, gain=1.4, top=0.3)
    cv.fill(m_rect(W, H, 10, 9, 31, 9), IRON[6])
    cv.fill(m_rect(W, H, 11, 10, 30, 10), IRON[5])
    # hot ingot on top
    ing = m_rect(W, H, 17, 7, 22, 8)
    cv.fill(ing, FIRE[3] if on else FIRE[1])
    cv.fill(m_rect(W, H, 17, 7, 22, 7), FIRE[4] if on else FIRE[2])
    # hammer leaning on stump
    cv.fill(m_line(W, H, [(31, 28), (35, 19)]), WOOD[4])
    hh = m_poly(W, H, [(32, 17), (37, 19), (36, 21), (31, 19)])
    shade(cv, hh, IRON, contour=True, R=1, base=0.5)
    # tongs
    cv.fill(m_line(W, H, [(4, 28), (9, 20)]) | m_line(W, H, [(6, 28), (9, 21)]), IRON[3])
    outline(cv)
    if on:
        glow(cv, 20, 8, 7, 4, FIRE[3], steps=((1.0, 0.18), (0.6, 0.25)))
        sparks(cv, 20, 6, f, 4, "anvil", count=10, spread=11)
        if f == 0:
            sparkle(cv, 20, 6, 2, WHITE_HOT, FIRE[4])
    return cv


@prop("incense_burner", 20, 24, states=(("idle", 2, 4),))
def incense_burner(state, f):
    W, H = 20, 24
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ground_shadow(cv, 10, 22, 8, 1.3)
    for lx in (5, 13):
        cv.fill(m_rect(W, H, lx, 18, lx + 1, 21), BRONZE[3])
        cv.put(lx + (0 if lx < 10 else 1), 21, BRONZE[5])
    body = lathe(W, H, 10, [(11, 5), (12, 7), (15, 7.5), (18, 6), (19, 4)])
    shade(cv, body, BRONZE, contour=True, mode="cyl", base=0.55, gain=1.3)
    pat = body & (vnoise(W, H, 2, 12) > 0.72) & (yy > 14)
    cv.fill(pat, PATINA[3])
    cv.fill(body & (yy == 14) & (xx % 2 == 1), BRONZE[6])
    lid = lathe(W, H, 10, [(6, 1.5), (8, 3.5), (10, 5.5), (11, 6)])
    shade(cv, lid, BRONZE, contour=True, mode="cyl", base=0.6, top=0.2)
    cv.fill(lid & (yy == 9) & (xx % 2 == 0), INK)
    knob = m_ellipse(W, H, 10, 5, 1.3, 1.3)
    shade(cv, knob, GOLD, mode="sphere")
    for ex in (3, 16):
        cv.fill(m_rect(W, H, ex, 12, ex + 1, 14) & ~m_rect(W, H, ex + (1 if ex < 10 else 0), 13, ex + (1 if ex < 10 else 0), 13), BRONZE[3])
    outline(cv)
    wisp(cv, 10, 3, f, 2, height=4, seed=0.5, alpha=0.7, amp=0.8)
    smoke(cv, 10, 2, f, 2, height=3, seed=4, count=1, size=1.1, alpha=0.5)
    wisp(cv, 8, 9, f, 2, height=3, seed=2.0, alpha=0.5, amp=0.6)
    return cv


@prop("small_bell", 12, 16, states=(("idle", 1, 0), ("ringing", 2, 8)))
def small_bell(state, f):
    W, H = 12, 16
    cv = Canvas(W, H)
    ground_shadow(cv, 6, 14, 6, 1.2)
    # wooden frame
    for px in (0, 11):
        cv.fill(m_rect(W, H, px, 3, px, 13), WOOD[3])
    cv.fill(m_rect(W, H, 0, 3, 0, 13), WOOD[4])
    cv.fill(m_rect(W, H, 0, 1, 11, 2), LACQUER[3])
    cv.fill(m_rect(W, H, 0, 1, 11, 1), LACQUER[5])
    cv.fill(m_rect(W, H, 0, 0, 1, 0) | m_rect(W, H, 10, 0, 11, 0), LACQUER[4])
    sw = 0 if state == "idle" else (-1 if f == 0 else 1)
    cv.put(6, 3, ROPE[3])
    bell = lathe(W, H, 6 + sw, [(4, 1.2), (5, 2.2), (8, 2.6), (9, 3.2), (10, 3.5)])
    shade(cv, bell, BRONZE, contour=True, mode="cyl", base=0.6, gain=1.3)
    cv.fill(m_rect(W, H, 3 + sw, 7, 8 + sw, 7) & bell, BRONZE[6])
    cv.put(6 + sw, 11, BRONZE[1])
    outline(cv)
    if state == "ringing":
        for (x, y) in (((0, 6), (0, 8)) if f == 0 else ((11, 6), (11, 8))):
            cv.put(x, y, PALE_GOLD, 0.9)
    return cv


# ------------------------------------------------------------------ training
@prop("training_stump", 20, 36, states=(("idle", 1, 0), ("hit", 1, 0)))
def training_stump(state, f):
    W, H = 20, 36
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    hit = state == "hit"
    ground_shadow(cv, 10, 34, 9, 1.4)
    soil_mound(cv, 10, 33, 8, 2, "ts_soil", moss=0.3)
    top = 4
    lean = 2 if hit else 0
    body = m_poly(W, H, [(6, 32), (14, 32), (13 + lean, top + 2), (12 + lean, top), (7 + lean, top), (6 + lean, top + 2)])
    nz = vnoise(W, H, 2, 21, 2)
    shade(cv, body, WOOD, contour=True, mode="cyl", base=0.5, gain=1.1, noise=nz, namp=0.25)
    for gx in (8, 11):
        cv.fill(body & (xx == gx + (lean if False else 0)) & (yy > top + 3) & (yy < 30) & (nz > 0.45), WOOD[2])
    # top cut face
    cv.fill(m_rect(W, H, 7 + lean, top, 12 + lean, top), WOOD[5])
    cv.fill(m_rect(W, H, 8 + lean, top + 1, 11 + lean, top + 1), WOOD[4])
    # rope wraps
    for ry in (10, 12, 22, 24):
        rope_band(cv, 6 + (lean if ry < 20 else 0), 13 + (lean if ry < 20 else 0), ry)
    # worn strike patch
    cv.fill(m_rect(W, H, 8, 16, 11, 18), WOOD[3])
    cv.fill(m_rect(W, H, 9, 17, 10, 17), WOOD[5])
    outline(cv)
    if hit:
        imp = m_poly(W, H, [(3, 17), (6, 15), (5, 17), (8, 18), (5, 19), (6, 21), (3, 19), (1, 20), (2, 18), (0, 16)])
        cv.fill(imp, PALE_GOLD, 0.9)
        cv.fill(m_ellipse(W, H, 3.5, 17.5, 1.2, 1.0), WHITE_HOT)
        for (x, y) in ((2, 12), (1, 23), (4, 25), (16, 14)):
            cv.put(x, y, WOOD[5])
            cv.put(x + 1, y + 1, WOOD[3])
        cv.fill(m_line(W, H, [(15, 15), (18, 13)]), PALE_GOLD, 0.8)
        cv.fill(m_line(W, H, [(15, 18), (19, 18)]), PALE_GOLD, 0.8)
    return cv


@prop("lifting_stone", 28, 20)
def lifting_stone(state, f):
    W, H = 28, 20
    cv = Canvas(W, H)
    ground_shadow(cv, 14, 18, 13, 1.4)
    body = m_rect(W, H, 3, 8, 24, 17)
    for (x, y) in ((3, 8), (24, 8), (3, 17), (24, 17)):
        body[y, x] = False
    nz = vnoise(W, H, 3, 31, 2)
    shade(cv, body, STONE, contour=True, R=3, strength=2.4, base=0.55, gain=1.5, noise=nz, namp=0.3)
    handle = m_rect(W, H, 7, 2, 20, 8) & ~m_rect(W, H, 10, 5, 17, 8)
    handle[2, 7] = handle[2, 20] = False
    shade(cv, handle, STONE, contour=True, R=2, base=0.6, gain=1.4, noise=nz, namp=0.3)
    cv.fill(m_rect(W, H, 10, 5, 17, 7), hexc("#000000"), 0.0)
    # carved band + worn grip
    cv.fill(m_rect(W, H, 5, 12, 22, 12), STONE[2])
    cv.fill(m_rect(W, H, 5, 13, 22, 13), STONE[5])
    cv.fill(m_rect(W, H, 11, 2, 16, 2), STONE[6])
    moss_top(cv, body, "ls_moss", 0.25, thick=1)
    outline(cv)
    return cv


@prop("training_dummy", 24, 44, states=(("idle", 1, 0), ("hit", 1, 0)))
def training_dummy(state, f):
    W, H = 24, 44
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    hit = state == "hit"
    ground_shadow(cv, 12, 42, 9, 1.4)
    soil_mound(cv, 12, 41, 7, 2, "td_soil")
    L = 4 if hit else 0  # lean (px at top)

    def lx(y):  # x offset for lean, 0 at base
        return round(L * (40 - y) / 36)
    # post
    postm = np.zeros((H, W), bool)
    for y in range(4, 41):
        postm[y, 11 + lx(y):13 + lx(y)] = True
    shade(cv, postm, WOOD, contour=True, mode="cyl", base=0.5)
    # arms
    arm = m_rect(W, H, 3 + lx(15), 14, 20 + lx(15), 15)
    shade(cv, arm, WOOD, contour=True, R=1, base=0.55)
    # straw body
    body = np.zeros((H, W), bool)
    for y in range(13, 31):
        hw = 5 if 15 <= y <= 27 else 4
        c = 12 + lx(y)
        body[y, c - hw:c + hw] = True
    nz = vnoise(W, H, 2, 41, 1)
    shade(cv, body, STRAW, contour=True, mode="cyl", base=0.55, gain=1.1, noise=nz, namp=0.3)
    cv.fill(body & ((xx + yy // 3) % 3 == 0) & erode(body), STRAW[3])
    for ry in (16, 23, 29):
        rope_band(cv, 7 + lx(ry), 16 + lx(ry), ry)
    # straw tufts at arms ends
    for ex in (3, 20):
        cv.fill(m_rect(W, H, ex + lx(15) - (1 if ex < 10 else 0), 13, ex + lx(15) + (0 if ex < 10 else 1), 16), STRAW[4])
    # sack head
    head = m_ellipse(W, H, 12 + lx(8), 8, 4.2, 4.5)
    shade(cv, head, PAPER_R, contour=True, mode="sphere", base=0.45, gain=1.2)
    cv.fill(m_rect(W, H, 9 + lx(8), 11, 15 + lx(8), 11), ROPE[2])
    # stitched seam on the sack head, painted target on the chest
    cv.fill(m_rect(W, H, 12 + lx(8), 5, 12 + lx(8), 9), PAPER_R[2])
    tgt = m_ellipse(W, H, 12 + lx(21), 20.5, 2.6, 2.6)
    cv.fill(tgt, CLOTH_RED[3])
    cv.fill(m_ellipse(W, H, 12 + lx(21), 20.5, 1.3, 1.3), PAPER_R[4])
    cv.put(12 + lx(21), 20, CLOTH_RED[4])
    outline(cv)
    if hit:
        for (x, y) in ((2, 20), (4, 25), (1, 16), (6, 13), (3, 28)):
            cv.fill(m_line(W, H, [(x, y), (x + 1, y - 1)]), STRAW[5])
        imp = m_poly(W, H, [(6, 21), (9, 19), (8, 21), (11, 22), (8, 23), (9, 25), (6, 23), (4, 24), (5, 22), (3, 20)])
        cv.fill(imp, PALE_GOLD, 0.9)
        cv.fill(m_ellipse(W, H, 6.5, 21.5, 1.2, 1.0), WHITE_HOT)
    return cv


@prop("weapon_rack", 48, 48)
def weapon_rack(state, f):
    W, H = 48, 48
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ground_shadow(cv, 24, 46, 22, 1.5)
    # frame: end posts, top rail with notches, base beam
    for px in (3, 42):
        plank_v(cv, px, 9, px + 2, 44, LACQUER, seed=("wr", px))
        cv.fill(m_rect(W, H, px - 1, 7, px + 3, 8), GOLD[3])
        cv.fill(m_rect(W, H, px - 1, 7, px + 3, 7), GOLD[5])
    plank_h(cv, 3, 12, 44, 14, LACQUER, seed="wrt", base=0.55, grain=False)
    plank_h(cv, 2, 41, 45, 44, WOOD, seed="wrb", base=0.45)
    # spear: 2px shaft, leaf blade, red tassel
    sp = m_rect(W, H, 10, 7, 11, 41)
    shade(cv, sp, WOOD, mode="cyl", base=0.55)
    blade = m_poly(W, H, [(10.5, 0), (13, 4), (11.5, 7), (9.5, 7), (8, 4)])
    shade(cv, blade, IRON, R=1, base=0.6, gain=1.3)
    cv.fill(m_line(W, H, [(10, 1), (10, 6)]), IRON[6])
    tas = m_poly(W, H, [(9, 7), (13, 7), (14, 11), (12, 10), (10, 11), (8, 10)])
    shade(cv, tas, CLOTH_RED, R=1, base=0.55)
    # staff with bronze caps
    st = m_rect(W, H, 17, 3, 18, 41)
    shade(cv, st, WOOD, mode="cyl", base=0.6)
    cv.fill(m_rect(W, H, 17, 3, 18, 5) | m_rect(W, H, 17, 37, 18, 40), BRONZE[5])
    cv.put(17, 3, BRONZE[6])
    # jian in scabbard: guard, hilt, pommel, tassel
    sh = m_rect(W, H, 25, 11, 26, 40)
    shade(cv, sh, LACQUER, mode="cyl", base=0.35)
    cv.fill(m_rect(W, H, 25, 20, 26, 21) | m_rect(W, H, 25, 34, 26, 35), GOLD[3])
    cv.fill(m_rect(W, H, 23, 9, 28, 10), GOLD[4])
    cv.fill(m_rect(W, H, 23, 9, 28, 9), GOLD[5])
    hilt = m_rect(W, H, 25, 3, 26, 8)
    cv.fill(hilt, CLOTH_JADE[3])
    cv.fill(hilt & (yy % 2 == 0), CLOTH_JADE[1])
    cv.fill(m_rect(W, H, 24, 1, 27, 2), GOLD[4])
    cv.fill(m_curve(W, H, [(27, 2), (29, 5), (29, 9)]), CLOTH_RED[4])
    cv.put(29, 10, CLOTH_RED[2])
    # bow (recurve) with string
    bow = m_curve(W, H, [(33, 4), (34, 6), (37, 12), (38, 24), (37, 36), (34, 42), (33, 44)])
    bow2 = shift(bow, 1, 0) & m_rect(W, H, 35, 9, 40, 39)
    cv.fill(bow | bow2, WOOD[3])
    cv.fill(bow & ~bow2, WOOD[5])
    cv.fill(m_rect(W, H, 37, 22, 39, 26), CLOTH_RED[3])
    cv.fill(m_line(W, H, [(33, 5), (33, 43)]), PAPER_R[3])
    # front rail pieces over the weapons (rests)
    for sx in (10, 17, 25, 36):
        cv.fill(m_rect(W, H, sx - 1, 12, sx + 2, 12), LACQUER[5])
    outline(cv)
    return cv


@prop("meditation_mat", 32, 8, ground=1)
def meditation_mat(state, f):
    W, H = 32, 8
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    mat = m_ellipse(W, H, 16, 4.5, 15, 2.8)
    shade(cv, mat, STRAW, R=2, base=0.5, gain=1.0)
    for r in (12, 8):
        ring = m_ellipse(W, H, 16, 4.5, r, r * 0.19) & ~m_ellipse(W, H, 16, 4.5, r - 1, max(0.4, r * 0.19 - 0.8))
        cv.fill(ring & mat, STRAW[2])
    cush = m_ellipse(W, H, 16, 3.5, 7, 2)
    shade(cv, cush, CLOTH_JADE, R=1, base=0.55, gain=1.2)
    cv.fill(m_rect(W, H, 15, 3, 16, 3), GOLD[4])
    outline(cv, t=0.6)
    return cv


@prop("formation_node", 16, 24, states=(("idle", 1, 0), ("active", 3, 6)))
def formation_node(state, f):
    W, H = 16, 24
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    on = state == "active"
    ground_shadow(cv, 8, 22, 7, 1.3)
    stone_block(cv, 3, 17, 12, 21, "fn_base", moss=0.3)
    ped = m_rect(W, H, 5, 12, 10, 16)
    shade(cv, ped, STONE, contour=True, R=1, base=0.55)
    cv.fill(m_rect(W, H, 6, 14, 9, 14), JADE_R[3] if on else STONE[2])
    cv.fill(m_rect(W, H, 4, 11, 11, 12), STONE[5])
    cv.fill(m_rect(W, H, 4, 12, 11, 12), STONE[3])
    bob = [0, -1, 0][f % 3] if on else 0
    cr = m_poly(W, H, [(8, 2 + bob), (11, 6 + bob), (8, 10 + bob), (5, 6 + bob)])
    shade(cv, cr, JADE_R, contour=True, R=1, base=0.5 + (0.2 if on else 0), gain=1.4)
    cv.fill(m_line(W, H, [(8, 3 + bob), (8, 9 + bob)]) & cr, JADE_R[5] if on else JADE_R[4])
    outline(cv)
    if on:
        glow(cv, 8, 6 + bob, 6 + f, 6 + f, BRIGHT_JADE, steps=((1.0, 0.1), (0.6, 0.18)))
        ring = m_ellipse(W, H, 8, 18, 7, 2) & ~m_ellipse(W, H, 8, 18, 6, 1.2)
        cv.fill(ring & (xx % 3 == f % 3), BRIGHT_JADE, 0.8)
        sparkle(cv, [5, 11, 8][f], [4, 7, 1][f], 1, WHITE_HOT, BRIGHT_JADE)
    return cv


@prop("fishing_net_rack", 48, 40)
def fishing_net_rack(state, f):
    W, H = 48, 40
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ground_shadow(cv, 24, 38, 22, 1.4)
    # A-frame poles
    for (a, b) in (((4, 37), (9, 4)), ((13, 37), (8, 4)), ((35, 37), (40, 4)), ((44, 37), (39, 4))):
        lm = m_line(W, H, [a, b], 2)
        shade(cv, lm, WOOD_GREY, contour=True, R=1, base=0.5)
    plank_h(cv, 5, 5, 43, 6, WOOD_GREY, grain=False, base=0.6)
    # net draped
    net = m_poly(W, H, [(9, 7), (40, 7), (38, 22), (32, 30), (24, 27), (16, 31), (10, 22)])
    mesh = net & (((xx + yy) % 3 == 0) | ((xx - yy) % 3 == 0))
    cv.fill(mesh, ROPE[2])
    cv.fill(mesh & (yy < 14), ROPE[4])
    cv.fill(border(net) & (yy > 8), ROPE[1])
    # floats
    for (fx, fy) in ((12, 23), (20, 28), (29, 28), (36, 22)):
        fl = m_ellipse(W, H, fx, fy, 1.6, 1.3)
        shade(cv, fl, CLOTH_RED, mode="sphere", base=0.55)
    # drying fish
    for i, fx in enumerate((17, 25, 32)):
        cv.fill(m_rect(W, H, fx, 7, fx, 9), ROPE[3])
        fish = m_poly(W, H, [(fx - 1, 10), (fx + 1, 10), (fx + 2, 14), (fx, 17), (fx - 2, 14)])
        shade(cv, fish, CLOTH_WHITE, contour=True, R=1, base=0.45)
        cv.fill(m_poly(W, H, [(fx - 1, 17), (fx + 1, 17), (fx, 18)]), CLOTH_WHITE[2])
        cv.put(fx, 11, INK)
    # basket at base
    bas = lathe(W, H, 24, [(32, 6), (34, 6.5), (37, 5.5)])
    shade(cv, bas, STRAW, contour=True, mode="cyl", base=0.5)
    cv.fill(bas & (xx % 2 == 0) & (yy > 32), STRAW[2])
    outline(cv)
    return cv


@prop("well", 32, 40)
def well(state, f):
    W, H = 32, 40
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ground_shadow(cv, 16, 38, 15, 1.5)
    # posts (behind well lip)
    for px in (5, 25):
        plank_v(cv, px, 10, px + 1, 30, WOOD, seed=("wp", px))
    # crank beam + rope + bucket
    plank_h(cv, 4, 14, 27, 15, WOOD, grain=False, base=0.55)
    cv.fill(m_rect(W, H, 26, 13, 28, 16), WOOD[2])
    cv.fill(m_rect(W, H, 28, 15, 29, 15), IRON[4])
    cv.fill(m_rect(W, H, 12, 14, 18, 15) & True, ROPE[3])
    cv.fill(m_rect(W, H, 15, 16, 15, 21), ROPE[2])
    buck = lathe(W, H, 15.5, [(21, 3), (25, 2.5)])
    shade(cv, buck, WOOD, contour=True, mode="cyl", base=0.5)
    cv.fill(m_rect(W, H, 13, 22, 17, 22), IRON[4])
    # roof
    roof_side(cv, 2, 29, 4, 10, "well_roof", curl=2, finials=False, top_frac=0.25)
    # stone well drum
    drum = lathe(W, H, 16, [(24, 13), (37, 13)])
    stone_block(cv, 3, 25, 28, 37, "well_drum", course=4, joint=6, moss=0.35)
    cv.fill(m_rect(W, H, 3, 24, 28, 25), STONE[5])
    cv.fill(m_rect(W, H, 4, 25, 27, 25), STONE[3])
    cv.fill(m_ellipse(W, H, 16, 25, 11, 0.6), INK)
    grass_tuft(cv, 2, 37, "wg1", h=4, n=3)
    grass_tuft(cv, 29, 37, "wg2", h=5, n=3)
    outline(cv)
    return cv


@prop("notice_board", 40, 44)
def notice_board(state, f):
    W, H = 40, 44
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ground_shadow(cv, 20, 42, 18, 1.4)
    for px in (4, 33):
        plank_v(cv, px, 8, px + 2, 41, LACQUER, seed=("nb", px), mode="cyl")
        stone_block(cv, px - 1, 38, px + 3, 41, ("nbf", px))
    board = m_rect(W, H, 7, 12, 32, 33)
    shade(cv, board, WOOD, contour=True, R=1, base=0.45, gain=0.8)
    for gy in (17, 22, 27):
        cv.fill(board & (yy == gy) & erode(board), WOOD[2])
    plank_h(cv, 6, 11, 33, 12, LACQUER, grain=False, base=0.6)
    plank_h(cv, 6, 33, 33, 34, LACQUER, grain=False, base=0.45)
    # notices
    papers = [(9, 14, 16, 22, 0), (18, 13, 24, 20, 1), (26, 15, 31, 24, 2), (11, 24, 18, 31, 3), (20, 22, 25, 31, 4)]
    for (x0, y0, x1, y1, i) in papers:
        pm = m_rect(W, H, x0, y0, x1, y1)
        cv.fill(pm, PAPER_R[4] if i % 2 == 0 else PAPER_R[3])
        cv.fill(right_edge(pm) | bottom_edge(pm), PAPER_R[2])
        for ly in range(y0 + 2, y1 - 1, 2):
            cv.fill(m_rect(W, H, x0 + 1, ly, x1 - 2 - (ly % 3 == 0), ly), PAPER_R[1])
        cv.put((x0 + x1) // 2, y0, CLOTH_RED[4])
    cv.fill(m_rect(W, H, 26, 15, 31, 16), CLOTH_RED[3])
    roof_side(cv, 1, 38, 3, 8, "nb_roof", curl=2, finials=True, top_frac=0.35)
    outline(cv)
    return cv


@prop("signpost", 20, 36)
def signpost(state, f):
    W, H = 20, 36
    cv = Canvas(W, H)
    ground_shadow(cv, 10, 34, 6, 1.3)
    soil_mound(cv, 10, 33, 5, 1.5, "sp_soil", moss=0.3)
    plank_v(cv, 9, 3, 10, 32, WOOD, seed="sp")
    cv.fill(m_rect(W, H, 8, 2, 11, 3), ROOF[3])
    cv.fill(m_rect(W, H, 8, 2, 11, 2), ROOF[5])
    a1 = m_poly(W, H, [(1, 7), (15, 7), (18, 9.5), (15, 12), (1, 12)])
    shade(cv, a1, WOOD, contour=True, R=1, base=0.6, gain=1.0)
    a2 = m_poly(W, H, [(19, 15), (5, 15), (2, 17.5), (5, 20), (19, 20)])
    shade(cv, a2, WOOD, contour=True, R=1, base=0.5, gain=1.0)
    # brush strokes (illegible)
    for (x0, x1, y) in ((4, 7, 9), (9, 12, 10), (8, 10, 17), (12, 16, 18)):
        cv.fill(m_rect(W, H, x0, y, x1, y), WOOD[1])
    cv.put(10, 9, IRON[5])
    cv.put(10, 17, IRON[5])
    grass_tuft(cv, 6, 33, "spg", h=4, n=3)
    outline(cv)
    return cv


@prop("teleport_stone", 24, 48, states=(("inactive", 1, 0), ("active", 4, 6)))
def teleport_stone(state, f):
    W, H = 24, 48
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    on = state == "active"
    ground_shadow(cv, 12, 46, 11, 1.5)
    stone_block(cv, 2, 40, 21, 45, "tp_base", moss=0.35, joint=7)
    st = m_poly(W, H, [(5, 40), (19, 40), (18, 8), (16, 4), (12, 2), (8, 4), (6, 8)])
    nz = vnoise(W, H, 3, 51, 2)
    shade(cv, st, STONE, contour=True, R=3, strength=2.2, base=0.55, gain=1.4, noise=nz, namp=0.3)
    # jade inlay: ring rune + vertical channel
    ring = m_ellipse(W, H, 11.5, 14, 4.5, 4.5) & ~m_ellipse(W, H, 11.5, 14, 3.2, 3.2)
    bars = (m_rect(W, H, 8, 22, 15, 23) | m_rect(W, H, 8, 26, 10, 27) | m_rect(W, H, 13, 26, 15, 27)
            | m_rect(W, H, 8, 30, 15, 31) | m_rect(W, H, 9, 35, 14, 35))
    rune = ring | bars | m_rect(W, H, 11, 13, 12, 14)
    if on:
        c = [JADE_R[4], JADE_R[5], JADE_R[6], JADE_R[5]][f]
        cv.fill(rune, c)
        cv.fill(shift(rune, 1, 1) & st & ~rune, JADE_R[2])
    else:
        cv.fill(rune, JADE_R[1])
        cv.fill(shift(rune, 1, 1) & st & ~rune, STONE[5])
    moss_top(cv, st, "tp_moss", 0.3, thick=1)
    grass_tuft(cv, 2, 45, "tpg", h=4, n=3)
    grass_tuft(cv, 21, 45, "tpg2", h=3, n=2)
    outline(cv)
    if on:
        glow(cv, 12, 20, 11 + (f % 2), 20, BRIGHT_JADE, steps=((1.0, 0.07), (0.7, 0.1), (0.4, 0.12)))
        motes(cv, 3, 0, 21, 40, f, 4, "tp_m", count=8)
    return cv
