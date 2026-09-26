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


def spirit_spade():
    """S45: a jade-edged spade on a dark wooden shaft, a leaf tied at the grip."""
    c = Canvas(32)
    handle(c, (6, 27), (19, 12), R['darkwood'], 2.6, [(0.0, 0.25)], R['hemp'])
    blade = c.poly([(17, 13), (23, 5), (28, 8), (29, 13), (22, 17)])
    c.put(blade, R['jade'], 'ray', base=2, sep=True)
    c.put(c.poly([(24, 7), (28, 9), (28, 12)]) & blade, R['jade'][4], 'flat')
    collar = c.circle(18.5, 13.5, 2.2)
    c.put(collar, R['bronze'], 'sphere', sep=True)
    c.put(S.leaf(c, 7, 23, 200, 6, 2.6, 0.1), R['leaf'], 'ray', base=2, sep=True)
    c.outline()
    S.sparkle(c, 27, 5, '#FFFFFF', R['jade'][3], 1)
    return c


def verdant_dew_vial():
    """S45: a green glass vial with a jade stopper, a single bright dewdrop inside."""
    c = Canvas(32)
    body = c.ellipse(16, 21, 7.5, 8) | c.rect(13, 8, 19, 14)
    c.put(body, R['mistjade'], 'sphere', base=2, sep=True)
    liquid = c.ellipse(16, 23, 6, 5.5) & body
    c.put(liquid, R['jade'], 'sphere', base=3)
    stopper = c.rect(12, 4, 20, 8)
    c.put(stopper, R['deepjade'], 'ray', base=2, sep=True)
    c.put(c.circle(16, 22, 2.2), R['cyan'], 'sphere', base=3)
    c.put(c.rect(11, 16, 12, 22) & body, R['mistjade'][4], 'flat')
    c.outline()
    c.glow('#8CF0B4', (70,))
    return c


for _id, _fn in (('spirit_spade', spirit_spade), ('verdant_dew_vial', verdant_dew_vial)):
    register(FAM, _id, _fn, 'tools')

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


def purifying_offering():
    """S46: incense sticks and a salt cone on a lotus leaf, smoke curling up."""
    c = Canvas(32)
    leaf = c.ellipse(16, 24, 12, 5)
    c.put(leaf, R['leaf'], 'ray', base=2, sep=True)
    salt = c.poly([(12, 23), (20, 23), (16, 15)])
    c.put(salt, R['pearl'], 'ray', base=3, sep=True)
    for x in (9, 23):
        c.put(c.rect(x, 12, x, 22), R['red'], 'flat', base=2)
        c.put(c.rect(x, 11, x, 11), R['fire'], 'flat', base=4)
    smoke = S.bez_line(c, (9, 10), (6, 6), (10, 2)) | S.bez_line(c, (23, 10), (26, 6), (22, 2))
    c.put(smoke, R['cloud'], 'flat', base=3)
    c.outline()
    c.glow('#E8F4FF', (60,))
    return c


register(FAM, 'purifying_offering', purifying_offering, 'talismans')


# ============================================================================ V10 · Keeping Post: tool ladders
# Four crafts, nine tiers each (0-8). Tier 0 of the pick, sickle and rod ladders (old_pickaxe, herb_sickle,
# bamboo_rod) and the tier-2 iron_pickaxe are drawn above and stay as they are; the net ladder starts at the new
# reed_net (old_net is a torn fishing net, not a tool). A tier row sets the head/blade metal, the shaft,
# the grip wrap and the trim (pick eye ring, sickle ferrule, rod reel, net collar). From tier 4 a gem sits in
# the trim, from tier 7 the tool has a faint glow; the two glass tiers add a clear highlight streak.
TL_STORMSTEEL = Ramp(['#0E121C', '#1C2434', '#323F56', '#566A8A', '#94A8C8'], '#05070C')
TL_SUNGLASS = Ramp(['#6E360A', '#B46612', '#EEA232', '#FFD676', '#FFF6D2'], '#2A1204')
TL_DRIFTGLASS = Ramp(['#2A5A6C', '#5294AA', '#96D4E2', '#D4F4F6', '#FFFFFF'], '#0C2630')
TL_LACQUER = Ramp(['#2A0A0E', '#4E1418', '#7A2226', '#A8383A', '#D86A62'], '#140406')
TL_BOLT = ('#E8FBFF', '#7FD4FF')   # lightning streak: core, edge

