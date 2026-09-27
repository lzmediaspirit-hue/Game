"""Copperjaw swarm - a cloud of small copper beetles, the Copperjaw Box let loose (Metal).

View: side, heading right, flying (anchored at the cloud's centre).  Eleven beetles at three
depths make a loose cloud ~28 art px wide and ~18 tall on a 64 px art canvas (cell 128); the
near ones are ~7 art px long with a glint in the eye, the far ones ~4 px and dim.  Each
beetle is a copper wing-case oval with a seam and a darker pronotum band, a dark chitin head,
pale-gold jaws (the copper jaw) and, whenever its wing cases lift, two pale wing blurs over
its back.  The wing cases flick open and shut from beetle to beetle so the cloud buzzes.
Idle: the cloud hangs, every beetle drifting round its own small loop.  Walk: the cloud
streams forward, stretched and pitched nose-down, with streaks behind.  Windup: the cloud
draws back and balls up, jaws opening, a copper ring tightening round it (held).  Attack:
the ball lances forward as a spearhead and bites on frame 1 (a spark at the tip), then
loosens.  Hurt: the cloud is blown back and scattered, beetles tumbling, copper dust flung
off.  Death: the beetles tumble and rain down, land on their backs with their legs up, and
fade.
``draw(cv, action, frame, queen=True)`` adds a large gold-cased Queen with a pale-gold crown
at the heart of the cloud, leading its lance (the ``copperjaw_queen`` sheet).
"""
import math

import pixel as px

SPEC = {
    "id": "copperjaw_swarm",
    "cell": 128,
    "anchor": [64, 64],
    "flying": True,
    "hit_frame": 1,
}

# ---- palette: copper wing cases, dark chitin, pale wing blurs, the Queen's gold, copper dust ------
COPPER = px.material("cj_copper", "#f4c98c", "#cf8442", "#93522a", "#5c311a", outline="#1c0d07",
                     thresholds=(0.86, 0.5, 0.18))
CHITIN = px.material("cj_chitin", "#8c6a4e", "#5e4131", "#3f2a20", "#241612", outline="#0f0806")
WING = px.material("cj_wing", "#fff6dc", "#f0dcaa", "#cdb07a", "#9c8354", outline="#4a3a26")
QUEEN = px.material("cj_queen", "#fff0b8", "#e5b84c", "#a87c2c", "#6a4b1c", outline="#1c0d07",
                    thresholds=(0.86, 0.5, 0.18))
SPECK = px.material("cj_speck", "#f4c98c", "#e0a258", "#b3743a", "#7c4c26", outline="#3a2010")
JAW = px.rgb("#ffe6a1")
JAW_DIM = px.rgb("#e5b84c")
CROWN = px.rgb("#ffe6a1")
RING = px.rgb("#b3743a")
RING_HOT = px.rgb("#ffe6a1")
STREAK = px.rgb("#cdb07a")

# ---- the cloud: (x, y) from its centre, depth tier, loop phase (deg) ----------------------------
# Tier 0 is the far back of the cloud (small, dim), 1 the middle, 2 the near front (large, lit).
BEETLES = [
    (-12.0, -3.0, 0, 0), (-3.0, -9.5, 0, 90), (6.5, -8.0, 0, 180), (11.5, -0.5, 0, 270),
    (-9.5, 5.5, 1, 45), (-1.0, -3.5, 1, 135), (9.0, -4.5, 1, 225), (0.5, 9.0, 1, 315),
    (-5.0, 0.0, 2, 30), (4.5, 2.0, 2, 150), (7.5, 8.0, 2, 270),
]
# per tier: wing-case radii, head radius, wing blur length, body shading
TIER = (
    dict(rx=1.8, ry=1.1, hr=0.75, wl=1.5, shade="nolight", head="dark"),
    dict(rx=2.5, ry=1.45, hr=1.0, wl=2.0, shade="two", head="two"),
    dict(rx=3.1, ry=1.8, hr=1.3, wl=2.5, shade="full", head="two"),
)
QUEEN_TIER = dict(rx=4.8, ry=2.9, hr=1.9, wl=3.2, shade="full", head="two")

