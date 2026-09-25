"""Thousand-eye toad - FIELD BOSS of Mirrorwater Lake (Toad's Hollow, Azure Expanse): a lake
spirit-toad that has swallowed centuries of reflections (Water / Soul).

View: side, facing right (cell 256, 128 art px).  A huge squat toad, ~90 art px long and
~60 tall with its lily crown.  The body sits a little left of the anchor so the slam wave
has room in front of the snout.
Parts, back to front: far legs (dark), body (fat rump + head + blunt snout + parotoid ridge
+ eye mound as one form, flat belly on the ground), pearl belly and throat, warts, crown of
water-lily pads with lotus buds and an open lotus, throat sac, heavy lower lip and wide
mouth, the main head eye (violet iris) under a heavy brow, then the signature: dozens of
round mirror eyes of different sizes over the back and flanks (silver-white sclera, dark
pupils, a few always half-lidded), stamped crisp and unrotated; near hind leg (thick Z
fold via ``px.ik2``) with two more eyes on the thigh, near foreleg.
Idle: breathing while blinks roll over the back from rump to head.  Walk: heavy
hop-crawl.  Windup: the throat sac swells huge and every back eye opens wide and glows
violet (long, held tell).  Attack: leaps and belly-slams (hit frame 1) - a wall of lake
water bursts forward with splashes and a ripple ring.  Hurt: every eye squeezes shut.
Death: the eyes close one by one while it deflates and sinks into the lake, fading.
"""
import math

import numpy as np

import helpers_batch_b as hb
import pixel as px

SPEC = {
    "id": "thousand_eye_toad",
    "cell": 256,
    "anchor": [128, 224],
    "flying": False,
    "hit_frame": 1,
    "airborne": [["walk", 2], ["attack", 0]],
}

# ---- palette: lake-blue/indigo hide, pearl belly, silver mirror eyes, lily green, lotus pink --
SKIN = px.material("tet_skin", "#6cb6cc", "#3b6ca8", "#35468b", "#2b2562", outline="#0b0a1f",
                   thresholds=(0.93, 0.55, 0.2))
BELLY = px.material("tet_belly", "#fbfaf3", "#e2e0ec", "#b4b0d3", "#8079ab", outline="#120f29")
LILY = px.material("tet_lily", "#b8e38c", "#66ad6a", "#3a7b62", "#25524f", outline="#08181a")
LOTUS = px.material("tet_lotus", "#fff0f5", "#f5a6c3", "#d56d9a", "#9d4577", outline="#230a1c")
WATER = px.WATER_FX
FOAM = BELLY  # foam and bubbles reuse the pearl ramp
MOUTH_IN = px.rgb("#2a1435")
WART = SKIN.step(-1)
# mirror eyes (flat colours): rim, sclera, silver shadow, pupil, glint, head-eye iris
RIM = px.rgb("#16122f")
WHITE = px.rgb("#eef0fb")
SILVER = px.rgb("#a9acd6")
PUPIL = px.rgb("#1d1846")
GLINT = px.rgb("#ffffff")
IRIS = px.rgb("#8f68d6")
# soul glow (windup)
GLOW_W = px.rgb("#fbf3ff")
GLOW_V = px.rgb("#d2b1ff")
GLOW_RIM = px.rgb("#7b4fd0")
HALO = px.rgb("#b58af2")

# ---- poses --------------------------------------------------------------------------------
# bx, by   body offset          rot  pitch (deg, + = nose up)   sq  squash about the ground
# sx       horizontal stretch   breathe  body swell 0..1          puff  throat sac 0..1
# jaw      mouth gape 0..1      hind  None = sitting | (ankle dx, dy, toe dx, dy) from the hip
# front    None | (hand dx, dy) from the shoulder
# eyes     back-eye mode: blink | open | rise (wide from the rump forward up to ``glow``) |
#          wide | squeeze | dying (the ``closed`` fraction shut, one by one)
# blink    blink-wave phase (idle)   head  main eye: open|angry|squeeze|half|closed
# glow     0..1 soul glow         crown  lotus sway phase
# sink     px sunk into the lake (death)   fade  opacity
# slam     slam FX life 0..1 (None = off)   hit  impact spark   splash  hop splash life
DEFAULTS = dict(bx=0, by=0, rot=0, sq=1.0, sx=1.0, breathe=0.0, puff=0.12, jaw=0.0, hind=None, front=None,
                eyes="blink", blink=0, head="open", glow=0.0, closed=0.0, crown=0.0, sink=0.0, fade=1.0,
                slam=None, hit=False, splash=None)

