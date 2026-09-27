"""Food (HD, Style A): every dish, brew and remedy at 64 art px, shown 1:1 in the 76 px slot, with a native @32 render
for the HUD item ring and the small slots.

A dish is its vessel and what is in it, with steam rising and a gloss on the liquid: a tea in a wide cup on its
saucer, a soup or congee in a footed bowl, a stew in a lidless wooden pot with ring handles, a rice ball or dumplings
on a plate, the roast fish on its bamboo skewer, the salve in its bronze tin, the cactus water in a clay gourd. The
vessels are shared templates (`cup_hd`, `bowl_hd`, `plate_hd`, `pot_hd`) and each dish draws its contents on them.
The grade is the ware, form and trim, never colour alone (WARE_HD, after the pills' ladder): a plain dish is served
in bare earthenware; Common in earthenware with a bronze band and lip; Earth in white porcelain with jade; Heaven in
skyware with silver; Spirit in storm glaze with silver and Sage in sand glaze with gold, both with their aura (a pot
takes the grade's metal for its handles and band). Every icon comes from one table (FOOD_HD).
"""
import math

import numpy as np

from pix import Ramp, WHITE, dilate4, erode4
from palette import M, TEX, kit, mat7
from registry import hd, register
import shapes as S
from families.beast_parts import GRADE_HD, XY, lmask
from families.fish import fish_hd
from families.herbs import leaf_hd

FAM, GROUP = 'items', 'food'
ART = 64   # HD (tools/icons/README.md, "How to convert a family")


# ============================================================================= materials
CLAY, BRONZE, PORCELAIN, JADE, SILVER, GOLD, DARKWOOD, BAMBOO, IRON = (M('clay'), M('bronze'), M('porcelain'), M('jade'), M('silver'), M('gold'),
                                                                     M('darkwood'), M('bamboo'), M('iron'))
MIST, PAPER, RICE, BROTH, TEA, LEAF, MOSS, PINK, LOTUS, YELLOW, WAX, BONE, OIL, FIRE, RED, EMBER, EARTH, CLOUD, VIOLET, STORM, SAND, WOOD, STRAW = (
    M('mist'), M('paper'), M('rice', 'porcelain'), M('broth', 'glass'), M('tea', 'glass'), M('leaf'), M('moss', 'glass'), M('pink', 'porcelain'),
    M('lotuspink', 'glass'), M('yellow', 'glass'), M('wax', 'porcelain'), M('bone', 'porcelain'), M('oil', 'glass'), M('fire', 'glass'), M('red'),
    M('ember', 'porcelain'), M('earth'), M('cloud', 'silk'), M('violet'), M('storm', 'glass'), M('sand'), M('wood'), M('straw'))
NORI = mat7(Ramp(['#0A1A14', '#12281E', '#1E3C2C', '#2E5A40', '#4A7A58'], '#050D0A'), 'matte')
CACTUS_WATER = mat7(Ramp(['#3A6A50', '#62987A', '#9ED0A8', '#CDEFCF', '#F2FFF2'], '#13261C'), 'glass')
FLESH_SLICE = mat7(Ramp(['#8A4A42', '#C07868', '#E8A896', '#F6CDBE', '#FFF0E8'], '#3A1A16'), 'porcelain')
BOLT = '#F4FBFF'

# The ware by grade: the vessel's body, its trim (bands, lip, foot; the pot's metal) and the aura from Mystic up.
WARE_HD = {
    'plain': dict(body=CLAY, trim=None, glow=None),
    'common': dict(body=CLAY, trim=BRONZE, glow=None),
    'earth': dict(body=PORCELAIN, trim=JADE, glow=None),
    'heaven': dict(body=M('sky', 'porcelain'), trim=SILVER, glow=None),
    'mystic': dict(body=M('mistjade'), trim=GOLD, glow=kit('mystic')['glow']),
    'spirit': dict(body=M('storm', 'porcelain'), trim=SILVER, glow=kit('spirit')['glow']),
    'sage': dict(body=M('sand', 'porcelain'), trim=GOLD, glow=kit('sage')['glow']),
}


