"""Technique emblems (HD, Style A): one composer, its parts as tables.

An emblem is composed from four layers (docs/technique_plan.md §3.9, the emblem grammar): the element's domed
DISC, the form's MARK (the form's verb, drawn once, with the family's WEAPON inset placed where the form asks),
a RIM for the grade or the kind (a secret art, a keystone, a Dao art, a lost art) and a path STAMP at the lower
right. `emblem(element, form, family, grade, kind, path)` returns the drawing `draw(p)`; the build renders it at
64 (the page slot), 48 (the HUD technique ring) and 32 (the small slots). Every part is drawn once, so the arts
P13 generates need no new drawing: a row's element, form, family, grade, kind and path pick the parts. A
keystone, a Dao art or a lost art may bring a HAND mark of its own instead of a form.

Today's 66 icons are the 56 rows of data/techniques.json (element, family, grade and path flags from the data;
the form from FORM_OF, the plan's 24 forms) and the ten secret arts (SECRET_ARTS: an element and a hand mark,
under the secret rim). A path art's mark takes the path's colour as well as its stamp, so the same form reads
as the path's at a glance.

Geometry: icon space 64, the disc centred at (32, 32), rim radius 30, the dome inside 26. A weapon inset lies
along a `Frame` from its butt (t = 0) to its point (t = L); PLACES names the frames the forms use.
"""
import json
import sys
import math
import os

import numpy as np

from pix import Frame, Ramp, dilate4, erode4, move
from palette import M, mat7
from registry import hd, register

FAM, GROUP = 'techniques', 'techniques'
ART = 64   # HD (tools/icons/README.md, "How to convert a family")
PROJECT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))

CX, CY, R_RIM, R_DISC = 32.0, 32.0, 30.0, 26.0
DOME = ((0.93, 2), (0.74, 1), (0.44, 0), (0.1, -1), (-0.3, -2), (-9, -3))

# ----------------------------------------------------------------------------- discs (11 elements)
# element -> (disc ramp, mark ramp, steel ramp): the domed disc, the mark drawn on it, the steel of a weapon inset.
# Formless is the plan's pale paper disc, so its mark is ink and its steel dark.
_STEEL = ['#56687C', '#8A9CB0', '#CBD8E4', '#F0F6FA', '#FFFFFF']
DISCS = {
    'water': (['#081E2C', '#0F3A52', '#18607C', '#2E8AA6', '#62BCD0'], ['#1E5A70', '#4A9AB2', '#9EE0EC', '#DDF8FB', '#FFFFFF'], _STEEL),
    'wood': (['#0A2014', '#123A22', '#1C5A32', '#2E8248', '#5EB06A'], ['#2A6A34', '#5AA052', '#B0E08A', '#E6F8CC', '#FFFFFF'], _STEEL),
    'fire': (['#2A0A08', '#4E140E', '#7C2414', '#B0401E', '#E27436'], ['#9A3012', '#DA6224', '#FFB850', '#FFEAA6', '#FFFFFF'], _STEEL),
    'earth': (['#1E1408', '#382610', '#5A3E1C', '#84602E', '#B48A4E'], ['#74522A', '#A87E40', '#E6C88A', '#FAEECC', '#FFFFFF'], _STEEL),
    'metal': (['#121A24', '#212E3C', '#344658', '#50667C', '#8098AE'], ['#56687C', '#8A9CB0', '#CBD8E4', '#F0F6FA', '#FFFFFF'], _STEEL),
    'wind': (['#0E3234', '#1A5254', '#2A8280', '#54B4AE', '#98DCD6'], ['#3A8A80', '#78C4B8', '#C6F0E8', '#EEFFFA', '#FFFFFF'], _STEEL),
    'thunder': (['#2A2206', '#4A3C0A', '#7A6412', '#B0921E', '#E0C43A'], ['#8A7418', '#C4A82A', '#F4E070', '#FFF6C0', '#FFFFFF'], _STEEL),
    'soul': (['#150C26', '#251640', '#3A2466', '#583C92', '#8A6CC4'], ['#553A90', '#8A6ACA', '#D0BCF6', '#F2EAFF', '#FFFFFF'], _STEEL),
    'formless': (['#6A6458', '#9E9580', '#CFC6AE', '#E8E1CF', '#FFFBEF'], ['#05090C', '#0D161C', '#1A2830', '#2E424C', '#4E6670'],
                 ['#121A24', '#212E3C', '#344658', '#50667C', '#8098AE']),
    'space': (['#0C0A24', '#1A1646', '#2C2874', '#4A44A6', '#7A72D2'], ['#4C46A0', '#8078D4', '#C4BCF4', '#ECE8FF', '#FFFFFF'], _STEEL),
    'time': (['#1A2A3C', '#2C4460', '#44688C', '#7098B8', '#A8CCE0'], ['#4E7A98', '#86B0C8', '#CCE8F4', '#EEF8FF', '#FFFFFF'], _STEEL),
}
ELEMENT_OF = {'none': 'formless'}   # the data's element keys that differ from the disc's

# ----------------------------------------------------------------------------- rims (13 grades) and kinds (4)
# band: the rim's metal (palette ramp); line: the keyline under the band's inner edge (the band's own light when
# absent); notch: small diamonds set into the band at the diagonals; dots: star dots round it; studs: the kind's
# studs on the band; torn: the lost art's rim, bitten out in three places.
RIMS = {
    'plain': dict(band='bronze'),
    'common': dict(band='bronze'),
    'earth': dict(band='jadeiron', line='jade'),
    'heaven': dict(band='silver', line='cloud'),
    'mystic': dict(band='mistjade_m', line='gold'),
    'spirit': dict(band='storm', line='silver', notch=4),
    'sage': dict(band='gold', line='jade', notch=4),
    'sovereign': dict(band='cometiron', line='driftteal', notch=4),
    'will': dict(band='nightsteel', line='starlight', dots=8),
    'sphere': dict(band='orchardsteel', line='rosegold', notch=4),
    'law': dict(band='starlight', line='gold', dots=8),
    'monarch': dict(band='rosegold', line='pearl', notch=8),
    'inner_heaven': dict(band='pearl', line='gold', notch=8),
    'genesis': dict(band='gold', line='pearl', notch=8, dots=8),
}
KINDS = {
    'secret': dict(band='gold', line='gold', studs=4),
    'keystone': dict(band='gold', line='gold', studs=8),
    'dao': dict(band='jade', line='jade', studs=6),
    'lost': dict(torn=True),
}

# ----------------------------------------------------------------------------- paths (5)
# mark: the ramp a path art's mark is drawn in (None keeps the element's pale mark); the stamp is drawn by STAMPS.
PATHS = {
    'body': dict(mark=None, stamp=['#3E2918', '#664525', '#B87A3C', '#D8A060', '#F0D0A0']),
    'blood': dict(mark=['#6E0C12', '#B8283A', '#E45858', '#FF9C86', '#FFE0D8'], stamp=['#3A0508', '#6E0C12', '#B8283A', '#E45858', '#FF9C86']),
    'buddhist': dict(mark=['#9A6A20', '#D09A3A', '#FFE28C', '#FFF7D8', '#FFFFFF'], stamp=['#6E4A1C', '#A8772F', '#D9A632', '#FFE6A1', '#FFF8E2']),
    'poison': dict(mark=['#3E5E14', '#6E9A1E', '#A8D23E', '#E2F88A', '#F6FFD0'], stamp=['#1E3A10', '#3E6416', '#6AA82C', '#A8D23E', '#E2F88A']),
    'confucian': dict(mark=['#2E3780', '#4A5AB8', '#7A8AE0', '#C6CEF8', '#F0F2FF'], stamp=['#1E2350', '#2E3780', '#4A5AB8', '#7A8AE0', '#C6CEF8']),
}
PATH_FLAGS = (('body', 'body'), ('blood_path', 'blood'), ('needs_vow', 'buddhist'), ('poison_path', 'poison'), ('confucian_path', 'confucian'))

