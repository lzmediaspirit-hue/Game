"""Miscellany (HD, Style A): the manuals, pages and scrolls, the tokens and keys, the goods and components, the eggs,
the beast bags, the incenses, the natural treasures, the Starsea charts and ships, the rite tablets and the rest, at 64
art px shown 1:1 in the 76 px slot, with a native @32 render for the HUD item ring and the small slots.

One language per kind (the HD section's templates): a page is paper with its laid lines and columns of script, a closed
scroll lies on the diagonal with its tie and tag, a hand scroll opens between its rollers; a token hangs upright from a
cord loop and bead with a tassel below, its face carved inside a keyline or a rim; a bag is a drawstring pouch tied at
the neck; an egg sits in its nest; incense stands in a bowl or a cup with its hours on the label; a tablet stands in its
stepped pedestal. The grade shows by kit and trim and, from Mystic up, by the aura in the object's own light.
"""
import math

import numpy as np

from pix import Frame, Ramp, WHITE, dilate4, dilate8, erode4, rgb, shift
from palette import GLOW_STRENGTH, M, TEX, mat7
from registry import hd, register
import shapes as S
from families.weapons import fitting_hd, tassel_hd
from families.beast_parts import GRADE_HD, XY, cap_hd, cord_hd, knot_hd, lmask, vial_hd
from families.herbs import leaf_hd, lotus_front, lotus_hd, pad_hd, stem_hd

FAM, GROUP = 'items', 'misc'
ART = 64   # HD (tools/icons/README.md, "How to convert a family")


# ============================================================================= HD (Style A, 64 icon space)
# Every icon is one drawing `draw(p)` in a 64 x 64 icon space (tools/icons/README.md, "HD drawing model"), the object
# inside the 4-px margin; the same description renders at 64 and at 32. One language per kind: a manual or a page is
# paper with its laid lines and columns of script, a closed scroll lies on the diagonal with its tie and tag, a hand
# scroll opens between two rollers; a token hangs upright from its cord loop and bead with a tassel below, its face
# carved inside a keyline (a rim from Earth); a bag is a drawstring pouch tied at the neck; an egg sits in its nest;
# incense stands in a bowl or a cup; the goods, the treasures, the ships and the tablets are one-offs on the shared
# builders (the weapons' tassel, the beast parts' cords, vials and heaps, the herbs' leaves and lotus, the minerals'
# dish). The grade shows by kit and trim (a cord, a bead, a rim, a richer holder) and, from Mystic up, by the aura as
# stepped glow bands in the object's own light at the grade's strength; never by colour alone.

PAPER, TALISMAN, DARKWOOD, WOOD, BAMBOO, HEMP, STRAW, LEATHER = (M('paper'), M('talisman', 'paper'), M('darkwood'), M('wood'), M('bamboo'), M('hemp'),
                                                                 M('straw'), M('leather'))
JADE, DEEPJADE, GOLD, BRONZE, IRON, SILVER, COPPER, STONE, BONE = (M('jade'), M('deepjade', 'jade'), M('gold'), M('bronze'), M('iron'), M('silver'),
                                                                   M('copper'), M('stone'), M('bone', 'porcelain'))
RED, SEAL, NAVY, SKY, QI, VIOLET, PLUM, INDIGO, VIOLETSILK = (M('red', 'silk'), M('seal'), M('navy', 'silk'), M('sky', 'silk'), M('qi', 'gem'),
                                                              M('violet', 'silk'), M('plum', 'silk'), M('indigo', 'silk'), M('violetsilk'))
PORCELAIN, CLAY, MUD, INK, MIST, CLOUD, RICE, PEARL, LOTUS, LEAF, MOSS, FIRE, EMBER, SAND, TEA = (
    M('porcelain'), M('clay'), M('mud'), M('ink'), M('mist'), M('cloud'), M('rice'), M('pearl'), M('lotuspink', 'porcelain'), M('leaf'), M('moss'),
    M('fire'), M('ember'), M('sand'), M('tea'))
STARLIGHT, LANTERNBRONZE, COMETIRON, STORM, CYAN, VENOM = M('starlight'), M('lanternbronze'), M('cometiron'), M('storm'), M('cyan'), M('venom', 'glass')
AGED_HD = mat7(Ramp(['#5A4A30', '#8E774E', '#C4AA78', '#DCC79A', '#F2E6C4'], '#261E12'), 'paper')
LEDGER_HD = mat7(Ramp(['#1A1414', '#2E2222', '#4A3432', '#6E4E48', '#98746A'], '#0A0707'), 'leather')
KITE_HD = mat7(Ramp(['#6A2A2A', '#B04438', '#E86A4E', '#F7B07A', '#FFE3B8'], '#2A0E0E'), 'paper')
# Act II · Starsea: star paper, sky ink, the ward's Qi mist and black lacquer
STARPAPER_HD = mat7(Ramp(['#4A5664', '#8793A3', '#C6CFDA', '#E6EBF0', '#FFFDF4'], '#19202A'), 'paper')
SKY_INK_HD = mat7(Ramp(['#0C0E26', '#191D46', '#2A3070', '#4652A0', '#8290D4'], '#050616'), 'glass')
QI_MIST_HD = mat7(Ramp(['#1B5A6E', '#2F86A0', '#58B6CC', '#94DBE6', '#D6F6FA'], '#0B2530'), 'light')
LACQUER_HD = mat7(Ramp(['#07080B', '#121419', '#22262F', '#3C4250', '#7D879C'], '#020203'), 'porcelain')
# Act III · Lantern Star Field: the wyrm egg's shell, the smoke of lantern incense
WYRM_HD = mat7(Ramp(['#6A6478', '#A6A0B4', '#DCD8E6', '#F3F1F7', '#FFFFFF'], '#24212E'), 'porcelain')
SMOKE_HD = mat7(Ramp(['#3C3A52', '#626080', '#9492B2', '#C4C2DA', '#ECEAF6'], '#16151F'), 'matte')
# V10c · the rite tablets' star jade and cloud stone; the components' amber and red lacquer
STARJADE_HD = mat7(Ramp(['#0E1030', '#1C2258', '#2E3A86', '#4A5CB4', '#8294DC'], '#060818'), 'jade')
CLOUDSTONE_HD = mat7(Ramp(['#6C7E8A', '#A2B4BE', '#D8E2E6', '#F0F5F6', '#FFFFFF'], '#222C33'), 'porcelain')
AMBER_HD = mat7(Ramp(['#5A2E08', '#9A5410', '#DC8E22', '#F6C257', '#FFF0B8'], '#241204'), 'glass')
REDLAC_HD = mat7(Ramp(['#3E0A0E', '#761418', '#B82A26', '#E0503E', '#FF9A80'], '#1A0406'), 'porcelain')
# v1.2 Phase D · Ash and Tide: Kharn's crimson steel, the Copperjaw box's black-red lacquer
CRIMSON_HD = mat7(Ramp(['#3A0A10', '#6E141C', '#A8222A', '#D84A44', '#F0907A'], '#1A0407'), 'metal')
BLACKLAC_HD = mat7(Ramp(['#150609', '#2C0C12', '#4A141C', '#70222A', '#9E3C40'], '#080203'), 'porcelain')
SUN_GLOW_HD, STAR_GLOW_HD, WARD_GLOW_HD, LANTERN_GLOW_HD = '#FFC870', '#BFD8FF', '#8AEBEE', '#F3E3A6'


def glow_hd(p, grade, col):
    """The aura from Mystic up, in the object's own light at the grade's strength."""
    if grade in GLOW_STRENGTH:
        p.glow(col, GLOW_STRENGTH[grade])


def faint_hd(p, mask, col, al):
    """Semi-transparent pixels on empty canvas only (a ward ring behind an object): no body, so no outline."""
    c = p.c
    free = mask & (c.alpha == 0)
    c.rgb[free] = rgb(col)
    c.alpha[free] = al


def stamp_hd(p, x, y, s, clip, mat=None):
    """A square seal stamped on paper, its carved mark a lighter red inside."""
    c = p.c
    mat = mat or SEAL
    p.decal(c.box(x - s, y - s, x + s, y + s) & clip, mat, 0)
    p.decal((c.box(x - s * 0.5, y - s * 0.55, x + s * 0.5, y - s * 0.15) | c.box(x - s * 0.2, y - s * 0.15, x + s * 0.2, y + s * 0.55)) & clip, mat, 2)


# ----------------------------------------------------------------------------- pages and scrolls
def page_hd(p, x0, y0, x1, y1, paper=None, fold=True, torn=False, cols=4, ink=None, ink_lv=0, fold_size=9.0):
    """A sheet of paper with its laid lines: a corner folded back at the top right, a torn foot, and columns of script
    (dashes down the page, right to left) in `ink`."""
    c = p.c
    paper, ink = paper or PAPER, ink or INK
    m = c.box(x0, y0, x1, y1)
    if torn:
        X, Y = XY(p)
        xi = np.floor(X).astype(int)
        m &= ~(((Y > y1 - 2.4) & ((xi * 7) % 5 == 0)) | ((Y > y1 - 1.3) & ((xi * 3) % 4 == 1)))
    f = fold_size
    if fold:
        m &= ~c.poly([(x1 - f, y0 - 1), (x1 + 1, y0 - 1), (x1 + 1, y0 + f)])
    p.part(m, paper, 'bevel', base=0, sep=False, hw=1, sw=1, tex='paper', rim=False)
    if fold:
        flap = c.poly([(x1 - f, y0), (x1 - f, y0 + f), (x1, y0 + f)]) & m
        p.part(flap, paper, 'flat', base=-1, sep=True, rim=False)
        p.line([(x1 - f, y0 + 0.5), (x1 - 0.5, y0 + f)], paper, 1, 1.0)
    for k in range(cols):
        x = x1 - 6.0 - k * 6.0
        top = y0 + 5.0 + (f + 1.0 if fold and k == 0 else 0.0)
        bot = y1 - 5.0 - (k * 4) % 9
        y, i = top, 0
        while y + 3.4 <= bot:
            if (i + k) % 4 != 3:
                p.decal(c.box(x, y, x + 2.2, y + 3.4) & m, ink, ink_lv)
            y += 5.2
            i += 1
    return m


def scroll_hd(p, a=(13.0, 49.0), b=(46.0, 13.0), hw=7.4, paper=None, wood=None, tie=None):
    """A closed scroll on the diagonal: the roll with its laid lines, the rolled edge (a spiral) at the far end, the
    roller knob at the near end, the tie band across the middle. Returns the frame, its length and the body."""
    c = p.c
    paper, wood, tie = paper or PAPER, wood or DARKWOOD, tie or RED
    ang = math.degrees(math.atan2(-(b[1] - a[1]), b[0] - a[0]))
    fr = Frame(a, ang)
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    body = fr.prof(c, [(-2.0, hw), (L + 1.0, hw)])
    p.cylinder(fr, body, hw, paper, sep=False, tex='paper')
    e = c.circle(b[0], b[1], hw - 0.4)
    p.part(e, paper, 'flat', base=-1, sep=True, rim=False)
    p.decal(c.ring(b[0], b[1], hw * 0.65, 1.2) & e, paper, -3)
    p.decal(c.ring(b[0], b[1], hw * 0.3, 1.2) & e, paper, -3)
    p.part(c.circle(b[0] - 1.0, b[1] + 1.0, hw * 0.3), wood, 'sphere', base=0, sep=True)
    p.part(c.circle(a[0] - 2.5, a[1] + 2.5, hw * 0.76), wood, 'sphere', base=0, sep=True, tex='wood', axis=ang, spec=(a[0] - 4.5, a[1] + 0.5))
    mt = L / 2.0
    band = fr.prof(c, [(mt - 2.4, hw + 0.2), (mt + 2.4, hw + 0.2)]) & (body | dilate4(body))
    p.part(band, tie, 'ray_soft', base=0, sep=True, rim=False)
    p.decal(fr.prof(c, [(mt - 0.5, hw + 0.2), (mt + 0.5, hw + 0.2)]) & band, tie, -2)
    return fr, L, body


def tag_hd(p, x0, y0, x1, y1, cord_from, cord=None, mat=None):
    """A paper tag hung on a cord from `cord_from`, its hole punched near the top."""
    c = p.c
    cord, mat = cord or RED, mat or TALISMAN
    kx, ky = cord_from
    p.line([(kx, ky), (kx + 4.0, ky + 6.0), ((x0 + x1) / 2.0, y0 + 3.5)], cord, 0, 1.4, only_on=False)
    tag = c.rrect(x0, y0, x1, y1, 1.8)
    p.part(tag, mat, 'bevel', base=0, sep=True, hw=1, sw=1, tex='paper', rim=False)
    p.decal(c.circle((x0 + x1) / 2.0, y0 + 3.5, 1.1), mat, -3)
    return tag


def hand_scroll_hd(p, paper=None, roller=None, knob=None, y0=14.0, y1=50.0, x0=12.0, x1=52.0):
    """An open hand scroll: the sheet with its laid lines held flat between two upright rollers, a knob at each end
    of both."""
    c = p.c
    paper, roller, knob = paper or PAPER, roller or DARKWOOD, knob or JADE
    sheet = c.box(x0, y0 + 1.5, x1, y1 - 1.5)
    p.part(sheet, paper, 'bevel', base=0, sep=False, hw=1, sw=1, tex='paper', rim=False)
    for x in (x0 - 3.0, x1 + 3.0):
        fr = Frame((x, y1 + 3.0), 90.0)
        rod = fr.prof(c, [(0.0, 3.0), (y1 - y0 + 6.0, 3.0)])
        p.cylinder(fr, rod, 3.0, roller, sep=True, tex='wood', axis=90.0)
        for y in (y0 - 4.5, y1 + 4.5):
            p.part(c.ellipse(x, y, 3.6, 2.4), knob, 'sphere', base=0, sep=True, tex=TEX.get(knob.kind))
    return sheet


def manual_page_hd(p):
    """A loose manual page: three columns of script, a stance figure sketched in jade ink at the lower left, the
    library's seal at the head."""
    c = p.c
    m = page_hd(p, 12.0, 6.0, 52.0, 58.0, cols=3)
    fig = (c.circle(21.0, 34.0, 2.8) | c.polyline([(21.0, 37.0), (21.0, 46.0)], 2.2) | c.polyline([(14.0, 41.0), (28.0, 39.0)], 1.8)
           | c.polyline([(21.0, 46.0), (15.5, 53.0)], 2.0) | c.polyline([(21.0, 46.0), (26.5, 52.0)], 2.0))
    p.decal(fig & m, JADE, -1)
    stamp_hd(p, 20.0, 14.0, 4.2, m)


def lu_journal_page_hd(p):
    """A page of Lu's journal, aged and leaning, lines of script running with the lean, a river sketched in Qi ink
    across its foot, a ring where a cup stood, a stain in one corner."""
    c = p.c
    m = c.poly([(10.0, 12.0), (46.0, 5.0), (54.0, 52.0), (18.0, 59.0)])
    p.part(m, AGED_HD, 'bevel', base=0, sep=False, hw=1, sw=1, tex='paper', rim=False)
    for k in range(6):
        y = 15.0 + k * 6.4
        L = 30.0 - (k * 5) % 9
        p.line([(17.0 + k * 0.9, y + 2.0), (17.0 + k * 0.9 + L, y + 2.0 - L * 0.19)], AGED_HD, -3, 1.6)
    p.line(S.curve_pts((20.0, 52.0), (30.0, 40.0), (48.0, 46.0), 12), QI, -1, 1.8)
    p.line(S.curve_pts((22.0, 55.0), (32.0, 45.0), (49.0, 50.0), 12), QI, -2, 1.2)
    p.decal(c.ring(40.0, 22.0, 6.0, 1.6) & m, AGED_HD, -2)
    p.decal(c.ellipse(15.0, 50.0, 5.0, 4.0) & m, AGED_HD, -2)
    fold = c.poly([(46.0, 5.0), (48.5, 16.0), (37.0, 14.0)]) & m
    p.part(fold, AGED_HD, 'flat', base=-1, sep=True, rim=False)


def riverbreath_scroll_hd(p):
    """The Riverbreath inheritance scroll: a hand scroll open on three waves of the method in Qi ink under a title
    column and the sect's seal, its rollers knobbed in Qi jade."""
    c = p.c
    sheet = hand_scroll_hd(p, knob=M('qi'))
    for k, y in enumerate((27.0, 34.0, 41.0)):
        p.line([(16.0 + x, y + 1.8 * math.sin((x + k * 3) / 3.4)) for x in range(0, 33)], QI, 1 if k else 2, 1.6)
    for y in (19.0, 24.0):
        p.decal(c.box(17.0, y, 19.4, y + 3.2) & sheet, INK, 0)
    stamp_hd(p, 45.0, 21.0, 3.6, sheet)


def recipe_scroll_hd(p):
    """A recipe scroll: a closed scroll with darkwood rollers and a red tie, a tag hung from the tie with a pill
    drawn on it."""
    c = p.c
    fr, L, body = scroll_hd(p, tie=RED)
    kx, ky = fr.P(L / 2.0, 7.8)
    tag = tag_hd(p, 33.0, 36.0, 56.0, 58.0, (kx, ky))
    pill = c.circle(44.5, 48.5, 5.0)
    p.decal(pill & tag, M('red'), 0)
    p.decal(c.circle(42.5, 46.5, 1.6) & tag, M('red'), 3)
    p.decal(c.arc(44.5, 48.5, 4.0, 1.4, 200, 340) & tag, M('red'), -2)


# ----------------------------------------------------------------------------- tokens and keys
def token_hd(p, body, shape='tablet', cord=None, cx=32.0, top=14.0, bottom=48.0, w=14.0, rim=None, lv=1, tassel=True, tex=None):
    """A token hung from a cord loop with a gold bead: a tablet or a disc, its face inside a carved keyline (or a
    metal rim), a tassel below in the cord. Returns the body and the face."""
    c = p.c
    cord = cord or RED
    loop = c.ring(cx, top - 3.6, 4.4, 2.0) & c.box(0, 0, 64, top + 0.5)
    p.part(loop, cord, 'ray_soft', base=0, sep=False, rim=False)
    p.part(c.circle(cx, top - 8.2, 2.4), GOLD, 'sphere', base=0, sep=True, tex='metal')
    if tassel:
        tassel_hd(p, dict(tassel=cord, bead=GOLD, lv=lv), cx, bottom + 1.0, 1.4)
    if shape == 'tablet':
        def tab(w, top, bottom):
            return c.poly([(cx - w, top + 5.0), (cx - w + 5.0, top), (cx + w - 5.0, top), (cx + w, top + 5.0), (cx + w, bottom - 4.0),
                           (cx + w - 4.0, bottom), (cx - w + 4.0, bottom), (cx - w, bottom - 4.0)])
        m, inner = tab(w, top, bottom), tab(w - 3.0, top + 3.0, bottom - 3.0)
    else:
        r = (bottom - top) / 2.0
        m, inner = c.circle(cx, top + r, r), c.circle(cx, top + r, r - 3.0)
    p.part(m, body, 'ray', base=0, sep=True, tex=tex or TEX.get(body.kind))
    if rim is not None:
        p.part(m & ~inner, rim, 'ray_soft', base=0, sep=True, tex=TEX.get(rim.kind))
    else:
        key = inner & ~erode4(inner)
        p.decal(key, body, -2)
        p.decal(shift(key, -1, -1) & ~inner & m, body, 2)
    return m, inner


