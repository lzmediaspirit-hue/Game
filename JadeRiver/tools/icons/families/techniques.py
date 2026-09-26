"""Technique icons: a round emblem in the element colour + one pale motion / weapon
mark with its own dark keyline, so they read inside the circular HUD skill slots.

Combat techniques use a plain dark rim; secret arts use a gold rim with four studs.
"""
import math

from pix import Canvas, Ramp, dilate4, erode4, move
from palette import R
from registry import register
import shapes as S

FAM, GROUP = 'techniques', 'techniques'

EL = {  # disc ramp, mark ramp
    'water': (['#081E2C', '#0F3A52', '#18607C', '#2E8AA6', '#62BCD0'],
              ['#1E5A70', '#4A9AB2', '#9EE0EC', '#DDF8FB', '#FFFFFF']),
    'qi': (['#06232C', '#0B4450', '#12707E', '#20A2AE', '#5CD4D8'],
           ['#1A6A76', '#40A8B4', '#9CF0F0', '#E0FFFC', '#FFFFFF']),
    'wood': (['#0A2014', '#123A22', '#1C5A32', '#2E8248', '#5EB06A'],
             ['#2A6A34', '#5AA052', '#B0E08A', '#E6F8CC', '#FFFFFF']),
    'jade': (['#082220', '#0F3C38', '#185E56', '#27887A', '#56BCA8'],
             ['#2C7A6C', '#58B4A0', '#A8EEDA', '#E2FFF4', '#FFFFFF']),
    'metal': (['#121A24', '#212E3C', '#344658', '#50667C', '#8098AE'],
              ['#56687C', '#8A9CB0', '#CBD8E4', '#F0F6FA', '#FFFFFF']),
    'fire': (['#2A0A08', '#4E140E', '#7C2414', '#B0401E', '#E27436'],
             ['#9A3012', '#DA6224', '#FFB850', '#FFEAA6', '#FFFFFF']),
    'earth': (['#1E1408', '#382610', '#5A3E1C', '#84602E', '#B48A4E'],
              ['#74522A', '#A87E40', '#E6C88A', '#FAEECC', '#FFFFFF']),
    'wind': (['#0A2220', '#133C38', '#1E5A54', '#34827A', '#68B4A8'],
             ['#3A7E74', '#6AB4A6', '#B4EEDE', '#E8FFF6', '#FFFFFF']),
    'soul': (['#150C26', '#251640', '#3A2466', '#583C92', '#8A6CC4'],
             ['#553A90', '#8A6ACA', '#D0BCF6', '#F2EAFF', '#FFFFFF']),
    'shadow': (['#08060F', '#120F20', '#1E1934', '#302A50', '#524A7C'],
               ['#4A4070', '#7A6EA8', '#B8ACDC', '#E8E2F8', '#FFFFFF']),
    'heaven': (['#2A1A04', '#4A300A', '#744C14', '#A87424', '#DAA84A'],
               ['#9A6A20', '#D09A3A', '#FFE28C', '#FFF7D8', '#FFFFFF']),
}


def emblem(element, secret=False):
    c = Canvas(32)
    disc_c, mark_c = EL[element]
    disc = Ramp(disc_c, '#05080B')
    mk = Ramp(mark_c, disc_c[0])
    outer = c.circle(16, 16, 15)
    rim = R['gold'] if secret else Ramp([disc_c[0], disc_c[1], disc_c[2], disc_c[3], disc_c[4]], '#05080B')
    c.put(outer, rim, 'sphere', base=2 if secret else 1)
    inner = c.circle(16, 16, 13)
    c.put(inner, disc, 'sphere', base=2, bands=((0.9, 1), (0.55, 0), (0.1, -1), (-9, -2)))
    c.put(S.outline_only(inner), disc, 'flat', base=0)
    if secret:
        for (x, y) in ((16, 2.5), (29.5, 16), (16, 29.5), (2.5, 16)):
            c.put(S.diamond(c, x, y, 1.8, 1.8), R['gold'], 'flat', base=4, sep=True)
    c.clip = inner
    return c, mk, disc


def mark(c, m, mk, base=3, mode='ray'):
    """Paint a mark with a dark keyline (drawn over the disc)."""
    ring = dilate4(m) & ~m
    c.rgb[ring & c.a] = mk.out
    c.put(m, mk, mode, base=base)
    return m


def done(c, glow=None):
    c.outline()
    if glow:
        c.glow(glow, (80,))
    return c


# ----------------------------------------------------------------------------- mark builders
def crescent(c, cx, cy, r, dx, dy, r2=None):
    return c.circle(cx, cy, r) & ~c.circle(cx + dx, cy + dy, r2 or r)


