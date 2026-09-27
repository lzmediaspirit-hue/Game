"""Fish (HD, Style A): every catch of the angling post at 64 art px, shown 1:1 in the 76 px slot, with a native @32
render for the HUD item ring and the small slots.

Each fish is a side view, nose to the right, drawn as the living species: the body profile, a forked tail and the
dorsal, pectoral, pelvic and anal fins with their rays, overlapping scales in rows down the flank, the gill cover, a
lateral line, the eye with its ring and catch-light, and the species' own markings (a perch's bars, a trout's spots,
a carp's gold-edged scales and barbels, a salmon's hooked jaw, the moon carp's crescent). One template (`fish_hd`)
takes the species as parameters; the eel has its own serpentine body. The grade is form and trim, never colour alone
(beast_parts.GRADE_HD): a plain fish lies as it came out of the water; from Common it hangs from a stringer loop at
the jaw, hemp at Common, the grade's silk with a metal bead from Earth; the aura from Mystic up. Every icon comes
from one table (FISH_HD).
"""
import math

import numpy as np

from pix import Ramp, WHITE, erode4
from palette import M, mat7
from registry import hd, register
import shapes as S
from families.beast_parts import GRADE_HD, XY, glow_hd, lmask, loop_hd, offset_pts, tangents

FAM, GROUP = 'items', 'fish'
ART = 64   # HD (tools/icons/README.md, "How to convert a family")


# ============================================================================= materials
# A fish's skin is wet: it takes the porcelain rim light; fins are matte membranes.
SILVER, PEARL, HOLLOW, STONE = M('silver', 'porcelain'), M('pearl', 'porcelain'), M('hollow'), M('stone')
JADE, GOLD, PAPER, MIST, NAVY, EMBER, STRAW, MOSS, BONE, FLESH, QI, INKM, LOTUS = (M('jade', 'porcelain'), M('gold'), M('paper', 'porcelain'), M('mist'),
                                                                                 M('navy'), M('ember'), M('straw'), M('moss'), M('bone', 'porcelain'),
                                                                                 M('flesh'), M('qi'), M('ink'), M('lotuspink'))
SALMON, EEL = M('salmon', 'porcelain'), M('eel', 'porcelain')
PERCH = mat7(Ramp(['#1E3418', '#35562A', '#5E8A3E', '#9EBE5E', '#DDEBA0'], '#0C1609'), 'porcelain')
TROUT = mat7(Ramp(['#2C4A58', '#4E7486', '#88AEBC', '#C6DEE2', '#F4FCFC'], '#101C22'), 'porcelain')
MOON = mat7(Ramp(['#4A5870', '#7A8AA6', '#BAC6DA', '#E6ECF6', '#FFFFFF'], '#161C26'), 'porcelain')
EYE_GOLD = M('gold', 'gem')


# ============================================================================= the body axis
class Axis:
    """A body axis in icon space: u runs along it toward the head (angle: 0 right, 90 up), v across it, upward
    (to the axis's left). Shared with the insects and critters."""

    def __init__(self, cx, cy, angle):
        a = math.radians(angle)
        self.cx, self.cy = cx, cy
        self.d = (math.cos(a), -math.sin(a))
        self.n = (-math.sin(a), -math.cos(a))

    def p(self, u, v):
        return (self.cx + u * self.d[0] + v * self.n[0], self.cy + u * self.d[1] + v * self.n[1])

    def uv(self, p):
        X, Y = XY(p)
        dx, dy = X - self.cx, Y - self.cy
        return dx * self.d[0] + dy * self.d[1], dx * self.n[0] + dy * self.n[1]

    def ell(self, p, u0, v0, a, b, rot=0.0):
        """An ellipse in axis coordinates; rot turns its long axis from u toward v (degrees)."""
        U, V = self.uv(p)
        du, dv = U - u0, V - v0
        r = math.radians(rot)
        s = du * math.cos(r) + dv * math.sin(r)
        t = -du * math.sin(r) + dv * math.cos(r)
        return (s / a) ** 2 + (t / b) ** 2 <= 1.0


