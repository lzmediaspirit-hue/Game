"""Tools (HD, Style A): the Keeping Post's four tool ladders (picks, sickles, rods and hoop nets, nine tiers each) and the
snare kits, the one-off tools (a clay pot, the bronze furnace, a hammer, the formation kit, a needle case, the loupe, the
spade and the dew vial) and the paper talismans, their materials and the offerings, at 64 art px shown 1:1 in the 76 px
slot, with a native @32 render for the HUD item ring and the small slots.

Each ladder is one builder on the weapons' diagonal frame and kit builders (grip, fitting, gem, work), painting with
TK(tier): the tier's head metal (copper, iron, jadeiron, cloudsteel, mistjade, stormsteel, then sunglass and driftglass
through-lit) over the grade's kit, so the tier shows as material, fittings and work, never as colour alone: a hemp grip
on plain wood, then leather on darkwood and the guard metal's butt cap and eye ring, a gem at the eye, the ferrule or the
reel from Earth, the grade's work down the head (a fuller, a jade inlay, cloud curls, gold runes, a lightning zigzag,
ember beads, driftglass diamonds), capped points from Mystic and the aura as stepped glow bands. A talisman is a strip of
yellow paper with red bars, its glyph traced in the element's ink (TALISMAN_GLYPHS) over the maker's seal.
"""
import math

import numpy as np

from pix import Frame, Ramp, WHITE, erode4, shift
from palette import M, mat7
from registry import hd, register
import shapes as S
from families.weapons import K as WK, along, fitting_hd, gem_hd, grip_hd, tassel_hd, ttex, work_hd
from families.beast_parts import GRADE_HD, XY, cord_hd, fang_hd, heap_hd, knot_hd, lmask, vial_hd
from families.minerals import core_hd as mcore_hd, es_dish_hd
from families.herbs import leaf_hd, stem_hd

FAM = 'items'
ART = 64   # HD (tools/icons/README.md, "How to convert a family")


# ============================================================================= the tables
# The tool ladders' own materials: stormsteel, the two glass tiers, the sunglass tier's lacquer, the silk snare's cord
TL_STORMSTEEL = Ramp(['#0E121C', '#1C2434', '#323F56', '#566A8A', '#94A8C8'], '#05070C')
TL_SUNGLASS = Ramp(['#6E360A', '#B46612', '#EEA232', '#FFD676', '#FFF6D2'], '#2A1204')
TL_DRIFTGLASS = Ramp(['#2A5A6C', '#5294AA', '#96D4E2', '#D4F4F6', '#FFFFFF'], '#0C2630')
TL_LACQUER = Ramp(['#2A0A0E', '#4E1418', '#7A2226', '#A8383A', '#D86A62'], '#140406')
SN_SPIRITSILK = Ramp(['#2E6A7A', '#5AA6B6', '#9EDCE4', '#D8F6F6', '#FFFFFF'], '#0E2A32')

# S47 talisman craft: each talisman shows its own traced glyph (the stroke template in talismans.json).
TALISMAN_GLYPHS = {
    "flame_talisman": ("fire", [(0.25, 0.9), (0.4, 0.45), (0.5, 0.7), (0.6, 0.2), (0.75, 0.9)]),
    "thunder_talisman": ("storm", [(0.62, 0.05), (0.35, 0.5), (0.62, 0.5), (0.38, 0.95)]),
    "iron_wall_talisman": ("iron", [(0.2, 0.2), (0.8, 0.2), (0.8, 0.8), (0.2, 0.8), (0.2, 0.25)]),
    "wind_step_talisman": ("jade", [(0.5, 0.5), (0.7, 0.42), (0.72, 0.7), (0.38, 0.78), (0.25, 0.4), (0.55, 0.15), (0.9, 0.28)]),
    "veil_talisman": ("violet", [(0.08, 0.5), (0.3, 0.3), (0.5, 0.5), (0.7, 0.3), (0.92, 0.5)]),
    "binding_talisman": ("seal", [(0.2, 0.8), (0.5, 0.2), (0.8, 0.8), (0.2, 0.45), (0.8, 0.45)]),
}

# ============================================================================= HD (Style A, 64 icon space)
# Every icon is one drawing `draw(p)` in a 64 x 64 icon space (tools/icons/README.md, "HD drawing model"), the object
# inside the 4-px margin; the same description renders at 64 and at 32. The tools lie on the weapons' diagonal, the
# head at the upper right, and paint with the weapons' kit builders (tassel, grip, fitting, gem, work) on TK(tier):
# the tier's head metal over the grade's kit, so a ladder is one builder and the tier its material, fittings and work.


SUNGLASS_HD, DRIFTGLASS_HD, LACQUER_HD, STORMSTEEL_HD = (mat7(TL_SUNGLASS, 'glass'), mat7(TL_DRIFTGLASS, 'glass'), mat7(TL_LACQUER, 'porcelain'),
                                                         mat7(TL_STORMSTEEL, 'metal'))
SPIRITSILK_HD = mat7(SN_SPIRITSILK, 'silk')
WOOD, DARKWOOD, BAMBOO, HEMP, STRAW, PAPER, TALISMAN, SEAL, GOLD, BRONZE, IRON, SILVER, JADE = (
    M('wood'), M('darkwood'), M('bamboo'), M('hemp'), M('straw'), M('paper'), M('talisman', 'paper'), M('seal'), M('gold'),
    M('bronze'), M('iron'), M('silver'), M('jade'))
CLAY, PORCELAIN, RED, INK, CLOUD, SKY, QI, PINK, LEAF, WAX, PEARL, NAVY = (M('clay'), M('porcelain'), M('red', 'silk'), M('ink'), M('cloud'), M('sky'),
                                                                           M('qi', 'gem'), M('pink', 'porcelain'), M('leaf'), M('wax'), M('pearl'),
                                                                           M('navy', 'silk'))
NONE = GRADE_HD['plain']    # a part builder's grade with no trim of its own

# The tool ladders' tiers: the grade whose kit a tier paints with, and the head metal over it (copper before iron,
# then the ore's metal, the two glass tiers through-lit).
TIER_GRADE = {0: 'plain', 1: 'common', 2: 'common', 3: 'earth', 4: 'heaven', 5: 'mystic', 6: 'spirit', 7: 'sage', 8: 'sovereign'}
TIER_HEAD = {1: M('copper'), 2: M('iron'), 3: M('jadeiron'), 4: M('cloudsteel'), 5: M('mistjade_m'), 6: STORMSTEEL_HD, 7: SUNGLASS_HD, 8: DRIFTGLASS_HD}
TFRAME = Frame((9.0, 57.0), 48.0)     # the haft of a pick, a sickle or a hammer, lower left to upper right


def TK(t):
    """The tier's kit: the weapons' kit of its grade (blade, guard, grip, wrap, gem, tassel, bead, shaft, glow) with
    the tier's head metal as the blade; hemp on a plain wood haft at copper, darkwood at iron, lacquer at sunglass."""
    k = WK(TIER_GRADE[t])
    k['tier'] = t
    if t >= 1:
        k['blade'] = TIER_HEAD[t]
    if t == 1:
        k['grip'], k['wrap'], k['shaft'] = HEMP, STRAW, WOOD
    elif t == 2:
        k['shaft'] = DARKWOOD
    elif t == 7:
        k['shaft'] = LACQUER_HD
    return k


def finish_hd(p, k):
    if k.get('glow'):
        p.glow(*k['glow'])


def haft_hd(p, fr, k, t0, t1, hw, grip=(2.0, 16.0), cap=True, angle=48.0):
    """A wooden (or lacquered) haft along the frame, its grain along it, the grade's wrapped grip at the butt and a
    butt cap in the guard metal from Earth."""
    m = fr.prof(p.c, [(t0, hw), (t1, hw)])
    p.cylinder(fr, m, hw, k['shaft'], sep=True, tex=ttex(k['shaft']), axis=angle)
    if grip is not None:
        grip_hd(p, fr, k, grip[0], grip[1], hw + 0.3)
    if cap and k['lv'] >= 2:
        fitting_hd(p, fr, k, t0 - 0.5, t0 + 2.6, hw + 0.6, 0.6)
    return m


