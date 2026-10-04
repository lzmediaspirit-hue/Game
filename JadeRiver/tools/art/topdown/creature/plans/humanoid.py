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

`monkey` (M1, the bamboo monkey): a hunched body (`hunch`, a lean every frame carries), `fur` paint (gold fur, an olive
mantle over the back and shoulders, a pale belly), a `monkey` face (a pale heart-shaped face and muzzle, big amber eyes,
round ears, a leaf tuft on the crown), long arms, a curling tail (`tail`), and a bamboo shoot in its right hand (`held`
kind "shoot", thrown on the blow). Its styles: idle `perch`, walk `lope`, windup `wind_shoot`, attack `hurl`, hurt
`knock`, death `tumble`.

`guardian` (M1, the stone guardian): a squat temple lion-dog of carved stone on two legs: `temple` paint (warm temple
stone in pits and flecks, moss on its shoulders and crown), the imp's `grin` face in jade (`glow` "jade": bulging glowing
jade eyes), a mane of spiral curls round its head (`mane`), a carved collar with a stone bell (`collar`), a flame-curl
tail, cracks that light up jade in its tell and its slam (`cracks`, the channel `glow`). It hauls both fists up over its
head (the tell, held) and slams them down before it in dust (the blow); beaten, it comes apart into a heap of blocks.
Its styles: idle `stand`, walk `stomp`, windup `fists_up`, attack `double_slam`, hurt `knock`, death `crumble`.

`ape` (M2, the cliff ape): the monkey's body grown heavy, a mane over its shoulders, a pale face under a heavy brow
(`monkey` face, `brow`), and a boulder held over its head in both hands (`held` kind "boulder"). Its styles: idle
`knuckle`, walk `knuckle_lope`, windup `hoist`, attack `boulder_smash`, hurt `knock`, death `topple_back`.

`sentinel` and `gate` (M2, the jade sentinel and the gate guardian): an armoured body, `armor` paint (rows of plates, a
belt), a `helm` face (a dome, a brim, a crest, a mask, glowing eyes; the gate's brows, mouth and eave horns), pauldrons,
tassets and gold runes (`armor`); the sentinel's halberd (`held` kind "halberd"), the gate guardian's bronze chest plate
and two jade bi rings orbiting it (`rings`). Styles: the sentinel's idle `halberd_rest`, walk `march`, windup
`halberd_back`, attack `halberd_sweep`, hurt `armor_rock`, death `topple_crack`; the gate's idle `ring_orbit`, walk
`ring_stomp`, windup `rings_rise`, attack `ring_sweep`, hurt `ring_wobble`, death `kneel_crack`.

`golem` (M4, the gravity golem): a body of separate chamfered basalt blocks floating apart, held by gravity (indigo
ripples in its gaps), a faceless hunched head, a violet singularity in its chest, a ring of pale stones orbiting it; it
takes the guardian's moves with its own styles: idle `orbit_bob`, walk `stomp`, windup `gravity_raise` (the singularity
swelling, drawing in lines and pebbles), attack `orbit_slam` (a shockwave ring), hurt `gravity_jolt` (its blocks jolted
apart), death `gravity_fails` (its blocks dropping into a heap).

`chief`, `abbot` and `elder` (M2, the people of size: Big Toad Tan, the Drowned Abbot, Elder Gu): see "the people of
size" below. Their styles: Tan's `chief_idle`, `chief_waddle`, `cleaver_raise`, `cleaver_slam`, `chief_rock`,
`chief_fall`; the Abbot's `abbot_sway`, `abbot_glide`, `staff_raise`, `staff_slam`, `abbot_rock`, `abbot_collapse`;
Gu's `elder_stand`, `elder_walk`, `tide_draw`, `tide_strike`, `elder_rock`, `elder_fall`.

