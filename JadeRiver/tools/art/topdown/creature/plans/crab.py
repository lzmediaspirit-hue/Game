"""The crab plan (audit 45 §6.2), from the mud crab (`mud`).

A wide shell over a rim and a raised brow, eyes on stalks, legs a side jointed knee-up and scuttling in alternating
sets, and two claws (an arm, a palm, a fixed finger and a moving dactyl) held up at its sides like a boxer's guard. It
keeps its broad side to the camera and scuttles sideways (creatures.Spec `sideways`): `aim` is where it faces in its
own frame, and the lunge, the stride and the struck side's claw follow it.

  shell  the carapace's size and pattern (pale blotches, grooves, the pale underside it shows on its back)
  legs   `n` a side along the shell, their reach and the scuttle's lift and stride
  claws  the rest pose (ahead, out, up, yaw in, pitch, open) and the materials of the arm and the tips; M1: `scale`, each
         claw's size (its left's, its right's: the tide crab's great shield claw)
  shell  M1: `pearls`, pearls grown on the carapace (along, across)

The motion styles (STYLES): idle `snap`, walk `scuttle`, windup `claws_high`, attack `slam_drag`, hurt `flung`,
death `flip_curl`. A claw's channel `claw` is (ahead, out, up, yaw in, pitch up, open) a frame.
"""
from __future__ import annotations

import math

import numpy as np

from .. import mats as M
from ..motion import gait, wave
from ..sculpt import E, L, Pose, S, rot, v3

STYLES = {
    "snap": {"bob_amp": 0.25, "snap": True},
    "scuttle": {"kind": "scuttle", "bob_amp": 0.45, "sway": 4.0},
    "claws_high": {"lunge": (-0.6, -1.2, -1.6, -1.8), "bob": (0.4, 0.8, 1.0, 0.9), "pitch": (6.0, 10.0, 13.0, 14.0),
                   "claw": ((5.2, 7.0, 4.4, 40.0, 30.0, 0.4), (4.2, 8.2, 6.4, 25.0, 55.0, 0.7), (3.6, 8.8, 8.2, 14.0, 70.0, 1.0),
                            (3.4, 9.0, 8.8, 10.0, 76.0, 1.0)),
                   "stalk": (0.4, 0.8, 1.0, 1.0), "planted": True, "squash": {3: (0.97, 0.98, 1.04)}},
    "slam_drag": {"lunge": (2.4, 4.0, 3.8, 2.6, 1.2, 0.4), "bob": (0.6, -0.8, -0.9, -0.5, -0.1, 0.0),
                  "pitch": (-4.0, -12.0, -10.0, -5.0, -2.0, 0.0),
                  "claw": ((6.2, 7.0, 6.4, 30.0, 25.0, 1.0), (9.4, 4.4, 1.2, 48.0, -26.0, 0.0), (9.6, 4.4, 0.9, 48.0, -30.0, 0.0),
                           (8.0, 5.6, 1.6, 50.0, -14.0, 0.15), (6.6, 6.8, 2.6, 40.0, 8.0, 0.3), (5.6, 7.6, 3.4, 35.0, 22.0, 0.3)),
                  "stalk": (0.6, 0.2, 0.2, 0.4, 0.6, 0.8), "reach": (0, 1, 2, 3), "dust": (1, 2), "squash": {1: (1.06, 1.04, 0.9)}},
    "flung": {"lunge": (-2.4, -1.4, -0.4), "bob": (-0.6, 0.3, 0.0), "pitch": (10.0, -3.0, 0.0),
              "claw": ((4.4, 9.0, 6.4, 24.0, 55.0, 0.9), (5.0, 8.4, 4.4, 30.0, 36.0, 0.5), (5.2, 7.9, 3.8, 34.0, 28.0, 0.35)),
              "curl": (0.3, 0.1, 0.0), "stalk": (-1.0, -0.6, -0.2)},
    "flip_curl": {"lunge": (-0.6, -0.8, -0.8, -0.8, -0.8, -0.8, -0.8, -0.8),
                  "claw": ((5.6, 6.8, 4.0, 40.0, 30.0, 0.8), (5.4, 8.0, 2.4, 30.0, 0.0, 0.8), (5.2, 8.6, 1.2, 25.0, -10.0, 0.9),
                           (5.2, 8.8, 0.6, 22.0, -14.0, 0.9), (5.2, 8.8, 0.6, 22.0, -14.0, 0.9), (5.2, 8.8, 0.6, 22.0, -14.0, 0.9),
                           (5.2, 8.8, 0.6, 22.0, -14.0, 0.9), (5.2, 8.8, 0.6, 22.0, -14.0, 0.9)),
                  "roll": (6.0, 30.0, 90.0, 150.0, 176.0, 172.0, 178.0, 176.0), "curl": (0.0, 0.1, 0.3, 0.6, 0.8, 1.0, 0.85, 1.0),
                  "stalk": (0.0, -0.6, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0), "glint_until": 2, "edge": (7.0, 3.6)},
}

