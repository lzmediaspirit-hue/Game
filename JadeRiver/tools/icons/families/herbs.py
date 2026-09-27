"""Herbs (HD, Style A): every herb, seed and garden material at 64 art px, shown 1:1 in the 76 px slot, with a native
@32 render for the HUD item ring and the small slots.

A herb is living plant matter drawn with botanical care on the clump of earth, stone, snow or water it grows from.
The species drawers (SPECIES_HD) take the herb's age from HERBS_HD and show it by form, never by colour alone: an
older herb is larger, with more growth rings and root hairs, more petals, bells or pods; its veins turn gold at a
hundred years and jade-pale at ten thousand; a herb of Mystic grade and above carries its spirit aura as stepped glow
bands. The seeds share one hemp pouch and a tag stamped in the herb's colour, the seeds spilled beside it in their
own shape (SEEDS_HD). The garden materials (spring water, spirit soil, the dyed root, rice wine) are one-offs.
"""
import math

import numpy as np

from pix import Ramp, erode4, dilate4, move
from palette import GLOW_STRENGTH, M, R, STAR_GLOW, mat7
from registry import hd, register
import shapes as S

FAM, GROUP = 'items', 'herbs'
ART = 64   # HD (tools/icons/README.md, "How to convert a family")

# The ember cactus's green (Act II, Sunscar)
CACTUS = Ramp(['#173A2C', '#27603F', '#428A55', '#78B46A', '#BEDF9C'], '#081A12')
# Act III, Lantern Star Field: the star lotus's nebula sea and its seed head
NEBULA_TEAL = Ramp(['#0A2436', '#123E52', '#1E6474', '#3A9498', '#8CD4C8'], '#041018')
NEBULA_MAGENTA = Ramp(['#3A1240', '#6A2470', '#A444A0', '#D67CCC', '#F6C4EE'], '#18061C')
SEED_HEAD = Ramp(['#443A12', '#766A22', '#B0A23E', '#DCD078', '#F6F0C0'], '#1C1806')


# ============================================================================= HD (Style A, 64 icon space)
# Every icon is one drawing `draw(p)` in a 64 x 64 icon space (tools/icons/README.md, "HD drawing model"), the object
# inside the 4-px margin; the same description renders at 64 and at 32. The materials, then the shared builders (the
# clump of earth, a stem, a leaf with its rib and age veins, the lotus bloom, the seed pouch), then the species.
LEAF, MOSS, SOIL, STONE, SAND, SNOW, WAX, GOLD, STRAW, HEMP, PAPER = (M('leaf'), M('moss'), M('mud'), M('warmstone'), M('sand'),
                                                                    M('cloud'), M('wax'), M('gold'), M('straw'), M('hemp'), M('paper'))
PAD, MIST, PINK, ICE_PETAL, ICE, BERRY, PEPPER, PEPPER_OLD, PEPPER_YOUNG, FIRE = (M('jade', 'matte'), M('mist'), M('lotuspink'), M('sky'), M('ice'),
                                                                                  M('red', 'porcelain'), M('ember', 'porcelain'), M('seal', 'porcelain'),
                                                                                  M('fire', 'porcelain'), M('fire'))
ORCHID, VIOLET, QI, BONE, YELLOW, WOODROOT, CLAY, CYAN, PEARL = (M('cloud', 'silk'), M('violet', 'silk'), M('qi'), M('bone'), M('yellow'), M('darkwood'),
                                                                 M('clay'), M('cyan'), M('pearl'))
CACTUS_HD = mat7(CACTUS, 'matte')
# A ten-thousand-year root: pale as jade, through-lit like it
JADEROOT = mat7(Ramp(['#4E6A5C', '#86A88E', '#C4E0C0', '#E4F6E0', '#F6FFF6'], '#1C2E26'), 'jade')
# The vein material and level by age (None: the leaf's own dark tone)
VEINS = {10: None, 100: (GOLD, 0), 1000: (GOLD, 1), 10000: (JADEROOT, 2)}


def XY(p):
    """Pixel centres in icon space."""
    return p.c.X / p.s, p.c.Y / p.s


def lmask(p, pts, w=1.0):
    """The mask of a stroke through icon-space points, as `PixelPainter.line` draws it (1-px Bresenham at 1:1)."""
    c = p.c
    if w <= 1.0 and p.s == 1.0:
        return c.bres_path([(int(math.floor(x)), int(math.floor(y))) for x, y in pts])
    return c.polyline(pts, w)


def soil_hd(p, cx, cy, rx, ry, mat=None):
    """The clump of earth a herb grows from: a low mound with dark clods and two lit grains."""
    c = p.c
    mat = mat or SOIL
    m = c.ellipse(cx, cy, rx, ry)
    p.part(m, mat, 'sphere', base=0, sep=True, cx=cx - rx * 0.25, cy=cy - ry * 0.4, rx=rx * 1.2, ry=ry * 1.7, rim=False)
    for (fx, fy, r) in ((-0.55, 0.25, 1.5), (0.12, 0.45, 1.3), (0.55, -0.05, 1.4), (-0.15, -0.35, 1.0)):
        p.decal(c.circle(cx + fx * rx, cy + fy * ry, r) & m, mat, -2)
    for (fx, fy) in ((-0.35, -0.45), (0.3, -0.55)):
        p.decal(c.circle(cx + fx * rx, cy + fy * ry, 0.8) & m, mat, 2)
    return m


def stem_hd(p, pts, w, mat=None, lv=0):
    """A stem along the quadratic bezier through three icon-space points, its width from w[0] to w[1]."""
    if isinstance(w, (int, float)):
        w = (w, w)
    m = p.c.taper(pts[0], pts[1], pts[2], w[0], w[1])
    p.part(m, mat or LEAF, 'ray_soft' if max(w) >= 3 else 'flat', base=lv, sep=True, rim=False)
    return m


def rib_pts(bx, by, ang, L, bend=0.0, frac=0.78, n=8):
    """Points along a leaf's centre line (shapes.lens_pts' bow) from the base to `frac` of its length."""
    dx, dy = S._dir(ang)
    px, py = -dy, dx
    out = []
    for i in range(n + 1):
        t = i / float(n) * frac
        off = bend * math.sin(math.pi * t) * L
        out.append((bx + dx * t * L + px * off, by + dy * t * L + py * off))
    return out