def _tex(mat):
    return TEX.get(mat.kind)


# ============================================================================= the vessels
def steam_hd(p, xs, y0, h, mat=None, lv=(1, 2)):
    """Steam: wisps rising from y0 to y0 - h at each x, swaying as they climb, thinning at the top."""
    c = p.c
    mat = mat or MIST
    for k, x in enumerate(xs):
        pts = [(x + 2.4 * math.sin((y - y0) / 3.4 + k * 1.7), y) for y in np.arange(y0, y0 - h, -1.0)]
        m = c.polyline(pts[:int(len(pts) * 0.55)], 2.0) | c.polyline(pts[int(len(pts) * 0.55) - 1:], 1.4)
        p.part(m & ~c.a, mat, 'flat', base=lv[k % len(lv)], sep=False, rim=False)


def gloss_hd(p, inner, mat, x, y, rx, ry):
    """The light on a liquid: a bright ellipse toward the lit side."""
    p.decal(p.c.ellipse(x, y, rx, ry) & inner, mat, 3)


def lip_hd(p, w, ring, body):
    """The vessel's lip: the trim material's line on the rim (or the body's own light)."""
    if w['trim'] is not None:
        p.part(ring, w['trim'], 'flat', base=1, sep=False, rim=False, tex=_tex(w['trim']))
    else:
        p.decal(ring & body, w['body'], 2)


def bowl_hd(p, w, soup, cy=30, rx=22, depth=21):
    """A footed bowl: the foot, the body, the grade's band and lip, the rim and the soup inside with its meniscus."""
    c = p.c
    body_mat = w['body']
    tex = _tex(body_mat)
    foot = c.box(21, cy + depth - 2.5, 43, cy + depth + 2.2)
    p.part(foot, w['trim'] or body_mat, 'ray', base=-1, sep=False, rim=False, tex=_tex(w['trim'] or body_mat))
    body = c.ellipse(32, cy, rx, depth) & c.box(0, cy, 64, 64)
    p.part(body, body_mat, 'sphere', base=0, sep=True, cx=25, cy=cy - 2, rx=rx + 4, ry=depth + 6, tex=tex)
    if w['trim'] is not None:
        band = c.box(0, cy + 9, 64, cy + 12.5) & body
        p.part(band, w['trim'], 'hgrad', base=0, sep=True, rim=False, tex=_tex(w['trim']))
    rim = c.ellipse(32, cy, rx, 7.2)
    p.part(rim, body_mat, 'ray_soft', base=1, sep=True, tex=tex)
    lip_hd(p, w, c.ring(32, cy, rx, 1.6, 7.2), rim)
    inner = c.ellipse(32, cy + 0.5, rx - 2.4, 5.2)
    p.part(inner, soup, 'ray_soft', base=0, sep=True, rim=False)
    p.decal(c.ellipse(32, cy - 0.8, rx - 2.4, 3.4) & inner, soup, 1)
    gloss_hd(p, inner, soup, 24, cy - 0.5, 5.5, 1.3)
    return inner


