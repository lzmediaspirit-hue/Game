"""Manuals, curios and workshop goods (HD, Style A): appraisal, puppetry, research and formations, at 64 art px
shown 1:1 in the 76 px slot, with a native @32 render for the small slots and the Works page's rows.

Method manuals and the pet skill books are thread-bound books (`book_hd`): the cover's cloth or leather names the
element or the skill, the stitched spine and its thread wraps, the pages' fore-edge, a title slip, the emblem on the
cover (`EMBLEMS_HD`: a mountain, a leaf, a flame, waves, wind curls, reeds, a paw). Technique manuals are tied
scrolls (`manual_hd`) with an element tag on a cord. Curios are small antiques: a grimed bronze ding, a carved river
jade bi (`jades.bi_hd`) beside its glass fake with a chip and bubbles, old coins on a string. The workshop goods are
the spirit wood with Qi in its grain, the puppet's jade heart in its frame, the three array plates with their arrays
lit (a trigram ring, four blades, a chain spiral) and the Sphere Comprehension Stone with a world folded in it.
The grade is in the fittings and the aura from Mystic up (the Will-grade stone).
"""
import math

import numpy as np

from pix import Frame, Ramp, WHITE, dilate4, erode4
from palette import M, TEX, mat7, kit
from registry import hd, register
import shapes as S
from families.jades import bi_hd
from families.minerals import lmask
from families.treasures import ding_hd

FAM, GROUP = 'items', 'workshop'
ART = 64   # HD (tools/icons/README.md, "How to convert a family")

PAPER, INKM, GOLD, SILVER, BRONZE, JADE, DARKWOOD, LEATHER, HEMP, RED, QI, VIOLET = (M('paper'), M('ink'), M('gold'), M('silver'), M('bronze'), M('jade'),
                                                                                    M('darkwood'), M('leather'), M('hemp'), M('red', 'silk'), M('qi', 'light'),
                                                                                    M('violet', 'gem'))
LEAF, EMBER, YELLOW, CLOUD, BAMBOO, STRAW, STONE, MUD, SEAL = M('leaf'), M('ember'), M('yellow'), M('cloud', 'porcelain'), M('bamboo'), M('straw'), M('stone'), M('mud'), M('seal', 'gem')
TALISMAN = M('talisman')
INK_TEXT = mat7(Ramp(['#151418', '#1E1D22', '#2B2A30', '#3E3D44', '#5A5860'], '#08080A'), 'ink')
ELEMENT_COVER = {
    'earth': mat7(Ramp(['#2E2418', '#4C3B26', '#6E5738', '#94795A', '#BCA27E'], '#140F08'), 'cloth'),
    'wood': mat7(Ramp(['#12301F', '#1C4A2E', '#2E6A40', '#4E9058', '#8CC47C'], '#07150C'), 'cloth'),
    'fire': mat7(Ramp(['#3A1010', '#5E1A18', '#8A2A22', '#B8483A', '#E07E62'], '#1A0606'), 'cloth'),
    'water': mat7(Ramp(['#0C1C30', '#15304C', '#1F4870', '#35699A', '#6C9CC8'], '#060C16'), 'cloth'),
    'wind': mat7(Ramp(['#2A3848', '#44586C', '#667E92', '#8FA8BA', '#C4D6E2'], '#121A22'), 'cloth'),
}
FADED = mat7(Ramp(['#3E3A30', '#5E5846', '#7E7660', '#9E967C', '#C2BA9E'], '#1A1812'), 'cloth')
MUDPAPER = mat7(Ramp(['#4E4636', '#7A6E56', '#A89A7C', '#C8BC9C', '#E6DCC0'], '#221E16'), 'paper')
DUST = mat7(Ramp(['#6A6458', '#8A8476', '#AAA496', '#C6C0B2', '#E0DACC'], '#2A2620'), 'matte')
GREEN_GLASS = mat7(Ramp(['#2E4A1A', '#4E7428', '#7AA83A', '#B2D86A', '#EAFFB8'], '#14200A'), 'glass')
VERDIGRIS = mat7(Ramp(['#2A4A3E', '#3E6E5A', '#5E9A7E', '#8CC2A2', '#C8E8D2'], '#12201A'), 'metal')
PALEWOOD = mat7(Ramp(['#5A4E3A', '#8C7C5E', '#BCAE8C', '#DCD2B4', '#F6F0DC'], '#26200F'), 'wood')
PET_COVER = {'iron_hide': M('iron', 'leather'), 'frenzy': M('red', 'leather'), 'deep_pockets': M('leather'), 'herb_whisper': M('leaf', 'leather'),
             'thunder_roar': M('storm', 'leather'), 'guardian_spirit': M('violet', 'leather')}


