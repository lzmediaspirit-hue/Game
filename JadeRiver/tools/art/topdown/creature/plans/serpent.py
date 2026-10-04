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

M2's variants: `dragon` (the riverbed serpent: the eel's key poses with a jade river dragon on them, gold belly scutes
and spines, horns, whiskers, a gill frill, a water orb gathered before its jaws in the tell; styles `coil_sway`,
`surge`, `rear_orb`, `dragon_bite`, `toss_back`, `dive_under`) and `boulder` (the boulder serpent: a thick snake under
stone plates that curls into a ball of rock and rolls; styles `rest_s`, `slither`, `curl_ball`, `boulder_roll`,
`flinch_back`, `slump_crack`).

M4's sky swimmers: `ribbon` (the nebula eel: a ribbon body in an S-wave with fins along its back and belly, a gaping
jaw, a glowing cyan eye; styles `ribbon_drift`, `ribbon_swim`, `coil_gape`, `lunge_bite`, `kink_jerk`, `unravel_fade`)
and `leviathan` (the Nebula Leviathan, a whale head on a serpent body with veils and constellations, the void gathered in
its mouth and breathed; styles `levi_drift`, `levi_glide`, `void_gather`, `void_breath`, `levi_recoil`, `levi_sink`). Their
bodies are laid along a spine integrated back from the neck (`_sky_spine`), a wave of its heading travelling down it.
The leviathan also swims (`swim`, its spec's `extra`, played where it crosses water on the grid; style `levi_swim`): its
body mostly under the star-water, its head's dome and eye, the loops of its back and its veil breaking the surface, a
wake spreading behind its head and foam where it breaks the water (`parts.swim`: the water's line under its feet, the
body's height against it).
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
    if "ribbon" in B.parts:
        return _ribbon(B, action, f, view)               # M4: the nebula eel
    if "leviathan" in B.parts:
        return _leviathan(B, action, f, view, k)         # M4: the Nebula Leviathan
    if "mound" in B.parts:
        return _worm(B, action, f, view)
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


# ================================================================================================= the sky swimmers (M4)
# The nebula eel (`ribbon`) and the Nebula Leviathan (`leviathan`) swim the air of the Lantern Star Field (flyers: the room
# view's shadow under them). Each body is laid along a spine integrated back from its neck by arc length: a wave of the
# heading travels along it from the head to the tail (`amp` degrees across, `wl` its wavelength, `vamp` its rise and fall),
# so its length holds as it swims. Channels: `lunge`, `rise`, `amp`, `wl`, `vamp`, `hpitch` (the head's pitch), `gape`,
# `flare` (the eyes', the tell's light), `kink` (a jerk across the body's middle, degrees), `ripple` (the eel's void ripple
# before its snout on the blow), `void` (0..1: the void gathering in the leviathan's mouth), `breath` (how far its void
# breath has reached), `unravel` (0..1: the eel coming apart from its tail into wisps), `lights` (the leviathan's
# constellations lit, 0..1), `drop` (sunk toward the floor), `dissolve`, `squint`.
SKY_STYLES = {
    # the nebula eel
    "ribbon_drift": {"kind": "wave", "n": 6, "amp": 40.0, "wl": 12.0, "vamp": 6.0, "bob": 0.4},
    "ribbon_swim": {"kind": "wave", "n": 8, "amp": 50.0, "wl": 11.0, "vamp": 7.0, "bob": 0.5, "lunge_amp": 0.6},
    "coil_gape": {"amp": (50.0, 62.0, 72.0, 76.0), "wl": (10.0, 8.8, 8.0, 7.6), "lunge": (-0.6, -1.4, -2.0, -2.2), "hpitch": (6.0, 12.0, 16.0, 18.0),
                  "gape": (0.3, 0.6, 0.9, 1.0), "flare": (0.5, 1.0, 1.0, 1.0), "phase": (0.0, 0.4, 0.7, 0.8), "rise": (0.2, 0.4, 0.6, 0.6)},
    "lunge_bite": {"amp": (34.0, 14.0, 14.0, 22.0, 30.0, 38.0), "wl": (12.0,) * 6, "lunge": (2.0, 5.6, 5.8, 4.4, 2.4, 0.8), "hpitch": (6.0, -6.0, -6.0, -2.0, 0.0, 0.0),
                   "gape": (1.0, 0.0, 0.0, 0.1, 0.1, 0.0), "flare": (1.0, 0.6, 0.3, 0.0, 0.0, 0.0), "ripple": (0.0, 1.0, 1.7, 0.0, 0.0, 0.0),
                   "phase": (0.8, 1.0, 1.1, 1.2, 1.3, 1.4), "squash": {1: (1.04, 0.98, 0.98)}},
    "kink_jerk": {"amp": (26.0, 32.0, 38.0), "wl": (12.0,) * 3, "kink": (56.0, 26.0, 8.0), "lunge": (-2.0, -1.2, -0.4), "hpitch": (14.0, 6.0, 0.0),
                  "gape": (0.4, 0.2, 0.0), "specks": (0, 1), "squint": True},
    "unravel_fade": {"amp": (40.0, 30.0, 24.0, 20.0, 18.0, 18.0, 18.0, 18.0), "wl": (12.0,) * 8, "kink": (30.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                     "unravel": (0.0, 0.1, 0.25, 0.42, 0.6, 0.78, 0.92, 1.0), "drop": (0.0, 0.08, 0.18, 0.3, 0.42, 0.52, 0.6, 0.66),
                     "hpitch": (16.0, 0.0, -8.0, -14.0, -18.0, -20.0, -20.0, -20.0), "gape": (0.5, 0.3, 0.2, 0.1, 0.1, 0.1, 0.1, 0.1),
                     "dissolve": (0.0, 0.0, 0.0, 0.05, 0.15, 0.3, 0.5, 0.75), "dead": 2},
    # the Nebula Leviathan
    "levi_drift": {"kind": "wave", "n": 6, "amp": 20.0, "wl": 22.0, "vamp": 7.0, "bob": 0.5, "lights": 1.0},
    "levi_glide": {"kind": "wave", "n": 8, "amp": 26.0, "wl": 20.0, "vamp": 8.0, "bob": 0.6, "lights": 1.0, "lunge_amp": 0.6},
    "void_gather": {"amp": (14.0, 16.0, 18.0, 18.0), "wl": (18.0,) * 4, "lunge": (-0.8, -1.8, -2.6, -2.8), "hpitch": (8.0, 16.0, 22.0, 24.0),
                    "gape": (0.4, 0.75, 1.0, 1.0), "void": (0.3, 0.6, 0.9, 1.0), "rise": (0.4, 0.9, 1.3, 1.4), "lights": (1.0,) * 4,
                    "phase": (0.0, 0.2, 0.35, 0.4), "spiral": True},
    "void_breath": {"amp": (14.0, 10.0, 10.0, 12.0, 14.0, 14.0), "wl": (18.0,) * 6, "lunge": (0.0, 2.6, 2.8, 2.2, 1.2, 0.4),
                    "hpitch": (16.0, 0.0, -2.0, 0.0, 2.0, 2.0), "gape": (1.0, 1.0, 0.9, 0.6, 0.3, 0.1), "void": (1.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                    "breath": (0.0, 1.0, 1.6, 2.0, 0.0, 0.0), "lights": (1.0,) * 6, "phase": (0.4, 0.5, 0.6, 0.7, 0.8, 0.9),
                    "squash": {1: (1.03, 1.0, 0.98)}},
    "levi_recoil": {"amp": (10.0, 14.0, 14.0), "wl": (18.0,) * 3, "kink": (18.0, 8.0, 2.0), "lunge": (-2.4, -1.4, -0.4), "hpitch": (18.0, 8.0, 2.0),
                    "gape": (0.5, 0.2, 0.0), "lights": (0.3, 0.6, 1.0), "squint": True},
    "levi_swim": {"kind": "wave", "n": 8, "amp": 26.0, "wl": 18.0, "vamp": 9.0, "bob": 0.25, "lights": 1.0, "lunge_amp": 0.4, "swim": True},
    "levi_sink": {"amp": (14.0, 12.0, 10.0, 8.0, 8.0, 8.0, 8.0, 8.0), "wl": (18.0,) * 8, "drop": (0.0, 0.1, 0.22, 0.36, 0.5, 0.62, 0.7, 0.74),
                  "hpitch": (12.0, 4.0, -4.0, -10.0, -14.0, -16.0, -16.0, -16.0), "gape": (0.4, 0.3, 0.2, 0.15, 0.1, 0.1, 0.1, 0.1),
                  "lights": (0.85, 0.7, 0.55, 0.4, 0.25, 0.1, 0.0, 0.0), "dissolve": (0.0, 0.0, 0.0, 0.0, 0.1, 0.25, 0.45, 0.7), "dead": 3},
}
STYLES.update(SKY_STYLES)
RIBBON = {
    "ribbon": True, "Z": 10.0, "n": 19, "length": 17.0, "w": (1.2, 0.3), "tall": 1.15, "fin": (0.62, 0.28), "paddle": (1.6, 1.25),
    "head": {"skull": ((1.3, 0.0, 0.1), (1.9, 1.05, 1.0)), "snout": ((2.9, 0.0, -0.1), (1.15, 0.78, 0.62)), "jaw": ((0.6, 0.0, -0.5), (1.95, 0.85, 0.36)),
             "eye": (1.95, 0.72, 0.35), "crown": 0.55, "gills": 3},
    "pectoral": ((0.2, 1.0, -0.4), (0.9, 0.12, 0.55)),
    "specks": 7, "clouds": True,
}
LEVIATHAN = {
    "leviathan": True, "Z": 15.0, "n": 18, "length": 24.0, "w": (3.9, 0.7), "tall": 1.05, "sweep": 20.0,
    "head": {"crown": ((3.2, 0.0, 0.8), (5.6, 3.9, 3.5)), "rostrum": ((7.4, 0.0, 0.2), (3.4, 3.0, 2.3)), "jaw": ((2.8, 0.0, -1.6), (6.0, 3.6, 2.0)),
             "hinge": (0.4, 0.0, -0.8), "eye": (4.8, 3.35, 0.5), "baleen": 15},
    "veils": {"dorsal": (0.15, 0.7, 3.0), "pectoral": ((1.4, 3.2, -1.8), 8.5, 3.4), "tail": ((5.5, 2.4), (7.5, 3.4), (5.8, 2.6))},
    "lights": 14,
    # Swimming: the water's line this far under its feet on the screen (art px: about the flier's hover over the ground,
    # EnemyAuthority._hover), the neck's height over it, the body's dip below the neck (degrees), the head
    # raised over the neck so its eye clears the water, the neck's place ahead of its feet (a share of its length), and
    # its length (its far body lost under the water, so the frame holds it facing away).
    "swim": {"lift": 3.0, "z": -1.3, "sweep": 16.0, "head": 1.1, "ahead": 0.15, "length": 0.72},
}
VARIANTS["ribbon"] = {"parts": RIBBON, "mats": {"skin": "neel_teal", "cloud": "neel_mag", "fin": "neel_fin", "mouth": "neel_mouth", "fang": "neel_fang"},
                      "motion": {"idle": "ribbon_drift", "walk": "ribbon_swim", "windup": "coil_gape", "attack": "lunge_bite", "hurt": "kink_jerk",
                                 "death": "unravel_fade"}}
VARIANTS["leviathan"] = {"parts": LEVIATHAN, "mats": {"skin": "nlev_hide", "belly": "nlev_belly", "teal": "nlev_teal", "mag": "nlev_mag",
                                                      "veil": "nlev_veil", "baleen": "nlev_baleen", "mouth": "nlev_mouth", "void": "nlev_void"},
                         "motion": {"idle": "levi_drift", "walk": "levi_glide", "windup": "void_gather", "attack": "void_breath", "hurt": "levi_recoil",
                                    "death": "levi_sink", "swim": "levi_swim"}}


def _sky_wave(B, action: str, f: int):
    """This frame's wave: (amp, wl, vamp, phase, bob, lunge)."""
    st = B.style(action)
    if st.get("kind") == "wave":
        n = st.n
        ph = f / n * math.tau
        lunge = st.get("lunge_amp", 0.0) * math.sin(ph)
        return st.amp, st.wl, st.vamp, ph, st.bob * math.sin(ph + 1.0), lunge
    ph = B.pick("phase", action, f) * math.tau
    return B.pick("amp", action, f), B.pick("wl", action, f, 10.0), B.pick("vamp", action, f, 4.0), ph, 0.0, B.pick("lunge", action, f)


def _sky_spine(n: int, length: float, amp: float, wl: float, vamp: float, ph: float, kink: float, sweep: float = 0.0):
    """The spine's points from the neck back (its own frame, the neck at the origin) and its unit tangents (pointing back):
    the heading's wave travelling from the head to the tail, growing from the neck; `kink` a jerk across its middle;
    `sweep` the body's fall below the neck (degrees, easing back up toward the tail)."""
    ds = length / (n - 1)
    q = v3(0.0, 0.0, 0.0)
    pts, tans = [q.copy()], []
    for i in range(n - 1):
        s = (i + 0.5) * ds
        grow = min(1.0, 0.25 + s / (0.45 * wl))
        y = math.radians(amp * grow * math.sin(math.tau * s / wl - ph) + kink * math.exp(-((s / length - 0.42) / 0.16) ** 2))
        p = math.radians(vamp * grow * math.sin(math.tau * s / (wl * 1.3) - ph * 0.8 + 1.1) - sweep * math.cos(math.pi * s / length))
        d = v3(-math.cos(p) * math.cos(y), -math.cos(p) * math.sin(y), math.sin(p))
        tans.append(d)
        q = q + d * ds
        pts.append(q.copy())
    tans.append(tans[-1])
    return pts, tans


def _frame_of(t):
    """An orthonormal frame (tangent, left, up) for a segment along `t`."""
    t = t / float(np.linalg.norm(t))
    left = np.cross(v3(0.0, 0.0, 1.0), t)
    if float(np.linalg.norm(left)) < 1e-6:
        left = v3(0.0, 1.0, 0.0)
    left = left / float(np.linalg.norm(left))
    up = np.cross(t, left)
    return np.stack([t, left, up], axis=1)


def _ribbon_paint(m, centre, F, s0: float, seed: int, clouds: bool):
    """The nebula eel's body: deep teal, its belly a step dark, magenta nebula clouds drifting over its back (blotches by
    the place along it), a lit line along its back."""
    def paint(q, n):
        d = (q - centre) @ F
        nl = n @ F
        along = s0 - d[:, 0]
        cloud = np.zeros(len(q), dtype=bool)
        if clouds:
            cloud = (nl[:, 2] > 0.1) & (h01v(np.floor(along * 0.9 + 50), np.floor((d[:, 1] + 3.0) * 0.8), seed % 89 + 4) > 0.55)
        belly = nl[:, 2] < -0.45
        ridge = (nl[:, 2] > 0.88) & ~cloud
        names = np.where(cloud, m.cloud, m.skin).astype(object)
        return names, np.where(belly, -1, np.where(ridge, 1, 0)).astype(np.int16)
    return paint


def _ribbon(B, action: str, f: int, view: float) -> Pose:
    """M4, the nebula eel (see SKY_STYLES): a ribbon body in an S-wave, translucent violet fins along its back and belly
    meeting in a paddle at its tail, a head with a hinged lower jaw (a dark violet gape, pale fangs), gill slits, a magenta
    crown and a glowing cyan eye. It coils back into a tight S as its jaws gape and its eyes flare (the tell, held), and
    lunges straight to bite (a void ripple before its snout on the blow); struck, its body kinks; beaten, it unravels from
    its tail into teal and magenta wisps that drift apart and fade."""
    P = Pose()
    p, m = B.parts, B.mats
    st = B.style(action)
    seed = int(B.opts.get("seed", 0))
    amp, wl, vamp, ph, bob, lunge = _sky_wave(B, action, f)
    rise = B.pick("rise", action, f)
    drop = B.pick("drop", action, f)
    kink = B.pick("kink", action, f)
    unravel = B.pick("unravel", action, f)
    z = (p.Z + rise + bob) * (1.0 - drop) + drop * 2.0
    neck = v3(lunge, 0.0, z)
    pts, tans = _sky_spine(p.n, p.length, amp, wl, vamp, ph, kink)
    pts = [neck + q + v3(p.length * 0.42, 0.0, 0.0) for q in pts]      # the body's middle over its feet
    neck = pts[0]
    n = p.n
    cut = int(round((n - 1) * (1.0 - unravel)))                       # the segments left as it unravels from the tail
    for i in range(n - 1):
        u = i / (n - 2)
        w = p.w[0] + (p.w[1] - p.w[0]) * u ** 1.3
        a, b = pts[i], pts[i + 1]
        c = (a + b) * 0.5
        F = _frame_of(b - a)
        seg = float(np.linalg.norm(b - a))
        if i >= cut:
            # Unravelled: teal and magenta wisps drifting apart from where it was.
            k0 = i - cut
            for j in range(3):
                off = v3(math.cos(i * 2.1 + j) * (1.0 + k0 * 0.6), math.sin(i * 1.7 + j) * (1.0 + k0 * 0.6), 0.5 + 0.4 * j + 0.3 * k0)
                P.fx.append((c + off, M.NEEL_WISP if (i + j) % 2 else M.NEEL_WISP_MAG))
            continue
        P.add(E(c, (seg * 0.62, w, w * p.tall), m.skin, "body", F, _ribbon_paint(m, c, F, p.length * u, seed, p.clouds)))
        fh = p.fin[0] + (p.fin[1] - p.fin[0]) * u
        for sgn in (1, -1):
            P.add(E(c + F @ v3(0.0, 0.0, sgn * (w * p.tall + fh * 0.55)), (seg * 0.6, 0.12, fh), m.fin, "fin", F, line=False))
        if i % 2 == 0 and i < cut - 1 and (i + f) % 3 != 0 and action != "death":
            P.glow.append((c + F @ v3(0.0, 0.0, w * p.tall + 0.1), M.STAR_W if (i + f) % 2 else M.STAR_C))
    if cut >= n - 1:
        tail = pts[-1]
        F = _frame_of(tans[-1])
        P.add(E(tail + F @ v3(p.paddle[0] * 0.5, 0.0, 0.0), (p.paddle[0], 0.12, p.paddle[1]), m.fin, "paddle", F, line=False))
    # The head: its heading the neck's (forward, opposite the body's first tangent), pitched by the channel.
    t0 = -tans[0]
    yaw = math.degrees(math.atan2(t0[1], t0[0]))
    hm = rot("c", yaw) @ rot("b", B.pick("hpitch", action, f))
    hd = p.head
    gape = B.pick("gape", action, f)
    flare = B.pick("flare", action, f)
    hc = neck + hm @ v3(0.0, 0.0, 0.0)
    P.add(E(hc + hm @ v3(hd.skull[0]), hd.skull[1], m.skin, "head", hm, _crown_paint(m, hc + hm @ v3(hd.skull[0]), hm, hd.crown)))
    P.add(E(hc + hm @ v3(hd.snout[0]), hd.snout[1], m.skin, "head", hm))
    jm = hm @ rot("b", -gape * 38.0)
    hinge = hc + hm @ v3(hd.jaw[0])
    P.add(E(hinge + jm @ v3(hd.jaw[1][0] * 0.9, 0.0, 0.0), hd.jaw[1], m.skin, "jaw", jm))
    if gape > 0.2:
        P.add(E(hinge + hm @ v3(1.6, 0.0, 0.15), (1.5, 0.7, 0.35 + 0.3 * gape), m.mouth, "maw", hm, line=False))
        for k in range(4):
            x = 0.9 + k * 0.6
            for sgn in (1, -1):
                P.mark(hinge + jm @ v3(x, sgn * 0.55, hd.jaw[1][2] + 0.1), M.FANG)
                P.mark(hc + hm @ v3(hd.snout[0][0] + x - 1.9, sgn * 0.55, -0.5), M.FANG)
    for sgn in (1, -1):
        for k in range(hd.gills):
            P.mark(hc + hm @ v3(-0.1 - k * 0.35, sgn * 0.98, -0.1 + 0.15 * k), M.RAMPS[m.skin][0])
        eye = hc + hm @ v3(*(hd.eye[0], sgn * hd.eye[1], hd.eye[2]))
        P.mark(eye + hm @ v3(-0.3, 0.0, 0.0), M.NEEL_SOCKET)
        if action == "death" and f >= st.get("dead", 99) or st.get("squint"):
            P.mark(eye, M.NEEL_SOCKET)
        else:
            P.eye(eye, M.NEEL_EYE)
            if flare >= 0.9:
                for d in ((0.5, sgn * 0.5, 0.6), (0.6, sgn * 0.9, 0.0), (0.5, sgn * 0.5, -0.5)):
                    P.glow.append((eye + hm @ v3(*d), M.NEEL_EYE))
    pe, pr = p.pectoral
    for sgn in (1, -1):
        pm = hm @ rot("c", sgn * 40.0)
        P.add(E(hc + hm @ v3(pe[0], sgn * pe[1], pe[2]) + pm @ v3(-pr[0] * 0.6, 0.0, 0.0), pr, m.fin, "pectoral", pm, line=False))
    # The void ripple before its snout on the blow; star specks scattering off it when struck.
    rip = B.pick("ripple", action, f)
    if rip > 0.0:
        c = hc + hm @ v3(hd.snout[0][0] + 1.8 + rip * 0.8, 0.0, 0.0)
        for k in range(12):
            ang = math.radians(k * 30.0)
            rr = 0.8 + rip * 0.9
            P.glow.append((c + hm @ v3(0.0, math.cos(ang) * rr, math.sin(ang) * rr), M.RIFT_V if k % 2 else M.RIFT_W))
    if f in st.get("specks", ()):
        for k in range(8):
            ang = math.radians(k * 45.0 + f * 20.0)
            c = pts[n // 2]
            P.glow.append((c + v3(math.cos(ang) * (2.0 + f), math.sin(ang) * (2.0 + f), 1.0 + (k % 3) * 0.5), M.STAR_W if k % 2 else M.STAR_C))
    d = B.pick("dissolve", action, f)
    if d > 0.0:
        P.dissolve = d
        P.dissolve_col = M.NEEL_WISP
    sq = st.get("squash", {}).get(f)
    if sq is not None:
        P.squash(sq[0], sq[1], sq[2], tuple(neck))
    return P


def _crown_paint(m, centre, hm, share: float):
    """The eel's head: a magenta patch over its crown's back half."""
    def paint(q, n):
        d = (q - centre) @ hm
        nl = n @ hm
        crown = (nl[:, 2] > share) & (d[:, 0] < 0.4)
        return np.where(crown, m.cloud, m.skin).astype(object), np.where(nl[:, 2] < -0.45, -1, 0).astype(np.int16)
    return paint


def _levi_paint(m, centre, F, s0: float, length: float):
    """The leviathan's hide: deep indigo over its back, its pale star-white belly in pleats, a teal band and a magenta band
    of nebula along each flank (waving along its length)."""
    def paint(q, n):
        d = (q - centre) @ F
        nl = n @ F
        along = s0 - d[:, 0]
        side = np.abs(nl[:, 1])
        wv = 0.12 * np.sin(along * 0.5)
        belly = nl[:, 2] < -0.35
        teal = (~belly) & (nl[:, 2] > -0.32 + wv) & (nl[:, 2] < 0.02 + wv) & (side > 0.4)
        mag = (~belly) & (nl[:, 2] >= 0.02 + wv) & (nl[:, 2] < 0.3 + wv) & (side > 0.35)
        pleat = belly & ((np.abs(d[:, 1]) * 2.2) % 1.0 < 0.25)
        names = np.where(belly, m.belly, np.where(teal, m.teal, np.where(mag, m.mag, m.skin))).astype(object)
        return names, np.where(pleat, -1, np.where((nl[:, 2] > 0.9) & ~belly, 1, 0)).astype(np.int16)
    return paint


def _veil(P, root, d_out, d_back, length: float, width: float, mat, group: str, flutter: float) -> None:
    """A translucent veil fin: a long thin plate from `root` out along `d_out`, its trailing edge back along `d_back`,
    waving."""
    d_out = d_out / float(np.linalg.norm(d_out))
    d_back = d_back - d_out * float(d_back @ d_out)
    d_back = d_back / max(1e-6, float(np.linalg.norm(d_back)))
    nrm = np.cross(d_out, d_back)
    F = np.stack([d_out, d_back, nrm], axis=1) @ rot("a", flutter)
    P.add(E(root + d_out * length * 0.5 + d_back * width * 0.35, (length * 0.55, width * 0.6, 0.14), mat, group, F, line=False,
            paint=lambda q, n, root=root, F=F: (np.full(len(q), mat, dtype=object),
                                                 np.where(((((q - root) @ F)[:, 0] * 1.6) % 1.0) < 0.2, -1, 0).astype(np.int16))))


def _leviathan(B, action: str, f: int, view: float, k: float = 2.6) -> Pose:
    """M4, the Nebula Leviathan (see SKY_STYLES): a colossal sky whale-serpent, a vast whale head (a domed crown over a
    rostrum, an arched mouth fringed with ivory baleen, a pleated lower jaw, a small ancient gold eye) on a serpent body
    sweeping back (deep indigo, a pale belly in pleats, teal and magenta nebula bands along its flanks, constellations of
    lights on its back), translucent violet veils (its pectorals, a long veil down its back, a fan at its tail). It rears
    its head back, its mouth gaping as the void gathers in it and star lines spiral in (the tell, held), and lunges to
    breathe the void (a cone of darkness full of stars ending in a burst); struck, it recoils and its lights flicker;
    beaten, its lights go out one by one as it sinks and fades. Swimming (`levi_swim`), it is drawn mostly under the
    water (see _levi_water)."""
    P = Pose()
    p, m = B.parts, B.mats
    st = B.style(action)
    amp, wl, vamp, ph, bob, lunge = _sky_wave(B, action, f)
    rise = B.pick("rise", action, f)
    drop = B.pick("drop", action, f)
    kink = B.pick("kink", action, f)
    lights = B.pick("lights", action, f, st.get("lights", 1.0))
    z = (p.Z + rise + bob) * (1.0 - drop) + drop * 4.0
    sweep = p.sweep
    swim = bool(st.get("swim"))
    if swim:
        P.water = -p.swim.lift / math.cos(ELEV)        # in the world, at its drawn size
        wz = P.water / k                               # in its own frame
        z, sweep = wz + p.swim.z + bob, p.swim.sweep
    length = p.length * (p.swim.length if swim else 1.0)
    pts, tans = _sky_spine(p.n, length, amp, wl, vamp, ph, kink, sweep)
    off = v3(lunge + length * (p.swim.ahead if swim else 0.3), 0.0, z)
    pts = [off + q for q in pts]
    neck = pts[0]
    n = p.n
    flutter = 10.0 * math.sin(f * 0.9)
    vl = p.veils
    bodies = []
    for i in range(n - 1):
        u = i / (n - 2)
        w = p.w[0] + (p.w[1] - p.w[0]) * u ** 1.1
        a, b = pts[i], pts[i + 1]
        c = (a + b) * 0.5
        F = _frame_of(b - a)
        seg = float(np.linalg.norm(b - a))
        P.add(E(c, (seg * 0.62, w, w * p.tall), m.skin, "body", F, _levi_paint(m, c, F, length * u, length)))
        bodies.append((c, F, w))
        # The long veil down its back, in short waving plates.
        if 0.15 < u < 0.85 and i % 2 == 0:
            fh = vl.dorsal[2] * (1.0 - abs(u - 0.5))
            P.add(E(c + F @ v3(0.0, 0.0, w * p.tall + fh * 0.5), (seg * 1.1, 0.14, fh), m.veil, "dorsal", F @ rot("a", flutter * 0.4), line=False))
    # The tail's veils: a fan of three long plates off its tip.
    tail = pts[-1]
    Ft = _frame_of(tans[-1])
    for j, (ln, wd) in enumerate(vl.tail):
        ang = (j - 1) * 34.0
        dout = Ft @ (rot("a", ang) @ v3(0.0, 0.0, 1.0)) * 0.55 + Ft @ v3(1.0, 0.0, 0.0)
        _veil(P, tail, dout, Ft @ v3(0.0, 0.0, -1.0), ln, wd, m.veil, "tailveil", flutter * (1 if j % 2 else -1))
    # The constellations: lights over its back, joined by faint lines, going out one by one as it dies.
    lit = int(round(p.lights * lights))
    stars = []
    for k in range(p.lights):
        c, F, w = bodies[min(len(bodies) - 1, 1 + k)]
        sd = (0.45 if k % 2 else -0.35) * w
        q = c + F @ v3(0.0, sd, w * p.tall * 0.92)
        stars.append(q)
        if k < lit:
            P.glow.append((q, M.STAR_W if k % 3 == 0 else (M.STAR_C if k % 3 == 1 else M.STAR_G)))
        else:
            P.mark(q, M.LEVI_STAR_OFF)
    for k in range(min(lit, len(stars)) - 1):
        P.mark((stars[k] + stars[k + 1]) * 0.5, M.LEVI_CLINE)
    # The head: the crown dome over the rostrum, the hinged pleated jaw, the arched mouth and its baleen, a gold eye.
    t0 = -tans[0]
    yaw = math.degrees(math.atan2(t0[1], t0[0]))
    hm = rot("c", yaw) @ rot("b", B.pick("hpitch", action, f))
    hd = p.head
    gape = B.pick("gape", action, f)
    hc = neck + v3(0.0, 0.0, p.swim.head if swim else 0.0)
    crown_c = hc + hm @ v3(hd.crown[0])
    P.add(E(crown_c, hd.crown[1], m.skin, "head", hm, _levi_head_paint(m, crown_c, hm)))
    P.add(E(hc + hm @ v3(hd.rostrum[0]), hd.rostrum[1], m.skin, "head", hm, _levi_head_paint(m, hc + hm @ v3(hd.rostrum[0]), hm)))
    jm = hm @ rot("b", -gape * 28.0)
    hinge = hc + hm @ v3(hd.hinge)
    jc = hinge + jm @ v3(np.asarray(hd.jaw[0]) - np.asarray(hd.hinge))
    P.add(E(jc, hd.jaw[1], m.belly, "jaw", jm, _pleats(m, jc, jm)))
    # The mouth: dark inside as it gapes, the baleen's ivory fringe hanging along the arch of the upper jaw.
    if gape > 0.15:
        P.add(E(hinge + hm @ v3(3.4, 0.0, 0.3), (3.6, 2.3, 0.5 + 1.2 * gape), m.mouth, "maw", hm, line=False))
    for k in range(hd.baleen):
        x = 1.6 + k * 0.52
        arch = 0.55 * math.sin(math.pi * k / (hd.baleen - 1))
        for sgn in (1, -1):
            q = hc + hm @ v3(x, sgn * (2.3 - 0.06 * k), -0.85 + arch)
            P.add(L(q, q + hm @ v3(0.0, 0.0, -0.55 - 0.4 * gape), 0.22, 0.14, m.baleen, "baleen", line=False))
    for sgn in (1, -1):
        eye = hc + hm @ v3(hd.eye[0], sgn * hd.eye[1], hd.eye[2])
        for d in ((-0.4, 0.0, 0.45), (-0.5, 0.0, -0.4), (-0.8, 0.0, 0.0)):
            P.mark(eye + hm @ v3(*d), M.RAMPS[m.skin][1])
        if action == "death" and f >= st.get("dead", 99) or st.get("squint"):
            P.mark(eye, M.RAMPS[m.skin][0])
        else:
            P.eye(eye, M.LEVI_EYE)
    # The pectoral veils: great translucent fins off its throat, sweeping back like wings.
    (pa, pb, pc), pl, pw = vl.pectoral
    for sgn in (1, -1):
        root = hc + hm @ v3(pa, sgn * pb, pc)
        dout = hm @ v3(-0.55, sgn * 0.75, -0.25 + 0.15 * math.sin(f * 0.9 + sgn))
        _veil(P, root, dout, hm @ v3(-1.0, 0.0, 0.0), pl, pw, m.veil, "pectoral%d" % sgn, flutter * sgn)
    # The void gathering in its mouth (a dark orb rimmed in violet light) as star lines spiral into it; the breath.
    vd = B.pick("void", action, f)
    mouth = hc + hm @ v3(6.0, 0.0, -0.3)
    if vd > 0.0:
        r = 0.8 + 1.6 * vd
        P.add(S(mouth, r, m.void, "void", line=False))
        for k in range(16):
            ang = math.radians(k * 22.5 + f * 30.0)
            P.glow.append((mouth + v3(0.0, math.cos(ang) * (r + 0.4), math.sin(ang) * (r + 0.4)), M.LEVI_VOID_RIM if k % 2 else M.LEVI_VOID_HI))
        if st.get("spiral"):
            for arm in range(3):
                for k in range(7):
                    t = k / 6.0
                    ang = math.radians(arm * 120.0 + f * 40.0 + t * 260.0)
                    rr = (r + 1.0) + (1.0 - t) * 7.0
                    P.glow.append((mouth + v3(math.cos(ang) * rr * 0.5, math.sin(ang) * rr, math.cos(ang * 1.3) * rr * 0.4),
                                   M.STAR_W if k % 3 == 0 else M.LEVI_VOID_RIM))
    br = B.pick("breath", action, f)
    if br > 0.0:
        fwd = hm @ v3(1.0, 0.0, 0.0)
        reach = 3.0 + 4.0 * br
        for k in range(7):
            t = k / 6.0
            q = mouth + fwd * (1.5 + reach * t)
            r = 0.9 + 2.2 * t
            P.add(S(q, r, m.void, "breath", line=False))
            for j in range(3):
                ang = math.radians(j * 120.0 + k * 50.0 + f * 30.0)
                P.glow.append((q + hm @ v3(0.0, math.cos(ang) * r * 0.6, math.sin(ang) * r * 0.6), M.STAR_W if (j + k) % 2 else M.STAR_C))
        end = mouth + fwd * (1.5 + reach)
        rb = 2.6 + 1.2 * br
        for k in range(18):
            ang = math.radians(k * 20.0)
            P.glow.append((end + hm @ v3(0.3, math.cos(ang) * rb, math.sin(ang) * rb), M.LEVI_VOID_HI if k % 2 else M.LEVI_VOID_RIM))
    d = B.pick("dissolve", action, f)
    if d > 0.0:
        P.dissolve = d
        P.dissolve_col = M.STAR_C
    sq = st.get("squash", {}).get(f)
    if sq is not None:
        P.squash(sq[0], sq[1], sq[2], tuple(neck))
    if swim:
        _levi_water(P, B, f, wz, bodies, hc, hm)
    return P


def _levi_water(P, B, f: int, wz: float, bodies: list, hc, hm) -> None:
    """The Nebula Leviathan swimming: everything of it under the water's line cut away (its parts clipped at the
    surface, its lights and marks under it gone), and the star-water round it (P.water_fx): a darker wash over its body
    under the surface with stars glinting in it, foam where its head and the loops of its back break the water, a wake
    spreading back from its head in a V, a ring spreading round its head."""
    under = lambda q: q[:, 2] > wz
    for part in P.parts:
        part.clip = under if part.clip is None else (lambda q, c0=part.clip: under(q) & c0(q))
    P.glow = [g for g in P.glow if g[0][2] > wz]
    P.marks = [g for g in P.marks if g[0][2] > wz]
    P.eyes = [g for g in P.eyes if g[0][2] > wz]
    P.fx = [g for g in P.fx if g[0][2] > wz]
    # Where it breaks the surface: each piece of the body whose back rises over the water, and the head.
    breaks = [(c[0], c[1], w * 0.85) for c, F, w in bodies if c[2] + w * B.parts.tall > wz + 0.2 and c[2] - w < wz]
    ha, hb = float(hc[0] + (hm @ v3(3.4, 0.0, 0.0))[0]), float(hc[1] + (hm @ v3(3.4, 0.0, 0.0))[1])
    back = -(hm @ v3(1.0, 0.0, 0.0))[:2]
    back = back / max(1e-6, float(np.linalg.norm(back)))
    side = np.array((-back[1], back[0]))
    spine = [(float(c[0]), float(c[1]), w) for c, F, w in bodies]
    ring = 6.0 + (f % 8) * 0.5
    tan = math.tan(math.radians(17.0))

    def water(a, b):
        q = np.array((a - ha, b - hb))
        da, ds = float(q @ back), float(q @ side)
        dh = math.hypot(a - ha, b - hb)
        if dh < 5.4:
            ang = int((math.degrees(math.atan2(b - hb, a - ha)) + 360.0) // 24.0)
            return M.LEVI_FOAM if h01(ang, f, 23) > 0.35 else M.LEVI_RIPPLE
        for ba, bb, br in breaks:
            if math.hypot(a - ba, b - bb) < br + 0.8:
                return M.LEVI_FOAM if h01(int(a * 3.0 + b * 7.0), f, 29) > 0.45 else M.LEVI_RIPPLE
        # The wake: two lines spreading back from its head, a step behind it.
        if 2.0 < da < 15.0 and abs(abs(ds) - (3.4 + da * tan)) < 0.45:
            return M.LEVI_RIPPLE if da < 9.0 else M.LEVI_RIPPLE_DIM
        if abs(dh - ring) < 0.42 and da < 0.0:
            return M.LEVI_RIPPLE_DIM
        near = min((math.hypot(a - sa, b - sb) - sw for sa, sb, sw in spine), default=99.0)
        if near < 1.4:
            return M.LEVI_GLINT if h01(int(a * 2.0) * 31 + int(b * 2.0), 0, 37) > 0.93 else M.LEVI_WASH
        return None

    P.water_fx = water


def _levi_head_paint(m, centre, hm):
    """The whale head: indigo over its dome with a teal and a magenta band of nebula along its sides above the mouth."""
    def paint(q, n):
        nl = n @ hm
        side = np.abs(nl[:, 1])
        teal = (nl[:, 2] > -0.25) & (nl[:, 2] < 0.08) & (side > 0.45)
        mag = (nl[:, 2] >= 0.08) & (nl[:, 2] < 0.32) & (side > 0.4)
        names = np.where(teal, m.teal, np.where(mag, m.mag, m.skin)).astype(object)
        return names, np.where(nl[:, 2] > 0.9, 1, 0).astype(np.int16)
    return paint


def _pleats(m, centre, jm):
    """The pleated throat of its lower jaw: lines along it a step dark."""
    def paint(q, n):
        d = (q - centre) @ jm
        pleat = (np.abs(d[:, 1]) * 1.6) % 1.0 < 0.22
        return np.full(len(q), m.belly, dtype=object), np.where(pleat, -1, 0).astype(np.int16)
    return paint

# ================================================================================================= the dune worm (M3)
# The dune worm (`mound`): a giant burrowing sand worm of the Worm Sea, only ever seen rising out of the sand to strike
# (the room view shows a travelling mound while it is under). Its body a tube out of a mound of sand through key control
# points (its side-view sheet's): overlapping armour rings of dusky ochre, each flaring to a lit lip toward its head, dark
# sand crust packed in the seams, the pale ridged underbelly down its front; no eyes, a few glassy sense pits on its head
# plates; at its end the round lamprey mouth (an armoured lip collar, the deep red maw, a ring of clear desert-glass
# teeth and a smaller ring inside it, the dark throat); sand pouring off it.
#
# Its styles give key poses (five control points (along, up) a frame, the first under the sand) or a kind: `sway` (the
# idle, standing out of its mound swaying), `surge` (the walk, low, its front swinging as it ploughs on). Channels:
# `gape` (the mouth, 0..1), `pits` (the sense pits' flare), `burst` (sand bursting round its mound), `blast` (the sand
# explosion of its slam, the blow), `chips` (plate shards when struck), `sink` (0..1: sunk back into the sand), `fade`.
_WI = ((0.0, -2.5), (0.2, 3.0), (0.2, 7.6), (1.5, 11.0), (3.3, 11.4))
_WW = ((0.0, -2.5), (0.6, 2.2), (1.6, 5.4), (3.2, 7.2), (5.0, 7.4))
_WR = ((0.0, -2.5), (-0.4, 4.0), (-1.0, 10.2), (-0.6, 15.5), (1.0, 18.4))
_WH = ((0.0, -2.5), (-0.4, 3.0), (-1.4, 7.2), (-1.6, 11.0), (-0.6, 12.8))
_WD = ((0.0, -2.5), (1.2, 2.0), (4.0, 3.2), (7.6, 2.6), (10.4, 1.4))
WORM_STYLES = {
    "worm_sway": {"kind": "sway", "gape": (0.35,) * 6},
    "worm_surge": {"kind": "surge", "gape": (0.5,) * 8},
    "worm_rear": {"keys": (((0.0, -2.5), (0.1, 3.4), (-0.2, 8.5), (0.6, 12.6), (2.4, 14.6)),
                           ((0.0, -2.5), (-0.1, 3.8), (-0.6, 9.5), (-0.1, 14.2), (1.6, 16.6)),
                           ((0.0, -2.5), (-0.3, 4.0), (-0.9, 10.0), (-0.5, 15.2), (1.1, 18.0)), _WR),
                  "gape": (0.5, 0.75, 0.95, 1.0), "pits": (0.5, 1.0, 1.5, 2.0), "burst": (0.4, 0.7, 1.0, 1.0)},
    "worm_slam": {"keys": (_WR, ((0.0, -2.5), (0.8, 4.0), (3.6, 8.0), (7.6, 8.2), (10.6, 3.6)),
                           ((0.0, -2.5), (0.8, 4.0), (3.4, 7.8), (7.2, 7.8), (10.0, 3.4)),
                           ((0.0, -2.5), (0.6, 3.8), (2.4, 8.4), (5.0, 10.0), (7.4, 8.8)),
                           ((0.0, -2.5), (0.4, 3.4), (1.0, 8.0), (2.6, 11.0), (4.8, 11.8)), _WI),
                  "gape": (1.0, 1.0, 0.7, 0.5, 0.4, 0.35), "blast": (0.0, 1.0, 0.6, 0.25, 0.0, 0.0), "pits": (2.0, 1.0, 0.0, 0.0, 0.0, 0.0)},
    "worm_recoil": {"keys": (_WH, ((0.0, -2.5), (-0.2, 3.0), (-0.8, 7.4), (-0.4, 11.2), (1.0, 12.9)),
                             ((0.0, -2.5), (0.1, 3.0), (-0.2, 7.5), (0.6, 11.2), (2.4, 12.9))),
                    "gape": (0.8, 0.5, 0.4), "chips": (1.0, 0.6, 0.3), "burst": (0.6, 0.3, 0.0)},
    "worm_sink": {"keys": (_WH, ((0.0, -2.5), (0.4, 3.0), (1.4, 7.0), (3.6, 9.6), (6.0, 10.0)),
                           ((0.0, -2.5), (0.8, 2.6), (3.0, 5.6), (6.4, 6.4), (9.0, 5.0)), _WD, _WD, _WD, _WD, _WD),
                  "gape": (0.8, 0.6, 0.4, 0.3, 0.2, 0.2, 0.2, 0.2), "sink": (0.0, 0.0, 0.0, 0.0, 0.25, 0.5, 0.75, 0.95),
                  "burst": (0.0, 0.0, 0.0, 0.8, 0.5, 0.3, 0.1, 0.0), "fade": (0.0, 0.0, 0.0, 0.0, 0.0, 0.25, 0.55, 0.85), "dark_from": 3},
}
STYLES.update(WORM_STYLES)
WORM = {
    "mound": {"r": (4.8, 4.6, 1.7)},
    "body": {"r": (2.15, 1.85), "ring": 1.05, "n": 40},
    "mouth": {"teeth": 9, "inner": 5},
    "pits": 4,
}
VARIANTS["worm"] = {"parts": WORM, "mats": {"armour": "dw_armour", "belly": "dw_belly", "crust": "dw_crust", "sand": "dw_sand",
                                            "glass": "dw_glass", "maw": "dw_maw"},
                    "motion": {"idle": "worm_sway", "walk": "worm_surge", "windup": "worm_rear", "attack": "worm_slam",
                               "hurt": "worm_recoil", "death": "worm_sink"}}


def _worm(B, action: str, f: int, view: float) -> Pose:
    """M3, the dune worm (see WORM_STYLES): standing out of its mound, swaying, sand pouring off it; low, its front swinging
    as it ploughs on; in its tell it rears up tall (about twice a person), its mouth gaping to show its glass teeth, its
    sense pits flaring cyan, the sand bursting round its mound; it lunges forward and down onto its foe in an explosion
    of sand; struck, it recoils and its plates chip; beaten, it topples forward, goes slack and sinks back into the sand,
    its mound collapsing."""
    P = Pose()
    p, m = B.parts, B.mats
    st = B.style(action)
    gape = B.pick("gape", action, f, 0.35)
    pits = B.pick("pits", action, f)
    burst = B.pick("burst", action, f)
    blast = B.pick("blast", action, f)
    chips = B.pick("chips", action, f)
    sink = B.pick("sink", action, f)
    fade = B.pick("fade", action, f)
    dead = action == "death" and f >= st.get("dark_from", 99)
    kind = st.get("kind")
    yy = [0.0] * 5
    if kind == "sway":
        ph = f / 6.0 * math.tau
        keys = [(x + 0.7 * math.sin(ph) * (i / 4.0) ** 1.5, z) for i, (x, z) in enumerate(_WI)]
        yy = [0.6 * math.sin(ph + 1.2) * (i / 4.0) ** 1.5 for i in range(5)]
    elif kind == "surge":
        ph = f / 8.0 * math.tau
        keys = [(x + 0.9 * math.sin(ph) * (i / 4.0), z + 0.6 * math.sin(ph + 1.0) * (i / 4.0)) for i, (x, z) in enumerate(_WW)]
        yy = [1.4 * math.sin(ph + 0.6 * i) * (i / 4.0) for i in range(5)]
    else:
        keys = st["keys"][f]
    pts = [v3(x, yy[i], z - 4.0 * sink * (i > 0)) for i, (x, z) in enumerate(keys)]
    bd = p.body
    spine = _spline(pts, bd.n)
    # The tube: armour rings at every `ring` along the spine, each a band oriented along it; its tail end flared into a lit
    # lip over the ring behind it, dark sand crust packed in the seam under the lip, the pale ridged underbelly down its
    # front (the side its spine bends toward).
    seg = [float(np.linalg.norm(spine[i + 1] - spine[i])) for i in range(len(spine) - 1)]
    total = sum(seg)
    rings = []
    s_at, j, acc = 0.6, 0, 0.0
    while s_at < total - 0.2:
        while j < len(seg) - 1 and acc + seg[j] < s_at:
            acc += seg[j]
            j += 1
        t = (s_at - acc) / (seg[j] or 1.0)
        q = spine[j] + (spine[j + 1] - spine[j]) * t
        T = spine[j + 1] - spine[j]
        T = T / (float(np.linalg.norm(T)) or 1.0)
        u = s_at / total
        rings.append((q, T, bd.r[0] + (bd.r[1] - bd.r[0]) * u))
        s_at += bd.ring
    hl = bd.ring * 0.62

    def under(qq):
        return qq[:, 2] > -0.05

    for i, (q, T, r) in enumerate(rings):
        if q[2] + r < -0.2:
            continue
        side = v3(0.0, 1.0, 0.0)
        Nv = np.cross(T, side)
        Nv = Nv / (float(np.linalg.norm(Nv)) or 1.0)       # the belly's side: ahead of the spine, under it where it lies
        if float(Nv @ v3(1.0, 0.0, 0.0)) < 0.0 and float(Nv @ v3(0.0, 0.0, -1.0)) < 0.3:
            Nv = -Nv
        mm = np.stack([T, side, np.cross(T, side)], axis=1)

        def armour(qq, n, Nv=Nv, lit=0):
            belly = (n @ Nv) > 0.5
            names = np.where(belly, m.belly, m.armour).astype(object)
            return names, np.where(belly, -1 + lit, lit - 1).astype(np.int16)

        P.add(E(q, (hl, r, r), m.armour, "body", mm, armour, under))
        P.add(E(q - T * hl * 0.72, (hl * 0.32, r * 1.15, r * 1.15), m.armour, "body", mm, lambda qq, n, Nv=Nv: armour(qq, n, Nv, 1), under))
        P.add(E(q - T * hl * 1.02, (hl * 0.16, r * 1.0, r * 1.0), m.crust, "body", mm, None, under))
    # The head: the last ring's end, the mouth facing along the spine: the armoured lip collar, the deep red maw filling
    # it, glass teeth round it and a few inside, the dark throat.
    q, T, r = rings[-1]
    side = v3(0.0, 1.0, 0.0)
    up = np.cross(T, side)
    up = up / (float(np.linalg.norm(up)) or 1.0)
    side = np.cross(up, T)
    hm = np.stack([T, side, up], axis=1)
    mc = q + T * hl
    P.add(E(mc, (0.4, r * 1.12, r * 1.12), m.armour, "collar", hm))
    g = 0.75 + 0.25 * gape
    rm = r * 0.9 * g
    P.add(E(mc + T * 0.3, (0.14, rm, rm), m.maw, "maw", hm, line=False))
    P.add(E(mc + T * 0.34, (0.1, rm * 0.32, rm * 0.32), m.crust, "throat", hm, line=False))
    mo = p.mouth
    for ring_, nt, rr in ((0, mo.teeth, 0.72), (1, mo.inner, 0.45)):
        for k in range(nt):
            a = math.radians(k * 360.0 / nt + 20.0 * ring_)
            tq = mc + T * 0.46 + hm @ v3(0.0, math.cos(a) * rm * rr, math.sin(a) * rm * rr)
            P.mark(tq, M.DW_TOOTH if (k + ring_) % 2 == 0 or gape > 0.6 else M.DW_GLINT)
    # The sense pits on its head plates: glassy, flaring cyan in its tell.
    if not dead:
        for k in range(p.pits):
            a = math.radians(-50.0 + 33.0 * k)
            pq = q - T * 0.2 + hm @ v3(0.0, math.sin(a) * r * 0.95, math.cos(a) * r * 0.95) * 1.04
            P.mark(pq, M.DW_PIT_HOT if pits >= 1.0 else M.DW_PIT)
            if pits >= 1.0:
                P.glow.append((pq + up * 0.4, M.DW_PIT_GLOW))
    # The mound it rises from (collapsing as it sinks), its ripples.
    mr = p.mound.r
    mrr = (mr[0], mr[1], mr[2] * (1.0 - 0.7 * sink))

    def sand(qq, n):
        rr_ = np.hypot(qq[:, 0], qq[:, 1])
        ripple = ((rr_ * 1.3) % 1.0) < 0.2
        return np.full(len(qq), m.sand, dtype=object), np.where(ripple & (n[:, 2] > 0.4), -1, 0).astype(np.int16)

    P.add(E(v3(0.0, 0.0, 0.0), mrr, m.sand, "mound", None, sand))
    # Sand pouring off it; bursting round its mound; the explosion of its slam; plate shards when struck.
    if action in ("idle", "walk", "windup") or (action == "hurt"):
        for k in range(8):
            u = (k * 0.23 + f * 0.17) % 1.0
            j = int((k * 7) % (len(rings) - 4)) + 3
            rq, _, rr_ = rings[j]
            sgn = 1.0 if k % 2 else -1.0
            P.fx.append((rq + v3(0.0, sgn * (rr_ + 0.4), -u * 3.0), M.DW_SAND if u < 0.6 else M.DW_SAND_DIM))
    if burst > 0.0:
        for k in range(16):
            a = math.radians(k * 22.5 + f * 11.0)
            rr_ = mr[0] + 0.6 + 1.4 * burst * ((k % 3) / 2.0)
            hz = 0.5 + 2.5 * burst * ((k * 5) % 4) / 3.0
            P.fx.append((v3(math.cos(a) * rr_, math.sin(a) * rr_, hz), M.DW_SAND if k % 2 else M.DW_SAND_DIM))
    if blast > 0.0:
        hit = v3(pts[-1][0] + 0.6, 0.0, 0.0)
        for k in range(24):
            a = math.radians(k * 15.0)
            rr_ = 1.8 + 3.2 * blast * (0.6 + 0.4 * ((k * 7) % 3) / 2.0)
            hz = 0.4 + 3.0 * blast * ((k * 3) % 4) / 3.0
            P.fx.append((hit + v3(math.cos(a) * rr_, math.sin(a) * rr_, hz), M.DW_SAND if k % 3 else M.DW_SAND_DIM))
        for k in range(6):
            a = math.radians(k * 60.0 + 30.0)
            P.add(E(hit + v3(math.cos(a) * 2.2 * blast, math.sin(a) * 2.2 * blast, 0.3), (0.9, 0.8, 0.5 * blast + 0.2), m.sand, "blast", None))
    if chips > 0.0:
        for k in range(7):
            j = len(rings) - 2 - k
            rq, _, rr_ = rings[max(0, j)]
            a = math.radians(k * 51.0)
            P.fx.append((rq + v3(math.cos(a) * (rr_ + 1.0 + 1.5 * (1.0 - chips)), math.sin(a) * (rr_ + 1.0), 0.5), M.RAMPS[m.armour][4 if k % 2 else 3]))
    if fade > 0.0:
        P.dissolve = fade
        P.dissolve_col = M.DW_SAND
    return P