TOOL_TIERS = {
    1: dict(metal=R['copper'], shaft=R['wood'], wrap=R['hemp'], trim=R['bronze'], gem=None, glow=None),
    2: dict(metal=R['iron'], shaft=R['darkwood'], wrap=R['leather'], trim=R['bronze'], gem=None, glow=None),
    3: dict(metal=R['jadeiron'], shaft=R['darkwood'], wrap=R['deepjade'], trim=R['bronze'], gem=None, glow=None,
            inlay=R['jade'], blade_base=2),
    4: dict(metal=R['cloudsteel'], shaft=R['darkwood'], wrap=R['silk_navy'], trim=R['silver'], gem=R['qi'],
            glow=None),
    5: dict(metal=R['mistjade_m'], shaft=R['plum'], wrap=R['violetsilk'], trim=R['gold'], gem=R['violet'],
            glow=None),
    6: dict(metal=TL_STORMSTEEL, shaft=R['navy'], wrap=R['navy'], trim=R['silver'], gem=R['cyan'], glow=None,
            bolt=True, blade_base=2),
    7: dict(metal=TL_SUNGLASS, shaft=TL_LACQUER, wrap=R['gold'], trim=R['gold'], gem=R['ember'], glow='#FFC870',
            glass=True),
    8: dict(metal=TL_DRIFTGLASS, shaft=R['navy'], wrap=R['starlight'], trim=R['starlight'], gem='star',
            glow='#BFEFFF', glass=True),
}


def _tl_gem(c, x, y, T, r=1.6):
    """Tier gem (tier 4+) centred on (x, y): a round cabochon, or a star-white glint for tier 8."""
    if T['gem'] is None:
        return
    if T['gem'] == 'star':
        c.put(c.circle(x, y, r), R['starlight'], 'sphere', base=3)
        return
    c.put(c.circle(x, y, r), T['gem'], 'sphere', base=3)


def _tl_finish(c, T, glint=None):
    c.outline()
    if T['glow']:
        c.glow(T['glow'], (70,))
    if T['gem'] == 'star' and glint:
        S.sparkle(c, glint[0], glint[1], '#FFFFFF', R['starlight'][3], 2)


# ---------------------------------------------------------------------------- Delving: picks
def _tier_pick(t):
    T = TOOL_TIERS[t]
    c = Canvas(32)
    wraps = [(0.05, 0.32)] if t < 4 else [(0.05, 0.3), (0.66, 0.74)]
    pick = pickaxe(c, T['metal'], T['shaft'], wraps=wraps, wrap_ramp=T['wrap'])
    if T.get('inlay'):  # a jade inlay strip along the upper arm, a shorter one down the lower arm
        c.put(c.pts([(9, 5), (10, 5), (11, 5), (12, 5), (13, 5), (14, 6), (15, 6), (16, 6), (17, 7), (18, 8)]) & pick,
              T['inlay'], 'flat', base=3)
        c.put(c.pts([(24, 13), (25, 14), (25, 15), (26, 16), (26, 17), (27, 18), (27, 19)]) & pick, T['inlay'],
              'flat', base=2)
    if T.get('bolt'):  # a jagged lightning streak along the upper arm; the rest of the head stays dark
        top = S.bez_line(c, (19, 7), (13, 4), (6, 5))
        c.put(top & pick, T['metal'][3], 'flat', out=T['metal'].out)
        c.put(c.pts([(7, 5), (8, 5), (9, 4), (10, 4), (11, 5), (12, 6), (13, 5), (14, 5), (15, 6), (16, 7),
                     (17, 6), (18, 7), (19, 8)]) & pick, TL_BOLT[0], 'flat', out=T['metal'].out)
        c.put(c.pts([(12, 5), (16, 6), (10, 5)]) & pick, TL_BOLT[1], 'flat', out=T['metal'].out)
    if T.get('glass'):
        c.put(c.pts([(24, 12), (25, 13), (26, 14), (27, 16)]) & pick, T['metal'][4], 'flat', out=T['metal'].out)
    if t >= 5:  # precious tips: trim-metal caps on both points
        c.put((c.circle(4.5, 6.2, 1.8) | c.circle(28.8, 23.5, 1.8)) & pick, T['trim'], 'flat', base=3)
    ring = c.circle(21, 10, 3.6) & ~c.circle(21, 10, 2.4)
    if t >= 3:
        c.put(ring, T['trim'], 'flat', base=3, only_on=True)
    if T['gem'] is not None:
        _tl_gem(c, 21, 10, T)
    _tl_finish(c, T, glint=(26, 4))
    return c


