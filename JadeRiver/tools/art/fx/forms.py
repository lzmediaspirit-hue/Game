"""The 24 technique forms (docs/technique_plan.md §3.2) as frame-by-frame effect animations.

Each form is a drawer `draw(cv, f, n, band, el)`: frame f of n on an index canvas (fxpix), at richness `band`
(0 for vfx tiers 1-2, 1 for 3-4, 2 for 5-7: thicker strokes, more particles, extra layers) with the element's
dressing from elements.py. FORMS holds each form's sheet spec, which the builder writes to data/fx_art.json:

  cell     the frame in art px (x2 on screen)
  anchor   the point of the frame the game places on the effect's anchor (art px)
  frames   frames in the animation; fps its speed
  impact   the frame that lands on the pose's hit frame (the blow, the pop, the slam)
  span     the art px the effect's shape represents (a ring's diameter, a line's length, a tile's width; for a
           fitted form, how far it reaches forward of its anchor)
  at       where it anchors: chest (the caster's hand height), feet, target (the foe's feet), target_chest
  size     how the game sizes it: band (bigger by tier; with fit, never past a strike's reach), reach (a ring at
           the hitbox's true reach, snapped down), stretch (a line drawn to the exact reach), tile (repeated
           across the reach), travel (moves along the reach)
  bolt     for thrown forms, the projectile's looping sheet: cell, anchor (its head), frames, fps

Right-facing; the game mirrors for the left.
"""
from __future__ import annotations

import math

from elements import dress_edge, fling, ground_ripple, particle, ring_burst
from fxpix import (ACCENT, BASE, CORE, DEEP, GLINT, GLOW_BANDS, HAZE, INK, LIGHT, SOFT_BANDS, STROKE_BANDS, Canvas,
                   ease_in, ease_out, lerp, px_hash)

W = (1.0, 1.3, 1.6)         # stroke width by band
FADE_BANDS = ((0.5, BASE), (1.0, DEEP))
THIN_BANDS = ((0.6, LIGHT), (1.0, BASE))


# ------------------------------------------------------------------------------------------ helpers
def arc_pts(cx, cy, r, a0, a1, sy=1.0, count=12, out=1.0):
    pts = []
    for i in range(count):
        a = lerp(a0, a1, i / max(1, count - 1))
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r * sy
        pts.append((x, y, math.cos(a) * out, math.sin(a) * out))
    return pts


def seg_pts(p0, p1, count=8, side=1.0):
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L * side, dx / L * side
    return [(lerp(p0[0], p1[0], i / max(1, count - 1)), lerp(p0[1], p1[1], i / max(1, count - 1)), nx, ny) for i in range(count)]


def star(cv: Canvas, cx, cy, r, points=4, idx=CORE, halo=GLINT, w=2.0):
    """A radial flash: `points` spikes of radius r with a halo disc."""
    if r <= 0.5:
        return
    cv.disc(cx, cy, r * 0.45, table=((0.5, halo), (1.0, LIGHT)))
    for i in range(points):
        a = i * 2 * math.pi / points + (math.pi / 4 if points == 4 else 0)
        rr = r * (1.0 if i % 2 == 0 else 0.6)
        cv.stroke_seg((cx, cy), (cx + math.cos(a) * rr, cy + math.sin(a) * rr), w, 1.0, table=((0.6, idx), (1.0, halo)))
    cv.dot(cx, cy, CORE, 2)


def smear(cv: Canvas, cx, cy, r, a_from, a_to, w, sy=1.0):
    """The haze of a fast stroke: the sector it swept, in the base haze under the stroke."""
    if abs(a_to - a_from) < 0.02:
        return
    pts = [(cx, cy)] + [(cx + math.cos(a) * r, cy + math.sin(a) * r * sy) for a in
                        [lerp(a_from, a_to, i / 10.0) for i in range(11)]]
    m = cv.mask_polygon(pts)
    inner = cv.mask_ellipse(cx, cy, r - w, (r - w) * sy)
    cv.paint(m & ~inner, HAZE, "under")


# ------------------------------------------------------------------------------------------ 1 strike
def draw_strike(cv, f, n, band, el, cx=14.0, cy=34.0, r=30.0, a0=-1.35, a1=1.05, seed=1):
    k = f / (n - 1)
    w = 7.0 * W[band]
    head_t = min(1.0, ease_out(f / 3.0))
    if f == 0:
        # the gleam at the arc's start: the blade drawn back
        star(cv, cx + math.cos(a0) * r, cy + math.sin(a0) * r, 4 + band, points=4, w=1.5)
        return
    a_head = lerp(a0, a1, head_t)
    if f <= 3:
        a_prev = lerp(a0, a1, min(1.0, ease_out((f - 1) / 3.0)))
        smear(cv, cx, cy, r + w * 0.3, a_prev - 0.15, a_head, w * 0.9)
        # the stroke: fat at the head, thin at the tail
        cv.stroke_arc(cx, cy, r, a0, a_head, w * 0.35, w)
        cv.stroke_arc(cx, cy, r, max(a0, a_head - 0.5), a_head, w * 0.8, w * 1.05)
        pts = arc_pts(cx, cy, r + w * 0.5, a0 + 0.2, a_head, count=10)
        dress_edge(cv, el, pts, f, n, band, seed)
        if f == 3:
            hx, hy = cx + math.cos(a1) * r, cy + math.sin(a1) * r
            star(cv, hx, hy, 6 + band * 2, points=4, w=2.0)
    else:
        # the arc thins and fades from the tail
        u = (f - 3) / (n - 4)
        tail = lerp(a0, a1, u * 0.85)
        table = STROKE_BANDS if u < 0.4 else (THIN_BANDS if u < 0.75 else ((1.0, DEEP),))
        cv.stroke_arc(cx, cy, r, tail, a1, w * 0.4 * (1 - u), w * (1 - u * 0.7), table=table)
        pts = arc_pts(cx, cy, r + w * 0.5, tail, a1, count=8)
        if u < 0.6:
            dress_edge(cv, el, pts, f, n, band, seed, every=4)
    tip = arc_pts(cx, cy, r, a0 + 0.6, a1, count=6)
    fling(cv, el, tip, f, n, band, seed, count=5, start=2, life=4, speed=2.4)


# ------------------------------------------------------------------------------------------ 2 flurry
def draw_flurry(cv, f, n, band, el):
    # three quick cuts, each three frames: a downward jab-cut, a rising cut, a straight cross that lands hardest
    strokes = [((8, 10), (50, 28), 1), ((10, 40), (54, 12), 4), ((4, 24), (60, 24), 7)]
    w = 7.0 * W[band]
    for si, (p0, p1, at) in enumerate(strokes):
        u = f - at
        if u < 0 or u > 3:
            continue
        mid = (lerp(p0[0], p1[0], 0.5), lerp(p0[1], p1[1], 0.5))
        side = seg_pts(p0, p1, 2, side=1.0)[0][2:]
        if u == 0:
            head = (lerp(p0[0], p1[0], 0.55), lerp(p0[1], p1[1], 0.55))
            cv.stroke_seg(p0, head, w * 0.4, w * 1.1)
            cv.paint(cv.mask_polygon([p0, (head[0] + side[0] * 5, head[1] + side[1] * 5), (head[0] - side[0] * 5, head[1] - side[1] * 5)]), HAZE, "under")
        elif u == 1:
            cv.stroke_seg(p0, p1, w * 0.35, w * (1.15 if si == 2 else 1.0))
            cv.paint(cv.mask_polygon([p0, (p1[0] + side[0] * 4, p1[1] + side[1] * 4), (p1[0] - side[0] * 4, p1[1] - side[1] * 4)]), HAZE, "under")
            star(cv, p1[0], p1[1], 5 + band + (3 if si == 2 else 0), points=4, w=1.5)
            dress_edge(cv, el, seg_pts(p0, p1, 8, side=-1.0), f, n, band, 21 + si, every=3)
        elif u == 2:
            cv.stroke_seg((lerp(p0[0], p1[0], 0.35), lerp(p0[1], p1[1], 0.35)), p1, w * 0.3, w * 0.75, table=THIN_BANDS)
            star(cv, p1[0], p1[1], (3 + band) * 0.7, points=4, w=1.0)
            fling(cv, el, seg_pts(p0, p1, 5, side=-1.0)[3:], 1, 4, band, 31 + si, count=4, start=0, life=2, speed=2.2)
        else:
            cv.stroke_seg((lerp(p0[0], p1[0], 0.6), lerp(p0[1], p1[1], 0.6)), p1, 1.0, w * 0.4, table=((1.0, DEEP),))
            fling(cv, el, seg_pts(p0, p1, 5, side=-1.0)[3:], 2, 4, band, 31 + si, count=4, start=0, life=2, speed=2.2)


