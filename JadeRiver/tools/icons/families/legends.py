"""S47 legendary chains: the three pieces of each legend (a hilt or grip, a blade or body fragment, a heart) tinted
in the chain's own colour, and the Weapon Soul Crystal that awakens a +10 weapon."""
import colorsys
import math
import os
import sys

from pix import Canvas, Ramp, erode4
from palette import R
from registry import register
import shapes as S

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "data"))
from legends import CHAINS  # noqa: E402

FAM, GROUP = 'items', 'legends'


def _ramp(hex_col):
    """Five tones, dark to light, around a chain's tint."""
    r, g, b = (int(hex_col[i:i + 2], 16) / 255.0 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    tones = []
    for lt in (0.16, 0.30, 0.48, 0.68, 0.88):
        rr, gg, bb = colorsys.hls_to_rgb(h, lt, min(1.0, s * 0.9 + 0.1))
        tones.append('#%02X%02X%02X' % (int(rr * 255), int(gg * 255), int(bb * 255)))
    return Ramp(tones)


def _grip(tint):
    """Piece one: a broken hilt, the wrap still on it, a gold guard and a jagged stub of the tinted metal."""
    def build():
        c = Canvas(32)
        t = _ramp(tint)
        grip = c.seg(8, 25, 15, 18, 3.2)
        c.put(grip, R['darkwood'], 'ray', base=2)
        for k in range(3):
            c.put(c.seg(9 + k * 2.2, 23.6 - k * 2.2, 11 + k * 2.2, 25.2 - k * 2.2, 0.8), R['red'], 'flat', base=3)
        c.put(c.seg(13, 14, 19, 20, 2.0), R['gold'], 'ray', base=3, sep=True)
        stub = c.poly([(16, 17), (22, 11), (25, 10), (23, 13), (24, 15), (20, 19)])
        c.put(stub, t, 'ray', base=3, sep=True)
        c.put(c.circle(6.5, 26.5, 1.8), R['gold'], 'flat', base=3)
        c.outline()
        c.glow(tint, (60,))
        return c
    return build


def _fragment(tint):
    """Piece two: an angular fragment of the weapon's body, bright along its broken edge."""
    def build():
        c = Canvas(32)
        t = _ramp(tint)
        body = c.poly([(6, 22), (18, 6), (25, 9), (21, 15), (24, 18), (13, 27)])
        c.put(body, t, 'ray', base=2)
        c.put(c.seg(8, 21, 19, 8, 0.9) & erode4(body), t[4], 'flat')
        for (x, y) in ((22, 12), (19, 21), (11, 17)):
            c.put(c.circle(x, y, 0.9) & body, t[4], 'flat')
        c.outline()
        c.glow(tint, (70,))
        return c
    return build


def _heart(tint):
    """Piece three: the legend's heart, a lit bead held in a small cage of old gold."""
    def build():
        c = Canvas(32)
        t = _ramp(tint)
        bead = c.circle(16, 16, 6.5)
        c.put(bead, t, 'sphere', base=2, sep=True, cx=14, cy=14, rx=7, ry=7)
        for k in range(4):
            a = k * math.pi / 2
            x, y = 16 + 9.0 * math.cos(a), 16 + 9.0 * math.sin(a)
            c.put(c.seg(16 + 6.0 * math.cos(a), 16 + 6.0 * math.sin(a), x, y, 1.1), R['gold'], 'flat', base=3)
            c.put(c.circle(x, y, 1.3), R['gold'], 'flat', base=4)
        c.put(c.ring(16, 16, 7.2, 0.7), R['gold'], 'flat', base=2)
        c.put(c.circle(14, 13.5, 1.6), t[4], 'flat')
        c.outline()
        c.glow(tint, (70,))
        return c
    return build


def weapon_soul_crystal():
    """A long faceted crystal with a flame-like core: it wakes a weapon forged to its limit."""
    c = Canvas(32)
    body = c.poly([(16, 3), (22, 11), (20, 27), (16, 30), (12, 27), (10, 11)])
    c.put(body, R['gold'], 'ray', base=2)
    c.put(c.poly([(16, 3), (22, 11), (16, 13), (10, 11)]), R['gold'][4], 'flat')
    c.put(c.seg(16, 13, 16, 29, 0.8) & body, R['gold'][1], 'flat')
    core = S.flame(c, 16, 23, 5, 9) & erode4(body)
    c.put(core, R['ember'], 'ray', base=3)
    c.outline()
    c.glow('#FFD27A', (120, 50))
    return c


for ch in CHAINS:
    for i, builder in enumerate((_grip, _fragment, _heart)):
        register(FAM, ch["pieces"][i][0], builder(ch["tint"]), GROUP)
register(FAM, 'weapon_soul_crystal', weapon_soul_crystal, GROUP)