# ----------------------------------------------------------------------------- the disc, the rim and the mark
def keyline(p, m, mk):
    """The mark's dark keyline, a pixel wider on the lower right (the shadow under it)."""
    ring = dilate4(m) & ~m
    p.decal(ring | (move(ring, 1, 1) & ~m), mk.out, 0)


def mark_hd(p, m, mk, base=0, mode='ray', **kw):
    keyline(p, m, mk)
    return p.part(m, mk, mode, base=base, sep=False, rim=False, **kw)


def disc_hd(p, element, grade='common', kind=None):
    """Paint the rim band and the domed disc; returns the disc mask, the rim's spec and the disc ramp."""
    c = p.c
    disc_c = DISCS[element][0]
    disc = mat7(Ramp(disc_c, '#05080B'), 'matte')
    spec = KINDS[kind] if kind in KINDS else RIMS[grade]
    if 'band' not in spec:
        spec = dict(RIMS[grade], **spec)
    band = M(spec['band'])
    line = M(spec['line']) if spec.get('line') else band
    p.part(c.circle(CX, CY, R_RIM), band, 'sphere', base=-1, sep=False, rim=False)
    inner = c.circle(CX, CY, R_DISC)
    p.part(inner, disc, 'sphere', base=0, sep=True, bands=DOME, rim=False)
    p.decal(c.arc(CX, CY, 22.5, 2.2, 108, 160) & inner, disc, 2)      # the dome's gloss, top-left
    p.decal(inner & ~erode4(inner), disc, -3)
    p.decal(c.ring(CX, CY, 27.6, 1.0), line, 1)
    for k in range(spec.get('notch', 0)):
        a = math.radians(45 + 360.0 * k / spec['notch'])
        p.part(c.diamond(CX + 28 * math.cos(a), CY - 28 * math.sin(a), 2.2), line, 'flat', base=1, sep=True, rim=False)
    for k in range(spec.get('dots', 0)):
        a = math.radians(22.5 + 360.0 * k / spec['dots'])
        p.decal(c.circle(CX + 28 * math.cos(a), CY - 28 * math.sin(a), 1.1), line, 2)
    for k in range(spec.get('studs', 0)):
        a = math.radians(90 + 360.0 * k / spec['studs'])
        p.part(c.diamond(CX + 27.2 * math.cos(a), CY - 27.2 * math.sin(a), 3.4), band, 'ray', base=2, sep=True, rim=False)
    return inner, spec, disc


def tear_rim(p):
    """The lost art's rim: the band torn out in three places, a ragged edge bitten into the disc along each tear."""
    c = p.c
    for (a0, a1) in ((14, 52), (140, 166), (244, 290)):
        tear = c.arc(CX, CY, 29.5, 4.4, a0, a1)
        for k in range(a0, a1, 7):
            a = math.radians(k + 3)
            tear |= c.circle(CX + 26.4 * math.cos(a), CY + 26.4 * math.sin(a), 1.6 + (k % 3) * 0.5)
        p.erase(tear)


# ----------------------------------------------------------------------------- the context a mark is drawn in
# The weapon inset's frames: (butt, angle, length). 'diag' crosses the disc; the small ones sit in a quarter.
PLACES = {
    'diag': ((15.0, 49.0), 45.0, 34.0),
    'sw': ((9.0, 55.0), 45.0, 20.0),
    'nw': ((9.0, 24.0), 45.0, 20.0),
    'se': ((41.0, 55.0), 45.0, 20.0),
    'centre': ((32.0, 45.0), 90.0, 26.0),
    'pivot': ((30.0, 35.0), 60.0, 26.0),
    'down': ((32.0, 8.0), -90.0, 34.0),
    'release': ((21.0, 51.0), 68.0, 36.0),
    'hand': ((45.0, 41.0), 62.0, 18.0),
}


class Ctx:
    """What a mark draws with: the painter, the disc mask, the mark and steel materials and the family."""

    def __init__(self, p, inner, mk, steel, fam):
        self.p, self.c, self.inner, self.mk, self.steel, self.fam = p, p.c, inner, mk, steel, fam

    def key(self, m):
        keyline(self.p, m & self.inner, self.mk)

    def fill(self, m, base=0, mode='ray', mat=None, **kw):
        """A part of the mark without a keyline (base: the mark level; kw: the painter's shading options)."""
        return self.p.part(m & self.inner, mat or self.mk, mode, base=base, sep=False, rim=False, **kw)

    def verb(self, m, base=0, mode='ray', mat=None, **kw):
        """A keylined part of the mark."""
        self.key(m)
        return self.fill(m, base, mode, mat, **kw)

    def light(self, m, lv=1):
        """A flat pale detail without a keyline (speed lines, ground, ripples)."""
        return self.p.part(m & self.inner, self.mk, 'flat', base=lv, sep=False, rim=False)

    def dark(self, m, lv=-3):
        """An engraved line on the mark (or the disc)."""
        return self.p.decal(m & self.inner, self.mk, lv)

    def spark(self, x, y, arm=1):
        self.p.sparkle(x, y, arm, self.mk[6])

    def frame(self, place, L=None):
        p0, ang, L0 = PLACES[place]
        return Frame(p0, ang), (L if L is not None else L0)

    def weapon(self, place, L=None):
        """The family's weapon inset at a PLACES frame; the free hand's open palm sits at PALM_AT instead, a little
        larger, since it is drawn upright. Returns the mask."""
        fr, L = self.frame(place, L)
        draw = WEAPONS.get(self.fam, WEAPONS['any'])
        if draw is w_palm and place in PALM_AT:
            return w_palm_at(self, PALM_AT[place][0], PALM_AT[place][1], max(L, 24.0))
        return draw(self, fr, L)


def _ang(fr):
    return math.degrees(math.atan2(-fr.u[1], fr.u[0]))


def _arrow(c, fr, t0, t1, w, head=6.0, hw=3.2, fletch=True):
    """An arrow along the frame from t0 (the nock) to t1 (the point)."""
    m = c.seg(*fr.P(t0, 0.0), *fr.P(t1 - head * 0.6, 0.0), w)
    m |= c.poly([fr.P(t1 + 0.4, 0.0), fr.P(t1 - head, hw), fr.P(t1 - head, -hw)])
    if fletch:
        for s in (1, -1):
            m |= c.seg(*fr.P(t0 + 2.0, 0.0), *fr.P(t0 - 1.5, 2.6 * s), w * 0.8)
    return m


def _projectile(x, fr, t0, t1, w=2.4):
    """What the family shoots, along the frame from t0 to t1: an arrow (bow), a note (flute, bell), a drop of ink
    (brush), a knife (the short blades, the rope dart), else a dart."""
    c, fam = x.c, x.fam
    if fam == 'bow':
        return _arrow(c, fr, t0, t1, w)
    if fam in ('flute', 'bell'):
        hx, hy = fr.P(t1 - 3.0, 0.0)
        return c.ellipse(hx, hy, 3.4, 2.6) | c.seg(hx + 2.4, hy, hx + 2.4, hy - 10.5, 1.8) | c.seg(hx + 2.4, hy - 10.5, hx + 6.0, hy - 7.5, 1.8)
    if fam == 'brush':
        return c.taper(fr.P(t0, 0.0), fr.P((t0 + t1) / 2.0, 0.0), fr.P(t1 - 3.0, 0.0), 1.2, 4.0) | c.circle(*fr.P(t1 - 3.0, 0.0), 3.2)
    if fam in ('short_blade', 'dual_blades', 'rope_dart'):
        return c.leaf(*fr.P(t0, 0.0), _ang(fr), t1 - t0, 5.6, 0.0, tip_power=0.6)
    return c.taper(fr.P(t0, 0.0), fr.P((t0 + t1) / 2.0, 0.0), fr.P(t1 - 4.0, 0.0), 1.6, 3.6) | c.poly([fr.P(t1 + 0.4, 0.0), fr.P(t1 - 5.0, 2.6), fr.P(t1 - 5.0, -2.6)])