MUD = {
    "Z": 5.6,
    "shell": {"r": (5.2, 7.4, 3.4), "rim": ((-0.3, 0.0, -1.3), (5.6, 7.9, 2.3)), "brow": ((3.6, 0.0, 0.2), (1.6, 5.0, 1.6)),
              "blotches": ((1.2, 2.8, 1.5), (-1.6, -2.6, 1.7), (1.8, -4.2, 1.1), (-2.0, 3.8, 1.3), (-0.2, 0.2, 1.2))},
    "mouth": ((5.4, 0.7, -0.8), (5.5, 0.0, -1.2)),
    "stalks": {"base": (3.8, 1.8, 1.2), "tip": (4.4, 2.3, 4.6), "rise": (0.3, 1.6), "r": (0.62, 0.55), "eye": 1.2},
    "legs": {"at": (-3.2, -0.8, 1.6), "hip": (6.4, -1.0), "knee": (9.8, 1.8), "foot": (11.6, 0.5), "lift": 1.8, "stride": 1.5,
             "r": ((1.05, 0.95), (0.9, 0.45))},
    "claws": {"rest": (5.2, 7.8, 3.6, 34.0, 26.0, 0.3), "root": (2.6, 5.8, -0.4)},
}
VARIANTS = {
    "mud": {"parts": MUD, "mats": {"shell": "shell", "rim": "shell_rim", "pale": "shell_pale", "leg": "crab_leg", "claw": "claw",
                                   "tip": "claw_tip", "eye": "eye"},
            "motion": {"idle": "snap", "walk": "scuttle", "windup": "claws_high", "attack": "slam_drag", "hurt": "flung",
                       "death": "flip_curl"}},
}