# ------------------------------------------------------------------------------------------ 3 thrust
def draw_thrust(cv, f, n, band, el):
    y = 16.0
    w = 6.0 * W[band]
    x0 = 4.0
    if f <= 3:
        tip = lerp(8.0, 88.0, ease_out(f / 3.0))
        prev = lerp(8.0, 88.0, ease_out(max(0, f - 1) / 3.0))
        # the trail: thin at the hand, fat behind the point
        cv.stroke_seg((x0, y), (tip - 4, y), w * 0.35, w)
        # the point
        cv.polygon([(tip - 6, y - w * 0.5), (tip + 4, y), (tip - 6, y + w * 0.5)], LIGHT)
        cv.polygon([(tip - 4, y - w * 0.25), (tip + 3, y), (tip - 4, y + w * 0.25)], CORE)
        cv.paint(cv.mask_polygon([(prev - 6, y - w * 0.9), (tip, y - w * 0.4), (tip, y + w * 0.4), (prev - 6, y + w * 0.9)]), HAZE, "under")
        pts = seg_pts((x0 + 8, y), (tip - 6, y), 10, side=-1.0) + seg_pts((x0 + 8, y), (tip - 6, y), 10, side=1.0)
        dress_edge(cv, el, pts, f, n, band, 41, every=4)
        if f == 3:
            star(cv, tip - 1, y, 7 + band * 2, points=8, w=1.5)
            cv.ring(tip - 1, y, 5, 1.0, GLINT)
    else:
        u = (f - 3) / (n - 4)
        tip = 88.0
        # the trail breaks up from the hand forward
        start = lerp(x0 + 6, tip - 14, u)
        cv.stroke_seg((start, y), (tip - 4, y), w * 0.3 * (1 - u), w * (1 - u * 0.6), table=THIN_BANDS if u < 0.5 else ((1.0, DEEP),))
        for i in range(3):
            xx = start - 6 - i * 7
            if xx > x0:
                cv.line1((xx, y), (xx - 3, y), DEEP)
        cv.ring(tip - 1, y, 5 + u * 10, 1.0, LIGHT if u < 0.5 else DEEP)
        fling(cv, el, seg_pts((tip - 10, y), (tip - 2, y), 4, side=-1.0) + seg_pts((tip - 10, y), (tip - 2, y), 4, side=1.0),
              f - 3, n - 3, band, 43, count=6, start=0, life=4, speed=2.0)


# ------------------------------------------------------------------------------------------ 4 lunge
def draw_lunge(cv, f, n, band, el):
    y = 22.0
    feet = 46.0
    hit = (104.0, y - 2)   # the blow lands a step ahead of the caster (the anchor is his chest)
    if f <= 3:
        u = f / 3.0
        # afterimages of the dash trail off behind the caster, sliding after him and thinning
        for i in range(3):
            ax = lerp(8.0, 48.0, i / 2.0) + u * 14.0
            if ax > 64:
                continue
            tone = (HAZE, DEEP, BASE)[min(2, i + (1 if u > 0.6 else 0))] if i + f < 5 else HAZE
            cv.figure(ax, feet, 44, tone, lean=0.25)
        for i in range(4 + band * 2):
            yy = y - 14 + i * (28 / (3 + band * 2))
            xs = 4 + px_hash(i, 5) * 20 + u * 24
            cv.line1((xs, yy), (xs + 10 + u * 10, yy), LIGHT if i % 2 else DEEP)
        for i in range(3):
            cv.dot(6 + i * 6 + u * 10, feet - 1 - (i % 2), HAZE, 2)   # the dust of the dash
        if f == 3:
            star(cv, hit[0], hit[1], 10 + band * 3, points=8, w=2.5)
            cv.ring(hit[0], hit[1], 8, 1.5, GLINT)
            cv.stroke_seg((76, y), (hit[0] - 8, hit[1]), 2.0, 6.0 * W[band])   # the rush into the blow
    else:
        u = (f - 3) / (n - 4)
        if u < 0.5:
            cv.figure(60, feet, 44, HAZE, lean=0.25)
        star(cv, hit[0], hit[1], (10 + band * 3) * (1 - u), points=8, w=2.0)
        cv.ring(hit[0], hit[1], 8 + u * 14, 1.5 if u < 0.5 else 1.0, LIGHT if u < 0.5 else DEEP)
        fling(cv, el, arc_pts(hit[0], hit[1], 6, -math.pi, math.pi, count=8), f - 3, n - 3, band, 51, count=8, start=0, life=4, speed=2.6)


# ------------------------------------------------------------------------------------------ 5 sweep
def draw_sweep(cv, f, n, band, el):
    cx, cy, r, sy = 48.0, 36.0, 44.0, 0.3
    w = 6.0 * W[band]
    if f <= 3:
        u = ease_out(f / 3.0)
        # the near half: from the back (left) over the front to the right
        a_head = lerp(math.pi, 0.0, u)
        cv.stroke_arc(cx, cy, r, math.pi, a_head, w * 0.4, w, sy=sy)
        smear(cv, cx, cy, r + 2, math.pi, a_head, w, sy)
        pts = arc_pts(cx, cy, r + 2, math.pi, a_head, sy, count=12)
        dress_edge(cv, el, pts, f, n, band, 61, every=3)
        for x, y, nx, ny in pts[::3]:
            cv.dot(x + nx * 3, y + 3, HAZE, 2)   # the dust the sweep kicks up
        if f == 3:
            star(cv, cx + r, cy, 5 + band * 2, points=4, w=1.5)
    else:
        u = (f - 3) / (n - 4)
        # the far half, dim behind the body, then everything fades
        far = lerp(0.0, -math.pi, min(1.0, u * 1.6))
        cv.stroke_arc(cx, cy, r, far, 0.0, 1.0, w * 0.5, sy=sy, table=((1.0, DEEP),))
        tail = lerp(math.pi, 0.4, u)
        cv.stroke_arc(cx, cy, r, tail, 0.0, w * 0.3 * (1 - u), w * (1 - u * 0.7), sy=sy, table=THIN_BANDS if u < 0.5 else ((1.0, DEEP),))
        ring_burst(cv, el, cx, cy, r, f - 3, n - 3, band, 62, count=8, sy=sy, rise=0.4, life=4)
        if u < 0.6:
            ground_ripple(cv, el, cx, cy, r * 0.9, f, n, band, sy)


# ------------------------------------------------------------------------------------------ 6 arc (launch)
def crescent(cv, cx, cy, r, w, span=1.3, table=STROKE_BANDS):
    cv.stroke_arc(cx - r * 0.5, cy, r, -span, span, w * 0.3, w * 0.3)
    cv.stroke_arc(cx - r * 0.5, cy, r, -span * 0.6, span * 0.6, w, w, table=table)


def draw_arc(cv, f, n, band, el):
    cx, cy = 22.0, 32.0
    w = 6.0 * W[band]
    if f <= 2:
        u = (f + 1) / 3.0
        crescent(cv, cx, cy, 8 + 14 * u, w * u)
        if f == 2:
            star(cv, cx + 8, cy, 6 + band * 2, points=4, w=1.5)
        pts = arc_pts(cx - 11, cy, 22 * u + 2, -1.1, 1.1, count=9)
        dress_edge(cv, el, pts, f, n, band, 71, every=3)
    elif f <= 5:
        u = (f - 2) / 3.0
        x = cx + ease_in(u) * 70
        crescent(cv, x, cy, 22, w)
        # the wake it leaves
        for i in range(3 + band):
            yy = cy - 10 + i * (20 / (2 + band))
            cv.line1((max(10, x - 30 - i * 4), yy), (x - 10, yy), HAZE if i % 2 else DEEP)
        pts = arc_pts(x - 11, cy, 24, -1.1, 1.1, count=9)
        dress_edge(cv, el, pts, f, n, band, 72, every=3)
        fling(cv, el, [(x - 8, cy - 14, -0.3, -1.0), (x - 8, cy + 14, -0.3, 1.0)], f - 2, 4, band, 73, count=4, start=0, life=3)
    else:
        u = (f - 5) / max(1, n - 6)
        for i in range(3 + band):
            yy = cy - 10 + i * (20 / (2 + band))
            cv.line1((40 + u * 30 + i * 3, yy), (70 + u * 20, yy), DEEP if u < 0.5 else HAZE)


