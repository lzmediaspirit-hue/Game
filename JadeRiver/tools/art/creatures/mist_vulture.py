"""Mist vulture - grey-white vulture with frayed, mist-dissolving wing edges (Wind).

View: side, facing right, flying (cell 192, anchor at the body centre).  ~40 art px tall
with the wings mid-stroke.
Parts, back to front: mist wisps (FX), far wing (dark), tail fan, tucked legs + talons, body,
white neck ruff, bald pink head, hooked ivory beak, eye; near wing in front (fingered
primaries, a frayed pale trailing edge dissolving into mist).
Idle / walk: wing-flap cycles.  Windup: rises with a big upstroke, then folds its wings
and tips nose-down (held).  Attack: dives and rakes with its talons on frame 1, wings flaring.
Death: tumbles out of the air, falling and fading.
"""
import math

import pixel as px

SPEC = {
    "id": "mist_vulture",
    "cell": 192,
    "anchor": [96, 96],
    "flying": True,
    "hit_frame": 1,
}

# ---- palette: grey-white plumage, slate shadows, bald pink head, mist ------------------------
FEATHER = px.material("mv_feather", "#f6fafa", "#cbd6dc", "#8c9eae", "#5a6a82", outline="#131b28",
                      thresholds=(0.88, 0.5, 0.14))
FLIGHT = px.material("mv_flight", "#bcc8d0", "#8e9cac", "#606e84", "#3e485c", outline="#10161f",
                     thresholds=(0.88, 0.5, 0.14))
BODY = px.material("mv_body", "#e2e8ec", "#a9b5c0", "#717f92", "#48546a", outline="#10161f",
                   thresholds=(0.88, 0.5, 0.14))
MIST = px.material("mv_mist", "#ffffff", "#e2eef4", "#b6ccd8", "#88a4b8", outline="#4a6072")
SKIN = px.material("mv_skin", "#ffd4ca", "#e9948e", "#b4646c", "#764252", outline="#1f0f16")
BEAK = px.material("mv_beak", "#f6eed8", "#d8ccae", "#a09478", "#686052", outline="#17120c")
LEG = px.material("mv_leg", "#dcd0a8", "#b0a078", "#7c7058", "#524a40", outline="#15120e")
TALON = px.rgb("#1d1b20")
IRIS = px.rgb("#c8402e")

# ---- poses --------------------------------------------------------------------------------
# bx, by  body offset       tilt  body pitch (deg, - = nose down)
# wing    (angle, span, bend): near wing direction (deg, 90 = up, 180 = back, 250 = down-back),
#         span = projected length (1 = spread flat to the camera, ~0.4 = mid-stroke), bend =
#         extra angle of the hand past the wrist
# legs    talons: 0 tucked .. 1 thrust forward   head  head tilt   jaw  beak gape 0..1
# eye     open|angry|squeeze|dead   mist  mist trail strength   streak  dive speed lines
# fade    opacity   hit  impact
DEFAULTS = dict(bx=0, by=0, tilt=0, wing=(150, 0.5, 10), legs=0.0, head=0, jaw=0.0, eye="open", mist=1.0,
                streak=False, fade=1.0, hit=False)

UP, MIDDOWN, DOWN, MIDUP = (98, 1.0, 14), (158, 0.5, 8), (250, 0.95, -14), (142, 0.45, 12)

