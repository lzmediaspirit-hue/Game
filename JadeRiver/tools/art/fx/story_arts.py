"""The story's own arts in the top-down world (decision 45, docs/redesign/story_staging.md "The first boss"): the
first boss's waking and the three arts the elders of Lotus Ferry slay it with, drawn on the ground plane of the
world's 3/4 view (plane.py) like the technique forms, at art resolution, nearest neighbour, in the index tones of
fxpix, each in a palette of its own. The staged scenes play them where a target stands (SceneDirector's `art` step,
TopdownFx.story).

  river_boil      the river boils round the Hollowed eel as it wakes: a grey stain spreading, rings racing out,
                  spouts of grey water leaping and falling, bubbles bursting (flat, on the water under it)
  talisman_array  Granny Liu's Nine Seals: nine paper talismans spiral in and plant themselves round the foe, a double
                  ring and a nine-pointed star of vermilion ink join them, and the array flares, a wall of light
                  rising off every seal (flat, under the bound foe)
  force_palm      Old Ma's Thousand-Catty Palm: a golden palm the size of a door falls out of the dark onto the foe,
                  fingers up, and slams it into the ground: a shock ring, cracks, stone chips, and the print's
                  after-image fading (upright, over the foe)
  water_dragon    Lu's Coiling River Dragon: the river rises as a dragon, horned and whiskered, arches over the bank and
                  dives onto the foe, bursting into a crown of spray (upright, over the foe)

A drawer is `draw(pl, f, n)`: frame f of n on the Plane `pl` (its canvas and its anchor on the floor, facing east: the
arts are round, drawn once). STORY holds each art's spec for build_fx_topdown.py: its canvas and anchor (art px, before
the build's crop), frames, fps, the frame its blow lands on (`impact`), its layer (`floor`: under the bodies in it;
`sorted`: in front of the body at its anchor), how far north of its anchor a flat one reaches (`north`, its sort
key) and its palette. Everything is deterministic (px_hash gives the variety): the sheets rebuild byte-identical.
"""
from __future__ import annotations

import math

from elements import fling, palette as element_palette, particle
from forms import star
from fxpix import (ACCENT, BASE, CORE, DEEP, GLINT, GLOW_BANDS, HAZE, INK, LIGHT, SOFT_BANDS, STROKE_BANDS, ease_in,
                   ease_out, lerp, px_hash)
from plane import Plane
from wuxia import palm_print, talisman

# ------------------------------------------------------------------------------------------ palettes
# index -> colour, as elements.palette: ink, deep, base, light, glint, (core white), accent, haze (base, half there)
_P = {
    # the Hollow's grey water: slate and violet-grey, a sick pale glint (the eel's own colours)
    "hollow": dict(ink="#0C1018", deep="#3A3652", base="#6C6886", light="#A7A1BE", glint="#DAD5E8", accent="#B8F0E2"),
    # a talisman array: vermilion ink, gold light, paper white
    "talisman": dict(ink="#2A0B08", deep="#B3301E", base="#E3B458", light="#F4DC9A", glint="#FFF6DA", accent="#D8402E"),
    # a palm of force: old gold and bronze, a warm white core
    "palm": dict(ink="#1F1306", deep="#8C5A1C", base="#DDA43E", light="#F3D27C", glint="#FFF1C4", accent="#FFFFFF"),
}


def _rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def palette(name: str):
    """Index -> RGBA for a story palette (the water dragon takes the water element's)."""
    if name not in _P:
        return element_palette(name)
    p = _P[name]
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


