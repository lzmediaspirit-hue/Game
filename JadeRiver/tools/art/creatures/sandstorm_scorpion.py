"""Sandstorm scorpion - a dog-sized desert scorpion whose carapace has fused with wind-blown
sand into plates of rough amber desert glass (Earth).

Sunscar Desert (Glass Dunes, Scorpion Flats), Azure Expanse, levels 73-78.
View: side, facing right, camera a little above so the far legs and the far pincer peek out
behind the near ones.  ~27 art px tall at rest with the tail curled over the back (the back
plates at ~16, the player's waist), ~49 long (cell 192: room for the raised tail, the stab and
the sprawled death).
Parts, back to front: sand streams + stinger glow (behind), far legs, far pincer, body
(sand-gold prosoma + mesosoma, bone-pale belly, amber glass plates with bright glints, eye),
tail (five sand-gold segments, venom-amber telson with a dark umber barb), near legs (umber
knees and tarsi), near pincer.
Idle: pincers flex, the tail sways, sand streams off the back.  Walk: the eight legs scuttle
in two alternating sets, body low.  Windup: the tail climbs into a high arc forward over the
body, the telson glow swells and the pincers gape wide (held).  Attack: the body pitches
nose-down and the tail stabs forward over the lowered, gaping claws on frame 1 with a sand
burst and a venom spark.  Hurt: recoil, glass chips fly.  Death: rears, flips onto its back,
legs curl, the carapace cracks and sand pours out into heaps while it fades.
"""
import math

import numpy as np

import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "sandstorm_scorpion",
    "cell": 192,
    "anchor": [96, 168],
    "flying": False,
    "hit_frame": 1,
}

# ---- palette: sun-bleached sand gold, amber glass, dark umber joints, bone belly, venom amber --
# shadows lean violet-brown, lights warm cream
SAND = px.material("scorp_sand", "#fdf0c4", "#dcb46e", "#a97d62", "#6c4c5c", outline="#1d1018",
                   thresholds=(0.86, 0.46, 0.1))
LEG = px.material("scorp_leg", "#e8c286", "#bb8c58", "#86604e", "#553c4a", outline="#1d1018")
GLASS = px.material("scorp_glass", "#ffe7a2", "#f2a843", "#c46c37", "#823c3e", outline="#2a1010",
                    thresholds=(0.8, 0.45, 0.12))
UMBER = px.material("scorp_umber", "#8a6654", "#5c3e38", "#40292e", "#2a1a22", outline="#100a0e")
BELLY = px.material("scorp_belly", "#fffaea", "#f0e4c8", "#cbb59c", "#98828a", outline="#1d1018")
VENOM = px.material("scorp_venom", "#fff4b8", "#ffc444", "#ef8a2c", "#b2562e", outline="#3a160c")
VENOM_HOT = px.material("scorp_venom_hot", "#fffce6", "#fff0a0", "#ffc648", "#f2902e", outline="#4a1c0c")
GRAIN = px.material("scorp_grain", "#fdf3d6", "#ead3a0", "#c9a878", "#9c7c62", outline="#5e4238")
SEAM = SAND.step(1)
# single-colour accents with a warm outline (an auto outline of the pale glint would read grey-teal)
GLINT = px.flat(px.GLINT, outline="#2a1010")
INK = px.flat(px.INK, outline="#1d1018")
CRACK = px.flat(UMBER.deep, outline="#1d1018")
CRACK_LIT = px.flat(GRAIN.light, outline="#1d1018")

