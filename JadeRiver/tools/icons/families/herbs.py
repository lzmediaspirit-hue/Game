"""Herbs: shared leaf / stem / root builders with species variants."""
import math

from pix import Canvas, dilate4, erode4, move
from palette import R
from registry import register
import shapes as S

FAM, GROUP = 'items', 'herbs'


def _leaves(c, specs, ramp=None, rib=True):
    """specs: (bx, by, angle, length, width, bend). Back-to-front order."""
    ramp = ramp or R['leaf']
    for (bx, by, ang, L, W, bend) in specs:
        m = S.leaf(c, bx, by, ang, L, W, bend)
        c.put(m, ramp, 'ray', sep=True)
        if rib and L >= 7:
            c.put(S.midrib(c, bx, by, ang, L, bend, 0.75) & m, ramp[1], 'flat', out=ramp.out)


# ----------------------------------------------------------------------------- willow moss
def willow_moss():
    c = Canvas(32)
    ramp = R['moss']
    ends = [(5.5, 24), (8, 28), (10.5, 25.5), (13, 30), (15.5, 27), (18, 30), (20.5, 26), (23, 28.5), (26, 23.5)]
    body = c.ellipse(15.5, 13.5, 7.5, 5.5)
    strands = []
    for i, (ex, ey) in enumerate(ends):
        sx = 15.5 + (ex - 15.5) * 0.45
        m = S.taper_curve(c, (sx, 13), (sx + (ex - sx) * 0.4, 20), (ex, ey), 3.4, 1.3)
        strands.append(m)
        body |= m
    c.put(body, ramp, 'ray')
    # grooves between strands and lit strand crowns
    for i, (ex, ey) in enumerate(ends[1:-1], 1):
        if i % 2 == 0:
            g = S.bez_line(c, (15.5 + (ex - 15.5) * 0.3, 15), (15.5 + (ex - 15.5) * 0.6, 20), (ex, ey - 1.5))
            c.put(g & erode4(body), ramp[1], 'flat', out=ramp.out)
    for (ex, ey) in ends[:4]:
        g = S.bez_line(c, (13.5 + (ex - 15.5) * 0.2, 11), (12 + (ex - 15.5) * 0.35, 16), (ex + 0.8, ey - 4))
        c.put(g & erode4(body), ramp[3], 'flat', out=ramp.out)
    c.pxs([(8, 26), (13, 28), (5, 22), (18, 28)], ramp[4])
    # straw tie + hanging loop
    tie = c.ellipse(15.5, 8.5, 5, 2.2)
    c.put(tie, R['straw'], 'ray', sep=True)
    c.put(c.rect(11, 8, 20, 8) & tie, R['straw'][1], 'flat', out=R['straw'].out)
    loop = c.ring(15.5, 4.5, 3.2, 1.2) & c.rect(0, 0, 31, 6)
    c.put(loop, R['straw'], 'flat', base=3)
    c.outline()
    return c


