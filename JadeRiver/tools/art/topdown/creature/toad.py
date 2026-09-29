"""The mossback toad: a fat, warty toad in olive khaki, a mat of bright moss and three curled fiddlehead ferns growing on
its back, parotoid ridges behind golden slit-pupilled eyes under heavy lids, a wide down-turned mouth and a cream belly
and throat. It breathes with a fluttering throat while its ferns sway, and goes in short heavy hops. Its tell: it rocks
back on its haunches, cheeks and throat bulging, the lids narrowing, the ferns standing up. It lashes a long pink tongue
out at its prey (a glint at its sticky tip on the hit) and reels it in with a gulp; struck, it squashes; beaten, it
flops onto its back, its ferns drooping.
"""
from __future__ import annotations

import math

import numpy as np

from . import mats as M
from .motion import h01v, pick, wave
from .sculpt import E, L, Pose, S, chain, rot, v3

Z = 4.4

HOP = {"walk": (0.0, 0.4, 1.8, 2.8, 2.4, 1.0, 0.0, 0.0), "death": (0.8, 1.6, 1.0, 0.2, 0.0, 0.0, 0.0, 0.0)}
AHEAD = {"walk": (-0.8, -0.8, -0.2, 0.4, 0.8, 1.0, 0.8, 0.0), "hurt": (-2.0, -1.2, -0.4), "windup": (-0.4, -0.8, -1.0, -1.1)}
SQ = {"walk": (0.86, 0.94, 1.06, 1.04, 1.0, 0.96, 0.84, 0.94), "idle": (1.0, 1.02, 1.04, 1.03, 1.01, 1.0),
      "hurt": (0.8, 1.04, 1.0), "windup": (0.98, 1.02, 1.05, 1.06), "attack": (1.02, 0.96, 0.98, 1.02, 1.0, 1.0)}
LEAN = {"walk": (0.0, 6.0, 12.0, 6.0, -4.0, -8.0, -2.0, 0.0), "windup": (-6.0, -12.0, -16.0, -18.0),
        "attack": (6.0, 8.0, 6.0, 2.0, 0.0, 0.0), "hurt": (-8.0, -3.0, 0.0)}
PUFF = {"idle": (0.0, 0.15, 0.3, 0.2, 0.1, 0.0), "windup": (0.4, 0.8, 1.1, 1.25), "attack": (0.2, 0.0, 0.0, 0.1, 0.5, 0.2),
        "hurt": (0.0, 0.1, 0.0)}
REACH = {"attack": (7.0, 15.0, 11.0, 5.0, 0.0, 0.0)}
ROLL = {"death": (10.0, 40.0, 100.0, 150.0, 176.0, 172.0, 176.0, 176.0)}


