"""The study's icons, described once in icon space and rendered by either painter.

Items, equipment and techniques are described in a 64-px space (object inside a
4-px margin, glows may use it); HUD glyphs in a 32-px space. Every function takes a
painter `p` (see study_lib) and returns it.
"""
from __future__ import annotations

import math

import numpy as np

from study_lib import Mat, M, mat7, solid, WHITE, dilate4, erode4, shift
from pix import Ramp, mix, INK
from palette import R

# ----------------------------------------------------------------------------- materials
IRON = M('iron', 'metal')
BRONZE = M('bronze', 'metal')
GOLD = M('gold', 'gold')
SILVER = M('silver', 'metal')
STORM = M('storm', 'metal')
JADE = M('jade', 'jade')
DEEPJADE = M('deepjade', 'cloth')
JADEIRON = M('jadeiron', 'metal')
LEATHER = M('leather', 'leather')
DARKWOOD = M('darkwood', 'wood')
WOOD = M('wood', 'wood')
RED = M('red', 'silk')
NAVY = M('navy', 'silk')
CLAY = M('clay', 'clay')
PAPER = M('paper', 'paper')
STRAW = M('straw', 'matte')
MISTJADE = M('mistjade', 'porcelain')
VIOLET = M('violet', 'gem')
CYAN = M('cyan', 'gem')
EMBER = M('ember', 'gem')
STARLIGHT = M('starlight', 'gem')
NIGHTSTEEL = mat7(Ramp(['#151A2E', '#22304C', '#3A4E78', '#6478A8', '#B8C6E6'], '#080B16'), 'metal')
PLUM = M('plum', 'silk')
TALISMAN = M('talisman', 'paper')
QI = M('qi', 'light')
SAND = M('sand', 'matte')
INKM = M('ink', 'ink')
BONE = M('bone', 'matte')
SHADOWSILK = M('shadow', 'silk')

VIOLET_GLASS = mat7(Ramp(['#2A1E4A', '#4A3A80', '#7A66B8', '#B4A6E0', '#E6DEFF'], '#120C24'), 'glass')
TEAL_GLASS = mat7(Ramp(['#0C3A40', '#166A6E', '#2AA6A4', '#78DCD2', '#D2FAF2'], '#051A1C'), 'glass')
NEBULA_TEAL = mat7(Ramp(['#0A2436', '#123E52', '#1E6474', '#3A9498', '#8CD4C8'], '#041018'), 'matte')
NEBULA_MAGENTA = mat7(Ramp(['#3A1240', '#6A2470', '#A444A0', '#D67CCC', '#F6C4EE'], '#18061C'), 'light')
SEED_HEAD = mat7(Ramp(['#443A12', '#766A22', '#B0A23E', '#DCD078', '#F6F0C0'], '#1C1806'), 'matte')
PETAL = mat7(R['starlight'], 'silk')

EL = {  # disc ramp, mark ramp (from families/techniques.py)
    'fire': (['#2A0A08', '#4E140E', '#7C2414', '#B0401E', '#E27436'], ['#9A3012', '#DA6224', '#FFB850', '#FFEAA6', '#FFFFFF']),
    'jade': (['#082220', '#0F3C38', '#185E56', '#27887A', '#56BCA8'], ['#2C7A6C', '#58B4A0', '#A8EEDA', '#E2FFF4', '#FFFFFF']),
    'metal': (['#121A24', '#212E3C', '#344658', '#50667C', '#8098AE'], ['#56687C', '#8A9CB0', '#CBD8E4', '#F0F6FA', '#FFFFFF']),
}
HUD_GOLD = mat7(Ramp(['#6E4A1C', '#9A6A35', '#E5B84C', '#FFE6A1', '#FFF6D6'], '#071015'), 'gold')

GRADE_COL = {'plain': '#b9b2a0', 'common': '#e8e1cf', 'earth': '#67d67a', 'heaven': '#6fb8f0', 'mystic': '#b07ce8',
             'spirit': '#5ee0e8', 'sage': '#d8c27a', 'sovereign': '#e8a24c', 'will': '#f3e3a6', 'sphere': '#8f7ae0'}

# jian kits: blade, guard, grip, wrap, pommel, gem, tassel, glow
JIAN_KITS = {
    'common': dict(blade=IRON, guard=BRONZE, grip=LEATHER, wrap=DARKWOOD, pommel=BRONZE, gem=None, tassel=RED, glow=None),
    'spirit': dict(blade=STORM, guard=SILVER, grip=NAVY, wrap=M('indigo', 'silk'), pommel=SILVER, gem=CYAN, tassel=M('sky', 'silk'),
                   glow=('#7FD4FF', 0.9)),
    'sage': dict(blade=GOLD, guard=JADE, grip=CLAY, wrap=RED, pommel=JADE, gem=EMBER, tassel=RED, glow=('#FFC870', 0.9)),
    'will': dict(blade=NIGHTSTEEL, guard=GOLD, grip=SHADOWSILK, wrap=DARKWOOD, pommel=GOLD, gem=STARLIGHT, tassel=STARLIGHT,
                 glow=('#F3E3A6', 1.0)),
}


