"""Nest guardian - a heavy six-legged guardian beast of the wyrm nests (Earth / Star, large).

View: side, facing right.  ~70 art px from the tail club to the snout, ~40 px tall to the
crystal tips, on a 96 px canvas (cell 192).  A stocky lizard-tortoise: low slate-indigo hide
speckled with star scales, a banded carapace of dark bronze plates running the length of its
back with glowing star crystals growing from the ridge, a blunt head under a horned bronze
helm, a thick tail ending in a bronze club.
Parts, back to front: far legs (dark, set forward so all six read), tail + club, pale sand
belly, near hind and middle legs, body + thick neck as one form (pale plastron edge, star-speck
scales), the bronze carapace (five domed plates, each riding over the one behind, a scalloped
rim band with rivets), the crystal clusters on the ridge (each a lit facet and a teal-shaded
facet), blunt head (hinged jaw, helm plate, forward brow horn, swept cheek horn, glowing gold
eye), near foreleg.  FX: crystal twinkles, dust, the stomp burst (flash, shards, ground ring).
Idle: slow breathing, the head nods, the crystals twinkle in turn.  Walk: a heavy tripod gait
(near fore + far middle + near hind swap with the other three) with a body roll.  Windup:
rears its front up on the hind legs, tail club raised high behind, jaws open, the crystals
flare (held).  Attack: slams the forelegs down in a stomp; on the hit frame (1) a burst of
star light, flying crystal shards and a dust ring.  Hurt: recoils, eyes shut, crystals
flicker.  Death: the legs buckle, it collapses onto its belly and the crystals go dark.
"""
import math

import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "nest_guardian",
    "cell": 192,
    "anchor": [96, 168],
    "flying": False,
    "hit_frame": 1,
}

# ---- palette: slate-indigo star-scaled hide, dark bronze plates, pale star crystals, sand belly
HIDE = px.material("ng_hide", "#a3a8d2", "#6d72a3", "#4a4e7c", "#2f3158", outline="#0b0c1d",
                   thresholds=(0.88, 0.54, 0.2))
BRONZE = px.material("ng_bronze", "#c98f4c", "#85572d", "#5a3a24", "#39241e", outline="#140b09",
                     thresholds=(0.86, 0.5, 0.16))
BELLY = px.material("ng_belly", "#f2e2b4", "#d4b983", "#a88c62", "#75604a", outline="#15110d")
HORN = px.material("ng_horn", "#f6ecc8", "#d2bf8e", "#9c8a64", "#675a45", outline="#17130d")
CRYSTAL = px.material("ng_crystal", "#ffffff", "#fff0b8", "#8fdcdc", "#3f8f9e", outline="#0b2228")
CRYSTAL_HOT = px.material("ng_crystal_hot", "#ffffff", "#ffffff", "#fff0b8", "#8fdcdc", outline="#15313a")
CRYSTAL_DIM = px.material("ng_crystal_dim", "#b4bcc6", "#7e8a98", "#58626f", "#3a414c", outline="#0d1116")
STAR_SPECK = px.rgb("#c9c8f0")
EYE_GOLD = px.rgb("#ffd45a")
MOUTH = px.rgb("#2a1420")
TWINKLE = px.rgb("#fff6c8")

# ---- poses --------------------------------------------------------------------------------
# bx, by    body offset          rear  front lifted about the hind feet (deg)     sq  squash
# roll      small body tilt (deg)   breathe  0..1 swell    head  head tilt (deg)  jaw  gape 0..1
# feet      (dx, lift) near-fore, near-mid, near-hind, far-fore, far-mid, far-hind
# tail      tail raise (deg, + = club up)   eye  open|angry|squeeze|closed|dead
# glow      crystals: 0 dark, 1 dim, 2 normal, 3 flared    twk  twinkle step
# dust      dust life (None = off)   burst  stomp burst life (None = off)
# sink      0..1 legs buckled (death)   fade  opacity
DEFAULTS = dict(bx=0, by=0, rear=0, sq=1.0, roll=0, breathe=0.0, head=0, jaw=0.0, feet=((0, 0),) * 6, tail=0,
                eye="open", glow=2, twk=0, dust=None, burst=None, sink=0.0, fade=1.0, hit=False)