# ---- poses --------------------------------------------------------------------------------------
# bx, by    cloud offset            sx, sy   cloud stretch          spin  loop phase of every beetle (deg)
# amp       loop radius (x, y)      gather   0..1 pull toward the centre (the ball)
# pitch     heading of every beetle (deg, CCW; - = nose down)      spread  per-beetle heading scatter (deg)
# jaws      jaws open               beat     wing-case flicker parity   scatter  push out from the centre (px)
# tumble    per-beetle roll (deg)   drop     0..1 fall to the landing row   lying  on their backs, legs up
# ring      windup ring 0..2        hit      impact spark at the tip       streaks  speed lines behind
# dust      copper dust life (None = off)   fade  frame opacity
DEFAULTS = dict(bx=0, by=0, sx=1.0, sy=1.0, spin=0, amp=(1.0, 0.8), gather=0.0, pitch=0, spread=0, jaws=False,
                beat=0, scatter=0.0, tumble=0.0, drop=0.0, lying=False, ring=0, hit=False, streaks=0, dust=None,
                fade=1.0)

POSE = px.poses(DEFAULTS, {
    "idle": [  # the cloud hangs and breathes; every beetle rounds its own small loop
        dict(spin=0, beat=0),
        dict(spin=90, beat=1, by=-1),
        dict(spin=180, beat=0, by=-1, spread=4),
        dict(spin=270, beat=1, spread=4),
    ],
    "walk": [  # streams forward: stretched, nose-down, streaks behind
        dict(spin=0, beat=0, sx=1.15, sy=0.85, amp=(1.4, 1.0), pitch=-8, streaks=2),
        dict(spin=60, beat=1, sx=1.18, sy=0.82, amp=(1.4, 1.0), pitch=-9, bx=1, streaks=3),
        dict(spin=120, beat=0, sx=1.2, sy=0.8, amp=(1.4, 1.0), pitch=-8, bx=1, by=-1, streaks=3),
        dict(spin=180, beat=1, sx=1.18, sy=0.82, amp=(1.4, 1.0), pitch=-7, by=-1, streaks=2),
        dict(spin=240, beat=0, sx=1.15, sy=0.85, amp=(1.4, 1.0), pitch=-8, streaks=3),
        dict(spin=300, beat=1, sx=1.15, sy=0.85, amp=(1.4, 1.0), pitch=-9, bx=1, streaks=3),
    ],
    "windup": [  # draws back and balls up, jaws open, a copper ring tightens - held
        dict(gather=0.35, bx=-1, jaws=True, spin=20, beat=0, spread=12),
        dict(gather=0.7, bx=-2, jaws=True, spin=40, beat=1, spread=6, ring=1),
        dict(gather=0.85, bx=-3, jaws=True, spin=60, beat=0, ring=2),
    ],
    "attack": [  # the ball lances forward as a spearhead; bites on frame 1; loosens
        dict(gather=0.5, bx=3, sx=1.3, sy=0.7, jaws=True, spin=80, beat=1, streaks=2),
        dict(gather=0.4, bx=5, sx=1.3, sy=0.55, jaws=True, spin=100, beat=0, streaks=3, hit=True),
        dict(gather=0.15, bx=4, sx=1.15, sy=0.85, jaws=True, spin=120, beat=1, spread=14),
        dict(bx=2, spin=140, beat=0, spread=8),
    ],
    "hurt": [  # blown back and scattered, beetles tumbling, dust flung off
        dict(bx=-4, scatter=3.0, tumble=40, spin=200, beat=1, spread=20, dust=0.2),
        dict(bx=-3, scatter=1.5, tumble=20, spin=220, beat=0, spread=10, dust=0.55),
    ],
    "death": [  # tumble, rain down, land on their backs, fade
        dict(bx=-3, scatter=3.0, tumble=45, spin=200, beat=1, dust=0.2),
        dict(bx=-3, scatter=3.5, tumble=120, drop=0.3, spread=30),
        dict(bx=-3, scatter=4.0, tumble=200, drop=0.7),
        dict(bx=-3, scatter=4.0, drop=1.0, lying=True, fade=0.6),
        dict(bx=-3, scatter=4.0, drop=1.0, lying=True, fade=0.3),
    ],
})

LAND_Y = 50.0  # the row the fallen beetles land on (art px), plus a little each


