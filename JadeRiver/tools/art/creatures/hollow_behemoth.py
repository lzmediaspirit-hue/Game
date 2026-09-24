"""Hollow behemoth - story boss: a giant boar assembled from grey-white Hollow drones and
armour plates, with glowing white weak-point cracks and mist pouring off it.

View: side, facing right.  ~98 art px tall to the tip of the back ridge, ~112 long, on a
128 px art canvas (cell 256).
Parts, back to front: far legs, dark void body (the gaps between the plates), rows of
overlapping armour plates (back, hump, flank, hip, chest), the drone swarm that fills the
belly, joints and the spiked back ridge (each drone a small shell with one empty white
eye), head (skull plate, snout disc, curved tusks, empty white eye), near legs.  The
weak points are jagged white cracks on the flank plate and the skull.  FX: mist pouring
off the back and belly, dust, speed lines, drifting drones.
Windup: rears up on the hind legs, weak points flaring (held); attack: stampede charge
(hit on frame 2); hurt: the weak points flicker; death: it breaks apart into drones.
"""
import math

import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "hollow_behemoth",
    "cell": 256,
    "anchor": [128, 224],
    "flying": False,
    "hit_frame": 2,
    "airborne": [["death", 2], ["death", 3], ["death", 4]],
}

# ---- palette: Hollow grey-white plates over a dark void, white weak-point glow ----------------
PLATE = px.material("hb_plate", "#f1f4f1", "#bcc5c7", "#8b979d", "#5f6a72", outline="#151b20",
                    thresholds=(0.88, 0.52, 0.18))
PLATE_D = px.material("hb_plate_far", "#a3adb1", "#838f95", "#667178", "#4b555c", outline="#151b20")
VOID = px.material("hb_void", "#6a757c", "#4c565d", "#394249", "#283036", outline="#10151a")
DRONE = px.material("hb_drone", "#d9dfdf", "#9ba6aa", "#707c83", "#4d575e", outline="#12181c")
TUSK = px.material("hb_tusk", "#ffffff", "#e6ebe8", "#b8c1c0", "#848f92", outline="#161c21")
GLOW = px.rgb("#ffffff")
GLOW_EDGE = px.rgb("#bfeaf5")
GLOW_DIM = px.rgb("#8fa3ab")
EYE_W = px.EYE_WHITE

# ---- poses ------------------------------------------------------------------------------------
# bx, by  body offset     rear  rear up about the hind feet (deg)    head  head tilt (deg)
# feet    (dx, lift): near-front, far-front, near-hind, far-hind     glow  weak points 0 dim .. 2 flare
# jaw     tusk-jaw open   dust  dust life    speed  charge streaks   mist  mist phase
# burst   0..1 break apart into drones (death)                       fade  opacity
DEFAULTS = dict(bx=0, by=0, rear=0, head=0, feet=((0, 0), (0, 0), (0, 0), (0, 0)), glow=1, jaw=0.0, dust=None,
                speed=False, mist=0.0, burst=0.0, hit=False, fade=1.0, breathe=0.0)

