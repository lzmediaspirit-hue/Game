"""Manuals, curios and workshop goods (appraisal, puppetry, research, formations).

Method manuals are thread-bound books: the cover colour and emblem name the
element. Technique manuals are tied scrolls with an element tag. Curios are small
antiques; the fake reads as glass (bubbles, a chip) beside the real carving.
"""
import math

from pix import Canvas, Ramp, dilate4, erode4, move
from palette import R
from registry import register
import shapes as S

FAM, GROUP = 'items', 'workshop'
INKC = '#2B2A30'


# ============================================================================ emblems
def _emblem(c, kind, cx, cy, clip):
    """A small element mark painted as a decal inside `clip`."""
    if kind == 'earth':
        m = c.poly([(cx - 4.5, cy + 3), (cx - 1, cy - 3.5), (cx + 1, cy - 0.5), (cx + 2.5, cy - 2.5), (cx + 5, cy + 3)])
        c.put(m & clip, R['gold'], 'ray', base=3)
    elif kind == 'wood':
        m = S.leaf(c, cx - 3, cy + 3, -50, 9, 4.2, 0.2)
        c.put(m & clip, R['leaf'], 'ray', base=3)
        c.put(S.midrib(c, cx - 3, cy + 3, -50, 9, 0.2) & m & clip, R['leaf'][1], 'flat')
    elif kind == 'fire':
        m = S.flame(c, cx, cy + 4, 7, 9)
        c.put(m & clip, R['ember'], 'ray', base=3)
        c.put(S.flame(c, cx, cy + 4, 3, 5) & m & clip, R['yellow'], 'flat', base=3)
    elif kind == 'water':
        for k, y in enumerate((cy - 2, cy + 1, cy + 4)):
            c.put(S.wave_line(c, int(cx - 4), int(cx + 4), int(y), 1, 5, phase=k) & clip, R['qi'], 'flat', base=3 if k else 4)
    elif kind == 'wind':
        c.put(c.arc(cx, cy, 3.5, 1.2, 180, 450) & clip, R['cloud'], 'flat', base=3)
        c.put(c.arc(cx + 1, cy + 1, 1.6, 1, 180, 400) & clip, R['cloud'], 'flat', base=4)
        c.put(c.seg(cx - 5, cy + 4, cx + 2, cy + 4, 1) & clip, R['cloud'], 'flat', base=3)
    elif kind == 'reed':
        for k, x in enumerate((cx - 3, cx, cx + 3)):
            c.put(c.seg(x, cy + 4, x + 1, cy - 3 + k, 1) & clip, R['bamboo'], 'flat', base=3)
            c.put(c.rect(int(x), int(cy - 4 + k), int(x) + 1, int(cy - 3 + k)) & clip, R['straw'], 'flat', base=3)


ELEMENT_COVER = {
    'earth': Ramp(['#2E2418', '#4C3B26', '#6E5738', '#94795A', '#BCA27E'], '#140F08'),
    'wood': Ramp(['#12301F', '#1C4A2E', '#2E6A40', '#4E9058', '#8CC47C'], '#07150C'),
    'fire': Ramp(['#3A1010', '#5E1A18', '#8A2A22', '#B8483A', '#E07E62'], '#1A0606'),
    'water': Ramp(['#0C1C30', '#15304C', '#1F4870', '#35699A', '#6C9CC8'], '#060C16'),
    'wind': Ramp(['#2A3848', '#44586C', '#667E92', '#8FA8BA', '#C4D6E2'], '#121A22'),
}


