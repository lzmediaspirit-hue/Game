"""V10c timed stations: a beast trail (Beast Snaring gathering node) and an ancestral altar (Ancestral Rites
station in sect halls).

`beast_trail` uses the herb patch / swarm layout (bottom-centre anchor on the ground line, ground=2, about
the swarm footprint) with three static states: `idle` (the empty trail), `set` (a spring snare set on the
bent sapling: cord, trigger peg and an open noose over the trail) and `caught` (the snare sprung, the
sapling bent further, the noose tight round a small furry critter, tufts of fur on the trail).

`ancestral_altar` is a low grey stone altar table, a little smaller than the lacquered `altar`, with three
ancestral tablets on a stone riser, a bronze tripod censer with a thread of incense smoke and two short red
candles. `idle` (4 frames) has the candles out and one thin wisp; `lit` (4 frames) burns the candles, thickens
the smoke and lays a warm glow round the tablets.

Cords and fur are drawn before the silhouette outline so they get an ink edge and read at game scale;
smoke, flames and glows go on after it."""
from __future__ import annotations

import math

import numpy as np

from defs_expanse import tube
from defs_swarms import _halo, _ink, _stamp
from palette import *  # noqa: F401,F403
from parts import blob_mask, flame, ground_shadow, lathe, smoke, wisp
from pixlib import (Canvas, bottom_edge, erode, glow, grid, hexc, left_edge, m_curve, m_ellipse, m_line, m_poly,
                    m_rect, outline, right_edge, seed_of, shade, shift, top_edge, vnoise)
from registry import prop

# ------------------------------------------------------------------ beast trail
TRAIL_W, TRAIL_H = 32, 28
TRAIL_GRASS = ramp("#12281c", "#1d3f24", "#2d5a2b", "#447535", "#66923e", "#98b457")
CORD = ramp("#6e5634", "#a8894f", "#d8c08a", "#f2e2b4")
HARE = ramp("#3b3530", "#5f5750", "#877e74", "#ada393", "#d0c7b3", "#eee7d6")  # pale mist-hare fur
CUT_PALE = hexc("#e6cf9c")
PRINT = ramp("#2a1c12", "#3b2818")
PAW = ("d.d", ".D.")
PAW_PAL = {"d": PRINT[0], "D": PRINT[1]}
SAPLING_TIP = {"idle": ((6, 24), (6, 17), (9, 10), (14, 5), (18, 4)),
               "set": ((6, 24), (6, 17), (10, 10), (16, 6), (21, 7)),
               "caught": ((6, 24), (7, 17), (9, 12), (13, 9), (16, 12))}


def _cord(cv, pts, c=CORD[2], hi=CORD[3]):
    """A 1 px snare cord along pts (straight segments), lit on its upper-left pixels."""
    m = m_line(cv.w, cv.h, pts)
    cv.fill(m, c)
    cv.fill(m & ~shift(m, 0, 1) & ~shift(m, 1, 0), hi)
    return m


