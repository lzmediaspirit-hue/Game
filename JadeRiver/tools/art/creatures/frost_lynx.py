"""Frost lynx - a big pale mountain lynx rimed with ice, eyes glowing ice-blue (Ice / Water).

Azure Expanse, Rimefrost Heights (67-70).  Built on the mist wolf rig (cell 192): the body is
shorter with high haunches and long hind legs, the head is round with a short muzzle, tall
black-tipped ears end in tufts, a flared cheek ruff frames the face and the tail is a short
dark-tipped bob.  Faint grey-blue rosettes, a cream belly, ice crystals on the shoulders and
rime on the ruff.
Walk is a low stalking trot; windup sinks into a pounce crouch while the haunches wiggle, the
ears flatten and frost breath gathers at the muzzle (held); attack is a long pounce that rakes
with the claws out on frame 1 (airborne); death collapses onto its side while frost creeps
over the body, then fades.
"""
import math

import numpy as np

import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "frost_lynx",
    "cell": 192,
    "anchor": [96, 168],
    "flying": False,
    "hit_frame": 1,
    "airborne": [["attack", 1]],
}

# ---- palette: frost-white / silver-blue fur, violet-blue shadows, warm white lights ------------
FUR = px.material("lynx_fur", "#fffbf0", "#d6e1ec", "#a0afcb", "#6c74a3", outline="#141830",
                  thresholds=(0.9, 0.55, 0.2))
BELLY = px.material("lynx_belly", "#fffcef", "#f1e9d5", "#c7c1cb", "#9690b0", outline="#18182c")
SPOT = px.material("lynx_spot", "#b2c0d8", "#909fbe", "#6d78a2", "#4e5583", outline="#141830")
TIP = px.material("lynx_tip", "#6a7092", "#464b6a", "#30344e", "#212438", outline="#0b0d18")
ICE = px.material("lynx_ice", "#f6ffff", "#c2eefa", "#82c6e6", "#4f8cc2", outline="#10284a")
FROST = px.material("lynx_frost", "#ffffff", "#e0f2fa", "#b0d2e8", "#86a6cc", outline="#3a5474")
RIME = px.material("lynx_rime", "#f2fbff", "#c6e4f4", "#8cb6dc", "#5f7fba", outline="#10284a")
EYE_V = px.rgb("#8ff0ff")  # the two glowing-ice accents: eye iris / glow trail / impact
EYE_C = px.rgb("#2f86c8")

# ---- poses ------------------------------------------------------------------------------------
# bx, by   body offset        crouch  lower the body        rump   raise the haunches (px)
# pitch    body tilt (deg)    stretch body length           head   head tilt (deg)
# jaw      mouth 0..1         ear     ear angle (- = flattened back)
# feet     (dx, lift): near-front, far-front, near-hind, far-hind
# tail     (lift, twitch phase)          eye   open|angry|squeeze|dead      glow  eye trail px
# breath   frost breath life 0..1 (None = off)   claws  claws out   slash  claw rake FX life
# frost    0..1 frost creeping over the body      lying  collapsed on its side (death)
DEFAULTS = dict(bx=0, by=0, crouch=0, rump=0, pitch=0, stretch=1.0, head=0, jaw=0.0, ear=0,
                feet=((-1, 0), (2, 0), (0, 0), (0, 0)), tail=(1, 0.0), eye="open", glow=0, breath=None,
                claws=False, slash=None, hit=False, frost=0.0, lying=False, fade=1.0, breathe=0.0)

