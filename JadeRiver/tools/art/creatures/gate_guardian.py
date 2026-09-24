"""Gate guardian - final boss of the valley: a towering jade-and-bronze gate guardian with a
stern bronze mask, glowing gold eyes and two floating jade bi rings orbiting it (Earth).

View: side, facing right.  ~114 art px tall to the tip of the crown on a 128 px art canvas
(cell 256).  The anchor is lowered to [128, 244] (ground on art row 122) so the full
height fits inside the cell with the 2 px margin.
Rig: pelvis P, torso up to the shoulders S (``lean``), two-bone legs (``px.ik2``) under an
armoured skirt, two-bone arms with bronze gauntlets.  The rings orbit on a tilted ellipse
round the body: the one on the far side is drawn behind the guardian, the near one in
front.
Parts, back to front: far ring, far leg, far arm, torso (jade cuirass, bronze chest plate,
belt), armoured skirt panels, near leg, head (bronze mask with heavy brows and a stern
mouth, gold eyes, jade crown with swept eave horns), layered bronze pauldron, near arm,
near ring.  Cracks spread across the jade and bronze in the death.
Idle: the rings orbit slowly; walk: heavy steps; windup: the rings spin up and rise
(held); attack: a ring sweep (hit on frame 2); hurt: the rings wobble; death: the rings
drop and the guardian kneels, cracking.
"""
import math

import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "gate_guardian",
    "cell": 256,
    "anchor": [128, 244],
    "flying": False,
    "hit_frame": 2,
}

# ---- palette: imperial jade, aged bronze, gold glow ----------------------------------------------
JADE = px.material("gg_jade", "#a4e4c8", "#539f86", "#316e5f", "#1e4743", outline="#0a1917",
                   thresholds=(0.9, 0.55, 0.2))
JADE_D = px.material("gg_jade_far", "#72b39a", "#3f7d6a", "#29574e", "#193833", outline="#0a1917")
BRONZE = px.material("gg_bronze", "#f3c67c", "#b9803f", "#84572f", "#563722", outline="#1a0f08",
                     thresholds=(0.88, 0.52, 0.18))
BRONZE_D = px.material("gg_bronze_far", "#b98e55", "#8a5f34", "#644327", "#442d1c", outline="#1a0f08")
RING = px.material("gg_ring", "#c4f7e0", "#63cdab", "#2f9078", "#1b5a50", outline="#08201c",
                   thresholds=(0.85, 0.5, 0.15))
EYE = px.rgb("#ffe6a1")
EYE_HOT = px.rgb("#fffbe6")
EYE_DEAD = px.rgb("#3a2a1c")
CRACK = px.rgb("#0e211e")
GLINT_GOLD = px.rgb("#e5b84c")

# ---- poses ------------------------------------------------------------------------------------
# bx, by    pelvis offset     lean  torso angle (deg, 90 upright)     head  head tilt
# fn, ff    near / far foot (dx, lift)     hn, hf  hand targets relative to the shoulders
# orbit     ring orbit angle (deg)         ry  ring height above the ground   rr  orbit radius
# spin      spin-blur arcs 0..2            wob  ring wobble (hurt)             swing  rings flung forward 0..1
# drop      rings fallen 0..1 (death)      kneel  0..1     crack  0..3     eye  open|flare|squint|dead
DEFAULTS = dict(bx=0, by=0, lean=90, head=0, fn=(6, 0), ff=(-5, 0), hn=None, hf=None, orbit=0.0, ry=62.0, rr=34.0,
                spin=0, wob=0.0, swing=0.0, drop=0.0, kneel=0.0, crack=0, eye="open", hit=False, fade=1.0,
                breathe=0.0)

