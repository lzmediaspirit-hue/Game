"""The top-down melee FX (decision 38): every weapon family's smears, the shared guard, parry, Plunge, charge and foe
marks, the impact marks and the dust, drawn on the ground plane (plane.py) in the five drawn directions.

The look rule (decision 38): the feel is the reference game's (smears few and fast, one bright contact frame, a
readable follow-through), the look is wuxia. A family's smear is its own qi in the art bible's palette:

  jade sword-light   jian, spear, short blade, flute        (the river's jade ramp, a lantern-gold accent)
  gold qi            fists, gauntlets, staff, heavy sabre, bow (the lantern ramp)
  ink                brush                                   (ink and paper, a red seal)
  wind               fan                                     (the wind's teal, lotus-pink petals)
  bronze             bell                                    (bell bronze, the soul's violet)

Punches leave palm prints, blades sword-light crescents with a qi trail, the brush an ink stroke with dry-brush
breaks, the bell rings of sound on the floor, the fan a gust with petals. Impacts are calligraphic marks: an ink
dab for a light blow, a brush slash for a heavy one, a crossed stroke for a finisher, each in the element's colours
with its Dao motif (wuxia.py).

A family sheet's rows are MOVES x DIRS: each combo step, the charged (dragged) finisher, the dash attack and the air
blow, in the five drawn directions. Frames: SMEAR frames at SMEAR_FPS, the contact on SMEAR_IMPACT.
"""
from __future__ import annotations

import math

from elements import fling
from forms import THIN_BANDS, star
from fxpix import (ACCENT, BASE, CORE, DEEP, GLINT, HAZE, INK, LIGHT, STROKE_BANDS, ease_out, lerp, px_hash)
from wuxia import INK_BANDS, brush_stroke, motif, palm_print, stone

H = 14.0
SMEAR = 6            # frames of a smear: 0 the lead-in, 1 the contact, 2 the follow-through, 3-5 the qi fading
SMEAR_FPS = 20
SMEAR_IMPACT = 1
MOVES = ["step_1", "step_2", "step_3", "charged", "dash", "air"]


def _rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# qi palettes in the art bible's ramps (docs/redesign/art_bible.md §2): ink, deep, base, light, glint, accent
QI = {
    "jade": ("#0A2A2E", "#1D6C61", "#4CA992", "#8BD5BC", "#D6F5E6", "#FFF0B0"),
    "gold": ("#3A1F0C", "#9A6A20", "#E0B040", "#FFE08A", "#FFF6D0", "#FFFFFF"),
    "ink": ("#0E1A1E", "#2E3A3F", "#5E6F76", "#D9D0BC", "#F6F1E3", "#C23D37"),
    "wind": ("#0E3234", "#3A8A80", "#8FD0C8", "#CFE8E6", "#EEFFFA", "#F2A0B8"),
    "bronze": ("#2A1A10", "#7A5020", "#C8913A", "#F0C878", "#FFF0C8", "#9B78D1"),
    "foe": ("#1E1410", "#6A4A3A", "#C8B8A0", "#F0E8D8", "#FFFFFF", "#C23D37"),
    "dust": ("#3B281B", "#7A5A38", "#B79463", "#D2B282", "#E8D3A6", "#FFFFFF"),
}


def palette(name: str):
    """Index -> RGBA for a qi palette (the same index ramp as elements.palette)."""
    ink, deep, base, light, glint, accent = QI[name]
    lut = [(0, 0, 0, 0)] * 9
    lut[INK] = _rgb(ink) + (255,)
    lut[DEEP] = _rgb(deep) + (255,)
    lut[BASE] = _rgb(base) + (255,)
    lut[LIGHT] = _rgb(light) + (255,)
    lut[GLINT] = _rgb(glint) + (255,)
    lut[CORE] = (255, 255, 255, 255)
    lut[ACCENT] = _rgb(accent) + (255,)
    lut[HAZE] = _rgb(base) + (110,)
    return lut


