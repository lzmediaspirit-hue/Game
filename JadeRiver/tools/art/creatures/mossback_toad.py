"""Mossback toad - fat, warty marsh toad with a garden of moss and tiny ferns growing
on its back (Wood element).

View: side, facing right.  ~20 art px tall (ferns included), ~26 long.
Parts, back to front: far legs (dark), body (fat rump + head + wide flat snout +
parotoid ridge + eye bump as one form), cream belly, warts, moss mats (decals) and
moss tufts breaking the back line, fern fronds swaying on the back, wide down-turned
mouth, puffing throat / cheek sac, near hind leg (thick Z fold via ``px.ik2``), near
foreleg, golden eye with a slit pupil under a heavy lid.  Attack: a long sticky
tongue lashes out to the right edge of the cell (ranged).
"""
import math

import helpers_batch_a as hb
import pixel as px

SPEC = {
    "id": "mossback_toad",
    "cell": 128,
    "anchor": [64, 112],
    "flying": False,
    "hit_frame": 1,
    "airborne": [["walk", 2], ["walk", 3]],
}

# ---- palette: earthy olive-brown hide, cream belly, Wood moss greens, pink tongue --------
HIDE = px.material("toad_hide", "#b9a66a", "#877a4a", "#5d5637", "#3b3a2a", outline="#10110b",
                   thresholds=(0.86, 0.5, 0.18))
BELLY = px.material("toad_belly", "#f3e6b8", "#d9c690", "#aa9870", "#766a55", outline="#10110b")
LEG = px.material("toad_leg", "#c9b67a", "#998a55", "#6a6040", "#44412f", outline="#10110b",
                  thresholds=(0.8, 0.45, 0.15))
MOSS = px.material("toad_moss", "#b6d86a", "#78a845", "#4d7c38", "#2f5230", outline="#0b1810")
FERN = px.material("toad_fern", "#c2e27a", "#7fb04c", "#4f8440", "#2f5a36", outline="#1c3a26")
WART = px.rgb("#cdbb80")
SPOT = HIDE.step(1)
TONGUE = px.material("toad_tongue", "#f6b7b0", "#e0827f", "#b0565f", "#733946", outline="#1f0c10")
SAC = px.material("toad_sac", "#fffae0", "#f2e3b2", "#d6c28e", "#ad9a70", outline="#10110b")
MOUTH_IN = px.rgb("#35191e")
IRIS = px.rgb("#f2c145")

# ---- poses --------------------------------------------------------------------------------
# bx, by  body offset    rot  pitch (deg)   sq  squash about the ground (weight)
# hind    None = sitting | (ankle dx, dy, toe dx, dy) from the hip      front  None | (dx, dy)
# puff    throat/cheek sac 0..1    jaw  mouth gape 0..1   tongue  tongue reach 0..1 (None = off)
# fern    frond sway phase         eye  open|angry|squeeze|dead          flip  on its back
DEFAULTS = dict(bx=0, by=0, rot=0, sq=1.0, hind=None, front=None, puff=0.0, jaw=0.0, tongue=None, fern=0.0,
                eye="open", flip=False, fade=1.0, dust=None, hit=False, breathe=0.0)

