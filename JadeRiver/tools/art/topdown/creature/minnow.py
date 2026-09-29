"""The hollow minnow: a small river fish drained grey by the Hollow, swimming through the night air. It flies (the
enemy's `flying`): the view draws it at its hover, its shadow on the ground under it, so the fish is drawn round its
feet. A dark back and a pale belly, scale rows, a ragged dorsal fin, a forked tail, an empty white eye in a dark socket;
two grey strands trail and rise from its tail as its wake. It hangs and sways while idle and swims with a swish of its
whole body. Its tell: it curls into a C, tail bent hard back, and gapes. It darts in straight as a needle to nibble,
overshoots and curls back; struck, it jerks back rolling; beaten, it turns belly-up and comes apart into grey mist.
"""
from __future__ import annotations

import math

import numpy as np

from . import mats as M
from .motion import pick, wave
from .sculpt import E, L, Pose, S, chain, rot, v3

DART = {"windup": (-0.8, -1.6, -2.4, -2.8), "attack": (3.4, 6.0, 6.6, 5.4, 3.2, 1.2), "hurt": (-2.6, -1.6, -0.6)}
BOB = {"idle": (0.0, -0.4, -0.7, -0.6, -0.3, 0.0), "death": (0.0, -0.5, -1.0, -1.4, -1.8, -2.2, -2.6, -3.0)}
# The body's bend: the tail's swish (degrees, + toward its left) and how much the whole body curves with it.
SWISH = {"idle": (8.0, 14.0, 8.0, -4.0, -10.0, -2.0), "windup": (26.0, 42.0, 54.0, 58.0), "attack": (-20.0, -6.0, 10.0, 18.0, 10.0, 4.0),
         "hurt": (24.0, 10.0, 2.0), "death": (20.0, 30.0, 10.0, 0.0, 0.0, 0.0, 0.0, 0.0)}
NOSE = {"windup": (6.0, 10.0, 12.0, 14.0), "attack": (-4.0, -8.0, -6.0, -2.0, 0.0, 0.0), "hurt": (14.0, 6.0, 0.0)}
GAPE = {"windup": (0.4, 0.8, 1.0, 1.1), "attack": (1.0, 0.0, 0.0, 0.3, 0.2, 0.0), "death": (0.6, 0.8, 0.6, 0.4, 0.4, 0.4, 0.4, 0.4)}
STRETCH = {"attack": (1.18, 1.06, 0.94, 1.0, 1.0, 1.0), "hurt": (0.86, 1.0, 1.0), "windup": (1.0, 0.98, 0.96, 0.95)}
ROLL = {"hurt": (28.0, 14.0, 4.0), "death": (60.0, 120.0, 170.0, 178.0, 180.0, 180.0, 180.0, 180.0)}
MIST = {"death": (0.0, 0.0, 0.2, 0.42, 0.62, 0.8, 0.94, 1.0)}


