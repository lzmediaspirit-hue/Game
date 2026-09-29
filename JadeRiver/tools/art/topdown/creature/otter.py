"""The reed otter: a long, sleek brown body on short legs, darker paws, a pale muzzle, throat and chest, small round
ears, whiskers and a thick tapering tail. It looks about and grooms while idle, and runs in a bounding lope, its back
arching and stretching. Its tell: it sits up on its haunches (as its side-view sheet does), forepaws tucked, head up,
teeth bared. It drops and lunges to bite, shaking its prey; struck, it flinches back; beaten, it curls up on its side.
"""
from __future__ import annotations

import math

import numpy as np

from . import mats as M
from .motion import pick, wave
from .sculpt import E, L, Pose, S, rot, v3

Z = 5.0

LUNGE = {"windup": (-0.4, -0.8, -1.2, -1.2), "attack": (3.0, 5.4, 5.2, 4.4, 2.6, 0.8), "hurt": (-2.4, -1.4, -0.4),
         "death": (-0.6, -0.8, -0.8, -0.8, -0.8, -0.8, -0.8, -0.8)}
REAR = {"windup": (16.0, 34.0, 46.0, 50.0), "attack": (-8.0, -4.0, 0.0, 0.0, 0.0, 0.0), "hurt": (10.0, 2.0, 0.0),
        "death": (24.0, 10.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)}
HEAD = {"idle": (0.0, 6.0, 10.0, -8.0, -14.0, -4.0), "windup": (-6.0, -14.0, -22.0, -26.0), "attack": (-10.0, -18.0, -8.0, -14.0, -4.0, 0.0),
        "hurt": (20.0, 6.0, 0.0), "death": (20.0, 6.0, -6.0, -14.0, -18.0, -20.0, -20.0, -20.0)}
YAW = {"idle": (0.0, 18.0, 22.0, 0.0, -16.0, -8.0), "attack": (0.0, 0.0, 14.0, -14.0, 6.0, 0.0)}
GAPE = {"windup": (0.2, 0.4, 0.7, 0.8), "attack": (0.9, 0.1, 0.1, 0.0, 0.1, 0.0), "hurt": (0.5, 0.2, 0.0)}
SQUASH = {"attack": ((1.14, 0.9), (0.93, 1.05), (1.0, 1.0), (1.0, 1.0), (1.0, 1.0), (1.0, 1.0)), "hurt": ((0.88, 1.06), (1.03, 0.98), (1.0, 1.0))}
ROLL = {"death": (0.0, 0.0, 28.0, 60.0, 84.0, 90.0, 88.0, 90.0)}
CURL = {"death": (0.0, 0.0, 0.2, 0.4, 0.6, 0.8, 0.9, 1.0)}


