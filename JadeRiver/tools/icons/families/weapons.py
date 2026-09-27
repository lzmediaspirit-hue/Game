"""Weapons (HD, Style A): eleven families at nine grades on one diagonal frame, and the Star Wardens' four pieces.

Every weapon lies on WFRAME, the diagonal from the lower left to the upper right the study's jian set (the hand-bell
hangs mouth down-right on BFRAME; the gauntlets stand upright, a fist over its cuff). A family is one builder that
takes a grade and paints with the grade's kit (`palette.kit`: blade, guard, grip, wrap, gem, tassel, cloth, metal2,
glow), so the family is the silhouette and the grade the material, its fittings and its work, never a colour alone:

  Plain     - a wooden blade with its grain, darkwood fittings, a hemp lattice wrap, a red cord
  Common    - iron with a plain fuller, bronze fittings, a leather grip in a darkwood wrap
  Earth     - jadeiron with a jade inlay down the fuller, a jade gem in the guard
  Heaven    - cloudsteel engraved with silver cloud curls, silver fittings, a qi gem, a sky tassel
  Mystic    - mistjade with gold runes down a dark fuller, gold fittings, a violet gem, a metal bead on the tassel, a glow
  Spirit    - stormsteel with a lightning zigzag, silver fittings, a cyan spark, the glow
  Sage      - sunsteel with desert-glass beads on an ember line, jade fittings, the sun glow
  Sovereign - driftsteel (comet iron) set with driftglass diamonds on a driftteal line, driftteal fittings
  Will      - lanternsteel (night steel) with star dots down the fuller and a starlight edge, gold fittings
  Sphere    - orchardsteel with pearls on a rose-gold line, rose-gold fittings (the kit is here; no weapon yet)

The silhouettes follow the held sprites (data/parts.json `weapon`): the jian's straight blade under a winged guard,
the sabre's broad single edge under a disc, the spear's leaf head and tassel on a long shaft, the short blade's leaf,
the staff's crook, the bow's recurve on its string, the fan open on its sticks, the flute with its holes and cord,
the brush with its tuft dipped in ink, the bell with its cord and clapper, the fist in its cuff. The grade's work runs
along the fuller (`work_hd`), or the limb, the leaf's arc, the cuff or the bell's waist where a weapon has no blade.
"""
import math

import numpy as np

from pix import Frame, erode4
from palette import GRADE_ORDER, M, TEX, kit
from registry import hd, register
import shapes as S

FAM, GROUP = 'equipment', 'weapons'
ART = 64   # HD (tools/icons/README.md, "How to convert a family")

GRADE_WORDS = [('training', 'plain'), ('iron', 'common'), ('jadeiron', 'earth'), ('cloudsteel', 'heaven'), ('mistjade', 'mystic'),
               ('stormsteel', 'spirit'), ('sunsteel', 'sage'), ('driftsteel', 'sovereign'), ('lanternsteel', 'will')]
WFRAME = Frame((6.5, 57.5), 45.0)      # the weapons' diagonal, lower left to upper right (the study's jian)
BFRAME = Frame((30.0, 30.0), -45.0)    # the bell's, its mouth down-right


def level(grade):
    return GRADE_ORDER.index(grade)


def K(grade):
    """The grade's kit with its level and the materials the weapons derive from it: the shaft (wood, then darkwood,
    then lacquered in the grade's silk), the bamboo of the plain flute and brush, the hair of a brush."""
    k = kit(grade)
    k['grade'], k['lv'] = grade, level(grade)
    k['shaft'] = M('wood') if k['lv'] <= 1 else (M('darkwood') if k['lv'] == 2 else k['grip'])
    k['body'] = M('bamboo') if k['lv'] == 0 else k['blade']
    k['bead'] = k['guard'] if k['lv'] >= 4 else k['tassel']
    return k


def ttex(mat):
    """The pixel texture a part of this material takes (none for a matte or silk part)."""
    return TEX.get(mat.kind) if mat.kind not in ('silk', 'cloth', 'leather') else None


# --------------------------------------------------------------------------- the shared builders
def tassel_hd(p, k, x, y, sc=1.0, knot=True):
    """A tassel from (x, y): two strands hanging down and to the left, under a knot (a metal bead from Mystic)."""
    c = p.c
    m = c.taper((x, y), (x - 5.5 * sc, y + 1.6 * sc), (x - 4.4 * sc, y + 4.8 * sc), 3.0 * sc, 1.6 * sc) | \
        c.taper((x, y), (x - 3.4 * sc, y + 3.4 * sc), (x + 0.4 * sc, y + 5.3 * sc), 2.4 * sc, 1.2 * sc)
    p.part(m, k['tassel'], 'ray_soft', base=0, sep=False, rim=False)
    if knot:
        p.part(c.circle(x, y, 2.2 * sc), k['bead'], 'sphere', base=1, sep=True, rim=k['lv'] >= 4)
    return m


