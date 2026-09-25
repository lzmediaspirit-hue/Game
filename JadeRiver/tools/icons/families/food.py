"""Cooked food: bowl / plate / cup / pot / jar templates with contents and garnish."""
import math

from pix import Canvas, Ramp, dilate4, erode4, move
from palette import R
from registry import register
import shapes as S

FAM, GROUP = 'items', 'food'

CELADON = Ramp(['#2A4A40', '#487462', '#7EAA92', '#B6D8C0', '#E8F6EA'], '#0F1D18')
BLUEWARE = Ramp(['#3A4E66', '#6C84A0', '#C0D0DE', '#EAF0F4', '#FFFFFF'], '#141C26')


def steam(c, xs=(12, 17, 22), y0=10, h=7, col=None):
    col = col or R['mist']
    for k, x in enumerate(xs):
        pts = [(x + int(round(math.sin((y + k * 2) / 2.2))), y) for y in range(y0 - h, y0)]
        m = c.pts(pts)
        c.put(m & ~c.a, col, 'flat', base=4 if k % 2 == 0 else 3)


def bowl(c, ware=None, soup=None, cy=16, rx=13, depth=10, band=True):
    ware = ware or BLUEWARE
    body = c.ellipse(16, cy, rx, depth) & (c.Y >= cy)
    foot = c.rect(11, cy + depth - 1, 20, cy + depth + 1)
    c.put(foot, ware, 'ray', base=1)
    c.put(body, ware, 'sphere', base=2, cx=14, cy=cy, rx=rx + 2, ry=depth + 3, sep=True)
    if band:
        b = (c.ellipse(16, cy + 1, rx, depth - 4) & ~c.ellipse(16, cy + 1, rx, depth - 5.5)) & body & (c.Y > cy + 2)
        c.put(b, R['navy'] if ware is BLUEWARE else ware[1], 'flat', base=3 if ware is BLUEWARE else 0, out=ware.out)
    rim = c.ellipse(16, cy, rx, 3.6)
    c.put(rim, ware, 'flat', base=4, sep=True)
    inner = c.ellipse(16, cy + 0.3, rx - 1.5, 2.6)
    if soup is not None:
        c.put(inner, soup, 'ray', base=2)
        c.put(c.ellipse(16, cy - 0.6, rx - 1.5, 1.8) & inner, soup, 'flat', base=1)
    return inner


def plate(c, ware=None, cy=24, rx=14, ry=4.5):
    ware = ware or BLUEWARE
    under = c.ellipse(16, cy + 1.2, rx - 1, ry)
    c.put(under, ware, 'flat', base=1)
    top = c.ellipse(16, cy, rx, ry)
    c.put(top, ware, 'ray', base=3, sep=True)
    c.put(c.ellipse(16, cy, rx - 3, ry - 1.5), ware, 'flat', base=2)
    return top


def cup(c, ware=None, tea=None, x=14, y0=15, y1=26, w=11):
    ware = ware or CELADON
    body = c.poly([(x - w, y0), (x + w, y0), (x + w - 0.5, y0 + 4), (x + w - 2.5, y1 - 4), (x + w - 5.5, y1 - 1.5),
                   (x - w + 5.5, y1 - 1.5), (x - w + 2.5, y1 - 4), (x - w + 0.5, y0 + 4)])
    body |= c.rect(int(x - 4), y1 - 2, int(x + 3), y1)
    c.put(body, ware, 'ray', base=2)
    rim = c.ellipse(x, y0, w, 2.6)
    c.put(rim, ware, 'flat', base=4, sep=True)
    inner = c.ellipse(x, y0 + 0.3, w - 1.3, 1.8)
    c.put(inner, tea, 'flat', base=2)
    c.put(c.ellipse(x - 1.5, y0, w - 4, 0.9) & inner, tea, 'flat', base=3)
    return inner


# ============================================================================ recipes
def herbal_tea():
    c = Canvas(32)
    inner = cup(c, CELADON, R['tea'], x=16, y0=13, y1=27, w=13)
    lf = S.leaf(c, 12, 14.5, 10, 8, 3.2, 0.05)
    c.put(lf & inner, R['leaf'], 'ray', base=3)
    c.put(c.rect(7, 20, 25, 20) & c.a, CELADON[1], 'flat', only_on=True)
    steam(c, (11, 16, 21), 11, 7)
    c.outline()
    return c