def XY(p):
    """Pixel centres in icon space."""
    return p.c.X / p.s, p.c.Y / p.s


# ============================================================================= the emblems
# Each is (p, cx, cy, clip, s): a small mark about 16 s px across, drawn as parts so it takes its own dark keyline
# where it sits on the cover or the tag.
def em_earth(p, cx, cy, clip, s=1.0):
    c = p.c
    m = c.poly([(cx - 8.5 * s, cy + 5 * s), (cx - 2.5 * s, cy - 6 * s), (cx + 0.5 * s, cy - 1.5 * s), (cx + 3.5 * s, cy - 4.5 * s), (cx + 8.5 * s, cy + 5 * s)]) & clip
    p.part(m, GOLD, 'ray', base=0, sep=True, rim=False)
    p.decal(c.poly([(cx - 4.5 * s, cy - 2 * s), (cx - 2.5 * s, cy - 6 * s), (cx - 0.5 * s, cy - 3 * s)]) & m, GOLD, 2)


def em_wood(p, cx, cy, clip, s=1.0):
    c = p.c
    m = c.leaf(cx - 6.5 * s, cy + 6 * s, 52, 16 * s, 8 * s, 0.18) & clip
    p.part(m, LEAF, 'ray', base=0, sep=True, rim=False)
    p.decal(c.polyline([(cx - 5.5 * s, cy + 5 * s), (cx + 2.5 * s, cy - 4.5 * s)], 1.0) & m, LEAF, -2)


def em_fire(p, cx, cy, clip, s=1.0):
    c = p.c
    m = S.flame(c, cx, cy + 7.5 * s, 12 * s, 15 * s, 0.1) & clip
    p.part(m, EMBER, 'ray', base=0, sep=True, rim=False)
    p.decal(S.flame(c, cx, cy + 6.5 * s, 5.5 * s, 8 * s, -0.1) & m, YELLOW, 1)


def em_water(p, cx, cy, clip, s=1.0):
    c = p.c
    for k, y in enumerate((cy - 4.5 * s, cy, cy + 4.5 * s)):
        pts = [(cx - 7 * s + x * s, y + 1.5 * s * math.sin((x + k * 2) / 2.4)) for x in range(0, 15)]
        p.part(c.polyline(pts, 1.8 * s) & clip, QI, 'flat', base=1 if k == 0 else 0, sep=True, rim=False)


def em_wind(p, cx, cy, clip, s=1.0):
    c = p.c
    for (x, y, r) in ((cx - 2 * s, cy - 2 * s, 4.2 * s), (cx + 4 * s, cy + 3 * s, 2.8 * s)):
        m = (c.arc(x, y, r, 1.8 * s, 300, 200) | c.box(x + 0.5 * s, y + r - 1.8 * s, x + r * 2.4, y + r)) & clip
        p.part(m, CLOUD, 'flat', base=1, sep=True, rim=False)
    p.part(c.box(cx - 8 * s, cy + 6 * s, cx + 1 * s, cy + 7.6 * s) & clip, CLOUD, 'flat', base=0, sep=True, rim=False)


