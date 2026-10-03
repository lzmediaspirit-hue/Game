"""The long-bodied plan (audit 45 §6.2), from the hollowed eel (`eel`) and the marsh leech (`leech`): a body laid along
a spine, its radius a profile along it, posed by moving the spine.

  eel    a river serpent rising out of the water in an S-curve through key control points (taken from its side-view
         sheet), cut off at the surface; a torn dorsal fin, a loop of its back breaking the surface behind it, a long
         head with a hinged jaw of teeth, empty eyes in a halo; the Hollow's strands curling off its back shedding motes;
         the water round it (the stain, foam, rings, a wake). `awake` (decision 45, a boss's second phase): a crest of
         spines, burning eyes, twice the strands. Drawn at its size (creatures.Spec `sized`) against its water.
  leech  a flattened, ringed body on the ground that moves as a leech does: an inchworm's loop on land, a ribbon's wave
         in water (`swim`), its front half rearing in an S in the tell; a sucker mouth that flares into a cup, a rear
         sucker, eyespots, an elite's gold glow spots; the wet sheen on every ring.

The motion styles (STYLES): the eel's idle `sway`, walk `glide`, windup `rear_back`, attack `lunge_snap`, hurt
`snap_back`, death `sink`, its key poses written per frame as (control points, head tilt, gape, eyes, sunk); the leech's
idle `quest`, walk `inchworm`, swim `ribbon`, windup `rear_s`, attack `latch_drink`, hurt `ball_up`, death `writhe_flat`.
"""
from __future__ import annotations

import math

import numpy as np

from .. import mats as M
from ..motion import h01, smooth, wave
from ..sculpt import E, L, Pose, chain, rot, v3

# ================================================================================================= the eel
ELEV = math.radians(35.0)
# Key poses from its side-view sheet (tools/art/creatures/hollowed_eel.py): the spine's control points (x ahead, y down
# from the water, its art px; the first under the water).
POSES = {
    "idle": (((0, 8), (-6, -12), (8, -32), (20, -50), (12, -70), (24, -84)), ((0, 8), (-5, -12), (9, -32), (21, -50), (13, -70), (25, -83)),
             ((0, 8), (-4, -12), (10, -32), (21, -50), (14, -70), (26, -83)), ((0, 8), (-5, -12), (9, -32), (20, -50), (13, -70), (25, -84))),
    "wind": (((0, 8), (-4, -14), (10, -32), (16, -50), (6, -68), (14, -84)), ((0, 8), (-1, -16), (13, -32), (11, -50), (-2, -66), (2, -85)),
             ((0, 8), (0, -17), (14, -33), (9, -52), (-5, -68), (-2, -88))),
    "attack": (((0, 8), (-4, -14), (10, -30), (23, -44), (35, -54), (46, -60)), ((0, 8), (-2, -14), (13, -28), (28, -40), (42, -48), (54, -51)),
               ((0, 8), (-4, -13), (10, -30), (24, -46), (30, -64), (42, -74))),
    "hurt": (((0, 8), (-5, -12), (10, -32), (16, -50), (4, -68), (8, -86)), ((0, 8), (-6, -12), (9, -32), (18, -50), (9, -70), (18, -85))),
    "dead": (((0, 8), (-6, -12), (6, -30), (18, -44), (20, -60), (32, -66)), ((0, 8), (-6, -12), (6, -28), (18, -40), (24, -52), (36, -54))),
}


def _mix(a, b, t):
    return tuple((pa[0] + (pb[0] - pa[0]) * t, pa[1] + (pb[1] - pa[1]) * t) for pa, pb in zip(a, b))


def _ctrl(ref):
    """A key pose by name ("wind.0"), or ("mix", a, b, t): two eased between."""
    if isinstance(ref, str):
        name, _, i = ref.partition(".")
        return POSES[name][int(i)]
    return _mix(_ctrl(ref[1]), _ctrl(ref[2]), ref[3])


