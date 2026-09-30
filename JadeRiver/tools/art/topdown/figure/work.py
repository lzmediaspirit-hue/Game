"""The work and place poses (decision 44): what the villagers do in their work loops (data/topdown/life.json, built by
tools/data/topdown_life.py) and what the player does at a place (data/places.json), drawn on the unclothed body first
(AGENTS.md rule 4) like every other action, in every drawn facing.

Work actions put the weapon away (its layer is explicitly hidden: `STOW`) and hold a tool (figure/kinds/tool.py, the
`tool` layer set): each pose says where its tool goes in `W(tools={...})`, from the hands the pose puts on it, so the
tool is in the hands on every frame. The tool layer draws nothing in the other actions (explicit hidden entries), save
where a tool is carried: the broom, the rod, the axe and the herb basket in the idle and walk poses (actions.py).

  work_sweep   a two-handed broom sweep: drawn back to the right, pushed across the front (the key pose), followed
               through to the left, lifted and carried back
  work_carry   walking with a shoulder pole on the right shoulder, both hands steadying it, its baskets bobbing a beat
               behind the step; the washing's basket rides the same shoulder in it
  work_rod     holding a rod out over the water, the tip nodding, the line to its float
  work_cast    casting the rod: lifted back over the shoulder, flicked forward (the key pose), the line flying out
  work_hang    reaching up to hang washing: a cloth taken up, shaken out, lifted and laid over a line above the head
  work_stir    stirring a pot held on the left arm with a ladle, round the pot
  work_grind   a pestle in a mortar, kneeling: lifted, driven down (the contact), ground round
  work_chop    an axe's overhead chop: raised, over the head (anticipation), down into the block (the contact),
               wrenched free, back to the ready
  work_hammer  a one-handed hammer at an anvil, the tongs holding the hot bar: raised, the blow (the contact), the
               rebound
  work_pick    crouching to pick herbs into a basket on the left arm
  work_mend    mending a net, seated, the netting needle drawn through and pulled tight
  open         opening a lid, a letter box or a door with the left hand (the weapon stays in the right)
  tend         crouched, the left hand working the ground or the fire (a garden bed, a furnace)
  sit          sitting down on a mat, cross-legged, hands on the knees (the weapon laid beside, as in meditation)
"""
from __future__ import annotations

import math

from .actions import BLADE_IDLE, POLE_IDLE, W, feet
from .skeleton import pose


def _unit(v):
    n = math.sqrt(sum(x * x for x in v))
    return tuple(x / n for x in v)


def _add(a, b, k=1.0):
    return tuple(x + y * k for x, y in zip(a, b))


def _sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def stow(**tools) -> dict:
    """A work pose's lines: the weapon put away, the tools drawn as said."""
    return W(stow=True, tools=tools)


# ------------------------------------------------------------------ the broom
BROOM_L = 22.0          # the top of the handle to the bristles' tips
BROOM_TOP = 1.3         # the left hand's grip below the top
BROOM_LOW = 8.0         # the right hand's grip below the top


def _broom(end, top_hint):
    """The hands on a broom whose bristles end at `end` (the figure's frame) and whose handle leans toward
    `top_hint`: (left hand, right hand)."""
    d = _unit(_sub(end, top_hint))
    top = _add(end, d, -BROOM_L)
    return _add(top, d, BROOM_TOP), _add(top, d, BROOM_LOW)


