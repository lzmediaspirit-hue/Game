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

  viper  (M1, the green viper) a slender snake: its hind body coiled flat on the ground, its neck raised in an S, a
         wedge of a head (a brow scale, gold slit eyes, fangs, a forked tongue); green with faint crossbands, a pale
         belly and flank stripe, an orange tail tip; it side-winds, draws back into a tight S (the tell), strikes along
         the ground, recoils, goes limp and rolls onto its back. Styles: idle `coiled`, walk `sidewind`, windup `draw_s`,
         attack `strike`, hurt `recoil`, death `go_limp`; channels `neck` (rise, bend back, reach, head height), `lunge`,
         `gape`, `hpitch`, `writhe`, `limp`, `roll`.

The motion styles (STYLES): the eel's idle `sway`, walk `glide`, windup `rear_back`, attack `lunge_snap`, hurt
`snap_back`, death `sink`, its key poses written per frame as (control points, head tilt, gape, eyes, sunk); the leech's
idle `quest`, walk `inchworm`, swim `ribbon`, windup `rear_s`, attack `latch_drink`, hurt `ball_up`, death `writhe_flat`.
"""
from __future__ import annotations

import math

import numpy as np

from .. import mats as M
from ..motion import h01, h01v, smooth, wave
from ..sculpt import E, L, Pose, S, chain, rot, v3

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

VIPER_STYLES = {
    "coiled": {"neck": ((4.6, 1.4, 3.6, 4.4), (4.7, 1.5, 3.5, 4.5), (4.8, 1.6, 3.5, 4.6), (4.7, 1.5, 3.6, 4.5), (4.6, 1.4, 3.7, 4.4),
                        (4.5, 1.3, 3.7, 4.3)), "sway": 0.7, "tongue": (1, 4)},
    "sidewind": {"kind": "wind", "tongue": (3,)},
    "draw_s": {"neck": ((5.0, 1.9, 2.8, 4.8), (5.4, 2.5, 2.0, 5.3), (5.6, 2.9, 1.5, 5.6), (5.7, 3.0, 1.4, 5.7)),
               "gape": (0.15, 0.35, 0.55, 0.7), "hpitch": (4.0, 8.0, 10.0, 10.0), "lunge": (-0.3, -0.6, -0.8, -0.9)},
    "strike": {"neck": ((4.2, 0.4, 6.4, 3.4), (2.8, -0.6, 9.4, 1.9), (2.8, -0.4, 9.0, 2.0), (3.6, 0.4, 6.6, 3.1), (4.3, 1.1, 4.6, 4.0),
                        (4.6, 1.4, 3.8, 4.4)),
               "lunge": (0.6, 1.6, 1.4, 0.8, 0.3, 0.0), "gape": (1.0, 0.9, 0.5, 0.2, 0.1, 0.0), "hpitch": (0.0, -8.0, -6.0, -2.0, 0.0, 0.0),
               "streaks": (0, 1)},
    "recoil": {"neck": ((5.2, 2.8, 1.4, 5.6), (4.9, 2.1, 2.4, 5.0), (4.7, 1.6, 3.2, 4.6)), "hpitch": (18.0, 8.0, 2.0),
               "gape": (0.5, 0.2, 0.0), "writhe": (0.7, -0.3, 0.0)},
    "go_limp": {"neck": ((5.0, 2.4, 2.0, 5.2),) + ((4.6, 1.4, 3.6, 4.4),) * 7, "limp": (0.0, 0.2, 0.45, 0.7, 0.9, 1.0, 1.0, 1.0),
                "roll": (0.0, 0.0, 0.0, 0.0, 40.0, 110.0, 150.0, 165.0), "writhe": (0.9, -0.6, 0.4, -0.2, 0.0, 0.0, 0.0, 0.0),
                "gape": (0.6, 0.4, 0.3, 0.2, 0.2, 0.2, 0.2, 0.2), "dead_from": 3},
}
STYLES.update(VIPER_STYLES)
VIPER = {
    "length": 24.0, "coil_share": 0.62, "coil_r": 4.2, "neck_rest": (4.6, 1.4, 3.6, 4.4), "tip": 0.1,
    "width": ((0.0, 0.2), (0.15, 0.6), (0.45, 1.0), (0.7, 0.9), (0.88, 0.62), (1.0, 0.7)),
    "head": {"skull": (2.0, 1.45, 1.0), "snout": ((1.4, 0.0, -0.2), (1.2, 0.95, 0.7)), "brow": (0.6, 0.9, 0.7), "eye": (0.9, 1.15, 0.45)},
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
    "viper": {"parts": VIPER, "mats": {"skin": "viper_scale", "belly": "viper_belly", "tip": "viper_tail", "mouth": "viper_mouth"},
              "motion": {"idle": "coiled", "walk": "sidewind", "windup": "draw_s", "attack": "strike", "hurt": "recoil", "death": "go_limp"}},
    "eel": {"parts": EEL, "mats": {"skin": "eel", "belly": "eel_belly", "fin": "eel_fin", "mouth": "eel_mouth"},
            "motion": {"idle": "sway", "walk": "glide", "windup": "rear_back", "attack": "lunge_snap", "hurt": "snap_back",
                       "death": "sink"}},
    "leech": {"parts": LEECH, "mats": {"skin": "leech", "dark": "leech_dark", "belly": "leech_belly", "lip": "leech_lip", "maw": "leech_maw"},
              "motion": {"idle": "quest", "walk": "inchworm", "swim": "ribbon", "windup": "rear_s", "attack": "latch_drink",
                         "hurt": "ball_up", "death": "writhe_flat"}},
}


def pose(B, action: str, f: int, k: float = 1.44, awake: bool = False, view: float = 90.0) -> Pose:
    if "coil_share" in B.parts:
        return _viper(B, action, f, view)
    if B.variant == "leech" or "rest" in B.parts:
        return _leech(B, action, f, view)
    if "horns" in B.parts:
        return _dragon(B, action, f, k)
    if "ball" in B.parts:
        return _boulder(B, action, f, view)
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


# ================================================================================================= the dragon (M2)
# The riverbed serpent: the eel's key poses (its side-view sheet's S is the same rising curve), a jade dragon-eel on
# them. Its own styles name the eel's poses and what the dragon adds: `orb` (0..1, the water orb its tell gathers before
# its jaws), `splash` (frames throwing spray), `whisk` (the whiskers' wave).
DRAGON_STYLES = {
    "coil_sway": dict(STYLES["sway"], motes=False, whisk=1.0),
    "surge": dict(STYLES["glide"], motes=False, whisk=1.4),
    "rear_orb": dict(STYLES["rear_back"], motes=False, orb=(0.3, 0.55, 0.8, 1.0), whisk=0.6),
    "dragon_bite": dict(STYLES["lunge_snap"], splash=(1, 2), whisk=1.8),
    "toss_back": dict(STYLES["snap_back"], splash=(0,), whisk=1.6),
    "dive_under": dict(STYLES["sink"], mist=False, splash=(1, 2, 3, 4, 5), whisk=0.8),
}
STYLES.update(DRAGON_STYLES)
DRAGON = dict(EEL, **{
    "lift": 3.0,                      # it hovers a little (a flyer's bob, EnemyAuthority._hover): its water a step under
    "s": (0.0, 2.2, -1.6, 2.0, -0.8, 0.3),
    "profile": ((0.0, 4.7), (0.3, 4.3), (0.6, 3.8), (0.85, 3.3), (1.0, 3.1)),
    "crest": (3.4, 1.3),              # the gold spines' length, the fin web's height between them
    "skull": ((0.8, 0.0, 0.5), (3.9, 3.1, 2.8)), "snout": ((5.3, 0.0, 0.1), (3.6, 2.05, 1.6)),
    "brow": ((2.2, 1.7, 1.95), (2.1, 1.05, 0.85)), "eye": (2.85, 2.15, 1.15),
    "horns": ((-0.9, 1.45, 2.0), (-3.0, 2.2, 3.6), (-5.6, 2.6, 4.2), (-7.4, 2.5, 3.6)), "horn_r": (0.85, 0.6, 0.35, 0.12),
    "whiskers": {"root": (7.4, 1.25, -0.5), "n": 8, "step": 1.45, "r": (0.34, 0.16)},
    "frill": ((-0.4, 2.4, 0.2), 3.0, 3),
    "orb": (11.2, 0.0, -2.2),
})
VARIANTS["dragon"] = {"parts": DRAGON, "mats": {"skin": "rs_scale", "belly": "rs_belly", "fin": "rs_fin", "mouth": "rs_mouth",
                                                "horn": "rs_horn", "gold": "rs_gold", "orb": "rs_orb"},
                      "motion": {"idle": "coil_sway", "walk": "surge", "windup": "rear_orb", "attack": "dragon_bite", "hurt": "toss_back",
                                 "death": "dive_under"}}


def _dragon(B, action: str, f: int, k: float) -> Pose:
    """M2, the riverbed serpent: a jade dragon-eel rising out of clear water on the eel's S. Jade scales in arcs over its
    back, gold belly scutes down its front, a crest of gold spines webbed in pale jade fin down its back and over the loop
    behind it; a long dragon head (a heavy brow over a glowing gold eye, a long snout, swept-back ivory horns, a gill frill
    of gold-spined fins, long gold whiskers trailing from its snout and waving); its jaw drops on white fangs and a red
    maw. Its tell gathers the river into an orb before its open jaws (held); it lunges and bites in a splash; struck, it
    tosses back; beaten, it dives under in spray. No Hollow in it: clear water, white foam, no strands."""
    p, m = B.parts, B.mats
    st = B.style(action)
    P = Pose()
    P.water = -p.lift / math.cos(ELEV)
    wz = P.water / k
    ctrl, head_deg, gape, eye, sink = _key(B, action, f)
    sway = st.sway[0] * wave(action, f, st.sway[1]) if "sway" in st else 0.0
    ahead = st.get("ahead", p.ahead)
    pts = [v3(x * ahead, p.s[i] + sway * (i / 5.0) ** 2, wz - (y + sink) * p.up) for i, (x, y) in enumerate(ctrl)]
    spine = _spline(pts, p.n)
    if "undulate" in st:
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
    under = lambda q: q[:, 2] > wz
    prof = p.profile

    def radius(t):
        for (t0, r0), (t1, r1) in zip(prof, prof[1:]):
            if t <= t1:
                return r0 + (r1 - r0) * (t - t0) / (t1 - t0)
        return prof[-1][1]

    def skin(q, nn):
        """Jade scales in arcs over the back and flanks (a step dark at each arc's edge, a step lit inside the next); the
        gold belly down its front in scutes, a dark line between each."""
        belly = (nn[:, 0] > 0.6) | (nn[:, 2] < -0.6)
        u = q[:, 2] * 0.8 + np.abs(q[:, 1]) * 0.55 + q[:, 0] * 0.25
        arc = (u % 1.25) < 0.24
        lit = ((u % 1.25) > 0.6) & ((u % 1.25) < 0.78) & (nn[:, 2] > 0.2)
        scute = (q[:, 2] * 0.62) % 1.0 < 0.16
        names = np.where(belly, m.belly, m.skin).astype(object)
        bias = np.where(belly, np.where(scute, -1, 0), np.where(arc, -1, np.where(lit, 1, 0))).astype(np.int16)
        return names, bias

    def tangent(i):
        a, b = spine[max(i - 3, 0)], spine[min(i + 3, n - 1)]
        ta, tc = b[0] - a[0], b[2] - a[2]
        ln = math.hypot(ta, tc) or 1.0
        return ta / ln, tc / ln

    for i in range(0, n - 1, 2):
        r0, r1 = radius(i / (n - 1)), radius(min(n - 1, i + 2) / (n - 1))
        P.add(L(spine[i], spine[min(n - 1, i + 2)], r0, r1, m.skin, "body", skin, under))
    # The crest down its back: gold spines, the pale jade fin webbed between them, fluttering a little.
    spine_h, web = p.crest
    for j, i in enumerate(range(9, n - 7, 3)):
        q = spine[i]
        if q[2] < wz:
            continue
        ta, tc = tangent(i)
        da, dc = -tc, ta
        r = radius(i / (n - 1))
        h = spine_h * (0.75 + 0.25 * math.sin(j * 1.9)) + 0.25 * math.sin(f * 1.7 + j)
        mm = np.array(((ta, 0.0, da), (0.0, 1.0, 0.0), (tc, 0.0, dc)))
        base = v3(q[0] + da * (r - 0.4), q[1], q[2] + dc * (r - 0.4))
        P.add(E(base + v3(da, 0.0, dc) * (web * 0.5), (1.6, 0.35, web * 0.9), m.fin, "crest", mm, clip=under, line=False))
        tip = base + v3(da - ta * 0.7, 0.0, dc - tc * 0.7) * h
        P.add(L(base, tip, 0.55, 0.15, m.gold, "crest", clip=under, line=False))
    # The loop of its back breaking the surface behind it, crested, and its tail fin fanning beyond.
    roll = st.roll_amp * math.sin(f / 8.0 * math.tau) if "roll_amp" in st else 0.0
    lift = (st.lift[0] * wave(action, f, st.lift[1]) if "lift" in st else 0.0) - sink * p.up
    low = -2.6 - sink * p.up
    lp = p.loop
    loop = ((lp[0][0], lp[0][1], low), (lp[1][0], lp[1][1], lp[1][2] + lift), (lp[2][0], lp[2][1], lp[2][2] + lift),
            (lp[3][0], lp[3][1], lp[3][2] + lift * 0.5), (lp[4][0], lp[4][1], low))
    hump = _spline([v3(a + roll, b, wz + c_) for a, b, c_ in loop], 12)
    for i in range(len(hump) - 1):
        P.add(L(hump[i], hump[i + 1], 3.0 - 0.5 * i / 11.0, 3.0 - 0.5 * (i + 1) / 11.0, m.skin, "hump", skin, under))
    for i in (3, 5, 7, 9):
        q = hump[i]
        P.add(E(v3(q[0], q[1], q[2] + 2.9), (0.9, 0.3, 0.8), m.fin, "hump_fin", rot("c", -42.0), clip=under, line=False))
        P.add(L(v3(q[0], q[1], q[2] + 2.4), v3(q[0] - 0.6, q[1] + 0.5, q[2] + 2.4 + spine_h * 0.8), 0.35, 0.12, m.gold, "hump_fin",
                clip=under, line=False))
    tail = v3(-14.2 + roll, 10.2, wz + 0.2 + lift * 0.4)
    tm_ = rot("c", -42.0) @ rot("b", -20.0)
    P.add(E(tail, (2.2, 0.35, 1.9), m.fin, "tailfin", tm_, clip=under))
    for t_ in (-35.0, 0.0, 35.0):
        P.add(L(tail - tm_ @ v3(1.2, 0.0, 0.0), tail + tm_ @ v3(-math.cos(math.radians(t_)) * 0.4 - 1.0, 0.0, math.sin(math.radians(t_)) * 2.4 + 0.6),
                0.3, 0.1, m.gold, "tailfin", clip=under, line=False))
    # The head: skull and long snout along the neck's end, a heavy brow, the jaw dropping by the gape.
    H = spine[-1]
    ta, tc = tangent(n - 1)
    pitch = math.degrees(math.atan2(tc, ta)) * 0.35 + head_deg * 0.8
    hm = rot("b", pitch)
    hp = lambda q: H + hm @ v3(q)
    skull_c, skull_r = hp(p.skull[0]), p.skull[1]
    P.add(E(skull_c, skull_r, m.skin, "head", hm, skin, under), E(hp(p.snout[0]), p.snout[1], m.skin, "head", hm, skin, under))
    for s in (1, -1):
        bc, br = p.brow
        P.add(E(hp((bc[0], s * bc[1], bc[2])), br, m.skin, "brow", hm, skin, under, line=False))
    jm = hm @ rot("b", -gape * 38.0)
    hinge = hp((0.6, 0.0, -1.2))
    if gape > 0.2:
        P.add(E(hinge + hm @ rot("b", -gape * 19.0) @ v3(3.4, 0.0, -0.2), (3.0, 1.45, 0.8), m.mouth, "mouth", jm, clip=under, line=False))
        for t in (3.0, 4.4, 5.8, 7.0):
            for s in (1, -1):
                P.mark(hp((t, s * 1.25, -1.35)), M.EEL_TOOTH)
                P.mark(hinge + jm @ v3(t - 0.4, s * 1.05, 0.35), M.EEL_TOOTH)
    P.add(E(hinge + jm @ v3(3.8, 0.0, -0.4), (3.6, 1.7, 0.85), m.belly, "jaw", jm, clip=under))
    # Swept-back ivory horns from the back of its skull.
    hr = p.horn_r
    for s in (1, -1):
        hpts = [hp((x, s * y, z)) for x, y, z in p.horns]
        for i in range(len(hpts) - 1):
            P.add(L(hpts[i], hpts[i + 1], hr[i], hr[i + 1], m.horn, "horn%d" % s, clip=under))
    # The gill frill behind the jaw: gold-spined fins fanning back.
    (fa, fb, fc), flen, fn = p.frill
    for s in (1, -1):
        root = hp((fa, s * fb, fc))
        for j in range(fn):
            ang = math.radians(-30.0 + 30.0 * j)
            d = hm @ v3(-math.cos(ang), s * 0.55, math.sin(ang))
            tip = root + d * flen
            mm_ = np.stack([d / np.linalg.norm(d), hm @ v3(0.0, 1.0, 0.0), np.cross(d / np.linalg.norm(d), hm @ v3(0.0, 1.0, 0.0))], axis=1)
            P.add(E((root + tip) * 0.5, (flen * 0.5, 0.25, 0.7), m.fin, "frill%d" % s, mm_, clip=under, line=False))
            P.add(L(root, tip, 0.28, 0.1, m.gold, "frill%d" % s, clip=under, line=False))
    # Its eyes: gold, glowing under the brow (flaring wide in the tell), screwed shut when struck, dull when it dies.
    ea, eb, ec = p.eye
    for s in (1, -1):
        e_ = hp((ea, s * eb, ec))
        if eye in ("open", "wide"):
            P.eye(e_, M.RS_EYE_CORE)
            P.mark(e_ + hm @ v3(-0.45, 0.0, 0.0), M.RS_EYE)
            P.mark(e_ + hm @ v3(0.0, 0.0, -0.45), M.RS_EYE_RING)
            if eye == "wide":
                for dd in ((0.3, 0.0, 0.8), (-0.6, 0.0, 0.6), (0.6, 0.0, -0.2)):
                    P.glow.append((e_ + hm @ v3(*dd) + hm @ v3(0.0, s * 0.4, 0.0), M.RS_EYE_GLOW))
        elif eye == "dead":
            P.mark(e_, M.RAMPS[m.skin][1])
        else:
            P.mark(e_, M.RAMPS[m.skin][0])
        P.mark(hp((p.snout[0][0] + p.snout[1][0] - 0.3, s * 0.7, 0.6)), M.RAMPS[m.skin][0])     # its nostril
    # Long gold whiskers from its snout, trailing back and down, waving.
    w = p.whiskers
    wk = st.get("whisk", 1.0)
    for s in (1, -1):
        wp = [hp((w.root[0], s * w.root[1], w.root[2]))]
        for j in range(1, w.n + 1):
            u = j / float(w.n)
            wav = math.sin(f * 1.3 + j * 0.9 + (0.0 if s > 0 else 1.4)) * 0.7 * wk * u
            wp.append(wp[0] + hm @ v3(-j * w.step * 0.8, s * (0.5 + j * 0.35), -j * w.step * 0.55 + wav) + v3(0.0, 0.0, -u * u * 1.6))
        for i in range(len(wp) - 1):
            r0 = w.r[0] + (w.r[1] - w.r[0]) * i / w.n
            P.add(L(wp[i], wp[i + 1], r0, r0 - (w.r[0] - w.r[1]) / w.n, m.gold, "whisker%d" % s, clip=under, line=False))
    # The tell: the river spirals up into an orb before its open jaws, swelling until the blow.
    orb = B.pick("orb", action, f)
    if orb > 0.0:
        oc = hp(p.orb) + hm @ v3(orb * 0.8, 0.0, 0.0)
        r = 0.8 + 1.7 * orb
        P.add(S(oc, r, m.orb, "orb", line=False))
        P.glow.append((oc + v3(0.0, 0.0, r * 0.55) + hm @ v3(-r * 0.3, 0.0, 0.0), M.RS_ORB_GLINT))
        for j in range(14):
            u = ((j * 0.071 + f * 0.13) % 1.0)
            ang = u * 4.0 * math.tau + j
            rr = r + 1.2 + 5.0 * (1.0 - u)
            q = oc + v3(math.cos(ang) * rr * 0.7, math.sin(ang) * rr, -(1.0 - u) * 9.0 * orb)
            P.fx.append((q, M.SPLASH if j % 3 else M.SPLASH_DIM))
        for j in range(8):
            ang = math.radians(j * 45.0 + f * 30.0)
            P.glow.append((oc + v3(math.cos(ang) * (r + 0.6) * 0.6, math.sin(ang) * (r + 0.6), math.sin(ang * 2.0) * 0.5), M.RS_ORB_AURA))
    # Spray: off its jaws as it bites, off its body as it tosses back or dives under.
    if f in st.get("splash", ()):
        at_ = hp((7.0, 0.0, -1.5)) if action == "attack" else v3(spine[n // 3][0], 0.0, wz + 0.5)
        for j in range(18):
            ang = math.radians(j * 20.0 + f * 17.0)
            rr = 2.5 + (j % 3) * 1.6 + f * 1.0
            q = at_ + v3(math.cos(ang) * rr * 0.6, math.sin(ang) * rr, 1.0 + (j % 4) * 1.1 + (2.0 if j % 2 else 0.0))
            P.fx.append((q, M.SPLASH if j % 2 else M.SPLASH_DIM))
    # The water round it: clear river, white foam where the body and the loop break the surface, rings spreading.
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
            return M.FOAM if h01(ang, f, 17) > 0.25 else M.RS_POOL_LIT
        if dh < 2.6:
            return M.FOAM
        if abs(d0 - ring) < 0.5 and d0 > base_r + 3.0:
            return M.RS_RIPPLE
        if abs(d0 - ring + 3.8) < 0.45 and d0 > base_r + 3.0:
            return M.RS_RIPPLE_DIM
        if wake and -14.0 + roll > a > -19.5:
            wd = (-14.0 + roll - a) * 0.5 + 0.8
            if abs(abs(b - 10.0) - wd) < 0.45:
                return M.RS_RIPPLE_DIM
        if d0 < base_r + 3.2 or dh < 4.2 or (along(a, b) < 3.3 and sink < 30):
            return M.RS_POOL
        return None

    P.water_fx = water
    return P


# ================================================================================================= the boulder serpent (M2)
# A heavy serpent armoured in boulder plates (the Echo Cliffs). Its styles' channels: `rise` (its head's height over the
# ground), `reach` (its head held ahead), `wave` (the S of its body, its amplitude), `ball` (0..1: curled up into a
# boulder), `spin` (the ball rolled forward, degrees), `lunge`, `gape`, `hpitch`, `limp` (lying slack), `crack` (0..1: its
# plates split as it dies), `writhe`.
BOULDER_STYLES = {
    "rest_s": {"rise": (3.2, 3.3, 3.4, 3.3, 3.2, 3.1), "wave": (1.0,) * 6, "sway": 0.6, "tongue": (2, 5)},
    "slither": {"kind": "slither", "rise": (2.4,) * 8, "wave": (1.3,) * 8, "tongue": (4,)},
    "curl_ball": {"ball": (0.3, 0.65, 0.9, 1.0), "spin": (0.0, 0.0, -12.0, -22.0), "lunge": (-0.3, -0.6, -0.9, -1.0),
                  "rise": (2.4, 1.6, 1.0, 1.0), "wave": (0.8, 0.5, 0.3, 0.2), "dust": (2, 3), "peek": True},
    "boulder_roll": {"ball": (1.0, 1.0, 1.0, 0.7, 0.35, 0.0), "spin": (130.0, 255.0, 320.0, 350.0, 360.0, 360.0),
                     "lunge": (3.6, 6.8, 7.4, 6.2, 3.4, 1.0), "rise": (1.0, 1.0, 1.0, 1.6, 2.4, 3.0), "wave": (0.2, 0.2, 0.2, 0.5, 0.8, 1.0),
                     "squash": {1: (0.92, 1.04, 1.06)}, "dust": (0, 1, 2), "streaks": (0, 1), "spark": 1},
    "flinch_back": {"rise": (4.0, 3.6, 3.3), "reach": (-1.6, -0.8, -0.2), "hpitch": (20.0, 8.0, 2.0), "gape": (0.6, 0.2, 0.0),
                    "wave": (1.2, 1.1, 1.0), "writhe": (0.6, -0.3, 0.0)},
    "slump_crack": {"rise": (3.6, 2.4, 1.2, 0.6, 0.5, 0.5, 0.5, 0.5), "limp": (0.0, 0.3, 0.6, 0.85, 1.0, 1.0, 1.0, 1.0),
                    "hpitch": (16.0, 6.0, -4.0, -10.0, -12.0, -12.0, -12.0, -12.0), "gape": (0.6, 0.5, 0.4, 0.3, 0.3, 0.3, 0.3, 0.3),
                    "wave": (1.0, 0.9, 0.8, 0.7, 0.7, 0.7, 0.7, 0.7), "writhe": (0.8, -0.5, 0.3, -0.1, 0.0, 0.0, 0.0, 0.0),
                    "crack": (0.0, 0.0, 0.2, 0.45, 0.7, 0.9, 1.0, 1.0), "dead_from": 3},
}
STYLES.update(BOULDER_STYLES)
BOULDER = {
    "length": 28.0, "ball": 4.6,
    "width": ((0.0, 0.45), (0.12, 1.4), (0.35, 2.15), (0.62, 2.2), (0.85, 1.6), (0.93, 1.45), (1.0, 1.7)),
    "plates": {"from": 0.1, "to": 0.86, "n": 10, "r": (1.75, 1.35, 1.15)},
    "head": {"skull": (2.8, 2.1, 1.6), "snout": ((1.9, 0.0, -0.25), (1.8, 1.55, 1.1)), "brow": ((0.8, 0.0, 1.05), (1.8, 1.9, 0.75)),
             "eye": (1.25, 1.65, 0.55)},
}
VARIANTS["boulder"] = {"parts": BOULDER, "mats": {"skin": "bs_hide", "belly": "bs_belly", "rock": "bs_rock", "lichen": "bs_lichen",
                                                  "mouth": "bs_mouth"},
                       "motion": {"idle": "rest_s", "walk": "slither", "windup": "curl_ball", "attack": "boulder_roll",
                                  "hurt": "flinch_back", "death": "slump_crack"}}


def _boulder(B, action: str, f: int, view: float) -> Pose:
    """M2, the boulder serpent: a heavy serpent laid in an S on the ground, its head raised a little; a thick ochre hide,
    a sandstone belly in scutes, a row of grey boulder plates down its spine (each its own lump, dark seams between them,
    lichen on some), a heavy wedge of a head under a rocky brow plate (amber slit eyes, a forked tongue). It slithers; it
    curls up into a boulder (the tell, held: its head tucked in, one eye peeking) and rolls forward to slam on the blow,
    then unrolls; struck, it rears back; beaten, it slumps slack and its plates crack. The spine is laid out (the S on the
    ground, or a spiral round the ball) and resampled evenly; the body is ellipsoids along it, the plates lumps over it."""
    p, m = B.parts, B.mats
    st = B.style(action)
    P = Pose()
    seed = int(B.opts.get("seed", 0))
    L_ = p.length
    R = p.ball
    ph = f / 8.0 * math.tau if action == "walk" else f / 6.0 * math.tau
    rise = B.pick("rise", action, f, 3.0)
    reach = B.pick("reach", action, f)
    wav = B.pick("wave", action, f, 1.0)
    ball = B.pick("ball", action, f)
    spin = B.pick("spin", action, f)
    lunge = B.pick("lunge", action, f)
    gape = B.pick("gape", action, f)
    hp_ = B.pick("hpitch", action, f)
    limp = B.pick("limp", action, f)
    crack = B.pick("crack", action, f)
    y = math.radians(view)
    fronton = max(0.0, math.sin(y))
    sway = st.get("sway", 0.0) * math.sin(ph)
    K = 40
    u = np.linspace(0.0, 1.0, K)
    # Laid out: an S along the ground behind the head (travelling down it as it slithers), its neck rising at the front.
    travel = ph if st.get("kind") == "slither" else 0.0
    a = -L_ * (1.0 - u) * 0.62 + 4.0 + lunge * (1.0 - ball) + reach * u ** 4
    b = wav * 2.6 * np.sin(2 * math.pi * 1.05 * u - travel + 0.6) * (0.3 + 0.7 * (1.0 - u)) + sway * u ** 2 - 0.9 * fronton * u ** 3
    neck = np.clip((u - 0.8) / 0.2, 0.0, 1.0)
    c = rise * (neck * neck * (3.0 - 2.0 * neck)) * (1.0 - limp)
    spine = np.stack([a, b, c], axis=1)
    if B.has("writhe", action):
        wr = B.pick("writhe", action, f)
        spine[:, 1] += wr * 1.2 * np.sin(np.linspace(0.0, 8.0, K) + f)
    C = v3(lunge, 0.0, R + 0.1)
    if ball > 0.0:
        # Curled up: a spiral round a ball, from the tail at its back underneath to the head at its front, peeking out.
        # Wound from the bottom round to the crown (so its plates cover the ball all over), the neck coming down over
        # the front to the head.
        w_ = np.clip(u / 0.8, 0.0, 1.0)
        h_ = np.clip((u - 0.8) / 0.2, 0.0, 1.0)
        lat = np.radians(-68.0 + 136.0 * w_ - 50.0 * h_)
        lon = np.radians(560.0 * (1.0 - w_) + 8.0 + 50.0 * (1.0 - h_) * (w_ >= 1.0))
        sph = np.stack([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)], axis=1)
        rolled = sph @ rot("b", -spin).T
        coil = C + rolled * (R - 0.2)
        e = ball * ball * (3.0 - 2.0 * ball)
        spine = spine * (1.0 - e) + coil * e
    pts, total = _resample(np.asarray(spine, float), 32)
    n = len(pts)
    T = np.gradient(pts, axis=0)
    T /= np.maximum(1e-6, np.linalg.norm(T, axis=1))[:, None]
    up = np.array((0.0, 0.0, 1.0))
    W = p.width
    frames = []
    prevB = np.array((0.0, 1.0, 0.0))
    for k in range(n):
        Tk = T[k]
        out = up if ball <= 0.0 else _unit(up * (1.0 - ball) + _unit(pts[k] - C) * ball)
        Bk = np.cross(out, Tk)
        if np.linalg.norm(Bk) < 0.2:
            Bk = prevB
        Bk = Bk / np.linalg.norm(Bk)
        prevB = Bk
        Nk = np.cross(Tk, Bk)
        frames.append((Tk, Bk, Nk))
    if ball > 0.0:
        # The core of the ball, stone between the coils, grown as it curls (so it reads as one boulder).
        P.add(S(C, (R - 0.5) * ball, m.rock, "core", _rock(m, C, up, seed + 7, 0.0)))
    for k in range(n):
        Tk, Bk, Nk = frames[k]
        s = k / (n - 1.0)
        r = _width(W, s)
        centre = pts[k] + Nk * r * 0.8 if ball <= 0.0 else pts[k]
        if ball <= 0.0:
            centre = pts[k] + np.array((0.0, 0.0, r * 0.85))
        mm = np.stack([Tk, Bk, Nk], axis=1)
        P.add(E(centre, (max(0.6 * total / (n - 1) + 0.35, 0.8), r, r * 0.85), m.skin, "body", mm, _hide(m, centre, Nk, s * total, r)))
        frames[k] = (Tk, Bk, Nk, centre, r)
    # The boulder plates down its spine: grey lumps, dark seams between them, lichen on some, pale flecks; cracked as it
    # dies (dark lines across them, by its seed).
    pl = p.plates
    for j in range(pl.n):
        s = pl["from"] + (pl.to - pl["from"]) * j / (pl.n - 1.0)
        k = int(round(s * (n - 1)))
        Tk, Bk, Nk, centre, r = frames[k]
        big = pl.r[0] * (0.75 + 0.25 * math.sin(math.pi * s)) * (1.0 + 0.15 * ((j * 7 + seed) % 3 == 0))
        q = centre + Nk * (r * 0.78)
        mm = np.stack([Tk, Bk, Nk], axis=1) @ rot("c", ((j * 37 + seed) % 21) - 10.0)
        P.add(E(q, (big * 1.05, big * pl.r[1] / pl.r[0] * 1.15, big * pl.r[2] / pl.r[0]), m.rock, "plate%d" % (j % 2), mm,
                _rock(m, q, Nk, seed + j, crack)))
    # The head: a heavy wedge at the neck's end, under its rocky brow plate; tucked against the ball as it curls, one eye
    # peeking out.
    Tn, Bn, Nn, centre, r = frames[-1]
    Tn = Tn.copy()
    if ball <= 0.0:
        Tn[2] *= 0.3
        Tn /= np.linalg.norm(Tn)
        Bn = np.cross(up, Tn)
        Bn = Bn / max(1e-6, np.linalg.norm(Bn))
        Nn = np.cross(Tn, Bn)
    hm = np.stack([Tn, Bn, Nn], axis=1) @ rot("b", hp_ + 4.0 * fronton)
    hd = p.head
    hc = centre + hm @ v3(1.0, 0.0, 0.15)
    P.add(E(hc, hd.skull, m.skin, "head", hm, _hide(m, hc, hm[:, 2], 0.0, hd.skull[1])))
    P.add(E(hc + hm @ v3(hd.snout[0]), hd.snout[1], m.skin, "head", hm, _hide(m, hc, hm[:, 2], 0.0, hd.skull[1])))
    P.add(E(hc + hm @ v3(hd.brow[0]), hd.brow[1], m.rock, "brow", hm, _rock(m, hc, hm[:, 2], seed + 99, crack)))
    dead = action == "death" and f >= st.get("dead_from", 99)
    for sd in (1, -1):
        eye = hc + hm @ v3(hd.eye[0], sd * hd.eye[1], hd.eye[2])
        if dead or (ball > 0.6 and sd < 0):
            P.mark(eye, M.RAMPS[m.skin][0])
        else:
            P.eye(eye, M.BOULDER_EYE)
            P.mark(eye + hm @ v3(0.0, sd * 0.05, 0.35), M.INKY)
    if gape > 0.08:
        jm = hm @ rot("b", -gape * 34.0)
        hinge = hc + hm @ v3(-0.8, 0.0, -0.7)
        P.add(E(hinge + jm @ v3(2.0, 0.0, -0.1), (1.9, 1.4, 0.5), m.belly, "jaw", jm))
        P.add(E(hinge + hm @ v3(1.8, 0.0, -0.2), (1.5, 1.1, 0.35), m.mouth, "maw", hm, line=False))
        for sd in (1, -1):
            P.mark(hc + hm @ v3(hd.snout[0][0] + 0.6, sd * 0.6, -1.0), M.FANG)
    if f in st.get("tongue", ()) and ball <= 0.0:
        tip = hc + hm @ v3(hd.snout[0][0] + hd.snout[1][0] + 0.3, 0.0, -0.4)
        for t in (0.0, 0.6, 1.2):
            P.mark(tip + hm @ v3(t, 0.0, 0.0), M.VIPER_TONGUE)
        for sd in (1, -1):
            P.mark(tip + hm @ v3(1.7, sd * 0.45, 0.0), M.VIPER_TONGUE)
    # Dust as it curls and as it rolls, speed streaks behind the ball, the spark of its slam.
    if f in st.get("dust", ()):
        for k in range(7):
            ang = math.radians(k * 51.0 + f * 25.0)
            rr = R * 0.9 + (k % 3) * 0.8
            P.fx.append((v3(lunge - R * 0.5 + math.cos(ang) * rr * 0.6, math.sin(ang) * rr, 0.3 + (k % 2) * 0.6), M.DUST if k % 2 else M.DUST_DIM))
    if action == "attack" and f in st.get("streaks", ()):
        for k in range(4):
            yy = (k - 1.5) * 2.2
            for d in range(3):
                P.fx.append((v3(lunge - R - 2.2 - d * 1.3 - k % 2, yy, R + (k % 2) * 1.0), M.DUST_DIM if d else M.DUST))
    if action == "attack" and f == st.get("spark", -1):
        for k in range(6):
            ang = math.radians(k * 60.0)
            P.glow.append((v3(lunge + R + 0.6, math.cos(ang) * 1.8, R * 0.6 + math.sin(ang) * 1.8), M.SPECK))
    sq = st.get("squash", {}).get(f)
    if sq is not None:
        P.squash(sq[0], sq[1], sq[2], (lunge, 0.0, 0.0))
    return P


def _unit(v):
    return v / max(1e-9, float(np.linalg.norm(v)))


def _hide(m, centre, N, s0: float, w: float):
    """The boulder serpent's hide: thick ochre, scales a step dark in rows across it; the sandstone belly underneath in
    scutes (a dark line between each)."""
    def skin(q, nrm):
        d = q - centre
        nz = nrm @ N
        belly = nz < -0.25
        rows = ((d @ N) * 0.0 + (q[:, 0] * 0.9 + q[:, 1] * 0.9 + q[:, 2] * 0.6)) % 1.3 < 0.25
        scute = (q[:, 0] * 1.2 + q[:, 1] * 0.35) % 1.1 < 0.2
        names = np.where(belly, m.belly, m.skin).astype(object)
        return names, np.where(belly, np.where(scute, -1, 0), np.where(rows, -1, 0)).astype(np.int16)
    return skin


def _rock(m, centre, N, seed: int, crack: float):
    """A boulder plate: grey stone, pits a step dark and pale flecks, lichen over its top on some (by the seed); cracked as
    the serpent dies (dark lines across it, more as `crack` grows)."""
    lichen_on = seed % 3 == 0

    def rock(q, nrm):
        d = q - centre
        nz = nrm @ N
        pit = h01v(np.floor(q[:, 0] * 1.6 + 60), np.floor(q[:, 1] * 1.6 + 60) + np.floor(q[:, 2] * 1.6), seed % 97 + 3) > 0.84
        fleck = h01v(np.floor(q[:, 1] * 2.4 + 40), np.floor(q[:, 2] * 2.4 + 40), seed % 89 + 5) > 0.92
        lichen = lichen_on & (nz > 0.45) & (h01v(np.floor(q[:, 0] * 0.9 + 20), np.floor(q[:, 1] * 0.9 + 20), seed % 83 + 7) > 0.4)
        cracked = np.zeros(len(q), dtype=bool)
        if crack > 0.0:
            line = np.abs(((d[:, 0] * 0.8 + d[:, 1] * 1.3 + d[:, 2] * 0.5) % 2.2) - 1.1) < 0.12 * (1.0 + crack)
            cracked = line & (h01v(np.floor(d[:, 0] * 2.0 + 30), np.floor(d[:, 1] * 2.0 + 30), seed % 71 + 9) < crack * 1.2)
        names = np.where(lichen & ~cracked, m.lichen, m.rock).astype(object)
        return names, np.where(cracked, -3, np.where(pit, -1, np.where(fleck & ~lichen, 1, 0))).astype(np.int16)
    return rock


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


# ================================================================================================= the viper (M1)
def _viper(B, action: str, f: int, view: float) -> Pose:
    """A slender pit viper (M1, the green viper): its hind body coiled flat on the ground in a loose loop, its neck raised
    in an S with the head held level, a wedge of a head (a heavy brow scale, gold eyes with a slit, a jaw that drops on
    its fangs, a forked tongue flicking); the back green with faint crossbands, a pale yellow belly and a pale stripe
    along each flank, the tail's tip orange. It side-winds as it moves (a wave running down a body laid out behind it),
    draws its neck back into a tight S with its jaws parting (the tell), strikes along the ground (the blow on frame 1),
    recoils when struck, and goes limp, rolling onto its back. The spine is a coil on the ground and a neck curve through
    control points (`neck`: per frame the S's rise, its bend back, the head's reach and height), resampled evenly; the
    body is ellipsoids along it, painted by the length along it so the bands stay on it."""
    p, m = B.parts, B.mats
    st = B.style(action)
    P = Pose()
    L_ = p.length
    ph = f / 8.0 * math.tau
    rise, bend, reach, hz = B.pick("neck", action, f, p.neck_rest)
    gape = B.pick("gape", action, f)
    lunge = B.pick("lunge", action, f)
    sway = st.get("sway", 0.0) * wave(action, f)
    hp_ = B.pick("hpitch", action, f)
    roll = B.pick("roll", action, f)
    y = math.radians(view)
    fronton = max(0.0, math.sin(y))
    uc = p.coil_share
    if st.get("kind") == "wind":
        # Side-winding: the body laid out behind the head in a wave that runs down it as it goes.
        K = 40
        u = np.linspace(0.0, 1.0, K)
        a = -L_ * (1.0 - u) * 0.82 + 2.0
        b = 2.2 * np.sin(2 * math.pi * 1.3 * u - ph) * (0.35 + 0.65 * (1.0 - u))
        c = 0.0 * u + np.clip((u - 0.82) / 0.18, 0.0, 1.0) ** 2 * 1.4
        spine = np.stack([a, b, c], axis=1)
    else:
        # The coil: a loose loop on the ground behind the neck (the tail innermost), then the neck's S.
        # The loop runs round from the tail (innermost, at its back) and ends at its front, where the neck rises.
        R = p.coil_r
        coil = []
        for k in range(26):
            t = k / 25.0
            th = math.radians(-20.0 - (1.0 - t) * 310.0)
            r = R * (0.55 + 0.45 * t)
            coil.append(v3(-R * 0.8 + r * math.cos(th), r * math.sin(th) * (1.0 - 0.2 * fronton), 0.0))
        end = coil[-1]
        lean = 0.6 * fronton
        ctrl = [end, end + v3(0.6, 0.2, rise * 0.25), end + v3(0.6 - bend, 0.4 * sway, rise * 0.75),
                end + v3(0.4 - bend * 0.6 + reach * 0.5 + lunge * 0.5, 0.6 * sway - lean, rise),
                end + v3(reach + lunge, sway - lean, hz)]
        neck = _spline(ctrl, 16)
        spine = np.array(coil + list(neck[1:]))
        if B.has("limp", action):
            # Going limp: the neck sinks to the ground and the coil slackens.
            lim = B.pick("limp", action, f)
            straight = np.stack([np.linspace(-L_ * 0.6, 3.0, len(spine)), 1.4 * np.sin(np.linspace(0.0, 3.0, len(spine))),
                                 np.zeros(len(spine))], axis=1)
            spine = spine * (1.0 - lim) + straight * lim
            spine[:, 2] = np.maximum(0.0, spine[:, 2] * (1.0 - lim))
    if B.has("writhe", action):
        wr = B.pick("writhe", action, f)
        n0 = len(spine)
        spine = spine + np.stack([np.zeros(n0), wr * 1.4 * np.sin(np.linspace(0.0, 9.0, n0) + f), np.zeros(n0)], axis=1)
    pts, total = _resample(np.asarray(spine, float), 30)
    n = len(pts)
    T = np.gradient(pts, axis=0)
    T /= np.maximum(1e-6, np.linalg.norm(T, axis=1))[:, None]
    up = np.array((0.0, 0.0, 1.0))
    prevB = np.array((0.0, 1.0, 0.0))
    W = p.width
    for k in range(n):
        Tk = T[k]
        Bk = np.cross(up, Tk)
        if np.linalg.norm(Bk) < 0.2:
            Bk = prevB
        Bk = Bk / np.linalg.norm(Bk)
        prevB = Bk
        Nk = np.cross(Tk, Bk)
        s = k / (n - 1.0)
        r = _width(W, s)
        centre = pts[k] + np.array((0.0, 0.0, r * 0.85))
        mm = np.stack([Tk, Bk, Nk], axis=1)
        P.add(E(centre, (max(0.6 * total / (n - 1) + 0.3, 0.7), r, r * 0.85), m.skin, "body", mm,
                _scaled(m, centre, Tk, Bk, Nk, r, s * total, s < p.tip)))
    # The head: a wedge at the neck's end, held level (pitched by `hpitch`), the jaw dropping on its fangs.
    Tn = T[-1].copy()
    Tn[2] *= 0.3
    Tn /= np.linalg.norm(Tn)
    Bn = np.cross(up, Tn)
    Bn = Bn / max(1e-6, np.linalg.norm(Bn))
    hm = np.stack([Tn, Bn, np.cross(Tn, Bn)], axis=1) @ rot("b", hp_ + 4.0 * fronton)
    hc = pts[-1] + np.array((0.0, 0.0, _width(W, 1.0) * 0.85)) + hm @ v3(1.2, 0.0, 0.1)
    hd = p.head
    P.add(E(hc, hd.skull, m.skin, "head", hm, _scaled(m, hc, hm[:, 0], hm[:, 1], hm[:, 2], hd.skull[1], total, False)))
    P.add(E(hc + hm @ v3(hd.snout[0]), hd.snout[1], m.skin, "head", hm))
    for sd in (1, -1):
        P.add(E(hc + hm @ v3(hd.brow[0], sd * hd.brow[1], hd.brow[2]), (0.8, 0.55, 0.35), m.skin, "brow", hm, line=False))
        eye = hc + hm @ v3(hd.eye[0], sd * hd.eye[1], hd.eye[2])
        if action == "death" and f >= st.get("dead_from", 99):
            P.mark(eye, M.RAMPS[m.skin][0])
        else:
            P.eye(eye, M.VIPER_EYE)
            P.mark(eye + hm @ v3(0.0, sd * 0.05, 0.35), M.INKY)
    if gape > 0.08:
        jm = hm @ rot("b", -gape * 38.0)
        hinge = hc + hm @ v3(-0.6, 0.0, -0.6)
        P.add(E(hinge + jm @ v3(1.6, 0.0, -0.1), (1.6, 1.15, 0.4), m.belly, "jaw", jm))
        P.add(E(hinge + hm @ v3(1.5, 0.0, -0.15), (1.2, 0.9, 0.3), m.mouth, "maw", hm, line=False))
        for sd in (1, -1):
            P.mark(hc + hm @ v3(hd.snout[0][0] + 0.4, sd * 0.45, -0.9), M.FANG)
    if f in st.get("tongue", ()):
        tip = hc + hm @ v3(hd.snout[0][0] + hd.snout[1][0] + 0.4, 0.0, -0.3)
        for t in (0.0, 0.6, 1.2):
            P.mark(tip + hm @ v3(t, 0.0, 0.0), M.VIPER_TONGUE)
        for sd in (1, -1):
            P.mark(tip + hm @ v3(1.7, sd * 0.45, 0.0), M.VIPER_TONGUE)
    if action == "attack" and f in st.get("streaks", ()):
        for k in range(3):
            for d in range(3):
                P.fx.append((hc - hm @ v3(2.0 + d * 1.1, (k - 1) * 0.9, 0.0), M.DUST_DIM if d else M.DUST))
    if roll:
        P.m = rot("a", roll)
        turned = P.m @ v3(0.0, 0.0, 1.0)
        P.shift = v3(-turned[0], -turned[1], 1.0 - turned[2])
    return P


def _scaled(m, centre, T, B, N, w: float, s0: float, tip: bool):
    """The viper's scales: the green back crossed by faint darker bands every two units along it, a pale stripe along
    each flank, the pale yellow belly; the tail's tip orange."""
    def skin(q, nrm):
        d = q - centre
        s = s0 + d @ T
        lat = (d @ B) / max(0.3, w)
        nz = nrm @ N
        belly = nz < -0.3
        stripe = (np.abs(np.abs(lat) - 0.72) < 0.12) & (nz > -0.3) & (nz < 0.45)
        band = ((s / 2.1) % 1.0 < 0.22) & (nz > 0.2)
        if tip:
            return np.full(len(q), m.tip, dtype=object), np.where(belly, -1, 0).astype(np.int16)
        names = np.where(belly | stripe, m.belly, m.skin).astype(object)
        bias = np.where(stripe, 1, np.where(band & ~belly, -1, 0)).astype(np.int16)
        return names, bias
    return skin
