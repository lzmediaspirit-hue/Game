"""Void crab - a crab of the Lantern Star Field whose shell is a window onto the void (Space).

View: 3/4 front, turned toward the right (like the mudshell crab).  ~24 art px tall to the
eye tips, ~37 px wide from the far legs to the big claw (cell 128; the geometry is authored
~15% larger and drawn at ``SIZE``).  Also a tameable pet, so it is kept round and bright-eyed.
Parts, back to front: legs (far pair first; black-violet chitin, silver tips), pale violet
underside and mouth, the carapace (a silver-rimmed dome with two short lateral spines) whose
top is a flat black-violet window onto space: a faint nebula swirl and a scatter of stars
inside it, a bright bevel on the lower rim; eye stalks with glowing white-violet eyes, the
small far claw, then the big near claw (black-violet palm with its own little star window,
silver-edged fingers).
Idle: shifts its weight, claws clack.  Walk: sideways scuttle on alternating tripods.
Windup: the big claw rises high and gapes, a faint tear in space shimmers around it (held).
Attack: the claw slams forward and snaps shut on frame 1 with a small rift-flash at the pinch.
Hurt: the shell window flashes white.  Death: tips and flips onto its back, legs curl and the
starfield in the shell fades out to black.
"""
import math

import numpy as np

import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "void_crab",
    "cell": 128,
    "anchor": [64, 112],
    "flying": False,
    "hit_frame": 1,
}

# ---- palette (5 ramps): silver rim, black-violet chitin, pale violet underside, the void
# (flat), glowing eyes; accents: stars, nebula swirl, rift light --------------------------------
SILVER = px.material("vc_silver", "#f6f4ff", "#c6c2e0", "#8e8ab2", "#5b5784", outline="#0b0a1c",
                     thresholds=(0.88, 0.52, 0.18))
CHITIN = px.material("vc_chitin", "#9584cc", "#5a4a94", "#3b2f6c", "#261d48", outline="#0a0717",
                     thresholds=(0.9, 0.55, 0.2))
UNDER = px.material("vc_under", "#d2c8ee", "#a497cc", "#776a9f", "#4f4574", outline="#0a0717")
VOID = px.rgb("#0e0819")
NEB_D = px.rgb("#2a1648")
NEB_M = px.rgb("#5a2a82")
NEB_L = px.rgb("#8a3f96")
NEB_T = px.rgb("#1f4a64")
STAR_W = px.rgb("#ffffff")
STAR_V = px.rgb("#d8c8ff")
STAR_C = px.rgb("#a8ecff")
STAR_G = px.rgb("#ffe6a1")
STAR_DIM = px.rgb("#6a5e8c")
FLASH = px.rgb("#efe6ff")
FLASH_2 = px.rgb("#b9a2f4")
EYE_W = px.rgb("#fcf8ff")
EYE_V = px.rgb("#c4a6ff")
PUPIL = px.rgb("#2a1a52")
RIFT_W = px.rgb("#ffffff")
RIFT_V = px.rgb("#b58cff")
RIFT_D = px.rgb("#5a2aa8")
MOUTH = px.rgb("#2a1a3e")

# ---- poses ------------------------------------------------------------------------------------
# bx, by  body offset        rot  lean of the whole crab (deg) about its feet
# bc      big claw: (dx, dy) palm offset from rest, angle (deg, 90 = up), opening 0..1
# sc      small claw: (dx, dy) hand offset, angle, opening
# lift, slide  per-leg tip lift / x-slide     knees  body dip
# eye     open|angry|squeeze|dead    lean  eye-stalk lean (px)
# tear    space-tear shimmer round the raised claw 0..3     rift  rift-flash (None | 1 hit | 0.5 fading)
# flash   shell window flashes (hurt)     stars  starfield brightness 1 .. 0 (death: fades to black)
# flip    on its back    flail  tipping over    curl  leg curl 0..1    fade  opacity
DEFAULTS = dict(bx=0, by=0, rot=0, bc=(0, 0, 50, 0.25), sc=(0, 0, 125, 0.3), lift=(0,) * 6, slide=(0,) * 6,
                knees=0, eye="open", lean=0, tear=0, rift=None, flash=False, stars=1.0, flip=False, flail=False,
                curl=0.0, fade=1.0, twinkle=0)