# ------------------------------------------------------------------------------------------ 7 volley
def draw_volley(cv, f, n, band, el):
    hx, hy = 10.0, 24.0
    angles = (-0.26, 0.0, 0.26) if band < 2 else (-0.36, -0.12, 0.12, 0.36)
    if f <= 1:
        star(cv, hx + 4, hy, 6 + f * 4 + band * 2, points=8, w=2.0)
        cv.paint(cv.mask_polygon([(hx, hy), (hx + 22, hy - 9), (hx + 22, hy + 9)]), HAZE, "dither")
        return
    u = (f - 2) / max(1, n - 3)
    if f <= 3:
        star(cv, hx + 4, hy, (11 + band * 2) * (1 - u), points=8, w=2.0)
    cv.paint(cv.mask_polygon([(hx, hy), (hx + 26 + u * 16, hy - 11 - u * 3), (hx + 26 + u * 16, hy + 11 + u * 3)]), HAZE, "dither") if u < 0.5 else None
    for i, a in enumerate(angles):
        d = lerp(6.0, 95.0, ease_out((f - 2 + i * 0.15) / 3.5))
        head = (hx + math.cos(a) * d, hy + math.sin(a) * d)
        tail = (hx + math.cos(a) * max(4.0, d - 26 - band * 6), hy + math.sin(a) * max(4.0, d - 26 - band * 6))
        if head[0] < 82:
            cv.stroke_seg(tail, head, 1.0, 4.5 * W[band], table=STROKE_BANDS if f < 6 else THIN_BANDS)
            cv.polygon([(head[0] - 3, head[1] - 2.5), (head[0] + 3, head[1]), (head[0] - 3, head[1] + 2.5)], CORE)
            dress_edge(cv, el, seg_pts(tail, head, 5, side=-1.0 if i % 2 else 1.0), f, n, band, 81 + i, every=3)
        elif f < 7:
            cv.stroke_seg(tail, (80, hy + math.sin(a) * 80), 1.0, 2.5, table=((1.0, DEEP),))
    # smoke of the loosing
    if 2 <= f <= 6:
        for i in range(4 + band):
            cv.dot(hx - 2 + px_hash(i, 4) * 8 - u * 6, hy - 7 + px_hash(i, 6) * 14 - u * 4, HAZE, 2)


# ------------------------------------------------------------------------------------------ 8 rain
def draw_rain(cv, f, n, band, el):
    ground = 88.0
    count = (9, 12, 16)[band]
    for i in range(count):
        x0 = 4 + px_hash(i, 91) * 52
        born = int(px_hash(i, 92) * 5)
        u = f - born
        if u < 0:
            continue
        fall = 20.0 + band * 2
        head_y = u * fall
        slant = 0.18
        if head_y < ground:
            hx = x0 + head_y * slant
            L = 18 + band * 6
            tail = (hx - L * slant, head_y - L)
            cv.stroke_seg(tail, (hx, head_y), 1.0, 4.0 * W[band] * 0.75)
            cv.polygon([(hx - 2, head_y - 4), (hx + 2, head_y - 4), (hx + 0.5, head_y + 1), (hx - 0.5, head_y + 1)], CORE)
            if band and i % 2:
                cv.dot(hx - 2, head_y - 7, GLINT)
        else:
            # the splash where it lands: a crown of the element, and a ring on the ground
            age = (head_y - ground) / fall
            if age <= 3.0:
                lx = x0 + ground * slant
                a = min(1.0, age / 3.0)
                for k, (dx, dy) in enumerate(((-1.0, -1.2), (1.0, -1.2), (-0.3, -1.6), (0.4, -1.5))):
                    if k >= 2 and not band:
                        continue
                    particle(cv, el, lx + dx * (2 + a * 5), ground - 3 - (1 - a) * 5 * -dy + a * 3, dx, dy, a, i * 5 + k)
                cv.ring(lx, ground, 3 + a * 7, 1.5 if a < 0.4 else 1.0, LIGHT if a < 0.5 else DEEP, 0.35)
                if a < 0.45:
                    star(cv, lx, ground - 3, 3 + band, points=4, w=1.0)


# ------------------------------------------------------------------------------------------ 9 pillar
def draw_pillar(cv, f, n, band, el):
    cx, ground = 24.0, 104.0
    top = 6.0
    wmax = (12.0, 15.0, 18.0)[band]
    if f <= 2:
        u = ease_out((f + 1) / 3.0)
        h = (ground - top) * u
        w = wmax * (0.5 + 0.5 * u)
        cv.stroke_seg((cx, ground), (cx, ground - h), w, w * 0.6, table=((0.2, CORE), (0.5, LIGHT), (0.8, BASE), (1.0, DEEP)))
        star(cv, cx, ground - h, w * 0.5, points=4, w=1.5)
        cv.ring(cx, ground, 6 + 10 * u, 1.5, LIGHT, 0.3)
    elif f <= 6:
        u = (f - 3) / 3.0
        pulse = 1.0 + 0.12 * math.sin(f * 2.1)
        cv.stroke_seg((cx, ground), (cx, top), wmax * pulse, wmax * 0.7, table=((0.25, CORE), (0.5, LIGHT), (0.8, BASE), (1.0, DEEP)))
        # the light flares out at the top
        cv.paint(cv.mask_polygon([(cx - wmax * 0.35, top + 10), (cx + wmax * 0.35, top + 10), (cx + wmax * 0.8, top - 2), (cx - wmax * 0.8, top - 2)]), LIGHT, "under")
        star(cv, cx, top + 2, wmax * 0.5 * pulse, points=4, w=1.5)
        if f == 3:
            star(cv, cx, ground - 6, 10 + band * 3, points=8, w=2.0)
            cv.ring(cx, ground, 16, 2.0, GLINT, 0.3)
        cv.ring(cx, ground, 16 + u * 6, 1.0, LIGHT if u < 0.5 else DEEP, 0.3)
        # motes climbing the column
        for i in range(4 + band * 3):
            y = ground - ((f * 9 + px_hash(i, 101) * 90) % (ground - top))
            x = cx + (px_hash(i, 102) - 0.5) * wmax * 1.4
            cv.dot(x, y, GLINT if i % 2 else ACCENT)
        dress_edge(cv, el, seg_pts((cx + wmax * 0.5, ground - 8), (cx + wmax * 0.5, top + 8), 8, side=-1.0)
                   + seg_pts((cx - wmax * 0.5, ground - 8), (cx - wmax * 0.5, top + 8), 8, side=1.0), f, n, band, 111, every=3)
    else:
        u = (f - 7) / max(1, n - 8)
        w = wmax * (1 - u * 0.8)
        cv.stroke_seg((cx, ground - u * 40), (cx, top), w, w * 0.5, table=THIN_BANDS if u < 0.5 else ((1.0, DEEP),))
        cv.ring(cx, ground, 22 + u * 6, 1.0, DEEP, 0.3)
    ground_ripple(cv, el, cx, ground, 14 + band * 2, f, n, band, 0.3) if 3 <= f <= 7 else None


# ------------------------------------------------------------------------------------------ 10 wave (a travelling crest)
def draw_wave(cv, f, n, band, el):
    cx, gy = 30.0, 40.0
    hmax = (22.0, 26.0, 30.0)[band]
    h = hmax * (ease_out((f + 1) / 2.5) if f < 2 else (1.0 if f < 6 else 1.0 - (f - 5) / (n - 5) * 0.8))
    # the crest: a long back slope, a steep front face, and a lip that curls forward and over, leaving a hollow
    roll = (f % 4) / 4.0                      # the curl rolls a quarter turn a frame
    lip_x = cx + 10 + roll * 4
    lip_y = gy - h * (0.62 - roll * 0.12)
    top = (cx + 2, gy - h)
    pts = [(cx - 28, gy), (cx - 16, gy - h * 0.42), (cx - 6, gy - h * 0.86), top, (cx + 9, gy - h * 0.96), (cx + 14, gy - h * 0.82),
           (lip_x + 2, lip_y), (lip_x - 2, lip_y + 3), (cx + 8, gy - h * 0.5), (cx + 12, gy - h * 0.34), (cx + 16, gy - h * 0.12), (cx + 18, gy)]
    body = cv.mask_polygon(pts)
    hollow = cv.mask_ellipse(cx + 9, gy - h * 0.55, 4.5, h * 0.16)
    body &= ~hollow
    cv.paint(body, BASE)
    # lit along the lip and the top, deep on the back slope and under the curl
    cv.paint(cv.mask_polygon([(cx - 6, gy - h * 0.86), top, (cx + 9, gy - h * 0.96), (cx + 14, gy - h * 0.82), (lip_x + 2, lip_y), (cx + 9, gy - h * 0.72), (cx, gy - h * 0.72)]) & body, LIGHT)
    cv.paint(cv.mask_polygon([(cx - 1, gy - h * 0.98), top, (cx + 9, gy - h * 0.96), (cx + 7, gy - h * 0.86), (cx + 1, gy - h * 0.88)]) & body, GLINT)
    cv.paint(cv.mask_polygon([(cx - 28, gy), (cx - 16, gy - h * 0.42), (cx - 8, gy - h * 0.5), (cx - 12, gy)]) & body, DEEP)
    cv.paint(cv.mask_polygon([(cx + 4, gy - h * 0.45), (cx + 12, gy - h * 0.5), (cx + 16, gy - h * 0.12), (cx + 6, gy - h * 0.1)]) & body, DEEP)
    # foam along the lip, and spray thrown ahead of it
    cv.line1((cx + 4, gy - h - 1), (cx + 10, gy - h * 0.94 - 1), CORE)
    cv.dot(lip_x + 2, lip_y - 1, CORE, 2)
    for i in range(3 + band):
        cv.dot(lip_x + 3 + i * 2 + (f % 2), lip_y - 2 - px_hash(i, f) * 5, GLINT if i % 2 else CORE)
    # the trail behind: the ground it passed, as haze
    cv.paint(cv.mask_polygon([(2, gy - 3), (cx - 22, gy - 5), (cx - 12, gy), (2, gy)]), HAZE, "under")
    tip_pts = [(lip_x + 2, lip_y - 2, 0.8, -0.6), (cx + 15, gy - h * 0.8, 0.9, -0.4), (cx + 17, gy - h * 0.2, 1.0, -0.1)]
    fling(cv, el, tip_pts, f, n, band, 121, count=7, start=0, life=3, speed=2.2, gravity=0.5)
    dress_edge(cv, el, arc_pts(cx - 4, gy, h, -2.3, -0.9, count=7), f, n, band, 122, every=3)
    if f == 3:
        star(cv, cx + 18, gy - h * 0.4, 4 + band, points=4, w=1.0)
    if el != "water" and f > 1:
        ground_ripple(cv, el, cx + 4, gy, 12, f, n, band, 0.3)