TAU = 2 * math.pi


def _tripod(i):
    """Walk frame i: tripod A (near fore, far mid, near hind) swaps with tripod B."""
    ph = TAU * i / 6

    def leg(off):
        a = ph + off
        return (round(3.0 * math.cos(a), 1), round(max(0.0, 3.0 * math.sin(a)), 1))

    A, B = leg(0.0), leg(math.pi)
    return (A, B, A, B, A, B)


POSE = px.poses(DEFAULTS, {
    "idle": [  # slow breaths, the head nods, crystals twinkle in turn
        dict(twk=0),
        dict(breathe=0.5, head=-2, twk=1),
        dict(breathe=1.0, head=-3, twk=2, tail=2),
        dict(breathe=0.5, head=-1, twk=3, tail=1),
    ],
    "walk": [  # heavy tripod gait with a body roll
        dict(feet=_tripod(0), roll=0.0, twk=0, head=1),
        dict(feet=_tripod(1), roll=-1.0, by=-1, twk=1, head=2, tail=2),
        dict(feet=_tripod(2), roll=-1.0, twk=2, head=1, tail=3),
        dict(feet=_tripod(3), roll=0.0, twk=3, head=0, tail=2),
        dict(feet=_tripod(4), roll=1.0, by=-1, twk=4, head=1),
        dict(feet=_tripod(5), roll=1.0, twk=5, head=2, tail=-1),
    ],
    "windup": [  # rears the front up on the hind legs, club raised high, jaws open, crystals flare - held
        dict(rear=6, feet=((1, 2), (0, 1), (0, 0), (1, 2), (0, 1), (0, 0)), head=6, jaw=0.3, tail=30, eye="angry",
             glow=3, twk=1, dust=0.15),
        dict(rear=12, feet=((2, 4), (1, 2), (0, 0), (2, 4), (1, 2), (0, 0)), head=10, jaw=0.7, tail=56,
             eye="angry", glow=3, twk=2, dust=0.4),
        dict(rear=15, feet=((2, 5), (1, 3), (0, 0), (2, 5), (1, 3), (0, 0)), head=12, jaw=0.9, tail=68,
             eye="angry", glow=3, twk=3, dust=0.6),
    ],
    "attack": [  # slams the forelegs down: the stomp lands on frame 1 with a burst of star light
        dict(rear=5, feet=((3, 2), (1, 1), (0, 0), (3, 2), (1, 1), (0, 0)), head=-4, jaw=0.9, tail=36,
             eye="angry", glow=3, twk=0),
        dict(sq=0.94, by=1, rear=-1, feet=((5, 0), (1, 0), (0, 0), (5, 0), (1, 0), (0, 0)), head=2, jaw=1.0,
             tail=4, eye="angry", glow=3, burst=0.15, hit=True, twk=1),
        dict(sq=0.97, feet=((5, 0), (1, 0), (0, 0), (5, 0), (1, 0), (0, 0)), head=-3, jaw=0.5, tail=0,
             eye="angry", glow=2, burst=0.5, twk=2),
        dict(feet=((2, 0), (0, 0), (0, 0), (2, 0), (0, 0), (0, 0)), head=-1, tail=2, burst=0.85, twk=3),
    ],
    "hurt": [  # recoils: head up and back, eyes shut, crystals flicker
        dict(bx=-3, rear=4, head=12, jaw=0.4, eye="squeeze", feet=((1, 2), (0, 1), (0, 0), (1, 2), (0, 0), (0, 0)),
             tail=10, glow=1),
        dict(bx=-2, rear=2, head=6, jaw=0.2, eye="squeeze", tail=5, glow=2),
    ],
    "death": [  # the legs buckle, it collapses onto its belly and the crystals go dark
        dict(bx=-3, rear=4, head=12, jaw=0.4, eye="squeeze", feet=((1, 2), (0, 1), (0, 0), (1, 2), (0, 0), (0, 0)),
             tail=10, glow=1),
        dict(bx=-3, head=-6, jaw=0.3, eye="squeeze", sink=0.45, tail=-2, glow=1),
        dict(bx=-3, head=-14, jaw=0.2, eye="dead", sink=1.0, tail=-8, glow=1, dust=0.3),
        dict(bx=-3, head=-16, jaw=0.1, eye="dead", sink=1.0, tail=-10, glow=0, dust=0.7),
        dict(bx=-3, head=-16, jaw=0.1, eye="dead", sink=1.0, tail=-10, glow=0, fade=0.6),
    ],
})