def _figure(c, x, y, s=1.0):
    """A small standing figure: the head over a robe."""
    return c.circle(x, y - 12 * s, 5.2 * s) | c.poly([(x - 7 * s, y - 5 * s), (x + 7 * s, y - 5 * s), (x + 9 * s, y + 16 * s), (x - 9 * s, y + 16 * s)])


# ----------------------------------------------------------------------------- weapons (16 families and the free hand)
# Each draws its weapon along `fr` from the butt (t = 0) to the point (t = L), its widths scaled by L / 34, and
# returns its mask. Blades are steel with a ridge; shafts, grips and guards the mark's pale material.
def w_jian(x, fr, L):
    c, k = x.c, L / 34.0
    g, hw = 0.17 * L, 3.3 * k
    blade = fr.prof(c, [(g, hw), (0.86 * L, hw), (L, 0.0)])
    guard = fr.prof(c, [(g - 1.3 * k, 6.8 * k), (g + 1.3 * k, 6.8 * k)])
    grip = fr.prof(c, [(0.0, 2.3 * k), (g, 2.3 * k)]) | c.circle(*fr.P(0.6 * k, 0.0), 2.8 * k)
    x.key(blade | guard | grip)
    x.p.cylinder(fr, blade & x.inner, lambda t: np.where(t > 0.86 * L, np.clip(hw * (L - t) / (0.14 * L), 0, hw), hw), x.steel, ridge=True, sep=False, rim=False)
    x.fill(guard | grip, 0)
    return blade | guard | grip


def w_short_blade(x, fr, L):
    c, k = x.c, L / 34.0
    g = 0.3 * L
    blade = c.poly([fr.P(g, 2.4 * k), fr.P(0.7 * L, 2.4 * k), fr.P(L, -0.6 * k), fr.P(0.62 * L, -4.0 * k), fr.P(g, -2.6 * k)])
    guard = fr.prof(c, [(g - 1.0 * k, 4.8 * k), (g + 1.0 * k, 4.8 * k)])
    grip = fr.prof(c, [(0.0, 2.2 * k), (g, 2.2 * k)])
    x.key(blade | guard | grip)
    x.p.cylinder(fr, blade & x.inner, 3.0 * k, x.steel, ridge=True, sep=False, rim=False)
    x.fill(guard | grip, 0)
    return blade | guard | grip


def w_heavy_sabre(x, fr, L):
    c, k = x.c, L / 34.0
    g = 0.24 * L
    blade = c.poly([fr.P(g, 2.8 * k), fr.P(0.8 * L, 2.4 * k), fr.P(L, -3.0 * k), fr.P(0.88 * L, -5.6 * k), fr.P(0.5 * L, -6.2 * k), fr.P(g, -3.4 * k)])
    guard = c.circle(*fr.P(g, 0.0), 4.2 * k)
    grip = fr.prof(c, [(0.0, 2.4 * k), (g, 2.4 * k)])
    x.key(blade | guard | grip)
    x.p.cylinder(fr, blade & x.inner, 4.2 * k, x.steel, ridge=True, sep=False, rim=False)
    x.fill(guard | grip, 0)
    return blade | guard | grip


def w_spear(x, fr, L):
    c, k = x.c, L / 34.0
    shaft = fr.prof(c, [(0.0, 1.8 * k), (0.7 * L, 1.8 * k)])
    head = c.leaf(*fr.P(0.65 * L, 0.0), _ang(fr), 0.37 * L, 7.8 * k, 0.0, tip_power=0.6)
    tuft = c.taper(fr.P(0.66 * L, 2.0 * k), fr.P(0.6 * L, 5.5 * k), fr.P(0.6 * L, 9.0 * k), 2.6 * k, 1.4 * k)
    x.key(shaft | head | tuft)
    x.p.cylinder(fr, shaft & x.inner, 1.8 * k, x.mk, base=-1, sep=False, rim=False)
    x.p.cylinder(fr, head & x.inner, 3.9 * k, x.steel, ridge=True, sep=False, rim=False)
    x.fill(tuft, 0, 'ray_soft', M('red'))
    return shaft | head | tuft


def w_staff(x, fr, L):
    c, k = x.c, L / 34.0
    shaft = fr.prof(c, [(0.0, 2.2 * k), (L, 2.2 * k)])
    bands = c.empty()
    for t in (0.08 * L, 0.92 * L):
        bands |= fr.prof(c, [(t - 1.8 * k, 2.9 * k), (t + 1.8 * k, 2.9 * k)])
    x.key(shaft | bands)
    x.p.cylinder(fr, shaft & x.inner, 2.2 * k, x.mk, base=-1, sep=False, rim=False)
    x.fill(bands, 0, 'ray', x.steel)
    return shaft | bands


def w_bow(x, fr, L):
    c, k = x.c, L / 34.0
    limbs = c.taper(fr.P(0.0, 0.0), fr.P(0.5 * L, -0.52 * L), fr.P(L, 0.0), 2.8 * k, 2.8 * k)
    grip = c.circle(*fr.P(0.5 * L, -0.26 * L), 3.4 * k)
    x.key(limbs | grip)
    x.fill(limbs, 0)
    x.fill(grip, -1)
    x.light(c.seg(*fr.P(0.0, 0.0), *fr.P(L, 0.0), 1.2), 2)
    return limbs | grip


def w_fan(x, fr, L):
    c, k = x.c, L / 34.0
    px, py = fr.P(0.0, 0.0)
    a = _ang(fr)
    fan = c.sector(px, py, L, a - 34, a + 34) & ~c.circle(px, py, 0.16 * L)
    x.verb(fan, 0)
    for da in (-17, 0, 17):
        x.dark(c.seg(px, py, px + L * math.cos(math.radians(a + da)), py - L * math.sin(math.radians(a + da)), 1.0) & fan, -2)
    x.dark(c.arc(px, py, L, 2.0 * k, a - 34, a + 34) & fan, 2)
    x.fill(c.circle(px, py, 2.8 * k), 0, 'sphere', x.steel)
    return fan


def w_flute(x, fr, L):
    c, k = x.c, L / 34.0
    body = fr.prof(c, [(0.0, 1.9 * k), (L, 1.9 * k)])
    x.key(body)
    x.p.cylinder(fr, body & x.inner, 1.9 * k, x.mk, base=0, sep=False, rim=False)
    for t in (0.42, 0.56, 0.7):
        x.dark(c.circle(*fr.P(t * L, 0.0), 1.1 * k), -3)
    for t in (0.06, 0.94):
        x.dark(fr.prof(c, [(t * L - 0.8 * k, 1.9 * k), (t * L + 0.8 * k, 1.9 * k)]), -2)
    return body


