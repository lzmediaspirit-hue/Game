"""Minerals (HD, Style A): ores, stones, spirit stones, fuel crystals, beast cores, essence salts and the Act II and III
materials at 64 art px, shown 1:1 in the 76 px slot, with a native @32 render for the HUD item ring and the small slots.

Every icon is one drawing `draw(p)` in a 64 x 64 icon space (tools/icons/README.md, "HD drawing model"), the object
inside the 4-px margin; the same description renders at 64 and at 32. One language per kind: raw ore is its
material in a chunk of rock (nuggets, veins or a crystal cluster on the rock); an ingot is a bar with its three
faces and the metal's sheen band; a cut crystal has a table, crown facets and light pooling through its shade side;
a polished stone is a disc, a stele or a chip with stone grain and an inlay; a spirit stone is a cut gem of Qi; a
core is a sphere with a bright heart in its element's shape; sand and dust are a heap in a footed dish or on the
ground. The grade shows by form and trim (a larger stone, more facets, a setting, a richer dish) and, from Mystic
up, the aura as stepped glow bands; never by colour alone. The templates (rock, nugget, crystal, cut gem, core, dish
and heap) are driven from the tables (SPIRIT_STONES_HD, CORE_TIERS x CORE_MARKS, ES_TIERS_HD); the rest are one-offs.
"""
import math

import numpy as np

from pix import BANDS, WHITE, Ramp, bbox, dilate4, erode4, move, shift
from palette import GLOW_STRENGTH, M, STAR_GLOW, TEX, mat7
from registry import hd, register
import shapes as S

FAM, GROUP = 'items', 'minerals'
ART = 64   # HD (tools/icons/README.md, "How to convert a family")

# Act II · Sunscar Desert: the Wardens' fired clay and its paint, the desert glass the sun fused
TERRACOTTA = Ramp(['#4A200F', '#833B1D', '#B96531', '#DC9152', '#F4C088'], '#1F0C05')
FADED_VERMILION = Ramp(['#5A1A14', '#8E2E24', '#BE4A38', '#D9705A', '#EE9C84'], '#240806')
SUNGLASS = Ramp(['#5C2E0A', '#9C5A16', '#D8952E', '#F6CB64', '#FFF3C0'], '#261204')
# Act II · Starsea: the comet's light in the iron
COMET_GLOW = '#BFE6FF'
# Act III · Lantern Star Field: clear crystal and deep jade (the currencies)
CLEAR = Ramp(['#4A5470', '#8290B0', '#BCC8DC', '#E4ECF6', '#FFFFFF'], '#161C2C')
DEEP_JADE = Ramp(['#0A2A22', '#12473A', '#1D6B55', '#3A9B7C', '#9ADCBF'], '#04140F')
# S46 beast cores: each element's stuff and its aura
_CORE_RAMP = {"fire": "fire", "water": "cyan", "wood": "leaf", "earth": "warmstone", "wind": "mist", "thunder": "violet", "soul": "qi",
              "metal": "silver", "star": "gold", "space": "plum"}
_CORE_GLOW = {"fire": "#FF8A4A", "water": "#6FD6FF", "wood": "#7FE08A", "earth": "#E0B870", "wind": "#CFE8F0", "thunder": "#B98CFF", "soul": "#A8F0FF",
              "metal": "#E8EEF2", "star": "#FFF0B0", "space": "#B49CFF"}
# V10d · essence salts from the Calcination Furnace: six salts and the black lacquer of the richer dishes
ES_VERMILION = Ramp(['#4E1210', '#8E2416', '#D2402A', '#F2744A', '#FFB48A'], '#220806')
ES_VERDIGRIS = Ramp(['#123429', '#1F5A45', '#398A68', '#6CBC8E', '#BCE8C8'], '#07170F')
ES_AZURITE = Ramp(['#0E1A48', '#1A307E', '#2A50B6', '#5886E0', '#B4D0FF'], '#060A22')
ES_PEARL = Ramp(['#7A6478', '#B49AB2', '#E6D6E2', '#F8EEF3', '#FFFFFF'], '#2C2230')
ES_AMETHYST = Ramp(['#2A1450', '#4C2690', '#7C48C8', '#B084EE', '#EAD8FF'], '#120828')
ES_STARSALT = Ramp(['#07081A', '#10133A', '#1C225E', '#303C8C', '#5A6CBC'], '#030410')
ES_LACQUER = Ramp(['#07080B', '#121419', '#22262F', '#3C4250', '#7D879C'], '#020203')
# v1.2 Phase C and D: the Orbit Ruins' pale stone, the Ashen Reach's ash and char
V12C_ORBIT_STONE = Ramp(['#3A4658', '#5E6E84', '#94A4B6', '#C4D0DA', '#EEF4F8'], '#151C26')
V12D_ASH = Ramp(['#1C1E22', '#2F3236', '#484C51', '#686D72', '#8E9398'], '#0A0C0E')
V12D_CHAR = Ramp(['#16100E', '#2A1E1A', '#443028', '#5E463A', '#7A6050'], '#080504')


# ============================================================================= HD (Style A, 64 icon space)
# The materials, then the shared helpers (a relative-level decal for grain, ridges and crescents), the templates
# (rock, nugget, crystal, cut gem, core, the salt dish and heap), then the drawings.
WARMSTONE_HD, STONE_HD, IRON_HD, COPPER_HD, JADE_HD, QI_HD, FIRE_HD, EMBER_HD = (M('warmstone'), M('stone'), M('iron'), M('copper'), M('jade'), M('qi', 'gem'),
                                                                                  M('fire'), M('ember'))
GOLD_HD, SILVER_HD, BRONZE_HD, HOLLOW_HD, CLOUDSTEEL_HD, MISTJADE_HD, STORM_HD, SHADOW_HD = (M('gold'), M('silver'), M('bronze'), M('hollow'), M('cloudsteel', 'gem'),
                                                                                             M('mistjade', 'gem'), M('storm', 'gem'), M('shadow'))
MOSS_HD, SAND_HD, COMET_HD, STARLIGHT_HD, MIST_HD, YELLOW_HD, INK_HD = (M('moss'), M('sand'), M('cometiron'), M('starlight'), M('mist'), M('yellow'), M('ink'))
RIVERSTONE_HD = mat7(Ramp(['#27353C', '#3F5560', '#62808C', '#93AFB8', '#CFE2E4'], '#0E171B'), 'matte')
SPIRIT_HIGH_HD = mat7(Ramp(['#155E76', '#2A93B0', '#5ED6E6', '#B6F6F6', '#FFFFFF'], '#05202D'), 'gem')
SERPENT_HD = mat7(Ramp(['#12301F', '#1F5236', '#3A8452', '#7DC47A', '#D2F2B0'], '#07150C'), 'gem')
SENTINEL_HD = mat7(Ramp(['#0F3A44', '#1B6070', '#2E97A4', '#74D2D0', '#D4FAF2'], '#051A20'), 'gem')
TERRACOTTA_HD, VERMILION_HD, SUNGLASS_HD = mat7(TERRACOTTA, 'clay'), mat7(FADED_VERMILION, 'matte'), mat7(SUNGLASS, 'glass')
CLEAR_HD, DEEP_JADE_HD, ORBIT_HD, ASH_HD, CHAR_HD = mat7(CLEAR, 'glass'), mat7(DEEP_JADE, 'jade'), mat7(V12C_ORBIT_STONE, 'matte'), mat7(V12D_ASH, 'matte'), mat7(V12D_CHAR, 'matte')
LACQUER_HD = mat7(ES_LACQUER, 'porcelain')


def XY(p):
    """Pixel centres in icon space."""
    return p.c.X / p.s, p.c.Y / p.s


def lmask(p, pts, w=1.0):
    """The mask of a stroke through icon-space points, as `PixelPainter.line` draws it (1-px Bresenham at 1:1)."""
    c = p.c
    if w <= 1.0 and p.s == 1.0:
        return c.bres_path([(int(math.floor(x)), int(math.floor(y))) for x, y in pts])
    return c.polyline(pts, w)


def levels_hd(p, mask, mat):
    """The level of each painted pixel of `mat` in `mask` (-1 where the pixel is another material)."""
    c = p.c
    idx = np.full(mask.shape, -1, int)
    for i, col in enumerate(mat.c):
        idx[mask & np.all(c.rgb == np.array(col, np.uint8), axis=2)] = i
    return idx