POSE = px.poses(DEFAULTS, {
    "idle": [
        dict(tail=(1, 0.0)),
        dict(tail=(1, 1.0), breathe=0.4),
        dict(tail=(2, 2.0), breathe=0.6, head=1, ear=-8),
        dict(tail=(1, 3.0), breathe=0.2),
    ],
    "walk": [  # low stalking trot: diagonal pairs swap, head level, 1 px bob on the passing frames
        dict(feet=((3, 0), (-3, 1), (-3, 1), (3, 0)), crouch=1, head=-3, tail=(1, 0.0)),
        dict(feet=((1, 0), (-1, 3), (-1, 3), (1, 0)), crouch=1, head=-3, by=-1, tail=(1, 1.0)),
        dict(feet=((-1, 0), (1, 2), (1, 2), (-1, 0)), crouch=1, head=-3, tail=(1, 2.0)),
        dict(feet=((-3, 1), (3, 0), (3, 0), (-3, 1)), crouch=1, head=-3, tail=(1, 3.0)),
        dict(feet=((-1, 3), (1, 0), (1, 0), (-1, 3)), crouch=1, head=-3, by=-1, tail=(1, 4.0)),
        dict(feet=((1, 2), (-1, 0), (-1, 0), (1, 2)), crouch=1, head=-3, tail=(1, 5.0)),
    ],
    "windup": [  # sinks into the pounce crouch, haunches wiggle, ears flatten, frost breath - held
        dict(crouch=3, bx=-1, rump=1, head=-3, ear=-30, eye="angry", tail=(2, 0.5), breath=0.25, glow=1,
             feet=((2, 0), (3, 0), (-1, 0), (-1, 0))),
        dict(crouch=6, bx=-2, rump=3, head=-3, ear=-55, eye="angry", tail=(3, 1.5), breath=0.55, glow=1,
             pitch=-3, stretch=0.96, jaw=0.2, feet=((3, 0), (4, 0), (-1, 1), (-2, 0))),
        dict(crouch=7, bx=-3, rump=2, head=-3, ear=-65, eye="angry", tail=(3, 2.6), breath=0.9, glow=2,
             pitch=-4, stretch=0.95, jaw=0.35, breathe=0.5, feet=((3, 0), (4, 0), (-2, 0), (-1, 0))),
    ],
    "attack": [  # long pounce: springs off the haunches, rakes with the claws out on frame 1
        dict(bx=3, by=-4, pitch=14, stretch=1.06, head=-2, jaw=0.7, ear=-45, eye="angry", glow=2, tail=(3, 3.0),
             claws=True, feet=((7, 14), (5, 15), (-8, 0), (-10, 0))),
        dict(bx=11, by=-6, pitch=0, stretch=1.2, head=-3, jaw=1.0, ear=-50, eye="angry", glow=2, tail=(2, 4.0),
             claws=True, slash=0.0, hit=True, feet=((10, 15), (8, 16), (-10, 13), (-12, 12))),
        dict(bx=13, pitch=-8, crouch=2, stretch=1.04, head=-2, jaw=0.4, ear=-30, eye="angry", tail=(2, 5.0),
             claws=True, slash=0.7, feet=((3, 0), (1, 0), (-5, 4), (-7, 3))),
        dict(bx=9, crouch=1, head=-1, ear=-8, tail=(1, 6.0), feet=((0, 0), (2, 0), (-1, 0), (0, 0))),
    ],
    "hurt": [
        dict(bx=-4, by=-2, head=14, eye="squeeze", jaw=0.4, ear=-50, pitch=6, tail=(3, 1.0),
             feet=((0, 3), (2, 2), (0, 0), (0, 0))),
        dict(bx=-2, head=7, eye="squeeze", ear=-25, pitch=3, tail=(2, 2.0)),
    ],
    "death": [  # rears in pain, legs buckle, collapses onto its side while frost creeps over it
        dict(bx=-4, by=-2, head=18, eye="squeeze", jaw=0.5, ear=-55, pitch=7, tail=(3, 1.0),
             feet=((0, 3), (2, 2), (0, 0), (0, 0))),
        dict(bx=-4, crouch=7, head=-10, eye="dead", ear=-60, tail=(0, 2.0), frost=0.15,
             feet=((3, 0), (4, 0), (-1, 0), (-1, 0))),
        dict(bx=-3, lying=True, eye="dead", frost=0.35),
        dict(bx=-3, lying=True, eye="dead", frost=0.7, fade=0.6),
        dict(bx=-3, lying=True, eye="dead", frost=1.0, fade=0.3),
    ],
})

