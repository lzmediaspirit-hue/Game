"""Ember fox - small orange-red fox kit with a flickering flame-tipped tail, a Fire pet.

View: side, facing right.  ~22 art px tall to the ear tips, ~30 long with the tail.
Parts, back to front: far legs, far ear, bushy tail (cream band + flame tip that
flickers every frame), near hind leg, body + neck + head as one form (``cv.union``),
white bib and muzzle decals, near foreleg, near ear (cream inside, dark tip), amber eye
with a dark eye line.  Windup: crouch low with the tail flame flaring; attack: a pounce
and ember bite with sparks; death: curls up nose-under-tail and fades into its token.
"""
import math

import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "ember_fox",
    "cell": 128,
    "anchor": [64, 112],
    "flying": False,
    "hit_frame": 1,
    "airborne": [["attack", 0]],
}

# ---- palette: orange-red fur toward pale gold lights and red-violet shadows -----------------
FUR = px.material("fox_fur", "#ffb35e", "#e06d2e", "#ab4328", "#6b2926", outline="#1d0a0b",
                  thresholds=(0.92, 0.58, 0.22))
WHITE = px.material("fox_white", "#fffbf0", "#f2e4cd", "#ccb4a2", "#927873", outline="#1d0a0b")
SOCK = px.material("fox_sock", "#70403a", "#4b2a28", "#361d1e", "#241314", outline="#110808")
EAR_IN = px.material("fox_ear_in", "#fbe3c4", "#e8bf98", "#bf8f74", "#8a6255", outline="#1d0a0b")
FLAME = (px.rgb("#e2452c"), px.rgb("#ff9a36"), px.rgb("#ffe9a6"))
IRIS = px.rgb("#ffb62e")
NOSE = px.rgb("#221214")
TOOTH = px.rgb("#fff6e2")

# ---- poses ------------------------------------------------------------------------------------
# bx, by   body offset        crouch  lower the body (px, legs bend)     pitch  body tilt (deg)
# head     head tilt (deg)    jaw     mouth 0..1        ear   ear angle (deg, - = back)
# feet     (dx, lift): near-front, far-front, near-hind, far-hind
# tail     (raise deg, wave phase)    flame  flame height (px)   ph  flame flicker phase
# eye      open|angry|squeeze|sleep   sparks  ember burst life at the jaws (None = off)
# curl     curled up asleep (death)   fade    frame opacity
DEFAULTS = dict(bx=0, by=0, crouch=0, pitch=0, head=0, jaw=0.0, ear=0,
                feet=((0, 0), (0, 0), (0, 0), (0, 0)), tail=(0, 0.0), flame=7.0, ph=0.0, eye="open",
                sparks=None, hit=False, curl=False, fade=1.0, breathe=0.0, stretch=1.0)

