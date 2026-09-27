"""Insects (HD, Style A): every catch of the netting post at 64 art px, shown 1:1 in the 76 px slot, with a native
@32 render for the HUD item ring and the small slots.

Each insect is the living specimen seen from above, from the side or three-quarter on, filling the icon: the head
with its eyes and antennae, the thorax, the segmented abdomen, six jointed legs, and the wings as the species wears
them (wing cases parted over a glowing tail, clear veined wings folded past the body, a domed metallic shell, wings
spread with their bands and eyespots, hind wings fanned in flight, four star-dusted points). Parts are laid out in a
body axis (fish.Axis: u along the body toward the head, v across it) so a specimen can sit on the diagonal. The grade
is form and trim, never colour alone (beast_parts.GRADE_HD): a plain insect is as it was netted; from Common a thread
is tied round its waist, hemp at Common, the grade's silk with a metal bead from Earth; the aura from Mystic up.
Every icon comes from one table (INSECTS_HD).
"""
import math

import numpy as np

from pix import Ramp, WHITE, dilate4, dilate8, erode4, rgb
from palette import M, STAR_GLOW, mat7
from registry import hd, register
import shapes as S
from families.beast_parts import GRADE_HD, XY, cap_hd, cord_hd, glow_hd, knot_hd, lmask
from families.fish import Axis

FAM, GROUP = 'items', 'insects'
ART = 64   # HD (tools/icons/README.md, "How to convert a family")


# ============================================================================= materials
GLOWTAIL = mat7(Ramp(['#40560E', '#7A9A18', '#BEE03A', '#E8FF86', '#FBFFD6'], '#18220A'), 'light')
BLACKSHELL = mat7(Ramp(['#121010', '#221D19', '#382F27', '#584C3E', '#86775F'], '#060504'), 'porcelain')
CICADA = mat7(Ramp(['#20200F', '#3A3A1A', '#5E5E2C', '#8A884C', '#BAB67E'], '#0C0C05'), 'porcelain')
CLEARWING = mat7(Ramp(['#5E7C86', '#8EAAB2', '#BCD4D8', '#E0F0F0', '#FFFFFF'], '#223238'), 'glass')
SCARAB = mat7(Ramp(['#0C3226', '#16553C', '#2A8A5A', '#5CC486', '#C8F4B4'], '#051710'), 'jade')
CREAM = mat7(Ramp(['#6A5C44', '#A49274', '#D8C8A4', '#F0E6CC', '#FFFBEE'], '#28221A'), 'silk')
MANTIS = mat7(Ramp(['#1A1846', '#2E2C78', '#4A4EAA', '#7C82D6', '#BEC4F4'], '#090820'), 'porcelain')
FROST = mat7(Ramp(['#1C4460', '#32769A', '#62B2D6', '#A8E2F2', '#EEFCFF'], '#0A1C2A'), 'glass')
LOCUST = mat7(Ramp(['#4A140E', '#861E14', '#C8401E', '#EE7A32', '#FFC070'], '#200604'), 'porcelain')
MIDNIGHT = mat7(Ramp(['#0A0E26', '#141C44', '#223070', '#3A4EA0', '#6E86D0'], '#04060F'), 'porcelain')
SALMON, PEARL, BRONZE, VIOLET, QI, CLOUD, FIRE, GOLD, STARLIGHT, INKM, MOSS = (M('salmon', 'porcelain'), M('pearl', 'porcelain'), M('bronze'), M('violet', 'silk'),
                                                                               M('qi'), M('cloud', 'porcelain'), M('fire'), M('gold'), M('starlight'), M('ink'), M('moss'))
SPARK = '#9FE8FF'


# ============================================================================= helpers
def poly(p, B, pts):
    return p.c.poly([B.p(u, v) for (u, v) in pts])


def line(p, B, pts, w=1.0):
    return lmask(p, [B.p(u, v) for (u, v) in pts], w)


def pair(p, B, pts, w=1.0):
    """A leg or antenna and its mirror on the other side of the body."""
    return line(p, B, pts, w) | line(p, B, [(u, -v) for (u, v) in pts], w)


def legs_hd(p, mask, mat, lv=0, joints=()):
    """Legs (a mask of strokes) in a flat tone with their joints as small knobs."""
    p.part(mask, mat, 'flat', base=lv, sep=True, rim=False)
    for (x, y, r) in joints:
        p.part(p.c.circle(x, y, r), mat, 'flat', base=lv, sep=False, rim=False)


