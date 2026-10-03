"""The 24 technique forms (docs/technique_plan.md §3.2) redrawn for the top-down world (decision 38), on the ground
plane in the world's own 3/4 view (plane.py): every form is geometry on the floor and in the air over it, projected
for each of the five drawn directions, never a side-view sprite turned on the screen.

The look rule (decision 38): only the feel comes from the reference game. Every form reads as wuxia: sword-light arcs
and qi trails, ink strokes, jade and gold qi, the element's Dao image (elements.py's flourishes and wuxia.py's
motifs: water ripples, wind petals, thunder talismans, fire lotus, earth stone, metal sword-qi), sword formations,
bagua and talisman seals.

A drawer is `draw(pl, f, n, band, el)`: frame f of n on the Plane `pl` (its canvas, its anchor on the floor and its
direction), at richness band 0-2 and element `el`. TD_FORMS holds each form's spec for build_fx_topdown.py:

  canvas   the drawing canvas (art px) before the build crops it; anchor the floor point in it
  frames, fps, impact   as the side view's sheets (the impact frame lands on the pose's hit frame)
  span     the art px of reach the drawing represents (the game scales by whole steps to the technique's reach)
  at       feet (the caster's) or target (the foe's feet, or the point a circle lands on)
  layer    sorted (upright: sorts with the bodies at its anchor) or floor (flat: under every body inside it)
  dirs     drawn in the five directions (True) or once (False: round forms)
  size     reach (scaled to the reach), travel (moves along the reach over its life) or fixed
  bolt     the projectile's loop for a thrown form (its own canvas, anchor at its head, dirs)
"""
from __future__ import annotations

import math

from elements import dress_edge, fling, ground_ripple, particle, ring_burst
from forms import FADE_BANDS, THIN_BANDS, W, star, tendril
from fxpix import (ACCENT, BASE, CORE, DEEP, GLINT, GLOW_BANDS, HAZE, INK, LIGHT, STROKE_BANDS, ease_in, ease_out, lerp,
                   px_hash)
from plane import Plane
from wuxia import motif, sword_sliver, talisman

H = 17.0          # the hand's height over the floor (art px): a blade's path (decision 43: the 46 px figure's)
CHEST = 26.0      # the chest's (a cast's gathering)


def _fade_table(u: float):
    return STROKE_BANDS if u < 0.35 else (THIN_BANDS if u < 0.7 else ((1.0, DEEP),))


def ground_trace(pl: Plane, pts3: list, idx=HAZE) -> None:
    """The mark a stroke leaves on the floor under it: its path dropped to the ground, dithered (it reads the
    direction of a blow even where the stroke is seen edge-on)."""
    pts = [pl.pt(f, l, 0.0) for f, l in pts3]
    for i in range(len(pts) - 1):
        pl.cv.line1(pts[i], pts[i + 1], idx)


# ------------------------------------------------------------------------------------------ 1 strike
def td_strike(pl, f, n, band, el, R=34.0, seed=1, a0=1.2, a1=-1.15, tilt=0.45, f0=0.0):
    """A sword-light crescent round the body at the hand's height, from high on the right down across the front."""
    cv = pl.cv
    w = 6.0 * W[band]
    centre = pl.pt(f0, 0, H)
    if f == 0:
        x, y = pl.arc(R, a0, a0, H, tilt, n=1, f0=f0)[0]
        star(cv, x, y, 4 + band, points=4, w=1.5)
        return
    if f <= 3:
        head = lerp(a0, a1, ease_out(f / 3.0))
        prev = lerp(a0, a1, ease_out((f - 1) / 3.0))
        path = pl.arc(R, a0, head, H, tilt, 18, f0=f0)
        pl.sweep_haze(pl.arc(R + w * 0.3, prev + 0.15, head, H, tilt, 10, f0=f0), centre, w * 0.9)
        pl.stroke(path, w * 0.3, w)
        pl.stroke(pl.arc(R, max(head, head + 0.5) if a1 < a0 else head - 0.5, head, H, tilt, 6, f0=f0), w * 0.8, w * 1.05)
        dress_edge(cv, el, pl.outward(pl.arc(R + w * 0.5, a0 - 0.2, head, H, tilt, 10, f0=f0), centre), f, n, band, seed)
        if f == 3:
            x, y = pl.arc(R, a1, a1, H, tilt, n=1, f0=f0)[0]
            star(cv, x, y, 6 + band * 2, points=4, w=2.0)
            if band:
                ground_trace(pl, [(f0 + R * math.cos(a), R * math.sin(a) * math.cos(tilt)) for a in (lerp(a0, a1, k / 8) for k in range(9))])
    else:
        u = (f - 3) / (n - 4)
        tail = lerp(a0, a1, u * 0.85)
        pl.stroke(pl.arc(R, tail, a1, H, tilt, 14, f0=f0), w * 0.4 * (1 - u), w * (1 - u * 0.7), _fade_table(u))
        if u < 0.6:
            dress_edge(cv, el, pl.outward(pl.arc(R + w * 0.5, tail, a1, H, tilt, 8, f0=f0), centre), f, n, band, seed, every=4)
    fling(cv, el, pl.outward(pl.arc(R, lerp(a0, a1, 0.5), a1, H, tilt, 6, f0=f0), centre), f, n, band, seed, count=5, start=2, life=4, speed=2.4)


# ------------------------------------------------------------------------------------------ 2 flurry
def td_flurry(pl, f, n, band, el):
    """Three quick cuts across the front, each a short sword-light stroke; the third, straight across, lands hardest."""
    cv = pl.cv
    w = 5.5 * W[band]
    cuts = [((18, -14, H + 8), (30, 12, H - 6), 1), ((16, 14, H - 4), (32, -12, H + 10), 4), ((22, -16, H + 1), (26, 16, H + 1), 7)]
    for si, (p0, p1, at) in enumerate(cuts):
        u = f - at
        if u < 0 or u > 3:
            continue
        a, b = pl.pt(*p0), pl.pt(*p1)
        mid = (lerp(a[0], b[0], 0.55), lerp(a[1], b[1], 0.55))
        if u == 0:
            cv.stroke_seg(a, mid, w * 0.4, w * 1.1)
        elif u == 1:
            cv.stroke_seg(a, b, w * 0.35, w * (1.15 if si == 2 else 1.0))
            pl.sweep_haze([a, b], pl.pt(0, 0, H), w * 0.8)
            star(cv, b[0], b[1], 5 + band + (3 if si == 2 else 0), points=4, w=1.5)
            dress_edge(cv, el, pl.side([a, mid, b], -1.0), f, n, band, 21 + si, every=1)
        elif u == 2:
            cv.stroke_seg(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), b, w * 0.3, w * 0.75, table=THIN_BANDS)
            fling(cv, el, pl.side([mid, b], -1.0), 1, 4, band, 31 + si, count=4, start=0, life=2, speed=2.2)
        else:
            cv.stroke_seg(mid, b, 1.0, w * 0.4, table=((1.0, DEEP),))
            fling(cv, el, pl.side([mid, b], -1.0), 2, 4, band, 31 + si, count=4, start=0, life=2, speed=2.2)


