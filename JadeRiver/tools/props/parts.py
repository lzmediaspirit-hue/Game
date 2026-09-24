"""Reusable drawing parts: rocks, moss, grass, planks, roofs, lanterns, flames, smoke, motes."""
from __future__ import annotations

import math

import numpy as np

from pixlib import (Canvas, bbox, border, bottom_edge, depth_from_top, dilate, erode, glow, grid, hexc,
                    left_edge, m_ellipse, m_line, m_poly, m_rect, mix, right_edge, rng, seed_of, shade,
                    shade_idx, shift, sparkle, top_edge, vnoise)
from palette import *  # noqa: F401,F403


# ---------------------------------------------------------------- shapes
def blob_mask(w, h, cx, cy, rx, ry, seed, rough=0.12, harmonics=4, flat_base=None):
    xx, yy = grid(w, h)
    dx = (xx - cx) / max(rx, .5)
    dy = (yy - cy) / max(ry, .5)
    th = np.arctan2(dy, dx)
    g = rng("blob", seed)
    r = np.ones_like(th)
    for k in range(2, 2 + harmonics):
        r += rough / (k - 1) * g.uniform(-1, 1) * np.cos(k * th + g.uniform(0, 6.283))
    m = dx * dx + dy * dy <= r * r
    if flat_base is not None:
        m &= yy <= flat_base
    return m


def facet_field(m, seed, cuts=3):
    """Split mask into facet regions with a tilted normal each (chunky carved look)."""
    h, w = m.shape
    xx, yy = grid(w, h)
    x0, y0, x1, y1 = bbox(m)
    g = rng("facet", seed)
    rid = np.zeros((h, w), int)
    for i in range(cuts):
        px = g.uniform(x0 + (x1 - x0) * 0.25, x1 - (x1 - x0) * 0.25)
        py = g.uniform(y0 + (y1 - y0) * 0.2, y1 - (y1 - y0) * 0.3)
        ang = g.uniform(0, math.pi)
        side = ((xx - px) * math.sin(ang) - (yy - py) * math.cos(ang)) > 0
        rid = rid * 2 + side.astype(int)
    nx = np.zeros((h, w))
    ny = np.zeros((h, w))
    for r in np.unique(rid[m]):
        reg = m & (rid == r)
        ys, xs = np.nonzero(reg)
        cyr = (ys.mean() - y0) / max(1, (y1 - y0))
        cxr = (xs.mean() - (x0 + x1) / 2) / max(1, (x1 - x0) / 2)
        nx[reg] = cxr * 0.45 + g.uniform(-0.2, 0.2)
        ny[reg] = (cyr - 0.45) * 0.9 + g.uniform(-0.15, 0.15)
    return nx, ny, rid


def rock(cv: Canvas, cx, by, rx, ry, seed, pal=STONE, moss=0.0, rough=0.14, R=3, base=0.5, cracks=0,
         contour=True, namp=0.3, facets=3, gain=1.5):
    """Chunky faceted boulder resting on baseline `by` (last solid row)."""
    m = blob_mask(cv.w, cv.h, cx, by - ry + 1, rx, ry, seed, rough, flat_base=by)
    nz = vnoise(cv.w, cv.h, 3, seed_of("rockn", seed), 2)
    normal = None
    if facets:
        fx, fy, rid = facet_field(m, seed, facets)
        normal = (fx, fy)
    shade(cv, m, pal, contour=contour, R=R, strength=2.2, base=base, gain=gain, noise=nz, namp=namp, ao=0.12,
          normal=normal)
    # light speckle texture (small pits and glints)
    g = rng("speck", seed)
    inner = erode(m)
    x0, y0, x1, y1 = bbox(m)
    for _ in range(max(1, int((x1 - x0) * (y1 - y0) / 30))):
        px, py = int(g.integers(x0, x1 + 1)), int(g.integers(y0, y1 + 1))
        if inner[py, px] and inner[min(cv.h - 1, py + 1), px]:
            c = cv.color_at(px, py)
            cv.put(px, py, mix(c, pal[0], 0.55))
            cv.put(px - 1, py - 1, mix(cv.color_at(max(0, px - 1), max(0, py - 1)), pal[-1], 0.35)) if inner[py - 1, px - 1] else None
    if cracks:
        crack_lines(cv, m, seed, cracks, pal[1])
    if moss > 0:
        moss_top(cv, m, seed, moss)
    return m


