"""The top-down action catalog: every animation the figure has, frame by frame, as poses of the unclothed body
(AGENTS.md rule 4). Every layer is cast from these same poses (rule 2), in every drawn facing (S, SE, E, NE, N; the
west facings mirror). Meditation faces the camera only (redesign plan §1.4): its other facings redirect to S.

Poses are in the figure's own frame (skeleton.py): f forward, r the character's right, u up. The weapon lines:
`blade` is where the jian's and the short blade's point goes, `pole` the spear's line (`two_hand` runs it through both
hands). The combo strikes follow the side view's three families (weapon_families.json): punch_1-3 for fists and
gauntlets (lead jab, rear cross, rising uppercut), swing_1-3 for the jian (rising cut, return cut, heavy descending
cut), thrust_1-3 for the spear and the short blade (straight, low, high lunging thrust).
"""
from __future__ import annotations

import math

from .skeleton import pose

# idle / walk carriage of each weapon line
BLADE_IDLE = (0.7, 0.42, -0.58)
POLE_IDLE = {"dir": (0.14, 0.12, 1.0), "butt": 12.6}


def W(blade=None, pole=None, flat=(0.0, 1.0, 0.0), laid=None, smear_from=None):
    return {"blade": blade or BLADE_IDLE, "pole": pole or POLE_IDLE, "flat": flat, "laid": laid, "smear_from": smear_from}


def feet(fl=0.0, fr=0.0, wl=2.2, wr=2.2, ul=1.3, ur=1.3):
    return {"foot_l": (fl, -wl, ul), "foot_r": (fr, wr, ur)}


def stance(front=2.2, back=-1.8, **kw):
    """A fighting stance: left foot forward, right foot back and out."""
    d = feet(front, back, 2.0, 2.5)
    d["foot_yaw_r"] = 22.0
    d.update(kw)
    return d


def guard_hands(**kw):
    d = {"hand_l": (4.2, -1.9, 21.2), "hand_r": (3.2, 2.3, 20.2), "elbow_l": (-0.3, -1.0, -1.0),
         "elbow_r": (-0.3, 1.0, -1.0), "grip_l": "fist", "grip_r": "fist"}
    d.update(kw)
    return d


def _idle(i):
    b = [0.0, -0.1, -0.2, -0.1][i]
    return pose(pelvis=(0.0, 0.0, 13.4 + b), hand_l=(0.4, -5.9, 13.6 + b * 0.6), hand_r=(0.4, 5.9, 13.6 + b * 0.6),
                drag=(0.0, [0.0, 0.08, 0.0, -0.08][i], 0.0), weapon=W())


def _walk(i, n=8):
    ph = 2 * math.pi * i / n
    c, s = math.cos(ph), math.sin(ph)
    stride, lift = 2.9, 1.7
    fl, fr = stride * c, -stride * c
    ul = 1.3 + lift * max(0.0, -s)
    ur = 1.3 + lift * max(0.0, s)
    bob = -0.35 * math.cos(2 * ph)
    return pose(pelvis=(0.0, 0.0, 13.35 + bob), hip_yaw=5 * c, twist=-9 * c,
                **feet(fl, fr, 2.1, 2.1, ul, ur), toe_l=-12 * c * (ul < 1.4), toe_r=12 * c * (ur < 1.4),
                hand_l=(-2.3 * c + 0.3, -5.8, 14.2), hand_r=(2.3 * c + 0.3, 5.8, 14.2),
                drag=(-0.5, 0.12 * s, 0.0), weapon=W(blade=(0.45 + 0.25 * c, 0.42, -0.6), pole={"dir": (0.28, 0.1, 1.0), "butt": 12.6}))