# ============================================================================ method manuals (bound books)
def bound_book(c, cover, emblem=None, torn=False, stain=False):
    x0, y0, x1, y1 = 7, 4, 24, 28
    pages = c.rect(x0 + 2, y0 + 2, x1 + 2, y1 + 1)
    if torn:
        pages &= ~c.poly([(x1 - 3, y1 + 2), (x1 + 3, y1 - 5), (x1 + 3, y1 + 2)])
    c.put(pages, R['paper'], 'hgrad', base=2)
    for y in range(y0 + 4, y1, 3):
        c.put(c.rect(x1 + 1, y, x1 + 2, y) & pages, R['paper'][1], 'flat')
    m = c.rect(x0, y0, x1, y1)
    if torn:
        m &= ~c.poly([(x1 - 6, y1 + 1), (x1 + 1, y1 - 7), (x1 + 1, y1 + 1)])
    c.put(m, cover, 'bevel', base=2, sep=True, hw=1, sw=1)
    # stitched spine: thread wraps every four pixels, a darker spine band
    c.put(c.rect(x0, y0, x0 + 2, y1) & m, cover, 'flat', base=1)
    for y in range(y0 + 2, y1, 4):
        c.put(c.rect(x0, y, x0 + 2, y) & m, R['paper'], 'flat', base=3)
    # title slip
    lab = c.rect(x1 - 6, y0 + 3, x1 - 3, y0 + 14)
    c.put(lab, R['paper'], 'bevel', base=3, sep=True, sep_col=cover[0])
    for y in range(y0 + 5, y0 + 13, 3):
        c.put(c.rect(x1 - 5, y, x1 - 4, y + 1), INKC, 'flat', only_on=True)
    if emblem:
        _emblem(c, emblem, 13.5, 20.5, erode4(m) & ~c.rect(x0, y0, x0 + 2, y1))
    if stain:
        st = c.ellipse(15, 19, 6, 5) & erode4(m)
        c.put(st & ~c.ellipse(15, 19, 4.5, 3.5), cover[3], 'flat')
        c.put(c.ellipse(19, 9, 3.5, 3) & lab, R['paper'][1], 'flat')
    return m


def _method_manual(element):
    def build():
        c = Canvas(32)
        bound_book(c, ELEMENT_COVER[element], element)
        c.outline()
        return c
    return build


def torn_manual():
    c = Canvas(32)
    faded = Ramp(['#3E3A30', '#5E5846', '#7E7660', '#9E967C', '#C2BA9E'], '#1A1812')
    bound_book(c, faded, None, torn=True, stain=True)
    c.outline()
    return c


# ============================================================================ technique manuals (tied scrolls)
def _technique_manual(element, paper=None, tie=None, stained=False):
    def build():
        c = Canvas(32)
        from families.misc import closed_scroll
        body, (mx, my) = closed_scroll(c, paper=paper, cap=R['darkwood'], tie=tie or R['red'], a=(5, 20), b=(22, 5), w=8.0)
        if stained:
            c.put(c.ellipse(11, 14, 3.5, 2.5) & erode4(body), R['mud'], 'flat', base=3)
        # hanging element tag
        tag = S.rounded_rect(c, 16, 17, 27, 29, 1)
        c.put(c.bres(int(mx) + 1, int(my) + 1, 20, 17), (tie or R['red']), 'flat', base=3)
        c.put(tag, R['talisman'], 'bevel', base=3, sep=True)
        _emblem(c, element, 21.5, 23, erode4(tag))
        c.outline()
        return c
    return build


# ============================================================================ curios
def dusty_curio():
    c = Canvas(32)
    legs = c.seg(10, 22, 8, 29, 2) | c.seg(22, 22, 24, 29, 2) | c.seg(16, 24, 16, 29, 2)
    c.put(legs, R['bronze'], 'ray', base=1)
    body = c.ellipse(16, 18, 10, 7.5)
    c.put(body, R['bronze'], 'sphere', base=2, sep=True)
    rim = c.rect(6, 10, 26, 12)
    c.put(rim, R['bronze'], 'ray', base=3, sep=True)
    for x in (8, 24):
        c.put(c.ring(x, 7, 2.4, 1.2) & (c.Y < 10), R['bronze'], 'flat', base=2)
    # a cast band of cloud scrolls, half hidden by grime
    c.put(S.wave_line(c, 8, 24, 17, 1, 6) & erode4(body), R['bronze'][1], 'flat')
    dust = Ramp(['#6A6458', '#8A8476', '#AAA496', '#C6C0B2', '#E0DACC'], '#2A2620')
    for (x, y, r) in ((11, 20, 2.5), (19, 22, 2.8), (23, 16, 1.8), (14, 14, 1.6)):
        c.put(c.circle(x, y, r) & erode4(body), dust, 'flat', base=1)
    c.put(c.rect(9, 11, 13, 11) | c.rect(18, 11, 21, 11), dust, 'flat', base=3, only_on=True)
    c.outline()
    return c


def _bi_disc(c, ramp, cx=16, cy=18, r=10.5, hole=3.6):
    disc = c.circle(cx, cy, r) & ~c.circle(cx, cy, hole)
    c.put(disc, ramp, 'sphere', base=2, cx=cx - 2, cy=cy - 2, rx=r + 2, ry=r + 2)
    return disc