def tips_hd(p, k, pts, mask):
    """From Mystic, the points of a head are capped in the guard metal."""
    if k['lv'] >= 4:
        for (x, y) in pts:
            p.decal(p.c.circle(x, y, 2.2) & mask, k['guard'], 0)
            p.decal(p.c.circle(x - 0.6, y - 0.6, 0.9) & mask, k['guard'], 2)


# ----------------------------------------------------------------------------- Delving: picks
def pick_hd(p, t):
    """A pickaxe: the haft on the diagonal, the head across it at the eye, two arms curving out and forward to their
    points; the eye bound in the guard metal with the gem from Earth, the grade's work down the upper arm. The old
    pickaxe's head is dull iron spotted with rust and lashed to a split haft."""
    k, c, fr = TK(t), p.c, TFRAME
    head = k['blade'] if t >= 1 else IRON
    ex, ey = fr.P(44.0, 0.0)
    haft_hd(p, fr, k, 0.0, 47.0, 3.2, grip=(2.0, 17.0) if t < 4 else (2.0, 15.0))
    if t >= 4:
        grip_hd(p, fr, k, 32.0, 38.0, 3.4)
    block = fr.prof(c, [(39.5, 6.0), (48.5, 6.0)])
    p.cylinder(fr, block, 6.0, head, sep=True, tex=ttex(head))
    up = fang_hd(p, NONE, fr.P(44.0, -3.0), fr.P(50.5, -13.0), fr.P(48.5, -24.0), 9.6, mat=head, w1=1.8, trim=False, tex=ttex(head), grain=False)
    low = fang_hd(p, NONE, fr.P(44.0, 3.0), fr.P(49.0, 12.0), fr.P(40.0, 24.0), 9.0, mat=head, w1=1.8, trim=False, tex=ttex(head), grain=False)
    arms = up | low | block
    if t == 0:
        for (x, y, r) in ((fr.P(50.0, -15.0) + (2.2,)), (fr.P(47.5, 13.0) + (2.0,)), (fr.P(46.0, -7.0) + (1.6,))):
            p.decal(c.circle(x, y, r) & arms, M('copper'), -2)
        p.line([fr.P(20.0, -2.4), fr.P(27.0, 1.8)], k['shaft'], -3, 1.0)
        cord_hd(p, [fr.P(36.5, -4.4), fr.P(38.5, 4.4)], HEMP, 2.4)
        cord_hd(p, [fr.P(48.5, -6.0), fr.P(50.5, 5.0)], HEMP, 2.4)
    else:
        work_hd(p, k, S.curve_pts(fr.P(44.0, -5.0), fr.P(50.0, -13.0), fr.P(48.5, -21.0), 12)[1:], arms, dark=head)
    tips_hd(p, k, [fr.P(48.5, -24.0), fr.P(40.0, 24.0)], arms)
    eye = c.ring(ex, ey, 4.4, 1.8)
    p.part(eye, k['guard'] if t >= 1 else HEMP, 'ray', base=0, sep=True, tex=ttex(k['guard']) if t >= 1 else None, rim=t >= 1)
    if k['gem'] is not None:
        gem_hd(p, k, ex, ey, 2.6)
    else:
        p.part(c.circle(ex, ey, 2.6), k['shaft'], 'sphere', base=-1, sep=True, rim=False)
    p.sparkle(*fr.P(48.0, -20.0), 1)
    finish_hd(p, k)


# ----------------------------------------------------------------------------- Foraging: sickles
def sickle_hd(p, t):
    """A herb sickle: a short wrapped handle on the diagonal, a ferrule, and the blade curving up from it and over to
    the right, thick at the back and honed to its inner edge; the grade's work along the back. The herb sickle is a
    small hand blade on plain wood."""
    k, c, fr = TK(t), p.c, TFRAME
    head = k['blade'] if t >= 1 else IRON
    small = t == 0
    haft_hd(p, fr, k, 0.0, 22.0 if small else 24.0, 3.4, grip=(2.0, 18.0))
    fitting_hd(p, fr, k, 21.0 if small else 23.0, 26.0, 3.9, 0.8)
    cx, cy, r = (37.0, 30.0, 20.0) if small else (37.0, 28.0, 23.0)
    hole = c.ellipse(cx + 5.0, cy + 3.4, r - 3.2, r - 4.2)
    blade = c.sector(cx, cy, r, 20, 218) & ~hole
    blade |= c.poly([fr.P(24.0, -3.2), fr.P(24.0, 3.2), fr.P(31.0, 2.0), fr.P(31.0, -3.5)]) & ~hole
    p.part(blade, head, 'ray', base=0, sep=True, tex=ttex(head))
    inner = blade & ~erode4(blade)
    X, Y = XY(p)
    p.decal(inner & (((X - cx - 5.0) / (r - 3.2)) ** 2 + ((Y - cy - 3.4) / (r - 4.2)) ** 2 < 1.15) & (Y > cy - r * 0.9), head, 3)
    p.decal(erode4(blade) & ~erode4(erode4(blade)) & (Y < cy) & (X < cx + r * 0.6), head, -2)
    arc = [(cx + (r - 2.6) * math.cos(math.radians(a)), cy - (r - 2.6) * math.sin(math.radians(a))) for a in range(40, 190, 6)]
    work_hd(p, k, arc, blade, dark=head)
    tips_hd(p, k, [(cx + r * math.cos(math.radians(24)), cy - r * math.sin(math.radians(24)))], blade)
    if k['lv'] >= 2:
        gem_hd(p, k, *fr.P(24.5, 0.0), 2.2)
    p.sparkle(cx - 4.0, cy - r + 3.0, 1)
    finish_hd(p, k)


# ----------------------------------------------------------------------------- Angling: rods
# The rod's own materials by tier: the rod body (reed and wood before the head metal), the line, the float and its band
ROD_HD = {
    0: dict(rod=BAMBOO, marks='nodes', line=PAPER, flt=M('red', 'porcelain'), band=PAPER, hook=IRON),
    1: dict(rod=STRAW, marks='nodes', line=HEMP, flt=M('copper'), band=PAPER, hook=IRON),
    2: dict(rod=DARKWOOD, marks='rings', line=PAPER, flt=IRON, band=RED, hook=IRON),
    3: dict(rod=M('jadeiron'), marks='rings', line=JADE, flt=JADE, band=PAPER, hook=BRONZE),
    4: dict(rod=M('cloudsteel'), marks='rings', line=SKY, flt=CLOUD, band=QI, hook=SILVER),
    5: dict(rod=M('mistjade_m'), marks='rings', line=M('violet', 'silk'), flt=GOLD, band=M('violet'), hook=GOLD),
    6: dict(rod=STORMSTEEL_HD, marks='rings', line=M('cyan'), flt=M('storm'), band=WHITE, hook=SILVER),
    7: dict(rod=SUNGLASS_HD, marks='rings', line=GOLD, flt=M('fire', 'porcelain'), band=GOLD, hook=GOLD),
    8: dict(rod=DRIFTGLASS_HD, marks='rings', line=M('starlight', 'silk'), flt=M('starlight'), band=WHITE, hook=M('starlight')),
}
RFRAME = Frame((7.0, 58.0), 47.0)