def _run(i, n=8):
    ph = 2 * math.pi * i / n
    c, s = math.cos(ph), math.sin(ph)
    stride = 4.0
    fl, fr = stride * c, -stride * c
    # the swinging foot lifts high; the one behind kicks up
    ul = 1.3 + max(0.0, -s) * 2.6 + max(0.0, -c) * 1.6
    ur = 1.3 + max(0.0, s) * 2.6 + max(0.0, c) * 1.6
    bob = -0.6 * math.cos(2 * ph) + 0.2
    return pose(pelvis=(0.4, 0.0, 12.9 + bob), lean=14.0, hip_yaw=7 * c, twist=-13 * c,
                **feet(fl + 0.4, fr + 0.4, 2.0, 2.0, ul, ur), toe_l=18 * max(0, -c), toe_r=18 * max(0, c),
                hand_l=(-3.2 * c + 1.8, -5.0, 17.0 + 1.2 * max(0, c)), hand_r=(3.2 * c + 1.8, 5.0, 17.0 + 1.2 * max(0, -c)),
                elbow_l=(-1.0, -0.5, -0.3), elbow_r=(-1.0, 0.5, -0.3), grip_l="fist", grip_r="fist",
                drag=(-1.7, 0.1 * s, 0.35), weapon=W(blade=(-0.8, 0.35, -0.55), pole={"dir": (-0.55, 0.12, 0.85), "butt": 14.0}))


def _jump(i):
    return [
        # takeoff crouch
        pose(pelvis=(0.3, 0.0, 11.3), lean=12, **feet(0.4, -0.4, 2.3, 2.3), hand_l=(-2.0, -5.6, 13.5),
             hand_r=(-2.0, 5.6, 13.5), drag=(-0.2, 0.0, -0.3), weapon=W(blade=(-0.4, 0.4, -0.9))),
        # rise: legs stretched down, arms up
        pose(pelvis=(0.0, 0.0, 13.8), lean=-4, **feet(0.4, -0.6, 2.0, 2.0, 0.6, 0.9), toe_l=35, toe_r=30,
             hand_l=(2.0, -5.5, 25.0), hand_r=(2.0, 5.5, 25.0), elbow_l=(-1.0, -1.0, 0.0), elbow_r=(-1.0, 1.0, 0.0),
             drag=(-0.3, 0.0, -1.0), weapon=W(blade=(0.4, 0.8, 0.2))),
        # apex: knees tucked
        pose(pelvis=(0.0, 0.0, 14.0), **feet(1.6, 1.0, 2.2, 2.2, 5.6, 6.4), knee_l=(1, -0.3, 0.2), knee_r=(1, 0.3, 0.2),
             toe_l=20, toe_r=20, hand_l=(1.4, -6.6, 20.0), hand_r=(1.4, 6.6, 20.0), drag=(-0.2, 0.0, 0.3),
             weapon=W(blade=(0.2, 0.9, -0.3))),
        # fall: legs reaching down, arms up and out
        pose(pelvis=(0.0, 0.0, 13.8), **feet(0.8, -0.3, 2.4, 2.4, 1.8, 2.6), toe_l=20, toe_r=25,
             hand_l=(0.5, -7.0, 24.0), hand_r=(0.5, 7.0, 24.0), drag=(-0.2, 0.0, 0.7), weapon=W(blade=(0.3, 0.9, -0.3))),
        # land: a deep crouch
        pose(pelvis=(0.4, 0.0, 10.9), lean=16, **feet(0.3, -0.3, 2.5, 2.5), hand_l=(3.0, -5.2, 12.5),
             hand_r=(3.0, 5.2, 12.5), drag=(0.2, 0.0, -0.6), weapon=W(blade=(0.5, 0.5, -0.8))),
    ][i]


def _dash(i):
    return [
        pose(pelvis=(0.6, 0.0, 12.6), lean=22, **feet(3.2, -3.4, 2.0, 2.2, 1.3, 2.8), toe_r=30,
             hand_l=(-3.5, -5.4, 16.0), hand_r=(-3.5, 5.4, 16.0), drag=(-2.2, 0.0, 0.5),
             weapon=W(blade=(-0.9, 0.35, -0.35), pole={"dir": (-0.8, 0.12, 0.55), "butt": 15.0})),
        pose(pelvis=(1.0, 0.0, 12.2), lean=30, **feet(4.4, -4.8, 2.0, 2.2, 1.6, 4.2), toe_l=-10, toe_r=45,
             hand_l=(-5.0, -5.0, 17.5), hand_r=(-5.0, 5.0, 17.5), drag=(-3.0, 0.0, 0.9),
             weapon=W(blade=(-0.95, 0.3, -0.15), pole={"dir": (-0.9, 0.12, 0.4), "butt": 15.0})),
        pose(pelvis=(1.0, 0.0, 12.3), lean=30, **feet(4.0, -4.6, 2.0, 2.2, 2.0, 3.6), toe_l=5, toe_r=40,
             hand_l=(-5.0, -5.2, 17.0), hand_r=(-5.0, 5.2, 17.0), drag=(-3.0, 0.0, 0.7),
             weapon=W(blade=(-0.95, 0.3, -0.2), pole={"dir": (-0.9, 0.12, 0.4), "butt": 15.0})),
        pose(pelvis=(0.4, 0.0, 12.8), lean=12, **feet(1.8, -1.6, 2.1, 2.2), hand_l=(-1.0, -5.8, 14.5),
             hand_r=(-1.0, 5.8, 14.5), drag=(-1.0, 0.0, 0.2), weapon=W(blade=(-0.4, 0.4, -0.9))),
    ][i]