# legs: name, hip offset from B, default foot x offset from B, radius scale, far?
LEGS = (
    ("nf", (12.5, 6.0), 14.5, 0.95, False),
    ("nm", (0.0, 7.0), 0.5, 0.85, False),
    ("nh", (-12.0, 6.0), -13.5, 1.0, False),
    ("ff", (17.0, 4.0), 21.0, 0.9, True),
    ("fm", (5.5, 5.0), 7.5, 0.8, True),
    ("fh", (-6.5, 4.5), -6.0, 0.95, True),
)
# crystal clusters on the ridge: (x offset along the shell, main height, lean deg, small crystal side)
CLUSTERS = ((-15.0, 5.0, 20, 1), (-6.5, 7.5, 10, -1), (2.5, 8.0, 2, 1), (11.0, 5.5, -8, -1))


# ---- parts ----------------------------------------------------------------------------------
def _leg(cv, hip, foot, far, k, sink):
    mat_shade = "dark" if far else "two"
    fx, fy = foot
    if sink > 0:  # buckled: the knee splays out, the foot slides flat under it
        knee = (hip[0] + 3.0 * sink + (fx - hip[0]) * 0.4, hip[1] + (fy - hip[1]) * (0.6 - 0.25 * sink))
    else:
        knee = (hip[0] + (fx - hip[0]) * 0.5 + 1.8, hip[1] + (fy - hip[1]) * 0.5)
    cv.limb([hip, knee, (fx, fy - 2.2)], [4.2 * k, 3.2 * k, 2.8 * k], HIDE, shade=mat_shade, name="leg",
            sep=False if far else "deep")
    cv.ellipse(fx + 1.0, fy - 1.3, 3.6 * k, 1.8, HIDE, shade="dark" if far else "two", name="foot")
    if not far:
        cv.limb([(knee[0] - 2.4, knee[1] - 0.6), (knee[0] + 2.4, knee[1] + 0.4)], 0.5, HIDE.step(1), decal=True,
                clip="leg")
        for j in range(3):  # pale claws
            cv.pixel(math.floor(fx + 2.0 + j * 1.5), math.floor(fy - 1.0), HORN.base, name="claw")


def _crystal(cv, base, ang, h, w, mat, name="crystal"):
    """A faceted crystal growing from ``base`` along ``ang`` (deg, 90 = up): the facet facing
    the upper-left light is lit, the other shaded."""
    tip = px.polar(base, ang, h)
    mid = px.polar(base, ang, h * 0.45)
    l = px.polar(mid, ang + 90, w)
    r = px.polar(mid, ang - 90, w)
    b0 = px.polar(base, ang + 90, w * 0.55)
    b1 = px.polar(base, ang - 90, w * 0.55)
    cv.polygon([tip, l, b0, base], mat, shade=0, name=name)
    cv.polygon([tip, base, b1, r], mat, shade=2, name=name)
    cv.line((math.floor(base[0]), math.floor(base[1])), (math.floor(tip[0]), math.floor(tip[1])), mat.base,
            decal=True, name=name)
    return tip


