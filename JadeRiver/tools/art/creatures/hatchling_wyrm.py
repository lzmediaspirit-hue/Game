"""Hatchling wyrm - a young star wyrm, the player's Primordial Beast companion (Star/Space).

View: side, facing right, walking (not flying: its wings are still stubs).  ~34 art px from
the tail star to the snout, ~27 px tall to the horn tips, on a 64 px art canvas (cell 128).
A baby dragonet: big round head, long curved neck, a plump bean body on four stubby legs,
a tail that curls up and ends in a small glowing star.  Endearing and noble.
Parts, back to front: far legs, far wing stub, tail (with the tail star), body + neck as one
pearl form (soft blue-violet underbelly and throat with belly-plate lines, pale-gold nubs
along the spine), near legs (gold claws), near wing stub (gold finger spars, indigo membrane
with star specks), far horn, head (round cranium + short snout, gold forehead star, big
star-blue eye with a glint, swept-back gold horns).
Idle: looks up and around while breathing, the tail star twinkles.  Walk: a waddle-trot on
diagonal leg pairs with a bobbing head and a swaying tail.  Windup: puffs itself up, rears
its head back, flares its wing stubs and its chest glows pale gold (held).  Attack: a small
burst of star-breath out of its open jaws on frame 1.  Hurt: a squeak-flinch - eyes
squeezed, head thrown back, a couple of squeak marks.  Death (knocked out): it sinks, curls
up with its tail wrapped round and its head down, eyes closed, and its lights dim.
"""
import math

import pixel as px

SPEC = {
    "id": "hatchling_wyrm",
    "cell": 128,
    "anchor": [64, 112],
    "flying": False,
    "hit_frame": 1,
}

# ---- palette: pearl scales, pale gold horns/claws/spars, blue-violet belly, starry membrane ----
PEARL = px.material("hw_pearl", "#fffdf6", "#efe8de", "#cbc1da", "#9b90ba", outline="#1c1730",
                    thresholds=(0.88, 0.5, 0.16))
PEARL_D = px.material("hw_pearl_dim", "#e4dfe0", "#cdc6cf", "#a79ebd", "#7f75a0", outline="#1c1730",
                      thresholds=(0.88, 0.5, 0.16))
GOLD = px.material("hw_gold", "#fff3c2", "#f2cd6e", "#c6923f", "#8a5a35", outline="#24160c")
BELLY = px.material("hw_belly", "#dedcfb", "#b0acf0", "#8782d4", "#605aa8", outline="#161234")
MEMB = px.material("hw_membrane", "#6f6ecf", "#4644a0", "#312e7a", "#211f56", outline="#0b0a22")
MOUTH = px.material("hw_mouth", "#b06a86", "#8a4a6a", "#643552", "#43233b", outline="#1a0c16")
INK = px.rgb("#161230")
IRIS = px.rgb("#4cc8f4")
IRIS_HI = px.rgb("#b8f0ff")
STAR_W = px.rgb("#fffbe6")
STAR_G = px.rgb("#ffe07a")
STAR_DIM = px.rgb("#b8a978")
GLOW = px.rgb("#fff1b0")
GLOW_EDGE = px.rgb("#f2cd6e")
SQUEAK = px.rgb("#fffbe6")

# ---- poses ------------------------------------------------------------------------------------
# bx, by    body offset       crouch  lower the body (px)       tilt  body roll (deg)
# neck      neck angle (deg, 90 = straight up)    head  head tilt (deg, + = chin up)
# jaw       0..1 mouth open   eye  open|angry|squeeze|closed    look  glint shift (dx)
# feet      (dx, lift) near-front, far-front, near-hind, far-hind
# tail      tail sway (deg)   star  twinkle: 0 plus, 1 cross, 2 big, 3 small, -1 dim, -2 out
# wing      0..1 wing stubs flared     puff  body swell (scale)     glow  chest glow 0..3
# breath    star-breath life (None = off)    squeak  hurt marks    curl  0..1 knocked-out curl
DEFAULTS = dict(bx=0, by=0, crouch=0, tilt=0, neck=62, head=0, jaw=0.0, eye="open", look=0,
                feet=((0, 0), (0, 0), (0, 0), (0, 0)), tail=0, star=0, wing=0.0, puff=1.0, glow=0, breath=None,
                squeak=False, curl=0.0, breathe=0.0, dim=False)

