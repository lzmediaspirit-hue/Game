"""Weapons: 6 family silhouettes x 5 grade material sets.

Weapons are drawn diagonally (bottom-left -> top-right) in 45-degree space:
u = x - y runs along the weapon, v = x + y across it (v = 31 is the canvas
anti-diagonal). A part is a band `|v - vc(u)| <= hw(u)` over a u-range, shaded
across its width (upper-left side lit), which keeps every edge a clean 1:1
pixel staircase.

Grades: training (Plain: wood + hemp wraps), iron (Common: iron grey),
jadeiron (Earth: green jadeiron + jade inlay), cloudsteel (Heaven: pale blue +
cloud engravings), mistjade (Mystic: violet + gold + faint glow).
"""
import numpy as np

from pix import Canvas, Ramp, dilate4, erode4
from palette import R, GRADES
from registry import register
import shapes as S

FAM, GROUP = 'equipment', 'weapons'

GRADE_WORDS = [('training', 'plain'), ('iron', 'common'), ('jadeiron', 'earth'),
               ('cloudsteel', 'heaven'), ('mistjade', 'mystic'), ('stormsteel', 'spirit'), ('sunsteel', 'sage')]

LV_BLADE = ((0.34, 3), (0.5, 4), (0.75, 2), (9, 1))   # lit edge, ridge, shade
LV_ROUND = ((0.3, 3), (0.66, 2), (9, 1))
LV_FLATLIT = ((0.4, 3), (0.8, 2), (9, 1))


def UV(c):
    return c.xi - c.yi, c.xi + c.yi


def _val(f, u):
    return f(u) if callable(f) else np.full(u.shape, float(f))


def band(c, u0, u1, vc=31, hw=1):
    u, v = UV(c)
    vcv, hwv = _val(vc, u), _val(hw, u)
    return (u >= u0) & (u <= u1) & (np.abs(v - vcv) <= hwv + 1e-6) & (hwv >= 0)


def paint_band(c, mask, ramp, vc=31, hw=1, levels=LV_ROUND, sep=False, sep_col=None, only_on=False):
    u, v = UV(c)
    vcv, hwv = _val(vc, u), _val(hw, u)
    t = (v - (vcv - hwv)) / (2 * hwv + 1.0)
    idx = np.full(mask.shape, levels[-1][1])
    for thr, lv in reversed(levels):
        idx = np.where(t < thr, lv, idx)
    if sep:
        ring = dilate4(mask) & ~mask & c.a
        c.rgb[ring] = ramp.out if sep_col is None else sep_col
        c.oc[ring] = ramp.out
    if only_on:
        mask = mask & c.a
    cols = np.array(ramp.c, np.uint8)
    idx = np.clip(idx, 0, len(ramp) - 1)
    c.rgb[mask] = cols[idx[mask]]
    c.a |= mask
    c.alpha[mask] = 255
    c.oc[mask] = ramp.out
    return mask


def part(c, u0, u1, vc, hw, ramp, levels=LV_ROUND, sep=True):
    m = band(c, u0, u1, vc, hw)
    return paint_band(c, m, ramp, vc, hw, levels, sep=sep)


def wraps(c, mask, ramp, period=3, phase=0):
    u, v = UV(c)
    stripe = mask & ((u + phase) % period == 0)
    c.put(stripe, ramp[0] if len(ramp) > 1 else ramp, 'flat', only_on=True)


def taper(u0, u1, w0, w1):
    def f(u):
        t = np.clip((u - u0) / float(max(1, u1 - u0)), 0, 1)
        return w0 + (w1 - w0) * t
    return f


def G(grade):
    g = dict(GRADES[grade])
    if grade == 'plain':
        g['blade'] = R['wood']
        g['guard'] = R['darkwood']
    else:
        g['blade'] = g['metal']
        g['guard'] = g['accent']
    return g


