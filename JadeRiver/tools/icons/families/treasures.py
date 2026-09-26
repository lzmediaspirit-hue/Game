"""Build Prompt v2 S44/S47: deployable treasures (bells, pagoda, mirror, seal, cauldron, banner,
sealing gourd), throwables, a talisman treasure, flight vessels, Heavenly Flames and the
furnace ladder. Same drawing model as the other families: one bold object, upper-left
light, automatic outline; glow only for qi-charged objects."""
import math

from pix import Canvas, Ramp
from palette import R
from registry import register
import shapes as S

FAM = 'items'


# ============================================================================ deployable treasures
def practice_bell():
    # A plain sect training bell: small iron body, red cord, no inlay.
    c = Canvas(32)
    ramp = R['iron']
    cord = c.poly([(14, 3), (18, 3), (18, 9), (14, 9)])
    c.put(cord, R['red'], 'flat', base=2)
    body = c.poly([(11, 9), (21, 9), (24, 23), (8, 23)]) | c.ellipse(16, 10, 5, 2.5)
    c.put(body, ramp, 'ray', base=2, sep=True)
    c.put(c.rect(7, 22, 25, 24), ramp, 'vgrad', base=3, sep=True)
    c.put(c.rect(10, 15, 22, 15) & body, ramp[4], 'flat', only_on=True)
    c.put(c.circle(16, 26, 1.6), ramp, 'sphere', sep=True)
    c.outline()
    return c


def bronze_bell():
    c = Canvas(32)
    ramp = R['bronze']
    loop = c.ring(16, 5.5, 3.0, 1.4)
    c.put(loop, ramp, 'flat', base=3)
    body = c.poly([(9, 9), (23, 9), (26, 25), (6, 25)]) | c.ellipse(16, 10, 7, 3)
    c.put(body, ramp, 'ray', base=2, sep=True)
    lip = c.rect(4, 24, 27, 26)
    c.put(lip, ramp, 'vgrad', base=3, sep=True)
    for y in (13, 18):
        c.put(c.rect(8, y, 24, y) & body, ramp[4], 'flat', only_on=True)
    for (x, y) in ((12, 15), (16, 15), (20, 15), (13, 20), (19, 20)):
        c.put(c.rect(x, y, x, y) & body, R['jade'][3], 'flat', only_on=True)
    c.put(c.circle(16, 28, 1.8), R['jade'], 'sphere', sep=True)
    c.outline()
    return c


def little_pagoda():
    c = Canvas(32)
    for i, (w, y) in enumerate(((11, 25), (9, 19), (7, 13), (5, 8))):
        roof = c.poly([(16 - w - 2, y), (16 + w + 2, y), (16 + w - 1, y - 2), (16 - w + 1, y - 2)])
        c.put(roof, R['jade'], 'vgrad', base=2, sep=True)
        wall = c.rect(16 - w + 2, y + 1, 16 + w - 2, y + 4 if i else y + 4)
        c.put(wall, R['red'], 'bevel', base=2, sep=True)
        c.put(c.rect(15, y + 2, 16, y + 4), R['gold'], 'flat', base=3)
    c.put(c.rect(15, 2, 16, 6), R['gold'], 'ray', base=3, sep=True)
    c.put(c.circle(15.5, 2.5, 1.2), R['gold'], 'sphere')
    c.put(c.rect(4, 29, 27, 30), R['stone'], 'flat', base=2, sep=True)
    c.outline()
    c.glow('#9FE8D8', (110, 45))
    return c


def bright_mirror():
    c = Canvas(32)
    rim = c.circle(15.5, 14.5, 11.5)
    c.put(rim, R['bronze'], 'sphere', base=2)
    face = c.circle(15.5, 14.5, 8.5)
    c.put(face, Ramp(['#16464F', '#2C7C86', '#62C0C4', '#B8EDEA', '#F4FFFF'], '#0B2129'), 'ray', base=2, sep=True)
    c.put(c.arc(15.5, 14.5, 6.0, 1.5, 120, 175), '#F4FFFF', 'flat')
    c.put(c.rect(11, 9, 12, 10), '#F4FFFF', 'flat')
    for a in range(0, 360, 45):
        x = 15.5 + math.cos(math.radians(a)) * 10.2
        y = 14.5 + math.sin(math.radians(a)) * 10.2
        c.put(c.rect(round(x), round(y), round(x), round(y)), R['gold'][4], 'flat', only_on=True)
    tassel = c.seg(15.5, 26, 15.5, 30, 1.6)
    c.put(tassel, R['red'], 'flat', base=2)
    c.put(c.circle(15.5, 26.5, 1.8), R['jade'], 'sphere', sep=True)
    c.outline()
    return c