POSE = px.poses(DEFAULTS, {
    "idle": [  # looks up and around, breathes, the tail star twinkles
        dict(star=0),
        dict(neck=66, head=10, star=1, breathe=0.4, tail=-3),
        dict(neck=64, head=4, star=2, breathe=0.6, tail=-5, look=1),
        dict(neck=60, head=-4, star=3, breathe=0.2, tail=-2),
    ],
    "walk": [  # waddle-trot: diagonal pairs, head bobs, tail sways
        dict(feet=((2, 0), (-2, 1), (-2, 1), (2, 0)), tilt=-2, tail=4, star=0, neck=60),
        dict(feet=((1, 0), (0, 2), (0, 2), (1, 0)), by=-1, tilt=0, tail=2, star=1, neck=62, head=3),
        dict(feet=((-1, 0), (1, 1), (1, 1), (-1, 0)), tilt=2, tail=-2, star=2, neck=64),
        dict(feet=((-2, 1), (2, 0), (2, 0), (-2, 1)), tilt=2, tail=-4, star=3, neck=60),
        dict(feet=((0, 2), (1, 0), (1, 0), (0, 2)), by=-1, tilt=0, tail=-2, star=0, neck=62, head=3),
        dict(feet=((1, 1), (-1, 0), (-1, 0), (1, 1)), tilt=-2, tail=2, star=1, neck=64),
    ],
    "windup": [  # puffs up, rears its head back, flares its wings, chest glows - held
        dict(neck=72, head=10, puff=1.05, wing=0.5, glow=1, eye="angry", bx=-1, tail=-6, star=2, crouch=0),
        dict(neck=80, head=16, puff=1.12, wing=1.1, glow=2, eye="angry", bx=-2, tail=-10, star=2, jaw=0.2),
        dict(neck=82, head=18, puff=1.15, wing=1.3, glow=3, eye="angry", bx=-2, tail=-12, star=2, jaw=0.25),
    ],
    "attack": [  # head snaps forward, a burst of star-breath on frame 1
        dict(neck=58, head=-4, puff=1.06, wing=0.8, glow=3, eye="angry", jaw=0.7, breath=0.12, star=2),
        dict(neck=50, head=-8, puff=1.02, wing=0.6, glow=2, eye="angry", jaw=1.0, bx=1, breath=0.5, star=2),
        dict(neck=52, head=-5, wing=0.3, glow=1, eye="angry", jaw=0.6, bx=1, breath=0.85, star=0),
        dict(neck=58, head=0, jaw=0.1, star=1),
    ],
    "hurt": [  # squeak-flinch
        dict(neck=78, head=22, eye="squeeze", bx=-3, tilt=6, squeak=True, tail=8, jaw=0.5, wing=0.4,
             feet=((0, 1), (0, 0), (0, 0), (0, 0)), star=3),
        dict(neck=70, head=12, eye="squeeze", bx=-2, tilt=3, tail=4, jaw=0.2, star=0),
    ],
    "death": [  # knocked out: sinks, curls up, eyes closed, its lights dim
        dict(neck=78, head=22, eye="squeeze", bx=-3, tilt=6, squeak=True, tail=8, jaw=0.5, star=3),
        dict(neck=36, head=-24, eye="closed", bx=-2, crouch=3, tilt=-4, tail=12, star=-1),
        dict(curl=1.0, eye="closed", star=-1),
        dict(curl=1.0, eye="closed", star=-2),
        dict(curl=1.0, eye="closed", star=-2, dim=True),
    ],
})


# ---- parts ------------------------------------------------------------------------------------
def _leg(cv, root, foot, far, mat, lift=0):
    """Stubby leg: a plump thigh tapering to a round foot with two gold claws."""
    fx, fy = foot
    knee = (root[0] + (fx - root[0]) * 0.4 + 0.6, root[1] + (fy - root[1]) * 0.55)
    shade = "dark" if far else "two"
    cv.limb([root, knee, (fx, fy - 1.4)], [2.3, 1.7, 1.3], mat, shade=shade, name="leg")
    cv.ellipse(fx + 0.6, fy - 0.6, 1.9, 1.1, mat, shade=shade, name="foot")
    if not far:
        cv.pixels([(math.floor(fx + 2.0), math.floor(fy - 1)), (math.floor(fx + 0.5), math.floor(fy - 1))],
                  GOLD.base, name="claw")


