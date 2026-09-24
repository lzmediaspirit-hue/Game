"""Cliff ape - big grey-brown mountain ape with a shaggy white mane (Earth).

View: side, facing right.  ~50 art px tall in the knuckle stance (the mane crest), ~70
standing with the boulder overhead, on a 96 px art canvas (cell 192).
Rig: pelvis P and shoulders S on a spine tilted by ``tilt`` (30 = knuckle stance,
80 = upright).  Legs and arms are two-bone limbs solved with ``px.ik2``.
Parts, back to front: far leg, far arm, hips + chest (one form), white shaggy mane over
the shoulders, head (dark leathery face, heavy brow, amber eye), near leg, near arm (in
front, with ``sep``), boulder.  FX: dust, impact, flying stone chips.
Windup: stands up and hoists a boulder overhead (held); attack: smashes it down in front
(hit on frame 1); death: topples over backwards and lies still.
"""
import math

import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "cliff_ape",
    "cell": 192,
    "anchor": [96, 168],
    "flying": False,
    "hit_frame": 1,
}

# ---- palette: grey-brown fur, white mane, dark leathery skin, ochre earth stone --------------
FUR = px.material("ape_fur", "#a8977f", "#7b6a5a", "#554a4b", "#373138", outline="#130f12",
                  thresholds=(0.9, 0.56, 0.2))
MANE = px.material("ape_mane", "#fbf8ee", "#dcd8cb", "#a9aaa6", "#77797e", outline="#16171b",
                   thresholds=(0.86, 0.5, 0.16))
SKIN = px.material("ape_skin", "#7a6f78", "#544b56", "#3a343f", "#26222b", outline="#0e0c10")
STONE = px.material("boulder", "#d8b27a", "#a67c4c", "#76583e", "#4b3a31", outline="#1a1310",
                    thresholds=(0.9, 0.55, 0.2))
MOSS = px.material("boulder_moss", "#b3cf6a", "#7ea346", "#5a7b37", "#3b562b", outline="#0d170c")
IRIS = px.rgb("#f0b43c")
TOOTH = px.rgb("#f2ead2")

# ---- poses ------------------------------------------------------------------------------------
# bx, by    pelvis offset       tilt  spine angle (deg: 0 flat, 90 upright)
# head      head tilt (deg)     jaw   roar 0..1        eye  angry|squeeze|dead|open
# hn, hf    near / far hand target relative to the shoulder (None = knuckles on the ground)
# kn, kf    knuckle offsets on the ground (dx, lift) for near / far hands
# fn, ff    near / far foot (dx, lift)         breathe  chest swell       mane  mane ruffle
# rock      boulder: None | "held" (between the hands) | ("ground", dx) smashed on the ground
# crack     boulder cracks 0..2      dust  dust life    chips  flying chip life
# rot       whole-body roll for the topple (deg, + = backwards)
DEFAULTS = dict(bx=0, by=0, tilt=30, head=0, jaw=0.0, eye="angry", hn=None, hf=None, kn=(0, 0), kf=(0, 0),
                fn=(0, 0), ff=(0, 0), breathe=0.0, mane=0.0, rock=None, crack=0, dust=None, chips=None,
                hit=False, rot=0, fade=1.0)