# ------------------------------------------------------------------------------------------ 11 burst
def draw_burst(cv, f, n, band, el):
    cx, cy, gy = 48.0, 30.0, 48.0
    R = 46.0
    sy = 0.35
    if f <= 1:
        # the gathering: a core that tightens, a ring that draws in
        cv.disc(cx, cy, 7 - f * 2, table=GLOW_BANDS)
        cv.ring(cx, gy, 20 - f * 8, 1.5, LIGHT, sy)
        for i in range(6 + band * 2):
            a = i * 2 * math.pi / (6 + band * 2)
            d = 16 - f * 6
            cv.dot(cx + math.cos(a) * d, cy + math.sin(a) * d * 0.6, GLINT)
        return
    u = (f - 2) / (n - 3)
    r = lerp(14.0, R, ease_out(u * 1.3))
    if f == 2:
        star(cv, cx, cy, 16 + band * 4, points=12, w=3.0)
        cv.disc(cx, cy, 6, table=((1.0, CORE),))
    else:
        star(cv, cx, cy, (16 + band * 4) * max(0.0, 1 - u * 1.4), points=12, w=2.0)
    # the ring on the ground at the reach, thick then thin
    cv.ring(cx, gy, r, 4.0 * W[band] * (1 - u * 0.7) + 1.0, LIGHT if u < 0.5 else BASE, sy)
    cv.ring(cx, gy, r - 2, 1.0, GLINT if u < 0.4 else DEEP, sy)
    if band:
        cv.ring(cx, gy, r * 0.62, 1.5, DEEP, sy)
    # the wall of the burst rising off the ring
    if u < 0.6:
        for i in range(10 + band * 4):
            a = i * 2 * math.pi / (10 + band * 4) + u
            x, y = cx + math.cos(a) * r, gy + math.sin(a) * r * sy
            cv.stroke_seg((x, y), (x, y - (8 + band * 3) * (1 - u)), 2.0, 1.0, table=((0.5, LIGHT), (1.0, BASE)) if u < 0.3 else FADE_BANDS)
    ring_burst(cv, el, cx, gy, r * 0.8, f - 2, n - 2, band, 131, count=10, sy=sy, rise=1.2, life=4)
    ground_ripple(cv, el, cx, gy, r * 0.8, f, n, band, sy)


# ------------------------------------------------------------------------------------------ 12 seeker (launch)
def draw_seeker(cv, f, n, band, el):
    hx, hy = 12.0, 24.0
    m = 3 + (band > 1)
    if f <= 2:
        # the motes gather round the hand
        for i in range(m):
            a = f * 1.1 + i * 2 * math.pi / m
            d = 9 - f * 2
            x, y = hx + math.cos(a) * d, hy + math.sin(a) * d * 0.7
            cv.disc(x, y, 2.5, table=GLOW_BANDS)
            cv.dot(x, y, CORE)
        if f == 2:
            star(cv, hx, hy, 7 + band * 2, points=4, w=1.5)
        return
    u = (f - 3) / (n - 4)
    for i in range(m):
        curve = (i - (m - 1) / 2) * 9
        d = lerp(4.0, 90.0, ease_out(u * 1.1))
        x = hx + d
        y = hy + curve * math.sin(u * math.pi * 0.9) + curve * 0.3
        if x < 80:
            cv.disc(x, y, 3 + band * 0.5, table=GLOW_BANDS)
            cv.dot(x, y, CORE, 2)
            # the trail
            trail = []
            for j in range(6 + band * 2):
                dd = d - j * 5
                if dd < 4:
                    break
                uu = max(0.0, u - j * 0.05)
                trail.append((hx + dd, hy + curve * math.sin(uu * math.pi * 0.9) + curve * 0.3))
            if len(trail) > 1:
                cv.stroke_poly(trail, 2.5, 1.0, table=((0.5, LIGHT), (1.0, BASE)) if u < 0.6 else FADE_BANDS)
            dress_edge(cv, el, [(t[0], t[1], 0.0, -1.0 if i % 2 else 1.0) for t in trail[1:]], f, n, band, 141 + i, every=3)
        else:
            cv.line1((60, y), (78, y), DEEP)


# ------------------------------------------------------------------------------------------ 13 return (launch)
def blade(cv, cx, cy, ang, L, w):
    ux, uy = math.cos(ang), math.sin(ang)
    px_, py_ = -uy, ux
    pts = [(cx - ux * L * 0.5, cy - uy * L * 0.5), (cx + px_ * w, cy + py_ * w), (cx + ux * L * 0.5, cy + uy * L * 0.5), (cx - px_ * w, cy - py_ * w)]
    cv.shaded_polygon(pts, table=((0.3, GLINT), (0.7, LIGHT), (1.0, BASE)))
    cv.dot(cx + ux * L * 0.5, cy + uy * L * 0.5, CORE)


def draw_return(cv, f, n, band, el):
    hx, hy = 14.0, 24.0
    if f <= 2:
        # the spin-up at the hand: a circular blur growing
        cv.stroke_arc(hx, hy, 6 + f * 3, f * 1.6, f * 1.6 + 2.4 + f * 1.2, 2.0, 5.0 * W[band], table=STROKE_BANDS)
        blade(cv, hx, hy, f * 1.6 + 2.4, 12, 2.5)
        return
    if f <= 5:
        u = (f - 3) / 2.0
        x = lerp(hx + 8, 88.0, ease_in(u))
        # the streak out, a trail bending up (the way back)
        cv.stroke_seg((hx + 4, hy + 2), (x - 6, hy - 2 - u * 6), 1.5, 5.0 * W[band], table=STROKE_BANDS)
        cv.paint(cv.mask_polygon([(hx + 4, hy + 4), (x - 6, hy - 6 - u * 6), (x - 6, hy + 3 - u * 4), (hx + 6, hy + 7)]), HAZE, "under")
        if x < 84:
            blade(cv, x, hy - 2 - u * 6, f * 1.3, 12, 2.5)
        dress_edge(cv, el, seg_pts((hx + 8, hy + 2), (x - 6, hy - 2 - u * 6), 8, side=-1.0), f, n, band, 151, every=3)
        fling(cv, el, [(x - 4, hy - 6 - u * 6, 0.3, -1.0)], f - 3, 4, band, 152, count=4, start=0, life=3)
        return
    u = (f - 6) / max(1, n - 7)
    # the streak fades; the call-back ring at the hand
    cv.stroke_seg((hx + 10 + u * 30, hy - u * 2), (84, hy - 8), 1.0, 3.0, table=((1.0, DEEP),)) if u < 0.7 else None
    cv.ring(hx, hy, 4 + u * 8, 1.0, LIGHT if u < 0.5 else DEEP)
    cv.ring(hx, hy, 2 + u * 5, 1.0, GLINT) if u < 0.5 else None


