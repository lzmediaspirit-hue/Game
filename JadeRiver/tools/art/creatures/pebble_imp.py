"""Pebble imp - a small, grinning earth spirit whose stony skin is studded with pebbles;
it pelts intruders with stones (Earth element).

View: side, turned 3/4 toward the viewer (both glowing eyes and the whole grin show).
~30 art px tall: a big round stone head with shard ears, a pot-bellied torso, stubby
legs and long arms.  Parts, back to front: far leg, far arm, torso (+ pebble studs and
a glowing amber crack), near leg, head (shard ears, heavy brow, wide toothy grin, nub
nose, two glowing amber eyes), near arm with the pebble.  Arms and legs are solved with
``px.ik2``.  The throw releases the pebble on ``hit_frame`` (the engine draws the flying
stone); the death cracks the body into chunks that tumble into a pile of pebbles.
"""
import math

import helpers_batch_a as hb
import pixel as px

SPEC = {
    "id": "pebble_imp",
    "cell": 128,
    "anchor": [64, 112],
    "flying": False,
    "hit_frame": 1,
}

# ---- palette: warm grey-brown stone, three pebble kinds, amber inner glow -----------------
STONE = px.material("imp_stone", "#cfbf9d", "#9b8b71", "#6c6052", "#463e39", outline="#15110f",
                    thresholds=(0.86, 0.52, 0.2))
LIMB = px.material("imp_limb", "#bfae8e", "#8c7d66", "#62584c", "#403a36", outline="#15110f")
P_OCHRE = px.material("peb_ochre", "#e6bf7e", "#bb8f59", "#8b6945", "#5e4734", outline="#15110f")
P_SLATE = px.material("peb_slate", "#b7bebb", "#838c8b", "#5c6466", "#3c4347", outline="#111618")
P_RUST = px.material("peb_rust", "#d49373", "#a7684e", "#784a3c", "#4f302b", outline="#15110f")
EMBER = px.rgb("#ffbe45")
EMBER_CORE = px.rgb("#fff1b8")
EMBER_DIM = px.rgb("#a8692c")
MOUTH = px.rgb("#2b1712")
TEETH = px.rgb("#f4ead0")

# ---- poses --------------------------------------------------------------------------------
# bx, by    body offset         lean  torso + head tilt about the hips (deg, + = lean back)
# head      extra head tilt     near, far  hand targets (dx, dy) from each shoulder
# feet      (dx, lift) near / far foot      pebble  stone in the near hand   open  open hand
# grin      grin width 0..1     eye  open|angry|squeeze|dead   glow  eye brightness 0..1
# kneel     sink toward the ground (death)  crumble  None | chunk fall 0..1   pile  0..1
DEFAULTS = dict(bx=0, by=0, lean=0, head=0, near=(3.5, 7.0), far=(-2.5, 7.0), feet=((0, 0), (0, 0)),
                pebble=True, open=False, grin=1.0, eye="open", glow=1.0, kneel=0.0, crumble=None, pile=None,
                fade=1.0, streak=False, ear=0)