def wrap_hd(p, fr, k, mask, hw, t0=None):
    """The wrap on a grip already painted: bands of the kit's wrap every 3.4 px along the frame (a hemp lattice at
    Plain), a thread of the guard metal between the turns from Mystic."""
    c = p.c
    t, w = fr.along(c)
    core = mask & erode4(mask)
    if k['lv'] == 0:
        a = np.floor((t + 0.7 * w) / 3.2).astype(int) % 2 == 0
        b = np.floor((t - 0.7 * w) / 3.2).astype(int) % 2 == 0
        p.decal(core & (a ^ b), k['wrap'], -1)
        return
    turn = np.floor((t + 0.35 * w) / 3.4).astype(int) % 2 == 0
    p.decal(core & turn, k['wrap'], -1)
    p.decal(core & turn & (w < -hw * 0.5), k['wrap'], 1)
    if k['lv'] >= 4:
        p.decal(core & ~turn & (np.abs(w) < 0.6), k['guard'], 1)


def grip_hd(p, fr, k, t0, t1, hw):
    """A wrapped grip along the frame from t0 to t1."""
    grip = fr.prof(p.c, [(t0, hw), (t1, hw)])
    p.cylinder(fr, grip, hw, k['grip'], sep=True)
    wrap_hd(p, fr, k, grip, hw)
    return grip


def fitting_hd(p, fr, k, t0, t1, hw, flare=0.8, line=None):
    """A round fitting across the frame (a pommel, a ferrule, a collar, a band): the guard metal, flared at both
    ends by `flare`; `line` puts a bright ring at that t."""
    m = fr.prof(p.c, [(t0, hw - flare), (t0 + flare, hw), (t1 - flare, hw), (t1, hw - flare)])
    p.cylinder(fr, m, hw, k['guard'], sep=True, tex=ttex(k['guard']))
    if line is not None:
        p.line([fr.P(line, -hw + 0.6), fr.P(line, hw - 0.6)], k['guard'], 2, 1.0)
    return m


def gem_hd(p, k, x, y, r, fallback=True):
    """The kit's gem set at (x, y), or a stud of the guard metal below Earth."""
    c = p.c
    if k['gem'] is not None:
        return p.part(c.circle(x, y, r), k['gem'], 'sphere', base=1, sep=True, spec=(x - r * 0.35, y - r * 0.35))
    if fallback:
        return p.part(c.circle(x, y, r * 0.8), k['guard'], 'sphere', base=0, sep=True)
    return c.empty()


def blade_hd(p, fr, k, t0, t1, tip, hw):
    """A straight double-edged blade with its ridge: parallel edges from t0 to t1, the point at `tip`."""
    m = fr.prof(p.c, [(t0, hw), (t1, hw), (tip, 0.0)])
    p.cylinder(fr, m, lambda t: np.where(t > t1, np.clip(hw * (tip - t) / (tip - t1), 0.0, hw), hw), k['blade'], ridge=True,
               sep=True, tex=ttex(k['blade']), axis=45.0)
    return m


def leaf_blade_hd(p, fr, k, t0, t1, hw, power=0.5, n=26):
    """A leaf-shaped blade (a spear head, a short blade) from its root at t0 to the point at t1, its widest early."""
    def half(t):
        u = np.clip((t - t0) / float(t1 - t0), 0.0, 1.0)
        return hw * np.sin(np.pi * np.minimum(1.0, u ** power))
    ts = np.linspace(t0, t1, n)
    m = fr.prof(p.c, [(float(t), float(max(0.0, half(np.array(t))))) for t in ts])
    p.cylinder(fr, m, half, k['blade'], ridge=True, sep=True, tex=ttex(k['blade']), axis=45.0)
    return m


def edge_hd(p, fr, k, blade, tip_t):
    """The blade's lit edge in the grade's own light (a starlight edge on lanternsteel), short of the point."""
    if k['grade'] == 'will':
        t, w = fr.along(p.c)
        p.decal(blade & ~erode4(blade) & (w < 0) & (t < tip_t - 4.0), k['gem'], 1)


