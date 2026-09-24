"""Herb patches, ore veins, springs, water decor and other natural props."""
from __future__ import annotations

import math

import numpy as np

from palette import *  # noqa: F401,F403
from parts import (blob_mask, crack_lines, fern, grass_tuft, ground_shadow, herb_sparkle, moss_top, motes, rock,
                   soil_mound, wisp)
from pixlib import (Canvas, bbox, border, bottom_edge, depth_from_top, dilate, erode, glow, grid, hexc, left_edge,
                    m_curve, m_ellipse, m_line, m_poly, m_rect, mix, outline, right_edge, rng, seed_of, shade,
                    shift, sparkle, top_edge, vnoise)
from registry import prop

HERB_STATES = (("ready", 3, 5), ("depleted", 1, 0))


def leaf(cv, x, y, dx, dy, length, pal=LEAF, width=1.0, light=None):
    """Pointed leaf from (x,y) along direction (dx,dy)."""
    n = math.hypot(dx, dy) or 1
    ux, uy = dx / n, dy / n
    px, py = -uy, ux
    tip = (x + ux * length, y + uy * length)
    mid = (x + ux * length * 0.45, y + uy * length * 0.45)
    pts = [(x, y), (mid[0] + px * width, mid[1] + py * width), tip, (mid[0] - px * width, mid[1] - py * width)]
    m = m_poly(cv.w, cv.h, pts)
    lit = light if light is not None else (ux < 0.2 and uy < 0.5)
    cv.fill(m, pal[3] if lit else pal[2])
    # midrib highlight on the upper side
    rib = m_line(cv.w, cv.h, [(round(x + ux), round(y + uy)), (round(mid[0]), round(mid[1]))]) & m
    cv.fill(rib, pal[4] if lit else pal[3])
    return m


def stem(cv, pts, c, curve=True):
    m = m_curve(cv.w, cv.h, pts) if curve and len(pts) > 2 else m_line(cv.w, cv.h, pts)
    cv.fill(m, c)
    return m


def cut_stems(cv, spots, pal=LEAF, h=2):
    for (x, y) in spots:
        cv.fill(m_rect(cv.w, cv.h, x, y - h + 1, x, y), pal[2])
        cv.put(x, y - h + 1, FOLIAGE_DRY[4])