@prop("beast_trail", TRAIL_W, TRAIL_H, states=(("idle", 1, 0), ("set", 1, 0), ("caught", 1, 0)))
def beast_trail(state, f):
    """A worn animal trail through a grass clump: packed bare earth with the grass parted and pressed flat,
    paw prints along it, and a springy sapling bent over it from the left."""
    W, H = TRAIL_W, TRAIL_H
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 25
    ground_shadow(cv, 16, 26, 15, 1.4)
    # grass standing at the back and at both ends; the middle is parted where the trail runs
    blades = [(2, 15, 0), (3, 12, 2), (4, 16, 6), (5, 14, 3), (7, 17, 9), (25, 14, 23), (26, 11, 27), (27, 16, 30),
              (28, 13, 29), (29, 17, 31), (24, 18, 21), (11, 19, 10), (21, 19, 22)]
    for i, (bx, ty, tx) in enumerate(blades):
        pts = [(bx, gy - 2), (bx + (tx - bx) * 0.25, (gy - 2 + ty) / 2 + 1), (tx, ty)]
        m = m_curve(W, H, pts)
        m |= shift(m, 1, 0) & (yy >= gy - 6)
        cv.fill(m, TRAIL_GRASS[2 + i % 3])
        cv.fill(m & (yy <= ty + 1), TRAIL_GRASS[5] if tx < bx else TRAIL_GRASS[4])
    # sapling: springy, bent over the trail
    pts = SAPLING_TIP[state]
    stem = tube(W, H, list(pts[:3]), 1.2, 0.8) | tube(W, H, list(pts[2:]), 0.8, 0.5)
    shade(cv, stem, WOOD, contour=False, R=1, base=0.55, gain=1.2)
    tx, ty = pts[-1]
    lx = [(pts[2][0] - 2, pts[2][1] - 1), (pts[3][0] - 1, pts[3][1] - 2), (pts[3][0] + 1, pts[3][1] + 1),
          (tx - 1, ty - 1)]
    for k, (x, y) in enumerate(lx):
        leaf = m_ellipse(W, H, x, y, 1.6, 1.0)
        cv.fill(leaf, LEAF[3 + k % 2])
        cv.put(x - 1, y, LEAF[5])
    # the trail bed: packed earth, pale down the worn middle
    bed = blob_mask(W, H, 16, gy, 15, 4.2, "bt_bed", 0.06, flat_base=gy)
    nz = vnoise(W, H, 2, seed_of("bt_bed"), 2)
    shade(cv, bed, MUD, contour=True, contour_c=MUD[1], R=2, strength=1.6, base=0.5, gain=1.0, noise=nz, namp=0.3)
    worn = bed & m_ellipse(W, H, 16, gy - 2, 11, 1.6)
    cv.fill(worn, MUD[4])
    cv.fill(worn & (nz > 0.6), MUD[5])
    # grass pressed flat along the trail, pointing the way the beasts go
    for (x0, y0, ln, c) in ((3, 21, 4, 3), (8, 22, 3, 4), (22, 22, 4, 3), (26, 21, 3, 4), (13, 24, 3, 2),
                            (19, 24, 3, 2)):
        cv.fill(m_rect(W, H, x0, y0, x0 + ln - 1, y0), TRAIL_GRASS[c])
        cv.put(x0 + ln - 1, y0, TRAIL_GRASS[5])
    for (px, py) in ((5, 22), (10, 23), (15, 22), (20, 23), (25, 22)):
        _stamp(cv, px, py, PAW, PAW_PAL)
    # front tufts at both ends
    for (bx, gty, gtx) in ((1, 20, 0), (2, 21, 3), (30, 20, 31), (29, 21, 28)):
        cv.fill(m_line(W, H, [(bx, gy), (gtx, gty)]), TRAIL_GRASS[3])
        cv.put(gtx, gty, TRAIL_GRASS[5])
    if state == "set":
        # trigger peg at the trail edge, cord from the sapling tip down to its toggle, open noose over the trail
        peg = m_rect(W, H, 24, 16, 25, gy - 1)
        shade(cv, peg, WOOD, contour=False, mode="cyl", base=0.55, gain=1.0)
        cv.fill(m_rect(W, H, 24, 16, 25, 16), CUT_PALE)
        cv.fill(m_rect(W, H, 21, 16, 23, 16), WOOD[4])  # the toggle stick caught under the peg's hook
        cv.put(21, 17, WOOD[2])
        _cord(cv, [(tx, ty + 1), (22, 15)])
        ring = m_ellipse(W, H, 18, 18, 3.2, 3.2) & ~m_ellipse(W, H, 18, 18, 2.2, 2.2)
        cv.fill(ring, CORD[2])
        cv.fill(ring & (xx + yy < 36), CORD[3])
        cv.fill(ring & (xx + yy > 38), CORD[1])
        _cord(cv, [(21, 17), (20, 16)])
    elif state == "caught":
        # the trigger has sprung free of the peg; the critter hangs in the noose, fur torn off in the struggle
        peg = m_rect(W, H, 24, 16, 25, gy - 1)
        shade(cv, peg, WOOD, contour=False, mode="cyl", base=0.55, gain=1.0)
        cv.fill(m_rect(W, H, 24, 16, 25, 16), CUT_PALE)
        cv.fill(m_rect(W, H, 26, gy - 3, 29, gy - 3), WOOD[4])  # the toggle stick, knocked away
        torso = m_ellipse(W, H, 20, 20.5, 4.6, 3.3) & (yy <= gy - 2)
        for (x, y) in ((18, 16), (20, 16), (22, 17)):
            torso[y, x] = True  # fur standing up along the back
        head = m_ellipse(W, H, 13.5, 19.4, 2.3, 2.1) & (yy <= gy - 2)
        body = torso | head
        ears = m_line(W, H, [(14, 17), (15, 14)]) | m_line(W, H, [(13, 17), (12, 14)])
        fn = vnoise(W, H, 1, seed_of("bt_fur"), 1)
        shade(cv, torso, HARE, contour=False, mode="sphere", base=0.62, gain=1.0, noise=fn, namp=0.25)
        shade(cv, head, HARE, contour=False, mode="sphere", base=0.7, gain=0.9)
        cv.fill(body & (yy >= gy - 3), HARE[1])
        cv.fill(m_ellipse(W, H, 19, 22.2, 3, 0.8) & body, HARE[4])  # pale belly fur
        for (x, y) in ((18, 17), (20, 17), (22, 18)):
            cv.put(x, y, HARE[5])  # ruffled fur on the back
        cv.fill(ears, HARE[3])
        cv.put(15, 14, HARE[5])
        cv.put(12, 14, HARE[5])
        cv.put(15, 15, hexc("#c89a8a"))  # pink inner ear
        cv.put(12, 19, INK)  # eye
        cv.put(11, 20, hexc("#c89a8a"))  # nose
        tail = m_ellipse(W, H, 24.8, 19.4, 1.3, 1.3)
        cv.fill(tail, HARE[5])
        cv.put(24, 19, WHITE_HOT)
        _ink(cv, body | ears | tail, body | ears | tail, t=0.7)
        # noose drawn tight round the neck, cord taut up to the sapling tip
        cv.fill(m_line(W, H, [(16, 17), (16, 21)]), CORD[2])
        cv.put(16, 17, CORD[3])
        cv.put(15, 21, CORD[1])
        _cord(cv, [(tx, ty + 1), (16, 16)])
        for (x, y, big) in ((28, 20, True), (8, 21, False), (26, 23, False)):
            cv.fill(m_rect(W, H, x, y, x + (1 if big else 0), y), HARE[5])
            cv.put(x, y + 1, HARE[3])
            if big:
                cv.put(x + 1, y - 1, HARE[4])
    outline(cv)
    if state == "caught":
        for (x, y) in ((11, 11), (26, 12)):  # drifting tufts (no ink)
            cv.put(x, y, HARE[5], 0.9)
            cv.put(x + 1, y + 1, HARE[4], 0.6)
    return cv