def _shell(cv, B, p):
    """The carapace: five domed dark-bronze plates overlapping front over back along the spine,
    a dark scalloped rim with rivets, and the crystal clusters growing from the ridge."""
    br = p.breathe
    S = (B[0] - 1.0, B[1] + 3.5)
    rx, ry = 22.5, 15.0 + 0.5 * br

    def env(x):  # height of the carapace above S at x
        u = max(-1.0, min(1.0, (x - S[0]) / rx))
        return ry * max(0.0, 1 - u * u) ** 0.42

    top = [(S[0] + rx * math.cos(math.pi * i / 24), S[1] - env(S[0] + rx * math.cos(math.pi * i / 24)))
           for i in range(25)]
    envelope = cv.mask_polygon(top + [(S[0] - rx, S[1] + 3.0), (S[0] + rx, S[1] + 3.0)])
    n = 5
    w = 2 * rx / n
    for j in range(n):  # back (tail) to front: each plate's rear edge rides over the one behind
        cx = S[0] - rx + w * (j + 0.5)
        h = env(cx) + 2.0
        g = cv.geom_ellipse(cx + 0.8, S[1] + 1.0, w * 0.5 + 2.4, h)
        cv.draw_geom((g[0] & envelope,) + g[1:], BRONZE, name="shell", sep="deep" if j else False)
    # the dark rim band along the bottom with rivets and a scalloped edge
    rim = []
    xs = [S[0] - rx + 1 + j * (2 * rx - 2) / 5 for j in range(6)]
    for j in range(5):
        a_, b_ = xs[j], xs[j + 1]
        rim += [(a_, S[1] - 1.0), ((a_ + b_) / 2, S[1] + 2.8), (b_, S[1] - 1.0)]
    cv.polygon([(S[0] - rx - 1.5, S[1] - 2.0), (S[0] + rx + 1.5, S[1] - 2.0), (S[0] + rx + 1.5, S[1] - 0.8)]
               + rim[::-1] + [(S[0] - rx - 1.5, S[1] - 0.8)], BRONZE.step(1), shade="two", name="rim", sep="deep")
    for j in range(5):
        x = (xs[j] + xs[j + 1]) / 2
        cv.pixel(math.floor(x), math.floor(S[1] - 1.0), BRONZE.light, name="rim")
    # crystal clusters along the ridge
    mat = {0: CRYSTAL_DIM, 1: CRYSTAL_DIM, 2: CRYSTAL, 3: CRYSTAL_HOT}[p.glow]
    tips = []
    for (ox, h, lean, side) in CLUSTERS:
        base = (S[0] + ox, S[1] - env(S[0] + ox) + 1.6)
        _crystal(cv, (base[0] - side * 2.2, base[1] + 0.8), 90 + lean + side * 24, h * 0.5, 1.3, mat)
        tips.append(_crystal(cv, base, 90 + lean, h, 1.9, mat))
    return tips


