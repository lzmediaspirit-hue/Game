"""Mudshell crab - small mud-brown river crab (Water element).

View: 3/4 front, turned toward the right (a crab scuttles sideways, so the camera sees
its face).  ~17 art px tall, ~28 wide on a 64 px art canvas.

Parts, back to front: legs (back pair first), underside + mouth, shell (+ pale mud
spots as decals), eye stalks + beady eyes, left claw (far, smaller), right claw.

Pattern to copy for new creatures:
  * palette block: one hand-picked ``px.material`` per part family
  * ``POSE = px.poses(DEFAULTS, {...})`` - a few named numbers per frame
  * ``draw(cv, action, frame)`` turns the pose into parts; all geometry is relative
    to the body centre ``C`` so bobbing, leaning and flipping move everything.
"""
import pixel as px

SPEC = {
    "id": "mudshell_crab",
    "cell": 128,
    "anchor": [64, 112],
    "flying": False,
    "hit_frame": 2,
}

# ---- palette: mud brown, warm ochre lights, cool violet-grey shadows ----------------------
SHELL = px.material("mud_shell", "#c09565", "#8e6444", "#634739", "#40303a", outline="#1a1216")
SPOT = px.material("mud_spot", "#f0dfb6", "#d4bd92", "#a99173", "#7a6656", outline="#1a1216")
UNDER = px.material("crab_under", "#d8bf97", "#ae8f6c", "#806a5b", "#574845", outline="#1a1216")
LEG = px.material("crab_leg", "#c0925f", "#96694a", "#684b3b", "#453235", outline="#1a1216")
TIP = px.material("claw_tip", "#a4f2dc", "#46baa6", "#257f78", "#174d52", outline="#0a1a1d")
STALK = px.flat("#c9a97c", outline="#1a1216")

# ---- poses -------------------------------------------------------------------------------
# bx, by  body offset          rot   lean of the whole crab (deg, CCW) about its feet
# rh, lh  right / left hand offset from rest      ra, la  pincer direction (deg, 90 = up)
# ro, lo  pincer opening 0..1                     lift, slide  per-leg tip lift / x-slide
# eye     open|angry|squeeze|dead                 lean  eye-stalk lean (px, + = right)
# flip    on its back          curl  leg curl 0..1 (dead)   fade  frame opacity
DEFAULTS = dict(bx=0, by=0, rot=0, rh=(0, 0), lh=(0, 0), ra=62, la=110, ro=0.4, lo=0.4,
                lift=(0,) * 6, slide=(0,) * 6, eye="open", lean=0, flip=False, curl=0.0,
                fade=1.0, hit=False, knees=0, flail=False)

# legs: 0-2 left (front, mid, back), 3-5 right.  Tripods for the scuttle: A / B.
A = (1, 0, 1, 0, 1, 0)
B = (0, 1, 0, 1, 0, 1)


def _k(mask, k):
    return tuple(m * k for m in mask)


