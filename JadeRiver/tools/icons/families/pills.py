"""Pills (HD, Style A): a vessel by the kind of pill, a paper label with the effect mark, the pill in front.

The vessel is the pill's kind (VESSEL_OF): a squat jar for what heals and restores, a footed bottle for what is
taken at a breakthrough, a settling or a cleansing, a gourd for a draught that lifts you for a while, a round box for
what remakes the body, a method or an animal, and an open paper wrap for loose pills (the simple remedies, the
failed pill, the pill that is thrown). The grade is the vessel's material and its trim (PILL_GRADES), never the
colour alone:
  Plain     - coarse hemp paper (the wrap only)
  Common    - earthenware, bronze bands, lip and foot, a red cloth cap tied with straw
  Earth     - white porcelain, jade trims, a jade plug
  Heaven    - pale-blue skyware, silver bands, a silver cloud lid
  Mystic    - violet mistjade, gold trims, a gold domed lid with a violet finial, ring handles, a glow
  Sage      - sun-warmed sand glaze, gold trims, an ember finial, handles, a glow
  Sovereign - driftglass, comet-iron trims, a driftteal finial, handles, a glow
  Law       - night steel with star dots, gold trims, a starlight finial, handles, a glow
  Monarch   - rose gold, pearl trims and finial, handles, a glow
The pill carries the grade too (a groove, a white crescent, a dark ring). Quality is the slot's gem and halo.
"""
import math

from pix import WHITE
from palette import M, TEX, kit
from registry import hd, register
import shapes as S

FAM, GROUP = 'items', 'pills'
ART = 64   # HD (tools/icons/README.md, "How to convert a family")


GLOW_MYSTIC = ('#B18DE2', 1.0)   # the approved Sage-condensing pill's glow (kit('mystic') gives 0.8)


PILL_GRADES = {
    # body: the vessel; trim: the bands, foot, lip, lid and clasp; gem: the finial; lid: the closure's form; cord: the
    # gourd's cord; handles: ring handles on jars and bottles; stars: star dots on the body (Law); glow (Mystic up).
    'plain': dict(body=M('hemp', 'paper'), trim=M('darkwood'), gem=None, lid='cloth', cord='hemp', handles=False, stars=False, glow=None),
    'common': dict(body=M('clay'), trim=M('bronze'), gem=None, lid='cloth', cord='red', handles=False, stars=False, glow=None),
    'earth': dict(body=M('porcelain'), trim=M('jade'), gem=None, lid='plug', cord='red', handles=False, stars=False, glow=None),
    'heaven': dict(body=M('sky', 'porcelain'), trim=M('silver'), gem=None, lid='cloud', cord='sky', handles=False, stars=False, glow=None),
    'mystic': dict(body=M('mistjade'), trim=M('gold'), gem=M('violet'), lid='finial', cord='violet', handles=True, stars=False, glow=GLOW_MYSTIC),
    'sage': dict(body=M('sand', 'porcelain'), trim=M('gold'), gem=M('ember'), lid='finial', cord='red', handles=True, stars=False, glow=kit('sage')['glow']),
    'sovereign': dict(body=M('driftglass'), trim=M('cometiron'), gem=M('driftteal'), lid='finial', cord='driftteal', handles=True, stars=False, glow=kit('sovereign')['glow']),
    # Beyond the equipment kits: Law is lanternsteel (night steel, gold, a starlight finial and star dots), Monarch
    # rose gold set with pearl.
    'law': dict(body=M('nightsteel'), trim=M('gold'), gem=M('starlight'), lid='finial', cord='starlight', handles=True, stars=True, glow=kit('will')['glow']),
    'monarch': dict(body=M('rosegold'), trim=M('pearl', 'porcelain'), gem=M('pearl'), lid='finial', cord='rosegold', handles=True, stars=False, glow=('#E6A888', 1.0)),
}
# The pixel texture of a vessel body or a trim by its material kind (palette.TEX, and jade for jade trims).
PILL_TEX = {'metal': 'metal', 'gold': 'metal', 'glass': 'glass', 'gem': 'glass', 'jade': 'jade', 'porcelain': 'glass'}