A = (1, 0, 1, 0, 1, 0)
B = (0, 1, 0, 1, 0, 1)


def _k(mask, k):
    return tuple(m * k for m in mask)


POSE = px.poses(DEFAULTS, {
    "idle": [  # shifts its weight from side to side, the claws clack
        dict(twinkle=0),
        dict(bc=(0, -1, 54, 0.7), sc=(0, 0, 122, 0.6), twinkle=1),
        dict(bx=1, by=1, knees=1, lean=1, bc=(0, 0, 48, 0.0), sc=(0, 1, 128, 0.1), twinkle=2),
        dict(bx=1, by=1, knees=1, lean=1, bc=(0, 0, 51, 0.55), sc=(0, 1, 125, 0.5), twinkle=3),
    ],
    "walk": [  # sideways scuttle: tripod A steps while B pushes, then swap
        dict(by=-1, lift=_k(A, 2), slide=_k(A, 1), bc=(0, -1, 52, 0.25), twinkle=0),
        dict(bx=1, by=-1, lift=_k(A, 1), slide=_k(A, 2), twinkle=0),
        dict(bx=1, slide=_k(B, -1), sc=(0, 1, 128, 0.3), twinkle=1),
        dict(by=-1, lift=_k(B, 2), slide=_k(B, 1), sc=(0, -1, 122, 0.3), bc=(0, -1, 48, 0.25), twinkle=1),
        dict(bx=1, by=-1, lift=_k(B, 1), slide=_k(B, 2), twinkle=2),
        dict(bx=1, slide=_k(A, -1), twinkle=2),
    ],
    "windup": [  # the big claw rises high and gapes, space tears beside it - held
        dict(by=1, knees=1, rot=3, bc=(-3, -9, 80, 0.6), sc=(-1, -1, 118, 0.6), eye="angry", lean=-1, tear=1),
        dict(by=1, knees=1, rot=6, bc=(-5, -15, 100, 0.95), sc=(-1, -2, 114, 0.8), eye="angry", lean=-1, tear=2),
        dict(by=2, knees=2, rot=7, bc=(-6, -17, 106, 1.0), sc=(-1, -2, 112, 0.9), eye="angry", lean=-1, tear=3),
    ],
    "attack": [  # swings over open, slams forward and snaps shut on frame 1 (rift-flash), recovers
        dict(bx=1, rot=-3, bc=(2, -7, 40, 1.0), eye="angry", knees=1, slide=(1, 1, 1, 0, 0, 0)),
        dict(bx=1, rot=-6, bc=(-1, 0, -10, 0.0), eye="angry", knees=1, slide=(1, 1, 1, 0, 0, 0), rift=1.0),
        dict(bx=1, rot=-5, bc=(-2, 0, -6, 0.1), eye="angry", knees=1, slide=(1, 1, 1, 0, 0, 0), rift=0.5),
        dict(bx=0, rot=-1, bc=(1, 0, 34, 0.3)),
    ],
    "hurt": [  # recoils, the window in the shell flashes white
        dict(bx=-2, by=-1, rot=8, bc=(-1, -3, 70, 0.7), sc=(-1, -2, 140, 0.7), eye="squeeze", lean=-2,
             lift=(1, 1, 1, 0, 0, 0), flash=True),
        dict(bx=-1, rot=4, bc=(0, -1, 60, 0.3), sc=(0, -1, 132, 0.4), eye="squeeze", lean=-1),
    ],
    "death": [  # tips, flips onto its back, legs curl, the starfield fades to black
        dict(bx=-2, by=-2, rot=12, bc=(-1, -4, 76, 0.8), sc=(-1, -2, 140, 0.8), eye="squeeze", lean=-2,
             flash=True),
        dict(bx=1, by=-3, rot=38, bc=(0, -3, 80, 0.9), sc=(0, -2, 160, 0.9), eye="dead", flail=True, stars=0.8),
        dict(flip=True, eye="dead", bc=(0, 0, -30, 1.0), sc=(0, 0, 210, 1.0), stars=0.55),
        dict(flip=True, eye="dead", curl=0.55, bc=(0, 0, -30, 0.5), sc=(0, 0, 210, 0.5), stars=0.25),
        dict(flip=True, eye="dead", curl=1.0, bc=(0, 0, -30, 0.2), sc=(0, 0, 210, 0.2), stars=0.0),
    ],
})