def antennae_hd(p, mask, mat, lv=0):
    """Antennae: 1-px strokes that never cross a painted part."""
    p.part(mask & ~p.c.a, mat, 'flat', base=lv, sep=False, rim=False)


def eye_hd(p, x, y, r, iris, pupil=True):
    """A compound eye: the iris, a dark pupil toward the front, a catch-light at the top left."""
    c = p.c
    p.part(c.circle(x, y, r), iris, 'sphere', base=0, sep=True, rim=False)
    if pupil:
        p.decal(c.circle(x + r * 0.2, y + r * 0.15, r * 0.45), INKM, -1)
    p.decal(c.box(x - r * 0.6, y - r * 0.6, x - r * 0.6 + 1, y - r * 0.6 + 1), WHITE, 0)


def segments_hd(p, B, mask, mat, u0, u1, pitch=3.0, lv=-2, lit=True):
    """The rings of an abdomen: dark lines across the axis every `pitch` from u0 to u1, a lit line beside each."""
    U, V = B.uv(p)
    inner = erode4(mask)
    u = u0
    while u <= u1:
        ring = inner & (U >= u - 0.5) & (U < u + 0.5)
        p.decal(ring, mat, lv)
        if lit:
            p.decal(inner & (U >= u + 0.5) & (U < u + 1.5) & ~ring, mat, 1)
        u += pitch


def tie_hd(p, g, B, u, hw, side=1, curl=(4.5, 3.5)):
    """The grade's thread tied round the body at axis `u` (half-width `hw`): the cord across it, the knot on
    `side`, its end trailing away, and a metal bead on the knot from Earth. Nothing on a plain catch."""
    if g['cord'] is None:
        return
    c = p.c
    cord_hd(p, [B.p(u, hw + 0.8), B.p(u, -hw - 0.8)], g['cord'], 2.2)
    kx, ky = B.p(u, side * (hw + 0.6))
    mx, my = B.p(u + 2.0, side * (hw + curl[1] * 0.6))
    ex, ey = B.p(u - curl[0], side * (hw + curl[1] + 1.2))
    p.part(c.taper((kx, ky), (mx, my), (ex, ey), 2.2, 1.2), g['cord'], 'flat', base=0, sep=True, rim=False)
    knot_hd(p, kx, ky, 1.9, g['cord'])
    if g['metal'] is not None:
        cap_hd(p, kx, ky, 1.8, g['metal'])


def halo_hd(p, mask, col, alphas=(110, 50)):
    """A local light: stepped alpha bands around one part only, outside the room the outline will take. It is not
    the grade's aura (which rings the whole silhouette); a firefly's tail or a spark carries one at any grade."""
    c = p.c
    cur = dilate4(mask)
    blocked = dilate4(c.a)
    for al in alphas:
        ring = dilate8(cur) & ~cur
        free = ring & ~blocked & (c.alpha == 0)
        c.rgb[free] = rgb(col)
        c.alpha[free] = al
        cur |= ring


def sparks_hd(p, pts):
    for (x, y, arm) in pts:
        p.sparkle(x, y, arm)