POSE = px.poses(DEFAULTS, {
    "idle": [  # bobbing on its toes, tossing the pebble in its palm
        dict(near=(5.0, 3.5)),
        dict(by=1, near=(5.0, 2.5), ear=-5),
        dict(by=1, near=(5.0, 1.0), head=3),
        dict(near=(5.0, 2.5), head=2),
    ],
    "walk": [  # jaunty waddle, arms swinging opposite the legs
        dict(feet=((3, 0), (-3, 1)), near=(1.5, 7.0), far=(0.5, 6.5), lean=-3),
        dict(feet=((2, 1), (-1, 0)), by=-1, near=(2.5, 7.0), far=(-1.0, 6.5), lean=-3),
        dict(feet=((0, 2), (1, 0)), by=-1, near=(4.0, 6.0), far=(-2.5, 6.5), lean=-3),
        dict(feet=((-3, 1), (3, 0)), near=(5.0, 5.5), far=(-3.0, 6.0), lean=-3),
        dict(feet=((-1, 0), (2, 1)), by=-1, near=(4.0, 6.0), far=(-1.5, 6.5), lean=-3),
        dict(feet=((1, 0), (0, 2)), by=-1, near=(2.5, 7.0), far=(0.0, 6.5), lean=-3),
    ],
    "windup": [  # rears back, the pebble drawn behind its head, eyes flare - held
        dict(lean=6, near=(-3.5, -4.0), far=(3.0, 3.0), eye="angry", feet=((2, 0), (-2, 0)), head=4),
        dict(lean=12, near=(-7.0, -6.5), far=(5.0, 0.5), eye="angry", feet=((3, 0), (-3, 0)), head=6, glow=1.2),
        dict(lean=14, near=(-8.0, -7.0), far=(5.5, 0.0), eye="angry", feet=((3, 0), (-3, 0)), head=7, glow=1.3,
             ear=-10),
    ],
    "attack": [  # overarm throw: whip forward, release on frame 1, follow through, recover
        dict(lean=0, near=(1.0, -9.0), far=(1.0, 5.0), eye="angry", feet=((3, 0), (-3, 0))),
        dict(lean=-12, near=(8.5, -2.0), far=(-4.0, 3.0), eye="angry", pebble=False, open=True,
             feet=((4, 0), (-3, 1)), streak=True),
        dict(lean=-16, near=(6.5, 5.0), far=(-4.5, 2.0), pebble=False, open=True, feet=((4, 0), (-3, 1)),
             head=-4),
        dict(lean=-5, near=(4.0, 6.0), far=(-2.5, 6.5), pebble=False, feet=((2, 0), (-2, 0))),
    ],
    "hurt": [
        dict(bx=-3, by=-1, lean=16, head=10, near=(-2.0, 2.0), far=(-4.0, 1.0), eye="squeeze", grin=0.3,
             glow=0.6, feet=((1, 2), (0, 0)), ear=-15),
        dict(bx=-2, lean=8, head=5, near=(0.0, 4.0), far=(-3.0, 4.0), eye="squeeze", grin=0.5, glow=0.8),
    ],
    "death": [  # reels, sinks to its knees cracking, bursts into chunks, a pile of pebbles
        dict(bx=-3, by=-1, lean=16, head=12, near=(-2.0, 2.0), far=(-4.0, 1.0), eye="squeeze", grin=0.2,
             glow=0.5, feet=((1, 2), (0, 0)), ear=-15),
        dict(bx=-3, lean=-10, head=-14, near=(3.0, 8.0), far=(0.0, 8.0), eye="dead", grin=0.0, glow=0.3,
             kneel=1.0, crumble=0.0, pebble=False),
        dict(bx=-3, lean=-10, head=-14, near=(3.0, 8.0), far=(0.0, 8.0), eye="dead", grin=0.0, glow=0.0,
             kneel=1.0, crumble=0.55, pebble=False),
        dict(bx=-3, pile=0.3, fade=0.6),
        dict(bx=-3, pile=0.0, fade=0.3),
    ],
})

# pebble studs: (part centre key, dx, dy, rx, ry, material)
STUDS_HEAD = ((-3.5, -3.0, 1.5, 1.2, P_OCHRE), (0.5, -4.8, 1.1, 0.9, P_SLATE), (-4.5, 1.5, 1.2, 1.0, P_RUST),
              (-1.5, 3.8, 0.9, 0.8, P_SLATE))
STUDS_BODY = ((-2.2, -2.0, 1.5, 1.2, P_RUST), (-2.4, 2.8, 1.2, 1.0, P_SLATE))


def _studs(cv, c, studs, clip):
    for dx, dy, rx, ry, mat in studs:  # raised pebbles, each with a dark rim
        cv.ellipse(c[0] + dx, c[1] + dy, rx, ry, mat, shade="soft", decal=True, clip=clip)


def _leg(cv, hip, foot, far, kneel):
    if kneel > 0:  # kneeling: shin flat on the ground behind the knee
        knee = (hip[0] + 2.5, foot[1] - 0.8)
        heel = (knee[0] - 5.0, foot[1] - 0.6)
        cv.limb([hip, knee, heel], [1.9, 1.5, 1.2], LIMB, shade="dark" if far else "soft", name="leg")
        return
    knee = px.ik2(hip, (foot[0], foot[1] - 1.6), 3.9, 3.9, bend=1)
    shade = "dark" if far else "soft"
    cv.limb([hip, knee, (foot[0], foot[1] - 1.6)], [2.0, 1.7, 1.6], LIMB, shade=shade, name="leg",
            sep=False if far else "deep")
    cv.ellipse(foot[0] + 1.2, foot[1] - 1.0, 2.6, 1.5, STONE, shade="dark" if far else "two", name="foot")