`captain`, `admiral`, `general` and `presence` (M4, the late game's people of size: Comet Captain Rao, Admiral Voss,
General Kharn, the Ninth Presence): see "the people of size (M4)" below. Their styles: Rao's `capt_idle`, `capt_stride`,
`anchor_raise`, `anchor_slam`, `capt_rock`, `capt_fall`; Voss's `adm_stand`, `adm_walk`, `cannon_aim`, `broadside_cut`,
`adm_rock`, `adm_fall`; Kharn's `gen_stand`, `gen_march`, `glaive_raise`, `glaive_cleave`, `gen_rock`, `gen_fall`; the
Presence's `pres_hover`, `pres_glide`, `crown_gather`, `seat_palm`, `pres_rock`, `pres_fade`.
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
MONKEY_STYLES = {
    "perch": {"sway_amp": 0.25, "guard": 0.0,
              "right": ((3.2, -3.0, -3.6), (3.3, -2.9, -3.2), (3.4, -2.8, -2.9), (3.3, -2.9, -3.2), (3.2, -3.0, -3.6), (3.1, -3.1, -3.8)),
              "left": ((3.8, 2.8, -8.2),) * 6, "tail_wave": True},
    "lope": {"kind": "march", "bounce": 1.1, "twist_amp": 6.0, "stride": 2.4, "lift": 1.8, "swing": 2.4, "tail_wave": True},
    "wind_shoot": {"lean": (-10.0, -20.0, -26.0, -28.0), "twist": (-12.0, -24.0, -32.0, -34.0), "step": (-0.3, -0.6, -0.8, -0.9),
                   "sink": (0.2, 0.5, 0.7, 0.8), "plant": True, "chatter": (0.4, 1.0, 0.6, 1.0),
                   "right": ((0.4, -4.0, 0.6), (-1.0, -4.2, 3.0), (-2.0, -4.2, 4.6), (-2.4, -4.2, 5.2)),
                   "left": ((3.8, 3.4, -5.4), (4.2, 3.4, -3.8), (4.4, 3.2, -2.8), (4.4, 3.2, -2.6))},
    "hurl": {"lean": (-6.0, 10.0, 16.0, 12.0, 6.0, 2.0), "twist": (14.0, 36.0, 42.0, 34.0, 16.0, 4.0), "step": (0.8, 2.0, 2.4, 2.2, 1.2, 0.4),
             "sink": (0.6, 1.0, 0.9, 0.6, 0.3, 0.1), "plant": True, "release": 1, "chatter": (1.0, 0.7, 0.3, 0.1, 0.0, 0.0),
             "squash": {1: (1.04, 1.0, 0.97)},
             "right": ((-0.6, -2.6, 5.6), (5.0, -1.2, 2.0), (5.8, -0.6, -1.6), (4.6, -1.0, -3.6), (3.6, -2.0, -4.0), (3.2, -2.8, -3.8)),
             "left": ((3.6, 3.2, -1.4), (1.0, 4.0, -3.6), (2.6, 3.4, -6.6), (3.4, 3.0, -7.6), (3.8, 2.8, -8.0), (3.8, 2.8, -8.2))},
    "tumble": {"lean": (-14.0, -24.0, -30.0, -30.0, -30.0, -30.0, -30.0, -30.0), "sink": (0.0, 0.8, 2.0, 3.0, 3.4, 3.6, 3.6, 3.6),
               "droop": (-10.0, -18.0, -24.0, -26.0, -26.0, -26.0, -26.0, -26.0),
               "roll": (0.0, 0.0, 10.0, 34.0, 62.0, 84.0, 90.0, 88.0), "limp": True, "dark_from": 4, "fall": (5.0, 2.6),
               "chatter": (0.8, 0.6, 0.4, 0.3, 0.3, 0.3, 0.3, 0.3)},
}
STYLES.update(MONKEY_STYLES)
GUARDIAN_STYLES = {
    "stand": {"sway_amp": 0.2, "guard": 0.25},
    "stomp": {"kind": "march", "bounce": 0.45, "twist_amp": 5.0, "stride": 2.4, "lift": 1.6, "swing": 1.2},
    "fists_up": {"lean": (-2.0, -6.0, -8.0, -8.0), "step": (-0.2, -0.5, -0.7, -0.8), "sink": (0.4, 0.2, 0.0, 0.0), "plant": True,
                 "glare": True, "glow": (0.4, 0.8, 1.0, 1.0),
                 "right": ((1.6, -4.4, 3.0), (-0.4, -3.4, 7.6), (-1.2, -3.0, 9.0), (-1.4, -3.0, 9.2)),
                 "left": ((1.6, 4.4, 3.0), (-0.4, 3.4, 7.6), (-1.2, 3.0, 9.0), (-1.4, 3.0, 9.2))},
    "double_slam": {"lean": (4.0, 24.0, 24.0, 12.0, 4.0, 0.0), "step": (0.2, 1.4, 1.4, 0.7, 0.2, 0.0), "sink": (0.0, 2.2, 2.2, 0.9, 0.2, 0.0),
                    "plant": True, "glare": True, "glow": (1.0, 1.0, 0.6, 0.2, 0.0, 0.0), "dust": (1, 2, 3),
                    "squash": {1: (1.04, 1.04, 0.94)},
                    "right": ((2.6, -2.8, 8.4), (8.0, -2.4, -7.0), (8.0, -2.4, -7.0), (6.0, -3.2, -4.6), (4.4, -4.0, -3.4), (3.6, -4.6, -4.2)),
                    "left": ((2.6, 2.8, 8.4), (8.0, 2.4, -7.0), (8.0, 2.4, -7.0), (6.0, 3.2, -4.6), (4.4, 4.0, -3.4), (3.6, 4.6, -4.2))},
}
STYLES.update(GUARDIAN_STYLES)
# M2, the cliff ape: idle `knuckle` (hunched on its knuckles, breathing), walk `knuckle_lope`, windup `hoist` (it stands up
# roaring and hoists a boulder over its head, held), attack `boulder_smash` (it smashes the boulder down before it, the
# stone shattering in chips: the blow on frame 1; its throw has the same tell), death `topple_back`.
APE_STYLES = {
    "knuckle": {"sway_amp": 0.25, "guard": 0.0},
    "knuckle_lope": {"kind": "march", "bounce": 0.9, "twist_amp": 7.0, "stride": 2.6, "lift": 1.6, "swing": 2.6},
    "hoist": {"lean": (-8.0, -18.0, -26.0, -28.0), "step": (-0.2, -0.5, -0.7, -0.8), "sink": (0.6, 0.2, -0.6, -0.9), "plant": True,
              "chatter": (0.3, 1.0, 0.7, 1.0), "boulder": (0.3, 0.7, 1.0, 1.0),
              "right": ((4.6, -2.6, -9.0), (3.2, -2.4, -3.0), (0.6, -2.4, 4.4), (0.0, -2.4, 5.6)),
              "left": ((4.6, 2.6, -9.0), (3.2, 2.4, -3.0), (0.6, 2.4, 4.4), (0.0, 2.4, 5.6))},
    "boulder_smash": {"lean": (-26.0, 10.0, 12.0, 4.0, 0.0, 0.0), "step": (0.4, 1.8, 1.8, 1.0, 0.4, 0.0), "sink": (-0.8, 1.4, 1.4, 0.7, 0.2, 0.0),
                      "plant": True, "chatter": (1.0, 0.8, 0.5, 0.2, 0.0, 0.0), "boulder": (1.0, 1.0, 0.0, 0.0, 0.0, 0.0), "smash_at": 1,
                      "chips": (1, 2, 3), "dust": (1, 2, 3), "squash": {1: (1.04, 1.04, 0.95)},
                      "right": ((0.4, -2.4, 6.0), (8.0, -2.2, -9.0), (8.0, -2.4, -9.4), (6.6, -3.2, -9.6), (5.4, -3.8, -9.8), (4.8, -4.2, -10.0)),
                      "left": ((0.4, 2.4, 6.0), (8.0, 2.2, -9.0), (8.0, 2.4, -9.4), (6.6, 3.2, -9.6), (5.4, 3.8, -9.8), (4.8, 4.2, -10.0))},
    "topple_back": {"lean": (-16.0, -28.0, -40.0, -48.0, -52.0, -52.0, -52.0, -52.0), "sink": (0.0, 0.8, 2.0, 3.4, 4.2, 4.6, 4.6, 4.6),
                    "droop": (-10.0, -18.0, -24.0, -26.0, -26.0, -26.0, -26.0, -26.0),
                    "roll": (0.0, 0.0, 6.0, 26.0, 56.0, 80.0, 88.0, 86.0), "limp": True, "dark_from": 4, "fall": (7.0, 3.6),
                    "chatter": (0.8, 0.6, 0.4, 0.3, 0.3, 0.3, 0.3, 0.3)},
}
STYLES.update(APE_STYLES)
# M2, the jade sentinel: idle `halberd_rest` (the halberd held upright at its side), walk `march`, windup `halberd_back`
# (drawn back over its shoulder, its runes flaring, held), attack `halberd_sweep` (a wide sweep landing low before it,
# the blow on frame 1), hurt `armor_rock`, death `topple_crack` (it cracks, topples, its runes die).
SENTINEL_STYLES = {
    "halberd_rest": {"sway_amp": 0.15, "guard": 0.1,
                     "right": ((2.4, -3.5, 1.2),) * 6, "left": ((2.6, -2.9, -2.4),) * 6},
    "halberd_back": {"lean": (-3.0, -6.0, -8.0, -8.0), "twist": (-10.0, -22.0, -30.0, -32.0), "step": (-0.2, -0.5, -0.7, -0.8),
                     "sink": (0.2, 0.5, 0.7, 0.8), "plant": True, "glow": (0.4, 0.8, 1.0, 1.0),
                     "right": ((1.6, -3.4, 2.2), (0.2, -3.2, 3.2), (-1.0, -3.0, 3.8), (-1.3, -3.0, 4.0)),
                     "left": ((2.4, -2.2, -0.6), (2.2, -1.4, 0.2), (1.8, -0.8, 0.8), (1.7, -0.6, 0.9))},
    "halberd_sweep": {"lean": (2.0, 12.0, 12.0, 8.0, 3.0, 0.0), "twist": (-30.0, 34.0, 40.0, 30.0, 12.0, 0.0), "step": (0.4, 2.2, 2.4, 1.8, 0.8, 0.2),
                      "sink": (0.8, 1.4, 1.4, 1.0, 0.4, 0.1), "plant": True, "glow": (1.0, 1.0, 0.6, 0.2, 0.0, 0.0), "sweep_trail": (1, 2),
                      "squash": {1: (1.03, 1.0, 0.97)},
                      "right": ((-0.4, -3.4, 3.6), (5.4, 1.6, -3.0), (5.0, 2.6, -3.4), (4.0, 1.0, -2.6), (3.0, -1.8, -0.6), (2.4, -3.3, 1.0)),
                      "left": ((2.0, -1.0, 0.6), (2.6, -0.4, -1.4), (2.2, 0.6, -1.8), (2.4, -0.8, -1.8), (2.6, -2.2, -2.2), (2.6, -2.8, -2.4))},
    "armor_rock": {"lean": (-12.0, -6.0, -2.0), "twist": (8.0, -4.0, 0.0), "step": (-2.0, -1.2, -0.4), "sink": (0.4, 0.2, 0.0),
                   "droop": (-14.0, -4.0, 0.0), "right": ((1.6, -4.0, 2.4), (2.2, -3.8, 1.6), (2.4, -3.5, 1.2)),
                   "left": ((2.0, -2.6, -1.0), (2.4, -2.8, -2.0), (2.6, -2.9, -2.4)), "squint": True},
    "topple_crack": {"lean": (-6.0, 4.0, 10.0, 18.0, 16.0, 14.0, 14.0, 14.0), "sink": (0.0, 0.6, 3.0, 6.0, 6.4, 6.6, 6.6, 6.6),
                     "droop": (0.0, 18.0, 26.0, 30.0, 30.0, 30.0, 30.0, 30.0), "roll": (0.0, 0.0, 0.0, 16.0, 46.0, 76.0, 88.0, 86.0),
                     "limp": True, "dark_from": 3, "fall": (8.0, 3.0), "crack": (0.2, 0.5, 0.8, 1.0, 1.0, 1.0, 1.0, 1.0),
                     "right": ((2.6, -3.6, 0.8), (3.0, -3.8, -0.4), (3.4, -4.0, -2.0), (3.6, -4.4, -3.4), (3.6, -4.6, -4.0), (3.6, -4.6, -4.2),
                               (3.6, -4.6, -4.2), (3.6, -4.6, -4.2)),
                     "left": ((2.6, -2.8, -2.4), (2.6, -2.0, -3.0), (2.6, 1.0, -3.6), (2.0, 3.8, -4.2), (1.6, 4.4, -4.6), (1.6, 4.6, -4.6),
                              (1.6, 4.6, -4.6), (1.6, 4.6, -4.6))},
}
STYLES.update(SENTINEL_STYLES)
# M2, the gate guardian: idle `ring_orbit` (its bi rings orbiting slowly), walk `stomp`, windup `rings_rise` (its arms
# raised wide, the rings spinning up and rising, its eyes and runes flaring: held), attack `ring_sweep` (the rings whirled
# round it wide on both sides: the blow on frame 1), hurt `ring_wobble`, death `kneel_crack` (the rings drop, it kneels,
# cracking, its eyes dying). Channels: `orbit` (the rings' angle round it, degrees), `spin` (their own turn), `rise`,
# `out` (their orbit's reach), `drop` (fallen to the floor), `trail`.
GATE_STYLES = {
    "ring_orbit": {"sway_amp": 0.15, "guard": 0.15, "orbit": (0.0, 12.0, 24.0, 36.0, 48.0, 60.0), "spin": (0.0, 15.0, 30.0, 45.0, 60.0, 75.0)},
    "ring_stomp": {"kind": "march", "bounce": 0.4, "twist_amp": 4.0, "stride": 2.6, "lift": 1.6, "swing": 1.0,
                   "orbit": tuple(10.0 * i for i in range(8)), "spin": tuple(20.0 * i for i in range(8))},
    "rings_rise": {"lean": (-2.0, -5.0, -7.0, -7.0), "step": (-0.2, -0.4, -0.6, -0.6), "sink": (0.3, 0.1, -0.2, -0.3), "plant": True,
                   "glow": (0.5, 0.9, 1.0, 1.0), "orbit": (60.0, 100.0, 150.0, 210.0), "spin": (60.0, 140.0, 240.0, 360.0),
                   "rise": (1.0, 2.6, 3.8, 4.2), "out": (1.0, 1.08, 1.15, 1.18),
                   "right": ((2.0, -5.0, 0.0), (1.4, -6.0, 3.0), (0.8, -6.4, 5.0), (0.6, -6.4, 5.6)),
                   "left": ((2.0, 5.0, 0.0), (1.4, 6.0, 3.0), (0.8, 6.4, 5.0), (0.6, 6.4, 5.6))},
    "ring_sweep": {"lean": (-6.0, 6.0, 8.0, 5.0, 2.0, 0.0), "twist": (-20.0, 30.0, 40.0, 26.0, 10.0, 0.0), "step": (-0.4, 0.8, 1.0, 0.8, 0.4, 0.1),
                   "sink": (-0.2, 0.8, 0.9, 0.6, 0.3, 0.1), "plant": True, "glow": (1.0, 1.0, 0.7, 0.3, 0.0, 0.0),
                   "orbit": (240.0, 330.0, 400.0, 450.0, 480.0, 495.0), "spin": (400.0, 520.0, 600.0, 650.0, 680.0, 690.0),
                   "rise": (4.0, 0.6, 0.0, 0.4, 0.8, 0.8), "out": (1.2, 1.75, 1.8, 1.5, 1.2, 1.05), "trail": (1, 2),
                   "squash": {1: (1.02, 1.0, 0.98)},
                   "right": ((0.6, -6.4, 5.0), (5.4, -5.4, -1.6), (5.0, -3.0, -3.0), (4.0, -4.0, -2.6), (3.0, -4.6, -2.0), (2.4, -4.8, -1.6)),
                   "left": ((0.6, 6.4, 5.0), (-2.0, 6.0, -1.0), (-1.6, 5.6, -2.4), (0.0, 5.4, -2.6), (1.4, 5.0, -2.2), (2.0, 4.8, -1.8))},
    "ring_wobble": {"lean": (-10.0, -5.0, -1.0), "twist": (6.0, -3.0, 0.0), "step": (-1.6, -0.9, -0.3), "sink": (0.4, 0.2, 0.0),
                    "droop": (-12.0, -4.0, 0.0), "orbit": (30.0, 36.0, 40.0), "rise": (-1.0, 1.4, 0.2), "out": (0.85, 1.12, 1.0),
                    "wobble": (30.0, -20.0, 8.0), "squint": True},
    "kneel_crack": {"lean": (-4.0, 6.0, 14.0, 20.0, 22.0, 22.0, 22.0, 22.0), "sink": (0.0, 1.2, 3.2, 5.0, 5.6, 5.8, 5.8, 5.8),
                    "droop": (0.0, 10.0, 20.0, 26.0, 28.0, 28.0, 28.0, 28.0), "limp": True, "dark_from": 3,
                    "crack": (0.2, 0.45, 0.7, 0.9, 1.0, 1.0, 1.0, 1.0), "orbit": (40.0, 44.0, 48.0, 50.0, 50.0, 50.0, 50.0, 50.0),
                    "drop": (0.0, 0.3, 0.65, 0.9, 1.0, 1.0, 1.0, 1.0), "kneel": True},
}
STYLES.update(GATE_STYLES)
# M2, the people of size (sculpted on this plan's body: see "the people of size" below). Channels besides the body's:
# `roar` (the mouth open), `blade` (the cleaver's direction in the trunk's frame), `staff` (the ringed staff's), `tide`
# (Elder Gu's water orb, 0..1 gathering; on the blow's frames, how far its wave has spread), `heap` (the abbot's robe falling
# into a heap), `hat_tilt`.
_REST = (-0.55, -0.15, 0.82)
FOLK_STYLES = {
    # Big Toad Tan
    "chief_idle": {"sway_amp": 0.3, "guard": 0.2, "right": ((2.8, -3.4, -0.6),) * 6, "left": ((2.6, 3.9, -4.4),) * 6,
                   "lean": (0.0, -0.6, -1.0, -0.6, 0.0, 0.4)},
    "chief_waddle": {"kind": "march", "bounce": 0.7, "twist_amp": 9.0, "stride": 2.0, "lift": 1.3, "swing": 0.8,
                     "right": ((2.8, -3.4, -0.6),) * 8},
    "cleaver_raise": {"lean": (-4.0, -10.0, -14.0, -15.0), "step": (-0.2, -0.5, -0.7, -0.8), "sink": (0.3, 0.1, -0.2, -0.3), "plant": True,
                      "roar": (0.3, 0.8, 1.0, 1.0), "glare": True,
                      "right": ((1.8, -2.6, 1.6), (0.8, -1.6, 4.4), (0.2, -1.0, 6.0), (0.0, -1.0, 6.4)),
                      "left": ((2.4, 1.0, 0.0), (1.0, 0.4, 4.0), (0.3, 0.2, 5.6), (0.1, 0.2, 6.0)),
                      "blade": ((-0.4, -0.2, 0.9), (-0.8, 0.0, 0.6), (-0.95, 0.0, 0.3), (-1.0, 0.0, 0.2))},
    "cleaver_slam": {"lean": (-14.0, 14.0, 16.0, 10.0, 4.0, 0.0), "step": (0.2, 1.6, 1.8, 1.2, 0.6, 0.2), "sink": (-0.2, 1.4, 1.4, 0.8, 0.3, 0.0),
                     "plant": True, "roar": (1.0, 1.0, 0.6, 0.2, 0.0, 0.0), "dust": (1, 2, 3), "squash": {1: (1.03, 1.04, 0.95)},
                     "right": ((0.0, -1.0, 6.4), (5.0, -0.6, -3.6), (5.0, -0.6, -3.8), (4.2, -1.6, -2.8), (3.4, -2.8, -1.6), (2.8, -3.4, -0.6)),
                     "left": ((0.1, 0.2, 6.0), (4.6, 0.8, -3.4), (4.6, 0.8, -3.6), (3.6, 2.0, -3.6), (2.8, 3.2, -4.0), (2.6, 3.9, -4.4)),
                     "blade": ((-1.0, 0.0, 0.2), (0.75, 0.0, -0.65), (0.75, 0.0, -0.68), (0.5, -0.2, 0.0), (-0.1, -0.2, 0.7), _REST)},
    "chief_rock": {"lean": (-12.0, -6.0, -2.0), "twist": (8.0, -4.0, 0.0), "step": (-2.0, -1.2, -0.4), "sink": (0.4, 0.2, 0.0),
                   "droop": (-14.0, -4.0, 0.0), "squint": True, "roar": (0.6, 0.3, 0.0),
                   "right": ((2.0, -4.2, 0.6), (2.4, -3.8, 0.0), (2.8, -3.4, -0.6)), "left": ((1.6, 4.8, -2.4), (2.2, 4.2, -3.6), (2.6, 3.9, -4.4))},
    "chief_fall": {"lean": (-10.0, -18.0, -24.0, -26.0, -26.0, -26.0, -26.0, -26.0), "sink": (0.0, 0.6, 1.6, 2.6, 3.0, 3.2, 3.2, 3.2),
                   "droop": (-10.0, -16.0, -20.0, -22.0, -22.0, -22.0, -22.0, -22.0),
                   "roll": (0.0, 0.0, 8.0, 30.0, 62.0, 84.0, 90.0, 88.0), "limp": True, "dark_from": 4, "fall": (8.0, 4.4),
                   "roar": (0.6, 0.4, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0)},
    # the Drowned Abbot
    "abbot_sway": {"sway_amp": 0.25, "guard": 0.1, "right": ((2.2, -4.6, -1.4),) * 6, "left": ((3.0, 0.4, -2.6),) * 6},
    "abbot_glide": {"kind": "march", "bounce": 0.3, "twist_amp": 3.0, "stride": 1.6, "lift": 0.8, "swing": 0.6,
                    "right": ((2.2, -4.6, -1.4),) * 8},
    "staff_raise": {"lean": (-4.0, -8.0, -12.0, -12.0), "step": (-0.2, -0.4, -0.6, -0.6), "plant": True, "glare": True,
                    "hat_tilt": (-4.0, -8.0, -12.0, -12.0),
                    "right": ((2.2, -3.6, 1.2), (1.8, -4.0, 4.2), (1.3, -4.2, 6.4), (1.2, -4.2, 6.9)),
                    "left": ((3.0, 0.4, -1.8), (2.9, 0.3, -1.0), (2.8, 0.2, -0.6), (2.8, 0.2, -0.6)),
                    "staff": ((0.1, -0.05, 1.0), (0.08, -0.1, 1.0), (0.05, -0.12, 1.0), (0.05, -0.12, 1.0))},
    "staff_slam": {"lean": (-10.0, 18.0, 18.0, 10.0, 4.0, 0.0), "sink": (0.0, 1.2, 1.2, 0.6, 0.2, 0.0), "step": (0.0, 0.8, 0.8, 0.5, 0.2, 0.0),
                   "plant": True, "glare": True, "toll": (1, 2, 3), "squash": {1: (1.03, 1.03, 0.96)}, "hat_tilt": (-10.0, 8.0, 8.0, 4.0, 2.0, 0.0),
                   "right": ((1.2, -4.2, 6.9), (3.6, -2.4, -1.0), (3.6, -2.4, -1.2), (3.2, -3.2, -1.3), (2.6, -4.0, -1.4), (2.2, -4.6, -1.4)),
                   "left": ((2.8, 0.2, -0.6), (3.2, 0.0, 0.4), (3.2, 0.0, 0.2), (3.0, 0.4, -0.8), (3.0, 0.4, -1.8), (3.0, 0.4, -2.6)),
                   "staff": ((0.05, -0.12, 1.0), (0.25, 0.0, 1.0), (0.25, 0.0, 1.0), (0.15, 0.0, 1.0), (0.1, 0.0, 1.0), (0.08, 0.0, 1.0))},
    "abbot_rock": {"lean": (-12.0, -6.0, -2.0), "twist": (8.0, -4.0, 0.0), "step": (-2.0, -1.2, -0.4), "sink": (0.4, 0.2, 0.0),
                   "droop": (-14.0, -4.0, 0.0), "squint": True, "hat_tilt": (6.0, 2.0, 0.0),
                   "right": ((1.8, -4.8, -0.6), (2.0, -4.7, -1.0), (2.2, -4.6, -1.4)), "left": ((2.0, 2.6, -1.0), (2.6, 1.4, -2.0), (3.0, 0.4, -2.6))},
    "abbot_collapse": {"sink": (0.0, 1.5, 3.5, 6.0, 7.6, 8.4, 8.6, 8.6), "heap": (0.0, 0.1, 0.3, 0.55, 0.8, 0.95, 1.0, 1.0),
                       "lean": (6.0, 14.0, 24.0, 30.0, 30.0, 30.0, 30.0, 30.0), "droop": (0.0, 10.0, 20.0, 28.0, 30.0, 30.0, 30.0, 30.0),
                       "limp": True, "dark_from": 3, "hat_tilt": (0.0, -8.0, -16.0, -24.0, -28.0, -30.0, -30.0, -30.0)},
    # Elder Gu
    "elder_stand": {"sway_amp": 0.2, "guard": 0.0, "right": ((2.9, -0.7, -4.4),) * 6, "left": ((2.9, 0.7, -4.4),) * 6},
    "elder_walk": {"kind": "march", "bounce": 0.3, "twist_amp": 4.0, "stride": 1.8, "lift": 0.8, "swing": 0.6,
                   "right": ((2.9, -0.7, -4.4),) * 8, "left": ((2.9, 0.7, -4.4),) * 8},
    "tide_draw": {"lean": (-3.0, -6.0, -8.0, -9.0), "twist": (-10.0, -20.0, -28.0, -30.0), "step": (-0.3, -0.6, -0.8, -0.9),
                  "sink": (0.2, 0.5, 0.7, 0.8), "plant": True, "tide": (0.3, 0.6, 0.9, 1.0), "glare": True,
                  "right": ((1.2, -4.0, -1.6), (-0.6, -4.4, -0.4), (-1.6, -4.4, 0.4), (-1.8, -4.4, 0.6)),
                  "left": ((3.6, 2.6, -2.0), (4.6, 2.0, -1.6), (5.0, 1.6, -1.4), (5.0, 1.6, -1.4))},
    "tide_strike": {"lean": (6.0, 12.0, 12.0, 10.0, 5.0, 2.0), "twist": (-10.0, 24.0, 30.0, 30.0, 14.0, 4.0), "step": (1.4, 3.0, 3.2, 2.8, 1.6, 0.6),
                    "sink": (0.6, 1.0, 1.0, 0.8, 0.4, 0.1), "plant": True, "tide": (1.0, 0.3, 0.8, 0.0, 0.0, 0.0), "squash": {1: (1.03, 1.0, 0.97)},
                    "right": ((3.0, -3.4, -1.0), (7.6, -1.6, -0.4), (7.8, -1.6, -0.4), (6.6, -2.0, -1.0), (4.4, -1.6, -2.6), (3.2, -1.0, -4.0)),
                    "left": ((4.0, 2.6, -1.6), (1.4, 3.6, -2.8), (1.2, 3.6, -3.0), (1.8, 3.0, -3.4), (2.4, 1.6, -4.0), (2.8, 0.8, -4.4))},
    "elder_rock": {"lean": (-12.0, -6.0, -2.0), "twist": (8.0, -4.0, 0.0), "step": (-2.0, -1.2, -0.4), "sink": (0.4, 0.2, 0.0),
                   "droop": (-14.0, -4.0, 0.0), "squint": True,
                   "right": ((1.6, -4.4, -0.6), (2.4, -2.6, -2.6), (2.9, -0.7, -4.4)), "left": ((1.6, 4.4, -0.6), (2.4, 2.6, -2.6), (2.9, 0.7, -4.4))},
    "elder_fall": {"lean": (-6.0, 4.0, 10.0, 16.0, 16.0, 16.0, 16.0, 16.0), "sink": (0.0, 1.0, 3.0, 5.0, 5.4, 5.6, 5.6, 5.6),
                   "droop": (0.0, 14.0, 22.0, 26.0, 26.0, 26.0, 26.0, 26.0), "roll": (0.0, 0.0, 0.0, 14.0, 44.0, 74.0, 86.0, 84.0),
                   "limp": True, "dark_from": 4, "fall": (6.0, 3.6)},
}
STYLES.update(FOLK_STYLES)


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
MONKEY = {
    "hip": 5.6, "hunch": 22.0,
    "legs": {"top": (1.7, -0.3), "foot": (2.0, 0.9, 0.9), "bones": (3.2, 3.2), "thigh": (1.5, 1.2), "shin": (1.05, 0.85),
             "knee": None, "boot": ((0.8, 0.0, -0.3), (1.6, 0.95, 0.55)), "plant": (0.8, -0.9)},
    "trunk": [{"at": (0.0, 0.0, 0.8), "r": (2.1, 2.5, 1.9), "paint": True}, {"at": (0.4, 0.0, 3.0), "r": (2.2, 2.6, 2.3), "paint": True},
              {"at": (0.5, 0.0, 5.0), "r": (1.9, 2.8, 1.9), "paint": True}],
    "neck": ((0.7, 0.0, 6.3), 0.9),
    "head": {"at": ((1.0, 0.0, 6.4), 2.7), "r": (2.6, 2.75, 2.6)},
    "face": {"kind": "monkey", "disc": ((1.55, 0.0, -0.3), (1.35, 2.15, 1.95)), "muzzle": ((2.55, 0.0, -1.05), (0.95, 1.2, 0.85)),
             "eyes": (2.55, 0.85, 0.35), "nose": (3.45, 0.0, -0.85), "mouth": (3.2, 0.0, -1.55), "ears": ((-0.1, 2.7, 0.3), 1.05),
             "tuft": ((-0.3, 0.0, 2.4), ((0.6, 0.0, 1.8), (-0.6, 0.5, 1.6), (0.0, -0.6, 1.9)), (0.55, 0.38, 1.4))},
    "arms": {"shoulder": (2.7, 5.2), "bones": (4.2, 4.2), "hint": (-0.6, 1.0, -1.0), "ball": None, "upper": (0.95, 0.85), "elbow": None,
             "lower": (0.85, 0.75), "wrap": None, "fist": (0.95, 0.85, 0.8), "guard": (3.6, 3.0, -7.6), "limp": (0.6, 4.6, -4.6, 0.3)},
    "paint": {"kind": "fur"},
    "tail": {"root": (-2.0, 0.0, 1.2), "segs": (2.2, 2.2, 2.0, 1.8, 1.6, 1.4, 1.2, 1.0), "r": (0.75, 0.42)},
    "held": {"kind": "shoot", "r": 0.42, "mat": "cane", "length": 4.2},
}
GUARDIAN = {
    "hip": 8.2,
    "legs": {"top": (2.6, -0.8), "foot": (3.0, 1.3, 0.9), "bones": (4.3, 4.1), "thigh": (2.4, 2.1), "shin": (2.1, 1.9), "knee": None,
             "boot": ((1.0, 0.0, -0.4), (2.9, 1.9, 1.3)), "plant": (1.0, -1.2)},
    "trunk": [{"at": (0.0, 0.0, 1.0), "r": (3.0, 4.0, 2.4), "paint": True}, {"at": (0.3, 0.0, 4.0), "r": (3.4, 4.4, 3.0), "paint": True},
              {"at": (0.5, 0.0, 7.0), "r": (3.6, 5.0, 3.4), "paint": True}],
    "neck": ((0.8, 0.0, 9.6), 1.9),
    "head": {"at": ((1.5, 0.0, 9.8), 3.5), "r": (3.7, 4.0, 3.5)},
    "face": {"kind": "grin", "glow": "jade", "brow": ((2.9, 0.0, 1.3), (1.4, 3.6, 1.0)), "eyes": (3.45, 1.6, 0.45),
             "nose": ((4.0, 0.0, -0.4), 0.95), "grin": ((3.1, 0.0, -1.9), (1.1, 3.0, 0.7)), "teeth": (3.85, 2.2, -1.75, 0.7),
             "ears": ((0.0, 3.6, 1.5), (-1.0, 5.2, 3.2), (1.25, 0.3))},
    "mane": ((150.0, 20.0, 1.5), (180.0, 30.0, 1.5), (-150.0, 20.0, 1.5), (120.0, 45.0, 1.4), (-120.0, 45.0, 1.4), (180.0, 65.0, 1.4),
             (90.0, 30.0, 1.3), (-90.0, 30.0, 1.3), (140.0, -15.0, 1.4), (-140.0, -15.0, 1.4), (100.0, -25.0, 1.3), (-100.0, -25.0, 1.3)),
    "collar": {"at": 0.35, "bell": 1.15},
    "arms": {"shoulder": (4.8, 8.4), "bones": (5.0, 4.8), "hint": (-0.6, 1.0, -1.0), "ball": None, "upper": (2.0, 1.8), "elbow": None,
             "lower": (1.8, 1.7), "wrap": None, "fist": (2.4, 2.2, 2.1), "guard": (3.4, 4.8, -4.6), "limp": (0.8, 6.4, -6.0, 0.4)},
    "paint": {"kind": "temple"},
    "tail": {"root": (-2.6, 0.0, 2.4), "segs": (2.4, 2.2, 2.0, 1.8, 1.4, 1.2), "r": (1.2, 0.7)},
    "cracks": ((2, ((-40.0, 40.0), (-20.0, 20.0), (-35.0, 0.0), (-15.0, -20.0))), (1, ((30.0, 30.0), (15.0, 5.0), (30.0, -20.0))),
               (3, ((60.0, 40.0), (45.0, 20.0), (60.0, 5.0)))),
}
# M2: the cliff ape (its side-view sheet: ~50 px tall on its knuckles): the monkey grown huge and heavy, no tail, a
# shaggy white mane over its shoulders, back and crown, a dark leathery face and chest under a heavy brow, long thick arms.
APE = {
    "hip": 7.2, "hunch": 30.0,
    "legs": {"top": (2.2, -0.3), "foot": (2.8, 0.9, 1.1), "bones": (3.8, 3.8), "thigh": (2.2, 1.8), "shin": (1.7, 1.35),
             "knee": None, "boot": ((0.9, 0.0, -0.3), (2.0, 1.3, 0.75)), "plant": (1.0, -1.0)},
    "trunk": [{"at": (0.0, 0.0, 1.0), "r": (2.9, 3.3, 2.5), "paint": True}, {"at": (0.6, 0.0, 3.9), "r": (3.3, 3.9, 3.3), "paint": True},
              {"at": (0.8, 0.0, 6.8), "r": (3.1, 4.8, 3.0), "paint": True}],
    "neck": ((1.3, 0.0, 8.6), 1.4),
    "head": {"at": ((1.7, 0.0, 8.8), 3.0), "r": (2.8, 2.9, 2.8)},
    "face": {"kind": "monkey", "disc": ((1.7, 0.0, -0.4), (1.5, 2.2, 2.0)), "muzzle": ((2.8, 0.0, -1.2), (1.2, 1.6, 1.0)),
             "eyes": (2.75, 0.95, 0.3), "nose": (3.9, 0.0, -0.95), "mouth": (3.65, 0.0, -1.8), "ears": ((-0.1, 2.9, 0.2), 1.0),
             "tuft": ((-0.3, 0.0, 2.6), (), (0.5, 0.3, 1.0)), "brow": ((2.1, 0.0, 1.05), (0.9, 2.3, 0.5))},
    "arms": {"shoulder": (4.2, 7.0), "bones": (5.8, 5.8), "hint": (-0.6, 1.0, -1.0), "ball": None, "upper": (1.9, 1.7), "elbow": None,
             "lower": (1.7, 1.45), "wrap": None, "fist": (1.6, 1.5, 1.35), "guard": (4.8, 4.2, -11.0), "limp": (0.8, 6.0, -6.0, 0.4)},
    "paint": {"kind": "fur"},
    "tail": None,
    "held": {"kind": "boulder", "r": 3.0, "mat": "boulder"},
}
# M2: the jade sentinel (its side-view sheet: ~58 px tall to the helmet's crest): a warrior statue of carved jade in
# lamellar armour, a bronze belt and trim, plates hanging from its belt, great pauldrons, a crested helmet with cheek
# guards over a stern mask, a glowing gold slit for its eyes, gold runes on its cuirass and pauldrons, a bronze-bladed
# halberd on a dark shaft.
SENTINEL = {
    "hip": 8.4,
    "legs": {"top": (1.5, -0.6), "foot": (1.9, 1.0, 0.6), "bones": (4.3, 4.2), "thigh": (1.45, 1.25), "shin": (1.25, 1.05), "knee": 1.25,
             "boot": ((0.8, 0.0, -0.3), (1.9, 1.15, 0.85)), "plant": (1.2, -1.4)},
    "trunk": [{"at": (0.0, 0.0, 0.6), "r": (2.0, 2.8, 1.7), "paint": True}, {"at": (0.0, 0.0, 2.6), "r": (1.75, 2.45, 1.2), "mat": "trim"},
              {"at": (0.1, 0.0, 5.0), "r": (2.3, 3.4, 2.6), "paint": True}],
    "neck": ((0.2, 0.0, 7.5), 1.0),
    "head": {"at": ((0.4, 0.0, 7.8), 2.1), "r": (2.05, 1.95, 2.2)},
    "face": {"kind": "helm", "dome": ((-0.1, 0.0, 0.55), (2.25, 2.15, 2.0)), "brim": ((0.0, 0.0, -0.05), (2.35, 2.25, 0.45)),
             "crest": ((1.6, 0.0, 2.2), (-1.8, 0.0, 2.6), 0.55), "cheeks": ((0.7, 1.85, -0.9), (0.9, 0.35, 1.1)),
             "mask": ((1.45, 0.0, -0.3), (0.75, 1.55, 1.45)), "slit": (2.15, 0.85, 0.1), "glow": "gold"},
    "arms": {"shoulder": (3.4, 6.2), "bones": (3.4, 3.3), "hint": (-0.6, 1.0, -1.0), "ball": None, "upper": (1.15, 1.05), "elbow": None,
             "lower": (1.05, 0.95), "wrap": None, "fist": (1.15, 1.05, 1.05), "guard": (2.6, 3.2, -4.0), "limp": (0.8, 4.6, -5.0, 0.4)},
    "paint": {"kind": "armor", "rows": 1.1, "belt": (2.0, 3.2)},
    "armor": {"pauldrons": ((0.0, 3.6, 6.6), (1.7, 1.5, 1.05)), "tassets": 5, "tasset": (1.3, 0.3, 1.7),
              "runes": ((2, 0.0, 55.0), (2, 25.0, 35.0), (2, -25.0, 35.0), (0, 0.0, 30.0)), "dead": "dark"},
    "held": {"kind": "halberd", "shaft": (7.0, 4.2), "r": 0.4, "blade": (2.3, 0.3, 1.9), "spike": 3.0},
}
# M2: the gate guardian (its side-view sheet: ~114 px tall to the crown's tip): the sentinel's armoured body grown into a
# towering guardian of jade and bronze: a bronze chest plate over a jade cuirass, layered bronze pauldrons, long armoured
# skirt panels, bronze gauntlets, a stern bronze mask with heavy brows and glowing gold eyes under a jade crown with eave
# horns swept up like a temple roof's, gold runes; two jade bi rings orbiting it.
GATE = {
    "hip": 9.0,
    "legs": {"top": (1.8, -0.6), "foot": (2.3, 1.2, 0.6), "bones": (4.5, 4.4), "thigh": (1.9, 1.6), "shin": (1.6, 1.35), "knee": 1.5,
             "boot": ((0.9, 0.0, -0.3), (2.3, 1.4, 1.0)), "plant": (1.2, -1.4)},
    "trunk": [{"at": (0.0, 0.0, 0.6), "r": (2.4, 3.3, 2.0), "paint": True}, {"at": (0.0, 0.0, 2.8), "r": (2.1, 2.9, 1.3), "mat": "trim"},
              {"at": (0.2, 0.0, 5.6), "r": (2.8, 4.1, 3.2), "paint": True}, {"at": (1.75, 0.0, 6.6), "r": (1.3, 2.7, 1.9), "mat": "trim"}],
    "neck": ((0.3, 0.0, 8.6), 1.3),
    "head": {"at": ((0.5, 0.0, 9.0), 2.3), "r": (2.2, 2.1, 2.3)},
    "face": {"kind": "helm", "dome": ((-0.2, 0.0, 0.7), (2.35, 2.25, 2.1)), "brim": ((-0.1, 0.0, 0.4), (2.5, 2.4, 0.5)),
             "crest": ((1.4, 0.0, 2.6), (-1.6, 0.0, 3.2), 0.75), "cheeks": ((0.6, 2.0, -0.8), (1.0, 0.35, 1.2)),
             "mask": ((1.35, 0.0, -0.3), (1.0, 1.75, 1.7)), "mask_mat": "trim", "eyes": (2.3, 0.75, 0.15),
             "brows": ((2.2, 0.75, 0.6), (0.5, 0.8, 0.3)), "mouth": (2.35, 0.0, -1.0),
             "eaves": ((-0.2, 2.0, 1.6), (-0.6, 3.4, 2.0), (-1.0, 4.4, 3.0), (-1.2, 4.7, 4.2)), "glow": "gold"},
    "arms": {"shoulder": (4.2, 7.0), "bones": (4.0, 3.8), "hint": (-0.6, 1.0, -1.0), "ball": None, "upper": (1.5, 1.35), "elbow": None,
             "lower": (1.35, 1.25), "wrap": None, "fist": (1.6, 1.5, 1.45), "guard": (2.6, 4.8, -4.4), "limp": (1.0, 5.0, -5.8, 0.4)},
    "paint": {"kind": "armor", "rows": 1.25, "belt": (2.2, 3.5)},
    "armor": {"pauldrons": ((0.0, 4.4, 7.4), (2.3, 2.0, 1.3)), "tassets": 7, "tasset": (1.5, 0.35, 2.9),
              "runes": ((2, 0.0, 30.0), (2, 35.0, 50.0), (2, -35.0, 50.0), (0, 20.0, 20.0), (0, -20.0, 20.0)), "dead": "dark"},
    "rings": {"n": 2, "orbit": 7.8, "r": 2.6, "tube": 0.9, "z": 10.6, "beads": 14},
}
# M2: the people of size. Big Toad Tan (`chief`): the Mudwater bandits' chief, a head and a half taller than his men and
# twice as broad, a great bare belly under an open leather vest, a wide red sash, baggy trousers wrapped at the shin,
# heavy arms, a small head sunk between his shoulders with a topknot, a wide toad's grin and a stubbled jaw; his Mudwater
# Cleaver (a broad blade with nine brass rings on its spine) on his shoulder, a wine gourd at his hip.
CHIEF = {
    "hip": 6.4,
    "legs": {"top": (2.3, -0.6), "foot": (3.0, 1.0, 0.8), "bones": (3.4, 3.3), "thigh": (2.1, 1.75), "shin": (1.6, 1.35), "knee": None,
             "boot": ((0.9, 0.0, -0.3), (2.1, 1.35, 0.95)), "plant": (1.2, -1.4)},
    "trunk": [{"at": (0.0, 0.0, 0.8), "r": (3.0, 3.7, 2.2), "paint": True}, {"at": (1.1, 0.0, 3.4), "r": (3.7, 4.0, 3.4), "paint": True},
              {"at": (0.4, 0.0, 6.5), "r": (2.9, 4.7, 2.5), "paint": True}],
    "neck": ((0.7, 0.0, 8.2), 1.7),
    "head": {"at": ((1.0, 0.0, 8.4), 2.4), "r": (2.35, 2.45, 2.4)},
    "face": {"kind": "human", "eyes": (2.1, 0.8, 0.35), "brow": (0.4, 0.75, 0.3), "brow_tilt": -16.0, "nose": (2.45, 0.0, -0.15),
             "mouth": (2.05, 1.3, -1.0), "grin": 1.0, "ears": (0.0, 2.35, 0.1), "beard": "stubble", "hair": "topknot"},
    "arms": {"shoulder": (4.5, 6.8), "bones": (3.6, 3.4), "hint": (-0.6, 1.0, -1.0), "ball": None, "upper": (1.65, 1.5), "elbow": None,
             "lower": (1.5, 1.3), "wrap": None, "fist": (1.25, 1.15, 1.15), "guard": (2.2, 5.2, -3.4), "limp": (1.0, 5.4, -5.4, 0.4)},
    "paint": {"kind": "clothes", "zones": [{"mat": "sash", "z": (1.5, 3.1), "inner": 4.3},
                                           {"mat": "trousers", "z": (-30.0, 1.5), "inner": 4.6, "folds": 1.4},
                                           {"mat": "wrap", "z": (-30.0, -4.6)},
                                           {"mat": "vest", "z": (3.1, 8.4), "side": 1.6, "inner": 4.4},
                                           {"mat": "vest", "z": (3.1, 8.4), "back": 0.15, "inner": 4.4}]},
    "dress": True,
    "prop": {"kind": "cleaver", "grip": 1.5, "length": 7.0, "width": 2.6, "rings": 9},
    "gourd": {"at": (0.4, 4.1, 0.4), "r": (1.45, 0.95)},
}
# The Drowned Abbot (`abbot`): tall and gaunt, stooped, pale with the river, a waterlogged robe to the floor (weed hanging
# off its hem) with wide sleeves, a faded kasaya across it, long white hair loose from under a wide conical straw hat
# dripping, eyes glowing cold under its brim, prayer beads round his neck; a monk's ringed staff with a drowned bronze
# bell hung under its loop.
ABBOT = {
    "hip": 9.2, "hunch": 14.0,
    "legs": {"top": (1.3, -0.5), "foot": (1.6, 1.0, 0.6), "bones": (4.5, 4.4), "thigh": (1.1, 0.95), "shin": (0.95, 0.8), "knee": None,
             "boot": ((0.7, 0.0, -0.3), (1.5, 0.9, 0.6)), "plant": (0.8, -1.0)},
    "trunk": [{"at": (0.0, 0.0, 0.6), "r": (2.0, 2.8, 1.6), "paint": True}, {"at": (0.2, 0.0, 3.0), "r": (1.7, 2.4, 1.6), "paint": True},
              {"at": (0.2, 0.0, 5.4), "r": (2.0, 3.0, 2.1), "paint": True}],
    "neck": ((0.4, 0.0, 7.2), 0.9),
    "head": {"at": ((0.8, 0.0, 7.5), 1.9), "r": (1.8, 1.7, 2.0)},
    "face": {"kind": "human", "eyes": (1.65, 0.65, 0.25), "brow": (0.35, 0.6, 0.22), "brow_tilt": 14.0, "nose": (1.95, 0.0, -0.2),
             "mouth": (1.75, 0.45, -0.9), "ears": (-0.1, 1.7, 0.0), "hair": "loose", "glow": True},
    "arms": {"shoulder": (3.0, 5.6), "bones": (3.6, 3.4), "hint": (-0.6, 1.0, -1.0), "ball": None, "upper": (0.85, 0.8), "elbow": None,
             "lower": (0.8, 0.75), "wrap": None, "fist": (0.75, 0.7, 0.7), "guard": (2.4, 3.0, -4.2), "limp": (0.8, 3.8, -5.2, 0.3)},
    "paint": {"kind": "clothes", "zones": [{"mat": "kasaya", "diag": (4.4, 0.85)}, {"mat": "robe", "folds": 1.2}]},
    "dress": True,
    "robe": {"top": 1.4, "r": (2.5, 3.9), "lead": 0.6, "damp": True, "weed": 7},
    "sleeves": {"r": (1.0, 1.75), "over": 0.4},
    "hat": {"height": 3.2, "base": 1.6, "r": 3.1, "tilt": 24.0},
    "beads": {"n": 12, "r": (1.5, 1.7), "size": 0.42},
    "prop": {"kind": "staff", "below": 12.6, "above": 7.0, "r": 0.34, "loop": 1.0, "bell": 1.3},
}
# Elder Gu (`elder`): the trade house's master, portly and stately in a voluminous crimson robe trimmed in gold with wide
# sleeves (his hands folded in them), a black sash, his dark cape over his shoulders, his grey hair tied back in a tail, a
# drooping grey moustache and goatee, a gold abacus at his belt; the river's tide gathers in his palm.
ELDER = {
    "hip": 8.0,
    "legs": {"top": (1.6, -0.5), "foot": (2.0, 1.0, 0.6), "bones": (3.9, 3.8), "thigh": (1.4, 1.2), "shin": (1.15, 1.0), "knee": None,
             "boot": ((0.8, 0.0, -0.3), (1.7, 1.0, 0.7)), "plant": (1.0, -1.2)},
    "trunk": [{"at": (0.0, 0.0, 0.8), "r": (2.5, 3.3, 2.1), "paint": True}, {"at": (1.0, 0.0, 3.2), "r": (3.2, 3.5, 2.8), "paint": True},
              {"at": (0.3, 0.0, 5.8), "r": (2.4, 3.6, 2.4), "paint": True}],
    "neck": ((0.5, 0.0, 7.6), 1.1),
    "head": {"at": ((0.8, 0.0, 7.9), 2.1), "r": (2.0, 1.9, 2.2)},
    "face": {"kind": "human", "eyes": (1.85, 0.7, 0.3), "brow": (0.35, 0.65, 0.22), "brow_tilt": -8.0, "nose": (2.2, 0.0, -0.15),
             "mouth": (1.95, 0.55, -0.85), "ears": (-0.1, 1.9, 0.0), "beard": "moustache", "hair": "tail"},
    "arms": {"shoulder": (3.6, 6.0), "bones": (3.4, 3.2), "hint": (-0.6, 1.0, -1.0), "ball": None, "upper": (1.05, 0.95), "elbow": None,
             "lower": (0.95, 0.85), "wrap": None, "fist": (0.75, 0.7, 0.7), "guard": (2.9, 0.7, -4.4), "limp": (0.8, 4.4, -5.4, 0.3)},
    "paint": {"kind": "clothes", "zones": [{"mat": "trim", "z": (6.9, 7.8)}, {"mat": "sash", "z": (2.6, 3.5)}, {"mat": "robe", "folds": 1.3}]},
    "dress": True,
    "robe": {"top": 2.2, "r": (3.4, 4.5), "lead": 0.5, "trim_w": 0.7},
    "sleeves": {"r": (1.2, 2.0), "over": 0.6, "trim": True, "palm": True},
    "cape": {"top": 6.6, "bottom": 2.6, "back": 2.2, "r": (3.3, 3.9), "front": -0.6},
    "abacus": {"at": (1.4, 3.5, 2.8), "size": (1.2, 0.8)},
    "prop": {"kind": "tide"},
}
VARIANTS = {
    "chief": {"parts": CHIEF, "mats": {"body": "folk_skin", "limb": "folk_skin", "dark": "tan_boot", "joint": "folk_skin", "neck": "folk_skin",
                                       "skin": "folk_skin", "hand": "folk_skin", "hair": "tan_hair", "cord": "tan_sash", "sash": "tan_sash",
                                       "vest": "tan_vest", "trousers": "tan_trousers", "wrap": "tan_wrap", "steel": "cleaver_steel",
                                       "trim": "brass", "grip": "halberd_shaft", "gourd": "gourd", "maw": "maw"},
              "motion": {"idle": "chief_idle", "walk": "chief_waddle", "windup": "cleaver_raise", "attack": "cleaver_slam", "hurt": "chief_rock",
                         "death": "chief_fall"}},
    "abbot": {"parts": ABBOT, "mats": {"body": "drowned_skin", "limb": "drowned_skin", "dark": "abbot_dark", "joint": "drowned_skin",
                                       "neck": "drowned_skin", "skin": "drowned_skin", "hand": "drowned_skin", "hair": "abbot_hair",
                                       "robe": "abbot_robe", "kasaya": "abbot_kasaya", "trim": "abbot_kasaya", "hat": "abbot_hat", "weed": "weed",
                                       "bead": "abbot_dark", "grip": "halberd_shaft", "iron": "abbot_dark", "bell": "abbot_bell",
                                       "patina": "abbot_patina", "maw": "maw"},
              "motion": {"idle": "abbot_sway", "walk": "abbot_glide", "windup": "staff_raise", "attack": "staff_slam", "hurt": "abbot_rock",
                         "death": "abbot_collapse"}},
    "elder": {"parts": ELDER, "mats": {"body": "folk_skin", "limb": "folk_skin", "dark": "gu_shoe", "joint": "folk_skin", "neck": "folk_skin",
                                       "skin": "folk_skin", "hand": "folk_skin", "hair": "gu_hair", "robe": "gu_robe", "trim": "gu_gold",
                                       "sash": "gu_sash", "cape": "gu_cape", "orb": "rs_orb", "maw": "maw"},
              "motion": {"idle": "elder_stand", "walk": "elder_walk", "windup": "tide_draw", "attack": "tide_strike", "hurt": "elder_rock",
                         "death": "elder_fall"}},
    "gate": {"parts": GATE, "mats": {"body": "gg_jade", "limb": "gg_jade", "dark": "gg_jade_dark", "joint": "gg_bronze", "neck": "gg_jade_dark",
                                     "trim": "gg_bronze", "ring": "gg_ring"},
             "motion": {"idle": "ring_orbit", "walk": "ring_stomp", "windup": "rings_rise", "attack": "ring_sweep", "hurt": "ring_wobble",
                        "death": "kneel_crack"}},
    "sentinel": {"parts": SENTINEL, "mats": {"body": "sentinel_jade", "limb": "sentinel_jade", "dark": "sentinel_jade_dark",
                                             "joint": "sentinel_bronze", "neck": "sentinel_jade_dark", "trim": "sentinel_bronze",
                                             "shaft": "halberd_shaft", "blade": "halberd_blade"},
                 "motion": {"idle": "halberd_rest", "walk": "march", "windup": "halberd_back", "attack": "halberd_sweep", "hurt": "armor_rock",
                            "death": "topple_crack"}},
    "ape": {"parts": APE, "mats": {"body": "ape_fur", "limb": "ape_fur", "dark": "ape_skin", "joint": "ape_fur", "neck": "ape_fur",
                                   "pale": "ape_face", "mantle": "ape_mane", "maw": "maw", "boulder": "boulder", "moss": "boulder_moss",
                                   "leaf": "boulder_moss"},
            "motion": {"idle": "knuckle", "walk": "knuckle_lope", "windup": "hoist", "attack": "boulder_smash", "hurt": "knock",
                       "death": "topple_back"}},
    "guardian": {"parts": GUARDIAN, "mats": {"body": "sg_stone", "limb": "sg_stone", "dark": "sg_stone_dark", "joint": "sg_stone",
                                             "neck": "sg_stone", "maw": "sg_mouth", "moss": "sg_moss", "mantle": "sg_stone_dark",
                                             "bell": "sg_stone_dark"},
                 "motion": {"idle": "stand", "walk": "stomp", "windup": "fists_up", "attack": "double_slam", "hurt": "knock",
                            "death": "crumble"}},
    "monkey": {"parts": MONKEY, "mats": {"body": "monkey_fur", "limb": "monkey_fur", "dark": "monkey_skin", "joint": "monkey_fur",
                                         "neck": "monkey_fur", "pale": "monkey_skin", "mantle": "monkey_mantle", "leaf": "bamboo_leaf",
                                         "cane": "bamboo_cane", "node": "bamboo_node", "maw": "maw"},
               "motion": {"idle": "perch", "walk": "lope", "windup": "wind_shoot", "attack": "hurl", "hurt": "knock", "death": "tumble"}},
    "imp": {"parts": IMP, "mats": {"body": "imp_stone", "limb": "imp_limb", "dark": "imp_limb", "joint": "imp_limb", "neck": "imp_limb",
                                   "maw": "maw", "ochre": "peb_ochre", "slate": "peb_slate", "rust": "peb_rust"},
            "motion": {"idle": "toss", "walk": "waddle", "windup": "wind_throw", "attack": "throw", "hurt": "knock", "death": "crumble"}},
    "puppet": {"parts": PUPPET, "mats": {"body": "timber", "limb": "timber", "dark": "timber_dark", "joint": "brass", "sash": "puppet_jade",
                                         "wrap": "rope"},
               "motion": {"idle": "guard_sway", "walk": "march", "windup": "draw_palm", "attack": "palm_strike", "hurt": "rock_back",
                          "death": "joints_give"}},
}


