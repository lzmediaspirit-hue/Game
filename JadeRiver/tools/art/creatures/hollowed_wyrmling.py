"""Hollowed wyrmling - a young wyrm of the star-sea nests corrupted by the Hollow (Hollow Fire).

View: side, facing right, on the ground (cell 128): it hops and scrambles, its small wings too
ragged to fly.  ~40 art px from the curled tail to the snout, ~20 px tall with the head up.
A serpentine little dragonet: grey-violet ashen scales split by ash-white cracks that leak a
sickly violet glow, empty glowing violet eyes, dull ember fire smouldering in its throat.
Parts, back to front: far legs (dark), far torn wing, the body tube along a curved spine (tail
coiled into a spiral behind it, pale ash belly, dorsal spines, glowing cracks), near stubby
legs with pale claws, the near torn wing (bony fingers, holed membrane with a ragged edge),
head (swept-back ash horns, snout, hinged jaw, ember throat glow, glowing eye).
FX: violet glow specks, ash puffs, the spit of grey-violet fire.
Idle: coiled, it twitches and the cracks pulse with violet light.  Walk: a fast low scuttle,
the body rippling, tail swinging out behind.  Windup: rears up on its hind legs, wings flared,
the throat swelling with violet-orange fire (held).  Attack: lunges and spits a short cone of
grey-violet fire on frame 1.  Hurt: flinches back shedding puffs of ash.  Death: it crumbles
into a heap of ash that drifts away.
"""
import math

import numpy as np

import helpers_batch_a as hb
import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "hollowed_wyrmling",
    "cell": 128,
    "anchor": [64, 112],
    "flying": False,
    "hit_frame": 1,
}

# ---- palette: grey-violet ash scales, pale ash belly, torn wing membrane, violet glow, ember --
SCALE = px.material("hw_scale", "#c7c0d3", "#918aa3", "#676079", "#443e56", outline="#120e1b",
                    thresholds=(0.88, 0.52, 0.18))
BELLY = px.material("hw_belly", "#e8e3ea", "#c2bbc9", "#978fa5", "#6d6580", outline="#120e1b")
WING = px.material("hw_wing", "#a497c2", "#76699c", "#584c7c", "#3d335a", outline="#120c1e")
HORN = px.material("hw_horn", "#f0ecf2", "#cdc6d4", "#9d95aa", "#6e667f", outline="#141019")
ASH = px.material("hw_ash", "#e6e2ea", "#bab3c4", "#8e869c", "#686078", outline="#3a3446")
FIRE_GV = px.material("hw_fire_gv", "#d6c8ea", "#9f8cc0", "#76659a", "#524672", outline="#1d1530")
FIRE_V = px.material("hw_fire_v", "#f0dcff", "#c79bff", "#9a68dc", "#6a42a8", outline="#1d1030")
EMBER = px.material("hw_ember", "#ffd79a", "#f09a48", "#c2582e", "#853426", outline="#2a0e0c")
CRACK = px.rgb("#f2eef6")  # ash-white crack
GLOW = px.rgb("#c79bff")  # sickly violet glow
GLOW_HI = px.rgb("#efdcff")
GLOW_DIM = px.rgb("#9a78c8")
MOUTH = px.rgb("#1d1325")

# ---- poses --------------------------------------------------------------------------------
# bx, by    body offset       lift  front body raised about the hips (deg)   neck  neck rise (deg)
# head      head tilt (deg)   jaw   gape 0..1      coil  tail curl 1 (spiral) .. 0 (straight out)
# wave, ph  body ripple amplitude (px) / phase     sway  tail sway (px)
# feet      (dx, lift) near-fore, near-hind, far-fore, far-hind      wing  0 folded .. 1 flared
# eye       open|angry|squeeze|dead     glow  crack light 0..2     ember  throat fire 0..2
# spit      fire-spit life (None = off) ash  ash puff life (None = off)   crumble  0..1 (death)
# fade      opacity
DEFAULTS = dict(bx=0, by=0, lift=0, neck=0.0, head=0, jaw=0.0, coil=1.0, wave=0.0, ph=0.0, sway=0.0,
                feet=((0, 0),) * 4, wing=0.0, eye="open", glow=1, ember=1, spit=None, ash=None, crumble=0.0,
                fade=1.0, hit=False, reach=0.0)

TAU = 2 * math.pi