def em_reed(p, cx, cy, clip, s=1.0):
    c = p.c
    for k, x in enumerate((cx - 4.5 * s, cx, cx + 4.5 * s)):
        top = cy - 6 * s + k * 1.5 * s
        p.part(c.seg(x, cy + 7 * s, x + 1.2 * s, top, 1.6 * s) & clip, BAMBOO, 'flat', base=0, sep=True, rim=False)
        p.part(c.ellipse(x + 1.0 * s, top - 1.0 * s, 1.4 * s, 2.6 * s) & clip, STRAW, 'ray_soft', base=0, sep=True, rim=False)


def em_paw(p, cx, cy, clip, s=1.0):
    c = p.c
    p.part(c.ellipse(cx, cy + 3 * s, 4.8 * s, 3.8 * s) & clip, GOLD, 'ray_soft', base=0, sep=True, rim=False)
    for (dx, dy) in ((-5.6, -1.6), (-2.0, -5.2), (2.0, -5.2), (5.6, -1.6)):
        p.part(c.circle(cx + dx * s, cy + dy * s, 1.9 * s) & clip, GOLD, 'ray_soft', base=1, sep=True, rim=False)


EMBLEMS_HD = {'earth': em_earth, 'wood': em_wood, 'fire': em_fire, 'water': em_water, 'wind': em_wind, 'reed': em_reed, 'paw': em_paw}


# ============================================================================= bound books
def book_hd(p, cover, emblem=None, torn=False, stain=False):
    """A thread-bound book seen from the front: the pages' fore-edge and foot behind the cover, the cover in its
    cloth or leather with the stitched spine down the left and its thread wraps, a title slip with its characters,
    the emblem on the lower cover. `torn` takes the lower right corner off, `stain` spreads a water stain."""
    c = p.c
    x0, y0, x1, y1 = 12.0, 7.0, 47.0, 56.0
    pages = c.box(x0 + 3, y0 + 3, x1 + 4, y1 + 3)
    tear = c.poly([(x1 - 11, y1 + 3.5), (x1 - 7, y1 - 4), (x1 - 2, y1 - 8), (x1 + 4.5, y1 - 13), (x1 + 4.5, y1 + 3.5)])
    if torn:
        pages &= ~tear
    p.part(pages, PAPER, 'hgrad', base=0, sep=False, rim=False)
    for y in np.arange(y0 + 6, y1 + 2, 3.0):
        p.decal(c.box(x1 + 0.5, y, x1 + 4, y + 1) & pages, PAPER, -1)
    m = c.rrect(x0, y0, x1, y1, 1.6)
    if torn:
        m &= ~c.poly([(x1 - 13, y1 + 1), (x1 - 9, y1 - 5), (x1 - 4, y1 - 9), (x1 + 1, y1 - 15), (x1 + 1, y1 + 1)])
    p.part(m, cover, 'bevel', base=0, sep=True, hw=2, sw=2, tex=TEX.get(cover.kind), axis=90, rim=cover.kind != 'cloth')
    spine = c.box(x0, y0, x0 + 5.5, y1) & m
    p.decal(spine, cover, -1)
    p.decal(c.box(x0 + 5.5, y0, x0 + 6.5, y1) & m, cover, -3)
    for y in np.arange(y0 + 4.0, y1 - 2.0, 6.0):
        p.part(c.box(x0 - 0.5, y, x0 + 6.0, y + 1.6) & (m | c.box(x0 - 0.5, y0, x0, y1)), PAPER, 'flat', base=1, sep=False, rim=False)
        p.decal(c.box(x0 + 2.4, y - 0.8, x0 + 3.6, y + 2.4) & m, PAPER, 0)
    lab = c.rrect(x1 - 12.5, y0 + 4.5, x1 - 5.0, y0 + 27.0, 1.0)
    p.part(lab, PAPER, 'bevel', base=0, sep=True, hw=1, sw=1, tex='paper', rim=False)
    for y in (y0 + 7.5, y0 + 12.0, y0 + 16.5, y0 + 21.0):
        p.decal(c.box(x1 - 10.5, y, x1 - 7.0, y + 2.6) & lab, INK_TEXT, 0)
        p.decal(c.box(x1 - 9.5, y + 0.8, x1 - 8.0, y + 1.8) & lab, INK_TEXT, 2)
    if emblem:
        EMBLEMS_HD[emblem](p, (x0 + x1) / 2.0 + 2.0, y1 - 14.5, erode4(m) & ~spine & c.box(x0 + 7, y0 + 29, x1, y1), 1.15)
    if stain:
        st = c.ellipse(29, 40, 9, 7) & erode4(m) & ~spine
        p.decal(st & ~c.ellipse(29, 40, 7.2, 5.4), cover, 1)
        p.decal(c.ellipse(29, 40, 7.2, 5.4) & st, cover, -1)
        p.decal(c.ellipse(41, 13, 4.5, 3.5) & lab, PAPER, -1)
    return m