POSE = px.poses(DEFAULTS, {
    "idle": [  # heavy breathing, throat flutter, ferns sway
        dict(fern=0.0),
        dict(fern=1.0, breathe=0.4, puff=0.15),
        dict(fern=2.0, breathe=0.7, puff=0.25),
        dict(fern=3.0, breathe=0.3, puff=0.1),
    ],
    "walk": [  # short heavy hop: squat, shove, hang, drop, splat, settle
        dict(sq=0.94, fern=0.0),
        dict(bx=1, rot=10, hind=(-7.0, 4.5, -10.0, 6.0), front=(1.5, 3.5), fern=1.0, dust=0.1),
        dict(bx=3, by=-4, rot=6, hind=(-7.5, 3.0, -10.5, 3.5), front=(3.0, 3.0), fern=2.0),
        dict(bx=4, by=-2, rot=-6, hind=(-5.0, 3.5, -1.5, 4.0), front=(2.5, 4.5), fern=3.0),
        dict(bx=4, sq=0.9, fern=4.0, dust=0.3),
        dict(bx=2, sq=0.97, fern=5.0, dust=0.6),
    ],
    "windup": [  # cheeks and throat puff up, eyes narrow, leans back - held
        dict(puff=0.45, eye="angry", rot=3, fern=1.0),
        dict(puff=0.8, eye="angry", rot=6, bx=-1, fern=2.0),
        dict(puff=1.0, eye="angry", rot=7, bx=-1, fern=2.5, breathe=0.5),
    ],
    "attack": [  # tongue lash: gape, tongue snaps to the right edge (hit), reels back, gulp
        dict(jaw=1.0, tongue=0.35, eye="angry", rot=2, puff=0.3, fern=3.0),
        dict(jaw=1.0, tongue=1.0, eye="angry", rot=-2, bx=1, hit=True, fern=3.5),
        dict(jaw=0.7, tongue=0.45, eye="angry", rot=0, fern=4.0),
        dict(jaw=0.0, puff=0.3, fern=4.5),
    ],
    "hurt": [
        dict(bx=-3, by=-2, rot=14, eye="squeeze", hind=(-5.0, 5.5, -1.5, 7.0), front=(2.0, 3.0), puff=0.2),
        dict(bx=-2, rot=6, eye="squeeze", sq=0.95),
    ],
    "death": [  # knocked back, rolls over, flops onto its back, legs splayed, fades
        dict(bx=-3, by=-2, rot=18, eye="squeeze", hind=(-5.0, 5.5, -1.5, 7.0), front=(2.0, 3.0), jaw=0.5),
        dict(bx=-4, rot=95, eye="dead", hind=(-6.0, 5.0, -3.0, 6.5), front=(2.5, 4.0), jaw=0.5),
        dict(bx=-4, flip=True, eye="dead", hind=(-5.5, 5.0, -8.5, 7.5), front=(2.5, 4.5), jaw=0.6),
        dict(bx=-4, flip=True, eye="dead", hind=(-6.5, 4.0, -9.5, 5.5), front=(3.0, 3.5), jaw=0.6, sq=0.95,
             fade=0.6),
        dict(bx=-4, flip=True, eye="dead", hind=(-7.0, 3.0, -10.5, 3.5), front=(3.5, 2.5), jaw=0.6, sq=0.92,
             fade=0.3),
    ],
})

HIP = (-6.0, 3.8)
SHOULDER = (4.5, 4.4)


def _hind(cv, hip, ground, p, far):
    if p.hind is None:
        ankle = (hip[0] - 1.5 + (1.2 if far else 0), ground - 1.0)
        toe = (ankle[0] + 7.0, ground - 0.6)
    else:
        ax, ay, tx, ty = p.hind
        if far:
            ax, tx = ax + 1.4, tx + 1.4
        ankle = (hip[0] + ax, hip[1] + ay)
        toe = (hip[0] + tx, hip[1] + ty)
    knee = px.ik2(hip, ankle, 5.2, 5.2, bend=1 if ankle[0] <= hip[0] + 3 else -1)
    shade = "dark" if far else "two"
    sep = False if far else "deep"
    mid = px.lerp_pt(hip, knee, 0.5)
    ang = math.degrees(math.atan2(-(knee[1] - hip[1]), knee[0] - hip[0]))
    cv.ellipse(mid[0], mid[1], 4.0, 2.7, LEG, angle=ang, shade="dark" if far else "soft", name="thigh", sep=sep)
    cv.limb([knee, ankle], [1.8, 1.3], LEG, shade=shade, name="shin", sep=sep)
    cv.limb([ankle, toe], [1.2, 0.9], LEG, shade="dark" if far else "two", name="foot")
    if not far:
        q = px.lerp_pt(hip, knee, 0.5)
        cv.pixels([(math.floor(q[0]), math.floor(q[1]) - 1), (math.floor(q[0]) - 2, math.floor(q[1]))], WART,
                  name="wart", clip="thigh")
    return toe


def _front(cv, sh, ground, p, far):
    if p.front is None:
        hand = (sh[0] + 1.5 + (1.0 if far else 0), ground - 0.6)
    else:
        hand = (sh[0] + p.front[0] + (1.0 if far else 0), sh[1] + p.front[1])
    elbow = px.ik2(sh, hand, 3.2, 3.2, bend=1)
    shade = "dark" if far else "two"
    cv.limb([sh, elbow, hand], [1.8, 1.4, 1.1], LEG, shade=shade, name="arm", sep=False if far else "deep")
    cv.limb([hand, (hand[0] + 2.0, hand[1] + 0.1)], [0.9, 0.7], LEG, shade="dark" if far else "two", name="hand")


