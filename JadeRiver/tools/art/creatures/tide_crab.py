"""Tide crab - big blue-teal crab with one oversized shield claw and pearl-studded shell (Water).

View: 3/4 front, turned toward the right (like the mudshell crab).  ~26 art px tall,
~40 wide (cell 128).
Parts, back to front: legs (back pair first), underside + mouth, shell (pearl nodules and
pale rim as decals), eye stalks + eyes, small far pincer, oversized near shield claw (broad
flat palm with a crusted rim and pearls) held in front of the face.
Windup: the shield claw rears up high and gapes open (held).  Attack: it thrusts forward
and snaps shut on frame 1.  Death: flips over onto its back, legs curling.
"""
import math

import pixel as px

SPEC = {
    "id": "tide_crab",
    "cell": 128,
    "anchor": [64, 112],
    "flying": False,
    "hit_frame": 1,
}

# ---- palette: deep sea teal-blue shell, sandy underside, pearl white-pink ---------------------
SHELL = px.material("tide_shell", "#7ecae4", "#2f80aa", "#1f567e", "#163658", outline="#06111c",
                    thresholds=(0.9, 0.55, 0.2))
CLAW = px.material("tide_claw", "#b2f2e4", "#4cbab0", "#2a8088", "#1c5264", outline="#06141a",
                   thresholds=(0.9, 0.55, 0.2))
RIM = px.material("tide_rim", "#d4f4ec", "#8fd4d0", "#4fa0aa", "#2e6a7c", outline="#07141f")
UNDER = px.material("tide_under", "#f0e2c2", "#c9b690", "#948468", "#625a4e", outline="#07141f")
LEG = px.material("tide_leg", "#7ccfd8", "#3690a8", "#23627e", "#183f58", outline="#07141f")
PEARL = px.material("pearl", "#ffffff", "#f6e2ea", "#d0aec4", "#8e7294", outline="#1e1422")
TIP = px.material("tide_tip", "#f4a07c", "#d8664e", "#9a3e3c", "#5e2230", outline="#1c0a0e")
STALK = px.flat("#a8dcd8", outline="#07141f")

# ---- poses -------------------------------------------------------------------------------
# bx, by  body offset          rot  lean of the whole crab (deg) about its feet
# sh      shield claw: (dx, dy) palm offset, angle (deg, 90 = up), opening 0..1
# lh      small claw hand offset       la  small claw angle        lo  small claw opening
# lift, slide  per-leg tip lift / x-slide     eye  open|angry|squeeze|dead   lean  eye-stalk lean
# flip   on its back      curl  leg curl 0..1      fade  frame opacity      knees  body dip
DEFAULTS = dict(bx=0, by=0, rot=0, sh=(0, 0, 96, 0.0), lh=(0, 0), la=120, lo=0.3, lift=(0,) * 6,
                slide=(0,) * 6, eye="open", lean=0, flip=False, curl=0.0, fade=1.0, hit=False, knees=0,
                flail=False)

A = (1, 0, 1, 0, 1, 0)
B = (0, 1, 0, 1, 0, 1)


def _k(mask, k):
    return tuple(m * k for m in mask)


