"""Snow ape - a huge white-furred mountain ape of the Rimefrost Heights (Ice / Earth).

Azure Expanse, Rimefrost Heights - Snow Ape Ledges (68-72), a heavy brute.  Built on the
cliff ape rig (cell 192) but bulkier and shaggier: a deeper chest, a thick shoulder cape
of long white locks, a fringe under the belly and rump, and long forearm fur crusted with
frost clumps and icicles.  Snow-white fur lit warm cream and shaded cool blue-violet, a
pale blue-grey leathery face under a heavy brow, two small tusks and frost-blue glowing
eyes; dark slate hands and feet.
Rig: pelvis P and shoulders S on a spine tilted by ``tilt`` (30 = knuckle stance,
80 = upright).  Legs and arms are two-bone limbs solved with ``px.ik2``.
Idle: breathing and a snort of frosty breath.  Windup: rears up and heaves a great block
of ice overhead (held, with a glint); attack: slams it down in front (hit on frame 1) with
ice shards and snow spray; death: overbalanced by the block it topples backwards, the
block shatters behind it and it lies still.
"""
import math

import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "snow_ape",
    "cell": 192,
    "anchor": [96, 168],
    "flying": False,
    "hit_frame": 1,
}

# ---- palette: snow-white fur (cream lights, blue-violet shadows), slate skin, glacier ice ----
FUR = px.material("snow_ape_fur", "#fffaec", "#e3e6ef", "#aab0cd", "#757ba1", outline="#17162b",
                  thresholds=(0.86, 0.48, 0.14))
SKIN = px.material("snow_ape_skin", "#aebbcc", "#7a869e", "#535d76", "#363d55", outline="#0f111d")
ICE = px.material("snow_ape_ice", "#f0fcff", "#a9e2f3", "#5fa6d0", "#38679c", outline="#0d1b35",
                  thresholds=(0.88, 0.5, 0.18))
SNOW = px.material("snow_ape_snow", "#ffffff", "#deebf4", "#adc2d6", "#8093b0", outline="#334560")
IRIS = px.rgb("#86ecff")  # frost-blue eye glow
TUSK = px.rgb("#f4eedb")

# ---- poses ------------------------------------------------------------------------------------
# bx, by    pelvis offset       tilt  spine angle (deg: 0 flat, 90 upright)
# head      head tilt (deg)     jaw   roar 0..1        eye  angry|squeeze|dead
# hn, hf    near / far hand target relative to the shoulder (None = knuckles on the ground)
# kn, kf    knuckle offsets on the ground (dx, lift) for near / far hands
# fn, ff    near / far foot (dx, lift)         breathe  chest swell       shag  fur ruffle phase
# ice       None | "lift" (gripped on the ground) | "held" (in the hands) | ("ground", dx) slammed |
#           "fall" (tumbling off behind) | ("shatter", t) | "rubble"
# crack     block cracks 0..2      dust  snow dust life     shards  flying ice shard life
# breath    frosty breath puff life     glint  sparkle on the held block
# rot       whole-body roll for the topple (deg, + = backwards)
DEFAULTS = dict(bx=0, by=0, tilt=30, head=0, jaw=0.0, eye="angry", hn=None, hf=None, kn=(0, 0), kf=(0, 0),
                fn=(0, 0), ff=(0, 0), breathe=0.0, shag=0.0, ice=None, crack=0, dust=None, shards=None,
                breath=None, glint=False, hit=False, rot=0, fade=1.0, iang=0)