# ------------------------------------------------------------------------------------------ 3 thrust
def td_thrust(pl, f, n, band, el, L=64.0):
    """A line of sword-qi driven along the floor at the hand's height, a spiral ribbon of qi round it."""
    cv = pl.cv
    w = 5.0 * W[band]
    tipf = lerp(8.0, L, ease_out(min(3, f) / 3.0))
    if f <= 3:
        pl.stroke(pl.line(4, tipf - 4, 0, H, 8), w * 0.35, w)
        cv.polygon([pl.pt(tipf - 6, -w * 0.5, H), pl.pt(tipf + 4, 0, H), pl.pt(tipf - 6, w * 0.5, H)], LIGHT)
        cv.polygon([pl.pt(tipf - 4, -w * 0.25, H), pl.pt(tipf + 3, 0, H), pl.pt(tipf - 4, w * 0.25, H)], CORE)
        # the qi ribbon spiralling round the line
        rib = [pl.pt(x, math.sin(x * 0.3 + f * 1.3) * (3 + band), H + math.cos(x * 0.3 + f * 1.3) * (3 + band)) for x in range(8, int(tipf) - 4, 2)]
        pl.stroke(rib, 1.0, 2.0 + band * 0.5, THIN_BANDS, "under")
        dress_edge(cv, el, pl.side(pl.line(10, tipf - 6, 0, H, 8), 1.0) + pl.side(pl.line(10, tipf - 6, 0, H, 8), -1.0), f, n, band, 41, every=4)
        if f == 3:
            x, y = pl.pt(L - 1, 0, H)
            star(cv, x, y, 7 + band * 2, points=8, w=1.5)
            pl.ring(5, 1.0, GLINT, H, L - 1)
    else:
        u = (f - 3) / (n - 4)
        start = lerp(10.0, L - 14.0, u)
        pl.stroke(pl.line(start, L - 4, 0, H, 6), w * 0.3 * (1 - u), w * (1 - u * 0.6), THIN_BANDS if u < 0.5 else ((1.0, DEEP),))
        if u < 0.6:
            pl.ring(4 + u * 7, 1.0, LIGHT if u < 0.3 else DEEP, H, L - 1)
        fling(cv, el, pl.side(pl.line(L - 10, L - 2, 0, H, 4), 1.0) + pl.side(pl.line(L - 10, L - 2, 0, H, 4), -1.0),
              f - 3, n - 3, band, 43, count=6, start=0, life=4, speed=2.0)
    if band and 3 <= f <= 5:
        ground_trace(pl, [(x, 0.0) for x in range(6, int(L), 6)])


# ------------------------------------------------------------------------------------------ 4 lunge
def td_lunge(pl, f, n, band, el, hit=44.0):
    """The body dashes along the floor (afterimages in its robe's silhouette, dust at the feet) into a blow ahead."""
    cv = pl.cv
    lean = pl.c * 0.22
    if f <= 3:
        u = f / 3.0
        for i in range(3):
            fd = lerp(0.0, 26.0, i / 2.0) + u * 8.0
            x, y = pl.pt(fd, 0, 0)
            tone = (HAZE, DEEP, BASE)[min(2, i + (1 if u > 0.6 else 0))] if i + f < 5 else HAZE
            cv.figure(x, y, 30, tone, lean=lean)
        for i in range(3 + band * 2):
            lo = (i - (2 + band)) * 3.5
            pl.stroke(pl.line(2 + px_hash(i, 5) * 10 + u * 14, 14 + u * 16, lo, 8 + (i % 3) * 7, 2), 1.0, 1.0, ((1.0, LIGHT if i % 2 else DEEP),))
        for i in range(3):
            x, y = pl.pt(2 + i * 6 + u * 8, (i - 1) * 3, 0)
            cv.dot(x, y, HAZE, 2)
        if f == 3:
            x, y = pl.pt(hit, 0, H)
            star(cv, x, y, 9 + band * 3, points=8, w=2.5)
            pl.ring(7, 1.5, GLINT, H, hit)
            pl.stroke(pl.line(30, hit - 6, 0, H, 4), 2.0, 5.5 * W[band])
    else:
        u = (f - 3) / (n - 4)
        if u < 0.5:
            x, y = pl.pt(34, 0, 0)
            cv.figure(x, y, 30, HAZE, lean=lean)
        x, y = pl.pt(hit, 0, H)
        star(cv, x, y, (9 + band * 3) * (1 - u), points=8, w=2.0)
        pl.ring(7 + u * 12, 1.5 if u < 0.5 else 1.0, LIGHT if u < 0.5 else DEEP, H, hit)
        fling(cv, el, pl.outward([pl.pt(hit + math.cos(a) * 6, math.sin(a) * 6, H) for a in (-1.0, -0.3, 0.3, 1.0)], (x, y)),
              f - 3, n - 3, band, 45, count=6, start=0, life=4)


# ------------------------------------------------------------------------------------------ 5 sweep
def td_sweep(pl, f, n, band, el, R=40.0):
    """A low sweep skimming the floor round the front, throwing up dust and the element along its edge."""
    cv = pl.cv
    w = 6.0 * W[band]
    a0, a1 = -1.55, 1.55
    centre = pl.pt(0, 0, 2)
    if f <= 3:
        head = lerp(a0, a1, ease_out(f / 3.0))
        path = pl.arc(R, a0, head, 3, 0.0, 20)
        pl.sweep_haze(pl.arc(R + 2, a0, head, 3, 0.0, 14), centre, w * 1.2)
        pl.stroke(path, w * 0.4, w)
        dress_edge(cv, el, pl.outward(pl.arc(R + 2, a0, head, 3, 0.0, 12), centre), f, n, band, 61, every=3)
        for x, y, nx, ny in pl.outward(pl.arc(R + 2, a0, head, 0, 0.0, 12), centre)[::3]:
            cv.dot(x + nx * 3, y + ny * 3 - 2, HAZE, 2)
        if f == 3:
            x, y = pl.arc(R, a1, a1, 3, n=1)[0]
            star(cv, x, y, 5 + band * 2, points=4, w=1.5)
    else:
        u = (f - 3) / (n - 4)
        tail = lerp(a0, a1 - 0.3, u)
        pl.stroke(pl.arc(R, tail, a1, 3, 0.0, 14), w * 0.3 * (1 - u), w * (1 - u * 0.7), _fade_table(u))
        x, y = pl.pt(0, 0, 0)
        ring_burst(cv, el, x, y, R * 0.85, f - 3, n - 3, band, 62, count=8, sy=1.0, rise=0.5, life=4)
        if u < 0.6:
            for k in range(3 + band):
                gx, gy = pl.pt(R * math.cos(lerp(a0, a1, (k + 0.5) / (3 + band))), R * math.sin(lerp(a0, a1, (k + 0.5) / (3 + band))), 0)
                ground_ripple(cv, el, gx, gy, 6, f, n, band, 1.0)


# ------------------------------------------------------------------------------------------ 6 arc
def crescent(pl, fc, r, w, h=H, span=1.25, table=STROKE_BANDS):
    """A crescent of sword-qi lying nearly flat, convex forward, its tips at forward `fc` - r*0.5."""
    pl.stroke(pl.arc(r, -span, span, h, 0.35, 16, f0=fc - r), w * 0.3, w * 0.3, ((0.6, LIGHT), (1.0, BASE)))
    pl.stroke(pl.arc(r, -span * 0.6, 0.0, h, 0.35, 8, f0=fc - r), w * 0.35, w, table)
    pl.stroke(pl.arc(r, 0.0, span * 0.6, h, 0.35, 8, f0=fc - r), w, w * 0.35, table)