POSE = px.poses(DEFAULTS, {
    "idle": [
        dict(ph=0.0, tail=(0, 0.0)),
        dict(ph=1.6, tail=(3, 0.8), breathe=0.4, flame=7.5),
        dict(ph=3.2, tail=(5, 1.6), breathe=0.5, head=2, ear=-6, flame=8.0),
        dict(ph=4.8, tail=(2, 2.4), breathe=0.2, head=1, flame=7.0),
    ],
    "walk": [  # light trot: diagonal pairs (near-front + far-hind) swap, a bob on the passing frames
        dict(feet=((2, 0), (-2, 2), (-2, 2), (2, 0)), ph=0.0, tail=(4, 0.0)),
        dict(feet=((1, 0), (0, 2), (-1, 1), (0, 0)), by=-1, ph=1.1, tail=(6, 0.7), head=1),
        dict(feet=((-1, 1), (1, 0), (1, 0), (-1, 1)), ph=2.2, tail=(5, 1.4)),
        dict(feet=((-2, 2), (2, 0), (2, 0), (-2, 2)), ph=3.3, tail=(4, 2.1)),
        dict(feet=((0, 2), (1, 0), (0, 0), (-1, 1)), by=-1, ph=4.4, tail=(6, 2.8), head=1),
        dict(feet=((1, 1), (-1, 0), (-1, 0), (1, 1)), ph=5.5, tail=(5, 3.5)),
    ],
    "windup": [  # crouches low, head level, ears back, tail raised with the flame flaring - held
        dict(crouch=1, bx=-1, head=-6, ear=-15, eye="angry", tail=(14, 0.5), flame=9.5, ph=1.0,
             feet=((1, 0), (1, 0), (-1, 0), (-1, 0))),
        dict(crouch=3, bx=-2, head=-10, ear=-28, eye="angry", tail=(26, 0.8), flame=12.0, ph=2.4, jaw=0.3,
             feet=((2, 0), (2, 0), (-1, 0), (-1, 0)), pitch=-3),
        dict(crouch=3, bx=-2, head=-10, ear=-32, eye="angry", tail=(30, 1.0), flame=13.5, ph=3.7, jaw=0.5,
             feet=((2, 0), (2, 0), (-1, 0), (-1, 0)), pitch=-3, breathe=0.4),
    ],
    "attack": [  # pounce and ember bite; the jaws snap on frame 1 with a burst of sparks
        dict(bx=4, by=-4, pitch=10, head=6, jaw=1.0, ear=-30, eye="angry", tail=(10, 2.0), flame=11.0,
             ph=4.8, feet=((4, 5), (3, 4), (-3, 1), (-4, 0)), stretch=1.08),
        dict(bx=8, by=-1, pitch=-4, head=-6, jaw=0.1, ear=-25, eye="angry", tail=(6, 3.0), flame=9.5,
             ph=6.0, feet=((3, 0), (2, 0), (-3, 1), (-4, 1)), sparks=0.25, hit=True, stretch=1.06),
        dict(bx=7, pitch=-2, head=-3, jaw=0.2, ear=-15, eye="angry", tail=(4, 4.0), flame=8.5, ph=7.2,
             feet=((2, 0), (1, 0), (-1, 0), (-2, 0)), sparks=0.7),
        dict(bx=3, head=0, ear=-5, tail=(3, 5.0), flame=7.5, ph=8.4),
    ],
    "hurt": [
        dict(bx=-3, by=-1, head=16, eye="squeeze", jaw=0.4, ear=-35, tail=(14, 1.0), flame=5.5, ph=2.0,
             feet=((1, 2), (0, 1), (0, 0), (0, 0))),
        dict(bx=-2, head=8, eye="squeeze", ear=-20, tail=(8, 2.0), flame=6.0, ph=3.0),
    ],
    "death": [  # not a death: curls up with its nose under the tail and fades into its token
        dict(bx=-3, by=-1, head=16, eye="squeeze", jaw=0.3, ear=-35, tail=(14, 1.0), flame=5.5, ph=2.0,
             feet=((1, 2), (0, 1), (0, 0), (0, 0))),
        dict(bx=-2, crouch=4, head=-14, eye="sleep", ear=-25, tail=(-6, 2.0), flame=4.5, ph=3.0,
             feet=((1, 0), (1, 0), (-1, 0), (-1, 0))),
        dict(curl=True, eye="sleep", flame=4.0, ph=4.0),
        dict(curl=True, eye="sleep", flame=3.0, ph=5.0, fade=0.6),
        dict(curl=True, eye="sleep", flame=2.5, ph=6.0, fade=0.3),
    ],
})


# ---- parts ------------------------------------------------------------------------------------
def _front_leg(cv, hip, foot, far):
    fx, fy = foot
    elbow = (hip[0] + 0.3 + (fx - hip[0]) * 0.3, hip[1] + (fy - hip[1]) * 0.45)
    cv.limb([hip, elbow, (fx, fy - 1.0)], [1.8, 1.2, 1.0], FUR, shade="dark" if far else "two", name="leg")
    cv.limb([px.lerp_pt(elbow, (fx, fy), 0.35), (fx, fy - 1.0)], [1.2, 1.0], SOCK, decal=True, clip="leg",
            shade="dark" if far else "two")
    cv.ellipse(fx + 0.5, fy - 0.4, 1.4, 0.9, SOCK, shade="dark" if far else "two", name="paw")


def _hind_leg(cv, hip, foot, far, crouch):
    fx, fy = foot
    knee = (hip[0] + 1.6, hip[1] + 2.4 - crouch * 0.2)
    hock = (fx - 1.3 - crouch * 0.3, fy - 2.4 + crouch * 0.2)
    cv.limb([hip, knee, hock, (fx, fy - 1.0)], [2.6, 1.7, 1.1, 1.0], FUR, shade="dark" if far else "two",
            name="leg")
    cv.limb([hock, (fx, fy - 1.0)], [1.1, 1.0], SOCK, decal=True, clip="leg", shade="dark" if far else "two")
    cv.ellipse(fx + 0.5, fy - 0.4, 1.4, 0.9, SOCK, shade="dark" if far else "two", name="paw")