def work_hd(p, k, pts, mask, dark=None):
    """The grade's work along a line of points (the fuller of a blade, a bow limb, a fan leaf's arc, a cuff, a
    bell's waist), clipped to `mask`: a fuller below Earth, then the grade's inlay, engraving or setting."""
    c, g = p.c, k['grade']
    dark = dark or k['blade']
    line = c.polyline(pts, 1.0) & mask
    gem = k['gem']
    if gem is None:
        if k['lv'] == 1:
            p.decal(line, dark, -1)
        return
    # the tangent and the normal at each point, for the work that steps across the line
    def normal(i):
        (x0, y0), (x1, y1) = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
        L = math.hypot(x1 - x0, y1 - y0) or 1.0
        return (-(y1 - y0) / L, (x1 - x0) / L)
    if g == 'earth':                      # a jade inlay
        p.decal(line, gem, 0)
    elif g == 'heaven':                   # cloud curls in silver
        for i in range(3, len(pts), 8):
            x, y = pts[i]
            p.decal(c.arc(x, y, 1.9, 1.0, 200, 120) & mask, k['metal2'], 2)
    elif g == 'mystic':                   # gold runes down a dark fuller
        p.decal(line, dark, -2)
        for i in range(1, len(pts), 5):
            (x, y), (nx, ny) = pts[i], normal(i)
            p.decal((c.seg(x - nx * 0.8, y - ny * 0.8, x + nx * 0.8, y + ny * 0.8, 1.0) | c.circle(*pts[min(len(pts) - 1, i + 2)], 0.6)) & mask, k['guard'], 1)
    elif g == 'spirit':                   # a lightning zigzag
        zig = [(x + nx * (1.2 if (i // 2) % 2 else -1.2), y + ny * (1.2 if (i // 2) % 2 else -1.2)) for i, ((x, y), (nx, ny)) in
               enumerate((pts[i], normal(i)) for i in range(0, len(pts), 2))]
        p.decal(c.polyline(zig, 1.0) & mask, gem, 2)
    elif g == 'sage':                     # desert-glass beads on an ember line
        p.decal(line, gem, 0)
        for i in range(2, len(pts), 5):
            p.decal(c.circle(*pts[i], 1.1) & mask, gem, 2)
    elif g == 'sovereign':                # driftglass diamonds set in a driftteal line
        p.decal(line, k['guard'], 1)
        for i in range(3, len(pts), 7):
            x, y = pts[i]
            p.decal(c.diamond(x, y, 1.7, 1.7) & mask, gem, 1)
            p.decal(c.circle(x - 0.5, y - 0.5, 0.55) & mask, gem, 3)
    elif g == 'will':                     # star dots down a night fuller
        p.decal(line, dark, -2)
        for i in range(1, len(pts), 4):
            p.decal(c.circle(*pts[i], 0.9) & mask, gem, 2)
    else:                                 # sphere: pearls on a rose-gold line
        p.decal(line, k['guard'], 1)
        for i in range(2, len(pts), 5):
            p.decal(c.circle(*pts[i], 1.0) & mask, gem, 2)


def along(fr, t0, t1, w=0.0, step=1.0):
    """Points along the frame from t0 to t1 at offset w, `step` apart."""
    n = max(2, int(round((t1 - t0) / step)) + 1)
    return [fr.P(t, w) for t in np.linspace(t0, t1, n)]


def finish_hd(p, k):
    if k['glow']:
        p.glow(*k['glow'])


# --------------------------------------------------------------------------- the families
def jian_hd(p, grade='common'):
    """A straight double-edged jian: the tassel and pommel, the wrapped grip, the winged guard set with the gem over
    the root of the blade, the fuller with the grade's work."""
    k, c, fr = K(grade), p.c, WFRAME
    tassel_hd(p, k, 9.0, 55.2)
    fitting_hd(p, fr, k, 1.5, 7.2, 4.2, 1.2)
    grip_hd(p, fr, k, 6.8, 22.0, 3.3)
    blade = blade_hd(p, fr, k, 25.0, 58.0, 71.0, 4.4)
    work_hd(p, k, along(fr, 31.0, 56.0), blade)
    edge_hd(p, fr, k, blade, 71.0)
    p.part(fr.prof(c, [(21.0, 3.8), (22.5, 8.4), (24.2, 10.2), (26.0, 9.2), (28.0, 5.6), (29.0, 3.9)]), k['guard'], 'ray', base=0, sep=True, tex=ttex(k['guard']))
    p.line([fr.P(23.2, -7.0), fr.P(23.2, 7.0)], k['guard'], 2, 1.0)
    gem_hd(p, k, *fr.P(24.6, 0.0), 2.5)
    p.sparkle(*fr.P(64.0, -0.6), 1)
    finish_hd(p, k)


def heavy_sabre_hd(p, grade='common'):
    """A broad single-edged sabre: a ring pommel with its strands, the grip, a disc guard, the blade widening to a
    clipped point with its ridge, the fuller along the spine."""
    k, c, fr = K(grade), p.c, WFRAME
    rx, ry = fr.P(2.4, 0.0)
    p.part(c.taper((6.4, 58.0), (4.9, 59.2), (5.6, 60.4), 2.4, 1.3) | c.taper((7.6, 58.6), (8.2, 59.8), (10.2, 60.4), 2.0, 1.1), k['tassel'], 'ray_soft', base=0, sep=False, rim=False)
    p.part(c.ring(rx, ry, 3.3, 1.8), k['guard'], 'ray', base=0, sep=True, tex=ttex(k['guard']))
    grip_hd(p, fr, k, 5.4, 20.5, 3.2)
    # the blade curves back toward its spine as it broadens, and the edge sweeps up to a clipped point
    ts, spine, edge = [23.0, 38.0, 52.0, 62.0, 69.0], [-2.8, -3.4, -4.4, -5.2, -4.4], [3.0, 3.6, 3.8, 2.4, -4.4]
    blade = c.poly([fr.P(t, w) for t, w in zip(ts, spine)] + [fr.P(t, w) for t, w in zip(ts[::-1], edge[::-1])])
    t, w = fr.along(c)
    ws, we = np.interp(t, ts, spine), np.interp(t, ts, edge)
    f = (w - ws) / np.maximum(we - ws, 0.2)
    p.part(blade, k['blade'], 'field', base=0, field=f, bands=((0.08, 2), (0.46, 1), (0.58, 2), (0.84, 0), (9, -1)), sep=True, tex=ttex(k['blade']), axis=45.0)
    work_hd(p, k, [fr.P(tt, float(np.interp(tt, ts, spine)) + 1.9) for tt in np.linspace(27.0, 58.0, 32)], blade)
    edge_hd(p, fr, k, blade, 69.0)
    p.part(fr.prof(c, [(19.8, 4.0), (20.8, 8.4), (23.8, 8.4), (24.8, 4.2)]), k['guard'], 'ray', base=0, sep=True, tex=ttex(k['guard']))
    p.line([fr.P(22.3, -7.2), fr.P(22.3, 7.2)], k['guard'], 2, 1.0)
    gem_hd(p, k, *fr.P(22.3, 0.0), 2.3)
    p.sparkle(*fr.P(60.0, -3.0), 1)
    finish_hd(p, k)


def short_blade_hd(p, grade='common'):
    """A short blade: a leaf blade, broad and quick, under a small oval guard; the grip and pommel; shorter on
    the diagonal than the jian by a third."""
    k, c, fr = K(grade), p.c, WFRAME
    fitting_hd(p, fr, k, 9.0, 13.4, 3.4, 1.0)
    grip_hd(p, fr, k, 13.0, 25.0, 2.8)
    blade = leaf_blade_hd(p, fr, k, 25.0, 58.5, 5.0, 0.5)
    work_hd(p, k, along(fr, 31.0, 50.0), blade)
    edge_hd(p, fr, k, blade, 58.5)
    p.part(fr.prof(c, [(24.5, 3.0), (25.5, 5.8), (28.0, 5.8), (29.0, 3.2)]), k['guard'], 'ray', base=0, sep=True, tex=ttex(k['guard']))
    p.line([fr.P(26.7, -4.8), fr.P(26.7, 4.8)], k['guard'], 2, 1.0)
    gem_hd(p, k, *fr.P(26.7, 0.0), 1.9)
    p.sparkle(*fr.P(53.0, -0.9), 1)
    finish_hd(p, k)


def spear_hd(p, grade='common'):
    """A spear: the long shaft with its butt ferrule and a wrapped hand, the collar with its tassel hanging under
    the head, the leaf head with its ridge."""
    k, c, fr = K(grade), p.c, WFRAME
    fitting_hd(p, fr, k, 0.5, 5.0, 2.8, 0.9)
    shaft = fr.prof(c, [(4.5, 1.9), (52.5, 1.9)])
    p.cylinder(fr, shaft, 1.9, k['shaft'], sep=True, tex=ttex(k['shaft']), axis=45.0)
    wrap_hd(p, fr, k, shaft & fr.prof(c, [(15.0, 1.9), (25.0, 1.9)]), 1.9)
    knot = fr.P(52.6, 2.6)
    p.part(c.taper(knot, (knot[0] - 1.4, knot[1] + 4.6), (knot[0] + 0.6, knot[1] + 9.2), 3.2, 1.5) |
           c.taper(knot, (knot[0] + 2.4, knot[1] + 3.6), (knot[0] + 4.2, knot[1] + 7.6), 2.6, 1.3), k['tassel'], 'ray_soft', base=0, sep=False, rim=False)
    head = leaf_blade_hd(p, fr, k, 53.0, 71.0, 5.2, 0.55)
    work_hd(p, k, along(fr, 57.0, 66.0), head)
    edge_hd(p, fr, k, head, 71.0)
    fitting_hd(p, fr, k, 51.0, 56.0, 3.2, 0.9, line=53.5)
    p.part(c.circle(knot[0] + 0.2, knot[1] + 1.6, 1.9), k['bead'], 'sphere', base=1, sep=True, rim=k['lv'] >= 4)
    gem_hd(p, k, *fr.P(53.5, 0.0), 1.5, fallback=False)
    p.sparkle(*fr.P(66.5, -0.8), 1)
    finish_hd(p, k)


def staff_hd(p, grade='common'):
    """A staff: a long shaft with a ferrule, bindings and a wrapped middle, its head curled into a crook capped
    in the grade's metal."""
    k, c, fr = K(grade), p.c, WFRAME
    fitting_hd(p, fr, k, 0.5, 5.5, 3.3, 0.9)
    shaft = fr.prof(c, [(5.0, 2.4), (58.0, 2.4)])
    p.cylinder(fr, shaft, 2.4, k['shaft'], sep=True, tex=ttex(k['shaft']), axis=45.0)
    cx, cy = fr.P(57.5, -4.7)
    crook = c.arc(cx, cy, 7.1, 4.8, 315, 205)
    p.part(crook, k['shaft'], 'ray', base=0, sep=False, tex=ttex(k['shaft']), axis=45.0)
    ex, ey = cx + 4.7 * math.cos(math.radians(205)), cy - 4.7 * math.sin(math.radians(205))
    p.part(c.circle(ex, ey, 2.7), k['guard'], 'sphere', base=0, sep=True)
    gem_hd(p, k, ex - 0.2, ey - 0.2, 1.5, fallback=False)
    for t0 in ((8.0, 12.0) if k['lv'] >= 1 else ()) + (47.0, 51.0):
        fitting_hd(p, fr, k, t0 - 0.9, t0 + 0.9, 2.8, 0.0)
    mid = shaft & fr.prof(c, [(24.0, 2.4), (36.0, 2.4)])
    p.part(mid, k['wrap'] if k['lv'] >= 1 else k['grip'], 'field', base=0, field=fr.field(c, 2.4)[1], bands=((0.18, 2), (0.42, 1), (0.66, 0), (0.86, -1), (9, -2)), sep=True)
    wrap_hd(p, fr, k, mid, 2.4)
    work_hd(p, k, along(fr, 38.0, 46.0), shaft, dark=k['shaft'])
    p.sparkle(*fr.P(56.0, -1.0), 1)
    finish_hd(p, k)


def bow_hd(p, grade='common'):
    """A recurve bow strung on the diagonal: the limbs bowed out to the upper left and curling back at the tips,
    the wrapped grip with its gem on the back, the string from tip to tip."""
    k, c, fr = K(grade), p.c, WFRAME
    limb = k['blade'] if k['lv'] >= 2 else (M('wood') if k['lv'] == 0 else M('darkwood'))

    def at(u):
        """The stave's centre line: a parabola bowed to the upper left, the tips curling back at the ends."""
        t = 5.0 + 62.0 * u
        w = 0.5 - 15.0 * (1.0 - (2.0 * u - 1.0) ** 2) - 3.0 * max(0.0, (abs(2.0 * u - 1.0) - 0.78) / 0.22) ** 1.5
        return fr.P(t, w)
    pts = [at(i / 40.0) for i in range(41)]
    string = M('paper') if k['lv'] < 4 else k['gem']
    p.part(c.seg(*pts[0], *pts[-1], 1.3), string, 'flat', base=1, sep=False, rim=False)
    stave = c.empty()
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        u = abs(2.0 * (i + 0.5) / 40.0 - 1.0)
        stave |= c.seg(a[0], a[1], b[0], b[1], 4.4 - 1.6 * u)
    p.part(stave, limb, 'ray', base=0, sep=True, tex=ttex(limb), axis=45.0)
    for i in (0, -1):
        p.part(c.circle(pts[i][0], pts[i][1], 2.2), k['guard'], 'sphere', base=0, sep=True)
    grip = c.polyline(pts[17:24], 6.2)
    p.part(grip, k['grip'], 'ray', base=0, sep=True)
    wrap_hd(p, Frame(pts[17], 45.0), k, grip, 2.8)
    gx, gy = pts[20]
    gem_hd(p, k, gx - 2.6, gy - 2.6, 1.8)
    work_hd(p, k, pts[25:36], stave, dark=limb)
    p.sparkle(pts[30][0] - 1.0, pts[30][1] - 1.0, 1)
    finish_hd(p, k)


def fan_hd(p, grade='common'):
    """A folding fan open on its sticks: the leaf (paper, then the grade's silk) in its folds, the ribs through it,
    the two guard sticks, the sticks gathered at the rivet, a tassel from the pivot, the grade's work on the leaf."""
    k, c = K(grade), p.c
    px, py, R, a0, a1 = 11.0, 53.0, 44.0, 12.0, 78.0
    leaf_mat = M('paper') if k['lv'] <= 1 else k['cloth']
    stick = M('darkwood') if k['lv'] == 0 else k['guard']

    def ray(a, r0, r1):
        a = math.radians(a)
        return (px + r0 * math.cos(a), py - r0 * math.sin(a), px + r1 * math.cos(a), py - r1 * math.sin(a))
    tassel_hd(p, k, 10.4, 55.4, 0.9)
    leaf = c.sector(px, py, R, a0, a1) & ~c.circle(px, py, 16.0)
    p.part(leaf, leaf_mat, 'ray_soft', base=0, sep=True, tex=ttex(leaf_mat), rim=False)
    for i in range(6):
        if i % 2:
            p.decal(c.sector(px, py, R, a0 + 11.0 * i, a0 + 11.0 * (i + 1)) & leaf, leaf_mat, -1)
    for i in range(1, 6):
        p.decal(c.seg(*ray(a0 + 11.0 * i, 16.0, R - 1.0), 1.0) & leaf, leaf_mat, -2)
    band = c.arc(px, py, R, 2.6, a0, a1) & leaf
    p.decal(band, M('ink') if k['lv'] <= 1 else k['guard'], 1 if k['lv'] <= 1 else 0)
    arc_pts = [(px + 31.0 * math.cos(math.radians(a)), py - 31.0 * math.sin(math.radians(a))) for a in np.linspace(a0 + 5, a1 - 5, 40)]
    work_hd(p, k, arc_pts, leaf & ~band, dark=leaf_mat)
    for a in (23.0, 34.0, 45.0, 56.0, 67.0):
        p.part(c.seg(*ray(a, 0.0, 15.0), 2.0), stick, 'ray_soft', base=-1, sep=True)
    for a in (a0, a1):
        p.part(c.seg(*ray(a, 0.0, R + 0.5), 3.2), stick, 'ray', base=0, sep=True, tex=ttex(stick))
    if k['gem'] is not None:
        gem_hd(p, k, px, py, 2.4)
    else:
        p.part(c.circle(px, py, 2.2), M('gold') if k['lv'] == 1 else stick, 'sphere', base=0, sep=True)
    p.sparkle(px + 12.0, py - 30.0, 1)
    finish_hd(p, k)


def flute_hd(p, grade='common'):
    """A transverse flute along the diagonal: bamboo at Plain, then the grade's metal, capped and banded in the
    guard metal, its finger holes and blow hole, the grade's work at the cord end, the cord hanging from it."""
    k, c, fr = K(grade), p.c, WFRAME
    tassel_hd(p, k, 8.8, 55.6, 0.9)
    body = fr.prof(c, [(2.5, 2.7), (68.0, 2.7)])
    p.cylinder(fr, body, 2.7, k['body'], sep=True, tex=ttex(k['body']), axis=45.0)
    if k['lv'] == 0:
        for t0 in (13.0, 30.0, 47.0):
            p.decal(fr.prof(c, [(t0 - 0.5, 2.7), (t0 + 0.5, 2.7)]) & body, k['body'], -2)
    fitting_hd(p, fr, k, 2.0, 5.6, 3.0, 0.6)
    fitting_hd(p, fr, k, 65.4, 68.6, 3.0, 0.6)
    for t0 in (19.0, 54.0):
        fitting_hd(p, fr, k, t0 - 0.9, t0 + 0.9, 3.0, 0.0)
    for i in range(6):
        p.decal(c.circle(*fr.P(26.0 + 4.6 * i, 0.0), 1.1), M('ink'), 0)
    p.decal(c.circle(*fr.P(60.5, 0.0), 1.3), M('ink'), 0)
    work_hd(p, k, along(fr, 7.5, 16.5), body, dark=k['body'])
    p.sparkle(*fr.P(22.5, -1.4), 1)
    finish_hd(p, k)


def brush_hd(p, grade='common', look=None):
    """A calligraphy brush: the cord loop at the butt cap, the jointed shaft (bamboo at Plain, then the grade's
    metal), the collar, the tuft of hair dipped in ink at the point. `look` (the Wardens' brushes): shaft, collar,
    hair, tip materials, `drop` (the drop's material) and `lit` (a starlight point)."""
    k, c, fr = K(grade), p.c, WFRAME
    look = look or {}
    shaft_mat, collar = look.get('shaft', k['body']), look.get('collar', k['guard'])
    hair, tip = look.get('hair', M('bone')), look.get('tip', M('ink'))
    lx, ly = fr.P(1.4, 0.0)
    p.part(c.ring(lx, ly, 2.5, 1.3), k['tassel'], 'ray_soft', base=0, sep=False, rim=False)
    shaft = fr.prof(c, [(4.0, 2.6), (47.0, 2.6)])
    p.cylinder(fr, shaft, 2.6, shaft_mat, sep=True, tex=ttex(shaft_mat), axis=45.0)
    for t0 in (16.0, 28.0, 40.0):
        if k['lv'] == 0 or shaft_mat.kind == 'wood':
            p.decal(fr.prof(c, [(t0 - 0.5, 2.6), (t0 + 0.5, 2.6)]) & shaft, shaft_mat, -2)
        elif t0 != 28.0:
            fitting_hd(p, fr, k, t0 - 0.8, t0 + 0.8, 2.9, 0.0)
    fitting_hd(p, fr, k, 3.5, 7.0, 3.0, 0.8)
    work_hd(p, k, along(fr, 18.5, 26.5), shaft, dark=shaft_mat)
    p.part(fr.prof(c, [(46.5, 2.8), (47.5, 3.4), (51.5, 3.4), (52.3, 2.9)]), collar, 'ray', base=0, sep=True, tex=ttex(collar))
    p.line([fr.P(49.0, -2.8), fr.P(49.0, 2.8)], collar, 2, 1.0)
    t0, t1 = 52.0, 70.5

    def half(t):
        u = np.clip((t - t0) / (t1 - t0), 0.0, 1.0)
        return 3.6 * (1.0 - u) ** 0.7
    tuft = fr.prof(c, [(float(t), float(half(np.array(t)))) for t in np.linspace(t0, t1, 22)])
    p.cylinder(fr, tuft, half, hair, sep=True)
    t, w = fr.along(c)
    p.decal(tuft & (t > 63.0), tip, 1)
    p.decal(tuft & (t > 63.0) & (t < 66.5) & (w < -0.3), tip, 3)
    if look.get('lit'):
        p.decal(tuft & (t > 67.5), look['lit'], 1)
        p.decal(tuft & (t > 69.0), look['lit'], 3)
    if 'drop' in look:
        dx, dy = fr.P(69.5, 5.4)
        p.part(S.drop(c, dx, dy + 1.0, 1.5, 3.2), look['drop'], 'ray_soft', base=1, sep=True)
    p.sparkle(*fr.P(43.0, -1.4), 1)
    finish_hd(p, k)


def bell_hd(p, grade='common', look=None):
    """A hand-bell on a short handle, its mouth down-right: the cord loop, the handle and its collar, the crown,
    the flaring skirt with its cast bands and the grade's work round the waist, the lip, the clapper in the mouth.
    `look` (the Wardens' bells): body, collar, clapper and mouth materials, `scroll` (a cloud scroll round the
    waist), `lattice` (a lantern cage's lattice cast into the skirt), `mouth_glow`."""
    k, c, fr = K(grade), p.c, BFRAME
    look = look or {}
    Kc = 1.28
    body_mat = look.get('body', k['blade'])
    handle_mat = M('wood') if k['lv'] == 0 else M('darkwood')
    collar = look.get('collar', k['guard'])
    p.part(c.ring(*fr.P(-24.5 * Kc, 0.0), 3.9, 2.0), k['tassel'], 'ray_soft', base=0, sep=False, rim=False)
    handle = fr.prof(c, [(-23.0 * Kc, 2.0), (-21.0 * Kc, 3.2), (-19.0 * Kc, 2.5), (-15.0 * Kc, 2.3), (-12.0 * Kc, 2.6), (-9.5 * Kc, 2.6)])
    p.cylinder(fr, handle, 2.6, handle_mat, sep=True, tex='wood', axis=-45.0)
    p.cylinder(fr, fr.prof(c, [(-10.5 * Kc, 3.9), (-6.0 * Kc, 3.9)]), 3.9, collar, sep=True, tex=ttex(collar))
    p.line([fr.P(-8.2 * Kc, -3.7), fr.P(-8.2 * Kc, 3.7)], collar, -2 if collar.kind == 'jade' else 2, 1.0)
    prof = [(-7.0 * Kc, 2.6), (-5.5 * Kc, 5.4), (-3.0 * Kc, 7.2), (0.0, 8.2), (4.0 * Kc, 8.8), (8.0 * Kc, 9.9),
            (11.0 * Kc, 11.8), (13.0 * Kc, 13.6), (14.5 * Kc, 14.2)]
    body = fr.prof(c, prof)

    def hw_bell(t):
        return np.interp(t, np.array([q[0] for q in prof]), np.array([q[1] for q in prof]))
    p.cylinder(fr, body, hw_bell, body_mat, sep=True, tex=ttex(body_mat))
    t, w = fr.along(c)
    for tt, lv in ((2.0 * Kc, -2), (2.9 * Kc, 1), (9.5 * Kc, -2), (10.4 * Kc, 1)):
        p.decal(body & (t >= tt) & (t < tt + 0.9) & (np.abs(w) < hw_bell(t) - 0.8), body_mat, lv)
    if look.get('scroll'):
        scroll = c.empty()
        for i in range(5):
            scroll |= c.arc(*fr.P(6.0 * Kc, -6.0 + i * 3.0), 1.3, 0.8, 0, 270)
        p.decal(scroll & body, body_mat, -2)
    elif look.get('lattice'):
        X, Y = c.X / c.s, c.Y / c.s
        lat = ((np.floor(X).astype(int) % 3 == 1) | (np.floor(Y).astype(int) % 3 == 1)) & erode4(body) & (t > -2.5 * Kc) & (t < 9.0 * Kc)
        p.decal(lat, body_mat, -2)
        p.decal(lat & (X + Y < 54), body_mat, 0)
    else:
        work_hd(p, k, [fr.P(6.0 * Kc, ww) for ww in np.linspace(-7.6, 7.6, 16)], body & (np.abs(w) < hw_bell(t) - 0.8), dark=body_mat)
    lip = fr.prof(c, [(14.0 * Kc, 14.7), (16.4 * Kc, 14.7)])
    p.cylinder(fr, lip, 14.7, body_mat, base=1, sep=True)
    mouth = fr.prof(c, [(15.6 * Kc, 12.7), (18.4 * Kc, 11.8)]) & ~lip
    p.part(mouth, look.get('mouth', M('ink')), 'flat', base=1 if 'mouth' not in look else 0, sep=True, rim=False)
    if 'mouth' in look:
        p.decal(mouth & ~erode4(mouth), look['mouth'], 1)
    mx, my = fr.P(18.2 * Kc, 0.0)
    clapper = look.get('clapper', k['gem'] if k['lv'] >= 2 else handle_mat)
    p.part(c.circle(mx, my, 3.8), clapper, 'sphere', base=0, sep=True, spec=(mx - 1.2, my - 1.2))
    p.sparkle(*fr.P(-1.5 * Kc, -5.0), 1)
    if 'mouth_glow' in look:
        p.glow(look['mouth_glow'], 1.0)
    elif 'glow' in look:
        if look['glow']:
            p.glow(*look['glow'])
    else:
        finish_hd(p, k)


def gauntlets_hd(p, grade='common'):
    """A gauntlet, the fist over its cuff: four fingers with their knuckle plates, the back of the hand, the thumb
    across, the cuff with its trim bands and the grade's work between them, the gem on the back."""
    k, c = K(grade), p.c
    plain = k['lv'] == 0
    plate = M('straw') if plain else k['blade']
    under = k['grip']
    trim = k['guard']
    cuff = c.poly([(16.0, 42.0), (48.0, 42.0), (52.0, 59.0), (12.0, 59.0)])
    p.part(cuff, M('hemp') if plain else plate, 'ray', base=0, sep=True, tex=ttex(plate), axis=90.0)
    for y in (44.5, 54.5):
        p.part(c.box(11.5, y, 52.5, y + 2.6) & cuff, trim, 'bevel', base=0, sep=True, hw=1, sw=1, rim=False)
    work_hd(p, k, [(x, 50.5) for x in np.linspace(17.0, 47.0, 31)], cuff, dark=plate)
    # the fingers curl under: the knuckles are a row of domed plates, the hand's back covers the rest
    for i in range(4):
        x0 = 12.5 + i * 9.75
        top = 13.0 + (2.0 if i in (0, 3) else 0.0)
        p.part(c.rrect(x0, top, x0 + 9.0, 28.0, 4.2), under, 'ray', base=0, sep=True)
        p.part(c.rrect(x0, top, x0 + 9.0, top + 9.0, 4.2), plate, 'bevel', base=0 if plain else 1, sep=True, hw=1, sw=1, tex=ttex(plate) if not plain else None)
    hand = c.rrect(12.0, 24.0, 52.0, 43.5, 6.0)
    p.part(hand, under, 'ray', base=0, sep=True)
    if plain:
        wrap_hd(p, Frame((12.0, 24.0), 0.0), k, hand, 10.0)
    else:
        p.part(c.rrect(16.0, 26.5, 48.0, 41.0, 5.0), plate, 'ray', base=0, sep=True, tex=ttex(plate), axis=90.0)
    p.part(c.rrect(9.5, 33.0, 34.0, 41.5, 4.2), M('hemp') if plain else plate, 'ray', base=0, sep=True, tex=ttex(plate), axis=0.0)
    if plain:
        for x in range(12, 33, 3):
            p.decal(c.box(x, 33.5, x + 1, 41.0), M('hemp'), -1)
    gem_hd(p, k, 41.5, 31.5, 2.6)
    p.sparkle(15.0, 15.0, 1)
    finish_hd(p, k)


BUILDERS = {'gauntlets': gauntlets_hd, 'jian': jian_hd, 'spear': spear_hd, 'short_blade': short_blade_hd, 'staff': staff_hd,
            'bow': bow_hd, 'heavy_sabre': heavy_sabre_hd, 'fan': fan_hd, 'flute': flute_hd, 'brush': brush_hd, 'bell': bell_hd}

for _fam, _build in BUILDERS.items():
    for _word, _grade in GRADE_WORDS:
        _draw = (lambda p, f=_build, g=_grade: f(p, g))
        register(FAM, '%s_%s' % (_word, _fam), _draw, GROUP)
        hd('%s_%s' % (_word, _fam), _draw)


# --------------------------------------------------------------------------- the Star Wardens' arms (v1.2 Phase D)
# The Sage pair carries the sage kit; the Will pair is darker and richer, lit by lantern light.
ASH = M('hollow', 'matte')
STAR_GLOW, TIDE_GLOW = '#F3E3A6', '#7FD4FF'


def ink_warden_brush_hd(p):
    """The Ink-Warden's Brush: a Warden scribe's brush, sand bamboo with jade joints, its hairs set in black
    lacquer, a drop of ink falling from the tip."""
    brush_hd(p, 'sage', dict(shaft=M('sand', 'wood'), collar=M('ink'), drop=M('ink')))


def starwrit_brush_hd(p):
    """The Starwrit Brush: a dark shaft with gold bands, its ash-grey tip dipped in lantern ash and lit at the
    point, a drop of starlight falling from it."""
    brush_hd(p, 'will', dict(shaft=M('darkwood'), hair=ASH, tip=ASH, lit=M('starlight'), drop=M('starlight')))


def handbell_hd(p):
    """The Warden's hand-bell: cast bronze on a darkwood handle with a jade collar, a cloud scroll round the waist,
    a red cord, its mouth down-right."""
    bell_hd(p, 'sage', dict(body=M('bronze'), collar=M('jade'), scroll=True, clapper=M('darkwood'), glow=('#FFC870', 0.8)))


def tidebreak_bell_hd(p):
    """The Tidebreak Bell: pale silver cast from a lantern cage that fell in the Breach, the cage's lattice still
    in the skirt, a gold collar, a cold blue light in its mouth round an ice clapper."""
    bell_hd(p, 'will', dict(body=M('silver'), collar=M('gold'), lattice=True, clapper=M('ice'), mouth=M('ice'), mouth_glow=TIDE_GLOW))


for _id, _draw in (('ink_warden_brush', ink_warden_brush_hd), ('starwrit_brush', starwrit_brush_hd),
                   ('wardens_handbell', handbell_hd), ('tidebreak_bell', tidebreak_bell_hd)):
    register(FAM, _id, _draw, GROUP)
    hd(_id, _draw)
