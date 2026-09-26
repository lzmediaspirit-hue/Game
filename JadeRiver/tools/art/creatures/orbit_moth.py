"""Orbit moth - a large soft moth whose wings are a map of the night sky (Star/Wind).

View: from above and a little to the side, head to the right, wings spread up (far pair)
and down (near pair, a touch larger) like a pinned specimen come alive.  ~40 art px from
wing tip to wing tip, ~27 px from the tail to the antenna tips, on a 64 px art canvas
(cell 128).  Flying: anchored at the thorax.  Also a tameable pet, so it stays round and soft.
Parts, back to front: the motes on the far side of their orbit, far hindwing and forewing,
near hindwing and forewing (dusky indigo, a dusky-rose fringe along the outer margin, a pale
leading edge, and a star chart: pale-gold stars joined by thin gold lines, one bright
four-point star on each wing), far feathered antenna, the fuzzy pale body (scalloped fur
collar, banded abdomen, round head) with one big dark eye, near antenna, the motes on the
near side of their orbit.  Three tiny teal-white motes circle it all the time.
Idle: a slow flutter (the wings foreshorten as they beat), the motes orbit.  Walk: a
quicker, deeper beat, nosing forward.  Windup: the wings lift and spread wide, the moth
rears back and the motes gather into a glowing knot in front of its head (held).  Attack:
the wings snap down and a burst of glittering star dust sprays forward (frame 1).  Hurt:
the wings flinch and puff dust.  Death: the wings fold, it spirals down, the motes wink
out one by one, and it fades.
"""
import math

import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "orbit_moth",
    "cell": 128,
    "anchor": [64, 64],
    "flying": True,
    "hit_frame": 1,
}

# ---- palette: dusky indigo wings, pale gold star chart, cream fur, teal-white motes -------------
WING = px.material("om_wing", "#7d77cf", "#4b4598", "#342f74", "#231f54", outline="#0b0920",
                   thresholds=(0.93, 0.62, 0.2))
FRINGE = px.material("om_fringe", "#c9a0dc", "#9a70bf", "#744f9c", "#533975", outline="#140b22")
FUR = px.material("om_fur", "#fffaf0", "#ece2cf", "#c3b4bc", "#8f809e", outline="#1b1426",
                  thresholds=(0.88, 0.55, 0.2))
ANT = px.material("om_antenna", "#fff3c8", "#e6cc88", "#b8955a", "#7d6040", outline="#21170e")
LINE = px.rgb("#bc9f62")
GOLD = px.rgb("#ffe6a1")
WHITE = px.rgb("#fffbe6")
EYE = px.rgb("#120c22")
MOTE_CORE = px.rgb("#fffbe6")
MOTE_ARM = px.rgb("#8ff2e2")
MOTE_DIM = px.rgb("#4fa8a8")
GLITTER = (px.rgb("#fffbe6"), px.rgb("#ffe6a1"), px.rgb("#8ff2e2"), px.rgb("#f2a2e0"))
PUFF = px.material("om_puff", "#fbf4ff", "#ddd0ee", "#b2a2cf", "#8977ad", outline="#3a2c55")

# ---- wing geometry: upper (far) wings, local to the wing root; the lower pair mirrors y ---------
FORE = [(3.0, -1.0), (4.6, -7.5), (4.4, -13.5), (2.6, -18.0), (0.0, -19.6), (-2.8, -18.8), (-6.2, -15.0),
        (-9.2, -10.6), (-10.6, -7.0), (-6.0, -3.6), (-2.0, -1.0)]
FORE_MARGIN = (3, 4, 5, 6, 7, 8)  # vertex indices of the outer margin
FORE_COSTA = (1, 2, 3)
HIND = [(-2.0, -1.0), (-6.0, -3.8), (-10.6, -6.8), (-14.0, -9.4), (-15.8, -8.4), (-16.0, -5.4), (-14.2, -2.4),
        (-10.0, -0.4)]
HIND_MARGIN = (2, 3, 4, 5, 6)
# star chart on the forewing: stars (x, y, kind) and the lines joining them
STARS = [(-0.5, -15.5, "big"), (-4.5, -11.2, "dot"), (-1.2, -7.2, "dot"), (-7.2, -7.8, "dot")]
LINKS = [(0, 1), (1, 2), (1, 3)]
HSTAR = (-12.2, -5.6)

# ---- poses ------------------------------------------------------------------------------------
# bx, by   body offset          tilt   body pitch (deg, + = nose up)
# s        wing span scale (1 = spread flat to the camera, lower = foreshortened mid-beat)
# sweep    wings swept forward (deg)     ph   mote orbit phase (deg)      motes  how many still lit
# gather   0..1 the motes pull into a knot in front of the head          eye  open|angry|squeeze|closed
# burst    glitter life (None = off)     puff  dust puffs (hurt)   fold  0..1 wings folding (death)
DEFAULTS = dict(bx=0, by=0, tilt=0, s=1.0, sweep=0, ph=0.0, motes=3, gather=0.0, eye="open", burst=None,
                puff=False, fold=0.0, fade=1.0, knot=0)