# family -> kind of strike, qi palette, drawn reach (art px) and the whole-step scale the game draws it at
FAMILIES = {
    "fists": dict(kind="palm", qi="gold", r=23, scale=1),
    "gauntlets": dict(kind="palm", qi="gold", r=25, scale=1, glint=True),
    "jian": dict(kind="blade", qi="jade", r=39, scale=1),
    "spear": dict(kind="point", qi="jade", r=58, scale=1),
    "short_blade": dict(kind="twin", qi="jade", r=26, scale=1),
    "staff": dict(kind="blunt", qi="gold", r=48, scale=1),
    "heavy_sabre": dict(kind="heavy", qi="gold", r=46, scale=1),
    "fan": dict(kind="gust", qi="wind", r=35, scale=2),
    "flute": dict(kind="note", qi="jade", r=14, scale=1),
    "brush": dict(kind="ink", qi="ink", r=28, scale=2),
    "bell": dict(kind="ring", qi="bronze", r=40, scale=2),
    "bow": dict(kind="shot", qi="gold", r=18, scale=1),
}


def _k(f):
    """The smear's life: 0 lead-in, 1 contact, 2 follow-through, then 0..1 over the fade."""
    return max(0.0, (f - 2) / (SMEAR - 3))


# ------------------------------------------------------------------------------------------ swings
def swing(pl, f, r, w, a0, a1, tilt, h0, style="blade", seed=1):
    """A cut's smear along an arc: the lead-in sliver, the full sweep at contact with its haze, the follow-through,
    then the qi thinning from the tail. style: blade (thin sword-light), heavy (broad, an ink edge), ink (a brush
    stroke), gust (wind streaks and petals)."""
    cv = pl.cv
    centre = pl.pt(0, 0, h0)
    if f == 0:
        pl.stroke(pl.arc(r, a0, lerp(a0, a1, 0.3), h0, tilt, 8), w * 0.2, w * 0.6, THIN_BANDS)
        x, y = pl.arc(r, a0, a0, h0, tilt, 1)[0]
        star(cv, x, y, 3 + w * 0.3, points=4, w=1.0)
        return
    tail = a0 if f <= 2 else lerp(a0, a1, 0.2 + 0.8 * _k(f))
    head = a1 if f >= 1 else lerp(a0, a1, 0.5)
    path = pl.arc(r, tail, head, h0, tilt, 18)
    if f <= 2:
        # the smear: the band the blade swept, widest on the contact frame, a thin lit edge outside it
        pl.sweep_haze(pl.arc(r + w * 0.4, tail, head, h0, tilt, 14), centre, w * (2.4 if f == 1 else 1.2))
        if f == 1 and style in ("blade", "heavy"):
            edge = pl.arc(r + w * 0.75, lerp(tail, head, 0.25), head, h0, tilt, 12)
            for i in range(len(edge) - 1):
                cv.line1(edge[i], edge[i + 1], LIGHT)
    u = _k(f)
    if style == "ink":
        brush_stroke(cv, path[::-1] if f > 2 else path, w * (1.0 - 0.6 * u), seed, INK_BANDS if f <= 2 else ((0.5, DEEP), (1.0, BASE)))
        if f == 1:
            for i in range(3):
                x, y = path[int(len(path) * (0.3 + 0.3 * i))]
                cv.dot(x + 2, y + 2 + i, ACCENT, 2)   # a red seal's spatter
    elif style == "heavy":
        tb = ((0.25, CORE), (0.55, LIGHT), (0.85, BASE), (1.0, DEEP)) if f <= 2 else ((0.5, BASE), (1.0, DEEP))
        pl.stroke(path, w * 0.5 * (1 - u), w * (1.2 - u * 0.8), tb)
        brush_stroke(cv, pl.arc(r + w * 0.55, tail, head, h0, tilt, 12), max(1.5, w * 0.35 * (1 - u)), seed, INK_BANDS, mode="under")
    else:
        pl.stroke(path, w * 0.3 * (1 - u) + 0.8, w * (1.0 - u * 0.7), STROKE_BANDS if f == 1 else (THIN_BANDS if u < 0.6 else ((1.0, DEEP),)))
    if style == "gust":
        for i in range(3):
            pl.stroke(pl.arc(r * (0.7 + 0.15 * i), tail, head, h0 + i * 2, tilt, 10), 1.0, 1.0, ((1.0, LIGHT if i % 2 else DEEP),), "under")
        for i in range(4):
            x, y = path[int((len(path) - 1) * px_hash(seed, i))]
            motif(cv, "wind", x + (f - 1) * 2, y - (f - 1), 5.0, min(1.0, f / 5.0), seed + i)
            cv.dot(x + 3 + f, y - 2, ACCENT, 2 if f < 3 else 1)
    if f == 1:
        x, y = path[-1]
        star(cv, x, y, 3 + w * 0.5, points=4, w=1.5)
    if f >= 2:
        # the qi motes left in the air along the path
        for i in range(4):
            x, y = path[int((len(path) - 1) * px_hash(seed, i, 3))]
            cv.dot(x, y - u * 4 - i % 2, GLINT if u < 0.5 else LIGHT)


