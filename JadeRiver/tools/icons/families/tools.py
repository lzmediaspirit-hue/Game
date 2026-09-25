"""Tools (pickaxes, sickle, rod, pot, furnace, hammer, kits, loupe) and paper
talismans / offerings."""
import math

from pix import Canvas, Ramp, dilate4, erode4, move
from palette import R
from registry import register
import shapes as S

FAM = 'items'


# ============================================================================ tool templates
def handle(c, a, b, ramp, w=2.6, wraps=None, wrap_ramp=None):
    m = c.seg(a[0], a[1], b[0], b[1], w)
    c.put(m, ramp, 'across', base=2)
    if wraps:
        for (t0, t1) in wraps:
            x0, y0 = a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0
            x1, y1 = a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1
            wm = c.seg(x0, y0, x1, y1, w + 0.6)
            c.put(wm, wrap_ramp or R['hemp'], 'across', base=2, sep=True)
            # stripe the wrap
            u = c.xi - c.yi
            c.put(wm & (u % 3 == 0), (wrap_ramp or R['hemp'])[1], 'flat', only_on=True)
    return m


def pickaxe(c, head, shaft, rust=False, wraps=None, wrap_ramp=None):
    handle(c, (5, 28), (21, 10), shaft, 3.0, wraps, wrap_ramp)
    pick = S.taper_curve(c, (21, 10), (13, 3), (4, 6), 4.2, 1.4) | S.taper_curve(c, (21, 10), (28, 14), (29, 24), 4.0, 1.4)
    c.put(pick, head, 'ray', base=2, sep=True)
    eye = c.circle(21, 10, 3.0)
    c.put(eye, head, 'sphere', base=2)
    c.put(c.circle(21, 10, 1.1), shaft, 'flat', base=1)
    top = S.bez_line(c, (19, 7), (13, 4), (6, 5))
    c.put(top & pick, head[4], 'flat', out=head.out)
    if rust:
        for (x, y, r) in ((10, 5, 1.6), (26, 17, 1.5), (23, 12, 1.1), (15, 5, 1.0)):
            c.put(c.circle(x, y, r) & pick, R['copper'], 'flat', base=1)
    return pick


def old_pickaxe():
    c = Canvas(32)
    pickaxe(c, R['stone'], R['wood'], rust=True, wraps=[(0.08, 0.3)], wrap_ramp=R['hemp'])
    crack = c.bres(10, 23, 13, 20)
    c.put(crack & c.a, R['wood'][0], 'flat', only_on=True)
    c.outline()
    return c


def iron_pickaxe():
    c = Canvas(32)
    pickaxe(c, R['iron'], R['darkwood'], wraps=[(0.05, 0.32)], wrap_ramp=R['leather'])
    c.put(c.circle(21, 10, 3.6) & ~c.circle(21, 10, 2.4), R['bronze'], 'flat', base=3, only_on=True)
    c.outline()
    return c


def herb_sickle():
    c = Canvas(32)
    handle(c, (5, 28), (12, 19), R['wood'], 3.2, [(0.0, 1.0)], R['hemp'])
    blade = c.arc(19, 14, 10.5, 4.2, 20, 205) & ~c.ellipse(21, 16, 8, 7)
    blade = c.sector(18, 15, 11, 15, 215) & ~c.ellipse(20.5, 17.5, 9.5, 8.5)
    c.put(blade, R['jadeiron'], 'ray', base=3, sep=True)
    edge = S.outline_only(dilate4(c.ellipse(20.5, 17.5, 9.5, 8.5))) & blade
    c.put(edge, R['jadeiron'][4], 'flat', out=R['jadeiron'].out)
    ferrule = c.circle(12.5, 18.5, 2.4)
    c.put(ferrule, R['bronze'], 'sphere', sep=True)
    c.outline()
    return c