def _dodge(i):
    return [
        pose(pelvis=(-0.4, 0.0, 12.8), lean=-8, **feet(1.0, -3.0, 2.1, 2.4), foot_yaw_r=20,
             **guard_hands(hand_l=(3.4, -2.2, 20.0), hand_r=(2.6, 2.6, 19.0)), drag=(0.8, 0.0, 0.2),
             weapon=W(blade=(0.8, 0.2, 0.5), pole={"two_hand": True})),
        pose(pelvis=(-1.0, 0.0, 14.4), lean=-14, **feet(0.4, -2.6, 2.2, 2.4, 3.4, 3.0), toe_l=25, toe_r=25,
             **guard_hands(hand_l=(3.0, -2.6, 21.0), hand_r=(2.4, 3.0, 20.0)), drag=(1.6, 0.0, 0.6),
             weapon=W(blade=(0.8, 0.2, 0.55), pole={"two_hand": True})),
        pose(pelvis=(-0.6, 0.0, 11.8), lean=-6, **feet(0.8, -2.2, 2.3, 2.5), foot_yaw_r=20,
             **guard_hands(hand_l=(3.4, -2.2, 19.0), hand_r=(2.8, 2.6, 18.2)), drag=(0.9, 0.0, -0.3),
             weapon=W(blade=(0.8, 0.2, 0.4), pole={"two_hand": True})),
        pose(pelvis=(-0.2, 0.0, 13.0), lean=-2, **feet(0.6, -1.2, 2.2, 2.3), hand_l=(1.4, -5.6, 15.0),
             hand_r=(1.4, 5.6, 15.0), drag=(0.3, 0.0, 0.0), weapon=W()),
    ][i]


def _hurt(i):
    return [
        pose(pelvis=(-0.9, 0.0, 13.0), lean=-14, twist=10, head_pitch=-16, **feet(0.6, -1.2, 2.3, 2.3),
             hand_l=(-1.0, -7.2, 18.0), hand_r=(-1.5, 7.2, 17.0), eyes="shut", drag=(1.2, 0.0, 0.5),
             weapon=W(blade=(-0.3, 0.7, -0.6))),
        pose(pelvis=(-0.5, 0.0, 13.1), lean=-7, twist=5, head_pitch=-6, **feet(0.4, -0.8, 2.2, 2.2),
             hand_l=(0.0, -6.6, 16.0), hand_r=(-0.4, 6.6, 15.5), drag=(0.6, 0.0, 0.2),
             weapon=W(blade=(0.0, 0.5, -0.9))),
    ][i]