def spin(pl, f, r, w, h0, style="blade", seed=2):
    """The charged finisher of a cutting family: a full spin of sword-light round the body (the reference's spin
    finisher), a second faint ring outside it."""
    cv = pl.cv
    if f == 0:
        cv.ring(*pl.pt(0, 0, h0), r * 0.6, 1.0, LIGHT)
        star(cv, *pl.pt(0, 0, h0), 5 + w * 0.3, points=8, w=1.5)
        return
    swing(pl, f, r, w, -math.pi, math.pi - 0.25, 0.2, h0, style, seed)
    if f <= 2:
        pl.ring(r + 4, 1.0, LIGHT if f == 1 else DEEP, h0)


# ------------------------------------------------------------------------------------------ thrusts
def thrust(pl, f, L, w, h0, h1, style="point", seed=3):
    """A thrust's smear: a line of qi to the point (point), a round shock at the end (blunt, the staff), or two quick
    stabs side by side (twin, the short blade); a spiral of qi round the charged one."""
    cv = pl.cv
    u = _k(f)
    reach = L * (0.55 if f == 0 else 1.0)
    lanes = (-3.0, 3.0) if style == "twin" else (0.0,)
    for lo in lanes:
        start = 2 if f <= 2 else lerp(2, L * 0.8, u)
        pts = [pl.pt(lerp(start, reach, k / 7), lo, lerp(h0, h1, k / 7)) for k in range(8)]
        if f <= 2:
            pl.sweep_haze([pl.pt(start, lo - w, h0), pl.pt(reach, lo - w * 0.4, h1)], pl.pt(start, lo + w, h0), w * 1.6)
        pl.stroke(pts, w * 0.3, w * (1.0 - 0.7 * u), STROKE_BANDS if f == 1 else (THIN_BANDS if u < 0.6 else ((1.0, DEEP),)))
        tip = pl.pt(reach, lo, h1)
        if style == "blunt":
            if 1 <= f <= 3:
                cv.ring(tip[0], tip[1], 3 + f * 2, 1.5 if f < 3 else 1.0, LIGHT if f < 3 else DEEP)
        elif f <= 2:
            cv.polygon([pl.pt(reach - 5, lo - w * 0.45, h1), pl.pt(reach + 3, lo, h1), pl.pt(reach - 5, lo + w * 0.45, h1)], CORE if f == 1 else LIGHT)
        if f == 1:
            star(cv, tip[0], tip[1], 3 + w * 0.6, points=8 if style != "twin" else 4, w=1.5)
    if style == "spiral" and f <= 3:
        rib = [pl.pt(x, math.sin(x * 0.35 + f * 1.4) * 4, lerp(h0, h1, x / L) + math.cos(x * 0.35 + f * 1.4) * 4) for x in range(4, int(reach) - 2, 2)]
        pl.stroke(rib, 1.0, 2.0, ((0.5, GLINT), (1.0, LIGHT)), "under")


