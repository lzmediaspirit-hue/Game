"""Hollow drone - a small Hollow construct-insect that hunts in swarms (Hollow Metal).

View: side, facing right, flying (anchored at the shell centre).  ~28 art px from the tail
vanes to the lance tip, ~14 px tall with its wings, on a 64 px art canvas (cell 128).
Not a wasp (no waist, no rear sting) and not a beetle (no legs, no split wing cases): a
smooth spindle-shaped gunmetal shell in three riveted sections that ends in a long needle
lance at the front and two small vanes at the back.
Parts, back to front: far wing pair (a pale, blurred sweep; a dithered ghost shows the
other end of each beat), tail vanes, the shell (rear cone, mid section, darker front cowl),
ash-white fissures spreading from the sickly violet core light in the mid section, one
empty white Hollow eye in a dark socket on the cowl, the lance (pale steel, bright tip),
near wing pair.
Idle: hovers with a jittery 1 px buzz, the wings flick between the ends of the beat and the
core pulses.  Walk: darts forward in short bursts with speed streaks.  Windup: pulls back,
levels the lance at the target, the core flares brighter inside a violet glow (held).
Attack: a lance thrust; the lance telescopes out and a violet spark bursts at its tip on
frame 1.  Hurt: sparks spit from the shell.  Death: the core bursts, the shell splits into
grey flakes that tumble away and fade.
"""
import math

import numpy as np

import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "hollow_drone",
    "cell": 128,
    "anchor": [64, 64],
    "flying": True,
    "hit_frame": 1,
}

# ---- palette: dull gunmetal, pale steel lance, ash-white cracks, sickly violet core -------------
SHELL = px.material("hd_shell", "#b4bac6", "#7e8594", "#565b6c", "#3a3d4d", outline="#0c0e15",
                    thresholds=(0.84, 0.42, 0.06))
LANCE = px.material("hd_lance", "#f0f0f6", "#b4b6c6", "#7e8096", "#50526a", outline="#10111c")
WING = px.material("hd_wing", "#f6f7fd", "#d4d8ee", "#a3a9cc", "#7a80a6", outline="#262b44")
FLAKE = px.material("hd_flake", "#c9cdd2", "#979ca4", "#6c7179", "#4a4f57", outline="#15181d")
ASH = px.rgb("#ebe8df")
VOID = px.rgb("#1d1827")
CORE = px.material("hd_core", "#f6ecff", "#c08cf0", "#8350c8", "#45256e", outline="#130a22")
GHOST = px.rgb("#b9bed8")
SPARK_V = px.rgb("#c08cf0")
SPARK_W = px.rgb("#f6ecff")
STREAK = px.rgb("#9aa0b8")

# shell outline, local to the shell centre (x forward): tail point, belly, cowl nose, back
SHELL_PTS = [(-12.0, 0.8), (-8.5, 3.2), (-3.0, 4.6), (2.5, 4.4), (6.0, 3.0), (7.8, 0.6), (7.2, -1.6), (5.0, -3.6),
             (0.5, -4.8), (-4.5, -4.4), (-9.0, -2.4)]

# ---- poses ------------------------------------------------------------------------------------
# bx, by   shell offset      tilt  pitch (deg, + = nose up)     wing  beat end: 0 = up, 1 = down
# ghost    draw the dithered other end of the beat     glow  core brightness 0..3
# reach    lance telescoped out (px)     spark  lance-tip spark (None / size)   streaks  speed lines
# eye      open|squeeze    hurt  shell sparks     burst  death core burst life    split  0..1 shell apart
DEFAULTS = dict(bx=0, by=0, tilt=0, wing=0, ghost=True, glow=0, reach=0.0, spark=None, streaks=0, eye="open",
                hurt=False, burst=None, split=0.0, fade=1.0, flakes=0.0)

