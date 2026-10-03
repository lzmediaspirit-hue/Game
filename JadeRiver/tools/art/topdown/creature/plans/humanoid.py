"""The two-legged plan (audit 45 §6.2), from the Trial Puppet (`puppet`): legs bent by two-bone IK, a trunk of hips,
waist and chest twisting and leaning over them, a head on a neck joint, and arms reaching their hands to targets.

  body   the hips' height, the legs' bones and radii, the trunk's three pieces, the neck, the head
  arms   the shoulders' place, the bones and radii; the hands' targets per frame (the channels `right` and `left`, from
         the chest at the shoulders' height: ahead, out, up), else on guard
  joints `ball`: balls at the knees, shoulders and elbows, and a wrap at the wrists (the puppet's brass and rope)
  paint  `grain`: carved timber's grain, a sash across the chest and a plate on the back
  face   carved slits for eyes, a mouth line, a tuft on the crown and a mark on the brow (dark when beaten)
  qi     the puppet's palm: a jade orb gathering at the drawn palm in the tell, a ring bursting on the blow

The motion styles (STYLES): idle `guard_sway`, walk `march`, windup `draw_palm`, attack `palm_strike`, hurt
`rock_back`, death `joints_give`. Channels: lean, twist, step, sink, droop (the head), roll, right, left, qi.
"""
from __future__ import annotations

import math

import numpy as np

from figure.geom import ik2

from .. import mats as M
from ..motion import wave
from ..sculpt import E, L, Pose, S, rot, v3

STYLES = {
    "guard_sway": {"sway_amp": 0.35, "guard": 0.4},
    "march": {"kind": "march", "bounce": 0.5, "twist_amp": 6.0, "stride": 2.8, "lift": 1.4, "swing": 1.6},
    "draw_palm": {"lean": (-4.0, -8.0, -10.0, -11.0), "twist": (-10.0, -22.0, -30.0, -34.0), "step": (-0.4, -0.8, -1.0, -1.2),
                  "sink": (0.2, 0.5, 0.8, 1.0), "plant": True,
                  "right": ((0.6, -4.6, -2.0), (-1.4, -4.8, -3.6), (-2.6, -4.6, -4.4), (-3.0, -4.4, -4.6)),
                  "left": ((4.0, 3.4, -1.4), (5.6, 2.4, -1.0), (6.4, 1.6, -0.8), (6.6, 1.4, -0.8)), "qi": (0.0, 0.3, 0.65, 1.0)},
    "palm_strike": {"lean": (6.0, 12.0, 12.0, 14.0, 6.0, 2.0), "twist": (-10.0, 24.0, 30.0, 36.0, 16.0, 4.0), "step": (1.6, 3.4, 3.6, 3.4, 2.0, 0.8),
                    "sink": (0.6, 1.2, 1.1, 0.8, 0.4, 0.1), "plant": True,
                    "right": ((3.2, -3.6, -1.2), (8.6, -2.2, -0.6), (8.8, -2.2, -0.6), (7.6, -2.6, -1.0), (4.4, -3.4, -1.6), (3.2, -3.6, -1.8)),
                    "left": ((4.0, 3.6, -1.6), (1.0, 4.6, -2.8), (0.6, 4.8, -3.0), (1.4, 4.6, -2.4), (2.6, 4.0, -1.8), (3.2, 3.8, -1.8)),
                    "qi": (1.0, 1.6, 2.3, 0.0, 0.0, 0.0), "squash": {1: (1.04, 1.0, 0.97)}},
    "rock_back": {"lean": (-12.0, -6.0, -2.0), "twist": (8.0, -4.0, 0.0), "step": (-2.0, -1.2, -0.4), "sink": (0.4, 0.2, 0.0),
                  "droop": (-14.0, -4.0, 0.0), "right": ((1.6, -6.4, 1.4), (2.6, -5.0, -1.0), (3.2, -3.8, -1.8)),
                  "left": ((1.0, 6.6, 1.6), (2.2, 5.0, -1.0), (3.0, 3.8, -1.8)), "squint": True},
    "joints_give": {"lean": (-6.0, 4.0, 10.0, 18.0, 16.0, 14.0, 14.0, 14.0), "sink": (0.0, 0.6, 3.0, 6.0, 6.4, 6.6, 6.6, 6.6),
                    "droop": (0.0, 18.0, 26.0, 30.0, 30.0, 30.0, 30.0, 30.0), "roll": (0.0, 0.0, 0.0, 16.0, 46.0, 76.0, 88.0, 86.0),
                    "limp": True, "dark_from": 5, "fall": (8.0, 3.2)},
}

