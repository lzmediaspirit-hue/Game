"""The hollowed eel, the Hollow Night's great foe: a huge river eel drained grey by the Hollow, rising out of the river
in an S-curve over a dark stain in the water, drawn larger than the other foes for its boss presence. A grey body with a
pale belly down its front, a torn dorsal fin along its back, gill slits, a long snout with a hinged jaw of jagged
teeth, empty white eyes in a cold halo; grey strands rise and curl off its back, shedding motes of mist; behind it a loop
of its back breaks the surface. Foam rings its body where it leaves the water, rings spread from it and a wake trails
when it glides. It sways while idle and undulates as it glides. Its tell: it rears back high, the S drawn tight, its
jaws gaping wide and its eyes flaring. It lunges head-down on the strike, snaps its jaws and recoils; struck, it snaps
back, eyes screwed shut; beaten, it convulses and sinks back under the water, its strands coming apart into mist,
until only the stain and the rings are left.

The game hovers it 40 world units over the river's surface (enemy_authority.gd `_eel`), 20 art px, and the view draws
a foe's feet where it hovers and its shadow on the surface under it: so the figure rises out of water drawn EEL_LIFT px
under its feet.
"""
from __future__ import annotations

import math

import numpy as np

from . import mats as M
from .motion import h01, wave
from .sculpt import E, L, Pose, chain, rot, v3

EEL_LIFT = 20.0
ELEV = math.radians(35.0)
# Key poses from its side-view sheet (tools/art/creatures/hollowed_eel.py): the spine's control points (x ahead, y down
# from the water, its art px; the first under the water), the head's tilt, the gape, the eyes and how far it has sunk.
IDLE = [((0, 8), (-6, -12), (8, -32), (20, -50), (12, -70), (24, -84)), ((0, 8), (-5, -12), (9, -32), (21, -50), (13, -70), (25, -83)),
        ((0, 8), (-4, -12), (10, -32), (21, -50), (14, -70), (26, -83)), ((0, 8), (-5, -12), (9, -32), (20, -50), (13, -70), (25, -84))]
IDLE_HEAD = [0, -2, -3, -1]
WIND = [((0, 8), (-4, -14), (10, -32), (16, -50), (6, -68), (14, -84)), ((0, 8), (-1, -16), (13, -32), (11, -50), (-2, -66), (2, -85)),
        ((0, 8), (0, -17), (14, -33), (9, -52), (-5, -68), (-2, -88))]
ATTACK = [((0, 8), (-4, -14), (10, -30), (23, -44), (35, -54), (46, -60)), ((0, 8), (-2, -14), (13, -28), (28, -40), (42, -48), (54, -51)),
          ((0, 8), (-4, -13), (10, -30), (24, -46), (30, -64), (42, -74))]
HURT = [((0, 8), (-5, -12), (10, -32), (16, -50), (4, -68), (8, -86)), ((0, 8), (-6, -12), (9, -32), (18, -50), (9, -70), (18, -85))]
DEAD = [((0, 8), (-6, -12), (6, -30), (18, -44), (20, -60), (32, -66)), ((0, 8), (-6, -12), (6, -28), (18, -40), (24, -52), (36, -54))]


def _mix(a, b, t):
    return tuple((pa[0] + (pb[0] - pa[0]) * t, pa[1] + (pb[1] - pa[1]) * t) for pa, pb in zip(a, b))