POSE = px.poses(DEFAULTS, {
    "idle": [  # coiled, a twitch of the head, the cracks pulse violet
        dict(glow=1, ember=1),
        dict(glow=2, ember=1, head=2, by=0),
        dict(glow=2, ember=2, head=-10, neck=6, jaw=0.25, wing=0.1),
        dict(glow=1, ember=1, head=-3),
    ],
    "walk": [  # a low fast scuttle: diagonal legs, the body ripples, tail swings out behind
        dict(feet=((2, 0), (-2, 1.5), (-2, 1.5), (2, 0)), coil=0.3, wave=0.8, ph=0.0, neck=18, head=-6, sway=1.0,
             reach=1.0),
        dict(feet=((1, 0), (-1, 2.5), (-1, 2.5), (1, 0)), coil=0.3, wave=0.8, ph=TAU / 6, neck=18, head=-7, by=-1,
             sway=0.5, glow=2, reach=1.0),
        dict(feet=((-1, 1), (1, 0), (1, 0), (-1, 1)), coil=0.3, wave=0.8, ph=TAU * 2 / 6, neck=18, head=-6,
             sway=-0.5, glow=2, reach=1.0),
        dict(feet=((-2, 1.5), (2, 0), (2, 0), (-2, 1.5)), coil=0.3, wave=0.8, ph=TAU * 3 / 6, neck=18, head=-5,
             sway=-1.0, reach=1.0),
        dict(feet=((-1, 2.5), (1, 0), (1, 0), (-1, 2.5)), coil=0.3, wave=0.8, ph=TAU * 4 / 6, neck=18, head=-7,
             by=-1, sway=-0.5, glow=1, reach=1.0),
        dict(feet=((1, 0), (-1, 1), (-1, 1), (1, 0)), coil=0.3, wave=0.8, ph=TAU * 5 / 6, neck=18, head=-6,
             sway=0.5, glow=1, reach=1.0),
    ],
    "windup": [  # rears up, wings flared, the throat swells with violet-orange fire - held
        dict(lift=10, neck=-6, head=8, jaw=0.2, wing=0.45, eye="angry", glow=2, ember=2, coil=0.85,
             feet=((1, 2), (0, 0), (1, 2), (0, 0))),
        dict(lift=17, neck=-14, head=16, jaw=0.45, wing=0.85, eye="angry", glow=2, ember=3, coil=0.75,
             feet=((1, 4), (0, 0), (2, 4), (0, 0)), bx=-1),
        dict(lift=20, neck=-16, head=20, jaw=0.55, wing=1.0, eye="angry", glow=2, ember=3, coil=0.75,
             feet=((1, 5), (0, 0), (2, 5), (0, 0)), bx=-2),
    ],
    "attack": [  # lunges forward and spits a short cone of grey-violet fire (frame 1)
        dict(lift=5, neck=30, head=-6, jaw=1.0, wing=0.7, eye="angry", glow=2, ember=3, coil=0.85, bx=-6,
             feet=((3, 1), (-1, 0), (3, 1), (-1, 0)), spit=0.15, reach=1.0),
        dict(lift=0, neck=40, head=-8, jaw=1.0, wing=0.5, eye="angry", glow=2, ember=2, coil=0.8, bx=-7,
             feet=((3, 0), (-1, 0), (3, 0), (-1, 0)), spit=0.5, hit=True, reach=1.5),
        dict(lift=0, neck=34, head=-4, jaw=0.6, wing=0.3, eye="angry", glow=1, ember=1, coil=0.85, bx=-7,
             feet=((2, 0), (0, 0), (2, 0), (0, 0)), spit=0.85, reach=1.0),
        dict(neck=10, head=-6, jaw=0.2, wing=0.1, glow=1, ember=1, coil=0.9, bx=-3),
    ],
    "hurt": [  # flinches back, ash puffs off the scales
        dict(bx=-3, lift=8, neck=-14, head=20, jaw=0.5, eye="squeeze", glow=0, ember=0, wing=0.5, coil=0.9,
             feet=((0, 2), (0, 0), (0, 2), (0, 0)), ash=0.25),
        dict(bx=-2, lift=4, neck=-8, head=10, jaw=0.3, eye="squeeze", glow=1, ember=1, wing=0.2, ash=0.6),
    ],
    "death": [  # shudders, slumps and crumbles into a heap of ash that drifts away
        dict(bx=-3, lift=8, neck=-14, head=20, jaw=0.5, eye="squeeze", glow=0, ember=0, wing=0.5, coil=0.9,
             feet=((0, 2), (0, 0), (0, 2), (0, 0)), ash=0.25),
        dict(bx=-3, neck=64, head=-18, jaw=0.4, eye="dead", glow=0, ember=0, wing=0.2, coil=0.8, ash=0.5),
        dict(bx=-3, neck=64, head=-18, jaw=0.4, eye="dead", glow=0, ember=0, wing=0.2, coil=0.8, crumble=0.35,
             ash=0.2),
        dict(bx=-3, neck=64, head=-18, jaw=0.4, eye="dead", glow=0, ember=0, wing=0.2, coil=0.8, crumble=0.75,
             ash=0.55, fade=0.6),
        dict(bx=-3, neck=64, head=-18, jaw=0.4, eye="dead", glow=0, ember=0, wing=0.2, coil=0.8, crumble=1.0,
             ash=0.9, fade=0.3),
    ],
})

