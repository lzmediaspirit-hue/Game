"""Ores, stones, spirit stones, fuel crystals and beast cores.

Templates: rock chunk (+ nuggets / veins / crystals), faceted crystal, cut gem,
sphere core.
"""
import math

from pix import Canvas, Ramp, dilate4, erode4, move
from palette import R
from registry import register
import shapes as S

FAM, GROUP = 'items', 'minerals'


# ----------------------------------------------------------------------------- templates
def rock(c, pts, ramp, top_pts=None, facet_lines=()):
    m = c.poly(pts)
    c.put(m, ramp, 'ray')
    if top_pts:
        c.put(c.poly(top_pts) & m, ramp, 'flat', base=3)
    for (a, b) in facet_lines:
        c.put(c.bres(*a, *b) & erode4(m), ramp[1], 'flat', out=ramp.out)
    return m


def nugget(c, x, y, r, ramp, clip=None):
    m = c.circle(x, y, r)
    if clip is not None:
        m &= clip
    c.put(m, ramp, 'sphere', sep=True)
    return m


def crystal(c, bx, by, angle, L, w, ramp, sep=True):
    """Faceted crystal prism with a pointed tip; lit face on the upper-left side."""
    a = math.radians(angle)
    dx, dy = math.cos(a), -math.sin(a)
    px, py = -dy, dx
    B = (bx, by)
    Sx, Sy = bx + dx * L * 0.68, by + dy * L * 0.68
    T = (bx + dx * L, by + dy * L)
    bl = (bx - px * w, by - py * w)
    br = (bx + px * w, by + py * w)
    sl = (Sx - px * w, Sy - py * w)
    sr = (Sx + px * w, Sy + py * w)
    whole = c.poly([bl, sl, T, sr, br])
    c.put(whole, ramp, 'flat', base=1, sep=sep)
    lit_left = (px * -1 + py * -1) > 0  # which side faces the upper-left light
    faceL = c.poly([bl, B, (Sx, Sy), sl]) & whole
    faceR = c.poly([B, br, sr, (Sx, Sy)]) & whole
    tipL = c.poly([sl, (Sx, Sy), T]) & whole
    tipR = c.poly([(Sx, Sy), sr, T]) & whole
    if lit_left:
        c.put(faceL, ramp, 'flat', base=3)
        c.put(faceR, ramp, 'flat', base=1)
        c.put(tipL, ramp, 'flat', base=4)
        c.put(tipR, ramp, 'flat', base=2)
    else:
        c.put(faceR, ramp, 'flat', base=3)
        c.put(faceL, ramp, 'flat', base=1)
        c.put(tipR, ramp, 'flat', base=4)
        c.put(tipL, ramp, 'flat', base=2)
    return whole


def cut_gem(c, cx, cy, rw, rh, ramp, table=0.45):
    """Octagonal cut gem seen from the front: table, crown facets, dark pavilion."""
    k = 0.42
    outer = [(cx - rw * k, cy - rh), (cx + rw * k, cy - rh), (cx + rw, cy - rh * k), (cx + rw, cy + rh * k),
             (cx + rw * k, cy + rh), (cx - rw * k, cy + rh), (cx - rw, cy + rh * k), (cx - rw, cy - rh * k)]
    m = c.poly(outer)
    c.put(m, ramp, 'ray', base=2, sep=True)
    tw, th = rw * table, rh * table
    tab = c.poly([(cx - tw * k * 1.4, cy - th), (cx + tw * k * 1.4, cy - th), (cx + tw, cy - th * k),
                  (cx + tw, cy + th * k), (cx + tw * k * 1.4, cy + th), (cx - tw * k * 1.4, cy + th),
                  (cx - tw, cy + th * k), (cx - tw, cy - th * k)])
    c.put(tab, ramp, 'dgrad', base=3, bands=((0.35, 1), (0.75, 0), (9, -1)))
    # facet spokes from table corners to outer corners
    for (ox, oy), sx, sy in ((outer[0], -1, -1), (outer[3], 1, 1), (outer[4], 1, 1), (outer[7], -1, -1)):
        c.put(c.bres(int(cx + sx * tw * 0.8), int(cy + sy * th * 0.8), int(ox), int(oy)) & erode4(m),
              ramp[1] if sx > 0 else ramp[3], 'flat', out=ramp.out)
    return m


def core(c, cx, cy, r, ramp, glow=None):
    m = c.circle(cx, cy, r)
    c.put(m, ramp, 'sphere', base=2)
    return m