def w_brush(x, fr, L):
    c, k = x.c, L / 34.0
    shaft = fr.prof(c, [(0.0, 1.8 * k), (0.68 * L, 1.8 * k)])
    ferrule = fr.prof(c, [(0.68 * L, 2.6 * k), (0.76 * L, 2.6 * k)])
    tip = c.taper(fr.P(0.76 * L, 0.0), fr.P(0.9 * L, 0.0), fr.P(L, 0.0), 5.0 * k, 1.0)
    x.key(shaft | ferrule | tip)
    x.p.cylinder(fr, shaft & x.inner, 1.8 * k, x.mk, base=-1, sep=False, rim=False)
    x.fill(ferrule, 0, 'ray', x.steel)
    x.fill(tip, 1)
    t = fr.along(c)[0]
    x.dark(tip & (t > 0.9 * L), -3)
    return shaft | ferrule | tip


def w_bell(x, fr, L):
    c, k = x.c, L / 34.0
    knob = c.circle(*fr.P(0.0, 0.0), 2.6 * k)
    handle = fr.prof(c, [(0.0, 1.6 * k), (0.3 * L, 1.6 * k)])
    body = fr.prof(c, [(0.3 * L, 3.4 * k), (0.55 * L, 4.6 * k), (0.82 * L, 6.0 * k), (0.9 * L, 7.6 * k), (0.97 * L, 8.0 * k)])
    clapper = c.circle(*fr.P(1.02 * L, 0.0), 2.0 * k)
    x.key(knob | handle | body | clapper)
    x.p.cylinder(fr, body & x.inner, 6.0 * k, x.mk, base=0, sep=False, rim=False)
    x.dark(fr.prof(c, [(0.89 * L, 8.0 * k), (0.91 * L, 8.0 * k)]) & body, -2)
    x.fill(knob | handle, -1)
    x.fill(clapper, 0, 'sphere', x.steel)
    return knob | handle | body | clapper


def w_fists(x, fr, L):
    c, k = x.c, L / 34.0
    cx, cy = fr.P(0.5 * L, 0.0)
    fist = c.rrect(cx - 9 * k, cy - 6 * k, cx + 9 * k, cy + 8 * k, 3.5 * k)
    for i in range(4):
        fist |= c.circle(cx - 6.75 * k + i * 4.5 * k, cy - 6 * k, 2.5 * k)
    thumb = c.rrect(cx - 9 * k, cy + 1 * k, cx + 3 * k, cy + 7 * k, 2.5 * k)
    wrist = c.box(cx - 5 * k, cy + 8 * k, cx + 6 * k, cy + 15 * k)
    x.key(fist | thumb | wrist)
    x.fill(fist, 0)
    for i in (-1, 0, 1):
        x.dark(c.seg(cx + i * 4.5 * k, cy - 5 * k, cx + i * 4.5 * k, cy + 0.5 * k, 1.0), -2)
    x.key(thumb)
    x.fill(thumb, 1)
    x.fill(wrist, -1)
    return fist | thumb | wrist


# Where the free hand's palm sits for each placement (its centre), in place of a weapon along the frame.
PALM_AT = {'diag': (34.0, 34.0), 'sw': (20.0, 38.0), 'nw': (19.0, 22.0), 'se': (44.0, 38.0), 'hand': (46.0, 34.0)}


def w_palm(x, fr, L):
    """The free hand: an open palm, upright, on the frame's middle."""
    return w_palm_at(x, *fr.P(0.5 * L, 0.0), L)


def w_palm_at(x, cx, cy, L):
    c, k = x.c, L / 34.0
    palm = c.rrect(cx - 8.5 * k, cy - 2 * k, cx + 8.5 * k, cy + 15 * k, 4 * k)
    for (fx, top, w) in ((-7 * k, -17 * k, 3.4 * k), (-2.5 * k, -20 * k, 3.6 * k), (2.5 * k, -19 * k, 3.6 * k), (7 * k, -15 * k, 3.2 * k)):
        palm |= c.rrect(cx + fx - w / 2, cy + top, cx + fx + w / 2, cy + 1 * k, 1.6 * k)
    palm |= c.poly([(cx - 9 * k, cy + 4 * k), (cx - 16 * k, cy - 4 * k), (cx - 13.5 * k, cy - 6 * k), (cx - 6 * k, cy + 1 * k)])
    x.verb(palm, 0)
    return palm


def w_dual_blades(x, fr, L):
    a = _ang(fr)
    cpt = fr.P(0.5 * L, 0.0)
    ub = (math.cos(math.radians(a - 90)), -math.sin(math.radians(a - 90)))
    fb = Frame((cpt[0] - ub[0] * 0.45 * L, cpt[1] - ub[1] * 0.45 * L), a - 90)
    m = w_short_blade(x, fb, 0.9 * L)
    return m | w_short_blade(x, Frame(fr.P(0.05 * L, 0.0), a), 0.9 * L)


def w_rope_dart(x, fr, L):
    c, k = x.c, L / 34.0
    pts = [fr.P(t, 2.8 * k * math.sin(t / (4.5 * k))) for t in np.linspace(0.0, 0.62 * L, 18)]
    rope = c.polyline(pts, 1.9 * k)
    ring = c.ring(*fr.P(0.62 * L, 0.0), 2.6 * k, 1.5 * k)
    head = c.leaf(*fr.P(0.62 * L, 0.0), _ang(fr), 0.4 * L, 6.6 * k, 0.0, tip_power=0.6)
    x.key(rope | ring | head)
    x.fill(rope, -1)
    x.fill(ring, 0)
    x.p.cylinder(fr, head & x.inner, 3.3 * k, x.steel, ridge=True, sep=False, rim=False)
    return rope | ring | head


def w_whip(x, fr, L):
    c, k = x.c, L / 34.0
    handle = fr.prof(c, [(0.0, 2.2 * k), (0.3 * L, 2.2 * k)])
    lash = c.taper(fr.P(0.3 * L, 0.0), fr.P(0.62 * L, -0.3 * L), fr.P(L, 0.02 * L), 2.6 * k, 1.0)
    x.key(handle | lash)
    x.p.cylinder(fr, handle & x.inner, 2.2 * k, x.mk, base=-1, sep=False, rim=False)
    x.fill(lash, 0)
    return handle | lash


def w_umbrella(x, fr, L):
    c, k = x.c, L / 34.0
    a = _ang(fr)
    handle = fr.prof(c, [(0.0, 1.6 * k), (0.62 * L, 1.6 * k)])
    t = fr.along(c)[0]
    hook = c.ring(*fr.P(0.0, 2.7 * k), 2.8 * k, 1.7 * k) & (t < 0.0)
    canopy = c.sector(*fr.P(0.62 * L, 0.0), 0.4 * L, a - 90, a + 90)
    tip = c.seg(*fr.P(0.62 * L, 0.0), *fr.P(L + 2.0 * k, 0.0), 1.5 * k)
    x.key(handle | hook | canopy | tip)
    x.fill(handle | hook, -1)
    x.verb(canopy, 0)
    for da in (-45, 0, 45):
        px, py = fr.P(0.62 * L, 0.0)
        x.dark(c.seg(px, py, px + 0.4 * L * math.cos(math.radians(a + da)), py - 0.4 * L * math.sin(math.radians(a + da)), 1.0) & canopy, -2)
    x.fill(tip, 0, 'ray', x.steel)
    return handle | hook | canopy | tip


WEAPONS = {'any': w_palm, 'fists': w_fists, 'gauntlets': w_fists, 'jian': w_jian, 'short_blade': w_short_blade,
           'heavy_sabre': w_heavy_sabre, 'spear': w_spear, 'staff': w_staff, 'bow': w_bow, 'fan': w_fan, 'flute': w_flute,
           'brush': w_brush, 'bell': w_bell, 'dual_blades': w_dual_blades, 'rope_dart': w_rope_dart, 'whip': w_whip,
           'umbrella': w_umbrella}