# ---- poses ------------------------------------------------------------------------------------
# bx, by    body offset            pitch  body tilt (deg, + = nose up)   fx  feet shift
# tail      5 segment directions + telson direction (deg, 90 = up), body-local
# dtail     same, but canvas angles (used while lying on its back)
# sway      extra tail curl (deg, grows toward the tip)
# nc, fc    near / far pincer: (dx, dy, angle, opening 0..1)
# lift, slide  per-leg lift / x slide: near legs 0-3 (front -> back), far legs 4-7
# knees     body dip           eye  open|angry|squeeze|dead      glow  stinger glow 0..3
# grains    sand-stream phase 0..1 (None = off)   gust  number of streams
# burst     sand burst life at the stinger (None = off)   hit  venom spark
# chips     flying glass chips life (None = off)
# flip      on its back   flail  legs thrash   curl  legs curl 0..1
# crack     carapace cracks 0..1   spill  sand pouring out 0..1   fade  frame opacity
REST_TAIL = (160, 128, 88, 45, 8, -40)
DEFAULTS = dict(bx=0, by=0, pitch=0, fx=0, tail=REST_TAIL, dtail=None, sway=0, nc=(0, 0, -2, 0.25),
                fc=(0, 0, 4, 0.25), lift=(0,) * 8, slide=(0,) * 8, knees=0, eye="open", glow=0, grains=0.0,
                gust=2, breathe=0.0, burst=None, hit=False, chips=None, flip=False, flail=False,
                curl=0.0, crack=0.0, spill=None, fade=1.0)

A = (1, 0, 1, 0, 0, 1, 0, 1)  # near 1st + 3rd, far 2nd + 4th
B = (0, 1, 0, 1, 1, 0, 1, 0)


def _ab(a, b):
    """Per-leg values: ``a`` for leg set A, ``b`` for leg set B."""
    return tuple(ma * a + mb * b for ma, mb in zip(A, B))