# ----------------------------------------------------------------------------- ginseng
def _ginseng(old):
    c = Canvas(32)
    root = R['wax']
    s = 1.12 if old else 1.0
    cx = 16.0
    top = 12.8 if old else 14.0

    def P(x, y):  # scale about the root top
        return (cx + (x - 16) * s, top + (y - 14) * s)

    # palmate leaves on two stalks + berry stalk (behind the root)
    for (ex, ey, fan) in ((8.5, 7.0, (95, 140, 185)), (23.5, 7.0, (85, 40, -5))):
        ex = cx + (ex - 16) * s
        stalk = c.seg(cx, top - 1, ex, ey, 1.2)
        c.put(stalk, R['leaf'][2], 'flat', out=R['leaf'].out)
        _leaves(c, [(ex, ey, a, 5.6, 3.3, 0.0) for a in fan], rib=False)
    stem = c.seg(cx, top + 1, cx, 5.0, 1.4)
    c.put(stem, R['leaf'][3], 'flat', out=R['leaf'].out)
    bx, by = cx, 4.6
    berries = c.circle(bx - 1.6, by, 1.7) | c.circle(bx + 1.6, by, 1.7) | c.circle(bx, by - 1.9, 1.7)
    c.put(berries, R['red'], 'sphere', sep=True)
    c.px(int(bx - 2), int(by - 1), R['red'][4])
    c.px(int(bx), int(by - 3), R['red'][4])

    # root body: rhizome neck, taproot, arms and legs
    neck = c.poly([P(14.2, 13), P(17.8, 13), P(18.6, 16), P(13.4, 16)])
    body = c.ellipse(*P(16, 19.5), 5.2 * s, 5.6 * s)
    armL = S.taper_curve(c, P(12.5, 17.5), P(9.5, 18), P(7.5, 21.5), 3.0 * s, 1.2)
    armR = S.taper_curve(c, P(19.5, 17.5), P(22.5, 18), P(24.5, 21), 3.0 * s, 1.2)
    legL = S.taper_curve(c, P(14.5, 23), P(12.5, 26.5), P(10, 29.5), 3.8 * s, 1.2)
    legR = S.taper_curve(c, P(17.5, 23), P(19.5, 26), P(21.5, 29), 3.8 * s, 1.2)
    mroot = neck | body | armL | armR | legL | legR
    c.put(mroot, root, 'ray', sep=True)
    # growth rings / wrinkles
    rings = []
    for yy in ((14, 15.5, 17.5) if not old else (13.8, 15.2, 16.6, 18.2, 20.6)):
        x0, y0 = P(13, yy)
        x1, y1 = P(19, yy + 0.6)
        rings.append(c.seg(x0, y0, x1, y1, 0.9))
    for m in rings:
        c.put(m & erode4(mroot), root[1], 'flat', out=root.out)
    # root hairs
    hair_col = R['gold'][3] if old else root[1]
    hairs = [((7.5, 21.5), (5.5, 23.5)), ((24.5, 21), (26.5, 23)), ((10, 29.5), (8, 29.3)),
             ((21.5, 29), (23.5, 29.3)), ((13, 22), (10.5, 23.5)), ((19, 22.5), (21.5, 24))]
    if old:
        hairs += [((8, 21), (5, 19.5)), ((24, 20.5), (27, 19)), ((11, 28), (8.5, 27)), ((20.5, 28), (23, 27))]
    for (a, b) in hairs:
        pa, pb = P(*a), P(*b)
        h = c.bres(int(pa[0]), int(pa[1]), int(pb[0]), int(pb[1])) & ~erode4(mroot)
        c.put(h, hair_col, 'flat', out=R['gold'].out if old else root.out)
    if old:
        S.sparkle(c, 26, 9, R['gold'][4], R['gold'][3], 2)
        S.sparkle(c, 5, 13, R['gold'][4], R['gold'][3], 1)
    c.outline()
    return c


# ----------------------------------------------------------------------------- ember pepper
def ember_pepper():
    c = Canvas(32)
    ramp = R['ember']
    # small back pepper (orange)
    back = S.taper_curve(c, (7.5, 12), (6, 22), (11.5, 28.5), 5.2, 1.4)
    c.put(back, R['fire'], 'ray')
    body = S.taper_curve(c, (13, 9.5), (25, 11), (24, 28.5), 8.0, 1.5)
    c.put(body, ramp, 'ray', sep=True)
    gloss = S.bez_line(c, (13, 8.5), (20.5, 9), (22, 17))
    c.put(gloss & erode4(body), ramp[4], 'flat', out=ramp.out)
    c.px(22, 18, ramp[3])
    # calyx caps and stems
    for (x, y, r) in ((11.5, 9.5, 3.2), (7.5, 11.2, 2.3)):
        cap = c.ellipse(x, y, r, r * 0.75)
        c.put(cap, R['leaf'], 'ray', sep=True)
    st = S.bez_line(c, (11, 8), (9, 4.5), (12.5, 3), 1.6)
    c.put(st, R['leaf'][3], 'flat', out=R['leaf'].out)
    st2 = S.bez_line(c, (7, 10), (5.5, 8), (6, 6.5))
    c.put(st2, R['leaf'][2], 'flat', out=R['leaf'].out)
    # ember wisps
    fl = S.flame(c, 26.5, 8.5, 4.2, 7.5, 0.6)
    c.put(fl, R['fire'], 'vgrad', base=3, bands=((0.35, 1), (0.75, 0), (9, -1)))
    c.outline()
    return c


