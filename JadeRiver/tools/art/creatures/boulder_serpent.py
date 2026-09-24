"""Boulder serpent - a heavy serpent armoured with rounded boulder plates (Earth).

View: side, facing right.  ~33 art px tall with the head raised, ~66 long (cell 192).
The body is one spline (tail tip -> head) drawn as a thick ochre tube with a sandstone belly
(scute lines), a row of grey boulder plates along the spine (each its own lump, separated
by dark seams, lichen on a few), and a heavy wedge head (rocky brow plate, hinged jaw,
amber slit eye, forked tongue).
Walk: slithering wave.  Windup: curls up into a boulder ball, one eye peeking (held).
Attack: the ball rolls forward and slams the target on frame 1, then unrolls.
Death: uncurls limp on the ground; cracks split the plates as it fades.
"""
import math

import pixel as px
import helpers_batch_b as hb

SPEC = {
    "id": "boulder_serpent",
    "cell": 192,
    "anchor": [96, 168],
    "flying": False,
    "hit_frame": 1,
}

# ---- palette: ochre hide, grey boulder plates, sandstone belly, lichen, amber eye ------------
HIDE = px.material("bs_hide", "#d2a064", "#9c6c3c", "#6b4a33", "#43302a", outline="#1b1210",
                   thresholds=(0.9, 0.52, 0.16))
ROCK = px.material("bs_rock", "#d0c6aa", "#9a8e76", "#686054", "#423d3e", outline="#141214",
                   thresholds=(0.88, 0.5, 0.14))
BELLY = px.material("bs_belly", "#f2dcaa", "#c9ab78", "#967c58", "#5e4e3c", outline="#1b1210")
LICHEN = px.material("bs_lichen", "#d8dc88", "#a8b25e", "#7a8646", "#4e5a34", outline="#141a0c")
IRIS = px.rgb("#ffb440")
TONGUE = px.rgb("#b8303c")
MOUTH = px.material("bs_mouth", "#d67a7a", "#a84a52", "#72303c", "#461c28", outline="#1b0c10")

# ---- poses --------------------------------------------------------------------------------
# neck   3 keypoints (dx, height) from the body to the head base       head  (dx, height)
# ang    head angle (deg)   jaw 0..1   tongue 0/1/2   wave (phase, amp) slither wave
# shift  whole body x offset   eye open|angry|squeeze|dead
# ball   None or (dx, spin deg, coil 0..1 [1 = closed ball], head_out 0..1)
# dust / hit / crack / limp / fade
NECK = ((15.0, 8.0), (18.0, 16.0), (20.0, 23.0))
DEFAULTS = dict(neck=NECK, head=(24.0, 26.0), ang=-4, jaw=0.0, tongue=0, wave=(0.0, 0.0), shift=0,
                eye="open", ball=None, dust=None, hit=False, crack=0, limp=False, fade=1.0)