def bamboo_rod():
    c = Canvas(32)
    rod = c.seg(3, 29, 26, 4, 2.4)
    c.put(rod, R['bamboo'], 'across', base=2)
    for t in (0.2, 0.42, 0.64, 0.84):
        x, y = 3 + 23 * t, 29 - 25 * t
        c.put(c.seg(x - 1, y - 1, x + 1, y + 1, 1.2) & rod, R['bamboo'][0], 'flat', only_on=True)
    grip = c.seg(3, 29, 8, 23.5, 3.2)
    c.put(grip, R['leather'], 'across', base=2, sep=True)
    line = S.bez_line(c, (26, 4), (29, 12), (27, 20))
    c.put(line & ~rod, R['paper'], 'flat', base=4)
    flt = c.ellipse(27, 21.5, 1.8, 2.5)
    c.put(flt, R['red'], 'flat', base=2, sep=True)
    c.put(c.rect(26, 21, 28, 21) & flt, R['paper'], 'flat', base=4)
    hook = c.arc(27, 26, 1.8, 1, 180, 360) | c.rect(28, 24, 28, 26)
    c.put(hook, R['iron'], 'flat', base=3)
    reel = c.circle(10.5, 21.5, 2.6)
    c.put(reel, R['wood'], 'sphere', sep=True)
    c.outline()
    return c


def clay_pot():
    c = Canvas(32)
    body = c.ellipse(15, 20, 11, 9)
    c.put(body, R['clay'], 'sphere', base=2, cx=14, cy=18, rx=12, ry=11)
    spout = S.taper_curve(c, (24, 19), (28, 17), (30, 12), 4.0, 2.2)
    c.put(spout, R['clay'], 'ray', base=2, sep=True)
    handle_m = c.ring(4, 18, 3.5, 1.6) & (c.X < 5)
    c.put(handle_m, R['clay'], 'flat', base=1, sep=True)
    lid = c.ellipse(15, 11.5, 7.5, 2.4)
    c.put(lid, R['clay'], 'ray', base=3, sep=True)
    knob = c.circle(15, 8.5, 1.8)
    c.put(knob, R['clay'], 'sphere', base=3, sep=True)
    band = c.rect(4, 17, 26, 17) & body
    c.put(band, R['clay'][1], 'flat', only_on=True)
    c.outline()
    return c


def bronze_furnace():
    c = Canvas(32)
    ramp = R['bronze']
    for x in (8, 15.5, 23):
        c.put(c.poly([(x - 1.6, 22), (x + 1.6, 22), (x + 1.2, 29), (x - 1.2, 29)]), ramp, 'ray', base=1)
    body = c.ellipse(15.5, 18, 11, 8) & (c.Y > 13)
    body |= c.rect(5, 13, 26, 15)
    c.put(body, ramp, 'sphere', base=2, cx=15, cy=15, rx=12, ry=10, sep=True)
    for x in (3.5, 27.5):
        ear = c.ring(x, 10.5, 2.4, 1.2)
        c.put(ear, ramp, 'flat', base=2, sep=True)
    rim = c.rect(4, 11, 27, 13)
    c.put(rim, ramp, 'vgrad', base=3, sep=True)
    lid = c.ellipse(15.5, 10, 7, 3) & (c.Y < 11)
    c.put(lid, ramp, 'ray', base=3, sep=True)
    c.put(c.circle(15.5, 6, 1.8), R['jade'], 'sphere', sep=True)
    # taotie band + fire glow window
    c.put(c.rect(7, 16, 24, 16) & body, ramp[4], 'flat', out=ramp.out)
    win = c.ellipse(15.5, 20, 3.5, 2.2)
    c.put(win, R['fire'], 'flat', base=3, sep=True)
    c.put(c.ellipse(15.5, 20.5, 1.8, 1), R['fire'], 'flat', base=4)
    c.outline()
    return c


