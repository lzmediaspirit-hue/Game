"""The top-down action catalog: every animation the figure has, frame by frame, as poses of the unclothed body
(AGENTS.md rule 4). Every layer is cast from these same poses (rule 2), in every drawn facing (S, SE, E, NE, N; the
west facings mirror). Meditation faces the camera only (redesign plan §1.4): its other facings redirect to S.

Poses are in the figure's own frame (skeleton.py): f forward, r the character's right, u up. The weapon lines:
`blade` is where the jian's and the short blade's point goes, `pole` the spear's line (`two_hand` runs it through both
hands), `bow` how the bow is held (kinds/bow.py: slung on the back unless a pose puts it in a hand). The combo strikes
follow the side view's three families (weapon_families.json): punch_1-3 for fists and gauntlets (lead jab, rear cross,
rising uppercut), swing_1-3 for the jian (rising cut, return cut, heavy descending cut), thrust_1-3 for the spear, the
staff and the short blade (straight, low, high lunging thrust).

The combat poses beyond the combos (decision 38, combat_feel.json): the charged finisher's held wind-up, the dash attack
of the cutting and palm families, a blow in the air, the parry's deflection; and each family's own (OWN): the heavy
sabre's two-handed cuts, the bow's draw and release, the flute played at the lips, the bell rung on both sides, the fan
thrown, the brush writing. The story's gestures (decision 39, the staged scenes): the salute, a kneel, pointing, a
startled step back. Every layer is drawn in every one of them, a family's own included: the other weapons are held as
the pose's lines say.
"""
from __future__ import annotations

import math

from .skeleton import pose

# idle / walk carriage of each weapon line
BLADE_IDLE = (0.7, 0.42, -0.58)
POLE_IDLE = {"dir": (0.14, 0.24, 1.0), "butt": 12.6}


def W(blade=None, pole=None, flat=(0.0, 1.0, 0.0), laid=None, smear_from=None, bow=None, **own):
    """The weapon lines of a pose. `bow` is how the bow (kinds/bow.py) is held, None for its carry in the left hand;
    `own` holds a family's own keys for this pose (the flute's `note`), which the other weapons ignore."""
    d = {"blade": blade or BLADE_IDLE, "pole": pole or POLE_IDLE, "flat": flat, "laid": laid, "smear_from": smear_from,
         "bow": bow}
    d.update(own)
    return d


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


SEAL_L = {"hand_l": (1.8, -4.4, 22.0), "elbow_l": (-0.5, -1.0, -0.6), "grip_l": "seal"}   # the sword-hand seal
GUARD_BLADE = (0.3, -0.65, 0.72)


def _unit(v):
    n = math.sqrt(sum(x * x for x in v))
    return tuple(x / n for x in v)