POSE = px.poses(DEFAULTS, {
    "idle": [  # slow flutter, motes orbit 30 deg a frame (120 deg apart -> loops in 4)
        dict(s=1.0, by=0, ph=0),
        dict(s=0.88, by=-1, ph=30),
        dict(s=0.74, by=-1, ph=60),
        dict(s=0.88, by=0, ph=90),
    ],
    "walk": [  # quicker, deeper beat, nosing forward
        dict(s=1.0, tilt=-6, by=1, ph=0),
        dict(s=0.72, tilt=-6, by=0, ph=20),
        dict(s=0.46, tilt=-7, by=-1, ph=40, bx=1),
        dict(s=0.58, tilt=-7, by=-1, ph=60, bx=1),
        dict(s=0.8, tilt=-6, by=0, ph=80),
        dict(s=0.95, tilt=-6, by=1, ph=100),
    ],
    "windup": [  # wings lift and spread wide, rears back, motes gather in front - held
        dict(s=1.06, sweep=6, tilt=6, bx=-1, by=-1, ph=20, gather=0.45, eye="angry"),
        dict(s=1.12, sweep=12, tilt=10, bx=-2, by=-1, ph=35, gather=0.85, eye="angry", knot=1),
        dict(s=1.14, sweep=14, tilt=12, bx=-3, by=-2, ph=45, gather=1.0, eye="angry", knot=2),
    ],
    "attack": [  # wings snap down, a burst of glittering dust sprays forward on frame 1
        dict(s=0.8, sweep=-4, tilt=-4, bx=1, ph=50, gather=1.0, eye="angry", burst=0.15, knot=2),
        dict(s=0.6, sweep=-10, tilt=-8, bx=3, by=1, ph=55, gather=0.6, eye="angry", burst=0.5),
        dict(s=0.72, sweep=-4, tilt=-4, bx=2, ph=70, gather=0.25, burst=0.85),
        dict(s=0.92, bx=1, ph=90),
    ],
    "hurt": [  # wings flinch, dust puffs off them
        dict(s=0.5, sweep=-10, tilt=14, bx=-3, by=-1, ph=10, eye="squeeze", puff=True),
        dict(s=0.7, sweep=-5, tilt=8, bx=-2, ph=20, eye="squeeze"),
    ],
    "death": [  # wings fold, it spirals down, the motes wink out one by one, fades
        dict(s=0.5, sweep=-10, tilt=14, bx=-3, by=-1, ph=10, eye="squeeze", puff=True, motes=2),
        dict(s=0.8, tilt=-25, bx=-1, by=3, ph=30, eye="closed", fold=0.45, motes=1),
        dict(s=0.72, tilt=-70, bx=1, by=6, ph=50, eye="closed", fold=0.8, motes=0),
        dict(s=0.66, tilt=-125, bx=-1, by=9, ph=70, eye="closed", fold=1.0, motes=0, fade=0.6),
        dict(s=0.62, tilt=-175, bx=-2, by=11, ph=90, eye="closed", fold=1.0, motes=0, fade=0.3),
    ],
})


def _wing_pts(pts, p, lower, big=1.0):
    """Local wing outline -> scaled (span ``s``), swept, folded and mirrored for the lower pair."""
    out = []
    for (x, y) in pts:
        y = y * p.s * big
        x = x * big
        x, y = px.rot_pt((x, y), -p.sweep + 72 * p.fold, (0.0, 0.0))  # forward sweep; folding sweeps back
        out.append((x, -y if lower else y))
    return out