# ---- geometry (relative to the body centre C) --------------------------------------------------
SIZE = 0.87  # overall scale (the geometry below is authored ~15% larger)
RX, RY = 10.5, 8.0  # carapace radii
WIN = (-0.3, -1.4, 8.3, 5.4)  # the void window: centre offset and radii
# legs: (hip, knee, tip dx from the anchor); 0-2 left (front, mid, back), 3-5 right
_LEFT = (
    ((-6.0, 3.8), (-10.0, -0.5), -13.0),
    ((-7.8, 2.8), (-12.0, -2.2), -15.5),
    ((-9.2, 1.6), (-13.8, -3.8), -17.5),
)
LEGS = _LEFT + tuple(((-h[0] + 1.0, h[1]), (-k[0] + 1.0, k[1]), -t + 1.0) for h, k, t in _LEFT)
LEG_ORDER = (2, 5, 1, 4, 0, 3)
# stars in the window: (dx, dy) from the window centre, kind (0 white, 1 violet, 2 cyan, 3 gold cross)
STARS = ((-4.5, -1.0, 0), (-2.0, 1.5, 1), (1.5, -2.0, 2), (3.5, 1.0, 0), (5.5, -1.0, 1), (-6.0, 1.0, 2),
         (0.0, 0.0, 3), (-2.5, -2.5, 1), (6.0, 1.5, 0))


def _leg(cv, C, body, ground, i, p):
    (hx, hy), (kx, ky), tx = LEGS[i]
    back = i in (2, 5)
    if p.flip:
        c = p.curl
        hip = (C[0] + hx, C[1] + hy)
        knee = (C[0] + kx * (1.0 - 0.15 * c), C[1] + 9.0 - ky * 0.5)
        tip = (C[0] + tx * (0.95 - 0.45 * c), C[1] + 14.5 - c * 3.0)
    elif p.flail:
        hip = (C[0] + hx, C[1] + hy)
        knee = (C[0] + kx * 1.05, C[1] + ky - 1.0)
        tip = (C[0] + tx * (1.1 - 0.1 * (i % 3)), C[1] + ky + 3.5 + 2.0 * (i % 3))
    else:
        hip = body((C[0] + hx, C[1] + hy))
        knee = body((C[0] + kx + p.slide[i] * 0.5, C[1] + ky - p.lift[i] + p.knees * 0.5))
        tip = (cv.gx - 3 + tx + p.slide[i], ground - p.lift[i])
    cv.limb([hip, knee, tip], [1.35, 1.1, 0.55], CHITIN, shade="dark" if back else "soft", name=f"leg{i}",
            sep=False if back else "deep")
    if not back:  # silver leg tip
        cv.limb([px.lerp_pt(knee, tip, 0.72), tip], [0.8, 0.55], SILVER, shade="two", decal=True, clip=f"leg{i}",
                name=f"leg{i}")