def minnow(action: str, f: int) -> Pose:
    P = Pose()
    dart = pick(DART, action, f)
    bob = pick(BOB, action, f)
    if action == "walk":
        bob = 0.3 * wave(action, f)
    swish = pick(SWISH, action, f)
    if action == "walk":
        swish = 28.0 * math.sin(f / 8.0 * math.tau)
    nose = pick(NOSE, action, f)
    gape = pick(GAPE, action, f)
    flap = -10.0 - 20.0 * max(0.0, math.sin(f * 1.3)) if action in ("idle", "walk", "windup") else 0.0
    body_m = rot("b", nose) @ rot("c", -swish * 0.25)        # the head turns against the tail
    C = v3(dart, 0.0, bob)
    at = lambda p: C + body_m @ v3(p)

    def fish(q, n):
        """A dark back, a pale belly, rows of scales (a step lit every other half-row) and the lateral line."""
        nz = n[:, 2]
        back = nz > 0.5
        belly = nz < -0.35
        scale = ((np.floor((q[:, 0] - C[0]) * 0.9) + np.floor((q[:, 2] + 3.0) * 1.2)) % 2 == 0) & ~back & ~belly
        lateral = np.abs(q[:, 2] - C[2] - 0.2) < 0.25
        names = np.where(back, "minnow_back", np.where(belly, "minnow_belly", "minnow")).astype(object)
        return names, np.where(lateral, -1, np.where(scale, 1, 0)).astype(np.int16)

    P.add(E(at((0.0, 0.0, 0.0)), (4.4, 1.9, 2.4), "minnow", "body", body_m, fish),
          E(at((3.2, 0.0, 0.1)), (2.4, 1.75, 2.0), "minnow", "body", body_m, fish))
    tm = body_m @ rot("c", swish)
    piv = at((-3.2, 0.0, 0.0))
    P.add(E(piv + tm @ v3(-1.5, 0.0, 0.0), (2.2, 1.0, 1.4), "minnow", "body", tm, fish))
    for s in (1, -1):   # the forked tail: an upper and a lower lobe
        P.add(E(piv + tm @ v3(-4.1, 0.0, s * 0.95), (2.0, 0.35, 0.85), "minnow_fin", "tail", tm @ rot("b", -s * 38.0)))
    for a, h in ((-1.4, 1.0), (-0.3, 1.5), (0.8, 1.1), (1.7, 0.6)):   # the ragged dorsal fin
        P.add(E(at((a, 0.0, 2.1 + h * 0.5)), (0.6, 0.3, h), "minnow_fin", "dorsal", body_m))
    for s in (1, -1):
        P.add(E(at((1.6, s * 1.6, -0.8)), (1.3, 1.0, 0.3), "minnow_fin", "pec%d" % s, body_m @ rot("a", s * flap)))
        sock = at((3.2, 0.0, 0.1))
        P.mark(sock + body_m @ v3(1.0, s * 1.35, 0.9), M.RAMPS["minnow_back"][0])
        P.mark(sock + body_m @ v3(1.3, s * 1.3, 0.6), M.HOLLOW_EYE if action not in ("hurt", "death") else M.RAMPS["minnow_back"][0])
    P.mark(at((5.5, 0.0, -0.3)), M.FISH_MOUTH)
    if gape > 0.1:
        P.add(E(at((3.9, 0.0, -1.2 - gape * 0.4)), (1.5, 1.0, 0.45), "minnow_belly", "jaw", body_m @ rot("b", -30.0 * gape)))
        P.mark(at((5.1, 0.0, -0.8)), M.FISH_MOUTH)
    if action == "attack" and f == 1:
        for d in ((6.8, 0.0, 0.4), (7.4, 0.0, 0.9), (6.3, 0.0, 1.0)):
            P.glow.append((at(d), M.GLINT))
    # The wake: two grey strands trailing from the tail and rising, waving as it swims (thin in the dart).
    trail = {"attack": 7.0, "hurt": 3.4, "windup": 3.6}.get(action, 5.0 + 0.6 * wave(action, f) if action in ("idle", "walk") else 4.0)
    wv = 0.7 * wave(action, f) if action in ("idle", "walk") else 0.3
    if action != "death" or f < 3:
        for s in (1, -1):
            root = piv + tm @ v3(-5.6, s * 0.4, 0.3)
            back = tm @ v3(-1.0, 0.0, 0.0)
            pts = [root, root + back * trail * 0.35 + v3(0.0, s * 0.7 + wv, 0.3), root + back * trail * 0.7 + v3(0.0, s * 0.5 - wv, 0.8),
                   root + back * trail + v3(0.0, s * 1.2 + wv * 0.5, 1.4)]
            P.add(chain(pts, 0.45, 0.3, "strand", "strand%d" % s, line=False))
    roll = pick(ROLL, action, f)
    if roll:
        P.m = rot("a", roll)
    sa = pick(STRETCH, action, f, 1.0)
    if sa != 1.0:
        P.squash(sa, 1.0 / math.sqrt(sa), 1.0 / math.sqrt(sa), (dart, 0.0, bob))
    if action == "death":
        P.dissolve = pick(MIST, action, f)
        P.dissolve_col = M.MOTE
        for k in range(int(4 + f * 1.5)):
            ang = math.radians(k * 47.0 + f * 23.0)
            rr = 1.5 + f * 1.1 + (k % 3) * 0.7
            if f >= 2:
                P.fx.append((v3(math.cos(ang) * rr, math.sin(ang) * rr * 0.6, 0.4 + f * 0.9 + (k % 4) * 0.8), M.MOTE if k % 2 else M.MOTE_DIM))
    return P
