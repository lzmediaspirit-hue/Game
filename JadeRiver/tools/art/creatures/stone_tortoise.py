"""Stone tortoise - a huge, slow tortoise whose shell is a small stone mountain: craggy
peaks, mossy ledges and a tiny wind-bent pine (Earth element, large creature).

View: side, facing right.  ~33 art px tall (peak), ~62 long, on a 96 px canvas (cell 192).
Parts, back to front: far legs (dark), stub tail, plastron, near legs (elephantine
columns with scale bands and pale nails), the mountain shell (faceted: each ridge splits
a lit left face from a shaded right face; strata lines, moss on the ledges, a pine on the
saddle, dark scute rim along the base), neck + old beaked head (heavy lid, amber eye).
Windup rears up on the hind legs; the slam lands on ``hit_frame`` with a shockwave dust
ring.  Death: head and legs withdraw, the mountain cracks.
"""
import math

import pixel as px

SPEC = {
    "id": "stone_tortoise",
    "cell": 192,
    "anchor": [96, 168],
    "flying": False,
    "hit_frame": 1,
}

# ---- palette: pale granite, warm grey-olive hide, moss greens, pine -----------------------
ROCK = px.material("mtn_rock", "#d6d0bd", "#a39e8f", "#72726b", "#4b4e50", outline="#111416")
RIM = px.material("mtn_rim", "#8e897a", "#6a675c", "#4c4b45", "#333431", outline="#111416")
SKIN = px.material("tort_skin", "#b8ae8e", "#888067", "#5e5a4a", "#3d3c33", outline="#121310",
                   thresholds=(0.9, 0.55, 0.2))
BELLY = px.material("tort_belly", "#d9cc9e", "#ae9f76", "#7f735a", "#554d3f", outline="#121310")
MOSS = px.material("mtn_moss", "#b9d86c", "#7fa947", "#557f39", "#36572e", outline="#0d170c")
PINE = px.material("mtn_pine", "#6f9c55", "#3f6e44", "#2c5139", "#1d372b", outline="#0a130e")
BARK = px.material("mtn_bark", "#9a7452", "#6d4f38", "#4c372a", "#33251e", outline="#140d09")
BEAK = px.material("tort_beak", "#e5d7a8", "#b9a77a", "#877858", "#5a5040", outline="#14110d")
NAIL = px.flat("#e6dcbc", outline="#121310")
IRIS = px.rgb("#e0a93c")
CRACK = px.rgb("#23272a")
SEAM = ROCK.step(1)

# ---- poses --------------------------------------------------------------------------------
# bx, by   body offset          rear  rear up about the hind feet (deg)     sq  vertical squash
# neck     neck reach 1 (out) .. 0 (in)     head  head tilt (deg)    jaw  beak gape 0..1
# feet     (dx, lift) near-front, far-front, near-hind, far-hind       legs  leg extension 0..1
# eye      open|angry|squeeze|dead|closed   crack  shell cracks 0..1    ring  shockwave life
# pine     pine sway (px)    fade  opacity
DEFAULTS = dict(bx=0, by=0, rear=0, sq=1.0, neck=1.0, head=0, jaw=0.0, feet=((0, 0),) * 4, legs=1.0, eye="open",
                crack=0.0, ring=None, pine=0.0, fade=1.0, hit=False, breathe=0.0, chunk=0.0)

