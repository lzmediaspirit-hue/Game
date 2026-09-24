"""Old snapper - elite mini-boss: ancient river snapping turtle with one crab crusher claw.

View: side, facing right.  ~38 art px tall, ~64 long on a 96 px art canvas (cell 192).
Parts, back to front: far legs, tail, belly, near legs, shell (+ keel knobs, seams,
moss, barnacles, serrated rim), trailing weeds, neck + head (beak, eye, brow),
crusher claw (arm solved with ``px.ik2``), FX (splash + dust + impact).
"""
import math

import pixel as px

SPEC = {
    "id": "old_snapper",
    "cell": 192,
    "anchor": [96, 168],
    "flying": False,
    "hit_frame": 1,
}

# ---- palette ------------------------------------------------------------------------------
SHELL = px.material("snap_shell", "#61784a", "#3d5034", "#2a392c", "#1a2621", outline="#09110e",
                    thresholds=(0.93, 0.6, 0.26))
MOSS = px.material("moss", "#b3d066", "#80a445", "#5b7c36", "#3c5a2b", outline="#0d170c")
BARNACLE = px.material("barnacle", "#f4f2e6", "#cbcfc2", "#959c92", "#616b65", outline="#131918")
WEED = px.material("river_weed", "#93ae58", "#62803d", "#425c33", "#2b3e2a", outline="#0b140d")
SKIN = px.material("snap_skin", "#a29a6c", "#736e4f", "#4f4f3e", "#33372f", outline="#0f1210",
                   thresholds=(0.92, 0.56, 0.22))
BELLY = px.material("snap_belly", "#d0c08e", "#a7966b", "#786c52", "#4f493c", outline="#0f1210")
BEAK = px.material("snap_beak", "#f0e2b6", "#cbb98a", "#958561", "#5c5242", outline="#14110d",
                   thresholds=(0.9, 0.45, 0.15))
HOOK = px.material("snap_hook", "#8a7a5c", "#5e533f", "#443c31", "#2e2922", outline="#14110d")
CLAW = px.material("crusher", "#de9463", "#a95c3d", "#763c33", "#4a262b", outline="#1a0b0e",
                   thresholds=(0.9, 0.55, 0.2))
CLAW_TIP = px.material("crusher_tip", "#74514b", "#44302f", "#2e2024", "#1d1519", outline="#0c0709")
TOOTH = px.material("crusher_tooth", "#fdf3d8", "#e6d4a8", "#b6a27a", "#7e6f56", outline="#1a0b0e")
TALON = px.flat("#ddd3b2", outline="#0f1210")
IRIS = px.rgb("#f4b73a")
SEAM = SHELL.step(1)  # seams / creases: one tone darker than the surface under them
FOLD = SKIN.step(1)

# ---- poses --------------------------------------------------------------------------------
# bx, by   body offset          sq  vertical squash of the whole turtle (weight)
# neck     neck reach (1 = out, 0 = pulled into the shell)   head  head tilt (deg)
# jaw      beak gape 0..1       claw (dx, dy, angle, open): palm offset from its resting
#          place, pointing angle (deg, 0 = right, 90 = up) and pincer opening 0..1
# feet     (dx, lift) near-front, far-front, near-hind, far-hind
# weed     weed sway phase      eye  angry|squeeze|dead
# elbow    claw-arm bend: 0 = auto (forward, off the ground), +1 / -1 = force a side
# rear     rear up (deg) about the hind feet - lifts the front for the windup
# rot      whole-body roll (deg, death tumble)   flip  on its back   curl  legs curl (dead)
# splash   splash/dust life 0..1 at the claw impact point (None = off)
DEFAULTS = dict(bx=0, by=0, sq=1.0, neck=1.0, head=0, jaw=0.0, claw=(0, 0, 4, 0.25),
                feet=((0, 0), (0, 0), (0, 0), (0, 0)), weed=0.0, eye="angry", rot=0, flip=False,
                splash=None, hit=False, fade=1.0, curl=0.0, breathe=0.0, rear=0, elbow=0)

