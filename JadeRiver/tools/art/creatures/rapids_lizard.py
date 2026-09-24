"""Rapids lizard - long, sleek blue-green water lizard with a finned crest (Water).

View: side, facing right.  ~18 art px tall to the crest, ~48 long nose to tail (cell 128).
Parts, back to front: far legs (dark), the dorsal fin crest (webbed spines), tail + body as
one tapered tube (tail tip -> neck), pale belly and dark cross-bands as decals, near legs
(sprawling, splayed toes), head (skull + snout, hinged jaw, amber eye, cheek fin).
Walk: fast scurry (diagonal pairs, body low).  Windup: tail raised and curled over the back,
crest flared, hissing (held).  Attack: a spinning tail whip - it whirls round so the tail
lashes out in front on frame 1, then spins back.  Death: flips onto its back, legs curl.
"""
import math

import pixel as px
import helpers_batch_b as hb

SPEC = {
    "id": "rapids_lizard",
    "cell": 128,
    "anchor": [64, 112],
    "flying": False,
    "hit_frame": 1,
}

# ---- palette ------------------------------------------------------------------------------
SKIN = px.material("rl_skin", "#7fd8c6", "#28868f", "#1b5a74", "#133a52", outline="#05121a",
                   thresholds=(0.9, 0.52, 0.16))
BELLY = px.material("rl_belly", "#f2f6d6", "#c8e2c0", "#8fb4a0", "#5a7c78", outline="#06151c")
BAND = SKIN.step(1)
FIN = px.material("rl_fin", "#e2fff6", "#8cf0d6", "#45bcb2", "#23808a", outline="#05121a")
CLAW = px.flat("#d8ecd8", outline="#06151c")
IRIS = px.rgb("#f2b640")
MOUTH = px.rgb("#8a2f40")

# ---- poses --------------------------------------------------------------------------------
# bx, by   body offset       sx  horizontal squash (spin: <1 turning, <0 facing away)
# head     head tilt (deg)   jaw  0..1     crest  fin crest height scale
# tail     (lift, curl)  lift raises the tail root angle, curl bends it up over the back
# feet     (dx, lift) near-front, far-front, near-hind, far-hind     eye  open|angry|squeeze|dead
# flip     on its back (death)   curl  legs curl   fade  opacity   hit  impact   whirl  spin streaks
DEFAULTS = dict(bx=0, by=0, sx=1.0, head=0, jaw=0.0, crest=1.0, tail=(0.0, 0.0),
                feet=((0, 0), (0, 0), (0, 0), (0, 0)), eye="open", flip=False, curl=0.0, fade=1.0, hit=False,
                whirl=0, sway=0.0, breathe=0.0)

POSE = px.poses(DEFAULTS, {
    "idle": [  # basking alert: head bobs, crest breathes, tail tip flicks
        dict(),
        dict(head=3, breathe=0.3, sway=0.6),
        dict(head=4, breathe=0.5, crest=1.1, sway=1.2),
        dict(head=1, breathe=0.2, sway=0.6),
    ],
    "walk": [  # fast scurry: diagonal pairs, body swings low, tail whips side to side
        dict(feet=((3, 0), (-2, 2), (-3, 2), (2, 0)), sway=0.0, head=-2),
        dict(feet=((1, 1), (0, 0), (-1, 0), (1, 1)), sway=1.0, by=-1, head=-3),
        dict(feet=((-2, 2), (2, 0), (2, 0), (-3, 2)), sway=2.0, head=-2),
        dict(feet=((-3, 2), (3, 0), (3, 0), (-2, 2)), sway=3.0, head=-2),
        dict(feet=((0, 0), (1, 1), (1, 1), (-1, 0)), sway=4.0, by=-1, head=-3),
        dict(feet=((2, 0), (-3, 2), (-2, 2), (3, 0)), sway=5.0, head=-2),
    ],
    "windup": [  # crouch, crest flares, tail rises and curls up over the back, hiss - held
        dict(by=1, tail=(0.4, 14), crest=1.3, head=6, jaw=0.4, eye="angry", bx=-1),
        dict(by=1, tail=(0.8, 30), crest=1.6, head=8, jaw=0.8, eye="angry", bx=-2),
        dict(by=1, tail=(0.9, 34), crest=1.7, head=9, jaw=1.0, eye="angry", bx=-2),
    ],
    "attack": [  # spin: turn away, the tail lashes out in front (hit), turn back
        dict(sx=0.5, tail=(0.3, 0), crest=1.4, eye="angry", jaw=0.5, whirl=1, bx=-2),
        dict(sx=-1.0, tail=(-0.1, -4), crest=1.4, eye="angry", jaw=0.6, hit=True, whirl=2, bx=-9),
        dict(sx=-0.5, tail=(0.2, 0), crest=1.2, eye="angry", jaw=0.3, whirl=1, bx=-2),
        dict(sx=1.0, tail=(0.1, 4), crest=1.1, head=2, bx=1),
    ],
    "hurt": [
        dict(bx=-3, by=-1, head=16, jaw=0.6, eye="squeeze", tail=(0.5, 10), feet=((1, 2), (0, 1), (0, 0), (0, 0))),
        dict(bx=-1, head=8, jaw=0.2, eye="squeeze", tail=(0.3, 6)),
    ],
    "death": [  # jerks up, flips onto its back, legs curl, fades
        dict(bx=-3, by=-1, head=20, jaw=0.8, eye="squeeze", tail=(0.6, 14), feet=((1, 2), (0, 1), (0, 0), (0, 0))),
        dict(flip=True, eye="dead", jaw=0.6, curl=0.2),
        dict(flip=True, eye="dead", jaw=0.6, curl=0.6),
        dict(flip=True, eye="dead", jaw=0.6, curl=1.0, fade=0.6),
        dict(flip=True, eye="dead", jaw=0.6, curl=1.0, fade=0.3),
    ],
})


