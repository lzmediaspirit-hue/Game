"""Qi jades and ward discs (HD, Style A): the five inlay gems and the eight attunement wards, at 64 art px shown
1:1 in the 76 px slot, with a native @32 render for the small slots.

A Qi jade is a cut stone in a bezel (`cut_hd`): one template, a distinct cut and colour per jade so they read apart
even in greyscale (a cushion, a marquise, a twelve-sided round, a hexagon, a kite with an eye). Its crown facets are
lit at the top left and dark at the bottom right, the light pools through the far facets, the spokes are drawn and
the table carries one gloss. A ward is a bi disc (`bi_hd`): a pierced disc of storm glass or one of the Star Field's
four stones, sphere-lit with a raised rim and a collar round its hole, through-lit like jade, carved with its sign
in its own light (a thunder scroll, three gales, rain, lightning; a tide, a comet, a wick, the void's stars), with a
soft aura in that light. `bi_hd` is shared with the workshop's jade trinket and its glass fake.
"""
import math

from pix import Ramp, WHITE, dilate4, erode4
from palette import M, mat7
from registry import hd, register
import shapes as S
from families.minerals import lmask, throughlit_hd

FAM, GROUP = 'items', 'qi_jades'
ART = 64   # HD (tools/icons/README.md, "How to convert a family")

GOLD, SILVER, INKM = M('gold'), M('silver'), M('ink')
CARNELIAN = mat7(Ramp(['#4A1410', '#84281C', '#C24A2E', '#EC8A58', '#FFD2A6'], '#200806'), 'gem')
VERDANT = mat7(Ramp(['#0E3A2C', '#1C6A4A', '#34A070', '#7CDCA2', '#D8FFE6'], '#061A12'), 'gem')
AMBER = mat7(Ramp(['#5A300A', '#9A5A12', '#DA9826', '#FFD266', '#FFF6CC'], '#241404'), 'gem')
SPIRIT = M('qi', 'gem')
IRIS = mat7(Ramp(['#241444', '#46287E', '#7650BE', '#B08EEC', '#EEE2FF'], '#10081E'), 'gem')
# The wards: storm glass, and the Star Field's stones (their values step from near-black through teal and orange to
# pale gold, so the four read apart in greyscale).
STORM_GLASS = mat7(Ramp(['#16244A', '#2C4E86', '#4F86C4', '#96C8EE', '#E6F8FF'], '#0A1226'), 'glass')
TIDE = mat7(Ramp(['#082A30', '#10464E', '#1C6E74', '#48A8A4', '#B4EEE2'], '#03141A'), 'glass')
COMET = mat7(Ramp(['#5A3A10', '#9A6A1E', '#D8A83A', '#F3E3A6', '#FFFBEA'], '#241604'), 'glass')
WICK = mat7(Ramp(['#4E1A08', '#8C3212', '#D2622A', '#FFA24E', '#FFE2A0'], '#200A03'), 'glass')
VOID = mat7(Ramp(['#0A0716', '#171028', '#2A1E46', '#4E3A7A', '#9C86D4'], '#040209'), 'glass')
WARD_GLOW = 0.5   # a ward's soft aura, in its own light


def XY(p):
    """Pixel centres in icon space."""
    return p.c.X / p.s, p.c.Y / p.s


def poly_n(cx, cy, rx, ry, n, rot=0.0):
    return [(cx + rx * math.cos(rot + 2 * math.pi * k / n), cy + ry * math.sin(rot + 2 * math.pi * k / n)) for k in range(n)]