def _bow_draw(i):
    """The bow's shot (plan §1.4: draw, hold, release, 7 frames): side-on to the target, the bow arm straight along the
    shot, the string drawn to the chin and loosed, the drawing hand flying back past the ear."""
    side = dict(pelvis=(-0.2, 0.0, 13.2), hip_yaw=30.0, twist=35.0, head_yaw=-58.0, foot_yaw_l=4.0, foot_yaw_r=30.0,
                **feet(1.4, -1.4, 2.4, 2.8), elbow_l=(0.0, -1.0, -0.4), elbow_r=(0.0, 1.0, 0.3), grip_l="fist",
                grip_r="fist")
    aim = (13.4, -1.6, 22.8)                 # the bow arm straight along the shot
    CANT = {"dir": (0.05, -0.6, 1.0)}       # the bow canted out to the left, clear of the face
    seq = [
        # nock: the bow raised before the body, the arrow set on the string
        dict(twist=24.0, head_yaw=-44.0, hand_l=(8.2, -2.2, 20.6), hand_r=(5.2, 0.4, 20.4), bow=dict(CANT, draw="r", arrow=True)),
        # draw: the bow arm out along the shot, the string half back
        dict(hand_l=aim, hand_r=(7.4, 0.2, 22.6), bow=dict(CANT, draw="r", arrow=True)),
        # full draw: the string at the chin
        dict(hand_l=aim, hand_r=(2.6, 1.8, 23.2), lean=-2.0, bow=dict(CANT, draw="r", arrow=True), drag=(-0.2, 0.0, 0.0)),
        # hold: settled on the anchor
        dict(hand_l=aim, hand_r=(2.4, 1.9, 23.1), lean=-2.0, bow=dict(CANT, draw="r", arrow=True), drag=(-0.1, 0.05, 0.0)),
        # release: the string snaps back, the hand flies open past the ear
        dict(hand_l=aim, hand_r=(-1.2, 3.4, 24.6), grip_r="open", lean=-3.0, bow=dict(CANT, loosed=True, back=(1.0, -0.2, 0.0)), drag=(0.6, 0.0, 0.2)),
        # follow-through: the bow arm held on the line
        dict(hand_l=aim, hand_r=(-1.8, 3.8, 23.2), grip_r="open", lean=-2.0, bow=dict(CANT, back=(1.0, -0.2, 0.0)), drag=(0.3, 0.0, 0.1)),
        # recover: the bow lowered
        dict(twist=20.0, head_yaw=-30.0, hip_yaw=18.0, hand_l=(6.4, -3.0, 18.0), hand_r=(1.2, 5.2, 15.4), grip_r="relaxed",
             bow={"dir": (0.35, -0.25, 1.0)}),
    ]
    d = dict(side)
    s = dict(seq[i])
    bow = s.pop("bow")
    d.update(s)
    d["weapon"] = W(blade=(-0.3, 0.5, -0.8), pole={"dir": (0.2, 0.3, 1.0), "butt": 13.0}, bow=bow)
    return pose(**d)


def _flute_play(i):
    """The flute played (its note, and the held melody: frames 1-4 loop): a transverse dizi to the right of the mouth,
    the left hand crossing to its holes, the head tilted to it; the note leaves on frame 2."""
    d_fl = _unit((0.08, -1.0, 0.16))         # the tube's line from the right hand toward the mouth
    base = dict(twist=15.0, head_yaw=8.0, head_roll=-6.0, **feet(0.4, -0.3, 2.3, 2.3), foot_yaw_r=14.0,
                elbow_l=(-0.2, -1.0, -0.8), elbow_r=(-0.2, 1.0, -0.6), grip_l="relaxed", grip_r="relaxed")
    play_r, play_l = (4.8, 7.6, 26.2), (5.2, 1.4, 27.1)
    seq = [
        dict(hand_r=(4.2, 7.0, 21.5), hand_l=(4.2, 1.6, 22.4), head_roll=-3.0, blade=_unit((0.2, -1.0, 0.45))),
        dict(hand_r=play_r, hand_l=play_l, lean=-3.0, drag=(0.0, 0.0, 0.0)),
        dict(hand_r=play_r, hand_l=play_l, lean=3.0, drag=(-0.4, 0.0, 0.2)),
        dict(hand_r=play_r, hand_l=play_l, lean=1.0, roll=3.0, drag=(-0.2, -0.2, 0.1)),
        dict(hand_r=play_r, hand_l=play_l, lean=-1.0, roll=-3.0, drag=(0.0, 0.2, 0.0)),
        dict(hand_r=(4.4, 7.2, 23.4), hand_l=(4.6, 1.8, 24.2), head_roll=-4.0, blade=_unit((0.12, -1.0, 0.3))),
    ]
    d = dict(base)
    s = dict(seq[i])
    blade = s.pop("blade", d_fl)
    d.update(s)
    d["weapon"] = W(blade=blade, pole={"dir": (0.2, 0.25, 1.0), "butt": 13.0}, note=(1.0, 0.25, 0.1))
    return pose(**d)