def _knockdown(i):
    lying = dict(pelvis=(0.0, 0.0, 13.4), **feet(0.4, 0.8, 2.6, 2.8), hand_l=(1.0, -7.8, 16.5), hand_r=(0.5, 7.8, 17.0),
                 tip_at=-1.2, eyes="shut", weapon=W(blade=(0.3, 0.9, 0.0)))
    return [
        pose(pelvis=(-1.2, 0.0, 12.6), lean=-20, head_pitch=-12, **feet(0.8, -2.4, 2.3, 2.5), hand_l=(-0.5, -7.5, 20.0),
             hand_r=(-0.8, 7.5, 19.0), eyes="shut", drag=(1.4, 0.0, 0.6), weapon=W(blade=(-0.2, 0.8, -0.3))),
        pose(pelvis=(-0.6, 0.0, 12.2), lean=-12, **feet(0.6, -0.6, 2.4, 2.5, 1.3, 2.0), hand_l=(0.5, -7.5, 21.0),
             hand_r=(0.3, 7.5, 21.0), tip=-38, tip_at=-1.2, turn=12, eyes="shut", drag=(1.2, 0.0, 1.0), weapon=W(blade=(0.0, 0.8, 0.4))),
        pose(pelvis=(-0.2, 0.0, 12.8), lean=-4, **feet(0.8, 0.2, 2.5, 2.6, 1.8, 2.4), hand_l=(1.0, -7.6, 19.0),
             hand_r=(1.0, 7.6, 19.0), tip=-70, tip_at=-1.2, turn=24, sink=-1.8, eyes="shut", drag=(0.6, 0.0, 0.8),
             weapon=W(blade=(0.2, 0.9, 0.2))),
        pose(tip=-90, turn=32, sink=-3.0, head_pitch=-6, drag=(0.0, 0.0, 0.4), **lying),
        pose(tip=-90, turn=32, sink=-3.0, head_yaw=25, head_pitch=-4, drag=(0.0, 0.3, 0.2), **lying),
    ][i]


def _punch(k, i):
    st = stance()
    g = guard_hands()
    if k == 1:   # lead jab (left)
        seq = [dict(g, twist=0), dict(g, twist=8, hand_l=(6.5, -1.4, 21.4)), dict(g, twist=14, hand_l=(9.4, -0.9, 21.6), lean=6),
               dict(g, twist=8, hand_l=(6.0, -1.5, 21.3)), dict(g, twist=0)]
    elif k == 2:   # rear cross (right)
        seq = [dict(g, twist=4), dict(g, twist=-10, hand_r=(5.8, 1.6, 21.0)), dict(g, twist=-24, hand_r=(9.4, 0.6, 21.4), lean=8,
               hip_yaw=-10, hand_l=(3.4, -2.6, 20.6)), dict(g, twist=-12, hand_r=(6.0, 1.5, 20.8)), dict(g, twist=0)]
    else:   # rising uppercut (right)
        seq = [dict(g, twist=6, pelvis=(0.0, 0.0, 12.2), lean=10, hand_r=(3.4, 2.8, 15.5)),
               dict(g, twist=-6, pelvis=(0.3, 0.0, 12.6), lean=4, hand_r=(4.8, 1.8, 20.0)),
               dict(g, twist=-18, pelvis=(0.5, 0.0, 14.2), lean=-6, hand_r=(4.6, 1.0, 30.0), elbow_r=(0.2, 1.0, -1.0),
                    **feet(2.2, -1.8, 2.0, 2.5, 2.2, 2.6)),
               dict(g, twist=-10, pelvis=(0.3, 0.0, 13.6), lean=-2, hand_r=(4.4, 1.6, 26.0)),
               dict(g, twist=0)]
    out = []
    for j, s in enumerate(seq):
        d = dict(st)
        d.update(s)
        d.setdefault("drag", (0.4 if j == 2 else 0.1, 0.0, 0.0))
        d["weapon"] = W(blade=(0.9, 0.1, 0.45), pole={"two_hand": True})
        out.append(pose(**d))
    return out[i]