# ------------------------------------------------------------------ ancestral altar
ALTAR_W, ALTAR_H = 52, 44
TABLET = ramp("#170a0a", "#2e1210", "#4a1a16", "#6a2820")
CANDLE = ramp("#4f141a", "#7c1f22", "#a92e2a", "#cf4a38", "#e8765a")
INCENSE_STICK = hexc("#8a3a24")
EMBER = hexc("#ff8a3a")
GLOW_WARM = hexc("#ffc26a")
TABLETS = ((15, 9, 5), (23, 6, 6), (32, 9, 5))  # (left x, top y, width); all stand on the riser at y 21


def _tablet(cv, x0, top, w, lit):
    """An ancestral spirit tablet: a dark red-black lacquer board under a rounded gold cap, on a bronze foot,
    with a column of gold characters down its face."""
    W, H = cv.w, cv.h
    bot = 20
    body = m_rect(W, H, x0, top + 2, x0 + w - 1, bot)
    cap = m_rect(W, H, x0, top + 1, x0 + w - 1, top + 1) | m_rect(W, H, x0 + 1, top, x0 + w - 2, top)
    foot = m_rect(W, H, x0 - 1, bot + 1, x0 + w, bot + 1)
    cv.fill(body, TABLET[2])
    cv.fill(left_edge(body), TABLET[3])
    cv.fill(right_edge(body), TABLET[1])
    cv.fill(cap, GOLD[4])
    cv.fill(top_edge(cap) | left_edge(cap), GOLD[6] if lit else GOLD[5])
    cv.put(x0 + w - 1, top + 1, GOLD[2])
    cv.fill(m_rect(W, H, x0, top + 2, x0 + w - 1, top + 2), TABLET[0])
    cv.fill(foot, BRONZE[3])
    cv.fill(top_edge(foot), BRONZE[5])
    ch = GOLD[6] if lit else GOLD[4]
    cx = x0 + (w - 1) // 2
    for k, y in enumerate(range(top + 4, bot - 1, 2)):
        cv.fill(m_rect(W, H, cx, y, cx + (1 if w % 2 == 0 else 0), y), ch if k % 2 == 0 else GOLD[3])
    return body | cap | foot