STYLES = {
    # the eel: `keys` a frame (control points, head tilt, gape, eyes, sunk); `cycle` eases round the idle keys
    "sway": {"cycle": ("idle.0", "idle.1", "idle.2", "idle.3"), "heads": (0, -2, -3, -1), "sway": (1.2, 0.0), "lift": (0.4, 0.0),
             "stir": 0.5, "motes": True, "ring": (7.4, 0.6)},
    "glide": {"poses": "idle.0", "sway": (0.6, 0.25), "lift": (0.7, 0.25), "stir": 0.7, "motes": True, "ring": (7.8, 0.45), "wake": True,
              "roll_amp": 1.6, "undulate": 1.7},
    "rear_back": {"poses": ((("mix", "idle.0", "wind.0", 0.55), 6, 0.3, "open", 0), ("wind.0", 12, 0.55, "wide", 0),
                           (("mix", "wind.0", "wind.1", 0.7), 22, 0.85, "wide", 0), ("wind.2", 32, 1.1, "wide", 0)), "motes": True},
    "lunge_snap": {"poses": (("attack.0", -6, 1.0, "wide", 0), ("attack.1", -12, 0.2, "wide", 0),
                            (("mix", "attack.1", "attack.2", 0.25), -10, 0.0, "open", 0), ("attack.2", -4, 0.4, "open", 0),
                            (("mix", "attack.2", "idle.0", 0.5), -2, 0.2, "open", 0), (("mix", "attack.2", "idle.0", 0.85), 0, 0.05, "open", 0)),
                   "ahead": 0.42, "drawn": True},
    "snap_back": {"poses": (("hurt.0", 26, 0.6, "squeeze", 0), ("hurt.1", 12, 0.3, "squeeze", 0),
                           (("mix", "hurt.1", "idle.0", 0.6), 4, 0.1, "open", 0))},
    "sink": {"poses": (("hurt.0", 22, 0.7, "squeeze", 0), ("dead.0", -24, 0.5, "dead", 8), (("mix", "dead.0", "dead.1", 0.5), -28, 0.45, "dead", 20),
                      ("dead.1", -32, 0.4, "dead", 32), ("dead.1", -34, 0.4, "dead", 44), ("dead.1", -36, 0.4, "dead", 58),
                      ("dead.1", -36, 0.4, "dead", 74), ("dead.1", -36, 0.4, "dead", 92)),
             "ahead": 0.38, "drawn": True, "mist": True, "ring": (7.4, 0.55)},
    # the leech: REAR (0..1), GAPE, LUNGE, LENGTH, SPAN (below 1 the middle loops), DRINK, WRITHE, CURL, FLAT
    "quest": {"gape": (0.05, 0.1, 0.2, 0.1, 0.05, 0.0), "quest": (0.0, 0.6, 1.0, 0.4, -0.6, -1.0), "breathe": 0.12},
    "inchworm": {"kind": "inchworm"},
    "ribbon": {"kind": "ribbon"},
    "rear_s": {"rear": (0.25, 0.6, 0.9, 1.0), "gape": (0.35, 0.65, 0.95, 1.0), "lunge": (-0.4, -0.9, -1.3, -1.5),
               "length": (0.97, 0.94, 0.92, 0.92)},
    "latch_drink": {"rear": (0.35, 0.0, 0.0, 0.0, 0.1, 0.1), "gape": (1.0, 0.75, 0.7, 0.7, 0.5, 0.15), "lunge": (5.0, 6.2, 6.0, 5.4, 3.6, 1.2),
                    "length": (1.18, 0.9, 0.94, 0.9, 0.96, 1.0), "span": (1.0, 0.86, 0.9, 0.84, 0.94, 1.0),
                    "drink": (0.0, 0.1, 0.22, 0.3, 0.2, 0.08), "glints": (1, 2)},
    "ball_up": {"rear": (0.3, 0.1, 0.0), "gape": (0.0, 0.2, 0.1), "lunge": (-2.2, -1.4, -0.5), "length": (0.62, 0.78, 0.92),
                "span": (1.0, 1.0, 1.0), "writhe": (0.5, -0.3, 0.0)},
    "writhe_flat": {"rear": (0.5, 0.15, 0.3, 0.0, 0.0, 0.0, 0.0, 0.0), "gape": (0.8, 0.3, 0.6, 0.2, 0.1, 0.0, 0.0, 0.0),
                    "lunge": (-0.6, -0.8, -0.8, -0.8, -0.8, -0.8, -0.8, -0.8), "length": (1.05, 0.9, 1.0, 0.95, 0.92, 0.9, 0.9, 0.9),
                    "writhe": (1.0, -1.0, 0.8, -0.6, 0.3, 0.0, 0.0, 0.0), "curl": (0.0, 0.2, 0.45, 0.8, 1.0, 0.95, 0.85, 0.8),
                    "flat": (0.0, 0.0, 0.0, 0.1, 0.25, 0.4, 0.5, 0.55)},
}