def _charge_hold(i):
    """The dragged finisher's held wind-up (a loop): low and coiled, the weight on the back foot, the weapon drawn back
    behind the hip, the sword-hand seal forward over the lead foot; the second frame trembles lower."""
    b = [0.0, -0.3][i]
    return pose(pelvis=(-0.5, 0.0, 11.6 + b), lean=9.0, twist=28.0, hip_yaw=10.0, head_yaw=-24.0,
                **stance(2.8, -2.4), hand_r=(-3.0, 5.6, 15.4 + b), elbow_r=(-1.0, 0.6, -0.2), grip_r="fist",
                hand_l=(5.4, -2.0, 20.8 + b), elbow_l=(-0.2, -1.0, -0.6), grip_l="seal",
                drag=(-0.2, [0.1, -0.1][i], 0.3),
                weapon=W(blade=(-0.72, 0.25, 0.64), pole={"dir": (1.0, 0.0, 0.1), "butt": 16.0}))


def _dash_slash(i):
    """The dash attack of the cutting and palm families: the dash carried into a wide level cut across the front, from
    the right to the left, the free hand flung back; its smear on the cut."""
    seq = [
        dict(pelvis=(0.8, 0.0, 12.4), lean=26, twist=18, **feet(3.6, -4.0, 2.0, 2.2, 1.4, 3.6), toe_r=35,
             hand_r=(-2.4, 5.4, 15.8), hand_l=(-2.2, -5.0, 17.6), blade=(-0.85, 0.35, -0.3), drag=(-2.6, 0.0, 0.8)),
        dict(pelvis=(1.0, 0.0, 12.0), lean=20, twist=26, **feet(4.4, -3.6, 2.1, 2.3), foot_yaw_r=24,
             hand_r=(2.6, 6.8, 18.6), hand_l=(-2.8, -4.6, 18.6), blade=(0.15, 0.95, 0.1), drag=(-2.2, 0.0, 0.6)),
        dict(pelvis=(1.2, 0.0, 11.8), lean=16, twist=0, **feet(4.6, -3.4, 2.1, 2.4), foot_yaw_r=24,
             hand_r=(8.4, 0.6, 19.2), hand_l=(-2.0, -5.4, 19.0), blade=(0.93, -0.35, 0.08), drag=(-1.4, 0.0, 0.5)),
        dict(pelvis=(1.2, 0.0, 11.9), lean=14, twist=-34, **feet(4.6, -3.4, 2.1, 2.4), foot_yaw_r=24,
             hand_r=(4.2, -3.8, 19.6), hand_l=(-1.2, -5.8, 19.4), blade=(-0.1, -0.98, 0.12), drag=(-0.8, 0.3, 0.3)),
        dict(pelvis=(0.6, 0.0, 12.8), lean=6, twist=-6, **stance(2.4, -1.8), hand_r=(4.0, 2.4, 17.0),
             blade=(0.9, -0.1, 0.4), drag=(-0.2, 0.0, 0.0), **SEAL_L),
    ]
    s = dict(seq[i])
    blade = s.pop("blade")
    s.setdefault("grip_l", "open")
    smear = seq[i - 1]["blade"] if i in (2, 3) else None
    return pose(grip_r="fist", **s, weapon=W(blade=blade, pole={"dir": blade, "butt": 14.0}, smear_from=smear))


