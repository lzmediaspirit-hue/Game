"""Legendary chains (HD, Style A): the three pieces of each of the nine legends and the Weapon Soul Crystal, at
64 art px shown 1:1 in the 76 px slot, with a native @32 render for the small slots.

Every piece is the thing its name says (`PIECES_HD`): the Stone Drum's knuckle plates, cuff and heart; the
Riverlight's hilt, blade and soul bead; the Heron's spearhead, shaft and tassel; the Reedwhisper's edge, grip and
sheath; the Ferryman's iron cap, oak shaft and knot; the Mountainsplit's spine, edge and guard; the Seven Winds'
rib, silk and pin; the Crane's bone mouthpiece, jade body and tassel; the Dragonfly's limb, string and sight. They
lie on the weapons' diagonal frame and are built from the weapons' builders (the grip, fittings, blades and tassel)
in the chain's own tint (`data/legends.py` CHAINS, `chain_kit`: the tint as the piece's material, silk and gem)
with the Mystic grade's gold fittings and a Mystic aura in the tint. A broken piece ends in a jagged break with its
edge lit (`broken_hd`). The Weapon Soul Crystal is a gold crystal with an ember flame inside it.
"""
import colorsys
import math
import os
import sys

import numpy as np

from pix import Frame, Ramp, WHITE, dilate4, erode4
from palette import M, mat7
from registry import hd, register
import shapes as S
from families.beast_parts import core_hd
from families.minerals import crystal_hd, grain_hd, lmask
from families.weapons import K, WFRAME, blade_hd, fitting_hd, gem_hd, grip_hd, leaf_blade_hd, tassel_hd, work_hd, wrap_hd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "data"))
from legends import CHAINS  # noqa: E402

FAM, GROUP = 'items', 'legends'
ART = 64   # HD (tools/icons/README.md, "How to convert a family")

GOLD, IRON, DARKWOOD, LEATHER, INKM, EMBER, GOLD_GLASS = M('gold'), M('iron'), M('darkwood'), M('leather'), M('ink'), M('ember'), M('gold', 'glass')
# What each legend's tint is made of: its kind sets the rim light and the texture the pieces take.
CHAIN_KIND = {'stone_drum': 'porcelain', 'riverlight': 'glass', 'heron_reach': 'porcelain', 'reedwhisper': 'jade', 'ferryman': 'wood',
              'mountainsplit': 'metal', 'seven_winds': 'porcelain', 'crane_mourning': 'porcelain', 'dragonfly': 'glass'}
CHAIN_TEX = {'porcelain': 'metal', 'glass': 'glass', 'jade': 'jade', 'wood': 'wood', 'metal': 'metal'}