# ------------------------------------------------------------------------------------------ palms
def palm(pl, f, reach, h0, h1, size, seed=4, glint=False):
    """A palm strike: a short streak of qi to the reach and the palm print it leaves in the air there, brightest at
    contact, spreading a ring as it dims and gone by the last frame."""
    cv = pl.cv
    u = _k(f)
    end = pl.pt(reach, 0, h1)
    if f <= 2:
        pts = [pl.pt(lerp(4, reach - 2, k / 5), 0, lerp(h0, h1, k / 5)) for k in range(6)]
        pl.stroke(pts, 1.0, 3.0 + size * 0.15, THIN_BANDS)
        pl.sweep_haze([pl.pt(4, -3, h0), pl.pt(reach, -size * 0.3, h1)], pl.pt(4, 3, h0), size * 0.5)
    if f == 1:
        star(cv, end[0], end[1], 3 + size * 0.35, points=8, w=1.5)
    if 1 <= f <= 4:
        s = size * (0.85 + 0.1 * f)
        ang = math.atan2(end[1] - pl.pt(0, 0, h1)[1], end[0] - pl.pt(0, 0, h1)[0])
        if abs(pl.c) < 0.2 and h1 > h0 + 4:
            ang = -math.pi / 2
        tone, rim = ((GLINT, LIGHT), (LIGHT, BASE), (BASE, DEEP), (DEEP, DEEP))[f - 1]
        palm_print(cv, end[0], end[1], s, ang, tone, rim)
        if f in (2, 3):
            cv.ring(end[0], end[1], s * 0.5 + (f - 1) * size * 0.35, 1.0, GLINT if f == 2 else DEEP)
        if glint and f <= 2:
            cv.plus(end[0] + s * 0.4, end[1] - s * 0.4, CORE, 2)


# ------------------------------------------------------------------------------------------ sound and shots
def rings(pl, f, r, both=True, notes=False):
    """The bell's toll or the flute's note: rings of sound spreading over the floor round the bearer (both sides, the
    bell rings out behind as well as ahead), notes rising for the flute."""
    cv = pl.cv
    gx, gy = pl.pt(0, 0, 0)
    for j in range(3):
        u = (f - j) / 3.0
        if u < 0 or u > 0.85:
            continue
        rr = lerp(4.0, r, ease_out(u))
        if both:
            cv.ring(gx, gy, rr, 2.0 if u < 0.4 else 1.0, LIGHT if u < 0.5 else BASE)
        else:
            pl.ring(rr, 2.0 if u < 0.4 else 1.0, LIGHT if u < 0.5 else BASE, 0, 0, 0, -1.0, 1.0)
        if j == 0 and u < 0.5:
            cv.ring(gx, gy - H, rr * 0.4, 1.0, GLINT)
    if f == 1:
        star(cv, gx, gy - H, 6, points=8, w=1.5)
    for i in range(3 if notes else 2):
        uu = (f / SMEAR + px_hash(i, 7)) % 1.0
        x, y = gx + (px_hash(i, 8) - 0.5) * 20, gy - H - 4 - uu * 18
        if notes:
            cv.stamp([".L", "LL", "L."], x - 1, y - 1, {"L": GLINT})
            cv.line1((x + 1, y - 1), (x + 1, y - 5), GLINT)
        else:
            cv.dot(x, y, ACCENT)


def shot(pl, f, L, h0, charged=False):
    """A bow's release: a line of gold qi along the shot and the string's ring at the hand."""
    cv = pl.cv
    u = _k(f)
    hx, hy = pl.pt(4, 0, h0)
    if f <= 2:
        pl.stroke(pl.line(4, L * (0.6 + 0.4 * min(1, f)), 0, h0, 6), 1.0, 2.5 + (1.5 if charged else 0), THIN_BANDS)
    cv.ring(hx, hy, 3 + f * 2, 1.0, LIGHT if u < 0.5 else DEEP)
    if f == 1:
        star(cv, hx, hy, 6 + (4 if charged else 0), points=8, w=1.5)
    if charged and f <= 3:
        for k in (0.4, 0.7, 1.0):
            x, y = pl.pt(L * k, 0, h0)
            cv.ring(x, y, 3 + f, 1.0, GLINT)