def _window(cv, C, p, frame):
    """The flat void window in the top of the shell: nebula swirl and stars (or a flash)."""
    wx, wy, wrx, wry = WIN
    cx, cy = C[0] + wx, C[1] + wy
    m = cv.mask_ellipse(cx, cy, wrx, wry) & cv.mask_of("shell")
    if p.flash:
        cv.fill(m, px.flat(FLASH), shade="flat", name="window")
        inner = cv.mask_ellipse(cx + 0.5, cy + 0.5, wrx - 2.0, wry - 1.6) & m
        cv.fill(inner, px.flat(STAR_W), shade="flat", name="window")
        ring = m & ~cv.mask_ellipse(cx - 0.3, cy - 0.3, wrx - 0.9, wry - 0.9)
        cv.fill(ring, px.flat(FLASH_2), shade="flat", name="window")
        return
    cv.fill(m, px.flat(VOID), shade="flat", name="window")
    s = p.stars
    if s > 0.5:  # a faint nebula swirl drifting across the void
        sw = cv.mask_ellipse(cx - 1.0, cy + 0.6, wrx - 2.4, wry - 1.9, angle=-12) & \
            ~cv.mask_ellipse(cx - 0.2, cy + 0.2, wrx - 4.4, wry - 2.8, angle=-12)
        cv.fill(sw & m, px.flat(NEB_D), shade="flat", name="window")
        arc = cv.mask_ellipse(cx - 1.0, cy + 0.6, wrx - 2.4, wry - 1.9, angle=-12) & \
            ~cv.mask_ellipse(cx - 1.4, cy + 0.2, wrx - 3.4, wry - 2.4, angle=-12) & (cv.Y < cy + 0.2)
        cv.fill(arc & m, px.flat(NEB_M), shade="flat", name="window")
        core = cv.mask_ellipse(cx + 1.8, cy + 0.9, 1.6, 0.9) & m
        cv.fill(core, px.flat(NEB_L), shade="flat", name="window")
        teal = cv.mask_ellipse(cx - 4.0, cy + 2.4, 3.0, 1.2, angle=-8) & m & ~sw
        cv.fill(teal, px.flat(NEB_T), shade="flat", name="window")
    n_st = int(round(len(STARS) * min(1.0, s)))
    for k, (dx, dy, kind) in enumerate(STARS[:n_st]):
        x, y = math.floor(cx + dx), math.floor(cy + dy)
        if not m[min(cv.h - 1, max(0, y)), min(cv.w - 1, max(0, x))]:
            continue
        if s < 0.5:
            cv.pixel(x, y, STAR_DIM, clip=m, name="window")
            continue
        tw = (k + p.twinkle) % 4 == 0 and kind != 3  # one star twinkles each frame
        if kind == 3:
            cv.pixels([(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)], STAR_G, clip=m, name="window")
            cv.pixel(x, y, STAR_W, clip=m, name="window")
        elif tw:
            cv.pixels([(x, y - 1), (x, y + 1)], STAR_V, clip=m, name="window")
            cv.pixel(x, y, STAR_W, clip=m, name="window")
        else:
            cv.pixel(x, y, (STAR_W, STAR_V, STAR_C)[kind], clip=m, name="window")


def _eyes(cv, C, p):
    """Eye stalks and glowing eyes, stamped crisp in canvas space (never resampled)."""
    lean_x = 1 if p.lean > 0 else (-1 if p.lean < 0 else 0)
    bases = [cv.tp((C[0] + ex, C[1] - RY + 1.0)) for ex in (-2.2, 3.2)]
    with cv.xform(np.linalg.inv(cv.M)):
        for bx_, by_ in bases:
            base = (math.floor(bx_), math.floor(by_))
            topx = base[0] + lean_x
            cv.line(base, (topx, base[1] - 2), SILVER.base, name="stalk")
            cv.line((base[0] + 1, base[1]), (topx + 1, base[1] - 1), SILVER.shadow, name="stalk")
            x0, y0 = topx - 1, base[1] - 5
            if p.eye == "dead":
                cv.stamp(["k.k", ".k.", "k.k"], x0, y0, {"k": STAR_DIM}, name="eye")
            elif p.eye == "squeeze":
                cv.stamp(["v..", ".vv", "v.."], x0, y0, {"v": EYE_V}, name="eye")
            else:
                cv.stamp([".vv.", "vwwv", "vwkv", ".vv."], x0, y0 - 1, {"v": EYE_V, "w": EYE_W, "k": PUPIL},
                         name="eye")
                if p.eye == "angry":
                    cv.pixels([(x0, y0 - 2), (x0 + 1, y0 - 2), (x0 + 2, y0 - 1), (x0 + 3, y0 - 1)], PUPIL,
                              name="brow")


def _small_claw(cv, shoulder, hand, ang, opening):
    """The far, ordinary pincer (turned away: no highlight)."""
    cv.limb([shoulder, hand], [1.4, 1.6], CHITIN, shade="two", name="arm")
    cv.ellipse(hand[0], hand[1], 3.2, 2.6, CHITIN, angle=ang, shade="nolight", name="claw", sep=True)
    front = px.polar(hand, ang, 2.2)
    for sgn, ln in ((1, 4.0), (-1, 3.6)):
        a = ang + (sgn * (8 + 30 * opening) if sgn > 0 else -6)
        root = px.polar(front, ang + 90 * sgn, 1.0)
        tip = px.polar(root, a - sgn * 18, ln)
        cv.limb([root, tip], [1.1, 0.5], CHITIN, shade="nolight", name="finger")
        cv.limb([px.lerp_pt(root, tip, 0.5), tip], [0.8, 0.45], SILVER, shade="two", decal=True, clip="finger",
                name="finger")