def _tail(cv, root, p, big=1.0):
    """Bushy tail curving up and back; a cream band, then the flickering flame tip."""
    raise_, ph = p.tail
    pts = [root]
    ang0 = 160 - raise_ * 0.6
    segs = ((3.2, ang0 + 12), (3.0, ang0 - 18), (2.8, ang0 - 42))
    q = root
    for k, (ln, a) in enumerate(segs):
        a += 6 * math.sin(ph * 1.4 + k * 1.2) * (k + 1) / 3
        q = px.polar(q, a - raise_ * 0.5, ln * big)
        pts.append(q)
    cv.limb(pts, [1.5, 2.6, 2.9, 2.3], FUR, name="tail")
    tip = pts[-1]
    back = pts[-2]
    cv.limb([px.lerp_pt(back, tip, 0.85), tip], [2.6, 2.3], EAR_IN, shade="two", decal=True, clip="tail")
    d = math.degrees(math.atan2(-(tip[1] - back[1]), tip[0] - back[0]))
    lean = math.cos(math.radians(d)) * 0.35 - 0.15
    base = px.polar(tip, d, 1.6)
    hc.flame(cv, base, p.flame, 2.4 + p.flame * 0.08, p.ph, FLAME, lean=lean, name="flame")
    return tip


def _eye(cv, x, y, state):
    if state == "squeeze":
        hc.eye_stamp(cv, ["k.", ".k", "k."], x, y - 1, {})
    elif state == "sleep":
        hc.eye_stamp(cv, ["k..k", ".kk."], x - 1, y + 1, {})
    else:
        hc.eye_stamp(cv, ["gi.", "ikk"], x, y, {"i": IRIS})
        if state == "angry":
            cv.pixels([(x - 1, y - 1), (x, y - 1), (x + 1, y), (x + 2, y)], FUR.deep, name="brow")


def _ear(cv, H, ang, far):
    pivot = (H[0] - 1.0, H[1] - 3.0)
    pts = [px.rot_pt(q, ang, pivot) for q in ((H[0] - 2.9, H[1] - 1.8), (H[0] - 1.5, H[1] - 8.8),
                                              (H[0] + 1.0, H[1] - 3.2))]
    if far:
        pts = [(x + 2.0, y + 0.4) for (x, y) in pts]
        cv.polygon(pts, FUR, shade="dark", name="ear_far")
        cv.polygon([px.lerp_pt(pts[0], pts[1], 0.62), pts[1], px.lerp_pt(pts[2], pts[1], 0.62)], SOCK,
                   shade="dark", decal=True, clip="ear_far")
        return
    cv.polygon(pts, FUR, name="ear", sep="deep")
    cv.polygon([px.lerp_pt(pts[0], pts[2], 0.5), px.lerp_pt(pts[0], pts[1], 0.6), px.lerp_pt(pts[2], pts[1], 0.45)],
               EAR_IN, shade="two", decal=True, clip="ear")
    cv.polygon([px.lerp_pt(pts[0], pts[1], 0.7), pts[1], px.lerp_pt(pts[2], pts[1], 0.7)], SOCK, shade="two",
               decal=True, clip="ear")