def _sweep(i):
    """Frame 0 the ready, 1 drawn back to the right (the anticipation), 2 the push across the front (the key pose, the
    bristles pressed and splayed), 3 the follow-through to the left, 4 lifted and carried back, 5 set down again."""
    seq = [
        # end on the ground, the handle's lean, twist, lean, pelvis's shift, lift of the bristles
        ((10.0, 8.0, 0.3), (1.6, -0.2, 17.2), 12.0, 12.0, 0.0, 0.0),
        ((7.4, 10.6, 0.3), (0.8, 1.2, 17.6), 28.0, 8.0, 0.4, 0.0),
        ((12.4, 1.4, 0.3), (2.4, -0.8, 16.6), 0.0, 20.0, 0.0, 0.0),
        ((10.2, -6.4, 0.3), (2.2, -2.0, 17.0), -22.0, 16.0, -0.4, 0.0),
        ((11.0, 0.6, 2.2), (1.8, 0.0, 17.6), -6.0, 12.0, -0.1, 2.0),
        ((10.2, 6.4, 0.9), (1.8, -0.2, 17.2), 8.0, 12.0, 0.1, 0.7),
    ]
    end, hint, tw, ln, shift, lift = seq[i]
    hl, hr = _broom(end, hint)
    return pose(pelvis=(0.2, shift, 12.6), lean=ln, twist=tw, hip_yaw=tw * 0.3, head_pitch=10.0,
                **feet(1.4, -0.9, 2.5, 2.6), foot_yaw_r=16.0,
                hand_l=hl, hand_r=hr, elbow_l=(-0.4, -1.0, -0.4), elbow_r=(-0.6, 1.0, -0.6),
                grip_l="fist", grip_r="fist", drag=(-0.2, [0.0, 0.3, -0.2, -0.3, 0.1, 0.2][i], 0.0),
                weapon=stow(broom={"lift": lift, "press": 1.0 if i == 2 else 0.0}))


# ------------------------------------------------------------------ the shoulder pole
def _carry(i, n=8):
    """The walk's own legs (actions._walk), the body a little stooped under the load, both hands up at the pole on the
    right shoulder; the pole bows and the baskets bob a beat behind the step."""
    ph = 2 * math.pi * i / n
    c, s = math.cos(ph), math.sin(ph)
    stride, lift = 2.5, 1.4
    fl, fr = stride * c, -stride * c
    ul = 1.3 + lift * max(0.0, -s)
    ur = 1.3 + lift * max(0.0, s)
    bob = -0.35 * math.cos(2 * ph)
    load = -0.55 * math.cos(2 * ph - 0.9)          # the baskets' bob, a beat behind the body's
    return pose(pelvis=(0.0, 0.0, 13.2 + bob), lean=6.0, roll=-3.0, hip_yaw=4 * c, twist=-5 * c,
                **feet(fl, fr, 2.1, 2.1, ul, ur), toe_l=-12 * c * (ul < 1.4), toe_r=12 * c * (ur < 1.4),
                hand_r=(4.2, 5.8, 22.4 + bob * 0.5), hand_l=(3.0, 3.4, 22.8 + bob * 0.5),
                elbow_r=(0.0, 1.0, -1.0), elbow_l=(0.0, -0.4, -1.0), grip_l="fist", grip_r="fist",
                head_roll=3.0, drag=(-0.4, 0.1 * s, 0.0),
                weapon=stow(pole={"bob": load, "bow": 0.5 + 0.3 * math.cos(2 * ph - 0.9)},
                            washing={"basket": True, "bob": load * 0.5}))


# ------------------------------------------------------------------ the rod
ROD_DIR = (0.64, 0.44, 0.63)        # held out over the water, up at about 38 degrees and off to the right
ROD_BACK = 3.3                      # the left fist's grip behind the right's, along the rod


def _rod_hands(hr, d):
    return hr, _add(hr, _unit(d), -ROD_BACK)


def _rod(i):
    """Holding the rod out over the water: both hands on the butt before the belly, the rod up at a slant, its tip
    nodding (a nibble on frame 1), the line down to its float."""
    nod = [0.0, -1.2, 0.2, 0.8][i]
    b = [0.0, -0.1, -0.2, -0.1][i]
    hr, hl = _rod_hands((4.6, 2.4, 15.8 + b), ROD_DIR)
    return pose(pelvis=(0.0, 0.0, 13.3 + b), lean=4.0, **feet(1.0, -0.6, 2.3, 2.4), foot_yaw_r=12.0,
                hand_r=hr, hand_l=hl, elbow_r=(-0.6, 1.0, -0.6), elbow_l=(-0.8, -0.4, -0.8), grip_l="fist",
                grip_r="fist", head_pitch=4.0, drag=(0.0, [0.0, 0.05, 0.0, -0.05][i], 0.0),
                weapon=stow(rod={"dir": ROD_DIR, "nod": nod,
                                 "line": {"to": (22.5, 13.0, -1.0), "sag": 0.6 + 0.2 * (i % 2)}}))