POSE = px.poses(DEFAULTS, {
    "idle": [
        dict(),
        dict(ro=0.55, lo=0.5),
        dict(by=1, ro=0.2, lo=0.2, knees=1, lean=1),
        dict(by=1, ro=0.3, lo=0.35, knees=1, lean=1),
    ],
    "walk": [  # sideways scuttle: tripod A steps while B pushes, then swap
        dict(by=-1, lift=_k(A, 2), slide=_k(A, 1), rh=(0, -1)),
        dict(bx=1, by=-1, lift=_k(A, 1), slide=_k(A, 2)),
        dict(bx=1, by=0, slide=_k(B, -1), lh=(0, 1)),
        dict(bx=0, by=-1, lift=_k(B, 2), slide=_k(B, 1), lh=(0, -1)),
        dict(bx=1, by=-1, lift=_k(B, 1), slide=_k(B, 2)),
        dict(bx=1, by=0, slide=_k(A, -1), rh=(0, 1)),
    ],
    "windup": [  # both claws up and open - the tell, held on the last frame
        dict(by=1, knees=1, rh=(1, -4), lh=(-1, -4), ra=75, la=100, ro=0.6, lo=0.6),
        dict(by=1, knees=1, rh=(2, -8), lh=(-2, -8), ra=80, la=100, ro=1.0, lo=1.0, lean=-1),
        dict(by=2, knees=2, rh=(3, -9), lh=(-3, -9), ra=78, la=102, ro=1.0, lo=1.0, lean=-1,
             eye="angry"),
    ],
    "attack": [  # claws chop forward and down; hit on frame 2
        dict(bx=1, rot=-4, rh=(1, -8), lh=(0, -8), ra=75, la=95, ro=1.0, lo=1.0, eye="angry",
             knees=1),
        dict(bx=2, rot=-8, rh=(3, -3), lh=(2, -4), ra=20, la=40, ro=0.8, lo=0.8, eye="angry",
             slide=(1, 1, 1, 0, 0, 0)),
        dict(bx=2, rot=-9, rh=(2, 1), lh=(1, 1), ra=-42, la=-25, ro=0.0, lo=0.0, eye="angry",
             slide=(1, 1, 1, 0, 0, 0), hit=True, knees=1),
        dict(bx=1, rot=-4, rh=(1, 1), lh=(0, 0), ra=20, la=80, ro=0.2, lo=0.2),
    ],
    "hurt": [
        dict(bx=-2, by=-1, rot=8, rh=(-1, -3), lh=(-1, -3), ra=95, la=120, ro=0.7, lo=0.7,
             eye="squeeze", lean=-2, lift=(1, 1, 1, 0, 0, 0)),
        dict(bx=-1, rot=4, rh=(0, -1), lh=(0, -1), ra=75, la=115, ro=0.4, lo=0.4, eye="squeeze", lean=-1),
    ],
    "death": [
        dict(bx=-2, by=-2, rot=14, eye="squeeze", lean=-2, ro=0.8, lo=0.8, rh=(0, -3), lh=(0, -3)),
        dict(bx=-2, by=-3, rot=40, eye="dead", ro=0.9, lo=0.9, flail=True),
        dict(flip=True, eye="dead", ro=1.0, lo=1.0),
        dict(flip=True, eye="dead", curl=0.55, ro=0.5, lo=0.5, fade=0.6),
        dict(flip=True, eye="dead", curl=1.0, ro=0.1, lo=0.1, fade=0.3),
    ],
})

# ---- geometry (relative to body centre C) -----------------------------------------------
RX, RY = 9.3, 5.2  # carapace radii
# (hip, knee, tip_dx) per leg; left legs listed front -> back; right legs mirror them.
# Upper segment thick and nearly level, lower segment thin and fanned outward.
_LEFT = (
    ((-5.0, 3.2), (-8.8, 1.8), -9.8),
    ((-6.5, 2.2), (-10.8, 0.0), -12.3),
    ((-7.5, 1.0), (-12.3, -1.8), -14.5),
)
LEGS = _LEFT + tuple(((-h[0], h[1]), (-k[0], k[1]), -t) for h, k, t in _LEFT)
LEG_ORDER = (2, 5, 1, 4, 0, 3)  # back pair first, front pair last


def _leg(cv, C, body, ground, i, p):
    """``body`` maps body-local points (hips/knees) through the upper-body lean, while
    tips stay planted on the ground."""
    (hx, hy), (kx, ky), tx = LEGS[i]
    back = i in (2, 5)
    if p.flip:  # on its back: legs point up (local +y) and curl in toward the belly
        c = p.curl
        hip = (C[0] + hx, C[1] + hy)
        knee = (C[0] + kx * (1 - 0.2 * c), C[1] + 3.5 - ky * 0.6 + c)
        tip = (C[0] + tx * (1 - 0.6 * c), C[1] + 9.0 - c * 4.0)
    elif p.flail:  # tumbling: legs splay out and dangle, each at its own angle
        hip = (C[0] + hx, C[1] + hy)
        knee = (C[0] + kx * 1.05, C[1] + ky - 1.0)
        tip = (C[0] + tx * (1.15 - 0.12 * (i % 3)), C[1] + ky + 2.5 + 2.0 * (i % 3))
    else:
        hip = body((C[0] + hx, C[1] + hy))
        knee = body((C[0] + kx + p.slide[i] * 0.5, C[1] + ky - p.lift[i] + p.knees * 0.5))
        tip = (cv.gx + tx + p.slide[i], ground - p.lift[i])
    cv.limb([hip, knee, tip], [1.15, 0.95, 0.5], LEG, shade="dark" if back else "soft",
            name=f"leg{i}", sep=False if back else "deep")


