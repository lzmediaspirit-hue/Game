"""Shrines, stones, gates, posts and other built structures."""
from __future__ import annotations

import math

import numpy as np

from palette import *  # noqa: F401,F403
from parts import (blob_mask, flame, fern, grass_tuft, ground_shadow, lantern, lathe, moss_top, motes, plank_h, plank_v,
                   post, rock, roof_side, smoke, wisp)
from pixlib import (Canvas, border, bottom_edge, dilate, erode, glow, grid, left_edge, m_ellipse, m_line, m_poly,
                    m_rect, mix, outline, right_edge, rng, seed_of, shade, shift, sparkle, top_edge, vnoise)
from registry import prop


def stone_block(cv, x0, y0, x1, y1, seed, pal=STONE, moss=0.0, base=0.52, course=0, joint=0, chip=True):
    """Dressed stone block (optionally with masonry courses/joints and chipped corners)."""
    m = m_rect(cv.w, cv.h, x0, y0, x1, y1)
    if chip:
        for (cx, cy) in ((x0, y0), (x1, y0)):
            m[cy, cx] = False
    nz = vnoise(cv.w, cv.h, 3, seed_of("blk", seed), 2)
    shade(cv, m, pal, contour=True, R=2, strength=2.2, base=base, gain=1.4, noise=nz, namp=0.35)
    xx, yy = grid(cv.w, cv.h)
    inner = erode(m)
    if course:
        for cy in range(y0 + course, y1, course):
            cv.fill(inner & (yy == cy), pal[1])
            cv.fill(inner & (yy == cy + 1) & (nz > 0.45), pal[4])
    if joint:
        g = rng("joint", seed)
        rows = list(range(y0, y1 + 1, course)) if course else [y0]
        for ri, ry in enumerate(rows):
            ry1 = min(y1, ry + (course or (y1 - y0 + 1)) - 1)
            off = int(g.integers(0, joint))
            for jx in range(x0 + off + (joint // 2 if ri % 2 else 0), x1, joint):
                if x0 + 2 <= jx <= x1 - 2:
                    cv.fill(inner & (xx == jx) & (yy >= ry + 1) & (yy <= ry1), pal[1])
                    cv.fill(inner & (xx == jx + 1) & (yy >= ry + 1) & (yy <= ry1) & (nz > 0.5), pal[4])
    # top highlight edge
    cv.fill(top_edge(m) & ~left_edge(m) & (nz > 0.3), pal[min(len(pal) - 1, 5)])
    if moss:
        moss_top(cv, m, seed, moss, thick=1)
    return m


# ------------------------------------------------------------------ shrine
@prop("shrine", 40, 56, states=(("idle", 1, 0), ("active", 4, 6)))
def shrine(state, f):
    cv = Canvas(40, 56)
    W, H = 40, 56
    active = state == "active"
    ground_shadow(cv, 20, 54, 18, 1.6)
    # plinth
    stone_block(cv, 4, 47, 35, 53, "shr1", moss=0.4, joint=9)
    stone_block(cv, 8, 42, 31, 46, "shr2", moss=0.3, joint=8)
    # back wall + alcove
    back = m_rect(W, H, 12, 22, 27, 41)
    shade(cv, back, LACQUER, contour=True, R=1, base=0.25, gain=0.6)
    alc = m_rect(W, H, 14, 25, 25, 40)
    cv.fill(alc, hexc("#1c0c0f") if not active else hexc("#4a1e14"))
    cv.fill(m_rect(W, H, 14, 25, 25, 26), hexc("#12070a") if not active else hexc("#34140f"))
    if active:
        glow(cv, 19.5, 36, 10, 11, hexc("#ffb85a"), steps=((1.0, 0.16), (0.75, 0.2), (0.5, 0.26), (0.3, 0.3)),
             m_limit=alc)
    # tablet / statue
    tab = m_rect(W, H, 17, 29, 22, 38) | m_rect(W, H, 18, 28, 21, 28)
    shade(cv, tab, JADE_R, contour=True, R=1, base=0.42 + (0.18 if active else 0), gain=1.2)
    cv.fill(m_rect(W, H, 19, 31, 20, 31) | m_rect(W, H, 19, 33, 20, 33) | m_rect(W, H, 19, 35, 20, 35),
            JADE_R[1] if not active else GOLD[5])
    ped = m_rect(W, H, 16, 38, 23, 40)
    shade(cv, ped, BRONZE, contour=True, R=1, base=0.55)
    # posts
    post(cv, 10, 21, 12, 41, LACQUER)
    post(cv, 27, 21, 29, 41, LACQUER)
    cv.fill(m_rect(W, H, 10, 39, 12, 41), GOLD[2])
    cv.fill(m_rect(W, H, 27, 39, 29, 41), GOLD[2])
    # lintel + gold trim
    lin = m_rect(W, H, 8, 20, 31, 23)
    shade(cv, lin, LACQUER, contour=True, R=1, base=0.55)
    cv.fill(m_rect(W, H, 9, 22, 30, 22), GOLD[3])
    xx, yy = grid(W, H)
    cv.fill(m_rect(W, H, 9, 22, 30, 22) & (xx % 3 == 0), GOLD[5])
    # brackets
    for bx in (13, 26):
        cv.fill(m_rect(W, H, bx, 24, bx, 25), GOLD[2])
    # roof
    roof_side(cv, 3, 36, 10, 19, "shrine_roof", curl=3)
    # finial pearl
    fin = m_ellipse(W, H, 19.5, 6.5, 1.8, 1.8)
    shade(cv, fin, GOLD, mode="sphere", base=0.5, gain=1.0)
    cv.fill(m_rect(W, H, 19, 8, 20, 9), GOLD[2])
    # censer on upper step
    cen = m_ellipse(W, H, 19.5, 44, 3.6, 2.2) & m_rect(W, H, 0, 42, W, 46)
    shade(cv, cen, BRONZE, contour=True, mode="sphere", base=0.55)
    cv.fill(m_rect(W, H, 16, 42, 23, 42), BRONZE[4])
    # sticks
    for sx, top in ((18, 36), (20, 35), (21, 37)):
        cv.fill(m_rect(W, H, sx, top, sx, 41), hexc("#6a3a20"))
        cv.put(sx, top, FIRE[4] if active else FIRE[1])
    # hanging lanterns
    lantern(cv, 6, 20, 4, 5, lit=active, flick=f % 2, cord=2)
    lantern(cv, 33, 20, 4, 5, lit=active, flick=(f + 1) % 2, cord=2)
    # grass at base
    for i, (gx, s) in enumerate(((5, 1), (34, 2), (9, 3), (31, 4))):
        grass_tuft(cv, gx, 53, ("shrg", s), h=4 + i % 2, n=3)
    outline(cv)
    if active:
        glow(cv, 6, 25, 4, 4, hexc("#ffb060"), steps=((1.0, 0.18), (0.6, 0.22)))
        glow(cv, 33, 25, 4, 4, hexc("#ffb060"), steps=((1.0, 0.18), (0.6, 0.22)))
        for i, sx in enumerate((18, 20, 21)):
            wisp(cv, sx, 34 - (i % 2), f, 4, height=14, seed=i * 1.7, alpha=0.65, amp=1.2)
    return cv


# ------------------------------------------------------------------ lantern post
@prop("lantern_post", 16, 56, states=(("lit", 2, 4),))
def lantern_post(state, f):
    cv = Canvas(16, 56)
    W, H = 16, 56
    ground_shadow(cv, 8, 54, 6, 1.5)
    stone_block(cv, 3, 48, 12, 53, "lp_base", moss=0.4)
    cv.fill(m_rect(W, H, 4, 47, 11, 47), STONE[5])
    plank_v(cv, 6, 9, 9, 47, LACQUER, seed="lp")
    cv.fill(m_rect(W, H, 6, 44, 9, 46), GOLD[2])
    cv.fill(m_rect(W, H, 6, 44, 9, 44), GOLD[4])
    # cross arm with a small bracket
    plank_h(cv, 3, 11, 13, 12, LACQUER, seed="lparm", grain=False, base=0.6)
    cv.fill(m_line(W, H, [(9, 16), (12, 13)]), LACQUER[3])
    cv.fill(m_line(W, H, [(6, 16), (3, 13)]), LACQUER[3])
    # tiny glazed cap roof
    roof_side(cv, 1, 14, 3, 8, "lp_roof", curl=1, thick=2, top_frac=0.3, finials=False)
    lantern(cv, 12, 13, 4, 6, lit=True, flick=f, cord=1)
    lantern(cv, 3, 13, 4, 6, lit=True, flick=1 - f, cord=1)
    outline(cv)
    for lx in (12, 3):
        glow(cv, lx, 17, 4 + f * 0.5, 4 + f * 0.5, hexc("#ffb060"), steps=((1.0, 0.14), (0.6, 0.2)))
    return cv


# ------------------------------------------------------------------ door (interior exit)
@prop("door", 40, 64, states=(("closed", 1, 0), ("open", 1, 0)))
def door(state, f):
    W, H = 40, 64
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    op = state == "open"
    # threshold stone
    stone_block(cv, 1, 58, 38, 61, "door_thr", chip=False)
    # opening
    opening = m_rect(W, H, 7, 12, 32, 57)
    if op:
        # daylight outside: pale sky, distant hills, ground
        cv.fill(opening, hexc("#cfe3de"))
        cv.fill(opening & (yy >= 30), hexc("#b7d3cc"))
        hills = opening & (yy >= 36 - (np.sin(xx * 0.5) * 2 + 2).astype(int))
        cv.fill(hills, hexc("#7fa89a"))
        cv.fill(opening & (yy >= 44), hexc("#9d8a62"))
        cv.fill(opening & (yy >= 50), hexc("#b49c6c"))
        cv.fill(opening & (yy == 44), hexc("#6f8a5a"))
        # doors swung open, foreshortened
        for (x0, x1) in ((7, 10), (29, 32)):
            leaf = m_rect(W, H, x0, 12, x1, 57)
            shade(cv, leaf, LACQUER, contour=True, R=1, base=0.35, gain=0.8)
            cv.fill(leaf & ((yy - 14) % 8 == 0), LACQUER[4])
    else:
        for (x0, x1, ring_x) in ((7, 19, 17), (20, 32, 22)):
            leaf = m_rect(W, H, x0, 12, x1, 57)
            shade(cv, leaf, LACQUER, contour=True, R=1, base=0.5, gain=1.0)
            # lattice panel (paper backed)
            lat = m_rect(W, H, x0 + 2, 15, x1 - 2, 33)
            cv.fill(lat, PAPER_R[3])
            cv.fill(lat & (((xx - x0) % 3 == 1) | ((yy - 15) % 3 == 0)), LACQUER[2])
            cv.fill(border(lat), LACQUER[1])
            # lower panel
            low = m_rect(W, H, x0 + 2, 37, x1 - 2, 54)
            cv.fill(border(low), LACQUER[2])
            cv.fill(top_edge(low) | left_edge(low), LACQUER[1])
            cv.fill(m_rect(W, H, x0 + 3, 38, x1 - 3, 38), LACQUER[5])
            # ring pull
            ring = m_ellipse(W, H, ring_x, 36, 1.6, 1.6) & ~m_rect(W, H, ring_x, 36, ring_x, 36)
            cv.fill(ring, GOLD[4])
            cv.put(ring_x, 34, GOLD[5])
        cv.fill(m_rect(W, H, 19, 12, 20, 57), LACQUER[0])
    # frame posts and lintel
    post(cv, 3, 8, 6, 57, LACQUER)
    post(cv, 33, 8, 36, 57, LACQUER)
    lin = m_rect(W, H, 1, 6, 38, 11)
    shade(cv, lin, LACQUER, contour=True, R=1, base=0.55)
    cv.fill(m_rect(W, H, 2, 9, 37, 9), GOLD[3])
    cv.fill(m_rect(W, H, 2, 9, 37, 9) & (xx % 4 == 0), GOLD[5])
    cv.fill(m_rect(W, H, 2, 7, 37, 7), LACQUER[5])
    # plaque
    plq = m_rect(W, H, 14, 1, 25, 6)
    shade(cv, plq, ROOF, contour=True, R=1, base=0.4)
    cv.fill(border(plq), GOLD[3])
    cv.fill(m_rect(W, H, 17, 3, 22, 3) | m_rect(W, H, 18, 4, 21, 4), GOLD[5])
    for bx in (3, 33):
        cv.fill(m_rect(W, H, bx, 55, bx + 3, 57), STONE[4])
    outline(cv)
    if op:
        glow(cv, 20, 50, 16, 10, PALE_GOLD, steps=((1.0, 0.1), (0.6, 0.12)), m_limit=yy >= 56)
    return cv


# ------------------------------------------------------------------ portal swirl
def lantern_pole(cv, x, top, bottom, flick, seed):
    plank_v(cv, x, top, x + 2, bottom, LACQUER, seed=seed)
    cv.fill(m_rect(cv.w, cv.h, x - 1, top - 1, x + 3, top), GOLD[3])
    cv.fill(m_rect(cv.w, cv.h, x - 1, top - 1, x + 3, top - 1), GOLD[5])
    stone_block(cv, x - 2, bottom - 3, x + 4, bottom, (seed, "f"))


@prop("portal_swirl", 48, 72, states=(("idle", 6, 10),))
def portal_swirl(state, f):
    W, H = 48, 72
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ground_shadow(cv, 24, 70, 23, 1.6)
    # stone dais
    stone_block(cv, 6, 64, 41, 69, "ps_dais", joint=8, moss=0.3)
    # vortex
    cx, cy, rx, ry = 24, 36, 14, 25
    vort = m_ellipse(W, H, cx, cy, rx, ry)
    cv.fill(vort, JADE_R[0])
    dx = (xx - cx) / rx
    dy = (yy - cy) / ry
    r = np.sqrt(dx * dx + dy * dy)
    th = np.arctan2(dy, dx)
    phase = f / 6.0 * (2 * math.pi / 3)
    spiral = np.mod(th * 3 / (2 * math.pi) * 1.0 + r * 2.2 - phase * 3 / (2 * math.pi), 1.0)
    arms = vort & (spiral < 0.34)
    cv.fill(vort & (r > 0.25), JADE_R[1])
    cv.fill(arms & (r > 0.2), JADE_R[3])
    cv.fill(arms & (spiral < 0.14) & (r > 0.3), JADE_R[4])
    cv.fill(arms & (spiral < 0.06) & (r > 0.45), JADE_R[5])
    core = m_ellipse(W, H, cx, cy, rx * 0.28, ry * 0.26)
    cv.fill(core, JADE_R[0])
    cv.fill(m_ellipse(W, H, cx, cy, rx * 0.14, ry * 0.12), DEEP_TEAL)
    rim = border(vort)
    cv.fill(rim, JADE_R[5])
    cv.fill(rim & (yy > cy) & (xx > cx), JADE_R[4])
    # lantern posts
    lantern_pole(cv, 2, 10, 69, f, "ps_l")
    lantern_pole(cv, 43, 10, 69, f, "ps_r")
    for (lx, arm_dir) in ((3, 1), (44, -1)):
        cv.fill(m_rect(W, H, min(lx, lx + arm_dir * 4), 11, max(lx, lx + arm_dir * 4), 12), LACQUER[3])
    lantern(cv, 7, 12, 4, 6, lit=True, flick=f % 2, cord=1)
    lantern(cv, 40, 12, 4, 6, lit=True, flick=(f + 1) % 2, cord=1)
    outline(cv)
    glow(cv, cx, cy, rx + 5, ry + 5, BRIGHT_JADE, steps=((1.0, 0.08), (0.8, 0.1)))
    motes(cv, 10, 8, 38, 64, f, 6, "ps_m", count=8, pal=(BRIGHT_JADE, WHITE_HOT))
    glow(cv, 7, 16, 4, 4, hexc("#ffb060"), steps=((1.0, 0.16),))
    glow(cv, 40, 16, 4, 4, hexc("#ffb060"), steps=((1.0, 0.16),))
    return cv


# ------------------------------------------------------------------ sealed gate
@prop("sealed_gate", 48, 72, states=(("idle", 1, 0),))
def sealed_gate(state, f):
    W, H = 48, 72
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ground_shadow(cv, 24, 70, 23, 1.6)
    # arch mass
    arch_outer = m_rect(W, H, 1, 20, 46, 69) | m_ellipse(W, H, 23.5, 21, 22.5, 19)
    arch_outer &= yy <= 69
    open_ = m_rect(W, H, 10, 26, 37, 66) | m_ellipse(W, H, 23.5, 27, 13.5, 13)
    body = arch_outer & ~open_
    nz = vnoise(W, H, 3, 61, 2)
    shade(cv, body, STONE, contour=True, R=3, strength=2.2, base=0.52, gain=1.4, noise=nz, namp=0.3)
    # voussoir joints radiating around the arch
    for a in np.linspace(math.pi * 1.05, math.pi * 1.95, 7):
        pts = [(23.5 + math.cos(a) * 14, 27 + math.sin(a) * 13.5), (23.5 + math.cos(a) * 22, 21 + math.sin(a) * 19)]
        cv.fill(m_line(W, H, pts) & erode(body), STONE[1])
    for jy in (34, 44, 54, 64):
        cv.fill(erode(body) & (yy == jy), STONE[1])
        cv.fill(erode(body) & (yy == jy + 1) & (nz > 0.5), STONE[5])
    # keystone
    ks = m_poly(W, H, [(20, 1), (27, 1), (26, 9), (21, 9)])
    shade(cv, ks, STONE, contour=True, R=1, base=0.6)
    cv.fill(m_rect(W, H, 22, 3, 25, 6), JADE_R[2])
    cv.fill(m_rect(W, H, 23, 4, 24, 5), JADE_R[4])
    # sealed stone doors
    doors = open_ & (yy <= 66)
    shade(cv, doors, STONE_DARK, contour=True, R=2, base=0.5, gain=1.2, noise=nz, namp=0.25)
    cv.fill(doors & (xx == 23), INK)
    cv.fill(doors & (xx == 24), STONE_DARK[1])
    for (x0, x1) in ((12, 21), (26, 35)):
        panel = m_rect(W, H, x0, 36, x1, 62)
        cv.fill(border(panel) & doors, STONE_DARK[2])
        cv.fill(top_edge(panel) & doors, STONE_DARK[4])
    # talismans across the seam
    for (tx, ty) in ((19, 44), (26, 50)):
        tal = m_rect(W, H, tx, ty, tx + 3, ty + 9)
        cv.fill(tal, hexc("#e8c86a"))
        cv.fill(right_edge(tal), hexc("#b8963e"))
        cv.fill(m_rect(W, H, tx + 1, ty + 2, tx + 2, ty + 2) | m_rect(W, H, tx + 1, ty + 4, tx + 2, ty + 6), CLOTH_RED[3])
    # glowing lock rune
    ring = m_ellipse(W, H, 23.5, 36, 6, 6) & ~m_ellipse(W, H, 23.5, 36, 4.6, 4.6)
    cv.fill(m_ellipse(W, H, 23.5, 36, 4.6, 4.6), STONE_DARK[1])
    cv.fill(ring, JADE_R[4])
    cv.fill(ring & (yy < 34) & (xx < 23), JADE_R[6])
    glyph = m_rect(W, H, 21, 34, 26, 34) | m_rect(W, H, 23, 32, 24, 40) | m_rect(W, H, 21, 38, 26, 38)
    cv.fill(glyph, JADE_R[5])
    stone_block(cv, 0, 66, 47, 69, "sg_base", joint=9, chip=False, moss=0.3)
    moss_top(cv, body, "sg_moss", 0.3)
    grass_tuft(cv, 2, 69, "sgg", h=5, n=3)
    grass_tuft(cv, 45, 69, "sgg2", h=4, n=3)
    outline(cv)
    glow(cv, 23.5, 36, 10, 10, BRIGHT_JADE, steps=((1.0, 0.1), (0.6, 0.16)))
    return cv


# ------------------------------------------------------------------ boat
@prop("lu_boat", 160, 48, ground=5)
def lu_boat(state, f):
    W, H = 160, 48
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    # hull: long sampan, raised bow (right) and stern (left)
    top = []
    bot = []
    for x in range(4, 157):
        t = (x - 4) / 152.0
        ty = 30 - 7 * max(0, (0.12 - t) / 0.12) ** 1.5 - 10 * max(0, (t - 0.82) / 0.18) ** 1.6
        by = 42 - 6 * max(0, (0.1 - t) / 0.1) ** 1.2 - 12 * max(0, (t - 0.8) / 0.2) ** 1.3
        top.append((x, ty))
        bot.append((x, by))
    hull = m_poly(W, H, top + list(reversed(bot)))
    nz = vnoise(W, H, 4, 71, 2)
    shade(cv, hull, WOOD, contour=True, R=2, base=0.42, gain=1.1, noise=nz, namp=0.2)
    # planks
    for k in (3, 6, 9):
        seam = m_poly(W, H, [(x, y + k) for x, y in top] + [(x, y + k + 0.8) for x, y in reversed(top)])
        cv.fill(seam & hull & erode(hull), WOOD[1])
    # gunwale rail
    rail = m_poly(W, H, [(x, y - 1) for x, y in top] + [(x, y + 1.2) for x, y in reversed(top)])
    shade(cv, rail, WOOD, R=1, base=0.7, gain=0.8)
    cv.fill(top_edge(rail), WOOD[6])
    # tar at waterline
    cv.fill(hull & (yy >= 40), WOOD[0])
    # canopy (woven bamboo arch)
    can = m_ellipse(W, H, 74, 29, 30, 20) & (yy <= 29) & (xx >= 46) & (xx <= 102)
    shade(cv, can, STRAW, contour=True, R=3, base=0.5, gain=1.2, top=0.2)
    weave = can & erode(can) & ((((xx // 2) + (yy // 2)) % 2) == 0)
    cv.fill(weave & (yy > 12), STRAW[2])
    cv.fill(weave & (yy <= 12), STRAW[3])
    for rx in (52, 63, 74, 85, 96):
        cv.fill(can & (xx == rx), STRAW[1])
    # canopy opening (dark inside) facing viewer on the right end
    ins = m_ellipse(W, H, 101, 29, 5, 15) & (yy <= 29) & can
    cv.fill(ins, WOOD[0])
    # mast pole + oar
    cv.fill(m_line(W, H, [(128, 29), (148, 2)], 1), WOOD[4])
    cv.fill(m_line(W, H, [(129, 29), (149, 2)], 1), WOOD[2])
    oar = m_line(W, H, [(18, 22), (4, 45)], 2)
    shade(cv, oar, WOOD, R=1, base=0.5)
    blade = m_poly(W, H, [(4, 40), (8, 42), (4, 47), (1, 46)])
    shade(cv, blade, WOOD, R=1, base=0.45)
    # stern lantern + items
    cv.fill(m_rect(W, H, 24, 12, 24, 22), WOOD[3])
    cv.fill(m_rect(W, H, 24, 12, 28, 12), WOOD[3])
    lantern(cv, 28, 13, 4, 5, lit=True, cord=1)
    bask = lathe(W, H, 118, [(24, 4), (28, 4.5), (29, 4)])
    shade(cv, bask, STRAW, contour=True, mode="cyl", base=0.5)
    jar = lathe(W, H, 38, [(22, 2), (24, 3.5), (28, 3.5), (29, 2.5)])
    shade(cv, jar, POTTERY, contour=True, mode="cyl", base=0.5)
    outline(cv)
    # waterline ripples (translucent, not outlined)
    for (x0, x1, y) in ((10, 22, 44), (40, 60, 45), (80, 100, 44), (120, 138, 45), (30, 38, 46), (140, 150, 46)):
        cv.fill(m_rect(W, H, x0, y, x1, y) & ~cv.solid, WATER[7], 0.7)
    glow(cv, 28, 17, 5, 5, hexc("#ffb060"), steps=((1.0, 0.15),))
    return cv


# ------------------------------------------------------------------ market stall
@prop("market_stall", 96, 72)
def market_stall(state, f):
    W, H = 96, 72
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ground_shadow(cv, 48, 70, 46, 1.6)
    # back posts
    for px in (8, 85):
        plank_v(cv, px, 14, px + 2, 69, WOOD, seed=("ms", px))
    # back shelf with goods
    back = m_rect(W, H, 11, 26, 84, 48)
    shade(cv, back, WOOD, contour=True, R=1, base=0.25, gain=0.6)
    plank_h(cv, 11, 36, 84, 37, WOOD, grain=False, base=0.55)
    for i, x in enumerate(range(14, 82, 7)):
        pal = [POTTERY, GLAZE_DARK, POTTERY, CLOTH_BLUE][i % 4]
        v = lathe(W, H, x + 2, [(30, 1.5), (31, 2.5), (35, 2.5)])
        shade(cv, v, pal, contour=True, mode="cyl", base=0.5)
    for i, x in enumerate(range(14, 82, 9)):
        bolt = m_rect(W, H, x, 41, x + 6, 47)
        shade(cv, bolt, [CLOTH_RED, CLOTH_JADE, CLOTH_BLUE, STRAW][i % 4], contour=True, mode="cylh", base=0.55)
    # hanging goods from awning beam
    for i, x in enumerate((20, 34, 60, 74)):
        cv.fill(m_rect(W, H, x, 17, x, 19), ROPE[2])
        if i % 2 == 0:
            for k in range(3):
                g_ = m_ellipse(W, H, x, 21 + k * 2.5, 1.6, 1.3)
                shade(cv, g_, PAPER_R, mode="sphere", base=0.55)
        else:
            fish = m_poly(W, H, [(x - 1, 20), (x + 1, 20), (x + 2, 24), (x, 27), (x - 2, 24)])
            shade(cv, fish, CLOTH_WHITE, contour=True, R=1, base=0.4)
    # counter
    ctr = m_rect(W, H, 4, 52, 91, 69)
    shade(cv, ctr, WOOD, contour=True, R=1, base=0.5, gain=0.9)
    for px in range(10, 90, 10):
        cv.fill(ctr & (xx == px) & (yy > 56), WOOD[2])
    plank_h(cv, 2, 50, 93, 53, WOOD, grain=True, base=0.62, seed="ctop")
    cloth = m_rect(W, H, 30, 54, 64, 64)
    shade(cv, cloth, CLOTH_JADE, R=1, base=0.5)
    cv.fill(border(cloth), GOLD[3])
    # goods on counter: baskets of produce, gourds, jars
    for i, (bx, pal) in enumerate(((14, ((CLOTH_RED, 4), (FIRE, 2))), (34, ((LEAF, 3), (LEAF, 4))),
                                   (54, ((GOLD, 4), (GOLD, 3))), (74, ((PAPER_R, 4), (FLESH_ROOT, 3))))):
        bas = lathe(W, H, bx + 5, [(45, 7), (49, 6), (50, 5)])
        shade(cv, bas, STRAW, contour=True, mode="cyl", base=0.5)
        cv.fill(bas & (xx % 2 == 0) & (yy > 46), STRAW[2])
        for k in range(5):
            px = bx + 1 + k * 2
            py = 44 - (k % 2)
            (p, idx) = pal[k % 2]
            cv.fill(m_ellipse(W, H, px + 0.5, py, 1.5, 1.4), p[idx])
            cv.put(px, py - 1, p[min(len(p) - 1, idx + 1)])
    # awning: striped cloth, scalloped edge
    aw = m_poly(W, H, [(2, 16), (12, 4), (84, 4), (94, 16)])
    cv.fill(aw, CLOTH_RED[3])
    stripes = aw & (((xx - 2) // 6) % 2 == 0)
    cv.fill(stripes, PAPER_R[4])
    cv.fill(aw & (yy <= 6), CLOTH_RED[4])
    cv.fill(stripes & (yy <= 6), PAPER_R[5])
    cv.fill(aw & (yy >= 14) & ~stripes, CLOTH_RED[2])
    cv.fill(aw & (yy >= 14) & stripes, PAPER_R[2])
    for sx in range(2, 94, 6):
        sc = m_ellipse(W, H, sx + 3, 16.5, 3, 2) & (yy >= 16)
        cv.fill(sc, PAPER_R[3] if ((sx - 2) // 6) % 2 == 0 else CLOTH_RED[2])
    cv.fill(m_rect(W, H, 12, 3, 84, 4), WOOD[3])
    # front posts
    for px in (3, 91):
        plank_v(cv, px, 14, px + 2, 69, WOOD, seed=("msf", px))
    # small sign board (no readable text)
    sb = m_rect(W, H, 40, 0, 56, 7)
    shade(cv, sb, LACQUER, contour=True, R=1, base=0.5)
    cv.fill(border(sb), GOLD[3])
    cv.fill(m_rect(W, H, 43, 3, 46, 3) | m_rect(W, H, 49, 3, 53, 3) | m_rect(W, H, 44, 4, 45, 4), GOLD[5])
    outline(cv)
    return cv


# ------------------------------------------------------------------ recruiter tents
def recruiter_tent(theme):
    W, H = 96, 80
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    if theme == "jade":
        cloth, trim, flag, emb = CLOTH_JADE, GOLD, CLOTH_JADE, GOLD
    else:
        cloth, trim, flag, emb = CLOTH_WHITE, CLOTH_BLUE, CLOTH_WHITE, CLOTH_BLUE
    ground_shadow(cv, 48, 78, 46, 1.6)
    # banner poles
    for (px, sgn) in ((4, 1), (89, -1)):
        plank_v(cv, px, 4, px + 1, 77, WOOD, grain=False, seed=("rtp", px))
        cv.fill(m_rect(W, H, px - 1, 2, px + 2, 3), GOLD[4])
        cv.put(px, 1, GOLD[5])
        cv.put(px + 1, 1, GOLD[5])
        bx0 = px + 2 if sgn > 0 else px - 8
        ban = m_poly(W, H, [(bx0, 6), (bx0 + 8, 6), (bx0 + 8, 40), (bx0 + 4, 36), (bx0, 40)])
        shade(cv, ban, flag, contour=True, R=1, base=0.55, gain=1.1)
        cv.fill(left_edge(ban) | right_edge(ban), trim[3])
        cv.fill(m_rect(W, H, bx0, 6, bx0 + 8, 7), trim[4])
        emb_m = m_ellipse(W, H, bx0 + 4, 16, 2.6, 2.6)
        cv.fill(emb_m, emb[4])
        cv.fill(m_ellipse(W, H, bx0 + 4, 16, 1.2, 1.2), flag[1])
        for k in range(3):
            cv.fill(m_rect(W, H, bx0 + 3, 22 + k * 4, bx0 + 5, 22 + k * 4), emb[3])
    # tent back wall
    wall = m_rect(W, H, 16, 32, 79, 76)
    shade(cv, wall, cloth, R=1, base=0.25, gain=0.5)
    cv.fill(wall & ((xx - 16) % 9 == 0), cloth[0])
    # table with ledger and scrolls
    tbl = m_rect(W, H, 30, 60, 65, 63)
    shade(cv, tbl, LACQUER, contour=True, R=1, base=0.6)
    for lx in (32, 62):
        cv.fill(m_rect(W, H, lx, 64, lx + 1, 76), LACQUER[2])
    cv.fill(m_rect(W, H, 30, 64, 65, 66), cloth[3])
    cv.fill(m_rect(W, H, 30, 66, 65, 66), trim[3])
    led = m_rect(W, H, 38, 57, 47, 59)
    cv.fill(led, PAPER_R[4])
    cv.fill(m_rect(W, H, 42, 57, 42, 59), PAPER_R[1])
    for (sx, c) in ((52, PAPER_R), (57, PAPER_R)):
        sc = m_rect(W, H, sx, 57, sx + 4, 59)
        shade(cv, sc, c, mode="cylh", base=0.5)
        cv.put(sx + 4, 58, CLOTH_RED[3])
    cv.fill(m_rect(W, H, 34, 55, 35, 59), INK)
    cv.put(34, 54, PAPER_R[4])
    # side flaps (tied back)
    for (x0, x1, sgn) in ((12, 22, 1), (73, 83, -1)):
        flap = m_poly(W, H, [(x0 if sgn > 0 else x1, 30), ((x1 if sgn > 0 else x0), 30),
                             ((x0 + 3 if sgn > 0 else x1 - 3), 50), ((x0 if sgn > 0 else x1), 76),
                             ((x0 - 1 if sgn > 0 else x1 + 1), 76)])
        shade(cv, flap, cloth, contour=True, R=2, base=0.55, gain=1.2)
        cv.fill(m_rect(W, H, min(x0, x1) + (2 if sgn > 0 else 5), 49, min(x0, x1) + (5 if sgn > 0 else 8), 50), trim[4])
    # front poles
    for px in (11, 83):
        plank_v(cv, px, 28, px + 1, 77, WOOD, grain=False, seed=("rtf", px))
    # peaked roof
    roof = m_poly(W, H, [(6, 32), (26, 16), (48, 8), (70, 16), (90, 32), (84, 34), (48, 30), (12, 34)])
    shade(cv, roof, cloth, contour=True, R=3, base=0.55, gain=1.3, top=0.25)
    for sx in (27, 38, 48, 58, 69):
        cv.fill(m_line(W, H, [(48, 9), (sx if sx != 48 else 48, 31)]) & erode(roof), cloth[2])
    # scalloped valance
    val = m_rect(W, H, 10, 31, 85, 34)
    cv.fill(val, trim[3])
    cv.fill(val & (yy == 31), trim[5])
    for sx in range(10, 86, 5):
        cv.fill(m_ellipse(W, H, sx + 2.5, 34.5, 2.5, 2) & (yy >= 34), trim[2] if (sx // 5) % 2 else trim[3])
    # finial + pennant
    cv.fill(m_rect(W, H, 47, 1, 48, 8), WOOD[3])
    pen = m_poly(W, H, [(49, 1), (56, 3), (49, 5)])
    cv.fill(pen, flag[4])
    cv.fill(bottom_edge(pen), flag[2])
    cv.put(47, 0, GOLD[5])
    outline(cv)
    return cv


@prop("recruiter_tent_jade", 96, 80)
def recruiter_tent_jade(state, f):
    return recruiter_tent("jade")


@prop("recruiter_tent_cloud", 96, 80)
def recruiter_tent_cloud(state, f):
    return recruiter_tent("cloud")


# ------------------------------------------------------------------ rite circle (ground decal)
@prop("rite_circle", 128, 32, states=(("idle", 1, 0), ("active", 4, 6)), ground=0, decal=True)
def rite_circle(state, f):
    W, H = 128, 32
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    on = state == "active"
    cx, cy = 64, 16
    disc = m_ellipse(W, H, cx, cy, 62, 15)
    cv.fill(disc, STONE[3], 0.55)
    cv.fill(m_ellipse(W, H, cx, cy, 58, 13.2), STONE[2], 0.5)

    def ring(rx, ry):
        return border(m_ellipse(W, H, cx, cy, rx, ry))
    lines = ring(60, 14.2) | ring(46, 10.8) | ring(24, 5.6)
    th = np.arctan2((yy - cy) / 14.0, (xx - cx) / 60.0)
    rr = np.sqrt(((xx - cx) / 60.0) ** 2 + ((yy - cy) / 14.2) ** 2)
    # trigram marks between the two outer rings
    marks = np.zeros((H, W), bool)
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        mx, my = cx + math.cos(a) * 53, cy + math.sin(a) * 12.4
        for j in range(3):
            broken = (k >> j) & 1
            y = round(my) - 1 + j
            if broken:
                marks |= m_rect(W, H, round(mx) - 3, y, round(mx) - 2, y) | m_rect(W, H, round(mx) + 1, y, round(mx) + 2, y)
            else:
                marks |= m_rect(W, H, round(mx) - 3, y, round(mx) + 2, y)
    marks = marks & disc
    spokes = np.zeros((H, W), bool)
    for k in range(8):
        a = k * math.pi / 4
        spokes |= m_line(W, H, [(cx + math.cos(a) * 24, cy + math.sin(a) * 5.6), (cx + math.cos(a) * 46, cy + math.sin(a) * 10.8)])
    # centre taiji-like swirl
    centre = border(m_ellipse(W, H, cx, cy, 10, 2.6))
    centre |= m_rect(W, H, cx - 5, cy, cx + 5, cy)
    allm = lines | marks | spokes | centre
    if on:
        cv.fill(allm, JADE_R[4])
        run = allm & (np.mod(th / (2 * math.pi) * 4 - f / 4.0, 1.0) < 0.25)
        cv.fill(run, JADE_R[6])
        cv.fill(marks, PALE_GOLD)
        glow(cv, cx, cy, 64, 16, BRIGHT_JADE, steps=((1.0, 0.1), (0.75, 0.08)))
        motes(cv, 10, 0, 118, 26, f, 4, "rite_m", count=10)
    else:
        cv.fill(allm, STONE[1], 0.9)
        cv.fill(shift(allm, 0, 1) & ~allm & disc, STONE[5], 0.6)
        cv.fill(marks, GOLD[2], 0.9)
    return cv


# ------------------------------------------------------------------ banners
def banner(theme):
    W, H = 24, 64
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    if theme == "jade":
        cloth, trim, emb = CLOTH_JADE, GOLD, GOLD
    else:
        cloth, trim, emb = CLOTH_WHITE, CLOTH_BLUE, CLOTH_BLUE
    ground_shadow(cv, 12, 62, 8, 1.3)
    stone_block(cv, 6, 57, 17, 61, ("bn_base", theme), moss=0.3)
    plank_v(cv, 11, 3, 12, 57, LACQUER, grain=False)
    cv.fill(m_rect(W, H, 10, 1, 13, 2), GOLD[4])
    cv.put(11, 0, GOLD[5])
    cv.put(12, 0, GOLD[5])
    # crossbar
    plank_h(cv, 3, 5, 20, 6, LACQUER, grain=False, base=0.6)
    cv.fill(m_rect(W, H, 2, 5, 2, 6) | m_rect(W, H, 21, 5, 21, 6), GOLD[4])
    # cloth with gentle wave and swallowtail
    pts_l = [(4 + math.sin(y * 0.25) * 0.8, y) for y in range(7, 48)]
    pts_r = [(19 + math.sin(y * 0.25 + 0.6) * 0.8, y) for y in range(47, 6, -1)]
    ban = m_poly(W, H, pts_l + [(4, 50), (11.5, 45), (19, 50)] + pts_r)
    wave = np.sin(yy * 0.25) * 0.5
    shade(cv, ban, cloth, contour=True, mode="cyl", base=0.55, gain=0.9, bias=wave * 0.25)
    cv.fill(ban & ((xx == 5) | (xx == 18)) & (yy < 46), trim[3])
    cv.fill(ban & (yy == 8), trim[4])
    # emblem: ring + three bars
    er = m_ellipse(W, H, 11.5, 17, 4, 4) & ~m_ellipse(W, H, 11.5, 17, 2.6, 2.6)
    cv.fill(er, emb[4])
    cv.fill(m_ellipse(W, H, 11.5, 17, 1.4, 1.4), emb[5] if theme == "jade" else emb[3])
    for k in range(3):
        cv.fill(m_rect(W, H, 9, 26 + k * 5, 14, 27 + k * 5), emb[3])
        cv.fill(m_rect(W, H, 9, 26 + k * 5, 14, 26 + k * 5), emb[5] if theme == "jade" else emb[4])
    # tassels
    for tx in (3, 20):
        cv.fill(m_rect(W, H, tx, 7, tx, 11), CLOTH_RED[4])
        cv.put(tx, 12, GOLD[4])
    outline(cv)
    return cv


@prop("banner_jade", 24, 64)
def banner_jade(state, f):
    return banner("jade")


@prop("banner_cloud", 24, 64)
def banner_cloud(state, f):
    return banner("cloud")


# ------------------------------------------------------------------ S49 territory: the banners over the spirit mines
def mine_banner(cloth, trim, pole, cap, emblem, tassel=CLOTH_RED, hem="swallow"):
    """A sect's banner planted beside a spirit-stone mine: the same frame as the sect banners (stone foot, pole,
    crossbar, waving cloth), with the holder's own cloth, trim and emblem."""
    W, H = 24, 64
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ground_shadow(cv, 12, 62, 8, 1.3)
    stone_block(cv, 6, 57, 17, 61, ("mb_base", emblem.__name__), moss=0.15)
    plank_v(cv, 11, 3, 12, 57, pole, grain=False)
    cv.fill(m_rect(W, H, 10, 1, 13, 2), cap[4])
    cv.put(11, 0, cap[5])
    cv.put(12, 0, cap[5])
    plank_h(cv, 3, 5, 20, 6, pole, grain=False, base=0.6)
    cv.fill(m_rect(W, H, 2, 5, 2, 6) | m_rect(W, H, 21, 5, 21, 6), cap[4])
    pts_l = [(4 + math.sin(y * 0.25) * 0.8, y) for y in range(7, 48)]
    pts_r = [(19 + math.sin(y * 0.25 + 0.6) * 0.8, y) for y in range(47, 6, -1)]
    tail = [(4, 50), (11.5, 45), (19, 50)] if hem == "swallow" else [(4, 49), (7.5, 52), (11.5, 48.5), (15.5, 52), (19, 49)]
    ban = m_poly(W, H, pts_l + tail + pts_r)
    shade(cv, ban, cloth, contour=True, mode="cyl", base=0.55, gain=0.9, bias=np.sin(yy * 0.25) * 0.12)
    cv.fill(ban & ((xx == 5) | (xx == 18)) & (yy < 46), trim[3])
    cv.fill(ban & (yy == 8), trim[4])
    emblem(cv, ban, xx, yy)
    for tx in (3, 20):
        cv.fill(m_rect(W, H, tx, 7, tx, 11), tassel[4])
        cv.put(tx, 12, cap[4])
    outline(cv)
    return cv


def _pine_emblem(cv, ban, xx, yy):
    """Ironpine Gate: a pine of three tiers on a short trunk, over two crossed spear shafts."""
    W, H = cv.w, cv.h
    for k, (top, half) in enumerate(((12, 2.5), (16, 4.0), (20, 5.5))):
        tier = m_poly(W, H, [(11.5, top), (11.5 + half, top + 5), (11.5 - half, top + 5)]) & ban
        cv.fill(tier, BONE[3])
        cv.fill(tier & (xx >= 12), BONE[2])
        cv.fill(tier & (yy == top + 5), BONE[1])
    cv.fill(m_rect(W, H, 11, 26, 12, 29) & ban, BONE[2])
    for (x0, x1) in ((7, 16), (16, 7)):
        cv.fill(m_line(W, H, [(x0, 31), (x1, 40)]) & ban, BONE[3])
    cv.fill(m_rect(W, H, 9, 43, 14, 43) & ban, BONE[2])


def _reed_emblem(cv, ban, xx, yy):
    """Blackreed Hall: three marsh reeds with seed heads, leaning together, over a still line of water."""
    W, H = cv.w, cv.h
    for (bx, tx, head) in ((9, 8, 14), (12, 12, 11), (15, 16, 15)):
        cv.fill(m_line(W, H, [(bx, 38), (tx, head + 4)]) & ban, HOLLOW[4])
        cat = m_rect(W, H, tx - 1, head, tx, head + 4) & ban      # a cattail head, brown and velvety
        cv.fill(cat, WOOD[4])
        cv.fill(cat & (xx == tx), WOOD[3])
        cv.put(tx, head - 1, HOLLOW[5])
    cv.fill(m_line(W, H, [(10, 33), (6, 27)]) & ban, HOLLOW[3])
    cv.fill(m_line(W, H, [(14, 32), (18, 26)]) & ban, HOLLOW[3])
    cv.fill(m_rect(W, H, 6, 40, 17, 40) & ban, JADE_R[3])
    cv.fill(m_rect(W, H, 8, 42, 15, 42) & ban, JADE_R[2])


def _kiln_emblem(cv, ban, xx, yy):
    """Scarlet Kiln Sect: a round kiln with its mouth aglow and a flame rising from the chimney."""
    W, H = cv.w, cv.h
    dome = m_ellipse(W, H, 11.5, 30, 6.0, 7.0) & (yy <= 33) & ban
    cv.fill(dome, GOLD[3])
    cv.fill(dome & (xx >= 13), GOLD[2])
    for by in (25, 29):                                          # brick courses
        cv.fill(dome & (yy == by), GOLD[1])
    cv.fill(dome & (yy > 25) & (yy < 29) & ((xx == 9) | (xx == 14)), GOLD[1])
    cv.fill(m_rect(W, H, 5, 33, 18, 35) & ban, GOLD[2])
    cv.fill(m_rect(W, H, 5, 35, 18, 35) & ban, GOLD[1])
    mouth = m_ellipse(W, H, 11.5, 31.5, 2.5, 2.2) & (yy <= 33)
    cv.fill(mouth, FIRE[3])
    cv.fill(m_rect(W, H, 11, 31, 12, 33), FIRE[4])
    cv.fill(m_rect(W, H, 10, 20, 13, 23) & ban, GOLD[2])
    fl = m_poly(W, H, [(11.5, 10), (14, 15), (13, 19), (10, 19), (9, 15)]) & ban
    cv.fill(fl, FIRE[2])
    cv.fill(fl & m_ellipse(W, H, 11.5, 16.5, 1.4, 2.4), FIRE[4])
    cv.put(11, 13, FIRE[5])


def _lotus_emblem(cv, ban, xx, yy):
    """Your own sect: a jade lotus of five petals on a gold ring (the banner your disciples plant)."""
    W, H = cv.w, cv.h
    ring = m_ellipse(W, H, 11.5, 22, 6.0, 6.0) & ~m_ellipse(W, H, 11.5, 22, 4.8, 4.8) & ban
    cv.fill(ring, GOLD[4])
    for (cx, cy, rx, ry) in ((11.5, 20, 1.6, 3.4), (8.8, 21.5, 1.4, 2.6), (14.2, 21.5, 1.4, 2.6), (7.6, 23.6, 1.8, 1.2), (15.4, 23.6, 1.8, 1.2)):
        pet = m_ellipse(W, H, cx, cy, rx, ry) & ban
        cv.fill(pet, JADE_R[4])
        cv.fill(pet & (yy <= cy - 1), JADE_R[5])
    cv.fill(m_rect(W, H, 9, 24, 14, 24) & ban, GOLD[3])
    for k in range(2):
        cv.fill(m_rect(W, H, 9, 32 + k * 5, 14, 33 + k * 5) & ban, GOLD[3])
        cv.fill(m_rect(W, H, 9, 32 + k * 5, 14, 32 + k * 5) & ban, GOLD[5])


@prop("banner_ironpine", 24, 64)
def banner_ironpine(state, f):
    return mine_banner(BRONZE, IRON, WOOD, IRON, _pine_emblem, tassel=STRAW)


@prop("banner_blackreed", 24, 64)
def banner_blackreed(state, f):
    return mine_banner(STONE_DARK, JADE_R, WOOD_GREY, IRON, _reed_emblem, tassel=HOLLOW, hem="ragged")


@prop("banner_scarlet_kiln", 24, 64)
def banner_scarlet_kiln(state, f):
    return mine_banner(CLOTH_RED, GOLD, LACQUER, GOLD, _kiln_emblem, tassel=GOLD)


@prop("banner_your_sect", 24, 64)
def banner_your_sect(state, f):
    return mine_banner(PAPER_R, JADE_R, LACQUER, GOLD, _lotus_emblem, tassel=CLOTH_JADE)


# ------------------------------------------------------------------ ladder / rope (vertical tiles)
def vtile(w, h, draw):
    """Draw on a 3x tall canvas and crop the middle so outlines wrap seamlessly."""
    big = Canvas(w, h * 3)
    draw(big)
    outline(big)
    out = Canvas(w, h)
    out.rgb = big.rgb[h:2 * h].copy()
    out.a = big.a[h:2 * h].copy()
    return out


@prop("ladder", 24, 32, kind="prop", repeat="y", ground=0, tile=True)
def ladder(state, f):
    def draw(cv):
        W, H = cv.w, cv.h
        for x0 in (3, 18):
            rail = m_rect(W, H, x0, 0, x0 + 2, H - 1)
            shade(cv, rail, WOOD, mode="cyl", base=0.55, gain=1.0, clean=False)
            for y in range(0, H, 16):
                cv.put(x0 + 1, y + 5, WOOD[2])
                cv.put(x0 + 1, y + 6, WOOD[2])
        for y in range(4, H, 8):
            rung = m_rect(W, H, 6, y, 17, y + 1)
            cv.fill(rung, WOOD[4])
            cv.fill(m_rect(W, H, 6, y + 1, 17, y + 1), WOOD[2])
            cv.fill(m_rect(W, H, 7, y, 9, y), WOOD[5])
            # rope lashings
            for x in (5, 18):
                cv.put(x, y - 1, ROPE[4])
                cv.put(x, y + 2, ROPE[2])
    return vtile(24, 32, draw)


@prop("rope", 8, 32, kind="prop", repeat="y", ground=0, tile=True)
def rope(state, f):
    def draw(cv):
        W, H = cv.w, cv.h
        xx, yy = grid(W, H)
        body = m_rect(W, H, 3, 0, 5, H - 1)
        cv.fill(body, ROPE[3])
        tw = (yy + xx) % 4
        cv.fill(body & (tw == 0), ROPE[1])
        cv.fill(body & (tw == 1), ROPE[2])
        cv.fill(body & (tw == 3), ROPE[4])
        cv.fill(body & (xx == 3) & (tw == 2), ROPE[5])
    return vtile(8, 32, draw)