def forge_hammer():
    c = Canvas(32)
    handle(c, (3, 29), (17, 15), R['darkwood'], 3.4, [(0.0, 0.3)], R['leather'])
    head = c.diag(0, 13, 19, 45)
    c.put(head, R['iron'], 'ray', base=2, sep=True)
    for (v0, v1) in ((19, 21), (43, 45)):
        c.put(c.diag(0, 13, v0, v1), R['iron'], 'flat', base=3 if v0 < 30 else 1)
    band = c.diag(0, 13, 29, 35)
    c.put(band, R['bronze'], 'ray', base=2)
    c.put(c.diag(11, 13, 22, 42), R['iron'][4], 'flat', only_on=True)
    c.outline()
    return c


def formation_kit():
    c = Canvas(32)
    for k, (x, ramp) in enumerate(((9, R['red']), (15, R['jade']), (21, R['qi']))):
        pole = c.rect(x, 4 + k % 2 * 2, x, 18)
        c.put(pole, R['wood'], 'flat', base=3)
        fl = c.poly([(x + 1, 4 + k % 2 * 2), (x + 7, 6.5 + k % 2 * 2), (x + 1, 10 + k % 2 * 2)])
        c.put(fl, ramp, 'ray', base=2, sep=True)
    box = c.rect(4, 17, 27, 29)
    c.put(box, R['darkwood'], 'bevel', base=3, sep=True)
    lid = c.rect(4, 17, 27, 19)
    c.put(lid, R['darkwood'], 'flat', base=4)
    c.put(c.ring(15.5, 24.5, 3.2, 1), R['gold'], 'flat', base=3)
    c.put(c.rect(15, 24, 16, 25), R['gold'], 'flat', base=4)
    for (x, y) in ((7, 22), (24, 22), (7, 27), (24, 27)):
        c.put(c.rect(x, y, x, y), R['bronze'], 'flat', base=4)
    c.outline()
    return c


def needle_case():
    c = Canvas(32)
    tube = c.seg(8, 26, 20, 14, 7.0)
    c.put(tube, R['bamboo'], 'across', base=2)
    for t in (0.3, 0.7):
        x, y = 8 + 12 * t, 26 - 12 * t
        c.put(c.seg(x - 2.4, y - 2.4, x + 2.4, y + 2.4, 1.0) & tube, R['bamboo'][1], 'flat', only_on=True)
    cap = c.circle(7.5, 26.5, 3.6)
    c.put(cap, R['red'], 'sphere', sep=True)
    mouth = c.ellipse(20.5, 13.5, 3.0, 3.0)
    c.put(mouth, R['bamboo'], 'flat', base=0, sep=True)
    for (dx, dy, L) in ((0, 0, 9), (-1.8, 1.2, 7), (1.4, -1.6, 8)):
        n = c.seg(20.5 + dx, 13.5 + dy, 20.5 + dx + L * 0.7, 13.5 + dy - L * 0.7, 1.0)
        c.put(n & ~c.a | (n & mouth), R['silver'], 'flat', base=4)
    c.put(c.rect(26, 7, 26, 7), R['gold'], 'flat', base=3)
    c.outline()
    return c


def appraiser_loupe():
    c = Canvas(32)
    handle(c, (5, 28), (13, 20), R['darkwood'], 3.4, [(0.0, 0.5)], R['jade'])
    rim = c.ring(19, 13, 9.5, 2.4)
    lens = c.circle(19, 13, 7.2)
    c.put(lens, Ramp(['#1F4E5E', '#3A7F92', '#6FB9C6', '#B6E6E6', '#F2FFFF'], '#0B2129'), 'ray', base=2)
    c.put(c.arc(19, 13, 5.2, 1.4, 110, 170), '#F2FFFF', 'flat')
    c.put(c.rect(15, 9, 16, 9), '#F2FFFF', 'flat')
    c.put(rim, R['bronze'], 'ray', base=3, sep=True)
    c.put(c.circle(12, 20, 2.2), R['bronze'], 'sphere', sep=True)
    c.outline()
    return c


