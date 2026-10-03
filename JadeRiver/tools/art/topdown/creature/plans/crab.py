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


def pose(B, action: str, f: int, aim=(1.0, 0.0)) -> Pose:
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