def rod_hd(p, t):
    """A fishing rod on the diagonal, its grip at the butt and a reel below it, the rod tapering to the tip, the line
    falling from the tip to a float and a hook at the right; reed and bamboo show their nodes, a metal rod its rings
    in the guard metal."""
    k, R, c, fr = TK(t), ROD_HD[t], p.c, RFRAME
    rod = fr.prof(c, [(0.0, 2.9), (16.0, 2.6), (68.0, 1.1)])
    p.cylinder(fr, rod, lambda tt: np.clip(2.9 - 1.8 * tt / 68.0, 1.1, 2.9), R['rod'], sep=True, tex=ttex(R['rod']), axis=47.0)
    if R['marks'] == 'nodes':
        for t0 in (22.0, 34.0, 46.0, 57.0):
            p.decal(fr.prof(c, [(t0 - 0.6, 3.0), (t0 + 0.6, 3.0)]) & rod, R['rod'], -2)
            p.decal(fr.prof(c, [(t0 + 0.6, 3.0), (t0 + 1.4, 3.0)]) & rod, R['rod'], 1)
    else:
        for t0 in (26.0, 40.0, 53.0):
            fitting_hd(p, fr, k, t0 - 0.9, t0 + 0.9, 2.9 - 1.8 * t0 / 68.0 + 0.5, 0.0)
    grip_hd(p, fr, k, 1.0, 14.0, 3.3)
    if k['lv'] >= 2:
        fitting_hd(p, fr, k, 13.5, 16.5, 3.4, 0.6)
    work_hd(p, k, along(fr, 17.5, 25.0), rod, dark=R['rod'])
    tx, ty = fr.P(68.0, 0.0)
    line = c.polyline(S.curve_pts((tx, ty), (tx + 7.0, ty + 10.0), (tx + 3.0, ty + 22.0), 12), 1.2)
    p.part(line & ~rod, R['line'], 'flat', base=1, sep=False, rim=False)
    fx, fy = tx + 3.0, ty + 26.0
    flt = c.ellipse(fx, fy, 2.4, 4.4)
    p.part(flt, R['flt'], 'sphere', base=0, sep=True, spec=(fx - 0.8, fy - 1.6))
    p.decal(c.box(fx - 2.4, fy - 0.8, fx + 2.4, fy + 0.6) & flt, R['band'], 1)
    p.part(c.seg(fx, fy + 4.0, fx, fy + 9.0, 1.2), R['line'], 'flat', base=1, sep=False, rim=False)
    hook = c.arc(fx - 1.8, fy + 10.5, 2.6, 1.3, 180, 360) | c.box(fx + 0.4, fy + 8.0, fx + 1.6, fy + 11.0)
    p.part(hook, R['hook'], 'flat', base=0, sep=True)
    rx, ry = fr.P(17.0, 4.6)
    p.part(c.circle(rx, ry, 3.6), k['guard'] if t >= 1 else WOOD, 'sphere', base=0, sep=True, tex=ttex(k['guard']) if t >= 1 else None)
    gem_hd(p, k, rx, ry, 1.8, fallback=False)
    p.sparkle(*fr.P(44.0, -2.6), 1)
    finish_hd(p, k)


# ----------------------------------------------------------------------------- Netting: hoop nets
# the hoop (the head metal from copper), the mesh and its pitch (finer up the ladder), the collar at the handle
NET_HD = {
    0: dict(hoop=STRAW, mesh=HEMP, pitch=7, shaft=BAMBOO, collar=HEMP),
    1: dict(hoop=WOOD, mesh=HEMP, pitch=6, shaft=WOOD, collar=HEMP),
    2: dict(hoop=IRON, mesh=M('clay', 'cloth'), pitch=6, shaft=DARKWOOD, collar=BRONZE),
    3: dict(hoop=M('jadeiron'), mesh=PAPER, pitch=5, shaft=DARKWOOD, collar=BRONZE),
    4: dict(hoop=M('cloudsteel'), mesh=CLOUD, pitch=5, shaft=DARKWOOD, collar=SILVER),
    5: dict(hoop=M('mistjade_m'), mesh=M('violet', 'silk'), pitch=5, shaft=M('plum', 'silk'), collar=GOLD),
    6: dict(hoop=STORMSTEEL_HD, mesh=M('storm', 'silk'), pitch=4, shaft=NAVY, collar=SILVER),
    7: dict(hoop=SUNGLASS_HD, mesh=GOLD, pitch=4, shaft=LACQUER_HD, collar=GOLD),
    8: dict(hoop=DRIFTGLASS_HD, mesh=PEARL, pitch=4, shaft=NAVY, collar=M('starlight')),
}


def net_hd(p, t):
    """A hoop net: the handle from the lower left up to the hoop at the upper right, the collar where they meet, the
    bag hanging behind the hoop and drooping to the lower right in its mesh (finer up the ladder); the grade's work
    round the hoop. The reed net is a short bare bamboo stick with a straw hoop."""
    k, N, c = TK(t), NET_HD[t], p.c
    X, Y = XY(p)
    hx, hy, rx, ry = 40.0, 22.0, 16.0, 12.5
    a = math.radians(212)
    jx, jy = hx + rx * math.cos(a), hy - ry * math.sin(a)
    a0 = (12.0, 54.0) if t == 0 else (7.0, 58.0)
    ang = math.degrees(math.atan2(a0[1] - jy, jx - a0[0]))
    fr = Frame(a0, ang)
    L = math.hypot(jx - a0[0], jy - a0[1])
    k['shaft'] = N['shaft']
    haft_hd(p, fr, k, 0.0, L + 1.0, 2.6, grip=None if t == 0 else (1.5, 13.0), angle=ang)
    if t == 0:
        for t0 in (10.0, 20.0):
            p.decal(fr.prof(c, [(t0 - 0.6, 2.7), (t0 + 0.6, 2.7)]) & c.a, BAMBOO, -2)
    # the bag: the hoop's inside and the sag below it
    inner = c.ellipse(hx, hy, rx - 1.2, ry - 1.2)
    tip = (hx + 0.55 * rx, hy + 2.4 * ry)
    left = S.curve_pts((hx - 0.8 * rx, hy + 0.5 * ry), (hx - 0.3 * rx, hy + 1.9 * ry), tip, 12)
    right = S.curve_pts(tip, (hx + 1.1 * rx, hy + 1.9 * ry), (hx + 0.98 * rx, hy + 0.25 * ry), 12)
    bag = (c.poly(left + right) | inner) & c.box(0, 0, 61, 61)
    p.part(bag, N['mesh'], 'ray_soft', base=-2, sep=True, rim=False)
    xi, yi = np.floor(X).astype(int), np.floor(Y).astype(int)
    pitch = N['pitch']
    grid = ((xi + yi) % pitch == 0) | ((xi - yi) % pitch == 0)
    p.decal(bag & erode4(bag) & grid, N['mesh'], 1)
    p.decal(bag & erode4(bag) & ((xi + yi) % pitch == 0) & ((xi - yi) % pitch == 0), N['mesh'], 2)
    p.decal(bag & ~erode4(bag) & ~inner, N['mesh'], 0)
    if t == 8:
        for (x, y) in ((44, 40), (52, 46), (36, 26), (47, 20)):
            p.sparkle(x, y, 0)
    # the hoop
    hoop = c.ring(hx, hy, rx, 3.0, ry)
    p.part(hoop, N['hoop'], 'ray', base=0, sep=True, tex=ttex(N['hoop']))
    p.decal(hoop & ~erode4(hoop) & (X + Y < hx + hy - 6), N['hoop'], 2)
    ring_pts = [(hx + (rx - 1.5) * math.cos(math.radians(g)), hy - (ry - 1.5) * math.sin(math.radians(g))) for g in range(120, -30, -6)]
    work_hd(p, k, ring_pts, hoop, dark=N['hoop'])
    if t == 0:
        for g in (40, 100, 160, 250, 320):
            p.decal(c.circle(hx + rx * math.cos(math.radians(g)), hy - ry * math.sin(math.radians(g)), 1.6) & hoop, HEMP, -1)
    p.part(c.circle(jx, jy, 3.2), N['collar'], 'sphere', base=0, sep=True, tex=ttex(N['collar']), rim=t >= 2)
    gem_hd(p, k, jx, jy, 1.7, fallback=False)
    p.sparkle(hx - rx * 0.5, hy - ry - 1.0, 1)
    finish_hd(p, k)