def mountain_seal():
    c = Canvas(32)
    block = c.rect(6, 15, 25, 28)
    c.put(block, R['jade'], 'bevel', base=2)
    beast = c.ellipse(15.5, 11, 7, 4.5) | c.poly([(10, 14), (21, 14), (22, 16), (9, 16)])
    c.put(beast, R['jade'], 'sphere', base=3, sep=True)
    c.put(c.circle(12, 9, 1.5), R['jade'][4], 'flat')
    c.put(c.circle(19.5, 9.5, 1.2), R['deepjade'] if 'deepjade' in R else R['jade'][0], 'flat')
    # the carved face: a red square seal glyph
    face = c.rect(9, 19, 22, 26)
    c.put(face, R['red'], 'flat', base=2, sep=True)
    for (x0, y0, x1, y1) in ((11, 21, 20, 21), (11, 24, 20, 24), (15, 20, 16, 25)):
        c.put(c.rect(x0, y0, x1, y1), R['paper'][4], 'flat', only_on=True)
    c.outline()
    return c


def taming_cauldron():
    c = Canvas(32)
    ramp = R['iron']
    for x in (8, 23):
        c.put(c.poly([(x - 1.5, 23), (x + 1.5, 23), (x + 2, 29), (x - 2, 29)]), ramp, 'ray', base=1)
    body = c.ellipse(15.5, 18, 12, 9) & (c.Y > 11)
    c.put(body, ramp, 'sphere', base=2, cx=14, cy=15, rx=13, ry=11)
    rim = c.rect(4, 10, 27, 12)
    c.put(rim, R['bronze'], 'vgrad', base=3, sep=True)
    for x in (4.5, 26.5):
        c.put(c.ring(x, 8.0, 2.0, 1.0), R['bronze'], 'flat', base=2, sep=True)
    # a spirit beast's claw mark cast on the belly
    for dx in (-3, 0, 3):
        c.put(c.seg(15.5 + dx - 1.5, 15, 15.5 + dx + 1.5, 22, 1.1) & body, R['gold'][3], 'flat', only_on=True)
    mist = S.bez_line(c, (12, 9), (8, 5), (13, 2), 1.6) | S.bez_line(c, (19, 9), (24, 5), (19, 2), 1.6)
    c.put(mist & ~rim, R['qi'], 'flat', base=3)
    c.outline()
    return c


def wisp_banner():
    c = Canvas(32)
    pole = c.rect(7, 3, 8, 30)
    c.put(pole, R['darkwood'], 'across', base=2)
    c.put(c.circle(7.5, 3, 1.6), R['gold'], 'sphere', sep=True)
    cloth = c.poly([(9, 5), (26, 5), (26, 21), (21, 24), (17, 21), (13, 24), (9, 21)])
    c.put(cloth, R['indigo'], 'ray', base=2, sep=True)
    c.put(c.rect(9, 5, 26, 7), R['gold'], 'vgrad', base=3, sep=True)
    for (x, y) in ((14, 12), (20, 11), (17, 16)):
        c.put(c.circle(x, y, 1.8), R['qi'], 'sphere', only_on=True)
        c.put(c.rect(x, y - 1, x, y - 1), '#F2FFFF', 'flat', only_on=True)
    c.outline()
    c.glow('#8FE9FF', (100, 40))
    return c


def sealing_gourd():
    c = Canvas(32)
    body = R['violet'] if 'violet' in R else R['mistjade']
    low = c.circle(16, 21.5, 8.5)
    up = c.circle(16, 10.5, 5.5)
    c.put(low | up | c.rect(13, 13, 18, 16), body, 'sphere', base=2, cx=15, cy=17, rx=11, ry=15)
    c.put(low, body, 'sphere', base=2)
    c.put(up, body, 'sphere', base=2)
    c.put(c.rect(11, 14, 20, 15), R['gold'], 'vgrad', base=3, sep=True)
    c.put(c.rect(14, 3, 17, 6), R['gold'], 'ray', base=2, sep=True)
    # a paper seal pasted on its belly
    seal = c.rect(13, 18, 18, 26)
    c.put(seal, R['paper'], 'flat', base=3, sep=True)
    c.put(c.rect(15, 19, 16, 25), R['red'], 'flat', base=2)
    c.outline()
    c.glow('#C9A8FF', (110, 45))
    return c