# ------------------------------------------------------------------------------------------ 14 snare
def tendril(cv, el, base, tip, u, band, seed, w):
    """One tendril from `base` to `tip`, grown by u (0..1), in the element's own way."""
    if u <= 0.02:
        return
    n_pts = 7
    pts = []
    for i in range(n_pts):
        t = i / (n_pts - 1) * u
        x = lerp(base[0], tip[0], t)
        y = lerp(base[1], tip[1], t)
        if el in ("earth", "metal", "thunder"):
            x += (px_hash(seed, i) - 0.5) * 4 * (1 if el != "earth" else 0.5)
        else:
            x += math.sin(t * 5 + seed) * 3.0 * (1.0 - t * 0.5)
        pts.append((x, y))
    if el == "metal":
        # a chain: alternating links
        for i in range(len(pts) - 1):
            cv.stroke_seg(pts[i], pts[i + 1], w, w, table=((0.5, LIGHT), (1.0, DEEP)) if i % 2 else ((1.0, DEEP),))
    elif el == "thunder":
        for i in range(len(pts) - 1):
            cv.line1(pts[i], pts[i + 1], CORE if i % 2 else GLINT)
        cv.stroke_poly(pts, w * 0.8, w * 0.8, table=((0.5, LIGHT), (1.0, BASE)))
        for i in range(len(pts) - 1):
            cv.line1(pts[i], pts[i + 1], CORE if i % 2 else GLINT)
    elif el == "earth":
        cv.stroke_poly(pts, w * 1.4, w * 0.5, table=((0.4, LIGHT), (0.8, BASE), (1.0, DEEP)))
    else:
        cv.stroke_poly(pts, w * 1.1, w * 0.5, table=STROKE_BANDS if el in ("water", "fire", "soul", "space", "time") else ((0.4, LIGHT), (0.8, BASE), (1.0, DEEP)))
    if u > 0.5:
        dress_edge(cv, el, [(p[0], p[1], 1.0 if (seed + i) % 2 else -1.0, -0.3) for i, p in enumerate(pts[2:])], int(u * 6), 8, band, seed, every=2)


def draw_snare(cv, f, n, band, el):
    cx, gy = 40.0, 48.0
    R, sy = 30.0, 0.32
    top = (40.0, 16.0)
    m = 5 + band
    w = 3.0 * W[band]
    k = f / (n - 1)
    if f <= 3:
        u = ease_out((f + 1) / 4.5)
        cv.ring(cx, gy, R * min(1.0, (f + 1) / 2.5), 1.5, LIGHT, sy)
        for i in range(m):
            a = i * 2 * math.pi / m + 0.4
            base = (cx + math.cos(a) * R, gy + math.sin(a) * R * sy)
            tendril(cv, el, base, top, u * 0.85, band, 161 + i, w)
        ground_ripple(cv, el, cx, gy, R, f, n, band, sy)
    elif f <= 7:
        u = 0.85 + 0.15 * min(1.0, (f - 3) / 1.5)
        pulse = 1.0 + 0.1 * math.sin(f * 2.0)
        cv.ring(cx, gy, R, 1.0, DEEP if f > 4 else LIGHT, sy)
        for i in range(m):
            a = i * 2 * math.pi / m + 0.4
            base = (cx + math.cos(a) * R, gy + math.sin(a) * R * sy)
            tendril(cv, el, base, top, u, band, 161 + i, w * pulse)
        if f == 4:
            star(cv, top[0], top[1], 8 + band * 2, points=4, w=1.5)
        cv.ring(top[0], top[1], 3 + band, 1.5, GLINT if f < 6 else LIGHT)   # the knot
        ground_ripple(cv, el, cx, gy, R, f, n, band, sy)
    else:
        u = (f - 8) / max(1, n - 9)
        for i in range(m):
            a = i * 2 * math.pi / m + 0.4
            base = (cx + math.cos(a) * R, gy + math.sin(a) * R * sy)
            tendril(cv, el, base, (top[0], top[1] + u * 24), 1.0 - u * 0.5, band, 161 + i, w * (1 - u * 0.6))
        cv.ring(cx, gy, R, 1.0, DEEP, sy)
        fling(cv, el, arc_pts(top[0], top[1] + 4, 4, -math.pi, 0, count=5), f - 7, 4, band, 171, count=5, start=0, life=3, gravity=0.6)


# ------------------------------------------------------------------------------------------ 15 counter
def draw_counter(cv, f, n, band, el):
    gx, gy = 34.0, 30.0
    if f == 0:
        cv.stroke_seg((gx, 10), (gx, 54), 2.0, 2.0, table=((0.5, LIGHT), (1.0, DEEP)))
        cv.dot(gx, gy, GLINT, 2)
        return
    u = (f - 1) / (n - 2)
    if f == 1:
        cv.stroke_seg((gx, 8), (gx, 56), 3.0 * W[band], 3.0 * W[band])
        star(cv, gx, gy, 12 + band * 3, points=4, w=3.0)
        cv.ring(gx, gy, 6, 1.5, GLINT)
        dress_edge(cv, el, seg_pts((gx, 12), (gx, 52), 8, side=-1.0), f, n, band, 181, every=2)
        return
    cv.stroke_seg((gx, 12 + u * 10), (gx, 52 - u * 10), 2.0 * (1 - u), 2.0 * (1 - u), table=THIN_BANDS if u < 0.5 else ((1.0, DEEP),))
    star(cv, gx, gy, (12 + band * 3) * (1 - u), points=4, w=2.0)
    cv.ring(gx, gy, 6 + u * 16, 1.5 if u < 0.5 else 1.0, LIGHT if u < 0.5 else DEEP)
    fling(cv, el, arc_pts(gx, gy, 5, -math.pi, math.pi, count=8), f - 2, n - 2, band, 182, count=6, start=0, life=3, speed=2.4)


# ------------------------------------------------------------------------------------------ 16 ward
def draw_ward(cv, f, n, band, el):
    cx, gy = 40.0, 68.0
    rx, ry = 34.0, 58.0
    if f <= 3:
        u = ease_out((f + 1) / 4.5)
        # the dome closes from the ground up on both sides
        a = math.pi * u * 0.5
        for side in (0, 1):
            a0 = math.pi + (a if side else 0.0)
            a1 = 2 * math.pi - (0.0 if side else a)
            cv.stroke_arc(cx, gy, rx, math.pi, math.pi + a, 2.0, 2.5 * W[band], sy=ry / rx)
            cv.stroke_arc(cx, gy, rx, 2 * math.pi - a, 2 * math.pi, 2.5 * W[band], 2.0, sy=ry / rx)
        cv.ring(cx, gy, rx, 1.5, LIGHT, 0.3)
        cv.paint(cv.mask_ellipse(cx, gy, rx - 2, ry - 2) & (cv.Y < gy) & (cv.Y > gy - ry * u), HAZE, "under")
        pts = arc_pts(cx, gy, rx + 2, math.pi, math.pi + a, ry / rx, count=6) + arc_pts(cx, gy, rx + 2, 2 * math.pi - a, 2 * math.pi, ry / rx, count=6)
        dress_edge(cv, el, pts, f, n, band, 191, every=3)
        return
    u = (f - 4) / (n - 5)
    outline = STROKE_BANDS if f < 8 else THIN_BANDS
    cv.stroke_arc(cx, gy, rx, math.pi, 2 * math.pi, 2.5 * W[band] * (1 - u * 0.4), 2.5 * W[band] * (1 - u * 0.4), sy=ry / rx, table=outline)
    cv.ring(cx, gy, rx, 1.5, LIGHT if f < 8 else DEEP, 0.3)
    if f < 8:
        cv.paint(cv.mask_ellipse(cx, gy, rx - 2, ry - 2) & (cv.Y < gy), HAZE, "under")
    # a highlight at the upper left and a sheen that travels across
    cv.stroke_arc(cx, gy, rx - 3, math.pi * 1.15, math.pi * 1.4, 1.5, 1.5, sy=ry / rx, table=((1.0, GLINT),))
    sheen = math.pi + math.pi * ((u * 1.4) % 1.0)
    cv.stroke_arc(cx, gy, rx - 5, sheen - 0.15, sheen + 0.15, 1.0, 1.0, sy=ry / rx, table=((1.0, CORE),))
    if f == 4:
        star(cv, cx, gy - ry, 7 + band * 2, points=4, w=1.5)
    pts = arc_pts(cx, gy, rx + 2, math.pi, 2 * math.pi, ry / rx, count=14)
    dress_edge(cv, el, pts, f, n, band, 192, every=3)
    ring_burst(cv, el, cx, gy, rx, f - 4, n - 4, band, 193, count=6, sy=0.3, rise=1.0, life=5)


