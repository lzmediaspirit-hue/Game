"""Terracotta warden - a life-size fired-clay tomb soldier woken by the sand Qi of the Tomb
of Sunscar (a sand king's burial palace, Azure Expanse, level 77), a slow, heavy guard (Earth).

View: side, facing right.  ~62 art px tall to the top of the hair knot on a 96 px art canvas
(cell 192), about 1.2x the player (52 px).
Rig: pelvis P and a spine tilted by ``lean`` (90 = upright) up to the shoulders; two-bone
legs and arms solved with ``px.ik2``.  The ge (bronze dagger-axe) is defined by the near
hand's grip point, the shaft angle and ``hold`` (grip -> head length); the far hand either
hangs free or grips lower on the shaft (``slide``).
Parts, back to front: far leg, far arm, near leg (puttee-wrapped shin, square-toed shoe),
knee-length robe skirt, lamellar vest (rows of clay plates, faded vermilion hem and lacing,
mineral-green collar), green scarf, ge (lacquered shaft, verdigris-bloomed bronze blade with
its hu and tang), head (hair combed into a corded knot, calm sculpted face with a moustache
and fine cracks, molten amber eye), near arm, lamellar shoulder guard.
Sand trickles from the cracks at the knee, elbow and hip.
Idle: rigid, sand trickles, the eye pulses.  Walk: stiff heavy march, plates clack.
Windup: the ge is hauled up overhead with both hands, the eye flares (held).  Attack: a heavy
downward chop, the blade bites the ground in front with a burst of sand and clay chips on
frame 1.  Hurt: recoil, a clay chip flies off.  Death: glowing cracks spread, it breaks
apart into shards and a heap of sand, the ge falls, then it fades.
"""
import math
from types import SimpleNamespace

import numpy as np

import helpers_batch_a as hb
import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "terracotta_warden",
    "cell": 192,
    "anchor": [96, 168],
    "flying": False,
    "hit_frame": 1,
}

# ---- palette: fired terracotta (pale-clay lights, violet-brown shadows), paler armour clay,
# faded vermilion + mineral-green paint, verdigris bronze, molten amber, tomb sand -------------
CLAY = px.material("tw_clay", "#efbf8f", "#c47c4e", "#8f5040", "#5c3039", outline="#1e0c10",
                   thresholds=(0.9, 0.55, 0.2))
CLAY_D = px.material("tw_clay_dark", "#c68a5f", "#9b5b3f", "#713d37", "#48262f", outline="#1a0a0e",
                     thresholds=(0.9, 0.55, 0.2))
PLATE = px.material("tw_plate", "#ecc9a0", "#bb8c6b", "#8a5c4f", "#5a3845", outline="#1d0e13",
                    thresholds=(0.9, 0.55, 0.2))
RED = px.material("tw_vermilion", "#ea967a", "#c9624f", "#96434a", "#612a3a", outline="#1f0b10")
GREEN = px.material("tw_malachite", "#aad4a7", "#72a88b", "#4c7b6f", "#30524e", outline="#0c1a18")
BRONZE = px.material("tw_bronze", "#ecc47c", "#b98547", "#7e5633", "#4c3326", outline="#170d08")
VERD = px.material("tw_verdigris", "#a8e6c9", "#62b99d", "#3d8a7a", "#275859", outline="#0b1d1c")
SAND = px.material("tw_sand", "#f7e4b4", "#e2c286", "#b99460", "#8b6a48", outline="#4a3526")
HAIR = CLAY_D.step(1)
GLOW = px.rgb("#ffb347")
CORE = px.rgb("#fff1b6")
EMBER = RED.base  # dim eye: a banked, reddish ember
CRACK = CLAY.deep

L_THIGH, L_SHIN = 11.0, 11.0
L_UPPER, L_FORE = 9.5, 10.5
TORSO = 18.0
SHAFT = 56.0
HEAD_K = 1.12  # head scale about the chin

# ---- poses --------------------------------------------------------------------------------
# bx, by   pelvis offset          lean  spine angle (deg, 90 = upright, > 90 leans back)
# head     head tilt (deg)        grip  near-hand grip point from the shoulders (dx, dy)
# ang      ge shaft angle (deg, 90 = head up)     hold  grip -> head length (None = butt planted)
# slide    far hand this far down the shaft (None = far hand free at ``fh`` from its shoulder)
# nb       near elbow bend side   fn, ff  near / far foot (dx from the pelvis, lift)
# glow     eye 1 dim .. 3 flare   eye  open | squeeze | dead      sand  trickle phase (None = off)
# crack    0..3 extra cracks      cglow  cracks glow amber        clack  walk plate jostle (1, 2)
# step     planted foot kicks sand (0 near / 1 far)    swoosh  chop trail sweep (deg, None = off)
# burst    ground burst life      hit  impact spark    chip  hurt chip life   pour  death sand
# brk      crumble 0..1           drop  "fall" = ge tipping over          pile  heap frames
DEFAULTS = dict(bx=0, by=0, lean=90, head=0, grip=(13, 13), ang=89, hold=None, slide=None, fh=(1.0, 16.0),
                nb=-1, fn=(4, 0), ff=(-3, 0), glow=1, eye="open", sand=None, crack=0, cglow=False, clack=0,
                step=None, swoosh=None, burst=None, hit=False, chip=None, pour=None, brk=None, drop=None,
                pile=0, fade=1.0)