def _cast_rod(i):
    """Casting: 0 the hold, 1 the rod lifted up before the face (the line trailing), 2 back over the right shoulder
    (the anticipation), 3 flicked forward (the key pose: the rod up and out, the line flying in an arc), 4 the line
    lands, the rod following through low, 5 settled into the hold."""
    seq = [
        ((4.6, 2.4, 15.8), ROD_DIR, 0.0, 4.0, {"to": (22.5, 13.0, -1.0), "sag": 0.6}),
        ((2.6, 3.4, 21.0), (0.25, 0.35, 0.9), 10.0, -4.0, {"to": (8.0, 6.0, 8.0), "sag": 2.0}),
        ((1.2, 3.8, 24.0), (-0.45, 0.35, 0.82), 14.0, -8.0, {"to": (-10.0, 8.0, 16.0), "sag": 1.2}),
        ((5.6, 2.4, 20.0), (0.55, 0.35, 0.76), -2.0, 12.0, {"to": (22.0, 14.0, 16.0), "sag": -2.5}),
        ((6.6, 2.4, 16.4), (0.72, 0.45, 0.5), -4.0, 12.0, {"to": (24.0, 15.0, -1.0), "sag": 2.0}),
        ((5.0, 2.4, 16.0), (0.64, 0.42, 0.62), 0.0, 6.0, {"to": (23.0, 13.5, -1.0), "sag": 0.8}),
    ]
    hr, d, tw, ln, line = seq[i]
    hr, hl = _rod_hands(hr, d)
    return pose(pelvis=(0.0, 0.0, 13.3), lean=ln, twist=tw, **feet(1.2, -0.8, 2.3, 2.4), foot_yaw_r=12.0,
                hand_r=hr, hand_l=hl, elbow_r=(-0.4, 1.0, -0.8), elbow_l=(-0.6, -0.6, -0.8), grip_l="fist",
                grip_r="fist", head_pitch=[4.0, -6.0, -8.0, 2.0, 4.0, 4.0][i],
                drag=([0.0, 0.3, 0.4, -0.6, -0.4, 0.0][i], 0.0, [0.0, 0.2, 0.3, 0.2, 0.0, 0.0][i]),
                weapon=stow(rod={"dir": d, "nod": 0.0, "line": line}))


# ------------------------------------------------------------------ the washing
def _hang(i):
    """Hanging a cloth on a line above the head: 0 taken up from the basket, bent over it, 1 rising, shaken out between
    the hands, 2 lifted before the chest, 3 reached up to the line on the toes (the key pose), 4 laid over it, 5 smoothed
    down over it, the hands still up."""
    seq = [
        # pelvis, lean, the hands (l, r), the heels' lift, the cloth's hang below the hands
        ((0.4, 0.0, 12.2), 26.0, (5.6, -1.8, 10.2), (5.6, 1.8, 10.4), 0.0, 3.2),
        ((0.2, 0.0, 13.0), 8.0, (4.6, -3.6, 17.4), (4.6, 3.6, 17.4), 0.0, 7.0),
        ((0.0, 0.0, 13.3), 0.0, (4.0, -3.4, 23.0), (4.0, 3.4, 23.0), 0.0, 7.4),
        ((0.0, 0.0, 14.0), -6.0, (3.2, -3.6, 30.2), (3.2, 3.6, 30.2), 1.0, 7.6),
        ((0.0, 0.0, 14.0), -5.0, (3.8, -3.6, 29.6), (3.8, 3.6, 29.6), 1.0, 4.6),
        ((0.0, 0.0, 13.6), -3.0, (4.0, -4.0, 28.6), (4.0, 4.0, 28.6), 0.4, 4.2),
    ]
    pel, ln, hl, hr, heel, hang = seq[i]
    return pose(pelvis=pel, lean=ln, head_pitch=[14.0, 4.0, -6.0, -14.0, -12.0, -10.0][i],
                **feet(0.6, -0.4, 2.2, 2.2, 1.3 + heel, 1.3 + heel), toe_l=28.0 * heel, toe_r=28.0 * heel,
                hand_l=hl, hand_r=hr, elbow_l=(-0.2, -1.0, -0.6), elbow_r=(-0.2, 1.0, -0.6),
                grip_l="fist", grip_r="fist", drag=(0.0, 0.0, [0.0, 0.5, 0.3, 0.2, 0.0, 0.0][i]),
                weapon=stow(washing={"hang": hang, "over": i >= 4, "shake": 1.0 if i == 1 else 0.0}))