for _id, _fn in (('old_pickaxe', old_pickaxe), ('iron_pickaxe', iron_pickaxe), ('herb_sickle', herb_sickle),
                 ('bamboo_rod', bamboo_rod), ('clay_pot', clay_pot), ('bronze_furnace', bronze_furnace),
                 ('forge_hammer', forge_hammer), ('formation_kit', formation_kit), ('needle_case', needle_case),
                 ('appraiser_loupe', appraiser_loupe)):
    register(FAM, _id, _fn, 'tools')


# ============================================================================ talismans
def talisman_strip(c, paper=None, script=None, x0=9, x1=22, y0=2, y1=29, tilt=0):
    """Vertical paper talisman with red border bars and a script glyph mask."""
    paper = paper or R['talisman']
    m = c.poly([(x0 + tilt, y0), (x1 + tilt, y0), (x1 - tilt, y1), (x0 - tilt, y1)])
    c.put(m, paper, 'bevel', base=3)
    for y in (y0 + 2, y1 - 2):
        c.put(c.rect(x0 + 1, y, x1 - 2, y) & m, R['seal'], 'flat', base=2)
    c.put(c.rect(x0 + 1, y0 + 4, x0 + 1, y1 - 4) & m, R['seal'][1], 'flat', only_on=True)
    c.put(c.rect(x1 - 2, y0 + 4, x1 - 2, y1 - 4) & m, R['seal'][1], 'flat', only_on=True)
    return m


def revival_talisman():
    c = Canvas(32)
    m = talisman_strip(c)
    # script: a rising phoenix-feather glyph + lotus seal
    g = (c.rect(15, 6, 16, 22) | c.bres(12, 9, 15, 11) | c.bres(19, 9, 16, 11) | c.bres(12, 14, 15, 16) |
         c.bres(19, 14, 16, 16) | c.rect(12, 19, 19, 19))
    c.put(g & m, R['seal'], 'flat', base=2)
    seal = c.circle(15.5, 24.5, 2.6)
    c.put(seal, R['seal'], 'flat', base=2)
    c.put(c.rect(15, 24, 16, 25), R['gold'], 'flat', base=4)
    c.outline()
    c.glow('#E5B84C', (80,))
    return c


# S47 talisman craft: each talisman shows its own traced glyph (the stroke template in talismans.json).
TALISMAN_GLYPHS = {
    "flame_talisman": ("fire", [(0.25, 0.9), (0.4, 0.45), (0.5, 0.7), (0.6, 0.2), (0.75, 0.9)]),
    "thunder_talisman": ("storm", [(0.62, 0.05), (0.35, 0.5), (0.62, 0.5), (0.38, 0.95)]),
    "iron_wall_talisman": ("iron", [(0.2, 0.2), (0.8, 0.2), (0.8, 0.8), (0.2, 0.8), (0.2, 0.25)]),
    "wind_step_talisman": ("jade", [(0.5, 0.5), (0.7, 0.42), (0.72, 0.7), (0.38, 0.78), (0.25, 0.4), (0.55, 0.15), (0.9, 0.28)]),
    "veil_talisman": ("violet", [(0.08, 0.5), (0.3, 0.3), (0.5, 0.5), (0.7, 0.3), (0.92, 0.5)]),
    "binding_talisman": ("seal", [(0.2, 0.8), (0.5, 0.2), (0.8, 0.8), (0.2, 0.45), (0.8, 0.45)]),
}


def _glyph_talisman(tid):
    ramp_id, pts = TALISMAN_GLYPHS[tid]
    c = Canvas(32)
    m = talisman_strip(c)
    path = [(11 + p[0] * 9, 6 + p[1] * 17) for p in pts]
    g = c.polyline(path, 1.6)
    c.put(g & m, R[ramp_id], 'flat', base=1)
    c.put(c.circle(15.5, 25.5, 1.8) & m, R['seal'], 'flat', base=2)
    c.outline()
    return c


