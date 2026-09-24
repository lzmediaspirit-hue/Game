"""Reed otter - playful brown river otter, a Water spirit-animal pet.

View: side, facing right.  ~20 art px tall (head up), ~33 long including the tail.
Parts, back to front: far legs, thick tapered tail, near hind leg, body + neck + head
shaded as one form (``cv.union``: haunch, arched mid-back and chest along a spine that
humps with ``arch``), cream throat and muzzle decals, near foreleg, ear, nose, eye,
whiskers (unoutlined FX so they stay fine).  The windup rears up on the hind legs with
the little forepaws tucked; the attack is a splash nip.  Death is not a death: the pet
curls up asleep and fades back into its spirit token.
"""
import math

import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "reed_otter",
    "cell": 128,
    "anchor": [64, 112],
    "flying": False,
    "hit_frame": 1,
    "airborne": [["walk", 3]],
}

# ---- palette: warm otter brown, cream bib, dark webbed paws, teal spirit bead ----------------
FUR = px.material("otter_fur", "#c79262", "#8e5c3a", "#61402f", "#3f2a2b", outline="#170c0e",
                  thresholds=(0.92, 0.58, 0.22))
CREAM = px.material("otter_cream", "#fdf1d2", "#ead1a2", "#c09f79", "#8d705b", outline="#170c0e")
PAW = px.material("otter_paw", "#6e4d3f", "#4c332b", "#372520", "#261819", outline="#110909")
BEAD = px.material("spirit_bead", "#b8fff0", "#4fd1bf", "#23918a", "#155a5c", outline="#08191b")
NOSE = px.rgb("#2a1818")
IRIS = px.rgb("#5a2e1a")
SHEEN = px.rgb("#79e3d2")
WHISKER = px.rgb("#f3e6c8")
TOOTH = px.rgb("#fbf4e0")

# ---- poses ------------------------------------------------------------------------------------
# bx, by   body offset             arch   spine hump (-0.5 stretched .. 1 humped)
# pitch    body tilt about C (deg)  rear   rear up about the hind feet (deg, nose up)
# head     head+neck tilt (deg)     neck   neck reach 0..1       jaw   mouth open 0..1
# feet     (dx, lift): near-front, far-front, near-hind, far-hind
# tail     (lift, wave phase)       eye   open|angry|squeeze|closed|sleep
# paws     forepaws tucked up (rearing)      ear  ear angle      whisk  whisker twitch
# splash   splash life at the snout (None = off)   curl  curled-up sleeping ball
DEFAULTS = dict(bx=0, by=0, arch=0.3, pitch=0, rear=0, head=0, neck=1.0, jaw=0.0,
                feet=((0, 0), (0, 0), (0, 0), (0, 0)), tail=(0, 0.0), eye="open", paws=False, ear=0,
                whisk=0, splash=None, hit=False, curl=False, fade=1.0, breathe=0.0, token=False)