# ============================================================================ throwables
def iron_needles():
    c = Canvas(32)
    for i, (x0, y0) in enumerate(((5, 26), (8, 27), (11, 28))):
        n = c.seg(x0, y0, x0 + 18, y0 - 18, 1.2)
        c.put(n, R['silver'], 'flat', base=4 if i == 1 else 3)
        c.put(c.rect(x0, y0, x0 + 1, y0), R['red'], 'flat', base=2)
    c.outline()
    return c


def flying_knives():
    c = Canvas(32)
    for i, (bx, by) in enumerate(((5, 25), (11, 27))):
        # a leaf-shaped throwing blade, a short wrapped grip and a red ring pommel
        blade = S.leaf(c, bx + 5, by - 5, 45, 15, 4.0, 0.0)
        c.put(blade, R['iron'], 'ray', base=2 + i, sep=True)
        c.put(S.midrib(c, bx + 5, by - 5, 45, 15, 0.0, 0.8) & blade, R['silver'][4], 'flat', only_on=True)
        grip = c.seg(bx + 1, by - 1, bx + 5, by - 5, 2.4)
        c.put(grip, R['leather'], 'across', base=2, sep=True)
        c.put(c.ring(bx, by, 1.9, 0.9), R['red'], 'flat', base=2, sep=True)
    c.outline()
    return c


def thunderclap_pellet():
    c = Canvas(32)
    ball = c.circle(15, 18, 9)
    c.put(ball, R['ink'], 'sphere', base=2)
    c.put(c.rect(7, 16, 23, 17) & ball, R['red'], 'flat', base=2, only_on=True)
    fuse = S.bez_line(c, (15, 9), (17, 5), (21, 4), 1.2)
    c.put(fuse, R['hemp'], 'flat', base=3)
    spark = S.star4(c, 22, 4, 2)
    c.put(spark, R['fire'], 'flat', base=4)
    bolt = c.poly([(13, 20), (16, 19), (15, 22), (18, 21), (14, 26), (15, 23), (12, 24)])
    c.put(bolt & ball, R['yellow'] if 'yellow' in R else R['gold'], 'flat', base=4, only_on=True)
    c.outline()
    return c


# ============================================================================ talisman treasure
def elder_hus_talisman():
    # Elder Hu's Heaven-Splitting Palm folded into paper: a red palm print on gold, glowing.
    c = Canvas(32)
    paper = c.poly([(9, 2), (23, 2), (23, 29), (9, 29)])
    c.put(paper, R['gold'], 'vgrad', base=3)
    c.put(c.rect(9, 2, 23, 4) | c.rect(9, 27, 23, 29), R['red'], 'flat', base=2, sep=True)
    palm = c.ellipse(16, 18, 4.2, 4.6)
    for fx, top in ((13, 8), (15, 7), (17, 7), (19, 8)):
        palm = palm | c.rect(fx - 0.6, top, fx + 0.6, 16)
    palm = palm | c.poly([(11.5, 15), (12.5, 14), (14, 18), (13, 19)])
    c.put(palm, R['red'], 'ray', base=3, sep=True)
    c.outline()
    c.glow('#FFE38A', (120, 50))
    return c


def lightning_rod_talisman():
    # A tribulation talisman: violet spirit paper, a copper rod, a bolt glyph.
    c = Canvas(32)
    paper = c.poly([(9, 3), (23, 3), (23, 29), (9, 29)])
    c.put(paper, R['sky'], 'vgrad', base=3)
    c.put(c.rect(9, 3, 23, 5) | c.rect(9, 27, 23, 29), R['bronze'], 'flat', base=2, sep=True)
    bolt = c.poly([(18, 7), (13, 16), (16.5, 16), (13, 25), (20, 13), (16.5, 13), (19.5, 7)])
    c.put(bolt, R['gold'], 'ray', base=4, sep=True)
    c.outline()
    c.glow('#BFE8FF', (110, 40))
    return c


# ============================================================================ flight vessels
def flying_sword_vessel():
    c = Canvas(32)
    blade = c.poly([(3, 23), (24, 9), (28, 7), (26, 11), (5, 25)])
    c.put(blade, R['cloudsteel'], 'ray', base=3)
    c.put(c.seg(5, 24, 26, 9, 0.8), '#F2FFFF', 'flat')
    guard = c.seg(6, 20, 10, 27, 2.2)
    c.put(guard, R['gold'], 'ray', base=3, sep=True)
    c.put(c.seg(3, 26, 6, 24, 2.2), R['darkwood'], 'flat', base=2, sep=True)
    for k in range(3):
        c.put(c.seg(10 + k * 5, 28 - k, 14 + k * 5, 28 - k, 1.0), R['qi'][3], 'flat')
    c.outline()
    c.glow('#9FE8FF', (110, 45))
    return c