def toad(action: str, f: int) -> Pose:
    P = Pose()
    hop = pick(HOP, action, f)
    ahead = pick(AHEAD, action, f)
    sq = pick(SQ, action, f, 1.0)
    lean = pick(LEAN, action, f)
    puff = pick(PUFF, action, f)
    z = Z * sq + hop
    tm = rot("b", lean)
    C = v3(ahead - 1.0, 0.0, z)
    at = lambda p: C + tm @ v3(p)

    def hide(q, n):
        """The cream belly underneath; the moss over the back behind the head, its edge ragged; warts a step lit."""
        loc = (q - C) @ tm
        nl = n @ tm
        belly = nl[:, 2] < -0.4
        edge = 0.4 + 0.28 * h01v(np.floor(loc[:, 0] * 1.5 + 30), np.floor(loc[:, 1] * 1.5 + 30), 11)
        moss = (loc[:, 0] < 3.0) & (nl[:, 2] > edge) & ~belly
        wart = (h01v(np.floor(loc[:, 0] * 1.1 + 50), np.floor(loc[:, 1] * 1.1 + 50), 3) > 0.84) & ~moss & ~belly
        names = np.where(belly, "toad_belly", np.where(moss, "toad_moss", "toad")).astype(object)
        return names, np.where(wart, 1, 0).astype(np.int16)

    body_r = (6.8, 6.4, 3.9 * sq)
    P.add(E(C, body_r, "toad", "body", tm, hide),
          E(at((5.0, 0.0, 0.4)), (4.0, 5.5, 2.7 * sq), "toad", "body", tm, hide),
          E(at((7.9, 0.0, -0.3)), (2.0, 4.0 + puff * 0.6, 1.7), "toad", "body", tm, hide))
    for s in (1, -1):
        P.add(E(at((2.4, s * 3.8, 2.9 * sq)), (2.4, 1.4, 1.0), "toad", "gland%d" % s, tm, line=False))
    # Moss tufts breaking the back's line, and three fiddlehead ferns curling up out of it, swaying (up in the tell,
    # drooping in death).
    sway = 0.7 * wave(action, f) if action in ("idle", "walk") else (0.4 if action == "windup" else 0.0)
    stand = 1.0 + (0.25 * f / 3.0 if action == "windup" else 0.0) - (0.35 * min(1.0, f / 4.0) if action == "death" else 0.0)
    for p in ((-4.4, 0.8, 3.2), (0.6, 2.8, 3.2), (-1.6, -3.0, 3.2), (-5.4, -1.8, 2.3)):
        P.add(E(at((p[0], p[1], p[2] * sq)), (1.3, 1.2, 0.9), "toad_moss", "moss", tm, line=False))
    for k, (a0, b0) in enumerate(((-2.4, 1.8), (-0.2, -1.2), (-4.6, -0.4))):
        sv = sway * (1.0 if k % 2 else -1.0)
        h0 = 3.6 * sq
        pts = [(a0, b0, h0), (a0 - 0.4, b0 + sv * 0.3, h0 + 2.0 * stand), (a0 - 0.1, b0 + sv * 0.6, h0 + 3.8 * stand),
               (a0 + 1.0, b0 + sv * 0.8, h0 + 4.6 * stand), (a0 + 1.7, b0 + sv * 0.8, h0 + 3.8 * stand), (a0 + 1.0, b0 + sv * 0.7, h0 + 3.1 * stand)]
        P.add(chain([at(p) for p in pts], 0.7, 0.55, "toad_fern", "fern%d" % k, line=False))
    # Golden eyes on top of the head, a black slit in each, heavy lids (lower in the tell's glare).
    for s in (1, -1):
        eye = at((5.4, s * 2.9, 2.5 * sq))
        P.add(S(eye, 1.75, "toad_eye", "eye%d" % s))
        shut = action == "hurt" and f == 0 or action == "death" and f >= 3
        if not shut:
            P.mark(eye + tm @ v3(1.6, s * 0.4, 0.5), M.INKY)
            P.mark(eye + tm @ v3(1.3, s * 0.5, 1.0), M.INKY)
            P.mark(eye + tm @ v3(0.8, s * 0.3, 1.5), M.GLINT)
        lid = 1.0 if shut else (0.6 if action == "windup" and f >= 2 else 0.25)
        P.add(E(eye + tm @ v3(-0.2, 0.0, 0.5 + 0.7 * (1 - lid)), (1.9, 1.8, 0.9), "toad", "lid%d" % s, tm, line=False))
        for u in (38.0, 58.0, 78.0):
            a = math.radians(s * u)
            P.mark(at((7.9 + 2.2 * math.cos(math.radians(-16)) * math.cos(a), 4.2 * math.sin(a), -0.3 + 1.9 * math.sin(math.radians(-16)))), M.TOAD_MOUTH)
    # The throat sac (and in the tell the cheeks) bulge.
    P.add(E(at((6.3, 0.0, -2.4)), (1.8 + puff * 1.3, 3.0 + puff * 1.6, 1.2 + puff * 1.4), "toad_sac", "throat", tm))
    if puff > 0.3:
        for s in (1, -1):
            P.add(E(at((5.4, s * 4.4, -0.4)), (1.4 + puff, 1.0 + puff * 0.9, 1.1 + puff * 0.8), "toad_sac", "cheek%d" % s, tm))
    # Legs: the thick hind legs folded at its sides, trailing in a hop; short front legs propping the chest.
    air = hop > 1.2
    for s in (1, -1):
        if air:
            hip, knee, foot = v3(ahead - 4.2, s * 3.8, z - 1.0), v3(ahead - 7.4, s * 4.8, z - 1.8), v3(ahead - 10.2, s * 4.4, z - 2.4)
        else:
            hip, knee, foot = v3(ahead - 4.0, s * 4.6, z - 1.6), v3(ahead + 0.4, s * 6.8, 2.2), v3(ahead - 3.0, s * 7.0, 0.6)
        P.add(E(hip + v3(0.6, 0.0, 0.0), (3.2, 2.2, 2.3), "toad", "hind%d" % s, rot("c", s * 20.0), hide),
              L(hip, knee, 1.8, 1.4, "toad_leg", "hind%d" % s), L(knee, foot, 1.3, 1.0, "toad_leg", "hind%d" % s),
              E(foot + v3(-0.8 if air else 1.0, 0.0, 0.0), (2.1, 1.5, 0.55), "toad_leg", "hind%d" % s))
        hand = v3(ahead + 5.4 + (1.8 if air else 0.0), s * 4.8, 0.6 + (hop * 0.5 if air else 0.0))
        P.add(L(at((3.8, s * 3.6, -2.2)), hand, 1.25, 1.0, "toad_leg", "arm%d" % s), E(hand, (1.3, 1.1, 0.5), "toad_leg", "arm%d" % s))
    # The mouth opens on its dark maw in the tell's last frame; the tongue lashes out to its full reach on the hit.
    mouth = at((9.2, 0.0, -0.8))
    if action == "windup" and f >= 2 or action == "attack" and f < 4:
        P.add(E(mouth + v3(-0.3, 0.0, -0.2), (1.0, 2.6, 0.7), "maw", "maw", tm))
    reach = pick(REACH, action, f)
    if reach > 0:
        tip = v3(mouth[0] + reach, 0.0, max(2.4, mouth[2] - reach * 0.06))
        mid = (mouth + tip) * 0.5 + v3(0.0, 0.0, 0.6 if f in (0, 2) else 0.2)
        P.add(chain([mouth, mid, tip], 0.95, 0.8, "tongue", "tongue"), S(tip, 1.55, "tongue", "tongue"))
        if f == 1:
            for d in ((1.9, 0.0, 1.6), (2.5, 0.0, 2.2), (1.3, 0.0, 2.2), (1.9, 0.0, 2.8)):
                P.glow.append((tip + v3(*d), M.GLINT))
    roll = pick(ROLL, action, f)
    if roll:
        P.m = rot("a", roll)
        turned = P.m @ v3(0.0, 0.0, z)
        P.shift = v3(-turned[0], -turned[1], z - turned[2] - (z - 4.0) * (1.0 if roll > 90 else math.sin(math.radians(roll))) + (0.6 if roll > 150 else 0.0))
    return P