def _tex(mat):
    return TEX.get(mat.kind)


def closure_h(lid, half):
    """How far the closure of a mouth of half-width `half` rises above its rim (see `closure`)."""
    k = half / 11.0
    return {'cloth': 9.6 * k, 'plug': 9.2 * k + 2.0, 'cloud': 11.6 * k + 2.5, 'finial': 8 * k + max(4.6, 6.4 * k)}[lid]


def offset(g, top, half):
    """How far down a vessel whose mouth rim sits at `top` moves so its closure keeps the 2-px margin."""
    return max(0.0, 2.0 + closure_h(g['lid'], half) - top)


def closure(p, g, cx, top, half):
    """The grade's closure on a mouth of half-width `half` whose rim is at `top`, scaled from the jar's (half 11):
    a red cloth cap tied with straw (Common), a jade plug (Earth), a silver cloud lid (Heaven), or a domed lid in
    the trim with a gem finial (Mystic and above)."""
    c = p.c
    k = half / 11.0
    trim, lid = g['trim'], g['lid']
    if lid == 'cloth':
        cloth = M(g['cord'], 'silk')
        cap = c.ellipse(cx, top - 4 * k, half - 1.2 * k, 5.6 * k)
        p.part(cap, cloth, 'ray', base=0, sep=True, rim=False)
        p.part(c.box(cx - half + 2.5 * k, top - 2 * k, cx + half - 2.5 * k, top) & cap, M('straw'), 'flat', base=0, sep=True, rim=False)
        p.line([(cx - 5.5 * k, top - 7 * k), (cx + 1.5 * k, top - 8 * k), (cx + 6.5 * k, top - 6 * k)], cloth, -1, 1.0)
    elif lid == 'plug':
        w = max(2.6, 4.0 * k)
        p.part(c.rrect(cx - w, top - 7 * k - 1, cx + w, top + 1.5, 1.2), trim, 'ray', base=0, sep=True, tex=PILL_TEX.get(trim.kind))
        p.part(c.ellipse(cx, top - 7 * k - 1, w + 1.5, 2.2 * k + 1.0), trim, 'ray', base=1, sep=True)
    elif lid == 'cloud':
        dome = (c.ellipse(cx, top, half + 1, 4.5 * k + 1.5) & c.box(0, 0, 64, top)) | c.box(cx - half - 1, top - 1, cx + half + 1, top + 1.5)
        p.part(dome, trim, 'ray', base=0, sep=True, tex='metal')
        r, y1, y2 = 2.8 * k + 0.6, top - (4.5 * k + 1.2), top - (6 * k + 1.5)
        cloud = c.circle(cx - 4.2 * k - 1, y1, r) | c.circle(cx + 4.2 * k + 1, y1, r) | c.circle(cx, y2, r)
        p.part(cloud, trim, 'ray_soft', base=1, sep=True, tex='metal')
        rk = 1.4 * k + 0.4
        p.part(c.circle(cx, y2 - r - rk + 0.6, rk), trim, 'sphere', base=1, sep=True)
    else:   # finial
        dome = (c.ellipse(cx, top + k, half + 4 * k, 6.2 * k) & c.box(0, 0, 64, top + 4 * k)) | c.box(cx - half - 4 * k, top, cx + half + 4 * k, top + 3 * k)
        p.part(dome, trim, 'ray', base=1, sep=True, tex='metal')
        fw, fh = max(3.0, 4.4 * k), max(4.6, 6.4 * k)
        p.part(c.diamond(cx, top - 8 * k, fw, fh), g['gem'], 'ray', base=1, sep=True, spec=(cx - 1.4, top - 8 * k - fh * 0.375))