def step_hd(p, mask, mat, k):
    """Shift the painted pixels of `mat` in `mask` by `k` levels: a relative decal for grain, ridges and crescents."""
    c = p.c
    idx = levels_hd(p, mask & c.a, mat)
    sel = idx >= 0
    if sel.any():
        c.rgb[sel] = np.array(mat.c, np.uint8)[np.clip(idx[sel] + k, 0, 6)]
    return sel


def grain_hd(p, m, mat, phase=0):
    """Stone grain: scattered dark and lit flecks in the stone's own tones, inside the part."""
    X, Y = XY(p)
    xi, yi = np.floor(X).astype(int), np.floor(Y).astype(int)
    inner = erode4(m)
    step_hd(p, inner & ((xi * 7 + yi * 3 + phase) % 11 == 0), mat, -1)
    step_hd(p, inner & ((xi * 5 + yi * 11 + phase * 3) % 13 == 0), mat, 1)


def throughlit_hd(p, m, mat, start=3):
    """Light pooling through a crystal or glass part: it gathers along the far (lower-right) inner edge and builds up
    in steps as it goes round, as the painter's glass texture does, on whatever levels the part already has."""
    X, Y = XY(p)
    in2 = erode4(erode4(m))
    if not in2.any():
        return
    far = X + Y
    x0, y0, x1, y1 = bbox(m)
    mid = ((x0 + y0) + (x1 + y1)) / 2.0 / p.s
    for depth, off, k in ((3, start, 1), (2, start + 4, 2), (1, start + 8, 3)):
        step_hd(p, in2 & ~shift(in2, depth, depth) & (far > mid + off), mat, k)


def tilted_ring(p, cx, cy, rx, ry, angle, w):
    """A ring of the ellipse (rx, ry) about (cx, cy), its long axis raised `angle` degrees to the right, and the
    signed distance across it (positive on the near, lower side)."""
    X, Y = XY(p)
    a = math.radians(angle)
    dx, dy = X - cx, Y - cy
    u = dx * math.cos(a) - dy * math.sin(a)
    v = dx * math.sin(a) + dy * math.cos(a)
    outer = (u / rx) ** 2 + (v / ry) ** 2 <= 1.0
    inner = (u / max(0.01, rx - w)) ** 2 + (v / max(0.01, ry - w)) ** 2 <= 1.0
    return outer & ~inner, v


# ----------------------------------------------------------------------------- the templates
def rock_hd(p, pts, mat, top=None, cracks=(), base=0, grain=True):
    """A chunk of rock: an angular lump lit from the top left, a flat broken facet on top with its dark edge, fracture
    lines and stone grain."""
    c = p.c
    m = c.poly(pts)
    p.part(m, mat, 'ray', base=base, sep=True)
    if top:
        t = c.poly(top) & m
        p.decal(t, mat, base + 1)
        p.decal(dilate4(t) & ~t & erode4(m), mat, base - 2)
    for line in cracks:
        p.decal(lmask(p, line) & erode4(m), mat, base - 2)
    if grain:
        grain_hd(p, m, mat)
    return m


def nugget_hd(p, x, y, r, mat, clip=None):
    """A nugget of metal in the rock: a small sphere with the metal's sheen and one glint."""
    m = p.c.circle(x, y, r)
    if clip is not None:
        m &= clip
    p.part(m, mat, 'sphere', base=0, sep=True, cx=x, cy=y, rx=r, ry=r, tex='metal', spec=(x - r * 0.4, y - r * 0.45))
    return m


def crystal_hd(p, bx, by, angle, L, w, mat, base=0, sep=True):
    """A faceted crystal prism from its base (bx, by) along `angle` (0 right, 90 up), `L` long and `w` to each side:
    a lit face and a shade face meeting on the ridge, the tip's two facets, light pooling through the shade face,
    one specular on the lit shoulder."""
    c = p.c
    a = math.radians(angle)
    dx, dy = math.cos(a), -math.sin(a)
    px, py = -dy, dx
    B = (bx, by)
    Sx, Sy = bx + dx * L * 0.68, by + dy * L * 0.68
    T = (bx + dx * L, by + dy * L)
    bl, br = (bx - px * w, by - py * w), (bx + px * w, by + py * w)
    sl, sr = (Sx - px * w, Sy - py * w), (Sx + px * w, Sy + py * w)
    whole = c.poly([bl, sl, T, sr, br])
    lit_left = (-px - py) > 0
    faceL, faceR = c.poly([bl, B, (Sx, Sy), sl]) & whole, c.poly([B, br, sr, (Sx, Sy)]) & whole
    tipL, tipR = c.poly([sl, (Sx, Sy), T]) & whole, c.poly([(Sx, Sy), sr, T]) & whole
    lit, shade, tlit, tshade = (faceL, faceR, tipL, tipR) if lit_left else (faceR, faceL, tipR, tipL)
    p.part(whole, mat, 'flat', base=base - 1, sep=sep)
    p.decal(lit, mat, base + 1)
    p.decal(tlit, mat, base + 2)
    p.decal(tshade, mat, base)
    p.decal(lmask(p, [B, T]) & whole, mat, base + 2)
    throughlit_hd(p, shade | tshade, mat)
    k = 1.0 if lit_left else -1.0
    p.decal(c.circle(bx + dx * L * 0.56 - px * w * 0.5 * k, by + dy * L * 0.56 - py * w * 0.5 * k, 1.0) & whole, mat, 3)
    return whole


def gem_hd(p, cx, cy, rw, rh, mat, table=0.5, base=0, sep=True):
    """A cut gem seen from the front: an octagon with a flat table and eight crown facets, lit to the top left and
    dark to the bottom right, the spokes between them, light pooling through the far facets, a glint on the table."""
    c = p.c
    k = 0.42
    outer = [(cx - rw * k, cy - rh), (cx + rw * k, cy - rh), (cx + rw, cy - rh * k), (cx + rw, cy + rh * k),
             (cx + rw * k, cy + rh), (cx - rw * k, cy + rh), (cx - rw, cy + rh * k), (cx - rw, cy - rh * k)]
    m = c.poly(outer)
    p.part(m, mat, 'flat', base=base - 1, sep=sep)
    inner = [(cx + (x - cx) * table, cy + (y - cy) * table) for x, y in outer]
    L = (-0.7071, -0.7071)
    for i in range(8):
        a, b = outer[i], outer[(i + 1) % 8]
        ta, tb = inner[i], inner[(i + 1) % 8]
        mx, my = (a[0] + b[0]) / 2 - cx, (a[1] + b[1]) / 2 - cy
        d = (mx * L[0] + my * L[1]) / (math.hypot(mx, my) or 1)
        lvl = 2 if d > 0.75 else 1 if d > 0.2 else 0 if d > -0.35 else -1 if d > -0.8 else -2
        p.decal(c.poly([a, b, tb, ta]) & m, mat, base + lvl)
    tab = c.poly(inner)
    p.decal(tab, mat, base + 1)
    p.decal(c.ellipse(cx - rw * 0.1, cy - rh * 0.1, rw * table * 0.5, rh * table * 0.5) & tab, mat, base + 2)
    throughlit_hd(p, m, mat, start=4)
    for i in range(8):
        d = ((outer[i][0] - cx) * L[0] + (outer[i][1] - cy) * L[1]) / (math.hypot(outer[i][0] - cx, outer[i][1] - cy) or 1)
        p.decal(lmask(p, [inner[i], outer[i]]) & erode4(m), mat, base + (2 if d > 0.3 else -2))
    p.decal(c.circle(cx - rw * table * 0.55, cy - rh * table * 0.55, 1.4) & tab, mat, 3)
    return m


CORE_BANDS = ((0.9, 2), (0.6, 1), (0.2, 0), (-0.18, -1), (-0.52, -2), (-9, -3))   # a sphere lit more gently than a pill, so its heart is its light