def arrow(c, x0, y0, x1, y1, head=3.2, w=1.4, fletch=True):
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    px, py = -uy, ux
    m = c.seg(x0, y0, x1 - ux * head * 0.6, y1 - uy * head * 0.6, w)
    m |= c.poly([(x1 + ux * 0.5, y1 + uy * 0.5), (x1 - ux * head + px * head * 0.7, y1 - uy * head + py * head * 0.7),
                 (x1 - ux * head - px * head * 0.7, y1 - uy * head - py * head * 0.7)])
    if fletch:
        for s in (1, -1):
            m |= c.seg(x0 + ux * 1.5, y0 + uy * 1.5, x0 - ux * 1.2 + px * 2.2 * s, y0 - uy * 1.2 + py * 2.2 * s, 1.2)
    return m


def blade(c, x0, y0, x1, y1, w=3.2, guard=True):
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    px, py = -uy, ux
    tipL = 3.5
    b = c.poly([(x0 + px * w / 2, y0 + py * w / 2), (x1 - ux * tipL + px * w / 2, y1 - uy * tipL + py * w / 2),
                (x1, y1), (x1 - ux * tipL - px * w / 2, y1 - uy * tipL - py * w / 2),
                (x0 - px * w / 2, y0 - py * w / 2)])
    if guard:
        gx, gy = x0, y0
        b |= c.seg(gx + px * 3.5, gy + py * 3.5, gx - px * 3.5, gy - py * 3.5, 1.8)
        b |= c.seg(gx, gy, gx - ux * 4.5, gy - uy * 4.5, 1.8)
    return b


def speed_lines(c, pts, L=4, ang=225):
    m = c.empty()
    dx, dy = math.cos(math.radians(ang)), -math.sin(math.radians(ang))
    for (x, y) in pts:
        m |= c.bres(int(x), int(y), int(round(x + dx * L)), int(round(y + dy * L)))
    return m


def palm(c, cx=16, cy=19, s=1.0):
    m = S.rounded_rect(c, int(cx - 5 * s), int(cy - 3 * s), int(cx + 4 * s), int(cy + 5 * s), 2)
    fingers = []
    for k, (dx, top) in enumerate(((-4, -9), (-1.3, -11), (1.4, -10.5), (4, -8))):
        fingers.append(c.seg(cx + dx * s, cy - 2 * s, cx + dx * s, cy + top * s, 2.6 * s))
    thumb = c.seg(cx - 5 * s, cy + 1 * s, cx - 9 * s, cy - 4 * s, 2.6 * s)
    return m, fingers, thumb


def paint_palm(c, mk, cx=16, cy=19, s=1.0):
    m, fingers, thumb = palm(c, cx, cy, s)
    whole = m | thumb
    for f in fingers:
        whole |= f
    mark(c, whole, mk)
    for f in fingers[1:]:
        edge = dilate4(f) & ~f & whole & (c.Y < cy - 2 * s)
        c.recolor(edge, mk[1])
    c.recolor(dilate4(thumb) & ~thumb & m, mk[1])
    return whole


def cloud_shape(c, cx, cy, s=1.0):
    return (c.ellipse(cx - 3.5 * s, cy + 0.5 * s, 3.2 * s, 2.4 * s) | c.ellipse(cx, cy - 1 * s, 3.6 * s, 3.2 * s) |
            c.ellipse(cx + 3.8 * s, cy + 0.6 * s, 3 * s, 2.3 * s) | c.rect(int(cx - 6 * s), int(cy + 0.5 * s),
                                                                          int(cx + 6 * s), int(cy + 2.5 * s)))


def wave_crest(c, cx, cy, s=1.0):
    base = c.rect(int(cx - 10 * s), int(cy + 1 * s), int(cx + 10 * s), int(cy + 5 * s))
    crest = crescent(c, cx, cy, 7 * s, -3 * s, 3.5 * s, 6 * s) & (c.Y < cy + 3 * s)
    curl = c.circle(cx - 1.5 * s, cy + 1.5 * s, 2.2 * s)
    return base | crest | curl, curl


def eye_shape(c, cx, cy, rx, ry):
    # almond: intersection of two offset circles
    R0 = (rx * rx + ry * ry) / (2 * ry)
    return c.circle(cx, cy + R0 - ry, R0) & c.circle(cx, cy - R0 + ry, R0)


# ============================================================================ techniques
def flowing_palm():
    c, mk, d = emblem('water')
    for k, y in enumerate((23, 26)):
        w = S.wave_line(c, 5, 27, y, 1, 7, phase=k * 3) & c.circle(16, 16, 12.5)
        c.put(w, mk, 'flat', base=2 - k)
    paint_palm(c, mk, 16, 18, 1.0)
    return done(c)


def jade_thrust():
    c, mk, d = emblem('jade')
    b = blade(c, 9, 23, 26, 6, 3.4)
    mark(c, b, mk)
    sl = speed_lines(c, [(8, 16), (13, 26), (5, 20)], 4, 225)
    c.put(sl & ~b, mk, 'flat', base=2)
    return done(c)