# ------------------------------------------------------------------ the ladle and pot
POT_AT = (5.4, -0.6, 16.2)          # the pot's centre, held on the left forearm before the belly


def _stir(i):
    """Stirring round the pot: the ladle's bowl goes round inside it (front, right, back, left), the right hand
    circling above; the pot held on the left arm."""
    a = math.radians(90.0 * i + 20.0)
    bowl = (POT_AT[0] + 1.5 * math.cos(a), POT_AT[1] + 1.5 * math.sin(a), POT_AT[2] + 0.4)
    hand = (POT_AT[0] - 0.4 + 1.2 * math.cos(a), POT_AT[1] + 2.4 + 1.2 * math.sin(a), POT_AT[2] + 6.4)
    return pose(pelvis=(0.0, 0.0, 13.2), lean=10.0, twist=4.0 * math.sin(a), head_pitch=14.0,
                **feet(0.9, -0.5, 2.3, 2.4), foot_yaw_r=10.0,
                hand_l=(POT_AT[0] - 0.6, POT_AT[1] - 2.9, POT_AT[2] - 0.8), elbow_l=(-0.8, -1.0, -0.4), grip_l="open",
                hand_r=hand, elbow_r=(-0.4, 1.0, -0.4), grip_r="fist", drag=(0.0, 0.08 * math.sin(a), 0.0),
                weapon=stow(ladle={"pot": POT_AT, "bowl": bowl}))


# ------------------------------------------------------------------ the pestle and mortar
MORTAR_AT = (5.2, 0.8, 0.0)         # the mortar's foot on the ground, before the knees


def _grind(i):
    """Kneeling on the right knee at a mortar on the ground, the left hand steadying its rim, the right driving the
    pestle: 0 lifted, 1 at the top (the anticipation), 2 driven down (the contact), 3 ground round."""
    seq = [
        ((5.0, 1.6, 11.6), 6.0, (0.1, 0.0, 1.0)),
        ((4.6, 1.8, 13.8), 2.0, (0.05, 0.0, 1.0)),
        ((5.2, 1.1, 7.8), 14.0, (0.0, 0.0, 1.0)),
        ((5.8, 0.6, 8.2), 12.0, (-0.2, -0.15, 1.0)),
    ]
    hr, ln, tilt = seq[i]
    return pose(pelvis=(0.2, 0.0, 7.9), lean=ln, head_pitch=16.0, foot_l=(3.0, -2.3, 1.3), foot_r=(-4.0, 2.2, 1.25),
                toe_r=70.0, knee_l=(1.0, -0.2, 0.6), knee_r=(1.0, 0.2, -1.0), foot_yaw_l=-4.0, foot_yaw_r=10.0,
                hand_l=(4.4, -0.9, 4.6), elbow_l=(-0.4, -1.0, 0.2), grip_l="open",
                hand_r=hr, elbow_r=(-0.4, 1.0, -0.2), grip_r="fist", drag=(0.0, 0.0, [0.0, -0.2, 0.3, 0.0][i]),
                weapon=stow(pestle={"mortar": MORTAR_AT, "tilt": tilt, "down": i == 2}))