def td_arc(pl, f, n, band, el):
    """A crescent of qi forms before the body and flies out along the floor, a wake behind it."""
    cv = pl.cv
    w = 5.5 * W[band]
    if f <= 2:
        u = (f + 1) / 3.0
        crescent(pl, 12 + 6 * u, 6 + 10 * u, w * u)
        if f == 2:
            x, y = pl.pt(18, 0, H)
            star(cv, x, y, 6 + band * 2, points=4, w=1.5)
        dress_edge(cv, el, pl.outward(pl.arc(10 * u + 2, -1.1, 1.1, H, 0.35, 9, f0=18 - 10 * u), pl.pt(0, 0, H)), f, n, band, 71, every=3)
    elif f <= 5:
        u = (f - 2) / 3.0
        fc = 18 + ease_in(u) * 44
        crescent(pl, fc, 16, w)
        for i in range(3 + band):
            lo = -9 + i * (18 / (2 + band))
            pl.stroke(pl.line(max(8, fc - 30 - i * 4), fc - 12, lo, H, 2), 1.0, 1.0, ((1.0, HAZE if i % 2 else DEEP),))
        dress_edge(cv, el, pl.outward(pl.arc(18, -1.1, 1.1, H, 0.35, 9, f0=fc - 16), pl.pt(fc - 30, 0, H)), f, n, band, 72, every=3)
    else:
        u = (f - 5) / max(1, n - 6)
        for i in range(3 + band):
            lo = -9 + i * (18 / (2 + band))
            pl.stroke(pl.line(34 + u * 18, 58 + u * 8, lo, H, 2), 1.0, 1.0, ((1.0, DEEP if u < 0.5 else HAZE),))


def bolt_arc(pl, f, n, band, el):
    w = 4.0 * W[band]
    crescent(pl, 0, 12, w)
    for i in range(3):
        lo = -6 + i * 6
        pl.stroke(pl.line(-28 - (f % 2) * 2 - i * 3, -12, lo, H, 2), 1.0, 1.0, ((1.0, DEEP if i % 2 else HAZE),))
    dress_edge(pl.cv, el, pl.outward(pl.arc(13, -1.1, 1.1, H, 0.35, 7, f0=-12), pl.pt(-20, 0, H)), f, n, band, 301, every=3)


# ------------------------------------------------------------------------------------------ 7 volley
def dart(pl, fd, lo, w, h=H):
    pl.stroke([pl.pt(fd - 16, lo, h), pl.pt(fd - 2, lo, h)], 1.0, w)
    pl.cv.polygon([pl.pt(fd - 4, lo - 2, h), pl.pt(fd + 3, lo, h), pl.pt(fd - 4, lo + 2, h)], CORE)


def td_volley(pl, f, n, band, el):
    """Two to four darts of qi loosed in a fan from the hand, a puff of qi where they leave."""
    cv = pl.cv
    fan = (-0.26, 0.0, 0.26) if band < 2 else (-0.36, -0.12, 0.12, 0.36)
    hx, hy = pl.pt(6, 0, H)
    if f <= 1:
        star(cv, hx, hy, 5 + f * 3 + band * 2, points=8, w=2.0)
        return
    u = (f - 2) / max(1, n - 3)
    if f <= 3:
        star(cv, hx, hy, (9 + band * 2) * (1 - u), points=8, w=2.0)
    for i, a in enumerate(fan):
        d = lerp(10.0, 66.0, ease_out((f - 2 + i * 0.15) / 3.5))
        fd, lo = 6 + math.cos(a) * d, math.sin(a) * d
        if d < 62:
            dart(pl, fd, lo, 4.0 * W[band])
            dress_edge(cv, el, pl.side([pl.pt(fd - 14, lo, H), pl.pt(fd - 3, lo, H)], -1.0 if i % 2 else 1.0), f, n, band, 81 + i, every=1)
    if 2 <= f <= 6:
        for i in range(3 + band):
            x, y = pl.pt(2 - u * 5 + px_hash(i, 4) * 6, (px_hash(i, 6) - 0.5) * 10, H - 2 + u * 4)
            cv.dot(x, y, HAZE, 2)


def bolt_volley(pl, f, n, band, el):
    dart(pl, 0, 0, 3.5 * W[band])
    for i in range(2 + band):
        pl.stroke(pl.line(-26 - i * 4 - (f % 2) * 2, -18 - i * 4, -3 + i * 3, H, 2), 1.0, 1.0, ((1.0, DEEP),))
    dress_edge(pl.cv, el, pl.side(pl.line(-14, -4, 0, H, 5), -1.0), f, n, band, 311, every=2)


# ------------------------------------------------------------------------------------------ 8 rain
def td_rain(pl, f, n, band, el, R=26.0):
    """A rain of qi needles falling on a circle of floor: each lands with the element's crown and a ring."""
    cv = pl.cv
    count = (9, 12, 16)[band]
    top = 70.0
    for i in range(count):
        a, rr = px_hash(i, 91) * 2 * math.pi, R * math.sqrt(px_hash(i, 93))
        gf, gl = math.cos(a) * rr, math.sin(a) * rr
        born = int(px_hash(i, 92) * 5)
        u = f - born
        if u < 0:
            continue
        h = top - u * 24.0
        if h > 0:
            L = 14 + band * 4
            head = pl.pt(gf, gl, h)
            tail = pl.pt(gf, gl, h + L)
            tail = (tail[0] - L * 0.18, tail[1])
            cv.stroke_seg(tail, head, 1.0, 3.0 * W[band] * 0.75)
            cv.polygon([(head[0] - 1.5, head[1] - 3), (head[0] + 1.5, head[1] - 3), (head[0], head[1] + 1)], CORE)
        else:
            age = -h / 24.0
            if age <= 3.0:
                k = min(1.0, age / 3.0)
                x, y = pl.pt(gf, gl, 0)
                motif(cv, el, x, y - 2, 5 + band, k, i)
                cv.ring(x, y, 2 + k * 5, 1.0, LIGHT if k < 0.5 else DEEP)
                if k < 0.4:
                    star(cv, x, y - 2, 2 + band, points=4, w=1.0)
    if f >= 4:
        x, y = pl.pt(0, 0, 0)
        cv.ring(x, y, R + 2, 1.0, DEEP if f > 7 else LIGHT)


