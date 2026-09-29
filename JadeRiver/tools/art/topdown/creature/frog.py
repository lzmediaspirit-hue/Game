"""The reed frog: leaf green with a gold stripe down each flank and darker spots, a pale belly, gold eyes set high. It
sits with its long hind legs folded at its sides and gulps while idle, and goes in hops: a crouch, a stretched leap,
the landing squashed. Its tell: it crouches low with its hind legs coiled and its throat sac puffs up big and pale. It
leaps at its prey, forefeet reaching (the jump kick), and lands squashed; struck, it is knocked back flat; beaten, it
flips onto its back, its legs splayed.
"""
from __future__ import annotations

import math

import numpy as np

from . import mats as M
from .motion import pick, wave
from .sculpt import E, L, Pose, S, rot, v3

Z = 4.6

# The hop: (height of the body over its rest, ahead, tilt nose-up, squash along c, the hind legs' stretch 0 folded .. 1)
HOP = {"walk": ((0.0, -1.2, 0.0, 0.84, 0.0), (0.4, -1.0, 8.0, 1.08, 0.4), (2.2, -0.4, 16.0, 1.14, 1.0), (3.2, 0.2, 10.0, 1.06, 1.0),
                (2.6, 0.8, -4.0, 1.0, 0.8), (1.0, 1.2, -10.0, 1.0, 0.4), (0.0, 1.2, -4.0, 0.82, 0.0), (0.0, 0.0, 0.0, 0.94, 0.0)),
       "windup": ((-0.4, -0.2, 4.0, 0.94, 0.0), (-0.9, -0.5, 8.0, 0.88, 0.0), (-1.3, -0.8, 11.0, 0.84, 0.0), (-1.5, -0.9, 12.0, 0.82, 0.0)),
       "attack": ((2.6, 2.6, 16.0, 1.2, 1.0), (4.0, 5.4, 4.0, 1.1, 1.0), (1.2, 6.4, -8.0, 0.92, 0.6), (0.0, 6.6, -4.0, 0.8, 0.0),
                  (0.0, 6.4, 0.0, 0.96, 0.0), (0.0, 6.2, 0.0, 1.0, 0.0)),
       "hurt": ((0.4, -2.4, -10.0, 0.82, 0.3), (0.2, -1.6, -4.0, 1.04, 0.1), (0.0, -0.6, 0.0, 1.0, 0.0)),
       "death": ((1.4, -0.6, 14.0, 1.1, 0.6), (2.4, -1.0, 20.0, 1.0, 0.8), (1.6, -1.2, 10.0, 1.0, 0.9), (0.6, -1.2, 0.0, 1.0, 1.0),
                 (0.0, -1.2, 0.0, 0.9, 1.0), (0.0, -1.2, 0.0, 1.0, 1.0), (0.0, -1.2, 0.0, 1.0, 1.0), (0.0, -1.2, 0.0, 1.0, 1.0))}
PUFF = {"idle": (0.0, 0.25, 0.5, 0.25, 0.0, 0.1), "windup": (0.35, 0.7, 1.0, 1.15), "attack": (0.4, 0.2, 0.1, 0.0, 0.0, 0.0),
        "hurt": (0.0, 0.0, 0.0)}
ROLL = {"death": (10.0, 50.0, 110.0, 160.0, 178.0, 174.0, 178.0, 178.0)}


