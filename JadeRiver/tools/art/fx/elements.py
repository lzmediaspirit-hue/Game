"""The eleven elements of the technique FX: a palette each (the index ramp fxpix draws in) and the flourishes that
make an element read as itself on any form: water in droplets and ripples, fire in tongues and embers, wood in
leaves, earth in rock and dust, metal in shards and glints, wind in streaks, thunder in forked bolts, soul in thin
rings and wisps, formless in plain ink flicks, space in stars over a dark rift, time in ticks and a ghost of the
frame before.

Colours sit on the game's element colours (data/elements.json) and the Style A emblems' mark ramps
(tools/icons/families/techniques.py DISCS), so an art's effect matches its icon.
"""
from __future__ import annotations

import math

from fxpix import ACCENT, BASE, CORE, DEEP, GLINT, HAZE, INK, LIGHT, Canvas, px_hash

ELEMENTS = ["water", "wood", "fire", "earth", "metal", "wind", "thunder", "soul", "formless", "space", "time"]

# element -> {index: (r, g, b, a)}
_P = {
    "water": dict(ink="#081E2C", deep="#1E5A70", base="#32BED1", light="#9EE0EC", glint="#DDF8FB", accent="#FFFFFF"),
    "wood": dict(ink="#0A2014", deep="#2A6A34", base="#67D67A", light="#B0E08A", glint="#E6F8CC", accent="#F6FFD0"),
    "fire": dict(ink="#2A0A08", deep="#9A3012", base="#F08A3C", light="#FFB850", glint="#FFEAA6", accent="#FFE6A1"),
    "earth": dict(ink="#1E1408", deep="#74522A", base="#C9A060", light="#E6C88A", glint="#FAEECC", accent="#8E6A3A"),
    "metal": dict(ink="#121A24", deep="#56687C", base="#B8C4CE", light="#E4ECF2", glint="#FFFFFF", accent="#FFFFFF"),
    "wind": dict(ink="#0E3234", deep="#3A8A80", base="#8FD0C8", light="#CFE8E6", glint="#EEFFFA", accent="#FFFFFF"),
    "thunder": dict(ink="#2A2206", deep="#8A7418", base="#E8D24C", light="#F4E070", glint="#FFF6C0", accent="#FFFFFF"),
    "soul": dict(ink="#150C26", deep="#553A90", base="#9B78D1", light="#D0BCF6", glint="#F2EAFF", accent="#F2EAFF"),
    "formless": dict(ink="#1A2830", deep="#9E9580", base="#E8E1CF", light="#FFFBEF", glint="#FFFFFF", accent="#2E424C"),
    "space": dict(ink="#0C0A24", deep="#4C46A0", base="#8F7AE0", light="#C4BCF4", glint="#ECE8FF", accent="#FFFFFF"),
    "time": dict(ink="#1A2A3C", deep="#4E7A98", base="#A8CCE0", light="#D6F5FF", glint="#EEF8FF", accent="#FFFFFF"),
}


def _rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def palette(element: str):
    """Index -> RGBA for one element (a numpy-ready lookup of 9 rows)."""
    p = _P[element]
    lut = [(0, 0, 0, 0)] * 9
    lut[INK] = _rgb(p["ink"]) + (255,)
    lut[DEEP] = _rgb(p["deep"]) + (255,)
    lut[BASE] = _rgb(p["base"]) + (255,)
    lut[LIGHT] = _rgb(p["light"]) + (255,)
    lut[GLINT] = _rgb(p["glint"]) + (255,)
    lut[CORE] = (255, 255, 255, 255)
    lut[ACCENT] = _rgb(p["accent"]) + (255,)
    lut[HAZE] = _rgb(p["base"]) + (110,)
    return lut