def cloudpiercing_stroke():
    c, mk, d = emblem('wind')
    steel = Ramp(EL['metal'][1], EL['wind'][0][0])
    b = blade(c, 6, 26, 26, 6, 3.6, guard=False)
    mark(c, b, steel, base=3)
    cl = cloud_shape(c, 13, 19, 1.25)
    mark(c, cl, mk, base=3)
    sl = speed_lines(c, [(21, 17), (23, 20), (15, 8)], 3, 225)
    c.put(sl & ~b & ~cl, mk, 'flat', base=2)
    return done(c)


def reedcutter_slash():
    c, mk, d = emblem('wood')
    arc = crescent(c, 17, 17, 11, -3.5, 3.5, 10.5)
    arc &= c.circle(16, 16, 13)
    mark(c, arc, mk)
    for (x, y, a) in ((9, 24, 70), (13, 26, 95)):
        lf = S.leaf(c, x, y, a, 6, 2, 0)
        mark(c, lf, mk, base=2)
    return done(c)


def riverstone_sweep():
    c, mk, d = emblem('earth')
    sweep = crescent(c, 15, 11, 13, 0, -4.5, 13.5) & (c.Y > 13) & c.circle(16, 16, 12.8)
    mark(c, sweep, mk)
    sl = speed_lines(c, [(7, 13), (9, 10)], 3, 200)
    c.put(sl & ~sweep, mk, 'flat', base=2)
    st = c.ellipse(21, 11, 3.8, 2.8)
    mark(c, st, Ramp(EL['metal'][1], EL['earth'][0][0]), base=2)
    c.put(c.rect(19, 10, 20, 10), '#FFFFFF', 'flat')
    return done(c)


def twin_reed_shot():
    c, mk, d = emblem('wood')
    for (dx, dy) in ((-3, 3), (3, -3)):
        a = arrow(c, 8 + dx, 24 + dy, 24 + dx, 8 + dy, 3.6, 1.5)
        mark(c, a, mk)
    return done(c)


def tiger_rush():
    c, mk, d = emblem('fire')
    for k in range(3):
        o = (k - 1) * 5
        cl = S.taper_curve(c, (9 + o, 7 - o * 0.2), (15 + o, 15), (18 + o, 26 + o * 0.2), 3.4, 0.8)
        mark(c, cl, mk)
    return done(c)


def willow_leaf_parry():
    c, mk, d = emblem('wood')
    lf = S.leaf(c, 8, 24, 55, 20, 7.5, 0.1)
    mark(c, lf, mk)
    c.put(S.midrib(c, 8, 24, 55, 20, 0.1, 0.85), mk[1], 'flat', only_on=True)
    arc = c.arc(16, 16, 11, 1.6, 20, 110)
    mark(c, arc & c.circle(16, 16, 12.5), mk, base=2)
    return done(c)


def dragon_tail_sweep():
    c, mk, d = emblem('water')
    tail = S.taper_curve(c, (5, 12), (12, 30), (27, 16), 5.5, 1.5)
    mark(c, tail, mk)
    for (x, y) in ((9, 18), (12, 22), (16, 23)):
        c.put(c.rect(x, y, x + 1, y), mk[1], 'flat', only_on=True)
    fin = c.poly([(24, 17), (28, 10), (26, 18)])
    mark(c, fin, mk, base=2)
    return done(c)


def shadow_flick():
    c, mk, d = emblem('shadow')
    for (x0, y0, x1, y1) in ((5, 21, 21, 7), (10, 27, 26, 13)):
        b = blade(c, x0 + 7, y0 - 7, x1, y1, 3.2, guard=False)
        tr = S.taper_curve(c, (x0, y0), (x0 + 3, y0 - 3), (x0 + 7, y0 - 7), 0.8, 2.6) & c.circle(16, 16, 12.8)
        c.put(tr, mk, 'flat', base=1)
        mark(c, b, mk, base=3)
    return done(c)


def bell_toll_strike():
    c, mk, d = emblem('metal')
    bell = c.poly([(13, 7), (19, 7), (21, 12), (22.5, 19), (24.5, 22), (7.5, 22), (9.5, 19), (11, 12)])
    bell |= c.rect(15, 5, 16, 7)
    mark(c, bell, mk)
    c.put(c.rect(9, 18, 22, 18) & bell, mk[1], 'flat', only_on=True)
    cl = c.circle(16, 24, 1.8)
    mark(c, cl, mk, base=2)
    for r in (11.5,):
        ring = c.arc(16, 15, r, 1.2, 150, 210) | c.arc(16, 15, r, 1.2, 330, 30)
        c.put(ring, mk, 'flat', base=2)
    return done(c)


def pinning_arrow():
    c, mk, d = emblem('metal')
    a = arrow(c, 16, 5, 16, 22, 4.0, 1.6)
    mark(c, a, mk)
    ground = c.rect(6, 23, 25, 24) & c.circle(16, 16, 12.5)
    c.put(ground, mk, 'flat', base=1)
    cracks = c.bres_path([(16, 24), (12, 27)]) | c.bres_path([(16, 24), (21, 27)]) | c.bres_path([(16, 24), (16, 27)])
    c.put(cracks & c.circle(16, 16, 12.5), mk, 'flat', base=3)
    return done(c)