def make_book_hd(cover, emblem=None, torn=False, stain=False):
    def draw(p):
        book_hd(p, cover, emblem, torn, stain)
    return draw


# ============================================================================= technique manuals (tied scrolls)
def manual_hd(p, element='water', tie=RED, paper=PAPER, stained=False):
    """A closed technique scroll on the diagonal: rolled edge and roller knob, a tie band, a cord to a
    talisman tag carrying the element's mark."""
    c = p.c
    wood, tag_m = DARKWOOD, TALISMAN
    a, b = (13.0, 49.0), (46.0, 13.0)
    ang = math.degrees(math.atan2(-(b[1] - a[1]), b[0] - a[0]))
    fr = Frame(a, ang)
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    body = fr.prof(c, [(-2.0, 7.4), (L + 1.0, 7.4)])
    p.cylinder(fr, body, 7.4, paper, sep=False, tex='paper')
    if stained:
        t, w = fr.along(c)
        p.decal(c.ellipse(*fr.P(L * 0.32, 1.5), 6.0, 4.0) & erode4(body), MUD, 0)
        p.decal(c.ellipse(*fr.P(L * 0.32, 1.5), 3.6, 2.2) & erode4(body), MUD, -1)
    # the rolled edge (a spiral) at the far end, and the roller knob at the near end
    e = c.circle(b[0], b[1], 7.0)
    p.part(e, paper, 'flat', base=-1, sep=True, rim=False)
    p.decal(c.ring(b[0], b[1], 4.8, 1.2) & e, paper, -3)
    p.decal(c.ring(b[0], b[1], 2.2, 1.2) & e, paper, -3)
    p.part(c.circle(b[0] - 1.0, b[1] + 1.0, 2.2), wood, 'sphere', base=0, sep=True)
    p.part(c.circle(a[0] - 2.5, a[1] + 2.5, 5.6), wood, 'sphere', base=0, sep=True, tex='wood', axis=ang, spec=(a[0] - 4.5, a[1] + 0.5))
    # the tie band across the middle and the cord to the tag
    mt = L / 2.0
    band = fr.prof(c, [(mt - 2.4, 7.6), (mt + 2.4, 7.6)]) & (body | dilate4(body))
    p.part(band, tie, 'ray_soft', base=0, sep=True, rim=False)
    p.decal(fr.prof(c, [(mt - 0.5, 7.6), (mt + 0.5, 7.6)]) & band, tie, -2)
    kx, ky = fr.P(mt, 7.8)
    p.line([(kx, ky), (kx + 4, ky + 6), (40, 38)], tie, 0, 1.4, only_on=False)
    tag = c.rrect(33, 36, 56, 58, 1.8)
    p.part(tag, tag_m, 'bevel', base=0, sep=True, hw=1, sw=1, tex='paper', rim=False)
    p.decal(c.circle(44.5, 39.5, 1.1), tag_m, -3)
    EMBLEMS_HD[element](p, 44.5, 48.5, erode4(tag), 0.85)