# ============================================================================= the template
def fin_rays(p, fin, base, tips, mat, lv=-1):
    """Fin rays: dark lines fanning from `base` to each of `tips`, inside the fin."""
    inner = erode4(fin)
    for t in tips:
        p.decal(lmask(p, [base, t]) & inner, mat, lv)


def scales_hd(p, A, body, mat, u0, u1, v0, v1, pitch=(4.0, 3.0), lv=-1, edge=None):
    """Overlapping scales: rows of crescents down the flank between u0..u1 and v0..v1 (axis coordinates), each
    crescent the free (tail-side) edge of a scale, staggered row by row; `edge` paints a lit pixel on the head side
    of each crescent in another material (a carp's gold-edged scales)."""
    U, V = A.uv(p)
    inner = erode4(body)
    pu, pv = pitch
    dark, lit = p.c.empty(), p.c.empty()
    row = 0
    v = v0
    while v <= v1:
        u = u0 + (row % 2) * pu * 0.5
        while u <= u1:
            du, dv = U - u, V - v
            d = np.sqrt(du * du + dv * dv)
            dark |= (d >= pu * 0.42) & (d < pu * 0.42 + 1.0) & (du < -pu * 0.05)
            lit |= (d >= pu * 0.42) & (d < pu * 0.42 + 1.0) & (du > pu * 0.28)
            u += pu
        v += pv
        row += 1
    p.decal(dark & inner, mat, lv)
    if edge is not None:
        p.decal(lit & inner & ~dark, edge, 1)