POSE = px.poses(DEFAULTS, {
    "idle": [  # slow breathing, throat flutter, a blink wave rolls over the back
        dict(blink=0, crown=0.0),
        dict(blink=1, crown=1.0, breathe=0.4, puff=0.2),
        dict(blink=2, crown=2.0, breathe=0.7, puff=0.26),
        dict(blink=3, crown=3.0, breathe=0.3, puff=0.16),
    ],
    "walk": [  # heavy hop-crawl: squat, shove, hang, catch on the hands, splat, settle
        dict(sq=0.95, eyes="open", crown=0.0),
        dict(bx=1, by=-1, rot=7, hind=(-11.0, 11.0, 8.0, 13.0), front=(8.0, 14.0), eyes="open", crown=1.0),
        dict(bx=3, by=-6, rot=4, hind=(-14.0, 9.0, -2.0, 12.0), front=(10.0, 13.0), eyes="open", crown=2.0),
        dict(bx=4, by=-2, rot=-5, hind=(-9.0, 10.0, 7.0, 11.0), front=(8.0, 16.0), eyes="open", crown=3.0),
        dict(bx=4, sq=0.9, eyes="open", crown=4.0, splash=0.25),
        dict(bx=2, sq=0.97, eyes="open", crown=5.0, splash=0.6),
    ],
    "windup": [  # the throat sac swells, the back eyes open wide and glow violet - held
        dict(bx=-1, rot=3, sq=1.01, puff=0.5, eyes="rise", glow=0.4, head="angry", crown=1.0),
        dict(bx=-2, rot=5, sq=1.03, puff=0.85, eyes="rise", glow=0.8, head="angry", crown=2.0, breathe=0.5),
        dict(bx=-2, rot=6, sq=1.04, puff=1.0, eyes="wide", glow=1.0, head="angry", crown=2.5, breathe=0.8),
    ],
    "attack": [  # leap, crushing belly-slam (hit), water wall rolls forward, settle
        dict(bx=0, by=-12, rot=-3, sq=1.04, puff=0.35, jaw=0.6, hind=(-10.0, 14.0, -1.0, 18.0), front=(7.0, 16.0),
             eyes="wide", glow=0.6, head="angry", crown=3.0),
        dict(bx=1, sq=0.84, sx=1.06, puff=0.0, jaw=0.9, eyes="wide", glow=0.3, head="angry", crown=4.0, slam=0.3,
             hit=True),
        dict(bx=1, sq=0.93, sx=1.02, puff=0.0, jaw=0.4, eyes="open", head="angry", crown=5.0, slam=0.65),
        dict(bx=1, sq=0.98, puff=0.1, eyes="open", crown=6.0, slam=0.95),
    ],
    "hurt": [  # recoil, every eye squeezed shut
        dict(bx=-4, by=-1, rot=8, jaw=0.5, eyes="squeeze", head="squeeze", puff=0.05, front=(3.0, 16.0)),
        dict(bx=-2, rot=3, sq=0.96, jaw=0.2, eyes="squeeze", head="squeeze", puff=0.08),
    ],
    "death": [  # the eyes close one by one while it deflates and sinks into the lake
        dict(bx=-3, rot=6, jaw=0.5, eyes="dying", closed=0.2, head="squeeze", puff=0.3),
        dict(bx=-3, rot=2, sq=0.95, jaw=0.3, eyes="dying", closed=0.5, head="half", puff=0.12),
        dict(bx=-3, sq=0.9, jaw=0.2, eyes="dying", closed=0.8, head="half", puff=0.0, sink=4.0),
        dict(bx=-3, sq=0.86, eyes="dying", closed=1.0, head="closed", puff=0.0, sink=10.0, fade=0.6),
        dict(bx=-3, sq=0.82, eyes="dying", closed=1.0, head="closed", puff=0.0, sink=17.0, fade=0.3),
    ],
})

# body-local anchor points (relative to the body centre C)
HEAD = (26.0, -6.5)
HIP = (-18.0, 9.0)
SHOULDER = (22.0, 6.0)