def core_hd(p, cx, cy, r, mat, heart=None, band=False, swirl=False, coil=False, spec=True):
    """A core: a sphere of the element's stuff, its light pooling through it, a bright heart (a shape from CORE_MARKS,
    or a round one) and, by rank, a band round the middle, a swirl of light inside, or a coil of light round it."""
    c = p.c
    m = c.circle(cx, cy, r)
    if coil:
        ring, v = tilted_ring(p, cx, cy, r * 1.22, r * 0.42, 22, max(2.0, r * 0.14))
        p.part(ring & (v < 0) & ~m, mat, 'flat', base=0, sep=False, rim=False)
    p.part(m, mat, 'sphere', base=0, sep=True, cx=cx, cy=cy, rx=r, ry=r, tex='glass', spec=(cx - r * 0.5, cy - r * 0.5) if spec else None,
           bands=CORE_BANDS)
    if band:
        ring, v = tilted_ring(p, cx, cy, r + 0.5, r * 0.36, 16, max(2.0, r * 0.15))
        near = ring & (v > 0) & m
        p.decal(near, mat, -1)
        p.decal(near & ~shift(near, 0, -1), mat, 1)
    if swirl:
        p.decal(c.arc(cx, cy, r * 0.7, max(2.0, r * 0.16), 20, 240) & m, mat, 2)
        p.decal(c.arc(cx, cy, r * 0.7, max(1.0, r * 0.07), 60, 200) & m, mat, 3)
        p.decal(c.arc(cx + r * 0.1, cy + r * 0.12, r * 0.42, max(1.6, r * 0.12), 190, 50) & m, mat, 1)
    if heart:
        # the heart is the brightest thing in the core, a step darker round it so it holds on a pale sphere too
        body = heart[0][0] & m
        p.decal(dilate4(body) & ~body & m, mat, -1)
        for mask, lv in heart:
            p.decal(mask & m, mat, lv)
    if coil:
        ring, v = tilted_ring(p, cx, cy, r * 1.22, r * 0.42, 22, max(2.0, r * 0.14))
        near = ring & (v >= 0)
        p.part(near, mat, 'flat', base=1, sep=True, rim=False)
        p.decal(near & ~shift(near, 0, -1), mat, 3)
    return m


# The bright heart of a beast core in its element's shape: (c, x, y, s) -> [(mask, level offset), ...], `s` its
# half-size; the heart is light (+2) with a white-hot point (+3).
def _dot(c, x, y, s):
    return c.circle(x, y, s * 0.3)


def mk_fire(c, x, y, s):
    return [(S.flame(c, x, y + s * 1.05, s * 1.6, s * 2.4, 0.15), 2), (c.circle(x - s * 0.1, y + s * 0.3, s * 0.35), 3)]


def mk_water(c, x, y, s):
    pts = [(x - s * 1.1 + s * 2.2 * i / 12.0, s * 0.3 * math.sin(math.pi * i / 3.0)) for i in range(13)]
    m = c.polyline([(px, y - s * 0.45 + py) for px, py in pts], s * 0.42) | c.polyline([(px, y + s * 0.45 + py) for px, py in pts], s * 0.42)
    return [(m, 2), (c.circle(x - s * 0.55, y - s * 0.45, s * 0.28), 3)]


def mk_wood(c, x, y, s):
    return [(c.leaf(x - s * 1.0, y + s * 1.0, 45, s * 2.7, s * 1.5, 0.0, tip_power=0.75), 2), (_dot(c, x - s * 0.15, y + s * 0.15, s), 3)]


def mk_earth(c, x, y, s):
    m = c.poly([(x - s * 1.15, y + s * 0.8), (x - s * 0.5, y - s * 0.2), (x - s * 0.15, y + s * 0.25), (x + s * 0.3, y - s * 0.95), (x + s * 1.15, y + s * 0.8)])
    return [(m, 2), (c.circle(x + s * 0.3, y - s * 0.4, s * 0.28), 3)]


def mk_wind(c, x, y, s):
    pts = []
    for i in range(29):
        th = 1.55 * 2 * math.pi * i / 28.0
        r = s * 1.05 * (1.0 - 0.55 * i / 28.0)
        pts.append((x + r * math.cos(th), y - r * math.sin(th)))
    return [(c.polyline(pts, s * 0.42), 2), (c.circle(x + s * 0.2, y - s * 0.1, s * 0.3), 3)]


def mk_thunder(c, x, y, s):
    m = c.poly([(x + s * 0.35, y - s * 1.15), (x - s * 0.7, y + s * 0.15), (x - s * 0.05, y + s * 0.15), (x - s * 0.35, y + s * 1.15),
                (x + s * 0.7, y - s * 0.15), (x + s * 0.05, y - s * 0.15)])
    return [(m, 2), (c.circle(x, y, s * 0.28), 3)]


def mk_soul(c, x, y, s):
    lens = c.circle(x, y - s * 0.65, s * 1.2) & c.circle(x, y + s * 0.65, s * 1.2)
    return [(lens, 2), (c.circle(x, y, s * 0.42), -1), (c.circle(x - s * 0.15, y - s * 0.15, s * 0.16), 3)]


def mk_metal(c, x, y, s):
    return [(c.diamond(x, y, s * 0.62, s * 1.2), 2), (c.circle(x - s * 0.1, y - s * 0.2, s * 0.26), 3)]


def mk_star(c, x, y, s):
    return [(c.diamond(x, y, s * 1.2, s * 0.34) | c.diamond(x, y, s * 0.34, s * 1.2), 2), (_dot(c, x, y, s), 3)]


def mk_space(c, x, y, s):
    return [(c.ring(x, y, s * 1.0, s * 0.42), 2), (c.circle(x, y, s * 0.3), 3)]


def mk_round(c, x, y, s):
    return [(c.circle(x, y, s * 0.95), 2), (c.circle(x - s * 0.15, y - s * 0.15, s * 0.42), 3)]


CORE_MARKS = {'fire': mk_fire, 'water': mk_water, 'wood': mk_wood, 'earth': mk_earth, 'wind': mk_wind, 'thunder': mk_thunder, 'soul': mk_soul,
              'metal': mk_metal, 'star': mk_star, 'space': mk_space, 'round': mk_round}


# ----------------------------------------------------------------------------- ores: the material in its rock
def ore_copper_hd(p):
    """Copper ore: nuggets of soft copper in a lump of warm quarry stone, one spot of green patina."""
    c = p.c
    m = rock_hd(p, [(7, 40), (13, 21), (29, 12), (47, 15), (57, 31), (54, 51), (34, 58), (13, 54)], WARMSTONE_HD,
                top=[(13, 22), (29, 13), (46, 16), (38, 27), (22, 29)], cracks=[[(22, 29), (38, 27)], [(38, 27), (52, 38)], [(22, 29), (14, 47)]])
    clip = erode4(m)
    for (x, y, r) in ((24.5, 37, 6.4), (43, 40.5, 5.4), (35, 23.5, 4.2), (16, 45.5, 3.4), (44, 27, 3.0), (30, 50, 2.8)):
        nugget_hd(p, x, y, r, COPPER_HD, clip)
    p.part(c.ellipse(49, 48, 4.4, 2.8) & clip, JADE_HD, 'flat', base=0, sep=False, rim=False)
    p.decal(c.ellipse(48, 47.5, 2.2, 1.2) & clip, JADE_HD, 1)


def ore_riverstone_hd(p):
    """Riverstone: two river-polished stones, one behind, a pale quartz band round the front one."""
    c = p.c
    back = c.ellipse(40, 25, 17, 11)
    p.part(back, WARMSTONE_HD, 'sphere', base=0, sep=False, cx=36, cy=22, rx=19, ry=13)
    grain_hd(p, back, WARMSTONE_HD, 2)
    p.decal(c.ellipse(33, 19, 4, 2) & back, WARMSTONE_HD, 2)
    front = c.ellipse(29, 41, 24, 15)
    p.part(front, RIVERSTONE_HD, 'sphere', base=0, sep=True, cx=24, cy=37, rx=27, ry=18)
    grain_hd(p, front, RIVERSTONE_HD, 5)
    band = (c.ellipse(30, 52, 28, 12) & ~c.ellipse(30, 53.6, 28, 10.4)) & erode4(front)
    p.decal(band, M('paper'), 0)
    p.decal(band & c.box(0, 0, 30, 64), M('paper'), 1)
    p.decal(c.ellipse(22, 32, 6, 2.6) & front, RIVERSTONE_HD, 3)
    p.decal(c.circle(17, 35, 1.0) & front, RIVERSTONE_HD, 3)