# ============================================================================= the species
def glowfly_hd(p, g):
    """A firefly from above: a rose shield, near-black wing cases parted over the glowing yellow-green tail."""
    c = p.c
    B = Axis(31, 33, 58)
    legs = pair(p, B, [(8.3, 3.7), (12, 12), (15.7, 15.7)], 1.8) | pair(p, B, [(3.7, 4.6), (2.8, 13.9), (-1.9, 17.6)], 1.8) | \
        pair(p, B, [(-0.9, 4.6), (-8.3, 13), (-13.9, 14.8)], 1.8)
    legs_hd(p, legs, BLACKSHELL, -1, [B.p(u, v * s) + (1.2,) for s in (1, -1) for (u, v) in ((12, 12), (2.8, 13.9), (-8.3, 13))])
    tail = B.ell(p, -12, 0, 12, 7.4)
    p.part(tail, GLOWTAIL, 'sphere', base=0, sep=True, rim=False, cx=B.p(-11, 0)[0], cy=B.p(-11, 0)[1], rx=12, ry=12)
    segments_hd(p, B, tail, GLOWTAIL, -20, -3, 4.0, -2)
    p.decal(B.ell(p, -13, 0, 7, 3.6), GLOWTAIL, 3)
    left = B.ell(p, 0.9, 4.6, 13, 5.4, -8)
    right = B.ell(p, 0.9, -4.6, 13, 5.4, 8)
    for m in (left, right):
        p.part(m, BLACKSHELL, 'ray', base=0, sep=True, tex='metal')
    p.decal(line(p, B, [(11, 7.5), (2, 9.2), (-8, 8.6)]) & erode4(left), BLACKSHELL, 3)
    p.decal(line(p, B, [(11, -7.5), (2, -9.2), (-8, -8.6)]) & erode4(right), BLACKSHELL, 2)
    p.decal(line(p, B, [(10, 3.0), (-9, 2.2)]) & erode4(left), BLACKSHELL, -3)
    p.decal(line(p, B, [(10, -3.0), (-9, -2.2)]) & erode4(right), BLACKSHELL, -3)
    shield = B.ell(p, 13.7, 0, 5.2, 7.2)
    p.part(shield, SALMON, 'sphere', base=0, sep=True, cx=B.p(13, 1)[0], cy=B.p(13, 1)[1], rx=7, ry=7)
    p.decal(B.ell(p, 14.2, 0, 2.2, 2.2) & shield, BLACKSHELL, 0)
    head = B.ell(p, 18.8, 0, 3.0, 3.7)
    p.part(head, BLACKSHELL, 'sphere', base=0, sep=True)
    for s in (1, -1):
        x, y = B.p(19.5, 2.4 * s)
        p.decal(c.circle(x, y, 1.2) & head, BLACKSHELL, 3)
    antennae_hd(p, pair(p, B, [(21, 1.5), (25, 4.6), (27, 9.5)]), BLACKSHELL, 0)
    x, y = B.p(-24, 0)
    tie_hd(p, g, B, 11.5, 6.6, side=-1)
    halo_hd(p, tail, '#DFFF6A', (120, 55))
    sx, sy = B.p(-19, 10.5)
    p.sparkle(sx, sy, 1, '#FBFFD6')


def cicada_hd(p, g):
    """A reed cicada from above: broad brown-green head and thorax, clear dark-veined wings folded past its tail."""
    c = p.c
    B = Axis(32, 30, 90)
    legs = pair(p, B, [(11, 7.5), (14, 14), (17.5, 16)], 1.8) | pair(p, B, [(6.5, 7.5), (4.6, 15), (0.9, 17.6)], 1.8) | \
        pair(p, B, [(1, 6.5), (-4, 12.5), (-8, 14)], 1.6)
    legs_hd(p, legs, CICADA, -1, [B.p(u, v * s) + (1.1,) for s in (1, -1) for (u, v) in ((14, 14), (4.6, 15), (-4, 12.5))])
    body = B.ell(p, -6, 0, 15, 6.6)
    p.part(body, CICADA, 'ray', base=0, sep=True)
    segments_hd(p, B, body, CICADA, -19, -2, 3.2)
    wpts = [(10, 3.7), (6.5, 12.6), (-2.8, 15.5), (-14.8, 13.3), (-24.4, 6.7), (-26.3, 1.5), (-11, 0.6), (1.9, 1.5)]
    wl = poly(p, B, wpts)
    wr = poly(p, B, [(u, -v) for (u, v) in wpts])
    for m, lit in ((wr, -1), (wl, 0)):
        p.part(m, CLEARWING, 'flat', base=lit, sep=True, tex='glass')
        p.decal(m & body, CICADA, 1)
    veins = c.empty()
    for s in (1, -1):
        veins |= line(p, B, [(8.3, 4.4 * s), (4.6, 12.2 * s), (-3.7, 14.8 * s), (-14.8, 12.6 * s), (-24, 6.5 * s)])
        veins |= line(p, B, [(6.5, 4.8 * s), (-5.5, 8.5 * s), (-16.6, 8.1 * s), (-23, 4.1 * s)])
        veins |= line(p, B, [(-5.5, 8.5 * s), (-7.4, 14.4 * s)]) | line(p, B, [(-16.6, 8.1 * s), (-18.5, 11.5 * s)])
        veins |= line(p, B, [(-11, 5.2 * s), (-11, 8.5 * s)]) | line(p, B, [(0, 4.5 * s), (-1, 8.6 * s)])
    p.decal(veins & (wl | wr), CICADA, -3)
    thorax = B.ell(p, 10.7, 0, 6.3, 8.9)
    p.part(thorax, CICADA, 'sphere', base=0, sep=True)
    p.decal(line(p, B, [(14, -2.8), (8.5, 0), (14, 2.8)]) & thorax, MOSS, 2)
    p.decal(line(p, B, [(6, -5), (5, 0), (6, 5)]) & thorax, CICADA, -2)
    head = B.ell(p, 18.1, 0, 3.5, 9.6)
    p.part(head, CICADA, 'ray', base=1, sep=True)
    for s in (1, -1):
        x, y = B.p(18.5, 9.0 * s)
        eye_hd(p, x, y, 2.8, INKM, pupil=False)
    p.decal(B.ell(p, 20.5, 0, 1.6, 2.6), CICADA, 3)
    antennae_hd(p, pair(p, B, [(21.5, 2.5), (24.5, 4.5)]), CICADA, -1)
    tie_hd(p, g, B, 3.0, 6.8, side=1)