def _air_strike(i):
    """A blow struck in the air: knees tucked, the weapon raised over the head and cut down before the body, the legs
    kicking back with it; its smear on the cut."""
    tuck = dict(**feet(1.6, 1.0, 2.2, 2.2, 5.6, 6.4), knee_l=(1, -0.3, 0.2), knee_r=(1, 0.3, 0.2), toe_l=20, toe_r=20)
    seq = [
        dict(pelvis=(0.0, 0.0, 14.0), lean=-8, **tuck, hand_r=(0.4, 3.0, 31.0), elbow_r=(0.0, 1.0, -0.2),
             hand_l=(1.0, -6.6, 24.0), blade=(-0.6, 0.2, 0.75), drag=(0.0, 0.0, -0.6)),
        dict(pelvis=(0.0, 0.0, 14.0), lean=-2, **tuck, hand_r=(4.0, 2.6, 30.0), elbow_r=(0.0, 1.0, -0.2),
             hand_l=(0.6, -6.8, 23.0), blade=(0.3, 0.25, 0.92), drag=(-0.2, 0.0, -0.2)),
        dict(pelvis=(0.3, 0.0, 13.8), lean=16, **feet(0.4, -1.0, 2.2, 2.2, 3.4, 4.6), knee_l=(1, -0.3, 0.1),
             knee_r=(1, 0.3, 0.1), toe_l=30, toe_r=35, hand_r=(8.2, 1.2, 21.0), hand_l=(-0.6, -6.6, 22.0),
             blade=(0.85, 0.1, -0.5), drag=(-0.6, 0.0, 0.6)),
        dict(pelvis=(0.4, 0.0, 13.6), lean=20, **feet(-0.4, -1.6, 2.2, 2.2, 3.0, 4.0), toe_l=35, toe_r=40,
             hand_r=(6.8, 1.0, 16.4), hand_l=(-1.2, -6.4, 21.0), blade=(0.4, 0.0, -0.9), drag=(-0.4, 0.0, 0.8)),
    ]
    s = dict(seq[i])
    blade = s.pop("blade")
    smear = seq[i - 1]["blade"] if i in (2, 3) else None
    return pose(grip_r="fist", grip_l="seal", **s, weapon=W(blade=blade, pole={"dir": blade, "butt": 14.0},
                                                           smear_from=smear))


def _parry_deflect(i):
    """The instant a guard parries: from the guard the weapon snaps out and up to turn the blow aside, the body giving
    back a step's weight, then settles toward the guard again; a short smear on the turn."""
    g = dict(pelvis=(0.0, 0.0, 12.8), lean=6, **stance(1.8, -1.4),
             **guard_hands(hand_r=(4.6, 1.8, 22.4), hand_l=(4.0, -1.7, 21.6), elbow_l=(-0.2, -1.0, -1.0),
                           elbow_r=(-0.2, 1.0, -1.0)))
    seq = [
        dict(blade=GUARD_BLADE),
        dict(pelvis=(-0.6, 0.0, 12.9), lean=-6, twist=12, hand_r=(5.6, 3.8, 24.0), hand_l=(3.4, -2.2, 21.0),
             blade=(0.3, 0.82, 0.48), drag=(0.8, 0.0, 0.3)),
        dict(pelvis=(-0.3, 0.0, 12.8), lean=0, twist=6, hand_r=(4.9, 2.4, 22.8), blade=(0.35, -0.1, 0.93),
             drag=(0.4, 0.0, 0.1)),
    ]
    d = dict(g)
    s = dict(seq[i])
    blade = s.pop("blade")
    d.update(s)
    return pose(**d, weapon=W(blade=blade, pole={"two_hand": True, "behind": 18.0},
                              smear_from=GUARD_BLADE if i == 1 else None))