PUPPET = {
    "hip": 15.6,
    "legs": {"top": (2.3, -0.6), "foot": (2.8, 1.0, 0.8), "bones": (7.4, 7.6), "thigh": (1.75, 1.45), "shin": (1.45, 1.25),
             "knee": 1.6, "boot": ((0.9, 0.0, -0.2), (2.6, 1.4, 1.0)), "plant": (1.2, -1.4)},
    "trunk": [{"at": (0.0, 0.0, 0.6), "r": (2.5, 3.8, 2.0), "paint": True}, {"at": (0.0, 0.0, 3.4), "r": (1.9, 2.8, 1.8), "mat": "dark"},
              {"at": (0.0, 0.0, 6.4), "r": (2.9, 4.6, 4.2), "paint": True}],
    "neck": ((0.0, 0.0, 11.0), 1.15),
    "head": {"at": ((0.3, 0.0, 11.4), 2.6), "r": (2.7, 2.5, 3.0)},
    "face": {"kind": "slits", "eyes": ((2.55, 1.0, 0.5), (2.6, 0.55, 0.5)), "mouth": (2.7, 0.0, -1.1), "tuft": ((-0.3, 0.0, 3.2), 1.05, (-0.8, 0.3, 0.9), 0.8),
             "brow": (2.4, 0.0, 1.9)},
    "arms": {"shoulder": (5.1, 8.6), "bones": (4.4, 4.2), "hint": (-0.6, 1.0, -1.0), "ball": 1.6, "upper": (1.3, 1.2), "elbow": 1.25,
             "lower": (1.2, 1.1), "wrap": (0.82, 1.2), "fist": (1.7, 1.55, 1.55), "guard": (3.4, 3.4, -1.2), "limp": (0.8, 5.8, -5.8, 0.4)},
    "paint": {"kind": "grain"},
    "qi": True,
}
VARIANTS = {
    "puppet": {"parts": PUPPET, "mats": {"body": "timber", "dark": "timber_dark", "joint": "brass", "sash": "puppet_jade", "wrap": "rope"},
               "motion": {"idle": "guard_sway", "walk": "march", "windup": "draw_palm", "attack": "palm_strike", "hurt": "rock_back",
                          "death": "joints_give"}},
}