POSE = px.poses(DEFAULTS, {
    "idle": [  # hovering buzz: 1 px jitter, wings flick, core pulses
        dict(wing=0, by=0, glow=0),
        dict(wing=1, by=-1, glow=1),
        dict(wing=0, by=0, bx=1, glow=0),
        dict(wing=1, by=1, glow=1),
    ],
    "walk": [  # darts forward in bursts
        dict(wing=0, tilt=-6, bx=-1),
        dict(wing=1, tilt=-10, bx=2, streaks=2),
        dict(wing=0, tilt=-10, bx=4, by=1, streaks=3),
        dict(wing=1, tilt=-6, bx=4, by=1, streaks=1),
        dict(wing=0, tilt=-3, bx=2),
        dict(wing=1, tilt=-4, bx=0, by=-1),
    ],
    "windup": [  # pulls back, lance levelled at the target, the core flares - held
        dict(wing=0, tilt=8, bx=-2, by=-1, glow=2),
        dict(wing=1, tilt=2, bx=-4, by=-1, glow=3),
        dict(wing=0, tilt=-3, bx=-5, by=-1, glow=3, eye="open"),
    ],
    "attack": [  # lance thrust: violet spark at the tip on frame 1
        dict(wing=1, tilt=-4, bx=1, glow=3, streaks=3, reach=1.0),
        dict(wing=0, tilt=-3, bx=6, glow=3, reach=2.5, spark=4, streaks=2),
        dict(wing=1, tilt=2, bx=4, glow=1, reach=1.5, spark=2),
        dict(wing=0, tilt=0, bx=1, glow=0),
    ],
    "hurt": [  # knocked back, sparks spit from the shell
        dict(wing=1, tilt=14, bx=-4, by=-1, eye="squeeze", hurt=True, glow=0),
        dict(wing=0, tilt=6, bx=-2, eye="squeeze", glow=1),
    ],
    "death": [  # the core bursts, the shell splits into grey flakes that tumble away
        dict(wing=1, tilt=10, bx=-3, by=-1, eye="squeeze", glow=3, burst=0.2),
        dict(wing=0, tilt=-10, bx=-3, by=1, eye="squeeze", glow=3, burst=0.6, split=0.35, ghost=False),
        dict(tilt=-20, bx=-3, by=3, split=0.75, flakes=0.3, ghost=False, burst=0.95),
        dict(tilt=-30, bx=-3, by=5, split=1.15, flakes=0.65, ghost=False, fade=0.6),
        dict(tilt=-40, bx=-3, by=6, split=1.45, flakes=1.0, ghost=False, fade=0.3),
    ],
})

# shell pieces for the break-up: (polygon indices / custom points, drift dx, dy, spin)
PIECES = [
    ([(-12.0, 0.8), (-8.5, 3.2), (-5.5, 4.0), (-5.0, -3.8), (-9.0, -2.4)], (-5.0, 3.0, 40)),  # rear cone
    ([(-5.0, -3.8), (-5.5, 4.0), (-3.0, 4.6), (1.2, 4.5), (1.0, -0.2)], (-1.0, 6.0, -30)),  # mid, lower
    ([(-5.0, -3.8), (1.0, -0.2), (1.2, -4.7), (0.5, -4.8), (-4.5, -4.4)], (-2.0, -3.0, 55)),  # mid, upper
    ([(1.2, -4.7), (1.0, -0.2), (1.2, 4.5), (2.5, 4.4), (6.0, 3.0), (7.8, 0.6), (7.2, -1.6), (5.0, -3.6)],
     (4.0, 2.0, -45)),  # cowl
]