def fish_hd(p, g, L=42, H=19, angle=12, cx=None, cy=None, body=None, belly=None, fin=None, tail=11, dorsal=(0.02, 0.32, 0.58),
            spiny=0, pattern=None, pat=None, barbels=False, hook=False, eye=None, scales=True, scale_edge=None, lateral=True,
            sparks=(), loop=True):
    """A fish in side view on the axis through (cx, cy) at `angle`, nose to the right: body length L, height H,
    the tail fin `tail` long. dorsal: (start, length, height) as fractions of L, L and H; spiny: the front dorsal is
    that many spines. pattern: 'bars', 'spots', 'stripe', 'band' in `pat`. Trim: the grade's stringer loop at the
    jaw (loop_hd), nothing on a plain fish."""
    c = p.c
    body = body or SILVER
    belly = belly or PEARL
    fin = fin or body
    eye = eye or EYE_GOLD
    if cx is None:
        cx = 32.0 + tail * 0.5 * math.cos(math.radians(angle))
    if cy is None:
        cy = 32.0 - tail * 0.5 * math.sin(math.radians(angle))
    A = Axis(cx, cy, angle)
    hl = L / 2.0
    top, bot = [], []
    k = 32
    for i in range(k + 1):
        t = i / float(k)
        u = -hl + t * L
        f = 0.2 + 0.8 * math.sin(math.pi * min(1.0, t ** 0.85)) ** 0.55
        if t > 0.86:
            f *= math.sqrt(max(0.0, (1.0 - t) / 0.14)) * 0.85 + 0.15
        top.append(A.p(u, H / 2.0 * f))
        bot.append(A.p(u, -H / 2.0 * f * (0.8 if hook else 0.86)))
    bodym = c.poly(top + bot[::-1])
    # --- the fins behind the body: the tail, the dorsal, the pelvic and anal fins
    tailm = c.poly([A.p(-hl + 2.5, H * 0.14), A.p(-hl - tail * 0.35, H * 0.4), A.p(-hl - tail, H * 0.66), A.p(-hl - tail * 0.5, H * 0.04),
                    A.p(-hl - tail * 0.5, -H * 0.04), A.p(-hl - tail, -H * 0.66), A.p(-hl - tail * 0.35, -H * 0.4), A.p(-hl + 2.5, -H * 0.14)])
    p.part(tailm, fin, 'ray', base=0, sep=False, rim=False)
    fin_rays(p, tailm, A.p(-hl + 1.0, 0), [A.p(-hl - tail * 0.95, H * s * 0.6) for s in (1, 0.62, 0.3, -0.3, -0.62, -1)], fin)
    d0, dl, dh = dorsal
    u0, u1 = -hl * 0.05 + d0 * L, -hl * 0.05 + (d0 + dl) * L
    if spiny:
        dors = c.empty()
        n = spiny
        for i in range(n):
            uu = u0 + (u1 - u0) * i / float(n - 1)
            hh = H * (0.5 + dh * (1.0 - 0.45 * i / float(n - 1)))
            dors |= c.poly([A.p(uu - 1.6, H * 0.4), A.p(uu + 0.6, hh), A.p(uu + 1.9, H * 0.4)])
        dors |= c.poly([A.p(u0 - 1, H * 0.46), A.p(u1 + 2, H * 0.46), A.p(u1 + 2, H * 0.36), A.p(u0 - 1, H * 0.36)])
        p.part(dors, fin, 'ray', base=0, sep=False, rim=False)
        p.decal(dors & ~erode4(dors) & A.ell(p, (u0 + u1) / 2, H * 0.6, (u1 - u0) * 0.7, H * 0.4), fin, -2)
    else:
        dors = c.poly([A.p(u0, H * 0.4), A.p(u0 + (u1 - u0) * 0.18, H * (0.5 + dh)), A.p(u0 + (u1 - u0) * 0.5, H * (0.5 + dh * 0.72)),
                       A.p(u1, H * (0.5 + dh * 0.28)), A.p(u1 + 1.5, H * 0.4)])
        p.part(dors, fin, 'ray', base=0, sep=False, rim=False)
        fin_rays(p, dors, A.p(u0 + (u1 - u0) * 0.2, H * 0.36), [A.p(u0 + (u1 - u0) * f, H * (0.5 + dh * (0.95 - 0.7 * f))) for f in (0.3, 0.55, 0.8, 1.0)], fin)
    anal = c.poly([A.p(-hl * 0.5, -H * 0.36), A.p(-hl * 0.38, -H * 0.7), A.p(-hl * 0.12, -H * 0.62), A.p(-hl * 0.05, -H * 0.38)])
    pelv = c.poly([A.p(hl * 0.1, -H * 0.4), A.p(hl * 0.14, -H * 0.76), A.p(hl * 0.36, -H * 0.66), A.p(hl * 0.4, -H * 0.42)])
    for m in (anal, pelv):
        p.part(m, fin, 'ray', base=-1, sep=False, rim=False)
    fin_rays(p, anal, A.p(-hl * 0.3, -H * 0.36), [A.p(-hl * 0.4, -H * 0.68), A.p(-hl * 0.2, -H * 0.66)], fin)
    fin_rays(p, pelv, A.p(hl * 0.22, -H * 0.4), [A.p(hl * 0.15, -H * 0.72), A.p(hl * 0.32, -H * 0.66)], fin)
    # --- the body, its belly and lateral line, the scales
    p.part(bodym, body, 'ray', base=0, sep=True)
    U, V = A.uv(p)
    inner = erode4(bodym)
    bel = bodym & (V < -H * 0.1) & (U < hl * 0.62)
    p.part(bel, belly, 'ray_soft', base=0, sep=False, rim=False)
    p.decal(bel & (V < -H * 0.1 - 1.0) & (V > -H * 0.1 - 2.0) & (U < hl * 0.45) & (U > -hl * 0.7), belly, 2)
    if lateral:
        p.decal(lmask(p, [A.p(hl * 0.42, H * 0.06), A.p(0, H * 0.02), A.p(-hl * 0.55, -H * 0.02), A.p(-hl * 0.92, 0)]) & inner, body, -2)
    if scales:
        scales_hd(p, A, bodym & (V >= -H * 0.1) & (U < hl * 0.45) & (U > -hl * 0.86), body, -hl * 0.85, hl * 0.42, -H * 0.05, H * 0.45,
                  edge=scale_edge)
    # --- the species' markings
    if pattern == 'bars':
        bars = inner & (V > -H * 0.24) & (np.floor((U + hl) / 5.0) % 2 == 1) & (U < hl * 0.4) & (U > -hl * 0.78)
        p.decal(bars, pat or body, -2)
        p.decal(bars & (V > H * 0.3), pat or body, -3)
    elif pattern == 'spots':
        for (su, sv, r) in ((-12, 3, 1.5), (-5, 5, 1.3), (3, 4, 1.6), (-8, 0.5, 1.2), (0, 1, 1.4), (7, 5, 1.2), (-16, 2, 1.1), (10, 2.5, 1.3), (-3, 7, 1.0), (-14, 6, 1.0)):
            x, y = A.p(su, sv)
            p.decal(c.circle(x, y, r) & inner, pat or body, -1)
            p.decal(c.circle(x - 0.5, y - 0.5, r * 0.4) & inner, pat or body, 1)
    elif pattern == 'stripe':
        st = inner & (np.abs(V - H * 0.02) < 1.3) & (U < hl * 0.6) & (U > -hl * 0.9)
        p.decal(st, pat or body, -1)
        p.decal(st & (np.abs(V - H * 0.02) < 0.5), pat or body, -3)
    elif pattern == 'band':
        st = inner & (np.abs(V + H * 0.04) < 2.2) & (U < hl * 0.55) & (U > -hl * 0.85)
        p.decal(st, pat, 0)
        p.decal(st & (V + H * 0.04 > 0.6), pat, 2)
    # --- the head: gill cover, eye, mouth, barbels
    gx, gy = A.p(hl * 0.36, H * 0.02)
    gill = c.arc(gx, gy, H * 0.44, 1.2, angle - 70, angle + 70) & inner
    p.decal(gill, body, -2)
    p.decal(c.arc(gx, gy, H * 0.44 + 1.2, 1.0, angle - 60, angle + 60) & inner, body, 1)
    p.decal(c.arc(gx + A.d[0] * 4, gy + A.d[1] * 4, H * 0.3, 1.0, angle - 50, angle + 50) & inner, body, -1)
    ex, ey = A.p(hl * 0.7, H * 0.12)
    p.decal(c.circle(ex, ey, 3.0) & bodym, INKM, 0)
    p.decal(c.circle(ex, ey, 2.1) & bodym, eye, 1)
    p.decal(c.circle(ex + 0.3, ey + 0.2, 1.15) & bodym, INKM, -2)
    p.decal(c.box(ex - 1.6, ey - 1.6, ex - 0.6, ey - 0.6) & bodym, WHITE, 0)
    mx, my = A.p(hl, -H * 0.1)
    if hook:
        jaw = c.taper((mx - A.d[0] * 5, my - A.d[1] * 5), (mx + 1.5, my + 2.5), (mx + 2.5, my - 2.0), 5.0, 2.0)
        p.part(jaw, body, 'ray_soft', base=0, sep=False)
        p.decal(lmask(p, [(mx - 5, my + 1.5), (mx + 1, my + 2.8)]) & (bodym | jaw), body, -3)
    else:
        p.decal(lmask(p, [(mx - 5.5, my - 0.5), (mx - 0.5, my + 0.8)]) & bodym, body, -3)
        p.decal(lmask(p, [(mx - 5.0, my - 1.6), (mx - 1.5, my - 0.6)]) & bodym, body, 2)
    if barbels:
        bx, by = A.p(hl - 1.5, -H * 0.22)
        for (dx, dy) in ((0.8, 3.5), (-1.5, 3.2)):
            p.part(c.taper((bx, by), (bx + dx, by + dy), (bx + dx - 2.5, by + dy + 3.5), 1.6, 1.0) & ~bodym, GOLD, 'flat', base=0, sep=True, rim=False)
    # --- the pectoral fin in front, over the flank
    px, py = A.p(hl * 0.36, -H * 0.12)
    pec = c.leaf(px, py, angle - 150, H * 0.62, H * 0.32, bend=0.12)
    p.part(pec, fin, 'ray_soft', base=1, sep=True, rim=False)
    fin_rays(p, pec, (px, py), [A.p(hl * 0.36 - H * 0.5, -H * 0.12 - H * 0.36 * s) for s in (0.4, 0.8, 1.2)], fin)
    p.decal(bodym & ~erode4(bodym) & (V > 0) & (U < hl * 0.3) & (U > -hl * 0.8), body, 2)
    # --- the grade's stringer loop at the jaw
    if loop and g['cord'] is not None:
        jx, jy = A.p(hl - 3.5, -H * 0.36)
        loop_hd(p, g, jx - 1.0, jy + 3.0, r=3.4, w=1.8, under=bodym)
    for (x, y) in sparks:
        p.sparkle(x, y, 1)
    return bodym, A