def cinnabar():
    """Cinnabar: a heap of red powder in a shallow porcelain dish."""
    c = Canvas(32)
    dish = c.ellipse(16, 23, 12, 5)
    c.put(dish, R['porcelain'], 'sphere', base=2, cx=13, cy=21, rx=13, ry=6)
    heap = c.ellipse(16, 19, 8, 5) & (c.Y < 23)
    c.put(heap, R['red'], 'sphere', base=2, cx=14, cy=16, rx=9, ry=6)
    for (x, y) in ((12, 17), (18, 16), (15, 19), (20, 19)):
        c.put(c.circle(x, y, 0.7), R['red'][4], 'flat')
    c.outline()
    return c


def beast_blood_ink():
    """Beast-blood ink: a squat ink pot of dark red, a brush resting across it."""
    c = Canvas(32)
    pot = c.ellipse(16, 21, 9, 7)
    c.put(pot, R['clay'], 'sphere', base=2, cx=13, cy=18, rx=10, ry=8)
    c.put(c.ellipse(16, 16, 6, 2.2), R['red'][0], 'flat')
    c.put(c.ellipse(15, 15.6, 3.5, 1.1), R['red'][2], 'flat')
    c.put(c.seg(6, 11, 26, 18, 1.4), R['bamboo'], 'ray', base=1)
    c.put(c.ellipse(26, 18.5, 2.2, 1.6), R['ink'], 'flat', base=1)
    c.outline()
    return c


def spirit_paper():
    """Spirit paper: a small stack of talisman paper breathing a pale blue Qi."""
    c = Canvas(32)
    for i, (y, t) in enumerate(((20, 1), (15, 0), (10, -1))):
        sheet = c.poly([(7 + t, y), (25 + t, y - 2), (26 + t, y + 5), (8 + t, y + 7)])
        c.put(sheet, R['talisman'], 'bevel', base=3)
    c.put(c.rect(10, 12, 22, 12), R['sky'], 'flat', base=3)
    for (x, y) in ((9, 6), (22, 5), (26, 10)):
        c.put(c.circle(x, y, 1.1), R['sky'], 'flat', base=4)
    c.outline()
    return c


def shattered_moon_blade():
    """The Shattered Moon Blade: a pale jian in three pieces, a faint glow still in the steel."""
    c = Canvas(32)
    steel = R['silver']
    for (x0, y0, x1, y1) in ((6, 27, 10, 23), (13, 20, 17, 16), (21, 12, 26, 7)):
        c.put(c.seg(x0, y0, x1, y1, 2.4), steel, 'ray', base=2)
    c.put(c.seg(4, 25, 8, 29, 1.4), R['gold'], 'flat', base=2)
    c.put(c.seg(3, 30, 6, 27, 1.6), R['darkwood'], 'flat', base=1)
    c.outline()
    c.glow('#CFE3FF', (70,))
    return c


def return_charm():
    c = Canvas(32)
    cord = c.ring(16, 6, 3, 1.2) & (c.Y < 8)
    c.put(cord, R['red'], 'flat', base=2)
    knot = c.poly([(16, 7), (22, 11), (16, 15), (10, 11)])
    c.put(knot, R['red'], 'ray', base=2)
    c.put(c.bres(13, 11, 16, 8) | c.bres(16, 14, 19, 11), R['red'][4], 'flat', only_on=True)
    body = S.rounded_rect(c, 10, 14, 21, 27, 2)
    c.put(body, R['jade'], 'ray', base=2, sep=True)
    # return glyph: circular arrow
    arr = c.arc(15.5, 20.5, 3.6, 1.3, 60, 330)
    head = c.poly([(17, 15.5), (20.5, 17.5), (17, 19.5)])
    c.put((arr | head) & erode4(body), R['jade'][4], 'flat', out=R['jade'].out)
    tas = c.poly([(14, 27), (17, 27), (19, 31), (12, 31)])
    c.put(tas, R['red'], 'ray', base=2, sep=True)
    c.outline()
    return c