# ----------------------------------------------------------------------------- ores
def copper_ore():
    c = Canvas(32)
    rk = R['warmstone']
    m = rock(c, [(4, 20), (8, 10), (15, 6), (24, 8), (29, 16), (27, 26), (17, 29), (7, 27)], rk,
             top_pts=[(8, 11), (15, 7), (23, 9), (19, 14), (11, 15)],
             facet_lines=[((11, 15), (19, 14)), ((19, 14), (26, 19)), ((11, 15), (7, 24))])
    for (x, y, r) in ((12.5, 18.5, 3.4), (21.5, 20.5, 2.8), (18, 11.5, 2.3), (8.5, 22.5, 1.8), (22, 13, 1.5)):
        nugget(c, x, y, r, R['copper'], clip=erode4(m))
    patina = c.ellipse(25, 24, 2.2, 1.4) & erode4(m)
    c.put(patina, R['jade'], 'flat', base=3)
    c.outline()
    return c


def riverstone():
    c = Canvas(32)
    rk = R['stone']
    back = c.ellipse(20, 12.5, 8.5, 5.5)
    c.put(back, R['warmstone'], 'sphere')
    front = c.ellipse(14.5, 20.5, 12, 7.5)
    c.put(front, Ramp(['#27353C', '#3F5560', '#62808C', '#93AFB8', '#CFE2E4'], '#0E171B'), 'sphere', sep=True)
    band = (c.ellipse(15, 26, 14, 6) & ~c.ellipse(15, 26.8, 14, 5.2)) & front
    c.put(band, R['paper'], 'flat', base=3)
    c.put(c.ellipse(11, 16, 3, 1.3) & front, '#E7F4F2', 'flat')
    c.put(c.ellipse(16.5, 9.5, 2, 1) & back, R['warmstone'][4], 'flat')
    c.outline()
    return c


def jadeiron():
    c = Canvas(32)
    rk = R['iron']
    m = rock(c, [(3, 19), (9, 9), (17, 5), (26, 9), (29, 18), (24, 27), (13, 29), (5, 26)], rk,
             top_pts=[(9, 10), (17, 6), (25, 10), (18, 14), (11, 15)],
             facet_lines=[((11, 15), (18, 14)), ((18, 14), (25, 20)), ((11, 15), (7, 24))])
    vein = S.bez_line(c, (6, 22), (14, 15), (26, 14), 2.2) | S.bez_line(c, (14, 18), (18, 24), (22, 26), 1.6)
    c.put(vein & erode4(m), R['jade'], 'flat', base=2)
    c.put(S.bez_line(c, (6, 21), (14, 14), (26, 13)) & vein & erode4(m), R['jade'][3], 'flat', out=R['jade'].out)
    crystal(c, 16, 13, 70, 9, 2.4, R['jade'])
    crystal(c, 21, 14, 35, 6.5, 2.0, R['jade'])
    c.outline()
    return c


def spirit_stone_shard():
    c = Canvas(32)
    ramp = R['qi']
    crystal(c, 12, 28, 75, 25, 5.2, ramp)
    crystal(c, 20, 27, 45, 12, 3.0, ramp)
    chip = c.poly([(5, 25), (8, 21), (10, 26)])
    c.put(chip, ramp, 'flat', base=3, sep=True)
    S.sparkle(c, 23, 7, ramp[4], ramp[3], 2)
    c.outline()
    return c


def cloudsteel_ore():
    c = Canvas(32)
    rk = R['porcelain']
    m = rock(c, [(4, 22), (7, 15), (13, 12), (20, 14), (28, 19), (27, 27), (16, 29), (6, 28)], R['hollow'],
             top_pts=[(7, 16), (13, 13), (20, 15), (16, 19), (9, 20)],
             facet_lines=[((9, 20), (16, 19)), ((16, 19), (24, 24))])
    del rk
    crystal(c, 13, 18, 88, 15, 3.4, R['cloudsteel'])
    crystal(c, 19, 19, 55, 11, 3.0, R['cloudsteel'])
    crystal(c, 9, 20, 130, 8, 2.4, R['cloudsteel'])
    S.sparkle(c, 25, 7, R['cloud'][4], R['cloudsteel'][3], 2)
    c.outline()
    return c


def mystic_ore():
    c = Canvas(32)
    m = rock(c, [(4, 22), (8, 14), (14, 12), (22, 13), (28, 20), (26, 27), (15, 29), (6, 28)], R['shadow'],
             top_pts=[(8, 15), (14, 13), (21, 14), (16, 18), (10, 19)])
    crystal(c, 14, 19, 95, 16, 3.6, R['mistjade'])
    crystal(c, 20, 20, 60, 11, 2.8, R['mistjade'])
    crystal(c, 9, 21, 135, 8, 2.2, R['mistjade'])
    c.outline()
    c.glow('#9B78D1', (110, 45))
    return c