# ------------------------------------------------------------------------------------------ 9 pillar
def td_pillar(pl, f, n, band, el):
    """A column of light rises from a rune circle on the floor under the foe."""
    cv = pl.cv
    gx, gy = pl.pt(0, 0, 0)
    top = gy - 96.0
    wmax = (10.0, 13.0, 16.0)[band]
    col = ((0.2, CORE), (0.5, LIGHT), (0.8, BASE), (1.0, DEEP))
    # the rune circle: a ring with eight ticks, drawn first so the column stands on it
    rr = 12 + band * 2
    cv.ring(gx, gy, rr, 1.0, LIGHT if f < 7 else DEEP)
    for i in range(8):
        a = i * math.pi / 4 + f * 0.12
        cv.line1((gx + math.cos(a) * (rr - 3), gy + math.sin(a) * (rr - 3)), (gx + math.cos(a) * (rr + 1), gy + math.sin(a) * (rr + 1)), GLINT if i % 2 else DEEP)
    if f <= 2:
        u = ease_out((f + 1) / 3.0)
        h = (gy - top) * u
        w = wmax * (0.5 + 0.5 * u)
        cv.stroke_seg((gx, gy), (gx, gy - h), w, w * 0.6, table=col)
        star(cv, gx, gy - h, w * 0.5, points=4, w=1.5)
    elif f <= 6:
        u = (f - 3) / 3.0
        pulse = 1.0 + 0.12 * math.sin(f * 2.1)
        cv.stroke_seg((gx, gy), (gx, top), wmax * pulse, wmax * 0.7, table=col)
        star(cv, gx, top + 2, wmax * 0.5 * pulse, points=4, w=1.5)
        if f == 3:
            star(cv, gx, gy - 6, 9 + band * 3, points=8, w=2.0)
        for i in range(4 + band * 3):
            y = gy - ((f * 9 + px_hash(i, 101) * 90) % (gy - top))
            cv.dot(gx + (px_hash(i, 102) - 0.5) * wmax * 1.4, y, GLINT if i % 2 else ACCENT)
        edge = [(gx + wmax * 0.5, y, 1.0, 0.0) for y in range(int(top + 8), int(gy - 8), 8)] + \
               [(gx - wmax * 0.5, y, -1.0, 0.0) for y in range(int(top + 8), int(gy - 8), 8)]
        dress_edge(cv, el, edge, f, n, band, 111, every=2)
        ground_ripple(cv, el, gx, gy, rr + 4, f, n, band, 1.0)
    else:
        u = (f - 7) / max(1, n - 8)
        w = wmax * (1 - u * 0.8)
        cv.stroke_seg((gx, gy - u * 30), (gx, top), w, w * 0.5, table=THIN_BANDS if u < 0.5 else ((1.0, DEEP),))


# ------------------------------------------------------------------------------------------ 10 wave
def td_wave(pl, f, n, band, el, half=16.0):
    """A crest of the element rolling along the floor: the side view's crest (a long back slope, a steep face, a lip
    curling over) drawn as a solid across the direction, slice by slice from the far side to the near, lit on its lip,
    spray ahead of it and the floor it passed left in haze. The game moves it along the reach."""
    cv = pl.cv
    hmax = (16.0, 19.0, 22.0)[band]
    k = ease_out((f + 1) / 2.5) if f < 2 else (1.0 if f < 6 else 1.0 - (f - 5) / (n - 5) * 0.8)
    roll = (f % 4) / 4.0
    cv.paint(cv.mask_polygon([pl.pt(-30, -half * 0.8, 0), pl.pt(-8, -half, 0), pl.pt(-8, half, 0), pl.pt(-30, half * 0.8, 0)]), HAZE, "dither")
    slices = [-half + i for i in range(int(2 * half) + 1)]   # a slice a pixel, so the crest is solid
    slices.sort(key=lambda l: pl.pt(0, l, 0)[1])      # the far side first, the near side over it
    for si, l in enumerate(slices):
        h = hmax * k * (1.0 - (l / half) ** 2 * 0.6)
        lip = (8 + roll * 3, h * (0.62 - roll * 0.12))
        prof = [(-20, 0), (-11, h * 0.42), (-4, h * 0.86), (1, h), (6, h * 0.96), (10, h * 0.82), (lip[0] + 1, lip[1]),
                (lip[0] - 2, lip[1] - 2), (6, h * 0.5), (9, h * 0.34), (11, h * 0.12), (13, 0)]
        pts = [pl.pt(fw, l, hh) for fw, hh in prof]
        near = si == len(slices) - 1
        cv.polygon(pts, BASE)
        cv.polygon([pl.pt(-4, l, h * 0.86), pl.pt(1, l, h), pl.pt(6, l, h * 0.96), pl.pt(10, l, h * 0.82), pl.pt(lip[0] + 1, l, lip[1]),
                    pl.pt(6, l, h * 0.7), pl.pt(0, l, h * 0.7)], LIGHT)
        cv.polygon([pl.pt(-20, l, 0), pl.pt(-11, l, h * 0.42), pl.pt(-6, l, h * 0.5), pl.pt(-9, l, 0)], DEEP)
        if near or si % 8 == 0:
            cv.line1(pl.pt(1, l, h + 0.5), pl.pt(6, l, h * 0.96 + 0.5), CORE if near else GLINT)
    fling(cv, el, pl.outward([pl.pt(10, l, hmax * k * 0.7) for l in (-half * 0.6, 0.0, half * 0.6)], pl.pt(-6, 0, 0)), f, n, band, 121,
          count=7, start=0, life=3, speed=2.2, gravity=0.5)
    dress_edge(cv, el, pl.outward([pl.pt(2, l, hmax * k) for l in slices[::4]], pl.pt(-4, 0, 0)), f, n, band, 122, every=2)
    if f == 3:
        x, y = pl.pt(10, 0, hmax * 0.5)
        star(cv, x, y, 4 + band, points=4, w=1.0)


# ------------------------------------------------------------------------------------------ 11 burst
def td_burst(pl, f, n, band, el, R=40.0):
    """Qi gathered at the chest bursts out: a ring races over the floor to the reach, a wall of light rising off it,
    the element's motifs thrown round the circle."""
    cv = pl.cv
    gx, gy = pl.pt(0, 0, 0)
    cx, cy = gx, gy - CHEST
    if f <= 1:
        cv.disc(cx, cy, 6 - f * 2, table=GLOW_BANDS)
        cv.ring(gx, gy, 18 - f * 7, 1.5, LIGHT)
        for i in range(6 + band * 2):
            a = i * 2 * math.pi / (6 + band * 2)
            d = 14 - f * 5
            cv.dot(cx + math.cos(a) * d, cy + math.sin(a) * d, GLINT)
        return
    u = (f - 2) / (n - 3)
    r = lerp(12.0, R, ease_out(u * 1.3))
    star(cv, cx, cy, (14 + band * 4) * (1.0 if f == 2 else max(0.0, 1 - u * 1.4)), points=12, w=3.0 if f == 2 else 2.0)
    cv.ring(gx, gy, r, 3.5 * W[band] * (1 - u) + 1.0, LIGHT if u < 0.4 else (BASE if u < 0.75 else DEEP))
    if u < 0.7:
        cv.ring(gx, gy, r - 2, 1.0, GLINT if u < 0.4 else DEEP)
    if band and u < 0.6:
        cv.ring(gx, gy, r * 0.62, 1.0, DEEP)
    if u < 0.6:
        m = 12 + band * 4
        for i in range(m):
            a = i * 2 * math.pi / m + u
            x, y = gx + math.cos(a) * r, gy + math.sin(a) * r
            cv.stroke_seg((x, y), (x, y - (7 + band * 3) * (1 - u)), 2.0, 1.0, table=((0.5, LIGHT), (1.0, BASE)) if u < 0.3 else FADE_BANDS)
    if band and 0.1 < u < 0.8:
        for i in range(4 + band * 2):
            a = i * 2 * math.pi / (4 + band * 2) + 0.4
            motif(cv, el, gx + math.cos(a) * r * 0.8, gy + math.sin(a) * r * 0.8 - 3, 8 + band * 2, u, i, ang=a)
    ring_burst(cv, el, gx, gy, r * 0.8, f - 2, n - 2, band, 131, count=10, sy=1.0, rise=1.2, life=4)
    ground_ripple(cv, el, gx, gy, r * 0.8, f, n, band, 1.0)


