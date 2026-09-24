"""Jade crane chick - fluffy white-and-jade crane chick on long legs, a Wind pet.

View: side, facing right.  ~36 art px tall (long legs), ~24 long.
Parts, back to front: far leg, far stubby wing, jade tail tuft, fluffy down body (a ball
with a tufted fringe), jade down tips as decals, neck + round head as one form, near leg,
near stubby wing (jade, three blunt feather fingers), beak, red crown, head tufts, eye.
Walk is a high-stepping strut with a head bob; the windup spreads both wings and puffs
up; the attack is a wing buffet with wind lines.  Death folds it down to sit with the
head tucked, then it fades back into its token.
"""
import math

import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "jade_crane_chick",
    "cell": 128,
    "anchor": [64, 112],
    "flying": False,
    "hit_frame": 2,
    "airborne": [["attack", 1]],
}

# ---- palette: white down with jade-tinted shadows, jade wings, horn beak, red crown ---------
DOWN = px.material("chick_down", "#ffffff", "#e6f3ee", "#a9d3c5", "#6ea596", outline="#0c2622",
                   thresholds=(0.9, 0.52, 0.16))
JADE = px.material("chick_jade", "#9cf0d2", "#43b393", "#277d6a", "#17514a", outline="#07201d")
LEG = px.material("chick_leg", "#9fbab0", "#6e8d85", "#4e6a66", "#35494a", outline="#0c1a1c")
BEAK = px.material("chick_beak", "#fff0b0", "#e2c86a", "#b0944a", "#76663a", outline="#1e1a0c")
CROWN = px.material("chick_crown", "#ff9a8a", "#e45858", "#b33a44", "#7a2432", outline="#240a10")
IRIS = px.rgb("#2a1a12")

# ---- poses ------------------------------------------------------------------------------------
# bx, by    body offset            lean  body tilt (deg, + = nose up)   puff  fluff swell 0..1
# neck      head reach (px fwd)    nod   head drop (px)    head  head tilt (deg)
# legs      (dx, lift) for near, far
# wing      ((dir, spread), (dir, spread)) near/far: direction deg (0 fwd, 90 up, 195 folded)
# beak      beak open 0..1         eye   open|angry|squeeze|sleep      wind  wind-line life
# sit       folded sitting (death) tuck  head tucked into the wing     fade  opacity
DEFAULTS = dict(bx=0, by=0, lean=0, puff=0.0, neck=0.0, nod=0.0, head=0, legs=((0, 0), (0, 0)),
                wing=((195, 0.0), (190, 0.0)), beak=0.0, eye="open", wind=None, hit=False, sit=False,
                tuck=False, fade=1.0, breathe=0.0)

