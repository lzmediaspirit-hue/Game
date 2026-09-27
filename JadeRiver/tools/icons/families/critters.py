"""Critters (HD, Style A): every catch of the snaring post at 64 art px, shown 1:1 in the 76 px slot, with a native
@32 render for the HUD item ring and the small slots.

Each critter is the living animal, drawn with care in its species' colours and after its sprite where it has one
(art/creatures: the reed frog's green and gold eye, the ember fox's white chest and sail ears): the body built from a
spine of overlapping discs so it keeps one bold silhouette, fur in strands lying down it (beast_parts.fur_hd), the
face with its eyes (ring, iris, pupil and catch-light), nose and whiskers, ears with their pink inside, paws with
their toes, and the species' own mark (the frog's gold eyes, the hare's misty ear tips, the marmot's cloud tail, the
hedgehog's sparking quills, the stoat's black tail tip, the gecko's star spots, the pelt's iridescent sheen). The
grade is form and trim, never colour alone (beast_parts.GRADE_HD): a plain critter is as it was snared; from Common
it wears a cord at the neck, hemp at Common, the grade's silk with a metal bead from Earth (the pelt is tied with
it); the aura from Mystic up. Every icon comes from one table (CRITTERS_HD).
"""
import math

import numpy as np

from pix import Ramp, WHITE, erode4
from palette import M, STAR_GLOW, mat7
from registry import hd, register
import shapes as S
from families.beast_parts import GRADE_HD, XY, cap_hd, cord_hd, fur_hd, glow_hd, knot_hd, lmask
from families.insects import halo_hd

FAM, GROUP = 'items', 'critters'
ART = 64   # HD (tools/icons/README.md, "How to convert a family")


# ============================================================================= materials
FROG = mat7(Ramp(['#0C3E24', '#16663A', '#2FA253', '#6CD877', '#C8F7A8'], '#05190E'), 'porcelain')
FROGBELLY = mat7(Ramp(['#5E6A2A', '#96A846', '#CCDB7E', '#E8F2B0', '#FBFFE2'], '#232A0E'), 'porcelain')
HARE = mat7(Ramp(['#56616A', '#8A969E', '#C2CBD0', '#E4EAEC', '#FFFFFF'], '#1E262C'), 'leather')
FERRET = mat7(Ramp(['#2E1A0E', '#553219', '#835128', '#B17A42', '#D8A868'], '#140B05'), 'leather')
CREAM = mat7(Ramp(['#6E5E44', '#A8946E', '#DCC9A0', '#F2E6C8', '#FFFBEC'], '#2A2319'), 'leather')
TAN = mat7(Ramp(['#5A3E1E', '#8E6532', '#C49552', '#E4BE7E', '#F8E2B2'], '#24170A'), 'leather')
QUILL = mat7(Ramp(['#191A44', '#2E3276', '#4E56B0', '#8490E2', '#C8D0FF'], '#0A0A22'), 'porcelain')
SNOW = mat7(Ramp(['#5C7082', '#93A8B8', '#D0DEE6', '#EEF5F8', '#FFFFFF'], '#1C2833'), 'leather')
OCHRE = mat7(Ramp(['#5C3212', '#94541C', '#CE8A34', '#EDB660', '#FFE0A0'], '#261205'), 'leather')
MIDNIGHT = mat7(Ramp(['#0A0F2A', '#16204C', '#243480', '#3C54B0', '#7690DC'], '#04060F'), 'porcelain')
PELT = mat7(Ramp(['#6A6280', '#A69EBE', '#DCD6EE', '#F4F0FA', '#FFFFFF'], '#25202F'), 'leather')
GOLD, ICE, PINK, INKM, BAMBOO, WOOD, CLOUD, SAND, STARLIGHT, MIST = (M('gold', 'gem'), M('ice'), M('pink', 'porcelain'), M('ink'), M('bamboo'), M('wood'),
                                                                   M('cloud', 'leather'), M('sand', 'leather'), M('starlight'), M('mist'))
SPARK = '#9FE8FF'
NOSE = mat7(Ramp(['#6A3040', '#A8505E', '#E88C94', '#F6B8BC', '#FFE6E6'], '#2A1018'), 'porcelain')


# ============================================================================= helpers
def spine_hd(c, pts, radii, k=8):
    """Union of discs along a polyline: soft animal bodies, necks and tails."""
    m = c.empty()
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        r0, r1 = radii[i], radii[i + 1]
        for j in range(k + 1):
            t = j / float(k)
            m |= c.circle(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, r0 + (r1 - r0) * t)
    return m