def ore_jadeiron_hd(p):
    """Jadeiron: iron rock threaded with veins of jade, two jade crystals grown out of the top facet."""
    c = p.c
    m = rock_hd(p, [(6, 38), (18, 18), (34, 10), (52, 18), (58, 36), (48, 54), (26, 58), (10, 52)], IRON_HD,
                top=[(18, 19), (34, 11), (50, 19), (36, 28), (22, 30)], cracks=[[(22, 30), (36, 28)], [(36, 28), (50, 40)], [(22, 30), (14, 48)]])
    clip = erode4(m)
    for (p0, p1, p2, w0, w1) in (((11, 44), (28, 30), (53, 28), 4.6, 3.0), ((28, 36), (36, 48), (46, 52), 3.4, 2.2)):
        vein = c.taper(p0, p1, p2, w0, w1) & clip
        p.part(vein, JADE_HD, 'flat', base=-1, sep=True, rim=False, tex='jade')
        p.decal(lmask(p, S.curve_pts((p0[0], p0[1] - 1), (p1[0], p1[1] - 1), (p2[0], p2[1] - 1), 12)) & vein, JADE_HD, 1)
    crystal_hd(p, 30, 27, 72, 20, 5.6, JADE_HD)
    crystal_hd(p, 41, 29, 38, 15, 4.8, JADE_HD)


def cluster_ore_hd(p, rock, crystal, rock_pts, top, crystals, base=0):
    """An ore that grows as a cluster of crystals out of a chunk of rock: the back crystals first, the front last."""
    m = rock_hd(p, rock_pts, rock, top=top, base=base)
    for (bx, by, ang, L, w) in crystals:
        crystal_hd(p, bx, by, ang, L, w, crystal)
    return m


def ore_cloudsteel_hd(p):
    """Cloudsteel ore: pale, feather-light rock from the sky ledges with a cluster of pale-blue crystals and a glint."""
    cluster_ore_hd(p, HOLLOW_HD, CLOUDSTEEL_HD, [(7, 44), (14, 30), (26, 24), (40, 28), (56, 38), (54, 54), (32, 58), (12, 56)],
                   [(14, 31), (26, 25), (40, 29), (32, 38), (18, 40)],
                   [(26, 36, 88, 30, 6.8), (38, 38, 55, 22, 6.0), (18, 40, 130, 16, 4.8)])
    p.sparkle(50, 15, 2)


def ore_mystic_hd(p):
    """Mystic ore: dark rock that hums, a cluster of violet mistjade crystals on it, its aura round it."""
    cluster_ore_hd(p, SHADOW_HD, MISTJADE_HD, [(7, 44), (16, 28), (28, 24), (44, 26), (56, 40), (52, 54), (30, 58), (12, 56)],
                   [(16, 29), (28, 25), (42, 27), (32, 36), (20, 38)],
                   [(28, 38, 95, 32, 7.2), (40, 40, 60, 22, 5.6), (18, 42, 135, 16, 4.4)])
    p.glow('#B18DE2', GLOW_STRENGTH['mystic'])


def ore_stormsteel_hd(p):
    """Stormsteel ore: blue-black rock with storm-blue crystals, a bolt still forking down into it."""
    cluster_ore_hd(p, SHADOW_HD, STORM_HD, [(7, 46), (14, 30), (26, 24), (42, 26), (56, 38), (54, 54), (32, 58), (12, 56)],
                   [(14, 31), (26, 25), (42, 27), (32, 38), (18, 40)],
                   [(28, 36, 92, 32, 6.8), (40, 38, 58, 22, 5.6), (18, 40, 132, 16, 4.4)])
    bolt = p.c.poly([(31, 6), (25, 18), (30, 18), (26, 30), (35, 16), (30, 16)])
    p.part(bolt, M('ice'), 'flat', base=3, sep=True, rim=False)
    p.decal(p.c.poly([(31, 8), (27, 17), (30.5, 17), (28.5, 25), (33, 17.5), (29.5, 17.5)]) & bolt, WHITE, 0)
    p.glow('#7FD4FF', GLOW_STRENGTH['spirit'])


def driftglass_hd(p):
    """Driftglass: a sea-rounded lump of violet glass with teal light seeping in from the far side, and a small bead."""
    c = p.c
    violet, teal = M('driftglass'), M('driftteal')
    far = (c.X + c.Y) / p.s
    m = c.poly([(7, 35), (11, 25), (20, 19), (32, 17), (43, 19), (51, 24), (54, 33), (51, 42), (42, 49), (28, 51), (15, 49), (8, 43)])
    p.part(m, violet, 'sphere', base=0, sep=False, cx=30, cy=34, rx=26, ry=19, tex='glass')
    p.part(m & (far >= 62), teal, 'sphere', base=0, sep=False, cx=31, cy=33, rx=24, ry=18, tex='glass')
    # frosted skin on the lit rim, one wet gleam
    p.decal(m & ~erode4(erode4(m)) & (far <= 50), violet, 1)
    p.line([(14, 27), (19, 22), (26, 20)], WHITE, 0, 1.2)
    p.decal(c.circle(16, 31, 0.9), WHITE, 0)
    bead = c.poly([(39, 51), (43, 44), (51, 42), (57, 46), (57, 54), (50, 58), (42, 57)])
    p.part(bead, teal, 'sphere', base=0, sep=True, tex='glass')
    p.part(bead & (far <= 92), violet, 'sphere', base=0, sep=False, cx=48, cy=50, rx=10, ry=9, tex='glass')
    p.decal(c.circle(45.5, 46, 1.0), WHITE, 0)
    p.sparkle(50, 30, 1)
    p.glow('#9C8CE0', 0.45)


def ore_sunglass_hd(p):
    """Sunglass: a lump of amber desert glass the sun fused out of the dunes, the light held inside it, a crust of
    sand still on its lower side."""
    c = p.c
    m = c.poly([(10, 40), (13, 26), (22, 16), (34, 10), (46, 12), (55, 22), (56, 36), (51, 48), (38, 54), (24, 56), (13, 52)])
    p.part(m, SUNGLASS_HD, 'sphere', base=0, sep=False, cx=30, cy=32, rx=27, ry=24, tex='glass')
    top = c.poly([(13, 26), (22, 16), (34, 10), (46, 12), (55, 22), (42, 25), (26, 29)]) & m
    p.decal(top, SUNGLASS_HD, 1)
    p.decal(dilate4(top) & ~top & erode4(m), SUNGLASS_HD, -1)
    p.decal(c.poly([(34, 11), (46, 13), (40, 19)]) & top, SUNGLASS_HD, 2)
    p.decal(c.ellipse(42, 40, 6, 4.4) & m, SUNGLASS_HD, 2)
    p.decal(c.ellipse(43, 39, 3, 2.2) & m, SUNGLASS_HD, 3)
    p.decal(lmask(p, [(28, 34), (32, 40), (30, 46)]) & erode4(m), SUNGLASS_HD, -1)
    crust = m & c.poly([(6, 36), (12, 42), (16, 38), (20, 44), (26, 42), (30, 48), (36, 46), (40, 54), (44, 62), (6, 62)])
    crust |= c.circle(11, 48, 3.6) | c.circle(17, 55, 3.2) | c.circle(27, 57.5, 2.8)
    p.part(crust, SAND_HD, 'ray', base=-1, sep=True, rim=False)
    grain_hd(p, crust, SAND_HD, 3)
    p.decal(lmask(p, [(18, 24), (24, 18)]) | c.box(28, 14, 32, 15), M('paper'), 3)
    p.sparkle(43, 39, 1)
    p.sparkle(52, 8, 2)
    p.glow('#FFC870', GLOW_STRENGTH['sage'])


# ----------------------------------------------------------------------------- an ingot, a drop of Qi, a splinter
def ingot_hd(p, mat):
    """A bar of metal seen from the front and a little above: the dark end, the front face with the metal's sheen
    band, the lit top with a bright edge."""
    c = p.c
    end = c.poly([(46, 25), (52, 14), (56, 37), (50, 49)])
    p.part(end, mat, 'flat', base=-2, sep=False, tex='metal')
    front = c.poly([(12, 25), (46, 25), (50, 49), (8, 49)])
    p.part(front, mat, 'ray', base=0, sep=True, tex='metal')
    top = c.poly([(18, 14), (52, 14), (46, 25), (12, 25)])
    p.part(top, mat, 'bevel', base=1, sep=True, hw=2, sw=1, tex='metal')
    p.decal(c.box(14, 24, 46, 25) & front, mat, 2)
    p.decal(c.box(19, 14, 51, 15) & top, mat, 3)
    return front


