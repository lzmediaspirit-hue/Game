"""Reed frog - slim, long-legged marsh frog striped like river reeds (Wood element).

View: side, facing right.  ~18 art px tall sitting, ~20 long (legs folded).
Parts, back to front: far legs (dark), body (rump + chest + head + eye bump shaded as one
form), pale belly, reed stripes (a gold dorsolateral line and dark green bands along
the back), eardrum, mouth line, near hind leg (Z-folded thigh / shin / long foot, solved
with ``px.ik2``, dark bars across it), near foreleg, big gold eye with a slit pupil.
FX: dust puffs (hop / landing / kick), impact.
"""
import math

import pixel as px

SPEC = {
    "id": "reed_frog",
    "cell": 128,
    "anchor": [64, 112],
    "flying": False,
    "hit_frame": 2,
    "airborne": [["walk", 1], ["walk", 2], ["walk", 3], ["attack", 0], ["attack", 1], ["attack", 2],
                 ["death", 0]],
}

# ---- palette: fresh reed greens, pale lime belly, gold stripe, dark reed bands -----------
SKIN = px.material("frog_skin", "#b8dc6c", "#6fa845", "#467b3b", "#2b4f35", outline="#0b1810",
                   thresholds=(0.86, 0.5, 0.18))
BELLY = px.material("frog_belly", "#f1f2c2", "#d5dc98", "#a7b477", "#72845c", outline="#0b1810")
LEG = px.material("frog_leg", "#a9d466", "#62993f", "#3f7038", "#284a33", outline="#0b1810")
BAND = px.material("reed_band", "#4f7a34", "#3a5e2c", "#2b4826", "#1d3220", outline="#0b1810")
GOLD = px.material("reed_gold", "#f2e38a", "#d4bf5a", "#a39245", "#6f6534", outline="#0b1810")
TOE = px.material("frog_toe", "#d6e79a", "#a9c46c", "#7d9651", "#56693f", outline="#0b1810")
IRIS = px.rgb("#e9b43c")
MOUTH = SKIN.step(2)

# ---- poses --------------------------------------------------------------------------------
# bx, by   body offset (by < 0 = up)     rot  body pitch (deg, + nose up)
# hind     None = sitting (foot flat on the ground) | (ankle dx, dy, toe dx, dy) from the hip
# front    None = planted under the chest | (hand dx, dy) from the shoulder
# eye      open|angry|squeeze|dead       throat  throat pulse 0..1    flip  on its back
# dust     dust life (None = off)        hit  impact at the feet       fade  opacity
DEFAULTS = dict(bx=0, by=0, rot=0, hind=None, front=None, eye="open", throat=0.0, flip=False, dust=None,
                hit=False, fade=1.0, crouch=0.0)

POSE = px.poses(DEFAULTS, {
    "idle": [  # sitting: throat pulses, tiny body sway
        dict(),
        dict(throat=0.5),
        dict(throat=1.0, by=0),
        dict(throat=0.4, rot=1),
    ],
    "walk": [  # hop cycle: crouch, launch, sail, reach, land, settle
        dict(crouch=0.6, rot=6),
        dict(bx=2, by=-5, rot=20, hind=(-9.5, 5.5, -13.5, 7.0), front=(2.5, 3.0), dust=0.15),
        dict(bx=4, by=-7, rot=4, hind=(-8.5, 2.5, -12.5, 2.5), front=(4.5, 2.0)),
        dict(bx=5, by=-4, rot=-14, hind=(-6.0, 3.5, -2.0, 3.5), front=(4.0, 5.0)),
        dict(bx=4, by=-1, rot=-10, crouch=0.3, front=(3.0, 5.5), dust=0.2),
        dict(bx=2, crouch=0.4, rot=0, dust=0.5),
    ],
    "windup": [  # crouches low, rocks back on its haunches, eyes narrowed - held
        dict(crouch=0.6, rot=6, eye="angry", bx=-1),
        dict(crouch=1.0, rot=12, eye="angry", bx=-2, throat=0.5),
        dict(crouch=1.2, rot=14, eye="angry", bx=-2, throat=0.7, dust=0.2),
    ],
    "attack": [  # drop kick: spring up, swing upright with knees tucked, both legs lash out (frame 2)
        dict(bx=3, by=-7, rot=26, hind=(-9.5, 6.0, -13.5, 7.5), front=(3.0, 1.0), eye="angry", dust=0.2),
        dict(bx=5, by=-9, rot=48, hind=(4.0, 3.5, 8.0, 4.0), front=(2.5, -1.0), eye="angry", dust=0.5),
        dict(bx=6, by=-7, rot=70, hind=(10.0, 0.5, 15.0, 0.0), front=(3.0, -2.5), eye="angry", hit=True,
             dust=0.8),
        dict(bx=8, crouch=0.5, rot=4),
    ],
    "hurt": [
        dict(bx=-3, by=-2, rot=18, eye="squeeze", hind=(-5.0, 6.0, -1.0, 7.5), front=(2.5, 3.5)),
        dict(bx=-2, rot=8, eye="squeeze", crouch=0.3),
    ],
    "death": [  # knocked up and back, flips over, lies on its back, legs sag, fades
        dict(bx=-3, by=-4, rot=34, eye="squeeze", hind=(-7.0, 6.0, -4.0, 8.0), front=(2.0, 4.5)),
        dict(bx=-4, rot=120, eye="dead", hind=(-7.0, 5.0, -3.0, 6.5), front=(3.0, 4.0)),
        dict(bx=-4, flip=True, eye="dead", hind=(-6.0, 5.5, -9.0, 8.0), front=(3.0, 5.0)),
        dict(bx=-4, flip=True, eye="dead", hind=(-7.5, 4.5, -10.5, 6.0), front=(3.5, 4.0), fade=0.6),
        dict(bx=-4, flip=True, eye="dead", hind=(-8.0, 3.5, -11.5, 4.0), front=(4.0, 3.0), fade=0.3),
    ],
})


