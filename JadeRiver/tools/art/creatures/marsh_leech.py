"""Marsh leech - fat, glossy dark-olive swamp leech with a toothed sucker mouth (Water).

View: side, facing right.  ~12 art px tall, ~28 long when stretched.
The body is one tapered tube along a smooth spine (Catmull-Rom through a few control
points per pose), so the inchworm arch, the rear-up and the lunge share one drawing.
Parts, back to front: tube body (+ pale olive belly, a dashed teal Water flank
stripe, a glossy wet highlight streak), rear sucker pad, front sucker disc (dark
throat ringed with pale teeth, turns toward the viewer as it opens), small amber eye.
"""
import math

import helpers_batch_a as hb
import pixel as px

SPEC = {
    "id": "marsh_leech",
    "cell": 128,
    "anchor": [64, 112],
    "flying": False,
    "hit_frame": 1,
}

# ---- palette: dark wet olive, olive-ochre belly, teal Water spots, fleshy sucker ---------
SKIN = px.material("leech_skin", "#7b8645", "#4d5631", "#343c27", "#22291e", outline="#090c08",
                   thresholds=(0.86, 0.5, 0.18))
BELLY = px.material("leech_belly", "#a99a57", "#7d713f", "#5a5134", "#3d3829", outline="#090c08")
SPOT = px.material("leech_spot", "#8fe3d0", "#3aa99c", "#237470", "#174a4d", outline="#0a0d09")
SUCKER = px.material("leech_sucker", "#c09a78", "#93695a", "#684848", "#452f33", outline="#140b0c")
GLOSS = px.rgb("#dce7a6")
STRIPE = px.rgb("#3fae9f")
STRIPE_DK = px.rgb("#237470")
THROAT = px.rgb("#2a1419")
TOOTH = px.rgb("#f4eed2")
IRIS = px.rgb("#e2a93c")
CREASE = SKIN.step(1)

# ---- poses --------------------------------------------------------------------------------
# spine   control points (dx from the body centre, lift of the underside above the ground)
#         listed rear -> front; the curve passes through them
# thick   body thickness factor     open  sucker opening 0..1 (turns toward the viewer)
# eye     open|angry|squeeze|dead   shrivel  0..1 dries and shrinks (death)
# fade    opacity   hit  impact fx   gulp  bulge travelling down the body (0..1 position)
FLAT = ((-14, 0), (-7, 0), (0, 0), (7, 0), (13, 1))
DEFAULTS = dict(spine=FLAT, thick=1.0, open=0.0, eye="open", shrivel=0.0, fade=1.0, hit=False, gulp=None,
                bx=0, dust=None)