def eye_hd(p, x, y, r, iris, rx=None, ry=None, pupil=0.5, catch=True):
    """A critter's eye: a dark ring, the iris, a pupil toward the front-bottom, a catch-light at the top left."""
    c = p.c
    rx, ry = rx or r, ry or r
    p.decal(c.ellipse(x, y, rx + 0.9, ry + 0.9), INKM, 0)
    p.decal(c.ellipse(x, y, rx, ry), iris, 1)
    p.decal(c.ellipse(x + rx * 0.15, y + ry * 0.1, rx * pupil, ry * pupil), INKM, -2)
    if catch:
        p.decal(c.box(x - rx * 0.55, y - ry * 0.6, x - rx * 0.55 + 1, y - ry * 0.6 + 1), WHITE, 0)


def nose_hd(p, x, y, r=1.6):
    p.decal(p.c.ellipse(x, y, r, r * 0.8), INKM, 1)
    p.decal(p.c.box(x - r * 0.5, y - r * 0.6, x - r * 0.5 + 1, y - r * 0.6 + 1), INKM, 3)


def whiskers_hd(p, pts_list, mat, lv=2):
    for pts in pts_list:
        p.decal(lmask(p, pts), mat, lv)


def collar_hd(p, g, pts, knot, tail=None, w=2.4):
    """The grade's cord at the neck along `pts`, its knot at `knot` and its end trailing to `tail`, the bead in
    the grade's metal from Earth. Nothing on a plain critter."""
    if g['cord'] is None:
        return
    c = p.c
    cord_hd(p, pts, g['cord'], w)
    if tail is not None:
        kx, ky = knot
        tx, ty = tail
        p.part(c.taper(knot, ((kx + tx) / 2 + (ty - ky) * 0.25, (ky + ty) / 2 - (tx - kx) * 0.25), tail, w, 1.2), g['cord'], 'flat', base=0, sep=True, rim=False)
    knot_hd(p, knot[0], knot[1], w * 0.85, g['cord'])
    if g['metal'] is not None:
        cap_hd(p, knot[0], knot[1], w * 0.8, g['metal'])


def toes_hd(p, mat, pts, r=1.5, lv=0):
    for (x, y) in pts:
        p.part(p.c.circle(x, y, r), mat, 'flat', base=lv, sep=True, rim=False)


# ============================================================================= the species
def frog_hd(p, g):
    """A squat jade-green frog seen from the front: bulging gold eyes, a pale mottled belly, hind legs folded at its
    sides and the webbed feet splayed, three-fingered hands set down in front."""
    c = p.c
    for s in (1, -1):
        thigh = c.ellipse(32 + 17.4 * s, 42.5, 8.4, 9.8)
        p.part(thigh, FROG, 'sphere', base=0, sep=False, cx=32 + 15 * s, cy=39, rx=10, ry=11)
        foot = c.poly([(32 + 14 * s, 50.5), (32 + 26.4 * s, 52.6), (32 + 27 * s, 57.4), (32 + 13 * s, 57.4)])
        p.part(foot, FROG, 'ray', base=-1 if s > 0 else 0, sep=True, rim=False)
        for dx in (19.5, 23.5):
            p.decal(lmask(p, [(32 + dx * s, 52), (32 + (dx + 1.2) * s, 57)]) & foot, FROG, -3)
        for dx in (17.5, 21.5, 25.5):
            p.part(c.circle(32 + dx * s, 57.3, 1.4), FROG, 'flat', base=0, sep=False, rim=False)
    body = c.ellipse(32, 40.3, 17, 14)
    p.part(body, FROG, 'sphere', base=0, sep=True, cx=27, cy=33, rx=22, ry=20)
    head = c.ellipse(32, 29.2, 17.8, 10.7)
    p.part(head, FROG, 'sphere', base=0, sep=True, cx=25, cy=23, rx=23, ry=17)
    belly = c.ellipse(32, 45.6, 10.4, 8.6) & body
    p.part(belly, FROGBELLY, 'ray_soft', base=0, sep=False, rim=False)
    for (x, y) in ((26, 43), (36, 41), (31, 49), (38, 48)):
        p.decal(c.circle(x, y, 1.2) & belly, FROGBELLY, -2)
    # the throat, a paler fold under the mouth
    throat = c.ellipse(32, 37.5, 8, 2.8) & body
    p.decal(throat, FROGBELLY, 0)
    # the back's mottling and the pale ridge along the spine
    for (x, y, r) in ((17, 36, 2.0), (46, 35, 2.2), (15, 42, 1.6), (49, 42, 1.6), (24, 33, 1.5), (41, 32, 1.6), (20, 28, 1.3), (44, 27, 1.3)):
        p.decal(c.circle(x, y, r) & (body | head) & ~belly, FROG, -2)
        p.decal(c.circle(x - 0.6, y - 0.6, r * 0.45) & (body | head), FROG, 1)
    p.decal(lmask(p, [(24, 31.5), (32, 30), (40, 31.5)]) & head, FROG, 2)
    # front legs and three-fingered hands
    for s in (1, -1):
        arm = c.seg(32 + 10.4 * s, 43, 32 + 12.2 * s, 53.5, 4.8)
        p.part(arm, FROG, 'ray_soft', base=0 if s < 0 else -1, sep=True)
        hand = c.ellipse(32 + 12.5 * s, 55, 4.2, 2.6)
        p.part(hand, FROG, 'flat', base=0, sep=True, rim=False)
        for dx in (-3, 0, 3):
            p.part(c.circle(32 + 12.5 * s + dx, 56.6, 1.3), FROG, 'flat', base=0, sep=False, rim=False)
    # the wide mouth, and the nostrils
    mouth = c.polyline(S.curve_pts((17.5, 31.5), (32, 39.5), (46.5, 31.5), 16), 1.4)
    p.decal(mouth & head, FROG, -3)
    p.decal(c.polyline(S.curve_pts((19, 32.5), (32, 40.5), (45, 32.5), 16), 1.0) & head & ~mouth, FROG, 2)
    for x in (28.5, 35.5):
        p.decal(c.circle(x, 25, 0.9), FROG, -3)
    # the bulging gold eyes on their sockets
    for s in (1, -1):
        ex = 32 + 10.7 * s
        socket = c.circle(ex, 20.2, 6.2)
        p.part(socket, FROG, 'sphere', base=0, sep=True, cx=ex - 2, cy=18, rx=7, ry=7)
        ball = c.circle(ex, 19.8, 4.4)
        p.part(ball, GOLD, 'sphere', base=0, sep=True, cx=ex - 1.5, cy=18, rx=5.5, ry=5.5, tex='glass')
        p.decal(c.ellipse(ex + 0.3, 19.8, 1.4, 3.0) & ball, INKM, -1)
        p.decal(c.box(ex - 2.6, 17.4, ex - 1.6, 18.4), WHITE, 0)
        p.decal(c.arc(ex, 20.2, 5.4, 1.0, 200, 340) & socket, FROG, -2)