def comet_iron_hd(p):
    """Comet iron: a bar of pale blue-grey metal, the comet that once passed through it streaking along the front
    face to a white head near the end."""
    c = p.c
    front = ingot_hd(p, COMET_HD)
    inner = erode4(front)
    ice = M('ice')
    p.decal(c.taper((10, 46), (24, 42), (42, 34), 2.0, 7.0) & inner, ice, 0)
    p.decal(c.taper((16, 44), (28, 40), (42, 34), 1.6, 4.6) & inner, ice, 2)
    p.decal(c.ellipse(41, 33.5, 3.8, 2.8) & inner, ice, 3)
    p.decal(c.ellipse(41, 33.5, 2.2, 1.6) & inner, WHITE, 0)
    p.sparkle(45, 32, 1)
    p.glow(COMET_GLOW, 0.7)


def refining_essence_hd(p):
    """Refining Essence: the salvaged Qi of a broken piece, an amber drop of light with a spark above it."""
    c = p.c
    drop = c.ellipse(31, 40, 16, 16) | c.poly([(17, 34), (31, 7), (45, 34)])
    p.part(drop, FIRE_HD, 'sphere', base=0, sep=False, cx=27, cy=32, rx=20, ry=26, rim=False)
    p.decal(c.ellipse(27, 38, 5.6, 7.4) & drop, FIRE_HD, 2)
    p.decal(c.ellipse(26, 36, 3.0, 4.2) & drop, FIRE_HD, 3)
    p.decal(lmask(p, [(23, 44), (23, 48)]) & drop, FIRE_HD, 2)
    p.sparkle(50, 16, 2)
    p.sparkle(14, 50, 1)


def spirit_stone_shard_hd(p):
    """Spirit Stone Shard: splinters of crystallised Qi, two long ones and a chip, and a glint."""
    c = p.c
    crystal_hd(p, 24, 57, 75, 50, 10.4, QI_HD)
    crystal_hd(p, 41, 55, 45, 24, 6.0, QI_HD)
    chip = c.poly([(9, 51), (16, 43), (21, 53)])
    p.part(chip, QI_HD, 'flat', base=0, sep=True)
    p.decal(c.poly([(9, 51), (16, 43), (14, 51)]) & chip, QI_HD, 2)
    p.sparkle(48, 14, 2)


# ----------------------------------------------------------------------------- spirit stones and fuel crystals
SPIRIT_STONES_HD = {
    # level: the Qi's material, the gem's half-size, whether it is set in gold prongs (Mystic), sparkles, the aura
    'low': dict(mat=JADE_HD, rw=15, rh=14, prongs=False, sparkles=(), glow=None),
    'mid': dict(mat=QI_HD, rw=19, rh=17.5, prongs=False, sparkles=((51, 13, 2),), glow=None),
    'high': dict(mat=SPIRIT_HIGH_HD, rw=21, rh=20, prongs=True, sparkles=((53, 11, 2), (10, 53, 1)), glow=('#8AEBEE', GLOW_STRENGTH['mystic'])),
}


def make_spirit_stone_hd(level):
    def draw(p):
        c = p.c
        T = SPIRIT_STONES_HD[level]
        cx, cy = 32, 33
        gem_hd(p, cx, cy, T['rw'], T['rh'], T['mat'])
        if T['prongs']:
            for (x, y) in ((cx - T['rw'] - 1.5, cy), (cx + T['rw'] + 1.5, cy), (cx, cy - T['rh'] - 1.5), (cx, cy + T['rh'] + 1.5)):
                p.part(c.circle(x, y, 3.2), GOLD_HD, 'sphere', base=0, sep=True, tex='metal', spec=(x - 1.2, y - 1.4))
        for (x, y, arm) in T['sparkles']:
            p.sparkle(x, y, arm)
        if T['glow']:
            p.glow(*T['glow'])
    return draw


def make_fuel_crystal_hd(level):
    """A fuel crystal: one prism of fire-orange crystal standing on a stone foot; the mid one three, on a wider foot
    banded in silver, and the fuel already burning above it."""
    def draw(p):
        c = p.c
        if level == 'low':
            crystal_hd(p, 30, 56, 82, 44, 10.0, FIRE_HD)
            foot = c.ellipse(30, 56, 12, 4)
            p.part(foot, WARMSTONE_HD, 'ray', base=0, sep=True)
        else:
            crystal_hd(p, 18, 54, 115, 28, 6.8, FIRE_HD)
            crystal_hd(p, 42, 54, 60, 30, 7.2, FIRE_HD)
            crystal_hd(p, 31, 58, 88, 50, 10.0, FIRE_HD)
            foot = c.ellipse(32, 57, 20, 4.4)
            p.part(foot, WARMSTONE_HD, 'ray', base=0, sep=True)
            p.part(c.box(12, 55.5, 52, 57.5) & foot, SILVER_HD, 'flat', base=0, sep=True, rim=False, tex='metal')
            fl = S.flame(c, 52, 22, 8, 14, 0.5)
            p.part(fl, FIRE_HD, 'vgrad', base=0, sep=True, rim=False, bands=((0.3, 2), (0.6, 1), (9, 0)))
        grain_hd(p, foot, WARMSTONE_HD)
    return draw


# ----------------------------------------------------------------------------- stones
def formation_stone_hd(p):
    """Formation stone: a palm-sized disc of grey stone with two rings of jade inlaid, the eight trigram studs
    between them and a bead of Qi at the centre."""
    c = p.c
    cx, cy = 32, 35
    side = c.ellipse(cx, cy + 5, 26, 19)
    p.part(side, STONE_HD, 'flat', base=-2, sep=False)
    disc = c.ellipse(cx, cy, 26, 19)
    p.part(disc, STONE_HD, 'ray', base=0, sep=True)
    grain_hd(p, disc, STONE_HD)
    for (r, ry, w) in ((19, 13.6, 2.4), (10, 7.2, 2.0)):
        ring = c.ring(cx, cy, r, w, ry) & disc
        p.part(ring, JADE_HD, 'flat', base=0, sep=True, rim=False)
        p.decal(ring & c.sector(cx, cy, 30, 100, 200, 30), JADE_HD, 1)
    for k in range(8):
        a = k * math.pi / 4
        x, y = cx + math.cos(a) * 14.6, cy + math.sin(a) * 10.4
        p.part(c.circle(x, y, 1.9), JADE_HD, 'sphere', base=1, sep=True, rim=False)
    p.part(c.circle(cx, cy, 3.2), QI_HD, 'sphere', base=1, sep=True, spec=(cx - 1.2, cy - 1.4))


def guardian_stone_hd(p):
    """Guardian stone: the heart-stone of a Stone Guardian, a small stele on its plinth with a shield carved into
    it and jade set in the shield, moss at its foot."""
    c = p.c
    base = c.poly([(10, 58), (14, 50), (50, 50), (54, 58)])
    p.part(base, STONE_HD, 'ray', base=0, sep=False)
    grain_hd(p, base, STONE_HD, 4)
    stele = c.poly([(16, 52), (16, 14), (20, 8), (44, 8), (48, 14), (48, 52)])
    p.part(stele, STONE_HD, 'ray', base=0, sep=True)
    grain_hd(p, stele, STONE_HD)
    p.decal(lmask(p, [(17, 15), (21, 9)]) & stele, STONE_HD, 2)
    sh = c.poly([(22, 18), (42, 18), (42, 30), (32, 44), (22, 30)])
    p.decal(sh, STONE_HD, -2)
    shin = c.poly([(25, 21), (39, 21), (39, 29.6), (32, 39.6), (25, 29.6)])
    p.part(shin, JADE_HD, 'ray', base=0, sep=True, tex='jade')
    p.decal(c.box(31.5, 22, 32.5, 36) & shin, JADE_HD, -2)
    p.decal(c.box(26, 25, 38, 26) & shin, JADE_HD, -2)
    moss = c.ellipse(18, 50, 7, 3) | c.ellipse(46, 51, 6, 2.6)
    p.part(moss, MOSS_HD, 'ray', base=0, sep=True, rim=False)


