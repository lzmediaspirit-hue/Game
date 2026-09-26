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

from pix import Canvas, Ramp, dilate4, dilate8, erode4, rgb
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


# ============================================================================ v1.2 Phase D · the brush and the bell
# The Star Wardens' arms, in the same diagonal frame as the per-grade weapons. The Sage pair (ink_warden_brush,
# wardens_handbell) carries the sage kit: sunsteel gold, jade, red silk and the sun glow. The Will pair
# (starwrit_brush, tidebreak_bell) is darker and richer, lit by lantern light.
V12D_ASH_TIP = Ramp(['#2A2C32', '#474A52', '#666A72', '#8C9098', '#B4B8BE'], '#101216')
V12D_STAR_GLOW = '#F3E3A6'
V12D_TIDE_GLOW = '#7FD4FF'
V12D_LV_INK = ((0.3, 4), (0.62, 2), (9, 1))


def _v12d_halo(c, mask, col, alphas):
    """Stepped glow bands round one part only, on empty canvas (call after c.outline())."""
    cur = dilate4(mask) & (c.alpha > 0)
    for al in alphas:
        ring = dilate8(cur) & ~cur
        free = ring & (c.alpha == 0)
        c.rgb[free] = np.array(rgb(col), np.uint8)
        c.alpha[free] = al
        cur |= ring


def _v12d_brush(will):
    """A large calligraphy brush on the diagonal: the jointed shaft, a black lacquered collar, the tapered tip, a
    drop falling from it. Sage: sand bamboo with jade joints, an ink tip. Will: a dark shaft with a gold band,
    an ash-grey tip lit at the point."""
    c = Canvas(32)
    g = G('sage')
    shaft = R['darkwood'] if will else R['sand']
    joint = R['gold'] if will else R['jade']
    tip = V12D_ASH_TIP if will else R['ink']
    # the cord loop at the butt
    tas = S.bez_line(c, (5.5, 26.5), (2.6, 27.6), (3.2, 30.2), 1.3)
    c.put(tas, R['red'], 'flat', base=2)
    u, v = UV(c)
    part(c, -25, 5, 31.5, 2.0, shaft, LV_ROUND)
    for uc in (-18, -10, -2):
        part(c, uc, uc + 1, 31.5, 2.3, shaft, LV_ROUND)
        c.put(band(c, uc, uc + 1, 31.5, 2.3) & (v < 31), shaft[3], 'flat', only_on=True)
    part(c, -27, -24, 31.5, 2.4, joint, LV_ROUND)
    if will:
        part(c, 3, 5, 31.5, 2.5, joint, LV_ROUND)
    # the lacquered collar, then the tip: fuller than the shaft at its root, tapering to the point
    part(c, 6, 9, 31.5, 2.5, R['ink'], V12D_LV_INK)
    c.put(band(c, 6, 9, 31.5, 2.5) & (c.X + c.Y < 30), R['ink'][4], 'flat', only_on=True)
    tip_hw = taper(9, 27, 3.4, 0.0)
    part(c, 9, 27, 31.5, tip_hw, tip, V12D_LV_INK if not will else LV_ROUND)
    if will:
        pt = band(c, 22, 27, 31.5, tip_hw) & c.a
        c.put(band(c, 25, 27, 31.5, tip_hw) & c.a, R['starlight'], 'flat', base=3)
        c.put(band(c, 27, 27, 31.5, tip_hw) & c.a, R['starlight'], 'flat', base=4)
    # the drop falling from the tip
    drop = S.drop(c, 27.3, 11.5, 1.7, 3.6)
    c.put(drop, R['starlight'] if will else R['ink'], 'ray', base=3 if will else 2)
    c.outline()
    if will:
        c.glow(V12D_STAR_GLOW, (60, 25))
        _v12d_halo(c, pt, V12D_STAR_GLOW, (130, 60))
    else:
        c.glow(g['glow'], (95, 40))
    return c