def leaf_hd(p, bx, by, ang, L, W, bend=0.0, age=10, mat=None, tip_power=0.8, rib=True, base=0):
    """A leaf from (bx, by) along `ang` (0 right, 90 up), with its midrib; from a hundred years the rib and two pairs
    of side veins are gold (VEINS), at ten thousand jade-pale."""
    c = p.c
    mat = mat or LEAF
    m = c.leaf(bx, by, ang, L, W, bend, tip_power=tip_power)
    p.part(m, mat, 'ray', base=base, sep=True, rim=False)
    if rib and L >= 10:
        vein, lv = VEINS[age] or (mat, -2)
        pts = rib_pts(bx, by, ang, L, bend)
        p.decal(lmask(p, pts) & m, vein, lv)
        if age >= 100 and L >= 14:
            dx, dy = S._dir(ang)
            px, py = -dy, dx
            for t in (0.3, 0.55):
                i = int(round(t / 0.78 * 8))
                x, y = pts[i]
                for sgn in (1, -1):
                    p.decal(lmask(p, [(x, y), (x + (dx * L * 0.12 + px * W * 0.3 * sgn), y + (dy * L * 0.12 + py * W * 0.3 * sgn))]) & m, vein, lv)
    return m


def sparkles_hd(p, pts, age):
    """The glints an aged herb throws: one at a hundred years, two at a thousand, three at ten thousand."""
    for (x, y, arm) in pts[:{10: 0, 100: 1, 1000: 2, 10000: 3}[age]]:
        p.sparkle(x, y, arm)


# ----------------------------------------------------------------------------- willow moss
def willow_moss_hd(p, age=10):
    """Willow moss on the gnarled root it grows from: a moss cushion over the root, strands hanging beneath."""
    c = p.c
    # the strands hang from under the root, back to front, each overlapping the last so the mass reads as one drape
    strands = [(9, 24, 7, 49), (15, 22, 13, 56), (21, 20, 20, 52), (27, 18.5, 27, 58), (33, 18, 33, 53), (39, 18.5, 39, 58), (45, 19.5, 46, 52), (51, 21, 52, 56), (56, 23, 57, 48)]
    for (sx, sy, ex, ey) in strands:
        strand = c.taper((sx, sy), (sx + (ex - sx) * 0.3, (sy + ey) / 2.0), (ex, ey), 7.4, 2.6)
        p.part(strand, MOSS, 'ray', base=0, sep=True, rim=False)
        p.decal(lmask(p, [(sx - 2, sy + 8), (sx + (ex - sx) * 0.35 - 2, (sy + ey) / 2.0 + 2), (ex - 1, ey - 6)]) & erode4(strand), MOSS, 1)
    # the willow root, bowed, with a knot and a long crack
    root = c.taper((8, 25), (28, 12), (57, 21), 9.5, 7.5) | c.ellipse(44, 16.5, 6.5, 5.5)
    p.part(root, WOODROOT, 'ray', base=0, sep=True, tex='wood', axis=8)
    p.decal(lmask(p, [(8, 23.5), (20, 18.5), (34, 16.5), (48, 17.5), (56, 20.5)]) & erode4(root), WOODROOT, -2)
    p.decal(c.ring(44, 16.5, 3.4, 1.0) & erode4(root), WOODROOT, -2)
    p.decal(c.ring(44, 16.5, 1.4, 0.9) & erode4(root), WOODROOT, -2)
    cushion = (c.ellipse(15, 15.5, 8, 4.8) | c.ellipse(27, 12.5, 9.5, 5.4) | c.ellipse(39, 11.5, 8, 4.6) | c.ellipse(52, 14.5, 6, 3.8)) & c.box(0, 0, 64, 20)
    p.part(cushion, MOSS, 'ray_soft', base=1, sep=True, rim=False)
    X, Y = XY(p)
    tuft = (np.floor(Y / 3).astype(int) % 2 == 0) & (np.floor((X + 1.5 * (np.floor(Y / 3) % 2)) / 3).astype(int) % 2 == 0)
    p.decal(tuft & erode4(cushion), MOSS, -1)
    for (x, y) in ((12, 12), (24, 9), (37, 8.5), (51, 12)):
        p.decal(c.circle(x, y, 0.9), MOSS, 2)
    for (sx, sy, ex, ey) in ((18, 15, 15, 34), (34, 12, 32, 36), (49, 15, 48, 30)):
        strand = c.taper((sx, sy), (sx + (ex - sx) * 0.5, (sy + ey) / 2.0), (ex, ey), 4.6, 1.8)
        p.part(strand, MOSS, 'ray', base=0, sep=True, rim=False)