POSE = px.poses(DEFAULTS, {
    "idle": [  # slow breaths, the old head nods
        dict(),
        dict(breathe=0.5, head=2, pine=0.5),
        dict(breathe=0.7, head=3, pine=1.0),
        dict(breathe=0.3, head=1, pine=0.5, eye="closed"),
    ],
    "walk": [  # ponderous lumber: diagonal pairs, the mountain rocks a little
        dict(feet=((3, 0), (-2, 2), (-3, 2), (2, 0)), head=1),
        dict(feet=((2, 0), (-1, 3), (-2, 1), (1, 0)), by=-1, head=2, pine=0.5),
        dict(feet=((0, 1), (1, 1), (0, 0), (0, 1)), head=1, pine=1.0),
        dict(feet=((-2, 2), (3, 0), (2, 0), (-3, 2)), head=0, pine=0.5),
        dict(feet=((-1, 3), (2, 0), (1, 0), (-2, 1)), by=-1, head=1),
        dict(feet=((1, 1), (0, 1), (0, 1), (1, 0)), head=2),
    ],
    "windup": [  # heaves its front up onto the hind legs, head raised - held
        dict(rear=6, feet=((1, 3), (1, 3), (0, 0), (0, 0)), head=6, eye="angry", pine=-0.5),
        dict(rear=13, feet=((2, 6), (2, 6), (0, 0), (0, 0)), head=10, eye="angry", jaw=0.3, pine=-1.0),
        dict(rear=17, feet=((2, 8), (2, 8), (0, 0), (0, 0)), head=12, eye="angry", jaw=0.5, pine=-1.5),
    ],
    "attack": [  # slams down: the shockwave ring bursts out on frame 1, spreads, settles
        dict(rear=6, feet=((2, 3), (2, 3), (0, 0), (0, 0)), head=-2, eye="angry", jaw=0.4, pine=1.0),
        dict(sq=0.94, by=1, head=-6, eye="angry", jaw=0.6, ring=0.12, hit=True, pine=1.5),
        dict(sq=0.97, head=-4, eye="angry", jaw=0.3, ring=0.5, pine=0.5),
        dict(head=-1, ring=0.85),
    ],
    "hurt": [
        dict(bx=-2, neck=0.5, head=10, eye="squeeze", feet=((1, 2), (0, 1), (0, 0), (0, 0)), pine=-1.0),
        dict(bx=-1, neck=0.7, head=5, eye="squeeze"),
    ],
    "death": [  # draws head and legs into the shell, the mountain cracks and sheds a rock
        dict(bx=-2, neck=0.4, head=10, eye="squeeze", legs=0.7),
        dict(bx=-2, neck=0.05, eye="closed", legs=0.3, by=4, crack=0.3),
        dict(bx=-2, neck=0.0, eye="closed", legs=0.0, by=6, crack=0.7, chunk=0.4),
        dict(bx=-2, neck=0.0, eye="closed", legs=0.0, by=6, crack=1.0, chunk=1.0, fade=0.6),
        dict(bx=-2, neck=0.0, eye="closed", legs=0.0, by=6, crack=1.0, chunk=1.0, fade=0.3),
    ],
})

# mountain outline relative to the shell base centre (x right, y up = negative)
PEAKS = ((-9.5, -18.5), (-1.5, -24.0), (6.0, -18.5))  # secondary, main, third
OUTLINE = ((-24.5, 3.0), (-23.5, -2.0), (-20.0, -6.0), (-17.5, -6.8), (-15.0, -11.0), (-12.5, -12.0), PEAKS[0],
           (-7.5, -15.0), (-5.5, -15.5), PEAKS[1], (1.0, -20.0), (3.0, -19.8), PEAKS[2], (8.0, -15.0),
           (10.5, -13.8), (13.0, -10.0), (16.0, -8.6), (19.5, -4.5), (22.5, -1.0), (23.5, 3.0))
VALLEYS = (5, 8, 11, 14)


def _leg(cv, hip, foot, far, ext):
    shade = "dark" if far else "soft"
    fx, fy = foot
    top = (hip[0], hip[1])
    bot = (fx, fy - 4.2)
    if ext < 1.0:  # withdrawing: the leg shortens up into the shell
        bot = (hip[0] + (fx - hip[0]) * ext, hip[1] + (fy - 4.2 - hip[1]) * ext)
    cv.limb([top, bot], [4.4, 4.0], SKIN, shade=shade, name="leg", sep=False if far else "deep")
    if ext > 0.5:
        cv.ellipse(bot[0] + 0.8, fy - 1.4, 4.6, 1.8, SKIN, shade="dark" if far else "two", name="foot")
        if not far:
            # scale bands and pale nails
            for k in (0.35, 0.7):
                q = (top[0] + (bot[0] - top[0]) * k, top[1] + (bot[1] - top[1]) * k)
                cv.limb([(q[0] - 3.2, q[1] - 0.3), (q[0] + 3.2, q[1] + 0.3)], 0.5, SKIN.step(1), decal=True,
                        clip="leg")
            for k in range(3):
                cv.pixel(math.floor(bot[0] + 2.0 + k * 1.6), math.floor(fy - 1.0), NAIL, name="nail")


