"""Green viper - slender bamboo pit viper, coiled with its neck raised in an S (Wood).

View: side, facing right.  ~16 art px tall, ~44 px of body (cell 128).
The body is one spline (tail tip -> head) drawn as a tapered tube in two pieces so the
upper coil overlaps the lower one (separation line).  Decals: pale yellow belly strip and
a pale lateral stripe that follow the tube's belly side, faint crossbands on the back,
an orange tail tip.  Head: triangular viper wedge (skull + hinged lower jaw), gold eye
with a slit pupil, heavy brow scale, forked tongue.
Walk: side-winding (sections of the body lift and travel).  Windup: coils back into a
tight S, jaws parting.  Attack: fast strike lunge (hit on frame 1).  Death: goes limp.
"""
import math

import pixel as px
import helpers_batch_b as hb

SPEC = {
    "id": "green_viper",
    "cell": 128,
    "anchor": [64, 112],
    "flying": False,
    "hit_frame": 1,
}

# ---- palette ------------------------------------------------------------------------------
SCALE = px.material("viper_scale", "#c9f27e", "#6ec24a", "#358c45", "#1e5a3e", outline="#07170e",
                    thresholds=(0.9, 0.5, 0.12))
BELLY = px.material("viper_belly", "#fff6b8", "#eadc80", "#bba955", "#7e713c", outline="#07170e")
STRIPE = px.flat("#f4f2c4", outline="#07170e")
TAILTIP = px.material("viper_tail", "#ffb070", "#e3703f", "#a8442f", "#6a2a26", outline="#1a0908")
MOUTH = px.material("viper_mouth", "#f59aa4", "#d9667a", "#9c3a50", "#5e1e32", outline="#1a0810")
IRIS = px.rgb("#f6c945")
TONGUE = px.rgb("#e0303c")
FANG = px.rgb("#fbf6e6")

# ---- poses --------------------------------------------------------------------------------
# neck   4 keypoints (dx, dy from the anchor, y up = negative) from the coil top to the head
# ang    head angle (deg, + = nose up)       jaw  0..1 gape       tongue  0 = in, 1..2 = out
# wave   side-winding phase / None           lift  side-wind lift amplitude (px)
# shift  whole-snake x offset               eye  open|angry|squeeze|dead
# limp   lying flat (death)   fade  opacity   hit  impact   streak  strike speed lines
N_IDLE = ((-1.0, 7.6), (-5.0, 9.2), (-5.2, 12.2), (-1.5, 14.3))
DEFAULTS = dict(neck=N_IDLE, head=(2.5, 14.3), ang=4, jaw=0.0, tongue=0, wave=None, lift=0.0,
                shift=0, eye="open", limp=False, fade=1.0, hit=False, streak=False, coil=0.0)