def _claw(cv, shoulder, hand, ang, opening, size, far=False):
    """Short arm, round palm and two tapered fingers opening around ``ang``."""
    shade = "nolight" if far else "full"
    cv.limb([shoulder, hand], [1.1 * size, 1.3 * size], SHELL, shade="two", name="arm", sep=True)
    cv.ellipse(hand[0], hand[1], 3.0 * size, 2.5 * size, SHELL, angle=ang, shade=shade,
               name="claw", sep=True)
    spread = 10 + 24 * opening
    root = px.polar(hand, ang, 1.6 * size)
    for sgn in (1, -1):  # upper finger (dactyl), lower finger (pollex)
        a0 = ang + sgn * spread
        mid = px.polar(px.polar(root, ang + sgn * 90, 0.9 * size), a0, 2.2 * size)
        tip = px.polar(mid, a0 - sgn * (22 + 18 * (1 - opening)), 2.2 * size)
        cv.limb([px.polar(root, ang + sgn * 90, 0.9 * size), mid, tip],
                [1.15 * size, 0.95 * size, 0.45], SHELL, shade=shade, name="finger")
        cv.limb([px.lerp_pt(mid, tip, 0.45), tip], [1.0 * size, 0.6], TIP, decal=True, clip="finger")


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    ground = cv.ground  # centre of the last filled row (outline lands on gy - 1)
    C = (cv.gx - 1 + p.bx, ground - 7.5 + p.by)

    def body(pt):  # upper-body lean for leg attachment points (feet stay planted)
        return px.rot_pt(pt, p.rot, (C[0], ground))

    xf = [px.rotate(p.rot, (C[0], ground))]
    if p.flip:  # on its back: turn 180 about the body centre (near-symmetric front view)
        C = (cv.gx - 1, ground - 7.5)
        xf = [px.rotate(180, C)]
    cv.snap_ground = p.flip or p.flail  # tumbling / lying: settle the lowest pixel on the ground
    cv.opacity = p.fade

    if p.flip or p.flail:
        with cv.xform(*xf):
            for i in LEG_ORDER:
                _leg(cv, C, lambda q: q, ground, i, p)
    else:
        for i in LEG_ORDER:
            _leg(cv, C, body, ground, i, p)
    with cv.xform(*xf):
        # belly / mouth plate peeking below the carapace
        cv.ellipse(C[0] + 0.5, C[1] + 3.0, 6.0, 2.6, UNDER, shade="two", name="under")
        cv.pixels([(int(C[0]) + 1, int(C[1]) + 4), (int(C[0]) + 2, int(C[1]) + 4)], "#3a2a2c", name="mouth")
        # carapace + dried mud spots (decals follow the shell shading)
        cv.ellipse(C[0], C[1], RX, RY, SHELL, name="shell", sep="deep")
        for (sx, sy, rx, ry) in ((-4.2, -1.2, 1.6, 1.1), (0.2, -3.0, 1.2, 0.8), (4.2, -1.8, 1.5, 1.0),
                                 (1.8, 1.4, 0.9, 0.7), (-6.4, 1.2, 0.8, 0.7)):
            cv.ellipse(C[0] + sx, C[1] + sy, rx, ry, SPOT, shade="soft", decal=True, clip="shell")
        # eye stalks + beady eyes (3/4 turn: both sit right of centre)
        lean_x = 1 if p.lean > 0 else (-1 if p.lean < 0 else 0)
        for ex in (() if p.flip else (-1.0, 4.0)):
            base = (round(C[0] + ex), round(C[1] - RY + 1.0))
            topx = base[0] + lean_x
            cv.line(base, (topx, base[1] - 2), STALK, name="stalk")
            ex0, ey0 = topx, base[1] - 4
            if p.eye == "dead":
                cv.stamp(["k.k", ".k.", "k.k"], ex0 - 1 + (0 if ex < 0 else 1), ey0 - 1, {"k": px.INK}, name="eye")
            elif p.eye == "squeeze":
                cv.stamp(["kk"], ex0, ey0 + 1, {"k": px.INK}, name="eye")
            else:
                cv.stamp(["gk", "kk"], ex0, ey0, {"k": px.INK, "g": px.GLINT}, name="eye")
                if p.eye == "angry":  # brows slant down toward the middle
                    cv.pixel(ex0 + (1 if ex < 0 else 0), ey0 - 1, px.INK, name="brow")
        # claws: left (far side, a bit smaller) then right (near side)
        lsh = (C[0] - 6.5, C[1] + 2.0)
        lhand = (C[0] - 10.5 + p.lh[0], C[1] - 1.5 + p.lh[1])
        _claw(cv, lsh, lhand, p.la, p.lo, 0.9, far=True)
        rsh = (C[0] + 6.5, C[1] + 2.0)
        rhand = (C[0] + 11.0 + p.rh[0], C[1] - 1.5 + p.rh[1])
        _claw(cv, rsh, rhand, p.ra, p.ro, 1.0)
        if p.hit:
            tip = cv.tp(px.polar(rhand, p.ra, 6.5))
    if p.hit:
        fx = cv.layer(above=True, outline=False)
        px.impact(fx, tip[0] + 1, tip[1], size=3)
