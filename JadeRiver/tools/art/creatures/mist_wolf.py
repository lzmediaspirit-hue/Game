"""Mist wolf - pale blue-grey spirit wolf whose tail frays into mist (Water / Soul).

View: side, facing right.  ~34 art px tall to the ear tips, ~58 long with the misty tail,
on a 96 px art canvas (cell 192).
Parts, back to front: far legs, mist tail (a short furred root that frays into drifting
mist puffs), near hind leg, body (haunch, waist, deep chest) + neck + head as one form,
darker saddle and pale belly decals, neck ruff, hackles (raised in the windup), near
foreleg, ears, muzzle, violet soul-glow eye.
Walk is a loping canter; windup crouches with the hackles up; attack is a lunge bite
(hit on frame 1); death dissolves the wolf into mist from the tail forward.
"""
import math

import numpy as np

import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "mist_wolf",
    "cell": 192,
    "anchor": [96, 168],
    "flying": False,
    "hit_frame": 1,
    "airborne": [["walk", 2], ["attack", 0], ["attack", 1], ["death", 3], ["death", 4]],
}

# ---- palette: pale blue-grey fur, slate saddle, misty tail, violet soul eyes -----------------
FUR = px.material("wolf_fur", "#f1f6f8", "#bccbd6", "#8a9db0", "#5d6f86", outline="#121a27",
                  thresholds=(0.9, 0.55, 0.2))
SADDLE = px.material("wolf_saddle", "#aebfce", "#8597ab", "#617388", "#44536a", outline="#121a27")
PAW = px.material("wolf_paw", "#7d8a9c", "#566276", "#3e4758", "#2a3140", outline="#0e1219")
MIST_T = px.material("wolf_mist", "#f6fafb", "#d6e2ea", "#aebfcd", "#8597ab", outline="#46566a")
NOSE = px.rgb("#1b2130")
EYE_GLOW = px.rgb("#d9c6ff")
EYE_CORE = px.rgb("#9b78d1")
EYE_DEEP = px.rgb("#3b2766")
TOOTH = px.rgb("#f7f3e6")
MOUTH = px.rgb("#5a2d3e")

# ---- poses ------------------------------------------------------------------------------------
# bx, by   body offset     crouch  lower the body     pitch  body tilt (deg)   stretch  body length
# head     head tilt       jaw     mouth 0..1         ear    ear angle (- = pinned back)
# feet     (dx, lift): near-front, far-front, near-hind, far-hind
# hackles  raised fur along the neck/back 0..1        tail  (lift, drift phase)
# eye      open|angry|squeeze|dead                    dissolve  0..1 turned to mist (death)
DEFAULTS = dict(bx=0, by=0, crouch=0, pitch=0, stretch=1.0, head=0, jaw=0.0, ear=0,
                feet=((0, 0), (0, 0), (0, 0), (0, 0)), hackles=0.0, tail=(0, 0.0), eye="open", dissolve=0.0,
                hit=False, fade=1.0, breathe=0.0, glow=0)