# ============================================================================= the species
def minnow_hd(p, g):
    """River minnows, a small shoal: one grown minnow with a dark stripe down its side, two little ones above."""
    fish_hd(p, g, L=22, H=7.5, angle=16, cx=27, cy=15, body=SILVER, belly=PEARL, fin=HOLLOW, tail=6, dorsal=(0.08, 0.28, 0.5),
            pattern='stripe', pat=STONE, scales=False, loop=False)
    fish_hd(p, g, L=16, H=5.5, angle=8, cx=47, cy=24, body=SILVER, belly=PEARL, fin=HOLLOW, tail=4.5, dorsal=(0.08, 0.28, 0.5),
            pattern='stripe', pat=STONE, scales=False, loop=False)
    fish_hd(p, g, L=36, H=12, angle=14, cx=30, cy=43, body=SILVER, belly=PEARL, fin=HOLLOW, tail=9, dorsal=(0.06, 0.3, 0.5),
            pattern='stripe', pat=STONE, scale_edge=None)


def perch_hd(p, g):
    """A reed perch: deep green body barred dark, a spiny front dorsal and orange fins."""
    fish_hd(p, g, L=40, H=24, angle=12, body=PERCH, belly=STRAW, fin=EMBER, tail=10, dorsal=(-0.02, 0.38, 0.5), spiny=6, pattern='bars')


