"""The boarlet and the hollowed boarlet.

The wild boarlet: a young boar's warm brown hide with the pale stripes of its youth along its back and flanks, a high
shoulder, a bristle crest, a darker head with a long snout, a pink snout disc, small tusks, pointed ears and a curled
tail. It trots on diagonal pairs of legs. Its tell: it lowers its head and paws the ground, scraping the near forehoof
back twice in a spurt of dust, then crouches coiled. It charges, tosses its tusks up on the hit and skids to a stop;
struck, it jerks its head up and stumbles; beaten, its forelegs buckle and it rolls onto its side.

Hollowed (the Reed Marsh's grey boarlets): the same beast with its colour drunk out of it, ash grey with pale stripes,
cold white eyes in a pale halo, and grey strands rising and curling from its back; beaten, it falls and comes apart into
grey motes.
"""
from __future__ import annotations

import math

import numpy as np

from figure.geom import ik2

from . import mats as M
from .motion import gait, pick, wave
from .sculpt import E, L, Pose, S, chain, rot, v3

MATS = {"hide": "hide", "head": "hide_head", "stripe": "stripe", "hoof": "hoof", "snout": "snout", "bristle": "bristle"}
HOLLOW = {"hide": "h_hide", "head": "h_head", "stripe": "h_stripe", "hoof": "h_bristle", "snout": "h_snout",
          "bristle": "h_bristle"}
PALETTE = ["hide", "hide_head", "stripe", "hoof", "snout", "bristle", "tusk", "pink"]
H_PALETTE = ["h_hide", "h_head", "h_stripe", "h_snout", "h_bristle", "tusk", "strand", "pink"]

Z = 8.4   # the body's middle over the ground at rest

# Per-frame spacing (motion.py's catalogue).
LUNGE = {"windup": (-0.6, -1.2, -1.6, -2.0), "attack": (2.6, 4.2, 4.6, 4.0, 2.6, 1.0), "hurt": (-2.2, -1.6, -0.6),
         "death": (-1.2, -1.6, -1.6, -1.4, -1.2, -1.0, -1.0, -1.0)}
BOB = {"windup": (0.0, -0.3, -0.4, -0.8), "attack": (0.9, 0.2, 0.0, -0.2, 0.0, 0.0), "hurt": (0.3, -0.3, 0.0),
       "death": (0.4, -0.6, -1.6, -1.8, -1.9, -2.0, -2.0, -2.0)}
PITCH = {"windup": (-3.0, -5.0, -6.0, -8.0), "attack": (1.0, 4.0, 6.0, 2.0, 0.0, -1.0), "hurt": (5.0, -2.0, 0.0),
         "death": (6.0, -8.0, -12.0, -8.0, -4.0, 0.0, 0.0, 0.0)}
HEAD = {"idle": (-6.0, -10.0, -16.0, -18.0, -12.0, -7.0), "windup": (-14.0, -24.0, -28.0, -34.0),
        "attack": (-22.0, 12.0, 24.0, 10.0, -4.0, -10.0), "hurt": (16.0, -4.0, -8.0),
        "death": (20.0, 8.0, -10.0, -14.0, -16.0, -18.0, -18.0, -18.0)}
SQUASH = {"windup": ((1.0, 0.99), (0.99, 0.97), (0.98, 0.96), (0.97, 0.92)),
          "attack": ((1.14, 0.9), (0.93, 1.06), (0.97, 1.03), (1.03, 0.97), (1.0, 1.0), (1.0, 1.0)),
          "hurt": ((0.9, 1.05), (1.04, 0.97), (1.0, 1.0)),
          "death": ((1.0, 1.0),) * 5 + ((1.02, 0.95), (1.0, 1.0), (1.0, 1.0))}
ROLL = {"death": (0.0, 0.0, 8.0, 34.0, 64.0, 88.0, 84.0, 86.0)}
DISSOLVE = {"death": (0.0, 0.0, 0.0, 0.0, 0.12, 0.34, 0.62, 0.9)}