def handles(p, g, y):
    if g['handles']:
        for x in (6, 46):
            p.part(p.c.ring(x, y, 4.6, 2.1), g['trim'], 'ray_soft', base=1, sep=True)


def stars(p, g, body, pts):
    """Star dots in the gem material on a Law vessel's body."""
    if g['stars']:
        for (x, y) in pts:
            p.decal(p.c.circle(x, y, 0.9) & body, g['gem'], 2)


def jar_hd(p, g):
    """A squat jar with a wide mouth: a band at the shoulder, a lip, the closure on the mouth."""
    c = p.c
    dy = offset(g, 14, 11)
    body = c.ellipse(26, 39 + dy, 21, 19) | c.box(18, 16 + dy, 34, 26 + dy)
    p.part(body, g['body'], 'sphere', base=0, sep=False, cx=23, cy=34 + dy, rx=25, ry=25, tex=_tex(g['body']))
    stars(p, g, body, ((12, 34 + dy), (19, 42 + dy), (40, 36 + dy), (33, 52 + dy)))
    p.part(c.box(5, 24 + dy, 47, 28 + dy) & body, g['trim'], 'vgrad', base=0, sep=True, tex=PILL_TEX.get(g['trim'].kind))
    if g['lid'] != 'finial':
        p.part(c.box(15, 14 + dy, 37, 18 + dy), g['trim'], 'vgrad', base=1, sep=True, tex=PILL_TEX.get(g['trim'].kind))
    closure(p, g, 25.5, 14 + dy, 11)
    handles(p, g, 36 + dy)
    return (16, 31 + dy, 36, 49 + dy)


def bottle_hd(p, g):
    """A round bottle on a foot: bands at the shoulder and the base; a neck with a lip and the closure, or from
    Mystic up a domed lid over the shoulder; ring handles from Mystic up."""
    c = p.c
    trim = g['trim']
    ttex = PILL_TEX.get(trim.kind)
    dy = 0.0 if g['lid'] == 'finial' else offset(g, 11, 8)
    p.part(c.poly([(13, 58 + dy), (18, 50 + dy), (34, 50 + dy), (39, 58 + dy)]), trim, 'ray', base=0, sep=False, tex=ttex)
    body = c.ellipse(26, 36.5 + dy, 21, 17.5)
    p.part(body, g['body'], 'sphere', base=0, sep=True, cx=23, cy=31 + dy, rx=25, ry=22, tex=_tex(g['body']))
    stars(p, g, body, ((12, 30 + dy), (17, 42 + dy), (39, 31 + dy), (31, 47 + dy)))
    for y in (21.5, 49.5):
        p.part(c.box(4, y + dy, 48, y + 1.8 + dy) & body, trim, 'flat', base=1, sep=True, rim=False)
    if g['lid'] == 'finial':
        closure(p, g, 26, 18, 11)
    else:
        p.part(c.box(20, 13 + dy, 32, 22 + dy), g['body'], 'hgrad', base=0, sep=True, tex=_tex(g['body']))
        p.part(c.box(18, 11 + dy, 34, 14 + dy), trim, 'vgrad', base=1, sep=True, tex=ttex)
        closure(p, g, 26, 11 + dy, 8)
    handles(p, g, 32 + dy)
    return (17, 28 + dy, 35, 45 + dy)