POSE = px.poses(DEFAULTS, {
    "idle": [
        dict(weed=0.0),
        dict(weed=1.0, breathe=0.5, head=2, claw=(0, -1, 6, 0.35)),
        dict(weed=2.0, breathe=0.7, head=2, claw=(0, -1, 6, 0.4), jaw=0.15),
        dict(weed=3.0, breathe=0.2, claw=(0, 0, 4, 0.2)),
    ],
    "walk": [  # heavy lumber: diagonal pairs, shell rocks, claw swings a little
        dict(feet=((3, 0), (-2, 2), (-3, 2), (2, 0)), weed=0.0),
        dict(feet=((2, 0), (-1, 3), (-2, 1), (1, 0)), weed=1.0, by=-1, head=1, claw=(1, -2, 6, 0.25)),
        dict(feet=((0, 1), (1, 1), (0, 0), (0, 1)), weed=2.0),
        dict(feet=((-2, 2), (3, 0), (2, 0), (-3, 2)), weed=3.0),
        dict(feet=((-1, 3), (2, 0), (1, 0), (-2, 1)), weed=4.0, by=-1, head=1, claw=(-1, -2, 2, 0.25)),
        dict(feet=((1, 1), (0, 1), (0, 1), (1, 0)), weed=5.0),
    ],
    "windup": [  # crusher raised high overhead, pincer gaping - held as the tell
        dict(claw=(-3, -11, 30, 0.5), head=4, neck=0.9, weed=1.0, jaw=0.2, rear=2),
        dict(claw=(-6, -21, 38, 0.9), head=8, neck=0.8, weed=2.0, jaw=0.5, rear=5),
        dict(claw=(-7, -24, 42, 1.0), head=10, neck=0.75, weed=3.0, jaw=0.7, rear=6),
    ],
    "attack": [  # slam: fast drop, hit on frame 1 with a splash, hold, recover
        dict(claw=(1, -15, 5, 0.7), head=-4, weed=4.0, jaw=0.4, rear=2),
        dict(claw=(-2, -2, -12, 0.0), head=-8, weed=5.0, jaw=0.6, by=1, sq=0.97, splash=0.15, hit=True),
        dict(claw=(-2, -2, -12, 0.0), head=-6, weed=0.0, jaw=0.3, by=1, sq=0.98, splash=0.5),
        dict(claw=(-1, -1, -2, 0.2), head=-2, weed=1.0, splash=0.85),
    ],
    "hurt": [  # head pulls partly into the shell, eyes squeezed, claw flinches up
        dict(neck=0.4, head=12, eye="squeeze", claw=(5, -5, -12, 0.7), bx=-2, weed=2.0, by=1, jaw=0.3,
             elbow=-1),
        dict(neck=0.6, head=6, eye="squeeze", claw=(4, -4, -6, 0.5), bx=-1, weed=3.0, elbow=-1),
    ],
    "death": [  # stagger, roll over, land on its back, settle
        dict(neck=0.5, head=12, eye="squeeze", claw=(-3, -6, 50, 0.8), bx=-2, rot=5, weed=2.0),
        dict(neck=0.4, eye="dead", rot=28, claw=(-2, -8, 60, 0.9), weed=3.0, by=-3),
        dict(flip=True, neck=0.5, eye="dead", claw=(0, 0, 20, 1.0), weed=4.0, jaw=0.5, sq=1.03),
        dict(flip=True, neck=0.6, eye="dead", claw=(0, 0, 20, 0.6), weed=5.0, sq=0.94, curl=0.5, jaw=0.6),
        dict(flip=True, neck=0.6, eye="dead", claw=(0, 0, 20, 0.3), weed=5.0, curl=1.0, jaw=0.6),
    ],
})