POSE = px.poses(DEFAULTS, {
    "idle": [
        dict(tail=(0, 0.0)),
        dict(tail=(1, 1.0), breathe=0.4, head=1),
        dict(tail=(1, 2.0), breathe=0.6, head=2),
        dict(tail=(0, 3.0), breathe=0.2, ear=-6),
    ],
    "walk": [  # loping canter: gather, push off, float, land
        dict(feet=((-2, 0), (-4, 1), (4, 0), (2, 0)), pitch=-3, tail=(1, 0.0), stretch=0.95, by=0),
        dict(feet=((3, 3), (1, 2), (0, 0), (-2, 0)), pitch=3, tail=(1, 1.0), by=-1),
        dict(feet=((6, 2), (4, 3), (-5, 2), (-7, 1)), pitch=2, tail=(2, 2.0), stretch=1.06, by=-3),
        dict(feet=((3, 0), (5, 1), (-6, 3), (-4, 2)), pitch=-3, tail=(1, 3.0), stretch=1.03, by=-1),
        dict(feet=((0, 0), (2, 0), (-2, 3), (-1, 2)), pitch=-4, tail=(1, 4.0), by=0),
        dict(feet=((-2, 0), (-1, 0), (2, 2), (1, 1)), pitch=-3, tail=(1, 5.0), stretch=0.97, by=0),
    ],
    "windup": [  # drops into a crouch, hackles bristle, lips peel back - held
        dict(crouch=2, bx=-1, head=-6, ear=-15, eye="angry", hackles=0.4, jaw=0.15, tail=(2, 0.5), glow=1,
             feet=((1, 0), (1, 0), (-1, 0), (-1, 0))),
        dict(crouch=5, bx=-3, head=-10, ear=-30, eye="angry", hackles=0.9, jaw=0.35, tail=(3, 1.0), glow=1,
             pitch=-4, stretch=0.95, feet=((2, 0), (2, 0), (-1, 0), (-1, 0))),
        dict(crouch=6, bx=-3, head=-12, ear=-35, eye="angry", hackles=1.0, jaw=0.4, tail=(3, 1.4), glow=2,
             pitch=-5, stretch=0.94, feet=((2, 0), (2, 0), (-1, 0), (-1, 0)), breathe=0.5),
    ],
    "attack": [  # lunge: springs off the hind legs and bites at full reach on frame 1
        dict(bx=6, by=-5, pitch=8, stretch=1.1, head=10, jaw=1.0, ear=-35, eye="angry", hackles=0.7, glow=2,
             tail=(3, 2.0), feet=((6, 6), (5, 5), (-6, 1), (-8, 0))),
        dict(bx=12, by=-2, pitch=-2, stretch=1.14, head=-6, jaw=0.05, ear=-30, eye="angry", hackles=0.5, glow=2,
             tail=(2, 3.0), feet=((6, 2), (5, 3), (-7, 3), (-9, 2)), hit=True),
        dict(bx=10, pitch=-3, stretch=1.05, head=-4, jaw=0.2, ear=-15, eye="angry", hackles=0.3, tail=(1, 4.0),
             feet=((2, 0), (1, 0), (-2, 0), (-3, 0))),
        dict(bx=5, head=0, ear=-5, tail=(1, 5.0), feet=((1, 0), (0, 0), (-1, 0), (0, 0))),
    ],
    "hurt": [
        dict(bx=-4, by=-2, head=16, eye="squeeze", jaw=0.4, ear=-35, pitch=6, tail=(3, 1.0),
             feet=((1, 3), (0, 2), (0, 0), (0, 0))),
        dict(bx=-2, head=8, eye="squeeze", ear=-20, pitch=3, tail=(2, 2.0)),
    ],
    "death": [  # recoils, sinks, and unravels into drifting mist from the tail forward
        dict(bx=-4, by=-2, head=18, eye="squeeze", jaw=0.5, ear=-35, pitch=6, tail=(3, 1.0),
             feet=((1, 3), (0, 2), (0, 0), (0, 0))),
        dict(bx=-4, crouch=6, head=-12, eye="dead", ear=-40, tail=(0, 2.0), dissolve=0.2,
             feet=((2, 0), (2, 0), (-1, 0), (-1, 0))),
        dict(bx=-4, crouch=8, head=-16, eye="dead", ear=-40, tail=(0, 3.0), dissolve=0.5,
             feet=((3, 0), (3, 0), (-1, 0), (-1, 0))),
        dict(bx=-4, crouch=8, head=-16, eye="dead", ear=-40, tail=(0, 4.0), dissolve=0.8,
             feet=((3, 0), (3, 0), (-1, 0), (-1, 0)), fade=0.6),
        dict(bx=-4, crouch=8, head=-16, eye="dead", ear=-40, tail=(0, 5.0), dissolve=1.0,
             feet=((3, 0), (3, 0), (-1, 0), (-1, 0)), fade=0.3),
    ],
})


# ---- parts ------------------------------------------------------------------------------------
def _front_leg(cv, hip, foot, far):
    fx, fy = foot
    elbow = (hip[0] - 0.4 + (fx - hip[0]) * 0.3, hip[1] + (fy - hip[1]) * 0.42)
    wrist = (fx - 0.3, fy - 2.4)
    cv.limb([hip, elbow, wrist, (fx, fy - 1.2)], [3.0, 1.9, 1.3, 1.2], FUR, shade="dark" if far else "two",
            name="leg", sep=False if far else "deep")
    cv.ellipse(fx + 0.8, fy - 0.8, 1.9, 1.2, PAW, shade="dark" if far else "two", name="paw")