def _star(fx, c, kind):
    """The glowing tail star: 0 plus, 1 cross, 2 big plus, 3 small; -1 dim, -2 out."""
    x, y = math.floor(c[0]), math.floor(c[1])
    if kind == -2:
        fx.pixels([(x, y), (x + 1, y), (x, y + 1)], STAR_DIM, name="star")
        return
    if kind == -1:
        fx.pixels([(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)], STAR_DIM, name="star")
        fx.pixel(x, y, STAR_G, name="star")
        return
    if kind in (0, 2):
        r = 2
        for d in range(1, r + 1):
            col = STAR_G if d == 1 else GLOW_EDGE
            fx.pixels([(x - d, y), (x + d, y), (x, y - d), (x, y + d)], col, name="star")
        if kind == 2:
            fx.pixels([(x - 1, y - 1), (x + 1, y - 1), (x - 1, y + 1), (x + 1, y + 1)], GLOW_EDGE, name="star")
    elif kind == 1:  # a diagonal glint
        fx.pixels([(x - 1, y - 1), (x + 1, y - 1), (x - 1, y + 1), (x + 1, y + 1)], STAR_G, name="star")
        fx.pixels([(x - 2, y - 2), (x + 2, y - 2), (x - 2, y + 2), (x + 2, y + 2)], GLOW_EDGE, name="star")
    else:
        fx.pixels([(x + 1, y), (x, y + 1), (x - 1, y), (x, y - 1)], GLOW_EDGE, name="star")
    fx.pixel(x, y, STAR_W, name="star")


def _tail_pts(T0, sway, curl=0.0):
    pts = [(0.0, 0.0), (-3.8, 1.6), (-7.6, 1.2), (-10.4, -1.4), (-11.4, -5.0)]
    out = []
    for i, (x, y) in enumerate(pts):
        a = sway * (i / 4.0) ** 1.2
        q = px.rot_pt((T0[0] + x, T0[1] + y), a, T0)
        out.append(q)
    return out


def _wing(cv, W, raise_, far, mat=MEMB):
    """Stubby wing: a gold arm spar up and back from the shoulder, two short finger spars,
    an indigo membrane with star specks between them."""
    arm = 118 - 30 * raise_
    wr = px.polar(W, arm, 5.0 + 1.5 * raise_)
    f1 = px.polar(wr, arm + 95 + 10 * raise_, 5.5 + 1.5 * raise_)
    f2 = px.polar(wr, arm + 130 + 15 * raise_, 6.0 + 1.0 * raise_)
    back = px.polar(W, 185, 3.5)
    name = "wing_far" if far else "wing"
    cv.polygon([W, wr, f1, f2, back], mat, shade="dark" if far else "two", name=name, sep=None if far else "deep")
    if not far:
        for q in (px.lerp_pt(wr, f2, 0.45), px.lerp_pt(W, f1, 0.5)):
            cv.pixel(math.floor(q[0]), math.floor(q[1]), STAR_G, decal=True, clip=name, name=name)
    spar = GOLD
    cv.limb([W, wr], [0.9, 0.7], spar, shade="dark" if far else "two", name=name)
    cv.limb([wr, f1], [0.6, 0.4], spar, shade="dark" if far else "two", name=name)
    cv.limb([wr, f2], [0.6, 0.4], spar, shade="dark" if far else "two", name=name)


def _eye(cv, ex, ey, state, look):
    pal = {"k": INK, "g": px.GLINT, "i": IRIS, "h": IRIS_HI}
    if state == "squeeze":
        cv.stamp(["kk..", "..kk", "kk.."], ex, ey, pal, name="eye")
    elif state == "closed":
        cv.stamp(["....", "k..k", ".kk."], ex, ey, pal, name="eye")
    else:
        rows = [".kk.", "kgik", "kihk", ".kk."] if look == 0 else [".kk.", "kigk", "khik", ".kk."]
        cv.stamp(rows, ex, ey, pal, name="eye")
        if state == "angry":  # a brave little brow, low toward the snout
            cv.pixels([(ex, ey - 2), (ex + 1, ey - 2), (ex + 2, ey - 2), (ex + 3, ey - 1)], INK, name="brow")