def pose(B, action: str, f: int, aim=(1.0, 0.0), view=None) -> Pose:
    if "tail" in B.parts:
        return _scorpion(B, action, f)
    P = Pose()
    p, m = B.parts, B.mats
    st = B.style(action)
    da, db = aim
    Z = p.Z
    lunge = B.pick("lunge", action, f)
    bob = B.pick("bob", action, f)
    if action == "idle":
        bob = st.bob_amp * wave(action, f)
    elif st.get("kind") == "scuttle":
        bob = st.bob_amp * abs(math.sin(f / 8.0 * 2.0 * math.pi))
    pitch = B.pick("pitch", action, f)
    sway = 0.0
    if st.get("kind") == "scuttle":
        sway = st.sway * math.sin(f / 8.0 * 2.0 * math.pi)       # it rocks side to side as it scuttles
    z = Z + bob
    C = v3(da * lunge, db * lunge, z)
    bm = rot("b", pitch) @ rot("a", sway * (1 if abs(db) > 0.3 else 0.4))
    at = lambda q: C + bm @ v3(q)
    sh = p.shell
    shell_c, shell_r = at((0.0, 0.0, 0.0)), sh.r

    def shell(q, n):
        """Pale patches over the top (lit blotches), the grooves of the carapace, the brow's rim a step darker."""
        loc = (q - C) @ bm
        nz = (n @ bm)[:, 2]
        a, b = loc[:, 0], loc[:, 1]
        blotch = np.zeros(len(a), dtype=bool)
        for pa, pb, r in sh.blotches:
            blotch |= (a - pa) ** 2 + (b - pb) ** 2 < r * r
        blotch &= nz > 0.35
        groove = (np.abs(np.abs(b) - 2.2 - 0.25 * a) < 0.3) & (nz > 0.2) | (np.abs(a - 1.9 + 0.05 * b * b) < 0.28) & (nz > 0.3)
        belly = nz < -0.35                         # the pale underside (it shows when it lies on its back)
        names = np.where(blotch | belly, m.pale, m.shell).astype(object)
        bias = np.where(groove & ~blotch & ~belly | belly & (np.abs(b) % 2.2 < 0.35), -1, 0).astype(np.int16)
        return names, bias

    def rim(q, n):
        nz = (n @ bm)[:, 2]
        return np.where(nz < -0.4, m.pale, m.rim).astype(object), np.zeros(len(nz), dtype=np.int16)

    P.add(E(shell_c, shell_r, m.shell, "body", bm, shell),
          E(at(sh.rim[0]), sh.rim[1], m.rim, "body", bm, rim),
          E(at(sh.brow[0]), sh.brow[1], m.shell, "body", bm, shell))       # the brow over the eyes
    # M1: pearls grown on the carapace (the tide crab's), each with its glint.
    for pa, pb, pr in sh.get("pearls", ()):
        u = min(0.95, (pa / shell_r[0]) ** 2 + (pb / shell_r[1]) ** 2)
        q = at((pa, pb, shell_r[2] * math.sqrt(1.0 - u) + pr * 0.2))
        P.add(S(q, pr, m.pearl, "pearl", line=False))
        P.mark(q + v3(-0.2, 0.2, pr * 0.9), M.GLINT)
    # Mouth parts under the brow.
    (ma, mb, mc), mid = p.mouth
    for s in (1, -1):
        P.mark(at((ma, s * mb, mc)), M.RAMPS[m.rim][0])
    P.mark(at(mid), M.RAMPS[m.leg][1])
    # Eye stalks: up from the brow, black eyes with a glint; up in the tell, down when struck or beaten.
    sk = p.stalks
    stalk = B.pick("stalk", action, f)
    look = 0.5 * wave(action, f, 0.2) if action == "idle" else 0.0
    for s in (1, -1):
        base = at((sk.base[0], s * sk.base[1], sk.base[2]))
        tip = at((sk.tip[0] + look * s, s * (sk.tip[1] + sk.rise[0] * stalk), sk.tip[2] + sk.rise[1] * stalk))
        P.add(L(base, tip, sk.r[0], sk.r[1], m.leg, "stalk%d" % s))
        eye = tip + v3(0.2, 0.0, 0.8)
        P.add(S(eye, sk.eye, m.eye, "stalk%d" % s))
        if f < st.get("glint_until", 99):
            P.mark(eye + v3(0.9, -0.4 * s, 0.9), M.GLINT)
    # Legs: knees up and out, pointed feet on the ground; a scuttle lifts them in two sets and strides them along the way
    # it goes; beaten, they curl up.
    g = p.legs
    curl = B.pick("curl", action, f)
    for s in (1, -1):
        for k, a0 in enumerate(g.at):
            lift, stride = gait(action, f, (0.5 if (k + (s > 0)) % 2 else 0.0), g.lift, g.stride)
            hip = at((a0, s * g.hip[0], g.hip[1]))
            knee = v3(da * lunge + a0 + da * stride * 0.5 - 0.3, s * (g.knee[0] - curl * 3.0) + db * stride * 0.5,
                      z + g.knee[1] + lift * 0.5 - curl * 1.0)
            foot = v3(da * lunge + a0 + da * stride - 0.9 + 0.3 * k, s * (g.foot[0] - curl * 4.6) + db * stride,
                      g.foot[1] + lift + curl * 3.6)
            if st.get("planted"):
                foot = foot + v3(-da * lunge, -db * lunge, 0.0)   # the feet stay planted as it rears back
            P.add(L(hip, knee, g.r[0][0], g.r[0][1], m.leg, "leg%d%d" % (s, k)), L(knee, foot, g.r[1][0], g.r[1][1], m.leg, "leg%d%d" % (s, k)))
    # Claws: arms from the shell's front corners to the chelae, held before it with the pincers turned in (a boxer's
    # guard); raised high and wide open in the tell; slammed shut before it on the strike, the struck side furthest.
    cl = p.claws
    for s in (1, -1):
        k = cl.get("scale", (1.0, 1.0))[0 if s > 0 else 1]
        pa, pb, pc, yaw_in, pitch_c, open_ = B.pick("claw", action, f, cl.rest)
        if action == "idle" and st.get("snap"):
            open_ = 0.2 + 0.55 * max(0.0, math.sin((f / 6.0 + (0.0 if s > 0 else 0.5)) * math.tau))
            pc += 0.3 * wave(action, f, 0.25 if s > 0 else 0.75)
        if st.get("kind") == "scuttle":
            pc += 0.5 * wave(action, f, 0.0 if s > 0 else 0.5)
            pb += 0.4 * wave(action, f, 0.25)
        if f in st.get("reach", ()):
            w = s * db + 0.4 * da                  # the claw on the struck side reaches furthest
            pa += 1.2 * w
            pb -= 0.8 * max(0.0, w) * s * 0
        if k != 1.0:
            # A great claw is held further forward, in toward the middle and a little higher: before the face.
            pa, pb, pc = pa + 2.4 * (k - 1.0), pb - 2.0 * (k - 1.0), pc + 1.2 * (k - 1.0)
        palm = at((pa, s * pb, pc))
        elbow = at((pa * 0.55 + 1.6, s * (pb + 2.8), pc * 0.5 + 0.4))
        cm = bm @ rot("c", s * yaw_in) @ rot("b", pitch_c)
        P.add(L(at((cl.root[0], s * cl.root[1], cl.root[2])), elbow, 1.35 * min(k, 1.25), 1.25 * min(k, 1.25), m.claw, "arm%d" % s),
              L(elbow, palm, 1.25 * min(k, 1.25), 1.4 * k, m.claw, "arm%d" % s))
        P.add(E(palm, (2.8 * k, 1.6 * k, 2.3 * k), m.claw, "claw%d" % s, cm),
              E(palm + cm @ v3(2.9 * k, 0.0, -0.7 * k), (1.9 * k, 1.0 * k, 1.0 * k), m.claw, "claw%d" % s, cm),
              E(palm + cm @ v3(4.6 * k, 0.0, -0.6 * k), (1.2 * k, 0.8 * k, 0.75 * k), m.tip, "claw%d" % s, cm))
        dm = cm @ rot("b", 12.0 + open_ * 42.0)
        hinge = palm + cm @ v3(1.3 * k, 0.0, 1.1 * k)
        P.add(E(hinge + dm @ v3(2.0 * k, 0.0, 0.2 * k), (1.9 * k, 0.95 * k, 0.85 * k), m.claw, "dactyl%d" % s, dm),
              E(hinge + dm @ v3(3.6 * k, 0.0, 0.1 * k), (1.1 * k, 0.75 * k, 0.7 * k), m.tip, "dactyl%d" % s, dm))
        P.mark(palm + cm @ v3(1.0 * k, 0.0, 2.3 * k), M.RAMPS[m.claw][4])
        if k > 1.0 and m.get("pearl"):
            for t in (-0.5, 0.4):        # the shield claw's crusted rim, a pearl in it
                P.mark(palm + cm @ v3(t * 2.2 * k, -0.9 * k, 1.9 * k), M.RAMPS[m.pearl][3])
        if action == "attack" and f in st.get("dust", ()):
            tipp = palm + cm @ v3(4.6 * k, 0.0, -0.8 * k)
            for k in range(5):
                ang = math.radians(k * 72.0 + f * 30.0)
                P.fx.append((v3(tipp[0] + math.cos(ang) * (1.6 + f), tipp[1] + math.sin(ang) * (1.6 + f), 0.3 + (k % 2) * 0.6),
                             M.DUST if k % 2 else M.DUST_DIM))
    roll = B.pick("roll", action, f)
    if roll:
        edge, back = st.edge
        P.m = rot("a", roll)
        turned = P.m @ v3(0.0, 0.0, Z)
        r = math.sin(math.radians(roll))
        h = Z + (edge - Z) * r if roll <= 90.0 else back + (edge - back) * r   # over its edge onto its back
        P.shift = v3(-turned[0], -turned[1], h - turned[2])
    sq = st.get("squash", {}).get(f)
    if sq is not None:
        P.squash(sq[0], sq[1], sq[2], (0.0, 0.0, 0.0))
    return P