def stormsteel_ore():
    c = Canvas(32)
    m = rock(c, [(4, 23), (7, 15), (13, 12), (21, 13), (28, 19), (27, 27), (16, 29), (6, 28)], R['shadow'],
             top_pts=[(7, 16), (13, 13), (21, 14), (16, 19), (9, 20)],
             facet_lines=[((9, 20), (16, 19)), ((16, 19), (24, 24))])
    crystal(c, 14, 18, 92, 16, 3.4, R['storm'])
    crystal(c, 20, 19, 58, 11, 2.8, R['storm'])
    crystal(c, 9, 20, 132, 8, 2.2, R['storm'])
    bolt = c.bres_path([(15, 6), (13, 10), (16, 11), (14, 15)])
    c.put(bolt & c.a, '#F4FBFF', 'flat')
    c.outline()
    c.glow('#7FD4FF', (100, 40))
    return c

# ----------------------------------------------------------------------------- spirit stones
def _spirit_stone(level):
    c = Canvas(32)
    ramp = R['qi'] if level < 2 else Ramp(['#155E76', '#2A93B0', '#5ED6E6', '#B6F6F6', '#FFFFFF'], '#05202D')
    if level == 0:
        cut_gem(c, 16, 18, 9, 8, R['jade'])
        c.put(c.rect(12, 14, 13, 14), R['jade'][4], 'flat')
    elif level == 1:
        cut_gem(c, 16, 17, 11.5, 10, ramp)
        c.put(c.rect(10, 11, 12, 11) | c.rect(10, 12, 10, 12), ramp[4], 'flat')
        S.sparkle(c, 25, 7, ramp[4], ramp[3], 2)
    else:
        cut_gem(c, 16, 16.5, 12.5, 11.5, ramp)
        c.put(c.rect(9, 10, 12, 10) | c.rect(9, 11, 9, 12), ramp[4], 'flat')
        # gold setting prongs
        for (x, y) in ((6, 16), (26, 16), (16, 5), (16, 28)):
            c.put(c.circle(x + 0.5, y + 0.5, 1.6), R['gold'], 'sphere', sep=True)
    c.outline()
    if level == 2:
        c.glow('#8AEBEE', (120, 50))
        S.sparkle(c, 26, 6, '#FFFFFF', ramp[3], 2)
        S.sparkle(c, 5, 26, '#FFFFFF', ramp[3], 1)
    return c


def _fuel(level):
    c = Canvas(32)
    ramp = R['fire']
    if level == 0:
        crystal(c, 15, 28, 82, 22, 5.0, ramp)
        base = c.ellipse(15, 28, 6, 2)
        c.put(base, R['warmstone'], 'ray', sep=True)
    else:
        crystal(c, 9, 27, 115, 14, 3.4, ramp)
        crystal(c, 21, 27, 60, 15, 3.6, ramp)
        crystal(c, 15.5, 29, 88, 25, 5.0, ramp)
        base = c.ellipse(16, 28.5, 10, 2.2)
        c.put(base, R['warmstone'], 'ray', sep=True)
        fl = S.flame(c, 26, 10, 4, 7, 0.5)
        c.put(fl, R['fire'], 'vgrad', base=3, bands=((0.35, 1), (0.75, 0), (9, -1)))
    c.outline()
    return c


def formation_stone():
    c = Canvas(32)
    disc = c.ellipse(16, 18, 13, 9.5)
    side = c.ellipse(16, 20.5, 13, 9.5)
    c.put(side, R['stone'], 'flat', base=1)
    c.put(disc, R['stone'], 'ray', base=3, sep=True)
    ring = c.ring(16, 18, 9.5, 1.2, 6.8)
    c.put(ring, R['jade'], 'flat', base=3)
    ring2 = c.ring(16, 18, 5, 1.0, 3.6)
    c.put(ring2, R['jade'], 'flat', base=3)
    # trigram ticks between the rings
    for k in range(8):
        a = k * math.pi / 4
        x, y = 16 + math.cos(a) * 7.3, 18 + math.sin(a) * 5.2
        c.put(c.circle(x, y, 0.9), R['jade'], 'flat', base=4)
    c.put(c.circle(16, 18, 1.3), R['qi'], 'flat', base=4)
    c.outline()
    return c


def guardian_stone():
    c = Canvas(32)
    base = c.poly([(5, 29), (7, 25), (25, 25), (27, 29)])
    c.put(base, R['stone'], 'ray')
    stele = c.poly([(8, 26), (8, 7), (10, 4), (22, 4), (24, 7), (24, 26)])
    c.put(stele, R['stone'], 'ray', base=2, sep=True)
    # carved shield glyph
    sh = c.poly([(11, 9), (21, 9), (21, 15), (16, 22), (11, 15)])
    c.put(sh, R['stone'], 'flat', base=1)
    shin = c.poly([(12.5, 10.5), (19.5, 10.5), (19.5, 14.8), (16, 19.8), (12.5, 14.8)])
    c.put(shin, R['jade'], 'ray', base=3)
    c.put(c.rect(15, 11, 16, 17) & shin, R['jade'][1], 'flat', out=R['jade'].out)
    moss = c.ellipse(9, 25, 3.5, 1.5) | c.ellipse(23, 25.5, 3, 1.3)
    c.put(moss, R['moss'], 'ray', base=3)
    c.outline()
    return c


