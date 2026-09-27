"""Treasures (HD, Style A): the deployable treasures (bells, pagoda, mirror, seal, cauldron, banner, sealing gourd,
sword array), the throwables, the two talisman treasures, the flight vessels, the Heavenly Flames and the furnace
ladder, at 64 art px shown 1:1 in the 76 px slot, with a native @32 render for the HUD treasure ring and the small
slots.

Each treasure is the object the item is, drawn once in icon space on the shared builders: the upright temple bell
(`bell_hd`), the three-legged vessel (`ding_hd`: a cauldron, a curio, the furnaces), the paper talisman strip
(`talisman_hd`), the Heavenly Flame on its dish (`flame_hd`), the furnace on a grade's kit (`furnace_hd`). The grade
is form and trim from `palette.kit`, never colour alone: a plain iron bell against a bronze temple bell set with jade
studs; jade trims at Earth, silver at Heaven, gold at Mystic; a furnace's walls in the grade's metal with the grade's
work round the belly (a jade inlay, silver clouds, gold runes, a lightning zigzag, desert-glass beads, driftglass
diamonds, star dots) and its jewel as the lid's finial. The aura is stepped glow bands from Mystic up, in the object's
own light (a wisp's cyan, a flame's colour, the kit's glow).
"""
import math

import numpy as np

from pix import BANDS, Frame, Ramp, WHITE, dilate4, erode4
from palette import GLOW_STRENGTH, M, mat7
from registry import hd, register
import shapes as S
from families.weapons import K, blade_hd, fitting_hd, gem_hd, grip_hd, leaf_blade_hd, ttex, work_hd
from families import pills

FAM = 'items'
ART = 64   # HD (tools/icons/README.md, "How to convert a family")

IRON, BRONZE, GOLD, SILVER, JADE, DARKWOOD, STONE, PAPER, HEMP, INKM = (M('iron'), M('bronze'), M('gold'), M('silver'), M('jade'), M('darkwood'),
                                                                        M('stone'), M('paper'), M('hemp'), M('ink'))
RED, INDIGO, CLOUD, SKY, QI, FIRE, EMBER, YELLOW, COPPER, TALISMAN = (M('red', 'silk'), M('indigo', 'silk'), M('cloud', 'porcelain'), M('sky', 'porcelain'),
                                                                     M('qi', 'light'), M('fire'), M('ember'), M('yellow'), M('copper'), M('talisman'))
LACQUER = M('red', 'porcelain')                  # red lacquer: a wet sheen and the rim light
VIOLET_GLASS = M('violet', 'glass')              # the sealing gourd
MIRROR = mat7(Ramp(['#16464F', '#2C7C86', '#62C0C4', '#B8EDEA', '#F4FFFF'], '#0B2129'), 'glass')
SEAL_RED = M('seal', 'gem')
LANTERN = M('lanternbronze')
CYL = BANDS['cylinder']


def XY(p):
    """Pixel centres in icon space."""
    return p.c.X / p.s, p.c.Y / p.s


def finish(p, grade, col=None):
    """The aura from Mystic up, in `col` (the object's own light) or the kit's glow, at the grade's strength."""
    g = K(grade)
    if g['glow']:
        p.glow(col or g['glow'][0], g['glow'][1])


# ============================================================================= the shared builders
def bell_hd(p, mat, top, bottom, hw_top, hw_bot, power=1.7, tex=None):
    """An upright bell's body from its rounded shoulder to its lip: the skirt flares out to `hw_bot`, lit from the
    left across its curve. Returns the mask and the half-width per row."""
    c = p.c
    X, Y = XY(p)
    u = np.clip((Y - top) / float(bottom - top), 0.0, 1.0)
    hw = hw_top + (hw_bot - hw_top) * u ** power
    m = ((Y >= top) & (Y < bottom) & (np.abs(X - 32.0) <= hw)) | (c.ellipse(32, top, hw_top, hw_top * 0.5) & (Y < top))
    f = ((X - 32.0) + hw) / np.maximum(2.0 * hw, 1e-3)
    p.part(m, mat, 'field', field=f, bands=CYL, sep=True, tex=tex)
    return m, hw


def bell_lip_hd(p, mat, y0, y1, hw, clapper, clapper_r=2.6, tex=None):
    """A bell's lip band, its dark mouth under it and the clapper hanging in the mouth."""
    c = p.c
    p.part(c.box(32 - hw, y0, 32 + hw, y1), mat, 'vgrad', base=0, sep=True, tex=tex)
    p.part(c.ellipse(32, y1, hw - 1.0, 3.0) & c.box(0, y1, 64, 64), INKM, 'flat', base=0, sep=True, rim=False)
    p.part(c.circle(32, y1 + 1.6, clapper_r), clapper, 'sphere', base=0, sep=True, spec=(32 - clapper_r * 0.4, y1 + 1.6 - clapper_r * 0.4))


def cast_band_hd(p, body, mat, y, w=1.2):
    """A cast band round a bell or a vessel: a dark line with a lit line under it."""
    c = p.c
    p.decal(c.box(0, y, 64, y + w) & body, mat, -2)
    p.decal(c.box(0, y + w, 64, y + w + 1.0) & body, mat, 1)