# ---------------------------------------------------------------------------- Foraging: sickles
def _tier_sickle(t):
    T = TOOL_TIERS[t]
    c = Canvas(32)
    handle(c, (5, 28), (12, 19), T['shaft'], 3.2, [(0.0, 0.62)], T['wrap'])
    blade = c.sector(18, 15, 11, 15, 215) & ~c.ellipse(20.5, 17.5, 9.5, 8.5)
    c.put(blade, T['metal'], 'ray', base=T.get('blade_base', 3), sep=True)
    edge = S.outline_only(dilate4(c.ellipse(20.5, 17.5, 9.5, 8.5))) & blade
    c.put(edge, T['metal'][4], 'flat', out=T['metal'].out)
    if T.get('inlay'):
        c.put(S.bez_line(c, (10, 13), (12, 7), (19, 6)) & erode4(blade), T['inlay'], 'flat', base=4)
    if t >= 5:  # a trim-metal spine along the back of the blade
        spine = S.outline_only(blade) & ~dilate4(c.ellipse(20.5, 17.5, 9.5, 8.5)) & (c.Y < 12)
        c.put(spine, T['trim'], 'flat', base=3, out=T['metal'].out)
    if T.get('bolt'):
        bolt = c.bres_path([(17, 5), (13, 8), (15, 8), (10, 13)])
        c.put(move(bolt, 1, 0) & ~bolt & erode4(blade), TL_BOLT[1], 'flat', out=T['metal'].out)
        c.put(bolt & blade, TL_BOLT[0], 'flat', out=T['metal'].out)
    if T.get('glass'):
        c.put(c.pts([(10, 13), (10, 12), (11, 10), (12, 9)]) & blade, T['metal'][4], 'flat', out=T['metal'].out)
    ferrule = c.circle(12.5, 18.5, 2.4)
    c.put(ferrule, T['trim'], 'sphere', sep=True)
    if T['gem'] is not None:
        pom = c.circle(4.6, 28.4, 2.0)
        c.put(pom, T['trim'], 'sphere', sep=True)
        _tl_gem(c, 12.5, 18.5, T, 1.3)
    _tl_finish(c, T, glint=(26, 5))
    return c


# ---------------------------------------------------------------------------- Angling: rods
# rod body, rod marks (bamboo-like nodes or trim rings), line colour, float ramp and float band colour
ROD_TIERS = {
    1: dict(rod=R['straw'], marks='nodes', grip=R['hemp'], line=R['hemp'][3], flt=R['copper'],
            band=R['paper'][4], reel=R['wood']),
    2: dict(rod=R['darkwood'], marks='rings', grip=R['leather'], line=R['paper'][3], flt=R['iron'],
            band=R['red'][3], reel=R['iron']),
    3: dict(rod=R['jadeiron'], marks='rings', grip=R['deepjade'], line=R['jade'][3], flt=R['jade'],
            band=R['paper'][4], reel=R['bronze']),
    4: dict(rod=R['cloud'], marks='rings', grip=R['silk_navy'], line=R['sky'][3], flt=R['cloud'],
            band=R['qi'][2], reel=R['silver']),
    5: dict(rod=R['mistjade_m'], marks='rings', grip=R['violetsilk'], line=R['violet'][3], flt=R['gold'],
            band=R['violet'][2], reel=R['gold']),
    6: dict(rod=TL_STORMSTEEL, marks='bolt', grip=R['navy'], line=R['cyan'][3], flt=R['storm'],
            band=TL_BOLT[0], reel=R['silver']),
    7: dict(rod=TL_SUNGLASS, marks='rings', grip=TL_LACQUER, line=R['gold'][3], flt=R['fire'],
            band=R['gold'][4], reel=R['gold']),
    8: dict(rod=TL_DRIFTGLASS, marks='rings', grip=R['navy'], line=R['starlight'][4], flt='star',
            band=None, reel=R['starlight']),
}