POSE = px.poses(DEFAULTS, {
    "idle": [
        dict(),
        dict(breathe=0.5, mane=1.0, head=2),
        dict(breathe=0.8, mane=2.0, head=3, by=-1),
        dict(breathe=0.3, mane=3.0, head=1),
    ],
    "walk": [  # knuckle walk: near hand + far foot swing together, then swap
        dict(kn=(5, 0), kf=(-3, 0), fn=(-4, 0), ff=(3, 0), mane=0.0),
        dict(kn=(3, 0), kf=(0, 3), fn=(-2, 0), ff=(0, 2), mane=1.0, by=-1, tilt=31),
        dict(kn=(0, 0), kf=(4, 2), fn=(0, 2), ff=(-2, 0), mane=2.0, by=-1),
        dict(kn=(-3, 0), kf=(5, 0), fn=(3, 0), ff=(-4, 0), mane=3.0),
        dict(kn=(0, 3), kf=(3, 0), fn=(0, 2), ff=(-2, 0), mane=4.0, by=-1, tilt=31),
        dict(kn=(4, 2), kf=(0, 0), fn=(-2, 0), ff=(0, 2), mane=5.0, by=-1),
    ],
    "windup": [  # grabs a boulder, heaves it up and holds it overhead - held
        dict(tilt=22, by=3, bx=2, head=-10, hn=(9, 25), hf=(11, 25), rock="lift", eye="angry", jaw=0.2,
             fn=(-2, 0), ff=(1, 0)),
        dict(tilt=58, by=-1, bx=-1, head=10, hn=(8, -3), hf=(10, -4), rock="held", jaw=0.5, mane=1.5,
             fn=(-2, 0), ff=(2, 0)),
        dict(tilt=76, by=-2, bx=-3, head=14, hn=(2, -13), hf=(4, -14), rock="held", jaw=0.9, mane=3.0,
             fn=(-3, 0), ff=(3, 0), breathe=0.6),
    ],
    "attack": [  # slams the boulder down in front: hit on frame 1, dust + chips
        dict(tilt=64, by=-2, bx=2, head=0, hn=(13, -9), hf=(14, -10), rock="held", jaw=1.0, mane=4.0,
             fn=(-2, 0), ff=(3, 0)),
        dict(tilt=26, by=2, bx=6, head=-6, hn=(16, 20), hf=(17, 20), rock=("ground", 0), crack=1, jaw=0.8,
             dust=0.15, chips=0.2, hit=True, fn=(1, 0), ff=(4, 0), mane=5.0),
        dict(tilt=28, by=1, bx=6, head=-4, hn=(15, 21), hf=(16, 21), rock=("ground", 0), crack=2, jaw=0.4,
             dust=0.5, chips=0.6, fn=(1, 0), ff=(4, 0), mane=0.0),
        dict(tilt=30, bx=3, head=0, rock=("ground", 0), crack=2, dust=0.85, mane=1.0, kn=(2, 0)),
    ],
    "hurt": [
        dict(tilt=44, bx=-4, by=-2, head=18, eye="squeeze", jaw=0.6, hn=(-2, 8), kf=(2, 0), mane=2.0),
        dict(tilt=36, bx=-2, head=8, eye="squeeze", jaw=0.2, mane=1.0),
    ],
    "death": [  # rears back, teeters and topples onto its back
        dict(tilt=48, bx=-4, by=-2, head=20, eye="squeeze", jaw=0.8, hn=(-2, 6), hf=(0, 4), mane=2.0),
        dict(tilt=70, bx=-6, by=-2, head=26, eye="dead", jaw=0.6, hn=(-4, -10), hf=(-2, -12), mane=3.0,
             fn=(2, 0), ff=(4, 0)),
        dict(tilt=80, bx=13, head=20, eye="dead", jaw=0.5, hn=(-6, -12), hf=(-4, -14), rot=40, mane=4.0,
             fn=(3, 0), ff=(5, 0)),
        dict(tilt=84, bx=12, head=14, eye="dead", jaw=0.4, hn=(9, 6), hf=(11, 3), rot=86, mane=5.0,
             fn=(4, 3), ff=(7, 5), dust=0.3),
        dict(tilt=84, bx=12, head=10, eye="dead", jaw=0.4, hn=(10, 8), hf=(12, 5), rot=90, mane=5.0,
             fn=(5, 2), ff=(8, 3), dust=0.75),
    ],
})

L_THIGH, L_SHIN = 8.5, 8.5
L_UPPER, L_FORE = 13.0, 14.0
SPINE = 20.0
K = 1.2  # overall scale of the rig (drawn about the anchor)


