"""Qi jades (inlay gems): one faceted-gem template, a distinct cut and colour per
jade so they read apart even in greyscale."""
import math

from pix import Canvas, Ramp, erode4
from palette import R
from registry import register
import shapes as S

FAM, GROUP = 'items', 'qi_jades'


def faceted(c, outer, ramp, table=0.5, bezel=None):
    cx = sum(p[0] for p in outer) / len(outer)
    cy = sum(p[1] for p in outer) / len(outer)
    inner = [(cx + (x - cx) * table, cy + (y - cy) * table) for x, y in outer]
    whole = c.poly(outer)
    if bezel is not None:
        from pix import dilate4
        c.put(dilate4(dilate4(whole)), bezel, 'ray', base=3)
    c.put(whole, ramp, 'flat', base=2, sep=bezel is not None)
    n = len(outer)
    L = (-0.7071, -0.7071)
    for i in range(n):
        a, b = outer[i], outer[(i + 1) % n]
        ta, tb = inner[i], inner[(i + 1) % n]
        mx, my = (a[0] + b[0]) / 2 - cx, (a[1] + b[1]) / 2 - cy
        ln = math.hypot(mx, my) or 1
        d = (mx * L[0] + my * L[1]) / ln
        lvl = 4 if d > 0.75 else 3 if d > 0.2 else 2 if d > -0.35 else 1 if d > -0.8 else 0
        facet = c.poly([a, b, tb, ta]) & whole
        c.put(facet, ramp, 'flat', base=lvl)
    tab = c.poly(inner)
    c.put(tab, ramp, 'dgrad', base=3, bands=((0.3, 1), (0.7, 0), (9, -1)))
    return whole


def _poly_n(cx, cy, rx, ry, n, rot=0.0):
    return [(cx + rx * math.cos(rot + 2 * math.pi * k / n), cy + ry * math.sin(rot + 2 * math.pi * k / n))
            for k in range(n)]


def body_jade():
    c = Canvas(32)
    ramp = Ramp(['#4A1410', '#84281C', '#C24A2E', '#EC8A58', '#FFD2A6'], '#200806')
    outer = [(9, 5), (23, 5), (27, 9), (27, 23), (23, 27), (9, 27), (5, 23), (5, 9)]
    faceted(c, outer, ramp, 0.5, R['gold'])
    c.outline()
    return c


def swift_jade():
    c = Canvas(32)
    ramp = Ramp(['#0E3A2C', '#1C6A4A', '#34A070', '#7CDCA2', '#D8FFE6'], '#061A12')
    outer = [(16, 2), (21, 8), (24, 16), (21, 24), (16, 30), (11, 24), (8, 16), (11, 8)]
    faceted(c, outer, ramp, 0.45, R['gold'])
    c.outline()
    return c


def essence_jade():
    c = Canvas(32)
    ramp = Ramp(['#5A300A', '#9A5A12', '#DA9826', '#FFD266', '#FFF6CC'], '#241404')
    faceted(c, _poly_n(16, 16, 12, 12, 12, math.pi / 12), ramp, 0.5, R['gold'])
    c.outline()
    return c


def spirit_jade():
    c = Canvas(32)
    faceted(c, _poly_n(16, 16, 13, 12, 6, 0.0), R['qi'], 0.5, R['silver'])
    c.outline()
    return c


def insight_jade():
    c = Canvas(32)
    ramp = Ramp(['#241444', '#46287E', '#7650BE', '#B08EEC', '#EEE2FF'], '#10081E')
    outer = [(16, 3), (27, 15), (27, 18), (16, 29), (5, 18), (5, 15)]
    faceted(c, outer, ramp, 0.46, R['gold'])
    c.put(c.ellipse(16, 16.5, 3, 1.8), ramp, 'flat', base=0)
    c.put(c.rect(15, 16, 16, 16), ramp[4], 'flat')
    c.outline()
    return c


# ----------------------------------------------------------------------------- attunement (S18)
# Storm Ward jades are bi discs of storm-glass, each carved with one aspect of the storm.
WARD = Ramp(['#16244A', '#2C4E86', '#4F86C4', '#96C8EE', '#E6F8FF'], '#0A1226')


def _bi(c, ramp):
    disc = c.ellipse(16, 16, 13, 13) & ~c.ellipse(16, 16, 4, 4)
    c.put(disc, ramp, 'sphere', base=2, cx=12, cy=12, rx=16, ry=16)
    rim = disc & ~c.ellipse(16, 16, 11.5, 11.5)
    c.put(rim, ramp, 'flat', base=1, only_on=True)
    c.put(c.ellipse(16, 16, 5, 5) & ~c.ellipse(16, 16, 4, 4), ramp, 'flat', base=3)
    return disc


def ward_thunder():
    c = Canvas(32)
    _bi(c, WARD)
    for k in range(4):   # square thunder-scroll (leiwen) at the four quarters
        a = math.pi / 4 + k * math.pi / 2
        x, y = 16 + math.cos(a) * 8.5, 16 + math.sin(a) * 8.5
        c.put(c.rect(int(x) - 2, int(y) - 2, int(x) + 1, int(y) + 1) & ~c.rect(int(x) - 1, int(y) - 1, int(x), int(y)), WARD[4], 'flat')
    c.outline()
    c.glow('#7FD4FF', (40,))
    return c


def ward_gale():
    c = Canvas(32)
    _bi(c, WARD)
    for k in range(3):
        a0 = k * 2 * math.pi / 3
        pts = [(16 + math.cos(a0 + t * 0.25) * (5.5 + t * 0.9), 16 + math.sin(a0 + t * 0.25) * (5.5 + t * 0.9)) for t in range(7)]
        c.put(c.bres_path([(int(round(x)), int(round(y))) for x, y in pts]), WARD[4], 'flat')
    c.outline()
    c.glow('#7FD4FF', (40,))
    return c


def ward_rain():
    c = Canvas(32)
    _bi(c, WARD)
    for (x, y) in ((9, 10), (22, 9), (8, 20), (23, 21), (15, 25), (16, 6)):
        c.put(c.ellipse(x, y + 0.5, 1.2, 1.6) | c.rect(x, y - 2, x, y - 1), WARD[4], 'flat')
    c.outline()
    c.glow('#7FD4FF', (40,))
    return c


def ward_lightning():
    c = Canvas(32)
    _bi(c, WARD)
    for pts in (((9, 5), (6, 11), (10, 12), (7, 17)), ((24, 15), (21, 21), (25, 22), (22, 28))):
        c.put(c.bres_path(list(pts)), '#F4FBFF', 'flat')
    c.outline()
    c.glow('#7FD4FF', (70,))
    return c


for _id, _fn in (('ward_thunder', ward_thunder), ('ward_gale', ward_gale), ('ward_rain', ward_rain), ('ward_lightning', ward_lightning)):
    register(FAM, _id, _fn, GROUP)


for _id, _fn in (('body_jade', body_jade), ('swift_jade', swift_jade), ('essence_jade', essence_jade),
                 ('spirit_jade', spirit_jade), ('insight_jade', insight_jade)):
    register(FAM, _id, _fn, GROUP)