def _tier_rod(t):
    T, Rt = TOOL_TIERS[t], ROD_TIERS[t]
    c = Canvas(32)
    rod = c.seg(3, 29, 26, 4, 2.4)
    c.put(rod, Rt['rod'], 'across', base=2)
    for k, f in enumerate((0.2, 0.42, 0.64, 0.84)):
        x, y = 3 + 23 * f, 29 - 25 * f
        mark = c.seg(x - 1, y - 1, x + 1, y + 1, 1.2) & rod
        if Rt['marks'] == 'nodes':
            c.put(mark, Rt['rod'][0], 'flat', only_on=True)
        elif Rt['marks'] == 'rings' and k > 0:
            c.put(mark, T['trim'], 'flat', base=3, only_on=True)
    if Rt['marks'] == 'bolt':
        c.put(c.pts([(13, 17), (14, 16), (14, 15), (15, 14), (16, 14), (17, 12), (18, 11), (19, 11), (20, 9)]) & rod,
              TL_BOLT[0], 'flat', out=Rt['rod'].out)
    if T.get('glass'):
        c.put(c.pts([(16, 14), (17, 13), (20, 9), (21, 8), (22, 7)]) & rod, Rt['rod'][4], 'flat', out=Rt['rod'].out)
    grip = c.seg(3, 29, 8, 23.5, 3.2)
    c.put(grip, Rt['grip'], 'across', base=2, sep=True)
    if t >= 4:
        c.put(c.seg(7.6, 24, 9, 22.4, 3.4), T['trim'], 'across', base=3, sep=True)
    line = S.bez_line(c, (26, 4), (29, 12), (27, 20))
    c.put(line & ~rod, Rt['line'], 'flat', out=R['ink'][1])
    if Rt['flt'] == 'star':
        flt = S.diamond(c, 27, 22, 2.6, 3.2) | c.rect(25, 21, 28, 22)
        c.put(flt, R['starlight'], 'sphere', base=3, sep=True)
        c.put(c.rect(26, 21, 27, 22), '#FFFDF4', 'flat', out=R['starlight'].out)
    else:
        flt = c.ellipse(27, 21.5, 1.8, 2.5)
        c.put(flt, Rt['flt'], 'flat', base=2 if t != 4 else 3, sep=True)
        c.put(c.rect(26, 21, 28, 21) & flt, Rt['band'], 'flat', out=Rt['flt'].out)
    hook = c.arc(27, 26, 1.8, 1, 180, 360) | c.rect(28, 24, 28, 26)
    c.put(hook, T['trim'] if t >= 5 else R['iron'], 'flat', base=3)
    reel = c.circle(10.5, 21.5, 2.6)
    c.put(reel, Rt['reel'], 'sphere', sep=True)
    if T['gem'] is not None:
        _tl_gem(c, 10.5, 21.5, T, 1.3)
    c.outline()
    if T['glow']:
        c.glow(T['glow'], (70,))
    if T['gem'] == 'star':
        S.sparkle(c, 22, 3, '#FFFFFF', R['starlight'][3], 2)
    return c


# ---------------------------------------------------------------------------- Netting: hoop nets
# hoop material, mesh material, mesh pitch (smaller = finer), handle, wrap, collar
NET_TIERS = {
    0: dict(hoop=R['straw'], mesh=R['hemp'], pitch=5, shaft=R['bamboo'], wrap=None, collar=R['hemp'],
            gem=None, glow=None, size=(19.0, 11.5, 7.5, 6.5)),
    1: dict(hoop=R['wood'], mesh=R['hemp'], pitch=4, shaft=R['wood'], wrap=R['hemp'], collar=R['hemp'],
            gem=None, glow=None),
    2: dict(hoop=R['iron'], mesh=R['clay'], pitch=4, shaft=R['darkwood'], wrap=R['leather'], collar=R['bronze'],
            gem=None, glow=None, knots=True),
    3: dict(hoop=R['jadeiron'], mesh=R['paper'], pitch=3, shaft=R['darkwood'], wrap=R['deepjade'],
            collar=R['bronze'], gem=None, glow=None, inlay=R['jade']),
    4: dict(hoop=R['cloudsteel'], mesh=R['cloud'], pitch=3, shaft=R['darkwood'], wrap=R['silk_navy'],
            collar=R['silver'], gem=R['qi'], glow=None),
    5: dict(hoop=R['mistjade_m'], mesh=R['violet'], pitch=3, shaft=R['plum'], wrap=R['violetsilk'],
            collar=R['gold'], gem=R['violet'], glow=None, studs=R['gold'], rim=R['gold'][3]),
    6: dict(hoop=TL_STORMSTEEL, mesh=R['storm'], pitch=2, shaft=R['navy'], wrap=R['navy'], collar=R['silver'],
            gem=R['cyan'], glow=None, bolt=True),
    7: dict(hoop=TL_SUNGLASS, mesh=R['gold'], pitch=2, shaft=TL_LACQUER, wrap=R['gold'], collar=R['gold'],
            gem=R['ember'], glow='#FFC870', glass=True),
    8: dict(hoop=TL_DRIFTGLASS, mesh=R['pearl'], pitch=2, shaft=R['navy'], wrap=R['starlight'],
            collar=R['starlight'], gem='star', glow='#BFEFFF', glass=True),
}