# ------------------------------------------------------------------------------------------ 12 seeker
def mote(cv, x, y, band):
    cv.disc(x, y, 2.5 + band * 0.5, table=GLOW_BANDS)
    cv.dot(x, y, CORE, 2)


def td_seeker(pl, f, n, band, el):
    """Motes of qi gather round the hand and fly out along curving paths to find their foes."""
    cv = pl.cv
    m = 3 + (band > 1)
    if f <= 2:
        for i in range(m):
            a = f * 1.1 + i * 2 * math.pi / m
            d = 8 - f * 2
            x, y = pl.pt(6 + math.cos(a) * d, math.sin(a) * d, H + math.sin(a) * 2)
            mote(cv, x, y, band)
        if f == 2:
            x, y = pl.pt(6, 0, H)
            star(cv, x, y, 6 + band * 2, points=4, w=1.5)
        return
    u = (f - 3) / (n - 4)
    for i in range(m):
        curve = (i - (m - 1) / 2) * 9
        trail = []
        for j in range(7 + band * 2):
            uu = max(0.0, u - j * 0.05)
            d = lerp(6.0, 62.0, ease_out(uu * 1.1))
            trail.append(pl.pt(d, curve * math.sin(uu * math.pi * 0.9) + curve * 0.3, H + 6 * math.sin(uu * math.pi)))
        if lerp(6.0, 62.0, ease_out(u * 1.1)) < 58:
            mote(cv, trail[0][0], trail[0][1], band)
            pl.stroke(trail, 2.5, 1.0, ((0.5, LIGHT), (1.0, BASE)) if u < 0.6 else FADE_BANDS)
            dress_edge(cv, el, pl.side(trail[1:], 1.0 if i % 2 else -1.0), f, n, band, 141 + i, every=3)


def bolt_seeker(pl, f, n, band, el):
    trail = [pl.pt(-j * 4, math.sin(f * 1.5 + j * 0.9) * (2.5 + band), H) for j in range(8 + band * 2)]
    pl.stroke(trail, 3.0 * W[band], 1.0)
    mote(pl.cv, trail[0][0], trail[0][1], band)
    dress_edge(pl.cv, el, pl.side(trail[1:], 1.0), f, n, band, 321, every=3)


# ------------------------------------------------------------------------------------------ 13 return
def td_return(pl, f, n, band, el):
    """A blade spun from the hand and thrown out along a bending path; it comes back as the projectile."""
    cv = pl.cv
    hx, hy = pl.pt(6, 0, H)
    if f <= 2:
        cv.stroke_arc(hx, hy, 5 + f * 3, f * 1.6, f * 1.6 + 2.4 + f * 1.2, 2.0, 4.5 * W[band])
        sword_sliver(cv, hx + math.cos(f * 1.6 + 2.4) * 6, hy + math.sin(f * 1.6 + 2.4) * 6, f * 1.6 + 2.4, 10)
        return
    if f <= 5:
        u = (f - 3) / 2.0
        fd = lerp(10, 60, ease_in(u))
        path = [pl.pt(8 + (fd - 8) * k / 7, 6 * math.sin(k / 7 * math.pi) * u, H) for k in range(8)]
        pl.stroke(path, 1.5, 4.5 * W[band])
        pl.sweep_haze(path, pl.pt(0, 8, H), 4)
        x, y = path[-1]
        cv.stroke_arc(x, y, 6, f * 1.3, f * 1.3 + 3.0, 1.5, 3.0, table=THIN_BANDS)
        sword_sliver(cv, x + math.cos(f * 1.3) * 5, y + math.sin(f * 1.3) * 5, f * 1.3, 10)
        dress_edge(cv, el, pl.side(path, -1.0), f, n, band, 151, every=3)
        return
    u = (f - 6) / max(1, n - 7)
    if u < 0.7:
        pl.stroke(pl.line(12 + u * 26, 58, 2, H, 4), 1.0, 3.0, ((1.0, DEEP),))
    cv.ring(hx, hy, 4 + u * 8, 1.0, LIGHT if u < 0.5 else DEEP)


def bolt_return(pl, f, n, band, el):
    cv = pl.cv
    x, y = pl.pt(0, 0, H)
    ang = f * math.pi / 4
    cv.stroke_arc(x, y, 8, ang - 2.4, ang - 0.4, 1.0, 3.0 * W[band], table=THIN_BANDS)
    cv.stroke_arc(x, y, 8, ang + math.pi - 2.4, ang + math.pi - 0.4, 1.0, 3.0 * W[band], table=THIN_BANDS)
    sword_sliver(cv, x + math.cos(ang) * 7, y + math.sin(ang) * 7, ang, 13)
    dress_edge(cv, el, [(x + math.cos(ang - k) * 10, y + math.sin(ang - k) * 10, math.cos(ang - k), math.sin(ang - k)) for k in (0.8, 1.4, 2.0)], f, n, band, 331, every=1)


# ------------------------------------------------------------------------------------------ 14 snare
def td_snare(pl, f, n, band, el, R=24.0):
    """Tendrils of the element (vines, chains, water ropes, lightning) rise from a ring on the floor round the foe and
    knot over it."""
    cv = pl.cv
    gx, gy = pl.pt(0, 0, 0)
    top = (gx, gy - 24.0)
    m = 5 + band
    w = 2.6 * W[band]
    bases = [(gx + math.cos(i * 2 * math.pi / m + 0.4) * R, gy + math.sin(i * 2 * math.pi / m + 0.4) * R) for i in range(m)]
    if f <= 3:
        u = ease_out((f + 1) / 4.5)
        cv.ring(gx, gy, R * min(1.0, (f + 1) / 2.5), 1.5, LIGHT)
        for i, b in enumerate(bases):
            tendril(cv, el, b, top, u * 0.85, band, 161 + i, w)
        ground_ripple(cv, el, gx, gy, R, f, n, band, 1.0)
    elif f <= 7:
        u = 0.85 + 0.15 * min(1.0, (f - 3) / 1.5)
        cv.ring(gx, gy, R, 1.0, DEEP if f > 4 else LIGHT)
        for i, b in enumerate(bases):
            tendril(cv, el, b, top, u, band, 161 + i, w * (1.0 + 0.1 * math.sin(f * 2.0)))
        if f == 4:
            star(cv, top[0], top[1], 7 + band * 2, points=4, w=1.5)
        cv.ring(top[0], top[1], 3 + band, 1.5, GLINT if f < 6 else LIGHT)
    else:
        u = (f - 8) / max(1, n - 9)
        for i, b in enumerate(bases):
            tendril(cv, el, b, (top[0], top[1] + u * 18), 1.0 - u * 0.5, band, 161 + i, w * (1 - u * 0.6))
        cv.ring(gx, gy, R, 1.0, DEEP)