def _swing(k, i):
    st = stance(1.8, -1.6)
    left_seal = {"hand_l": (1.8, -4.4, 22.0), "elbow_l": (-0.5, -1.0, -0.6), "grip_l": "seal"}
    ready = dict(left_seal, hand_r=(4.2, 2.6, 17.6), blade=(0.9, -0.15, 0.45))
    if k == 1:   # rising cut: low left, up across to high right
        seq = [ready,
               dict(left_seal, hand_r=(2.6, -1.6, 14.2), blade=(0.25, -0.7, -0.7), twist=-24),
               dict(left_seal, hand_r=(7.4, 1.0, 19.6), blade=(0.7, 0.55, 0.45), twist=-2, lean=8),
               dict(left_seal, hand_r=(4.2, 5.4, 27.0), blade=(-0.1, 0.6, 0.8), twist=18, lean=2),
               dict(left_seal, hand_r=(4.2, 3.8, 20.5), blade=(0.6, 0.3, 0.7), twist=6),
               ready]
    elif k == 2:   # return cut: from the right, level across the front to the left
        seq = [ready,
               dict(left_seal, hand_r=(1.8, 6.2, 21.6), blade=(-0.6, 0.75, 0.15), twist=30),
               dict(left_seal, hand_r=(8.0, 1.2, 20.6), blade=(0.97, 0.12, 0.08), twist=0, lean=8),
               dict(left_seal, hand_r=(4.4, -3.6, 20.4), blade=(0.1, -0.97, 0.1), twist=-30, lean=4),
               dict(left_seal, hand_r=(3.8, 1.2, 18.4), blade=(0.8, 0.0, 0.55), twist=-8),
               ready]
    else:   # heavy descending cut: raised over the head, chopped down in front
        seq = [ready,
               dict(left_seal, hand_r=(0.6, 2.4, 32.5), blade=(-0.55, 0.1, 0.8), lean=-8, elbow_r=(0.0, 1.0, -0.3)),
               dict(left_seal, hand_r=(-0.4, 2.0, 33.5), blade=(-0.92, 0.05, 0.3), lean=-12, elbow_r=(0.0, 1.0, -0.2)),
               dict(left_seal, hand_r=(8.6, 1.0, 22.0), blade=(0.92, 0.0, -0.3), lean=15, **feet(3.4, -1.8, 2.0, 2.5)),
               dict(left_seal, hand_r=(6.8, 1.2, 15.6), blade=(0.55, 0.0, -0.8), lean=19, pelvis=(0.6, 0.0, 12.4),
                    **feet(3.4, -1.8, 2.0, 2.5)),
               ready]
    hit = 3 if k == 3 else 2
    out = []
    for j, s in enumerate(seq):
        d = dict(st)
        s = dict(s)
        blade = s.pop("blade")
        d.update(s)
        d["grip_r"] = "fist"
        d["drag"] = (0.3 if j in (2, 3) else 0.05, 0.0, 0.0)
        # the cut's smear on its hit frame and the one after, from the blade's last place
        smear = seq[j - 1]["blade"] if j in (hit, hit + 1) else None
        d["weapon"] = W(blade=blade, pole={"dir": blade, "butt": 14.0}, smear_from=smear)
        out.append(pose(**d))
    return out[i]


def _thrust(k, i):
    st = stance(2.2, -1.8)
    ready = {"hand_r": (3.4, 2.0, 16.8), "hand_l": (0.4, 1.2, 16.2), "elbow_l": (-0.6, -1.0, -0.4)}
    if k == 1:   # straight thrust
        seq = [ready, dict(ready, hand_r=(0.8, 2.5, 17.0), hand_l=(-1.8, 1.4, 16.4), lean=-4),
               dict(hand_r=(10.0, 1.2, 18.4), hand_l=(3.2, 0.9, 17.6), lean=12, **feet(3.8, -2.2, 2.0, 2.5)),
               dict(hand_r=(7.0, 1.5, 17.8), hand_l=(1.4, 1.0, 17.0), lean=6), ready]
        blade = [(1.0, 0.0, 0.08)] * 5
    elif k == 2:   # low thrust
        low = dict(pelvis=(0.3, 0.0, 12.0))
        seq = [ready, dict(ready, hand_r=(0.6, 2.6, 15.8), hand_l=(-1.6, 1.4, 14.6), lean=4, **low),
               dict(hand_r=(9.8, 1.0, 12.8), hand_l=(3.0, 0.8, 14.0), lean=22, **low, **feet(3.6, -2.2, 2.1, 2.5)),
               dict(hand_r=(7.0, 1.4, 14.0), hand_l=(1.4, 1.0, 14.8), lean=12, **low), ready]
        blade = [(1.0, 0.0, 0.08), (1.0, 0.0, -0.1), (1.0, 0.0, -0.35), (1.0, 0.0, -0.25), (1.0, 0.0, 0.08)]
    else:   # high lunging thrust
        seq = [ready, dict(hand_r=(0.2, 2.6, 19.4), hand_l=(-1.2, 1.4, 17.0), pelvis=(0.0, 0.0, 12.2), lean=-6),
               dict(hand_r=(12.2, 0.8, 25.0), hand_l=(5.0, 0.6, 21.4), pelvis=(2.4, 0.0, 12.4), lean=10,
                    **feet(6.4, -2.2, 2.0, 2.5)),
               dict(hand_r=(9.0, 1.2, 22.4), hand_l=(3.4, 0.8, 19.6), pelvis=(1.6, 0.0, 12.8), lean=6,
                    **feet(5.2, -2.0, 2.0, 2.5)),
               ready]
        blade = [(1.0, 0.0, 0.08), (1.0, 0.0, 0.2), (0.9, 0.0, 0.35), (0.92, 0.0, 0.3), (1.0, 0.0, 0.08)]
    out = []
    for j, s in enumerate(seq):
        d = dict(st)
        d.update(s)
        d["grip_r"] = "fist"
        d["grip_l"] = "fist"
        d["drag"] = (0.5 if j == 2 else 0.05, 0.0, 0.0)
        d["weapon"] = W(blade=blade[j], pole={"two_hand": True, "behind": 6.5})
        out.append(pose(**d))
    return out[i]