POSE = px.poses(DEFAULTS, {
    "idle": [
        dict(mist=0.0),
        dict(mist=1.0, breathe=0.6, head=1),
        dict(mist=2.0, breathe=1.0, head=2, glow=2),
        dict(mist=3.0, breathe=0.4, head=1),
    ],
    "walk": [  # ponderous trot
        dict(feet=((4, 0), (-3, 3), (-4, 3), (3, 0)), mist=0.0),
        dict(feet=((2, 0), (0, 4), (-1, 2), (1, 0)), mist=0.8, by=-1, head=1),
        dict(feet=((-1, 2), (3, 0), (2, 0), (-1, 2)), mist=1.6),
        dict(feet=((-3, 3), (4, 0), (3, 0), (-4, 3)), mist=2.4),
        dict(feet=((0, 4), (2, 0), (1, 0), (-1, 2)), mist=3.2, by=-1, head=1),
        dict(feet=((3, 0), (-1, 2), (-1, 2), (2, 0)), mist=4.0),
    ],
    "windup": [  # rears up, weak points blazing - held
        dict(rear=6, head=6, glow=2, mist=0.5, feet=((2, 4), (1, 3), (0, 0), (0, 0)), jaw=0.3, bx=3),
        dict(rear=12, head=12, glow=2, mist=1.0, feet=((4, 8), (3, 7), (0, 0), (0, 0)), jaw=0.6, bx=5),
        dict(rear=14, head=14, glow=2, mist=1.5, feet=((5, 9), (4, 8), (0, 0), (0, 0)), jaw=0.7, bx=5),
    ],
    "attack": [  # slams down and stampedes forward; the tusks hit on frame 2
        dict(rear=-3, head=-8, glow=2, bx=0, feet=((2, 0), (1, 0), (-2, 0), (-2, 0)), dust=0.1, jaw=0.5,
             mist=2.0),
        dict(rear=-4, head=-12, glow=2, bx=2, feet=((4, 2), (2, 0), (-4, 0), (-3, 2)), dust=0.4, speed=True,
             jaw=0.6, mist=2.5),
        dict(rear=-2, head=-4, glow=2, bx=3, feet=((3, 0), (4, 0), (-3, 2), (-4, 0)), dust=0.7, speed=True,
             hit=True, jaw=0.9, mist=3.0),
        dict(rear=0, head=0, glow=1, bx=2, feet=((1, 0), (1, 0), (-1, 0), (-1, 0)), dust=0.95, mist=3.5),
    ],
    "hurt": [  # the weak points flicker
        dict(bx=1, rear=4, head=10, glow=0, mist=1.0, feet=((1, 2), (0, 1), (0, 0), (0, 0))),
        dict(bx=1, rear=2, head=5, glow=2, mist=2.0),
    ],
    "death": [  # the weak points burst and the swarm comes apart into drifting drones
        dict(bx=1, rear=5, head=12, glow=2, mist=1.0, feet=((1, 2), (0, 1), (0, 0), (0, 0))),
        dict(bx=2, rear=2, head=-6, glow=0, mist=2.0, burst=0.2),
        dict(bx=3, head=-10, glow=0, mist=3.0, burst=0.5),
        dict(bx=3, head=-10, glow=0, mist=4.0, burst=0.8, fade=0.6),
        dict(bx=3, head=-10, glow=0, mist=5.0, burst=0.92, fade=0.3),
    ],
})

# the back's top line in body-local coords (x right, y down; origin = body centre)
TOPLINE = ((-46, -20), (-38, -32), (-26, -42), (-12, -49), (2, -52), (14, -50), (24, -42))
FLANK = 1  # index into LOWER of the plate that carries the weak-point crack
# lower row of big plates: hip, flank, shoulder, chest
LOWER = (
    ((-50, -8), (-42, -22), (-26, -22), (-24, 4), (-42, 10)),
    ((-30, -26), (-6, -32), (6, -18), (2, 8), (-22, 10), (-28, -6)),
    ((0, -36), (20, -38), (30, -24), (28, 0), (10, 0), (4, -16)),
    ((24, -8), (34, -12), (36, 8), (26, 16), (16, 10)),
)
# drones in body-local coords (x, y, r): belly swarm and joints
DRONES = ((-38, 12, 3.6), (-28, 14, 4.2), (-17, 15, 4.0), (-6, 13, 4.2), (6, 13, 3.8), (17, 15, 3.6),
          (-46, 4, 3.2), (-12, 6, 3.0))
# the bristle ridge: drones with spikes along the top line
RIDGE = ((-34, -36, 3.0), (-22, -45, 3.4), (-8, -52, 3.8), (6, -55, 4.0), (18, -51, 3.4))


def _topline_plates(T):
    """Lamellar back plates hanging from the top line, each overlapping the one behind."""
    out = []
    for a, b in zip(TOPLINE, TOPLINE[1:]):
        drop = 16.0 + 0.1 * (b[0] + 40)
        out.append([T((a[0] - 2, a[1] + 1)), T((b[0] + 1, b[1] - 1)), T((b[0] - 1, b[1] + drop)),
                    T((a[0] - 5, a[1] + drop - 3))])
    return out


def _drone(cv, x, y, r, far=False, name="drone", eye=True):
    """One Hollow drone: a small domed shell with a single empty white eye."""
    cv.ellipse(x, y, r, r * 0.85, DRONE if not far else PLATE_D, shade="dark" if far else "full", name=name,
               sep="deep")
    if eye and r >= 3.0:
        cv.pixels([(math.floor(x + r * 0.35), math.floor(y - r * 0.1)), (math.floor(x + r * 0.35) + 1,
                                                                        math.floor(y - r * 0.1))], EYE_W, name=name)


