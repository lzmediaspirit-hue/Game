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

`imp` (the pebble imp, E2): no joints, `stone` paint (pits and flecks by the species' seed), a `grin` face (a heavy
brow, glowing eyes, a nub nose, a toothy grin, shard ears), pebble studs and an ember crack, a stone held in the right
hand (`held`, released on the blow), and `crumble` (kit.collapse: it comes apart into a heap). Its styles: idle `toss`,
walk `waddle`, windup `wind_throw`, attack `throw`, hurt `knock`, death `crumble`.
"""
from __future__ import annotations

import math

import numpy as np

from figure.geom import ik2

from .. import mats as M
from ..motion import h01v, wave
from ..sculpt import E, L, Pose, S, on, rot, v3
from .kit import collapse

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
IMP_STYLES = {
    "toss": {"sway_amp": 0.3, "guard": 0.3,
             "right": ((2.6, -2.6, -2.2), (2.8, -2.4, -1.4), (2.9, -2.3, -0.8), (2.8, -2.4, -1.2), (2.6, -2.6, -2.0), (2.5, -2.7, -2.4)),
             "toss": (0.0, 0.9, 2.0, 1.3, 0.3, 0.0)},
    "waddle": {"kind": "march", "bounce": 0.6, "twist_amp": 10.0, "stride": 1.8, "lift": 1.0, "swing": 1.2},
    "wind_throw": {"lean": (-4.0, -9.0, -13.0, -15.0), "twist": (-14.0, -28.0, -38.0, -42.0), "step": (-0.3, -0.6, -0.8, -0.9),
                   "sink": (0.2, 0.4, 0.6, 0.7), "plant": True, "glare": True,
                   "right": ((0.0, -4.2, 0.8), (-1.2, -4.6, 3.4), (-2.2, -4.6, 5.2), (-2.6, -4.6, 5.9)),
                   "left": ((2.2, 3.6, -1.8), (3.4, 3.2, -0.6), (4.4, 2.8, 0.4), (4.8, 2.6, 0.8))},
    "throw": {"lean": (6.0, 14.0, 16.0, 12.0, 6.0, 2.0), "twist": (14.0, 36.0, 42.0, 34.0, 16.0, 4.0), "step": (0.8, 2.0, 2.4, 2.2, 1.2, 0.4),
              "sink": (0.6, 1.0, 0.9, 0.6, 0.3, 0.1), "plant": True, "release": 1, "squash": {1: (1.04, 1.0, 0.97)},
              "right": ((-0.6, -2.6, 5.6), (4.8, -1.2, 2.2), (5.6, -0.6, -1.2), (4.4, -1.0, -3.2), (2.6, -2.2, -4.0), (1.4, -3.4, -4.4)),
              "left": ((3.6, 3.2, -0.4), (0.4, 4.0, -2.6), (-0.6, 4.2, -3.4), (0.0, 4.2, -3.6), (0.6, 4.0, -4.0), (1.0, 3.9, -4.4))},
    "knock": {"lean": (-14.0, -6.0, -2.0), "twist": (10.0, -4.0, 0.0), "step": (-1.8, -1.0, -0.3), "sink": (0.3, 0.1, 0.0),
              "droop": (-12.0, -4.0, 0.0), "squint": True,
              "right": ((1.0, -5.0, 0.8), (1.6, -4.4, -2.0), (1.2, -3.8, -3.6)), "left": ((0.8, 5.0, 0.8), (1.4, 4.4, -2.0), (1.0, 3.9, -4.0))},
    "crumble": {"lean": (-6.0, 4.0, 10.0, 14.0, 14.0, 14.0, 14.0, 14.0), "sink": (0.0, 1.0, 2.4, 3.4, 3.6, 3.6, 3.6, 3.6),
                "droop": (0.0, 16.0, 24.0, 28.0, 28.0, 28.0, 28.0, 28.0), "crumble": (0.0, 0.0, 0.2, 0.45, 0.7, 0.9, 1.0, 1.0),
                "limp": True, "dark_from": 3},
}
STYLES.update(IMP_STYLES)

IMP = {
    "hip": 5.4,
    "legs": {"top": (1.8, -0.4), "foot": (2.3, 0.9, 0.5), "bones": (2.6, 2.7), "thigh": (1.25, 1.1), "shin": (1.1, 0.95),
             "knee": None, "boot": ((0.7, 0.0, -0.3), (1.8, 1.25, 0.8)), "plant": (0.9, -1.0)},
    "trunk": [{"at": (0.0, 0.0, 0.6), "r": (2.0, 2.6, 1.7), "mat": "dark"}, {"at": (0.6, 0.0, 2.8), "r": (2.6, 2.9, 2.5), "paint": True},
              {"at": (0.0, 0.0, 4.9), "r": (2.0, 3.0, 1.9), "paint": True}],
    "neck": ((0.1, 0.0, 6.3), 1.0),
    "head": {"at": ((0.4, 0.0, 6.4), 3.4), "r": (3.7, 4.2, 3.5)},
    "face": {"kind": "grin", "brow": ((2.5, 0.0, 1.2), (1.3, 3.2, 0.9)), "eyes": (3.25, 1.4, 0.3), "nose": ((3.75, 0.0, -0.3), 0.6),
             "grin": ((2.9, 0.0, -1.6), (1.0, 2.7, 0.55)), "teeth": (3.65, 1.9, -1.45, 0.62),
             "ears": ((0.2, 3.3, 1.0), (-0.8, 6.2, 3.8), (1.1, 0.15))},
    "arms": {"shoulder": (3.2, 5.4), "bones": (3.3, 3.4), "hint": (-0.6, 1.0, -1.0), "ball": None, "upper": (1.0, 0.92), "elbow": None,
             "lower": (0.92, 0.85), "wrap": None, "fist": (1.25, 1.1, 1.1), "guard": (1.2, 4.4, -4.4), "limp": (0.6, 4.4, -5.0, 0.3)},
    "paint": {"kind": "stone"},
    # Pebbles studding it (on the belly, the chest, the head: which piece, round it, up it, how big) and the glowing crack
    # in its belly (points round and up the belly).
    "studs": ((1, 30.0, 40.0, 0.55, "ochre"), (1, -40.0, 10.0, 0.6, "slate"), (1, 70.0, -20.0, 0.5, "rust"), (2, -60.0, 50.0, 0.5, "ochre"),
              (2, 110.0, 30.0, 0.55, "slate"), (3, 150.0, 30.0, 0.6, "slate"), (3, -120.0, 50.0, 0.5, "ochre")),
    "crack": ((-16.0, 34.0), (-6.0, 22.0), (-13.0, 10.0), (-3.0, -2.0), (-10.0, -14.0)),
    "held": {"r": 1.0, "mat": "slate"},
}
VARIANTS = {
    "imp": {"parts": IMP, "mats": {"body": "imp_stone", "limb": "imp_limb", "dark": "imp_limb", "joint": "imp_limb", "neck": "imp_limb",
                                   "maw": "maw", "ochre": "peb_ochre", "slate": "peb_slate", "rust": "peb_rust"},
            "motion": {"idle": "toss", "walk": "waddle", "windup": "wind_throw", "attack": "throw", "hurt": "knock", "death": "crumble"}},
    "puppet": {"parts": PUPPET, "mats": {"body": "timber", "limb": "timber", "dark": "timber_dark", "joint": "brass", "sash": "puppet_jade",
                                         "wrap": "rope"},
               "motion": {"idle": "guard_sway", "walk": "march", "windup": "draw_palm", "attack": "palm_strike", "hurt": "rock_back",
                          "death": "joints_give"}},
}


def pose(B, action: str, f: int, view: float = 48.0) -> Pose:
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

    limb = grain
    if p.paint.kind == "stone":
        grain, limb = _stone(m, hip, tm, int(B.opts.get("seed", 0))), None

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
        P.add(L(top, knee, g.thigh[0], g.thigh[1], m.limb, "leg%d" % s, limb), *([S(knee, g.knee, m.joint, "leg%d" % s)] if g.knee else []),
              L(knee, end, g.shin[0], g.shin[1], m.limb, "leg%d" % s, limb),
              E(end + v3(g.boot[0]), g.boot[1], m.dark, "foot%d" % s))
    # The trunk: hips, waist, chest (the sash and back plate), a neck joint, the head.
    P.add(*[E(up(t.at), t.r, m[t.get("mat", "body")], "body", tm, grain if t.get("paint") else None) for t in p.trunk])
    P.add(S(up(p.neck[0]), p.neck[1], m.get("neck", m.joint), "neck"))
    droop = B.pick("droop", action, f)
    hm = tm @ rot("b", -droop)
    hc = up(p.head.at[0]) + hm @ v3(0.0, 0.0, p.head.at[1])
    P.add(E(hc, p.head.r, m.body, "head", hm, grain))
    fc = p.face
    if fc.kind == "grin":
        _grin(P, B, action, f, hc, hm, grain, math.sin(math.radians(view)) > -0.5)
    else:
        _slits(P, B, action, f, hc, hm)
    _arms(P, B, action, f, up, tm, limb, march)
    if p.get("studs"):
        _studs(P, B, up, tm, hc, hm, math.sin(math.radians(view)) > -0.5)
    _finish(P, B, action, f, step)
    return P


def _slits(P, B, action: str, f: int, hc, hm) -> None:
    """Carved slits for eyes, a mouth line, a tuft on the crown (dark when beaten) and a mark on the brow."""
    m, st, fc = B.mats, B.style(action), B.parts.face
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


def _arms(P, B, action: str, f: int, up, tm, grain, march: bool) -> None:
    """Arms: balls at the shoulders, limbs, balls at the elbows, a wrap at the wrists (where it has them), fists; the
    hands reach for the frame's targets (`right`, `left`), else hang limp in the fall, else on guard, swinging in the
    march. The puppet's palm gathers Qi; a thrower's right hand holds what it throws until the blow."""
    p, m, st = B.parts, B.mats, B.style(action)
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
        P.add(*([S(sh, a_.ball, m.joint, "arm%d" % s)] if a_.ball else []),
              L(sh, elbow, a_.upper[0], a_.upper[1], m.limb, "arm%d" % s, grain),
              *([S(elbow, a_.elbow, m.joint, "arm%d" % s)] if a_.elbow else []),
              L(elbow, end, a_.lower[0], a_.lower[1], m.limb, "arm%d" % s, grain),
              *([S(elbow + (end - elbow) * a_.wrap[0], a_.wrap[1], m.wrap, "arm%d" % s)] if a_.wrap else []),
              E(end, a_.fist, m.dark, "arm%d" % s, tm))
        if p.get("qi") and s < 0:
            _qi(P, B, action, f, end, tm)
        if p.get("held") and s < 0:
            _held(P, B, action, f, end, tm)


def _finish(P, B, action: str, f: int, step: float) -> None:
    """The fall (toppled onto its side, or crumbled into a heap of stones) and the squash."""
    st = B.style(action)
    roll = B.pick("roll", action, f)
    if roll:
        mid, half = st.fall
        P.m = rot("a", roll)
        turned = P.m @ v3(0.0, 0.0, mid)
        P.shift = v3(-turned[0], -turned[1], mid - turned[2] - (mid - half) * math.sin(math.radians(min(roll, 90.0))))
    crumble = B.pick("crumble", action, f)
    if crumble > 0.0:
        collapse(P, crumble, int(B.opts.get("seed", 0)))
    sq = st.get("squash", {}).get(f)
    if sq is not None:
        P.squash(sq[0], sq[1], sq[2], (step, 0.0, 0.0))


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


# ================================================================================================= stone bodies (the imp)
def _stone(m, hip, tm, seed: int):
    """Stone: its grain a step dark in pits and cracks, a step lit in flecks (by the species' seed), on its own
    material."""
    def stone(q, n):
        loc = (q - hip) @ tm
        pit = h01v(np.floor(loc[:, 0] * 1.5 + 40), np.floor(loc[:, 2] * 1.5 + 40) + np.floor(loc[:, 1] * 1.5), seed % 97 + 1) > 0.84
        fleck = h01v(np.floor(loc[:, 1] * 2.2 + 60), np.floor(loc[:, 2] * 2.2 + 60), seed % 89 + 2) > 0.93
        return np.full(len(q), m.body, dtype=object), np.where(pit, -1, np.where(fleck, 1, 0)).astype(np.int16)
    return stone


def _grin(P, B, action: str, f: int, hc, hm, paint, facing: bool = True) -> None:
    """A stone imp's face: a heavy brow over two glowing amber eyes (flaring in the tell, squinting when struck, dark when
    it crumbles), a nub of a nose, a wide grin of pale teeth, and a shard of stone for each ear."""
    m, st, fc = B.mats, B.style(action), B.parts.face
    br = fc.brow[1]
    P.add(E(hc + hm @ v3(fc.brow[0]), br, m.body, "brow", hm, paint, line=False))
    P.add(S(hc + hm @ v3(fc.nose[0]), fc.nose[1], m.body, "nose", paint))
    P.add(E(hc + hm @ v3(fc.grin[0]), fc.grin[1], m.maw, "grin", hm, line=False))
    ta, tw, tc, step = fc.teeth
    y = -tw
    while y <= tw + 1e-6:
        P.mark(hc + hm @ v3(ta - 0.15 * abs(y), y, tc), M.IMP_TOOTH)
        y += step
    (e0, e1, (r0, r1)) = fc.ears
    for s in (1, -1):
        P.add(L(hc + hm @ v3(e0[0], s * e0[1], e0[2]), hc + hm @ v3(e1[0], s * e1[1], e1[2]), r0, r1, m.body, "ear%d" % s, paint))
    dark = action == "death" and f >= st.get("dark_from", 99)
    ea, eb, ec = fc.eyes
    for s in (1, -1):
        eye = hc + hm @ v3(ea, s * eb, ec)
        if dark:
            P.mark(eye, M.RAMPS[m.body][0])
            continue
        if st.get("squint"):
            P.mark(eye, M.EMBER_DIM)
            continue
        P.eye(eye, M.EMBER_CORE)
        for d in ((0.0, 0.35, 0.0), (0.0, -0.35, 0.0), (0.0, 0.0, 0.35)):
            P.mark(eye + hm @ v3(*d), M.EMBER)
        if st.get("glare") and facing:
            for d in ((0.3, 0.0, 0.8), (0.3, 0.7, 0.4), (0.3, -0.7, 0.4), (0.3, 0.0, -0.7)):
                P.glow.append((eye + hm @ v3(*d), M.EMBER_GLOW))


def _studs(P, B, up, tm, hc, hm, facing: bool = True) -> None:
    """Pebbles studding its stone (ochre, slate, rust), and the crack in its belly glowing with the ember inside it."""
    p, m = B.parts, B.mats
    pieces = [(up(t.at), t.r, tm) for t in p.trunk] + [(hc, p.head.r, hm)]
    for i, u, v, r, kind in p.studs:
        c, rad, mm = pieces[i]
        P.add(S(on(c, rad, mm, u, v, -r * 0.35), r, m[kind], "stud", line=False))
    c, rad, mm = pieces[1]
    pts = [on(c, rad, mm, u, v, 0.15) for u, v in p.crack]
    for a, b in zip(pts, pts[1:]):
        for k in range(4):
            q = a + (b - a) * (k / 4.0)
            P.mark(q, M.EMBER if k % 2 else M.EMBER_CORE)
            if facing:
                P.glow.append((q + mm @ v3(0.4, 0.0, 0.0), M.EMBER_GLOW))


def _held(P, B, action: str, f: int, end, tm) -> None:
    """What it throws, held in its right hand (tossed up and caught while idle) until the blow, and on the release frame
    leaving the hand (the room view draws it in flight)."""
    h, m, st = B.parts.held, B.mats, B.style(action)
    rel = st.get("release")
    if action == "death" or rel is not None and f > rel:
        return
    if rel is not None and f == rel:
        q = end + tm @ v3(3.0, 0.0, 0.3)
        P.add(S(q, h.r, m[h.mat], "pebble"))
        for k in range(3):
            P.fx.append((q - tm @ v3(1.6 + k * 0.9, 0.0, 0.1 * k), M.DUST if k else M.DUST_DIM))
        return
    toss = B.pick("toss", action, f)
    P.add(S(end + tm @ v3(0.9, 0.0, 0.7 + toss), h.r, m[h.mat], "pebble"))