def jade_carp_hd(p, g):
    """A jade carp: green-jade flank with gold-edged scales, gold fins and barbels, a high dorsal."""
    fish_hd(p, g, L=42, H=22, angle=13, body=JADE, belly=PAPER, fin=GOLD, tail=11, dorsal=(-0.02, 0.44, 0.42), scale_edge=GOLD, barbels=True)


def trout_hd(p, g):
    """A mist trout: slender, pale blue-grey with navy spots and a lotus-pink band along the side."""
    fish_hd(p, g, L=44, H=17, angle=10, body=TROUT, belly=PEARL, fin=MIST, tail=10, dorsal=(0.06, 0.3, 0.5), pattern='spots', pat=NAVY)
    # the pink band, over the spots
    A = Axis(32.0 + 5 * math.cos(math.radians(10)), 32.0 - 5 * math.sin(math.radians(10)), 10)
    U, V = A.uv(p)
    band = erode4(p.c.a) & (np.abs(V + 1.0) < 1.6) & (U < 12) & (U > -19)
    p.decal(band, LOTUS, 0)
    p.decal(band & (V + 1.0 > 0.4), LOTUS, 2)


def salmon_hd(p, g):
    """A rapids salmon leaping: red flank with pale spots, a hooked jaw, spray flung off the tail."""
    fish_hd(p, g, L=42, H=20, angle=28, cx=35, cy=31, body=SALMON, belly=BONE, fin=FLESH, tail=10, dorsal=(0.02, 0.32, 0.5), pattern='spots',
            pat=FLESH, hook=True)
    c = p.c
    for (x, y, r) in ((10, 50, 2.8), (17, 56, 2.0), (8, 42, 1.8), (22, 52, 1.5)):
        p.part(c.circle(x, y, r), QI, 'sphere', base=0, sep=True, rim=False)
        p.decal(c.circle(x - r * 0.35, y - r * 0.35, r * 0.4), QI, 3)


def moon_carp_hd(p, g):
    """A moon carp: pearl-white, mist fins and barbels, a gold crescent on its flank, a glint or two in the dark."""
    bodym, A = fish_hd(p, g, L=42, H=22, angle=13, body=MOON, belly=PEARL, fin=MIST, tail=11, dorsal=(-0.02, 0.44, 0.42), barbels=True,
                       sparks=((9, 12), (55, 50)))
    c = p.c
    mx, my = A.p(-4, 1.5)
    moon = c.circle(mx, my, 6.2) & ~c.circle(mx + 2.8, my - 2.0, 5.2) & erode4(bodym)
    p.decal(moon, GOLD, 0)
    p.decal(moon & c.circle(mx - 2, my + 2, 5.0), GOLD, 2)