def hare_hd(p, g):
    """A pale grey-white hare sitting in profile, its long ears raised, their tips fading into misty blue."""
    c = p.c
    far = c.leaf(37.6, 22.8, 106, 17.4, 6.8, bend=0.05)
    p.part(far, HARE, 'ray', base=-1, sep=False, rim=False)
    p.decal(far & c.box(0, 0, 64, 11), ICE, -1)
    haunch = c.ellipse(23.7, 42.2, 15.2, 13.7)
    chest = c.ellipse(35.7, 37.6, 10.4, 11.8)
    body = haunch | chest
    p.part(body, HARE, 'sphere', base=0, sep=True, cx=24, cy=32, rx=23, ry=20)
    fur_hd(p, body, HARE, -70, pitch=4.5, L=5)
    foot = c.ellipse(26.5, 54.2, 12.6, 3.5)
    p.part(foot, HARE, 'ray_soft', base=0, sep=True, rim=False)
    toes_hd(p, HARE, ((34, 55.5), (37, 54.8)), 1.6, 0)
    paw = c.seg(40.3, 45, 41.3, 54.2, 4.4)
    p.part(paw, HARE, 'ray_soft', base=1, sep=True, rim=False)
    toes_hd(p, HARE, ((39.5, 56), (42.5, 56)), 1.5, 1)
    p.decal(c.arc(23.7, 41, 9.5, 1.2, 20, 150) & erode4(haunch), HARE, -2)
    tail = c.circle(9.2, 41.3, 4.1)
    p.part(tail, HARE, 'sphere', base=1, sep=True, rim=False)
    head = c.ellipse(44.2, 26.8, 10, 7.8) | c.ellipse(50.5, 29.2, 4.8, 4.4)
    p.part(head, HARE, 'sphere', base=0, sep=True, cx=41, cy=23, rx=13, ry=11)
    near = c.leaf(40.3, 23.7, 98, 17.8, 7.4, bend=-0.08)
    p.part(near, HARE, 'ray', base=1, sep=True, rim=False)
    inner_ear = c.leaf(40.6, 24, 98, 14.5, 3.4, bend=-0.08) & erode4(near) & c.box(0, 11, 64, 64)
    p.decal(inner_ear, PINK, 0)
    p.decal(inner_ear & c.box(0, 0, 64, 18), PINK, 2)
    tips = (near | far) & c.box(0, 0, 64, 11.5)
    p.decal(tips & near, ICE, 0)
    p.decal(tips & near & c.box(0, 0, 40, 9), ICE, 2)
    eye_hd(p, 45.5, 25.2, 2.6, INKM, pupil=0.5)
    nose_hd(p, 54.2, 28.3, 1.4)
    p.decal(lmask(p, [(52, 31.5), (54.5, 31)]) & head, HARE, -3)
    whiskers_hd(p, ([(50, 30), (58, 27.5)], [(50, 31), (58, 31)]), HARE, 3)
    collar_hd(p, g, [(36.5, 30.5), (40, 33.5), (44, 34.5)], (44.5, 34.8), (48, 39))
    halo_hd(p, tips, '#AFC9D1', (110, 45))