# ----------------------------------------------------------------------------- riverreed ginseng
def ginseng_hd(p, age):
    """A riverreed ginseng root lifted whole with its clump of earth, the leaves and the berry stalk above. Age by
    form: a larger root with more growth rings and root hairs, gold hairs at a hundred years, gold to the tips at a
    thousand, and a root pale as jade at ten thousand."""
    c = p.c
    s = {10: 0.9, 100: 1.0, 1000: 1.06, 10000: 1.1}[age]
    root = JADEROOT if age >= 10000 else WAX

    def P(x, y):   # scale about the neck's top
        return (32 + (x - 32) * s, 24 + (y - 24) * s)
    soil_hd(p, 32, 55, 16, 4.6)
    for (ex, ey, fan) in ((17, 15, (112, 148, 184)), (47, 15, (68, 32, -4))):
        ex, ey = P(ex, ey)
        stem_hd(p, [P(32, 23), ((32 + ex) / 2.0, ey + 5), (ex, ey)], (2.6, 1.8))
        for a in fan:
            leaf_hd(p, ex, ey, a, 10.5 * s, 5.6 * s, 0.0, age, rib=False)
    stem_hd(p, [P(32, 23), P(32.5, 16), P(32, 10)], (2.6, 2.0))
    berries = [(32, 7.6), (29.2, 10.4), (34.8, 10.4)] + ([(30.4, 13.6), (33.6, 13.6)] if age >= 100 else [])
    for (bx, by) in berries:
        bx, by = P(bx, by)
        r = 2.3 * s
        p.part(c.circle(bx, by, r), BERRY, 'sphere', base=0, sep=True, spec=(bx - r * 0.4, by - r * 0.4))
    neck = c.poly([P(28, 22), P(36, 22), P(37.5, 30), P(26.5, 30)])
    body = c.ellipse(*P(32, 37), 9.5 * s, 10 * s)
    arms = c.taper(P(25, 33), P(18, 33.5), P(12, 40), 6 * s, 2.2 * s) | c.taper(P(39, 33), P(46, 33.5), P(52, 39), 6 * s, 2.2 * s)
    legs = c.taper(P(29, 44), P(25, 49), P(21, 54), 7 * s, 2.4 * s) | c.taper(P(35, 44), P(39, 48.5), P(43, 54), 7 * s, 2.4 * s)
    m = neck | body | arms | legs
    p.part(m, root, 'ray', base=0, sep=True)
    # growth rings across the neck and body, more with age (softer on the jade root, which is lit from within)
    core = erode4(neck | body)
    ys = {10: (25, 28), 100: (25, 27.5, 30, 33), 1000: (24.5, 27, 29.5, 32, 35, 38),
          10000: (24.5, 27, 29.5, 32, 34.5, 37, 40)}[age]
    for y in ys:
        ring = lmask(p, [P(23, y), P(32, y + 0.9), P(41, y)]) & core
        p.decal(ring, root, -1 if age >= 10000 else -2)
        if age < 10000:
            p.decal(move(ring, 0, 1) & core & ~ring, root, 1)
    if age >= 10000:
        p.decal(c.ellipse(*P(30, 36), 4.5 * s, 5 * s) & core, root, 1)
    # the tips go gold at a thousand years
    if age == 1000:
        for (x, y) in ((12, 40), (52, 39), (21, 54), (43, 54)):
            p.decal(c.circle(*P(x, y), 3.2 * s) & m, GOLD, 0)
    # root hairs
    hairs = [((12, 40), (7, 43)), ((52, 39), (57, 42)), ((21, 54), (17, 56.5)), ((43, 54), (47, 56.5)), ((24, 39), (19, 43)), ((40, 40), (45, 44))]
    if age >= 100:
        hairs += [((13, 37), (8, 35)), ((51, 36), (56, 34)), ((23, 51), (18, 51.5)), ((41, 51), (46, 51.5))]
    if age >= 1000:
        hairs += [((27, 47), (22, 49)), ((37, 47), (42, 49)), ((25, 35), (21, 31)), ((39, 35), (43, 31))]
    if age >= 10000:
        hairs += [((16, 42), (12, 46)), ((48, 41), (52, 45))]
    hmat, hlv = VEINS[age] or (root, -1)
    for (a, b) in hairs:
        h = lmask(p, [P(*a), P(*b)]) & ~erode4(m)
        p.decal(h, hmat, hlv, only_on=False)
    sparkles_hd(p, ((53, 15, 1), (11, 20, 1), (55, 47, 1)), age)


# ----------------------------------------------------------------------------- ember pepper
def pepper_hd(p, age):
    """An ember pepper plant: a stem with two leaves from its clump of earth, the pods hanging glossy on the right,
    heat wisps off the tip. At a hundred years both pods are full-grown and dark red, and the heat rises in three."""
    c = p.c
    old = age >= 100
    soil_hd(p, 28, 56, 14, 4.2)
    stem_hd(p, [(22, 54), (18, 34), (24, 15)], (3.2, 2.2))
    leaf_hd(p, 21, 44, 162, 16, 8.0, 0.1, age)
    leaf_hd(p, 19, 30, 128, 14, 7.0, 0.08, age)
    leaf_hd(p, 23, 20, 52, 11, 5.6, -0.06, age)
    # the pods hang from the stem's top, the back one behind and to the right
    pods = [((40, 18), (48, 32), (43, 50), (12.5 if old else 9.5, 2.4), PEPPER_OLD if old else PEPPER_YOUNG),
            ((27, 21), (35, 38), (30, 57), (13.5, 2.6), PEPPER_OLD if old else PEPPER)]
    for (p0, p1, p2, (w0, w1), mat) in pods:
        pod = c.taper(p0, p1, p2, w0, w1)
        p.part(pod, mat, 'ray', base=0, sep=True)
        gloss = c.taper((p0[0] - w0 * 0.22, p0[1] + 4), (p1[0] - w0 * 0.34, p1[1] - 2), (p2[0] - 1.5, p2[1] - 9), 2.6, 1.0)
        p.decal(gloss & erode4(pod), mat, 2)
        p.decal(c.circle(p0[0] - w0 * 0.2, p0[1] + 5, 1.0) & pod, mat, 3)
        for a in (238, 270, 302):
            p.part(c.leaf(p0[0], p0[1] - 1, a, w0 * 0.6, w0 * 0.3, 0.0, tip_power=0.7), LEAF, 'ray', base=0, sep=True, rim=False)
        p.part(c.ellipse(p0[0], p0[1] - 0.5, w0 * 0.36, w0 * 0.22), LEAF, 'ray', base=0, sep=True, rim=False)
        stem_hd(p, [(p0[0], p0[1] - 2), ((p0[0] + 24) / 2.0, 13), (24, 15)], 2.0, lv=-1)
    # the heat off its flank: one wisp, three at a hundred years
    for (x, by, w, h, lean) in [(52, 42, 5.0, 10, 0.4), (56, 28, 4.2, 8, -0.3), (48, 12, 4.0, 7, 0.3)][:3 if old else 1]:
        p.part(S.flame(c, x, by, w, h, lean), FIRE, 'vgrad', base=1, sep=False, rim=False)
    sparkles_hd(p, ((10, 16, 1),), age)