POSE = px.poses(DEFAULTS, {
    "idle": [  # pincers flex, tail sways, sand streams off the back
        dict(nc=(0, 0, -2, 0.25), fc=(0, 0, 4, 0.4), grains=0.0, gust=3),
        dict(nc=(0, 0, -1, 0.5), fc=(0, 0, 5, 0.25), sway=-3, breathe=0.3, grains=0.25, gust=3),
        dict(nc=(0, 1, -2, 0.4), fc=(0, 1, 4, 0.55), sway=-5, breathe=0.5, by=1, knees=1, grains=0.5, gust=3),
        dict(nc=(0, 1, -3, 0.2), fc=(0, 1, 3, 0.4), sway=-2, breathe=0.2, by=1, knees=1, grains=0.75, gust=3),
    ],
    "walk": [  # low scuttle: leg sets A / B alternate
        dict(by=1, lift=_ab(2, 0), slide=_ab(0, 1), sway=-2, grains=0.0, gust=3, nc=(0, -1, -2, 0.2)),
        dict(by=1, lift=_ab(3, 0), slide=_ab(2, 0), sway=-1, grains=1 / 6, gust=3),
        dict(by=2, slide=_ab(2, -1), sway=1, grains=2 / 6, gust=3, knees=1, fc=(0, 1, 4, 0.2)),
        dict(by=1, lift=_ab(0, 2), slide=_ab(1, 0), sway=2, grains=3 / 6, gust=3, nc=(0, -1, -2, 0.2)),
        dict(by=1, lift=_ab(0, 3), slide=_ab(0, 2), sway=1, grains=4 / 6, gust=3),
        dict(by=2, slide=_ab(-1, 2), sway=-1, grains=5 / 6, gust=3, knees=1, fc=(0, 1, 4, 0.2)),
    ],
    "windup": [  # the tail climbs into a high forward arc, the stinger glows, pincers gape - held
        dict(tail=(140, 112, 84, 52, 18, -35), by=1, knees=1, pitch=-2, nc=(0, 0, -4, 0.5), fc=(0, -1, 8, 0.5),
             eye="angry", glow=1, grains=0.1, gust=2),
        dict(tail=(118, 96, 74, 44, 10, -45), by=1, knees=1, bx=-1, pitch=-4, nc=(-1, 1, -8, 0.85),
             fc=(-1, -2, 14, 0.85), eye="angry", glow=2, grains=0.3, gust=3),
        dict(tail=(100, 84, 64, 36, 5, -50), by=2, knees=2, bx=-2, pitch=-5, nc=(-1, 2, -10, 1.0),
             fc=(-1, -3, 17, 1.0), eye="angry", glow=3, grains=0.5, gust=4),
    ],
    "attack": [  # the tail whips over and stabs forward (hit on frame 1), sand burst + venom spark
        dict(tail=(88, 58, 26, 0, -20, -42), bx=2, pitch=-7, nc=(-1, 2, -10, 1.0), fc=(-1, 3, 6, 1.0),
             eye="angry", glow=2, fx=1),
        dict(tail=(60, 12, 4, 0, -4, -10), bx=4, pitch=-12, nc=(-2, 3, -12, 1.0), fc=(-3, 5, 0, 1.0),
             eye="angry", glow=2, burst=0.1, hit=True, fx=2, slide=(1, 1, 0, 0, 1, 1, 0, 0)),
        dict(tail=(68, 24, 8, 0, -8, -20), bx=3, pitch=-9, nc=(-1, 2, -8, 0.35), fc=(-2, 4, 2, 0.35),
             eye="angry", glow=1, burst=0.6, fx=2, slide=(1, 1, 0, 0, 1, 1, 0, 0)),
        dict(tail=(125, 104, 74, 38, 6, -40), bx=1, pitch=-2, nc=(0, 0, -2, 0.2), fc=(0, 0, 4, 0.2), fx=1),
    ],
    "hurt": [  # recoil to the left, front up, glass chips fly off the back
        dict(bx=-3, fx=-1, pitch=8, tail=(172, 142, 102, 62, 26, -20), nc=(-3, -1, 8, 0.6), fc=(-3, -2, 14, 0.6),
             eye="squeeze", chips=0.25, lift=(2, 1, 0, 0, 2, 1, 0, 0), grains=None),
        dict(bx=-1, pitch=3, tail=(166, 134, 94, 50, 14, -32), nc=(-1, 0, 2, 0.3), fc=(-1, -1, 7, 0.3),
             eye="squeeze", chips=0.75, grains=None),
    ],
    "death": [  # rears, flips onto its back, legs curl, carapace cracks, sand pours out, fades
        dict(bx=-3, fx=-1, pitch=12, tail=(178, 152, 118, 78, 42, 0), nc=(-3, -1, 10, 0.7), fc=(-3, -2, 16, 0.5),
             eye="squeeze", lift=(3, 2, 0, 0, 3, 2, 0, 0), grains=None),
        dict(bx=0, flip=True, flail=True, eye="dead", dtail=(196, 168, 138, 108, 80, 50),
             nc=(0, -1, 20, 0.9), fc=(0, -1, 30, 0.9), grains=None),
        dict(bx=0, flip=True, curl=0.25, eye="dead", dtail=(196, 188, 172, 150, 124, 95), nc=(0, 1, -20, 0.8),
             fc=(0, 1, -10, 0.8), crack=0.4, spill=0.3, grains=None),
        dict(bx=0, flip=True, curl=0.6, eye="dead", dtail=(196, 188, 172, 150, 124, 95), nc=(0, 1, -24, 0.4),
             fc=(0, 1, -14, 0.4), crack=0.8, spill=0.65, fade=0.6, grains=None),
        dict(bx=0, flip=True, curl=1.0, eye="dead", dtail=(196, 188, 172, 150, 124, 95), nc=(0, 1, -26, 0.1),
             fc=(0, 1, -16, 0.1), crack=1.0, spill=1.0, fade=0.3, grains=None),
    ],
})