def _v12d_bell(will):
    """A hand-bell on a short dark-wood handle, the mouth down-right: the cord loop, the handle and its collar,
    the crown, the flaring skirt, the lip, the clapper hanging in the mouth. Sage: bronze, jade collar, red cord.
    Will: pale grey-silver cast from a lantern cage, the lattice still on it, a blue glow at the mouth."""
    c = Canvas(32)
    g = G('sage')
    body_r = R['silver'] if will else R['bronze']
    cx = cy = 15.6
    k = 0.70710678

    def P(s, t):
        return (cx + (s + t) * k, cy + (s - t) * k)

    def prof(pts):
        return c.poly([P(s, t) for (s, t) in pts] + [P(s, -t) for (s, t) in pts[::-1]])

    # the cord loop and the handle
    lx, ly = P(-16.5, 0)
    loop = c.ring(lx, ly, 2.3, 1.2)
    c.put(loop, R['red'], 'flat', base=2)
    c.put(loop & (c.X + c.Y < lx + ly), R['red'], 'flat', base=3)
    handle = prof([(-14.5, 1.4), (-13, 2.2), (-11.5, 1.6), (-6.5, 1.6)])
    c.put(handle, R['darkwood'], 'ray', base=2, sep=True)
    collar = prof([(-7.5, 2.3), (-4.5, 2.3)])
    c.put(collar, R['gold'] if will else g['accent'], 'ray', base=2, sep=True)
    # the bell: crown, waist, skirt and lip
    bell = prof([(-5, 1.6), (-4, 3.4), (-2.5, 4.4), (0, 4.9), (3, 5.2), (5.5, 5.8), (7.5, 7.0), (8.5, 8.2), (9.6, 8.4)])
    lip = prof([(8.3, 8.6), (10.2, 8.6)])
    c.put(bell, body_r, 'ray', base=2, sep=True, bands=((0.2, 2), (0.42, 1), (0.7, 0), (0.88, -1), (9, -2)))
    if will:
        # the lantern cage's lattice, still cast into the metal
        lat = ((c.xi % 3 == 1) | (c.yi % 3 == 1)) & erode4(bell) & ~prof([(-5, 3), (-2.6, 3)])
        c.put(lat, body_r[1], 'flat', out=body_r.out)
        c.put(lat & (c.X + c.Y < 27), body_r[3], 'flat', out=body_r.out)
    else:
        c.put(prof([(1.5, 5.1), (2.5, 5.1)]) & bell, body_r[1], 'flat', out=body_r.out)
        c.put(prof([(-3, 3.9), (-2, 3.9)]) & bell, body_r[4], 'flat', out=body_r.out)
    c.put(lip, body_r, 'ray', base=3, sep=True)
    c.put(lip & (c.X + c.Y > 40), body_r, 'flat', base=1)
    # the mouth, and the clapper hanging in it
    mx, my = P(10.9, 0)
    mouth = prof([(9.8, 7.2), (12.0, 6.6)]) & ~lip
    c.put(mouth, R['ink'] if not will else R['ice'], 'flat', base=1 if not will else 0, sep=True)
    if will:
        c.put(mouth & ~erode4(mouth), R['ice'], 'flat', base=1)
    clap = c.circle(mx + 0.4, my + 0.4, 2.0)
    c.put(clap, R['ice'] if will else R['darkwood'], 'sphere', base=3 if will else 2, sep=True)
    c.outline()
    if will:
        c.glow(V12D_STAR_GLOW, (40,))
        _v12d_halo(c, mouth | clap, V12D_TIDE_GLOW, (120, 55))
    else:
        c.glow(g['glow'], (95, 40))
    return c


register(FAM, 'ink_warden_brush', lambda: _v12d_brush(False), GROUP)
register(FAM, 'starwrit_brush', lambda: _v12d_brush(True), GROUP)
register(FAM, 'wardens_handbell', lambda: _v12d_bell(False), GROUP)
register(FAM, 'tidebreak_bell', lambda: _v12d_bell(True), GROUP)
