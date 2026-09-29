"""The mud crab: a wide brown shell with pale patches and a raised brow, six jointed legs, black eyes on stalks, and two
claws with jade tips held up at its sides. Like its side-view sheet it keeps its broad side to the camera and scuttles
sideways (`aim` is where it faces, in its own frame). It snaps its claws and swivels its eyes while idle, scuttles on
alternating sets of three legs; its tell: it rears back on its legs and raises both claws high and wide open, eyes up;
it lunges and slams the claws shut before it, dragging them back through the dust; struck, it is knocked back with its
claws flung up and its eyes pulled down; beaten, it flips onto its back, its legs curling up.
"""
from __future__ import annotations

import math

import numpy as np

from . import mats as M
from .motion import gait, pick, wave
from .sculpt import E, L, Pose, S, rot, v3

Z = 5.6   # the shell's middle over the ground

LUNGE = {"windup": (-0.6, -1.2, -1.6, -1.8), "attack": (2.4, 4.0, 3.8, 2.6, 1.2, 0.4), "hurt": (-2.4, -1.4, -0.4),
         "death": (-0.6, -0.8, -0.8, -0.8, -0.8, -0.8, -0.8, -0.8)}
BOB = {"windup": (0.4, 0.8, 1.0, 0.9), "attack": (0.6, -0.8, -0.9, -0.5, -0.1, 0.0), "hurt": (-0.6, 0.3, 0.0)}
PITCH = {"windup": (6.0, 10.0, 13.0, 14.0), "attack": (-4.0, -12.0, -10.0, -5.0, -2.0, 0.0), "hurt": (10.0, -3.0, 0.0)}
# Each chela: where it is (ahead, out to the side, up), how far it turns in (yaw) and up (pitch), and how open.
REST = (5.2, 7.8, 3.6, 34.0, 26.0, 0.3)
CLAW = {"windup": ((5.2, 7.0, 4.4, 40.0, 30.0, 0.4), (4.2, 8.2, 6.4, 25.0, 55.0, 0.7), (3.6, 8.8, 8.2, 14.0, 70.0, 1.0),
                   (3.4, 9.0, 8.8, 10.0, 76.0, 1.0)),
        "attack": ((6.2, 7.0, 6.4, 30.0, 25.0, 1.0), (9.4, 4.4, 1.2, 48.0, -26.0, 0.0), (9.6, 4.4, 0.9, 48.0, -30.0, 0.0),
                   (8.0, 5.6, 1.6, 50.0, -14.0, 0.15), (6.6, 6.8, 2.6, 40.0, 8.0, 0.3), (5.6, 7.6, 3.4, 35.0, 22.0, 0.3)),
        "hurt": ((4.4, 9.0, 6.4, 24.0, 55.0, 0.9), (5.0, 8.4, 4.4, 30.0, 36.0, 0.5), (5.2, 7.9, 3.8, 34.0, 28.0, 0.35)),
        "death": ((5.6, 6.8, 4.0, 40.0, 30.0, 0.8), (5.4, 8.0, 2.4, 30.0, 0.0, 0.8), (5.2, 8.6, 1.2, 25.0, -10.0, 0.9),
                  (5.2, 8.8, 0.6, 22.0, -14.0, 0.9), (5.2, 8.8, 0.6, 22.0, -14.0, 0.9), (5.2, 8.8, 0.6, 22.0, -14.0, 0.9),
                  (5.2, 8.8, 0.6, 22.0, -14.0, 0.9), (5.2, 8.8, 0.6, 22.0, -14.0, 0.9))}
ROLL = {"death": (6.0, 30.0, 90.0, 150.0, 176.0, 172.0, 178.0, 176.0)}
CURL = {"death": (0.0, 0.1, 0.3, 0.6, 0.8, 1.0, 0.85, 1.0), "hurt": (0.3, 0.1, 0.0)}
STALK = {"windup": (0.4, 0.8, 1.0, 1.0), "attack": (0.6, 0.2, 0.2, 0.4, 0.6, 0.8), "hurt": (-1.0, -0.6, -0.2),
         "death": (0.0, -0.6, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0)}