# ============================================================================= the cut stone
def cut_hd(p, outer, mat, table=0.5, bezel=None, base=0):
    """A cut stone from any outline `outer`: the bezel behind it (a metal band 3 px wide), the crown facets between
    the outline and the table lit toward the top left, the spokes between them, the table with its gloss, light
    pooling through the far facets, a glint. Returns the stone's mask."""
    c = p.c
    n = len(outer)
    cx, cy = sum(x for x, _ in outer) / n, sum(y for _, y in outer) / n
    whole = c.poly(outer)
    if bezel is not None:
        rmean = sum(math.hypot(x - cx, y - cy) for x, y in outer) / n
        k = 1.0 + 3.2 / rmean
        band = c.poly([(cx + (x - cx) * k, cy + (y - cy) * k) for x, y in outer])
        p.part(band, bezel, 'ray', base=0, sep=False, tex='metal')
        p.decal(band & ~dilate4(whole) & ~erode4(band), bezel, 1)
    p.part(whole, mat, 'flat', base=base - 1, sep=bezel is not None)
    inner = [(cx + (x - cx) * table, cy + (y - cy) * table) for x, y in outer]
    L = (-0.7071, -0.7071)
    for i in range(n):
        a, b = outer[i], outer[(i + 1) % n]
        ta, tb = inner[i], inner[(i + 1) % n]
        mx, my = (a[0] + b[0]) / 2 - cx, (a[1] + b[1]) / 2 - cy
        d = (mx * L[0] + my * L[1]) / (math.hypot(mx, my) or 1)
        lvl = 2 if d > 0.75 else 1 if d > 0.2 else 0 if d > -0.35 else -1 if d > -0.8 else -2
        p.decal(c.poly([a, b, tb, ta]) & whole, mat, base + lvl)
    tab = c.poly(inner)
    p.decal(tab, mat, base + 1)
    p.decal(c.ellipse(cx - (cx - inner[0][0]) * 0.2, cy - (cy - inner[0][1]) * 0.2, abs(inner[0][0] - cx) * 0.6 + 2, abs(inner[0][1] - cy) * 0.6 + 2) & tab, mat, base + 2)
    throughlit_hd(p, whole, mat, start=4)
    for i in range(n):
        d = ((outer[i][0] - cx) * L[0] + (outer[i][1] - cy) * L[1]) / (math.hypot(outer[i][0] - cx, outer[i][1] - cy) or 1)
        p.decal(lmask(p, [inner[i], outer[i]]) & erode4(whole), mat, base + (2 if d > 0.3 else -2))
    p.decal(c.circle(cx - (cx - inner[0][0]) * 0.55 - 1, cy - (cy - inner[0][1]) * 0.55 - 1, 1.5) & tab, mat, 3)
    return whole


def body_jade_hd(p):
    """Body: a cushion of carnelian in gold."""
    cut_hd(p, [(20, 10), (44, 10), (54, 20), (54, 44), (44, 54), (20, 54), (10, 44), (10, 20)], CARNELIAN, 0.5, GOLD)


def swift_jade_hd(p):
    """Swift: a marquise of verdant stone in gold, standing on its point."""
    cut_hd(p, [(32, 8), (41, 19), (46, 32), (41, 45), (32, 56), (23, 45), (18, 32), (23, 19)], VERDANT, 0.45, GOLD)


def essence_jade_hd(p):
    """Essence: a twelve-sided round of amber in gold."""
    cut_hd(p, poly_n(32, 32, 23, 23, 12, math.pi / 12), AMBER, 0.5, GOLD)


def spirit_jade_hd(p):
    """Spirit: a hexagon of Qi-blue stone in silver."""
    cut_hd(p, poly_n(32, 32, 24, 22, 6, 0.0), SPIRIT, 0.5, SILVER)


def insight_jade_hd(p):
    """Insight: a kite of iris stone in gold, an eye opened in its table."""
    c = p.c
    m = cut_hd(p, [(32, 8), (52, 30), (52, 34), (32, 56), (12, 34), (12, 30)], IRIS, 0.46, GOLD)
    eye = c.ellipse(32, 32.5, 6.0, 3.6) & m
    p.decal(eye, IRIS, -3)
    p.decal(c.circle(32, 32.5, 1.9) & m, IRIS, 1)
    p.decal(c.box(31, 31.5, 33, 33.5) & m, WHITE, 0)