# ------------------------------------------------------------------------------------------ 17 chorus
def draw_chorus(cv, f, n, band, el):
    cx, gy = 48.0, 52.0
    R, sy = 44.0, 0.35
    for j in range(3 + (band > 1)):
        born = j * 2
        u = (f - born) / 5.0
        if u < 0 or u > 1:
            continue
        r = lerp(6.0, R, ease_out(u))
        cv.ring(cx, gy, r, 3.0 * W[band] * (1 - u * 0.7) + 1.0, LIGHT if u < 0.5 else BASE, sy)
        cv.ring(cx, gy, r - 1, 1.0, GLINT if u < 0.3 else DEEP, sy)
        ground_ripple(cv, el, cx, gy, r * 0.85, f, n, band, sy) if j == 0 else None
    # notes and motes rising from the singer
    for i in range(4 + band * 2):
        u = ((f * 0.13) + px_hash(i, 201)) % 1.0
        x = cx + (px_hash(i, 202) - 0.5) * 30 + math.sin(u * 6 + i) * 3
        y = gy - 20 - u * 36
        if i % 2 == 0:
            cv.stamp([".L", "LL", "L."], x - 1, y - 1, {"L": GLINT if u < 0.6 else LIGHT})   # a small quaver head
            cv.line1((x + 1, y - 1), (x + 1, y - 5), GLINT if u < 0.6 else LIGHT)
        else:
            particle(cv, el, x, y, 0, -1, u, i)
    if f == 3:
        star(cv, cx, gy - 30, 6 + band * 2, points=4, w=1.5)


# ------------------------------------------------------------------------------------------ 18 blink
def draw_blink(cv, f, n, band, el):
    y = 20.0
    feet = 46.0
    if f <= 3:
        # the departure puff at the left, then afterimages of the caster along the way
        if f == 0:
            cv.ring(8, feet, 6, 1.5, LIGHT, 0.35)
            cv.stroke_seg((8, y - 12), (8, y + 14), 3.0, 1.0, table=THIN_BANDS)
        for i in range(f):
            ax = 16 + i * 20
            tone = (BASE, DEEP, HAZE)[max(0, min(2, i - f + 3))]
            cv.figure(ax, feet, 42, tone, lean=0.2, dither=tone != BASE)
            cv.line1((ax - 8, y - 4 + i * 3), (ax + 2, y - 4 + i * 3), LIGHT)
        cv.ring(8, feet, 6 + f * 4, 1.0, DEEP if f > 1 else LIGHT, 0.35)
        return
    u = (f - 4) / (n - 5)
    for i in range(3):
        ax = 16 + i * 20
        if u < 0.7 or i == 2:
            cv.figure(ax, feet, 42, HAZE if u > 0.3 or i < 2 else DEEP, lean=0.2)
    # the arrival: a flash and the cut
    if f == 4:
        star(cv, 80, y, 12 + band * 3, points=8, w=2.5)
        cv.stroke_arc(74, y - 6, 16, -1.2, 0.9, 2.0, 6.0 * W[band])
        dress_edge(cv, el, arc_pts(74, y - 6, 20, -1.2, 0.9, count=8), f, n, band, 211, every=3)
    else:
        star(cv, 80, y, (12 + band * 3) * (1 - u), points=8, w=2.0)
        cv.stroke_arc(74, y - 6, 16, -1.2 + u * 1.2, 0.9, 1.0, 6.0 * W[band] * (1 - u * 0.7), table=THIN_BANDS if u < 0.5 else ((1.0, DEEP),))
        fling(cv, el, arc_pts(74, y - 6, 16, -0.6, 0.9, count=5), f - 4, n - 4, band, 212, count=6, start=0, life=3, speed=2.4)


# ------------------------------------------------------------------------------------------ 19 plunge
def draw_plunge(cv, f, n, band, el):
    cx, gy = 48.0, 44.0
    R, sy = 46.0, 0.35
    if f <= 1:
        h = 40 - f * 12
        cv.stroke_seg((cx, gy - h), (cx, gy - 4 - f * 2), 4.0 * W[band], 8.0 * W[band], table=STROKE_BANDS)
        cv.paint(cv.mask_polygon([(cx - 9, gy - h - 6), (cx + 9, gy - h - 6), (cx + 5, gy - 2), (cx - 5, gy - 2)]), HAZE, "under")
        for i in range(3 + band):
            xx = cx - 12 + i * (24 / (2 + band))
            cv.line1((xx, gy - h + 6 + i * 2), (xx, gy - h - 6 + i * 2), DEEP if i % 2 else LIGHT)
        return
    u = (f - 2) / (n - 3)
    r = lerp(12.0, R, ease_out(u * 1.2))
    if f == 2:
        star(cv, cx, gy - 4, 14 + band * 3, points=8, w=3.0)
    else:
        star(cv, cx, gy - 4, (14 + band * 3) * max(0.0, 1 - u * 1.5), points=8, w=2.0)
    cv.ring(cx, gy, r, 3.5 * W[band] * (1 - u * 0.6) + 1.0, LIGHT if u < 0.5 else BASE, sy)
    cv.ring(cx, gy, r - 2, 1.0, GLINT if u < 0.4 else DEEP, sy)
    # cracks in the ground
    for i in range(6 + band * 2):
        a = i * 2 * math.pi / (6 + band * 2) + 0.3
        L = min(r, 8 + u * 30 + px_hash(i, 221) * 8)
        pts = [(cx, gy)]
        for j in range(1, 4):
            d = L * j / 3
            pts.append((cx + math.cos(a + (px_hash(i, j) - 0.5) * 0.4) * d, gy + math.sin(a + (px_hash(i, j) - 0.5) * 0.4) * d * sy))
        for j in range(len(pts) - 1):
            cv.line1(pts[j], pts[j + 1], INK if u < 0.7 else DEEP)
    # dust and rock thrown up
    for i in range(6 + band * 3):
        a = px_hash(i, 231) * 2 * math.pi
        d = r * (0.5 + px_hash(i, 232) * 0.5)
        cv.dot(cx + math.cos(a) * d, gy + math.sin(a) * d * sy - u * 6 - px_hash(i, 233) * 6, HAZE, 3 if band else 2)
    ring_burst(cv, el, cx, gy, 10, f - 2, n - 2, band, 241, count=10, sy=sy, rise=2.0, life=5)
    ground_ripple(cv, el, cx, gy, r * 0.7, f, n, band, sy) if u < 0.8 else None


# ------------------------------------------------------------------------------------------ 20 release
def draw_release(cv, f, n, band, el):
    hx, hy = 32.0, 44.0
    if f <= 2:
        cv.disc(hx, hy, 4 + f * 2, table=GLOW_BANDS)
        cv.ring(hx, hy, 8 + f * 4, 1.0, LIGHT)
        for i in range(5 + band * 2):
            a = i * 2 * math.pi / (5 + band * 2) - f * 0.7
            d = 14 - f * 3
            cv.dot(hx + math.cos(a) * d, hy + math.sin(a) * d * 0.6, GLINT)
        return
    if f <= 4:
        u = (f - 3) / 1.0
        top = lerp(hy - 6, 8.0, ease_out(u * 0.9 + 0.1))
        cv.stroke_seg((hx, hy), (hx, top), 2.0, 5.0 * W[band])
        cv.paint(cv.mask_polygon([(hx - 5, hy), (hx + 5, hy), (hx + 3, top + 4), (hx - 3, top + 4)]), HAZE, "under")
        star(cv, hx, top, 6 + band * 2, points=4, w=1.5)
        dress_edge(cv, el, seg_pts((hx, hy - 6), (hx, top + 4), 8, side=1.0), f, n, band, 251, every=2)
        cv.ring(hx, hy, 12 + u * 6, 1.0, DEEP)
        return
    u = (f - 5) / (n - 6)
    # the streak curls forward at the top and thins
    cv.stroke_seg((hx, hy - u * 20), (hx, 12), 1.5, 4.0 * W[band] * (1 - u * 0.6), table=STROKE_BANDS if u < 0.4 else THIN_BANDS)
    cv.stroke_arc(hx + 10, 12, 10, -math.pi, -math.pi + 1.5 * min(1.0, u * 2), 4.0 * W[band] * (1 - u * 0.6), 1.5, table=STROKE_BANDS if u < 0.4 else THIN_BANDS)
    tip = (hx + 10 + math.cos(-math.pi + 1.5 * min(1.0, u * 2)) * 10, 12 + math.sin(-math.pi + 1.5 * min(1.0, u * 2)) * 10)
    cv.dot(tip[0], tip[1], CORE, 2)
    fling(cv, el, [(tip[0], tip[1], 1.0, -0.3)], f - 5, n - 5, band, 252, count=6, start=0, life=4, speed=2.0)
    dress_edge(cv, el, seg_pts((hx, hy - 8), (hx, 14), 6, side=1.0), f, n, band, 253, every=3) if u < 0.6 else None


