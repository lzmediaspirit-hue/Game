"""Star jellyfish - a drifting jellyfish of starlight from the Lantern Star Field (Star).

View: side, facing right (the body is nearly symmetric; it leans and lashes to the right).
Flying (cell 128, anchor at the bell centre).  ~29 art px wide bell, ~16 px tall, trailing
tentacles to ~52 px total height (the player is ~45).
Parts, back to front: glow rings and the lash smear (FX, behind), four long pale star-lit
tentacles and two shorter magenta oral arms (tapered wavy strands), the magenta frilled rim (a
row of scallops hanging under the bell), the translucent indigo-violet bell (one dome form
with a lit halo inside around the star, the strand roots showing faintly through its lower
half, radial canals and a glassy highlight arc), the pale-gold star glowing inside it, and
twinkling star points along the tentacles (FX).
Idle: the bell pulses (contracts taller / relaxes wider), tentacles sway, 1 px bob.
Walk: leans into the drift and pulses forward, tentacles streaming back.
Windup: the bell clenches hard, the inner star flares, a double ring of star-glow opens round
it and the tentacles curl up and forward (held).  Attack: the bell snaps back and the
tentacles lash forward in a stinging arc; the spark burst lands at the tips on frame 1.
Hurt: the bell dents, the star flickers dim.  Death: the bell deflates and sags, the star
gutters out (its last light drifts up), it sinks with limp tentacles and fades.
"""
import math

import numpy as np

import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "star_jellyfish",
    "cell": 128,
    "anchor": [64, 36],
    "flying": True,
    "hit_frame": 1,
}

# ---- palette: indigo-violet bell, magenta frill, pale star-lit tentacles, pale-gold star ------
BELL = px.material("sj_bell", "#b9a6f2", "#7b63d2", "#4f3ea2", "#2f256c", outline="#0e0a26",
                   thresholds=(0.88, 0.5, 0.16))
FRILL = px.material("sj_frill", "#ffc9ef", "#e47cca", "#a94b9f", "#6b2d70", outline="#1d0a22")
TENT = px.material("sj_tentacle", "#f1f4ff", "#c3cbf4", "#8e93d8", "#5f5cab", outline="#130f33")
STAR_W = px.rgb("#fffdf0")
STAR_Y = px.rgb("#ffe6a1")
STAR_O = px.rgb("#f2bf55")
STAR_DIM = px.rgb("#b79a6a")
STAR_OUT = px.rgb("#6c6388")
GLASS = px.rgb("#e9e2ff")
SPARK_V = px.rgb("#d8c8ff")
SMEAR = px.rgb("#a99be6")

# star stamps (w white core, y pale gold, o warm gold edge)
STAR_S = ["..y..", ".yyy.", "yywyy", ".yyy.", ".y.y."]
STAR_M = ["...o...", "...y...", "oyywyyo", ".yywyy.", "..yyy..", ".yy.yy.", ".o...o."]
STAR_L = ["....o....", "....y....", "...yyy...", "oyyywyyyo", ".yyywyyy.", "..yyyyy..", "..yy.yy..",
          ".yy...yy.", ".o.....o."]

# ---- poses --------------------------------------------------------------------------------
# bx, by   offset of the bell centre     tilt  lean (deg, + = top back / left)
# sx, sy   bell width / height pulse     ph  tentacle wave phase    amp  wave amplitude (deg)
# trail    tentacle base angle (deg from straight down, + = streaming back, - = forward)
# curl     extra bend toward the tip (deg, - = curling forward / up)     tlen  length factor
# spread   root spacing of the strands   fan  angle fan (deg per px of root offset)
# star     0 out | 1 dim | 2 normal | 3 flare
# glow     star-glow rings behind (0 = off)     dent  0..1 bell dented (hurt)
# droop    bell rim sagging (death, px)  smear  lash arc behind the strands (attack)
# spark    sting burst life (None = off)  motes  last light drifting up (death)
# twk      twinkle step                  fade  opacity
DEFAULTS = dict(bx=0, by=0, tilt=0, sx=1.0, sy=1.0, ph=0.0, amp=14.0, trail=0.0, curl=0.0, tlen=1.0, star=2,
                glow=0, dent=0.0, droop=0.0, spark=None, twk=0, fade=1.0, spread=1.0, smear=0, motes=0, fan=1.3)