def _head(cv, H, p, mat, sep=None):
    """Round cranium + short snout (one form), open jaw, gold forehead star, horns, eye."""
    with cv.xform(px.rotate(p.head, H)):
        x, y = H
        if p.jaw > 0:  # mouth cavity and the hinged lower jaw
            cv.polygon([(x + 1.5, y + 1.6), (x + 6.8, y + 1.4), (x + 6.6, y + 2.6 + 2.0 * p.jaw),
                        (x + 1.5, y + 3.2)], MOUTH, shade="two", name="mouth")
            with cv.xform(px.rotate(-28 * p.jaw, (x + 1.0, y + 2.4))):
                cv.limb([(x + 1.0, y + 3.0), (x + 5.8, y + 3.0)], [1.6, 1.1], mat, shade="two", name="jaw")
        cran = cv.geom_ellipse(x, y, 4.9, 4.5)
        snout = cv.geom_ellipse(x + 3.9, y + 1.4, 2.9, 2.3 if p.jaw <= 0 else 1.8)
        cv.draw_geom(cv.union(cran, snout, weights=[1.0, 0.75]), mat, name="head", sep=sep)
        # nostril and a small smiling mouth line
        cv.pixel(math.floor(x + 5.6), math.floor(y + 0.4), mat.deep, name="head")
        if p.jaw <= 0:
            cv.line((math.floor(x + 3), math.floor(y + 2.6)), (math.floor(x + 5), math.floor(y + 2.6)), mat.shadow,
                    decal=True, clip="head", name="head")
        # swept-back gold horns
        cv.limb([(x - 2.2, y - 3.4), (x - 4.6, y - 5.8), (x - 7.4, y - 6.4)], [1.15, 0.75, 0.35], GOLD, shade="two",
                name="horn", sep="deep")
        # gold forehead star
        sx, sy = math.floor(x + 1.2), math.floor(y - 3.2)
        cv.pixels([(sx, sy - 1), (sx - 1, sy), (sx + 1, sy), (sx, sy + 1)], GOLD.base, decal=True, clip="head",
                  name="head")
        cv.pixel(sx, sy, GOLD.light, decal=True, clip="head", name="head")
        _eye(cv, math.floor(x - 0.8), math.floor(y - 1.4), p.eye, p.look)
        mouth_at = cv.tp((x + 7.4, y + 2.4))
    return mouth_at