POSE = px.poses(DEFAULTS, {
    "idle": [  # slow soaring flaps
        dict(wing=UP, by=1),
        dict(wing=MIDDOWN, by=0),
        dict(wing=DOWN, by=-1),
        dict(wing=MIDUP, by=0),
    ],
    "walk": [  # stronger flapping flight, leaning into it
        dict(wing=(94, 1.05, 18), by=1, tilt=-6, head=-2),
        dict(wing=(128, 0.7, 12), by=1, tilt=-6),
        dict(wing=(172, 0.45, 4), by=0, tilt=-6, head=2),
        dict(wing=(246, 1.0, -16), by=-1, tilt=-6, head=2),
        dict(wing=(205, 0.55, -8), by=-1, tilt=-6),
        dict(wing=(140, 0.5, 12), by=0, tilt=-6, head=-2),
    ],
    "windup": [  # a big upstroke to climb, then the wings fold and it tips nose-down - held
        dict(wing=(92, 1.1, 20), by=-3, tilt=8, head=6, eye="angry", jaw=0.4),
        dict(wing=(138, 0.75, 30), by=-6, tilt=-14, head=-4, eye="angry", jaw=0.6, legs=0.2, mist=1.4),
        dict(wing=(150, 0.7, 34), by=-7, tilt=-26, head=-6, eye="angry", jaw=0.7, legs=0.3, mist=1.8),
    ],
    "attack": [  # the dive: plunge, rake with the talons (hit), flare, climb away
        dict(wing=(160, 0.6, 30), bx=6, by=4, tilt=-42, head=-6, eye="angry", legs=0.6, streak=True, jaw=0.5),
        dict(wing=(96, 1.1, 22), bx=10, by=10, tilt=6, head=-10, eye="angry", legs=1.0, hit=True, jaw=0.8),
        dict(wing=(245, 0.95, -14), bx=8, by=6, tilt=4, eye="angry", legs=0.6, jaw=0.3),
        dict(wing=(150, 0.5, 10), bx=3, by=2, tilt=0, legs=0.2),
    ],
    "hurt": [
        dict(wing=(88, 1.1, 30), bx=-4, by=-2, tilt=18, head=16, eye="squeeze", jaw=0.8, mist=1.6),
        dict(wing=(130, 0.7, 14), bx=-3, by=-1, tilt=10, head=8, eye="squeeze", jaw=0.3, mist=1.3),
    ],
    "death": [  # knocked out of the air: tumble, fall, fade into mist
        dict(wing=(86, 1.1, 34), bx=-3, by=-2, tilt=20, head=20, eye="squeeze", jaw=0.9, mist=1.6),
        dict(wing=(110, 0.9, 40), bx=-4, by=4, tilt=70, head=30, eye="dead", jaw=0.6, mist=1.8),
        dict(wing=(200, 0.8, 30), bx=-5, by=11, tilt=130, head=30, eye="dead", jaw=0.6, mist=2.0),
        dict(wing=(230, 0.8, 30), bx=-5, by=16, tilt=165, head=30, eye="dead", jaw=0.6, mist=2.2, fade=0.6),
        dict(wing=(240, 0.8, 30), bx=-5, by=20, tilt=178, head=30, eye="dead", jaw=0.6, mist=2.4, fade=0.3),
    ],
})