# faint broken rosettes: cluster centres (dx, dy) from the body centre, before the stretch
ROSETTES = ((-11.0, -2.4), (-6.4, 1.8), (-5.8, -4.2), (-1.6, -0.2), (2.4, -3.6), (5.0, 1.2), (-9.4, 2.6))


# ---- parts ------------------------------------------------------------------------------------
def _deg(v):
    return math.degrees(math.atan2(-v[1], v[0]))


def _paw(cv, foot, ang, far, claws, grounded=True):
    """Big padded paw whose sole rests on ``foot``; ``ang`` tilts it (deg, 0 = flat forward).
    Returns the point just in front of the toes."""
    shade = "dark" if far else "two"
    c = px.polar((foot[0], foot[1] - 0.9), ang, 0.9)
    cv.ellipse(c[0], c[1], 2.7, 1.6, FUR, angle=ang, shade=shade, name="paw")
    if not far and abs(ang) < 20:  # toe split
        t = px.polar(c, ang, 1.2)
        cv.pixel(math.floor(t[0]), math.floor(t[1] + 0.4), FUR.shadow, name="paw")
    if claws:  # icy hooked claws out of the front of the paw
        for k in (-0.7, 1.0):
            b = px.polar(px.polar(c, ang, 2.0), ang - 90, k)
            tip = px.polar(b, ang - (15 if grounded else 40), 2.2)
            if grounded:
                b, tip = (b[0], min(b[1], cv.ground)), (tip[0], min(tip[1], cv.ground))
            cv.line((math.floor(b[0]), math.floor(b[1])), (math.floor(tip[0]), math.floor(tip[1])),
                    ICE, band=0 if not far else 2, name="claw")
    return px.polar(c, ang, 3.6)


def _front_leg(cv, hip, foot, far, claws=False, sep=False):
    fx, fy = foot
    d = (fx - hip[0], fy - hip[1])
    ln = math.hypot(*d) or 1.0
    u = (d[0] / ln, d[1] / ln)
    wrist = (fx - u[0] * 2.4 - 0.2, fy - u[1] * 2.4 - 0.2)
    elbow = px.ik2(hip, wrist, 5.2, 4.8, bend=-1)
    elbow = (elbow[0], min(elbow[1], cv.ground - 2.6))  # a folded foreleg's elbow rides up, never into the snow
    lift = cv.ground - fy
    reach = min(1.0, max(0.0, (u[0] - 0.3) / 0.5)) * min(1.0, max(0.0, lift / 4.0))
    ang = reach * _deg(u)
    cv.limb([hip, elbow, wrist, (fx, fy - 1.2)], [2.9, 2.1, 1.6, 1.6], FUR, shade="dark" if far else "two",
            name="leg", sep=sep)
    return _paw(cv, foot, ang, far, claws, grounded=lift < 1.0)


def _hind_leg(cv, hip, foot, far, crouch, lift=0):
    fx, fy = foot
    a_h = _deg((hip[0] - fx, hip[1] - fy))
    hock = px.polar((fx, fy - 1.0), a_h + 24 + crouch * 4, 5.4 - crouch * 0.3)
    knee = px.ik2(hip, hock, 5.8, 5.4, bend=1)
    cv.limb([hip, knee, hock, (fx, fy - 1.2)], [3.8, 2.3, 1.5, 1.5], FUR, shade="dark" if far else "two",
            name="leg")
    t = min(1.0, max(0.0, (lift - 2) / 6.0))
    _paw(cv, foot, t * _deg((fx - hock[0], fy - hock[1])), far, False)