def cup_hd(p, w, tea, y0=27, y1=50, hw=18):
    """A wide tea cup on its saucer: the saucer, the tapering body, the grade's band and lip, the tea inside."""
    c = p.c
    body_mat = w['body']
    tex = _tex(body_mat)
    saucer = c.ellipse(32, y1 + 2, 25, 5.5)
    p.part(saucer, body_mat, 'ray_soft', base=-1, sep=False, tex=tex)
    lip_hd(p, w, c.ring(32, y1 + 2, 25, 1.4, 5.5), saucer)
    body = c.poly([(32 - hw, y0), (32 + hw, y0), (32 + hw - 0.5, y0 + 7), (32 + hw - 4, y1 - 5), (32 + hw - 9, y1 - 1),
                   (32 - hw + 9, y1 - 1), (32 - hw + 4, y1 - 5), (32 - hw + 0.5, y0 + 7)])
    body |= c.box(32 - 7, y1 - 3, 32 + 7, y1 + 0.5)
    p.part(body, body_mat, 'ray', base=0, sep=True, tex=tex)
    if w['trim'] is not None:
        band = c.box(0, y0 + 7.5, 64, y0 + 10) & body
        p.part(band, w['trim'], 'hgrad', base=0, sep=True, rim=False, tex=_tex(w['trim']))
    rim = c.ellipse(32, y0, hw, 5.4)
    p.part(rim, body_mat, 'ray_soft', base=1, sep=True, tex=tex)
    lip_hd(p, w, c.ring(32, y0, hw, 1.4, 5.4), rim)
    inner = c.ellipse(32, y0 + 0.4, hw - 2.2, 3.8)
    p.part(inner, tea, 'ray_soft', base=0, sep=True, rim=False)
    p.decal(c.ellipse(32, y0 - 0.6, hw - 2.2, 2.4) & inner, tea, 1)
    gloss_hd(p, inner, tea, 26, y0 - 0.2, 4.5, 1.0)
    return inner


def plate_hd(p, w, cy=47, rx=25, ry=7.5):
    """A plate seen from a little above: the underside, the rim with the grade's line, the well."""
    c = p.c
    body_mat = w['body']
    tex = _tex(body_mat)
    under = c.ellipse(32, cy + 2, rx - 1, ry)
    p.part(under, body_mat, 'flat', base=-2, sep=False, rim=False)
    top = c.ellipse(32, cy, rx, ry)
    p.part(top, body_mat, 'ray', base=1, sep=True, tex=tex)
    lip_hd(p, w, c.ring(32, cy, rx, 1.4, ry), top)
    well = c.ellipse(32, cy, rx - 4.5, ry - 3)
    p.part(well, body_mat, 'flat', base=0, sep=True, rim=False)
    return well


def pot_hd(p, w, stew, cy=31, rx=21, depth=20):
    """A lidless wooden pot: the turned body with its grain, ring handles and a band in the grade's metal, the stew."""
    c = p.c
    metal = w['trim'] or IRON
    mtex = _tex(metal)
    for x in (9, 55):
        p.part(c.ring(x, cy + 5, 4.8, 2.2), metal, 'ray_soft', base=0, sep=False, tex=mtex)
    body = c.ellipse(32, cy, rx, depth) & c.box(0, cy, 64, 64)
    p.part(body, DARKWOOD, 'sphere', base=0, sep=True, cx=26, cy=cy - 2, rx=rx + 4, ry=depth + 6, tex='wood', axis=0)
    band = c.box(0, cy + 8, 64, cy + 11.5) & body
    p.part(band, metal, 'hgrad', base=0, sep=True, rim=False, tex=mtex)
    rim = c.ellipse(32, cy, rx, 7.0)
    p.part(rim, DARKWOOD, 'ray_soft', base=1, sep=True, tex='wood', axis=0)
    p.part(c.ring(32, cy, rx, 1.8, 7.0), metal, 'flat', base=1, sep=False, rim=False, tex=mtex)
    inner = c.ellipse(32, cy + 0.5, rx - 2.6, 5.0)
    p.part(inner, stew, 'ray_soft', base=0, sep=True, rim=False)
    p.decal(c.ellipse(32, cy - 0.8, rx - 2.6, 3.2) & inner, stew, 1)
    gloss_hd(p, inner, stew, 24, cy - 0.5, 5, 1.2)
    return inner


def blossom_hd(p, x, y, r, petal, centre, n=5):
    """A small flower: `n` round petals about a centre."""
    c = p.c
    for k in range(n):
        a = math.radians(90 + k * 360.0 / n)
        p.part(c.circle(x + math.cos(a) * r * 0.62, y - math.sin(a) * r * 0.62, r * 0.42), petal, 'sphere', base=0, sep=True, rim=False)
    p.part(c.circle(x, y, r * 0.28), centre, 'sphere', base=1, sep=True, rim=False)


