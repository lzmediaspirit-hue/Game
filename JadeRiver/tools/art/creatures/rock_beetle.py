"""Rock beetle - squat beetle whose carapace is a set of rocky grey-brown plates (Earth).

View: side, facing right.  ~18 art px tall, ~30 long (horn included).
Two drawing modes share the palette:
  * standing: far legs, dark underbody, carapace dome cut flat underneath (pronotum
    plate + three rocky elytra plates with seams, cracks and pale pebble specks), small
    dark head with a curved ochre horn, amber eye, clubbed antenna, near legs;
  * ball: the whole beetle rolled up - a round stone ball with the dark tucked belly,
    folded legs and horn tip showing on one side; the belly patch, seams and specks turn
    with the roll angle so the rolling attack reads frame to frame.
FX: dust (curl, roll), speed lines, impact.
"""
import math

import pixel as px

SPEC = {
    "id": "rock_beetle",
    "cell": 128,
    "anchor": [64, 112],
    "flying": False,
    "hit_frame": 2,
}

# ---- palette: grey-brown stone plates, dark umber chitin, ochre horn --------------------
ROCK = px.material("beetle_rock", "#cbbf9f", "#998b70", "#6c604f", "#473f37", outline="#14110f",
                   thresholds=(0.84, 0.5, 0.2))
PRONOTUM = px.material("beetle_pronotum", "#b4a78b", "#857861", "#5e5446", "#3f3833", outline="#14110f",
                       thresholds=(0.84, 0.5, 0.2))
LICHEN = px.material("beetle_lichen", "#e2c27a", "#b8904e", "#8a6a3e", "#5e4a30", outline="#14110f")
CHITIN = px.material("beetle_chitin", "#7d675a", "#56463c", "#3b302b", "#271f1d", outline="#0e0a0a")
HORN = px.material("beetle_horn", "#ecd49a", "#c29b5b", "#8c6a41", "#5c452e", outline="#1a120b")
SPECK = px.rgb("#e6dcc0")
SEAM = ROCK.step(1)
CRACK = ROCK.step(2)
IRIS = px.rgb("#f0b23e")

# ---- poses --------------------------------------------------------------------------------
# bx, by   body offset          pitch  body tilt about the feet (deg, - = nose down)
# lift, slide  per-leg tip lift / x slide, legs: near F M H, far F M H
# tuck     0..1 legs + head pulled in    eye  open|angry|squeeze|dead    horn  head tilt (deg)
# ball     None | roll angle of the rolled-up ball (deg)   bsq  ball squash
# flip     on its back   curl  legs curl 0..1   rot  tumble angle   fade  opacity
# dust     dust life (None = off)   speed  speed lines   hit  impact fx
DEFAULTS = dict(bx=0, by=0, pitch=0, lift=(0,) * 6, slide=(0,) * 6, tuck=0.0, eye="open", horn=0, ant=0,
                ball=None, bsq=1.0, flip=False, curl=0.0, rot=0, fade=1.0, dust=None, speed=False, hit=False,
                breathe=0.0, round=0.0)

A = (1, 0, 1, 0, 1, 0)  # tripod: near F, near H, far M
B = (0, 1, 0, 1, 0, 1)


def _k(mask, k):
    return tuple(m * k for m in mask)


POSE = px.poses(DEFAULTS, {
    "idle": [
        dict(),
        dict(breathe=0.4, ant=1),
        dict(breathe=0.6, ant=2, horn=2),
        dict(breathe=0.3, ant=1, horn=1),
    ],
    "walk": [  # tripod gait: one tripod steps while the other pushes, body bobs
        dict(lift=_k(A, 2), slide=_k(A, 1), by=-1),
        dict(lift=_k(A, 1), slide=_k(A, 2), ant=1),
        dict(slide=_k(B, -1)),
        dict(lift=_k(B, 2), slide=_k(B, 1), by=-1),
        dict(lift=_k(B, 1), slide=_k(B, 2), ant=1),
        dict(slide=_k(A, -1)),
    ],
    "windup": [  # tucks the head, pulls the legs in and curls into a stone ball - held
        dict(pitch=-8, tuck=0.4, eye="angry", horn=-10, by=1, dust=None),
        dict(tuck=0.85, eye="angry", horn=-28, by=2, round=1.0, dust=0.1),
        dict(ball=-55, bx=-1, bsq=0.96, dust=0.35),
    ],
    "attack": [  # rolls forward as a boulder; smashes on frame 2, then starts to uncurl
        dict(ball=-145, bx=4, dust=0.15, speed=True),
        dict(ball=-235, bx=9, dust=0.45, speed=True),
        dict(ball=-325, bx=13, dust=0.75, hit=True, bsq=0.94),
        dict(pitch=-10, tuck=0.6, bx=9, eye="angry", horn=-12),
    ],
    "hurt": [
        dict(bx=-3, by=-1, pitch=10, eye="squeeze", horn=16, lift=(2, 2, 1, 1, 1, 0), slide=(-1,) * 6),
        dict(bx=-2, pitch=5, eye="squeeze", horn=8),
    ],
    "death": [  # knocked back, tips over, lands on its back, legs curl, fade
        dict(bx=-3, by=-1, pitch=12, eye="squeeze", horn=18, lift=(2, 2, 1, 1, 1, 0)),
        dict(bx=-3, rot=70, eye="dead", horn=10, lift=(3, 3, 3, 3, 3, 3)),
        dict(bx=-3, flip=True, eye="dead", curl=0.2),
        dict(bx=-3, flip=True, eye="dead", curl=0.65, fade=0.6),
        dict(bx=-3, flip=True, eye="dead", curl=1.0, fade=0.3),
    ],
})