def _tier_net(t):
    N = NET_TIERS[t]
    c = Canvas(32)
    hx, hy, rx, ry = N.get('size', (19.5, 10.5, 9.0, 7.5))
    cx, cy = hx - 0.69 * rx, hy + 0.83 * ry   # where the handle meets the hoop
    # the handle runs up to the hoop's lower-left rim (a short bare bamboo stick for the reed net)
    a0 = (6.5, 25.5) if t == 0 else (3, 29)
    handle(c, a0, (cx, cy), N['shaft'], 2.6, [(0.0, 0.34)] if N['wrap'] else None, N['wrap'])
    if t == 0:
        for f in (0.35, 0.7):
            x, y = a0[0] + (cx - a0[0]) * f, a0[1] + (cy - a0[1]) * f
            c.put(c.seg(x - 1, y - 1, x + 1, y + 1, 1.2) & c.a, R['bamboo'][0], 'flat', only_on=True)
    # the bag hangs behind the hoop and droops to a rounded tip at the lower right
    inner = c.ellipse(hx, hy, rx - 0.6, ry - 0.6)
    tip = (hx + 0.55 * rx, hy + 2.4 * ry)
    left = S.curve_pts((hx - 0.78 * rx, hy + 0.55 * ry), (hx - 0.35 * rx, hy + 1.95 * ry), tip, 12)
    right = S.curve_pts(tip, (hx + 1.08 * rx, hy + 1.95 * ry), (hx + 0.97 * rx, hy + 0.27 * ry), 12)
    bag = c.poly(left + right) | inner
    droop = bag & ~c.ellipse(hx, hy, rx, ry)
    p = N['pitch']
    grid = (((c.xi + c.yi) % p) == 0) | (((c.xi - c.yi) % p) == 0)
    c.put(droop & grid, N['mesh'], 'ray', base=3 if p > 2 else 2)
    c.put(inner & grid, N['mesh'], 'flat', base=1)
    rim = S.outline_only(droop | inner) & droop
    c.put(rim, N['mesh'], 'flat', base=2)
    if N.get('knots'):
        c.put(droop & (((c.xi + c.yi) % p) == 0) & (((c.xi - c.yi) % p) == 0), N['mesh'], 'flat', base=4)
    if N['gem'] == 'star':  # star-dust glints caught in the starsilk
        c.pxs([(21, 21), (25, 25), (19, 7), (24, 12)], '#FFFDF4', out=R['starlight'].out)
    # the hoop
    hoop = c.ring(hx, hy, rx, 1.8, ry)
    c.put(hoop, N['hoop'], 'ray', base=2)
    c.put(S.outline_only(c.ellipse(hx, hy, rx, ry)) & c.sector(hx, hy, rx + 1, 95, 200),
          N.get('rim', N['hoop'][4]), 'flat', out=N['hoop'].out)
    if N.get('inlay'):
        c.pxs([(19, 3), (26, 5), (28, 11), (12, 8)], N['inlay'][3], out=N['hoop'].out)
    if N.get('studs'):
        c.pxs([(19, 3), (26, 5), (28, 11), (25, 16), (12, 8)], N['studs'][3], out=N['hoop'].out)
    if N.get('bolt'):
        c.put(c.pts([(12, 9), (13, 7), (14, 6), (15, 5), (16, 4), (17, 4), (18, 3), (22, 3), (23, 4), (24, 4)]) & hoop,
              TL_BOLT[0], 'flat', out=N['hoop'].out)
    if N.get('glass'):
        c.put(c.pts([(26, 16), (27, 15), (28, 13)]) & hoop, N['hoop'][4], 'flat', out=N['hoop'].out)
    collar = c.circle(cx, cy, 2.2)
    c.put(collar, N['collar'], 'sphere', sep=True)
    if N['gem'] is not None:
        _tl_gem(c, cx, cy, N, 1.2)
    c.outline()
    if N['glow']:
        c.glow(N['glow'], (70,))
    if N['gem'] == 'star':
        S.sparkle(c, 29, 3, '#FFFFFF', R['starlight'][3], 2)
    return c