def ding_hd(p, body, trim, cx=32.0, cy=40.0, rx=22.0, ry=14.0, rim=(23.0, 27.5), legs=3, ears=True, tex=None):
    """A three-legged vessel seen from the front: the legs, the belly, the rim band in the trim and two ring ears.
    Returns the belly and rim masks."""
    c = p.c
    ttx = ttex(trim)
    xs = (cx - rx * 0.66, cx + rx * 0.66) if legs == 2 else (cx - rx * 0.62, cx + rx * 0.62)
    y0 = cy + ry - 5.0
    for x in xs:
        p.part(c.poly([(x - 2.8, y0), (x + 2.8, y0), (x + 2.1, 58.0), (x - 2.1, 58.0)]), body, 'ray', base=-1, sep=True, tex=tex)
    bel = (c.ellipse(cx, cy, rx, ry) & c.box(0, rim[0], 64, 64)) | c.box(cx - rx + 3, rim[0], cx + rx - 3, rim[1] + 2)
    p.part(bel, body, 'sphere', base=0, sep=True, cx=cx - 5, cy=cy - 7, rx=rx + 8, ry=ry + 9, tex=tex)
    if legs == 3:
        p.part(c.poly([(cx - 2.9, cy + ry - 3.5), (cx + 2.9, cy + ry - 3.5), (cx + 2.2, 58.5), (cx - 2.2, 58.5)]), body, 'ray', base=0, sep=True, tex=tex)
    rm = c.box(cx - rx - 2, rim[0], cx + rx + 2, rim[1])
    p.part(rm, trim, 'vgrad', base=1, sep=True, tex=ttx)
    if ears:
        for x in (cx - rx - 1.6, cx + rx + 1.6):
            p.part(c.ring(x, rim[0] - 2.4, 4.4, 2.0), trim, 'ray_soft', base=0, sep=True, tex=ttx)
    return bel, rm


def talisman_hd(p, paper, band, x0=21.0, x1=43.0, y0=6.0, y1=58.0):
    """A paper talisman strip with a band across each end. Returns the strip's mask."""
    c = p.c
    strip = c.box(x0, y0, x1, y1)
    p.part(strip, paper, 'vgrad', base=0, sep=False, tex='paper', rim=False)
    for (a, b) in ((y0, y0 + 5.5), (y1 - 5.5, y1)):
        p.part(c.box(x0, a, x1, b), band, 'ray_soft', base=0, sep=True, rim=False)
    return strip


def dish_hd(p, mat, cx=32.0, cy=55.0, rx=16.0, ry=3.6):
    """A shallow dish a flame stands in."""
    return p.part(p.c.ellipse(cx, cy, rx, ry), mat, 'ray', base=0, sep=True, tex=ttex(mat))


def flame_hd(p, outer, mid, core, cx=32.0, by=55.0, w=24.0, h=46.0, lean=0.1):
    """A flame on (cx, by): the outer tongues darkest at their tips, the inner flame in the hotter colours, a
    white-hot heart low in it. Returns the flame's mask."""
    c = p.c
    f_out = mat7(Ramp([outer[0], outer[1], mid[0], mid[1], core]), 'light')
    f_in = mat7(Ramp([mid[0], mid[1], core, core, '#FFFFFF']), 'light')
    f1 = S.flame(c, cx, by, w, h, lean)
    p.part(f1, f_out, 'vgrad', base=0, sep=False, rim=False, bands=((0.32, -2), (0.6, -1), (0.8, 0), (9, 1)))
    f2 = S.flame(c, cx, by, w * 0.52, h * 0.6, -lean)
    p.part(f2, f_in, 'vgrad', base=0, sep=False, rim=False, bands=((0.3, -1), (0.62, 0), (9, 1)))
    p.decal(c.ellipse(cx - w * 0.04, by - h * 0.17, w * 0.15, h * 0.12), f_in, 3)
    return f1


# ============================================================================= deployable treasures
def practice_bell_hd(p):
    """A sect training bell: a small plain iron bell on a red cord, one cast band, an iron clapper."""
    c = p.c
    p.part(c.ring(32, 10.5, 4.4, 2.2) & c.box(0, 0, 64, 12.6), RED, 'ray_soft', base=0, sep=False, rim=False)
    p.part(c.box(28.5, 12, 35.5, 17), IRON, 'hgrad', base=0, sep=True, tex='metal')
    body, hw = bell_hd(p, IRON, 17.0, 49.0, 10.0, 20.0, tex='metal')
    cast_band_hd(p, body, IRON, 33.0)
    bell_lip_hd(p, IRON, 49.0, 54.0, 22.0, IRON, tex='metal')
    p.sparkle(24, 24, 1)


def bronze_bell_hd(p):
    """A drowned temple bell: cast bronze with a bronze loop, two bands studded with jade, a jade line on the lip and
    a jade clapper (the Earth grade's jade on bronze)."""
    c = p.c
    p.part(c.ring(32, 9.5, 4.6, 2.4) & c.box(0, 0, 64, 12.0), BRONZE, 'ray_soft', base=0, sep=False, tex='metal')
    p.part(c.box(27, 11.5, 37, 16), BRONZE, 'hgrad', base=0, sep=True, tex='metal')
    body, hw = bell_hd(p, BRONZE, 16.0, 48.0, 11.5, 22.5, power=1.6, tex='metal')
    for y in (27.0, 38.0):
        cast_band_hd(p, body, BRONZE, y)
    for (x, y) in ((22, 32), (32, 32), (42, 32), (26, 43.5), (38, 43.5)):
        p.part(c.circle(x, y, 1.7), JADE, 'sphere', base=1, sep=True, rim=False)
    bell_lip_hd(p, BRONZE, 48.0, 54.0, 25.0, JADE, 2.8, tex='metal')
    p.decal(c.box(8, 50.5, 56, 51.6), JADE, 1)
    p.sparkle(23, 22, 1)