def _eye(cv, x, y, state):
    if state == "squeeze":
        cv.stamp(["k...", ".kkk", "k..."], x, y, {"k": px.INK}, name="eye")
    elif state == "dead":
        cv.stamp(["k..k", ".kk.", ".kk.", "k..k"], x, y, {"k": px.INK}, name="eye")
    else:
        cv.stamp([".ii.", "igki", "ikki", ".ii."], x, y, {"g": px.GLINT, "i": IRIS, "k": px.INK}, name="eye")
        # heavy warty lid: straight when calm, slanting hard toward the snout when angry
        lid = [(x - 1, y - 1), (x, y - 1), (x + 1, y - 1), (x + 2, y - 1), (x + 3, y - 1)]
        if state == "angry":
            lid = [(x - 1, y - 1), (x, y - 1), (x + 1, y), (x + 2, y), (x + 3, y + 1)]
        cv.pixels(lid, HIDE.deep, name="lid")


def _fern(cv, base, sway, height, lean):
    """Tiny fern frond on an outlined layer behind the body: a thin arched stem with
    paired leaflets that shorten toward the curled tip."""
    tip = (base[0] + lean + sway, base[1] - height)
    mid = (base[0] + lean * 0.5 + sway * 0.4, base[1] - height * 0.5)
    stem = hb.catmull([base, mid, tip], per=3)
    cv.limb(stem, 0.5, FERN, shade="flat", name="fern")
    n = len(stem)
    for k in range(1, n - 1, 2):
        q = stem[k]
        ln = 1.6 * (1 - k / n) + 0.6
        for side in (-1, 1):
            cv.limb([q, (q[0] + side * ln, q[1] - 0.6 * ln)], 0.45, FERN, shade="flatlight" if side < 0 else "flat",
                    name="fern")


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    ground = cv.ground
    C = (cv.gx - 3 + p.bx, ground - 7.6 + p.by)
    cv.opacity = p.fade
    tumble = p.flip or p.rot > 60
    xf = [px.scale(1.0, p.sq, (C[0], ground)), px.rotate(p.rot, C)]
    if p.flip:
        xf = [px.scale(1.0, p.sq, (C[0], ground)), px.flip_y(C[1] - 1)]
    # the fat belly rests on the ground: keep the lowest pixel on the ground row except mid-hop
    cv.snap_ground = not (action == "walk" and frame in (2, 3))

    def lp(q):
        return (C[0] + q[0], C[1] + q[1])

    if not tumble:
        with cv.xform(*xf):
            hip, sh = cv.tp(lp(HIP)), cv.tp(lp(SHOULDER))
        _hind(cv, (hip[0] + 1.4, hip[1] - 0.8), ground, p, far=True)
        _front(cv, (sh[0] + 1.2, sh[1] - 0.6), ground, p, far=True)
    with cv.xform(*xf):
        if tumble:
            h, s_ = lp(HIP), lp(SHOULDER)
            _hind(cv, (h[0] + 1.4, h[1] - 0.8), ground, p, far=True)
            _front(cv, (s_[0] + 1.2, s_[1] - 0.6), ground, p, far=True)
        br = p.breathe
        H = (C[0] + 7.0, C[1] - 1.0)  # head centre
        # fat body, head, flat wide snout, parotoid ridge and eye bump shaded as one form
        g = cv.union(cv.geom_ellipse(C[0] - 2.5, C[1] + 0.8 - br * 0.3, 8.6, 6.8 + br * 0.5),
                     cv.geom_ellipse(H[0], H[1], 6.0, 5.0),
                     cv.geom_limb([(H[0] + 1.5, H[1] + 1.2), (H[0] + 6.4, H[1] + 1.9)], [3.6, 2.4]),
                     cv.geom_limb([(H[0] - 5.0, H[1] - 3.8), (H[0] - 1.0, H[1] - 4.2)], [1.9, 1.6]),
                     cv.geom_ellipse(H[0] + 0.8, H[1] - 4.6, 2.8, 2.3),
                     weights=[1.0, 0.85, 0.6, 0.55, 0.7])
        flat = cv.mask_polygon([(C[0] - 20, C[1] + 7.7), (C[0] + 20, C[1] + 7.7), (C[0] + 20, C[1] + 20),
                                (C[0] - 20, C[1] + 20)])
        cv.draw_geom(g, HIDE, name="body", sep="deep", minus=flat)
        # cream belly and throat
        cv.ellipse(H[0] + 0.5, H[1] + 4.6, 5.0, 2.0, BELLY, shade="two", decal=True, clip="body")
        # dark blotches and pale warts
        for (sx, sy) in ((-7.5, 0.5), (-2.5, 1.0), (H[0] - C[0] - 3.0, -2.5)):
            x, y = math.floor(C[0] + sx), math.floor(C[1] + sy)
            cv.pixels([(x, y), (x + 1, y)], WART, name="wart", clip="body")
        # moss mats over the back (decals keep the body's light bands)
        for (mx, my, rx, ry) in ((-5.5, -4.8, 4.8, 2.4), (0.5, -5.6, 3.8, 2.0), (-10.0, -1.5, 1.8, 2.6)):
            cv.ellipse(C[0] + mx, C[1] + my - br * 0.3, rx, ry, MOSS, decal=True, clip="body")
        if not p.flip:
            # moss tufts breaking the back line
            for (mx, my) in ((-8.5, -5.0), (-6.0, -6.8), (-2.0, -7.0), (1.5, -6.6)):
                x, y = math.floor(C[0] + mx), math.floor(C[1] + my - br * 0.3)
                cv.pixels([(x, y), (x + 1, y)], MOSS.base, name="moss")
                cv.pixel(x, y - 1, MOSS.light, name="moss")
            # two tiny fern fronds growing out of the moss (on a layer behind the back line)
            ferns = cv.layer(above=False, outline=True)
            sw = math.sin(p.fern * 1.3) * 0.8
            with ferns.xform(*xf):
                _fern(ferns, (C[0] - 4.5, C[1] - 5.0 - br * 0.3), sw, 6.5, -1.5)
                _fern(ferns, (C[0] - 0.5, C[1] - 5.2 - br * 0.3), sw * 0.7, 5.0, 1.2)
        # throat / cheek sac: a pale balloon swelling under the jaw
        if p.puff > 0.05:
            pr = 1.2 + 3.4 * p.puff
            cv.ellipse(H[0] + 2.0, H[1] + 4.0 + pr * 0.3, pr * 1.2, pr, SAC, shade="soft", name="sac", sep="deep")
            cv.circle(H[0] - 0.5, H[1] + 1.8, 1.0 + 1.6 * p.puff, HIDE, shade="soft", name="cheek", sep="deep")
        # wide down-turned mouth; opens as a dark gape for the tongue
        mouth_y = H[1] + 1.6
        if p.jaw > 0.05:
            gape = 2.6 * p.jaw
            cv.polygon([(H[0] - 3.5, mouth_y), (H[0] + 7.5, mouth_y - 0.8 - gape * 0.3), (H[0] + 7.5, mouth_y + gape)],
                       px.flat(MOUTH_IN), name="gape")
        else:
            cv.line((math.floor(H[0] - 3.5), math.floor(mouth_y) + 1), (math.floor(H[0] + 6.5), math.floor(mouth_y)),
                    HIDE.deep, name="mouth")
        _eye(cv, math.floor(H[0] - 0.8), math.floor(H[1] - 6.2), p.eye)
        mouth_pt = cv.tp((H[0] + 6.5, mouth_y + 0.6))
        if tumble:
            _hind(cv, lp(HIP), ground, p, far=False)
            _front(cv, lp(SHOULDER), ground, p, far=False)
    if not tumble:
        _hind(cv, hip, ground, p, far=False)
        _front(cv, sh, ground, p, far=False)
    if p.tongue is not None:  # sticky tongue lashing toward the right edge of the cell
        reach_x = mouth_pt[0] + (cv.w - 4.5 - mouth_pt[0]) * p.tongue
        tip = (reach_x, mouth_pt[1] - 0.5 - 1.0 * p.tongue)
        mid = ((mouth_pt[0] + tip[0]) / 2, (mouth_pt[1] + tip[1]) / 2 + 1.0 * (1 - p.tongue))
        top = cv.layer(above=True, outline=True)
        top.limb([mouth_pt, mid, tip], [1.1, 0.95, 0.9], TONGUE, shade="soft", name="tongue")
        top.circle(tip[0], tip[1], 1.9, TONGUE, name="tongue")
        top.pixel(math.floor(tip[0]) - 1, math.floor(tip[1]) - 1, TONGUE.light, name="tongue")
        if p.hit:
            spark = cv.layer(above=True, outline=False)
            px.impact(spark, min(tip[0], cv.w - 6), tip[1] - 3.5, size=2)
    if p.dust is not None:
        fx = cv.layer(above=True, outline=True)
        px.dust(fx, C[0] - 10, cv.gy - 1, p.dust, size=0.75, direction=-1)
