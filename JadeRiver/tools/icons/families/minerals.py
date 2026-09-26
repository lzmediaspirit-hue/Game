"""Ores, stones, spirit stones, fuel crystals and beast cores.

Templates: rock chunk (+ nuggets / veins / crystals), faceted crystal, cut gem,
sphere core.
"""
import math

import numpy as np

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


def refining_essence():
    """Salvaged Qi of a broken piece: a glowing amber drop with a spark above it."""
    c = Canvas(32)
    ramp = R['fire']
    drop = c.ellipse(16, 20, 8, 8) | c.poly([(9, 17), (16, 3), (23, 17)])
    c.put(drop, ramp, 'sphere', base=2, cx=13, cy=15, rx=10, ry=12)
    c.put(c.ellipse(13, 18, 2.2, 3.4), ramp[4], 'flat')
    S.sparkle(c, 25, 8, ramp[4], ramp[3], 2)
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
register(FAM, 'refining_essence', refining_essence, GROUP)
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


# ----------------------------------------------------------------------------- Act II · Sunscar Desert
TERRACOTTA = Ramp(['#4A200F', '#833B1D', '#B96531', '#DC9152', '#F4C088'], '#1F0C05')
FADED_VERMILION = Ramp(['#5A1A14', '#8E2E24', '#BE4A38', '#D9705A', '#EE9C84'], '#240806')
SUNGLASS = Ramp(['#5C2E0A', '#9C5A16', '#D8952E', '#F6CB64', '#FFF3C0'], '#261204')


def terracotta_shard():
    """A broken piece of a Terracotta Warden's lamellar armour, a trace of vermilion paint left on it."""
    c = Canvas(32)
    m = c.poly([(4, 9), (10, 8), (16, 7.5), (22, 7.5), (27.5, 8), (26.5, 12), (23.5, 13.5), (25, 17.5), (21, 19.5),
                (19.5, 24.5), (15.5, 23), (12.5, 28), (9.5, 24.5), (6, 25.5), (5, 20), (3.5, 16), (5.5, 13)])
    paint = (c.ellipse(9.5, 14, 4.5, 2.6) | c.ellipse(14, 18.5, 2.6, 1.6)) & erode4(m)
    side = (move(m, 1, 2) | move(m, 0, 2)) & ~m  # thickness of the broken clay
    c.put(side, TERRACOTTA, 'flat', base=1)
    c.put(m, TERRACOTTA, 'ray', base=2, sep=True, sep_col=TERRACOTTA[0])
    # narrow lamellae laced in rows that curve gently around the body
    cx, cy = 16.0, -24.0
    u = np.arctan2(c.X - cx, c.Y - cy)
    v = np.hypot(c.X - cx, c.Y - cy)
    v0, pitch = 34.0, 6.0
    for r in range(3):
        band = m & (v >= v0 + r * pitch) & (v < v0 + (r + 1) * pitch)
        du = 4.4 / (v0 + (r + 0.5) * pitch)
        for k in range(-8, 9):
            cell = band & (u >= (k - 0.5) * du) & (u < (k + 0.5) * du)
            if cell.sum() < 4:
                continue
            ys, xs = np.nonzero(cell)
            lit = (xs.mean() + ys.mean()) < 28
            c.put(cell, TERRACOTTA, 'ray', base=3 if lit else 2, sep=True, sep_col=TERRACOTTA[1])
            c.put(cell & paint, FADED_VERMILION, 'ray', base=2)
            y = ys.min() + 1
            row = xs[ys == y]
            if len(row) >= 3 and (ys.max() - ys.min()) >= 4:
                c.put(c.rect(row.min() + 1, y, row.min() + 1, y) & erode4(m), TERRACOTTA[4], 'flat', out=TERRACOTTA.out)
    rows = m & (v >= v0)
    c.put(rows & (np.floor((v - v0) / pitch) != np.floor((move(v, 0, 1) - v0) / pitch)) & erode4(m), TERRACOTTA[0],
          'flat', out=TERRACOTTA.out)
    hem = m & (v < v0)
    c.put(hem, TERRACOTTA, 'ray', base=3, sep=True)
    band = hem & erode4(m) & (v >= v0 - 2.2) & (v < v0 - 0.8) & (np.floor(u / 0.09) % 3 != 2) & (c.X < 20)
    c.put(band, FADED_VERMILION, 'flat', base=3)
    crack = c.bres_path([(25, 14), (21, 16), (19, 19), (20, 22)])
    c.put(crack & m, TERRACOTTA[0], 'flat', out=TERRACOTTA.out)
    c.outline()
    return c