def key(action: str, f: int):
    """(control points, head tilt, gape, eyes, sunk) for a frame, the old keys eased between for the new frames."""
    if action == "idle":
        u = f / 6.0 * 4.0
        i, t = int(u) % 4, u - int(u)
        return _mix(IDLE[i], IDLE[(i + 1) % 4], t), IDLE_HEAD[i] + (IDLE_HEAD[(i + 1) % 4] - IDLE_HEAD[i]) * t, 0.05 * (i == 2), "open", 0
    if action == "walk":
        return IDLE[0], -1.0 - wave(action, f), 0.0, "open", 0
    if action == "windup":
        return ((_mix(IDLE[0], WIND[0], 0.55), 6, 0.3, "open", 0), (WIND[0], 12, 0.55, "wide", 0),
                (_mix(WIND[0], WIND[1], 0.7), 22, 0.85, "wide", 0), (WIND[2], 32, 1.1, "wide", 0))[f]
    if action == "attack":
        return ((ATTACK[0], -6, 1.0, "wide", 0), (ATTACK[1], -12, 0.2, "wide", 0), (_mix(ATTACK[1], ATTACK[2], 0.25), -10, 0.0, "open", 0),
                (ATTACK[2], -4, 0.4, "open", 0), (_mix(ATTACK[2], IDLE[0], 0.5), -2, 0.2, "open", 0),
                (_mix(ATTACK[2], IDLE[0], 0.85), 0, 0.05, "open", 0))[f]
    if action == "hurt":
        return ((HURT[0], 26, 0.6, "squeeze", 0), (HURT[1], 12, 0.3, "squeeze", 0), (_mix(HURT[1], IDLE[0], 0.6), 4, 0.1, "open", 0))[f]
    return ((HURT[0], 22, 0.7, "squeeze", 0), (DEAD[0], -24, 0.5, "dead", 8), (_mix(DEAD[0], DEAD[1], 0.5), -28, 0.45, "dead", 20),
            (DEAD[1], -32, 0.4, "dead", 32), (DEAD[1], -34, 0.4, "dead", 44), (DEAD[1], -36, 0.4, "dead", 58),
            (DEAD[1], -36, 0.4, "dead", 74), (DEAD[1], -36, 0.4, "dead", 92))[f]


EEL_AHEAD, EEL_UP = 0.5, 0.55     # the side view's art px to the figure's, ahead and up (a lunge's reach a little less)
EEL_S = (0.0, 2.6, -1.8, 2.2, -0.9, 0.3)   # its S-curve sideways too, so it winds from every side, not a pillar
EEL_FIN = (1.4, 2.2, 1.0, 2.4, 1.6, 0.8, 2.0, 1.4, 2.2, 1.0, 1.8, 1.2)   # the torn dorsal fin's plates


def _spline(pts, n: int) -> list:
    """`n` points along a Catmull-Rom curve through `pts`, its ends held."""
    Q = [pts[0]] + list(pts) + [pts[-1]]
    segs = len(pts) - 1
    out = []
    for k in range(n):
        u = k / (n - 1) * segs
        s = min(int(u), segs - 1)
        t = u - s
        p0, p1, p2, p3 = (np.asarray(Q[s + i], float) for i in range(4))
        out.append(0.5 * (2.0 * p1 + (p2 - p0) * t + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t * t + (3.0 * p1 - p0 - 3.0 * p2 + p3) * t * t * t))
    return out