for _tl_t, _tl_mat in enumerate(('', 'copper', 'iron', 'jadeiron', 'cloudsteel', 'mystic', 'stormsteel',
                                 'sunglass', 'driftglass')):
    if _tl_t in (1, 3, 4, 5, 6, 7, 8):
        register(FAM, _tl_mat + '_pick', (lambda tt: lambda: _tier_pick(tt))(_tl_t), 'tools')
    if _tl_t >= 1:
        register(FAM, _tl_mat + '_sickle', (lambda tt: lambda: _tier_sickle(tt))(_tl_t), 'tools')
for _tl_t, _tl_id in enumerate(('', 'reedline_rod', 'ironwood_rod', 'jadeline_rod', 'cloud_rod', 'mystic_rod',
                                'storm_rod', 'sunglass_rod', 'starline_rod')):
    if _tl_t >= 1:
        register(FAM, _tl_id, (lambda tt: lambda: _tier_rod(tt))(_tl_t), 'tools')
for _tl_t, _tl_id in enumerate(('reed_net', 'hemp_net', 'cord_net', 'silk_net', 'cloudsilk_net', 'mystic_net',
                                'storm_net', 'sunglass_net', 'starsilk_net')):
    register(FAM, _tl_id, (lambda tt: lambda: _tier_net(tt))(_tl_t), 'tools')


# ============================================================================ V10c · snare kits
# The snaring craft's kits: a coiled snare cord with a running noose, tied off to its stake(s). Richer with tier:
# the cord (hemp, iron wire, spirit silk, star silk), the noose fitting (a plain knot, an iron ring, a jade
# toggle, a driftglass ring) and the stakes (one wooden peg, then two capped stakes). Upright stakes and a coil
# keep them apart from the diagonal hoop nets.
SN_SPIRITSILK = Ramp(['#2E6A7A', '#5AA6B6', '#9EDCE4', '#D8F6F6', '#FFFFFF'], '#0E2A32')

SNARE_TIERS = {
    'hemp': dict(cord=R['hemp'], w=1.8, twist=True, stake=R['wood'], cap=None, stakes=1, fit='knot', glow=None),
    'iron': dict(cord=R['iron'], w=1.4, twist=False, stake=R['darkwood'], cap=R['iron'], stakes=2, fit='ring',
                 ring=R['iron'], glow=None),
    'silk': dict(cord=SN_SPIRITSILK, w=1.6, twist=False, stake=R['bamboo'], cap=R['silver'], stakes=2, fit='toggle',
                 glow=None),
    'star': dict(cord=R['starlight'], w=1.6, twist=False, stake=R['navy'], cap=R['starlight'], stakes=2,
                 fit='ring', ring=TL_DRIFTGLASS, glow='#BFEFFF'),
}


