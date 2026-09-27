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

Deterministic: two runs give byte-identical PNGs. Nothing in art/, data/ or the icon manifest is touched.
"""
from __future__ import annotations

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..')))

from pix import Frame, PixelPainter, dilate4, erode4  # noqa: E402
from palette import M  # noqa: E402

PROJECT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(PROJECT, 'docs', 'mockups', 'assets')


def post_arts(p):
    """A thread-bound manual, cover in indigo cloth with a paper title slip, a carving knife across it."""
    c = p.c
    cloth, paper, thread, steel, wood = M('indigo'), M('paper'), M('hemp'), M('iron'), M('wood')
    # the page block showing under the cover (the lower and right edges), then the cover
    block = c.poly([(12, 22), (50, 14), (54, 46), (16, 54)])
    p.part(block, paper, 'flat', base=1, sep=False, tex='paper')
    cover = c.poly([(10, 19), (48, 11), (52, 43), (14, 51)])
    p.part(cover, cloth, 'ray', base=0, sep=True, tex='cloth', axis=78)
    # the spine at the left, stitched through four holes
    spine = c.poly([(10, 19), (15, 18), (19, 50), (14, 51)])
    p.decal(spine & cover, cloth, -1)
    for k in range(4):
        t = 0.14 + k * 0.24
        x, y = 10 + (14 - 10) * t + 2.2, 19 + (51 - 19) * t
        p.line([(x - 3.4, y + 0.6), (x + 2.2, y - 0.4)], thread, 1, 1.3, only_on=False)
        p.decal(c.circle(x + 2.2, y - 0.4, 0.9), cloth, -3)
    # the title slip
    slip = c.poly([(25, 19), (33, 17.4), (35.6, 36), (27.6, 37.6)])
    p.part(slip, paper, 'bevel', base=1, sep=True, hw=1, sw=1, rim=False)
    for k in range(3):
        y0 = 22 + k * 4.6
        p.line([(28.2 + k * 0.5, y0 + 0.2), (31.4 + k * 0.5, y0 - 0.5)], cloth, -2, 1.2)
    # the knife: a wooden handle and a short steel blade, laid across the lower corner
    fr = Frame((22.0, 58.0), 32.0)
    handle = fr.prof(c, [(0.0, 2.4), (14.0, 2.6)])
    p.cylinder(fr, handle, 2.6, wood, tex='wood', axis=32)
    ferrule = fr.prof(c, [(13.6, 2.8), (16.0, 2.8)])
    p.part(ferrule, M('bronze'), 'ray', base=1, sep=True)
    blade = fr.prof(c, [(15.6, 2.2), (26.0, 2.0), (31.0, 0.3)])
    p.cylinder(fr, blade, 2.2, steel, ridge=True, sep=True)
    p.sparkle(*fr.P(27.0, -0.6), 1)


def seal(p):
    """A jade seal: a square stone with a crouching beast on top, red paste on its face, a silk tassel."""
    c = p.c
    jade, red, silk = M('jade'), M('seal'), M('red')
    # the tassel behind, hanging from the knob to the right
    p.line([(40, 17), (47, 22), (50, 30)], silk, 0, 1.6, only_on=False)
    knot = c.diamond(50.5, 31.5, 2.6)
    p.part(knot, silk, 'ray', base=1, sep=True)
    fringe = c.poly([(48.4, 33), (52.6, 33), (54, 44), (47, 44)])
    p.part(fringe, silk, 'vgrad', base=0, sep=True)
    for x in (48.8, 50.6, 52.4):
        p.decal(c.seg(x, 35, x + 0.4, 43.4, 0.8), silk, -2)
    # the stone: a tall square block seen from the front and a little above
    top = c.poly([(17, 31), (41, 31), (46, 27), (22, 27)])
    front = c.box(17, 31, 41, 55)
    side = c.poly([(41, 31), (46, 27), (46, 51), (41, 55)])
    p.part(front, jade, 'ray', base=0, sep=False, tex='jade')
    p.part(side, jade, 'flat', base=-2, sep=True, tex='jade')
    p.part(top, jade, 'flat', base=1, sep=True)
    # the red paste on the face's foot, and a carved band
    p.part(c.box(17, 52, 41, 56) | c.poly([(41, 52), (46, 48), (46, 51), (41, 55)]), red, 'flat', base=0, sep=True)
    p.decal(c.box(17, 36, 41, 37.2), jade, -2)
    # the knob: a beast crouched on the top, its head to the left, a hole under its belly for the cord
    body = c.ellipse(33, 24, 10, 5.6) & c.box(0, 0, 64, 29)
    head = c.circle(22.6, 21.6, 4.6)
    ears = c.poly([(19.6, 18.6), (20.4, 14.6), (23, 17.4)]) | c.poly([(23.8, 17), (25.8, 13.8), (26.6, 17.8)])
    tail = c.taper((42, 23), (46, 17), (41.4, 15), 2.4, 1.4)
    beast = body | head | ears | tail
    p.part(beast, jade, 'sphere', base=1, sep=True, cx=28, cy=17, rx=16, ry=10)
    p.decal(c.circle(21.2, 21.0, 0.9), jade, -3)
    p.decal(c.ellipse(34, 27.4, 3.0, 1.2), jade, -3)
    p.decal(c.seg(29, 21.4, 37, 20.6, 0.9) & body, jade, 2)
    p.sparkle(19.4, 34.4, 1)


def stele(p):
    """A Guardian Stele: a round-topped stone slab on a plinth, a carved border, three columns of script, a jade boss
    in the crown and moss at its foot."""
    c = p.c
    stone, plinth, jade, moss = M('stone'), M('warmstone'), M('jade'), M('moss')
    slab = c.box(18, 18, 46, 52) | c.ellipse(32, 18, 14, 11)
    p.part(slab, stone, 'ray', base=0, sep=False)
    inner = c.box(21.4, 19, 42.6, 49) | c.ellipse(32, 19, 10.6, 8)
    p.decal(slab & ~inner & dilate4(inner), stone, -2)
    # three carved columns of script: short strokes stacked
    for col, x in enumerate((26.0, 32.0, 38.0)):
        for k in range(5 - (col == 1)):
            y = 25 + k * 4.8 + (col == 1) * 1.8
            w = 2.6 if (k + col) % 2 else 1.8
            p.decal(c.seg(x - w, y, x + w, y + 0.2, 1.1), stone, -3)
            p.decal(c.seg(x - w, y + 1.1, x + w, y + 1.3, 0.8), stone, 1)
    # the jade boss in the crown
    p.part(c.circle(32, 14.6, 3.4), jade, 'sphere', base=1, sep=True)
    # the plinth: a stepped base
    p.part(c.box(13, 51, 51, 55), plinth, 'bevel', base=0, sep=True, hw=1, sw=1)
    p.part(c.box(10, 55, 54, 60), plinth, 'bevel', base=-1, sep=True, hw=1, sw=1)
    # moss on the left foot and creeping up the stone
    tuft = c.ellipse(19, 51.2, 6, 2.6) | c.ellipse(15, 55.4, 4.6, 2.2) | c.ellipse(20, 47.4, 2.4, 2.8)
    p.part(tuft, moss, 'sphere', base=0, sep=True)
    p.sparkle(30.4, 12.8, 1)


def favour(p):
    """The county's favour: a decree on pale gold silk opened between its two rollers, lines of writing and the
    magistrate's red seal on it, a red cord with a jade tally hanging from the right roller."""
    c = p.c
    silk, red, wood, cord, jade, gold = M('talisman'), M('seal'), M('darkwood'), M('red'), M('jade'), M('gold')
    # the sheet, a little wavy, between the rollers
    sheet = c.poly([(13, 18), (24, 16.6), (38, 18.2), (51, 16.8), (51, 45.2), (38, 46.8), (24, 45.2), (13, 46.6)])
    p.part(sheet, silk, 'ray', base=0, sep=False, tex='paper')
    # a ruled border and five columns of writing (short strokes), right to left
    border = sheet & ~erode4(erode4(sheet))
    p.decal(border & ~erode4(sheet), silk, -2)
    for i, x in enumerate((44.0, 39.4, 34.8, 30.2, 25.6)):
        n = 4 if i % 2 == 0 else 3
        for k in range(n):
            y = 22.4 + k * 5.4 + (i % 2) * 2.2
            p.decal(c.seg(x, y, x + 0.3, y + 3.0, 1.2), silk, -3)
    # the magistrate's seal at the lower left of the writing
    sq = c.box(15.6, 30.6, 23.6, 38.6)
    p.part(sq, red, 'flat', base=0, sep=False, rim=False)
    p.decal(sq & ~c.box(16.8, 31.8, 22.4, 37.4), red, -2)
    p.decal(c.seg(17.8, 33.2, 21.4, 33.2, 1.0) | c.seg(19.6, 33.2, 19.6, 36.4, 1.0) | c.seg(17.8, 36.2, 21.4, 36.2, 1.0), red, 2)
    # the two rollers, with gold end caps
    for x in (11.4, 52.6):
        fr = Frame((x, 52.0), 90.0)
        roller = fr.prof(c, [(0.0, 2.6), (40.0, 2.6)])
        p.cylinder(fr, roller, 2.6, wood, tex='wood', axis=90)
        for y in (11.2, 52.4):
            p.part(c.rrect(x - 3.2, y - 1.8, x + 3.2, y + 1.8, 1.0), gold, 'bevel', base=1, sep=True, hw=1, sw=1)
    # the cord and the jade tally
    p.line([(54, 30), (57.4, 38), (56.6, 46)], cord, 0, 1.4, only_on=False)
    tally = c.rrect(52.2, 46, 60.2, 57, 2.4)
    p.part(tally, jade, 'sphere', base=0, sep=True)
    p.decal(c.ring(56.2, 51.4, 2.2, 0.9) & tally, jade, -2)
    p.sparkle(20.4, 21.2, 1)