def make_manual_hd(element, tie=RED, paper=PAPER, stained=False):
    def draw(p):
        manual_hd(p, element, tie, paper, stained)
    return draw


# ============================================================================= curios
def dusty_curio_hd(p):
    """An old trinket of uncertain worth: a bronze ding under a hundred years of grime, its cloud-scroll band half
    hidden, one ear still bright."""
    c = p.c
    bel, rim = ding_hd(p, BRONZE, BRONZE, cy=39.0, rx=21.0, ry=14.5, rim=(20.0, 25.0), tex='metal')
    pts = [(12 + x, 32.5 + 1.6 * math.sin(x / 2.6)) for x in range(0, 41)]
    p.decal(c.polyline(pts, 1.4) & erode4(bel), BRONZE, -2)
    p.decal(c.polyline([(x, y - 1.4) for x, y in pts], 1.0) & erode4(bel), BRONZE, 1)
    for (x, y, rx, ry) in ((21, 43, 6.0, 4.0), (37, 46, 6.5, 4.4), (46, 34, 4.2, 3.0), (27, 28, 3.6, 2.4), (14, 22.5, 6.0, 1.6), (34, 22.5, 7.0, 1.6)):
        d = c.ellipse(x, y, rx, ry) & (bel | rim)
        p.part(d, DUST, 'flat', base=-1, sep=False, rim=False)
        p.decal(c.ellipse(x - rx * 0.2, y - ry * 0.3, rx * 0.5, ry * 0.45) & d, DUST, 0)
    p.part(c.taper((44, 28), (48, 22), (56, 18), 1.6, 0.8), DUST, 'flat', base=1, sep=False, rim=False)
    p.sparkle(50, 15, 1)


def jade_trinket_hd(p):
    """A small carving of real river jade: a grain-pattern bi on a red cord, its dots raised in rings."""
    c = p.c
    p.part(c.ring(32, 9.0, 4.4, 2.2) & c.box(0, 0, 64, 11.5), RED, 'ray_soft', base=0, sep=False, rim=False)
    p.part(c.box(30.8, 11, 33.2, 15), RED, 'flat', base=0, sep=False, rim=False)
    disc, band = bi_hd(p, JADE, cx=32, cy=36, r=23.0, hole=6.5, rim=2.6)
    for k in range(10):
        a = k * 2 * math.pi / 10 + 0.3
        x, y = 32 + 14.5 * math.cos(a), 36 + 14.5 * math.sin(a)
        p.decal(c.circle(x + 0.6, y + 0.6, 1.5) & band, JADE, -2)
        p.decal(c.circle(x, y, 1.4) & band, JADE, 2)
    p.decal(c.ring(32, 36, 10.4, 1.0) & disc, JADE, -2)


def fake_jade_hd(p):
    """Green glass: the same bi with a chip out of its rim, bubbles trapped in it and a crack, too bright to be jade."""
    c = p.c
    disc, band = bi_hd(p, GREEN_GLASS, cx=32, cy=32, r=25.0, hole=7.0, tex='glass', glint=False)
    chip = c.poly([(46, 50), (56, 40), (57, 52)])
    p.erase(chip)
    for (x, y, r) in ((21, 40, 2.0), (39, 22, 1.7), (43, 40, 2.3), (25, 24, 1.3)):
        p.decal(c.ring(x, y, r + 0.6, 1.0) & disc & ~chip, GREEN_GLASS, 2)
        p.decal(c.circle(x - r * 0.4, y - r * 0.4, 0.7) & disc, GREEN_GLASS, 3)
    p.decal(lmask(p, [(14, 33), (20, 35), (22, 41), (19, 47)]) & disc, GREEN_GLASS, -3)
    p.decal(c.ellipse(20, 17, 4.5, 2.4) & disc, WHITE, 0)