# ------------------------------------------------------------------------------------------ 15 counter
def td_counter(pl, f, n, band, el, R=16.0):
    """A stance: a ring of sword-light round the body at the hand's height, four glints on it; the instant it
    catches a blow it flashes and throws the element off."""
    cv = pl.cv
    gx, gy = pl.pt(0, 0, 0)
    cy = gy - H
    if f == 0:
        cv.ring(gx, cy, R, 1.0, LIGHT)
        cv.dot(gx, cy - R, GLINT, 2)
        return
    u = (f - 1) / (n - 2)
    cv.ring(gx, cy, R, (2.5 * W[band]) * (1 - u * 0.6), GLINT if f == 1 else (LIGHT if u < 0.5 else DEEP))
    for i in range(4):
        a = i * math.pi / 2 + math.pi / 4 + u * 0.8
        x, y = gx + math.cos(a) * R, cy + math.sin(a) * R
        star(cv, x, y, (6 + band * 2) * (1 - u) + 1, points=4, w=1.5)
    if f == 1:
        star(cv, gx, cy, 10 + band * 3, points=8, w=2.5)
        dress_edge(cv, el, [(gx + math.cos(a) * R, cy + math.sin(a) * R, math.cos(a), math.sin(a)) for a in [k * 0.5 for k in range(12)]], f, n, band, 181, every=2)
    fling(cv, el, [(gx + math.cos(a) * R, cy + math.sin(a) * R, math.cos(a), math.sin(a)) for a in [k * 0.8 for k in range(8)]],
          f - 1, n - 1, band, 182, count=6, start=0, life=3, speed=2.4)


# ------------------------------------------------------------------------------------------ 16 ward
def td_ward(pl, f, n, band, el, R=24.0):
    """A bagua on the floor round the caster and a dome of qi closing over it from the ground up."""
    cv = pl.cv
    gx, gy = pl.pt(0, 0, 0)
    k = ease_out(min(1.0, (f + 1) / 4.5))
    # the bagua: two rings and eight trigrams of three bars (broken bars where the hash says yin)
    cv.ring(gx, gy, R, 1.0, LIGHT if f < 8 else DEEP)
    cv.ring(gx, gy, R * 0.62, 1.0, DEEP)
    for i in range(8):
        a = i * math.pi / 4 + 0.2 * (f / n)
        for j in range(3):
            rr = R * (0.7 + j * 0.09)
            px_, py_ = -math.sin(a), math.cos(a)
            x, y = gx + math.cos(a) * rr, gy + math.sin(a) * rr
            L = 3.0
            if px_hash(i, j, 7) < 0.4:
                cv.line1((x - px_ * L, y - py_ * L), (x - px_ * 0.8, y - py_ * 0.8), GLINT if f < 8 else LIGHT)
                cv.line1((x + px_ * 0.8, y + py_ * 0.8), (x + px_ * L, y + py_ * L), GLINT if f < 8 else LIGHT)
            else:
                cv.line1((x - px_ * L, y - py_ * L), (x + px_ * L, y + py_ * L), GLINT if f < 8 else LIGHT)
    # the golden bell of qi over the bagua: its two sides rise from the floor and close over the top by the contact
    ry = R * 1.45
    sy = ry / R
    a = math.pi * 0.5 * (k if f <= 3 else 1.0)
    fade = f >= n - 2
    tb = STROKE_BANDS if f < 7 else (THIN_BANDS if not fade else ((1.0, DEEP),))
    wd = 2.5 * W[band] * (1.0 if f < 7 else 0.6)
    cv.stroke_arc(gx, gy, R, math.pi, math.pi + a, wd * 0.7, wd, sy=sy, table=tb)
    cv.stroke_arc(gx, gy, R, 2 * math.pi - a, 2 * math.pi, wd, wd * 0.7, sy=sy, table=tb)
    if not fade:
        inside = cv.mask_ellipse(gx, gy, R - 2, ry - 2) & (cv.Y < gy) & (cv.Y > gy - ry * (k if f <= 3 else 1.0))
        cv.paint(inside, HAZE, "dither")
    if f >= 4:
        u = (f - 4) / (n - 5)
        sheen = math.pi + math.pi * ((u * 1.4) % 1.0)
        cv.stroke_arc(gx, gy, R - 4, sheen - 0.14, sheen + 0.14, 1.0, 1.0, sy=sy, table=((1.0, CORE),))
        cv.stroke_arc(gx, gy, R - 3, math.pi * 1.15, math.pi * 1.4, 1.5, 1.5, sy=sy, table=((1.0, GLINT),))
        if f == 4:
            star(cv, gx, gy - ry, 6 + band * 2, points=4, w=1.5)
        ring_burst(cv, el, gx, gy, R, f - 4, n - 4, band, 193, count=6, sy=1.0, rise=1.0, life=5)
    dress_edge(cv, el, [(gx + math.cos(t) * (R + 2), gy + math.sin(t) * (ry + 2), math.cos(t), math.sin(t))
                        for t in [math.pi + a * i / 5 for i in range(6)] + [2 * math.pi - a * i / 5 for i in range(6)]], f, n, band, 191, every=3)


# ------------------------------------------------------------------------------------------ 17 chorus
def td_chorus(pl, f, n, band, el, R=40.0):
    """A song of qi: rings of sound spread over the floor from the singer, notes and motes rise."""
    cv = pl.cv
    gx, gy = pl.pt(0, 0, 0)
    for j in range(3 + (band > 1)):
        u = (f - j * 2) / 5.0
        if u < 0 or u > 1:
            continue
        r = lerp(6.0, R, ease_out(u))
        cv.ring(gx, gy, r, 2.5 * W[band] * (1 - u * 0.7) + 1.0, LIGHT if u < 0.5 else BASE)
        cv.ring(gx, gy, r - 1, 1.0, GLINT if u < 0.3 else DEEP)
        if j == 0:
            ground_ripple(cv, el, gx, gy, r * 0.85, f, n, band, 1.0)
    for i in range(4 + band * 2):
        u = ((f * 0.13) + px_hash(i, 201)) % 1.0
        x = gx + (px_hash(i, 202) - 0.5) * 30 + math.sin(u * 6 + i) * 3
        y = gy - 16 - u * 30
        if i % 2 == 0:
            cv.stamp([".L", "LL", "L."], x - 1, y - 1, {"L": GLINT if u < 0.6 else LIGHT})
            cv.line1((x + 1, y - 1), (x + 1, y - 5), GLINT if u < 0.6 else LIGHT)
        else:
            particle(cv, el, x, y, 0, -1, u, i)
    if f == 3:
        star(cv, gx, gy - 26, 6 + band * 2, points=4, w=1.5)


# ------------------------------------------------------------------------------------------ 18 blink
def td_blink(pl, f, n, band, el):
    """Anchored at the foe: afterimages arrive from before it, then a cut falls just past it (the caster is behind
    it now)."""
    cv = pl.cv
    lean = pl.c * 0.2
    if f <= 3:
        for i in range(f):
            x, y = pl.pt(-34 + i * 12, 0, 0)
            tone = (BASE, DEEP, HAZE)[max(0, min(2, i - f + 3))]
            cv.figure(x, y, 30, tone, lean=lean, dither=tone != BASE)
        x, y = pl.pt(-40, 0, 0)
        cv.ring(x, y, 4 + f * 3, 1.0, DEEP if f > 1 else LIGHT)
        return
    u = (f - 4) / (n - 5)
    for i in range(3):
        if u < 0.7 or i == 2:
            x, y = pl.pt(-34 + i * 12, 0, 0)
            cv.figure(x, y, 30, HAZE if u > 0.3 or i < 2 else DEEP, lean=lean)
    td_strike(pl, min(7, 3 + int(u * 4)), 8, band, el, R=16.0, seed=211, f0=10.0)


