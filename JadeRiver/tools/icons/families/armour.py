"""Armour slot silhouettes (hat, robe, trousers, footwear, cape) with grade palettes,
the soul talisman, and calabash gourds.

Grade palettes: Plain (hemp/straw), Common (iron-grey cotton), Earth (dark jade
cloth + jadeiron plates + jade trim), Heaven (pale-blue cloudsilk + silver trim +
cloud embroidery), Mystic (mistjade violet + gold trim + faint glow).
"""
from pix import Canvas, Ramp, dilate4, erode4, move
from palette import R
from registry import register
import shapes as S

FAM = 'equipment'

COTTON = Ramp(['#23282E', '#3C444D', '#606B76', '#8E99A2', '#C3CBD0'], '#0D1013')

CLOTH = {
    'plain': dict(cloth=R['hemp'], trim=R['straw'], sash=R['straw'], plate=None, gem=None, glow=None),
    'common': dict(cloth=COTTON, trim=R['ink'], sash=R['ink'], plate=None, gem=None, glow=None),
    'earth': dict(cloth=R['deepjade'], trim=R['jade'], sash=R['bronze'], plate=R['jadeiron'], gem=R['jade'],
                  glow=None),
    'heaven': dict(cloth=R['sky'], trim=R['cloud'], sash=R['silk_navy'], plate=None, gem=R['qi'], glow=None),
    'mystic': dict(cloth=R['mistjade'], trim=R['gold'], sash=R['plum'], plate=None, gem=R['violet'],
                   glow='#B18DE2'),
    'spirit': dict(cloth=R['storm'], trim=R['silver'], sash=R['navy'], plate=None, gem=R['cyan'], glow='#7FD4FF'),
    'sage': dict(cloth=R['sand'], trim=R['gold'], sash=R['red'], plate=None, gem=R['ember'], glow='#FFC870'),
}


def finish(c, grade):
    c.outline()
    if CLOTH[grade]['glow']:
        c.glow(CLOTH[grade]['glow'], (95, 40))
    return c


def cloud_curl(c, x, y, col, clip=None):
    m = c.rect(x, y, x + 2, y) | c.rect(x + 2, y - 1, x + 2, y - 1) | c.rect(x + 1, y - 2, x + 1, y - 2) | \
        c.rect(x + 3, y, x + 4, y)
    if clip is not None:
        m &= clip
    c.put(m, col, 'flat', only_on=True)


# ============================================================================ robes
def robe(grade):
    P = CLOTH[grade]
    c = Canvas(32)
    cl, tr = P['cloth'], P['trim']
    body = c.poly([(10, 4), (22, 4), (23, 14), (26, 29), (6, 29), (9, 14)])
    sl = c.poly([(10, 5), (4, 8), (1.5, 22), (8.5, 23), (10, 14)])
    sr = c.poly([(22, 5), (28, 8), (30.5, 22), (23.5, 23), (22, 14)])
    c.put(sl, cl, 'ray', base=1)
    c.put(sr, cl, 'ray', base=1)
    c.put(body, cl, 'ray', base=2, sep=True)
    for s in (sl, sr):
        cuff = s & (c.Y > 19.5)
        c.put(cuff, tr, 'flat', base=2)
    # inner collar + crossed lapels
    c.put(c.poly([(13, 4), (19, 4), (16, 9)]), R['paper'], 'flat', base=3)
    lap = c.polyline([(12.5, 4.5), (19.5, 14.5)], 2.4)
    lap2 = c.polyline([(19.5, 4.5), (16.5, 8.5)], 2.2)
    c.put(lap2, tr, 'flat', base=2)
    c.put(lap, tr, 'flat', base=3, sep=True)
    # sash + hanging tie
    sash = c.rect(9, 14, 23, 16) & body
    c.put(sash, P['sash'], 'vgrad', base=2, sep=True)
    tie = c.rect(12, 17, 12, 22) | c.rect(14, 17, 14, 21)
    c.put(tie, P['sash'], 'flat', base=3)
    hem = body & (c.Y > 27)
    c.put(hem, tr, 'flat', base=2)
    if P['plate'] is not None:
        for (x0, x1) in ((3, 9), (23, 29)):
            pad = S.rounded_rect(c, x0, 6, x1, 11, 2)
            c.put(pad, P['plate'], 'bevel', base=2, sep=True)
            c.put(c.rect(x0 + 1, 8, x1 - 1, 8) & pad, P['plate'][1], 'flat', only_on=True)
        chest = c.rect(10, 9, 21, 13) & body
        c.put(chest & ((c.yi % 2 == 0)), P['plate'][3], 'flat', only_on=True)
    if P['gem'] is not None:
        c.put(S.diamond(c, 16, 15.5, 1.8, 1.8), P['gem'], 'ray', base=3, sep=True)
    if grade == 'heaven':
        for (x, y) in ((9, 26), (18, 25), (3, 18), (25, 18)):
            cloud_curl(c, x, y, R['cloud'][4])
    if grade == 'mystic':
        for x in (8, 23):
            c.put(c.rect(x, 18, x, 26) & body, R['gold'], 'flat', base=3)
    return finish(c, grade)