def little_pagoda_hd(p):
    """A jade pagoda the size of a palm: four tiers of upturned jade roofs with silver ridges over red walls with
    gold doors, a gold spire, on a stone base (the Heaven grade's silver on jade)."""
    c = p.c
    p.part(c.rrect(7, 53, 57, 58.5, 1.5), STONE, 'ray', base=0, sep=True)
    tiers = ((21.0, 44.0, 53.0), (16.5, 34.0, 42.0), (12.0, 25.5, 32.5), (8.0, 17.5, 24.0))
    for (w, ry, wall_b) in tiers:
        wall = c.box(32 - w + 2.5, ry + 1.5, 32 + w - 2.5, wall_b)
        p.part(wall, LACQUER, 'bevel', base=0, sep=True, hw=1, sw=1, rim=False)
        p.part(c.box(30.2, ry + 3.5, 33.8, wall_b), GOLD, 'vgrad', base=0, sep=True, rim=False)
        roof = c.poly([(32 - w - 4.5, ry + 2.5), (32 - w - 5.5, ry - 1.5), (32 - w + 1.5, ry - 4.0), (32 + w - 1.5, ry - 4.0),
                       (32 + w + 5.5, ry - 1.5), (32 + w + 4.5, ry + 2.5)])
        p.part(roof, JADE, 'vgrad', base=0, sep=True, tex='jade')
        p.decal(c.box(32 - w + 1.5, ry - 4.0, 32 + w - 1.5, ry - 3.0), SILVER, 1)
        p.decal(c.box(32 - w - 4.5, ry + 1.5, 32 + w + 4.5, ry + 2.5) & roof, JADE, -3)
    p.part(c.box(30.5, 8.5, 33.5, 14.5), GOLD, 'hgrad', base=0, sep=True, tex='metal')
    p.part(c.ring(32, 11.5, 4.2, 1.4), SILVER, 'ray_soft', base=1, sep=True)
    p.part(c.circle(32, 7.5, 2.8), GOLD, 'sphere', base=1, sep=True, spec=(31, 6.5))


def bright_mirror_hd(p):
    """A polished bronze mirror: the cast rim with eight gold bosses, the pale face catching a window's light, a
    red tassel with a jade bead below (Earth's jade on bronze)."""
    c = p.c
    cx, cy = 32.0, 27.0
    p.part(c.taper((cx, 50), (cx - 2, 55), (cx - 3, 59), 3.6, 2.0) | c.taper((cx, 50), (cx + 3, 55), (cx + 4, 59), 3.0, 1.6), RED, 'ray_soft', base=0, sep=False, rim=False)
    p.part(c.circle(cx, cy, 23.0), BRONZE, 'sphere', base=0, sep=True, cx=cx - 6, cy=cy - 6, rx=30, ry=30, tex='metal')
    face = c.circle(cx, cy, 17.0)
    p.part(face, MIRROR, 'ray', base=0, sep=True, tex='glass')
    p.decal(c.arc(cx, cy, 12.5, 2.6, 118, 172) & face, WHITE, 0)
    p.decal(c.ellipse(cx - 5.5, cy - 6.5, 2.6, 1.8) & face, WHITE, 0)
    p.decal(c.arc(cx, cy, 14.5, 1.2, 250, 340) & face, MIRROR, 2)
    for a in range(0, 360, 45):
        x, y = cx + 20.0 * math.cos(math.radians(a)), cy - 20.0 * math.sin(math.radians(a))
        p.part(c.circle(x, y, 1.9), GOLD, 'sphere', base=1, sep=True, rim=False)
    p.part(c.circle(cx, 52.5, 3.0), JADE, 'sphere', base=1, sep=True, spec=(cx - 1, 51.5))


def mountain_seal_hd(p):
    """A jade seal the weight of a hill: a carved beast crouched on the block, a silver band round its shoulder
    (Heaven), the seal's red face with its white script."""
    c = p.c
    X, Y = XY(p)
    top = c.poly([(16, 27), (48, 27), (52, 23), (12, 23)])
    p.part(top, JADE, 'flat', base=1, sep=True, tex='jade')
    block = c.box(12, 27, 52, 56)
    p.part(block, JADE, 'bevel', base=0, sep=True, hw=2, sw=2, tex='jade')
    p.part(c.box(12, 27, 52, 30.5), SILVER, 'vgrad', base=1, sep=True, tex='metal')
    body = c.ellipse(31, 16.5, 13.5, 7.0) | c.poly([(19, 21), (44, 21), (46, 24), (17, 24)])
    p.part(body, JADE, 'sphere', base=1, sep=True, cx=28, cy=12, rx=16, ry=10, tex='jade')
    head = c.circle(43.5, 13.0, 5.2)
    p.part(head, JADE, 'sphere', base=1, sep=True, spec=(41.5, 11))
    p.decal(c.circle(45.0, 12.2, 1.0), JADE, -3)
    p.part(c.taper((18, 18), (12, 14), (14, 9), 3.0, 1.6), JADE, 'ray_soft', base=0, sep=True, rim=False)
    for x in (23, 29, 35):
        p.decal(c.arc(x, 15.5, 2.6, 1.0, 20, 160) & body, JADE, -2)
    face = c.box(17, 35, 47, 52)
    p.part(face, SEAL_RED, 'flat', base=0, sep=True, rim=False)
    for (x0, y0, x1, y1) in ((20, 38.5, 44, 40.5), (20, 46, 44, 48), (31, 37, 33, 50), (23, 41.5, 26, 45.5), (38, 41.5, 41, 45.5)):
        p.decal(c.box(x0, y0, x1, y1), PAPER, 1)
    p.sparkle(17, 30, 1)