def pose(B, action: str, f: int, view: float = 48.0) -> Pose:
    if B.parts.get("golem"):
        return _golem(B, action, f, view)                # M4: the gravity golem
    P = Pose()
    p, m = B.parts, B.mats
    st = B.style(action)
    lean = B.pick("lean", action, f) + p.get("hunch", 0.0)
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
    elif p.paint.kind == "temple":
        grain = limb = _temple(m, hip, tm, int(B.opts.get("seed", 0)))
    elif p.paint.kind == "fur":
        grain, limb = _fur(m, hip, tm), None
    elif p.paint.kind == "armor":
        grain = limb = _armor(m, hip, tm, p.paint)
    elif p.paint.kind == "clothes":
        grain = limb = _clothes(m, hip, tm, p.paint, bool(B.opts.get("bare")))
    elif p.paint.kind == "lamellar":
        grain = limb = _lamellar(m, hip, tm, p.paint, bool(B.opts.get("bare")))     # M4: General Kharn's armour

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
    if p.get("hunch"):
        hm = hm @ rot("b", p.hunch * 0.85)          # a hunched body holds its head up, its face to the front
    hc = up(p.head.at[0]) + hm @ v3(0.0, 0.0, p.head.at[1])
    P.add(E(hc, p.head.r, m.body, "head", hm, None if p.paint.kind in ("fur", "clothes", "lamellar") else grain))   # a face wears no clothes
    fc = p.face
    if fc.kind == "grin":
        _grin(P, B, action, f, hc, hm, grain, math.sin(math.radians(view)) > -0.5)
    elif fc.kind == "monkey":
        _monkey_face(P, B, action, f, hc, hm)
    elif fc.kind == "helm":
        _helm(P, B, action, f, hc, hm)
    elif fc.kind == "human":
        _human_face(P, B, action, f, hc, hm)
    else:
        _slits(P, B, action, f, hc, hm)
    if p.get("tail"):
        _tail(P, B, action, f, up)
    if p.get("mane"):
        _mane(P, B, action, f, hc, hm, up, tm, grain)
    ends, elbows = _arms(P, B, action, f, up, tm, limb, march)
    if p.get("dress"):
        _dress(P, B, action, f, up, tm, hip, hc, hm, ends, elbows)
    if p.get("studs"):
        _studs(P, B, up, tm, hc, hm, math.sin(math.radians(view)) > -0.5)
    if p.get("cracks"):
        _cracks(P, B, action, f, up, tm, hc, hm, math.sin(math.radians(view)) > -0.5)
    if p.get("armor"):
        _armor_parts(P, B, action, f, up, tm, hc, hm)
    if p.get("rings"):
        _bi_rings(P, B, action, f, hip)
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
    ends, elbows = {}, {}
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
              E(end, a_.fist, m.get("hand", m.dark), "arm%d" % s, tm))
        if p.get("qi") and s < 0:
            _qi(P, B, action, f, end, tm)
        if p.get("held") and s < 0 and p.held.get("kind") not in ("boulder", "halberd"):
            _held(P, B, action, f, end, tm)
        ends[s], elbows[s] = end, elbow
    if p.get("held") and p.held.get("kind") == "boulder":
        _boulder(P, B, action, f, ends, tm)
    if p.get("held") and p.held.get("kind") == "halberd":
        _halberd(P, B, action, f, ends, tm)
    return ends, elbows


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
    core, main, dim, glow = GLOWS[fc.get("glow", "ember")]
    for s in (1, -1):
        eye = hc + hm @ v3(ea, s * eb, ec)
        if dark:
            P.mark(eye, M.RAMPS[m.body][0])
            continue
        if st.get("squint"):
            P.mark(eye, dim)
            continue
        P.eye(eye, core)
        for d in ((0.0, 0.35, 0.0), (0.0, -0.35, 0.0), (0.0, 0.0, 0.35)):
            P.mark(eye + hm @ v3(*d), main)
        if st.get("glare") and facing:
            for d in ((0.3, 0.0, 0.8), (0.3, 0.7, 0.4), (0.3, -0.7, 0.4), (0.3, 0.0, -0.7)):
                P.glow.append((eye + hm @ v3(*d), glow))


# A grin face's glowing eyes: (core, main, squinting, glow) for the imp's ember and the guardian's jade (M1).
GLOWS = {"ember": (M.EMBER_CORE, M.EMBER, M.EMBER_DIM, M.EMBER_GLOW), "jade": (M.QI_BRIGHT, M.QI, M.QI_DIM, M.QI_GLOW)}


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
    if h.get("kind") == "shoot":
        _shoot(P, B, end, tm, action, f)
        return
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


# ================================================================================================= the stone guardian (M1)
def _temple(m, hip, tm, seed: int):
    """Warm temple stone: its grain a step dark in pits, a step lit in flecks (by the species' seed), moss over the
    tops of its shoulders and crown where the stone turns to the sky."""
    def temple(q, n):
        loc = (q - hip) @ tm
        nl = n @ tm
        pit = h01v(np.floor(loc[:, 0] * 1.3 + 40), np.floor(loc[:, 2] * 1.3 + 40) + np.floor(loc[:, 1] * 1.3), seed % 97 + 1) > 0.86
        fleck = h01v(np.floor(loc[:, 1] * 2.0 + 60), np.floor(loc[:, 2] * 2.0 + 60), seed % 89 + 2) > 0.93
        moss = (nl[:, 2] > 0.72) & (loc[:, 2] > 6.0) & (loc[:, 2] < 9.2) & (h01v(np.floor(loc[:, 0] * 0.8 + 70), np.floor(loc[:, 1] * 0.8 + 70), seed % 83 + 3) > 0.35)
        names = np.where(moss, m.moss, m.body).astype(object)
        return names, np.where(pit & ~moss, -1, np.where(fleck & ~moss, 1, 0)).astype(np.int16)
    return temple


def _mane(P, B, action: str, f: int, hc, hm, up, tm, paint) -> None:
    """The lion-dog's mane: spiral curls of darker stone round the back, the sides and the crown of its head; and its
    carved collar round the neck with a stone bell hanging at its throat."""
    p, m = B.parts, B.mats
    r = p.head.r
    for u, v, cr in p.mane:
        P.add(S(on(hc, r, hm, u, v, -cr * 0.25), cr, m.dark, "mane", paint))
    co = p.get("collar")
    if co:
        n0 = up(p.neck[0])
        for k in range(12):
            t = math.radians(k * 30.0)
            P.add(S(n0 + tm @ v3(math.cos(t) * 2.6, math.sin(t) * 3.0, -0.4), 0.85, m.dark, "collar", line=False))
        bell = n0 + tm @ v3(2.9, 0.0, -1.6)
        P.add(S(bell, co.bell, m.bell, "bell"))
        P.mark(bell + tm @ v3(co.bell * 0.9, 0.0, -co.bell * 0.4), M.RAMPS[m.dark][0])


def _cracks(P, B, action: str, f: int, up, tm, hc, hm, facing: bool = True) -> None:
    """Cracks over the stone (on the trunk's pieces and the head: (piece, points round and up it)), dark; alight with jade
    in its tell and its slam (the channel `glow`), and flaring as it breaks."""
    p, m = B.parts, B.mats
    g = B.pick("glow", action, f)
    if action == "death" and f < 2:
        g = 1.0
    pieces = [(up(t.at), t.r, tm) for t in p.trunk] + [(hc, p.head.r, hm)]
    for i, path in p.cracks:
        c, rad, mm = pieces[i]
        pts = [on(c, rad, mm, u, v, 0.15) for u, v in path]
        for a, b in zip(pts, pts[1:]):
            for k in range(4):
                q = a + (b - a) * (k / 4.0)
                if g > 0.5:
                    P.mark(q, M.QI_BRIGHT if k % 2 else M.QI)
                    if facing:
                        P.glow.append((q + mm @ v3(0.4, 0.0, 0.0), M.QI_GLOW))
                else:
                    P.mark(q, M.RAMPS[m.dark][0] if g <= 0.0 else M.QI_DIM)
    if f in B.style(action).get("dust", ()):
        for k in range(10):
            ang = math.radians(k * 36.0 + f * 20.0)
            rr = 3.0 + f * 1.4 + (k % 3) * 0.6
            P.fx.append((v3(8.6 + math.cos(ang) * rr, math.sin(ang) * rr, 0.3 + (k % 3) * 0.6), M.DUST if k % 2 else M.DUST_DIM))


# ================================================================================================= the bamboo monkey (M1)
def _fur(m, hip, tm):
    """Gold fur; an olive mantle over the back, the shoulders and the crown; the pale belly; its grain in fine streaks."""
    def fur(q, n):
        loc = (q - hip) @ tm
        nl = n @ tm
        mantle = ((nl[:, 0] < -0.15) | (nl[:, 2] > 0.55)) & (loc[:, 2] > 2.4)
        belly = (nl[:, 0] > 0.45) & (loc[:, 2] < 4.4) & (np.abs(loc[:, 1]) < 1.8)
        streak = ((loc[:, 2] * 1.4 + loc[:, 1] * 0.5) % 1.3 < 0.22) & ~belly
        names = np.where(belly, m.pale, np.where(mantle, m.mantle, m.body)).astype(object)
        return names, np.where(streak, -1, 0).astype(np.int16)
    return fur


def _monkey_face(P, B, action: str, f: int, hc, hm) -> None:
    """The monkey's face: a pale heart-shaped face and muzzle on the front of its head, big amber eyes with a dark pupil
    (glaring in the tell, squeezed shut when struck, dark when beaten), a nose and a mouth that chatters open, round ears
    on the sides, a tuft of bamboo leaves on its crown."""
    m, st, fc = B.mats, B.style(action), B.parts.face
    P.add(E(hc + hm @ v3(fc.disc[0]), fc.disc[1], m.pale, "face", hm, line=False))
    P.add(E(hc + hm @ v3(fc.muzzle[0]), fc.muzzle[1], m.pale, "face", hm))
    (ea, eb, ec) = fc.eyes
    dark = action == "death" and f >= st.get("dark_from", 99)
    for s in (1, -1):
        eye = hc + hm @ v3(ea, s * eb, ec)
        if dark or st.get("squint"):
            P.mark(eye, M.RAMPS[m.pale][0])
        else:
            P.eye(eye, M.MONKEY_EYE)
            P.mark(eye + hm @ v3(0.05, s * 0.35, 0.0), M.INKY)
            P.mark(eye + hm @ v3(0.0, 0.0, 0.45), M.RAMPS[m.mantle][0] if st.get("chatter") else M.RAMPS[m.pale][1])
        (ra, rb, rc), rr = fc.ears
        ear = hc + hm @ v3(ra, s * rb, rc)
        P.add(S(ear, rr, m.body, "ear%d" % s))
        P.mark(ear + hm @ v3(0.5, s * 0.1, 0.0), M.RAMPS[m.pale][1])
    P.mark(hc + hm @ v3(fc.nose), M.RAMPS[m.pale][0])
    open_ = B.pick("chatter", action, f)
    mouth = hc + hm @ v3(fc.mouth)
    if open_ > 0.3:
        P.add(E(mouth, (0.4, 0.75 * open_ + 0.3, 0.35 + 0.4 * open_), m.maw, "mouth", hm, line=False))
        P.mark(mouth + hm @ v3(0.3, 0.3, 0.3), M.IMP_TOOTH)
        P.mark(mouth + hm @ v3(0.3, -0.3, 0.3), M.IMP_TOOTH)
    else:
        P.mark(mouth, M.RAMPS[m.pale][0])
    if fc.get("brow"):
        # M2, the cliff ape: a heavy brow ridge over its eyes.
        P.add(E(hc + hm @ v3(fc.brow[0]), fc.brow[1], m.pale, "brow", hm, line=False))
    t0, leaves, (lr0, lr1, lh) = fc.tuft
    base = hc + hm @ v3(t0)
    for k, d in enumerate(leaves):
        tip = base + hm @ v3(d)
        P.add(L(base, tip, lr0, lr1, m.leaf, "tuft", line=False))


def _tail(P, B, action: str, f: int, up) -> None:
    """A long tail from the base of the back, sweeping back and down, then curling up into a loose spiral, swaying."""
    t, m, st = B.parts.tail, B.mats, B.style(action)
    phase = f / 8.0 * math.tau if st.get("tail_wave") else 0.6
    root = up(t.root)
    pts = [root]
    ang = math.radians(200.0 + 6.0 * math.sin(phase))
    q = np.array(root, float)
    for k, ln in enumerate(t.segs):
        ang -= math.radians(4.0 if k < 2 else 30.0 + 4.0 * math.sin(phase * 1.6 + k))
        q = q + v3(math.cos(ang) * ln * 0.8, 0.35 * ln * math.sin(phase + k * 0.7), -math.sin(ang) * ln * 0.8)
        q[2] = max(q[2], 0.6)
        pts.append(q.copy())
    n = len(pts) - 1
    for i in range(n):
        r0 = t.r[0] + (t.r[1] - t.r[0]) * i / n
        r1 = t.r[0] + (t.r[1] - t.r[0]) * (i + 1) / n
        P.add(L(pts[i], pts[i + 1], r0, r1, m.mantle if i < n - 3 else m.body, "tail", caps=i == 0))