def _hind_leg(cv, hip, foot, far, crouch):
    fx, fy = foot
    knee = (hip[0] + 2.4, hip[1] + 4.2 - crouch * 0.3)
    hock = (fx - 2.2 - crouch * 0.35, fy - 4.4 + crouch * 0.3)
    cv.limb([hip, knee, hock, (fx, fy - 1.2)], [3.8, 2.3, 1.4, 1.2], FUR, shade="dark" if far else "two",
            name="leg")
    cv.ellipse(fx + 0.8, fy - 0.8, 1.9, 1.2, PAW, shade="dark" if far else "two", name="paw")


def _tail(cv, fx, root, p, ground):
    """Bushy tail hanging from the rump; its lower half pales into mist and frays into
    wisps that trail behind, with a puff drifting off."""
    lift, ph = p.tail
    w = math.sin(ph * 1.2)
    a0 = 205 - lift * 12  # hang angle (deg): lifts toward horizontal when excited
    pts = [root]
    q = root
    for k, (ln, bend) in enumerate(((3.6, 0), (3.8, 12), (3.6, 22), (3.0, 30))):
        q = px.polar(q, a0 + bend + w * 4 * k / 3, ln)
        pts.append((q[0], min(q[1], ground - 3.0)))
    cv.limb(pts, [2.2, 3.4, 3.8, 3.4, 2.2], FUR, name="tail")
    cv.limb(pts[2:], [3.8, 3.4, 2.2], MIST_T, shade="soft", decal=True, clip="tail", name="tail")
    tip = pts[-1]
    back = math.degrees(math.atan2(-(tip[1] - pts[-2][1]), tip[0] - pts[-2][0]))
    for k, (ln, da, wd) in enumerate(((7.0, 20, 1.8), (5.5, -12, 1.4))):
        qq = [tip]
        for j in range(1, 4):
            t = j / 3
            a = back + da * t + math.sin(ph * 1.5 + k * 2.1 + t * 2.5) * 14 * t
            qq.append(px.polar(qq[-1], a, ln / 3))
        qq = [(x, min(y, ground - 1.5)) for x, y in qq]
        cv.limb(qq, [wd + 0.4, wd, wd * 0.7, 0.6], MIST_T, shade="soft", name="tail")
    d = (ph * 0.9) % 3.0
    hc.mist_puff(fx, tip[0] - 8.5 - d * 2.2, min(tip[1] - 2.0 - d * 1.5, ground - 4), 2.6 - 0.3 * d, mat=MIST_T)


def _eye(cv, fx, x, y, state, glow):
    if state == "squeeze":
        hc.eye_stamp(cv, ["kk.", "..k"], x - 1, y, {})
    elif state == "dead":
        hc.eye_stamp(cv, ["k.k", ".k.", "k.k"], x - 1, y - 1, {})
    else:
        hc.eye_stamp(cv, ["gv", "vc"], x, y, {"v": EYE_CORE, "c": EYE_DEEP})
        brow = [(x - 1, y - 1), (x, y - 1), (x + 1, y - 1)]
        if state == "angry":
            brow = [(x - 1, y - 2), (x, y - 1), (x + 1, y - 1), (x + 2, y)]
        cv.pixels(brow, FUR.deep, name="brow")
        if glow:  # faint soul glow trailing from the eye
            fx.line((x - 1, y + 1), (x - 1 - glow, y + 1), EYE_CORE, name="glow")
            fx.line((x - 1, y + 2), (x - 2 - glow, y + 2), EYE_GLOW, name="glow")


def _ear(cv, H, ang, far):
    pivot = (H[0] - 1.0, H[1] - 3.4)
    pts = [px.rot_pt(q, ang, pivot) for q in ((H[0] - 3.4, H[1] - 2.2), (H[0] - 1.8, H[1] - 9.4),
                                              (H[0] + 0.8, H[1] - 3.4))]
    if far:
        pts = [(x + 2.2, y + 0.3) for (x, y) in pts]
        cv.polygon(pts, SADDLE, shade="dark", name="ear_far")
        return
    cv.polygon(pts, FUR, name="ear", sep="deep")
    cv.polygon([px.lerp_pt(pts[0], pts[2], 0.5), px.lerp_pt(pts[0], pts[1], 0.65), px.lerp_pt(pts[2], pts[1], 0.5)],
               SADDLE, shade="two", decal=True, clip="ear")