def coin_hd(p, cx, cy, r, mat, string):
    """An old coin: a sphere-lit disc with a raised rim, four characters round its square hole, the string through it."""
    c = p.c
    m = c.circle(cx, cy, r)
    p.part(m, mat, 'sphere', base=0, sep=True, cx=cx - r * 0.3, cy=cy - r * 0.3, rx=r * 1.3, ry=r * 1.3, tex='metal')
    p.decal(c.ring(cx, cy, r, 1.2) & m, mat, -1)
    p.decal(c.ring(cx, cy, r - 1.2, 0.9) & m, mat, 2)
    hole = c.box(cx - 2.2, cy - 2.2, cx + 2.2, cy + 2.2)
    p.decal(dilate4(hole) & m & ~hole, mat, -2)
    p.decal(hole & m, string, -1)
    p.decal(c.box(cx - 0.8, cy - 2.2, cx + 0.8, cy + 2.2) & m, string, 1)
    for (dx, dy) in ((0, -5.4), (0, 5.4), (-5.4, 0), (5.4, 0)):
        p.decal(c.box(cx + dx - 1.2, cy + dy - 1.2, cx + dx + 1.2, cy + dy + 1.2) & m, mat, -2)
        p.decal(c.box(cx + dx - 0.4, cy + dy - 0.4, cx + dx + 0.4, cy + dy + 0.4) & m, mat, 1)
    return m


def string_of_old_coins_hd(p):
    """Coins from a dynasty nobody remembers, strung on red silk: four on the diagonal, one gone green."""
    c = p.c
    p.part(c.seg(6, 58, 58, 6, 2.0), RED, 'ray_soft', base=0, sep=False, rim=False)
    for k, mat in enumerate((BRONZE, BRONZE, VERDIGRIS, BRONZE)):
        x, y = 12.5 + k * 13.0, 51.5 - k * 13.0
        coin_hd(p, x, y, 10.0, mat, RED)
    p.part(c.circle(6, 58, 2.2) | c.circle(58, 6, 2.2), RED, 'sphere', base=0, sep=True, rim=False)
    p.sparkle(46, 12, 1)


# ============================================================================= puppetry and research
def spirit_wood_hd(p):
    """Pale wood that holds a trace of Qi: a log on the diagonal, its cut end showing the rings, the Qi running as
    light along the grain."""
    c = p.c
    fr = Frame((11.0, 48.0), 30.0)
    log = fr.prof(c, [(0.0, 8.5), (50.0, 8.5)])
    p.cylinder(fr, log, 8.5, PALEWOOD, sep=True, tex='wood', axis=30.0)
    end = c.ellipse(11.0, 48.0, 5.2, 8.8)
    p.part(end, PALEWOOD, 'flat', base=1, sep=True, rim=False)
    for r in (5.6, 3.0):
        p.decal(c.ring(11.0, 48.0, r * 0.6, 0.9, ry=r) & end, PALEWOOD, -2)
    p.decal(c.circle(11.0, 48.0, 0.9) & end, QI, 2)
    t, w = fr.along(c)
    inner = erode4(log) & ~end & (t > 4.0) & (t < 48.0)
    for (off, lv, wd) in ((-3.4, 0, 1.6), (2.4, 1, 2.0)):
        vein = c.polyline([fr.P(5.0, off), fr.P(20.0, off + 0.8), fr.P(34.0, off - 0.6), fr.P(48.0, off + 0.4)], wd) & inner
        p.part(vein, QI, 'flat', base=lv, sep=False, rim=False)
        p.decal(c.polyline([fr.P(12.0, off), fr.P(26.0, off + 0.4)], 1.0) & vein, QI, 3)
    p.sparkle(*fr.P(30.0, -6.5), 1)