# the mirror eyes: (dx, dy) from C in body space, diameter, sleepy (always half-lidded)
BACK_EYES = (
    # along the back line (the big ones bulge out of the silhouette)
    (-32.0, -8.0, 6, False), (-25.0, -14.0, 7, False), (-15.0, -18.5, 11, False), (-3.5, -19.0, 7, True),
    (5.0, -16.0, 6, False),
    # upper flank
    (-33.0, 2.0, 6, False), (-24.5, -2.5, 7, False), (-16.0, -6.5, 6, False), (-7.0, -8.0, 9, False),
    (3.0, -6.5, 6, False), (10.0, -8.0, 6, True),
    # lower flank, above and in front of the thigh
    (-29.5, 9.0, 6, False), (-12.0, 0.0, 6, True), (-1.5, 1.5, 7, False), (8.0, 2.0, 6, False),
    (15.0, -2.5, 6, False),
)
# two more eyes on the near thigh (drawn after it)
THIGH_EYES = ((-16.0, 12.0, 7, False), (-8.0, 17.5, 6, False))


# ---- mirror eye stamps -----------------------------------------------------------------------
_EYE_CACHE = {}


def _pupil(d, look, wide):
    """Pupil pixels as offsets of pixel centres from the eye centre (integers for odd
    diameters, half-integers for even ones)."""
    if d % 2 == 0:
        sx, sy = (look if d >= 8 and not wide else (0, 0))
        return {(x + sx, y + sy) for x in (-0.5, 0.5) for y in (-0.5, 0.5)}
    if wide:  # wide open: a pinpoint pupil in a glowing white
        return {(0.0, 0.0)} if d < 13 else {(x, y) for x in (0.0, 1.0) for y in (0.0, 1.0)}
    sx, sy = (float(look[0]), float(look[1])) if d >= 7 else (0.0, 0.0)
    if d <= 5:
        return {(0.0, 0.0)}
    if d == 7:
        return {(x + sx, y + sy) for x in (0.0, 1.0) for y in (0.0, 1.0)}
    rr = 1 if d < 11 else 2  # 3x3 square, or a 5x5 disc for the biggest eyes
    return {(x + sx, y + sy) for x in range(-rr, rr + 1) for y in range(-rr, rr + 1)
            if not (rr == 2 and abs(x) == 2 and abs(y) == 2)}


def _eye_rows(d, state, look=(0, 0)):
    """ASCII stamp of a round mirror eye of diameter ``d``.

    k rim, w sclera, s silver shadow, p pupil, g glint; l / m / n lid (light / base / deep
    skin), c lid crease; wide eyes use x (glow white), y (glow violet), v (glow rim)."""
    key = (d, state, look)
    if key in _EYE_CACHE:
        return _EYE_CACHE[key]
    R = d / 2.0
    wide = state == "wide"
    pupil = _pupil(d, look, wide)
    rows = []
    for j in range(d):
        row = []
        for i in range(d):
            dx, dy = i + 0.5 - R, j + 0.5 - R
            r = math.hypot(dx, dy)
            if r > R + 0.08:
                row.append(".")
                continue
            rim = r > R - 1.0
            if state in ("closed", "squeeze"):
                # a lidded bump: lit top, shadowed lower rim and a dark crease across it
                crease_y = 0.0 if (d < 7 or abs(dx) < R * 0.5) else -1.0
                if d % 2 == 0:
                    crease_y += 0.5
                if rim:
                    row.append("n" if dy > 0.2 else ("l" if dx + dy < -R * 0.6 else "m"))
                elif abs(dy - crease_y) < 0.5 or (state == "squeeze" and abs(dy) < 1.6 and abs(dx) > R - 2.2):
                    row.append("c")
                else:
                    row.append("l" if dy < crease_y and dx + dy < 0.5 else "m")
                continue
            if rim:
                row.append("v" if wide else "k")
                continue
            if state == "half" and dy < -R * 0.2:  # heavy upper lid
                lowest = dy + 1.0 >= -R * 0.2
                row.append("c" if (lowest and d >= 7) else ("l" if dx + dy < -R * 0.4 else "m"))
                continue
            if (dx, dy) in pupil:
                row.append("p")
            elif dx + dy > R * 0.35:
                row.append("y" if wide else "s")
            else:
                row.append("x" if wide else "w")
        rows.append("".join(row))
    # glint: the top-left-most sclera pixel
    if state in ("open", "wide", "half") and d >= 5:
        best = None
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch in "wx" and (best is None or i + j < best[0]):
                    best = (i + j, i, j)
        if best is not None:
            _, i, j = best
            rows[j] = rows[j][:i] + "g" + rows[j][i + 1:]
    if state == "open" and d >= 9:  # catchlight on the big pupils
        cx = sum(q[0] for q in pupil) / len(pupil) - 1.0
        cy = sum(q[1] for q in pupil) / len(pupil) - 1.0
        i, j = int(round(cx + R - 0.5)), int(round(cy + R - 0.5))
        if 0 <= j < d and 0 <= i < d and rows[j][i] == "p":
            rows[j] = rows[j][:i] + "g" + rows[j][i + 1:]
    _EYE_CACHE[key] = rows
    return rows