def nine_sword_array():
    """Nine slim swords fanned up out of a red lacquered case."""
    c = Canvas(32)
    for k in range(5):
        x = 8.5 + k * 3.8
        tip = (x + (k - 2) * 1.6, 3.5 + abs(k - 2) * 1.6)
        b = c.poly([(x - 0.9, 20), (tip[0] - 0.9, tip[1] + 2.2), tip, (tip[0] + 0.9, tip[1] + 2.2), (x + 0.9, 20)])
        c.put(b, R['cloudsteel'], 'ray', base=3, sep=True)
        c.put(c.seg(x - 1.8, 19.5, x + 1.8, 19.5, 1.2), R['gold'], 'flat', base=3)
    case = S.rounded_rect(c, 5, 20, 26, 28, 2)
    c.put(case, R['red'], 'ray', base=2)
    c.put(c.seg(6, 21.2, 25, 21.2, 0.8), R['gold'], 'flat', base=4)
    c.put(S.diamond(c, 15.5, 24.8, 1.8, 1.8), R['gold'], 'flat', base=4)
    c.outline()
    c.glow('#9FE8FF', (110, 45))
    return c


def cloud_puff_vessel():
    c = Canvas(32)
    puff = c.circle(10, 19, 6) | c.circle(17, 15, 7.5) | c.circle(24, 19, 5.5) | c.rect(6, 19, 28, 24)
    c.put(puff, R['cloud'], 'sphere', base=3, cx=15, cy=13, rx=14, ry=10)
    c.put(c.arc(17, 15, 4.5, 1.2, 190, 260), '#FFFFFF', 'flat')
    for x in (9, 16, 23):
        c.put(c.ring(x, 22, 2.2, 0.8) & puff, R['sky'][2], 'flat', only_on=True)
    c.outline()
    return c


def jade_gourd_vessel():
    c = Canvas(32)
    low = c.ellipse(17, 20, 11, 6.5)
    up = c.ellipse(7.5, 15, 4.5, 4)
    c.put(low | up | c.rect(8, 15, 12, 19), R['jade'], 'sphere', base=2)
    c.put(low, R['jade'], 'sphere', base=2)
    c.put(c.rect(3, 13, 4, 17), R['gold'], 'flat', base=3, sep=True)
    c.put(c.rect(10, 16, 11, 22), R['gold'], 'vgrad', base=3, sep=True)
    c.put(c.circle(3, 15, 1.6), R['red'], 'sphere', sep=True)
    c.outline()
    c.glow('#9FE8D8', (100, 40))
    return c


def maple_leaf_vessel():
    c = Canvas(32)
    leaf = S.leaf(c, 5, 25, 35, 24, 11, 0.06)
    c.put(leaf, R['ember'] if 'ember' in R else R['red'], 'ray', base=2)
    rib = S.midrib(c, 5, 25, 35, 24, 0.06, 0.9)
    c.put(rib & leaf, R['gold'][3], 'flat', only_on=True)
    for t in (0.35, 0.6):
        x, y = 5 + 24 * t * math.cos(math.radians(35)), 25 - 24 * t * math.sin(math.radians(35))
        c.put(c.seg(x, y, x - 2, y - 5, 0.8) & leaf, R['gold'][3], 'flat', only_on=True)
        c.put(c.seg(x, y, x + 5, y + 2, 0.8) & leaf, R['gold'][3], 'flat', only_on=True)
    c.outline()
    return c


# ============================================================================ Heavenly Flames
def _flame(core, mid, outer, glow):
    def draw():
        c = Canvas(32)
        base = c.ellipse(16, 27, 8, 2.5)
        c.put(base, R['stone'], 'flat', base=1)
        f1 = S.flame(c, 16, 27, 11, 23, 0.1)
        c.put(f1, Ramp([outer[0], outer[1], mid[0], mid[1], core], outer[0]), 'vgrad', base=2)
        f2 = S.flame(c, 16, 27, 6, 14, -0.1)
        c.put(f2, Ramp([mid[0], mid[1], core, core, '#FFFFFF'], mid[0]), 'vgrad', base=3)
        c.outline()
        c.glow(glow, (130, 55))
        return c
    return draw