POSE = px.poses(DEFAULTS, {
    "idle": [  # slow pulsing swell, front end probing
        dict(spine=((-14, 0), (-7, 0), (0, 0), (7, 0), (13, 1))),
        dict(spine=((-14, 0), (-7, 0), (0, 0), (7, 0.5), (13, 2)), thick=1.04),
        dict(spine=((-14, 0), (-7, 0), (0, 0), (7, 1), (13, 3)), thick=1.07, open=0.15),
        dict(spine=((-14, 0), (-7, 0), (0, 0), (7, 0.5), (13, 2)), thick=1.03),
    ],
    "walk": [  # inchworm: rear sucker creeps up into an arch, then the front reaches ahead
        dict(spine=((-14, 0), (-7, 0), (0, 0), (7, 0), (13, 1)), thick=0.94),
        dict(spine=((-11, 0), (-6, 2), (0, 3.5), (7, 0.5), (12, 1)), thick=1.0),
        dict(spine=((-8, 0), (-5, 5), (0, 8), (5, 4), (9, 0.5)), thick=1.08),
        dict(spine=((-7, 0), (-4, 5), (1, 7), (7, 5), (12, 2.5)), thick=1.06),
        dict(spine=((-8, 0), (-3, 3), (3, 4), (9, 2.5), (14, 1)), thick=1.0),
        dict(spine=((-12, 0), (-5, 1), (2, 1.5), (9, 0.5), (15, 1)), thick=0.95),
    ],
    "windup": [  # rears the front end up and back, sucker turning out, teeth bared - held
        dict(spine=((-14, 0), (-7, 0), (-1, 1), (4, 4), (7, 8)), thick=1.04, open=0.4, eye="angry"),
        dict(spine=((-14, 0), (-8, 0), (-3, 1), (1, 6), (3, 12)), thick=1.08, open=0.8, eye="angry"),
        dict(spine=((-14, 0), (-8, 0), (-4, 1), (0, 7), (1, 14)), thick=1.1, open=1.0, eye="angry"),
    ],
    "attack": [  # latch lunge: the front slams forward and down onto the target (frame 1)
        dict(spine=((-13, 0), (-6, 0), (1, 3), (8, 6), (15, 6)), thick=0.96, open=1.0, eye="angry"),
        dict(spine=((-11, 0), (-3, 0), (5, 2), (12, 2), (19, 1)), thick=0.9, open=0.9, eye="angry", hit=True),
        dict(spine=((-11, 0), (-4, 0.5), (4, 2), (11, 1.5), (17, 1)), thick=1.02, open=0.5, eye="angry",
             gulp=0.6),
        dict(spine=((-13, 0), (-6, 0), (1, 0.5), (8, 0.5), (14, 1.5)), thick=1.0, open=0.2, gulp=0.2),
    ],
    "hurt": [  # recoils: front snaps back up and curls, body clenches
        dict(spine=((-13, 0), (-7, 0), (-2, 1.5), (2, 5), (4, 9)), thick=1.1, open=0.3, eye="squeeze", bx=-3),
        dict(spine=((-13, 0), (-6, 0), (0, 1), (5, 3), (8, 5)), thick=1.05, open=0.1, eye="squeeze", bx=-2),
    ],
    "death": [  # writhes, curls, then dries and shrivels on the ground, fading
        dict(spine=((-13, 0), (-7, 0), (-2, 1.5), (2, 5), (4, 9)), thick=1.1, open=0.4, eye="squeeze", bx=-3),
        dict(spine=((-11, 1.5), (-6, 0), (0, 0), (5, 0.5), (9, 3)), thick=1.0, open=0.2, eye="dead", bx=-2),
        dict(spine=((-9, 0), (-5, 0), (0, 0), (5, 0), (8, 1.5)), thick=0.86, eye="dead", shrivel=0.4, bx=-2),
        dict(spine=((-8, 0), (-4, 0), (0, 0), (4, 0), (7, 1)), thick=0.74, eye="dead", shrivel=0.75, bx=-2,
             fade=0.6),
        dict(spine=((-8, 0), (-4, 0), (0, 0), (4, 0), (7, 0.5)), thick=0.66, eye="dead", shrivel=1.0, bx=-2,
             fade=0.3),
    ],
})

# radius profile along the body, rear (0) -> front (1): fat middle, rounded rear pad,
# a narrow neck behind the sucker
PROFILE = ((0.0, 3.4), (0.12, 4.5), (0.35, 5.6), (0.58, 5.3), (0.8, 3.7), (0.93, 2.5), (1.0, 2.3))


def _radius(t, thick):
    for (t0, r0), (t1, r1) in zip(PROFILE, PROFILE[1:]):
        if t <= t1:
            return (r0 + (r1 - r0) * (t - t0) / (t1 - t0)) * thick
    return PROFILE[-1][1] * thick


