"""Beast parts (HD, Style A): every hide, scale, horn, fang, claw, feather, shell, vial, pouch, shard and core a beast
leaves, at 64 art px shown 1:1 in the 76 px slot, with a native @32 render for the HUD item ring and the small slots.

Each part is drawn as the material it is, in the colour of the beast it came from (its creature sheet): fur in strands
lying down the pelt, scales overlapping with their growth ridges, keratin and horn with a sheen band, bone grained
along its length, glass and jade through-lit with the light pooling on the far side. The kinds share one drawing each
(`hide_hd`, `scale_hd`, `fang_hd`, `feather_hd`, `vial_hd`, `pouch_hd`, `heap_hd`, `shard_hd`, `core_hd`) and the
species is its parameters; the one-offs (a claw, a shell, a tail, a badge, the pet gear) are drawn by hand on the same
helpers. Every icon comes from one table (PARTS_HD).

The grade (BEAST_GRADE in tools/data/items.py) is shown by form and trim, never by colour alone (GRADE_HD): a plain
part is raw; a common one is tied or pegged with hemp and wood; from Earth the binding is silk in the grade's colour
with a cap, peg or bead in its metal (bronze, silver, gold, comet iron); from Mystic the part carries its aura as
stepped glow bands, in the beast's own light, at the grade's strength (GLOW_STRENGTH).
"""
import math

import numpy as np

from pix import Ramp, WHITE, dilate4, erode4, move, shift
from palette import M, R, STAR_GLOW, TEX, kit, mat7
from registry import hd, register
import shapes as S

FAM, GROUP = 'items', 'beast_parts'
ART = 64   # HD (tools/icons/README.md, "How to convert a family")


# ============================================================================= materials
FUR, GREYFUR, LEATHER, HEMP, STRAW, WOOD, DARKWOOD, PAPER = M('fur'), M('greyfur'), M('leather'), M('hemp'), M('straw'), M('wood'), M('darkwood'), M('paper')
BONE = M('bone', 'porcelain')                  # ivory, horn and claw: keratin takes the rim light and a sheen band
FLESH, TOAD, VENOM, PLUM, PINK, MIST, WAX, GOLD, SILVER, JADE, VIOLET, CYAN = (M('flesh'), M('toad'), M('venom'), M('plum'), M('pink'), M('mist'), M('wax'), M('gold'),
                                                                               M('silver'), M('jade'), M('violet'), M('cyan'))
STONE, MOSS, EARTH, SAND, BAMBOO, NAVY, STORM, SKY, CLOUD, INKM, LOTUS, YELLOW = (M('warmstone'), M('moss'), M('earth'), M('sand'), M('bamboo'), M('navy', 'silk'),
                                                                                  M('storm'), M('sky'), M('cloud'), M('ink'), M('lotuspink', 'porcelain'), M('yellow'))
GLASS = M('mist', 'glass')                     # a vial's glass
OIL, HOLLOW, HOLLOW_GLASS, HOLLOW_METAL = M('oil', 'glass'), M('hollow'), M('hollow', 'glass'), M('hollow', 'metal')
CRAB = mat7(Ramp(['#3A1E14', '#64341F', '#96522E', '#C27E4E', '#E6B285'], '#180B06'), 'porcelain')      # the Mudshell Crab's mud-brown shell
BEETLE = mat7(Ramp(['#101B26', '#1B3440', '#2A5A5E', '#4E9A8A', '#B8F0D2'], '#050A0E'), 'metal')
TIDE = mat7(Ramp(['#2B4A58', '#4C7E8C', '#8CC3C6', '#D2EEE6', '#FFFFFF'], '#0F1E24'), 'porcelain')
CRADLE = mat7(Ramp(['#3E4A5C', '#6A7A92', '#A9B5C8', '#D8E0EC', '#FFFFFF'], '#141A24'), 'porcelain')
LIZARD = mat7(Ramp(['#2A2A14', '#4A4A22', '#7A7436', '#AEA35A', '#DCD39A'], '#12120A'), 'leather')
SERPENT = mat7(Ramp(['#0E2418', '#1A4029', '#2E6A42', '#5BA06A', '#A8D6A0'], '#06120A'), 'jade')
MISTFUR = mat7(Ramp(['#3A5664', '#61838F', '#9CBBC4', '#D2E6EA', '#F8FFFF'], '#15242B'), 'leather')
APE = mat7(Ramp(['#2A1A12', '#4A2E1E', '#6E4A30', '#9A7048', '#C69E70'], '#120A06'), 'leather')
SNAPPER = mat7(Ramp(['#122A2A', '#1E4644', '#326E62', '#5EA08A', '#A8D8C0'], '#081414'), 'porcelain')
LEECH = mat7(Ramp(['#2A0E14', '#4E1622', '#7A2432', '#A84A4A', '#D48A7A'], '#12050A'), 'glass')
# Act II · Rimefrost and Mirrorwater
ICE = mat7(Ramp(['#2C4C6E', '#4A78A2', '#7FB0D6', '#B8DCF2', '#E8F7FF'], '#10202E'), 'glass')
SNOWFUR = mat7(Ramp(['#6E7F96', '#9AAABE', '#C6D2DE', '#E6EDF3', '#FFFFFF'], '#222C38'), 'leather')
AZURE = mat7(Ramp(['#123A5E', '#1E6190', '#3A93C4', '#7CC8E8', '#D2F2FF'], '#061828'), 'jade')
MIRROR = mat7(Ramp(['#6C6A8E', '#A5A6C4', '#D6D8EA', '#F1F2FA', '#FFFFFF'], '#1E1C30'), 'glass')
IRIS = mat7(Ramp(['#2B1B52', '#46307E', '#7556AB', '#A687E0', '#D6C4FF'], '#10081E'), 'gem')
# Act II · Sunscar Desert
SANDGOLD = mat7(Ramp(['#4A3216', '#84602A', '#C39A4E', '#E6C77E', '#FFF1C2'], '#1F1407'), 'porcelain')
VENOM_AMBER = mat7(Ramp(['#6A300A', '#B25E12', '#EE9A26', '#FFC957', '#FFF3B0'], '#2A1204'), 'gem')
DESERT_GLASS = mat7(Ramp(['#35606E', '#5E98A8', '#9ED4DC', '#D8F4F2', '#FFFFFF'], '#10262E'), 'glass')
# Act II · Starsea, S46
BADGE = M('navy', 'jade')
BLOOD = mat7(Ramp(['#2A0A0E', '#561420', '#8A2230', '#C0463E', '#F0A070'], '#12050A'), 'glass')
# Act III · Lantern Star Field
JELLY = mat7(Ramp(['#262062', '#4646A4', '#7880DE', '#B2BCF8', '#EEF2FF'], '#0E0B2A'), 'light')
RUSSET = mat7(Ramp(['#3E1810', '#72301A', '#A8502A', '#D27A40', '#F2B070'], '#1A0906'))
STAR_DUST = mat7(Ramp(['#16204A', '#243A7A', '#3C62B4', '#78A2E4', '#D4E6FF'], '#080C22'), 'gem')
DARK_BRONZE = mat7(Ramp(['#1E140C', '#3A2616', '#5E3E22', '#8A6034', '#B88A50'], '#0C0804'), 'metal')
WYRM_ASH = mat7(Ramp(['#2A2634', '#46404E', '#6A6272', '#968EA0', '#C4BECC'], '#110F16'))
LANTERN, STARLIGHT = M('lanternbronze'), M('starlight')
# v1.2 · the Citadel, the Orbit Ruins, the Tidebreak Front, the Nebula Deep
GRAVITY = mat7(Ramp(['#100D1C', '#1E1A2C', '#332E44', '#504A64', '#766E90'], '#050410'), 'glass')
MOTH_SILVER = mat7(Ramp(['#4A5460', '#7C8896', '#B4C0CA', '#E0E8EC', '#FFFFFF'], '#1A2028'), 'metal')
HOLLOW_SHEEN = '#B8B0D2'
EEL_LIGHT = mat7(Ramp(['#2A2E8E', '#4C52D2', '#7E88F4', '#B6BEFE', '#F0F2FF'], '#0E1044'), 'light')
VOID = mat7(Ramp(['#05060F', '#0C0E24', '#171B3E', '#262E5E', '#404C88'], '#020208'), 'glass')
LEVIATHAN = mat7(Ramp(['#12103A', '#221E64', '#3A3694', '#5E5CC4', '#9A9AEA'], '#07061A'), 'jade')
STAR = '#FFFBEA'

# The grade's trim (form and trim, never colour alone): a plain part is raw; a common one is bound with hemp and
# pegged with wood; from Earth the cord is silk in the grade's colour (the kits' tassels; Spirit in its navy grip)
# and the cap, peg or bead is the grade's metal (the kits' guard); from Mystic the aura, at GLOW_STRENGTH.
GRADE_HD = {
    'plain': dict(level=0, cord=None, metal=None, glow=None),
    'common': dict(level=1, cord=HEMP, metal=None, glow=None),
    'earth': dict(level=2, cord=kit('earth')['tassel'], metal=kit('earth')['guard'], glow=None),
    'heaven': dict(level=3, cord=kit('heaven')['tassel'], metal=kit('heaven')['guard'], glow=None),
    'mystic': dict(level=4, cord=kit('mystic')['tassel'], metal=kit('mystic')['guard'], glow=kit('mystic')['glow']),
    'spirit': dict(level=5, cord=kit('spirit')['grip'], metal=kit('spirit')['guard'], glow=kit('spirit')['glow']),
    'sage': dict(level=6, cord=kit('sage')['tassel'], metal=kit('sage')['blade'], glow=kit('sage')['glow']),
    'sovereign': dict(level=7, cord=kit('sovereign')['tassel'], metal=kit('sovereign')['blade'], glow=kit('sovereign')['glow']),
    'will': dict(level=8, cord=kit('will')['tassel'], metal=kit('will')['guard'], glow=kit('will')['glow']),
}


# ============================================================================= helpers
def XY(p):
    """Pixel centres in icon space."""
    return p.c.X / p.s, p.c.Y / p.s


def far(p):
    """x + y per pixel in icon space: small at the lit corner, large at the shadow corner."""
    return (p.c.X + p.c.Y) / p.s


def lmask(p, pts, w=1.0):
    """The mask of a stroke through icon-space points, as `PixelPainter.line` draws it (1-px Bresenham at 1:1)."""
    c = p.c
    if w <= 1.0 and p.s == 1.0:
        return c.bres_path([(int(math.floor(x)), int(math.floor(y))) for x, y in pts])
    return c.polyline(pts, w)


def ibox(p, mask):
    """The mask's bounding box in icon space (x0, y0, x1, y1), or None when empty."""
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return xs.min() / p.s, ys.min() / p.s, (xs.max() + 1) / p.s, (ys.max() + 1) / p.s


def tangents(pts):
    """Per point: the unit tangent (ux, uy) and the unit normal (nx, ny) to its screen-right."""
    out = []
    n = len(pts)
    for i in range(n):
        a, b = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        out.append((dx / L, dy / L, -dy / L, dx / L))
    return out


def offset_pts(pts, d):
    """A polyline moved `d` icon px along its normals (to the screen-right of its direction)."""
    return [(x + nx * d, y + ny * d) for (x, y), (ux, uy, nx, ny) in zip(pts, tangents(pts))]