# ----------------------------------------------------------------------------- the lotuses
def lotus_hd(p, mat, base, tip_lv, age, extra_back=False, tip_power=0.7):
    """A lotus bloom at (32, 46): three back petals, two side petals (a taller pair behind them when `extra_back`),
    then, after the caller draws the seed head, `lotus_front` cups it with two low front petals. Petals in `mat` at
    `base`, their tips recoloured by `tip_lv`, a rib by age."""
    bx, by = 32.0, 46.0
    back = [(bx - 2, by, 128, 28, 13.6, -0.06), (bx + 2, by, 52, 28, 13.6, 0.06), (bx, by + 1, 90, 31, 15.4, 0.0)]
    if extra_back:
        back = [(bx - 4, by, 146, 26, 12.4, -0.1), (bx + 4, by, 34, 26, 12.4, 0.1)] + back
    side = [(bx - 2, by, 160, 25, 12.4, -0.12), (bx + 2, by, 20, 25, 12.4, 0.12)]
    for (x, y, a, L, W, b) in back + side:
        petal_hd(p, mat, base, tip_lv, age, x, y, a, L, W, b, tip_power)


def petal_hd(p, mat, base, tip_lv, age, x, y, a, L, W, b, tip_power=0.7):
    c = p.c
    m = c.leaf(x, y, a, L, W, b, tip_power=tip_power)
    p.part(m, mat, 'ray', base=base, sep=True, tex='cloth', axis=a, rim=False)
    dx, dy = math.cos(math.radians(a)), -math.sin(math.radians(a))
    p.decal(c.circle(x + dx * L * 0.9, y + dy * L * 0.9, L * 0.3) & m, mat, tip_lv)
    vein, lv = VEINS[age] or (mat, base - 1)
    p.decal(lmask(p, [(x + dx * 3, y + dy * 3), (x + dx * L * 0.7, y + dy * L * 0.7)]) & m, vein, lv)
    return m


def lotus_front(p, mat, base, tip_lv, age):
    for (x, y, a) in ((30, 47, 116), (34, 47, 64)):
        petal_hd(p, mat, base, tip_lv, age, x, y, a, 12.5, 10, 0.0)


def pad_hd(p, rx, mat=None):
    """The lily pad the lotus floats on, with its radial vein and a lit crease."""
    mat = mat or PAD
    pad = p.c.ellipse(32, 51, rx, 7.6)
    p.part(pad, mat, 'ray', base=0, sep=False, rim=False)
    p.line([(32, 49), (32 + rx * 0.8, 48.5)], mat, -2, 1.0)
    p.line([(32 - rx * 0.5, 47), (30, 45)], mat, 1, 1.0)
    return pad


def mist_lotus_hd(p, age):
    """A mist lotus open on its pad, waterfall mist drifting in front. At a hundred years a taller pair of petals
    stands behind, its seed head is fuller, and the petal ribs are gold."""
    c = p.c
    old = age >= 100
    pad = pad_hd(p, 27 if old else 25)
    lotus_hd(p, PINK, 1, 0, age, extra_back=old)
    head = c.ellipse(32, 34, 7.2 if old else 6.2, 4.0 if old else 3.4)
    p.part(head, GOLD, 'ray', base=0, sep=True, rim=False)
    for (x, y) in ((28, 33.5), (32, 32.5), (36, 33.5), (30, 35.5), (34, 35.5)):
        p.decal(c.circle(x, y, 0.9) & head, GOLD, -2)
    lotus_front(p, PINK, 1, 0, age)
    mist = (c.ellipse(15, 57, 12.5, 3.2) | c.ellipse(43, 58, 15, 3.4) | c.ellipse(55, 53, 6, 2.8)) & ~erode4(pad)
    p.part(mist, MIST, 'ray_soft', base=1, sep=True, rim=False)
    sparkles_hd(p, ((50, 20, 1),), age)


def frost_lotus_hd(p, age=10):
    """A frost lotus on a snow drift: ice-blue petals with sharper tips rimed white, an ice crystal in its heart."""
    c = p.c
    drift = c.ellipse(32, 52, 26, 7.6) | c.ellipse(20, 55, 10, 4.5)
    p.part(drift, SNOW, 'ray', base=1, sep=False, rim=False)
    p.line([(14, 51), (26, 48)], SNOW, 3, 1.0)
    lotus_hd(p, ICE_PETAL, 1, 3, age, tip_power=0.55)
    crystal = c.diamond(32, 34, 3.6, 5.0)
    p.part(crystal, ICE, 'ray', base=1, sep=True, tex='glass', spec=(30.6, 31.5))
    lotus_front(p, ICE_PETAL, 1, 3, age)
    for (x, y) in ((12, 22), (52, 22), (32, 10), (46, 56), (18, 57)):
        p.sparkle(x, y, 1)


# ----------------------------------------------------------------------------- cloudtop orchid
def orchid_bloom(p, cx, cy, s, old=False):
    """An orchid bloom: five cloud-white petals, a violet lip, a gold throat."""
    c = p.c
    for (a, L, W) in ((95, 12.5, 7.0), (200, 11.5, 7.0), (340, 11.5, 7.0), (150, 10.5, 8.2), (30, 10.5, 8.2)):
        m = c.leaf(cx, cy, a, L * s, W * s, 0.0, tip_power=0.9)
        p.part(m, ORCHID, 'ray', base=1, sep=True, rim=False)
        dx, dy = math.cos(math.radians(a)), -math.sin(math.radians(a))
        p.decal(lmask(p, [(cx + dx * 2, cy + dy * 2), (cx + dx * L * s * 0.6, cy + dy * L * s * 0.6)]) & m, ICE_PETAL, 0)
    lip = c.ellipse(cx, cy + 4.6 * s, 4.2 * s, 4.6 * s)
    p.part(lip, VIOLET, 'ray', base=-1 if old else 0, sep=True, rim=False)
    p.decal(c.ellipse(cx, cy + 5.5 * s, 2.0 * s, 2.2 * s) & lip, VIOLET, -2)
    p.part(c.ellipse(cx, cy + 0.6 * s, 2.4 * s, 2.0 * s), GOLD, 'ray', base=0, sep=True, rim=False)


