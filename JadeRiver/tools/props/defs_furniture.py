"""Interior furniture."""
from __future__ import annotations

import numpy as np

from palette import *  # noqa: F401,F403
from parts import flame, ground_shadow, lathe, plank_h, plank_v, smoke, vessel
from pixlib import (Canvas, border, bottom_edge, erode, glow, grid, left_edge, m_ellipse, m_line, m_poly, m_rect,
                    outline, right_edge, rng, seed_of, shade, shift, top_edge, vnoise)
from registry import prop
from defs_buildings import barrel, crate_box


def teapot(cv, cx, by, pal=GLAZE_DARK):
    W, H = cv.w, cv.h
    body = lathe(W, H, cx, [(by - 4, 1.5), (by - 3, 3), (by, 3)])
    shade(cv, body, pal, contour=True, mode="cyl", base=0.55)
    cv.fill(m_line(W, H, [(cx + 3, by - 2), (cx + 5, by - 4)]), pal[3])
    cv.fill(m_rect(W, H, cx - 4, by - 3, cx - 4, by - 1), pal[2])
    cv.put(cx, by - 5, pal[4])


def cup(cv, x, by, pal=PAPER_R):
    m = m_rect(cv.w, cv.h, x, by - 1, x + 2, by)
    cv.fill(m, pal[4])
    cv.put(x + 2, by, pal[2])


@prop("bed", 48, 24)
def bed(state, f):
    W, H = 48, 24
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ground_shadow(cv, 24, 22, 23, 1.3)
    # legs + frame
    for lx in (3, 43):
        cv.fill(m_rect(W, H, lx, 17, lx + 2, 21), LACQUER[2])
    frame = m_rect(W, H, 2, 13, 45, 17)
    shade(cv, frame, LACQUER, contour=True, R=1, base=0.5)
    cv.fill(m_rect(W, H, 3, 14, 44, 14), LACQUER[5])
    cv.fill(m_rect(W, H, 6, 16, 42, 16) & (xx % 6 == 0), GOLD[3])
    # headboard (left) + footboard (right)
    hb = m_rect(W, H, 1, 3, 4, 17)
    shade(cv, hb, LACQUER, contour=True, mode="cyl", base=0.5)
    cv.fill(m_rect(W, H, 0, 2, 5, 3), GOLD[3])
    fb = m_rect(W, H, 43, 8, 46, 17)
    shade(cv, fb, LACQUER, contour=True, mode="cyl", base=0.5)
    cv.fill(m_rect(W, H, 42, 7, 47, 8), GOLD[3])
    # mattress, quilt, pillow
    mat = m_rect(W, H, 5, 10, 42, 12)
    shade(cv, mat, PAPER_R, R=1, base=0.55)
    quilt = m_poly(W, H, [(15, 8), (40, 8), (43, 10), (43, 14), (14, 14), (13, 10)])
    shade(cv, quilt, CLOTH_JADE, contour=True, R=2, base=0.55, gain=1.2)
    cv.fill(quilt & ((xx - 15) % 7 == 0) & (yy > 8), CLOTH_JADE[2])
    cv.fill(m_rect(W, H, 14, 8, 17, 14) & quilt, CLOTH_JADE[5])
    pil = m_ellipse(W, H, 9, 8.5, 4, 2)
    shade(cv, pil, PAPER_R, contour=True, mode="sphere", base=0.55)
    cv.fill(m_rect(W, H, 7, 8, 11, 8), CLOTH_RED[3])
    outline(cv)
    return cv


@prop("table", 40, 24)
def table(state, f):
    W, H = 40, 24
    cv = Canvas(W, H)
    ground_shadow(cv, 20, 22, 19, 1.3)
    for lx in (4, 34):
        leg = m_rect(W, H, lx, 13, lx + 2, 21)
        shade(cv, leg, WOOD, contour=True, mode="cyl", base=0.45)
        cv.fill(m_rect(W, H, lx - 1, 20, lx + 3, 21), WOOD[2])
    apron = m_rect(W, H, 3, 12, 36, 14)
    shade(cv, apron, WOOD, contour=True, R=1, base=0.4)
    cv.fill(m_rect(W, H, 12, 13, 27, 13), WOOD[1])
    top = m_rect(W, H, 1, 9, 38, 11)
    shade(cv, top, WOOD, contour=True, R=1, base=0.65, top=0.3)
    cv.fill(m_rect(W, H, 2, 9, 37, 9), WOOD[6])
    teapot(cv, 16, 8)
    for x in (23, 27, 9):
        cup(cv, x, 8)
    outline(cv)
    smoke(cv, 21, 2, 0, 4, height=3, seed=3, count=1, size=1.0, alpha=0.4)
    return cv