def river_token_hd(p):
    """Lu's River Token: a jade tablet on a Qi-blue cord, three waves of the river cut deep in its face."""
    c = p.c
    m, inner = token_hd(p, JADE, 'tablet', cord=M('qi', 'silk'), lv=0)
    p.decal(inner, DEEPJADE, 0)
    for k, y in enumerate((25.0, 32.0, 39.0)):
        pts = [(21.0 + x, y + 1.8 * math.sin((x + k * 3) / 3.0)) for x in range(0, 23)]
        p.line(pts, JADE, 1, 1.6)
        p.line([(x, yy + 1.4) for x, yy in pts], DEEPJADE, -3, 1.0)


def jade_token_hd(p):
    """The Jade Sect's token: a jade disc pierced at its heart, a ring cut round the hole and four gold studs."""
    c = p.c
    m, inner = token_hd(p, JADE, 'disc', cord=RED, lv=0)
    hole = c.circle(32.0, 31.0, 4.4)
    p.decal(c.ring(32.0, 31.0, 11.0, 1.8) & inner, JADE, 1)
    p.decal(dilate4(hole) & ~hole, JADE, -2)
    p.erase(hole)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        x, y = 32.0 + math.cos(a) * 8.0, 31.0 + math.sin(a) * 8.0
        p.decal(c.circle(x, y, 1.6) & inner, GOLD, 0)
        p.decal(c.circle(x - 0.5, y - 0.5, 0.6) & inner, GOLD, 3)


def cloud_token_hd(p):
    """The Cloud Sect's token: a porcelain disc on a sky cord, a cloud raised in sky blue on its face."""
    c = p.c
    m, inner = token_hd(p, PORCELAIN, 'disc', cord=SKY, lv=0)
    cl = (c.ellipse(26.0, 34.0, 6.0, 5.0) | c.ellipse(33.0, 29.0, 7.5, 6.5) | c.ellipse(40.0, 34.5, 5.5, 4.5) | c.box(22.0, 34.0, 44.0, 38.0)) & inner
    p.part(cl, SKY, 'ray', base=0, sep=True, rim=False)
    p.decal(c.arc(33.0, 29.0, 4.2, 1.4, 90, 300) & cl, SKY, 2)
    p.decal(c.box(23.0, 36.5, 43.0, 38.0) & cl, SKY, -2)


def alliance_token_hd(p):
    """The Nine Peaks Alliance token: a navy-jade disc with a gold rim on a gold cord, three gold summits and a
    gold ring on its face, lit in gold (Spirit)."""
    c = p.c
    m, inner = token_hd(p, M('navy', 'jade'), 'disc', cord=M('gold', 'silk'), rim=GOLD, lv=4, tex='jade')
    peaks = c.poly([(20.0, 40.0), (26.0, 27.0), (29.5, 33.0), (32.0, 20.0), (35.0, 33.0), (38.0, 27.0), (44.0, 40.0)]) & inner
    p.decal(peaks, GOLD, 1)
    p.decal(c.poly([(32.0, 20.0), (35.0, 33.0), (38.0, 27.0), (44.0, 40.0), (32.0, 40.0)]) & peaks, GOLD, -1)
    p.decal(c.ring(32.0, 31.0, 13.0, 1.4) & inner, GOLD, 0)
    p.sparkle(45.0, 20.0, 1)
    glow_hd(p, 'spirit', '#E5B84C')


def ironroot_token_hd(p):
    """The Ironroot Token: an iron-hard sliver of root on the diagonal, the clan's mark cut into it and filled with
    gold, a hemp cord through its end, lit in gold (Spirit)."""
    c = p.c
    root = c.taper((14.0, 54.0), (28.0, 34.0), (52.0, 12.0), 11.0, 4.0)
    p.part(root, IRON, 'ray', base=-1, sep=True, tex='wood', axis=45.0)
    p.part(c.taper((22.0, 42.0), (15.0, 36.0), (10.0, 34.0), 4.0, 1.6), IRON, 'ray', base=-2, sep=True)
    p.part(c.taper((36.0, 27.0), (40.0, 20.0), (39.0, 13.0), 3.6, 1.4), IRON, 'ray', base=-2, sep=True)
    for (x, y) in ((24.0, 41.0), (32.0, 32.0), (40.0, 23.0)):
        mark = c.poly([(x - 2.4, y + 2.4), (x + 2.4, y + 2.4), (x + 3.2, y - 1.4), (x, y - 3.4), (x - 3.2, y - 1.4)]) & root
        p.decal(mark, GOLD, 0)
        p.decal(c.box(x - 0.8, y - 1.6, x + 0.8, y + 1.4) & mark, GOLD, -2)
    cord_hd(p, [(14.0, 48.0), (10.0, 52.0), (9.0, 57.0)], HEMP, 2.2)
    p.sparkle(47.0, 14.0, 1)
    glow_hd(p, 'spirit', '#E5B84C')


def entry_token_hd(p):
    """An entry token: a bronze tablet on a red cord, the gate character stamped into its face."""
    c = p.c
    m, inner = token_hd(p, BRONZE, 'tablet', cord=RED, w=12.0, lv=0)
    g = (c.box(24.0, 23.0, 40.0, 25.4) | c.box(30.8, 25.0, 33.2, 42.0) | c.box(22.0, 31.5, 42.0, 33.9) | c.box(25.0, 40.0, 39.0, 42.4)) & inner
    p.decal(g, BRONZE, -3)
    p.decal(shift(g, -1, -1) & ~g & inner, BRONZE, 2)


def mudwater_key_hd(p):
    """The Mudwater key: a heavy bronze key on the diagonal, its bow a ring at the lower left, two bits at the tip,
    river mud still clotted on it."""
    c = p.c
    fr = Frame((12.0, 52.0), 45.0)
    bow = c.ring(13.0, 51.0, 8.0, 3.6)
    p.part(bow, BRONZE, 'ray', base=0, sep=True, tex='metal')
    shaft = fr.prof(c, [(6.0, 2.8), (46.0, 2.8)])
    p.cylinder(fr, shaft, 2.8, BRONZE, sep=True, tex='metal')
    fitting_hd(p, fr, dict(guard=BRONZE), 8.0, 12.0, 3.6, 0.6)
    for (t0, t1, d) in ((36.0, 40.0, 8.0), (42.0, 46.0, 6.5)):
        bit = c.poly([fr.P(t0, 2.0), fr.P(t1, 2.0), fr.P(t1, d), fr.P(t0, d)])
        p.part(bit, BRONZE, 'ray', base=0, sep=True, tex='metal')
    for (x, y, r) in ((11.0, 46.0, 3.2), (31.0, 34.0, 2.8), (44.0, 26.0, 2.2), (18.0, 56.0, 2.0)):
        p.part(c.ellipse(x, y, r, r * 0.7) & c.a, MUD, 'ray_soft', base=0, sep=True, rim=False)
        p.decal(c.circle(x - r * 0.4, y - r * 0.4, 0.8) & c.a, MUD, 2)
    p.sparkle(*fr.P(30.0, -3.0), 1)


def siege_medal_hd(p):
    """A siege medal: a gold disc on a red ribbon, the two sects' crossed spears struck in bronze on its face."""
    c = p.c
    rib = c.poly([(20.0, 5.0), (30.0, 5.0), (34.0, 26.0), (26.0, 29.0)]) | c.poly([(34.0, 5.0), (44.0, 5.0), (38.0, 29.0), (30.0, 26.0)])
    p.part(rib, RED, 'ray', base=0, sep=True, rim=False, tex='cloth', axis=100)
    p.decal(c.box(30.5, 5.0, 33.5, 25.0) & rib, GOLD, 0)
    p.part(c.circle(32.0, 27.0, 3.4), GOLD, 'sphere', base=0, sep=True, tex='metal')
    med = c.circle(32.0, 43.0, 15.5)
    p.part(med, GOLD, 'sphere', base=0, sep=True, cx=30.0, cy=41.0, rx=17.0, ry=17.0, tex='metal')
    p.decal(c.ring(32.0, 43.0, 12.6, 1.4) & med, GOLD, -2)
    p.decal(c.ring(32.0, 43.0, 15.5, 1.2) & med & (c.X / p.s + c.Y / p.s < 72), GOLD, 3)
    for (a, b) in (((24.0, 51.0), (40.0, 35.0)), ((24.0, 35.0), (40.0, 51.0))):
        p.line([a, b], BRONZE, -2, 2.0)
        p.decal(c.poly([(b[0] - 1.5, b[1] - 1.5), (b[0] + 2.0, b[1] - 3.5), (b[0] + 3.5, b[1] + 0.5)]) & med, BRONZE, -2)
    p.sparkle(24.0, 33.0, 1)


def book_hd(p, cover, x0=12.0, y0=8.0, x1=48.0, y1=54.0, spine=6.0, stitch=None, pages=None, block=True):
    """A closed book: the page block set back at the right and foot, the cover over it with its spine and
    stitching. Returns the cover."""
    c = p.c
    pages = pages or PAPER
    if block:
        blk = c.box(x0 + 3.0, y0 + 3.0, x1 + 3.0, y1 + 3.0)
        p.part(blk, pages, 'flat', base=-1, sep=True, rim=False)
        for y in np.arange(y0 + 5.0, y1 + 2.0, 2.2):
            p.decal(c.box(x1 + 0.5, y, x1 + 3.0, y + 1.0) & blk, pages, -3)
        for x in np.arange(x0 + 5.0, x1 + 1.0, 2.2):
            p.decal(c.box(x, y1 + 0.5, x + 1.0, y1 + 3.0) & blk, pages, -3)
    cv = c.rrect(x0, y0, x1, y1, 1.5)
    p.part(cv, cover, 'bevel', base=0, sep=True, hw=2, sw=2, tex=TEX.get(cover.kind), axis=90)
    sp = c.box(x0, y0, x0 + spine, y1) & cv
    p.decal(sp, cover, -2)
    p.decal(c.box(x0 + spine - 0.5, y0 + 1.0, x0 + spine + 0.6, y1 - 1.0) & cv, cover, -3)
    if stitch is not None:
        for y in np.arange(y0 + 5.0, y1 - 3.0, 9.0):
            p.decal(c.box(x0 + 1.0, y, x0 + spine - 0.5, y + 1.8) & cv, stitch, 0)
    return cv


def smuggler_ledger_hd(p):
    """Elder Gu's smuggler ledger: a dark leather book stitched with hemp, a paper label on its cover with a coin
    struck on it and a line of the tally beneath."""
    c = p.c
    cv = book_hd(p, LEDGER_HD, x0=10.0, y0=7.0, x1=48.0, y1=54.0, spine=7.0, stitch=HEMP)
    lab = c.rrect(24.0, 15.0, 42.0, 40.0, 1.4)
    p.part(lab, PAPER, 'bevel', base=0, sep=True, hw=1, sw=1, tex='paper', rim=False)
    coin = c.circle(33.0, 25.0, 5.6)
    p.decal(coin & lab, GOLD, 0)
    p.decal(c.box(32.0, 23.0, 34.0, 27.0) & lab, GOLD, -3)
    p.decal(c.circle(31.0, 23.0, 1.4) & lab, GOLD, 3)
    for y in (33.0, 36.0):
        p.decal(c.box(27.0, y, 39.0, y + 1.2) & lab, INK, 1)


# ----------------------------------------------------------------------------- goods
def old_net_hd(p):
    """An old fishing net: a heap of hemp mesh with a hole torn in it, cork floats along its edge and one glass
    float caught in the folds."""
    c = p.c
    X, Y = XY(p)
    blob = c.ellipse(32.0, 38.0, 25.0, 18.0) | c.ellipse(24.0, 24.0, 14.0, 10.0)
    hole = c.ellipse(40.0, 36.0, 6.5, 5.0)
    net = blob & ~hole
    p.part(net, HEMP, 'ray_soft', base=-2, sep=False, rim=False)
    xi, yi = np.floor(X).astype(int), np.floor(Y).astype(int)
    grid = ((xi + yi) % 6 == 0) | ((xi - yi) % 6 == 0)
    p.decal(erode4(net) & grid, HEMP, 1)
    p.decal(erode4(net) & ((xi + yi) % 6 == 0) & ((xi - yi) % 6 == 0), HEMP, 2)
    p.decal(net & dilate4(hole), HEMP, -3)
    for (x, y) in ((44.0, 32.0), (37.0, 40.0), (45.0, 41.0)):
        p.decal(lmask(p, [(x, y), (x + 2.0, y - 2.0)]) & net, HEMP, 2)
    for (x, y) in ((13.0, 46.0), (32.0, 56.0), (51.0, 44.0)):
        p.part(c.ellipse(x, y, 4.6, 3.4), M('wood'), 'sphere', base=0, sep=True, tex='wood', axis=0)
    g = c.circle(48.0, 18.0, 5.2)
    p.part(g, M('mist', 'glass'), 'sphere', base=1, sep=True, tex='glass', spec=(46.0, 16.0))


def river_mud_hd(p):
    """River mud: a grey heap slumped on the bank, wet and glossy on its lit side, a puddle at its foot."""
    c = p.c
    pile = c.ellipse(32.0, 46.0, 26.0, 12.0) | c.ellipse(28.0, 34.0, 16.0, 12.0) | c.ellipse(38.0, 28.0, 10.0, 9.0)
    p.part(pile, MUD, 'sphere', base=0, sep=False, cx=28.0, cy=30.0, rx=28.0, ry=24.0, tex='clay', rim=False)
    for pts in (((12.0, 46.0), (24.0, 42.0), (36.0, 48.0)), ((24.0, 32.0), (34.0, 30.0), (44.0, 34.0))):
        p.decal(c.polyline(pts, 1.4) & erode4(pile), MUD, -2)
    p.decal(c.ellipse(34.0, 24.0, 4.8, 2.4) & pile, MUD, 2)
    p.decal(c.ellipse(18.0, 36.0, 3.2, 1.8) & pile, MUD, 2)
    puddle = c.ellipse(46.0, 56.0, 12.0, 3.2) & ~pile
    p.part(puddle, QI, 'flat', base=-2, sep=True, rim=False)
    p.decal(c.box(42.0, 55.0, 48.0, 56.2) & puddle, QI, 1)


def aunt_pings_ladle_hd(p):
    """Aunt Ping's ladle: a wooden soup ladle on the diagonal, its deep bowl at the lower right, a hanging loop at
    the end of the handle."""
    c = p.c
    fr = Frame((44.0, 46.0), 135.0)
    handle = fr.prof(c, [(0.0, 3.0), (42.0, 2.6)])
    p.cylinder(fr, handle, 2.8, WOOD, sep=True, tex='wood', axis=135.0)
    lx, ly = fr.P(43.0, 0.0)
    p.part(c.ring(lx, ly, 4.0, 2.2), WOOD, 'ray', base=-1, sep=True)
    bowl = c.ellipse(43.0, 45.0, 15.0, 11.0)
    p.part(bowl, WOOD, 'sphere', base=0, sep=True, cx=39.0, cy=41.0, rx=17.0, ry=13.0, tex='wood', axis=0)
    well = c.ellipse(43.0, 42.0, 11.0, 5.4)
    p.part(well, WOOD, 'flat', base=-3, sep=True, rim=False)
    p.decal(c.ellipse(41.0, 42.5, 8.0, 3.2) & well, M('broth'), 0)
    p.decal(c.ellipse(38.0, 41.0, 3.0, 1.2) & well, M('broth'), 3)


def tinkerers_gear_hd(p):
    """The tinkerer's gear: a brass gear with ten teeth round a spoked hub, a bent iron pin through it."""
    c = p.c
    body = c.circle(32.0, 32.0, 19.0)
    for k in range(10):
        a = k * math.pi / 5 + 0.3
        body |= c.ellipse(32.0 + 22.0 * math.cos(a), 32.0 + 22.0 * math.sin(a), 4.2, 4.2)
    hub = c.circle(32.0, 32.0, 6.0)
    p.part(body & ~hub, BRONZE, 'sphere', base=0, sep=True, cx=27.0, cy=26.0, rx=26.0, ry=26.0, tex='metal')
    p.decal(c.ring(32.0, 32.0, 12.0, 1.6) & body, BRONZE, -2)
    for k in range(4):
        a = k * math.pi / 2 + 0.8
        p.decal(c.ellipse(32.0 + 15.0 * math.cos(a), 32.0 + 15.0 * math.sin(a), 2.6, 2.6) & body, BRONZE, -3)
    p.decal(dilate4(hub) & ~hub & body, BRONZE, -3)
    pin = c.polyline([(18.0, 50.0), (30.0, 34.0), (34.0, 30.0), (46.0, 14.0)], 2.6)
    p.part(pin, IRON, 'ray_soft', base=0, sep=True, tex='metal')
    p.part(c.circle(46.0, 14.0, 2.4), IRON, 'sphere', base=0, sep=True)
    p.sparkle(22.0, 20.0, 1)


def bag_hd(p, cloth, tie, trim=None, tex='cloth'):
    """A closed drawstring pouch: the plump bag with its gathers, the mouth pulled shut, the tie round the neck with
    its knot and a loose end, a bead in the trim metal on the knot. Returns the bag."""
    c = p.c
    body = c.ellipse(32.0, 41.0, 21.0, 17.5) | c.poly([(18.0, 30.0), (46.0, 30.0), (42.0, 19.0), (22.0, 19.0)])
    p.part(body, cloth, 'sphere', base=0, sep=False, cx=26.0, cy=34.0, rx=25.0, ry=23.0, tex=tex, axis=80)
    for pts in (((40.0, 21.0), (44.0, 31.0)), ((24.0, 21.0), (20.0, 31.0)), ((32.0, 21.0), (32.0, 28.0))):
        p.decal(lmask(p, pts) & body, cloth, -2)
    mouth = c.ellipse(32.0, 18.5, 11.0, 4.4)
    p.part(mouth, cloth, 'ray', base=-1, sep=True, rim=False)
    p.decal(c.ellipse(32.0, 18.5, 6.0, 2.0) & mouth, cloth, -3)
    band = c.box(19.0, 23.0, 45.0, 26.4) & dilate4(body)
    p.part(band, tie, 'ray_soft', base=0, sep=True, rim=False, tex=TEX.get(tie.kind) if tie.kind not in ('silk', 'cloth') else None)
    knot_hd(p, 43.0, 24.5, 2.6, tie)
    p.part(c.taper((44.0, 26.0), (50.0, 29.0), (51.0, 36.0), 2.4, 1.2), tie, 'flat', base=0, sep=True, rim=False)
    if trim is not None:
        cap_hd(p, 43.0, 24.5, 2.2, trim)
    return body


