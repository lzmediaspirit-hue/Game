"""The bird plan (M1), from the jade crane chick (`chick`): a body of down on two long legs, a neck to a round head and
a beak, two wings that fold, spread and beat, a tail tuft. Made for the crane chick first; the cranes, hawks and
vultures after it lay their own parts over it (a longer neck and beak, wings of a span, legs, a crest).

  body   the down's ball (radii) at its height over the ground, its pitch; `puff` swells it (the tell), `fringe` tufts
         round its lower edge in the jade of its wings
  neck   from the body's front to the head (its base, length, radii), reaching and bobbing by the channels
  head   a round head, a beak (length, radii) that opens, the eyes (shut, glaring, squeezed), a red crown, head tufts
  wings  stubby wings at the shoulders (`span`: the folded wing's length), folded along the body, spread wide in the
         tell, swept forward and down in a buffet (the blow); three blunt feather fingers at their ends
  legs   long legs bending back at the heel (two bones by IK), three toes flat on the ground; a high-stepping strut
  tail   a tuft at the back

The motion styles (STYLES): idle `peer`, walk `strut`, windup `spread_puff`, attack `buffet`, hurt `ruffle`, death
`fold_sit`. Channels: `lunge`, `rise` (the body's lift), `hop` (off the ground), `pitch`, `head` (its pitch), `yaw`,
`reach` (the neck), `puff`, `spread` (the wings, 0 folded to 1 spread wide), `sweep` (the wings swept forward, degrees),
`beak`, `sit`, `tuck`, `wind` (wind lines from the buffet).
"""
from __future__ import annotations

import math

import numpy as np

from figure.geom import ik2

from .. import mats as M
from ..motion import gait, headon, wave
from ..sculpt import E, L, Pose, S, rot, v3

STYLES = {
    "peer": {"head": (0.0, 4.0, 8.0, 4.0, -2.0, 0.0), "yaw": (0.0, 10.0, 18.0, 8.0, -12.0, -4.0), "reach": (0.0, 0.2, 0.3, 0.2, 0.0, 0.0),
             "bob_amp": 0.25, "blink": (3,)},
    "strut": {"kind": "strut", "lift": 2.6, "stride": 1.8, "bob": 0.5, "reach_amp": 0.8},
    "spread_puff": {"lunge": (-0.3, -0.6, -0.9, -1.0), "rise": (0.2, 0.5, 0.7, 0.8), "pitch": (4.0, 8.0, 10.0, 10.0),
                    "head": (8.0, 12.0, 16.0, 16.0), "reach": (-0.4, -0.8, -1.0, -1.0), "puff": (0.3, 0.6, 0.9, 1.0),
                    "spread": (0.3, 0.7, 1.0, 1.0), "beak": (0.2, 0.4, 0.6, 0.7), "glare": True},
    "buffet": {"lunge": (1.2, 3.4, 3.6, 2.6, 1.2, 0.4), "hop": (1.2, 2.2, 1.0, 0.3, 0.0, 0.0), "pitch": (2.0, -8.0, -10.0, -4.0, 0.0, 0.0),
               "head": (4.0, -6.0, -10.0, -2.0, 2.0, 0.0), "reach": (0.0, 0.6, 0.8, 0.4, 0.1, 0.0), "puff": (0.8, 0.6, 0.4, 0.2, 0.1, 0.0),
               "spread": (1.0, 1.0, 0.8, 0.5, 0.2, 0.0), "sweep": (-20.0, 55.0, 70.0, 30.0, 10.0, 0.0), "beak": (0.4, 0.8, 0.6, 0.2, 0.0, 0.0),
               "glare": True, "wind": (1, 2, 3), "squash": {1: (1.04, 1.0, 0.96)}},
    "ruffle": {"lunge": (-2.0, -1.2, -0.3), "rise": (0.4, 0.2, 0.0), "pitch": (10.0, 4.0, 0.0), "head": (18.0, 8.0, 0.0),
               "reach": (-0.8, -0.4, 0.0), "puff": (0.9, 0.5, 0.1), "spread": (0.6, 0.3, 0.0), "beak": (0.5, 0.2, 0.0), "squint": True},
    "fold_sit": {"lunge": (-1.0, -1.4, -1.4, -1.4, -1.4, -1.4, -1.4, -1.4), "pitch": (10.0, 4.0, 0.0, -2.0, -2.0, -2.0, -2.0, -2.0),
                 "head": (18.0, -6.0, -20.0, -36.0, -48.0, -54.0, -56.0, -56.0), "reach": (-0.6, -1.0, -1.6, -2.2, -2.6, -2.8, -2.8, -2.8),
                 "puff": (0.9, 0.5, 0.4, 0.3, 0.3, 0.3, 0.3, 0.3), "spread": (0.6, 0.3, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0),
                 "sit": (0.0, 0.3, 0.6, 0.85, 1.0, 1.0, 1.0, 1.0), "tuck": (0.0, 0.0, 0.2, 0.5, 0.8, 1.0, 1.0, 1.0), "shut_from": 2},
}