def orchid_hd(p, age):
    """A cloudtop orchid on the ledge only flyers reach: strap leaves from a stone shelf wreathed in cloud, the
    blooms on an arching stem. At a hundred years a third bloom opens and the lips go deep violet."""
    c = p.c
    old = age >= 100
    ledge = c.poly([(6, 51), (13, 45), (28, 43), (45, 44.5), (58, 50), (57, 58), (8, 58)])
    p.part(ledge, STONE, 'ray', base=0, sep=False)
    p.line([(14, 50), (26, 47), (42, 48)], STONE, -2, 1.0)
    p.decal(c.ellipse(24, 46, 5, 1.6) & ledge, STONE, 1)
    leaf_hd(p, 28, 46, 118, 26, 7.4, 0.10, age)
    leaf_hd(p, 30, 46, 64, 22, 6.8, -0.12, age)
    leaf_hd(p, 27, 47, 156, 16, 6.0, 0.08, age)
    stem_hd(p, [(30, 45), (30, 22), (47, 10)], (3.0, 2.0))
    stem_hd(p, [(30, 32), (26, 22), (23, 16)], (2.2, 1.6))
    if old:
        stem_hd(p, [(38, 16), (46, 22), (52, 30)], (2.2, 1.6))
    cloud = (c.ellipse(13, 55, 9, 4.6) | c.ellipse(24, 57, 8, 3.6) | c.ellipse(50, 56, 9, 4.6) | c.ellipse(40, 58, 7, 3.0)) & c.box(0, 0, 64, 60)
    p.part(cloud, SNOW, 'ray_soft', base=1, sep=True, rim=False)
    p.decal(c.arc(13, 55, 8, 1.2, 200, 260) & cloud, SNOW, -1)
    p.decal(c.arc(50, 56, 8, 1.2, 280, 340) & cloud, SNOW, -1)
    orchid_bloom(p, 45, 19, 1.15, old)
    orchid_bloom(p, 22, 15, 0.85, old)
    if old:
        orchid_bloom(p, 53, 33, 0.9, old)
    bud = c.ellipse(51, 9, 3.2, 2.6)
    p.part(bud, ORCHID, 'ray', base=1, sep=True, rim=False)
    sparkles_hd(p, ((10, 18, 1),), age)


# ----------------------------------------------------------------------------- soulbell flower
def bell_hd(p, x, y, s):
    """A soulbell hanging from (x, y): the violet bell with its ribs, the glowing mouth and clapper, a green cap."""
    c = p.c
    pts = [(-4.4, 0), (4.4, 0), (6, 6.4), (10.4, 14), (8.8, 16), (-8.8, 16), (-10.4, 14), (-6, 6.4)]
    m = c.poly([(x + px * s, y + py * s) for px, py in pts])
    p.part(m, VIOLET, 'ray', base=0, sep=True, rim=False)
    for k in (-1, 1):
        p.decal(lmask(p, [(x + 2 * k * s, y + 2 * s), (x + 6.5 * k * s, y + 13 * s)]) & erode4(m), VIOLET, -2)
    mouth = c.ellipse(x, y + 15.2 * s, 7.6 * s, 2.2 * s) & m
    p.decal(mouth, QI, 1)
    p.decal(c.ellipse(x, y + 15.6 * s, 4 * s, 1.2 * s) & m, QI, 3)
    p.part(c.box(x - 1.1 * s, y + 16 * s, x + 1.1 * s, y + 18.6 * s), QI, 'flat', base=0, sep=True, rim=False)
    p.part(c.ellipse(x, y - 0.4 * s, 5.2 * s, 2.6 * s), LEAF, 'ray', base=0, sep=True, rim=False)


def soulbell_hd(p, age):
    """A soulbell flower from its clump of earth: two leaves, an arching stem and the bells that ring against the
    soul, qi motes drifting off them. At a hundred years a third bell hangs from the stem's crook."""
    c = p.c
    old = age >= 100
    soil_hd(p, 30, 56, 15, 4.2)
    leaf_hd(p, 28, 54, 148, 19, 7.6, 0.1, age)
    leaf_hd(p, 30, 54, 36, 19, 7.6, -0.1, age)
    stem_hd(p, [(29, 54), (22, 6), (48, 12)], (3.0, 2.0))
    stem_hd(p, [(27, 32), (22, 24), (14, 26)], (2.2, 1.6))
    if old:
        stem_hd(p, [(30, 20), (36, 16), (39, 22)], (2.2, 1.6))
    bell_hd(p, 47, 13, 1.25)
    bell_hd(p, 14, 26, 0.95)
    if old:
        bell_hd(p, 39, 22, 1.0)
    for (x, y) in ((56, 44), (40, 50), (8, 50), (58, 30)):
        p.decal(c.circle(x, y, 1.1), QI, 2, only_on=False)
    p.sparkle(57, 38, 1)
    sparkles_hd(p, ((9, 12, 1),), age)


# ----------------------------------------------------------------------------- ember cactus
def cactus_hd(p, age=10):
    """A round desert cactus with ribs and pale spines on its mound of sand, a pup beside it, crowned by the flower
    that stores the Sunscar sun."""
    c = p.c
    X, Y = XY(p)
    soil_hd(p, 32, 56, 20, 4.6, SAND)
    pup = c.ellipse(50, 47, 7, 6.6)
    p.part(pup, CACTUS_HD, 'sphere', base=0, sep=True, rim=False)
    body = c.ellipse(30, 38, 17, 16)
    p.part(body, CACTUS_HD, 'sphere', base=0, sep=True, rim=False)
    inner = erode4(body)
    for rx in (6.0, 12.4):
        rib = S.outline_only(c.ellipse(30, 38, rx, 16)) & inner & (abs(Y - 38) < 14.5)
        p.decal(rib, CACTUS_HD, -2)
    p.decal(c.box(29.5, 24, 30.5, 53) & inner, CACTUS_HD, -2)
    p.decal(c.box(49.5, 42, 50.5, 52) & erode4(pup), CACTUS_HD, -2)
    for (x, y) in ((26, 30), (26, 40), (20, 34), (20, 44), (34, 34), (34, 44), (40, 30), (40, 40), (16, 40), (44, 40), (46, 46), (26, 50), (54, 50), (30, 27)):
        p.decal(c.circle(x, y, 0.9), BONE, 2)
    for (x0, y0, x1, y1) in ((14, 28, 10, 26), (46, 28, 50, 26), (12, 44, 8, 46), (46, 34, 50, 32), (18, 22, 16, 18), (57, 42, 60, 40)):
        p.decal(lmask(p, [(x0, y0), (x1, y1)]) & ~body & ~pup, BONE, 1, only_on=False)
    for (a, L) in ((22, 11), (158, 11), (60, 12.5), (120, 12.5), (90, 13.5)):
        petal = c.leaf(30, 22, a, L, 7.6, 0.0, tip_power=0.8)
        p.part(petal, FIRE, 'ray', base=0, sep=True, rim=False)
        dx, dy = math.cos(math.radians(a)), -math.sin(math.radians(a))
        p.decal(c.circle(30 + dx * L * 0.85, 22 + dy * L * 0.85, L * 0.3) & petal, FIRE, 1)
    p.part(c.ellipse(30, 21, 4.4, 3.0), YELLOW, 'ray', base=0, sep=True, rim=False)
    p.decal(c.circle(29, 20, 1.2), YELLOW, 3)