_NEAR = [(6, 0), (2.5, 0), (-1.5, 0), (-5, 0), (-1.5, 3), (2.5, 3)]
_FAR = [(-5, 0), (-1.5, 3), (2.5, 3), (6, 0), (2.5, 0), (-1.5, 0)]
_BOB = [1, 0, 0, 1, 0, 0]
_SWING = [(-2.0, 16.0), (-0.5, 16.2), (1.5, 16.0), (3.0, 15.8), (1.5, 16.0), (-0.5, 16.2)]
_TILT = [87, 88, 88, 87, 88, 88]

POSE = px.poses(DEFAULTS, {
    "idle": [  # rigid on guard, ge planted: only the sand trickles and the eye pulses
        dict(sand=0, glow=1),
        dict(sand=1, glow=2),
        dict(sand=2, glow=2),
        dict(sand=3, glow=1),
    ],
    "walk": [  # stiff, heavy march: the body drops on each planted foot, the plates clack
        dict(fn=_NEAR[i], ff=_FAR[i], by=_BOB[i], fh=_SWING[i], hold=30, ang=_TILT[i], grip=(13, 12),
             clack=(1 if i == 0 else 2 if i == 3 else 0), step=(0 if i == 0 else 1 if i == 3 else None),
             sand=i % 4)
        for i in range(6)
    ],
    "windup": [  # hauls the ge up overhead with both hands, the eye flares - held
        dict(grip=(12, 1), ang=100, hold=24, slide=10, lean=91, fn=(5, 0), ff=(-4, 0), glow=2),
        dict(grip=(0, -15), ang=138, hold=20, slide=10, lean=95, head=3, fn=(6, 0), ff=(-5, 0), glow=3, nb=1,
             crack=1, cglow=True),
        dict(grip=(-3, -19), ang=160, hold=18, slide=10, lean=97, head=4, fn=(7, 0), ff=(-6, 0), glow=3, nb=1,
             by=1, crack=1, cglow=True),
    ],
    "attack": [  # over the top and down: the blade bites the ground in front on frame 1
        dict(grip=(10, -8), ang=58, hold=26, slide=10, lean=86, fn=(6, 0), ff=(-6, 0), glow=3, nb=1, crack=1,
             cglow=True,
             swoosh=70),
        dict(grip=(13, 13), ang=-36, hold=26, slide=10, lean=72, by=3, bx=1, fn=(8, 0), ff=(-6, 0), glow=3,
             swoosh=60, burst=0.15, hit=True, crack=1, cglow=True),
        dict(grip=(13, 13), ang=-36, hold=26, slide=10, lean=73, by=3, bx=1, fn=(8, 0), ff=(-6, 0), glow=2,
             burst=0.5),
        dict(grip=(11, 6), ang=62, hold=28, slide=10, lean=84, by=1, fn=(6, 0), ff=(-5, 0), glow=2, burst=0.85),
    ],
    "hurt": [  # rocks back on its heels, a clay chip flies off the shoulder guard, the eye gutters
        dict(bx=-3, lean=100, head=8, grip=(10, 14), ang=100, hold=30, eye="squeeze", chip=0.5, crack=1,
             fh=(-3.0, 15.0)),
        dict(bx=-2, lean=95, head=4, grip=(11, 14), ang=95, hold=30, eye="squeeze", chip=0.95, crack=1,
             fh=(-1.0, 15.5)),
    ],
    "death": [  # cracks flare amber and spread, it breaks into shards and sand, the ge falls
        dict(bx=-3, lean=100, head=10, grip=(10, 15), ang=104, hold=30, eye="squeeze", crack=3, cglow=True,
             pour=0.3, fh=(-3.0, 15.0)),
        dict(bx=-2, by=2, lean=96, head=-6, eye="dead", crack=3, cglow=True, brk=0.3, drop="fall", pour=0.8),
        dict(pile=1, eye="dead"),
        dict(pile=1, eye="dead", fade=0.6),
        dict(pile=1, eye="dead", fade=0.3),
    ],
})


def _dir(ang):
    return (math.cos(math.radians(ang)), -math.sin(math.radians(ang)))


def _fl(q):
    return (math.floor(q[0]), math.floor(q[1]))


def _geom(cv, p):
    """Rig points for pose ``p`` (no drawing)."""
    up = p.lean
    P = (cv.gx - 3 + p.bx, cv.ground - 23.5 + p.by)

    def body(q):  # upright spine frame -> world
        return px.rot_pt(q, up - 90, P)

    S = body((P[0], P[1] - TORSO))
    G = (S[0] + p.grip[0], S[1] + p.grip[1])
    u = _dir(p.ang)
    hold = p.hold if p.hold is not None else SHAFT - (cv.ground - 0.3 - G[1]) / max(0.2, -u[1])
    G2 = (G[0] - u[0] * p.slide, G[1] - u[1] * p.slide) if p.slide is not None else None
    return SimpleNamespace(P=P, S=S, body=body, sh_n=body((P[0] + 1.6, P[1] - 16.2)),
                           sh_f=body((P[0] - 1.8, P[1] - 16.8)), H=body((P[0] + 1.2, P[1] - 26.0)), G=G, G2=G2,
                           hold=hold)