def eel_hd(p, g):
    """A river eel: the long olive body in an S, a fin ribbon down its back, the pale belly, the small head."""
    c = p.c
    pts = S.curve_pts((9, 53), (17, 22), (31, 33), 18) + S.curve_pts((31, 33), (46, 44), (51, 15), 18)[1:]
    n = len(pts)
    body = c.empty()
    widths = []
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        t = i / float(n - 1)
        w = 3.2 + 6.4 * min(1.0, t * 1.5) if t < 0.94 else 9.6
        widths.append(w)
        body |= c.seg(a[0], a[1], b[0], b[1], w)
    head = c.ellipse(51.5, 13.0, 5.6, 6.4)
    body |= head
    tg = tangents(pts)
    # the fin ribbon along the back (the side away from the belly), behind the body
    back = offset_pts(pts, -1.0)
    ribbon = c.empty()
    for i in range(3, n - 4):
        (x, y), (ux, uy, nx, ny) = back[i], tg[i]
        wv = widths[min(i, len(widths) - 1)]
        ribbon |= c.seg(x - nx * (wv * 0.5), y - ny * (wv * 0.5), x - nx * (wv * 0.5 + 3.6), y - ny * (wv * 0.5 + 3.6), 2.2)
    p.part(ribbon & ~body, MOSS, 'flat', base=0, sep=False, rim=False)
    p.decal(ribbon & ~body & ~erode4(ribbon), MOSS, -1)
    p.part(body, EEL, 'ray', base=0, sep=True)
    inner = erode4(body)
    # the pale belly along the inside of the curve and the rings down the body
    belly = c.empty()
    for i in range(2, n - 3):
        (x, y), (ux, uy, nx, ny) = pts[i], tg[i]
        wv = widths[min(i, len(widths) - 1)]
        belly |= c.seg(x + nx * wv * 0.28, y + ny * wv * 0.28, x + nx * wv * 0.5, y + ny * wv * 0.5, 1.6)
    p.decal(belly & inner, STRAW, 0)
    for i in range(6, n - 5, 4):
        (x, y), (ux, uy, nx, ny) = pts[i], tg[i]
        wv = widths[min(i, len(widths) - 1)] * 0.5
        p.decal(lmask(p, [(x + nx * wv * 0.85, y + ny * wv * 0.85), (x - nx * wv * 0.85, y - ny * wv * 0.85)]) & inner, EEL, -2)
    p.decal(lmask(p, offset_pts(pts[4:-4], -1.4)) & inner, EEL, 2)
    # the head: gill line, gold eye, the mouth
    p.decal(c.arc(50.5, 14, 5.2, 1.2, 200, 330) & erode4(head), EEL, -2)
    p.decal(c.circle(53.0, 11.2, 2.4), INKM, 0)
    p.decal(c.circle(53.0, 11.2, 1.6), EYE_GOLD, 1)
    p.decal(c.circle(53.3, 11.5, 0.8), INKM, -2)
    p.decal(c.box(52.0, 10.0, 53.0, 11.0), WHITE, 0)
    p.decal(lmask(p, [(52, 17.5), (56.5, 15.5)]) & head, EEL, -3)
    loop_hd(p, g, 54.5, 21.5, r=3.2, w=1.8, under=body)


# ============================================================================= the table
FISH_HD = [
    # id, grade (items.py), the aura's colour from Mystic up (None: the grade's), the drawing
    ('river_minnow', 'plain', None, minnow_hd),
    ('reed_perch', 'plain', None, perch_hd),
    ('jade_carp_fish', 'earth', None, jade_carp_hd),
    ('river_eel', 'common', None, eel_hd),
    ('mist_trout', 'earth', None, trout_hd),
    ('rapids_salmon', 'earth', None, salmon_hd),
    ('moon_carp', 'heaven', None, moon_carp_hd),
]

def make_catch_hd(grade, aura, draw):
    """A catch's drawing `draw(p, g)` with its grade's trim and, from Mystic, its aura (the module's own wrapper, so
    the icon belongs to this family module)."""
    g = GRADE_HD[grade]

    def hd_draw(p):
        draw(p, g)
        glow_hd(p, g, aura)
    return hd_draw


for _id, _grade, _aura, _draw in FISH_HD:
    _fn = make_catch_hd(_grade, _aura, _draw)
    register(FAM, _id, _fn, GROUP)
    hd(_id, _fn)
