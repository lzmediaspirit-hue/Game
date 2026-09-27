#!/usr/bin/env python3
"""Technique emblem grammar samples (docs/technique_plan.md §3.9), drawn by the icon study's Style A pipeline.

An emblem is composed from four layers: the element's disc, the form's mark, a rim for the grade or the kind
(keystone, lost art) and a path stamp. This draws four compositions for the mockups:

    python3 tools/icons/study/technique_emblems.py      # -> docs/mockups/assets/emblemA_*.png (64 px), emblemA48_*, emblemA32_*

  undertow_crescent        Water disc x the jian Arc mark x the Earth rim
  upright_undertow_script  Water disc x the Pillar mark x the Confucian stamp (a path art)
  nine_undertows           Water disc x a whirlpool mark x the keystone rim (gold, eight studs)
  tide_palm                Water disc x the palm mark x the lost-art rim (torn)

Deterministic: two runs give byte-identical PNGs. Nothing in art/icons, the manifest or game data is touched.
"""
from __future__ import annotations

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..')))

import study_lib as L  # noqa: E402
import study_icons as I  # noqa: E402
from pix import Ramp  # noqa: E402
from study_lib import mat7, WHITE, dilate4  # noqa: E402

PROJECT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(PROJECT, 'docs', 'mockups', 'assets')

# The study drew three discs (fire, jade, metal); the Water disc is today's ramp from families/techniques.py.
I.EL.setdefault('water', (['#081E2C', '#0F3A52', '#18607C', '#2E8AA6', '#62BCD0'],
                          ['#1E5A70', '#4A9AB2', '#9EE0EC', '#DDF8FB', '#FFFFFF']))

# path stamps: one colour each (docs/technique_plan.md §3.9)
CONFUCIAN = mat7(Ramp(['#1E2350', '#2E3780', '#4A5AB8', '#7A8AE0', '#C6CEF8'], '#0A0C22'), 'matte')
EARTH_RIM = mat7(Ramp(['#123A1E', '#1E5A30', '#2E8446', '#56B46A', '#9CE0A6'], '#06140A'), 'metal')


def _stud(p, x, y):
    p.part(p.c.diamond(x, y, 1.8, 1.8), I.GOLD, 'flat', base=1, sep=True, rim=False)


def undertow_crescent(p):
    c = p.c
    inner, mk, d = I._emblem(p, 'water')
    # the Earth grade rim: a green-bronze ring just inside the outer rim
    p.decal(c.ring(32, 32, 28.6, 1.2) & ~c.circle(32, 32, 26.4), EARTH_RIM, 1)
    # the Arc: a crescent of sword Qi sweeping up and right, with a jian's line inside it
    cres = c.circle(30, 34, 19) & ~c.circle(37, 28, 18.5)
    I.mark(p, cres & inner, mk, base=0, bevel=2.0)
    blade = c.seg(18, 46, 43, 21, 2.2) & inner
    p.part(blade, mk, 'flat', base=2, sep=False, rim=False)
    # the Water verb: an undertow curl drawn back toward the caster
    curl = c.arc(21, 42, 6.0, 1.6, 200, 20) & inner
    p.part(curl, mk, 'flat', base=1, sep=False, rim=False)
    p.sparkle(43, 21, 1, WHITE)
    return p


def upright_undertow_script(p):
    c = p.c
    inner, mk, d = I._emblem(p, 'water')
    # the Pillar: a column of written water falling on one foe
    left = [(30.0 - 0.06 * (y - 9) + 0.9 * math.sin(y / 3.0), float(y)) for y in range(9, 47)]
    right = [(34.0 + 0.06 * (y - 9) + 0.9 * math.sin(y / 3.0 + 1.3), float(y)) for y in range(46, 8, -1)]
    col = c.poly(left + right) | c.ellipse(32, 48, 9, 2.8)   # the pool where it lands
    for (x, y) in ((21.5, 42.0), (42.5, 42.0), (18.5, 47.0), (45.5, 47.0)):   # the splash
        col |= c.circle(x, y, 1.5)
    I.mark(p, col & inner, mk, base=0, bevel=1.8)
    for y in (16, 23, 30, 37):      # script strokes written down the column
        p.line([(29.5, y), (34.5, y - 1.5)], mk, -2, 1.0)
    # the Confucian stamp: a square seal at the lower right
    seal = c.rrect(42, 42, 57, 57, 1.5)
    p.part(seal, CONFUCIAN, 'flat', base=0, sep=True, rim=False)
    p.line([(45.0, 46.0), (54.0, 46.0)], WHITE, 0, 1.0)
    p.line([(49.5, 46.0), (49.5, 54.0)], WHITE, 0, 1.0)
    p.line([(45.0, 54.0), (54.0, 54.0)], WHITE, 0, 1.0)
    return p