# ----------------------------------------------------------------------------- frames
class Frame:
    """A local axis: P(t, w) = p0 + u t + v w, with u along `angle` (0 right, 90 up) and v to its screen-right."""

    def __init__(self, p0, angle):
        a = math.radians(angle)
        self.p0 = p0
        self.u = (math.cos(a), -math.sin(a))
        self.v = (-self.u[1], self.u[0])

    def P(self, t, w):
        return (self.p0[0] + self.u[0] * t + self.v[0] * w, self.p0[1] + self.u[1] * t + self.v[1] * w)

    def prof(self, c, pts):
        """Symmetric profile (t, halfwidth) -> polygon mask."""
        return c.poly([self.P(t, hw) for t, hw in pts] + [self.P(t, -hw) for t, hw in pts[::-1]])

    def field(self, c, hw_of_t):
        """(t, f) per pixel: f in [0, 1] across the part, 0 on the v<0 side."""
        t, w = c.field_along(self.p0, self.P(1.0, 0.0))
        hw = hw_of_t(t)
        f = (w + hw) / np.maximum(2 * hw, 1e-3)
        return t, f

    def lit_first(self):
        """True when the v<0 side is the upper-left (lit) side."""
        return (-self.v[0] - self.v[1]) > 0


def cyl_field(p, fr, mask, hw_of_t, mat, base=0, ridge=False, **kw):
    """Paint a cylinder- or blade-like part with the field mode, lit side first."""
    t, f = fr.field(p.c, hw_of_t)
    vdir = fr.v
    if not fr.lit_first():
        f = 1.0 - f
        vdir = (-fr.v[0], -fr.v[1])
    bands = None if ridge else ((0.18, 2), (0.42, 1), (0.66, 0), (0.86, -1), (9, -2))
    return p.part(mask, mat, 'field', base=base, field=f, bands=bands, vdir=vdir, ridge=ridge, **kw)


# ============================================================================= jian
def jian(p, grade='common'):
    k = JIAN_KITS[grade]
    c = p.c
    fr = Frame((6.5, 57.5), 45.0)
    TIP = 71.0
    # tassel from the pommel: a knot and two hanging strands
    tas = c.taper((8.5, 55.5), (2.5, 57.0), (4.0, 62.0), 3.0, 1.6) | c.taper((8.5, 55.5), (5.0, 59.0), (9.0, 62.5), 2.4, 1.2)
    p.part(tas, k['tassel'], 'ray_soft', base=0, sep=False, rim=False)
    p.part(c.circle(8.8, 55.6, 2.3), k['tassel'], 'sphere', base=1, sep=True, rim=False)
    # pommel and grip
    pom = fr.prof(c, [(1.5, 2.6), (2.8, 4.2), (6.2, 4.2), (7.2, 3.3)])
    cyl_field(p, fr, pom, lambda t: np.full(t.shape, 4.2), k['pommel'], sep=True)
    grip = fr.prof(c, [(6.8, 3.3), (22.0, 3.3)])
    cyl_field(p, fr, grip, lambda t: np.full(t.shape, 3.3), k['grip'], sep=True)
    t, w = c.field_along(fr.p0, fr.P(1, 0))
    wrap = grip & (np.floor((t + 0.35 * w) / 3.4).astype(int) % 2 == 0)
    p.decal(wrap & erode4(grip), k['wrap'], -1)
    p.decal(wrap & erode4(grip) & (w < -1.6), k['wrap'], 1)
    # blade with a ridge and a fuller; the guard's wings over its root
    HW = 4.4
    T0, T1 = 25.0, 58.0

    def hw_blade(t):
        return np.where(t > T1, np.clip(HW * (TIP - t) / (TIP - T1), 0.0, HW), HW)
    blade = fr.prof(c, [(T0, HW), (T1, HW), (TIP, 0.0)])
    cyl_field(p, fr, blade, hw_blade, k['blade'], ridge=True, sep=True, tex='metal')
    # fuller and the grade's blade work
    fuller = fr.prof(c, [(31.0, 0.7), (56.0, 0.7)]) & blade
    if grade == 'common':
        p.decal(fuller, k['blade'], -1)
    elif grade == 'spirit':
        pts = [fr.P(31 + i * 3.2, 1.2 if i % 2 else -1.2) for i in range(9)]
        p.line(pts, CYAN, 2, 1.2)
    elif grade == 'sage':
        p.decal(fuller, EMBER, 0)
        for tt in range(33, 56, 5):
            p.decal(c.circle(*fr.P(tt, 0.0), 1.1), EMBER, 2)
    elif grade == 'will':
        p.decal(fuller, NIGHTSTEEL, -2)
        for tt in range(32, 58, 4):
            p.decal(c.circle(*fr.P(tt, 0.0), 0.9), STARLIGHT, 2)
        edge = blade & ~fr.prof(c, [(T0, HW - 1.2), (T1, HW - 1.2), (TIP - 1.5, 0.0)])
        p.decal(edge & (w < 0), STARLIGHT, 1)
    guard = fr.prof(c, [(21.0, 3.8), (22.5, 8.4), (24.2, 10.2), (26.0, 9.2), (28.0, 5.6), (29.0, 3.9)])
    p.part(guard, k['guard'], 'ray', base=0, sep=True, tex='metal')
    p.line([fr.P(23.2, -7.0), fr.P(23.2, 7.0)], k['guard'], 2, 1.0)
    if k['gem'] is not None:
        p.part(c.circle(*fr.P(24.6, 0.0), 2.5), k['gem'], 'sphere', base=1, sep=True, spec=fr.P(23.8, -0.9))
    else:
        p.part(c.circle(*fr.P(24.6, 0.0), 2.0), k['pommel'], 'sphere', base=0, sep=True)
    p.sparkle(*fr.P(64.0, -0.6), 1, WHITE)
    if k['glow']:
        p.glow(*k['glow'])
    p.grade = grade
    return p