EYE_PAL = {"k": RIM, "w": WHITE, "s": SILVER, "p": PUPIL, "g": GLINT, "l": (SKIN, 0), "m": (SKIN, 1),
           "n": (SKIN, 3), "c": RIM, "x": GLOW_W, "y": GLOW_V, "v": GLOW_RIM}


def _stamp_eye(cv, cx, cy, d, state, look=(0, 0), halo=False):
    if state == "wide":
        d = d + 2
    x0, y0 = math.floor(cx - d / 2.0 + 0.5), math.floor(cy - d / 2.0 + 0.5)
    if halo:  # 1 px violet glow ring round a wide eye
        ring = []
        for j in range(-1, d + 1):
            for i in range(-1, d + 1):
                r = math.hypot(i + 0.5 - d / 2.0, j + 0.5 - d / 2.0)
                if d / 2.0 + 0.08 < r <= d / 2.0 + 1.1:
                    ring.append((x0 + i, y0 + j))
        cv.pixels(ring, HALO, name="halo")
        return
    cv.stamp(_eye_rows(d, state, look), x0, y0, EYE_PAL, name="eye")


def _eye_state(p, k, x_rank, sleepy):
    if p.eyes == "blink":  # a wave of blinks rolls from the rump to the head
        if sleepy:
            return "half"
        if px.hash01("tet_blink", k) > 0.72:
            return "open"
        band = min(3, int(x_rank * 4))
        if band == p.blink % 4:
            return "closed"
        if band == (p.blink - 1) % 4:
            return "half"
        return "open"
    if p.eyes == "open":
        return "half" if sleepy else "open"
    if p.eyes == "rise":
        return "wide" if x_rank <= p.glow else ("half" if sleepy else "open")
    if p.eyes == "wide":
        return "wide"
    if p.eyes == "squeeze":
        return "squeeze"
    if p.eyes == "dying":  # one by one, in a scattered order
        order = px.hash01("tet_close", k)
        if order < p.closed:
            return "closed"
        return "half" if sleepy or order < p.closed + 0.2 else "open"
    return "open"


def _look(k):
    return ((-1, 0), (1, 0), (0, -1), (1, 1), (0, 0), (-1, 1))[int(px.hash01("tet_look", k) * 6)]


# ---- head eye (violet iris, horizontal pupil) ---------------------------------------------------
HEAD_EYE = {
    "open": ["..kkkkk..", ".kgwiiik.", "kwwipppik", "kwiipppik", "kwsiiiisk", ".kssiisk.", "..kkkkk.."],
    "half": ["..mmmmm..", ".mllllmm.", "kllllmmmk", "kcccccccc", "kwsipppik", ".kssiisk.", "..kkkkk.."],
    "closed": ["..mmmmm..", ".mllllmm.", "mllllmmmm", "ccllllmcc", ".cccccccn", "..nnnnn..", "........."],
    "squeeze": ["..mmmmm..", ".mlcllmm.", "mllccmmmm", "cccccccc.", "mmmccmmmn", ".nmcmmn..", "..nnnnn.."],
}
HEAD_PAL = dict(EYE_PAL, i=IRIS)


# ---- limbs -------------------------------------------------------------------------------------
def _hind(cv, hip, gl, p, far):
    if p.hind is None:
        ankle = (hip[0] - 5.0 + (3.0 if far else 0.0), gl - 2.8)
        toe = (ankle[0] + 18.0, gl - 1.3)
    else:
        ax, ay, tx, ty = p.hind
        if far:
            ax, tx = ax + 3.0, tx + 3.0
        ankle = (hip[0] + ax, hip[1] + ay)
        toe = (hip[0] + tx, hip[1] + ty)
    knee = px.ik2(hip, ankle, 14.0, 14.0, bend=1 if ankle[0] <= hip[0] + 8 else -1)
    sep = False if far else "deep"
    mid = px.lerp_pt(hip, knee, 0.45)
    ang = math.degrees(math.atan2(-(knee[1] - hip[1]), knee[0] - hip[0]))
    cv.ellipse(mid[0], mid[1], 12.0, 8.0, SKIN, angle=ang, shade="dark" if far else "soft", name="thigh", sep=sep)
    cv.limb([knee, ankle], [5.0, 3.4], SKIN, shade="dark" if far else "two", name="shin", sep=sep)
    cv.limb([ankle, toe], [3.2, 1.7], SKIN, shade="dark" if far else "two", name="foot", sep=sep)
    # webbed toes: pale pads at the tip of the foot
    for (dx, dy, r) in ((1.0, -1.4, 1.6), (3.4, -0.2, 1.4)):
        cv.circle(toe[0] + dx, min(gl - r + 0.1, toe[1] + dy), r, SKIN if far else BELLY,
                  shade="dark" if far else "two", name="toe")