# ---- geometry (relative to the body centre C) -------------------------------------------------
# The rig is drawn at K times its modelled size about the anchor, so the back reaches the player's
# waist and the curled tail a little above it.  Pixel-exact details (eye, grains, glow rays,
# sparks, chips, heaps) are drawn in raw canvas pixels so they stay crisp; pose offsets for the
# body bob, leg lift and slide are given in canvas pixels too.
K = 0.8
SEG_L = 5.4
TAIL_R = (2.6, 2.45, 2.3, 2.2, 2.1)
TAIL_ROOT = (-13.5, -2.0)
MESO = (-3.5, 0.0, 11.0, 4.7)  # cx, cy, rx, ry
PRO = (8.0, 0.6, 6.8, 4.1)
# near legs, front -> back: hip, knee (body-local), foot dx (from the resting body x)
NEAR_LEGS = (
    ((9.0, 2.6), (15.0, 3.0), 18.0),
    ((5.0, 3.4), (8.5, 4.8), 10.0),
    ((0.5, 4.0), (-2.5, 5.2), -3.0),
    ((-4.0, 3.8), (-10.5, 4.2), -13.0),
)
FAR_OFF = (2.6, -1.2, 3.0)  # hip/knee shift (x, y) and foot shift: far feet fall between the near ones
# glass plates along the back: (dx, half width, height)
PLATES = ((-10.6, 2.4, 2.8), (-5.9, 2.6, 3.6), (-1.1, 2.5, 3.2), (4.0, 1.9, 2.2))
# sand streams peeling off the windward side: anchor (tail joint / back), offset, length, rise, wave
STREAMS = (("p2", -2.0, 0.0, 14.0, 2.5, 1.0), ("root", -2.5, 2.0, 12.0, 1.0, 0.8),
           ("p3", -2.0, -1.0, 11.0, 3.0, 0.8), ("back", 0.0, -1.5, 7.0, 2.0, 0.6))


def _canvas(cv):
    """``with _canvas(cv):`` draws in raw canvas pixels (undoes every active transform)."""
    return cv.xform(np.linalg.inv(cv.M))


def _apply(mats, pt):
    """Map a point through a list of transform matrices (as ``cv.xform(*mats)`` would)."""
    m = np.eye(3)
    for a in mats:
        m = m @ a
    v = m @ np.array([pt[0], pt[1], 1.0])
    return (float(v[0]), float(v[1]))


def _meso_top(C, x):
    cx, cy, rx, ry = MESO
    u = (x - (C[0] + cx)) / rx
    return C[1] + cy - ry * math.sqrt(max(0.0, 1 - u * u))


def _pro_top(C, x):
    cx, cy, rx, ry = PRO
    u = (x - (C[0] + cx)) / rx
    return C[1] + cy - ry * math.sqrt(max(0.0, 1 - u * u))


def _glint(cv, m, n=1):
    """Bright glint pixel(s) at the upper-left of the lit part of mask ``m`` (canvas space)."""
    lit = m & (cv.band == 0)
    if not lit.any():
        lit = m
    ys, xs = np.nonzero(lit)
    if not len(xs):
        return
    order = np.argsort(xs + ys * 1.2, kind="stable")
    g = np.zeros_like(m)
    for k in range(min(n, len(order))):
        g[ys[order[k]], xs[order[k]]] = True
    cv._commit(g, np.where(g, 0, -1).astype(np.int8), GLINT, name="glint")


def _plate(cv, x0, top_fn, w, h, k):
    """One rough shard of desert glass set into the back (shingled over its neighbour)."""
    xl, xr = x0 - w, x0 + w
    yl, yr = top_fn(xl), top_fn(xr)
    j = px.hash01("plate", k) - 0.5
    pts = [(xl, yl + 1.6), (xl + 0.2, yl - h * 0.55), (x0 - 0.3 + j * 0.8, min(yl, yr) - h),
           (xr - 0.3, yr - h * 0.45 + j * 0.6), (xr, yr + 1.6)]
    m = cv.polygon(pts, GLASS, name="glass", sep="deep")
    _glint(cv, m, 2 if w > 2.1 else 1)