POSE = px.poses(DEFAULTS, {
    "idle": [  # poised, neck swaying, tongue flicking
        dict(),
        dict(neck=((-1.0, 7.6), (-5.2, 9.3), (-5.4, 12.4), (-1.6, 14.6)), head=(2.4, 14.6), ang=6, tongue=1),
        dict(neck=((-1.0, 7.6), (-5.3, 9.4), (-5.6, 12.6), (-1.8, 14.8)), head=(2.2, 14.8), ang=6, tongue=2),
        dict(neck=((-1.0, 7.6), (-5.1, 9.3), (-5.3, 12.4), (-1.6, 14.5)), head=(2.4, 14.5), ang=5),
    ],
    "walk": [  # side-winding: lifted sections travel down the body, head held low and level
        dict(wave=0.0, lift=1.2, shift=0, neck=((-1, 7.4), (-4.5, 8.8), (-4.0, 11.4), (0.0, 12.6)),
             head=(3.8, 12.6), ang=0),
        dict(wave=1.05, lift=1.2, shift=1, neck=((-1, 7.4), (-4.3, 8.8), (-3.7, 11.2), (0.3, 12.3)),
             head=(4.1, 12.3), ang=-2, tongue=1),
        dict(wave=2.1, lift=1.2, shift=1, neck=((-1, 7.4), (-4.1, 8.7), (-3.5, 11.0), (0.5, 12.0)),
             head=(4.3, 12.0), ang=-2),
        dict(wave=3.14, lift=1.2, shift=2, neck=((-1, 7.4), (-4.5, 8.8), (-4.0, 11.4), (0.0, 12.6)),
             head=(3.8, 12.6), ang=0),
        dict(wave=4.19, lift=1.2, shift=1, neck=((-1, 7.4), (-4.3, 8.8), (-3.7, 11.2), (0.3, 12.3)),
             head=(4.1, 12.3), ang=-2, tongue=2),
        dict(wave=5.24, lift=1.2, shift=1, neck=((-1, 7.4), (-4.1, 8.7), (-3.5, 11.0), (0.5, 12.0)),
             head=(4.3, 12.0), ang=-2),
    ],
    "windup": [  # draws back into a tight S, head high, jaws parting - held
        dict(neck=((-1.5, 7.8), (-6.0, 9.6), (-7.0, 12.8), (-4.0, 15.2)), head=(0.0, 15.6), ang=10,
             jaw=0.25, tongue=1, eye="angry", coil=0.5),
        dict(neck=((-2.0, 8.0), (-7.5, 9.8), (-8.8, 13.2), (-6.0, 16.2)), head=(-2.2, 16.8), ang=14,
             jaw=0.55, tongue=0, eye="angry", coil=1.0),
        dict(neck=((-2.0, 8.0), (-7.8, 9.9), (-9.2, 13.4), (-6.4, 16.4)), head=(-2.6, 17.0), ang=16,
             jaw=0.7, tongue=0, eye="angry", coil=1.0),
    ],
    "attack": [  # strike: neck whips straight out, bite lands on frame 1, snap back
        dict(neck=((0.0, 8.0), (3.0, 10.0), (7.5, 10.6), (11.0, 10.4)), head=(14.2, 10.0), ang=-6, jaw=1.0,
             eye="angry", streak=True),
        dict(neck=((1.0, 7.8), (5.0, 8.6), (9.5, 8.2), (13.5, 7.2)), head=(16.8, 6.6), ang=-14, jaw=0.35,
             eye="angry", hit=True, streak=True),
        dict(neck=((0.0, 7.8), (-2.5, 9.6), (1.0, 11.6), (5.0, 12.2)), head=(8.5, 12.0), ang=-4, jaw=0.2,
             eye="angry"),
        dict(neck=((-1.0, 7.6), (-4.8, 9.2), (-4.8, 12.0), (-1.0, 14.0)), head=(3.0, 14.0), ang=2, jaw=0.0),
    ],
    "hurt": [
        dict(neck=((-1.5, 7.8), (-6.5, 9.5), (-8.0, 12.6), (-6.5, 15.5)), head=(-3.6, 16.6), ang=34,
             jaw=0.6, eye="squeeze", shift=-2),
        dict(neck=((-1.2, 7.7), (-5.8, 9.4), (-6.5, 12.6), (-3.5, 15.0)), head=(0.2, 15.4), ang=18,
             jaw=0.2, eye="squeeze", shift=-1),
    ],
    "death": [  # recoil, the neck topples forward, lies limp, fades
        dict(neck=((-1.5, 7.8), (-6.5, 9.5), (-8.0, 12.6), (-6.5, 15.5)), head=(-3.6, 16.6), ang=34,
             jaw=0.6, eye="squeeze", shift=-2),
        dict(neck=((0.0, 7.0), (3.0, 7.6), (6.5, 7.0), (9.0, 5.6)), head=(12.0, 4.4), ang=-24, jaw=0.4,
             eye="dead", coil=-0.5),
        dict(limp=True, eye="dead", jaw=0.3, tongue=1),
        dict(limp=True, eye="dead", jaw=0.3, tongue=1, fade=0.6),
        dict(limp=True, eye="dead", jaw=0.3, tongue=1, fade=0.3),
    ],
})


# ---- parts --------------------------------------------------------------------------------
def _tube(cv, pts, radii, name, sep=False):
    """Scaled tube + belly strip + lateral stripe + back crossbands (decals)."""
    cv.limb(pts, radii, SCALE, name=name, sep=sep)
    nrm = hb.belly_normals(pts)
    belly = hb.offset(pts, nrm, radii, 0.85)
    cv.limb(belly, [r * 0.55 for r in radii], BELLY, shade="two", decal=True, clip=name)
    stripe = hb.offset(pts, nrm, radii, 0.3)
    for a, b in zip(stripe[::1], stripe[1:]):
        cv.line((math.floor(a[0]), math.floor(a[1])), (math.floor(b[0]), math.floor(b[1])), STRIPE, band=None,
                decal=True, clip=name)
    for i in range(3, len(pts) - 2, 5):  # faint crossbands over the back
        if radii[i] < 1.4:
            continue
        a = hb.offset([pts[i]], [nrm[i]], [radii[i]], -1.0)[0]
        b = hb.offset([pts[i]], [nrm[i]], [radii[i]], -0.2)[0]
        cv.line((math.floor(a[0]), math.floor(a[1])), (math.floor(b[0]), math.floor(b[1])), SCALE.step(1),
                band=None, decal=True, clip=name)