def _far_horn(cv, H, p):
    with cv.xform(px.rotate(p.head, H)):
        x, y = H
        cv.limb([(x - 0.8, y - 3.8), (x - 3.0, y - 6.6), (x - 5.4, y - 7.6)], [1.0, 0.7, 0.35], GOLD, shade="dark",
                name="horn_far")


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    if p.curl > 0:
        _curled(cv, p, frame)
        return
    X = cv.gx + p.bx
    G = cv.ground
    mat = PEARL_D if p.dim else PEARL
    B0 = (X - 2.0, G - 8.2 + p.crouch + p.by)
    br = p.breathe
    pz = p.puff
    fx_back = cv.layer(above=False, outline=False)
    top = cv.layer(above=True, outline=False)

    def foot(root_x, i):
        f = p.feet[i]
        return (root_x + f[0], G + 0.5 - f[1])

    roll = px.rotate(p.tilt, (B0[0], G))
    fr, hr = (B0[0] + 4.0, B0[1] + 2.4), (B0[0] - 4.2, B0[1] + 2.2)
    with cv.xform(roll):
        frw, hrw = cv.tp(fr), cv.tp(hr)
    # far legs
    _leg(cv, (frw[0] + 1.2, frw[1]), foot(fr[0] + 1.4, 1), True, mat)
    _leg(cv, (hrw[0] + 1.2, hrw[1]), foot(hr[0] + 1.0, 3), True, mat)
    with cv.xform(roll):
        W = (B0[0] + 2.2, B0[1] - 4.0)
        _wing(cv, (W[0] + 1.2, W[1] - 0.6), p.wing, far=True)
        # tail
        T0 = (B0[0] - 6.0, B0[1] + 0.2)
        tp = _tail_pts(T0, p.tail)
        cv.limb(tp, [2.6, 2.1, 1.6, 1.1, 0.8], mat, shade="full", name="tail")
        star_at = cv.tp((tp[-1][0] - 0.2, tp[-1][1] - 1.6))
        # body + neck as one form, puffed up about the belly
        N0 = (B0[0] + 5.2, B0[1] - 2.8)
        H = px.polar(N0, p.neck, 10.0)
        mid = px.lerp_pt(N0, H, 0.5)
        mid = (mid[0] + 1.2 * math.cos(math.radians(p.neck + 90)), mid[1] - 1.2 * math.sin(math.radians(p.neck + 90)))
        with cv.xform(px.scale(pz, pz, (B0[0], B0[1] + 5.0))):
            body = cv.geom_ellipse(B0[0], B0[1], 7.4, 5.0 + br * 0.4)
            chest = cv.geom_ellipse(B0[0] + 4.2, B0[1] - 0.8, 4.4, 4.4)
            neck = cv.geom_limb([N0, mid, H], [3.2, 2.3, 2.1])
            cv.draw_geom(cv.union(body, chest, neck, weights=[1.0, 0.9, 0.75]), mat, name="body")
            # soft blue-violet underbelly and throat, with belly-plate lines
            cv.ellipse(B0[0] + 1.0, B0[1] + 3.6, 7.0, 2.6, BELLY, shade="two", decal=True, clip="body", name="body")
            thr = [px.lerp_pt(N0, H, t) for t in (0.0, 0.5, 1.0)]
            thr = [(q[0] + 1.6, q[1] + 1.6) for q in thr]
            cv.limb([(B0[0] + 6.5, B0[1] + 1.5)] + thr[1:], [1.8, 1.4, 1.0], BELLY, shade="two", decal=True,
                    clip="body", name="body")
            for dx in (-3.0, 0.0, 3.0):
                cv.line((math.floor(B0[0] + dx), math.floor(B0[1] + 2.5)),
                        (math.floor(B0[0] + dx), math.floor(B0[1] + 4.5)), BELLY.shadow, band=None, decal=True,
                        clip="body", name="body")
            if p.glow:  # the chest glows pale gold
                gc = (B0[0] + 6.0, B0[1] + 0.5)
                cv.ellipse(gc[0], gc[1], 1.4 + p.glow * 0.8, 1.4 + p.glow * 0.7, px.flat(GLOW), decal=True,
                           clip="body", name="body")
                chest_c = cv.tp(gc)
            # gold nubs along the spine
            for (dx, dy) in ((-4.5, -4.6), (-1.5, -5.0), (1.5, -4.8)):
                q = (B0[0] + dx, B0[1] + dy)
                cv.pixels([(math.floor(q[0]), math.floor(q[1])), (math.floor(q[0]) + 1, math.floor(q[1]))], GOLD.base,
                          name="nub")
                cv.pixel(math.floor(q[0]), math.floor(q[1]) - 1, GOLD.light, name="nub")
            H = cv.tp(H)
            Hn = cv.tp(px.lerp_pt(N0, H, 0.55))
    # near legs
    _leg(cv, frw, foot(fr[0], 0), False, mat)
    _leg(cv, hrw, foot(hr[0], 2), False, mat)
    with cv.xform(roll):
        _wing(cv, W, p.wing, far=False)
    _far_horn(cv, H, p)
    mouth = _head(cv, H, p, mat)
    _star(top, star_at, p.star)
    if p.glow >= 2:  # a star flares in the chest, glints spark off it
        cx, cy = math.floor(chest_c[0]), math.floor(chest_c[1])
        arm = p.glow
        for d in range(1, arm + 1):
            top.pixels([(cx - d, cy), (cx + d, cy), (cx, cy - d), (cx, cy + d)], STAR_W if d < arm else GLOW,
                       name="glint")
        top.pixel(cx, cy, STAR_W, name="glint")
        for (dx, dy) in ((5, -4), (6, 3), (-1, -7))[:p.glow]:
            top.pixels([(cx + dx - 1, cy + dy), (cx + dx + 1, cy + dy), (cx + dx, cy + dy - 1),
                        (cx + dx, cy + dy + 1)], GLOW_EDGE, name="glint")
            top.pixel(cx + dx, cy + dy, STAR_W, name="glint")
    if p.breath is not None:
        _breath(top, cv.layer(above=True, outline=True), mouth, p.breath)
    if p.squeak:  # squeak marks above the head
        hx, hy = math.floor(H[0]), math.floor(H[1])
        top.line((hx + 3, hy - 8), (hx + 4, hy - 10), SQUEAK, name="squeak")
        top.line((hx + 6, hy - 6), (hx + 8, hy - 7), SQUEAK, name="squeak")
        top.line((hx + 0, hy - 9), (hx + 0, hy - 11), SQUEAK, name="squeak")
    del Hn