# ============================================================================= bell (the Warden's hand-bell)
def bell(p):
    c = p.c
    fr = Frame((30.0, 30.0), -45.0)     # u runs down-right: handle up-left, mouth down-right
    K = 1.28
    # cord loop, handle, jade collar
    lx, ly = fr.P(-24.5 * K, 0.0)
    p.part(c.ring(lx, ly, 3.9, 2.0), RED, 'ray_soft', base=0, sep=False, rim=False)
    handle = fr.prof(c, [(-23.0 * K, 2.0), (-21.0 * K, 3.2), (-19.0 * K, 2.5), (-15.0 * K, 2.3), (-12.0 * K, 2.6), (-9.5 * K, 2.6)])
    cyl_field(p, fr, handle, lambda t: np.full(t.shape, 2.6), DARKWOOD, sep=True, tex='wood', axis=-45.0)
    collar = fr.prof(c, [(-10.5 * K, 3.9), (-6.0 * K, 3.9)])
    cyl_field(p, fr, collar, lambda t: np.full(t.shape, 3.9), JADE, sep=True, tex='jade')
    p.line([fr.P(-8.2 * K, -3.7), fr.P(-8.2 * K, 3.7)], JADE, -2, 1.0)
    # the bell: crown, waist, skirt and lip
    prof = [(-7.0 * K, 2.6), (-5.5 * K, 5.4), (-3.0 * K, 7.2), (0.0, 8.2), (4.0 * K, 8.8), (8.0 * K, 9.9),
            (11.0 * K, 11.8), (13.0 * K, 13.6), (14.5 * K, 14.2)]
    body = fr.prof(c, prof)

    def hw_bell(t):
        ts = np.array([q[0] for q in prof])
        hs = np.array([q[1] for q in prof])
        return np.interp(t, ts, hs)
    cyl_field(p, fr, body, hw_bell, BRONZE, sep=True, tex='metal')
    # cast bands and a cloud scroll engraved round the waist
    t, w = c.field_along(fr.p0, fr.P(1, 0))
    for tt, lv in ((2.0 * K, -2), (2.9 * K, 1), (9.5 * K, -2), (10.4 * K, 1)):
        p.decal(body & (t >= tt) & (t < tt + 0.9) & (np.abs(w) < hw_bell(t) - 0.8), BRONZE, lv)
    scroll = c.empty()
    for i in range(5):
        cx_, cy_ = fr.P(6.0 * K, -6.0 + i * 3.0)
        scroll |= c.arc(cx_, cy_, 1.3, 0.8, 0, 270)
    p.decal(scroll & body, BRONZE, -2)
    lip = fr.prof(c, [(14.0 * K, 14.7), (16.4 * K, 14.7)])
    cyl_field(p, fr, lip, lambda t: np.full(t.shape, 14.7), BRONZE, base=1, sep=True)
    # the mouth and the clapper
    mouth = fr.prof(c, [(15.6 * K, 12.7), (18.4 * K, 11.8)]) & ~lip
    p.part(mouth, INKM, 'flat', base=1, sep=True, rim=False)
    mx, my = fr.P(18.2 * K, 0.0)
    p.part(c.circle(mx, my, 3.8), DARKWOOD, 'sphere', base=0, sep=True, spec=(mx - 1.2, my - 1.2))
    p.sparkle(*fr.P(-1.5 * K, -5.0), 1, WHITE)
    p.glow('#FFC870', 0.8)
    p.grade = 'sage'
    return p