def tint_mat(hex_col, kind):
    """Seven tones, dark to light, around a chain's tint."""
    r, g, b = (int(hex_col[i:i + 2], 16) / 255.0 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    tones = []
    for lt in (0.16, 0.30, 0.48, 0.68, 0.88):
        rr, gg, bb = colorsys.hls_to_rgb(h, lt, min(1.0, s * 0.9 + 0.1))
        tones.append('#%02X%02X%02X' % (int(rr * 255), int(gg * 255), int(bb * 255)))
    return mat7(Ramp(tones), kind)


def chain_kit(ch):
    """The Mystic kit with the chain's tint as its blade, body, silk and gem, gold fittings, a leather grip and the
    aura in the tint."""
    k = K('mystic')
    kind = CHAIN_KIND.get(ch['id'], 'metal')
    t = tint_mat(ch['tint'], kind)
    k.update(tint=t, blade=t, body=t, tex=CHAIN_TEX[kind], gem=tint_mat(ch['tint'], 'gem'), tassel=tint_mat(ch['tint'], 'silk'),
             wrap=tint_mat(ch['tint'], 'silk'), grip=LEATHER, shaft=DARKWOOD, glow=(ch['tint'], 0.8))
    k['bead'] = k['guard']
    return k


def broken_hd(p, fr, mask, t, hw, ahead=True, mat=None, teeth=4):
    """Break a part on the frame at `t`: what lies beyond it (or before it, `ahead=False`) is gone along a jagged
    line, and the break's edge is lit in `mat`. Returns the part that remains."""
    c = p.c
    ws = np.linspace(-hw - 1.5, hw + 1.5, teeth * 2 + 1)
    pts = [fr.P(t + (1.5 if i % 2 else -1.5), w) for i, w in enumerate(ws)]
    d = 60.0 if ahead else -60.0
    poly = c.poly(pts + [fr.P(t + d, hw + 1.5), fr.P(t + d, -hw - 1.5)])
    p.erase(mask & poly)
    kept = mask & ~poly
    if mat is not None:
        p.decal(kept & dilate4(poly) & erode4(dilate4(kept)), mat, 2)
    return kept


def finish(p, k):
    p.glow(*k['glow'])


# ============================================================================= the piece templates
def hilt_hd(p, k, stub='blade'):
    """A hilt: the tassel, pommel, wrapped grip and winged guard with the gem, and the root of the blade broken off
    beyond it; `stub='tang'` is a grip on its own, a small oval guard and the bare tang."""
    c, fr = p.c, WFRAME
    tassel_hd(p, k, 9.0, 55.2)
    fitting_hd(p, fr, k, 1.5, 7.2, 4.2, 1.2)
    grip_hd(p, fr, k, 6.8, 23.0, 3.4)
    if stub == 'blade':
        blade = blade_hd(p, fr, k, 26.0, 60.0, 70.0, 4.6)
        work_hd(p, k, [fr.P(t, 0.0) for t in np.linspace(32.0, 46.0, 15)], blade)
        broken_hd(p, fr, blade, 47.0, 4.6, True, k['tint'])
        p.part(fr.prof(c, [(22.0, 3.9), (23.5, 8.6), (25.2, 10.4), (27.0, 9.4), (29.0, 5.8), (30.0, 4.0)]), k['guard'], 'ray', base=0, sep=True, tex='metal')
        p.line([fr.P(24.2, -7.2), fr.P(24.2, 7.2)], k['guard'], 2, 1.0)
        gem_hd(p, k, *fr.P(25.6, 0.0), 2.6)
    else:
        tang = fr.prof(c, [(26.0, 1.8), (44.0, 1.8)])
        p.cylinder(fr, tang, 1.8, k['tint'], sep=True, tex=k['tex'])
        broken_hd(p, fr, tang, 39.0, 1.8, True, k['tint'], teeth=2)
        p.part(fr.prof(c, [(23.5, 3.2), (24.5, 6.0), (27.0, 6.0), (28.0, 3.4)]), k['guard'], 'ray', base=0, sep=True, tex='metal')
        p.line([fr.P(25.7, -5.0), fr.P(25.7, 5.0)], k['guard'], 2, 1.0)
        gem_hd(p, k, *fr.P(25.7, 0.0), 2.0)
    p.sparkle(*fr.P(15.0, -3.6), 1)
    finish(p, k)


def blade_piece_hd(p, k, shape='straight'):
    """A fragment of the weapon's blade on the diagonal, broken at its root: a straight jian blade, a leaf, the
    sabre's edge with its clipped point, or the sabre's thick spine."""
    c, fr = p.c, WFRAME
    if shape == 'straight':
        blade = blade_hd(p, fr, k, 6.0, 60.0, 70.0, 4.8)
        work_hd(p, k, [fr.P(t, 0.0) for t in np.linspace(16.0, 56.0, 41)], blade)
        blade = broken_hd(p, fr, blade, 11.0, 4.8, False, k['tint'])
        p.sparkle(*fr.P(63.0, -0.8), 1)
    elif shape == 'leaf':
        blade = leaf_blade_hd(p, fr, k, 4.0, 68.0, 7.0, 0.5)
        work_hd(p, k, [fr.P(t, 0.0) for t in np.linspace(14.0, 52.0, 39)], blade)
        blade = broken_hd(p, fr, blade, 10.0, 7.0, False, k['tint'])
        p.sparkle(*fr.P(58.0, -1.2), 1)
    elif shape == 'sabre':
        ts, spine, edge = [6.0, 22.0, 38.0, 52.0, 62.0, 70.0], [-3.0, -3.6, -4.4, -5.4, -6.0, -4.8], [3.2, 3.8, 4.2, 4.4, 2.6, -4.8]
        blade = c.poly([fr.P(t, w) for t, w in zip(ts, spine)] + [fr.P(t, w) for t, w in zip(ts[::-1], edge[::-1])])
        t, w = fr.along(c)
        ws, we = np.interp(t, ts, spine), np.interp(t, ts, edge)
        f = (w - ws) / np.maximum(we - ws, 0.2)
        p.part(blade, k['blade'], 'field', base=0, field=f, bands=((0.08, 2), (0.46, 1), (0.58, 2), (0.84, 0), (9, -1)), sep=True, tex=k['tex'], axis=45.0)
        work_hd(p, k, [fr.P(tt, float(np.interp(tt, ts, spine)) + 2.0) for tt in np.linspace(14.0, 56.0, 43)], blade)
        blade = broken_hd(p, fr, blade, 11.0, 6.0, False, k['tint'])
        p.sparkle(*fr.P(58.0, -3.2), 1)
    else:   # spine: the sabre's thick back, both ends broken
        blade = fr.prof(c, [(4.0, 5.6), (68.0, 5.6)])
        t, w = fr.along(c)
        p.part(blade, k['blade'], 'field', base=0, field=(w + 5.6) / 11.2, bands=((0.12, 2), (0.3, 1), (0.42, 2), (0.7, 0), (0.86, -1), (9, -2)), sep=True, tex=k['tex'], axis=45.0)
        work_hd(p, k, [fr.P(tt, 1.6) for tt in np.linspace(16.0, 56.0, 41)], blade)
        blade = broken_hd(p, fr, blade, 10.0, 5.6, False, k['tint'])
        blade = broken_hd(p, fr, blade, 62.0, 5.6, True, k['tint'])
        p.sparkle(*fr.P(40.0, -3.8), 1)
    finish(p, k)


def heart_hd(p, k):
    """The legend's heart: a lit bead of the tint held in a cage of old gold, four arms and a ring."""
    c = p.c
    cx, cy = 32.0, 32.0
    p.part(c.ring(cx, cy, 24.0, 2.2), GOLD, 'ray', base=0, sep=False, tex='metal')
    for a in (0.0, 90.0, 180.0, 270.0):
        ar = math.radians(a)
        p.part(c.seg(cx + 10.0 * math.cos(ar), cy - 10.0 * math.sin(ar), cx + 23.0 * math.cos(ar), cy - 23.0 * math.sin(ar), 2.8), GOLD, 'ray_soft', base=0, sep=True, tex='metal')
        p.part(c.circle(cx + 23.0 * math.cos(ar), cy - 23.0 * math.sin(ar), 3.0), GOLD, 'sphere', base=1, sep=True)
    core_hd(p, k['gem'], cx, cy, 14.5)
    finish(p, k)


def spearhead_hd(p, k):
    """A spearhead on the stump of its shaft: the leaf head with the grade's work, the gold collar and its gem, the
    shaft broken a hand below it."""
    c, fr = p.c, WFRAME
    shaft = fr.prof(c, [(6.0, 2.3), (26.0, 2.3)])
    p.cylinder(fr, shaft, 2.3, k['shaft'], sep=True, tex='wood', axis=45.0)
    broken_hd(p, fr, shaft, 10.0, 2.3, False, k['shaft'], teeth=2)
    head = leaf_blade_hd(p, fr, k, 28.0, 70.0, 6.4, 0.55)
    work_hd(p, k, [fr.P(t, 0.0) for t in np.linspace(34.0, 56.0, 23)], head)
    fitting_hd(p, fr, k, 24.5, 30.0, 3.6, 1.0, line=27.2)
    gem_hd(p, k, *fr.P(27.2, 0.0), 1.7, fallback=False)
    p.sparkle(*fr.P(62.0, -1.0), 1)
    finish(p, k)


def shaft_hd(p, k, mat=None, feather=False):
    """A length of shaft broken at both ends: gold bands, a wrapped hand in the chain's silk; `feather` ties a
    heron's white feather under the upper band."""
    c, fr = p.c, WFRAME
    mat = mat or k['tint']
    shaft = fr.prof(c, [(4.0, 3.4), (70.0, 3.4)])
    p.cylinder(fr, shaft, 3.4, mat, sep=True, tex=CHAIN_TEX.get(mat.kind, 'wood'), axis=45.0)
    shaft = broken_hd(p, fr, shaft, 9.0, 3.4, False, mat, teeth=3)
    shaft = broken_hd(p, fr, shaft, 64.0, 3.4, True, mat, teeth=3)
    mid = shaft & fr.prof(c, [(24.0, 3.4), (38.0, 3.4)])
    p.part(mid, k['wrap'], 'field', base=0, field=fr.field(c, 3.4)[1], bands=((0.18, 2), (0.42, 1), (0.66, 0), (0.86, -1), (9, -2)), sep=True)
    wrap_hd(p, fr, k, mid, 3.4)
    for t0 in (20.0, 44.0):
        fitting_hd(p, fr, k, t0 - 1.6, t0 + 1.6, 3.9, 0.4)
    if feather:
        fx, fy = fr.P(46.0, 4.6)
        vane = c.leaf(fx, fy, -60, 15.0, 6.5, 0.15)
        p.part(vane, M('bone', 'porcelain'), 'ray_soft', base=1, sep=True, rim=False)
        p.decal(lmask(p, [(fx, fy), (fx + 6.5, fy + 11.5)]) & erode4(vane), M('bone', 'porcelain'), -2)
        p.part(c.circle(fx, fy, 1.4), k['tassel'], 'sphere', base=0, sep=True, rim=False)
    p.sparkle(*fr.P(52.0, -1.8), 1)
    finish(p, k)


def tassel_piece_hd(p, k):
    """A weapon's tassel on its own: the cord loop, a gold bead, the knot, a gold band gathering the skirt of
    strands in the chain's silk."""
    c = p.c
    silk = k['tassel']
    p.part(c.ring(32, 9.0, 4.6, 2.2) & c.box(0, 0, 64, 11.4), silk, 'ray_soft', base=0, sep=False, rim=False)
    p.part(c.box(30.6, 11, 33.4, 15), silk, 'flat', base=0, sep=False, rim=False)
    p.part(c.circle(32, 18.0, 4.2), GOLD, 'sphere', base=1, sep=True, spec=(30.5, 16.5))
    knot = c.ellipse(32, 26.5, 7.5, 5.5)
    p.part(knot, silk, 'sphere', base=0, sep=True, rim=False)
    p.decal(lmask(p, [(26, 24), (32, 29), (38, 24)]) & knot, silk, -2)
    p.decal(lmask(p, [(26, 29), (32, 24), (38, 29)]) & knot, silk, -2)
    for i in range(7):
        x0 = 24.5 + i * 2.5
        x1 = 19.0 + i * 4.3
        m = c.taper((x0, 31.0), ((x0 + x1) / 2.0 + (1.0 if i % 2 else -1.0), 44.0), (x1, 57.0), 2.8, 1.6)
        p.part(m, silk, 'ray_soft', base=(1 if i in (2, 3) else 0), sep=True, rim=False)
    p.part(c.box(25.0, 30.0, 39.0, 33.6), GOLD, 'vgrad', base=1, sep=True, tex='metal')
    p.sparkle(28, 22, 1)
    finish(p, k)


def sheath_hd(p, k):
    """A sheath on the diagonal: lacquer in the chain's tint, a gold throat and chape, a band with the grade's work,
    a cord loop with its bead."""
    c, fr = p.c, WFRAME
    body = fr.prof(c, [(3.0, 3.8), (6.0, 4.8), (56.0, 4.8), (58.0, 4.4)])
    p.cylinder(fr, body, 4.8, k['tint'], sep=True, tex=k['tex'], axis=45.0)
    work_hd(p, k, [fr.P(t, 0.0) for t in np.linspace(14.0, 32.0, 19)], body)
    fitting_hd(p, fr, k, 2.5, 9.0, 5.2, 1.4)
    fitting_hd(p, fr, k, 52.0, 59.0, 5.4, 1.0, line=55.5)
    fitting_hd(p, fr, k, 34.0, 38.0, 5.2, 0.4)
    lx, ly = fr.P(40.0, 7.6)
    p.part(c.ring(lx, ly, 3.4, 1.8), k['tassel'], 'ray_soft', base=0, sep=True, rim=False)
    p.part(c.circle(lx - 1.0, ly + 3.4, 2.0), GOLD, 'sphere', base=1, sep=True)
    gem_hd(p, k, *fr.P(55.5, 0.0), 1.8, fallback=False)
    p.sparkle(*fr.P(46.0, -2.4), 1)
    finish(p, k)


def cap_hd(p, k):
    """The Ferryman's iron cap: the pole's ferrule, ringed, its end rounded, a gold band at its mouth, the oak stub
    still in it, broken."""
    c, fr = p.c, WFRAME
    stub = fr.prof(c, [(4.0, 3.4), (28.0, 3.4)])
    p.cylinder(fr, stub, 3.4, k['tint'], sep=True, tex='wood', axis=45.0)
    broken_hd(p, fr, stub, 9.0, 3.4, False, k['tint'], teeth=3)
    cap = fr.prof(c, [(26.0, 4.0), (28.5, 5.6), (52.0, 5.6), (56.0, 4.6), (58.0, 2.4), (58.6, 0.0)])
    p.cylinder(fr, cap, lambda t: np.interp(t, [26.0, 28.5, 52.0, 56.0, 58.6], [4.0, 5.6, 5.6, 4.6, 0.0]), IRON, sep=True, tex='metal', axis=45.0)
    for t0 in (36.0, 46.0):
        p.line([fr.P(t0, -5.0), fr.P(t0, 5.0)], IRON, -2, 1.0)
        p.line([fr.P(t0 + 1.0, -5.0), fr.P(t0 + 1.0, 5.0)], IRON, 1, 1.0)
    fitting_hd(p, fr, k, 26.0, 31.0, 6.0, 1.2, line=28.5)
    p.sparkle(*fr.P(50.0, -3.0), 1)
    finish(p, k)


def knot_hd(p, k):
    """The Ferryman's knot: two loops of oak-brown rope crossed, their tails trailing, a gold bead where they meet."""
    c = p.c
    rope = tint_mat('#b08a5a', 'cloth') if k['tint'].kind == 'wood' else k['tassel']
    a = c.ring(25.5, 29.0, 12.0, 5.6)
    b = c.ring(38.5, 33.0, 12.0, 5.6)
    p.part(a, rope, 'ray_soft', base=0, sep=False, rim=False)
    p.part(b, rope, 'ray_soft', base=0, sep=True, rim=False)
    p.part(a & c.box(0, 0, 33, 33), rope, 'ray_soft', base=0, sep=True, rim=False)
    X, Y = p.c.X / p.s, p.c.Y / p.s
    for m in (a, b):
        p.decal(erode4(m) & (np.floor((X + Y) / 3.0).astype(int) % 2 == 0), rope, -1)
        p.decal(erode4(m) & ~erode4(erode4(m)) & (X + Y < 64), rope, 1)
    for (p0, p1, p2) in (((15.0, 38.0), (10.0, 46.0), (9.0, 57.0)), ((49.0, 24.0), (54.0, 16.0), (55.0, 7.0))):
        p.part(c.taper(p0, p1, p2, 4.4, 2.4), rope, 'ray_soft', base=0, sep=True, rim=False)
        p.part(c.circle(p2[0], p2[1], 2.4), rope, 'sphere', base=-1, sep=True, rim=False)
    p.part(c.circle(32.0, 31.0, 3.4), GOLD, 'sphere', base=1, sep=True, spec=(30.8, 29.8))
    finish(p, k)


def guard_hd(p, k):
    """The Mountainsplit's disc guard: a broad disc in the chain's steel, a raised rim and gold rivets, the gem set
    in it, the tang's slot with the broken tang still standing in it."""
    c = p.c
    cx, cy = 32.0, 36.0
    tang = c.box(29.0, 10.0, 35.0, 30.0)
    p.part(tang, k['tint'], 'hgrad', base=0, sep=True, tex=k['tex'])
    fr = Frame((32.0, 30.0), 90.0)
    broken_hd(p, fr, tang, 17.0, 3.0, True, k['tint'], teeth=2)
    disc = c.ellipse(cx, cy, 25.0, 15.0)
    p.part(disc, k['tint'], 'ray', base=0, sep=True, tex=k['tex'])
    p.decal(c.ring(cx, cy, 25.0, 2.4, ry=15.0) & disc, k['tint'], -1)
    p.decal(c.ring(cx, cy, 22.6, 1.0, ry=12.6) & disc, k['tint'], 2)
    p.part(c.rrect(28.6, 30.0, 35.4, 40.0, 1.4), INKM, 'flat', base=0, sep=True, rim=False)
    p.decal(c.box(29.6, 31.0, 34.4, 32.0), INKM, 2)
    for (x, y) in ((cx - 17.0, cy), (cx + 17.0, cy), (cx, cy + 10.0)):
        p.part(c.circle(x, y, 2.0), GOLD, 'sphere', base=1, sep=True, rim=False)
    gem_hd(p, k, cx, cy + 10.0, 2.4)
    p.decal(c.arc(cx, cy, 20.0, 1.2, 120, 170, ry=11.0) & disc, k['tint'], 3)
    finish(p, k)


def rib_hd(p, k):
    """The Seven Winds' rib: a fan's guard stick on the diagonal, the pivot hole with its gold rivet, wind curls
    carved along it, a gold cap at the head."""
    c, fr = p.c, WFRAME
    stick = fr.prof(c, [(2.0, 3.0), (30.0, 3.4), (62.0, 4.0), (67.0, 3.4)])
    p.cylinder(fr, stick, lambda t: np.interp(t, [2.0, 30.0, 62.0, 67.0], [3.0, 3.4, 4.0, 3.4]), k['tint'], sep=True, tex=k['tex'], axis=45.0)
    hx, hy = fr.P(7.0, 0.0)
    p.part(c.ring(hx, hy, 2.6, 1.3), GOLD, 'ray_soft', base=1, sep=True)
    p.decal(c.circle(hx, hy, 1.3), INKM, 0)
    for t0 in (22.0, 34.0, 46.0):
        x, y = fr.P(t0, 0.0)
        curl = c.arc(x, y, 2.6, 1.2, 300, 200) | c.box(x + 0.4, y + 1.4, x + 5.0, y + 2.6)
        p.decal(dilate4(curl) & stick & ~curl, k['tint'], -2)
        p.decal(curl & stick, k['tint'], 2)
    fitting_hd(p, fr, k, 62.0, 67.5, 4.4, 1.0, line=65.0)
    p.sparkle(*fr.P(54.0, -2.2), 1)
    finish(p, k)


def silk_hd(p, k):
    """The Seven Winds' silk: a fragment of the fan's leaf in its folds, a gold band along its arc, the inner edge
    torn, two wind curls in gold."""
    c = p.c
    px, py, R0, R1, a0, a1 = 12.0, 58.0, 24.0, 52.0, 16.0, 72.0
    silk = k['tassel']
    leaf = c.sector(px, py, R1, a0, a1) & ~c.circle(px, py, R0)
    for (x, y, r) in ((30.0, 43.0, 3.6), (22.0, 36.0, 2.8), (39.0, 51.0, 3.0), (34.0, 36.0, 2.4)):
        leaf &= ~c.circle(x, y, r)
    p.part(leaf, silk, 'ray_soft', base=0, sep=True, tex='cloth', axis=45.0, rim=False)

    def ray(a, r0, r1):
        a = math.radians(a)
        return (px + r0 * math.cos(a), py - r0 * math.sin(a), px + r1 * math.cos(a), py - r1 * math.sin(a))
    for i in range(7):
        if i % 2:
            p.decal(c.sector(px, py, R1, a0 + 8.0 * i, a0 + 8.0 * (i + 1)) & leaf, silk, -1)
    for i in range(1, 7):
        p.decal(c.seg(*ray(a0 + 8.0 * i, R0, R1), 1.0) & leaf, silk, -2)
    band = c.arc(px, py, R1, 3.0, a0, a1) & leaf
    p.part(band, GOLD, 'flat', base=0, sep=True, rim=False, tex='metal')
    for (a, r) in ((30.0, 40.0), (56.0, 42.0)):
        x, y = px + r * math.cos(math.radians(a)), py - r * math.sin(math.radians(a))
        curl = c.arc(x, y, 3.2, 1.4, 300, 200) | c.box(x + 0.6, y + 1.8, x + 6.0, y + 3.2)
        p.decal(dilate4(curl) & leaf & ~curl, silk, -2)
        p.decal(curl & leaf, GOLD, 1)
    p.sparkle(46, 22, 1)
    finish(p, k)


def pin_hd(p, k):
    """The Seven Winds' pin: the fan's gold rivet on the diagonal, a washer, a round head set with the chain's gem, a
    small ring at its foot."""
    c, fr = p.c, WFRAME
    fx, fy = fr.P(4.0, 0.0)
    p.part(c.ring(fx, fy, 3.6, 1.8), GOLD, 'ray_soft', base=0, sep=False, tex='metal')
    shaft = fr.prof(c, [(6.0, 2.4), (46.0, 2.4)])
    p.cylinder(fr, shaft, 2.4, GOLD, sep=True, tex='metal', axis=45.0)
    fitting_hd(p, fr, k, 38.0, 43.0, 3.6, 0.6)
    wx, wy = fr.P(47.0, 0.0)
    p.part(c.ellipse(wx, wy, 7.4, 7.4), GOLD, 'ray', base=0, sep=True, tex='metal')
    p.decal(c.ring(wx, wy, 7.4, 1.2), GOLD, -2)
    hx, hy = fr.P(55.0, 0.0)
    p.part(c.circle(hx, hy, 7.6), GOLD, 'sphere', base=1, sep=True, spec=(hx - 2.6, hy - 2.6))
    gem_hd(p, k, hx + 0.4, hy + 0.4, 4.4)
    p.sparkle(*fr.P(28.0, -1.6), 1)
    finish(p, k)


def mouthpiece_hd(p, k):
    """The Crane's bone mouthpiece: a short length of crane bone, banded in gold, the blow hole cut in it, carved
    rings at each end."""
    c, fr = p.c, WFRAME
    tube = fr.prof(c, [(10.0, 5.8), (54.0, 5.8)])
    p.cylinder(fr, tube, 5.8, k['tint'], sep=True, tex='metal', axis=45.0)
    hx, hy = fr.P(34.0, -0.4)
    p.part(c.ellipse(hx, hy, 2.8, 2.2), INKM, 'flat', base=0, sep=True, rim=False)
    p.decal(c.arc(hx, hy, 2.4, 1.0, 20, 160), INKM, 2)
    for t0 in (20.0, 44.0):
        p.line([fr.P(t0, -5.2), fr.P(t0, 5.2)], k['tint'], -2, 1.0)
        p.line([fr.P(t0 - 1.0, -5.2), fr.P(t0 - 1.0, 5.2)], k['tint'], 2, 1.0)
    fitting_hd(p, fr, k, 9.0, 14.0, 6.4, 1.0)
    fitting_hd(p, fr, k, 50.0, 55.0, 6.4, 1.0, line=52.5)
    p.sparkle(*fr.P(26.0, -3.4), 1)
    finish(p, k)


def flute_body_hd(p, k):
    """The Crane's jade body: the flute's length in pale jade, its finger holes, gold bands at each end and the
    grade's work near the foot."""
    c, fr = p.c, WFRAME
    body = fr.prof(c, [(3.0, 3.4), (69.0, 3.4)])
    p.cylinder(fr, body, 3.4, k['tint'], sep=True, tex='jade', axis=45.0)
    for i in range(6):
        p.decal(c.circle(*fr.P(26.0 + 5.0 * i, 0.0), 1.3), INKM, 0)
    work_hd(p, k, [fr.P(t, 0.0) for t in np.linspace(9.0, 19.0, 11)], body)
    fitting_hd(p, fr, k, 2.5, 6.5, 3.8, 0.7)
    fitting_hd(p, fr, k, 65.5, 69.5, 3.8, 0.7)
    fitting_hd(p, fr, k, 21.0, 23.5, 3.8, 0.0)
    p.sparkle(*fr.P(58.0, -1.4), 1)
    finish(p, k)


def limb_hd(p, k):
    """The Dragonfly's limb: one limb of the bow, bowed to the upper left and curling back at the nock, veined like
    a wing, its root wrapped in the chain's silk under a gold band, a gold tip."""
    c, fr = p.c, WFRAME

    def at(u):
        t = 4.0 + 62.0 * u
        w = 1.0 - 11.0 * (1.0 - (2.0 * u - 1.0) ** 2) - 3.0 * max(0.0, (u - 0.8) / 0.2) ** 1.5
        return fr.P(t, w)
    pts = [at(i / 40.0) for i in range(41)]
    stave = c.empty()
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        stave |= c.seg(a[0], a[1], b[0], b[1], 5.4 - 3.0 * (i + 0.5) / 40.0)
    p.part(stave, k['tint'], 'ray', base=0, sep=True, tex=k['tex'], axis=45.0)
    inner = erode4(stave)
    p.decal(lmask(p, pts[3:37]) & inner, k['tint'], -2)
    for i in range(6, 36, 5):
        (x, y) = pts[i]
        p.decal(lmask(p, [(x - 2.5, y - 2.5), (x + 2.5, y + 2.5)]) & inner, k['tint'], -2)
    root = c.polyline(pts[:8], 5.6)
    p.part(root, k['wrap'], 'ray_soft', base=0, sep=True, rim=False)
    wrap_hd(p, Frame(pts[0], 45.0), k, root, 2.8)
    p.part(c.circle(pts[8][0], pts[8][1], 3.2), GOLD, 'sphere', base=1, sep=True)
    p.part(c.circle(pts[-1][0], pts[-1][1], 2.6), GOLD, 'sphere', base=1, sep=True)
    p.sparkle(pts[22][0] - 1.5, pts[22][1] - 1.5, 1)
    finish(p, k)


def string_hd(p, k):
    """The Dragonfly's string: a bowstring coiled in three turns, its loop end over the coil with a gold bead, the
    loose end hanging."""
    c = p.c
    silk = k['tassel']
    for i, y in enumerate((40.0, 34.0, 28.0)):
        m = c.ring(32.0, y, 21.0, 2.8, ry=8.0)
        p.part(m, silk, 'ray_soft', base=(0 if i % 2 else 1), sep=True, rim=False)
        p.decal(c.arc(32.0, y, 21.0 - 1.4, 1.0, 100, 200, ry=8.0 - 1.4) & m, silk, 2)
    loop = c.ring(45.0, 17.0, 5.0, 2.4)
    p.part(loop, silk, 'ray_soft', base=1, sep=True, rim=False)
    p.part(c.taper((40.5, 19.0), (34.0, 22.0), (30.0, 22.0), 2.6, 2.4), silk, 'flat', base=1, sep=True, rim=False)
    p.part(c.circle(40.0, 20.0, 2.6), GOLD, 'sphere', base=1, sep=True)
    p.part(c.taper((14.0, 44.0), (10.0, 50.0), (12.0, 57.0), 2.6, 1.6), silk, 'ray_soft', base=0, sep=True, rim=False)
    p.sparkle(20, 25, 1)
    finish(p, k)


def sight_hd(p, k):
    """The Dragonfly's sight: a gold ring on a short stem, a lens of the chain's glass in it with a fine cross and a
    bead at the centre."""
    c = p.c
    cx, cy = 32.0, 28.0
    p.part(c.box(30.2, 46.0, 33.8, 56.0), GOLD, 'hgrad', base=0, sep=True, tex='metal')
    p.part(c.ellipse(32.0, 56.5, 9.0, 3.0), GOLD, 'ray', base=0, sep=True, tex='metal')
    p.part(c.ring(cx, cy, 21.0, 4.4), GOLD, 'ray', base=0, sep=True, tex='metal')
    lens = c.circle(cx, cy, 16.8)
    p.part(lens, k['gem'], 'sphere', base=0, sep=True, cx=cx - 5, cy=cy - 5, rx=21, ry=21, tex='glass')
    p.decal(lmask(p, [(cx - 15.0, cy), (cx + 15.0, cy)]) & lens, GOLD, 1)
    p.decal(lmask(p, [(cx, cy - 15.0), (cx, cy + 15.0)]) & lens, GOLD, 1)
    p.decal(c.circle(cx, cy, 1.8) & lens, GOLD, 2)
    p.decal(c.arc(cx, cy, 12.5, 2.0, 110, 165) & lens, k['gem'], 3)
    for a in (45.0, 135.0, 225.0, 315.0):
        ar = math.radians(a)
        p.part(c.circle(cx + 21.0 * math.cos(ar), cy - 21.0 * math.sin(ar), 1.8), GOLD, 'sphere', base=2, sep=True, rim=False)
    finish(p, k)


def knuckle_hd(p, k):
    """The Stone Drum's knuckle: four domed plates of drum stone riveted to a leather strap, a drum's ring carved in
    each, the Mystic grade's gold lines along the strap."""
    c = p.c
    strap = c.rrect(7.0, 36.0, 57.0, 50.0, 3.0)
    p.part(strap, LEATHER, 'ray', base=0, sep=True)
    for y in (38.5, 47.0):
        p.decal(c.box(9.0, y, 55.0, y + 1.0) & strap, GOLD, 0)
    for i in range(4):
        x0 = 8.5 + i * 12.0
        plate = c.rrect(x0, 18.0, x0 + 11.0, 40.0, 4.6)
        p.part(plate, k['tint'], 'bevel', base=0, sep=True, hw=2, sw=2, tex='metal')
        grain_hd(p, plate, k['tint'], i)
        p.decal(c.ring(x0 + 5.5, 27.0, 3.2, 1.0) & plate, k['tint'], -2)
        p.decal(c.circle(x0 + 5.5, 27.0, 1.4) & plate, k['tint'], 2)
        for (px, py) in ((x0 + 2.4, 36.5), (x0 + 8.6, 36.5)):
            p.decal(c.circle(px, py, 0.9) & plate, GOLD, 2)
    gem_hd(p, k, 52.0, 43.0, 2.6)
    p.sparkle(11, 21, 1)
    finish(p, k)


def cuff_hd(p, k):
    """The Stone Drum's cuff: the gauntlet's cuff in drum stone, two gold trim bands with the grade's work between
    them, the gem at the wrist, a drum's ring carved round it."""
    c = p.c
    cuff = c.poly([(15.0, 13.0), (49.0, 13.0), (56.0, 52.0), (8.0, 52.0)])
    p.part(cuff, k['tint'], 'ray', base=0, sep=True, tex='metal', axis=90.0)
    grain_hd(p, cuff, k['tint'])
    for y in (16.0, 45.0):
        p.part(c.box(7.5, y, 56.5, y + 3.4) & dilate4(cuff), GOLD, 'bevel', base=0, sep=True, hw=1, sw=1, rim=False)
    work_hd(p, k, [(x, 24.5) for x in np.linspace(17.0, 47.0, 31)], cuff, dark=k['tint'])
    work_hd(p, k, [(x, 40.0) for x in np.linspace(14.0, 50.0, 37)], cuff, dark=k['tint'])
    p.decal(c.ring(32.0, 32.0, 7.6, 1.2) & cuff, k['tint'], -2)
    p.decal(c.ring(32.0, 32.0, 6.4, 1.0) & cuff, k['tint'], 1)
    gem_hd(p, k, 32.0, 32.0, 3.4)
    p.sparkle(20, 21, 1)
    finish(p, k)


def weapon_soul_crystal_hd(p):
    """A long faceted crystal of gold glass with a flame inside it: it wakes a weapon forged to its limit."""
    c = p.c
    whole = crystal_hd(p, 32.0, 56.0, 90.0, 50.0, 11.0, GOLD_GLASS)
    inner = erode4(erode4(whole))
    fl = S.flame(c, 32.0, 47.0, 12.0, 22.0, 0.1) & inner
    p.decal(dilate4(fl) & inner & ~fl, GOLD_GLASS, -2)
    p.decal(fl, EMBER, 0)
    p.decal(S.flame(c, 32.0, 46.0, 6.0, 12.0, -0.1) & fl, EMBER, 2)
    p.decal(c.ellipse(31.5, 42.0, 2.0, 3.0) & fl, WHITE, 0)
    p.part(c.box(19.0, 54.0, 45.0, 59.0), GOLD, 'vgrad', base=0, sep=True, tex='metal')
    p.glow('#FFD27A', 0.6)


# ============================================================================= the table
PIECES_HD = {
    'stone_drum_knuckle': knuckle_hd, 'stone_drum_cuff': cuff_hd, 'stone_drum_heart': heart_hd,
    'riverlight_hilt': hilt_hd, 'riverlight_blade': lambda p, k: blade_piece_hd(p, k, 'straight'), 'riverlight_soul': heart_hd,
    'heron_spearhead': spearhead_hd, 'heron_shaft': lambda p, k: shaft_hd(p, k, feather=True), 'heron_tassel': tassel_piece_hd,
    'reedwhisper_edge': lambda p, k: blade_piece_hd(p, k, 'leaf'), 'reedwhisper_grip': lambda p, k: hilt_hd(p, k, 'tang'), 'reedwhisper_sheath': sheath_hd,
    'ferryman_iron_cap': cap_hd, 'ferryman_oak_shaft': shaft_hd, 'ferryman_knot': knot_hd,
    'mountainsplit_spine': lambda p, k: blade_piece_hd(p, k, 'spine'), 'mountainsplit_edge': lambda p, k: blade_piece_hd(p, k, 'sabre'), 'mountainsplit_guard': guard_hd,
    'seven_winds_rib': rib_hd, 'seven_winds_silk': silk_hd, 'seven_winds_pin': pin_hd,
    'crane_mouthpiece': mouthpiece_hd, 'crane_jade_body': flute_body_hd, 'crane_tassel': tassel_piece_hd,
    'dragonfly_limb': limb_hd, 'dragonfly_string': string_hd, 'dragonfly_sight': sight_hd,
}

for _ch in CHAINS:
    _k = chain_kit(_ch)
    for _pid, _pname, _src, _chance, _zone in _ch['pieces']:
        _draw = (lambda p, f=PIECES_HD[_pid], k=_k: f(p, k))
        register(FAM, _pid, _draw, GROUP)
        hd(_pid, _draw)
register(FAM, 'weapon_soul_crystal', weapon_soul_crystal_hd, GROUP)
hd('weapon_soul_crystal', weapon_soul_crystal_hd)