def sunglass_ore():
    """Amber desert glass the sun fused out of the dunes, a crust of sand still on one side."""
    c = Canvas(32)
    m = c.poly([(5, 20), (6.5, 13), (11, 8), (17, 5), (23, 6), (27.5, 11), (28, 18), (25.5, 24), (19, 27), (12, 28),
                (6.5, 26)])
    # through-lit glass: dark on the near side, light pooling on the far side
    c.put(m, SUNGLASS, 'sphere', base=2, light=(0.6, 0.55, 0.6))
    top = c.poly([(6.5, 13), (11, 8), (17, 5), (23, 6), (27.5, 11), (21, 12.5), (13, 14.5)]) & m
    c.put(top, SUNGLASS, 'flat', base=3)
    c.put(S.outline_only(top) & ~S.outline_only(m) & (c.Y > 10), SUNGLASS[1], 'flat', out=SUNGLASS.out)
    c.put(c.poly([(17, 5), (23, 6), (20, 9)]) & top, SUNGLASS, 'flat', base=4)
    c.put(c.ellipse(21, 20, 3.0, 2.2) & m, SUNGLASS, 'flat', base=4)
    c.put(c.bres_path([(14, 17), (16, 20), (15, 23)]) & erode4(m), SUNGLASS[1], 'flat', out=SUNGLASS.out)
    crust = m & c.poly([(3, 18), (6, 21), (8, 19), (10, 22), (13, 21), (15, 24), (18, 23), (20, 27), (22, 31), (3, 31)])
    crust |= (c.circle(5, 24, 1.8) | c.circle(8, 27.5, 1.6) | c.circle(13, 28.5, 1.4))
    c.put(crust, R['sand'], 'ray', base=2, sep=True)
    c.pxs([(7, 23), (11, 25), (15, 26), (6, 26)], R['sand'][0])
    c.pxs([(9, 23), (13, 24), (5, 22)], R['sand'][4])
    c.put(c.bres(9, 12, 12, 9) | c.rect(14, 7, 15, 7), '#FFFFFF', 'flat')
    c.pxs([(17, 16), (24, 15), (19, 23)], SUNGLASS[4])
    c.outline()
    c.glow('#FFC870', (80, 35))
    S.sparkle(c, 21, 20, '#FFFFFF', SUNGLASS[4], 1)
    S.sparkle(c, 26, 4, '#FFFFFF', SUNGLASS[3], 2)
    return c


register(FAM, 'terracotta_shard', terracotta_shard, GROUP)
register(FAM, 'sunglass_ore', sunglass_ore, GROUP)



# ----------------------------------------------------------------------------- Act II · Starsea
COMET_GLOW = '#BFE6FF'