def ferret_hd(p, g):
    """A slim brown ferret loping through the reeds: long low body, cream belly and throat, a dark masked face."""
    c = p.c
    # the reeds behind it: a cattail on the left, a bent blade on the right
    p.part(c.seg(13.5, 57.5, 15.4, 8.5, 2.2) | c.seg(54, 57.5, 52.4, 12, 2.2), BAMBOO, 'flat', base=0, sep=False, rim=False)
    p.part(c.ellipse(15.4, 15.4, 2.8, 6.7), WOOD, 'ray', base=0, sep=True, rim=False)
    p.part(c.leaf(13.5, 46, 148, 15, 4.4, bend=0.1), BAMBOO, 'ray', base=1, sep=True, rim=False)
    p.part(c.leaf(53.5, 21, 150, 13, 4.0, bend=-0.12), BAMBOO, 'ray', base=1, sep=True, rim=False)
    far_legs = c.seg(22.5, 46.5, 19.5, 55.5, 3.8) | c.seg(42, 44.5, 45, 54.5, 3.8)
    p.part(far_legs, FERRET, 'flat', base=-2, sep=True, rim=False)
    spine = [(7, 53.3), (13.5, 49.6), (20.9, 45), (30.2, 40.5), (39.4, 40.9), (45.9, 36.6)]
    body = spine_hd(c, spine, [1.5, 3.0, 6.3, 6.7, 6.1, 4.8])
    p.part(body, FERRET, 'ray', base=0, sep=True)
    belly = body & c.box(0, 44.5, 64, 64) & c.box(21, 0, 46, 64)
    p.part(belly, CREAM, 'ray_soft', base=0, sep=False, rim=False)
    fur_hd(p, body & c.box(14, 0, 64, 44.5), FERRET, 175, pitch=4, L=5)
    p.decal(body & c.box(0, 0, 9.5, 64), FERRET, -2)
    near_legs = c.seg(25.5, 46, 27.5, 55.5, 4.2) | c.seg(39, 44.5, 37, 55.5, 4.2)
    p.part(near_legs, FERRET, 'ray_soft', base=0, sep=True)
    for x in (27.5, 37):
        paw = c.ellipse(x, 56, 3.6, 1.8)
        p.part(paw, FERRET, 'flat', base=-1, sep=True, rim=False)
    head = c.ellipse(49, 32.4, 6.7, 5.2) | c.poly([(50.5, 28.3), (58.5, 33.9), (50.5, 36.8)])
    p.part(head, FERRET, 'ray', base=1, sep=True)
    throat = c.poly([(46.5, 34.6), (58.5, 34.2), (52.5, 38), (45.5, 38.4)]) & head
    p.decal(throat, CREAM, 1)
    ear = c.circle(45.5, 27.5, 2.7)
    p.part(ear, FERRET, 'flat', base=0, sep=True, rim=False)
    p.decal(c.circle(45.8, 27.8, 1.2), PINK, 0)
    mask = c.poly([(45, 30.5), (54.5, 29), (56, 32), (52, 33.5), (44.5, 33)]) & head
    p.decal(mask, FERRET, -3)
    eye_hd(p, 50.5, 31.2, 1.8, INKM, pupil=0.45)
    nose_hd(p, 57.4, 33.6, 1.3)
    whiskers_hd(p, ([(54, 35), (60, 34)], [(54, 36), (59.5, 37.5)]), CREAM, 2)
    collar_hd(p, g, [(43.5, 36.5), (46, 38.5), (49, 38)], (49.5, 38.2), (53, 42.5))