EEL = {
    "lift": 20.0,                    # the game hovers it this far over the water (art px): its water is drawn under its feet
    "ahead": 0.5, "up": 0.55,        # the side view's art px to the figure's, ahead and up
    "s": (0.0, 2.6, -1.8, 2.2, -0.9, 0.3),   # its S-curve sideways too, so it winds from every side, not a pillar
    "n": 56, "profile": ((0.0, 4.8), (0.3, 4.4), (0.6, 3.9), (0.85, 3.4), (1.0, 3.2)),
    "fin": (1.4, 2.2, 1.0, 2.4, 1.6, 0.8, 2.0, 1.4, 2.2, 1.0, 1.8, 1.2),   # the torn dorsal fin's plates
    "loop": ((-5.6, 2.0), (-7.4, 3.8, 2.4), (-9.4, 5.6, 3.4), (-11.2, 7.2, 1.4), (-12.6, 8.6)),
    "skull": ((1.0, 0.0, 0.3), (3.8, 3.0, 2.7)), "snout": ((4.6, 0.0, -0.2), (2.8, 2.1, 1.7)),
}
LEECH = {
    "rest": 19.0,          # its length at rest, rear sucker to lip (art px at size 1)
    "ring": 2.0,           # a ring's length along it
    "sheen": (0.9, 0.97),  # N.H thresholds: the sheen and the glint on each ring (sculpt.Part.sheen)
    # The body's half-width along it, tail (0) to head (1); its half-depth is `depth` of that (a leech is flat).
    "width": ((0.0, 1.05), (0.1, 1.9), (0.3, 2.55), (0.55, 2.35), (0.78, 1.7), (0.92, 1.2), (1.0, 0.95)),
    "depth": 0.56,
}
VARIANTS = {
    "eel": {"parts": EEL, "mats": {"skin": "eel", "belly": "eel_belly", "fin": "eel_fin", "mouth": "eel_mouth"},
            "motion": {"idle": "sway", "walk": "glide", "windup": "rear_back", "attack": "lunge_snap", "hurt": "snap_back",
                       "death": "sink"}},
    "leech": {"parts": LEECH, "mats": {"skin": "leech", "dark": "leech_dark", "belly": "leech_belly", "lip": "leech_lip", "maw": "leech_maw"},
              "motion": {"idle": "quest", "walk": "inchworm", "swim": "ribbon", "windup": "rear_s", "attack": "latch_drink",
                         "hurt": "ball_up", "death": "writhe_flat"}},
}


def pose(B, action: str, f: int, k: float = 1.44, awake: bool = False, view: float = 90.0) -> Pose:
    if B.variant == "leech" or "rest" in B.parts:
        return _leech(B, action, f, view)
    return _eel(B, action, f, k, awake)


def _key(B, action: str, f: int):
    """(control points, head tilt, gape, eyes, sunk) for a frame, the key poses eased between for the frames between."""
    st = B.style(action)
    if "cycle" in st:
        cyc, heads = st.cycle, st.heads
        n = len(cyc)
        u = f / 6.0 * n
        i, t = int(u) % n, u - int(u)
        return _mix(_ctrl(cyc[i]), _ctrl(cyc[(i + 1) % n]), t), heads[i] + (heads[(i + 1) % n] - heads[i]) * t, 0.05 * (i == 2), "open", 0
    if isinstance(st.poses, str):
        return _ctrl(st.poses), -1.0 - wave(action, f), 0.0, "open", 0
    ref, head, gape, eye, sink = st.poses[f]
    return _ctrl(ref), head, gape, eye, sink


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


