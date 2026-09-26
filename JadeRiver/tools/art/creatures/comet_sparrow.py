"""Comet sparrow - a small fierce sparrow wreathed in comet fire (Fire; also a tameable pet).

View: side, flying right (cell 128, anchor at the body centre).  ~26 art px from the tail
feathers to the beak, ~13 px body height (wings add ~10 when raised), plus a comet tail of
flame streaming ~30 px behind it.  Round, big-headed and bright-eyed so it reads as a pet.
Parts, back to front: comet tail (a tapering ribbon of flame, gold-white at the root through
orange and magenta to violet at the tip, with flickering tongues and star sparks), far wing
(dark), forked russet tail with gold tips, tucked feet, body + head as one russet form with a
white-hot breast, gold brow stripe, pale cheek, little flame crest, gold beak, big dark eye,
near wing (russet coverts, dark flight feathers, gold tips) over the body.
Idle: hovering flap, the comet tail flickers.  Walk: fast level flapping, the tail streams
straight back.  Windup: pulls up and back, wings swept back, tips nose-down into a dive pose
while the comet tail flares wide with sparks (held).  Attack: a streaking dive with speed
lines; a burning slash crescent on the hit frame (1), then it pulls up through the embers.
Hurt: knocked back, feathers and sparks fly.  Death: the fire gutters to smoke, it tumbles
and falls, breaking into embers as it fades.
"""
import math

import numpy as np

import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "comet_sparrow",
    "cell": 128,
    "anchor": [74, 64],
    "flying": True,
    "hit_frame": 1,
}

# ---- palette: russet + gold feathers, white-hot breast, flame ramp orange -> magenta -> violet
FEATHER = px.material("cs_feather", "#e0935a", "#a8532e", "#763627", "#4b2027", outline="#1d0a0e",
                      thresholds=(0.88, 0.52, 0.18))
FLIGHT = px.material("cs_flight", "#9a5236", "#71352a", "#522427", "#381a24", outline="#1a080c")
GOLD = px.material("cs_gold", "#fff2ae", "#f4c24e", "#cf8a34", "#8e4f2a", outline="#220e08")
BREAST = px.material("cs_breast", "#ffffff", "#fff3d2", "#ffd690", "#f29a4c", outline="#2a0e0a")
FL_OR = px.material("cs_flame_or", "#fff0b0", "#ffbd4f", "#f5832f", "#cf4a2c", outline="#3a0f10")
FL_MG = px.material("cs_flame_mg", "#ffb0cf", "#f2649c", "#c83e88", "#8e2b78", outline="#2c0a26")
FL_VI = px.material("cs_flame_vi", "#cfb0ff", "#9d6ee2", "#6f48ba", "#46307e", outline="#150c2e")
SMOKE = px.material("cs_smoke", "#b8aecb", "#8a7fa3", "#655c80", "#463f5e", outline="#1a1628")
EYE_K = px.rgb("#1a0d14")
CORE = px.rgb("#fffbe6")
SPARK_Y = hc.SPARK_Y
SPARK_W = hc.SPARK_W
SPEED = px.rgb("#ffd79a")

# ---- poses --------------------------------------------------------------------------------
# bx, by   body offset          tilt  pitch (deg, + = nose up)     wn / wf  near / far wing key
# head     head tilt (deg)      eye   open|angry|squeeze|dead       tail  tail-feather spread 0..1
# ca       comet tail direction (deg, 180 = straight back)  cl  comet length   cw  comet width
# cph      flame flicker phase  fire  0 out .. 1 normal .. 2 flared (colour + tongues)
# feet     0 tucked .. 1 thrust forward   crest  flame crest height 0..1
# speed    dive speed lines     slash  burning slash (1 = the cut, 0.5 = fading)   spark  spark burst
# feathers torn feathers flying (hurt)   embers  falling embers (death)   fade  opacity
DEFAULTS = dict(bx=0, by=0, tilt=8, wn="mid", wf="mid", head=0, eye="open", tail=0.5, ca=196, cl=25.0, cw=4.0,
                cph=0.0, fire=1.0, feet=0.0, crest=1.0, speed=False, slash=0.0, spark=0.0, feathers=0.0,
                embers=0.0, fade=1.0, wave=1.0, seed=0)

TAU = 2 * math.pi