POSE = px.poses(DEFAULTS, {
    "idle": [  # the rings drift round (two identical rings: half a turn loops)
        dict(orbit=0.0),
        dict(orbit=45.0, breathe=0.5),
        dict(orbit=90.0, breathe=0.8, eye="flare"),
        dict(orbit=135.0, breathe=0.3),
    ],
    "walk": [  # heavy, ground-shaking steps
        dict(orbit=0.0, fn=(10, 0), ff=(-8, 0), by=0),
        dict(orbit=30.0, fn=(7, 0), ff=(-3, 5), by=-2),
        dict(orbit=60.0, fn=(3, 0), ff=(3, 5), by=-2),
        dict(orbit=90.0, fn=(-8, 0), ff=(10, 0), by=0),
        dict(orbit=120.0, fn=(-3, 5), ff=(7, 0), by=-2),
        dict(orbit=150.0, fn=(3, 5), ff=(3, 0), by=-2),
    ],
    "windup": [  # the rings spin up and rise to the crown; the near hand lifts to command them
        dict(orbit=40.0, ry=78.0, rr=30.0, spin=1, hn=(10, 2), eye="flare", lean=92),
        dict(orbit=100.0, ry=94.0, rr=28.0, spin=2, hn=(8, -14), eye="flare", lean=95, head=4),
        dict(orbit=170.0, ry=100.0, rr=26.0, spin=2, hn=(6, -18), eye="flare", lean=96, head=5, by=1),
    ],
    "attack": [  # ring sweep: both rings arc out and down in front; they strike on frame 2
        dict(orbit=200.0, ry=96.0, rr=26.0, swing=0.3, spin=2, hn=(18, -12), eye="flare", lean=90),
        dict(orbit=230.0, ry=70.0, rr=30.0, swing=0.75, spin=2, hn=(24, 4), eye="flare", lean=84, head=-4,
             fn=(8, 0)),
        dict(orbit=250.0, ry=40.0, rr=32.0, swing=1.0, spin=1, hn=(22, 14), eye="flare", lean=80, head=-6,
             fn=(9, 0), hit=True),
        dict(orbit=280.0, ry=56.0, rr=34.0, swing=0.4, hn=(14, 18), lean=86, head=-2, fn=(7, 0)),
    ],
    "hurt": [  # the rings wobble off their orbit
        dict(orbit=20.0, wob=1.0, bx=-3, lean=96, head=8, eye="squint", crack=1),
        dict(orbit=35.0, wob=0.5, bx=-2, lean=93, head=4, eye="squint", crack=1),
    ],
    "death": [  # the rings drop and the guardian sinks to one knee, cracking apart
        dict(orbit=20.0, wob=1.0, bx=-3, lean=96, head=10, eye="squint", crack=2),
        dict(orbit=30.0, drop=0.45, lean=88, head=-8, eye="squint", crack=2, kneel=0.35, fn=(12, 0), ff=(-8, 0)),
        dict(orbit=30.0, drop=1.0, lean=80, head=-16, eye="dead", crack=3, kneel=1.0, fn=(12, 0), ff=(-10, 0),
             hn=(12, 30), hf=(16, 28)),
        dict(orbit=30.0, drop=1.0, lean=76, head=-22, eye="dead", crack=3, kneel=1.0, fn=(12, 0), ff=(-10, 0),
             hn=(12, 32), hf=(16, 30), by=1),
        dict(orbit=30.0, drop=1.0, lean=76, head=-24, eye="dead", crack=3, kneel=1.0, fn=(12, 0), ff=(-10, 0),
             hn=(12, 32), hf=(16, 30), by=1),
    ],
})

L_THIGH, L_SHIN = 21.0, 21.0
L_UPPER, L_FORE = 17.0, 17.0
TORSO = 32.0


# ---- parts ------------------------------------------------------------------------------------
def _ring(cv, c, scale, tilt, name, far=False, flat=1.0):
    """A jade bi disc: a thick ring with carved dots, seen at ``tilt`` (1 face-on .. 0.3 edge-on);
    ``flat`` < 1 squashes it vertically (a ring lying on the ground)."""
    R, r = 9.5 * scale, 3.6 * scale
    mat = RING
    outer = cv.geom_ellipse(c[0], c[1], R * tilt, R * flat, angle=0)
    hole = cv.mask_ellipse(c[0], c[1], r * tilt, r * flat)
    cv.draw_geom(outer, mat, shade="dark" if far else "full", minus=hole, name=name, sep=False if far else "deep")
    if not far:
        for k in range(6):  # carved grain dots
            q = (c[0] + math.cos(math.radians(k * 60 + 15)) * (R + r) / 2 * tilt,
                 c[1] - math.sin(math.radians(k * 60 + 15)) * (R + r) / 2 * flat)
            cv.pixel(math.floor(q[0]), math.floor(q[1]), RING.shadow, decal=True, name=name)