def taming_cauldron_hd(p):
    """An iron cauldron that takes a beast in whole: the belly on three legs, a bronze rim and ring ears, a spirit
    beast's claw cast in gold on the belly, a jade stud at the rim (Earth), mist rising from the mouth."""
    c = p.c
    bel, rim = ding_hd(p, IRON, BRONZE, cy=40.0, rx=22.0, ry=14.5, rim=(24.0, 28.5), tex='metal')
    for dx in (-6.0, 0.0, 6.0):
        p.decal(c.taper((32 + dx - 2.0, 33.0), (32 + dx + 0.5, 39.0), (32 + dx + 2.4, 47.0), 2.4, 1.0) & bel, GOLD, 1)
    p.part(c.circle(32, 26.2, 1.8), JADE, 'sphere', base=1, sep=True, rim=False)
    for (a, b, d) in (((24, 22), (16, 14), (22, 8)), ((40, 22), (48, 14), (42, 8))):
        p.part(c.taper(a, b, d, 3.4, 1.6) & ~rim, QI, 'ray_soft', base=0, sep=True, rim=False)
    p.sparkle(20, 32, 1)


def wisp_banner_hd(p):
    """A formation banner that calls three wisps: a dark pole with a gold finial, indigo cloth with a gold band and
    the Mystic grade's gold lines, its hem in two tails, three wisps of light drifting over it, the aura in their light."""
    c = p.c
    p.part(c.box(11.5, 8, 15.5, 58.5), DARKWOOD, 'hgrad', base=0, sep=True, tex='wood', axis=90)
    p.part(c.circle(13.5, 7.5, 3.0), GOLD, 'sphere', base=1, sep=True, spec=(12.5, 6.5))
    cloth = c.poly([(16, 11), (55, 11), (55, 41), (46, 47), (36, 41), (26, 47), (16, 41)])
    p.part(cloth, INDIGO, 'ray', base=0, sep=True, tex='cloth', axis=90, rim=False)
    p.part(c.box(16, 11, 55, 15.5), GOLD, 'vgrad', base=1, sep=True, tex='metal')
    for x in (20.5, 50.5):
        p.decal(c.box(x - 0.5, 17, x + 0.5, 40) & cloth, GOLD, 0)
    for (x, y, r) in ((27, 25, 4.0), (43, 22, 4.6), (35, 34, 3.6)):
        p.part(c.taper((x - r * 0.3, y + r), (x - r * 1.4, y + r * 2.2), (x - r * 1.2, y + r * 3.4), r * 0.7, r * 0.25) & cloth, QI, 'flat', base=-1, sep=False, rim=False)
        p.part(c.circle(x, y, r), QI, 'sphere', base=1, sep=True, rim=False)
        p.decal(c.circle(x - r * 0.35, y - r * 0.35, r * 0.34), WHITE, 0)
    finish(p, 'mystic', '#8FE9FF')


def sealing_gourd_hd(p):
    """A violet glass gourd with a paper seal: two bulbs on a waist banded in silver, a silver cloud lid over the
    mouth (Heaven's closure), the red-scripted seal pasted on its belly."""
    c = p.c
    g = pills.PILL_GRADES['heaven']
    lower = c.circle(32, 41, 16.5) | c.poly([(25, 26), (39, 26), (42, 33), (22, 33)])
    upper = c.circle(32, 21, 10.0) | c.box(27.5, 11, 36.5, 15)
    p.part(lower, VIOLET_GLASS, 'sphere', base=0, sep=False, cx=27, cy=36, rx=21, ry=20, tex='glass')
    p.part(upper, VIOLET_GLASS, 'sphere', base=0, sep=True, cx=29, cy=18, rx=12, ry=12, tex='glass')
    p.part(c.box(23, 27.5, 41, 30.5), SILVER, 'vgrad', base=1, sep=True, tex='metal')
    p.part(c.box(26.5, 10, 37.5, 12.5), SILVER, 'vgrad', base=1, sep=True, tex='metal')
    pills.closure(p, g, 32, 10, 5.5)
    seal = c.rrect(27, 35, 37, 54, 1.2)
    p.part(seal, PAPER, 'bevel', base=0, sep=True, hw=1, sw=1, tex='paper', rim=False)
    for (y0, y1, w) in ((37.5, 41, 3.0), (43, 46.5, 3.0), (48, 52, 3.0)):
        p.decal(c.box(32 - w / 2.0, y0, 32 + w / 2.0, y1) & seal, SEAL_RED, 0)
    p.decal(c.box(30.5, 37.5, 33.5, 52) & seal, SEAL_RED, -1)