def otter(action: str, f: int) -> Pose:
    P = Pose()
    lunge = pick(LUNGE, action, f)
    rear = pick(REAR, action, f)
    arch, bob = 0.0, 0.0
    if action == "walk":                        # the lope: arched, then stretched long
        arch = 10.0 * math.sin(f / 8.0 * math.tau)
        bob = 1.2 * max(0.0, math.sin(f / 8.0 * math.tau + 0.6))
    if action == "idle":
        bob = 0.12 * wave(action, f)
    curl = pick(CURL, action, f)
    z = Z + bob
    hips = v3(lunge - 4.6, 0.0, z)
    bm = rot("b", rear + arch * 0.5) @ rot("c", curl * 35.0)
    at = lambda p: hips + bm @ (v3(p) - v3(-4.6, 0.0, 0.0))

    def coat(q, n):
        """The pale throat and chest under the forebody, a sleek sheen of darker streaks along the back."""
        loc = (q - hips) @ bm
        nl = n @ bm
        pale = (nl[:, 2] < -0.05) & (nl[:, 0] > -0.3) & (loc[:, 0] > 3.0)
        streak = ((loc[:, 0] * 0.5 + np.abs(loc[:, 1]) * 0.9) % 1.6 < 0.5) & (nl[:, 2] > 0.2)
        return np.where(pale, "otter_pale", "otter").astype(object), np.where(streak & ~pale, -1, 0).astype(np.int16)

    hm_arch = rot("b", -arch * 0.6)
    P.add(E(at((0.8, 0.0, 0.3)), (6.0, 3.3, 3.1), "otter", "body", bm @ hm_arch, coat),
          E(hips, (3.9, 3.7, 3.4), "otter", "body", bm, coat),
          E(at((4.6, 0.0, 0.8)), (2.8, 2.8, 2.9), "otter", "body", bm, coat))
    gape = pick(GAPE, action, f)
    hm = bm @ rot("c", pick(YAW, action, f)) @ rot("b", -8.0 - rear * 0.9 + pick(HEAD, action, f))
    hc = at((7.4, 0.0, 1.6))
    hp = lambda p: hc + hm @ v3(p)
    P.add(E(hc, (2.9, 2.7, 2.5), "otter", "head", hm, coat),
          E(hp((2.4, 0.0, -0.6)), (1.6, 1.9, 1.3), "otter_pale", "head", hm))
    P.mark(hp((3.9, 0.0, -0.2)), M.INKY)                         # the nose
    if gape > 0.1:
        jm = hm @ rot("b", -gape * 30.0)
        P.add(E(hp((1.2, 0.0, -1.5)) + jm @ v3(1.4, 0.0, -0.2), (1.6, 1.3, 0.6), "otter_pale", "jaw", jm))
        for sd in (0.5, -0.5):
            P.mark(hp((3.2, sd, -1.1)), (0xF4, 0xEE, 0xDC, 255))
    for s in (1, -1):
        shut = action == "hurt" and f == 0 or action == "death" and f >= 4
        (P.mark if shut else P.eye)(hp((1.5, s * 1.65, 1.2)), M.RAMPS["otter"][1] if shut else M.INKY)
        if not shut:
            P.mark(hp((1.7, s * 1.5, 1.5)), M.GLINT)
        P.add(S(hp((-0.7, s * 2.2, 1.9)), 0.8, "otter_dark", "ear%d" % s))
        for w in range(3):
            P.mark(hp((2.6 + w * 0.4, s * (1.9 + w * 0.5), -0.4 - w * 0.3)), M.RAMPS["otter_pale"][4])
    # Legs: short, dark paws; the lope reaches with the fore pair and gathers the hind pair under; in the tell the
    # forepaws tuck against the chest.
    for k, (a0, b0, front) in enumerate(((3.6, 2.2, True), (3.6, -2.2, True), (-5.6, 2.5, False), (-5.6, -2.5, False))):
        ph = f / 8.0 * math.tau + (0.0 if front else math.pi)
        stride = 2.4 * math.cos(ph) if action == "walk" else 0.0
        up = 1.2 * max(0.0, math.sin(ph)) if action == "walk" else 0.0
        top = at((a0, b0, -1.6)) if front else v3(hips[0] - 1.0, b0, z - 1.8)
        if front and rear > 20.0:
            foot = top + bm @ v3(1.6, -b0 * 0.2, -1.4)
        elif front and curl > 0.2:
            foot = top + bm @ v3(1.8, 0.0, -2.0)
        else:
            foot = v3(top[0] + stride + (0.8 if front else 0.0), b0, 0.7 + up)
        P.add(L(top, foot, 1.25, 1.0, "otter", "leg%d" % k), E(foot + v3(0.5, 0.0, -0.1), (1.1, 0.9, 0.5), "otter_dark", "leg%d" % k))
    # The thick tail, tapering, wagging; laid along the ground in the tell as a prop.
    wag = 1.2 * wave(action, f) if action in ("idle", "walk") else 0.0
    root = hips + v3(-3.0, 0.0, -0.6)
    prev = root
    for k in range(1, 9):
        u = k / 8.0
        p = v3(root[0] - 8.2 * u + curl * 5.0 * u * u, wag * math.sin(u * 2.4) + curl * 6.0 * u * u, root[2] - 3.4 * u + (0.8 * u if rear > 20 else 0.0))
        p[2] = max(p[2], 0.9)
        P.add(L(prev, p, 1.7 - 0.9 * (k - 1) / 8.0, 1.7 - 0.9 * k / 8.0, "otter", "tail", caps=k == 1))
        prev = p
    roll = pick(ROLL, action, f)
    if roll:
        P.m = rot("a", roll)
        turned = P.m @ v3(0.0, 0.0, Z)
        P.shift = v3(-turned[0], -turned[1], Z - turned[2] - (Z - 3.3) * math.sin(math.radians(min(roll, 90.0))))
    sa, sc = pick(SQUASH, action, f, (1.0, 1.0))
    if sa != 1.0 or sc != 1.0:
        P.squash(sa, 1.0 / math.sqrt(sa * sc), sc, (lunge, 0.0, 0.0))
    return P