def puppet_core_hd(p):
    """A carved jade heart that lets a puppet follow orders, set in an octagonal frame of dark wood pegged with gold."""
    c = p.c
    frame = c.poly([(20, 6), (44, 6), (58, 20), (58, 44), (44, 58), (20, 58), (6, 44), (6, 20)])
    p.part(frame, DARKWOOD, 'ray', base=0, sep=True, tex='wood', axis=90)
    inner = c.poly([(22, 11), (42, 11), (53, 22), (53, 42), (42, 53), (22, 53), (11, 42), (11, 22)])
    p.decal(inner & ~erode4(erode4(inner)), DARKWOOD, -3)
    p.decal(erode4(erode4(inner)), DARKWOOD, -1)
    heart = c.circle(25.0, 26.0, 8.6) | c.circle(39.0, 26.0, 8.6) | c.poly([(17.2, 29.0), (46.8, 29.0), (32.0, 47.0)])
    p.part(heart, JADE, 'sphere', base=0, sep=True, cx=27, cy=22, rx=20, ry=20, tex='jade')
    p.decal(lmask(p, [(24, 25), (32, 33), (40, 25)]) & erode4(heart), JADE, 3)
    for (x, y) in ((20, 8.5), (44, 8.5), (55.5, 20), (55.5, 44), (44, 55.5), (20, 55.5), (8.5, 20), (8.5, 44)):
        p.part(c.circle(x, y, 1.6), GOLD, 'sphere', base=1, sep=True, rim=False)
    p.sparkle(22, 20, 1)


def array_plate_hd(p, kind='guard'):
    """A bronze plate with an array engraved in it and lit: the guarding array (a cyan trigram ring), the killing
    array (red, four blades pointing in) or the binding array (violet, a chain spiralling in)."""
    c = p.c
    ink, glow = {'guard': (QI, 1), 'killing': (M('red', 'light'), 0), 'binding': (VIOLET, 1)}[kind]
    cx, cy = 32.0, 32.0
    p.part(c.rrect(8, 12, 56, 59, 4.0), BRONZE, 'flat', base=-2, sep=False, rim=False)
    plate = c.rrect(8, 8, 56, 55, 4.0)
    p.part(plate, BRONZE, 'bevel', base=0, sep=True, hw=3, sw=3, tex='metal')
    border = c.rrect(12, 12, 52, 51, 2.5)
    p.decal(border & ~erode4(border), BRONZE, -2)
    p.decal(erode4(border) & ~erode4(erode4(border)) & c.box(0, 0, 64, 40), BRONZE, 1)
    ring = c.ring(cx, cy, 15.0, 2.4)
    p.part(ring, ink, 'flat', base=glow, sep=True, rim=False)
    if kind == 'guard':
        for k in range(8):
            a = k * math.pi / 4
            x, y = cx + 9.6 * math.cos(a), cy + 9.6 * math.sin(a)
            bar = c.seg(x - 2.6 * math.sin(a), y + 2.6 * math.cos(a), x + 2.6 * math.sin(a), y - 2.6 * math.cos(a), 1.8)
            p.part(bar, ink, 'flat', base=glow + (1 if k % 2 else 0), sep=True, rim=False)
        p.part(c.circle(cx, cy, 2.4), GOLD, 'sphere', base=1, sep=True, rim=False)
    elif kind == 'killing':
        for k in range(4):
            a = k * math.pi / 2 + math.pi / 4
            ox, oy = cx + 13.5 * math.cos(a), cy + 13.5 * math.sin(a)
            ix, iy = cx + 2.6 * math.cos(a), cy + 2.6 * math.sin(a)
            px, py = -math.sin(a), math.cos(a)
            p.part(c.poly([(ox + px * 3.4, oy + py * 3.4), (ox - px * 3.4, oy - py * 3.4), (ix, iy)]), ink, 'ray_soft', base=glow, sep=True, rim=False)
        p.part(c.circle(cx, cy, 2.2), GOLD, 'sphere', base=1, sep=True, rim=False)
    else:
        for k in range(7):
            a = k * 0.95
            r = 11.0 - k * 1.25
            p.part(c.ring(cx + r * math.cos(a), cy + r * math.sin(a), 2.6, 1.3), ink, 'flat', base=glow + (1 if k % 2 else 0), sep=True, rim=False)
    for (x, y) in ((15, 15), (49, 15), (15, 48), (49, 48)):
        p.part(c.circle(x, y, 1.7), GOLD, 'sphere', base=1, sep=True, rim=False)
    p.sparkle(17, 21, 1)