def gourd_hd(p, g):
    """A gourd, two bulbs and a waist: a collar and the closure at the mouth, a cord tied at the waist with a
    knot and a tassel down the lower bulb."""
    c = p.c
    dy = offset(g, 9, 5.5)
    lower = c.ellipse(27, 41 + dy, 16.5, 14) | c.poly([(20.5, 24 + dy), (31.5, 24 + dy), (34, 31 + dy), (20, 31 + dy)])
    upper = c.ellipse(26, 20.5 + dy, 8.6, 8.2) | c.box(22.5, 10 + dy, 29.5, 14 + dy)
    p.part(lower, g['body'], 'sphere', base=0, sep=False, cx=24, cy=38 + dy, rx=20, ry=17, tex=_tex(g['body']))
    p.part(upper, g['body'], 'sphere', base=0, sep=True, cx=24, cy=19 + dy, rx=10.5, ry=10, tex=_tex(g['body']))
    stars(p, g, lower | upper, ((15, 38 + dy), (21, 18 + dy), (38, 44 + dy), (30, 26 + dy)))
    p.part(c.box(20.5, 9 + dy, 31.5, 12 + dy), g['trim'], 'vgrad', base=1, sep=True, tex=PILL_TEX.get(g['trim'].kind))
    closure(p, g, 26, 9 + dy, 5.5)
    cord = M(g['cord'], 'silk')
    p.part(c.box(8, 27 + dy, 44, 29.4 + dy) & (lower | upper), cord, 'flat', base=0, sep=True, rim=False)
    p.part(c.circle(20, 28.6 + dy, 2.4), cord, 'sphere', base=1, sep=True, rim=False)
    tas = c.taper((19, 30.5 + dy), (14, 36 + dy), (13, 43 + dy), 2.6, 1.4) | c.taper((20.5, 30.5 + dy), (17.5, 37 + dy), (17, 44 + dy), 2.2, 1.2)
    p.part(tas, cord, 'ray_soft', base=0, sep=True, rim=False)
    return (19, 34 + dy, 37, 50 + dy)


CYL = ((0.10, 1), (0.22, 2), (0.40, 1), (0.62, 0), (0.82, -1), (9, -2))   # a round box wall, lit from the left


def box_hd(p, g):
    """A round lidded box seen from the front and a little above: the lid's rim and the clasp in the trim, the
    closure as the lid's knob, the label on the front."""
    c = p.c
    cx, rx, ry = 25, 19, 6.5
    trim = g['trim']
    ttex = PILL_TEX.get(trim.kind)
    wall = c.box(cx - rx, 31, cx + rx, 50) | c.ellipse(cx, 50, rx, ry)
    p.part(wall, g['body'], 'hgrad', base=0, sep=False, bands=CYL, tex=_tex(g['body']))
    lidwall = c.box(cx - rx - 1, 24, cx + rx + 1, 31) | c.ellipse(cx, 31, rx + 1, ry + 0.3)
    p.part(lidwall, g['body'], 'hgrad', base=0, sep=True, bands=CYL, tex=_tex(g['body']))
    top = c.ellipse(cx, 24, rx + 1, ry + 0.3)
    p.part(top, g['body'], 'sphere', base=1, sep=True, cx=cx - 4, cy=21, rx=26, ry=13, tex=_tex(g['body']))
    stars(p, g, wall | lidwall | top, ((12, 40), (22, 22), (36, 45), (30, 36)))
    rim = (c.box(cx - rx - 1, 28.5, cx + rx + 1, 31) | (c.ellipse(cx, 31, rx + 1, ry + 0.3) & ~c.ellipse(cx, 31, rx - 1.2, ry - 1.9))) & c.box(0, 28.5, 64, 64)
    p.part(rim, trim, 'ray_soft', base=0, sep=True, tex=ttex)
    p.part(c.rrect(cx - 3, 29.5, cx + 3, 38, 1.2), trim, 'ray', base=1, sep=True, tex=ttex)
    closure(p, g, cx, 17.5, 5.5)
    return (15, 37, 35, 53)