CHICK = {
    "Z": 8.6,                                      # the body's middle over the ground
    "body": {"r": (3.4, 3.0, 3.2), "fringe": 10},
    "neck": {"base": (2.0, 0.0, 1.6), "up": (0.6, 0.0, 3.0), "r": (1.15, 0.9)},
    "head": {"r": (1.9, 1.8, 1.8), "beak": (2.4, 0.6, 0.15), "eye": (0.8, 1.15, 0.45), "crown": (-0.2, 0.0, 1.7, 0.75),
             "tufts": ((-0.9, 0.3, 1.6), (-1.3, -0.3, 1.3), (-1.6, 0.1, 0.9))},
    "wings": {"at": (0.6, 2.8, 1.0), "r": (2.4, 0.65, 1.6), "fingers": 3, "span": 1.0},
    "legs": {"hip": (-0.3, 1.3, -2.2), "bones": (3.7, 4.0), "r": (0.5, 0.38), "toe": 1.3},
    "tail": {"at": (-3.4, 0.0, 0.9), "r": (1.4, 1.5, 1.0)},
}
VARIANTS = {
    "chick": {"parts": CHICK, "mats": {"down": "chick_down", "jade": "chick_jade", "leg": "chick_leg", "beak": "chick_beak",
                                       "crown": "chick_crown"},
              "motion": {"idle": "peer", "walk": "strut", "windup": "spread_puff", "attack": "buffet", "hurt": "ruffle",
                         "death": "fold_sit"}},
}