def scarab_hd(p, g):
    """A jade scarab from above: toothed head, broad shield and domed wing cases with a jade sheen."""
    c = p.c
    B = Axis(32, 33, 90)
    legs = pair(p, B, [(11, 9), (15, 16.5), (21, 18.5)], 2.6) | pair(p, B, [(2, 11), (0, 19), (-5.5, 22)], 2.4) | \
        pair(p, B, [(-7.5, 10), (-15, 18.5), (-22, 19.5)], 2.4)
    legs_hd(p, legs, SCARAB, -1, [B.p(u, v * s) + (1.6,) for s in (1, -1) for (u, v) in ((15, 16.5), (0, 19), (-15, 18.5))])
    for (u, v) in ((15, 16.5), (0, 19), (-15, 18.5)):
        for s in (1, -1):
            x, y = B.p(u, v * s)
            p.decal(c.box(x - 1.5, y - 1.5, x + 1.5, y + 1.5) & legs, SCARAB, 1)
    for (u, v) in ((21, 18.5), (-5.5, 22), (-22, 19.5)):
        for s in (1, -1):
            x, y = B.p(u, v * s)
            p.part(c.circle(x, y, 1.6), SCARAB, 'flat', base=-2, sep=False, rim=False)
    elytra = B.ell(p, -6.5, 0, 18.5, 15.2)
    p.part(elytra, SCARAB, 'sphere', base=0, sep=True, cx=B.p(-3, 5)[0], cy=B.p(-3, 5)[1], rx=20, ry=18, tex='jade')
    p.decal(line(p, B, [(8, 0), (-24, 0)]) & elytra, SCARAB, -3)
    for vv in (6.5, -6.5, 11.5, -11.5):
        p.decal(line(p, B, [(6.5, vv), (-19, vv * 0.8)]) & erode4(elytra), SCARAB, -2)
    pron = B.ell(p, 11.6, 0, 7.4, 13.2) & (B.uv(p)[0] > 5.5)
    p.part(pron, SCARAB, 'sphere', base=0, sep=True, cx=B.p(12, 4)[0], cy=B.p(12, 4)[1], rx=13, ry=13, tex='jade')
    p.decal(line(p, B, [(6, -11), (7.5, -6), (7.8, 0), (7.5, 6), (6, 11)]) & pron, SCARAB, -3)
    head = poly(p, B, [(15.5, 8.2), (20.5, 7.8), (22.5, 4.1), (21, 1.5), (22.8, 0), (21, -1.5), (22.5, -4.1), (20.5, -7.8), (15.5, -8.2)])
    p.part(head, SCARAB, 'ray', base=0, sep=True, tex='jade')
    for s in (1, -1):
        x, y = B.p(18.5, 5.8 * s)
        eye_hd(p, x, y, 1.6, INKM, pupil=False)
    # the jade sheen: a mint streak along the lit shoulder, a warm glint on the shield, a lit edge on the teeth
    p.decal(line(p, B, [(3, 9), (-4, 11.5), (-14, 10)], 1.6) & erode4(elytra), SCARAB, 3)
    p.decal(line(p, B, [(3, -4.5), (-7, -4.2)], 1.2) & elytra, SCARAB, 2)
    p.decal(line(p, B, [(14, 6.5), (12, 2.5)], 1.4) & pron, '#D8F29A', 0)
    p.decal(line(p, B, [(21.5, 5), (21.5, 2)]) & head, SCARAB, 3)
    tie_hd(p, g, B, 4.5, 13.0, side=1, curl=(5, 3))
    sx, sy = B.p(-2, 17.5)
    p.sparkle(sx, sy, 1)