# ------------------------------------------------------------------------------------------------ particles
def particle(cv: Canvas, el: str, x: float, y: float, vx: float, vy: float, age: float, seed: int, big: bool = False) -> None:
    """One flourish of the element at (x, y), moving (vx, vy) (art px a frame), `age` 0..1 over its life."""
    if age < 0.0 or age > 1.0:
        return
    fade = age > 0.66
    if el == "water":
        # a droplet: a glint head and a lighter tail below it, falling as it ages
        cv.dot(x, y, GLINT if not fade else LIGHT, 2 if big and age < 0.5 else 1)
        cv.dot(x, y + 1, LIGHT if not fade else BASE)
        if big and age < 0.4:
            cv.dot(x, y - 1, CORE)
    elif el == "fire":
        # a flame tongue rising: a teardrop of base, lit at the heart, with an ember above it
        h = (4 if big else 3) * (1.0 - age * 0.6)
        cv.stroke_seg((x, y), (x + vx * 0.3, y - h), 3.0 if big else 2.0, 1.0,
                      table=((0.4, LIGHT), (1.0, BASE)) if not fade else ((1.0, DEEP),))
        if age < 0.7:
            cv.dot(x + (px_hash(seed, 3) - 0.5) * 2, y - h - 1 - age * 3, ACCENT)
    elif el == "wood":
        # a leaf: a 3 x 2 diagonal, turned by its age
        k = int(age * 3 + px_hash(seed, 5) * 3) % 3
        rows = (["LB.", ".BL"], [".L.", "LBL"], ["B.L", ".L."])[k]
        cv.stamp(rows, x - 1, y, {"L": LIGHT if not fade else BASE, "B": BASE if not fade else DEEP})
    elif el == "earth":
        # a chunk of rock, angular and dark, and a puff of dust behind it as it lands
        s = 3 if big and age < 0.5 else 2
        cv.dot(x, y, BASE, s)
        cv.dot(x + s * 0.5 - 1, y + s * 0.5 - 1, DEEP)
        if age > 0.5:
            cv.dot(x - vx, y + 1, HAZE, 2)
    elif el == "metal":
        # a shard: a short bright diagonal with a plus glint on its head
        L = 4 if big else 3
        n = math.hypot(vx, vy) or 1.0
        cv.line1((x, y), (x - vx / n * L, y - vy / n * L), LIGHT if not fade else DEEP)
        if age < 0.5:
            cv.plus(x, y, GLINT, 1)
    elif el == "wind":
        # a curved streak along the flight, thin and pale
        n = math.hypot(vx, vy) or 1.0
        ux, uy = vx / n, vy / n
        L = 7 if big else 5
        pts = [(x - ux * i - uy * (i * i) * 0.06, y - uy * i + ux * (i * i) * 0.06) for i in range(0, L)]
        for i in range(len(pts) - 1):
            cv.line1(pts[i], pts[i + 1], GLINT if (i < 2 and not fade) else LIGHT)
    elif el == "thunder":
        # a forked bolt: a zigzag away from the source with a white core
        n = math.hypot(vx, vy) or 1.0
        ux, uy = vx / n, vy / n
        px_, py_ = -uy, ux
        L = 6 if big else 4
        p = (x, y)
        pts = [p]
        for i in range(1, L + 1):
            side = (px_hash(seed, i) - 0.5) * 2.5
            pts.append((x + ux * i * 1.4 + px_ * side, y + uy * i * 1.4 + py_ * side))
        for i in range(len(pts) - 1):
            cv.line1(pts[i], pts[i + 1], CORE if (i < 2 and age < 0.5) else GLINT)
        if big and age < 0.5:
            b = pts[len(pts) // 2]
            cv.line1(b, (b[0] + px_ * 3 + ux, b[1] + py_ * 3 + uy), GLINT)
    elif el == "soul":
        # a wisp: a pale head and two deep dots trailing it
        cv.dot(x, y, GLINT if not fade else LIGHT)
        cv.dot(x - vx * 0.8, y - vy * 0.8, DEEP)
        if big:
            cv.dot(x - vx * 1.6, y - vy * 1.6, DEEP)
    elif el == "formless":
        # an ink flick: plain, one or two dots of ink
        cv.dot(x, y, ACCENT if not fade else DEEP)
        if big and age < 0.5:
            cv.dot(x - vx * 0.7, y - vy * 0.7, DEEP)
    elif el == "space":
        # a star that twinkles: a plus one frame, a dot the next
        if int(age * 6 + seed) % 2 == 0:
            cv.plus(x, y, ACCENT if not fade else LIGHT, 2 if big else 1)
        else:
            cv.dot(x, y, GLINT)
    elif el == "time":
        # a tick of a clock: a short bright line, and the echo of where it was
        n = math.hypot(vx, vy) or 1.0
        cv.line1((x, y), (x - vx / n * 2, y - vy / n * 2), CORE if age < 0.5 else GLINT)
        cv.dot(x - vx * 1.5, y - vy * 1.5, DEEP)


def fling(cv: Canvas, el: str, pts, f: int, n: int, band: int, seed: int, count: int, spread: float = 1.0,
          gravity: float = 0.35, life: int = 5, start: int = 0, speed: float = 2.2) -> None:
    """Particles flung from sample points `pts` = [(x, y, nx, ny), ...] (a point and its outward normal), born over
    the first frames and flying out along the normal with a little gravity. `count` scales with the band."""
    total = int(count * (1.0, 1.6, 2.4)[band])
    for i in range(total):
        h0, h1, h2, h3 = px_hash(seed, i, 1), px_hash(seed, i, 2), px_hash(seed, i, 3), px_hash(seed, i, 4)
        x0, y0, nx, ny = pts[int(h0 * len(pts)) % len(pts)]
        born = start + int(h1 * max(1, n - life - start))
        age_f = f - born
        if age_f < 0 or age_f > life:
            continue
        sp = speed * (0.6 + h2 * 0.8)
        # a spread round the normal
        ang = math.atan2(ny, nx) + (h3 - 0.5) * 1.2 * spread
        vx, vy = math.cos(ang) * sp, math.sin(ang) * sp
        x = x0 + vx * age_f
        y = y0 + vy * age_f + gravity * age_f * age_f
        particle(cv, el, x, y, vx, vy + gravity * age_f, age_f / max(1, life), seed * 31 + i, big=(band > 0 and h2 > 0.6))


def ring_burst(cv: Canvas, el: str, cx: float, cy: float, r: float, f: int, n: int, band: int, seed: int, count: int,
               sy: float = 0.35, rise: float = 0.0, start: int = 0, life: int = 6) -> None:
    """Particles that leave a ring of radius r (y squashed) outward, rising a little (rise px a frame)."""
    total = int(count * (1.0, 1.6, 2.4)[band])
    for i in range(total):
        h0, h1, h2 = px_hash(seed, i, 7), px_hash(seed, i, 8), px_hash(seed, i, 9)
        ang = h0 * 2 * math.pi
        born = start + int(h1 * max(1, n - life - start))
        age_f = f - born
        if age_f < 0 or age_f > life:
            continue
        sp = 1.4 + h2 * 1.6
        vx, vy = math.cos(ang) * sp, math.sin(ang) * sp * sy - rise
        x = cx + math.cos(ang) * r + vx * age_f
        y = cy + math.sin(ang) * r * sy + vy * age_f
        particle(cv, el, x, y, vx, vy, age_f / max(1, life), seed * 17 + i, big=(band > 1 and h2 > 0.5))


def dress_edge(cv: Canvas, el: str, pts, f: int, n: int, band: int, seed: int, every: int = 3) -> None:
    """Element dressing along a stroke's outer edge: sample points `pts` = [(x, y, nx, ny)] with outward normals.
    Fire grows tongues, water beads droplets, wood hangs leaves, earth crumbs, metal glints, wind streaks, thunder
    forks, soul rings, formless nothing but a flick, space stars, time ticks."""
    step = max(1, every - band)
    for i, (x, y, nx, ny) in enumerate(pts):
        if i % step:
            continue
        h = px_hash(seed, i, 11)
        k = 1.0 + band * 0.5
        if el == "fire":
            hh = (2 + h * 3) * k
            cv.stroke_seg((x, y), (x + nx * hh * 0.4, y - hh), 2.5 if band else 2.0, 1.0, table=((0.45, LIGHT), (1.0, BASE)))
            if h > 0.5:
                cv.dot(x + nx * 2, y - hh - 1.5, ACCENT)
        elif el == "water":
            cv.dot(x + nx * (1.5 + h * 2 * k), y + ny * (1.5 + h * 2 * k) + 1, GLINT)
            cv.dot(x + nx * (1.5 + h * 2 * k), y + ny * (1.5 + h * 2 * k) + 2, LIGHT)
        elif el == "wood":
            if h > 0.35:
                particle(cv, el, x + nx * 2.5, y + ny * 2.5, nx, ny, 0.2 + h * 0.3, seed + i)
        elif el == "earth":
            cv.dot(x + nx * 1.5, y + ny * 1.5, DEEP, 2 if h > 0.5 else 1)
            if band:
                cv.dot(x + nx * 3.5, y + ny * 3.5 + 1, HAZE, 2)
        elif el == "metal":
            if h > 0.45:
                cv.plus(x + nx * 1.5, y + ny * 1.5, GLINT, 1 + (1 if band > 1 and h > 0.8 else 0))
        elif el == "wind":
            cv.line1((x + nx * 2.5, y + ny * 2.5), (x + nx * (2.5 + 3 * k) - ny * 3 * k, y + ny * (2.5 + 3 * k) + nx * 3 * k), LIGHT)
        elif el == "thunder":
            if h > 0.4:
                particle(cv, el, x + nx, y + ny, nx * 2, ny * 2, 0.3 + h * 0.3, seed + i, big=band > 0)
        elif el == "soul":
            if h > 0.5:
                cv.ring(x + nx * (2 + k), y + ny * (2 + k), 1.5 + band * 0.5, 1.0, DEEP if h < 0.75 else LIGHT)
        elif el == "formless":
            if h > 0.7:
                cv.dot(x + nx * 2.5, y + ny * 2.5, DEEP)
        elif el == "space":
            if h > 0.45:
                particle(cv, el, x + nx * (2.5 + h * 2), y + ny * (2.5 + h * 2), nx, ny, (f % 3) / 3.0, seed + i, big=band > 1)
        elif el == "time":
            if h > 0.5:
                cv.line1((x + nx * 2, y + ny * 2), (x + nx * (3.5 + band), y + ny * (3.5 + band)), CORE if (i + f) % 2 else GLINT)


def ground_ripple(cv: Canvas, el: str, cx: float, cy: float, r: float, f: int, n: int, band: int, sy: float = 0.35) -> None:
    """The element's mark on the ground round a point: water's ripple rings, fire's ember ring, earth's crack
    lines, wood's sprouting leaves, thunder's arcs, soul's ring, space's dark rift ring; the rest a faint ring."""
    k = f / max(1, n - 1)
    if el == "water":
        for j in range(1 + band):
            rr = r * (0.4 + 0.6 * ((k + j * 0.3) % 1.0))
            cv.ring(cx, cy, rr, 1.0, LIGHT if j == 0 else DEEP, sy)
    elif el == "fire":
        for i in range(6 + band * 4):
            ang = px_hash(i, 21) * 2 * math.pi
            cv.dot(cx + math.cos(ang) * r * (0.9 + 0.2 * px_hash(i, 22)), cy + math.sin(ang) * r * sy - k * 4 - px_hash(i, 23) * 3, ACCENT)
    elif el == "earth":
        for i in range(4 + band * 2):
            ang = px_hash(i, 31) * 2 * math.pi
            p0 = (cx + math.cos(ang) * r * 0.3, cy + math.sin(ang) * r * 0.3 * sy)
            p1 = (cx + math.cos(ang + 0.2) * r * (0.7 + 0.3 * k), cy + math.sin(ang + 0.2) * r * (0.7 + 0.3 * k) * sy)
            cv.line1(p0, p1, DEEP)
    elif el == "wood":
        for i in range(5 + band * 3):
            ang = px_hash(i, 41) * 2 * math.pi
            particle(cv, el, cx + math.cos(ang) * r * 0.8, cy + math.sin(ang) * r * 0.8 * sy - k * 3, 0, -1, k, i)
    elif el == "thunder":
        for i in range(3 + band * 2):
            a0 = px_hash(i, 51) * 2 * math.pi + k * 2
            cv.ring(cx, cy, r * 0.95, 1.0, GLINT, sy, a0=a0, a1=a0 + 0.6)
    elif el == "soul":
        cv.ring(cx, cy, r * (0.5 + 0.5 * k), 1.0, LIGHT, sy)
        cv.ring(cx, cy, r * (0.3 + 0.7 * k), 1.0, DEEP, sy)
    elif el == "space":
        cv.ring(cx, cy, r, 2.0, INK, sy)
        cv.ring(cx, cy, r + 1.5, 1.0, GLINT, sy)
    elif el == "time":
        for i in range(12):
            ang = i * math.pi / 6 + k * 0.4
            p0 = (cx + math.cos(ang) * r * 0.9, cy + math.sin(ang) * r * 0.9 * sy)
            p1 = (cx + math.cos(ang) * r * 1.05, cy + math.sin(ang) * r * 1.05 * sy)
            cv.line1(p0, p1, CORE if i % 3 == 0 else LIGHT)
    elif el == "metal":
        for i in range(4 + band * 2):
            ang = px_hash(i, 61) * 2 * math.pi
            cv.plus(cx + math.cos(ang) * r, cy + math.sin(ang) * r * sy, GLINT, 1)
    elif el == "wind":
        for i in range(3 + band):
            a0 = px_hash(i, 71) * 2 * math.pi + k * 3
            cv.ring(cx, cy, r * 1.05, 1.0, LIGHT, sy, a0=a0, a1=a0 + 1.0)
    else:
        cv.ring(cx, cy, r, 1.0, DEEP, sy)