# ------------------------------------------------------------------------------------------ one family's move
def draw_move(pl, f, fam: str, move: str):
    """Frame f of `move` (MOVES) of family `fam`, on the Plane."""
    spec = FAMILIES[fam]
    kind, r = spec["kind"], float(spec["r"])
    w = {"blade": 5.0, "heavy": 8.0, "ink": 6.0, "gust": 4.0}.get(kind, 5.0)
    seed = hash_of(fam, move)
    if kind in ("blade", "heavy", "ink", "gust"):
        style = kind
        if move == "step_1":
            swing(pl, f, r, w, -1.3, 1.0, 0.6, H - 2, style, seed)
        elif move == "step_2":
            swing(pl, f, r, w, 1.3, -1.3, 0.1, H, style, seed)
        elif move == "step_3":
            swing(pl, f, r * 0.9, w * 1.25, 1.5, -0.35, math.pi / 2, H + 2, style, seed)
            if f == 1:
                ground = pl.pt(r * 0.8, 0, 0)
                pl.cv.ring(ground[0], ground[1], 6, 1.0, LIGHT)
        elif move == "charged":
            spin(pl, f, r * 1.1, w * 1.3, H, style, seed)
        elif move == "dash":
            thrust(pl, f, r * 1.3, w, H, H, "point", seed)
            dash_trail(pl, f)
        else:   # air: a chop down in front out of the air
            swing(pl, f, r * 0.8, w, 1.2, -0.9, math.pi / 2, H + 18, style, seed)
    elif kind in ("point", "blunt", "twin"):
        L = r
        if move == "step_1":
            thrust(pl, f, L, w, H, H, kind, seed)
        elif move == "step_2":
            thrust(pl, f, L * 0.95, w, H - 2, 5, kind, seed)
        elif move == "step_3":
            thrust(pl, f, L * 1.15, w * 1.2, H + 2, H + 8, kind, seed)
            thrust(pl, f, L * 1.15, w * 0.5, H + 2, H + 8, "spiral", seed)
        elif move == "charged":
            thrust(pl, f, L * 1.3, w * 1.4, H, H, kind, seed)
            thrust(pl, f, L * 1.3, w, H, H, "spiral", seed)
            if kind == "blunt" and 1 <= f <= 3:
                pl.ring(10 + f * 4, 1.0, LIGHT if f < 3 else DEEP, 0, L * 1.3)
        elif move == "dash":
            thrust(pl, f, L * 1.2, w, H, H, kind, seed)
            dash_trail(pl, f)
        else:
            thrust(pl, f, L * 0.7, w, H + 22, 0, kind, seed)
    elif kind == "palm":
        g = bool(spec.get("glint"))
        if move == "step_1":
            palm(pl, f, r, H + 4, H + 4, 9, seed, g)
        elif move == "step_2":
            palm(pl, f, r * 1.05, H + 3, H + 5, 11, seed, g)
        elif move == "step_3":
            palm(pl, f, r * 0.9, H - 2, H + 18, 13, seed, g)
        elif move == "charged":
            palm(pl, f, r * 1.4, H + 4, H + 6, 18, seed, g)
            if 1 <= f <= 3:
                pl.ring(8 + f * 5, 1.0, LIGHT if f < 3 else DEEP, H + 6, r * 1.4)
        elif move == "dash":
            palm(pl, f, r * 1.2, H + 4, H + 4, 12, seed, g)
            dash_trail(pl, f)
        else:
            palm(pl, f, r * 0.6, H + 20, 1, 12, seed, g)
    elif kind in ("ring", "note"):
        big = move in ("step_3", "charged")
        rings(pl, f, r * (1.3 if big else 1.0) * (1.2 if move == "charged" else 1.0), both=kind == "ring", notes=kind == "note")
        if move == "dash":
            dash_trail(pl, f)
    else:   # shot
        shot(pl, f, r * (1.6 if move == "charged" else 1.0), H + (4 if move != "air" else 16), charged=move in ("charged", "step_3"))
        if move == "dash":
            dash_trail(pl, f)