POSE = px.poses(DEFAULTS, {
    "idle": [  # guarding behind the shield claw; small claw clicks
        dict(),
        dict(lo=0.6, sh=(0, 0, 97, 0.0)),
        dict(by=1, lo=0.2, knees=1, lean=1, sh=(0, 1, 96, 0.0)),
        dict(by=1, lo=0.4, knees=1, lean=1, sh=(0, 1, 95, 0.1)),
    ],
    "walk": [  # sideways scuttle behind the shield: tripods alternate
        dict(by=-1, lift=_k(A, 2), slide=_k(A, 1), sh=(0, -1, 96, 0.0)),
        dict(bx=1, by=-1, lift=_k(A, 1), slide=_k(A, 2)),
        dict(bx=1, by=0, slide=_k(B, -1), lh=(0, 1)),
        dict(bx=0, by=-1, lift=_k(B, 2), slide=_k(B, 1), lh=(0, -1), sh=(0, -1, 96, 0.0)),
        dict(bx=1, by=-1, lift=_k(B, 1), slide=_k(B, 2)),
        dict(bx=1, by=0, slide=_k(A, -1)),
    ],
    "windup": [  # the shield claw rears up and gapes - held
        dict(by=1, knees=1, sh=(-1, -5, 80, 0.4), lh=(-1, -2), la=110, lo=0.6, lean=-1, eye="angry"),
        dict(by=1, knees=1, sh=(-2, -10, 70, 0.9), lh=(-1, -3), la=105, lo=0.8, lean=-1, eye="angry", rot=4),
        dict(by=2, knees=2, sh=(-2, -11, 68, 1.0), lh=(-1, -3), la=105, lo=0.9, lean=-1, eye="angry", rot=5),
    ],
    "attack": [  # thrust forward open, snap shut on frame 1, hold, pull back behind the shield
        dict(bx=1, rot=-4, sh=(8, -2, 20, 1.0), eye="angry", knees=1, slide=(1, 1, 1, 0, 0, 0)),
        dict(bx=0, rot=-7, sh=(9, 1, 6, 0.0), eye="angry", slide=(1, 1, 1, 0, 0, 0), hit=True, knees=1),
        dict(bx=0, rot=-6, sh=(8, 1, 8, 0.0), eye="angry", slide=(1, 1, 1, 0, 0, 0), knees=1),
        dict(bx=1, rot=-2, sh=(3, 0, 60, 0.1)),
    ],
    "hurt": [
        dict(bx=-2, by=-1, rot=8, sh=(-1, -3, 104, 0.5), lh=(-1, -3), la=130, lo=0.7, eye="squeeze", lean=-2,
             lift=(1, 1, 1, 0, 0, 0)),
        dict(bx=-1, rot=4, sh=(0, -1, 100, 0.2), la=125, lo=0.4, eye="squeeze", lean=-1),
    ],
    "death": [
        dict(bx=-2, by=-2, rot=14, eye="squeeze", lean=-2, sh=(-1, -4, 110, 0.7), lo=0.8),
        dict(bx=1, by=-3, rot=40, eye="dead", sh=(0, -4, 120, 0.9), lo=0.9, flail=True),
        dict(flip=True, eye="dead", sh=(0, 0, 60, 1.0), lo=1.0),
        dict(flip=True, eye="dead", curl=0.55, sh=(0, 0, 60, 0.5), lo=0.5, fade=0.6),
        dict(flip=True, eye="dead", curl=1.0, sh=(0, 0, 60, 0.2), lo=0.1, fade=0.3),
    ],
})

# ---- geometry (relative to body centre C) -----------------------------------------------
RX, RY = 12.5, 6.8  # carapace radii
_LEFT = (
    ((-6.5, 4.0), (-11.5, 2.6), -13.0),
    ((-8.5, 3.0), (-14.0, 0.8), -16.0),
    ((-10.0, 1.6), (-16.0, -1.4), -18.5),
)
LEGS = _LEFT + tuple(((-h[0], h[1]), (-k[0], k[1]), -t) for h, k, t in _LEFT)
LEG_ORDER = (2, 5, 1, 4, 0, 3)


