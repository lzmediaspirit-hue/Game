"""The reed rat: a grey-brown coat with a paler belly, pink ears, nose and feet, red eyes, whiskers and a long green reed
tail in segments. It sniffs and looks about while idle and scurries in bounds, its tail swinging. Its tell: it rears up
on its haunches, forepaws up, mouth open on its yellow teeth, tail lashing high. It lunges to bite and shakes its head;
struck, it is knocked back squashed; beaten, it rears and topples onto its side, its tail flopping.
"""
from __future__ import annotations

import math

import numpy as np

from . import mats as M
from .motion import gait, pick, wave
from .sculpt import E, L, Pose, S, rot, v3

Z = 4.6

LUNGE = {"windup": (-0.4, -1.0, -1.4, -1.6), "attack": (2.6, 4.8, 5.0, 4.2, 2.4, 0.8), "hurt": (-2.4, -1.4, -0.4),
         "death": (-0.8, -1.2, -1.2, -1.2, -1.2, -1.2, -1.2, -1.2)}
PITCH = {"windup": (8.0, 18.0, 30.0, 36.0), "attack": (-10.0, -6.0, -2.0, 0.0, 0.0, 0.0), "hurt": (14.0, 4.0, 0.0),
         "death": (22.0, 10.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)}
HEAD = {"idle": (0.0, 4.0, -6.0, -4.0, 6.0, 2.0), "windup": (6.0, 10.0, 12.0, 14.0), "attack": (-12.0, -22.0, -18.0, -14.0, -6.0, 0.0),
        "hurt": (18.0, 6.0, 0.0), "death": (24.0, 10.0, 0.0, -6.0, -8.0, -8.0, -8.0, -8.0)}
YAW = {"idle": (0.0, 0.0, 14.0, 14.0, -10.0, 0.0), "attack": (0.0, 0.0, 14.0, -14.0, 6.0, 0.0)}
GAPE = {"windup": (0.2, 0.5, 0.8, 1.0), "attack": (1.0, 0.1, 0.0, 0.0, 0.2, 0.0), "hurt": (0.6, 0.2, 0.0),
        "death": (0.9, 0.6, 0.4, 0.3, 0.3, 0.3, 0.3, 0.3)}
SQUASH = {"attack": ((1.15, 0.9), (0.92, 1.06), (1.0, 1.0), (1.0, 1.0), (1.0, 1.0), (1.0, 1.0)), "hurt": ((0.88, 1.06), (1.04, 0.97), (1.0, 1.0)),
          "windup": ((1.0, 0.94), (1.0, 1.0), (1.0, 1.0), (1.0, 1.02))}
ROLL = {"death": (0.0, 0.0, 30.0, 62.0, 86.0, 92.0, 88.0, 90.0)}
TAIL = {"windup": (1.0, 1.6, 2.2, 2.6), "attack": (0.4, -0.2, 0.0, 0.2, 0.4, 0.4), "death": (1.0, 0.6, 0.4, 0.2, 0.0, -0.1, 0.0, 0.0)}