# ------------------------------------------------------------------ the axe
def _chop(i):
    """An overhead chop at a block before the feet: 0 the ready (the head at the block), 1 swung up past the right
    shoulder, 2 over the head (the anticipation: up on the toes, leaning back), 3 down into the block (the contact),
    4 wrenched free, 5 back to the ready. Both hands on the haft, the left at its butt."""
    seq = [
        # right hand (the upper), left hand (the butt), lean, pelvis, the heels' lift, the haft's direction
        ((4.6, 0.6, 15.4), (2.6, 0.2, 13.8), 8.0, (0.2, 0.0, 12.8), 0.0, (0.72, 0.1, -0.68)),
        ((2.4, 3.4, 23.6), (1.0, 2.4, 20.6), -2.0, (0.0, 0.0, 13.3), 0.0, (0.1, 0.5, 0.86)),
        ((0.2, 0.9, 32.4), (0.4, 0.3, 29.6), -10.0, (-0.2, 0.0, 13.9), 0.8, (-0.62, 0.05, 0.78)),
        ((6.8, 0.5, 13.8), (4.4, 0.3, 15.0), 22.0, (0.6, 0.0, 11.6), 0.0, (0.88, 0.05, -0.46)),
        ((5.6, 0.5, 15.2), (3.4, 0.3, 15.6), 16.0, (0.5, 0.0, 12.0), 0.0, (0.84, 0.05, -0.54)),
        ((4.8, 0.6, 15.6), (2.8, 0.2, 14.0), 10.0, (0.3, 0.0, 12.6), 0.0, (0.76, 0.1, -0.64)),
    ]
    hr, hl, ln, pel, heel, haft = seq[i]
    return pose(pelvis=pel, lean=ln, head_pitch=[10.0, -2.0, -6.0, 14.0, 12.0, 10.0][i],
                **feet(1.9, -1.6, 2.6, 2.6, 1.3 + heel, 1.3 + heel), toe_l=24.0 * heel, toe_r=24.0 * heel,
                foot_yaw_r=14.0, hand_r=hr, hand_l=hl, elbow_r=(-0.4, 1.0, -0.6), elbow_l=(-0.4, -1.0, -0.6),
                grip_l="fist", grip_r="fist", drag=([0.0, 0.2, 0.5, -0.6, -0.3, 0.0][i], 0.0, [0.0, -0.3, -0.6, 0.6, 0.3, 0.0][i]),
                weapon=stow(axe={"haft": haft}))


# ------------------------------------------------------------------ the hammer
ANVIL_AT = (6.4, 0.6, 0.0)          # the anvil's stump on the ground before the feet


def _hammer(i):
    """At the anvil, the tongs in the left hand holding the hot bar on it: 0 the rest (the hammer lifted a little over
    the bar), 1 raised by the ear (the anticipation), 2 at the top, 3 the blow (the contact), 4 the rebound, 5 turning
    the bar (the tongs roll it) as the hammer comes back."""
    seq = [
        # the right hand, the hammer's handle direction (from the hand to the head), lean, twist
        ((5.4, 2.2, 13.6), (0.5, -0.35, 0.3), 12.0, 4.0),
        ((2.6, 4.2, 20.2), (0.1, -0.2, 0.97), 4.0, 12.0),
        ((0.8, 4.0, 24.4), (-0.45, -0.1, 0.88), 0.0, 16.0),
        ((5.2, 1.8, 11.2), (0.8, -0.45, -0.1), 16.0, 0.0),
        ((4.8, 2.2, 14.2), (0.55, -0.35, 0.45), 12.0, 4.0),
        ((4.6, 2.6, 15.8), (0.4, -0.3, 0.6), 10.0, 6.0),
    ]
    hr, d, ln, tw = seq[i]
    return pose(pelvis=(0.1, 0.0, 12.9), lean=ln, twist=tw, head_pitch=16.0, **feet(1.2, -1.0, 2.5, 2.6),
                foot_yaw_r=14.0, hand_r=hr, elbow_r=(-0.6, 1.0, -0.2) if i in (1, 2) else (-0.6, 1.0, -0.5),
                grip_r="fist", hand_l=(5.0, -1.8, 12.4 + (0.3 if i == 5 else 0.0)), elbow_l=(-0.6, -1.0, -0.4),
                grip_l="fist", drag=([0.0, 0.1, 0.2, -0.4, -0.1, 0.0][i], 0.0, 0.0),
                weapon=stow(hammer={"dir": _unit(d), "anvil": ANVIL_AT, "turn": i == 5}))