POSE = px.poses(DEFAULTS, {
    "idle": [
        dict(),
        dict(breathe=0.4, nod=0.5),
        dict(breathe=0.6, nod=0.5, head=4, wing=((186, 0.2), (184, 0.1))),
        dict(breathe=0.2, head=2, eye="sleep"),
    ],
    "walk": [  # proud strut: each foot lifts high, the head bobs back then shoots forward
        dict(legs=((3, 0), (-3, 0)), neck=1.5, by=0),
        dict(legs=((0, 0), (-1, 5)), neck=-0.5, by=-1),
        dict(legs=((-2, 0), (3, 6)), neck=-1.0, by=-1, head=4),
        dict(legs=((-3, 0), (3, 0)), neck=1.5, by=0),
        dict(legs=((-1, 5), (0, 0)), neck=-0.5, by=-1),
        dict(legs=((3, 6), (-2, 0)), neck=-1.0, by=-1, head=4),
    ],
    "windup": [  # wings spread wide, fluff puffs up, head drawn back - held
        dict(wing=((165, 0.5), (140, 0.4)), puff=0.4, neck=-1.0, head=8, eye="angry", beak=0.3, lean=4),
        dict(wing=((152, 0.9), (118, 0.8)), puff=0.8, neck=-2.0, head=12, eye="angry", beak=0.6, lean=8,
             by=-1),
        dict(wing=((146, 1.0), (110, 1.0)), puff=1.0, neck=-2.0, head=14, eye="angry", beak=0.7, lean=9,
             by=-1, legs=((1, 0), (-1, 0))),
    ],
    "attack": [  # wing buffet: a hop forward and both wings sweep down - hit on frame 2
        dict(wing=((128, 1.0), (100, 1.0)), puff=0.8, neck=0.0, head=4, eye="angry", beak=0.4, lean=4, bx=1,
             legs=((1, 0), (-1, 0))),
        dict(wing=((62, 1.0), (54, 0.9)), puff=0.6, neck=2.0, head=-4, eye="angry", beak=0.8, lean=-6, bx=4,
             by=-3, legs=((1, 3), (-1, 2)), wind=0.2),
        dict(wing=((-12, 1.0), (4, 0.9)), puff=0.5, neck=3.0, head=-8, eye="angry", beak=0.6, lean=-8, bx=6,
             legs=((2, 0), (-2, 0)), wind=0.5, hit=True),
        dict(wing=((200, 0.4), (196, 0.3)), puff=0.2, neck=1.0, head=-2, lean=-2, bx=4, wind=0.85,
             legs=((1, 0), (-1, 0))),
    ],
    "hurt": [
        dict(bx=-3, by=-1, head=18, neck=-2.0, eye="squeeze", puff=0.9, beak=0.5, lean=8,
             wing=((150, 0.6), (120, 0.5)), legs=((1, 2), (0, 0))),
        dict(bx=-2, head=8, neck=-1.0, eye="squeeze", puff=0.5, lean=4, wing=((175, 0.3), (160, 0.2))),
    ],
    "death": [  # folds down to sit, tucks its head into the wing and fades into its token
        dict(bx=-3, by=-1, head=18, neck=-2.0, eye="squeeze", puff=0.9, beak=0.4, lean=8,
             wing=((150, 0.6), (120, 0.5)), legs=((1, 2), (0, 0))),
        dict(bx=-2, by=5, head=-10, neck=-1.0, nod=2.0, eye="sleep", puff=0.4, legs=((1, 0), (-1, 0)),
             sit=True),
        dict(bx=-2, sit=True, tuck=True, eye="sleep", puff=0.3),
        dict(bx=-2, sit=True, tuck=True, eye="sleep", puff=0.3, fade=0.6),
        dict(bx=-2, sit=True, tuck=True, eye="sleep", puff=0.3, fade=0.3),
    ],
})


# ---- parts ------------------------------------------------------------------------------------
def _leg(cv, hip, foot, lift, far):
    """Long crane leg: the heel bends backward; toes spread flat or curl when lifted."""
    shade = "dark" if far else "two"
    fx, fy = foot
    if lift > 0:  # lifted: the heel rises and the foot swings up under the body
        heel = (hip[0] - 1.5, hip[1] + 6.0 - lift * 0.3)
        ankle = (fx + 0.5, fy - 1.0)
    else:
        heel = px.ik2(hip, (fx, fy - 0.5), 6.8, 7.4, bend=-1)
        ankle = (fx, fy - 0.5)
    cv.limb([hip, heel, ankle], [1.2, 0.95, 0.75], LEG, shade=shade, name="leg")
    cv.circle(heel[0], heel[1], 1.0, LEG, shade=shade, name="leg")
    if lift > 0:  # toes hang, pointing down-forward
        cv.limb([ankle, (fx + 2.2, fy + 0.8)], [0.7, 0.5], LEG, shade=shade, name="toe")
    else:
        cv.limb([(fx - 1.6, fy), (fx + 2.6, fy)], [0.6, 0.5], LEG, shade=shade, name="toe")