# ----------------------------------------------------------------------------- forms (the plan's 24)
# Each form draws its verb once and places the family's weapon where it belongs; the free hand draws a palm.
def f_strike(x):
    """The weapon across the disc and the blow bursting at its point."""
    c = x.c
    x.weapon('diag')
    sx, sy = 47.0, 17.0
    star = c.empty()
    for (dx, dy, ln) in ((1, 0, 8), (-1, 0, 8), (0, 1, 8), (0, -1, 8), (0.7, 0.7, 5), (-0.7, 0.7, 5), (0.7, -0.7, 5), (-0.7, -0.7, 5)):
        star |= c.seg(sx + dx * 2.5, sy + dy * 2.5, sx + dx * ln, sy + dy * ln, 2.8)
    x.verb(star, 2)
    x.fill(c.circle(sx, sy, 2.4), 3, 'flat')
    for (px, py) in ((11, 39), (19, 53)):
        x.light(c.seg(px, py, px - 6, py + 6, 1.8), -1)


def f_flurry(x):
    """Three quick slashes, one over the other, the weapon below them."""
    c = x.c
    x.weapon('sw', 18)
    for i, (px, py) in enumerate(((27, 30), (35, 36), (43, 42))):
        x.verb(c.seg(px, py, px + 11, py - 18, 3.4), 1 - (i == 1))


def f_thrust(x):
    """The weapon across the disc, its lance running on past the point, speed lines behind."""
    c = x.c
    x.weapon('diag')
    x.light(c.seg(41.5, 22.5, 51, 13, 2.4), 2)
    for (px, py) in ((13, 31), (21, 51), (9, 41)):
        x.light(c.seg(px, py, px - 7, py + 7, 1.8), -1)


def f_lunge(x):
    """Two chevrons driving right, dust behind, the weapon carried low."""
    c = x.c
    for dx, lv in ((0, 0), (12, 1)):
        x.verb(c.polyline([(27 + dx, 14), (40 + dx, 32), (27 + dx, 50)], 4.6), lv)
    for (px, py) in ((8, 26), (7, 32), (8, 38)):
        x.light(c.seg(px, py, px + 8, py, 2.0), -1)
    x.weapon('sw', 16)


def f_sweep(x):
    """A wide crescent through the lower half, swung from the weapon at its pivot."""
    c = x.c
    x.verb(c.arc(32, 22, 22, 7.0, 200, 340), 0)
    for a in (210, 230, 250):
        r = math.radians(a)
        x.light(c.seg(32 + 23 * math.cos(r), 22 - 23 * math.sin(r), 32 + 27 * math.cos(r), 22 - 27 * math.sin(r), 1.8), 1)
    x.weapon('pivot')


def f_arc(x):
    """A crescent of Qi sweeping up and right, the weapon's line inside it."""
    c = x.c
    x.verb(c.circle(30, 34, 19) & ~c.circle(37, 28, 18.5), 0)
    x.weapon('diag', 30)
    x.spark(43, 21, 1)


def f_volley(x):
    """Three of what the family shoots, fanning up and right from the weapon."""
    c = x.c
    x.weapon('sw', 18)
    for i, a in enumerate((28, 45, 62)):
        fr = Frame((24.0, 46.0), a)
        x.verb(_projectile(x, fr, 4.0, 30.0 + 3 * (i == 1)), 1)


def f_rain(x):
    """Five shafts falling on the ground, the weapon below."""
    c = x.c
    for (px, top, ln) in ((20, 14, 16), (28, 9, 20), (36, 13, 18), (44, 9, 20), (51, 16, 14)):
        x.verb(c.taper((px, top), (px - 1.5, top + ln / 2.0), (px - 3, top + ln), 3.2, 1.4), 0)
    x.light(c.seg(24, 47, 52, 47, 2.4), -1)
    for (px, r) in ((30, 3.4), (44, 3.0)):
        x.light(c.arc(px, 47, r, 1.6, 20, 160), 1)
    x.weapon('sw', 16)


def f_pillar(x):
    """A column falling on one point and the pool where it lands."""
    c = x.c
    left = [(30.0 - 0.06 * (y - 9) + 0.9 * math.sin(y / 3.0), float(y)) for y in range(9, 47)]
    right = [(34.0 + 0.06 * (y - 9) + 0.9 * math.sin(y / 3.0 + 1.3), float(y)) for y in range(46, 8, -1)]
    col = c.poly(left + right) | c.ellipse(32, 48, 9, 2.8)
    for (px, py) in ((21.5, 42.0), (42.5, 42.0), (18.5, 47.0), (45.5, 47.0)):
        col |= c.circle(px, py, 1.5)
    x.verb(col, 0)
    x.light(c.seg(31, 12, 31, 40, 1.0), 2)
    x.weapon('nw', 18)


def f_wave(x):
    """A wave breaking right: its body, the lip curling over the hollow tube, the swell under; the weapon above."""
    c = x.c
    body = (c.circle(33, 31, 17) & c.box(0, 0, 64, 31)) | c.box(16, 31, 50, 43)
    hollow = c.circle(43, 35, 8.5) | c.box(43, 35, 60, 43)
    crest = body & ~hollow
    swell = c.box(8, 44, 56, 50)
    x.verb(crest | swell, 0)
    x.light(c.arc(43, 35, 10.6, 1.8, 15, 150) & crest, 2)
    x.light(c.seg(12, 46.5, 52, 46.5, 1.2), 2)
    x.weapon('nw', 18)


def f_burst(x):
    """A burst from the centre round the caster; a weapon family holds its weapon in the heart of it."""
    c = x.c
    pts = []
    for k in range(16):
        a = k * math.pi / 8 + 0.2
        r = 22 if k % 2 == 0 else 10
        pts.append((32 + r * math.cos(a), 32 + r * math.sin(a)))
    x.verb(c.poly(pts), 0)
    x.fill(c.circle(32, 32, 7), 2, 'sphere')
    x.fill(c.circle(31, 31, 2.6), 3, 'flat')
    for (px, py) in ((17, 14), (49, 13), (52, 47), (14, 48)):
        x.light(c.circle(px, py, 1.4), 1)
    if x.fam != 'any':
        x.weapon('centre', 22)


def f_seeker(x):
    """Three of what the family shoots, homing on one mark from the weapon's side."""
    c = x.c
    x.weapon('sw', 16)
    x.verb(c.ring(46, 22, 5.2, 2.4), -1)
    x.fill(c.circle(46, 22, 1.6), 2, 'flat')
    if x.fam in ('flute', 'bell', 'brush'):
        for (px, py, a) in ((12, 24, 20), (20, 40, 35), (24, 12, 5)):
            x.verb(_projectile(x, Frame((float(px), float(py)), float(a)), 0.0, 13.0), 1)
        return
    for (p0, p1, p2) in (((12, 16), (26, 8), (39, 18)), ((10, 30), (26, 26), (39, 23)), ((18, 46), (30, 38), (40, 27))):
        x.verb(c.taper(p0, p1, p2, 1.4, 3.4), 1)


def f_return(x):
    """The weapon flying out on a loop and back."""
    c = x.c
    loop = c.ring(33, 31, 15, 3.4) & ~c.sector(33, 31, 20, 295, 350)
    x.verb(loop, 0)
    x.verb(c.poly([(33, 10), (26, 16), (33, 22)]), 1)
    fr = Frame((41.6, 43.3), 35.0)
    WEAPONS.get(x.fam, WEAPONS['any'])(x, fr, 18.0)


def f_snare(x):
    """A snare coiling in on its catch, the weapon below."""
    c = x.c
    pts = []
    for k in range(60):
        t = k / 59.0
        r, a = 18 - t * 16, t * 4.2 * math.pi
        pts.append((37 + r * math.cos(a), 29 + r * math.sin(a)))
    coil = c.empty()
    for a_, b_ in zip(pts, pts[1:]):
        coil |= c.seg(a_[0], a_[1], b_[0], b_[1], 3.2)
    x.verb(coil, 0)
    for (px, py) in ((53, 24), (24, 40), (44, 42)):
        x.verb(c.circle(px, py, 2.4), 1)
    x.weapon('sw', 16)