# ---- parts --------------------------------------------------------------------------------
def _leg(cv, hip, foot, far):
    """Thick scaly column with a flat foot and three pale talons."""
    shade = "dark" if far else "soft"
    fx, fy = foot
    knee = px.ik2(hip, (fx, fy - 2.4), 5.0, 5.0, bend=1)
    cv.limb([hip, knee, (fx, fy - 2.4)], [3.8, 3.2, 2.8], SKIN, shade=shade, name="leg",
            sep=False if far else "deep")
    cv.ellipse(fx + 1.0, fy - 1.4, 3.8, 1.7, SKIN, shade="dark" if far else "two", name="foot")
    if not far:
        for k in range(3):
            cv.pixel(round(fx + 2.6 + k * 1.4) - 1, round(fy - 1.0), TALON, name="talon")


def _claw(cv, shoulder, palm, ang, opening, bend=0):
    """The crusher: 2-bone arm, bulbous palm, two heavy toothed fingers, dark tips."""
    wrist = px.polar(palm, ang + 180, 5.0)
    if bend:
        elbow = px.ik2(shoulder, wrist, 9.5, 9.5, bend=bend)
    else:  # elbow on whichever side keeps it forward and off the ground
        cands = [px.ik2(shoulder, wrist, 9.5, 9.5, bend=b) for b in (1, -1)]
        elbow = max(cands, key=lambda e: e[0] - max(0.0, e[1] - shoulder[1] - 4.0) * 3)
    cv.limb([shoulder, elbow, wrist], [3.0, 2.7, 3.0], CLAW, shade="soft", name="arm", sep=True)
    cv.ellipse(palm[0], palm[1], 7.2, 5.6, CLAW, angle=ang, name="claw", sep=True)
    front = px.polar(palm, ang, 4.6)
    fingers = []
    # upper finger (dactyl) hinges open; the lower one (pollex) stays in line with the palm
    for sgn, ln, r0, a in ((1, 10.0, 2.8, ang + 6 + 44 * opening), (-1, 8.8, 3.2, ang - 4 - 6 * opening)):
        root = px.polar(front, ang + 90 * sgn, 2.0)
        mid = px.polar(root, a, ln * 0.55)
        tip = px.polar(mid, a - sgn * (30 + 14 * (1 - opening)), ln * 0.5)
        fingers.append((root, mid, tip, r0))
        cv.limb([root, mid, tip], [r0, r0 * 0.72, 0.75], CLAW, name="finger", sep="deep")
        cv.limb([px.lerp_pt(mid, tip, 0.3), tip], [r0 * 0.75, 0.8], CLAW_TIP, decal=True, clip="finger")
        # crusher teeth: two pale nubs on the inner edge
        for t in (0.45, 0.85):
            nub = px.polar(px.lerp_pt(root, mid, t), ang - sgn * 90, r0 * 0.55)
            cv.circle(nub[0], nub[1], 0.75, TOOTH, shade="soft", decal=True, clip="finger")
    # old barnacles on the back of the claw
    for off, r in ((110, 1.5), (140, 1.1)):
        b = px.polar(palm, ang + off, 4.2)
        cv.circle(b[0], b[1], r, BARNACLE, shade="soft", name="claw")
    return fingers


def _weeds(cv, roots, phase, lengths):
    """River weed strands trailing from the shell rim, swaying with ``phase``."""
    for k, ((x, y), ln) in enumerate(zip(roots, lengths)):
        pts = [(x, y)]
        for s in range(1, 4):
            sway = math.sin(phase * 1.1 + k * 1.7 + s * 0.8) * 1.0 * s / 3
            pts.append((x - 0.8 * s + sway, y + ln * s / 3))
        cv.limb(pts, [1.3, 1.1, 0.85, 0.55], WEED, shade="soft", name="weed", sep="deep")