# legs: (hip dx, knee dx, knee dy, foot dx) relative to C; near legs 0-2, far legs 3-5
NEAR = ((6.5, 9.0, 1.0, 10.5), (0.5, 1.8, 1.5, 2.2), (-5.5, -8.5, 1.0, -9.5))
FAR = tuple((h + 1.8, k + 1.8, dy - 0.5, f + 1.8) for h, k, dy, f in NEAR)
RX, RY = 11.0, 8.6


def _leg(cv, C, ground, i, p, far):
    hx, kx, kdy, fx = (FAR if far else NEAR)[i]
    j = i + (3 if far else 0)
    t = p.tuck
    hip = (C[0] + hx * 0.9, C[1] + 4.2)
    if p.flip:  # on its back (local frame is mirrored): feet point up, curling inward
        c = p.curl
        knee = (C[0] + kx * 1.1 - c * kx * 0.25, C[1] + 7.4 - c * 0.8 + (i == 1) * 0.8)
        foot = (C[0] + kx * 0.7 * (1 - c) + hx * c, C[1] + 10.8 - c * 3.4 + (i == 1) * 0.8)
    else:
        lift = p.lift[j]
        foot = (C[0] + fx + p.slide[j] - fx * 0.5 * t, ground - lift - 4.0 * t)
        knee = (C[0] + kx + p.slide[j] * 0.5 - kx * 0.3 * t, C[1] + 4.2 + kdy - lift * 0.5 - 1.5 * t)
    shade = "dark" if far else "soft"
    cv.limb([hip, knee], [1.3, 1.1], CHITIN, shade=shade, name="leg")
    cv.limb([knee, foot], [1.0, 0.55], CHITIN, shade=shade, name="leg")
    if not far and not p.flip and t < 0.5:  # a pale claw tip on the near feet
        cv.pixel(math.floor(foot[0] + (0.6 if fx > 0 else -1.4)), math.floor(foot[1]), HORN.shadow, name="claw")


