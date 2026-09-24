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


for _id, _fn in (('body_jade', body_jade), ('swift_jade', swift_jade), ('essence_jade', essence_jade),
                 ('spirit_jade', spirit_jade), ('insight_jade', insight_jade)):
    register(FAM, _id, _fn, GROUP)