def _front(cv, sh, gl, p, far):
    if p.front is None:
        hand = (sh[0] + 5.5 + (2.5 if far else 0.0), gl - 2.2)
    else:
        hand = (sh[0] + p.front[0] + (2.5 if far else 0.0), sh[1] + p.front[1])
    elbow = px.ik2(sh, hand, 10.5, 10.5, bend=1)
    shade = "dark" if far else "two"
    cv.limb([sh, elbow, hand], [5.6, 4.3, 3.3], SKIN, shade=shade, name="arm", sep=False if far else "deep")
    # splayed fingers with pale tips
    for (a, ln) in ((-8.0, 6.5), (14.0, 5.5)):
        tip = px.polar(hand, a, ln)
        tip = (tip[0], min(tip[1], gl - 1.0))
        cv.limb([hand, tip], [2.0, 1.3], SKIN, shade=shade, name="hand")
        cv.circle(tip[0] + 0.3, min(tip[1], gl - 1.3), 1.3, SKIN if far else BELLY, shade="dark" if far else "two",
                  name="toe")


# ---- crown of lily pads and lotus -------------------------------------------------------------------
def _pad(cv, cx, cy, rx, ry, ang, notch):
    wedge = cv.mask_polygon([(cx, cy), px.polar((cx, cy), ang + notch - 14, rx * 1.4),
                             px.polar((cx, cy), ang + notch + 14, rx * 1.4)])
    cv.ellipse(cx, cy, rx, ry, LILY, angle=ang, shade="soft", name="pad", sep="deep", minus=wedge)


def _bud(cv, base, height, width, lean):
    """A closed lotus bud: a round bulb drawing up to a pointed, slightly leaning tip."""
    bulb = (base[0] + lean * 0.2, base[1] - height * 0.33)
    tip = (base[0] + lean, base[1] - height)
    g = cv.union(cv.geom_ellipse(bulb[0], bulb[1], width, height * 0.34),
                 cv.geom_polygon([(bulb[0] - width * 0.75, bulb[1] - height * 0.12), tip,
                                  (bulb[0] + width * 0.75, bulb[1] - height * 0.12)]))
    cv.draw_geom(g, LOTUS, shade="soft", name="lotus", sep="deep")
    cv.line((math.floor(bulb[0] + 0.5), math.floor(base[1]) - 1), (math.floor(tip[0]), math.floor(tip[1]) + 3),
            LOTUS.shadow, decal=True, clip="lotus", name="lotus")


def _flower(cv, base, sway):
    """An open lotus: petals splayed out to both sides round a pointed centre petal."""
    for a, ln, rx in ((125, 3.0, 3.0), (55, 3.0, 3.0), (168, 3.6, 3.4), (12, 3.6, 3.4)):
        c = px.polar(base, a + sway * 3, ln)
        cv.ellipse(c[0], c[1], rx, 1.5, LOTUS, angle=a + sway * 3, shade="soft", name="lotus", sep="deep")
    _bud(cv, (base[0], base[1] + 0.5), 7.5, 2.3, 0.3 + sway)


def _crown(cv, H, p):
    sw = math.sin(p.crown * 1.4) * 0.8
    _pad(cv, H[0] - 18.0, H[1] - 11.0, 7.0, 2.2, 20, 180)
    _pad(cv, H[0] - 9.0, H[1] - 14.5, 8.5, 2.6, 5, 0)
    _bud(cv, (H[0] - 12.0, H[1] - 15.0), 13.0, 3.2, 1.0 + sw)
    _bud(cv, (H[0] - 19.0, H[1] - 12.5), 8.5, 2.4, -2.0 + sw * 0.7)
    _flower(cv, (H[0] - 5.0, H[1] - 16.0), sw)