def _leg(cv, hip, foot, far, kneel_knee=None, shin_back=False):
    mat = JADE_D if far else JADE
    shade = "dark" if far else "two"
    ankle = (foot[0] - 1.0, foot[1] - 5.0) if foot is not None else None
    if kneel_knee is not None:
        knee = kneel_knee
    else:
        knee = px.ik2(hip, ankle, L_THIGH, L_SHIN, bend=1)
    cv.limb([hip, knee], [9.0, 7.6], mat, shade=shade, name="leg")
    if shin_back:  # kneeling: the shin lies back along the ground, sole up
        cv.limb([knee, (knee[0] - 18.0, knee[1] + 1.0)], [7.0, 5.8], mat, shade=shade, name="leg")
        cv.circle(knee[0] + 1.0, knee[1] - 1.0, 5.0, BRONZE_D if far else BRONZE, shade="dark" if far else "two",
                  name="knee")
        return knee
    cv.limb([knee, ankle], [7.4, 5.8], mat, shade=shade, name="leg", sep=False if far else "deep")
    cv.circle(knee[0] + 1.5, knee[1], 5.2, BRONZE_D if far else BRONZE, shade="dark" if far else "two", name="knee")
    # heavy boot with an upturned bronze toe
    cv.polygon([(foot[0] - 8.0, foot[1] - 8.0), (foot[0] + 3.5, foot[1] - 8.0), (foot[0] + 10.5, foot[1] - 1.5),
                (foot[0] + 11.5, foot[1] + 0.9), (foot[0] - 8.0, foot[1] + 0.9)], mat, shade=shade, name="boot",
               sep=False if far else "deep")
    cv.limb([(foot[0] + 6.0, foot[1] - 1.0), (foot[0] + 11.0, foot[1] - 3.5)], 1.6, BRONZE_D if far else BRONZE,
            shade="two", name="boot")
    return knee


def _arm(cv, shoulder, hand, far):
    mat = JADE_D if far else JADE
    shade = "dark" if far else "soft"
    d = math.hypot(hand[0] - shoulder[0], hand[1] - shoulder[1])
    if d < L_UPPER + L_FORE - 0.3:
        elbow = px.ik2(shoulder, hand, L_UPPER, L_FORE, bend=-1)
    else:
        elbow = px.lerp_pt(shoulder, hand, 0.5)
    cv.limb([shoulder, elbow, hand], [7.6, 6.6, 5.8], mat, shade=shade, name="arm_far" if far else "arm",
            sep=False if far else "deep")
    br = BRONZE_D if far else BRONZE
    cv.limb([px.lerp_pt(elbow, hand, 0.25), px.lerp_pt(elbow, hand, 0.85)], [6.9, 6.3], br,
            shade="dark" if far else "two", decal=True, clip="arm_far" if far else "arm")
    cv.circle(hand[0], hand[1], 6.2, br, shade="dark" if far else "full", name="fist", sep=False if far else "deep")
    return elbow