def _shell(cv, S, br, flip):
    rx, ry = 24.0, 20.0 + br
    dome = cv.geom_ellipse(S[0], S[1], rx, ry, angle=-2)
    # knobbly keel: bumps sitting on the dome's top line
    knobs = []
    for dx in (-13.0, -5.0, 3.5, 11.5):
        top = S[1] - ry * math.sqrt(max(0.0, 1 - (dx / rx) ** 2))
        knobs.append(cv.geom_ellipse(S[0] + dx, top + 1.4, 3.0, 2.2))
    shell = cv.union(dome, *knobs, weights=[1.0] + [0.45] * len(knobs))
    cut = cv.mask_polygon([(S[0] - 30, S[1] + 2.5), (S[0] + 30, S[1] + 1.5),
                           (S[0] + 30, S[1] + 30), (S[0] - 30, S[1] + 30)])
    # serrated rear marginal scutes hanging below the cut line
    teeth = cv.mask_polygon([(S[0] - 23.5, S[1] + 1.5), (S[0] - 22.0, S[1] + 5.2), (S[0] - 20.3, S[1] + 2.0),
                             (S[0] - 19.2, S[1] + 5.6), (S[0] - 17.2, S[1] + 2.2), (S[0] - 16.2, S[1] + 5.4),
                             (S[0] - 14.2, S[1] + 2.4)])
    mask = (shell[0] & ~cut) | teeth
    cv.draw_geom((mask,) + shell[1:], SHELL, name="shell", sep="deep")
    # marginal rim: a darker band with a lighter lip along the bottom edge
    cv.limb([(S[0] - 24, S[1] - 1.0), (S[0] - 8, S[1] + 1.8), (S[0] + 10, S[1] + 1.2), (S[0] + 24, S[1] - 2.0)],
            1.8, SEAM, decal=True, clip="shell")
    # scute seams (vertebral row on top, costal row on the side), slightly irregular
    for a, b in (((-9.0, -18.0), (-10.0, -9.0)), ((0.0, -19.5), (0.5, -9.5)), ((9.0, -17.8), (10.0, -9.0)),
                 ((-19.0, -9.5), (-10.0, -9.0)), ((-10.0, -9.0), (0.5, -9.5)), ((0.5, -9.5), (10.0, -9.0)),
                 ((10.0, -9.0), (19.5, -8.0)), ((-15.5, -8.5), (-16.5, -1.0)), ((-5.0, -9.2), (-5.5, -0.5)),
                 ((5.5, -9.2), (6.0, -0.5)), ((15.5, -8.2), (16.5, -1.5))):
        cv.line((round(S[0] + a[0]), round(S[1] + a[1])), (round(S[0] + b[0]), round(S[1] + b[1])),
                SEAM, band=None, decal=True, clip="shell")
    # moss mats on the upper dome (decals keep the shell's light bands)
    for (mx, my, rx_, ry_) in ((-6.5, -16.5, 6.0, 2.8), (3.5, -17.0, 5.0, 2.4), (-15.5, -11.0, 3.4, 2.4),
                               (13.5, -12.5, 3.2, 2.0), (-1.0, -13.0, 2.4, 1.5), (-11.0, -6.5, 1.8, 1.4)):
        cv.ellipse(S[0] + mx, S[1] + my, rx_, ry_, MOSS, decal=True, clip="shell")
    if not flip:  # tufts poking above the ridge + moss dripping over the side
        for (mx, my) in ((-9.5, -20.2), (-3.5, -21.0), (2.5, -21.0), (6.0, -20.6), (-12.5, -18.6)):
            cv.pixel(round(S[0] + mx), round(S[1] + my), MOSS.light, name="moss")
        for (mx, my, ln) in ((-15.0, -9.0, 3.0), (13.0, -10.5, 2.0)):
            cv.line((round(S[0] + mx), round(S[1] + my)), (round(S[0] + mx), round(S[1] + my + ln)),
                    MOSS, band=None, decal=True, clip="shell")
    # barnacle clusters on the rear flank
    for (bx_, by_, r) in ((-18.0, -4.5, 2.1), (-21.0, -1.0, 1.6), (-15.0, -7.5, 1.5), (17.5, -4.0, 1.8)):
        c = (round(S[0] + bx_), round(S[1] + by_))
        cv.polygon([(c[0] - r, c[1] + r * 0.9), (c[0] - r * 0.45, c[1] - r * 0.8), (c[0] + r * 0.45, c[1] - r * 0.8),
                    (c[0] + r, c[1] + r * 0.9)], BARNACLE, shade="soft", name="barnacle", sep="deep")
        cv.pixel(c[0] - 1 if r < 2 else c[0] - 1, c[1] - 1, BARNACLE.deep, name="barnacle")
        if r >= 2:
            cv.pixel(c[0], c[1] - 1, BARNACLE.deep, name="barnacle")