def comet_iron():
    """A bar of comet iron: pale blue-grey metal with a bright comet streak along it; it rings."""
    c = Canvas(32)
    ramp = R['cometiron']
    end = c.poly([(23, 12.5), (26, 7), (28, 18.5), (25, 24.5)])
    c.put(end, ramp, 'flat', base=1)
    front = c.poly([(6, 12.5), (23, 12.5), (25, 24.5), (4, 24.5)])
    c.put(front, ramp, 'ray', base=2, sep=True, sep_col=ramp[0])
    top = c.poly([(9, 7), (26, 7), (23, 12.5), (6, 12.5)])
    c.put(top, ramp, 'bevel', base=3, sep=True, sep_col=ramp[1])
    c.put(c.rect(7, 12, 22, 12), ramp[4], 'flat', out=ramp.out)
    # the comet: a white head near the right end, its tail streaming back along the bar
    tail = S.taper_curve(c, (5, 22.5), (12, 20.5), (21, 17), 0.9, 3.2)
    c.put(tail & erode4(front), '#7FC4EA', 'flat', out=ramp.out)
    c.put(S.taper_curve(c, (9, 21.5), (14, 19.6), (21, 17), 0.7, 2.1) & erode4(front), '#BFE9FF', 'flat', out=ramp.out)
    c.put(c.rect(19, 16, 22, 17) & front, '#FFFFFF', 'flat', out=ramp.out)
    c.outline()
    c.glow(COMET_GLOW, (70, 30))
    S.sparkle(c, 22, 16, '#FFFFFF', '#BFE9FF', 1)
    return c


register(FAM, 'comet_iron', comet_iron, GROUP)



# ----------------------------------------------------------------------------- S46 beast cores
_CORE_RAMP = {"fire": "fire", "water": "cyan", "wood": "leaf", "earth": "warmstone", "wind": "mist", "thunder": "violet", "soul": "qi",
              "metal": "silver", "star": "gold", "space": "plum"}
_CORE_GLOW = {"fire": "#FF8A4A", "water": "#6FD6FF", "wood": "#7FE08A", "earth": "#E0B870", "wind": "#CFE8F0", "thunder": "#B98CFF", "soul": "#A8F0FF",
              "metal": "#E8EEF2", "star": "#FFF0B0", "space": "#B49CFF"}


def _beast_core(el, tier):
    """A beast core: a sphere in its element's colour with a bright heart, its glow widening with the rank tier."""
    c = Canvas(32)
    rad = {"low": 8.5, "mid": 9.5, "high": 10.5, "peak": 11.5}[tier]
    ramp = R[_CORE_RAMP[el]]
    m = core(c, 16, 17, rad, ramp)
    heart = c.circle(16, 17, rad * 0.38)
    c.put(heart & m, ramp, 'sphere', base=3)
    c.put(c.ellipse(12.5, 12.5, 2.2, 1.5) & m, ramp[4], 'flat')
    if tier in ("high", "peak"):
        c.put(c.ring(16, 17, rad - 2.5, 1) & c.sector(16, 17, rad, 200, 330), ramp[4], 'flat', only_on=True)
    c.outline()
    bands = {"low": (), "mid": (70,), "high": (110, 45), "peak": (150, 90, 40)}[tier]
    if bands:
        c.glow(_CORE_GLOW[el], bands)
    if tier == "peak":
        S.sparkle(c, 26, 6, '#FFFFFF', ramp[3], 2)
    return c


for _el in _CORE_RAMP:
    for _tier in ("low", "mid", "high", "peak"):
        register(FAM, '%s_core_%s' % (_el, _tier), (lambda e, t: lambda: _beast_core(e, t))(_el, _tier), GROUP)


# ----------------------------------------------------------------------------- Act III · Lantern Star Field
from palette import STAR_GLOW  # noqa: E402

VIOLET_GLASS = Ramp(['#2A1F52', '#46398A', '#7462B8', '#A898DE', '#E6DEFA'], '#120C26')
TEAL_GLASS = Ramp(['#0E3E4A', '#1A6E7A', '#36A4A8', '#7CD8CC', '#D4FAF0'], '#06181E')
CLEAR = Ramp(['#4A5470', '#8290B0', '#BCC8DC', '#E4ECF6', '#FFFFFF'], '#161C2C')
DEEP_JADE = Ramp(['#0A2A22', '#12473A', '#1D6B55', '#3A9B7C', '#9ADCBF'], '#04140F')