def _curled(cv, p):
    """Curled asleep: round back, the tail wrapped over the nose, ears up, flame low."""
    cv.snap_ground = True
    g = cv.ground
    C = (cv.gx - 1.5, g - 5.6)
    H = (C[0] + 4.6, C[1] - 2.6)
    _ear(cv, H, -30, True)
    cv.ellipse(C[0] - 0.5, C[1], 8.0, 5.8, FUR, name="body")
    cv.ellipse(C[0] + 1.0, C[1] + 4.4, 6.0, 1.4, WHITE, shade="two", decal=True, clip="body")
    head = cv.union(cv.geom_ellipse(H[0], H[1], 4.0, 3.5), cv.geom_limb([(H[0] + 1.5, H[1] + 1.0),
                                                                        (H[0] + 5.2, H[1] + 2.6)], [2.2, 1.0]))
    cv.draw_geom(head, FUR, name="head", sep="deep")
    cv.ellipse(H[0] + 2.8, H[1] + 2.6, 3.0, 1.2, WHITE, shade="soft", decal=True, clip="head")
    _ear(cv, H, -30, False)
    _eye(cv, round(H[0] + 0.4), round(H[1] - 1.0), p.eye)
    # tail sweeps round the front and over the nose; its flame glows low
    pts = [(C[0] - 7.5, C[1] + 1.5), (C[0] - 3.0, C[1] + 4.6), (C[0] + 3.5, C[1] + 4.8), (C[0] + 8.6, C[1] + 2.8)]
    cv.limb(pts, [2.0, 2.6, 2.7, 2.2], FUR, name="tail", sep="deep")
    cv.limb([px.lerp_pt(pts[2], pts[3], 0.5), pts[3]], [2.6, 2.2], EAR_IN, shade="two", decal=True, clip="tail")
    hc.flame(cv, (C[0] + 9.8, C[1] + 3.0), p.flame, 2.0, p.ph, FLAME, lean=0.2, name="flame")


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    if p.curl:
        _curled(cv, p)
        return
    ground = cv.ground
    cr = p.crouch
    C = (cv.gx - 2 + p.bx, ground - 10.5 + p.by + cr)
    br = p.breathe
    R = (C[0] - 4.2 * p.stretch, C[1])
    K = (C[0] + 4.0 * p.stretch, C[1] + 0.3)
    body_x = [px.rotate(p.pitch, C)]

    def B(pt):
        return px.rot_pt(pt, p.pitch, C)

    def foot(hx, i):
        f = p.feet[i]
        return (hx + f[0], ground - f[1])

    hips = {"nf": (K[0] + 0.2, K[1] + 2.0), "ff": (K[0] + 1.6, K[1] + 1.8),
            "nh": (R[0] + 0.2, R[1] + 1.6), "fh": (R[0] + 1.6, R[1] + 1.4)}
    # far legs, far ear and the tail go behind the body
    _front_leg(cv, B(hips["ff"]), foot(hips["ff"][0] + 0.4, 1), True)
    _hind_leg(cv, B(hips["fh"]), foot(hips["fh"][0] + 0.6, 3), True, cr)
    N0 = (K[0] + 1.6, K[1] - 2.4)
    with cv.xform(*body_x):
        with cv.xform(px.rotate(p.head, N0)):
            H = (N0[0] + 3.0, N0[1] - 3.4 + cr * 0.3)
            _ear(cv, H, p.ear, True)
        _tail(cv, (R[0] - 3.2, R[1] - 1.0), p)
    _hind_leg(cv, B(hips["nh"]), foot(hips["nh"][0] + 0.2, 2), False, cr)
    _front_leg(cv, B(hips["nf"]), foot(hips["nf"][0], 0), False)
    with cv.xform(*body_x):
        body_g = [cv.geom_limb([(R[0] - 0.8, R[1] + 0.2), (C[0], C[1] - 0.6 - br * 0.5), (K[0] + 0.4, K[1])],
                               [4.0 + br * 0.4, 3.8 + br, 3.7 + br * 0.4])]
        with cv.xform(px.rotate(p.head, N0)):
            if p.jaw > 0.05:  # lower jaw hinges open
                with cv.xform(px.rotate(-30 * p.jaw, (H[0] + 1.6, H[1] + 2.0))):
                    cv.limb([(H[0] + 1.6, H[1] + 2.2), (H[0] + 5.2, H[1] + 2.6)], [1.3, 0.7], WHITE,
                            shade="nolight", name="jaw")
                    cv.pixel(round(H[0] + 4.4), round(H[1] + 1.4), TOOTH, name="tooth")
            head_g = [cv.geom_limb([N0, H], [3.2, 3.0]), cv.geom_ellipse(H[0], H[1], 4.1, 3.7),
                      cv.geom_limb([(H[0] + 1.6, H[1] + 0.6), (H[0] + 5.7, H[1] + 1.6)], [2.5, 1.25])]
        cv.draw_geom(cv.union(*body_g, *head_g, weights=[1.0, 0.6, 0.9, 0.75]), FUR, name="body", sep="deep")
        # white bib + belly line
        cv.limb([(K[0] + 2.6, K[1] - 2.0), (K[0] + 3.2, K[1] + 2.4), (C[0] - 1.0, C[1] + 3.6)], [1.8, 1.6, 0.9],
                WHITE, shade="two", decal=True, clip="body")
        with cv.xform(px.rotate(p.head, N0)):
            cv.ellipse(H[0] + 2.6, H[1] + 2.1, 3.8, 1.5, WHITE, shade="soft", decal=True, clip="body")
            _ear(cv, H, p.ear, False)
            nx, ny = int(H[0] + 6.4), int(H[1] + 1.0)
            cv.pixels([(nx, ny), (nx - 1, ny)], NOSE, name="nose")
            if p.jaw <= 0.05:
                cv.pixels([(nx - 2, ny + 1), (nx - 3, ny + 1)], WHITE.shadow, name="mouth")
            _eye(cv, round(H[0] + 0.2), round(H[1] - 1.2), p.eye)
            jaws = cv.tp((H[0] + 6.8, H[1] + 2.0))

    if p.sparks is not None:
        fx = cv.layer(above=True, outline=False)
        hc.sparks(fx, jaws[0] + 1, jaws[1], p.sparks, n=6, radius=7, seed=3, aim=40, spread=200,
                  colors=(px.rgb("#fff1b8"), px.rgb("#ff9a36")))
    if p.hit:
        top = cv.layer(above=True, outline=False)
        px.impact(top, jaws[0] + 1, jaws[1], size=3, color=px.rgb("#ffc85a"))