def nine_undertows(p):
    c = p.c
    inner, mk, d = I._emblem(p, 'water', secret=True)
    # the keystone rim: the secret art's gold rim with its four studs, and four more at the diagonals
    for a in (45, 135, 225, 315):
        r = 29.2
        _stud(p, 32 + r * math.cos(math.radians(a)), 32 + r * math.sin(math.radians(a)))
    # a whirlpool of nine blades: a spiral and blade tips around it
    spiral = c.empty()
    for k in range(3):
        spiral |= c.arc(32, 32, 7 + k * 6, 2.6, k * 40, k * 40 + 250)
    I.mark(p, spiral & inner, mk, base=0, bevel=1.6)
    for k in range(9):
        a = math.radians(k * 40 + 10)
        x, y = 32 + 21 * math.cos(a), 32 + 21 * math.sin(a)
        tip = c.seg(x, y, x + 5 * math.cos(a + 1.9), y + 5 * math.sin(a + 1.9), 1.8) & inner
        p.part(tip, mk, 'flat', base=2, sep=False, rim=False)
    p.part(c.circle(32, 32, 3.2), mk, 'sphere', base=2, sep=False, rim=False)
    return p


def tide_palm(p):
    c = p.c
    inner, mk, d = I._emblem(p, 'water')
    # the palm mark
    palm = c.rrect(23, 30, 40, 47, 4.0)
    for (x, top, w) in ((24.5, 15, 3.4), (29.5, 12, 3.6), (34.5, 13, 3.6), (39.0, 17, 3.2)):
        palm |= c.rrect(x - w / 2, top, x + w / 2, 33, 1.6)
    palm |= c.poly([(22.0, 36.0), (15.0, 28.0), (17.5, 26.0), (25.0, 33.0)])
    I.mark(p, palm & inner, mk, base=0, bevel=2.0)
    # a tide line across the heel of the hand
    pts = [(18 + x, 47 + 1.6 * math.sin(x / 2.6)) for x in range(0, 28)]
    p.line(pts, mk, 2, 1.4)
    # the lost-art rim: torn out of the outer ring in three places
    for (a0, a1) in ((14, 52), (140, 166), (244, 290)):
        tear = c.arc(32, 32, 29.5, 4.4, a0, a1)
        # a ragged edge: bite a few pixels into the disc along the tear
        for k in range(a0, a1, 7):
            a = math.radians(k + 3)
            tear |= c.circle(32 + 26.4 * math.cos(a), 32 + 26.4 * math.sin(a), 1.6 + (k % 3) * 0.5)
        p.erase(tear)
    return p


SAMPLES = [('undertow_crescent', undertow_crescent), ('upright_undertow_script', upright_undertow_script),
           ('nine_undertows', nine_undertows), ('tide_palm', tide_palm)]


def main():
    os.makedirs(OUT, exist_ok=True)
    for ident, fn in SAMPLES:
        for tag, scale in (('emblemA_', 1.0), ('emblemA48_', 0.75), ('emblemA32_', 0.5)):
            p = L.PixelPainter(64, scale)
            fn(p)
            p.image().save(os.path.join(OUT, tag + ident + '.png'), format='PNG', optimize=False, compress_level=9)
            print(os.path.relpath(os.path.join(OUT, tag + ident + '.png'), PROJECT))


if __name__ == '__main__':
    main()