def dash_trail(pl, f):
    """The dash attack's trail: the body's afterimages behind the blow and the dust of the dash."""
    cv = pl.cv
    if f > 3:
        return
    for i in range(2):
        x, y = pl.pt(-10 - i * 9 - f * 2, 0, 0)
        cv.figure(x, y, 28, HAZE if i or f > 1 else DEEP, lean=pl.c * 0.25)
    for i in range(3):
        x, y = pl.pt(-4 - i * 7 - f * 3, (i - 1) * 3, 0)
        cv.dot(x, y - f, HAZE, 2)


def hash_of(*parts) -> int:
    h = 7
    for p in parts:
        for ch in str(p):
            h = (h * 31 + ord(ch)) & 0xFFFF
    return h


# ------------------------------------------------------------------------------------------ the shared marks
def draw_guard(pl, f, n):
    """A guard: a curved wall of qi before the body (jade), a shimmer running across it; it loops while held."""
    cv = pl.cv
    r = 13.0
    wall = [pl.pt(r * math.cos(a), r * math.sin(a), 0) for a in [-1.45 + 2.9 * k / 12 for k in range(13)]]
    top = [pl.pt(r * math.cos(a), r * math.sin(a), 28) for a in [-1.45 + 2.9 * k / 12 for k in range(13)]]
    cv.paint(cv.mask_polygon(wall + top[::-1]), HAZE, "dither")
    for p in (wall, top):
        for i in range(len(p) - 1):
            cv.line1(p[i], p[i + 1], LIGHT)
    k = int((f / n) * 13) % 13
    cv.line1(wall[k], top[k], GLINT)
    cv.line1(wall[(k + 6) % 13], top[(k + 6) % 13], BASE)


def draw_parry(pl, f, n):
    """A parry (gold): two brush strokes crossing before the body at the instant of the catch, sparks thrown back
    toward the attacker, a ring spreading."""
    cv = pl.cv
    x, y = pl.pt(12, 0, H + 4)
    u = f / (n - 1)
    if f <= 2:
        s = 10 + f * 2
        brush_stroke(cv, [(x - s, y - s), (x - s * 0.3, y - s * 0.3), (x + s * 0.4, y + s * 0.4), (x + s, y + s)], 4.0 - f, 11,
                     ((0.4, CORE), (0.8, LIGHT), (1.0, BASE)))
        brush_stroke(cv, [(x + s, y - s), (x + s * 0.3, y - s * 0.3), (x - s * 0.4, y + s * 0.4), (x - s, y + s)], 4.0 - f, 12,
                     ((0.4, CORE), (0.8, LIGHT), (1.0, BASE)))
    star(cv, x, y, (11) * (1 - u) + 2, points=8, w=2.0)
    cv.ring(x, y, 4 + u * 16, 1.5 if u < 0.4 else 1.0, GLINT if u < 0.4 else DEEP)
    fling(cv, "metal", pl.outward([pl.pt(14, l, H + 4) for l in (-6, -2, 2, 6)], pl.pt(0, 0, H + 4)), f, n, 1, 13, count=5, start=0, life=4, speed=3.0)


def draw_swipe(pl, f, n):
    """A foe's blow: three claw scratches across the front, pale with an ink edge (the foe's own, never qi)."""
    cv = pl.cv
    u = _k(f)
    for i in range(3):
        lo = (i - 1) * 4.0
        a = pl.pt(10, lo - 8, 12 + i)
        b = pl.pt(26, lo + 8, 4 + i)
        if f == 0:
            cv.stroke_seg(a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), 1.0, 2.0, THIN_BANDS)
        elif f <= 2:
            cv.stroke_seg(a, b, 1.0, 3.0, ((0.5, LIGHT), (1.0, INK)))
        else:
            cv.stroke_seg(((a[0] * (1 - u) + b[0] * u), (a[1] * (1 - u) + b[1] * u)), b, 1.0, 2.0 * (1 - u) + 0.5, ((1.0, DEEP),))
    if f == 1:
        x, y = pl.pt(22, 0, 8)
        star(cv, x, y, 5, points=4, w=1.0)