def _pos(C, b, i, p):
    """Canvas position of beetle ``i`` (cloud offset ``b``) in pose ``p``."""
    x, y, _tier, ph = b
    th = math.radians(ph + p.spin)
    lx = x * p.sx + math.cos(th) * p.amp[0]
    ly = y * p.sy + math.sin(th) * p.amp[1]
    lx *= 1.0 - 0.45 * p.gather
    ly *= 1.0 - 0.5 * p.gather
    if p.scatter:  # pushed out from the centre, a little more for the outer beetles
        d = math.hypot(x, y) or 1.0
        lx += x / d * p.scatter * (0.7 + 0.6 * px.hash01("cj_sc", i))
        ly += y / d * p.scatter * (0.7 + 0.6 * px.hash01("cj_sc", i))
    cx, cy = C[0] + p.bx + lx, C[1] + p.by + ly
    if p.drop:  # falls to its own landing row, drifting sideways as it tumbles
        t = p.drop * p.drop  # gathering speed
        land = LAND_Y + 6.0 * px.hash01("cj_land", i)
        cx += (px.hash01("cj_drift", i) - 0.5) * 8.0 * p.drop
        cy = cy + (land - cy) * t
    return cx, cy


def _heading(i, p):
    if p.lying:
        return 0.0
    ang = p.pitch + (px.hash01("cj_head", i) - 0.5) * 2.0 * p.spread
    if p.tumble:
        ang += (px.hash01("cj_tumble", i) - 0.5) * 2.0 * p.tumble + p.drop * 90.0 * (1 if i % 2 else -1)
    return ang


def _beetle(cv, i, C, T, ang, p, mat=COPPER, open_wings=False, crown=False):
    """One beetle centred at ``C`` heading ``ang`` (deg, CCW): wing blurs, wing cases with a
    seam and pronotum band, head, jaws, a glint; legs up when lying on its back."""
    x, y = C
    rx, ry, hr = T["rx"], T["ry"], T["hr"]
    n = "b%d" % i
    xf = [px.rotate(ang, (x, y))]
    if p.lying:
        xf.append(px.flip_y(y))
    with cv.xform(*xf):
        if open_wings:  # the lifted cases: two pale blurs swept up and back over the body
            cv.ellipse(x - rx * 0.7, y - ry - 1.4, T["wl"] * 0.8, 0.6, WING, angle=-14, shade="two", name=n + "w")
            cv.ellipse(x - rx * 0.4, y - ry - 0.7, T["wl"], 0.7, WING, angle=-34, shade="soft", name=n + "w")
        cv.ellipse(x, y, rx, ry, mat, shade=T["shade"], name=n, sep=True)
        if rx >= 2.5:  # the seam between the wing cases and the darker pronotum in front
            row = math.floor(y)
            cv.line((math.floor(x - rx + 1), row), (math.floor(x + rx * 0.3), row), mat.shadow, decal=True, clip=n, name=n)
            col = math.floor(x + rx * 0.45)
            cv.line((col, math.floor(y - ry + 0.6)), (col, math.floor(y + ry - 0.6)), mat.shadow, decal=True, clip=n, name=n)
        if rx >= 3.0:  # a pale speck of light on the near cases
            cv.pixel(math.floor(x - rx * 0.35), math.floor(y - ry * 0.55), mat.light, decal=True, clip=n, name=n)
        hx, hy = x + rx + hr * 0.5, y + 0.3
        cv.circle(hx, hy, hr, CHITIN, shade=T["head"], name=n + "h", sep="deep")
        jx, jy = math.floor(hx + hr * 0.9), math.floor(hy)
        if p.jaws and rx >= 2.5:  # open: a V of pale gold
            cv.pixels([(jx, jy - 1), (jx, jy + 1)], JAW, name=n + "j")
        elif rx >= 2.5 or p.jaws:
            cv.pixel(jx, jy, JAW_DIM if rx < 3.0 else JAW, name=n + "j")
        if rx >= 3.0:
            cv.pixel(math.floor(hx - hr * 0.3), math.floor(hy - hr * 0.55), px.GLINT, name="eye")
        if p.lying and rx >= 2.5:  # legs in the air (the frame is flipped, so they hang below the belly)
            for dx in (-1.6, 0.2, 1.6):
                cv.pixels([(math.floor(x + dx), math.floor(y + ry + 0.3)), (math.floor(x + dx), math.floor(y + ry + 1.3))],
                          CHITIN.base, name=n + "l")
        if crown:  # the Queen's pale-gold crown over the pronotum
            cx = math.floor(x + rx * 0.35)
            top = math.floor(y - ry) - 2
            cv.stamp(["g.g.g", "ggggg"], cx - 2, top, {"g": CROWN}, name=n + "c")