def lotus_root_tea():
    c = Canvas(32)
    cup(c, CELADON, R['lotuspink'], x=14, y0=15, y1=28, w=12)
    c.put(c.rect(5, 21, 23, 21) & c.a, CELADON[1], 'flat', only_on=True)
    sl = c.circle(24.5, 11.5, 5.4)
    c.put(sl, R['wax'], 'ray', base=3, sep=True)
    for (dx, dy) in ((-2, -1.5), (1.5, -2), (2.2, 1.2), (-1.4, 2.2), (0, 0)):
        c.put(c.circle(24.5 + dx, 11.5 + dy, 0.9), R['wax'], 'flat', base=1)
    c.put(S.outline_only(sl), R['lotuspink'], 'flat', base=2)
    steam(c, (8, 13), 12, 6)
    c.outline()
    return c


def rice_ball():
    c = Canvas(32)
    plate(c, cy=25)
    ball = c.poly([(16, 4), (26, 22), (24, 25), (8, 25), (6, 22)])
    ball = ball & c.ellipse(16, 17, 12, 12) | c.ellipse(16, 21, 9.5, 4.5)
    c.put(ball, R['rice'], 'ray', base=3)
    for (x, y) in ((13, 10), (18, 13), (11, 16), (20, 18), (15, 15), (22, 21), (9, 21)):
        c.put(c.rect(x, y, x, y), R['rice'][1], 'flat', only_on=True)
    wrap = c.rect(10, 18, 22, 25) & ball
    c.put(wrap, Ramp(['#0A1A14', '#12281E', '#1E3C2C', '#2E5A40', '#4A7A58'], '#050D0A'), 'ray', base=2)
    for (x, y) in ((14, 20), (18, 22), (12, 23)):
        c.put(c.rect(x, y, x, y), R['straw'], 'flat', base=4, only_on=True)
    c.outline()
    return c


def toad_oil_dumplings():
    c = Canvas(32)
    plate(c, cy=24)
    for (x, y) in ((10, 19), (22, 19), (16, 22)):
        d = c.ellipse(x, y, 6, 4.5) & (c.Y < y + 2.5)
        d |= c.ellipse(x, y + 1.5, 6, 1.6)
        c.put(d, R['broth'], 'ray', base=3, sep=True)
        for k in (-3, 0, 3):
            c.put(c.rect(x + k, y - 4, x + k, y - 2) & d, R['broth'][1], 'flat', only_on=True)
        c.put(c.rect(x - 3, y - 3, x - 2, y - 3) & d, R['broth'][4], 'flat', only_on=True)
    c.put(c.ellipse(26, 25, 2, 1), R['oil'], 'flat', base=3)
    steam(c, (11, 21), 14, 6)
    c.outline()
    return c


def riverfish_soup():
    c = Canvas(32)
    inner = bowl(c, BLUEWARE, R['rice'])
    for (x, y) in ((11, 16), (19, 15)):
        s = c.ellipse(x, y, 3, 1.3) & inner
        c.put(s, R['pink'], 'flat', base=3)
    for (x, y) in ((15, 16), (22, 16), (8, 16), (17, 14)):
        c.put(c.rect(x, y, x, y) & inner, R['leaf'], 'flat', base=3)
    steam(c, (11, 16, 21), 12, 7)
    c.outline()
    return c


def boar_bone_broth():
    c = Canvas(32)
    bone = c.seg(18, 16, 26, 6, 2.8) | c.circle(25, 5.5, 1.9) | c.circle(27.5, 7.5, 1.9)
    c.put(bone, R['bone'], 'ray', base=3)
    inner = bowl(c, R['clay'], R['broth'], band=False)
    c.put(c.seg(18, 16, 20, 13.5, 2.8), R['bone'], 'ray', base=3)
    for (x, y) in ((10, 16), (13, 15), (22, 16)):
        c.put(c.rect(x, y, x, y) & inner, R['oil'], 'flat', base=4)
    c.put(c.rect(8, 16, 9, 16) & inner, R['leaf'], 'flat', base=3)
    steam(c, (8, 13), 12, 6)
    c.outline()
    return c