def lit_side(pts):
    """+1 or -1: the sign of the normal offset that points toward the light (up-left) along a curve."""
    ux, uy, nx, ny = tangents(pts)[len(pts) // 2]
    return -1 if (nx + ny) > 0 else 1


def fur_hd(p, mask, mat, ang=-70, pitch=4.0, L=5.5, lv=(-1, 1)):
    """Fur strands lying along `ang` (0 right, 90 up): short dark strokes in staggered rows, a lit stroke beside
    each, on the inside of `mask`."""
    c = p.c
    bb = ibox(p, mask)
    if bb is None:
        return
    x0, y0, x1, y1 = bb
    a = math.radians(ang)
    dx, dy = math.cos(a), -math.sin(a)
    px, py = -dy, dx
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    rad = math.hypot(x1 - x0, y1 - y0) / 2.0
    dark, light = c.empty(), c.empty()
    row, v = 0, -rad
    while v <= rad:
        u = -rad + (row % 2) * L * 0.85
        while u <= rad:
            sx, sy = cx + dx * u + px * v, cy + dy * u + py * v
            dark |= c.seg(sx, sy, sx + dx * L, sy + dy * L, 1.0)
            light |= c.seg(sx + px + dx * 1.5, sy + py + dy * 1.5, sx + px + dx * (L - 1.0), sy + py + dy * (L - 1.0), 1.0)
            u += L * 1.7
        v += pitch
        row += 1
    inner = erode4(mask)
    p.decal(dark & inner, mat, lv[0])
    p.decal(light & inner & ~dark, mat, lv[1])


def grain_hd(p, mask, mat, pts, hw, n=3, lv=-1):
    """Bone grain: `n` fine lines along a curve (icon-space points) spread across its half-width."""
    inner = erode4(mask)
    for k in range(n):
        d = (k - (n - 1) / 2.0) / max(1, n - 1) * hw * 1.1
        p.decal(lmask(p, offset_pts(pts, d)) & inner, mat, lv)


def cord_hd(p, pts, mat, w=2.4, lv=0):
    """A cord or thread through icon-space points, shaded across."""
    m = p.c.polyline(pts, w)
    p.part(m, mat, 'ray_soft', base=lv, sep=True, rim=False)
    return m


def knot_hd(p, x, y, r, mat, lv=0):
    return p.part(p.c.circle(x, y, r), mat, 'sphere', base=lv, sep=True, rim=False)


def cap_hd(p, x, y, r, mat, ry=None):
    """A metal cap, bead or peg."""
    return p.part(p.c.ellipse(x, y, r, ry or r), mat, 'sphere', base=0, sep=True, tex='metal')


def loop_hd(p, g, x, y, r=3.4, w=1.8, under=None):
    """The grade's cord loop hung from (x, y) (nothing on a plain part), and its metal bead on the loop."""
    if g['cord'] is None:
        return
    c = p.c
    m = c.ring(x, y, r, w)
    if under is not None:
        m &= ~under
    p.part(m, g['cord'], 'ray_soft', base=0, sep=True, rim=False)
    if g['metal'] is not None:
        cap_hd(p, x, y - r + 0.4, 1.7, g['metal'])


def wrap_hd(p, g, pts, w=4.2):
    """The grade's binding wrapped round a quill, a root or a haft along `pts`, with cross threads and its bead."""
    if g['cord'] is None:
        return
    c = p.c
    m = c.polyline(pts, w)
    p.part(m, g['cord'], 'ray_soft', base=0, sep=True, rim=False)
    tg = tangents(pts)
    for i in range(1, len(pts) - 1, 2):
        (x, y), (ux, uy, nx, ny) = pts[i], tg[i]
        p.decal(lmask(p, [(x + nx * w * 0.45, y + ny * w * 0.45), (x - nx * w * 0.45 + ux, y - ny * w * 0.45 + uy)]) & m, g['cord'], -2)
    if g['metal'] is not None:
        cap_hd(p, pts[-1][0], pts[-1][1], w * 0.55, g['metal'])


def glow_hd(p, g, col=None):
    """The aura from Mystic up: stepped bands in the beast's own light (or the grade's), at the grade's strength."""
    if g['glow'] is not None:
        p.glow(col or g['glow'][0], g['glow'][1])


# ============================================================================= the kinds
def hide_hd(p, g, fur, ang=-72, bristle=None, thorns=None, marks=(), stripe=None, scar=None, wisps=False, glints=(), sparks=()):
    """A pelt pegged out flat, seen from above: the body, four leg flaps, the neck and the tail, the fur in strands
    lying down it. bristle: a ridge of stiff hair down the spine; thorns: bone thorns studding it; marks: pale
    patches (x, y, r); stripe: (points, material) a dark stripe; scar: the points of a healed cut; wisps: mist
    drifting off it; glints: ice (x, y); sparks: static (x, y). Trim: pegs at the flap tips (wood from Common, the
    grade's metal from Earth), the neck tied with the grade's cord from Earth."""
    c = p.c
    body = c.ellipse(32, 34, 18.5, 20)
    legs = (c.poly([(21, 19), (7, 10), (11, 24), (20, 27)]) | c.poly([(43, 19), (57, 10), (53, 24), (44, 27)]) |
            c.poly([(18, 43), (7, 55), (15, 57), (24, 50)]) | c.poly([(46, 43), (57, 55), (49, 57), (40, 50)]))
    neck = c.poly([(25, 17), (27, 6), (37, 6), (39, 17)])
    tail = c.poly([(29.5, 51), (31.5, 59), (33.5, 51)])
    m = body | legs | neck | tail
    p.part(m, fur, 'ray_soft', base=0, sep=False)
    p.decal(m & ~erode4(m), fur, -1)      # the cut edge, the skin side a shade darker
    fur_hd(p, m, fur, ang)
    if bristle is not None:
        spine = c.box(30.5, 9, 33.5, 50) & m
        p.part(spine, bristle, 'flat', base=0, sep=False, rim=False)
        for y in range(11, 49, 4):
            p.decal(c.box(29, y, 35, y + 1.2) & m, bristle, -1)
            p.decal(c.box(30.5, y + 1.2, 33.5, y + 2.2) & m, bristle, 1)
    for (x, y, r) in marks:
        p.decal(c.ellipse(x, y, r, r * 0.65) & erode4(m), fur, 2)
    if stripe is not None:
        pts, mat = stripe
        p.decal(c.polyline(pts, 3.6) & erode4(m), mat, 0)
        p.decal(c.polyline(pts, 1.4) & erode4(m), mat, -2)
    if scar is not None:
        p.decal(lmask(p, scar) & m, fur, -3)
        (x0, y0), (x1, y1) = scar[0], scar[-1]
        for t in (0.25, 0.5, 0.75):
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            p.decal(lmask(p, [(x - 1.5, y + 1.5), (x + 1.5, y - 1.5)]) & m, fur, 2)
    if thorns is not None:
        for (x, y) in ((16, 30), (14, 38), (48, 30), (50, 38), (24, 50), (40, 50), (32, 22), (24, 28), (40, 28), (32, 40)):
            p.part(c.poly([(x - 2.4, y + 2), (x + 0.8, y - 5.5), (x + 2.6, y + 2)]), thorns, 'ray', base=0, sep=True, tex='metal')
    if wisps:
        for (x0, y0) in ((4.5, 33), (46, 53)):
            w = c.polyline([(x0 + k, y0 + 1.8 * math.sin(k / 2.6)) for k in range(0, 14)], 1.8)
            p.part(w, MIST, 'flat', base=2, sep=True, rim=False)
    for (x, y) in glints:
        p.decal(c.box(x, y, x + 2, y + 1) & m, ICE, 3)
    if g['level'] >= 1:
        peg = g['metal'] or WOOD
        for (x, y) in ((8.5, 11.5), (55.5, 11.5), (8.5, 53.5), (55.5, 53.5)):
            p.part(c.circle(x, y, 2.3), peg, 'sphere', base=0, sep=True, tex='metal' if g['metal'] is not None else None)
    if g['level'] >= 2:
        cord_hd(p, [(24.5, 12.5), (32, 14), (39.5, 12.5)], g['cord'], 2.6)
        knot_hd(p, 39.5, 12.5, 1.8, g['cord'])
    for (x, y) in sparks:
        p.sparkle(x, y, 1)
    return m


def scale_hd(p, mat, cx, cy, w, h, ridges=2, point=False, tex='jade', base=0, sep=True):
    """A single scale: a shield (or a pointed diamond) with growth ridges following its foot, through-lit like jade
    or sheened like horn by `tex`."""
    c = p.c
    m = c.diamond(cx, cy, w / 2.0, h / 2.0) if point else shield_hd(c, cx, cy, w / 2.0, h / 2.0)
    p.part(m, mat, 'ray', base=base, sep=sep, tex=tex)
    for k in range(1, ridges + 1):
        f = 1.0 - k * 0.3
        inner = c.diamond(cx, cy + h * 0.1 * k, w / 2.0 * f, h / 2.0 * f) if point else shield_hd(c, cx, cy + h * 0.1 * k, w / 2.0 * f, h / 2.0 * f)
        ridge = inner & ~erode4(inner) & c.box(0, cy - h * 0.2 + h * 0.1 * k, 64, 64) & m
        p.decal(ridge, mat, -2)
        p.decal(shift(ridge, 0, 1) & m & ~ridge, mat, 1)
    return m


def fang_hd(p, g, p0, p1, p2, w0, mat=None, w1=0.9, root=None, trim=True, tex='metal', glints=(), grain=True, loop=None):
    """A fang, tusk, horn or claw: a tapering curve from the root p0 through p1 to the point p2, its half-width from
    w0 to w1; a keratin sheen band (`tex`), the grain along it, a lit line inside the lit edge and a dark line inside
    the shade edge. root: the material at the root. Trim: the grade's cord loop at the root (behind it along the
    curve, or at `loop`), a metal cap over it."""
    c = p.c
    mat = mat or BONE
    m = c.taper(p0, p1, p2, w0, w1)
    p.part(m, mat, 'ray', base=0, sep=True, tex=tex)
    pts = S.curve_pts(p0, p1, p2, 20)
    sd = lit_side(pts)
    n = len(pts)
    lit, shade = [], []
    for i, ((x, y), (ux, uy, nx, ny)) in enumerate(zip(pts, tangents(pts))):
        hw = (w0 + (w1 - w0) * i / float(n - 1)) / 2.0
        lit.append((x + nx * sd * hw * 0.42, y + ny * sd * hw * 0.42))
        shade.append((x - nx * sd * hw * 0.5, y - ny * sd * hw * 0.5))
    inner = erode4(m)
    p.decal(c.polyline(lit[:-3], 1.2) & inner, mat, 2)
    p.decal(c.polyline(shade[:-4], 1.0) & inner, mat, -2)
    if grain:
        p.decal(lmask(p, pts[2:-5]) & inner, mat, -1)
    if root is not None:
        p.part(c.circle(p0[0], p0[1], w0 * 0.55) & m, root, 'ray_soft', base=0, sep=False, rim=False)
    if trim:
        if g['metal'] is not None:
            cap_hd(p, p0[0], p0[1], w0 * 0.58, g['metal'])
        (ux, uy, nx, ny) = tangents(pts)[0]
        lx, ly = loop or (p0[0] - ux * w0 * 0.75, p0[1] - uy * w0 * 0.75)
        loop_hd(p, g, lx, ly, under=m)
    for (x, y) in glints:
        p.decal(c.box(x, y, x + 1, y + 2.5) & m, mat, 3)
    return m


def feather_hd(p, g, vane, shaft=None, shaft_lv=1, tip=None, tip_frac=0.0, base=None, width=19.0, notches=((0.55, 1), (0.35, -1)),
               p0=(9, 57), p1=(24, 22), p2=(56, 7), bars=None, eye=None, sparks=(), bolt=None):
    """A feather on the diagonal, quill at the lower left, tip at the upper right: the vane with its barbs swept
    back toward the quill and a notch or two where they part, the shaft with its shade side, the bare quill. tip
    and base recolour the ends (tip_frac of the length); bars: (n, material) a hawk's barring; eye: (x, y, rx, ry)
    an eye spot; bolt: points of a lightning mark. Trim: the quill wrapped in the grade's cord with its bead."""
    c = p.c
    X, Y = XY(p)
    shaft = shaft or BONE
    pts = S.curve_pts(p0, p1, p2, 40)
    n = len(pts)
    vm = c.empty()
    for i in range(4, n - 1):
        t = i / float(n - 1)
        hw = width / 2.0 * math.sin(math.pi * min(1.0, (t - 0.1) / 0.92) ** 0.85) if t > 0.1 else 0.0
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        vm |= c.seg(x0, y0, x1, y1, max(0.6, 2 * hw))
    tg = tangents(pts)
    for (t, side) in notches:
        i = int(t * (n - 1))
        (x, y), (ux, uy, nx, ny) = pts[i], tg[i]
        vm &= ~c.seg(x + nx * side * 3.0, y + ny * side * 3.0, x + nx * side * 11 - ux * 4, y + ny * side * 11 - uy * 4, 1.6)
    p.part(vm, vane, 'ray', base=0, sep=False, rim=False)

    def beyond(frac, sign):
        x, y = pts[int(frac * (n - 1))]
        return vm & ((((X - x) * (p2[0] - p0[0]) + (Y - y) * (p2[1] - p0[1])) * sign) > 0)
    regions = [(vm, vane)]
    if tip is not None:
        tm = beyond(1 - tip_frac, 1)
        p.part(tm, tip, 'ray', base=0, sep=False, rim=False)
        regions = [(vm & ~tm, vane), (tm, tip)]
    if base is not None:
        bm = beyond(0.3, -1)
        p.part(bm, base, 'ray', base=0, sep=False, rim=False)
        regions = [(mm & ~bm, mt) for mm, mt in regions] + [(bm, base)]
    inner = erode4(vm)
    if bars is not None:
        nb, bmat = bars
        for k in range(nb):
            (x, y), (ux, uy, nx, ny) = pts[int((0.34 + k * 0.13) * (n - 1))], tg[int((0.34 + k * 0.13) * (n - 1))]
            bar = c.seg(x + nx * width * 0.6 - ux * 2, y + ny * width * 0.6 - uy * 2, x - nx * width * 0.6 - ux * 2, y - ny * width * 0.6 - uy * 2, 2.6) & inner
            p.decal(bar, bmat, -1)
    barbs = c.empty()
    for k in range(6, n - 3, 2):
        (x, y), (ux, uy, nx, ny) = pts[k], tg[k]
        for sgn in (1, -1):
            barbs |= lmask(p, [(x, y), (x + nx * sgn * width * 0.55 - ux * width * 0.3, y + ny * sgn * width * 0.55 - uy * width * 0.3)])
    for mm, mt in regions:
        p.decal(barbs & inner & mm, mt, -1)
    if bolt is not None:
        b = c.polyline(bolt, 1.8) & vm
        p.decal(dilate4(b) & vm & ~b, NAVY, -2)
        p.decal(b, YELLOW, 1)
    sm = c.polyline(pts[:-3], 2.0)
    p.part(sm, shaft, 'flat', base=shaft_lv, sep=True, rim=False)
    p.decal(lmask(p, offset_pts(pts[:-3], 0.7)) & sm, shaft, shaft_lv - 2)
    p.part(c.polyline(pts[:6], 2.8), shaft, 'ray_soft', base=shaft_lv - 1, sep=True, rim=False)
    if eye is not None:
        ex, ey, rx, ry = eye
        e = c.ellipse(ex, ey, rx, ry) & vm
        p.part(e, NAVY, 'flat', base=-1, sep=True, rim=False)
        p.decal(c.ellipse(ex, ey, rx * 0.5, ry * 0.5) & e, GOLD, 0)
        p.decal(c.circle(ex - rx * 0.25, ey - ry * 0.3, 0.9) & e, GOLD, 3)
    wrap_hd(p, g, pts[3:8], 4.4)
    for (x, y) in sparks:
        p.sparkle(x, y, 1)
    return vm


def vial_hd(p, g, liquid, glass=None, cork=None, shape='round', level=0.6, flecks=(), fleck_mat=None, spot=None):
    """A stoppered glass vial: round on a neck, or a tall bottle. The liquid to `level` with its meniscus, flecks
    (x, y) in it and a `spot` (x, y, rx, ry, material) floating in it; a lit line down the glass; the lip; a cork
    (wood, or the material given). Trim: the neck tied with the grade's cord, its bead in the grade's metal."""
    c = p.c
    glass = glass or GLASS
    cork = cork or WOOD
    if shape == 'round':
        body = c.circle(32, 40.5, 16.5)
        neck = c.box(26.5, 14, 37.5, 30)
        top, bot, lip_y, hx = 24.0, 57.0, 12.5, 20.5
    else:
        body = c.rrect(21.5, 22, 42.5, 58, 4.5)
        neck = c.box(26.5, 12, 37.5, 24)
        top, bot, lip_y, hx = 22.0, 58.0, 10.5, 23.5
    p.part(body | neck, glass, 'ray_soft', base=1, sep=False, tex='glass')
    surf = top + (bot - top) * (1 - level)
    liq = erode4(body) & c.box(0, surf, 64, 64)
    p.part(liq, liquid, 'ray_soft', base=0, sep=False, rim=False, tex='glass')
    bb = ibox(p, liq & c.box(0, surf, 64, surf + 1.5))
    if bb is not None:
        p.decal(c.ellipse(32, surf + 0.9, (bb[2] - bb[0]) / 2.0 - 0.5, 1.6) & liq, liquid, 2)
    for (x, y) in flecks:
        p.decal(c.circle(x, y, 0.9) & liq, fleck_mat or GOLD, 2)
    if spot is not None:
        sx, sy, rx, ry, smat = spot
        p.decal(c.ellipse(sx, sy, rx, ry) & liq, smat, 0)
    p.line([(hx, top + 9), (hx, top + 21)], glass, 3, 1.4)
    p.decal(c.circle(hx + 2.5, top + 6, 1.0), WHITE, 0)
    lip = c.box(24, lip_y, 40, lip_y + 3.5)
    p.part(lip, glass, 'ray_soft', base=2, sep=True, tex='glass')
    ctex = 'wood' if cork.kind == 'wood' else ('metal' if cork.kind in ('gold', 'metal') else None)
    p.part(c.rrect(27.5, 5, 36.5, lip_y + 1.5, 1.4), cork, 'ray', base=0, sep=True, tex=ctex, axis=90)
    if g['cord'] is not None:
        ny = lip_y + 6
        cord_hd(p, [(25, ny), (32, ny + 1.2), (39, ny)], g['cord'], 2.6)
        knot_hd(p, 39.5, ny, 2.0, g['cord'])
        p.part(c.taper((40, ny + 1), (44, ny + 4), (43.5, ny + 10), 2.0, 1.2), g['cord'], 'flat', base=0, sep=True, rim=False)
        if g['metal'] is not None:
            cap_hd(p, 39.5, ny, 1.9, g['metal'])
    return body


def pouch_hd(p, g, bag, dust, glints=(), flecks=(), fleck_mat=None, fuse=False, sparks=()):
    """A cloth pouch tied at the neck, its mouth open on the dust inside, and a heap of it spilled in front. glints:
    lit grains (x, y) in the heap; flecks: grains of `fleck_mat`; fuse: a waxed cord out of the neck. Trim: the tie
    is the grade's cord (hemp on a plain pouch, which still needs tying), its bead in the grade's metal."""
    c = p.c
    body = c.ellipse(28, 42, 19.5, 16.5) | c.poly([(17, 32), (21, 22), (35, 22), (39, 32)])
    p.part(body, bag, 'sphere', base=0, sep=False, cx=22, cy=37, rx=25, ry=23, tex='cloth', axis=75)
    for pts in (((16, 38), (20, 46), (26, 53)), ((38, 32), (41, 38), (42, 45))):
        p.decal(lmask(p, pts) & erode4(body), bag, -2)
    frill = c.poly([(16, 22), (18, 12), (23, 16), (28, 9), (33, 16), (38, 12), (40, 22)])
    p.part(frill, bag, 'ray', base=1, sep=True, tex='cloth', axis=90, rim=False)
    p.part(c.ellipse(28, 17, 6.5, 3) & frill, dust, 'ray_soft', base=0, sep=True, rim=False)
    tie = g['cord'] or HEMP
    p.part(c.box(16, 22, 40, 25.5) & dilate4(body | frill), tie, 'ray_soft', base=0, sep=True, rim=False)
    knot_hd(p, 38, 24, 2.4, tie)
    p.part(c.taper((39, 25), (44, 27), (44, 33), 2.2, 1.2), tie, 'flat', base=0, sep=True, rim=False)
    if g['metal'] is not None:
        cap_hd(p, 38, 24, 2.0, g['metal'])
    if fuse:
        f = c.polyline(S.curve_pts((30, 12), (33, 4.5), (42, 6.5), 10), 2.2) & ~c.a
        p.part(f, HEMP, 'flat', base=0, sep=True, rim=False)
        p.sparkle(43, 5, 1)
    heap = (c.ellipse(47, 54, 12.5, 6.5) | c.ellipse(41, 56, 9, 3.6)) & c.box(0, 0, 64, 59)
    p.part(heap, dust, 'ray_soft', base=0, sep=True, rim=False)
    for (x, y) in glints:
        p.decal(c.box(x, y, x + 2, y + 1) & c.a, dust, 3)
    for (x, y) in flecks:
        p.decal(c.circle(x, y, 0.9) & c.a, fleck_mat or GOLD, 1)
    for (x, y) in sparks:
        p.sparkle(x, y, 1)
    return body


def heap_hd(p, mat, top=(32, 20), rx=27, base_y=56, dark=(), light=()):
    """A small heap of ash or dust: a cone with a slump down its shadow side, dark and lit grains (x, y)."""
    c = p.c
    tx, ty = top
    heap = c.poly([(32 - rx, base_y), (32 - rx * 0.72, base_y - 9), (32 - rx * 0.42, base_y - 21), (tx - 4, ty + 3), top, (tx + 4, ty + 3),
                   (32 + rx * 0.42, base_y - 20), (32 + rx * 0.72, base_y - 8), (32 + rx, base_y)]) | c.ellipse(32, base_y - 2, rx, 5)
    heap &= c.box(0, 0, 64, base_y + 1.5)
    p.part(heap, mat, 'sphere', base=0, sep=False, cx=27, cy=42, rx=32, ry=26, rim=False)
    p.decal(lmask(p, [(tx + 6, ty + 8), (tx + 10, ty + 20), (tx + 18, base_y - 8)]) & erode4(heap), mat, -2)
    for (x, y) in dark:
        p.decal(c.circle(x, y, 0.9) & erode4(heap), mat, -1)
    for (x, y) in light:
        p.decal(c.circle(x, y, 0.9) & erode4(heap), mat, 2)
    return heap


def shard_hd(p, pts, mat, facet=None, tex='glass', mark=None, mark_mat=None):
    """A crystal shard: a faceted polygon, through-lit, one facet lit a step brighter with its edges drawn, a
    bright lit edge, and a `mark` (points) of light inside it."""
    c = p.c
    m = c.poly(pts)
    p.part(m, mat, 'ray', base=0, sep=True, tex=tex)
    if facet:
        f = c.poly(facet) & m
        p.decal(f, mat, 1)
        p.decal(f & ~erode4(f), mat, -1)
    p.decal(m & ~erode4(m) & (far(p) < ibox(p, m)[0] + ibox(p, m)[1] + 18), mat, 2)
    if mark:
        p.decal(c.polyline(mark, 1.4) & erode4(m), mark_mat or WHITE, 3 if mark_mat else 0)
    return m


def core_hd(p, mat, x=32, y=31, r=17.5, rings=None, ring_mat=None):
    """A beast core: a sphere through-lit (the light pooling in a crescent on its far side), a glint, and, when
    `rings` gives (rx, ry, tilt) pairs, rings of light bent round it, the far arcs behind, the near arcs in front."""
    c = p.c
    X, Y = XY(p)
    core = c.circle(x, y, r)
    arcs = []
    for (rx, ry, ang, w) in (rings or ()):
        a = math.radians(ang)
        u = (X - x) * math.cos(a) - (Y - y) * math.sin(a)
        v = (X - x) * math.sin(a) + (Y - y) * math.cos(a)
        ring = ((u / rx) ** 2 + (v / ry) ** 2 <= 1.0) & ~((u / (rx - w)) ** 2 + (v / (ry - w)) ** 2 <= 1.0)
        arcs.append((ring, v))
    for k, (ring, v) in enumerate(arcs):
        p.part(ring & (v < 0) & ~core, ring_mat, 'flat', base=k - 1, sep=False, rim=False)
    p.part(core, mat, 'sphere', base=0, sep=True, cx=x, cy=y, rx=r, ry=r, tex='glass')
    if ring_mat is not None:
        p.decal(core & ~erode4(core) & (far(p) > x + y + 11), ring_mat, -1)
    p.decal(c.ellipse(x - r * 0.4, y - r * 0.45, r * 0.24, r * 0.15) & core, mat, 3)
    p.decal(c.box(x - r * 0.5, y - r * 0.5, x - r * 0.38, y - r * 0.44) & core, ring_mat or WHITE, 2 if ring_mat else 0)
    for k, (ring, v) in enumerate(arcs):
        near = ring & (v >= 0)
        p.part(near, ring_mat, 'flat', base=k, sep=True, rim=False)
        p.decal(near & (far(p) < x + y - 4), ring_mat, k + 1)
    return core


# ----------------------------------------------------------------------------- the study's scale
def shield_hd(c, sx, sy, hw, hh):
    """A scale's shield outline: a notched top and a pointed foot."""
    top = sy - hh
    return c.poly([(sx - hw, top + hh * 0.18), (sx - hw * 0.5, top), (sx, top + hh * 0.12), (sx + hw * 0.5, top),
                   (sx + hw, top + hh * 0.18), (sx + hw * 0.92, sy + hh * 0.35), (sx, sy + hh), (sx - hw * 0.92, sy + hh * 0.35)])


def jade_scale_hd(p):
    """A through-lit jade scale with two growth ridges, a lit edge and a glint."""
    c = p.c
    jade = M('jade')
    m = shield_hd(c, 32, 32, 24, 26)
    p.part(m, jade, 'ray', base=0, sep=False, tex='jade')
    for k in (1, 2):
        f = 1.0 - k * 0.3
        inner = shield_hd(c, 32, 32 + 52 * 0.1 * k, 24 * f, 26 * f)
        ridge = inner & ~erode4(inner) & c.box(0, 32 - 26 * 0.2 + 5.2 * k, 64, 64) & m
        p.decal(ridge, jade, -2)
        p.decal(shift(ridge, 0, 1) & m & ~ridge, jade, 1)
    p.line([(17, 19), (16, 27)], jade, 3, 1.4)
    p.line([(20, 16), (23, 15)], jade, 3, 1.2)
    p.decal(c.ellipse(40, 44, 5, 3) & erode4(erode4(m)), jade, 1)
    p.sparkle(19, 22, 1)
    p.glow('#67D6BD', 0.7)


# ============================================================================= the species
# --- scales
def three_scales_hd(p, g, mat, tex, glint=None, keel=False):
    """Three scales as they overlapped on the flank, the lower one in front; `keel`: a horn scale's raised ridge
    down the middle and its edge darkening toward the foot."""
    c = p.c
    for (x, y, w, h, ridges) in ((21, 24, 24, 27, 1), (43, 24, 24, 27, 1), (32, 40, 30, 33, 2)):
        m = scale_hd(p, mat, x, y, w, h, ridges, tex=tex)
        if keel:
            p.decal(m & ~erode4(m) & (far(p) > x + y - 2), mat, -2)
            p.decal(c.box(x - 0.9, y - h * 0.4, x + 0.9, y + h * 0.4) & erode4(m), mat, 2)
            p.decal(c.box(x + 0.9, y - h * 0.35, x + 1.9, y + h * 0.4) & erode4(m), mat, -1)
    if glint is not None:
        p.decal(p.c.box(glint[0], glint[1], glint[0] + 4, glint[1] + 1.2), glint[2], 3)


def serpent_scale_hd(p, g):
    """The Riverbed Serpent's heavy scale: a pointed diamond, its centre a violet keel."""
    c = p.c
    m = scale_hd(p, SERPENT, 32, 32, 38, 48, 2, point=True)
    p.decal(c.diamond(32, 32, 5, 9) & erode4(m), VIOLET, 0)
    p.decal(c.diamond(31, 30, 2, 4) & erode4(m), VIOLET, 2)
    p.line([(22, 24), (30, 10)], SERPENT, 3, 1.4)


def leviathan_scale_hd(p, g):
    """One broad leviathan scale, violet-blue with a silver edge, a slow swirl of stars turning in it."""
    c = p.c
    m = scale_hd(p, LEVIATHAN, 32, 32, 42, 46, 0)
    edge = m & ~erode4(m)
    p.decal(edge, SILVER, 0)
    p.decal(edge & (far(p) < 60), SILVER, 2)
    inner = erode4(erode4(m))
    for k in range(3):
        pts = []
        for i in range(16):
            t = i / 15.0
            a = k * 2.094 + t * 3.4
            r = 2.5 + t * 15.0
            pts.append((32 + r * math.cos(a), 33 + r * math.sin(a) * 0.9))
        arm = c.polyline(pts, 1.6) & inner
        p.decal(arm, LEVIATHAN, 1)
        p.decal(arm & (far(p) < 62), LEVIATHAN, 2)
    for (x, y) in ((32, 32), (26, 24), (42, 28), (22, 40), (38, 44), (32, 18), (46, 40), (18, 30)):
        p.decal(c.box(x, y, x + 1, y + 1) & inner, STAR, 0)
    p.decal(c.box(32, 32, 33, 33), WHITE, 0)
    p.sparkle(26, 24, 1)


def guardian_scale_hd(p, g):
    """A Nest Guardian's shell plate: curved dark bronze with its growth ridges, a starlight crystal set glowing in a
    lantern-bronze bezel at its heart."""
    c = p.c

    def scute(s):
        cx, cy = 32.0, 30.0
        return c.ellipse(cx, cy - 2 * s, 22 * s, 20 * s) | c.poly([(cx - 20.4 * s, cy + 4 * s), (cx + 20.4 * s, cy + 4 * s), (cx, cy + 28 * s)])
    plate = scute(1.0)
    k = max(1, int(round(2 * p.s)))
    p.part((move(plate, k, k) | move(plate, k + 1, k + 1)) & ~plate, DARK_BRONZE, 'flat', base=-2, sep=False, rim=False)
    p.part(plate, DARK_BRONZE, 'sphere', base=0, sep=True, cx=28, cy=24, rx=30, ry=32, tex='metal')
    for s in (0.74, 0.5):
        ring = S.outline_only(scute(s)) & erode4(plate)
        p.decal(ring, DARK_BRONZE, -2)
        p.decal(ring & (far(p) < 60), DARK_BRONZE, 2)
    p.line([(13, 22), (19, 14)], LANTERN, 2, 1.2)
    p.part(c.diamond(32, 31, 9.2, 11.6), LANTERN, 'ray', base=0, sep=True, tex='metal')
    gem = c.diamond(32, 31, 6, 8.4)
    p.part(gem, STARLIGHT, 'ray', base=0, sep=True, tex='glass')
    p.decal(gem & (far(p) < 62), STARLIGHT, 1)
    p.decal(c.box(30, 26, 31, 27), WHITE, 0)


# --- hides and fur
def ape_fur_hd(p, g):
    """A hank of Cliff Ape fur bound in a band: the strands fanning down from the tie, a tuft above it."""
    c = p.c
    ends = [(13, 51), (18, 56.5), (25, 53), (32, 57.5), (39, 53), (46, 56.5), (51, 49.5)]
    m = c.ellipse(32, 27, 12, 10.5)
    for (ex, ey) in ends:
        sx = 32 + (ex - 32) * 0.4
        m |= c.taper((sx, 25), (sx + (ex - sx) * 0.3 + 2, 39), (ex, ey), 7.0, 2.4)
    tuft = c.taper((32, 20), (27, 11), (20, 9.5), 7, 2.2) | c.taper((34, 20), (39, 11), (46, 10), 6, 2.2)
    p.part(m | tuft, APE, 'ray', base=0, sep=False)
    for (ex, ey) in ends[1:-1]:
        p.decal(lmask(p, S.curve_pts((32 + (ex - 32) * 0.3, 30), (32 + (ex - 32) * 0.55, 41), (ex, ey - 2.5), 8)) & erode4(m), APE, -2)
    for (ex, ey) in ends[:3]:
        p.decal(lmask(p, S.curve_pts((28 + (ex - 32) * 0.2, 27), (27 + (ex - 32) * 0.4, 37), (ex + 2, ey - 7), 8)) & erode4(m), APE, 2)
    fur_hd(p, m & c.box(0, 30, 64, 64), APE, -80, pitch=5, L=6)
    band = c.ellipse(32, 23, 11.5, 4)
    p.part(band, g['cord'] or M('red', 'silk'), 'ray_soft', base=0, sep=True, tex='cloth', axis=0, rim=False)
    p.line([(22, 22), (28, 20.5), (36, 20.5)], g['cord'] or M('red', 'silk'), 2, 1.0)
    if g['metal'] is not None:
        cap_hd(p, 32, 23, 2.4, g['metal'])


# --- horns and antlers
def hollow_antler_hd(p, g):
    """A Hollow Stag's antler, grey and cold: the beam from the burr with three tines, the bone grained along it."""
    c = p.c
    beam = fang_hd(p, g, (16, 56), (12, 27), (41, 9), 9.5, HOLLOW, 3.4, trim=False, tex=None)
    for (a, b, d, w) in (((16, 42), (27, 33), (30, 21), 6.6), ((25, 18), (42, 25), (53, 20), 6.2), ((16, 50), (30, 51), (39, 42), 6.2)):
        t = c.taper(a, b, d, w, 2.6)
        p.part(t, HOLLOW, 'ray', base=0, sep=True)
        pts = S.curve_pts(a, b, d, 10)
        p.decal(lmask(p, offset_pts(pts, -1.4)[1:-2]) & erode4(t), HOLLOW, 2)
        p.decal(lmask(p, pts[1:-3]) & erode4(t), HOLLOW, -1)
    burr = c.ellipse(17, 55.5, 6.2, 3.6)
    p.part(burr, HOLLOW, 'ray_soft', base=-1, sep=True)
    for (x, y) in ((13, 55), (16, 57), (20, 55)):
        p.decal(c.circle(x, y, 0.9) & burr, HOLLOW, -3)
    del beam
    if g['metal'] is not None:
        cap_hd(p, 17, 55.5, 4.0, g['metal'], 2.4)
    loop_hd(p, g, 11, 50, under=c.a)


def thunder_horn_hd(p, g):
    """A thunderhorn's horn, bone over a storm-blue root, the charge it still holds arcing up its side."""
    c = p.c
    m = fang_hd(p, g, (19, 53), (28, 25), (54, 9), 15, BONE, 1.0, root=STORM, loop=(10, 46))
    arc = c.polyline([(38, 15), (45, 22), (41, 27), (49, 34), (45, 38), (52, 46)], 1.8)
    p.part(arc & ~erode4(m), CYAN, 'flat', base=2, sep=True, rim=False)
    p.decal(arc & m, CYAN, 3)
    p.decal(c.polyline([(45, 22), (41, 27), (49, 34)], 0.8) & ~m, CYAN, 3)
    p.sparkle(53, 48, 1)


# --- fangs, claws and teeth
def viper_fang_hd(p, g):
    """A Green Viper's fangs, the long one still beaded with venom, their roots in pink gum."""
    c = p.c
    fang_hd(p, g, (14, 22), (30, 24), (28, 42), 6.5, trim=False, root=FLESH)
    fang_hd(p, g, (20, 14), (46, 18), (42, 50), 10.5, root=FLESH)
    d = S.drop(c, 40.5, 56, 3.2, 8)
    p.part(d, VENOM, 'sphere', base=0, sep=True, tex='glass')
    p.decal(c.circle(39.5, 55, 0.9), VENOM, 3)


def hollow_eel_fang_hd(p, g):
    """The Hollowed eel's fang from the Hollow Night: one long hooked fang gone grey to the root, the root still in a
    scrap of the eel's dark gum, a bead of the grey on its point."""
    c = p.c
    fang_hd(p, g, (17, 13), (47, 16), (41, 51), 12.0, HOLLOW, root=INKM, loop=(11, 9))
    d = S.drop(c, 40.5, 57.5, 3.0, 7)
    p.part(d, HOLLOW_GLASS, 'sphere', base=0, sep=True, tex='glass')
    p.decal(c.circle(39.8, 56.8, 0.9), HOLLOW_GLASS, 3)


def hound_fang_hd(p, g):
    """A Mud Hound's fang, the big one strung between two small ones on a cord, a leather knot at its root."""
    c = p.c
    cord = g['cord'] or LEATHER
    cord_hd(p, S.curve_pts((7, 10), (32, 30), (57, 10), 16), cord, 2.4)
    fang_hd(p, g, (18, 22), (21, 30), (18, 39), 6.2, trim=False)
    fang_hd(p, g, (46, 22), (47, 30), (44, 39), 6.2, trim=False)
    fang_hd(p, g, (32, 27), (36, 41), (28, 57), 12.5, trim=False)
    p.part(c.ellipse(32, 26, 6.5, 4), LEATHER, 'ray', base=0, sep=True)
    if g['metal'] is not None:
        for x in (18, 46):
            cap_hd(p, x, 21.5, 3.0, g['metal'], 2.0)


def rime_fang_hd(p, g):
    """A Frost Lynx's fang rimed with ice that never melts: the ice through-lit over a bone root, white glints on it."""
    fang_hd(p, g, (21, 50), (30, 24), (49, 10), 14, ICE, 1.0, root=BONE, tex='glass', glints=((42, 14), (34, 26), (27, 38)), loop=(11, 43))
    for (x, y) in ((53, 7), (14, 36)):
        p.sparkle(x, y, 1)


def worm_glass_tooth_hd(p, g):
    """A Dune Worm's tooth of clear desert glass, an amber thread at its core and sand still crusted on the root."""
    c = p.c
    m = fang_hd(p, g, (42, 50), (48, 20), (16, 13), 15, DESERT_GLASS, 1.0, trim=False, tex='glass', grain=False)
    core = c.taper((41, 47), (44, 22), (22, 15), 3.2, 1.2) & erode4(erode4(m))
    p.decal(core, VENOM_AMBER, 0)
    p.decal(c.taper((41, 46), (44, 23), (24, 16), 1.2, 0.8) & core, VENOM_AMBER, 2)
    crust = c.ellipse(42, 51, 8, 4.4) | c.ellipse(35, 54, 5.2, 2.6) | c.ellipse(49, 54, 5, 2.6)
    p.part(crust, SAND, 'ray', base=0, sep=True, rim=False)
    for (x, y) in ((39, 51), (45, 53), (34, 54), (49, 54)):
        p.decal(c.circle(x, y, 0.9) & crust, SAND, -2)
    for (x, y) in ((41, 49), (32, 53)):
        p.decal(c.circle(x, y, 0.8) & crust, SAND, 2)
    p.decal(c.box(34, 24, 35, 32) & m, WHITE, 0)
    p.decal(c.box(33, 20, 34, 21) & m, WHITE, 0)
    wrap_hd(p, g, [(44, 44), (43.5, 40), (43, 36)], 4.0)
    p.sparkle(50, 8, 1)


def mole_claw_hd(p, g):
    """An Ironclaw Mole's digging paw: the furred arm and pad, three long claws still sharp enough to scratch iron."""
    c = p.c
    paw = c.ellipse(23, 38, 14, 12.5)
    arm = c.poly([(7, 47), (12, 32), (21, 36), (18, 54)])
    m = arm | paw
    p.part(m, FUR, 'ray_soft', base=0, sep=False)
    fur_hd(p, m, FUR, -60)
    p.part(c.ellipse(23, 40, 8.5, 7) & paw, FLESH, 'ray', base=0, sep=True, rim=False)
    for (x, y) in ((19, 38), (24, 36), (28, 40)):
        p.decal(c.circle(x, y, 1.6) & paw, FLESH, 1)
    for (y, L) in ((25, 22), (36, 25), (47, 22)):
        fang_hd(p, g, (30, y), (42 + L * 0.3, y - 5), (32 + L, y + 5), 8.0, trim=False)
    if g['level'] >= 1:
        cord_hd(p, [(9, 33), (12, 30), (15, 32)], g['cord'], 2.4)


def snapper_claw_hd(p, g):
    """Old Snapper's claw: the wrist, the palm and two pincers of green-black shell, teeth along their edges."""
    c = p.c
    wrist = c.poly([(9, 55), (11, 42), (21, 37), (27, 46), (18, 57)])
    p.part(wrist, SNAPPER, 'ray', base=0, sep=False, tex='glass')
    palm = c.ellipse(30, 34, 14, 12.5)
    p.part(palm, SNAPPER, 'sphere', base=0, sep=True, tex='glass')
    upper = c.taper((34, 25), (46, 9), (55, 21), 10.5, 2.0)
    lower = c.taper((39, 37), (51, 37), (55, 28), 8.5, 1.8)
    p.part(upper, SNAPPER, 'ray', base=0, sep=True, tex='glass')
    p.part(lower, SNAPPER, 'ray', base=-1, sep=True, tex='glass')
    for (x, y) in ((44, 14), (48, 17), (51, 21), (46, 33), (50, 32)):
        p.decal(c.box(x, y, x + 1.5, y + 1.5) & c.a, BONE, 0)
    for (x, y) in ((25, 28), (30, 37), (18, 47), (35, 27)):
        p.decal(c.circle(x, y, 1.6) & c.a, SNAPPER, 2)
    p.decal(lmask(p, [(14, 44), (17, 52)]) & wrist, SNAPPER, -2)
    p.decal(lmask(p, [(22, 40), (27, 44)]) & wrist, SNAPPER, -2)


def scorpion_stinger_hd(p, g):
    """The last tail segments of a Sandstorm Scorpion: sand-gold plates that bulge between their joints, the bulb,
    and the hooked barb with a bead of amber venom at its tip."""
    c = p.c
    pts = S.curve_pts((15, 52), (11, 24), (29, 19), 30)
    for (i0, i1, wm) in ((0, 11, 13.5), (10, 20, 13.0), (19, 29, 12.4)):
        seg = _barrel(c, pts[i0:i1 + 1], 7.6, wm)
        p.part(seg, SANDGOLD, 'ray', base=0, sep=True, tex='metal')
        mid, nxt = pts[(i0 + i1) // 2], pts[(i0 + i1) // 2 + 1]
        dx, dy = nxt[0] - mid[0], nxt[1] - mid[1]
        L = math.hypot(dx, dy) or 1.0
        for off, lv in ((3.0, 2), (-2.4, -2)):
            kx, ky = mid[0] + dy / L * off, mid[1] - dx / L * off
            p.decal(c.seg(kx - dx / L * 3.2, ky - dy / L * 3.2, kx + dx / L * 3.2, ky + dy / L * 3.2, 1.2) & erode4(seg), SANDGOLD, lv)
    bulb = c.ellipse(34.5, 20.5, 8.8, 8.0)
    thorn = c.taper((35, 20.5), (55, 18), (47, 43), 15.5, 1.0, 30)
    p.part(bulb | thorn, SANDGOLD, 'sphere', base=0, sep=True, cx=37, cy=19, rx=16, ry=14, tex='metal')
    tip = thorn & c.box(41, 25, 64, 64)
    p.part(tip, mat7(Ramp(['#3E200C', '#703E16', '#A8662A', '#D4954A', '#F4C77E'], '#1A0C04'), 'porcelain'), 'ray', base=0, sep=False)
    p.decal(c.ellipse(32.5, 16.5, 3.8, 1.8) & bulb, SANDGOLD, 3)
    p.decal(lmask(p, S.curve_pts((41, 16), (48, 15), (50, 22), 8)) & erode4(thorn), SANDGOLD, 2)
    bead = S.drop(c, 46.5, 50, 3.3, 7.5)
    p.part(bead, VENOM_AMBER, 'sphere', base=0, sep=True, tex='glass')
    p.decal(c.circle(45.4, 48.8, 0.9), VENOM_AMBER, 3)


def _barrel(c, pts, w_joint, w_max):
    """A segment along a point run: narrow at both joints, bulging in the middle."""
    left, right = [], []
    n = len(pts)
    for i, ((x, y), (ux, uy, nx, ny)) in enumerate(zip(pts, tangents(pts))):
        hw = (w_joint + (w_max - w_joint) * math.sin(math.pi * i / (n - 1.0)) ** 0.6) / 2.0
        left.append((x + nx * hw, y + ny * hw))
        right.append((x - nx * hw, y - ny * hw))
    return c.poly(left + right[::-1])


# --- shells and plates
def crab_shell_hd(p, g):
    """A Mudshell Crab's carapace: the mud-brown dome with its grooves and bumps, four side spines, the eye stalks."""
    c = p.c
    shell = (c.ellipse(32, 36, 23, 16) & c.box(0, 19, 64, 64)) | c.ellipse(32, 27, 21, 9)
    for x in (10, 16, 48, 54):
        shell |= c.poly([(x - 2.5, 28), (x - 5 if x < 32 else x + 5, 21), (x + 2.5, 26)])
    p.part(shell, CRAB, 'sphere', base=0, sep=False, cx=28, cy=30, rx=26, ry=20, tex='glass')
    p.decal(c.ellipse(32, 32, 14, 8) & shell, CRAB, 1)
    for pts in ([(21, 26), (27, 33), (25, 45)], [(43, 26), (37, 33), (39, 45)], [(27, 33), (37, 33)]):
        p.decal(lmask(p, pts) & erode4(shell), CRAB, -2)
    for (x, y) in ((19, 40), (45, 40), (32, 44), (25, 24), (39, 24), (32, 38)):
        p.decal(c.circle(x, y, 2.0) & erode4(shell), CRAB, 2)
        p.decal(c.circle(x + 0.7, y + 0.7, 0.9) & erode4(shell), CRAB, 3)
    for x in (25, 39):
        p.part(c.box(x - 1.2, 11, x + 1.2, 20), CRAB, 'flat', base=-1, sep=True, rim=False)
        p.part(c.circle(x, 10.5, 3.0), INKM, 'sphere', base=1, sep=True)
        p.decal(c.circle(x - 1, 9.5, 0.9), WHITE, 0)


def beetle_shell_hd(p, g):
    """A Rock Beetle's plate, hard as slate: two elytra meeting at the seam under the pronotum, the iridescence
    streaking them violet and mint."""
    c = p.c
    left = c.ellipse(25, 35, 13.5, 22.5) & c.box(0, 0, 32, 64)
    right = c.ellipse(39, 35, 13.5, 22.5) & c.box(32, 0, 64, 64)
    pron = c.ellipse(32, 14.5, 12, 7)
    p.part(pron, BEETLE, 'sphere', base=0, sep=False, tex='metal')
    p.part(left, BEETLE, 'sphere', base=0, sep=True, cx=25, cy=31, rx=15, ry=25, tex='metal')
    p.part(right, BEETLE, 'sphere', base=0, sep=True, cx=38, cy=31, rx=15, ry=25, tex='metal')
    p.part(c.box(31, 13, 33, 57) & (left | right), BEETLE, 'flat', base=-3, sep=False, rim=False)
    p.decal(lmask(p, S.curve_pts((19, 20), (15, 34), (19, 50), 10)) & erode4(left), VIOLET, 0)
    p.decal(lmask(p, S.curve_pts((38, 22), (36, 34), (38, 46), 10)) & erode4(right), BEETLE, 3)
    for (x, y) in ((22, 26), (28, 42), (44, 30), (41, 46)):
        p.decal(c.circle(x, y, 1.1) & c.a, BEETLE, -2)
    p.decal(c.ellipse(27, 12, 3, 1.6) & pron, BEETLE, 3)


def tortoise_plate_hd(p, g):
    """A slab of Stone Tortoise shell: the earth-brown dome ringed by its rim, hexagonal scutes scored across it."""
    c = p.c
    dome = c.ellipse(32, 36, 24, 20)
    p.part(dome, EARTH, 'sphere', base=0, sep=False, cx=28, cy=30, rx=27, ry=24, tex='clay')
    rim = c.ring(32, 36, 24, 3.2, 20)
    p.part(rim, STONE, 'ray_soft', base=0, sep=True, rim=False)
    for (x, y) in ((32, 26), (20, 34), (44, 34), (32, 42), (20, 48), (44, 48)):
        h = c.poly([(x - 5, y - 6), (x + 5, y - 6), (x + 8, y), (x + 5, y + 6), (x - 5, y + 6), (x - 8, y)])
        p.decal(S.outline_only(h) & erode4(dome) & ~dilate4(rim), EARTH, -3)
        p.decal(c.box(x - 2.5, y - 3, x + 0.5, y - 1.5) & erode4(dome), EARTH, 2)


def tide_shell_hd(p, g):
    """A Tide Crab's shell, ridged like waves: a scallop fan, the ribs alternating dark and lit, the pink hinge."""
    c = p.c
    fan = (c.sector(32, 47, 25, 22, 158) | c.ellipse(32, 47, 9, 5.5)) & c.ellipse(32, 42, 27, 25)
    p.part(fan, TIDE, 'ray', base=0, sep=False, tex='glass')
    for k, a in enumerate(range(30, 160, 12)):
        r = math.radians(a)
        p.decal(lmask(p, [(32 + math.cos(r) * 4, 46 - math.sin(r) * 3), (32 + math.cos(r) * 24, 46 - math.sin(r) * 22)]) & erode4(fan), TIDE, -2 if k % 2 == 0 else 2)
    p.decal(c.arc(32, 46, 16, 1.4, 30, 150) & erode4(fan), TIDE, -1)
    hinge = c.poly([(21, 50), (43, 50), (39, 57), (25, 57)])
    p.part(hinge, LOTUS, 'ray', base=0, sep=True, rim=False)
    p.decal(c.box(26, 51, 32, 52.5) & hinge, LOTUS, 2)


def pearl_hd(p, g):
    """A river pearl in the half shell it grew in: the nacre cup, its pink lining, the pearl through-lit."""
    c = p.c
    cup = c.ellipse(32, 44, 26, 13) & c.box(0, 43, 64, 64)
    p.part(cup, CRADLE, 'ray', base=0, sep=False, tex='glass')
    for a in range(200, 345, 18):
        r = math.radians(a)
        p.decal(lmask(p, [(32 + math.cos(r) * 8, 44 - math.sin(r) * 4), (32 + math.cos(r) * 25, 44 - math.sin(r) * 12.5)]) & erode4(cup), CRADLE, -2)
    inner = c.ellipse(32, 44, 22, 8.5)
    p.part(inner, LOTUS, 'ray', base=1, sep=True, rim=False)
    pearl = c.circle(32, 32, 15)
    p.part(pearl, M('pearl'), 'sphere', base=0, sep=True, cx=32, cy=32, rx=15, ry=15, tex='glass')
    p.decal(c.arc(32, 32, 13, 1.8, 290, 340) & pearl, LOTUS, 1)
    p.decal(c.ellipse(26.5, 26, 4.2, 3.0), WHITE, 0)
    p.sparkle(51, 15, 2)


def void_carapace_hd(p, g):
    """A plate of Void Crab shell, indigo-black, a few tiny stars inside it as if it went deeper than it is thick."""
    c = p.c
    plate = (c.ellipse(32, 36, 22, 15) & c.box(0, 22, 64, 64)) | c.ellipse(32, 28.5, 19.5, 9)
    for x in (12, 52):
        plate |= c.poly([(x - 2.5, 29), (x - 4.5 if x < 32 else x + 4.5, 21), (x + 2.5, 27)])
    k = max(1, int(round(2 * p.s)))
    p.part((move(plate, k, k) | move(plate, k, k + 1)) & ~plate, VOID, 'flat', base=-2, sep=False, rim=False)
    p.part(plate, VOID, 'sphere', base=0, sep=True, cx=27, cy=27, rx=27, ry=23, tex='glass')
    for pts in ([(21, 28), (25, 34), (23, 46)], [(43, 28), (39, 34), (41, 46)], [(25, 34), (39, 34)]):
        p.decal(lmask(p, pts) & erode4(plate), VOID, -2)
    p.decal(plate & ~erode4(plate) & (far(p) < 52), mat7(R['storm']), 0)
    p.decal(c.ellipse(23, 29, 5.5, 2.4) & erode4(plate), VOID, 3)
    for (x, y) in ((29, 40), (39, 44), (17, 36), (48, 38), (33, 28), (23, 50), (44, 31)):
        p.decal(c.box(x, y, x + 1, y + 1) & erode4(plate), STAR, 0)
    for (x, y) in ((43, 30), (13, 42), (35, 50), (27, 32), (50, 46)):
        p.decal(c.box(x, y, x + 1, y + 1) & erode4(plate), VOID, 3)
    p.decal(S.star4(c, 39, 44, 2) & erode4(plate), SKY, 2)
    p.decal(c.box(39, 44, 40, 45), STAR, 0)


def drone_shell_hd(p, g):
    """A plate broken off a Hollow Drone's carapace: grey Hollow metal with a keel down it, pits in its face, a
    grey-violet sheen on the lit shoulder, the broken edge along the top."""
    c = p.c
    plate = c.poly([(12, 25), (16, 22.5), (19, 15.5), (25, 18), (29.5, 11), (34.5, 16.5), (41, 12), (46, 18), (51.5, 19), (54, 28.5), (51.5, 40),
                    (42.5, 49.5), (32, 55), (21.5, 50.5), (13.5, 40)])
    k = max(1, int(round(2 * p.s)))
    p.part((move(plate, k, k) | move(plate, k + 1, k + 1)) & ~plate, HOLLOW_METAL, 'flat', base=-3, sep=False, rim=False)
    p.part(plate, HOLLOW_METAL, 'sphere', base=0, sep=True, cx=25, cy=25, rx=32, ry=34, tex='metal')
    rim = plate & ~erode4(erode4(plate)) & c.box(0, 22, 64, 64)
    p.decal(rim & (far(p) < 62), HOLLOW_METAL, 2)
    p.decal(rim & (far(p) >= 62), HOLLOW_METAL, -2)
    sheen = erode4(erode4(plate)) & (far(p) >= 38) & (far(p) < 44) & c.box(0, 17, 64, 64)
    p.decal(sheen, HOLLOW_SHEEN, 0)
    keel = lmask(p, [(30, 18), (32, 32), (34, 46), (34, 52)]) & erode4(plate)
    p.decal(keel, HOLLOW_METAL, 3)
    p.decal(move(keel, 1, 0) & erode4(plate) & ~keel, HOLLOW_METAL, -2)
    for (x, y) in ((20, 32), (24, 44), (46, 30), (48, 42), (42, 48), (18, 40), (46, 22)):
        p.decal(c.box(x, y, x + 1.5, y + 1.5) & erode4(plate), HOLLOW_METAL, -3)
        p.decal(c.box(x + 1.5, y + 1.5, x + 3, y + 3) & erode4(plate), HOLLOW_METAL, 1)


# --- feathers are feather_hd rows in PARTS_HD; the two with their own marks:
def comet_plume_hd(p, g):
    """A Comet Sparrow's tail feather, russet at the quill burning to gold at the tip, sparks falling off it."""
    c = p.c
    feather_hd(p, g, RUSSET, shaft=GOLD, shaft_lv=2, tip=GOLD, tip_frac=0.36, width=17.0, notches=((0.5, 1), (0.34, -1)),
               p0=(9, 57), p1=(14, 27), p2=(52, 12))
    for (x, y, lv) in ((55, 20, 3), (57, 27, 2), (53, 33, 1), (58, 37, 1)):
        p.part(c.box(x, y, x + 1.5, y + 1.5), GOLD, 'flat', base=lv, sep=False, rim=False)
    p.sparkle(56, 9, 1)


# --- vials, sacs and wax
def venom_sac_hd(p, g):
    """A Green Viper's venom sac: the plum membrane, the venom pooled bright inside it, veins over it, the duct
    and one drop wept from it."""
    c = p.c
    sac = c.ellipse(30, 37, 18.5, 17) | c.ellipse(37, 23, 9, 7.5)
    p.part(sac, PLUM, 'sphere', base=0, sep=False, cx=28, cy=34, rx=22, ry=20, tex='glass')
    inner = c.ellipse(28, 40, 11.5, 9.5)
    p.part(inner, VENOM, 'sphere', base=0, sep=True, rim=False, tex='glass')
    for pts in ([(15, 28), (20, 38), (16, 47)], [(43, 30), (38, 40), (43, 48)], [(34, 22), (30, 30)]):
        p.decal(lmask(p, pts) & erode4(sac) & ~inner, PLUM, 2)
    duct = c.taper((41, 19), (46, 10), (54, 12), 6.2, 4.2)
    p.part(duct, PINK, 'ray', base=0, sep=True)
    p.decal(c.ellipse(19, 27, 4, 2.8) & sac, PLUM, 3)
    d = S.drop(c, 46, 54, 3.2, 8)
    p.part(d, VENOM, 'sphere', base=0, sep=True, tex='glass')
    p.decal(c.circle(45, 53, 0.9), VENOM, 3)


def soul_wax_hd(p, g):
    """Wax from a Weeping Lantern that burns without heat: the lump with its drips, the violet wisp standing on it."""
    c = p.c
    lump = c.ellipse(32, 44, 19.5, 11.5) | c.ellipse(27, 36, 10.5, 8) | c.ellipse(39, 37.5, 9, 7)
    p.part(lump, WAX, 'ray', base=0, sep=False)
    drips = c.box(18, 47, 20.5, 53) | c.box(43, 49, 45.5, 55.5) | c.box(31, 52, 33.5, 56)
    p.part(drips, WAX, 'ray_soft', base=-1, sep=False)
    for (x, y) in ((19, 53.5), (44, 56), (32, 56.5)):
        p.part(c.circle(x, y, 1.6), WAX, 'sphere', base=0, sep=False)
    p.decal(c.ellipse(25, 34, 4.4, 2.6) & lump, WAX, 3)
    p.decal(lmask(p, [(21, 44), (28, 48), (38, 48)]) & erode4(lump), WAX, -2)
    wisp = S.flame(c, 34, 30, 9.5, 19, -1.5)
    p.part(wisp, VIOLET, 'vgrad', base=0, sep=True, bands=((0.3, 2), (0.6, 1), (0.85, 0), (9, -1)), rim=False)
    p.part(c.ellipse(34, 21, 1.4, 2.6), VIOLET, 'flat', base=3, sep=False, rim=False)
    p.decal(c.ellipse(34, 21, 1.0, 1.8), WHITE, 0)


def frog_leg_hd(p, g):
    """A Reed Frog's leg: the thigh and shin in its mottled green, the webbed foot with three toes, the bone end."""
    c = p.c
    web = c.poly([(44, 40), (33, 55), (45, 58), (57, 50)])
    p.part(web, TOAD, 'ray', base=-1, sep=False, rim=False)
    for a in (238, 275, 312):
        p.part(c.leaf(44, 40, a, 18, 4.6, 0), TOAD, 'ray', base=0, sep=True, rim=False)
    shin = c.taper((28, 28), (44, 25), (44, 40), 10, 6.5)
    p.part(shin, TOAD, 'ray', base=0, sep=True, rim=False)
    thigh = c.ellipse(23, 23, 14, 10.5)
    p.part(thigh, TOAD, 'ray', base=0, sep=True, rim=False)
    p.decal(c.ellipse(21, 28, 9, 4) & thigh, FLESH, 2)
    for (x, y) in ((17, 18), (26, 16), (40, 30), (30, 21), (36, 35), (21, 22)):
        p.decal(c.circle(x, y, 1.6) & c.a, TOAD, -2)
        p.decal(c.circle(x - 0.6, y - 0.6, 0.7) & c.a, TOAD, 1)
    bone = c.seg(10, 15, 14, 19, 4.4) | c.circle(8.5, 15.5, 3.0) | c.circle(10.5, 12.5, 3.0)
    p.part(bone, BONE, 'ray', base=0, sep=True, tex='metal')


def tough_meat_hd(p, g):
    """A slab of stringy beast meat: the cut face marbled with fat, the rind along its foot."""
    c = p.c
    slab = c.poly([(11, 32), (18, 20), (34, 14.5), (49.5, 18), (55, 30), (49.5, 46), (30, 51), (14.5, 46)])
    p.part(slab, FLESH, 'ray', base=0, sep=False)
    top = c.poly([(18, 21.5), (34, 16), (48, 19.5), (41, 28.5), (23, 30.5)])
    p.decal(top & slab, FLESH, 1)
    p.decal(c.ellipse(28, 22, 5, 2.4) & slab, FLESH, 2)
    fat = c.polyline(S.curve_pts((14, 36), (30, 27), (50, 34), 12), 2.8) | c.polyline(S.curve_pts((21, 43), (33, 38), (44, 43), 10), 2.2)
    p.decal(fat & erode4(slab), BONE, 0)
    p.decal(c.polyline(S.curve_pts((14, 36), (30, 27), (50, 34), 12), 1.0) & erode4(slab), BONE, 2)
    rind = c.poly([(14.5, 46), (30, 51), (49.5, 46), (49.5, 50), (30, 55), (14.5, 50)])
    p.part(rind, BONE, 'ray', base=-1, sep=True, rim=False)
    p.decal(c.box(20, 51, 40, 52.4) & rind, BONE, 1)


def rat_tail_hd(p, g):
    """A Reedtail Rat's tail, curled, the skin ringed along it, the furred stump where it was cut."""
    c = p.c
    t = c.taper((16, 50), (54, 58), (48, 26), 10, 4.4) | c.taper((48, 26), (42, 6), (22, 16), 4.8, 2.0)
    p.part(t, PINK, 'ray', base=-1, sep=False)
    inner = erode4(t)
    for pts in (S.curve_pts((16, 50), (54, 58), (48, 26), 26), S.curve_pts((48, 26), (42, 6), (22, 16), 16)):
        tg = tangents(pts)
        for i in range(2, len(pts) - 1, 2):
            (x, y), (ux, uy, nx, ny) = pts[i], tg[i]
            p.decal(lmask(p, [(x + nx * 5, y + ny * 5), (x - nx * 5, y - ny * 5)]) & inner, PINK, -3)
    p.decal(c.polyline(offset_pts(S.curve_pts((16, 50), (54, 58), (48, 26), 20), -2.2)[2:-3], 1.2) & inner, PINK, 2)
    stump = c.ellipse(13, 49, 6.5, 7)
    p.part(stump, GREYFUR, 'ray_soft', base=0, sep=True)
    fur_hd(p, stump, GREYFUR, 200, pitch=3, L=4)


def moss_hd(p, g):
    """Damp moss scraped from a Mossback Toad's back, on the stone it clung to, spore stalks standing out of it."""
    c = p.c
    stone = c.ellipse(32, 48, 24, 11)
    p.part(stone, STONE, 'ray', base=0, sep=False)
    p.decal(c.ellipse(24, 44, 5, 2) & stone, STONE, 2)
    blob = c.ellipse(21, 35, 11, 9) | c.ellipse(35, 29, 12.5, 11.5) | c.ellipse(46, 39, 10, 8) | c.ellipse(30, 40, 18, 7)
    p.part(blob, MOSS, 'ray_soft', base=0, sep=True, rim=False)
    X, Y = XY(p)
    tuft = (np.floor(Y / 3).astype(int) % 2 == 0) & (np.floor((X + 1.5 * (np.floor(Y / 3) % 2)) / 3).astype(int) % 2 == 0)
    p.decal(tuft & erode4(blob), MOSS, -1)
    for (x, y) in ((20, 30), (34, 22), (45, 34), (26, 38), (39, 36), (14, 36)):
        p.decal(c.circle(x, y, 1.1), MOSS, 2)
    for (x, y) in ((25, 42), (42, 44), (17, 40)):
        p.decal(c.circle(x, y, 1.1), MOSS, -2)
    for (x, h) in ((28, 12), (41, 10), (50, 7)):
        p.part(c.box(x - 0.8, 27 - h, x + 0.8, 30), MOSS, 'flat', base=0, sep=True, rim=False)
        p.part(c.circle(x, 26.5 - h, 1.6), STRAW, 'sphere', base=0, sep=True, rim=False)


def bamboo_shoot_hd(p, g):
    """A tender bamboo shoot a Bamboo Monkey was hoarding: the sheaths overlapping up it, the green tip, on earth."""
    c = p.c
    body = c.poly([(18, 55), (20, 40), (25, 25), (32, 9), (39, 25), (44, 40), (46, 55)])
    p.part(body, SAND, 'ray', base=0, sep=False, tex='cloth', axis=90)
    for k, y in enumerate((49, 40, 31, 22)):
        edge = lmask(p, [(17, y + 9), (45 - 2 * k, y - 1)]) if k % 2 == 0 else lmask(p, [(47, y + 9), (21 + 2 * k, y - 1)])
        p.decal(edge & body, SAND, -3)
        p.decal(move(edge, 0, 1) & body & ~edge, SAND, 2)
    for (x, y) in ((26, 46), (38, 36), (30, 28), (36, 51), (23, 53)):
        p.decal(c.circle(x, y, 1.1) & body, SAND, -1)
    tip = c.poly([(27, 20), (32, 6), (37, 20), (32, 17)])
    p.part(tip, BAMBOO, 'ray', base=0, sep=True, rim=False)
    p.part(c.poly([(23, 25), (19, 14), (28, 22)]), BAMBOO, 'ray', base=-1, sep=True, rim=False)
    p.part(c.ellipse(32, 56, 16, 3.6), EARTH, 'ray', base=0, sep=True, rim=False)


# --- pouches and heaps are pouch_hd / heap_hd rows; the ash and dust with their own marks:
def wyrm_ash_hd(p, g):
    """A little heap of star-wyrm ash, gone cold and grey-violet, faint violet embers still in it."""
    c = p.c
    heap = heap_hd(p, WYRM_ASH, (32, 19), 27, 56, dark=((20, 44), (28, 50), (38, 48), (46, 44), (16, 50), (34, 40), (42, 52), (24, 38)),
                   light=((24, 32), (30, 28), (18, 42), (36, 34), (12, 48)))
    for (x, y) in ((32, 42), (26, 46), (42, 46), (36, 52), (22, 52)):
        p.decal(c.circle(x, y, 1.5) & heap, VIOLET, -1)
        p.decal(c.circle(x, y, 0.8) & heap, VIOLET, 2)


def moth_dust_hd(p, g):
    """A small heap of silver dust from an Orbit Moth's wings, a few sparkles still hanging in the air above it."""
    c = p.c
    heap = heap_hd(p, MOTH_SILVER, (31, 30), 25, 56, dark=((18, 50), (26, 52), (34, 50), (42, 54), (14, 54), (30, 44), (48, 54), (22, 46)),
                   light=((20, 44), (28, 38), (16, 48), (34, 42), (12, 52), (24, 48)))
    del heap
    p.sparkle(18, 20, 2)
    p.sparkle(42, 10, 2)
    p.sparkle(48, 26, 1)
    for (x, y) in ((30, 16), (10, 32), (52, 38)):
        p.decal(c.box(x, y, x + 1, y + 1), MOTH_SILVER, 1, only_on=False)
    p.decal(c.ellipse(46, 54, 3, 1.2) & c.a, MOTH_SILVER, 3)


# --- cores, eyes and threads of light
def gravity_core_hd(p, g):
    """The heavy heart of a Gravity Golem: a dense dark sphere of golem stone, violet rings of bent light round it."""
    core_hd(p, GRAVITY, 32, 31, 17.5, rings=((22.5, 6.2, 22, 1.8), (27.5, 9.0, 22, 2.2)), ring_mat=VIOLET)


def mirror_eye_hd(p, g):
    """One of the Thousand-Eye Toad's mirror eyes: the pale ball through-lit, the violet iris rayed round the pupil."""
    c = p.c
    ball = c.circle(32, 32, 22)
    p.part(ball, MIRROR, 'sphere', base=0, sep=False, cx=27, cy=27, rx=27, ry=27, tex='glass')
    for pts in (([(14, 40), (20, 46), (26, 49)]), ([(46, 14), (50, 20), (52, 27)])):
        p.decal(lmask(p, pts) & erode4(ball), IRIS, 2)
    iris = c.circle(34, 32, 11)
    p.part(iris, IRIS, 'ray', base=0, sep=True, tex='glass')
    for a in range(0, 360, 30):
        r = math.radians(a)
        p.decal(lmask(p, [(34 + 4.5 * math.cos(r), 32 - 4.5 * math.sin(r)), (34 + 10 * math.cos(r), 32 - 10 * math.sin(r))]) & iris, IRIS, -2)
    p.part(c.ellipse(34, 32, 4.4, 6.8), INKM, 'flat', base=-1, sep=True, rim=False)
    p.decal(c.ellipse(24, 22, 4.8, 3.2), WHITE, 0)
    p.decal(c.circle(31.5, 28.5, 1.2), WHITE, 0)


def eel_essence_hd(p, g):
    """The bright thread of a Nebula Eel's life, coiled twice into a drop, its tail trailing off the bottom."""
    c = p.c
    outer = S.drop(c, 31, 38, 15.5, 30)
    inner = S.drop(c, 31, 39, 9, 17.5)
    ring_o = outer & ~erode4(erode4(outer))
    ring_i = inner & ~erode4(erode4(inner))
    join = c.polyline(S.curve_pts((30, 9), (24, 24), (23, 36), 12), 2.0) & ~ring_o
    tail = c.polyline(S.curve_pts((44, 48), (52, 57), (58, 50), 10), 2.0) & ~outer
    thread = ring_o | ring_i | join | tail
    p.part(thread, EEL_LIGHT, 'flat', base=0, sep=False, rim=False)
    p.decal(thread & (far(p) < 66), EEL_LIGHT, 1)
    p.decal(thread & (far(p) < 44), EEL_LIGHT, 2)
    p.decal(dilate4(join) & ring_i, EEL_LIGHT, 3)
    for (x, y) in ((30, 6), (32, 8), (16, 36), (44, 30), (31, 22)):
        p.decal(c.box(x, y, x + 1, y + 1) & thread, STAR, 0)
    p.sparkle(50, 16, 1)


def jelly_silk_hd(p, g):
    """A coil of Star Jellyfish silk: loops of translucent violet-blue strands that glow brighter where they cross,
    flecked with star specks and tied with lantern bronze."""
    c = p.c
    rings = [c.ring(x, y, rx, 2.6, ry) for (x, y, rx, ry) in ((29, 31, 22, 18), (31, 33, 20, 16), (33, 35, 18, 14))]
    coil = rings[0] | rings[1] | rings[2]
    p.part(coil, JELLY, 'sphere', base=0, sep=False, cx=24, cy=24, rx=32, ry=28, rim=False, bands=((0.9, 1), (0.45, 0), (-0.1, -1), (-9, -2)))
    p.decal(coil & (sum(r.astype(int) for r in rings) >= 2), JELLY, 2)
    tie = c.poly([(21, 11), (28, 9), (31, 21), (24, 23)])
    p.part(tie, LANTERN, 'ray', base=0, sep=True, tex='metal')
    p.decal(lmask(p, [(22, 16), (29, 14)]) & tie, LANTERN, -2)
    tail = c.polyline(S.curve_pts((42, 50), (44, 58), (53, 57), 10), 2.4) & ~coil
    p.part(tail, JELLY, 'flat', base=0, sep=True, rim=False)
    for (x, y) in ((10, 30), (52, 24), (22, 48), (44, 16), (38, 52)):
        p.decal(c.box(x, y, x + 1, y + 1) & coil, STAR, 0)
    p.sparkle(54, 8, 1)
    p.sparkle(8, 54, 1)


# --- silk, badge and the pet gear
def kite_silk_hd(p, g):
    """Painted silk from a Wind Kite: the red panel on its bamboo spars, an ink cloud painted on it, a gold tail."""
    c = p.c
    silk = c.poly([(14.5, 18), (49.5, 12.5), (46, 42.5), (18, 49.5)])
    p.part(silk, M('red', 'silk'), 'ray', base=0, sep=False, tex='cloth', axis=100)
    for (a, b) in (((14.5, 18), (46, 42.5)), ((49.5, 12.5), (18, 49.5))):
        p.part(c.seg(a[0], a[1], b[0], b[1], 1.8) & silk, BAMBOO, 'flat', base=0, sep=True, rim=False)
    cloud = (c.ellipse(27, 30, 5.5, 3.6) | c.ellipse(34, 26.5, 6.5, 4.8) | c.ellipse(40, 31, 4.6, 3.2)) & silk
    p.part(cloud, INKM, 'flat', base=1, sep=True, rim=False)
    p.decal(c.arc(34, 26.5, 5.5, 1.2, 100, 170) & cloud, INKM, 3)
    p.part(c.polyline([(18, 49.5), (12, 55), (20, 57.5)], 1.8), GOLD, 'flat', base=1, sep=True, rim=False)
    p.decal(c.ellipse(22, 22, 3.5, 1.6) & silk, M('red', 'silk'), 2)


def alliance_badge_hd(p, g):
    """A Nine Peaks disciple's navy-jade badge, its gold peaks gouged out by a deserter's knife, the cord cut."""
    c = p.c
    body = c.poly([(22.5, 16.5), (41.5, 16.5), (49.5, 24), (49.5, 45), (41.5, 53), (22.5, 53), (14.5, 45), (14.5, 24)])
    p.part(body, BADGE, 'ray', base=0, sep=False, tex='jade')
    inner = erode4(erode4(erode4(body)))
    p.decal(S.outline_only(inner), BADGE, -2)
    p.decal(c.ring(32, 35, 13.5, 1.6) & body, GOLD, 0)
    peaks = c.poly([(21, 42), (26, 32), (29, 37), (32, 24.5), (35, 37), (38, 32), (43, 42)]) & inner
    p.decal(peaks, GOLD, 2)
    p.decal(peaks & c.box(0, 39, 64, 64), GOLD, 0)
    for path in ([(43, 20), (38, 27), (32, 32), (22, 46)], [(20, 22), (27, 29), (32, 32), (43, 46)]):
        gm = lmask(p, path) & inner
        p.decal(move(gm, 1, 0) & inner & ~gm, mat7(R['cometiron']), 2)
        p.decal(gm, BADGE, -3)
    for (a, b) in (((18, 33), (22, 29)), ((38, 50), (42, 46)), ((44, 36), (47, 32))):
        p.decal(lmask(p, [a, b]) & inner, BADGE, -3)
    p.erase(c.poly([(44, 46), (51, 41), (51, 50)]))
    hole = c.circle(32, 21, 2.2)
    p.decal(dilate4(hole) & ~hole & body, BADGE, -3)
    p.erase(hole)
    p.part(c.polyline(S.curve_pts((31, 18), (27, 9), (20, 9), 10), 2.4) & ~body, GOLD, 'flat', base=0, sep=True, rim=False)
    p.decal(c.box(17, 8, 19, 9) | c.box(17.5, 10, 19.5, 11), GOLD, 1, only_on=False)


def bone_collar_hd(p, g, band=LEATHER, stud=HEMP, claw=BONE):
    """A collar of boar hide hung with three mole claws: the stitched band, the claws swinging under it. The ladder
    swaps the band, the studs and the claws for a grade's kit."""
    c = p.c
    ring = c.ring(32, 27, 19, 6.5)
    p.part(ring, band, 'ray', base=0, sep=True, tex=TEX.get(band.kind), axis=0)
    for a in range(0, 360, 30):
        x, y = 32 + 19 * math.cos(math.radians(a)), 27 + 19 * math.sin(math.radians(a))
        p.decal(c.circle(x, y, 0.9) & ring, stud, 2)
    p.decal(c.ring(32, 27, 17, 1.0) & ring, band, 2)
    p.decal(c.ring(32, 27, 14.5, 1.0) & ring, band, -2)
    for (x, top) in ((22, 37), (32, 41), (42, 37)):
        fang_hd(p, g, (x, top), (x + 3, top + 8), (x - 1, top + 17), 6.6, claw, trim=False)
    if g['metal'] is not None:
        for x in (22, 42):
            cap_hd(p, x, 35.5, 2.2, g['metal'])


def scale_talisman_hd(p, g, plaque=SERPENT, scale=JADE, cord=None):
    """Serpent and jade scales overlapping on a plaque, hung from a red cord. The ladder swaps the plaque, the scales
    and the cord for a grade's kit."""
    c = p.c
    cord_hd(p, S.curve_pts((13, 10), (32, 26), (51, 10), 16), cord or g['cord'] or M('red', 'silk'), 2.4)
    pm = c.poly([(32, 20), (49, 34), (32, 58), (15, 34)])
    p.part(pm, plaque, 'ray', base=0, sep=True, tex=TEX.get(plaque.kind, 'jade'))
    for (x, y) in ((26, 31), (38, 31), (32, 40), (24, 42), (40, 42), (32, 50)):
        m = shield_hd(c, x, y, 4.6, 5.2) & erode4(pm)
        p.part(m, scale, 'ray', base=0, sep=True, tex=TEX.get(scale.kind, 'jade'), rim=False)
        p.decal(c.box(x - 2, y - 4, x, y - 3) & m, scale, 3)
    if g['metal'] is not None:
        cap_hd(p, 32, 21, 2.4, g['metal'])


def reed_saddle_hd(p, g, seat=STRAW, pad=LEATHER, strap=HEMP, buckle=None):
    """A woven reed saddle on a boar-hide pad, with a girth strap and its bronze buckle. The ladder swaps the seat,
    the pad, the strap and the buckle for a grade's kit."""
    c = p.c
    pm = c.ellipse(32, 40, 25, 11)
    p.part(pm, pad, 'ray', base=0, sep=True, tex=TEX.get(pad.kind), axis=0)
    if pad.kind == 'leather':
        fur_hd(p, pm & c.box(0, 40, 64, 64), pad, -75, pitch=5, L=5)
    sm = c.poly([(12, 34), (20, 20), (44, 20), (52, 34), (32, 42)])
    p.part(sm, seat, 'ray', base=0, sep=True, tex='cloth', axis=0)
    for x in range(18, 48, 5):
        p.decal(c.seg(x, 21, x - 2, 38, 1.0) & erode4(sm), seat, -2)
    for y in (25, 30, 35):
        p.decal(c.seg(16, y, 48, y, 1.0) & erode4(sm), seat, 1)
    p.part(c.box(29.5, 42, 34.5, 58), strap, 'hgrad', base=0, sep=True, rim=False)
    p.part(c.rrect(27.5, 54, 36.5, 58.5, 1.0), buckle or g['metal'] or M('bronze'), 'ray', base=0, sep=True, tex='metal')


# --- shards
def tiny_hollow_shard_hd(p, g):
    """A grey sliver of the Hollow Tide that drinks warmth."""
    shard_hd(p, [(23, 51), (21, 34), (30, 20), (41, 27), (39, 45), (30, 54)], HOLLOW_GLASS, facet=[(22, 34), (30, 22), (35, 29), (28, 38)])


def hollow_shard_hd(p, g):
    """Two shards of the Hollow Tide, the taller behind."""
    shard_hd(p, [(18, 54), (14, 34), (23, 13), (32, 8), (35, 25), (30, 43), (27, 55)], HOLLOW_GLASS, facet=[(16, 34), (23, 15), (30, 11), (27, 32)])
    shard_hd(p, [(30, 54), (35, 30), (46, 18), (52, 32), (43, 54)], HOLLOW_GLASS, facet=[(35, 32), (46, 20), (44, 36)])


def storm_shard_hd(p, g):
    """A splinter of the Expanse's storms: storm-blue glass with a bolt of light frozen in it."""
    shard_hd(p, [(22, 54), (16, 34), (26, 13), (36, 8), (45, 26), (39, 47), (30, 56)], M('storm', 'glass'), facet=[(19, 34), (27, 15), (34, 11), (31, 33)],
             mark=[(33, 17), (27, 30), (36, 32), (29, 47)])


# ============================================================================= the table
def part(fn, **params):
    """A drawing `fn(p, g, **params)`."""
    return lambda p, g: fn(p, g, **params)


PARTS_HD = [
    # id, grade (BEAST_GRADE / items.py), the aura's colour from Mystic up (None: the grade's), the drawing
    # Act I · the valley: hides
    ('boar_hide', 'plain', None, part(hide_hd, fur=FUR, bristle=DARKWOOD)),
    ('thorn_hide', 'common', None, part(hide_hd, fur=TOAD, thorns=BONE)),
    ('grey_hide', 'common', None, part(hide_hd, fur=GREYFUR, marks=((24, 30, 4.5), (40, 40, 4)), scar=[(36, 20), (44, 30)])),
    ('mist_pelt', 'heaven', None, part(hide_hd, fur=MISTFUR, marks=((26, 28, 4.5), (38, 38, 4.5), (28, 44, 3.5)), wisps=True)),
    ('ape_fur', 'heaven', None, ape_fur_hd),
    # scales
    ('jade_scale', 'earth', None, lambda p, g: jade_scale_hd(p)),
    ('lizard_scale', 'earth', None, part(three_scales_hd, mat=LIZARD, tex=None, glint=(15, 21, LIZARD), keel=True)),
    ('serpent_scale', 'earth', None, serpent_scale_hd),
    # feathers
    ('vulture_plume', 'earth', None, part(feather_hd, vane=FUR, shaft=BONE, tip=BONE, tip_frac=0.22, width=18.0)),
    ('cloud_feather', 'heaven', None, part(feather_hd, vane=CLOUD, shaft=CLOUD, shaft_lv=3, tip=SKY, tip_frac=0.12, width=20.0, notches=((0.6, 1), (0.45, -1), (0.3, 1)))),
    ('storm_feather', 'heaven', None, part(feather_hd, vane=STORM, shaft=SKY, shaft_lv=2, tip=NAVY, tip_frac=0.25, width=18.0, bolt=[(40, 26), (33, 33), (40, 33), (31, 43)])),
    ('roc_feather', 'mystic', '#FFB86A', part(feather_hd, vane=M('broth'), shaft=STRAW, shaft_lv=2, tip=M('ember'), tip_frac=0.3, width=21.0, p0=(8, 58), p1=(24, 22), p2=(57, 7),
                                            eye=(42, 19, 5.5, 4.5))),
    # horns, fangs and claws
    ('hollow_antler', 'mystic', '#EEF3F2', hollow_antler_hd),
    ('viper_fang', 'common', None, viper_fang_hd),
    ('hound_fang', 'common', None, hound_fang_hd),
    ('hollow_eel_fang', 'common', None, hollow_eel_fang_hd),
    ('mole_claw', 'plain', None, mole_claw_hd),
    ('snapper_claw', 'common', None, snapper_claw_hd),
    # shells and plates
    ('crab_shell', 'plain', None, crab_shell_hd),
    ('beetle_shell', 'plain', None, beetle_shell_hd),
    ('tortoise_plate', 'plain', None, tortoise_plate_hd),
    ('tide_shell', 'earth', None, tide_shell_hd),
    ('pearl', 'earth', None, pearl_hd),
    # vials, sacs, wax and the rest of the beast
    ('toad_oil', 'plain', None, part(vial_hd, liquid=OIL, level=0.6, spot=(35, 44, 4, 2.6, TOAD))),
    ('leech_oil', 'plain', None, part(vial_hd, liquid=LEECH, shape='tall', level=0.7)),
    ('venom_sac', 'common', None, venom_sac_hd),
    ('soul_wax', 'heaven', None, soul_wax_hd),
    ('frog_leg', 'plain', None, frog_leg_hd),
    ('tough_meat', 'plain', None, tough_meat_hd),
    ('rat_tail', 'plain', None, rat_tail_hd),
    ('moss', 'plain', None, moss_hd),
    ('bamboo_shoot', 'common', None, bamboo_shoot_hd),
    # pouches and shards
    ('ore_dust', 'plain', None, part(pouch_hd, bag=HEMP, dust=STONE, glints=((48, 52), (55, 54), (27, 16)), flecks=((44, 55), (52, 51), (30, 18)), fleck_mat=M('copper'))),
    ('mirror_dust', 'heaven', None, part(pouch_hd, bag=M('indigo', 'silk'), dust=SILVER, glints=((48, 52), (55, 54), (27, 16), (30, 18)), sparks=((56, 44), (12, 14)))),
    ('tiny_hollow_shard', 'common', None, tiny_hollow_shard_hd),
    ('hollow_shard', 'earth', None, hollow_shard_hd),
    # Act II · Azure Expanse
    ('spark_pelt', 'spirit', '#8AEBEE', part(hide_hd, fur=YELLOW, marks=((24, 30, 4.5), (40, 42, 4)), stripe=([(11, 27), (26, 23), (44, 26), (54, 34)], NAVY),
                                             sparks=((52, 14), (11, 40), (44, 56)))),
    ('thunder_horn', 'spirit', '#7FD4FF', thunder_horn_hd),
    ('storm_shard', 'spirit', '#7FD4FF', storm_shard_hd),
    # Act II · Rimefrost and Mirrorwater
    ('rime_fang', 'spirit', '#9FD8FF', rime_fang_hd),
    ('snow_ape_hide', 'spirit', '#BFE2FF', part(hide_hd, fur=SNOWFUR, bristle=MIST, marks=((24, 30, 4.5), (40, 38, 4)), glints=((20, 22), (44, 26), (30, 44)))),
    ('dragonet_scale', 'spirit', '#7CC8E8', part(three_scales_hd, mat=AZURE, tex='jade', glint=(30, 28, GOLD))),
    ('mirror_eye', 'spirit', '#B18DE2', mirror_eye_hd),
    ('harpy_plume', 'spirit', '#F4C77E', part(feather_hd, vane=M('broth'), shaft=WAX, shaft_lv=2, tip=DARKWOOD, tip_frac=0.2, width=20.0, notches=((0.6, 1), (0.42, -1), (0.28, 1)),
                                               p0=(8, 58), p1=(24, 22), p2=(57, 7), bars=(4, DARKWOOD))),
    ('kite_silk', 'spirit', '#FFC9A8', kite_silk_hd),
    # Act II · Sunscar Desert
    ('scorpion_stinger', 'spirit', '#FFB844', scorpion_stinger_hd),
    ('worm_glass_tooth', 'sage', '#BFF2F0', worm_glass_tooth_hd),
    # Act II · Starsea, S46
    ('alliance_badge', 'spirit', '#8FA7D2', alliance_badge_hd),
    ('beast_essence_blood', 'earth', None, part(vial_hd, liquid=BLOOD, glass=M('jade', 'glass'), cork=GOLD, level=0.72, flecks=((28, 44), (36, 50), (32, 54)))),
    ('bone_collar', 'common', None, bone_collar_hd),
    ('scale_talisman', 'earth', None, scale_talisman_hd),
    ('reed_saddle', 'common', None, reed_saddle_hd),
    # Act III · Lantern Star Field
    ('jelly_silk', 'sovereign', '#8C96F0', jelly_silk_hd),
    ('comet_plume', 'sovereign', '#FFC870', comet_plume_hd),
    ('star_powder', 'sovereign', '#7EA4E8', part(pouch_hd, bag=M('red', 'silk'), dust=STAR_DUST, glints=((48, 52), (55, 54), (27, 16)),
                                                 flecks=((44, 55), (51, 51), (57, 55), (26, 18), (31, 16)), fuse=True, sparks=((10, 54),))),
    ('guardian_scale', 'sovereign', STAR_GLOW, guardian_scale_hd),
    ('wyrm_ash', 'will', '#9B78D1', wyrm_ash_hd),
    # v1.2 · the Citadel, the Orbit Ruins, the Tidebreak Front, the Nebula Deep
    ('gravity_core', 'will', '#9B78D1', gravity_core_hd),
    ('moth_dust', 'sovereign', '#D5E0E5', moth_dust_hd),
    ('drone_shell', 'will', '#EEF3F2', drone_shell_hd),
    ('eel_essence', 'will', '#8C96F0', eel_essence_hd),
    ('void_carapace', 'will', '#5670A6', void_carapace_hd),
    ('leviathan_scale', 'will', '#7C86F0', leviathan_scale_hd),
]


def make_part_hd(grade, aura, draw):
    g = GRADE_HD[grade]

    def hd_draw(p):
        draw(p, g)
        glow_hd(p, g, aura)
    return hd_draw


# ----------------------------------------------------------------------------- the pet gear ladders (P7b, item_plan §2.9)
# The three S46 pieces at every grade of the banded ladder (items.py PET_LADDER: a slot's ladder starts at `first`
# and skips the S46 piece's own grade), each in its grade's kit: the collar's band is the kit's grip, its studs the
# guard metal, its claws the blade metal; the talisman's plaque the blade metal, its scales the gem (the guard below
# Earth), its cord the tassel; the saddle's seat the kit cloth, its pad the grip, its strap the wrap, its buckle the
# guard. The aura from Mystic up is the kit's glow.
GRADE_WORD = {'plain': 'training', 'common': 'iron', 'earth': 'jadeiron', 'heaven': 'cloudsteel', 'mystic': 'mistjade', 'spirit': 'stormsteel',
              'sage': 'sunsteel', 'sovereign': 'driftsteel', 'will': 'lanternsteel'}
PET_GEAR_HD = [
    # slot word, the S46 piece's grade, the ladder's first grade, the drawing (its kit parameters)
    ('collar', 'common', 'earth', lambda k: part(bone_collar_hd, band=k['grip'], stud=k['guard'], claw=k['blade'])),
    ('beast_talisman', 'earth', 'common', lambda k: part(scale_talisman_hd, plaque=k['blade'], scale=k['gem'] or k['guard'], cord=k['tassel'])),
    ('saddle', 'common', 'earth', lambda k: part(reed_saddle_hd, seat=k['cloth'], pad=k['grip'], strap=k['wrap'], buckle=k['guard'])),
]
_LADDER = list(GRADE_WORD)
for _slot, _own, _first, _make in PET_GEAR_HD:
    for _grade in _LADDER[_LADDER.index(_first):]:
        if _grade != _own:
            PARTS_HD.append(('%s_%s' % (GRADE_WORD[_grade], _slot), _grade, None, _make(kit(_grade))))

for _id, _grade, _aura, _draw in PARTS_HD:
    _fn = make_part_hd(_grade, _aura, _draw)
    register(FAM, _id, _fn, GROUP)
    hd(_id, _fn)


# ============================================================================= legacy helpers other families still use
# Two 32-px Canvas helpers that the unconverted families import (misc: `vial`; insects, critters and misc: `halo`),
# kept here unchanged until those families' own Style A pass.
from pix import dilate8, rgb  # noqa: E402


def vial(c, liquid, glass=None, cork=None, shape='round', level=0.55, x=16):
    """Legacy: a stoppered glass vial on a 32-px canvas (round, or tall)."""
    glass = glass or R['mist']
    cork = cork or R['wood']
    if shape == 'round':
        body = c.circle(x, 21, 8.5)
        neck = c.rect(x - 3, 7, x + 2, 14)
    else:
        body = S.rounded_rect(c, x - 6, 11, x + 5, 29, 2)
        neck = c.rect(x - 3, 6, x + 2, 11)
    lip = c.rect(x - 4, 7, x + 3, 8)
    c.put(body | neck, glass, 'ray', base=2)
    ys = [y for y in range(32) if body[y].any()]
    top = min(ys) + (max(ys) - min(ys)) * (1 - level)
    liq = erode4(body) & (c.Y > top)
    c.put(liq, liquid, 'ray', base=2)
    c.put(liq & ~move(liq, 0, 1), liquid, 'flat', base=4)  # surface line
    # glass glints
    hx = x - 5 if shape == 'round' else x - 4
    c.put(c.rect(hx, 17 if shape == 'round' else 13, hx, 21 if shape == 'round' else 18), '#F4FBFB', 'flat')
    c.put(c.rect(hx + 1, 15 if shape == 'round' else 12, hx + 1, 15 if shape == 'round' else 12), '#F4FBFB', 'flat')
    c.put(lip, glass, 'flat', base=3, sep=True)
    ck = c.rect(x - 2, 3, x + 1, 6)
    c.put(ck, cork, 'ray', sep=True)
    return body


def halo(c, mask, col, alphas=(110, 50)):
    """Legacy: stepped glow bands around one part only (call after c.outline())."""
    cur = dilate4(mask) & (c.alpha > 0)
    for al in alphas:
        ring = dilate8(cur) & ~cur
        free = ring & (c.alpha == 0)
        c.rgb[free] = rgb(col)
        c.alpha[free] = al
        cur |= ring