def _arm(cv, sh, target, far, p):
    bend = -1 if target[1] < sh[1] - 2 else 1
    elbow = px.ik2(sh, target, 4.6, 4.6, bend=bend if not far else 1)
    shade = "dark" if far else "soft"
    cv.limb([sh, elbow, target], [1.8, 1.4, 1.4], LIMB, shade=shade, name="arm", sep=False if far else "deep")
    # big knobbly stone hand
    cv.circle(target[0], target[1], 1.9, STONE, shade="dark" if far else "soft", name="hand",
              sep=False if far else "deep")
    if not far:
        if p.open:  # splayed fingers after the release
            d = (target[0] - elbow[0], target[1] - elbow[1])
            ln = math.hypot(*d) or 1.0
            u = (d[0] / ln, d[1] / ln)
            for a in (-35, 0, 35):
                q = px.rot_pt((target[0] + u[0] * 2.8, target[1] + u[1] * 2.8), a, target)
                cv.limb([target, q], [0.8, 0.55], LIMB, shade="two", name="finger")
        if p.pebble:
            cv.circle(target[0] + 0.8, target[1] - 1.6, 1.7, P_SLATE, name="pebble", sep="deep")
            cv.pixel(math.floor(target[0]), math.floor(target[1] - 2.6), P_SLATE.light, name="pebble")
    return elbow


GRIN = ["k.......k", "ktt.tttkk", ".kttttkk.", "..kkkk..."]
GRIMACE = ["..kkkk.", ".k....k"]


def _head(cv, Hc, p):
    # chunky shard ears swept back: the far one dark behind, the near one a clear stone blade
    with cv.xform(px.rotate(p.ear * 0.6, (Hc[0] + 1.0, Hc[1] - 4.5))):
        cv.polygon([(Hc[0] - 1.0, Hc[1] - 4.0), (Hc[0] + 0.5, Hc[1] - 10.5), (Hc[0] + 3.5, Hc[1] - 4.5)],
                   STONE, shade="dark", name="ear")
    with cv.xform(px.rotate(p.ear, (Hc[0] - 3.0, Hc[1] - 3.0))):
        cv.polygon([(Hc[0] - 4.5, Hc[1] - 0.5), (Hc[0] - 9.5, Hc[1] - 8.5), (Hc[0] - 0.5, Hc[1] - 5.5)],
                   STONE, shade="soft", name="ear")
    head = cv.union(cv.geom_ellipse(Hc[0], Hc[1], 6.4, 6.0),
                    cv.geom_ellipse(Hc[0] + 2.5, Hc[1] + 2.4, 4.6, 3.6),
                    weights=[1.0, 0.7])
    cv.draw_geom(head, STONE, name="head", sep="deep")
    # pebbles set into the skull (decals follow the head's light), a lit edge on each
    for dx, dy, r, mat in ((-3.6, -2.4, 1.6, P_OCHRE), (-4.2, 2.0, 1.2, P_SLATE)):
        cv.ellipse(Hc[0] + dx, Hc[1] + dy, r * 1.15, r, mat, shade="soft", decal=True, clip="head")
    # nub nose at the front
    cv.circle(Hc[0] + 6.4, Hc[1] + 0.6, 1.4, STONE, shade="soft", name="nose", sep="deep")
    # big crescent grin with a row of pale teeth (3/4 view: it wraps round the snout)
    mx, my = math.floor(Hc[0] - 1.0), math.floor(Hc[1] + 2.0)
    if p.grin > 0.6:
        cv.stamp(GRIN, mx, my, {"k": MOUTH, "t": TEETH}, name="mouth")
    else:
        cv.stamp(GRIMACE, mx + 1, my + 1, {"k": MOUTH}, name="mouth")
    # two glowing eyes (near eye larger) in dark sockets
    near = (math.floor(Hc[0] + 1.0), math.floor(Hc[1] - 2.0))
    far = (math.floor(Hc[0] + 4.6), math.floor(Hc[1] - 2.0))
    glow = p.glow
    core = EMBER_CORE if glow >= 1.0 else EMBER
    rim = EMBER if glow >= 0.6 else EMBER_DIM
    if p.eye == "squeeze":
        cv.stamp(["k..", ".kk", "k.."], near[0], near[1], {"k": px.INK}, name="eye")
        cv.stamp(["k.", ".k"], far[0] + 1, far[1], {"k": px.INK}, name="eye")
    elif p.eye == "dead":
        cv.stamp(["k.k", ".k.", "k.k"], near[0], near[1], {"k": px.INK}, name="eye")
        cv.stamp(["kk"], far[0] + 1, far[1] + 1, {"k": px.INK}, name="eye")
    else:
        big = glow > 1.1
        cv.stamp(["rrr", "rcr", "rrr"] if big else ["rr", "cr"], near[0], near[1], {"r": rim, "c": core},
                 name="eye")
        cv.stamp(["r", "c"] if not big else ["rr", "cr"], far[0] + 1, far[1], {"r": rim, "c": core}, name="eye")
        hb.socket(cv, colour=STONE.deep)
        if p.eye == "angry":  # brow notch slanting down toward the nose
            cv.pixels([(near[0] - 1, near[1] - 2), (near[0], near[1] - 1), (near[0] + 1, near[1] - 1),
                       (far[0] + 1, far[1] - 1), (far[0] + 2, far[1] - 2)], px.INK, name="brow", clip="head")