def terracotta_shard_hd(p):
    """Terracotta shard: a broken piece of a Terracotta Warden's lamellar armour, the clay's thickness on its broken
    edge, the narrow lamellae laced in curving rows, a trace of vermilion paint left on them, a crack."""
    c = p.c
    X, Y = XY(p)
    m = c.poly([(8, 18), (20, 16), (32, 15), (44, 15), (55, 16), (53, 24), (47, 27), (50, 35), (42, 39), (39, 49), (31, 46), (25, 56), (19, 49), (12, 51),
                (10, 40), (7, 32), (11, 26)])
    ox, oy = max(1, int(round(2 * p.s))), max(1, int(round(4 * p.s)))
    side = (move(m, ox, oy) | move(m, 0, oy) | move(m, ox, 0)) & ~m
    p.part(side, TERRACOTTA_HD, 'flat', base=-2, sep=False, rim=False)
    p.part(m, TERRACOTTA_HD, 'ray', base=0, sep=True, tex='clay')
    paint = (c.ellipse(19, 28, 9, 5.2) | c.ellipse(28, 37, 5.2, 3.2)) & erode4(m)
    p.part(paint, VERMILION_HD, 'ray_soft', base=0, sep=False, rim=False)
    # the lamellae: rows that curve round the body, each plate with a lit corner and a dark lace line
    cx, cy = 32.0, -48.0
    u = np.arctan2(X - cx, Y - cy)
    v = np.hypot(X - cx, Y - cy)
    v0, pitch = 68.0, 12.0
    rows = m & (v >= v0)
    row_i = np.floor((v - v0) / pitch)
    du = 8.8 / (v0 + pitch * 0.5)
    col_i = np.floor(u / du + 0.5 * (row_i % 2))
    lines = (rows & (row_i != np.floor((shift(v, 0, 1) - v0) / pitch))) | (rows & (col_i != shift(col_i, 1, 0)))
    lines &= erode4(m)
    corner = rows & (row_i != np.floor((shift(v, 0, -1) - v0) / pitch)) & (col_i != shift(col_i, -1, 0)) & erode4(m)
    for mat, sel in ((TERRACOTTA_HD, ~paint), (VERMILION_HD, paint)):
        p.decal(lines & sel, mat, -2)
        p.decal(corner & sel & ~lines, mat, 2)
    hem = m & (v < v0)
    p.decal(hem & erode4(m) & (v >= v0 - 4.4) & (v < v0 - 1.6) & (np.floor(u / 0.09) % 3 != 2) & (X < 40), VERMILION_HD, 0)
    p.decal(lmask(p, [(50, 28), (42, 32), (38, 38), (40, 44)]) & erode4(m), TERRACOTTA_HD, -3)
    p.glow('#F58A3A', 0.45)


def star_shard_hd(p):
    """Star shard: a sharp chip of fallen starlight broken into three facets, the light caught inside it."""
    c = p.c
    A, B, C_, D = (51, 6), (54, 27), (41, 48), (26, 58)
    E, F, G, H = (21, 51), (10, 51), (11, 34), (25, 16)
    P = (33, 32)
    m = c.poly([A, B, C_, D, E, F, G, H])
    p.part(m, STARLIGHT_HD, 'flat', base=-2, sep=False)
    top = c.poly([H, A, P, G]) & m
    right = c.poly([A, B, C_, P]) & m
    low = m & ~top & ~right
    p.decal(low, STARLIGHT_HD, -1)
    p.decal(low & c.poly([G, P, (28, 44), (16, 44)]), STARLIGHT_HD, 0)
    p.decal(right, STARLIGHT_HD, 0)
    p.decal(right & c.poly([A, (52, 20), (40, 36), P]), STARLIGHT_HD, 1)
    p.decal(top, STARLIGHT_HD, 1)
    p.decal(top & c.poly([H, (40, 14), P, (20, 28)]), STARLIGHT_HD, 2)
    throughlit_hd(p, right | low, STARLIGHT_HD)
    p.decal(lmask(p, [(A[0], A[1] + 1), (32, 31)]) & m, WHITE, 0)
    p.decal(lmask(p, [(32, 32), (14, 36)]) & m, STARLIGHT_HD, 3)
    p.decal(lmask(p, [(34, 34), (40, 46)]) & m, STARLIGHT_HD, -2)
    p.sparkle(26, 44, 1)
    p.glow(STAR_GLOW, GLOW_STRENGTH['sovereign'])


def sage_crystal_hd(p):
    """Sage Crystal (currency): a clear cut crystal with warm gold light burning at its core, lit through."""
    c = p.c
    cx, cy = 32, 33
    m = gem_hd(p, cx, cy, 23, 25, CLEAR_HD, table=0.5)
    tab = c.poly([(cx - 23 * 0.42 * 0.5, cy - 12.5), (cx + 23 * 0.42 * 0.5, cy - 12.5), (cx + 11.5, cy - 12.5 * 0.42), (cx + 11.5, cy + 12.5 * 0.42),
                  (cx + 23 * 0.42 * 0.5, cy + 12.5), (cx - 23 * 0.42 * 0.5, cy + 12.5), (cx - 11.5, cy + 12.5 * 0.42), (cx - 11.5, cy - 12.5 * 0.42)])
    p.decal(tab, STARLIGHT_HD, -1)
    p.decal(erode4(tab), STARLIGHT_HD, 0)
    p.decal(c.ellipse(cx, cy, 5.2, 6.0) & tab, STARLIGHT_HD, 2)
    p.decal(c.ellipse(cx, cy, 2.4, 3.0) & tab, WHITE, 0)
    for (x, y) in ((24, 48), (40, 48), (48, 38), (16, 38)):
        p.decal(c.circle(x, y, 1.4) & m, STARLIGHT_HD, -1)
    p.decal(c.circle(cx - 6, cy - 9, 1.4) & tab, WHITE, 0)
    p.sparkle(54, 10, 2)
    p.glow(STAR_GLOW, 1.0)


def star_jade_hd(p):
    """Star Jade (currency): a polished bi disc of deep jade, a star of starlight inlaid round its hole."""
    c = p.c
    cx, cy = 32, 31
    side = c.ellipse(cx, cy + 4, 24, 22)
    p.part(side, DEEP_JADE_HD, 'flat', base=-3, sep=False)
    top = c.ellipse(cx, cy, 24, 22)
    p.part(top, DEEP_JADE_HD, 'sphere', base=0, sep=True, cx=25, cy=23, rx=30, ry=28, tex='jade')
    pts = []
    for k in range(8):
        a = math.radians(90 - k * 45)
        r = 18.0 if k % 2 == 0 else 8.8
        pts.append((cx + math.cos(a) * r, cy - math.sin(a) * r * 0.93))
    star = c.poly(pts) & erode4(top)
    p.part(star, STARLIGHT_HD, 'ray', base=0, sep=True, tex='glass', bands=((0.18, 2), (0.5, 1), (0.8, 0), (9, -1)))
    hole = c.ellipse(cx, cy, 5.2, 5.0)
    p.decal(dilate4(hole) & ~hole, DEEP_JADE_HD, -3)
    p.erase(hole)
    p.decal(c.arc(cx, cy, 22, 2.2, 105, 165, 20) & top, DEEP_JADE_HD, 3)
    p.glow(STAR_GLOW, 0.5)


def orbit_stone_chip_hd(p):
    """Orbit stone chip: a chip of the Orbit Ruins' pale grey-blue stone, one broken-off pebble still circling it on
    a thin arc that passes behind and in front."""
    c = p.c
    A, B, C_, D, E, F, G = (14, 25), (27, 17), (44, 20), (51, 31), (43, 45), (26, 48), (11, 39)
    ring, v = tilted_ring(p, 31, 33, 27, 9.6, 26, 1.6)
    m = c.poly([A, B, C_, D, E, F, G])
    p.part(ring & (v < 0) & ~m, MIST_HD, 'flat', base=-1, sep=False, rim=False)
    rock_hd(p, [A, B, C_, D, E, F, G], ORBIT_HD, top=[A, B, C_, D, (39, 30), (23, 32)], cracks=[[(30, 34), (32, 40), (28, 46)]])
    p.decal((lmask(p, [(18, 24), (24, 20)]) | c.box(28, 18, 31, 19)) & m, ORBIT_HD, 3)
    p.part(ring & (v >= 0), MIST_HD, 'flat', base=1, sep=True, rim=False)
    pebble = c.circle(54.5, 24, 4.6)
    p.part(pebble, ORBIT_HD, 'sphere', base=0, sep=True, spec=(52.5, 22))
    p.glow('#AFC9D1', 0.4)