# tail control points behind the hips: coiled spiral vs stretched out (hip-relative)
TAIL_COIL = ((-4.5, 0.8), (-9.0, 0.4), (-12.0, -3.0), (-10.8, -7.2), (-7.0, -7.6), (-6.4, -4.8))
TAIL_OUT = ((-5.0, 0.6), (-10.0, 1.0), (-14.5, 1.0), (-18.5, 0.2), (-21.5, -0.8), (-23.5, -2.2))
TAIL_R = (3.8, 3.1, 2.4, 1.8, 1.3, 0.8)


def _catmull(points, per=4):
    return hb.catmull(points, per=per)


def _leg(cv, hip, foot, far, front):
    shade = "dark" if far else "two"
    knee = (hip[0] + (-1.6 if front else 1.6), hip[1] + (foot[1] - hip[1]) * 0.55)
    cv.limb([hip, knee, (foot[0], foot[1] - 1.2)], [2.3, 1.8, 1.4], SCALE, shade=shade, name="leg")
    cv.ellipse(foot[0] + 0.6, foot[1] - 0.9, 2.0, 1.0, SCALE, shade="dark" if far else "two", name="foot")
    if not far:
        cv.pixels([(math.floor(foot[0] + 2.0), math.floor(foot[1] - 0.6))], HORN.base, name="claw")