def sealed_storage_pouch_hd(p):
    """A sealed storage pouch: a hemp drawstring pouch, a red seal slip pasted down across its knot with two marks."""
    c = p.c
    body = bag_hd(p, HEMP, M('wood'), tex='cloth')
    slip = c.box(29.0, 17.0, 36.0, 44.0)
    p.part(slip, SEAL, 'flat', base=0, sep=True, rim=False)
    p.decal(c.box(30.0, 17.0, 31.0, 44.0) & slip, SEAL, 1)
    for y in (24.0, 34.0):
        p.decal((c.box(31.0, y, 34.0, y + 1.6) | c.box(32.0, y + 2.6, 33.0, y + 5.0) | c.box(31.0, y + 5.6, 34.0, y + 7.0)) & slip, PAPER, 1)


def cloth_hd(p):
    """A bolt of cloth: three folded lengths stacked (hemp, indigo, jade), each with its fold line and lit edge, a
    straw tie round the stack."""
    c = p.c
    for k, (mat, y) in enumerate(((HEMP, 40.0), (INDIGO, 27.0), (JADE, 14.0))):
        slab = c.rrect(10.0 + k * 2.0, y, 54.0 - k * 2.0, y + 14.0, 3.0)
        p.part(slab, M('jade', 'cloth') if mat is JADE else mat, 'bevel', base=0, sep=True, hw=2, sw=2, tex='cloth', axis=0, rim=False)
        p.decal(c.box(12.0 + k * 2.0, y + 6.5, 52.0 - k * 2.0, y + 7.8) & slab, mat, -2)
        p.decal(c.box(14.0 + k * 2.0, y + 2.0, 26.0 + k * 2.0, y + 3.2) & slab, mat, 2)
    tie = c.box(29.0, 12.0, 35.0, 55.0) & c.a
    p.part(tie, STRAW, 'ray_soft', base=0, sep=True, rim=False)
    p.decal(c.box(29.0, 30.0, 35.0, 33.0) & tie, STRAW, -2)


def arrow_hd(p, a, b, fletch, head=None, shaft=None):
    """One arrow from its nock at `a` to its point at `b`: the shaft, an iron head, two fletching vanes."""
    c = p.c
    head, shaft = head or IRON, shaft or WOOD
    fr = Frame(a, math.degrees(math.atan2(a[1] - b[1], b[0] - a[0])))
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    s = fr.prof(c, [(0.0, 1.5), (L - 6.0, 1.5)])
    p.cylinder(fr, s, 1.5, shaft, sep=True)
    p.part(fr.prof(c, [(L - 8.0, 1.2), (L - 5.0, 3.4), (L, 0.0)]), head, 'ray', base=0, sep=True, tex='metal')
    for sgn in (-1, 1):
        vane = c.poly([fr.P(1.0, 0.0), fr.P(2.0, sgn * 4.6), fr.P(11.0, sgn * 3.6), fr.P(12.0, 0.0)])
        p.part(vane, fletch, 'ray_soft', base=0, sep=True, rim=False)


def arrows_hd(p):
    """A bundle of arrows: three on the diagonal, iron heads up, red and white fletching, bound with a straw band."""
    c = p.c
    arrow_hd(p, (8.0, 48.0), (46.0, 10.0), RED)
    arrow_hd(p, (16.0, 56.0), (56.0, 16.0), PAPER)
    arrow_hd(p, (10.0, 58.0), (44.0, 24.0), RED)
    band = c.polyline([(22.0, 38.0), (30.0, 46.0)], 5.0) & dilate4(c.a)
    p.part(band, STRAW, 'ray_soft', base=0, sep=True, rim=False)
    p.line([(24.0, 42.0), (28.0, 41.0)], STRAW, -2, 1.0)


def bow_parts_hd(p):
    """Bow parts: a cracked bow limb with its bone nock, and a spool of bowstring wound on a peg beside it."""
    c = p.c
    limb = c.taper((10.0, 56.0), (14.0, 18.0), (46.0, 8.0), 7.0, 3.6)
    p.part(limb, WOOD, 'ray', base=0, sep=True, tex='wood', axis=75.0)
    p.line([(14.0, 40.0), (18.0, 34.0), (15.0, 30.0)], WOOD, -3, 1.4)
    p.decal(lmask(p, [(15.0, 40.0), (19.0, 34.0)]) & limb, WOOD, 2)
    p.part(c.circle(46.0, 8.0, 3.0), BONE, 'sphere', base=0, sep=True, tex='glass')
    p.part(c.polyline([(11.0, 44.0), (13.0, 54.0)], 8.0) & limb, LEATHER, 'ray_soft', base=0, sep=True, rim=False)
    peg = c.box(40.0, 30.0, 45.0, 58.0)
    p.part(peg, DARKWOOD, 'hgrad', base=0, sep=True, tex='wood', axis=90)
    spool = c.ellipse(42.5, 44.0, 12.0, 9.0)
    p.part(spool, PAPER, 'sphere', base=0, sep=True, cx=39.0, cy=40.0, rx=14.0, ry=11.0)
    for k in range(5):
        p.decal(c.ring(42.5, 44.0, 11.0 - k * 2.2, 0.9, 8.2 - k * 1.6) & spool, PAPER, -2 if k % 2 else 1)
    p.part(c.polyline(S.curve_pts((52.0, 40.0), (57.0, 48.0), (54.0, 57.0), 10), 1.4), PAPER, 'flat', base=1, sep=True, rim=False)


def prayer_beads_hd(p):
    """Prayer beads: a loop of dark sandalwood beads worn smooth, a jade guru bead at its foot, a red tassel."""
    c = p.c
    n = 16
    tassel_hd(p, dict(tassel=RED, bead=JADE, lv=2), 32.0, 54.0, 1.2, knot=False)
    for k in range(n):
        a = -math.pi / 2 + k * 2 * math.pi / n
        x, y = 32.0 + math.cos(a) * 20.0, 30.0 + math.sin(a) * 19.0
        if k == n // 2:
            continue
        p.part(c.circle(x, y, 4.2), DARKWOOD, 'sphere', base=0, sep=True, spec=(x - 1.4, y - 1.4))
    p.part(c.circle(32.0, 49.5, 5.4), JADE, 'sphere', base=0, sep=True, tex='jade', spec=(30.0, 47.5))
    p.part(c.ellipse(32.0, 55.0, 2.0, 1.4), GOLD, 'sphere', base=0, sep=True)


def talisman_paper_hd(p):
    """Talisman paper: three blank yellow sheets fanned out, the top one ruled with its red border."""
    c = p.c
    for k, (x, y, base) in enumerate(((30.0, 12.0, -2), (22.0, 9.0, -1), (12.0, 6.0, 0))):
        m = c.poly([(x + 10.0, y), (x + 24.0, y + 4.0), (x + 14.0, y + 50.0), (x, y + 46.0)])
        p.part(m, TALISMAN, 'bevel', base=base, sep=True, hw=1, sw=1, tex='paper', rim=False)
    top = c.poly([(22.0, 6.0), (36.0, 10.0), (26.0, 56.0), (12.0, 52.0)])
    border = top & ~c.poly([(24.5, 10.0), (32.5, 12.4), (23.4, 52.0), (15.4, 49.6)])
    p.decal(border & erode4(top) & ~(top & ~erode4(erode4(top))), SEAL, 0)


def ink_hd(p):
    """Ink: an ink stone with its well of black ink, an ink stick with gold characters leaning against it."""
    c = p.c
    slab = c.rrect(6.0, 34.0, 50.0, 56.0, 3.0)
    p.part(slab | shift(slab, 0, -2), STONE, 'flat', base=-2, sep=False)
    p.part(slab, STONE, 'bevel', base=0, sep=True, hw=2, sw=2)
    well = c.rrect(11.0, 38.0, 44.0, 51.0, 3.0)
    p.part(well, INK, 'flat', base=-2, sep=True, rim=False)
    p.decal(c.box(14.0, 40.0, 24.0, 41.2) & well, INK, 2)
    p.decal(c.ellipse(30.0, 46.0, 8.0, 2.4) & well, INK, 0)
    fr = Frame((40.0, 50.0), 72.0)
    stick = fr.prof(c, [(0.0, 5.4), (42.0, 5.4)])
    p.cylinder(fr, stick, 5.4, INK, sep=True)
    for t0 in (10.0, 20.0, 30.0):
        p.decal(fr.prof(c, [(t0 - 2.0, 2.6), (t0 + 2.0, 2.6)]) & stick, GOLD, 0)
        p.decal(fr.prof(c, [(t0 - 0.5, 1.2), (t0 + 0.5, 1.2)]) & stick, INK, 0)
    p.decal(fr.prof(c, [(0.0, 5.4), (3.0, 5.4)]) & stick, INK, -3)


def lantern_wick_hd(p):
    """A lantern wick: a spool of braided spirit-silk wick between two wooden ends, the loose end running up to a
    small flame."""
    c = p.c
    fr = Frame((12.0, 34.0), 0.0)
    spool = fr.prof(c, [(0.0, 11.0), (34.0, 11.0)])
    p.cylinder(fr, spool, 11.0, HEMP, sep=True, tex='cloth', axis=0)
    X, Y = XY(p)
    for x in np.arange(14.0, 46.0, 3.0):
        p.decal(lmask(p, [(x, 24.0), (x + 1.5, 44.0)]) & spool, HEMP, -2)
        p.decal(lmask(p, [(x + 1.5, 24.0), (x + 3.0, 44.0)]) & spool, HEMP, 1)
    for x in (12.0, 46.0):
        p.part(c.ellipse(x, 34.0, 4.0, 13.0), WOOD, 'ray', base=0, sep=True, tex='wood', axis=90)
    p.decal(c.ellipse(46.0, 34.0, 1.6, 5.0), WOOD, -3)
    p.part(c.polyline(S.curve_pts((46.0, 23.0), (54.0, 20.0), (54.0, 12.0), 10), 2.4) & ~c.a, HEMP, 'flat', base=0, sep=True, rim=False)
    fl = S.flame(c, 54.0, 11.0, 6.5, 10.0, 0.3)
    p.part(fl, FIRE, 'vgrad', base=0, sep=True, rim=False, bands=((0.3, 1), (0.7, 0), (9, -1)))
    p.decal(S.flame(c, 54.0, 10.5, 2.8, 5.0, 0.2) & fl, FIRE, 3)
    p.part(c.box(53.0, 10.0, 55.0, 12.5), INK, 'flat', base=0, sep=True, rim=False)
    p.glow('#FFB45A', 0.4)


def rice_hd(p):
    """Rice: a hemp sack rolled open at the mouth on the grain, the mill's red stamp on it, a spill of grains at
    its foot."""
    c = p.c
    sack = c.rrect(12.0, 20.0, 50.0, 58.0, 5.0) | c.poly([(16.0, 22.0), (20.0, 10.0), (42.0, 10.0), (46.0, 22.0)])
    p.part(sack, HEMP, 'ray', base=0, sep=False, tex='cloth', axis=90)
    X, Y = XY(p)
    xi, yi = np.floor(X).astype(int), np.floor(Y).astype(int)
    p.decal(erode4(sack) & (Y > 24) & (yi % 5 == 0) & ((xi + yi) % 2 == 0), HEMP, -1)
    p.part(c.box(15.0, 19.0, 47.0, 23.0), HEMP, 'vgrad', base=-1, sep=True, rim=False)
    grains = c.ellipse(31.0, 12.5, 11.0, 4.4)
    p.part(grains, RICE, 'ray', base=0, sep=True, rim=False)
    for (x, y) in ((26.0, 12.0), (34.0, 10.5), (30.0, 14.0), (38.0, 13.0), (23.0, 14.0)):
        p.decal(c.ellipse(x, y, 1.4, 0.8) & grains, RICE, 3)
    stamp_hd(p, 39.0, 46.0, 5.0, sack)
    heap = c.ellipse(53.0, 56.0, 8.0, 3.6) & ~sack
    p.part(heap, RICE, 'ray', base=0, sep=True, rim=False)
    for (x, y) in ((50.0, 55.0), (55.0, 54.0), (58.0, 56.0)):
        p.decal(c.ellipse(x, y, 1.4, 0.8) & heap, RICE, 3)


def kite_hd(p):
    """Little Dou's kite: a red paper diamond on crossed spars painted with a fish face, its tail of paper bows
    trailing from the foot."""
    c = p.c
    body = c.diamond(28.0, 26.0, 20.0, 22.0)
    p.part(body, KITE_HD, 'ray', base=0, sep=False, tex='paper', rim=False)
    p.decal(c.diamond(28.0, 26.0, 16.0, 17.6) & ~c.diamond(28.0, 26.0, 14.4, 15.8), KITE_HD, 2)
    p.decal(lmask(p, [(28.0, 5.0), (28.0, 47.0)]) & body, WOOD, -1)
    p.decal(lmask(p, [(9.0, 26.0), (47.0, 26.0)]) & body, WOOD, -1)
    for x in (20.0, 36.0):
        p.decal(c.circle(x, 21.0, 4.0) & body, PAPER, 1)
        p.decal(c.circle(x + 0.6, 21.4, 1.8) & body, INK, -1)
        p.decal(c.circle(x - 0.4, 20.4, 0.7) & body, WHITE, 0)
    p.decal(c.polyline([(22.0, 34.0), (28.0, 37.0), (34.0, 34.0)], 1.8) & body, INK, 0)
    tail = c.polyline(S.curve_pts((28.0, 48.0), (36.0, 58.0), (56.0, 54.0), 12), 1.4)
    p.part(tail & ~body, PAPER, 'flat', base=1, sep=True, rim=False)
    for (x, y) in ((36.0, 54.0), (48.0, 56.0)):
        bow = c.poly([(x - 4.0, y - 3.0), (x + 4.0, y + 3.0), (x + 4.0, y - 3.0), (x - 4.0, y + 3.0)])
        p.part(bow, JADE, 'flat', base=0, sep=True, rim=False)
        p.decal(c.circle(x, y, 1.0), JADE, 2)


def bowl_hd(p, mat, cx=32.0, top=44.0, rx=21.0, depth=10.0, ash=None):
    """A low incense bowl: its wall from the lip down to a foot, the lip's ellipse, a bed of ash in it."""
    c = p.c
    wall = c.ellipse(cx, top, rx, depth) & c.box(0, top, 64, 64)
    p.part(wall, mat, 'ray', base=0, sep=True, tex=TEX.get(mat.kind))
    lip = c.ellipse(cx, top, rx, 4.4)
    p.part(lip, mat, 'ray', base=1, sep=True, tex=TEX.get(mat.kind))
    p.part(c.ellipse(cx, top, rx - 3.0, 3.0), ash or M('warmstone'), 'flat', base=0, sep=True, rim=False)
    p.part(c.box(cx - rx * 0.55, top + depth - 1.0, cx + rx * 0.55, top + depth + 2.0), mat, 'flat', base=-2, sep=True)
    return wall | lip


def sticks_hd(p, xs, top, foot, mat, lit=True):
    """Incense sticks standing in a bowl, each with an ember tip."""
    c = p.c
    for k, (x, y0) in enumerate(zip(xs, top)):
        p.part(c.box(x - 1.0, y0, x + 1.0, foot), mat, 'flat', base=0 if k % 2 == 0 else -1, sep=True, rim=False)
        if lit:
            p.decal(c.box(x - 1.0, y0, x + 1.0, y0 + 1.8), FIRE, 2)


def smoke_hd(p, x, y, mat, h=14.0, lean=-1.0, w=2.0):
    """A curl of smoke rising from (x, y)."""
    c = p.c
    pts = S.curve_pts((x, y), (x + 5.0 * lean, y - h * 0.5), (x + 1.5 * lean, y - h), 10)
    m = c.polyline(pts, w) & ~c.a
    p.part(m, mat, 'flat', base=1, sep=False, rim=False)
    return m


def calm_incense_hd(p):
    """Calm incense: three red sticks lit in a bronze bowl, a curl of mist off the tallest."""
    bowl_hd(p, BRONZE)
    sticks_hd(p, (26.0, 32.0, 38.0), (24.0, 18.0, 24.0), 44.0, RED)
    smoke_hd(p, 32.0, 16.0, MIST, h=10.0)
    smoke_hd(p, 26.0, 22.0, MIST, h=8.0, lean=-0.8, w=1.6)


def myriad_year_calm_incense_hd(p):
    """Myriad Year Calm Incense: a gold censer with a jade ring round its belly and a pierced lid, violet smoke
    breathing out of it, glints in the air (Heaven)."""
    c = p.c
    body = c.ellipse(32.0, 44.0, 20.0, 12.0)
    p.part(body, GOLD, 'sphere', base=0, sep=True, cx=28.0, cy=39.0, rx=23.0, ry=15.0, tex='metal')
    for x in (13.0, 51.0):
        p.part(c.box(x - 2.0, 50.0, x + 2.0, 58.0), GOLD, 'ray', base=-1, sep=True, tex='metal')
    p.part(c.ring(32.0, 44.0, 14.0, 2.4, 7.0) & erode4(body), JADE, 'flat', base=0, sep=True, rim=False, tex='jade')
    lid = c.ellipse(32.0, 33.0, 15.0, 5.0) | c.poly([(24.0, 32.0), (32.0, 22.0), (40.0, 32.0)])
    p.part(lid, GOLD, 'ray', base=1, sep=True, tex='metal')
    for (x, y) in ((28.0, 30.0), (32.0, 27.0), (36.0, 30.0)):
        p.decal(c.circle(x, y, 1.2) & lid, GOLD, -3)
    p.part(c.circle(32.0, 21.0, 2.2), JADE, 'sphere', base=0, sep=True)
    smoke_hd(p, 26.0, 29.0, VIOLET, h=12.0, lean=-1.2, w=2.4)
    smoke_hd(p, 38.0, 28.0, VIOLET, h=10.0, lean=1.0, w=2.0)
    p.sparkle(52.0, 14.0, 2)
    p.sparkle(10.0, 24.0, 1)


def restoration_ink_hd(p):
    """Restoration ink: a porcelain jar lidded in jade, a swirl of the jade-green ink on its face, a bamboo brush
    with a jade-dipped tip leaning against it."""
    c = p.c
    jar = c.ellipse(28.0, 42.0, 17.0, 15.0) | c.box(19.0, 24.0, 37.0, 30.0)
    p.part(jar, PORCELAIN, 'sphere', base=0, sep=True, cx=24.0, cy=36.0, rx=20.0, ry=19.0, tex='glass')
    p.part(c.ellipse(28.0, 24.0, 11.0, 3.6), JADE, 'ray', base=0, sep=True, tex='jade')
    p.part(c.circle(28.0, 20.5, 2.6), JADE, 'sphere', base=0, sep=True)
    sw = c.circle(28.0, 44.0, 7.0) & jar
    p.decal(sw, JADE, 0)
    p.decal(c.arc(28.0, 44.0, 4.4, 1.8, 30, 250) & jar, JADE, 2)
    p.decal(c.circle(28.0, 44.0, 1.6) & jar, JADE, 3)
    fr = Frame((36.0, 32.0), 58.0)
    shaft = fr.prof(c, [(0.0, 2.2), (28.0, 2.2)])
    p.cylinder(fr, shaft, 2.2, BAMBOO, sep=True, tex='wood', axis=58.0)
    p.decal(fr.prof(c, [(13.5, 2.3), (14.5, 2.3)]) & shaft, BAMBOO, -2)
    tuft = c.poly([fr.P(0.0, -2.4), fr.P(0.0, 2.4), fr.P(-9.0, 0.0)])
    p.part(tuft, BONE, 'ray', base=0, sep=True)
    p.decal(c.poly([fr.P(-4.0, -1.4), fr.P(-4.0, 1.4), fr.P(-9.0, 0.0)]) & tuft, JADE, 0)