def furnace(p):
    """The calcination furnace: a round bronze ding on three legs, two upright handles, a lid with a jade knob, fire
    under its belly and the heat showing through the vents."""
    c = p.c
    bronze, fire, ember, jade = M('bronze'), M('fire'), M('ember'), M('jade')
    # the fire behind the legs
    flames = c.empty()
    for (x, h, w) in ((24, 11, 4.4), (32, 14, 5.2), (40, 11, 4.4)):
        flames |= c.poly([(x - w, 60), (x - w * 0.4, 60 - h * 0.55), (x, 60 - h), (x + w * 0.5, 60 - h * 0.5), (x + w, 60)])
    p.part(flames, fire, 'vgrad', base=0, sep=False, rim=False)
    p.part(c.ellipse(32, 60, 12, 1.8), ember, 'flat', base=1, sep=True, rim=False)
    # three legs
    for (x0, x1) in ((20, 17), (32, 32), (44, 47)):
        leg = c.taper((x0, 44), (x0 + (x1 - x0) * 0.4, 52), (x1, 58), 4.2, 2.6)
        p.part(leg, bronze, 'ray', base=-1, sep=True)
    # the belly and the rim
    belly = c.ellipse(32, 38, 19, 12) & c.box(0, 30, 64, 64)
    p.part(belly, bronze, 'sphere', base=0, sep=True, cx=26, cy=33, rx=22, ry=14, tex='metal')
    rim = c.rrect(11, 27, 53, 32, 1.4)
    p.part(rim, bronze, 'bevel', base=1, sep=True, hw=1, sw=1)
    # the handles standing on the rim
    for x in (16.0, 48.0):
        ear = c.box(x - 3, 18, x + 3, 28) & ~c.box(x - 1.4, 20.4, x + 1.4, 28)
        p.part(ear, bronze, 'bevel', base=0, sep=True, hw=1, sw=1)
    # the lid and its jade knob
    lid = c.ellipse(32, 27, 15, 5.4) & c.box(0, 0, 64, 27.4)
    p.part(lid, bronze, 'sphere', base=1, sep=True, cx=28, cy=23, rx=16, ry=6)
    p.part(c.circle(32, 19.4, 3.2), jade, 'sphere', base=1, sep=True)
    # a band of cloud-scroll relief and three glowing vents
    p.decal(c.box(13, 34, 51, 35.2) & belly, bronze, -2)
    for x in (24.0, 32.0, 40.0):
        v = c.ellipse(x, 41, 2.2, 1.6)
        p.part(v, ember, 'flat', base=2, sep=True, rim=False)
    # heat above: two curls
    p.line([(26, 14), (24.4, 10), (26.4, 6)], ember, 1, 1.2, only_on=False)
    p.line([(38, 14), (39.6, 10), (37.6, 6)], ember, 0, 1.2, only_on=False)
    p.sparkle(20.4, 30.0, 1)