def _sn_stake(c, top, tip, K):
    """A pointed stake from its head (top) down to its tip, cord lashed under the head, an optional cap."""
    (x0, y0), (x1, y1) = top, tip

    def at(f):
        return x0 + (x1 - x0) * f, y0 + (y1 - y0) * f

    # a tent-peg barb on the right, where the snare's line catches
    bx, by = at(0.3)
    barb = c.poly([(bx, by - 1.2), (bx + 3.4, by - 3.0), (bx + 3.0, by - 1.4), (bx, by + 1.4)])
    c.put(barb, K['stake'], 'ray', base=2)
    px, py = at(0.8)
    shaft = c.seg(x0, y0, px, py, 3.0)
    point = c.poly([(px - 1.5, py - 0.5), (px + 1.5, py - 0.5), (x1 + 0.3, y1)])
    c.put(shaft | point, K['stake'], 'across', base=2, sep=True)
    c.put(point, K['stake'], 'flat', base=1)
    c.put(c.ellipse(x0, y0 - 0.2, 1.6, 0.9), K['stake'], 'flat', base=4)
    if K['cap'] is not None:  # a metal (or jade, or star-gold) ferrule round the head
        cap = c.seg(x0, y0 - 0.2, *at(0.08), 3.4)
        c.put(cap, K['cap'], 'across', base=2, sep=True)
        c.put(c.ellipse(x0, y0 - 0.4, 1.6, 0.8), K['cap'], 'flat', base=4)
    # the cord lashed round the stake under the head
    for f in (0.17, 0.23):
        x, y = at(f)
        c.put(c.seg(x - 1.8, y, x + 1.8, y, 1.0) & shaft, K['cord'], 'flat', base=3)
    return shaft | point


def _tier_snare(tier):
    K = SNARE_TIERS[tier]
    c = Canvas(32)
    cord = K['cord']
    # stakes, the back one first
    stakes = [((23.5, 8.5), (22, 29.5))]
    if K['stakes'] == 2:
        stakes = [((26.8, 12.5), (26, 29.5))] + stakes
    for (top, tip) in stakes:
        _sn_stake(c, top, tip, K)
    # the coil: the spare cord wound in a flat spiral, seen at a slant
    cx, cy = 11.5, 11.5
    pts = []
    for i in range(121):
        f = i / 120.0
        th = -math.pi * 0.5 + f * 2.25 * 2 * math.pi
        r = 1.4 + 7.6 * f
        pts.append((cx + r * math.cos(th), cy + r * 0.78 * math.sin(th)))
    coil = c.polyline(pts, K['w'])
    c.put(coil, cord, 'ray', base=2, sep=True)
    if K['twist']:
        c.put(coil & ((c.xi + c.yi) % 4 == 0), cord, 'flat', base=1)
    else:
        c.put(coil & c.sector(cx, cy, 12, 100, 170, 9), cord, 'flat', base=4)
    # the running line from the coil's outer end over to the front stake's lashing
    ex, ey = pts[-1]
    line = S.bez_line(c, (ex, ey), (ex + 5, ey - 2), (23.5, 13.5), K['w'])
    c.put(line & ~coil, cord, 'flat', base=3, sep=True)
    # the noose hanging below the coil, its slip fitting where it closes
    drop = c.seg(10.5, 18.5, 10.5, 21.5, K['w'])
    noose = c.ring(10.5, 25.4, 5.2, K['w'], 3.6)
    c.put(drop | noose, cord, 'ray', base=3, sep=True)
    if K['twist']:
        c.put(noose & ((c.xi + c.yi) % 3 == 0), cord, 'flat', base=1)
    if K['fit'] == 'knot':
        c.put(c.rect(9, 20, 11, 22), cord, 'ray', base=2, sep=True)
        c.put(c.rect(10, 20, 10, 20), cord, 'flat', base=4)
    elif K['fit'] == 'ring':
        ring = c.ring(10.5, 21.2, 2.4, 1.2)
        c.put(ring, K['ring'], 'ray', base=3, sep=True)
        c.put(c.arc(10.5, 21.2, 2.4, 1.2, 100, 190), K['ring'], 'flat', base=4)
    else:  # jade toggle: a small bar threaded through the loop
        tog = c.seg(7.2, 21.6, 13.8, 20.2, 2.2)
        c.put(tog, R['jade'], 'across', base=3, sep=True)
        c.put(c.rect(8, 20, 9, 20) & tog, R['jade'], 'flat', base=4)
    c.outline()
    if K['glow']:
        c.glow(K['glow'], (70,))
        S.sparkle(c, 4, 4, '#FFFFFF', R['starlight'][3], 2)
        c.pxs([(15, 25), (6, 12)], '#FFFDF4', out=R['starlight'].out)
    return c


for _sn_tier in ('hemp', 'iron', 'silk', 'star'):
    register(FAM, _sn_tier + '_snare_kit', (lambda tt: lambda: _tier_snare(tt))(_sn_tier), 'tools')