def jade_trinket():
    c = Canvas(32)
    cord = c.ring(16, 5, 3, 1.1) & (c.Y < 8)
    c.put(cord, R['red'], 'flat', base=2)
    c.put(c.rect(15, 6, 16, 8), R['red'], 'flat', base=2)
    disc = _bi_disc(c, R['jade'])
    # carved grain: small raised dots in rings, like a grain-pattern bi
    for k in range(10):
        a = k * 2 * math.pi / 10
        x, y = 16 + 7.2 * math.cos(a), 18 + 7.2 * math.sin(a)
        c.put(c.rect(int(x), int(y), int(x), int(y)) & erode4(disc), R['jade'][4], 'flat')
    c.put(c.ring(16, 18, 5, 1) & disc, R['jade'][1], 'flat', out=R['jade'].out)
    c.put(c.ellipse(11, 12.5, 2, 1.2), R['jade'][4], 'flat')
    c.outline()
    c.glow('#67D6BD', (60,))
    return c


def fake_jade():
    c = Canvas(32)
    glass = Ramp(['#2E4A1A', '#4E7428', '#7AA83A', '#B2D86A', '#EAFFB8'], '#14200A')
    disc = _bi_disc(c, glass)
    # a chip out of the rim and bubbles trapped in the glass
    chip = c.poly([(24, 24), (28, 20), (29, 27)])
    c.erase(chip)
    disc &= ~chip
    for (x, y, r) in ((11, 20, 1.2), (19, 12, 1.0), (21, 21, 1.4), (13, 13, 0.8)):
        c.put(c.ring(x, y, r + 0.5, 0.8) & erode4(disc), glass[4], 'flat')
    c.put(c.bres_path([(8, 17), (11, 18), (12, 21)]) & erode4(disc), glass[0], 'flat')
    c.put(c.ellipse(11, 12.5, 2.2, 1.2), '#FFFFFF', 'flat')
    c.outline()
    return c


def _coin(c, cx, cy, r, ramp):
    m = c.circle(cx, cy, r)
    c.put(m, ramp, 'sphere', base=2, sep=True)
    c.put(S.outline_only(c.rect(int(cx) - 2, int(cy) - 2, int(cx) + 1, int(cy) + 1)), ramp[1], 'flat')
    c.put(c.ring(cx, cy, r - 1, 0.8) & m, ramp[3], 'flat')
    c.erase(c.rect(int(cx) - 1, int(cy) - 1, int(cx), int(cy)))
    return m


def string_of_old_coins():
    c = Canvas(32)
    string = c.seg(3, 28, 28, 3, 1.2)
    c.put(string, R['red'], 'flat', base=2)
    verdigris = Ramp(['#2A4A3E', '#3E6E5A', '#5E9A7E', '#8CC2A2', '#C8E8D2'], '#12201A')
    for k in range(4):
        x, y = 8 + k * 5.4, 23.5 - k * 5.4
        _coin(c, x, y, 5.2, verdigris if k == 2 else R['bronze'])
    c.put(c.circle(3, 28.5, 1.4) | c.circle(28.5, 3, 1.4), R['red'], 'sphere', base=2)
    c.outline()
    return c


# ============================================================================ puppetry and research
def spirit_wood():
    c = Canvas(32)
    pale = Ramp(['#5A4E3A', '#8C7C5E', '#BCAE8C', '#DCD2B4', '#F6F0DC'], '#26200F')
    log = c.poly([(9, 8), (27, 16), (22, 27), (4, 19)])
    c.put(log, pale, 'across', base=2)
    end = c.ellipse(6.5, 13.5, 4.5, 6)
    c.put(end, pale, 'flat', base=3, sep=True)
    for r in (3.2, 1.6):
        c.put(c.ring(6.5, 13.5, r, 0.8, ry=r * 1.3) & end, pale[1], 'flat')
    # Qi runs in the grain
    for k, (a, b) in enumerate((((11, 11), (25, 18)), ((9, 16), (23, 23)))):
        c.put(c.seg(a[0], a[1], b[0], b[1], 0.8) & erode4(log) & ~end, R['qi'], 'flat', base=3 + (k % 2))
    c.put(c.circle(6.5, 13.5, 0.8), R['qi'], 'flat', base=4)
    c.outline()
    c.glow('#8AEBEE', (60,))
    return c