def flag(p):
    """A post flag: a swallowtail pennant on a pole with a gold finial and a red tassel, planted in a stone socket."""
    c = p.c
    pole_m, cloth, gold, trim, stone, red = M('darkwood'), M('jade'), M('gold'), M('gold'), M('stone'), M('red')
    # the pennant: a waving swallowtail from the pole to the right
    top = [(21, 11), (30, 9.6), (40, 11.4), (50, 13.6), (57, 12.4)]
    bot = [(52, 26), (57, 34.6), (46, 33.4), (36, 33.8), (27, 36), (21, 36)]
    pen = c.poly(top + bot)
    p.part(pen, cloth, 'ray', base=0, sep=False, tex='cloth', axis=0)
    # a gold band along the hoist and the edges
    p.decal(pen & c.box(21, 0, 25, 64), trim, 0)
    edge = pen & ~erode4(pen)
    p.decal(edge & ~c.box(0, 0, 25, 64), cloth, -2)
    # the post's mark on the pennant: a ringed dot and two strokes
    p.decal(c.ring(36, 22.6, 4.8, 1.3) & pen, trim, 1)
    p.decal(c.circle(36, 22.6, 1.4) & pen, trim, 1)
    p.decal(c.seg(44, 19, 49, 20, 1.2) & pen | c.seg(44, 25.4, 48, 26.4, 1.2) & pen, cloth, 2)
    # the pole, the finial and the tassel
    fr = Frame((21.0, 58.0), 90.0)
    pole = fr.prof(c, [(0.0, 1.8), (51.0, 1.6)])
    p.cylinder(fr, pole, 1.8, pole_m, tex='wood', axis=90)
    p.part(c.diamond(21, 5.6, 2.6, 3.6), gold, 'ray', base=1, sep=True)
    p.line([(19.6, 9.4), (16.6, 14)], red, 0, 1.2, only_on=False)
    p.part(c.poly([(15, 14), (18.4, 14), (18.6, 20), (14.4, 20)]), red, 'vgrad', base=0, sep=True)
    # the stone socket
    sock = c.poly([(13, 62), (29, 62), (27, 54), (15, 54)])
    p.part(sock, stone, 'bevel', base=0, sep=True, hw=1, sw=1)
    p.decal(c.seg(15.4, 57.6, 26.6, 57.6, 0.9) & sock, stone, -2)
    p.sparkle(22.4, 4.4, 1)