def _spine(cv, p, C):
    """Canvas points of the body centre line, rear -> front."""
    ctrl = []
    n = len(p.spine)
    for k, (dx, lift) in enumerate(p.spine):
        t = k / (n - 1)
        ctrl.append((C[0] + dx, cv.ground + 0.5 - _radius(t, p.thick) - lift))
    return hb.catmull(ctrl, per=3)


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    C = (cv.gx - 1 + p.bx, cv.ground)
    cv.opacity = p.fade
    cv.snap_ground = True  # the underside always rests on the ground row
    sp = _spine(cv, p, C)
    n = len(sp)
    ts = [k / (n - 1) for k in range(n)]
    radii = [_radius(t, p.thick) for t in ts]
    if p.gulp is not None:  # a swallowed gulp bulging back along the body
        radii = [r * (1.0 + 0.16 * math.exp(-((t - p.gulp) / 0.12) ** 2)) for r, t in zip(radii, ts)]
    skin = SKIN
    if p.shrivel > 0.5:
        skin = SKIN.step(1)
    cv.limb(sp, radii, skin, name="body")
    # pale belly along the underside
    under = []
    for k in range(1, n - 1):
        nx, ny = hb.normal_at(sp, k)
        under.append((sp[k][0] - nx * radii[k] * 0.72, sp[k][1] - ny * radii[k] * 0.72))
    cv.limb(under, [r * 0.42 for r in radii[1:n - 1]], BELLY, shade="two", decal=True, clip="body")
    # dashed teal Water stripe along the flank (dashes follow the body curve)
    if p.shrivel < 0.7:
        flank = []
        for k in range(1, n - 2):
            nx, ny = hb.normal_at(sp, k)
            flank.append((sp[k][0] + nx * radii[k] * 0.12, sp[k][1] + ny * radii[k] * 0.12))
        for k in range(0, len(flank) - 1, 3):
            a, b = flank[k], flank[k + 1]
            col = STRIPE if p.shrivel < 0.3 else STRIPE_DK
            cv.limb([a, px.lerp_pt(a, b, 0.8)], 0.5, px.flat(col), decal=True, clip="body")
    # wet gloss: a bright streak on the upper-left of the tube (drying away in death)
    if p.shrivel < 0.3:
        gl = []
        for k in range(2, max(3, int(n * 0.62))):
            nx, ny = hb.normal_at(sp, k)
            gl.append((sp[k][0] + nx * radii[k] * 0.6, sp[k][1] + ny * radii[k] * 0.6))
        if len(gl) >= 2:
            cv.limb(gl, 0.42, px.flat(GLOSS), decal=True, clip="body")
    # rear sucker pad: a flat darker foot on the ground
    rx_, ry_ = sp[0]
    cv.ellipse(rx_ - 0.5, ry_ + radii[0] * 0.55, radii[0] * 0.9, radii[0] * 0.5, skin, shade="dark", name="pad",
               sep="deep")
    # front sucker disc, facing along the body end, turning toward the viewer as it opens
    hx, hy = sp[-1]
    d = (sp[-1][0] - sp[-3][0], sp[-1][1] - sp[-3][1])
    ang = math.degrees(math.atan2(-d[1], d[0]))
    R = radii[-1] * 1.25
    face = 1.1 + 1.9 * p.open  # apparent width of the disc
    D = px.polar((hx, hy), ang, 1.2)
    cv.ellipse(D[0], D[1], face, R, SUCKER, angle=ang, name="sucker", sep="deep")
    if p.open > 0.25 and p.shrivel < 0.5:
        hole_w = max(0.6, face - 1.2)
        cv.ellipse(D[0] + 0.2, D[1], hole_w, R - 1.2, px.flat(THROAT), angle=ang, name="throat")
        # ring of pale teeth around the throat
        k_n = 7
        for k in range(k_n):
            a = 2 * math.pi * (k + 0.5) / k_n
            lx, ly = math.cos(a) * (hole_w + 0.35), math.sin(a) * (R - 0.9)
            q = px.rot_pt((D[0] + 0.2 + lx, D[1] + ly), ang, (D[0], D[1]))
            cv.pixel(math.floor(q[0]), math.floor(q[1]), TOOTH, name="tooth", clip="sucker")
    else:
        q = px.polar(D, ang, face * 0.6)
        cv.limb([px.polar(q, ang + 90, R * 0.55), px.polar(q, ang - 90, R * 0.55)], 0.5, px.flat(THROAT),
                name="throat", clip="sucker")
    # small amber eye on the neck, above and behind the sucker
    back = px.polar((hx, hy), ang + 180, 3.4)
    E = px.polar(back, ang + 90, radii[-3] * 0.35)
    ex, ey = math.floor(E[0]) - 1, math.floor(E[1]) - 1
    if p.eye == "squeeze":
        cv.stamp(["kk", ".k"], ex, ey, {"k": px.INK}, name="eye")
    elif p.eye == "dead":
        cv.stamp(["k.k", ".k.", "k.k"], ex - 1, ey - 1, {"k": px.INK}, name="eye")
    else:
        cv.stamp(["gi", "ik"], ex, ey, {"g": px.GLINT, "i": IRIS, "k": px.INK}, name="eye")
        if p.eye == "angry":
            cv.pixels([(ex - 1, ey - 1), (ex, ey - 1), (ex + 1, ey)], SKIN.deep, name="brow")
    if p.hit:
        fx = cv.layer(above=True, outline=False)
        tip = px.polar(D, ang, face + 1.5)
        px.impact(fx, tip[0] + 1, tip[1], size=3)
