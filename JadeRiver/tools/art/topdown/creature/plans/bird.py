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

M2's flyers (`wings.seg`): `vulture`, `crane`, `hawk` and `roc`, jointed wings of a span with their flight feathers
painted, drawn in the air over their feet. Styles: idle `soar`, walk `flap`, hurt `tumble_back`, death `fold_fall`; the
tells `rise_fold` (the vulture), `rise_coil` (the crane), `mantle` (the hawk), `gather_wind` (the roc); the blows
`dive_rake`, `swoop_peck`, `lightning_dive`, `wing_gust`.
"""
from __future__ import annotations

import math

import numpy as np

from figure.geom import ik2

from .. import mats as M
from ..motion import gait, headon, wave
from ..sculpt import E, L, Pose, S, rot, v3
from .kit import colour

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
    if "seg" in B.parts.wings:
        return _flyer(B, action, f, view)
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


# ================================================================================================= the flyers (M2)
# The birds that fly (the mist vulture, the cloudwing crane, the stormwing hawk, the cloudpeak roc): a body held level in
# the air over the floor (the room view's shadow under it), two wings of a span beating, a neck and head of the bird's
# kind, a fan of a tail, the legs tucked (or trailing, the crane's). Each wing is three feather panels from the shoulder
# out (the arm, the forearm, the hand: coverts over the leading half, flight feathers behind, a feather line between each,
# the tips in the bird's own colour) and the fingered primaries at its end.
#
# Channels: `rise` (over its height), `lunge`, `pitch` (+ nose up), `roll`, `head` (its pitch), `el` (the wings'
# elevation, degrees; else the beat's), `sweep` (the wings swept back, degrees), `fold` (0..1: folded along the body),
# `beak`, `reach` (the neck), `coil` (the crane's neck drawn back in an S), `talons` (0..1: thrust down and ahead), `drop`
# (0..1: fallen to the floor). A beat style (`kind` "beat") swings the wings by `amp` about `base`, the hand lagging.
FLYER_STYLES = {
    "soar": {"kind": "beat", "amp": 24.0, "base": 12.0, "bob": 0.6, "pitch": 0.0},
    "flap": {"kind": "beat", "amp": 34.0, "base": 6.0, "bob": 0.9, "pitch": -5.0},
    "rise_fold": {"rise": (1.5, 3.4, 4.4, 4.7), "pitch": (6.0, -8.0, -24.0, -30.0), "el": (58.0, 34.0, 10.0, 4.0), "fold": (0.0, 0.3, 0.6, 0.7),
                  "head": (4.0, -6.0, -12.0, -14.0), "talons": (0.2, 0.4, 0.8, 1.0), "glare": True},
    "rise_coil": {"rise": (1.0, 2.0, 2.8, 3.0), "pitch": (6.0, 10.0, 12.0, 12.0), "el": (52.0, 66.0, 74.0, 76.0), "coil": (0.3, 0.6, 0.9, 1.0),
                  "beak": (0.0, 0.0, 0.3, 0.4), "glare": True},
    "mantle": {"rise": (0.6, 1.2, 1.5, 1.6), "pitch": (4.0, 8.0, 10.0, 10.0), "el": (18.0, 2.0, -10.0, -16.0), "sweep": (-10.0, -24.0, -32.0, -36.0),
               "sparks": (1, 2, 3), "glare": True, "beak": (0.2, 0.4, 0.6, 0.6), "head": (4.0, 8.0, 10.0, 10.0)},
    "gather_wind": {"rise": (0.8, 1.6, 2.2, 2.4), "pitch": (6.0, 10.0, 14.0, 14.0), "el": (40.0, 56.0, 66.0, 70.0), "sweep": (10.0, 22.0, 32.0, 36.0),
                    "swirl": (0, 1, 2, 3), "glare": True, "beak": (0.3, 0.5, 0.7, 0.8), "head": (6.0, 10.0, 14.0, 14.0)},
    "dive_rake": {"lunge": (3.0, 6.0, 6.4, 5.0, 2.6, 0.8), "rise": (-2.0, -6.5, -6.0, -3.5, -1.5, 0.0), "pitch": (-30.0, -8.0, 4.0, 6.0, 3.0, 0.0),
                  "el": (8.0, 48.0, 56.0, 40.0, 24.0, 12.0), "fold": (0.55, 0.0, 0.0, 0.0, 0.0, 0.0), "talons": (0.6, 1.0, 1.0, 0.6, 0.3, 0.0),
                  "head": (-10.0, 6.0, 6.0, 2.0, 0.0, 0.0), "streaks": (0, 1), "rake": (1, 2), "squash": {1: (1.04, 1.0, 0.96)}},
    "swoop_peck": {"lunge": (3.0, 6.2, 6.4, 5.0, 2.6, 0.8), "rise": (-1.5, -5.5, -5.0, -3.0, -1.2, 0.0), "pitch": (-14.0, -22.0, -10.0, 0.0, 2.0, 0.0),
                   "el": (34.0, -12.0, 0.0, 20.0, 28.0, 18.0), "reach": (1.6, 2.8, 2.2, 1.2, 0.5, 0.0), "beak": (0.6, 0.1, 0.0, 0.0, 0.0, 0.0),
                   "head": (-10.0, -20.0, -12.0, -4.0, 0.0, 0.0), "streaks": (0, 1), "squash": {1: (1.04, 1.0, 0.96)}},
    "lightning_dive": {"lunge": (3.0, 6.2, 6.6, 5.0, 2.6, 0.8), "rise": (-2.0, -6.5, -6.0, -3.5, -1.5, 0.0), "pitch": (-30.0, -8.0, 4.0, 6.0, 3.0, 0.0),
                       "el": (-6.0, 46.0, 56.0, 40.0, 24.0, 12.0), "sweep": (40.0, 0.0, 0.0, 0.0, 0.0, 0.0), "fold": (0.5, 0.0, 0.0, 0.0, 0.0, 0.0),
                       "talons": (0.6, 1.0, 1.0, 0.6, 0.3, 0.0), "head": (-10.0, 6.0, 6.0, 2.0, 0.0, 0.0), "streaks": (0, 1), "bolt": (0, 1, 2),
                       "sparks": (1, 2), "squash": {1: (1.04, 1.0, 0.96)}},
    "wing_gust": {"lunge": (-0.5, 1.4, 1.8, 1.2, 0.6, 0.2), "rise": (2.0, 0.4, 0.0, 0.4, 0.8, 1.2), "el": (70.0, -22.0, -28.0, -12.0, 6.0, 12.0),
                  "sweep": (34.0, -36.0, -40.0, -22.0, -6.0, 0.0), "pitch": (10.0, -6.0, -8.0, -4.0, 0.0, 0.0), "gust": (1, 2, 3),
                  "beak": (0.8, 0.6, 0.3, 0.1, 0.0, 0.0), "squash": {1: (1.03, 1.0, 0.97)}},
    "tumble_back": {"lunge": (-2.6, -1.5, -0.5), "rise": (1.0, 0.6, 0.2), "pitch": (24.0, 10.0, 2.0), "roll": (18.0, 8.0, 0.0),
                    "el": (72.0, 46.0, 24.0), "head": (20.0, 8.0, 0.0), "beak": (0.6, 0.3, 0.0), "squint": True},
    "fold_fall": {"drop": (0.0, 0.12, 0.3, 0.55, 0.8, 1.0, 1.0, 1.0), "roll": (8.0, 16.0, 22.0, 18.0, 12.0, 10.0, 10.0, 10.0),
                  "pitch": (22.0, 10.0, 0.0, -8.0, -12.0, -12.0, -12.0, -12.0), "el": (64.0, 36.0, 12.0, -4.0, -10.0, -12.0, -12.0, -12.0),
                  "fold": (0.0, 0.15, 0.3, 0.35, 0.35, 0.35, 0.35, 0.35), "head": (20.0, 0.0, -24.0, -40.0, -48.0, -50.0, -50.0, -50.0),
                  "beak": (0.6, 0.4, 0.2, 0.1, 0.1, 0.1, 0.1, 0.1), "dead_from": 3},
}
STYLES.update(FLYER_STYLES)

FLYER = {
    "Z": 11.0,                                     # the body's middle over the floor
    "body": {"r": (3.0, 2.2, 1.9), "breast": -0.35},
    "neck": {"kind": "ruff", "base": (2.3, 0.0, 0.5), "head": (4.2, 0.0, 1.5), "r": (1.15, 0.8), "ruff": (1.7, 1.9, 1.4)},
    "head": {"r": (1.35, 1.1, 1.15), "eye": (0.55, 0.85, 0.35), "beak": (1.0, 1.7, 0.55, 0.6), "hook": 0.9},
    "wings": {"at": (0.9, 1.6, 0.7), "seg": (3.0, 3.6, 4.0), "chord": (4.2, 3.8, 2.8), "fingers": 5, "finger": 2.4, "covert": 0.5,
              "tip": 0.0, "feathers": 4},
    "tail": {"at": (-3.0, 0.0, 0.1), "length": 3.0, "spread": 2.0, "bands": 0, "tip": 0.0},
    "legs": {"kind": "tucked", "at": (-0.6, 0.9, -1.4), "r": (0.45, 0.35), "talon": 1.0},
    "fx": None, "iris": "VULTURE_EYE",
}


def _bird(base, **over):
    from .kit import merge
    return merge(base, over)


VULTURE = _bird(FLYER, fx="mist", wings={"chord": (4.8, 4.5, 3.3), "finger": 2.8})
CRANE = _bird(FLYER, Z=12.0, body={"r": (3.2, 2.0, 1.9), "breast": -2.0},
              neck={"kind": "long", "base": (2.6, 0.0, 0.5), "head": (8.2, 0.0, 1.0), "r": (0.8, 0.6), "ruff": None},
              head={"r": (1.15, 0.85, 0.9), "eye": (0.55, 0.65, 0.3), "beak": (1.0, 3.6, 0.45, 0.2), "hook": 0.0, "crown": (0.0, 0.0, 0.9, 0.6),
                    "mask": True},
              wings={"seg": (3.4, 3.8, 4.4), "chord": (3.8, 3.4, 2.6), "tip": 0.45, "fingers": 5, "finger": 2.0},
              tail={"length": 2.4, "spread": 1.5},
              legs={"kind": "trailing", "at": (-1.6, 0.6, -1.0), "r": (0.3, 0.22), "length": 7.0},
              fx="cloud", iris="CRANE_EYE")
HAWK = _bird(FLYER, Z=10.0, body={"r": (2.6, 1.8, 1.6), "breast": -0.2, "bars": True},
             neck={"kind": "short", "base": (2.0, 0.0, 0.5), "head": (3.3, 0.0, 1.2), "r": (1.15, 1.0), "ruff": None},
             head={"r": (1.35, 1.15, 1.15), "eye": (0.6, 0.85, 0.35), "beak": (1.0, 1.2, 0.5, 0.55), "hook": 0.8, "cere": True, "brow": True},
             wings={"seg": (2.5, 3.0, 3.6), "chord": (3.7, 3.4, 2.6), "fingers": 4, "finger": 1.9, "bolt": True},
             tail={"length": 3.0, "spread": 1.6, "bands": 3},
             fx="storm", iris="HAWK_EYE")
ROC = _bird(FLYER, Z=13.0, body={"r": (3.6, 2.6, 2.3), "breast": -0.3},
            neck={"kind": "short", "base": (2.8, 0.0, 0.7), "head": (4.6, 0.0, 1.9), "r": (1.6, 1.3), "ruff": None},
            head={"r": (1.75, 1.45, 1.5), "eye": (0.75, 1.1, 0.45), "beak": (1.3, 2.2, 0.75, 0.75), "hook": 1.0, "brow": True,
                  "crest": ((-0.8, 0.0, 1.2), 3, 2.6)},
            wings={"seg": (3.4, 4.0, 4.6), "chord": (4.8, 4.2, 3.0), "fingers": 6, "finger": 2.8, "tip": 0.35},
            tail={"length": 5.0, "spread": 2.6, "bands": 2, "tip": 0.25},
            legs={"kind": "tucked", "at": (-0.6, 1.1, -1.8), "r": (0.6, 0.45), "talon": 1.3},
            fx="wind", iris="ROC_EYE")
_FLY = {"idle": "soar", "walk": "flap", "hurt": "tumble_back", "death": "fold_fall"}
VARIANTS.update({
    "vulture": {"parts": VULTURE, "mats": {"body": "mv_body", "covert": "mv_feather", "flight": "mv_flight", "tip": "mv_mist",
                                           "ruff": "mv_feather", "skin": "mv_skin", "beak": "mv_beak", "leg": "mv_leg", "breast": "mv_feather"},
                "motion": dict(_FLY, windup="rise_fold", attack="dive_rake")},
    "crane": {"parts": CRANE, "mats": {"body": "crane_plume", "covert": "crane_plume", "flight": "crane_flight", "tip": "cloud_tip",
                                       "skin": "crane_plume", "beak": "crane_beak", "leg": "crane_slate", "breast": "crane_plume",
                                       "mask": "crane_slate", "crown": "crane_crown"},
              "motion": dict(_FLY, windup="rise_coil", attack="swoop_peck")},
    "hawk": {"parts": HAWK, "mats": {"body": "hawk_body", "covert": "hawk_covert", "flight": "hawk_flight", "tip": "hawk_flight",
                                     "skin": "hawk_body", "beak": "hawk_beak", "leg": "hawk_cere", "breast": "hawk_breast", "cere": "hawk_cere",
                                     "bolt": "hawk_bolt"},
             "motion": dict(_FLY, windup="mantle", attack="lightning_dive")},
    "roc": {"parts": ROC, "mats": {"body": "roc_plume", "covert": "roc_plume", "flight": "roc_flight", "tip": "roc_gold", "skin": "roc_plume",
                                   "beak": "roc_beak", "leg": "roc_talon", "breast": "roc_plume", "crest": "roc_gold"},
            "motion": dict(_FLY, windup="gather_wind", attack="wing_gust")},
})


def _wing_paint(m, centre, span, chord, hs: float, hc: float, outer: bool, w):
    """A wing panel's feathers: coverts over its leading part in rows, the flight feathers behind (a line between each), on
    the outer panel the tips in the bird's own colour (`tip`: the share of the panel's span from its end)."""
    def paint(q, n):
        rel = q - centre
        u = (rel @ span) / max(0.1, hs)            # -1 at the panel's root .. 1 at its end
        v = (rel @ chord) / max(0.1, hc)           # -1 at the leading edge .. 1 at the trailing edge
        covert = v < (w.covert * 2.0 - 1.0)
        line = ((u + 1.0) * w.feathers * 0.5 % 1.0) < 0.2
        row = ((v + 1.0) * 1.6 % 1.0) < 0.2
        tip = outer & (u > 1.0 - 2.0 * w.tip) if w.tip > 0.0 else np.zeros(len(q), dtype=bool)
        names = np.where(tip & ~covert, m.tip, np.where(covert, m.covert, m.flight)).astype(object)
        bias = np.where(covert, np.where(row, -1, 0), np.where(line, -1, 0)).astype(np.int16)
        return names, bias
    return paint


def _flyer(B, action: str, f: int, view: float) -> Pose:
    """M2: a bird in flight (see FLYER_STYLES). The body is held level over the floor at `Z`, bobbing on the beat; the
    wings spread from its shoulders, three panels and the primaries, beating (the hand lagging the arm), raised, swept or
    folded by the action; the neck and head of its kind; the tail fanned behind; the legs tucked under it, thrust down
    to rake in a dive, or trailing behind (the crane's)."""
    P = Pose()
    p, m = B.parts, B.mats
    st = B.style(action)
    fr, bk = headon(view)
    seed = int(B.opts.get("seed", 0))
    lunge = B.pick("lunge", action, f)
    rise = B.pick("rise", action, f)
    pitch = B.pick("pitch", action, f, st.get("pitch", 0.0))
    roll = B.pick("roll", action, f)
    hpitch = B.pick("head", action, f)
    fold = B.pick("fold", action, f)
    sweep = B.pick("sweep", action, f)
    beak = B.pick("beak", action, f)
    reach = B.pick("reach", action, f)
    coil = B.pick("coil", action, f)
    talons = B.pick("talons", action, f)
    drop = B.pick("drop", action, f)
    bob = 0.0
    if st.get("kind") == "beat":
        n = 6 if action == "idle" else 8
        ph = f / n * math.tau
        el = st.base + st.amp * math.sin(ph)
        lag = st.amp * 0.45 * math.sin(ph - 1.3)
        bob = -st.bob * math.sin(ph)
    else:
        el = B.pick("el", action, f, 10.0)
        lag = 0.0
    z = (p.Z + rise + bob) * (1.0 - drop) + drop * (p.body.r[2] * 0.9)
    C = v3(lunge, 0.0, z)
    bm = rot("a", roll) @ rot("b", pitch)
    at = lambda q: C + bm @ v3(q)
    bd = p.body

    def plumage(q, n):
        """Its body: the bird's colour over the back, the breast underneath (barred, the hawk's)."""
        loc = (q - C) @ bm
        nl = n @ bm
        breast = nl[:, 2] < bd.breast
        bars = breast & (((loc[:, 0] * 1.4) % 1.0) < 0.25) if bd.get("bars") else np.zeros(len(q), dtype=bool)
        return np.where(breast, m.breast, m.body).astype(object), np.where(bars, -1, 0).astype(np.int16)

    P.add(E(C, bd.r, m.body, "body", bm, plumage))
    # The tail: a fan behind it (spread wider as it strikes), its feathers lined, banded (the hawk's, the roc's), its tip in
    # the bird's colour.
    t = p.tail
    spread = t.spread * (1.0 + 0.3 * (action in ("windup", "attack")))
    tc = at((t.at[0] - t.length * 0.55, 0.0, t.at[2]))
    tmm = bm @ rot("b", 6.0 + 4.0 * math.sin(f * 0.9))

    def tailp(q, n):
        loc = (q - tc) @ tmm
        u = -loc[:, 0] / t.length + 0.5            # 0 at its root .. 1 at its tip
        line = ((np.arctan2(loc[:, 1], -loc[:, 0] + t.length) * 6.0) % 1.0) < 0.22
        band = ((u * 2.0 * t.bands) % 1.0 < 0.3) & (u > 0.3) if t.bands else np.zeros(len(q), dtype=bool)
        tip = u > 1.0 - t.tip if t.tip else np.zeros(len(q), dtype=bool)
        names = np.where(tip, m.tip, m.flight).astype(object)
        return names, np.where(band & ~tip, -2, np.where(line, -1, 0)).astype(np.int16)

    P.add(E(tc, (t.length * 0.6, spread, 0.35), m.flight, "tail", tmm, tailp))
    # The wings.
    w = p.wings
    for s in (1, -1):
        root = at((w.at[0], s * w.at[1], w.at[2]))
        segs = [L_ * (1.0 - 0.55 * fold) for L_ in w.seg]
        prev = root
        for i, (ln, ch) in enumerate(zip(segs, w.chord)):
            e_ = el + (lag if i == 2 else lag * 0.4 if i == 1 else 0.0)
            e_ = e_ * (1.0 - fold) - 8.0 * fold
            sw = sweep + (8.0 + 18.0 * i) * (1.0 if i else 0.4) + 70.0 * fold * (i + 1) / 3.0
            sp = bm @ v3(-math.sin(math.radians(sw)), s * math.cos(math.radians(sw)) * math.cos(math.radians(e_)),
                         math.cos(math.radians(sw)) * math.sin(math.radians(e_)))
            sp = sp / float(np.linalg.norm(sp))
            cd = bm @ v3(-1.0, 0.0, 0.0)
            cd = cd - sp * float(cd @ sp)
            cd = cd / max(1e-6, float(np.linalg.norm(cd)))
            nm = np.cross(sp, cd)
            end = prev + sp * ln
            centre = (prev + end) * 0.5 + cd * (ch * 0.3)
            hs, hc = ln * 0.62, ch * 0.55 * (1.0 - 0.3 * fold)
            mm = np.stack([sp, cd, nm], axis=1)
            P.add(E(centre, (hs, hc, 0.42), m.covert, "wing%d" % s, mm, _wing_paint(m, centre, sp, cd, hs, hc, i == 2, w)))
            prev = end
        # The primaries: fingers fanning back from the hand's end.
        for j in range(w.fingers):
            ang = math.radians(-8.0 + 16.0 * j) * (1.0 - 0.6 * fold)
            d = sp * math.cos(ang) + cd * math.sin(ang)
            base = prev - sp * 0.6 + cd * (j * 0.35)
            P.add(L(base, base + d * w.finger * (1.0 - 0.15 * abs(j - w.fingers / 2.0) / w.fingers), 0.42, 0.22,
                    m.tip if w.tip else m.flight, "wing%d" % s, line=False))
        if w.get("bolt") and fold < 0.5:
            # The hawk's lightning streak: a zig-zag of storm gold across the wing's coverts.
            for k in range(6):
                q = root + sp * (1.4 + k * 1.3) * (1.0 - 0.55 * fold) + cd * (0.6 if k % 2 else 1.5) + nm * 0.5
                P.mark(q, M.RAMPS[m.bolt][3 if k % 2 else 2])
        if p.fx == "mist" and action != "death":
            # The vulture's frayed trailing edge: mist puffs coming off it.
            for k in range(4):
                u = (k * 0.31 + f * 0.17) % 1.0
                q = root + sp * (2.0 + 7.0 * u) * (1.0 - 0.5 * fold) + cd * (3.2 + u * 1.6)
                P.fx.append((q, M.MIST_PUFF if k % 2 else M.MIST_PUFF_DIM))
    # The legs: tucked under the tail (talons thrust down and ahead in a dive, raking), or trailing behind (the crane's).
    g = p.legs
    for s in (1, -1):
        hip = at((g.at[0], s * g.at[1], g.at[2]))
        if g.kind == "trailing":
            foot = hip + bm @ v3(-g.length, s * 0.3, -0.6)
            knee = (hip + foot) * 0.5 + bm @ v3(0.0, 0.0, -0.4)
            P.add(L(hip, knee, g.r[0], g.r[1], m.leg, "leg%d" % s, line=False), L(knee, foot, g.r[1], g.r[1], m.leg, "leg%d" % s, line=False))
            for tt in (-25.0, 0.0, 25.0):
                d = bm @ v3(-math.cos(math.radians(tt)), math.sin(math.radians(tt)), 0.0)
                P.add(L(foot, foot + d * 0.9, 0.2, 0.14, m.leg, "toe%d" % s, line=False))
            continue
        foot = hip + bm @ v3(-1.2 + 3.4 * talons, s * 0.2, -0.6 - 2.4 * talons)
        P.add(L(hip, foot, g.r[0], g.r[1], m.leg, "leg%d" % s))
        for tt in (-30.0, 0.0, 30.0):
            d = bm @ v3(math.cos(math.radians(tt)) * (1.0 if talons > 0.3 else -0.6), math.sin(math.radians(tt)) * 0.7, -0.5)
            P.add(L(foot, foot + d * g.talon, 0.28, 0.12, m.leg, "talon%d" % s, line=False))
            P.mark(foot + d * g.talon, M.TALON_DARK)
    # The neck and head.
    nk, hd = p.neck, p.head
    yaw = 6.0 * math.sin(f * 0.8) * (1.0 - fr) if action == "idle" else 0.0
    base = at(nk.base)
    if nk.kind == "long":
        # The crane's: stretched out ahead in flight, drawn back into an S in its tell, thrust out in the peck.
        tip = v3(nk.head) + v3(reach * 1.0 - coil * 4.2, 0.0, coil * 2.6)
        mid1 = v3(nk.base) + (tip - v3(nk.base)) * 0.35 + v3(0.0, 0.0, 1.2 * coil + 0.2)
        mid2 = v3(nk.base) + (tip - v3(nk.base)) * 0.7 + v3(coil * 1.6, 0.0, -0.8 * coil)
        pts = [base, at(mid1), at(mid2), at(tip)]
        for i in range(3):
            P.add(L(pts[i], pts[i + 1], nk.r[0] - (nk.r[0] - nk.r[1]) * i / 3.0, nk.r[0] - (nk.r[0] - nk.r[1]) * (i + 1) / 3.0, m.body, "neck"))
        hc = pts[-1]
    else:
        hc = at(v3(nk.head) + v3(reach, 0.0, 0.0))
        P.add(L(base, hc, nk.r[0], nk.r[1], m.skin if nk.kind == "ruff" else m.body, "neck"))
        if nk.get("ruff"):
            P.add(E(base + bm @ v3(-0.2, 0.0, 0.2), nk.ruff, m.ruff, "ruff", bm))
    hm = bm @ rot("c", yaw) @ rot("b", hpitch - 6.0 * coil + 10.0 * fr)

    def face(q, n):
        loc = (q - hc) @ hm
        mask = (loc[:, 0] > 0.15) & (np.abs(loc[:, 2]) < 0.55) if hd.get("mask") else np.zeros(len(q), dtype=bool)
        return np.where(mask, m.get("mask", m.skin), m.skin).astype(object), np.zeros(len(q), dtype=np.int16)

    P.add(E(hc, hd.r, m.skin, "head", hm, face))
    hp = lambda q: hc + hm @ v3(q)
    b0, bl, br0, br1 = hd.beak
    bq = hp((hd.r[0] * 0.75, 0.0, 0.0))
    tipq = bq + hm @ v3(bl, 0.0, -0.25 - 0.1 * bl)
    P.add(L(bq, tipq, br0, br1, m.beak, "beak"))
    if hd.hook:
        P.add(L(tipq, tipq + hm @ v3(0.15, 0.0, -hd.hook * 0.7), br1, 0.15, m.beak, "beak"))
    if beak > 0.15:
        jm = hm @ rot("b", -beak * 24.0)
        P.add(L(bq + hm @ v3(0.0, 0.0, -0.35), bq + jm @ v3(bl * 0.8, 0.0, -0.45), br0 * 0.7, br1 * 0.8, m.beak, "jaw"))
    if hd.get("cere"):
        P.add(S(bq + hm @ v3(0.1, 0.0, 0.2), br0 * 0.9, m.cere, "cere", line=False))
    if hd.get("crown"):
        ca, cb, cc, cr = hd.crown
        P.add(S(hp((ca, cb, cc)), cr, m.crown, "crown", line=False))
    if hd.get("crest"):
        (qa, qb, qc), cn, clen = hd.crest
        for j in range(cn):
            sd = (j - (cn - 1) / 2.0) * 0.45
            r0 = hp((qa, sd, qc))
            r1 = r0 + hm @ v3(-clen * 0.7, sd * 1.2, clen * 0.45 + 0.3 * math.sin(f * 1.1 + j))
            r2 = r1 + hm @ v3(-clen * 0.5, sd * 0.6, -0.1)
            P.add(L(r0, r1, 0.45, 0.3, m.crest, "crest", line=False), L(r1, r2, 0.3, 0.12, m.crest, "crest", line=False))
    dead = action == "death" and f >= st.get("dead_from", 99)
    ea, eb, ec = hd.eye
    for s in (1, -1):
        eye = hp((ea, s * eb, ec))
        if hd.get("brow"):
            P.add(E(hp((ea - 0.1, s * (eb - 0.15), ec + 0.4)), (0.7, 0.4, 0.3), m.skin, "brow", hm, line=False))
        if dead or st.get("squint"):
            P.mark(eye, M.RAMPS[m.skin][0])
        else:
            P.eye(eye, colour(p.iris))
            if st.get("glare"):
                P.mark(eye + hm @ v3(0.0, 0.0, 0.4), M.INKY)
    # Its kind's air: the hawk's sparks and its bolt, the roc's gathering wind and its gust, the crane's cloud wisps, the
    # dive's streaks.
    if f in st.get("sparks", ()) and p.fx == "storm":
        for k in range(8):
            ang = math.radians(k * 45.0 + f * 33.0)
            rr = 4.0 + (k % 3) * 1.4
            P.glow.append((C + v3(math.cos(ang) * rr * 0.8, math.sin(ang) * rr, 1.0 + (k % 4) * 0.8), M.SPARK if k % 2 else M.SPARK_DIM))
    if f in st.get("bolt", ()) and p.fx == "storm":
        q = C + v3(2.0, 0.0, -1.0)
        for k in range(7):
            q = q + v3(1.0, 0.7 if k % 2 else -0.7, -1.2)
            P.glow.append((q, M.SPARK))
    if f in st.get("swirl", ()) and p.fx == "wind":
        for k in range(14):
            ang = math.radians(k * 26.0 + f * 40.0)
            rr = 9.0 - f * 1.4 + (k % 3) * 0.6
            P.fx.append((C + v3(math.cos(ang) * rr * 0.6, math.sin(ang) * rr, 2.0 + math.sin(ang * 2.0) * 1.5), M.WIND if k % 2 else M.DUST_DIM))
    if action == "attack" and f in st.get("gust", ()):
        for j in range(5):
            yy = (j - 2.0) * 2.6
            for d in range(4):
                P.fx.append((C + v3(5.0 + f * 2.0 + d * 1.2, yy + 0.4 * math.sin(d + j), -1.0 + (j % 2) * 1.6), M.WIND if d < 3 else M.DUST_DIM))
    if action == "attack" and f in st.get("streaks", ()):
        for j in range(4):
            yy = (j - 1.5) * 2.0
            for d in range(3):
                P.fx.append((C + v3(-bd.r[0] - 1.5 - d * 1.3, yy, 1.5 + d * 0.9), M.WIND if d < 2 else M.DUST_DIM))
    if action == "attack" and f in st.get("rake", ()):
        for j in range(3):
            for d in range(3):
                P.fx.append((v3(lunge + 3.0 + d * 0.9, (j - 1) * 0.9, 0.4 + d * 0.2), M.DUST if d else M.SPECK))
    if p.fx == "cloud" and action in ("idle", "walk", "windup"):
        for k in range(5):
            u = (k * 0.23 + f * 0.11) % 1.0
            P.fx.append((C + v3(-4.0 - 6.0 * u, (k - 2.0) * 2.4, 0.5 - u), M.CLOUD_WISP if k % 2 else M.CLOUD_WISP_DIM))
    sq = st.get("squash", {}).get(f)
    if sq is not None:
        P.squash(sq[0], sq[1], sq[2], (lunge, 0.0, z))
    return P
