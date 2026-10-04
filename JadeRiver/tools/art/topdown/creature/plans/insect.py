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