def pose(B, action: str, f: int, view: float = 48.0) -> Pose:
    P = Pose()
    p, m = B.parts, B.mats
    st = B.style(action)
    fr, bk = headon(view)
    lunge = B.pick("lunge", action, f)
    rise = B.pick("rise", action, f)
    hop = B.pick("hop", action, f)
    pitch = B.pick("pitch", action, f)
    hpitch = B.pick("head", action, f)
    yaw = B.pick("yaw", action, f) * (1.0 - 0.6 * fr)
    reach = B.pick("reach", action, f)
    puff = B.pick("puff", action, f)
    spread = B.pick("spread", action, f)
    sweep = B.pick("sweep", action, f)
    beak = B.pick("beak", action, f)
    sit = B.pick("sit", action, f)
    tuck = B.pick("tuck", action, f)
    bob = 0.0
    if action == "idle":
        bob = st.get("bob_amp", 0.0) * wave(action, f)
    strut = st.get("kind") == "strut"
    if strut:
        bob = st.bob * abs(math.sin(f / 8.0 * 2.0 * math.pi))
        reach = st.reach_amp * math.sin(f / 8.0 * 2.0 * math.pi + 1.2)
    g = p.legs
    leg_len = g.bones[0] + g.bones[1]
    z = p.Z + bob + rise + hop - sit * (p.Z - p.body.r[2] * 0.9)
    C = v3(lunge, 0.0, z)
    bm = rot("b", pitch)
    at = lambda q: C + bm @ v3(q)
    k = 1.0 + 0.16 * puff
    br = tuple(r * k for r in p.body.r)

    def down(q, n):
        """White down, a step dark in fluffy tufts; the fringe round its lower edge tipped in jade."""
        loc = (q - C) @ bm
        nl = n @ bm
        tuft = ((loc[:, 0] * 1.1 + np.abs(loc[:, 1]) * 0.9 + loc[:, 2] * 0.4) % 1.4 < 0.22)
        jade = (nl[:, 2] < -0.2) & (((loc[:, 0] * 0.9 + loc[:, 1] * 0.7) % 1.6) < 0.7)
        return np.where(jade, m.jade, m.down).astype(object), np.where(tuft & ~jade, -1, 0).astype(np.int16)

    P.add(E(C, br, m.down, "body", bm, down))
    # The fringe: tufts round its lower edge.
    for i in range(p.body.fringe):
        ang = math.radians(i * 360.0 / p.body.fringe + 10.0)
        q = at((br[0] * 0.92 * math.cos(ang), br[1] * 0.92 * math.sin(ang), -br[2] * 0.45))
        P.add(S(q, 0.75 + 0.15 * (i % 2), m.jade if i % 3 == 0 else m.down, "fringe", line=False))
    # The tail tuft.
    P.add(E(at(p.tail.at) + v3(0.0, 0.0, 0.3 * wave(action, f) if action in ("idle", "walk") else 0.0), p.tail.r, m.jade, "tail", bm))
    # Legs: from the hips under the body down to the ground, the heel bent back; a strut lifts each foot high.
    for s in (1, -1):
        hip = at((g.hip[0], s * g.hip[1] * (1.0 + 0.3 * (fr + bk)), g.hip[2]))
        lift, stride = gait(action, f, 0.0 if s > 0 else 0.5, st.get("lift", 1.6), st.get("stride", 1.6))
        foot = v3(lunge + g.hip[0] + 0.6 + stride, s * g.hip[1] * (1.15 + 0.4 * (fr + bk)), 0.4 + lift + hop)
        if sit > 0.0:
            foot = foot + (hip + v3(1.4, 0.0, -0.6) - foot) * sit
        heel, end = ik2(hip, foot, g.bones[0], g.bones[1], v3(-1.0, 0.0, 0.0))
        P.add(L(hip, heel, g.r[0], g.r[1] * 1.2, m.leg, "leg%d" % s), S(heel, g.r[0] * 1.1, m.leg, "leg%d" % s),
              L(heel, end, g.r[1] * 1.2, g.r[1], m.leg, "leg%d" % s))
        for t in (-30.0, 0.0, 30.0):           # three toes flat on the ground (hanging when lifted)
            d = v3(math.cos(math.radians(t)), math.sin(math.radians(t)), -0.6 if lift > 0.4 else 0.0)
            P.add(L(end, end + d * g.toe, 0.32, 0.22, m.leg, "toe%d" % s, line=False))
    # Wings: folded along its sides, spread wide in the tell, swept forward in the buffet, feather fingers at their ends.
    w = p.wings
    for s in (1, -1):
        root = at((w.at[0], s * w.at[1] * k * 0.9, w.at[2]))
        # Its direction: round from straight back (folded) toward its side (spread) and on forward (swept), raised as
        # it spreads and lowered as it sweeps; its flat turned up as it opens.
        az = 165.0 - 90.0 * spread - sweep
        el = -12.0 + 40.0 * spread - 0.5 * max(0.0, sweep)
        wm = bm @ rot("c", s * az) @ rot("b", el) @ rot("a", -s * 60.0 * spread)
        mid = root + wm @ v3(w.r[0] * w.span, 0.0, 0.0)
        P.add(E(root + wm @ v3(w.r[0] * w.span * 0.55, 0.0, 0.0), (w.r[0] * w.span * 0.75, w.r[1], w.r[2]), m.jade, "wing%d" % s, wm))
        for j in range(w.fingers):
            off = (j - (w.fingers - 1) / 2.0) * 0.75
            tip = mid + wm @ v3(0.9 + 0.3 * (j == 1), 0.0, off)
            P.add(L(mid + wm @ v3(-0.4, 0.0, off * 0.8), tip, 0.55, 0.4, m.jade, "wing%d" % s, line=False))
    # The neck and the head: reaching and bobbing; pitched up in the tell; tucked down into its wing as it dies.
    n = p.neck
    base = at(n.base)
    top = base + bm @ v3(n.up[0] + reach * 0.8, 0.0, n.up[2] - tuck * 2.0) + v3(0.0, 0.0, 0.0)
    hm = bm @ rot("c", yaw) @ rot("b", hpitch + 6.0 * fr)
    hc = top + hm @ v3(0.4, 0.0, 0.6)
    P.add(L(base, top, n.r[0] * k, n.r[1], m.down, "neck"))
    hd = p.head
    P.add(E(hc, hd.r, m.down, "head", hm))
    bl, b0, b1 = hd.beak
    bq = hc + hm @ v3(hd.r[0] * 0.8, 0.0, -0.2)
    P.add(L(bq, bq + hm @ v3(bl, 0.0, -0.25), b0, b1, m.beak, "beak"))
    if beak > 0.15:
        bm2 = hm @ rot("b", -beak * 22.0)
        P.add(L(bq + hm @ v3(0.1, 0.0, -0.3), bq + bm2 @ v3(bl * 0.85, 0.0, -0.55), b0 * 0.75, b1, m.beak, "jaw"))
    ca, cb, cc, cr = hd.crown
    P.add(S(hc + hm @ v3(ca, cb, cc), cr, m.crown, "crown"))
    for t in hd.tufts:
        P.add(L(hc + hm @ v3(t[0] * 0.5, t[1] * 0.5, t[2] * 0.8), hc + hm @ v3(*t) + hm @ v3(-0.6, 0.0, 0.5), 0.35, 0.15, m.down, "tuft", line=False))
    shut = action == "death" and f >= st.get("shut_from", 99) or f in st.get("blink", ())
    ea, eb, ec = hd.eye
    for s in (1, -1):
        eye = hc + hm @ v3(ea, s * eb, ec)
        if shut or st.get("squint"):
            P.mark(eye, M.RAMPS[m.down][1])
        else:
            P.eye(eye, M.CHICK_EYE)
            P.mark(eye + hm @ v3(0.15, 0.0, 0.4), M.GLINT if not st.get("glare") else M.RAMPS[m.down][0])
    # The buffet's wind: short lines thrown ahead of its wings.
    if action == "attack" and f in st.get("wind", ()):
        for j in range(4):
            y = (j - 1.5) * 2.6
            for d in range(3):
                P.fx.append((v3(lunge + 5.0 + f * 1.4 + d * 1.1, y, z + (j % 2) * 1.2 - 1.0), M.WIND if d < 2 else M.DUST_DIM))
    sq = st.get("squash", {}).get(f)
    if sq is not None:
        P.squash(sq[0], sq[1], sq[2], (lunge, 0.0, 0.0))
    return P