POSE = px.poses(DEFAULTS, {
    "idle": [
        dict(tail=(0, 0.0)),
        dict(tail=(0, 0.9), breathe=0.4, head=3, whisk=1),
        dict(tail=(0, 1.8), breathe=0.5, head=3, eye="closed"),
        dict(tail=(0, 2.7), breathe=0.2, head=1, whisk=1),
    ],
    "walk": [  # bouncy bounding gallop: the back humps as the hind feet gather, then stretches
        dict(arch=1.0, by=0, pitch=-4, head=-4, feet=((-1, 0), (-2, 0), (4, 1), (3, 0)), tail=(1, 0.0)),
        dict(arch=0.6, by=-1, pitch=2, head=0, feet=((2, 2), (1, 1), (3, 0), (2, 0)), tail=(1, 1.0)),
        dict(arch=-0.2, by=-2, pitch=5, head=4, feet=((4, 2), (3, 2), (-2, 0), (-3, 1)), tail=(2, 2.0)),
        dict(arch=-0.5, by=-3, pitch=2, head=4, feet=((4, 1), (3, 1), (-4, 2), (-5, 2)), tail=(2, 3.0)),
        dict(arch=0.1, by=-1, pitch=-5, head=-2, feet=((2, 0), (1, 0), (-2, 3), (-3, 2)), tail=(1, 4.0)),
        dict(arch=0.7, by=0, pitch=-5, head=-5, feet=((0, 0), (-1, 0), (1, 2), (0, 1)), tail=(0, 5.0)),
    ],
    "windup": [  # rears up on the hind legs, forepaws tucked, mouth opening - held
        dict(rear=22, head=-8, paws=True, eye="angry", jaw=0.2, tail=(0, 1.0), ear=-10, bx=-1),
        dict(rear=46, head=-18, paws=True, eye="angry", jaw=0.5, tail=(0, 1.5), ear=-20, bx=-2),
        dict(rear=54, head=-22, paws=True, eye="angry", jaw=0.8, tail=(0, 1.8), ear=-25, bx=-2,
             breathe=0.4),
    ],
    "attack": [  # drops forward into a nip; the snap lands on frame 1 with a splash
        dict(rear=16, bx=2, by=-1, head=-16, jaw=1.0, eye="angry", paws=True, ear=-25, tail=(1, 2.0),
             arch=-0.2),
        dict(rear=-8, bx=6, head=-10, jaw=0.1, eye="angry", ear=-20, arch=-0.4, tail=(1, 3.0),
             feet=((3, 0), (2, 0), (-2, 0), (-3, 0)), splash=0.15, hit=True),
        dict(rear=-4, bx=5, head=-4, jaw=0.0, eye="angry", ear=-10, arch=0.0, tail=(0, 4.0),
             feet=((2, 0), (1, 0), (-1, 0), (-2, 0)), splash=0.5),
        dict(bx=2, head=0, arch=0.2, tail=(0, 5.0), splash=0.85),
    ],
    "hurt": [
        dict(bx=-3, by=-1, head=16, eye="squeeze", jaw=0.4, ear=-30, arch=0.8, tail=(2, 1.0),
             feet=((1, 2), (0, 1), (0, 0), (0, 0))),
        dict(bx=-2, head=8, eye="squeeze", ear=-20, arch=0.6, tail=(1, 2.0)),
    ],
    "death": [  # not a death: it curls up to sleep and fades back into its token
        dict(bx=-3, by=-1, head=16, eye="squeeze", jaw=0.3, ear=-30, arch=0.8, tail=(2, 1.0),
             feet=((1, 2), (0, 1), (0, 0), (0, 0))),
        dict(bx=-2, by=2, head=-14, eye="closed", ear=-20, arch=1.0, tail=(0, 2.0), neck=0.6,
             feet=((-1, 0), (-1, 0), (1, 0), (1, 0))),
        dict(curl=True, eye="sleep"),
        dict(curl=True, eye="sleep", fade=0.6, token=True),
        dict(curl=True, eye="sleep", fade=0.3, token=True),
    ],
})


# ---- parts ------------------------------------------------------------------------------------
def _leg(cv, hip, foot, far, tucked=False):
    """Stubby otter leg with a dark webbed paw."""
    shade = "dark" if far else "soft"
    fx, fy = foot
    if tucked:  # forepaw folded up against the chest (rearing)
        cv.limb([hip, (fx, fy)], [1.9, 1.3], FUR, shade=shade, name="leg")
        cv.ellipse(fx + 0.6, fy + 0.2, 1.5, 1.1, PAW, shade="dark" if far else "two", name="paw")
        return
    ankle = (fx - 0.2, fy - 1.3)
    cv.limb([hip, ankle], [2.2, 1.4], FUR, shade=shade, name="leg")
    cv.ellipse(fx + 0.7, fy - 0.5, 1.8, 1.0, PAW, shade="dark" if far else "two", name="paw")


def _tail(cv, root, p, ground, flat=False):
    lift, ph = p.tail
    pts = [root]
    for k, (dx, dy) in enumerate(((-3.2, 1.9), (-6.2, 3.0), (-9.0, 2.9)), start=1):
        wave = 0.7 * math.sin(ph * 1.3 + k * 1.1) * k / 3
        y = root[1] + dy - lift * 0.9 * k + wave
        if flat:  # propping on the ground behind a rearing otter
            y = ground - 1.2 - (0.0 if k < 3 else 0.6)
        pts.append((root[0] + dx, min(y, ground - 0.8)))
    cv.limb(pts, [2.5, 1.9, 1.3, 0.6], FUR, name="tail")


def _eye(cv, x, y, state):
    if state == "squeeze":
        hc.eye_stamp(cv, ["k.", ".k", "k."], x, y - 1, {})
    elif state in ("closed", "sleep"):
        hc.eye_stamp(cv, ["k..k", ".kk."] if state == "sleep" else ["kkk"], x - 1, y + 1, {})
    else:
        hc.eye_stamp(cv, ["gk.", "kki", ".k."], x, y - 1, {"i": SHEEN})
        if state == "angry":
            cv.pixels([(x - 1, y - 2), (x, y - 2), (x + 1, y - 1)], FUR.deep, name="brow")