def _eel(B, action: str, f: int, k: float, awake: bool) -> Pose:
    p, m = B.parts, B.mats
    st = B.style(action)
    P = Pose()
    P.water = -p.lift / math.cos(ELEV)            # in the world, at its drawn size
    wz = P.water / k                              # in its own frame
    ctrl, head_deg, gape, eye, sink = _key(B, action, f)
    sway = st.sway[0] * wave(action, f, st.sway[1]) if "sway" in st else 0.0
    ahead = st.get("ahead", p.ahead)
    pts = [v3(x * ahead, p.s[i] + sway * (i / 5.0) ** 2, wz - (y + sink) * p.up) for i, (x, y) in enumerate(ctrl)]
    spine = _spline(pts, p.n)
    if "undulate" in st:   # a wave rolls up the body
        ph = f / 8.0 * math.tau
        out = []
        for i, q in enumerate(spine):
            t = i / (len(spine) - 1)
            nxt, prv = spine[min(i + 1, len(spine) - 1)], spine[max(i - 1, 0)]
            ta, tc = nxt[0] - prv[0], nxt[2] - prv[2]
            ln = math.hypot(ta, tc) or 1.0
            s = st.undulate * math.sin(ph - t * 6.0) * min(1.0, t * 3.0) * (1.0 - t * 0.4)
            out.append(v3(q[0] - tc / ln * s, q[1], q[2] + ta / ln * s))
        spine = out
    n = len(spine)
    under = lambda q: q[:, 2] > wz               # cut off at the water's surface
    prof = p.profile

    def radius(t):
        for (t0, r0), (t1, r1) in zip(prof, prof[1:]):
            if t <= t1:
                return r0 + (r1 - r0) * (t - t0) / (t1 - t0)
        return prof[-1][1]

    def skin(q, nn):
        """The pale belly down its front and underneath; faint scale rows (a step lit every other row) on the grey."""
        belly = (nn[:, 0] > 0.5) | (nn[:, 2] < -0.6)
        rows = (np.floor(q[:, 2] * 0.8) + np.floor(q[:, 1] * 0.8)) % 2 == 0
        return np.where(belly, m.belly, m.skin).astype(object), np.where(rows & ~belly & (nn[:, 2] > 0.1), 1, 0).astype(np.int16)

    def tangent(i):
        a, b = spine[max(i - 3, 0)], spine[min(i + 3, n - 1)]
        ta, tc = b[0] - a[0], b[2] - a[2]
        ln = math.hypot(ta, tc) or 1.0
        return ta / ln, tc / ln

    for i in range(0, n - 1, 2):
        r0, r1 = radius(i / (n - 1)), radius(min(n - 1, i + 2) / (n - 1))
        P.add(L(spine[i], spine[min(n - 1, i + 2)], r0, r1, m.skin, "body", skin, under))
    # The torn dorsal fin along its back (the side away from the belly), fluttering; awake, a crest of spines.
    for j, i in enumerate(range(10, n - 8, 3)):
        ta, tc = tangent(i)
        da, dc = -tc, ta
        h = p.fin[j % len(p.fin)] * (1.7 if awake else 1.0) + 0.35 * math.sin(f * 1.7 + j)
        r = radius(i / (n - 1))
        q = spine[i]
        if q[2] < wz:
            continue
        mm = np.array(((ta, 0.0, da), (0.0, 1.0, 0.0), (tc, 0.0, dc)))
        P.add(E(v3(q[0] + da * (r + h * 0.5 - 0.5), q[1], q[2] + dc * (r + h * 0.5 - 0.5)), (1.5, 0.45, h * 0.95), m.fin, "fin", mm,
                clip=under, line=False))
    # A loop of its back breaking the surface behind it, a fin tip beyond; it rolls back along the body as it glides.
    roll = st.roll_amp * math.sin(f / 8.0 * math.tau) if "roll_amp" in st else 0.0
    lift = (st.lift[0] * wave(action, f, st.lift[1]) if "lift" in st else 0.0) - sink * p.up
    low = -2.6 - sink * p.up
    lp = p.loop
    loop = ((lp[0][0], lp[0][1], low), (lp[1][0], lp[1][1], lp[1][2] + lift), (lp[2][0], lp[2][1], lp[2][2] + lift),
            (lp[3][0], lp[3][1], lp[3][2] + lift * 0.5), (lp[4][0], lp[4][1], low))
    hump = _spline([v3(a + roll, b, wz + c_) for a, b, c_ in loop], 12)
    for i in range(len(hump) - 1):
        P.add(L(hump[i], hump[i + 1], 3.0 - 0.5 * i / 11.0, 3.0 - 0.5 * (i + 1) / 11.0, m.skin, "hump", skin, under))
    for i in (4, 6, 8):
        q = hump[i]
        P.add(E(v3(q[0], q[1], q[2] + 3.0), (1.0, 0.35, 0.9 + 0.3 * (i % 3)), m.fin, "hump_fin", rot("c", -42.0), clip=under, line=False))
    P.add(E(v3(-14.2 + roll, 10.2, wz + 0.2 + lift * 0.4), (1.8, 0.35, 1.4), m.fin, "tailfin", rot("c", -42.0) @ rot("b", -20.0), clip=under))
    # The head: its skull and long snout along the neck's end; the jaw hangs by the gape.
    H = spine[-1]
    ta, tc = tangent(n - 1)
    pitch = math.degrees(math.atan2(tc, ta)) * 0.35 + head_deg * 0.8
    hm = rot("b", pitch)
    skull_c, skull_r = H + hm @ v3(p.skull[0]), p.skull[1]
    P.add(E(skull_c, skull_r, m.skin, "head", hm, skin, under), E(H + hm @ v3(p.snout[0]), p.snout[1], m.skin, "head", hm, None, under))
    jm = hm @ rot("b", -gape * 38.0)
    hinge = H + hm @ v3(0.8, 0.0, -1.3)
    if gape > 0.2:
        P.add(E(hinge + hm @ rot("b", -gape * 19.0) @ v3(3.0, 0.0, -0.2), (2.6, 1.5, 0.8), m.mouth, "mouth", jm, clip=under, line=False))
        for t in (2.6, 3.8, 5.0):
            for s in (1, -1):
                P.mark(H + hm @ v3(t, s * 1.3, -1.7), M.EEL_TOOTH)
                P.mark(hinge + jm @ v3(t - 0.6, s * 1.1, 0.35), M.EEL_TOOTH)
    P.add(E(hinge + jm @ v3(3.4, 0.0, -0.5), (3.2, 1.9, 0.9), m.belly, "jaw", jm, clip=under))

    def on(c, r, mm, u, v, out=0.2):
        cu, su = math.cos(math.radians(u)), math.sin(math.radians(u))
        cv, sv = math.cos(math.radians(v)), math.sin(math.radians(v))
        return c + mm @ v3((r[0] + out) * cv * cu, (r[1] + out) * cv * su, (r[2] + out) * sv)

    for s in (1, -1):
        # An empty white eye in a dark socket (so it glows on the pale head), a cold halo round it that flares in the
        # tell; screwed shut when struck, dull when dead.
        for du, dv in ((-15.0, 0.0), (15.0, 0.0), (0.0, 16.0), (0.0, -16.0), (-12.0, 13.0), (12.0, -13.0)):
            P.mark(on(skull_c, skull_r, hm, s * (62.0 + du), 18.0 + dv), M.RAMPS[m.skin][0])
        eye_c, halo_c = (M.WAKE_EYE, M.WAKE_HALO) if awake else (M.HOLLOW_EYE, M.EYE_HALO)
        if eye in ("open", "wide"):
            P.mark(on(skull_c, skull_r, hm, s * 62.0, 18.0), eye_c)
            P.mark(on(skull_c, skull_r, hm, s * 60.0, 40.0), halo_c)
            if eye == "wide" or awake:
                P.mark(on(skull_c, skull_r, hm, s * 52.0, 20.0), eye_c)
                for du, dv in ((-24.0, 34.0), (0.0, 44.0), (-30.0, 10.0)):
                    P.glow.append((on(skull_c, skull_r, hm, s * (62.0 + du), 18.0 + dv, 0.9), (0xFF, 0x7A, 0x60, 170) if awake else (0xE2, 0xF4, 0xEE, 150)))
        elif eye == "dead":
            P.mark(on(skull_c, skull_r, hm, s * 62.0, 18.0), M.RAMPS[m.skin][2])
        for d in (6, 9, 12):   # gill slits behind the head
            i = max(0, n - 1 - d)
            P.mark(on(spine[i], (radius(i / (n - 1)),) * 3, np.eye(3), s * 80.0, 5.0), M.RAMPS[m.skin][1])
    # Grey strands rising off its back and the loop behind, curling back as they rise, shedding motes.
    stir = st.stir * wave(action, f) if "stir" in st else 0.6
    drawn = st.get("drawn", False)
    roots = []
    at_ = (0.3,) if drawn else (0.4, 0.62)
    if awake:
        at_ = (0.22, 0.42) if drawn else (0.28, 0.46, 0.64, 0.8)
    for i in [int(n * a_) for a_ in at_]:
        ta, tc = tangent(i)
        r = radius(i / (n - 1))
        roots.append(v3(spine[i][0] - tc * r, spine[i][1], spine[i][2] + ta * r))
    roots.append(v3(hump[6][0], hump[6][1], hump[6][2] + 2.6))
    fade = min(1.0, sink / 40.0)
    for j, b0 in enumerate(roots):
        if b0[2] < wz or fade >= 0.9:
            continue
        s = 1.0 if j % 2 else -1.0
        rise = (1.0, 0.8, 0.7, 0.9, 0.75, 0.85)[j % 6] * (0.45 if drawn else 1.0) * (1.0 - fade) * (1.25 if awake else 1.0)
        back = 1.0 if drawn else 0.0
        wisp = _spline([b0, b0 + v3(-0.6 - back * 1.6, s * 0.4 + stir * 0.3, 2.8 * rise),
                        b0 + v3(-1.8 - back * 3.4, -s * 0.5 - stir * 0.3, 5.6 * rise),
                        b0 + v3(-1.6 - back * 5.2, s * 0.3 + stir * 0.5, 8.4 * rise),
                        b0 + v3(0.2 - back * 6.4, s * 0.9 + stir * 0.6, 9.6 * rise),
                        b0 + v3(1.4 - back * 6.8, s * 1.2 + stir * 0.6, 8.6 * rise)], 9)
        P.add(chain(wisp, 0.55, 0.3, "strand", "strand%d" % j, clip=under, line=False))
        if st.get("motes"):
            for m_ in range(2):
                u = (f * 0.37 + m_ * 0.5 + j * 0.21) % 1.0
                top = wisp[-1]
                P.fx.append((top + v3(-0.8 + m_ * 1.6, s * 0.6, 1.0 + u * 5.0), M.MOTE if m_ else M.MOTE_DIM))
    if st.get("mist"):
        # Mist where it goes under: motes rising off the water, more as it sinks.
        for m_ in range(int(3 + sink / 10.0)):
            ang = math.radians(m_ * 53.0 + f * 29.0)
            rr = 2.5 + (m_ % 4) * 1.6
            P.fx.append((v3(math.cos(ang) * rr, math.sin(ang) * rr * 0.7, wz + 1.0 + (m_ % 5) * 1.3 + f * 0.6), M.MOTE if m_ % 2 else M.MOTE_DIM))
    # The water round it: the Hollow's dark stain, foam where the body and the loop break the surface, the rings
    # spreading from it (a step each frame) and, gliding, a wake behind the loop.
    k0 = next((i for i, q in enumerate(spine) if q[2] >= wz), 0)
    base_a, base_r = spine[k0][0], radius(k0 / (n - 1))
    ring = st.ring[0] + f * st.ring[1] if "ring" in st else 8.4
    breaks = [q for q in (hump[0], hump[-1]) if sink < 30]
    wake = st.get("wake", False)
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