# ----------------------------------------------------------------------------- cores
def jade_core_hd(p):
    """Jade core: a sentinel's core of clear jade, light moving inside it in a slow swirl."""
    core_hd(p, 32, 32, 21, JADE_HD, heart=mk_round(p.c, 33, 33, 6.5), swirl=True)


def pebble_core_hd(p):
    """Pebble core: a Pebble Imp's tiny earth core, a stone ball cracked through, the cracks lit gold from inside."""
    c = p.c
    m = c.circle(32, 33, 20)
    p.part(m, WARMSTONE_HD, 'sphere', base=0, sep=False, cx=32, cy=33, rx=20, ry=20, spec=(23, 24))
    grain_hd(p, m, WARMSTONE_HD, 1)
    inner = erode4(m)
    cr = lmask(p, [(18, 27), (26, 33), (24, 41), (32, 47)]) | lmask(p, [(26, 33), (38, 29), (44, 35)]) | lmask(p, [(38, 29), (40, 20)])
    p.decal(dilate4(cr) & inner, WARMSTONE_HD, -3)
    p.decal(cr & inner, GOLD_HD, 0)
    p.decal((lmask(p, [(26, 34), (24, 40)]) | lmask(p, [(30, 31), (38, 29)])) & inner, GOLD_HD, 2)


def serpent_core_hd(p):
    """Serpent core: the Riverbed Serpent's core, a green sphere with a slit-pupilled yellow eye looking out of it and
    a coil of scales round its far side."""
    c = p.c
    m = core_hd(p, 32, 32, 21, SERPENT_HD, spec=True)
    iris = c.ellipse(32, 32, 9.5, 14)
    p.part(iris & m, YELLOW_HD, 'ray', base=0, sep=True, rim=False)
    p.decal(c.ellipse(30, 28, 3.6, 4.2) & iris, YELLOW_HD, 2)
    p.part(c.ellipse(32, 32, 3.0, 12.5) & m, INK_HD, 'flat', base=0, sep=False, rim=False)
    p.decal(c.ellipse(31, 26, 1.2, 2.0), M('paper'), 1)
    p.decal(c.ring(32, 32, 19.5, 2.0) & c.sector(32, 32, 24, 200, 340) & m, SERPENT_HD, -2)


def sentinel_core_hd(p):
    """Sentinel core: a River Sentinel's heart-stone, a river pebble polished to aquamarine, water turning inside."""
    c = p.c
    m = core_hd(p, 32, 32, 22, SENTINEL_HD, spec=True)
    p.decal(c.arc(32, 32, 12, 2.8, 20, 240) & m, SENTINEL_HD, 2)
    p.decal(c.arc(34, 36, 6, 2.4, 190, 50) & m, SENTINEL_HD, 2)
    p.decal(c.arc(32, 32, 12, 1.2, 60, 200) & m, SENTINEL_HD, 3)
    p.decal(c.ellipse(23, 21, 4.8, 3.2) & m, SENTINEL_HD, 3)
    p.glow('#74D2D0', GLOW_STRENGTH['spirit'])


CORE_TIERS = {
    # rank tier: the sphere's radius, the heart's half-size, the form that marks the tier, the aura from Mystic up
    'low': dict(r=13.0, s=5.4, band=False, swirl=False, coil=False, sparkle=False, glow=None),
    'mid': dict(r=15.5, s=6.0, band=True, swirl=False, coil=False, sparkle=False, glow=None),
    'high': dict(r=18.0, s=6.8, band=False, swirl=True, coil=False, sparkle=False, glow=GLOW_STRENGTH['mystic']),
    'peak': dict(r=19.5, s=7.6, band=False, swirl=True, coil=True, sparkle=True, glow=GLOW_STRENGTH['spirit']),
}


def make_beast_core_hd(el, tier):
    """A beast core: a sphere of its element with a bright heart in the element's shape; by rank tier a larger
    sphere, then a band round its middle, a swirl of light inside, a coil of light round it and a glint."""
    def draw(p):
        T = CORE_TIERS[tier]
        mat = M(_CORE_RAMP[el], 'gem')
        cx, cy = 32, 33
        core_hd(p, cx, cy, T['r'], mat, heart=CORE_MARKS[el](p.c, cx + 0.5, cy + 0.5, T['s']), band=T['band'], swirl=T['swirl'], coil=T['coil'])
        if T['sparkle']:
            p.sparkle(cx + T['r'] * 0.9, cy - T['r'] * 0.95, 2)
        if T['glow']:
            p.glow(_CORE_GLOW[el], T['glow'])
    return draw


# ----------------------------------------------------------------------------- essence salts: a heap in a footed dish
ES_TIERS_HD = {
    'cinnabar': dict(salt=mat7(ES_VERMILION, 'matte'), dish=WARMSTONE_HD, rim=None, crystals=0, glow=None),
    'verdigris': dict(salt=mat7(ES_VERDIGRIS, 'matte'), dish=WARMSTONE_HD, rim=BRONZE_HD, crystals=0, glow=None),
    'azurite': dict(salt=mat7(ES_AZURITE, 'gem'), dish=BRONZE_HD, rim=None, crystals=2, glow=None),
    'pearl': dict(salt=mat7(ES_PEARL, 'gem'), dish=LACQUER_HD, rim=SILVER_HD, crystals=2, glow=('#F8D2E0', 0.5)),
    'amethyst': dict(salt=mat7(ES_AMETHYST, 'gem'), dish=LACQUER_HD, rim=GOLD_HD, crystals=3, glow=('#B18DE2', 0.7)),
    'star': dict(salt=mat7(ES_STARSALT, 'matte'), dish=GOLD_HD, rim=None, crystals=0, glow=('#F3E3A6', 0.85)),
}


def es_dish_hd(p, T):
    """The shallow footed dish: foot, outer wall, lip and the dark well the salt sits in."""
    c = p.c
    dish, rim = T['dish'], T['rim'] or T['dish']
    dtex, rtex = TEX.get(dish.kind), TEX.get(rim.kind)
    foot = c.ellipse(32, 55.2, 13, 3.6)
    p.part(foot, dish, 'ray', base=-1, sep=False, tex=dtex)
    wall = c.ellipse(32, 45, 26, 10.4) & c.box(0, 44, 64, 64)
    p.part(wall, dish, 'ray', base=0, sep=True, tex=dtex)
    lip = c.ellipse(32, 44, 26, 6.8)
    p.part(lip, rim, 'ray', base=1, sep=True, tex=rtex)
    well = c.ellipse(32, 44, 22, 4.6)
    p.part(well, dish, 'flat', base=-2 if dish is not LACQUER_HD else -3, sep=True, rim=False)
    p.decal(well & c.box(0, 45, 64, 64), dish, -3)
    return well


def es_heap_hd(p, well, top=14.0):
    """A cone of salt with a rounded crown, its edge nicked and bumped by single grains."""
    c = p.c
    X, Y = XY(p)
    xi, yi = np.floor(X).astype(int), np.floor(Y).astype(int)
    half = 1.6 + (Y - top) * 0.7
    cone = (np.abs(X - 32) <= half) & (Y >= top) & (np.abs(X - 32) <= 22.4)
    cone &= c.ellipse(32, top + 11, 13, 11) | (Y > top + 8)
    edge = cone & ~erode4(cone) & (Y < 42)
    cone &= ~(edge & ((xi * 7 + yi * 3) % 5 == 0))
    bump = dilate4(cone) & ~cone & (Y < 41) & (Y > top + 4) & ((xi * 5 + yi * 11) % 6 == 0)
    return (cone | bump) & (well | (Y < 45))