def _tail(cv, root, p):
    """Short bobbed tail with a dark tip; lifts and twitches."""
    lift, ph = p.tail
    w = math.sin(ph * 1.6)
    a0 = 185 - lift * 13
    pts = [root]
    q = root
    for k, (ln, bend) in enumerate(((2.8, 0), (2.6, -16))):
        q = px.polar(q, a0 + bend + w * 8 * (k + 1) / 2, ln)
        pts.append(q)
    cv.limb(pts, [2.1, 2.3, 1.8], FUR, name="tail")
    cv.limb([px.lerp_pt(pts[1], pts[2], 0.7), pts[2]], [2.3, 1.8], TIP, shade="two", decal=True, clip="tail")


def _ear(cv, H, ang, far):
    """Tall pointed ear with a pale inside, a black tip and a black tuft.  The far ear stands
    a little forward of the near one so both points read in the silhouette."""
    pivot = (H[0] - 2.2, H[1] - 3.8)
    if far:
        ang += 10  # splayed a little forward so the two ears make a V
    # ``ang`` < 0 flattens the ear back (the tip swings toward the tail)
    base_b, tip, base_f = [px.rot_pt(q, -ang, pivot) for q in ((H[0] - 4.8, H[1] - 2.2), (H[0] - 3.0, H[1] - 10.8),
                                                               (H[0] + 0.0, H[1] - 4.2))]
    tuft = px.rot_pt((H[0] - 2.9, H[1] - 13.2), -ang, pivot)
    if far:
        base_b, tip, base_f, tuft = [(x + 2.8, y + 0.8) for (x, y) in (base_b, tip, base_f, tuft)]
    name = "ear_far" if far else "ear"
    mid = px.lerp_pt(base_b, base_f, 0.5)
    ax = _deg((tip[0] - mid[0], tip[1] - mid[1]))
    # a true triangle, with a 1 px flat top so the point always rasterises
    ear = [base_b, px.polar(tip, ax + 90, 0.6), px.polar(tip, ax - 90, 0.6), base_f]
    cv.polygon(ear, FUR, shade="nolight" if far else "full", name=name)
    cv.limb([px.lerp_pt(tip, mid, 0.08), tuft], [0.7, 0.55], TIP, shade="dark" if far else "two", name=name)
    if not far:
        cv.polygon([px.lerp_pt(base_b, base_f, 0.5), px.lerp_pt(base_b, tip, 0.55), px.lerp_pt(base_f, tip, 0.5)],
                   BELLY, shade="two", decal=True, clip="ear")
    cv.limb([px.lerp_pt(mid, tip, 0.8), tip], [1.4, 1.2], TIP, shade="two", decal=True, clip=name)


def _shard(cv, base, ang, ln, w):
    """One ice crystal growing out of ``base`` toward ``ang`` (deg)."""
    tip = px.polar(base, ang, ln)
    mid = px.lerp_pt(base, tip, 0.45)
    pts = [px.polar(base, ang + 90, w * 0.8), px.polar(mid, ang + 90, w), tip, px.polar(mid, ang - 90, w),
           px.polar(base, ang - 90, w * 0.8)]
    cv.polygon(pts, ICE, shade="soft", name="ice", sep="deep")


def _eye(cv, fx, x, y, state, glow):
    if state == "squeeze":
        hc.eye_stamp(cv, ["k.", ".k", "k."], x, y - 1, {})
    elif state == "dead":
        hc.eye_stamp(cv, ["k.k", ".k.", "k.k"], x - 1, y - 1, {})
    else:
        # almond eye: dark upper lid, ice-blue iris with a glint, dark tear line at the front corner
        rows = [".kkk", "kgv.", ".vck"] if state == "angry" else [".kk.", "kgv.", ".vck"]
        hc.eye_stamp(cv, rows, x - 1, y - 1, {"v": EYE_V, "c": EYE_C})
        if state == "angry":  # brow slanting down toward the snout
            cv.pixels([(x - 1, y - 2), (x + 2, y)], TIP.base, name="brow")
        if glow:  # cold light trailing back from the eye
            fx.line((x - 2, y), (x - 3 - glow, y), EYE_V, name="glow")
            fx.line((x - 2, y + 1), (x - 2 - glow, y + 1), EYE_C, name="glow")