def _curled(cv, p):
    """Sleeping ball: back to the viewer's left, head resting on the wrapped tail."""
    g = cv.ground
    C = (cv.gx - 1.0, g - 5.2)
    cv.draw_geom(cv.union(cv.geom_ellipse(C[0] - 1.0, C[1], 8.4, 5.4),
                          cv.geom_ellipse(C[0] + 4.5, C[1] + 0.8, 5.0, 4.4)), FUR, name="body")
    cv.ellipse(C[0] + 3.5, C[1] + 3.2, 5.5, 1.6, CREAM, shade="two", decal=True, clip="body")
    # tail wraps round the front, under the chin
    cv.limb([(C[0] - 8.0, C[1] + 2.6), (C[0] - 3.0, C[1] + 4.2), (C[0] + 3.0, C[1] + 4.3), (C[0] + 8.2, C[1] + 3.0),
             (C[0] + 10.2, C[1] + 1.2)], [2.2, 2.1, 1.9, 1.4, 0.7], FUR, name="tail", sep="deep")
    # head resting on the tail, nose tucked down to the right
    H = (C[0] + 7.0, C[1] - 1.0)
    head = cv.union(cv.geom_ellipse(H[0], H[1], 3.6, 3.1), cv.geom_ellipse(H[0] + 2.6, H[1] + 1.4, 2.3, 1.8))
    cv.draw_geom(head, FUR, name="head", sep="deep")
    cv.ellipse(H[0] + 2.4, H[1] + 2.2, 2.6, 1.2, CREAM, shade="two", decal=True, clip="head")
    cv.pixel(round(H[0] + 4.2), round(H[1] + 1.2), NOSE, name="nose")
    cv.circle(H[0] - 2.4, H[1] - 2.4, 1.2, FUR, name="ear", sep="deep")
    _eye(cv, round(H[0]) , round(H[1]) - 1, p.eye)
    if p.token:  # the spirit token glints as the otter fades back into it
        fx = cv.layer(above=True, outline=False)
        s = 2 if p.fade > 0.5 else 3
        px.impact(fx, C[0] + 1, C[1] - 9, size=s, color=BEAD.light, core=px.GLINT)


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    if p.curl:
        _curled(cv, p)
        return
    ground = cv.ground
    C = (cv.gx - 2 + p.bx, ground - 8.0 + p.by)
    br = p.breathe
    a = p.arch
    R = (C[0] - 5.5, C[1] + 0.2 + a * 0.6)
    M = (C[0] - 0.5, C[1] - 0.3 - a * 2.6)
    K = (C[0] + 5.0, C[1] + 0.4 + a * 0.4)
    pivot = (R[0] + 1.0, ground)  # rearing pivot: the hind feet
    body_x = [px.rotate(p.rear, pivot), px.rotate(p.pitch, C)]

    def B(pt):  # body-local point -> canvas (through rear + pitch)
        return px.rot_pt(px.rot_pt(pt, p.pitch, C), p.rear, pivot)

    def foot(hip_x, i):
        f = p.feet[i]
        return (hip_x + f[0], ground - f[1])

    hips = {"nf": (K[0] + 0.6, K[1] + 2.4), "ff": (K[0] + 2.0, K[1] + 2.0),
            "nh": (R[0] + 1.0, R[1] + 2.6), "fh": (R[0] + 2.4, R[1] + 2.2)}
    # far legs (behind everything)
    fh = B(hips["fh"])
    _leg(cv, fh, foot(hips["fh"][0] + 0.5, 3), True)
    if p.paws:
        with cv.xform(*body_x):
            q = hips["ff"]
            _leg(cv, q, (q[0] + 3.4, q[1] + 0.2), True, tucked=True)
    else:
        _leg(cv, B(hips["ff"]), foot(hips["ff"][0] + 0.4, 1), True)
    # tail: lies flat on the ground as a prop while rearing
    if p.rear > 20:
        _tail(cv, B((R[0] - 4.0, R[1] + 1.0)), p, ground, flat=True)
    else:
        with cv.xform(*body_x):
            _tail(cv, (R[0] - 4.0, R[1] + 0.6), p, ground)
    _leg(cv, B(hips["nh"]), foot(hips["nh"][0], 2), False)
    if not p.paws:
        _leg(cv, B(hips["nf"]), foot(hips["nf"][0], 0), False)

    fx = cv.layer(above=True, outline=False)  # whiskers
    with cv.xform(*body_x):
        body_g = [cv.geom_ellipse(R[0], R[1], 5.4, 4.8 + br * 0.6),
                  cv.geom_ellipse(M[0], M[1], 5.0, 4.4 + br),
                  cv.geom_ellipse(K[0], K[1], 4.7, 4.2 + br * 0.4)]
        N0 = (K[0] + 2.2, K[1] - 2.0)
        with cv.xform(px.rotate(p.head, N0)):
            H = (N0[0] + 3.2 * p.neck + 0.4, N0[1] - 5.6 * p.neck - 0.4)
            head_g = [cv.geom_limb([(N0[0] - 1.0, N0[1] + 1.0), H], [3.4, 2.9]),
                      cv.geom_ellipse(H[0], H[1], 3.9, 3.3),
                      cv.geom_ellipse(H[0] + 3.4, H[1] + 1.0, 2.5, 2.0)]
            if p.jaw > 0.05:  # lower jaw drops open under the muzzle
                with cv.xform(px.rotate(-26 * p.jaw, (H[0] + 1.2, H[1] + 2.2))):
                    cv.limb([(H[0] + 1.2, H[1] + 2.4), (H[0] + 4.8, H[1] + 2.6)], [1.4, 0.9], FUR,
                            shade="nolight", name="jaw")
                    cv.pixel(round(H[0] + 4.2), round(H[1] + 1.4), TOOTH, name="tooth")
        cv.draw_geom(cv.union(*body_g, *head_g, weights=[1.0, 0.95, 0.9, 0.6, 0.85, 0.7]), FUR,
                     name="body", sep="deep")
        # cream belly line and bib
        cv.ellipse(K[0] + 1.0, K[1] + 3.6, 4.4, 1.5, CREAM, shade="two", decal=True, clip="body")
        with cv.xform(px.rotate(p.head, N0)):
            cv.limb([(H[0] + 3.2, H[1] + 2.4), (N0[0] + 1.6, N0[1] + 1.2), (K[0] + 3.0, K[1] + 2.6)],
                    [1.5, 1.9, 1.6], CREAM, shade="two", decal=True, clip="body")
            cv.ellipse(H[0] + 3.0, H[1] + 1.9, 3.0, 1.3, CREAM, shade="soft", decal=True, clip="body")
            # spirit bead on a cord at the throat (the pet's token)
            cv.pixels([(round(N0[0]) + 1, round(N0[1]) - 1)], BEAD.base, name="bead")
            cv.pixels([(round(N0[0]) + 2, round(N0[1]) - 1)], BEAD.light, name="bead")
            # ear, nose, mouth, eye
            ear_c = px.rot_pt((H[0] - 2.8, H[1] - 2.3), p.ear, (H[0] - 1.5, H[1] - 1.0))
            cv.circle(ear_c[0], ear_c[1], 1.35, FUR, name="ear", sep="deep")
            cv.pixel(round(ear_c[0]), round(ear_c[1]), FUR.deep, name="ear")
            nx, ny = round(H[0] + 5.4), round(H[1] + 0.2)
            cv.pixels([(nx - 1, ny), (nx, ny)], NOSE, name="nose")
            if p.jaw <= 0.05:
                cv.pixels([(nx - 2, ny + 2), (nx - 3, ny + 2)], FUR.deep, name="mouth")
            _eye(cv, round(H[0] + 0.2), round(H[1] - 1.2), p.eye)
            w = p.whisk * 0.6
            fx.line((nx - 1, ny + 1), (nx + 3, ny - 0 - round(w)), WHISKER, name="whisker")
            fx.line((nx - 1, ny + 2), (nx + 3, ny + 3 - round(w)), WHISKER, name="whisker")
            snout = cv.tp((H[0] + 6.0, H[1] + 1.5))
        if p.paws:  # near forepaw tucked against the chest
            q = hips["nf"]
            _leg(cv, (q[0] + 0.4, q[1] - 0.4), (q[0] + 3.6, q[1] + 0.8), False, tucked=True)

    if p.splash is not None:
        sp = cv.layer(above=True, outline=True)
        px.splash(sp, snout[0] + 1, cv.gy - 1, p.splash, size=0.8)
    if p.hit:
        top = cv.layer(above=True, outline=False)
        px.impact(top, snout[0] + 1, snout[1] - 1, size=3)