def crack_lines(cv, m, seed, n, c, length=5):
    g = rng("crack", seed)
    x0, y0, x1, y1 = bbox(m)
    for _ in range(n):
        for _try in range(10):
            x = int(g.integers(x0 + 2, max(x0 + 3, x1 - 1)))
            y = int(g.integers(y0 + 2, max(y0 + 3, y1 - 1)))
            if m[y, x]:
                break
        pts = [(x, y)]
        for _s in range(length):
            x += int(g.integers(-1, 2))
            y += 1 if g.random() < 0.7 else 0
            pts.append((x, y))
        cm = m_line(cv.w, cv.h, pts) & erode(m)
        cv.fill(cm, c)


def moss_top(cv, m, seed, coverage=0.5, pal=MOSS, thick=2, drips=True):
    """Moss clusters on the upward-facing surface of mask m."""
    d = depth_from_top(m)
    nz = vnoise(cv.w, cv.h, 4, seed_of("moss", seed), 2)
    nz2 = vnoise(cv.w, cv.h, 2, seed_of("moss2", seed), 1)
    th = (nz * (thick + 1.8)).astype(int)
    band = m & (d <= th) & (nz > 1.0 - coverage)
    if drips:
        drip = m & (d <= th + 2) & (nz2 > 0.82) & (nz > 1.0 - coverage * 1.1)
        band |= drip
    if not band.any():
        return band
    idx = np.full(m.shape, 3)
    idx[d == 0] = 4
    idx[(d >= 2)] = 2
    idx[bottom_edge(band)] = 1
    idx[(d == 0) & (nz2 > 0.7)] = 5
    idx[left_edge(band) & (d <= 1)] = np.maximum(idx[left_edge(band) & (d <= 1)], 4)
    cv.fill_idx(band, idx, pal)
    return band


def grass_tuft(cv, x, by, seed, h=5, pal=LEAF, n=4, spread=3):
    g = rng("tuft", seed)
    for i in range(n):
        bx = x + int(round((i - (n - 1) / 2) * spread / max(1, n - 1) * 2))
        hh = max(2, int(h * g.uniform(0.6, 1.1)))
        lean = g.uniform(-1.3, 1.3) + (i - (n - 1) / 2) * 0.6
        pts = [(bx, by)]
        for s in range(1, hh + 1):
            t = s / hh
            pts.append((bx + lean * t * t * 2.0, by - s))
        mm = m_line(cv.w, cv.h, [(round(px), round(py)) for px, py in pts])
        ys = np.nonzero(mm)[0]
        top = ys.min() if len(ys) else by
        col_i = 3 + (1 if lean < 0 else 0)
        cv.fill(mm, pal[col_i])
        # tip highlight / base shadow
        tip = mm & (grid(cv.w, cv.h)[1] <= top)
        cv.fill(tip, pal[min(len(pal) - 1, col_i + 1)])
        base = mm & (grid(cv.w, cv.h)[1] >= by - 1)
        cv.fill(base, pal[1])


def fern(cv, x, by, seed, h=7, pal=LEAF, side=1):
    """Arching leafy frond made of small leaflets."""
    g = rng("fern", seed)
    pts = []
    for s in range(h + 1):
        t = s / h
        pts.append((x + side * (t * t * h * 0.8), by - math.sin(t * 2.3) * h * 0.8))
    stem = m_line(cv.w, cv.h, pts)
    cv.fill(stem, pal[2])
    for i, (px, py) in enumerate(pts[1:-1:2]):
        lm = m_ellipse(cv.w, cv.h, px, py - 1, 1.2, 1.0)
        cv.fill(lm, pal[3 + (i % 2)])