POSE = px.poses(DEFAULTS, {
    "idle": [  # hovering flap, 1 px bob against the beat, comet tail flickers
        dict(wn="up", wf="up", by=1, cph=0.0, tail=0.6),
        dict(wn="mid", wf="mid", by=0, cph=TAU * 0.25, tail=0.5),
        dict(wn="down", wf="down", by=-1, cph=TAU * 0.5, tail=0.4, ca=192),
        dict(wn="mid", wf="mid", by=0, cph=TAU * 0.75, tail=0.5, head=-3),
    ],
    "walk": [  # fast level flapping forward, the comet tail streaming straight back
        dict(wn="up_high", wf="up_high", by=1, tilt=0, ca=184, cl=26, cph=0.0, tail=0.3),
        dict(wn="up", wf="up", by=0, tilt=0, ca=184, cl=26, cph=TAU / 6, tail=0.3),
        dict(wn="mid", wf="mid", by=-1, tilt=-1, ca=182, cl=26, cph=TAU * 2 / 6, tail=0.2),
        dict(wn="down", wf="down", by=-1, tilt=-2, ca=180, cl=26, cph=TAU * 3 / 6, tail=0.2),
        dict(wn="down_low", wf="down_low", by=0, tilt=-2, ca=180, cl=26, cph=TAU * 4 / 6, tail=0.3),
        dict(wn=(150, 168, 1, 0.5), wf=(146, 164, 1, 0.5), by=1, tilt=0, ca=182, cl=26, cph=TAU * 5 / 6, tail=0.3),
    ],
    "windup": [  # pulls up and back, sweeps the wings back, noses down - the comet tail flares (held)
        dict(wn=(120, 150, 1, 0.6), wf=(116, 146, 1, 0.6), bx=-1, by=-2, tilt=-4, ca=165, cl=24, cw=4.8,
             cph=0.6, fire=1.5, eye="angry", tail=0.9, crest=1.4, spark=0.3, seed=1),
        dict(wn=(140, 170, 1, 0.3), wf=(136, 166, 1, 0.3), bx=-2, by=-4, tilt=-16, ca=142, cl=24, cw=5.0,
             cph=1.2, fire=2.0, eye="angry", tail=1.0, crest=1.8, spark=0.6, seed=2, head=6),
        dict(wn=(148, 176, 1, 0.2), wf=(144, 172, 1, 0.2), bx=-3, by=-5, tilt=-22, ca=136, cl=25, cw=5.4,
             cph=1.7, fire=2.0, eye="angry", tail=1.0, crest=2.0, spark=0.9, seed=3, head=8),
    ],
    "attack": [  # streaking dive forward-down, the burning slash on frame 1, then it pulls up
        dict(wn="tuck", wf="tuck", bx=-1, by=-2, tilt=-30, ca=150, cl=26, cw=4.8, cph=2.0, fire=2.0, eye="angry",
             tail=0.1, crest=1.6, speed=True, head=4, feet=0.3),
        dict(wn="up", wf="up", bx=3, by=5, tilt=-8, ca=166, cl=22, cw=5.0, cph=2.6, fire=2.0, eye="angry",
             tail=0.9, crest=1.8, slash=1.0, feet=1.0, head=-2),
        dict(wn="mid", wf="mid", bx=3, by=3, tilt=10, ca=192, cl=22, cw=4.2, cph=3.2, fire=1.5, eye="angry",
             tail=0.7, crest=1.3, slash=0.5, feet=0.6),
        dict(wn="down", wf="down", bx=1, by=1, tilt=8, ca=196, cl=24, cph=3.8, tail=0.5, feet=0.2),
    ],
    "hurt": [  # knocked back and up, feathers and sparks fly, the flame flickers small
        dict(wn="up_high", wf="up_high", bx=-4, by=-2, tilt=22, head=14, eye="squeeze", ca=214, cl=18, cw=2.8,
             cph=1.0, fire=0.8, tail=1.0, crest=0.6, feathers=0.35, spark=0.5, seed=4),
        dict(wn="up", wf="up", bx=-2, by=-1, tilt=14, head=8, eye="squeeze", ca=206, cl=22, cph=1.6, fire=0.9,
             tail=0.7, crest=0.8, feathers=0.8, seed=5),
    ],
    "death": [  # the fire gutters to smoke, it tumbles and falls, breaking into embers
        dict(wn="up_high", wf="up_high", bx=-4, by=-2, tilt=22, head=14, eye="squeeze", ca=214, cl=18, cw=2.8,
             cph=1.0, fire=0.8, tail=1.0, crest=0.6, feathers=0.35, spark=0.5, seed=4),
        dict(wn=(118, 150, 1, 0.5), wf=(114, 146, 1, 0.5), bx=-3, by=2, tilt=70, head=-10, eye="dead", ca=250,
             cl=14, cw=2.4, cph=1.8, fire=0.35, tail=0.4, crest=0.2, embers=0.2),
        dict(wn=(140, 172, 1, 0.3), wf=(136, 168, 1, 0.3), bx=-2, by=7, tilt=160, head=-10, eye="dead", ca=300,
             cl=10, cw=2.0, cph=2.4, fire=0.0, tail=0.3, crest=0.0, embers=0.5),
        dict(wn=(150, 176, 1, 0.3), wf=(146, 172, 1, 0.3), bx=-1, by=12, tilt=250, head=-10, eye="dead",
             ca=330, cl=8, cw=1.8, cph=3.0, fire=0.0, tail=0.3, crest=0.0, embers=0.75, fade=0.6),
        dict(wn=(150, 176, 1, 0.3), wf=(146, 172, 1, 0.3), bx=0, by=16, tilt=320, head=-10, eye="dead",
             ca=340, cl=6, cw=1.6, cph=3.4, fire=0.0, tail=0.3, crest=0.0, embers=1.0, fade=0.3),
    ],
})