def star_lotus_hd(p):
    """The star lotus open on the night sea: five back petals, a seed head with its star, two front petals."""
    c = p.c
    teal, petal, seed, nebula = mat7(NEBULA_TEAL, 'matte'), mat7(R['starlight'], 'silk'), mat7(SEED_HEAD, 'matte'), mat7(NEBULA_MAGENTA, 'light')
    pad = c.ellipse(32, 51, 28, 7.6)
    p.part(pad, teal, 'ray', base=0, sep=False, rim=False)
    p.line([(32, 49), (54, 49)], teal, -2, 1.0)
    p.line([(18, 47), (30, 45)], teal, 1, 1.0)
    bx, by = 32.0, 46.0
    back = [(bx - 2, by, 128, 28, 13.6, -0.06), (bx + 2, by, 52, 28, 13.6, 0.06), (bx, by + 1, 90, 31, 15.4, 0.0)]
    side = [(bx - 2, by, 160, 25, 12.4, -0.12), (bx + 2, by, 20, 25, 12.4, 0.12)]
    for (x, y, a, L, W, b) in back + side:
        m = c.leaf(x, y, a, L, W, b, tip_power=0.7)
        p.part(m, petal, 'ray', base=0, sep=True, tex='cloth', axis=a, rim=False)
        dx, dy = math.cos(math.radians(a)), -math.sin(math.radians(a))
        p.decal(c.circle(x + dx * L * 0.9, y + dy * L * 0.9, L * 0.3) & m, petal, 2)
        p.line([(x + dx * 3, y + dy * 3), (x + dx * L * 0.7, y + dy * L * 0.7)], petal, -1, 1.0)
    head = c.ellipse(32, 33, 8.4, 4.8)
    p.part(head, seed, 'ray', base=0, sep=True, rim=False)
    for (x, y) in ((26, 32), (38, 32), (30, 30.5), (34, 30.5), (30, 34.5), (34, 34.5)):
        p.decal(c.circle(x, y, 1.0) & head, seed, -3)
    for (x, y, a) in ((30, 47, 116), (34, 47, 64)):
        m = c.leaf(x, y, a, 12.5, 10, 0.0, tip_power=0.7)
        p.part(m, petal, 'ray', base=0, sep=True, tex='cloth', axis=a, rim=False)
        p.decal(c.circle(x + math.cos(math.radians(a)) * 9, y - math.sin(math.radians(a)) * 9, 3.0) & m, petal, 2)
    # a nebula ripple on the water in front of the pad
    ripple = (c.ellipse(44, 57, 13, 2.4) | c.ellipse(18, 56.5, 7, 2.0)) & ~pad
    p.part(ripple, nebula, 'flat', base=0, sep=True, rim=False)
    p.decal(ripple & c.box(0, 0, 44, 64), nebula, 1)
    p.sparkle(32, 32, 2)
    p.sparkle(32, 7, 1)
    p.glow(STAR_GLOW, 0.6)




SPECIES_HD = {'willow_moss': willow_moss_hd, 'riverreed_ginseng': ginseng_hd, 'ember_pepper': pepper_hd, 'mist_lotus': mist_lotus_hd,
              'frost_lotus': frost_lotus_hd, 'cloudtop_orchid': orchid_hd, 'soulbell_flower': soulbell_hd, 'ember_cactus': cactus_hd,
              'star_lotus': lambda p, age: star_lotus_hd(p)}

HERBS_HD = [
    # id, species (SPECIES_HD), age (HERB_AGE in tools/data/items.py), grade (HERBS there), the spirit aura from Mystic up
    ('willow_moss', 'willow_moss', 10, 'plain', None),
    ('riverreed_ginseng_10', 'riverreed_ginseng', 10, 'common', None),
    ('riverreed_ginseng_100', 'riverreed_ginseng', 100, 'earth', None),
    ('riverreed_ginseng_1000', 'riverreed_ginseng', 1000, 'heaven', None),
    ('riverreed_ginseng_10000', 'riverreed_ginseng', 10000, 'mystic', '#CFF2E2'),
    ('ember_pepper', 'ember_pepper', 10, 'common', None),
    ('ember_pepper_100', 'ember_pepper', 100, 'earth', None),
    ('mist_lotus', 'mist_lotus', 10, 'earth', None),
    ('mist_lotus_100', 'mist_lotus', 100, 'heaven', None),
    ('frost_lotus', 'frost_lotus', 10, 'spirit', '#BFE2FF'),
    ('cloudtop_orchid', 'cloudtop_orchid', 10, 'heaven', None),
    ('cloudtop_orchid_100', 'cloudtop_orchid', 100, 'mystic', '#C8E2F1'),
    ('soulbell_flower', 'soulbell_flower', 10, 'heaven', None),
    ('soulbell_flower_100', 'soulbell_flower', 100, 'mystic', '#8AEBEE'),
    ('ember_cactus', 'ember_cactus', 10, 'sage', '#FFB45A'),
    ('star_lotus', 'star_lotus', 10, 'sovereign', None),   # its drawing carries the star glow
]