def nine_sword_array_hd(p):
    """Nine slim swords fanned up out of a red lacquered case: stormsteel blades with silver guards (the Spirit
    grade), a silver line and a cyan gem on the case, the aura."""
    c = p.c
    k = K('spirit')
    px, py = 32.0, 62.0
    for i in range(9):
        a = math.radians(58.0 + 8.0 * i)
        fr = Frame((px, py), math.degrees(a))
        blade = fr.prof(c, [(20.0, 1.7), (43.0, 1.7), (48.0, 0.0)])
        p.cylinder(fr, blade, lambda t: np.where(t > 43.0, np.clip(1.7 * (48.0 - t) / 5.0, 0.0, 1.7), 1.7), k['blade'], ridge=True, sep=True, tex='metal')
        guard = fr.prof(c, [(19.0, 1.9), (19.8, 3.2), (21.4, 3.2), (22.2, 1.9)])
        p.part(guard, k['guard'], 'ray_soft', base=1, sep=True)
    case = c.rrect(8, 42, 56, 57, 3.0)
    p.part(case, LACQUER, 'ray', base=0, sep=True, rim=True)
    p.decal(c.box(10.5, 44.5, 53.5, 45.5), SILVER, 1)
    p.decal(c.box(10.5, 54, 53.5, 55), LACQUER, -2)
    p.part(c.diamond(32, 50, 3.2, 3.2), k['gem'], 'ray', base=1, sep=True, spec=(31, 49))
    p.sparkle(32, 14, 1)
    finish(p, 'spirit')


# ============================================================================= throwables
def iron_needles_hd(p):
    """Three needles flicked at once: silver needles on the diagonal, each threaded with red silk at its eye."""
    c = p.c
    for i, off in enumerate((-8.0, 0.0, 8.0)):
        fr = Frame((14.0 + off * 0.7, 50.0 + off * 0.7), 45.0)
        needle = fr.prof(c, [(0.0, 1.9), (38.0, 1.9), (45.0, 0.0)])
        p.cylinder(fr, needle, lambda t: np.where(t > 38.0, np.clip(1.9 * (45.0 - t) / 7.0, 0.0, 1.9), 1.9), SILVER, base=1 if i == 1 else 0, sep=True, tex='metal')
        ex, ey = fr.P(2.6, 0.0)
        p.decal(c.circle(ex, ey, 0.9), SILVER, -3)
        p.part(c.taper((ex - 1.2, ey + 1.2), (ex - 5.0, ey + 2.4), (ex - 4.5, ey + 6.0), 2.4, 1.2), RED, 'ray_soft', base=0, sep=True, rim=False)
    p.sparkle(*Frame((14.0, 50.0), 45.0).P(30.0, -1.6), 1)


def flying_knives_hd(p):
    """A balanced throwing knife, and its twin behind it: a leaf blade of jadeiron with a jade inlay (Earth), a
    leather grip and a red ring at the pommel."""
    c = p.c
    k = K('earth')
    for i, (p0, base) in enumerate((((16.0, 58.0), -1), ((7.0, 52.0), 0))):
        fr = Frame(p0, 45.0)
        ring = c.ring(*fr.P(1.5, 0.0), 3.0, 1.6)
        p.part(ring, RED, 'ray_soft', base=base, sep=True, rim=False)
        grip_hd(p, fr, k, 3.6, 16.0, 2.6)
        fitting_hd(p, fr, k, 15.5, 18.5, 3.0, 0.6)
        blade = leaf_blade_hd(p, fr, k, 18.5, 52.0, 5.4, 0.55)
        work_hd(p, k, [fr.P(t, 0.0) for t in np.linspace(23.0, 44.0, 22)], blade)
        if i == 1:
            p.sparkle(*fr.P(46.0, -0.8), 1)


def thunderclap_pellet_hd(p):
    """A lacquered pellet packed with ore dust and pepper: a black ball with a red band and a thunder mark, its
    waxed fuse lit at the tip."""
    c = p.c
    ball = c.circle(30.0, 37.0, 18.0)
    p.part(ball, INKM, 'sphere', base=1, sep=True, cx=25, cy=31, rx=22, ry=22, spec=(23, 30))
    p.decal(c.box(0, 34.5, 64, 39.0) & ball, LACQUER, 0)
    p.decal(c.box(0, 34.5, 64, 35.5) & ball, LACQUER, 1)
    bolt = c.poly([(34, 40), (24.5, 51), (30.5, 51), (26.5, 58.5), (38, 46), (32, 46), (36.5, 40)]) & ball
    p.decal(dilate4(bolt) & ball & ~bolt, INKM, -1)
    p.decal(bolt, YELLOW, 2)
    p.decal(c.polyline([(32, 42.5), (28, 48)], 1.0) & bolt, YELLOW, 3)
    fuse = c.polyline(S.curve_pts((31, 19.5), (34, 10), (44, 9), 12), 2.4)
    p.part(fuse & ~ball, HEMP, 'flat', base=0, sep=True, rim=False)
    p.part(S.star4(c, 46, 8, 3) | c.circle(46.5, 8.5, 1.6), FIRE, 'flat', base=1, sep=False, rim=False)
    p.sparkle(46, 8, 1, WHITE)