def star_shard():
    """A sharp chip of fallen starlight: a pale-gold crystal broken into three facets, a glint caught inside."""
    c = Canvas(32)
    ramp = R['starlight']
    A, B, C, D = (25.5, 3), (27, 13.5), (20.5, 24), (13, 29)
    E, F, G, H = (10.5, 25.5), (5, 25.5), (5.5, 17), (12.5, 8)
    P = (16.5, 16)   # where the three facets meet
    m = c.poly([A, B, C, D, E, F, G, H])
    c.put(m, ramp, 'flat', base=1)
    top = c.poly([H, A, P, G]) & m
    right = c.poly([A, B, C, P]) & m
    low = m & ~top & ~right
    c.put(low, ramp, 'ray', base=2, bands=((0.3, 0), (0.75, -1), (9, -2)))
    c.put(right, ramp, 'ray', base=3, bands=((0.35, 0), (0.8, -1), (9, -1)))
    c.put(top, ramp, 'ray', base=4, bands=((0.5, 0), (9, -1)))
    # ridges: bright where the lit face meets the others
    c.put(c.bres_path([(int(A[0]), int(A[1]) + 1), (16, 15)]) & m, '#FFFFFF', 'flat', out=ramp.out)
    c.put(c.bres_path([(16, 16), (7, 18)]) & m, ramp[4], 'flat', out=ramp.out)
    c.put(c.bres_path([(17, 17), (20, 23)]) & m, ramp[1], 'flat', out=ramp.out)
    c.outline()
    c.glow(STAR_GLOW, (90, 40))
    S.sparkle(c, 13, 22, '#FFFFFF', ramp[4], 1)
    return c


def driftglass():
    """A smooth tumbled lump of sea glass: frosted violet on the near side, teal light pooling where it shines
    through."""
    c = Canvas(32)
    through = (0.6, 0.55, 0.6)   # through-lit: the near side darker, light gathering toward the far side
    m = c.poly([(3.5, 17.5), (5.5, 12.5), (10, 9.5), (16, 8.5), (21.5, 9.5), (25.5, 12), (27, 16.5), (25.5, 21),
                (21, 24.5), (14, 25.5), (7.5, 24.5), (4, 21.5)])
    c.put(m, VIOLET_GLASS, 'sphere', base=2, light=through)
    teal = m & ((c.xi + c.yi) >= 30)
    c.put(teal, TEAL_GLASS, 'sphere', base=2, cx=15.5, cy=16.5, rx=12, ry=9, light=through)
    # the light passing through gathers in a bright crescent inside the far edge
    inner = erode4(erode4(m))
    cres = inner & ~move(inner, -2, -2) & ((c.xi + c.yi) >= 27)
    c.put(cres, TEAL_GLASS, 'flat', base=3)
    c.put(cres & ~move(inner, -3, -3) & ((c.xi + c.yi) >= 32), TEAL_GLASS, 'flat', base=4)
    # frosted skin on the lit rim, one small wet gleam
    rim = S.outline_only(m) & ((c.xi + c.yi) <= 24)
    c.put(rim, VIOLET_GLASS, 'flat', base=3)
    c.put(c.bres(7, 13, 9, 11) | c.rect(10, 10, 12, 10), '#FFFFFF', 'flat')
    c.put(c.rect(8, 15, 8, 15), VIOLET_GLASS[4], 'flat')
    # a smaller tumbled bead of the same glass in front
    bead = c.poly([(19.5, 25), (21.5, 21.5), (25.5, 20.5), (28.5, 22.5), (28.5, 26.5), (25, 28.5), (21, 28)])
    c.put(bead, TEAL_GLASS, 'sphere', base=2, sep=True, light=through)
    c.put(bead & ((c.xi + c.yi) <= 44), VIOLET_GLASS, 'sphere', base=2, cx=24, cy=24.5, rx=5, ry=4.5, light=through)
    c.put(c.rect(22, 22, 23, 22), '#FFFFFF', 'flat')
    c.outline()
    c.glow('#9C8CE0', (45,))
    return c