# ============================================================================= robe (jadeiron, Earth)
def robe(p):
    c = p.c
    cloth, trim, sash, plate, gem = DEEPJADE, JADE, BRONZE, JADEIRON, JADE
    body = c.poly([(20, 8), (44, 8), (46, 28), (52, 58), (12, 58), (18, 28)])
    sl = c.poly([(20, 10), (8, 16), (3, 44), (17, 46), (20, 28)])
    sr = c.poly([(44, 10), (56, 16), (61, 44), (47, 46), (44, 28)])
    p.part(sl, cloth, 'ray', base=-1, sep=False, tex='cloth', axis=100.0, rim=False)
    p.part(sr, cloth, 'ray', base=-1, sep=False, tex='cloth', axis=80.0, rim=False)
    p.part(body, cloth, 'ray', base=0, sep=True, tex='cloth', axis=90.0, rim=False)
    for s_ in (sl, sr):
        p.part(s_ & c.box(0, 39, 64, 64), trim, 'ray_soft', base=0, sep=True, tex='jade', rim=False)
    # inner collar and the crossed lapels
    p.part(c.poly([(26, 8), (38, 8), (32, 18)]), PAPER, 'flat', base=0, sep=True, rim=False)
    p.part(c.polyline([(39, 9), (33, 17)], 4.2), trim, 'ray_soft', base=-1, sep=True, rim=False)
    p.part(c.polyline([(25, 9), (39, 29)], 4.6), trim, 'ray_soft', base=0, sep=True, rim=False)
    # the sash and its hanging ties
    p.part(c.box(18, 28, 46, 33) & body, sash, 'vgrad', base=0, sep=True, tex='metal', rim=False)
    p.part(c.polyline([(24, 33), (24, 45)], 2.0) | c.polyline([(28, 33), (28, 43)], 2.0), sash, 'flat', base=1, sep=True, rim=False)
    # hem
    p.part(body & c.box(0, 54, 64, 64), trim, 'ray_soft', base=0, sep=True, tex='jade', rim=False)
    # skirt folds
    for x0, x1 in ((22, 20), (32, 32), (42, 44)):
        p.line([(x0, 34), (x1, 53)], cloth, -1, 1.0)
        p.line([(x0 + 1, 34), (x1 + 1, 53)], cloth, 1, 1.0)
    # shoulder plates of jadeiron with a rivet line, and the chest scales
    for (x0, x1) in ((5, 19), (45, 59)):
        pad = c.rrect(x0, 12, x1, 23, 2.5)
        p.part(pad, plate, 'bevel', base=0, sep=True, hw=2, sw=2, tex='metal')
        p.line([(x0 + 2, 17.5), (x1 - 2, 17.5)], plate, -2, 1.0)
        for x in range(x0 + 3, x1 - 1, 4):
            p.decal(c.circle(x, 15, 0.7), plate, 2)
    chest = c.box(21, 18, 43, 27) & body
    rows = c.empty()
    for y in range(18, 27, 3):
        for x in range(21, 43, 4):
            rows |= c.arc(x + 2 + (2 if (y // 3) % 2 else 0), y + 1.5, 2.0, 0.9, 180, 360)
    p.decal(rows & chest, plate, 1)
    p.part(c.diamond(32, 31.5, 3.6, 3.6), gem, 'ray', base=1, sep=True, spec=(31.0, 30.2))
    p.grade = 'earth'
    return p


# ============================================================================= pills
def _heart(c, cx, cy, r):
    return c.circle(cx - r * 0.55, cy - r * 0.2, r * 0.6) | c.circle(cx + r * 0.55, cy - r * 0.2, r * 0.6) | \
        c.poly([(cx - r * 1.1, cy), (cx + r * 1.1, cy), (cx, cy + r * 1.15)])


def _label(p, x0, y0, x1, y1):
    c = p.c
    lab = c.rrect(x0, y0, x1, y1, 1.5)
    p.part(lab, PAPER, 'bevel', base=0, sep=True, hw=1, sw=1, tex='paper', rim=False)
    return lab


def healing_pill(p):
    c = p.c
    body = c.ellipse(26, 39, 21, 19) | c.box(18, 16, 34, 26)
    p.part(body, CLAY, 'sphere', base=0, sep=False, cx=23, cy=34, rx=25, ry=25, tex='clay')
    p.part(c.box(5, 24, 47, 28) & body, BRONZE, 'vgrad', base=0, sep=True, tex='metal')
    p.part(c.box(15, 14, 37, 18), BRONZE, 'vgrad', base=1, sep=True, tex='metal')
    cap = c.ellipse(25.5, 10, 9.8, 5.6)
    p.part(cap, RED, 'ray', base=0, sep=True, rim=False)
    p.part(c.box(17, 12, 34, 14) & cap, STRAW, 'flat', base=0, sep=True, rim=False)
    p.line([(20, 7), (27, 6), (32, 8)], RED, -1, 1.0)
    lab = _label(p, 16, 31, 36, 49)
    p.decal(_heart(c, 26, 39, 4.2) & lab, RED, 0)
    p.decal(c.circle(23.6, 38.2, 1.0) & lab, RED, 2)
    pill = c.circle(50, 50, 9.6)
    p.part(pill, RED, 'sphere', base=0, sep=True, spec=(46.5, 46.5))
    p.grade = 'common'
    return p


def breakthrough_pill(p):
    c = p.c
    p.part(c.poly([(13, 58), (18, 50), (34, 50), (39, 58)]), GOLD, 'ray', base=0, sep=False, tex='metal')
    body = c.ellipse(26, 36.5, 21, 17.5)
    p.part(body, MISTJADE, 'sphere', base=0, sep=True, cx=23, cy=31, rx=25, ry=22, tex='glass')
    for y in (21.5, 49.5):
        p.part(c.box(4, y, 48, y + 1.8) & body, GOLD, 'flat', base=1, sep=True, rim=False)
    lid = (c.ellipse(26, 19, 15, 6.2) & c.box(0, 0, 64, 22)) | c.box(11, 18, 41, 21)
    p.part(lid, GOLD, 'ray', base=1, sep=True, tex='metal')
    p.part(c.diamond(26, 10, 4.4, 6.4), VIOLET, 'ray', base=1, sep=True, spec=(24.6, 7.6))
    for x in (5.5, 46.5):
        p.part(c.ring(x, 32, 4.6, 2.1), GOLD, 'ray_soft', base=1, sep=True)
    lab = _label(p, 17, 28, 35, 45)
    knot = (c.ring(23, 36.5, 3.8, 1.7) | c.ring(29, 36.5, 3.8, 1.7)) & lab
    p.decal(knot, PLUM, -1)
    pill = c.circle(50, 50, 9.6)
    p.part(pill, GOLD, 'sphere', base=0, sep=True, spec=(46.5, 46.5), tex='metal')
    p.decal(c.ring(50, 50, 6.8, 1.4) & c.box(0, 50, 64, 64) & pill, GOLD, -2)
    p.glow('#B18DE2', 1.0)
    p.grade = 'mystic'
    return p


# ============================================================================= star lotus
def star_lotus(p):
    c = p.c
    pad = c.ellipse(32, 51, 28, 7.6)
    p.part(pad, NEBULA_TEAL, 'ray', base=0, sep=False, rim=False)
    p.line([(32, 49), (54, 49)], NEBULA_TEAL, -2, 1.0)
    p.line([(18, 47), (30, 45)], NEBULA_TEAL, 1, 1.0)
    bx, by = 32.0, 46.0
    back = [(bx - 2, by, 128, 28, 13.6, -0.06), (bx + 2, by, 52, 28, 13.6, 0.06), (bx, by + 1, 90, 31, 15.4, 0.0)]
    side = [(bx - 2, by, 160, 25, 12.4, -0.12), (bx + 2, by, 20, 25, 12.4, 0.12)]
    for (x, y, a, L, W, b) in back + side:
        m = c.leaf(x, y, a, L, W, b, tip_power=0.7)
        p.part(m, PETAL, 'ray', base=0, sep=True, tex='cloth', axis=a, rim=False)
        dx, dy = math.cos(math.radians(a)), -math.sin(math.radians(a))
        tip = c.circle(x + dx * L * 0.9, y + dy * L * 0.9, L * 0.3) & m
        p.decal(tip, PETAL, 2)
        p.line([(x + dx * 3, y + dy * 3), (x + dx * L * 0.7, y + dy * L * 0.7)], PETAL, -1, 1.0)
    head = c.ellipse(32, 33, 8.4, 4.8)
    p.part(head, SEED_HEAD, 'ray', base=0, sep=True, rim=False)
    for (x, y) in ((26, 32), (38, 32), (30, 30.5), (34, 30.5), (30, 34.5), (34, 34.5)):
        p.decal(c.circle(x, y, 1.0) & head, SEED_HEAD, -3)
    for (x, y, a) in ((30, 47, 116), (34, 47, 64)):
        m = c.leaf(x, y, a, 12.5, 10, 0.0, tip_power=0.7)
        p.part(m, PETAL, 'ray', base=0, sep=True, tex='cloth', axis=a, rim=False)
        p.decal(c.circle(x + math.cos(math.radians(a)) * 9, y - math.sin(math.radians(a)) * 9, 3.0) & m, PETAL, 2)
    ripple = (c.ellipse(44, 57, 13, 2.4) | c.ellipse(18, 56.5, 7, 2.0)) & ~pad
    p.part(ripple, NEBULA_MAGENTA, 'flat', base=0, sep=True, rim=False)
    p.decal(ripple & c.box(0, 0, 44, 64), NEBULA_MAGENTA, 1)
    p.sparkle(32, 32, 2, WHITE)
    p.sparkle(32, 7, 1, WHITE)
    p.glow('#F3E3A6', 0.6)
    p.grade = 'sage'
    return p


# ============================================================================= driftglass
def driftglass(p):
    c = p.c
    m = c.poly([(7, 35), (11, 25), (20, 19), (32, 17), (43, 19), (51, 24), (54, 33), (51, 42), (42, 49), (28, 51), (15, 49), (8, 43)])
    p.part(m, VIOLET_GLASS, 'sphere', base=0, sep=False, cx=30, cy=34, rx=26, ry=19, tex='glass')
    if p.style == 'A':
        teal = m & ((c.X + c.Y) / p.s >= 62)
        p.part(teal, TEAL_GLASS, 'sphere', base=0, sep=False, cx=31, cy=33, rx=24, ry=18, tex='glass')
    else:
        # the teal light seeps in from the far side: painted as soft bands, not a hard split
        teal = m & ((c.X + c.Y) / p.s >= 56)
        p.part(teal, TEAL_GLASS, 'sphere', base=0, sep=False, cx=31, cy=33, rx=24, ry=18, tex='glass')
        for k, thr in enumerate((56, 60, 64, 68)):
            band = m & ((c.X + c.Y) / p.s >= thr - 4) & ((c.X + c.Y) / p.s < thr)
            p.decal(band, VIOLET_GLASS, 1 - k // 2, alpha=0.82 - k * 0.2)
    # frosted skin on the lit rim, one wet gleam
    rim = m & ~erode4(erode4(m)) & ((c.X + c.Y) / p.s <= 50)
    p.decal(rim, VIOLET_GLASS, 1)
    p.line([(14, 27), (19, 22), (26, 20)], WHITE, 0, 1.2)
    p.decal(c.circle(16, 31, 0.9), WHITE, 0)
    bead = c.poly([(39, 51), (43, 44), (51, 42), (57, 46), (57, 54), (50, 58), (42, 57)])
    p.part(bead, TEAL_GLASS, 'sphere', base=0, sep=True, tex='glass')
    p.part(bead & ((c.X + c.Y) / p.s <= 92), VIOLET_GLASS, 'sphere', base=0, sep=False, cx=48, cy=50, rx=10, ry=9, tex='glass')
    p.decal(c.circle(45.5, 46, 1.0), WHITE, 0)
    p.sparkle(50, 30, 1, WHITE)
    p.glow('#9C8CE0', 0.45)
    p.grade = 'heaven'
    return p


# ============================================================================= jade scale
def _shield(c, sx, sy, hw, hh):
    top = sy - hh
    return c.poly([(sx - hw, top + hh * 0.18), (sx - hw * 0.5, top), (sx, top + hh * 0.12), (sx + hw * 0.5, top),
                   (sx + hw, top + hh * 0.18), (sx + hw * 0.92, sy + hh * 0.35), (sx, sy + hh), (sx - hw * 0.92, sy + hh * 0.35)])


def jade_scale(p):
    c = p.c
    m = _shield(c, 32, 32, 24, 26)
    p.part(m, JADE, 'ray', base=0, sep=False, tex='jade', bevel=4.0)
    for k in (1, 2):
        f = 1.0 - k * 0.3
        inner = _shield(c, 32, 32 + 52 * 0.1 * k, 24 * f, 26 * f)
        ridge = inner & ~erode4(inner) & c.box(0, 32 - 26 * 0.2 + 5.2 * k, 64, 64) & m
        if p.style == 'A':
            p.decal(ridge, JADE, -2)
            p.decal(shift(ridge, 0, 1) & m & ~ridge, JADE, 1)
        else:
            p.decal(c.polyline([(32 - 24 * f * 0.92, 32 + 5.2 * k + 26 * f * 0.35), (32, 32 + 5.2 * k + 26 * f), (32 + 24 * f * 0.92, 32 + 5.2 * k + 26 * f * 0.35)], 1.2) & m, JADE, -3, alpha=0.85)
            p.decal(c.polyline([(32 - 24 * f * 0.92, 33.2 + 5.2 * k + 26 * f * 0.35), (32, 33.2 + 5.2 * k + 26 * f), (32 + 24 * f * 0.92, 33.2 + 5.2 * k + 26 * f * 0.35)], 1.0) & m, JADE, 2, alpha=0.6)
    p.line([(17, 19), (16, 27)], JADE, 3, 1.4)
    p.line([(20, 16), (23, 15)], JADE, 3, 1.2)
    p.decal(c.ellipse(40, 44, 5, 3) & m, JADE, 2, alpha=0.6) if p.style == 'B' else p.decal(c.ellipse(40, 44, 5, 3) & erode4(erode4(m)), JADE, 1)
    p.sparkle(19, 22, 1, WHITE)
    p.glow('#67D6BD', 0.7)
    p.grade = 'earth'
    return p


# ============================================================================= manual (a closed scroll with an element tag)
def manual(p):
    c = p.c
    a, b = (13.0, 49.0), (46.0, 13.0)
    ang = math.degrees(math.atan2(-(b[1] - a[1]), b[0] - a[0]))
    fr = Frame(a, ang)
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    body = fr.prof(c, [(-2.0, 7.4), (L + 1.0, 7.4)])
    cyl_field(p, fr, body, lambda t: np.full(t.shape, 7.4), PAPER, sep=False, tex='paper')
    t, w = c.field_along(a, b)
    # the rolled edge (a spiral) at the near end, and the roller knob at the far end
    e = c.circle(b[0], b[1], 7.0)
    p.part(e, PAPER, 'flat', base=-1, sep=True, rim=False)
    p.decal(c.ring(b[0], b[1], 4.8, 1.2) & e, PAPER, -3)
    p.decal(c.ring(b[0], b[1], 2.2, 1.2) & e, PAPER, -3)
    p.part(c.circle(b[0] - 1.0, b[1] + 1.0, 2.2), DARKWOOD, 'sphere', base=0, sep=True)
    knob = c.circle(a[0] - 2.5, a[1] + 2.5, 5.6)
    p.part(knob, DARKWOOD, 'sphere', base=0, sep=True, tex='wood', axis=ang, spec=(a[0] - 4.5, a[1] + 0.5))
    # the tie band across the middle and the cord to the tag
    mt = L / 2.0
    band = fr.prof(c, [(mt - 2.4, 7.6), (mt + 2.4, 7.6)]) & (body | dilate4(body))
    p.part(band, RED, 'ray_soft', base=0, sep=True, rim=False)
    p.decal(fr.prof(c, [(mt - 0.5, 7.6), (mt + 0.5, 7.6)]) & band, RED, -2)
    kx, ky = fr.P(mt, 7.8)
    p.line([(kx, ky), (kx + 4, ky + 6), (40, 38)], RED, 0, 1.4, only_on=False)
    tag = c.rrect(33, 36, 56, 58, 1.8)
    p.part(tag, TALISMAN, 'bevel', base=0, sep=True, hw=1, sw=1, tex='paper', rim=False)
    p.decal(c.circle(44.5, 39.5, 1.1), TALISMAN, -3)
    # the water element: three waves
    for k, y in enumerate((44.0, 48.5, 53.0)):
        pts = [(36 + x, y + 1.4 * math.sin((x + k * 2) / 3.2)) for x in range(0, 18)]
        p.line(pts, QI, 1 if k else 2, 1.4)
    p.grade = 'earth'
    return p


# ============================================================================= technique emblems
def _emblem(p, element, secret=False):
    c = p.c
    disc_c, mark_c = EL[element]
    disc = mat7(Ramp(disc_c, '#05080B'), 'matte')
    mk = mat7(Ramp(mark_c, disc_c[0]), 'light')
    rim = GOLD if secret else mat7(Ramp(disc_c, '#05080B'), 'metal')
    outer = c.circle(32, 32, 30)
    p.part(outer, rim, 'sphere', base=-1, sep=False, rim=False)
    inner = c.circle(32, 32, 26)
    p.part(inner, disc, 'sphere', base=0, sep=True, bands=((0.9, 1), (0.55, 0), (0.1, -1), (-9, -2)), rim=False, gain=2.0)
    p.decal(inner & ~erode4(inner), disc, -3)
    p.decal(c.ring(32, 32, 27.6, 1.0), rim, 2, alpha=0.5) if p.style == 'B' else p.decal(c.ring(32, 32, 27.6, 1.0), rim, 1)
    return inner, mk, disc


def mark(p, m, mk, base=0, mode='ray', **kw):
    """A pale motion mark with its own dark keyline over the disc."""
    c = p.c
    ring = dilate4(m) & ~m
    p.decal(ring, mk.out, 0)
    return p.part(m, mk, mode, base=base, sep=False, rim=False, **kw)


def ember_burst(p):
    c = p.c
    inner, mk, d = _emblem(p, 'fire')
    pts = []
    for k in range(16):
        a = k * math.pi / 8 + 0.2
        r = 22 if k % 2 == 0 else 10
        pts.append((32 + r * math.cos(a), 32 + r * math.sin(a)))
    burst = c.poly(pts)
    mark(p, burst & inner, mk, base=0, bevel=2.2)
    core = c.circle(32, 32, 7)
    p.part(core, mk, 'sphere', base=2, sep=False, rim=False)
    p.decal(c.circle(31, 31, 2.6), WHITE, 0)
    for (x, y) in ((17, 14), (49, 13), (52, 47), (14, 48)):
        p.part(c.circle(x, y, 1.4) & inner, mk, 'flat', base=1, sep=False, rim=False)
    p.grade = 'common'
    return p


def jade_thrust(p):
    c = p.c
    inner, mk, d = _emblem(p, 'jade')
    steel = mat7(Ramp(EL['metal'][1], EL['jade'][0][0]), 'metal')
    fr = Frame((16.0, 48.0), 45.0)
    blade = fr.prof(c, [(0.0, 3.6), (30.0, 3.6), (40.0, 0.0)])
    guard = fr.prof(c, [(-2.5, 7.5), (0.5, 7.5)]) | fr.prof(c, [(-9.0, 2.2), (-2.0, 2.2)])
    ring = dilate4(blade | guard) & ~(blade | guard)
    p.decal(ring & inner, mk.out, 0)
    cyl_field(p, fr, blade & inner, lambda t: np.where(t > 30, np.clip(3.6 * (40 - t) / 10, 0, 3.6), 3.6), steel, ridge=True, sep=False, rim=False)
    p.part(guard & inner, mk, 'ray', base=0, sep=False, rim=False, bevel=1.6)
    for (x, y) in ((14, 30), (24, 50), (9, 40)):
        m = c.seg(x, y, x - 7, y + 7, 1.6) & inner
        p.part(m, mk, 'flat', base=-1, sep=False, rim=False)
    p.sparkle(*fr.P(37.0, 0.0), 1, WHITE)
    p.grade = 'earth'
    return p


# ============================================================================= HUD glyphs (32-px space)
def _hud_part(p, m, base=1, bevel=1.6):
    """HUD glyph faces are pale gold with a lit edge and a warm shade edge (today's language, one step richer)."""
    if p.style == 'A':
        return p.part(m, HUD_GOLD, 'bevel', base=base, sep=True, hw=1, sw=1, rim=False)
    return p.part(m, HUD_GOLD, 'ray', base=base, sep=True, bevel=bevel, rim=False, gain=2.2)


def hud_jian(p):
    c = p.c
    fr = Frame((2.5, 29.5), 45.0)
    TIP = 37.5
    blade = fr.prof(c, [(11.0, 3.1), (30.0, 3.1), (TIP, 0.0)])
    guard = fr.prof(c, [(8.0, 2.6), (9.0, 6.0), (11.0, 6.4), (12.5, 3.0)])
    grip = fr.prof(c, [(2.5, 2.1), (8.5, 2.1)])
    pom = c.circle(*fr.P(2.0, 0.0), 2.5)
    _hud_part(p, grip, 1, 1.3)
    _hud_part(p, pom, 1, 1.3)
    cyl_field(p, fr, blade, lambda t: np.where(t > 30, np.clip(3.1 * (TIP - t) / (TIP - 30), 0, 3.1), 3.1), HUD_GOLD,
              base=1, ridge=True, sep=True, rim=False)
    _hud_part(p, guard, 1, 1.4)
    t, w = c.field_along(fr.p0, fr.P(1, 0))
    p.decal(grip & (np.floor(t / 2.0).astype(int) % 2 == 0) & erode4(grip), HUD_GOLD, -1)
    p.decal(c.circle(*fr.P(10.2, 0.0), 1.0), HUD_GOLD, 3)
    return p


def hud_cultivate(p):
    c = p.c
    bowl = c.ellipse(16, 27.0, 13.0, 5.0) & c.box(0, 24.5, 32, 32)
    petals = []
    for (a, L, W, dx) in ((90, 19.0, 8.0, 0.0), (60, 16.5, 6.6, 2.5), (120, 16.5, 6.6, -2.5), (30, 13.0, 5.6, 5.0), (150, 13.0, 5.6, -5.0)):
        petals.append(c.leaf(16 + dx, 26.5, a, L, W, 0.0, tip_power=0.75))
    for i in (3, 4, 1, 2, 0):
        _hud_part(p, petals[i], 1, 1.7)
    _hud_part(p, bowl, 0, 1.6)
    p.decal(c.circle(15.2, 12.0, 1.4), HUD_GOLD, 3)
    p.line([(16, 15), (16, 24)], HUD_GOLD, -1, 1.0)
    p.line([(13, 16), (12, 24)], HUD_GOLD, -1, 1.0)
    p.line([(19, 16), (20, 24)], HUD_GOLD, -1, 1.0)
    return p


# ============================================================================= the empty-slot motif (cloud seal)
def empty_motif(p):
    c = p.c
    col = mat7(Ramp(['#0F3D3B', '#15514F', '#1E6A66', '#2C9E8F', '#67D6BD'], '#082322'), 'matte')
    curl = c.arc(27, 34, 11, 3.2, 0, 300) | c.arc(27, 34, 6, 3.0, 20, 250) | c.arc(43, 38, 6.5, 3.0, 300, 210)
    base = c.box(14, 46, 52, 49.5)
    m = curl | base
    if p.style == 'A':
        p.part(m, col, 'flat', base=0, sep=False, rim=False)
        p.decal(m & ~erode4(m) & (c.Y < c.X * 0 + 30 * p.s), col, 1)
    else:
        p.shadow = False
        p.contour = 0.2
        p.part(m, col, 'ray', base=0, sep=False, rim=False, bevel=1.6)
    return p


ITEMS = [
    # id, family, today's icon id, draw fn, kwargs, label
    ('iron_jian', 'equipment', 'iron_jian', jian, {'grade': 'common'}, 'Iron jian'),
    ('wardens_handbell', 'equipment', 'wardens_handbell', bell, {}, "Warden's hand-bell"),
    ('jadeiron_robe', 'equipment', 'jadeiron_robe', robe, {}, 'Jadeiron robe'),
    ('healing_pill', 'items', 'healing_pill', healing_pill, {}, 'Healing pill'),
    ('sage_condensing_pill', 'items', 'sage_condensing_pill', breakthrough_pill, {}, 'Sage-condensing pill'),
    ('star_lotus', 'items', 'star_lotus', star_lotus, {}, 'Star lotus'),
    ('driftglass', 'items', 'driftglass', driftglass, {}, 'Driftglass'),
    ('jade_scale', 'items', 'jade_scale', jade_scale, {}, 'Jade scale'),
    ('inner_art_manual', 'items', 'inner_art_manual', manual, {}, 'Inner-art manual'),
    ('ember_burst', 'techniques', 'ember_burst', ember_burst, {}, 'Ember Burst'),
    ('jade_thrust', 'techniques', 'jade_thrust', jade_thrust, {}, 'Jade Thrust'),
]
HUD = [
    ('jian', 'hud', 'jian', hud_jian, {}, 'Attack (jian)'),
    ('cultivate', 'hud', 'cultivate', hud_cultivate, {}, 'Cultivate (lotus)'),
]
LADDER = ['common', 'spirit', 'sage', 'will']