POSE = px.poses(DEFAULTS, {
    "idle": [  # heavy breathing, then a snort of frosty breath
        dict(),
        dict(breathe=0.5, shag=1.0, head=2),
        dict(breathe=0.9, shag=2.0, head=4, by=-1, jaw=0.35, breath=0.2),
        dict(breathe=0.3, shag=3.0, head=1, breath=0.7),
    ],
    "walk": [  # knuckle walk: near hand + far foot swing together, then swap
        dict(kn=(5, 0), kf=(-3, 0), fn=(-4, 0), ff=(3, 0), shag=0.0),
        dict(kn=(3, 0), kf=(0, 3), fn=(-2, 0), ff=(0, 2), shag=1.0, by=-1, tilt=31),
        dict(kn=(0, 0), kf=(4, 2), fn=(0, 2), ff=(-2, 0), shag=2.0, by=-1),
        dict(kn=(-3, 0), kf=(5, 0), fn=(3, 0), ff=(-4, 0), shag=3.0),
        dict(kn=(0, 3), kf=(3, 0), fn=(0, 2), ff=(-2, 0), shag=4.0, by=-1, tilt=31),
        dict(kn=(4, 2), kf=(0, 0), fn=(-2, 0), ff=(0, 2), shag=5.0, by=-1),
    ],
    "windup": [  # grips a block of ice, heaves it up and rears with it overhead - held
        dict(tilt=22, by=3, bx=2, head=-10, hn=(9, 25), hf=(11, 25), ice="lift", jaw=0.2, fn=(-2, 0), ff=(1, 0)),
        dict(tilt=56, by=-1, bx=-1, head=8, hn=(8, -3), hf=(10, -4), ice="held", jaw=0.5, shag=1.5,
             fn=(-2, 0), ff=(2, 0)),
        dict(tilt=72, by=0, bx=-3, head=14, hn=(2, -10), hf=(4, -11), ice="held", jaw=0.9, shag=3.0,
             fn=(-3, 0), ff=(3, 0), breathe=0.6, glint=True),
    ],
    "attack": [  # slams the block down in front: hit on frame 1, shards + snow spray
        dict(tilt=62, by=-1, bx=0, head=0, hn=(13, -9), hf=(14, -10), ice="held", jaw=1.0, shag=4.0,
             fn=(-2, 0), ff=(3, 0), iang=-10),
        dict(tilt=45, by=1, bx=-3, head=8, hn=(24, 18), hf=(26, 17), ice=("ground", 0), crack=1, jaw=1.0,
             dust=0.2, shards=0.25, hit=True, fn=(0, 0), ff=(4, 0), shag=5.0),
        dict(tilt=41, by=1, bx=-2, head=2, hn=(23, 19), hf=(25, 18), ice=("ground", 0), crack=2, jaw=0.5,
             dust=0.5, shards=0.6, fn=(0, 0), ff=(4, 0), shag=0.0),
        dict(tilt=30, bx=0, head=0, ice=("ground", 0), crack=2, dust=0.85, shag=1.0, kn=(1, 0)),
    ],
    "hurt": [
        dict(tilt=44, bx=-4, by=-2, head=18, eye="squeeze", jaw=0.6, hn=(-2, 8), kf=(2, 0), shag=2.0),
        dict(tilt=36, bx=-2, head=8, eye="squeeze", jaw=0.2, shag=1.0),
    ],
    "death": [  # reels back as the block tips over, topples onto it, the block shatters, lies still
        dict(tilt=84, bx=1, by=-1, head=24, eye="squeeze", jaw=0.8, hn=(-3, -8), hf=(-1, -9), ice="held",
             iang=22, shag=2.0),
        dict(tilt=98, bx=2, by=-1, head=30, eye="dead", jaw=0.6, hn=(-7, -7), hf=(-5, -8), ice="held", iang=58,
             shag=3.0, fn=(2, 0), ff=(4, 0)),
        dict(tilt=80, bx=19, head=20, eye="dead", jaw=0.5, hn=(-6, -12), hf=(-4, -14), rot=40, shag=4.0,
             fn=(3, 0), ff=(5, 0), ice=("fx", -20, -8, 0, 2), shards=0.12),
        dict(tilt=84, bx=19, head=14, eye="dead", jaw=0.4, hn=(9, 6), hf=(11, 3), rot=86, shag=5.0,
             fn=(4, 3), ff=(7, 5), dust=0.3, ice=("burst", -22), shards=0.45),
        dict(tilt=84, bx=19, head=10, eye="dead", jaw=0.4, hn=(10, 8), hf=(12, 5), rot=90, shag=5.0,
             fn=(5, 2), ff=(8, 3), ice=("rubble", -24)),
    ],
})

L_THIGH, L_SHIN = 8.5, 8.5
L_UPPER, L_FORE = 13.0, 14.0
SPINE = 20.0
K = 1.2  # overall scale of the rig (drawn about the anchor)