# ================================================================================================= the leech
def _width(W, u: float) -> float:
    for (u0, w0), (u1, w1) in zip(W, W[1:]):
        if u <= u1:
            t = (u - u0) / (u1 - u0)
            return w0 + (w1 - w0) * (t * t * (3 - 2 * t))
    return W[-1][1]


def _resample(pts: np.ndarray, n: int) -> tuple:
    """Points along the polyline `pts` at n even steps of its length, and the length."""
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    total = float(cum[-1])
    out = []
    for s in np.linspace(0.0, total, n):
        k = min(len(seg) - 1, int(np.searchsorted(cum, s, side="right") - 1))
        t = (s - cum[k]) / max(1e-9, seg[k])
        out.append(pts[k] + (pts[k + 1] - pts[k]) * t)
    return np.array(out), total


def _walk_ends(f: int) -> tuple:
    """The inchworm's ends over the walk (the sheet's origin travels on at the walk's rate, so a planted sucker slides
    back at it): the rear holds while the front reaches out and plants, then the front holds while the rear is drawn
    up. One cycle carries it 8 art px (the species' cycle)."""
    t = f / 8.0
    half, lc = 4.0, 9.6                 # a planted end slides back 4 a half cycle; the ends 9.6 apart drawn up
    if t < 0.5:
        u = t / 0.5
        rear = -lc / 2 - half * u
        front = lc / 2 + half * smooth(u)
        lift_f, lift_r = math.sin(u * math.pi) * 0.9, 0.0
    else:
        u = (t - 0.5) / 0.5
        front = lc / 2 + half - half * u
        rear = -lc / 2 - half + half * smooth(u)
        lift_f, lift_r = 0.0, math.sin(u * math.pi) * 0.7
    return rear, front, lift_r, lift_f