def _big_claw(cv, shoulder, palm, ang, opening, p):
    """Big crusher: heavy arm, round black-violet palm with a silver rim, silver-edged
    fingers; the fixed finger stays in line with the palm, the dactyl hinges open."""
    wrist = px.polar(palm, ang + 180, 4.4)
    # the elbow bends whichever way keeps it up off the ground
    elbow = min((px.ik2(shoulder, wrist, 6.0, 6.0, bend=b) for b in (1, -1)), key=lambda e: e[1])
    cv.limb([shoulder, elbow, wrist], [2.0, 1.9, 2.2], CHITIN, shade="soft", name="arm", sep=True)
    cv.ellipse(palm[0], palm[1], 5.8, 4.7, CHITIN, angle=ang, name="palm", sep="deep")
    # silver rim along the upper edge of the palm
    cv.ellipse(palm[0], palm[1], 5.8, 4.7, SILVER, angle=ang, shade="two", decal=True, clip="palm", name="palm",
               minus=cv.mask_ellipse(palm[0] + 0.6, palm[1] + 0.8, 5.1, 4.0, angle=ang))
    if p.flash:
        cv.ellipse(palm[0] + 0.4, palm[1] + 0.4, 3.0, 2.2, px.flat(FLASH), angle=ang, decal=True, clip="palm",
                   name="palm")
    front = px.polar(palm, ang, 4.0)
    tips = []
    for sgn, ln, r0, a in ((1, 8.0, 2.3, ang + 6 + 50 * opening), (-1, 7.2, 2.6, ang - 4)):
        root = px.polar(front, ang + 90 * sgn, 1.9)
        mid = px.polar(root, a, ln * 0.55)
        tip = px.polar(mid, a - sgn * (30 + 16 * (1 - opening)), ln * 0.5)
        cv.limb([root, mid, tip], [r0, r0 * 0.72, 0.7], CHITIN, name="finger", sep="deep")
        cv.limb([px.lerp_pt(root, mid, 0.6), mid, tip], [r0 * 0.62, r0 * 0.62, 0.7], SILVER, decal=True,
                clip="finger", name="finger")
        tips.append(tip)
    return tips


def _slit(fx, x, y, h, bright):
    """A vertical tear in space, ``h`` px tall: void core, violet lips, white-hot when ``bright``."""
    for j in range(h):
        t = (j + 0.5) / h
        w = 1 if 0.2 < t < 0.8 and h >= 5 else 0
        jig = (0, 1, 0, -1)[j % 4] if h >= 6 else 0
        xc = x + jig
        if w:
            fx.pixel(xc, y + j, VOID, name="tear")
            fx.pixel(xc - 1, y + j, RIFT_W if bright else RIFT_V, name="tear")
            fx.pixel(xc + 1, y + j, RIFT_V if bright else RIFT_D, name="tear")
        else:
            fx.pixel(xc, y + j, RIFT_V if bright else RIFT_D, name="tear")


def _tear(fx, tip, level, frame):
    """A faint tear in space shimmering beside the raised claw, with a few glints."""
    x, y = math.floor(tip[0]) + 9, math.floor(tip[1]) - 1
    _slit(fx, x, y - level, 2 + 3 * level, level >= 3)
    gl = [(-2, -5 - level), (4, 2), (-8, 0)][:level]
    for k, (dx, dy) in enumerate(gl):
        gx, gy = x + dx, y + dy - (frame + k) % 2
        fx.pixels([(gx - 1, gy), (gx + 1, gy), (gx, gy - 1), (gx, gy + 1)], RIFT_V, name="tear")
        fx.pixel(gx, gy, RIFT_W, name="tear")