def moth_hd(p, g):
    """A silk moth with its wings spread: cream wings with a wavy band and an eyespot each, a soft pearl body and
    feathery comb antennae."""
    c = p.c
    B = Axis(32, 33, 90)
    fw = [(9.5, 2.8), (15.5, 12), (19, 22.5), (15.7, 26.6), (6, 24.2), (-2.2, 17.6), (-3.7, 2.8)]
    fore_l, fore_r = poly(p, B, fw), poly(p, B, [(u, -v) for (u, v) in fw])
    hind_l, hind_r = B.ell(p, -8.5, 11.8, 10.6, 10.0, -20), B.ell(p, -8.5, -11.8, 10.6, 10.0, 20)
    for m in (hind_l, hind_r):
        p.part(m, CREAM, 'ray', base=-1, sep=False, rim=False, tex='cloth', axis=90)
    for m in (fore_l, fore_r):
        p.part(m, CREAM, 'ray', base=0, sep=True, rim=False, tex='cloth', axis=90)
    for s in (1, -1):
        band = line(p, B, [(13, 5.5 * s), (8.5, 11 * s), (9.5, 17.5 * s), (4.5, 23 * s)], 1.6)
        p.decal(band & (fore_l | fore_r), CREAM, -2)
        p.decal(line(p, B, [(13, 4.2 * s), (8.5, 9.7 * s), (9.5, 16.2 * s), (4.5, 21.7 * s)]) & (fore_l | fore_r), CREAM, 2)
        ex, ey = B.p(-9, 12 * s)
        p.decal(c.circle(ex, ey, 3.8), BRONZE, -2)
        p.decal(c.circle(ex, ey, 2.6), BRONZE, 1)
        p.decal(c.circle(ex + 0.3, ey + 0.3, 1.5), INKM, 0)
        p.decal(c.box(ex - 1.5, ey - 1.5, ex - 0.5, ey - 0.5), CREAM, 3)
        p.decal(line(p, B, [(-2, 5.5 * s), (-8, 8 * s), (-16, 7.5 * s)]) & (hind_l | hind_r), CREAM, -2)
        p.decal(line(p, B, [(6, 4 * s), (2, 10 * s), (0, 17 * s)]) & (fore_l | fore_r), CREAM, -1)
    p.decal(S.outline_only(hind_l | hind_r) & (B.uv(p)[0] < -13), CREAM, -2)
    body = B.ell(p, -3, 0, 14.5, 4.4)
    p.part(body, PEARL, 'ray', base=0, sep=True, rim=False)
    segments_hd(p, B, body, PEARL, -15, -4, 3.0, -1)
    thorax = B.ell(p, 8.8, 0, 4.8, 4.8)
    p.part(thorax, PEARL, 'sphere', base=0, sep=True, rim=False)
    head = B.ell(p, 14, 0, 2.8, 3.3)
    p.part(head, PEARL, 'sphere', base=-1, sep=True, rim=False)
    for s in (1, -1):
        x, y = B.p(14.5, 2.4 * s)
        p.decal(c.circle(x, y, 1.1), INKM, 0)
    for s in (1, -1):
        plume = B.ell(p, 20.5, 7.4 * s, 6.4, 2.8, 52 * s)
        p.part(plume, BRONZE, 'flat', base=0, sep=True, rim=False)
        U, V = B.uv(p)
        comb = plume & (np.floor((U * 0.6 - V * s * 0.8) * 1.0).astype(int) % 2 == 0)
        p.decal(comb, BRONZE, -2)
        p.part(line(p, B, [(15.5, 1.5 * s), (20, 7 * s), (24.5, 13 * s)]), BRONZE, 'flat', base=-1, sep=False, rim=False)
    tie_hd(p, g, B, 3.5, 4.6, side=1, curl=(4, 2.5))