def marmot_hd(p, g):
    """A plump marmot standing up on its haunches: tan back, white face and belly, a cloud-puff tail behind it."""
    c = p.c
    puff = c.circle(49.4, 44, 7) | c.circle(52.4, 35.7, 5.4) | c.circle(46.4, 51.2, 5.6) | c.circle(54.2, 44.6, 4.4)
    p.part(puff, CLOUD, 'sphere', base=1, sep=False, cx=46, cy=38, rx=12, ry=15, rim=False)
    p.decal(c.arc(50, 43.5, 3.4, 1.4, 30, 260) & puff, CLOUD, -2)
    p.decal(c.arc(52.5, 35.5, 2.6, 1.2, 40, 250) & puff, CLOUD, -2)
    p.decal(c.circle(47.5, 41, 1.6) & puff, CLOUD, 3)
    body = c.ellipse(31, 40.3, 15.5, 16.7)
    p.part(body, TAN, 'sphere', base=0, sep=True, cx=26, cy=32, rx=21, ry=23)
    fur_hd(p, body, TAN, -80, pitch=4.5, L=5.5)
    belly = c.ellipse(31, 43.1, 9.6, 12.6) & body
    p.part(belly, CLOUD, 'ray_soft', base=0, sep=False, rim=False)
    feet = c.ellipse(23.7, 56, 5.6, 3) | c.ellipse(38.5, 56, 5.6, 3)
    p.part(feet, TAN, 'ray_soft', base=0, sep=True, rim=False)
    toes_hd(p, TAN, ((20, 57.5), (23.5, 58), (27, 57.5), (35, 57.5), (38.5, 58), (42, 57.5)), 1.3, -1)
    head = c.ellipse(31, 21.3, 11.8, 10)
    p.part(head, TAN, 'sphere', base=0, sep=True, cx=26, cy=17, rx=15, ry=13)
    for s in (1, -1):
        ear = c.circle(31 + 8.9 * s, 13.1, 3)
        p.part(ear, TAN, 'sphere', base=-1 if s > 0 else 1, sep=True, rim=False)
        p.decal(c.circle(31 + 8.6 * s, 13.4, 1.3), PINK, 0)
    face = (c.ellipse(31, 25, 7.4, 5.2) | c.ellipse(31, 19.8, 3.0, 4.4)) & head
    p.part(face, CLOUD, 'ray_soft', base=0, sep=False, rim=False)
    for s in (1, -1):
        eye_hd(p, 31 + 5.4 * s, 19.2, 1.7, INKM, rx=1.5, ry=2.0, pupil=0.5)
    nose_hd(p, 31, 24.6, 1.5)
    p.decal(lmask(p, [(31, 26), (31, 27.5)]) & face, TAN, -2)
    p.decal(c.box(29.5, 27.5, 32.5, 29), WHITE, 0)
    whiskers_hd(p, ([(27, 25), (21, 24)], [(35, 25), (41, 24)]), CLOUD, 3)
    paws = c.ellipse(26.4, 34.8, 4, 3.1) | c.ellipse(35.6, 34.8, 4, 3.1)
    p.part(paws, TAN, 'ray_soft', base=1, sep=True, rim=False)
    for x in (24, 26.4, 28.8, 33.2, 35.6, 38):
        p.decal(lmask(p, [(x, 36.5), (x, 37.5)]) & paws, TAN, -2)
    collar_hd(p, g, [(22, 30.5), (31, 33), (40, 30.5)], (40.5, 30.5), (44, 27))


def hedgehog_hd(p, g):
    """A hedgehog in profile under a dome of blue-violet quills, each tipped with a spark before the storm."""
    c = p.c
    cx, cy = 29.2, 44
    pts, tips = [], []
    n = 19
    for i in range(n + 1):
        a = math.radians(188 - i * (196 / n))
        r = 24.4 if i % 2 == 0 else 17.6
        x, y = cx + math.cos(a) * r * 1.02, cy - math.sin(a) * r
        pts.append((x, y))
        if i % 2 == 0 and 1 <= i <= n - 1:
            tips.append((x, y))
    quills = c.poly(pts + [(cx + 20, cy + 8), (cx - 22, cy + 8)]) & c.box(0, 0, 64, 52)
    p.part(quills, QUILL, 'ray', base=0, sep=False)
    inner = erode4(quills)
    for i in range(1, n, 2):
        a = math.radians(188 - i * (196 / n) - 4)
        for (r0, r1, lv) in ((7, 19, -2), (5, 15, 1)):
            off = 0 if lv < 0 else 1.5
            p.decal(lmask(p, [(cx + math.cos(a) * r0 + off, cy - math.sin(a) * r0), (cx + math.cos(a) * r1 + off, cy - math.sin(a) * r1)]) & inner, QUILL, lv)
    for (x, y) in tips:
        p.decal(c.circle(x - 0.4, y + 0.8, 1.2) & quills, QUILL, 3)
    face = c.ellipse(47.7, 45, 8.5, 7) | c.poly([(48.7, 40.3), (58.8, 47.2), (48.7, 51.4)])
    p.part(face, SAND, 'ray', base=1, sep=True, rim=False)
    fur_hd(p, face, SAND, 190, pitch=3.5, L=4)
    eye_hd(p, 49.5, 43.5, 1.9, INKM, pupil=0.45)
    nose_hd(p, 57.8, 47.2, 1.5)
    p.decal(lmask(p, [(55, 49), (57, 48.5)]) & face, SAND, -3)
    whiskers_hd(p, ([(53, 48), (59, 51)], [(52, 49.5), (57, 53)]), SAND, 3)
    feet = c.ellipse(21.5, 54.5, 4.2, 2.4) | c.ellipse(44, 54.5, 4.2, 2.4)
    p.part(feet, SAND, 'ray_soft', base=0, sep=True, rim=False)
    toes_hd(p, SAND, ((19, 56), (22, 56.5), (25, 56), (41.5, 56), (44.5, 56.5), (47.5, 56)), 1.1, -1)
    collar_hd(p, g, [(43, 40), (45, 46), (43.5, 51.5)], (43.5, 51.5), (39.5, 56))
    for (x, y) in tips[2:-1:2]:
        p.sparkle(x + 1.5, y - 1.5, 1, SPARK)
    p.sparkle(30, 8, 2)
    p.sparkle(9, 22, 1)
    halo_hd(p, c.pts([(int(x), int(y)) for (x, y) in tips]), SPARK, (90,))