POSE = px.poses(DEFAULTS, {
    "idle": [  # head raised, swaying, tongue tasting the air
        dict(),
        dict(neck=((15.0, 8.0), (18.3, 16.3), (20.5, 23.4)), head=(24.4, 26.4), tongue=1),
        dict(neck=((15.0, 8.0), (18.5, 16.5), (20.8, 23.6)), head=(24.8, 26.6), ang=-2, tongue=2),
        dict(neck=((15.0, 8.0), (18.3, 16.2), (20.4, 23.3)), head=(24.4, 26.3)),
    ],
    "walk": [  # slithering: a wave travels down the body, head held lower and forward
        dict(wave=(0.0, 1.8), neck=((16.0, 7.0), (20.0, 12.0), (23.0, 17.0)), head=(27.0, 19.0), ang=-8),
        dict(wave=(1.05, 1.8), neck=((16.0, 7.0), (20.3, 12.4), (23.4, 17.4)), head=(27.4, 19.4), ang=-8,
             shift=1),
        dict(wave=(2.1, 1.8), neck=((16.0, 7.0), (20.0, 12.0), (23.0, 17.0)), head=(27.0, 19.0), ang=-8,
             shift=1, tongue=1),
        dict(wave=(3.14, 1.8), neck=((16.0, 7.0), (20.3, 12.4), (23.4, 17.4)), head=(27.4, 19.4), ang=-8,
             shift=2),
        dict(wave=(4.19, 1.8), neck=((16.0, 7.0), (20.0, 12.0), (23.0, 17.0)), head=(27.0, 19.0), ang=-8,
             shift=1),
        dict(wave=(5.24, 1.8), neck=((16.0, 7.0), (20.3, 12.4), (23.4, 17.4)), head=(27.4, 19.4), ang=-8,
             shift=1, tongue=2),
    ],
    "windup": [  # curls up into a boulder ball, one eye glaring out - held
        dict(ball=(0.0, 0.0, 0.55, 1.0), eye="angry", jaw=0.3),
        dict(ball=(-1.0, -10.0, 0.9, 0.5), eye="angry"),
        dict(ball=(-2.0, -14.0, 1.0, 0.3), eye="angry"),
    ],
    "attack": [  # the ball rolls in and slams (hit on frame 1), bounces, unrolls
        dict(ball=(8.0, -110.0, 1.0, 0.0), dust=0.25),
        dict(ball=(17.0, -230.0, 1.0, 0.0), dust=0.55, hit=True),
        dict(ball=(14.0, -290.0, 0.7, 0.8), dust=0.85, eye="angry"),
        dict(shift=6, neck=((15.0, 7.0), (19.0, 13.0), (22.0, 19.0)), head=(26.0, 21.0), ang=-10, jaw=0.4,
             eye="angry"),
    ],
    "hurt": [
        dict(shift=-3, neck=((14.0, 8.0), (15.0, 16.0), (15.5, 24.0)), head=(17.0, 28.0), ang=30, jaw=0.6,
             eye="squeeze"),
        dict(shift=-2, neck=((14.5, 8.0), (16.5, 16.0), (18.0, 23.5)), head=(21.0, 27.0), ang=12, jaw=0.2,
             eye="squeeze"),
    ],
    "death": [  # rears in pain, crashes down, lies limp; cracks split the plates, fades
        dict(shift=-3, neck=((14.0, 8.0), (15.0, 16.0), (15.5, 24.0)), head=(17.0, 28.0), ang=34, jaw=0.8,
             eye="squeeze"),
        dict(shift=-2, neck=((16.0, 7.0), (21.0, 9.0), (25.0, 8.0)), head=(29.0, 6.0), ang=-26, jaw=0.5,
             eye="dead", crack=1),
        dict(limp=True, eye="dead", jaw=0.4, tongue=1, crack=2),
        dict(limp=True, eye="dead", jaw=0.4, tongue=1, crack=3, fade=0.6),
        dict(limp=True, eye="dead", jaw=0.4, tongue=1, crack=3, fade=0.3),
    ],
})


# ---- parts --------------------------------------------------------------------------------
def _radius(t):
    """Body radius along the spine (0 = tail tip, 1 = head base)."""
    if t < 0.55:
        return 0.8 + 4.9 * math.sin(t / 0.55 * math.pi / 2)
    return 5.7 - 1.5 * (t - 0.55) / 0.45


def _plates(cv, pts, radii, crack, name="plate", every=5, start=4, stop=3):
    """Row of boulder plates riding the dorsal side of the tube."""
    nrm = hb.belly_normals(pts, toward=(0.0, 1.0))
    k = 0
    for i in range(start, len(pts) - stop, every):
        r = radii[i]
        if r < 1.6:
            continue
        a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
        ang = math.degrees(math.atan2(-(b[1] - a[1]), b[0] - a[0]))
        c = (pts[i][0] - nrm[i][0] * r * 0.42, pts[i][1] - nrm[i][1] * r * 0.42)
        drop = (0.0, 0.0)
        if crack >= 3 and k % 3 == 1:  # plates knocked loose
            drop = (1.0, 1.5)
        rx, ry = r * 0.62 + 0.9, r * 0.62
        cv.ellipse(c[0] + drop[0], c[1] + drop[1], rx, ry, ROCK, angle=ang, name=name, sep="deep")
        if k % 3 == 0:  # lichen on the sunny top of some plates
            cv.ellipse(c[0] - 0.6, c[1] - ry * 0.45, rx * 0.45, ry * 0.3, LICHEN, angle=ang, shade="two",
                       decal=True, clip=name, name=name)
        if crack >= 1 and k % 2 == crack % 2 or crack >= 2:  # cracks spreading through the plates
            q0 = (c[0] - rx * 0.4, c[1] - ry * 0.6)
            q1 = (c[0] + 0.3, c[1])
            q2 = (c[0] - 0.4, c[1] + ry * 0.7)
            for u, v in ((q0, q1), (q1, q2)):
                cv.line((math.floor(u[0]), math.floor(u[1])), (math.floor(v[0]), math.floor(v[1])), ROCK.deep,
                        band=None, decal=True, clip=name, name=name)
        k += 1


