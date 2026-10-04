"""The insect plan (M4): a flying insect held in the air over the floor (a flyer: the room view's shadow under it), a
body along its length and two pairs of wings off its back. Made for the Hollow's drones (`drone`) and the orbit moth
(`moth`).

`drone` (the hollow drone): not a wasp and not a beetle, a Hollow construct. A smooth spindle of gunmetal in three
riveted sections (`shell`: a rear cone, a mid section, a darker front cowl, their seams and rivets), a long needle lance
before it (`lance`: pale steel, its tip bright, telescoping out on the blow), two small vanes at its back, two pairs of
pale wings beating too fast to see (each drawn at the two ends of its beat, the far end its ghost), the sickly violet
core light in its mid section with ash-white fissures spreading from it (`core`), and one empty white Hollow eye on the
cowl. It hovers with a jittery buzz; in its tell it pulls back and levels its lance as its core flares in a violet glow
(held); it thrusts (a violet spark at the lance's tip on the blow); struck, sparks spit off it; beaten, its core bursts
and its shell comes apart into grey flakes that fall and fade.

`moth` (the orbit moth): a large soft moth whose wings are a map of the night sky: a fuzzy pale body (a fur collar, a
banded abdomen, a round head with big dark eyes), feathered gold antennae, two pairs of dusky indigo wings (`wings`: a
rose fringe along their outer margins, a pale leading edge, a star chart of pale-gold stars joined by gold lines, one
bright four-point star on each forewing), and three teal-white motes orbiting it (`motes`). Its wings beat slow; in its
tell they lift and spread wide as it rears back and the motes gather into a glowing knot before its head (held); they
snap down and a burst of star dust sprays forward (the blow); struck, it flinches in a puff of dust; beaten, its wings
fold and it spirals down as its motes wink out, and fades.

Channels: `lunge`, `rise` (over its height), `pitch` (+ nose up), `roll`, `yaw`, `beat` (the wings' beat: their
elevation, degrees, else the loop's), `spread` (0..1: the wings opened wide and up, the moth's tell), `fold` (0..1: folded
back along the body), `lance` (its reach, 1 at rest), `core` (the drone's light: 0 dark .. 2 flaring), `knot` (the
moth's motes gathered before its head, 0..1), `burst` (the spray or the spark on the blow, how far it has spread),
`drop` (fallen to the floor), `flakes` (0..1: the drone's shell coming apart), `dissolve`, `squint`.

The motion styles (STYLES): the drone's idle `buzz`, walk `dart`, windup `level_lance`, attack `lance_thrust`, hurt
`spark_jolt`, death `shell_burst`; the moth's idle `flutter`, walk `cruise`, windup `motes_gather`, attack `dust_burst`,
hurt `flinch_puff`, death `spiral_fall`.

M5's `swarm` (the Copperjaw swarm, and its Queen's sheet with `queen`): a cloud of small copper beetles, each sculpted (its
own place, size and loop in the cloud); styles idle `hang`, walk `stream`, windup `ball_up`, attack `lance`, hurt
`scatter`, death `rain` (below, with its channels).
"""
from __future__ import annotations

import math

import numpy as np

from .. import mats as M
from ..sculpt import E, L, Pose, S, rot, v3
from .kit import collapse