def _two_hand(k, i):
    """The heavy sabre's cuts, two-handed: both fists on the long grip (the left under the right), a wide stance,
    the whole body behind each blow. 1: a diagonal cut from over the right shoulder down across to the left; 2: a
    level sweep back from the left to the right; 3: a leaping chop from high over the head. Smears on the cuts."""
    st = stance(2.2, -2.0)
    ready = dict(hand_r=(4.4, 1.2, 17.6), blade=(0.85, 0.05, 0.5))
    if k == 1:
        seq = [ready,
               dict(hand_r=(1.0, 3.8, 29.0), blade=(-0.4, 0.45, 0.8), twist=20, lean=-6),
               dict(hand_r=(8.0, 0.2, 20.2), blade=(0.75, -0.45, -0.45), twist=-10, lean=12),
               dict(hand_r=(5.4, -3.2, 14.8), blade=(0.25, -0.75, -0.6), twist=-30, lean=16, pelvis=(0.4, 0.0, 12.4)),
               dict(hand_r=(4.2, 0.6, 17.0), blade=(0.85, 0.1, 0.45), twist=-8, lean=6),
               ready]
    elif k == 2:
        seq = [ready,
               dict(hand_r=(3.0, -4.0, 20.6), blade=(-0.35, -0.9, 0.2), twist=-40, lean=2),
               dict(hand_r=(8.4, 0.8, 20.2), blade=(0.97, 0.15, 0.05), twist=0, lean=8),
               dict(hand_r=(3.4, 5.4, 20.2), blade=(-0.2, 0.97, 0.1), twist=38, lean=4),
               dict(hand_r=(4.2, 1.6, 18.0), blade=(0.85, 0.2, 0.45), twist=8),
               ready]
    else:
        seq = [ready,
               dict(hand_r=(-0.2, 0.8, 34.0), blade=(-0.75, 0.05, 0.6), lean=-10, pelvis=(0.0, 0.0, 14.0),
                    **feet(1.6, -1.6, 2.1, 2.4, 2.2, 1.6)),
               dict(hand_r=(0.2, 0.6, 34.5), blade=(-0.9, 0.0, 0.2), lean=-12, pelvis=(0.4, 0.0, 14.8),
                    **feet(2.2, -1.4, 2.1, 2.4, 3.6, 3.0), toe_l=25, toe_r=25),
               dict(hand_r=(8.8, 0.4, 19.0), blade=(0.85, 0.0, -0.5), lean=18, pelvis=(1.2, 0.0, 11.8),
                    **feet(4.0, -2.0, 2.0, 2.5)),
               dict(hand_r=(7.2, 0.4, 14.2), blade=(0.5, 0.0, -0.85), lean=22, pelvis=(1.0, 0.0, 11.2),
                    **feet(4.0, -2.0, 2.0, 2.5)),
               ready]
    hit = 3 if k == 3 else 2
    out = []
    for j, s in enumerate(seq):
        d = dict(st)
        s = dict(s)
        blade = _unit(s.pop("blade"))
        d.update(s)
        hr = d["hand_r"]
        d["hand_l"] = tuple(hr[n] - blade[n] * 2.2 for n in range(3))       # the left fist under the right on the grip
        d["elbow_l"] = (-0.4, -1.0, -0.6)
        d["elbow_r"] = (-0.4, 1.0, -0.4)
        d["grip_r"] = d["grip_l"] = "fist"
        d["drag"] = (0.35 if j in (hit, hit + 1) else 0.05, 0.0, 0.0)
        smear = _unit(seq[j - 1]["blade"]) if j in (hit, hit + 1) else None
        d["weapon"] = W(blade=blade, pole={"two_hand": True, "behind": 8.0}, smear_from=smear)
        out.append(pose(**d))
    return out[i]


def _bell_toll(i):
    """The bell rung out on both sides: drawn across to the left shoulder, flung out to the right at arm's length (the
    peal, frame 2) and swung back across to the left to ring again (frame 3), the sword-hand seal before the chest."""
    seq = [
        dict(hand_r=(4.2, 2.6, 18.6), blade=(0.75, 0.1, 0.65)),
        dict(hand_r=(2.8, -1.8, 25.0), blade=(-0.2, -0.6, 0.78), twist=-25, lean=-2),
        dict(hand_r=(4.4, 8.2, 23.2), blade=(0.25, 0.95, 0.2), twist=22, lean=4, drag=(-0.2, -0.4, 0.2)),
        dict(hand_r=(5.0, -5.6, 22.4), blade=(0.3, -0.95, 0.2), twist=-26, lean=4, drag=(-0.2, 0.4, 0.2),
             hand_l=(0.6, -5.4, 19.6)),
        dict(hand_r=(4.0, 1.6, 19.0), blade=(0.7, 0.2, 0.7), twist=-4),
        dict(hand_r=(4.2, 2.6, 18.6), blade=(0.75, 0.1, 0.65)),
    ]
    d = dict(stance(1.8, -1.6), **SEAL_L)
    s = dict(seq[i])
    blade = s.pop("blade")
    d.update(s)
    d["grip_r"] = "fist"
    return pose(**d, weapon=W(blade=blade, pole={"dir": blade, "butt": 14.0}))