def _ge_pts(G, ang, hold, side=1, flat=1.0):
    """Key points of the ge: shaft ends and a local blade frame ``L(a, b)`` (a along the blade,
    b along the shaft toward its head).  ``flat`` foreshortens the blade (lying on its side)."""
    u = _dir(ang)
    f = _dir(ang - 90 * side)
    top = (G[0] + u[0] * hold, G[1] + u[1] * hold)
    butt = (G[0] - u[0] * (SHAFT - hold), G[1] - u[1] * (SHAFT - hold))
    R = (top[0] - u[0] * 1.8, top[1] - u[1] * 1.8)

    def L(a, b):
        return (R[0] + f[0] * a * flat + u[0] * b, R[1] + f[1] * a * flat + u[1] * b)

    return SimpleNamespace(top=top, butt=butt, L=L, tip=L(11.2, 2.4), low=L(10.2, 0.0))


def _strike(cv):
    """Where the blade bites the ground on the hit frame (x of its lowest point)."""
    g = _geom(cv, POSE("attack", SPEC["hit_frame"]))
    p = POSE("attack", SPEC["hit_frame"])
    k = _ge_pts(g.G, p.ang, g.hold)
    q = max((k.tip, k.low, k.L(8.0, -0.6)), key=lambda t: t[1])
    return (q[0], cv.gy - 1)


def _tip(cv, action, frame):
    p = POSE(action, frame)
    g = _geom(cv, p)
    return _ge_pts(g.G, p.ang, g.hold).tip


# ---- parts ------------------------------------------------------------------------------------
def _crack(cv, pts, glow, clip):
    col = GLOW if glow else CRACK
    for a, b in zip(pts, pts[1:]):
        cv.line(_fl(a), _fl(b), col, band=None, decal=True, clip=clip, name=clip if isinstance(clip, str) else None)


def _paint(cv, pts, mat, clip, seed, r=0.6):
    """Faded paint trace along a poly-line: dashes with gaps where the pigment flaked off."""
    for k, (a, b) in enumerate(zip(pts, pts[1:])):
        if px.hash01(seed, k) < 0.22:
            continue
        cv.limb([a, b], r, mat, shade="two", decal=True, clip=clip, name=clip)


def _leg(cv, hip, foot, far):
    mat = CLAY_D if far else CLAY
    shade = "dark" if far else "soft"
    ank = (foot[0] - 0.5, foot[1] - 3.0)
    knee = px.ik2(hip, ank, L_THIGH, L_SHIN, bend=1)
    sep = False if far else "deep"
    cv.limb([hip, knee], [4.0, 3.4], mat, shade=shade, name="thigh")
    cv.limb([knee, ank], [3.3, 2.5], mat, shade=shade, name="shin", sep=sep)
    # puttee wraps: diagonal bands around the shin
    for t in (0.35, 0.6, 0.85):
        q = px.lerp_pt(knee, ank, t)
        cv.line(_fl((q[0] - 3, q[1] - 1)), _fl((q[0] + 3, q[1] + 1)), mat.step(1), decal=True, clip="shin",
                name="shin")
    # square-toed shoe with an upturned toe block
    g = foot[1] + 0.5
    ax = ank[0]
    cv.polygon([(ax - 3.2, ank[1] - 0.6), (ax + 1.8, ank[1] - 0.8), (ax + 4.6, g - 2.4), (ax + 5.2, g - 3.4),
                (ax + 6.4, g - 3.4), (ax + 6.4, g), (ax - 3.4, g)], CLAY_D, shade="dark" if far else "two",
               name="shoe", sep=sep)
    return knee, ank


def _arm(cv, sh, hand, far, bend=-1):
    mat = CLAY_D if far else CLAY
    shade = "dark" if far else "soft"
    d = math.hypot(hand[0] - sh[0], hand[1] - sh[1])
    reach = L_UPPER + L_FORE - 0.4
    if d > reach:  # keep the fist attached
        hand = px.lerp_pt(sh, hand, reach / d)
    elbow = px.ik2(sh, hand, L_UPPER, L_FORE, bend=bend)
    nm = "arm_far" if far else "arm"
    sep = False if far else "deep"
    cv.limb([sh, elbow, hand], [3.4, 2.9, 2.3], mat, shade=shade, name=nm, sep=sep)
    # sleeve cuff above the wrist
    c0, c1 = px.lerp_pt(elbow, hand, 0.55), px.lerp_pt(elbow, hand, 0.62)
    cv.limb([c0, c1], 2.8, mat.step(1), shade="two", decal=True, clip=nm, name=nm)
    cv.ellipse(hand[0], hand[1], 2.6, 2.4, mat, shade="dark" if far else "soft", name="fist", sep=sep)
    return elbow, hand