TAU = 2 * math.pi

POSE = px.poses(DEFAULTS, {
    "idle": [  # pulse: relax wide -> clench tall -> release; tentacles sway; 1 px bob
        dict(sx=1.04, sy=0.95, ph=0.0, by=0, twk=0),
        dict(sx=0.93, sy=1.07, ph=TAU * 0.25, by=-1, twk=1, spread=0.9),
        dict(sx=0.97, sy=1.03, ph=TAU * 0.5, by=-1, twk=2),
        dict(sx=1.02, sy=0.97, ph=TAU * 0.75, by=0, twk=3),
    ],
    "walk": [  # leans into the drift: a hard pulse, glide, relax; tentacles stream back
        dict(tilt=-10, sx=1.05, sy=0.94, ph=0.0, trail=12, amp=11, twk=0, bx=2),
        dict(tilt=-12, sx=0.88, sy=1.1, ph=TAU / 6, trail=18, amp=9, twk=1, by=-1, bx=2, spread=0.8),
        dict(tilt=-13, sx=0.9, sy=1.08, ph=TAU * 2 / 6, trail=22, amp=9, twk=2, by=-1, bx=3, spread=0.8),
        dict(tilt=-12, sx=0.96, sy=1.02, ph=TAU * 3 / 6, trail=19, amp=10, twk=3, bx=3),
        dict(tilt=-11, sx=1.02, sy=0.97, ph=TAU * 4 / 6, trail=15, amp=11, twk=4, by=1, bx=3),
        dict(tilt=-10, sx=1.06, sy=0.93, ph=TAU * 5 / 6, trail=12, amp=11, twk=5, by=1, bx=2),
    ],
    "windup": [  # clenches hard, the star flares, tentacles curl up and forward - held
        dict(sx=0.9, sy=1.08, tilt=4, bx=-1, by=1, ph=0.8, amp=7, trail=0, curl=-50, star=3, glow=1, twk=1,
             spread=0.85, tlen=0.95),
        dict(sx=0.82, sy=1.16, tilt=7, bx=-2, by=2, ph=1.0, amp=4, trail=2, curl=-95, star=3, glow=2, twk=2,
             spread=0.75, tlen=0.86),
        dict(sx=0.8, sy=1.18, tilt=8, bx=-2, by=2, ph=1.1, amp=3, trail=2, curl=-115, star=3, glow=3, twk=3,
             spread=0.72, tlen=0.84),
    ],
    "attack": [  # snaps open and lashes the tentacles forward in an arc; the sting lands on frame 1
        dict(sx=1.08, sy=0.92, tilt=10, bx=-4, ph=2.0, amp=4, trail=-34, curl=34, star=3, twk=0, tlen=0.92,
             smear=1, spread=0.8),
        dict(sx=1.1, sy=0.9, tilt=12, bx=-8, ph=2.2, amp=3, trail=-74, curl=-10, star=3, spark=0.4, twk=1,
             spread=0.7, fan=2.6, tlen=0.84, smear=2),
        dict(sx=1.04, sy=0.95, tilt=8, bx=-6, ph=2.6, amp=6, trail=-62, curl=40, star=2, spark=0.85, twk=2,
             spread=0.8, fan=2.0, tlen=0.86),
        dict(sx=0.98, sy=1.02, tilt=2, bx=-2, ph=3.4, amp=12, trail=-12, curl=14, star=2, twk=3),
    ],
    "hurt": [  # knocked back: the bell dents, the star flickers dim, tentacles fling forward
        dict(sx=1.06, sy=0.88, tilt=14, bx=-3, by=-1, ph=1.0, amp=10, trail=-22, curl=14, star=1, dent=1.0, twk=0),
        dict(sx=1.0, sy=0.96, tilt=8, bx=-2, ph=1.6, amp=12, trail=-10, curl=8, star=2, dent=0.5, twk=1),
    ],
    "death": [  # dents, deflates and sags, the star gutters out, it sinks with limp tentacles and fades
        dict(sx=1.06, sy=0.88, tilt=14, bx=-3, by=-1, ph=1.0, amp=10, trail=-22, curl=14, star=1, dent=1.0),
        dict(sx=1.02, sy=0.74, tilt=6, bx=-3, by=3, ph=1.6, amp=9, trail=-6, curl=12, star=1, dent=0.6, droop=2.5,
             tlen=0.84, spread=1.1, motes=1),
        dict(sx=0.96, sy=0.6, tilt=0, bx=-2, by=6, ph=2.2, amp=7, trail=0, curl=6, star=0, dent=0.4, droop=4.5,
             tlen=0.72, spread=1.2, motes=2),
        dict(sx=0.92, sy=0.54, tilt=-4, bx=-2, by=9, ph=2.8, amp=6, trail=4, curl=4, star=0, droop=5.5, tlen=0.62,
             spread=1.25, fade=0.6, motes=3),
        dict(sx=0.9, sy=0.5, tilt=-6, bx=-2, by=11, ph=3.3, amp=5, trail=6, curl=2, star=0, droop=6.0, tlen=0.55,
             spread=1.3, fade=0.3),
    ],
})

