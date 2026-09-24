"""Hollow stag - a grey-white Hollow stag with broken branching antlers, empty white eyes
and grey mist seeping off it.

View: side, facing right.  ~56 art px tall to the antler tips, ~44 long on a 96 px art
canvas (cell 192).
Parts, back to front: far legs, far antler, short flag tail, near hind leg, body (haunch,
barrel, deep chest) + raised neck + head as one form, dark hollow cracks, near foreleg,
ear, near antler (branching, two tines snapped off), empty white eye.  FX: mist wisps
rising off the back, dust from the hoof stamp.
Windup: the head drops, antlers levelled, a forehoof stamps (held); attack: an antler
charge (hit on frame 2); death: the legs fold and it collapses into mist.
"""
import math

import numpy as np

import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "hollow_stag",
    "cell": 192,
    "anchor": [96, 168],
    "flying": False,
    "hit_frame": 2,
    "airborne": [["death", 3], ["death", 4]],
}

# ---- palette: Hollow grey-white family -------------------------------------------------------
HIDE = px.material("stag_hide", "#eef2ef", "#bcc6c8", "#8a979d", "#5f6a72", outline="#161c21",
                   thresholds=(0.9, 0.55, 0.2))
HIDE_D = px.material("stag_hide_far", "#a9b4b8", "#87949a", "#687379", "#4a545b", outline="#161c21")
ANTLER = px.material("stag_antler", "#e4e8e4", "#aeb7b8", "#7e8a90", "#56616a", outline="#141a1f")
HOOF = px.material("stag_hoof", "#6e777e", "#4d555c", "#384046", "#262c31", outline="#0e1216")
VOID = px.rgb("#2e363d")
EYE_W = px.EYE_WHITE

# ---- poses ------------------------------------------------------------------------------------
# bx, by   body offset     crouch  lower body     pitch  body tilt (deg)   neck  neck angle (deg)
# head     head tilt       ear     ear angle      feet   (dx, lift) near-front, far-front, near-hind, far-hind
# dust     stamp dust life (None = off)   mist  wisp phase    sink  0..1 legs folded (death)
# dissolve 0..1 turned to mist            fade  opacity
DEFAULTS = dict(bx=0, by=0, crouch=0, pitch=0, neck=62, head=0, ear=0, feet=((0, 0), (0, 0), (0, 0), (0, 0)),
                dust=None, mist=0.0, sink=0.0, dissolve=0.0, hit=False, fade=1.0, breathe=0.0, eye="open")

POSE = px.poses(DEFAULTS, {
    "idle": [
        dict(mist=0.0),
        dict(mist=1.0, breathe=0.4, head=-2),
        dict(mist=2.0, breathe=0.6, head=-3, ear=-10),
        dict(mist=3.0, breathe=0.2),
    ],
    "walk": [  # stately trot: diagonal pairs swap
        dict(feet=((3, 0), (-3, 2), (-3, 2), (3, 0)), mist=0.0),
        dict(feet=((2, 0), (-1, 4), (-1, 3), (1, 0)), mist=0.8, by=-1, head=1),
        dict(feet=((-1, 1), (2, 1), (2, 0), (-1, 1)), mist=1.6),
        dict(feet=((-3, 2), (3, 0), (3, 0), (-3, 2)), mist=2.4),
        dict(feet=((-1, 4), (2, 0), (1, 0), (-1, 3)), mist=3.2, by=-1, head=1),
        dict(feet=((2, 1), (-1, 1), (-1, 1), (2, 0)), mist=4.0),
    ],
    "windup": [  # head drops to level the antlers, a forehoof lifts and stamps - held
        dict(neck=40, head=-20, crouch=1, bx=-1, feet=((3, 6), (0, 0), (0, 0), (0, 0)), mist=0.5, ear=-20),
        dict(neck=24, head=-34, crouch=2, bx=-2, feet=((1, 0), (0, 0), (0, 0), (0, 0)), dust=0.2, mist=1.0,
             ear=-30, pitch=-3),
        dict(neck=20, head=-38, crouch=3, bx=-3, feet=((2, 0), (1, 0), (-1, 0), (-1, 0)), dust=0.55, mist=1.5,
             ear=-35, pitch=-4),
    ],
    "attack": [  # antler charge: drives forward, antlers first; they strike on frame 2
        dict(neck=20, head=-38, bx=2, pitch=-4, crouch=2, feet=((4, 3), (3, 2), (-3, 0), (-4, 0)), mist=2.0,
             dust=0.1, ear=-35),
        dict(neck=22, head=-36, bx=8, pitch=-5, crouch=1, feet=((5, 1), (4, 3), (-4, 2), (-5, 0)), mist=2.5,
             dust=0.4, ear=-35),
        dict(neck=26, head=-30, bx=7, pitch=-3, feet=((3, 0), (4, 0), (-3, 0), (-4, 1)), mist=3.0, hit=True,
             ear=-30),
        dict(neck=48, head=-8, bx=7, feet=((1, 0), (1, 0), (-1, 0), (-1, 0)), mist=3.5, ear=-10),
    ],
    "hurt": [
        dict(bx=-4, by=-2, neck=76, head=18, pitch=6, eye="squeeze", ear=-35, feet=((1, 4), (0, 3), (0, 0), (0, 0)),
             mist=1.0),
        dict(bx=-2, neck=70, head=8, pitch=3, eye="squeeze", ear=-20, mist=2.0),
    ],
    "death": [  # buckles, sinks to the ground and unravels into grey mist
        dict(bx=-4, by=-2, neck=78, head=20, pitch=6, eye="squeeze", ear=-35, feet=((1, 4), (0, 3), (0, 0), (0, 0)),
             mist=1.0),
        dict(bx=-4, neck=40, head=-20, sink=0.5, eye="squeeze", ear=-40, mist=2.0),
        dict(bx=-4, neck=24, head=-30, sink=1.0, eye="squeeze", ear=-40, mist=3.0, dissolve=0.3),
        dict(bx=-4, neck=20, head=-32, sink=1.0, eye="squeeze", ear=-40, mist=4.0, dissolve=0.65, fade=0.6),
        dict(bx=-4, neck=20, head=-32, sink=1.0, eye="squeeze", ear=-40, mist=5.0, dissolve=1.0, fade=0.3),
    ],
})