def _breath(fx, puff, M, t):
    """Star-breath: a bright flash at the jaws and a fan of twinkling stars flying out."""
    x0, y0 = M
    if t < 0.7:
        c = (min(x0 + 2 + 4 * t, fx.w - 9), y0)
        px.impact(fx, c[0], c[1], size=3 if t < 0.3 else 4, color=GLOW, core=STAR_W)
    fan = ((0, 1.0, "big"), (28, 0.85, "big"), (-26, 0.9, "big"), (14, 0.6, "dot"), (-12, 0.62, "dot"),
           (40, 0.55, "dot"), (-38, 0.58, "dot"), (6, 1.25, "dot"))
    for i, (a, r0, kind) in enumerate(fan):
        r = (4 + 8 * t) * r0 + 1.5
        q = px.polar((x0, y0), a, r)
        x, y = math.floor(q[0]), math.floor(q[1])
        if x > fx.w - 5 or r < 4:
            continue
        if kind == "big" and t < 0.95:
            arm = 2 if (t > 0.3 and i == 0) else 1
            for d in range(1, arm + 1):
                fx.pixels([(x - d, y), (x + d, y), (x, y - d), (x, y + d)], STAR_G if d == 1 else GLOW_EDGE,
                          name="breath")
            fx.pixel(x, y, STAR_W, name="breath")
        else:
            fx.pixels([(x, y), (x + 1, y)] if i % 2 else [(x, y), (x, y + 1)], STAR_W if i % 2 else STAR_G,
                      name="breath")


def _curled(cv, p, frame):
    """Knocked out: curled up on the ground, head resting on its forepaws, tail wrapped round."""
    cv.snap_ground = True
    X, G = cv.gx, cv.ground
    mat = PEARL_D if p.dim else PEARL
    B0 = (X - 3.0, G - 4.6)
    top = cv.layer(above=True, outline=False)
    _wing(cv, (B0[0] + 1.6, B0[1] - 3.6), 0.0, far=True)
    body = cv.geom_ellipse(B0[0], B0[1], 7.6, 4.6)
    chest = cv.geom_ellipse(B0[0] + 4.4, B0[1] + 0.2, 4.0, 4.0)
    N0 = (B0[0] + 5.0, B0[1] - 1.6)
    H = (B0[0] + 12.0, G - 3.4)
    neck = cv.geom_limb([N0, (B0[0] + 9.0, B0[1] - 2.0), (H[0] - 1.5, H[1] - 0.8)], [3.0, 2.4, 2.0])
    cv.draw_geom(cv.union(body, chest, neck, weights=[1.0, 0.9, 0.75]), mat, name="body")
    cv.ellipse(B0[0] + 1.0, B0[1] + 3.0, 6.8, 2.0, BELLY, shade="two", decal=True, clip="body", name="body")
    for (dx, dy) in ((-4.5, -4.2), (-1.5, -4.6), (1.5, -4.4)):
        q = (B0[0] + dx, B0[1] + dy)
        cv.pixels([(math.floor(q[0]), math.floor(q[1])), (math.floor(q[0]) + 1, math.floor(q[1]))], GOLD.base,
                  name="nub")
    _wing(cv, (B0[0] + 0.8, B0[1] - 3.0), 0.0, far=False)
    # tucked forepaw under the chin
    cv.ellipse(B0[0] + 9.0, G - 0.6, 2.2, 1.1, mat, shade="two", name="foot")
    # tail wrapped round the front, lying on the ground, star at its tip near the nose
    T0 = (B0[0] - 6.0, B0[1] + 1.0)
    tp = [T0, (T0[0] - 3.5, G - 2.0), (T0[0] - 1.0, G - 0.9), (B0[0] + 1.0, G - 0.9), (B0[0] + 6.0, G - 1.0)]
    cv.limb(tp, [2.4, 1.9, 1.5, 1.1, 0.8], mat, shade="two", name="tail", sep="deep")
    star_at = (tp[-1][0] + 1.4, tp[-1][1] - 0.6)
    hp = SimpleHead(p)
    _far_horn(cv, H, hp)
    _head(cv, H, hp, mat, sep="deep")
    _star(top, star_at, p.star)


class SimpleHead:
    """Pose view for the resting head (chin down on the paws, eyes closed)."""

    def __init__(self, p):
        self.head = -14
        self.jaw = 0.0
        self.eye = p.eye
        self.look = 0