def fish_bait_hd(p):
    """Fish bait: a clay pot of worms, one hanging over the rim, a hook on its line lying against it."""
    c = p.c
    pot = c.ellipse(30.0, 42.0, 19.0, 15.0) | c.box(16.0, 28.0, 44.0, 34.0)
    p.part(pot, CLAY, 'sphere', base=0, sep=True, cx=26.0, cy=36.0, rx=22.0, ry=20.0, tex='clay')
    p.part(c.box(14.0, 27.0, 46.0, 31.0), CLAY, 'vgrad', base=1, sep=True)
    mouth = c.ellipse(30.0, 28.5, 13.0, 3.6)
    p.part(mouth, MUD, 'flat', base=-2, sep=True, rim=False)
    worm = M('pink', 'porcelain')
    for (a, b, d, w0, w1) in (((20.0, 28.0), (26.0, 22.0), (34.0, 26.0), 3.4, 2.6), ((38.0, 27.0), (46.0, 24.0), (50.0, 34.0), 3.2, 2.2),
                              ((14.0, 33.0), (10.0, 40.0), (14.0, 48.0), 3.0, 2.0)):
        m = c.taper(a, b, d, w0, w1)
        p.part(m, worm, 'ray_soft', base=0, sep=True, rim=False)
        for f in (0.3, 0.6, 0.85):
            x, y = S.curve_pts(a, b, d, 20)[int(f * 20)]
            p.decal(c.circle(x, y, 1.6) & m & ~erode4(erode4(m)), worm, -2)
    p.part(c.polyline(S.curve_pts((48.0, 10.0), (54.0, 20.0), (50.0, 30.0), 10), 1.2), PAPER, 'flat', base=1, sep=True, rim=False)
    hook = c.arc(48.0, 33.0, 4.0, 1.6, 180, 360) | c.box(51.0, 27.0, 52.6, 33.0)
    p.part(hook, IRON, 'flat', base=0, sep=True)


def blank_plate_hd(p):
    """A blank jade plate for a portable array: a thick slab with a chamfered edge, a ring cut for the array to come
    and four gold studs at the corners."""
    c = p.c
    m = c.rrect(8.0, 10.0, 56.0, 56.0, 5.0)
    p.part(shift(m, 0, -3) | m, JADE, 'flat', base=-2, sep=False)
    p.part(m, JADE, 'ray', base=0, sep=True, tex='jade')
    inner = c.rrect(12.0, 14.0, 52.0, 52.0, 4.0)
    p.decal(inner & ~erode4(inner), JADE, -2)
    p.decal(shift(inner & ~erode4(inner), -1, -1) & ~inner & m, JADE, 2)
    p.decal(c.ring(32.0, 33.0, 12.0, 1.8) & m, JADE, -2)
    p.decal(c.ring(32.0, 33.0, 6.0, 1.6) & m, JADE, 2)
    for (x, y) in ((16.0, 18.0), (48.0, 18.0), (16.0, 48.0), (48.0, 48.0)):
        p.part(c.circle(x, y, 2.0), GOLD, 'sphere', base=0, sep=True, tex='metal')


MISC_HD_A = [
    ('manual_page', manual_page_hd), ('lu_journal_page', lu_journal_page_hd), ('riverbreath_scroll', riverbreath_scroll_hd), ('recipe_scroll', recipe_scroll_hd),
    ('river_token', river_token_hd), ('jade_token', jade_token_hd), ('cloud_token', cloud_token_hd), ('alliance_token', alliance_token_hd),
    ('ironroot_token', ironroot_token_hd), ('entry_token', entry_token_hd), ('mudwater_key', mudwater_key_hd), ('siege_medal', siege_medal_hd),
    ('smuggler_ledger', smuggler_ledger_hd), ('old_net', old_net_hd), ('river_mud', river_mud_hd), ('aunt_pings_ladle', aunt_pings_ladle_hd),
    ('tinkerers_gear', tinkerers_gear_hd), ('sealed_storage_pouch', sealed_storage_pouch_hd), ('cloth', cloth_hd), ('arrows', arrows_hd),
    ('bow_parts', bow_parts_hd), ('prayer_beads', prayer_beads_hd), ('talisman_paper', talisman_paper_hd), ('ink', ink_hd),
    ('lantern_wick', lantern_wick_hd), ('rice', rice_hd), ('kite', kite_hd), ('calm_incense', calm_incense_hd),
    ('myriad_year_calm_incense', myriad_year_calm_incense_hd), ('restoration_ink', restoration_ink_hd), ('fish_bait', fish_bait_hd),
    ('blank_plate', blank_plate_hd),
]