# ---- parts ------------------------------------------------------------------------------------
def _front_leg(cv, hip, foot, far, sink):
    fx, fy = foot
    mat = HIDE_D if far else HIDE
    shade = "dark" if far else "two"
    if sink > 0:  # folded under the chest
        knee = (hip[0] + 4.0 * sink, hip[1] + 6.0 - 2.0 * sink)
        hoof = (knee[0] - 6.0 * sink, fy - 1.2)
        cv.limb([hip, knee, hoof], [3.0, 1.8, 1.4], mat, shade=shade, name="leg")
        cv.ellipse(hoof[0] - 0.6, hoof[1], 1.6, 1.2, HOOF, shade="dark" if far else "two", name="hoof")
        return
    elbow = (hip[0] - 0.6 + (fx - hip[0]) * 0.25, hip[1] + (fy - hip[1]) * 0.35)
    knee = (fx - 0.6 + (elbow[0] - fx) * 0.15, fy - 7.5)
    cv.limb([hip, elbow, knee, (fx, fy - 2.4)], [3.2, 2.0, 1.5, 1.2], mat, shade=shade, name="leg",
            sep=False if far else "deep")
    cv.polygon([(fx - 1.2, fy - 2.8), (fx + 1.0, fy - 2.8), (fx + 2.0, fy + 0.9), (fx - 1.4, fy + 0.9)], HOOF,
               shade="dark" if far else "two", name="hoof")


def _hind_leg(cv, hip, foot, far, sink, crouch):
    fx, fy = foot
    mat = HIDE_D if far else HIDE
    shade = "dark" if far else "two"
    if sink > 0:
        knee = (hip[0] + 5.0, hip[1] + 4.0)
        hock = (hip[0] - 3.0 * sink, fy - 1.6)
        cv.limb([hip, knee, hock, (hock[0] + 4.0, fy - 1.2)], [4.2, 2.6, 1.6, 1.3], mat, shade=shade, name="leg")
        return
    stifle = (hip[0] + 3.0, hip[1] + 5.0 - crouch * 0.3)
    hock = (fx - 3.0 - crouch * 0.4, fy - 9.0 + crouch * 0.3)
    cv.limb([hip, stifle, hock, (fx, fy - 2.4)], [4.4, 2.8, 1.5, 1.2], mat, shade=shade, name="leg")
    cv.polygon([(fx - 1.2, fy - 2.8), (fx + 1.0, fy - 2.8), (fx + 2.0, fy + 0.9), (fx - 1.4, fy + 0.9)], HOOF,
               shade="dark" if far else "two", name="hoof")