def _wing(cv, R, p, lower):
    """One wing pair (hind then fore) rooted at R, with fringe, costa and star chart."""
    big = 1.06 if lower else 1.0
    shade = "soft" if lower else "two"
    tag = "lo" if lower else "up"
    hind = [(R[0] + x, R[1] + y) for x, y in _wing_pts(HIND, p, lower, big)]
    fore = [(R[0] + x, R[1] + y) for x, y in _wing_pts(FORE, p, lower, big)]
    cv.polygon(hind, WING, shade=shade if lower else "nolight", bulge=0.7, name=f"hind_{tag}")
    cv.limb([hind[i] for i in HIND_MARGIN], 0.9, FRINGE, shade="two", decal=True, clip=f"hind_{tag}",
            name=f"hind_{tag}")
    hs = [(R[0] + x, R[1] + y) for x, y in _wing_pts([HSTAR], p, lower, big)][0]
    _star(cv, hs, "plus" if p.s > 0.6 else "dot", f"hind_{tag}")
    cv.polygon(fore, WING, shade=shade, bulge=0.7, name=f"fore_{tag}", sep="deep")
    cv.limb([fore[i] for i in FORE_MARGIN], 1.0, FRINGE, shade="two", decal=True, clip=f"fore_{tag}",
            name=f"fore_{tag}")
    cv.limb([fore[i] for i in FORE_COSTA], 0.6, WING.step(-1), shade="flat", decal=True, clip=f"fore_{tag}",
            name=f"fore_{tag}")
    stars = [(R[0] + x, R[1] + y) for x, y in _wing_pts([(a, b) for a, b, _ in STARS], p, lower, big)]
    if p.s > 0.5:
        for i, j in LINKS:
            a, b = stars[i], stars[j]
            cv.line((math.floor(a[0]), math.floor(a[1])), (math.floor(b[0]), math.floor(b[1])), LINE, decal=True,
                    clip=f"fore_{tag}", name=f"fore_{tag}")
    for (x, y), (_, _, kind) in zip(stars, STARS):
        _star(cv, (x, y), ("plus" if p.s > 0.6 else "dot") if kind == "big" else "dot", f"fore_{tag}")


def _star(cv, q, kind, clip):
    x, y = math.floor(q[0]), math.floor(q[1])
    if kind == "plus":
        cv.pixels([(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)], GOLD, decal=True, clip=clip, name=clip)
        cv.pixel(x, y, WHITE, decal=True, clip=clip, name=clip)
    else:
        cv.pixel(x, y, GOLD, decal=True, clip=clip, name=clip)


def _antenna(cv, root, bend, far):
    """Feathered (comb) antenna: a curved leaf-shaped frond with a darker shaft.  ``bend``
    rotates the whole frond (deg, + = further up/back)."""
    shape = [(0.0, 0.0), (1.2, -2.8), (3.2, -5.2), (5.8, -6.6)] if not far else \
            [(0.0, 0.0), (0.4, -3.0), (0.6, -6.0), (-0.6, -8.4)]
    pts = [px.rot_pt((root[0] + x, root[1] + y), bend, root) for x, y in shape]
    name = "ant_far" if far else "ant"
    cv.limb(pts, [0.5, 1.35, 1.2, 0.5], ANT, shade="dark" if far else "two", name=name)
    for a, b in zip(pts, pts[1:]):
        cv.line((math.floor(a[0]), math.floor(a[1])), (math.floor(b[0]), math.floor(b[1])),
                ANT.deep if far else ANT.shadow, decal=True, clip=name, name=name)


def _body(cv, C, p):
    x, y = C
    # plump banded abdomen + fluffy thorax as one soft form
    abd = cv.geom_limb([(x - 1.0, y + 0.3), (x - 5.0, y + 0.7), (x - 9.0, y + 1.0), (x - 11.0, y + 1.1)],
                       [3.9, 3.6, 2.3, 1.0])
    thor = cv.geom_ellipse(x + 1.0, y - 0.2, 4.8, 4.6)
    head = cv.geom_ellipse(x + 6.8, y + 0.8, 3.5, 3.3)
    tufts = [cv.geom_ellipse(x + 1.0 + 4.3 * math.cos(a), y - 0.2 - 4.1 * math.sin(a), 1.6, 1.6)
             for a in (math.radians(d) for d in (75, 120, 165, 210, 255))]
    cv.draw_geom(cv.union(abd, thor, head, *tufts, weights=[0.8, 1.0, 1.05] + [0.7] * 5), FUR, name="body")
    for dx in (-4.5, -7.5):  # abdomen bands
        cv.line((math.floor(x + dx), math.floor(y - 2)), (math.floor(x + dx), math.floor(y + 3)), FUR.shadow,
                band=None, decal=True, clip="body", name="body")
    # the fur ruff between thorax and head, one big dark eye with a glint
    cv.limb([(x + 3.6, y - 3.0), (x + 3.2, y + 0.5), (x + 3.8, y + 3.6)], 0.6, FUR.shadow, shade="flat",
            decal=True, clip="body", name="body")
    ex, ey = math.floor(x + 6.2), math.floor(y)
    if p.eye == "squeeze":
        hc.eye_stamp(cv, ["k..", ".kk", "k.."], ex, ey, {"k": EYE})
    elif p.eye == "closed":
        hc.eye_stamp(cv, ["...", "kkk", ".k."], ex, ey, {"k": EYE})
    else:
        hc.eye_stamp(cv, ["gkk", "kkk", ".kk"] if p.eye == "open" else ["kkk", "gkk", ".kk"], ex, ey,
                     {"k": EYE, "g": px.GLINT})
        if p.eye == "angry":  # a determined little brow
            cv.pixels([(ex - 1, ey - 1), (ex, ey - 1), (ex + 1, ey)], EYE, name="eye")