def _pile(cv, x, ground, ember):
    """Settled heap of pebbles (the imp's remains), a last amber ember inside."""
    rocks = ((0.0, 2.3, STONE), (-4.0, 1.9, P_OCHRE), (4.0, 1.8, P_SLATE), (-7.0, 1.3, STONE), (7.0, 1.4, P_RUST),
             (-2.0, 1.7, P_RUST), (2.2, 1.6, STONE), (0.0, 1.5, P_SLATE), (-5.0, 1.2, P_SLATE), (5.3, 1.1, STONE))
    for k, (dx, r, mat) in enumerate(rocks):
        lift = 2.4 if k in (5, 6) else (4.2 if k == 7 else 0.0)
        cv.circle(x + dx, ground + 0.5 - r - lift, r, mat, shade="soft", name="pile", sep="deep")
    if ember > 0:
        cv.pixels([(math.floor(x) - 1, math.floor(ground - 3.0))], EMBER, name="ember")


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    ground = cv.ground
    cv.opacity = p.fade
    if p.pile is not None:
        _pile(cv, cv.gx + p.bx, ground, p.pile)
        return
    kn = p.kneel
    Hp = (cv.gx - 1 + p.bx, ground - 7.2 + p.by + 4.2 * kn)  # hips
    lean = px.rotate(p.lean, Hp)
    with cv.xform(lean):
        T = (Hp[0] + 0.3, Hp[1] - 4.8)
        sh_n, sh_f = cv.tp((T[0] + 1.2, T[1] - 3.2)), cv.tp((T[0] - 1.2, T[1] - 3.6))
        Hc = (T[0] + 1.2, T[1] - 10.2)
    # far leg + far arm behind the body
    ff = p.feet[1]
    _leg(cv, (Hp[0] - 1.2, Hp[1] + 0.5), (Hp[0] - 1.0 + ff[0], ground - ff[1]), True, kn)
    _arm(cv, sh_f, (sh_f[0] + p.far[0], sh_f[1] + p.far[1]), True, p)
    with cv.xform(lean):
        cv.ellipse(T[0], T[1], 4.6, 5.6, STONE, name="torso", sep="deep")
        _studs(cv, T, STUDS_BODY, "torso")
        # glowing amber crack across the belly
        if p.glow > 0.2:
            cv.limb([(T[0] - 0.5, T[1] - 1.5), (T[0] + 0.8, T[1] + 0.2), (T[0] + 0.2, T[1] + 1.8)], 0.45,
                    px.flat(EMBER if p.glow >= 0.6 else EMBER_DIM), decal=True, clip="torso")
    fn = p.feet[0]
    _leg(cv, (Hp[0] + 1.0, Hp[1] + 0.8), (Hp[0] + 1.5 + fn[0], ground - fn[1]), False, kn)
    with cv.xform(lean, px.rotate(p.head, (Hc[0] - 1.0, Hc[1] + 5.0))):
        _head(cv, Hc, p)
    target = (sh_n[0] + p.near[0], sh_n[1] + p.near[1])
    _arm(cv, sh_n, target, False, p)
    if p.crumble is not None:
        seeds = [(Hc[0] - 3, Hc[1] - 3), (Hc[0] + 3, Hc[1] - 2), (Hc[0], Hc[1] + 3), (Hc[0] - 7, Hc[1] - 6),
                 (T[0] - 3, T[1] - 2), (T[0] + 3, T[1]), (T[0] - 1, T[1] + 4), (Hp[0] - 4, ground - 2),
                 (Hp[0] + 4, ground - 2), (target[0], target[1])]
        hb.crumble(cv, seeds, p.crumble, cv.gy - 2, seed=7, spread=1.2)
        cv.snap_ground = False
    if p.streak:  # the release: a short whoosh behind the empty hand
        back = cv.layer(above=False, outline=False)
        px.speed_lines(back, target[0] - 2, target[1], length=6, count=2, spacing=3, color=px.DUST.light)