def stoat_hd(p, g):
    """A white winter stoat standing up like a sentry: slim S-shaped body, the black tail tip, ice-blue eyes."""
    c = p.c
    tail = spine_hd(c, [(26.5, 52.4), (37.6, 54.9), (46.8, 52.7), (53.3, 45.9)], [3.3, 3.3, 3.1, 3.1])
    p.part(tail, SNOW, 'ray', base=0, sep=False)
    fur_hd(p, tail, SNOW, 15, pitch=3.5, L=4)
    tip = tail & ((XY(p)[0] - 0.5 * XY(p)[1]) > 22)
    p.part(tip, INKM, 'ray', base=1, sep=False, rim=False)
    haunch = c.ellipse(23.7, 46.8, 8.5, 8.9)
    spine = [(24.6, 46.8), (27.4, 37.6), (32, 29.2), (34.8, 22.8)]
    body = spine_hd(c, spine, [7.8, 7.0, 5.7, 5.0]) | haunch
    p.part(body, SNOW, 'sphere', base=0, sep=True, cx=22, cy=30, rx=17, ry=24)
    fur_hd(p, body, SNOW, -75, pitch=4.5, L=5)
    p.decal(c.polyline([(31.5, 32), (29.5, 40), (29, 46)], 1.6) & erode4(body), SNOW, 3)
    p.decal(c.arc(23.7, 47.5, 6.3, 1.2, 20, 140) & erode4(body), SNOW, -2)
    feet = c.ellipse(22.8, 56, 6.3, 2.8) | c.ellipse(32.4, 56, 4.1, 2.6)
    p.part(feet, SNOW, 'ray_soft', base=0, sep=True, rim=False)
    toes_hd(p, SNOW, ((19, 57.5), (22.5, 58), (26, 57.5), (31, 57.5), (34, 57.5)), 1.2, -1)
    paws = c.seg(36.6, 31.1, 39.8, 36.1, 3.7)
    p.part(paws, SNOW, 'ray_soft', base=1, sep=True, rim=False)
    toes_hd(p, SNOW, ((39, 38), (41.5, 37)), 1.2, 0)
    head = c.ellipse(35.7, 17.9, 7, 5.7) | c.poly([(36.6, 13.9), (47.5, 19.1), (36.6, 22.8)])
    p.part(head, SNOW, 'sphere', base=1, sep=True, cx=33, cy=15, rx=11, ry=9)
    ear = c.circle(30.9, 12.8, 3)
    p.part(ear, SNOW, 'flat', base=0, sep=True, rim=False)
    p.decal(c.circle(31.1, 13.1, 1.3), PINK, 1)
    eye_hd(p, 38.2, 16.2, 2.0, ICE, pupil=0.5)
    nose_hd(p, 46.5, 19.1, 1.3)
    p.decal(lmask(p, [(42, 21.5), (45.5, 20.5)]) & head, SNOW, -2)
    whiskers_hd(p, ([(43, 21), (49, 23.5)], [(42, 22.5), (47, 25.5)]), SNOW, 3)
    collar_hd(p, g, [(31, 22.5), (34.5, 26), (39.5, 25)], (39.8, 25), (43.5, 28.5))
    p.sparkle(53, 9, 2)
    p.sparkle(11, 22, 1)