# ------------------------------------------------------------------ the herb basket
def _pick(i):
    """Crouched over the herbs, a basket on the ground before the feet, the left hand on the knee: 0 reaching down to a
    plant, 1 grasping, 2 the pluck (pulled up), 3 carried over the basket, 4 dropped in, 5 back down."""
    seq = [
        ((5.8, 3.0, 2.6), 28.0, 6.0),
        ((6.2, 2.6, 1.6), 32.0, 5.0),
        ((5.4, 2.4, 5.4), 26.0, 2.0),
        ((5.2, -0.6, 5.8), 26.0, -8.0),
        ((5.4, -1.2, 4.2), 28.0, -10.0),
        ((5.4, 1.8, 4.4), 26.0, 0.0),
    ]
    hr, ln, tw = seq[i]
    return pose(pelvis=(-0.8, 0.0, 7.6), lean=ln, twist=tw, head_pitch=14.0,
                **feet(1.2, 0.6, 2.8, 2.8), foot_yaw_l=-18.0, foot_yaw_r=18.0,
                knee_l=(1.0, -0.6, 0.6), knee_r=(1.0, 0.6, 0.6),
                hand_r=hr, elbow_r=(-0.4, 1.0, -0.2), grip_r="fist" if i in (1, 2, 3) else "relaxed",
                hand_l=(3.2, -3.6, 8.6), elbow_l=(-0.2, -1.0, -0.6), grip_l="relaxed",
                drag=(0.0, 0.0, [0.0, 0.0, 0.2, 0.0, 0.0, 0.0][i]),
                weapon=stow(herbs={"sprig": i in (2, 3), "basket": (6.4, -2.2, 0.0)}))


# ------------------------------------------------------------------ the net
SEAT = dict(foot_l=(2.6, 1.4, 1.1), foot_r=(2.2, -1.6, 2.1), knee_l=(0.4, -1.0, 0.3), knee_r=(0.4, 1.0, 0.3),
            foot_yaw_l=60.0, foot_yaw_r=-60.0)


def _mend(i):
    """Seated cross-legged, the net over the lap and spilling before the knees: the left hand holds up the mesh, the
    right draws the netting needle through (0), out (1), pulls the knot tight (2) and goes back in (3)."""
    seq = [
        ((5.0, 0.6, 12.6), 0.0),
        ((4.6, 3.6, 13.6), 4.0),
        ((3.4, 5.8, 15.0), 8.0),
        ((4.8, 1.8, 13.2), 2.0),
    ]
    hr, tw = seq[i]
    return pose(pelvis=(-0.4, 0.0, 4.2), lean=10.0, twist=tw, head_pitch=18.0, **SEAT,
                hand_l=(4.6, -3.4, 14.6), elbow_l=(-0.6, -1.0, -0.2), grip_l="fist",
                hand_r=hr, elbow_r=(-0.6, 1.0, -0.2), grip_r="fist", drag=(0.0, 0.0, 0.0),
                weapon=stow(net={"needle": i}))


# ------------------------------------------------------------------ the places
def _open(i):
    """Opening with the left hand (a chest's lid, a letter box's flap, a door): 0 the reach, 1 the grasp, 2 the pull
    (up and back), 3 held open, looking in. The right hand keeps the weapon at the side."""
    seq = [
        (0.4, 6.0, (5.6, -2.4, 16.0), 0.0, "open"),
        (0.6, 12.0, (7.4, -1.8, 15.0), 4.0, "fist"),
        (0.2, 4.0, (5.8, -2.8, 21.4), -6.0, "fist"),
        (0.0, 6.0, (6.0, -2.6, 22.6), 2.0, "fist"),
    ]
    pf, ln, hl, hp, grip = seq[i]
    return pose(pelvis=(pf, 0.0, 13.3), lean=ln, twist=[4.0, 8.0, 6.0, 6.0][i], head_pitch=hp,
                **feet(1.4, -0.6, 2.2, 2.3), hand_l=hl, elbow_l=(-0.4, -1.0, -0.6), grip_l=grip,
                hand_r=(0.6, 5.9, 13.8), grip_r="relaxed", drag=([0.2, 0.3, -0.3, 0.0][i], 0.0, 0.0),
                weapon=W())