def f_counter(x):
    """The weapon held across the body, the blow turned aside on it."""
    c = x.c
    x.weapon('diag')
    x.verb(c.arc(36, 28, 20, 3.6, 128, 200), 1)
    x.spark(24, 26, 1)


def f_ward(x):
    """A shield round the self, the weapon beside it."""
    c = x.c
    shield = c.poly([(20, 14), (44, 14), (44, 31), (32, 47), (20, 31)])
    x.verb(shield, -1, 'bevel', hw=2, sw=2)
    x.dark(c.poly([(24, 18), (40, 18), (40, 30), (32, 41), (24, 30)]) & ~c.poly([(26, 20), (38, 20), (38, 29), (32, 38), (26, 29)]), -3)
    x.light(c.seg(32, 21, 32, 36, 2.4), 2)
    if x.fam != 'any':
        x.weapon('sw', 16)


def f_chorus(x):
    """Two companions under the canopy of one song."""
    c = x.c
    x.weapon('nw', 18)
    x.verb(c.arc(32, 46, 23, 3.6, 12, 168), 1)
    x.verb(c.arc(32, 46, 15, 3.0, 20, 160), 0)
    for px in (25, 40):
        x.verb(_figure(c, px, 46, 0.75), 0)


def f_blink(x):
    """The self left behind as a shade, the self arrived; the weapon in the arriving hand."""
    c = x.c
    x.fill(_figure(c, 19, 34), -2, 'flat')
    for py in (28, 34, 40):
        x.light(c.seg(29, py, 34, py, 1.6), 0)
    x.verb(_figure(c, 43, 34), 0)
    if x.fam != 'any':
        x.weapon('hand')


def f_plunge(x):
    """Down from above onto the ground, which cracks."""
    c = x.c
    if x.fam == 'any':
        x.verb(c.box(29.5, 9, 34.5, 34) | c.poly([(20, 32), (44, 32), (32, 46)]), 0)
    else:
        x.weapon('down')
    x.light(c.seg(14, 50, 50, 50, 2.6), -1)
    for (x0, x1) in ((18, 12), (46, 52)):
        x.light(c.seg(x0, 48, x1, 42, 1.8), 0)
    for (x0, y0, x1, y1) in ((22, 46, 17, 40), (42, 46, 47, 40)):
        x.light(c.seg(x0, y0, x1, y1, 1.6), 2)


def f_release(x):
    """The weapon flying free, point up, on the wide arc of its path."""
    c = x.c
    x.light(c.arc(32, 34, 21, 3.0, 195, 330), 0)
    x.weapon('release')
    for (px, py) in ((13, 22), (50, 20), (46, 50)):
        x.spark(px, py, 1)


def f_swarm(x):
    """Six of the weapon orbiting a bright heart, every point outward."""
    c = x.c
    x.light(c.ring(32, 32, 13, 1.6), -1)
    for k in range(6):
        a = math.radians(k * 60 + 20)
        fr = Frame((32 + 7.5 * math.cos(a), 32 - 7.5 * math.sin(a)), math.degrees(a))
        WEAPONS.get(x.fam, WEAPONS['any'])(x, fr, 15.0)
    x.fill(c.circle(32, 32, 3.6), 0, 'sphere', M('gold'))


def f_domain(x):
    """A field held round the self, its four corners marked; the weapon planted at its heart."""
    c = x.c
    x.verb(c.ring(32, 32, 21, 3.0), -1)
    for (px, py) in ((32, 11), (53, 32), (32, 53), (11, 32)):
        x.verb(c.rrect(px - 3, py - 3, px + 3, py + 3, 0.8), 1)
    if x.fam == 'any':
        x.verb(c.circle(32, 32, 4.0), 1)
        x.light(c.ring(32, 32, 9, 1.6), 0)
    else:
        x.weapon('centre', 24)


def f_seal(x):
    """A seal pressed on the foe: the square print, its border and the ring it closes; the weapon below."""
    c = x.c
    x.weapon('sw', 16)
    sq = c.rrect(30, 16, 54, 40, 2.0)
    x.verb(sq, 0)
    x.dark(sq & ~c.rrect(33, 19, 51, 37, 1.5), -3)
    x.dark(c.ring(42, 28, 5.6, 2.2) | c.circle(42, 28, 1.6), -3)
    for (px, py) in ((25, 45), (29, 49)):
        x.light(c.seg(px, py, px + 6, py - 6, 1.6), 1)


def f_echo(x):
    """The stroke and, a moment behind it, its echo."""
    c = x.c
    fr, L = x.frame('diag')
    ghost = WEAPONS.get(x.fam, WEAPONS['any'])(x, Frame((fr.p0[0] - 7, fr.p0[1] + 7), 45.0), L)
    x.p.decal(ghost & x.inner, x.mk, -2)
    x.weapon('diag')
    for r in (5, 9):
        x.light(c.arc(41, 23, r, 1.8, 20, 100), 1)


FORMS = {'strike': f_strike, 'flurry': f_flurry, 'thrust': f_thrust, 'lunge': f_lunge, 'sweep': f_sweep, 'arc': f_arc,
         'volley': f_volley, 'rain': f_rain, 'pillar': f_pillar, 'wave': f_wave, 'burst': f_burst, 'seeker': f_seeker,
         'return': f_return, 'snare': f_snare, 'counter': f_counter, 'ward': f_ward, 'chorus': f_chorus, 'blink': f_blink,
         'plunge': f_plunge, 'release': f_release, 'swarm': f_swarm, 'domain': f_domain, 'seal': f_seal, 'echo': f_echo}


# ----------------------------------------------------------------------------- hand marks
# Marks of their own for arts off the grammar's line: today the secret arts and the models of the plan's keystone
# templates; later the keystones, the Dao arts and the Lost Arts.
def _lens(c, cx, cy, rx, ry):
    r0 = (rx * rx + ry * ry) / (2 * ry)
    return c.circle(cx, cy + r0 - ry, r0) & c.circle(cx, cy - r0 + ry, r0)


def h_eye(x):
    """The appraising eye and its loupe."""
    c = x.c
    x.verb(_lens(c, 28, 30, 17, 10), 1)
    x.fill(c.circle(28, 30, 6.2), 0, 'sphere', M('jade'))
    x.dark(c.circle(28, 30, 2.6), -3)
    x.spark(25, 27, 0)
    x.verb(c.ring(41, 40, 8.6, 2.8), 0, 'ray', x.steel)
    x.verb(c.seg(47, 46, 53, 52, 4.4), -1)


def h_breath(x):
    """A breath held under water: the spiral of it and the bubbles rising."""
    c = x.c
    pts = []
    for k in range(50):
        t = k / 49.0
        r, a = 4 + t * 16, -t * 3.2 * math.pi
        pts.append((28 + r * math.cos(a), 33 + r * math.sin(a) * 0.8))
    sp = c.empty()
    for a_, b_ in zip(pts, pts[1:]):
        sp |= c.seg(a_[0], a_[1], b_[0], b_[1], 4.0)
    x.verb(sp, 0)
    for (px, py, r) in ((47, 42, 2.0), (50, 32, 2.6), (52, 21, 3.2)):
        x.verb(c.ring(px, py, r, 1.4), 1)