def _body(cv, C, p):
    br = p.breathe
    mcx, mcy, mrx, mry = MESO
    pcx, pcy, prx, pry = PRO
    meso = cv.geom_ellipse(C[0] + mcx, C[1] + mcy - br * 0.5, mrx, mry + br * 0.5)
    pro = cv.geom_ellipse(C[0] + pcx, C[1] + pcy, prx, pry)
    cv.draw_geom(cv.union(meso, pro, weights=[1.0, 0.95]), SAND, name="body", sep="deep")
    # bone-pale sternites along the underside
    cv.limb([(C[0] - 12.0, C[1] + 3.0), (C[0] - 3.0, C[1] + 4.4), (C[0] + 9.0, C[1] + 4.2)], [1.2, 1.7, 1.3],
            BELLY, shade="two", clip="body", name="body")
    # tergite seams under the plates
    for sx in (-8.2, -3.5):
        top = _meso_top(C, C[0] + sx)
        cv.limb([(C[0] + sx, top + 2.0), (C[0] + sx - 0.4, C[1] + 1.0), (C[0] + sx + 0.1, C[1] + 3.2)], 0.5,
                SEAM, decal=True, clip="body")
    # amber glass plates shingled along the back, rear first
    for k, (dx, w, h) in enumerate(PLATES):
        fn = (lambda x: _meso_top(C, x)) if dx < 3.5 else (lambda x: _pro_top(C, x))
        _plate(cv, C[0] + dx, fn, w, h, k)
    # eye: median eyes on the head ridge (stamped in canvas pixels so it never loses a pixel)
    q = cv.tp((C[0] + 9.9, C[1] + 0.4))
    ex, ey = math.floor(q[0]) - 1, math.floor(q[1]) - 1
    with _canvas(cv):
        if p.eye == "squeeze":
            cv.stamp(["k.", ".k", "k."], ex, ey - 1, {"k": INK}, name="eye")
        elif p.eye == "dead":
            cv.stamp(["k.k", ".k.", "k.k"], ex - 1, ey - 1, {"k": INK}, name="eye")
        else:
            cv.stamp(["gk", "kk"], ex, ey, {"k": INK, "g": GLINT}, name="eye")
            if p.eye == "angry":
                cv.pixels([(ex - 1, ey - 1), (ex, ey - 1), (ex + 1, ey)], INK, name="brow")


def _cracks(cv, C, amount):
    """Dark fractures across the carapace, pale sand showing along their lower edge."""
    if amount <= 0:
        return
    lines = (((-9.0, -5.0), (-7.5, -2.0), (-9.0, 0.5), (-7.0, 3.0)),
             ((-1.0, -6.0), (-2.5, -2.5), (-0.5, 0.0), (-2.0, 3.5)),
             ((7.0, -3.5), (5.5, -1.0), (7.5, 1.5)),
             ((-5.0, -6.5), (-4.0, -4.0), (-5.5, -1.5)))
    n = 2 if amount < 0.6 else 4
    for pts in lines[:n]:
        pts = [(math.floor(C[0] + x), math.floor(C[1] + y)) for x, y in pts]
        for a, b in zip(pts, pts[1:]):
            cv.line((a[0] + 1, a[1]), (b[0] + 1, b[1]), CRACK_LIT, decal=True, clip=["body", "glass", "glint"])
            cv.line(a, b, CRACK, decal=True, clip=["body", "glass", "glint"])


def _leg(cv, C, B, x0, ground, i, p, far):
    (hx, hy), (kx, ky), fdx = NEAR_LEGS[i]
    if far:
        hx, hy, kx, ky, fdx = hx + FAR_OFF[0], hy + FAR_OFF[1], kx + FAR_OFF[0], ky + FAR_OFF[1], fdx + FAR_OFF[2]
    j = i + (4 if far else 0)
    if p.flip:  # on its back (local frame is mirrored): legs point up and curl in
        c = p.curl
        hip = (C[0] + hx, C[1] + hy)
        knee = (C[0] + kx * (1 - 0.2 * c), C[1] + ky + 2.0 - c * 1.0)
        foot = (C[0] + (kx + (fdx - kx) * 0.5) * (1 - 0.6 * c), C[1] + 11.5 - c * 5.0)
        if p.flail:
            knee = (C[0] + kx * 1.1, C[1] + ky + 1.0)
            foot = (C[0] + fdx * (1.05 + 0.1 * (i % 2)), C[1] + 8.0 + 2.0 * ((i + j) % 3))
    else:
        lift, slide = p.lift[j], p.slide[j]
        hip = B((C[0] + hx, C[1] + hy))
        knee = B((C[0] + kx + slide * 0.5 / K, C[1] + ky - lift * 0.6 / K + p.knees * 0.4))
        foot = (x0 + fdx + (slide + p.fx) / K, ground - lift / K)
    shade = "dark" if far else "soft"
    name = f"leg{j}"
    cv.limb([hip, knee, foot], [1.3, 1.15, 0.55], LEG, shade=shade, name=name, sep=False if far else "deep")
    # dark umber knee + tarsus
    cv.circle(knee[0], knee[1], 0.9, UMBER, decal=True, clip=name)
    cv.limb([px.lerp_pt(knee, foot, 0.72), foot], [0.8, 0.55], UMBER, decal=True, clip=name)