# ============================================================================= the dishes
def herbal_tea_hd(p, w):
    """Willow-moss tea in a wide cup: the green brew, a moss leaf floating, steam."""
    cup_hd(p, w, TEA)
    leaf_hd(p, 22, 28.5, 12, 15, 6, bend=0.05, mat=LEAF)
    steam_hd(p, (22, 32, 42), 21, 15)


def lotus_root_tea_hd(p, w):
    """Lotus-root tea: the pink brew, a slice of lotus root with its holes leaning on the rim, steam."""
    c = p.c
    cup_hd(p, w, LOTUS)
    sl = c.circle(47, 20, 9.5)
    p.part(sl, WAX, 'ray', base=0, sep=True, rim=False)
    for (dx, dy) in ((-3.8, -2.6), (2.6, -3.8), (4.2, 2.2), (-2.6, 4.2), (0, 0), (-4.6, 1.4), (2.0, -0.4)):
        p.decal(c.circle(47 + dx, 20 + dy, 1.6) & sl, WAX, -2)
        p.decal(c.circle(47 + dx + 0.5, 20 + dy + 0.5, 0.8) & sl, WAX, -3)
    p.decal(S.outline_only(sl) & sl, LOTUS, 0)
    steam_hd(p, (18, 28), 21, 14)


def jasmine_dew_tea_hd(p, w):
    """Stoneford's jasmine: the pale gold brew, a white blossom on the saucer's edge, steam."""
    cup_hd(p, w, YELLOW)
    blossom_hd(p, 51, 47, 7.5, RICE, YELLOW)
    steam_hd(p, (20, 30, 40), 21, 14)


def marsh_mist_tea_hd(p, w):
    """Greyreed's grey-green tea in a plain cup, a reed leaf laid across it, thin steam."""
    cup_hd(p, w, MOSS)
    leaf_hd(p, 9, 24, 20, 36, 4.4, bend=0.06, mat=LEAF)
    steam_hd(p, (22, 34, 44), 21, 13, lv=(0, 1))


def thunderhead_tea_hd(p, w):
    """A Cloudgate brew, dark as a storm, a little bolt of light standing over the cup."""
    c = p.c
    cup_hd(p, w, STORM)
    bolt = c.poly([(38, 5), (28, 18), (33.5, 18), (26, 27), (42, 15), (36, 15), (42, 5)])
    p.part(bolt, YELLOW, 'flat', base=1, sep=True, rim=False)
    p.decal(bolt & ~erode4(bolt) & (XY(p)[0] + XY(p)[1] < 48), YELLOW, 3)
    p.decal(c.poly([(35.5, 8), (31, 15), (33, 15)]) & bolt, BOLT, 0)


def rice_ball_hd(p, w):
    """A rice ball on a plate: the pressed triangle of rice, a band of nori round its foot, sesame on top."""
    c = p.c
    plate_hd(p, w, cy=50)
    ball = c.poly([(32, 9), (52, 44), (48, 50), (16, 50), (12, 44)]) & c.ellipse(32, 34, 24, 24) | c.ellipse(32, 44, 19, 8)
    p.part(ball, RICE, 'ray', base=0, sep=True)
    X, Y = XY(p)
    grain = erode4(ball) & ((np.floor(X / 2) + np.floor(Y / 2)) % 2 == 0) & ((np.floor(X * 3 + Y) % 5) == 0)
    p.decal(grain, RICE, -1)
    p.decal(erode4(ball) & ((np.floor(X * 2 + Y * 3) % 7) == 0) & (X + Y < 60), RICE, 2)
    wrap = c.box(19, 36, 45, 50) & ball
    p.part(wrap, NORI, 'ray', base=0, sep=True, rim=False)
    p.decal(erode4(wrap) & ((np.floor(X / 3) + np.floor(Y / 3)) % 2 == 0), NORI, -1)
    for (x, y) in ((27, 40), (36, 44), (23, 46)):
        p.decal(c.box(x, y, x + 1.5, y + 1), STRAW, 2)
    for (x, y) in ((28, 22), (36, 26), (24, 30), (40, 34), (31, 32)):
        p.decal(c.box(x, y, x + 1.5, y + 1), NORI, 0)