# ------------------------------------------------------------------------------------------ the river boils
def river_boil(pl: Plane, f: int, n: int) -> None:
    """The river boiling round the waking eel (the scene's `eel_awakens`): a grey stain spreading on the water, rings
    racing out of it, spouts of grey water leaping up round it in turn and falling back in drops, bubbles bursting."""
    cv = pl.cv
    gx, gy = pl.pt(0, 0, 0)
    u = f / max(1, n - 1)
    grow = ease_out(min(1.0, (f + 1) / 4.0))
    fade = 1.0 if f < n - 3 else (n - f) / 3.0
    # the stain: a dark dithered pool, a deeper heart
    cv.paint(cv.mask_ellipse(gx, gy, 40 * grow, 40 * grow), HAZE, "dither")
    cv.paint(cv.mask_ellipse(gx, gy, 18 * grow, 18 * grow), DEEP, "dither")
    # rings racing out, three at a time
    for k in range(3):
        r = ((f * 5 + k * 17) % 50) + 8
        if r < 48 * grow + 4:
            cv.ring(gx, gy, r, 1.0, LIGHT if r < 26 else (BASE if r < 40 else DEEP))
    # bubbles rising and bursting
    for i in range(12):
        a = px_hash(i, 511) * 2 * math.pi
        rr = 6 + px_hash(i, 512) * 34 * grow
        x, y = gx + math.cos(a) * rr, gy + math.sin(a) * rr
        t = (f + int(px_hash(i, 513) * 5)) % 5
        if t < 3:
            cv.dot(x, y, LIGHT if t < 2 else GLINT, 2 if t == 1 else 1)
        elif t == 3 and fade > 0.5:
            cv.plus(x, y, GLINT, 1)
    # spouts leaping in turn round the eel, and their drops
    for i in range(7):
        a = i * 2 * math.pi / 7 + 0.4
        rr = 24 + px_hash(i, 521) * 14
        x, y = gx + math.cos(a) * rr, gy + math.sin(a) * rr
        born = int(px_hash(i, 522) * (n - 6))
        t = f - born
        if t < 0 or t > 5:
            continue
        h = (18 + px_hash(i, 523) * 14) * math.sin(math.pi * min(1.0, t / 5.0)) * fade
        w = 9.0 - t * 0.8
        if h > 2.0:
            # a column of grey water, fat at its foot, its head breaking into a crown of drops
            cv.stroke_seg((x, y), (x, y - h), w, max(3.0, w * 0.55), table=((0.25, GLINT), (0.55, LIGHT), (0.85, BASE), (1.0, DEEP)))
            cv.disc(x, y - h, max(2.0, w * 0.4), table=((0.5, GLINT), (1.0, LIGHT)))
            for c in (-1, 1):
                cv.dot(x + c * (w * 0.5 + t), y - h + t * 1.5, LIGHT)
            cv.dot(x, y - h - 2, CORE if t < 3 else GLINT)
        cv.ring(x, y, 2 + t, 1.0, LIGHT if t < 3 else DEEP)
        for d in range(3):
            if t >= 2:
                dx = (d - 1) * (2 + t)
                cv.dot(x + dx, y - h * 0.6 + (t - 2) * 3, LIGHT if d % 2 else GLINT)
    if u > 0.1 and fade > 0.3:
        cv.ring(gx, gy, 10 + (f % 3), 1.0, GLINT)


# ------------------------------------------------------------------------------------------ Granny Liu's Nine Seals
SEALS = 9
ARRAY_R = 34.0


def _seal_at(i: int, r: float, spin: float) -> tuple:
    a = i * 2 * math.pi / SEALS - math.pi / 2 + spin
    return a, r * math.cos(a), r * math.sin(a)