# ---- parts ------------------------------------------------------------------------------------
def _leg(cv, hip, foot, far):
    shade = "dark" if far else "two"
    knee = px.ik2(hip, (foot[0] - 1.0, foot[1] - 2.3), L_THIGH, L_SHIN, bend=1)
    cv.limb([hip, knee, (foot[0] - 1.0, foot[1] - 2.3)], [4.2, 3.4, 2.6], FUR, shade=shade, name="leg",
            sep=False if far else "deep")
    cv.ellipse(foot[0] + 1.0, foot[1] - 1.2, 3.8, 1.8, SKIN, shade="dark" if far else "two", name="foot")


def _arm(cv, shoulder, hand, far, knuckle=True, bend=-1):
    """Massive arm: shaggy upper arm, thick forearm, dark knuckled fist."""
    shade = "dark" if far else "soft"
    wrist = (hand[0] - 0.5, hand[1] - 3.6) if knuckle else hand
    d = math.hypot(wrist[0] - shoulder[0], wrist[1] - shoulder[1])
    elbow = px.ik2(shoulder, wrist, L_UPPER, L_FORE, bend=bend) if d < L_UPPER + L_FORE - 0.5 else \
        px.lerp_pt(shoulder, wrist, L_UPPER / (L_UPPER + L_FORE))
    cv.limb([shoulder, elbow, wrist], [4.6, 3.8, 3.3], FUR, shade=shade, name="arm_far" if far else "arm",
            sep=False if far else "deep")
    # shaggy elbow tuft
    cv.polygon([px.polar(elbow, 150, 2.0), px.polar(elbow, 220, 5.2), px.polar(elbow, 270, 2.2)], FUR,
               shade="dark" if far else "two", name="arm_far" if far else "arm")
    if knuckle:
        cv.ellipse(hand[0] + 0.6, hand[1] - 1.7, 3.2, 1.9, SKIN, shade="dark" if far else "two",
                   name="hand", sep=False if far else "deep")
    else:
        cv.circle(hand[0], hand[1], 3.0, SKIN, shade="dark" if far else "two", name="hand",
                  sep=False if far else "deep")
    return elbow


def _mane(cv, S, tilt, ruffle, clip=None):
    """Shaggy white mane crest over the shoulders and nape: a spiky arc."""
    pts = []
    n = 13
    a0, a1 = tilt - 60, tilt + 150  # from the chest front, over the top, down the back
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        r = 10.5 + (2.6 if i % 2 else 0.0) + 0.6 * math.sin(ruffle + i * 1.3)
        pts.append(px.polar(S, a, r))
    for i in range(n, -1, -1):
        a = a0 + (a1 - a0) * i / n
        pts.append(px.polar(S, a, 4.0))
    cv.polygon(pts, MANE, name="mane", sep="deep")
    # strands
    for i in range(2, n - 1, 3):
        a = a0 + (a1 - a0) * i / n
        q0, q1 = px.polar(S, a, 6.5), px.polar(S, a + 6, 10.5)
        cv.line((round(q0[0]), round(q0[1])), (round(q1[0]), round(q1[1])), MANE.step(1), band=None, decal=True,
                clip="mane", name="mane")