# ----------------------------------------------------------------------------- V10c · snare kits
SNARE_HD = {
    'hemp': dict(k='plain', cord=HEMP, w=2.6, twist=True, stake=WOOD, cap=None, stakes=1, fit='knot', ring=None),
    'iron': dict(k='earth', cord=IRON, w=2.0, twist=False, stake=DARKWOOD, cap=IRON, stakes=2, fit='ring', ring=IRON),
    'silk': dict(k='mystic', cord=SPIRITSILK_HD, w=2.4, twist=False, stake=BAMBOO, cap=SILVER, stakes=2, fit='toggle', ring=JADE),
    'star': dict(k='sovereign', cord=M('starlight', 'silk'), w=2.4, twist=False, stake=NAVY, cap=M('starlight'), stakes=2, fit='ring', ring=DRIFTGLASS_HD),
}


def stake_hd(p, top, tip, K):
    """A pointed stake from its head down to its tip, a barb on the right where the line catches, the cord lashed
    under the head, a ferrule cap on the richer kits."""
    c = p.c
    (x0, y0), (x1, y1) = top, tip
    ang = math.degrees(math.atan2(y0 - y1, x1 - x0))
    fr = Frame(top, ang)
    L = math.hypot(x1 - x0, y1 - y0)
    bx, by = fr.P(L * 0.3, 0.0)
    p.part(c.poly([(bx, by - 2.4), (bx + 6.4, by - 5.6), (bx + 5.6, by - 2.6), (bx, by + 2.6)]), K['stake'], 'ray', base=0, sep=True)
    body = fr.prof(c, [(0.0, 3.0), (L * 0.78, 3.0), (L, 0.4)])
    p.cylinder(fr, body, lambda t: np.where(t > L * 0.78, np.clip(3.0 * (L - t) / (L * 0.22), 0.4, 3.0), 3.0), K['stake'], sep=True,
               tex=ttex(K['stake']), axis=ang)
    p.decal(c.ellipse(x0, y0 + 0.4, 3.0, 1.4) & body, K['stake'], 2)
    if K['cap'] is not None:
        cap = fr.prof(c, [(-0.4, 3.5), (5.0, 3.5)])
        p.part(cap, K['cap'], 'ray', base=0, sep=True, tex=ttex(K['cap']))
        p.decal(c.ellipse(x0, y0 + 0.4, 3.0, 1.4) & cap, K['cap'], 2)
    cord_hd(p, [fr.P(L * 0.17, -3.6), fr.P(L * 0.19, 3.6)], K['cord'], K['w'] * 0.8)
    cord_hd(p, [fr.P(L * 0.24, -3.6), fr.P(L * 0.26, 3.6)], K['cord'], K['w'] * 0.8)
    return body


def snare_hd(p, tier):
    """A snare kit: the spare cord coiled flat at the upper left, its running noose hanging below with the fitting
    that closes it, the line over to the stake (two, capped, on the richer kits) driven upright at the right."""
    K, c = SNARE_HD[tier], p.c
    cord, k = K['cord'], WK(K['k'])
    stakes = [((47.0, 17.0), (44.0, 59.0))]
    if K['stakes'] == 2:
        stakes = [((54.0, 25.0), (52.0, 59.0))] + stakes
    for (top, tip) in stakes:
        stake_hd(p, top, tip, K)
    cx, cy = 23.0, 23.0
    pts = []
    for i in range(121):
        f = i / 120.0
        th = -math.pi * 0.5 + f * 2.25 * 2 * math.pi
        r = 2.8 + 15.2 * f
        pts.append((cx + r * math.cos(th), cy + r * 0.78 * math.sin(th)))
    coil = c.polyline(pts, K['w'])
    p.part(coil, cord, 'ray_soft', base=0, sep=True, rim=False)
    X, Y = XY(p)
    if K['twist']:
        p.decal(coil & (np.floor(X + Y).astype(int) % 4 == 0), cord, -2)
    else:
        p.decal(coil & (X + Y < cx + cy - 8), cord, 2)
        p.decal(coil & (X + Y > cx + cy + 14), cord, -2)
    ex, ey = pts[-1]
    line = c.polyline(S.curve_pts((ex, ey), (ex + 10.0, ey - 4.0), (47.0, 26.0), 12), K['w'])
    p.part(line & ~coil, cord, 'flat', base=0, sep=True, rim=False)
    drop = c.seg(21.0, 37.0, 21.0, 43.0, K['w'])
    noose = c.ring(21.0, 50.5, 10.4, K['w'], 7.2)
    p.part(drop | noose, cord, 'ray_soft', base=0, sep=True, rim=False)
    if K['twist']:
        p.decal(noose & (np.floor(X + Y).astype(int) % 3 == 0), cord, -2)
    if K['fit'] == 'knot':
        knot_hd(p, 21.0, 42.5, 3.0, cord)
    elif K['fit'] == 'ring':
        p.part(c.ring(21.0, 42.5, 4.6, 2.2), K['ring'], 'ray', base=0, sep=True, tex=ttex(K['ring']))
        p.decal(c.arc(21.0, 42.5, 4.6, 2.2, 100, 190), K['ring'], 2)
    else:
        tog = c.poly([(14.0, 44.0), (28.0, 41.0), (28.4, 43.6), (14.4, 46.6)])
        p.part(tog, K['ring'], 'ray', base=0, sep=True, tex='jade')
        p.decal(c.box(16.0, 42.6, 20.0, 43.6) & tog, K['ring'], 2)
    if k['glow']:
        p.glow(*k['glow'])
        for (x, y) in ((8, 8), (30, 50), (12, 40)):
            p.sparkle(x, y, 1 if x == 8 else 0)


# ----------------------------------------------------------------------------- the one-off tools
def clay_pot_hd(p):
    """A blackened clay cooking pot on three stub feet: a round belly with a wet sheen, a spout, a loop handle, a lid
    with a knob, soot up the far side."""
    c = p.c
    X, Y = XY(p)
    for x in (18.0, 32.0, 46.0):
        p.part(c.poly([(x - 2.6, 50.0), (x + 2.6, 50.0), (x + 2.0, 58.0), (x - 2.0, 58.0)]), CLAY, 'ray', base=-2, sep=True)
    body = c.ellipse(32.0, 38.0, 22.0, 17.0)
    p.part(body, CLAY, 'sphere', base=-1, sep=True, cx=28.0, cy=32.0, rx=25.0, ry=22.0, tex='clay')
    p.decal(body & (X + Y > 84), CLAY, -3)
    p.decal(c.ellipse(20.0, 30.0, 6.0, 4.0) & body, CLAY, 1)
    spout = c.taper((50.0, 33.0), (57.0, 29.0), (59.0, 22.0), 7.0, 3.6)
    p.part(spout, CLAY, 'ray', base=-1, sep=True)
    handle = c.ring(9.0, 34.0, 6.6, 3.0) & c.box(0, 0, 11.5, 64)
    p.part(handle, CLAY, 'ray', base=-2, sep=True)
    p.part(c.box(6.0, 26.0, 12.0, 28.2) | c.box(6.0, 40.0, 12.0, 42.2), CLAY, 'flat', base=-2, sep=True)
    lid = c.ellipse(32.0, 22.5, 15.0, 4.6)
    p.part(lid, CLAY, 'ray', base=0, sep=True, tex='clay')
    p.part(c.ellipse(32.0, 17.5, 3.6, 2.6), CLAY, 'sphere', base=0, sep=True)
    p.decal(c.box(12.0, 34.0, 52.0, 35.4) & body, CLAY, -2)