def _pine(cv, x, y, sway):
    """Tiny wind-bent pine on a ledge: a crooked trunk and three tiers of needles."""
    cv.limb([(x, y), (x + 0.4 + sway * 0.3, y - 3.0), (x + 1.2 + sway, y - 6.0)], [0.8, 0.6, 0.5], BARK, shade="two",
            name="pine")
    for k, (w, dy) in enumerate(((4.2, -2.4), (3.4, -4.4), (2.2, -6.4))):
        cx = x + 0.6 + sway * (0.4 + 0.3 * k)
        cv.polygon([(cx - w * 0.5 - 1.2, y + dy + 0.8), (cx + w * 0.3, y + dy - 2.0), (cx + w * 0.5 + 1.4, y + dy + 0.6)],
                   PINE, shade="soft", name="pine")


def _shell(cv, S, p):
    br = p.breathe
    pts = [(S[0] + x, S[1] + y * (1 + 0.02 * br)) for x, y in OUTLINE]
    cv.polygon(pts, ROCK, shade="flat", name="shell", sep="deep")
    # facets: each ridge splits a lit left face from a shaded right face
    valleys = [OUTLINE[i] for i in VALLEYS]
    for i, pk in enumerate(PEAKS):
        P = (S[0] + pk[0], S[1] + pk[1])
        vl = (S[0] + valleys[i][0], S[1] + valleys[i][1])
        vr = (S[0] + valleys[i + 1][0], S[1] + valleys[i + 1][1])
        # lit upper-left face (fades out halfway down), shaded right face runs to the base
        cv.polygon([vl, P, (P[0] + 1.0, P[1] + 4.0), (P[0] + 2.2, P[1] + 9.0), (vl[0] - 1.5, vl[1] + 4.5)], ROCK,
                   shade="flatlight", clip="shell", name="shell")
        cv.polygon([P, vr, (vr[0] + 1.0, vr[1] + 6.0), (P[0] + 4.0, S[1] + 1.0), (P[0] + 2.2, P[1] + 9.0),
                    (P[0] + 1.0, P[1] + 4.0)], ROCK, shade="flatdark", clip="shell", name="shell")
    # the long shaded flank at the right end and a lit shoulder at the left end
    cv.polygon([(S[0] + 13.0, S[1] - 10.0), (S[0] + 23.5, S[1] + 3.0), (S[0] + 13.0, S[1] + 3.0)], ROCK, shade="flatdark",
               clip="shell", name="shell")
    # strata lines slanting across the faces
    for a, b in (((-20.0, -3.5), (-12.0, -6.5)), ((-6.5, -6.0), (2.0, -9.5)), ((8.0, -5.0), (15.0, -7.5)),
                 ((-15.0, 0.0), (-7.0, -2.5)), ((3.0, -2.0), (11.0, -4.0))):
        cv.line((math.floor(S[0] + a[0]), math.floor(S[1] + a[1])), (math.floor(S[0] + b[0]), math.floor(S[1] + b[1])),
                SEAM, decal=True, clip="shell")
    # moss on the ledges and the upper-left slopes
    for (mx, my, rx, ry) in ((-12.5, -11.5, 3.2, 1.4), (-4.5, -15.0, 2.2, 1.1), (-17.0, -6.5, 2.8, 1.4),
                             (4.0, -15.8, 1.8, 1.0), (-9.0, -4.0, 3.5, 1.3), (12.0, -10.0, 2.0, 1.0)):
        cv.ellipse(S[0] + mx, S[1] + my, rx, ry, MOSS, shade="soft", decal=True, clip="shell")
    for (mx, my) in ((-13.5, -13.0), (-11.0, -13.2), (-18.0, -8.2), (3.5, -17.2)):
        cv.pixel(math.floor(S[0] + mx), math.floor(S[1] + my), MOSS.light, name="moss")
    # scute rim along the base: dark band with seams
    cv.polygon([(S[0] - 26, S[1] - 0.5), (S[0] + 26, S[1] - 0.5), (S[0] + 26, S[1] + 5), (S[0] - 26, S[1] + 5)],
               RIM, shade="flat", decal=True, clip="shell")
    for x in range(-19, 21, 6):
        cv.line((math.floor(S[0] + x), math.floor(S[1] - 0.5)), (math.floor(S[0] + x + 1), math.floor(S[1] + 2.5)),
                RIM.step(1), decal=True, clip="shell")
    if p.crack > 0:  # death: cracks run down from the peaks
        n = p.crack
        for pk, (dx1, dx2) in zip(PEAKS, ((-2.5, 1.0), (2.0, -1.5), (-1.5, 2.5))):
            a = (S[0] + pk[0] + 0.5, S[1] + pk[1] + 1.0)
            b = (a[0] + dx1, a[1] + 6.0 * n)
            c = (b[0] + dx2, b[1] + 6.0 * n)
            cv.line((math.floor(a[0]), math.floor(a[1])), (math.floor(b[0]), math.floor(b[1])), CRACK, decal=True,
                    clip="shell")
            if n > 0.5:
                cv.line((math.floor(b[0]), math.floor(b[1])), (math.floor(c[0]), math.floor(c[1])), CRACK, decal=True,
                        clip="shell")
    if p.chunk <= 0:
        _pine(cv, S[0] - 6.5, S[1] - 14.0, p.pine)