def _rosettes(cv, C, st, clip="body"):
    """Faint broken rosettes: small 2-3 px arcs of the spot tone (decals, so each keeps the
    fur's light band)."""
    shapes = (["ss", "s."], ["ss", ".s"], ["s.", "ss"], ["ss"])
    for k, (dx, dy) in enumerate(ROSETTES):
        cv.stamp(shapes[k % len(shapes)], math.floor(C[0] + dx * st), math.floor(C[1] + dy), {"s": SPOT},
                 decal=True, clip=clip)


def _frost_creep(cv, amount, top, bottom):
    """Frost climbing up the body from the ground: an icy decal with a bright rime edge."""
    if amount <= 0:
        return
    edge = bottom + 1.0 - amount * (bottom - top + 4.0)
    ragged = edge + 1.4 * np.sin(cv.X * 0.9 + 1.3) + 0.8 * np.sin(cv.X * 2.3)
    m = cv.filled & (cv.Y > ragged)
    if m.any():
        cv._commit(m, np.where(m, 1, -1).astype(np.int8), RIME, decal=True)
        # bright rime along the creeping edge (frosted pixel with unfrosted body above it)
        rim = m & ~px._shift(m, 0, 1, False) & px._shift(cv.filled, 0, 1, False)
        if rim.any():
            cv._commit(rim, np.where(rim, 1, -1).astype(np.int8), ICE)


def _breath(fx, mouth, t):
    """Frost breath gathering round the muzzle: a curling cold cloud plus ice glints."""
    for k, (dx, dy, r) in enumerate(((1.8, 1.8, 1.4), (4.2, 0.4, 1.8), (2.6, -1.8, 1.3))):
        if t < k * 0.3:
            continue
        g = min(1.0, (t - k * 0.3) / 0.4)
        fx.circle(mouth[0] + dx, mouth[1] + dy, r * (0.6 + 0.4 * g), FROST, shade="soft", name="breath")
    if t > 0.5:
        for (dx, dy) in ((8.0, -3.0), (6.0, 4.0))[: 1 + (t > 0.8)]:
            x, y = math.floor(mouth[0] + dx), math.floor(mouth[1] + dy)
            fx.pixels([(x, y - 1), (x - 1, y), (x + 1, y), (x, y + 1)], ICE.base, name="glint")
            fx.pixel(x, y, px.GLINT, name="glint")


def _slash(fx, at, t):
    """Three icy claw rakes curving down across the target (``t`` 0 = fresh, 1 = gone)."""
    n = 3 if t < 0.5 else 2
    for k in range(n):
        c = (at[0] - 4.0 + k * 2.6, at[1] - 1.0 + k * 0.6)
        r = 6.0 + k * 0.6
        a0, a1 = (60 - t * 50, -50 - t * 20)
        hc.arc_line(fx, (c[0] + 1, c[1]), r, a0, a1, ICE.shadow, name="slash")
        hc.arc_line(fx, c, r, a0, a1, ICE.light if t < 0.5 else ICE.base, name="slash")