def _wing(cv, S, spread, far, key):
    """A small torn bat wing: the arm rises from the shoulder to the wrist, three bony fingers
    fan back from it, the membrane between them is holed and bitten along its edge."""
    mat = WING
    name = "wing_f" if far else "wing"
    arm_a = 116 - 36 * spread  # folded: up and back; flared: up and forward
    W = px.polar(S, arm_a, 6.6 + 1.6 * spread)
    fingers = []
    for k, (a0, a1, ln) in enumerate(((176, 140, 8.6), (202, 172, 7.4), (226, 206, 5.8))):
        a = a0 + (a1 - a0) * spread
        fingers.append(px.polar(W, a, ln * (0.9 + 0.3 * spread)))
    edge = [S, W, fingers[0]]
    for k in range(len(fingers) - 1):  # scalloped trailing edge, one bite torn deeper
        a, b = fingers[k], fingers[k + 1]
        m = px.lerp_pt(a, b, 0.5)
        deep = 0.42 if (k + key) % 2 == 0 else 0.26
        edge += [px.lerp_pt(a, px.lerp_pt(m, W, deep), 0.7), px.lerp_pt(m, W, deep),
                 px.lerp_pt(b, px.lerp_pt(m, W, deep), 0.6), b]
    tail_pt = px.lerp_pt(fingers[-1], S, 0.55)
    edge += [(tail_pt[0], tail_pt[1] + 0.8), (S[0] - 1.5, S[1] + 1.0)]
    cv.polygon(edge, mat, shade="dark" if far else "two", name=name, sep=False if far else "deep")
    if not far:  # a hole torn through the membrane, then the bones over it
        h = px.lerp_pt(W, px.lerp_pt(fingers[0], fingers[1], 0.5), 0.55)
        cv.ellipse(h[0], h[1], 1.0, 0.9, mat, erase=True)
        cv.limb([S, W], [1.3, 0.9], HORN.step(1), shade="two", name=name)
        for f in fingers:
            cv.limb([W, f], [0.7, 0.45], HORN.step(1), shade="two", name=name)
        cv.pixel(math.floor(W[0]), math.floor(W[1]) - 1, HORN.light, name=name)  # wrist claw
    return W


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    cv.snap_ground = action == "death" and frame >= 1
    ground = cv.ground
    C = (cv.gx - 2.0 + p.bx, ground - 7.6 + p.by)
    H0 = (C[0] - 5.0, C[1] + 0.4)  # hips

    def L(pt):  # front-body points follow the rear-up
        return px.rot_pt(pt, p.lift, (H0[0], ground))

    def wv(pt, k):
        return (pt[0], pt[1] + p.wave * math.sin(p.ph + k * 1.4))

    S0 = L(wv((C[0] + 5.5, C[1] - 1.0), 2))
    Cm = L(wv(C, 1))
    # S-neck: up from the shoulders, then curving forward under the head (``neck`` leans it)
    up = 90 - p.neck
    N1 = px.polar(S0, up + p.lift, 6.2)
    N2 = px.polar(N1, up - 52 + p.lift, 5.2 + p.reach)
    # tail: blend coiled spiral <-> stretched out, swaying
    tail = []
    for k, ((ax, ay), (bx_, by_)) in enumerate(zip(TAIL_COIL, TAIL_OUT)):
        c = p.coil
        tx, ty = ax * c + bx_ * (1 - c), ay * c + by_ * (1 - c)
        ty += p.sway * (k / 5.0) ** 1.5 * 1.5
        tail.append((H0[0] + tx, H0[1] + ty))
    ctrl = list(reversed(tail)) + [wv(H0, 0), Cm, S0, N1, N2]
    radii_c = list(reversed(TAIL_R)) + [4.2, 4.6, 4.2, 2.8, 2.3]
    sp = _catmull(ctrl, per=4)
    # radius per sample: interpolate the control radii along the samples
    rs = []
    for i in range(len(sp)):
        t = i / 4.0
        j = min(len(radii_c) - 2, int(t))
        f = t - j
        rs.append(radii_c[j] + (radii_c[j + 1] - radii_c[j]) * f)

    # ---- legs (behind the body), far wing ------------------------------------------------------
    hips = {"nf": (S0[0] + 0.5, S0[1] + 2.5), "nh": (H0[0] + 0.5, H0[1] + 2.5),
            "ff": (S0[0] + 2.2, S0[1] + 1.8), "fh": (H0[0] + 2.2, H0[1] + 1.8)}
    feet = {}
    for i, name in enumerate(("nf", "nh", "ff", "fh")):
        dx, lf = p.feet[i]
        base_x = hips[name][0] + (1.0 if name[1] == "f" else 0.5)
        if p.lift and name[1] == "f":  # forelegs lifted off the ground with the rear-up
            feet[name] = (hips[name][0] + 1.5 + dx, min(ground, hips[name][1] + 5.0))
        else:
            feet[name] = (base_x + dx, ground - lf)
    _leg(cv, hips["fh"], feet["fh"], True, False)
    _leg(cv, hips["ff"], feet["ff"], True, True)
    wing_root = (S0[0] - 2.6, S0[1] - 3.2)
    _wing(cv, (wing_root[0] + 2.6, wing_root[1] - 0.8), p.wing, True, 1)
    _leg(cv, hips["nh"], feet["nh"], False, False)
    _leg(cv, hips["nf"], feet["nf"], False, True)

    # ---- body tube -------------------------------------------------------------------------------
    cv.limb(sp, rs, SCALE, name="body", sep="deep")
    # pale ash belly along the underside, dorsal spine nubs along the top
    n = len(sp)
    under, spines = [], []
    for k in range(2, n - 2):
        nx, ny = hb.normal_at(sp, k)  # left of travel = the top for a right-going body
        under.append((sp[k][0] - nx * rs[k] * 0.6, sp[k][1] - ny * rs[k] * 0.6))
        if k % 3 == 0 and k > n * 0.25:
            spines.append((sp[k], (nx, ny), rs[k]))
    cv.limb(under, [r * 0.45 for r in rs[2:n - 2]], BELLY, shade="two", decal=True, clip="body", name="body")
    for (q, (nx, ny), r) in spines:
        base = (q[0] + nx * (r - 0.6), q[1] + ny * (r - 0.6))
        tip = (base[0] + nx * 2.2 - ny * -1.2, base[1] + ny * 2.2 + nx * -1.2)
        cv.polygon([(base[0] - 1.0, base[1]), tip, (base[0] + 1.0, base[1] + 0.3)], HORN, shade="two",
                   name="spine", under=True)
    # cracks: ash-white seams leaking violet light
    for k0, (a, b, c) in enumerate(((0.42, (-0.5, 0.9), (0.6, 0.2)), (0.58, (0.4, -0.8), (0.8, 0.5)),
                                    (0.74, (-0.6, 0.5), (0.3, -0.7)))):
        i = int(a * (n - 1))
        q = sp[i]
        r = rs[i]
        p0 = (q[0] + b[0] * r * 0.8, q[1] + b[1] * r * 0.8)
        p1 = (q[0] + c[0] * r * 0.4, q[1] + c[1] * r * 0.4)
        p2 = (q[0] - b[0] * r * 0.5 + 1.2, q[1] - b[1] * r * 0.4 + 0.8)
        for u, v in ((p0, p1), (p1, p2)):
            cv.line((math.floor(u[0]), math.floor(u[1])), (math.floor(v[0]), math.floor(v[1])), CRACK,
                    decal=True, clip="body", name="crack")
    if p.glow > 0:  # the violet light leaking round the cracks pulses dim / bright
        glow = cv.mask_of("crack")
        ring = px.dilate(glow) & ~glow & cv.mask_of("body")
        cv._commit(ring, np.where(ring, 1, -1).astype(np.int8), px.flat(GLOW if p.glow >= 2 else GLOW_DIM),
                   decal=True, name="glowring")

    # ---- near wing -------------------------------------------------------------------------------
    _wing(cv, wing_root, p.wing, False, 0)

    # ---- head ------------------------------------------------------------------------------------
    d = (N2[0] - N1[0], N2[1] - N1[1])
    neck_dir = math.degrees(math.atan2(-d[1], d[0]))
    ha = p.head + 0.3 * (neck_dir - 38)
    Hc = px.polar(N2, ha, 2.2)
    mouth, throat = _head(cv, Hc, ha, p)

    # ---- FX ----------------------------------------------------------------------------------
    fx = cv.layer(above=True, outline=False)
    if p.glow >= 2 and p.crumble <= 0:  # violet motes rising off the cracks
        for k, (ox, oy) in enumerate(((-3.0, -7.0), (4.0, -8.0))):
            if (k + frame) % 2 == 0:
                x, y = math.floor(C[0] + ox), math.floor(C[1] + oy - (frame % 3))
                fx.line((x, y), (x, y + 1), GLOW if k else GLOW_HI, name="mote")
    if p.ember >= 3 and p.spit is None:  # the swollen throat pulses with violet light
        px.glow_ring(fx, throat[0] + 0.5, throat[1] + 0.5, 4.5, GLOW, thickness=1.0)
        for ang in (20, 160, 250):
            q = px.polar((throat[0] + 0.5, throat[1] + 0.5), ang, 6.5)
            fx.line((math.floor(q[0]), math.floor(q[1])), (math.floor(q[0]), math.floor(q[1]) - 1), GLOW_HI, name="mote")
    if p.spit is not None:
        _spit(cv, mouth, ha, p.spit, p.hit)
    if p.ash is not None:
        top = cv.layer(above=True, outline=True)
        for k, (ox, oy) in enumerate(((-4.0, -6.0), (5.0, -7.0), (-10.0, -3.0))):
            hb.mist_puff(top, C[0] + ox, C[1] + oy, p.ash, size=0.7, seed=k + frame * 3, mat=ASH, count=3,
                         spread=0.8)
    if p.crumble > 0:
        _crumble(cv, p, frame)