def ember_pepper_stew():
    c = Canvas(32)
    for x in (3.5, 28.5):
        c.put(c.ring(x, 16, 2.4, 1.2), R['darkwood'], 'flat', base=3)
    inner = bowl(c, R['darkwood'], R['ember'], cy=15, rx=13, depth=12, band=False)
    for (x, y, r) in ((10, 15, 2.2), (19, 14, 2.0), (15, 16, 1.6), (23, 16, 1.5)):
        c.put(c.circle(x, y, r) & inner, R['fire'] if r > 1.8 else R['leaf'], 'sphere', base=2)
    steam(c, (9, 15, 21), 11, 7, R['paper'])
    c.outline()
    return c


def ember_pepper_broth():
    c = Canvas(32)
    inner = bowl(c, BLUEWARE, R['fire'])
    for (x, y) in ((10, 16), (18, 15), (22, 16.5)):
        ring = c.ring(x, y, 1.9, 0.9) & inner
        c.put(ring, R['red'], 'flat', base=2)
    for (x, y) in ((14, 16), (7, 16)):
        c.put(c.rect(x, y, x, y) & inner, R['leaf'], 'flat', base=3)
    steam(c, (11, 16, 21), 12, 7, R['fire'])
    c.outline()
    return c


def cloudtop_orchid_broth():
    c = Canvas(32)
    inner = bowl(c, BLUEWARE, R['mist'])
    for a in (60, 150, 240, 330):
        p = S.leaf(c, 16, 15.5, a, 4.6, 3.2, 0)
        c.put(p & dilate4(inner), R['cloud'], 'ray', base=3, sep=True, sep_col=R['sky'][1])
    c.put(c.circle(16, 15.5, 1.3), R['violet'], 'flat', base=3)
    steam(c, (9, 23), 12, 6)
    c.outline()
    return c


def jade_carp_congee():
    c = Canvas(32)
    inner = bowl(c, CELADON, R['rice'])
    for (x, y) in ((11, 15.5), (18, 16), (22, 15)):
        c.put(c.ellipse(x, y, 2.6, 1.1) & inner, R['jade'], 'flat', base=3)
    for (x, y) in ((14, 15), (8, 16)):
        c.put(c.rect(x, y, x + 1, y) & inner, R['yellow'], 'flat', base=3)
    steam(c, (12, 18), 12, 7)
    c.outline()
    return c


def thunderhorn_stew():
    c = Canvas(32)
    for x in (3.5, 28.5):
        c.put(c.ring(x, 16, 2.4, 1.2), R['darkwood'], 'flat', base=3)
    inner = bowl(c, R['darkwood'], R['broth'], cy=15, rx=13, depth=12, band=False)
    for (x, y, r) in ((10, 15, 2.2), (17, 16, 2.0), (22, 14.5, 1.8)):
        c.put(c.circle(x, y, r) & inner, R['earth'], 'sphere', base=2)
    horn = c.poly([(12, 13), (15, 13), (20, 6), (21, 4), (18, 6)])
    c.put(horn, R['bone'], 'ray', base=3, sep=True)
    bolt = c.bres_path([(24, 4), (22, 8), (25, 9), (23, 13)])
    c.put(bolt, '#F4FBFF', 'flat')
    steam(c, (8, 26), 11, 6, R['paper'])
    c.outline()
    c.glow('#7FD4FF', (40,))
    return c


def roast_fish():
    c = Canvas(32)
    stick = c.seg(4, 29, 28, 4, 1.8)
    c.put(stick, R['bamboo'], 'flat', base=3)
    from families.fish import fish
    bm, F = fish(c, L=21, H=10, angle=46, cx=17, cy=15, body=R['broth'], belly=R['sand'], fin=R['earth'],
                 pattern=None, tail=5.5, low_fins=False)
    for k in range(-3, 3):
        x0, y0 = F.p(k * 3.2 + 1, 4)
        x1, y1 = F.p(k * 3.2 - 1, -4)
        c.put(c.seg(x0, y0, x1, y1, 1.0) & erode4(bm), R['earth'][0], 'flat', only_on=True)
    tip = c.seg(23, 9, 28, 4, 1.8) & ~bm
    c.put(tip, R['bamboo'], 'flat', base=3)
    c.outline()
    return c