def _ruff(cv, H):
    """Flared cheek ruff hanging below the jaw, a dark bar across it, its points rimed with frost."""
    pts = [(H[0] - 3.6, H[1] - 0.4), (H[0] + 3.2, H[1] + 2.6), (H[0] + 2.8, H[1] + 6.6), (H[0] + 0.8, H[1] + 5.0),
           (H[0] - 0.8, H[1] + 8.0), (H[0] - 2.4, H[1] + 5.4), (H[0] - 4.8, H[1] + 6.2), (H[0] - 4.4, H[1] + 2.6)]
    cv.polygon(pts, FUR, shade="soft", name="ruff")
    cv.limb([(H[0] - 3.6, H[1] + 1.6), (H[0] - 1.0, H[1] + 3.0), (H[0] + 1.2, H[1] + 3.2)], [0.6, 0.7, 0.5], TIP,
            decal=True, clip="ruff", name="ruff")
    for q in ((H[0] - 0.8, H[1] + 7.4), (H[0] - 4.4, H[1] + 5.8)):  # frosted points
        cv.ellipse(q[0], q[1], 1.0, 1.1, ICE, decal=True, clip="ruff")


# ---- lying on its side (death) -----------------------------------------------------------------
def _lying(cv, p, glowfx):
    """Collapsed on its side: long low body, stiff legs splayed out along the ground, the head
    resting on the forepaws, ears flat."""
    cv.snap_ground = True
    g = cv.ground
    C = (cv.gx - 4 + p.bx, g - 7.0)

    def stiff_leg(a, b, far, r0):
        cv.limb([a, px.lerp_pt(a, b, 0.55), b], [r0, 1.8, 1.5], FUR, shade="dark" if far else "two", name="leg",
                sep=False if far else "deep")
        ang = _deg((b[0] - a[0], b[1] - a[1]))
        c = px.polar(b, ang, 0.9)
        cv.ellipse(c[0], c[1], 2.5, 1.5, FUR, angle=ang, shade="dark" if far else "two", name="paw")

    # far legs splay out behind the near ones, then the bobbed tail
    stiff_leg((C[0] + 7.0, C[1] + 1.5), (C[0] + 18.5, g - 2.4), True, 2.4)
    stiff_leg((C[0] - 9.0, C[1] + 1.0), (C[0] - 19.0, g - 2.2), True, 3.0)
    T = (C[0] - 12.8, C[1] - 1.6)
    tail = [T, (T[0] - 2.8, T[1] + 0.2), (T[0] - 5.2, T[1] + 1.2)]
    cv.limb(tail, [2.0, 2.1, 1.7], FUR, name="tail")
    cv.limb([px.lerp_pt(tail[1], tail[2], 0.6), tail[2]], [2.1, 1.7], TIP, shade="two", decal=True, clip="tail")
    H = (C[0] + 15.0, C[1] - 0.6)
    tilt = [px.rotate(-12, H)]
    with cv.xform(*tilt):
        _ear(cv, H, -62, True)
    body = [cv.geom_ellipse(C[0] - 7.0, C[1] + 0.2, 6.2, 5.0),
            cv.geom_limb([(C[0] - 5.0, C[1]), (C[0] + 4.0, C[1] + 0.2)], [4.3, 4.7]),
            cv.geom_ellipse(C[0] + 5.2, C[1] + 0.4, 6.0, 5.0)]
    with cv.xform(*tilt):
        head = [cv.geom_limb([(C[0] + 9.0, C[1] - 0.6), H], [4.2, 4.0]),
                cv.geom_ellipse(H[0], H[1], 5.4, 4.8),
                cv.geom_limb([(H[0] + 2.4, H[1] + 1.4), (H[0] + 5.2, H[1] + 2.0)], [3.0, 2.2])]
    cv.draw_geom(cv.union(*body, *head, weights=[0.95, 0.8, 1.0, 0.6, 0.9, 0.7]), FUR, name="body", sep="deep")
    cv.limb([(C[0] - 10.0, C[1] + 3.6), (C[0], C[1] + 4.2), (C[0] + 8.0, C[1] + 4.0)], [1.4, 1.7, 1.6], BELLY,
            shade="two", decal=True, clip="body")
    _rosettes(cv, (C[0] + 1.0, C[1] + 0.4), 0.95)
    for base, ang, ln, w in (((C[0] + 3.2, C[1] - 3.8), 125, 2.8, 0.9), ((C[0] + 5.8, C[1] - 4.0), 105, 3.6, 1.1)):
        _shard(cv, base, ang, ln, w)
    with cv.xform(*tilt):
        _ruff(cv, H)
        _ear(cv, H, -62, False)
        cv.ellipse(H[0] + 4.6, H[1] + 2.8, 2.8, 1.4, BELLY, shade="soft", decal=True, clip="body")
        nx, ny = math.floor(H[0] + 7.2), math.floor(H[1] + 1.0)
        cv.pixels([(nx - 1, ny), (nx - 2, ny), (nx - 1, ny + 1)], TIP.base, name="nose")
        _eye(cv, glowfx, math.floor(H[0] + 1.6), math.floor(H[1] - 1.2), p.eye, 0)
    # near legs: stiff, splayed forward under the chin and back past the haunch
    stiff_leg((C[0] - 7.0, C[1] + 2.4), (C[0] - 17.0, g - 0.6), False, 3.2)
    stiff_leg((C[0] + 5.0, C[1] + 2.8), (C[0] + 16.5, g - 0.6), False, 2.6)
    _frost_creep(cv, p.frost, C[1] - 5.5, g)
    if p.frost >= 0.35:  # crystals growing out of the frozen body
        n = 2 if p.frost < 0.7 else 4
        for base, ang, ln, w in (((C[0] - 7.5, C[1] - 4.4), 110, 3.2, 1.1), ((C[0] - 1.5, C[1] - 3.8), 80, 2.6, 0.9),
                                 ((C[0] - 12.0, C[1] - 2.6), 145, 2.6, 0.9),
                                 ((C[0] + 12.0, C[1] - 4.4), 70, 2.4, 0.9))[:n]:
            _shard(cv, base, ang, ln, w)


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    glowfx = cv.layer(above=True, outline=False)
    if p.lying:
        _lying(cv, p, glowfx)
        return
    ground = cv.ground
    cr = p.crouch
    C = (cv.gx - 1 + p.bx, ground - 17.5 + p.by + cr)
    br = p.breathe
    st = p.stretch
    R = (C[0] - 8.4 * st, C[1] - 1.6 - p.rump)
    K = (C[0] + 7.6 * st, C[1] + 0.6)
    body_x = [px.rotate(p.pitch, C)]

    def B(pt):
        return px.rot_pt(pt, p.pitch, C)

    def foot(hx, i):
        f = p.feet[i]
        return (hx + f[0], ground - f[1])

    hips = {"nf": (K[0] + 0.6, K[1] + 4.2), "ff": (K[0] + 2.8, K[1] + 3.8),
            "nh": (R[0] + 0.6, R[1] + 3.4), "fh": (R[0] + 2.8, R[1] + 3.0)}
    _front_leg(cv, B(hips["ff"]), foot(hips["ff"][0] + 0.6, 1), True, claws=p.claws)
    _hind_leg(cv, B(hips["fh"]), foot(hips["fh"][0] + 1.2, 3), True, cr, p.feet[3][1])
    N0 = (K[0] + 3.0, K[1] - 3.8)
    with cv.xform(*body_x):
        with cv.xform(px.rotate(p.head, N0)):
            H = (N0[0] + 4.6, N0[1] - 3.8 + cr * 0.15)
            _ear(cv, H, p.ear, True)
        _tail(cv, (R[0] - 5.2, R[1] - 3.2), p)
    _hind_leg(cv, B(hips["nh"]), foot(hips["nh"][0] + 1.0, 2), False, cr, p.feet[2][1])
    with cv.xform(*body_x):
        body_g = [cv.geom_ellipse(R[0], R[1] + 0.2, 6.4, 6.4 + br * 0.3, angle=8),
                  cv.geom_limb([(R[0] + 2.5, R[1] - 0.2), (C[0] + 0.2, C[1] - 1.0 - br * 0.4), (K[0] - 2.4, K[1] - 0.6)],
                               [5.2, 4.4 + br * 0.4, 5.4]),
                  cv.geom_ellipse(K[0], K[1] + 0.4, 6.2, 6.2 + br, angle=12)]
        with cv.xform(px.rotate(p.head, N0)):
            if p.jaw > 0.05:  # lower jaw drops open, fangs showing
                with cv.xform(px.rotate(-32 * p.jaw, (H[0] + 1.8, H[1] + 2.4))):
                    cv.limb([(H[0] + 1.8, H[1] + 2.8), (H[0] + 6.0, H[1] + 3.2)], [1.9, 1.2], FUR, shade="nolight",
                            name="jaw")
                    cv.pixel(math.floor(H[0] + 5.0), math.floor(H[1] + 1.8), BELLY.light, name="tooth")
            head_g = [cv.geom_limb([N0, H], [5.0, 4.4]), cv.geom_ellipse(H[0], H[1], 5.7, 5.2),
                      cv.geom_limb([(H[0] + 2.4, H[1] + 1.4), (H[0] + 5.2, H[1] + 2.0)], [3.0, 2.2])]
        cv.draw_geom(cv.union(*body_g, *head_g, weights=[0.95, 0.8, 1.0, 0.6, 0.9, 0.7]), FUR, name="body",
                     sep="deep")
        # cream belly and chest bib, faint rosettes
        cv.limb([(R[0] + 1.0, R[1] + 5.6), (C[0], C[1] + 3.6), (K[0] + 1.0, K[1] + 6.2)], [1.3, 1.5, 2.2], BELLY,
                shade="two", decal=True, clip="body")
        cv.ellipse(K[0] + 4.4, K[1] + 1.6, 2.3, 4.2, BELLY, angle=10, shade="soft", decal=True, clip="body")
        _rosettes(cv, C, st)
        # rime crystals on the shoulders
        for base, ang, ln, w in (((K[0] - 3.2, K[1] - 4.4), 128, 2.8, 0.9), ((K[0] - 0.8, K[1] - 5.2), 108, 4.0, 1.2),
                                 ((K[0] + 1.6, K[1] - 4.6), 88, 2.6, 0.9)):
            _shard(cv, base, ang, ln, w)
        with cv.xform(px.rotate(p.head, N0)):
            _ruff(cv, H)
            _ear(cv, H, p.ear, False)
            cv.ellipse(H[0] + 4.6, H[1] + 2.8, 2.8, 1.4, BELLY, shade="soft", decal=True, clip="body")
            nx, ny = math.floor(H[0] + 7.2), math.floor(H[1] + 1.0)
            cv.pixels([(nx - 1, ny), (nx - 2, ny), (nx - 1, ny + 1)], TIP.base, name="nose")
            if p.jaw <= 0.05:
                cv.line((nx - 4, ny + 2), (nx - 2, ny + 2), FUR.deep, name="mouth")
            else:
                cv.pixel(nx - 3, ny + 2, TIP.deep, name="mouth")
            _eye(cv, glowfx, math.floor(H[0] + 1.6), math.floor(H[1] - 1.2), p.eye, p.glow)
            mouth = cv.tp((H[0] + 7.4, H[1] + 2.6))
    claw_at = _front_leg(cv, B(hips["nf"]), foot(hips["nf"][0] + 0.2, 0), False, claws=p.claws, sep="deep")

    if p.frost > 0:
        _frost_creep(cv, p.frost, C[1] - 8.0, ground)
    if p.breath is not None:
        _breath(cv.layer(above=True, outline=True), mouth, p.breath)
    if p.slash is not None:
        top = cv.layer(above=True, outline=False)
        _slash(top, (claw_at[0] + 2.0, claw_at[1]), p.slash)
        if p.hit:
            px.impact(top, claw_at[0] + 2.0, claw_at[1] - 1.0, size=3, color=EYE_V, core=px.GLINT)