def h_veil(x):
    """A closed eye under drifting mist."""
    c = x.c
    lid = c.circle(32, 20, 22) & ~c.circle(32, 13, 23) & c.box(0, 23, 64, 64)
    x.verb(lid, 0)
    for px in (18, 25, 32, 39, 46):
        x.verb(c.seg(px, 40, px + (px - 32) * 0.3, 48, 2.6), 1)
    for (x0, y0) in ((16, 18), (30, 14)):
        pts = [(x0 + i, y0 + 2.0 * math.sin(i / 16.0 * 2 * math.pi)) for i in range(0, 17)]
        x.light(c.polyline(pts, 2.0), -1)


def h_leaf(x):
    """A leaf drifting down."""
    c = x.c
    leaf = c.circle(18, 18, 28) & c.circle(44, 44, 28)
    x.verb(leaf, 0)
    x.dark(c.seg(16, 14, 44, 42, 2.0) & leaf, -2)
    for (px, py) in ((26, 26), (34, 34)):
        x.dark(c.seg(px, py, px - 6, py + 6, 1.6) & leaf, -2)
    for k, (px, py) in enumerate(((18, 46), (26, 52), (12, 38))):
        x.light(c.circle(px, py, 2.0 + 0.6 * (k == 0)), 1)


def h_swallow(x):
    """A swallow darting right."""
    c = x.c
    wings = c.polyline([(14, 22), (26, 30), (36, 28), (50, 18)], 4.4)
    body = c.ellipse(34, 32, 8.4, 4.8)
    tail = c.polyline([(28, 34), (20, 46)], 3.2) | c.polyline([(32, 36), (30, 48)], 3.2)
    x.verb(wings | body | tail, 0)
    for py in (38, 44):
        x.light(c.seg(42, py, 52, py, 2.0), -1)


def h_clouds(x):
    """Three clouds climbing like steps."""
    c = x.c
    for (px, py) in ((20, 46), (32, 32), (44, 18)):
        x.verb(c.circle(px - 5, py, 5.6) | c.circle(px + 5, py, 5.6) | c.circle(px, py - 4, 6.4), 0)


def h_skim(x):
    """Skips across the water."""
    c = x.c
    pts = [(10 + i, 46 + 2.0 * math.sin(i / 12.0 * 2 * math.pi)) for i in range(0, 45)]
    x.light(c.polyline(pts, 2.4), 0)
    for (px, r) in ((16, 5.2), (30, 6.4), (46, 7.6)):
        x.verb(c.arc(px, 44, r, 2.8, 20, 160), 1)
    x.light(c.polyline([(16, 38), (22, 28), (30, 38), (38, 24), (46, 36)], 2.0), -1)


