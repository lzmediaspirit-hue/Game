"""Humble village buildings (manifest adds "building": true and "roof_split").

roof_split = fraction of the image height (from the top) that is roof; the engine
turns that band into a walkable rooftop and draws the facade below it.
"""
from __future__ import annotations

import math

import numpy as np

from palette import *  # noqa: F401,F403
from parts import (blob_mask, grass_tuft, ground_shadow, lantern, lathe, moss_top, plank_h, plank_v, post, rock,
                   rope_band, roof_side, smoke)
from pixlib import (Canvas, bbox, border, bottom_edge, dilate, erode, glow, grid, left_edge, m_curve, m_ellipse,
                    m_line, m_poly, m_rect, mix, outline, right_edge, rng, seed_of, shade, shift, top_edge, vnoise)
from registry import prop
from defs_structures import stone_block


def building(pid, w, h, roof_px, ground=2, states=(("idle", 1, 0),)):
    return prop(pid, w, h, states=states, ground=ground, building=True, roof_split=round(roof_px / h, 3))


# ------------------------------------------------------------------ building parts
def plank_wall(cv, x0, y0, x1, y1, pal=WOOD_GREY, seed=0, pw=4, dirt=True):
    W, H = cv.w, cv.h
    xx, yy = grid(W, H)
    g = rng("pwall", seed)
    wall = m_rect(W, H, x0, y0, x1, y1)
    nz = vnoise(W, H, 3, seed_of("pwn", seed), 2)
    idx = np.zeros((H, W), int)
    n = len(pal)
    base_i = np.zeros((H, W))
    for px in range(x0, x1 + 1, pw):
        b = g.uniform(-0.12, 0.12)
        base_i[:, px:px + pw] = b
    v = 0.5 + base_i + (nz - 0.5) * 0.35
    if dirt:
        v -= np.clip((yy - (y1 - 10)) / 10.0, 0, 1) * 0.18
    v -= np.clip((y0 + 4 - yy) / 4.0, 0, 1) * 0.25  # eave shadow
    idx = np.clip((v * n).astype(int), 1, n - 2)
    cv.fill_idx(wall, idx, pal)
    seams = wall & ((xx - x0) % pw == pw - 1)
    cv.fill(seams, pal[1])
    cv.fill(wall & ((xx - x0) % pw == 0) & (nz > 0.55), pal[4])
    # knots and nails
    for _ in range((x1 - x0) * (y1 - y0) // 160):
        kx, ky = int(g.integers(x0 + 1, x1)), int(g.integers(y0 + 3, y1 - 2))
        if (kx - x0) % pw not in (0, pw - 1):
            cv.put(kx, ky, pal[1])
            cv.put(kx, ky - 1, pal[3])
    return wall


def plaster_wall(cv, x0, y0, x1, y1, pal=PLASTER, seed=0):
    W, H = cv.w, cv.h
    xx, yy = grid(W, H)
    wall = m_rect(W, H, x0, y0, x1, y1)
    nz = vnoise(W, H, 5, seed_of("plw", seed), 2)
    n = len(pal)
    v = 0.62 + (nz - 0.5) * 0.3
    v -= np.clip((yy - (y1 - 14)) / 14.0, 0, 1) * 0.3
    v -= np.clip((y0 + 5 - yy) / 5.0, 0, 1) * 0.35
    idx = np.clip((v * n).astype(int), 0, n - 1)
    cv.fill_idx(wall, idx, pal)
    # damp stain + a couple of hairline cracks
    stain = wall & (yy > y1 - 9) & (vnoise(W, H, 3, seed_of("stain", seed)) > 0.55)
    cv.fill(stain, mix(pal[1], MOSS[1], 0.25))
    g = rng("plcrack", seed)
    for _ in range(max(1, (x1 - x0) // 50)):
        cx, cy = int(g.integers(x0 + 4, x1 - 4)), int(g.integers(y0 + 6, y1 - 12))
        pts = [(cx, cy)]
        for _s in range(4):
            cx += int(g.integers(-1, 2))
            cy += 1
            pts.append((cx, cy))
        cv.fill(m_line(W, H, pts) & wall, pal[1])
    return wall


def timber(cv, x0, y0, x1, y1, pal=WOOD, horiz=False, seed=0):
    if horiz:
        return plank_h(cv, x0, y0, x1, y1, pal, seed=seed, grain=(x1 - x0) > 8)
    return plank_v(cv, x0, y0, x1, y1, pal, seed=seed, grain=(y1 - y0) > 10)


def thatch_roof(cv, pts, seed, pal=THATCH, ridge=None, fringe=3):
    """Straw/reed thatch: shaded mass, strand streaks, course lines, ragged fringe."""
    W, H = cv.w, cv.h
    xx, yy = grid(W, H)
    body = m_poly(W, H, pts)
    x0, y0, x1, y1 = bbox(body)
    g = rng("thatch", seed)
    # ragged fringe along the bottom edge
    fr = np.zeros((H, W), bool)
    be = bottom_edge(body)
    for x in range(x0, x1 + 1):
        ys = np.nonzero(be[:, x])[0]
        if len(ys):
            y = ys.max()
            d = int(g.integers(0, fringe + 1)) if (x % 2 == 0) else int(g.integers(0, 2))
            fr[y + 1:y + 1 + d, x] = True
    body |= fr
    nz = vnoise(W, H, 4, seed_of("thn", seed), 2)
    shade(cv, body, pal, contour=True, R=5, strength=2.0, base=0.5, gain=1.2, noise=nz, namp=0.35, top=0.25)
    # course bands every 7 rows (wavy)
    for cy in range(y0 + 7, y1, 7):
        wav = (np.sin(xx * 0.35 + cy) * 1.2).astype(int)
        band = body & (yy == cy + wav) & erode(body)
        cv.fill(band, pal[1])
        cv.fill(shift(band, 0, -1) & body & ~band, pal[4])
    # strand streaks
    for _ in range((x1 - x0) * (y1 - y0) // 14):
        sx, sy = int(g.integers(x0, x1 + 1)), int(g.integers(y0, y1 + 1))
        ln = int(g.integers(2, 5))
        st = m_rect(W, H, sx, sy, sx, sy + ln) & erode(body)
        c = pal[2] if g.random() < 0.6 else pal[5]
        cv.fill(st, c)
    # fringe colouring
    cv.fill(fr & (xx % 2 == 0), pal[2])
    cv.fill(fr & (xx % 2 == 1), pal[3])
    cv.fill(bottom_edge(body), pal[1])
    if ridge:
        rx0, rx1, ry = ridge
        rm = m_rect(W, H, rx0, ry - 2, rx1, ry + 2)
        rm[ry - 2, rx0] = rm[ry - 2, rx1] = False
        shade(cv, rm, pal, contour=True, mode="cylh", base=0.55, gain=1.0)
        for tx in range(rx0 + 4, rx1 - 2, 10):
            cv.fill(m_rect(W, H, tx, ry - 2, tx + 1, ry + 2), ROPE[2])
            cv.put(tx, ry - 2, ROPE[4])
    return body


def lattice_window(cv, x0, y0, x1, y1, lit=False, frame=WOOD, style="grid"):
    W, H = cv.w, cv.h
    xx, yy = grid(W, H)
    fr = m_rect(W, H, x0, y0, x1, y1)
    shade(cv, fr, frame, contour=True, R=1, base=0.45)
    inner = m_rect(W, H, x0 + 2, y0 + 2, x1 - 2, y1 - 2)
    paper = hexc("#f3c77a") if lit else PAPER_R[3]
    cv.fill(inner, paper)
    cv.fill(inner & (yy >= (y0 + y1) // 2), hexc("#e0a85a") if lit else PAPER_R[2])
    if style == "grid":
        lat = inner & (((xx - x0) % 3 == 1) | ((yy - y0) % 3 == 1))
    else:  # "ice" diagonal lattice
        lat = inner & (((xx + yy) % 4 == 0) | ((xx - yy) % 4 == 0))
    cv.fill(lat, frame[1])
    cv.fill(top_edge(fr) | left_edge(fr), frame[4])
    sill = m_rect(W, H, x0 - 1, y1, x1 + 1, y1 + 1)
    shade(cv, sill, frame, R=1, base=0.6)
    return fr


def round_window(cv, cx, cy, r, lit=False, frame=WOOD):
    W, H = cv.w, cv.h
    xx, yy = grid(W, H)
    outer = m_ellipse(W, H, cx, cy, r, r)
    shade(cv, outer, frame, contour=True, mode="sphere", base=0.45)
    inner = m_ellipse(W, H, cx, cy, r - 2, r - 2)
    cv.fill(inner, hexc("#f3c77a") if lit else PAPER_R[3])
    cv.fill(inner & (yy > cy), hexc("#e0a85a") if lit else PAPER_R[2])
    lat = inner & (((xx - int(cx)) % 4 == 0) | ((yy - int(cy)) % 4 == 0))
    cv.fill(lat, frame[1])
    cv.fill(border(outer) & (yy < cy) & (xx < cx), frame[5])
    return outer


def plank_door(cv, x0, y0, x1, y1, pal=WOOD, strap=IRON, ajar=0):
    W, H = cv.w, cv.h
    xx, yy = grid(W, H)
    frame = m_rect(W, H, x0 - 2, y0 - 2, x1 + 2, y1)
    shade(cv, frame, WOOD, contour=True, R=1, base=0.4)
    d = m_rect(W, H, x0, y0, x1, y1)
    cv.fill(d, INK)
    leaf = m_rect(W, H, x0 + ajar, y0, x1, y1)
    plank_wall(cv, x0 + ajar, y0, x1, y1, pal, seed=("door", x0), pw=3, dirt=True)
    cv.fill(left_edge(leaf), pal[1])
    for sy in (y0 + 4, y1 - 5):
        cv.fill(m_rect(W, H, x0 + ajar, sy, x1, sy + 1), strap[3])
        cv.fill(m_rect(W, H, x0 + ajar, sy, x1, sy), strap[5])
    cv.put(x0 + ajar + 2, (y0 + y1) // 2, GOLD[4])
    cv.put(x0 + ajar + 2, (y0 + y1) // 2 + 1, GOLD[2])
    if ajar:
        cv.fill(m_rect(W, H, x0, y0, x0 + ajar - 1, y1), hexc("#1a1210"))
    return frame


def barrel(cv, cx, by, r=5, hgt=12, pal=WOOD):
    m = lathe(cv.w, cv.h, cx, [(by - hgt + 1, r - 1), (by - hgt // 2, r), (by, r - 1)])
    shade(cv, m, pal, contour=True, mode="cyl", base=0.5)
    xx, yy = grid(cv.w, cv.h)
    for hy in (by - hgt + 3, by - 2):
        cv.fill(m & (yy == hy), IRON[3])
    cv.fill(top_edge(m), pal[5])
    return m


def crate_box(cv, x0, y0, s, pal=WOOD, seed=0):
    W, H = cv.w, cv.h
    m = m_rect(W, H, x0, y0, x0 + s - 1, y0 + s - 1)
    shade(cv, m, pal, contour=True, R=1, base=0.55, gain=1.2)
    inner = m_rect(W, H, x0 + 2, y0 + 2, x0 + s - 3, y0 + s - 3)
    cv.fill(border(inner), pal[2])
    cv.fill(m_line(W, H, [(x0 + 2, y0 + s - 3), (x0 + s - 3, y0 + 2)]), pal[4])
    cv.fill(top_edge(m), pal[6] if len(pal) > 6 else pal[-1])
    return m


def sack(cv, cx, by, w=6, h=7, pal=ROPE):
    W, H = cv.w, cv.h
    m = m_poly(W, H, [(cx - w / 2, by), (cx + w / 2, by), (cx + w / 2 - 0.5, by - h * 0.6), (cx + 1, by - h + 1),
                      (cx + 1, by - h - 1), (cx - 1, by - h - 1), (cx - 1, by - h + 1), (cx - w / 2 + 0.5, by - h * 0.6)])
    shade(cv, m, pal, contour=True, R=2, base=0.55, gain=1.2)
    cv.fill(m_rect(W, H, cx - 1, by - h + 1, cx + 1, by - h + 1), ROPE[1])
    cv.put(cx - 1, by - 3, pal[2])
    return m


def fish(cv, x, y, pal=CLOTH_WHITE):
    m = m_poly(cv.w, cv.h, [(x - 1, y), (x + 1, y), (x + 2, y + 4), (x, y + 7), (x - 2, y + 4)])
    shade(cv, m, pal, contour=True, R=1, base=0.42)
    cv.fill(m_poly(cv.w, cv.h, [(x - 1, y + 7), (x + 1, y + 7), (x, y + 8)]), pal[2])
    cv.put(x, y + 1, INK)
    return m


def herb_bundle(cv, x, y, pal, ln=8):
    W, H = cv.w, cv.h
    cv.fill(m_rect(W, H, x, y, x, y + 1), ROPE[3])
    m = m_poly(W, H, [(x - 1, y + 2), (x + 1, y + 2), (x + 3, y + ln), (x - 3, y + ln)])
    shade(cv, m, pal, contour=True, R=1, base=0.5, gain=1.2)
    xx, yy = grid(W, H)
    cv.fill(m & (xx % 2 == 0) & (yy > y + 3), pal[2])
    cv.fill(m_rect(W, H, x - 1, y + 2, x + 1, y + 2), ROPE[2])
    return m


def eave_shadow(cv, x0, x1, y, depth=3):
    """Darken the wall just under an eave (drawn after walls)."""
    W, H = cv.w, cv.h
    m = m_rect(W, H, x0, y, x1, y + depth - 1) & cv.solid
    cv.fill(m, INK, 0.35)
    cv.fill(m_rect(W, H, x0, y, x1, y) & cv.solid, INK, 0.3)


def grass_row(cv, x0, x1, by, seed, step=9):
    g = rng("grow", seed)
    for x in range(x0, x1, step):
        if g.random() < 0.7:
            grass_tuft(cv, x + int(g.integers(0, 4)), by, (seed, x), h=int(g.integers(3, 6)), n=3)


# ------------------------------------------------------------------ thatched fisher's hut
@building("thatched_hut", 180, 120, roof_px=58)
def thatched_hut(state, f):
    W, H = 180, 120
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ground_shadow(cv, 90, 118, 86, 1.8)
    stone_block(cv, 10, 110, 169, 117, "th_base", course=4, joint=9, moss=0.35)
    plank_wall(cv, 14, 50, 165, 109, WOOD_GREY, seed="th_wall", pw=5)
    for px in (12, 88, 164):
        timber(cv, px, 48, px + 3, 110, WOOD, seed=("thp", px))
    timber(cv, 12, 80, 167, 82, WOOD, horiz=True, seed="th_rail")
    # door (ajar) + step
    plank_door(cv, 64, 70, 82, 109, WOOD, ajar=4)
    stone_block(cv, 60, 107, 86, 109, "th_step", chip=True)
    # small window with propped shutter
    win = m_rect(W, H, 112, 66, 130, 80)
    shade(cv, win, WOOD, contour=True, R=1, base=0.4)
    cv.fill(m_rect(W, H, 114, 68, 128, 78), INK)
    cv.fill(m_rect(W, H, 114, 68, 128, 78) & ((xx - 114) % 4 == 1), STRAW[3])
    sh = m_poly(W, H, [(110, 64), (132, 64), (136, 58), (114, 58)])
    shade(cv, sh, WOOD_GREY, contour=True, R=1, base=0.55)
    cv.fill(m_line(W, H, [(130, 66), (134, 60)]), WOOD[4])
    # net draped on right wall
    net = m_poly(W, H, [(138, 56), (160, 56), (158, 88), (148, 94), (140, 86)])
    cv.fill(net & (((xx + yy) % 3 == 0) | ((xx - yy) % 3 == 0)), ROPE[3])
    cv.fill(border(net) & (yy > 57), ROPE[2])
    for (fx, fy) in ((142, 84), (150, 90), (157, 80)):
        fl = m_ellipse(W, H, fx, fy, 1.6, 1.3)
        shade(cv, fl, CLOTH_RED, mode="sphere")
    # oar + basket + barrel by the door
    oar = m_line(W, H, [(96, 108), (104, 60)], 2)
    shade(cv, oar, WOOD, R=1, base=0.55)
    blade = m_poly(W, H, [(102, 60), (106, 61), (107, 50), (104, 48), (101, 51)])
    shade(cv, blade, WOOD, R=1, base=0.5)
    bas = lathe(W, H, 30, [(98, 7), (104, 8), (109, 7)])
    shade(cv, bas, STRAW, contour=True, mode="cyl", base=0.5)
    cv.fill(bas & ((xx + yy) % 3 == 0), STRAW[2])
    cv.fill(top_edge(bas), STRAW[5])
    barrel(cv, 48, 109, 5, 13)
    # roof
    thatch_roof(cv, [(1, 56), (18, 30), (44, 12), (90, 5), (136, 12), (162, 30), (179, 56), (168, 57), (90, 54),
                     (12, 57)], "th_roof", ridge=(52, 128, 7))
    eave_shadow(cv, 14, 165, 59, 3)
    # hanging fish-drying rack under the eave
    for rx in (20, 56):
        cv.fill(m_rect(W, H, rx, 57, rx, 63), ROPE[2])
    rack = m_rect(W, H, 16, 63, 60, 64)
    shade(cv, rack, STRAW, R=1, base=0.6)
    for i, fx in enumerate(range(21, 58, 7)):
        cv.fill(m_rect(W, H, fx, 65, fx, 66), ROPE[3])
        fish(cv, fx, 67 + (i % 2), CLOTH_WHITE if i % 2 else FLESH_ROOT)
    grass_row(cv, 4, 176, 117, "th_g")
    lantern(cv, 90, 57, 4, 6, lit=False, cord=2)
    outline(cv)
    return cv


# ------------------------------------------------------------------ village store
@building("village_store", 200, 130, roof_px=46)
def village_store(state, f):
    W, H = 200, 130
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ground_shadow(cv, 100, 128, 96, 1.8)
    stone_block(cv, 4, 119, 195, 127, "vs_base", course=4, joint=11, moss=0.3)
    # side walls (plaster with timber)
    plaster_wall(cv, 8, 44, 46, 118, seed="vs_l")
    plaster_wall(cv, 154, 44, 192, 118, seed="vs_r")
    # shop interior
    inside = m_rect(W, H, 47, 44, 153, 118)
    shade(cv, inside, WOOD, R=1, base=0.18, gain=0.4)
    for sy in (62, 78, 94):
        plank_h(cv, 48, sy, 152, sy + 1, WOOD, grain=False, base=0.55)
    g = rng("vs_goods")
    for sy in (62, 78):
        x = 50
        while x < 148:
            k = int(g.integers(0, 4))
            if k == 0:
                v = lathe(W, H, x + 3, [(sy - 7, 1.5), (sy - 6, 3), (sy - 1, 3)])
                shade(cv, v, [POTTERY, GLAZE_DARK, CLOTH_BLUE][int(g.integers(0, 3))], contour=True, mode="cyl")
                x += 8
            elif k == 1:
                b = m_rect(W, H, x, sy - 5, x + 7, sy - 1)
                shade(cv, b, [CLOTH_RED, CLOTH_JADE, CLOTH_BLUE, STRAW][int(g.integers(0, 4))], contour=True,
                      mode="cylh", base=0.55)
                x += 9
            elif k == 2:
                b = m_rect(W, H, x, sy - 6, x + 6, sy - 1)
                shade(cv, b, WOOD, contour=True, R=1, base=0.6)
                cv.fill(m_rect(W, H, x + 1, sy - 4, x + 5, sy - 4), WOOD[2])
                x += 8
            else:
                x += 4
    # counter
    ctr = m_rect(W, H, 50, 98, 150, 118)
    shade(cv, ctr, WOOD, contour=True, R=1, base=0.5)
    for px in range(58, 150, 12):
        cv.fill(ctr & (xx == px) & (yy > 101), WOOD[2])
    plank_h(cv, 48, 96, 152, 99, WOOD, seed="vs_top", base=0.65)
    # goods on counter: abacus, scale, baskets
    ab = m_rect(W, H, 60, 88, 76, 95)
    shade(cv, ab, WOOD, contour=True, R=1, base=0.4)
    for ry in (90, 93):
        for bx in range(62, 75, 2):
            cv.put(bx, ry, [CLOTH_RED[4], PAPER_R[4]][(bx // 2) % 2])
    for i, bx in enumerate((92, 112, 132)):
        bas = lathe(W, H, bx + 5, [(90, 7), (95, 6)])
        shade(cv, bas, STRAW, contour=True, mode="cyl")
        for k in range(5):
            pal = [CLOTH_RED, LEAF, GOLD][i]
            cv.fill(m_ellipse(W, H, bx + 1 + k * 2, 88 - (k % 2), 1.5, 1.4), pal[4])
    # timber posts
    for px in (6, 45, 153, 191):
        timber(cv, px, 42, px + 3, 119, WOOD, seed=("vsp", px))
    # vertical shop sign on the left wall (no readable text)
    vs = m_rect(W, H, 20, 56, 30, 100)
    shade(cv, vs, LACQUER, contour=True, R=1, base=0.45)
    cv.fill(border(vs), GOLD[3])
    for k, sy in enumerate(range(61, 96, 9)):
        cv.fill(m_rect(W, H, 23, sy, 27, sy) | m_rect(W, H, 25, sy + 1, 25, sy + 4) | m_rect(W, H, 23 + (k % 2) * 3, sy + 3, 24 + (k % 2) * 3, sy + 3), GOLD[5])
    # window on right wall
    lattice_window(cv, 164, 62, 182, 82, lit=False)
    # awning over shop front
    aw = m_poly(W, H, [(44, 50), (156, 50), (162, 62), (38, 62)])
    cv.fill(aw, CLOTH_BLUE[3])
    stripes = aw & (((xx - 38) // 8) % 2 == 0)
    cv.fill(stripes, PAPER_R[4])
    cv.fill(aw & (yy <= 52) & ~stripes, CLOTH_BLUE[4])
    cv.fill(aw & (yy >= 60) & ~stripes, CLOTH_BLUE[2])
    cv.fill(aw & (yy >= 60) & stripes, PAPER_R[2])
    for sx in range(38, 162, 8):
        sc = m_ellipse(W, H, sx + 4, 62.5, 4, 2.2) & (yy >= 62)
        cv.fill(sc, PAPER_R[3] if ((sx - 38) // 8) % 2 == 0 else CLOTH_BLUE[2])
    for px in (40, 158):
        cv.fill(m_line(W, H, [(px, 62), (px - (2 if px < 100 else -2), 118)]), WOOD[3])
    # roof
    roof_side(cv, 2, 197, 8, 40, "vs_roof", pal=ROOF_GREY, curl=3, thick=3, top_frac=0.4)
    eave_shadow(cv, 6, 194, 44, 3)
    # horizontal sign board under the eave
    sb = m_rect(W, H, 78, 42, 122, 49)
    shade(cv, sb, LACQUER, contour=True, R=1, base=0.4)
    cv.fill(border(sb), GOLD[3])
    for k, sx in enumerate(range(84, 118, 9)):
        cv.fill(m_rect(W, H, sx, 44, sx + 4, 44) | m_rect(W, H, sx + 2, 45, sx + 2, 47) | m_rect(W, H, sx + (k % 2) * 3, 47, sx + 1 + (k % 2) * 3, 47), GOLD[5])
    lantern(cv, 12, 45, 5, 7, lit=True, cord=2)
    lantern(cv, 187, 45, 5, 7, lit=True, cord=2)
    grass_row(cv, 2, 198, 127, "vs_g", step=12)
    outline(cv)
    glow(cv, 12, 51, 6, 6, hexc("#ffb060"), steps=((1.0, 0.14),))
    glow(cv, 187, 51, 6, 6, hexc("#ffb060"), steps=((1.0, 0.14),))
    return cv


# ------------------------------------------------------------------ herb hut
@building("herb_hut", 170, 120, roof_px=56)
def herb_hut(state, f):
    W, H = 170, 120
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ground_shadow(cv, 85, 118, 82, 1.8)
    stone_block(cv, 8, 110, 161, 117, "hh_base", course=4, joint=8, moss=0.4)
    plaster_wall(cv, 12, 48, 157, 109, pal=MUD, seed="hh_wall")
    for px in (10, 56, 100, 156):
        timber(cv, px, 46, px + 3, 110, WOOD, seed=("hhp", px))
    timber(cv, 10, 78, 159, 80, WOOD, horiz=True, seed="hh_rail")
    # door with cloth curtain
    fr = m_rect(W, H, 68, 64, 90, 109)
    shade(cv, fr, WOOD, contour=True, R=1, base=0.4)
    cv.fill(m_rect(W, H, 70, 66, 88, 109), hexc("#1a1210"))
    cur = m_poly(W, H, [(70, 66), (88, 66), (88, 92), (84, 90), (79, 93), (74, 90), (70, 92)])
    shade(cv, cur, CLOTH_JADE, contour=True, mode="cylh", base=0.5, gain=0.7)
    cv.fill(cur & ((xx - 70) % 6 == 0), CLOTH_JADE[1])
    leafm = m_poly(W, H, [(79, 72), (82, 76), (79, 81), (76, 76)])
    cv.fill(leafm, GOLD[4])
    cv.fill(m_rect(W, H, 79, 73, 79, 80), GOLD[2])
    stone_block(cv, 64, 107, 94, 109, "hh_step")
    # round moon window
    round_window(cv, 124, 72, 10, lit=True)
    # small square window on the left
    lattice_window(cv, 26, 60, 42, 74, lit=False, style="ice")
    # bench with medicine jars, mortar
    bench = m_rect(W, H, 112, 96, 152, 98)
    shade(cv, bench, WOOD, contour=True, R=1, base=0.6)
    for lx in (114, 149):
        cv.fill(m_rect(W, H, lx, 99, lx + 1, 109), WOOD[2])
    for i, (jx, pal) in enumerate(((117, POTTERY), (125, GLAZE_DARK), (133, POTTERY), (143, CLOTH_BLUE))):
        v = lathe(W, H, jx, [(88, 1.5), (89, 2.5), (91, 3.5), (95, 3.5)])
        shade(cv, v, pal, contour=True, mode="cyl", base=0.55)
        lab = m_rect(W, H, jx - 1, 91, jx + 1, 93)
        cv.fill(lab, PAPER_R[4] if i % 2 else CLOTH_RED[4])
    mort = lathe(W, H, 100, [(104, 4), (108, 3), (109, 2.5)])
    shade(cv, mort, STONE, contour=True, mode="cyl")
    cv.fill(m_line(W, H, [(101, 104), (104, 99)]), WOOD[4])
    # drying tray leaning on the wall
    tray = m_ellipse(W, H, 36, 98, 10, 10) & (yy <= 109)
    shade(cv, tray, STRAW, contour=True, R=2, base=0.5)
    cv.fill(tray & erode(erode(tray)) & ((xx + yy) % 3 == 0), STRAW[2])
    for (hx, hy, pal) in ((31, 94, LEAF), (38, 98, FOLIAGE_DRY), (34, 102, CLOTH_RED)):
        cv.fill(m_ellipse(W, H, hx, hy, 2, 1.4), pal[3])
    # roof
    thatch_roof(cv, [(1, 54), (22, 26), (50, 8), (85, 3), (120, 8), (148, 26), (169, 54), (158, 55), (85, 52),
                     (12, 55)], "hh_roof", ridge=(50, 120, 5))
    eave_shadow(cv, 12, 157, 57, 3)
    # herb bundles hanging from the eave
    hp = [LEAF, FOLIAGE_DRY, VIOLET, LEAF_BLUE, FOLIAGE_DRY, LEAF, VIOLET]
    for i, hx in enumerate(range(18, 160, 20)):
        if 64 <= hx <= 94:
            continue
        cv.fill(m_rect(W, H, hx, 55, hx, 57), ROPE[3])
        herb_bundle(cv, hx, 58, hp[i % len(hp)], ln=8 + (i % 2) * 2)
    grass_row(cv, 2, 168, 117, "hh_g", step=10)
    outline(cv)
    glow(cv, 124, 72, 12, 12, hexc("#ffb060"), steps=((1.0, 0.1),))
    return cv


# ------------------------------------------------------------------ stilt house
@building("stilt_house", 190, 150, roof_px=52, ground=12)
def stilt_house(state, f):
    W, H = 190, 150
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    wl = 138  # waterline
    # stilts (behind deck); submerged parts drawn after outline
    stilts = [14, 40, 66, 94, 122, 150, 176]
    for sx in stilts:
        m = m_rect(W, H, sx, 97, sx + 3, wl - 1)
        shade(cv, m, WOOD_GREY, contour=True, mode="cyl", base=0.45)
        cv.fill(m & (yy >= wl - 6), mix(WOOD_GREY[2], MOSS[2], 0.4))
    # cross braces
    for i in range(len(stilts) - 1):
        a, b = stilts[i] + 2, stilts[i + 1] + 1
        cv.fill(m_line(W, H, [(a, 102), (b, 124)]), WOOD_GREY[3])
        cv.fill(m_line(W, H, [(a, 124), (b, 102)]), WOOD_GREY[2])
    # house walls: woven reed
    wall = m_rect(W, H, 28, 48, 162, 91)
    nzw = vnoise(W, H, 5, seed_of("sh_w"), 2)
    shade(cv, wall, FOLIAGE_DRY, R=1, base=0.5, gain=0.5, noise=nzw, namp=0.3, ao=0.15)
    weave = wall & ((((xx // 3) + (yy // 3)) % 2) == 0)
    cv.fill(weave & (nzw > 0.35), FOLIAGE_DRY[3])
    cv.fill(wall & ((yy % 3) == 0) & weave, FOLIAGE_DRY[4])
    cv.fill(wall & ((xx % 3) == 0) & ~weave, FOLIAGE_DRY[1])
    cv.fill(wall & (yy <= 52), FOLIAGE_DRY[1])
    for px in (26, 94, 160):
        m = m_rect(W, H, px, 46, px + 3, 92)
        shade(cv, m, FOLIAGE_DRY, contour=True, mode="cyl", base=0.5)
        for ny in range(52, 92, 8):
            cv.fill(m_rect(W, H, px, ny, px + 3, ny), FOLIAGE_DRY[1])
    # reed curtain door
    fr = m_rect(W, H, 68, 58, 88, 91)
    shade(cv, fr, WOOD, contour=True, R=1, base=0.4)
    cv.fill(m_rect(W, H, 70, 60, 86, 91), hexc("#1c140f"))
    cur = m_rect(W, H, 70, 60, 86, 80) & ((xx % 2) == 0)
    cv.fill(cur, STRAW[3])
    cv.fill(cur & (yy % 4 == 0), STRAW[1])
    # window
    lattice_window(cv, 118, 60, 136, 76, lit=True)
    # deck
    deck = m_rect(W, H, 6, 92, 184, 97)
    plank_h(cv, 6, 92, 184, 97, WOOD_GREY, seed="sh_deck", base=0.5)
    cv.fill(m_rect(W, H, 6, 92, 184, 92), WOOD_GREY[5])
    for px in range(6, 185, 8):
        cv.fill(m_rect(W, H, px, 93, px, 97), WOOD_GREY[1])
    # railing
    for px in (8, 20, 32, 158, 170, 182):
        cv.fill(m_rect(W, H, px, 80, px + 1, 91), WOOD_GREY[3])
        cv.put(px, 80, WOOD_GREY[5])
    for (a, b) in ((8, 50), (150, 184)):
        cv.fill(m_rect(W, H, a, 81, b, 82), WOOD_GREY[4])
        cv.fill(m_rect(W, H, a, 82, b, 82), WOOD_GREY[2])
    # drying net on railing + fishing pole + jars
    net = m_poly(W, H, [(150, 82), (184, 82), (182, 90), (152, 91)])
    cv.fill(net & (((xx + yy) % 3 == 0) | ((xx - yy) % 3 == 0)), ROPE[3])
    cv.fill(m_line(W, H, [(40, 91), (58, 40)]), WOOD[4])
    cv.fill(m_curve(W, H, [(58, 40), (64, 50), (66, 64)]), PAPER_R[3])
    v = lathe(W, H, 110, [(84, 2), (86, 3.5), (91, 3.5)])
    shade(cv, v, POTTERY, contour=True, mode="cyl")
    # ladder down to the water
    for rx in (148, 157):
        m = m_rect(W, H, rx, 94, rx + 1, wl + 2)
        shade(cv, m, WOOD, mode="cyl", base=0.55)
    for ry in range(100, wl, 7):
        cv.fill(m_rect(W, H, 150, ry, 156, ry), WOOD[4])
        cv.fill(m_rect(W, H, 150, ry + 1, 156, ry + 1), WOOD[2])
    # roof
    thatch_roof(cv, [(10, 50), (32, 24), (62, 8), (95, 3), (128, 8), (158, 24), (180, 50), (168, 52), (95, 48),
                     (22, 52)], "sh_roof", pal=THATCH, ridge=(58, 132, 5))
    eave_shadow(cv, 28, 162, 53, 3)
    lantern(cv, 92, 51, 4, 6, lit=True, cord=3)
    outline(cv)
    # water: submerged stilt tint + ripples at waterline
    for sx in stilts:
        m = m_rect(W, H, sx - 1, wl, sx + 4, wl + 5)
        cv.fill(m & (yy <= wl + 1), WATER[4], 0.9)
        cv.fill(m & (yy > wl + 1), WATER[3], 0.6)
        cv.fill(m_rect(W, H, sx - 4, wl, sx - 2, wl) | m_rect(W, H, sx + 5, wl, sx + 7, wl), WATER[7], 0.8)
    for (x0, x1, y) in ((20, 34, wl + 3), (74, 92, wl + 2), (104, 116, wl + 4), (160, 176, wl + 3), (130, 140, wl + 6)):
        cv.fill(m_rect(W, H, x0, y, x1, y), WATER[6], 0.6)
    glow(cv, 92, 57, 6, 6, hexc("#ffb060"), steps=((1.0, 0.15),))
    glow(cv, 127, 68, 12, 10, hexc("#ffb060"), steps=((1.0, 0.08),))
    return cv


# ------------------------------------------------------------------ village house
@building("village_house", 190, 125, roof_px=46)
def village_house(state, f):
    W, H = 190, 125
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ground_shadow(cv, 95, 123, 90, 1.8)
    stone_block(cv, 6, 113, 183, 122, "vh_base", course=5, joint=12, moss=0.3)
    plaster_wall(cv, 12, 44, 178, 112, seed="vh_wall")
    # dark timber frame
    for px in (10, 62, 126, 176):
        timber(cv, px, 42, px + 3, 113, WOOD, seed=("vhp", px))
    timber(cv, 10, 44, 179, 47, WOOD, horiz=True, seed="vh_top")
    timber(cv, 10, 108, 179, 110, WOOD, horiz=True, seed="vh_sill")
    # windows
    lattice_window(cv, 28, 62, 50, 82, lit=False)
    lattice_window(cv, 140, 62, 162, 82, lit=False)
    # double door
    fr = m_rect(W, H, 80, 60, 110, 110)
    shade(cv, fr, WOOD, contour=True, R=1, base=0.35)
    for (x0, x1) in ((83, 94), (96, 107)):
        leaf = m_rect(W, H, x0, 63, x1, 110)
        shade(cv, leaf, WOOD, contour=True, R=1, base=0.5, gain=0.9)
        cv.fill(border(m_rect(W, H, x0 + 2, 66, x1 - 2, 84)), WOOD[2])
        cv.fill(border(m_rect(W, H, x0 + 2, 88, x1 - 2, 106)), WOOD[2])
        cv.fill(m_rect(W, H, x0 + 3, 67, x1 - 3, 67), WOOD[5])
    cv.put(93, 86, GOLD[4])
    cv.put(97, 86, GOLD[4])
    # red couplets (no readable text) + door god paper above
    for cx0 in (74, 113):
        cp = m_rect(W, H, cx0, 62, cx0 + 3, 100)
        cv.fill(cp, CLOTH_RED[3])
        cv.fill(right_edge(cp), CLOTH_RED[2])
        for sy in range(65, 98, 5):
            cv.fill(m_rect(W, H, cx0 + 1, sy, cx0 + 2, sy + 1), INK)
    hp = m_rect(W, H, 86, 52, 104, 57)
    cv.fill(hp, CLOTH_RED[3])
    for sx in range(88, 103, 4):
        cv.fill(m_rect(W, H, sx, 54, sx + 1, 55), INK)
    stone_block(cv, 76, 110, 114, 112, "vh_step")
    # potted plant + ivy
    pot = lathe(W, H, 124, [(102, 4), (108, 3)])
    shade(cv, pot, POTTERY, contour=True, mode="cyl")
    bush = blob_mask(W, H, 124, 97, 6, 5, "vh_bush", 0.25)
    shade(cv, bush, LEAF, contour=True, R=2, base=0.5, noise=vnoise(W, H, 2, 4), namp=0.5)
    ivy = (m_rect(W, H, 12, 48, 24, 112) & (vnoise(W, H, 2, seed_of("ivy"), 2) > 0.58)) | \
          (m_rect(W, H, 12, 48, 16, 60) & (vnoise(W, H, 2, seed_of("ivy2")) > 0.45))
    cv.fill(ivy, LEAF[3])
    cv.fill(ivy & ~shift(ivy, 0, 1), LEAF[4])
    cv.fill(ivy & ~shift(ivy, 0, -1), LEAF[1])
    # roof
    roof_side(cv, 2, 187, 8, 40, "vh_roof", pal=ROOF_GREY, curl=3, thick=3, top_frac=0.42)
    eave_shadow(cv, 12, 178, 44, 3)
    lantern(cv, 95, 44, 5, 7, lit=True, cord=2)
    grass_row(cv, 2, 188, 122, "vh_g", step=11)
    outline(cv)
    glow(cv, 95, 50, 6, 6, hexc("#ffb060"), steps=((1.0, 0.14),))
    return cv


# ------------------------------------------------------------------ watch tower
@building("watch_tower", 90, 190, roof_px=34)
def watch_tower(state, f):
    W, H = 90, 190
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ground_shadow(cv, 45, 188, 42, 1.8)
    # legs (splayed)
    legs = [((10, 186), (20, 60)), ((76, 186), (66, 60))]
    for (a, b) in legs:
        m = m_line(W, H, [a, b], 4)
        shade(cv, m, WOOD, contour=True, R=2, base=0.5, gain=1.0)
    # back legs (darker, thinner)
    for (a, b) in (((28, 186), (32, 60)), ((60, 186), (56, 60))):
        m = m_line(W, H, [a, b], 3)
        shade(cv, m, WOOD, contour=True, R=1, base=0.3, gain=0.6)
    # cross braces between front legs
    def legx(side, y):
        (ax, ay), (bx, by) = legs[side]
        t = (y - ay) / (by - ay)
        return ax + (bx - ax) * t
    levels = [182, 150, 118, 88, 62]
    for i in range(len(levels) - 1):
        y0, y1 = levels[i], levels[i + 1]
        m = m_line(W, H, [(legx(0, y0) + 2, y0), (legx(1, y1) - 2, y1)], 2)
        m |= m_line(W, H, [(legx(1, y0) - 2, y0), (legx(0, y1) + 2, y1)], 2)
        shade(cv, m, WOOD_GREY, contour=True, R=1, base=0.5)
        hb = m_rect(W, H, int(legx(0, y1)), y1, int(legx(1, y1)), y1 + 2)
        shade(cv, hb, WOOD, contour=True, R=1, base=0.55)
        for x in (int(legx(0, y1)) + 1, int(legx(1, y1)) - 1):
            rope_band(cv, x - 1, x + 1, y1 + 3)
    # ladder up the middle
    for rx in (38, 50):
        m = m_rect(W, H, rx, 60, rx + 1, 186)
        shade(cv, m, WOOD, mode="cyl", base=0.6)
    for ry in range(66, 186, 7):
        cv.fill(m_rect(W, H, 40, ry, 49, ry), WOOD[4])
        cv.fill(m_rect(W, H, 40, ry + 1, 49, ry + 1), WOOD[2])
    # stone footings
    for fx in (10, 76, 28, 60):
        stone_block(cv, fx - 5, 182, fx + 5, 187, ("wt_f", fx))
    # watch cabin: back wall, platform, railing
    cab = m_rect(W, H, 14, 34, 75, 56)
    plank_wall(cv, 14, 34, 75, 56, WOOD_GREY, seed="wt_cab", pw=4)
    # signal drum & bell inside
    drum = m_ellipse(W, H, 30, 47, 5, 5)
    shade(cv, drum, CLOTH_RED, contour=True, mode="sphere", base=0.5)
    cv.fill(m_ellipse(W, H, 30, 47, 3, 3), PAPER_R[3])
    bell = lathe(W, H, 58, [(38, 1.5), (40, 3), (45, 4)])
    shade(cv, bell, BRONZE, contour=True, mode="cyl", base=0.6)
    cv.fill(m_rect(W, H, 58, 35, 58, 37), ROPE[2])
    plat = m_rect(W, H, 6, 56, 83, 61)
    plank_h(cv, 6, 56, 83, 61, WOOD, seed="wt_plat", base=0.5)
    cv.fill(m_rect(W, H, 6, 56, 83, 56), WOOD[5])
    for px in range(6, 84, 9):
        cv.fill(m_rect(W, H, px, 44, px + 1, 55), WOOD[3])
        cv.put(px, 44, WOOD[5])
    for ry in (44, 50):
        cv.fill(m_rect(W, H, 6, ry, 84, ry + 1), WOOD[4])
        cv.fill(m_rect(W, H, 6, ry + 1, 84, ry + 1), WOOD[2])
    for px in (8, 78):
        timber(cv, px, 28, px + 3, 56, WOOD, seed=("wtc", px))
    # cap roof
    roof_side(cv, 2, 87, 10, 29, "wt_roof", pal=ROOF, curl=3, thick=2, top_frac=0.22)
    # goal pennant on top
    cv.fill(m_rect(W, H, 44, 0, 45, 9), WOOD[4])
    pen = m_poly(W, H, [(46, 0), (58, 2), (54, 4), (58, 6), (46, 7)])
    shade(cv, pen, CLOTH_RED, contour=True, R=1, base=0.55)
    cv.fill(top_edge(pen), CLOTH_RED[5])
    lantern(cv, 12, 31, 4, 6, lit=True, cord=1)
    lantern(cv, 77, 31, 4, 6, lit=True, cord=1)
    outline(cv)
    glow(cv, 12, 36, 5, 5, hexc("#ffb060"), steps=((1.0, 0.15),))
    glow(cv, 77, 36, 5, 5, hexc("#ffb060"), steps=((1.0, 0.15),))
    return cv


# ------------------------------------------------------------------ stockade wall
@building("stockade_wall", 160, 80, roof_px=12)
def stockade_wall(state, f):
    W, H = 160, 80
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ground_shadow(cv, 80, 78, 78, 1.6)
    g = rng("stockade")
    x = 0
    logs = []
    while x < W:
        w = int(g.integers(6, 9))
        if not (52 <= x + w // 2 <= 108):
            top = int(g.integers(4, 9))
            logs.append((x, x + w - 1, top))
        x += w
    for (x0, x1, top) in logs:
        cxm = (x0 + x1) / 2
        m = m_poly(W, H, [(x0, 77), (x0, top + 4), (cxm, top), (x1, top + 4), (x1, 77)])
        nz = vnoise(W, H, 2, seed_of("log", x0), 2)
        shade(cv, m, WOOD, contour=True, mode="cyl", base=0.5, gain=1.1, noise=nz, namp=0.3)
        cut = m & (yy <= top + 3)
        cv.fill(cut & (xx <= cxm), WOOD[5])
        cv.fill(cut & (xx > cxm), WOOD[4])
        bark = m & erode(m) & (nz > 0.6) & (yy > top + 6)
        cv.fill(bark, WOOD[2])
    for ry in (22, 58):
        for (x0, x1, top) in logs:
            rope_band(cv, x0, x1, ry)
            rope_band(cv, x0, x1, ry + 1)
    # gate posts + crossbeam
    for px in (50, 104):
        m = m_rect(W, H, px, 0, px + 5, 77)
        shade(cv, m, WOOD, contour=True, mode="cyl", base=0.45)
        cv.fill(m_poly(W, H, [(px, 3), (px + 2.5, 0), (px + 5, 3)]) & m, WOOD[5])
    beam = m_rect(W, H, 46, 8, 113, 12)
    shade(cv, beam, WOOD, contour=True, R=1, base=0.5)
    # gate doors (log leaves with braces)
    for (x0, x1) in ((56, 79), (81, 103)):
        for lx in range(x0, x1, 4):
            m = m_rect(W, H, lx, 14, min(x1, lx + 3), 77)
            shade(cv, m, WOOD, contour=True, mode="cyl", base=0.42)
        for by in (24, 62):
            b = m_rect(W, H, x0, by, x1, by + 2)
            shade(cv, b, WOOD_GREY, contour=True, R=1, base=0.55)
        br = m_line(W, H, [(x0 + 1, 61), (x1 - 1, 27)], 2)
        shade(cv, br, WOOD_GREY, contour=True, R=1, base=0.5)
    cv.fill(m_rect(W, H, 80, 14, 80, 77), INK)
    # bar across the gate
    bar = m_rect(W, H, 60, 42, 99, 44)
    shade(cv, bar, WOOD, contour=True, R=1, base=0.6)
    for bx in (64, 95):
        cv.fill(m_rect(W, H, bx, 41, bx + 1, 45), IRON[4])
    # tattered bandit flag on the left post + skull
    cv.fill(m_rect(W, H, 52, 0, 52, 0), WOOD[4])
    flag = m_poly(W, H, [(56, 13), (70, 13), (68, 18), (70, 22), (63, 20), (56, 24)])
    shade(cv, flag, CLOTH_RED, contour=True, R=1, base=0.4)
    sk = m_ellipse(W, H, 80, 4.5, 3, 2.6)
    shade(cv, sk, BONE, contour=True, mode="sphere", base=0.55)
    cv.put(79, 4, INK)
    cv.put(81, 4, INK)
    cv.fill(m_line(W, H, [(76, 3), (73, 1)]) | m_line(W, H, [(84, 3), (87, 1)]), BONE[3])
    grass_row(cv, 0, 158, 77, "st_g", step=8)
    outline(cv)
    return cv


# ------------------------------------------------------------------ warehouse
@building("warehouse", 220, 130, roof_px=46)
def warehouse(state, f):
    W, H = 220, 130
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ground_shadow(cv, 110, 128, 106, 1.8)
    stone_block(cv, 6, 119, 213, 127, "wh_base", course=4, joint=13, moss=0.3)
    plank_wall(cv, 10, 44, 209, 118, WOOD, seed="wh_wall", pw=5)
    for px in (8, 72, 146, 208):
        timber(cv, px, 42, px + 3, 119, WOOD, seed=("whp", px))
    timber(cv, 8, 44, 211, 47, WOOD, horiz=True, seed="wh_top")
    timber(cv, 8, 84, 72, 86, WOOD, horiz=True, seed="wh_mid1")
    timber(cv, 146, 84, 211, 86, WOOD, horiz=True, seed="wh_mid2")
    # vents
    for vx in (30, 176):
        v = m_rect(W, H, vx, 54, vx + 16, 62)
        shade(cv, v, WOOD, contour=True, R=1, base=0.4)
        cv.fill(m_rect(W, H, vx + 2, 56, vx + 14, 60), INK)
        cv.fill(m_rect(W, H, vx + 2, 56, vx + 14, 60) & ((xx - vx) % 3 == 0), WOOD[3])
    # big double doors
    fr = m_rect(W, H, 80, 56, 140, 118)
    shade(cv, fr, WOOD, contour=True, R=1, base=0.3)
    for (x0, x1) in ((83, 109), (111, 137)):
        plank_wall(cv, x0, 59, x1, 118, WOOD_GREY, seed=("whd", x0), pw=4)
        for sy in (66, 88, 110):
            cv.fill(m_rect(W, H, x0, sy, x1, sy + 2), IRON[3])
            cv.fill(m_rect(W, H, x0, sy, x1, sy), IRON[5])
            for nx in range(x0 + 2, x1, 5):
                cv.put(nx, sy + 1, IRON[6])
        br = m_line(W, H, [(x0 + 1, 87), (x1 - 1, 69)], 2)
        shade(cv, br, WOOD_GREY, contour=True, R=1, base=0.55)
    cv.fill(m_rect(W, H, 110, 59, 110, 118), INK)
    for rx in (106, 114):
        ring = m_ellipse(W, H, rx, 97, 2, 2) & ~m_ellipse(W, H, rx, 97, 1, 1)
        cv.fill(ring, IRON[5])
    # plaque above doors
    pl = m_rect(W, H, 94, 48, 126, 54)
    shade(cv, pl, LACQUER, contour=True, R=1, base=0.4)
    cv.fill(border(pl), GOLD[3])
    for sx in range(98, 124, 7):
        cv.fill(m_rect(W, H, sx, 50, sx + 3, 50) | m_rect(W, H, sx + 1, 51, sx + 1, 52), GOLD[5])
    # loading beam with pulley and hook
    lb = m_rect(W, H, 140, 48, 160, 51)
    shade(cv, lb, WOOD, contour=True, R=1, base=0.55)
    pul = m_ellipse(W, H, 157, 54, 2.5, 2.5)
    shade(cv, pul, IRON, contour=True, mode="sphere")
    cv.fill(m_rect(W, H, 159, 54, 159, 76), ROPE[3])
    cv.fill(m_rect(W, H, 155, 54, 155, 66), ROPE[2])
    cv.fill(m_curve(W, H, [(159, 76), (161, 79), (159, 81), (157, 79)]), IRON[4])
    # stacked crates (left) and barrels + sacks (right)
    crate_box(cv, 16, 102, 16, WOOD, "c1")
    crate_box(cv, 33, 106, 12, WOOD, "c2")
    crate_box(cv, 20, 88, 14, WOOD, "c3")
    crate_box(cv, 47, 104, 14, WOOD, "c4")
    barrel(cv, 158, 118, 6, 16)
    barrel(cv, 171, 118, 6, 16)
    barrel(cv, 164, 102, 5, 12)
    for i, sx in enumerate((186, 195, 204, 190, 199)):
        sack(cv, sx, 118 if i < 3 else 108, 8, 10)
    # roof
    roof_side(cv, 2, 217, 10, 40, "wh_roof", pal=ROOF_GREY, curl=3, thick=3, top_frac=0.45)
    eave_shadow(cv, 10, 209, 44, 3)
    grass_row(cv, 2, 218, 127, "wh_g", step=12)
    outline(cv)
    return cv