@prop("ancestral_altar", ALTAR_W, ALTAR_H, states=(("idle", 4, 4), ("lit", 4, 6)), ground=2)
def ancestral_altar(state, f):
    """A low grey stone altar table with a carved cloud-scroll apron, three ancestral tablets on a stone
    riser, a bronze tripod censer with incense sticks and two short red candles on bronze prickets."""
    W, H = ALTAR_W, ALTAR_H
    lit = state == "lit"
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 41
    ground_shadow(cv, 26, 42, 24, 1.5)
    nz = vnoise(W, H, 3, seed_of("aa_stone"), 2)
    # base plinth and two squat legs
    plinth = m_rect(W, H, 6, gy - 2, 45, gy)
    shade(cv, plinth, STONE_WARM, contour=True, R=1, base=0.45, gain=1.2, noise=nz, namp=0.25)
    cv.fill(top_edge(plinth), STONE_WARM[4])
    for lx in (9, 37):
        leg = m_rect(W, H, lx, 33, lx + 5, gy - 3)
        shade(cv, leg, STONE_WARM, contour=True, R=1, base=0.5, gain=1.3, noise=nz, namp=0.25)
        cv.fill(left_edge(leg), STONE_WARM[4])
    # recess between the legs
    cv.fill(m_rect(W, H, 15, 33, 36, gy - 3), STONE_WARM[0])
    cv.fill(m_rect(W, H, 15, 33, 36, 33), hexc("#171414"))
    # apron with carved cloud scrolls
    apron = m_rect(W, H, 8, 29, 43, 32)
    shade(cv, apron, STONE_WARM, contour=True, R=1, base=0.5, gain=1.0, noise=nz, namp=0.2)
    for sx in (13, 25, 37):
        scroll = (m_ellipse(W, H, sx - 1.5, 30.5, 1.6, 1.2) & ~m_ellipse(W, H, sx - 1.5, 30.5, 0.6, 0.4))
        scroll |= m_ellipse(W, H, sx + 1.5, 30.5, 1.6, 1.2) & ~m_ellipse(W, H, sx + 1.5, 30.5, 0.6, 0.4)
        cv.fill(scroll, STONE_WARM[1])
        cv.fill(scroll & shift(scroll, 1, 1) & ~shift(scroll, -1, -1), STONE_WARM[5])
    for sx in (18, 31):
        cv.fill(m_rect(W, H, sx, 30, sx + 2, 30), STONE_WARM[1])
        cv.fill(m_rect(W, H, sx, 31, sx + 2, 31), STONE_WARM[4])
    # slab top: visible top face and a thick front edge
    top = m_rect(W, H, 4, 25, 47, 28)
    shade(cv, top, STONE_WARM, contour=True, R=1, base=0.55, gain=1.1, noise=nz, namp=0.25)
    cv.fill(m_rect(W, H, 4, 25, 47, 26), STONE_WARM[5])
    cv.fill(m_rect(W, H, 5, 25, 46, 25), STONE_WARM[6])
    cv.fill(m_rect(W, H, 4, 27, 47, 27), STONE_WARM[3])
    cv.fill(m_rect(W, H, 4, 28, 47, 28), STONE_WARM[2])
    cv.put(4, 25, STONE_WARM[4])
    cv.put(47, 25, STONE_WARM[4])
    # riser at the back of the table for the tablets
    riser = m_rect(W, H, 13, 22, 38, 24)
    shade(cv, riser, STONE_WARM, contour=True, R=1, base=0.5, gain=1.0)
    cv.fill(m_rect(W, H, 13, 22, 38, 22), STONE_WARM[5])
    cv.fill(m_rect(W, H, 13, 24, 38, 24), STONE_WARM[2])
    # the three tablets (drawn over a faint back glow when lit)
    for (x0, t, w) in TABLETS:
        _tablet(cv, x0, t, w, lit)
    # candles on bronze prickets at the two ends
    for cx in (7, 43):
        dish = m_rect(W, H, cx - 1, 24, cx + 2, 24)
        cv.fill(dish, BRONZE[4])
        cv.fill(m_rect(W, H, cx, 23, cx + 1, 23), BRONZE[2])
        cv.put(cx - 1, 24, BRONZE[5])
        candle = m_rect(W, H, cx, 18, cx + 1, 22)
        cv.fill(candle, CANDLE[2])
        cv.fill(candle & (xx == cx), CANDLE[3])
        cv.fill(m_rect(W, H, cx, 18, cx + 1, 18), CANDLE[4])
        cv.put(cx + 1, 19, CANDLE[4])  # a wax drip
        cv.put(cx + 1, 20, CANDLE[3])
        cv.put(cx, 17, INK if not lit else FIRE[2])
    # bronze tripod censer at the front centre
    cen = lathe(W, H, 25.5, [(20, 3.0), (21, 4.0), (23, 4.2), (25, 3.4), (26, 2.4)])
    shade(cv, cen, BRONZE, contour=True, mode="cyl", base=0.55, gain=1.3)
    cv.fill(m_rect(W, H, 22, 20, 29, 20), BRONZE[5])
    cv.fill(m_rect(W, H, 23, 20, 28, 20) & (xx % 2 == 0), BRONZE[6])
    cv.fill(cen & (yy == 23) & (xx % 2 == 1), PATINA[3])
    for ex in (21, 30):  # upright ear handles
        cv.fill(m_rect(W, H, ex, 18, ex, 20), BRONZE[3])
        cv.put(ex, 18, BRONZE[5])
    for lx in (23, 28):  # tripod feet
        cv.fill(m_rect(W, H, lx, 26, lx, 27), BRONZE[2])
    cv.fill(m_rect(W, H, 25, 26, 26, 26), BRONZE[2])
    # incense sticks in the ash
    sticks = ((24, 14), (25, 13), (27, 14)) if lit else ((24, 15), (26, 14), (27, 16))
    for (sx, st) in sticks:
        cv.fill(m_rect(W, H, sx, st, sx, 19), INCENSE_STICK)
    outline(cv)
    # ---- lights and smoke (never inked)
    if lit:
        solid = cv.solid.copy()
        glow(cv, 25.5, 14, 18, 11, GLOW_WARM, steps=((1.0, 0.12), (0.75, 0.14), (0.5, 0.16)), m_limit=~solid)
        for (x0, t, w) in TABLETS:
            cv.light(m_rect(W, H, x0 - 1, t - 1, x0 + w, 20) & ~solid, GLOW_WARM, 0.3)
            cv.light(m_rect(W, H, x0, t, x0 + w - 1, 20) & solid, GLOW_WARM, 0.07)
        glow(cv, 25.5, 25, 22, 3, GLOW_WARM, steps=((1.0, 0.08),), m_limit=cv.solid)
        for cx, ph in ((7, 0), (43, 2)):
            flame(cv, cx + 0.5, 17, 4, f + ph, width=3)
            _halo(cv, cx, 14, GLOW_WARM, r=3.6, inner=0.3, outer=0.14)
    for (sx, st) in sticks:
        cv.put(sx, st, EMBER if lit else FIRE[3])
    if lit:
        for i, (sx, st) in enumerate(sticks):
            wisp(cv, sx, st - 1, f, 4, height=13 - i, seed=1.3 + i * 2.1, alpha=0.8, amp=1.3)
        smoke(cv, 25, 10, f, 4, height=9, seed="aa_smoke", count=3, drift=1.6, size=1.5, alpha=0.55)
    else:
        wisp(cv, sticks[1][0], sticks[1][1] - 1, f, 4, height=11, seed=2.0, alpha=0.7, amp=1.0)
    return cv