def talisman_array(pl: Plane, f: int, n: int) -> None:
    """Granny Liu's Nine Seals (the scene's `elders_come`): nine paper talismans spiral in out of the dark and plant
    themselves upright on a ring round the foe; a double ring and a nine-pointed star of vermilion ink draw
    themselves between them; on the impact frame the array flares, a wall of light rising off every seal and a
    starburst at its heart; then it holds, pulsing, the seals scorching as the ink burns bright."""
    cv = pl.cv
    gx, gy = pl.pt(0, 0, 0)
    land, impact = 6, 9
    if f < land:
        # the seals in flight: spiralling in and dropping as they come
        u = ease_out((f + 1) / land)
        for i in range(SEALS):
            a, x, y = _seal_at(i, lerp(78.0, ARRAY_R, u), (1.0 - u) * 1.6)
            hh = lerp(34.0, 0.0, u)
            talisman(cv, gx + x - 2, gy + y - 13 - hh, 12, tilt=(1.0 - u) * 4 * math.cos(a), lit=True)
            if f > 0:
                _, x0, y0 = _seal_at(i, lerp(78.0, ARRAY_R, ease_out(f / land)), (1.0 - ease_out(f / land)) * 1.6)
                cv.line1((gx + x0, gy + y0 - 6 - lerp(34.0, 0.0, ease_out(f / land))), (gx + x, gy + y - 6 - hh), LIGHT)
        return
    k = min(1.0, (f - land + 1) / (impact - land + 1))
    burn = max(0.0, (f - impact) / max(1, n - impact - 1))
    # the double ring and the star, drawn in by k
    ring_tone = GLINT if f == impact else (LIGHT if burn < 0.6 else BASE)
    cv.ring(gx, gy, ARRAY_R + 6, 1.5 if f >= impact else 1.0, ring_tone, a0=-math.pi / 2, a1=-math.pi / 2 + 2 * math.pi * k)
    cv.ring(gx, gy, ARRAY_R - 5, 1.0, DEEP if f < impact else LIGHT, a0=-math.pi / 2, a1=-math.pi / 2 + 2 * math.pi * k)
    order = [(i * 4) % SEALS for i in range(SEALS + 1)]          # the nine-pointed star {9/4}
    drawn = int(round(k * SEALS))
    for s in range(drawn):
        _, x0, y0 = _seal_at(order[s], ARRAY_R - 5, 0.0)
        _, x1, y1 = _seal_at(order[s + 1], ARRAY_R - 5, 0.0)
        cv.line1((gx + x0, gy + y0), (gx + x1, gy + y1), ACCENT if f < impact else (GLINT if burn < 0.5 else LIGHT))
    # glyph ticks round the outer ring, turning
    for i in range(18):
        a = i * math.pi / 9 + f * 0.05
        if a > -math.pi / 2 + 2 * math.pi * k + math.pi / 2:
            continue
        x0, y0 = gx + math.cos(a) * (ARRAY_R + 3), gy + math.sin(a) * (ARRAY_R + 3)
        x1, y1 = gx + math.cos(a) * (ARRAY_R + 9), gy + math.sin(a) * (ARRAY_R + 9)
        cv.line1((x0, y0), (x1, y1), DEEP if i % 2 else LIGHT)
    # the flare: a wall of light off every seal, a burst at the heart
    if f >= impact:
        wall = (38.0 if f == impact else 30.0) * (1.0 - burn) ** 0.7
        for i in range(SEALS):
            _, x, y = _seal_at(i, ARRAY_R, 0.0)
            if wall > 3:
                cv.stroke_seg((gx + x, gy + y), (gx + x, gy + y - wall), 3.0, 1.0, table=((0.4, CORE if f == impact else GLINT), (1.0, LIGHT)))
        if f == impact:
            star(cv, gx, gy - 8, 22, points=8, w=3.0)
            cv.ring(gx, gy, ARRAY_R + 12, 2.0, GLINT)
        elif burn < 0.5:
            cv.ring(gx, gy, ARRAY_R + 12 + (f - impact) * 4, 1.0, LIGHT)
        # motes rising off the array
        for i in range(10):
            uu = ((f - impact) * 0.13 + px_hash(i, 531)) % 1.0
            a = px_hash(i, 532) * 2 * math.pi
            rr = px_hash(i, 533) * ARRAY_R
            cv.dot(gx + math.cos(a) * rr, gy + math.sin(a) * rr - uu * 40, GLINT if i % 2 else LIGHT)
    # the seals themselves, planted upright on the ring (the near ones drawn last)
    seals = sorted(range(SEALS), key=lambda i: _seal_at(i, ARRAY_R, 0.0)[2])
    for i in seals:
        _, x, y = _seal_at(i, ARRAY_R, 0.0)
        h = 12.0 * (1.0 - burn * 0.6)
        if burn > 0.75 and px_hash(i, 534) < burn:
            cv.dot(gx + x, gy + y - 3, DEEP, 2)          # burnt to a scrap of ash
            continue
        talisman(cv, gx + x - 2, gy + y - h, h, tilt=0.0, lit=burn < 0.4)
        if f >= impact and burn < 0.5:
            cv.dot(gx + x, gy + y - h - 2, CORE)