def _mote_positions(C, p):
    """Orbit (tilted ellipse around the body) blended toward a knot in front of the head."""
    K = (C[0] + 14.0, C[1] + 0.5)
    out = []
    for i in range(3):
        th = math.radians(p.ph + i * 120.0)
        q = (C[0] - 1.0 + 19.0 * math.cos(th), C[1] + 6.5 * math.sin(th))
        q = px.rot_pt(q, 16, C)
        kq = px.polar(K, 90 + i * 120 + p.ph * 2, 2.2)
        g = p.gather
        q = (q[0] + (kq[0] - q[0]) * g, q[1] + (kq[1] - q[1]) * g)
        depth = math.sin(th) if g < 0.5 else 1.0
        out.append((q, depth, i))
    return out, K


def _mote(fx, q, lit=True):
    x, y = math.floor(q[0]), math.floor(q[1])
    fx.pixels([(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)], MOTE_ARM if lit else MOTE_DIM, name="mote")
    fx.pixel(x, y, MOTE_CORE, name="mote")


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    C = (cv.gx + 0.5 + p.bx, cv.gy + 0.5 + p.by)
    back = cv.layer(above=False, outline=False)
    front = cv.layer(above=True, outline=False)
    motes, K = _mote_positions(C, p)
    for (q, depth, i) in motes:
        if i < p.motes and depth < 0:
            _mote(back, q)
    with cv.xform(px.rotate(p.tilt, C)):
        R = (C[0] + 0.5, C[1])
        _wing(cv, R, p, lower=False)
        _wing(cv, R, p, lower=True)
        _antenna(cv, (C[0] + 5.5, C[1] - 2.0), 8 * p.fold, far=True)
        _body(cv, C, p)
        _antenna(cv, (C[0] + 7.0, C[1] - 1.8), 30 * p.fold, far=False)
    for (q, depth, i) in motes:
        if i < p.motes and depth >= 0:
            _mote(front, q)
    if action == "death" and 1 <= frame <= 2:  # the mote that just went out leaves a tiny spark
        q = motes[p.motes][0]
        x, y = math.floor(q[0]), math.floor(q[1])
        front.pixels([(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1), (x, y)], MOTE_DIM, name="wink")
    if p.knot:  # the gathered motes glow as a knot in front of the head
        px.glow_ring(back, K[0], K[1], 2.6 + p.knot, MOTE_DIM, thickness=1.0)
        if p.knot >= 2:
            px.glow_ring(back, K[0], K[1], 1.2, MOTE_ARM, thickness=1.0)
    if p.burst is not None:
        _burst(front, cv.layer(above=True, outline=True), (C[0] + 9.0, C[1] + 0.5), p.burst)
    if p.puff:  # wing dust shaken loose: a few small puffs and specks
        lay = cv.layer(above=True, outline=True)
        for (dx, dy, r) in ((-6.0, -15.0, 1.4), (-9.0, 13.0, 1.3)):
            lay.circle(C[0] + dx, C[1] + dy, r, PUFF, shade="soft", name="puff")
        for (dx, dy) in ((-2.0, -19.0), (-12.0, -11.0), (-4.0, 17.0), (-13.0, 9.0), (3.0, -17.0)):
            front.pixels([(math.floor(C[0] + dx), math.floor(C[1] + dy)), (math.floor(C[0] + dx) - 1,
                          math.floor(C[1] + dy))], PUFF.light, name="speck")


def _burst(fx, puffs, E, t):
    """A cone of glittering star dust sprayed forward from the head."""
    n = 14
    for i in range(n):
        h = px.hash01("om", i)
        a = -30 + 60 * (i + 0.5) / n + (h - 0.5) * 8
        r = (6 + 17 * t) * (0.5 + 0.65 * px.hash01("omr", i))
        q = px.polar(E, a, r)
        x, y = math.floor(q[0]), math.floor(q[1])
        if x > fx.w - 6:
            continue
        col = GLITTER[i % 4]
        if i % 2 == 0 and t < 0.8:  # four-point glints
            fx.pixels([(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)], GLITTER[(i + 1) % 4], name="glitter")
            fx.pixel(x, y, GLITTER[0], name="glitter")
        else:
            fx.pixels([(x, y), (x + 1, y)], col, name="glitter")
    if t < 0.7:  # the bright core of the spray
        c = px.polar(E, 0, 3 + 12 * t)
        px.impact(fx, c[0], c[1], size=3 if t < 0.3 else 5, color=GLITTER[1], core=GLITTER[0])
    if t < 0.7:  # a wavefront of light racing ahead of the spray
        hc.arc_line(fx, (E[0] - 2, E[1]), 5 + 11 * t, -60, 60, GLITTER[2], name="glitter")
        hc.arc_line(fx, (E[0] - 2, E[1]), 3 + 11 * t, -45, 45, GLITTER[3], name="glitter")