def _head(cv, N0, Hc, p):
    neck = cv.geom_limb([N0, px.lerp_pt(N0, Hc, 0.5), Hc], [4.6, 4.0, 3.6])
    head = cv.geom_ellipse(Hc[0] + 1.0, Hc[1] - 0.5, 5.2, 4.2, angle=-8)
    cv.draw_geom(cv.union(neck, head, weights=[0.7, 1.0]), SKIN, name="head", sep="deep")
    for dx in (-5.5, -8.0):  # neck folds
        cv.line((math.floor(Hc[0] + dx), math.floor(Hc[1] - 2)), (math.floor(Hc[0] + dx + 1), math.floor(Hc[1] + 3)),
                SKIN.step(1), decal=True, clip="head")
    # hooked beak
    with cv.xform(px.rotate(-18 * p.jaw, (Hc[0] + 2.5, Hc[1] + 1.8))):
        cv.polygon([(Hc[0] + 2.0, Hc[1] + 1.4), (Hc[0] + 7.2, Hc[1] + 1.4), (Hc[0] + 6.8, Hc[1] + 3.0),
                    (Hc[0] + 3.0, Hc[1] + 3.6)], BEAK, shade="two", name="beak", sep="deep")
    cv.polygon([(Hc[0] + 3.0, Hc[1] - 2.5), (Hc[0] + 6.5, Hc[1] - 1.5), (Hc[0] + 7.8, Hc[1] + 1.2),
                (Hc[0] + 6.8, Hc[1] + 2.6), (Hc[0] + 2.8, Hc[1] + 1.4)], BEAK, name="beak", sep="deep")
    cv.pixel(math.floor(Hc[0] + 6), math.floor(Hc[1] - 1), BEAK.deep, name="nostril")
    ex, ey = math.floor(Hc[0] + 0.5), math.floor(Hc[1] - 2.0)
    if p.eye == "squeeze":
        cv.stamp(["kk.", "..k", "kk."], ex - 1, ey - 1, {"k": px.INK}, name="eye")
    elif p.eye == "dead":
        cv.stamp(["k.k", ".k.", "k.k"], ex - 1, ey - 1, {"k": px.INK}, name="eye")
    elif p.eye == "closed":
        cv.stamp(["kkk"], ex - 1, ey + 1, {"k": px.INK}, name="eye")
    else:
        cv.stamp(["gi", "ik"], ex, ey, {"g": px.GLINT, "i": IRIS, "k": px.INK}, name="eye")
    if p.eye in ("open", "angry"):  # heavy old lid; slants down toward the beak when angry
        lid = [(ex - 1, ey - 1), (ex, ey - 1), (ex + 1, ey - 1), (ex + 2, ey - 1)]
        if p.eye == "angry":
            lid = [(ex - 1, ey - 2), (ex, ey - 1), (ex + 1, ey - 1), (ex + 2, ey)]
        cv.pixels(lid, SKIN.deep, name="lid")
    return cv.tp((Hc[0] + 8.0, Hc[1] + 2.0))