def _head(cv, N0, H, p):
    """Blunt head under a horned bronze helm (the neck is part of the body form); returns the
    snout tip."""
    with cv.xform(px.rotate(p.head, (H[0] - 3.0, H[1] + 1.0))):
        hinge = (H[0] - 1.5, H[1] + 2.2)
        jaw_a = -28 * p.jaw
        # lower jaw first (the skull overlaps its root); it drops open about the hinge
        with cv.xform(px.rotate(jaw_a, hinge)):
            cv.limb([hinge, (H[0] + 4.0, H[1] + 3.4), (H[0] + 7.4, H[1] + 3.0)], [2.8, 2.2, 1.6], HIDE,
                    shade="nolight", name="jaw")
            if p.jaw > 0.2:
                cv.pixel(math.floor(H[0] + 5.5), math.floor(H[1] + 1.8), HORN.light, name="tooth")
        skull = cv.geom_ellipse(H[0], H[1] - 0.4, 6.0, 4.8)
        snout = cv.geom_limb([(H[0] + 1.6, H[1] + 0.4), (H[0] + 7.2, H[1] + 1.2)], [3.6, 2.8])
        cut = cv.mask_polygon([(hinge[0], hinge[1]), (H[0] + 14, hinge[1] - 0.4), (H[0] + 14, H[1] + 12),
                               (hinge[0], H[1] + 12)]) if p.jaw > 0.2 else None
        cv.draw_geom(cv.union(skull, snout, weights=[1.0, 0.85]), HIDE, name="head", sep="deep", minus=cut)
        if p.jaw > 0.2:  # dark mouth between the jaws
            lo = px.rot_pt((H[0] + 7.0, hinge[1] + 0.4), jaw_a, hinge)
            cv.polygon([(hinge[0] - 0.5, hinge[1] - 0.2), (H[0] + 8.0, hinge[1] - 0.2), lo], px.flat(MOUTH),
                       under=True, name="mouth")
        else:
            cv.line((math.floor(hinge[0] + 1), math.floor(hinge[1])), (math.floor(H[0] + 7.0), math.floor(hinge[1])),
                    HIDE.step(2), decal=True, clip="head", name="head")
        cv.pixel(math.floor(H[0] + 7.4), math.floor(H[1] - 0.4), HIDE.deep, name="nostril")
        # swept cheek horn behind, the bronze helm over the skull, the forward brow horn
        cv.limb([(H[0] - 2.4, H[1] - 1.0), (H[0] - 7.0, H[1] - 3.0), (H[0] - 9.6, H[1] - 2.2)], [1.9, 1.2, 0.5],
                HORN, shade="two", name="horn", sep="deep")
        helm = [(H[0] - 5.6, H[1] - 0.4), (H[0] - 4.8, H[1] - 4.2), (H[0] - 1.0, H[1] - 5.8), (H[0] + 3.4, H[1] - 5.0),
                (H[0] + 5.6, H[1] - 2.6), (H[0] + 3.2, H[1] - 2.2), (H[0] + 0.6, H[1] - 2.8), (H[0] - 2.4, H[1] - 1.0)]
        cv.polygon(helm, BRONZE, name="helm", sep="deep")
        cv.pixels([(math.floor(H[0] - 3.0), math.floor(H[1] - 3.0)), (math.floor(H[0] + 0.5), math.floor(H[1] - 4.2))],
                  BRONZE.light, name="helm")
        horn_tip = (H[0] + 7.8, H[1] - 9.0)
        cv.limb([(H[0] + 3.2, H[1] - 3.8), (H[0] + 5.8, H[1] - 6.4), horn_tip], [2.1, 1.4, 0.5], HORN, shade="two",
                name="horn", sep="deep")
        # glowing gold eye tucked under the helm brow
        ex, ey = math.floor(H[0] + 1.4), math.floor(H[1] - 1.8)
        if p.eye == "squeeze":
            cv.stamp(["kk.", "..k"], ex - 1, ey, {"k": px.INK}, name="eye")
        elif p.eye == "dead":
            cv.stamp(["k.k", ".k.", "k.k"], ex - 1, ey - 1, {"k": px.INK}, name="eye")
        elif p.eye == "closed":
            cv.stamp(["kkk"], ex - 1, ey + 1, {"k": px.INK}, name="eye")
        else:
            cv.stamp(["gi", "ik"], ex, ey, {"g": px.GLINT, "i": EYE_GOLD, "k": px.INK}, name="eye")
            if p.eye == "angry":  # the helm brow comes down toward the snout
                cv.pixels([(ex - 1, ey - 1), (ex, ey - 1), (ex + 1, ey - 1), (ex + 2, ey)], BRONZE.deep, name="brow")
        return cv.tp((H[0] + 8.5, H[1] + 1.5))