# ---- FX --------------------------------------------------------------------------------------------
def _water_wall(fx, C, gy, t):
    """A wall of lake water thrown up in front of the slam: it towers and its lip curls
    forward over an open hollow, then it collapses into foam.  Returns the lip tip."""
    base = gy - 1.0
    h = 38.0 * (1.0 - t) ** 0.9 + 3.0
    xs = C[0] + 36.0 + 6.0 * t  # where the surge leaves the ground behind the crest
    xc = C[0] + 55.0 + 5.0 * t  # crest
    span = xc - xs
    # the water mass: a long back slope, a steep front face under the curl
    fx.polygon([(xs, base), (xs + span * 0.5, base - h * 0.42), (xs + span * 0.85, base - h * 0.84), (xc, base - h),
                (xc + 1.5, base - h * 0.88), (xc + 0.5, base - h * 0.62), (xc + 2.5, base - h * 0.3),
                (xc + 5.0, base)], WATER, shade="soft", name="wave")
    # the lip curling forward and down over the hollow
    tip = (min(120.0, xc + 8.5), base - h * 0.62)
    fx.limb([(xc - 1.0, base - h + 0.5), (xc + 4.0, base - h - 0.6), (xc + 7.5, base - h * 0.86), tip],
            [2.4, 2.0, 1.5, 0.9], WATER, shade="soft", name="wave")
    # foam riding the crest
    fx.limb([(xs + span * 0.72, base - h * 0.74), (xc - 1.0, base - h - 0.6), (xc + 4.0, base - h - 1.8),
             (xc + 7.0, base - h * 0.96)], [0.8, 1.4, 1.3, 0.8], FOAM, shade="soft", name="wave")
    for k in range(3):  # spray thrown off the lip
        q = (min(122.0, tip[0] + 1.5 + k * 1.1), base - h - 2.0 - 3.0 * (1.0 - t) * (1 - k * 0.4) + t * 7.0 * k)
        if q[1] < base - 2.0:
            fx.circle(q[0], q[1], 1.0 if k % 2 else 0.8, WATER, shade="soft", name="drop")
    return tip


def _splash_crown(fx, x, gy, t, size=1.0, seed=0):
    """A crown of water spikes thrown up round a heavy impact, falling back as droplets."""
    base = gy - 1.0
    rise = math.sin(math.pi * min(1.0, t * 1.1))
    for k, a in enumerate((58, 78, 98, 118, 138)):
        a = a + (px.hash01("tet_spl", seed, k) - 0.5) * 12
        ln = (6.0 + 5.0 * px.hash01("tet_spl_l", seed, k)) * size * rise
        root = (x + (k - 2) * 1.6 * size, base)
        top = px.polar(root, a, ln)
        if t < 0.55 and ln > 2.0:
            fx.limb([root, top], [1.4 * size, 0.6], WATER, shade="soft", name="splash")
        drop = px.polar(root, a, ln + 2.0 + 4.0 * t)
        drop = (drop[0], drop[1] + 9.0 * t * t)
        if drop[1] < base - 1.5:
            fx.circle(drop[0], drop[1], 1.0 if k % 2 else 0.8, WATER, shade="soft", name="splash")
    fx.ellipse(x, base - 0.8, (4.0 + 5.0 * t) * size, 1.2, WATER, shade="soft", name="splash")


def _glow_motes(fx, pts, frame):
    for k, (x, y) in enumerate(pts):
        h = px.hash01("tet_mote", k)
        if h > 0.5:
            continue
        mx, my = math.floor(x + (h - 0.25) * 8), math.floor(y - 5 - (frame * 3 + k * 5) % 9)
        fx.pixels([(mx - 1, my), (mx + 1, my), (mx, my - 1), (mx, my + 1)], HALO, name="mote")
        fx.pixel(mx, my, GLOW_W, name="mote")