def _tend(i):
    """Crouched at a bed or a fire, the left hand working before the feet (pressing the soil, pulling a weed, feeding
    the fire), the right forearm on the right knee, the weapon held along the thigh."""
    seq = [
        ((5.4, -1.6, 3.2), 26.0),
        ((6.0, -1.2, 1.6), 30.0),
        ((5.2, -2.0, 4.4), 26.0),
        ((5.8, -0.6, 2.4), 28.0),
    ]
    hl, ln = seq[i]
    return pose(pelvis=(-0.8, 0.0, 7.6), lean=ln, head_pitch=12.0, **feet(1.2, 0.6, 2.8, 2.8),
                foot_yaw_l=-18.0, foot_yaw_r=18.0, knee_l=(1.0, -0.6, 0.6), knee_r=(1.0, 0.6, 0.6),
                hand_l=hl, elbow_l=(-0.2, -1.0, -0.4), grip_l="open" if i in (0, 2) else "relaxed",
                hand_r=(4.2, 3.8, 9.6), elbow_r=(-0.6, 1.0, -0.2), grip_r="fist", drag=(0.0, 0.0, 0.0),
                weapon=W(blade=(-0.55, 0.3, -0.35), pole={"dir": (0.05, 0.14, 1.0), "butt": 8.4}))


def _sit(i):
    """Sitting down on a mat: 0 the knees bending, 1 lowered, a hand forward for balance, 2 down, the legs crossing,
    3 settled, the hands on the knees. The weapon stays in the right hand until the body is down, then lies beside it."""
    seq = [
        dict(pelvis=(-0.3, 0.0, 11.4), lean=10.0, **feet(0.8, -0.4, 2.4, 2.4), hand_l=(3.0, -4.6, 13.0),
             hand_r=(2.0, 5.4, 12.2)),
        dict(pelvis=(-1.0, 0.0, 7.8), lean=14.0, **feet(2.0, 1.6, 2.6, 2.6), knee_l=(1.0, -0.6, 0.6),
             knee_r=(1.0, 0.6, 0.6), hand_l=(5.0, -3.6, 8.4), hand_r=(1.4, 5.6, 7.0)),
        dict(pelvis=(-0.5, 0.0, 4.6), lean=6.0, **SEAT, hand_l=(3.4, -4.2, 7.4), hand_r=(3.4, 4.2, 7.4)),
        dict(pelvis=(-0.4, 0.0, 4.2), lean=2.0, **SEAT, hand_l=(3.6, -4.0, 6.4), hand_r=(3.6, 4.0, 6.4)),
    ]
    d = dict(seq[i])
    laid = {"at": (5.0, 7.5, 0.7), "dir": (0.15, -1.0, 0.0)}
    wp = W(laid=laid) if i >= 2 else W(blade=(0.5, 0.45, -0.74), pole={"dir": (0.1, 0.2, 1.0), "butt": 6.0 if i else 10.0})
    return pose(elbow_l=(-0.6, -1.0, 0.0), elbow_r=(-0.6, 1.0, 0.0), grip_l="relaxed", grip_r="fist" if i < 2 else "relaxed",
                head_pitch=[6.0, 8.0, 2.0, 0.0][i], drag=(0.0, 0.0, [0.0, 0.4, 0.2, 0.0][i]), weapon=wp, **d)


# name: (frames, fps, loop, hit frame or None, label, pose function, facing lock), as actions.CATALOG
WORK_CATALOG = {
    "work_sweep": (6, 6.0, True, 2, "Work: broom sweep", _sweep, None),
    "work_carry": (8, 10.0, True, None, "Work: shoulder pole (walking)", _carry, None),
    "work_rod": (4, 3.0, True, None, "Work: rod held out", _rod, None),
    "work_cast": (6, 6.0, False, 3, "Work: rod cast", _cast_rod, None),
    "work_hang": (6, 6.0, False, 3, "Work: hang washing", _hang, None),
    "work_stir": (4, 5.0, True, None, "Work: ladle and pot", _stir, None),
    "work_grind": (4, 5.0, True, 2, "Work: pestle and mortar", _grind, None),
    "work_chop": (6, 6.0, True, 3, "Work: axe chop", _chop, None),
    "work_hammer": (6, 6.0, True, 3, "Work: hammer at the anvil", _hammer, None),
    "work_pick": (6, 5.0, True, None, "Work: picking herbs", _pick, None),
    "work_mend": (4, 4.0, True, None, "Work: mending a net", _mend, None),
}
PLACE_CATALOG = {
    "open": (4, 10.0, False, None, "Place: open", _open, None),
    "tend": (4, 8.0, True, None, "Place: tend", _tend, None),
    "sit": (4, 10.0, False, None, "Place: sit", _sit, None),
}
