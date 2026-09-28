"""The wuxia marks of the top-down FX (decision 38's look rule): what makes a blow or an art read as xianxia and never
as sci-fi or generic fantasy. Each is drawn in the index tones of fxpix, so it takes an element's or a family's palette.

  brush_stroke   an ink-brush stroke: a pressed, fat head, a tapering body, dry-brush breaks in the tail
  palm_print     a qi palm print: the palm and five fingers, the mark a palm strike leaves in the air or on the ground
  talisman       a paper talisman slip with an ink glyph (thunder's and the seal's)
  sword_sliver   a small jian of sword-qi: blade, guard and grip (metal's, and a sword formation's)
  lotus          a lotus of petals opening (fire's)
  petal          a drifting petal or leaf with its curl of wind (wind's, wood's)
  ripple         rings spreading on water (water's)
  stone          a lit chip of stone (earth's)
  motif          the element's own emblem, one call per element: the Dao images the rule names

Everything is deterministic (px_hash gives the variety).
"""
from __future__ import annotations

import math

from fxpix import ACCENT, BASE, CORE, DEEP, GLINT, HAZE, INK, LIGHT, Canvas, px_hash

INK_BANDS = ((0.35, INK), (0.8, DEEP), (1.0, BASE))       # a stroke of ink: black heart, a wet grey edge


def brush_stroke(cv: Canvas, pts: list, w: float, seed: int, table=INK_BANDS, dry: float = 0.35, mode: str = "over") -> None:
    """An ink-brush stroke along `pts`: pressed at the head (w), tapering to the tail, the last `dry` of it broken
    into dry-brush strands."""
    if len(pts) < 2:
        return
    n = len(pts)
    cut = max(2, int(round(n * (1.0 - dry))))
    cv.stroke_poly(pts[:cut], w, w * 0.45, table, mode)
    # the dry tail: three strands side by side, broken where the hash says the brush ran dry
    for k in (-1, 0, 1):
        for i in range(cut - 1, n - 1):
            if px_hash(seed, i, k + 5) < 0.3 + 0.15 * abs(k):
                continue
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            dx, dy = x1 - x0, y1 - y0
            d = math.hypot(dx, dy) or 1.0
            ox, oy = -dy / d * k * w * 0.18, dx / d * k * w * 0.18
            cv.line1((x0 + ox, y0 + oy), (x1 + ox, y1 + oy), table[0][1] if k == 0 else table[-1][1])


def palm_print(cv: Canvas, x: float, y: float, s: float, ang: float, tone=LIGHT, rim=BASE) -> None:
    """A palm print `s` px tall centred at (x, y), fingers toward `ang` (canvas radians)."""
    ux, uy = math.cos(ang), math.sin(ang)
    px_, py_ = -uy, ux
    # the palm: a rounded square
    cv.paint(cv.mask_ellipse(x, y, s * 0.36, s * 0.36), rim)
    cv.paint(cv.mask_ellipse(x, y, s * 0.27, s * 0.27), tone)
    # five fingers fanned toward `ang`, the thumb out to the side
    for i, (off, L) in enumerate(((-0.28, 0.5), (-0.1, 0.58), (0.08, 0.56), (0.25, 0.46))):
        bx, by = x + ux * s * 0.3 + px_ * s * off, y + uy * s * 0.3 + py_ * s * off
        cv.stroke_seg((bx, by), (bx + ux * s * L * 0.6, by + uy * s * L * 0.6), max(1.5, s * 0.16), max(1.2, s * 0.13),
                      table=((0.6, tone), (1.0, rim)))
    tx, ty = x - px_ * s * 0.34, y - py_ * s * 0.34
    cv.stroke_seg((tx, ty), (tx - px_ * s * 0.22 + ux * s * 0.2, ty - py_ * s * 0.22 + uy * s * 0.2), max(1.5, s * 0.15), 1.2,
                  table=((0.6, tone), (1.0, rim)))


def talisman(cv: Canvas, x: float, y: float, h: float, tilt: float = 0.0, lit: bool = True) -> None:
    """A paper talisman slip `h` px tall, its top at (x, y), leaning by `tilt` (px across over its height), with an
    ink glyph down its middle."""
    w = max(3.0, h * 0.38)
    pts = [(x - w / 2, y), (x + w / 2, y), (x + w / 2 + tilt, y + h), (x - w / 2 + tilt, y + h)]
    cv.polygon(pts, GLINT if lit else LIGHT)
    cv.paint(cv.mask_polygon([(x - w / 2, y), (x + w / 2, y), (x + w / 2 + tilt * 0.15, y + 1.5), (x - w / 2 + tilt * 0.15, y + 1.5)]), BASE)
    # the glyph: a vertical stroke with two short bars across it
    cv.line1((x + tilt * 0.2, y + 2), (x + tilt * 0.85, y + h - 1.5), INK)
    for k in (0.35, 0.6):
        cx, cy = x + tilt * k, y + h * k
        cv.line1((cx - w * 0.3, cy), (cx + w * 0.3, cy - 1), INK)


def sword_sliver(cv: Canvas, x: float, y: float, ang: float, L: float, tone=LIGHT) -> None:
    """A small jian of sword-qi, point at (x, y), pointing along `ang`: blade, guard and grip."""
    ux, uy = math.cos(ang), math.sin(ang)
    px_, py_ = -uy, ux
    hx, hy = x - ux * L * 0.72, y - uy * L * 0.72
    cv.stroke_seg((hx, hy), (x, y), max(2.0, L * 0.16), 1.0, table=((0.45, CORE), (1.0, tone)))
    cv.line1((hx + px_ * L * 0.16, hy + py_ * L * 0.16), (hx - px_ * L * 0.16, hy - py_ * L * 0.16), BASE)
    cv.line1((hx, hy), (x - ux * L, y - uy * L), DEEP)