def _skirt(cv, P, up, kn, kf):
    """Knee-length robe under the vest: flares from the hips to a hem that follows the knees."""
    w = px.polar
    top = w(P, up, 3.0)
    hem_y = max(kn[1], kf[1]) + 2.0
    back = min(kn[0], kf[0]) - 4.6
    front = max(kn[0], kf[0]) + 4.2
    pts = [w(top, up + 90, 6.2), w(top, up - 90, 6.6), (front, hem_y - 1.2), (front - 1.2, hem_y),
           (back + 1.2, hem_y + 0.6), (back, hem_y - 0.6)]
    cv.polygon(pts, CLAY, name="robe")
    for t in (0.3, 0.62):  # pleats
        a = px.lerp_pt(pts[0], pts[1], t)
        b = px.lerp_pt(pts[5], pts[2], t)
        cv.line(_fl(px.lerp_pt(a, b, 0.35)), _fl(b), CLAY.step(1), decal=True, clip="robe", name="robe")


def _vest(cv, P, p):
    """Lamellar vest drawn in the spine's upright frame (caller applies the lean)."""
    x, y = P
    j = 1 if p.clack == 1 else (-1 if p.clack == 2 else 0)  # rows jostle on the stomp
    vest = [(x - 6.8, y + 3.2 + j * 0.4), (x - 7.4, y - 6.0), (x - 6.9, y - 15.4), (x - 4.6, y - 18.6),
            (x + 3.6, y - 18.8), (x + 6.8, y - 15.6), (x + 7.8, y - 9.0), (x + 8.0, y - 2.0),
            (x + 7.0, y + 3.2 - j * 0.4), (x + 3.0, y + 4.6), (x - 2.0, y + 4.4)]
    cv.polygon(vest, PLATE, name="vest")
    seam = PLATE.step(1)
    # rows of lamellae: horizontal seams and staggered vertical joints
    for k in range(6):
        yy = math.floor(y + 2.0 - 3 * k + (j if k < 2 else 0))
        cv.line((math.floor(x - 9), yy), (math.floor(x + 9), yy), seam, decal=True, clip="vest", name="vest")
        off = 0 if k % 2 == 0 else 2
        for xx in range(math.floor(x - 8) + off, math.floor(x + 9), 4):
            cv.line((xx, yy - 2), (xx, yy - 1), seam, decal=True, clip="vest", name="vest")
    # smooth chest plate above the lamellae with a painted (faded) green collar edge
    _paint(cv, [(x - 4.6, y - 17.4), (x - 2.0, y - 16.2), (x + 1.0, y - 16.0), (x + 3.8, y - 17.2),
                (x + 6.2, y - 15.2)], GREEN, "vest", 3, r=0.65)
    # faded vermilion hem along the rounded bottom edge, and the laced front edge
    _paint(cv, [(x - 6.6, y + 2.6), (x - 3.5, y + 3.4), (x - 0.5, y + 3.8), (x + 2.5, y + 3.8), (x + 5.0, y + 3.2),
                (x + 7.0, y + 2.4)], RED, "vest", 5, r=0.7)
    _paint(cv, [(x + 7.2, y - 13.0), (x + 7.6, y - 9.0), (x + 7.6, y - 5.0), (x + 7.4, y - 1.0)], RED, "vest", 8,
           r=0.55)
    # sand-worn crack at the hip and extra cracks when breaking
    _crack(cv, [(x - 6, y - 1), (x - 4, y + 1), (x - 5, y + 3)], p.cglow, "vest")
    if p.crack >= 1:
        _crack(cv, [(x + 6, y - 14), (x + 3, y - 11), (x + 4, y - 8), (x + 1, y - 5)], p.cglow, "vest")
    if p.crack >= 3:
        _crack(cv, [(x - 6, y - 13), (x - 3, y - 10), (x - 4, y - 6), (x - 1, y - 3), (x - 2, y + 1)], p.cglow,
               "vest")
    # green scarf knotted at the throat
    cv.limb([(x - 3.6, y - 18.8), (x + 0.5, y - 19.4), (x + 3.4, y - 18.6)], [1.5, 1.5, 1.3], GREEN, shade="soft",
            name="scarf", sep="deep")
    cv.limb([(x + 3.0, y - 18.4), (x + 4.4, y - 16.4)], [1.1, 0.8], GREEN, shade="two", name="scarf")