def toad_oil_dumplings_hd(p, w):
    """Three dumplings on a plate, their pleats crimped along the top, a bead of toad oil beside them, steam."""
    c = p.c
    plate_hd(p, w, cy=48)
    for (x, y, base) in ((20, 39, 0), (44, 39, 0), (32, 45, 1)):
        d = (c.ellipse(x, y, 11, 8.5) & c.box(0, 0, 64, y + 4.5)) | c.ellipse(x, y + 3, 11, 3.4)
        p.part(d, BROTH, 'sphere', base=base, sep=True, cx=x - 4, cy=y - 5, rx=13, ry=12)
        for k in (-5, -1.5, 2, 5.5):
            p.decal(lmask(p, [(x + k, y - 7.5), (x + k + 1, y - 3.5)]) & erode4(d), BROTH, -2)
            p.decal(lmask(p, [(x + k + 1.2, y - 7.5), (x + k + 2.2, y - 3.5)]) & erode4(d), BROTH, 2)
        p.decal(c.ellipse(x - 5, y - 4.5, 3, 1.3) & d, BROTH, 3)
    p.part(c.ellipse(53, 50, 4, 2), OIL, 'ray_soft', base=1, sep=True, rim=False)
    p.decal(c.ellipse(52, 49.5, 1.4, 0.7), OIL, 3)
    steam_hd(p, (22, 42), 29, 13)


def riverfish_soup_hd(p, w):
    """A milky riverfish soup in a bowl: pale slices of fish and a few leaf bits floating, steam."""
    c = p.c
    inner = bowl_hd(p, w, RICE)
    for (x, y) in ((22, 31), (38, 30), (30, 33)):
        s = c.ellipse(x, y, 6, 2.6) & inner
        p.part(s, FLESH_SLICE, 'ray_soft', base=0, sep=True, rim=False)
        p.decal(lmask(p, [(x - 3, y), (x + 3, y)]) & s, FLESH_SLICE, -2)
    for (x, y) in ((30, 30), (44, 32), (16, 32), (34, 34.5)):
        p.decal(c.box(x, y, x + 2, y + 1.2) & inner, LEAF, 0)
    steam_hd(p, (22, 32, 42), 23, 17)


def boar_bone_broth_hd(p, w):
    """Boar bone broth in an earthenware bowl: the bone standing out of the brown broth, oil beads on it, steam."""
    c = p.c
    bone = c.seg(37, 33, 50, 14, 5.2) | c.circle(48, 12.5, 3.6) | c.circle(53, 16, 3.6)
    p.part(bone, BONE, 'ray', base=0, sep=True, tex='metal')
    p.decal(lmask(p, [(39, 30), (49, 16)]) & erode4(bone), BONE, -1)
    inner = bowl_hd(p, w, BROTH)
    p.part(c.seg(37, 33, 41, 27, 5.2) & dilate4(inner), BONE, 'ray', base=0, sep=True, tex='metal')
    for (x, y) in ((20, 31), (26, 29.5), (44, 32), (34, 34)):
        p.decal(c.ellipse(x, y, 1.6, 0.9) & inner, OIL, 3)
    p.decal(c.box(15, 32, 18, 33.2) & inner, LEAF, 0)
    steam_hd(p, (18, 28), 23, 15)


def ember_pepper_broth_hd(p, w):
    """A spicy broth: red-orange and glossy, pepper rings floating, a leaf, steam with the heat in it."""
    c = p.c
    inner = bowl_hd(p, w, FIRE)
    for (x, y) in ((21, 31), (37, 30), (45, 32.5)):
        ring = c.ring(x, y, 3.6, 1.6, 2.2) & inner
        p.part(ring, RED, 'flat', base=0, sep=True, rim=False)
        p.decal(c.arc(x, y, 3.6, 1.0, 100, 200, 2.2) & ring, RED, 2)
    for (x, y) in ((29, 32), (14, 32)):
        p.decal(c.box(x, y, x + 2.5, y + 1.2) & inner, LEAF, 0)
    steam_hd(p, (22, 32, 42), 23, 16, FIRE, lv=(2, 3))