def ground_shadow(cv, cx, gy, rx, ry=1.5, a=0.35):
    m = m_ellipse(cv.w, cv.h, cx, gy, rx, ry)
    cv.fill(m & (cv.a < 0.5), INK, a)
    return m


def soil_mound(cv, cx, by, rx, ry, seed, pal=EARTH, moss=0.0):
    m = blob_mask(cv.w, cv.h, cx, by, rx, ry, seed, 0.08, flat_base=by)
    nz = vnoise(cv.w, cv.h, 2, seed_of("soil", seed), 2)
    shade(cv, m, pal, R=2, strength=2.0, base=0.45, gain=1.5, noise=nz, namp=0.4)
    # pebbles
    g = rng("pebbles", seed)
    x0, y0, x1, y1 = bbox(m)
    for _ in range(max(1, (x1 - x0) // 6)):
        px = int(g.integers(x0 + 1, max(x0 + 2, x1)))
        py = int(g.integers(y0 + 1, max(y0 + 2, y1 + 1)))
        if m[py, px]:
            cv.put(px, py, pal[-1])
            if py + 1 < cv.h and m[py + 1, px]:
                cv.put(px, py + 1, pal[1])
    if moss:
        moss_top(cv, m, seed, moss, thick=1, drips=False)
    return m


# ---------------------------------------------------------------- wood / structure
def plank_h(cv, x0, y0, x1, y1, pal=WOOD, seed=0, grain=True, contour=True, base=0.5):
    m = m_rect(cv.w, cv.h, x0, y0, x1, y1)
    shade(cv, m, pal, contour=contour, R=1, strength=2.0, base=base, gain=1.3)
    if grain and (x1 - x0) > 4:
        g = rng("grain", seed, x0, y0)
        for _ in range(max(1, (x1 - x0) // 7)):
            gx = int(g.integers(x0 + 1, x1 - 1))
            gy = int(g.integers(y0 + 1, max(y0 + 2, y1)))
            ln = int(g.integers(2, 5))
            gm = m_rect(cv.w, cv.h, gx, gy, min(x1 - 1, gx + ln), gy) & m & ~top_edge(m) & ~bottom_edge(m)
            cv.fill(gm, pal[max(0, 2 if base >= 0.45 else 1)])
    return m


def plank_v(cv, x0, y0, x1, y1, pal=WOOD, seed=0, grain=True, contour=True, base=0.5, mode="cyl"):
    m = m_rect(cv.w, cv.h, x0, y0, x1, y1)
    shade(cv, m, pal, contour=contour, mode=mode, R=1, strength=2.0, base=base, gain=1.0)
    if grain and (y1 - y0) > 5 and (x1 - x0) >= 2:
        g = rng("vgrain", seed, x0, y0)
        for _ in range(max(1, (y1 - y0) // 8)):
            gx = int(g.integers(x0 + 1, max(x0 + 2, x1)))
            gy = int(g.integers(y0 + 1, max(y0 + 2, y1 - 3)))
            ln = int(g.integers(2, 5))
            gm = m_rect(cv.w, cv.h, gx, gy, gx, min(y1 - 1, gy + ln)) & m & ~left_edge(m) & ~right_edge(m)
            cv.fill(gm, pal[max(0, int(len(pal) * base) - 2)])
    return m


def post(cv, x0, y0, x1, y1, pal=LACQUER, contour=True, base=0.5):
    m = m_rect(cv.w, cv.h, x0, y0, x1, y1)
    shade(cv, m, pal, contour=contour, mode="cyl", base=base, gain=1.0)
    return m


def roof_side(cv, x0, x1, y_ridge, y_eave, seed, pal=ROOF, curl=3, ridge_pal=None, tiles=True, thick=2,
              top_frac=0.3, finials=True, sag=0.55):
    """Side-view glazed tile roof: concave slopes, upturned eave tips, ridge with end ornaments."""
    w, h = cv.w, cv.h
    cx = (x0 + x1) / 2.0
    half = (x1 - x0) / 2.0
    top_half = half * top_frac
    n = 24
    upper = []
    for i in range(n + 1):  # right slope from ridge to tip
        t = i / n
        x = cx + top_half + (half - top_half) * t
        y = y_ridge + 1 + (y_eave - y_ridge - 1) * (t ** sag)
        if t > 0.82:
            y -= curl * ((t - 0.82) / 0.18) ** 1.6
        upper.append((x, y))
    tip = upper[-1]
    lower = []
    for i in range(n, -1, -1):  # underside back toward centre
        t = i / n
        x = cx + (half - 1) * t
        y = y_eave + thick - 1
        if t > 0.8:
            y -= (curl + 0.5) * ((t - 0.8) / 0.2) ** 1.4
        lower.append((x, y))
    right = upper + lower
    left = [(2 * cx - x, y) for x, y in reversed(right)]
    body = m_poly(w, h, right) | m_poly(w, h, left)
    body |= m_rect(w, h, int(cx - top_half), y_ridge + 1, int(math.ceil(cx + top_half)), y_eave)
    body &= ~shift(m_rect(w, h, 0, 0, w, h), 0, 0) | True
    xx, yy = grid(w, h)
    nz = vnoise(w, h, 3, seed_of("roof", seed), 1)
    shade(cv, body, pal, contour=True, R=2, strength=1.6, base=0.5, gain=1.2, noise=nz, namp=0.15, top=0.3)
    # eave line (lower rim) following the curl
    rim = body & ~shift(body, 0, -1)
    rim2 = shift(rim, 0, -1) & body
    if tiles:
        chan = body & ~border(body) & ~rim2
        cv.fill(chan & ((xx - int(x0)) % 3 == 0), pal[2])
        cv.fill(chan & ((xx - int(x0)) % 3 == 1) & (nz > 0.5) & (yy > y_ridge + 2), pal[4])
        cv.fill(rim2, pal[1])
        cv.fill(rim2 & ((xx - int(x0)) % 3 == 1), pal[5])
        cv.fill(rim2 & ((xx - int(x0)) % 3 == 2), pal[3])
    cv.fill(rim, pal[0])
    # ridge
    rp = ridge_pal or pal
    rl, rr = int(cx - top_half) - 1, int(math.ceil(cx + top_half)) + 1
    rm = m_rect(w, h, rl, y_ridge - 1, rr, y_ridge + 1)
    shade(cv, rm, rp, contour=False, R=1, base=0.55, gain=1.2)
    cv.fill(top_edge(rm), rp[min(len(rp) - 1, 5)])
    cv.fill(bottom_edge(rm), rp[1])
    if finials:
        for ex, sgn in ((rl, -1), (rr, 1)):
            em = m_rect(w, h, min(ex, ex + sgn), y_ridge - 2, max(ex, ex + sgn), y_ridge + 1)
            em |= m_rect(w, h, ex + sgn * 2, y_ridge - 3, ex + sgn * 2, y_ridge - 2)
            em[max(0, y_ridge - 3), ex + sgn] = True
            shade(cv, em, rp, contour=False, R=1, base=0.6, gain=1.0)
            cv.put(ex + sgn * 2, y_ridge - 3, rp[5])
    # tip ornaments
    for sx in (1, -1):
        tx = cx + sx * (half + 0.5)
        cv.put(round(tx), round(tip[1]) - 1, GOLD[4])
    return body | rm


def lantern(cv, cx, top, w=5, h=6, lit=True, flick=0, pal=CLOTH_RED, cord=2):
    """Red paper lantern hanging from `top` (cord length `cord`)."""
    W, H = cv.w, cv.h
    if cord > 0:
        cv.fill(m_rect(W, H, cx, top, cx, top + cord - 1), INK)
    y0 = top + cord
    cap = m_rect(W, H, cx - w // 2 + 1, y0, cx + (w - 1) // 2 - 1, y0)
    body = m_ellipse(W, H, cx + (0 if w % 2 else -0.5), y0 + 1 + (h - 2) / 2, w / 2, (h - 2) / 2 + 0.3)
    body &= m_rect(W, H, 0, y0 + 1, W, y0 + h - 2)
    cap2 = m_rect(W, H, cx - w // 2 + 1, y0 + h - 1, cx + (w - 1) // 2 - 1, y0 + h - 1)
    if lit:
        lp = ramp_lit = [pal[2], pal[3], pal[4], hexc("#f39a5c"), hexc("#ffd28a")]
        shade(cv, body, lp, mode="sphere", base=0.55 + 0.08 * flick, gain=0.9)
        core = m_ellipse(W, H, cx - 0.5, y0 + h / 2, max(0.6, w / 4), max(0.6, h / 5)) & body
        cv.fill(core, hexc("#ffe2a0"))
    else:
        shade(cv, body, pal, mode="sphere", base=0.45, gain=1.0)
    # ribs
    xx, yy = grid(W, H)
    rib = body & (yy == y0 + h // 2) & ((xx % 2) == 0) & ~dilate(~body)
    cv.fill(m_rect(W, H, 0, 0, 0, 0) & False, INK)
    cv.fill(cap | cap2, GOLD[3])
    cv.put(cx, y0 + h, GOLD[4])
    return body | cap | cap2


def flame(cv, cx, by, h, frame, pal=FIRE, width=None, seed=0):
    """Small stylised flame, 4-frame flicker."""
    W, H = cv.w, cv.h
    w = width or max(2, h // 2 + 1)
    sway = [0, 1, 0, -1][frame % 4]
    hh = h + [0, 1, -1, 1][frame % 4]
    outer = m_poly(W, H, [(cx - w / 2, by), (cx + w / 2, by), (cx + w / 2 - 0.5, by - hh * 0.45),
                          (cx + sway, by - hh), (cx - w / 2 + 0.5, by - hh * 0.5)])
    inner = m_poly(W, H, [(cx - w / 4, by), (cx + w / 4, by), (cx + sway * 0.5, by - hh * 0.6)])
    core = m_rect(W, H, cx - (1 if w > 3 else 0), by - 1, cx, by)
    cv.fill(outer, pal[2])
    cv.fill(border(outer) & ~bottom_edge(outer), pal[1])
    cv.fill(inner, pal[3])
    cv.fill(core, pal[4])
    return outer


def smoke(cv, x, y, frame, nframes, height=14, seed=0, pal=SMOKE, count=3, drift=2.0, size=1.6, alpha=0.75):
    """Looping rising puffs from (x, y). frame in [0,nframes)."""
    g = rng("smoke", seed)
    ph = [g.uniform(0, 6.28) for _ in range(count)]
    for i in range(count):
        t = ((i + frame / nframes) / count) % 1.0
        py = y - t * height
        px = x + math.sin(t * 5.0 + ph[i]) * drift * (0.4 + t)
        r = size * (0.7 + t * 0.9)
        a = alpha * (1.0 - t) ** 0.7
        if a < 0.08:
            continue
        m = m_ellipse(cv.w, cv.h, px, py, r, r * 0.85)
        hl = m & ~shift(m, 1, 1)
        cv.fill(m, pal[1 + (1 if t < 0.5 else 0)], a)
        cv.fill(m & shift(m, -1, -1) & ~shift(m, 1, 1), pal[3], a)


def wisp(cv, x, y, frame, nframes, height=16, seed=0, c=None, alpha=0.7, amp=1.6, width=1):
    """Thin curling incense wisp (1px line) that scrolls upward."""
    c = c or SMOKE[3]
    ph = frame / nframes * 6.2832
    pts = []
    for s in range(height):
        t = s / height
        pts.append((x + math.sin(t * 7.0 - ph + seed) * amp * (0.3 + t), y - s))
    for i in range(len(pts) - 1):
        t = i / height
        a = alpha * (1 - t) ** 0.8
        mm = m_line(cv.w, cv.h, [(round(pts[i][0]), round(pts[i][1])), (round(pts[i + 1][0]), round(pts[i + 1][1]))])
        cv.fill(mm, c, a)


def motes(cv, x0, y0, x1, y1, frame, nframes, seed, count=5, pal=(BRIGHT_JADE, hexc("#d2fbea")), alpha=1.0,
          big=0):
    """Rising glints inside a rectangle; loops over nframes."""
    g = rng("motes", seed)
    xs = [g.uniform(x0, x1) for _ in range(count)]
    offs = [g.uniform(0, 1) for _ in range(count)]
    for i in range(count):
        t = (offs[i] + frame / nframes) % 1.0
        py = y1 - t * (y1 - y0)
        px = xs[i] + math.sin(t * 6.28 + i) * 1.0
        a = alpha * (1.0 if t < 0.7 else (1 - t) / 0.3)
        c = pal[1] if (i + frame) % 3 == 0 else pal[0]
        cv.put(round(px), round(py), c, a)
        if big and i % 2 == 0 and t < 0.6:
            cv.put(round(px), round(py) + 1, pal[0], a * 0.5)


def herb_sparkle(cv, frame, points, c1=PALE_GOLD, c2=hexc("#fffbea")):
    """Subtle 3-frame glint cycling through `points` (list of 3 (x,y))."""
    x, y = points[frame % len(points)]
    sparkle(cv, x, y, 1, c2, c1, 1.0)
    x2, y2 = points[(frame + 1) % len(points)]
    cv.put(x2, y2, c1, 0.8)


def lathe(w, h, cx, profile):
    """Symmetric mask from a profile [(y, half_width), ...] (linearly interpolated)."""
    m = np.zeros((h, w), bool)
    ys = [p[0] for p in profile]
    for y in range(int(min(ys)), int(max(ys)) + 1):
        for i in range(len(profile) - 1):
            (ya, wa), (yb, wb) = profile[i], profile[i + 1]
            if ya <= y <= yb:
                t = 0 if yb == ya else (y - ya) / (yb - ya)
                hw = wa + (wb - wa) * t
                x0 = int(math.floor(cx - hw + 0.5))
                x1 = int(math.ceil(cx + hw - 0.5)) - 1
                if 0 <= y < h:
                    m[y, max(0, x0):min(w, x1 + 1)] = True
                break
    return m


def vessel(cv, cx, profile, pal, base=0.5, gain=1.2, contour=True, rim_light=True):
    m = lathe(cv.w, cv.h, cx, profile)
    shade(cv, m, pal, contour=contour, mode="cyl", base=base, gain=gain, top=0.1, ao=0.15)
    if rim_light:
        cv.fill(top_edge(m) & ~right_edge(m), pal[min(len(pal) - 1, len(pal) - 2)])
    return m


def rope_band(cv, x0, x1, y, pal=ROPE):
    m = m_rect(cv.w, cv.h, x0, y, x1, y)
    xx = grid(cv.w, cv.h)[0]
    cv.fill(m, pal[3])
    cv.fill(m & (xx % 2 == 0), pal[2])
    return m


def sparks(cv, cx, cy, frame, nframes, seed, count=8, spread=10, pal=FIRE):
    g = rng("sparks", seed)
    for i in range(count):
        ang = g.uniform(-math.pi * 0.95, -math.pi * 0.05)
        sp = g.uniform(0.5, 1.0) * spread
        off = g.uniform(0, 1)
        t = ((frame / nframes) + off) % 1.0
        x = cx + math.cos(ang) * sp * t
        y = cy + math.sin(ang) * sp * t + 6 * t * t
        c = pal[5] if t < 0.3 else (pal[4] if t < 0.6 else pal[3])
        cv.put(round(x), round(y), c)
        if t < 0.5:
            cv.put(round(x - math.cos(ang)), round(y - math.sin(ang)), pal[3], 0.8)