def rat(action: str, f: int) -> Pose:
    P = Pose()
    lunge = pick(LUNGE, action, f)
    pitch = pick(PITCH, action, f)
    bob = 0.0
    if action == "walk":
        pitch = 6.0 * math.sin(f / 8.0 * math.tau)          # a bounding scurry: the back arches and stretches
        bob = 0.6 * max(0.0, math.sin(f / 8.0 * math.tau + 0.8))
    if action == "idle":
        bob = 0.15 * wave(action, f)
    z = Z + bob
    hips = v3(lunge - 3.6, 0.0, z - 0.2)
    bm = rot("b", pitch)
    at = lambda p: hips + bm @ (v3(p) - v3(-3.6, 0.0, -0.2))

    def coat(q, n):
        loc = (q - hips) @ bm
        nz = (n @ bm)[:, 2]
        belly = nz < -0.2
        streak = ((loc[:, 0] * 0.8 + np.abs(loc[:, 1]) * 0.6) % 1.0 < 0.15) & (nz > -0.1)
        return np.where(belly, "fur_light", "fur").astype(object), np.where(streak & ~belly, -1, 0).astype(np.int16)

    P.add(E(at((-3.8, 0.0, -0.1)), (3.8, 3.9, 3.6), "fur", "body", bm, coat),
          E(at((-0.6, 0.0, 0.2)), (5.2, 3.3, 3.2), "fur", "body", bm, coat),
          E(at((2.6, 0.0, 0.4)), (2.8, 2.8, 2.8), "fur", "body", bm, coat))
    # The head: skull, a tapering snout to a pink nose, pink ears, red eyes, whiskers; the jaw drops in a gape.
    sniff = 0.35 * wave(action, f, 0.1) if action == "idle" else 0.0
    hm = bm @ rot("c", pick(YAW, action, f)) @ rot("b", -10.0 + pick(HEAD, action, f))
    hc = at((5.4 + sniff, 0.0, 1.2))
    hp = lambda p: hc + hm @ v3(p)
    gape = pick(GAPE, action, f)
    P.add(E(hc, (3.0, 2.6, 2.4), "fur", "head", hm, coat),
          L(hp((1.2, 0.0, -0.3)), hp((4.2, 0.0, -0.7)), 1.9, 0.9, "fur", "head"))
    P.add(S(hp((4.6, 0.0, -0.6)), 0.75, "pink", "nose"))
    if gape > 0.05:
        jm = hm @ rot("b", -gape * 32.0)
        P.add(L(hp((0.8, 0.0, -1.4)), hp((0.8, 0.0, -1.4)) + jm @ v3(2.8, 0.0, -0.2), 1.1, 0.6, "fur_light", "jaw"))
        for s in (0.35, -0.35):
            P.mark(hp((4.0, s, -1.3)), c_teeth())
    for s in (1, -1):
        ear_m = hm @ rot("a", s * -18.0) @ rot("c", s * 20.0)
        P.add(E(hp((-0.8, s * 1.7, 2.3)), (0.8, 1.5, 1.8), "pink", "ear%d" % s, ear_m))
        P.mark(hp((-0.5, s * 1.8, 2.5)), M.RAMPS["pink"][0])
        shut = action == "hurt" and f == 0 or action == "death" and f >= 5
        P.mark(hp((1.6, s * 1.75, 0.9)), M.RAMPS["fur"][0] if shut else M.RAT_EYE)
        if not shut:
            P.mark(hp((1.8, s * 1.65, 1.2)), M.GLINT)
        for w in range(3):
            P.mark(hp((3.4 + w * 0.3, s * (1.7 + w * 0.55), -0.4 - w * 0.35)), M.RAMPS["fur_light"][4])
    # Legs: short forelegs with pink paws, haunches with long pink hind feet; the scurry lands the forepaws together,
    # then the hind; in the tell the forepaws lift off the ground.
    reared = action == "windup" or action == "death" and f < 2
    for k, (a0, b0, front) in enumerate(((3.2, 1.6, True), (3.2, -1.6, True), (-4.4, 2.2, False), (-4.4, -2.2, False))):
        lift, stride = gait(action, f, 0.0 if front else 0.45, 1.6, 2.2)
        if front and reared:
            top = at((a0, b0, -1.4))
            paw = top + bm @ v3(1.4, 0.0, -1.2)
        else:
            top = at((a0, b0, -1.6 if front else -1.0))
            paw = v3(lunge + a0 + stride + (0.6 if front else 1.4), b0, 0.6 + lift)
        P.add(L(top, paw, 1.05 if front else 1.4, 0.75, "fur", "leg%d" % k),
              E(paw + v3(0.5 if front else 0.9, 0.0, -0.1), (1.0 if front else 1.6, 0.8, 0.5), "pink", "leg%d" % k))
    # The reed tail: green segments curving back along the ground, the tip lifting and swaying; lashed high in the tell.
    sway = 2.0 * wave(action, f) if action in ("idle", "walk") else 0.6
    up = pick(TAIL, action, f)
    root = at((-7.2, 0.0, -0.2))
    pts = []
    for k in range(14):
        u = k / 13.0
        pts.append(v3(root[0] - 10.0 * u + up * 2.4 * u * u, (2.2 + sway) * math.sin(u * 2.6), root[2] - 2.4 * u + (3.0 + up * 3.4) * u * u))
    for k in range(13):
        r0 = 1.05 - 0.45 * k / 13.0
        P.add(L(pts[k], pts[k + 1], r0, r0 - 0.035, "tail_a" if k % 2 == 0 else "tail_b", "tail", caps=k == 0))
    roll = pick(ROLL, action, f)
    if roll:
        P.m = rot("a", roll)
        turned = P.m @ v3(0.0, 0.0, Z)
        P.shift = v3(-turned[0], -turned[1], Z - turned[2] - (Z - 3.3) * math.sin(math.radians(min(roll, 90.0))))
    sa, sc = pick(SQUASH, action, f, (1.0, 1.0))
    if sa != 1.0 or sc != 1.0:
        P.squash(sa, 1.0 / math.sqrt(sa * sc), sc, (lunge, 0.0, 0.0))
    return P


def c_teeth():
    return (0xF2, 0xE2, 0x9A, 255)