# ================================================================================================= armoured constructs (M2)
def _armor(m, hip, tm, a):
    """Carved armour: lamellar rows across the torso and the limbs (a groove a step dark every `rows`), the plates' edges a
    step lit, the bronze belt and trim between `belt` heights."""
    def armor(q, n):
        loc = (q - hip) @ tm
        nl = n @ tm
        row = (loc[:, 2] % a.rows) < 0.22
        lit = ((loc[:, 2] % a.rows) > a.rows - 0.25) & (nl[:, 2] > -0.2)
        belt = (loc[:, 2] > a.belt[0]) & (loc[:, 2] < a.belt[1])
        names = np.where(belt, m.trim, m.body).astype(object)
        return names, np.where(row & ~belt, -1, np.where(lit & ~belt, 1, 0)).astype(np.int16)
    return armor


GLOW_EYES = {"gold": (M.RUNE_CORE, M.RUNE, M.RUNE_DIM, M.RUNE_GLOW), "jade": GLOWS["jade"]}


def _helm(P, B, action: str, f: int, hc, hm) -> None:
    """A carved helmet over the head: its dome and brim, a crest along its top, cheek guards; a stern mask under it, its
    eyes a glowing slit (flaring in the tell, squinting when struck, dark when it falls)."""
    m, st, fc = B.mats, B.style(action), B.parts.face
    P.add(E(hc + hm @ v3(fc.dome[0]), fc.dome[1], m.body, "helm", hm))
    P.add(E(hc + hm @ v3(fc.brim[0]), fc.brim[1], m.trim, "brim", hm))
    c0, c1, cr = fc.crest
    P.add(L(hc + hm @ v3(c0), hc + hm @ v3(c1), cr, cr * 0.7, m.trim, "crest"))
    ca, cb, cc = fc.cheeks[0]
    for s in (1, -1):
        P.add(E(hc + hm @ v3(ca, s * cb, cc), fc.cheeks[1], m.body, "cheek%d" % s, hm @ rot("a", s * 12.0)))
    P.add(E(hc + hm @ v3(fc.mask[0]), fc.mask[1], m[fc.get("mask_mat", "dark")], "mask", hm, line=fc.get("mask_mat") is not None))
    dark = action == "death" and f >= st.get("dark_from", 99)
    core, main, dim, glow = GLOW_EYES[fc.get("glow", "gold")]
    g = B.pick("glow", action, f)
    if fc.get("eaves"):
        # M2, the gate guardian: the crown's eave horns, sweeping out and up from its sides like a temple roof's.
        for s in (1, -1):
            pts = [hc + hm @ v3(x, s * y, z) for x, y, z in fc.eaves]
            for i in range(len(pts) - 1):
                P.add(L(pts[i], pts[i + 1], 0.7 - 0.2 * i, 0.5 - 0.2 * i, m.body, "eave%d" % s))
    if fc.get("brows"):
        # A stern mask: heavy brows over its eyes, a hard line of a mouth.
        (ba, bb, bc), br = fc.brows
        for s in (1, -1):
            P.add(E(hc + hm @ v3(ba, s * bb, bc), br, m[fc.get("mask_mat", "dark")], "brow%d" % s, hm @ rot("a", s * -14.0), line=False))
        P.mark(hc + hm @ v3(fc.mouth), M.RAMPS[m[fc.get("mask_mat", "dark")]][0])
        P.mark(hc + hm @ v3(fc.mouth[0], 0.35, fc.mouth[2]), M.RAMPS[m[fc.get("mask_mat", "dark")]][0])
        P.mark(hc + hm @ v3(fc.mouth[0], -0.35, fc.mouth[2]), M.RAMPS[m[fc.get("mask_mat", "dark")]][0])
    if fc.get("eyes"):
        ea, eb, ec = fc.eyes
        for s in (1, -1):
            q = hc + hm @ v3(ea, s * eb, ec)
            if dark:
                P.mark(q, M.RAMPS[m.dark][0])
            elif st.get("squint"):
                P.mark(q, dim)
            else:
                P.eye(q, core)
                P.mark(q + hm @ v3(0.0, s * 0.35, 0.0), main)
                if g >= 0.8:
                    for d in ((0.4, 0.0, 0.6), (0.4, s * 0.6, 0.2), (0.4, 0.0, -0.5)):
                        P.glow.append((q + hm @ v3(*d), glow))
        return
    sa, sb, sc = fc.slit
    for k in range(5):
        y = -sb + 2.0 * sb * k / 4.0
        q = hc + hm @ v3(sa - 0.1 * abs(y), y, sc)
        if dark:
            P.mark(q, M.RAMPS[m.dark][0])
        elif st.get("squint"):
            P.mark(q, dim)
        else:
            (P.eye if k in (1, 3) else P.mark)(q, core if k in (1, 3) else main)
            if g >= 0.8:
                P.glow.append((q + hm @ v3(0.4, 0.0, 0.5), glow))


def _armor_parts(P, B, action: str, f: int, up, tm, hc, hm) -> None:
    """The armour over the body: great pauldrons on its shoulders, plates hanging from its belt round its hips, gold runes
    on its cuirass (glowing in its tell and its blow, dark as it falls), cracks spreading over it as it dies."""
    p, m, st = B.parts, B.mats, B.style(action)
    a = p.armor
    (pa, pb, pc), pr = a.pauldrons
    for s in (1, -1):
        q = up((pa, s * pb, pc))
        P.add(E(q, pr, m.body, "pauldron%d" % s, tm @ rot("a", s * 25.0), _armor(m, q - tm @ v3(0.0, 0.0, 0.0), tm, p.paint)))
        P.add(E(q + tm @ v3(0.0, s * 0.3, -pr[2] * 0.6), (pr[0] * 1.02, pr[1] * 1.02, 0.3), m.trim, "pauldron%d" % s, tm @ rot("a", s * 25.0),
                line=False))
    n = a.tassets
    for k in range(n):
        ang = math.radians(-80.0 + 160.0 * k / (n - 1.0))
        q = up((math.cos(ang) * 2.2, math.sin(ang) * 2.9, -0.4))
        mm = tm @ rot("c", math.degrees(ang)) @ rot("b", -12.0)
        P.add(E(q, a.tasset, m.body if k % 2 else m.dark, "tasset", mm))
    dark = action == "death" and f >= st.get("dark_from", 99)
    g = B.pick("glow", action, f)
    pieces = [(up(t.at), t.r, tm) for t in p.trunk] + [(hc, p.head.r, hm)]
    for i, u, v in a.runes:
        c, rad, mm = pieces[i]
        q = on(c, rad, mm, u, v, 0.15)
        for d in ((0.0, 0.0, 0.0), (0.0, 0.35, 0.0), (0.0, 0.0, 0.35), (0.0, -0.35, -0.35)):
            P.mark(q + mm @ v3(*d), M.RAMPS[m.dark][0] if dark else (M.RUNE_CORE if g >= 0.8 else M.RUNE))
        if g >= 0.8 and not dark:
            P.glow.append((q + mm @ v3(0.5, 0.0, 0.4), M.RUNE_GLOW))
    crack = B.pick("crack", action, f)
    if crack > 0.0:
        seed = int(B.opts.get("seed", 0))
        for i, (c, rad, mm) in enumerate(pieces[:3] + pieces[3:]):
            for k in range(int(2 + 4 * crack)):
                u0 = (seed * 7 + i * 61 + k * 97) % 360 - 180.0
                v0 = (seed * 3 + i * 29 + k * 53) % 120 - 60.0
                for t in range(4):
                    P.mark(on(c, rad, mm, u0 + t * 9.0 * (1 if k % 2 else -1), v0 - t * 11.0, 0.15), M.CRACK)


# ================================================================================================= the people of size (M2)
# The bosses who are people (Big Toad Tan, the Drowned Abbot, Elder Gu) are sculpted on this plan's body, as the puppet
# and the guardians are, not cast in the shared character body: a boss needs the bulk and posture of his own that the one
# figure body cannot take (decision 43's figure is the player's and the villagers'). The body is drawn first (AGENTS.md
# rule 4: the unclothed sculpture, `opts.bare`, reviewed in every action and facing), then dressed over it: the clothes
# are paint over the body's own parts (`paint` kind "clothes": its zones) and parts laid over it (a robe's skirt, wide
# sleeves, a hat, a vest's flaps), then the props in his hands (the cleaver, the ringed staff and its bell, the abacus and
# the tide's orb).
#
# Face kind "human": a skin head with heavy brows, eyes (dark, a glint; glowing for the drowned), a nose, a mouth line
# (a wide toad's grin, a stern line), ears, and its hair and beard: `hair` (a topknot, a tied tail, long loose hair) and
# `beard` (stubble, a drooping moustache and goatee).
def _clothes(m, hip, tm, c, bare: bool):
    """The clothes over a person's trunk and limbs, by zones in the trunk's frame (`c.zones`, the first that holds wins):
    each a material and its bounds (z: heights; front/back: the normal's lean; side: |y| past it). `bare`: the body's
    own skin (the review of the body before it is dressed)."""
    zones = c.zones

    def clothes(q, n):
        loc = (q - hip) @ tm
        nl = n @ tm
        names = np.full(len(q), m.skin, dtype=object)
        if bare:
            return names, np.zeros(len(q), dtype=np.int16)
        done = np.zeros(len(q), dtype=bool)
        bias = np.zeros(len(q), dtype=np.int16)
        for zn in zones:
            sel = ~done
            if "z" in zn:
                sel &= (loc[:, 2] >= zn["z"][0]) & (loc[:, 2] <= zn["z"][1])
            if "front" in zn:
                sel &= nl[:, 0] > zn["front"]
            if "back" in zn:
                sel &= nl[:, 0] < zn["back"]
            if "side" in zn:
                sel &= np.abs(loc[:, 1]) > zn["side"]
            if "inner" in zn:
                sel &= np.abs(loc[:, 1]) < zn["inner"]
            if "diag" in zn:
                # A band across the chest from one shoulder to the other hip (a kasaya, a baldric).
                a0, w = zn["diag"]
                sel &= np.abs((loc[:, 2] - a0) - loc[:, 1] * 0.9) < w
            names = np.where(sel, m[zn["mat"]], names).astype(object)
            if zn.get("folds"):
                fold = ((loc[:, 1] * 1.3 + loc[:, 2] * 0.25) % zn["folds"]) < 0.3
                bias = np.where(sel & fold, -1, bias)
            if zn.get("trim"):
                edge = sel & (np.abs(loc[:, 2] - zn["z"][0]) < zn["trim"])
                names = np.where(edge, m.trim, names).astype(object)
            done |= sel
        return names, bias
    return clothes