def _head(cv, H, p):
    """Stern bronze mask under a tall jade crown with swept eave horns."""
    # crown: a tall jade block with bronze bands, eave horns sweeping up at front and back
    crown = [(H[0] - 9.0, H[1] - 6.0), (H[0] - 8.0, H[1] - 19.0), (H[0] + 7.0, H[1] - 20.0), (H[0] + 9.0, H[1] - 6.0)]
    cv.polygon(crown, JADE, name="crown", sep="deep")
    cv.limb([(H[0] - 7.5, H[1] - 8.0), (H[0] + 7.5, H[1] - 8.0)], 1.4, BRONZE, shade="two", decal=True, clip="crown",
            name="crown")
    cv.limb([(H[0] - 7.0, H[1] - 18.0), (H[0] + 6.0, H[1] - 19.0)], 1.2, BRONZE, shade="two", decal=True,
            clip="crown", name="crown")
    for sgn in (-1, 1):  # eave horns
        base = (H[0] + sgn * 6.5, H[1] - 19.5)
        cv.limb([base, (base[0] + sgn * 5.0, base[1] - 1.5), (base[0] + sgn * 7.5, base[1] - 5.5)], [2.0, 1.6, 0.8],
                BRONZE, shade="two", name="crown", sep="deep")
    cv.circle(H[0] - 0.5, H[1] - 23.0, 2.4, BRONZE, name="crown", sep="deep")  # finial
    cv.pixel(math.floor(H[0] - 1.0), math.floor(H[1] - 24.0), GLINT_GOLD, name="crown")
    # helmet sides + mask
    cv.ellipse(H[0] - 1.0, H[1], 9.8, 9.0, JADE, name="helm", sep="deep")
    mask = [(H[0] + 0.5, H[1] - 6.5), (H[0] + 9.5, H[1] - 5.5), (H[0] + 11.0, H[1] + 1.0), (H[0] + 9.4, H[1] + 8.5),
            (H[0] + 3.0, H[1] + 10.0), (H[0] + 0.0, H[1] + 3.0)]
    cv.polygon(mask, BRONZE, name="mask", sep="deep")
    # heavy scowling brow ridge, stern down-turned mouth and moustache
    cv.limb([(H[0] + 1.5, H[1] - 4.6), (H[0] + 6.0, H[1] - 3.0), (H[0] + 10.6, H[1] - 1.4)], [1.7, 1.5, 1.1],
            BRONZE, shade="nolight", name="brow", sep="deep")
    cv.line((round(H[0] + 4), round(H[1] + 6)), (round(H[0] + 9), round(H[1] + 5)), BRONZE.deep, name="mask")
    cv.pixels([(round(H[0] + 4), round(H[1] + 7)), (round(H[0] + 10), round(H[1] + 6))], BRONZE.deep, name="mask")
    cv.limb([(H[0] + 5.0, H[1] + 3.2), (H[0] + 10.4, H[1] + 2.4)], 1.0, BRONZE.step(1), shade="two", decal=True,
            clip="mask", name="mask")
    cv.pixel(round(H[0] + 10), round(H[1] + 1), BRONZE.deep, name="mask")  # nostril
    ex, ey = round(H[0] + 5), round(H[1] - 1)
    if p.eye == "dead":
        cv.pixels([(ex, ey), (ex + 1, ey), (ex + 2, ey)], EYE_DEAD, name="eye")
    elif p.eye == "squint":
        cv.pixels([(ex, ey), (ex + 1, ey + 1), (ex + 2, ey)], EYE, name="eye")
    else:
        cv.pixels([(ex, ey), (ex + 1, ey), (ex + 2, ey), (ex + 1, ey + 1)], EYE_HOT if p.eye == "flare" else EYE,
                  name="eye")
    if p.crack >= 2:
        for a, b in (((1.5, -5.0), (4.0, 0.0)), ((4.0, 0.0), (2.5, 5.0))):
            cv.line((round(H[0] + a[0]), round(H[1] + a[1])), (round(H[0] + b[0]), round(H[1] + b[1])), CRACK,
                    decal=True, name="mask")