def _hind(cv, hip, ground, p, far):
    """Z-folded hind leg: thigh + shin (ik2, knee forward) + long flat foot."""
    if p.hind is None:  # sitting / crouching: ankle tucked under the hip, foot flat forward
        ankle = (hip[0] - 1.6 + (1.0 if far else 0), ground - 0.9)
        toe = (ankle[0] + 7.0, ground - 0.6)
    else:
        ax, ay, tx, ty = p.hind
        if far:
            ax, tx = ax + 1.2, tx + 1.2
        ankle = (hip[0] + ax, hip[1] + ay)
        toe = (hip[0] + tx, hip[1] + ty)
    knee = px.ik2(hip, ankle, 5.6, 5.8, bend=1 if ankle[0] <= hip[0] + 3 else -1)
    cv.limb([hip, knee], [2.5, 1.7], LEG, shade="dark" if far else "two", name="thigh",
            sep=False if far else "deep")
    cv.limb([knee, ankle], [1.4, 0.95], LEG, shade="dark" if far else "two", name="shin",
            sep=False if far else "deep")
    cv.limb([ankle, toe], [0.95, 0.75], LEG, shade="dark" if far else "two", name="foot")
    if not far:
        # dark reed bars across thigh and shin
        for a, b, t in ((hip, knee, 0.55), (knee, ankle, 0.5)):
            q = px.lerp_pt(a, b, t)
            d = (b[0] - a[0], b[1] - a[1])
            ln = math.hypot(*d) or 1.0
            n = (-d[1] / ln * 2.2, d[0] / ln * 2.2)
            cv.limb([(q[0] - n[0], q[1] - n[1]), (q[0] + n[0], q[1] + n[1])], 0.5, BAND, decal=True,
                    clip=["thigh", "shin"])
        # splayed toe tips
        cv.pixel(math.floor(toe[0]) + 1, math.floor(toe[1]), TOE.base, name="toe")
    return toe


def _front(cv, sh, ground, p, far):
    if p.front is None:
        hand = (sh[0] + 1.2 + (0.8 if far else 0), ground - 0.5)
    else:
        hand = (sh[0] + p.front[0] + (0.8 if far else 0), sh[1] + p.front[1])
    elbow = px.ik2(sh, hand, 3.2, 3.2, bend=1)
    shade = "dark" if far else "soft"
    cv.limb([sh, elbow, hand], [1.2, 0.9, 0.7], LEG, shade=shade, name="arm", sep=False if far else "deep")
    cv.limb([hand, (hand[0] + 1.6, hand[1])], [0.7, 0.5], TOE if not far else LEG, shade="two" if not far else "dark",
            name="hand")