def make_herb_hd(species, age, grade, aura):
    def draw(p):
        SPECIES_HD[species](p, age)
        if aura:
            p.glow(aura, GLOW_STRENGTH[grade])
    return draw


# ----------------------------------------------------------------------------- seeds: the pouch and the seeds
def pouch_hd(p, stamp):
    """A hemp seed pouch tied with straw, a paper tag on it stamped in the herb's colour."""
    c = p.c
    bag = c.ellipse(24, 40, 15, 14.5) | c.poly([(14, 31), (34, 31), (30.5, 18), (17.5, 18)])
    p.part(bag, HEMP, 'sphere', base=0, sep=False, cx=19, cy=35, rx=20, ry=21, tex='cloth', axis=90)
    p.line([(20, 20), (18, 30)], HEMP, -2, 1.0)
    p.line([(28, 20), (30, 30)], HEMP, -2, 1.0)
    tie = c.box(13, 27.5, 35, 30.5) & dilate4(bag)
    p.part(tie, STRAW, 'ray_soft', base=0, sep=True, rim=False)
    p.part(c.circle(30, 29, 2.2), STRAW, 'sphere', base=0, sep=True, rim=False)
    p.part(c.taper((31, 30), (35, 33), (37, 38), 2.2, 1.2), STRAW, 'flat', base=0, sep=True, rim=False)
    p.part(c.ellipse(24, 16.5, 7.4, 3.2), HEMP, 'ray', base=0, sep=True, rim=False)
    tag = c.rrect(16.5, 36, 31.5, 50, 1.4)
    p.part(tag, PAPER, 'bevel', base=0, sep=True, hw=1, sw=1, tex='paper', rim=False)
    p.decal(c.circle(24, 43, 4.4) & tag, stamp, 0)
    p.decal(c.circle(22.8, 41.8, 1.3) & tag, stamp, 2)


def seed_moss(p):
    """Willow moss spores: a pinch of green dust on the leaf they were wrapped in."""
    c = p.c
    leaf_hd(p, 36, 55, 25, 22, 10.5, 0.06, 10, tip_power=0.7)
    for (x, y) in ((44, 50), (48, 52), (46, 54), (50, 49), (52, 53), (42, 53), (47, 48), (54, 51)):
        p.decal(c.circle(x, y, 0.8), MOSS, 1)


def seed_pepper(p):
    """Flat, pale pepper seeds."""
    c = p.c
    for (x, y, rx, ry) in ((45, 47, 4.0, 3.4), (54, 42, 3.4, 4.0), (51, 55, 4.1, 3.2)):
        m = c.ellipse(x, y, rx, ry)
        p.part(m, YELLOW, 'flat', base=1, sep=True, rim=False)
        p.decal(m & ~erode4(m) & c.box(x - 1, y - 1, 64, 64), YELLOW, -1)
        p.decal(c.circle(x + 0.4, y + 0.4, 1.0) & m, YELLOW, -1)


def seed_berry(p):
    """Red ginseng berries with the seed still inside."""
    c = p.c
    for (x, y) in ((45, 48), (54, 42), (52, 55)):
        m = c.circle(x, y, 3.6)
        p.part(m, BERRY, 'sphere', base=0, sep=True, spec=(x - 1.4, y - 1.4))
    p.part(c.taper((45, 45), (49, 40), (54, 38), 1.6, 1.2), LEAF, 'flat', base=-1, sep=True, rim=False)


def seed_lotus(p):
    """Pearl-white lotus seeds, a dark point on each."""
    c = p.c
    for (x, y, a) in ((45, 48, 70), (54, 42, 110), (52, 55, 60)):
        m = oval(c, x, y, 3.2, 4.4, a)
        p.part(m, PEARL, 'sphere', base=0, sep=True, spec=(x - 1.2, y - 1.6))
        dx, dy = math.cos(math.radians(a)), -math.sin(math.radians(a))
        p.decal(c.circle(x + dx * 3.6, y + dy * 3.6, 1.2) & m, PEARL, -2)


def oval(c, x, y, rx, ry, ang):
    """An ellipse whose long axis lies along `ang` (0 right, 90 up)."""
    ca, sa = math.cos(math.radians(ang)), -math.sin(math.radians(ang))
    pts = []
    for k in range(24):
        t = 2 * math.pi * k / 24.0
        u, v = ry * math.cos(t), rx * math.sin(t)
        pts.append((x + u * ca - v * sa, y + u * sa + v * ca))
    return c.poly(pts)


def seed_orchid(p):
    """Orchid seed finer than flour, sealed in beads of wax, a sky fleck showing through each."""
    c = p.c
    for (x, y) in ((45, 48), (54, 42), (52, 55)):
        m = c.circle(x, y, 3.8)
        p.part(m, WAX, 'sphere', base=0, sep=True, spec=(x - 1.4, y - 1.6))
        p.decal(c.circle(x + 0.6, y + 0.6, 1.4) & m, ICE_PETAL, 0)


def seed_soulbell(p):
    """Soulbell seeds: small violet bells that hum."""
    c = p.c
    for (x, y) in ((45, 47), (54, 41), (52, 54)):
        m = S.drop(c, x, y + 1, 3.0, 5.5)
        p.part(m, VIOLET, 'ray', base=0, sep=True, rim=False)
        p.decal(c.ellipse(x, y + 2.4, 1.8, 0.9) & m, QI, 2)


SEEDS_HD = [
    # id, the stamp on the tag, the seeds spilled beside the pouch
    ('willow_moss_seed', MOSS, seed_moss),
    ('ember_pepper_seed', YELLOW, seed_pepper),
    ('riverreed_ginseng_seed', BERRY, seed_berry),
    ('mist_lotus_seed', PEARL, seed_lotus),
    ('cloudtop_orchid_seed', ICE_PETAL, seed_orchid),
    ('soulbell_flower_seed', VIOLET, seed_soulbell),
]


def make_seed_hd(stamp, seeds):
    def draw(p):
        pouch_hd(p, stamp)
        seeds(p)
    return draw