def _claw(cv, sh, hand, ang, opening, far):
    """Heavy pincer: 2-bone arm with an umber elbow, bulbous hand, a fixed finger in line with
    the palm and a movable finger hinging open on top, both umber-tipped.  Returns the tips."""
    arm_shade = "dark" if far else "two"
    shade = "nolight" if far else "full"
    tag = "f" if far else "n"
    s = 0.86 if far else 1.0
    wrist = px.polar(hand, ang + 180, 4.4 * s)
    elbow = px.ik2(sh, wrist, 4.2, 4.0, bend=1)
    cv.limb([sh, elbow, wrist], [1.5 * s, 1.35 * s, 1.5 * s], LEG, shade=arm_shade, name=f"arm{tag}",
            sep=False if far else "deep")
    cv.circle(elbow[0], elbow[1], 1.15, UMBER, decal=True, clip=f"arm{tag}")
    cv.ellipse(hand[0], hand[1], 5.0 * s, 3.6 * s, SAND, angle=ang, shade=shade, name=f"hand{tag}", sep="deep")
    front = px.polar(hand, ang, 3.4 * s)
    tips = []
    # movable finger (top) hinges open; the fixed finger (bottom) stays in line with the palm
    for sgn, ln, r0, a in ((1, 6.2, 1.45, ang + 4 + 46 * opening), (-1, 5.6, 1.6, ang - 3 - 4 * opening)):
        root = px.polar(front, ang + 90 * sgn, 1.7 * s)
        mid = px.polar(root, a, ln * 0.55 * s)
        tip = px.polar(mid, a - sgn * (32 + 12 * (1 - opening)), ln * 0.5 * s)
        cv.limb([root, mid, tip], [r0 * s, r0 * 0.72 * s, 0.5], SAND, shade=shade, name=f"finger{tag}",
                sep="deep")
        cv.limb([px.lerp_pt(mid, tip, 0.1), tip], [r0 * 0.75 * s, 0.5], UMBER, decal=True, clip=f"finger{tag}")
        tips.append(tip)
    return tips


def _tail(cv, root, angs, glow):
    """Five sand-gold segments from ``root`` along canvas angles ``angs[:5]``, then the venom
    telson pointing along ``angs[5]`` with a dark barb.  Returns (bulb centre, barb tip)."""
    pts = [root]
    q = root
    for a in angs[:5]:
        q = px.polar(q, a, SEG_L)
        pts.append(q)
    for i in range(5):
        r = TAIL_R[i]
        cv.limb([pts[i], pts[i + 1]], [r, r * 0.94], SAND, name="tail", sep="deep")
    ta = angs[5]
    bulb = px.polar(pts[5], ta, 2.4)
    mat = VENOM_HOT if glow >= 3 else VENOM
    cv.ellipse(bulb[0], bulb[1], 3.3, 2.7, mat, angle=ta, shade="soft" if glow >= 2 else "full", name="telson",
               sep="deep")
    b0 = px.polar(bulb, ta, 2.4)
    b1 = px.polar(b0, ta - 22, 2.3)
    b2 = px.polar(b1, ta - 62, 1.8)
    cv.limb([b0, b1, b2], [1.15, 0.75, 0.45], UMBER, shade="two", name="barb")
    return bulb, px.polar(b1, ta, 1.8), pts