# ---- draw ------------------------------------------------------------------------------------------
def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    ground = cv.ground
    gl = ground + p.sink  # where the feet rest (they sink with the body)
    C = (cv.gx - 12.0 + p.bx, ground - 25.0 + p.by + p.sink)
    airborne = [action, frame] in SPEC["airborne"]
    cv.snap_ground = not airborne and p.sink == 0
    xf = [px.scale(p.sx, p.sq, (C[0], gl)), px.rotate(p.rot, C)]

    def lp(q):
        return (C[0] + q[0], C[1] + q[1])

    with cv.xform(*xf):
        hip, sh = cv.tp(lp(HIP)), cv.tp(lp(SHOULDER))
    # far legs (behind the body)
    _hind(cv, (hip[0] + 3.5, hip[1] - 2.0), gl, p, far=True)
    _front(cv, (sh[0] + 3.0, sh[1] - 1.5), gl, p, far=True)

    with cv.xform(*xf):
        br = p.breathe
        H = lp(HEAD)
        g = cv.union(cv.geom_ellipse(C[0] - 3.0, C[1] + 1.0 - br * 0.5, 33.0, 25.0 + br * 0.8),
                     cv.geom_ellipse(H[0], H[1], 18.5, 14.0),
                     cv.geom_limb([(H[0] + 4.0, H[1] + 3.5), (H[0] + 16.0, H[1] + 5.5)], [12.5, 7.5]),
                     cv.geom_limb([(H[0] - 14.0, H[1] - 8.5), (H[0] - 4.0, H[1] - 11.5)], [5.5, 4.2]),
                     cv.geom_ellipse(H[0] + 2.0, H[1] - 11.5, 7.0, 6.0),
                     weights=[1.0, 0.85, 0.6, 0.55, 0.7])
        flat = cv.mask_polygon([(C[0] - 60, C[1] + 25.6), (C[0] + 60, C[1] + 25.6), (C[0] + 60, C[1] + 60),
                                (C[0] - 60, C[1] + 60)])
        cv.draw_geom(g, SKIN, name="body", minus=flat)
        # pearl belly and throat
        cv.ellipse(C[0] + 15.0, C[1] + 21.0, 29.0, 9.0, BELLY, shade="two", decal=True, clip="body")
        cv.ellipse(H[0] + 9.0, H[1] + 12.0, 14.0, 5.5, BELLY, shade="two", decal=True, clip="body")
        # a few pale warts on the head and lower flank
        for (wx, wy) in ((H[0] - 9.0, H[1] - 1.0), (H[0] + 9.0, H[1] - 4.0), (C[0] - 31.0, C[1] + 18.0),
                         (H[0] + 15.0, H[1] - 0.5), (C[0] + 2.0, C[1] + 9.0)):
            x, y = math.floor(wx), math.floor(wy)
            cv.pixels([(x, y), (x + 1, y)], WART, name="wart", clip="body", decal=True)
            cv.pixels([(x, y + 1), (x + 1, y + 1)], SKIN.step(1), name="wart", clip="body", decal=True)
        _crown(cv, H, p)
        # throat sac: a pearl balloon swelling under the jaw
        if p.puff > 0.05:
            pr = 2.0 + 14.0 * p.puff
            sc = (H[0] + 7.0 + 5.0 * p.puff, H[1] + 13.0 + 2.0 * p.puff)
            cv.ellipse(sc[0], sc[1], pr * 1.15, pr * 0.9, BELLY, shade="full", name="sac", sep="deep")
            if p.puff > 0.4:  # wet highlight on the stretched skin
                gx_, gy_ = math.floor(sc[0] - pr * 0.55), math.floor(sc[1] - pr * 0.5)
                cv.pixels([(gx_, gy_), (gx_ + 1, gy_), (gx_, gy_ + 1)], GLINT, name="sac")
        # wide down-turned mouth over a heavy lower lip
        corner = (H[0] - 8.0, H[1] + 2.5)
        gape = 7.0 * p.jaw
        if p.jaw > 0.05:
            cv.polygon([(corner[0], corner[1] - 0.5), (H[0] + 8.0, H[1] + 3.5), (H[0] + 23.0, H[1] + 2.5),
                        (H[0] + 22.0, H[1] + 4.5 + gape), (H[0] + 8.0, H[1] + 5.5 + gape * 0.8),
                        (corner[0] + 1.0, corner[1] + 1.5)], px.flat(MOUTH_IN), name="gape")
        cv.limb([corner, (H[0] + 6.0, H[1] + 6.5 + gape * 0.8), (H[0] + 20.0, H[1] + 5.0 + gape)],
                [1.8, 3.4, 2.6], SKIN, shade="soft", name="lip", sep="deep")
        # main head eye under a heavy brow
        head_eye_at = cv.tp((H[0] - 2.5, H[1] - 15.0))
        brow = [(H[0] - 3.5, H[1] - 15.8), (H[0] + 1.5, H[1] - 16.8), (H[0] + 6.5, H[1] - 15.0)]
        if p.head == "angry":
            brow = [(H[0] - 3.5, H[1] - 17.0), (H[0] + 1.5, H[1] - 16.0), (H[0] + 6.5, H[1] - 13.2)]
        eye_spots = [(cv.tp(lp((dx, dy))), d, sleepy) for (dx, dy, d, sleepy) in BACK_EYES]
        thigh_spots = [(cv.tp(lp((dx, dy))), d, sleepy) for (dx, dy, d, sleepy) in THIGH_EYES]
    # the head eye, stamped crisp, then its brow
    ex, ey = math.floor(head_eye_at[0]), math.floor(head_eye_at[1])
    cv.stamp(HEAD_EYE["open" if p.head in ("open", "angry") else p.head], ex, ey, HEAD_PAL, name="eye")
    with cv.xform(*xf):
        cv.limb(brow, [2.0, 1.8, 1.3], SKIN, shade="soft", name="brow", sep="deep")
    if p.head == "angry":  # the heavy lid drops toward the snout: a narrowed glare
        cv.polygon([(ex - 2.0, ey - 2.0), (ex + 11.0, ey - 2.0), (ex + 11.0, ey + 2.5), (ex - 2.0, ey - 0.5)], SKIN,
                   shade="two", clip="eye", name="lid")
        cv.line((ex - 1, ey - 1), (ex + 9, ey + 2), RIM, name="lid")

    # back eyes (stamped unrotated; all halos first so they never cut into an eye)
    xs = [q[0] for q, _, _ in eye_spots]
    xmin, xmax = min(xs), max(xs)
    states = [_eye_state(p, k, (q[0] - xmin) / max(1.0, xmax - xmin), sleepy)
              for k, (q, d, sleepy) in enumerate(eye_spots)]
    for (q, d, _), st in zip(eye_spots, states):
        if st == "wide":
            _stamp_eye(cv, q[0], q[1], d, st, halo=True)
    for k, ((q, d, _), st) in enumerate(zip(eye_spots, states)):
        _stamp_eye(cv, q[0], q[1], d, st, _look(k))

    # near legs in front, with their own eyes
    _hind(cv, hip, gl, p, far=False)
    tstates = [_eye_state(p, 100 + k, 0.15 + 0.2 * k, sleepy) for k, (q, d, sleepy) in enumerate(thigh_spots)]
    for (q, d, _), st in zip(thigh_spots, tstates):
        if st == "wide":
            _stamp_eye(cv, q[0], q[1], d, st, halo=True)
    for k, ((q, d, _), st) in enumerate(zip(thigh_spots, tstates)):
        _stamp_eye(cv, q[0], q[1], d, st, _look(100 + k))
    _front(cv, sh, gl, p, far=False)

    # sinking: the lake swallows everything below the surface
    if p.sink > 0:
        cv.rect(0, cv.gy - 1, cv.w, cv.h - cv.gy + 1, SKIN, erase=True)

    # ---- FX ----
    if p.glow > 0.5:  # soul motes lifting off the glowing back
        motes = cv.layer(above=True, outline=False)
        _glow_motes(motes, [q for q, _, _ in eye_spots], frame)
    if p.slam is not None:
        back = cv.layer(above=False, outline=True)
        hb.ripple(back, C[0] + 10.0, cv.gy + 0.5, 36.0 + 8.0 * p.slam, WATER)
        fx = cv.layer(above=True, outline=True)
        lip = _water_wall(fx, C, cv.gy, p.slam)
        _splash_crown(fx, C[0] - 31.0, cv.gy, min(1.0, p.slam + 0.1), size=1.3, seed=1)
        _splash_crown(fx, C[0] - 4.0, cv.gy, min(1.0, p.slam + 0.15), size=1.0, seed=2)
        if p.hit:
            top = cv.layer(above=True, outline=False)
            px.impact(top, lip[0] - 2.0, lip[1] - 1.0, size=5)
    if p.splash is not None:
        fx = cv.layer(above=True, outline=True)
        _splash_crown(fx, sh[0] + 10.0, cv.gy, p.splash, size=0.7, seed=3)
    if p.sink > 0:
        # rings spread on the surface (their far arc hides behind the sinking body)
        hb.ripple(cv.layer(above=False, outline=True), C[0] + 8.0, cv.gy + 0.5, 40.0 + p.sink * 0.5, WATER)
        fx = cv.layer(above=True, outline=True)
        cols = np.nonzero(cv.filled[cv.gy - 2])[0]
        if len(cols):  # foam where the body breaks the surface
            for x, w in ((cols.min(), 3.0), (cols.max(), 2.5)):
                fx.ellipse(x + 0.5, cv.gy - 2.0, w, 1.3, FOAM, shade="soft", name="foam")
        if p.sink > 8:  # the last breath bubbles up
            for k, (dx, r) in enumerate(((-6.0, 1.4), (5.0, 1.0), (14.0, 1.2))):
                fx.circle(C[0] + dx, cv.gy - 4.0 - k * 2.5 - p.sink * 0.2, r, FOAM, shade="soft", name="bubble")