def _fan_throw(i):
    """The fan's third step, which throws it: drawn back open across the body to the left, swept round to the front and
    loosed from an open hand (frame 3), which follows through and opens to catch it; the fan is in flight from the
    release on (the throw's own art draws it)."""
    seq = [
        dict(hand_r=(4.2, 2.6, 17.6), blade=(0.9, -0.15, 0.45), **SEAL_L),
        dict(hand_r=(0.6, -3.6, 17.6), blade=(-0.5, -0.8, 0.2), twist=-40, lean=4, **SEAL_L),
        dict(hand_r=(6.6, -1.4, 20.0), blade=(0.9, -0.4, 0.1), twist=-10, lean=8, hand_l=(-1.0, -5.4, 19.0)),
        dict(hand_r=(8.6, 2.2, 20.6), blade=(0.95, 0.3, 0.0), twist=16, lean=10, grip_r="open",
             hand_l=(-1.6, -5.6, 19.6), drag=(-0.6, 0.0, 0.3)),
        dict(hand_r=(5.4, 5.6, 19.6), blade=(0.3, 0.95, -0.1), twist=26, lean=6, grip_r="open",
             hand_l=(-1.0, -5.6, 18.6), drag=(-0.3, 0.0, 0.1)),
        dict(hand_r=(4.6, 2.2, 19.2), blade=(0.85, 0.2, 0.45), twist=6, grip_r="open", **SEAL_L),
    ]
    d = dict(stance(1.8, -1.6))
    s = dict(seq[i])
    blade = s.pop("blade")
    d["grip_r"] = "fist"
    d.update(s)
    d.setdefault("grip_l", "open")
    smear = seq[i - 1]["blade"] if i == 2 else None
    return pose(**d, weapon=W(blade=blade, pole={"dir": blade, "butt": 14.0}, smear_from=smear))


def _brush_write(i):
    """The brush writing its strokes in the air, as on a scroll before the body: the left hand holding back the right
    sleeve, the tuft swept through a level stroke, a falling stroke (frame 2) and a pressed sweep to the right, then
    lifted; each stroke leaves its ink (the brush set's smear)."""
    seq = [
        dict(hand_r=(5.0, 1.8, 24.0), blade=(0.6, -0.35, 0.72)),
        dict(hand_r=(5.4, 2.6, 24.2), blade=(0.6, 0.55, 0.58)),
        dict(hand_r=(6.4, 1.6, 21.6), blade=(0.65, 0.1, -0.75), lean=6),
        dict(hand_r=(6.0, 3.0, 20.6), blade=(0.45, 0.8, -0.4), lean=6, twist=8),
        dict(hand_r=(5.0, 2.0, 23.0), blade=(0.7, 0.2, 0.68)),
        dict(hand_r=(4.4, 2.4, 19.2), blade=(0.75, 0.1, 0.65)),
    ]
    d = dict(stance(1.6, -1.4), hand_l=(3.0, 1.4, 19.2), elbow_l=(-0.4, -1.0, -0.8), grip_l="relaxed", grip_r="fist")
    s = dict(seq[i])
    blade = s.pop("blade")
    d.update(s)
    smear = seq[i - 1]["blade"] if i in (1, 2, 3) else None
    return pose(**d, drag=(-0.2 if i in (1, 2, 3) else 0.0, 0.0, 0.0),
                weapon=W(blade=blade, pole={"dir": blade, "butt": 14.0}, smear_from=smear))


# The story's gestures (decision 39, the staged scenes; NPC figures play them too). Each ends in its held pose.
def _salute(i):
    """The wuxia salute: the right fist into the left palm before the chest, elbows rounded out, then a bow over it,
    heels together. A weapon stays in the right fist, reversed up and out behind the forearm, clear of the face; the
    bow stays slung on the back."""
    seq = [
        dict(hand_r=(3.0, 1.8, 17.6), hand_l=(3.0, -1.8, 18.0), grip_l="open"),
        dict(hand_r=(4.6, 0.35, 21.2), hand_l=(4.9, -0.6, 21.6), grip_l="open"),
        dict(hand_r=(5.2, 0.35, 20.4), hand_l=(5.5, -0.6, 20.8), grip_l="open", lean=14, head_pitch=10),
    ]
    d = dict(**feet(0.0, 0.0, 1.5, 1.5), foot_yaw_l=-14.0, foot_yaw_r=14.0, elbow_l=(-0.2, -1.0, -0.2),
             elbow_r=(-0.2, 1.0, -0.2), grip_r="fist")
    d.update(seq[i])
    return pose(**d, drag=(0.0, 0.0, 0.0), weapon=W(blade=(-0.3, 0.55, -0.78), pole={"dir": (0.15, 1.0, 0.3), "butt": 16.0}))