# ============================================================================= talisman treasures
def elder_hus_talisman_hd(p):
    """Elder Hu's Heaven-Splitting Palm folded into paper: gold talisman paper banded in red, the palm printed in
    seal red, the Mystic aura in its gold."""
    c = p.c
    strip = talisman_hd(p, TALISMAN, RED)
    palm = c.ellipse(32.5, 39, 7.8, 8.2) | c.poly([(23.0, 30.5), (25.6, 28.5), (28.5, 36.5), (25.5, 38.5)])
    p.part(palm & strip, SEAL_RED, 'ray_soft', base=0, sep=False, rim=False)
    for (fx, top) in ((26.4, 21.0), (30.4, 17.5), (34.6, 17.5), (38.6, 21.0)):
        p.part(c.rrect(fx - 1.5, top, fx + 1.5, 35, 1.4) & strip, SEAL_RED, 'ray_soft', base=0, sep=True, rim=False)
    p.decal(c.ellipse(30.0, 37, 2.6, 3.0) & palm, SEAL_RED, 1)
    finish(p, 'mystic', '#FFE38A')


def lightning_rod_talisman_hd(p):
    """A tribulation talisman: sky-blue spirit paper banded in silver (Heaven), a copper rod down its length and the
    bolt glyph it draws in gold."""
    c = p.c
    strip = talisman_hd(p, SKY, SILVER)
    p.part(c.box(30.8, 12, 33.2, 52), COPPER, 'hgrad', base=0, sep=True, tex='metal')
    bolt = c.poly([(36, 15), (25, 34), (31.5, 34), (26, 50), (39, 29), (32.5, 29), (38.5, 15)]) & strip
    p.part(bolt, GOLD, 'ray_soft', base=1, sep=True, rim=False)
    p.decal(c.polyline([(33.5, 17), (28.5, 31)], 1.2) & bolt, GOLD, 3)


# ============================================================================= flight vessels
def flying_sword_vessel_hd(p):
    """Ride your sword into the sky: a cloudsteel jian with silver fittings (Heaven) climbing on the diagonal, the
    Qi of its flight streaming behind it."""
    c = p.c
    k = K('heaven')
    fr = Frame((10.0, 48.0), 32.0)
    for i, (w, t0) in enumerate(((5.0, 1.0), (0.0, -3.0), (-5.0, 2.0))):
        a, b = fr.P(t0, w), fr.P(t0 + 12.0, w + 0.5)
        p.part(c.taper((a[0] - 3.5, a[1] + 4.0), ((a[0] + b[0]) / 2.0 - 2.0, (a[1] + b[1]) / 2.0 + 3.0), (b[0], b[1] + 1.0), 1.4, 3.0), QI, 'ray_soft', base=0 if i == 1 else -1, sep=False, rim=False)
    fitting_hd(p, fr, k, 1.0, 5.6, 3.6, 1.0)
    grip_hd(p, fr, k, 5.2, 18.0, 2.9)
    blade = blade_hd(p, fr, k, 20.5, 52.0, 62.0, 4.0)
    work_hd(p, k, [fr.P(t, 0.0) for t in np.linspace(26.0, 50.0, 25)], blade)
    p.part(fr.prof(c, [(17.0, 3.4), (18.5, 7.6), (20.5, 8.8), (22.5, 7.0), (24.0, 3.6)]), k['guard'], 'ray', base=0, sep=True, tex='metal')
    gem_hd(p, k, *fr.P(20.5, 0.0), 2.2)
    p.sparkle(*fr.P(56.0, -0.6), 1)


def cloud_puff_vessel_hd(p):
    """A small obedient cloud: three soft lumps with a lit crown, sky-blue curls under it where it rolls."""
    c = p.c
    puff = c.circle(19, 38, 11.5) | c.circle(33, 31, 15.5) | c.circle(47, 38, 10.5) | c.box(10, 38, 56, 48)
    p.part(puff, CLOUD, 'sphere', base=0, sep=False, cx=27, cy=26, rx=30, ry=24, rim=False)
    p.decal(c.arc(33, 31, 10.0, 2.4, 110, 165) & puff, CLOUD, 3)
    p.decal(c.arc(19, 38, 7.0, 1.6, 120, 170) & puff, CLOUD, 2)
    for x in (17, 32, 47):
        p.decal(c.arc(x, 45.5, 4.4, 1.6, 200, 20) & puff, SKY, -1)
    for (x0, y, L) in ((9.0, 52.5, 14.0), (27.0, 55.0, 16.0), (46.0, 52.5, 12.0)):
        p.part(c.taper((x0, y), (x0 + L * 0.5, y - 1.2), (x0 + L, y + 0.4), 3.0, 1.2), SKY, 'ray_soft', base=1, sep=False, rim=False)