# ------------------------------------------------------------------------------------------ 21 swarm
def draw_swarm(cv, f, n, band, el):
    cx, cy = 48.0, 30.0
    rx, ry = 40.0, 12.0
    m = (6, 8, 10)[band]
    if f <= 2:
        cv.disc(cx, cy, 5 + f * 2, table=GLOW_BANDS)
        for i in range(m):
            a = i * 2 * math.pi / m + f * 0.3
            blade(cv, cx + math.cos(a) * (4 + f * 3), cy + math.sin(a) * (2 + f * 1.5), a, 6, 1.5)
        return
    u = (f - 3) / (n - 4)
    spread = ease_out(min(1.0, u * 2.2))
    for i in range(m):
        a = i * 2 * math.pi / m + f * 0.45
        x, y = cx + math.cos(a) * rx * spread, cy + math.sin(a) * ry * spread
        # the trail of each blade along the orbit
        pts = [(cx + math.cos(a - j * 0.16) * rx * spread, cy + math.sin(a - j * 0.16) * ry * spread) for j in range(2, 6 + band)]
        cv.stroke_poly(pts, 1.5, 1.0, table=((1.0, DEEP),) if math.sin(a) > 0 else ((1.0, HAZE),))
        tx, ty = -math.sin(a) * rx, math.cos(a) * ry   # the orbit's tangent: the blade points the way it flies
        ang = math.atan2(ty, tx)
        blade(cv, x, y, ang, 12 + band * 2, 2.5)
        if math.sin(a) <= 0:   # the far side, behind the body: dimmer
            cv.paint(cv.mask_ellipse(x, y, 8, 4) & (cv.idx >= LIGHT), BASE)
    cv.rim(INK, of=(BASE, LIGHT, GLINT))
    if f == 3:
        star(cv, cx, cy, 9 + band * 2, points=8, w=2.0)
    cv.ring(cx, cy + 14, rx * spread, 1.0, DEEP, 0.3)
    dress_edge(cv, el, arc_pts(cx, cy, rx * spread + 3, 0, 2 * math.pi, ry / rx, count=12), f, n, band, 261, every=4)


# ------------------------------------------------------------------------------------------ 22 seal
SEAL_GLYPH = [".###.", "#...#", "#.#.#", "#...#", ".###.", "..#..", ".###."][:5]   # a seal-script "bind": a ringed eye


def seal_face(cv, cx, cy, s, glow):
    pts = [(cx - s, cy - s), (cx + s, cy - s), (cx + s, cy + s), (cx - s, cy + s)]
    cv.polygon(pts, BASE)
    cv.polygon([(cx - s, cy - s), (cx + s, cy - s), (cx + s - 2, cy - s + 2), (cx - s + 2, cy - s + 2)], LIGHT)
    cv.polygon([(cx - s, cy - s), (cx - s + 2, cy - s + 2), (cx - s + 2, cy + s - 2), (cx - s, cy + s)], LIGHT)
    cv.polygon([(cx + s, cy - s), (cx + s, cy + s), (cx + s - 2, cy + s - 2), (cx + s - 2, cy - s + 2)], DEEP)
    cv.polygon([(cx - s, cy + s), (cx + s, cy + s), (cx + s - 2, cy + s - 2), (cx - s + 2, cy + s - 2)], DEEP)
    g = int(s * 0.9)
    scale = max(1, int(g / 3))
    for j, row in enumerate(SEAL_GLYPH):
        for i, ch in enumerate(row):
            if ch == "#":
                cv.dot(cx - 2.5 * scale + i * scale + scale * 0.5, cy - 2.5 * scale + j * scale + scale * 0.5, CORE if glow else ACCENT, scale)


def draw_seal(cv, f, n, band, el):
    cx, gy = 32.0, 52.0
    s = 9 + band
    if f <= 2:
        u = ease_in((f + 1) / 3.5)
        y = lerp(6.0, gy - s - 6, u)
        seal_face(cv, cx, y, s * (0.8 + 0.2 * u), False)
        cv.paint(cv.mask_polygon([(cx - s * 0.6, y - s - 10), (cx + s * 0.6, y - s - 10), (cx + s * 0.8, y - s), (cx - s * 0.8, y - s)]), HAZE, "under")
        cv.ring(cx, gy, 6 + f * 3, 1.0, DEEP, 0.3)
        return
    u = (f - 3) / (n - 4)
    y = gy - s - 6
    if f == 3:
        seal_face(cv, cx, y, s, True)
        cv.rim(INK, of=(BASE, LIGHT, DEEP))
        star(cv, cx, gy - 2, 12 + band * 3, points=8, w=2.0)
        cv.ring(cx, gy, 14, 2.0, GLINT, 0.3)
        ring_burst(cv, el, cx, gy, 8, 0, 4, band, 271, count=8, sy=0.3, rise=1.5, life=3)
        return
    seal_face(cv, cx, y, s, u < 0.5 and f % 2 == 0)
    cv.rim(INK, of=(BASE, LIGHT, DEEP))
    cv.ring(cx, gy, 14 + u * 10, 1.0, LIGHT if u < 0.5 else DEEP, 0.3)
    # the four ticks of the seal's binding, turning
    for i in range(4):
        a = i * math.pi / 2 + u * 1.2
        d = s + 5 + math.sin(u * 4) * 1.5
        p0 = (cx + math.cos(a) * d, y + math.sin(a) * d)
        p1 = (cx + math.cos(a) * (d + 3), y + math.sin(a) * (d + 3))
        cv.line1(p0, p1, GLINT if u < 0.6 else DEEP)
    ring_burst(cv, el, cx, gy, 8, f - 3, n - 3, band, 271, count=8, sy=0.3, rise=1.5, life=3)
    ground_ripple(cv, el, cx, gy, 12 + band * 2, f, n, band, 0.3) if u < 0.7 else None


# ------------------------------------------------------------------------------------------ 23 domain
def draw_domain(cv, f, n, band, el):
    cx, gy = 56.0, 48.0
    R, sy = 52.0, 0.34
    r2 = R * 0.66
    if f <= 3:
        u = ease_out((f + 1) / 4.0)
        cv.ring(cx, gy, R, 2.0 * W[band], LIGHT, sy, a0=-math.pi / 2, a1=-math.pi / 2 + 2 * math.pi * u)
        cv.ring(cx, gy, r2, 1.5, BASE, sy, a0=math.pi / 2, a1=math.pi / 2 + 2 * math.pi * u)
        cv.dot(cx + math.cos(-math.pi / 2 + 2 * math.pi * u) * R, gy + math.sin(-math.pi / 2 + 2 * math.pi * u) * R * sy, CORE, 2)
        if f == 3:
            star(cv, cx, gy - 10, 8 + band * 2, points=4, w=1.5)
        return
    u = (f - 4) / (n - 5)
    dim = f >= n - 2
    cv.paint(cv.mask_ellipse(cx, gy, R - 1, (R - 1) * sy), HAZE, "under") if not dim else None
    cv.ring(cx, gy, R, 2.0 * W[band], LIGHT if not dim else DEEP, sy)
    cv.ring(cx, gy, R - 2, 1.0, GLINT if not dim else DEEP, sy)
    cv.ring(cx, gy, r2, 1.5, BASE if not dim else DEEP, sy)
    # eight bars between the rings, turning
    for i in range(8):
        a = i * math.pi / 4 + f * 0.13
        p0 = (cx + math.cos(a) * (r2 + 3), gy + math.sin(a) * (r2 + 3) * sy)
        p1 = (cx + math.cos(a) * (R - 4), gy + math.sin(a) * (R - 4) * sy)
        cv.stroke_seg(p0, p1, 2.0, 2.0, table=((0.6, LIGHT), (1.0, DEEP)) if not dim else ((1.0, DEEP),))
        if i % 2 == 0 and band:
            q0 = (cx + math.cos(a + 0.12) * (r2 + 5), gy + math.sin(a + 0.12) * (r2 + 5) * sy)
            q1 = (cx + math.cos(a + 0.12) * (R - 6), gy + math.sin(a + 0.12) * (R - 6) * sy)
            cv.line1(q0, q1, DEEP)
    # the faint dome, a few motes drifting up inside it
    if band and not dim:
        cv.stroke_arc(cx, gy, R - 4, math.pi, 2 * math.pi, 1.0, 1.0, sy=0.75, table=((1.0, DEEP),))
    for i in range(5 + band * 3):
        uu = ((f * 0.09) + px_hash(i, 281)) % 1.0
        x = cx + (px_hash(i, 282) - 0.5) * R * 1.4
        y = gy - 2 - uu * 30
        particle(cv, el, x, y, 0, -0.5, uu, i)
    ground_ripple(cv, el, cx, gy, R * 0.5 + (u * 10 % 10), f, n, band, sy) if not dim else None