# ============================================================================ trousers
def trousers(grade):
    P = CLOTH[grade]
    c = Canvas(32)
    cl, tr = P['cloth'], P['trim']
    legL = c.poly([(8, 7), (16, 7), (15.5, 13), (15, 28), (6, 28), (6.5, 13)])
    legR = c.poly([(16, 7), (24, 7), (25.5, 13), (26, 28), (17, 28), (16.5, 13)])
    c.put(legL, cl, 'ray', base=2)
    c.put(legR, cl, 'ray', base=2, sep=True)
    for (x0, x1) in ((6, 15), (17, 26)):
        cuff = c.rect(x0, 23, x1, 25) & (legL | legR)
        c.put(cuff, tr, 'vgrad', base=2)
    band = c.rect(7, 3, 25, 7)
    c.put(band, tr, 'vgrad', base=3, sep=True)
    ties = c.bres(14, 7, 12, 12) | c.bres(17, 7, 19, 12)
    c.put(ties, P['sash'], 'flat', base=3)
    for x in (10, 21):
        c.put(c.bres(x, 9, x - 1 if x < 16 else x + 1, 21) & (legL | legR), cl[1], 'flat', only_on=True)
    if P['plate'] is not None:
        for (x0, x1) in ((7, 14), (18, 25)):
            gr = S.rounded_rect(c, x0, 14, x1, 21, 2)
            c.put(gr, P['plate'], 'bevel', base=2, sep=True)
            c.put(c.rect(x0 + 1, 17, x1 - 1, 17) & gr, P['plate'][1], 'flat', only_on=True)
    if P['gem'] is not None:
        c.put(c.rect(15, 4, 16, 5), P['gem'], 'flat', base=4)
    if grade == 'heaven':
        for (x, y) in ((8, 20), (19, 20)):
            cloud_curl(c, x, y, R['cloud'][4])
    return finish(c, grade)


# ============================================================================ footwear
def _boot(c, dx, dy, cl, sole, tr, base=2):
    shaft = c.poly([(8 + dx, 5 + dy), (17 + dx, 5 + dy), (17 + dx, 18 + dy), (8 + dx, 21 + dy)])
    foot = c.poly([(8 + dx, 19 + dy), (17 + dx, 16 + dy), (24 + dx, 19 + dy), (26.5 + dx, 23 + dy), (8 + dx, 24 + dy)])
    m = shaft | foot
    c.put(m, cl, 'ray', base=base, sep=True)
    c.put(c.rect(8 + dx, 5 + dy, 17 + dx, 7 + dy) & m, tr, 'vgrad', base=base + 1)
    so = c.poly([(7 + dx, 23 + dy), (27 + dx, 22 + dy), (27.5 + dx, 25 + dy), (7 + dx, 25.5 + dy)])
    c.put(so, sole, 'flat', base=3, sep=True)
    return m