def eel(action: str, f: int, k: float = 1.44) -> Pose:
    P = Pose()
    P.water = -EEL_LIFT / math.cos(ELEV)          # in the world, at its drawn size
    wz = P.water / k                              # in its own frame
    ctrl, head_deg, gape, eye, sink = key(action, f)
    sway = {"idle": 1.2 * wave(action, f), "walk": 0.6 * wave(action, f, 0.25)}.get(action, 0.0)
    ahead = {"attack": 0.42, "death": 0.38}.get(action, EEL_AHEAD)
    pts = [v3(x * ahead, EEL_S[i] + sway * (i / 5.0) ** 2, wz - (y + sink) * EEL_UP) for i, (x, y) in enumerate(ctrl)]
    spine = _spline(pts, 56)
    if action == "walk":   # a wave rolls up the body
        ph = f / 8.0 * math.tau
        out = []
        for i, q in enumerate(spine):
            t = i / (len(spine) - 1)
            nxt, prv = spine[min(i + 1, len(spine) - 1)], spine[max(i - 1, 0)]
            ta, tc = nxt[0] - prv[0], nxt[2] - prv[2]
            ln = math.hypot(ta, tc) or 1.0
            s = 1.7 * math.sin(ph - t * 6.0) * min(1.0, t * 3.0) * (1.0 - t * 0.4)
            out.append(v3(q[0] - tc / ln * s, q[1], q[2] + ta / ln * s))
        spine = out
    n = len(spine)
    under = lambda q: q[:, 2] > wz               # cut off at the water's surface

    def radius(t):
        prof = ((0.0, 4.8), (0.3, 4.4), (0.6, 3.9), (0.85, 3.4), (1.0, 3.2))
        for (t0, r0), (t1, r1) in zip(prof, prof[1:]):
            if t <= t1:
                return r0 + (r1 - r0) * (t - t0) / (t1 - t0)
        return prof[-1][1]

    def skin(q, nn):
        """The pale belly down its front and underneath; faint scale rows (a step lit every other row) on the grey."""
        belly = (nn[:, 0] > 0.5) | (nn[:, 2] < -0.6)
        rows = (np.floor(q[:, 2] * 0.8) + np.floor(q[:, 1] * 0.8)) % 2 == 0
        return np.where(belly, "eel_belly", "eel").astype(object), np.where(rows & ~belly & (nn[:, 2] > 0.1), 1, 0).astype(np.int16)

    def tangent(i):
        a, b = spine[max(i - 3, 0)], spine[min(i + 3, n - 1)]
        ta, tc = b[0] - a[0], b[2] - a[2]
        ln = math.hypot(ta, tc) or 1.0
        return ta / ln, tc / ln

    for i in range(0, n - 1, 2):
        r0, r1 = radius(i / (n - 1)), radius(min(n - 1, i + 2) / (n - 1))
        P.add(L(spine[i], spine[min(n - 1, i + 2)], r0, r1, "eel", "body", skin, under))
    # The torn dorsal fin along its back (the side away from the belly), fluttering.
    for j, i in enumerate(range(10, n - 8, 3)):
        ta, tc = tangent(i)
        da, dc = -tc, ta
        h = EEL_FIN[j % len(EEL_FIN)] + 0.35 * math.sin(f * 1.7 + j)
        r = radius(i / (n - 1))
        q = spine[i]
        if q[2] < wz:
            continue
        m = np.array(((ta, 0.0, da), (0.0, 1.0, 0.0), (tc, 0.0, dc)))
        P.add(E(v3(q[0] + da * (r + h * 0.5 - 0.5), q[1], q[2] + dc * (r + h * 0.5 - 0.5)), (1.5, 0.45, h * 0.95), "eel_fin", "fin", m,
                clip=under, line=False))
    # A loop of its back breaking the surface behind it, a fin tip beyond; it rolls back along the body as it glides.
    roll = 1.6 * math.sin(f / 8.0 * math.tau) if action == "walk" else 0.0
    lift = {"idle": 0.4 * wave(action, f), "walk": 0.7 * wave(action, f, 0.25)}.get(action, 0.0) - sink * EEL_UP
    low = -2.6 - sink * EEL_UP
    loop = ((-5.6, 2.0, low), (-7.4, 3.8, 2.4 + lift), (-9.4, 5.6, 3.4 + lift), (-11.2, 7.2, 1.4 + lift * 0.5), (-12.6, 8.6, low))
    hump = _spline([v3(a + roll, b, wz + c_) for a, b, c_ in loop], 12)
    for i in range(len(hump) - 1):
        P.add(L(hump[i], hump[i + 1], 3.0 - 0.5 * i / 11.0, 3.0 - 0.5 * (i + 1) / 11.0, "eel", "hump", skin, under))
    for i in (4, 6, 8):
        q = hump[i]
        P.add(E(v3(q[0], q[1], q[2] + 3.0), (1.0, 0.35, 0.9 + 0.3 * (i % 3)), "eel_fin", "hump_fin", rot("c", -42.0), clip=under, line=False))
    P.add(E(v3(-14.2 + roll, 10.2, wz + 0.2 + lift * 0.4), (1.8, 0.35, 1.4), "eel_fin", "tailfin", rot("c", -42.0) @ rot("b", -20.0), clip=under))
    # The head: its skull and long snout along the neck's end; the jaw hangs by the gape.
    H = spine[-1]
    ta, tc = tangent(n - 1)
    pitch = math.degrees(math.atan2(tc, ta)) * 0.35 + head_deg * 0.8
    hm = rot("b", pitch)
    skull_c, skull_r = H + hm @ v3(1.0, 0.0, 0.3), (3.8, 3.0, 2.7)
    P.add(E(skull_c, skull_r, "eel", "head", hm, skin, under), E(H + hm @ v3(4.6, 0.0, -0.2), (2.8, 2.1, 1.7), "eel", "head", hm, None, under))
    jm = hm @ rot("b", -gape * 38.0)
    hinge = H + hm @ v3(0.8, 0.0, -1.3)
    if gape > 0.2:
        P.add(E(hinge + hm @ rot("b", -gape * 19.0) @ v3(3.0, 0.0, -0.2), (2.6, 1.5, 0.8), "eel_mouth", "mouth", jm, clip=under, line=False))
        for t in (2.6, 3.8, 5.0):
            for s in (1, -1):
                P.mark(H + hm @ v3(t, s * 1.3, -1.7), M.EEL_TOOTH)
                P.mark(hinge + jm @ v3(t - 0.6, s * 1.1, 0.35), M.EEL_TOOTH)
    P.add(E(hinge + jm @ v3(3.4, 0.0, -0.5), (3.2, 1.9, 0.9), "eel_belly", "jaw", jm, clip=under))

    def on(c, r, m, u, v, out=0.2):
        cu, su = math.cos(math.radians(u)), math.sin(math.radians(u))
        cv, sv = math.cos(math.radians(v)), math.sin(math.radians(v))
        return c + m @ v3((r[0] + out) * cv * cu, (r[1] + out) * cv * su, (r[2] + out) * sv)

    for s in (1, -1):
        # An empty white eye in a dark socket (so it glows on the pale head), a cold halo round it that flares in the
        # tell; screwed shut when struck, dull when dead.
        for du, dv in ((-15.0, 0.0), (15.0, 0.0), (0.0, 16.0), (0.0, -16.0), (-12.0, 13.0), (12.0, -13.0)):
            P.mark(on(skull_c, skull_r, hm, s * (62.0 + du), 18.0 + dv), M.RAMPS["eel"][0])
        if eye in ("open", "wide"):
            P.mark(on(skull_c, skull_r, hm, s * 62.0, 18.0), M.HOLLOW_EYE)
            P.mark(on(skull_c, skull_r, hm, s * 60.0, 40.0), M.EYE_HALO)
            if eye == "wide":
                P.mark(on(skull_c, skull_r, hm, s * 52.0, 20.0), M.HOLLOW_EYE)
                for du, dv in ((-24.0, 34.0), (0.0, 44.0), (-30.0, 10.0)):
                    P.glow.append((on(skull_c, skull_r, hm, s * (62.0 + du), 18.0 + dv, 0.9), (0xE2, 0xF4, 0xEE, 150)))
        elif eye == "dead":
            P.mark(on(skull_c, skull_r, hm, s * 62.0, 18.0), M.RAMPS["eel"][2])
        for d in (6, 9, 12):   # gill slits behind the head
            i = max(0, n - 1 - d)
            P.mark(on(spine[i], (radius(i / (n - 1)),) * 3, np.eye(3), s * 80.0, 5.0), M.RAMPS["eel"][1])
    # Grey strands rising off its back and the loop behind, curling back as they rise, shedding motes.
    stir = {"idle": 0.5 * wave(action, f), "walk": 0.7 * wave(action, f)}.get(action, 0.6)
    roots = []
    for i in ((int(n * 0.3),) if action in ("attack", "death") else (int(n * 0.4), int(n * 0.62))):
        ta, tc = tangent(i)
        r = radius(i / (n - 1))
        roots.append(v3(spine[i][0] - tc * r, spine[i][1], spine[i][2] + ta * r))
    roots.append(v3(hump[6][0], hump[6][1], hump[6][2] + 2.6))
    fade = min(1.0, sink / 40.0)
    for j, b0 in enumerate(roots):
        if b0[2] < wz or fade >= 0.9:
            continue
        s = 1.0 if j % 2 else -1.0
        rise = (1.0, 0.8, 0.7)[j] * (0.45 if action in ("attack", "death") else 1.0) * (1.0 - fade)
        back = 1.0 if action in ("attack", "death") else 0.0
        wisp = _spline([b0, b0 + v3(-0.6 - back * 1.6, s * 0.4 + stir * 0.3, 2.8 * rise),
                        b0 + v3(-1.8 - back * 3.4, -s * 0.5 - stir * 0.3, 5.6 * rise),
                        b0 + v3(-1.6 - back * 5.2, s * 0.3 + stir * 0.5, 8.4 * rise),
                        b0 + v3(0.2 - back * 6.4, s * 0.9 + stir * 0.6, 9.6 * rise),
                        b0 + v3(1.4 - back * 6.8, s * 1.2 + stir * 0.6, 8.6 * rise)], 9)
        P.add(chain(wisp, 0.55, 0.3, "strand", "strand%d" % j, clip=under, line=False))
        if action in ("idle", "walk", "windup"):
            for m_ in range(2):
                u = (f * 0.37 + m_ * 0.5 + j * 0.21) % 1.0
                top = wisp[-1]
                P.fx.append((top + v3(-0.8 + m_ * 1.6, s * 0.6, 1.0 + u * 5.0), M.MOTE if m_ else M.MOTE_DIM))
    if action == "death":
        # Mist where it goes under: motes rising off the water, more as it sinks.
        for m_ in range(int(3 + sink / 10.0)):
            ang = math.radians(m_ * 53.0 + f * 29.0)
            rr = 2.5 + (m_ % 4) * 1.6
            P.fx.append((v3(math.cos(ang) * rr, math.sin(ang) * rr * 0.7, wz + 1.0 + (m_ % 5) * 1.3 + f * 0.6), M.MOTE if m_ % 2 else M.MOTE_DIM))
    # The water round it: the Hollow's dark stain, foam where the body and the loop break the surface, the rings
    # spreading from it (a step each frame) and, gliding, a wake behind the loop.
    k0 = next((i for i, q in enumerate(spine) if q[2] >= wz), 0)
    base_a, base_r = spine[k0][0], radius(k0 / (n - 1))
    ring = {"idle": 7.4 + f * 0.6, "walk": 7.8 + f * 0.45, "death": 7.4 + f * 0.55}.get(action, 8.4)
    breaks = [q for q in (hump[0], hump[-1]) if sink < 30]
    wake = action == "walk"
    la, lb = (loop[0][0] + roll, loop[0][1]), (loop[-1][0] + roll, loop[-1][1])

    def along(a, b):
        da, db = lb[0] - la[0], lb[1] - la[1]
        u = max(0.0, min(1.0, ((a - la[0]) * da + (b - la[1]) * db) / (da * da + db * db)))
        return math.hypot(a - la[0] - da * u, b - la[1] - db * u)

    def water(a, b):
        d0 = math.hypot(a - base_a, b)
        dh = min((math.hypot(a - q[0], b - q[1]) for q in breaks), default=99.0)
        if d0 < base_r + 1.1 and sink < 60:
            ang = int((math.degrees(math.atan2(b, a - base_a)) + 360.0) // 30.0)
            return M.FOAM if h01(ang, f, 17) > 0.25 else M.POOL
        if dh < 2.6:
            return M.FOAM
        if abs(d0 - ring) < 0.5 and d0 > base_r + 3.0:
            return M.RIPPLE
        if abs(d0 - ring + 3.8) < 0.45 and d0 > base_r + 3.0:
            return M.RIPPLE_DIM
        if wake and -14.0 + roll > a > -19.5:
            w = (-14.0 + roll - a) * 0.5 + 0.8
            if abs(abs(b - 10.0) - w) < 0.45:
                return M.RIPPLE_DIM
        if d0 < base_r + 3.2 or dh < 4.2 or (along(a, b) < 3.3 and sink < 30):
            return M.POOL
        return None

    P.water_fx = water
    return P