def frog(action: str, f: int) -> Pose:
    P = Pose()
    hop, ahead, tilt, sq, stretch = pick(HOP, action, f, (0.0, 0.0, 0.0, 1.0, 0.0))
    if action == "idle":
        sq = 1.0 + 0.02 * wave(action, f)
    z = Z * sq + hop
    tm = rot("b", tilt)
    C = v3(ahead - 0.6, 0.0, z)
    at = lambda p: C + tm @ v3(p)

    def skin(q, n):
        """The pale belly underneath; a gold stripe down each flank; darker spots over the back."""
        loc = (q - C) @ tm
        nz = (n @ tm)[:, 2]
        b = np.abs(loc[:, 1])
        belly = nz < -0.35
        stripe = (b > 2.9) & (b < 3.6) & (nz > -0.15) & (nz < 0.6)
        spot = np.zeros(len(b), dtype=bool)
        for pa, pb, r in ((-1.8, 1.2, 0.7), (0.6, -1.6, 0.6), (-3.4, -0.6, 0.6), (1.8, 1.4, 0.5), (-0.6, 0.2, 0.5)):
            spot |= (loc[:, 0] - pa) ** 2 + (loc[:, 1] - pb) ** 2 < r * r
        names = np.where(belly, "frog_belly", np.where(stripe, "frog_stripe", "frog")).astype(object)
        return names, np.where(spot & ~belly & ~stripe & (nz > 0.3), -1, 0).astype(np.int16)

    P.add(E(C, (5.4, 4.2, 3.2 * sq), "frog", "body", tm, skin),
          E(at((4.4, 0.0, 0.6)), (3.3, 3.8, 2.5 * sq), "frog", "body", tm, skin))
    puff = pick(PUFF, action, f)
    # The throat sac: pale, puffing out under the chin (big in the tell).
    P.add(E(at((5.6, 0.0, -1.7 - puff * 0.4)), (1.8 + puff * 1.2, 2.5 + puff * 1.4, 1.1 + puff * 1.5), "frog_sac", "throat", tm))
    for s in (1, -1):
        eye = at((5.0, s * 2.2, 2.7 * sq))
        P.add(S(eye, 1.55, "frog_eye", "eye%d" % s))
        shut = action == "hurt" and f == 0 or action == "death" and f >= 4
        (P.mark if shut else P.eye)(eye + tm @ v3(1.2, s * 0.5, 0.6), M.RAMPS["frog"][1] if shut else M.INKY)
        P.mark(eye + tm @ v3(1.3, s * 0.3, 0.2), M.RAMPS["frog"][1] if shut else M.INKY)
        if not shut:
            P.mark(eye + tm @ v3(0.4, s * 0.1, 1.4), M.GLINT)
        P.mark(at((7.2, s * 1.4, -0.2)), M.RAMPS["frog"][0])      # the mouth's corner
        # Hind legs: folded at the sides (thigh forward, shin back, the long foot flat), trailing straight in a leap.
        hip = v3(ahead - 3.8, s * 3.4, z - 1.0)
        folded = (v3(ahead + 0.0, s * 5.2, 2.0), v3(ahead - 3.4, s * 5.4, 0.6))
        straight = (v3(ahead - 7.0, s * 3.8, z - 1.4), v3(ahead - 10.2, s * 3.6, z - 2.2))
        knee = folded[0] + (straight[0] - folded[0]) * stretch
        foot = folded[1] + (straight[1] - folded[1]) * stretch
        if action == "windup":
            knee = knee + v3(0.4, s * 0.4, -0.3 * f)
        P.add(E(hip + v3(0.8, 0.0, 0.0), (3.0, 1.8, 1.9), "frog", "hind%d" % s, rot("c", s * 20.0), skin),
              L(hip, knee, 1.6, 1.25, "frog", "hind%d" % s), L(knee, foot, 1.15, 0.85, "frog", "hind%d" % s),
              E(foot + v3(-0.9 if stretch > 0.5 else 1.0, 0.0, 0.0), (2.0, 1.4, 0.5), "frog_belly", "hind%d" % s))
        # Front legs: short props under the chest, reaching ahead in a leap.
        reach = 2.4 * stretch
        shoulder = at((3.6, s * 2.4, -1.2))
        hand = v3(ahead + 4.4 + reach, s * 3.0, 0.6 + (hop * 0.6 if stretch > 0.5 else 0.0))
        P.add(L(shoulder, hand, 0.9, 0.75, "frog", "arm%d" % s), E(hand, (1.1, 1.0, 0.45), "frog_belly", "arm%d" % s))
    if action == "walk" and f in (6, 7) or action == "attack" and f in (2, 3):
        for k in range(4):
            ang = math.radians(k * 90.0 + 45.0)
            P.fx.append((v3(ahead + math.cos(ang) * 5.6, math.sin(ang) * 5.0, 0.3), M.DUST_DIM))
    roll = pick(ROLL, action, f)
    if roll:
        P.m = rot("a", roll)
        turned = P.m @ v3(0.0, 0.0, z)
        P.shift = v3(-turned[0], -turned[1], z - turned[2] - (z - 3.0) * (1.0 if roll > 90 else math.sin(math.radians(roll))) + (0.4 if roll > 150 else 0.0))
    return P