def bronze_furnace_hd(p):
    """A bronze tripod furnace: the ding on three legs, ring ears at the shoulder, a taotie band, a domed lid with a
    jade knob, the fire showing in the window at its foot."""
    c = p.c
    for x in (16.0, 32.0, 48.0):
        p.part(c.poly([(x - 3.4, 44.0), (x + 3.4, 44.0), (x + 2.4, 58.5), (x - 2.4, 58.5)]), BRONZE, 'ray', base=-1, sep=True, tex='metal')
    body = (c.ellipse(32.0, 36.0, 23.0, 15.0) & c.box(0, 26.0, 64, 64)) | c.box(9.0, 24.0, 55.0, 30.0)
    p.part(body, BRONZE, 'sphere', base=0, sep=True, cx=28.0, cy=30.0, rx=27.0, ry=22.0, tex='metal')
    for x in (7.0, 57.0):
        p.part(c.ring(x, 22.0, 4.6, 2.2), BRONZE, 'ray', base=0, sep=True, tex='metal')
    p.part(c.box(7.0, 22.0, 57.0, 26.0), BRONZE, 'vgrad', base=1, sep=True, tex='metal')
    band = c.box(12.0, 32.0, 52.0, 35.5) & body
    p.decal(band, BRONZE, -2)
    for x in range(15, 50, 6):
        p.decal(c.box(x, 32.6, x + 3.0, 34.8) & body, BRONZE, 2)
    lid = c.ellipse(32.0, 21.0, 15.0, 6.0) & c.box(0, 0, 64, 22.5)
    p.part(lid, BRONZE, 'ray', base=1, sep=True, tex='metal')
    p.part(c.circle(32.0, 13.5, 3.6), JADE, 'sphere', base=0, sep=True, spec=(30.8, 12.2), tex='jade')
    win = c.ellipse(32.0, 41.0, 7.0, 4.4)
    p.part(win, M('fire'), 'ray_soft', base=0, sep=True, rim=False)
    p.decal(c.ellipse(32.0, 42.0, 3.6, 2.0) & win, M('fire'), 2)
    p.decal(c.ellipse(31.0, 42.5, 1.4, 0.9) & win, M('fire'), 3)
    p.sparkle(20.0, 27.0, 1)


def forge_hammer_hd(p):
    """A smith's hammer on the diagonal: a darkwood haft in a leather grip, a bronze band under the head, the iron
    head square across the haft with a bright face and a struck edge."""
    k, c, fr = WK('common'), p.c, TFRAME
    k['shaft'] = DARKWOOD
    haft_hd(p, fr, k, 0.0, 48.0, 3.6, grip=(2.0, 18.0), cap=False)
    fitting_hd(p, fr, k, 39.0, 43.5, 4.2, 0.8, line=41.0)
    head = fr.prof(c, [(43.0, 14.0), (56.0, 14.0)])
    p.cylinder(fr, head, 14.0, IRON, sep=True, tex='metal')
    t, w = fr.along(c)
    p.decal(head & (t < 45.0), IRON, -2)
    p.decal(head & (t > 54.5), IRON, 1)
    p.decal(head & (w < -12.4), IRON, 2)
    p.decal(head & (w > 12.0), IRON, -3)
    p.line([fr.P(44.0, -13.0), fr.P(55.0, -13.0)], IRON, 3, 1.0)
    p.sparkle(*fr.P(52.0, -8.0), 1)


def formation_kit_hd(p):
    """A formation kit: a darkwood box with bronze corners, its lid pushed back, a compass dial set in the lid, a
    stick of chalk on the rim and three small flags on their poles standing out of it."""
    c = p.c
    for i, (x, mat) in enumerate(((16.0, RED), (30.0, JADE), (44.0, QI))):
        y0 = 8.0 + (i % 2) * 4.0
        p.part(c.box(x - 0.9, y0, x + 0.9, 36.0), WOOD, 'flat', base=0, sep=True, rim=False)
        p.part(c.poly([(x + 1.0, y0), (x + 12.0, y0 + 4.5), (x + 1.0, y0 + 10.0)]), mat, 'ray', base=0, sep=True, rim=False, tex='cloth', axis=0)
    box = c.rrect(8.0, 34.0, 56.0, 58.0, 2.0)
    p.part(box, DARKWOOD, 'bevel', base=0, sep=True, hw=2, sw=2, tex='wood', axis=0)
    lid = c.rrect(6.0, 30.0, 58.0, 38.0, 1.5)
    p.part(lid, DARKWOOD, 'ray', base=1, sep=True, tex='wood', axis=0)
    for (x0, y0, x1, y1) in ((8.0, 52.0, 13.0, 58.0), (51.0, 52.0, 56.0, 58.0), (6.0, 30.0, 11.0, 35.0), (53.0, 30.0, 58.0, 35.0)):
        p.part(c.box(x0, y0, x1, y1) & (box | lid), BRONZE, 'bevel', base=0, sep=True, hw=1, sw=1, tex='metal')
    dial = c.circle(32.0, 46.5, 7.0)
    p.part(dial, GOLD, 'ray', base=0, sep=True, tex='metal')
    p.decal(c.circle(32.0, 46.5, 4.6) & dial, PAPER, 0)
    p.decal(c.poly([(32.0, 42.4), (30.8, 46.5), (33.2, 46.5)]) & dial, SEAL, 0)
    p.decal(c.poly([(32.0, 50.6), (30.8, 46.5), (33.2, 46.5)]) & dial, INK, 1)
    p.part(c.seg(14.0, 42.0, 24.0, 40.0, 3.0), PAPER, 'ray_soft', base=1, sep=True, rim=False)


def needle_case_hd(p):
    """A bamboo needle case on the diagonal, its red lacquer cap at the near end, three silver needles standing out
    of its open mouth, a gold thread wound on one."""
    c = p.c
    fr = Frame((10.0, 52.0), 42.0)
    tube = fr.prof(c, [(0.0, 7.2), (40.0, 7.2)])
    p.cylinder(fr, tube, 7.2, BAMBOO, sep=True, tex='wood', axis=42.0)
    for t0 in (14.0, 27.0):
        p.decal(fr.prof(c, [(t0 - 0.7, 7.3), (t0 + 0.7, 7.3)]) & tube, BAMBOO, -2)
        p.decal(fr.prof(c, [(t0 + 0.7, 7.3), (t0 + 1.6, 7.3)]) & tube, BAMBOO, 1)
    mx, my = fr.P(40.0, 0.0)
    mouth = c.ellipse(mx, my, 7.0, 7.0)
    p.part(mouth, BAMBOO, 'flat', base=-3, sep=True, rim=False)
    p.decal(c.ring(mx, my, 7.0, 1.4) & mouth, BAMBOO, 1)
    cap = fr.prof(c, [(-1.5, 7.9), (8.0, 7.9)])
    p.cylinder(fr, cap, 7.9, M('seal', 'porcelain'), sep=True, tex='glass')
    for (dw, L) in ((0.0, 17.0), (-3.4, 13.0), (3.0, 15.0)):
        a, b = fr.P(38.5, dw), fr.P(38.5 + L, dw * 0.6)
        p.part(c.seg(a[0], a[1], b[0], b[1], 1.6) & ~cap, SILVER, 'flat', base=1, sep=True)
        p.decal(c.circle(b[0], b[1], 1.0), SILVER, 3)
    p.line([fr.P(46.0, 3.0), fr.P(47.5, 1.4), fr.P(49.0, 3.0), fr.P(50.5, 1.4)], GOLD, 1, 1.4, only_on=False)
    p.sparkle(*fr.P(55.0, -1.0), 1)