def _head(cv, H, p):
    """Round furred head, white mane cap, dark face with a muzzle, heavy brow."""
    cv.circle(H[0], H[1], 5.6, FUR, name="head", sep="deep")
    cv.ellipse(H[0] - 1.4, H[1] - 3.2, 4.6, 3.0, MANE, shade="soft", decal=True, clip="head")
    # face + muzzle (the jaw drops for a roar)
    face = cv.union(cv.geom_ellipse(H[0] + 2.4, H[1] + 0.2, 3.4, 3.8),
                    cv.geom_ellipse(H[0] + 4.4, H[1] + 2.4, 3.0, 2.4))
    cv.draw_geom(face, SKIN, name="face", sep="deep")
    if p.jaw > 0.05:
        with cv.xform(px.rotate(-30 * p.jaw, (H[0] + 2.0, H[1] + 3.2))):
            cv.limb([(H[0] + 2.0, H[1] + 3.6), (H[0] + 6.4, H[1] + 4.4)], [2.0, 1.4], SKIN, shade="nolight",
                    name="jaw", sep="deep")
        cv.pixels([(round(H[0] + 5.6), round(H[1] + 3.8)), (round(H[0] + 3.6), round(H[1] + 3.9))], TOOTH,
                  name="tooth")
    else:
        cv.line((round(H[0] + 3.6), round(H[1] + 3.6)), (round(H[0] + 6.4), round(H[1] + 3.4)), SKIN.deep,
                name="mouth")
    cv.pixels([(round(H[0] + 6.6), round(H[1] + 1.6))], SKIN.deep, name="nostril")
    # heavy brow ridge and the eye beneath it
    ex, ey = round(H[0] + 2.8), round(H[1] - 0.8)
    cv.limb([(H[0] + 0.6, H[1] - 2.4), (H[0] + 5.6, H[1] - 2.0)], [1.3, 1.0], SKIN, shade="two", name="brow")
    if p.eye == "squeeze":
        hc.eye_stamp(cv, ["kk.", "..k"], ex - 1, ey, {})
    elif p.eye == "dead":
        hc.eye_stamp(cv, ["k.k", ".k.", "k.k"], ex - 1, ey - 1, {})
    else:
        hc.eye_stamp(cv, ["gi", "ik"], ex, ey, {"i": IRIS})