def _head(cv, N0, Hc, p):
    neck_g = cv.geom_limb([N0, px.lerp_pt(N0, Hc, 0.55), Hc], [5.0, 4.6, 4.6])
    head_g = cv.geom_ellipse(Hc[0] + 0.5, Hc[1] - 0.8, 7.0, 6.0, angle=-6)
    cv.draw_geom(cv.union(neck_g, head_g, weights=[0.7, 1.0]), SKIN, name="head", sep="deep")
    # skin folds on the neck, flecks of lighter scales
    for a, b in (((-7.5, -2.0), (-6.5, 3.5)), ((-10.5, -1.5), (-9.5, 3.8))):
        cv.line((round(Hc[0] + a[0]), round(Hc[1] + a[1])), (round(Hc[0] + b[0]), round(Hc[1] + b[1])),
                FOLD, band=None, decal=True, clip="head")
    for (sx, sy) in ((-4.0, 2.5), (-8.5, 0.5), (-2.5, -4.0)):
        cv.pixel(round(Hc[0] + sx), round(Hc[1] + sy), SKIN.light, name="fleck")
    # lower jaw hinges open under the hooked upper beak
    with cv.xform(px.rotate(-20 * p.jaw, (Hc[0] + 2.0, Hc[1] + 3.0))):
        cv.polygon([(Hc[0] + 1.0, Hc[1] + 2.4), (Hc[0] + 9.0, Hc[1] + 3.2), (Hc[0] + 9.6, Hc[1] + 4.6),
                    (Hc[0] + 2.5, Hc[1] + 6.4)], BEAK, shade="two", name="beak", sep="deep")
    # massive hooked upper beak
    cv.polygon([(Hc[0] + 1.5, Hc[1] - 5.0), (Hc[0] + 8.0, Hc[1] - 3.4), (Hc[0] + 11.6, Hc[1] + 0.2),
                (Hc[0] + 11.8, Hc[1] + 4.2), (Hc[0] + 10.6, Hc[1] + 6.2), (Hc[0] + 9.2, Hc[1] + 3.2),
                (Hc[0] + 2.0, Hc[1] + 2.4)], BEAK, name="beak", sep="deep")
    cv.polygon([(Hc[0] + 9.6, Hc[1] + 0.8), (Hc[0] + 12.5, Hc[1] + 1.0), (Hc[0] + 12.5, Hc[1] + 7.0),
                (Hc[0] + 9.4, Hc[1] + 3.6)], HOOK, decal=True, clip="beak")
    cv.pixel(round(Hc[0] + 9), round(Hc[1] - 2), BEAK.deep, name="nostril")
    cv.line((round(Hc[0] + 3), round(Hc[1] + 2)), (round(Hc[0] + 9), round(Hc[1] + 3)), BEAK.deep, name="mouth")
    # eye: gold iris under a heavy brow ridge
    ex, ey = round(Hc[0] - 1.0), round(Hc[1] - 3.0)
    if p.eye == "squeeze":
        cv.stamp(["kk...", "..kkk", "kk..."], ex - 1, ey - 1, {"k": px.INK}, name="eye")
    elif p.eye == "dead":
        cv.stamp(["k.k", ".k.", "k.k"], ex, ey - 1, {"k": px.INK}, name="eye")
    else:
        cv.stamp(["gii", "iki", "iik"], ex, ey - 1, {"k": px.INK, "g": px.GLINT, "i": IRIS}, name="eye")
    if p.eye not in ("dead", "squeeze"):  # heavy brow ridge (a squint carries its own shape)
        cv.limb([(ex - 2.0, ey - 3.2), (ex + 1.5, ey - 2.2), (ex + 4.6, ey - 0.4)], [1.4, 1.3, 0.8], SKIN,
                shade="nolight", name="brow", sep="deep")
    cv.line((ex - 1, ey + 3), (ex + 2, ey + 3), FOLD, band=None, decal=True, clip="head")  # eye bag


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    ground = cv.ground  # centre of the last filled row (outline lands on gy - 1)
    B = (cv.gx - 5 + p.bx, ground - 13.5 + p.by)
    cv.opacity = p.fade
    xf = [px.scale(1.0, p.sq, (B[0], ground))]
    if p.rear:  # pivot on the hind feet: the front (and claw shoulder) lifts
        xf.append(px.rotate(p.rear, (B[0] - 14.0, ground)))
    if p.rot:
        xf.append(px.rotate(p.rot, B))
        cv.snap_ground = True
    if p.flip:  # rolled onto its back along the spine: mirror vertically, head stays right
        xf = [px.scale(1.0, p.sq, (B[0], ground)), px.flip_y(B[1])]
        cv.snap_ground = True

    def foot(dx, i):
        if p.flip:  # legs in the air, curling toward the plastron
            return (B[0] + dx * (1 - 0.3 * p.curl), B[1] + 14.0 - 5.0 * p.curl)
        f = p.feet[i]
        return (B[0] + dx + f[0], ground - f[1])

    with cv.xform(*xf):
        _leg(cv, (B[0] + 16.0, B[1] + 3.5), foot(18.0, 1), True)
        _leg(cv, (B[0] - 11.0, B[1] + 3.5), foot(-11.0, 3), True)
        # thick tail with a saw-tooth ridge
        tail = [(B[0] - 20.0, B[1] + 3.0), (B[0] - 26.5, B[1] + 6.5), (B[0] - 33.0, B[1] + 8.5)]
        cv.limb(tail, [3.2, 2.0, 0.6], SKIN, name="tail")
        for t in (0.3, 0.6, 0.85):
            q = px.lerp_pt(tail[0], tail[2], t)
            h = 2.2 * (1 - t) + 0.6
            cv.polygon([(q[0] - 1.3, q[1] - h), (q[0], q[1] - h - 2.0), (q[0] + 1.1, q[1] - h + 0.2)],
                       SKIN, shade="two", name="tail")
        cv.ellipse(B[0] + 1.0, B[1] + 4.5, 20.0, 4.6, BELLY, shade="two", name="belly")
        _leg(cv, (B[0] - 13.0, B[1] + 4.0), foot(-14.5, 2), False)
        _leg(cv, (B[0] + 13.0, B[1] + 4.0), foot(14.5, 0), False)

        _shell(cv, (B[0] - 1.0, B[1] + 1.5), p.breathe, p.flip)
        _weeds(cv, [(B[0] - 16.0, B[1] + 4.0), (B[0] - 5.0, B[1] + 5.2), (B[0] + 6.0, B[1] + 4.8)],
               p.weed, (8.5, 6.0, 5.0) if not p.flip else (3.0, 2.5, 2.0))

        N0 = (B[0] + 18.0, B[1] + 0.5)
        Hc = (N0[0] + 2.5 + 8.0 * p.neck, N0[1] - 5.5 * p.neck)
        with cv.xform(px.rotate(p.head, Hc)):
            _head(cv, N0, Hc, p)

        cdx, cdy, cang, copen = p.claw
        shoulder = (B[0] + 15.0, B[1] + 4.0)
        palm = (B[0] + 29.0 + cdx, B[1] + 8.0 + cdy)
        fingers = _claw(cv, shoulder, palm, cang, copen, p.elbow)
        impact = cv.tp(fingers[1][2])

    if p.splash is not None:
        fx = cv.layer(above=True, outline=True)
        px.splash(fx, impact[0] + 1, cv.gy - 1, p.splash, size=1.3)
        px.dust(fx, impact[0] - 4, cv.gy - 1, p.splash, size=0.9, direction=-1)
    if p.hit:
        top = cv.layer(above=True, outline=False)
        px.impact(top, impact[0] + 2, impact[1] - 2, size=4)