def pose(B, action: str, f: int) -> Pose:
    P = Pose()
    p, m = B.parts, B.mats
    st = B.style(action)
    lean = B.pick("lean", action, f)
    twist = B.pick("twist", action, f)
    step = B.pick("step", action, f)
    sink = B.pick("sink", action, f)
    sway = st.sway_amp * wave(action, f) if "sway_amp" in st else 0.0
    bounce = 0.0
    march = st.get("kind") == "march"
    if march:
        bounce = st.bounce * abs(math.sin(f / 8.0 * math.tau))
        twist = st.twist_amp * math.sin(f / 8.0 * math.tau)
    hip = v3(step, sway, p.hip - sink + bounce)
    tm = rot("c", twist) @ rot("b", -lean) @ rot("a", sway * 3.0)
    up = lambda q: hip + tm @ v3(q)

    def grain(q, n):
        """Carved timber: the grain in fine dark streaks up the torso; the sash from the left shoulder to the right hip,
        and the plate on the back."""
        loc = (q - hip) @ tm
        nl = n @ tm
        sash = (np.abs((loc[:, 2] - 6.0) - loc[:, 1] * 0.95) < 1.05) & (nl[:, 0] > -0.2)
        plate = (nl[:, 0] < -0.5) & (loc[:, 2] > 4.6) & (loc[:, 2] < 9.4) & (np.abs(loc[:, 1]) < 2.4)
        streak = ((loc[:, 1] * 1.3 + loc[:, 0] * 0.4) % 1.9 < 0.4) & ~sash & ~plate
        names = np.where(sash | plate, m.sash, m.body).astype(object)
        return names, np.where(streak, -1, 0).astype(np.int16)

    # Legs: a stride in the march, planted apart otherwise; knees folding as it sinks.
    g = p.legs
    for s in (1, -1):
        ph = f / 8.0 * math.tau + (0.0 if s > 0 else math.pi)
        stride = st.stride * math.sin(ph) if march else 0.0
        lift = st.lift * max(0.0, math.cos(ph)) if march else 0.0
        plant = (g.plant[0] if s > 0 else g.plant[1]) if st.get("plant") else 0.0
        foot = v3(stride + plant + g.foot[2] + (step if s > 0 else step * 0.5), s * g.foot[0], g.foot[1] + lift)
        top = hip + rot("c", twist * 0.4) @ v3(0.0, s * g.top[0], g.top[1])
        knee, end = ik2(top, foot, g.bones[0], g.bones[1], v3(1.0, 0.0, 0.0))
        P.add(L(top, knee, g.thigh[0], g.thigh[1], m.body, "leg%d" % s, grain), S(knee, g.knee, m.joint, "leg%d" % s),
              L(knee, end, g.shin[0], g.shin[1], m.body, "leg%d" % s, grain),
              E(end + v3(g.boot[0]), g.boot[1], m.dark, "foot%d" % s))
    # The trunk: hips, waist, chest (the sash and back plate), a neck joint, the head.
    P.add(*[E(up(t.at), t.r, m[t.get("mat", "body")], "body", tm, grain if t.get("paint") else None) for t in p.trunk])
    P.add(S(up(p.neck[0]), p.neck[1], m.joint, "neck"))
    droop = B.pick("droop", action, f)
    hm = tm @ rot("b", -droop)
    hc = up(p.head.at[0]) + hm @ v3(0.0, 0.0, p.head.at[1])
    P.add(E(hc, p.head.r, m.body, "head", hm, grain))
    fc = p.face
    (ea, eb, ec), (ia, ib, ic) = fc.eyes
    for s in (1, -1):
        P.mark(hc + hm @ v3(ea, s * eb, ec), M.INKY)
        P.mark(hc + hm @ v3(ia, s * ib, ic), M.INKY if not st.get("squint") else M.RAMPS[m.body][1])
    P.mark(hc + hm @ v3(fc.mouth), M.RAMPS[m.dark][0])
    dark = action == "death" and f >= st.get("dark_from", 99)
    jade = m.dark if dark else m.sash
    t0, r0, t1, r1 = fc.tuft
    tuft = hc + hm @ v3(t0)
    P.add(S(tuft, r0, jade, "tuft"), S(tuft + hm @ v3(t1), r1, jade, "tuft"))
    if not dark:
        P.mark(hc + hm @ v3(fc.brow), M.QI)      # the jade mark on the brow
    # Arms: balls at the shoulders, limbs, balls at the elbows, a wrap at the wrists, dark fists. Guard: fists up before
    # the chest; the march swings them.
    a_ = p.arms
    sw = st.swing * math.sin(f / 8.0 * math.tau) if march else 0.0
    guard = st.guard * wave(action, f, 0.25) if "guard" in st else 0.0
    for s in (1, -1):
        sh = up((0.0, s * a_.shoulder[0], a_.shoulder[1]))
        if s < 0 and B.has("right", action):
            rel = B.pick("right", action, f)
        elif s > 0 and B.has("left", action):
            rel = B.pick("left", action, f)
        elif st.get("limp"):
            rel = (a_.limp[0], s * a_.limp[1], a_.limp[2] - min(f, 3) * a_.limp[3])
        else:
            rel = (a_.guard[0] + sw * s, s * a_.guard[1], a_.guard[2] + guard)
        fist = up((rel[0], rel[1], a_.shoulder[1] + rel[2]))
        elbow, end = ik2(sh, fist, a_.bones[0], a_.bones[1], tm @ v3(a_.hint[0], s * a_.hint[1], a_.hint[2]))
        P.add(S(sh, a_.ball, m.joint, "arm%d" % s), L(sh, elbow, a_.upper[0], a_.upper[1], m.body, "arm%d" % s, grain),
              S(elbow, a_.elbow, m.joint, "arm%d" % s),
              L(elbow, end, a_.lower[0], a_.lower[1], m.body, "arm%d" % s, grain),
              S(elbow + (end - elbow) * a_.wrap[0], a_.wrap[1], m.wrap, "arm%d" % s),
              E(end, a_.fist, m.dark, "arm%d" % s, tm))
        if p.get("qi") and s < 0:
            _qi(P, B, action, f, end, tm)
    roll = B.pick("roll", action, f)
    if roll:
        mid, half = st.fall
        P.m = rot("a", roll)
        turned = P.m @ v3(0.0, 0.0, mid)
        P.shift = v3(-turned[0], -turned[1], mid - turned[2] - (mid - half) * math.sin(math.radians(min(roll, 90.0))))
    sq = st.get("squash", {}).get(f)
    if sq is not None:
        P.squash(sq[0], sq[1], sq[2], (step, 0.0, 0.0))
    return P


def _qi(P, B, action: str, f: int, end, tm) -> None:
    """Qi: a jade orb gathering at the drawn palm in the tell (a bright core in a glow, a ring turning round it),
    bursting at the knuckles on the blow in a wide ring."""
    q = B.pick("qi", action, f)
    if q <= 0.0:
        return
    c = end + tm @ v3(1.2 + (0.8 if action == "attack" else 0.0), 0.0, 0.0)
    core = 0.5 + 0.9 * min(q, 1.0) if action == "windup" or f == 0 else 0.6
    for dy in np.arange(-core * 2.2, core * 2.2 + 0.01, 0.55):
        for dz in np.arange(-core * 2.2, core * 2.2 + 0.01, 0.55):
            d = math.hypot(dy, dz)
            if d <= core * 2.2:
                col = M.QI_BRIGHT if d < core * 0.9 else (M.QI if d < core * 1.6 else (0x4C, 0xB6, 0xA2, 150))
                P.glow.append((c + tm @ v3(0.0, dy, dz), col))
    rr = 2.2 + q * 1.8
    n = 12 if q < 1.2 else 20
    for k in range(n):
        ang = math.radians(k * 360.0 / n + f * 15.0)
        col = M.QI_BRIGHT if k % 2 == 0 and q >= 1.0 else (M.QI if k % 3 else M.QI_DIM)
        P.glow.append((c + tm @ v3(0.0, math.cos(ang) * rr, math.sin(ang) * rr), col))
    if action == "windup" and f >= 1:
        for k in range(4):
            P.glow.append((c + v3(-0.6 + k * 0.7, -1.4 + k * 0.9, 3.0 + k * 1.1 + f * 0.5), M.QI_DIM))