def draw_plunge_mark(pl, f, n):
    """The Plunge's landing (the movement art, decision 35): a crater ring, cracks and stone chips on the floor."""
    cv = pl.cv
    gx, gy = pl.pt(0, 0, 0)
    u = f / (n - 1)
    r = lerp(6, 30, ease_out(u * 1.3))
    cv.ring(gx, gy, r, 2.0 if u < 0.4 else 1.0, LIGHT if u < 0.5 else BASE)
    for i in range(7):
        a = i * 2 * math.pi / 7 + 0.2
        L = min(r, 6 + u * 22)
        cv.line1((gx, gy), (gx + math.cos(a) * L, gy + math.sin(a) * L), INK if u < 0.6 else DEEP)
    for i in range(5):
        a = px_hash(i, 51) * 2 * math.pi
        d = r * (0.4 + 0.5 * px_hash(i, 52))
        stone(cv, gx + math.cos(a) * d, gy + math.sin(a) * d - 10 * math.sin(math.pi * min(1.0, u * 1.4)), 2.2, i)
    if f <= 1:
        star(cv, gx, gy - 3, 10, points=8, w=2.5)


def draw_charge(pl, f, n):
    """Qi gathering for a charged blow: motes drawn in to the hands and a ring tightening on the floor (loops)."""
    cv = pl.cv
    gx, gy = pl.pt(0, 0, 0)
    k = f / n
    cv.ring(gx, gy, 18 - k * 10, 1.0, LIGHT)
    for i in range(8):
        a = i * math.pi / 4 + k * 1.5
        d = 16 - k * 12
        cv.dot(gx + math.cos(a) * d, gy - H - 2 + math.sin(a) * d * 0.8, GLINT if i % 2 else ACCENT)
    cv.disc(gx, gy - H - 2, 2 + k * 2, table=((0.5, CORE), (1.0, LIGHT)))


def draw_tell(pl, f, n):
    """A foe's wind-up tell: a red-cored glint over its head."""
    cv = pl.cv
    x, y = pl.pt(0, 0, 30)
    s = (4, 7, 5, 3)[f % 4]
    star(cv, x, y, s, points=4, w=1.5)
    cv.dot(x, y, ACCENT, 2)


# name: (drawer, frames, fps, impact, loop, directional, palette)
COMMON = {
    "guard": (draw_guard, 4, 8, 0, True, True, "jade"),
    "parry": (draw_parry, 6, 20, 0, False, True, "gold"),
    "swipe": (draw_swipe, 6, 20, 1, False, True, "foe"),
    "plunge": (draw_plunge_mark, 8, 16, 0, False, False, "dust"),
    "charge": (draw_charge, 6, 12, 0, True, False, "jade"),
    "tell": (draw_tell, 4, 12, 0, False, False, "foe"),
}


# ------------------------------------------------------------------------------------------ impacts and dust
WEIGHTS = ["light", "heavy", "finisher"]
IMPACT_FRAMES, IMPACT_FPS = 6, 20