def mirror(p):
    """The Mirror of Echoes: a round bronze mirror on a wooden stand, an echo turning in its polished face."""
    c = p.c
    bronze, glass, wood, silk = M('lanternbronze'), M('ice'), M('darkwood'), M('red')
    # the stand: two legs and a cross-bar behind the mirror, a base
    for (x0, x1) in ((20, 14), (44, 50)):
        leg = c.taper((x0, 34), ((x0 + x1) / 2.0, 48), (x1, 60), 3.2, 3.6)
        p.part(leg, wood, 'ray', base=-1, sep=True, tex='wood', axis=70)
    p.part(c.box(10, 58, 54, 62), wood, 'bevel', base=0, sep=True, hw=1, sw=1)
    # the mirror: a bronze rim, the polished face
    rim = c.circle(32, 30, 21)
    p.part(rim, bronze, 'sphere', base=0, sep=True, tex='metal')
    face = c.circle(32, 30, 17)
    p.part(face, glass, 'sphere', base=0, sep=True, cx=27, cy=24, rx=20, ry=20, rim=False)
    # the echo: rings turning out from a point in the face, and the shine
    for (r, lv) in ((3.2, 2), (7.4, 1), (11.6, 0)):
        p.decal(c.arc(34, 32, r, 1.1, 200, 60) & face, glass, lv)
    p.decal(c.arc(32, 30, 14.4, 1.6, 115, 165) & face, glass, 3)
    # four studs on the rim and the silk cord knot at the top
    for a in (45, 135, 225, 315):
        r = math.radians(a)
        p.part(c.circle(32 + 19 * math.cos(r), 30 - 19 * math.sin(r), 1.5), bronze, 'sphere', base=2, sep=True)
    p.part(c.diamond(32, 8, 3.2, 2.6), silk, 'ray', base=0, sep=True)
    p.line([(30.6, 10), (28.6, 16)], silk, 0, 1.2, only_on=False)
    p.line([(33.4, 10), (35.4, 16)], silk, 0, 1.2, only_on=False)
    p.sparkle(25.2, 22.4, 1)


WORKS = [('post_arts', post_arts), ('seal', seal), ('stele', stele), ('favour', favour), ('furnace', furnace),
         ('flag', flag), ('mirror', mirror)]


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