def wrap_hd(p, g):
    """An open paper wrap (a square of paper, two corners folded back) for loose pills; the mark is stamped on it."""
    c = p.c
    paper = g['body'] if g['lid'] == 'cloth' and g['body'].kind == 'paper' else M('paper')
    a = math.radians(15)
    cx, cy, h = 27.0, 34.0, 18.5
    corners = [(cx + h * (math.cos(a) * sx - math.sin(a) * sy), cy + h * (math.sin(a) * sx + math.cos(a) * sy)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    wrap = c.poly(corners)
    p.part(wrap, paper, 'bevel', base=0, sep=False, hw=2, sw=2, tex='paper', rim=False)
    # the top and the left corners folded back over the wrap: the paper's underside, a step darker, with a crease
    for i, (fx, fy) in ((0, (0.42, 0.42)), (3, (0.42, 0.42))):
        x, y = corners[i]
        nx, ny = corners[(i + 1) % 4], corners[(i - 1) % 4]
        p1 = (x + (nx[0] - x) * fx, y + (nx[1] - y) * fy)
        p2 = (x + (ny[0] - x) * fx, y + (ny[1] - y) * fy)
        fold = c.poly([p1, p2, (p1[0] + p2[0] - x, p1[1] + p2[1] - y)])
        p.decal(fold & wrap, paper, -1)
        p.line([p1, p2], paper, -3, 1.0)
    return (13, 18, 30, 34)


VESSELS_HD = {'jar': jar_hd, 'bottle': bottle_hd, 'gourd': gourd_hd, 'box': box_hd, 'wrap': wrap_hd}
# The vessel of each kind of pill: by its data group, with the breakthrough, settling and cleansing pills in bottles,
# the body / method / animal pills in boxes, and the loose pills on a wrap.
VESSEL_OF = {'healing': 'jar', 'restoration': 'jar', 'buff': 'gourd', 'utility': 'box', 'breakthrough': 'bottle', 'loose': 'wrap'}


# ----------------------------------------------------------------------------- effect marks
# Each mark is a function (c, x, y) -> [(mask, level offset), ...] centred on (x, y) in icon space, about 12 px
# across; the label decals them in the pill's ink (a level offset of +2 is a highlight).
def _spiral(x, y, r0=5.4, k=0.5, turns=1.6, n=36):
    pts = []
    for i in range(n + 1):
        th = turns * 2 * math.pi * i / n
        pts.append((x + (r0 - k * th) * math.cos(th), y - (r0 - k * th) * math.sin(th)))
    return pts


def mk_heart(c, x, y):
    r = 4.2
    y -= 1
    heart = c.circle(x - r * 0.55, y - r * 0.2, r * 0.6) | c.circle(x + r * 0.55, y - r * 0.2, r * 0.6) | \
        c.poly([(x - r * 1.1, y), (x + r * 1.1, y), (x, y + r * 1.15)])
    return [(heart, 0), (c.circle(x - 2.4, y - 0.8, 1.0), 2)]


def mk_knot(c, x, y):
    return [(c.ring(x - 3, y, 3.8, 1.7) | c.ring(x + 3, y, 3.8, 1.7), 0)]


def mk_spiral(c, x, y):
    return [(c.polyline(_spiral(x, y), 1.6), 0)]


def mk_spiral_up(c, x, y):
    return [(c.polyline(_spiral(x, y + 1.5, 4.8, 0.45, 1.5), 1.5) | c.poly([(x - 2.8, y - 4.4), (x + 2.8, y - 4.4), (x, y - 7.4)]), 0)]


def mk_bone(c, x, y):
    m = c.box(x - 3.6, y - 1.1, x + 3.6, y + 1.1)
    for sx in (-1, 1):
        for sy in (-1, 1):
            m |= c.circle(x + 3.9 * sx, y + 1.6 * sy, 1.75)
    return [(m, 0)]


def mk_drop_leaf(c, x, y):
    return [(S.drop(c, x, y + 2, 3.6, 7.8), 0), (c.polyline([(x, y - 2.5), (x, y + 4)], 1.0), 2)]


def mk_leaf(c, x, y):
    return [(c.leaf(x - 5.8, y + 5.5, 44, 15.5, 7.6, 0.05), 0), (c.polyline([(x - 5, y + 4.7), (x + 3.5, y - 3.5)], 1.0), 2)]


def mk_flame(c, x, y):
    return [(S.flame(c, x, y + 6.5, 9.5, 13), 0), (S.flame(c, x, y + 5.5, 4.2, 6.5), 2)]


def mk_sun(c, x, y):
    m = c.empty()
    for a in range(0, 360, 45):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        m |= c.seg(x + 4.0 * ca, y - 4.0 * sa, x + 6.2 * ca, y - 6.2 * sa, 1.3)
    return [(c.circle(x, y, 2.7) | m, 0)]


def _gate(c, x, y, foot):
    posts = c.box(x - 4.6, y - 4.4, x - 3.1, y + foot) | c.box(x + 3.1, y - 4.4, x + 4.6, y + foot)
    lintel = c.box(x - 6.5, y - 6, x + 6.5, y - 4.4) | c.box(x - 6.5, y - 7.2, x - 5.2, y - 6) | c.box(x + 5.2, y - 7.2, x + 6.5, y - 6)
    return posts | lintel | c.box(x - 5, y - 2.2, x + 5, y - 1)


def mk_gate(c, x, y):
    return [(_gate(c, x, y, 6), 0)]


def mk_gate_cloud(c, x, y):
    cloud = (c.ring(x - 2.4, y + 4.6, 2.0, 1.3) | c.ring(x + 2.4, y + 4.6, 2.0, 1.3)) & c.box(0, 0, 64, y + 4.6)
    return [(_gate(c, x, y, 2.5) | cloud | c.box(x - 5.5, y + 4.6, x + 5.5, y + 6), 0)]


def mk_lamp(c, x, y):
    body = c.ellipse(x, y + 0.8, 4.4, 2.0) | c.box(x - 1.2, y + 2, x + 1.2, y + 4) | c.box(x - 4, y + 4, x + 4, y + 5.5)
    return [(body, 0), (S.drop(c, x, y - 3.8, 1.3, 3.0), 0), (c.circle(x, y - 3.9, 0.6), 2)]


def mk_arrows_loop(c, x, y):
    ring = c.ring(x, y, 4.6, 1.5) & ~c.sector(x, y, 7, 15, 75)
    return [(ring | c.poly([(x + 2.4, y - 1.4), (x + 6.6, y - 1.4), (x + 4.5, y - 5.2)]), 0)]


def mk_arrows(c, x, y):
    m = c.arc(x, y, 4.6, 1.5, 200, 340) | c.poly([(x + 2.6, y + 2.2), (x + 6.6, y + 2.2), (x + 4.6, y - 1.6)])
    m |= c.arc(x, y, 4.6, 1.5, 20, 160) | c.poly([(x - 6.6, y - 2.2), (x - 2.6, y - 2.2), (x - 4.6, y + 1.6)])
    return [(m, 0)]


def _lens(c, x, y, r, d):
    return c.circle(x, y - d, r) & c.circle(x, y + d, r)


def mk_eye(c, x, y):
    return [((_lens(c, x, y, 7.4, 4.2) & ~_lens(c, x, y, 6.0, 4.2)) | c.circle(x, y, 1.9), 0)]


def mk_eye_gate(c, x, y):
    gate = c.box(x - 6.5, y - 7, x + 6.5, y - 5.4) | c.box(x - 4.8, y - 5.4, x - 3.3, y + 6) | c.box(x + 3.3, y - 5.4, x + 4.8, y + 6)
    ey = y + 0.5
    return [(gate | (_lens(c, x, ey, 4.6, 2.7) & ~_lens(c, x, ey, 3.7, 2.7)) | c.circle(x, ey, 1.1), 0)]


def mk_law(c, x, y):
    m = c.box(x - 6, y - 5.2, x + 6, y - 3.6) | c.box(x - 0.8, y - 7.2, x + 0.8, y + 2)
    for px in (x - 4, x + 4):
        m |= c.box(px - 0.8, y - 3.6, px + 0.8, y + 2)
    return [(m | c.arc(x, y + 0.5, 5.2, 1.6, 190, 350), 0)]


def mk_crown(c, x, y):
    m = c.box(x - 5.5, y + 1.5, x + 5.5, y + 4.5)
    for (x0, xt, x1, yt) in ((x - 6, x - 4, x - 2, y - 4.5), (x - 2.5, x, x + 2.5, y - 6), (x + 2, x + 4, x + 6, y - 4.5)):
        m |= c.poly([(x0, y + 2), (xt, yt), (x1, y + 2)])
    return [(m, 0), (c.circle(x, y + 3, 0.9), 2)]


def mk_anchor(c, x, y):
    m = c.ring(x, y - 5, 2.0, 1.3) | c.box(x - 0.9, y - 3.5, x + 0.9, y + 5.5) | c.box(x - 3.8, y - 2.6, x + 3.8, y - 1.2)
    return [(m | c.arc(x, y + 0.5, 5.2, 1.6, 195, 345) | c.circle(x - 4.9, y + 2.4, 1.2) | c.circle(x + 4.9, y + 2.4, 1.2), 0)]


def mk_bolt(c, x, y):
    return [(c.poly([(x + 1.5, y - 7), (x - 4, y + 0.8), (x - 0.3, y + 0.8), (x - 2, y + 7), (x + 4, y - 0.8), (x + 0.3, y - 0.8)]), 0)]


def mk_paw(c, x, y):
    m = c.ellipse(x, y + 2.4, 3.8, 3.0)
    for (px, py) in ((x - 4.3, y - 0.8), (x - 1.6, y - 3.4), (x + 1.6, y - 3.4), (x + 4.3, y - 0.8)):
        m |= c.circle(px, py, 1.55)
    return [(m, 0)]


def mk_fang(c, x, y):
    m = c.poly([(x - 5.2, y - 6), (x - 1, y - 6), (x - 3.1, y + 1.5)]) | c.poly([(x + 1, y - 6), (x + 5.2, y - 6), (x + 3.1, y + 1.5)])
    return [(m | S.drop(c, x + 3.1, y + 5, 1.5, 3.5), 0)]


MARKS_HD = {'heart': mk_heart, 'knot': mk_knot, 'spiral': mk_spiral, 'spiral_up': mk_spiral_up, 'bone': mk_bone,
            'drop_leaf': mk_drop_leaf, 'leaf': mk_leaf, 'flame': mk_flame, 'sun': mk_sun, 'gate': mk_gate,
            'gate_cloud': mk_gate_cloud, 'lamp': mk_lamp, 'arrows_loop': mk_arrows_loop, 'arrows': mk_arrows,
            'eye': mk_eye, 'eye_gate': mk_eye_gate, 'law': mk_law, 'crown': mk_crown, 'anchor': mk_anchor,
            'bolt': mk_bolt, 'paw': mk_paw, 'fang': mk_fang}


def mark_hd(p, lab, name, x, y, ink, lv):
    for mask, d in MARKS_HD[name](p.c, x, y):
        p.decal(mask & lab, ink, lv + d)


# ----------------------------------------------------------------------------- the pill and the extras
def pill_hd(p, g, x, y, r, mat):
    """The pill: a sphere with the grade's band (Earth a groove, Heaven a white crescent, Mystic up a dark ring)."""
    c = p.c
    m = c.circle(x, y, r)
    p.part(m, mat, 'sphere', base=0, sep=True, spec=(x - r * 0.365, y - r * 0.365), tex=PILL_TEX.get(mat.kind))
    lid = g['lid']
    if lid == 'plug':
        p.decal(c.arc(x, y, r - 1.6, 1.3, 200, 340) & m, mat, -2)
    elif lid == 'cloud':
        p.decal(c.arc(x, y + 0.5, r - 1.8, 1.2, 20, 160) & m, WHITE, 0)
    elif lid == 'finial':
        p.decal(c.ring(x, y, r * 0.71, 1.4) & c.box(0, y, 64, 64) & m, mat, -2)
    return m


def extra_grit(p, m, x, y, r, mat):
    """The failed pill: pitted, cracked."""
    c = p.c
    for (px, py) in ((x - 4, y - 1), (x + 2, y - 5), (x + 5, y + 3), (x - 1, y + 5), (x + 1, y + 1)):
        p.decal(c.circle(px, py, 1.1) & m, mat, -2)
    p.line([(x - r * 0.7, y + 2), (x - 2, y - 1), (x + 1, y + 3), (x + r * 0.6, y - 2)], mat, -3, 1.0)


def extra_smoke(p, m, x, y, r, mat):
    """A pill to throw: two wisps of its cloud rising from it."""
    c = p.c
    wisp = c.taper((x - 3, y - r + 1), (x - 6, y - r - 4), (x - 2, y - r - 9), 2.4, 1.2) | c.taper((x + 4, y - r + 2), (x + 7.5, y - r - 2), (x + 6, y - r - 9), 2.6, 1.0)
    p.part(wisp & ~m, mat, 'flat', base=2, sep=False, rim=False)


EXTRAS_HD = {'grit': extra_grit, 'smoke': extra_smoke}


def make_pill_hd(vessel, grade, mark, pill, ink, extra=None):
    """vessel: a VESSELS_HD key; grade: a PILL_GRADES key; mark: a MARKS_HD key; pill: its material name;
    ink: (material name, level) for the mark; extra: an EXTRAS_HD key."""
    def draw(p):
        c = p.c
        g = PILL_GRADES[grade]
        mat, inkmat = M(pill), M(ink[0])
        x0, y0, x1, y1 = VESSELS_HD[vessel](p, g)
        if vessel == 'wrap':
            lab = c.rrect(x0, y0, x1, y1, 1.5)
            mark_hd(p, lab, mark, (x0 + x1) / 2.0, (y0 + y1) / 2.0, inkmat, ink[1])
            for (x, y, r) in ((19, 46, 5.2), (27.5, 53, 4.8)):
                pill_hd(p, g, x, y, r, mat)
            x, y, r = 42, 44, 11.5
        else:
            lab = c.rrect(x0, y0, x1, y1, 1.5)
            p.part(lab, M('paper'), 'bevel', base=0, sep=True, hw=1, sw=1, tex='paper', rim=False)
            mark_hd(p, lab, mark, (x0 + x1) / 2.0, (y0 + y1) / 2.0, inkmat, ink[1])
            x, y, r = 50, 50, 9.6
        m = pill_hd(p, g, x, y, r, mat)
        if extra:
            EXTRAS_HD[extra](p, m, x, y, r, mat)
        if g['glow']:
            p.glow(*g['glow'])
    return draw


def family_pills():
    """The pill families' icons (the item engine, tools/content/items/specs/pills.py `icon=`): (id, kind, grade, mark,
    pill material, mark ink[, extra]), the vessel by kind and the grade's kit."""
    import os
    import sys
    tools = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
    if tools not in sys.path:
        sys.path.append(tools)
    from content.items import engine
    return engine.pill_icons()


PILLS_HD = family_pills() + [
    # id, kind (VESSEL_OF), grade, mark, pill material, mark ink (material, level), extra: the pills no family writes
    ('beast_revival_pill', 'utility', 'earth', 'paw', 'leaf', ('earth', -2)),          # pet medicine (items.py)
    ('beast_marrow_washing_pill', 'utility', 'earth', 'bone', 'pearl', ('earth', -2)),
    ('viper_smoke_pill', 'loose', 'common', 'fang', 'venom', ('navy', -1), 'smoke'),  # thrown from quick-use
]

for _row in PILLS_HD:
    _id, _kind, _grade, _mark, _pill, _ink = _row[:6]
    _draw = make_pill_hd(VESSEL_OF[_kind], _grade, _mark, _pill, _ink, _row[6] if len(_row) > 6 else None)
    register(FAM, _id, _draw, GROUP)
    hd(_id, _draw)