# ------------------------------------------------------------------------------------------ Old Ma's palm
def force_palm(pl: Plane, f: int, n: int) -> None:
    """Old Ma's Thousand-Catty Palm: a golden palm the size of a door falls out of the dark onto the foe, fingers to the
    sky and speed lines above it, and slams down on the impact frame: a starburst, a shock ring racing over the ground,
    cracks, chips of stone flung out; the print's after-image holds and fades, a ring of dust settling."""
    cv = pl.cv
    gx, gy = pl.pt(0, 0, 0)
    impact = 5
    S = 70.0
    if f < impact:
        u = ease_in((f + 1) / impact)
        h = lerp(150.0, 34.0, u)
        s = lerp(34.0, S, u)
        cy = gy - h
        # speed lines above it
        for i in range(7):
            x = gx + (i - 3) * s * 0.16
            L = 20 + u * 26
            cv.line1((x, cy - s * 0.7 - L), (x, cy - s * 0.7 - 4), LIGHT if i % 2 else BASE)
        cv.disc(gx, cy, s * 0.62, table=((0.6, HAZE), (1.0, HAZE)), mode="under")
        palm_print(cv, gx, cy, s, -math.pi / 2, tone=LIGHT if u < 0.8 else GLINT, rim=BASE)
        cv.ring(gx, gy, 10 + u * 14, 1.0, DEEP)          # its shadow of light on the ground, closing
        return
    t = f - impact
    u = t / max(1, n - impact - 1)
    # the print slammed down (flattened toward the ground), then its after-image fading
    if t == 0:
        palm_print(cv, gx, gy - 26, S, -math.pi / 2, tone=CORE, rim=GLINT)
        star(cv, gx, gy - 10, 30, points=8, w=3.5)
    elif u < 0.55:
        tone = GLINT if u < 0.2 else (LIGHT if u < 0.4 else BASE)
        palm_print(cv, gx, gy - 22 - t * 1.5, S * (1.0 + u * 0.15), -math.pi / 2, tone=tone, rim=DEEP)
    else:
        ghost = cv.mask_ellipse(gx, gy - 24 - t, S * 0.45, S * 0.45)
        cv.paint(ghost, HAZE, "dither")
    # the shock ring on the ground, and a second after it
    r = 16 + ease_out(min(1.0, u * 1.6)) * 58
    if u < 0.85:
        cv.ring(gx, gy, r, 3.0 * (1.0 - u) + 1.0, GLINT if u < 0.3 else (LIGHT if u < 0.6 else DEEP))
    if 0.15 < u < 0.95:
        cv.ring(gx, gy, r * 0.62, 1.0, BASE)
    # cracks radiating from the blow
    for i in range(8):
        a = i * 2 * math.pi / 8 + px_hash(i, 541) * 0.5
        L = (14 + px_hash(i, 542) * 18) * min(1.0, (t + 1) / 2.0)
        mx, my = gx + math.cos(a) * L * 0.55, gy + math.sin(a) * L * 0.55
        bend = (px_hash(i, 543) - 0.5) * 6
        tone = INK if u < 0.7 else DEEP
        cv.line1((gx, gy), (mx + bend, my), tone)
        cv.line1((mx + bend, my), (gx + math.cos(a) * L, gy + math.sin(a) * L), tone)
    # stone chips and dust flung out, falling
    for i in range(14):
        a = px_hash(i, 544) * 2 * math.pi
        sp = 2.0 + px_hash(i, 545) * 3.0
        x = gx + math.cos(a) * (10 + sp * t * 2.2)
        y = gy + math.sin(a) * (6 + sp * t * 1.4) - (sp * 3 * t - 1.2 * t * t)
        if y > gy + 30 or t > 7:
            continue
        cv.dot(x, y, (DEEP, BASE, LIGHT)[i % 3], 2 if i % 4 == 0 else 1)