def _cast(i):
    seal = {"grip_l": "seal", "grip_r": "seal"}
    seq = [
        dict(hand_l=(3.4, -0.5, 20.5), hand_r=(3.4, 0.5, 20.5), elbow_l=(-0.2, -1.0, -0.8), elbow_r=(-0.2, 1.0, -0.8)),
        dict(hand_l=(3.8, -0.5, 24.2), hand_r=(3.8, 0.5, 24.2), elbow_l=(-0.2, -1.0, -0.8), elbow_r=(-0.2, 1.0, -0.8),
             head_pitch=6, drag=(0.0, 0.0, 0.6)),
        dict(hand_l=(8.2, -1.3, 21.6), hand_r=(8.2, 1.3, 21.6), lean=8, **feet(1.8, -0.8, 2.2, 2.4), drag=(-0.6, 0.0, 0.8)),
        dict(hand_l=(7.4, -1.4, 21.2), hand_r=(7.4, 1.4, 21.2), lean=6, **feet(1.8, -0.8, 2.2, 2.4), drag=(-0.4, 0.0, 0.5)),
        dict(hand_l=(3.0, -3.0, 17.0), hand_r=(3.0, 3.0, 17.0)),
    ]
    d = dict(seq[i])
    d.update(seal)
    d["weapon"] = W(blade=(-0.45, 0.55, -0.7), pole={"dir": (0.3, 0.12, 1.0), "butt": 13.0})
    return pose(**d)


def _guard(i):
    b = [0.0, -0.15][i]
    return pose(pelvis=(0.0, 0.0, 12.8 + b), lean=6, **stance(1.8, -1.4),
                **guard_hands(hand_r=(4.6, 1.8, 22.4 + b), hand_l=(4.0, -1.7, 21.6 + b), elbow_l=(-0.2, -1.0, -1.0),
                              elbow_r=(-0.2, 1.0, -1.0)),
                drag=(0.0, 0.0, 0.0), weapon=W(blade=(0.3, -0.65, 0.72), pole={"two_hand": True, "behind": 18.0}))


def _plunge(i):
    return [
        pose(pelvis=(0.0, 0.0, 14.0), **feet(1.4, 0.6, 2.2, 2.2, 5.0, 6.0), knee_l=(1, -0.3, 0.2), knee_r=(1, 0.3, 0.2),
             toe_l=25, toe_r=25, hand_l=(1.2, -1.4, 32.5), hand_r=(1.2, 1.4, 33.0), elbow_l=(0, -1, 0), elbow_r=(0, 1, 0),
             grip_l="fist", grip_r="fist", drag=(0.0, 0.0, -0.6),
             weapon=W(blade=(0.2, 0.0, -1.0), pole={"dir": (0.2, 0.0, -1.0), "butt": 9.0})),
        pose(pelvis=(0.5, 0.0, 13.2), lean=18, tip=14, **feet(-1.2, -2.0, 2.2, 2.2, 3.2, 4.4), toe_l=30, toe_r=30,
             hand_l=(6.0, -1.1, 15.0), hand_r=(6.2, 1.1, 15.4), grip_l="fist", grip_r="fist", drag=(-0.4, 0.0, 0.7),
             weapon=W(blade=(0.35, 0.0, -1.0), pole={"dir": (0.35, 0.0, -1.0), "butt": 9.0})),
        pose(pelvis=(0.8, 0.0, 10.4), lean=26, **feet(1.4, -1.6, 2.6, 2.6), hand_l=(6.0, -1.0, 9.6),
             hand_r=(6.2, 1.0, 9.8), grip_l="fist", grip_r="fist", drag=(0.0, 0.0, -0.4),
             weapon=W(blade=(0.25, 0.0, -1.0), pole={"dir": (0.25, 0.0, -1.0), "butt": 9.0})),
    ][i]


