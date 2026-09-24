#!/usr/bin/env python3
"""Build the Jade River UI kit: art/ui/<asset>__<state>.png + data/ui_assets.json.

Everything is authored on an art-pixel canvas (half the screen size) and saved x2
with nearest neighbour, like the rest of the game's art. Frames are built from
concentric "rings" (distance-to-edge bands) so every nine-slice edge is constant
along its stretch axis: panels stretch or tile without seams. Deterministic.

Usage: python3 tools/ui/build_ui.py [--review-dir DIR]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

sys.dont_write_bytecode = True  # keep the repo free of __pycache__

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "props"))

from pixlib import Canvas, SCALE, grid, hexc, mix, save_png  # noqa: E402
from palette import (AGED_BRONZE, BRIGHT_JADE, DEEP_TEAL, GOLD, INK, JADE, JADE_R, JADE_SHADOW, LACQUER,  # noqa: E402
                     PALE_GOLD, PAPER, PAPER_R, RIVER_NIGHT, WARM_GOLD)

DEFAULT_REVIEW = "/tmp/claude-0/-home-user-Game/13461237-7857-505a-bd3b-55d18a20fe2c/scratchpad/art_review"

# ---------------------------------------------------------------- local colours
TEAL_HI = hexc("#1d4a4a")
TEAL_LO = hexc("#0b2a30")
INNER_SHADOW = hexc("#06161b")
JADE_TOP = hexc("#3fb3a2")
SLOT_FILL = hexc("#0c2830")
TROUGH = hexc("#0b171c")
GREY_RIM = hexc("#84958c")
GREY_INNER = hexc("#344d52")
BRONZE_HI = hexc("#c8923e")
BRONZE_LO = hexc("#6a4318")
DIS_RIM = hexc("#5d6663")
DIS_RIM_HI = hexc("#788280")
DIS_FILL = hexc("#1a2528")
DIS_FACE = hexc("#34403f")


# ---------------------------------------------------------------- ring geometry
def ring_field(w, h, r_tl=0, r_tr=None, r_bl=None, r_br=None):
    """Distance (in px) from the outer edge of a rounded rectangle, and nearest side.

    side: 0 top, 1 right, 2 bottom, 3 left. d < 0 = outside."""
    r_tr = r_tl if r_tr is None else r_tr
    r_bl = r_tl if r_bl is None else r_bl
    r_br = r_tl if r_br is None else r_br
    xx, yy = grid(w, h)
    px = xx + 0.5
    py = yy + 0.5
    dl, dr, dt, db = px, w - px, py, h - py
    d = np.minimum(np.minimum(dl, dr), np.minimum(dt, db))
    side = np.select([d == dt, d == db, d == dl], [0, 2, 3], 1)
    for (r, cx, cy, sx, sy) in ((r_tl, r_tl, r_tl, -1, -1), (r_tr, w - r_tr, r_tl * 0 + r_tr, 1, -1),
                                (r_bl, r_bl, h - r_bl, -1, 1), (r_br, w - r_br, h - r_br, 1, 1)):
        if r <= 0:
            continue
        qx = (px - cx) * sx
        qy = (py - cy) * sy
        zone = (qx > 0) & (qy > 0)
        dist = np.sqrt(qx ** 2 + qy ** 2)
        d = np.where(zone, r - dist, d)
        side = np.where(zone, np.where(qy >= qx, 0 if sy < 0 else 2, 1 if sx > 0 else 3), side)
    return d, side


def paint(cv, d, side, rings, fill=None, fill_alpha=1.0):
    """rings[k]: colour | (top, right, bottom, left) | None | (colour, alpha) for band k."""
    k = np.floor(d).astype(int)
    for i, spec in enumerate(rings):
        m = (k == i) & (d >= 0)
        if spec is None:
            continue
        if isinstance(spec, dict):
            a = spec.get("a", 1.0)
            cols = [spec.get(s) for s in ("t", "r", "b", "l")]
            for si, c in enumerate(cols):
                if c is not None:
                    cv.fill(m & (side == si), c, a)
        else:
            cv.fill(m, spec)
    if fill is not None:
        cv.fill((k >= len(rings)) & (d >= 0), fill, fill_alpha)


def bev(top, side_c, bottom, a=1.0):
    return {"t": top, "r": side_c, "b": bottom, "l": side_c, "a": a}


def tl_br(tl, br, a=1.0):
    return {"t": tl, "l": tl, "r": br, "b": br, "a": a}


# ---------------------------------------------------------------- stamps
def stamp(cv, x, y, rows, pal, flip_x=False, flip_y=False):
    rows = [r for r in rows]
    if flip_y:
        rows = rows[::-1]
    for j, row in enumerate(rows):
        if flip_x:
            row = row[::-1]
        for i, ch in enumerate(row):
            if ch in pal:
                c = pal[ch]
                if isinstance(c, tuple) and len(c) == 2 and isinstance(c[0], tuple):
                    cv.put(x + i, y + j, c[0], c[1])
                else:
                    cv.put(x + i, y + j, c)


def corners(cv, rows, pal, inset=0):
    h = len(rows)
    w = len(rows[0])
    stamp(cv, inset, inset, rows, pal)
    stamp(cv, cv.w - w - inset, inset, rows, pal, flip_x=True)
    stamp(cv, inset, cv.h - h - inset, rows, pal, flip_y=True)
    stamp(cv, cv.w - w - inset, cv.h - h - inset, rows, pal, flip_x=True, flip_y=True)


GOLDPAL = {"K": INK, "G": WARM_GOLD, "H": PALE_GOLD, "B": AGED_BRONZE, "D": RIVER_NIGHT, "d": DEEP_TEAL,
           "J": JADE, "L": BRIGHT_JADE, "S": JADE_SHADOW, "W": hexc("#fffbea"), "R": LACQUER[3], "r": LACQUER[1]}

# square key-fret (hui wen) corner for the major window, 11x11 incl. ink
KEY_CORNER = [
    "KKKKKKKKKKK",
    "KHHHHHHHHGK",
    "KHDDDDDDDBK",
    "KHDHHHHGDBK",
    "KHDHDDDBDBK",
    "KHDHDHDBDBK",
    "KHDHDDDBDBK",
    "KHDGBBBBDBK",
    "KHDDDDDDDBK",
    "KGBBBBBBBBK",
    "KKKKKKKKKKK",
]
BRACKET_CORNER = [
    "KKKKKK",
    "KHHHGK",
    "KHKKKK",
    "KHK...",
    "KGK...",
    "KKK...",
]
DOT_CORNER = [
    "KKKK",
    "KHGK",
    "KGBK",
    "KKKK",
]
JEWEL_CORNER = [
    "..KKK..",
    ".KGHGK.",
    "KGSLJGK",
    "KHLWJBK",
    "KGSJSBK",
    ".KGBBK.",
    "..KKK..",
]
CLOUD_CORNER = [
    "KKKKKK...",
    "KHHHGGK..",
    "KHKKKBGK.",
    "KHKHGKBK.",
    "KGKKGKBK.",
    "KGGBBKGK.",
    ".KKKKKGK.",
    "...KGGBK.",
    "....KKK..",
]
TINY_CORNER = [
    "KKK",
    "KHK",
    "KKK",
]


# ---------------------------------------------------------------- asset builders
def canvas(w_screen, h_screen):
    return Canvas(w_screen // SCALE, h_screen // SCALE)


def major_window(state):
    cv = canvas(256, 256)
    d, s = ring_field(cv.w, cv.h, 2)
    paint(cv, d, s, [INK, tl_br(TEAL_HI, TEAL_LO), DEEP_TEAL, INK, bev(JADE_TOP, JADE, JADE_SHADOW),
                     tl_br(INNER_SHADOW, RIVER_NIGHT)], fill=RIVER_NIGHT)
    corners(cv, KEY_CORNER, GOLDPAL)
    return cv


def minor_panel(state):
    cv = canvas(128, 128)
    d, s = ring_field(cv.w, cv.h, 1)
    paint(cv, d, s, [INK, tl_br(TEAL_HI, TEAL_LO), bev(JADE_TOP, JADE, JADE_SHADOW), tl_br(INNER_SHADOW, RIVER_NIGHT)],
          fill=RIVER_NIGHT)
    corners(cv, BRACKET_CORNER, GOLDPAL)
    return cv


def tooltip(state):
    cv = canvas(96, 96)
    d, s = ring_field(cv.w, cv.h, 1)
    paint(cv, d, s, [INK, bev(BRONZE_HI, AGED_BRONZE, BRONZE_LO), INK, tl_br(TEAL_LO, DEEP_TEAL)], fill=DEEP_TEAL)
    corners(cv, DOT_CORNER, GOLDPAL)
    return cv


def slot(state):
    cv = canvas(64, 64)
    d, s = ring_field(cv.w, cv.h, 1)
    if state == "normal":
        rings = [INK, tl_br(hexc("#1c3c40"), hexc("#3d6a66")), tl_br(INNER_SHADOW, SLOT_FILL)]
        fill = SLOT_FILL
    elif state == "selected":
        rings = [INK, bev(PALE_GOLD, WARM_GOLD, AGED_BRONZE), tl_br(AGED_BRONZE, GOLD[1]),
                 tl_br(hexc("#1e3a34"), SLOT_FILL)]
        fill = SLOT_FILL
    else:
        rings = [INK, tl_br(hexc("#252d2f"), hexc("#3b4446")), tl_br(hexc("#0e1416"), DIS_FILL)]
        fill = DIS_FILL
    paint(cv, d, s, rings, fill=fill)
    if state == "selected":
        corners(cv, TINY_CORNER, {"K": AGED_BRONZE, "H": PALE_GOLD}, inset=0)
    return cv


def slot_empty_motif(state):
    """Faint auspicious-cloud curl to sit inside an empty slot (transparent background)."""
    from pixlib import m_line, m_rect
    cv = canvas(64, 64)
    W, H = cv.w, cv.h
    c = hexc("#1f4a4c")
    c_hi = hexc("#285c5c")

    def spiral(cx, cy, r0, turns, sgn, start):
        pts = []
        n = 40
        for i in range(n):
            t = i / (n - 1)
            a = start + sgn * t * turns * 2 * math.pi
            r = r0 * (1 - t * 0.78)
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r * 0.9))
        return m_line(W, H, pts)
    m = spiral(13.5, 15.0, 6.5, 1.35, 1, math.pi * 0.5)
    m |= spiral(21.5, 18.0, 4.2, 1.2, -1, math.pi * 0.5)
    m |= m_line(W, H, [(9, 22), (26, 22)])
    cv.fill(m, c, 0.95)
    cv.fill(m & (np.roll(m, 1, 0) == False), c_hi, 0.95)
    return cv


def selected_slot_glow(state):
    cv = canvas(72, 72)
    d, s = ring_field(cv.w, cv.h, 4)
    k = np.floor(d).astype(int)
    for i, (c, a) in enumerate(((WARM_GOLD, 0.16), (WARM_GOLD, 0.3), (PALE_GOLD, 0.9), (WARM_GOLD, 0.45),
                                (WARM_GOLD, 0.2))):
        cv.fill((k == i) & (d >= 0), c, a)
    return cv


def button(kind, state):
    if kind == "primary":
        cv = canvas(192, 64)
        d, s = ring_field(cv.w, cv.h, 3)
        if state == "normal":
            rings = [INK, bev(PALE_GOLD, WARM_GOLD, AGED_BRONZE), hexc("#0b2a2a"),
                     bev(hexc("#6fd2bb"), hexc("#35a592"), hexc("#1d7466")),
                     bev(hexc("#48b8a3"), JADE, hexc("#23847a"))]
            fill = JADE
        elif state == "pressed":
            rings = [INK, bev(WARM_GOLD, GOLD[3], AGED_BRONZE), hexc("#0b2a2a"),
                     bev(hexc("#16594f"), hexc("#227f71"), hexc("#35a592")),
                     bev(hexc("#1d7466"), hexc("#248a7b"), hexc("#2a9585"))]
            fill = hexc("#248a7b")
        else:
            rings = [INK, bev(DIS_RIM_HI, DIS_RIM, hexc("#454d4b")), hexc("#161e20"),
                     bev(hexc("#4a5655"), DIS_FACE, hexc("#29312f")), DIS_FACE]
            fill = DIS_FACE
        paint(cv, d, s, rings, fill=fill)
        pal = dict(GOLDPAL)
        if state == "disabled":
            pal.update({"H": DIS_RIM_HI, "G": DIS_RIM, "B": hexc("#454d4b")})
        corners(cv, [
            "..KKK",
            ".KHGK",
            "KHGBK",
            "KGBK.",
            "KKK..",
        ], pal, inset=1)
    else:
        cv = canvas(160, 56)
        d, s = ring_field(cv.w, cv.h, 2)
        if state == "normal":
            rings = [INK, bev(BRONZE_HI, AGED_BRONZE, BRONZE_LO), hexc("#081a1f"),
                     bev(JADE_TOP, JADE, JADE_SHADOW), tl_br(hexc("#12393e"), DEEP_TEAL)]
            fill = DEEP_TEAL
        elif state == "pressed":
            rings = [INK, bev(AGED_BRONZE, BRONZE_LO, BRONZE_HI), hexc("#081a1f"),
                     bev(JADE_SHADOW, hexc("#1f7a6d"), JADE), tl_br(INNER_SHADOW, RIVER_NIGHT)]
            fill = RIVER_NIGHT
        else:
            rings = [INK, bev(DIS_RIM_HI, DIS_RIM, hexc("#454d4b")), hexc("#10181a"),
                     bev(hexc("#3d4a4a"), hexc("#34403f"), hexc("#28302f")), DIS_FILL]
            fill = DIS_FILL
        paint(cv, d, s, rings, fill=fill)
    return cv


def tab(state):
    cv = canvas(128, 48)
    d, s = ring_field(cv.w, cv.h, 3, 3, 0, 0)
    if state == "normal":
        rings = [INK, bev(hexc("#3d6a66"), hexc("#2a5552"), hexc("#16393a")), tl_br(TEAL_LO, DEEP_TEAL)]
        paint(cv, d, s, rings, fill=hexc("#0f3238"))
    else:
        # selected: gold top, jade sides, open bottom that merges into a window's fill
        rings = [{"t": INK, "l": INK, "r": INK, "b": JADE},
                 {"t": PALE_GOLD, "l": JADE, "r": JADE_SHADOW, "b": RIVER_NIGHT},
                 {"t": WARM_GOLD, "l": RIVER_NIGHT, "r": RIVER_NIGHT, "b": RIVER_NIGHT}]
        paint(cv, d, s, rings, fill=RIVER_NIGHT)
        corners(cv, ["KK", "KH"], {"K": INK, "H": PALE_GOLD}) if False else None
    return cv


def toast(state):
    cv = canvas(256, 64)
    d, s = ring_field(cv.w, cv.h, 3)
    paint(cv, d, s, [INK, tl_br(TEAL_HI, TEAL_LO), bev(BRIGHT_JADE, JADE, JADE_SHADOW), INK,
                     tl_br(INNER_SHADOW, RIVER_NIGHT)], fill=RIVER_NIGHT)
    corners(cv, [
        "..KKKK",
        ".KHHGK",
        "KHGKKK",
        "KHK...",
        "KGK...",
        "KKK...",
    ], GOLDPAL)
    return cv


def bar_shell(state):
    cv = canvas(256, 32)
    d, s = ring_field(cv.w, cv.h, 2)
    paint(cv, d, s, [INK, bev(BRONZE_HI, AGED_BRONZE, BRONZE_LO), INK, tl_br(hexc("#050d10"), TROUGH)], fill=TROUGH)
    for x in (1, cv.w - 3):
        cv.put(x, 1, PALE_GOLD)
        cv.put(x + 1, 1, WARM_GOLD)
    return cv


def title_plaque(state):
    cv = canvas(384, 72)
    W, H = cv.w, cv.h
    xx, yy = grid(W, H)
    # ribbon ends behind the plaque (left & right 24 art px), swallowtail notch
    for sgn in (1, -1):
        if sgn > 0:
            rib = (xx <= 17) & (yy >= 9) & (yy <= 26)
            notch = (xx <= 6 - np.abs(yy - 17.5) * 0.0 - (8 - np.abs(yy - 17.5)).clip(0) * 0.6) & (yy >= 9) & (yy <= 26)
            notch = (xx < (5 - np.abs(yy - 17.5) * 0.55 + 0.0)) & (yy >= 9) & (yy <= 26)
            fold = (xx >= 14) & (xx <= 17) & (yy >= 8) & (yy <= 27)
        else:
            rib = (xx >= W - 18) & (yy >= 9) & (yy <= 26)
            notch = (xx > W - 1 - (5 - np.abs(yy - 17.5) * 0.55)) & (yy >= 9) & (yy <= 26)
            fold = (xx >= W - 18) & (xx <= W - 15) & (yy >= 8) & (yy <= 27)
        rib &= ~notch
        cv.fill(rib, WARM_GOLD)
        cv.fill(rib & (yy == 9), INK)
        cv.fill(rib & (yy == 26), INK)
        cv.fill(rib & (yy == 10), PALE_GOLD)
        cv.fill(rib & (yy == 25), AGED_BRONZE)
        cv.fill(rib & ((yy == 14) | (yy == 21)), GOLD[3])
        edge = rib & ~(np.roll(rib, 1, 1) & np.roll(rib, -1, 1))
        cv.fill(edge & (yy > 9) & (yy < 26), INK)
        cv.fill(fold, AGED_BRONZE)
        cv.fill(fold & ((yy == 8) | (yy == 27)), INK)
        cv.fill(fold & ((xx == 14) | (xx == W - 15)), GOLD[1])
    # plaque body
    body = Canvas(W - 32, H)
    d, s = ring_field(body.w, body.h, 3)
    paint(body, d, s, [INK, bev(PALE_GOLD, WARM_GOLD, AGED_BRONZE), INK, bev(JADE_R[4], JADE_R[3], JADE_R[1]),
                       bev(JADE_R[3], JADE_R[2], hexc("#155a55"))], fill=JADE_R[2])
    cv.paste(body, 16, 0)
    stamp_pal = dict(GOLDPAL)
    for (x, flip) in ((16, False), (W - 16 - 6, True)):
        stamp(cv, x, 0, ["KKKKKK", "KHHGGK", "KHKKKK", "KGK...", "KKK..."], stamp_pal, flip_x=flip)
        stamp(cv, x, H - 5, ["KKK...", "KGK...", "KGKKKK", "KGBBBK", "KKKKKK"], stamp_pal, flip_x=flip)
    return cv


def currency_pill(state):
    cv = canvas(160, 40)
    d, s = ring_field(cv.w, cv.h, 10)
    paint(cv, d, s, [INK, bev(PALE_GOLD, WARM_GOLD, AGED_BRONZE), INK, tl_br(INNER_SHADOW, RIVER_NIGHT)],
          fill=RIVER_NIGHT)
    return cv


def close_button(state):
    cv = canvas(52, 52)
    d, s = ring_field(cv.w, cv.h, 13)
    pressed = state == "pressed"
    paint(cv, d, s, [INK, bev(PALE_GOLD, WARM_GOLD, AGED_BRONZE) if not pressed else bev(GOLD[3], AGED_BRONZE, GOLD[4]),
                     INK, tl_br(TEAL_HI, INNER_SHADOW) if not pressed else tl_br(INNER_SHADOW, TEAL_LO)],
          fill=DEEP_TEAL if not pressed else RIVER_NIGHT)
    oy = 1 if pressed else 0
    xx, yy = grid(cv.w, cv.h)
    c = (cv.w - 1) / 2.0
    a = (np.abs((xx - c) - (yy - oy - c)) <= 1.0) | (np.abs((xx - c) + (yy - oy - c)) <= 1.0)
    a &= (np.abs(xx - c) <= 6.5) & (np.abs(yy - oy - c) <= 6.5)
    # ink outline around the X
    from pixlib import dilate
    cv.fill(dilate(a, diag=False) & ~a, INK)
    cv.fill(a, WARM_GOLD if not pressed else GOLD[3])
    cv.fill(a & ((yy - oy) < c - 1) & (xx < c + 3), PALE_GOLD if not pressed else WARM_GOLD)
    cv.fill(a & ((yy - oy) > c + 2), AGED_BRONZE)
    return cv


def hud_circle(size, state):
    cv = canvas(size, size)
    W = cv.w
    big = W >= 60
    d0, s0 = ring_field(W, W, W / 2.0)
    d = d0 - 2  # leave 2 art px for the active glow
    s = s0
    fill_a = 0.9
    if state == "normal":
        rings = [(INK, 0.9), bev(hexc("#a9b8ae"), GREY_RIM, hexc("#5f7069"))]
        if big:
            rings.append(bev(GREY_RIM, hexc("#6f8079"), hexc("#4f5f59")))
        rings += [(INK, 0.9), (GREY_INNER, 1.0)]
        fill = hexc("#091d24")
    elif state == "pressed":
        rings = [(INK, 0.95), bev(hexc("#5f7069"), hexc("#6f8079"), hexc("#84958c"))]
        if big:
            rings.append(bev(hexc("#4f5f59"), hexc("#5f7069"), hexc("#6f8079")))
        rings += [(INK, 0.95), (hexc("#223538"), 1.0), (INNER_SHADOW, 0.95)]
        fill = hexc("#061418")
        fill_a = 0.95
    else:
        rings = [(INK, 0.95), bev(PALE_GOLD, WARM_GOLD, AGED_BRONZE)]
        if big:
            rings.append(bev(WARM_GOLD, GOLD[3], AGED_BRONZE))
        rings += [(INK, 0.95), (JADE, 1.0)]
        fill = hexc("#0b2830")
    k = np.floor(d).astype(int)
    for i, spec in enumerate(rings):
        m = (k == i) & (d >= 0)
        if isinstance(spec, dict):
            for si, key in enumerate(("t", "r", "b", "l")):
                cv.fill(m & (s == si), spec[key])
        else:
            cv.fill(m, spec[0], spec[1])
    cv.fill((k >= len(rings)) & (d >= 0), fill, fill_a)
    if state == "active":
        cv.fill((d < 0) & (d >= -1), WARM_GOLD, 0.45)
        cv.fill((d < -1) & (d >= -2), WARM_GOLD, 0.18)
    return cv


def dialogue_box(state):
    cv = canvas(256, 128)
    d, s = ring_field(cv.w, cv.h, 2)
    paint(cv, d, s, [INK, bev(LACQUER[5], LACQUER[4], LACQUER[2]), bev(LACQUER[4], LACQUER[3], LACQUER[1]),
                     bev(PALE_GOLD, WARM_GOLD, AGED_BRONZE), LACQUER[1], tl_br(PAPER_R[2], PAPER_R[4]),
                     tl_br(PAPER_R[3], PAPER)], fill=PAPER)
    corners(cv, CLOUD_CORNER, GOLDPAL)
    return cv


def portrait_frame(state):
    cv = canvas(96, 96)
    d, s = ring_field(cv.w, cv.h, 2)
    paint(cv, d, s, [INK, bev(PALE_GOLD, WARM_GOLD, AGED_BRONZE), bev(WARM_GOLD, GOLD[3], GOLD[1]), INK,
                     bev(JADE_TOP, JADE, JADE_SHADOW), (tl_br(INK, INK, 0.45))], fill=None)
    corners(cv, JEWEL_CORNER, GOLDPAL)
    return cv


def minimap_frame(state):
    cv = canvas(232, 140)
    W, H = cv.w, cv.h
    d, s = ring_field(W, H, 2)
    paint(cv, d, s, [INK, bev(PALE_GOLD, WARM_GOLD, AGED_BRONZE), INK, bev(JADE_TOP, JADE, JADE_SHADOW),
                     tl_br(INNER_SHADOW, RIVER_NIGHT)], fill=RIVER_NIGHT)
    xx, yy = grid(W, H)
    # 22 px (11 art px) header band inside the top margin
    band = (yy >= 3) & (yy <= 10) & (xx >= 3) & (xx <= W - 4)
    cv.fill(band, DEEP_TEAL)
    cv.fill(band & (yy == 3), TEAL_HI)
    cv.fill(band & (yy == 10), INK)
    cv.fill((yy == 11) & (xx >= 3) & (xx <= W - 4), WARM_GOLD)
    cv.fill((yy == 11) & (xx >= 3) & (xx <= W - 4) & (xx % 4 == 0), PALE_GOLD)
    corners(cv, JEWEL_CORNER, GOLDPAL)
    return cv


def realm_badge(state):
    cv = canvas(64, 24)
    d, s = ring_field(cv.w, cv.h, 2)
    paint(cv, d, s, [INK, bev(PALE_GOLD, WARM_GOLD, AGED_BRONZE), bev(JADE_R[4], JADE_R[3], JADE_R[1])],
          fill=JADE_R[2])
    return cv


# name: (builder, states, margins in screen px [l, t, r, b])
ASSETS = {
    "major_window": (major_window, ["normal"], [24, 24, 24, 24]),
    "minor_panel": (minor_panel, ["normal"], [12, 12, 12, 12]),
    "tooltip": (tooltip, ["normal"], [10, 10, 10, 10]),
    "slot": (slot, ["normal", "selected", "disabled"], [8, 8, 8, 8]),
    "slot_empty_motif": (slot_empty_motif, ["normal"], [0, 0, 0, 0]),
    "selected_slot_glow": (selected_slot_glow, ["normal"], [12, 12, 12, 12]),
    "button_primary": (lambda st: button("primary", st), ["normal", "pressed", "disabled"], [16, 14, 16, 14]),
    "button_secondary": (lambda st: button("secondary", st), ["normal", "pressed", "disabled"], [14, 12, 14, 12]),
    "tab": (tab, ["normal", "selected"], [16, 10, 16, 10]),
    "toast": (toast, ["normal"], [20, 12, 20, 12]),
    "bar_shell": (bar_shell, ["normal"], [10, 8, 10, 8]),
    "title_plaque": (title_plaque, ["normal"], [48, 16, 48, 16]),
    "currency_pill": (currency_pill, ["normal"], [20, 10, 20, 10]),
    "close_button": (close_button, ["normal", "pressed"], [0, 0, 0, 0]),
    "hud_circle_large": (lambda st: hud_circle(132, st), ["normal", "pressed", "active"], [0, 0, 0, 0]),
    "hud_circle": (lambda st: hud_circle(64, st), ["normal", "pressed", "active"], [0, 0, 0, 0]),
    "hud_circle_small": (lambda st: hud_circle(52, st), ["normal", "pressed", "active"], [0, 0, 0, 0]),
    "dialogue_box": (dialogue_box, ["normal"], [24, 24, 24, 24]),
    "portrait_frame": (portrait_frame, ["normal"], [16, 16, 16, 16]),
    "minimap_frame": (minimap_frame, ["normal"], [24, 24, 24, 24]),
    "realm_badge": (realm_badge, ["normal"], [8, 8, 8, 8]),
}

SIZES = {"major_window": (256, 256), "minor_panel": (128, 128), "tooltip": (96, 96), "slot": (64, 64),
         "slot_empty_motif": (64, 64), "selected_slot_glow": (72, 72), "button_primary": (192, 64),
         "button_secondary": (160, 56), "tab": (128, 48), "toast": (256, 64), "bar_shell": (256, 32),
         "title_plaque": (384, 72), "currency_pill": (160, 40), "close_button": (52, 52),
         "hud_circle_large": (132, 132), "hud_circle": (64, 64), "hud_circle_small": (52, 52),
         "dialogue_box": (256, 128), "portrait_frame": (96, 96), "minimap_frame": (232, 140), "realm_badge": (64, 24)}


# ---------------------------------------------------------------- nine-slice preview
def nine_slice(img: Image.Image, margins, w, h):
    l, t, r, b = margins
    W, H = img.size
    out = Image.new("RGBA", (w, h))
    xs = [(0, l, 0, l), (l, W - r, l, w - r), (W - r, W, w - r, w)]
    ys = [(0, t, 0, t), (t, H - b, t, h - b), (H - b, H, h - b, h)]
    for (sy0, sy1, dy0, dy1) in ys:
        for (sx0, sx1, dx0, dx1) in xs:
            if sx1 <= sx0 or sy1 <= sy0 or dx1 <= dx0 or dy1 <= dy0:
                continue
            piece = img.crop((sx0, sy0, sx1, sy1)).resize((dx1 - dx0, dy1 - dy0), Image.NEAREST)
            out.alpha_composite(piece, (dx0, dy0))
    return out


def review(images, path):
    font = ImageFont.load_default()
    pad = 16
    cols = 1400
    tiles = []
    for name, states in images.items():
        margins = ASSETS[name][2]
        row = [(f"{name}__{st}", im) for st, im in states.items()]
        if any(margins):
            im = states["normal"]
            w, h = im.size
            tw = (w * 7) // 4 // 2 * 2
            th = (h * 3) // 2 // 2 * 2 if h >= 48 else h
            row.append((f"{name} stretched {tw}x{th}", nine_slice(im, margins, tw, th)))
        tiles.append(row)
    y = pad
    placed = []
    for row in tiles:
        x = pad
        rh = 0
        for label, im in row:
            if x + im.width > cols - pad and x > pad:
                y += rh + pad + 12
                x, rh = pad, 0
            placed.append((label, im, x, y))
            x += im.width + pad
            rh = max(rh, im.height)
        y += rh + pad + 14
    out = Image.new("RGBA", (cols, y + pad), (58, 66, 62, 255))
    d = ImageDraw.Draw(out)
    for label, im, x, yy in placed:
        # checker under transparent parts
        chk = Image.new("RGBA", im.size, (90, 98, 92, 255))
        cd = ImageDraw.Draw(chk)
        for cy in range(0, im.height, 8):
            for cx in range(0, im.width, 8):
                if (cx // 8 + cy // 8) % 2:
                    cd.rectangle([cx, cy, cx + 7, cy + 7], fill=(74, 82, 78, 255))
        out.alpha_composite(chk, (x, yy + 12))
        out.alpha_composite(im, (x, yy + 12))
        d.text((x, yy), label, fill=(232, 225, 207, 255), font=font)
    out.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--review-dir", default=DEFAULT_REVIEW)
    args = ap.parse_args()
    out_dir = os.path.join(ROOT, "art", "ui")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(args.review_dir, exist_ok=True)
    manifest = {}
    images = {}
    count = 0
    for name in sorted(ASSETS):
        fn, states, margins = ASSETS[name]
        entry = {}
        images[name] = {}
        for st in states:
            cv = fn(st)
            want = SIZES[name]
            img = cv.image(SCALE)
            assert img.size == want, (name, img.size, want)
            path = os.path.join(out_dir, f"{name}__{st}.png")
            save_png(img, path)
            entry[st] = f"res://art/ui/{name}__{st}.png"
            images[name][st] = img
            count += 1
        entry["margins"] = list(margins)
        manifest[name] = entry
    with open(os.path.join(ROOT, "data", "ui_assets.json"), "w") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")
    review(images, os.path.join(args.review_dir, "ui_contact.png"))
    print(f"built {count} UI images for {len(manifest)} assets")


if __name__ == "__main__":
    main()