W0, H0 = 14.5, 15.0  # bell half-width, dome height (local px)
RIM = 6.0  # rim line below the bell centre (local y)
# tentacles: (root x at the rim, length, root radius, tip radius, phase key, material)
STRANDS = (
    (-9.5, 32.0, 1.05, 0.55, 0.0, TENT),
    (9.5, 30.0, 1.05, 0.55, 2.1, TENT),
    (-5.5, 34.0, 1.1, 0.55, 1.1, TENT),
    (5.5, 33.0, 1.1, 0.55, 3.0, TENT),
    (-1.8, 24.0, 1.7, 0.7, 4.0, FRILL),
    (1.8, 22.0, 1.7, 0.7, 5.2, FRILL),
)


def _strand(root, L, a0, curl, amp, ph, key, n=16):
    """Integrated wavy strand from ``root``: angle 0 = straight down, + = back (left)."""
    pts = [root]
    x, y = root
    ds = L / n
    for i in range(1, n + 1):
        s = i / n
        a = math.radians(a0 + curl * s * s + amp * math.sin(ph - s * 5.0 + key) * (0.35 + s))
        x += -math.sin(a) * ds
        y += math.cos(a) * ds
        pts.append((x, y))
    return pts


def _bell_geom(cv, p):
    """Dome mask from a parametric outline (so it can sag); sphere normals of the dome."""
    W, H = W0 * p.sx, H0 * p.sy
    top = []
    n = 18
    for i in range(n + 1):
        t = math.pi * i / n  # 0 = right rim .. pi = left rim
        s = math.sin(t)
        x = W * math.cos(t) * (1.0 - 0.1 * p.droop / 6.0 * (1 - s))
        y = RIM - H * s ** 0.85 + p.droop * (1 - s) ** 2
        top.append((x, y))
    # the rim curls slightly inward (a shallow concave underside), listed left -> right
    bot = [(-W * 0.55, RIM + 0.6 + p.droop * 0.3), (0.0, RIM - 0.4), (W * 0.55, RIM + 0.6 + p.droop * 0.3)]
    m = cv.mask_polygon(top + bot)
    _, nx, ny, nz = cv.geom_ellipse(0.0, RIM, W, H)
    return (m, nx, ny, nz), W, H


def _line_local(cv, a, b, colour, **kw):
    """1 px line between two local points, rasterised in canvas space."""
    A, B = cv.tp(a), cv.tp(b)
    with cv.xform(np.linalg.inv(cv.M)):
        cv.line((math.floor(A[0]), math.floor(A[1])), (math.floor(B[0]), math.floor(B[1])), colour, **kw)