def h_wall(x):
    """Footsteps up a wall."""
    c = x.c
    wall = c.box(36, 8, 46, 56)
    x.verb(wall, 0, 'flat', x.steel)
    for py in range(12, 56, 8):
        x.dark(c.seg(36, py, 46, py, 1.0) & wall, -2)
        x.dark(c.seg(40 + (py // 8) % 2 * 4, py, 40 + (py // 8) % 2 * 4, py + 6, 1.0) & wall, -2)
    for (px, py) in ((24, 44), (28, 30), (24, 16)):
        x.verb(c.ellipse(px, py, 4.8, 6.4) | c.circle(px + 1, py - 8.4, 2.6), 0)


def h_double(x):
    """The self and its phantom."""
    c = x.c
    x.fill(_figure(c, 39, 33), -2, 'flat')
    x.verb(_figure(c, 25, 33), 0)


def h_wisp(x):
    """A soul's wisp and the probe put into it (Soul Search)."""
    c = x.c
    wisp = c.poly([(32, 11), (43, 26), (44, 40), (32, 52), (20, 40), (21, 26)])
    x.verb(wisp, 0)
    x.fill(c.circle(32, 37, 6.6) & wisp, 2, 'sphere')
    x.verb(c.seg(53, 55, 37, 40, 3.2), 0, 'ray', M('gold'))


def h_whirlpool(x):
    """Nine blades circling in a whirlpool (the Water keystone Nine Undertows, docs/technique_plan.md §3.7)."""
    c = x.c
    spiral = c.empty()
    for k in range(3):
        spiral |= c.arc(32, 32, 7 + k * 6, 2.6, k * 40, k * 40 + 250)
    x.verb(spiral, 0)
    for k in range(9):
        a = math.radians(k * 40 + 10)
        px, py = 32 + 21 * math.cos(a), 32 + 21 * math.sin(a)
        x.fill(c.seg(px, py, px + 5 * math.cos(a + 1.9), py + 5 * math.sin(a + 1.9), 1.8), 2, 'flat')
    x.fill(c.circle(32, 32, 3.2), 2, 'sphere')


def h_avatar(x):
    """The body turned to gold, seated under its halo."""
    c = x.c
    gold = M('gold')
    x.light(c.ring(32, 22, 13, 2.4), 2)
    x.verb(c.circle(32, 21, 6) | c.poly([(23, 29), (41, 29), (44, 42), (20, 42)]) | c.ellipse(32, 45, 18, 6), 0, 'ray', gold)


def h_burning_blood(x):
    """A drop of blood burning upward."""
    c = x.c
    blood = mat7(Ramp(['#3A0508', '#6E0C12', '#A8161E', '#D83A3A', '#FF8A7A'], '#1A0204'), 'matte')
    drop = c.poly([(32, 12), (42, 30), (44, 38), (38, 48), (26, 48), (20, 38), (22, 30)]) | c.circle(32, 39, 11.2)
    x.verb(drop, 0, 'sphere', blood)
    for (x0, y0, x1, y1) in ((24, 22, 20, 10), (40, 22, 44, 10), (32, 18, 32, 6)):
        x.verb(c.seg(x0, y0, x1, y1, 2.4), 1, 'ray', M('ember'))
    x.p.decal(c.circle(28, 33, 1.4), '#FFE0D8')


HAND = {'eye': h_eye, 'breath': h_breath, 'veil': h_veil, 'leaf': h_leaf, 'swallow': h_swallow, 'clouds': h_clouds,
        'skim': h_skim, 'wall': h_wall, 'double': h_double, 'wisp': h_wisp, 'whirlpool': h_whirlpool, 'avatar': h_avatar, 'burning_blood': h_burning_blood}


# ----------------------------------------------------------------------------- stamps (5 paths)
# A badge over the rim at the lower right: a bone on bronze (Body), a blood drop, a gold lotus, a needle on green
# (Poison), a square script seal (Confucian).
SX, SY = 49.0, 49.0


def st_body(p, mat):
    c = p.c
    p.part(c.circle(SX, SY, 7.6), mat, 'sphere', base=0, sep=True, rim=False)
    bone = c.box(SX - 3.6, SY - 1.1, SX + 3.6, SY + 1.1)
    for sx in (-1, 1):
        for sy in (-1, 1):
            bone |= c.circle(SX + 3.9 * sx, SY + 1.6 * sy, 1.75)
    p.decal(bone, M('bone'), 1)


def st_blood(p, mat):
    c = p.c
    drop = c.circle(SX, SY + 2.0, 6.0) | c.poly([(SX - 5.6, SY), (SX, SY - 9.5), (SX + 5.6, SY)])
    p.part(drop, mat, 'sphere', base=0, sep=True, rim=False)
    p.decal(c.circle(SX - 2.2, SY + 0.6, 1.2), mat, 3)


def st_buddhist(p, mat):
    c = p.c
    lotus = c.empty()
    for (dx, dy, rx, ry) in ((-5.0, 1.5, 2.6, 4.6), (5.0, 1.5, 2.6, 4.6), (-2.4, -0.5, 2.8, 5.8), (2.4, -0.5, 2.8, 5.8), (0, -2.0, 3.0, 7.0)):
        lotus |= c.ellipse(SX + dx, SY + dy, rx, ry)
    lotus |= c.ellipse(SX, SY + 6.0, 7.6, 2.4)
    p.part(lotus, mat, 'ray', base=0, sep=True, rim=False)
    p.decal(c.seg(SX, SY - 7, SX, SY + 3, 1.0), mat, -2)


def st_poison(p, mat):
    c = p.c
    p.part(c.circle(SX, SY, 7.6), mat, 'sphere', base=0, sep=True, rim=False)
    p.decal(c.seg(SX - 4.5, SY + 4.5, SX + 4.0, SY - 4.0, 2.0), mat, 3)
    p.decal(c.circle(SX + 4.4, SY - 4.4, 1.3), '#FFFFFF')


def st_confucian(p, mat):
    c = p.c
    p.part(c.rrect(SX - 7.5, SY - 7.5, SX + 7.5, SY + 7.5, 1.5), mat, 'flat', base=0, sep=True, rim=False)
    for (x0, y0, x1, y1) in ((SX - 4.5, SY - 3.5, SX + 4.5, SY - 3.5), (SX, SY - 3.5, SX, SY + 4.5), (SX - 4.5, SY + 4.5, SX + 4.5, SY + 4.5)):
        p.decal(c.seg(x0, y0, x1, y1, 1.2), mat, 3)


STAMPS = {'body': st_body, 'blood': st_blood, 'buddhist': st_buddhist, 'poison': st_poison, 'confucian': st_confucian}


# ----------------------------------------------------------------------------- the composer
def emblem(element, form=None, family='any', grade='common', kind=None, path=None, mark=None):
    """The emblem of an art: `element` a DISCS key (or a data key in ELEMENT_OF), `form` a FORMS key (or `mark` a
    HAND key instead), `family` a WEAPONS key, `grade` a RIMS key, `kind` a KINDS key when the art is one, `path`
    a PATHS key when the art is a path's. Returns the HD drawing draw(p)."""
    element = ELEMENT_OF.get(element, element)
    if (mark is None) == (form is None):
        raise ValueError('an emblem takes a form or a hand mark')
    if mark is None and form not in FORMS:
        raise ValueError('unknown form %s' % form)

    def draw(p):
        inner, spec, disc = disc_hd(p, element, grade, kind)
        disc_c, mark_c, steel_c = DISCS[element]
        tint = PATHS[path]['mark'] if path else None
        mk = mat7(Ramp(tint or mark_c, disc_c[0]), 'light')
        steel = mat7(Ramp(steel_c, disc_c[0]), 'metal')
        x = Ctx(p, inner, mk, steel, family)
        (HAND[mark] if mark else FORMS[form])(x)
        if path:
            STAMPS[path](p, mat7(Ramp(PATHS[path]['stamp'], '#05080B'), 'matte'))
        if spec.get('torn'):
            tear_rim(p)
    return draw


# ----------------------------------------------------------------------------- today's arts
# technique id -> its form (docs/technique_plan.md §3.2), or ('hand', mark) for the arts the plan gives a mark of
# their own: the Dao arts Phantom Double (the Mirror template's model) and Soul Search, Golden Body (the Avatar's
# model) and Blood Burning (a secret art). The element, family, grade, kind and path come from data/techniques.json.
FORM_OF = {
    'flowing_palm': 'flurry', 'jade_thrust': 'thrust', 'cloudpiercing_stroke': 'strike', 'reedcutter_slash': 'strike',
    'riverstone_sweep': 'sweep', 'twin_reed_shot': 'volley', 'tiger_rush': 'lunge', 'willow_leaf_parry': 'counter',
    'dragon_tail_sweep': 'sweep', 'shadow_flick': 'volley', 'bell_toll_strike': 'strike', 'pinning_arrow': 'snare',
    'mountain_cleaver': 'strike', 'gale_fan': 'wave', 'reed_song': 'seeker', 'thunder_dao_arc': 'arc',
    'returning_crane_fan': 'return', 'clear_heart_melody': 'chorus', 'rising_tide': 'burst', 'palm_wave': 'arc',
    'crescent_arc': 'arc', 'spear_lance': 'wave', 'sword_release': 'release', 'sword_swarm': 'swarm',
    'flying_blades': 'seeker', 'earthshaker_wave': 'wave', 'vine_snare': 'snare', 'rain_of_reeds': 'rain',
    'stone_skin': 'ward', 'gale_step': 'lunge', 'mountain_shaker': 'burst', 'ember_burst': 'burst',
    'still_water_focus': 'ward', 'shadowstep_cut': 'blink', 'cloud_descent': 'plunge', 'mirror_mind_spike': 'pillar',
    'soul_lantern_ward': 'ward', 'sense_lock': 'seal', 'phantom_double': ('hand', 'double'), 'soul_search': ('hand', 'wisp'),
    'crimson_palm': 'strike', 'blood_river_slash': 'arc', 'sanguine_lotus': 'burst', 'golden_body': ('hand', 'avatar'),
    'venom_needles': 'seeker', 'miasma_palm': 'burst', 'splashed_ink': 'volley', 'cursive_storm': 'rain',
    'stilling_peal': 'seal', 'qi_seal_toll': 'seal', 'wardens_call': 'chorus', 'upright_glyph': 'wave',
    'benevolent_script': 'chorus', 'rite_seal_script': 'seal', 'blood_burning': ('hand', 'burning_blood'),
    'glimpse_of_heaven': 'pillar',
}
# The secret arts (data/secret_arts.json, by icon id): an element for the disc and a form or a hand mark.
SECRET_ARTS = [
    ('dodge_dash', 'wind', 'blink'), ('appraisal_eye', 'metal', ('hand', 'eye')), ('breath_control', 'water', ('hand', 'breath')),
    ('wall_step', 'earth', ('hand', 'wall')), ('plunge', 'earth', 'plunge'), ('falling_leaf_glide', 'wood', ('hand', 'leaf')),
    ('swallow_dart', 'wind', ('hand', 'swallow')), ('cloud_ladder_step', 'wind', ('hand', 'clouds')),
    ('water_skimming', 'water', ('hand', 'skim')), ('concealment', 'soul', ('hand', 'veil')),
]


def rows():
    """(id, element, form or ('hand', mark), family, grade, kind, path) for every technique and secret art icon."""
    sys.path.insert(0, os.path.join(PROJECT, 'tools', 'data'))
    import technique_gen   # P13a: the rows are compact; their form's and ring's defaults fill them in
    entries = technique_gen.load_rows()
    out = []
    for e in entries:
        tid = str(e['id'])
        if e.get('icon') != tid:
            continue   # P13a: every other art's emblem is composed in the game from the atlas (emblem_atlas.py)
        if tid not in FORM_OF:
            raise ValueError('techniques.py: no form for technique %s (add it to FORM_OF)' % tid)
        kind = 'secret' if e.get('secret') else ('dao' if '_dao_' in str(e.get('source', '')) else None)
        path = next((p for flag, p in PATH_FLAGS if e.get(flag)), None)
        out.append((tid, str(e['element']), FORM_OF[tid], str(e.get('family', 'any')), str(e.get('grade', 'common')), kind, path))
    for (icon, element, form) in SECRET_ARTS:
        out.append((icon, element, form, 'any', 'common', 'secret', None))
    return out


TECHS_HD = rows()
for _id, _el, _form, _fam, _grade, _kind, _path in TECHS_HD:
    if isinstance(_form, tuple):
        _draw = emblem(_el, None, _fam, _grade, _kind, _path, mark=_form[1])
    else:
        _draw = emblem(_el, _form, _fam, _grade, _kind, _path)
    register(FAM, _id, _draw, GROUP)
    hd(_id, _draw)