def _wing(cv, shoulder, a, spread, far):
    """Stubby jade wing: a rounded paddle with three blunt feather fingers.
    ``a`` = the direction it points (deg: 0 forward, 90 up, 195 folded back)."""
    ln = 4.2 + 5.0 * spread
    tip = px.polar(shoulder, a, ln)
    shade = "dark" if far else "full"
    name = "wing_far" if far else "wing"
    g = [cv.geom_limb([shoulder, px.lerp_pt(shoulder, tip, 0.55), tip], [2.3, 2.9, 2.3])]
    for off in (-34, 0, 34):
        fa = a + off * (0.3 + 0.7 * spread)
        root = px.polar(tip, a + 180, 1.2)
        ft = px.polar(root, fa, 2.6 + 1.6 * spread - abs(off) / 30)
        g.append(cv.geom_limb([root, ft], [1.3, 0.9]))
    cv.draw_geom(cv.union(*g, weights=[1.0, 0.6, 0.6, 0.6]), JADE, shade=shade, name=name,
                 sep=False if far else "deep")
    # feather-finger gaps: short dark notches between the fingers
    if True:
        for off in (-17, 17):
            fa = a + off * (0.3 + 0.7 * spread)
            q0 = px.polar(tip, fa, 0.6)
            q1 = px.polar(tip, fa, 2.0 + spread)
            cv.line((round(q0[0]), round(q0[1])), (round(q1[0]), round(q1[1])), JADE.step(1), band=None,
                    decal=True, clip=name)


def _fluff(cv, B, rx, ry, puff):
    """Round down ball with a tufted fringe along the belly and the back."""
    g = [cv.geom_ellipse(B[0], B[1], rx, ry)]
    tufts = []
    for k in range(7):
        t = -25 + k * 30  # degrees around the lower half and rump
        base = (B[0] + (rx - 0.6) * math.cos(math.radians(180 + t)),
                B[1] - (ry - 0.6) * math.sin(math.radians(180 + t)))
        tip = px.polar(base, 180 + t - 18, 2.2 + 1.0 * puff)
        side = px.polar(base, 180 + t + 90, 1.8)
        side2 = px.polar(base, 180 + t - 90, 1.8)
        tufts.append([side, tip, side2])
    for tri in tufts:
        g.append(cv.geom_polygon(tri))
    return cv.union(*g, weights=[1.0] + [0.2] * len(tufts))


def _head(cv, H, p, beak_open):
    """Round head + short neck-joined skull, beak, red crown, fluff tufts, eye."""
    # beak: upper mandible, and a lower one that drops open
    with cv.xform(px.rotate(-22 * beak_open, (H[0] + 2.8, H[1] + 1.2))):
        cv.polygon([(H[0] + 3.0, H[1] + 0.8), (H[0] + 7.0, H[1] + 1.8), (H[0] + 3.0, H[1] + 2.4)], BEAK,
                   shade="two", name="beak")
    cv.polygon([(H[0] + 2.8, H[1] - 1.0), (H[0] + 5.0, H[1] - 0.2), (H[0] + 8.2, H[1] + 1.4),
                (H[0] + 3.0, H[1] + 1.6)], BEAK, name="beak", sep="deep")


