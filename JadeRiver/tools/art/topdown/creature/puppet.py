"""The Trial Puppet: a sparring figure of carved timber on brass ball joints, rope bound at the wrists, the sect's jade
sash across its chest and a jade plate on its back, a jade tuft on its crown and carved slits for eyes (as on its
side-view sheet); a head taller than a disciple. It sways on guard with its fists up and marches with them up. Its
tell: it twists back, drawing its right palm to its hip while the left reaches out, and Qi gathers in a jade ring at the
drawn palm. It steps in and drives the palm out, the ring bursting at the knuckles, and over-rotates through the blow;
struck, it rocks back on its joints; beaten, its joints give: the head drops, the knees fold, and it topples onto its
side, the jade on its crown going dark.
"""
from __future__ import annotations

import math

import numpy as np

from figure.geom import ik2

from . import mats as M
from .motion import pick, wave
from .sculpt import E, L, Pose, S, rot, v3

HIP = 15.6

LEAN = {"windup": (-4.0, -8.0, -10.0, -11.0), "attack": (6.0, 12.0, 12.0, 14.0, 6.0, 2.0), "hurt": (-12.0, -6.0, -2.0),
        "death": (-6.0, 4.0, 10.0, 18.0, 16.0, 14.0, 14.0, 14.0)}
TWIST = {"windup": (-10.0, -22.0, -30.0, -34.0), "attack": (-10.0, 24.0, 30.0, 36.0, 16.0, 4.0), "hurt": (8.0, -4.0, 0.0)}
STEP = {"windup": (-0.4, -0.8, -1.0, -1.2), "attack": (1.6, 3.4, 3.6, 3.4, 2.0, 0.8), "hurt": (-2.0, -1.2, -0.4)}
SINK = {"windup": (0.2, 0.5, 0.8, 1.0), "attack": (0.6, 1.2, 1.1, 0.8, 0.4, 0.1), "hurt": (0.4, 0.2, 0.0),
        "death": (0.0, 0.6, 3.0, 6.0, 6.4, 6.6, 6.6, 6.6)}
DROOP = {"death": (0.0, 18.0, 26.0, 30.0, 30.0, 30.0, 30.0, 30.0), "hurt": (-14.0, -4.0, 0.0)}
ROLL = {"death": (0.0, 0.0, 0.0, 16.0, 46.0, 76.0, 88.0, 86.0)}
# The right (striking) hand and the left: (ahead, out, up) from the shoulder's height at the chest.
RIGHT = {"windup": ((0.6, -4.6, -2.0), (-1.4, -4.8, -3.6), (-2.6, -4.6, -4.4), (-3.0, -4.4, -4.6)),
         "attack": ((3.2, -3.6, -1.2), (8.6, -2.2, -0.6), (8.8, -2.2, -0.6), (7.6, -2.6, -1.0), (4.4, -3.4, -1.6), (3.2, -3.6, -1.8)),
         "hurt": ((1.6, -6.4, 1.4), (2.6, -5.0, -1.0), (3.2, -3.8, -1.8))}
LEFT = {"windup": ((4.0, 3.4, -1.4), (5.6, 2.4, -1.0), (6.4, 1.6, -0.8), (6.6, 1.4, -0.8)),
        "attack": ((4.0, 3.6, -1.6), (1.0, 4.6, -2.8), (0.6, 4.8, -3.0), (1.4, 4.6, -2.4), (2.6, 4.0, -1.8), (3.2, 3.8, -1.8)),
        "hurt": ((1.0, 6.6, 1.6), (2.2, 5.0, -1.0), (3.0, 3.8, -1.8))}
QI = {"windup": (0.0, 0.3, 0.65, 1.0), "attack": (1.0, 1.6, 2.3, 0.0, 0.0, 0.0)}