def _core(kind):
    c = Canvas(32)
    if kind == 'jade':
        m = core(c, 16, 16, 11, R['jade'])
        sw = c.arc(16, 16, 6, 1.4, 30, 250) | c.arc(18, 17, 3, 1.2, 200, 60)
        c.put(sw & m, R['jade'], 'flat', base=4)
        c.put(c.ellipse(11.5, 10.5, 2.4, 1.6), R['jade'][4], 'flat')
        c.outline()
        c.glow('#67D6BD', (110, 45))
    elif kind == 'pebble':
        m = core(c, 16, 17, 10.5, R['warmstone'])
        cr = c.bres_path([(9, 13), (13, 16), (12, 20), (16, 23)]) | c.bres_path([(13, 16), (19, 14), (22, 17)])
        c.put(cr & erode4(m), R['warmstone'][0], 'flat', out=R['warmstone'].out)
        glow = c.bres_path([(13, 17), (12, 20)]) | c.bres_path([(15, 15), (19, 14)])
        c.put(glow & erode4(m), R['gold'], 'flat', base=3)
        c.put(c.ellipse(12, 11.5, 2.4, 1.4), R['warmstone'][4], 'flat')
        c.outline()
    else:
        ramp = Ramp(['#12301F', '#1F5236', '#3A8452', '#7DC47A', '#D2F2B0'], '#07150C')
        m = core(c, 16, 16, 11, ramp)
        pupil = c.ellipse(16, 16, 1.6, 6.5)
        iris = c.ellipse(16, 16, 5, 7.5) & m
        c.put(iris, R['yellow'], 'ray', base=3)
        c.put(pupil, R['ink'], 'flat', base=1)
        c.put(c.ellipse(11, 10, 2.4, 1.6), ramp[4], 'flat')
        # coiled scale ring
        c.put(c.ring(16, 16, 10, 1) & c.sector(16, 16, 12, 200, 340), ramp[1], 'flat', only_on=True)
        c.outline()
        c.glow('#9B78D1', (100, 40))
    return c


register(FAM, 'copper_ore', copper_ore, GROUP)
register(FAM, 'riverstone', riverstone, GROUP)
register(FAM, 'jadeiron', jadeiron, GROUP)
register(FAM, 'spirit_stone_shard', spirit_stone_shard, GROUP)
register(FAM, 'cloudsteel_ore', cloudsteel_ore, GROUP)
register(FAM, 'mystic_ore', mystic_ore, GROUP)
register(FAM, 'stormsteel_ore', stormsteel_ore, GROUP)
register(FAM, 'spirit_stone_low', lambda: _spirit_stone(0), GROUP)
register(FAM, 'spirit_stone_mid', lambda: _spirit_stone(1), GROUP)
register(FAM, 'spirit_stone_high', lambda: _spirit_stone(2), GROUP)
register(FAM, 'fuel_crystal_low', lambda: _fuel(0), GROUP)
register(FAM, 'fuel_crystal_mid', lambda: _fuel(1), GROUP)
register(FAM, 'formation_stone', formation_stone, GROUP)
register(FAM, 'guardian_stone', guardian_stone, GROUP)
register(FAM, 'jade_core', lambda: _core('jade'), GROUP)
register(FAM, 'pebble_core', lambda: _core('pebble'), GROUP)
register(FAM, 'serpent_core', lambda: _core('serpent'), GROUP)


def sentinel_core():
    """The heart of a River Sentinel: a river pebble polished to aquamarine, water swirling inside."""
    c = Canvas(32)
    ramp = Ramp(['#0F3A44', '#1B6070', '#2E97A4', '#74D2D0', '#D4FAF2'], '#051A20')
    m = core(c, 16, 16, 11, ramp)
    sw = c.arc(16, 16, 6, 1.4, 20, 240) | c.arc(17, 18, 3, 1.2, 190, 50)
    c.put(sw & m, ramp, 'flat', base=4)
    c.put(c.ellipse(11.5, 10.5, 2.4, 1.6), ramp[4], 'flat')
    c.outline()
    c.glow('#74D2D0', (110, 45))
    return c


register(FAM, 'sentinel_core', sentinel_core, GROUP)