def es_grains_hd(p, heap, salt):
    """Shade the heap round, then break it into grains: each grain a step lighter or darker than its neighbours, a
    bright facet at its top-left corner and a dark one at its lower right."""
    c = p.c
    p.part(heap, salt, 'flat', base=0, sep=True)
    idx = c.shade_index(heap, 7, 'sphere', 3, cx=28 * p.s, cy=30 * p.s, rx=24 * p.s, ry=24 * p.s, bands=BANDS['sphere'])
    cell = max(2, int(round(4 * p.s)))
    row = c.yi // cell
    sx = c.xi + (row % 2) * (cell // 2)
    col = sx // cell
    lx, ly = sx % cell, c.yi % cell
    jitter = np.array([0, 1, 0, -1, 0, -1, 1])[(col * 3 + row * 5 + (col * row) % 4) % 7]
    idx = idx + jitter
    idx = np.where((ly == 0) & (lx == 0), idx + 1, idx)
    idx = np.where((ly == cell - 1) & (lx == cell - 1), idx - 1, idx)
    idx = np.clip(idx, 0, 6)
    c.rgb[heap] = np.array(salt.c, np.uint8)[idx[heap]]


def make_salt_hd(tier):
    def draw(p):
        c = p.c
        T = ES_TIERS_HD[tier]
        salt = T['salt']
        well = es_dish_hd(p, T)
        heap = es_heap_hd(p, well)
        es_grains_hd(p, heap, salt)
        for (bx, by, ang, L, w) in [(31, 24, 94, 20, 4.8), (42, 30, 60, 14, 4.0), (20, 32, 124, 14, 3.8)][:T['crystals']]:
            crystal_hd(p, bx, by, ang, L, w, salt)
        p.decal(c.pts([(26, 30), (36, 28), (20, 38), (42, 36)]), salt, 3)
        if tier == 'star':
            p.decal(c.pts([(24, 32), (34, 26), (40, 36), (18, 40), (30, 38), (46, 42), (28, 22)]), GOLD_HD, 0)
            p.decal(c.pts([(32, 24), (36, 40)]), M('paper'), 2)
            p.sparkle(50, 14, 2)
        if T['glow']:
            p.glow(*T['glow'])
    return draw


# ----------------------------------------------------------------------------- the Ashen Reach: ash and an ember
def cinder_ash_hd(p):
    """Cinder ash: a small heap of cold grey ash, three orange embers still alive in it."""
    c = p.c
    heap = c.poly([(6, 55), (12, 49), (19, 44), (25, 39), (30, 36), (35, 37), (41, 41), (48, 47), (57, 55)]) | c.ellipse(32, 53, 26, 5.2)
    heap &= c.box(0, 0, 64, 57)
    p.part(heap, ASH_HD, 'sphere', base=0, sep=False, cx=26, cy=42, rx=32, ry=20, rim=False)
    inner = erode4(heap)
    p.decal(lmask(p, [(38, 42), (44, 48), (50, 52)]) & inner, ASH_HD, -1)
    for (x, y) in ((16, 50), (24, 54), (34, 54), (44, 54), (12, 54), (48, 50), (20, 46), (40, 44)):
        p.decal(c.circle(x, y, 1.1) & inner, ASH_HD, -2)
    for (x, y) in ((18, 44), (26, 40), (14, 48), (32, 40), (10, 52), (22, 48), (36, 44)):
        p.decal(c.circle(x, y, 0.9) & inner, ASH_HD, 2)
    hearts = c.box(28, 46, 33, 49) | c.box(40, 50, 43.5, 52) | c.box(18, 52, 21.5, 54)
    p.decal(dilate4(dilate4(hearts)) & heap & ~hearts, EMBER_HD, -2)
    p.decal(dilate4(hearts) & heap & ~hearts, EMBER_HD, -1)
    p.decal(hearts, EMBER_HD, 1)
    p.decal(c.box(29, 46, 31, 47) | c.box(40, 50, 41.5, 51), EMBER_HD, 3)
    p.glow('#F58A3A', 0.45)


def pyre_ember_hd(p):
    """Pyre ember: one coal lifted out of an Ashborn pyre, a crust of char cracked open on its orange-red core with
    a yellow heart, a tongue of flame standing on it."""
    c = p.c
    lump = c.poly([(13, 41), (17, 30), (27, 25), (39, 26), (50, 33), (53, 44), (46, 55), (31, 58), (19, 53)])
    p.part(lump, CHAR_HD, 'ray', base=0, sep=False, bands=((0.3, 1), (0.6, 0), (9, -1)))
    core = erode4(erode4(lump)) & ~c.poly([(36, 48), (49, 36), (54, 54), (32, 62)]) & ~c.poly([(12, 48), (18, 50), (26, 60), (10, 60)])
    core &= ~(c.ellipse(39, 32, 5.2, 3.2) | c.ellipse(20, 43, 4.0, 2.8))
    p.part(core, EMBER_HD, 'sphere', base=0, sep=True, cx=27, cy=39, rx=18, ry=14, rim=False)
    p.decal(c.ellipse(28, 40, 8.0, 6.0) & core, EMBER_HD, 1)
    p.decal(c.ellipse(26, 39, 4.4, 3.2) & core, EMBER_HD, 2)
    p.decal(c.ellipse(25, 38, 2.0, 1.4) & core, WHITE, 0)
    for pts in ([(42, 40), (48, 46), (46, 52)], [(16, 46), (22, 52)], [(38, 30), (42, 34)]):
        p.decal(lmask(p, pts) & lump & ~core, EMBER_HD, 1)
    p.decal(c.pts([(46, 48), (20, 50)]) & lump, EMBER_HD, 2)
    fl = S.flame(c, 29, 27, 12, 21, 1.4)
    p.part(fl & ~lump, FIRE_HD, 'vgrad', base=0, sep=True, rim=False, bands=((0.3, -1), (0.62, 0), (9, 1)))
    p.part(S.flame(c, 29, 27, 5.6, 11, 0.6) & ~lump, FIRE_HD, 'flat', base=2, sep=False, rim=False)
    p.glow('#F58A3A', GLOW_STRENGTH['will'])


# ----------------------------------------------------------------------------- the family's table
# The ores by grade, then the Qi stones and fuel, the stones, the cores, the Act II and III materials, the currencies,
# the salts and the beast cores: one drawing each from the templates above and the tables they read.
ORES_HD = [('copper_ore', ore_copper_hd), ('riverstone', ore_riverstone_hd), ('jadeiron', ore_jadeiron_hd), ('cloudsteel_ore', ore_cloudsteel_hd),
           ('mystic_ore', ore_mystic_hd), ('stormsteel_ore', ore_stormsteel_hd), ('sunglass_ore', ore_sunglass_hd), ('driftglass', driftglass_hd)]
ONE_OFFS_HD = [('spirit_stone_shard', spirit_stone_shard_hd), ('refining_essence', refining_essence_hd),
               ('formation_stone', formation_stone_hd), ('guardian_stone', guardian_stone_hd),
               ('pebble_core', pebble_core_hd), ('serpent_core', serpent_core_hd), ('jade_core', jade_core_hd), ('sentinel_core', sentinel_core_hd),
               ('terracotta_shard', terracotta_shard_hd), ('comet_iron', comet_iron_hd), ('star_shard', star_shard_hd), ('orbit_stone_chip', orbit_stone_chip_hd),
               ('cinder_ash', cinder_ash_hd), ('pyre_ember', pyre_ember_hd), ('sage_crystal', sage_crystal_hd), ('star_jade', star_jade_hd)]
MINERALS_HD = (ORES_HD
               + [('spirit_stone_' + lv, make_spirit_stone_hd(lv)) for lv in SPIRIT_STONES_HD]
               + [('fuel_crystal_' + lv, make_fuel_crystal_hd(lv)) for lv in ('low', 'mid')]
               + ONE_OFFS_HD
               + [(tier + '_salt', make_salt_hd(tier)) for tier in ES_TIERS_HD]
               + [('%s_core_%s' % (el, tier), make_beast_core_hd(el, tier)) for el in _CORE_RAMP for tier in CORE_TIERS])

for _id, _draw in MINERALS_HD:
    register(FAM, _id, _draw, GROUP)
    hd(_id, _draw)