def _leech(B, action: str, f: int, view: float) -> Pose:
    p, m = B.parts, B.mats
    st = B.style(action)
    REST, W = p.rest, p.width
    P = Pose()
    rear_up = B.pick("rear", action, f)
    gape = B.pick("gape", action, f)
    lunge = B.pick("lunge", action, f)
    length = B.pick("length", action, f, 1.0)
    span = B.pick("span", action, f, 1.0)
    drink = B.pick("drink", action, f)
    writhe = B.pick("writhe", action, f)
    curl = B.pick("curl", action, f)
    flat = B.pick("flat", action, f)
    swim = st.get("kind") == "ribbon"
    # Where the camera is in its own frame (a forward, b left): its reared head turns a little toward it.
    y = math.radians(view)
    cam_b = -math.cos(y)
    headon = abs(math.sin(y))          # 1 facing the camera or away from it, where a sideways wind is what reads
    fronton = max(0.0, math.sin(y))    # 1 facing the camera: its reared front stands up in a column, the cup toward it
    ph = f / 8.0 * math.tau

    # --- the spine: a polyline tail (index 0) to lip, laid out per action, then resampled evenly along its length.
    K = 48
    u = np.linspace(0.0, 1.0, K)
    arc = REST * length
    lift_r = lift_f = 0.0
    if st.get("kind") == "inchworm":
        rear, front, lift_r, lift_f = _walk_ends(f)
        d = front - rear
        arc = max(d + 0.4, 16.4 + (d - 9.6) / 8.0 * 4.0)     # it lengthens as it stretches (16.4 drawn up, 20.4 out)
    elif swim:
        rear, front = -arc * 0.5, arc * 0.5
        d = arc * 0.94
    else:
        d = arc * span
        rear, front = -d * 0.5 + lunge * 0.35, d * 0.5 + lunge
        d = front - rear
        arc = max(arc, d)
    a = rear + (front - rear) * u
    b = np.zeros(K)
    c = np.zeros(K)
    # The loop: where the ends are nearer than the body is long, its middle rises in a loop the body's length, its two
    # ends flat on the ground by the suckers.
    if arc > d + 0.05:
        bump = np.sin(np.pi * np.clip((u - 0.1) / 0.8, 0.0, 1.0)) ** 2
        lo, hi = 0.0, arc
        for _ in range(24):
            h = 0.5 * (lo + hi)
            pl = np.stack([a, b, c + h * bump], axis=1)
            if float(np.linalg.norm(np.diff(pl, axis=0), axis=1).sum()) > arc:
                hi = h
            else:
                lo = h
        c += lo * bump
        b += 0.5 * headon * lo * bump          # the loop leans a little to its side, so it shows from the front or behind
    c += lift_r * np.clip(1.0 - u / 0.2, 0.0, 1.0) + lift_f * np.clip((u - 0.8) / 0.2, 0.0, 1.0)
    if "quest" in st:
        # Holding by its rear sucker, head lifted and questing side to side; a slow swell runs down it as it breathes.
        quest = st.quest[f]
        fr = np.clip((u - 0.62) / 0.38, 0.0, 1.0) ** 2
        c += fr * (0.9 + 0.4 * abs(quest))
        b += fr * 2.8 * quest
    if swim:
        # A ribbon in the water: a wave running tailward, mostly up and down (a leech swims so) and a little sideways.
        wv = np.sin(2 * math.pi * 1.1 * u + ph)
        c += 0.6 + 0.9 * wv * (0.35 + 0.65 * (1 - u))
        b += 1.2 * np.sin(2 * math.pi * 0.9 * u + ph + 1.2) * (0.3 + 0.7 * (1 - u))
    if rear_up > 0.0:
        # The S: the hind half stays on the ground, the front half rises (up, then its head bent forward over its prey),
        # and it winds sideways too, one way low and the other high, so the S reads from every side.
        v = np.clip((u - 0.38) / 0.62, 0.0, 1.0)
        end = math.radians(58.0) * fronton
        th = rear_up * np.where(v < 0.45, math.radians(90.0) * np.sin(0.5 * np.pi * v / 0.45),
                                math.radians(90.0) + (end - math.radians(90.0)) * (v - 0.45) / 0.55)
        k0 = int(np.searchsorted(u, 0.38))
        for k in range(max(1, k0), K):
            ds = (u[k] - u[k - 1]) * arc
            a[k] = a[k - 1] + math.cos(th[k]) * ds
            c[k] = c[k - 1] + math.sin(th[k]) * ds
        side = 1.0 if cam_b >= 0 else -1.0
        wind = 1.0 + 0.7 * headon
        b += rear_up * wind * (-2.6 * np.sin(np.pi * np.clip(u / 0.5, 0, 1)) + 3.0 * side * np.sin(np.pi * v) * (0.4 + 0.6 * v))
    if writhe:
        b += writhe * 2.6 * np.sin(u * math.pi * 1.7 + f * 0.9)
    if curl:
        # Curling up on its side: the front bends round toward the tail (a C, then nearly a ring).
        ang = curl * math.radians(250.0) * u ** 1.2
        hd = np.zeros((K, 2))
        for k in range(1, K):
            ds = (u[k] - u[k - 1]) * arc
            hd[k] = hd[k - 1] + ds * np.array((math.cos(ang[k]), math.sin(ang[k])))
        hd -= hd.mean(axis=0)
        a = a * (1 - curl) + (hd[:, 0] + lunge) * curl
        b = b * (1 - curl) + hd[:, 1] * curl
    pts, total = _resample(np.stack([a, b, c], axis=1), 34)

    # --- the body: flattened ellipsoids along it, overlapping into one form; rings, flank and belly painted by the
    # length along it, so they stay on it as it loops and rears.
    thick = math.sqrt(REST / max(8.0, total)) * (1.0 + st.get("breathe", 0.0) * math.sin(ph))
    depth = p.depth * (1.0 - 0.45 * flat) * (0.72 if swim else 1.0)
    wide = 1.0 + 0.3 * flat + (0.12 if swim else 0.0)
    n = len(pts)
    T = np.gradient(pts, axis=0)
    T /= np.linalg.norm(T, axis=1)[:, None]
    up = np.array((0.0, 0.0, 1.0))
    prevB = np.array((0.0, 1.0, 0.0))
    frames = []
    for k in range(n):
        Bk = np.cross(up, T[k])
        if np.linalg.norm(Bk) < 0.2:
            Bk = prevB
        Bk /= np.linalg.norm(Bk)
        prevB = Bk
        N = np.cross(T[k], Bk)
        frames.append((T[k], Bk, N))
    for k in range(n):
        s = k / (n - 1)
        w = _width(W, s) * thick * wide * (1.0 + drink * (1.0 - s) * 1.1 * (s > 0.15))
        hh = max(0.55, w * depth * (1.0 + drink * 0.6 * (1.0 - s)))
        Tk, Bk, Nk = frames[k]
        # The body lies on the ground: its underside at the spine's height, not under the ground.
        centre = pts[k] + np.array((0.0, 0.0, hh))
        mm = np.stack([Tk, Bk, Nk], axis=1)
        sk = s * total
        P.add(E(centre, (max(0.62 * total / (n - 1) + 0.35, 0.7), w, hh), m.skin, "body", mm,
                _ringed(m, p.ring, centre, Tk, Bk, Nk, w, sk), sheen=p.sheen))
        # Paired spots down its back, three pairs (drawn on an elite only, in gold: its glow spots).
        if 0.2 < s < 0.8 and k % 6 == 3 and not swim:
            for sd in (1, -1):
                P.eye(centre + Bk * (sd * w * 0.42) + Nk * (hh + 0.25), None)
    # --- the rear sucker: a small disc under its tail, planted.
    T0, B0, N0 = frames[0]
    tail = pts[0] + np.array((0.0, 0.0, 0.45)) - T0 * 1.0
    disc_m = np.stack([T0, B0, N0], axis=1) if swim else np.eye(3)
    P.add(E(tail, (1.7 * thick, 1.7 * thick, 0.45), m.dark, "sucker", disc_m, _disc(m, tail, 1.7 * thick), sheen=p.sheen))
    # --- the head: eyespots on its crown, and the sucker mouth.
    Tn, Bn, Nn = frames[-1]
    wn = _width(W, 1.0) * thick
    headc = pts[-1] + np.array((0.0, 0.0, max(0.55, wn * depth)))
    for sd in (1, -1):
        P.eye(pts[-3] + np.array((0.0, 0.0, max(0.55, _width(W, 0.94) * thick * depth))) + Bn * sd * 0.55 + Nn * 0.45, M.LEECH_EYE)
    # The cup faces along the head, a little up at its prey in the tell and turned toward the camera in the side views.
    face = Tn + np.array((0.0, 0.0, 0.2 * rear_up))
    if rear_up > 0.3:
        face = face + np.array((0.0, cam_b, 0.0)) * 0.8 * rear_up
    face /= np.linalg.norm(face)
    fb = np.cross(np.array((0.0, 0.0, 1.0)), face)
    fb = fb / np.linalg.norm(fb) if np.linalg.norm(fb) > 0.2 else Bn
    fn = np.cross(face, fb)
    cm = np.stack([face, fb, fn], axis=1)
    R = 1.2 + 1.6 * gape
    lip = headc + face * (0.45 + 0.35 * gape)
    P.add(E(lip, (0.5 + 0.2 * gape, R, R * 0.92), m.lip, "mouth", cm))
    if gape > 0.25:
        maw = lip + face * (0.45 + 0.2 * gape)
        P.add(E(maw, (0.25, R * 0.64, R * 0.58), m.maw, "maw", cm, line=False))
        # Tiny teeth round the rim of the maw, muted so the cup reads as a mouth and not an eye.
        for i in range(6 if gape > 0.6 else 3):
            q = math.radians(90.0 + i * (60.0 if gape > 0.6 else 120.0))
            P.mark(maw + face * 0.2 + fb * math.cos(q) * R * 0.5 + fn * math.sin(q) * R * 0.46, M.LEECH_TOOTH)
    else:
        P.mark(lip + face * 0.55, M.RAMPS[m.maw][1])
    # The bite's glints as it latches, and the water a swimmer stirs.
    if f in st.get("glints", ()):
        for dd in ((1.6, 0.6, 0.8), (1.9, -0.7, 1.4), (2.2, 0.2, 2.0)):
            P.glow.append((lip + v3(*dd), M.GLINT))
    if swim:
        for k in range(6):
            s = k / 5.0
            at = pts[int(s * (n - 1))]
            wv = math.sin(ph + k * 1.3)
            for sd in (1, -1):
                P.fx.append((at + v3(0.0, sd * (2.9 + 0.5 * wv + 0.6 * (1 - s)), 0.05), M.SPLASH if (k + f) % 3 else M.SPLASH_DIM))
        for k in range(3):
            P.fx.append((pts[0] + v3(-1.8 - k * 1.2, (k - 1) * 1.1 + 0.4 * math.sin(ph + k), 0.05), M.SPLASH_DIM))
    return P