def appraiser_loupe_hd(p):
    """An appraiser's loupe: a bronze rim round a jade lens at the upper right, a darkwood handle on the diagonal
    wrapped in jade cord with a bronze collar."""
    k, c, fr = WK('earth'), p.c, TFRAME
    k['shaft'], k['grip'], k['wrap'] = DARKWOOD, M('deepjade'), JADE
    haft_hd(p, fr, k, 0.0, 26.0, 3.6, grip=(2.0, 22.0))
    fitting_hd(p, fr, k, 25.0, 30.0, 4.4, 0.8)
    lx, ly = 39.0, 25.0
    lens = c.circle(lx, ly, 14.0)
    p.part(lens, JADE, 'sphere', base=0, sep=True, cx=lx, cy=ly, rx=14.0, ry=14.0, tex='jade')
    p.decal(c.arc(lx, ly, 10.0, 2.4, 110, 165) & lens, JADE, 3)
    p.decal(c.circle(lx - 5.0, ly - 5.0, 1.6) & lens, WHITE, 0)
    p.part(c.ring(lx, ly, 17.0, 3.4), BRONZE, 'ray', base=0, sep=True, tex='metal')
    p.decal(c.arc(lx, ly, 17.0, 1.2, 100, 200) & c.a, BRONZE, 2)
    p.sparkle(lx + 9.0, ly + 8.0, 1)


def spirit_spade_hd(p):
    """The spirit spade: a darkwood shaft on the diagonal with a hemp grip and a bronze collar, a jade blade edged
    bright at the upper right, a leaf tied at the grip."""
    k, c, fr = WK('earth'), p.c, TFRAME
    k['shaft'], k['grip'], k['wrap'] = DARKWOOD, HEMP, STRAW
    haft_hd(p, fr, k, 0.0, 36.0, 3.0, grip=(2.0, 16.0))
    fitting_hd(p, fr, k, 34.0, 38.5, 4.0, 0.8)
    blade = fr.prof(c, [(37.0, 4.0), (42.0, 10.5), (56.0, 11.0), (64.0, 6.0), (66.5, 0.0)])

    def half(t):
        return np.where(t < 42.0, 4.0 + 6.5 * np.clip((t - 37.0) / 5.0, 0, 1),
                        np.where(t < 56.0, 10.5 + 0.5 * (t - 42.0) / 14.0, np.clip(11.0 * (66.5 - t) / 10.5, 0.0, 11.0)))
    p.cylinder(fr, blade, half, JADE, ridge=True, sep=True, tex='jade', axis=48.0)
    t, w = fr.along(c)
    p.decal(blade & ~erode4(blade) & (t > 44.0) & (w < 0), JADE, 3)
    p.decal(blade & (t > 43.0) & (t < 46.0) & (np.abs(w) < 8.0), JADE, -2)
    stem_hd(p, [fr.P(16.0, -3.4), fr.P(15.0, -6.5), fr.P(13.0, -8.5)], (1.8, 1.4), LEAF)
    lx, ly = fr.P(14.0, -7.0)
    leaf_hd(p, lx, ly, 150, 10.0, 5.0, 0.05, 10)
    p.sparkle(*fr.P(60.0, -4.0), 1)


def verdant_dew_vial_hd(p):
    """The verdant dew vial: a tall green glass bottle stoppered in jade and tied with the Spirit grade's cord, one
    bright drop of dew hanging inside over the green, a faint light on it."""
    c = p.c
    vial_hd(p, GRADE_HD['spirit'], JADE, glass=M('mistjade', 'glass'), cork=M('deepjade', 'jade'), shape='tall', level=0.62)
    drop = S.drop(c, 32.0, 40.0, 4.2, 8.5)
    p.part(drop, M('cyan', 'gem'), 'sphere', base=1, sep=True, cx=32.0, cy=40.0, rx=4.2, ry=4.2)
    p.decal(c.circle(30.6, 38.4, 1.2) & drop, WHITE, 0)
    p.sparkle(41.0, 30.0, 1)
    p.glow('#8CF0B4', 0.9)


# ----------------------------------------------------------------------------- talismans
def strip_hd(p, tilt=0.0, x0=21.0, x1=43.0, y0=6.0, y1=58.0):
    """A paper talisman strip: yellow talisman paper with its laid lines, red border bars top and bottom, thin red
    rails down both sides."""
    c = p.c
    m = c.poly([(x0 + tilt, y0), (x1 + tilt, y0), (x1 - tilt, y1), (x0 - tilt, y1)])
    p.part(m, TALISMAN, 'bevel', base=0, sep=False, hw=1, sw=1, tex='paper', rim=False)
    for y in (y0 + 3.0, y1 - 5.0):
        p.decal(c.box(x0 + 2.0, y, x1 - 2.0, y + 2.2) & m, SEAL, 0)
    for x in (x0 + 2.4, x1 - 3.4):
        p.decal(c.box(x, y0 + 7.0, x + 1.0, y1 - 7.0) & m, SEAL, -1)
    return m


def seal_hd(p, x, y, r=3.0, mat=SEAL):
    """The maker's red seal at the foot of a talisman, a dot of gold in it."""
    c = p.c
    p.decal(c.circle(x, y, r), mat, 0)
    p.decal(c.box(x - 0.9, y - 0.9, x + 0.9, y + 0.9), GOLD, 1)


def glyph_talisman_hd(tid):
    ramp_id, pts = TALISMAN_GLYPHS[tid]

    def draw(p):
        strip_hd(p)
        ink = M(ramp_id)
        path = [(24.5 + x * 15.0, 14.0 + y * 30.0) for (x, y) in pts]
        p.line(path, ink, -1, 3.2)
        p.line(path, ink, 1, 1.4)
        seal_hd(p, 32.0, 50.5)
    return draw


def revival_talisman_hd(p):
    """The revival talisman: a rising phoenix-feather glyph in vermilion down the strip, a lotus seal in gold at its
    foot, the paper lit."""
    c = p.c
    m = strip_hd(p)
    p.line([(32.0, 12.0), (32.0, 42.0)], SEAL, 0, 2.6)
    for y in (18.0, 26.0, 34.0):
        p.line([(32.0, y), (25.0, y - 5.0)], SEAL, 0, 2.0)
        p.line([(32.0, y), (39.0, y - 5.0)], SEAL, 0, 2.0)
    p.line([(26.0, 40.0), (38.0, 40.0)], SEAL, -1, 2.0)
    lotus = c.circle(32.0, 49.5, 4.2) | c.leaf(32.0, 49.5, 150, 6.0, 3.0) | c.leaf(32.0, 49.5, 30, 6.0, 3.0)
    p.decal(lotus & m, GOLD, 0)
    p.decal(c.circle(32.0, 49.5, 1.6) & m, GOLD, 3)
    p.glow('#E5B84C', 0.7)


def escape_talisman_hd(p):
    """The escape talisman: the strip leaning as if snatched, three speed strokes and a running-cloud glyph in navy,
    a small cloud slipping off its foot."""
    c = p.c
    m = strip_hd(p, tilt=3.0)
    for i, y in enumerate((16.0, 22.0, 28.0)):
        p.line([(26.0 + i * 1.5, y), (39.0 - i * 1.5, y)], NAVY, -1, 2.2)
    p.line([(27.0, 36.0), (38.0, 36.0), (33.0, 42.0)], NAVY, -1, 2.2)
    seal_hd(p, 31.0, 50.0)
    cloud = c.ellipse(48.0, 51.0, 7.0, 4.2) | c.ellipse(53.0, 47.5, 5.2, 4.0) | c.ellipse(43.0, 48.5, 4.0, 3.2)
    p.part(cloud, CLOUD, 'ray_soft', base=1, sep=True, rim=False)
    p.decal(c.arc(53.0, 47.5, 3.0, 1.2, 60, 240) & cloud, CLOUD, -2)
    for y in (46.0, 54.0):
        p.part(c.box(35.0, y, 41.0, y + 1.4) & ~m, CLOUD, 'flat', base=1, sep=False, rim=False)