# ----------------------------------------------------------------------------- eggs, beast bags, the rack
def egg_hd(p, shell, spots=None, crack=True, wisps=False, nest=True, glow=None):
    """A spirit egg, pointed at the top and full at the bottom, in a nest of straw: the shell with its spots and a
    crack where something stirs, mist drifting off it when `wisps`."""
    c = p.c
    X, Y = XY(p)
    cx, cy, ry = 32.0, 32.0, 23.0
    t = np.clip((cy - Y) / ry, 0.0, 1.0)
    rx = 17.0 * (1.0 - 0.24 * t)
    egg = ((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 <= 1.0
    if nest:
        bed = (c.ellipse(32.0, 55.0, 23.0, 6.0) | c.ellipse(32.0, 57.0, 25.0, 4.0)) & c.box(0, 0, 64, 60.5) & ~egg
        p.part(bed, STRAW, 'ray', base=0, sep=False, rim=False)
        for (a, b) in (((10.0, 54.0), (20.0, 50.0)), ((44.0, 50.0), (55.0, 54.0)), ((14.0, 58.0), (26.0, 56.0)), ((38.0, 57.0), (52.0, 58.0))):
            p.decal(lmask(p, [a, b]) & bed, STRAW, -2)
    p.part(egg, shell, 'sphere', base=0, sep=True, cx=30.0, cy=29.0, rx=19.0, ry=25.0, tex=TEX.get(shell.kind), spec=(25.0, 18.0))
    if spots is not None:
        for (x, y, r) in ((24.0, 22.0, 3.4), (40.0, 30.0, 4.2), (26.0, 42.0, 4.6), (40.0, 48.0, 3.0), (34.0, 15.0, 2.2)):
            p.decal(c.circle(x, y, r) & egg, spots, 0)
            p.decal(c.circle(x - r * 0.3, y - r * 0.3, r * 0.4) & egg, spots, 2)
    if crack:
        pts = [(17.0, 36.0), (23.0, 32.0), (28.0, 38.0), (34.0, 32.0), (40.0, 38.0), (46.0, 34.0)]
        p.line(pts, spots or shell, 2, 1.4)
        p.line([(x, y + 1.6) for x, y in pts], shell, -3, 1.0)
    if wisps:
        for (x0, y0) in ((5.0, 30.0), (48.0, 44.0)):
            w = c.polyline([(x0 + k, y0 + 1.8 * math.sin(k / 2.6)) for k in range(0, 12)], 1.8) & ~egg
            p.part(w, CLOUD, 'flat', base=2, sep=True, rim=False)
    if glow:
        p.glow(*glow)
    return egg


def wyrm_egg_hd(p):
    """The star wyrm's egg: pearl-white and faintly scaled, a gold star shimmering inside it, resting on a night
    cushion in a bronze cradle, lit in starlight (Will)."""
    c = p.c
    cush = (c.ellipse(32.0, 54.0, 22.0, 5.6) | c.ellipse(32.0, 56.5, 24.0, 4.0)) & c.box(0, 0, 64, 60.0)
    p.part(cush, NAVY, 'ray', base=0, sep=False, rim=False)
    p.decal(c.box(14.0, 53.0, 50.0, 54.2) & cush, NAVY, 1)
    for x in (9.0, 55.0):
        p.part(c.box(x - 1.6, 56.0, x + 1.6, 60.0), LANTERNBRONZE, 'ray', base=0, sep=True, tex='metal')
    egg = egg_hd(p, WYRM_HD, spots=None, crack=False, nest=False)
    inner = erode4(egg)
    for row, y in enumerate((18.0, 27.0, 36.0, 45.0)):
        for k in range(-3, 4):
            x = 32.0 + k * 8.4 + (4.2 if row % 2 else 0.0)
            p.decal(c.arc(x, y - 2.4, 4.6, 1.2, 200, 340) & inner & ~c.box(22.0, 28.0, 42.0, 48.0), WYRM_HD, -1)
    sx, sy = 32.0, 38.0
    p.decal(c.diamond(sx, sy, 7.6, 7.6) & inner, STARLIGHT, 0)
    p.decal((c.box(sx - 8.0, sy - 0.8, sx + 8.0, sy + 0.8) | c.box(sx - 0.8, sy - 8.0, sx + 0.8, sy + 8.0)) & inner, GOLD, 1)
    p.decal((c.box(sx - 2.5, sy - 0.8, sx + 2.5, sy + 0.8) | c.box(sx - 0.8, sy - 2.5, sx + 0.8, sy + 2.5)) & inner, WHITE, 0)
    for (x, y) in ((24.0, 26.0), (40.0, 48.0), (40.0, 26.0)):
        p.decal(c.circle(x, y, 1.0) & inner, GOLD, 1)
    p.glow(LANTERN_GLOW_HD, GLOW_STRENGTH['will'])


# The Spirit Beast Bags: the cloth tells the grade, the tie, its bead and the paw sewn on the front go with it
BEAST_BAGS_HD = {
    'reed': dict(grade='common', cloth=STRAW, tie=BAMBOO, trim=None, paw=DARKWOOD, glow=None),
    'hide': dict(grade='earth', cloth=LEATHER, tie=HEMP, trim=BRONZE, paw=BONE, glow=None),
    'cloud': dict(grade='heaven', cloth=M('cloud', 'silk'), tie=SKY, trim=SILVER, paw=JADE, glow=None),
    'mist': dict(grade='mystic', cloth=M('deepjade', 'silk'), tie=M('jade', 'silk'), trim=GOLD, paw=PEARL, glow='#67D6BD'),
    'star': dict(grade='spirit', cloth=VIOLETSILK, tie=M('gold', 'silk'), trim=GOLD, paw=GOLD, glow='#F3E3A6'),
}


def beast_bag_hd(kind):
    def draw(p):
        c = p.c
        B = BEAST_BAGS_HD[kind]
        body = bag_hd(p, B['cloth'], B['tie'], B['trim'], tex=TEX.get(B['cloth'].kind) or 'cloth')
        paw = c.ellipse(32.0, 45.0, 6.4, 5.2)
        for (x, y) in ((24.5, 38.0), (29.0, 34.0), (35.0, 34.0), (39.5, 38.0)):
            paw |= c.circle(x, y, 2.6)
        p.decal(paw & body, B['paw'], 0)
        p.decal(c.ellipse(30.0, 43.5, 2.4, 1.6) & body, B['paw'], 2)
        glow_hd(p, B['grade'], B['glow'])
    return draw


def drying_rack_hd(p):
    """A folding bamboo drying rack: two posts on their feet, two bars, bunches of herbs hung from the top bar and
    two more from the lower, tied with hemp."""
    c = p.c
    for x in (10.0, 54.0):
        post = c.box(x - 2.0, 8.0, x + 2.0, 58.0)
        p.part(post, BAMBOO, 'hgrad', base=0, sep=True, tex='wood', axis=90)
        for y in (24.0, 44.0):
            p.decal(c.box(x - 2.0, y, x + 2.0, y + 1.4) & post, BAMBOO, -2)
        p.part(c.box(x - 6.0, 57.0, x + 6.0, 60.0), BAMBOO, 'flat', base=-1, sep=True)
    for y in (13.0, 36.0):
        bar = c.box(6.0, y, 58.0, y + 3.6)
        p.part(bar, BAMBOO, 'vgrad', base=0, sep=True, tex='wood', axis=0)
    for k, (x, mat) in enumerate(((19.0, LEAF), (32.0, MOSS), (45.0, STRAW))):
        p.part(c.box(x - 1.0, 16.0, x + 1.0, 20.0), HEMP, 'flat', base=0, sep=True, rim=False)
        for (ang, L, W) in ((262, 15.0, 6.5), (278, 14.0, 6.0), (270, 16.0, 7.0)):
            leaf_hd(p, x, 19.0, ang, L, W, 0.0, 10, mat=mat)
    for k, (x, mat) in enumerate(((25.0, EMBER), (39.0, LEAF))):
        p.part(c.box(x - 1.0, 39.0, x + 1.0, 42.0), HEMP, 'flat', base=0, sep=True, rim=False)
        for (ang, L, W) in ((264, 13.0, 5.5), (276, 13.0, 5.5)):
            leaf_hd(p, x, 41.0, ang, L, W, 0.0, 10, mat=mat)


# ----------------------------------------------------------------------------- natural treasures
def mindwell_lotus_hd(p):
    """The Mindwell Lotus: a soul-violet lotus open on a jade pad, its gold heart giving off soul-light."""
    c = p.c
    pad_hd(p, 25.0, M('jade', 'matte'))
    lotus_hd(p, VIOLET, 0, 2, 10)
    head = c.ellipse(32.0, 34.0, 6.2, 3.4)
    p.part(head, GOLD, 'ray', base=0, sep=True, rim=False)
    for (x, y) in ((29.0, 33.5), (32.0, 32.5), (35.0, 33.5), (30.5, 35.5), (33.5, 35.5)):
        p.decal(c.circle(x, y, 0.9) & head, GOLD, -2)
    lotus_front(p, VIOLET, 0, 2, 10)
    p.sparkle(32.0, 9.0, 2)
    p.sparkle(50.0, 20.0, 1)
    p.glow('#9B78D1', 0.55)


def evergreen_heart_seed_hd(p):
    """The Evergreen Heart Seed: a dark almond seed with a red heart-line pulsing through it, the first green shoot
    breaking from its tip."""
    c = p.c
    seed = c.ellipse(30.0, 38.0, 15.0, 19.0)
    p.part(seed, WOOD, 'sphere', base=-1, sep=True, cx=27.0, cy=33.0, rx=17.0, ry=22.0, tex='wood', axis=90)
    vein = c.polyline(S.curve_pts((30.0, 22.0), (24.0, 36.0), (30.0, 54.0), 12), 2.2) & seed
    p.decal(vein, M('red'), 0)
    p.decal(c.polyline(S.curve_pts((30.0, 22.0), (24.0, 36.0), (30.0, 54.0), 12), 0.9) & seed, M('red'), 2)
    heart = c.circle(30.0, 38.0, 4.4) & seed
    p.decal(heart, M('red'), 0)
    p.decal(c.circle(28.6, 36.6, 1.4) & seed, M('red'), 3)
    stem_hd(p, [(32.0, 20.0), (36.0, 12.0), (42.0, 8.0)], (2.6, 1.8))
    leaf_hd(p, 41.0, 9.0, 20, 12.0, 6.0, 0.1, 10)
    p.glow('#D44B4E', 0.4)


def evergreen_heart_fruit_hd(p):
    """The Evergreen Heart Fruit: a heart-shaped crimson fruit on an evergreen sprig, warm with its own light."""
    c = p.c
    heart = c.circle(23.0, 30.0, 12.4) | c.circle(41.0, 30.0, 12.4) | c.poly([(11.2, 34.0), (52.8, 34.0), (32.0, 57.0)])
    p.part(heart, M('red', 'porcelain'), 'sphere', base=0, sep=True, cx=26.0, cy=30.0, rx=26.0, ry=26.0, spec=(20.0, 24.0))
    p.decal(c.ellipse(20.0, 27.0, 3.6, 2.2) & heart, M('red', 'porcelain'), 3)
    p.decal(c.polyline([(32.0, 34.0), (32.0, 52.0)], 1.2) & heart, M('red', 'porcelain'), -2)
    stem_hd(p, [(32.0, 22.0), (32.0, 16.0), (32.0, 10.0)], (2.4, 1.8), WOOD)
    for a, L in ((150, 15.0), (35, 15.0), (110, 11.0)):
        leaf_hd(p, 32.0, 13.0, a, L, 5.2, 0.0, 10)
    p.sparkle(48.0, 16.0, 2)
    p.glow('#F2B24C', 0.5)


def spirit_fruit_hd(p):
    """A Spirit Fruit: a pale jade peach with a blush of gold on its cheek, two leaves at the stem, a halo of Qi."""
    c = p.c
    body = c.circle(32.0, 36.0, 17.0) | c.poly([(20.0, 28.0), (44.0, 28.0), (32.0, 13.0)])
    p.part(body, JADE, 'sphere', base=1, sep=True, cx=28.0, cy=32.0, rx=19.0, ry=21.0, tex='jade')
    p.decal(c.circle(39.0, 40.0, 8.4) & body, GOLD, 0)
    p.decal(c.circle(41.0, 43.0, 4.4) & body, GOLD, 1)
    p.decal(c.ellipse(25.0, 30.0, 3.4, 2.4) & body, JADE, 3)
    p.decal(c.polyline(S.curve_pts((32.0, 16.0), (29.0, 30.0), (30.0, 50.0), 12), 1.0) & body, JADE, -2)
    stem_hd(p, [(32.0, 16.0), (32.0, 11.0), (33.0, 7.0)], (2.4, 1.6), WOOD)
    leaf_hd(p, 32.0, 11.0, 155, 15.0, 5.6, 0.0, 10)
    leaf_hd(p, 33.0, 10.0, 30, 13.0, 5.0, 0.0, 10)
    p.sparkle(50.0, 20.0, 2)
    p.glow('#9FE8C8', 0.5)


def hundred_year_wine_hd(p):
    """Hundred Year Wine: a jar dug from under old roots, black with age and furred with moss, its darkwood lid
    under a gold band and the paper seal still whole."""
    c = p.c
    jar = c.ellipse(32.0, 40.0, 19.0, 17.0) | c.box(24.0, 18.0, 40.0, 28.0)
    p.part(jar, MUD, 'sphere', base=0, sep=True, cx=27.0, cy=34.0, rx=23.0, ry=21.0, tex='clay')
    p.part(c.ellipse(32.0, 17.0, 10.0, 4.4), DARKWOOD, 'sphere', base=0, sep=True, tex='wood', axis=0)
    p.part(c.box(22.0, 24.0, 42.0, 27.0) & dilate4(jar), GOLD, 'flat', base=0, sep=True, tex='metal')
    for (x, y, r) in ((19.0, 44.0, 5.2), (43.0, 52.0, 4.4), (27.0, 54.0, 3.4), (46.0, 38.0, 2.8)):
        m = c.circle(x, y, r) & jar
        p.decal(m, MOSS, 0)
        p.decal(c.circle(x - r * 0.35, y - r * 0.35, r * 0.4) & jar, MOSS, 2)
    slip = c.box(29.0, 30.0, 36.0, 46.0) & jar
    p.part(slip, SEAL, 'flat', base=0, sep=True, rim=False)
    p.decal(c.box(30.0, 30.0, 31.0, 46.0) & slip, SEAL, 1)
    p.decal((c.box(31.5, 34.0, 34.5, 35.4) | c.box(32.5, 37.0, 33.5, 40.0) | c.box(31.5, 41.0, 34.5, 42.4)) & slip, PAPER, 1)


def longevity_peach_hd(p):
    """A Longevity Peach: pointed at the tip, rose-blushed on its lit cheek, cream at its foot, resting on two leaves."""
    c = p.c
    for a, L in ((200, 18.0), (340, 18.0)):
        leaf_hd(p, 32.0, 54.0, a, L, 6.5, 0.0, 10)
    body = c.circle(32.0, 38.0, 17.6) | c.poly([(17.0, 32.0), (47.0, 32.0), (33.0, 11.0)])
    p.part(body, LOTUS, 'sphere', base=1, sep=True, cx=28.0, cy=33.0, rx=20.0, ry=23.0)
    p.decal(c.circle(38.0, 26.0, 13.0) & body, M('red', 'porcelain'), 0)
    p.decal(c.circle(40.0, 24.0, 7.0) & body, M('red', 'porcelain'), 1)
    p.decal(c.circle(24.0, 48.0, 10.0) & body, RICE, 0)
    p.decal(c.polyline(S.curve_pts((33.0, 14.0), (28.0, 30.0), (26.0, 52.0), 12), 1.0) & body, LOTUS, -2)
    p.decal(c.ellipse(24.0, 28.0, 3.6, 2.4) & body, LOTUS, 3)


def thousand_year_lingzhi_hd(p):
    """A Thousand Year Lingzhi seen from the side: a lacquered red-brown cap ringed like an old tree with a pale
    growing edge, its dark stem set off-centre in moss."""
    c = p.c
    lac = mat7(Ramp(['#3A1410', '#6E2418', '#A83A22', '#D0653A', '#F0A070'], '#1A0806'), 'porcelain')
    p.part(c.ellipse(36.0, 57.0, 14.0, 3.2), MOSS, 'ray', base=0, sep=False, rim=False)
    stem = c.poly([(34.0, 32.0), (40.0, 32.0), (39.0, 56.0), (33.0, 56.0)])
    p.part(stem, DARKWOOD, 'ray', base=0, sep=True, tex='wood', axis=90)
    cap = c.ellipse(30.0, 32.0, 26.0, 18.0) & c.box(0, 0, 64, 34.0)
    p.part(cap, lac, 'sphere', base=0, sep=True, cx=24.0, cy=28.0, rx=30.0, ry=22.0, tex='glass')
    p.decal(cap & ~c.ellipse(30.0, 33.0, 23.2, 15.6), SAND, 0)
    p.decal(cap & ~c.ellipse(30.0, 33.0, 23.2, 15.6) & (c.X / p.s + c.Y / p.s < 56), SAND, 2)
    for r in (8.0, 15.0):
        p.decal(c.ring(30.0, 34.0, r, 1.6, r * 0.7) & cap & c.box(0, 0, 64, 31.0), lac, -2)
    p.decal(c.ellipse(20.0, 22.0, 4.0, 2.4) & cap, lac, 3)
    p.sparkle(52.0, 12.0, 2)


def guqin_hd(p):
    """A seven-string guqin lying on the diagonal: a lacquered board with its waisted end, the pale silk strings
    running its length, thirteen jade studs down one edge, a red tassel at the foot."""
    c = p.c
    qin = mat7(Ramp(['#1C0C08', '#321810', '#50261A', '#743C2A', '#A05C44'], '#0C0503'), 'porcelain')
    fr = Frame((12.0, 50.0), 40.0)
    L = 56.0
    board = fr.prof(c, [(0.0, 7.6), (6.0, 8.4), (38.0, 8.4), (42.0, 7.0), (47.0, 7.0), (51.0, 8.4), (L, 7.8)])
    p.part(board, qin, 'ray', base=0, sep=True, tex='glass')
    t, w = fr.along(c)
    top = board & (np.abs(w) < 6.2) & (t > 2.0) & (t < L - 2.0)
    p.decal(top & (w < -3.0), qin, 1)
    for k in range(7):
        wk = -5.4 + k * 1.8
        p.decal(top & (np.abs(w - wk) < 0.4) & (t > 5.0) & (t < L - 5.0), M('bone'), -1)
    p.decal(board & (t > 3.0) & (t < 5.0) & (np.abs(w) < 6.0), BRONZE, 0)
    p.decal(board & (t > L - 5.0) & (t < L - 3.0) & (np.abs(w) < 6.0), BRONZE, 0)
    for i in range(13):
        x, y = fr.P(7.0 + i * 3.5, -7.2)
        p.decal(c.circle(x, y, 1.0) & board, JADE, 2)
    p.decal(board & ~erode4(board) & (w < 0) & (t > 2.0) & (t < L - 2.0), qin, 2)
    tx, ty = fr.P(L - 1.0, 3.0)
    tassel_hd(p, dict(tassel=RED, bead=RED, lv=0), tx, ty + 1.0, 1.3)


# ----------------------------------------------------------------------------- S44 new forms: oils, a draught, baths, incense
def oil_hd(liquid):
    """A blade oil: a tall stoppered vial of it, a wiping rag knotted round its neck."""
    def draw(p):
        c = p.c
        vial_hd(p, GRADE_HD['plain'], liquid, cork=WOOD, shape='tall', level=0.72)
        rag = c.poly([(38.0, 16.0), (54.0, 20.0), (52.0, 30.0), (38.0, 24.0)]) | c.poly([(24.0, 17.0), (12.0, 26.0), (16.0, 30.0), (26.0, 24.0)])
        p.part(rag & ~c.rrect(27.5, 5.0, 36.5, 14.0, 1.4), HEMP, 'ray', base=0, sep=True, rim=False, tex='cloth', axis=20)
        p.part(c.box(25.0, 16.0, 39.0, 21.0), HEMP, 'ray_soft', base=-1, sep=True, rim=False)
        p.decal(c.ellipse(46.0, 24.0, 3.0, 2.0) & rag, liquid, 0)
    return draw


def riverreed_draught_hd(p):
    """A Riverreed Draught: a porcelain bowl of the green medicine, a reed root standing in it, steam rising."""
    c = p.c
    bowl = c.ellipse(32.0, 44.0, 23.0, 13.0) & c.box(0, 40.0, 64, 64)
    p.part(bowl, PORCELAIN, 'ray', base=0, sep=True, tex='glass')
    p.part(c.box(20.0, 55.0, 44.0, 58.5), PORCELAIN, 'flat', base=-2, sep=True)
    lip = c.ellipse(32.0, 40.0, 23.0, 5.0)
    p.part(lip, PORCELAIN, 'ray', base=1, sep=True, tex='glass')
    liq = c.ellipse(32.0, 40.0, 20.0, 3.4)
    p.part(liq, TEA, 'flat', base=0, sep=True, rim=False)
    p.decal(c.ellipse(26.0, 39.5, 6.0, 1.2) & liq, TEA, 2)
    root = c.polyline(S.curve_pts((40.0, 39.0), (48.0, 26.0), (44.0, 14.0), 12), 2.8)
    p.part(root, STRAW, 'ray_soft', base=0, sep=True, rim=False)
    for f in (0.3, 0.6):
        x, y = S.curve_pts((40.0, 39.0), (48.0, 26.0), (44.0, 14.0), 10)[int(f * 10)]
        p.decal(c.circle(x, y, 1.6) & root, STRAW, -2)
    smoke_hd(p, 26.0, 36.0, MIST, h=16.0, lean=-0.8, w=1.8)
    smoke_hd(p, 33.0, 35.0, MIST, h=18.0, lean=0.6, w=1.8)


def bath_hd(ribbon, herb, grade):
    """A body-trial bath: a bundle of hemp tied with its ribbon, the herbs that went into it standing out of the top."""
    def draw(p):
        c = p.c
        bundle = c.ellipse(32.0, 41.0, 20.0, 16.0) | c.poly([(20.0, 30.0), (25.0, 19.0), (39.0, 19.0), (44.0, 30.0)])
        p.part(bundle, HEMP, 'ray', base=0, sep=False, tex='cloth', axis=90)
        for pts in (((26.0, 22.0), (22.0, 40.0)), ((38.0, 22.0), (42.0, 40.0)), ((32.0, 21.0), (31.0, 30.0))):
            p.decal(lmask(p, pts) & bundle, HEMP, -2)
        for (a, b) in (((25.0, 21.0), (16.0, 9.0)), ((32.0, 20.0), (32.0, 7.0)), ((39.0, 21.0), (48.0, 9.0))):
            stem_hd(p, [a, ((a[0] + b[0]) / 2.0 - 1.5, (a[1] + b[1]) / 2.0), b], (2.6, 1.8), herb)
        for (x, y, ang, L) in ((20.0, 15.0, 165, 8.0), (44.0, 15.0, 15, 8.0), (32.0, 13.0, 150, 6.5), (32.0, 13.0, 30, 6.5)):
            leaf_hd(p, x, y, ang, L, 4.4, 0.05, 10, mat=herb)
        band = c.box(11.0, 31.0, 53.0, 36.0) & bundle
        p.part(band, ribbon, 'ray_soft', base=0, sep=True, rim=False, tex=TEX.get(ribbon.kind) if ribbon.kind in ('metal', 'gold') else None)
        p.part(c.diamond(32.0, 33.5, 4.6, 3.8), ribbon, 'ray', base=1, sep=True, rim=False)
        glow_hd(p, grade, '#FFE6A1')
    return draw


def calm_heart_incense_hd(p):
    """Calm Heart Incense: two plum sticks in a jade bowl ringed with prayer beads, the smoke tinged lotus-pink."""
    c = p.c
    bowl = bowl_hd(p, JADE)
    sticks_hd(p, (28.0, 36.0), (18.0, 22.0), 44.0, PLUM)
    for k in range(9):
        a = math.radians(200 + k * 17.5)
        x, y = 32.0 + 24.0 * math.cos(a), 46.0 - 9.0 * math.sin(a)
        p.part(c.circle(x, y, 2.4), WOOD, 'sphere', base=0, sep=True, spec=(x - 0.8, y - 0.8))
    smoke_hd(p, 28.0, 16.0, LOTUS, h=10.0, lean=-1.0, w=2.0)
    smoke_hd(p, 36.0, 20.0, LOTUS, h=12.0, lean=1.0, w=1.8)


# ----------------------------------------------------------------------------- V10 · Keeping Post: hour incense
# A fan of sandalwood sticks in a tall cup, the burn time as a numeral on the cup's label. Longer incense: more
# sticks and a richer holder (clay, then bronze, porcelain, jade and gold, with a rim, a band and feet).
DIGITS_HD = {'1': ['.#.', '##.', '.#.', '.#.', '###'], '2': ['###', '..#', '###', '#..', '###'], '4': ['#.#', '#.#', '###', '..#', '..#'],
             '7': ['###', '..#', '..#', '.#.', '.#.']}
STAGGER_HD = {2: [0, 2], 3: [2, 0, 3], 4: [2, 0, 3, 1], 5: [3, 1, 0, 2, 4], 6: [3, 1, 4, 0, 2, 4], 7: [4, 2, 0, 3, 1, 3, 5]}
HOUR_HD = {
    1: dict(grade='common', sticks=2, cup=CLAY, rim=None, band=None, feet=None, label=PAPER, ink=INK, ilv=0, glow=None),
    2: dict(grade='common', sticks=3, cup=CLAY, rim=BRONZE, band=None, feet=None, label=PAPER, ink=INK, ilv=0, glow=None),
    4: dict(grade='earth', sticks=4, cup=BRONZE, rim=BRONZE, band=None, feet=None, label=PAPER, ink=INK, ilv=0, glow=None),
    12: dict(grade='heaven', sticks=5, cup=PORCELAIN, rim=NAVY, band=NAVY, feet=NAVY, label=PAPER, ink=M('navy'), ilv=-1, glow=None),
    24: dict(grade='mystic', sticks=6, cup=JADE, rim=GOLD, band=None, feet=GOLD, label=PAPER, ink=INK, ilv=0, glow='#67D6BD'),
    72: dict(grade='spirit', sticks=7, cup=GOLD, rim=GOLD, band=JADE, feet=GOLD, label=SEAL, ink=GOLD, ilv=1, glow='#E5B84C'),
}


def digits_hd(p, s, cx, y0, cell, ink, lv, clip):
    """A numeral in 3 x 5 pixel digits, `cell` icon px a cell, centred on cx."""
    c = p.c
    w = (4 * len(s) - 1) * cell
    x = cx - w / 2.0
    for ch in s:
        for j, row in enumerate(DIGITS_HD[ch]):
            for i, ch2 in enumerate(row):
                if ch2 == '#':
                    p.decal(c.box(x + i * cell, y0 + j * cell, x + (i + 1) * cell, y0 + (j + 1) * cell) & clip, ink, lv)
        x += 4 * cell


def hour_incense_hd(hours):
    def draw(p):
        c = p.c
        H = HOUR_HD[hours]
        n = H['sticks']
        tops = []
        for k in range(n):
            x = 32.0 + (k - (n - 1) / 2.0) * 4.0
            y0 = 15.0 + 2.0 * STAGGER_HD[n][k]
            p.part(c.box(x - 1.0, y0, x + 1.0, 40.0), RED, 'flat', base=0 if k % 2 == 0 else -1, sep=True, rim=False)
            tops.append((x, y0))
        tall = sorted(tops, key=lambda t: (t[1], t[0]))[:2 if n > 3 else 1]
        for (x, y0) in tops:
            p.decal(c.box(x - 1.0, y0, x + 1.0, y0 + 1.8), FIRE, 2 if (x, y0) in tall else 0)
        for (x, y0) in tall:
            smoke_hd(p, x, y0 - 1.0, MIST, h=9.0, lean=-1.0 if x < 32.0 else 1.0, w=1.6)
        cup = c.rrect(18.0, 38.0, 46.0, 56.0, 2.5)
        p.part(cup, H['cup'], 'ray', base=0, sep=True, tex=TEX.get(H['cup'].kind))
        p.decal(c.box(19.0, 38.0, 45.0, 39.2) & cup, H['cup'], 2)
        if H['rim'] is not None:
            p.part(c.box(18.0, 38.0, 46.0, 41.5) & cup, H['rim'], 'vgrad', base=0, sep=True, tex=TEX.get(H['rim'].kind))
        if H['band'] is not None:
            p.part(c.box(18.0, 53.5, 46.0, 56.0) & cup, H['band'], 'flat', base=-1, sep=True, rim=False)
        if H['feet'] is not None:
            for x in (21.0, 43.0):
                p.part(c.box(x - 2.0, 56.0, x + 2.0, 59.0), H['feet'], 'ray', base=-1, sep=True)
        s = str(hours)
        lw = (4 * len(s) - 1) * 2.0 + 4.0
        lab = c.rrect(32.0 - lw / 2.0, 42.5, 32.0 + lw / 2.0, 54.5, 1.2)
        p.part(lab, H['label'], 'flat', base=0, sep=True, rim=False)
        digits_hd(p, s, 32.0, 43.5, 2.0, H['ink'], H['ilv'], lab)
        if hours == 72:
            p.sparkle(52.0, 44.0, 2)
        glow_hd(p, H['grade'], H['glow'])
    return draw


def wandering_incense_hd(p):
    """Wandering Incense: one twisted violet-brown stick in a bronze dish of sand, its smoke curling up into a
    question mark over the ember."""
    c = p.c
    dish = c.ellipse(32.0, 54.0, 16.0, 5.2)
    p.part(dish, BRONZE, 'ray', base=0, sep=True, tex='metal')
    sand = c.ellipse(32.0, 51.5, 9.5, 3.6)
    p.part(sand, SAND, 'ray', base=0, sep=True, rim=False)
    stick = c.polyline([(31.0 + 1.4 * math.sin(y / 3.0), y) for y in range(24, 53, 2)], 3.2)
    p.part(stick, PLUM, 'ray_soft', base=0, sep=True, rim=False)
    X, Y = XY(p)
    p.decal(stick & (np.floor(Y + X * 0.6).astype(int) % 4 == 0), PLUM, -2)
    p.decal(c.box(29.5, 24.0, 33.0, 26.4) & stick, FIRE, 1)
    p.decal(c.box(30.5, 23.5, 32.0, 24.8), FIRE, 3, only_on=False)
    q = c.arc(31.0, 12.0, 6.0, 2.6, 300, 200) | c.box(29.8, 14.5, 32.2, 19.5)
    p.part(q & ~c.a, VIOLET, 'ray_soft', base=0, sep=False, rim=False)
    p.part(c.circle(31.0, 21.5, 1.6) & ~stick, VIOLET, 'flat', base=1, sep=False, rim=False)
    p.decal(c.arc(31.0, 12.0, 6.0, 1.2, 100, 180), VIOLET, 2)


# ----------------------------------------------------------------------------- Act II · Sunscar Desert
def sun_crown_fragment_hd(p):
    """A ray broken from the Tomb King's sun crown: a gold spike with its lit and shaded faces, snapped from the
    band at its root, a jade bead set in a gold bezel there; it never cools (Sage)."""
    c = p.c
    fr = Frame((22.0, 44.0), 60.0)
    stump = c.poly([fr.P(-1.0, -9.0), fr.P(-1.0, 9.0), fr.P(-10.0, 8.5), fr.P(-7.0, 3.5), fr.P(-12.0, -0.5), fr.P(-8.0, -4.5), fr.P(-10.0, -8.5)])
    p.part(stump, GOLD, 'ray', base=0, sep=True, tex='metal')
    t, w = fr.along(c)
    p.decal(stump & (t < -6.5), GOLD, -2)
    ray = fr.prof(c, [(-1.0, 7.0), (14.0, 4.6), (44.0, 0.0)])
    p.cylinder(fr, ray, lambda tt: np.where(tt < 14.0, 7.0 - 2.4 * np.clip((tt + 1.0) / 15.0, 0, 1), np.clip(4.6 * (44.0 - tt) / 30.0, 0.0, 4.6)), GOLD,
               ridge=True, sep=True, tex='metal', axis=60.0)
    p.decal(ray & (np.abs(w) < 0.6) & (t > 6.0) & (t < 38.0), GOLD, 3)
    bx, by = fr.P(0.0, 0.0)
    p.part(c.circle(bx, by, 6.6), GOLD, 'sphere', base=0, sep=True, tex='metal')
    p.part(c.circle(bx, by, 4.2), JADE, 'sphere', base=0, sep=True, tex='jade', spec=(bx - 1.6, by - 1.6))
    p.sparkle(*fr.P(38.0, 3.0), 2)
    p.glow(SUN_GLOW_HD, GLOW_STRENGTH['sage'])


def sun_seal_hd(p, cx, cy, rd, rc, clip=None, rays=12, glyph=True):
    """The Sunscar sun seal: gold rays round a gold disc, a jade inlay ring, the field engraved between them, a jade
    heart with the sun glyph in gold."""
    c = p.c
    clip = np.ones_like(c.a) if clip is None else clip
    rm = c.empty()
    for k in range(rays):
        a = math.radians(k * 360.0 / rays + 90)
        L = rd + (rd * 0.45 if k % 2 == 0 else rd * 0.25)
        da = math.pi / rays * 0.8
        rm |= c.poly([(cx + math.cos(a - da) * (rd - 1.0), cy - math.sin(a - da) * (rd - 1.0)), (cx + math.cos(a) * L, cy - math.sin(a) * L),
                      (cx + math.cos(a + da) * (rd - 1.0), cy - math.sin(a + da) * (rd - 1.0))])
    p.part(rm & clip, GOLD, 'ray', base=0, sep=True, tex='metal')
    disc = c.circle(cx, cy, rd)
    p.part(disc & clip, GOLD, 'sphere', base=0, sep=True, cx=cx - 2.0, cy=cy - 2.0, rx=rd + 3.0, ry=rd + 3.0, tex='metal')
    ro, w = rd - 2.2, max(2.0, rd * 0.13)
    inlay = c.ring(cx, cy, ro, w) & clip
    p.part(inlay, JADE, 'flat', base=0, sep=True, rim=False, tex='jade')
    p.decal(inlay & c.sector(cx, cy, rd, 95, 200), JADE, 1)
    p.decal(inlay & c.sector(cx, cy, rd, 280, 350), JADE, -1)
    for k in range(rays):
        a = math.radians(k * 360.0 / rays + 90)
        r0, r1 = rc + 2.0, ro - w - 1.0
        p.decal(lmask(p, [(cx + math.cos(a) * r0, cy - math.sin(a) * r0), (cx + math.cos(a) * r1, cy - math.sin(a) * r1)]) & disc & ~inlay & clip, GOLD, -3)
    centre = c.circle(cx, cy, rc) & clip
    p.part(centre, JADE, 'sphere', base=0, sep=True, cx=cx - 1.0, cy=cy - 1.0, rx=rc + 2.0, ry=rc + 2.0, tex='jade')
    if glyph:
        p.decal((c.ring(cx, cy, rc * 0.62, 1.6) | c.circle(cx, cy, 1.4)) & centre, GOLD, 0)
    return disc | rm


def sun_seal_shard_hd(p):
    """A wedge snapped from the sun seal: about a third of the disc, from the jade heart out to the rayed rim, its
    broken edges showing the gold's thickness (Sage)."""
    c = p.c
    cx, cy, rd = 17.0, 45.0, 26.0
    pts = [(cx - 1.2, cy + 1.6)]
    for k, rr in enumerate((7.0, 13.0, 19.0, 25.0, 31.0, 39.0)):
        a = math.radians(-14 + (2.4 if k % 2 else -2.4) * (1 if k < 4 else 0))
        pts.append((cx + math.cos(a) * rr, cy - math.sin(a) * rr))
    for t in range(-14, 106, 6):
        a = math.radians(t)
        pts.append((cx + math.cos(a) * 40.0, cy - math.sin(a) * 40.0))
    for k, rr in enumerate((39.0, 31.0, 25.0, 19.0, 13.0, 7.0)):
        a = math.radians(104 + (2.4 if k % 2 else -2.4) * (1 if k > 1 else 0))
        pts.append((cx + math.cos(a) * rr, cy - math.sin(a) * rr))
    clip = c.poly(pts)
    side = (shift(clip, -2, -3) | shift(clip, 0, -2)) & ~clip & dilate4(c.circle(cx, cy, rd))
    p.part(side, GOLD, 'flat', base=-2, sep=False)
    sun_seal_hd(p, cx, cy, rd, 9.2, clip=clip, glyph=False)
    p.sparkle(44.0, 14.0, 1)
    p.glow(SUN_GLOW_HD, GLOW_STRENGTH['sage'] * 0.7)


def sunscar_seal_hd(p):
    """The Tomb King's sun seal, whole: a rayed gold disc with a jade heart, warm as a living hand (Sage)."""
    c = p.c
    sun_seal_hd(p, 32.0, 32.0, 19.0, 8.8)
    p.decal(c.ellipse(23.0, 23.0, 3.6, 2.0) & c.a, GOLD, 3)
    p.sparkle(52.0, 10.0, 2)
    p.glow(SUN_GLOW_HD, GLOW_STRENGTH['sage'])


# ----------------------------------------------------------------------------- Act II · Starsea
def star_hd(p, x, y, core=None, arm=None):
    """A small star: a bright core with four dimmer arms."""
    c = p.c
    p.decal(c.pts([(math.floor(x) + dx, math.floor(y) + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]), arm or SKY_INK_HD, 1 if arm is None else 0)
    p.decal(c.pts([(math.floor(x), math.floor(y))]), core or WHITE, 0)


def star_reading_hd(p):
    """A Star Reading: a slip of star paper, a constellation joined by fine lines in sky ink across it, one star
    caught in the red sighting ring, the far end rolling over (Sage)."""
    c = p.c
    fr = Frame((8.0, 41.0), 22.0)
    L = 50.0
    strip = fr.prof(c, [(0.0, 9.4), (L, 9.4)])
    p.part(strip, STARPAPER_HD, 'bevel', base=0, sep=False, hw=1, sw=1, tex='paper', rim=False)
    t, w = fr.along(c)
    roll = strip & (t > L - 7.0)
    p.part(roll, STARPAPER_HD, 'flat', base=-1, sep=True, rim=False)
    p.decal(roll & (t < L - 4.6), STARPAPER_HD, 1)
    p.decal(roll & (t > L - 2.0), STARPAPER_HD, -2)
    ear = strip & c.poly([fr.P(-0.5, 9.6), fr.P(6.0, 9.6), fr.P(-0.5, 3.0)])
    p.part(ear, STARPAPER_HD, 'flat', base=-1, sep=True, rim=False)
    stars = [fr.P(7.0, 3.0), fr.P(16.0, -4.0), fr.P(25.0, 3.0), fr.P(35.0, -3.5)]
    body = strip & ~roll & ~ear
    p.line(stars, SKY_INK_HD, 1, 1.0)
    for (x, y) in stars:
        p.decal(c.circle(x, y, 1.6) & body, SKY_INK_HD, -3)
        p.decal(c.pts([(math.floor(x), math.floor(y))]) & body, SKY_INK_HD, 2)
    sx, sy = stars[2]
    p.decal(c.ring(sx, sy, 6.0, 1.8) & body, SEAL, 0)
    p.sparkle(sx + 8.0, sy - 8.0, 1)
    p.glow(STAR_GLOW_HD, GLOW_STRENGTH['sage'] * 0.6)


def sky_ink_hd(p):
    """Sky Ink: a squat glass pot of deep indigo flecked with star-dust, corked under a silver cap, a run of ink
    down its shoulder (Spirit)."""
    c = p.c
    glass = M('mist', 'glass')
    body = c.rrect(8.0, 33.0, 56.0, 58.0, 8.0) | c.ellipse(32.0, 34.0, 20.0, 7.0)
    neck = c.box(22.0, 22.0, 42.0, 32.0)
    p.part(body | neck, glass, 'ray_soft', base=1, sep=False, tex='glass')
    ink = erode4(erode4(body)) & c.box(0, 31.0, 64, 64)
    p.part(ink, SKY_INK_HD, 'sphere', base=0, sep=False, rim=False, cx=27.0, cy=40.0, rx=26.0, ry=18.0, tex='glass')
    p.decal(ink & ~shift(ink, 0, 1), SKY_INK_HD, 2)
    for (x, y) in ((18.0, 42.0), (38.0, 40.0), (24.0, 50.0), (44.0, 50.0), (34.0, 53.0), (48.0, 43.0)):
        p.decal(c.circle(x, y, 0.9) & ink, WHITE, 0)
    for (x, y) in ((22.0, 45.0), (42.0, 46.0), (14.0, 49.0)):
        p.decal(c.circle(x, y, 0.8) & ink, GOLD, 1)
    p.sparkle(32.0, 44.0, 1)
    p.line([(11.0, 40.0), (11.0, 49.0)], glass, 3, 1.4)
    p.decal(c.circle(13.0, 36.0, 1.1), WHITE, 0)
    p.part(c.box(20.0, 21.0, 44.0, 24.0), glass, 'vgrad', base=2, sep=True, tex='glass')
    p.part(c.rrect(24.0, 15.0, 40.0, 22.0, 1.2), WOOD, 'ray', base=0, sep=True, tex='wood', axis=90)
    cap = c.rrect(22.0, 10.0, 42.0, 16.0, 1.5) | c.box(26.0, 8.0, 38.0, 10.0)
    p.part(cap, SILVER, 'ray', base=0, sep=True, tex='metal')
    p.decal(c.circle(32.0, 8.5, 1.2), CYAN, 1)
    drip = c.polyline([(42.0, 26.0), (44.0, 30.0), (45.0, 36.0), (44.5, 40.0)], 2.2) & ~ink
    p.part(drip & ~cap, SKY_INK_HD, 'flat', base=-1, sep=True, rim=False)
    p.decal(c.circle(44.5, 40.5, 1.6) & c.a, SKY_INK_HD, 1)
    p.glow('#9FB4FF', GLOW_STRENGTH['spirit'])


def ledger_page_hd(p):
    """One page torn from the Black Ledger: columns of entries leaning with the page, the stitch holes down its
    torn edge, a dark-red seal smudged across it."""
    c = p.c
    torn = [(20.0, 58.0), (17.0, 53.0), (20.0, 48.0), (16.0, 43.0), (19.0, 37.0), (15.0, 32.0), (18.0, 26.0), (14.0, 21.0), (17.0, 16.0), (14.0, 11.0)]
    m = c.poly([(48.0, 6.0), (55.0, 52.0)] + torn)
    p.part(m, PAPER, 'bevel', base=0, sep=False, hw=1, sw=1, tex='paper', rim=False)
    p.decal(m & ~erode4(m) & (c.X / p.s < 24), PAPER, 2)
    for (x, y) in ((22.0, 16.0), (22.0, 28.0), (24.0, 40.0), (26.0, 52.0)):
        p.decal(c.circle(x, y, 1.1) & m, PAPER, -3)
    for k, x0 in enumerate((44.0, 38.0, 32.0, 26.0)):
        y_top = 12.0 + (6.0 if k % 2 else 2.0)
        y_bot = 50.0 - (k * 6) % 10
        y, i = y_top, 0
        while y + 3.4 <= y_bot:
            if (i + k) % 4 != 3:
                x = x0 + (y - 8.0) * 0.14
                p.decal(c.box(x, y, x + 2.2, y + 3.4) & erode4(m), INK, 0)
            y += 5.2
            i += 1
    p.line([(24.0, 12.0), (46.0, 10.0)], SEAL, -1, 1.4)
    seal = c.poly([(38.0, 38.0), (49.0, 37.0), (50.0, 48.0), (39.0, 49.0)]) & erode4(m)
    smear = c.poly([(38.6, 42.0), (39.2, 48.8), (34.0, 51.2), (33.2, 48.4)]) & erode4(m)
    p.decal(smear, SEAL, -1)
    p.decal(seal, SEAL, -1)
    p.decal(seal & ~c.poly([(40.0, 40.0), (47.0, 39.2), (48.0, 46.0), (41.0, 47.0)]), SEAL, 0)
    p.decal(c.box(42.0, 42.0, 45.0, 43.4) & seal, SEAL, -3)


def black_ledger_hd(p):
    """Elder Gu's Black Ledger, stitched back together: a black lacquer cover split and sewn shut, gold corner
    caps, loose pages working out of the block, a red cord knotted round it."""
    c = p.c
    cv = book_hd(p, LACQUER_HD, x0=8.0, y0=8.0, x1=46.0, y1=50.0, spine=6.0, stitch=BONE)
    for pts in (((46.0, 18.0), (59.0, 21.0), (58.0, 26.0), (46.0, 24.0)), ((46.0, 40.0), (58.0, 45.0), (56.0, 49.0), (46.0, 44.0)),
                ((20.0, 52.0), (34.0, 53.0), (33.0, 59.0), (19.0, 58.0))):
        p.part(c.poly(pts) & ~cv, PAPER, 'flat', base=0, sep=True, rim=False)
    p.decal(lmask(p, [(18.0, 42.0), (24.0, 36.0)]) & cv, LACQUER_HD, 3)
    p.decal(lmask(p, [(40.0, 18.0), (42.0, 16.0)]) & cv, LACQUER_HD, 3)
    crack = c.polyline([(34.0, 8.0), (30.0, 14.0), (36.0, 20.0), (30.0, 26.0)], 1.0) & cv
    p.decal(shift(crack, 1, 0) & ~crack & cv, LACQUER_HD, 2)
    p.decal(crack, LACQUER_HD, -3)
    for (x, y) in ((32.0, 12.0), (32.0, 22.0)):
        p.decal(lmask(p, [(x - 2.0, y - 2.0), (x + 2.0, y + 2.0)]) | lmask(p, [(x + 2.0, y - 2.0), (x - 2.0, y + 2.0)]), HEMP, 0)
    for pts in (((40.0, 8.0), (46.0, 8.0), (46.0, 14.0)), ((46.0, 44.0), (46.0, 50.0), (40.0, 50.0))):
        p.part(c.poly(pts) & cv, GOLD, 'flat', base=0, sep=True, tex='metal')
    cord = c.box(8.0, 30.0, 46.0, 33.6) & cv
    p.part(cord, RED, 'ray_soft', base=0, sep=True, rim=False)
    p.part(c.polyline(S.curve_pts((36.0, 34.0), (40.0, 44.0), (48.0, 54.0), 10), 2.4), RED, 'flat', base=0, sep=True, rim=False)
    p.part(c.polyline(S.curve_pts((34.0, 34.0), (30.0, 46.0), (34.0, 57.0), 10), 2.4), RED, 'flat', base=-1, sep=True, rim=False)
    knot_hd(p, 35.0, 31.8, 3.4, RED)


def batten_sail_hd(p, pts, cloth, batten, n):
    """A junk sail: `n` battens split it into panels, each bellying (lit at its top, shaded below)."""
    c = p.c
    sail = c.poly(pts)
    p.part(sail, cloth, 'flat', base=0, sep=True, rim=False, tex='cloth', axis=0)
    ys = [y for (x, y) in pts]
    y0, y1 = min(ys), max(ys)
    rows = [y0 + (y1 - y0) * k / (n + 1.0) for k in range(1, n + 1)]
    edges = [y0] + rows + [y1]
    Y = XY(p)[1]
    for a, b in zip(edges, edges[1:]):
        panel = sail & (Y >= a) & (Y < b)
        p.decal(panel & (Y < a + (b - a) * 0.35), cloth, 1)
        p.decal(panel & (Y > a + (b - a) * 0.75), cloth, -1)
    for y in rows:
        p.decal(sail & (Y >= y - 0.7) & (Y < y + 0.7), batten, -2)
    return sail


def cloud_skiff_hd(p):
    """The player's cloud skiff: a low hull banded in jade with a painted eye, a mat canopy over the stern, one
    batten sail, a jade ward-lantern hung from a crook at the bow, a cushion of Qi mist under the keel (Sage)."""
    c = p.c
    mist = c.ellipse(19.0, 53.0, 8.4, 4.4) | c.ellipse(31.0, 54.5, 10.0, 4.6) | c.ellipse(43.0, 53.0, 8.4, 4.4)
    p.part(mist, QI_MIST_HD, 'ray', base=0, sep=False, rim=False)
    p.part(c.box(27.5, 6.0, 29.5, 38.0), WOOD, 'flat', base=0, sep=True, rim=False)
    batten_sail_hd(p, [(17.0, 11.0), (34.0, 8.0), (41.0, 18.0), (43.6, 36.0), (19.0, 36.0)], HEMP, DARKWOOD, 4)
    p.part(c.poly([(29.0, 5.0), (37.0, 6.6), (29.0, 9.0)]) & ~c.a, JADE, 'flat', base=0, sep=True, rim=False)
    can = c.ellipse(15.0, 37.0, 7.2, 6.4) & c.box(0, 0, 64, 37.0)
    p.part(can, STRAW, 'ray', base=0, sep=True, rim=False)
    Xc = XY(p)[0]
    p.decal(can & erode4(can) & (np.floor(Xc).astype(int) % 2 == 0), STRAW, -2)
    hull = c.poly([(7.0, 33.0), (16.0, 38.0), (46.0, 38.0), (54.0, 32.0), (51.0, 43.0), (42.0, 50.0), (18.0, 50.0), (12.0, 44.0)])
    p.part(hull, WOOD, 'ray', base=0, sep=True, tex='wood', axis=0)
    p.decal(c.box(8.0, 38.0, 52.0, 39.4) & hull, WOOD, 2)
    band = c.box(10.0, 40.0, 52.0, 42.4) & hull
    p.decal(band, JADE, -1)
    for x in np.arange(12.0, 50.0, 8.0):
        p.decal(c.box(x, 40.4, x + 2.4, 42.0) & hull, GOLD, 0)
    p.decal(c.ellipse(45.0, 45.5, 3.4, 2.2) & hull, PAPER, 1)
    p.decal(c.circle(45.8, 45.6, 1.2) & hull, INK, -1)
    crook = c.polyline([(50.0, 32.0), (50.0, 22.0), (52.0, 18.0), (56.0, 18.0)], 1.6)
    p.part(crook, WOOD, 'flat', base=0, sep=True, rim=False)
    lan = c.box(54.0, 20.0, 58.4, 27.0)
    p.part(lan, JADE, 'flat', base=2, sep=True, rim=False)
    p.part(c.box(53.4, 18.6, 59.0, 20.4) | c.box(53.4, 26.8, 59.0, 28.6), BRONZE, 'flat', base=0, sep=True)
    halo_hd(p, lan, '#67D6BD', (120, 60))
    p.glow(WARD_GLOW_HD, GLOW_STRENGTH['sage'] * 0.5)


def halo_hd(p, mask, col, alphas=(110, 50)):
    """Stepped glow bands round one part only, on empty canvas."""
    c = p.c
    cur = dilate4(mask) & (c.alpha > 0)
    for al in alphas:
        ring = dilate8(cur) & ~cur
        faint_hd(p, ring, col, al)
        cur |= ring


def storm_sloop_hd(p):
    """A two-sail storm sloop: a long dark hull on a comet-iron keel, two batten sails of sky silk, the formation
    ward's ring under her (Sage)."""
    c = p.c
    p.part(c.polyline([(23.0, 38.0), (19.0, 10.0)], 2.0) | c.polyline([(41.0, 38.0), (35.0, 8.0)], 2.0), DARKWOOD, 'flat', base=0, sep=True, rim=False)
    batten_sail_hd(p, [(9.0, 15.0), (20.0, 11.0), (25.0, 22.0), (27.0, 36.0), (11.0, 36.0)], SKY, STORM, 3)
    batten_sail_hd(p, [(26.0, 11.0), (36.0, 7.0), (47.0, 17.0), (53.0, 36.0), (29.0, 36.0)], SKY, STORM, 4)
    p.part(c.poly([(35.0, 5.0), (44.0, 6.4), (35.0, 9.0)]) & ~c.a, CYAN, 'flat', base=0, sep=True, rim=False)
    hull = c.poly([(6.0, 34.0), (12.0, 38.0), (52.0, 38.0), (59.0, 33.0), (53.0, 44.0), (15.0, 44.0), (9.0, 40.0)])
    p.part(hull, NAVY, 'ray', base=0, sep=True, tex='cloth', axis=0)
    p.decal(c.box(7.0, 38.0, 58.0, 39.4) & hull, GOLD, 0)
    keel = c.poly([(12.0, 44.0), (55.0, 44.0), (50.0, 48.0), (18.0, 48.0)])
    p.part(keel, COMETIRON, 'ray', base=0, sep=True, tex='metal')
    ring = c.ring(32.0, 41.0, 27.8, 2.0, 10.4)
    faint_hd(p, ring, WARD_GLOW_HD, 140)
    for (x, y) in ((4.0, 41.0), (60.0, 41.0), (16.0, 50.0), (48.0, 50.0)):
        faint_hd(p, c.circle(x, y, 1.6), '#E2FFFB', 230)
    p.glow(WARD_GLOW_HD, GLOW_STRENGTH['sage'] * 0.5)


def elder_token_hd(body, cord, face):
    """An Elder's token: the sect disc in a gold rim, a gold crest where the cord meets it, an elder's knot and
    tassel below, lit in gold (Sage)."""
    def draw(p):
        c = p.c
        m, inner = token_hd(p, body, 'disc', cord=cord, top=14.0, bottom=46.0, rim=GOLD, lv=6, tassel=False)
        knot = c.diamond(32.0, 50.0, 5.6, 4.8) | c.circle(26.0, 50.0, 2.6) | c.circle(38.0, 50.0, 2.6)
        p.part(knot, cord, 'ray', base=0, sep=True, rim=False)
        p.decal(c.diamond(32.0, 50.0, 2.6, 2.2), cord, -2)
        tassel_hd(p, dict(tassel=cord, bead=GOLD, lv=6), 32.0, 55.0, 1.2, knot=False)
        p.part(c.box(30.0, 53.0, 34.0, 55.5), GOLD, 'flat', base=0, sep=True, tex='metal')
        face(p, 32.0, 30.0, inner)
        crest = c.poly([(26.0, 18.0), (28.0, 12.0), (30.5, 15.0), (32.0, 10.0), (33.5, 15.0), (36.0, 12.0), (38.0, 18.0)]) & ~c.circle(32.0, 5.8, 2.4)
        p.part(crest, GOLD, 'ray', base=0, sep=True, tex='metal')
        p.sparkle(45.0, 20.0, 1)
        p.glow('#E5B84C', GLOW_STRENGTH['sage'])
    return draw


def jade_face_hd(p, cx, cy, inner):
    c = p.c
    hole = c.circle(cx, cy, 4.2)
    p.decal(c.ring(cx, cy, 10.5, 1.8) & inner, JADE, 1)
    p.decal(dilate4(hole) & ~hole, JADE, -2)
    p.erase(hole)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        x, y = cx + math.cos(a) * 7.6, cy + math.sin(a) * 7.6
        p.decal(c.circle(x, y, 1.6) & inner, GOLD, 0)
        p.decal(c.circle(x - 0.5, y - 0.5, 0.6) & inner, GOLD, 3)


def cloud_face_hd(p, cx, cy, inner):
    c = p.c
    cl = (c.ellipse(cx - 6.0, cy + 3.0, 5.6, 4.6) | c.ellipse(cx + 1.0, cy - 2.0, 7.0, 6.0) | c.ellipse(cx + 8.0, cy + 3.5, 5.0, 4.2) | c.box(cx - 10.0, cy + 3.0, cx + 12.0, cy + 7.0)) & inner
    p.part(cl, SKY, 'ray', base=0, sep=True, rim=False)
    p.decal(c.arc(cx + 1.0, cy - 2.0, 4.0, 1.4, 90, 300) & cl, SKY, 2)


# ----------------------------------------------------------------------------- Act III · Lantern Star Field
def admirals_seal_hd(p):
    """The Lantern Admiral's seal: a bronze eight-point star on a short chain, its points split along their spines
    to the light, an anchor engraved in the round face (Will)."""
    from families.pills import MARKS_HD
    c = p.c
    cx, cy, ro, ri = 32.0, 36.0, 23.0, 14.0
    p.part(c.box(30.5, 3.0, 33.5, 7.0), BRONZE, 'hgrad', base=0, sep=True, tex='metal')
    p.part(c.ring(32.0, 10.0, 4.2, 2.0, 5.0), BRONZE, 'ray', base=0, sep=True, tex='metal')
    pts = []
    for k in range(16):
        a = math.radians(90 - k * 22.5)
        r = ro if k % 2 == 0 else ri
        pts.append((cx + math.cos(a) * r, cy - math.sin(a) * r))
    star = c.poly(pts)
    p.part(star, LANTERNBRONZE, 'flat', base=0, sep=True, tex='metal')
    for k in range(0, 16, 2):
        tip = pts[k]
        for side in (-1, 1):
            nb = pts[(k + side) % 16]
            tri = c.poly([(cx, cy), tip, nb]) & star
            mx, my = (tip[0] + nb[0]) / 2.0 - cx, (tip[1] + nb[1]) / 2.0 - cy
            d = (-mx - my) / (math.hypot(mx, my) or 1.0) / 1.4142
            lvl = 1 if d > -0.2 else 0
            if side > 0 and lvl == 1 and d < 0.6:
                lvl = 0
            p.decal(tri, LANTERNBRONZE, lvl)
            p.decal(tri & ~erode4(tri) & star & (c.X / p.s + c.Y / p.s < cx + cy - 2.0), LANTERNBRONZE, 2)
    face = c.circle(cx, cy, 12.0)
    p.decal(face, LANTERNBRONZE, 0)
    p.decal(face & ~erode4(face), LANTERNBRONZE, -2)
    p.decal(face & ~erode4(face) & (c.X / p.s + c.Y / p.s > cx + cy + 2), LANTERNBRONZE, 2)
    for mask, d in MARKS_HD['anchor'](c, cx, cy + 1.0):
        p.decal(shift(mask, -1, -1) & face & ~mask, LANTERNBRONZE, 2)
        p.decal(mask & face, LANTERNBRONZE, -3 + d)
    p.sparkle(cx - 8.0, cy - 16.0, 1)
    p.glow(LANTERN_GLOW_HD, GLOW_STRENGTH['will'] * 0.7)


def lantern_incense_hd(p):
    """Lantern incense: a coil of pale-gold incense lying flat, its outer end burning with a small lantern flame
    and a curl of smoke (Sovereign)."""
    c = p.c
    cx, cy = 29.0, 43.0
    pts = []
    for i in range(111):
        f = i / 110.0
        th = math.pi * 1.5 + f * 2.2 * 2 * math.pi
        r = 3.0 + 21.0 * f
        pts.append((cx + r * math.cos(th), cy + r * 0.52 * math.sin(th)))
    coil = c.polyline(pts, 4.0)
    p.part(coil, STARLIGHT, 'sphere', base=0, sep=True, cx=cx - 6.0, cy=cy - 4.0, rx=30.0, ry=16.0, bands=((0.9, 1), (0.4, 0), (-0.2, -1), (-9, -2)))
    X, Y = XY(p)
    p.decal(coil & erode4(coil) & ~shift(erode4(coil), 0, -1), STARLIGHT, 2)
    p.decal(coil & ~erode4(coil) & (Y > cy + 2.0), STARLIGHT, -2)
    ex, ey = pts[-1]
    p.part(c.circle(ex, ey, 2.4), SMOKE_HD, 'sphere', base=0, sep=True, rim=False)
    fl = S.flame(c, ex + 1.0, ey - 2.0, 8.0, 14.0, 0.3)
    p.part(fl, FIRE, 'vgrad', base=0, sep=True, rim=False, bands=((0.3, 1), (0.7, 0), (9, -1)))
    p.decal(S.flame(c, ex + 1.0, ey - 3.0, 3.4, 7.0, 0.2) & fl, FIRE, 3)
    sm = c.polyline(S.curve_pts((ex + 1.0, ey - 17.0), (ex - 10.0, ey - 20.0), (ex - 4.0, ey - 28.0), 10), 2.2) | \
        c.polyline(S.curve_pts((ex - 4.0, ey - 28.0), (ex + 2.0, ey - 34.0), (ex - 6.0, ey - 37.0), 10), 1.8)
    p.part(sm & ~c.a, SMOKE_HD, 'flat', base=1, sep=False, rim=False)
    p.glow('#FFB45A', GLOW_STRENGTH['sovereign'])


# ----------------------------------------------------------------------------- V10c · rite tablets
# An upright plaque carved with columns of script in a stepped pedestal; the tier is the material and the crest.
RITE_HD = {
    'wood': dict(grade='common', body=DARKWOOD, face=M('red', 'porcelain'), script=(DARKWOOD, -3), trim=None, base=DARKWOOD, crest='round', glow=None),
    'jade': dict(grade='earth', body=JADE, face=JADE, script=(JADE, -3), trim=None, base=DEEPJADE, crest='hood', glow=None),
    'cloud': dict(grade='mystic', body=CLOUDSTONE_HD, face=CLOUDSTONE_HD, script=(M('sky'), -1), trim=SILVER, base=SILVER, crest='cloud', glow='#E9F1F4'),
    'star': dict(grade='sovereign', body=STARJADE_HD, face=STARJADE_HD, script=(GOLD, 1), trim=GOLD, base=GOLD, crest='star', glow=LANTERN_GLOW_HD),
}


def rite_crest_hd(c, kind):
    if kind == 'round':
        return c.ellipse(32.0, 18.0, 12.0, 8.0)
    if kind == 'hood':
        return c.ellipse(32.0, 17.0, 12.8, 8.4) | c.circle(20.0, 17.5, 3.8) | c.circle(44.0, 17.5, 3.8)
    if kind == 'cloud':
        return c.circle(23.5, 16.5, 5.6) | c.circle(32.0, 13.0, 6.8) | c.circle(40.5, 16.5, 5.6) | c.box(17.0, 16.0, 47.0, 21.0)
    return c.poly([(18.0, 22.0), (19.0, 16.0), (26.0, 13.0), (32.0, 5.5), (38.0, 13.0), (45.0, 16.0), (46.0, 22.0)])


def rite_tablet_hd(tier):
    def draw(p):
        c = p.c
        T = RITE_HD[tier]
        body, base = T['body'], T['base']
        foot = c.rrect(12.0, 52.0, 52.0, 59.0, 1.5)
        p.part(foot, base, 'ray', base=0, sep=False, tex=TEX.get(base.kind))
        step = c.box(16.0, 46.0, 48.0, 52.0)
        p.part(step, base, 'ray', base=1 if tier != 'star' else 0, sep=True, tex=TEX.get(base.kind))
        p.decal(c.box(17.0, 46.0, 47.0, 47.2) & step, base, 2)
        plaque = c.box(20.0, 18.0, 44.0, 46.0)
        crest = rite_crest_hd(c, T['crest'])
        m = plaque | crest
        p.part(m, body, 'ray', base=0, sep=True, tex=TEX.get(body.kind))
        if T['trim'] is not None:
            rim = m & ~erode4(erode4(m))
            p.part(rim, T['trim'], 'flat', base=0, sep=False, tex='metal')
            p.decal(rim & ((c.X / p.s > 43.0) | (c.Y / p.s > 44.5)), T['trim'], -2)
        else:
            p.decal(crest & ~erode4(crest) & (c.Y / p.s < 17.0) & (c.X / p.s < 34.0), body, 2)
        p.decal(c.box(20.0, 22.0, 44.0, 23.2) & ~erode4(crest & ~plaque) & m, body, -3)
        panel = c.box(24.0, 26.0, 40.0, 43.0)
        p.part(panel, T['face'], 'flat', base=1 if T['face'] is body else 0, sep=True, rim=False, tex=TEX.get(T['face'].kind))
        p.decal(c.box(24.0, 26.0, 40.0, 27.2) & panel, T['face'], 2)
        smat, slv = T['script']
        for (x, y0, y1) in ((35.0, 28.5, 41.0), (29.0, 30.5, 39.0)):
            y = y0
            while y + 2.2 <= y1:
                p.decal(c.box(x - 1.0, y, x + 1.0, y + 2.2) & panel, smat, slv)
                y += 3.4
        p.decal(c.pts([(36, 30), (32, 36), (26, 32)]) & panel, smat, slv)
        if tier == 'star':
            p.decal((c.box(28.0, 13.5, 36.0, 15.0) | c.box(31.2, 10.5, 32.8, 18.0)) & m, GOLD, 0)
            p.decal(c.box(31.2, 13.5, 32.8, 15.0) & m, WHITE, 0)
        if tier == 'cloud':
            for (x, y, r) in ((32.0, 14.0, 3.6), (23.5, 17.0, 2.4), (40.5, 17.0, 2.4)):
                p.decal(c.arc(x, y, r + 0.8, 1.4, 20, 250) & m, SILVER, -2)
        if tier == 'jade':
            p.part(c.circle(32.0, 15.5, 2.4), GOLD, 'sphere', base=0, sep=True, tex='metal')
        if T['glow']:
            p.sparkle(52.0, 10.0, 2)
            glow_hd(p, T['grade'], T['glow'])
    return draw


# ----------------------------------------------------------------------------- V10c · spirit wisp
def spirit_wisp_hd(p):
    """A spirit wisp: a small pale-blue soul flame, its teardrop head drifting down-left, the tail trailing up and
    curling over."""
    c = p.c
    head = c.circle(26.0, 41.0, 13.0)
    tail = c.taper((27.0, 32.0), (38.0, 26.0), (42.0, 12.0), 18.0, 5.0) | c.taper((42.0, 12.0), (45.0, 3.6), (53.0, 9.0), 5.0, 2.0)
    wisp = head | tail
    p.part(wisp, QI_MIST_HD, 'ray', base=-1, sep=False, rim=False)
    inner = (c.circle(25.0, 42.0, 8.8) | c.taper((26.0, 36.0), (35.0, 29.0), (39.0, 18.0), 11.0, 2.4)) & erode4(wisp)
    p.decal(inner, QI_MIST_HD, 1)
    p.decal(c.circle(24.0, 43.0, 4.8) & wisp, WHITE, 0)
    p.decal(c.circle(24.0, 43.0, 4.8) & wisp & ~c.circle(23.0, 42.0, 3.2), QI_MIST_HD, 3)
    for (x, y) in ((10.0, 28.0), (44.0, 48.0), (12.0, 54.0)):
        p.sparkle(x, y, 0)
    p.sparkle(54.0, 26.0, 1)
    p.glow(WARD_GLOW_HD, 1.0)


# ----------------------------------------------------------------------------- V10c · components
def hemp_cord_hd(p):
    """A hank of hemp rope: long loops bundled and bound round the middle with straw, a loose end hanging free."""
    c = p.c
    X, Y = XY(p)
    for (dy, base) in ((8.0, -1), (4.0, 0), (0.0, 0)):
        loop = c.ring(31.0, 26.0 + dy, 25.0, 4.8, 14.0)
        p.part(loop, HEMP, 'ray', base=base, sep=True, rim=False)
        p.decal(loop & (np.floor(X + Y).astype(int) % 3 == 0), HEMP, base - 1)
        p.decal(loop & (np.floor(X + Y).astype(int) % 3 == 1) & (Y < 26.0 + dy), HEMP, base + 1)
    end = c.taper((34.0, 44.0), (38.0, 54.0), (48.0, 57.0), 4.8, 4.0)
    p.part(end, HEMP, 'ray', base=0, sep=True, rim=False)
    p.decal(end & (np.floor(X + Y).astype(int) % 3 == 0), HEMP, -2)
    p.decal(c.box(46.0, 54.0, 50.0, 58.0) & end, HEMP, 2)
    bind = c.box(26.0, 8.0, 36.0, 46.0) & c.a
    p.part(bind, STRAW, 'hgrad', base=0, sep=True, rim=False)
    p.decal(bind & (np.floor(Y).astype(int) % 2 == 0), STRAW, -2)


def bronze_rivet_hd(p):
    """A handful of bronze rivets: domed heads on short shanks, some standing and some tipped over."""
    c = p.c

    def upright(x, y):
        shank = c.box(x - 1.2, y + 1.0, x + 1.2, y + 12.0)
        p.part(shank, BRONZE, 'hgrad', base=-1, sep=True, tex='metal')
        p.part(c.box(x - 2.6, y + 11.0, x + 2.6, y + 13.0), BRONZE, 'flat', base=-1, sep=True)
        head = c.ellipse(x, y + 0.5, 6.4, 3.2)
        p.part(head, BRONZE, 'sphere', base=0, sep=True, cx=x - 1.0, cy=y - 1.0, rx=7.0, ry=4.0, tex='metal')

    def lying(x, y):
        shank = c.box(x, y - 1.2, x + 12.0, y + 1.2)
        p.part(shank, BRONZE, 'vgrad', base=0, sep=True, tex='metal')
        p.part(c.box(x + 11.0, y - 2.6, x + 13.0, y + 2.6), BRONZE, 'flat', base=-1, sep=True)
        head = c.ellipse(x - 0.5, y, 3.2, 6.4)
        p.part(head, BRONZE, 'ray', base=0, sep=True, tex='metal')

    upright(16.0, 12.0)
    upright(38.0, 8.0)
    lying(34.0, 28.0)
    lying(8.0, 36.0)
    upright(28.0, 36.0)
    upright(48.0, 40.0)
    p.sparkle(56.0, 10.0, 1)


def kiln_brick_hd(p):
    """A fired kiln brick in three-quarter view, the bench's square stamp pressed into its top, scorch at its foot."""
    c = p.c
    X, Y = XY(p)
    top = c.poly([(8.0, 24.0), (36.0, 12.0), (58.0, 22.0), (30.0, 36.0)])
    front = c.poly([(8.0, 24.0), (30.0, 36.0), (30.0, 54.0), (8.0, 42.0)])
    side = c.poly([(30.0, 36.0), (58.0, 22.0), (58.0, 40.0), (30.0, 54.0)])
    p.part(front, CLAY, 'ray', base=0, sep=True, tex='clay')
    p.part(side, CLAY, 'ray', base=-1, sep=True)
    p.part(top, CLAY, 'ray', base=1, sep=True)
    for (x, y) in ((14.0, 32.0), (22.0, 40.0), (18.0, 44.0), (40.0, 38.0), (50.0, 32.0), (44.0, 44.0), (24.0, 22.0), (44.0, 18.0)):
        p.decal(c.circle(x, y, 0.9) & c.a, CLAY, -2)
    p.decal((front | side) & (Y > 47.0) & (np.floor(X).astype(int) % 2 == 0), CLAY, -3)
    st = c.poly([(24.0, 23.0), (34.0, 18.4), (43.0, 23.0), (33.0, 27.6)])
    p.decal(st, CLAY, -1)
    p.decal(st & ~(dilate4(~st)), CLAY, 0)
    p.decal((c.box(31.8, 21.6, 35.2, 24.4) | c.box(32.8, 20.4, 34.2, 25.6)) & st, CLAY, -2)
    p.decal(top & ~erode4(top) & (X < 37.0) & (Y < 25.0), CLAY, 2)


def lacquer_pot_hd(p):
    """A pot of red lacquer: a small black lidded pot with a red rim and knob, a drip down its belly, a brush with
    its red-dipped tip leaning on it."""
    c = p.c
    pot = c.ellipse(28.0, 43.0, 18.0, 14.4) | c.box(16.0, 26.0, 40.0, 32.0)
    p.part(pot, LACQUER_HD, 'sphere', base=0, sep=True, cx=22.0, cy=36.0, rx=22.0, ry=20.0, tex='glass')
    p.part(c.ellipse(28.0, 27.0, 14.8, 4.0), REDLAC_HD, 'ray', base=0, sep=True, tex='glass')
    lid = c.ellipse(28.0, 23.2, 15.2, 4.4)
    p.part(lid, LACQUER_HD, 'ray', base=1, sep=True, tex='glass')
    p.decal(c.box(18.0, 20.0, 32.0, 21.2) & lid, LACQUER_HD, 3)
    p.part(c.ellipse(28.0, 17.6, 4.0, 2.8), REDLAC_HD, 'sphere', base=0, sep=True)
    drip = c.box(18.0, 30.0, 20.4, 42.0) | c.circle(19.6, 43.6, 2.8)
    p.decal(drip & pot, REDLAC_HD, 0)
    p.decal(c.box(18.0, 30.0, 19.0, 37.0) & pot, REDLAC_HD, 2)
    p.decal(c.ellipse(28.0, 34.0, 18.0, 2.0) & pot & ~drip, REDLAC_HD, -1)
    fr = Frame((56.0, 8.0), 247.0)
    handle = fr.prof(c, [(0.0, 2.0), (36.0, 2.0)])
    p.cylinder(fr, handle, 2.0, BAMBOO, sep=True, tex='wood', axis=247.0)
    p.part(fr.prof(c, [(35.0, 2.2), (39.0, 2.6)]), BRONZE, 'ray', base=0, sep=True, tex='metal')
    bristle = fr.prof(c, [(39.0, 2.6), (46.0, 2.4), (52.0, 1.0)])
    p.part(bristle, STRAW, 'ray', base=0, sep=True, rim=False)
    t, w = fr.along(c)
    p.decal(bristle & (t > 46.0), REDLAC_HD, 0)


def whetstone_hd(p):
    """A grey whetstone on a small wooden stand, its top wet, with a glossy sheen and a bead of water."""
    c = p.c
    st = [((4.0, 34.0), (40.0, 18.0), (60.0, 28.0), (24.0, 46.0)), ((4.0, 34.0), (24.0, 46.0), (24.0, 54.0), (4.0, 42.0)), ((24.0, 46.0), (60.0, 28.0), (60.0, 36.0), (24.0, 54.0))]
    p.part(c.poly(st[1]), WOOD, 'flat', base=0, sep=False, tex='wood', axis=0)
    p.part(c.poly(st[2]), WOOD, 'flat', base=-1, sep=True, tex='wood', axis=30)
    p.part(c.poly(st[0]), WOOD, 'ray', base=1, sep=True, tex='wood', axis=30)
    stone_top = c.poly([(10.0, 28.0), (38.0, 15.0), (54.0, 23.0), (26.0, 36.4)])
    stone_front = c.poly([(10.0, 28.0), (26.0, 36.4), (26.0, 43.0), (10.0, 34.6)])
    stone_side = c.poly([(26.0, 36.4), (54.0, 23.0), (54.0, 29.6), (26.0, 43.0)])
    p.part(stone_front, STONE, 'flat', base=0, sep=True)
    p.part(stone_side, STONE, 'flat', base=-1, sep=True)
    p.part(stone_top, STONE, 'ray', base=1, sep=True)
    wet = c.poly([(18.0, 27.0), (38.0, 17.6), (48.0, 22.8), (28.0, 32.4)]) & erode4(stone_top)
    p.decal(wet, STONE, 0)
    p.decal(lmask(p, [(22.0, 26.0), (34.0, 20.0)]) & wet, M('ice'), 3)
    p.decal(lmask(p, [(30.0, 28.0), (40.0, 23.0)]) & wet, M('ice'), 2)
    p.part(c.circle(43.0, 24.4, 2.4), M('ice'), 'sphere', base=1, sep=True, rim=False)
    p.decal(c.circle(42.2, 23.6, 0.8), WHITE, 0)
    p.sparkle(14.0, 12.0, 2)


def spirit_glue_hd(p):
    """Spirit Glue: a small straw-yellow gourd corked and tied in red, amber glue welling at its mouth and running
    down its belly in a lit drip (Mystic)."""
    c = p.c
    lower = c.circle(31.0, 43.0, 16.4)
    upper = c.circle(31.0, 21.0, 9.6)
    neck = c.box(26.0, 24.0, 36.0, 30.0)
    gourd = lower | upper | neck
    p.part(gourd, STRAW, 'sphere', base=0, sep=False, cx=26.0, cy=32.0, rx=20.0, ry=26.0)
    p.decal(c.arc(31.0, 43.0, 12.8, 2.0, 110, 160) & gourd, STRAW, 2)
    p.part(c.rrect(28.0, 8.0, 34.0, 12.5, 1.0), WOOD, 'ray', base=0, sep=True, tex='wood', axis=90)
    tie = c.box(24.0, 28.0, 38.0, 30.4) & gourd
    p.part(tie, RED, 'flat', base=0, sep=True, rim=False)
    p.part(c.poly([(36.0, 30.0), (43.0, 37.0), (40.0, 38.0), (35.0, 32.0)]), RED, 'flat', base=1, sep=True, rim=False)
    well = c.ellipse(31.0, 14.0, 5.2, 2.4) | c.box(26.0, 14.0, 28.0, 20.0)
    drip = c.box(24.0, 18.0, 26.4, 36.0) | c.circle(25.2, 38.4, 3.4)
    glue = (well | drip) & ~c.rrect(28.0, 8.0, 34.0, 12.5, 1.0)
    p.part(glue, AMBER_HD, 'ray', base=0, sep=True, rim=False)
    p.decal(c.box(24.0, 20.0, 25.0, 32.0) & glue, AMBER_HD, 2)
    p.part(c.circle(25.2, 50.4, 2.4) & ~lower, AMBER_HD, 'sphere', base=0, sep=True, rim=False)
    p.sparkle(14.0, 12.0, 1)
    p.glow('#FFC870', GLOW_STRENGTH['mystic'])


# ----------------------------------------------------------------------------- v1.2 Phase D · Ash and Tide
def kharns_glaive_shard_hd(p):
    """The broken tip of Kharn's glaive: a broad curved blade, crimson on a bronze spine, its edge still ember-hot,
    the break jagged at the lower left (Will)."""
    c = p.c
    X, Y = XY(p)
    spine = S.curve_pts((9.0, 35.0), (26.0, 17.0), (57.0, 6.0), 18)
    edge = S.curve_pts((21.0, 58.0), (55.0, 46.0), (57.0, 6.0), 18)
    brk = [(21.0, 58.0), (15.0, 53.0), (18.0, 47.0), (11.0, 44.0), (14.0, 39.0), (9.0, 35.0)]
    blade = c.poly(spine + edge[::-1][:-1] + brk[:-1])
    p.part(blade, CRIMSON_HD, 'ray', base=0, sep=False, tex='metal')
    back = c.polyline(spine, 6.4) & blade
    p.part(back, BRONZE, 'ray', base=0, sep=True, tex='metal')
    p.decal(c.polyline(spine, 2.0) & blade & (Y > 8.0), BRONZE, 1)
    inset = [(x - 4.8, y - 4.8) for (x, y) in edge[:-2]]
    p.decal(c.polyline(inset, 1.6) & blade & ~back, CRIMSON_HD, 2)
    hot = c.polyline(edge, 4.0) & blade & ~back
    p.decal(hot, EMBER, 0)
    p.decal(c.polyline(edge, 2.0) & blade & ~back, EMBER, 1)
    p.decal(c.polyline(edge, 2.0) & blade & ~back & (X - Y > 8.0), EMBER, 3)
    p.decal(c.polyline(brk, 2.8) & blade, CRIMSON_HD, -3)
    p.decal(c.pts([(16, 42), (18, 50), (12, 46)]) & blade, BRONZE, -2)
    p.decal(c.pts([(14, 40), (20, 48)]) & blade, BRONZE, 2)
    p.glow('#F58A3A', GLOW_STRENGTH['will'])


def copperjaw_box_hd(p):
    """A lacquered Copperjaw box seen from the front, bronze at its corners, its lid lifted ajar and two copper
    beetles crawling on the rim (Will)."""
    c = p.c
    front = c.box(10.0, 34.0, 46.0, 56.0)
    side = c.poly([(46.0, 34.0), (56.0, 27.0), (56.0, 49.0), (46.0, 56.0)])
    top = c.poly([(10.0, 34.0), (20.0, 27.0), (56.0, 27.0), (46.0, 34.0)])
    p.part(top, INK, 'flat', base=-1, sep=False, rim=False)
    p.part(side, BLACKLAC_HD, 'flat', base=-1, sep=True, tex='glass')
    p.part(front, BLACKLAC_HD, 'bevel', base=0, sep=True, hw=2, sw=2, tex='glass')
    p.decal(lmask(p, [(16.0, 48.0), (22.0, 42.0)]) & front, BLACKLAC_HD, 3)
    for (x0, y0, x1, y1) in ((10.0, 50.0, 15.0, 56.0), (41.0, 50.0, 46.0, 56.0), (10.0, 34.0, 15.0, 39.0), (41.0, 34.0, 46.0, 39.0)):
        p.part(c.box(x0, y0, x1, y1), BRONZE, 'bevel', base=0, sep=True, hw=1, sw=1, tex='metal')
    p.part(c.box(52.0, 44.0, 56.0, 49.0), BRONZE, 'flat', base=-1, sep=True)
    lid_top = c.poly([(8.0, 19.0), (17.0, 12.0), (56.0, 17.0), (50.0, 25.0)])
    lid_front = c.poly([(8.0, 19.0), (50.0, 25.0), (50.0, 29.0), (8.0, 23.0)])
    p.part(lid_front, BLACKLAC_HD, 'flat', base=-1, sep=True, tex='glass')
    p.part(lid_top, BLACKLAC_HD, 'ray', base=0, sep=True, tex='glass')
    p.decal(lmask(p, [(14.0, 16.0), (22.0, 14.0)]) & lid_top, BLACKLAC_HD, 3)
    p.part(c.poly([(8.0, 19.0), (13.0, 15.2), (13.0, 23.8), (8.0, 23.0)]), BRONZE, 'flat', base=0, sep=True, tex='metal')
    p.part(c.poly([(45.0, 24.2), (50.0, 25.0), (50.0, 29.0), (45.0, 28.2)]), BRONZE, 'flat', base=0, sep=True, tex='metal')
    for (x, y) in ((22.0, 30.0), (38.0, 10.0)):
        body = c.ellipse(x + 1.0, y + 1.0, 3.8, 2.6)
        p.part(body, COPPER, 'sphere', base=1, sep=True, tex='metal')
        p.part(c.circle(x - 3.6, y + 0.4, 1.4), COPPER, 'sphere', base=-1, sep=True)
        for (ax, ay, bx, by) in ((x - 2.0, y + 3.0, x - 3.0, y + 5.0), (x + 2.0, y + 3.2, x + 3.0, y + 5.2), (x + 4.0, y - 1.0, x + 6.0, y - 2.4)):
            p.line([(ax, ay), (bx, by)], COPPER, -3, 1.0, only_on=False)
        p.decal(c.circle(x + 0.5, y + 0.5, 0.8), COPPER, 3)
    p.glow('#E69A5A', GLOW_STRENGTH['will'] * 0.5)


MISC_HD_B = (
    [('spirit_egg', lambda p: egg_hd(p, PEARL, QI)), ('rare_spirit_egg', lambda p: egg_hd(p, GOLD, M('red', 'porcelain'))),
     ('cloud_stag_egg', lambda p: egg_hd(p, M('cloud', 'porcelain'), SKY, crack=False, wisps=True)), ('wyrm_egg', wyrm_egg_hd)]
    + [('beast_bag_' + k, beast_bag_hd(k)) for k in BEAST_BAGS_HD]
    + [('drying_rack', drying_rack_hd), ('mindwell_lotus', mindwell_lotus_hd), ('evergreen_heart_seed', evergreen_heart_seed_hd),
       ('evergreen_heart_fruit', evergreen_heart_fruit_hd), ('spirit_fruit', spirit_fruit_hd), ('hundred_year_wine', hundred_year_wine_hd),
       ('longevity_peach', longevity_peach_hd), ('thousand_year_lingzhi', thousand_year_lingzhi_hd), ('guqin', guqin_hd),
       ('viper_oil', oil_hd(VENOM)), ('ember_oil', oil_hd(M('ember', 'glass'))), ('riverreed_draught', riverreed_draught_hd),
       ('copper_body_bath', bath_hd(COPPER, MOSS, 'common')), ('marrow_washing_bath', bath_hd(BONE, LOTUS, 'earth')),
       ('jade_marrow_bath', bath_hd(JADE, MIST, 'heaven')), ('golden_body_bath', bath_hd(GOLD, FIRE, 'mystic')),
       ('calm_heart_incense', calm_heart_incense_hd)]
    + [('hour_incense_%d' % h, hour_incense_hd(h)) for h in HOUR_HD]
    + [('wandering_incense', wandering_incense_hd), ('sun_crown_fragment', sun_crown_fragment_hd), ('sun_seal_shard', sun_seal_shard_hd),
       ('sunscar_seal', sunscar_seal_hd), ('star_reading', star_reading_hd), ('sky_ink', sky_ink_hd), ('ledger_page', ledger_page_hd),
       ('black_ledger', black_ledger_hd), ('star_chart_wreck', lambda p: star_chart_hd(p, 'wreck', JADE)),
       ('star_chart_lantern', lambda p: star_chart_hd(p, 'lantern', GOLD)), ('cloud_skiff', cloud_skiff_hd), ('storm_sloop', storm_sloop_hd),
       ('jade_elder_token', elder_token_hd(JADE, RED, jade_face_hd)), ('cloud_elder_token', elder_token_hd(PORCELAIN, SKY, cloud_face_hd)),
       ('admirals_seal', admirals_seal_hd), ('lantern_incense', lantern_incense_hd)]
    + [(t + '_rite_tablet', rite_tablet_hd(t)) for t in RITE_HD]
    + [('spirit_wisp', spirit_wisp_hd), ('hemp_cord', hemp_cord_hd), ('bronze_rivet', bronze_rivet_hd), ('kiln_brick', kiln_brick_hd),
       ('lacquer_pot', lacquer_pot_hd), ('whetstone', whetstone_hd), ('spirit_glue', spirit_glue_hd), ('kharns_glaive_shard', kharns_glaive_shard_hd),
       ('copperjaw_box', copperjaw_box_hd)]
)


def star_chart_hd(p, end, cord):
    """A star chart half open: a night field on star paper with a dotted route between the stars, the far edge
    curling, the rest rolled up on the right under a cord with a bead; the Wreck Run ends at a broken ship, the
    Lantern Run at lanterns hanging in the dark (Sage)."""
    c = p.c
    sheet = c.box(8.0, 14.0, 44.0, 50.0)
    p.part(sheet, STARPAPER_HD, 'bevel', base=0, sep=False, hw=1, sw=1, tex='paper', rim=False)
    field = c.box(10.0, 17.0, 42.0, 46.0)
    p.part(field, SKY_INK_HD, 'vgrad', base=0, sep=True, rim=False, bands=((0.3, 0), (0.7, -1), (9, -1)))
    p.part(c.box(6.0, 12.0, 8.5, 52.0), STARPAPER_HD, 'hgrad', base=0, sep=True, rim=False)
    fr = Frame((50.0, 56.0), 90.0)
    roll = fr.prof(c, [(0.0, 6.0), (48.0, 6.0)])
    p.cylinder(fr, roll, 6.0, STARPAPER_HD, sep=True, tex='paper')
    p.part(c.ellipse(50.0, 8.0, 6.0, 3.0), STARPAPER_HD, 'flat', base=0, sep=True, rim=False)
    p.decal(c.ellipse(50.0, 8.0, 3.0, 1.4), STARPAPER_HD, -3)
    if end == 'wreck':
        route, into = [(14.0, 42.0), (22.0, 36.0), (30.0, 40.0), (36.0, 32.0)], (28.0, 26.0)
    else:
        route, into = [(14.0, 42.0), (20.0, 34.0), (28.0, 38.0), (26.0, 28.0)], (34.0, 24.0)
    pts = route + [into]
    dots = c.empty()
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        for k in range(int(L / 3.0) + 1):
            f = k * 3.0 / L
            dots |= c.circle(a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, 0.7)
    p.decal(dots & field, GOLD, 0)
    for (x, y) in route:
        star_hd(p, x, y, core=WHITE, arm=SKY_INK_HD)
    if end == 'wreck':
        ex, ey = into
        hull = c.poly([(ex - 8.0, ey + 2.0), (ex - 1.0, ey + 2.0), (ex - 2.0, ey + 6.0), (ex - 7.0, ey + 6.0)]) | c.poly([(ex + 1.0, ey + 1.0), (ex + 8.0, ey + 1.0), (ex + 7.0, ey + 5.0), (ex + 2.0, ey + 5.0)])
        p.decal(hull & field, BONE, 0)
        p.decal((c.polyline([(ex - 4.0, ey + 2.0), (ex - 2.0, ey - 6.0)], 1.2) | c.polyline([(ex + 4.0, ey + 1.0), (ex + 8.0, ey - 5.0)], 1.2)) & field, BONE, -1)
    else:
        ex, ey = into
        for (x, y) in ((ex - 6.0, ey), (ex, ey - 4.0), (ex + 5.0, ey + 2.0), (ex - 2.0, ey + 6.0)):
            p.decal(c.box(x - 0.5, y - 3.0, x + 0.5, y - 1.5) & field, SKY_INK_HD, 2)
            p.decal(c.ellipse(x, y, 2.0, 2.4) & field, FIRE, 0)
            p.decal(c.circle(x - 0.6, y - 0.6, 0.8) & field, FIRE, 3)
    band = c.box(43.0, 30.0, 57.0, 33.6)
    p.part(band, cord, 'ray_soft', base=0, sep=True, rim=False, tex=TEX.get(cord.kind))
    p.part(c.polyline(S.curve_pts((56.0, 33.0), (60.0, 42.0), (57.5, 50.0), 10), 1.8) & ~roll, cord, 'flat', base=0, sep=True, rim=False)
    p.part(c.circle(57.5, 52.0, 2.4), cord, 'sphere', base=0, sep=True, tex=TEX.get(cord.kind))
    p.sparkle(24.0, 21.0, 1)
    p.glow(STAR_GLOW_HD, GLOW_STRENGTH['sage'] * 0.5)


for _id, _draw in MISC_HD_A + MISC_HD_B:
    register(FAM, _id, _draw, GROUP)
    hd(_id, _draw)