def _head(cv, H, p):
    x, y = H
    # hair knot on the crown, a little toward the back, bound with a faded vermilion cord
    cv.ellipse(x - 1.6, y - 5.9, 2.6, 1.9, CLAY_D, angle=18, shade="two", name="knot")
    # skull + face profile as one form
    skull = cv.geom_ellipse(x - 0.6, y - 0.2, 5.2, 5.6)
    face = cv.geom_polygon([(x + 1.6, y - 5.2), (x + 4.4, y - 3.8), (x + 5.2, y - 2.0), (x + 5.4, y - 0.6),
                            (x + 7.4, y + 2.0), (x + 5.8, y + 2.6), (x + 6.0, y + 3.6), (x + 5.4, y + 5.6),
                            (x + 2.2, y + 6.8), (x - 1.5, y + 5.0)])
    cv.draw_geom(cv.union(skull, face), CLAY, name="head", sep="deep")
    # hair combed back from a hairline above the brow; the sideburn frames the ear
    hair = [(x + 3.8, y - 4.4), (x + 2.2, y - 5.8), (x - 1.2, y - 6.2), (x - 4.6, y - 4.6), (x - 5.9, y - 1.0),
            (x - 5.4, y + 2.8), (x - 3.4, y + 3.6), (x - 2.6, y + 0.2), (x - 0.6, y - 2.8), (x + 2.4, y - 3.6)]
    cv.polygon(hair, HAIR, shade="two", decal=True, clip="head", name="head")
    for k in range(2):  # comb lines sweeping back to the knot
        cv.line(_fl((x + 1.0 - k * 2.4, y - 4.4 + k * 0.8)), _fl((x - 1.6 - k * 2.0, y - 5.4 + k * 1.6)),
                HAIR.step(1), decal=True, clip="head", name="head")
    kx, ky = _fl((x - 1.2, y - 5.2))
    cv.pixels([(kx - 1, ky), (kx, ky), (kx + 1, ky - 1)], RED.base, name="cord")
    # ear
    cv.ellipse(x - 1.2, y + 1.0, 1.4, 1.9, CLAY, shade="two", name="ear", sep="deep")
    # calm sculpted features: brow ridge, moustache, closed lips
    ex, ey = math.floor(x + 3), math.floor(y - 1)
    cv.line((ex - 1, ey - 2), (ex + 2, ey - 2), CLAY.step(1), decal=True, clip="head", name="head")
    cv.pixels([(ex + 2, ey + 3), (ex + 3, ey + 3), (ex + 1, ey + 3), (ex, ey + 2)], HAIR.base, name="stache")
    cv.pixels([(ex + 2, ey + 5), (ex + 3, ey + 5)], CLAY.deep, name="mouth")
    # fine firing cracks on the cheek and brow
    _crack(cv, [(x + 1, y + 2), (x + 2, y + 4), (x + 1, y + 6)], p.cglow, "head")
    if p.crack >= 2:
        _crack(cv, [(x + 4, y - 5), (x + 2, y - 3), (x + 3, y - 1)], p.cglow, "head")
    # the molten amber eye
    if p.eye == "dead":
        cv.stamp(["kk"], ex, ey, {"k": CLAY.deep}, name="eye")
    elif p.eye == "squeeze":
        cv.stamp(["ee"], ex, ey + 1, {"e": EMBER}, name="eye")
        cv.line((ex, ey), (ex + 2, ey - 1), CLAY.deep, name="eye")
    elif p.glow >= 3:
        cv.stamp(["gcg"], ex - 1, ey, {"g": GLOW, "c": CORE}, name="eye")
    elif p.glow == 2:
        cv.stamp(["gc"], ex, ey, {"g": GLOW, "c": CORE}, name="eye")
    else:
        cv.stamp(["eg"], ex, ey, {"e": EMBER, "g": GLOW}, name="eye")
    return (ex + 1, ey)


def _pauldron(cv, sh, rot, p):
    """Lamellar shoulder guard hanging over the near upper arm (three rows of plates)."""
    x, y = sh
    with cv.xform(px.rotate(rot, sh)):
        cv.polygon([(x - 4.4, y - 1.2), (x - 2.0, y - 3.4), (x + 2.2, y - 3.4), (x + 4.6, y - 1.0),
                    (x + 4.8, y + 5.6), (x + 0.2, y + 6.4), (x - 4.6, y + 5.6)], PLATE, name="pauldron", sep="deep")
        for k, dy in enumerate((0.0, 3.0)):
            yy = math.floor(y + dy)
            cv.line((math.floor(x - 5), yy), (math.floor(x + 5), yy), PLATE.step(1), decal=True, clip="pauldron",
                    name="pauldron")
            for xx in range(math.floor(x - 3) + 2 * (k % 2), math.floor(x + 5), 4):
                cv.line((xx, yy + 1), (xx, yy + 2), PLATE.step(1), decal=True, clip="pauldron", name="pauldron")
        _paint(cv, [(x - 4.2, y + 5.0), (x - 1.5, y + 5.8), (x + 1.5, y + 5.8), (x + 4.4, y + 5.0)], GREEN,
               "pauldron", 13, r=0.7)
        if p.crack >= 2:
            _crack(cv, [(x + 3, y - 2), (x + 1, y + 1), (x + 2, y + 4)], p.cglow, "pauldron")