def return_charm_hd(p):
    """A return charm: a jade plaque hung from a red knot with its loop, a circling arrow carved in it, a red tassel."""
    c = p.c
    X, Y = XY(p)
    p.part(c.ring(32.0, 9.5, 4.0, 2.0) & c.box(0, 0, 64, 12.0), RED, 'ray_soft', base=0, sep=False, rim=False)
    knot = c.diamond(32.0, 17.5, 7.0, 5.5)
    p.part(knot, RED, 'ray', base=0, sep=True, rim=False, tex='cloth', axis=45)
    p.line([(28.0, 17.5), (32.0, 13.5), (36.0, 17.5), (32.0, 21.5), (28.0, 17.5)], RED, 2, 1.0)
    p.line([(30.0, 17.5), (34.0, 17.5)], RED, -2, 1.0)
    tk = dict(tassel=RED, bead=GOLD, lv=1)
    tassel_hd(p, tk, 32.0, 50.0, 1.4)
    plaque = c.rrect(21.0, 22.0, 43.0, 50.0, 3.0)
    p.part(plaque, JADE, 'ray', base=0, sep=True, tex='jade')
    p.decal(plaque & ~erode4(plaque) & (X + Y < 60), JADE, 2)
    arr = c.arc(32.0, 36.0, 7.6, 2.6, 50, 330) & plaque
    head = c.poly([(35.0, 25.5), (42.0, 29.5), (35.0, 33.5)]) & plaque
    p.decal(arr | head, JADE, -3)
    p.decal(shift(arr | head, -1, -1) & ~(arr | head) & plaque, JADE, 2)
    p.sparkle(24.0, 25.0, 1)


def cinnabar_hd(p):
    """Cinnabar: red mercury ground to a heap of powder in a shallow porcelain dish, its grains catching the light."""
    well = es_dish_hd(p, dict(dish=PORCELAIN, rim=None))
    heap = heap_hd(p, M('seal'), top=(31.0, 24.0), rx=19.0, base_y=46.5, dark=((24, 38), (38, 40), (30, 43)), light=((28, 30), (34, 34), (26, 35)))
    p.decal(heap & ~well & (p.c.Y / p.s > 45), M('seal'), -2)
    p.sparkle(30.0, 29.0, 0)


def beast_blood_ink_hd(p):
    """Beast-blood ink: a squat clay pot, the ink dark red at its mouth, a bamboo brush lying across it with its tip
    stained."""
    c = p.c
    pot = c.ellipse(30.0, 40.0, 20.0, 15.0) | c.box(19.0, 26.0, 41.0, 32.0)
    p.part(pot, CLAY, 'sphere', base=0, sep=True, cx=25.0, cy=34.0, rx=24.0, ry=20.0, tex='clay')
    p.part(c.box(17.0, 25.0, 43.0, 29.0), CLAY, 'vgrad', base=1, sep=True)
    mouth = c.ellipse(30.0, 26.5, 11.0, 3.6)
    blood = mat7(Ramp(['#2A0A0E', '#561420', '#8A2230', '#C0463E', '#F0A070'], '#12050A'), 'glass')
    p.part(mouth, blood, 'ray_soft', base=-1, sep=True, rim=False)
    p.decal(c.ellipse(27.0, 26.0, 5.0, 1.4) & mouth, blood, 1)
    fr = Frame((8.0, 16.0), -22.0)
    shaft = fr.prof(c, [(0.0, 2.2), (34.0, 2.2)])
    p.cylinder(fr, shaft, 2.2, BAMBOO, sep=True, tex='wood', axis=-22.0)
    for t0 in (12.0, 24.0):
        p.decal(fr.prof(c, [(t0 - 0.5, 2.3), (t0 + 0.5, 2.3)]) & shaft, BAMBOO, -2)
    p.part(fr.prof(c, [(33.5, 2.4), (37.0, 2.6)]), BRONZE, 'ray', base=0, sep=True, tex='metal')
    tuft = fr.prof(c, [(37.0, 2.4), (44.0, 2.0), (50.0, 0.4)])
    p.cylinder(fr, tuft, lambda t: np.clip(2.4 - 2.0 * (t - 37.0) / 13.0, 0.4, 2.4), M('bone', 'porcelain'), sep=True)
    t, w = fr.along(c)
    p.decal(tuft & (t > 45.0), blood, 0)
    dx, dy = fr.P(50.5, 2.0)
    p.decal(c.circle(dx, dy, 1.3), blood, 0, only_on=False)


def spirit_paper_hd(p):
    """Spirit paper: a stack of talisman sheets steeped in Mist Lotus, a pale blue Qi breathing off the top sheet."""
    c = p.c
    for i, (y, t) in enumerate(((40.0, 2.0), (30.0, 0.0), (20.0, -2.0))):
        sheet = c.poly([(13.0 + t, y), (49.0 + t, y - 4.0), (51.0 + t, y + 12.0), (15.0 + t, y + 16.0)])
        p.part(sheet, TALISMAN, 'bevel', base=0 if i == 2 else -1, sep=True, hw=1, sw=1, tex='paper', rim=False)
    top = c.poly([(11.0, 20.0), (47.0, 16.0), (49.0, 32.0), (13.0, 36.0)])
    p.decal(c.box(18.0, 26.0, 42.0, 28.4) & top, SKY, 0)
    p.decal(c.box(20.0, 22.0, 30.0, 23.6) & top, SEAL, 0)
    for (x, y, r) in ((17.0, 11.0, 2.0), (44.0, 8.0, 2.4), (54.0, 17.0, 1.8), (30.0, 6.0, 1.4)):
        m = c.circle(x, y, r)
        p.part(m, SKY, 'sphere', base=1, sep=False, rim=False)
        p.decal(c.circle(x - r * 0.4, y - r * 0.4, 0.6) & m, SKY, 3)
    p.glow('#C8E2F1', 0.4)


def shattered_moon_blade_hd(p):
    """The Shattered Moon Blade: a pale jian in three pieces laid along the diagonal, the hilt with its gold guard at
    the lower left, the moonlight still in the steel."""
    c, fr = p.c, Frame((6.5, 57.5), 45.0)
    steel = M('silver')
    k = dict(tassel=M('sky', 'silk'), bead=GOLD, lv=3, grip=DARKWOOD, wrap=M('leather'), guard=GOLD, blade=steel, gem=None, glow=None, grade='heaven')
    grip_hd(p, fr, k, 3.0, 17.0, 3.2)
    fitting_hd(p, fr, k, 1.0, 4.5, 4.0, 1.0)
    t, w = fr.along(c)
    for (t0, t1, tip) in ((21.0, 32.0, None), (36.5, 50.0, None), (54.5, 66.0, 74.0)):
        hw = 4.4
        prof = [(t0, hw * 0.6), (t0 + 1.5, hw), (t1, hw)] + ([(tip, 0.0)] if tip else [(t1 + 1.2, hw * 0.55)])
        m = fr.prof(c, prof)
        if tip:
            half = (lambda tt: np.where(tt > t1, np.clip(hw * (tip - tt) / (tip - t1), 0.0, hw), hw))
        else:
            half = hw
        p.cylinder(fr, m, half, steel, ridge=True, sep=True, tex='metal', axis=45.0)
        p.decal(m & (np.abs(w) < 0.7) & (t > t0 + 2) & (t < t1 - 1), steel, 3)
    p.part(fr.prof(c, [(17.5, 3.6), (19.0, 7.8), (20.5, 8.6), (21.5, 3.8)]), GOLD, 'ray', base=0, sep=True, tex='metal')
    p.sparkle(*fr.P(61.0, -0.6), 1)
    p.sparkle(*fr.P(44.0, 0.6), 0)
    p.glow('#CFE3FF', 0.8)


OFFER_HD = {'common': dict(dish=BRONZE, rim=None), 'earth': dict(dish=JADE, rim=GOLD), 'heaven': dict(dish=SILVER, rim=SKY)}


