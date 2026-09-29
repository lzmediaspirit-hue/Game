"""The marsh leech: a long olive slug in soft rings, teal spots down its back, a paler belly and a round pink mouth at
its front. It pulses while idle and creeps like an inchworm, a hump travelling down its length. Its tell: it rears its
front half up in an S, the mouth opening wide on its ring of teeth. It lunges mouth first, latches (the hit) and pulses
as it drinks, then lets go and draws back; struck, it contracts; beaten, it writhes, shrivels and sags flat.
"""
from __future__ import annotations

import math

import numpy as np

from . import mats as M
from .motion import pick, wave
from .sculpt import E, L, Pose, S, rot, v3

N = 9          # rings

LUNGE = {"windup": (-0.6, -1.2, -1.6, -1.8), "attack": (3.0, 5.2, 5.0, 4.2, 2.4, 0.8), "hurt": (-2.0, -1.2, -0.4)}
# How high the front rears (the fore third lifting in an S) and how wide the mouth opens.
REAR = {"windup": (2.6, 5.2, 7.4, 8.4), "attack": (3.0, 0.4, 0.2, 0.4, 0.8, 0.4), "hurt": (1.4, 0.6, 0.0),
        "death": (3.0, 1.0, 2.4, 0.6, 0.2, 0.0, 0.0, 0.0)}
GAPE = {"idle": (0.2, 0.3, 0.2, 0.1, 0.2, 0.3), "windup": (0.4, 0.7, 1.0, 1.1), "attack": (1.0, 0.2, 0.2, 0.3, 0.5, 0.3),
        "hurt": (0.0, 0.1, 0.2), "death": (0.8, 0.4, 0.6, 0.2, 0.1, 0.0, 0.0, 0.0)}
SQUASH = {"attack": (1.18, 0.94, 1.0, 1.0, 1.0, 1.0), "hurt": (0.8, 0.9, 1.0), "windup": (0.96, 0.92, 0.9, 0.88)}
FLAT = {"death": (0.0, 0.05, 0.1, 0.25, 0.4, 0.55, 0.62, 0.66)}
WRITHE = {"death": (1.0, -1.0, 0.8, -0.5, 0.2, 0.0, 0.0, 0.0), "hurt": (0.6, -0.4, 0.0)}


def leech(action: str, f: int) -> Pose:
    P = Pose()
    lunge = pick(LUNGE, action, f)
    rear = pick(REAR, action, f)
    gape = pick(GAPE, action, f)
    length = pick(SQUASH, action, f, 1.0)
    flat = pick(FLAT, action, f)
    writhe = pick(WRITHE, action, f)
    drink = 0.4 * math.sin(f * 2.2) if action == "attack" and f in (2, 3) else 0.0
    segs = []
    for k in range(N):
        u = k / (N - 1)                       # 0 at the tail, 1 at the mouth
        a = (-8.4 + 16.0 * u) * length + lunge * u
        hump = 0.0
        if action == "walk":                  # an inchworm's hump travelling tailward
            ph = f / 8.0 * math.tau - u * 4.5
            hump = max(0.0, math.sin(ph)) ** 2 * 2.2
            a -= 0.9 * math.cos(ph) * (0.4 + u)
        elif action == "idle":
            hump = max(0.0, math.sin(f / 6.0 * math.tau - u * 3.0)) * 0.5
        up = max(0.0, u - 0.52) / 0.48
        lift = rear * up * up * (3.0 - 2.0 * up)
        r = (1.3 + 2.1 * math.sin(math.pi * (0.12 + 0.7 * u)) ** 0.8) * (1.0 + drink * (1.0 - u) * 0.3)
        side = writhe * 2.2 * math.sin(u * math.pi * 1.6 + f)
        zc = (r * 0.82 + hump) * (1.0 - flat) + lift
        segs.append((v3(a - lift * 0.45, side, max(zc, 0.9 * (1.0 - flat) + 0.5)), r))

    def skin(q, n):
        """Soft rings (a groove every 2.3 px along it with a lit ridge behind), two ochre stripes down its back, a paler
        belly."""
        belly = n[:, 2] < -0.35
        ph = (q[:, 0] - 0.4 * np.abs(q[:, 1])) % 2.3
        stripe = (np.abs(np.abs(q[:, 1]) - 1.0) < 0.3) & (n[:, 2] > 0.35)
        bias = np.where(ph < 0.85, -1, np.where(ph < 1.3, 1, 0))
        names = np.where(belly, "leech_belly", np.where(stripe, "leech_stripe", "leech")).astype(object)
        return names, np.where(belly, 0, bias).astype(np.int16)

    for k in range(N - 1):
        (p0, r0), (p1, r1) = segs[k], segs[k + 1]
        P.add(L(p0, p1, r0 * (1.0 - flat * 0.3), r1 * (1.0 - flat * 0.3), "leech", "body", skin, caps=True))
    for k, (p, r) in enumerate(segs[:-1]):
        if k % 2 == 0:
            for d in ((0.0, 0.9, r * 0.82), (0.5, 1.1, r * 0.78), (0.6, -1.0, r * 0.8), (1.1, -0.8, r * 0.72)):
                P.mark(p + v3(*d) * v3(1.0, 1.0, 1.0 - flat * 0.5), M.LEECH_SPOT)
    # The mouth: a pink ring at the front, opening wide on its teeth.
    head, r = segs[-1]
    tip = head + v3(r * 0.9, 0.0, 0.2 + rear * 0.12)
    mr = 0.9 + gape * 0.8
    P.add(E(tip, (0.7, mr * 1.3, mr * 1.2), "leech_mouth", "mouth", rot("b", -rear * 5.0)))
    if gape > 0.3:
        P.mark(tip + v3(0.8, 0.0, 0.0), M.RAMPS["leech_mouth"][0])
        for ang in range(0, 360, 60):
            P.mark(tip + v3(0.75, math.cos(math.radians(ang)) * mr * 0.9, math.sin(math.radians(ang)) * mr * 0.9), (0xF2, 0xE2, 0xC8, 255))
    if action == "attack" and f in (1, 2):
        for d in ((1.6, 0.6, 0.8), (1.9, -0.7, 1.4), (2.2, 0.2, 2.0)):
            P.glow.append((tip + v3(*d), M.GLINT))
    if action == "death" and f >= 5:
        P.dissolve = (0.0, 0.0, 0.0, 0.0, 0.0, 0.15, 0.3, 0.45)[f]
        P.dissolve_col = (0x7A, 0x8A, 0x3C, 200)
    return P