def _wing(cv, root, ang, length, far, blur=None, ghost_ang=None):
    """A buzzing insect wing: a slim pale blade with a dark vein, wrapped in a dithered blur
    (on the unoutlined layer ``blur``), plus a dithered ghost blade at the other end of the
    beat - reads as a fast blur without any alpha."""
    c = px.polar(root, ang, length * 0.5)
    name = "wing_far" if far else "wing"
    if blur is not None:
        dith = ((blur.X.astype(int) + blur.Y.astype(int)) % 2) == 0
        m = blur.mask_ellipse(c[0], c[1], length * 0.56, 2.9, angle=ang)
        if ghost_ang is not None:
            g = px.polar(root, ghost_ang, length * 0.5)
            m |= blur.mask_ellipse(g[0], g[1], length * 0.52, 1.8, angle=ghost_ang)
        m &= dith
        blur._commit(m, np.where(m, 1, -1).astype(np.int8), px.flat(GHOST), name="ghost")
    cv.ellipse(c[0], c[1], length * 0.5, 1.45, WING, angle=ang, shade="two" if far else "soft", bulge=0.5,
               name=name)
    a = px.polar(root, ang, length * 0.15)  # the vein along the blade
    b = px.polar(root, ang, length * 0.75)
    cv.line((math.floor(a[0]), math.floor(a[1])), (math.floor(b[0]), math.floor(b[1])),
            WING.deep if far else WING.shadow, decal=True, clip=name, name=name)


def _legs(cv, S, p):
    """Three small hooked legs tucked under the mid-section (dark, far pair darker)."""
    x, y = S
    swing = 1.0 if p.wing else 0.0
    for k, dx in enumerate((-4.0, -1.0, 2.0)):
        top = (x + dx, y + 3.2)
        knee = (x + dx - 0.5 + swing * 0.5, y + 6.2)
        foot = (x + dx - 2.5 + swing * 0.3, y + 7.6)
        cv.limb([top, knee, foot], [0.75, 0.6, 0.5], SHELL, shade="dark" if k != 1 else "two", name="leg")


def _shell(cv, S, p):
    pts = [(S[0] + x, S[1] + y) for x, y in SHELL_PTS]
    cv.polygon(pts, SHELL, name="shell")
    _shell_details(cv, S, p)


def _shell_details(cv, S, p):
    x, y = S
    # darker front cowl, a gunmetal sheen along the back, the section seams
    cv.polygon([(x + 1.5, y - 5.0), (x + 9.0, y - 5.0), (x + 9.0, y + 5.0), (x + 1.5, y + 5.0)], SHELL.step(1),
               decal=True, clip="shell", name="shell")
    cv.line((math.floor(x - 8), math.floor(y - 2)), (math.floor(x - 3), math.floor(y - 4)), SHELL.light, band=None,
            decal=True, clip="shell", name="shell")
    for sx in (-5.0, 1.0):
        cv.line((math.floor(x + sx), math.floor(y - 4.5)), (math.floor(x + sx + 0.5), math.floor(y + 4.5)),
                SHELL.deep, band=None, decal=True, clip="shell", name="shell")
    cv.pixel(math.floor(x - 6.0), math.floor(y - 2.0), SHELL.light, decal=True, clip="shell", name="shell")
    # the core: a dark socket, the violet light, ash-white fissures running out of it
    cx, cy = math.floor(x - 2.0), math.floor(y)
    fiss = [[(cx - 2, cy - 2), (cx - 3, cy - 3), (cx - 4, cy - 3)], [(cx + 2, cy + 2), (cx + 3, cy + 3), (cx + 3, cy + 4)],
            [(cx - 2, cy + 2), (cx - 4, cy + 2), (cx - 6, cy + 3)], [(cx - 2, cy), (cx - 5, cy - 1)]]
    crack = ASH if p.glow < 2 else (CORE.base if p.glow == 2 else CORE.light)  # the flare lights the cracks
    notch = VOID if p.glow < 2 else CORE.shadow
    for f in fiss:  # ash-white fissures, each opening from a dark notch at the core rim
        if len(f) == 2:
            cv.line(f[0], f[1], crack, decal=True, clip="shell", name="shell")
        for a, b in zip(f[1:], f[2:]):
            cv.line(a, b, crack, decal=True, clip="shell", name="shell")
        if p.glow >= 2:
            cv.line(f[0], f[1], crack, decal=True, clip="shell", name="shell")
        cv.pixel(f[0][0], f[0][1], notch, decal=True, clip="shell", name="shell")
    g = p.glow
    rows = ([".vv.", "vcCv", "vCCv", ".vv."] if g <= 0 else
            [".vv.", "vCwv", "vwCv", ".vv."] if g == 1 else
            [".cc.", "cwwc", "cwwc", ".cc."])
    hc.eye_stamp(cv, rows, cx - 1, cy - 1, {"v": CORE.deep, "c": CORE.shadow, "C": CORE.base, "w": CORE.light},
                 name="core")
    # one empty white Hollow eye in a dark socket on the cowl
    ex, ey = math.floor(x + 4.5), math.floor(y - 2.0)
    if p.eye == "squeeze":
        hc.eye_stamp(cv, ["kkkk", "kwwk", "kkkk"], ex - 1, ey, {"k": VOID, "w": px.EYE_WHITE}, name="eye")
    else:
        hc.eye_stamp(cv, ["kkkk", "kwwk", "kwwk", "kkkk"], ex - 1, ey - 1, {"k": VOID, "w": px.EYE_WHITE},
                     name="eye")