def _streams(fx, anchors, phase, n):
    """Loose sand streaming off the tail and back: dashed 1 px trails drifting away to the left.
    ``anchors`` are canvas points; draw inside ``_canvas``."""
    for s, (key, sx, sy, ln, rise, amp) in enumerate(STREAMS[:n]):
        ax, ay = anchors[key]
        sx, sy, ln, rise = sx * K, sy * K, ln * K, rise * K
        runs, run = [], []
        for i in range(int(ln) + 1):
            u = i / ln
            x = ax + sx - i
            y = ay + sy - u * rise + amp * math.sin(u * 4.2 + s * 1.7)
            v = (i / 5.0 - phase + 0.37 * s) % 1.0
            if v < 0.6:
                col = GRAIN.light if v < 0.2 else (GRAIN.base if u < 0.65 else GRAIN.shadow)
                run.append((math.floor(x), math.floor(y), col))
            elif run:
                runs.append(run)
                run = []
        if run:
            runs.append(run)
        for run in runs:
            if len(run) < 2:  # a lone grain would be a stray pixel
                continue
            for (gx, gy, col) in run:
                fx.pixel(gx, gy, col, name="sand")


def _glow(fx, bulb, level):
    """Venom light around the telson (behind the body); ``bulb`` in canvas px, draw in ``_canvas``."""
    if level <= 0:
        return
    cx, cy = bulb
    r = K * (4.6 + 0.6 * level)
    rays = ((90, r), (0, r), (180, r), (270, r))
    if level >= 2:
        rays += ((45, r - 0.8), (135, r - 0.8), (225, r - 0.8), (315, r - 0.8))
    for a, d in rays:
        p0 = px.polar((cx, cy), a, d - 1.0)
        p1 = px.polar((cx, cy), a, d + (0.8 if level >= 2 else 0.0))
        fx.line((math.floor(p0[0]), math.floor(p0[1])), (math.floor(p1[0]), math.floor(p1[1])), VENOM.base,
                name="glow")
    if level >= 3:
        px.glow_ring(fx, cx, cy, r - 1.2, VENOM.shadow)


def _burst(cv, fx, top, tip, t):
    """Sand exploding off the stinger tip (canvas px) on the stab: lumpy puffs thrown forward
    (outlined layer ``fx``) and loose grains flying out (unoutlined layer ``top``)."""
    grow = 0.9 + 0.8 * t
    puffs = ((2.2, -2.6, 2.0), (4.2, 0.6, 1.8), (1.2, 2.6, 1.5), (-0.8, -3.6, 1.4), (6.2, -2.4, 1.2))
    with _canvas(cv):
        for k, (dx, dy, r) in enumerate(puffs):
            if t > 0.5 and k >= 3:
                continue
            rr = max(1.1, r * K * (1.0 - 0.3 * t))
            fx.circle(tip[0] + dx * grow * K, tip[1] + dy * grow * K, rr, GRAIN, shade="soft", name="burst")
        hc.sparks(top, tip[0] + 1.0, tip[1], 0.35 + 0.6 * t, n=5, radius=8.0, colors=(GRAIN.light, GRAIN.base),
                  seed=11, spread=150, aim=15)


def _chips(cv, fx, C, t):
    """Amber glass chips knocked off the back (stamped in canvas pixels)."""
    for k, (sx, sy, vx, vy) in enumerate(((-3.0, -9.5, -6.0, -8.0), (1.5, -9.0, -0.5, -10.0),
                                          (-8.0, -8.0, -9.0, -4.0), (-5.5, -9.0, -3.0, -12.0))):
        x, y = cv.tp((C[0] + sx + vx * t, C[1] + sy + vy * t + 7.0 * t * t))
        rows = (["gl.", "lls", ".s."], ["gl", "ls", "s."], [".gl", "lls"], ["g.", "ls"])[k]
        with _canvas(cv):
            fx.stamp(rows, math.floor(x), math.floor(y), {"g": GLINT, "l": (GLASS, 0), "s": (GLASS, 2)},
                     name="chip")