def _antler(cv, base, far, lean):
    """Branching antler: a main beam curving up and back with forward tines; two tines are
    snapped off short with jagged ends (broken)."""
    mat = ANTLER
    shade = "dark" if far else "two"
    name = "antler_far" if far else "antler"
    a0 = 100 + lean
    pts = [base]
    q = base
    for k, (ln, da) in enumerate(((5.0, 0), (5.0, 18), (4.6, 22), (3.8, 16))):
        q = px.polar(q, a0 + da, ln)
        pts.append(q)
    cv.limb(pts, [1.8, 1.6, 1.3, 1.0, 0.6], mat, shade=shade, name=name)
    # tines off the beam (forward and up), some broken
    tines = ((1, -40, 5.0, False), (2, -25, 6.0, True), (3, -10, 4.6, False), (2, 60, 3.0, True))
    for (i, da, ln, broken) in tines:
        root = pts[i]
        tip = px.polar(root, a0 + da, ln * (0.5 if broken else 1.0))
        cv.limb([root, tip], [1.1, 0.8 if broken else 0.5], mat, shade=shade, name=name)
        if broken and not far:  # jagged snapped end
            cv.pixel(math.floor(tip[0]), math.floor(tip[1]) - 1, ANTLER.deep, name=name)
    return pts[-1]


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    ground = cv.ground
    sk = p.sink
    C = (cv.gx - 1 + p.bx, ground - 25.0 + p.by + p.crouch + sk * 12.0)
    br = p.breathe
    R = (C[0] - 11.5, C[1] - 0.5)
    K = (C[0] + 8.5, C[1] + 0.3)
    body_x = [px.rotate(p.pitch, C)]

    def B(pt):
        return px.rot_pt(pt, p.pitch, C)

    def foot(hx, i):
        f = p.feet[i]
        return (hx + f[0], ground - f[1])

    hips = {"nf": (K[0] + 1.0, K[1] + 4.0), "ff": (K[0] + 3.2, K[1] + 3.6),
            "nh": (R[0] + 0.5, R[1] + 3.0), "fh": (R[0] + 2.8, R[1] + 2.6)}
    wisps = cv.layer(above=False, outline=True)
    _front_leg(cv, B(hips["ff"]), foot(hips["ff"][0] + 0.4, 1), True, sk)
    _hind_leg(cv, B(hips["fh"]), foot(hips["fh"][0] + 1.0, 3), True, sk, p.crouch)
    N0 = (K[0] + 3.0, K[1] - 4.0)
    H = px.polar(N0, p.neck, 10.5)
    with cv.xform(*body_x):
        with cv.xform(px.rotate(p.head, H)):
            _antler(cv, (H[0] - 0.4, H[1] - 3.4), True, 12)
        # flag tail
        cv.polygon([(R[0] - 6.0, R[1] - 5.0), (R[0] - 10.0, R[1] - 3.4), (R[0] - 9.0, R[1] - 0.4),
                    (R[0] - 5.4, R[1] - 1.0)], HIDE, shade="two", name="tail")
    _hind_leg(cv, B(hips["nh"]), foot(hips["nh"][0] + 0.6, 2), False, sk, p.crouch)
    with cv.xform(*body_x):
        body_g = [cv.geom_ellipse(R[0], R[1], 8.4, 7.4 + br * 0.3, angle=-6),
                  cv.geom_limb([(R[0] + 2.0, R[1] - 0.6), (C[0], C[1] - 1.2 - br * 0.3), (K[0] - 2.0, K[1])],
                               [6.4, 5.8 + br * 0.4, 7.0]),
                  cv.geom_ellipse(K[0], K[1] + 0.4, 8.2, 8.4 + br, angle=12)]
        with cv.xform(px.rotate(p.head, H)):
            head_g = [cv.geom_ellipse(H[0], H[1], 3.8, 3.4, angle=-10),
                      cv.geom_limb([(H[0] + 1.5, H[1] + 0.4), (H[0] + 7.6, H[1] + 3.2)], [2.8, 1.8])]
        neck_g = cv.geom_limb([(N0[0] - 2.0, N0[1] + 3.0), px.lerp_pt(N0, H, 0.55), H], [6.0, 4.0, 3.0])
        cv.draw_geom(cv.union(*body_g, neck_g, *head_g, weights=[0.9, 0.8, 1.0, 0.7, 0.9, 0.8]), HIDE,
                     name="body", sep="deep")
        # pale belly and throat, dark Hollow cracks in the flank
        cv.limb([(R[0] + 3.0, R[1] + 5.6), (K[0] - 1.0, K[1] + 7.4)], [1.4, 2.4], HIDE.step(-1), shade="two",
                decal=True, clip="body")
        for a, b, c in (((-6.0, -3.0), (-3.0, 0.5), (-4.0, 3.5)), ((2.0, -4.0), (4.0, -1.0), (6.5, -1.5))):
            pts = [(C[0] + x, C[1] + y) for x, y in (a, b, c)]
            for q0, q1 in zip(pts, pts[1:]):
                cv.line((round(q0[0]), round(q0[1])), (round(q1[0]), round(q1[1])), VOID, decal=True, name="body")
            cv.pixel(round(pts[1][0]) + 1, round(pts[1][1]), EYE_W, decal=True, name="body")
        with cv.xform(px.rotate(p.head, H)):
            # ear, nose, empty white eye in a dark socket
            ep = (H[0] - 2.0, H[1] - 2.4)
            cv.ellipse(*px.rot_pt((ep[0] - 3.0, ep[1] - 0.4), p.ear, ep), 3.2, 1.4, HIDE,
                       angle=160 + p.ear, name="ear", sep="deep")
            cv.pixels([(round(H[0] + 7.8), round(H[1] + 2.4))], VOID, name="nose")
            ex, ey = round(H[0] + 0.6), round(H[1] - 1.2)
            if p.eye == "squeeze":
                cv.pixels([(ex - 1, ey), (ex, ey + 1), (ex + 1, ey + 1), (ex + 2, ey)], VOID, name="eye")
            else:
                hc.eye_stamp(cv, ["kkk", "kwk", "kwk"], ex - 1, ey - 1, {"k": VOID, "w": EYE_W})
            _antler(cv, (H[0] + 0.4, H[1] - 3.4), False, 0)
            prong = cv.tp(px.polar((H[0] + 0.4, H[1] - 3.4), 70, 8.0))
    _front_leg(cv, B(hips["nf"]), foot(hips["nf"][0], 0), False, sk)

    # grey mist seeping off the back and drifting away behind it, and pooling at the hooves
    ph = p.mist
    for k in range(3):
        age = ((ph * 0.3 + k * 0.34) % 1.0)
        q = B((R[0] - 5.0 - age * 10.0, C[1] - 9.0 + k * 4.5 - age * 4.0))
        r = 3.8 - 1.6 * age
        wisps.ellipse(q[0], q[1], r, 1.5, hc.HOLLOW_MIST, shade="soft", name="mist")
        wisps.ellipse(q[0] + r * 0.7, q[1] - 1.0, r * 0.5, 1.3, hc.HOLLOW_MIST, shade="soft", name="mist")
    for k, dx in enumerate((-4.0, 10.0)):  # vapour curling off the back
        age = ((ph * 0.3 + k * 0.5) % 1.0)
        q = B((C[0] + dx - age * 4.0, C[1] - 9.5 - age * 5.0))
        wisps.ellipse(q[0], q[1], 2.6 - age, 1.3, hc.HOLLOW_MIST, shade="soft", name="mist")
    if p.dust is not None:
        fx = cv.layer(above=True, outline=True)
        px.dust(fx, hips["nf"][0] + 1, cv.gy - 1, p.dust, size=1.0, direction=-1)
        px.dust(fx, hips["nf"][0] + 4, cv.gy - 1, p.dust * 0.8, size=0.8, direction=1)
    if p.dissolve > 0:  # collapses into mist from the rump forward
        d = p.dissolve
        x_left, x_right = R[0] - 12.0, K[0] + 18.0
        front = x_left + (d ** 1.2) * (x_right - x_left + 6.0)
        ragged = front + 2.2 * np.sin(cv.Y * 0.8 + d * 6.0) + 1.2 * np.sin(cv.Y * 2.1)
        hc.erase_mask(cv, cv.filled & (cv.X < ragged))
        hc.drop_specks(cv, 5)
        top = cv.layer(above=True, outline=True)
        for k, y in enumerate((C[1] - 10.0, C[1] - 3.0, C[1] + 3.0, ground - 5.0)):
            x = front - 1.0 + (k % 2) * 1.5
            if x_left - 2 < x < x_right + 4:
                hc.mist_puff(top, x, y - d * 2.0, 2.6 + 0.6 * ((k + 1) % 3), mat=hc.HOLLOW_MIST)
        for k in range(3 + int(3 * d)):
            x = front - 7.0 - k * 5.5
            y = C[1] - 6.0 - d * 6.0 - (k % 3) * 3.0 + k * 1.5
            if x > 8:
                hc.mist_puff(top, x, y, 2.8 - 0.25 * k, mat=hc.HOLLOW_MIST)
    if p.hit:
        top = cv.layer(above=True, outline=False)
        px.impact(top, prong[0] + 1, prong[1], size=4)