# ------------------------------------------------------------------ herb patches
@prop("willow_moss_patch", 28, 14, states=HERB_STATES)
def willow_moss_patch(state, f):
    cv = Canvas(28, 14)
    W, H = 28, 14
    ground_shadow(cv, 14, 12, 13, 1.4)
    m = rock(cv, 14, 11, 11, 5, "wm_rock", pal=STONE, moss=0.0, R=2, base=0.45)
    rock(cv, 22, 11, 4, 3, "wm_rock2", pal=STONE, R=1, base=0.5)
    xx, yy = grid(W, H)
    if state == "ready":
        pad = blob_mask(W, H, 13, 7, 10, 3.2, "wm_pad", 0.18) & (yy <= 8)
        shade(cv, pad, MOSS, R=2, base=0.55, gain=1.3, noise=vnoise(W, H, 2, 7), namp=0.4)
        # drooping willow strands
        g = rng("wm_strand")
        for i, sx in enumerate((5, 7, 10, 13, 14, 17, 20, 22)):
            ln = int(g.integers(1, 5))
            sy = 8 + int(g.integers(0, 2))
            c = FOLIAGE_DRY[4] if i % 3 == 0 else MOSS[3]
            drift = 1 if i % 2 else -1
            pts = [(sx, sy), (sx, sy + ln // 2), (sx + (drift if ln > 2 else 0), min(H - 3, sy + ln))]
            cv.fill(m_line(W, H, pts), c)
            cv.put(pts[-1][0], pts[-1][1], MOSS[1])
        for i, (tx, ty) in enumerate(((7, 4), (11, 3), (15, 4), (19, 5))):
            cv.put(tx, ty, MOSS[5])
        grass_tuft(cv, 3, 11, "wm_g", h=3, n=2, pal=LEAF)
    else:
        pad = blob_mask(W, H, 13, 8, 9, 2.0, "wm_pad2", 0.3) & (yy <= 8) & (vnoise(W, H, 2, 9) > 0.45)
        cv.fill(pad, MOSS[1])
        cut_stems(cv, [(8, 7), (12, 6), (16, 7), (19, 8)], pal=MOSS, h=1)
    outline(cv)
    if state == "ready":
        herb_sparkle(cv, f, [(9, 3), (17, 3), (13, 2)])
    return cv


@prop("riverreed_ginseng_patch", 24, 20, states=HERB_STATES)
def riverreed_ginseng(state, f):
    cv = Canvas(24, 20)
    W, H = 24, 20
    ground_shadow(cv, 12, 18, 11, 1.4)
    # reeds behind
    for i, (rx, top, lean) in enumerate(((3, 7, -2), (5, 5, -1), (19, 6, 1), (21, 9, 2))):
        stem(cv, [(rx, 17), (rx + lean * 0.3, (17 + top) / 2), (rx + lean, top)], LEAF_BLUE[3 if i % 2 else 2])
    for (rx, top) in ((5, 5),):
        cv.fill(m_rect(W, H, rx - 1, top - 3, rx - 1, top), WOOD[3])
        cv.put(rx - 1, top - 3, WOOD[5])
    soil_mound(cv, 12, 17, 10, 3.5, "gs_soil", pal=EARTH, moss=0.3)
    if state == "ready":
        # pale root peeking out
        root = m_poly(W, H, [(10, 14), (14, 14), (13, 16), (12, 17), (11, 16)])
        shade(cv, root, FLESH_ROOT, R=1, base=0.55)
        cv.put(9, 16, FLESH_ROOT[2])
        cv.put(15, 16, FLESH_ROOT[2])
        stem(cv, [(12, 14), (12, 9), (12, 4)], LEAF[2], curve=False)
        # palmate leaf groups
        for (bx, by, side) in ((12, 10, -1), (12, 10, 1), (12, 7, -1), (12, 7, 1)):
            for k, ang in enumerate((-0.9, -0.35, 0.2)):
                a = ang + (0.25 if by == 7 else 0)
                leaf(cv, bx, by, side * math.cos(a), math.sin(a) - 0.2, 5 - k % 2, LEAF, 1.0,
                     light=(side < 0))
        # berry cluster
        for (bx, by) in ((11, 3), (12, 2), (13, 3), (12, 4), (11, 4), (13, 4)):
            cv.put(bx, by, CLOTH_RED[4])
        cv.put(11, 3, hexc("#ff9a7a"))
        cv.put(12, 2, hexc("#ffb49a"))
    else:
        hole = m_ellipse(W, H, 12, 15, 2.5, 1.2)
        cv.fill(hole, EARTH[0])
        cut_stems(cv, [(12, 14)], h=2)
        leaf(cv, 13, 16, 1, 0.1, 4, FOLIAGE_DRY, 0.8)
    outline(cv)
    if state == "ready":
        herb_sparkle(cv, f, [(14, 1), (7, 7), (17, 6)])
    return cv


@prop("ember_pepper_bush", 28, 24, states=HERB_STATES)
def ember_pepper_bush(state, f):
    cv = Canvas(28, 24)
    W, H = 28, 24
    ground_shadow(cv, 14, 22, 12, 1.4)
    soil_mound(cv, 14, 21, 11, 2.5, "ep_soil")
    xx, yy = grid(W, H)
    if state == "ready":
        # woody stems
        for pts in (((14, 20), (13, 14), (9, 9)), ((14, 20), (15, 13), (19, 8)), ((14, 20), (14, 10))):
            stem(cv, list(pts), WOOD[2])
        bush = (blob_mask(W, H, 14, 12, 11, 7.5, "ep_bush", 0.22) | blob_mask(W, H, 8, 15, 5, 4, "ep_b2", 0.2)
                | blob_mask(W, H, 20, 14, 5.5, 4.5, "ep_b3", 0.2)) & (yy <= 19)
        nz = vnoise(W, H, 2, seed_of("ep_leaf"), 2)
        shade(cv, bush, LEAF, contour=True, R=3, base=0.5, gain=1.6, noise=nz, namp=0.55)
        # leaf-cluster notches along silhouette
        for (lx, ly) in ((5, 12), (9, 6), (15, 5), (21, 8), (24, 12)):
            cv.put(lx, ly, LEAF[4])
        # peppers
        pep = [(8, 12), (12, 9), (17, 10), (20, 14), (11, 15), (15, 15), (6, 16), (22, 11), (18, 6)]
        for i, (px, py) in enumerate(pep):
            ln = 3 if i % 3 else 2
            body = m_rect(W, H, px, py, px + 1, py + ln - 1)
            body[py + ln - 1, px + 1] = False
            cv.fill(body, FIRE[1] if i % 2 else CLOTH_RED[4])
            cv.put(px, py, FIRE[3])
            cv.put(px + 1, py - 1, LEAF[3])
    else:
        for pts in (((14, 20), (12, 15), (10, 14)), ((14, 20), (16, 16), (18, 15)), ((14, 20), (14, 15))):
            stem(cv, list(pts), WOOD[3])
        for (lx, ly, dx) in ((10, 14, -1), (18, 15, 1), (14, 15, 0.3)):
            leaf(cv, lx, ly, dx, -0.6, 3, LEAF, 0.8)
        cut_stems(cv, [(10, 14), (18, 15), (14, 15)], pal=WOOD, h=1)
    outline(cv)
    if state == "ready":
        herb_sparkle(cv, f, [(9, 11), (19, 13), (13, 8)], c1=hexc("#ffcf7a"))
    return cv


@prop("mist_lotus_patch", 32, 12, states=HERB_STATES, ground=3)
def mist_lotus(state, f):
    cv = Canvas(32, 12)
    W, H = 32, 12
    xx, yy = grid(W, H)
    # water ring under the pads
    ring = m_ellipse(W, H, 16, 9.5, 15, 2.3)
    cv.fill(ring, WATER[3], 0.55)
    cv.fill(ring & (yy == 9) & ((xx % 5) < 2), WATER[6], 0.6)

    def pad(cx, cy, rx, ry, notch):
        pm = m_ellipse(W, H, cx, cy, rx, ry)
        pm &= ~m_poly(W, H, [(cx, cy), (cx + notch * rx * 1.2, cy - ry * 0.9), (cx + notch * rx * 1.2, cy - ry * 0.2)])
        shade(cv, pm, LEAF_BLUE, contour=True, R=2, base=0.55, gain=1.2)
        cv.fill(m_line(W, H, [(round(cx), round(cy)), (round(cx - notch * rx * 0.7), round(cy))]) & pm, LEAF_BLUE[3])
        return pm
    pad(9, 9, 7, 2.2, 1)
    pad(23, 9, 6.5, 2, -1)
    pad(16, 10, 5, 1.6, 1)
    if state == "ready":
        # lotus flower
        petals = [((14, 8), (12, 3), (15, 6)), ((18, 8), (20, 3), (17, 6)), ((15, 8), (16, 1), (17, 8)),
                  ((13, 9), (10, 6), (14, 7)), ((19, 9), (22, 6), (18, 7))]
        cols = [PAPER_R[4], PAPER_R[3], PAPER_R[5], hexc("#e7b9c4"), hexc("#d99aac")]
        for pts, c in zip(petals, cols):
            pm = m_poly(W, H, list(pts))
            cv.fill(pm, c)
        cv.fill(m_rect(W, H, 15, 6, 17, 7), GOLD[4])
        cv.put(16, 1, hexc("#f2c6cf"))
        cv.put(12, 3, hexc("#f2c6cf"))
        cv.put(20, 3, hexc("#f2c6cf"))
    else:
        cut_stems(cv, [(16, 8)], pal=LEAF_BLUE, h=2)
    outline(cv, skip=ring & ~dilate(cv.solid, diag=True))
    if state == "ready":
        # thin drifting mist
        for i in range(3):
            y = 5 + i * 2 - (f % 3 == i)
            x0 = 4 + ((f + i) * 3) % 6
            cv.fill(m_rect(W, H, x0, y, x0 + 3, y) & ~cv.solid, MIST_BLUE, 0.35)
            cv.fill(m_rect(W, H, x0 + 18, y + 1, x0 + 21, y + 1) & ~cv.solid, MIST_BLUE, 0.3)
        herb_sparkle(cv, f, [(16, 1), (11, 5), (21, 4)])
    return cv


@prop("cloudtop_orchid_patch", 24, 22, states=HERB_STATES)
def cloudtop_orchid(state, f):
    cv = Canvas(24, 22)
    W, H = 24, 22
    ground_shadow(cv, 12, 20, 11, 1.4)
    rock(cv, 12, 19, 9, 4, "co_rock", pal=STONE, moss=0.35, R=2)
    rock(cv, 19, 19, 4, 2.5, "co_rock2", pal=STONE, R=1)
    # strap leaves
    for (x0, y0, x1, y1, x2, y2) in ((11, 16, 6, 11, 2, 13), (13, 16, 18, 10, 22, 12), (12, 16, 10, 10, 8, 8),
                                     (12, 16, 16, 12, 20, 16), (11, 16, 7, 14, 4, 17)):
        a = m_curve(W, H, [(x0, y0), (x1, y1), (x2, y2)])
        b = m_curve(W, H, [(x0, y0 + 1), (x1, y1 + 1.4), ((x2 + x1) / 2, (y2 + y1) / 2 + 1)])
        lm = a | b
        cv.fill(lm, LEAF_BLUE[2])
        cv.fill(a & ~b, LEAF_BLUE[4])
        cv.fill(b & ~a, LEAF_BLUE[1])
    if state == "ready":
        for spray in (((12, 14), (13, 8), (16, 3)), ((12, 14), (10, 9), (6, 5))):
            stem(cv, list(spray), LEAF[3])
        for (bx, by) in ((16, 3), (13, 6), (7, 5), (9, 8), (18, 6)):
            petals = m_rect(W, H, bx - 1, by - 1, bx + 1, by + 1)
            petals[by - 1, bx - 1] = petals[by - 1, bx + 1] = False
            cv.fill(petals, CLOTH_WHITE[4])
            cv.put(bx - 1, by, CLOTH_WHITE[5])
            cv.put(bx, by - 1, CLOTH_WHITE[5])
            cv.put(bx + 1, by + 1, CLOTH_WHITE[2])
            cv.put(bx - 1, by + 1, CLOTH_WHITE[3])
            cv.put(bx, by, hexc("#8fb6d6"))
            cv.put(bx, by + 1, GOLD[4])
    else:
        cut_stems(cv, [(12, 14), (11, 14)], pal=LEAF, h=3)
    outline(cv)
    if state == "ready":
        herb_sparkle(cv, f, [(17, 2), (6, 4), (13, 6)], c1=MIST_BLUE)
    return cv


@prop("soulbell_flower_patch", 24, 22, states=HERB_STATES)
def soulbell(state, f):
    cv = Canvas(24, 22)
    W, H = 24, 22
    ground_shadow(cv, 12, 20, 10, 1.4)
    soil_mound(cv, 12, 19, 9, 2.5, "sb_soil", pal=EARTH, moss=0.4)
    for (lx, ly, dx, dy) in ((9, 18, -1, -0.4), (15, 18, 1, -0.5), (11, 18, -0.3, -1), (13, 18, 0.5, -1)):
        leaf(cv, lx, ly, dx, dy, 5, LEAF, 1.1)
    if state == "ready":
        arcs = (((11, 17), (9, 8), (5, 6), (4, 9)), ((12, 17), (13, 6), (17, 3), (19, 6)),
                ((12, 17), (15, 10), (19, 9), (20, 12)))
        for a in arcs:
            stem(cv, list(a), LEAF[2])
        for (bx, by) in ((4, 10), (19, 7), (20, 13), (8, 7), (15, 4)):
            bell = m_poly(W, H, [(bx - 1, by), (bx + 1, by), (bx + 2, by + 3), (bx - 2, by + 3)])
            shade(cv, bell, VIOLET, R=1, base=0.55, gain=1.3)
            cv.put(bx, by + 4, VIOLET[5])
            cv.put(bx - 1, by + 1, VIOLET[5])
    else:
        cut_stems(cv, [(11, 17), (12, 16), (13, 17)], h=2)
    outline(cv)
    if state == "ready":
        glow(cv, 12, 9, 10, 7, SOUL_VIOLET, steps=((1.0, 0.07 + 0.03 * (f % 2)),))
        herb_sparkle(cv, f, [(5, 13), (19, 10), (15, 3)], c1=VIOLET[5], c2=hexc("#ffffff"))
    return cv


# ------------------------------------------------------------------ ore veins
ORES = {
    "copper_vein": dict(stone=STONE_WARM, ore=COPPER, accent=VERDIGRIS, kind="metal"),
    "riverstone_vein": dict(stone=STONE, ore=RIVERSTONE, accent=MIST_BLUE, kind="pebble"),
    "jadeiron_vein": dict(stone=STONE, ore=JADE_R, accent=BRIGHT_JADE, kind="metal"),
    "spirit_shard_vein": dict(stone=STONE_DARK, ore=SHARD, accent=QI_CYAN, kind="crystal"),
    "cloudsteel_vein": dict(stone=STONE, ore=CLOUDSTEEL, accent=PAPER, kind="metal"),
    "mystic_vein": dict(stone=STONE_DARK, ore=MYSTIC, accent=SOUL_VIOLET, kind="crystal"),
}


def _crack_path(g, x, y, steps, dx_bias):
    pts = [(x, y)]
    for _ in range(steps):
        x += dx_bias + int(g.integers(-1, 2))
        y += 1 if g.random() < 0.75 else 0
        pts.append((x, y))
    return pts


def crystal(cv, x, by, hgt, lean, pal, wide=2):
    """Small prism crystal standing on (x, by), leaning by `lean` px over its height."""
    W, H = cv.w, cv.h
    tip = (x + lean + (wide - 1) / 2, by - hgt)
    cm = m_poly(W, H, [(x, by), (x + wide - 1, by), (x + wide - 1 + lean, by - hgt + 1), tip,
                       (x + lean, by - hgt + 1)])
    cv.fill(cm, pal[2])
    cv.fill(cm & left_edge(cm), pal[4])
    cv.fill(cm & right_edge(cm) & ~left_edge(cm), pal[1])
    cv.put(round(tip[0]), round(tip[1]), pal[5])
    return cm


def ore_vein(pid, state):
    spec = ORES[pid]
    W, H = 36, 28
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    st, ore, kind = spec["stone"], spec["ore"], spec["kind"]
    by = 25
    ground_shadow(cv, 18, 26, 17, 1.6)
    if state == "depleted":
        m = rock(cv, 17, by, 11, 5, (pid, "stump"), pal=st, moss=0.2, R=2, base=0.5, facets=2)
        x0, y0, x1, y1 = bbox(m)
        top = m & (yy <= y0 + 1)
        cv.fill(top, st[5])
        cv.fill(top_edge(m) & ~top, st[4])
        for i, (rx, rr, rh) in enumerate(((5, 3, 2.2), (29, 4, 3), (24, 2.2, 1.6), (10, 2, 1.4), (33, 2, 1.4))):
            rock(cv, rx, by, rr, rh, (pid, "deb", i), pal=st, R=1, base=0.52, facets=1)
        cv.put(14, by - 3, ore[2])
        cv.put(21, by - 2, ore[1])
        cv.put(28, by - 2, ore[2])
        grass_tuft(cv, 2, by, (pid, "g1"), h=3, n=2)
        outline(cv)
        return cv
    cracked = state == "cracked"
    m = rock(cv, 18, by, 14, 10.5, (pid, "main"), pal=st, moss=0.0, R=3, base=0.55, rough=0.12, facets=3)
    rock(cv, 5, by, 4, 3, (pid, "s1"), pal=st, R=1, facets=1)
    rock(cv, 31, by, 4.5, 3.5, (pid, "s2"), pal=st, R=1, facets=1)
    inner = erode(erode(m))
    g = rng("vein", pid)
    starts = [(11, 8, 1), (20, 7, 0), (25, 12, -1)] + ([(15, 14, 1)] if cracked else [])
    nug_spots = []
    for i, (sx, sy, bias) in enumerate(starts):
        pts = _crack_path(g, sx, sy, 9 if cracked else 7, bias * 0.4)
        pm = m_line(W, H, pts) & inner
        if cracked:
            pm |= shift(pm, 1, 0) & inner & (vnoise(W, H, 2, seed_of(pid, i)) > 0.5)
        cv.fill(pm, st[0])
        side = shift(pm, 1, 0) & inner & ~pm
        runs = side & (vnoise(W, H, 2, seed_of(pid, "run", i)) > (0.35 if cracked else 0.5))
        cv.fill(runs, ore[2])
        cv.fill(runs & ~shift(runs, 0, 1), ore[3])
        lip = shift(pm, -1, 0) & inner & ~pm & ~side
        cv.fill(lip, st[5])
        nug_spots.append(pts[len(pts) // 2])
        nug_spots.append(pts[-2])
    for i, (nx, ny) in enumerate(nug_spots[: (6 if cracked else 4)]):
        nx, ny = int(round(nx)) + 1, int(round(ny))
        if not inner[min(H - 1, ny), min(W - 1, nx)]:
            continue
        if kind == "crystal":
            crystal(cv, nx - 1, ny + 1, 3 + (i % 2) + (1 if cracked else 0), (-1) ** i, ore)
        elif kind == "pebble":
            pm = m_ellipse(W, H, nx, ny, 1.7 + (0.5 if cracked else 0), 1.3)
            shade(cv, pm, ore, mode="sphere", base=0.5, gain=1.1)
            cv.put(nx - 1, ny - 1, ore[5])
        else:
            pm = m_rect(W, H, nx - 1, ny - 1, nx + (1 if cracked else 0), ny)
            cv.fill(pm, ore[2])
            cv.put(nx - 1, ny - 1, ore[4])
            cv.put(nx + (1 if cracked else 0), ny, ore[1])
            if pid == "copper_vein":
                cv.put(nx - 1, ny + 1, VERDIGRIS[2])
    if kind == "crystal":
        crystal(cv, 8, 15, 5 if cracked else 3, -2, ore, wide=2)
        if cracked:
            x0, y0, x1, y1 = bbox(m)
            crystal(cv, 16, y0 + 5, 6, 1, ore, wide=3)
    if cracked:
        # fresh broken face on the upper right
        x0, y0, x1, y1 = bbox(m)
        cut = m_poly(W, H, [(21, y0 - 1), (x1 + 2, y0 - 1), (x1 + 2, y0 + 7), (27, y0 + 5)])
        face = m & shift(cut, -1, 1) & ~cut
        cv.erase(cut & m)
        cv.fill(face, st[5])
        cv.fill(face & shift(face, 1, 0) & shift(face, 0, 1), st[4])
        for i, (rx, rr) in enumerate(((27, 2.2), (9, 1.8), (24, 1.4))):
            rock(cv, rx, by, rr, rr * 0.8, (pid, "dbr", i), pal=st, R=1, facets=0)
    else:
        moss_top(cv, m, (pid, "moss"), 0.3)
    grass_tuft(cv, 2, by, (pid, "g1"), h=4, n=3)
    grass_tuft(cv, 34, by, (pid, "g2"), h=3, n=2)
    outline(cv)
    return cv


def _reg_ore(pid):
    @prop(pid, 36, 28, states=(("full", 1, 0), ("cracked", 1, 0), ("depleted", 1, 0)))
    def _d(state, f, _pid=pid):
        return ore_vein(_pid, state)
    return _d


for _pid in ORES:
    _reg_ore(_pid)


# ------------------------------------------------------------------ springs, water decor
@prop("qi_spring", 64, 24, states=(("dormant", 1, 0), ("active", 4, 6)))
def qi_spring(state, f):
    W, H = 64, 24
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    active = state == "active"
    ground_shadow(cv, 32, 22, 31, 1.6)
    # back rim stones
    for i, (x, rx, ry) in enumerate(((14, 5, 3.5), (23, 5, 3), (32, 6, 3.2), (41, 5, 3), (50, 5, 3.5))):
        rock(cv, x, 12, rx, ry, ("qs_back", i), pal=STONE, moss=0.45, R=2, facets=1, base=0.5)
    # pool
    pool = m_ellipse(W, H, 32, 15, 24, 5.2)
    wp = JADE_R if active else WATER
    cv.fill(pool, wp[1] if active else WATER[2])
    cv.fill(pool & (yy <= 12), wp[0] if not active else JADE_R[0])
    inner = m_ellipse(W, H, 32, 15.5, 20, 3.8)
    cv.fill(inner, WATER[3] if not active else JADE_R[2])
    # reflections / ripples
    if active:
        for k in range(2):
            r = ((f + k * 2) % 4) / 4.0
            ring = m_ellipse(W, H, 32, 15.5, 4 + r * 16, 1 + r * 3) & ~m_ellipse(W, H, 32, 15.5, 3 + r * 16, 0.4 + r * 3)
            cv.fill(ring & inner, JADE_R[4] if r < 0.5 else JADE_R[3])
        cv.fill(m_rect(W, H, 24, 14, 28, 14) & inner, JADE_R[5])
        cv.fill(m_rect(W, H, 36, 17, 39, 17) & inner, JADE_R[4])
    else:
        cv.fill(m_rect(W, H, 20, 13, 27, 13) & inner, WATER[5])
        cv.fill(m_rect(W, H, 35, 16, 40, 16) & inner, WATER[4])
        cv.fill(m_rect(W, H, 29, 18, 31, 18) & inner, WATER[4])
    # side + front rim stones
    rock(cv, 7, 20, 7, 5, "qs_l", pal=STONE, moss=0.5, R=2, facets=2)
    rock(cv, 57, 20, 7, 5.5, "qs_r", pal=STONE, moss=0.5, R=2, facets=2)
    for i, (x, rx, ry) in enumerate(((17, 5, 2.5), (26, 4.5, 2), (35, 5, 2.4), (45, 5, 2.6))):
        rock(cv, x, 21, rx, ry, ("qs_front", i), pal=STONE, moss=0.25, R=1, facets=1, base=0.55)
    grass_tuft(cv, 2, 21, "qs_g1", h=5, n=3)
    grass_tuft(cv, 61, 21, "qs_g2", h=5, n=3)
    fern(cv, 12, 12, "qs_f", h=5, side=-1)
    outline(cv, skip=None)
    if active:
        glow(cv, 32, 13, 26, 9, BRIGHT_JADE, steps=((1.0, 0.1), (0.7, 0.14)))
        motes(cv, 14, 0, 50, 13, f, 4, "qs_m", count=9)
    return cv


@prop("reeds", 32, 40, ground=2)
def reeds(state, f):
    W, H = 32, 40
    cv = Canvas(W, H)
    g = rng("reeds")
    blades = []
    for i in range(11):
        bx = 5 + i * 2.2 + g.uniform(-1, 1)
        top = g.uniform(4, 22)
        lean = g.uniform(-5, 5) + (bx - 16) * 0.25
        blades.append((bx, top, lean))
    blades.sort(key=lambda b: -b[1])
    for i, (bx, top, lean) in enumerate(blades):
        pts = [(bx, 37), (bx + lean * 0.25, (37 + top) / 2 + 2), (bx + lean, top)]
        c = LEAF_BLUE[2 + (i % 3)]
        m = m_curve(W, H, pts)
        cv.fill(m, c)
        if i % 2 == 0:
            cv.fill(shift(m, 1, 0) & (grid(W, H)[1] > top + 6), LEAF_BLUE[1])
    for (bx, top) in ((10, 6), (19, 3), (24, 9)):
        stem(cv, [(bx, 37), (bx + (bx - 16) * 0.15, top + 6), (bx + (bx - 16) * 0.2, top)], FOLIAGE_DRY[2])
        cx = round(bx + (bx - 16) * 0.2)
        head = m_rect(W, H, cx - 1, top, cx, top + 4)
        cv.fill(head, WOOD[3])
        cv.fill(left_edge(head), WOOD[5])
        cv.put(cx, top - 1, FOLIAGE_DRY[3])
    base = blob_mask(W, H, 16, 37, 12, 2.2, "reedbase", 0.2) & (grid(W, H)[1] <= 37)
    shade(cv, base, EARTH, R=1, base=0.4)
    outline(cv)
    return cv


@prop("lotus_pads", 48, 10, ground=2)
def lotus_pads(state, f):
    W, H = 48, 10
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ring = m_ellipse(W, H, 24, 7, 23, 2.6)
    cv.fill(ring, WATER[3], 0.45)
    specs = ((8, 6, 7, 2.6, 1), (21, 5, 5.5, 2.1, -1), (33, 6.5, 8, 2.8, 1), (43, 5.5, 4.5, 1.9, -1), (15, 8, 4, 1.6, 1))
    for (cx, cy, rx, ry, n) in specs:
        pm = m_ellipse(W, H, cx, cy, rx, ry)
        pm &= ~m_poly(W, H, [(cx, cy), (cx + n * rx * 1.3, cy - ry * 0.8), (cx + n * rx * 1.3, cy - ry * 0.1)])
        shade(cv, pm, LEAF_BLUE, contour=True, R=2, base=0.58, gain=1.2)
        cv.fill(pm & (yy == round(cy)) & (abs(xx - cx) < rx * 0.6), LEAF_BLUE[3])
        cv.fill(top_edge(pm), LEAF_BLUE[5])
    # bud
    bud = m_poly(W, H, [(25, 5), (27, 5), (26, 1)])
    cv.fill(bud, hexc("#e7b9c4"))
    cv.put(25, 4, PAPER_R[5])
    cv.fill(m_rect(W, H, 26, 5, 26, 6), LEAF[3])
    outline(cv, skip=ring & ~dilate(cv.solid, diag=True))
    return cv


@prop("driftwood", 48, 14, ground=2)
def driftwood(state, f):
    W, H = 48, 14
    cv = Canvas(W, H)
    ground_shadow(cv, 24, 12, 22, 1.3)
    log = m_poly(W, H, [(3, 8), (8, 6), (22, 5), (36, 6), (44, 5), (46, 7), (43, 10), (30, 11), (12, 11), (4, 11)])
    nz = vnoise(W, H, 3, 11, 2)
    shade(cv, log, WOOD_GREY, contour=True, mode="cylh", base=0.55, gain=0.9, noise=nz, namp=0.3)
    xx, yy = grid(W, H)
    grain = log & erode(log) & ((yy * 7 + (xx // 6)) % 3 == 0) & (nz > 0.45)
    cv.fill(grain, WOOD_GREY[2])
    # branch stubs
    for pts in (((14, 6), (11, 2), (9, 1)), ((30, 6), (32, 3)), ((38, 6), (41, 2), (43, 2))):
        stem(cv, list(pts), WOOD_GREY[4])
        cv.fill(shift(m_curve(W, H, list(pts)), 1, 0) & ~cv.solid, WOOD_GREY[2])
    # end grain rings
    end = m_ellipse(W, H, 45, 7.5, 1.8, 2.4)
    cv.fill(end, WOOD_GREY[5])
    cv.put(45, 7, WOOD_GREY[3])
    moss_top(cv, log, "dw_moss", 0.25, thick=1, drips=False)
    outline(cv)
    return cv


@prop("beast_nest", 40, 20, ground=2)
def beast_nest(state, f):
    W, H = 40, 20
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ground_shadow(cv, 20, 18, 19, 1.4)
    bowl = m_ellipse(W, H, 20, 11.5, 17, 6.5) & (yy <= 17)
    shade(cv, bowl, WOOD, contour=False, R=3, base=0.3, gain=1.0, noise=vnoise(W, H, 2, 5), namp=0.3)
    hollow = m_ellipse(W, H, 20, 9.5, 11.5, 2.4)
    cv.fill(hollow, WOOD[0])
    cv.fill(hollow & (yy >= 10), FEATHER[1])
    g = rng("nest")
    cols = [WOOD[3], WOOD[4], WOOD_GREY[4], STRAW[3], WOOD[2], WOOD_GREY[3], STRAW[4]]
    for i in range(46):
        t = g.uniform(0, 2 * math.pi)
        # twigs hug the rim and the outer wall
        if i < 26:
            cx, cy = 20 + math.cos(t) * 14, 9.5 + math.sin(t) * 3.4
        else:
            cx, cy = 20 + g.uniform(-15, 15), g.uniform(11, 16.5)
        ang = g.uniform(-0.6, 0.6) + (0.5 if g.random() < 0.3 else 0)
        ln = g.uniform(4, 9)
        dx, dy = math.cos(ang) * ln / 2, math.sin(ang) * ln / 2 * 0.6
        m = m_line(W, H, [(cx - dx, cy - dy), (cx + dx, cy + dy)]) & ~hollow
        if yy[m].size and (yy[m] > 17).any():
            m &= yy <= 17
        cv.fill(m, cols[i % len(cols)])
    # twig ends poking out of the silhouette
    for (x0, y0, x1, y1) in ((2, 12, 6, 10), (34, 9, 38, 7), (4, 15, 1, 14), (36, 14, 39, 15), (9, 7, 6, 4), (29, 6, 31, 3)):
        cv.fill(m_line(W, H, [(x0, y0), (x1, y1)]), WOOD[3])
    # bones, skull and a feather in the hollow
    bone = m_line(W, H, [(13, 9), (19, 8)])
    cv.fill(bone, BONE[3])
    for (x, y) in ((12, 8), (12, 10), (20, 7), (20, 9)):
        cv.put(x, y, BONE[4])
    skull = m_ellipse(W, H, 25, 8.5, 2.4, 1.8)
    shade(cv, skull, BONE, mode="sphere", base=0.55)
    cv.put(24, 8, BONE[0])
    cv.put(26, 9, BONE[1])
    fea = m_poly(W, H, [(29, 9), (35, 3), (33, 8)])
    cv.fill(fea, FEATHER[3])
    cv.fill(m_line(W, H, [(29, 9), (35, 3)]), FEATHER[4])
    cv.put(35, 3, PAPER_R[4])
    outline(cv)
    return cv


@prop("grey_patch", 40, 10, ground=0, decal=True)
def grey_patch(state, f):
    W, H = 40, 10
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    nz = vnoise(W, H, 3, seed_of("greyp"), 2)
    stain = m_ellipse(W, H, 20, 5, 19, 4.6) & (nz > 0.32)
    stain |= m_ellipse(W, H, 20, 5, 13, 3)
    cv.fill(stain, HOLLOW[2], 0.55)
    core = m_ellipse(W, H, 19, 5, 11, 2.6) & (nz > 0.4)
    cv.fill(core, HOLLOW[3], 0.7)
    cv.fill(core & (nz > 0.62), HOLLOW[5], 0.6)
    edge = border(stain) & (nz > 0.5)
    cv.fill(edge, HOLLOW[1], 0.6)
    for (x, y) in ((9, 4), (27, 3), (31, 6), (14, 7)):
        cv.put(x, y, HOLLOW[6], 0.8)
    return cv


@prop("hollow_puddle", 48, 12, states=(("idle", 3, 5),), ground=1, decal=True)
def hollow_puddle(state, f):
    W, H = 48, 12
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    pud = blob_mask(W, H, 24, 6, 22, 4.6, "hpud", 0.12)
    cv.fill(pud, HOLLOW[1])
    inner = erode(pud)
    cv.fill(inner, HOLLOW[2])
    cv.fill(m_ellipse(W, H, 24, 6.5, 17, 3), HOLLOW[3])
    cv.fill(bottom_edge(pud), HOLLOW[0])
    cv.fill(top_edge(pud), HOLLOW[4])
    # shimmer bands move across
    for k in range(3):
        x = 8 + ((f * 5 + k * 13) % 30)
        y = 4 + k
        band = m_rect(W, H, x, y, x + 3 + k, y) & inner
        cv.fill(band, HOLLOW[5 if k != 1 else 6])
    cv.put(12 + f * 3, 7, HOLLOW[6])
    cv.put(34 - f * 2, 5, HOLLOW[5])
    outline(cv, t=0.55)
    glow(cv, 24, 5, 22, 5, HOLLOW[5], steps=((1.0, 0.06 + 0.03 * (f == 1)),))
    return cv


@prop("fishing_ripple", 40, 10, states=(("idle", 4, 6),), ground=0, decal=True)
def fishing_ripple(state, f):
    W, H = 40, 10
    cv = Canvas(W, H)
    for k in range(2):
        r = ((f + k * 2) % 4 + 1) / 4.0
        rx, ry = 3 + r * 16, 1 + r * 3.5
        ring = m_ellipse(W, H, 20, 5, rx, ry) & ~m_ellipse(W, H, 20, 5, rx - 1.2, max(0.3, ry - 1))
        a = 0.9 * (1.0 - r * 0.7)
        yy = grid(W, H)[1]
        cv.fill(ring & (yy <= 5), WATER[7], a)
        cv.fill(ring & (yy > 5), WATER[6], a * 0.8)
    cv.fill(m_rect(W, H, 19, 5, 21, 5), WATER[7], 0.9)
    if f in (1, 2):
        cv.put(17 + f, 4, PAPER_R[5], 0.9)
    return cv


@prop("stuck_kite", 24, 24, ground=2)
def stuck_kite(state, f):
    W, H = 24, 24
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ground_shadow(cv, 11, 22, 7, 1.2)
    # scrubby bush with bare twigs
    bush = blob_mask(W, H, 10, 18, 7, 4, "kite_bush", 0.25) & (yy <= 21)
    shade(cv, bush, LEAF, contour=True, R=2, base=0.45, noise=vnoise(W, H, 2, 3), namp=0.5)
    for pts in (((10, 18), (8, 11), (5, 7)), ((11, 18), (13, 12), (17, 9)), ((9, 15), (4, 12)), ((13, 13), (15, 6))):
        stem(cv, list(pts), WOOD[3])
    # kite: diamond paper kite with bamboo cross, red top half, jade eye
    k = m_poly(W, H, [(15, 0), (22, 5), (16, 13), (9, 6)])
    cv.fill(k, PAPER_R[4])
    cv.fill(k & (yy <= 6) & (xx <= 15), CLOTH_RED[4])
    cv.fill(k & (yy <= 6) & (xx > 15), CLOTH_RED[3])
    cv.fill(k & (yy > 6) & (xx > 15), PAPER_R[3])
    cv.fill(m_line(W, H, [(15, 0), (16, 13)]) & k, WOOD[2])
    cv.fill(m_line(W, H, [(9, 6), (22, 5)]) & k, WOOD[2])
    eye = m_ellipse(W, H, 15.5, 8.5, 1.5, 1.2)
    cv.fill(eye, JADE_R[3])
    cv.put(15, 8, INK)
    cv.erase(m_poly(W, H, [(19, 9), (22, 5), (21, 9)]))  # torn corner
    # tail ribbon tangled in the bush
    tail = m_curve(W, H, [(16, 13), (18, 15), (16, 17), (19, 20)])
    cv.fill(tail, WOOD[4])
    for (x, y) in ((18, 15), (16, 17), (19, 20)):
        cv.fill(m_rect(W, H, x - 1, y, x + 1, y), CLOTH_RED[4])
        cv.put(x, y + 1, CLOTH_RED[2])
    outline(cv)
    return cv


@prop("insight_stone", 36, 44, states=(("idle", 1, 0), ("glow", 4, 6)))
def insight_stone(state, f):
    W, H = 36, 44
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    on = state == "glow"
    ground_shadow(cv, 18, 42, 17, 1.6)
    body = (blob_mask(W, H, 18, 23, 13, 19, "ins_body", 0.1) & (yy <= 40))
    body |= blob_mask(W, H, 20, 12, 9, 9, "ins_top", 0.15)
    nz = vnoise(W, H, 3, seed_of("ins"), 2)
    fx, fy, _ = __import__("parts").facet_field(body, "ins", 2)
    shade(cv, body, STONE, contour=True, R=4, strength=2.4, base=0.55, gain=1.5, noise=nz, namp=0.3, normal=(fx, fy))
    # carved cloud swirl: two spirals
    def spiral(cx, cy, r0, turns=1.6, sgn=1):
        pts = []
        for i in range(28):
            t = i / 27
            a = t * turns * 6.2832
            r = r0 * (1 - t * 0.85)
            pts.append((cx + math.cos(a) * r * sgn, cy + math.sin(a) * r))
        return m_line(W, H, pts)
    sw = spiral(15, 20, 6) | spiral(22, 29, 5, sgn=-1) | m_line(W, H, [(9, 20), (9, 33), (16, 34)])
    sw &= erode(body)
    if on:
        c = [JADE_R[4], JADE_R[5], PALE_GOLD, JADE_R[5]][f]
        cv.fill(sw, c)
        cv.fill(shift(sw, 1, 1) & erode(body) & ~sw, JADE_R[2])
    else:
        cv.fill(sw, STONE[1])
        cv.fill(shift(sw, 1, 1) & erode(body) & ~sw, STONE[5])
    moss_top(cv, body, "ins_moss", 0.4, thick=2)
    rock(cv, 6, 40, 5, 3.5, "ins_r1", pal=STONE, moss=0.4, R=2, facets=1)
    rock(cv, 30, 40, 4.5, 3, "ins_r2", pal=STONE, moss=0.3, R=1, facets=1)
    grass_tuft(cv, 11, 40, "ins_g", h=5, n=3)
    grass_tuft(cv, 25, 40, "ins_g2", h=4, n=3)
    fern(cv, 31, 38, "ins_f", h=6, side=1)
    outline(cv)
    if on:
        glow(cv, 18, 26, 16 + (f % 2), 18 + (f % 2), BRIGHT_JADE, steps=((1.0, 0.08), (0.7, 0.1)))
        motes(cv, 6, 2, 30, 30, f, 4, "ins_m", count=7, pal=(BRIGHT_JADE, PALE_GOLD))
    return cv