def draw(cv: px.Canvas, action: str, frame: int, queen: bool = False) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    C = (cv.gx + 0.5, cv.gy + 0.5)
    back = cv.layer(above=False, outline=False)
    fx = cv.layer(above=True, outline=False)
    if p.streaks:  # streaks trailing the rear of the cloud
        rear = C[0] + p.bx - 13.0 * p.sx * (1.0 - 0.4 * p.gather)
        px.speed_lines(back, rear, C[1] + p.by - 1, length=5 + p.streaks, count=p.streaks, spacing=4,
                       direction=-1, color=STREAK)
    order = sorted(range(len(BEETLES)), key=lambda k: (BEETLES[k][2], _pos(C, BEETLES[k], k, p)[1]))
    for i in order:
        b = BEETLES[i]
        T = TIER[b[2]]
        pos = _pos(C, b, i, p)
        wings = ((i + p.beat) % 2 == 0) and not p.lying and p.drop < 0.5 and p.tumble < 30
        _beetle(cv, i, pos, T, _heading(i, p), p, open_wings=wings)
    if queen:  # the Queen at the heart of the cloud, a little ahead when it lances
        q = (C[0] + p.bx + 1.0 + 3.0 * p.gather + (0.5 if p.spin % 180 else 0.0),
             C[1] + p.by + 0.5 - (1.0 if 90 <= p.spin % 360 < 270 else 0.0))
        if p.scatter:
            q = (q[0] - p.scatter * 0.5, q[1] + p.scatter * 0.3)
        if p.drop:
            land = LAND_Y + 3.0
            q = (q[0] + 2.0 * p.drop, q[1] + (land - q[1]) * p.drop * p.drop)
        ang = p.pitch * 0.5 + (p.tumble * 0.35 + p.drop * 60.0 if p.tumble or p.drop else 0.0)
        _beetle(cv, 99, q, QUEEN_TIER, ang, p, mat=QUEEN, open_wings=(p.beat == 1 and not p.lying and p.drop < 0.5),
                crown=True)
    if p.ring:  # the windup tell: a copper ring closing round the ball, hot on the held frame
        cx, cy = C[0] + p.bx, C[1] + p.by
        r = 13.0 if p.ring == 1 else 11.0
        px.glow_ring(fx, cx, cy, r, RING if p.ring == 1 else RING_HOT, thickness=1.0)
        if p.ring == 2:  # glints at the jaws in front
            for (dx, dy) in ((9.0, -3.0), (11.0, 2.0), (8.0, 5.0)):
                gx, gy = math.floor(cx + dx), math.floor(cy + dy)
                fx.pixels([(gx - 1, gy), (gx + 1, gy), (gx, gy - 1), (gx, gy + 1)], JAW_DIM, name="glint")
                fx.pixel(gx, gy, px.GLINT, name="glint")
    if p.hit:  # the bite lands at the spearhead's tip
        tip = (C[0] + p.bx + 13.5 * p.sx * (1.0 - 0.45 * p.gather) + 2.0, C[1] + p.by + 0.5)
        px.impact(fx, tip[0], tip[1], size=3)
    if p.dust is not None:  # copper dust flung off the scattered cloud
        lay = cv.layer(above=True, outline=True)
        t = p.dust
        for k, (dx, dy) in enumerate(((-15.0, -7.0), (-17.0, 2.0), (-14.0, 9.0), (12.0, -9.0), (14.0, 8.0))):
            sx = C[0] + p.bx + dx * (1.0 + t * 0.5)
            sy = C[1] + p.by + dy * (1.0 + t * 0.4) - t * 2.0
            ix, iy = math.floor(sx), math.floor(sy)
            lay.pixels([(ix, iy), (ix + 1, iy)] + ([(ix, iy + 1)] if k % 2 == 0 and t < 0.4 else []),
                       SPECK.base if k % 2 else SPECK.light, name="dust")