def draw_impact(pl, f, n, weight: str, el: str):
    """A blow's mark where it lands (the anchor), the blow travelling along the Plane's forward: a calligraphic mark
    in the element's colours, sparks thrown on along the blow, the element's motif. Light: an ink dab and a small star;
    heavy: a brush slash across the blow and a ring; finisher: two crossed strokes, a wide ring and three motifs."""
    cv = pl.cv
    x, y = pl.pt(0, 0, 0)
    u = f / (n - 1)
    size = {"light": 6.0, "heavy": 9.0, "finisher": 12.0}[weight]
    if u < 0.8:
        star(cv, x, y, size * (1.2 - u), points=4 if weight == "light" else 8, w=1.5 if weight == "light" else 2.0)
    if weight == "light":
        if f <= 3:
            brush_stroke(cv, [pl.pt(-3, -3, 3), pl.pt(0, -1, 1), pl.pt(3, 2, -1)], 3.0 - f * 0.5, 31, ((0.5, LIGHT), (1.0, BASE)))
    else:
        if f <= 3:
            s = size * (1.0 + 0.15 * f)
            # a calligraphic slash across the blow: pressed where it starts, curving, a dry-brush tail
            brush_stroke(cv, [pl.pt(-s * 0.1, -s, s * 0.5), pl.pt(s * 0.15, -s * 0.4, s * 0.2), pl.pt(s * 0.15, s * 0.2, -s * 0.1),
                              pl.pt(0, s * 0.7, -s * 0.3), pl.pt(-s * 0.2, s * 1.1, -s * 0.5)],
                         6.5 - f * 1.2, 32, ((0.3, CORE), (0.7, LIGHT), (1.0, BASE)))
            if weight == "finisher":
                brush_stroke(cv, [pl.pt(-s * 0.3, s * 0.9, s * 0.6), pl.pt(0, s * 0.2, s * 0.2), pl.pt(s * 0.2, -s * 0.4, -s * 0.2), pl.pt(s * 0.3, -s, -s * 0.6)],
                             5.5 - f * 1.0, 33, ((0.3, CORE), (0.7, LIGHT), (1.0, BASE)))
        if u < 0.85:
            cv.ring(x, y, size * 0.4 + u * size * (1.6 if weight == "finisher" else 1.1), 1.5 if u < 0.4 else 1.0, GLINT if u < 0.4 else DEEP)
    count = {"light": 3, "heavy": 5, "finisher": 8}[weight]
    fling(cv, el, pl.outward([pl.pt(2, l, 0) for l in (-3, -1, 1, 3)], pl.pt(-6, 0, 0)), f, n, {"light": 0, "heavy": 1, "finisher": 2}[weight],
          hash_of(weight, el), count, start=0, life=4, speed=2.6, spread=0.9)
    motifs = {"light": 0, "heavy": 1, "finisher": 3}[weight]
    for i in range(motifs):
        dx, dy = pl.ground_dir(8 + i * 3, (i - 1) * 6)
        motif(cv, el, x + dx * (0.5 + u), y + dy * (0.5 + u) - 3, 8 + (weight == "finisher") * 2, u, i, ang=math.atan2(dy, dx))


def draw_dust(pl, f, n, kind: str):
    """Dust on the path's earth (art bible §2): a dash's kick-off puff behind the start, a skid's streak along the
    floor behind a sliding body, a landing's ring, a step's pinch."""
    cv = pl.cv
    u = f / (n - 1)
    if kind == "dash":
        for i in range(5):
            fd, lo = -2 - i * 3 - u * 8, (px_hash(i, 61) - 0.5) * 10
            x, y = pl.pt(fd, lo, 1 + u * 4 + i % 2)
            cv.dot(x, y, LIGHT if u < 0.5 else BASE, 3 if u < 0.4 else 2)
        pl.stroke(pl.line(-2, -14 - u * 6, 0, 1, 4), 1.0, 1.0, ((1.0, BASE if u < 0.5 else HAZE),)) if u < 0.7 else None
    elif kind == "skid":
        for i in range(6):
            fd = -i * 4 - u * 4
            x, y = pl.pt(fd, (i % 2 - 0.5) * 4, 1 + u * 3)
            cv.dot(x, y, LIGHT if i < 2 and u < 0.5 else BASE, 2)
        pl.stroke(pl.line(0, -20 * (1 - u * 0.5), 0, 0, 4), 1.0, 1.0, ((1.0, DEEP),)) if u < 0.8 else None
    elif kind == "land":
        gx, gy = pl.pt(0, 0, 0)
        for i in range(8):
            a = i * math.pi / 4
            d = 3 + u * 10
            cv.dot(gx + math.cos(a) * d, gy + math.sin(a) * d * 0.9 - u * 3, LIGHT if u < 0.5 else BASE, 2)
    else:   # step
        gx, gy = pl.pt(0, 0, 0)
        for s in (-1, 1):
            cv.dot(gx + s * (2 + u * 4), gy - u * 3, BASE, 2 if u < 0.5 else 1)


DUST = {"dash": True, "skid": True, "land": False, "step": False}
DUST_FRAMES, DUST_FPS = 6, 16