def _carapace(cv, C, p):
    br = p.breathe
    cut = cv.mask_polygon([(C[0] - 20, C[1] + 3.6), (C[0] + 20, C[1] + 3.6), (C[0] + 20, C[1] + 20),
                           (C[0] - 20, C[1] + 20)])
    ry = RY + br
    dome = cv.geom_ellipse(C[0] - 2.0, C[1] - br * 0.5, RX, ry)
    knobs = []
    for dx, r in ((-7.0, 2.2), (-1.5, 2.4), (4.0, 2.0)):  # rocky knobs breaking the dome line
        top = C[1] - br * 0.5 - ry * math.sqrt(max(0.0, 1 - ((dx + 2.0) / RX) ** 2))
        knobs.append(cv.geom_ellipse(C[0] + dx, top + 1.3, r, r * 0.8))
    elytra = cv.union(dome, *knobs, weights=[1.0] + [0.5] * len(knobs))
    cv.draw_geom(elytra, ROCK, minus=cut, name="shell", sep="deep")
    for (lx, ly, lr) in ((-8.5, -1.5, 1.4), (2.5, -6.2, 1.1)):  # ochre lichen crusts
        cv.ellipse(C[0] + lx, C[1] + ly - br * 0.5, lr * 1.3, lr, LICHEN, shade="two", decal=True, clip="shell")
    # three rocky plates: curved seams across the dome, cracks, pebble specks
    for sx in (-5.5, 1.0):
        top = C[1] - RY * math.sqrt(max(0.0, 1 - ((sx + 2.0) / RX) ** 2)) - br * 0.5
        cv.limb([(C[0] + sx - 0.4, top + 0.2), (C[0] + sx + 0.6, C[1] - 2.0), (C[0] + sx - 0.2, C[1] + 3.6)],
                0.5, SEAM, decal=True, clip="shell")
    # the elytra rim: a darker lip along the bottom edge
    cv.limb([(C[0] - RX - 1, C[1] + 2.4), (C[0] + 6, C[1] + 2.6)], 0.9, SEAM, decal=True, clip="shell")
    for a, b in (((-9.0, -3.0), (-7.0, -1.0)), ((3.5, -5.5), (5.5, -3.0)), ((-2.5, 0.5), (-1.0, 2.0))):
        cv.line((math.floor(C[0] + a[0]), math.floor(C[1] + a[1])), (math.floor(C[0] + b[0]), math.floor(C[1] + b[1])),
                CRACK, decal=True, clip="shell")
    for (sx, sy) in ((-8.0, -5.5), (-3.5, -7.0), (3.0, -1.0), (-0.5, -4.0)):  # pale pebbles set in the stone
        x, y = math.floor(C[0] + sx), math.floor(C[1] + sy - br * 0.5)
        cv.pixels([(x, y), (x + 1, y)], SPECK, name="speck", clip="shell")
    # pronotum: the front shield plate, overlapping the elytra
    cv.ellipse(C[0] + 8.2, C[1] + 0.2, 4.6, 5.2, PRONOTUM, angle=-10, name="pronotum", sep="deep", minus=cut)
    cv.pixel(math.floor(C[0] + 7), math.floor(C[1] - 3), SPECK, name="speck", clip="pronotum")


def _head(cv, C, p):
    H = (C[0] + 12.2, C[1] + 2.2 + 1.5 * p.tuck)
    with cv.xform(px.rotate(p.horn, (H[0] - 2, H[1]))):
        # antenna: a short clubbed feeler
        a0 = (H[0] + 1.0, H[1] - 1.5)
        a1 = (H[0] + 3.5, H[1] - 4.0 - 0.5 * p.ant)
        cv.limb([a0, a1], [0.45, 0.45], CHITIN, shade="dark", name="antenna")
        cv.circle(a1[0] + 0.3, a1[1] - 0.2, 0.9, CHITIN, shade="two", name="antenna")
        cv.ellipse(H[0], H[1], 3.3, 2.9, CHITIN, name="head", sep="deep")
        # curved horn sweeping up and forward
        cv.limb([(H[0] + 1.5, H[1] - 0.8), (H[0] + 4.2, H[1] - 2.8), (H[0] + 5.0, H[1] - 6.2)], [1.3, 0.95, 0.5],
                HORN, shade="soft", name="horn", sep="deep")
        # mandible
        cv.limb([(H[0] + 2.2, H[1] + 1.8), (H[0] + 3.6, H[1] + 2.2)], 0.6, CHITIN, shade="two", name="mandible")
        ex, ey = math.floor(H[0] - 0.5), math.floor(H[1] - 1.5)
        if p.eye == "squeeze":
            cv.stamp(["kk", ".k"], ex, ey, {"k": px.INK}, name="eye")
        elif p.eye == "dead":
            cv.stamp(["k.k", ".k.", "k.k"], ex - 1, ey - 1, {"k": HORN.light}, name="eye")
        else:
            cv.stamp(["gi", "ik"], ex, ey, {"g": px.GLINT, "i": IRIS, "k": px.INK}, name="eye")
            if p.eye == "angry":
                cv.pixels([(ex - 1, ey - 1), (ex, ey - 1), (ex + 1, ey)], px.INK, name="brow")
        return cv.tp((H[0] + 5.0, H[1] - 5.0))