# ----------------------------------------------------------------------------- garden materials
def spring_water_hd(p):
    """A stoppered bottle gourd of Qi-spring water (the pills' gourd with a wood plug and a hemp cord), beaded with
    cold, a faint cold light on it."""
    from families.pills import gourd_hd
    c = p.c
    gourd_hd(p, dict(body=STRAW, trim=WOODROOT, gem=None, lid='plug', cord='hemp', handles=False, stars=False, glow=None))
    for (x, y, r) in ((17, 44, 2.2), (36, 50, 2.0), (31, 38, 1.7), (22, 20, 1.5)):
        m = c.circle(x, y, r)
        p.part(m, CYAN, 'sphere', base=1, sep=True, rim=False)
        p.decal(c.circle(x - r * 0.4, y - r * 0.4, 0.7) & m, CYAN, 3)
    p.glow('#9FE6FF', 0.5)


def spirit_soil_hd(p):
    """A mound of black earth that remembers a spirit vein: jade veins threading it, a sprout breaking the crown."""
    c = p.c
    mound = c.ellipse(32, 44, 24, 13) | c.ellipse(30, 34, 15, 11)
    p.part(mound, SOIL, 'sphere', base=-1, sep=False, cx=24, cy=34, rx=28, ry=24, tex='clay', rim=False)
    for (fx, fy, r) in ((12, 44, 2.0), (26, 52, 1.8), (44, 48, 2.2), (36, 30, 1.4), (50, 40, 1.6), (20, 36, 1.5)):
        p.decal(c.circle(fx, fy, r) & mound, SOIL, -3)
    for pts in (((12, 46), (20, 40), (30, 43), (36, 38)), ((38, 50), (44, 44), (52, 46)), ((26, 30), (32, 34), (40, 32))):
        p.decal(c.polyline(pts, 1.6) & erode4(mound), M('jade'), 1)
        p.decal(c.polyline(pts, 0.8) & erode4(mound), M('jade'), 3)
    stem_hd(p, [(30, 26), (30, 18), (31, 12)], (2.4, 1.8))
    leaf_hd(p, 30, 16, 140, 11, 5.6, 0.0, 10)
    leaf_hd(p, 31, 14, 50, 11, 5.6, 0.0, 10)
    p.glow('#6FD9A0', 0.45)


def dyed_root_hd(p):
    """A carrot dyed ginseng-gold and combed into 'hairs' to pass for a hundred-year root, its orange showing where
    the dye ran out at the tip."""
    c = p.c
    root = c.poly([(24, 12), (40, 12), (44, 26), (39, 44), (34, 56), (30, 56), (23, 44), (20, 26)])
    p.part(root, PEPPER_YOUNG, 'ray', base=0, sep=False)
    for y in (20, 26, 32, 38, 44, 49):
        p.decal(lmask(p, [(21, y), (32, y + 1.2), (43, y)]) & erode4(root), PEPPER_YOUNG, -1)
    dye = c.poly([(23, 14), (41, 14), (44, 27), (38, 30), (41, 36), (30, 38), (24, 34), (21, 29)]) & root
    p.decal(dye, WAX, 0)
    p.decal(dye & (c.ellipse(28, 22, 5, 6) | c.ellipse(34, 30, 4, 3)), WAX, 1)
    p.decal(dye & ~erode4(dye) & c.box(0, 26, 64, 64), WAX, -2)
    for (a, b) in (((21, 24), (13, 22)), ((22, 30), (14, 33)), ((43, 22), (51, 20)), ((43, 30), (50, 34)), ((24, 40), (17, 45)), ((40, 40), (47, 45)), ((32, 56), (32, 59.5))):
        p.decal(lmask(p, [a, b]) & ~erode4(root), WAX, -1, only_on=False)
    stem_hd(p, [(32, 12), (32, 9), (33, 6)], (2.4, 1.8))
    leaf_hd(p, 32, 10, 145, 12, 5.6, 0.0, 10)
    leaf_hd(p, 33, 9, 40, 12, 5.6, 0.0, 10)


def rice_wine_hd(p):
    """A squat clay jar of cloudy rice wine: a red cloth over its mouth tied with straw, a paper label with a wine cup."""
    c = p.c
    jar = c.ellipse(31, 39, 19.5, 17.5) | c.box(22.5, 16, 39.5, 26)
    p.part(jar, CLAY, 'sphere', base=0, sep=False, cx=27, cy=34, rx=24, ry=22, tex='clay')
    p.part(c.box(20, 24, 42, 27.5) & dilate4(jar), CLAY, 'vgrad', base=-1, sep=True)
    cloth = c.ellipse(31, 15.5, 10.5, 5.2)
    p.part(cloth, M('red', 'silk'), 'ray', base=0, sep=True, rim=False)
    p.line([(24, 12), (30, 11), (37, 13)], M('red'), -1, 1.0)
    p.part(c.box(21, 17.5, 41, 20.5) & (cloth | jar), STRAW, 'flat', base=0, sep=True, rim=False)
    p.part(c.circle(38, 19, 2.0), STRAW, 'sphere', base=0, sep=True, rim=False)
    lab = c.rrect(22, 34, 40, 50, 1.4)
    p.part(lab, PAPER, 'bevel', base=0, sep=True, hw=1, sw=1, tex='paper', rim=False)
    cup = c.poly([(26, 38), (36, 38), (34, 44), (28, 44)]) | c.box(29.5, 44, 32.5, 46) | c.box(27.5, 46, 34.5, 47.5)
    p.decal(cup & lab, M('seal'), -1)
    p.decal(c.box(27.5, 39, 34.5, 40) & lab, M('seal'), 1)


MATERIALS_HD = [('spring_water', spring_water_hd), ('spirit_soil', spirit_soil_hd), ('dyed_root', dyed_root_hd), ('rice_wine', rice_wine_hd)]

for _id, _draw in ([(i, make_herb_hd(sp, age, grade, aura)) for i, sp, age, grade, aura in HERBS_HD]
                   + [(i, make_seed_hd(stamp, seeds)) for i, stamp, seeds in SEEDS_HD] + MATERIALS_HD):
    register(FAM, _id, _draw, GROUP)
    hd(_id, _draw)