# ice block: half width / half height of the front face and the depth offset of the top face
BW, BH, BD = 7.0, 5.5, (2.5, -3.0)


# ---- parts ------------------------------------------------------------------------------------
def _erad(rx, ry, major_deg, dir_deg):
    """Radius of an ellipse (radii rx, ry, major axis at major_deg) along direction dir_deg."""
    phi = math.radians(dir_deg - major_deg)
    return 1.0 / math.sqrt((math.cos(phi) / rx) ** 2 + (math.sin(phi) / ry) ** 2)


def _lock(cv, root, tip, r=1.8):
    """One tapered lock of fur (a geom for ``cv.union``)."""
    return cv.geom_limb([root, tip], [r, 0.35])


def _leg(cv, hip, foot, far):
    shade = "dark" if far else "two"
    ankle = (foot[0] - 1.0, foot[1] - 2.3)
    knee = px.ik2(hip, ankle, L_THIGH, L_SHIN, bend=1)
    g = [cv.geom_limb([hip, knee, ankle], [4.8, 3.8, 2.9])]
    # shaggy fur hanging off the back of the thigh
    q = px.lerp_pt(hip, knee, 0.6)
    g.append(_lock(cv, q, (q[0] - 4.2, q[1] + 3.2), 1.9))
    cv.draw_geom(cv.union(*g, weights=[1.0, 0.6]), FUR, shade=shade, name="leg", sep=False if far else "deep")
    cv.ellipse(foot[0] + 1.0, foot[1] - 1.2, 4.0, 1.8, SKIN, shade="dark" if far else "two", name="foot")


def _arm(cv, shoulder, hand, far, floor, knuckle=True, bend=-1):
    """Massive arm: thick upper arm, forearm with long hanging frosted fur, slate fist."""
    shade = "dark" if far else "soft"
    nm = "arm_far" if far else "arm"
    wrist = (hand[0] - 0.5, hand[1] - 3.8) if knuckle else hand
    d = math.hypot(wrist[0] - shoulder[0], wrist[1] - shoulder[1])
    elbow = px.ik2(shoulder, wrist, L_UPPER, L_FORE, bend=bend) if d < L_UPPER + L_FORE - 0.5 else \
        px.lerp_pt(shoulder, wrist, L_UPPER / (L_UPPER + L_FORE))
    geoms = [cv.geom_limb([shoulder, elbow, wrist], [5.2, 4.3, 3.6])]
    # long locks hanging from the back / underside of the forearm
    dx, dy = wrist[0] - elbow[0], wrist[1] - elbow[1]
    ln = math.hypot(dx, dy) or 1.0
    n = (-dy / ln, dx / ln)
    if n[1] - 0.6 * n[0] < -n[1] + 0.6 * n[0]:
        n = (-n[0], -n[1])
    tips = []
    for t, L in ((0.05, 5.5), (0.4, 5.2), (0.72, 4.4)):
        q = px.lerp_pt(elbow, wrist, t)
        root = (q[0] + n[0] * 2.4, q[1] + n[1] * 2.4)
        tip = (root[0] + n[0] * L * 0.55 - 0.8, min(floor - 2.0, root[1] + n[1] * L * 0.55 + L * 0.65))
        geoms.append(_lock(cv, root, tip, 2.0))
        tips.append(tip)
    cv.draw_geom(cv.union(*geoms, weights=[1.0, 0.55, 0.55, 0.55]), FUR, shade=shade, name=nm,
                 sep=False if far else "deep")
    if knuckle:
        cv.ellipse(hand[0] + 0.6, hand[1] - 1.7, 3.4, 1.9, SKIN, shade="dark" if far else "two",
                   name="hand", sep=False if far else "deep")
    else:
        cv.circle(hand[0], hand[1], 3.1, SKIN, shade="dark" if far else "two", name="hand",
                  sep=False if far else "deep")
    # a crust of frost on the forearm fur, and frost clumps with icicles hanging from the locks
    q = px.lerp_pt(elbow, wrist, 0.55)
    cv.ellipse(q[0] + n[0] * 1.2, q[1] + n[1] * 1.2, 2.6, 1.7, ICE, angle=math.degrees(math.atan2(-dy, dx)),
               name=nm, decal=True, clip=nm)
    for k, tip in enumerate(tips[:2] if not far else tips[1:2]):
        c = (tip[0] + 0.4, tip[1] - 1.0)
        cv.circle(c[0], c[1], 1.4, ICE, shade="two" if far else "soft", name="frost")
        drop = min(3.8 - k * 0.9, floor - 1.0 - c[1])
        if drop > 1.2:
            cv.limb([(c[0], c[1] + 0.6), (c[0] + 0.1, c[1] + 0.6 + drop)], [0.9, 0.3], ICE,
                    shade="two" if far else "soft", name="frost")
    return elbow