def _ring(cv, x, y, t):
    """Shockwave: a flat dust ring racing out along the ground plus puffs at its ends."""
    rx = 7 + 20 * t
    ry = 1.6 + 1.2 * t
    outer = ((cv.X - x) / rx) ** 2 + ((cv.Y - y) / ry) ** 2 <= 1.0
    inner = ((cv.X - x) / max(1.0, rx - 2.2)) ** 2 + ((cv.Y - y) / max(0.6, ry - 1.1)) ** 2 <= 1.0
    ring = outer & ~inner & (cv.Y < y + 0.5)
    if t < 0.95:
        cv.fill(ring, px.DUST, normals=None, shade="flat", name="ring")
    for d in (-1, 1):
        px.dust(cv, x + d * (rx - 2), y + 0.5, min(1.0, t * 1.1), size=0.95, direction=d)


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    ground = cv.ground
    B = (cv.gx - 4 + p.bx, ground - 12.5 + p.by)
    cv.opacity = p.fade
    xf = [px.scale(1.0, p.sq, (B[0], ground))]
    cv.snap_ground = p.legs < 0.5  # withdrawn: the shell settles on the ground
    if p.rear:
        xf.append(px.rotate(p.rear, (B[0] - 13.0, ground)))

    def foot(dx, i):
        f = p.feet[i]
        return (B[0] + dx + f[0], ground - f[1])

    with cv.xform(*xf):
        hips = {k: cv.tp(v) for k, v in {"nf": (B[0] + 14.0, B[1] + 3.0), "ff": (B[0] + 16.5, B[1] + 2.0),
                                           "nh": (B[0] - 12.0, B[1] + 3.0), "fh": (B[0] - 9.5, B[1] + 2.0)}.items()}
    # front feet follow the rear-up (lifted in the body frame), hind feet stay planted
    _leg(cv, hips["ff"], foot(17.5, 1) if not p.rear else (hips["ff"][0] + 1.5, hips["ff"][1] + 9.0 - p.feet[1][1] * 0.6),
         True, p.legs)
    _leg(cv, hips["fh"], foot(-9.0, 3), True, p.legs)
    with cv.xform(*xf):
        cv.limb([(B[0] - 20.0, B[1] + 3.0), (B[0] - 25.0, B[1] + 5.0), (B[0] - 28.0, B[1] + 5.5)], [2.6, 1.6, 0.6],
                SKIN, shade="two", name="tail")
        cv.ellipse(B[0] + 1.0, B[1] + 4.2, 20.5, 4.4, BELLY, shade="two", name="belly")
    _leg(cv, hips["nh"], foot(-13.0, 2), False, p.legs)
    _leg(cv, hips["nf"], foot(15.0, 0) if not p.rear else (hips["nf"][0] + 1.5, hips["nf"][1] + 9.5 - p.feet[0][1] * 0.6),
         False, p.legs)
    with cv.xform(*xf):
        _shell(cv, (B[0] - 1.0, B[1] + 1.0), p)
        if p.neck > 0.02:
            N0 = (B[0] + 19.0, B[1] + 0.5)
            Hc = (N0[0] + 2.0 + 7.0 * p.neck, N0[1] - 3.5 * p.neck)
            with cv.xform(px.rotate(p.head, Hc)):
                _head(cv, N0, Hc, p)
        else:  # withdrawn: only a dark opening under the front rim
            cv.ellipse(B[0] + 21.0, B[1] + 1.5, 2.6, 2.2, SKIN.step(2), shade="flat", name="hole")
    if p.chunk > 0:  # a rock breaks off the peak and tumbles to the ground
        rk = cv.layer(above=True, outline=True)
        t = p.chunk
        x = B[0] - 1.0 + PEAKS[1][0] + 14 * t
        y = B[1] + 1.0 + PEAKS[1][1] + (ground - 2.0 - (B[1] + 1.0 + PEAKS[1][1])) * min(1.0, t * t * 1.2)
        rk.polygon([(x - 2.2, y + 1.6), (x - 1.0, y - 1.8), (x + 2.0, y - 1.2), (x + 2.4, y + 1.6)], ROCK, name="rock")
    if p.ring is not None:
        fx = cv.layer(above=True, outline=True)
        _ring(fx, B[0] + 16.0, cv.gy - 1.5, p.ring)
    if p.hit:
        top = cv.layer(above=True, outline=False)
        px.impact(top, B[0] + 17.0, ground - 4.0, size=4)