# ============================================================================= the bi disc
def bi_hd(p, mat, cx=32.0, cy=32.0, r=26.0, hole=7.5, rim=2.8, tex='jade', glint=True):
    """A pierced disc: sphere-lit from the top left, a raised rim round the edge, a collar round the hole, light
    pooling through it like jade. Returns the disc's mask (rim and collar included) and the band the carving goes on."""
    c = p.c
    disc = c.circle(cx, cy, r) & ~c.circle(cx, cy, hole)
    p.part(disc, mat, 'sphere', base=0, sep=True, cx=cx - 7, cy=cy - 7, rx=r + 9, ry=r + 9, tex=tex)
    outer = c.ring(cx, cy, r, rim) & disc
    p.decal(outer, mat, -1)
    p.decal(c.ring(cx, cy, r - rim, 1.0) & disc, mat, 1)
    p.decal(c.arc(cx, cy, r - rim * 0.5, 1.2, 100, 200) & disc, mat, 1)
    collar = c.ring(cx, cy, hole + 2.6, 2.6) & disc
    p.decal(collar, mat, 1)
    p.decal(c.ring(cx, cy, hole + 0.9, 0.9) & disc, mat, -2)
    p.decal(c.arc(cx, cy, hole + 2.0, 1.2, 100, 200) & disc, mat, 2)
    throughlit_hd(p, disc, mat, start=8)
    band = c.ring(cx, cy, r - rim - 1.0, r - rim - 1.0 - hole - 3.4) & disc
    if glint:
        p.sparkle(cx - r * 0.55, cy - r * 0.55, 1)
    return disc, band


def sign_hd(p, mask, band, mat, lv=2, key=-2):
    """A sign carved into the band: its dark keyline, then the sign in the stone's light."""
    m = mask & band
    p.decal(dilate4(m) & band & ~m, mat, key)
    p.decal(m, mat, lv)
    return m


def spiral_pts(x, y, r0, k, turns=1.5, n=30):
    pts = []
    for i in range(n + 1):
        th = turns * 2 * math.pi * i / n
        pts.append((x + (r0 - k * th) * math.cos(th), y - (r0 - k * th) * math.sin(th)))
    return pts


def ward_thunder_hd(p):
    """Thunder: the square thunder scroll (leiwen) at the four quarters."""
    c = p.c
    disc, band = bi_hd(p, STORM_GLASS)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        x, y = 32 + 16.5 * math.cos(a), 32 + 16.5 * math.sin(a)
        m = (c.box(x - 4, y - 4, x + 4, y + 4) & ~c.box(x - 2, y - 2, x + 2, y + 2)) & ~c.box(x - 1, y - 4.5, x + 1, y - 2)
        m |= c.box(x - 1, y - 1, x + 1, y + 1)
        sign_hd(p, m, band, STORM_GLASS)
    p.glow('#7FD4FF', WARD_GLOW)


def ward_gale_hd(p):
    """Gale: three winds curling out from the hole."""
    c = p.c
    disc, band = bi_hd(p, STORM_GLASS)
    for k in range(3):
        a0 = k * 2 * math.pi / 3 + 0.4
        pts = [(32 + math.cos(a0 + t * 0.26) * (11.0 + t * 1.5), 32 + math.sin(a0 + t * 0.26) * (11.0 + t * 1.5)) for t in range(7)]
        sign_hd(p, c.polyline(pts, 2.2), band, STORM_GLASS)
        p.decal(c.circle(pts[-1][0], pts[-1][1], 1.6) & band, STORM_GLASS, 3)
    p.glow('#7FD4FF', WARD_GLOW)


def ward_rain_hd(p):
    """Rain: drops falling across the disc."""
    c = p.c
    disc, band = bi_hd(p, STORM_GLASS)
    for (x, y) in ((18, 20), (44, 18), (16, 40), (46, 42), (30, 50), (32, 13)):
        sign_hd(p, S.drop(c, x, y + 1.5, 2.4, 5.6), band, STORM_GLASS)
        p.decal(c.circle(x - 0.8, y + 1.2, 0.8) & band, STORM_GLASS, 3)
    p.glow('#7FD4FF', WARD_GLOW)


def ward_lightning_hd(p):
    """Lightning: two bolts, white-hot, cut across the disc."""
    c = p.c
    disc, band = bi_hd(p, STORM_GLASS)
    for pts in (((19, 10), (12, 22), (20, 24), (14, 35)), ((49, 30), (42, 42), (50, 44), (44, 55))):
        m = c.polyline(pts, 2.4)
        sign_hd(p, m, band, STORM_GLASS, 3)
        p.decal(c.polyline(pts, 1.0) & band, WHITE, 0)
    p.glow('#7FD4FF', 0.7)