def rising_tide():
    c, mk, d = emblem('water')
    w, curl = wave_crest(c, 15, 18, 1.0)
    w &= c.circle(16, 16, 12.5)
    mark(c, w & ~curl, mk)
    c.put(curl & w, d, 'flat', base=1)
    up = c.poly([(22, 5), (26.5, 10), (23.5, 10), (23.5, 14), (20.5, 14), (20.5, 10), (17.5, 10)])
    mark(c, up, mk, base=4)
    return done(c)


def palm_wave():
    c, mk, d = emblem('qi')
    for r in (5, 8.5):
        arc = c.arc(14, 16, r, 1.3, -50, 50) & c.circle(16, 16, 12.5)
        c.put(arc & ~c.rect(0, 0, 14, 31), mk, 'flat', base=2 if r > 6 else 3)
    whole = paint_palm(c, mk, 11, 19, 0.85)
    del whole
    ring = c.arc(14, 16, 11.5, 1.3, -40, 40) & c.circle(16, 16, 12.5)
    c.put(ring, mk, 'flat', base=1)
    return done(c)


def crescent_arc():
    c, mk, d = emblem('metal')
    m = crescent(c, 16, 16, 11.5, 4.5, -2.5, 10.5)
    mark(c, m, mk)
    S.sparkle(c, 22, 9, '#FFFFFF', mk[3], 1)
    return done(c)


def spear_lance():
    c, mk, d = emblem('metal')
    shaft = c.seg(5, 27, 17, 15, 2.0)
    head = S.leaf(c, 16, 16, 45, 13, 5.5, 0, tip_power=0.6)
    mark(c, shaft | head, mk)
    c.put(c.seg(15, 17, 18, 14, 3.4), R['red'], 'flat', base=2)
    sl = speed_lines(c, [(10, 13), (18, 26), (7, 18)], 5, 225)
    c.put(sl & ~c.a | (sl & ~(shaft | head)), mk, 'flat', base=1)
    return done(c)


def flying_blades():
    c, mk, d = emblem('metal')
    for (x0, y0, x1, y1) in ((10, 25, 14, 9), (12, 26, 24, 13), (8, 22, 5, 11)):
        b = blade(c, x0, y0, x1, y1, 2.6, guard=False)
        mark(c, b, mk)
    return done(c)


def sword_release():
    """One jian flying free, point up, with a wide arc of its path around it."""
    c, mk, d = emblem('metal')
    b = blade(c, 11, 25, 22, 7, 3.0, guard=True)
    mark(c, b, mk)
    inner = c.circle(16, 16, 12.8)
    arc = c.arc(16, 17, 10.5, 1.4, 200, 330) & inner
    c.put(arc, mk, 'flat', base=2)
    return done(c)


def earthshaker_wave():
    c, mk, d = emblem('earth')
    inner = c.circle(16, 16, 12.8)
    ground = c.rect(0, 20, 31, 31) & inner
    c.put(ground, d, 'flat', base=3)
    c.put(c.rect(0, 20, 31, 20) & inner, d, 'flat', base=4)
    for r, lv in ((5.5, 3), (9.5, 2)):
        arc = c.arc(16, 20, r, 1.6, 10, 170) & inner & (c.Y < 20)
        c.put(arc, mk, 'flat', base=lv)
    cr = c.polyline([(16, 20), (14, 23), (17, 25), (15, 29)], 1.8)
    mark(c, cr & ground, Ramp(EL['earth'][0], EL['earth'][0][0]), base=0)
    return done(c)


def vine_snare():
    c, mk, d = emblem('wood')
    vine = c.empty()
    pts = []
    for k in range(60):
        t = k / 59.0
        r = 11 - t * 9
        a = t * 4.2 * math.pi
        pts.append((16 + r * math.cos(a), 16 + r * math.sin(a)))
    for a_, b_ in zip(pts, pts[1:]):
        vine |= c.seg(a_[0], a_[1], b_[0], b_[1], 1.8)
    mark(c, vine, mk, base=2)
    for (x, y, a) in ((26, 14, 60), (8, 20, 220), (19, 25, 300)):
        lf = S.leaf(c, x, y, a, 5, 3, 0)
        mark(c, lf, mk, base=3)
    return done(c)


def rain_of_reeds():
    c, mk, d = emblem('wood')
    for (x, y) in ((8, 6), (15, 4), (22, 7), (11, 13), (19, 13)):
        a = arrow(c, x + 3, y, x - 1, y + 11, 2.6, 1.2, fletch=False)
        mark(c, a & c.circle(16, 16, 12.8), mk)
    ground = c.rect(6, 25, 25, 26) & c.circle(16, 16, 12.5)
    c.put(ground, mk, 'flat', base=1)
    return done(c)