def boarlet(action: str, f: int, hollow: bool = False) -> Pose:
    m = HOLLOW if hollow else MATS
    P = Pose()
    lunge = pick(LUNGE, action, f)
    bob = pick(BOB, action, f)
    if action == "idle":
        bob = 0.15 * wave(action, f)
    elif action == "walk":
        bob = -0.25 + 0.4 * math.cos(f / 8.0 * 4.0 * math.pi)
    pitch = pick(PITCH, action, f)
    if action == "walk":
        pitch = 1.2 * math.sin(f / 8.0 * 4.0 * math.pi + 0.6)
    hpitch = pick(HEAD, action, f, -8.0)
    if action == "walk":
        hpitch = -10.0 + 4.0 * math.sin(f / 8.0 * 4.0 * math.pi + 1.4)
    sa, sc = pick(SQUASH, action, f, (1.0, 1.0))
    if action == "idle":
        sc = 1.0 + 0.025 * wave(action, f)
    z = Z + bob
    C = v3(lunge - 1.4, 0.0, z)                     # the body's middle
    bm = rot("b", pitch)

    def at(p):
        """A point of the body (from its middle), pitched with it."""
        return C + bm @ v3(p)

    def hide(q, n):
        """The pale stripes of its youth along the back and flanks, and short tufts of fur (a groove a step down)."""
        loc = (q - C) @ bm
        nz = (n @ bm)[:, 2]
        b = np.abs(loc[:, 1])
        a = loc[:, 0]
        on_back = (nz > 0.2) & (a > -7.0) & (a < 4.6)
        stripe = on_back & (((b > 1.0) & (b < 1.55)) | ((b > 2.6) & (b < 3.05)))
        u = a * 0.62 + 0.45 * np.sin(loc[:, 2] * 0.9 + b * 1.7)
        fr = u - np.floor(u)
        tuft = (fr < 0.16) & ~stripe & (nz > -0.6)
        names = np.where(stripe, m["stripe"], m["hide"]).astype(object)
        bias = np.where(tuft, -1, 0).astype(np.int16)
        return names, bias

    # The body: a high shoulder, the barrel and the rump, one smooth hide.
    P.add(E(at((3.2, 0.0, 1.0)), (4.4, 4.5, 5.2), m["hide"], "body", bm, hide),
          E(at((-0.2, 0.0, 0.0)), (5.9, 4.6, 4.3), m["hide"], "body", bm, hide),
          E(at((-4.4, 0.0, 0.3)), (3.6, 4.1, 4.0), m["hide"], "body", bm, hide))
    # The bristle crest from the nape down the spine, stirring.
    stir = {"idle": 0.3 * wave(action, f), "walk": 0.4 * wave(action, f, 0.25)}.get(action, 0.0)
    if action in ("windup", "attack"):
        stir = -0.5   # raised in anger
    for k in range(8):
        a0 = 5.0 - k * 1.3
        top = 5.4 - max(0, k - 2) * 0.28
        base = at((a0, 0.0, top - 0.5))
        lean = -0.8 + stir * (0.6 if k % 2 else -0.4)
        tip = base + bm @ v3(lean, 0.0, 1.5 + (0.6 if action in ("windup", "attack") else 0.0) - k * 0.08)
        P.add(L(base, tip, 0.62, 0.22, m["bristle"], "crest", line=False))
    # The head: skull and jowls, a long snout ending in its pink disc, tusks, ears.
    hm = bm @ rot("b", -8.0 + hpitch)
    sniff = 0.25 * wave(action, f, 0.3) if action == "idle" else 0.0
    hc = at((7.8 + sniff, 0.0, -0.9))
    hp = lambda p: hc + hm @ v3(p)
    P.add(E(hc, (4.0, 3.6, 3.5), m["head"], "head", hm),
          E(hp((0.4, 0.0, -1.5)), (3.2, 3.9, 2.4), m["head"], "head", hm),
          L(hp((2.0, 0.0, -0.6)), hp((6.0, 0.0, -1.4)), 2.3, 1.7, m["head"], "head"))
    P.add(E(hp((6.6, 0.0, -1.5)), (0.8, 1.8, 1.6), m["snout"], "snout", hm))
    for s in (1, -1):
        P.mark(hp((7.45, s * 0.6, -1.3)), M.RAMPS[m["snout"]][0])
        # Tusks: short, curving up from the lower jaw.
        P.add(L(hp((4.6, s * 1.7, -2.3)), hp((5.8, s * 2.3, -0.8)), 0.45, 0.28, "tusk", "tusk%d" % s))
        # Eyes: a dark bead under the brow with a glint (shut when struck or beaten); the hollowed's cold white.
        shut = action == "hurt" and f == 0 or action == "death" and f >= 5
        eye = hp((2.1, s * 2.85, 0.9))
        if hollow and not shut:
            P.mark(eye, M.HOLLOW_EYE)
            P.mark(hp((1.8, s * 2.9, 1.6)), M.EYE_HALO)
        elif shut:
            P.mark(eye, M.RAMPS[m["head"]][0])
        else:
            P.mark(eye, M.INKY)
            P.mark(hp((2.4, s * 2.75, 1.3)), M.GLINT)
        # Ears: pointed, pricked forward, flicking.
        flick = 18.0 if action == "idle" and f in (3, 4) and s > 0 else 0.0
        if action in ("windup", "attack"):
            flick = -20.0   # laid back
        em = hm @ rot("a", s * -22.0) @ rot("b", -10.0 + flick)
        P.add(E(hp((-1.2, s * 2.3, 3.0)), (1.1, 1.0, 2.2), m["head"], "ear%d" % s, em))
        P.mark(hp((-0.4, s * 2.2, 3.4)), M.RAMPS["pink"][1] if not hollow else M.RAMPS["h_snout"][1])
    # Legs: forelegs under the shoulder, hind legs under the rump bent back at the hock, dark hooves.
    legs = (("fl", 3.8, 2.5, 0.0), ("fr", 3.8, -2.5, 0.5), ("hl", -5.0, 2.7, 0.5), ("hr", -5.0, -2.7, 0.0))
    roll = pick(ROLL, action, f)
    for name, a0, b0, off in legs:
        front = name[0] == "f"
        lift, stride = gait(action, f, off, 2.0, 2.2)
        top = at((a0 + 1.4 if front else a0 + 0.8, b0 * 0.92, -2.4 if front else -1.8))
        foot = v3(lunge + a0 + stride, b0, 0.9 + lift)
        if action == "windup" and name == "fr":
            foot = foot + v3(*((0.4, 0.0, 1.2), (-2.6, 0.0, 0.3), (0.9, 0.0, 1.6), (0.2, 0.0, 0.0))[f])
        if action == "windup" and not front:
            foot = foot + v3(0.6 * f / 3.0, 0.0, 0.0)
        if action == "attack":
            foot = foot + v3(*{0: ((2.6, 0, 1.8), (-2.8, 0, 0.6)), 1: ((1.2, 0, 0.0), (-1.4, 0, 0.0)),
                               2: ((0.6, 0, 0.0), (-0.8, 0, 0.0)), 3: ((1.0, 0, 0.0), (0.2, 0, 0.0))}.get(f, ((0, 0, 0), (0, 0, 0)))[0 if front else 1])
        if action == "hurt" and f == 0:
            foot = foot + v3(-0.8 if front else 0.4, 0.0, 0.6 if front else 0.0)
        if action == "death":
            fold = (0.0, 0.8, 1.0, 1.0, 0.8, 0.5, 0.4, 0.4)[f] if front else (0.0, 0.0, 0.3, 0.5, 0.5, 0.4, 0.3, 0.3)[f]
            foot = foot + v3(-2.6 * fold if front else 1.2 * fold, 0.0, 1.6 * fold)
        l1, l2 = (3.0, 2.9) if front else (3.1, 3.0)
        knee, end = ik2(top, foot, l1, l2, v3(1.0 if front else -1.0, 0.0, 0.0))
        P.add(L(top, knee, 1.7 if front else 2.0, 1.2, m["hide"], "leg_" + name),
              L(knee, end, 1.15, 0.95, m["hide"], "leg_" + name))
        P.add(E(end + v3(0.3, 0.0, -0.25), (1.15, 1.0, 0.8), m["hoof"], "leg_" + name))
    # The tail: a short curl with a tuft, flicking.
    wag = {"idle": (0.0, 0.8, 0.3, -0.5, 0.0, 0.4), "walk": tuple(0.8 * wave("walk", i) for i in range(8))}.get(action, (0.3,) * 8)
    w = wag[min(f, len(wag) - 1)]
    P.add(chain([at((-7.9, 0.0, 1.4)), at((-8.8, 0.2 + w * 0.5, 2.3)), at((-8.6, 0.6 + w, 3.2)), at((-7.9, 0.5 + w, 3.4))],
                0.62, 0.4, m["hide"], "tail"))
    P.add(S(at((-7.7, 0.4 + w, 3.3)), 0.62, m["bristle"], "tail"))
    if hollow and action != "death":
        # The grey strands: three thin wisps rising from the spine and curling back, stirring as it breathes.
        st = {"idle": 0.5 * wave(action, f), "walk": 0.7 * wave(action, f, 0.3)}.get(action, 0.9)
        for k, (a0, b0) in enumerate(((-4.0, 0.5), (-1.2, -0.4), (1.6, 0.3))):
            base = at((a0, b0, 4.3))
            rise = 1.0 if action not in ("attack",) else 0.6
            pts = [base, base + v3(-0.4, st * 0.4 * (1 if k % 2 else -1), 2.4 * rise),
                   base + v3(-1.6, -st * 0.5 * (1 if k % 2 else -1), 4.6 * rise),
                   base + v3(-1.3 - k * 0.3, st * 0.6, 6.4 * rise - k * 0.5), base + v3(-0.2, st * 0.7, 7.2 * rise - k * 0.7)]
            P.add(chain(pts, 0.5, 0.25, "strand", "strand%d" % k, line=False))
    # Dust: the pawing hoof's scrape, the charge's skid.
    if action == "windup" and f in (1, 2):
        for k in range(4):
            P.fx.append((v3(lunge + 3.8 - 2.6 - k * 1.1, -2.8 - k * 0.5, 0.4 + (k % 2) * 0.8 + f * 0.3), M.DUST if k % 2 else M.DUST_DIM))
    if action == "attack" and f in (1, 2, 3):
        for k in range(6):
            ang = math.radians(k * 60.0 + f * 20.0)
            r = 2.0 + f * 1.1
            P.fx.append((v3(lunge + 3.0 + math.cos(ang) * r * 0.5, math.sin(ang) * r, 0.4 + (k % 3) * 0.5), M.DUST if k % 2 else M.DUST_DIM))
    if action == "death":
        mid, half = Z, 4.6
        if roll:
            P.m = rot("a", roll)
            turned = P.m @ v3(0.0, 0.0, mid)
            P.shift = v3(-turned[0], -turned[1], mid - turned[2] - (mid - half) * math.sin(math.radians(roll)))
        if hollow:
            P.dissolve = pick(DISSOLVE, action, f)
            P.dissolve_col = M.MOTE
    if sa != 1.0 or sc != 1.0:
        P.squash(sa, 1.0 / math.sqrt(sa * sc), sc, (lunge, 0.0, 0.0))
    return P


def hollowed(action: str, f: int) -> Pose:
    return boarlet(action, f, True)