def _ge(cv, G, ang, hold, side=1, flat=1.0, name="ge"):
    """Bronze dagger-axe: lacquered shaft with a bronze butt ferrule; the blade (yuan) juts out
    perpendicular at the top, its lower edge running down the shaft as the hu, a short tang
    (nei) behind.  Verdigris blooms on the bronze.  ``side`` -1 mirrors the blade."""
    k = _ge_pts(G, ang, hold, side, flat)
    L = k.L
    cv.limb([k.butt, k.top], 1.0, CLAY_D, shade="dark", name=name)
    cv.limb([k.butt, px.lerp_pt(k.butt, k.top, 0.05)], 1.3, BRONZE, shade="two", name=name)
    cv.polygon([L(0, 1.8), L(5.5, 1.5), L(9.4, 1.9), L(11.2, 2.4), L(10.2, 0.0), L(6.0, -1.0), L(2.8, -1.7),
                L(1.9, -3.6), L(1.7, -7.4), L(0, -8.2)], BRONZE, name=name, sep="deep")
    cv.polygon([L(0, 1.2), L(-3.2, 1.0), L(-3.6, -0.2), L(0, -0.8)], BRONZE, shade="two", name=name)
    # verdigris bloom on the hu and around the root; the cutting edge stays bright
    for (a, b, ra, rb) in ((1.0, -5.0, 1.2, 2.6), (3.6, 0.2, 1.9, 1.1)):
        c = L(a, b)
        cv.ellipse(c[0], c[1], ra * max(flat, 0.5), rb, VERD, angle=ang - 90, shade="two", decal=True, clip=name,
                   name=name)
    cv.line(_fl(L(6.0, -0.5)), _fl(L(9.6, 0.5)), BRONZE.light, band=0, decal=True, clip=name, name=name)
    return k


def _trail(cv, G, tip, sweep):
    """Chop trail: two sand-coloured arcs round the hands (the swing's pivot) that end at the
    blade tip and reach ``sweep`` degrees back along the path it came from."""
    fx = cv.layer(above=False, outline=False)
    r = math.hypot(tip[0] - G[0], tip[1] - G[1])
    a = math.degrees(math.atan2(-(tip[1] - G[1]), tip[0] - G[0]))
    for (rr, a0, a1, col) in ((r, a + sweep, a + 4, SAND.light), (r - 2.5, a + sweep * 0.75, a + 10, SAND.base)):
        n = max(2, int(abs(a1 - a0) / 3.0))
        prev = None
        for i in range(n + 1):
            pt = _fl(px.polar(G, a0 + (a1 - a0) * i / n, rr))
            ok = 3 <= pt[0] <= cv.w - 4 and 3 <= pt[1] <= cv.gy - 3
            if ok and prev is not None and pt != prev:
                fx.line(prev, pt, col, name="swoosh")
            prev = pt if ok else None


def _stream(fx, x, y0, y1, phase):
    """A thin trickle of sand from (x, y0) down to y1: dashes that slide down with ``phase``."""
    on = [y for y in range(y0, y1 + 1) if y - y0 < 2 or (y - y0 - phase) % 4 != 3]
    for y in on:
        if (y - 1 in on) or (y + 1 in on):  # never leave a lone grain (stray pixel)
            k = (y - y0 - phase) % 4
            fx.pixel(x, y, SAND.light if k == 0 else SAND.base, name="sand")