# ================================================================================================= the sandstorm scorpion (M3)
# The sandstorm scorpion (`tail`): a dog-sized desert scorpion whose carapace has fused with wind-blown sand into plates
# of rough amber desert glass, low over its eight legs, walking the way it faces (not sideways, as the crabs do). A
# sand-gold prosoma (its eyes on top, a pair in the middle, a few at its front corners) and a segmented abdomen behind it,
# an amber glass plate glinting on each segment, a bone-pale belly; two pincers held before it (an arm of two joints, the
# chela's palm, a fixed finger and a moving one, umber-tipped); four legs a side, knees up, umber at the knees and the
# feet; its tail of five segments curled up and forward over its back, a venom-amber telson at its end with a dark
# umber barb. Sand streams off its back.
#
# Channels: `lunge`, `bob`, `pitch` (+ nose up), `roll` (over onto its back as it dies), `tail` (each segment's angle and
# the telson's, degrees from straight back toward straight up and on over forward), `claw` (ahead, out, open), `glow` (the
# telson's), `sting` (the venom spark and the sand burst of the blow), `chips` (glass chips flying when struck), `curl`
# (its legs curled), `crack` (its carapace cracked), `pour` (0..1: the sand poured out of it in heaps), `fade`.
SCORPION_STYLES = {
    "sting_ready": {"bob_amp": 0.2, "flex": True, "sway": 6.0},
    "skitter": {"kind": "scuttle", "bob_amp": 0.3, "sway": 3.0},
    "tail_arc": {"lunge": (-0.4, -0.8, -1.1, -1.2), "pitch": (2.0, 4.0, 5.0, 5.0), "bob": (0.2, 0.4, 0.5, 0.5),
                 "tail": ((48.0, 90.0, 130.0, 164.0, 194.0, 226.0), (56.0, 98.0, 138.0, 172.0, 202.0, 236.0),
                          (62.0, 104.0, 144.0, 178.0, 208.0, 244.0), (64.0, 106.0, 146.0, 180.0, 210.0, 246.0)),
                 "claw": ((5.4, 3.0, 0.5), (5.0, 3.6, 0.8), (4.8, 4.0, 1.0), (4.8, 4.1, 1.0)), "glow": (0.5, 1.0, 1.5, 2.0)},
    "tail_stab": {"lunge": (0.4, 2.2, 2.0, 1.3, 0.6, 0.2), "pitch": (2.0, -12.0, -10.0, -5.0, -2.0, 0.0), "bob": (0.4, -0.4, -0.4, -0.2, 0.0, 0.0),
                  "tail": ((64.0, 106.0, 146.0, 180.0, 210.0, 246.0), (78.0, 128.0, 170.0, 196.0, 218.0, 232.0),
                           (76.0, 124.0, 166.0, 192.0, 216.0, 232.0), (66.0, 110.0, 150.0, 182.0, 208.0, 236.0),
                           (54.0, 96.0, 136.0, 170.0, 198.0, 228.0), (44.0, 84.0, 124.0, 158.0, 188.0, 218.0)),
                  "reach": (0.0, 3.6, 3.2, 1.6, 0.6, 0.0),
                  "claw": ((5.0, 4.0, 1.0), (5.8, 3.4, 1.0), (5.8, 3.4, 0.8), (5.4, 3.2, 0.5), (5.2, 3.0, 0.3), (5.0, 2.9, 0.2)),
                  "glow": (2.0, 2.0, 1.0, 0.0, 0.0, 0.0), "sting": (0.0, 1.0, 0.5, 0.0, 0.0, 0.0)},
    "chip_recoil": {"lunge": (-2.2, -1.2, -0.4), "pitch": (10.0, 4.0, 0.0), "bob": (0.6, 0.3, 0.0), "chips": (1.0, 0.6, 0.3),
                    "tail": ((30.0, 66.0, 104.0, 140.0, 172.0, 204.0), (34.0, 72.0, 112.0, 148.0, 178.0, 208.0),
                             (38.0, 78.0, 118.0, 152.0, 182.0, 212.0)),
                    "claw": ((4.4, 3.6, 0.9), (4.6, 3.3, 0.6), (4.9, 3.0, 0.4))},
    "flip_pour": {"lunge": (-0.6, -0.8, -0.8, -0.8, -0.8, -0.8, -0.8, -0.8), "pitch": (14.0, 10.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                  "roll": (0.0, 40.0, 110.0, 165.0, 178.0, 176.0, 178.0, 178.0), "curl": (0.0, 0.2, 0.5, 0.8, 1.0, 1.0, 1.0, 1.0),
                  "tail": ((50.0, 92.0, 132.0, 166.0, 196.0, 226.0), (30.0, 60.0, 92.0, 124.0, 156.0, 190.0),
                           (14.0, 34.0, 60.0, 90.0, 120.0, 150.0), (6.0, 20.0, 40.0, 64.0, 92.0, 124.0),
                           (2.0, 12.0, 28.0, 50.0, 76.0, 104.0), (2.0, 10.0, 24.0, 44.0, 68.0, 96.0),
                           (2.0, 10.0, 24.0, 44.0, 68.0, 96.0), (2.0, 10.0, 24.0, 44.0, 68.0, 96.0)),
                  "claw": ((5.0, 4.0, 0.9), (4.6, 4.4, 0.8), (4.0, 4.6, 0.6), (3.8, 4.4, 0.4), (3.8, 4.2, 0.4), (3.8, 4.2, 0.4),
                           (3.8, 4.2, 0.4), (3.8, 4.2, 0.4)),
                  "crack": (0.0, 0.0, 0.3, 0.6, 1.0, 1.0, 1.0, 1.0), "pour": (0.0, 0.0, 0.0, 0.2, 0.45, 0.7, 0.9, 1.0),
                  "fade": (0.0, 0.0, 0.0, 0.0, 0.0, 0.25, 0.55, 0.85), "dark_from": 3},
}
STYLES.update(SCORPION_STYLES)
SCORPION = {
    "Z": 1.9,
    "prosoma": {"at": (1.9, 0.0, 0.1), "r": (2.0, 1.75, 0.95)},
    "segments": ((0.0, 1.95, 0.95), (-1.15, 2.0, 0.95), (-2.3, 1.95, 0.92), (-3.45, 1.8, 0.88), (-4.5, 1.55, 0.82)),
    "seg_len": 0.75,
    "eyes": ((3.0, 0.32, 0.85), (3.75, 1.1, 0.55)),
    "tail": {"base": (-5.1, 0.0, 0.45), "len": (1.45, 1.4, 1.35, 1.3, 1.25), "r": (0.78, 0.72, 0.66, 0.6, 0.56),
             "rest": (40.0, 80.0, 120.0, 155.0, 185.0, 215.0), "telson": (1.0, 0.72, 0.72), "barb": 1.1},
    "claws": {"root": (3.4, 1.15, 0.0), "rest": (5.2, 3.2, 0.4), "palm": (1.3, 0.85, 0.75), "finger": 1.6},
    "legs": {"at": (2.2, 1.1, 0.0, -1.1), "hip": (1.4, -0.2), "knee": (4.0, 0.9), "foot": (5.2, 0.0), "lift": 1.2, "stride": 1.0,
             "r": (0.42, 0.3)},
}
VARIANTS.update({
    "scorpion": {"parts": SCORPION, "mats": {"body": "ssc_sand", "leg": "ssc_leg", "glass": "ssc_glass", "umber": "ssc_umber",
                                             "belly": "ssc_belly", "venom": "ssc_venom", "grain": "ssc_grain"},
                 "motion": {"idle": "sting_ready", "walk": "skitter", "windup": "tail_arc", "attack": "tail_stab", "hurt": "chip_recoil",
                            "death": "flip_pour"}},
})


def _scorpion(B, action: str, f: int) -> Pose:
    """M3, the sandstorm scorpion (see SCORPION_STYLES): low on its legs, its pincers flexing, its tail swaying; it skitters,
    its legs in two alternating sets; in its tell its tail climbs into a high arc forward over its back, the telson
    glowing, its pincers gaping; it pitches nose-down and stabs forward with its tail over its open claws (a venom spark,
    a burst of sand); struck, glass chips fly off it; beaten, it rears, flips onto its back, curls its legs, its carapace
    cracks and the sand pours out of it into heaps as it fades."""
    P = Pose()
    p, m = B.parts, B.mats
    st = B.style(action)
    lunge = B.pick("lunge", action, f)
    bob = B.pick("bob", action, f)
    pitch = B.pick("pitch", action, f)
    roll = B.pick("roll", action, f)
    glow = B.pick("glow", action, f)
    sting = B.pick("sting", action, f)
    chips = B.pick("chips", action, f)
    curl = B.pick("curl", action, f)
    crack = B.pick("crack", action, f)
    pour = B.pick("pour", action, f)
    fade = B.pick("fade", action, f)
    reach = B.pick("reach", action, f)
    tl = p.tail
    angles = list(B.pick("tail", action, f, tl.rest))
    ca, cb, co = B.pick("claw", action, f, p.claws.rest)
    sway = 0.0
    if action == "idle":
        bob = st.bob_amp * wave(action, f)
        sw = math.sin(f / 6.0 * math.tau)
        angles = [a + 4.0 * sw * (i + 1) / len(angles) for i, a in enumerate(angles)]
        co = 0.25 + 0.4 * max(0.0, math.sin(f / 6.0 * math.tau + 1.0))
    elif st.get("kind") == "scuttle":
        bob = st.bob_amp * abs(math.sin(f / 8.0 * math.tau))
        sway = st.sway * math.sin(f / 8.0 * math.tau)
    dead = action == "death" and f >= st.get("dark_from", 99)
    # On its back the body rests on its rounded back: its middle sinks to the plates' height.
    flip = math.sin(math.radians(min(roll, 90.0))) if roll else 0.0
    z = p.Z + bob - (p.Z - 1.0) * flip * 0.6
    C = v3(lunge, 0.0, z)
    bm = rot("a", roll) @ rot("b", pitch) @ rot("c", sway)
    at = lambda q: C + bm @ v3(q)

    def carapace(cen, r, plates=True):
        def paint(q, n):
            loc = (q - cen) @ bm
            nz = (n @ bm)[:, 2]
            belly = nz < -0.3
            plate = plates & (nz > 0.45) & (np.abs(loc[:, 1]) < r[1] * 0.72)
            seam = (np.abs(loc[:, 1]) > r[1] * 0.64) & (np.abs(loc[:, 1]) < r[1] * 0.8) & (nz > 0.2)
            cracks = np.zeros(len(q), dtype=bool)
            if crack > 0.0:
                cracks = (np.abs(((loc[:, 0] * 1.7 + loc[:, 1] * 2.3) % 1.4) - 0.7) < 0.08 * crack) & (nz < 0.0)
            names = np.where(belly, m.belly, np.where(plate, m.glass, m.body)).astype(object)
            bias = np.where(cracks, -3, np.where(seam & ~belly, -1, 0))
            return names, bias.astype(np.int16)
        return paint

    # The legs, under it: four a side, knees up and out, the feet fanned (the front ones ahead, the hind ones back),
    # umber at the knee and the foot; in two alternating sets as it skitters; curled up as it lies on its back.
    g = p.legs
    for s in (1, -1):
        for k, a0 in enumerate(g.at):
            lift, stride = gait(action, f, (0.5 if (k + (s > 0)) % 2 else 0.0), g.lift, g.stride)
            fan = (1.5 - k) * 1.5
            hip = at((a0, s * g.hip[0], g.hip[1]))
            if roll > 60.0:
                # On its back: the legs curled up over its belly, kicking.
                knee = at((a0 + fan * 0.3, s * (g.knee[0] - 1.2 * curl), -1.4 - 1.0 * curl))
                foot = at((a0 + fan * 0.2, s * (g.foot[0] - 3.2 * curl), -2.0 - 0.3 * curl + 0.4 * math.sin(f * 1.7 + k)))
            else:
                knee = C + v3(a0 + fan * 0.5 + stride * 0.5, s * g.knee[0], g.knee[1] + lift * 0.5)
                foot = v3(lunge + a0 + fan + stride, s * g.foot[0], lift)
            P.add(L(hip, knee, g.r[0], g.r[0] * 0.9, m.leg, "leg%d%d" % (s, k)), L(knee, foot, g.r[0] * 0.85, g.r[1] * 0.7, m.leg, "leg%d%d" % (s, k)))
            P.add(S(knee, g.r[0] * 0.95, m.umber, "leg%d%d" % (s, k), line=False))
            P.add(L(foot + (knee - foot) * 0.25, foot, g.r[1] * 0.8, g.r[1] * 0.5, m.umber, "leg%d%d" % (s, k), line=False))
    # The body: the prosoma and the abdomen's segments, an amber glass plate on each, a seam down either side.
    pr = p.prosoma
    pc = at(pr.at)
    P.add(E(pc, pr.r, m.body, "body", bm, carapace(pc, pr.r)))
    for k, (sx, sy, sz) in enumerate(p.segments):
        cen = at((sx, 0.0, 0.05 * k))
        rr = (p.seg_len, sy, sz)
        P.add(E(cen, rr, m.body, "body", bm, carapace(cen, rr)))
        if not dead and k % 2 == 0:
            P.mark(at((sx + 0.2, -0.5 + 0.3 * k, sz + 0.12)), M.SSC_GLINT)
    if not dead:
        for (ea, eb, ec) in p.eyes:
            for s in (1, -1):
                P.mark(at((ea, s * eb, ec)), M.SSC_EYE)
    # The tail: five segments from the abdomen's end, each turned on by its angle (from straight back over toward
    # straight forward), the telson's bulb of venom and its dark barb.
    pts = [at(tl.base)]
    for i, (ln, r_) in enumerate(zip(tl.len, tl.r)):
        th = math.radians(angles[i])
        d = bm @ v3(-math.cos(th), 0.0, math.sin(th))
        nxt = pts[-1] + d * ln * (1.0 + 0.12 * reach * i / 4.0)
        cen = (pts[-1] + nxt) * 0.5
        sm = np.stack([d, bm @ v3(0.0, 1.0, 0.0), np.cross(d, bm @ v3(0.0, 1.0, 0.0))], axis=1)
        P.add(E(cen, (ln * 0.62, r_, r_ * 0.95), m.body, "tail", sm, carapace(cen, (ln, r_, r_), plates=i % 2 == 0)))
        pts.append(nxt)
    th = math.radians(angles[5])
    d = bm @ v3(-math.cos(th), 0.0, math.sin(th))
    tc = pts[-1] + d * tl.telson[0] * 0.9
    tmm = np.stack([d, bm @ v3(0.0, 1.0, 0.0), np.cross(d, bm @ v3(0.0, 1.0, 0.0))], axis=1)
    sw_ = 1.0 + 0.15 * min(glow, 2.0)
    P.add(E(tc, tuple(r * sw_ for r in tl.telson), m.venom, "telson", tmm))
    d2 = bm @ v3(-math.cos(th + 0.7), 0.0, math.sin(th + 0.7))
    bt = tc + d * tl.telson[0] * 0.6 + d2 * tl.barb
    P.add(L(tc + d * tl.telson[0] * 0.6, bt, 0.34, 0.08, m.umber, "barb", line=False))
    if glow >= 1.0 and not dead:
        for k in range(8):
            a = math.radians(k * 45.0 + f * 30.0)
            P.glow.append((tc + v3(math.cos(a) * 1.4, math.sin(a) * 1.4, 0.4 * math.sin(a * 2.0)), M.SSC_VENOM_GLOW if k % 2 else M.SSC_VENOM))
    if sting > 0.0:
        for k in range(10):
            a = math.radians(k * 36.0)
            rr = 0.9 + 1.4 * sting * (1 + k % 2)
            P.glow.append((bt + v3(math.cos(a) * rr, math.sin(a) * rr, 0.5 * math.sin(a)), M.SSC_VENOM if k % 2 else M.SSC_VENOM_HOT))
        for k in range(12):
            a = math.radians(k * 30.0 + 15.0)
            rr = 2.0 + 1.6 * sting + (k % 3) * 0.5
            P.fx.append((v3(bt[0] + math.cos(a) * rr * 0.8, math.sin(a) * rr, 0.3 + (k % 3) * 0.5), M.DUST if k % 2 else M.DUST_DIM))
    # The pincers: an arm of two joints from the prosoma's front corners, the chela held before it, its moving finger
    # opening outward (gaping in the tell).
    cl = p.claws
    for s in (1, -1):
        if action == "idle":
            o = co * (1.0 if s > 0 else 0.7)
        else:
            o = co
        root = at((cl.root[0], s * cl.root[1], cl.root[2]))
        palm = at((ca, s * cb, 0.55))
        elbow = at(((cl.root[0] + ca) * 0.5 + 0.2, s * (cb + 1.3), 0.9))
        P.add(L(root, elbow, 0.62, 0.55, m.body, "arm%d" % s), L(elbow, palm, 0.55, 0.7, m.body, "arm%d" % s))
        P.add(S(elbow, 0.58, m.umber, "arm%d" % s, line=False))
        yaw = -s * 18.0
        cm = bm @ rot("c", yaw)
        P.add(E(palm, cl.palm, m.body, "claw%d" % s, cm, carapace(palm, cl.palm)))
        fx_ = palm + cm @ v3(cl.palm[0] * 0.7, -s * 0.35, 0.0)
        tip = fx_ + cm @ v3(cl.finger, -s * 0.15, -0.1)
        P.add(L(fx_, tip, 0.42, 0.18, m.body, "claw%d" % s), L(tip - (tip - fx_) * 0.3, tip, 0.25, 0.14, m.umber, "claw%d" % s, line=False))
        dm = cm @ rot("c", s * (10.0 + 40.0 * o))
        hx = palm + cm @ v3(cl.palm[0] * 0.6, s * 0.4, 0.05)
        dt = hx + dm @ v3(cl.finger * 1.05, s * 0.1, 0.0)
        P.add(L(hx, dt, 0.4, 0.17, m.body, "dactyl%d" % s), L(dt - (dt - hx) * 0.3, dt, 0.24, 0.13, m.umber, "dactyl%d" % s, line=False))
    # Sand streaming off its back; glass chips flying when struck; the sand poured out of it in heaps as it dies.
    if action in ("idle", "walk", "windup") and not dead:
        for k in range(5):
            u = (k * 0.29 + f * 0.13) % 1.0
            P.fx.append((at((-1.0 - 5.0 * u, (k - 2.0) * 0.7, 1.4 + 0.8 * u)), M.SSC_SAND if k % 2 else M.SSC_SAND_DIM))
    if chips > 0.0:
        for k in range(8):
            a = math.radians(k * 45.0 + 20.0)
            rr = 2.4 + 2.6 * (1.0 - chips) + (k % 2) * 0.6
            P.fx.append((C + v3(math.cos(a) * rr, math.sin(a) * rr, 1.5 + (k % 3) * 0.7), M.RAMPS[m.glass][4 if k % 2 else 3]))
    if pour > 0.0:
        for s in (1, -1):
            for j, (hx_, hy) in enumerate(((0.8, 2.2), (-2.0, 2.4), (-4.0, 1.8))):
                rr = (1.4 + 0.5 * (j % 2)) * pour
                if rr > 0.15:
                    P.add(E(v3(lunge + hx_, s * (hy + 0.6 * pour), rr * 0.25), (rr * 1.2, rr, rr * 0.45), m.grain, "heap", None))
        for k in range(6):
            u = (k * 0.31 + f * 0.17) % 1.0
            P.fx.append((at((-1.0 * k + 1.0, (1 if k % 2 else -1) * 1.8, -0.5 - 1.2 * u)), M.SSC_SAND))
    if fade > 0.0:
        P.dissolve = fade
        P.dissolve_col = M.SSC_SAND
    return P