def _leg(cv, C, body, ground, i, p):
    (hx, hy), (kx, ky), tx = LEGS[i]
    back = i in (2, 5)
    if p.flip:
        c = p.curl
        hip = (C[0] + hx, C[1] + hy)
        knee = (C[0] + kx * (1 - 0.2 * c), C[1] + 4.5 - ky * 0.6 + c)
        tip = (C[0] + tx * (1 - 0.6 * c), C[1] + 11.0 - c * 5.0)
    elif p.flail:
        hip = (C[0] + hx, C[1] + hy)
        knee = (C[0] + kx * 1.05, C[1] + ky - 1.0)
        tip = (C[0] + tx * (1.12 - 0.1 * (i % 3)), C[1] + ky + 3.0 + 2.2 * (i % 3))
    else:
        hip = body((C[0] + hx, C[1] + hy))
        knee = body((C[0] + kx + p.slide[i] * 0.5, C[1] + ky - p.lift[i] + p.knees * 0.5))
        tip = (cv.gx - 4 + tx + p.slide[i], ground - p.lift[i])
    cv.limb([hip, knee, tip], [1.4, 1.15, 0.55], LEG, shade="dark" if back else "soft", name=f"leg{i}",
            sep=False if back else "deep")
    if not back and not p.flip:  # coral leg tip
        cv.limb([px.lerp_pt(knee, tip, 0.7), tip], [0.8, 0.55], TIP, shade="two", decal=True, clip=f"leg{i}",
                name=f"leg{i}")


def _small_claw(cv, shoulder, hand, ang, opening):
    """The far, ordinary pincer (nolight: turned away)."""
    cv.limb([shoulder, hand], [1.3, 1.5], LEG, shade="two", name="arm")
    cv.ellipse(hand[0], hand[1], 3.2, 2.6, CLAW, angle=ang, shade="nolight", name="claw", sep=True)
    front = px.polar(hand, ang, 2.2)
    for sgn, ln in ((1, 4.0), (-1, 3.6)):
        a = ang + (sgn * (8 + 30 * opening) if sgn > 0 else -6)
        root = px.polar(front, ang + 90 * sgn, 1.0)
        tip = px.polar(root, a - sgn * 18, ln)
        cv.limb([root, tip], [1.1, 0.5], CLAW, shade="nolight", name="finger")
        cv.limb([px.lerp_pt(root, tip, 0.5), tip], [0.8, 0.45], TIP, decal=True, clip="finger", name="finger")