# ---- parts --------------------------------------------------------------------------------
def _tail_pts(P, p, ground):
    lift, curl = p.tail
    a = 188 - 22 * lift  # root direction: back and a little down; lift raises it
    q = (P[0] - 1.5, P[1] - 0.5)
    pts = [q]
    for k in range(9):
        a -= curl * (0.35 + 0.1 * k) + 2.0 * math.sin(p.sway + k * 0.8) * (k / 8)
        q = px.polar(q, a, 2.7)
        if curl <= 0 and lift <= 0.2:
            q = (q[0], min(q[1], ground - 0.8))
        pts.append(q)
    return pts[::-1]  # tip first


def _leg(cv, hip, foot, far, front, curl=0.0, sep=False):
    fx, fy = foot
    shade = "dark" if far else "soft"
    if front:
        joint = (hip[0] - 2.8, hip[1] + 2.2)
    else:
        joint = (hip[0] + 3.4, hip[1] + 0.8)
    wrist = (fx - 0.5, fy - 0.4)
    cv.limb([hip, joint, wrist], [1.9, 1.35, 0.9], SKIN, shade=shade, name="leg", sep=sep)
    # splayed toes
    for a in ((0, 1.8), (20, 2.2), (170, 1.2)) if curl == 0 else ((60, 1.4), (90, 1.6)):
        t = px.polar(wrist, a[0], a[1] + 0.4)
        cv.line((math.floor(wrist[0]), math.floor(wrist[1])), (math.floor(t[0]), math.floor(t[1])),
                SKIN.shadow if far else SKIN.base, name="leg")


def _crest(cv, pts, radii, idx0, idx1, scale):
    """Webbed dorsal fin along the back between spine samples idx0..idx1: spines and web."""
    top, base = [], []
    for j, i in enumerate(range(idx0, idx1 + 1)):
        a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(tx, ty) or 1.0
        nx, ny = ty / ln, -tx / ln  # dorsal normal (left of the head-ward direction)
        if ny > 0:
            nx, ny = -nx, -ny
        r = radii[i]
        u = (i - idx0) / max(1, idx1 - idx0)
        h = (1.2 + 3.4 * math.sin(math.pi * min(1.0, u * 1.15))) * scale
        spike = 1.0 if j % 2 == 0 else 0.55
        base.append((pts[i][0] + nx * (r - 0.8), pts[i][1] + ny * (r - 0.8)))
        top.append((pts[i][0] + nx * (r + h * spike), pts[i][1] + ny * (r + h * spike)))
    cv.polygon(base + top[::-1], FIN, shade="soft", name="crest")
    for k in range(0, len(top), 2):  # the spines: darker rays to each spike
        cv.line((math.floor(base[k][0]), math.floor(base[k][1])), (math.floor(top[k][0]), math.floor(top[k][1])),
                FIN.shadow, band=None, decal=True, clip="crest", name="crest")