def crab(action: str, f: int, aim=(1.0, 0.0)) -> Pose:
    P = Pose()
    da, db = aim
    lunge = pick(LUNGE, action, f)
    bob = pick(BOB, action, f)
    if action == "idle":
        bob = 0.25 * wave(action, f)
    elif action == "walk":
        bob = 0.45 * abs(math.sin(f / 8.0 * 2.0 * math.pi))
    pitch = pick(PITCH, action, f)
    sway = 0.0
    if action == "walk":
        sway = 4.0 * math.sin(f / 8.0 * 2.0 * math.pi)       # it rocks side to side as it scuttles
    z = Z + bob
    C = v3(da * lunge, db * lunge, z)
    bm = rot("b", pitch) @ rot("a", sway * (1 if abs(db) > 0.3 else 0.4))
    at = lambda p: C + bm @ v3(p)
    shell_c, shell_r = at((0.0, 0.0, 0.0)), (5.2, 7.4, 3.4)

    def shell(q, n):
        """Pale patches over the top (lit blotches), the grooves of the carapace, the brow's rim a step darker."""
        loc = (q - C) @ bm
        nz = (n @ bm)[:, 2]
        a, b = loc[:, 0], loc[:, 1]
        blotch = np.zeros(len(a), dtype=bool)
        for pa, pb, r in ((1.2, 2.8, 1.5), (-1.6, -2.6, 1.7), (1.8, -4.2, 1.1), (-2.0, 3.8, 1.3), (-0.2, 0.2, 1.2)):
            blotch |= (a - pa) ** 2 + (b - pb) ** 2 < r * r
        blotch &= nz > 0.35
        groove = (np.abs(np.abs(b) - 2.2 - 0.25 * a) < 0.3) & (nz > 0.2) | (np.abs(a - 1.9 + 0.05 * b * b) < 0.28) & (nz > 0.3)
        belly = nz < -0.35                         # the pale underside (it shows when it lies on its back)
        names = np.where(blotch | belly, "shell_pale", "shell").astype(object)
        bias = np.where(groove & ~blotch & ~belly | belly & (np.abs(b) % 2.2 < 0.35), -1, 0).astype(np.int16)
        return names, bias

    def rim(q, n):
        nz = (n @ bm)[:, 2]
        return np.where(nz < -0.4, "shell_pale", "shell_rim").astype(object), np.zeros(len(nz), dtype=np.int16)

    P.add(E(shell_c, shell_r, "shell", "body", bm, shell),
          E(at((-0.3, 0.0, -1.3)), (5.6, 7.9, 2.3), "shell_rim", "body", bm, rim),
          E(at((3.6, 0.0, 0.2)), (1.6, 5.0, 1.6), "shell", "body", bm, shell))       # the brow over the eyes
    # Mouth parts under the brow.
    for s in (1, -1):
        P.mark(at((5.4, s * 0.7, -0.8)), M.RAMPS["shell_rim"][0])
    P.mark(at((5.5, 0.0, -1.2)), M.RAMPS["crab_leg"][1])
    # Eye stalks: up from the brow, black eyes with a glint; up in the tell, down when struck or beaten.
    st = pick(STALK, action, f)
    look = 0.5 * wave(action, f, 0.2) if action == "idle" else 0.0
    for s in (1, -1):
        base = at((3.8, s * 1.8, 1.2))
        tip = at((4.4 + look * s, s * (2.3 + 0.3 * st), 4.6 + 1.6 * st))
        P.add(L(base, tip, 0.62, 0.55, "crab_leg", "stalk%d" % s))
        eye = tip + v3(0.2, 0.0, 0.8)
        P.add(S(eye, 1.2, "eye", "stalk%d" % s))
        if action != "death" or f < 2:
            P.mark(eye + v3(0.9, -0.4 * s, 0.9), M.GLINT)
    # Legs: three a side, knees up and out, pointed feet on the ground; a scuttle lifts them in two sets of three and
    # strides them along the way it goes; beaten, they curl up.
    curl = pick(CURL, action, f)
    for s in (1, -1):
        for k, a0 in enumerate((-3.2, -0.8, 1.6)):
            lift, stride = gait(action, f, (0.5 if (k + (s > 0)) % 2 else 0.0), 1.8, 1.5)
            hip = at((a0, s * 6.4, -1.0))
            knee = v3(da * lunge + a0 + da * stride * 0.5 - 0.3, s * (9.8 - curl * 3.0) + db * stride * 0.5,
                      z + 1.8 + lift * 0.5 - curl * 1.0)
            foot = v3(da * lunge + a0 + da * stride - 0.9 + 0.3 * k, s * (11.6 - curl * 4.6) + db * stride,
                      0.5 + lift + curl * 3.6)
            if action == "windup":
                foot = foot + v3(-da * lunge, -db * lunge, 0.0)   # the feet stay planted as it rears back
            P.add(L(hip, knee, 1.05, 0.95, "crab_leg", "leg%d%d" % (s, k)), L(knee, foot, 0.9, 0.45, "crab_leg", "leg%d%d" % (s, k)))
    # Claws: arms from the shell's front corners to the chelae, held before it with the pincers turned in (a boxer's
    # guard); raised high and wide open in the tell; slammed shut before it on the strike, the struck side furthest.
    for s in (1, -1):
        pa, pb, pc, yaw_in, pitch_c, open_ = pick(CLAW, action, f, REST)
        if action == "idle":
            open_ = 0.2 + 0.55 * max(0.0, math.sin((f / 6.0 + (0.0 if s > 0 else 0.5)) * math.tau))
            pc += 0.3 * wave(action, f, 0.25 if s > 0 else 0.75)
        if action == "walk":
            pc += 0.5 * wave(action, f, 0.0 if s > 0 else 0.5)
            pb += 0.4 * wave(action, f, 0.25)
        if action == "attack" and f in (0, 1, 2, 3):
            w = s * db + 0.4 * da                  # the claw on the struck side reaches furthest
            pa += 1.2 * w
            pb -= 0.8 * max(0.0, w) * s * 0
        palm = at((pa, s * pb, pc))
        elbow = at((pa * 0.55 + 1.6, s * (pb + 2.8), pc * 0.5 + 0.4))
        cm = bm @ rot("c", s * yaw_in) @ rot("b", pitch_c)
        P.add(L(at((2.6, s * 5.8, -0.4)), elbow, 1.35, 1.25, "claw", "arm%d" % s),
              L(elbow, palm, 1.25, 1.4, "claw", "arm%d" % s))
        P.add(E(palm, (2.8, 1.6, 2.3), "claw", "claw%d" % s, cm),
              E(palm + cm @ v3(2.9, 0.0, -0.7), (1.9, 1.0, 1.0), "claw", "claw%d" % s, cm),
              E(palm + cm @ v3(4.6, 0.0, -0.6), (1.2, 0.8, 0.75), "claw_tip", "claw%d" % s, cm))
        dm = cm @ rot("b", 12.0 + open_ * 42.0)
        hinge = palm + cm @ v3(1.3, 0.0, 1.1)
        P.add(E(hinge + dm @ v3(2.0, 0.0, 0.2), (1.9, 0.95, 0.85), "claw", "dactyl%d" % s, dm),
              E(hinge + dm @ v3(3.6, 0.0, 0.1), (1.1, 0.75, 0.7), "claw_tip", "dactyl%d" % s, dm))
        P.mark(palm + cm @ v3(1.0, 0.0, 2.3), M.RAMPS["claw"][4])
        if action == "attack" and f in (1, 2):
            tipp = palm + cm @ v3(4.6, 0.0, -0.8)
            for k in range(5):
                ang = math.radians(k * 72.0 + f * 30.0)
                P.fx.append((v3(tipp[0] + math.cos(ang) * (1.6 + f), tipp[1] + math.sin(ang) * (1.6 + f), 0.3 + (k % 2) * 0.6),
                             M.DUST if k % 2 else M.DUST_DIM))
    roll = pick(ROLL, action, f)
    if roll:
        P.m = rot("a", roll)
        turned = P.m @ v3(0.0, 0.0, Z)
        r = math.sin(math.radians(roll))
        h = Z + (7.0 - Z) * r if roll <= 90.0 else 3.6 + (7.0 - 3.6) * r   # over its edge onto its back
        P.shift = v3(-turned[0], -turned[1], h - turned[2])
    if action == "attack" and f == 1:
        P.squash(1.06, 1.04, 0.9, (0.0, 0.0, 0.0))
    if action == "windup" and f == 3:
        P.squash(0.97, 0.98, 1.04, (0.0, 0.0, 0.0))
    return P