def stone_skin():
    c, mk, d = emblem('earth')
    sh = c.poly([(7, 7), (25, 7), (25, 17), (16, 27), (7, 17)])
    mark(c, sh, Ramp(EL['metal'][1], EL['earth'][0][0]), base=2)
    for (a, b) in (((7, 12), (25, 12)), ((7, 17), (25, 17)), ((16, 7), (16, 12)), ((12, 12), (12, 17)),
                   ((20, 12), (20, 17)), ((16, 17), (16, 22))):
        c.put(c.bres(*a, *b) & erode4(sh), EL['earth'][0][2], 'flat', only_on=True)
    c.put(c.rect(9, 9, 13, 9), '#FFFFFF', 'flat', only_on=True)
    return done(c)


def gale_step():
    c, mk, d = emblem('wind')
    boot = c.poly([(12, 6), (18, 6), (18, 16), (25, 19), (25, 23), (12, 23)])
    mark(c, boot, mk)
    c.put(c.rect(12, 21, 25, 23) & boot, mk, 'flat', base=1)
    for k, y in enumerate((10, 15, 20)):
        w = c.arc(8, y + 2, 3, 1.2, 60, 200) | c.rect(4 + k, y + 4, 10, y + 4)
        c.put(w & c.circle(16, 16, 12.5) & ~boot, mk, 'flat', base=3)
    return done(c)


def mountain_shaker():
    c, mk, d = emblem('earth')
    mt = c.poly([(4, 25), (12, 12), (16, 17), (20, 9), (28, 25)]) & c.circle(16, 16, 12.8)
    mark(c, mt, mk, base=2)
    snow = c.poly([(20, 9), (22.5, 13), (21, 12.5), (19.5, 14), (18, 12.5)])
    c.put(snow & mt, mk, 'flat', base=4)
    cr = c.bres_path([(20, 14), (18, 18), (21, 21), (19, 25)])
    c.put(cr & mt, EL['earth'][0][0], 'flat')
    for r in (3,):
        c.put(c.arc(20, 7, 5, 1.2, 20, 160) & ~mt, mk, 'flat', base=3)
    return done(c)


def ember_burst():
    c, mk, d = emblem('fire')
    pts = []
    for k in range(16):
        a = k * math.pi / 8 + 0.2
        r = 11 if k % 2 == 0 else 5
        pts.append((16 + r * math.cos(a), 16 + r * math.sin(a)))
    burst = c.poly(pts)
    mark(c, burst, mk)
    c.put(c.circle(16, 16, 3.5), mk, 'flat', base=4)
    return done(c)


def still_water_focus():
    c, mk, d = emblem('water')
    for r, lv in ((10.5, 1), (7, 2)):
        ring = c.ring(16, 22, r, 1.1, r * 0.34) & c.circle(16, 16, 12.5)
        c.put(ring, mk, 'flat', base=lv)
    dr = S.drop(c, 16, 14, 3.6, 8)
    mark(c, dr, mk)
    c.put(c.rect(14, 12, 14, 14), '#FFFFFF', 'flat')
    return done(c)


def shadowstep_cut():
    c, mk, d = emblem('shadow')
    ghost = c.seg(7, 22, 20, 9, 2.6)
    c.put(ghost & c.circle(16, 16, 12.5), mk, 'flat', base=1)
    cut = c.seg(11, 26, 25, 12, 3.0) & ~c.seg(11, 26, 25, 12, 0.8) | c.seg(11, 26, 25, 12, 1.0)
    cut = S.taper_curve(c, (9, 27), (17, 20), (26, 10), 1.0, 1.0) | S.leaf(c, 9, 27, 45, 22, 3.6, 0)
    mark(c, cut, mk)
    return done(c)


def cloud_descent():
    c, mk, d = emblem('wind')
    cl = cloud_shape(c, 16, 9, 1.2)
    mark(c, cl, mk, base=3)
    a = c.poly([(13, 14), (19, 14), (19, 20), (23, 20), (16, 27), (9, 20), (13, 20)])
    mark(c, a, Ramp(EL['heaven'][1], EL['wind'][0][0]))
    return done(c)


def mirror_mind_spike():
    c, mk, d = emblem('soul')
    mirror = c.circle(13, 18, 7)
    mark(c, mirror, mk, base=2)
    c.put(c.circle(13, 18, 5) & mirror, mk, 'dgrad', base=3)
    crack = c.bres_path([(13, 18), (10, 15), (9, 13)]) | c.bres_path([(13, 18), (16, 21)])
    c.put(crack & mirror, mk[0], 'flat')
    spike = c.poly([(16, 15), (27, 5), (19, 18)])
    mark(c, spike, mk, base=4)
    return done(c)


def soul_lantern_ward():
    c, mk, d = emblem('soul')
    ward = c.ring(16, 17, 11.5, 1.3) & c.circle(16, 16, 12.8)
    c.put(ward, mk, 'flat', base=2)
    body = S.rounded_rect(c, 11, 11, 20, 23, 2)
    mark(c, body, mk, base=2)
    c.put(c.rect(13, 13, 18, 21), R['qi'], 'flat', base=4)
    c.put(c.rect(15, 15, 16, 19), '#FFFFFF', 'flat')
    caps = c.rect(10, 9, 21, 10) | c.rect(10, 24, 21, 25)
    mark(c, caps, Ramp(EL['heaven'][1], EL['soul'][0][0]))
    hook = c.ring(15.5, 7, 2, 1) & (c.Y < 8)
    c.put(hook, mk, 'flat', base=3)
    return done(c)