def _cape(cv, S, tilt, ruffle):
    """Thick shaggy shoulder cape: long white locks swept back over the shoulders and nape."""
    n = 12
    a0, a1 = tilt - 70, tilt + 160
    outer = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        if i % 2:  # lock tip: hangs down at the chest, sweeps back over the top and the back
            sweep = -8.0 if a < tilt - 15 else (9.0 if a < tilt + 40 else 14.0)
            r = 13.4 + 0.7 * math.sin(ruffle + i * 1.3) - (1.6 if i in (1, n - 1) else 0.0)
            outer.append(px.polar(S, a + sweep, r))
        else:
            outer.append(px.polar(S, a, 10.4))
    inner = [px.polar(S, a0 + (a1 - a0) * i / n, 4.0) for i in range(n, -1, -1)]
    cv.polygon(outer + inner, FUR, name="cape", sep="deep")
    for i in range(1, n, 2):  # strands down the middle of each lock
        a = a0 + (a1 - a0) * i / n
        q0, q1 = px.polar(S, a - 3, 7.0), px.polar(S, a + 2, 11.0)
        cv.line((round(q0[0]), round(q0[1])), (round(q1[0]), round(q1[1])), FUR.step(1), band=None, decal=True,
                clip="cape", name="cape")


def _head(cv, H, p):
    """Shaggy white head with cheek fur, pale slate face, heavy brow, tusks, frost-blue eye."""
    g = cv.union(cv.geom_ellipse(H[0], H[1], 6.0, 5.7),
                 _lock(cv, (H[0] - 2.5, H[1] + 2.5), (H[0] - 5.5, H[1] + 7.0), 2.4),
                 _lock(cv, (H[0] + 0.5, H[1] + 3.5), (H[0] - 0.5, H[1] + 7.8), 2.2),
                 weights=[1.0, 0.5, 0.5])
    cv.draw_geom(g, FUR, name="head", sep="deep")
    face = cv.union(cv.geom_ellipse(H[0] + 2.6, H[1] + 0.3, 3.5, 3.9),
                    cv.geom_ellipse(H[0] + 4.7, H[1] + 2.5, 3.1, 2.5))
    cv.draw_geom(face, SKIN, name="face", sep="deep")
    if p.jaw > 0.05:
        with cv.xform(px.rotate(-30 * p.jaw, (H[0] + 2.0, H[1] + 3.2))):
            cv.limb([(H[0] + 2.0, H[1] + 3.7), (H[0] + 6.5, H[1] + 4.5)], [2.0, 1.5], SKIN, shade="nolight",
                    name="jaw", sep="deep")
            cv.pixels([(math.floor(H[0] + 6.0), math.floor(H[1] + 2.6)), (math.floor(H[0] + 6.0), math.floor(H[1] + 3.6)),
                       (math.floor(H[0] + 4.2), math.floor(H[1] + 3.2))], TUSK, name="tusk")
    else:
        cv.line((math.floor(H[0] + 3.4), math.floor(H[1] + 3.8)), (math.floor(H[0] + 7.0), math.floor(H[1] + 3.6)),
                SKIN.deep, name="mouth")
        cv.pixels([(math.floor(H[0] + 6.0), math.floor(H[1] + 2.6)), (math.floor(H[0] + 6.0), math.floor(H[1] + 1.9)),
                   (math.floor(H[0] + 4.3), math.floor(H[1] + 2.9))], TUSK, name="tusk")
    cv.pixels([(math.floor(H[0] + 6.9), math.floor(H[1] + 1.2))], SKIN.deep, name="nostril")
    # heavy brow ridge under a shaggy white fringe, the glowing eye in its shadow
    ex, ey = math.floor(H[0] + 2.8), math.floor(H[1] - 1.0)
    cv.limb([(H[0] + 0.2, H[1] - 2.6), (H[0] + 3.2, H[1] - 2.8), (H[0] + 6.4, H[1] - 1.7)], [1.6, 1.5, 1.0],
            SKIN.step(1), shade="two", name="brow")
    cv.draw_geom(cv.union(_lock(cv, (H[0] - 1.0, H[1] - 4.4), (H[0] + 5.6, H[1] - 3.6), 1.5),
                          _lock(cv, (H[0] + 0.5, H[1] - 5.2), (H[0] + 3.8, H[1] - 4.6), 1.3)),
                 FUR, shade="two", name="head")
    if p.eye == "squeeze":
        hc.eye_stamp(cv, ["kk.", "..k"], ex - 1, ey, {})
    elif p.eye == "dead":
        hc.eye_stamp(cv, ["k.k", ".k.", "k.k"], ex - 1, ey - 1, {})
    else:
        hc.eye_stamp(cv, ["gi", "ii"], ex, ey, {"i": IRIS})