def _rift(fx, c, life):
    """Rift-flash: a tall lens-shaped tear, white-hot rim, void core, and rays."""
    x, y = math.floor(c[0]), math.floor(c[1])
    if life >= 1.0:
        rows = ["...v...",
                "..vwv..",
                "..wkw..",
                ".vwkwv.",
                ".wkkkw.",
                "vwkkkwv",
                ".wkkkw.",
                ".vwkwv.",
                "..wkw..",
                "..vwv..",
                "...v..."]
        fx.stamp(rows, x - 3, y - 5, {"v": RIFT_V, "w": RIFT_W, "k": VOID}, name="rift")
        for a, r0, r1 in ((0, 4.8, 6.4), (180, 4.8, 6.4), (60, 6.0, 7.6), (120, 6.0, 7.6), (240, 6.0, 7.6),
                          (300, 6.0, 7.6)):
            p0 = px.polar((x + 0.5, y + 0.5), a, r0)
            p1 = px.polar((x + 0.5, y + 0.5), a, r1)
            fx.line((math.floor(p0[0]), math.floor(p0[1])), (math.floor(p1[0]), math.floor(p1[1])), RIFT_V,
                    name="rift")
    else:  # closing: a thin violet slit
        _slit(fx, x, y - 3, 7, False)


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    ground = cv.ground
    C = (cv.gx - 3 + p.bx, ground - 10.5 + p.by)

    def body(pt):
        return px.rot_pt(pt, p.rot, (C[0], ground))

    xf = [px.rotate(p.rot, (C[0], ground))]
    if p.flip:
        C = (cv.gx - 3, ground - 10.0)
        xf = [px.flip_y(C[1])]
    cv.snap_ground = p.flip or p.flail
    cv.opacity = p.fade

    with cv.xform(px.scale(SIZE, SIZE, (cv.gx - 3, ground))):  # the whole crab, scaled about its feet
        if p.flip or p.flail:
            with cv.xform(*xf):
                for i in LEG_ORDER:
                    _leg(cv, C, lambda q: q, ground, i, p)
        else:
            for i in LEG_ORDER:
                _leg(cv, C, body, ground, i, p)
        with cv.xform(*xf):
            cv.ellipse(C[0] + 0.5, C[1] + 5.4, 7.0, 2.6, UNDER, shade="two", name="under")
            cv.pixels([(int(C[0]) + k, int(C[1]) + 7) for k in (0, 1, 2)], MOUTH, name="mouth")
            # carapace: a silver dome with two short lateral spines
            g = cv.union(cv.geom_ellipse(C[0], C[1], RX, RY),
                         cv.geom_limb([(C[0] - 8.5, C[1] + 0.5), (C[0] - 12.8, C[1] - 1.4)], [1.6, 0.6]),
                         cv.geom_limb([(C[0] + 8.5, C[1] + 0.5), (C[0] + 12.8, C[1] - 1.4)], [1.6, 0.6]),
                         weights=[1.0, 0.5, 0.5])
            cv.draw_geom(g, SILVER, name="shell", sep="deep")
            _window(cv, C, p, frame)
            if not p.flip:
                _eyes(cv, C, p)
            sdx, sdy, sang, sop = p.sc
            _small_claw(cv, (C[0] - 7.5, C[1] + 2.5), (C[0] - 12.0 + sdx, C[1] - 0.5 + sdy), sang, sop)
            dx, dy, ang, op = p.bc
            palm = (C[0] + 13.0 + dx, C[1] + 1.0 + dy)
            tips = _big_claw(cv, (C[0] + 7.5, C[1] + 3.5), palm, ang, op, p)
            pinch = cv.tp(px.lerp_pt(tips[0], tips[1], 0.5))
            tip_w = cv.tp(palm)
            shell_top = cv.tp((C[0], C[1] - 6))
    if p.tear:
        _tear(cv.layer(above=True, outline=False), tip_w, p.tear, frame)
    if p.rift is not None:
        fx = cv.layer(above=True, outline=False)
        _rift(fx, (pinch[0] + 1.0, pinch[1] - 1.0), p.rift)
    if p.flash:  # a few sparks thrown off the flashing shell
        fx = cv.layer(above=True, outline=False)
        hc.sparks(fx, shell_top[0], shell_top[1], 0.5, n=4, radius=7.0, colors=(STAR_W, EYE_V), seed=11, spread=120,
                  aim=95)