ARM, HAND, CHORD = 5.4, 5.0, 4.6


# ---- parts ----------------------------------------------------------------------------------------
def _comet(cv, root, p):
    """The comet tail: nested tapering layers of flame streaming from ``root`` (canvas coords)
    like a flame lying on its side - a violet outer sheath, magenta inside it, then orange and
    a white-hot core, each layer shorter than the one around it.  Tongues lick back off both
    edges.  When the fire is out it is a thin wisp of violet smoke."""
    n = 16
    a = math.radians(p.ca)
    dx, dy = math.cos(a), -math.sin(a)
    nx, ny = -dy, dx

    def ribbon(frac, wfrac):
        pts, radii = [], []
        for i in range(n + 1):
            s = i / n
            off = p.wave * 1.8 * (s * frac) ** 1.2 * math.sin(p.cph - s * frac * 5.5)
            L = p.cl * frac * s
            pts.append((root[0] + dx * L + nx * off, root[1] + dy * L + ny * off))
            flick = 1.0 + 0.2 * math.sin(p.cph * 1.7 + s * frac * 9.0)
            radii.append(max(0.5, p.cw * wfrac * (1.0 - s) ** 0.65 * flick))
        return pts, radii

    pts, radii = ribbon(1.0, 1.0)
    if p.fire <= 0.05:  # guttered: a wisp of violet smoke
        cv.limb(pts[: n // 2 + 1], [r * 0.5 for r in radii[: n // 2 + 1]], SMOKE, shade="soft", name="comet")
        return pts
    hot = min(1.0, p.fire)
    k_mg = int(round(n * min(0.62, 0.3 + 0.12 * (p.fire - 1)) * hot))  # orange root runs to here
    k_vi = int(round(n * min(0.82, 0.62 + 0.1 * (p.fire - 1))))  # magenta runs to here, violet beyond

    def mat_at(i):
        return FL_OR if i <= k_mg else (FL_MG if i <= k_vi else FL_VI)

    cv.limb(pts, radii, FL_VI, shade="soft", name="comet")
    # flickering tongues licking back off the edges, coloured like the sheath they leave
    tongues = ((0.14, 1, 5.0), (0.28, -1, 4.6), (0.44, 1, 4.2), (0.6, -1, 3.4), (0.76, 1, 2.6))
    for j, (s, side, ln) in enumerate(tongues):
        i = int(round(s * n))
        r = radii[i]
        base = (pts[i][0] + side * nx * r * 0.5, pts[i][1] + side * ny * r * 0.5)
        lk = ln * (0.55 + 0.45 * abs(math.sin(p.cph * 1.3 + j * 1.9))) * min(1.35, p.fire)
        tip = (base[0] + dx * lk * 0.9 + side * nx * lk * 0.5, base[1] + dy * lk * 0.9 + side * ny * lk * 0.5)
        cv.limb([base, tip], [max(0.8, r * 0.45), 0.5], mat_at(min(n, i + 2)), shade="soft", name="comet")
    # sheath colour by distance along the stream: orange root -> magenta -> violet tip
    along = ((cv.X - root[0]) * dx + (cv.Y - root[1]) * dy) / max(1.0, p.cl)
    perp = ((cv.X - root[0]) * nx + (cv.Y - root[1]) * ny) / max(1.0, p.cw)
    # the hot colours reach furthest along the centre line and flicker at their edge (tongue shapes)
    along = along + 0.16 * np.abs(perp) + 0.05 * np.sin(perp * 2.2 + p.cph * 1.5)
    body = cv.mask_of("comet")
    t_or = min(0.62, 0.3 + 0.12 * (p.fire - 1)) * hot
    t_mg = min(0.82, 0.62 + 0.1 * (p.fire - 1))
    cv.fill(body & (along < t_mg), FL_MG, decal=True, name="comet")
    if t_or > 0.05:
        cv.fill(body & (along < t_or), FL_OR, decal=True, name="comet")
    # nested hot layers inside: an orange tongue through the magenta, a white-gold core at the root
    for mat, frac, wf in ((FL_OR, 0.5 * hot + 0.08 * (p.fire - 1), 0.4),
                          (px.flat(CORE), 0.26 * hot + 0.06 * (p.fire - 1), 0.34)):
        if frac < 0.12:
            continue
        q, r = ribbon(frac, wf)
        cv.limb(q, r, mat, shade="flatlight" if mat is FL_OR else "flat", decal=True, clip="comet", name="comet")
    hc.thin_body(cv, cv.mask_of("comet"))
    return pts


def _wing(cv, S, key, far):
    arm, hand, trail, fan = hc.FLAP[key] if isinstance(key, str) else key
    if far:
        arm, hand = arm - 14 * trail, hand - 12 * trail
    return hc.bird_wing(cv, S, arm, hand, ARM, HAND, CHORD, trail, FEATHER, FLIGHT, tip=GOLD, n_prim=4, far=far,
                        name="wing_far" if far else "wing", prim_len=1.3, fan=fan, prim_r=0.28, n_sec=3,
                        tip_frac=0.35)


def _eye(cv, x, y, state):
    if state == "squeeze":
        hc.eye_stamp(cv, ["kk.", "..k", "kk."], x, y - 1 + 1, {"k": EYE_K})
    elif state == "dead":
        hc.eye_stamp(cv, ["k.k", ".k.", "k.k"], x, y, {"k": EYE_K})
    else:
        hc.eye_stamp(cv, ["gkk", "kkk", ".kk"] if state == "open" else ["gkk", "kkk", "..k"], x, y, {"k": EYE_K})


def _crest(cv, H, p):
    """A little flame crest licking up from the crown."""
    if p.crest <= 0.05:
        return
    base = (H[0] - 1.8, H[1] - 3.4)
    for k, (dx, h, lean) in enumerate(((0.0, 3.6, -0.45), (-2.0, 2.6, -0.6))):
        hh = h * p.crest * (0.85 + 0.15 * math.sin(p.cph * 2 + k * 2))
        b = (base[0] + dx, base[1] + 0.5)
        cv.polygon([(b[0] - 1.3, b[1] + 0.8), (b[0] + lean * hh, b[1] - hh), (b[0] + 1.3, b[1] + 0.8)],
                   FL_OR, shade="soft", name="crest")


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    C = (cv.gx + p.bx, cv.gy + p.by)
    back = cv.layer(above=False, outline=False)
    with cv.xform(px.rotate(p.tilt, C)):
        root = cv.tp((C[0] - 8.5, C[1] + 1.2))
    comet_pts = _comet(cv, root, p)
    with cv.xform(px.rotate(p.tilt, C)):
        _wing(cv, (C[0] + 1.8, C[1] - 3.0), p.wf, True)
        # forked tail: two feather blades with gold tips, fanning with ``tail``
        sp = p.tail
        for k, (up, dn) in enumerate(((-2.6 - sp * 1.8, -0.2), (0.4, 2.8 + sp * 1.4))):
            blade = [(C[0] - 4.0, C[1] - 0.6 + (0 if k == 0 else 1.2)), (C[0] - 13.0, C[1] + up + (0 if k == 0 else 1.0)),
                     (C[0] - 12.2, C[1] + (up + dn) / 2 + 0.6), (C[0] - 4.0, C[1] + 1.4 + (0 if k == 0 else 1.2))]
            cv.polygon(blade, FEATHER if k == 0 else FLIGHT, shade="two", name="tail", sep=True)
            tip = blade[1]
            cv.limb([tip, px.lerp_pt(tip, blade[0], 0.25)], 1.0, GOLD, shade="two", decal=True, clip="tail", name="tail")
        # tucked feet (thrust forward to rake in the attack)
        ft = p.feet
        hip = (C[0] + 1.0, C[1] + 3.2)
        for k in (1, 0):
            foot = (C[0] - 1.0 + ft * 6.0 + k * 1.2, C[1] + 5.4 + ft * 1.0 - k * 0.5)
            cv.limb([hip, foot], [0.9, 0.7], GOLD, shade="dark" if k else "two", name="leg")
        # body + head: one round russet form
        H = (C[0] + 5.6, C[1] - 3.6)
        body_g = cv.geom_ellipse(C[0], C[1], 6.6, 5.2, angle=8)
        with cv.xform(px.rotate(p.head, (C[0] + 4.0, C[1] - 1.5))):
            head_g = cv.geom_ellipse(H[0], H[1], 4.6, 4.3)
        cv.draw_geom(cv.union(body_g, head_g, weights=[1.0, 0.95]), FEATHER, name="body", sep=True)
        for k in range(3):  # dark sparrow streaks down the back
            x0 = C[0] - 3.5 + k * 2.2
            cv.line((math.floor(x0), math.floor(C[1] - 3.6 + k * 0.3)), (math.floor(x0 - 1.5), math.floor(C[1] - 1.8 + k * 0.3)),
                    FEATHER.deep, decal=True, clip="body", name="body")
        # white-hot breast glowing from the belly up to the throat
        cv.ellipse(C[0] + 2.4, C[1] + 1.8, 5.0, 3.6, BREAST, shade="soft", decal=True, clip="body", name="body")
        with cv.xform(px.rotate(p.head, (C[0] + 4.0, C[1] - 1.5))):
            cv.ellipse(H[0] + 2.2, H[1] + 2.8, 2.6, 1.8, BREAST, shade="soft", decal=True, clip="body", name="body")
            # pale cheek under the eye and a gold brow stripe running back over it
            cv.ellipse(H[0] + 0.2, H[1] + 1.4, 2.0, 1.2, BREAST.step(1), shade="flat", decal=True, clip="body",
                       name="body")
            cv.limb([(H[0] - 3.6, H[1] - 1.2), (H[0] - 0.4, H[1] - 2.8), (H[0] + 2.2, H[1] - 2.4)], [0.55, 0.6, 0.5],
                    GOLD, shade="two", decal=True, clip="body", name="body")
            _crest(cv, H, p)
            # stout gold finch beak
            cv.polygon([(H[0] + 3.4, H[1] - 1.0), (H[0] + 7.2, H[1] + 0.4), (H[0] + 3.6, H[1] + 1.8)], GOLD,
                       name="beak", sep="deep")
            cv.line((math.floor(H[0] + 4.0), math.floor(H[1] + 0.5)), (math.floor(H[0] + 6.2), math.floor(H[1] + 0.5)),
                    GOLD.step(2), decal=True, clip="beak", name="beak")
            eye_at = cv.tp((H[0] + 0.2, H[1] - 1.6))
        beak_tip = cv.tp((H[0] + 7.4, H[1] + 0.4))
        near = _wing(cv, (C[0] + 0.4, C[1] - 1.8), p.wn, False)
        claw = cv.tp((C[0] - 1.0 + p.feet * 6.0 + 1.5, C[1] + 6.2 + p.feet * 1.0))
    ex, ey = math.floor(eye_at[0]), math.floor(eye_at[1])
    _eye(cv, ex, ey, p.eye)
    if p.eye == "angry":  # a fierce little brow slanting toward the beak
        cv.pixels([(ex - 1, ey - 1), (ex, ey - 1), (ex + 1, ey), (ex + 2, ey)], EYE_K, name="brow")
    # ---- FX ------------------------------------------------------------------------------------
    fx = cv.layer(above=True, outline=False)
    if p.fire > 0.05 and comet_pts:  # star sparks shed off the comet tail
        for k, s in enumerate((0.5, 0.72, 0.9)):
            q = comet_pts[min(len(comet_pts) - 1, int(s * (len(comet_pts) - 1)))]
            side = 1 if (k + int(p.cph * 2)) % 2 else -1
            x, y = max(3, math.floor(q[0])), math.floor(q[1] + side * (4 - k))
            fx.line((x, y), (x + 1, y), SPARK_Y if k % 2 else SPARK_W, name="spark")
    if p.spark > 0:  # the flare throws sparks off the comet root
        hc.sparks(fx, root[0], root[1] - 2, p.spark, n=5 + int(3 * p.spark), radius=8.0 + 4.0 * p.spark, seed=p.seed,
                  aim=130, spread=200)
    if p.speed:  # speed lines streaming off behind the dive
        a = math.radians(p.tilt)
        dx, dy = -math.cos(a), math.sin(a)
        nx, ny = -dy, dx
        for k, (o, s0, ln) in enumerate(((-7, 10, 9), (6, 9, 8))):
            x0, y0 = C[0] + dx * s0 + nx * o, C[1] + dy * s0 + ny * o
            back.line((math.floor(x0), math.floor(y0)), (math.floor(x0 + dx * ln), math.floor(y0 + dy * ln)), SPEED,
                      name="speed")
    if p.slash > 0:
        sl = cv.layer(above=True, outline=True)
        top = cv.layer(above=True, outline=False)
        c = (beak_tip[0] - 4.0, beak_tip[1] - 1.0)
        if p.slash >= 1:  # the burning slash: a crescent of fire raked down across the target
            _crescent(sl, c, 10.0, 84, -66, 3.4, FL_OR, edge=CORE, back=back)
            hit = px.polar(c, 5, 10.0)
            px.impact(top, min(cv.w - 7, hit[0] + 1), hit[1], size=4, color=SPARK_Y, core=CORE)
        else:  # it breaks into embers
            _crescent(sl, c, 11.0, 20, -70, 2.0, FL_MG)
            hc.ember_specks(top, [(c[0] + 11, c[1] + 4, 2), (c[0] + 8, c[1] + 9, 0), (c[0] + 12, c[1] - 3, 0)])
    if p.feathers > 0:  # torn feathers and sparks flung off
        f = p.feathers
        for k, (dx, dy, ang) in enumerate(((-9, -9, 30), (4, -12, -20), (-13, 2, 60))):
            x, y = C[0] + dx * (0.6 + f), C[1] + dy * (0.6 + f) + f * 3
            q = px.polar((x, y), ang, 2.4)
            fx.limb([(x, y), q], [0.9, 0.5], FEATHER if k % 2 else GOLD, shade="two", name="feather")
        hc.ember_specks(fx, [(C[0] + 8, C[1] - 9 - f * 3, 2), (C[0] - 4, C[1] - 11 - f * 2, 0)])
    if p.embers > 0:  # falling apart into embers
        e = p.embers
        pts = []
        for k in range(3 + int(e * 4)):
            ang = 60 + k * 47
            r = 5 + e * 7 + (k % 3) * 1.5
            q = px.polar(C, ang, r)
            pts.append((q[0], q[1] - e * 3, k % 3))
        hc.ember_specks(fx, pts, colors=(SPARK_Y, FL_OR.shadow))
    if p.fire <= 0.05 and p.embers > 0.4:  # a curl of smoke rising where the fire went out
        hc.wisp(back, C[0] - 2, C[1] - 6, 7.0, p.cph, mat=SMOKE, width=1.1)


def _crescent(fx, c, r, a0, a1, width, mat, edge=None, back=None):
    """A fiery slash crescent: an arc band from a0 to a1 (deg), thickest in the middle."""
    n = 14
    outer, inner = [], []
    for i in range(n + 1):
        t = i / n
        a = a0 + (a1 - a0) * t
        w = width * math.sin(math.pi * t) ** 0.8
        outer.append(px.polar(c, a, r))
        inner.append(px.polar(c, a, r - w))
    fx.polygon(outer + inner[::-1], mat, shade="soft", name="slash")
    if edge is not None:
        hc.arc_line(fx, c, r - 0.8, a0 + (a1 - a0) * 0.2, a0 + (a1 - a0) * 0.75, edge, name="slash")
    if back is not None:  # a trailing magenta echo behind the cut
        hc.arc_line(back, c, r - 3.5, a0 - 10, a1 + 25, FL_MG.base, name="slash")