# ------------------------------------------------------------------------------------------ 19 plunge
def td_plunge(pl, f, n, band, el, R=40.0):
    """The body drops out of the air: a shock ring over the floor, cracks, stone and dust thrown up."""
    cv = pl.cv
    gx, gy = pl.pt(0, 0, 0)
    if f <= 1:
        h = 40 - f * 14
        cv.stroke_seg((gx, gy - h), (gx, gy - 4 - f * 2), 4.0 * W[band], 8.0 * W[band])
        cv.paint(cv.mask_polygon([(gx - 8, gy - h - 6), (gx + 8, gy - h - 6), (gx + 4, gy - 2), (gx - 4, gy - 2)]), HAZE, "under")
        return
    u = (f - 2) / (n - 3)
    r = lerp(10.0, R, ease_out(u * 1.2))
    star(cv, gx, gy - 4, (13 + band * 3) * (1.0 if f == 2 else max(0.0, 1 - u * 1.5)), points=8, w=3.0 if f == 2 else 2.0)
    cv.ring(gx, gy, r, 3.0 * W[band] * (1 - u * 0.6) + 1.0, LIGHT if u < 0.5 else BASE)
    cv.ring(gx, gy, r - 2, 1.0, GLINT if u < 0.4 else DEEP)
    for i in range(6 + band * 2):
        a = i * 2 * math.pi / (6 + band * 2) + 0.3
        L = min(r, 8 + u * 26 + px_hash(i, 221) * 8)
        pts = [(gx, gy)]
        for j in range(1, 4):
            d = L * j / 3
            aa = a + (px_hash(i, j) - 0.5) * 0.4
            pts.append((gx + math.cos(aa) * d, gy + math.sin(aa) * d))
        for j in range(len(pts) - 1):
            cv.line1(pts[j], pts[j + 1], INK if u < 0.7 else DEEP)
    for i in range(5 + band * 2):
        a = px_hash(i, 231) * 2 * math.pi
        d = r * (0.5 + px_hash(i, 232) * 0.5)
        cv.dot(gx + math.cos(a) * d, gy + math.sin(a) * d - u * 6 - px_hash(i, 233) * 6, HAZE, 3 if band else 2)
    ring_burst(cv, el, gx, gy, 8, f - 2, n - 2, band, 241, count=10, sy=1.0, rise=2.0, life=5)
    if u < 0.8:
        ground_ripple(cv, el, gx, gy, r * 0.7, f, n, band, 1.0)


# ------------------------------------------------------------------------------------------ 20 release
def formation(cv, gx, gy, r, count, spin, tone=LIGHT, lift=0.0, out=True):
    """A sword formation: `count` swords of qi on a ring of radius r round (gx, gy), lifted by `lift`, pointing out
    (or along the ring)."""
    for i in range(count):
        a = spin + i * 2 * math.pi / count
        x, y = gx + math.cos(a) * r, gy + math.sin(a) * r - lift
        sword_sliver(cv, x, y, a if out else a + math.pi / 2, 8 + (r > 20) * 2, tone)


def td_release(pl, f, n, band, el):
    """The weapon leaves the hand: a sword of qi rises spinning over the caster while a sword formation turns on the
    floor round them."""
    cv = pl.cv
    gx, gy = pl.pt(0, 0, 0)
    hx, hy = gx, gy - H
    formation(cv, gx, gy, 20, 6 + band * 2, f * 0.25, LIGHT if f < 8 else DEEP)
    cv.ring(gx, gy, 20, 1.0, DEEP)
    if f <= 2:
        cv.disc(hx, hy, 3 + f * 2, table=GLOW_BANDS)
        for i in range(5 + band * 2):
            a = i * 2 * math.pi / (5 + band * 2) - f * 0.7
            cv.dot(hx + math.cos(a) * (12 - f * 3), hy + math.sin(a) * (12 - f * 3), GLINT)
        return
    u = (f - 3) / (n - 4)
    top = lerp(hy - 4, gy - 58.0, ease_out(min(1.0, u * 1.6)))
    sword_sliver(cv, hx, top, -math.pi / 2, 16 + band * 2, GLINT)
    cv.paint(cv.mask_polygon([(hx - 3, hy), (hx + 3, hy), (hx + 1.5, top + 16), (hx - 1.5, top + 16)]), HAZE, "dither")
    if f == 4:
        star(cv, hx, top, 7 + band * 2, points=4, w=1.5)
    dress_edge(cv, el, [(hx + 3, y, 1.0, 0.0) for y in range(int(top + 4), int(hy), 5)], f, n, band, 251, every=2)


# ------------------------------------------------------------------------------------------ 21 swarm
def td_swarm(pl, f, n, band, el, R=24.0):
    """A sword formation: swords of qi orbit the caster at the chest's height, the formation's ring on the floor."""
    cv = pl.cv
    gx, gy = pl.pt(0, 0, 0)
    k = ease_out(min(1.0, (f + 1) / 4.0))
    cv.paint(cv.mask_ellipse(gx, gy, R, R) & ~cv.mask_ellipse(gx, gy, R - 2, R - 2), HAZE, "dither")
    count = 6 + band * 2
    formation(cv, gx, gy, R * k, count, f * 0.35, GLINT if f == 3 else LIGHT, lift=18.0, out=False)
    if f == 3:
        star(cv, gx, gy - 18, 7 + band * 2, points=8, w=2.0)
    dress_edge(cv, el, [(gx + math.cos(a) * R * k, gy - 18 + math.sin(a) * R * k, math.cos(a), math.sin(a)) for a in [i * 0.7 + f * 0.35 for i in range(9)]],
               f, n, band, 261, every=2)


# ------------------------------------------------------------------------------------------ 22 seal
def td_seal(pl, f, n, band, el, R=16.0):
    """A talisman falls on the foe and slams a seal onto the floor under it: a square seal with its glyph, a shock
    ring, the slip burning away."""
    cv = pl.cv
    gx, gy = pl.pt(0, 0, 0)
    if f <= 2:
        h = lerp(56.0, 8.0, ease_in((f + 1) / 3.0))
        talisman(cv, gx - 3, gy - h - 12, 12 + band * 2, tilt=(1 - f) * 1.5)
        cv.ring(gx, gy, 6 + f * 3, 1.0, DEEP)
        return
    u = (f - 3) / (n - 4)
    # the seal on the floor: a square turned 45 degrees, a square inside, a cross glyph
    s = R * (1.0 if f > 3 else 1.15)
    outer = [(gx, gy - s), (gx + s, gy), (gx, gy + s), (gx - s, gy)]
    inner = [(gx, gy - s * 0.6), (gx + s * 0.6, gy), (gx, gy + s * 0.6), (gx - s * 0.6, gy)]
    tone = GLINT if u < 0.3 else (LIGHT if u < 0.7 else DEEP)
    for poly in (outer, inner):
        for i in range(4):
            cv.line1(poly[i], poly[(i + 1) % 4], tone)
    cv.line1((gx - s * 0.35, gy), (gx + s * 0.35, gy), INK if u < 0.7 else DEEP)
    cv.line1((gx, gy - s * 0.35), (gx, gy + s * 0.35), INK if u < 0.7 else DEEP)
    if f == 3:
        star(cv, gx, gy - 4, 10 + band * 3, points=8, w=2.5)
    if u < 0.6:
        cv.ring(gx, gy, s + 2 + u * 10, 1.0 if u > 0.3 else 2.0, LIGHT if u < 0.3 else DEEP)
    if u < 0.5:
        talisman(cv, gx - 3, gy - 14 + u * 6, (12 + band * 2) * (1 - u), lit=False)
    ring_burst(cv, el, gx, gy, s, f - 3, n - 3, band, 271, count=6, sy=1.0, rise=1.0, life=4)