def _shield(cv, shoulder, palm, ang, opening):
    """Oversized shield claw: broad flat palm (crusted rim, pearls), heavy dactyl hinging
    open, the pollex in line with the palm."""
    cv.limb([shoulder, px.polar(palm, ang + 180, 4.0)], [2.2, 2.6], LEG, shade="two", name="arm", sep=True)
    cv.ellipse(palm[0], palm[1], 7.4, 6.2, CLAW, angle=ang, name="shield", sep="deep")
    # pale crusted rim along the upper-left edge + a pearl cluster on the face of the claw
    cv.ellipse(palm[0], palm[1], 7.4, 6.2, RIM, angle=ang, shade="two", decal=True, clip="shield", name="shield",
               minus=cv.mask_ellipse(palm[0] + 0.9, palm[1] + 0.9, 6.4, 5.2, angle=ang))
    for off, d, r in ((150, 3.0, 1.5), (205, 3.6, 1.2)):
        q = px.polar(palm, ang + off, d)
        cv.circle(q[0], q[1], r, PEARL, shade="soft", name="pearl", sep="deep")
    front = px.polar(palm, ang, 5.6)
    tips = []
    for sgn, ln, r0, a in ((1, 8.2, 2.5, ang + 4 + 46 * opening), (-1, 7.4, 2.8, ang - 4)):
        root = px.polar(front, ang + 90 * sgn, 2.4)
        mid = px.polar(root, a, ln * 0.55)
        tip = px.polar(mid, a - sgn * (30 + 16 * (1 - opening)), ln * 0.5)
        cv.limb([root, mid, tip], [r0, r0 * 0.7, 0.7], CLAW, name="finger", sep="deep")
        cv.limb([px.lerp_pt(mid, tip, 0.25), tip], [r0 * 0.7, 0.7], TIP, decal=True, clip="finger", name="finger")
        nub = px.polar(px.lerp_pt(root, mid, 0.6), ang - sgn * 90, r0 * 0.5)
        cv.circle(nub[0], nub[1], 0.7, PEARL, shade="soft", decal=True, clip="finger", name="finger")
        tips.append(tip)
    return tips


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    ground = cv.ground
    C = (cv.gx - 4 + p.bx, ground - 10.5 + p.by)

    def body(pt):
        return px.rot_pt(pt, p.rot, (C[0], ground))

    xf = [px.rotate(p.rot, (C[0], ground))]
    if p.flip:
        C = (cv.gx - 3, ground - 10.0)
        xf = [px.rotate(180, C)]
    cv.snap_ground = p.flip or p.flail
    cv.opacity = p.fade

    if p.flip or p.flail:
        with cv.xform(*xf):
            for i in LEG_ORDER:
                _leg(cv, C, lambda q: q, ground, i, p)
    else:
        for i in LEG_ORDER:
            _leg(cv, C, body, ground, i, p)
    with cv.xform(*xf):
        cv.ellipse(C[0] + 0.5, C[1] + 4.0, 8.0, 3.2, UNDER, shade="two", name="under")
        cv.pixels([(int(C[0]) + k, int(C[1]) + 5) for k in (0, 1, 2)], "#3a2a2c", name="mouth")
        cv.ellipse(C[0], C[1], RX, RY, SHELL, name="shell", sep="deep")
        # pale rim along the front edge of the carapace
        cv.ellipse(C[0], C[1] + 2.4, RX - 0.5, RY - 2.2, RIM, shade="two", decal=True, clip="shell", name="shell",
                   minus=cv.mask_ellipse(C[0], C[1] + 1.2, RX - 1.2, RY - 2.2))
        # pearl nodules studding the carapace
        for (sx, sy, r) in ((-6.5, -2.6, 1.6), (-1.5, -4.4, 1.4), (-9.5, 0.4, 1.3), (-3.5, 0.2, 1.2),
                            (2.5, -2.0, 1.3)):
            cv.circle(C[0] + sx, C[1] + sy, r, PEARL, shade="soft", name="pearl", sep="deep")
        # eye stalks + beady eyes above the shell (both right of centre in the 3/4 turn)
        lean_x = 1 if p.lean > 0 else (-1 if p.lean < 0 else 0)
        for ex in (() if p.flip else (-1.0, 4.5)):
            base = (round(C[0] + ex), round(C[1] - RY + 1.0))
            topx = base[0] + lean_x
            cv.line(base, (topx, base[1] - 3), STALK, name="stalk")
            ex0, ey0 = topx, base[1] - 5
            if p.eye == "dead":
                cv.stamp(["k.k", ".k.", "k.k"], ex0 - 1 + (0 if ex < 0 else 1), ey0 - 1, {"k": px.INK}, name="eye")
            elif p.eye == "squeeze":
                cv.stamp(["kk"], ex0, ey0 + 1, {"k": px.INK}, name="eye")
            else:
                cv.stamp(["gk", "kk"], ex0, ey0, {"k": px.INK, "g": px.GLINT}, name="eye")
                if p.eye == "angry":
                    cv.pixel(ex0 + (1 if ex < 0 else 0), ey0 - 1, px.INK, name="brow")
        # small far pincer on the left
        _small_claw(cv, (C[0] - 8.5, C[1] + 2.5), (C[0] - 13.0 + p.lh[0], C[1] - 1.5 + p.lh[1]), p.la, p.lo)
        # oversized shield claw on the right, held in front of the face
        dx, dy, ang, op = p.sh
        palm = (C[0] + 6.5 + dx, C[1] - 2.0 + dy)
        tips = _shield(cv, (C[0] + 6.0, C[1] + 3.5), palm, ang, op)
        if p.hit:
            pinch = cv.tp(px.lerp_pt(tips[0], tips[1], 0.5))
    if p.hit:
        fx = cv.layer(above=True, outline=False)
        px.impact(fx, pinch[0], pinch[1], size=3)