def offering_hd(grade):
    """A bonding offering on a footed dish: three peaches on bronze (Common), a wax root with berries on jade with a
    gold rim (Earth), a Qi orb in clouds on silver with a sky rim and a light (Heaven)."""
    def draw(p):
        c = p.c
        es_dish_hd(p, OFFER_HD[grade])
        if grade == 'common':
            for (x, y, r) in ((21.0, 36.0, 8.0), (43.0, 36.0, 8.0), (32.0, 27.0, 8.5)):
                m = c.circle(x, y, r) | c.poly([(x - r * 0.7, y - r * 0.6), (x + r * 0.7, y - r * 0.6), (x, y - r * 1.25)])
                p.part(m, PINK, 'sphere', base=0, sep=True, cx=x, cy=y, rx=r, ry=r, spec=(x - r * 0.4, y - r * 0.45))
                p.decal(c.circle(x + r * 0.3, y + r * 0.2, r * 0.45) & m, M('red', 'porcelain'), 0)
                leaf_hd(p, x + 1.0, y - r * 1.15, 25, 7.0, 3.4, 0.05, 10)
        elif grade == 'earth':
            root = c.ellipse(32.0, 33.0, 11.0, 9.5)
            p.part(root, WAX, 'sphere', base=0, sep=True, cx=29.0, cy=30.0, rx=13.0, ry=12.0)
            for pts in (((24.0, 36.0), (17.0, 42.0)), ((40.0, 36.0), (47.0, 42.0)), ((32.0, 41.0), (33.0, 45.0))):
                p.decal(lmask(p, pts) & c.a, WAX, -2)
            for pts in (((21.0, 39.0), (14.0, 44.0)), ((43.0, 39.0), (50.0, 44.0))):
                p.part(c.polyline(pts, 1.6) & ~c.a, WAX, 'flat', base=-1, sep=True, rim=False)
            stem_hd(p, [(32.0, 24.0), (32.0, 19.0), (32.0, 15.0)], (2.2, 1.6))
            for ang, L in ((140, 12.0), (90, 11.0), (40, 12.0)):
                leaf_hd(p, 32.0, 17.0, ang, L, 5.6, 0.0, 10)
            for (x, y) in ((17.0, 37.0), (47.0, 37.0)):
                m = c.circle(x, y, 4.2)
                p.part(m, M('red', 'porcelain'), 'sphere', base=0, sep=True, spec=(x - 1.6, y - 1.6))
        else:
            for (x, y, rx, ry) in ((15.0, 39.0, 7.0, 4.4), (49.0, 39.0, 7.0, 4.4), (22.0, 43.0, 5.0, 3.0), (42.0, 43.0, 5.0, 3.0)):
                p.part(c.ellipse(x, y, rx, ry), CLOUD, 'ray_soft', base=1, sep=True, rim=False)
            mcore_hd(p, 32.0, 29.0, 13.0, QI, heart=[(c.circle(32.0, 29.0, 3.4), 2), (c.circle(31.0, 28.0, 1.4), 3)], swirl=True)
            p.sparkle(46.0, 16.0, 2)
            p.glow('#AFC9D1', 0.7)
    return draw


def purifying_offering_hd(p):
    """A purifying offering: a cone of salt on a lotus leaf with two incense sticks stood in it, their smoke rising,
    a pale light on the salt."""
    c = p.c
    leaf = c.ellipse(32.0, 47.0, 25.0, 10.0)
    p.part(leaf, LEAF, 'ray', base=0, sep=True, rim=False)
    for a in range(10, 360, 40):
        p.decal(lmask(p, [(32.0, 47.0), (32.0 + 23.0 * math.cos(math.radians(a)), 47.0 - 9.0 * math.sin(math.radians(a)))]) & erode4(leaf), LEAF, -2)
    p.decal(c.circle(32.0, 47.0, 2.0) & leaf, LEAF, -3)
    for (x, top) in ((20.0, 22.0), (44.0, 20.0)):
        p.part(c.box(x - 1.0, top, x + 1.0, 46.0), RED, 'flat', base=0, sep=True, rim=False)
        p.decal(c.box(x - 1.0, top, x + 1.0, top + 1.6), M('fire'), 2)
        smoke = c.polyline(S.curve_pts((x, top - 2.0), (x - 6.0, top - 8.0), (x + 2.0, top - 14.0), 10), 1.8)
        p.part(smoke & ~c.a, CLOUD, 'flat', base=1, sep=False, rim=False)
    heap = heap_hd(p, PEARL, top=(32.0, 24.0), rx=15.0, base_y=45.0, light=((28, 32), (34, 36)))
    p.decal(heap & (c.Y / p.s > 44.0) & ~erode4(heap), PEARL, -2)
    p.sparkle(35.0, 29.0, 1)
    p.glow('#E8F4FF', 0.5)


# ----------------------------------------------------------------------------- the family's table
PICKS = ('old_pickaxe', 'copper_pick', 'iron_pickaxe', 'jadeiron_pick', 'cloudsteel_pick', 'mystic_pick', 'stormsteel_pick', 'sunglass_pick', 'driftglass_pick')
SICKLES = ('herb_sickle', 'copper_sickle', 'iron_sickle', 'jadeiron_sickle', 'cloudsteel_sickle', 'mystic_sickle', 'stormsteel_sickle', 'sunglass_sickle',
           'driftglass_sickle')
RODS = ('bamboo_rod', 'reedline_rod', 'ironwood_rod', 'jadeline_rod', 'cloud_rod', 'mystic_rod', 'storm_rod', 'sunglass_rod', 'starline_rod')
NETS = ('reed_net', 'hemp_net', 'cord_net', 'silk_net', 'cloudsilk_net', 'mystic_net', 'storm_net', 'sunglass_net', 'starsilk_net')
LADDERS_HD = [(PICKS, pick_hd), (SICKLES, sickle_hd), (RODS, rod_hd), (NETS, net_hd)]

TOOLS_HD = (
    [(ids[t], (lambda fn, tt: lambda p: fn(p, tt))(fn, t)) for ids, fn in LADDERS_HD for t in range(9)]
    + [(tier + '_snare_kit', (lambda tt: lambda p: snare_hd(p, tt))(tier)) for tier in ('hemp', 'iron', 'silk', 'star')]
    + [('clay_pot', clay_pot_hd), ('bronze_furnace', bronze_furnace_hd), ('forge_hammer', forge_hammer_hd), ('formation_kit', formation_kit_hd),
       ('needle_case', needle_case_hd), ('appraiser_loupe', appraiser_loupe_hd), ('spirit_spade', spirit_spade_hd), ('verdant_dew_vial', verdant_dew_vial_hd)]
    + [(tid, glyph_talisman_hd(tid)) for tid in TALISMAN_GLYPHS]
    + [('revival_talisman', revival_talisman_hd), ('return_charm', return_charm_hd), ('escape_talisman', escape_talisman_hd),
       ('cinnabar', cinnabar_hd), ('beast_blood_ink', beast_blood_ink_hd), ('spirit_paper', spirit_paper_hd),
       ('shattered_moon_blade', shattered_moon_blade_hd), ('purifying_offering', purifying_offering_hd)]
    + [('bonding_offering_' + g, offering_hd(g)) for g in ('common', 'earth', 'heaven')]
)

TALISMAN_IDS = set(TALISMAN_GLYPHS) | {'revival_talisman', 'return_charm', 'escape_talisman', 'cinnabar', 'beast_blood_ink', 'spirit_paper',
                                       'shattered_moon_blade', 'purifying_offering', 'bonding_offering_common', 'bonding_offering_earth',
                                       'bonding_offering_heaven'}
for _id, _draw in TOOLS_HD:
    register(FAM, _id, _draw, 'talismans' if _id in TALISMAN_IDS else 'tools')
    hd(_id, _draw)