def fox_hd(p, g):
    """A small ochre desert fox sitting three-quarter on, huge sail ears up, its brush tail curled round its feet."""
    c = p.c
    tail = spine_hd(c, [(43.1, 44), (49.6, 48.7), (43.1, 54.2), (26.5, 54.6)], [4.4, 4.8, 4.4, 3.5])
    p.part(tail, OCHRE, 'ray', base=0, sep=False)
    fur_hd(p, tail, OCHRE, 10, pitch=3.5, L=4.5)
    p.part(tail & c.box(0, 0, 29.5, 64), CREAM, 'ray_soft', base=1, sep=False, rim=False)
    body = c.ellipse(33.9, 44, 11.8, 11.8)
    p.part(body, OCHRE, 'sphere', base=0, sep=True, cx=30, cy=36, rx=17, ry=19)
    fur_hd(p, body, OCHRE, -80, pitch=4, L=5)
    chest = c.ellipse(30.2, 43.1, 6.3, 9.3) & body
    p.part(chest, CREAM, 'ray_soft', base=0, sep=False, rim=False)
    legs = c.seg(26.5, 44, 25.5, 54.2, 4.4) | c.seg(33.9, 45.9, 33.9, 54.2, 4.4)
    p.part(legs, OCHRE, 'ray_soft', base=1, sep=True)
    for x in (25.5, 33.9):
        p.part(c.ellipse(x, 55.5, 3.4, 2.0), CREAM, 'flat', base=0, sep=True, rim=False)
        toes_hd(p, CREAM, ((x - 2, 57), (x, 57.3), (x + 2, 57)), 1.0, -1)
    for (bx, ang) in ((21.8, 118), (36.6, 66)):
        ear = c.leaf(bx, 23.7, ang, 16.7, 11.8, tip_power=0.55)
        p.part(ear, OCHRE, 'ray', base=1 if ang > 90 else 0, sep=True, rim=False)
        inner = c.leaf(bx + (0.7 if ang > 90 else -0.7), 23.7, ang, 12.6, 5.9, tip_power=0.55)
        p.decal(inner & erode4(ear), PINK, 0)
        p.decal(inner & erode4(erode4(ear)) & c.box(0, 0, 64, 16), PINK, 2)
    head = c.ellipse(29.2, 28.3, 10.4, 8.1) | c.poly([(23.7, 29.8), (29.2, 39), (34.8, 29.8)])
    p.part(head, OCHRE, 'sphere', base=0, sep=True, cx=25, cy=24, rx=13, ry=11)
    muzzle = c.poly([(24.3, 31.5), (29.2, 39), (34.2, 31.5), (29.2, 29.4)]) & head
    p.part(muzzle, CREAM, 'ray_soft', base=0, sep=False, rim=False)
    nose_hd(p, 29.2, 36, 1.5)
    p.decal(lmask(p, [(29.2, 37.5), (29.2, 38.5)]) & head, OCHRE, -3)
    for x in (24.5, 33.9):
        eye_hd(p, x, 27.8, 2.0, INKM, rx=2.1, ry=1.5, pupil=0.5)
    whiskers_hd(p, ([(25, 34), (19.5, 33)], [(33.5, 34), (39, 33)]), CREAM, 3)
    collar_hd(p, g, [(22, 36.5), (28, 40.5), (35, 38)], (35.5, 38), (39.5, 34))


def gecko_hd(p, g):
    """A midnight-blue gecko seen from above, splayed toes and a curling tail, gold star spots glowing faintly."""
    c = p.c
    legs = c.empty()
    toes = []
    for (a, b, t) in (((37.6, 22.8), (47.7, 16.3), (50.5, 10.7)), ((30.2, 22.8), (20, 18.1), (15.4, 11.6)),
                      ((34.8, 38.5), (45.9, 41.3), (51.4, 36.6)), ((27.4, 40.3), (19, 46.8), (20, 53.3))):
        legs |= c.polyline([a, b, t], 3.6)
        for (dx, dy) in ((-2.6, -1.1), (2.6, -1.1), (0, 2.6), (1.1, -2.8), (-1.6, 2.0)):
            toes.append((t[0] + dx, t[1] + dy))
    p.part(legs, MIDNIGHT, 'ray_soft', base=0, sep=False)
    for (x, y) in toes:
        p.part(c.circle(x, y, 1.5), MIDNIGHT, 'flat', base=1, sep=False, rim=False)
    tail = c.taper((31, 41.3), (24.6, 57.9), (10.7, 49.6), 6.7, 2.2) | c.taper((10.7, 49.6), (5.7, 42.2), (12, 39), 2.2, 1.5, k=10)
    p.part(tail, MIDNIGHT, 'ray', base=0, sep=True)
    body = spine_hd(c, [(34.8, 16.3), (33.9, 22.8), (32.9, 32), (32, 41.3)], [4.8, 4.4, 6.3, 4.4])
    p.part(body, MIDNIGHT, 'ray', base=1, sep=True)
    p.decal(lmask(p, [(34, 18), (33.5, 30), (32.5, 40)]) & erode4(body), MIDNIGHT, 2)
    for y in (26, 31, 36):
        p.decal(lmask(p, [(29.5, y), (36.5, y)]) & erode4(body), MIDNIGHT, -2)
    head = c.ellipse(35.7, 13.1, 6.3, 5.6)
    p.part(head, MIDNIGHT, 'sphere', base=1, sep=True, cx=33, cy=11, rx=8, ry=7)
    for x in (30.5, 40.5):
        eye_hd(p, x, 11.5, 1.8, GOLD, pupil=0.4)
    p.decal(lmask(p, [(33, 17), (38.5, 17)]) & head, MIDNIGHT, -3)
    # gold star spots along the back and tail, each a starlight core in a gold four-point
    spots = [(32, 20), (35, 26), (30, 30), (34, 36), (28, 46), (20, 52), (12, 48), (30, 41)]
    for (x, y) in spots:
        p.decal(S.star4(c, x, y, 2) & c.a, GOLD, 0)
    for (x, y) in spots:
        p.decal(c.box(x, y, x + 1, y + 1) & c.a, STARLIGHT, 3)
    collar_hd(p, g, [(30.5, 18.5), (34, 20), (38.5, 18.5)], (38.8, 18.5), (43, 22))
    p.sparkle(54, 24, 1)
    p.sparkle(9, 28, 1)