def puppet_core():
    c = Canvas(32)
    frame = c.poly([(10, 4), (22, 4), (28, 10), (28, 22), (22, 28), (10, 28), (4, 22), (4, 10)])
    c.put(frame, R['darkwood'], 'ray', base=2)
    heart = c.circle(12.5, 13.5, 4.5) | c.circle(19.5, 13.5, 4.5) | c.poly([(8.2, 15.5), (23.8, 15.5), (16, 25)])
    c.put(heart, R['jade'], 'sphere', base=2, sep=True, cx=14, cy=14, rx=10, ry=10)
    c.put(c.bres_path([(12, 13), (16, 17), (20, 13)]) & erode4(heart), R['jade'][4], 'flat')
    for (x, y) in ((10, 6), (22, 6), (26, 16), (22, 26), (10, 26), (6, 16)):
        c.put(c.rect(x - 1 if x > 16 else x, y, x if x > 16 else x + 1, y), R['gold'], 'flat', base=3)
    c.outline()
    c.glow('#67D6BD', (70,))
    return c


def array_plate():
    c = Canvas(32)
    m = S.rounded_rect(c, 4, 6, 27, 27, 3)
    side = move(m, 0, 2) & ~m
    c.put(side | m, R['bronze'], 'flat', base=1)
    c.put(m, R['bronze'], 'ray', base=3)
    c.put(S.outline_only(S.rounded_rect(c, 6, 8, 25, 25, 2)), R['bronze'][1], 'flat', out=R['bronze'].out)
    # an engraved, lit protection array: ring, eight trigram bars, the centre point
    c.put(c.ring(15.5, 16.5, 7, 1), R['qi'], 'flat', base=3)
    for k in range(8):
        a = k * math.pi / 4
        x, y = 15.5 + 4.6 * math.cos(a), 16.5 + 4.6 * math.sin(a)
        c.put(c.seg(x - 1.2 * math.sin(a), y + 1.2 * math.cos(a), x + 1.2 * math.sin(a), y - 1.2 * math.cos(a), 0.9),
              R['qi'], 'flat', base=4 if k % 2 else 3)
    c.put(c.circle(15.5, 16.5, 1.2), R['gold'], 'flat', base=4)
    for (x, y) in ((8, 10), (23, 10), (8, 23), (23, 23)):
        c.put(c.rect(x, y, x, y), R['gold'], 'flat', base=3)
    c.outline()
    c.glow('#8AEBEE', (80,))
    return c


def sphere_comprehension_stone():
    c = Canvas(32)
    stand = c.poly([(9, 29), (11, 24), (21, 24), (23, 29)])
    c.put(stand, R['darkwood'], 'ray', base=2)
    orb = c.circle(16, 14, 10)
    c.put(orb, R['violet'], 'sphere', base=1, sep=True)
    # a folded world inside: a small ringed island and a spiral of stars
    c.put(c.ellipse(16, 17, 5, 1.6) & orb, R['jade'], 'flat', base=3)
    c.put(c.poly([(13, 17), (16, 12), (19, 17)]) & orb, R['stone'], 'ray', base=3)
    c.put(c.arc(16, 14, 7, 1, 200, 340) & orb, R['qi'], 'flat', base=4)
    for (x, y) in ((10, 11), (22, 12), (12, 20), (21, 19)):
        c.px(x, y, '#FFFFFF')
    c.put(c.ellipse(11.5, 8.5, 2.5, 1.5), R['violet'][4], 'flat')
    c.outline()
    c.glow('#B18DE2', (110, 45))
    return c


for _id, _fn in (('manual_stonebody_canon', _method_manual('earth')),
                 ('manual_willow_breath_art', _method_manual('wood')),
                 ('manual_emberheart_sutra', _method_manual('fire')),
                 ('manual_tidal_sovereign_scripture', _method_manual('water')),
                 ('manual_nine_winds_canon', _method_manual('wind')),
                 ('torn_manual', torn_manual),
                 ('mudwater_manual', _technique_manual('water', paper=Ramp(['#4E4636', '#7A6E56', '#A89A7C', '#C8BC9C', '#E6DCC0'], '#221E16'), tie=R['hemp'], stained=True)),
                 ('manual_rain_of_reeds', _technique_manual('reed', tie=R['jade'])),
                 ('manual_ember_burst', _technique_manual('fire', tie=R['gold'])),
                 ('dusty_curio', dusty_curio), ('jade_trinket', jade_trinket), ('fake_jade', fake_jade),
                 ('string_of_old_coins', string_of_old_coins), ('spirit_wood', spirit_wood),
                 ('puppet_core', puppet_core), ('array_plate', array_plate),
                 ('sphere_comprehension_stone', sphere_comprehension_stone)):
    register(FAM, _id, _fn, GROUP)