# ------------------------------------------------------------------------------------------ 23 domain
def td_domain(pl, f, n, band, el, R=46.0):
    """A field of the Dao spreads over the floor: a great circle of runes and trigrams turning, motes rising, the
    element's ground mark pulsing inside."""
    cv = pl.cv
    gx, gy = pl.pt(0, 0, 0)
    k = ease_out(min(1.0, (f + 1) / 4.0))
    r = R * k
    dim = f >= n - 2
    cv.ring(gx, gy, r, 1.5 if not dim else 1.0, LIGHT if not dim else DEEP)
    cv.ring(gx, gy, r * 0.84, 1.0, DEEP)
    for i in range(16):
        a = i * math.pi / 8 + f * 0.08
        x0, y0 = gx + math.cos(a) * r * 0.86, gy + math.sin(a) * r * 0.86
        x1, y1 = gx + math.cos(a) * r * 0.97, gy + math.sin(a) * r * 0.97
        cv.line1((x0, y0), (x1, y1), GLINT if i % 4 == 0 else LIGHT)
    for i in range(8):
        a = -i * math.pi / 4 - f * 0.05
        px_, py_ = -math.sin(a), math.cos(a)
        x, y = gx + math.cos(a) * r * 0.55, gy + math.sin(a) * r * 0.55
        cv.line1((x - px_ * 3, y - py_ * 3), (x + px_ * 3, y + py_ * 3), LIGHT if not dim else DEEP)
    for i in range(5 + band * 3):
        uu = ((f * 0.09) + px_hash(i, 281)) % 1.0
        x = gx + (px_hash(i, 282) - 0.5) * r * 1.4
        y = gy + (px_hash(i, 283) - 0.5) * r * 1.2 - uu * 26
        particle(cv, el, x, y, 0, -0.5, uu, i)
    if f == 3:
        star(cv, gx, gy - 6, 8 + band * 3, points=8, w=2.0)
    if not dim:
        ground_ripple(cv, el, gx, gy, r * 0.4 + (f * 3 % 10), f, n, band, 1.0)


# ------------------------------------------------------------------------------------------ 24 echo
def td_echo(pl, f, n, band, el):
    """The strike, then its echo: the same sword-light again a step further on, half there."""
    cv = pl.cv
    if f <= 5:
        td_strike(pl, f, 6, band, el, R=30.0, seed=3)
        return
    g = f - 6
    from fxpix import Canvas
    gcv = Canvas(cv.w, cv.h)
    gpl = Plane(gcv, pl.ax, pl.ay, "e")
    gpl.th, gpl.c, gpl.s = pl.th, pl.c, pl.s
    td_strike(gpl, min(3, g), 6, band, el, R=28.0, seed=4, f0=8.0)
    body = gcv.idx > 0
    even = ((cv.X.astype(int) + cv.Y.astype(int)) % 2) == 0
    cv.paint(body & even, (BASE, LIGHT, DEEP, DEEP, HAZE, HAZE)[min(5, g)], "under")
    cv.paint(body & ~even & (gcv.idx >= LIGHT), GLINT if g < 3 else DEEP, "under")
    x, y = pl.arc(28.0, -1.15, -1.15, H, 0.45, n=1, f0=8.0)[0]
    if g == 3:
        cv.ring(x, y, 5, 1.0, GLINT)
    if g >= 3:
        cv.ring(x, y, 5 + (g - 3) * 5, 1.0, DEEP)


# ------------------------------------------------------------------------------------------ the table
def _s(draw, canvas, anchor, frames, fps, impact, span, at="feet", layer="sorted", dirs=True, size="reach", bolt=None):
    d = dict(draw=draw, canvas=canvas, anchor=anchor, frames=frames, fps=fps, impact=impact, span=span, at=at, layer=layer,
             dirs=dirs, size=size)
    if bolt:
        d["bolt"] = bolt
    return d


def _bolt(draw, dirs=True):
    return dict(draw=draw, canvas=(80, 80), anchor=(40, 40 + int(H)), frames=4, fps=12, dirs=dirs)


# Frames, fps and impact frames match the side view's sheets (tools/art/fx/forms.py), so a form lands on its pose's hit
# frame in both views.
TD_FORMS = {
    "strike": _s(td_strike, (104, 112), (52, 64), 8, 14, 3, 34),
    "flurry": _s(td_flurry, (96, 96), (48, 56), 10, 16, 2, 32),
    "thrust": _s(td_thrust, (160, 176), (80, 88), 8, 14, 3, 64),
    "lunge": _s(td_lunge, (128, 136), (64, 72), 8, 14, 3, 44, size="fixed"),
    "sweep": _s(td_sweep, (112, 112), (56, 56), 8, 12, 3, 40, layer="floor"),
    "arc": _s(td_arc, (152, 160), (76, 84), 8, 14, 2, 62, size="fixed", bolt=_bolt(bolt_arc)),
    "volley": _s(td_volley, (152, 160), (76, 84), 8, 14, 2, 66, size="fixed", bolt=_bolt(bolt_volley)),
    "rain": _s(td_rain, (72, 112), (36, 34 + 70), 10, 12, 5, 26, at="target", dirs=False),
    "pillar": _s(td_pillar, (48, 120), (24, 108), 10, 12, 3, 14, at="target", dirs=False, size="fixed"),
    "wave": _s(td_wave, (96, 96), (48, 56), 8, 12, 3, 16, dirs=True, size="travel"),
    "burst": _s(td_burst, (104, 112), (52, 60), 8, 12, 2, 40, layer="floor", dirs=False),
    "seeker": _s(td_seeker, (152, 160), (76, 84), 8, 14, 2, 62, size="fixed", bolt=_bolt(bolt_seeker)),
    "return": _s(td_return, (144, 152), (72, 80), 10, 12, 3, 60, size="fixed", bolt=_bolt(bolt_return, dirs=False)),
    "snare": _s(td_snare, (72, 88), (36, 60), 10, 12, 4, 24, at="target", dirs=False),
    "counter": _s(td_counter, (64, 72), (32, 48), 6, 14, 1, 16, dirs=False, size="fixed"),
    "ward": _s(td_ward, (72, 88), (36, 60), 10, 12, 4, 24, dirs=False),
    "chorus": _s(td_chorus, (96, 104), (48, 56), 10, 12, 3, 40, layer="floor", dirs=False),
    "blink": _s(td_blink, (144, 144), (72, 72), 8, 14, 4, 16, at="target", size="fixed"),
    "plunge": _s(td_plunge, (104, 112), (52, 60), 8, 12, 2, 40, layer="floor", dirs=False),
    "release": _s(td_release, (64, 104), (32, 76), 10, 12, 4, 20, dirs=False, size="fixed"),
    "swarm": _s(td_swarm, (72, 96), (36, 68), 10, 12, 3, 24, dirs=False),
    "seal": _s(td_seal, (56, 88), (28, 68), 10, 12, 3, 16, at="target", dirs=False, size="fixed"),
    "domain": _s(td_domain, (104, 112), (52, 60), 12, 10, 3, 46, layer="floor", dirs=False),
    "echo": _s(td_echo, (104, 112), (52, 64), 12, 14, 3, 34),
}
TD_ORDER = list(TD_FORMS.keys())