def jade_gourd_vessel_hd(p):
    """A great jade gourd you sit astride, lying on its side: two bulbs on a waist, bronze bands and a bronze
    mouth (Earth's bronze on jade), a red stopper."""
    c = p.c
    big = c.ellipse(37, 38, 21.5, 15.0)
    small = c.ellipse(15, 27, 9.5, 8.5)
    neck = c.poly([(19, 21), (26, 26), (26, 40), (16, 33)])
    p.part(big, JADE, 'sphere', base=0, sep=False, cx=31, cy=32, rx=26, ry=20, tex='jade')
    p.part(neck | small, JADE, 'sphere', base=0, sep=True, cx=13, cy=24, rx=12, ry=12, tex='jade')
    p.part(c.poly([(21, 20.5), (25, 24), (25, 39), (21, 35.5)]), BRONZE, 'hgrad', base=1, sep=True, tex='metal')
    p.part(c.poly([(5.5, 24), (9.5, 22), (9.5, 32), (5.5, 30)]), BRONZE, 'hgrad', base=1, sep=True, tex='metal')
    p.part(c.circle(5.5, 27, 2.6), RED, 'sphere', base=0, sep=True, rim=False)
    p.decal(c.arc(37, 38, 13.0, 1.6, 160, 215) & big, JADE, 2)
    p.sparkle(24, 30, 1)


def maple_leaf_vessel_hd(p):
    """A red maple leaf the size of a raft: five lobes on their gold veins, the stem trailing."""
    c = p.c
    cx, cy = 33.0, 31.0
    L = (19.0, 25.0, 27.0, 25.0, 19.0)
    pts = []
    for k in range(5):
        a = math.radians(90.0 + (k - 2) * 42.0)
        b0 = math.radians(90.0 + (k - 2) * 42.0 - 21.0)
        pts.append((cx + 14.0 * math.cos(b0), cy - 14.0 * math.sin(b0)))
        for f, w in ((0.62, 8.5), (1.0, 0.0), (0.62, -8.5)):
            pts.append((cx + L[k] * f * math.cos(a) - w * math.sin(a), cy - L[k] * f * math.sin(a) - w * math.cos(a)))
    b1 = math.radians(90.0 + 2 * 42.0 + 21.0)
    pts.append((cx + 14.0 * math.cos(b1), cy - 14.0 * math.sin(b1)))
    pts += [(cx + 5.0, cy + 14), (cx, cy + 19), (cx - 5.0, cy + 14)]
    leaf = c.poly(pts)
    p.part(leaf, EMBER, 'ray', base=0, sep=False, rim=False)
    inner = erode4(leaf)
    for k in range(5):
        a = math.radians(90.0 + (k - 2) * 42.0)
        p.decal(c.polyline([(cx, cy + 6), (cx + (L[k] - 4.0) * math.cos(a), cy - (L[k] - 4.0) * math.sin(a))], 1.3) & inner, GOLD, 1)
    p.part(c.taper((cx, cy + 17), (cx - 4, cy + 23), (cx - 9, cy + 27), 2.8, 1.6), DARKWOOD, 'ray_soft', base=0, sep=True, rim=False)
    p.decal(c.ellipse(cx - 9, cy - 5, 3.2, 2.2) & inner, EMBER, 2)


# ============================================================================= Heavenly Flames
def make_flame_hd(grade, core, mid, outer, glow):
    def draw(p):
        dish_hd(p, STONE)
        flame_hd(p, outer, mid, core)
        p.glow(glow, GLOW_STRENGTH[grade])
    return draw


def lantern_heart_flame_hd(p):
    """The flame at the heart of the Lantern Star Field, gold-white and brighter than any, in a small cage of
    lantern bronze: a dish, two bars, a capped ring and its loop; the Will grade's aura."""
    c = p.c
    dish_hd(p, LANTERN, cy=55.5, rx=14.0, ry=3.2)
    flame_hd(p, ('#E6A84A', '#F8CC72'), ('#FFE28C', '#FFF4CC'), '#FFFFFF', by=55.0, w=20.0, h=40.0)
    for x in (12.5, 51.5):
        p.part(c.box(x - 1.6, 14, x + 1.6, 54), LANTERN, 'hgrad', base=0 if x < 32 else -1, sep=True, tex='metal')
    p.part(c.box(10, 11.5, 54, 14.5), LANTERN, 'vgrad', base=1, sep=True, tex='metal')
    p.part(c.ellipse(32, 11.5, 13.0, 4.0) & c.box(0, 0, 64, 11.5), LANTERN, 'ray', base=0, sep=True, tex='metal')
    p.part(c.ring(32, 6.8, 2.6, 1.3) & c.box(0, 0, 64, 8.2), LANTERN, 'ray_soft', base=1, sep=True)
    p.part(c.box(10, 52, 54, 54), LANTERN, 'flat', base=1, sep=True, rim=False)
    p.glow('#FFF0B8', GLOW_STRENGTH['will'])


FLAMES_HD = [
    ('mist_lantern_flame', 'mystic', '#F4FFF8', ('#9ED8C0', '#C8F0E0'), ('#3E7F6A', '#5FA88E'), '#BFEFD8'),
    ('cold_lamp_flame', 'spirit', '#EAF8FF', ('#57A8E8', '#8FD0FF'), ('#1D4F8F', '#2F78C4'), '#8FC8FF'),
    ('sunscar_throne_ember', 'sage', '#FFF4C8', ('#F09A3A', '#FFC460'), ('#8F2A12', '#C8501E'), '#FFB25A'),
    ('comet_tail_flame', 'sage', '#FFFFFF', ('#C8D4F0', '#EEF2FF'), ('#6E7BA8', '#98A6D4'), '#DCE6FF'),
]