def _kneel(i):
    """Down on the right knee: the right foot steps back and the body lowers onto it, the left knee up with the left
    forearm on it, the right fist on the thigh, the head bowed. A blade lies across the raised knee, a pole stands
    upright by the right hand, the bow is slung on the back."""
    seq = [
        dict(pelvis=(0.3, 0.0, 12.2), lean=6, **feet(1.2, -2.6, 2.3, 2.3), hand_l=(1.6, -5.6, 13.6),
             hand_r=(0.0, 5.8, 13.4)),
        dict(pelvis=(0.4, 0.0, 9.8), lean=8, foot_l=(3.0, -2.3, 1.3), foot_r=(-3.2, 2.2, 1.6), toe_r=45,
             knee_l=(1.0, -0.2, 0.6), knee_r=(1.0, 0.2, -0.6), hand_l=(3.6, -3.6, 10.6), hand_r=(1.0, 5.0, 9.8),
             head_pitch=6),
        dict(pelvis=(0.3, 0.0, 7.9), lean=6, foot_l=(3.2, -2.2, 1.3), foot_r=(-4.0, 2.2, 1.25), toe_r=70,
             knee_l=(1.0, -0.2, 0.6), knee_r=(1.0, 0.2, -1.0), hand_l=(4.8, -2.6, 10.0), hand_r=(1.4, 4.6, 7.6),
             head_pitch=14),
    ]
    d = dict(elbow_l=(-0.5, -1.0, 0.0), elbow_r=(-0.8, 1.0, 0.0), grip_r="fist", grip_l="relaxed", foot_yaw_l=-4.0,
             foot_yaw_r=10.0)
    d.update(seq[i])
    return pose(**d, drag=(0.0, 0.0, [0.0, -0.3, 0.0][i]),
                weapon=W(blade=[BLADE_IDLE, (0.45, -0.6, -0.4), (0.45, -0.88, 0.05)][i],
                         pole=[POLE_IDLE, {"dir": (0.1, 0.15, 1.0), "butt": 9.0}, {"dir": (0.05, 0.12, 1.0), "butt": 7.2}][i]))


def _point(i):
    """Pointing the way (or at what the line is about) with the left hand's sword fingers, the arm straight, the body
    turned to it; the right hand stays at the side with its weapon."""
    seq = [
        dict(hand_l=(4.0, -4.6, 19.0), twist=6.0),
        dict(hand_l=(10.2, -4.8, 25.4), twist=14.0, head_yaw=-14.0, head_pitch=-4.0),
    ]
    d = dict(**feet(0.8, -0.6, 2.2, 2.3), grip_l="seal", elbow_l=(0.0, -1.0, -0.4), hand_r=(0.2, 5.9, 13.8))
    d.update(seq[i])
    return pose(**d, drag=(0.0, 0.0, 0.0), weapon=W())