def _lance(cv, S, reach):
    base = (S[0] + 7.0, S[1] + 0.2)
    tip = (S[0] + 18.5 + reach, S[1] + 0.8)
    mid = px.lerp_pt(base, tip, 0.35)
    cv.limb([base, mid, tip], [1.6, 1.0, 0.45], LANCE, shade="two", name="lance", sep="deep")
    # a collar ring where the lance leaves the cowl and a bright point
    cv.line((math.floor(base[0] + 1), math.floor(base[1] - 1)), (math.floor(base[0] + 1), math.floor(base[1] + 1)),
            LANCE.deep, band=None, decal=True, clip="lance", name="lance")
    cv.pixel(math.floor(tip[0]) - 1, math.floor(tip[1]), LANCE.light, decal=True, clip="lance", name="lance")
    return tip


def _vanes(cv, S):
    x, y = S
    cv.polygon([(x - 10.0, y - 1.2), (x - 13.5, y - 4.6), (x - 14.0, y - 3.0), (x - 12.4, y + 0.4)], SHELL,
               shade="two", name="vane")
    cv.polygon([(x - 10.0, y + 2.0), (x - 13.8, y + 4.6), (x - 14.0, y + 3.0), (x - 12.4, y + 1.0)], SHELL,
               shade="dark", name="vane")


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    S = (cv.gx - 3.5 + p.bx, cv.gy + 0.5 + p.by)
    back = cv.layer(above=False, outline=False)
    if p.split > 0:
        _broken(cv, S, p, frame)
        return
    beat = (96, 150) if p.wing == 0 else (150, 96)  # (current, other) forewing angle: up / back
    with cv.xform(px.rotate(p.tilt, S)):
        root = (S[0] + 0.5, S[1] - 3.8)
        blur = back if p.ghost else None
        # far pair, behind the shell
        _wing(cv, (root[0] + 1.5, root[1] - 0.2), beat[0] - 8, 12.0, far=True, blur=blur, ghost_ang=beat[1] - 8)
        _wing(cv, (root[0] - 1.5, root[1] + 0.2), beat[0] + 26, 9.5, far=True, blur=blur)
        _legs(cv, S, p)
        _vanes(cv, S)
        _shell(cv, S, p)
        tip = _lance(cv, S, p.reach)
        core_c = cv.tp((S[0] - 1.5, S[1] + 0.5))
        # near pair: forewing and a shorter hindwing fanned further back
        _wing(cv, root, beat[0] + 6, 13.0, far=False, blur=blur, ghost_ang=beat[1] + 6)
        _wing(cv, (root[0] - 2.5, root[1] + 0.6), beat[0] + 34, 8.5, far=False, blur=blur,
              ghost_ang=beat[1] + 20)
        tip = cv.tp(tip)
    if p.glow >= 2:  # the core flares: violet rays spitting from it
        glow = cv.layer(above=True, outline=False)
        cx, cy = math.floor(core_c[0]), math.floor(core_c[1])
        n = 3 + p.glow
        for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            glow.line((cx + dx * 3, cy + dy * 3), (cx + dx * n, cy + dy * n), CORE.base, name="glow")
        if p.glow >= 3:
            for (dx, dy) in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
                glow.line((cx + dx * 3, cy + dy * 3), (cx + dx * 4, cy + dy * 4), CORE.shadow, name="glow")
    if p.streaks:
        for k in range(p.streaks):
            y = S[1] - 3 + k * 3
            back.line((math.floor(S[0] - 15 - k), math.floor(y)), (math.floor(S[0] - 21 - 2 * (k % 2)), math.floor(y)),
                      STREAK, name="streak")
    if p.spark is not None:
        top = cv.layer(above=True, outline=False)
        px.impact(top, tip[0] + 1, tip[1], size=p.spark, color=SPARK_V, core=SPARK_W)
        if p.spark >= 4:
            px.glow_ring(back, tip[0] + 1, tip[1], 2.0, CORE.shadow, thickness=1.0)
            hc.sparks(top, tip[0] + 1, tip[1], 0.5, n=4, radius=7, colors=(SPARK_W, SPARK_V), seed=11,
                      spread=160, aim=0)
    if p.hurt:
        top = cv.layer(above=True, outline=False)
        hc.sparks(top, core_c[0], core_c[1] - 2, 0.6, n=5, radius=9, colors=(SPARK_W, SPARK_V), seed=5,
                  spread=200, aim=110)
        hc.sparks(top, S[0] + 5, S[1] - 3, 0.4, n=3, radius=6, colors=(px.GLINT, px.WARM_GOLD), seed=8,
                  spread=90, aim=60)
    if p.burst is not None:
        _core_burst(cv, core_c, p.burst)