def _boulder(cv, c, crack, r=7.0, name="rock"):
    g = cv.union(cv.geom_ellipse(c[0], c[1], r, r * 0.86, angle=12),
                 cv.geom_ellipse(c[0] + r * 0.35, c[1] - r * 0.3, r * 0.7, r * 0.6))
    cv.draw_geom(g, STONE, name=name, sep="deep")
    cv.ellipse(c[0] - r * 0.2, c[1] - r * 0.62, r * 0.55, r * 0.28, MOSS, shade="two", decal=True, clip=name)
    seams = [((-0.5, -0.1), (0.2, 0.3)), ((0.2, 0.3), (0.55, 0.1))]
    if crack >= 1:
        seams += [((0.0, -0.8), (-0.1, -0.1)), ((-0.1, -0.1), (-0.6, 0.5)), ((0.2, 0.3), (0.1, 0.85))]
    if crack >= 2:
        seams += [((0.55, 0.1), (0.9, -0.3)), ((-0.6, 0.5), (-0.9, 0.2))]
    for a, b in seams:
        cv.line((round(c[0] + a[0] * r), round(c[1] + a[1] * r)), (round(c[0] + b[0] * r), round(c[1] + b[1] * r)),
                STONE.step(2), band=None, decal=True, clip=name, name=name)


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    ground = cv.ground
    P = (cv.gx - 11 + p.bx, ground - 19.5 + p.by)
    tilt = p.tilt
    S = px.polar(P, tilt, SPINE)
    br = p.breathe
    xf = [px.scale(K, K, (cv.gx, ground))]
    if p.rot:  # topple backwards: pivot on the heels, then lie flat about the pelvis
        xf.append(px.rotate(p.rot, (P[0] - 3, ground) if p.rot < 60 else P))
        cv.snap_ground = True
    hips = [(P[0] + 1.0, P[1] + 3.0), (P[0] + 3.0, P[1] + 2.0)]  # near, far
    shoulders = [px.polar(S, tilt - 90, 3.5), px.polar(S, tilt - 70, 4.5)]  # near, far

    def foot(i):
        f = p.fn if i == 0 else p.ff
        return (P[0] + (1.5 if i == 0 else 4.0) + f[0], ground - f[1])

    def knuckles(i):
        k = p.kn if i == 0 else p.kf
        base = S[0] + (6.5 if i == 0 else 9.0)
        return (base + k[0], ground - k[1])

    def hand(i):
        h = p.hn if i == 0 else p.hf
        if h is not None and p.rock == "lift":  # hands on the sides of the grounded boulder
            return (S[0] + h[0] - (1.0 if i == 0 else -3.0), ground - 5.0)
        return None if h is None else (S[0] + h[0], S[1] + h[1])

    with cv.xform(*xf):
        # far limbs
        _leg(cv, hips[1], foot(1), True)
        hf = hand(1)
        _arm(cv, shoulders[1], hf if hf else knuckles(1), True, knuckle=hf is None, bend=-1 if hf is None else 1)
        # torso: hips + big chest as one form
        chest_c = px.lerp_pt(P, S, 0.7)
        g = cv.union(cv.geom_ellipse(P[0], P[1], 8.0, 7.4 + br * 0.3, angle=tilt * 0.5),
                     cv.geom_ellipse(chest_c[0], chest_c[1], 12.0, 10.4 + br, angle=tilt),
                     weights=[0.85, 1.0])
        cv.draw_geom(g, FUR, name="body")
        for k in range(3):  # fur strands on the flank
            q = px.lerp_pt(P, S, 0.2 + 0.2 * k)
            a0, a1 = px.polar(q, tilt + 110, 3.0), px.polar(q, tilt + 150, 7.0)
            cv.line((round(a0[0]), round(a0[1])), (round(a1[0]), round(a1[1])), FUR.step(1), band=None, decal=True,
                    clip="body", name="body")
        _leg(cv, hips[0], foot(0), False)
        # boulder: behind the near arm
        rc = None
        if p.rock == "lift":  # gripping the boulder where it lies
            rc = (S[0] + p.hn[0] + 2.5, ground - 5.6)
            _boulder(cv, rc, p.crack)
        elif p.rock == "held":
            hn_ = hand(0)
            rc = (hn_[0] + 2.5, hn_[1] - 5.5)
            _boulder(cv, rc, p.crack)
        elif isinstance(p.rock, tuple):
            rc = (knuckles(0)[0] + 9.0 + p.rock[1], ground - 5.2)
            _boulder(cv, rc, p.crack, r=6.4)
        hn = hand(0)
        overhead = hn is not None and hn[1] < S[1] - 4
        if not overhead:
            _arm(cv, shoulders[0], hn if hn else knuckles(0), False, knuckle=hn is None, bend=-1 if hn is None else 1)
        # the mane crest and the head sit on top of the shoulder
        _mane(cv, S, tilt, p.mane)
        H = px.polar(S, tilt - 55, 7.5)
        with cv.xform(px.rotate(p.head, H)):
            _head(cv, H, p)
        if overhead:  # arms raised: the near arm passes in front of the head
            _arm(cv, shoulders[0], hn, False, knuckle=False, bend=1)
        if p.rock in ("held", "lift"):  # near fingers wrap over the front of the boulder
            cv.circle(hn[0] + 0.5, hn[1] - 0.5, 2.6, SKIN, shade="two", name="hand", sep="deep")

    if p.dust is not None:
        fx = cv.layer(above=True, outline=True)
        x0 = rc[0] if rc else P[0] + 6
        gy = cv.gy - 1 - hc.snap_offset(cv)
        px.dust(fx, x0 - 5, gy, p.dust, size=1.2, direction=-1)
        px.dust(fx, x0 + 5, gy, p.dust * 0.9, size=1.0, direction=1)
    if p.chips is not None and rc is not None:
        ch = cv.layer(above=True, outline=True)
        t = p.chips
        for k, (vx, vy) in enumerate(((-4, 7), (3, 8), (5, 5), (-1, 9))):
            x = rc[0] + vx * t * 1.6
            y = ground - 6 - (vy * t * 1.8 - 6 * t * t)
            ch.circle(x, y, 1.1, STONE, shade="two", name="chip")
    if p.hit and rc is not None:
        top = cv.layer(above=True, outline=False)
        px.impact(top, rc[0] + 5, rc[1] - 5, size=4)