def _meditate(i):
    b = [0.0, 0.1, 0.2, 0.1][i]
    return pose(pelvis=(-0.4, 0.0, 4.2 + b), lean=2, foot_l=(2.6, 1.4, 1.1), foot_r=(2.2, -1.6, 2.1),
                knee_l=(0.4, -1.0, 0.3), knee_r=(0.4, 1.0, 0.3), foot_yaw_l=60, foot_yaw_r=-60,
                hand_l=(3.8, -4.4, 6.2 + b), hand_r=(3.8, 4.4, 6.2 + b), elbow_l=(-0.6, -1.0, 0.0), elbow_r=(-0.6, 1.0, 0.0),
                grip_l="seal", grip_r="seal", eyes="shut", drag=(0.0, [0.0, 0.05, 0.0, -0.05][i], 0.0),
                weapon=W(laid={"at": (5.0, 7.5, 0.7), "dir": (0.15, -1.0, 0.0)}))


# name: (frames, fps, loop, hit frame or None, label, pose function, facing lock)
CATALOG = {
    "idle": (4, 4.0, True, None, "Idle", _idle, None),
    "walk": (8, 10.0, True, None, "Walk", _walk, None),
    "run": (8, 14.0, True, None, "Run", _run, None),
    "jump": (5, 10.0, False, None, "Jump (takeoff, rise, apex, fall, land)", _jump, None),
    "dash": (4, 16.0, False, None, "Dash", _dash, None),
    "dodge": (4, 14.0, False, None, "Dodge (back-step)", _dodge, None),
    "hurt": (2, 10.0, False, None, "Hurt", _hurt, None),
    "knockdown": (5, 10.0, False, None, "Knock-down / defeat", _knockdown, None),
    "punch_1": (5, 14.0, False, 2, "Lead jab", lambda i: _punch(1, i), None),
    "punch_2": (5, 13.0, False, 2, "Rear cross", lambda i: _punch(2, i), None),
    "punch_3": (5, 11.0, False, 2, "Rising uppercut", lambda i: _punch(3, i), None),
    "swing_1": (6, 14.0, False, 2, "Rising cut", lambda i: _swing(1, i), None),
    "swing_2": (6, 13.0, False, 2, "Return cut", lambda i: _swing(2, i), None),
    "swing_3": (6, 11.0, False, 3, "Heavy descending cut", lambda i: _swing(3, i), None),
    "thrust_1": (5, 14.0, False, 2, "Straight thrust", lambda i: _thrust(1, i), None),
    "thrust_2": (5, 13.0, False, 2, "Low thrust", lambda i: _thrust(2, i), None),
    "thrust_3": (5, 11.0, False, 2, "High lunging thrust", lambda i: _thrust(3, i), None),
    "cast": (5, 12.0, False, 2, "Technique cast (hand seal)", _cast, None),
    "guard": (2, 4.0, True, None, "Guard (held)", _guard, None),
    "plunge": (3, 12.0, False, 2, "Plunge (drag-down in the air)", _plunge, None),
    "meditate": (4, 3.0, True, None, "Meditate", _meditate, "s"),
}

# Side-view action names Combat can still name (a technique's `action`, the old single-strike families): each plays a
# drawn top-down action, explicitly.
ALIASES = {"attack": "thrust_1", "swing": "swing_1", "punch": "punch_2", "bow": "cast", "meditate_burst": "cast"}


def poses(name: str) -> list:
    n = CATALOG[name][0]
    fn = CATALOG[name][5]
    return [fn(i) for i in range(n)]