@prop("counter", 64, 32)
def counter(state, f):
    W, H = 64, 32
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ground_shadow(cv, 32, 30, 31, 1.3)
    body = m_rect(W, H, 2, 14, 61, 29)
    shade(cv, body, WOOD, contour=True, R=1, base=0.45, gain=0.8)
    for px0 in range(5, 58, 14):
        pnl = m_rect(W, H, px0, 17, px0 + 10, 26)
        cv.fill(border(pnl), WOOD[2])
        cv.fill(top_edge(pnl) | left_edge(pnl), WOOD[1])
        cv.fill(m_rect(W, H, px0 + 1, 18, px0 + 9, 18), WOOD[5])
    cv.fill(m_rect(W, H, 2, 28, 61, 29), WOOD[1])
    top = m_rect(W, H, 0, 11, 63, 14)
    shade(cv, top, LACQUER, contour=True, R=1, base=0.6, top=0.3)
    cv.fill(m_rect(W, H, 1, 11, 62, 11), LACQUER[5])
    # abacus, ledger, brush, oil lamp
    ab = m_rect(W, H, 6, 5, 20, 10)
    shade(cv, ab, WOOD, contour=True, R=1, base=0.4)
    for ry in (7, 9):
        for bx in range(8, 19, 2):
            cv.put(bx, ry, [CLOTH_RED[4], PAPER_R[4]][(bx // 2) % 2])
    led = m_rect(W, H, 26, 8, 38, 10)
    cv.fill(led, PAPER_R[4])
    cv.fill(m_rect(W, H, 32, 8, 32, 10), PAPER_R[1])
    cv.fill(m_rect(W, H, 27, 9, 30, 9) | m_rect(W, H, 34, 9, 37, 9), PAPER_R[2])
    cv.fill(m_line(W, H, [(40, 10), (44, 6)]), WOOD[3])
    cv.put(44, 5, INK)
    lamp = lathe(W, H, 54, [(6, 1), (8, 3), (10, 2)])
    shade(cv, lamp, BRONZE, contour=True, mode="cyl")
    outline(cv)
    cv.fill(m_rect(W, H, 54, 3, 54, 5), FIRE[4])
    cv.put(54, 2, FIRE[3])
    glow(cv, 54, 4, 6, 5, PALE_GOLD, steps=((1.0, 0.12), (0.55, 0.16)))
    return cv


@prop("shelf", 48, 48)
def shelf(state, f):
    W, H = 48, 48
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ground_shadow(cv, 24, 46, 23, 1.3)
    back = m_rect(W, H, 3, 3, 44, 44)
    shade(cv, back, WOOD, R=1, base=0.2, gain=0.4)
    for sy in (14, 26, 38):
        plank_h(cv, 3, sy, 44, sy + 2, WOOD, grain=False, base=0.6)
    g = rng("shelf_items")
    for sy in (14, 26, 38):
        x = 5
        while x < 41:
            k = int(g.integers(0, 4))
            if k == 0 and x < 38:  # scroll stack
                for j in range(2):
                    m = m_rect(W, H, x, sy - 2 - j * 2, x + 6, sy - 1 - j * 2)
                    shade(cv, m, PAPER_R, mode="cylh", base=0.55)
                    cv.put(x + 6, sy - 2 - j * 2, CLOTH_RED[4])
                x += 8
            elif k == 1:  # jar
                pal = [POTTERY, GLAZE_DARK, CLOTH_BLUE][int(g.integers(0, 3))]
                v = lathe(W, H, x + 2.5, [(sy - 7, 1.5), (sy - 6, 2.5), (sy - 1, 2.5)])
                shade(cv, v, pal, contour=True, mode="cyl")
                x += 7
            elif k == 2:  # books (standing)
                for j in range(int(g.integers(2, 5))):
                    hgt = int(g.integers(6, 9))
                    m = m_rect(W, H, x + j * 2, sy - hgt, x + j * 2 + 1, sy - 1)
                    pal = [CLOTH_BLUE, CLOTH_RED, CLOTH_JADE, STRAW][(j + x) % 4]
                    cv.fill(m, pal[3])
                    cv.fill(left_edge(m), pal[4])
                    cv.put(x + j * 2, sy - hgt + 2, GOLD[4])
                x += 10
            else:  # box
                m = m_rect(W, H, x, sy - 5, x + 5, sy - 1)
                shade(cv, m, LACQUER, contour=True, R=1, base=0.55)
                cv.fill(m_rect(W, H, x + 2, sy - 3, x + 3, sy - 3), GOLD[4])
                x += 7
    for px in (1, 44):
        plank_v(cv, px, 1, px + 2, 45, WOOD, seed=("sh", px))
    plank_h(cv, 1, 1, 46, 3, WOOD, grain=False, base=0.65)
    plank_h(cv, 1, 43, 46, 45, WOOD, grain=False, base=0.4)
    outline(cv)
    return cv


@prop("herb_drawers", 48, 48)
def herb_drawers(state, f):
    W, H = 48, 48
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ground_shadow(cv, 24, 46, 23, 1.3)
    body = m_rect(W, H, 2, 10, 45, 45)
    shade(cv, body, WOOD, contour=True, R=1, base=0.4, gain=0.8)
    for r in range(5):
        for c in range(5):
            x0, y0 = 4 + c * 8, 12 + r * 6
            d = m_rect(W, H, x0, y0, x0 + 6, y0 + 4)
            shade(cv, d, WOOD, R=1, base=0.55 - 0.03 * r, gain=1.0)
            cv.fill(top_edge(d), WOOD[5])
            cv.fill(bottom_edge(d) | right_edge(d), WOOD[2])
            cv.fill(m_rect(W, H, x0 + 1, y0 + 1, x0 + 3, y0 + 2), PAPER_R[3] if (r + c) % 3 else PAPER_R[2])
            cv.fill(m_rect(W, H, x0 + 1, y0 + 2, x0 + 2 + (r + c) % 2, y0 + 2), PAPER_R[1])
            cv.put(x0 + 5, y0 + 2, BRONZE[5])
    plank_h(cv, 1, 8, 46, 10, WOOD, grain=False, base=0.65)
    cv.fill(m_rect(W, H, 3, 43, 44, 45), WOOD[1])
    # jars and a scale on top
    for (jx, pal) in ((8, POTTERY), (15, GLAZE_DARK), (21, CLOTH_BLUE)):
        v = lathe(W, H, jx, [(1, 1.5), (2, 2.5), (4, 3), (7, 3)])
        shade(cv, v, pal, contour=True, mode="cyl")
        cv.fill(m_rect(W, H, jx - 1, 4, jx + 1, 5), PAPER_R[4])
    cv.fill(m_rect(W, H, 34, 2, 34, 7), BRONZE[4])
    cv.fill(m_rect(W, H, 29, 2, 39, 2), BRONZE[5])
    for px in (29, 39):
        cv.fill(m_line(W, H, [(px, 3), (px - 2, 5)]) | m_line(W, H, [(px, 3), (px + 2, 5)]), BRONZE[3])
        cv.fill(m_rect(W, H, px - 2, 5, px + 2, 5), BRONZE[4])
    cv.fill(m_rect(W, H, 32, 7, 36, 7), BRONZE[3])
    outline(cv)
    return cv


@prop("stove", 40, 40)
def stove(state, f):
    W, H = 40, 40
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ground_shadow(cv, 20, 38, 19, 1.3)
    body = m_rect(W, H, 2, 16, 37, 37)
    nz = vnoise(W, H, 3, 91, 2)
    shade(cv, body, MUD, contour=True, R=2, base=0.5, gain=1.2, noise=nz, namp=0.3)
    # brick courses
    for by in range(20, 37, 4):
        cv.fill(body & erode(body) & (yy == by), MUD[1])
        off = 0 if (by // 4) % 2 else 4
        cv.fill(body & erode(body) & ((xx + off) % 8 == 0) & (yy > by - 4) & (yy < by), MUD[1])
    top = m_rect(W, H, 1, 14, 38, 16)
    shade(cv, top, STONE, contour=True, R=1, base=0.6)
    # fire mouth
    mouth = m_rect(W, H, 14, 27, 25, 34) | m_ellipse(W, H, 19.5, 27, 5.5, 2.5)
    mouth &= yy <= 34
    cv.fill(mouth, INK)
    cv.fill(m_rect(W, H, 15, 31, 24, 34), FIRE[1])
    cv.fill(m_rect(W, H, 16, 32, 23, 34), FIRE[2])
    cv.fill(m_rect(W, H, 18, 33, 21, 34), FIRE[4])
    # wok + pot
    wok = m_ellipse(W, H, 11, 13, 8, 3) & (yy <= 14)
    shade(cv, wok, IRON, contour=True, R=1, base=0.5)
    cv.fill(m_rect(W, H, 3, 11, 19, 11), IRON[5])
    cv.fill(m_rect(W, H, 1, 12, 3, 12), WOOD[3])
    pot = lathe(W, H, 28, [(6, 4), (7, 5), (13, 5)])
    shade(cv, pot, IRON, contour=True, mode="cyl", base=0.5)
    lid = m_rect(W, H, 23, 5, 33, 6)
    shade(cv, lid, WOOD, R=1, base=0.6)
    cv.fill(m_rect(W, H, 27, 3, 29, 4), WOOD[4])
    # firewood
    for (x0, y0) in ((29, 34), (30, 36)):
        lg = m_rect(W, H, x0, y0, x0 + 8, y0 + 1)
        shade(cv, lg, WOOD, R=1, base=0.5)
        cv.put(x0 + 8, y0, WOOD[5])
    outline(cv)
    glow(cv, 19.5, 32, 8, 5, FIRE[3], steps=((1.0, 0.15), (0.6, 0.2)))
    smoke(cv, 28, 2, 1, 4, height=3, seed=7, count=1, size=1.0, alpha=0.45)
    return cv