FLAMES = {
    'mist_lantern_flame': _flame('#F4FFF8', ('#9ED8C0', '#C8F0E0'), ('#3E7F6A', '#5FA88E'), '#BFEFD8'),
    'cold_lamp_flame': _flame('#EAF8FF', ('#57A8E8', '#8FD0FF'), ('#1D4F8F', '#2F78C4'), '#8FC8FF'),
    'sunscar_throne_ember': _flame('#FFF4C8', ('#F09A3A', '#FFC460'), ('#8F2A12', '#C8501E'), '#FFB25A'),
    'comet_tail_flame': _flame('#FFFFFF', ('#C8D4F0', '#EEF2FF'), ('#6E7BA8', '#98A6D4'), '#DCE6FF'),
}


# ============================================================================ furnaces
def _furnace(body_r, trim_r, jewel_r, legs=3, dragons=False):
    def draw():
        c = Canvas(32)
        xs = (8, 15.5, 23) if legs == 3 else (9, 22)
        for x in xs:
            c.put(c.poly([(x - 1.6, 22), (x + 1.6, 22), (x + 1.2, 29), (x - 1.2, 29)]), body_r, 'ray', base=1)
        body = (c.ellipse(15.5, 18, 11, 8) & (c.Y > 13)) | c.rect(5, 13, 26, 15)
        c.put(body, body_r, 'sphere', base=2, cx=15, cy=15, rx=12, ry=10, sep=True)
        for x in (3.5, 27.5):
            c.put(c.ring(x, 10.5, 2.4, 1.2), trim_r, 'flat', base=2, sep=True)
        c.put(c.rect(4, 11, 27, 13), trim_r, 'vgrad', base=3, sep=True)
        c.put(c.ellipse(15.5, 10, 7, 3) & (c.Y < 11), body_r, 'ray', base=3, sep=True)
        c.put(c.circle(15.5, 6, 1.8), jewel_r, 'sphere', sep=True)
        win = c.ellipse(15.5, 20, 3.5, 2.2)
        c.put(win, R['fire'], 'flat', base=3, sep=True)
        c.put(c.ellipse(15.5, 20.5, 1.8, 1), R['fire'], 'flat', base=4)
        if dragons:
            for sx in (-1, 1):
                d = S.bez_line(c, (15.5 + sx * 3, 23), (15.5 + sx * 11, 20), (15.5 + sx * 9, 14), 1.4)
                c.put(d & body, R['gold'], 'flat', base=4, only_on=True)
        c.outline()
        if dragons:
            c.glow('#FFD76A', (110, 45))
        return c
    return draw


FURNACES = {
    'earth_vein_furnace': _furnace(R['jadeiron'], R['jade'], R['jade']),
    'cloud_pattern_furnace': _furnace(R['cloudsteel'], R['silver'], R['sky']),
    'mystic_tripod': _furnace(R['mistjade'], R['gold'], R['gold'], legs=3),
    'nine_dragon_cauldron': _furnace(R['bronze'], R['gold'], R['red'], legs=3, dragons=True),
}

for _id, _fn in (('practice_bell', practice_bell), ('bronze_bell', bronze_bell), ('little_pagoda', little_pagoda), ('bright_mirror', bright_mirror),
                 ('mountain_seal', mountain_seal), ('taming_cauldron', taming_cauldron), ('wisp_banner', wisp_banner),
                 ('sealing_gourd', sealing_gourd), ('nine_sword_array', nine_sword_array)):
    register(FAM, _id, _fn, 'treasures')
for _id, _fn in (('iron_needles', iron_needles), ('flying_knives', flying_knives), ('thunderclap_pellet', thunderclap_pellet)):
    register(FAM, _id, _fn, 'throwables')
register(FAM, 'elder_hus_talisman', elder_hus_talisman, 'talismans')
register(FAM, 'lightning_rod_talisman', lightning_rod_talisman, 'talismans')
for _id, _fn in (('flying_sword_vessel', flying_sword_vessel), ('cloud_puff_vessel', cloud_puff_vessel),
                 ('jade_gourd_vessel', jade_gourd_vessel), ('maple_leaf_vessel', maple_leaf_vessel)):
    register(FAM, _id, _fn, 'vessels')
for _id, _fn in FLAMES.items():
    register(FAM, _id, _fn, 'flames')
for _id, _fn in FURNACES.items():
    register(FAM, _id, _fn, 'tools')