# ----------------------------------------------------------------------------- mist lotus
def mist_lotus():
    c = Canvas(32)
    pad = c.ellipse(16, 24.5, 13, 3.6)
    c.put(pad, R['jade'], 'ray')
    c.put(c.bres(16, 24, 26, 24) & pad, R['jade'][1], 'flat', out=R['jade'].out)
    bx, by = 16, 22.5
    petals = [
        (bx - 1, by, 158, 11, 5.6, -0.12), (bx + 1, by, 22, 11, 5.6, 0.12),
        (bx - 1, by, 128, 12.5, 6.2, -0.06), (bx + 1, by, 52, 12.5, 6.2, 0.06),
        (bx, by + 0.5, 90, 15, 7.4, 0.0),
    ]
    pr = R['lotuspink']
    for (x, y, a, L, W, b) in petals:
        m = S.leaf(c, x, y, a, L, W, b, tip_power=0.7)
        c.put(m, pr, 'ray', base=3, sep=True, sep_col=pr[1])
        # rosy tip
        dx, dy = math.cos(math.radians(a)), -math.sin(math.radians(a))
        tip = c.circle(x + dx * L * 0.92, y + dy * L * 0.92, L * 0.28) & m
        c.put(tip, pr, 'ray', base=2, bands=((0.4, 0), (9, -1)))
    # seed-pod glow in the heart
    c.put(c.ellipse(16, 20.5, 2.6, 1.4), R['gold'], 'flat', base=3)
    c.pxs([(15, 20)], R['gold'][4])
    # mist drifting in front of the pad
    mist = R['mist']
    band = c.ellipse(8, 28, 6.5, 1.8) | c.ellipse(21, 28.5, 8, 1.8) | c.ellipse(26.5, 26.2, 3.5, 1.4)
    c.put(band, mist, 'ray', base=3, sep=True, sep_col=mist[1])
    c.outline()
    return c


def frost_lotus():
    """A lotus that blooms in snow: ice-blue petals on a drift, rime glittering at the tips."""
    c = Canvas(32)
    drift = c.ellipse(16, 25, 13, 3.8)
    c.put(drift, R['mist'], 'ray', base=3)
    bx, by = 16, 22.5
    petals = [(bx - 1, by, 158, 11, 5.6, -0.12), (bx + 1, by, 22, 11, 5.6, 0.12),
              (bx - 1, by, 128, 12.5, 6.2, -0.06), (bx + 1, by, 52, 12.5, 6.2, 0.06), (bx, by + 0.5, 90, 15, 7.4, 0.0)]
    pr = R['sky']
    for (x, y, a, L, W, b) in petals:
        m = S.leaf(c, x, y, a, L, W, b, tip_power=0.7)
        c.put(m, pr, 'ray', base=3, sep=True, sep_col=pr[1])
    c.put(c.ellipse(16, 20.5, 2.6, 1.4), R['gold'], 'flat', base=4)
    for (x, y) in ((7, 12), (25, 12), (16, 6)):
        c.pxs([(x, y)], '#FFFFFF')
    c.outline()
    c.glow('#BFE2FF', (60,))
    return c


# ----------------------------------------------------------------------------- cloudtop orchid
def _orchid(c, cx, cy, s):
    pet = R['cloud']
    parts = [(95, 6.0, 3.4), (200, 5.6, 3.4), (340, 5.6, 3.4), (150, 5.2, 4.0), (30, 5.2, 4.0)]
    for (a, L, W) in parts:
        m = S.leaf(c, cx, cy, a, L * s, W * s, 0.0, tip_power=0.9)
        c.put(m, pet, 'ray', base=3, sep=True, sep_col=R['sky'][1])
    lip = c.ellipse(cx, cy + 2.2 * s, 2.0 * s, 2.2 * s)
    c.put(lip, R['violet'], 'ray', base=2, sep=True)
    c.put(c.ellipse(cx, cy + 0.2, 1.1 * s, 1.0 * s), R['gold'], 'flat', base=3)