# ---- main ------------------------------------------------------------------------------------
def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    ground = cv.ground
    if p.pile:
        _heap(cv, ground, p)
        return
    g = _geom(cv, p)
    P, S, H, G, body = g.P, g.S, g.H, g.G, g.body
    up = p.lean

    def foot(f):
        return (P[0] + f[0], ground - f[1])

    held = p.drop is None
    _leg(cv, (P[0] - 1.2, P[1] + 1.0), foot(p.ff), True)
    if held:
        fhand = g.G2 if g.G2 is not None else (g.sh_f[0] + p.fh[0], g.sh_f[1] + p.fh[1])
        _arm(cv, g.sh_f, fhand, True, bend=-1)
    kn, _ = _leg(cv, (P[0] + 1.2, P[1] + 1.2), foot(p.fn), False)
    kf = px.ik2((P[0] - 1.2, P[1] + 1.0), (P[0] + p.ff[0] - 0.5, ground - p.ff[1] - 3.0), L_THIGH, L_SHIN, bend=1)
    _skirt(cv, P, up, kn, kf)
    with cv.xform(px.rotate(up - 90, P)):
        _vest(cv, P, p)
    ge = _ge(cv, G, p.ang, g.hold) if held else None

    def near_arm():
        if held:
            el, hd = _arm(cv, g.sh_n, G, False, bend=p.nb)
        else:  # the ge slipped away: the arm hangs
            el, hd = _arm(cv, g.sh_n, (g.sh_n[0] + 3.0, g.sh_n[1] + 16.0), False, bend=-1)
        a_up = math.degrees(math.atan2(-(el[1] - g.sh_n[1]), el[0] - g.sh_n[0]))
        with cv.xform(px.translate(0, -1 if p.clack else 0)):  # the plates lag the stomp and clack
            _pauldron(cv, g.sh_n, max(-40.0, min(60.0, (a_up + 90) * 0.35)) + (up - 90), p)
        return el, hd

    raised = held and G[1] < g.sh_n[1] - 8
    if raised:
        elbow, nhand = near_arm()
    with cv.xform(px.rotate(p.head, (H[0], H[1] + 5.0)), px.scale(HEAD_K, HEAD_K, (H[0], H[1] + 6.0))):
        eye = _head(cv, H, p)
        eye = cv.tp((eye[0] + 0.5, eye[1] + 0.5))
    if not raised:
        elbow, nhand = near_arm()
    # knee crack (sand leaks from it) and elbow crack
    kc = (kn[0] + 1.0, kn[1] + 2.0)
    cv.line(_fl(kc), _fl((kc[0] + 1, kc[1] + 2)), GLOW if p.cglow else CRACK, decal=True, clip="shin", name="shin")
    cv.line(_fl((elbow[0] - 1, elbow[1] - 1)), _fl((elbow[0] + 1, elbow[1] + 1)), GLOW if p.cglow else CRACK,
            decal=True, clip="arm", name="arm")
    if p.brk is not None:  # the body breaks into shards along the glowing cracks
        seeds = [(H[0], H[1] - 3), (H[0] + 2, H[1] + 4), (S[0] - 4, S[1] + 3), (S[0] + 4, S[1] + 4),
                 (P[0] - 4, P[1] - 6), (P[0] + 4, P[1] - 5), (P[0] - 4, P[1] + 5), (P[0] + 4, P[1] + 6),
                 (kn[0], kn[1] + 4), (kf[0], kf[1] + 4), (P[0] + 2, ground - 2), (P[0] - 6, ground - 2),
                 (nhand[0], nhand[1]), (elbow[0], elbow[1]), (g.sh_n[0], g.sh_n[1])]
        hb.crumble(cv, seeds, p.brk, cv.gy - 2, seed=17, spread=1.1)
    if p.drop == "fall":  # the ge tips forward out of the loosened grip, butt still on the ground
        a = 62.0
        ge = _ge(cv, (cv.gx + 4 + 20 * math.cos(math.radians(a)), ground - 0.6 - 20 * math.sin(math.radians(a))), a,
                 SHAFT - 20)
    # anything driven below the ground row sinks out of sight
    below = np.zeros((cv.h, cv.w), bool)
    below[cv.gy - 1:, :] = True
    hc.erase_mask(cv, below & cv.filled)

    # ---- FX ----------------------------------------------------------------------------------
    if p.sand is not None:  # sand trickling from the knee, elbow and hip cracks
        fx = cv.layer(above=True, outline=False)
        hip = body((P[0] - 7.0, P[1] + 4.0))
        for k, (src, ln) in enumerate((((kc[0] + 1.0, kc[1] + 2.0), 5), ((hip[0], hip[1] + 0.5), 8))):
            x0, y0 = _fl(src)
            _stream(fx, x0, y0, min(y0 + ln, cv.gy - 3), (p.sand + k) % 4)
    if p.step is not None:  # the planted foot kicks up a little tomb sand
        fx = cv.layer(above=False, outline=True)
        f = foot(p.fn if p.step == 0 else p.ff)
        px.dust(fx, f[0] - 3.5, cv.gy - 1, 0.1, size=0.7, direction=-1, mat=SAND)
    if p.glow >= 3 and p.eye == "open":  # the eye flares: a molten streak
        fx = cv.layer(above=True, outline=False)
        ex, ey = _fl(eye)
        fx.pixels([(ex + 2, ey), (ex + 3, ey), (ex + 4, ey - 1)], GLOW, name="flare")
        fx.pixels([(ex - 3, ey), (ex - 4, ey)], EMBER, name="flare")
    if p.swoosh is not None and ge is not None:
        _trail(cv, G, ge.tip, p.swoosh)
    strike = _strike(cv)
    if p.burst is not None:  # sand bursts up where the blade bit, clay chips fly
        fx = cv.layer(above=True, outline=True)
        t = p.burst
        px.dust(fx, strike[0] + 1.0, strike[1], t, size=0.9, direction=1, mat=SAND)
        px.dust(fx, strike[0] - 4.0, strike[1], t, size=1.3, direction=-1, mat=SAND)
        for k, (vx, vy) in enumerate(((-4.0, 9.0), (1.0, 11.0), (2.5, 7.0))):
            x = strike[0] + vx * (0.5 + t) * 1.3
            y = strike[1] - 3 - (vy * (0.4 + t) * 1.3 - 9 * t * t)
            r = 1.5 - 0.3 * (k % 2)
            fx.polygon([(x - r, y + r * 0.7), (x - r * 0.1, y - r), (x + r, y + r * 0.5)], PLATE if k % 2 else CLAY,
                       shade="soft", name="chip")
    if p.hit and ge is not None:
        top = cv.layer(above=True, outline=False)
        px.impact(top, strike[0], strike[1] - 5, size=4, color=CORE, core=px.GLINT)
    if p.chip is not None:  # a clay chip knocked off the shoulder guard
        fx = cv.layer(above=True, outline=True)
        t = p.chip
        x = g.sh_n[0] - 6 - 11 * t
        y = g.sh_n[1] - 3 - 9 * t + 8 * t * t
        with fx.xform(px.rotate(90 * t, (x, y))):
            fx.polygon([(x - 2.2, y + 1.4), (x - 0.4, y - 2.0), (x + 2.2, y - 0.6), (x + 1.4, y + 1.8)], PLATE,
                       shade="soft", name="chip")
        if t < 0.5:  # a puff of sand where the chip broke off the shoulder guard
            sx, sy = _fl((g.sh_n[0] - 1.0, g.sh_n[1] - 3.5))
            fx.pixels([(sx, sy), (sx - 1, sy), (sx, sy - 1)], SAND.light, name="chip")
    if p.pour is not None:  # sand pours out through the cracks and piles at the feet
        fx = cv.layer(above=p.brk is None, outline=False)
        if p.brk is None:
            srcs = (body((P[0] - 5.0, P[1] + 4.5)), body((P[0] + 5.0, P[1] + 4.5)), (kc[0] + 1.0, kc[1] + 2.0))
        else:  # broken: sand spills from between the shards
            srcs = [(P[0] + dx, P[1] + 2) for dx in (-6, 0, 5)]
        for k, src in enumerate(srcs):
            x0, y0 = _fl(src)
            filled = np.nonzero(cv.filled[:, x0])[0]
            if p.brk is not None and len(filled):
                y0 = max(y0, int(filled.min()) + 3)
            _stream(fx, x0, y0, cv.gy - 3, k + frame)
        pile = cv.layer(above=True, outline=True)
        s = 0.7 + 0.7 * p.pour
        cx, gb = P[0] + 1, cv.gy - 1.0
        pile.polygon([(cx - 8 * s, gb), (cx - 4 * s, gb - 1.6 * s), (cx, gb - 2.4 * s), (cx + 4 * s, gb - 1.8 * s),
                      (cx + 8 * s, gb)], SAND, shade="soft", name="pile")