def _ball(cv, ground, p, cx):
    """Rolled-up beetle: stone ball, tucked belly patch + horn tip turning with the roll."""
    R = 9.3
    B = (cx, ground + 0.5 - R)
    roll = p.ball
    with cv.xform(px.scale(1.0 / p.bsq ** 0.5, p.bsq, (B[0], ground + 0.5))):
        cv.circle(B[0], B[1], R, ROCK, name="shell")
        # plate seams: two curved bands across the ball, turning with the roll
        for off in (-0.25, 0.3):
            pts = []
            for s in (-0.95, -0.4, 0.0, 0.4, 0.95):
                q = (off * R + 0.18 * R * (1 - s * s), s * R)
                pts.append(px.rot_pt((B[0] + q[0], B[1] + q[1]), roll, B))
            cv.limb(pts, 0.5, SEAM, decal=True, clip="shell")
        for (sx, sy) in ((-0.5, -0.45), (0.1, -0.7), (0.55, 0.1), (-0.6, 0.35), (0.15, 0.4)):
            q = px.rot_pt((B[0] + sx * R, B[1] + sy * R), roll, B)
            cv.pixel(math.floor(q[0]), math.floor(q[1]), SPECK, name="speck", clip="shell")
        # tucked belly: a dark cap of the ball in the direction ``roll`` (0 = right)
        u = px.polar((0, 0), roll, 1.0)
        cap = cv.mask_polygon([px.rot_pt((B[0] + 0.5 * R, B[1] + k * R * 1.2), roll, B) for k in (-1, 1)]
                              + [px.rot_pt((B[0] + 1.5 * R, B[1] + k * R * 1.2), roll, B) for k in (1, -1)])
        m = cv.mask_of("shell") & cap
        cv._commit(m, cv.band.copy(), CHITIN, name="belly")
        cv.limb([px.rot_pt((B[0] + 0.5 * R, B[1] - 0.75 * R), roll, B),
                 px.rot_pt((B[0] + 0.5 * R, B[1] + 0.75 * R), roll, B)], 0.5, ROCK.step(2), decal=True, clip="shell")
        # folded legs as short dark ribs on the belly
        for k in (-0.4, 0.05, 0.5):
            a = px.rot_pt((B[0] + 0.62 * R, B[1] + k * R), roll, B)
            b = px.rot_pt((B[0] + 0.82 * R, B[1] + (k + 0.15) * R), roll, B)
            cv.limb([a, b], 0.5, CHITIN.step(1), decal=True, clip="belly")
        # horn tip poking out of the curl
        h0 = px.rot_pt((B[0] + 0.8 * R, B[1] - 0.35 * R), roll, B)
        h1 = px.rot_pt((B[0] + 1.18 * R, B[1] - 0.2 * R), roll, B)
        cv.limb([h0, h1], [1.0, 0.5], HORN, shade="soft", name="horn")
        front = cv.tp((B[0] + R, B[1]))
    return B, R, front, u


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    ground = cv.ground
    cv.opacity = p.fade
    if p.ball is not None:
        cx = cv.gx - 1 + p.bx
        B, R, front, _ = _ball(cv, ground, p, cx)
        if p.dust is not None:
            fx = cv.layer(above=True, outline=True)
            px.dust(fx, B[0] - R + 1.0, cv.gy - 1, p.dust, size=0.8, direction=-1)
        if p.speed:
            back = cv.layer(above=False, outline=False)
            px.speed_lines(back, B[0] - R - 1, B[1] - 2, length=6, count=3, spacing=4, color=px.DUST.light)
        if p.hit:
            top = cv.layer(above=True, outline=False)
            px.impact(top, front[0] + 1.5, front[1] - 2, size=3)
        return
    C = (cv.gx - 3 + p.bx, ground - 9.0 + p.by)
    xf = []
    if p.pitch:  # tilt about the planted feet at the low end; snap keeps them on the ground
        xf = [px.rotate(p.pitch, (C[0] + (10 if p.pitch < 0 else -9), ground))]
        cv.snap_ground = True
    if p.round:  # half-curled: the body bunches up, shorter and taller
        xf.append(px.scale(1 - 0.16 * p.round, 1 + 0.12 * p.round, (C[0] + 2, ground)))
        cv.snap_ground = True
    if p.rot:
        xf = [px.rotate(p.rot, C)]
        cv.snap_ground = True
    if p.flip:
        xf = [px.flip_y(C[1])]
        cv.snap_ground = True
    with cv.xform(*xf):
        for i in (2, 1, 0):
            _leg(cv, C, ground, i, p, far=True)
        cv.ellipse(C[0] + 1.0, C[1] + 3.8, 10.5, 2.6, CHITIN, shade="nolight", name="under")
        if p.flip:  # legs point up out of the belly, drawn in front of it
            for i in (2, 1, 0):
                _leg(cv, C, ground, i, p, far=False)
        _carapace(cv, C, p)
        _head(cv, C, p)
        if not p.flip:
            for i in (2, 1, 0):
                _leg(cv, C, ground, i, p, far=False)
    if p.dust is not None:
        fx = cv.layer(above=True, outline=True)
        px.dust(fx, C[0] - 8, cv.gy - 1, p.dust, size=0.7, direction=-1)