# ------------------------------------------------------------------------------------------ 24 echo
def draw_echo(cv, f, n, band, el):
    if f <= 5:
        draw_strike(cv, f, 6, band, el, cx=14.0, cy=34.0, r=28.0, seed=3)
        return
    # the ghost strike: the same arc again, a step forward, half there
    g = f - 6
    gcv = Canvas(cv.w, cv.h)
    draw_strike(gcv, min(3, g), 6, band, el, cx=20.0, cy=34.0, r=26.0, seed=4)
    ghost = gcv.idx
    body = ghost > 0
    tone = (BASE, LIGHT, DEEP, DEEP, HAZE, HAZE)[min(5, g)]
    cv.paint(body & ((cv.X.astype(int) + cv.Y.astype(int)) % 2 == 0), tone, "under")
    cv.paint(body & ((cv.X.astype(int) + cv.Y.astype(int)) % 2 == 1) & (ghost >= LIGHT), GLINT if g < 3 else DEEP, "under")
    if g == 3:
        cv.ring(20 + 26 * math.cos(1.05), 34 + 26 * math.sin(1.05), 5, 1.0, GLINT)
    if g >= 3:
        cv.ring(20 + 26 * math.cos(1.05), 34 + 26 * math.sin(1.05), 5 + (g - 3) * 5, 1.0, DEEP)


# ------------------------------------------------------------------------------------------ bolts (looping projectiles)
def bolt_arc(cv, f, n, band, el):
    cx, cy = 36.0, 12.0
    crescent(cv, cx, cy, 10, 4.0 * W[band], span=1.2)
    for i in range(3):
        yy = cy - 5 + i * 5
        cv.line1((cx - 20 - i * 3 - (f % 2) * 2, yy), (cx - 8, yy), DEEP if i % 2 else HAZE)
    dress_edge(cv, el, arc_pts(cx - 5, cy, 11, -1.1, 1.1, count=7), f, n, band, 301, every=3)


def bolt_volley(cv, f, n, band, el):
    hx, hy = 40.0, 12.0
    cv.stroke_seg((hx - 22, hy), (hx - 2, hy), 1.0, 3.5 * W[band])
    cv.polygon([(hx - 4, hy - 2), (hx + 3, hy), (hx - 4, hy + 2)], CORE)
    for i in range(2 + band):
        cv.line1((hx - 30 - i * 4 - (f % 2) * 2, hy - 3 + i * 3), (hx - 22 - i * 4, hy - 3 + i * 3), DEEP)
    dress_edge(cv, el, seg_pts((hx - 18, hy), (hx - 4, hy), 5, side=-1.0), f, n, band, 311, every=2)


def bolt_seeker(cv, f, n, band, el):
    hx, hy = 38.0, 12.0
    pts = [(hx - j * 4, hy + math.sin(f * 1.5 + j * 0.9) * (2.5 + band)) for j in range(8 + band * 2)]
    cv.stroke_poly(pts, 3.0 * W[band], 1.0, table=STROKE_BANDS)
    cv.disc(hx, hy, 3 + band * 0.5, table=GLOW_BANDS)
    cv.dot(hx, hy, CORE, 2)
    dress_edge(cv, el, [(p[0], p[1], 0.0, -1.0 if j % 2 else 1.0) for j, p in enumerate(pts[1:])], f, n, band, 321, every=3)


def bolt_return(cv, f, n, band, el):
    cx, cy = 34.0, 12.0
    ang = f * math.pi / 4
    cv.stroke_arc(cx, cy, 7, ang - 2.4, ang - 0.4, 1.0, 3.0 * W[band], table=THIN_BANDS)
    blade(cv, cx, cy, ang, 14, 3.0)
    cv.rim(INK, of=(BASE, LIGHT, GLINT))
    for i in range(2 + band):
        cv.line1((cx - 18 - i * 4, cy - 3 + i * 3), (cx - 10 - i * 4, cy - 3 + i * 3), DEEP)
    dress_edge(cv, el, arc_pts(cx, cy, 9, ang - 2.2, ang - 0.6, count=5), f, n, band, 331, every=2)


# ------------------------------------------------------------------------------------------ the table
FORMS = {
    "strike": dict(fit=True, draw=draw_strike, cell=(64, 64), anchor=(14, 34), frames=8, fps=14, impact=3, span=32, at="chest", size="band"),
    "flurry": dict(fit=True, draw=draw_flurry, cell=(64, 48), anchor=(10, 24), frames=10, fps=16, impact=2, span=50, at="chest", size="band"),
    "thrust": dict(draw=draw_thrust, cell=(96, 32), anchor=(4, 16), frames=8, fps=14, impact=3, span=88, at="chest", size="stretch"),
    "lunge": dict(fit=True, draw=draw_lunge, cell=(120, 48), anchor=(70, 22), frames=8, fps=14, impact=3, span=44, at="chest", size="band"),
    "sweep": dict(draw=draw_sweep, cell=(96, 48), anchor=(48, 36), frames=8, fps=12, impact=3, span=88, at="feet", size="reach"),
    "arc": dict(draw=draw_arc, cell=(96, 64), anchor=(16, 32), frames=8, fps=14, impact=2, span=60, at="chest", size="band",
                bolt=dict(draw=bolt_arc, cell=(48, 24), anchor=(38, 12), frames=4, fps=12)),
    "volley": dict(draw=draw_volley, cell=(96, 48), anchor=(10, 24), frames=8, fps=14, impact=2, span=60, at="chest", size="band",
                   bolt=dict(draw=bolt_volley, cell=(48, 24), anchor=(40, 12), frames=4, fps=12)),
    "rain": dict(draw=draw_rain, cell=(64, 96), anchor=(32, 88), frames=10, fps=12, impact=5, span=64, at="feet", size="tile"),
    "pillar": dict(draw=draw_pillar, cell=(48, 112), anchor=(24, 104), frames=10, fps=12, impact=3, span=100, at="target", size="band"),
    "wave": dict(draw=draw_wave, cell=(64, 48), anchor=(32, 40), frames=8, fps=12, impact=3, span=40, at="feet", size="travel"),
    "burst": dict(draw=draw_burst, cell=(96, 64), anchor=(48, 48), frames=8, fps=12, impact=2, span=92, at="feet", size="reach"),
    "seeker": dict(draw=draw_seeker, cell=(96, 48), anchor=(12, 24), frames=8, fps=14, impact=2, span=60, at="chest", size="band",
                   bolt=dict(draw=bolt_seeker, cell=(48, 24), anchor=(38, 12), frames=4, fps=12)),
    "return": dict(draw=draw_return, cell=(96, 48), anchor=(14, 24), frames=10, fps=12, impact=3, span=60, at="chest", size="band",
                   bolt=dict(draw=bolt_return, cell=(48, 24), anchor=(34, 12), frames=4, fps=12)),
    "snare": dict(draw=draw_snare, cell=(80, 56), anchor=(40, 48), frames=10, fps=12, impact=4, span=60, at="target", size="band"),
    "counter": dict(draw=draw_counter, cell=(48, 64), anchor=(24, 30), frames=6, fps=14, impact=1, span=40, at="chest", size="band"),
    "ward": dict(draw=draw_ward, cell=(80, 80), anchor=(40, 68), frames=10, fps=12, impact=4, span=68, at="feet", size="band"),
    "chorus": dict(draw=draw_chorus, cell=(96, 64), anchor=(48, 52), frames=10, fps=12, impact=3, span=88, at="feet", size="reach"),
    "blink": dict(fit=True, draw=draw_blink, cell=(96, 48), anchor=(80, 20), frames=8, fps=14, impact=4, span=24, at="target_chest", size="band"),
    "plunge": dict(draw=draw_plunge, cell=(96, 56), anchor=(48, 44), frames=8, fps=12, impact=2, span=92, at="feet", size="reach"),
    "release": dict(draw=draw_release, cell=(64, 80), anchor=(32, 44), frames=10, fps=12, impact=4, span=60, at="chest", size="band"),
    "swarm": dict(draw=draw_swarm, cell=(96, 64), anchor=(48, 30), frames=10, fps=12, impact=3, span=80, at="chest", size="band"),
    "seal": dict(draw=draw_seal, cell=(64, 64), anchor=(32, 52), frames=10, fps=12, impact=3, span=56, at="target", size="band"),
    "domain": dict(draw=draw_domain, cell=(112, 64), anchor=(56, 48), frames=12, fps=10, impact=3, span=104, at="feet", size="reach"),
    "echo": dict(fit=True, draw=draw_echo, cell=(64, 64), anchor=(14, 34), frames=12, fps=14, impact=3, span=32, at="chest", size="band"),
}
ORDER = list(FORMS.keys())