def _head(cv, Hc, ha, p):
    """Small wyrm head: swept-back ash horns, snout, hinged jaw, ember throat, glowing eye.
    Returns (mouth point, throat point) in canvas coords."""
    with cv.xform(px.rotate(ha, Hc)):
        hinge = (Hc[0] - 0.8, Hc[1] + 1.6)
        jaw_a = -34 * p.jaw
        # far horn, lower jaw, skull + snout, near horn
        cv.limb([(Hc[0] - 0.6, Hc[1] - 2.4), (Hc[0] - 4.0, Hc[1] - 3.8), (Hc[0] - 6.6, Hc[1] - 3.4)], [0.95, 0.7, 0.45],
                HORN, shade="dark", name="horn")
        with cv.xform(px.rotate(jaw_a, hinge)):
            cv.limb([hinge, (Hc[0] + 3.4, Hc[1] + 2.4), (Hc[0] + 6.0, Hc[1] + 2.0)], [1.9, 1.4, 0.9], SCALE,
                    shade="nolight", name="jaw")
            lo_tip = cv.tp((Hc[0] + 5.8, Hc[1] + 1.6))
        skull = cv.geom_ellipse(Hc[0], Hc[1], 3.9, 3.2)
        snout = cv.geom_limb([(Hc[0] + 1.0, Hc[1] + 0.2), (Hc[0] + 6.6, Hc[1] + 1.0)], [2.6, 1.6])
        cut = cv.mask_polygon([hinge, (Hc[0] + 12, hinge[1] - 0.6), (Hc[0] + 12, Hc[1] + 9), (hinge[0], Hc[1] + 9)]) \
            if p.jaw > 0.2 else None
        cv.draw_geom(cv.union(skull, snout, weights=[1.0, 0.8]), SCALE, name="head", sep="deep", minus=cut)
        if p.jaw > 0.2:  # the gape glows with the fire in its throat
            lo = px.rot_pt((Hc[0] + 5.6, hinge[1] + 0.3), jaw_a, hinge)
            gape = [(hinge[0] - 0.3, hinge[1]), (Hc[0] + 6.4, hinge[1] - 0.2), lo]
            cv.polygon(gape, px.flat(MOUTH), under=True, name="mouth")
            if p.ember >= 2:
                inner = [px.lerp_pt(gape[0], gape[1], 0.1), px.lerp_pt(gape[0], gape[1], 0.6),
                         px.lerp_pt(gape[0], lo, 0.6)]
                cv.polygon(inner, EMBER if p.ember >= 3 else FIRE_V, shade="flat", decal=True, clip="mouth",
                           name="mouth")
        else:
            cv.line((math.floor(hinge[0] + 0.5), math.floor(hinge[1])), (math.floor(Hc[0] + 5.8), math.floor(hinge[1] - 0.4)),
                    SCALE.step(2), decal=True, clip="head", name="head")
        cv.pixel(math.floor(Hc[0] + 5.6), math.floor(Hc[1] - 0.6), SCALE.deep, name="nostril")
        cv.limb([(Hc[0] - 0.8, Hc[1] - 2.2), (Hc[0] - 4.2, Hc[1] - 3.2), (Hc[0] - 7.2, Hc[1] - 2.4)], [1.1, 0.8, 0.45],
                HORN, shade="two", name="horn", sep="deep")
        # an ash-white crack across the skull
        cv.line((math.floor(Hc[0] - 2.0), math.floor(Hc[1] + 0.5)), (math.floor(Hc[0] - 0.5), math.floor(Hc[1] - 1.2)),
                CRACK, decal=True, clip="head", name="head")
        E = cv.tp((Hc[0] + 1.2, Hc[1] - 1.2))
        mouth = cv.tp((Hc[0] + 6.6, Hc[1] + 1.2))
        throat = cv.tp((Hc[0] - 2.6, Hc[1] + 3.0))
    # ember glow smouldering in the throat (under the jaw, down the neck)
    if p.ember > 0:
        r = {1: 1.1, 2: 1.7, 3: 2.5}[min(3, p.ember)]
        cv.ellipse(throat[0], throat[1], r + 0.5, r, EMBER, shade="soft" if p.ember >= 2 else "nolight",
                   decal=True, clip="body", name="throat")
        if p.ember >= 3:  # violet fire ringing the swollen throat
            m = cv.mask_ellipse(throat[0], throat[1], r + 1.4, r + 1.0) & ~cv.mask_of("throat")
            m &= cv.mask_of(["body"])
            cv._commit(m, np.where(m, 1, -1).astype(np.int8), px.flat(GLOW), decal=True, name="throatglow")
    # the empty, glowing violet eye
    ex, ey = math.floor(E[0]), math.floor(E[1])
    if p.eye == "squeeze":
        cv.stamp(["v.", ".v", "v."], ex, ey - 1, {"v": GLOW}, name="eye")
    elif p.eye == "dead":
        cv.stamp(["k.k", ".k.", "k.k"], ex - 1, ey - 1, {"k": SCALE.deep}, name="eye")
    else:
        cv.stamp(["ww", "wv"], ex, ey, {"w": GLOW_HI, "v": GLOW}, name="eye")
        cv.pixels([(ex - 1, ey), (ex - 1, ey + 1)], GLOW_DIM, name="eyehalo", decal=True)
        if p.eye == "angry":  # a heavy brow ridge slanting down toward the snout
            cv.pixels([(ex - 1, ey - 1), (ex, ey - 1), (ex + 1, ey - 1), (ex + 2, ey)], SCALE.deep, name="brow")
    return mouth, throat