def mantis_hd(p, g):
    """A thunder mantis three-quarter on, forelegs raised, a spark crackling between its claws."""
    c = p.c
    far = lmask(p, [(27, 40), (33, 46), (35, 56)], 1.6) | lmask(p, [(18, 44), (22, 52), (20, 56)], 1.6)
    legs_hd(p, far, MANTIS, -2, [(33, 46, 1.1), (22, 52, 1.1)])
    B = Axis(18, 43, 25)
    abdomen = B.ell(p, -1, 0, 14, 6.1)
    p.part(abdomen, MANTIS, 'ray', base=0, sep=True)
    segments_hd(p, B, abdomen, MANTIS, -13, 8, 3.5, -2)
    wings = B.ell(p, 1.5, 3.2, 13.6, 3.5)
    p.part(wings, VIOLET, 'ray', base=0, sep=True, rim=False, tex='cloth', axis=25)
    p.decal(line(p, B, [(13, 3.5), (-10, 3.7)]) & wings, VIOLET, 2)
    p.decal(line(p, B, [(11, 1.8), (-9, 2.0)]) & wings, VIOLET, -2)
    neck = c.taper((29, 36), (32, 26), (33.5, 17), 5.2, 3.6)
    p.part(neck, MANTIS, 'ray_soft', base=0, sep=True)
    p.decal(lmask(p, [(30.5, 34), (33, 26), (34, 19)]) & erode4(neck), MANTIS, 2)
    head = c.poly([(26, 12), (37.5, 9.5), (35, 18.5), (31.5, 19)])
    p.part(head, MANTIS, 'ray', base=1, sep=True)
    for (x, y, r) in ((26.5, 11.5, 2.2), (37.5, 9.5, 2.0)):
        eye_hd(p, x, y, r, QI)
    antennae_hd(p, lmask(p, [(29, 8.5), (25, 3.5), (17, 5)]) | lmask(p, [(34, 8), (38, 3.5)]), MANTIS, 1)
    near = lmask(p, [(31, 38), (39, 45), (41, 56)], 1.8) | lmask(p, [(13, 48), (9, 54), (5, 56)], 1.8)
    legs_hd(p, near, MANTIS, 0, [(39, 45, 1.2), (9, 54, 1.2)])
    # the raptorial forelegs: coxa forward and down, the spined femur raised, the tibia hooked over at the top
    for (dx, dy, base) in ((3.0, 1.2, -1), (0, 0, 1)):
        coxa = c.seg(34 + dx, 22.5 + dy, 42 + dx, 29 + dy, 4.2)
        femur = c.seg(42 + dx, 29 + dy, 48 + dx, 15 + dy, 4.2)
        tibia = c.seg(48 + dx, 15 + dy, 45 + dx, 9 + dy, 2.8)
        p.part(coxa | femur | tibia, MANTIS, 'ray', base=base, sep=True)
        for (x, y) in ((43.5, 25), (45, 21), (46.5, 17.5)):
            p.decal(c.box(x + dx, y + dy, x + dx + 1.5, y + dy + 1.2) & femur, MANTIS, -3)
    p.decal(c.box(44, 21, 45, 25), MANTIS, 3)
    p.decal(c.box(46.5, 15, 47.5, 18), MANTIS, 3)
    tie_hd(p, g, B, -4, 6.3, side=-1, curl=(4, 4))
    spark = c.pts([(52, 7), (54, 9), (52, 11), (54, 13), (56, 11), (50, 9), (54, 5), (57, 8)])
    p.decal(spark & ~c.a, SPARK, 0, only_on=False)
    p.sparkle(53, 9, 2)
    halo_hd(p, c.circle(53.5, 9.5, 3.6), SPARK, (110, 45))


def cricket_hd(p, g):
    """A frost cricket in side view: long sweeping antennae, frost-white legs, the big hind leg cocked."""
    c = p.c
    far = lmask(p, [(38, 42), (38, 50), (34, 56)], 1.6)
    legs_hd(p, far, CLOUD, -2, [(38, 50, 1.1)])
    B = Axis(22, 40, 0)
    abdomen = c.ellipse(22, 40, 16.5, 8.4)
    p.part(abdomen, FROST, 'ray', base=0, sep=True, tex='glass')
    segments_hd(p, B, abdomen & c.box(0, 40, 64, 64), FROST, -14, 12, 4.0, -2, lit=False)
    wing = c.poly([(36, 30.5), (10, 32.5), (5.6, 37.6), (18, 39.2), (37, 36.4)])
    p.part(wing, FROST, 'ray', base=1, sep=True, tex='glass')
    p.decal(lmask(p, [(32, 32), (10, 34)]) & wing, FROST, -2)
    p.decal(lmask(p, [(33, 34.5), (14, 36.8)]) & wing, FROST, -1)
    thorax = c.ellipse(42, 36, 8.2, 7.6)
    p.part(thorax, FROST, 'sphere', base=0, sep=True, tex='glass')
    p.decal(c.arc(42, 36, 5.5, 1.2, 250, 330) & thorax, FROST, -2)
    head = c.ellipse(52, 35, 6.4, 7.0)
    p.part(head, FROST, 'sphere', base=1, sep=True, tex='glass')
    eye_hd(p, 53.5, 32.5, 2.4, INKM, pupil=False)
    p.decal(lmask(p, [(55, 39.5), (57, 43)]) & ~c.a, FROST, -2)
    p.part(c.taper((55, 39.5), (57, 42), (57.5, 45), 1.6, 1.0) & ~c.a, FROST, 'flat', base=-1, sep=False, rim=False)
    near = lmask(p, [(50, 41), (54, 49), (58, 53)], 1.8) | lmask(p, [(42, 42), (44, 50), (48, 56)], 1.8)
    legs_hd(p, near, CLOUD, 0, [(54, 49, 1.2), (44, 50, 1.2)])
    femur = c.seg(30, 41, 16, 21, 6.6)
    p.part(femur, CLOUD, 'ray', base=0, sep=True)
    p.decal(lmask(p, [(28, 38), (18, 24)]) & erode4(femur), CLOUD, -2)
    p.decal(lmask(p, [(26.5, 41.5), (15, 25)]) & erode4(femur), CLOUD, 2)
    tibia = c.taper((14, 20), (10, 38), (6.5, 56), 2.6, 1.6)
    p.part(tibia, CLOUD, 'ray_soft', base=1, sep=True)
    for (x, y) in ((8.5, 42), (8, 48), (7.5, 53)):
        p.part(c.poly([(x, y), (x - 2.6, y + 1.5), (x, y + 2)]), CLOUD, 'flat', base=0, sep=False, rim=False)
    ant = c.polyline(S.curve_pts((52, 28), (48, 4), (26, 6), 18), 1.4) | c.polyline(S.curve_pts((50, 28.5), (42, 10), (22, 14), 18), 1.4)
    p.part(ant & ~c.a, FROST, 'flat', base=1, sep=False, rim=False)
    tie_hd(p, g, B, 4.0, 8.2, side=1, curl=(4, 3))
    p.sparkle(58, 18, 1)
    p.sparkle(8, 8, 1)