def cloudtop_orchid_broth_hd(p, w):
    """A clear mist-pale broth with a cloud orchid opened on it, its violet heart, steam."""
    c = p.c
    inner = bowl_hd(p, w, MIST)
    for a in (55, 145, 235, 325):
        petal = c.leaf(32, 30, a, 9.5, 6.5, 0) & dilate4(dilate4(inner))
        p.part(petal, CLOUD, 'ray', base=1, sep=True, rim=False)
        p.decal(lmask(p, [(32, 30), (32 + math.cos(math.radians(a)) * 7, 30 - math.sin(math.radians(a)) * 7)]) & erode4(petal), CLOUD, -1)
    p.part(c.circle(32, 30, 2.6), VIOLET, 'sphere', base=0, sep=True, rim=False)
    steam_hd(p, (18, 46), 23, 15)


def jade_carp_congee_hd(p, w):
    """Jade carp congee: thick white rice, jade-green slices of carp and shreds of ginger on top, steam."""
    c = p.c
    inner = bowl_hd(p, w, RICE)
    for (x, y) in ((22, 30.5), (36, 31.5), (44, 29.5)):
        s = c.ellipse(x, y, 5.4, 2.4) & inner
        p.part(s, JADE, 'ray_soft', base=0, sep=True, rim=False, tex='jade')
        p.decal(lmask(p, [(x - 2.5, y - 0.5), (x + 2.5, y + 0.5)]) & s, JADE, -2)
    for (x, y) in ((29, 29.5), (16, 32), (39, 34)):
        p.decal(c.box(x, y, x + 3, y + 1.2) & inner, YELLOW, 1)
    steam_hd(p, (24, 36), 23, 16)


def ember_pepper_stew_hd(p, w):
    """Ember pepper stew in a wooden pot: whole fire peppers and greens in the red stew, pale steam."""
    c = p.c
    inner = pot_hd(p, w, EMBER)
    for (x, y, r, mat) in ((20, 31, 4.0, FIRE), (37, 29.5, 3.6, FIRE), (30, 33, 2.8, LEAF), (45, 32.5, 2.6, LEAF)):
        m = c.circle(x, y, r) & dilate4(inner)
        p.part(m, mat, 'sphere', base=0, sep=True, rim=False, cx=x - r * 0.3, cy=y - r * 0.3, rx=r * 1.2, ry=r * 1.2)
    steam_hd(p, (18, 30, 44), 23, 16, PAPER)


def thunderhorn_stew_hd(p, w):
    """Thunderhorn stew: chunks of meat in the broth, a horn standing out of the pot, a spark of the beast's charge."""
    c = p.c
    inner = pot_hd(p, w, BROTH)
    for (x, y, r) in ((20, 31, 4.2), (34, 32.5, 3.8), (45, 29.5, 3.4)):
        m = c.circle(x, y, r) & dilate4(inner)
        p.part(m, EARTH, 'sphere', base=0, sep=True, rim=False, cx=x - r * 0.3, cy=y - r * 0.3, rx=r * 1.2, ry=r * 1.2)
    horn = c.taper((27, 30), (34, 20), (43, 8), 7.5, 1.4)
    p.part(horn, BONE, 'ray', base=0, sep=True, tex='metal')
    p.decal(lmask(p, S.curve_pts((28, 29), (34, 21), (42, 9), 12)) & erode4(horn), BONE, -1)
    p.decal(c.circle(29, 29, 2.6) & horn, STORM, 0)
    bolt = c.polyline([(50, 8), (46, 16), (51, 18), (47, 26)], 1.8)
    p.part(bolt & ~c.a, YELLOW, 'flat', base=2, sep=True, rim=False)
    p.decal(bolt, BOLT, 0)
    steam_hd(p, (16, 54), 23, 14, PAPER)