def _spit(cv, mouth, ha, t, hit):
    """A short cone of grey-violet fire: grey-violet outside, violet inside, an ember core."""
    fl = cv.layer(above=True, outline=True)
    a = math.radians(ha - 8)
    dx, dy = math.cos(a), -math.sin(a)
    nx, ny = -dy, dx
    ln = (4.0 + 10.0 * min(1.0, t * 1.6)) * (1.0 if t < 0.7 else 0.8)
    ln = min(ln, (cv.w - 7.0 - mouth[0]) / max(0.3, dx) - 2.5)
    start = 1.0 + (8.0 * (t - 0.6) if t > 0.6 else 0.0)  # the cone detaches from the mouth as it fades
    half = 0.44

    def cone(lf, hf, off=0.0):
        pts = []
        steps = 6
        for i in range(steps + 1):  # upper edge, rippled
            s = i / steps
            w = (1.2 + s * ln * half) * hf
            wob = 0.5 * math.sin(s * 9 + t * 7)
            L = start + ln * lf * s
            pts.append((mouth[0] + dx * L + nx * (w + wob), mouth[1] + dy * L + ny * (w + wob)))
        tip = (mouth[0] + dx * (start + ln * lf + 1.5), mouth[1] + dy * (start + ln * lf + 1.5))
        low = []
        for i in range(steps, -1, -1):
            s = i / steps
            w = (1.2 + s * ln * half) * hf
            wob = 0.5 * math.sin(s * 8 + t * 5 + 1)
            L = start + ln * lf * s
            low.append((mouth[0] + dx * L - nx * (w + wob), mouth[1] + dy * L - ny * (w + wob)))
        return pts + [tip] + low

    if t < 0.95:
        fl.polygon(cone(1.0, 1.0), FIRE_GV, shade="soft", name="spit")
        fl.polygon(cone(0.75, 0.62), FIRE_V, shade="soft", decal=True, clip="spit", name="spit")
        if t < 0.7:
            fl.polygon(cone(0.45, 0.3), EMBER, shade="flatlight", decal=True, clip="spit", name="spit")
        hc.thin_body(fl, fl.mask_of("spit"))
    top = cv.layer(above=True, outline=False)
    if hit:
        tip = (mouth[0] + dx * (start + ln + 1.0), mouth[1] + dy * (start + ln + 1.0))
        px.impact(top, min(cv.w - 7, tip[0]), tip[1], size=4, color=GLOW_HI, core=EMBER.light)
    if t > 0.6:  # ash specks drifting off the dying flame
        hc.ember_specks(top, [(mouth[0] + dx * 10 + 1, mouth[1] + dy * 10 - 3, 0),
                              (mouth[0] + dx * 14, mouth[1] + dy * 14 + 2, 2)], colors=(ASH.light, GLOW_DIM))


def _crumble(cv, p, frame):
    """Death: the body breaks into chunks of ash that slump to the ground and blow away."""
    c = p.crumble
    ys, xs = np.nonzero(cv.filled)
    if not len(xs):
        return
    x0, x1 = xs.min(), xs.max()
    seeds = []
    for k in range(7):
        sx = x0 + (x1 - x0) * (k + 0.5) / 7
        col = cv.filled[:, int(sx)]
        rows = np.nonzero(col)[0]
        sy = rows.mean() if len(rows) else cv.gy - 6
        seeds.append((sx, sy - 2 + 4 * (k % 2)))
    hb.crumble(cv, seeds, c, cv.gy - 2, seed=11, crack=True, spread=0.6)
    if c > 0.3:  # the heap blows away from the back first
        edge = x0 + (x1 - x0) * (c - 0.3) * 1.3
        gone = hb.sweep_mask(cv, edge, seed=frame, jag=1.5, direction=-1) & cv.filled
        hc.erase_mask(cv, gone)
        hc.drop_specks(cv, 3)
    # recolour what is left toward pale ash
    m = cv.filled.copy()
    cv._commit(m, np.where(m, cv.band, -1).astype(np.int8), ASH if c > 0.5 else SCALE, decal=True, name="ash")
