#!/usr/bin/env python3
"""The seven Works of the Post as Style A objects, drawn large for the Works page mockup (roadmap decision 21).

`docs/page_identity.md` row 23 makes the Works page a bamboo curio cabinet with one object per work. None of the seven
has an HD icon on the build branch yet (the Seal Scripts, Guardian Steles, the county's Favours, the Calcination
furnace, the post Flags, the Mirror of Echoes and the Post Arts use legacy item icons or none), so they are drawn
here in the Style A description language (`tools/icons/README.md`, "HD drawing model"): a 64-unit icon space, palette
materials in seven steps, one light from the top left, the cool rim on the lower right and the selective outline.
A drawing renders at 64 for a page slot as any HD icon does; here it renders natively at 128 for the cabinet, where each
work is read at a glance:

  post_arts   a thread-bound artisan's manual with a carving knife laid across it (the character's own Post Arts)
  seal        a jade seal with a crouching beast knob, its red paste and a silk tassel (the Seal Scripts)
  stele       a Guardian Stele: carved stone on a plinth, a jade boss and moss (a craft's tools, in every hand)
  favour      the county's favour: a folded warrant under the magistrate's red seal, tied with a tally
  furnace     the calcination furnace: a three-legged bronze ding over its fire (it burns goods into Essence Salt)
  flag        a post flag: a swallowtail pennant on a pole planted in a stone socket (it serves its room's posts)
  mirror      the Mirror of Echoes: a bronze mirror on its stand, the echo of a post turning in its face

    python3 tools/icons/study/works_objects.py     # -> docs/mockups/assets/work_<id>.png (128), work96_<id>.png (96)

The drawings live in `tools/icons/families/works.py`, which the icon build renders for the game (64 and @96); this
script renders them for the mockups only. Deterministic: two runs give byte-identical PNGs.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..')))

from pix import PixelPainter  # noqa: E402
from families.works import WORKS  # noqa: E402

PROJECT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(PROJECT, 'docs', 'mockups', 'assets')


def main(keys=None):
    os.makedirs(OUT, exist_ok=True)
    for ident, draw in WORKS:
        if keys and ident not in keys:
            continue
        for tag, scale in (('work_', 2.0), ('work96_', 1.5)):
            p = PixelPainter(64, scale)
            draw(p)
            a = p.c.a
            if a[0, :].any() or a[-1, :].any() or a[:, 0].any() or a[:, -1].any():
                print('WARNING %s@%d: artwork touches the canvas edge' % (ident, int(64 * scale)))
            path = os.path.join(OUT, tag + ident + '.png')
            p.image().save(path, format='PNG', optimize=False, compress_level=9)
            print(os.path.relpath(path, PROJECT))


if __name__ == '__main__':
    main(sys.argv[1:] or None)