def sphere_comprehension_stone_hd(p):
    """A stone that holds a folded world: a violet orb on a dark wood stand, a ringed island, a peak and a sweep of
    stars inside it; the Will grade's aura in the orb's own light."""
    c = p.c
    p.part(c.poly([(16, 58.5), (21, 49), (43, 49), (48, 58.5)]), DARKWOOD, 'ray', base=0, sep=True, tex='wood', axis=90)
    p.part(c.ellipse(32, 49.5, 14.5, 4.0), DARKWOOD, 'ray_soft', base=1, sep=True)
    orb = c.circle(32, 30, 21.5)
    p.part(orb, VIOLET, 'sphere', base=-1, sep=True, cx=25, cy=23, rx=27, ry=27, tex='glass')
    p.decal(c.ellipse(32, 36, 11.0, 3.2) & orb, JADE, 0)
    p.decal(c.ellipse(32, 35, 8.0, 1.8) & orb, JADE, 1)
    p.decal(c.poly([(26, 35.5), (31.5, 24), (37, 35.5)]) & orb, STONE, 0)
    p.decal(c.poly([(28.5, 30), (31.5, 24), (33, 27)]) & orb, STONE, 2)
    p.decal(c.arc(32, 30, 15.5, 2.0, 195, 345) & orb, QI, 1)
    p.decal(c.arc(32, 30, 15.5, 1.0, 230, 320) & orb, QI, 3)
    for (x, y) in ((19, 24), (44, 21), (23, 41), (43, 39), (34, 16)):
        p.decal(S.star4(c, x, y, 1) & orb, WHITE, 0)
    p.decal(c.ellipse(23, 19, 5.0, 3.0) & orb, VIOLET, 3)
    p.glow('#B18DE2', kit('will')['glow'][1])


# ============================================================================= the table
WORKSHOP_HD = [
    ('pet_book_' + _id, make_book_hd(_cover, 'paw')) for _id, _cover in PET_COVER.items()
] + [
    ('manual_stonebody_canon', make_book_hd(ELEMENT_COVER['earth'], 'earth')),
    ('manual_willow_breath_art', make_book_hd(ELEMENT_COVER['wood'], 'wood')),
    ('manual_emberheart_sutra', make_book_hd(ELEMENT_COVER['fire'], 'fire')),
    ('manual_tidal_sovereign_scripture', make_book_hd(ELEMENT_COVER['water'], 'water')),
    ('manual_nine_winds_canon', make_book_hd(ELEMENT_COVER['wind'], 'wind')),
    ('inner_art_manual', make_manual_hd('water', tie=M('violet', 'silk'))),   # S48 Inner Arts
    ('torn_manual', make_book_hd(FADED, None, torn=True, stain=True)),
    ('mudwater_manual', make_manual_hd('water', tie=HEMP, paper=MUDPAPER, stained=True)),
    ('manual_rain_of_reeds', make_manual_hd('reed', tie=JADE)),
    ('manual_ember_burst', make_manual_hd('fire', tie=GOLD)),
    ('dusty_curio', dusty_curio_hd), ('jade_trinket', jade_trinket_hd), ('fake_jade', fake_jade_hd),
    ('string_of_old_coins', string_of_old_coins_hd), ('spirit_wood', spirit_wood_hd),
    ('puppet_core', puppet_core_hd), ('array_plate', lambda p: array_plate_hd(p, 'guard')),
    ('killing_array_plate', lambda p: array_plate_hd(p, 'killing')), ('binding_array_plate', lambda p: array_plate_hd(p, 'binding')),
    ('sphere_comprehension_stone', sphere_comprehension_stone_hd),
]

for _id, _draw in WORKSHOP_HD:
    register(FAM, _id, _draw, GROUP)
    hd(_id, _draw)