def roast_fish_hd(p, w):
    """A river fish roasted on a bamboo skewer, its skin browned and charred in bands, a wisp of smoke."""
    c = p.c
    stick = c.seg(8, 58, 56, 8, 3.4)
    p.part(stick, BAMBOO, 'ray_soft', base=0, sep=False, tex='wood', axis=46)
    for t in (0.3, 0.55, 0.8):
        x, y = 8 + 48 * t, 58 - 50 * t
        p.decal(lmask(p, [(x - 1.2, y - 1.4), (x + 1.4, y + 1.2)]) & stick, BAMBOO, -2)
    bodym, A = fish_hd(p, GRADE_HD['plain'], L=40, H=19, angle=46, cx=33, cy=31, body=BROTH, belly=SAND, fin=EARTH, tail=10,
                       dorsal=(0.0, 0.34, 0.5), scales=False, lateral=False, eye=WAX, loop=False)
    inner = erode4(bodym)
    for k in range(-2, 3):
        x0, y0 = A.p(k * 6.5 + 2, 8)
        x1, y1 = A.p(k * 6.5 - 2, -8)
        p.decal(c.seg(x0, y0, x1, y1, 1.8) & inner, EARTH, -3)
        p.decal(c.seg(x0 + 1.5, y0 + 1, x1 + 1.5, y1 + 1, 1.0) & inner, BROTH, 2)
    tip = c.seg(47, 17, 56, 8, 3.4) & ~bodym
    p.part(tip, BAMBOO, 'ray_soft', base=0, sep=True, tex='wood', axis=46)
    steam_hd(p, (14, 22), 20, 12, MIST, lv=(0, 1))


def willow_salve_hd(p, w):
    """A round bronze tin of willow salve, its lid leaning open against it, the green salve inside, a willow leaf."""
    c = p.c
    lid = c.ellipse(52, 36, 6.2, 17)
    p.part(lid, BRONZE, 'ray', base=0, sep=False, tex='metal')
    p.decal(c.ellipse(52.5, 36, 2.4, 10) & lid, BRONZE, 2)
    p.decal(c.ring(52, 36, 6.2, 1.2, 17) & lid & (XY(p)[0] > 52), BRONZE, -2)
    body = (c.ellipse(26, 44, 20.5, 12.5) & c.box(0, 38, 64, 64)) | c.box(5.5, 38, 46.5, 44)
    p.part(body, BRONZE, 'sphere', base=0, sep=True, cx=22, cy=38, rx=24, ry=18, tex='metal')
    top = c.ellipse(26, 38, 20.5, 6.4)
    p.part(top, BRONZE, 'ray_soft', base=1, sep=True, tex='metal')
    p.decal(c.ring(26, 38, 20.5, 1.2, 6.4) & top, BRONZE, 2)
    salve = c.ellipse(26, 38.4, 17.6, 4.6)
    p.part(salve, MOSS, 'ray_soft', base=0, sep=True, rim=False)
    p.decal(c.ellipse(20, 37.2, 6, 1.6) & salve, MOSS, 3)
    p.decal(c.box(8, 48, 44, 49.5) & body, BRONZE, -2)
    leaf_hd(p, 14, 54, 22, 17, 6, bend=0.1, mat=LEAF)
    leaf_hd(p, 38, 22, 150, 14, 5, bend=-0.1, mat=LEAF)