def pelt_hd(p, g):
    """A pearly pelt folded in half, leg flaps and tail poking out, an iridescent sheen and a few sparkles, tied
    with the grade's cord."""
    c = p.c
    flaps = (c.poly([(14.4, 21.8), (5.4, 13.1), (12.6, 34.8)]) | c.poly([(49.6, 34.8), (58.6, 47.9), (48.7, 46.8)]) |
             c.poly([(15.4, 46.8), (8.3, 58.3), (26.5, 48.7)]) | c.poly([(35.7, 48.7), (42.2, 58.6), (45.9, 48.7)]))
    p.part(flaps, PELT, 'ray', base=0, sep=False)
    fur_hd(p, flaps, PELT, -60, pitch=4, L=4.5)
    body = c.rrect(11.6, 17.2, 50.5, 48.7, 5.5)
    X, Y = XY(p)
    notch = ((X < 13) & (np.floor(Y / 3) % 2 == 0)) | ((X >= 49) & (np.floor(Y / 3) % 2 == 1)) | ((Y >= 47.2) & (np.floor(X / 3) % 2 == 0))
    body &= ~notch
    p.part(body, PELT, 'ray', base=0, sep=True)
    fur_hd(p, body & c.box(0, 25, 64, 64), PELT, -65, pitch=4.5, L=5.5)
    roll = c.rrect(11.6, 17.2, 50.5, 25, 3.5)
    p.part(roll, PELT, 'ray', base=1, sep=True)
    p.decal(c.box(15, 19, 47, 20.5) & roll, PELT, 3)
    p.decal(c.box(13, 23.5, 49.5, 24.6) & roll, PELT, -2)
    inner = erode4(body) & ~roll
    for (col, off) in (('#F2C4DC', 0), ('#C4ECF6', 4), ('#F8E4A6', 8)):
        band = inner & (np.abs((X + Y) - (66 + off)) < 1.2)
        p.decal(band, col, 0)
    p.decal(erode4(roll) & (np.abs((X + Y) - 48) < 1.0), '#C4ECF6', 0)
    p.decal(erode4(roll) & (np.abs((X + Y) - 52) < 1.0), '#F8E4A6', 0)
    # the grade's cord round the bundle, its knot at the front
    if g['cord'] is not None:
        cord_hd(p, [(31, 16), (31, 50)], g['cord'], 2.6)
        p.part(c.taper((31.5, 34), (37, 37), (38, 42), 2.4, 1.2), g['cord'], 'flat', base=0, sep=True, rim=False)
        knot_hd(p, 31, 33.5, 2.3, g['cord'])
        if g['metal'] is not None:
            cap_hd(p, 31, 33.5, 2.1, g['metal'])
    p.sparkle(54, 10, 2)
    p.sparkle(57.5, 27, 1)
    p.sparkle(23, 42, 1)


# ============================================================================= the table
CRITTERS_HD = [
    # id, grade (items.py), the aura's colour from Mystic up (None: the grade's), the drawing
    ('jade_frog', 'plain', None, frog_hd),
    ('mist_hare', 'common', None, hare_hd),
    ('reed_ferret', 'earth', None, ferret_hd),
    ('cloud_marmot', 'mystic', '#E9F1F4', marmot_hd),
    ('thunder_hedgehog', 'spirit', SPARK, hedgehog_hd),
    ('frost_stoat', 'spirit', '#B7EEF7', stoat_hd),
    ('sand_fox', 'sage', '#FFC870', fox_hd),
    ('star_gecko', 'sovereign', STAR_GLOW, gecko_hd),
    ('radiant_pelt', 'heaven', None, pelt_hd),
]


def make_catch_hd(grade, aura, draw):
    """A catch's drawing `draw(p, g)` with its grade's trim and, from Mystic, its aura (the module's own wrapper, so
    the icon belongs to this family module)."""
    g = GRADE_HD[grade]

    def hd_draw(p):
        draw(p, g)
        glow_hd(p, g, aura)
    return hd_draw


for _id, _grade, _aura, _draw in CRITTERS_HD:
    _fn = make_catch_hd(_grade, _aura, _draw)
    register(FAM, _id, _fn, GROUP)
    hd(_id, _fn)