def _head(cv, N, p):
    H = (N[0] + 3.5, N[1] - 1.0)
    jaw_a = -6 - 30 * p.jaw
    j0 = (H[0] - 0.5, H[1] + 1.2)
    if p.jaw > 0.05:
        jt = px.polar(j0, jaw_a, 6.2)
        cv.polygon([j0, (j0[0], j0[1] - 1.0), px.polar(j0, jaw_a + 14, 6.0), jt], MOUTH, shade="flat", name="mouth")
        cv.limb([j0, jt], [1.4, 0.7], BELLY, shade="two", name="jaw")
    snout = (H[0] + 6.5, H[1] + 0.8)
    head = cv.union(cv.geom_ellipse(H[0], H[1], 3.6, 2.7, angle=-6),
                    cv.geom_limb([(H[0] + 1.0, H[1]), snout], [2.3, 1.2]), weights=[1.0, 0.8])
    cv.draw_geom(head, SKIN, name="head", sep="deep")
    cv.limb([(H[0] - 1.0, H[1] + 1.6), (snout[0] - 0.5, snout[1] + 0.8)], [0.9, 0.6], BELLY, shade="two",
            decal=True, clip="head", name="head")
    cv.pixel(math.floor(snout[0]), math.floor(snout[1]) - 1, SKIN.deep, name="nostril")
    # frilled cheek fin behind the jaw
    cv.polygon([(H[0] - 2.5, H[1] - 0.5), (H[0] - 5.2, H[1] - 2.8), (H[0] - 4.8, H[1] + 0.2),
                (H[0] - 5.4, H[1] + 2.0), (H[0] - 2.2, H[1] + 1.8)], FIN, shade="soft", name="frill", sep="deep")
    ex, ey = math.floor(H[0] + 0.5), math.floor(H[1] - 2)
    hb.eye(cv, ex, ey, p.eye, iris=IRIS, brow=SKIN.deep)
    return snout


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    ground = cv.ground
    cv.opacity = p.fade
    P = (cv.gx - 2 + p.bx, ground - 6.0 + p.by)  # hips
    S = (P[0] + 11.0, P[1] - 0.8)  # shoulders
    xf = []
    if p.sx != 1.0:
        xf.append(px.scale(p.sx, 1.0, (P[0] + 5.5, ground)))
    if p.flip:
        xf.append(px.flip_y(P[1] - 1.0))
        cv.snap_ground = True

    def foot(dx, i):
        if p.flip:  # legs in the air, curling
            return (P[0] + dx * (1 - 0.25 * p.curl), P[1] + 7.5 - 3.5 * p.curl)
        f = p.feet[i]
        return (P[0] + dx + f[0], ground - f[1])

    with cv.xform(*xf):
        # far legs
        _leg(cv, (S[0] + 0.5, S[1] + 1.8), foot(S[0] - P[0] + 2.5, 1), True, True, p.curl if p.flip else 0)
        _leg(cv, (P[0] + 0.8, P[1] + 1.8), foot(3.5, 3), True, False, p.curl if p.flip else 0)
        # spine: tail tip -> hips -> shoulders -> neck
        tail = _tail_pts(P, p, ground)
        br = p.breathe
        neck = (S[0] + 3.5, S[1] - 1.8 + (-1.0 if p.head > 5 else 0.0))
        spine = tail + [(P[0] + 4.0, P[1] - 0.6 - br * 0.3), (S[0] - 2.0, S[1] - 0.3), neck]
        pts = hb.resample(hb.catmull(spine, 5), 1.0)
        n = len(pts)
        ti = next(i for i, q in enumerate(pts) if q[0] >= P[0] - 1.0 and i > n // 3)  # tail base index
        radii = []
        for i in range(n):
            if i <= ti:
                u = i / max(1, ti)
                radii.append(0.45 + (2.4 - 0.45) * u ** 1.3)
            else:
                u = (i - ti) / max(1, n - 1 - ti)
                radii.append(2.4 + 1.1 * math.sin(math.pi * min(1.0, u * 1.25)) + br * 0.3 - 0.6 * max(0.0, u - 0.8) * 5)
        _crest(cv, pts, radii, max(1, ti - 7), n - 3, p.crest)
        cv.limb(pts, radii, SKIN, name="body")
        nrm = hb.belly_normals(pts, toward=(0.0, 1.0))
        cv.limb(hb.offset(pts, nrm, radii, 0.75), [r * 0.5 for r in radii], BELLY, shade="two", decal=True,
                clip="body", name="body")
        for i in range(3, ti - 1, 4):  # dark cross-bands ringing the tail
            if i < 2:
                continue
            a = hb.offset([pts[i]], [nrm[i]], [radii[i]], -1.1)[0]
            b = hb.offset([pts[i]], [nrm[i]], [radii[i]], 0.1)[0]
            cv.limb([a, b], 0.6, BAND, decal=True, clip="body", name="body")
        # near legs
        _leg(cv, (P[0] - 0.5, P[1] + 2.0), foot(1.5, 2), False, False, p.curl if p.flip else 0, sep="deep")
        _leg(cv, (S[0] - 0.8, S[1] + 2.0), foot(S[0] - P[0] + 0.5, 0), False, True, p.curl if p.flip else 0,
             sep="deep")
        with cv.xform(px.rotate(p.head, neck)):
            _head(cv, neck, p)
        tip = cv.tp(pts[0])
    if p.whirl:  # spin streaks arcing around the body
        back = cv.layer(above=False, outline=False)
        c = (P[0] + 5.5, P[1] - 2.0)
        for k in range(4 + 2 * (p.whirl - 1)):
            a0 = 200 + k * 30
            q0 = px.polar(c, a0, 20.0)
            q1 = px.polar(c, a0 + 12, 20.0)
            back.line((math.floor(q0[0]), math.floor(q0[1] * 0.5 + c[1] * 0.5)),
                      (math.floor(q1[0]), math.floor(q1[1] * 0.5 + c[1] * 0.5)),
                      px.MIST_BLUE if k % 2 else px.PAPER, name="whirl")
    if p.hit:
        top = cv.layer(above=True, outline=False)
        px.impact(top, tip[0], tip[1] - 1, size=3)