def cloudtop_orchid():
    c = Canvas(32)
    # strap leaves
    _leaves(c, [(11, 27, 118, 14, 3.6, 0.10), (13, 27, 62, 12, 3.4, -0.12), (11, 27, 158, 9, 3.2, 0.08)])
    stem = S.bez_line(c, (13, 26), (13, 10), (24, 7), 1.4)
    c.put(stem, R['leaf'][3], 'flat', out=R['leaf'].out)
    # the cloud the orchid grows on
    cl = (c.ellipse(9, 27.5, 6, 3.2) | c.ellipse(16, 26.2, 5.5, 3.8) | c.ellipse(23.5, 27.6, 6.5, 3.2)
          | c.ellipse(16, 29, 12.5, 1.8))
    c.put(cl, R['cloud'], 'ray', base=3, sep=True, sep_col=R['sky'][1])
    c.put(c.arc(16, 26.2, 5.5, 1, 200, 250) & cl, R['sky'][2], 'flat', out=R['sky'].out)
    _orchid(c, 21.5, 11.5, 1.22)
    _orchid(c, 10.5, 9.0, 0.82)
    bud = c.ellipse(24.5, 6.2, 1.6, 1.3)
    c.put(bud, R['cloud'], 'ray', base=3, sep=True)
    c.outline()
    return c


# ----------------------------------------------------------------------------- soulbell flower
def _bell(c, x, y, s):
    pts = [(-2.2, 0), (2.2, 0), (3.0, 3.2), (5.2, 7.0), (4.4, 8.0), (-4.4, 8.0), (-5.2, 7.0), (-3.0, 3.2)]
    m = c.poly([(x + px * s, y + py * s) for px, py in pts])
    c.put(m, R['violet'], 'ray', base=2, sep=True)
    # glowing mouth + clapper
    mouth = c.ellipse(x, y + 7.6 * s, 3.8 * s, 1.1 * s) & m
    c.put(mouth, R['qi'], 'flat', base=4)
    c.put(c.rect(int(x) - 1, int(y + 8 * s), int(x), int(y + 9.2 * s)), R['qi'], 'flat', base=3)
    # ribs
    c.put(c.bres(int(x - 1), int(y + 1), int(x - 3 * s), int(y + 6.5 * s)) & m, R['violet'][3], 'flat',
          out=R['violet'].out)
    cap = c.ellipse(x, y - 0.2, 2.6 * s, 1.3 * s)
    c.put(cap, R['leaf'], 'ray', base=2, sep=True)


def soulbell_flower():
    c = Canvas(32)
    _leaves(c, [(14, 30, 150, 10, 3.8, 0.1), (15, 30, 40, 10, 3.8, -0.1)])
    stem = S.bez_line(c, (15, 29), (12, 3), (24, 8), 1.4)
    stem |= S.bez_line(c, (14, 16), (11, 12), (7, 14), 1.2)
    c.put(stem, R['leaf'][3], 'flat', out=R['leaf'].out)
    _bell(c, 23.5, 9.5, 1.25)
    _bell(c, 7.5, 14.5, 0.95)
    for (x, y) in ((27, 24), (19, 25), (4, 26)):
        c.put(c.rect(x, y, x, y), R['qi'], 'flat', base=4)
    S.sparkle(c, 28, 21, R['qi'][4], R['qi'][3], 1)
    c.outline()
    return c


register(FAM, 'willow_moss', willow_moss, GROUP)
register(FAM, 'frost_lotus', frost_lotus, GROUP)
register(FAM, 'riverreed_ginseng_10', lambda: _ginseng(False), GROUP)
register(FAM, 'riverreed_ginseng_100', lambda: _ginseng(True), GROUP)
register(FAM, 'ember_pepper', ember_pepper, GROUP)
register(FAM, 'mist_lotus', mist_lotus, GROUP)
register(FAM, 'cloudtop_orchid', cloudtop_orchid, GROUP)
register(FAM, 'soulbell_flower', soulbell_flower, GROUP)