def _core_burst(cv, c, t):
    top = cv.layer(above=True, outline=False)
    if t < 0.4:  # the core flares white
        px.glow_ring(top, c[0], c[1], 2.5, SPARK_W, thickness=1.0, inner=SPARK_V)
    else:
        px.glow_ring(top, c[0], c[1], 3 + 8 * t, SPARK_V if t < 0.8 else CORE.shadow, thickness=1.0)
        hc.sparks(top, c[0], c[1], t, n=7, radius=12, colors=(SPARK_W, SPARK_V), seed=21)


def _broken(cv, S, p, frame):
    """The shell split into pieces drifting apart and falling, shedding small grey flakes."""
    sp = p.split
    for k, (pts, (dx, dy, spin)) in enumerate(PIECES):
        off = (dx * sp, dy * sp + 3.0 * sp * sp)
        c = (sum(q[0] for q in pts) / len(pts), sum(q[1] for q in pts) / len(pts))
        mat = SHELL if sp < 0.5 else FLAKE
        with cv.xform(px.translate(S[0] + off[0], S[1] + off[1]), px.rotate(p.tilt + spin * sp, c)):
            cv.polygon(pts, mat, name=f"piece{k}")
            if k == 3 and sp < 0.9:  # the dead eye on the cowl piece
                cv.pixels([(4, -2), (5, -2)], FLAKE.deep, name="eye")
    if sp < 0.9:  # the lance tumbles
        with cv.xform(px.translate(S[0] + 6.0 * sp, S[1] + 5.0 * sp), px.rotate(-35 * sp, (7.0, 0.0))):
            cv.limb([(7.0, 0.2), (12.0, 0.4), (18.5, 0.8)], [1.6, 1.0, 0.45], LANCE if sp < 0.5 else FLAKE,
                    shade="two", name="lance")
    if p.flakes > 0:  # small grey flakes fluttering down
        fl = cv.layer(above=True, outline=True)
        for k in range(6):
            h = px.hash01("hdf", k)
            x = S[0] - 10 + k * 4.5 + (h - 0.5) * 3
            y = S[1] - 4 + p.flakes * (8 + 6 * h) + (k % 3) * 2
            w = 2 if (k + frame) % 2 else 1
            fl.rect(math.floor(x), math.floor(y), w, 3 - w, FLAKE, shade="two", name="flake")
    if p.burst is not None:
        _core_burst(cv, (S[0] - 1.5, S[1] + 0.5), p.burst)