STYLES = {
    # the drone
    "buzz": {"kind": "buzz", "jitter": 0.25, "beat_amp": 26.0},
    "dart": {"kind": "buzz", "jitter": 0.3, "beat_amp": 30.0, "pitch": -8.0,
             "lunge": (0.0, 0.6, 1.4, 1.6, 1.0, 0.4, 0.0, -0.2), "streaks": (1, 2, 3)},
    "level_lance": {"lunge": (-0.6, -1.2, -1.6, -1.8), "rise": (0.3, 0.6, 0.8, 0.8), "pitch": (-4.0, -8.0, -10.0, -10.0),
                    "core": (1.2, 1.6, 2.0, 2.0), "beat_amp": 30.0, "lance": (1.0, 1.0, 1.0, 1.0), "halo": True},
    "lance_thrust": {"lunge": (0.6, 3.6, 3.8, 2.8, 1.4, 0.4), "rise": (0.4, -0.8, -0.9, -0.6, -0.2, 0.0), "pitch": (-6.0, -14.0, -12.0, -6.0, -2.0, 0.0),
                     "lance": (1.2, 1.6, 1.55, 1.35, 1.15, 1.0), "core": (2.0, 1.6, 1.2, 1.0, 1.0, 1.0), "burst": (0.0, 1.0, 1.6, 0.0, 0.0, 0.0),
                     "beat_amp": 30.0, "streaks": (0, 1), "squash": {1: (1.06, 0.97, 0.97)}},
    "spark_jolt": {"lunge": (-2.2, -1.2, -0.4), "rise": (0.6, 0.3, 0.1), "pitch": (16.0, 6.0, 0.0), "roll": (14.0, 6.0, 0.0),
                   "core": (0.3, 0.7, 1.0), "sparks": (0, 1), "beat_amp": 18.0, "squint": True},
    "shell_burst": {"core": (2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0), "burst": (1.4, 2.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                    "flakes": (0.0, 0.1, 0.3, 0.5, 0.7, 0.85, 1.0, 1.0), "drop": (0.0, 0.2, 0.45, 0.7, 0.9, 1.0, 1.0, 1.0),
                    "roll": (10.0, 30.0, 60.0, 80.0, 90.0, 90.0, 90.0, 90.0), "dissolve": (0.0, 0.0, 0.0, 0.0, 0.1, 0.3, 0.55, 0.8),
                    "beat_amp": 0.0, "dead": True},
    # the moth
    "flutter": {"kind": "flap", "beat_base": 8.0, "beat_amp": 24.0, "bob": 0.5},
    "cruise": {"kind": "flap", "beat_base": 4.0, "beat_amp": 34.0, "bob": 0.8, "pitch": -6.0, "lunge": (0.0, 0.3, 0.6, 0.6, 0.3, 0.0, -0.2, -0.1)},
    "motes_gather": {"lunge": (-0.4, -0.9, -1.2, -1.3), "rise": (0.4, 0.9, 1.2, 1.3), "pitch": (8.0, 14.0, 18.0, 18.0),
                     "spread": (0.4, 0.75, 1.0, 1.0), "knot": (0.3, 0.6, 0.9, 1.0), "glare": True},
    "dust_burst": {"lunge": (-0.6, 1.4, 1.6, 1.0, 0.4, 0.0), "rise": (1.0, -0.4, -0.4, -0.1, 0.1, 0.0), "pitch": (14.0, -8.0, -6.0, -2.0, 0.0, 0.0),
                   "beat": (70.0, -34.0, -30.0, -10.0, 6.0, 8.0), "knot": (1.0, 0.0, 0.0, 0.0, 0.0, 0.0), "burst": (0.0, 1.0, 1.6, 2.2, 0.0, 0.0),
                   "squash": {1: (1.03, 1.0, 0.97)}},
    "flinch_puff": {"lunge": (-2.0, -1.2, -0.4), "rise": (0.6, 0.3, 0.1), "pitch": (16.0, 6.0, 0.0), "beat": (60.0, 30.0, 12.0),
                    "puff": (0, 1), "squint": True},
    "spiral_fall": {"beat": (40.0, 20.0, 0.0, -10.0, -14.0, -14.0, -14.0, -14.0), "fold": (0.0, 0.2, 0.45, 0.7, 0.85, 0.9, 0.9, 0.9),
                    "drop": (0.0, 0.12, 0.3, 0.55, 0.8, 1.0, 1.0, 1.0), "roll": (10.0, 35.0, 60.0, 50.0, 30.0, 20.0, 20.0, 20.0),
                    "yaw": (0.0, 40.0, 90.0, 140.0, 170.0, 180.0, 180.0, 180.0), "dissolve": (0.0, 0.0, 0.0, 0.0, 0.15, 0.35, 0.6, 0.85),
                    "dead": True, "motes_out": (1, 3, 5)},
}

DRONE = {
    "Z": 11.0,
    "shell": {"rear": ((-2.7, 0.0, 0.0), (2.1, 1.2, 1.2)), "mid": ((-0.2, 0.0, 0.0), (1.75, 1.6, 1.6)), "cowl": ((1.75, 0.0, 0.0), (1.5, 1.28, 1.28)),
              "seams": (-1.45, 0.75), "rivets": 6},
    "lance": {"root": 2.9, "length": 4.6, "r": (0.45, 0.08)},
    "vanes": {"at": (-3.6, 0.0, 0.3), "r": (1.0, 0.18, 0.7), "splay": 34.0},
    "wings": {"at": ((0.3, 0.0, 1.35), (-0.9, 0.0, 1.25)), "r": ((2.0, 0.55), (1.6, 0.5)), "sweep": (46.0, 68.0), "beat": (58.0, 16.0)},
    "core": {"at": (-0.2, 0.0, 0.0), "r": 0.9, "fissures": 5},
    "eye": (2.85, 0.7, 0.4),
}
MOTH = {
    "Z": 11.5,
    "body": {"thorax": ((0.0, 0.0, 0.0), (1.35, 1.25, 1.2)), "collar": ((0.5, 0.0, 0.25), 1.15, 8), "abdomen": ((-2.3, 0.0, -0.3), (2.0, 1.05, 1.0)),
             "bands": 4, "head": ((1.55, 0.0, 0.15), 0.85), "eye": (0.45, 0.55, 0.1)},
    "antennae": {"root": (1.9, 0.35, 0.6), "tip": (3.2, 2.2, 2.6), "barbs": 5},
    "wings": {"fore": ((0.4, 0.9, 0.5), 5.8, 4.2, 34.0), "hind": ((-0.7, 0.8, 0.3), 4.4, 3.6, 110.0), "fringe": 0.74,
              "stars": (((0.25, 0.1), (0.5, -0.25), (0.75, 0.15), (0.55, 0.45)), ((0.35, 0.0), (0.7, 0.2), (0.6, -0.35)))},
    "motes": {"n": 3, "orbit": 5.2, "tilt": 22.0},
}
VARIANTS = {
    "drone": {"parts": DRONE, "mats": {"shell": "hd_shell", "lance": "hd_lance", "wing": "hd_wing", "ghost": "hd_ghost"},
              "motion": {"idle": "buzz", "walk": "dart", "windup": "level_lance", "attack": "lance_thrust", "hurt": "spark_jolt",
                         "death": "shell_burst"}},
    "moth": {"parts": MOTH, "mats": {"wing": "om_wing", "fringe": "om_fringe", "fur": "om_fur", "antenna": "om_antenna", "eye": "om_eye"},
             "motion": {"idle": "flutter", "walk": "cruise", "windup": "motes_gather", "attack": "dust_burst", "hurt": "flinch_puff",
                        "death": "spiral_fall"}},
}


def pose(B, action: str, f: int, view: float = 48.0) -> Pose:
    if "beetles" in B.parts:
        return _swarm(B, action, f, view)                # M5: the Copperjaw swarm (its Queen's too)
    if "lance" in B.parts:
        return _drone(B, action, f, view)
    return _moth(B, action, f, view)


def _frame(B, action: str, f: int):
    """The body's place and turn over the floor this frame: (C, bm, beat elevation, the loop's phase)."""
    p, st = B.parts, B.style(action)
    lunge = B.pick("lunge", action, f, 0.0)
    rise = B.pick("rise", action, f)
    pitch = B.pick("pitch", action, f, st.get("pitch", 0.0))
    roll = B.pick("roll", action, f)
    yaw = B.pick("yaw", action, f)
    drop = B.pick("drop", action, f)
    n = 6 if action == "idle" else 8
    ph = f / n * math.tau
    bob = 0.0
    if st.get("kind") == "buzz":
        # a jittery buzz: a pixel's hop off the beat, never quite still
        bob = st.jitter * (1.0 if f % 2 else -1.0) + 0.3 * math.sin(ph)
    elif st.get("kind") == "flap":
        bob = -st.bob * math.sin(ph)
    z = (p.Z + rise + bob) * (1.0 - drop) + drop * 1.6
    C = v3(lunge, 0.0, z)
    bm = rot("c", yaw) @ rot("a", roll) @ rot("b", pitch)
    return C, bm, ph, drop


# ================================================================================================= the hollow drone
def _shell_paint(m, C, bm, sh):
    """Gunmetal: the seams between its sections a step dark round it, a lit band along its back."""
    def paint(q, n):
        loc = (q - C) @ bm
        nl = n @ bm
        seam = np.zeros(len(q), dtype=bool)
        for a0 in sh.seams:
            seam |= np.abs(loc[:, 0] - a0) < 0.2
        ridge = (nl[:, 2] > 0.86) & ~seam
        return np.full(len(q), m.shell, dtype=object), np.where(seam, -2, np.where(ridge, 1, 0)).astype(np.int16)
    return paint


def _drone(B, action: str, f: int, view: float) -> Pose:
    P = Pose()
    p, m = B.parts, B.mats
    st = B.style(action)
    C, bm, ph, drop = _frame(B, action, f)
    at = lambda q: C + bm @ v3(q)
    core = B.pick("core", action, f, 1.0)
    lance = B.pick("lance", action, f, 1.0)
    burst = B.pick("burst", action, f)
    flakes = B.pick("flakes", action, f)
    sh = p.shell
    paint = _shell_paint(m, C, bm, sh)
    P.add(E(at(sh.rear[0]), sh.rear[1], m.shell, "shell", bm, paint),
          E(at(sh.mid[0]), sh.mid[1], m.shell, "shell", bm, paint),
          E(at(sh.cowl[0]), sh.cowl[1], m.shell, "cowl", bm, paint))
    # The cowl a step darker (its own part, so its edge over the mid section draws a line), rivets round the seams.
    for k in range(sh.rivets):
        ang = math.radians(k * 360.0 / sh.rivets + 30.0)
        for a0 in sh.seams:
            r = sh.mid[1][1] * (0.82 if a0 < 0 else 0.78)
            P.mark(at((a0 + 0.25, math.cos(ang) * r, math.sin(ang) * r)), M.RAMPS[m.shell][4] if ang < math.pi else M.RAMPS[m.shell][1])
    # The lance: a long tapering needle of pale steel from the cowl's nose, telescoping out on the thrust, its tip bright.
    ln = p.lance
    root = at((ln.root, 0.0, 0.0))
    tip = at((ln.root + ln.length * lance, 0.0, 0.0))
    if flakes < 0.3:
        P.add(L(root, tip, ln.r[0], ln.r[1], m.lance, "lance"))
        P.add(S(root, ln.r[0] * 1.5, m.lance, "lance"))
        P.mark(tip, M.GLINT)
    # The tail vanes.
    vn = p.vanes
    for s in (1, -1):
        vm = bm @ rot("a", s * vn.splay)
        P.add(E(at(vn.at) + vm @ v3(0.0, 0.0, vn.r[2] * 0.6), vn.r, m.shell, "vane%d" % s, vm))
    # The core: a sickly violet light in the mid section's flanks and back, ash-white fissures spreading from it.
    cr = p.core
    cc = at(cr.at)
    if core > 0.05:
        # A band of light round its girth (it shows through its wings: light), brightest on top.
        r1 = sh.mid[1][1] * 1.02
        for k in range(14):
            ang = math.radians(k * 360.0 / 14.0)
            q = cc + bm @ v3(0.0, math.cos(ang) * r1, math.sin(ang) * r1)
            if math.sin(ang) > -0.3:
                P.glow.append((q, M.DRONE_CORE_HI if (core >= 1.5 and k % 2) else M.DRONE_CORE))
        top = cc + bm @ v3(0.0, 0.0, sh.mid[1][2] * 1.05)
        P.eye(top, M.DRONE_CORE_HI if core >= 1.0 else M.DRONE_CORE)
    for k in range(cr.fissures):
        ang = math.radians(-60.0 + k * 30.0)
        for t in (0.55, 0.8, 1.0):
            a0 = cr.at[0] + math.cos(ang) * t * 1.3
            P.mark(at((a0, math.sin(ang) * sh.mid[1][1] * 0.9, sh.mid[1][2] * (0.55 + 0.4 * t))), M.ASH_CRACK)
    # The Hollow eye: one empty white eye in a dark socket on the cowl, each side.
    ea, eb, ec = p.eye
    for s in (1, -1):
        q = at((ea, s * eb, ec))
        P.mark(q + bm @ v3(-0.25, 0.0, 0.0), M.RAMPS[m.shell][0])
        if action == "death" or st.get("squint"):
            P.mark(q, M.RAMPS[m.shell][0])
        else:
            P.eye(q, M.HOLLOW_EYE)
    # The wings: two pairs off its back, beating too fast to see: each at the two ends of its beat, the far end paler.
    wg = p.wings
    amp = st.get("beat_amp", 26.0) / 26.0
    up = (f % 2) == 0
    hi, lo = wg.beat
    mid = (hi + lo) * 0.5
    for j, (wa, (wl, ww), sw) in enumerate(zip(wg.at, wg.r, wg.sweep)):
        for s in (1, -1):
            for end in ((0, 1) if amp > 0.0 else (0,)):
                el = mid + (hi - mid) * amp * (1.0 if (end == 0) == up else -1.0)
                if amp == 0.0:
                    el = -10.0
                wm = bm @ rot("c", s * (90.0 + sw)) @ rot("b", el)
                ctr = at(wa) + wm @ v3(wl * 0.92, 0.0, 0.0)
                P.add(E(ctr, (wl, ww, 0.12), m.wing if end == 0 else m.ghost, "wing%d%d%d" % (j, s, end), wm, line=False))
    # The tell's violet glow round its core; the blow's spark at the lance's tip; sparks spat when struck; the core
    # bursting as it dies.
    if st.get("halo") and core >= 1.2:
        for k in range(12):
            ang = math.radians(k * 30.0 + f * 15.0)
            rr = 2.2 + 0.3 * f
            P.glow.append((cc + v3(math.cos(ang) * rr * 0.8, math.sin(ang) * rr, math.sin(ang * 2.0) * 0.8), M.DRONE_GLOW))
    if burst > 0.0:
        c0 = tip if action == "attack" else cc
        for k in range(10):
            ang = math.radians(k * 36.0 + f * 20.0)
            rr = 0.9 + burst * 1.3
            P.glow.append((c0 + v3(0.3 * math.cos(ang), math.cos(ang) * rr, math.sin(ang) * rr), M.DRONE_CORE_HI if k % 2 else M.DRONE_CORE))
        P.glow.append((c0, M.DRONE_CORE_HI))
    if f in st.get("sparks", ()):
        for k in range(6):
            ang = math.radians(k * 60.0 + f * 40.0)
            P.glow.append((C + v3(math.cos(ang) * 2.6, math.sin(ang) * 2.4, 1.2 + (k % 3) * 0.6), M.SPARK if k % 2 else M.DRONE_CORE))
    if f in st.get("streaks", ()):
        for j in range(3):
            for d in range(3):
                P.fx.append((at((-4.6 - d * 1.2, (j - 1) * 1.1, 0.2 * j)), M.STREAK if d < 2 else M.DUST_DIM))
    if flakes > 0.0:
        collapse(P, flakes, int(B.opts.get("seed", 0)))
    d = B.pick("dissolve", action, f)
    if d > 0.0:
        P.dissolve = d
        P.dissolve_col = M.ASH_CRACK
    sq = st.get("squash", {}).get(f)
    if sq is not None:
        P.squash(sq[0], sq[1], sq[2], tuple(C))
    return P


# ================================================================================================= the orbit moth
def _wing_paint(m, centre, wm, half, chord, fringe):
    """A moth's wing in its own frame (its centre; u out along its span, -1 at its root .. 1 at its tip; v back along its
    chord, -1 at its leading edge): the dusky indigo, a rose fringe round its outer margin, a pale leading edge, veins a
    step dark fanning from its root."""
    def paint(q, n):
        loc = (q - centre) @ wm
        u = loc[:, 0] / half
        v = loc[:, 1] / chord
        rad = np.hypot(u, v)
        edge = (rad > fringe) & (u > -0.2)
        lead = (v < -0.62) & ~edge
        vein = (np.abs((np.arctan2(v, u + 1.05) * 3.2) % 1.0 - 0.5) > 0.45) & ~edge
        names = np.where(edge, m.fringe, m.wing).astype(object)
        return names, np.where(lead, 1, np.where(vein, -1, 0)).astype(np.int16)
    return paint


def _moth(B, action: str, f: int, view: float) -> Pose:
    P = Pose()
    p, m = B.parts, B.mats
    st = B.style(action)
    C, bm, ph, drop = _frame(B, action, f)
    at = lambda q: C + bm @ v3(q)
    spread = B.pick("spread", action, f)
    fold = B.pick("fold", action, f)
    knot = B.pick("knot", action, f)
    burst = B.pick("burst", action, f)
    if st.get("kind") == "flap":
        beat = st.beat_base + st.beat_amp * math.sin(ph)
    else:
        beat = B.pick("beat", action, f, 10.0)
    beat = beat * (1.0 - spread) + 34.0 * spread
    bd = p.body

    def fur(q, n):
        loc = (q - C) @ bm
        band = (loc[:, 0] < -0.9) & ((((loc[:, 0] + 0.9) * -bd.bands / 3.6) % 1.0) < 0.3)
        tuft = ((loc[:, 1] * 2.1 + loc[:, 2] * 1.7 + loc[:, 0]) % 1.1) < 0.2
        return np.full(len(q), m.fur, dtype=object), np.where(band, -2, np.where(tuft, -1, 0)).astype(np.int16)

    (ta, tr), (ca, cr_, cn), (aa, ar) = bd.thorax, bd.collar, bd.abdomen
    P.add(E(at(aa), ar, m.fur, "abdomen", bm, fur), E(at(ta), tr, m.fur, "thorax", bm, fur))
    for k in range(cn):
        ang = math.radians(k * 360.0 / cn)
        P.add(S(at((ca[0], math.cos(ang) * cr_ * 0.9, ca[2] + math.sin(ang) * cr_ * 0.8)), 0.55, m.fur, "collar", fur, line=False))
    (ha, hr) = bd.head
    hc = at(ha)
    P.add(S(hc, hr, m.fur, "head", fur))
    ea, eb, ec = bd.eye
    for s in (1, -1):
        eye = hc + bm @ v3(ea, s * eb, ec)
        P.add(S(eye, 0.5, m.eye, "eye%d" % s, line=False))
        if action != "death" and not st.get("squint"):
            P.eye(eye + bm @ v3(0.25, s * 0.2, 0.3), M.MOTH_GLINT)
    # The feathered antennae: up and out from the head, barbs along them.
    an = p.antennae
    for s in (1, -1):
        r0 = at((an.root[0], s * an.root[1], an.root[2]))
        r1 = at((an.tip[0], s * an.tip[1], an.tip[2] + 0.4 * math.sin(f * 0.8)))
        P.add(L(r0, r1, 0.22, 0.14, m.antenna, "antenna%d" % s, line=False))
        dd = r1 - r0
        for k in range(1, an.barbs + 1):
            q = r0 + dd * (k / (an.barbs + 0.5))
            P.add(L(q, q + bm @ v3(-0.45, s * 0.35, 0.25), 0.14, 0.08, m.antenna, "antenna%d" % s, line=False))
    # The wings: a forewing and a hindwing a side, beating about the body's length, spread wide and up in the tell,
    # snapped down on the blow, folded back as it falls; their star charts and the fringe.
    wg = p.wings
    for s in (1, -1):
        for j, (key, lag) in enumerate((("fore", 0.0), ("hind", 8.0))):
            (wa, wb, wc), length, chord, sweep = wg[key]
            el = beat - lag
            sw = sweep * (1.0 - 0.45 * spread) + 50.0 * fold
            wm = bm @ rot("c", s * sw) @ rot("a", s * el)
            root = at((wa, s * wb, wc))
            # The wing's frame: its span out from the body (swept back, raised by the beat), its chord back along it.
            span = wm @ v3(0.0, s, 0.0)
            chord_d = wm @ v3(-1.0, 0.0, 0.0)
            nrm = np.cross(span, chord_d)
            fm = np.stack([span, chord_d, nrm], axis=1)
            ctr = root + span * length * 0.5 + chord_d * chord * 0.15
            P.add(E(ctr, (length * 0.55 * (1.0 - 0.35 * fold), chord * 0.55, 0.14), m.wing, "wing%s%d" % (key, s), fm,
                    _wing_paint(m, ctr, fm, length * 0.55 * (1.0 - 0.35 * fold), chord * 0.55, wg.fringe)))
            # The star chart: stars joined by gold lines, a bright star on the forewing.
            pts = []
            for u, v in wg.stars[j]:
                q = root + span * length * u * (1.0 - 0.35 * fold) + chord_d * chord * v * 0.6 + nrm * 0.2
                pts.append(q)
            for a_, b_ in zip(pts, pts[1:]):
                for t in (0.33, 0.66):
                    P.mark(a_ + (b_ - a_) * t, M.MOTH_LINE)
            for q in pts:
                P.mark(q, M.MOTH_STAR)
            if j == 0:
                q = root + span * length * 0.62 * (1.0 - 0.35 * fold) + chord_d * chord * 0.05 + nrm * 0.25
                P.mark(q, M.MOTH_WHITE)
                for dd in ((0.4, 0.0), (-0.4, 0.0), (0.0, 0.4), (0.0, -0.4)):
                    P.mark(q + span * dd[0] + chord_d * dd[1], M.MOTH_STAR)
    # The motes orbiting it (gathered into a glowing knot before its head in the tell, sprayed out in the blow, winking
    # out one by one as it falls).
    mo = p.motes
    out = sum(1 for k in st.get("motes_out", ()) if f >= k)
    for k in range(mo.n - out):
        ang = math.radians(k * 360.0 / mo.n + f * 30.0)
        ring = rot("a", mo.tilt) @ v3(math.cos(ang) * mo.orbit, math.sin(ang) * mo.orbit, 0.0)
        knot_q = v3(3.2 + 0.5 * math.cos(ang), 0.5 * math.sin(ang), 0.6 + 0.5 * math.cos(ang * 2.0))
        q = C + ring * (1.0 - knot) + bm @ knot_q * knot
        P.glow.append((q, M.MOTE_CORE))
        for d in ((0.35, 0.0, 0.0), (-0.35, 0.0, 0.0), (0.0, 0.35, 0.0), (0.0, -0.35, 0.0)):
            P.glow.append((q + v3(*d), M.MOTE_ARM if knot < 0.5 else M.MOTE_DIM2))
    if knot >= 0.6:
        kc = C + bm @ v3(3.2, 0.0, 0.6)
        for k in range(10):
            ang = math.radians(k * 36.0 + f * 20.0)
            rr = 1.0 + 0.6 * knot
            P.glow.append((kc + v3(0.0, math.cos(ang) * rr, math.sin(ang) * rr), M.MOTE_ARM if k % 2 else M.MOTE_CORE))
    if burst > 0.0:
        for k in range(16):
            ang = math.radians(-60.0 + k * 8.0)
            for t in range(2):
                rr = 2.0 + burst * 2.4 + t * 1.4
                q = C + bm @ v3(2.6 + math.cos(ang) * rr, math.sin(ang) * rr, 0.3 * ((k + t) % 3) - 0.3)
                P.glow.append((q, M.MOTH_STAR if (k + t) % 3 else M.MOTE_CORE))
    if f in st.get("puff", ()):
        for k in range(8):
            ang = math.radians(k * 45.0 + f * 30.0)
            P.fx.append((C + v3(math.cos(ang) * 3.0, math.sin(ang) * 3.2, 0.8 + (k % 3) * 0.5), M.MOTH_PUFF if k % 2 else M.MOTH_PUFF_DIM))
    d = B.pick("dissolve", action, f)
    if d > 0.0:
        P.dissolve = d
        P.dissolve_col = M.MOTE_ARM
    sq = st.get("squash", {}).get(f)
    if sq is not None:
        P.squash(sq[0], sq[1], sq[2], tuple(C))
    return P


# ================================================================================================= the Copperjaw swarm (M5)
from ..motion import h01  # noqa: E402
# `swarm` (the Copperjaw swarm, the Copperjaw Box let loose): not one insect but a cloud of them. Eleven small copper
# beetles of three sizes hang in a loose cloud over the floor (`beetles`: each one's place in the cloud, its size and the
# phase of its own small loop), each a sculpted beetle: copper wing cases with a dark seam down their middle, a dark
# chitin pronotum and head before them, pale-gold jaws (the copper jaw), a glint in the eye of the larger ones. Their
# cases lift and part from beetle to beetle so the cloud buzzes, pale wings blurring out from under them. It hangs,
# every beetle rounding its own loop; it streams forward stretched out and nose-down, specks of copper trailing it; in its
# tell it draws back and balls up, jaws open, a copper ring tightening round it (held); it lances forward as a spearhead
# and bites (a spark at its tip on the blow) and loosens; struck, it is blown back and scattered, beetles tumbling and
# copper dust flung off; beaten, the beetles tumble and rain down, land on their backs with their legs in the air, and
# fade. `queen` (the Copperjaw queen's sheet: the swarm once a Queen has risen in the box): a large gold-cased Queen with
# a pale-gold crown at the heart of the cloud, leading its lance and falling with the rest.
# Channels: `lunge`, `rise`, `gather` (0..1: drawn in toward the middle, the ball), `stretch` ((along, across): the
# cloud drawn out), `spin` (degrees: how far round its loop each beetle is), `pitch` (the beetles' noses, + up),
# `spread` (degrees: their headings' scatter), `jaws`, `ring` (the tell's ring: 0 none, 1 closing, 2 hot), `hit` (the
# spark at its tip), `scatter` (pushed out from the middle), `tumble` (degrees: each beetle's roll), `drop` (0..1: fallen
# to the floor), `lying` (on their backs), `dust`, `streaks`, `dissolve`.
SWARM_STYLES = {
    "hang": {"kind": "cloud", "turn": 60.0, "amp": (0.75, 0.75, 0.45), "rise_amp": 0.3},
    "stream": {"kind": "cloud", "turn": 45.0, "amp": (1.1, 0.8, 0.5), "rise_amp": 0.4, "stretch": (1.28, 0.84), "pitch": -10.0,
               "lunge": (0.0, 0.4, 0.8, 0.8, 0.4, 0.0, -0.2, -0.2), "streaks": (0, 2, 4, 6)},
    "ball_up": {"gather": (0.35, 0.65, 0.85, 0.85), "lunge": (-0.6, -1.2, -1.6, -1.6), "rise": (0.2, 0.4, 0.5, 0.5),
                "spin": (20.0, 40.0, 60.0, 60.0), "spread": (12.0, 6.0, 3.0, 3.0), "pitch": (4.0, 6.0, 8.0, 8.0), "jaws": True,
                "ring": (0, 1, 2, 2), "beat": (0, 1, 0, 0)},
    "lance": {"gather": (0.5, 0.42, 0.3, 0.15, 0.05, 0.0), "stretch": ((1.35, 0.66), (1.6, 0.52), (1.5, 0.58), (1.25, 0.78), (1.08, 0.94), (1.0, 1.0)),
              "lunge": (1.4, 4.2, 4.4, 3.4, 1.8, 0.5), "rise": (0.2, -0.6, -0.6, -0.4, -0.1, 0.0), "spin": (80.0, 100.0, 120.0, 140.0, 160.0, 180.0),
              "pitch": (-8.0, -14.0, -10.0, -4.0, 0.0, 0.0), "spread": (0.0, 0.0, 6.0, 12.0, 8.0, 4.0), "jaws": True, "hit": (1, 2),
              "streaks": (0, 1, 2), "beat": (1, 0, 1, 0, 1, 0)},
    "scatter": {"lunge": (-2.4, -1.6, -0.6), "rise": (0.6, 0.3, 0.1), "scatter": (2.6, 1.5, 0.5), "tumble": (40.0, 22.0, 6.0),
                "spin": (200.0, 220.0, 240.0), "spread": (20.0, 10.0, 4.0), "dust": (0, 1), "beat": (1, 0, 1)},
    "rain": {"lunge": (-2.4, -2.6, -2.6, -2.6, -2.6, -2.6, -2.6, -2.6), "scatter": (2.6, 3.0, 3.3, 3.5, 3.6, 3.6, 3.6, 3.6),
             "tumble": (45.0, 120.0, 200.0, 250.0, 0.0, 0.0, 0.0, 0.0), "spin": (200.0,) * 8,
             "drop": (0.0, 0.25, 0.55, 0.85, 1.0, 1.0, 1.0, 1.0), "lying": (4, 5, 6, 7), "dust": (0,),
             "dissolve": (0.0, 0.0, 0.0, 0.0, 0.0, 0.2, 0.45, 0.7), "beat": (1, 0, 1, 0, 0, 0, 0, 0), "dead": True},
}
STYLES.update(SWARM_STYLES)
# A beetle in the cloud: (a, b, c) from its middle, its size (0 small, 1 middling, 2 large), its loop's phase (degrees).
SWARM = {
    "Z": 8.0,
    "beetles": ((-5.0, 1.6, 1.2, 0, 0.0), (-1.2, 4.8, 2.4, 0, 90.0), (3.2, 3.8, 1.8, 0, 180.0), (5.4, -0.6, 0.9, 0, 270.0),
                (-3.9, -3.2, -0.6, 1, 45.0), (-0.2, 2.0, 3.1, 1, 135.0), (3.6, -3.6, 0.7, 1, 225.0), (0.4, -5.0, 1.8, 1, 315.0),
                (-2.4, 0.2, -1.4, 2, 30.0), (2.0, 1.7, -0.5, 2, 150.0), (1.4, -2.2, -2.0, 2, 270.0)),
    # each size: the wing cases' radii (a, b, c), the head's radius, the wings' length
    "sizes": (((0.9, 0.66, 0.5), 0.4, 1.0), ((1.15, 0.84, 0.6), 0.48, 1.3), ((1.4, 1.02, 0.72), 0.56, 1.6)),
    # the Queen (the Copperjaw queen's sheet: `queen` True): her place, her cases' radii, her head, her wings, her crown's
    # points, how far ahead of the cloud she leads its lance
    "queen": False,
    "regal": {"at": (0.8, 0.0, 0.9), "r": (2.3, 1.7, 1.15), "head": 0.85, "wing": 2.6, "crown": 3, "ahead": 2.6},
}
VARIANTS["swarm"] = {"parts": SWARM, "mats": {"case": "cj_copper", "chitin": "cj_chitin", "wing": "cj_wing", "queen": "cj_queen"},
                     "motion": {"idle": "hang", "walk": "stream", "windup": "ball_up", "attack": "lance", "hurt": "scatter", "death": "rain"}}


def _beetle(P, B, n, at, R, radii, head_r, wing_l, mat, open_, jaws, lying, big, crown=0, bare=False) -> np.ndarray:
    """One beetle at `at`, turned by R (its own a forward, b left, c up): its wing cases (a dark seam down their middle,
    parting at the rear as they lift, the wings blurring out pale from under them), a dark chitin pronotum and head before
    them, pale-gold jaws, a glint in a big one's eye; on its back, its six legs in the air; a Queen's crown. Bare (its
    body reviewed first): no wing blur, no crown. Returns its head's centre."""
    m = B.mats
    ra, rb, rc = radii
    loc = lambda q: at + R @ v3(q)

    def case(q, nn):
        """The wing cases: copper, the seam down their middle a step dark on top (opened, a dark V at the rear)."""
        lq = (q - at) @ R
        nl = nn @ R
        w = max(0.16, rb * 0.16) + (np.clip(-lq[:, 0] / ra, 0.0, 1.0) * rb * 0.34 if open_ else 0.0)
        seam = (np.abs(lq[:, 1]) < w) & (nl[:, 2] > 0.2) & (lq[:, 0] < ra * 0.6)
        return np.full(len(q), mat, dtype=object), np.where(seam, -2, 0).astype(np.int16)

    def belly(q, nn):
        return np.full(len(q), m.chitin, dtype=object), np.where((nn @ R)[:, 2] > 0.6, 1, 0).astype(np.int16)

    P.add(E(at, radii, mat, n + "case", R, belly if lying else case))
    P.add(E(loc((ra * 0.88, 0.0, rc * 0.02)), (ra * 0.34, rb * 0.78, rc * 0.74), m.chitin, n + "pro", R))
    hc = loc((ra * 1.16 + head_r * 0.6, 0.0, -rc * 0.08))
    P.add(S(hc, head_r, m.chitin, n + "head"))
    hp = lambda q: hc + R @ v3(q)
    if open_ and not lying and not bare:
        # The wings blurring out from under the lifted cases: faint pale ovals to each side, swept back.
        for s in (1, -1):
            for u in (-0.5, 0.0, 0.5):
                for v in (0.2, 0.6, 1.0):
                    P.fx.append((loc((-0.25 * ra + u * wing_l * 0.6 - v * 0.3, s * (rb * 0.8 + v * wing_l * 0.55), rc * 0.5)),
                                 M.CJ_WING_BLUR if v < 0.9 else M.CJ_WING_EDGE))
    if jaws:
        for s in (1, -1):
            P.mark(hp((head_r * 1.0, s * head_r * 0.6, -0.1)), M.CJ_JAW)
            P.mark(hp((head_r * 1.55, s * head_r * 0.8, -0.1)), M.CJ_JAW_DIM)
    else:
        P.mark(hp((head_r * 1.05, 0.0, -0.1)), M.CJ_JAW if big else M.CJ_JAW_DIM)
    if big and not lying:
        for s in (1, -1):
            P.eye(hp((head_r * 0.3, s * head_r * 0.72, head_r * 0.42)), M.GLINT)
    if lying:
        # Its six legs in the air (the beetle on its back: its belly up, the legs up off it).
        for k in (-1, 0, 1):
            for s in (1, -1):
                root = loc((k * ra * 0.55, s * rb * 0.5, -rc * 0.6))
                tip = root + v3(0.15 * k, s * 0.35, 0.0) + R @ v3(0.0, s * 0.3, -1.0) * (0.5 + 0.25 * rc)
                P.add(L(root, tip, 0.16, 0.1, m.chitin, n + "leg", line=False))
    if crown and not bare:
        # The Queen's crown: a pale-gold band over her pronotum, its points rising from it.
        for k in range(crown):
            u = (k - (crown - 1) * 0.5) / max(1.0, (crown - 1) * 0.5)
            base = loc((ra * 0.9, u * rb * 0.55, rc * 0.66))
            tip = base + R @ v3(0.1, u * 0.25, 0.95 - 0.3 * abs(u))
            P.add(L(base, tip, 0.3, 0.12, m.queen, n + "crown", line=False))
            P.mark(tip, M.CJ_CROWN)
        for s in (-1, 0, 1):
            P.mark(loc((ra * 0.9, s * rb * 0.45, rc * 0.7 + 0.1)), M.CJ_CROWN)
    return hc


def _swarm(B, action: str, f: int, view: float) -> Pose:
    P = Pose()
    p, m = B.parts, B.mats
    st = B.style(action)
    seed = int(B.opts.get("seed", 0))
    lunge = B.pick("lunge", action, f)
    rise = B.pick("rise", action, f)
    gather = B.pick("gather", action, f)
    sv = st.get("stretch")
    sa, sb = (1.0, 1.0) if sv is None else (sv[min(f, len(sv) - 1)] if isinstance(sv[0], (tuple, list)) else sv)
    turn = st.get("turn")
    spin = f * turn if turn else B.pick("spin", action, f)
    amp = st.get("amp", (0.5, 0.5, 0.3))
    pitch = B.pick("pitch", action, f, st.get("pitch", 0.0))
    spread = B.pick("spread", action, f)
    jaws = bool(st.get("jaws", False))
    scatter = B.pick("scatter", action, f)
    tumble = B.pick("tumble", action, f)
    drop = B.pick("drop", action, f)
    lying = f in st.get("lying", ())
    beat = B.pick("beat", action, f, f % 2)
    bare = bool(B.opts.get("bare"))
    n = 6 if action == "idle" else 8
    bob = st.get("rise_amp", 0.0) * math.sin(f / n * math.tau) if turn else 0.0
    C = v3(lunge, 0.0, p.Z + rise + bob)
    shrink = (1.0 - 0.5 * gather, 1.0 - 0.5 * gather, 1.0 - 0.45 * gather)
    front = -9.0
    for i, (x, y, z, size, ph) in enumerate(p.beetles):
        th = math.radians(ph + spin)
        q = v3(x * sa + math.cos(th) * amp[0], y * sb + math.sin(th) * amp[1], z + math.sin(2.0 * th) * amp[2]) * v3(shrink)
        if scatter:
            d = v3(x, y, z * 0.6)
            q = q + d / max(1e-6, float(np.linalg.norm(d))) * scatter * (0.7 + 0.6 * h01(i, 3, seed % 97))
        q = C + q
        if drop:
            t = drop * drop
            land = v3(q[0] + (h01(i, 5, seed % 89) - 0.5) * 3.0 * drop, q[1] + (h01(i, 7, seed % 83) - 0.5) * 3.0 * drop,
                      0.55 + 0.25 * size)
            q = q + (land - q) * t
        yaw = (h01(i, 11, seed % 79) - 0.5) * 2.0 * spread
        roll = (h01(i, 13, seed % 73) - 0.5) * 2.0 * tumble + drop * 90.0 * (1 if i % 2 else -1) if (tumble or drop) and not lying else 0.0
        R = rot("c", yaw) @ rot("b", pitch * (0.0 if lying else 1.0) + (0.0 if lying else (h01(i, 17, seed % 71) - 0.5) * 2.0 * tumble * 0.5)) @ rot("a", 180.0 if lying else roll)
        radii, head_r, wing_l = p.sizes[size]
        open_ = ((i + int(beat)) % 2 == 0) and not lying and drop < 0.5 and tumble < 30.0
        hc = _beetle(P, B, "b%d" % i, q, R, radii, head_r, wing_l, m.case, open_, jaws, lying, size >= 1, bare=bare)
        front = max(front, float(hc[0]))
    if p.get("queen"):
        qn = p.regal
        th = math.radians(spin)
        q = C + v3(qn.at[0] + qn.ahead * gather * (1.0 + (sa - 1.0) * 2.0) + 0.3 * math.cos(th), qn.at[1] + 0.3 * math.sin(th), qn.at[2])
        if scatter:
            q = q + v3(-scatter * 0.5, 0.0, scatter * 0.2)
        if drop:
            t = drop * drop
            q = q + (v3(q[0] + 1.0 * drop, q[1], 0.95) - q) * t
        roll = 0.0 if lying else (tumble * 0.35 + drop * 60.0 if (tumble or drop) else 0.0)
        R = rot("b", pitch * (0.0 if lying else 0.5)) @ rot("a", 180.0 if lying else roll)
        open_ = int(beat) == 1 and not lying and drop < 0.5
        hc = _beetle(P, B, "queen", q, R, qn.r, qn.head, qn.wing, m.queen, open_, jaws, lying, True, crown=qn.crown, bare=bare)
        front = max(front, float(hc[0]))
    ring = int(B.pick("ring", action, f))
    if bare:
        ring = 0                                         # its bodies alone (`opts.bare`, reviewed first): no light, no dust
    if ring:
        # The tell: a copper ring closing round the ball, hot as it is held; glints at the jaws before it.
        r = 8.4 if ring == 1 else 7.2
        for k in range(44):
            ang = math.radians(k * 360.0 / 44.0 + min(f, 2) * 9.0)      # held on its last frame (`share`)
            if ring == 1 and k % 4 == 3:
                continue
            P.glow.append((C + v3(math.cos(ang) * r, math.sin(ang) * r, 0.6 * math.sin(ang * 2.0)), M.CJ_RING if ring == 1 or k % 4 else M.CJ_RING_HOT))
        if ring == 2:
            for k, (db, dc) in enumerate(((-1.4, 0.8), (1.2, -0.2), (0.0, 1.4))):
                g = v3(front + 1.0, db, C[2] + dc - 0.4)
                P.glow.append((g, M.GLINT))
                for d in ((0.45, 0.0, 0.0), (-0.45, 0.0, 0.0), (0.0, 0.45, 0.0), (0.0, -0.45, 0.0)):
                    P.glow.append((g + v3(*d), M.CJ_JAW_DIM))
    if f in st.get("hit", ()) and not bare:
        # The bite lands at the spearhead's tip: a spark.
        tip = v3(front + 1.6, 0.0, C[2] - 0.6)
        P.glow.append((tip, M.SPARK))
        for k in range(8):
            ang = math.radians(k * 45.0 + f * 22.0)
            rr = 1.0 + (k % 2) * 0.9 + (f - 1) * 0.6
            P.glow.append((tip + v3(0.3 * math.cos(ang), math.cos(ang) * rr, math.sin(ang) * rr), M.SPARK if k % 2 else M.CJ_JAW))
    if f in st.get("streaks", ()) and not bare:
        for j in range(4):
            for d in range(3):
                P.fx.append((C + v3(-6.0 * sa - 0.9 * d - 0.6 * (j % 2), (j - 1.5) * 1.6, 0.6 * ((j + d) % 3) - 0.6), M.CJ_SPECK if d < 2 else M.DUST_DIM))
    if f in st.get("dust", ()) and not bare:
        for k in range(10):
            ang = math.radians(k * 36.0 + f * 18.0)
            rr = 6.0 + scatter + (k % 3) * 0.8
            P.fx.append((C + v3(math.cos(ang) * rr, math.sin(ang) * rr, (k % 3 - 1) * 1.2 - drop * C[2] * 0.6), M.CJ_SPECK if k % 2 else M.CJ_SPECK_DIM))
    d = B.pick("dissolve", action, f)
    if d > 0.0:
        P.dissolve = d
        P.dissolve_col = M.CJ_SPECK
    return P