def _shard(cv, pts, mat, name, seams=0, paint=None, rot=0.0):
    c = (sum(q[0] for q in pts) / len(pts), sum(q[1] for q in pts) / len(pts))
    with cv.xform(px.rotate(rot, c)):
        cv.polygon(pts, mat, name=name, sep="deep")
        ys = [q[1] for q in pts]
        xs = [q[0] for q in pts]
        for k in range(seams):
            yy = math.floor(min(ys) + (k + 1) * (max(ys) - min(ys)) / (seams + 1))
            cv.line((math.floor(min(xs)), yy), (math.floor(max(xs)), yy), mat.step(1), decal=True, clip=name,
                    name=name)
        if paint is not None:
            yb = max(ys) - 0.8
            cv.limb([(min(xs) + 1.0, yb), (max(xs) - 1.0, yb)], 0.6, paint, shade="two", decal=True, clip=name,
                    name=name)


def _heap(cv, ground, p):
    """A heap of tomb sand with fired-clay shards sunk in it; the calm face rests on top, its light
    gone, and the fallen ge lies behind it, blade showing past the sand."""
    X = cv.gx - 3
    g = ground + 0.5
    # the fallen ge on the ground, butt buried under the heap, blade on its side
    _ge(cv, (X + 14, g - 1.4), 0, 22.0, side=-1, flat=0.45)
    # sand mound (the bulk of the heap)
    mound = cv.union(cv.geom_ellipse(X - 3, g + 2.0, 16.0, 12.0), cv.geom_ellipse(X + 9, g + 1.0, 9.0, 7.0),
                     cv.geom_ellipse(X - 15, g + 1.0, 7.0, 5.0))
    cv.draw_geom(mound, SAND, name="sand", bulge=0.8, sep="deep")
    # shards sunk in the slopes: a lamellar torso plate, the shoulder guard, a forearm and fist
    _shard(cv, [(X - 12, g - 14), (X - 5, g - 15), (X - 4, g - 7), (X - 11, g - 6)], PLATE, "shard1", seams=2,
           paint=RED, rot=-24)
    _shard(cv, [(X + 6, g - 11), (X + 12, g - 10), (X + 12, g - 5), (X + 6, g - 5)], PLATE, "shard2", seams=1,
           paint=GREEN, rot=30)
    cv.limb([(X - 19, g - 2.5), (X - 15, g - 5.0)], [2.3, 2.1], CLAY, shade="soft", name="limb", sep="deep")
    cv.ellipse(X - 14.0, g - 5.6, 2.5, 2.3, CLAY, shade="soft", name="fist", sep="deep")
    # the head rests on the top of the heap, tipped back, face turned up
    H = (X + 0.5, g - 13.5)
    with cv.xform(px.rotate(40, H), px.scale(HEAD_K, HEAD_K, (H[0], H[1] + 6.0))):
        _head(cv, H, p)
    # front drift of sand over the foot of the heap
    drift = cv.union(cv.geom_ellipse(X - 4, g + 2.0, 12.0, 5.5), cv.geom_ellipse(X + 7, g + 2.0, 7.0, 4.0))
    cv.draw_geom(drift, SAND, name="drift", bulge=0.7, sep="deep")
    # loose clay chips on the ground
    for (cx, w) in ((X - 24, 2.4), (X + 19, 2.0)):
        cv.polygon([(cx - w, g), (cx - w * 0.3, g - w), (cx + w, g - w * 0.5), (cx + w, g)], CLAY, shade="two",
                   name="chip", sep="deep")
    below = np.zeros((cv.h, cv.w), bool)
    below[cv.gy - 1:, :] = True
    hc.erase_mask(cv, below & cv.filled)