def _tail(cv, root, p):
    """Thick tapering tail with bronze bands, ending in a round bronze club (raised by p.tail)."""
    with cv.xform(px.rotate(-p.tail, root)):
        pts = [root, (root[0] - 5.0, root[1] + 1.6), (root[0] - 9.0, root[1] + 1.8), (root[0] - 11.5, root[1] + 1.2)]
        cv.limb(pts, [5.2, 3.8, 2.9, 2.5], HIDE, shade="full", name="tail")
        for q in pts[1:3]:
            cv.limb([(q[0] + 0.5, q[1] - 4.0), (q[0] - 0.5, q[1] + 4.0)], 0.9, BRONZE, shade="two", decal=True,
                    clip="tail", name="tail")
        club = (root[0] - 15.0, root[1] + 0.8)
        cv.ellipse(club[0], club[1], 5.2, 4.6, BRONZE, name="club", sep="deep")
        cv.limb([(club[0] - 3.4, club[1] - 1.6), (club[0] + 1.8, club[1] - 2.6)], 0.5, BRONZE.step(1), decal=True,
                clip="club", name="club")
        mat = {0: CRYSTAL_DIM, 1: CRYSTAL_DIM, 2: CRYSTAL, 3: CRYSTAL_HOT}[p.glow]
        _crystal(cv, (club[0] - 1.0, club[1] - 3.4), 120, 3.6, 1.2, mat)
        return cv.tp(club)


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    ground = cv.ground
    sk = p.sink
    B = (cv.gx + 2.0 + p.bx, ground - 17.0 + p.by + sk * 6.0)
    pivot = (B[0] - 14.0, ground)
    xf = [px.scale(1.0, p.sq, (B[0], ground)), px.rotate(p.rear + p.roll, pivot)]
    cv.snap_ground = sk > 0.5
    back = cv.layer(above=False, outline=True)
    feet_at = {}
    with cv.xform(*xf):
        hips = {name: cv.tp((B[0] + h[0], B[1] + h[1])) for name, h, fx0, k, far in LEGS}
        for i, (name, h, fx0, k, far) in enumerate(LEGS):
            dx, lift = p.feet[i]
            if p.rear > 0 and name[1] in "fm":  # the fore and middle legs hang from the reared body
                feet_at[name] = cv.tp((B[0] + fx0 + dx, ground - lift * 0.6))
            else:
                feet_at[name] = None
    for i, (name, h, fx0, k, far) in enumerate(LEGS):
        if feet_at[name] is None:
            dx, lift = p.feet[i]
            spread = sk * (2.5 if name[1] == "f" else (-2.5 if name[1] == "h" else 0.0))
            feet_at[name] = (B[0] + fx0 + dx + spread, ground - lift)
    for name, h, fx0, k, far in LEGS:
        if far:
            _leg(cv, hips[name], feet_at[name], True, k, sk)
    with cv.xform(*xf):
        club = _tail(cv, (B[0] - 19.0, B[1] + 2.0), p)
        cv.ellipse(B[0] + 1.0, B[1] + 6.0, 19.0, 4.6, BELLY, shade="two", name="belly")
    for name in ("nh", "nm"):
        _leg(cv, hips[name], feet_at[name], False, dict((n, k) for n, _, _, k, _ in LEGS)[name], sk)
    with cv.xform(*xf):
        N0 = (B[0] + 17.0, B[1] + 1.0)
        H = (B[0] + 25.0, B[1] - 2.0)
        neck = cv.geom_limb([(B[0] + 12.0, B[1] + 1.5), N0, (H[0] - 3.0, H[1] + 1.0)], [8.0, 5.6, 4.4])
        body = cv.union(cv.geom_ellipse(B[0] - 11.0, B[1] + 1.0, 11.5, 9.5 + p.breathe * 0.4),
                        cv.geom_ellipse(B[0], B[1], 14.0, 10.0 + p.breathe * 0.5),
                        cv.geom_ellipse(B[0] + 11.5, B[1] + 1.5, 9.5, 8.8), neck,
                        weights=[1.0, 1.0, 1.0, 0.8])
        cv.draw_geom(body, HIDE, name="body", sep="deep")
        cv.ellipse(B[0] + 1.0, B[1] + 8.4, 17.5, 2.4, BELLY, shade="two", clip="body", name="body")
        # star scales: pale specks scattered over the flank and neck
        for j, (sx, sy) in enumerate(((-15, 5), (-8, 6), (-1, 5), (6, 6), (12, 5), (18, 2), (-11, 8), (3, 8))):
            cv.pixel(math.floor(B[0] + sx), math.floor(B[1] + sy), STAR_SPECK, name="speck", decal=True)
        tips = _shell(cv, B, p)
        snout = _head(cv, N0, H, p)
    _leg(cv, hips["nf"], feet_at["nf"], False, 1.0, sk)

    # ---- FX ------------------------------------------------------------------------------------
    fx = cv.layer(above=True, outline=False)
    if p.glow >= 2:  # crystals twinkle in turn (all of them when flared)
        for j, t in enumerate(tips):
            if p.glow == 3 or j == p.twk % len(tips):
                x, y = math.floor(t[0]), math.floor(t[1]) - 1
                fx.pixels([(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)], TWINKLE, name="twinkle")
                fx.pixel(x, y, px.GLINT, name="twinkle")
                if p.glow == 3 and j % 2 == 0:
                    fx.pixels([(x - 2, y), (x + 2, y), (x, y - 2)], CRYSTAL.shadow, name="twinkle")
    if p.dust is not None:
        dl = cv.layer(above=True, outline=True)
        if sk > 0:
            px.dust(dl, B[0] - 16.0, cv.gy - 1, p.dust, size=1.0, direction=-1)
            px.dust(dl, B[0] + 18.0, cv.gy - 1, p.dust, size=0.9, direction=1)
        else:  # the hind feet dig in as it rears
            px.dust(dl, feet_at["nh"][0] - 2.0, cv.gy - 1, p.dust, size=0.9, direction=-1)
    if p.burst is not None:
        _burst(cv, (feet_at["nf"][0] + 6.0, cv.gy - 1.0), p.burst, p.hit)