# ------------------------------------------------------------------------------------------ Lu's river dragon
# The dragon's flight: a curve through the air (forward x, right y toward the river, height h, art px), out of the
# river beside the foe, up and over the bank and down onto it.
_FLIGHT = [(56, 40, -14), (50, 34, 28), (40, 22, 84), (20, 8, 126), (-6, -2, 130), (-26, -2, 96), (-16, 0, 48), (0, 0, 4)]


def _flight(s: float) -> tuple:
    """A point on the dragon's flight at s in [0, 1] (Catmull-Rom through _FLIGHT, its ends held)."""
    pts = [_FLIGHT[0]] + _FLIGHT + [_FLIGHT[-1]]
    segs = len(_FLIGHT) - 1
    u = min(max(s, 0.0), 1.0) * segs
    i = min(int(u), segs - 1)
    t = u - i
    p0, p1, p2, p3 = pts[i], pts[i + 1], pts[i + 2], pts[i + 3]
    return tuple(0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (3 * b - a - 3 * c + d) * t * t * t)
                 for a, b, c, d in zip(p0, p1, p2, p3))


def water_dragon(pl: Plane, f: int, n: int) -> None:
    """Lu's Coiling River Dragon: the river rises as a dragon of water, horned, whiskered and finned, the river pouring
    off it; it arches high over the bank and dives head first onto the foe on the impact frame, bursting into a crown
    of spray, rings racing over the ground; its body falls back as rain, the last of it a mist of drops."""
    cv = pl.cv
    gx, gy = pl.pt(0, 0, 0)
    impact = 11
    body = 0.5
    if f <= impact:
        head = 0.12 + 0.88 * (ease_in(f / impact) * 0.35 + (f / impact) * 0.65)
        tail = max(0.0, head - body)
        samples = [tail + (head - tail) * i / 23.0 for i in range(24)]
        pts3 = [_flight(s) for s in samples]
        seen = [(pl.pt(x, y, max(h, 0.0)), h) for x, y, h in pts3]
        # the river where it leaves the water: foam rings
        wx, wy = pl.pt(_FLIGHT[0][0] - 4, _FLIGHT[0][1] - 4, 0)
        for k in range(2):
            cv.ring(wx, wy, 6 + ((f + k * 3) % 6) * 3, 1.0, LIGHT if k == 0 else BASE)
        above = [p for p, h in seen if h > -2.0]
        if len(above) >= 2:
            # the body: thick at the head, thinning to the tail, lit along its back, scaled
            n_ = len(above)
            cv.stroke_poly(above, 7.0, 24.0, table=((0.2, GLINT), (0.45, LIGHT), (0.78, BASE), (1.0, DEEP)))
            for i in range(0, n_ - 1):
                (x0, y0), (x1, y1) = above[i], above[i + 1]
                dx, dy = x1 - x0, y1 - y0
                d = math.hypot(dx, dy) or 1.0
                nx, ny = dy / d, -dx / d
                if ny > 0:
                    nx, ny = -nx, -ny                     # its back is the side toward the sky
                w = (7.0 + 17.0 * i / n_) * 0.5
                # the light running along its back, and a scale's arc every other step on its flank
                cv.dot(x0 + nx * w * 0.45, y0 + ny * w * 0.45, CORE if i % 3 == 0 else GLINT)
                if i % 2 == 0 and i < n_ - 3:
                    cv.line1((x0 - nx * w * 0.15 - dx / d * 2, y0 - ny * w * 0.15 - dy / d * 2),
                             (x0 - nx * w * 0.55, y0 - ny * w * 0.55), DEEP)
                # the fins off its back: a crest of water flames, taller toward the head
                if i % 2 == 0:
                    fh = 4.0 + 7.0 * i / n_
                    cv.stroke_seg((x0 + nx * w * 0.8, y0 + ny * w * 0.8), (x0 + nx * (w + fh) - dx / d * 4, y0 + ny * (w + fh) - dy / d * 4),
                                  3.0, 1.0, table=((0.45, LIGHT), (1.0, BASE)))
            # the river pouring off it: drops falling from its belly
            for i in range(16):
                j = int(px_hash(i, 551, f) * (n_ - 1))
                x, y = above[j]
                cv.dot(x + (px_hash(i, 552) - 0.5) * 12, y + 8 + px_hash(i, 553, f) * 14, GLINT if i % 2 else LIGHT)
        # the head: a skull along its flight, the snout ahead, an eye, antlers swept back, a mane, whiskers trailing
        hx, hy = seen[-1][0]
        px_, py_ = seen[-3][0]
        dx, dy = hx - px_, hy - py_
        d = math.hypot(dx, dy) or 1.0
        ux, uy = dx / d, dy / d
        vx, vy = -uy, ux
        if vy > 0:
            vx, vy = -vx, -vy
        for m in range(5):                                # the mane behind the skull, flowing back like water
            a = (m - 2) * 0.45
            mx_, my_ = hx - ux * 6 + vx * (m - 2) * 3, hy - uy * 6 + vy * (m - 2) * 3
            L = 12 + (m % 2) * 5
            cv.stroke_seg((mx_, my_), (mx_ - ux * L + vx * (6 + a * 4), my_ - uy * L + vy * (6 + a * 4)), 4.0, 1.0,
                          table=((0.5, LIGHT), (1.0, BASE)))
        cv.disc(hx, hy, 12.0, table=((0.3, GLINT), (0.65, LIGHT), (0.9, BASE), (1.0, DEEP)))
        gape = 0.0 if f < impact - 3 else 5.0
        cv.stroke_seg((hx, hy), (hx + ux * 19 + vx * gape * 0.5, hy + uy * 19 + vy * gape * 0.5), 15.0, 8.0,
                      table=((0.35, LIGHT), (0.8, BASE), (1.0, DEEP)))
        if gape:
            cv.stroke_seg((hx, hy), (hx + ux * 16 - vx * gape, hy + uy * 16 - vy * gape), 9.0, 4.0, table=((0.5, BASE), (1.0, DEEP)))
            cv.stroke_seg((hx + ux * 4, hy + uy * 4), (hx + ux * 13 - vx * gape * 0.4, hy + uy * 13 - vy * gape * 0.4), 3.0, 2.0,
                          table=((1.0, INK),))
            for k in range(3):
                cv.dot(hx + ux * (8 + k * 3) + vx * 1.5, hy + uy * (8 + k * 3) + vy * 1.5, CORE)
        ex, ey = hx + ux * 3 + vx * 6, hy + uy * 3 + vy * 6
        cv.dot(ex, ey, INK, 3)
        cv.dot(ex, ey, ACCENT)
        cv.dot(ex + ux, ey + uy, CORE)
        for side, L in ((1.0, 20.0), (0.55, 15.0)):     # antlers, each with a branch
            bx, by = hx - ux * 3 + vx * 9 * side, hy - uy * 3 + vy * 9 * side
            tx, ty = bx - ux * L + vx * 8, by - uy * L + vy * 8
            cv.stroke_seg((bx, by), (tx, ty), 3.0, 1.5, table=((0.5, GLINT), (1.0, LIGHT)))
            mx_, my_ = (bx + tx) * 0.5, (by + ty) * 0.5
            cv.line1((mx_, my_), (mx_ + vx * 6 - ux * 2, my_ + vy * 6 - uy * 2), GLINT)
        for side in (-1.0, 1.0):                          # the whiskers trailing from the snout
            sx, sy = hx + ux * 17, hy + uy * 17
            w1 = (sx - ux * 10 + vx * 8 * side, sy - uy * 10 + vy * 8 * side + math.sin(f * 1.3 + side) * 3)
            w2 = (sx - ux * 26 + vx * 4 * side, sy - uy * 26 + vy * 12 * side)
            cv.line1((sx, sy), w1, GLINT)
            cv.line1(w1, w2, LIGHT)
        if f == impact:
            star(cv, gx, gy - 6, 26, points=8, w=3.5)
            cv.ring(gx, gy, 20, 2.0, GLINT)
        return
    # the burst: a crown of spray, rings over the ground, the body falling back as rain
    t = f - impact
    u = t / max(1, n - impact - 1)
    for k in range(3):
        r = 14 + ease_out(min(1.0, u * 1.5)) * (34 + k * 14)
        if u < 0.9 - k * 0.15:
            cv.ring(gx, gy, r, 2.0 if k == 0 and u < 0.3 else 1.0, (GLINT, LIGHT, BASE)[k] if u < 0.5 else DEEP)
    # the crown: a ring of spouts round the blow, rising and collapsing
    for i in range(12):
        a = i * 2 * math.pi / 12
        rr = 10 + u * 22
        x, y = gx + math.cos(a) * rr, gy + math.sin(a) * rr * 0.9
        h = (26 + px_hash(i, 561) * 14) * math.sin(math.pi * min(1.0, u * 1.4))
        if h > 2:
            cv.stroke_seg((x, y), (x + math.cos(a) * 5, y - h), 7.0, 2.5, table=((0.3, GLINT), (0.6, LIGHT), (0.85, BASE), (1.0, DEEP)))
            cv.disc(x + math.cos(a) * 5, y - h, 2.0, table=((1.0, GLINT),))
    # the body's water falling back as rain along where it flew
    for i in range(26):
        s = px_hash(i, 562)
        x, y, h = _flight(0.4 + 0.6 * s)
        fall = h - t * (6 + px_hash(i, 563) * 6) - t * t * 0.6
        if fall < 0:
            continue
        px0, py0 = pl.pt(x + (px_hash(i, 564) - 0.5) * 10, y, fall)
        cv.dot(px0, py0, GLINT if i % 3 == 0 else LIGHT)
        if u < 0.5:
            cv.dot(px0, py0 + 1, BASE)
    # drops flung out of the burst
    pts = [(gx + math.cos(a) * 10, gy - 8 + math.sin(a) * 6, math.cos(a), math.sin(a) - 0.8)
           for a in [i * 2 * math.pi / 10 for i in range(10)]]
    fling(cv, "water", pts, t, n - impact, 2, 571, count=10, gravity=0.6, life=5, speed=3.0)
    if u > 0.6:
        for i in range(6):
            particle(cv, "water", gx + (px_hash(i, 572) - 0.5) * 50, gy - 4 - px_hash(i, 573) * 12, 0, 0.5, u, i)


# ------------------------------------------------------------------------------------------ the table
def _s(draw, canvas, anchor, frames, fps, impact, layer, pal, north=40):
    return dict(draw=draw, canvas=canvas, anchor=anchor, frames=frames, fps=fps, impact=impact, layer=layer, palette=pal, north=north)


STORY = {
    "river_boil": _s(river_boil, (120, 100), (60, 56), 12, 12, 3, "floor", "hollow", north=44),
    "talisman_array": _s(talisman_array, (128, 128), (64, 72), 16, 14, 9, "floor", "talisman", north=48),
    "force_palm": _s(force_palm, (150, 200), (75, 160), 13, 16, 5, "sorted", "palm"),
    "water_dragon": _s(water_dragon, (200, 200), (90, 160), 18, 14, 11, "sorted", "water"),
}
STORY_ORDER = list(STORY.keys())