def sage_crystal():
    """Sage Crystal (currency): a clear cut crystal with warm gold light burning at its core."""
    c = Canvas(32)
    cx, cy, rw, rh = 16, 16.5, 11.5, 12.5
    k = 0.42
    outer = [(cx - rw * k, cy - rh), (cx + rw * k, cy - rh), (cx + rw, cy - rh * k), (cx + rw, cy + rh * k),
             (cx + rw * k, cy + rh), (cx - rw * k, cy + rh), (cx - rw, cy + rh * k), (cx - rw, cy - rh * k)]
    m = c.poly(outer)
    c.put(m, CLEAR, 'flat', base=2)
    t = 0.5
    inner = [(cx + (x - cx) * t, cy + (y - cy) * t) for x, y in outer]
    # crown facets: lit to the upper left, dark to the lower right
    L = (-0.7071, -0.7071)
    for i in range(8):
        a, b = outer[i], outer[(i + 1) % 8]
        ta, tb = inner[i], inner[(i + 1) % 8]
        mx, my = (a[0] + b[0]) / 2 - cx, (a[1] + b[1]) / 2 - cy
        d = (mx * L[0] + my * L[1]) / (math.hypot(mx, my) or 1)
        lvl = 4 if d > 0.75 else 3 if d > 0.2 else 2 if d > -0.35 else 1 if d > -0.8 else 0
        c.put(c.poly([a, b, tb, ta]) & m, CLEAR, 'flat', base=lvl)
    # the table holds the warm core light: pale gold round a white-hot heart
    gold = R['starlight']
    tab = c.poly(inner)
    c.put(tab, gold, 'flat', base=2)
    c.put(erode4(tab), gold, 'flat', base=3)
    c.put(c.ellipse(cx, cy, 2.6, 3.0), gold, 'flat', base=4)
    c.put(c.rect(15, 16, 16, 16), '#FFFFFF', 'flat')
    # warm light caught in the facets below the core
    c.pxs([(12, 24), (20, 24), (24, 19), (8, 19)], gold[2])
    c.put(c.rect(10, 7, 12, 7) | c.rect(9, 8, 9, 9), '#FFFFFF', 'flat')
    c.outline()
    c.glow(STAR_GLOW, (120, 50))
    S.sparkle(c, 27, 5, '#FFFFFF', gold[3], 2)
    return c


def star_jade():
    """Star Jade (currency): a polished bi disc of deep jade, a star-white star inlaid round its hole."""
    c = Canvas(32)
    cx, cy = 16, 15.5
    side = c.ellipse(cx, cy + 2, 12, 11)
    c.put(side, DEEP_JADE, 'flat', base=0)
    top = c.ellipse(cx, cy, 12, 11)
    c.put(top, DEEP_JADE, 'sphere', base=2, sep=True, cx=12.5, cy=11.5, rx=15, ry=14)
    pts = []
    for k in range(8):
        a = math.radians(90 - k * 45)
        r = 9.0 if k % 2 == 0 else 4.4
        pts.append((cx + math.cos(a) * r, cy - math.sin(a) * r * 0.93))
    star = c.poly(pts) & erode4(top)
    c.put(star, R['starlight'], 'ray', base=3, sep=True, sep_col=DEEP_JADE[0],
          bands=((0.35, 1), (0.75, 0), (9, -1)))
    hole = c.ellipse(cx, cy, 2.6, 2.5)
    c.put(dilate4(hole) & ~hole, DEEP_JADE, 'flat', base=0)
    c.erase(hole)
    # polish: a bright arc on the lit rim
    c.put(c.arc(cx, cy, 11, 1.3, 105, 165, 10) & top, DEEP_JADE[4], 'flat')
    c.outline()
    c.glow(STAR_GLOW, (45,))
    return c


register(FAM, 'star_shard', star_shard, GROUP)
register(FAM, 'driftglass', driftglass, GROUP)
register(FAM, 'sage_crystal', sage_crystal, GROUP)
register(FAM, 'star_jade', star_jade, GROUP)