def _tube(cv, pts, crack, name="body"):
    n = len(pts)
    radii = [_radius(i / (n - 1)) for i in range(n)]
    cv.limb(pts, radii, HIDE, name=name)
    nrm = hb.belly_normals(pts, toward=(0.0, 1.0))
    belly = hb.offset(pts, nrm, radii, 0.7)
    cv.limb(belly, [r * 0.5 for r in radii], BELLY, shade="two", decal=True, clip=name, name=name)
    for i in range(3, n - 2, 3):  # ventral scute lines
        a = hb.offset([pts[i]], [nrm[i]], [radii[i]], 0.35)[0]
        b = hb.offset([pts[i]], [nrm[i]], [radii[i]], 1.0)[0]
        cv.line((math.floor(a[0]), math.floor(a[1])), (math.floor(b[0]), math.floor(b[1])), BELLY.step(1), band=None,
                decal=True, clip=name, name=name)
    _plates(cv, pts, radii, crack)
    return radii


def _head(cv, Hb, ang, p):
    """Heavy wedge head in a local frame (x forward), Hb = back of the skull."""
    with cv.xform(px.translate(Hb[0], Hb[1]), px.rotate(ang), px.scale(1.2, 1.2)):
        jr = -30 * p.jaw
        if p.jaw > 0.05:
            with cv.xform(px.rotate(jr * 0.5, (0.0, 1.5))):
                cv.polygon([(0.0, 0.5), (9.0, 0.8), (8.0, 2.4), (0.5, 2.8)], MOUTH, shade="two", name="mouth")
        with cv.xform(px.rotate(jr, (0.0, 1.5))):
            cv.polygon([(-1.0, 1.0), (9.0, 1.2), (9.4, 2.4), (5.0, 4.0), (-0.5, 4.4), (-2.0, 3.0)], HIDE,
                       shade="two", name="jaw", sep="deep")
            cv.polygon([(0.0, 3.2), (8.5, 2.0), (5.0, 4.2), (0.0, 4.6)], BELLY, shade="two", decal=True, clip="jaw",
                       name="jaw")
            if p.jaw > 0.3:
                cv.pixels([(6, 0), (3, 0)], px.PAPER, name="fang")
        skull = [(-2.2, -3.4), (2.5, -4.6), (7.5, -3.6), (10.6, -1.2), (11.0, 0.8), (9.0, 1.6), (0.0, 1.8),
                 (-2.6, 1.0)]
        cv.polygon(skull, HIDE, name="head", sep="deep")
        cv.line((0, 1), (9, 1), BELLY.shadow, band=None, decal=True, clip="head", name="head")
        cv.pixel(9, -1, HIDE.deep, name="nostril")
        if p.jaw > 0.3:
            cv.pixels([(7, 2), (7, 3), (3, 2)], px.PAPER, name="fang")
        # rocky brow plate over the eye + a plate on the crown
        cv.ellipse(0.5, -3.6, 3.4, 1.9, ROCK, angle=-8, name="plate", sep="deep")
        brow = [(3.0, -4.2), (6.8, -3.4), (8.0, -2.0)] if p.eye != "angry" else [(3.0, -4.6), (6.8, -3.0), (8.0, -1.2)]
        cv.limb(brow, [1.3, 1.1, 0.7], ROCK, shade="two", name="plate", sep="deep")
        ex, ey = 4, -2
        if p.eye in ("open", "angry"):
            cv.stamp(["gki", "iki"], ex, ey, {"k": px.INK, "g": px.GLINT, "i": IRIS}, name="eye")
        else:
            hb.eye(cv, ex, ey, p.eye)
        if p.tongue:
            L = 2 + p.tongue
            cv.pixels([(11 + k, 1) for k in range(L)] + [(11 + L, 0), (11 + L, 2)], TONGUE, name="tongue")
        tip = cv.tp((11.0, 1.0))
    return tip