def _eye(cv, x, y, state):
    if state == "squeeze":
        hc.eye_stamp(cv, ["k.", ".k", "k."], x, y - 1, {})
    elif state == "sleep":
        hc.eye_stamp(cv, ["k..k", ".kk."], x - 1, y + 1, {})
    else:
        hc.eye_stamp(cv, [".kk", "kgk", "kkk"], x - 1, y - 1, {"i": IRIS})
        if state == "angry":
            cv.pixels([(x - 1, y - 2), (x, y - 2), (x + 1, y - 1), (x + 2, y - 1)], JADE.deep, name="brow")


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    ground = cv.ground
    B = (cv.gx - 3 + p.bx, ground - 19.5 + p.by)
    if p.sit:
        B = (cv.gx - 2 + p.bx, ground - 6.4 + (0 if p.tuck else -1))
        cv.snap_ground = True
    br = p.breathe
    rx, ry = 8.4 + p.puff * 0.9 + br * 0.3, 7.4 + p.puff * 0.8 + br * 0.4
    body_x = px.rotate(p.lean, B)

    def foot(dx, i):
        f = p.legs[i]
        return (B[0] + dx + f[0], ground - f[1]), f[1]

    hips = ((B[0] + 1.0, B[1] + 5.0), (B[0] - 1.2, B[1] + 4.6))
    wn, wf = p.wing
    shoulder_n = px.rot_pt(px.lerp_pt((B[0] + 1.6, B[1] - 1.4), (B[0] - 0.5, B[1] - 4.2), wn[1]), p.lean, B)
    shoulder_f = px.rot_pt(px.lerp_pt((B[0] + 3.0, B[1] - 3.2), (B[0] - 1.5, B[1] - 5.4), wf[1]), p.lean, B)
    if not p.sit:
        ft, lift = foot(-0.6, 1)
        _leg(cv, hips[1], ft, lift, True)
    if not p.tuck:
        _wing(cv, shoulder_f, wf[0], wf[1], True)
    with cv.xform(body_x):
        # jade tail tuft
        T = (B[0] - rx + 0.8, B[1] - 1.0)
        cv.polygon([(T[0] + 1.5, T[1] - 1.8), (T[0] - 3.4, T[1] - 3.4 - p.puff), (T[0] - 2.2, T[1] - 0.6),
                    (T[0] - 3.6, T[1] + 1.2), (T[0] + 1.2, T[1] + 2.2)], JADE, shade="two", name="tail")
        # neck + head reach
        nod = p.nod
        H = (B[0] + 6.4 + p.neck, B[1] - 9.6 + nod + p.puff * 0.3)
        if p.tuck:
            H = (B[0] + 3.4, B[1] - 4.6)
        with cv.xform(px.rotate(p.head, (B[0] + 4.0, B[1] - 4.0))):
            neck_g = cv.geom_limb([(B[0] + 3.6, B[1] - 3.0), (H[0] - 0.8, H[1] + 2.0)], [3.4, 2.8])
            head_g = cv.geom_ellipse(H[0], H[1], 4.4, 4.1)
        body_g = _fluff(cv, B, rx, ry, p.puff)
        cv.draw_geom(cv.union(body_g, neck_g, head_g, weights=[1.0, 0.5, 0.9]), DOWN, name="body")
        # jade-tipped down along the back
        cv.limb([(B[0] - rx + 1.0, B[1] - 1.5), (B[0] - 3.0, B[1] - ry + 0.8), (B[0] + 2.0, B[1] - ry + 0.5)],
                [1.3, 1.1, 0.7], JADE.with_(light=JADE.light, base=px.rgb("#8fdcc3"), shadow=px.rgb("#5fb39c"),
                                           deep=px.rgb("#3f8a78")), shade="two", decal=True, clip="body")
    if not p.sit:
        ft, lift = foot(0.8, 0)
        _leg(cv, hips[0], ft, lift, False)
    else:  # folded legs: the heels poke out under the fluff
        cv.limb([(B[0] - 1.0, B[1] + 5.6), (B[0] + 4.6, B[1] + 5.8)], 0.8, LEG, shade="two", name="leg")
    with cv.xform(body_x):
        with cv.xform(px.rotate(p.head, (B[0] + 4.0, B[1] - 4.0))):
            if not p.tuck:
                _head(cv, H, p, p.beak)
            # red crown + down tufts on the crown
            cv.ellipse(H[0] - 0.2, H[1] - 3.2, 1.7, 1.1, CROWN, shade="soft", decal=True, clip="body")
            cv.pixels([(round(H[0]) - 2, round(H[1] - 4.4)), (round(H[0]) - 3, round(H[1] - 5.4))], DOWN.base,
                      name="tuft")
            cv.pixel(round(H[0]) - 1, round(H[1] - 4.6), CROWN.base, name="tuft")
            _eye(cv, round(H[0] + 0.4), round(H[1] - 0.8), p.eye)
        if p.tuck:  # the near wing folds over the tucked head
            _wing(cv, (B[0] + 2.6, B[1] - 2.8), 200, 0.2, False)
    if not p.tuck:
        _wing(cv, shoulder_n, wn[0], wn[1], False)
        wtip = (B[0] + rx + 6, B[1] + 1)
    if p.wind is not None:
        w = cv.layer(above=True, outline=False)
        t = p.wind
        for k, (dy, ln, cu) in enumerate(((-3, 6, 0.0), (1, 8, 1.0), (5, 5, 0.0))):
            hc.wind_streak(w, B[0] + 9 + t * 7 + k * 2, B[1] + dy + 2, ln * (0.6 + 0.6 * t), curl=cu)
    if p.hit:
        top = cv.layer(above=True, outline=False)
        px.impact(top, wtip[0], wtip[1], size=3)