# ---- parts --------------------------------------------------------------------------------
def _wing(cv, S, ang, span, bend, far, name, mist_on=True):
    """Broad vulture wing seen from the side.  The leading edge runs shoulder -> wrist -> hand
    along ``ang`` (projected by ``span``): pale coverts in front, a dark band of flight
    feathers behind, five separated 'finger' primaries splayed from the square hand, and a
    trailing edge fraying into mist."""
    W = px.polar(S, ang, 9.5 * span)
    T = px.polar(W, ang + bend, 7.5 * span)
    chord = (-12.0, 3.0)
    tr_root = (S[0] + chord[0] * 0.65, S[1] + chord[1] * 0.65 + 1.5)
    tr_w = (W[0] + chord[0], W[1] + chord[1])
    tr_t = (T[0] + chord[0] * 0.85, T[1] + chord[1] * 0.85)
    shade = "dark" if far else "full"
    # fingered primaries fanning out of the square hand, with gaps between them
    fa = (ang + bend) % 360
    toward_back = 1 if fa < 180 else -1  # fan from the leading finger back toward the chord
    for k in range(5):
        base = px.lerp_pt(T, tr_t, 0.06 + 0.22 * k)
        a = fa + toward_back * (k * 15 - 18)
        ln = (7.5, 8.5, 8.0, 7.0, 5.5)[k] * max(0.6, span)
        tip = px.polar(base, a, ln)
        cv.limb([px.polar(base, a + 180, 1.0), px.polar(base, a, ln * 0.6), tip], [0.9, 0.8, 0.45], FLIGHT,
                shade="dark", name=name)
    poly = [(S[0] + 2.5, S[1] + 1.5), S, W, T, tr_t, tr_w, tr_root]
    cv.polygon(poly, BODY if far else FEATHER, shade=shade, name=name, sep=False if far else "deep")
    # dark flight feathers along the trailing half
    cv.polygon([px.lerp_pt(S, tr_root, 0.45), px.lerp_pt(W, tr_w, 0.45), px.lerp_pt(T, tr_t, 0.3), tr_t, tr_w,
                tr_root], FLIGHT, shade="two" if not far else "dark", decal=True, clip=name, name=name)
    # frayed trailing edge dissolving into mist
    if not far and mist_on:
        for j in range(6):
            u = j / 5.0
            q = px.lerp_pt(tr_root, tr_w, u * 2) if u < 0.5 else px.lerp_pt(tr_w, tr_t, (u - 0.5) * 2)
            cv.polygon([(q[0] + 1.3, q[1] - 0.8), (q[0] - 1.3, q[1] - 0.8), (q[0] - 2.4, q[1] + 2.2)], MIST,
                       shade="soft", name=name)
    return T, tr_w


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    O = (cv.gx + p.bx, cv.gy + p.by)
    ang, span, bend = p.wing
    with cv.xform(px.rotate(p.tilt, O), px.scale(1.3, 1.3, O)):
        S_far = (O[0] - 1.5, O[1] - 3.5)
        # far wing: a lagging, shorter copy set back behind the body
        _wing(cv, S_far, ang + (26 if ang < 180 else -26), span * 0.8, bend, True, "farwing")
        # tail fan
        cv.polygon([(O[0] - 6.0, O[1] - 1.5), (O[0] - 16.0, O[1] - 1.0), (O[0] - 17.0, O[1] + 1.5),
                    (O[0] - 15.5, O[1] + 3.5), (O[0] - 6.0, O[1] + 3.0)], FLIGHT, shade="nolight", name="tail",
                   sep="deep")
        for k in range(2):
            y = O[1] + 0.3 + k * 1.6
            cv.line((math.floor(O[0] - 15), math.floor(y)), (math.floor(O[0] - 9), math.floor(y)), FLIGHT.deep,
                    band=None, decal=True, clip="tail", name="tail")
        # legs + talons: tucked under the tail, thrust forward to strike
        L = p.legs
        hip = (O[0] - 1.0, O[1] + 3.5)
        foot = (O[0] - 6.0 + 13.0 * L, O[1] + 6.0 + 5.0 * L)
        knee = (hip[0] + 1.0 + 1.5 * L, hip[1] + 3.0)
        cv.limb([hip, knee, foot], [2.0, 1.4, 1.2], LEG, shade="two", name="leg")
        spread = 0.3 + 0.7 * L
        for a in (-20 - 35 * spread, -20, -20 + 35 * spread, 200):
            t0 = px.polar(foot, a, 1.5)
            t1 = px.polar(t0, a - 50, 1.6)
            cv.limb([foot, t0, t1], [0.8, 0.7, 0.4], LEG if a != 200 else LEG.step(1), shade="two", name="leg")
            cv.pixel(math.floor(t1[0]), math.floor(t1[1]), TALON, name="talon")
        talon_at = cv.tp((foot[0] + 2.0, foot[1] + 1.0))
        # body: plump, with the white ruff at the neck
        cv.ellipse(O[0], O[1], 10.0, 6.0, BODY, angle=6, name="body", sep="deep")
        cv.ellipse(O[0] - 1.5, O[1] + 3.0, 8.0, 2.6, FLIGHT, shade="two", decal=True, clip="body", name="body")
        # neck + bald head
        with cv.xform(px.rotate(p.head, (O[0] + 7.0, O[1] - 2.0))):
            N = (O[0] + 7.5, O[1] - 1.5)
            Hc = (O[0] + 12.5, O[1] - 3.5)
            # fluffy white ruff collar
            ruff = cv.union(*[cv.geom_ellipse(N[0] + dx, N[1] + dy, 2.9, 2.5) for dx, dy in
                              ((-2.0, -1.8), (0.3, -2.8), (2.0, -0.8), (0.8, 1.6), (-1.6, 1.4), (-3.0, 0.0))])
            cv.draw_geom(ruff, FEATHER, shade="soft", name="ruff", sep="deep")
            cv.limb([(N[0] + 1.5, N[1] - 0.5), (N[0] + 3.5, N[1] - 1.8), Hc], [1.8, 1.5, 1.6], SKIN, shade="two",
                    name="neck", sep="deep")
            cv.ellipse(Hc[0], Hc[1], 3.2, 2.7, SKIN, name="head", sep="deep")
            # strongly hooked beak: pale horn, dark hooked tip; the lower mandible opens
            with cv.xform(px.rotate(-25 * p.jaw, (Hc[0] + 2.0, Hc[1] + 1.0))):
                cv.polygon([(Hc[0] + 1.8, Hc[1] + 0.8), (Hc[0] + 4.8, Hc[1] + 1.0), (Hc[0] + 4.2, Hc[1] + 1.9),
                            (Hc[0] + 2.0, Hc[1] + 2.0)], BEAK, shade="two", name="beak", sep="deep")
            cv.polygon([(Hc[0] + 1.6, Hc[1] - 1.2), (Hc[0] + 4.2, Hc[1] - 1.0), (Hc[0] + 5.8, Hc[1] + 0.2),
                        (Hc[0] + 5.8, Hc[1] + 2.4), (Hc[0] + 4.9, Hc[1] + 1.2), (Hc[0] + 1.8, Hc[1] + 0.9)], BEAK,
                       name="beak", sep="deep")
            cv.polygon([(Hc[0] + 4.4, Hc[1] - 0.8), (Hc[0] + 6.2, Hc[1] + 0.2), (Hc[0] + 6.2, Hc[1] + 2.8),
                        (Hc[0] + 4.6, Hc[1] + 1.2)], FLIGHT.step(1), shade="two", decal=True, clip="beak", name="beak")
            cv.pixel(math.floor(Hc[0] + 2.5), math.floor(Hc[1] - 1), BEAK.deep, name="nostril")
            eye_at = cv.tp((Hc[0] + 0.5, Hc[1] - 1.0))
        # near wing in front
        S = (O[0] + 1.5, O[1] - 2.5)
        T, trw = _wing(cv, S, ang, span, bend, False, "wing")
        trail = cv.tp(trw)
    # eye stamped at 1:1 (outside the body scale) so it stays crisp
    ex, ey = math.floor(eye_at[0]), math.floor(eye_at[1])
    if p.eye in ("open", "angry"):
        cv.stamp(["gi", "ik"], ex, ey, {"g": px.GLINT, "i": IRIS, "k": px.INK}, name="eye")
        brow = [(ex - 1, ey - 1), (ex, ey - 1), (ex + 1, ey - 1)]
        if p.eye == "angry":
            brow = [(ex - 1, ey - 2), (ex, ey - 1), (ex + 1, ey - 1), (ex + 2, ey)]
        cv.pixels(brow, SKIN.deep, name="brow")
    elif p.eye == "squeeze":
        cv.stamp(["k.", ".k", "k."], ex, ey - 1, {"k": px.INK}, name="eye")
    else:
        cv.stamp(["k.k", ".k.", "k.k"], ex - 1, ey - 1, {"k": px.INK}, name="eye")
    # mist: wisps shed from the frayed wing edge
    if p.mist > 0:
        fx = cv.layer(above=False, outline=True)
        for k in range(int(2 + p.mist)):
            t = (frame * 0.37 + k * 0.29) % 1.0
            cx = trail[0] - 3.0 - k * 3.5 - t * 3.0
            cy = trail[1] + 1.0 + math.sin(k * 2.1 + frame) * 2.0
            fx.circle(cx, cy, 1.6 - 0.4 * (k % 2), MIST, shade="soft", name="mist")
    if p.streak:
        back = cv.layer(above=False, outline=False)
        for k in range(3):
            q0 = (O[0] - 8 - k * 3, O[1] - 12 - k * 2)
            q1 = (q0[0] - 7, q0[1] - 7)
            back.line((math.floor(q0[0]), math.floor(q0[1])), (math.floor(q1[0]), math.floor(q1[1])), px.MIST_BLUE,
                      name="streak")
    if p.hit:
        top = cv.layer(above=True, outline=False)
        px.impact(top, talon_at[0] + 1, talon_at[1], size=4)