def locust_hd(p, g):
    """An ember locust in flight, seen from above: long forewings, fanned hind wings with ember-bright edges."""
    c = p.c
    B = Axis(31, 33, 52)
    fan_pts = [(7.4, 2.8), (6.5, 14.8), (0.9, 23.7), (-8.3, 24.4), (-15.7, 17.6), (-16.6, 2.8)]
    U, V = B.uv(p)
    for s in (1, -1):
        fan = poly(p, B, [(u, v * s) for (u, v) in fan_pts])
        p.part(fan, FIRE, 'ray', base=0, sep=False, rim=False)
        p.decal(S.outline_only(fan) & (V * s > 6.5), FIRE, 2)
        for (u, v) in ((0.9, 23.7), (-8.3, 24.4), (-15.7, 17.6), (5, 20)):
            p.decal(line(p, B, [(5.5, 3.3 * s), (u * 0.9, v * 0.9 * s)]) & erode4(fan), LOCUST, -1)
        p.decal(fan & (V * s > 12) & (V * s < 15), FIRE, 1)
    for s in (1, -1):
        fore = poly(p, B, [(11, 2.2 * s), (15.7, 6.3 * s), (8.3, 23 * s), (3.3, 25.2 * s), (1.5, 20.4 * s), (4.6, 2.8 * s)])
        p.part(fore, LOCUST, 'ray', base=0, sep=True, rim=False)
        p.decal(S.outline_only(fore) & (U > 6) & (V * s > 3.3), FIRE, 2)
        p.decal(line(p, B, [(11, 4 * s), (4.6, 21.3 * s)]) & erode4(fore), LOCUST, -2)
        p.decal(line(p, B, [(13.5, 6 * s), (7.5, 18 * s)]) & erode4(fore), LOCUST, 1)
    abdomen = B.ell(p, -12, 0, 11.5, 3.6)
    p.part(abdomen, LOCUST, 'ray', base=0, sep=True)
    segments_hd(p, B, abdomen, LOCUST, -22, -3, 2.8, -2)
    thorax = B.ell(p, 10.2, 0, 6.3, 4.8)
    p.part(thorax, LOCUST, 'sphere', base=0, sep=True)
    p.decal(line(p, B, [(15, 0), (6, 0)]) & thorax, LOCUST, 2)
    head = B.ell(p, 17.4, 0, 3.7, 4.1)
    p.part(head, LOCUST, 'sphere', base=1, sep=True)
    for s in (1, -1):
        x, y = B.p(17.8, 3.0 * s)
        eye_hd(p, x, y, 1.5, INKM, pupil=False)
    antennae_hd(p, pair(p, B, [(20, 1.8), (23, 3.7), (25.2, 7.8)]), LOCUST, -1)
    legs = pair(p, B, [(13.9, 4.4), (16.6, 8.3)], 1.6) | pair(p, B, [(-1.9, 3), (-6.5, 5.9), (-17.6, 6.3)], 1.6)
    p.part(legs & ~c.a, LOCUST, 'flat', base=-1, sep=False, rim=False)
    tie_hd(p, g, B, -2.5, 3.9, side=-1, curl=(3.5, 3))