def boots(grade):
    P = CLOTH[grade]
    c = Canvas(32)
    cl, tr = P['cloth'], P['trim']
    sole = R['paper'] if grade in ('common', 'heaven') else R['leather'] if grade == 'earth' else R['gold'] \
        if grade == 'mystic' else R['silver'] if grade == 'spirit' else R['clay'] if grade == 'sage' else R['hemp']
    _boot(c, -4, -2, cl, sole, tr, base=1)
    m = _boot(c, 1, 3, cl, sole, tr, base=2)
    if P['plate'] is not None:
        gr = S.rounded_rect(c, 10, 12, 17, 21, 2)
        c.put(gr, P['plate'], 'bevel', base=2, sep=True)
        c.put(c.rect(11, 16, 16, 16) & gr, P['plate'][1], 'flat', only_on=True)
    if P['gem'] is not None:
        c.put(S.diamond(c, 13.5, 11, 1.6, 1.6), P['gem'], 'ray', base=3, sep=True)
    if grade == 'heaven':
        cloud_curl(c, 19, 22, R['cloud'][4])
    if grade == 'mystic':
        c.put(c.rect(10, 18, 18, 18) & m, R['gold'], 'flat', base=3, only_on=True)
    return finish(c, grade)


def straw_sandals():
    c = Canvas(32)
    for (dx, dy, base) in ((-4, -4, 1), (3, 3, 2)):
        sole = c.ellipse(15 + dx, 16 + dy, 5.5, 11)
        c.put(sole, R['straw'], 'ray', base=base + 1, sep=True)
        for y in range(6 + dy, 27 + dy, 2):
            c.put(c.rect(10 + dx, y, 20 + dx, y) & erode4(sole), R['straw'][1], 'flat', only_on=True)
        strap = c.polyline([(10 + dx, 13 + dy), (15 + dx, 9 + dy), (20 + dx, 13 + dy)], 1.6)
        strap |= c.seg(15 + dx, 9 + dy, 15 + dx, 6 + dy, 1.4)
        c.put(strap, R['hemp'], 'flat', base=2, sep=True)
        heel = c.polyline([(10 + dx, 21 + dy), (15 + dx, 24 + dy), (20 + dx, 21 + dy)], 1.4)
        c.put(heel, R['hemp'], 'flat', base=2, sep=True)
    c.outline()
    return c


# ============================================================================ hats
def plain_straw_hat():
    c = Canvas(32)
    under = c.ellipse(16, 22, 14.5, 3)
    c.put(under, R['straw'], 'flat', base=1)
    cone = c.poly([(1, 22), (16, 6), (31, 22)]) | c.ellipse(16, 21, 15, 2.2)
    c.put(cone, R['straw'], 'ray', base=3, sep=True)
    for k in range(-5, 6):
        ln = c.bres(16, 7, 16 + k * 3, 22)
        c.put(ln & erode4(cone), R['straw'][1] if k % 2 else R['straw'][2], 'flat', only_on=True)
    top = c.circle(16, 6.5, 1.8)
    c.put(top, R['straw'], 'flat', base=2, sep=True)
    cord = S.bez_line(c, (9, 23), (12, 29), (16, 30)) | S.bez_line(c, (23, 23), (20, 29), (16, 30))
    c.put(cord & ~cone, R['hemp'], 'flat', base=2)
    c.outline()
    return c


