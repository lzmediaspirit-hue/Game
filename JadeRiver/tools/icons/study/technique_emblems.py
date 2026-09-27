#!/usr/bin/env python3
"""Technique emblem grammar samples (docs/technique_plan.md §3.9), composed by the techniques family's composer.

An emblem is composed from four layers: the element's disc, the form's mark (with the family's weapon inset), a rim
for the grade or the kind (keystone, Dao art, lost art) and a path stamp. This draws four compositions for the
mockups, natively at 64, 48 and 32:

    python3 tools/icons/study/technique_emblems.py      # -> docs/mockups/assets/emblemA_*.png, emblemA48_*, emblemA32_*

  undertow_crescent        Water disc x the jian's Arc mark x the Earth rim
  upright_undertow_script  Water disc x the Pillar mark x the Confucian stamp (a path art: its mark in the path's colour)
  nine_undertows           Water disc x the whirlpool hand mark x the keystone rim (gold, eight studs)
  tide_palm                Water disc x the free hand's Strike x the lost-art rim (torn)

Deterministic: two runs give byte-identical PNGs. Nothing in art/icons, the manifest or game data is touched.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..')))

from pix import PixelPainter  # noqa: E402
import families  # noqa: E402,F401
from families.techniques import emblem  # noqa: E402

PROJECT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(PROJECT, 'docs', 'mockups', 'assets')

SAMPLES = [
    ('undertow_crescent', emblem('water', 'arc', 'jian', 'earth')),
    ('upright_undertow_script', emblem('water', 'pillar', 'any', 'earth', path='confucian')),
    ('nine_undertows', emblem('water', None, 'jian', 'common', kind='keystone', mark='whirlpool')),
    ('tide_palm', emblem('water', 'strike', 'any', 'common', kind='lost')),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    for ident, draw in SAMPLES:
        for tag, scale in (('emblemA_', 1.0), ('emblemA48_', 0.75), ('emblemA32_', 0.5)):
            p = PixelPainter(64, scale)
            draw(p)
            p.image().save(os.path.join(OUT, tag + ident + '.png'), format='PNG', optimize=False, compress_level=9)
            print(os.path.relpath(os.path.join(OUT, tag + ident + '.png'), PROJECT))


if __name__ == '__main__':
    main()