def escape_talisman():
    c = Canvas(32)
    m = talisman_strip(c, tilt=1)
    # script: speed lines + running cloud
    g = c.empty()
    for k, y in enumerate((8, 12, 16)):
        g |= c.rect(11 + k, y, 19 - k, y)
    g |= c.bres(12, 20, 19, 20) | c.bres(19, 20, 16, 23)
    c.put(g & m, R['navy'], 'flat', base=2)
    cl = c.ellipse(24, 24, 4, 2.4) | c.ellipse(27, 22, 3, 2.2)
    c.put(cl, R['cloud'], 'ray', base=3, sep=True)
    for y in (21, 25):
        c.put(c.rect(20, y, 22, y) & ~m, R['cloud'], 'flat', base=4)
    c.outline()
    return c


def _offering(grade):
    c = Canvas(32)
    dish = {'common': R['bronze'], 'earth': R['jade'], 'heaven': R['silver']}[grade]
    trim = {'common': R['bronze'], 'earth': R['gold'], 'heaven': R['sky']}[grade]
    foot = c.poly([(12, 24), (20, 24), (22, 29), (10, 29)])
    c.put(foot, dish, 'ray', base=1)
    plate = c.ellipse(16, 23, 13, 3.4)
    # offerings
    if grade == 'common':
        for (x, y) in ((11, 17), (21, 17), (16, 14)):
            p = c.circle(x, y, 4.2)
            c.put(p, R['pink'], 'sphere', base=2, sep=True)
            c.put(c.poly([(x, y - 4), (x + 3, y - 6), (x + 1, y - 3)]), R['leaf'], 'flat', base=3, sep=True)
    elif grade == 'earth':
        root = c.ellipse(16, 16, 5.5, 5)
        c.put(root, R['wax'], 'sphere', sep=True)
        for (a, b) in (((12, 18), (8, 21)), ((20, 18), (24, 21)), ((16, 20), (16, 22))):
            c.put(c.bres(*a, *b), R['wax'][1], 'flat')
        for ang in (120, 90, 60):
            c.put(S.leaf(c, 16, 11.5, ang, 6, 3, 0), R['leaf'], 'ray', sep=True)
        for (x, y) in ((9, 19), (23, 19)):
            c.put(c.circle(x, y, 2.4), R['red'], 'sphere', sep=True)
    else:
        orb = c.circle(16, 14, 6.5)
        c.put(orb, R['qi'], 'sphere', sep=True)
        c.put(c.ring(16, 14, 4, 1) & c.sector(16, 14, 6, 90, 200), R['qi'][4], 'flat', only_on=True)
        for (x, y) in ((8, 19), (24, 19)):
            c.put(c.ellipse(x, y, 3, 2), R['cloud'], 'ray', base=3, sep=True)
    c.put(plate, dish, 'ray', base=3, sep=True)
    c.put(S.outline_only(plate) & (c.Y > 23), trim, 'flat', base=2)
    if grade != 'common':
        for (x) in (6, 16, 26):
            c.put(c.rect(x - 1, 23, x, 24) & plate, trim, 'flat', base=4)
    c.put(c.rect(10, 26, 21, 26) & foot, trim, 'flat', base=3)
    c.outline()
    if grade == 'heaven':
        c.glow('#AFC9D1', (70,))
        S.sparkle(c, 26, 7, '#FFFFFF', R['sky'][3], 2)
    return c


for _tid in TALISMAN_GLYPHS:
    register(FAM, _tid, (lambda t: lambda: _glyph_talisman(t))(_tid), 'talismans')
for _id, _fn in (('cinnabar', cinnabar), ('beast_blood_ink', beast_blood_ink), ('spirit_paper', spirit_paper),
                 ('shattered_moon_blade', shattered_moon_blade)):
    register(FAM, _id, _fn, 'talismans')
for _id, _fn in (('revival_talisman', revival_talisman), ('return_charm', return_charm),
                 ('escape_talisman', escape_talisman),
                 ('bonding_offering_common', lambda: _offering('common')),
                 ('bonding_offering_earth', lambda: _offering('earth')),
                 ('bonding_offering_heaven', lambda: _offering('heaven'))):
    register(FAM, _id, _fn, 'talismans')