def cactus_water_hd(p, w):
    """A clay gourd of pale green cactus water, the stopper pulled and leaning on the lip, an ember-cactus flower
    tied at its waist with the grade's cord."""
    c = p.c
    low = c.circle(29, 45, 14.6)
    up = c.circle(29, 26.5, 8.4)
    waist = c.box(24, 30, 34, 35)
    p.part(low, CLAY, 'sphere', base=0, sep=False, cx=25, cy=40, rx=17, ry=17, tex='clay')
    p.part(up | waist, CLAY, 'sphere', base=0, sep=True, cx=27, cy=25, rx=10, ry=10, tex='clay')
    neck = c.box(24, 14, 34, 20)
    p.part(neck, CLAY, 'ray', base=0, sep=True, tex='clay')
    lip = c.ellipse(29, 13, 7.6, 3.6)
    p.part(lip, CLAY, 'ray', base=1, sep=True)
    mouth = c.ellipse(29, 12.8, 5.2, 2.2)
    p.part(mouth, CACTUS_WATER, 'flat', base=0, sep=True, rim=False)
    p.decal(mouth & c.box(0, 0, 29, 13), CACTUS_WATER, 2)
    p.decal(c.arc(29, 36, 14.6, 1.4, 200, 340) & erode4(low), CLAY, -2)
    p.decal(c.ellipse(22, 39, 3.4, 2.2) & low, CLAY, 3)
    p.decal(c.ellipse(25, 23, 2, 1.4) & up, CLAY, 3)
    plug = c.seg(38, 13, 43, 7, 6)
    p.part(plug, WOOD, 'ray', base=0, sep=True, tex='wood', axis=50)
    cord = w['trim'] is not None and M('red', 'silk') or STRAW
    cord_band = c.box(20, 31.5, 38, 34) & dilate4(up | low | waist)
    p.part(cord_band, cord, 'ray_soft', base=0, sep=True, rim=False)
    tail = c.taper((38, 33), (44, 39), (42, 50), 2.6, 1.4)
    p.part(tail, cord, 'flat', base=0, sep=True, rim=False)
    fl = c.empty()
    for a in (20, 92, 164, 236, 308):
        fl |= c.leaf(42, 30.5, a, 7.2, 5.2, 0.0, tip_power=0.8)
    p.part(fl, FIRE, 'ray', base=0, sep=True, rim=False)
    p.decal(c.circle(42, 30.5, 1.6), YELLOW, 3)
    if w['trim'] is not None:
        p.part(c.circle(38.5, 32.8, 2.0), w['trim'], 'sphere', base=0, sep=True, tex='metal')
    p.sparkle(50, 22, 1)


# ============================================================================= the table
FOOD_HD = [
    # id, grade (items.py), the drawing on the grade's ware
    ('herbal_tea', 'plain', herbal_tea_hd),
    ('rice_ball', 'plain', rice_ball_hd),
    ('riverfish_soup', 'plain', riverfish_soup_hd),
    ('boar_bone_broth', 'plain', boar_bone_broth_hd),
    ('ember_pepper_stew', 'common', ember_pepper_stew_hd),
    ('lotus_root_tea', 'earth', lotus_root_tea_hd),
    ('toad_oil_dumplings', 'plain', toad_oil_dumplings_hd),
    ('cloudtop_orchid_broth', 'heaven', cloudtop_orchid_broth_hd),
    ('jade_carp_congee', 'earth', jade_carp_congee_hd),
    ('roast_fish', 'plain', roast_fish_hd),
    ('ember_pepper_broth', 'common', ember_pepper_broth_hd),
    ('willow_salve', 'plain', willow_salve_hd),
    ('thunderhorn_stew', 'spirit', thunderhorn_stew_hd),
    ('cactus_water', 'sage', cactus_water_hd),
    ('jasmine_dew_tea', 'common', jasmine_dew_tea_hd),
    ('marsh_mist_tea', 'common', marsh_mist_tea_hd),
    ('thunderhead_tea', 'earth', thunderhead_tea_hd),
]


def make_dish_hd(grade, draw):
    """A dish's drawing `draw(p, w)` on its grade's ware, with the aura from Mystic up."""
    w = WARE_HD[grade]

    def hd_draw(p):
        draw(p, w)
        if w['glow'] is not None:
            p.glow(w['glow'][0], w['glow'][1])
    return hd_draw


for _id, _grade, _draw in FOOD_HD:
    _fn = make_dish_hd(_grade, _draw)
    register(FAM, _id, _fn, GROUP)
    hd(_id, _fn)