def _burst(cv, F, t, hit):
    """The stomp: a flash of star light, crystal shards flung up and out, a ring of light and
    dust racing away along the ground."""
    ring = cv.layer(above=False, outline=False)
    rx, ry = 6.0 + 16.0 * t, 1.6 + 1.2 * t
    outer = ((ring.X - F[0]) / rx) ** 2 + ((ring.Y - F[1] + 0.5) / ry) ** 2 <= 1.0
    inner = ((ring.X - F[0]) / max(1.0, rx - 1.6)) ** 2 + ((ring.Y - F[1] + 0.5) / max(0.6, ry - 0.9)) ** 2 <= 1.0
    m = outer & ~inner & (ring.Y < F[1] + 0.5)
    if t < 0.95:
        ring.fill(m, px.flat(CRYSTAL.shadow), shade="flat", name="ring")
    dl = cv.layer(above=True, outline=True)
    for d, sz, reach in ((-1, 0.8, 12.0), (1, 0.9, 6.0)):
        px.dust(dl, F[0] + d * (4 + reach * t), F[1], min(1.0, t * 1.1), size=sz, direction=d)
    sh = cv.layer(above=True, outline=True)
    for j, (ang, v) in enumerate(((62, 1.0), (100, 0.75), (35, 0.8), (128, 0.6))):
        r = 6.0 + 12.0 * t * v
        q = px.polar((F[0], F[1] - 3.0), ang, r)
        q = (q[0], q[1] + 9.0 * t * t)  # they arc up and fall back
        if q[1] < F[1] - 3:
            _crystal(sh, q, ang + 50 * t, 3.0, 1.1, CRYSTAL, name="shard")
    top = cv.layer(above=True, outline=False)
    if hit:  # a flash of star light where the foot lands
        c = (F[0] + 2, F[1] - 7)
        px.impact(top, c[0], c[1], size=6, color=TWINKLE, core=px.GLINT)
        px.glow_ring(top, c[0] + 0.5, c[1] + 0.5, 6.5, CRYSTAL.shadow, thickness=1.0)
        for ang in (30, 150, 210, 330):
            q = px.polar((c[0] + 0.5, c[1] + 0.5), ang, 9.5)
            top.line((math.floor(q[0]), math.floor(q[1])), (math.floor(q[0]) + (1 if ang < 90 or ang > 270 else -1),
                     math.floor(q[1]) + (1 if ang > 180 else -1)), TWINKLE, name="ray")