def _ball(cv, B, spin, coil, head_out, p, R=12.5):
    """Coiled into a boulder: a round mass of coils ringed with plates.  ``coil`` < 1 leaves
    the tail loop open; ``head_out`` pokes the head out of the front."""
    with cv.xform(px.rotate(spin, B)):
        cv.circle(B[0], B[1], R - 1.0, HIDE, name="body", sep="deep")
        # inner coil seam + belly glimpses between the coils
        cv.limb([px.polar(B, a, R * 0.45) for a in range(40, 400, 30)], 0.6, HIDE.step(1), decal=True, clip="body",
                name="body")
        n_pl = 11
        for k in range(n_pl):  # ring of boulder plates around the outside
            a = k * 360.0 / n_pl + 8
            if coil < 1.0 and (a % 360) > 360 * coil + 30:
                continue
            c = px.polar(B, a, R - 3.2)
            cv.ellipse(c[0], c[1], 4.4, 3.4, ROCK, angle=a + 90, name="plate", sep="deep")
            if k % 3 == 0:
                cv.ellipse(c[0] - 0.5, c[1] - 1.2, 1.8, 0.9, LICHEN, angle=a + 90, shade="two", decal=True,
                           clip="plate", name="plate")
        cv.ellipse(B[0] - 1.0, B[1] - 1.0, 4.2, 3.6, ROCK, name="plate", sep="deep")  # the central boss
        if coil < 1.0:  # tail still unwinding from the ball
            t0 = px.polar(B, 360 * coil + 40, R - 2.0)
            cv.limb([t0, px.polar(t0, 360 * coil + 150, 5.0), px.polar(t0, 360 * coil + 170, 9.0)], [3.0, 2.0, 0.8],
                    HIDE, name="tail", sep="deep")
    if head_out > 0:  # head pushed out of the front of the ball
        Hb = (B[0] + R - 5.0 + 3.0 * head_out, B[1] + 2.0 - 3.0 * head_out)
        _head(cv, Hb, -6 + 10 * head_out, p)
    else:  # one glaring eye in the gap between the front plates
        ex, ey = math.floor(B[0] + R * 0.45), math.floor(B[1] + 1)
        cv.stamp(["kkkk", "kgik", "kiik", "kkkk"], ex, ey, {"k": HIDE.deep, "g": px.GLINT, "i": IRIS}, name="eye")


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    g = cv.ground
    cv.opacity = p.fade
    X = cv.gx - 4 + p.shift
    if p.ball is not None:
        dx, spin, coil, head_out = p.ball
        R = 12.5
        B = (X + 4 + dx, g + 0.5 - R)
        cv.snap_ground = True  # the lowest plate rests on the ground whatever the spin
        _ball(cv, B, spin, coil, head_out, p, R)
        if p.dust is not None:
            fx = cv.layer(above=True, outline=True)
            px.dust(fx, B[0] - R + 2, cv.gy - 1, p.dust, size=1.2, direction=-1)
        if p.hit:
            top = cv.layer(above=True, outline=False)
            px.impact(top, B[0] + R + 1, B[1], size=4)
        return
    if p.limp:
        kp = [(X - 36, g - 1.0), (X - 27, g - 2.2), (X - 17, g - 3.6), (X - 6, g - 4.8), (X + 5, g - 5.0),
              (X + 15, g - 4.6), (X + 22, g - 4.0)]
        pts = hb.resample(hb.catmull(kp, 8), 1.2)
        cv.snap_ground = True
        _tube(cv, pts, p.crack)
        _head(cv, (X + 23.5, g - 3.8), -3, p)
        return
    cv.snap_ground = action == "death"
    ph, amp = p.wave
    ground_kp = [(-34, 1.0), (-26, 2.5), (-17, 3.8), (-8, 4.9), (1, 5.2), (9, 5.4)]
    kp = []
    for dx, h in ground_kp:
        lift = amp * max(0.0, math.sin(ph + dx * 0.22)) if amp else 0.0
        kp.append((X + dx, g - h - lift))
    kp += [(X + dx, g - h) for dx, h in p.neck]
    Hb = (X + p.head[0], g - p.head[1])
    kp.append(Hb)
    pts = hb.resample(hb.catmull(kp, 8), 1.2)
    _tube(cv, pts, p.crack)
    tip = _head(cv, Hb, p.ang, p)