def _cross(fx, x, y, arm=STAR_Y, core=STAR_W, name="twinkle"):
    fx.pixels([(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)], arm, name=name)
    fx.pixel(x, y, core, name=name)


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    C = (cv.gx + p.bx, cv.gy + p.by)
    back = cv.layer(above=False, outline=False)
    fx = cv.layer(above=True, outline=False)
    body = (px.rotate(p.tilt, C), px.translate(C[0], C[1]))
    tips = []
    with cv.xform(*body):
        geom, W, H = _bell_geom(cv, p)
        root0 = cv.tp((0.0, RIM))
        # ---- tentacles + oral arms (behind the bell) ------------------------------------------
        strands = []
        for (rx, L, r0, r1, key, mat) in STRANDS:
            root = (rx * p.sx * p.spread, RIM - 1.0 + p.droop * 0.5 * abs(rx) / 10.0)
            fan = rx * p.fan * p.spread  # the outer strands fan out a little
            pts = _strand(root, L * p.tlen, p.trail - fan, p.curl, p.amp, p.ph, key)
            radii = [r0 + (r1 - r0) * (i / (len(pts) - 1)) ** 0.8 for i in range(len(pts))]
            cv.limb(pts, radii, mat, shade="two", name="strand")
            strands.append(([cv.tp(q) for q in pts], mat, rx))
            if mat is TENT:
                tips.append(cv.tp(pts[-1]))
        # ---- frill: scallops hanging under the rim, the bell over their upper halves -----------
        k = 7
        for i in range(k):
            x = -W + 2.4 + (2 * W - 4.8) * i / (k - 1)
            y = RIM + 1.5 + p.droop * (abs(x) / W) ** 2 * 0.9
            cv.circle(x, y, 1.8, FRILL, shade="soft", name="frill")
        cv.draw_geom(geom, BELL, name="bell", sep=True)
        if p.dent > 0:  # a dent punched into the upper front of the bell
            d = p.dent
            cv.ellipse(W * 0.72, RIM - H * 0.78, 3.4 * d + 0.6, 2.6 * d + 0.4, BELL, angle=-35, erase=True)
        # ---- inside the bell: strand roots showing through, lit halo, canals, highlight ---------
        for (rx, L, r0, r1, key, mat) in STRANDS:
            x = rx * p.sx * p.spread * 0.9
            _line_local(cv, (x, RIM - 1.0), (x * 0.8, RIM - 4.2), (mat.shadow if mat is FRILL else BELL.light),
                        band=None, decal=True, clip="bell", name="bell")
        S = (0.0, RIM - H * 0.5)
        halo = {0: 0.0, 1: 3.6, 2: 5.4, 3: 7.0}[p.star]
        if halo:
            cv.ellipse(S[0], S[1] + 0.5, halo * min(1.0, p.sx + 0.1), halo * 0.85 * p.sy, BELL, shade="flatlight",
                       decal=True, clip="bell", name="bell")
            if p.star >= 3:  # the flare floods the middle of the bell with light
                cv.ellipse(S[0], S[1] + 0.5, halo * 0.62, halo * 0.55, px.flat(GLASS), shade="flat", decal=True,
                           clip="bell", name="bell")
        for ang in (-58, 58):  # faint canals from the star toward the rim
            a = math.radians(ang)
            q0 = (S[0] + math.sin(a) * (halo * 0.8 + 1.0), S[1] + math.cos(a) * (halo * 0.8 + 1.0))
            q1 = (math.sin(a) * W * 0.9, RIM - 1.6)
            _line_local(cv, q0, q1, BELL.step(1), band=None, decal=True, clip="bell", name="bell")
        # glassy highlight arc along the upper-left of the dome
        arc = [(-W * 0.78 * math.cos(math.radians(t)) * 0.92, RIM - H * 0.86 * math.sin(math.radians(t)) - 0.2)
               for t in (28, 48, 66, 82)]
        for a, b in zip(arc, arc[1:]):
            _line_local(cv, a, b, GLASS, decal=True, clip="bell", name="bell")
        if p.droop > 3:  # the deflated bell creases
            _line_local(cv, (-W * 0.5, RIM - H * 0.35), (-W * 0.1, RIM - H * 0.62), BELL.step(2), band=None,
                        decal=True, clip="bell", name="bell")
            _line_local(cv, (W * 0.15, RIM - H * 0.7), (W * 0.55, RIM - H * 0.3), BELL.step(2), band=None,
                        decal=True, clip="bell", name="bell")
        star_at = cv.tp(S)
    # ---- the star (stamped upright so it stays crisp) ----------------------------------------
    sx, sy = math.floor(star_at[0]), math.floor(star_at[1])
    if p.star == 3:
        cv.stamp(STAR_L, sx - 4, sy - 4, {"w": STAR_W, "y": STAR_Y, "o": STAR_O}, name="star")
    elif p.star == 2:
        cv.stamp(STAR_M, sx - 3, sy - 3, {"w": STAR_W, "y": STAR_Y, "o": STAR_O}, name="star")
    elif p.star == 1:
        cv.stamp(STAR_S, sx - 2, sy - 2, {"w": STAR_Y, "y": STAR_DIM}, name="star")
    else:
        cv.stamp(STAR_S, sx - 2, sy - 2, {"w": STAR_DIM, "y": STAR_OUT}, name="star")
    # ---- twinkling star points along the tentacles --------------------------------------------
    if p.star >= 1:
        for j, (pts, mat, rx) in enumerate(strands):
            if mat is not TENT:
                continue
            for m, s in enumerate((0.42, 0.7, 0.93)):
                q = pts[int(round(s * (len(pts) - 1)))]
                x, y = math.floor(q[0]), math.floor(q[1])
                if (j + m + p.twk) % 3 == 0 and p.fade >= 1.0:
                    _cross(fx, x, y)
                else:
                    fx.pixel(x, y, STAR_Y if (j + m) % 2 else GLASS, name="twinkle")
    # ---- windup: rings of star-glow open round the bell -----------------------------------------
    if p.glow:
        G = (C[0] + 0.5, C[1] - 1.5)
        r = 12.0 + p.glow * 0.6
        px.glow_ring(back, G[0], G[1], r, SPARK_V, thickness=1.0)
        if p.glow >= 2:
            px.glow_ring(back, G[0], G[1], r + 2.2, SMEAR, thickness=1.0)
        if p.glow >= 3:  # star points pinned on the ring
            for ang in (40, 140, 205, 335):
                q = px.polar(G, ang, r)
                _cross(fx, math.floor(q[0]), math.floor(q[1]))
    # ---- attack: the lash smear behind the strands ------------------------------------------------
    if p.smear:
        R0 = (root0[0], root0[1])
        for k, (r, a0, a1) in enumerate(((19.0, -95, -40), (24.0, -80, -30), (14.0, -100, -55))):
            if k >= 1 + p.smear:
                continue
            hc.arc_line(back, R0, r, a0, a1 + (22 if p.smear >= 2 else 0), SMEAR if k != 1 else SPARK_V,
                        name="smear")
    # ---- the sting: sparks bursting at the lashing tentacle tips --------------------------------
    if p.spark is not None:
        t = p.spark
        ex = min(cv.w - 10.0, max(q[0] for q in tips) - 1)
        ey = sum(q[1] for q in tips) / len(tips)
        if t < 0.6:
            px.impact(fx, ex + 2, ey, size=4, color=STAR_Y, core=STAR_W)
            for k, (dx, dy) in enumerate(((1, -6), (4, 4), (-3, 5), (-4, -5))):
                q = (math.floor(ex + 2 + dx), math.floor(ey + dy))
                fx.line(q, (q[0] + (1 if dx > 0 else -1), q[1] + (1 if dy > 0 else -1)), GLASS if k % 2 else STAR_Y,
                        name="spark")
        else:  # the burst scatters into fading star points
            for k, (dx, dy) in enumerate(((2, -7), (5, 2), (0, 6), (-4, -4), (4, -3))):
                q = (math.floor(ex + dx), math.floor(ey + dy))
                fx.line(q, (q[0] + 1, q[1]), STAR_Y if k % 2 else SPARK_V, name="spark")
    # ---- death: the star's last light drifts up out of the bell -----------------------------------
    if p.motes:
        for k in range(p.motes + 1):
            q = (math.floor(star_at[0] + (-3, 3, 0, -1)[k]), math.floor(star_at[1] - 9 - 3 * p.motes + 3 * k))
            fx.line(q, (q[0], q[1] + 1), STAR_DIM if k % 2 else STAR_Y, name="mote")