def _hackles(cv, pts, amount, clip_name="body"):
    """Bristling fur spikes along a spine poly-line (``amount`` 0..1)."""
    if amount <= 0:
        return
    for a, b in zip(pts, pts[1:]):
        for t in (0.2, 0.6):
            q = px.lerp_pt(a, b, t)
            d = (b[0] - a[0], b[1] - a[1])
            ln = math.hypot(*d) or 1.0
            n = (d[1] / ln, -d[0] / ln)  # up-ish normal for a left-to-right spine
            tip = (q[0] + n[0] * (1.5 + 2.8 * amount) - d[0] / ln * 1.2, q[1] + n[1] * (1.5 + 2.8 * amount))
            cv.polygon([(q[0] - d[0] / ln * 1.6, q[1] - d[1] / ln * 1.6 + 0.6), tip,
                        (q[0] + d[0] / ln * 1.6, q[1] + d[1] / ln * 1.6 + 0.6)], SADDLE, shade="two", name=clip_name)


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    ground = cv.ground
    cr = p.crouch
    C = (cv.gx + 1 + p.bx, ground - 19.5 + p.by + cr)
    br = p.breathe
    st = p.stretch
    R = (C[0] - 9.0 * st, C[1] - 0.8)
    K = (C[0] + 7.0 * st, C[1] + 0.3)
    body_x = [px.rotate(p.pitch, C)]

    def B(pt):
        return px.rot_pt(pt, p.pitch, C)

    def foot(hx, i):
        f = p.feet[i]
        return (hx + f[0], ground - f[1])

    hips = {"nf": (K[0] + 1.0, K[1] + 4.4), "ff": (K[0] + 3.0, K[1] + 4.0),
            "nh": (R[0] + 0.4, R[1] + 3.0), "fh": (R[0] + 2.6, R[1] + 2.6)}
    mist = cv.layer(above=False, outline=True)
    glowfx = cv.layer(above=True, outline=False)
    _front_leg(cv, B(hips["ff"]), foot(hips["ff"][0] + 0.6, 1), True)
    _hind_leg(cv, B(hips["fh"]), foot(hips["fh"][0] + 1.2, 3), True, cr)
    N0 = (K[0] + 3.0, K[1] - 3.4)
    with cv.xform(*body_x):
        with cv.xform(px.rotate(p.head, N0)):
            H = (N0[0] + 4.6, N0[1] - 4.4 + cr * 0.2)
            _ear(cv, H, p.ear, True)
        _tail(cv, mist, (R[0] - 5.2, R[1] - 3.4), p, ground)
    _hind_leg(cv, B(hips["nh"]), foot(hips["nh"][0] + 0.8, 2), False, cr)
    with cv.xform(*body_x):
        body_g = [cv.geom_ellipse(R[0], R[1] - 0.2, 6.6, 6.0 + br * 0.3, angle=-6),
                  cv.geom_limb([(R[0] + 2.0, R[1] - 0.8), (C[0] + 0.5, C[1] - 1.6 - br * 0.4), (K[0] - 2.0, K[1] - 0.6)],
                               [5.2, 4.4 + br * 0.4, 6.0]),
                  cv.geom_ellipse(K[0], K[1] + 0.6, 7.6, 7.4 + br, angle=10)]
        with cv.xform(px.rotate(p.head, N0)):
            if p.jaw > 0.05:  # lower jaw drops open, teeth showing
                with cv.xform(px.rotate(-30 * p.jaw, (H[0] + 2.0, H[1] + 2.4))):
                    cv.limb([(H[0] + 2.0, H[1] + 2.8), (H[0] + 8.6, H[1] + 3.4)], [1.9, 1.1], FUR, shade="nolight",
                            name="jaw")
                    cv.pixels([(round(H[0] + 7.4), round(H[1] + 2.0)), (round(H[0] + 5.2), round(H[1] + 2.2))], TOOTH,
                              name="tooth")
            head_g = [cv.geom_limb([N0, H], [5.6, 4.4]), cv.geom_ellipse(H[0], H[1], 5.0, 4.4),
                      cv.geom_limb([(H[0] + 2.0, H[1] + 0.2), (H[0] + 9.0, H[1] + 1.6)], [3.2, 1.7])]
        cv.draw_geom(cv.union(*body_g, *head_g, weights=[0.9, 0.8, 1.0, 0.6, 0.9, 0.75]), FUR, name="body",
                     sep="deep")
        # darker saddle along the back, pale belly, ruff
        cv.limb([(R[0] - 3.0, R[1] - 4.5), (C[0], C[1] - 5.2), (K[0] - 1.0, K[1] - 5.6)], [2.6, 2.4, 2.2], SADDLE,
                shade="two", decal=True, clip="body")
        cv.limb([(R[0] + 3.0, R[1] + 4.6), (K[0] - 1.0, K[1] + 7.0)], [1.4, 2.6], FUR.step(-1), shade="two",
                decal=True, clip="body")
        spine = [(R[0] - 2.0, R[1] - 5.8), (C[0], C[1] - 6.0), (K[0] - 2.0, K[1] - 7.0), (N0[0], N0[1] - 4.8)]
        _hackles(cv, spine, p.hackles)
        with cv.xform(px.rotate(p.head, N0)):
            # ruff: a few pale tufts at the throat
            for k in range(3):
                q = px.lerp_pt((N0[0] + 3.6, N0[1] + 4.6), (K[0] + 5.2, K[1] + 3.6), k / 2)
                cv.polygon([(q[0] - 1.2, q[1] - 1.0), (q[0] + 1.6, q[1] + 1.8), (q[0] + 1.4, q[1] - 0.6)], FUR,
                           shade="soft", name="body")
            _ear(cv, H, p.ear, False)
            cv.ellipse(H[0] + 5.0, H[1] + 2.4, 3.8, 1.2, FUR.step(-1), shade="soft", decal=True, clip="body")
            nx, ny = round(H[0] + 9.6), round(H[1] + 0.8)
            cv.pixels([(nx - 1, ny), (nx - 2, ny), (nx - 1, ny + 1)], NOSE, name="nose")
            if p.jaw <= 0.05:
                cv.line((nx - 6, ny + 2), (nx - 3, ny + 2), FUR.deep, name="mouth")
            else:
                cv.pixel(nx - 3, ny + 2, MOUTH, name="mouth")
            _eye(cv, glowfx, round(H[0] + 1.2), round(H[1] - 1.4), p.eye, p.glow)
            snout = cv.tp((H[0] + 10.0, H[1] + 1.8))
    _front_leg(cv, B(hips["nf"]), foot(hips["nf"][0] + 0.2, 0), False)

    if p.dissolve > 0:  # the wolf unravels from the tail forward into mist
        d = p.dissolve
        x_left, x_right = R[0] - 22.0, K[0] + 20.0
        front = x_left + (d ** 1.5) * (x_right - x_left + 6.0)
        ragged = front + 2.2 * np.sin(cv.Y * 0.8 + d * 6.0) + 1.2 * np.sin(cv.Y * 2.1)
        gone = cv.filled & (cv.X < ragged)
        if gone.any():
            cv._commit(gone, np.where(gone, 1, -1).astype(np.int8), px.flat(px.INK), erase=True)
        hc.drop_specks(cv, 5)
        top = cv.layer(above=True, outline=True)
        ys = [C[1] - 8.0, C[1] - 2.5, C[1] + 3.5, ground - 5.0]
        for k, y in enumerate(ys):  # billowing mist along the dissolving edge
            x = front - 1.0 + (k % 2) * 1.5
            if x_left - 2 < x < x_right + 4:
                hc.mist_puff(top, x, y - d * 2.0, 2.4 + 0.6 * ((k + 1) % 3), mat=MIST_T)
        for k in range(3 + int(3 * d)):  # older mist drifting up and back
            x = front - 7.0 - k * 5.5
            y = C[1] - 5.0 - d * 6.0 - (k % 3) * 3.0 + k * 1.5
            if x > 8:
                hc.mist_puff(top, x, y, 2.6 - 0.25 * k, mat=MIST_T)
    if p.hit:
        fx = cv.layer(above=True, outline=False)
        px.impact(fx, snout[0] + 1, snout[1], size=4)