def lotus(cv: Canvas, x: float, y: float, r: float, openness: float, petals: int = 5, tilt: float = 0.55) -> None:
    """A lotus of flame or light at (x, y): `petals` teardrop petals round a bright heart, opening from a bud
    (openness 0) to a flower (1); the flower is seen from above and in front, so it is squashed by `tilt`."""
    if r < 1.0:
        return
    spread = 0.25 + 0.75 * openness
    for i in range(petals):
        a = -math.pi / 2 + (i - (petals - 1) / 2) * (2.2 / petals) * spread * 1.6
        tip = (x + math.cos(a) * r, y + math.sin(a) * r * tilt - r * 0.35 * (1 - openness))
        cv.stroke_seg((x, y), tip, max(2.0, r * 0.5), 1.0, table=((0.35, LIGHT), (0.75, BASE), (1.0, DEEP)))
    cv.dot(x, y - 1, CORE, 2 if r > 4 else 1)


def petal(cv: Canvas, x: float, y: float, ang: float, s: float, age: float) -> None:
    """A petal or leaf drifting along `ang`, curling, with the wind's curl behind it."""
    ux, uy = math.cos(ang), math.sin(ang)
    spin = math.sin(age * 6.0) * 0.6
    tx, ty = math.cos(ang + spin), math.sin(ang + spin)
    cv.stroke_seg((x - tx * s * 0.5, y - ty * s * 0.5), (x + tx * s * 0.5, y + ty * s * 0.5), max(2.0, s * 0.55), 1.0,
                  table=((0.5, LIGHT), (1.0, BASE)))
    for i in range(1, 4):
        cv.dot(x - ux * (s + i * 1.6) + math.sin(i + age * 4) * 0.8, y - uy * (s + i * 1.6), GLINT if i == 1 else HAZE)


def ripple(cv: Canvas, x: float, y: float, r: float, k: float, rings: int = 2) -> None:
    """Rings spreading on water from (x, y): `k` 0..1 over their life."""
    for j in range(rings):
        rr = r * (0.35 + 0.65 * ((k + j * 0.35) % 1.0))
        cv.ring(x, y, rr, 1.0, LIGHT if j == 0 else DEEP)


def stone(cv: Canvas, x: float, y: float, s: float, seed: int) -> None:
    """An angular chip of stone lit from the upper left."""
    pts = []
    for i in range(5):
        a = i * 2 * math.pi / 5 + px_hash(seed, i) * 0.8
        rr = s * (0.6 + 0.4 * px_hash(seed, i, 3))
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr * 0.8))
    cv.shaded_polygon(pts, table=((0.35, LIGHT), (0.75, BASE), (1.0, DEEP)))


def motif(cv: Canvas, el: str, x: float, y: float, s: float, age: float, seed: int, ang: float = -math.pi / 2) -> None:
    """The element's emblem at (x, y), `s` px across, `age` 0..1 over its life, pointing along `ang` where that
    matters: fire a lotus, water ripples, wood leaves, earth a stone, metal a sword of qi, wind a petal, thunder a
    talisman, soul a lantern wisp, formless an ink dab, space a star, time a tick ring."""
    if age < 0.0 or age > 1.0 or s < 1.0:
        return
    if el == "fire":
        lotus(cv, x, y, s * 0.55, min(1.0, age * 1.6))
    elif el == "water":
        ripple(cv, x, y, s * 0.6, age)
        cv.dot(x, y - s * 0.4 * (1 - age), GLINT)
    elif el == "wood":
        for k in (-1, 1):
            petal(cv, x + k * s * 0.2, y - age * s * 0.3, ang + k * 0.9, s * 0.4, age + k * 0.2)
    elif el == "earth":
        stone(cv, x, y - (1 - age) * s * 0.3, s * 0.35, seed)
        cv.dot(x - s * 0.3, y + s * 0.2, HAZE, 2)
    elif el == "metal":
        sword_sliver(cv, x + math.cos(ang) * s * 0.4, y + math.sin(ang) * s * 0.4, ang, s * 0.9)
    elif el == "wind":
        petal(cv, x, y, ang, s * 0.45, age)
    elif el == "thunder":
        talisman(cv, x - s * 0.1, y - s * 0.5, s * 0.8, tilt=(px_hash(seed, 1) - 0.5) * 2)
        if age < 0.6:
            cv.line1((x + s * 0.2, y + s * 0.3), (x + s * 0.45, y + s * 0.1), CORE)
            cv.line1((x + s * 0.45, y + s * 0.1), (x + s * 0.4, y + s * 0.45), GLINT)
    elif el == "soul":
        cv.ring(x, y, max(1.5, s * 0.3), 1.0, LIGHT)
        cv.dot(x, y - 1, GLINT, 2 if s > 5 else 1)
        cv.dot(x, y + s * 0.3 + 1, DEEP)
    elif el == "formless":
        brush_stroke(cv, [(x - s * 0.4, y + s * 0.1), (x - s * 0.1, y - s * 0.05), (x + s * 0.2, y), (x + s * 0.45, y + s * 0.12)],
                     max(2.0, s * 0.3), seed, table=((0.5, ACCENT), (1.0, DEEP)))
    elif el == "space":
        cv.plus(x, y, ACCENT if age < 0.5 else LIGHT, max(1, int(s * 0.25)))
        cv.dot(x, y, CORE)
    elif el == "time":
        for i in range(6):
            a = i * math.pi / 3 + age * 0.8
            cv.line1((x + math.cos(a) * s * 0.3, y + math.sin(a) * s * 0.3), (x + math.cos(a) * s * 0.45, y + math.sin(a) * s * 0.45),
                     CORE if i % 3 == 0 else LIGHT)