def mote_hd(p, g):
    """A starwing mote: a midnight-blue body under four pointed wings of gold star-dust, glowing softly."""
    c = p.c
    B = Axis(32, 33, 90)
    U, V = B.uv(p)
    wings = c.empty()
    for s in (1, -1):
        fore = poly(p, B, [(4.6, 1.8 * s), (15.7, 13.9 * s), (24, 23 * s), (9.3, 21.3 * s), (0, 7.4 * s)])
        hind = poly(p, B, [(-0.9, 1.8 * s), (-4.6, 13 * s), (-17.6, 22.2 * s), (-11, 9.3 * s), (-5.5, 1.8 * s)])
        for m, base in ((hind, -1), (fore, 0)):
            p.part(m, GOLD, 'ray', base=base, sep=True, rim=False, tex='metal')
            wings |= m
        p.decal(line(p, B, [(3.7, 2.8 * s), (20.4, 20.4 * s)]) & wings, GOLD, -3)
        p.decal(line(p, B, [(-2, 2.8 * s), (-15, 20 * s)]) & wings, GOLD, -3)
        p.decal(line(p, B, [(8, 5 * s), (15, 19 * s)]) & erode4(wings), GOLD, -2)
    X, Y = XY(p)
    dust = ((np.floor(X * 3 + Y * 5) % 7) == 0) | ((np.floor(X * 5 + Y * 2) % 11) == 0)
    p.decal(erode4(wings) & dust, '#FFFDF4', 0)
    body = B.ell(p, -4.6, 0, 11.1, 3.5)
    p.part(body, MIDNIGHT, 'ray', base=0, sep=True)
    segments_hd(p, B, body, MIDNIGHT, -14, -1, 2.6, -2)
    thorax = B.ell(p, 5.9, 0, 4.6, 4.4)
    p.part(thorax, MIDNIGHT, 'sphere', base=0, sep=True)
    head = B.ell(p, 11.5, 0, 3.3, 4.3)
    p.part(head, MIDNIGHT, 'sphere', base=0, sep=True)
    for s in (1, -1):
        x, y = B.p(12.2, 2.4 * s)
        eye_hd(p, x, y, 1.5, GOLD, pupil=False)
    antennae_hd(p, pair(p, B, [(14.5, 1.5), (18.5, 4.4), (20, 8)]), MIDNIGHT, 1)
    tail = B.ell(p, -16.3, 0, 2.2, 2.2)
    p.part(tail, STARLIGHT, 'sphere', base=1, sep=True, rim=False)
    p.decal(B.ell(p, -16.8, 0.5, 0.9, 0.9), WHITE, 0)
    tie_hd(p, g, B, 0.5, 3.6, side=1, curl=(3.5, 3))
    sx, sy = B.p(-17.5, 4.5)
    p.sparkle(sx, sy, 1)
    p.sparkle(54, 8, 1)
    p.sparkle(9, 12, 1)


# ============================================================================= the table
INSECTS_HD = [
    # id, grade (items.py), the aura's colour from Mystic up (None: the grade's), the drawing
    ('glowfly', 'plain', None, glowfly_hd),
    ('reed_cicada', 'common', None, cicada_hd),
    ('jade_scarab', 'earth', None, scarab_hd),
    ('silk_moth', 'mystic', '#F2E7FF', moth_hd),
    ('thunder_mantis', 'spirit', '#7FD4FF', mantis_hd),
    ('frost_cricket', 'spirit', '#9FD8FF', cricket_hd),
    ('ember_locust', 'sage', '#FFB142', locust_hd),
    ('starwing_mote', 'sovereign', STAR_GLOW, mote_hd),
]


def make_catch_hd(grade, aura, draw):
    """A catch's drawing `draw(p, g)` with its grade's trim and, from Mystic, its aura (the module's own wrapper, so
    the icon belongs to this family module)."""
    g = GRADE_HD[grade]

    def hd_draw(p):
        draw(p, g)
        glow_hd(p, g, aura)
    return hd_draw


for _id, _grade, _aura, _draw in INSECTS_HD:
    _fn = make_catch_hd(_grade, _aura, _draw)
    register(FAM, _id, _fn, GROUP)
    hd(_id, _fn)