def willow_salve():
    c = Canvas(32)
    lid = c.ellipse(26, 18, 3.2, 9)
    c.put(lid, R['bronze'], 'ray', base=2)
    c.put(c.ellipse(26.5, 18, 1.2, 5), R['bronze'], 'flat', base=4)
    body = c.ellipse(13, 22, 10.5, 6.5) & (c.Y > 19)
    body |= c.rect(3, 19, 23, 22)
    c.put(body, R['bronze'], 'sphere', base=2, cx=11, cy=19, rx=12, ry=9, sep=True)
    top = c.ellipse(13, 19, 10.5, 3.2)
    c.put(top, R['bronze'], 'flat', base=4, sep=True)
    salve = c.ellipse(13, 19.2, 9, 2.3)
    c.put(salve, R['moss'], 'ray', base=3)
    c.put(c.ellipse(10, 18.6, 3, 0.8) & salve, R['moss'][4], 'flat')
    c.put(c.rect(4, 24, 22, 24) & body, R['bronze'][1], 'flat', only_on=True)
    lf = S.leaf(c, 8, 27, 20, 8, 3, 0.1)
    c.put(lf & body, R['leaf'], 'flat', base=3, only_on=True)
    c.outline()
    return c


# ============================================================================ Act II · Sunscar Desert
CACTUS_WATER = Ramp(['#3A6A50', '#62987A', '#9ED0A8', '#CDEFCF', '#F2FFF2'], '#13261C')


def cactus_water():
    """A clay gourd of pale green cactus water, stopper pulled, an ember-cactus flower tied at its waist."""
    c = Canvas(32)
    clay = R['clay']
    low = c.circle(14.5, 22.5, 7.3)
    up = c.circle(14.5, 13.2, 4.2)
    waist = c.rect(12, 15, 17, 17)
    c.put(low, clay, 'sphere', base=2)
    c.put(up | waist, clay, 'sphere', base=2, cx=14, cy=12.5, rx=5, ry=5)
    neck = c.rect(12, 7, 16, 10)
    c.put(neck, clay, 'ray', base=2, sep=True)
    lip = c.ellipse(14, 6.5, 3.8, 1.9)
    c.put(lip, clay, 'ray', base=3, sep=True)
    mouth = c.ellipse(14, 6.4, 2.6, 1.2)
    c.put(mouth, CACTUS_WATER, 'flat', base=2)
    c.put(mouth & (c.X < 14) & (c.Y < 7), CACTUS_WATER, 'flat', base=4)
    # incised band on the lower bulb and glaze glints
    c.put(c.arc(14.5, 18, 7.3, 1.0, 200, 340) & erode4(low), clay[1], 'flat', out=clay.out)
    c.put(c.ellipse(11, 19.5, 1.8, 1.2) & low, clay[4], 'flat')
    c.put(c.ellipse(12.5, 11.5, 1.0, 0.8) & up, clay[4], 'flat')
    # the stopper, pulled out and leaning on the lip
    plug = c.seg(19, 6.5, 21.4, 3.6, 3.0)
    c.put(plug, R['wood'], 'ray', base=3, sep=True)
    # cord at the waist, its end hanging, and the flower tied into the knot
    cord = c.rect(10, 16, 18, 17) & dilate4(up | low | waist)
    c.put(cord, R['straw'], 'ray', base=2, sep=True)
    tail = S.bez_line(c, (19, 17), (22, 20), (21, 25))
    c.put(tail, R['straw'], 'flat', base=3, sep=True)
    fl = c.empty()
    for a in (20, 92, 164, 236, 308):
        fl |= S.leaf(c, 21, 15.5, a, 3.6, 2.6, 0.0, tip_power=0.8)
    c.put(fl, R['fire'], 'ray', base=3, sep=True, sep_col=R['fire'][1])
    c.put(c.rect(21, 15, 21, 15), R['yellow'][4], 'flat')
    c.outline()
    return c


for _id, _fn in (('herbal_tea', herbal_tea), ('rice_ball', rice_ball), ('riverfish_soup', riverfish_soup),
                 ('boar_bone_broth', boar_bone_broth), ('ember_pepper_stew', ember_pepper_stew),
                 ('lotus_root_tea', lotus_root_tea), ('toad_oil_dumplings', toad_oil_dumplings),
                 ('cloudtop_orchid_broth', cloudtop_orchid_broth), ('jade_carp_congee', jade_carp_congee),
                 ('roast_fish', roast_fish), ('ember_pepper_broth', ember_pepper_broth),
                 ('willow_salve', willow_salve), ('thunderhorn_stew', thunderhorn_stew),
                 ('cactus_water', cactus_water)):
    register(FAM, _id, _fn, GROUP)