def _eye(cv, x, y, state):
    """Big round bulging frog eye: gold iris ring, dark pupil, glint top-left."""
    if state == "squeeze":
        cv.stamp(["k...", ".kkk", "k..."], x, y, {"k": px.INK}, name="eye")
    elif state == "dead":
        cv.stamp(["k..k", ".kk.", ".kk.", "k..k"], x, y, {"k": px.INK}, name="eye")
    else:
        cv.stamp([".ii.", "igki", "ikki", ".ii."], x, y, {"g": px.GLINT, "i": IRIS, "k": px.INK}, name="eye")
        if state == "angry":  # heavy lid slanting down toward the snout
            cv.pixels([(x - 1, y - 1), (x, y - 1), (x + 1, y - 1), (x + 2, y), (x + 3, y), (x + 4, y + 1)],
                      SKIN.deep, name="lid")


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    ground = cv.ground
    cr = p.crouch
    C = (cv.gx - 1 + p.bx, ground - 8.0 + p.by + 1.6 * min(cr, 0.8))
    cv.opacity = p.fade
    xf = [px.rotate(p.rot, C)]
    if p.flip:
        xf = [px.flip_y(C[1])]
    tumble = p.flip or (action == "death" and p.rot > 60)  # legs follow the body frame
    if tumble or (p.crouch > 0.8 and p.hind is None):  # deep crouch: the rump rests on the ground
        cv.snap_ground = True
    # hips and shoulders in canvas space (legs reach for the real ground)
    hip = None if tumble else cv.tp((C[0] - 5.0, C[1] + 2.4))
    with cv.xform(*xf):
        if hip is None:  # tumbling / on its back: legs live in the body frame
            lhip, lsh = (C[0] - 5.0, C[1] + 2.4), (C[0] + 4.3, C[1] + 2.2)
            _hind(cv, (lhip[0] + 1.2, lhip[1] - 0.6), ground, p, far=True)
            _front(cv, (lsh[0] + 1.0, lsh[1] - 0.5), ground, p, far=True)
    if hip is not None:
        sh = cv.tp((C[0] + 4.3, C[1] + 2.2))
        _hind(cv, (hip[0] + 1.2, hip[1] - 0.6), ground, p, far=True)
        _front(cv, (sh[0] + 1.0, sh[1] - 0.5), ground, p, far=True)
    with cv.xform(*xf):
        # body: rump + chest + head + snout + eye bump as one form
        th = p.throat
        g = cv.union(cv.geom_ellipse(C[0] - 3.2, C[1] + 1.0, 5.6, 4.0, angle=-18),
                     cv.geom_ellipse(C[0] + 2.0, C[1] - 0.4, 5.0, 3.9 + 0.2 * th, angle=14),
                     cv.geom_ellipse(C[0] + 6.4, C[1] - 2.0, 4.2, 3.0, angle=4),
                     cv.geom_limb([(C[0] + 7.5, C[1] - 1.8), (C[0] + 10.6, C[1] - 1.0)], [2.3, 1.3]),
                     cv.geom_ellipse(C[0] + 5.9, C[1] - 4.4, 2.6, 2.2),
                     weights=[1.0, 0.95, 0.85, 0.6, 0.7])
        cv.draw_geom(g, SKIN, name="body", sep="deep")
        # pale belly and throat (the throat swells as it breathes)
        cv.ellipse(C[0] + 1.5, C[1] + 3.2, 7.0, 2.2 + 0.5 * th, BELLY, shade="two", decal=True, clip="body")
        # reed stripes: dark green bands along the back, a gold line from eye to rump
        cv.limb([(C[0] - 8.0, C[1] - 0.4), (C[0] - 3.0, C[1] - 3.2), (C[0] + 2.5, C[1] - 3.6)], 0.8, BAND,
                decal=True, clip="body")
        cv.limb([(C[0] - 7.5, C[1] + 1.4), (C[0] - 2.5, C[1] - 1.2), (C[0] + 3.5, C[1] - 1.8), (C[0] + 5.0, C[1] - 2.6)],
                0.55, GOLD, shade="two", decal=True, clip="body")
        # eardrum behind the eye and the long mouth line
        cv.circle(C[0] + 3.2, C[1] - 1.4, 1.2, SKIN.step(1), shade="two", decal=True, clip="body")
        cv.line((math.floor(C[0] + 4.5), math.floor(C[1] + 0.2)), (math.floor(C[0] + 10.5), math.floor(C[1] - 0.2)),
                MOUTH, decal=True, clip="body")
        _eye(cv, math.floor(C[0] + 4.2), math.floor(C[1] - 6.4), p.eye)
        if hip is None:
            _hind(cv, (C[0] - 5.0, C[1] + 2.4), ground, p, far=False)
            _front(cv, (C[0] + 4.3, C[1] + 2.2), ground, p, far=False)
    if hip is not None:
        toe = _hind(cv, hip, ground, p, far=False)
        _front(cv, sh, ground, p, far=False)
    if p.dust is not None:
        fx = cv.layer(above=True, outline=True)
        px.dust(fx, C[0] - 7 - p.bx * 0.6, cv.gy - 1, p.dust, size=0.7, direction=-1)
    if p.hit:
        top = cv.layer(above=True, outline=False)
        px.impact(top, toe[0] + 2, toe[1], size=3)