def _spill(cv, fx, C, t, base_y):
    """Sand poured out of the cracked carapace into small heaps; ``base_y`` is the canvas row the
    heaps rest on."""
    for k, (dx, w, t0) in enumerate(((-12.5, 6.0, 0.0), (10.0, 4.6, 0.2), (-1.0, 4.0, 0.55))):
        if t < t0:
            continue
        s = min(1.0, (t - t0) / (1.0 - t0))
        rx = max(2.0, K * w * (0.55 + 0.45 * s))
        ry = max(1.3, K * (1.3 + 1.6 * s))
        x = cv.tp((C[0] + dx, C[1]))[0]
        with _canvas(cv):
            fx.ellipse(x, base_y - ry + 0.5, rx, ry, GRAIN, shade="soft", name="heap")


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    back = cv.layer(above=False, outline=False)
    with cv.xform(px.scale(K, K, (cv.gx, cv.gy))):
        _draw(cv, back, p)


def _draw(cv, back, p):
    """The whole scorpion in rig space (scaled by K about the anchor)."""
    ground = cv.gy - 1.5 / K  # rig y that lands on the centre of the last foot row
    x0 = cv.gx - 3
    C = (x0 + p.bx / K, ground - 11.0 + p.by / K)
    pivot = (C[0] + (12.0 if p.pitch < 0 else -12.0), ground)

    def B(pt):
        return px.rot_pt(pt, p.pitch, pivot)

    xf = [px.rotate(p.pitch, pivot)]
    if p.flip:
        C = (x0 + p.bx / K, ground - 8.0)
        xf = [px.flip_y(C[1])]
        cv.snap_ground = True

    # far side: legs, then the far pincer
    if p.flip:
        with cv.xform(*xf):
            for i in (3, 2, 1, 0):
                _leg(cv, C, lambda q: q, x0, ground, i, p, far=True)
    else:
        for i in (3, 2, 1, 0):
            _leg(cv, C, B, x0, ground, i, p, far=True)
    with cv.xform(*xf):
        dx, dy, ang, op = p.fc
        _claw(cv, (C[0] + 13.0, C[1] - 0.8), (C[0] + 21.5 + dx, C[1] - 7.0 + dy), ang, op, far=True)
        _body(cv, C, p)
        _cracks(cv, C, p.crack)
    root = _apply(xf, (C[0] + TAIL_ROOT[0], C[1] + TAIL_ROOT[1]))
    if p.dtail is not None:
        angs = p.dtail
    else:
        angs = [a + p.pitch + p.sway * (k + 1) / 5.0 for k, a in enumerate(p.tail[:5])] + [p.tail[5] + p.pitch + p.sway]
    bulb, barb, tpts = _tail(cv, root, angs, p.glow)
    if p.flip:
        with cv.xform(*xf):
            for i in (3, 2, 1, 0):
                _leg(cv, C, lambda q: q, x0, ground, i, p, far=False)
    else:
        for i in (3, 2, 1, 0):
            _leg(cv, C, B, x0, ground, i, p, far=False)
    with cv.xform(*xf):
        dx, dy, ang, op = p.nc
        _claw(cv, (C[0] + 13.5, C[1] + 1.5), (C[0] + 24.5 + dx, C[1] + 0.0 + dy), ang, op, far=False)

    # FX in canvas pixels
    bulb_c, barb_c = cv.tp(bulb), cv.tp(barb)
    if p.grains is not None:
        anchors = {"root": cv.tp(tpts[0]), "p2": cv.tp(tpts[2]), "p3": cv.tp(tpts[3]),
                   "back": cv.tp(B((C[0] - 5.0, C[1] - 6.0)))}
        with _canvas(cv):
            _streams(back, anchors, p.grains, p.gust)
    with _canvas(cv):
        _glow(back, bulb_c, p.glow)
    if p.burst is not None:
        fx = cv.layer(above=True, outline=True)
        top = cv.layer(above=True, outline=False)
        _burst(cv, fx, top, (barb_c[0] + 1.0, barb_c[1]), p.burst)
        if p.hit:
            with _canvas(cv):
                px.impact(top, barb_c[0] + 1.0, barb_c[1], size=3, color=VENOM.base, core=px.GLINT)
    if p.chips is not None:
        _chips(cv, cv.layer(above=True, outline=True), C, p.chips)
    if p.spill is not None:
        off = hc.snap_offset(cv)
        _spill(cv, cv.layer(above=True, outline=True), C, p.spill, cv.gy - 2 - off)