def _block_faces(c):
    x0, x1, y0, y1 = c[0] - BW, c[0] + BW, c[1] - BH, c[1] + BH
    dx, dy = BD
    front = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    top = [(x0, y0), (x0 + dx, y0 + dy), (x1 + dx, y0 + dy), (x1, y0)]
    side = [(x1, y0), (x1 + dx, y0 + dy), (x1 + dx, y1 + dy), (x1, y1)]
    return front, top, side


def _ice_block(cv, c, crack=0, ang=0.0, name="ice", sep="deep", pivot=None):
    """A great block of glacier ice: lit top, clear front face with a glint, shaded side.
    ``ang`` tilts it about ``pivot`` (default: its own centre)."""
    with cv.xform(px.rotate(ang, c if pivot is None else pivot)):
        front, top, side = _block_faces(c)
        whole = cv.mask_polygon(front) | cv.mask_polygon(top) | cv.mask_polygon(side)
        cv.fill(whole, ICE, shade=1, name=name, sep=sep)
        cv.polygon(top, ICE, shade=0, name=name, clip=name)
        cv.polygon(side, ICE, shade=2, name=name, clip=name)
        x0, y0 = c[0] - BW, c[1] - BH
        # frozen cloudy core and the glint streak
        cv.ellipse(c[0] + 1.0, c[1] + 1.4, 3.6, 2.4, ICE, shade=2, name=name, clip=name)
        cv.line((math.floor(x0 + 2), math.floor(y0 + 5)), (math.floor(x0 + 5), math.floor(y0 + 2)), ICE.light,
                name=name, clip=name)
        cv.line((math.floor(x0 + 3), math.floor(y0 + 7)), (math.floor(x0 + 4), math.floor(y0 + 6)), ICE.light,
                name=name, clip=name)
        seams = []
        if crack >= 1:
            seams += [((0.1, -1.0), (-0.1, -0.1)), ((-0.1, -0.1), (-0.6, 0.6)), ((-0.1, -0.1), (0.5, 0.4))]
        if crack >= 2:
            seams += [((0.5, 0.4), (0.9, -0.3)), ((-0.6, 0.6), (-0.9, 0.2)), ((0.5, 0.4), (0.4, 1.0))]
        for a, b in seams:
            cv.line((math.floor(c[0] + a[0] * BW), math.floor(c[1] + a[1] * BH)),
                    (math.floor(c[0] + b[0] * BW), math.floor(c[1] + b[1] * BH)),
                    ICE.step(2), band=None, decal=True, clip=name, name=name)


def _shards(fx, c, t, n=6, seed=0, reach=1.0, aim=(25, 155)):
    """Ice shards bursting up and out of point c for life t (``aim`` = fan of angles, 90 = up)."""
    for k in range(n):
        h = px.hash01(seed, k)
        a = aim[0] + (aim[1] - aim[0]) * (k + 0.5 * h) / n
        v = (6.0 + 5.0 * px.hash01(seed, k, 3)) * reach
        x = c[0] + math.cos(math.radians(a)) * v * t * 1.5
        y = c[1] - math.sin(math.radians(a)) * v * t * 1.7 + 6.0 * t * t
        rot = 360 * px.hash01(seed, k, 5)
        s = 1.9 + 0.8 * h
        pts = [px.polar((x, y), rot, s * 1.6), px.polar((x, y), rot + 90, s * 0.7), px.polar((x, y), rot + 180, s),
               px.polar((x, y), rot + 270, s * 0.7)]
        fx.polygon(pts, ICE, shade="soft", name="shard")