def blood_burning():
    """S48 costly art: a drop of blood burning upward, on a fire disc with the secret-art rim."""
    c, mk, d = emblem('fire', secret=True)
    drop = c.poly([(16, 6), (21, 15), (22, 19), (19, 24), (13, 24), (10, 19), (11, 15)]) | c.circle(16, 19.5, 5.6)
    mark(c, drop, Ramp(['#3A0508', '#6E0C12', '#A8161E', '#D83A3A', '#FF8A7A'], '#1A0204'), base=3, mode='sphere')
    for (x0, y0, x1, y1) in ((12, 11, 10, 5), (20, 11, 22, 5), (16, 9, 16, 3)):
        c.put(c.seg(x0, y0, x1, y1, 1.1) & c.circle(16, 16, 12.8), mk, 'flat', base=4)
    c.put(c.rect(14, 16, 14, 17), '#FFE0D8', 'flat')
    return done(c, '#FF5A4A')


def glimpse_of_heaven():
    c, mk, d = emblem('heaven')
    for k in range(8):
        a = k * math.pi / 4
        ray = c.seg(16 + math.cos(a) * 9, 16 + math.sin(a) * 8, 16 + math.cos(a) * 12, 16 + math.sin(a) * 11.5, 1.6)
        c.put(ray & c.circle(16, 16, 12.8), mk, 'flat', base=3)
    eye = eye_shape(c, 16, 16, 9, 5)
    mark(c, eye, mk, base=4)
    iris = c.circle(16, 16, 3.4)
    c.put(iris, Ramp(EL['heaven'][0], '#000000'), 'flat', base=2)
    c.put(c.circle(16, 16, 1.5), EL['heaven'][0][0], 'flat')
    c.put(c.rect(14, 14, 14, 14), '#FFFFFF', 'flat')
    return done(c)


# ----------------------------------------------------------------------------- secret arts
def dodge_dash():
    c, mk, d = emblem('wind', secret=True)
    for k, x in enumerate((9, 15, 21)):
        ch = c.polyline([(x - 3, 9), (x + 2, 16), (x - 3, 23)], 2.6)
        mark(c, ch, mk, base=2 + (k == 2))
    return done(c)


def appraisal_eye():
    c, mk, d = emblem('heaven', secret=True)
    eye = eye_shape(c, 14, 15, 8.5, 5)
    mark(c, eye, mk, base=4)
    c.put(c.circle(14, 15, 3), Ramp(EL['jade'][0], '#000000'), 'flat', base=3)
    c.put(c.circle(14, 15, 1.3), '#071015', 'flat')
    c.put(c.rect(13, 14, 13, 14), '#FFFFFF', 'flat')
    loupe = c.ring(20, 20, 4.5, 1.4)
    mark(c, loupe, Ramp(EL['metal'][1], '#05080B'), base=2)
    h = c.seg(23, 23, 26, 26, 2.2)
    mark(c, h, mk, base=2)
    return done(c)


def breath_control():
    c, mk, d = emblem('qi', secret=True)
    sp = c.empty()
    pts = []
    for k in range(50):
        t = k / 49.0
        r = 2 + t * 8
        a = -t * 3.2 * math.pi
        pts.append((15 + r * math.cos(a), 16 + r * math.sin(a) * 0.8))
    for a_, b_ in zip(pts, pts[1:]):
        sp |= c.seg(a_[0], a_[1], b_[0], b_[1], 2.0)
    mark(c, sp & c.circle(16, 16, 12.5), mk, base=3)
    return done(c)