def _head(cv, Hb, ang, p):
    """Viper wedge in a local frame: x forward, y down.  Hb = back of the skull."""
    with cv.xform(px.translate(Hb[0], Hb[1]), px.rotate(ang)):
        jaw_rot = -38 * p.jaw
        if p.jaw > 0.05:  # pink mouth lining between the jaws
            with cv.xform(px.rotate(jaw_rot * 0.5, (0.0, 0.8))):
                cv.polygon([(-0.5, 0.2), (6.6, 0.4), (6.0, 1.6), (0.0, 1.8)], MOUTH, shade="two", name="mouth")
        with cv.xform(px.rotate(jaw_rot, (0.0, 0.8))):
            cv.polygon([(-0.8, 0.6), (6.4, 0.6), (6.8, 1.3), (4.2, 2.4), (0.2, 2.8), (-1.4, 1.9)], SCALE,
                       shade="two", name="jaw", sep="deep")
            cv.polygon([(0.5, 2.2), (6.0, 1.2), (4.2, 2.6), (0.2, 3.0)], BELLY, shade="two", decal=True,
                       clip="jaw")
            if p.jaw > 0.3:  # lower teeth line
                cv.pixel(5, 0, FANG, name="fang")
        skull = [(-1.6, -2.3), (1.5, -3.5), (5.0, -3.1), (7.4, -1.4), (8.0, 0.2), (6.6, 0.9), (0.6, 1.1),
                 (-1.8, 0.8)]
        cv.polygon(skull, SCALE, name="head", sep="deep")
        # pale lip scales along the upper jaw
        cv.line((0, 0), (6, 0), BELLY.base, band=None, decal=True, clip="head")
        if p.jaw > 0.3:  # long hinged fangs folded down
            cv.pixels([(5, 1), (5, 2)], FANG, name="fang")
        # nostril / heat pit
        cv.pixel(6, -1, SCALE.deep, name="pit")
        # eye: gold iris with a vertical slit, heavy brow scale
        ex, ey = 3, -2
        if p.eye in ("open", "angry"):
            cv.stamp(["gki", "iki"], ex, ey, {"k": px.INK, "g": px.GLINT, "i": IRIS}, name="eye")
            if p.eye == "angry":
                cv.pixel(5, -2, SCALE.deep, name="brow")
            brow = [(2, -3), (3, -3), (4, -3), (5, -3)] if p.eye == "open" else [(2, -3), (3, -3), (4, -2), (5, -2)]
            cv.pixels(brow, SCALE.deep, name="brow")
        else:
            hb.eye(cv, ex, ey, p.eye)
        if p.tongue:  # forked tongue flicking out of the snout
            L = 2 + p.tongue
            pts = [(8 + k, 0) for k in range(L)] + [(8 + L, -1), (8 + L, 1)]
            cv.pixels(pts, TONGUE, name="tongue")
        tip = cv.tp((8.0, 0.5))
    return tip


def _limp_path(X, g):
    return [(X - 25, g - 1.2), (X - 19, g - 2.0), (X - 13, g - 1.6), (X - 6, g - 2.2), (X + 1, g - 1.8),
            (X + 7, g - 2.2), (X + 11, g - 2.0)]


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    g = cv.ground
    cv.opacity = p.fade
    X = cv.gx + p.shift
    if p.limp:
        pts = hb.resample(hb.catmull(_limp_path(X, g), 8), 1.0)
        radii = hb.taper(len(pts), 0.5, 2.5, 1.9, mid_at=0.55)
        _tube(cv, pts, radii, "body")
        cv.limb(pts[:6], radii[:6], TAILTIP, shade="soft", decal=True, clip="body")
        _head(cv, (X + 11.5, g - 2.4), -4, p)
        return
    # ground coil (tail -> front of the lower loop); side-winding lifts travelling sections
    ground_kp = [(-24, 1.0), (-19, 2.2), (-13, 1.8), (-6, 2.2), (1, 2.4), (6, 3.0)]
    kp = []
    for dx, h in ground_kp:
        lift = 0.0
        if p.wave is not None:
            lift = p.lift * max(0.0, math.sin(p.wave + dx * 0.32))
        kp.append((X + dx, g - h - lift))
    c = p.coil  # coiling tighter pulls the loop back a little
    loop_kp = [(X + 8 - c, g - 5.5), (X + 5 - c, g - 7.8)]
    neck_kp = [(X + dx, g - dy) for dx, dy in p.neck]
    Hb = (X + p.head[0], g - p.head[1])
    all_kp = kp + loop_kp + neck_kp + [Hb]
    pts = hb.resample(hb.catmull(all_kp, 8), 1.0)
    radii = hb.taper(len(pts), 0.5, 2.6, 1.9, mid_at=0.5)
    # split where the path starts climbing the loop: lower coil first, upper coil over it
    split = next(i for i, q in enumerate(pts) if q[0] >= X + 6.5 - c)
    _tube(cv, pts[:split + 1], radii[:split + 1], "lower")
    _tube(cv, pts[split:], radii[split:], "upper", sep="deep")
    # orange tail tip
    cv.limb(pts[:6], radii[:6], TAILTIP, shade="soft", decal=True, clip="lower")
    tip = _head(cv, Hb, p.ang, p)
    if p.streak:
        back = cv.layer(above=False, outline=False)
        px.speed_lines(back, Hb[0] - 3, Hb[1] - 1, length=6, count=2, spacing=4, color=px.MIST_BLUE)
    if p.hit:
        top = cv.layer(above=True, outline=False)
        px.impact(top, tip[0] + 1, tip[1], size=3)