def _rubble(fx, x, gy, front=False):
    """Broken ice chunks lying on the ground around x (gy = ground line): a few angular
    lumps behind the body, or a couple of small ones in front of it."""
    chunks = ((-8.0, 3.2, 3.4, 0.3), (-1.5, 4.4, 5.6, -0.4), (5.5, 3.0, 3.2, 0.5)) if not front else \
        ((-9.5, 2.2, 2.2, -0.3), (3.0, 2.6, 2.6, 0.4))
    for dx, w, hgt, lean in chunks:
        cx, base = x + dx, gy - 1.0
        a, b = (cx - w * 0.7 + lean, base - hgt), (cx + w * 0.4 + lean, base - hgt - 0.6)
        fx.polygon([(cx - w, base), a, b, (cx + w, base - hgt * 0.4), (cx + w, base)], ICE, shade="two",
                   name="rubble")
        fx.line((math.floor(a[0]) + 1, math.floor(a[1]) + 1), (math.floor(b[0]), math.floor(b[1]) + 1), ICE.light,
                name="rubble", clip="rubble")


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    ground = cv.ground
    P = (cv.gx - 11 + p.bx, ground - 20.0 + p.by)
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
        if h is not None and p.ice == "lift":  # hands on the sides of the block on the ground
            return (S[0] + h[0] - (1.0 if i == 0 else -3.0), ground - 5.0)
        return None if h is None else (S[0] + h[0], S[1] + h[1])

    pts = {}
    with cv.xform(*xf):
        # far limbs
        _leg(cv, hips[1], foot(1), True)
        hf = hand(1)
        _arm(cv, shoulders[1], hf if hf else knuckles(1), True, ground, knuckle=hf is None,
             bend=-1 if hf is None else 1)
        # torso: hips + deep chest as one form, with a shaggy fringe under the belly and rump
        chest_c = px.lerp_pt(P, S, 0.68)
        crx, cry = 13.4, 11.2 + br
        g = [cv.geom_ellipse(P[0], P[1], 8.8, 8.0 + br * 0.3, angle=tilt * 0.5),
             cv.geom_ellipse(chest_c[0], chest_c[1], crx, cry, angle=tilt)]
        for d in (248, 268, 288):
            r = _erad(crx, cry, tilt, d)
            g.append(_lock(cv, px.polar(chest_c, d, r * 0.7), px.polar(chest_c, d - 14, r + 3.6), 2.2))
        for d, ln in ((tilt + 150, 10.5), (tilt + 180, 10.0)):  # rump locks, hanging down and back
            g.append(_lock(cv, px.polar(P, d, 5.5), px.polar(P, d + 22, ln), 2.3))
        cv.draw_geom(cv.union(*g, weights=[0.85, 1.0] + [0.5] * (len(g) - 2)), FUR, name="body")
        for k in range(3):  # fur strands on the flank
            q = px.lerp_pt(P, S, 0.2 + 0.2 * k)
            a0, a1 = px.polar(q, tilt + 110, 3.0), px.polar(q, tilt + 150, 7.0)
            cv.line((round(a0[0]), round(a0[1])), (round(a1[0]), round(a1[1])), FUR.step(1), band=None, decal=True,
                    clip="body", name="body")
        _leg(cv, hips[0], foot(0), False)
        # the ice block: behind the near arm
        rc, piv = None, None
        if p.ice == "lift":  # gripping the block where it lies
            rc = (S[0] + p.hn[0] + 2.5, ground - BH + 0.4)
        elif p.ice == "held":
            piv = hand(0)
            rc = (piv[0] + 1.0, piv[1] - BH + 0.5)
        elif isinstance(p.ice, tuple) and p.ice[0] == "ground":  # slammed down at a fixed spot
            rc = (cv.gx + 23.0 + p.ice[1], ground - BH + 0.4)
        if rc is not None:
            _ice_block(cv, rc, p.crack, ang=p.iang, pivot=piv)
            pv = rc if piv is None else piv
            pts["ice"] = cv.tp(px.rot_pt(rc, p.iang, pv))
            pts["ice_top"] = cv.tp(px.rot_pt((rc[0] - BW + BD[0], rc[1] - BH + BD[1]), p.iang, pv))
        hn = hand(0)
        overhead = hn is not None and hn[1] < S[1] - 4
        if not overhead:
            _arm(cv, shoulders[0], hn if hn else knuckles(0), False, ground, knuckle=hn is None,
                 bend=-1 if hn is None else 1)
        # the shaggy cape and the head sit on top of the shoulders
        _cape(cv, S, tilt, p.shag)
        H = px.polar(S, tilt - 55, 7.5)
        with cv.xform(px.rotate(p.head, H)):
            _head(cv, H, p)
            pts["nose"] = cv.tp((H[0] + 7.5, H[1] + 2.0))
            pts["head"] = cv.tp(H)
        if overhead:  # arms raised: the near arm passes in front of the head
            _arm(cv, shoulders[0], hn, False, ground, knuckle=False, bend=1)
        if p.ice in ("held", "lift"):  # near fingers wrap over the front of the block
            cv.circle(hn[0] + 0.5, hn[1] - 0.5, 2.7, SKIN, shade="two", name="hand", sep="deep")

    so = hc.snap_offset(cv)
    gy = cv.gy - 1 - so  # the ground line before the snap (FX land on it after the snap)
    if isinstance(p.ice, tuple) and p.ice[0] == "fx":  # the block tumbling free / landing behind
        _, dx, dy, ang, crack = p.ice
        c = (cv.gx + dx, cv.gy - so + dy)
        back = cv.layer(above=False, outline=True)
        with back.xform(px.scale(K, K, c)):
            _ice_block(back, c, crack, ang=ang, sep=False)
        pts["ice"] = c
    if isinstance(p.ice, tuple) and p.ice[0] in ("burst", "rubble"):  # crushed under the falling ape
        x0 = cv.gx + p.ice[1]
        pts["ice"] = (x0, gy - 6)
        _rubble(cv.layer(above=False, outline=True), x0, gy)
        _rubble(cv.layer(above=True, outline=True), x0, gy, front=True)
    if p.dust is not None:
        fx = cv.layer(above=True, outline=True)
        x0 = pts["ice"][0]
        px.dust(fx, x0 - 7, gy, p.dust, size=1.35, direction=-1, mat=SNOW)
        px.dust(fx, min(x0 + 7, cv.w - 16), gy, p.dust * 0.9, size=1.15, direction=1, mat=SNOW)
    if p.shards is not None:
        if action == "attack":
            _shards(cv.layer(above=True, outline=True), (pts["ice"][0] + 4, gy - 3), p.shards, n=6, seed=2)
        else:  # thrown up and back out from under the falling ape
            _shards(cv.layer(above=True, outline=True), (pts["ice"][0] - 2, gy - 4), p.shards, n=6, seed=5,
                    reach=1.3, aim=(70, 175))
    if p.hit:
        top = cv.layer(above=True, outline=False)
        px.impact(top, pts["ice"][0] + 10, gy - 5, size=4, color=IRIS)
    if p.glint:  # a cold glint flashes off the held block's top corner
        top = cv.layer(above=True, outline=False)
        gx_, gy_ = pts["ice_top"]
        px.impact(top, gx_, gy_, size=3, color=IRIS)
    if p.breath is not None:  # a snort of frosty breath, blown down and forward, then drifting up
        fx2 = cv.layer(above=True, outline=True)
        t = p.breath
        nx, ny = pts["nose"]
        for k, (d, r) in enumerate(((2.0, 1.1), (6.0, 1.5), (10.5, 1.8))):
            if t < k * 0.3:
                continue
            fx2.circle(nx + d + t * 2.0, ny + 1.5 - k * 1.0 - t * 1.2, r * (0.7 + 0.3 * t), SNOW, shade="soft",
                       name="breath")