def _ring_positions(p, cv, O):
    """[(pos, depth, scale, tilt), ...] for the two rings."""
    out = []
    for k in range(2):
        a = math.radians(p.orbit + 180 * k)
        x = O[0] + math.cos(a) * p.rr
        y = O[1] + math.sin(a) * 5.0
        depth = math.sin(a)  # > 0: in front
        if p.wob:
            x += math.sin(k * 2.0 + 1.0) * 3.0 * p.wob
            y += math.cos(k * 2.3) * 5.0 * p.wob
        if p.swing:  # flung forward in an arc
            x = px.lerp(x, O[0] + 34 + 8 * k, p.swing)
            y = px.lerp(y, O[1] - 6 + 14 * k * p.swing, p.swing)
            depth = 1.0 if k == 0 else 0.5
        tilt = 0.45 + 0.55 * abs(math.cos(a)) if not p.swing else 0.75
        out.append(((x, y), depth, 0.92 + 0.1 * depth, tilt, k))
    if p.drop:  # fallen: rolling to rest on the ground, lying flat-ish
        d = p.drop
        res = []
        for (pos, depth, sc, tilt, k) in out:
            rest = (O[0] + (22 if k == 0 else -24), cv.ground - 9.5 * 0.34 + 0.5)
            q = (px.lerp(pos[0], rest[0], d), px.lerp(pos[1], rest[1], d * d))
            res.append((q, 1.0 if k == 0 else -1.0, 1.0, px.lerp(tilt, 1.0, d), k, d))
        return res
    return [o + (0.0,) for o in out]


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    ground = cv.ground
    kn = p.kneel
    P = (cv.gx - 6 + p.bx, ground - 42.0 + p.by + kn * 20.0)
    S = px.polar(P, p.lean, TORSO)
    O = (P[0] + 2.0, ground - p.ry)
    rings = _ring_positions(p, cv, O)

    def foot(i):
        f = p.fn if i == 0 else p.ff
        return (P[0] + f[0], ground - f[1])

    shoulders = [px.polar(px.polar(S, p.lean + 180, 2.0), p.lean + 90, 1.0), px.polar(S, p.lean - 90, 6.0)]
    rest_hand = [(S[0] + 4.0, S[1] + 31.0 - kn * 4), (S[0] + 10.0, S[1] + 29.0 - kn * 4)]

    def hand(i):
        h = p.hn if i == 0 else p.hf
        return rest_hand[i] if h is None else (S[0] + h[0], S[1] + h[1])

    spin = cv.layer(above=False, outline=False)
    if p.spin:  # spin blur arcs round the orbit
        for k in range(p.spin + 1):
            hc.arc_line(spin, (O[0], O[1]), p.rr + 2 + k * 3, 200 + k * 25, 340 + k * 25, hc.WIND if k == 0 else
                        px.rgb("#8fe6c8"), name="spin")
    # rings behind the body
    for (pos, depth, sc, tilt, k, d) in rings:
        if depth <= 0:
            _ring(cv, pos, sc, tilt, "ring_far", far=True, flat=1.0 - 0.66 * d * d)
    # far limbs
    if kn >= 1.0:  # kneeling: the far knee rests on the ground, its shin lying back
        _leg(cv, (P[0] + 2.0, P[1] + 2.0), None, True, kneel_knee=(P[0] - 2.0, ground - 7.6), shin_back=True)
    else:
        _leg(cv, (P[0] + 2.0, P[1] + 2.0), foot(1), True)
    _arm(cv, shoulders[1], hand(1), True)
    # torso: jade cuirass, bronze chest plate with a gold boss, belt
    up = p.lean
    w = lambda q, a, r: px.polar(q, a, r)
    waist = w(P, up, 4.0)
    chest = [w(waist, up - 90, 13.0), w(S, up - 90, 18.0), w(w(S, up, 5.0), up - 50, 12.0),
             w(w(S, up, 5.2), up + 50, 12.0), w(S, up + 90, 16.5), w(waist, up + 90, 12.5)]
    cv.polygon(chest, JADE, name="body")
    plate = [w(w(waist, up, 8.0), up - 90, 12.5), w(w(S, up, -2.0), up - 90, 16.0), w(w(S, up, 2.0), up - 60, 8.0),
             w(w(S, up, 1.0), up + 150, 4.0), w(w(waist, up, 9.0), up + 90, 2.0)]
    cv.polygon(plate, BRONZE, name="plate", sep="deep")
    for k in range(3):  # scale-armour rows on the bronze plate
        a = w(w(waist, up, 12.0 + k * 6.0), up - 90, 14.0)
        b = w(w(waist, up, 12.0 + k * 6.0), up + 90, 1.0)
        cv.line((round(a[0]), round(a[1])), (round(b[0]), round(b[1])), BRONZE.step(1), band=None, decal=True,
                clip="plate", name="plate")
    boss = w(px.lerp_pt(S, waist, 0.45), up - 90, 9.0)
    cv.circle(boss[0], boss[1], 3.6, BRONZE, name="plate", sep="deep")
    cv.circle(boss[0], boss[1], 1.6, EYE if p.eye != "dead" else BRONZE.deep, shade="flat", name="plate")
    cv.limb([w(waist, up + 90, 13.0), w(waist, up - 90, 13.5)], 3.0, BRONZE, shade="two", name="belt", sep="deep")
    # armoured skirt: three long flaring panels hanging from the belt over the thighs
    for k, off in enumerate((-11.0, -2.0, 7.0)):
        q = w(waist, up - 90, off)
        ln = 28.0 - kn * 10.0
        panel = [w(q, up + 90, 5.0), w(q, up - 90, 5.0), w(w(q, up + 180, ln), up - 90, 6.4 + 1.5 * k * kn),
                 w(w(q, up + 180, ln + 1.0), up + 90, 5.2)]
        cv.polygon(panel, JADE_D if k == 0 else JADE, shade="two", name="skirt", sep="deep")
        edge = [w(w(q, up + 180, ln - 2.0), up + 90, 5.0), w(w(q, up + 180, ln - 2.0), up - 90, 6.0)]
        cv.limb(edge, 1.2, BRONZE, shade="two", decal=True, clip="skirt", name="skirt")
    # near leg (kneeling: shin forward, foot planted in front)
    near_knee = None
    if kn >= 1.0:  # the near knee is raised, its foot planted in front
        near_knee = (P[0] + 17.0, P[1] + 2.0)
    _leg(cv, (P[0] - 1.0, P[1] + 3.0), foot(0), False, kneel_knee=near_knee)
    # cracks in the jade and bronze
    if p.crack >= 1:
        c0 = w(px.lerp_pt(S, waist, 0.25), up - 90, 12.0)
        pts = [c0, w(c0, up - 150, 5.0), w(w(c0, up - 150, 5.0), up - 110, 6.0), w(w(c0, up - 150, 9.0), up + 170, 6.0)]
        for a, b in zip(pts, pts[1:]):
            cv.line((round(a[0]), round(a[1])), (round(b[0]), round(b[1])), CRACK, decal=True, name="body")
    if p.crack >= 3:
        c1 = w(waist, up + 90, 6.0)
        pts = [c1, w(c1, up + 60, 7.0), w(w(c1, up + 60, 7.0), up + 20, 7.0)]
        for a, b in zip(pts, pts[1:]):
            cv.line((round(a[0]), round(a[1])), (round(b[0]), round(b[1])), CRACK, decal=True, name="body")
    # head
    H = w(w(S, up, 14.5), up - 90, 4.0)
    neck = [w(S, up, 3.0), w(H, up + 180, 6.0)]
    cv.limb(neck, 6.0, JADE_D, shade="two", name="neck")
    with cv.xform(px.rotate(p.head, (H[0], H[1] + 6))):
        _head(cv, H, p)
    # layered bronze pauldron (three lames) with the near arm under it
    _arm(cv, shoulders[0], hand(0), False)
    pa = w(w(S, up + 180, 2.0), up + 90, 1.0)
    for k in range(3):
        c = w(pa, up + 180, k * 3.6)
        cv.ellipse(c[0] + k * 0.6, c[1], 10.0 - k * 1.0, 4.6, BRONZE, angle=up - 90 - k * 6, name="pauldron",
                   sep="deep")
    cv.circle(pa[0] + 1.0, pa[1] - 1.2, 1.8, EYE if p.eye != "dead" else BRONZE.deep, shade="flat", name="pauldron")
    # rings in front of the body
    hit_at = None
    for (pos, depth, sc, tilt, k, d) in rings:
        if depth > 0:
            _ring(cv, pos, sc, tilt, "ring", flat=1.0 - 0.66 * d * d)
            if k == 0:
                hit_at = pos
    if p.swing:  # sweep trail behind the flung rings
        tr = cv.layer(above=False, outline=False)
        c = (O[0] + 6, O[1] - 10)
        hc.arc_line(tr, c, 36.0, 150, 150 - 150 * p.swing, px.rgb("#8fe6c8"), name="trail")
        hc.arc_line(tr, c, 32.0, 145, 145 - 140 * p.swing, hc.WIND, name="trail")
    if p.hit and hit_at is not None:
        top = cv.layer(above=True, outline=False)
        px.impact(top, hit_at[0] + 8, hit_at[1], size=5, color=px.rgb("#b8f5dc"))
    if p.drop >= 1.0:  # dust where the rings landed
        dd = cv.layer(above=True, outline=True)
        for (pos, depth, sc, tilt, k, d) in rings:
            px.dust(dd, pos[0] + 4, cv.gy - 1, 0.6 if frame == 2 else 0.9, size=1.0, direction=1 if k == 0 else -1)