def _disc(m, centre, r: float):
    """The rear sucker: its rim a step lit round a darker middle, so it reads as a disc."""
    def disc(q, nrm):
        rim = np.linalg.norm((q - centre)[:, :2], axis=1) > r * 0.62
        return np.full(len(q), m.dark, dtype=object), np.where(rim, 1, -1).astype(np.int16)
    return disc


def _ringed(m, ring: float, centre, T, B, N, w: float, s0: float):
    """A ring of the body's paint: the length along it `s0` at `centre`. A groove a step dark every `ring` (two on its
    back, where it cuts the sheen) with a lit ridge behind it; the back dark olive, the flanks going to black; the belly
    paler and banded by the same grooves."""
    def skin(q, nrm):
        d = q - centre
        s = s0 + d @ T
        lat = np.abs(d @ B) / max(0.3, w)
        nz = nrm @ N
        ph = (s / ring) % 1.0
        groove = ph < 0.3
        ridge = (ph >= 0.3) & (ph < 0.6) & (nz > 0.55)
        belly = nz < -0.28
        flank = (lat > 0.6) | (nz < 0.25)
        names = np.where(belly, m.belly, np.where(flank, m.dark, m.skin)).astype(object)
        # The groove cuts through the sheen on its back, so the glint breaks ring by ring.
        bias = np.where(groove, np.where(nz > 0.6, -2, -1), np.where(ridge & ~belly, 1, 0)).astype(np.int16)
        return names, bias
    return skin