def bamboo_hat():
    c = Canvas(32)
    ramp = R['sand']
    under = c.ellipse(16, 21.5, 14, 3)
    c.put(under, ramp, 'flat', base=1)
    cone = c.poly([(2, 21), (13, 7), (19, 7), (30, 21)]) | c.ellipse(16, 20.5, 14.5, 2.4)
    c.put(cone, ramp, 'ray', base=3, sep=True)
    for y in range(9, 21, 2):
        c.put(c.rect(0, y, 31, y) & erode4(cone) & ((c.xi + y // 2) % 3 != 0), ramp[1], 'flat', only_on=True)
    crown = c.rect(12, 5, 20, 8) | c.ellipse(16, 5, 4, 1.5)
    c.put(crown, ramp, 'ray', base=2, sep=True)
    band = c.poly([(10, 11), (22, 11), (23.5, 13), (8.5, 13)])
    c.put(band, COTTON, 'flat', base=1)
    c.put(c.rect(9, 13, 23, 13) & band, COTTON, 'flat', base=0)
    cord = S.bez_line(c, (8, 22), (12, 29), (16, 30)) | S.bez_line(c, (24, 22), (20, 29), (16, 30))
    c.put(cord & ~cone, R['ink'], 'flat', base=3)
    c.outline()
    return c


def jadeiron_hat():
    c = Canvas(32)
    P = CLOTH['earth']
    neck = c.poly([(6, 17), (26, 17), (27, 25), (22, 27), (10, 27), (5, 25)])
    c.put(neck, P['cloth'], 'ray', base=2)
    for x in range(8, 26, 3):
        c.put(c.rect(x, 18, x, 26) & neck, P['cloth'][1], 'flat', only_on=True)
    dome = c.ellipse(16, 17, 10.5, 11) & (c.Y < 18)
    c.put(dome, P['plate'], 'sphere', base=2, cx=15, cy=15, rx=12, ry=12, sep=True)
    brim = c.rect(4, 16, 27, 18)
    c.put(brim, R['jade'], 'vgrad', base=3, sep=True)
    c.put(c.rect(15, 7, 16, 16) & dome, R['jade'], 'flat', base=3)
    gem = S.diamond(c, 16, 12.5, 2.4, 2.8)
    c.put(gem, R['jade'], 'ray', base=3, sep=True)
    tuft = S.flame(c, 16, 7, 5, 7, 0.8)
    c.put(tuft, R['red'], 'vgrad', base=2, sep=True)
    c.outline()
    return c


def cloudsilk_hat():
    c = Canvas(32)
    veil = c.poly([(4, 18), (28, 18), (29.5, 26), (2.5, 26)])
    for x in range(3, 30):
        if (x // 3) % 2 == 0:
            veil |= c.rect(x, 26, x, 27)
    c.put(veil, R['sky'], 'vgrad', base=3, bands=((0.3, 1), (0.8, 0), (9, -1)))
    for x in range(6, 28, 4):
        c.put(c.rect(x, 19, x, 26) & veil, R['sky'][2], 'flat', only_on=True)
    cone = c.poly([(1, 18), (16, 5), (31, 18)]) | c.ellipse(16, 17.5, 15, 2.2)
    c.put(cone, R['cloud'], 'ray', base=3, sep=True)
    rim = c.ellipse(16, 17.5, 15, 2.2) & ~c.ellipse(16, 16.5, 15, 2.2)
    c.put(rim, R['silver'], 'flat', base=2)
    for (x, y) in ((8, 15), (17, 12), (21, 16)):
        cloud_curl(c, x, y, R['sky'][2])
    c.put(c.circle(16, 5, 1.6), R['qi'], 'sphere', sep=True)
    c.outline()
    return c

def stormsilk_hat():
    """Spirit grade: a silver crown with a lightning crest and a cyan spark stone."""
    c = Canvas(32)
    bun = c.ellipse(16, 20, 8, 6)
    c.put(bun, R['ink'], 'ray', base=3)
    crown = c.poly([(8, 22), (8, 14), (12, 11), (14, 5), (16, 12), (18, 5), (20, 11), (24, 14), (24, 22)])
    c.put(crown, R['storm'], 'ray', base=2, sep=True)
    c.put(c.rect(8, 19, 24, 22), R['silver'], 'vgrad', base=3, sep=True)
    gem = S.diamond(c, 16, 15, 2.4, 3)
    c.put(gem, R['cyan'], 'ray', base=4, sep=True)
    pin = c.seg(1.5, 17.5, 30, 15, 1.6)
    c.put(pin & ~c.rect(9, 13, 23, 22), R['silver'], 'flat', base=3)
    c.outline()
    c.glow('#7FD4FF', (95, 40))
    return c


def sunsilk_hat():
    """Sage grade: a black lacquered hat with a gold band and a sheer sunsilk veil to the shoulders."""
    c = Canvas(32)
    veil = c.poly([(4, 15), (28, 15), (27, 29), (5, 29)])
    c.put(veil, R['sand'], 'vgrad', base=3)
    for x in (8, 13, 19, 24):
        c.put(c.rect(x, 17, x, 28) & veil, R['sand'][2], 'flat', only_on=True)
    crown = c.ellipse(16, 11, 6.5, 5) & (c.Y < 14)
    c.put(crown, R['ink'], 'ray', base=2, sep=True)
    brim = c.ellipse(16, 14, 13, 2.4)
    c.put(brim, R['ink'], 'hgrad', base=2, sep=True)
    c.put(c.rect(10, 11, 22, 12) & crown, R['gold'], 'flat', base=3)
    c.put(S.diamond(c, 16, 9, 1.6, 2), R['ember'], 'ray', base=4, sep=True)
    c.outline()
    c.glow('#FFC870', (80, 30))
    return c


def mistjade_hat():
    c = Canvas(32)
    bun = c.ellipse(16, 20, 8, 6)
    c.put(bun, R['ink'], 'ray', base=3)
    crown = c.poly([(8, 22), (8, 13), (11, 9), (13, 13), (16, 6), (19, 13), (21, 9), (24, 13), (24, 22)])
    c.put(crown, R['mistjade'], 'ray', base=2, sep=True)
    c.put(c.rect(8, 19, 24, 22), R['gold'], 'vgrad', base=3, sep=True)
    for (x, y) in ((11, 11), (21, 11)):
        c.put(c.circle(x + 0.5, y + 0.5, 1.2), R['gold'], 'flat', base=4)
    gem = S.diamond(c, 16, 14, 2.4, 3)
    c.put(gem, R['violet'], 'ray', base=4, sep=True)
    pin = c.seg(1.5, 17.5, 30, 15, 1.6)
    c.put(pin & ~c.rect(9, 13, 23, 22), R['gold'], 'flat', base=3)
    c.put(c.circle(2.5, 17.5, 1.8), R['jade'], 'sphere', sep=True)
    c.outline()
    c.glow('#B18DE2', (95, 40))
    return c


# ============================================================================ cape + talisman
def mistjade_cape():
    c = Canvas(32)
    ramp = R['mistjade']
    body = c.poly([(8, 4), (16, 6), (23, 5), (29, 9), (30, 17), (27, 24), (23, 29), (15, 28), (8, 30), (5, 22),
                   (6, 12)])
    c.put(body, ramp, 'ray', base=2)
    lining = c.poly([(23, 5), (29, 9), (30, 17), (27, 24), (24, 15), (23, 9)])
    c.put(lining & body, R['plum'], 'ray', base=2, sep=True)
    for (a, b) in (((9, 8), (8, 28)), ((13, 8), (14, 27)), ((18, 8), (20, 27))):
        c.put(S.bez_line(c, a, ((a[0] + b[0]) / 2 + 2, (a[1] + b[1]) / 2), b) & erode4(body) & ~lining,
              ramp[1], 'flat', only_on=True)
    c.put(S.bez_line(c, (10, 7), (9, 16), (7, 26)) & erode4(body), ramp[3], 'flat', only_on=True)
    trim = (S.outline_only(body) & (c.Y > 26)) | (S.outline_only(lining) & body)
    c.put(trim, R['gold'], 'flat', base=3)
    collar = c.poly([(5, 3), (13, 4), (12, 8), (6, 7)])
    c.put(collar, R['plum'], 'ray', base=3, sep=True)
    clasp = c.circle(10, 6, 2.4)
    c.put(clasp, R['gold'], 'sphere', sep=True)
    c.put(c.rect(10, 6, 10, 6), R['violet'], 'flat', base=4)
    c.outline()
    c.glow('#B18DE2', (95, 40))
    return c

def cloud_talisman():
    c = Canvas(32)
    paper = c.poly([(10, 8), (22, 8), (21, 29), (11, 29)])
    c.put(paper, R['paper'], 'bevel', base=3)
    for y in (10, 27):
        c.put(c.rect(11, y, 20, y) & paper, R['qi'], 'flat', base=1)
    script = c.rect(15, 12, 16, 22) | c.bres(12, 14, 15, 16) | c.bres(19, 14, 16, 16) | c.rect(12, 19, 19, 19)
    c.put(script & paper, R['navy'], 'flat', base=2)
    seal = S.rounded_rect(c, 13, 22, 18, 26, 1)
    c.put(seal, R['seal'], 'flat', base=2)
    c.put(c.rect(15, 23, 16, 25) | c.rect(14, 24, 17, 24), R['seal'], 'flat', base=4)
    clip = S.rounded_rect(c, 9, 3, 23, 9, 2)
    c.put(clip, R['jade'], 'ray', base=3, sep=True)
    c.put(c.rect(11, 6, 21, 6) & clip, R['jade'][1], 'flat', only_on=True)
    c.put(c.circle(16, 5.5, 1.3), R['gold'], 'flat', base=3)
    c.outline()
    c.glow('#8AEBEE', (70,))
    return c


# ============================================================================ gourds
def gourd(kind):
    c = Canvas(32)
    body = {'starter': R['straw'], 'bamboo': R['bamboo'], 'jadeiron': R['jadeiron'], 'cloud': R['porcelain'],
            'mistjade': R['mistjade'], 'stormsteel': R['storm'], 'sunsteel': R['gold']}[kind]
    band_r = {'starter': R['hemp'], 'bamboo': R['bamboo'], 'jadeiron': R['iron'], 'cloud': R['sky'],
              'mistjade': R['gold'], 'stormsteel': R['silver'], 'sunsteel': R['red']}[kind]
    stop = {'starter': R['wood'], 'bamboo': R['wood'], 'jadeiron': R['jade'], 'cloud': R['silver'],
            'mistjade': R['gold'], 'stormsteel': R['cyan'], 'sunsteel': R['jade']}[kind]
    low = c.circle(16, 21.5, 8.5)
    up = c.circle(16, 10.5, 5.5)
    waist = c.rect(13, 13, 18, 16)
    m = low | up | waist
    c.put(m, body, 'sphere', base=2, cx=15, cy=17, rx=11, ry=15)
    # re-shade the two bulbs individually for roundness
    c.put(low, body, 'sphere', base=2)
    c.put(up, body, 'sphere', base=2)
    neck = c.rect(14, 3, 17, 6)
    c.put(neck, stop, 'ray', base=2, sep=True)
    c.put(c.rect(13, 2, 18, 3), stop, 'flat', base=3, sep=True)
    # waist cord / band
    cord = c.rect(11, 14, 20, 15)
    c.put(cord, band_r, 'vgrad', base=2, sep=True)
    if kind == 'starter':
        tail = S.bez_line(c, (20, 15), (25, 18), (24, 24), 1.4)
        c.put(tail & ~low, R['hemp'], 'flat', base=3)
        c.put(c.circle(24, 25, 1.3), R['red'], 'flat', base=2)
    elif kind == 'bamboo':
        for y in (20, 26):
            c.put(c.rect(8, y, 24, y) & erode4(low), R['bamboo'][1], 'flat', only_on=True)
            c.put(c.rect(8, y + 1, 24, y + 1) & erode4(low), R['bamboo'][3], 'flat', only_on=True)
        lf = S.leaf(c, 20, 14, 30, 8, 3, 0)
        c.put(lf, R['leaf'], 'ray', sep=True)
    elif kind == 'jadeiron':
        for y in (18, 25):
            c.put(c.rect(7, y, 25, y) & low, R['iron'], 'flat', base=3)
        c.put(S.diamond(c, 16, 21.5, 2.4, 2.4), R['jade'], 'ray', base=3, sep=True)
    elif kind == 'cloud':
        for (x, y) in ((10, 22), (17, 25), (13, 9)):
            cloud_curl(c, x, y, R['sky'][2])
        tas = c.poly([(20, 16), (22, 16), (24, 23), (19, 23)])
        c.put(tas, R['sky'], 'ray', base=2, sep=True)
    elif kind == 'mistjade':
        for y in (18, 25):
            c.put(c.rect(7, y, 25, y) & low, R['gold'], 'flat', base=3)
        c.put(c.circle(16, 21.5, 1.8), R['violet'], 'flat', base=4)
    elif kind == 'stormsteel':
        for y in (18, 25):
            c.put(c.rect(7, y, 25, y) & low, R['silver'], 'flat', base=3)
        c.put(c.circle(16, 21.5, 1.8), R['cyan'], 'flat', base=4)
    elif kind == 'sunsteel':
        for y in (18, 25):
            c.put(c.rect(7, y, 25, y) & low, R['red'], 'flat', base=3)
        c.put(c.circle(16, 21.5, 1.8), R['ember'], 'flat', base=4)
    c.outline()
    if kind == 'mistjade':
        c.glow('#B18DE2', (95, 40))
    if kind == 'stormsteel':
        c.glow('#7FD4FF', (95, 40))
    if kind == 'sunsteel':
        c.glow('#FFC870', (95, 40))
    return c


for _g, _w in (('plain', 'hemp'), ('common', 'cotton'), ('earth', 'jadeiron'), ('heaven', 'cloudsilk'),
               ('mystic', 'mistjade'), ('spirit', 'stormsilk'), ('sage', 'sunsilk')):
    register(FAM, '%s_robe' % _w, (lambda gr=_g: robe(gr)), 'armour')
    register(FAM, '%s_trousers' % _w, (lambda gr=_g: trousers(gr)), 'armour')
    if _g not in ('plain', 'common'):
        register(FAM, '%s_boots' % _w, (lambda gr=_g: boots(gr)), 'armour')
register(FAM, 'cloth_boots', lambda: boots('common'), 'armour')
register(FAM, 'straw_sandals', straw_sandals, 'armour')
register(FAM, 'plain_straw_hat', plain_straw_hat, 'armour')
register(FAM, 'bamboo_hat', bamboo_hat, 'armour')
register(FAM, 'jadeiron_hat', jadeiron_hat, 'armour')
register(FAM, 'cloudsilk_hat', cloudsilk_hat, 'armour')
register(FAM, 'mistjade_hat', mistjade_hat, 'armour')
register(FAM, 'stormsilk_hat', stormsilk_hat, 'armour')
register(FAM, 'sunsilk_hat', sunsilk_hat, 'armour')
register(FAM, 'mistjade_cape', mistjade_cape, 'armour')
register(FAM, 'cloud_talisman', cloud_talisman, 'armour')
for _k in ('starter', 'bamboo', 'jadeiron', 'cloud', 'mistjade', 'stormsteel', 'sunsteel'):
    register(FAM, '%s_gourd' % _k, (lambda k=_k: gourd(k)), 'gourds')