def wall_step():
    c, mk, d = emblem('earth', secret=True)
    wall = c.rect(18, 4, 23, 28) & c.circle(16, 16, 12.8)
    c.put(wall, Ramp(EL['metal'][0], '#05080B'), 'flat', base=3)
    for y in range(6, 28, 4):
        c.put(c.rect(18, y, 23, y) & wall, EL['metal'][0][1], 'flat', only_on=True)
        c.put(c.rect(20 + (y // 4) % 2 * 2, y, 20 + (y // 4) % 2 * 2, y + 3) & wall, EL['metal'][0][1], 'flat',
              only_on=True)
    for (x, y) in ((12, 22), (14, 15), (12, 8)):
        f = c.ellipse(x, y, 2.4, 3.2) | c.circle(x + 0.5, y - 4.2, 1.3)
        mark(c, f, mk)
    return done(c)


# S43 movement arts.
def plunge():
    c, mk, d = emblem('earth', secret=True)
    shaft = c.seg(16, 5, 16, 17, 2.4)
    head = c.poly([(10, 14), (22, 14), (16, 22)])
    mark(c, shaft | head, mk, base=3)
    ground = c.seg(6, 25, 26, 25, 1.6) & c.circle(16, 16, 12.8)
    c.put(ground, mk, 'flat', base=1)
    for (x0, x1) in ((9, 6), (23, 26)):
        crack = c.seg(x0, 23, x1, 20, 1.2) & c.circle(16, 16, 12.8)
        c.put(crack, mk, 'flat', base=2)
    return done(c)


def falling_leaf_glide():
    c, mk, d = emblem('wood', secret=True)
    leaf = c.circle(9, 9, 14) & c.circle(22, 22, 14)
    mark(c, leaf, mk, base=3)
    c.put(c.seg(8, 7, 22, 21, 1.0) & leaf, mk[1], 'flat')
    for (x, y) in ((13, 13), (17, 17)):
        c.put(c.seg(x, y, x - 3, y + 3, 0.8) & leaf, mk[1], 'flat')
    for k, (x, y) in enumerate(((9, 23), (13, 26), (6, 19))):
        c.put(c.circle(x, y, 1.0 + 0.3 * (k == 0)) & c.circle(16, 16, 12.5), mk, 'flat', base=2)
    return done(c)


def swallow_dart():
    c, mk, d = emblem('wind', secret=True)
    wings = c.polyline([(7, 11), (13, 15), (18, 14), (25, 9)], 2.2)
    body = c.ellipse(17, 16, 4.2, 2.4)
    tail = c.polyline([(14, 17), (10, 23)], 1.6) | c.polyline([(16, 18), (15, 24)], 1.6)
    mark(c, wings | body | tail, mk, base=3)
    for y in (19, 22):
        c.put(c.seg(21, y, 26, y, 1.0) & c.circle(16, 16, 12.5), mk, 'flat', base=1)
    return done(c)


def cloud_ladder_step():
    c, mk, d = emblem('qi', secret=True)
    for (x, y) in ((10, 23), (16, 16), (22, 9)):
        puff = c.circle(x - 2.5, y, 2.8) | c.circle(x + 2.5, y, 2.8) | c.circle(x, y - 2, 3.2)
        mark(c, puff & c.circle(16, 16, 12.8), mk, base=3)
    return done(c)


def water_skimming():
    c, mk, d = emblem('water', secret=True)
    c.put(S.wave_line(c, 5, 27, 23, 1, 6) & c.circle(16, 16, 12.5), mk, 'flat', base=2)
    # Three skips across the water, each splash an arch that grows as the stone (or runner) slows.
    for k, (x, r) in enumerate(((8, 2.6), (15, 3.2), (23, 3.8))):
        splash = c.arc(x, 22, r, 1.4, 20, 160) & c.circle(16, 16, 12.5)
        mark(c, splash, mk, base=3)
    path = c.polyline([(8, 19), (11, 14), (15, 19), (19, 12), (23, 18)], 1.0) & c.circle(16, 16, 12.5)
    c.put(path, mk, 'flat', base=1)
    return done(c)


def concealment():
    c, mk, d = emblem('shadow', secret=True)
    lid = crescent(c, 16, 10, 11, 0, -3.5, 11.5) & (c.Y > 11)
    mark(c, lid & c.circle(16, 16, 12.5), mk)
    for x in (9, 12.5, 16, 19.5, 23):
        lash = c.seg(x, 20, x + (x - 16) * 0.3, 24, 1.3)
        c.put(lash, mk, 'flat', base=3)
    for (x0, y0) in ((8, 9), (15, 7)):
        c.put(S.wave_line(c, x0, x0 + 8, y0, 1, 8) & c.circle(16, 16, 12.5), mk, 'flat', base=1)
    return done(c)


# ----------------------------------------------------------------------------- S47 v1.1 weapon families
def _fan_mark(c, px, py, rad, a0, a1):
    pts = [(px, py)] + [(px + rad * math.cos(math.radians(a)), py - rad * math.sin(math.radians(a))) for a in range(a0, a1 + 1, 6)]
    return c.poly(pts)


def _note(c, x, y):
    head = c.ellipse(x, y, 2.2, 1.7)
    stem = c.seg(x + 1.8, y, x + 1.8, y - 7, 1.2)
    flag = c.seg(x + 1.8, y - 7, x + 4.2, y - 5, 1.2)
    return head | stem | flag


def mountain_cleaver():
    c, mk, d = emblem('metal')
    b = c.poly([(6, 24), (18, 12), (25, 6), (27.5, 9), (26, 15), (21, 20), (10, 28)])   # a broad sabre, edge up-right
    mark(c, b, mk, base=3)
    c.put(c.seg(5, 28, 8.5, 24.5, 2.4), mk, 'flat', base=1)
    c.recolor(c.seg(9, 25, 24, 10, 1.0) & b, mk[4])                            # the edge's gleam
    for (x0, y0, x1, y1) in ((20, 22, 24, 26), (23, 20, 27, 22), (18, 25, 20, 29)):   # the armour cracks where it lands
        c.put(c.seg(x0, y0, x1, y1, 1.1), mk, 'flat', base=4)
    return done(c)


def thunder_dao_arc():
    c, mk, d = emblem('metal')
    arc = crescent(c, 15, 17, 11, -4, 3, 11) & c.circle(16, 16, 12.8)
    mark(c, arc, mk, base=3)
    bolt = c.polyline([(18, 6), (15, 13), (19, 13), (15, 22)], 1.4)
    c.put(bolt, R['yellow'], 'flat', base=4)
    return done(c)


def gale_fan():
    c, mk, d = emblem('wind')
    fan = _fan_mark(c, 9, 24, 15, 10, 80)
    mark(c, fan & c.circle(16, 16, 12.8), mk, base=3)
    for a in range(16, 80, 12):
        rib = c.seg(9, 24, 9 + 14 * math.cos(math.radians(a)), 24 - 14 * math.sin(math.radians(a)), 0.8)
        c.recolor(rib & fan, mk[1])
    sl = speed_lines(c, [(22, 22), (24, 18), (20, 26)], 4, 20)
    c.put(sl & ~fan, mk, 'flat', base=2)
    return done(c)


def returning_crane_fan():
    c, mk, d = emblem('wind')
    fan = _fan_mark(c, 12, 19, 9, 20, 110)
    mark(c, fan, mk, base=3)
    loop = c.ring(16, 16, 10.5, 1.3) & ~c.circle(12, 13, 7) & (c.Y > 11)
    c.put(loop, mk, 'flat', base=2)
    head = c.poly([(6.5, 17), (4, 13.5), (9, 14)])
    c.put(head, mk, 'flat', base=2)
    return done(c)


def reed_song():
    c, mk, d = emblem('wood')
    notes = _note(c, 9, 22) | _note(c, 15, 18) | _note(c, 21, 21)
    mark(c, notes, mk, base=3)
    c.put(S.wave_line(c, 6, 26, 25, 1, 7) & c.circle(16, 16, 12.5), mk, 'flat', base=1)
    return done(c)


def clear_heart_melody():
    c, mk, d = emblem('water')
    flute = c.seg(7, 24, 25, 8, 2.6)
    mark(c, flute, mk, base=3)
    for t in (0.35, 0.5, 0.65):
        x, y = 7 + 18 * t, 24 - 16 * t
        c.put(c.circle(x, y, 0.7), mk, 'flat', base=0)
    for r in (5.0, 8.0):
        rip = c.ring(21, 21, r, 1.0) & (c.X > 15) & (c.Y > 15)
        c.put(rip, mk, 'flat', base=2)
    return done(c)


TECHS = [
    ('flowing_palm', flowing_palm), ('jade_thrust', jade_thrust), ('cloudpiercing_stroke', cloudpiercing_stroke),
    ('reedcutter_slash', reedcutter_slash), ('riverstone_sweep', riverstone_sweep),
    ('twin_reed_shot', twin_reed_shot), ('tiger_rush', tiger_rush), ('willow_leaf_parry', willow_leaf_parry),
    ('dragon_tail_sweep', dragon_tail_sweep), ('shadow_flick', shadow_flick), ('bell_toll_strike', bell_toll_strike),
    ('pinning_arrow', pinning_arrow), ('rising_tide', rising_tide), ('palm_wave', palm_wave),
    ('crescent_arc', crescent_arc), ('spear_lance', spear_lance), ('flying_blades', flying_blades), ('sword_release', sword_release),
    ('earthshaker_wave', earthshaker_wave), ('vine_snare', vine_snare), ('rain_of_reeds', rain_of_reeds),
    ('stone_skin', stone_skin), ('gale_step', gale_step), ('mountain_shaker', mountain_shaker),
    ('ember_burst', ember_burst), ('still_water_focus', still_water_focus), ('shadowstep_cut', shadowstep_cut),
    ('cloud_descent', cloud_descent), ('mirror_mind_spike', mirror_mind_spike),
    ('soul_lantern_ward', soul_lantern_ward), ('glimpse_of_heaven', glimpse_of_heaven), ('blood_burning', blood_burning),
    ('dodge_dash', dodge_dash), ('appraisal_eye', appraisal_eye), ('breath_control', breath_control),
    ('wall_step', wall_step), ('concealment', concealment),
    ('plunge', plunge), ('falling_leaf_glide', falling_leaf_glide), ('swallow_dart', swallow_dart),
    ('cloud_ladder_step', cloud_ladder_step), ('water_skimming', water_skimming),
    ('mountain_cleaver', mountain_cleaver), ('thunder_dao_arc', thunder_dao_arc), ('gale_fan', gale_fan),
    ('returning_crane_fan', returning_crane_fan), ('reed_song', reed_song), ('clear_heart_melody', clear_heart_melody),
]
for _id, _fn in TECHS:
    register(FAM, _id, _fn, GROUP)