def puppet(action: str, f: int) -> Pose:
    P = Pose()
    lean = pick(LEAN, action, f)
    twist = pick(TWIST, action, f)
    step = pick(STEP, action, f)
    sink = pick(SINK, action, f)
    sway = 0.35 * wave(action, f) if action == "idle" else 0.0
    bounce = 0.0
    if action == "walk":
        bounce = 0.5 * abs(math.sin(f / 8.0 * math.tau))
        twist = 6.0 * math.sin(f / 8.0 * math.tau)
    hip = v3(step, sway, HIP - sink + bounce)
    tm = rot("c", twist) @ rot("b", -lean) @ rot("a", sway * 3.0)
    up = lambda p: hip + tm @ v3(p)

    def grain(q, n):
        """Carved timber: the grain in fine dark streaks up the torso; the jade sash from the left shoulder to the right
        hip, and the jade plate on the back."""
        loc = (q - hip) @ tm
        nl = n @ tm
        sash = (np.abs((loc[:, 2] - 6.0) - loc[:, 1] * 0.95) < 1.05) & (nl[:, 0] > -0.2)
        plate = (nl[:, 0] < -0.5) & (loc[:, 2] > 4.6) & (loc[:, 2] < 9.4) & (np.abs(loc[:, 1]) < 2.4)
        streak = ((loc[:, 1] * 1.3 + loc[:, 0] * 0.4) % 1.9 < 0.4) & ~sash & ~plate
        names = np.where(sash | plate, "puppet_jade", "timber").astype(object)
        return names, np.where(streak, -1, 0).astype(np.int16)

    # Legs: a stride in the march, planted apart otherwise; knees folding as it sinks.
    for s in (1, -1):
        ph = f / 8.0 * math.tau + (0.0 if s > 0 else math.pi)
        stride = 2.8 * math.sin(ph) if action == "walk" else 0.0
        lift = 1.4 * max(0.0, math.cos(ph)) if action == "walk" else 0.0
        plant = (1.2 if s > 0 else -1.4) if action in ("windup", "attack") else 0.0
        foot = v3(stride + plant + 0.8 + (step if s > 0 else step * 0.5), s * 2.8, 1.0 + lift)
        top = hip + rot("c", twist * 0.4) @ v3(0.0, s * 2.3, -0.6)
        knee, end = ik2(top, foot, 7.4, 7.6, v3(1.0, 0.0, 0.0))
        P.add(L(top, knee, 1.75, 1.45, "timber", "leg%d" % s, grain), S(knee, 1.6, "brass", "leg%d" % s),
              L(knee, end, 1.45, 1.25, "timber", "leg%d" % s, grain),
              E(end + v3(0.9, 0.0, -0.2), (2.6, 1.4, 1.0), "timber_dark", "foot%d" % s))
    # The trunk: hips, waist, chest (the sash and back plate), a neck joint, the head.
    P.add(E(up((0.0, 0.0, 0.6)), (2.5, 3.8, 2.0), "timber", "body", tm, grain),
          E(up((0.0, 0.0, 3.4)), (1.9, 2.8, 1.8), "timber_dark", "body", tm),
          E(up((0.0, 0.0, 6.4)), (2.9, 4.6, 4.2), "timber", "body", tm, grain),
          S(up((0.0, 0.0, 11.0)), 1.15, "brass", "neck"))
    droop = pick(DROOP, action, f)
    hm = tm @ rot("b", -droop)
    hc = up((0.3, 0.0, 11.4)) + hm @ v3(0.0, 0.0, 2.6)
    P.add(E(hc, (2.7, 2.5, 3.0), "timber", "head", hm, grain))
    for s in (1, -1):
        P.mark(hc + hm @ v3(2.55, s * 1.0, 0.5), M.INKY)
        P.mark(hc + hm @ v3(2.6, s * 0.55, 0.5), M.INKY if action != "hurt" else M.RAMPS["timber"][1])
    P.mark(hc + hm @ v3(2.7, 0.0, -1.1), M.RAMPS["timber_dark"][0])
    dark = action == "death" and f >= 5
    jade = "timber_dark" if dark else "puppet_jade"
    tuft = hc + hm @ v3(-0.3, 0.0, 3.2)
    P.add(S(tuft, 1.05, jade, "tuft"), S(tuft + hm @ v3(-0.8, 0.3, 0.9), 0.8, jade, "tuft"))
    if not dark:
        P.mark(hc + hm @ v3(2.4, 0.0, 1.9), M.QI)      # the jade mark on the brow
    # Arms: brass shoulder balls, timber limbs, brass elbows, rope at the wrists, dark fists. Guard: fists up before
    # the chest; the march swings them.
    sw = 1.6 * math.sin(f / 8.0 * math.tau) if action == "walk" else 0.0
    guard = 0.4 * wave(action, f, 0.25) if action == "idle" else 0.0
    for s in (1, -1):
        sh = up((0.0, s * 5.1, 8.6))
        if s < 0 and action in RIGHT:
            rel = pick(RIGHT, action, f)
        elif s > 0 and action in LEFT:
            rel = pick(LEFT, action, f)
        elif action == "death":
            rel = (0.8, s * 5.8, -5.8 - min(f, 3) * 0.4)
        else:
            rel = (3.4 + sw * s, s * 3.4, -1.2 + guard)
        fist = up((rel[0], rel[1], 8.6 + rel[2]))
        elbow, end = ik2(sh, fist, 4.4, 4.2, tm @ v3(-0.6, s * 1.0, -1.0))
        P.add(S(sh, 1.6, "brass", "arm%d" % s), L(sh, elbow, 1.3, 1.2, "timber", "arm%d" % s, grain), S(elbow, 1.25, "brass", "arm%d" % s),
              L(elbow, end, 1.2, 1.1, "timber", "arm%d" % s, grain),
              S(elbow + (end - elbow) * 0.82, 1.2, "rope", "arm%d" % s),
              E(end, (1.7, 1.55, 1.55), "timber_dark", "arm%d" % s, tm))
        # Qi: a jade orb gathering at the drawn palm in the tell (a bright core in a glow, a ring turning round it),
        # bursting at the knuckles on the blow in a wide ring.
        q = pick(QI, action, f)
        if s < 0 and q > 0.0:
            c = end + tm @ v3(1.2 + (0.8 if action == "attack" else 0.0), 0.0, 0.0)
            core = 0.5 + 0.9 * min(q, 1.0) if action == "windup" or f == 0 else 0.6
            for dy in np.arange(-core * 2.2, core * 2.2 + 0.01, 0.55):
                for dz in np.arange(-core * 2.2, core * 2.2 + 0.01, 0.55):
                    d = math.hypot(dy, dz)
                    if d <= core * 2.2:
                        col = M.QI_BRIGHT if d < core * 0.9 else (M.QI if d < core * 1.6 else (0x4C, 0xB6, 0xA2, 150))
                        P.glow.append((c + tm @ v3(0.0, dy, dz), col))
            rr = 2.2 + q * 1.8
            n = 12 if q < 1.2 else 20
            for k in range(n):
                ang = math.radians(k * 360.0 / n + f * 15.0)
                col = M.QI_BRIGHT if k % 2 == 0 and q >= 1.0 else (M.QI if k % 3 else M.QI_DIM)
                P.glow.append((c + tm @ v3(0.0, math.cos(ang) * rr, math.sin(ang) * rr), col))
            if action == "windup" and f >= 1:
                for k in range(4):
                    P.glow.append((c + v3(-0.6 + k * 0.7, -1.4 + k * 0.9, 3.0 + k * 1.1 + f * 0.5), M.QI_DIM))
    roll = pick(ROLL, action, f)
    if roll:
        P.m = rot("a", roll)
        mid = 8.0
        turned = P.m @ v3(0.0, 0.0, mid)
        P.shift = v3(-turned[0], -turned[1], mid - turned[2] - (mid - 3.2) * math.sin(math.radians(min(roll, 90.0))))
    if action == "attack" and f == 1:
        P.squash(1.04, 1.0, 0.97, (step, 0.0, 0.0))
    return P