def _human_face(P, B, action: str, f: int, hc, hm) -> None:
    """A person's face (M2): heavy brows, eyes (a dark pupil and a glint, or the drowned's cold glow), a nose, a mouth
    (a wide grin, a hard line; open in a roar), ears; the hair (a topknot, a tied tail, long loose hair) and the beard
    (stubble, a drooping moustache and goatee)."""
    m, st, fc = B.mats, B.style(action), B.parts.face
    hr = B.parts.head.r
    dark = action == "death" and f >= st.get("dark_from", 99)
    ea, eb, ec = fc.eyes
    for s in (1, -1):
        eye = hc + hm @ v3(ea, s * eb, ec)
        P.add(E(hc + hm @ v3(ea - 0.25, s * eb, ec + 0.55), fc.brow, m.hair, "brow%d" % s, hm @ rot("a", s * fc.get("brow_tilt", 0.0)), line=False))
        if dark or st.get("squint"):
            P.mark(eye, M.RAMPS[m.skin][0])
        elif fc.get("glow"):
            eye_c, dim_c, glow_c = (M.DROWNED_EYE, M.DROWNED_EYE_DIM, M.DROWNED_GLOW) if fc.glow is True else FACE_GLOWS[fc.glow]
            P.eye(eye, eye_c)
            P.mark(eye + hm @ v3(0.0, s * 0.35, 0.0), dim_c)
            if st.get("glare"):
                P.glow.append((eye + hm @ v3(0.4, 0.0, 0.4), glow_c))
        else:
            P.eye(eye, M.INKY)
            P.mark(eye + hm @ v3(0.0, 0.0, 0.4), M.RAMPS[m.skin][4])
        ra, rb, rc = fc.ears
        P.add(E(hc + hm @ v3(ra, s * rb, rc), (0.55, 0.35, 0.8), m.skin, "ear%d" % s, hm))
    P.add(S(hc + hm @ v3(fc.nose), 0.5, m.skin, "nose"))
    (ma, mb, mc) = fc.mouth
    roar = B.pick("roar", action, f)
    if roar > 0.3:
        P.add(E(hc + hm @ v3(ma, 0.0, mc - 0.2), (0.4, mb, 0.35 + 0.45 * roar), m.maw, "mouth", hm, line=False))
        for y in (-mb * 0.6, 0.0, mb * 0.6):
            P.mark(hc + hm @ v3(ma + 0.25, y, mc + 0.1), M.IMP_TOOTH)
    else:
        y = -mb
        while y <= mb + 1e-6:
            P.mark(hc + hm @ v3(ma - 0.12 * abs(y) * fc.get("grin", 0.0), y, mc + fc.get("grin", 0.0) * 0.18 * abs(y)), M.RAMPS[m.skin][0])
            y += 0.4
    bd = fc.get("beard")
    if bd == "stubble":
        for k in range(14):
            u = -60.0 + 120.0 * (k % 7) / 6.0
            v = -35.0 - 12.0 * (k // 7)
            P.mark(on(hc, hr, hm, u, v, 0.1), M.RAMPS[m.hair][2])
    elif bd == "moustache":
        for s in (1, -1):
            p0 = hc + hm @ v3(ma + 0.1, s * 0.35, mc + 0.35)
            p1 = p0 + hm @ v3(0.2, s * 1.0, -0.6)
            p2 = p1 + hm @ v3(-0.1, s * 0.3, -1.6)
            P.add(L(p0, p1, 0.32, 0.26, m.hair, "moustache", line=False), L(p1, p2, 0.26, 0.12, m.hair, "moustache", line=False))
        g0 = hc + hm @ v3(ma - 0.2, 0.0, mc - 0.5)
        P.add(L(g0, g0 + hm @ v3(0.3, 0.0, -1.9), 0.45, 0.12, m.hair, "goatee", line=False))
    hair = fc.get("hair")
    if hair == "topknot":
        P.add(E(hc + hm @ v3(-0.4, 0.0, hr[2] * 0.55), (hr[0] * 0.95, hr[1] * 0.92, hr[2] * 0.6), m.hair, "hair", hm))
        knot = hc + hm @ v3(-0.5, 0.0, hr[2] + 0.6)
        P.add(S(knot, 0.95, m.hair, "knot"), E(knot + hm @ v3(0.0, 0.0, -0.75), (0.9, 0.9, 0.25), m.cord, "knot_band", hm, line=False))
    elif hair == "tail":
        P.add(E(hc + hm @ v3(-0.55, 0.0, hr[2] * 0.55), (hr[0] * 0.95, hr[1] * 0.97, hr[2] * 0.62), m.hair, "hair", hm))
        t0 = hc + hm @ v3(-hr[0] * 0.9, 0.0, hr[2] * 0.3)
        sw = 0.4 * math.sin(f * 0.9) if action in ("idle", "walk") else 0.0
        t1 = t0 + hm @ v3(-1.0, sw, -2.2)
        t2 = t1 + hm @ v3(-0.3, sw, -2.4)
        P.add(L(t0, t1, 0.55, 0.5, m.hair, "tail"), L(t1, t2, 0.5, 0.25, m.hair, "tail"))
    elif hair == "loose":
        P.add(E(hc + hm @ v3(-0.35, 0.0, hr[2] * 0.4), (hr[0] * 1.02, hr[1] * 1.04, hr[2] * 0.72), m.hair, "hair", hm))
        for k in range(5):
            y = (k - 2) * 0.7
            p0 = hc + hm @ v3(-hr[0] * 0.75, y * 1.1, hr[2] * 0.1)
            p1 = p0 + hm @ v3(-0.6, y * 0.25, -2.6) + v3(0.0, 0.0, 0.0)
            p2 = p1 + hm @ v3(-0.2, y * 0.15, -2.6)
            P.add(L(p0, p1, 0.5, 0.42, m.hair, "locks", line=False), L(p1, p2, 0.42, 0.18, m.hair, "locks", line=False))


# M4: a face's glowing eyes by name (`face.glow`; True is the drowned's): the eye, the mark beside it, the glare.
FACE_GLOWS = {"presence": (M.PRES_EYE, M.PRES_EYE_DIM, M.PRES_GLOW)}


def _robe(P, B, action: str, f: int, hip, tm, bare: bool) -> None:
    """A long robe's skirt from the waist to the floor over the legs (a bell, swaying as he walks, flattening into a heap
    as he collapses), its hem trimmed, weed hanging off it (the drowned's), and its sleeves are the arms' (`_sleeves`)."""
    p, m, st = B.parts, B.mats, B.style(action)
    rb = p.get("robe")
    if not rb or bare:
        return
    heap = B.pick("heap", action, f)
    sw = 0.6 * math.sin(f / 8.0 * math.tau) if st.get("kind") == "march" else 0.0
    top = hip + tm @ v3(0.2, 0.0, rb.top)
    bot = v3(hip[0] * 0.6 + sw * 0.6 + rb.lead, 0.0, rb.get("hem", 0.3))
    bot = bot + (v3(hip[0], 0.0, 0.2) - bot) * heap
    r0, r1 = rb.r[0], rb.r[1] * (1.0 + 0.5 * heap)
    if heap > 0.0:
        top = top + (v3(top[0], top[1], 1.6) - top) * heap
    P.add(L(top, bot, r0, r1, m.robe, "robe", _robe_paint(m, top, bot, r1, rb), caps=False))
    P.add(E(bot + v3(0.0, 0.0, 0.15), (r1 * 1.0, r1 * 1.0, 0.45), m.robe, "hem", None, _robe_paint(m, top, bot, r1, rb)))
    for k in range(rb.get("weed", 0)):
        ang = math.radians(k * 360.0 / rb.weed + 20.0)
        q0 = bot + v3(math.cos(ang) * r1 * 0.95, math.sin(ang) * r1 * 0.95, 0.9 + 0.6 * (k % 2))
        P.add(L(q0, q0 + v3(0.3 * math.cos(ang), 0.3 * math.sin(ang), -0.9 + 0.2 * math.sin(f + k)), 0.3, 0.12, m.weed, "weed", line=False))


def _robe_paint(m, top, bot, r1: float, rb):
    """The robe's skirt: its cloth in long folds down it, its hem trimmed, damp streaks a step darker (the drowned's)."""
    axis = (bot - top) / max(1e-6, float(np.linalg.norm(bot - top)))

    def paint(q, n):
        rel = q - top
        along = rel @ axis
        ang = np.arctan2(rel[:, 1], rel[:, 0])
        fold = ((ang * 2.6) % 1.0) < 0.22
        hem = along > float(np.linalg.norm(bot - top)) - rb.get("trim_w", 0.0) if rb.get("trim_w") else np.zeros(len(q), dtype=bool)
        names = np.where(hem, m.trim, m.robe).astype(object)
        damp = (((ang * 4.0 + along * 0.3) % 1.0) < 0.12) & bool(rb.get("damp"))
        return names, np.where(fold | damp, -1, 0).astype(np.int16)
    return paint


def _sleeves(P, B, action: str, f: int, ends: dict, elbows: dict, bare: bool) -> None:
    """Wide sleeves flaring from the elbow to past the wrist over the forearm, their cuffs trimmed."""
    sl = B.parts.get("sleeves")
    if not sl or bare:
        return
    m = B.mats
    for s in (1, -1):
        e, w = elbows[s], ends[s]
        d = w - e
        ln = float(np.linalg.norm(d)) or 1.0
        over = sl.over
        if s == (1 if sl.get("palm") == "left" else -1) and sl.get("palm") and action in ("windup", "attack"):
            over = -1.3                                     # the sleeve pushed back off the palm that throws the tide
        cuff = e + d * (1.0 + over / ln)
        P.add(L(e, cuff, sl.r[0], sl.r[1], m.robe, "sleeve%d" % s))
        if sl.get("trim"):
            P.add(L(cuff - d / ln * 0.55, cuff - d / ln * 0.1, sl.r[1] * 1.04, sl.r[1] * 1.04, m.trim, "cuff%d" % s, caps=False, line=False))


def _hat(P, B, action: str, f: int, hc, hm, bare: bool) -> None:
    """A wide conical hat of woven straw, dark with the river (the drowned abbot's), dripping off its brim."""
    h = B.parts.get("hat")
    if not h or bare:
        return
    m = B.mats
    tilt = B.pick("hat_tilt", action, f) + h.get("tilt", 0.0)
    hh = hm @ rot("b", tilt)
    apex = hc + hh @ v3(0.2, 0.0, h.height)
    rim = hc + hh @ v3(0.0, 0.0, h.base)
    P.add(L(apex, rim, 0.25, h.r, m.hat, "hat", _hat_paint(m, apex, hh), caps=False))
    P.add(E(rim, (h.r, h.r, 0.3), m.hat, "brim", hh, _hat_paint(m, apex, hh)))
    if action != "death":
        for k in range(4):
            ang = math.radians(k * 90.0 + 40.0)
            u = ((f * 0.27 + k * 0.31) % 1.0)
            P.fx.append((rim + hh @ v3(math.cos(ang) * h.r, math.sin(ang) * h.r, 0.0) + v3(0.0, 0.0, -0.6 - u * 4.0), M.DRIP))


def _hat_paint(m, apex, hh):
    def paint(q, n):
        rel = (q - apex) @ hh
        ang = np.arctan2(rel[:, 1], rel[:, 0])
        weave = ((ang * 5.0) % 1.0 < 0.18) | ((np.hypot(rel[:, 0], rel[:, 1]) * 1.4) % 1.0 < 0.18)
        return np.full(len(q), m.hat, dtype=object), np.where(weave, -1, 0).astype(np.int16)
    return paint


def _beads(P, B, up, tm) -> None:
    """Prayer beads round his neck, big and dark."""
    bd = B.parts.get("beads")
    if not bd:
        return
    m = B.mats
    n0 = up(B.parts.neck[0])
    for k in range(bd.n):
        t = math.radians(k * 360.0 / bd.n)
        q = n0 + tm @ v3(math.cos(t) * bd.r[0] + 0.4, math.sin(t) * bd.r[1], -0.9 - 0.9 * max(0.0, math.cos(t)))
        P.add(S(q, bd.size, m.bead, "beads", line=False))


def _cleaver(P, B, action: str, f: int, ends: dict, tm) -> None:
    """Big Toad Tan's Mudwater Cleaver: a heavy broad chopping blade on a short grip, nine brass rings along its spine
    (the Mudwater bandits' chief's), held in his right hand: on his shoulder at rest, raised over his head in both hands in
    his tell, slammed down before him on the blow; dropped beside him as he falls."""
    h, m, st = B.parts.prop, B.mats, B.style(action)
    hand = ends[-1]
    d = v3(B.pick("blade", action, f, st.get("blade_rest", (-0.55, -0.15, 0.82))))
    d = tm @ (d / float(np.linalg.norm(d)))
    if action == "death" and f >= 3:
        hand = v3(hand[0] + 1.2, hand[1] - 1.6, 0.4)
        d = v3(0.8, -0.6, 0.0) / 1.0
    side = np.cross(d, tm @ v3(1.0, 0.0, 0.0))
    if float(np.linalg.norm(side)) < 0.2:
        side = np.cross(d, v3(0.0, 0.0, 1.0))
    side = side / float(np.linalg.norm(side))
    grip0 = hand - d * h.grip * 0.5
    base = hand + d * h.grip * 0.5
    P.add(L(grip0, base, 0.35, 0.35, m.grip, "grip"), S(grip0, 0.42, m.trim, "pommel"))
    P.add(E(base, (0.4, 1.1, 0.75), m.trim, "guard", np.stack([d, side, np.cross(d, side)], axis=1)))
    # The blade: broad, widening toward its end, its back (spine) on `side`, its edge on the other.
    L_, W = h.length, h.width
    for k in range(3):
        u = (k + 0.5) / 3.0
        c = base + d * (L_ * u) - side * (W * (0.15 + 0.1 * u))
        P.add(E(c, (L_ / 3.0 * 0.62, W * (0.55 + 0.25 * u), 0.22), m.steel, "blade",
                np.stack([d, side, np.cross(d, side)], axis=1), _blade_paint(m, base, d, side, W)))
    for k in range(h.rings):
        q = base + d * (L_ * (0.12 + 0.8 * k / (h.rings - 1.0))) + side * (W * 0.38)
        P.add(S(q, 0.45, m.trim, "rings", line=False))
    if action == "attack" and f in st.get("dust", ()):
        tip = base + d * L_
        for k in range(10):
            ang = math.radians(k * 36.0 + f * 20.0)
            rr = 2.0 + f * 1.3 + (k % 3) * 0.6
            P.fx.append((v3(tip[0] + math.cos(ang) * rr, tip[1] + math.sin(ang) * rr, 0.3 + (k % 3) * 0.5), M.DUST if k % 2 else M.DUST_DIM))


def _blade_paint(m, base, d, side, W):
    def paint(q, n):
        rel = q - base
        v = rel @ side
        edge = v < -W * 0.55
        return np.full(len(q), m.steel, dtype=object), np.where(edge, 1, 0).astype(np.int16)
    return paint


def _gourd(P, B, up, tm) -> None:
    """A wine gourd hanging at his hip on a red cord (Big Toad Tan drinks from it at half his health)."""
    g = B.parts.get("gourd")
    if not g:
        return
    m = B.mats
    q = up(g.at)
    P.add(S(q, g.r[0], m.gourd, "gourd"), S(q + tm @ v3(0.0, 0.0, g.r[0] + g.r[1] * 0.6), g.r[1], m.gourd, "gourd"))
    P.add(L(q + tm @ v3(0.0, 0.0, g.r[0] + g.r[1] * 1.4), up((g.at[0], g.at[1] * 0.7, g.at[2] + 2.2)), 0.22, 0.22, m.cord, "cord", line=False))


def _staff(P, B, action: str, f: int, ends: dict, tm) -> None:
    """The Drowned Abbot's ringed staff (a monk's khakkhara): a long staff in his right hand, an iron loop at its head with
    rings hanging off it, and a drowned temple bell of verdigris bronze hung under the loop; struck down on the floor on
    his blow, the bell tolling in rings of sound and water."""
    h, m, st = B.parts.prop, B.mats, B.style(action)
    hand = ends[-1]
    d = v3(B.pick("staff", action, f, (-0.16, -0.06, 1.0)))     # upright against his stoop
    d = tm @ (d / float(np.linalg.norm(d)))
    if action == "death" and f >= 3:
        hand = v3(hand[0] + 1.6, hand[1] - 2.0, 0.4)
        d = v3(0.9, -0.4, 0.0) / float(np.linalg.norm(v3(0.9, -0.4, 0.0)))
    butt = hand - d * h.below
    head = hand + d * h.above
    P.add(L(butt, head, h.r, h.r, m.grip, "staff"))
    side = np.cross(d, v3(0.0, 0.0, 1.0))
    if float(np.linalg.norm(side)) < 0.2:
        side = np.cross(d, tm @ v3(1.0, 0.0, 0.0))
    side = side / float(np.linalg.norm(side))
    up_ = np.cross(side, d)
    loop_c = head + d * h.loop
    for k in range(12):
        t = math.radians(k * 30.0)
        P.add(S(loop_c + (d * math.cos(t) + side * math.sin(t)) * h.loop, 0.3, m.iron, "loop", line=False))
    for s in (1, -1):
        q = loop_c + side * s * h.loop * 0.95 - d * 0.6
        P.add(S(q, 0.42, m.iron, "staff_ring", line=False))
    swing = 0.5 * math.sin(f * 1.3) if action in ("idle", "walk") else (1.0 if action == "windup" else 0.3)
    bell_top = loop_c - d * h.loop + side * 0.0
    bell = bell_top - v3(0.0, 0.0, h.bell * 1.1) + side * swing * 0.6
    P.add(L(bell_top, bell + v3(0.0, 0.0, h.bell * 0.5), 0.15, 0.15, m.iron, "bell_cord", line=False))
    P.add(E(bell, (h.bell * 0.85, h.bell * 0.85, h.bell * 1.05), m.bell, "bell", None, _bell_paint(m, bell, h.bell)))
    P.add(E(bell - v3(0.0, 0.0, h.bell * 0.75), (h.bell * 1.05, h.bell * 1.05, 0.3), m.bell, "bell_lip"))
    if action == "attack" and f in st.get("toll", ()):
        k0 = f - min(st.get("toll", (1,)))
        rr = 3.0 + 4.0 * k0 + 1.5
        foot = v3(butt[0], butt[1], 0.3)
        for k in range(28):
            ang = math.radians(k * 360.0 / 28.0)
            P.fx.append((foot + v3(math.cos(ang) * rr, math.sin(ang) * rr * 0.95, 0.2), M.TOLL if k % 2 else M.SPLASH_DIM))
        for k in range(6):
            ang = math.radians(k * 60.0 + 30.0)
            P.fx.append((bell + v3(math.cos(ang) * (h.bell + 1.2 + k0), math.sin(ang) * (h.bell + 1.2 + k0), 0.4 * (k % 2)), M.TOLL))


def _bell_paint(m, c, r):
    def paint(q, n):
        rel = q - c
        band = np.abs(rel[:, 2] + r * 0.2) < 0.22
        patina = ((rel[:, 0] * 1.7 + rel[:, 1] * 1.3) % 1.4) < 0.3
        return np.where(patina & ~band, m.patina, m.bell).astype(object), np.where(band, 1, 0).astype(np.int16)
    return paint


def _abacus(P, B, up, tm) -> None:
    """Elder Gu's gold abacus hanging at his belt: a small frame and its beads."""
    a = B.parts.get("abacus")
    if not a:
        return
    m = B.mats
    q = up(a.at)
    mm = tm @ rot("c", 70.0)
    P.add(E(q, (a.size[0], 0.25, a.size[1]), m.trim, "abacus", mm))
    for k in range(4):
        for j in range(3):
            P.mark(q + mm @ v3(-a.size[0] * 0.6 + k * a.size[0] * 0.4, 0.3, -a.size[1] * 0.4 + j * a.size[1] * 0.4), M.RAMPS[m.cape][1])


def _tide(P, B, action: str, f: int, ends: dict, tm) -> None:
    """Elder Gu's tide palm: river water gathering in a swirling orb at his drawn-back palm in his tell, thrown forward in
    a burst on the blow."""
    q = B.pick("tide", action, f)
    if q <= 0.0:
        return
    m, hand = B.mats, ends[-1]
    if action != "attack" or f < 1:
        # The orb: a ball of river water over his palm, swelling as the river spirals up into it (`tide` 0..1).
        c = hand + tm @ v3(0.3, 0.0, 1.1)
        r = 0.6 + 1.3 * min(q, 1.0)
        P.add(S(c, r, m.orb, "orb", line=False))
        P.glow.append((c + v3(0.0, 0.0, r * 0.55) + tm @ v3(-r * 0.3, 0.0, 0.0), M.RS_ORB_GLINT))
        for k in range(12):
            ang = math.radians(k * 30.0 + f * 40.0)
            rr = r + 0.7
            P.glow.append((c + tm @ v3(math.cos(ang) * rr * 0.6, math.sin(ang) * rr, math.sin(ang * 2.0) * rr * 0.5), M.TIDE if k % 3 else M.TIDE_CORE))
        for k in range(10):
            u = ((k * 0.097 + f * 0.23) % 1.0)
            ang = u * 3.0 * math.tau + k
            rr = r + 0.8 + 3.5 * (1.0 - u)
            P.fx.append((c + v3(math.cos(ang) * rr * 0.7, math.sin(ang) * rr, -(1.0 - u) * 4.0 * min(q, 1.0)), M.SPLASH if k % 3 else M.SPLASH_DIM))
        return
    # The blow: the orb thrown off his palm bursts into a crescent wave before him (`tide`: how far it has spread).
    c = hand + tm @ v3(1.0 + 2.4 * q, 0.0, 0.2)
    rr = 1.8 + 2.2 * q
    for j in range(9):
        a = math.radians(-64.0 + j * 16.0)
        P.add(S(c + tm @ v3(-(1.0 - math.cos(a)) * rr * 0.7, math.sin(a) * rr, 0.4 * math.cos(a)), 0.85 - 0.3 * q, m.orb, "wave", line=False))
    for k in range(26):
        ang = math.radians(k * 360.0 / 26.0)
        P.glow.append((c + tm @ v3(-abs(math.cos(ang)) * 0.7, math.cos(ang) * (rr + 0.6), math.sin(ang) * (rr * 0.5 + 0.6)),
                       M.TIDE if k % 2 else M.TIDE_CORE))
    for k in range(12):
        P.fx.append((c + tm @ v3(0.6 + k * 0.45, (k % 3 - 1) * (1.0 + q), (k % 2) * 0.8 - 0.2), M.SPLASH if k % 2 else M.SPLASH_DIM))


def _dress(P, B, action: str, f: int, up, tm, hip, hc, hm, ends: dict, elbows: dict) -> None:
    """A person's clothes and props over the body (`opts.bare` leaves the body as it is, for its review)."""
    p = B.parts
    bare = bool(B.opts.get("bare"))
    _robe(P, B, action, f, hip, tm, bare)
    _sleeves(P, B, action, f, ends, elbows, bare)
    _hat(P, B, action, f, hc, hm, bare)
    if bare:
        return
    if p.get("m4"):
        _m4_wear(P, B, action, f, up, tm, hip, hc, hm, ends, elbows)       # M4: what the late game's people of size wear
    _beads(P, B, up, tm)
    _gourd(P, B, up, tm)
    _abacus(P, B, up, tm)
    pr = p.get("prop")
    if pr and pr.kind == "cleaver":
        _cleaver(P, B, action, f, ends, tm)
    elif pr and pr.kind == "staff":
        _staff(P, B, action, f, ends, tm)
    elif pr and pr.kind == "tide":
        _tide(P, B, action, f, ends, tm)
    elif pr and pr.kind in M4_PROPS:
        M4_PROPS[pr.kind](P, B, action, f, ends, tm)
    if p.get("cape"):
        # A cape over his shoulders and down his back.
        cp = p.cape
        top = up((-0.6, 0.0, cp.top))
        bot = v3(hip[0] - cp.back, 0.0, cp.bottom)
        P.add(L(top, bot, cp.r[0], cp.r[1], B.mats.cape, "cape", caps=False, clip=lambda qs, c_=hip: (qs - c_)[:, 0] < cp.front))


def _bi_rings(P, B, action: str, f: int, hip) -> None:
    """M2, the gate guardian's two jade bi rings: discs with a hole, standing upright, orbiting it on opposite sides at its
    chest's height (`orbit`), each turning (`spin`); spun up and risen in its tell, whirled out wide round it on the blow
    (trailing arcs of jade light), wobbling when it is struck, dropped to the floor as it dies."""
    rg, m, st = B.parts.rings, B.mats, B.style(action)
    orbit = B.pick("orbit", action, f)
    spin = B.pick("spin", action, f)
    rise = B.pick("rise", action, f)
    out = B.pick("out", action, f, 1.0)
    drop = B.pick("drop", action, f)
    wob = B.pick("wobble", action, f)
    for k in range(rg.n):
        ang = math.radians(orbit + 360.0 * k / rg.n + 20.0)
        rr = rg.orbit * out
        c = v3(hip[0] * 0.3 + math.cos(ang) * rr, math.sin(ang) * rr, (rg.z + rise) * (1.0 - drop) + drop * rg.tube)
        radial = v3(math.cos(ang), math.sin(ang), 0.0)
        tang = v3(-math.sin(ang), math.cos(ang), 0.0)
        upv = v3(0.0, 0.0, 1.0)
        # Its face toward the guardian (standing upright), or lying flat once dropped; tilted as it wobbles.
        mm = np.stack([tang, upv, radial], axis=1) if drop < 0.5 else np.stack([tang, radial, upv], axis=1)
        mm = mm @ rot("a", wob * (1 if k else -1))
        for j in range(rg.beads):
            t = math.radians(j * 360.0 / rg.beads + spin)
            q = c + mm @ v3(math.cos(t) * rg.r, math.sin(t) * rg.r, 0.0)
            P.add(S(q, rg.tube, m.ring, "ring%d" % k))
        # The ring's carving: notches round its face, a glint.
        for j in range(4):
            t = math.radians(j * 90.0 + spin + 45.0)
            P.mark(c + mm @ v3(math.cos(t) * rg.r, math.sin(t) * rg.r, rg.tube * 0.9), M.RAMPS[m.ring][1])
        if action == "attack" and f in st.get("trail", ()):
            for j in range(10):
                a2 = ang - math.radians(8.0 + j * 9.0)
                P.fx.append((v3(math.cos(a2) * rr, math.sin(a2) * rr, c[2] - 0.2 * j), M.QI if j % 2 else M.QI_DIM))
        if B.pick("glow", action, f) >= 0.8:
            P.glow.append((c + v3(0.0, 0.0, rg.r + rg.tube + 0.4), M.QI_GLOW))


def _halberd(P, B, action: str, f: int, ends: dict, tm) -> None:
    """The halberd: a dark shaft through both hands (the butt past the left, the head past the right), its bronze-edged
    blade an axe's crescent to one side of the head and a spike before it, a gold rune on the shaft; the sweep trails an
    arc of jade light."""
    h, m, st = B.parts.held, B.mats, B.style(action)
    r_, l_ = ends[-1], ends[1]
    d = r_ - l_
    d = d / max(1e-6, float(np.linalg.norm(d)))
    butt = l_ - d * h.shaft[0]
    head = r_ + d * h.shaft[1]
    P.add(L(butt, head, h.r, h.r, m.shaft, "shaft"))
    side = np.cross(d, tm @ v3(0.0, 0.0, 1.0))
    if float(np.linalg.norm(side)) < 0.2:
        side = tm @ v3(1.0, 0.0, 0.0)
    side = side / float(np.linalg.norm(side))
    bl, bt, bw = h.blade
    flat = np.cross(d, side)
    mm = np.stack([d, side, flat], axis=1)
    P.add(E(head - d * 0.8 + side * (bw * 0.7), (bl, bw, bt), m.blade, "blade", mm))
    P.add(L(head - d * 0.4, head + d * h.spike, 0.45, 0.08, m.blade, "spike"))
    P.add(S(head - d * 1.6, 0.5, m.trim, "collar"))
    P.mark(r_ - d * 1.6, M.RUNE)
    if action == "attack" and f in st.get("sweep_trail", ()):
        c = (r_ + l_) * 0.5
        for k in range(16):
            ang = math.radians(-20.0 - k * 9.0)
            rr = float(np.linalg.norm(head - c)) + 1.0
            q = c + tm @ v3(math.cos(ang) * rr, math.sin(ang) * rr, -1.5 + 0.1 * k)
            P.fx.append((q, M.QI if k % 2 else M.QI_DIM))


def _boulder(P, B, action: str, f: int, ends: dict, tm) -> None:
    """M2, the cliff ape: the boulder it hoists over its head in both hands in its tell (a rock of ochre stone, moss on its
    top), held until it smashes it down before it on the blow, where it shatters into chips and dust."""
    h, m, st = B.parts.held, B.mats, B.style(action)
    lift = B.pick("boulder", action, f)
    mid = (ends[1] + ends[-1]) * 0.5
    seed = int(B.opts.get("seed", 0))
    if lift > 0.0:
        r = h.r * (0.75 + 0.25 * lift)
        c = mid + tm @ v3(0.0, 0.0, r * 0.75)

        def stone(q, n):
            top = (n[:, 2] > 0.7) & (h01v(np.floor(q[:, 0] * 0.9 + 30), np.floor(q[:, 1] * 0.9 + 30), seed % 83 + 3) > 0.6)
            pit = h01v(np.floor(q[:, 0] * 1.4 + 50), np.floor(q[:, 2] * 1.4 + 50) + np.floor(q[:, 1] * 1.4), seed % 97 + 9) > 0.82
            return np.where(top, m.moss, m.boulder).astype(object), np.where(pit & ~top, -1, 0).astype(np.int16)
        P.add(E(c, (r * 1.1, r, r * 0.9), m.boulder, "boulder", tm @ rot("c", 20.0), stone))
    if action == "attack" and f in st.get("chips", ()):
        at_ = mid + tm @ v3(1.0, 0.0, 0.0)
        at_ = v3(at_[0], at_[1], 0.4)
        k0 = f - st.get("smash_at", 1)
        for k in range(12):
            ang = math.radians(k * 30.0 + f * 13.0)
            rr = 2.0 + k0 * 2.2 + (k % 3) * 0.8
            q = at_ + v3(math.cos(ang) * rr * 0.7, math.sin(ang) * rr, 0.4 + (k % 4) * 0.6 * (2 - k0) * 0.5)
            P.fx.append((q, M.RAMPS[m.boulder][2 + (k % 2)] if k % 3 else M.DUST))
        if k0 == 0:
            for k in range(5):
                P.add(S(at_ + v3((k - 2) * 1.3, ((k * 7) % 5 - 2) * 0.9, 0.6), 0.9 + 0.3 * (k % 2), m.boulder, "chip", line=False))
    if f in st.get("dust", ()) and action == "attack":
        for k in range(10):
            ang = math.radians(k * 36.0 + f * 20.0)
            rr = 3.0 + f * 1.4 + (k % 3) * 0.6
            P.fx.append((v3(mid[0] + math.cos(ang) * rr, mid[1] + math.sin(ang) * rr, 0.3 + (k % 3) * 0.6), M.DUST if k % 2 else M.DUST_DIM))


def _shoot(P, B, end, tm, action: str, f: int) -> None:
    """The bamboo shoot in its right hand: a short green cane with pale nodes and a sprig of leaf at its top, held up at
    the ready, drawn back over the shoulder in the tell, gone on the blow (the room view throws it)."""
    h, m, st = B.parts.held, B.mats, B.style(action)
    rel = st.get("release")
    if action == "death" or rel is not None and f >= rel:
        if rel is not None and f == rel:
            for k in range(3):
                P.fx.append((end + tm @ v3(1.6 + k * 0.9, 0.0, 0.4 + 0.2 * k), M.DUST if k else M.DUST_DIM))
        return
    back = action == "windup" or (action == "attack" and f == 0)
    d = tm @ (v3(-0.55, 0.0, 0.85) if back else v3(0.45, 0.0, 0.9))
    d = d / float(np.linalg.norm(d))
    a = end - d * h.length * 0.3
    b = end + d * h.length * 0.7
    P.add(L(a, b, h.r, h.r * 0.85, m.cane, "shoot"))
    for t in (0.25, 0.6):
        P.mark(a + (b - a) * t, M.RAMPS[m.node][3])
    P.add(L(b, b + d * 1.0 + tm @ v3(0.4, 0.3, 0.2), 0.35, 0.1, m.leaf, "shoot", line=False))


# ================================================================================================= the gravity golem (M4)
# A construct of dark basalt blocks held together by gravity alone (`golem`): every part of its body a separate chamfered
# block floating a little off its neighbours (the faces of each lit or shaded by their turn, `_basalt`), a faint indigo
# ripple of gravity in the gaps between them (its bonds), a hunched faceless head with a visor groove, a violet singularity
# for an eye in its chest, a ring of pale stones with star notches orbiting it. Its blocks bob out of step with each
# other; in its tell it hauls both arms overhead as the singularity swells and dark lines and pebbles spiral into it
# (held); it slams both fists down before it, a shockwave ring racing out along the ground on the blow; struck, its blocks
# jolt apart and the singularity pinches; beaten, gravity fails and its blocks drop into a heap. It takes the stone
# guardian's styles (stand, stomp, fists_up, double_slam, knock, crumble) and its own channels: `jolt` (the gaps opening),
# `well` (the singularity swelling and drawing in, 0..1), `shock` (the ring racing out on the blow).
GOLEM_STYLES = {
    "orbit_bob": {"sway_amp": 0.15, "guard": 0.2, "bob": True},
    "gravity_raise": dict(GUARDIAN_STYLES["fists_up"], well=(0.3, 0.6, 0.9, 1.0),
                          right=((1.6, -4.6, 3.0), (-0.2, -3.8, 8.0), (-1.0, -3.4, 9.6), (-1.2, -3.4, 9.8)),
                          left=((1.6, 4.6, 3.0), (-0.2, 3.8, 8.0), (-1.0, 3.4, 9.6), (-1.2, 3.4, 9.8))),
    "orbit_slam": dict(GUARDIAN_STYLES["double_slam"], well=(1.0, 0.4, 0.2, 0.0, 0.0, 0.0), shock=(0.0, 1.0, 1.7, 2.4, 0.0, 0.0),
                       right=((2.8, -3.0, 9.0), (8.6, -2.6, -7.4), (8.6, -2.6, -7.4), (6.4, -3.4, -5.0), (4.6, -4.2, -3.6), (3.8, -4.8, -4.4)),
                       left=((2.8, 3.0, 9.0), (8.6, 2.6, -7.4), (8.6, 2.6, -7.4), (6.4, 3.4, -5.0), (4.6, 4.2, -3.6), (3.8, 4.8, -4.4))),
    "gravity_jolt": dict(STYLES["knock"], jolt=(1.0, 0.5, 0.15)),
    "gravity_fails": {"lean": (-6.0, 2.0, 6.0, 8.0, 8.0, 8.0, 8.0, 8.0), "sink": (0.0, 0.5, 1.4, 2.4, 3.0, 3.2, 3.2, 3.2),
                      "crumble": (0.0, 0.1, 0.25, 0.45, 0.65, 0.85, 1.0, 1.0), "jolt": (0.6, 0.9, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
                      "limp": True, "dark_from": 1},
}
STYLES.update(GOLEM_STYLES)
GOLEM = {
    "golem": True, "hip": 6.6, "hunch": 16.0,
    "legs": {"top": (2.3, -0.6), "foot": (3.1, 1.1, 0.7), "bones": (3.4, 3.3), "thigh": (1.8, 1.7), "shin": (1.7, 1.6),
             "boot": ((1.0, 0.0, -0.1), (2.3, 1.7, 1.0)), "plant": (1.0, -1.2)},
    "trunk": [{"at": (0.0, 0.0, 0.7), "r": (2.4, 3.4, 1.6)}, {"at": (0.5, 0.0, 4.9), "r": (2.9, 4.4, 3.3)}],
    "head": {"at": (1.8, 0.0, 9.0), "r": (1.9, 2.1, 1.65)},
    "arms": {"shoulder": (5.4, 7.2), "bones": (4.2, 4.0), "hint": (-0.6, 1.0, -1.0), "pad": (2.0, 1.9, 1.7), "upper": (1.5, 1.4, 1.4),
             "lower": (1.6, 1.5, 1.5), "fist": (2.3, 2.1, 2.0), "guard": (3.2, 5.6, -6.0), "limp": (1.0, 6.4, -6.4, 0.4)},
    "core": {"at": (3.2, 0.0, 5.0), "r": 1.15},
    "ring": {"n": 16, "orbit": 8.2, "z": 5.4, "tilt": 20.0, "r": (0.85, 0.6, 0.5)},
    "gap": 0.45,
}
VARIANTS["golem"] = {"parts": GOLEM, "mats": {"body": "grav_basalt", "ring": "grav_ring", "core": "grav_sing"},
                     "motion": {"idle": "orbit_bob", "walk": "stomp", "windup": "gravity_raise", "attack": "orbit_slam", "hurt": "gravity_jolt",
                                "death": "gravity_fails"}}


def _basalt(m, centre, Mb):
    """A chamfered basalt block: its faces by the turn of its surface in its own frame (the dominant axis of its normal:
    the faces flat, lit or shaded as they turn), the chamfers where two faces meet a step lit along its top edges and a
    step dark below, columnar seams down its front."""
    def paint(q, n):
        nl = n @ Mb
        a = np.abs(nl)
        srt = np.sort(a, axis=1)
        chamfer = srt[:, 1] > srt[:, 2] * 0.72
        loc = (q - centre) @ Mb
        seam = (np.abs(nl[:, 0]) > 0.7) & ((np.abs(loc[:, 1]) * 1.4) % 1.0 < 0.16)
        bias = np.where(chamfer, np.where(nl[:, 2] > 0.2, 1, -1), np.where(seam, -1, 0))
        return np.full(len(q), m.body, dtype=object), bias.astype(np.int16)
    return paint


def _bone_block(P, m, a, b, radii, group: str, gap: float, lift) -> tuple:
    """A block along the bone from `a` to `b`, shrunk off both ends by `gap` (so it floats apart from its neighbours),
    `radii` (along it at its full length's half less the gap, across, down)."""
    d = b - a
    ln = float(np.linalg.norm(d)) or 1e-6
    ax = d / ln
    side = np.cross(ax, v3(0.0, 0.0, 1.0))
    if float(np.linalg.norm(side)) < 0.2:
        side = np.cross(ax, v3(1.0, 0.0, 0.0))
    side = side / float(np.linalg.norm(side))
    Mb = np.stack([ax, side, np.cross(ax, side)], axis=1)
    c = (a + b) * 0.5 + v3(0.0, 0.0, lift)
    half = max(0.6, ln * 0.5 - gap)
    rr = (radii[1] + radii[2]) * 0.5
    # A short column of basalt: its sides straight, its ends flat lids with a chamfered rim.
    p0, p1 = c - ax * half, c + ax * half
    P.add(L(p0 + ax * 0.15, p1 - ax * 0.15, rr, rr * 0.94, m.body, group, _basalt(m, c, Mb), caps=False))
    for q, rad in ((p0 + ax * 0.15, rr), (p1 - ax * 0.15, rr * 0.94)):
        P.add(E(q, (0.32, rad * 0.97, rad * 0.97), m.body, group, Mb, _basalt(m, c, Mb)))
    return c, Mb


def _golem(B, action: str, f: int, view: float) -> Pose:
    """M4, the gravity golem (see GOLEM_STYLES)."""
    P = Pose()
    p, m = B.parts, B.mats
    st = B.style(action)
    lean = B.pick("lean", action, f) + p.hunch
    twist = B.pick("twist", action, f)
    step = B.pick("step", action, f)
    sink = B.pick("sink", action, f)
    sway = st.sway_amp * wave(action, f) if "sway_amp" in st else 0.0
    march = st.get("kind") == "march"
    bounce = st.bounce * abs(math.sin(f / 8.0 * math.tau)) if march else 0.0
    if march:
        twist = st.twist_amp * math.sin(f / 8.0 * math.tau)
    jolt = B.pick("jolt", action, f)
    gap = p.gap * (1.0 + 2.2 * jolt)
    hip = v3(step, sway, p.hip - sink + bounce)
    tm = rot("c", twist) @ rot("b", -lean) @ rot("a", sway * 3.0)
    up = lambda q: hip + tm @ v3(q)
    k_ = [0]

    def bob():
        """Each block's own drift, out of step with the others (idle), jolted when struck."""
        k_[0] += 1
        k = k_[0]
        if st.get("bob"):
            return 0.25 * math.sin(f / 6.0 * math.tau + k * 1.7)
        return 0.35 * jolt * math.sin(k * 2.3)

    bonds = []
    # Legs: a thigh block, a shin block, a foot block each side, by two-bone IK as the humanoid's.
    g = p.legs
    for s in (1, -1):
        ph = f / 8.0 * math.tau + (0.0 if s > 0 else math.pi)
        stride = st.stride * math.sin(ph) if march else 0.0
        lift = st.lift * max(0.0, math.cos(ph)) if march else 0.0
        plant = (g.plant[0] if s > 0 else g.plant[1]) if st.get("plant") else 0.0
        foot = v3(stride + plant + g.foot[2] + (step if s > 0 else step * 0.5), s * g.foot[0], g.foot[1] + lift)
        top = hip + rot("c", twist * 0.4) @ v3(0.0, s * g.top[0], g.top[1])
        knee, end = ik2(top, foot, g.bones[0], g.bones[1], v3(1.0, 0.0, 0.0))
        _bone_block(P, m, top, knee, (0.0, g.thigh[0], g.thigh[1]), "leg%d" % s, gap, bob())
        _bone_block(P, m, knee, end, (0.0, g.shin[0], g.shin[1]), "leg%d" % s, gap, bob())
        fc = end + v3(g.boot[0]) + v3(0.0, 0.0, bob() * 0.3)
        P.add(E(fc, g.boot[1], m.body, "foot%d" % s, rot("c", twist * 0.4), _basalt(m, fc, rot("c", twist * 0.4))))
        bonds += [top, knee, end]
    # The pelvis and the torso, the hunched head with its visor groove.
    pieces = []
    for t in p.trunk:
        c = up(t.at) + v3(0.0, 0.0, bob())
        P.add(E(c, t.r, m.body, "body", tm, _basalt(m, c, tm)))
        pieces.append(c)
    bonds.append((pieces[0] + pieces[1]) * 0.5)
    hm = tm @ rot("b", p.hunch * 0.8 - B.pick("droop", action, f))
    hc = up(p.head.at) + v3(0.0, 0.0, bob() + gap * 0.6)
    P.add(E(hc, p.head.r, m.body, "head", hm, _basalt(m, hc, hm)))
    for k in range(5):
        P.mark(hc + hm @ v3(p.head.r[0] + 0.05, -1.0 + 0.5 * k, 0.1), M.GOLEM_VISOR)
    bonds.append((hc + pieces[1]) * 0.5)
    # Arms: a shoulder block, an upper arm, a forearm and a great fist each side; their hands reach the frame's targets.
    a_ = p.arms
    sw = st.swing * math.sin(f / 8.0 * math.tau) if march else 0.0
    guard = st.guard * wave(action, f, 0.25) if "guard" in st else 0.0
    fists = []
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
        pc = sh + v3(0.0, 0.0, bob() + 0.4)
        P.add(E(pc, a_.pad, m.body, "pad%d" % s, tm @ rot("a", s * 18.0), _basalt(m, pc, tm @ rot("a", s * 18.0))))
        _bone_block(P, m, sh, elbow, (0.0,) + tuple(a_.upper[1:]), "arm%d" % s, gap, bob())
        _bone_block(P, m, elbow, end, (0.0,) + tuple(a_.lower[1:]), "arm%d" % s, gap, bob())
        fc = end + (end - elbow) / max(1e-6, float(np.linalg.norm(end - elbow))) * (a_.fist[0] * 0.6 + gap)
        P.add(E(fc, a_.fist, m.body, "fist%d" % s, tm, _basalt(m, fc, tm)))
        fists.append(fc)
        bonds += [sh, elbow, end]
    # The gravity in its gaps: a faint indigo ripple at each bond, a bright dash travelling round it frame to frame.
    dead = action == "death" and f >= st.get("dark_from", 99)
    if not dead:
        for k, q in enumerate(bonds):
            ang = math.radians(k * 47.0 + f * 60.0)
            P.glow.append((q + v3(math.cos(ang) * 0.9, math.sin(ang) * 0.9, 0.3), M.GOLEM_BOND_HI if (k + f) % 3 == 0 else M.GOLEM_BOND))
    # The singularity in its chest: a violet orb with a dark heart, swelling as it draws the world in (its tell), pinched
    # when struck, dark as it dies.
    cr = p.core
    cc = up(cr.at)
    well = B.pick("well", action, f)
    if not dead:
        r = cr.r * (1.0 + 0.5 * well) * (0.6 if jolt > 0.4 else 1.0)
        P.add(S(cc, r, m.core, "core", line=False))
        P.eye(cc + tm @ v3(r * 0.8, 0.0, 0.0), M.GOLEM_CORE_HI)
        P.mark(cc + tm @ v3(r * 0.95, 0.0, 0.0), M.GOLEM_CORE_DARK)
        if well > 0.0:
            for arm in range(3):
                for k in range(6):
                    t = k / 5.0
                    ang = math.radians(arm * 120.0 + f * 45.0 + t * 220.0)
                    rr = r + 0.6 + (1.0 - t) * 5.5 * well
                    q = cc + tm @ v3(0.8 + 0.3 * (1.0 - t), math.cos(ang) * rr, math.sin(ang) * rr)
                    P.glow.append((q, M.GOLEM_PULL_LIGHT if k % 2 else M.GOLEM_PULL_DARK))
            for k in range(4):
                ang = math.radians(k * 90.0 + f * 70.0)
                rr = 2.2 + 3.0 * (1.0 - ((f * 0.25 + k * 0.3) % 1.0))
                P.add(S(cc + tm @ v3(1.2, math.cos(ang) * rr, math.sin(ang) * rr), 0.42, m.ring, "pebble", line=False))
    # The ring of pale stones orbiting it, tilted, turning; dropping as gravity fails.
    rg = p.ring
    crumble = B.pick("crumble", action, f)
    spin = f * (360.0 / rg.n / 2.0) + (40.0 * well if action in ("windup", "attack") else 0.0)
    for k in range(rg.n):
        ang = math.radians(k * 360.0 / rg.n + spin)
        q = rot("a", rg.tilt) @ v3(math.cos(ang) * rg.orbit, math.sin(ang) * rg.orbit, 0.0) + v3(hip[0] * 0.4, 0.0, rg.z)
        if crumble > 0.0:
            q = q + (v3(q[0] * 1.2, q[1] * 1.2, rg.r[2]) - q) * min(1.0, crumble * 1.4)
        mm = rot("c", math.degrees(ang) + 90.0)
        P.add(E(q, rg.r, m.ring, "ring", mm))
        if k % 3 == 0 and crumble < 0.5:
            P.mark(q + v3(0.0, 0.0, rg.r[2] + 0.1), M.GOLEM_NOTCH)
    # The slam's shockwave racing out along the ground before it.
    shock = B.pick("shock", action, f)
    if shock > 0.0:
        cx = (fists[0][0] + fists[1][0]) * 0.5
        rr = 3.0 + 4.0 * shock
        for k in range(36):
            ang = math.radians(k * 10.0 + shock * 11.0)
            for dd, col in ((0.0, M.GOLEM_SHOCK_HI), (1.0, M.GOLEM_SHOCK)):
                P.fx.append((v3(cx + math.cos(ang) * (rr + dd), math.sin(ang) * (rr + dd) * 0.95, 0.25), col))
        for k in range(8):
            ang = math.radians(k * 45.0 + 10.0)
            P.fx.append((v3(cx + math.cos(ang) * 2.0, math.sin(ang) * 2.0, 0.6 + 0.8 * (k % 2)), M.DUST))
    if crumble > 0.0:
        collapse(P, crumble, int(B.opts.get("seed", 0)))
    sq = st.get("squash", {}).get(f)
    if sq is not None:
        P.squash(sq[0], sq[1], sq[2], (step, 0.0, 0.0))
    return P


# ================================================================================================= the people of size (M4)
# The late game's bosses who are people: Comet Captain Rao (`captain`), Admiral Voss (`admiral`), General Kharn
# (`general`) and the Ninth Presence (`presence`), sculpted on this plan's body as M2's were (the body first, `opts.bare`;
# then dressed). What they wear past M2's robe, sleeves and paint (`m4`, `_m4_wear`): a coat's tails to the knee, a
# tattered or solid cape, a headband, an admiral's winged hat, a plumed war helm, a scholar's guan, epaulettes, pauldrons,
# a full or a long beard, a scar, the Ashborn's ember cracks, the Presence's crown of nine lights and its hem of mist; and
# their props (`M4_PROPS`): the captain's comet anchor on its chain, the admiral's starsteel sabre and brass hand cannon,
# the general's Cinder Glaive, the Presence's staff of nine.
def _turn(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


M4_FOLK_STYLES = {
    # Comet Captain Rao: his anchor on his shoulder (`anchor`: the shank's direction from his grip, in the trunk's frame),
    # raised over his head in both hands as comet fire runs along its flukes (`comet`), slammed down before him in a burst
    # of comet sparks (`impact`).
    "capt_idle": {"sway_amp": 0.3, "guard": 0.15, "right": ((2.7, -3.2, -0.6),) * 6, "left": ((1.8, 3.8, -4.0),) * 6,
                  "lean": (0.0, -0.5, -0.8, -0.5, 0.0, 0.3), "anchor": ((-0.62, -0.25, 0.74),) * 6},
    "capt_stride": {"kind": "march", "bounce": 0.6, "twist_amp": 8.0, "stride": 2.3, "lift": 1.4, "swing": 0.9,
                    "right": ((2.7, -3.2, -0.6),) * 8, "anchor": ((-0.62, -0.25, 0.74),) * 8},
    "anchor_raise": dict(FOLK_STYLES["cleaver_raise"], anchor=((-0.4, -0.2, 0.9), (-0.8, 0.0, 0.6), (-0.95, 0.0, 0.3), (-1.0, 0.0, 0.2)),
                         comet=(0.3, 0.6, 0.9, 1.0)),
    "anchor_slam": dict(FOLK_STYLES["cleaver_slam"], anchor=((-1.0, 0.0, 0.2), (0.75, 0.0, -0.65), (0.75, 0.0, -0.68), (0.5, -0.2, 0.0),
                                                              (-0.2, -0.25, 0.7), (-0.62, -0.25, 0.74)),
                        comet=(1.0, 1.0, 0.6, 0.2, 0.0, 0.0), impact=(1, 2, 3), dust=()),
    "capt_rock": dict(FOLK_STYLES["chief_rock"], anchor=((-0.3, -0.4, 0.86),) * 3),
    "capt_fall": dict(FOLK_STYLES["chief_fall"], anchor=((-0.62, -0.25, 0.74),) * 8),
    # Admiral Voss: his starsteel sabre in his right hand (`sabre`: its direction), his brass hand cannon in his left
    # (`cannon`, its barrel's), levelled at you as its fuse sparks and the sabre is drawn back (`fuse`), fired as he cuts
    # (`flash`: the muzzle's flash and smoke; `arc`: the sabre's starsteel arc).
    "adm_stand": {"sway_amp": 0.15, "guard": 0.0, "right": ((1.6, -3.9, -3.6),) * 6, "left": ((2.0, 3.4, -3.4),) * 6,
                  "sabre": ((0.45, -0.25, -0.86),) * 6, "cannon": ((0.8, 0.2, -0.55),) * 6},
    "adm_walk": {"kind": "march", "bounce": 0.3, "twist_amp": 3.0, "stride": 1.9, "lift": 0.9, "swing": 0.5,
                 "right": ((1.6, -3.9, -3.6),) * 8, "left": ((2.0, 3.4, -3.4),) * 8, "sabre": ((0.45, -0.25, -0.86),) * 8,
                 "cannon": ((0.8, 0.2, -0.55),) * 8},
    "cannon_aim": {"lean": (-2.0, -4.0, -5.0, -5.0), "twist": (10.0, 18.0, 24.0, 26.0), "step": (-0.2, -0.5, -0.7, -0.8),
                   "sink": (0.2, 0.4, 0.5, 0.5), "plant": True, "glare": True, "fuse": (0.3, 0.6, 0.9, 1.0),
                   "left": ((3.8, 2.2, -0.6), (5.6, 1.4, 0.2), (6.4, 1.0, 0.6), (6.6, 0.9, 0.6)),
                   "right": ((1.0, -3.8, 1.2), (0.0, -3.6, 3.4), (-0.8, -3.4, 4.6), (-1.0, -3.4, 4.8)),
                   "sabre": ((0.2, -0.3, 0.93), (-0.3, -0.3, 0.9), (-0.6, -0.2, 0.77), (-0.66, -0.2, 0.72)),
                   "cannon": ((1.0, 0.0, -0.1), (1.0, -0.1, 0.0), (1.0, -0.15, 0.05), (1.0, -0.15, 0.05))},
    "broadside_cut": {"lean": (4.0, 12.0, 12.0, 8.0, 4.0, 0.0), "twist": (26.0, -18.0, -24.0, -16.0, -6.0, 0.0),
                      "step": (0.6, 2.4, 2.6, 2.0, 1.0, 0.3), "sink": (0.4, 1.0, 1.0, 0.7, 0.3, 0.1), "plant": True,
                      "right": ((-1.0, -3.4, 4.8), (6.6, -0.4, -1.2), (6.2, 1.6, -2.2), (4.6, 0.8, -3.0), (3.0, -2.0, -3.4), (1.8, -3.6, -3.6)),
                      "sabre": ((-0.66, -0.2, 0.72), (0.9, 0.35, -0.25), (0.7, 0.7, -0.35), (0.5, 0.45, -0.74), (0.45, 0.0, -0.89), (0.45, -0.25, -0.86)),
                      "left": ((6.6, 0.9, 0.6), (5.4, 1.6, 0.8), (4.2, 2.4, 0.2), (3.2, 2.9, -1.4), (2.6, 3.2, -2.6), (2.0, 3.4, -3.4)),
                      "cannon": ((1.0, -0.15, 0.05), (0.9, 0.0, 0.4), (0.9, 0.1, 0.3), (0.85, 0.2, -0.2), (0.8, 0.2, -0.5), (0.8, 0.2, -0.55)),
                      "flash": (0.0, 1.0, 0.6, 0.0, 0.0, 0.0), "smoke": (1, 2, 3, 4), "arc": (1, 2), "squash": {1: (1.03, 1.0, 0.97)}},
    "adm_rock": {"lean": (-12.0, -6.0, -2.0), "twist": (8.0, -4.0, 0.0), "step": (-2.0, -1.2, -0.4), "sink": (0.4, 0.2, 0.0),
                 "droop": (-14.0, -4.0, 0.0), "squint": True,
                 "right": ((1.2, -4.4, -1.4), (1.4, -4.2, -2.6), (1.6, -3.9, -3.6)), "left": ((1.6, 4.2, -1.0), (1.8, 3.8, -2.4), (2.0, 3.4, -3.4)),
                 "sabre": ((0.3, -0.6, -0.74),) * 3, "cannon": ((0.6, 0.6, -0.5),) * 3},
    "adm_fall": dict(FOLK_STYLES["elder_fall"], sabre=((0.45, -0.25, -0.86),) * 8, cannon=((0.8, 0.2, -0.55),) * 8),
    # General Kharn: the Cinder Glaive in both hands (`glaive`: the pole's direction from his right hand toward the
    # blade), upright at his side, raised high over his head as its blade bursts into flame (`flame`), brought down in a
    # leaping cleave that sets the ground alight (`fire`).
    "gen_stand": {"sway_amp": 0.2, "guard": 0.0, "right": ((2.6, -4.6, -0.8),) * 6, "left": ((2.4, 4.4, -3.4),) * 6,
                  "glaive": ((0.08, -0.05, 1.0),) * 6},
    "gen_march": {"kind": "march", "bounce": 0.5, "twist_amp": 6.0, "stride": 2.4, "lift": 1.5, "swing": 0.8,
                  "right": ((2.6, -4.6, -0.8),) * 8, "glaive": ((0.08, -0.05, 1.0),) * 8},
    "glaive_raise": {"lean": (-4.0, -10.0, -14.0, -16.0), "step": (-0.2, -0.5, -0.7, -0.8), "sink": (0.4, 0.2, -0.2, -0.3), "plant": True,
                     "roar": (0.3, 0.8, 1.0, 1.0), "glare": True, "flame": (0.3, 0.6, 0.9, 1.0),
                     "right": ((2.0, -3.0, 1.6), (1.0, -2.0, 4.6), (0.4, -1.4, 6.2), (0.2, -1.4, 6.6)),
                     "left": ((2.6, 0.8, 0.6), (1.6, 0.4, 3.8), (0.8, 0.2, 5.4), (0.6, 0.2, 5.8)),
                     "glaive": ((-0.3, -0.1, 0.95), (-0.7, 0.0, 0.7), (-0.95, 0.0, 0.32), (-1.0, 0.0, 0.18))},
    "glaive_cleave": {"lean": (-14.0, 16.0, 18.0, 10.0, 4.0, 0.0), "step": (0.8, 3.2, 3.4, 2.6, 1.2, 0.4), "sink": (-0.8, 1.6, 1.6, 0.8, 0.2, 0.0),
                      "plant": True, "roar": (1.0, 1.0, 0.6, 0.2, 0.0, 0.0), "flame": (1.0, 1.0, 0.6, 0.3, 0.0, 0.0), "fire": (0.0, 1.0, 1.6, 2.2, 0.0, 0.0),
                      "squash": {1: (1.03, 1.04, 0.95)},
                      "right": ((0.2, -1.4, 6.6), (6.2, -0.6, -3.8), (6.2, -0.6, -4.0), (5.0, -1.6, -2.8), (3.6, -3.2, -1.6), (2.6, -4.6, -0.8)),
                      "left": ((0.6, 0.2, 5.8), (4.6, 0.8, -2.6), (4.6, 0.8, -2.8), (3.6, 2.0, -3.0), (2.8, 3.6, -3.2), (2.4, 4.4, -3.4)),
                      "glaive": ((-1.0, 0.0, 0.18), (0.82, 0.0, -0.57), (0.82, 0.0, -0.6), (0.5, -0.1, 0.2), (0.15, -0.05, 0.8), (0.08, -0.05, 1.0))},
    "gen_rock": dict(FOLK_STYLES["chief_rock"], right=((2.0, -4.8, 0.4), (2.4, -4.7, -0.2), (2.6, -4.6, -0.8)),
                     left=((1.6, 4.8, -2.0), (2.0, 4.6, -2.8), (2.4, 4.4, -3.4)), glaive=((-0.2, -0.3, 0.93),) * 3),
    "gen_fall": dict(FOLK_STYLES["chief_fall"], glaive=((0.08, -0.05, 1.0),) * 8),
    # The Ninth Presence: floating (its `sink` below zero), its staff of nine in its right hand (`staff`), its crown of nine
    # lights behind its head (`halo`: gathering into a blazing crown over its head, 0..1), thrown out round it on both
    # sides on the blow (`burst`) with its palm's ring (`palm`).
    "pres_hover": {"sway_amp": 0.2, "guard": 0.0, "sink": (0.0, -0.3, -0.5, -0.3, 0.0, 0.2),
                   "right": ((2.0, -3.6, -2.6),) * 6, "left": ((2.4, 2.2, -3.8),) * 6},
    "pres_glide": {"kind": "march", "bounce": 0.2, "twist_amp": 3.0, "stride": 1.2, "lift": 0.6, "swing": 0.4,
                   "right": ((2.0, -3.6, -2.6),) * 8, "left": ((2.4, 2.2, -3.8),) * 8},
    "crown_gather": {"lean": (-2.0, -4.0, -6.0, -6.0), "sink": (-0.3, -0.6, -0.9, -1.0), "plant": True, "glare": True,
                     "halo": (0.3, 0.6, 0.9, 1.0),
                     "right": ((1.8, -3.6, 2.0), (1.2, -3.8, 4.6), (0.8, -3.8, 6.2), (0.7, -3.8, 6.6)),
                     "left": ((2.4, 2.2, -1.2), (1.6, 2.8, -0.6), (1.0, 3.0, -0.2), (0.8, 3.0, 0.0))},
    "seat_palm": {"lean": (4.0, 12.0, 12.0, 8.0, 4.0, 0.0), "twist": (-14.0, 22.0, 26.0, 18.0, 8.0, 0.0), "step": (0.6, 2.4, 2.6, 2.0, 1.0, 0.3),
                  "sink": (-1.0, -0.4, -0.4, -0.2, 0.0, 0.0), "plant": True, "glare": True, "halo": (1.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                  "burst": (0.0, 1.0, 1.6, 2.2, 0.0, 0.0), "palm": (0.0, 1.0, 1.6, 0.0, 0.0, 0.0), "squash": {1: (1.03, 1.0, 0.97)},
                  "right": ((0.7, -3.8, 6.6), (2.4, -3.8, 1.6), (2.4, -3.6, 0.6), (2.3, -3.6, -0.8), (2.1, -3.6, -1.8), (2.0, -3.6, -2.6)),
                  "left": ((0.8, 3.0, 0.0), (7.2, 0.6, -0.4), (7.4, 0.6, -0.4), (6.0, 1.0, -1.0), (4.2, 1.6, -2.4), (2.4, 2.2, -3.8))},
    "pres_rock": {"lean": (-12.0, -6.0, -2.0), "twist": (8.0, -4.0, 0.0), "step": (-2.0, -1.2, -0.4), "sink": (0.0, -0.2, -0.3),
                  "droop": (-14.0, -4.0, 0.0), "squint": True,
                  "right": ((1.6, -3.8, -1.2), (1.8, -3.7, -2.0), (2.0, -3.6, -2.6)), "left": ((1.8, 2.8, -1.6), (2.1, 2.5, -2.8), (2.4, 2.2, -3.8))},
    "pres_fade": {"lean": (-6.0, -2.0, 2.0, 4.0, 4.0, 4.0, 4.0, 4.0), "sink": (0.0, 0.4, 1.0, 1.6, 2.0, 2.2, 2.2, 2.2),
                  "droop": (0.0, 10.0, 18.0, 22.0, 24.0, 24.0, 24.0, 24.0), "dark_from": 3,
                  "fade": (0.0, 0.08, 0.2, 0.35, 0.52, 0.7, 0.86, 1.0),
                  "right": ((2.4, -3.6, -2.0),) * 8, "left": ((2.6, 1.6, -3.4),) * 8},
}
STYLES.update(M4_FOLK_STYLES)

# Comet Captain Rao (`captain`): the pirates' captain from the comet sails, burly and barrel-chested, a head over his men
# and broad as two: a crimson coat open over a pale linen shirt, its tails to his knees, gold trim and a wide leather belt,
# dark cuffed trousers in high boots, a tattered black cape, his dark hair tied back under a jade headband, a short full
# beard and a scar across his eye; his comet anchor of blue-black comet iron on its chain over his shoulder.
CAPTAIN = {
    "hip": 7.6,
    "legs": {"top": (2.1, -0.6), "foot": (2.7, 1.0, 0.7), "bones": (4.0, 3.9), "thigh": (1.75, 1.5), "shin": (1.45, 1.3), "knee": None,
             "boot": ((0.9, 0.0, -0.3), (2.0, 1.3, 1.05)), "plant": (1.2, -1.4)},
    "trunk": [{"at": (0.0, 0.0, 0.8), "r": (2.6, 3.4, 2.0), "paint": True}, {"at": (0.7, 0.0, 3.5), "r": (3.0, 3.7, 2.7), "paint": True},
              {"at": (0.4, 0.0, 6.6), "r": (3.0, 4.9, 2.7), "paint": True}],
    "neck": ((0.6, 0.0, 8.4), 1.45),
    "head": {"at": ((0.9, 0.0, 8.6), 2.3), "r": (2.2, 2.15, 2.3)},
    "face": {"kind": "human", "eyes": (1.95, 0.75, 0.35), "brow": (0.4, 0.72, 0.26), "brow_tilt": -16.0, "nose": (2.3, 0.0, -0.15),
             "mouth": (2.0, 0.75, -0.95), "grin": 0.7, "ears": (-0.1, 2.15, 0.0), "hair": "tail"},
    "arms": {"shoulder": (4.5, 7.1), "bones": (3.8, 3.6), "hint": (-0.6, 1.0, -1.0), "ball": None, "upper": (1.5, 1.35), "elbow": None,
             "lower": (1.35, 1.2), "wrap": None, "fist": (1.05, 1.0, 1.0), "guard": (2.4, 4.8, -3.6), "limp": (1.0, 5.2, -5.4, 0.4)},
    "paint": {"kind": "clothes", "zones": [{"mat": "belt", "z": (1.5, 2.6), "inner": 4.2},
                                           {"mat": "boot", "z": (-30.0, -4.0)},
                                           {"mat": "trousers", "z": (-30.0, 1.5), "inner": 4.4, "folds": 1.4},
                                           {"mat": "shirt", "z": (2.6, 8.0), "front": 0.62, "inner": 1.4},
                                           {"mat": "trim", "z": (2.6, 8.4), "front": 0.45, "inner": 1.9},
                                           {"mat": "coat", "z": (2.6, 30.0), "folds": 1.6}]},
    "dress": True,
    "prop": {"kind": "anchor", "shank": 8.6, "r": 0.5, "stock": 4.0, "fluke": 2.9, "ring": 0.65},
    "m4": {"tails": {"top": 2.6, "hem": 3.2, "r": (3.2, 3.9), "lead": 0.2, "split": 0.9}, "cape": {"top": 7.4, "bottom": 1.4, "back": 3.0,
                                                                                                 "r": (3.4, 4.3), "tatter": True},
           "band": (0.1, 1.35, 2.25), "beard": "full", "scar": True},
}
# Admiral Voss (`admiral`): the master of Blackmast Haven, tall, lean and imperious: a long indigo greatcoat to his knees
# with gold trim, gold buttons and a high collar, gold epaulettes, a black cape, dark trousers in tall boots, a black
# winged official's hat whose long wings stand out to both sides, his black hair tied back, a thin drooping moustache; a
# starsteel sabre of pale blue light in his right hand and a brass hand cannon with a dragon's mouth in his left.
ADMIRAL = {
    "hip": 9.2,
    "legs": {"top": (1.5, -0.5), "foot": (1.9, 1.0, 0.6), "bones": (4.5, 4.4), "thigh": (1.25, 1.05), "shin": (1.05, 0.9), "knee": None,
             "boot": ((0.8, 0.0, -0.3), (1.75, 1.0, 0.95)), "plant": (1.0, -1.2)},
    "trunk": [{"at": (0.0, 0.0, 0.6), "r": (2.0, 2.8, 1.7), "paint": True}, {"at": (0.2, 0.0, 3.0), "r": (1.8, 2.6, 1.8), "paint": True},
              {"at": (0.2, 0.0, 5.6), "r": (2.2, 3.4, 2.4), "paint": True}],
    "neck": ((0.3, 0.0, 7.6), 0.95),
    "head": {"at": ((0.6, 0.0, 7.9), 2.0), "r": (1.85, 1.75, 2.05)},
    "face": {"kind": "human", "eyes": (1.7, 0.65, 0.3), "brow": (0.36, 0.6, 0.2), "brow_tilt": -20.0, "nose": (2.05, 0.0, -0.2),
             "mouth": (1.8, 0.5, -0.9), "ears": (-0.1, 1.75, 0.0), "beard": "moustache", "hair": "tail"},
    "arms": {"shoulder": (3.4, 6.0), "bones": (3.6, 3.4), "hint": (-0.6, 1.0, -1.0), "ball": None, "upper": (0.95, 0.85), "elbow": None,
             "lower": (0.85, 0.78), "wrap": None, "fist": (0.75, 0.7, 0.7), "guard": (2.4, 3.6, -3.6), "limp": (0.8, 4.0, -5.2, 0.3)},
    "paint": {"kind": "clothes", "zones": [{"mat": "trim", "z": (7.1, 7.9), "inner": 2.4},
                                           {"mat": "belt", "z": (2.2, 3.0)},
                                           {"mat": "boot", "z": (-30.0, -3.8)},
                                           {"mat": "trousers", "z": (-30.0, 2.2), "inner": 4.0},
                                           {"mat": "trim", "z": (3.0, 6.8), "front": 0.6, "inner": 0.45},
                                           {"mat": "coat", "z": (2.2, 30.0), "folds": 1.5}]},
    "dress": True,
    "prop": {"kind": "sabre_cannon", "blade": 5.4, "barrel": 3.0},
    "m4": {"tails": {"top": 2.4, "hem": 4.0, "r": (2.4, 3.1), "lead": 0.3, "split": 0.6, "trim": 0.5},
           "cape": {"top": 6.6, "bottom": 3.0, "back": 2.4, "r": (2.9, 3.4)}, "hat": "winged", "epaulettes": (0.0, 3.4, 6.3), "buttons": 5},
}
# General Kharn (`general`): the Ashborn's general, massive, his ash-grey skin cracked with embers: crimson lamellar armour
# over his chest and arms with dark iron plates and great iron pauldrons, a crimson cape, dark trousers in iron-shod boots,
# a war helm of dark iron with cheek guards and a tall crimson plume, his black hair tied back, a full black beard; the
# Cinder Glaive, a great guandao taller than he is, its curved blade glowing with embers along its edge.
GENERAL = {
    "hip": 8.2,
    "legs": {"top": (2.2, -0.6), "foot": (2.8, 1.0, 0.7), "bones": (4.2, 4.1), "thigh": (1.9, 1.65), "shin": (1.6, 1.4), "knee": None,
             "boot": ((1.0, 0.0, -0.3), (2.2, 1.45, 1.1)), "plant": (1.3, -1.5)},
    "trunk": [{"at": (0.0, 0.0, 0.8), "r": (2.8, 3.8, 2.2), "paint": True}, {"at": (0.4, 0.0, 3.6), "r": (2.7, 3.7, 2.6), "paint": True},
              {"at": (0.4, 0.0, 6.6), "r": (3.2, 5.1, 3.0), "paint": True}],
    "neck": ((0.6, 0.0, 8.8), 1.5),
    "head": {"at": ((0.9, 0.0, 9.0), 2.3), "r": (2.15, 2.1, 2.3)},
    "face": {"kind": "human", "eyes": (1.9, 0.75, 0.35), "brow": (0.42, 0.75, 0.28), "brow_tilt": -22.0, "nose": (2.25, 0.0, -0.15),
             "mouth": (1.95, 0.7, -1.0), "ears": (-0.1, 2.1, 0.0), "hair": "tail"},
    "arms": {"shoulder": (4.8, 7.4), "bones": (4.0, 3.8), "hint": (-0.6, 1.0, -1.0), "ball": None, "upper": (1.7, 1.5), "elbow": None,
             "lower": (1.5, 1.35), "wrap": None, "fist": (1.15, 1.1, 1.1), "guard": (2.6, 4.6, -3.4), "limp": (1.0, 5.6, -5.6, 0.4)},
    "paint": {"kind": "lamellar", "zones": [{"mat": "belt", "z": (2.4, 3.4), "inner": 5.0},
                                            {"mat": "boot", "z": (-30.0, -4.0)},
                                            {"mat": "armour", "z": (-2.2, 2.4), "inner": 5.0},
                                            {"mat": "trousers", "z": (-30.0, -2.2), "inner": 5.0, "folds": 1.4},
                                            {"mat": "armour", "z": (3.4, 30.0)}], "rows": 1.15},
    "dress": True,
    "prop": {"kind": "glaive", "below": 5.6, "above": 8.4, "r": 0.5, "blade": (5.6, 2.2)},
    "m4": {"cape": {"top": 7.6, "bottom": 2.6, "back": 3.2, "r": (3.4, 4.2)}, "helm": True, "beard": "full", "pauldrons": (0.0, 5.4, 8.0),
           "embers": True},
}
# The Ninth Presence (`presence`): the ninth seat of the Trial Hall filled by your own Presence grown old: a towering
# spectral sage, pale violet with the hall's light, in a scholar's long white robe with wide sleeves and a pale cape, a
# guan on its long white hair, a long white beard, its eyes glowing; floating, its hem thinning into mist; a staff of white
# jade crowned with nine lights in its right hand, and the crown of nine lights behind its head.
PRESENCE = {
    "hip": 10.0,
    "legs": {"top": (1.3, -0.5), "foot": (1.6, 1.0, 0.6), "bones": (4.9, 4.8), "thigh": (1.1, 0.95), "shin": (0.95, 0.8), "knee": None,
             "boot": ((0.7, 0.0, -0.3), (1.5, 0.9, 0.6)), "plant": (0.8, -1.0)},
    "trunk": [{"at": (0.0, 0.0, 0.6), "r": (2.0, 2.8, 1.6), "paint": True}, {"at": (0.2, 0.0, 3.0), "r": (1.7, 2.5, 1.7), "paint": True},
              {"at": (0.2, 0.0, 5.6), "r": (2.1, 3.2, 2.3), "paint": True}],
    "neck": ((0.4, 0.0, 7.5), 0.95),
    "head": {"at": ((0.8, 0.0, 7.8), 2.2), "r": (2.1, 2.0, 2.35)},
    "face": {"kind": "human", "eyes": (1.95, 0.72, 0.3), "brow": (0.4, 0.7, 0.24), "brow_tilt": 10.0, "nose": (2.25, 0.0, -0.2),
             "mouth": (2.0, 0.5, -1.0), "ears": (-0.1, 2.0, 0.0), "beard": "moustache", "hair": "loose", "glow": "presence"},
    "arms": {"shoulder": (3.2, 6.0), "bones": (3.7, 3.5), "hint": (-0.6, 1.0, -1.0), "ball": None, "upper": (0.9, 0.82), "elbow": None,
             "lower": (0.82, 0.76), "wrap": None, "fist": (0.75, 0.7, 0.7), "guard": (2.4, 3.2, -3.4), "limp": (0.8, 3.8, -5.2, 0.3)},
    "paint": {"kind": "clothes", "zones": [{"mat": "trim", "z": (6.9, 7.6)}, {"mat": "sash", "z": (2.4, 3.3)}, {"mat": "robe", "folds": 1.3}]},
    "dress": True,
    "robe": {"top": 2.0, "r": (2.8, 4.4), "lead": 0.4, "trim_w": 0.6, "hem": 1.6},
    "sleeves": {"r": (0.95, 1.65), "over": 0.6, "trim": True, "palm": "left"},
    "prop": {"kind": "nine_staff", "below": 9.0, "above": 6.4, "r": 0.34, "ring": 1.3},
    "m4": {"cape": {"top": 6.4, "bottom": 2.0, "back": 2.4, "r": (3.2, 4.0)}, "guan": True, "beard": "long", "halo": {"n": 9, "r": 3.2},
           "mist": True},
}
_SKIN = {"body": "folk_skin", "limb": "folk_skin", "joint": "folk_skin", "neck": "folk_skin", "skin": "folk_skin", "hand": "folk_skin"}
VARIANTS.update({
    "captain": {"parts": CAPTAIN, "mats": dict(_SKIN, dark="capt_boot", hair="capt_hair", cord="capt_band", band="capt_band", coat="capt_coat",
                                               shirt="capt_shirt", trousers="capt_trousers", belt="capt_belt", boot="capt_boot", trim="brass",
                                               cape="capt_cape", iron="comet_iron", maw="maw"),
                "motion": {"idle": "capt_idle", "walk": "capt_stride", "windup": "anchor_raise", "attack": "anchor_slam", "hurt": "capt_rock",
                           "death": "capt_fall"}},
    "admiral": {"parts": ADMIRAL, "mats": dict(_SKIN, dark="adm_boot", hair="adm_hair", cord="adm_gold", coat="adm_coat", trousers="adm_trousers",
                                               belt="adm_boot", boot="adm_boot", trim="adm_gold", cape="adm_cape", hat="adm_hat", steel="starsteel",
                                               brass="adm_brass", grip="halberd_shaft", maw="maw"),
                "motion": {"idle": "adm_stand", "walk": "adm_walk", "windup": "cannon_aim", "attack": "broadside_cut", "hurt": "adm_rock",
                           "death": "adm_fall"}},
    "general": {"parts": GENERAL, "mats": {"body": "ash_skin", "limb": "ash_skin", "joint": "ash_skin", "neck": "ash_skin", "skin": "ash_skin",
                                           "hand": "ash_skin", "dark": "gen_iron", "hair": "gen_hair", "cord": "gen_crimson", "armour": "gen_plate",
                                           "trousers": "gen_trousers", "belt": "gen_iron", "boot": "gen_iron", "trim": "brass", "cape": "gen_crimson",
                                           "iron": "gen_iron", "plume": "gen_plume", "shaft": "halberd_shaft", "blade": "cinder_blade", "maw": "maw"},
                "motion": {"idle": "gen_stand", "walk": "gen_march", "windup": "glaive_raise", "attack": "glaive_cleave", "hurt": "gen_rock",
                           "death": "gen_fall"}},
    "presence": {"parts": PRESENCE, "mats": {"body": "pres_skin", "limb": "pres_skin", "joint": "pres_skin", "neck": "pres_skin", "skin": "pres_skin",
                                             "hand": "pres_skin", "dark": "pres_robe", "hair": "pres_hair", "robe": "pres_robe", "trim": "pres_gold",
                                             "sash": "pres_sash", "cape": "pres_cape", "staff": "pres_jade", "hat": "pres_cap", "maw": "maw"},
                 "motion": {"idle": "pres_hover", "walk": "pres_glide", "windup": "crown_gather", "attack": "seat_palm", "hurt": "pres_rock",
                            "death": "pres_fade"}},
})


def _lamellar(m, hip, tm, c, bare: bool):
    """M4, the general's armour: the clothes' zones (`_clothes`), the armour's lamellae in rows round his chest and arms
    (laced in a band of `cord` every `rows`, the row's lower edge a step lit, the plates' seams a step dark), his skin
    bare where no zone holds."""
    base = _clothes(m, hip, tm, c, bare)
    rows = c.get("rows", 1.0)

    def paint(q, n):
        names, bias = base(q, n)
        if bare:
            return names, bias
        loc = (q - hip) @ tm
        arm = names == m.armour
        u = (loc[:, 2] % rows) / rows
        lace = arm & (u < 0.15)
        lit = arm & (u > 0.8)
        col = arm & ((loc[:, 1] * 1.5) % 1.0 < 0.15) & ~lace
        names = np.where(lace, m.cord, names).astype(object)
        return names, np.where(col, -1, np.where(lit, 1, bias)).astype(np.int16)
    return paint


def _m4_wear(P, B, action: str, f: int, up, tm, hip, hc, hm, ends: dict, elbows: dict) -> None:
    """What the M4 people of size wear past the robe and the sleeves (see the module's note)."""
    w, m, st = B.parts.m4, B.mats, B.style(action)
    hr = B.parts.head.r
    dead = action == "death" and f >= st.get("dark_from", 99)
    if w.get("tails"):
        _coat_tails(P, B, action, f, hip, tm, w.tails)
    if w.get("cape"):
        _cape4(P, B, action, f, up, tm, hip, w.cape)
    if w.get("band"):
        # A cloth band round his brow, its ends tied behind and trailing.
        b0, b1, rr = w.band
        q = hc + hm @ v3(b0, 0.0, b1)
        P.add(E(q, (hr[0] * 1.03, hr[1] * 1.04, 0.42), m.band, "band", hm, line=False))
        knot = hc + hm @ v3(-hr[0] * 0.95, 0.0, b1)
        sw = 0.4 * math.sin(f * 0.9) if action in ("idle", "walk") else -0.3
        for s in (1, -1):
            t1 = knot + hm @ v3(-1.3, s * 0.5 + sw * 0.3, -0.9)
            P.add(L(knot, t1, 0.32, 0.18, m.band, "band_tie", line=False))
    if w.get("hat") == "winged":
        # The official's winged hat: a black cap over his crown, a taller lobe behind, two long thin wings standing out to
        # either side from its back, tipped in gold.
        cap = hc + hm @ v3(-0.15, 0.0, hr[2] * 0.55)
        P.add(E(cap, (hr[0] * 1.02, hr[1] * 1.03, hr[2] * 0.62), m.hat, "hat", hm))
        lobe = hc + hm @ v3(-0.9, 0.0, hr[2] * 0.95)
        P.add(E(lobe, (0.95, hr[1] * 0.8, 1.05), m.hat, "hat", hm))
        P.add(E(cap + hm @ v3(0.0, 0.0, -hr[2] * 0.42), (hr[0] * 1.06, hr[1] * 1.07, 0.3), m.trim, "hatband", hm, line=False))
        flap = 3.0 * math.sin(f * 0.8) if action in ("idle", "walk") else 0.0
        for s in (1, -1):
            root = lobe + hm @ v3(-0.3, s * 0.6, -0.2)
            wm = hm @ rot("a", s * (6.0 + flap))
            tip = root + wm @ v3(-0.2, s * 4.6, 0.25)
            P.add(E((root + tip) * 0.5, (0.4, 2.35, 0.2), m.hat, "hatwing%d" % s, wm))
            P.mark(tip, M.RAMPS[m.trim][3])
    if w.get("helm"):
        # The war helm: a dark iron dome over his head, a crimson band, cheek guards, a gold brow plate and a tall crimson
        # plume rising from its crown and sweeping back.
        dome = hc + hm @ v3(-0.2, 0.0, hr[2] * 0.78)
        P.add(E(dome, (hr[0] * 1.06, hr[1] * 1.08, hr[2] * 0.56), m.iron, "helm", hm))
        P.add(E(dome + hm @ v3(0.0, 0.0, -hr[2] * 0.36), (hr[0] * 1.1, hr[1] * 1.1, 0.34), m.cord, "helmband", hm, line=False))
        P.add(E(hc + hm @ v3(hr[0] * 0.8, 0.0, hr[2] * 0.62), (0.4, 0.9, 0.5), m.trim, "browplate", hm))
        P.add(S(hc + hm @ v3(-0.2, 0.0, hr[2] * 1.32), 0.45, m.trim, "helmknob"))
        for s in (1, -1):
            P.add(E(hc + hm @ v3(0.4, s * hr[1] * 0.95, -0.4), (1.1, 0.35, 1.2), m.iron, "cheekguard%d" % s, hm @ rot("a", s * 14.0)))
        base = hc + hm @ v3(-0.2, 0.0, hr[2] * 1.4)
        sway = 0.5 * math.sin(f * 0.9) if action in ("idle", "walk") else (-0.8 if action == "attack" and f in (1, 2) else 0.0)
        pts = [base, base + hm @ v3(-0.5, 0.0, 1.0), base + hm @ v3(-1.6, sway * 0.3, 1.4), base + hm @ v3(-2.8, sway * 0.6, 0.6),
               base + hm @ v3(-3.5, sway, -0.9)]
        for i in range(len(pts) - 1):
            P.add(L(pts[i], pts[i + 1], 0.8 - 0.1 * i, 0.7 - 0.12 * i, m.plume, "plume", line=False))
    if w.get("guan"):
        # The scholar's guan: a small cap over its topknot, a pin through it.
        q = hc + hm @ v3(-0.3, 0.0, hr[2] * 1.02)
        P.add(E(q, (0.95, 0.75, 0.7), m.hat, "guan", hm))
        P.add(L(q + hm @ v3(0.0, -1.2, 0.2), q + hm @ v3(0.0, 1.2, 0.2), 0.14, 0.14, m.trim, "pin", line=False))
    if w.get("epaulettes"):
        ea, eb, ec = w.epaulettes
        for s in (1, -1):
            q = up((ea, s * eb, ec))
            P.add(E(q, (1.05, 0.95, 0.42), m.trim, "epaulette%d" % s, tm @ rot("a", s * 20.0)))
            for k in range(3):
                P.mark(q + tm @ v3(-0.6 + 0.6 * k, s * 0.8, -0.5), M.RAMPS[m.trim][4])
    if w.get("buttons"):
        for k in range(w.buttons):
            P.mark(up((2.2 - 0.05 * k, 0.0, 6.3 - k * 0.8)), M.RAMPS[m.trim][4])
    if w.get("pauldrons"):
        pa, pb, pc = w.pauldrons
        for s in (1, -1):
            q = up((pa, s * pb, pc))
            mm = tm @ rot("a", s * 24.0)
            P.add(E(q, (2.2, 1.9, 1.3), m.iron, "pauldron%d" % s, mm))
            P.add(E(q + mm @ v3(0.0, s * 0.3, -0.85), (2.25, 1.95, 0.32), m.cord, "pauldron%d" % s, mm, line=False))
            P.mark(q + mm @ v3(0.7, 0.0, 1.2), M.RAMPS[m.trim][3])
    if w.get("beard") == "full":
        # A short full beard round his jaw and chin, a moustache over it.
        P.add(E(hc + hm @ v3(hr[0] * 0.55, 0.0, -hr[2] * 0.55), (hr[0] * 0.62, hr[1] * 0.92, hr[2] * 0.45), m.hair, "beard", hm, line=False))
        fc = B.parts.face
        ma, mb, mc = fc.mouth
        for s in (1, -1):
            P.add(L(hc + hm @ v3(ma + 0.15, s * 0.2, mc + 0.35), hc + hm @ v3(ma, s * (mb + 0.3), mc - 0.1), 0.26, 0.2, m.hair, "moustache", line=False))
    if w.get("beard") == "long":
        # A long white beard from its chin down over its chest.
        fc = B.parts.face
        ma, mb, mc = fc.mouth
        c0 = hc + hm @ v3(ma - 0.1, 0.0, mc - 0.4)
        sw = 0.2 * math.sin(f * 0.8)
        c1 = c0 + tm @ v3(0.5, sw, -2.4)
        c2 = c1 + tm @ v3(0.2, sw * 1.5, -2.2)
        P.add(L(c0, c1, 0.6, 0.48, m.hair, "longbeard", line=False), L(c1, c2, 0.48, 0.15, m.hair, "longbeard", line=False))
    if w.get("scar"):
        # A scar across his left eye.
        ea, eb, ec = B.parts.face.eyes
        for t in (-0.55, 0.0, 0.55):
            P.mark(hc + hm @ v3(ea + 0.05, eb + t * 0.4, ec + t), M.SCAR)
    if w.get("embers") and not dead:
        # The Ashborn's ember cracks: glowing seams in the ash of his face and down his forearms.
        for k, (u, v) in enumerate(((40.0, 10.0), (-35.0, 25.0), (55.0, -20.0))):
            P.mark(on(hc, hr, hm, u, v, 0.1), M.EMBER_CRACK if (k + f) % 3 else M.EMBER_CRACK_HI)
        for s in (1, -1):
            e, h_ = elbows[s], ends[s]
            for t in (0.25, 0.5, 0.75):
                P.mark(e + (h_ - e) * t + v3(0.0, 0.0, 0.9), M.EMBER_CRACK if t != 0.5 else M.EMBER_CRACK_HI)
    if w.get("halo"):
        _halo(P, B, action, f, hc, hm, tm, w.halo, ends[1])
    if w.get("mist"):
        # Fading, it comes apart into motes of the hall's light, from its hem up.
        fade = B.pick("fade", action, f)
        if fade > 0.0:
            P.dissolve = fade * 0.95
            P.dissolve_col = M.PRES_LIGHT
    if w.get("mist") and not dead:
        # Its hem thinning into mist: wisps under the robe, drifting.
        rb = B.parts.robe
        for k in range(16):
            ang = math.radians(k * 22.5 + f * 12.0)
            rr = rb.r[1] * (0.6 + 0.35 * ((k * 7) % 3) / 2.0)
            z = rb.get("hem", 0.3) - 0.4 - ((f * 0.4 + k * 0.37) % 1.4)
            q = v3(hip[0] * 0.6 + rb.lead + math.cos(ang) * rr, math.sin(ang) * rr, max(0.2, z))
            P.fx.append((q, M.PRES_MIST if k % 2 else M.PRES_MIST_DIM))
            P.fx.append((q + v3(0.0, 0.5, 0.0), M.PRES_MIST_DIM))


def _coat_tails(P, B, action: str, f: int, hip, tm, t) -> None:
    """A long coat's skirt from the waist to the knee (a cone, swinging as he walks), split up its front over the legs, its
    hem trimmed."""
    m, st = B.mats, B.style(action)
    sw = 0.5 * math.sin(f / 8.0 * math.tau) if st.get("kind") == "march" else 0.0
    top = hip + tm @ v3(0.15, 0.0, t.top)
    bot = v3(hip[0] * 0.7 + sw * 0.5 + t.lead, 0.0, t.hem)
    if action == "death" and B.pick("roll", action, f) > 30.0:
        bot = hip + tm @ v3(0.0, 0.0, t.top - 4.0)
    axis = (bot - top) / max(1e-6, float(np.linalg.norm(bot - top)))
    trim = t.get("trim", 0.45)
    lng = float(np.linalg.norm(bot - top))

    def paint(q, n, top=top, axis=axis):
        rel = q - top
        along = rel @ axis
        hem = along > lng - trim
        fold = ((np.arctan2(rel[:, 1], rel[:, 0]) * 2.4) % 1.0) < 0.2
        return np.where(hem, m.trim, m.coat).astype(object), np.where(fold & ~hem, -1, 0).astype(np.int16)

    split = t.split
    P.add(L(top, bot, t.r[0], t.r[1], m.coat, "tails", paint, caps=False,
            clip=lambda qs, c_=hip, s_=split: ~((((qs - c_) @ tm)[:, 0] > 0.6) & (np.abs(((qs - c_) @ tm)[:, 1]) < s_))))


def _cape4(P, B, action: str, f: int, up, tm, hip, cp) -> None:
    """A cape over his shoulders and down his back to `bottom`, billowing as he moves; a tattered one's hem torn ragged."""
    m, st = B.mats, B.style(action)
    sw = 0.5 * math.sin(f / 8.0 * math.tau) if st.get("kind") == "march" else 0.25 * math.sin(f * 0.9)
    top = up((-0.6, 0.0, cp.top))
    bot = v3(hip[0] - cp.back - 0.4 * abs(sw), sw * 0.6, cp.bottom)
    if action == "death" and B.pick("roll", action, f) > 30.0:
        bot = up((-cp.back, 0.0, cp.top - 5.0))
    axis = (bot - top) / max(1e-6, float(np.linalg.norm(bot - top)))
    lng = float(np.linalg.norm(bot - top))
    tatter = bool(cp.get("tatter"))

    def clip(qs, c_=hip, top=top, axis=axis):
        keep = (qs - c_)[:, 0] < -0.6
        if tatter:
            rel = qs - top
            along = rel @ axis
            ang = np.arctan2(rel[:, 1], rel[:, 0])
            keep &= along < lng - 0.9 - 0.9 * np.abs(np.sin(ang * 5.0 + f * 0.6))
        return keep

    def paint(q, n, top=top, axis=axis):
        rel = q - top
        fold = ((np.arctan2(rel[:, 1], rel[:, 0]) * 2.0) % 1.0) < 0.18
        return np.full(len(q), m.cape, dtype=object), np.where(fold, -1, 0).astype(np.int16)

    P.add(L(top, bot, cp.r[0], cp.r[1], m.cape, "cape", paint, caps=False, clip=clip))


def _halo(P, B, action: str, f: int, hc, hm, tm, h, hand) -> None:
    """The Ninth Presence's crown of nine lights: nine motes on an arc of gold standing behind its head and over it (an
    aureole: its lower half would cross its face, the lights being drawn over the body), swaying; gathered up into a
    blazing crown over its head in the tell (`halo`), thrown out round it on both sides on the blow (`burst`); going out
    one by one as it fades."""
    g = B.pick("halo", action, f)
    burst = B.pick("burst", action, f)
    fade = B.pick("fade", action, f)
    lit = int(round(h.n * (1.0 - fade)))
    a0, a1 = -25.0, 205.0
    if burst <= 0.0 and g < 0.5 and lit:
        # The arc the nine lights stand on: a thin line of gold light behind its head.
        for k in range(31):
            ang = math.radians(a0 + (a1 - a0) * k / 30.0)
            P.glow.append((hc + tm @ v3(-1.4, math.cos(ang) * h.r, math.sin(ang) * h.r + 0.9), M.PRES_RING))
    for k in range(lit):
        if burst > 0.0:
            ang = math.radians(k * 360.0 / h.n + f * 8.0)
            rr = h.r + 4.0 * burst
            q = v3(hc[0] - 1.0 + math.cos(ang) * rr * 0.9, math.sin(ang) * rr, hc[2] * 0.55)
        else:
            ang = math.radians(a0 + (a1 - a0) * k / (h.n - 1) + 5.0 * math.sin(f * 0.8))
            behind = hc + tm @ v3(-1.4, math.cos(ang) * h.r, math.sin(ang) * h.r + 0.9)
            crown = hc + v3(math.cos(ang) * 1.8, math.sin(ang) * 1.8, 3.4)
            q = behind + (crown - behind) * g
        P.glow.append((q, M.PRES_LIGHT_HI))
        for d in ((0.0, 0.45, 0.0), (0.0, -0.45, 0.0), (0.0, 0.0, 0.5), (0.0, 0.0, -0.5)):
            P.glow.append((q + v3(*d), M.PRES_LIGHT if (k + f) % 3 or g >= 0.8 or burst > 0.0 else M.PRES_RING))
    pm = B.pick("palm", action, f)
    if pm > 0.0:
        # The palm's ring: before its left hand.
        c = hand + tm @ v3(1.0 + pm * 0.6, 0.0, 0.0)
        for k in range(14):
            ang = math.radians(k * 360.0 / 14.0)
            rr = 1.0 + 1.2 * pm
            P.glow.append((c + tm @ v3(0.0, math.cos(ang) * rr, math.sin(ang) * rr), M.PRES_LIGHT_HI if k % 2 else M.PRES_LIGHT))


def _anchor(P, B, action: str, f: int, ends: dict, tm) -> None:
    """Comet Captain Rao's anchor of comet iron: a long shank in his right hand (a ring at its top, a stock across it), its
    crown and two curved flukes with spade palms at its far end, a chain from its ring to his left hand; over his shoulder
    at rest, raised high in both hands as comet fire runs along its flukes (`comet`), slammed down before him in a burst
    of comet sparks and dust (`impact`); dropped beside him as he falls."""
    h, m, st = B.parts.prop, B.mats, B.style(action)
    hand = ends[-1]
    d = v3(B.pick("anchor", action, f, (-0.62, -0.25, 0.74)))
    d = tm @ (d / float(np.linalg.norm(d)))
    if action == "death" and f >= 3:
        hand = v3(hand[0] + 1.0, hand[1] - 2.2, 0.5)
        d = v3(0.85, -0.5, 0.0)
        d = d / float(np.linalg.norm(d))
    side = np.cross(d, tm @ v3(1.0, 0.0, 0.0))
    if float(np.linalg.norm(side)) < 0.25:
        side = np.cross(d, v3(0.0, 0.0, 1.0))
    side = side / float(np.linalg.norm(side))
    nrm = np.cross(d, side)
    top = hand - d * 1.0
    crown = hand + d * h.shank
    P.add(L(top, crown, h.r, h.r * 1.15, m.iron, "shank"))
    rc = top - d * h.ring * 1.1
    for k in range(8):
        t = math.radians(k * 45.0)
        P.add(S(rc + (d * math.cos(t) + nrm * math.sin(t)) * h.ring, 0.24, m.iron, "ring", line=False))
    s0 = hand + d * 0.9
    P.add(L(s0 - nrm * h.stock * 0.5, s0 + nrm * h.stock * 0.5, 0.3, 0.3, m.iron, "stock"))
    P.add(S(crown, 0.85, m.iron, "crown"))
    tips = []
    fl = h.fluke
    for s in (1, -1):
        a1 = crown + side * s * fl * 0.65 - d * 0.2
        a2 = crown + side * s * fl * 0.95 - d * fl * 0.75
        P.add(L(crown, a1, 0.62, 0.56, m.iron, "fluke%d" % s), L(a1, a2, 0.56, 0.4, m.iron, "fluke%d" % s))
        palm = a2 - d * 0.1 + side * s * 0.2
        P.add(E(palm, (1.15, 0.8, 0.25), m.iron, "palm%d" % s, np.stack([_u(a2 - a1), side * s, nrm], axis=1)))
        tips.append(a2 + _u(a2 - a1) * 0.8)
        P.mark(a2 + _u(a2 - a1) * 0.85, M.RAMPS[m.iron][4])
    # The chain from its ring to his left hand, sagging.
    lh = ends[1]
    n = 8
    for k in range(1, n):
        t = k / n
        q = rc + (lh - rc) * t - v3(0.0, 0.0, 1.3 * math.sin(math.pi * t))
        P.add(S(q, 0.26, m.iron, "chain", line=False))
    comet = B.pick("comet", action, f)
    if comet > 0.0:
        pts = [crown] + tips + [crown + (tips[0] - crown) * 0.5, crown + (tips[1] - crown) * 0.5]
        nfl = 6 + int(10 * comet)
        for k in range(nfl):
            base = pts[k % len(pts)]
            q = base + side * (0.4 * math.sin(k * 2.1 + f)) + nrm * (0.4 * math.cos(k * 1.7 + f)) - d * (0.3 * (k % 3))
            P.glow.append((q, M.COMET_BLUE_HI if k % 3 == 0 else M.COMET_BLUE))
        for k in range(int(5 * comet)):
            q = crown + d * (0.8 + 0.7 * k) + side * (0.6 * math.sin(f + k)) + v3(0.0, 0.0, 0.3 * k)
            P.glow.append((q, M.COMET_BLUE))
    if action == "attack" and f in st.get("impact", ()):
        k0 = f - min(st.get("impact", (1,)))
        foot = v3(crown[0], crown[1], 0.3)
        rr = 2.6 + 2.4 * k0
        for k in range(24):
            ang = math.radians(k * 15.0 + f * 9.0)
            P.fx.append((foot + v3(math.cos(ang) * rr, math.sin(ang) * rr * 0.95, 0.2 + 0.4 * (k % 3 == 0)), M.DUST if k % 2 else M.DUST_DIM))
        for k in range(10):
            ang = math.radians(k * 36.0 + 10.0)
            q = foot + v3(math.cos(ang) * (1.2 + k0), math.sin(ang) * (1.2 + k0), 1.0 + 1.6 * (2 - k0) * (k % 2))
            P.glow.append((q, M.COMET_BLUE_HI if k % 2 else M.COMET_BLUE))


def _u(v):
    return v / max(1e-9, float(np.linalg.norm(v)))


def _sabre_cannon(P, B, action: str, f: int, ends: dict, tm) -> None:
    """Admiral Voss's arms: a starsteel sabre in his right hand (a long faintly curved blade of pale blue light, a gold
    guard), its arc of starsteel trailing it on the cut (`arc`); a brass hand cannon in his left (a short barrel banded in
    gold, a dragon's mouth at its muzzle, its fuse sparking at the breech in the tell, `fuse`), firing in a flash and a
    cloud of smoke on the blow (`flash`, `smoke`)."""
    h, m, st = B.parts.prop, B.mats, B.style(action)
    rh, lh = ends[-1], ends[1]
    d = v3(B.pick("sabre", action, f, (0.45, -0.25, -0.86)))
    d = tm @ (d / float(np.linalg.norm(d)))
    if action == "death" and f >= 3:
        rh = v3(rh[0] + 1.4, rh[1] - 2.0, 0.4)
        d = _u(v3(0.8, -0.6, 0.0))
    side = np.cross(d, v3(0.0, 0.0, 1.0))
    if float(np.linalg.norm(side)) < 0.2:
        side = np.cross(d, tm @ v3(1.0, 0.0, 0.0))
    side = _u(side)
    P.add(L(rh - d * 0.9, rh + d * 0.3, 0.28, 0.28, m.grip, "grip"))
    P.add(E(rh + d * 0.45, (0.25, 0.85, 0.6), m.trim, "guard", np.stack([d, side, np.cross(d, side)], axis=1)))
    mid = rh + d * (h.blade * 0.5 + 0.5) + side * 0.25
    tip = rh + d * (h.blade + 0.6) + side * 0.65
    P.add(L(rh + d * 0.55, mid, 0.34, 0.3, m.steel, "sabre"), L(mid, tip, 0.3, 0.1, m.steel, "sabre"))
    P.mark(tip, M.STARSTEEL_HI)
    for t in (0.3, 0.6, 0.85):
        P.glow.append((rh + d * (h.blade * t + 0.6) + side * (0.25 + 0.4 * t) + v3(0.0, 0.0, 0.25), M.STARSTEEL))
    if action == "attack" and f in st.get("arc", ()):
        for k in range(14):
            ang = math.radians(-60.0 + k * 10.0 + (f - 1) * 25.0)
            rr = h.blade + 1.0
            q = rh + tm @ v3(math.cos(ang) * rr * 0.6 - 1.0, math.sin(ang) * rr * 0.8, -0.8 + 0.1 * k)
            P.fx.append((q, M.STARSTEEL if k % 2 else M.STARSTEEL_HI))
    # The hand cannon.
    b = v3(B.pick("cannon", action, f, (0.8, 0.2, -0.55)))
    b = tm @ (b / float(np.linalg.norm(b)))
    if action == "death" and f >= 3:
        lh = v3(lh[0] - 1.0, lh[1] + 2.2, 0.4)
        b = _u(v3(0.4, 0.9, 0.0))
    breech = lh - b * 0.9
    muzzle = lh + b * h.barrel
    P.add(L(breech, muzzle, 0.55, 0.5, m.brass, "cannon"), S(breech, 0.62, m.brass, "cannon"))
    bs = _u(np.cross(b, v3(0.0, 0.0, 1.0)) if float(np.linalg.norm(np.cross(b, v3(0.0, 0.0, 1.0)))) > 0.2 else np.cross(b, v3(0.0, 1.0, 0.0)))
    bm = np.stack([b, bs, np.cross(b, bs)], axis=1)
    P.add(E(muzzle + b * 0.35, (0.5, 0.85, 0.8), m.brass, "muzzle", bm))
    for t in (0.25, 0.65):
        P.add(E(breech + (muzzle - breech) * t, (0.18, 0.62, 0.62), m.trim, "band", bm, line=False))
    for s in (1, -1):
        P.mark(muzzle + b * 0.75 + bs * s * 0.45, M.RAMPS[m.trim][4])     # the dragon's teeth at its lips
    fuse = B.pick("fuse", action, f)
    if fuse > 0.0:
        q = breech + v3(0.0, 0.0, 0.8)
        P.glow.append((q, M.SPARK))
        for k in range(1 + int(4 * fuse)):
            ang = math.radians(k * 72.0 + f * 50.0)
            P.glow.append((q + v3(math.cos(ang) * 0.6, math.sin(ang) * 0.6, 0.3 + 0.3 * (k % 2)), M.FLAME if k % 2 else M.SPARK_DIM))
        P.glow.append((muzzle + b * 1.0, M.FLAME))
    flash = B.pick("flash", action, f)
    if flash > 0.0:
        # The muzzle's flash: a star of fire, a white-hot heart.
        c = muzzle + b * (1.6 + 0.8 * flash)
        for k in range(16):
            ang = math.radians(k * 22.5)
            for rr, col in ((1.0 + 2.2 * flash * (1.0 if k % 2 else 0.6), M.FLAME), (0.6 + 1.0 * flash, M.FLAME_CORE)):
                P.glow.append((c + b * (0.8 * rr * (k % 2)) + bm @ v3(0.0, math.cos(ang) * rr, math.sin(ang) * rr), col))
        for t in (0.0, 0.5, 1.0, 1.5):
            P.glow.append((c + b * t, M.FLAME_CORE))
    if action == "attack" and f in st.get("smoke", ()):
        k0 = f - 1
        for k in range(14):
            ang = math.radians(k * 51.0)
            rr = 0.6 + 0.5 * k0
            q = muzzle + b * (2.2 + 0.9 * k0 + 0.25 * (k % 4)) + v3(0.0, 0.0, 0.5 + 0.5 * k0) + bm @ v3(0.0, math.cos(ang) * rr, math.sin(ang) * rr)
            P.fx.append((q, M.SMOKE if k % 2 else M.SMOKE_DIM))


def _glaive(P, B, action: str, f: int, ends: dict, tm) -> None:
    """General Kharn's Cinder Glaive: a long dark pole through both hands (an iron butt-spike below, a crimson tassel under
    its head), a great curved blade at its head with a back spike, its edge glowing with embers; bursting into flame up
    its blade as he raises it (`flame`), the ground set alight where it lands on the blow (`fire`)."""
    h, m, st = B.parts.prop, B.mats, B.style(action)
    hand = ends[-1]
    d = v3(B.pick("glaive", action, f, (0.08, -0.05, 1.0)))
    d = tm @ (d / float(np.linalg.norm(d)))
    if action == "death" and f >= 3:
        hand = v3(hand[0] + 1.6, hand[1] - 2.4, 0.4)
        d = _u(v3(0.9, -0.45, 0.0))
    butt = hand - d * h.below
    head = hand + d * h.above
    P.add(L(butt, head, h.r, h.r, m.shaft, "pole"))
    P.add(L(butt - d * 0.8, butt, 0.1, h.r, m.iron, "spike"))
    for t in (0.35, 0.7):
        P.add(E(hand + d * (h.above * t), (0.3, h.r * 1.25, h.r * 1.25), m.cord, "wrap", np.stack([d, _u(np.cross(d, v3(0.0, 0.0, 1.0)) if abs(d[2]) < 0.95 else v3(0.0, 1.0, 0.0)), np.cross(d, _u(np.cross(d, v3(0.0, 0.0, 1.0)) if abs(d[2]) < 0.95 else v3(0.0, 1.0, 0.0)))], axis=1), line=False))
    # The blade: a broad curved crescent forward of the head, its edge on the far side, a back spike behind it.
    # Its edge forward as it cuts; standing upright at his side, turned out to his right as well, so its broad blade shows
    # from the front.
    fwd = tm @ v3(1.0, 0.0, 0.0) + tm @ v3(0.0, -1.0, 0.0) * max(0.0, (abs(float(d[2])) - 0.5) * 2.0)
    side = _u(np.cross(d, v3(0.0, 0.0, 1.0)) if float(np.linalg.norm(np.cross(d, v3(0.0, 0.0, 1.0)))) > 0.2 else np.cross(d, fwd))
    edge = _u(fwd - d * float(fwd @ d)) if float(np.linalg.norm(fwd - d * float(fwd @ d))) > 0.2 else side
    bl, bw = h.blade
    bm = np.stack([d, edge, np.cross(d, edge)], axis=1)
    bc = head + d * (bl * 0.45) + edge * (bw * 0.6)
    P.add(E(bc, (bl * 0.6, bw, 0.26), m.blade, "blade", bm, _cinder_paint(m, bc, edge, bw)))
    P.add(E(head + d * (bl * 0.98) + edge * (bw * 1.0), (1.2, 0.7, 0.24), m.blade, "blade", bm @ rot("c", 30.0), _cinder_paint(m, bc, edge, bw)))
    P.add(L(head + d * 0.3 - edge * 0.2, head + d * 0.9 - edge * 1.8, 0.36, 0.1, m.iron, "backspike"))
    P.add(S(head, 0.55, m.trim, "collar"))
    sw = 0.3 * math.sin(f * 1.1)
    P.add(L(head - d * 0.2, head - d * 0.2 + v3(sw, 0.0, -1.6), 0.38, 0.5, m.cord, "tassel", line=False))
    # The embers along its edge; its flames.
    flame = B.pick("flame", action, f)
    for k in range(9):
        t = (k + 0.5) / 9.0
        q = head + d * (bl * (0.05 + 1.0 * t)) + edge * (bw * (1.5 - 0.6 * abs(t - 0.5)))
        P.glow.append((q, M.EMBER_CRACK_HI if (k + f) % 3 == 0 or flame > 0.5 else M.EMBER_CRACK))
    if flame > 0.0:
        # Flame licking up the blade: tongues rising off its edge.
        nf = 6 + int(12 * flame)
        for k in range(nf):
            t = ((k * 0.37 + f * 0.11) % 1.0)
            q = head + d * (bl * t) + edge * (bw * (1.3 + 0.3 * math.sin(k)))
            for j in range(1 + int(3 * flame)):
                P.glow.append((q + v3(0.0, 0.0, 0.4 + 0.7 * j), M.FLAME_CORE if j == 0 else (M.FLAME if j < 2 else M.FLAME_DEEP)))
    fire = B.pick("fire", action, f)
    if fire > 0.0:
        # The ground alight where it lands: a ring of flame tongues spreading out.
        c = v3(head[0] + d[0] * bl * 0.5, head[1] + d[1] * bl * 0.5, 0.3)
        rr = 2.0 + 2.6 * fire
        tall = 3.4 * (2.6 - fire) / 2.6 + 0.8
        for k in range(16):
            ang = math.radians(k * 22.5 + fire * 17.0)
            q = c + v3(math.cos(ang) * rr, math.sin(ang) * rr * 0.95, 0.2)
            h_ = tall * (0.45 + 0.55 * ((k * 7) % 3) / 2.0)
            side = v3(-math.sin(ang), math.cos(ang), 0.0) * 0.35
            for j in range(1 + int(h_ / 0.5)):
                z = 0.5 * j
                col = M.FLAME_CORE if z < h_ * 0.3 else (M.FLAME if z < h_ * 0.7 else M.FLAME_DEEP)
                P.glow.append((q + v3(0.0, 0.0, z), col))
                if z < h_ * 0.5:
                    P.glow.append((q + side + v3(0.0, 0.0, z), M.FLAME))
                    P.glow.append((q - side + v3(0.0, 0.0, z), M.FLAME_DEEP))


def _cinder_paint(m, c, edge, bw):
    """The glaive's blade: dark iron, its edge a step lit along its far side (the embers are its glow)."""
    def paint(q, n):
        v = (q - c) @ edge
        return np.full(len(q), m.blade, dtype=object), np.where(v > bw * 0.55, 2, np.where(v < -bw * 0.5, -1, 0)).astype(np.int16)
    return paint


def _nine_staff(P, B, action: str, f: int, ends: dict, tm) -> None:
    """The Ninth Presence's staff of white jade: tall in its right hand, a ring at its head holding nine small lights."""
    h, m, st = B.parts.prop, B.mats, B.style(action)
    hand = ends[-1]
    d = v3(0.05, -0.05, 1.0)
    d = tm @ (d / float(np.linalg.norm(d)))
    fade = B.pick("fade", action, f)
    if action == "death" and f >= 4:
        hand = v3(hand[0] + 1.6, hand[1] - 2.0, 0.4)
        d = _u(v3(0.9, -0.4, 0.0))
    butt = hand - d * h.below
    head = hand + d * h.above
    P.add(L(butt, head, h.r, h.r, m.staff, "staff"))
    side = _u(np.cross(d, v3(0.0, 0.0, 1.0)) if float(np.linalg.norm(np.cross(d, v3(0.0, 0.0, 1.0)))) > 0.2 else np.cross(d, tm @ v3(1.0, 0.0, 0.0)))
    ring = head + d * h.ring
    for k in range(12):
        t = math.radians(k * 30.0)
        P.add(S(ring + (d * math.cos(t) + side * math.sin(t)) * h.ring, 0.28, m.staff, "staffring", line=False))
    lit = int(round(9 * (1.0 - fade)))
    for k in range(lit):
        t = math.radians(k * 40.0 + f * 10.0)
        P.glow.append((ring + (d * math.cos(t) + side * math.sin(t)) * h.ring + v3(0.0, 0.0, 0.2), M.PRES_LIGHT_HI if k % 3 == 0 else M.PRES_LIGHT))


M4_PROPS = {"anchor": _anchor, "sabre_cannon": _sabre_cannon, "glaive": _glaive, "nine_staff": _nine_staff}