# ============================================================================= the furnace ladder
def furnace_hd(p, grade, body=None, trim=None, jewel=None, dragons=False):
    """A pill furnace on the grade's kit: three legs, the belly with the grade's work round it and a fire window,
    the rim and ring ears in the trim, a domed lid with the grade's jewel as its finial; the aura from Mystic up."""
    c = p.c
    k = K(grade)
    body, trim = body or k['blade'], trim or k['guard']
    jewel = jewel or k['gem'] or trim
    btex = ttex(body)
    bel, rim = ding_hd(p, body, trim, cy=40.5, rx=22.0, ry=14.0, rim=(23.5, 28.0), tex=btex)
    work_hd(p, k, [(x, 33.0) for x in np.linspace(14.0, 50.0, 37)], bel & c.box(0, 29.5, 64, 37), dark=body)
    dome = c.ellipse(32, 23.5, 16.5, 7.5) & c.box(0, 0, 64, 23.5)
    p.part(dome, body, 'sphere', base=0, sep=True, cx=27, cy=19, rx=20, ry=12, tex=btex)
    p.part(c.box(14.5, 21, 49.5, 23.5), trim, 'vgrad', base=1, sep=True, tex=ttex(trim))
    p.part(c.box(29.5, 14.5, 34.5, 17.5), trim, 'hgrad', base=0, sep=True, tex=ttex(trim))
    p.part(c.diamond(32, 11.5, 3.4, 4.6), jewel, 'ray', base=1, sep=True, spec=(31, 9.5))
    win = c.ellipse(32, 44, 6.4, 4.6) | c.box(25.6, 44, 38.4, 50)
    p.part(win, INKM, 'flat', base=0, sep=True, rim=False)
    fl = S.flame(c, 32, 50, 9.0, 10.0, 0.15) & win
    p.part(fl, FIRE, 'vgrad', base=0, sep=False, rim=False, bands=((0.3, -1), (0.62, 0), (9, 1)))
    p.decal(c.ellipse(32, 48.5, 2.2, 1.6) & fl, FIRE, 3)
    if dragons:
        for sx in (-1, 1):
            d = c.taper((32 + sx * 6, 40), (32 + sx * 16, 38), (32 + sx * 12, 31), 2.6, 1.4) & bel & ~win
            p.decal(d, GOLD, 1)
            p.decal(c.circle(32 + sx * 12.5, 31.5, 1.8) & bel, GOLD, 2)
            p.decal(c.circle(32 + sx * 12, 31, 0.7) & bel, INKM, 0)
    p.sparkle(19, 30, 1)
    finish(p, grade)


FURNACES_HD = [
    # id, grade, look (body, trim, jewel materials; dragons on the named cauldron)
    ('earth_vein_furnace', 'earth', {}),
    ('cloud_pattern_furnace', 'heaven', {}),
    ('mystic_tripod', 'mystic', {}),
    ('nine_dragon_cauldron', 'heaven', dict(body=BRONZE, trim=GOLD, jewel=SEAL_RED, dragons=True)),
    ('stormsteel_furnace', 'spirit', {}),
    ('sunsteel_furnace', 'sage', {}),
    ('driftsteel_furnace', 'sovereign', {}),
    ('lanternsteel_furnace', 'will', {}),
]


# ============================================================================= the table
TREASURES_HD = [
    ('practice_bell', 'treasures', practice_bell_hd), ('bronze_bell', 'treasures', bronze_bell_hd), ('little_pagoda', 'treasures', little_pagoda_hd),
    ('bright_mirror', 'treasures', bright_mirror_hd), ('mountain_seal', 'treasures', mountain_seal_hd), ('taming_cauldron', 'treasures', taming_cauldron_hd),
    ('wisp_banner', 'treasures', wisp_banner_hd), ('sealing_gourd', 'treasures', sealing_gourd_hd), ('nine_sword_array', 'treasures', nine_sword_array_hd),
    ('iron_needles', 'throwables', iron_needles_hd), ('flying_knives', 'throwables', flying_knives_hd), ('thunderclap_pellet', 'throwables', thunderclap_pellet_hd),
    ('elder_hus_talisman', 'talismans', elder_hus_talisman_hd), ('lightning_rod_talisman', 'talismans', lightning_rod_talisman_hd),
    ('flying_sword_vessel', 'vessels', flying_sword_vessel_hd), ('cloud_puff_vessel', 'vessels', cloud_puff_vessel_hd),
    ('jade_gourd_vessel', 'vessels', jade_gourd_vessel_hd), ('maple_leaf_vessel', 'vessels', maple_leaf_vessel_hd),
] + [(_id, 'flames', make_flame_hd(_grade, _core, _mid, _outer, _glow)) for (_id, _grade, _core, _mid, _outer, _glow) in FLAMES_HD] + [
    (_id, 'tools', (lambda p, g=_grade, look=_look: furnace_hd(p, g, **look))) for (_id, _grade, _look) in FURNACES_HD
] + [('lantern_heart_flame', 'flames', lantern_heart_flame_hd)]

for _id, _group, _draw in TREASURES_HD:
    register(FAM, _id, _draw, _group)
    hd(_id, _draw)