def ward_tide_hd(p):
    """Tide: two rolling waves cut across the disc, above and below the hole."""
    c = p.c
    disc, band = bi_hd(p, TIDE)
    for y0 in (17.0, 46.0):
        pts = [(8 + x, y0 + 2.2 * math.sin((x + 2) / 3.6)) for x in range(0, 49)]
        m = c.polyline(pts, 2.4)
        p.decal(c.polyline([(x, y + 2.4) for x, y in pts], 2.0) & band, TIDE, -2)
        sign_hd(p, m, band, TIDE, 2, -2)
        p.decal(c.polyline([(x, y - 0.6) for x, y in pts], 1.0) & band, TIDE, 3)
    p.glow('#6FE0D8', WARD_GLOW)


def ward_comet_hd(p):
    """Comet: a comet streaking up across the disc, its head at the upper right, the tail thinning to the lower left."""
    c = p.c
    disc, band = bi_hd(p, COMET)
    tail = c.taper((10, 42), (24, 30), (42, 16), 1.6, 5.0)
    sign_hd(p, tail, band, COMET, 2)
    p.decal(c.taper((16, 38), (26, 29), (40, 18), 0.8, 2.2) & band, COMET, 3)
    head = S.star4(c, 44, 14, 4) | c.circle(44.5, 14.5, 3.2)
    sign_hd(p, head, band, COMET, 3)
    p.decal(c.circle(44.5, 14.5, 1.6) & band, WHITE, 0)
    for (x, y) in ((14, 50), (20, 46), (50, 40)):
        p.decal(c.circle(x, y, 1.0) & band, COMET, 3)
    p.glow('#F3E3A6', WARD_GLOW)


def ward_wick_hd(p):
    """Wick: a lantern flame rising from the lip of the hole, its wick below."""
    c = p.c
    disc, band = bi_hd(p, WICK)
    fl = S.flame(c, 32, 25, 13, 16, 0.3) & disc
    p.decal(dilate4(fl) & disc & ~fl, WICK, -2)
    p.decal(fl, WICK, 1)
    p.decal(S.flame(c, 32, 24, 6.5, 9, 0.2) & fl, WICK, 2)
    p.decal(c.ellipse(32, 18.5, 2.2, 3.4) & fl, WHITE, 0)
    p.decal(c.box(31.2, 24, 32.8, 27) & disc, WICK, -3)
    p.decal(c.arc(32, 32, 9.5, 1.4, 200, 340) & disc, WICK, 2)
    p.glow('#FFB45A', WARD_GLOW)


def ward_void_hd(p):
    """Void: five stars in the dark stone, each with a white heart."""
    c = p.c
    disc, band = bi_hd(p, VOID)
    for (x, y, arm) in ((18, 19, 4), (46, 22, 3), (16, 43, 3), (45, 46, 4), (31, 52, 2)):
        sign_hd(p, S.star4(c, x, y, arm) | c.circle(x + 0.5, y + 0.5, 1.7), band, VOID, 3, -1)
        p.decal(c.box(x, y, x + 1, y + 1) & band, WHITE, 0)
    p.glow('#9B78D1', WARD_GLOW)


JADES_HD = [('ward_thunder', ward_thunder_hd), ('ward_gale', ward_gale_hd), ('ward_rain', ward_rain_hd), ('ward_lightning', ward_lightning_hd),
            ('body_jade', body_jade_hd), ('swift_jade', swift_jade_hd), ('essence_jade', essence_jade_hd), ('spirit_jade', spirit_jade_hd),
            ('insight_jade', insight_jade_hd),
            ('ward_tide', ward_tide_hd), ('ward_comet', ward_comet_hd), ('ward_wick', ward_wick_hd), ('ward_void', ward_void_hd)]

for _id, _draw in JADES_HD:
    register(FAM, _id, _draw, GROUP)
    hd(_id, _draw)