def _crack(cv, pts, glow, name="crack"):
    """A glowing weak-point fissure: a 2 px white core inside a pale-blue rim."""
    core = GLOW if glow else GLOW_DIM
    rim = GLOW_EDGE if glow else VOID.shadow
    for a, b in zip(pts, pts[1:]):
        for dx, dy in ((0, -1), (0, 2), (-1, 0), (2, 0)):
            cv.line((round(a[0]) + dx, round(a[1]) + dy), (round(b[0]) + dx, round(b[1]) + dy), rim, decal=True,
                    name=name)
    for a, b in zip(pts, pts[1:]):
        for dx, dy in ((0, 0), (1, 0), (0, 1)):
            cv.line((round(a[0]) + dx, round(a[1]) + dy), (round(b[0]) + dx, round(b[1]) + dy), core, decal=True,
                    name=name)


def _leg(cv, hip, foot, far, burst=0.0):
    mat = PLATE_D if far else PLATE
    shade = "dark" if far else "two"
    fx, fy = foot
    knee = (hip[0] + (fx - hip[0]) * 0.5 + 2.0, hip[1] + (fy - hip[1]) * 0.5)
    cv.limb([hip, knee, (fx, fy - 6.0)], [8.0, 6.4, 5.6], VOID, shade="dark" if far else "nolight", name="leg")
    # greave plate + hoof
    cv.polygon([(knee[0] - 6.0, knee[1] - 2.0), (knee[0] + 5.0, knee[1] - 3.0), (fx + 5.0, fy - 5.0),
                (fx - 5.5, fy - 5.0)], mat, shade=shade, name="leg", sep="deep")
    cv.polygon([(fx - 6.0, fy - 5.5), (fx + 5.6, fy - 5.5), (fx + 7.0, fy + 0.4), (fx - 6.0, fy + 0.4)], VOID,
               shade="dark" if far else "two", name="hoof", sep="deep")
    _drone(cv, knee[0] - 1.0, knee[1] - 2.0, 3.4, far=far, name="leg")


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    ground = cv.ground
    B = (cv.gx - 10 + p.bx, ground - 38.0 + p.by)
    e = p.burst
    pivot = (B[0] - 32.0, B[1] + 10.0)  # rear / pitch about the near hind hip
    xf = [px.rotate(p.rear, pivot)]

    def T(pt):  # body-local -> canvas (before the rear transform)
        return (B[0] + pt[0], B[1] + pt[1])

    def fly(pt, k):  # break-apart offset: pieces drift out from the centre and up
        if e <= 0:
            return pt
        d = (pt[0] + 0.001, pt[1] - 10.0)
        ln = math.hypot(*d)
        s = e * (4.0 + 6.0 * px.hash01(k, 7))
        return (pt[0] + d[0] / ln * s * (0.6 if d[0] < 0 else 1.0),
                pt[1] + d[1] / ln * s * 0.6 - e * e * 8.0 * (0.5 + px.hash01(k, 9)))

    feet_base = {0: (18.0, 0), 1: (25.0, 1), 2: (-32.0, 2), 3: (-25.0, 3)}  # x offset, feet index

    def foot(i):
        dx, idx = feet_base[i]
        f = p.feet[idx]
        return (B[0] + dx + f[0], ground - f[1])

    hips = {0: (15.0, 12.0), 1: (22.0, 10.0), 2: (-32.0, 10.0), 3: (-25.0, 8.0)}
    mist_back = cv.layer(above=False, outline=True)
    with cv.xform(*xf):
        body_parts = e < 0.45
        if body_parts:
            for i in (1, 3):  # far legs
                if i >= 2:  # hind legs: the hip turns with the body, the hoof stays level on the ground
                    with cv.xform(px.rotate(-p.rear, pivot)):
                        _leg(cv, px.rot_pt(T(hips[i]), p.rear, pivot), foot(i), True)
                else:
                    _leg(cv, T(hips[i]), px.rot_pt(foot(i), -p.rear, pivot) if p.rear < 0 else foot(i), True)
            # dark void body mass: the gaps between plates
            g = cv.union(cv.geom_ellipse(*T((-28, -12)), 22.0, 22.0 + p.breathe * 0.5),
                         cv.geom_ellipse(*T((6, -18)), 26.0, 32.0 + p.breathe),
                         cv.geom_ellipse(*T((-10, 4)), 32.0, 12.0))
            cv.draw_geom(g, VOID, name="void", shade="nolight")
        # plates (they separate and drift when the swarm breaks apart)
        plates = _topline_plates(T) + [[T(q) for q in poly] for poly in LOWER]
        for k, pts in enumerate(plates):
            if e > 0:
                c = (sum(q[0] for q in pts) / len(pts), sum(q[1] for q in pts) / len(pts))
                loc = (c[0] - B[0], c[1] - B[1])
                off = fly(loc, k)
                pts = [(q[0] + off[0] - loc[0], q[1] + off[1] - loc[1]) for q in pts]
                c = (c[0] + off[0] - loc[0], c[1] + off[1] - loc[1])
                ang = (px.hash01(k, 3) - 0.5) * 50 * e
                pts = [px.lerp_pt(c, px.rot_pt(q, ang, c), 1.0) for q in pts]
                pts = [px.lerp_pt(c, q, 1.0 - 0.35 * e) for q in pts]
            cv.polygon(pts, PLATE, name="plate", sep="deep")
            if k == len(TOPLINE) - 1 + FLANK and e < 0.3:  # the flank weak point
                c = T((-10, -10))
                _crack(cv, [(c[0] - 8, c[1] - 5), (c[0] - 3, c[1] - 1), (c[0] - 5, c[1] + 4), (c[0] + 2, c[1] + 7),
                            (c[0] + 6, c[1] + 3)], p.glow > 0)
                _crack(cv, [(c[0] - 3, c[1] - 1), (c[0] + 4, c[1] - 4)], p.glow > 0)
        # drones: belly swarm and the bristling back ridge
        for k, (x, y, r) in enumerate(DRONES):
            q = T(fly((x, y), 20 + k))
            _drone(cv, q[0], q[1], r * (1.0 - 0.2 * e))
        for k, (x, y, r) in enumerate(RIDGE):
            q = T(fly((x, y), 40 + k))
            if e < 0.3:  # a backward-raked spike on each ridge drone
                cv.polygon([(q[0] - r * 0.2, q[1] - r * 0.3), (q[0] - 4.0, q[1] - r - 6.0),
                            (q[0] + r * 0.8, q[1] - r * 0.2)], PLATE, shade="two", name="spike", sep="deep")
            _drone(cv, q[0], q[1], r * (1.0 - 0.2 * e), eye=False)
        # head: a massive wedge - brow plate, cheek plate, snout disc, jaw, tusks, eye
        Hc = T(fly((36, -18), 60))
        with cv.xform(px.rotate(p.head - 6 * e, Hc)):
            jaw = [(Hc[0] - 2, Hc[1] + 12), (Hc[0] + 22, Hc[1] + 16), (Hc[0] + 21, Hc[1] + 21), (Hc[0] + 2, Hc[1] + 22)]
            with cv.xform(px.rotate(-16 * p.jaw, (Hc[0], Hc[1] + 14))):
                cv.polygon(jaw, VOID, shade="two", name="jaw", sep="deep")
                for k, (dx, far) in enumerate(((14.0, True), (18.0, False))):  # tusks curving up
                    base = (Hc[0] + dx, Hc[1] + 16)
                    tusk = [base, (base[0] + 5, base[1] - 1), (base[0] + 9, base[1] - 6), (base[0] + 9, base[1] - 12)]
                    cv.limb(tusk, [2.6, 2.2, 1.5, 0.6], TUSK, shade="dark" if far else "soft", name="tusk",
                            sep="deep")
            skull = [(Hc[0] - 10, Hc[1] - 12), (Hc[0] + 6, Hc[1] - 16), (Hc[0] + 20, Hc[1] - 8),
                     (Hc[0] + 27, Hc[1] + 4), (Hc[0] + 25, Hc[1] + 14), (Hc[0] + 4, Hc[1] + 14), (Hc[0] - 8, Hc[1] + 6)]
            cv.polygon(skull, PLATE, name="skull", sep="deep")
            cv.polygon([(Hc[0] - 8, Hc[1] - 12), (Hc[0] + 6, Hc[1] - 16), (Hc[0] + 16, Hc[1] - 8),
                        (Hc[0] + 2, Hc[1] - 4)], PLATE, shade="two", name="skull", sep="deep")
            cv.polygon([(Hc[0] - 6, Hc[1] + 2), (Hc[0] + 10, Hc[1] + 0), (Hc[0] + 14, Hc[1] + 12),
                        (Hc[0] - 2, Hc[1] + 12)], PLATE, shade="two", name="skull", sep="deep")
            cv.ellipse(Hc[0] + 27, Hc[1] + 7, 3.8, 7.4, PLATE, shade="two", name="snout", sep="deep")
            cv.pixels([(round(Hc[0] + 27), round(Hc[1] + 4)), (round(Hc[0] + 27), round(Hc[1] + 9))], VOID.deep,
                      name="snout")
            # empty white eye in a dark socket under the brow plate
            ex, ey = round(Hc[0] + 9), round(Hc[1] - 5)
            hc.eye_stamp(cv, [".kkk.", "kwwwk", ".kkk."], ex - 2, ey - 1, {"k": VOID.deep, "w": EYE_W})
            if e < 0.3:  # skull weak point
                _crack(cv, [(Hc[0] - 4, Hc[1] - 10), (Hc[0] + 1, Hc[1] - 6), (Hc[0] - 2, Hc[1] - 1), (Hc[0] + 3, Hc[1] + 2)],
                       p.glow > 0)
            tusk_tip = cv.tp((Hc[0] + 27, Hc[1] + 2))
        if body_parts:
            for i in (0, 2):  # near legs
                if i >= 2:
                    with cv.xform(px.rotate(-p.rear, pivot)):
                        _leg(cv, px.rot_pt(T(hips[i]), p.rear, pivot), foot(i), False)
                else:
                    _leg(cv, T(hips[i]), px.rot_pt(foot(i), -p.rear, pivot) if p.rear < 0 else foot(i), False)

    # weak points flaring: glow rays around the cracks
    if p.glow == 2 and e == 0:
        fx = cv.layer(above=True, outline=False)
        for c, n in ((T((-10, -10)), 6), (T((36, -24)), 4)):
            c = px.rot_pt(c, p.rear, pivot)
            for k in range(n):
                a = k * 360 / n + 15
                q0, q1 = px.polar(c, a, 10.0), px.polar(c, a, 15.0)
                fx.line((round(q0[0]), round(q0[1])), (round(q1[0]), round(q1[1])), GLOW_EDGE, name="flare")
    # mist pouring off the back and the belly
    ph = p.mist
    for k in range(4):
        age = ((ph * 0.3 + k * 0.25) % 1.0)
        q = px.rot_pt(T((-36 + k * 16 - age * 8, -44 + (k % 2) * 6 - age * 8)), p.rear, pivot)
        q = (max(9.0, q[0]), max(8.0, q[1]))
        mist_back.ellipse(q[0], q[1], 5.0 - 2.0 * age, 2.2, hc.HOLLOW_MIST, shade="soft", name="mist")
        mist_back.ellipse(q[0] + 3.0, q[1] - 1.5, 2.6 - age, 1.6, hc.HOLLOW_MIST, shade="soft", name="mist")
    for k in range(3):  # mist spilling off the belly between the legs
        age = ((ph * 0.3 + k * 0.33) % 1.0)
        q = px.rot_pt(T((-22 + k * 14 - age * 6, 20 + age * 8)), p.rear, pivot)
        if q[1] < ground - 3:
            mist_back.ellipse(q[0], q[1], 4.2 - 1.6 * age, 1.8, hc.HOLLOW_MIST, shade="soft", name="mist")
    if e > 0:  # the swarm lifting away
        top = cv.layer(above=True, outline=True)
        for k in range(8):
            a = 30 + k * 18
            r = 28 + 18 * e + 6 * px.hash01(k)
            q = px.polar((B[0], B[1] - 10), a, r * (0.6 + 0.4 * px.hash01(k, 1)))
            q = (q[0], q[1] - e * 12)
            if 6 < q[0] < cv.w - 8 and q[1] > 8:
                _drone(top, q[0], q[1], 2.6 + px.hash01(k, 2), name="swarm")
        for k in range(3):
            hc.mist_puff(top, B[0] - 20 + k * 22, ground - 8 - e * 6 - k * 3, 5.0 - k, mat=hc.HOLLOW_MIST)
    if p.dust is not None:
        d = cv.layer(above=True, outline=True)
        px.dust(d, B[0] - 28, cv.gy - 1, p.dust, size=1.6, direction=-1)
        px.dust(d, B[0] + 14, cv.gy - 1, p.dust * 0.8, size=1.4, direction=-1)
    if p.speed:
        back = cv.layer(above=False, outline=False)
        px.speed_lines(back, B[0] - 48, B[1] - 14, length=6, count=4, spacing=9, direction=-1, color=px.MIST_BLUE)
    if p.hit:
        top = cv.layer(above=True, outline=False)
        px.impact(top, min(tusk_tip[0] - 2, cv.w - 8), tusk_tip[1], size=4)