def decorate_blade(c, grade, g, u0, u1, vc=31):
    """Grade-specific blade decoration: jade inlay, cloud engraving, glow runes."""
    u, v = UV(c)
    if grade == 'earth':
        inlay = band(c, u0, u1, vc, 0) & c.a
        c.put(inlay, R['jade'], 'flat', base=3, only_on=True)
    elif grade == 'heaven':
        for uc in range(u0 + 2, u1 - 2, 7):
            curl = (band(c, uc, uc + 3, vc - 1, 0) | band(c, uc + 3, uc + 3, vc + 1, 1)) & c.a
            c.put(curl, R['cloud'][4], 'flat', only_on=True)
    elif grade == 'mystic':
        runes = band(c, u0, u1, vc, 0) & ((u // 2) % 3 != 0) & c.a
        c.put(runes, R['violet'][4], 'flat', only_on=True)
    elif grade == 'spirit':
        # a zigzag of lightning down the fuller
        zig = lambda uu: (vc(uu) if callable(vc) else float(vc)) + np.where((uu // 3) % 2 == 0, -0.5, 0.5)
        bolt = band(c, u0, u1, zig, 0) & c.a
        c.put(bolt, R['cyan'][4], 'flat', only_on=True)
    elif grade == 'sage':
        # desert glass set along the fuller, every few pixels a sun-bright bead
        inlay = band(c, u0, u1, vc, 0) & c.a
        c.put(inlay, R['ember'][3], 'flat', only_on=True)
        c.put(inlay & ((u // 4) % 3 == 0), R['ember'][4], 'flat', only_on=True)
    elif grade == 'plain':
        grain = band(c, u0, u1, vc + 1, 0) & ((u // 3) % 2 == 0) & c.a
        c.put(grain, R['wood'][1], 'flat', only_on=True)


def finish(c, grade):
    c.outline()
    if grade == 'mystic':
        c.glow('#B18DE2', (95, 40))
    if grade == 'spirit':
        c.glow('#7FD4FF', (95, 40))
    if grade == 'sage':
        c.glow('#FFC870', (95, 40))
    return c


# ============================================================================ jian
def jian(grade):
    g = G(grade)
    c = Canvas(32)
    blade_hw = lambda u: np.where(u > 19, np.maximum(0, 3 - (u - 19) * 0.5), 3.0)
    tas = S.bez_line(c, (5.5, 24.5), (2, 25), (2.5, 30), 1.6)
    c.put(tas, R['red'] if grade != 'mystic' else R['violet'], 'flat', base=2)
    part(c, -21, -8, 31, 2, g['grip'], LV_ROUND)
    grip = band(c, -20, -9, 31, 2)
    wraps(c, grip, R['hemp'] if grade == 'plain' else g['wrap'], 2 if grade == 'plain' else 3)
    part(c, -25, -21, 31, 2.5, g['guard'], LV_ROUND)
    part(c, -8, 26, 31, blade_hw, g['blade'], LV_BLADE if grade != 'plain' else LV_FLATLIT)
    decorate_blade(c, grade, g, -4, 18)
    guard_hw = lambda u: 6.5 - np.abs(u + 7) * 1.2
    part(c, -10, -4, 31, guard_hw, g['guard'], LV_ROUND)
    if g['gem'] is not None:
        part(c, -8, -6, 31, 1, g['gem'], ((0.5, 4), (9, 2)), sep=True)
    return finish(c, grade)

# ============================================================================ spear
def spear(grade):
    g = G(grade)
    c = Canvas(32)
    shaft = {'plain': R['wood'], 'common': R['wood'], 'earth': R['darkwood'], 'heaven': R['silk_navy'],
             'mystic': R['plum'], 'spirit': R['navy'], 'sage': R['clay']}[grade]
    part(c, -27, 9, 31.5, 1.5, shaft, LV_ROUND)
    wraps(c, band(c, -15, -5, 31.5, 1.5), R['hemp'] if grade == 'plain' else g['wrap'], 2 if grade == 'plain' else 3)
    part(c, -28, -24, 31.5, 2, g['guard'], LV_ROUND)
    tassel_col = R['red'] if grade != 'mystic' else R['violet']
    tvc = lambda u: 31.5 + (10 - u) * 0.45
    thw = lambda u: 1.5 + (10 - u) * 0.75
    tas = band(c, 3, 10, tvc, thw)
    paint_band(c, tas, tassel_col, tvc, thw, LV_ROUND, sep=True)
    u, v = UV(c)
    c.put(tas & (v % 2 == 0) & (u < 8), tassel_col[1], 'flat', only_on=True)
    part(c, 9, 12, 31.5, 2.5, g['guard'], LV_ROUND)
    head_hw = lambda u: np.where(u < 17, 1.5 + (u - 12) * 0.7, np.maximum(0, 4.3 - (u - 17) * 0.45))
    blade = g['blade'] if grade != 'plain' else R['straw']
    part(c, 12, 27, 31.5, head_hw, blade, LV_BLADE)
    decorate_blade(c, grade, g, 14, 24, 31)
    return finish(c, grade)

# ============================================================================ short blade (dao)
def short_blade(grade):
    g = G(grade)
    c = Canvas(32)
    ring = c.ring(6, 26, 3.2, 1.4)
    c.put(ring, g['guard'], 'flat', base=3)
    part(c, -18, -6, 31, 2, g['grip'], LV_ROUND)
    wraps(c, band(c, -17, -7, 31, 2), R['hemp'] if grade == 'plain' else g['wrap'], 2 if grade == 'plain' else 3)
    vc = lambda u: 31.5 + 0.014 * (u + 4) ** 2
    hw = lambda u: np.where(u < 14, 2.8 + (u + 4) * 0.07, np.maximum(0, 4.1 - (u - 14) * 0.6))
    lv = ((0.25, 3), (0.62, 2), (0.8, 1), (9, 4)) if grade != 'plain' else LV_FLATLIT
    part(c, -4, 21, vc, hw, g['blade'], lv)
    decorate_blade(c, grade, g, 0, 13, 30)
    part(c, -7, -3, 31, 4.5, g['guard'], LV_ROUND)
    if g['gem'] is not None:
        part(c, -6, -4, 31, 1, g['gem'], ((0.5, 4), (9, 2)), sep=True)
    return finish(c, grade)

# ============================================================================ staff
def staff(grade):
    g = G(grade)
    c = Canvas(32)
    pole = {'plain': R['wood'], 'common': R['darkwood'], 'earth': R['darkwood'], 'heaven': R['silk_navy'],
            'mystic': R['plum'], 'spirit': R['navy'], 'sage': R['clay']}[grade]
    part(c, -27, 27, 31.5, 1.5, pole, LV_ROUND)
    cap = g['guard'] if grade != 'plain' else R['darkwood']
    for (u0, u1) in ((-28, -21), (21, 28)):
        part(c, u0, u1, 31.5, 2, cap, LV_ROUND)
        ue = u1 - 1 if u0 < 0 else u0
        part(c, ue, ue + 1, 31.5, 3, cap, LV_ROUND)
    if grade == 'plain':
        part(c, -6, 6, 31.5, 2, R['hemp'], LV_ROUND)
        wraps(c, band(c, -6, 6, 31.5, 2), R['hemp'], 2)
    else:
        for uc in (-10, 10):
            part(c, uc - 1, uc + 1, 31.5, 2.5, g['accent'], LV_ROUND)
        part(c, -6, 6, 31.5, 2, g['wrap'], LV_ROUND)
        wraps(c, band(c, -6, 6, 31.5, 2), g['wrap'], 3)
    if g['gem'] is not None:
        for uc in (-26, 25):
            part(c, uc, uc + 1, 31.5, 1, g['gem'], ((0.5, 4), (9, 2)), sep=True)
    if grade == 'heaven':
        for uc in (-17, 14):
            curl = (band(c, uc, uc + 2, 30, 0) | band(c, uc + 2, uc + 2, 31, 0)) & c.a
            c.put(curl, R['cloud'][4], 'flat', only_on=True)
    return finish(c, grade)

# ============================================================================ gauntlets
def gauntlets(grade):
    g = G(grade)
    c = Canvas(32)
    plain = grade == 'plain'
    plate = g['metal'] if not plain else R['straw']
    under = g['grip'] if not plain else R['hemp']
    trim = g['accent'] if not plain else R['straw']
    # cuff / bracer
    cuff = c.poly([(8, 19), (24, 19), (26.5, 30), (5.5, 30)])
    c.put(cuff, plate if not plain else R['hemp'], 'ray', base=2)
    for y in (21, 27):
        c.put(c.rect(5, y, 27, y + 1) & cuff, trim, 'flat', base=3 if y == 21 else 2)
    if plain:
        c.put(cuff & (c.yi % 2 == 0), R['hemp'][1], 'flat', only_on=True)
    # back of the hand
    back = S.rounded_rect(c, 6, 9, 25, 20, 3)
    c.put(back, under, 'ray', base=2, sep=True)
    # four curled fingers with knuckle plates
    for k, (x0, x1) in enumerate(((6, 10), (11, 15), (16, 20), (21, 25))):
        top = 5 + (1 if k in (0, 3) else 0)
        f = S.rounded_rect(c, x0, top, x1, 13, 1)
        c.put(f, under, 'ray', base=2, sep=True)
        kp = S.rounded_rect(c, x0, top, x1, top + 3, 1)
        c.put(kp, plate, 'bevel', base=2 if not plain else 3, sep=True)
    # thumb across the front
    th = S.rounded_rect(c, 5, 14, 18, 18, 2)
    c.put(th, plate if not plain else R['hemp'], 'ray', base=2, sep=True)
    if plain:
        for x in range(7, 18, 3):
            c.put(c.rect(x, 14, x, 18) & th, R['hemp'][1], 'flat', only_on=True)
        c.put(back & (c.xi % 3 == 0) & (c.yi > 13), R['hemp'][1], 'flat', only_on=True)
    if g['gem'] is not None:
        gem = S.diamond(c, 16, 24.5, 2.6, 2.6)
        c.put(gem, g['gem'], 'ray', base=3, sep=True)
    if grade == 'heaven':
        for x0 in (8, 21):
            c.put(c.rect(x0, 24, x0 + 2, 24) | c.rect(x0 + 2, 25, x0 + 2, 25), R['cloud'][4], 'flat', only_on=True)
    return finish(c, grade)

# ============================================================================ bow
def bow(grade):
    g = G(grade)
    c = Canvas(32)
    limb = {'plain': R['wood'], 'common': R['darkwood'], 'earth': R['jadeiron'], 'heaven': R['cloudsteel'],
            'mystic': R['mistjade_m'], 'spirit': R['storm'], 'sage': R['gold']}[grade]
    depth = 12.0
    vc = lambda u: 31 - depth * (1 - (u / 25.0) ** 2) + np.where(np.abs(u) > 21, (np.abs(u) - 21) * 1.2, 0)
    hw = lambda u: np.where(np.abs(u) < 5, 2.0, np.maximum(1.0, 1.7 - (np.abs(u) - 5) * 0.03))
    # string first (behind)
    string = c.bres(4, 26, 26, 4) | c.bres(5, 26, 26, 5)
    c.put(string, R['paper'] if grade != 'mystic' else R['violet'], 'flat', base=4 if grade != 'mystic' else 3)
    part(c, -24, 24, vc, hw, limb, LV_ROUND)
    grip = band(c, -4, 4, vc, 2.5)
    paint_band(c, grip, g['grip'] if grade != 'plain' else R['hemp'], vc, 2.5, LV_ROUND, sep=True)
    wraps(c, grip, g['grip'] if grade != 'plain' else R['hemp'], 2)
    for s in (-1, 1):
        tip = band(c, 21 * s if s > 0 else -24, 24 if s > 0 else -21, vc, 2)
        paint_band(c, tip, g['accent'] if grade != 'plain' else R['bone'], vc, 2, LV_ROUND, sep=True)
    if g['gem'] is not None:
        gem = band(c, -1, 1, lambda u: vc(u) - 2.5, 0.8)
        paint_band(c, gem, g['gem'], lambda u: vc(u) - 2.5, 0.8, ((0.5, 4), (9, 2)), sep=True)
    if grade == 'heaven':
        for uc in (-14, 11):
            curl = band(c, uc, uc + 2, vc, 0) & c.a
            c.put(curl, R['cloud'][4], 'flat', only_on=True)
    return finish(c, grade)


# ============================================================================ heavy sabre (v1.1)
def heavy_sabre(grade):
    """A broad, curved dao: ring pommel, wrapped grip, a disc guard and a blade that widens toward the tip."""
    g = G(grade)
    c = Canvas(32)
    ring = c.ring(5.0, 26.5, 2.8, 1.4)
    c.put(ring, g['guard'], 'flat', base=3)
    tas = S.bez_line(c, (5.0, 29.2), (3.4, 29.9), (2.2, 29.8), 1.1)
    c.put(tas, R['red'] if grade != 'mystic' else R['violet'], 'flat', base=2)
    part(c, -21, -9, 31, 2, g['grip'], LV_ROUND)
    wraps(c, band(c, -20, -10, 31, 2), R['hemp'] if grade == 'plain' else g['wrap'], 2 if grade == 'plain' else 3)
    vc = lambda u: 31.0 + 0.005 * (u + 6) ** 2
    hw = lambda u: np.where(u < 16, 2.8 + (u + 6) * 0.07, np.maximum(0, 4.3 - (u - 16) * 0.66))
    lv = ((0.25, 3), (0.62, 2), (0.8, 1), (9, 4)) if grade != 'plain' else LV_FLATLIT
    part(c, -6, 22, vc, hw, g["blade"], lv)
    decorate_blade(c, grade, g, -2, 14, 31.6)
    part(c, -9, -5, 31, 5.0, g['guard'], LV_ROUND)
    if g['gem'] is not None:
        part(c, -8, -6, 31, 1, g['gem'], ((0.5, 4), (9, 2)), sep=True)
    return finish(c, grade)


# ============================================================================ fan (v1.1)
def fan(grade):
    """A folding fan opened in a quarter-circle: paper (silk above plain) on ribs of the grade's material."""
    g = G(grade)
    c = Canvas(32)
    px, py, rad = 7.0, 25.5, 21.0
    import math
    arc = [(px + rad * math.cos(math.radians(a)), py - rad * math.sin(math.radians(a))) for a in range(8, 84, 4)]
    paper = c.poly([(px, py)] + arc)
    inner = c.circle(px, py, rad * 0.36)
    leaf = {'plain': R['paper'], 'common': R['paper'], 'earth': R['jade'], 'heaven': R['cloud'], 'mystic': R['violetsilk'],
            'spirit': R['sky'], 'sage': R['gold']}[grade]
    c.put(paper & ~inner, leaf, 'flat', base=3)
    # Folds: alternate panels a shade darker.
    for k, a in enumerate(range(8, 84, 8)):
        a0, a1 = math.radians(a), math.radians(a + 4)
        panel = c.poly([(px, py), (px + rad * math.cos(a0), py - rad * math.sin(a0)), (px + rad * math.cos(a1), py - rad * math.sin(a1))])
        c.put(panel & paper & ~inner, leaf[2], 'flat', only_on=True)
    # An ink band near the edge, and the ribs gathered into the pivot.
    edge = paper & ~c.circle(px, py, rad - 3.0) & c.circle(px, py, rad - 1.5)
    c.put(edge, R['ink'] if grade in ('plain', 'common') else g['accent'], 'flat', base=2, only_on=True)
    rib_col = R['darkwood'] if grade == 'plain' else g['guard']
    for a in range(8, 88, 8):
        rib = c.seg(px, py, px + rad * 0.4 * math.cos(math.radians(a)), py - rad * 0.4 * math.sin(math.radians(a)), 1.2)
        c.put(rib, rib_col, 'flat', base=2)
    c.put(c.circle(px, py, 1.6), R['gold'], 'flat', base=4)
    return finish(c, grade)


# ============================================================================ flute (v1.1, the Music path)
def flute(grade):
    """A transverse flute along the diagonal: bamboo (or the grade's stone) with joints, finger holes and a tassel."""
    g = G(grade)
    c = Canvas(32)
    body = {'plain': R['bamboo'], 'common': R['bamboo'], 'earth': R['jade'], 'heaven': R['cloud'], 'mystic': R['mistjade'],
            'spirit': R['sky'], 'sage': R['gold']}[grade]
    part(c, -26, 26, 31.5, 1.6, body, LV_ROUND)
    for uc in (-18, -4, 10, 22):
        part(c, uc, uc, 31.5, 1.8, g['accent'] if grade != 'plain' else R['darkwood'], LV_ROUND)
    u, v = UV(c)
    holes = band(c, -14, 18, 30.5, 0) & (((u + 14) % 5) == 0) & c.a
    c.put(holes, R['ink'], 'flat', base=0, only_on=True)
    tas = S.bez_line(c, (6.5, 25.5), (3.2, 26.8), (3.4, 29.6), 1.3)
    c.put(tas, R['red'] if grade != 'mystic' else R['violet'], 'flat', base=2)
    return finish(c, grade)


BUILDERS = {'gauntlets': gauntlets, 'jian': jian, 'spear': spear, 'short_blade': short_blade, 'staff': staff,
            'bow': bow, 'heavy_sabre': heavy_sabre, 'fan': fan, 'flute': flute}

for _fam in ('gauntlets', 'jian', 'spear', 'short_blade', 'staff', 'bow', 'heavy_sabre', 'fan', 'flute'):
    for _word, _grade in GRADE_WORDS:
        register(FAM, '%s_%s' % (_word, _fam), (lambda f=_fam, gr=_grade: BUILDERS[f](gr)), GROUP)