def _startle(i):
    """Startled, a step back: the body jolts up and back, the right foot steps back and the hands come up open before
    the chest, holding there; a weapon comes up across the body."""
    seq = [
        dict(pelvis=(-0.6, 0.0, 13.9), lean=-10, head_pitch=-10, hand_l=(2.4, -4.6, 19.0), hand_r=(2.4, 4.6, 19.0),
             drag=(1.0, 0.0, 0.6)),
        dict(pelvis=(-1.2, 0.0, 13.0), lean=-8, head_pitch=-6, **feet(0.8, -3.0, 2.3, 2.5), foot_yaw_r=16,
             hand_l=(4.0, -2.0, 23.0), hand_r=(3.6, 2.4, 22.0), drag=(0.8, 0.0, 0.3)),
        dict(pelvis=(-1.0, 0.0, 12.6), lean=-4, head_pitch=-3, **feet(0.8, -3.0, 2.3, 2.5), foot_yaw_r=16,
             hand_l=(3.8, -2.2, 22.2), hand_r=(3.4, 2.6, 21.2), drag=(0.3, 0.0, 0.1)),
    ]
    d = dict(grip_l="open", grip_r="fist", elbow_l=(-0.4, -1.0, -0.8), elbow_r=(-0.4, 1.0, -0.8))
    d.update(seq[i])
    return pose(**d, weapon=W(blade=[(0.5, 0.4, 0.6), GUARD_BLADE, GUARD_BLADE][i],
                              pole={"two_hand": True, "behind": 16.0}))


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
    "charge_hold": (2, 6.0, True, None, "Charged finisher (held wind-up)", _charge_hold, None),
    "dash_slash": (5, 16.0, False, 2, "Dash attack (level cut)", _dash_slash, None),
    "air_strike": (4, 14.0, False, 2, "Air strike", _air_strike, None),
    "parry_deflect": (3, 12.0, False, 1, "Parry (deflect)", _parry_deflect, None),
    "two_hand_swing_1": (6, 12.0, False, 2, "Two-handed diagonal cut", lambda i: _two_hand(1, i), None),
    "two_hand_swing_2": (6, 11.0, False, 2, "Two-handed level sweep", lambda i: _two_hand(2, i), None),
    "two_hand_swing_3": (6, 10.0, False, 3, "Two-handed leaping chop", lambda i: _two_hand(3, i), None),
    "bow_draw": (7, 12.0, False, 4, "Bow (draw, hold, release)", _bow_draw, None),
    "flute_play": (6, 10.0, False, 2, "Flute (note; the melody loops frames 1-4)", _flute_play, None),
    "bell_toll": (6, 12.0, False, 2, "Bell toll (rung on both sides)", _bell_toll, None),
    "fan_throw": (6, 12.0, False, 3, "Fan throw", _fan_throw, None),
    "brush_write": (6, 12.0, False, 2, "Brush writing (three strokes)", _brush_write, None),
    "meditate": (4, 3.0, True, None, "Meditate", _meditate, "s"),
    "salute": (3, 6.0, False, None, "Salute (fist in palm, bow)", _salute, None),
    "kneel": (3, 6.0, False, None, "Kneel (on one knee)", _kneel, None),
    "point": (2, 6.0, False, None, "Point (sword fingers)", _point, None),
    "startle": (3, 10.0, False, None, "Startle (a step back)", _startle, None),
}

# The blows among the actions beyond the three combo families (punch, swing, thrust): their hit frame is a weapon's
# blow, so a sounding weapon (kinds/sound.py) rings on it as on a combo step.
BLOWS = ["dash_slash", "air_strike", "two_hand_swing_1", "two_hand_swing_2", "two_hand_swing_3", "flute_play",
         "bell_toll"]

# The actions that are one weapon family's own (weapon_families.json ids): the game plays them only with that family
# (combat_feel.json `poses`). Every other weapon is still drawn in them, held as the pose's lines say, so no layer is
# ever missing an action (AGENTS.md rule 2).
OWN = {"two_hand_swing_1": "heavy_sabre", "two_hand_swing_2": "heavy_sabre", "two_hand_swing_3": "heavy_sabre",
       "bow_draw": "bow", "flute_play": "flute", "bell_toll": "bell", "fan_throw": "fan", "brush_write": "brush"}

# Side-view action names Combat can still name (a technique's `action`, the old single-strike families): each plays a
# drawn top-down action, explicitly. `attack` is the flute's (its combo and techniques), `bow` the bow's.
ALIASES = {"attack": "flute_play", "swing": "swing_1", "punch": "punch_2", "bow": "bow_draw", "meditate_burst": "cast"}
# The aliases that only stand in for an action not drawn yet. The full set has none (decision 37).
STAND_INS: list = []


def poses(name: str) -> list:
    n = CATALOG[name][0]
    fn = CATALOG[name][5]
    return [fn(i) for i in range(n)]
