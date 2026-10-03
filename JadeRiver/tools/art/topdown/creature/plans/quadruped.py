"""The four-legged plan (audit 45 §6.2), from the reed rat (`rodent`), the reed otter (`mustelid`) and the boarlets
(`suid`, and `suid` told `hollowed`).

A body of three ellipsoids (rump, barrel, shoulders, in the order the variant lays them) pitched on its hips; a head of
one of three kinds; four legs of one of three kinds; a tail of one of three kinds; and the options a species adds (a
bristle crest, the hollowed strands, the charge's dust). Every size is a part's parameter; a size that turns with the
facing is (x, head-on, tail-on): motion.headon's `fr` (facing the camera) and `bk` (walking away), x + kf fr + kb bk.

  head  rodent    a skull, a tapering snout limb to a nose bead, a jaw limb that drops in the gape, leaf ears (the rat)
        mustelid  a round skull and a pale muzzle, a nose mark, a jaw that hangs, round ears (the otter)
        suid      skull, jowls and a long snout to its disc, nostrils, tusks, two-mark eyes, pricked ears (the boarlets)
  legs  paw       a straight limb to a long foot, gait() pairs, the forepaws lifted when it rears (the rat)
        lope      a bounding lope, fore and hind pairs half a cycle apart (the otter)
        hoof      two-bone legs bent at knee and hock, hooves, the paw-scrape tell and the charge's reach (the boarlets)
  tail  reed      a long tail in alternating segments, swept to the side head-on (the rat)
        thick     a thick tapering tail, curled round in the fall (the otter)
        tassel    a short drooping tail with a dark tassel (the boarlets)
  coat  streak (the rat), pale_chest (the otter), youth (the boarlets' stripes and tufts)

M1 adds the dogs and cats (`canine`, from the ember fox; the mud hound, and the wolves and lynxes after, lay their parts
over it):
  head  canine    a skull on a neck, a tapering muzzle to a nose pad, a jaw that drops on its fangs and tongue, tall ears
                  (pricked, laid back in anger, one torn), eyes with a glint, the pale of the muzzle and cheeks (`mask`);
                  a short muzzle and wide ears make a cat of it; a collar round the neck (`collar`)
  legs  digit     two-bone legs on the toes, the elbow and the hock, socks, small paws; the pounce's reach, the bark's
                  brace, tucked when it curls
  tail  brush     a bushy tail swelling and tapering, its tip in its own colour, carried up or low, swept aside head-on;
                  a flame at its tip (`flame`, the ember fox: flaring in the tell)
  coat  bib       a pale throat, chest and belly; dried mud in blotches on its flanks and legs (`mud`)

M1's thornback boar is the suid overgrown: `coat` "vines" (green vines winding over its back and flanks, leaves on
them), `crest` "thorns" (pale woody thorns along its spine, bristling up in anger), and the head's `eyes.colour` (its
small fierce red eye) and `tusk` (a longer, upcurved tusk).

The motion styles (STYLES) are the hand modules' key-frame tables, named: idle `sniff`, `groom`, `browse`; walk
`bound`, `lope`, `trot`; windup `rear`, `sit_up`, `paw_ground`; attack `lunge_bite`, `lunge_shake`, `charge_toss`;
hurt `knock_squash`, `flinch`, `stumble`; death `topple_side`, `curl_side`, `buckle_roll`. M1's: idle `alert`, `pant`;
windup `crouch` (low, the tail raised), `bark` (the head up, barking); attack `pounce_bite` (the forepaws reaching).
"""
from __future__ import annotations

import math

import numpy as np

from figure.geom import ik2

from .. import mats as M
from ..motion import gait, h01v, headon, wave
from ..sculpt import E, L, Pose, S, chain, on, rot, v3
from .kit import colour, lin, shut, topple

# ------------------------------------------------------------------------------------------------ motion styles
STYLES = {
    # idle
    "sniff": {"head": (0.0, 4.0, -6.0, -4.0, 6.0, 2.0), "yaw": (0.0, 0.0, 14.0, 14.0, -10.0, 0.0), "bob_amp": 0.15,
              "sniff": (0.35, 0.1)},
    "groom": {"head": (0.0, 6.0, 10.0, -8.0, -14.0, -4.0), "yaw": (0.0, 18.0, 22.0, 0.0, -16.0, -8.0), "bob_amp": 0.12},
    "browse": {"head": (-2.0, -5.0, -12.0, -14.0, -8.0, -3.0), "bob_amp": 0.15, "breathe": 0.025, "sniff": (0.25, 0.3)},
    # walk
    "bound": {"kind": "bound", "pitch_amp": 6.0, "bob_wave": (0.6, 0.8)},
    "lope": {"kind": "lope", "arch_amp": 10.0, "bob_wave": (1.2, 0.6)},
    "trot": {"kind": "trot", "bob_wave": (-0.25, 0.4), "pitch_wave": (1.2, 0.6), "head_wave": (-6.0, 4.0, 1.4)},
    # windup
    "rear": {"lunge": (-0.4, -1.0, -1.4, -1.6), "pitch": (8.0, 18.0, 30.0, 36.0), "head": (6.0, 10.0, 12.0, 14.0),
             "gape": (0.2, 0.5, 0.8, 1.0), "squash": ((1.0, 0.94), (1.0, 1.0), (1.0, 1.0), (1.0, 1.02)),
             "tail": (1.0, 1.6, 2.2, 2.6), "reared": True},
    "sit_up": {"lunge": (-0.4, -0.8, -1.2, -1.2), "pitch": (16.0, 34.0, 46.0, 50.0), "head": (-6.0, -14.0, -22.0, -26.0),
               "gape": (0.2, 0.4, 0.7, 0.8)},
    "paw_ground": {"lunge": (-0.6, -1.2, -1.6, -2.0), "bob": (0.0, -0.3, -0.4, -0.8), "pitch": (-3.0, -5.0, -6.0, -8.0),
                   "head": (-14.0, -24.0, -28.0, -34.0),
                   "squash": ((1.0, 0.99), (0.99, 0.97), (0.98, 0.96), (0.97, 0.92)), "angry": True,
                   "paw": ((0.4, 0.0, 1.2), (-2.6, 0.0, 0.3), (0.9, 0.0, 1.6), (0.2, 0.0, 0.0)), "brace": 0.6,
                   "dust": (1, 2)},
    # attack
    "lunge_bite": {"lunge": (2.6, 4.8, 5.0, 4.2, 2.4, 0.8), "pitch": (-10.0, -6.0, -2.0, 0.0, 0.0, 0.0),
                   "head": (-12.0, -22.0, -18.0, -14.0, -6.0, 0.0), "yaw": (0.0, 0.0, 14.0, -14.0, 6.0, 0.0),
                   "gape": (1.0, 0.1, 0.0, 0.0, 0.2, 0.0),
                   "squash": ((1.15, 0.9), (0.92, 1.06), (1.0, 1.0), (1.0, 1.0), (1.0, 1.0), (1.0, 1.0)),
                   "tail": (0.4, -0.2, 0.0, 0.2, 0.4, 0.4)},
    "lunge_shake": {"lunge": (3.0, 5.4, 5.2, 4.4, 2.6, 0.8), "pitch": (-8.0, -4.0, 0.0, 0.0, 0.0, 0.0),
                    "head": (-10.0, -18.0, -8.0, -14.0, -4.0, 0.0), "yaw": (0.0, 0.0, 14.0, -14.0, 6.0, 0.0),
                    "gape": (0.9, 0.1, 0.1, 0.0, 0.1, 0.0),
                    "squash": ((1.14, 0.9), (0.93, 1.05), (1.0, 1.0), (1.0, 1.0), (1.0, 1.0), (1.0, 1.0))},
    "charge_toss": {"lunge": (2.6, 4.2, 4.6, 4.0, 2.6, 1.0), "bob": (0.9, 0.2, 0.0, -0.2, 0.0, 0.0),
                    "pitch": (1.0, 4.0, 6.0, 2.0, 0.0, -1.0), "head": (-22.0, 12.0, 24.0, 10.0, -4.0, -10.0),
                    "squash": ((1.14, 0.9), (0.93, 1.06), (0.97, 1.03), (1.03, 0.97), (1.0, 1.0), (1.0, 1.0)),
                    "angry": True, "reach": (((2.6, 0, 1.8), (-2.8, 0, 0.6)), ((1.2, 0, 0.0), (-1.4, 0, 0.0)),
                                             ((0.6, 0, 0.0), (-0.8, 0, 0.0)), ((1.0, 0, 0.0), (0.2, 0, 0.0))),
                    "dust": (1, 2, 3)},
    # hurt
    "knock_squash": {"lunge": (-2.4, -1.4, -0.4), "pitch": (14.0, 4.0, 0.0), "head": (18.0, 6.0, 0.0),
                     "gape": (0.6, 0.2, 0.0), "squash": ((0.88, 1.06), (1.04, 0.97), (1.0, 1.0))},
    "flinch": {"lunge": (-2.4, -1.4, -0.4), "pitch": (10.0, 2.0, 0.0), "head": (20.0, 6.0, 0.0), "gape": (0.5, 0.2, 0.0),
               "squash": ((0.88, 1.06), (1.03, 0.98), (1.0, 1.0))},
    "stumble": {"lunge": (-2.2, -1.6, -0.6), "bob": (0.3, -0.3, 0.0), "pitch": (5.0, -2.0, 0.0), "head": (16.0, -4.0, -8.0),
                "squash": ((0.9, 1.05), (1.04, 0.97), (1.0, 1.0)), "flinch": ((-0.8, 0.0, 0.6), (0.4, 0.0, 0.0))},
    # death
    "topple_side": {"lunge": (-0.8, -1.2, -1.2, -1.2, -1.2, -1.2, -1.2, -1.2), "pitch": (22.0, 10.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                    "head": (24.0, 10.0, 0.0, -6.0, -8.0, -8.0, -8.0, -8.0), "gape": (0.9, 0.6, 0.4, 0.3, 0.3, 0.3, 0.3, 0.3),
                    "roll": (0.0, 0.0, 30.0, 62.0, 86.0, 92.0, 88.0, 90.0), "tail": (1.0, 0.6, 0.4, 0.2, 0.0, -0.1, 0.0, 0.0),
                    "reared": (0, 1)},
    "curl_side": {"lunge": (-0.6, -0.8, -0.8, -0.8, -0.8, -0.8, -0.8, -0.8), "pitch": (24.0, 10.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                  "head": (20.0, 6.0, -6.0, -14.0, -18.0, -20.0, -20.0, -20.0),
                  "roll": (0.0, 0.0, 28.0, 60.0, 84.0, 90.0, 88.0, 90.0), "curl": (0.0, 0.0, 0.2, 0.4, 0.6, 0.8, 0.9, 1.0)},
    # M1, the canines
    "alert": {"head": (0.0, 3.0, 6.0, 4.0, 0.0, -2.0), "yaw": (0.0, 8.0, 16.0, 12.0, -8.0, -4.0), "bob_amp": 0.12,
              "ears": (0.0, 0.0, 0.0, 1.0, 0.0, 0.0)},
    "pant": {"head": (0.0, 2.0, 0.0, 2.0, 0.0, 2.0), "yaw": (0.0, 0.0, 10.0, 10.0, -8.0, 0.0), "bob_amp": 0.18,
             "gape": (0.35, 0.5, 0.35, 0.5, 0.35, 0.5), "tongue": True},
    "crouch": {"lunge": (-0.4, -0.9, -1.3, -1.5), "bob": (-0.4, -1.0, -1.5, -1.7), "pitch": (-2.0, -4.0, -5.0, -5.0),
               "head": (-6.0, -12.0, -16.0, -18.0), "gape": (0.0, 0.0, 0.15, 0.25), "tail": (0.4, 0.8, 1.0, 1.1),
               "squash": ((1.0, 0.98), (1.02, 0.96), (1.03, 0.94), (1.04, 0.93)), "angry": True, "flare": (0, 1, 2, 3)},
    "bark": {"lunge": (-0.3, -0.6, -0.8, -0.9), "pitch": (4.0, 8.0, 10.0, 10.0), "head": (8.0, 18.0, 22.0, 20.0),
             "gape": (0.3, 1.0, 0.35, 1.0), "tail": (0.3, 0.5, 0.6, 0.6), "brace": 0.6, "angry": True, "barks": (1, 3)},
    "pounce_bite": {"lunge": (3.0, 5.4, 5.4, 4.4, 2.4, 0.8), "bob": (2.2, 0.5, 0.0, 0.0, 0.0, 0.0),
                    "pitch": (8.0, -6.0, -2.0, 0.0, 0.0, 0.0), "head": (-4.0, -22.0, -16.0, -10.0, -4.0, 0.0),
                    "yaw": (0.0, 0.0, 12.0, -12.0, 5.0, 0.0), "gape": (1.0, 0.1, 0.0, 0.0, 0.2, 0.0),
                    "squash": ((1.15, 0.9), (0.92, 1.06), (1.0, 1.0), (1.0, 1.0), (1.0, 1.0), (1.0, 1.0)),
                    "tail": (0.6, 0.2, 0.2, 0.3, 0.4, 0.4), "angry": True,
                    "reach": (((2.6, 0.0, 1.6), (-1.6, 0.0, 0.4)), ((1.6, 0.0, 0.0), (-0.6, 0.0, 0.0)), ((0.8, 0.0, 0.0), (-0.3, 0.0, 0.0)))},
    "buckle_roll": {"lunge": (-1.2, -1.6, -1.6, -1.4, -1.2, -1.0, -1.0, -1.0), "bob": (0.4, -0.6, -1.6, -1.8, -1.9, -2.0, -2.0, -2.0),
                    "pitch": (6.0, -8.0, -12.0, -8.0, -4.0, 0.0, 0.0, 0.0), "head": (20.0, 8.0, -10.0, -14.0, -16.0, -18.0, -18.0, -18.0),
                    "squash": ((1.0, 1.0),) * 5 + ((1.02, 0.95), (1.0, 1.0), (1.0, 1.0)),
                    "roll": (0.0, 0.0, 8.0, 34.0, 64.0, 88.0, 84.0, 86.0),
                    "dissolve": (0.0, 0.0, 0.0, 0.0, 0.12, 0.34, 0.62, 0.9),
                    "fold_front": (0.0, 0.8, 1.0, 1.0, 0.8, 0.5, 0.4, 0.4), "fold_hind": (0.0, 0.0, 0.3, 0.5, 0.5, 0.4, 0.3, 0.3)},
}

# ------------------------------------------------------------------------------------------------ variants
# A body piece: (where along it: (a, kf), height c), radii ((x, kf, kb) x 3), and `arch` (it bends against the lope).
RODENT = {
    "Z": 4.6, "hips": (-3.6, -0.2), "pivot": (-3.6, 0.0, -0.2), "side": 3.3,
    "body": [{"at": ((-3.8, 1.2), -0.1), "r": ((3.8, 0.0, 0.0), (3.9, 0.0, 0.3), (3.6, 0.0, 0.2))},
             {"at": ((-0.6, 0.5), 0.2), "r": ((5.2, -1.0, 0.0), (3.3, 0.3, 0.0), (3.2, 0.0, 0.0))},
             {"at": ((2.6, 0.0), 0.4), "r": ((2.8, 0.0, 0.0), (2.8, 0.4, 0.0), (2.8, 0.0, 0.0))}],
    "coat": {"kind": "streak", "belly": -0.2, "streak": (0.8, 0.6, 0.15)},
    "head": {"kind": "rodent", "yaw": 0.5, "pitch": (-10.0, 0.0, 4.0), "at": ((5.4, 0.0), (1.2, 0.0, 0.0)),
             "skull": (3.0, 2.6, 2.4), "snout": ((1.2, 0.0, -0.3), (4.2, 0.0, -0.7), 1.9, 0.9),
             "nose": {"kind": "bead", "at": (4.6, 0.0, -0.6), "r": 0.75},
             "jaw": {"kind": "limb", "gape": 0.05, "turn": 32.0, "at": (0.8, 0.0, -1.4), "to": (2.8, 0.0, -0.2), "r": (1.1, 0.6),
                     "teeth": ((4.0, 0.35, -1.3), (4.0, -0.35, -1.3)), "tooth": (0xF2, 0xE2, 0x9A, 255)},
             "ears": {"kind": "leaf", "roll": (18.0, 22.0), "yaw": 20.0, "at": ((-1.0, 0.2), (1.7, 0.6, 0.2), (2.3, 0.4, 0.5)),
                      "r": (0.8, (1.5, -0.2, 0.0), (1.8, -0.2, 0.0)), "inner": (0.8, 0.0, 0.2)},
             "eyes": {"at": (1.6, 1.75, 0.9), "glint": (1.8, 1.65, 1.2), "colour": "RAT_EYE", "shut": {"hurt": 0, "death": 5},
                      "shut_step": 0},
             "whiskers": {"n": 3, "at": (3.4, 1.7, -0.4), "step": (0.3, 0.55, -0.35)}},
    "legs": {"kind": "paw", "fore": (3.2, (1.6, 0.9, 0.3)), "hind": ((-4.4, 1.2), (2.2, 0.4, 1.9)), "narrow": 0.25,
             "lift": (1.6, 0.7), "stride": 2.2, "hind_off": 0.45, "top": (-1.6, -1.0), "reach": ((0.6, 0.6), 1.4),
             "rear": ((-1.4,), (1.4, 0.0, -1.2)), "r": ((1.05, 1.4), 0.75), "foot": ((0.5, 0.9), ((1.0, 1.6), 0.8, 0.5))},
    "tail": {"kind": "reed", "n": 14, "root": ((-7.2, 1.2), -0.2), "r": (1.05, 0.45, 0.035)},
}
MUSTELID = {
    "Z": 5.0, "hips": (-4.6, 0.0), "pivot": (-4.6, 0.0, 0.0), "side": 3.3, "curl_yaw": 35.0, "arch": 0.5,
    "body": [{"at": ((0.8, 0.6), 0.3), "r": ((6.0, -1.4, 0.0), (3.3, 0.3, 0.2), (3.1, 0.0, 0.0)), "arch": 0.6},
             {"at": ((-4.6, 1.6), 0.0), "r": ((3.9, 0.0, 0.0), (3.7, 0.0, 0.5), (3.4, 0.0, 0.0))},
             {"at": ((4.6, 0.0), 0.8), "r": ((2.8, 0.0, 0.0), (2.8, 0.5, 0.0), (2.9, 0.0, 0.0))}],
    "coat": {"kind": "pale_chest", "chest": (-0.05, -0.3, 3.0), "streak": (0.5, 0.9, 1.6, 0.5, 0.2)},
    "head": {"kind": "mustelid", "yaw": 0.5, "pitch": (-8.0, 0.9, 10.0), "at": ((7.4, -0.4), (1.6, 0.4, 0.8)),
             "skull": (2.9, 2.7, 2.5), "muzzle": ((2.4, 0.0, -0.6), (1.6, 1.9, 1.3)),
             "nose": {"kind": "mark", "at": (3.9, 0.0, -0.2), "colour": "INKY"},
             "jaw": {"kind": "drop", "gape": 0.1, "turn": 30.0, "at": (1.2, 0.0, -1.5), "to": (1.4, 0.0, -0.2), "r": (1.6, 1.3, 0.6),
                     "teeth": ((3.2, 0.5, -1.1), (3.2, -0.5, -1.1)), "tooth": (0xF4, 0xEE, 0xDC, 255)},
             "ears": {"kind": "round", "at": ((-0.7, -0.2), (2.2, 0.3, 0.2), (1.9, 0.0, 0.3)), "r": (0.8, 0.15)},
             "eyes": {"at": (1.5, 1.65, 1.2), "glint": (1.7, 1.5, 1.5), "colour": "INKY", "shut": {"hurt": 0, "death": 4},
                      "shut_step": 1},
             "whiskers": {"n": 3, "at": (2.6, 1.9, -0.4), "step": (0.4, 0.5, -0.3)}},
    "legs": {"kind": "lope", "fore": (3.6, (2.2, 1.1, 0.4)), "hind": (-5.6, (2.5, 0.5, 1.5)), "narrow": 0.2, "stride": 2.4,
             "lift": (1.2, 0.8), "r": (1.25, 1.0), "foot": (0.5, (1.1, 0.9, 0.5))},
    "tail": {"kind": "thick", "n": 8, "length": 8.2, "r": (1.7, 0.9), "wag": (1.2, 1.0)},
}
SUID = {
    "Z": 8.4, "hips": (-1.4, 0.0), "pivot": (0.0, 0.0, 0.0), "side": 4.6,
    "body": [{"at": ((3.2, 0.0), 1.0), "r": ((4.4, 0.0, 0.0), (4.9, 0.8, 0.0), (5.2, 0.0, 0.0))},
             {"at": ((-0.2, 0.5), 0.0), "r": ((5.9, -1.0, 0.0), (4.9, 0.4, 0.3), (4.3, 0.0, 0.0))},
             {"at": ((-4.4, 1.4), 0.3), "r": ((3.6, 0.0, 0.0), (4.1, 0.0, 0.7), (4.0, 0.0, 0.4))}],
    "coat": {"kind": "youth"},
    "crest": {"n": 8},
    "head": {"kind": "suid", "rest": -6.0, "pitch": (-4.0, 12.0), "at": ((7.8, -0.6), (-0.6, 0.5)), "skull": (4.2, 3.8, 3.7),
             "eyes": {"shut": {"hurt": 0, "death": 5}}},
    "legs": {"kind": "hoof"},
    "tail": {"kind": "tassel"},
    "dust": True,
}
# M1: the ember fox (its side-view sheet: ~22 px to the ear tips, ~30 long with the tail): a slim body low on long legs,
# a fine muzzle, tall ears, a white bib, dark socks, a bushy tail.
CANINE = {
    "Z": 6.2, "hips": (-3.2, 0.3), "pivot": (-3.2, 0.0, 0.3), "side": 2.7, "curl_yaw": 32.0, "arch": 0.0,
    "body": [{"at": ((2.8, 0.3), 0.7), "r": ((3.0, 0.0, 0.0), (2.4, 0.5, 0.0), (2.7, 0.0, 0.0))},
             {"at": ((-0.4, 1.2), 0.3), "r": ((4.0, -2.0, 0.0), (2.2, 0.3, 0.2), (2.3, -0.3, 0.0))},
             {"at": ((-3.6, 2.6), (0.5, -0.6, 0.0)), "r": ((2.6, -0.6, 0.0), (2.4, 0.0, 0.5), (2.5, -0.4, 0.3))}],
    "coat": {"kind": "bib", "chest": (-0.1, 1.2), "belly": -0.55, "mud": None},
    "head": {"kind": "canine", "at": ((6.0, 1.0), (2.7, 3.2, 0.6)), "pitch": (-6.0, 24.0), "skull": (2.4, 2.25, 2.0),
             "neck": ((3.6, 0.0, 1.0), 1.7, 1.3),
             "muzzle": ((1.2, 0.0, -0.5), (4.6, 0.0, -1.0), 1.15, 0.45), "nose": ((4.8, 0.0, -0.85), 0.55),
             "jaw": {"at": (1.0, 0.0, -1.2), "to": (3.0, 0.0, -0.3), "r": (0.85, 0.45), "turn": 34.0, "teeth": (3.6, 0.45, -1.4),
                     "tongue": ((2.4, 0.0, -0.2), (1.4, 0.7, 0.35))},
             "ears": {"base": (-0.5, 1.2, 1.35), "tip": (-0.9, 1.8, 4.8), "r": (1.2, 0.12), "spread": (0.7, 1.3), "back": 2.2,
                      "torn": 0, "tip_dark": True},
             "eyes": {"at": (1.55, 1.15, 0.45), "colour": "FOX_EYE", "shut": {"hurt": 0, "death": 5}},
             "mask": (-0.35, 0.6)},
    "legs": {"kind": "digit", "fore": (2.9, (1.4, 0.8, 0.3)), "hind": (-3.7, (1.5, 0.4, 0.9)), "top": (-1.4, -1.0),
             "bones": ((2.9, 2.8), (3.1, 3.0)), "r": ((1.05, 0.62), (1.35, 0.62)), "paw": (0.8, 0.62, 0.48),
             "lift": (1.5, 0.6), "stride": 2.0},
    "tail": {"kind": "brush", "root": (-5.6, 1.3), "n": 8, "length": 7.6, "r": (0.8, 1.9, 0.5), "rest": 12.0, "droop": -26.0,
             "tip": 0.3, "flame": False},
}
VARIANTS = {
    "canine": {"parts": CANINE, "mats": {"coat": "fox_fur", "pale": "fox_white", "sock": "fox_sock", "ear_in": "fox_ear_in",
                                         "tip": "fox_white", "nose": "hound_nose", "tongue": "tongue"},
               "motion": {"idle": "alert", "walk": "trot", "windup": "crouch", "attack": "pounce_bite", "hurt": "knock_squash",
                          "death": "curl_side"}},
    "rodent": {"parts": RODENT, "mats": {"coat": "fur", "pale": "fur_light", "pink": "pink", "tail": ("tail_a", "tail_b")},
               "motion": {"idle": "sniff", "walk": "bound", "windup": "rear", "attack": "lunge_bite", "hurt": "knock_squash",
                          "death": "topple_side"}},
    "mustelid": {"parts": MUSTELID, "mats": {"coat": "otter", "pale": "otter_pale", "dark": "otter_dark"},
                 "motion": {"idle": "groom", "walk": "lope", "windup": "sit_up", "attack": "lunge_shake", "hurt": "flinch",
                            "death": "curl_side"}},
    "suid": {"parts": SUID, "mats": {"hide": "hide", "head": "hide_head", "stripe": "stripe", "hoof": "hoof", "snout": "snout",
                                     "bristle": "bristle", "tusk": "tusk", "ear": ("pink", 1)},
             "motion": {"idle": "browse", "walk": "trot", "windup": "paw_ground", "attack": "charge_toss", "hurt": "stumble",
                        "death": "buckle_roll"}},
}
# The hollowed boarlets' materials (the boarlet with its colour drunk out of it).
HOLLOWED_SUID = {"hide": "h_hide", "head": "h_head", "stripe": "h_stripe", "hoof": "h_bristle", "snout": "h_snout",
                 "bristle": "h_bristle", "tusk": "tusk", "ear": ("h_snout", 1)}


class _F:
    """One frame's state: the action and frame, the facing's fr and bk, the body's motion values and its frame."""


def pose(B, action: str, f: int, view: float = 48.0) -> Pose:
    P = Pose()
    p = B.parts
    c = _F()
    c.action, c.f = action, f
    # Head-on (decision 44): facing the camera the face lifts and the forelegs stand apart, walking away the rump
    # rounds and the hind legs spread (motion.headon).
    c.fr, c.bk = headon(view)
    _motion(B, c)
    _frame(B, c)
    _body(P, B, c)
    if "crest" in p:
        _crest(P, B, c)
    {"rodent": _head_snout, "mustelid": _head_snout, "suid": _head_suid, "canine": _head_canine}[p.head.kind](P, B, c)
    {"paw": _legs_paw, "lope": _legs_lope, "hoof": _legs_hoof, "digit": _legs_digit}[p.legs.kind](P, B, c)
    {"reed": _tail_reed, "thick": _tail_thick, "tassel": _tail_tassel, "brush": _tail_brush}[p.tail.kind](P, B, c)
    if B.opts.get("hollowed") and action != "death":
        _strands(P, B, c)
    if p.get("dust"):
        _dust(P, B, c)
    _finish(P, B, c)
    return P


def _motion(B, c) -> None:
    """The body's motion this frame: lunge, pitch, bob (and the lope's arch, the fall's curl), the head's pitch where the
    walk drives it, and the squash."""
    a, f = c.action, c.f
    st = B.style(a)
    c.lunge = B.pick("lunge", a, f)
    c.pitch = B.pick("pitch", a, f)
    c.bob = B.pick("bob", a, f)
    c.arch = 0.0
    c.hpitch = B.pick("head", a, f, B.parts.head.get("rest", 0.0))
    kind = st.get("kind")
    if a == "idle":
        c.bob = st.bob_amp * wave(a, f)
    elif kind == "bound":                       # a bounding scurry: the back arches and stretches
        c.pitch = st.pitch_amp * math.sin(f / 8.0 * math.tau)
        c.bob = st.bob_wave[0] * max(0.0, math.sin(f / 8.0 * math.tau + st.bob_wave[1]))
    elif kind == "lope":                        # the lope: arched, then stretched long
        c.arch = st.arch_amp * math.sin(f / 8.0 * math.tau)
        c.bob = st.bob_wave[0] * max(0.0, math.sin(f / 8.0 * math.tau + st.bob_wave[1]))
    elif kind == "trot":                        # diagonal pairs: two bobs a cycle
        c.bob = st.bob_wave[0] + st.bob_wave[1] * math.cos(f / 8.0 * 4.0 * math.pi)
        c.pitch = st.pitch_wave[0] * math.sin(f / 8.0 * 4.0 * math.pi + st.pitch_wave[1])
        c.hpitch = st.head_wave[0] + st.head_wave[1] * math.sin(f / 8.0 * 4.0 * math.pi + st.head_wave[2])
    c.sa, c.sc = B.pick("squash", a, f, (1.0, 1.0))
    if a == "idle" and "breathe" in st:
        c.sc = 1.0 + st.breathe * wave(a, f)
    c.curl = B.pick("curl", a, f)
    c.z = B.parts.Z + c.bob


def _frame(B, c) -> None:
    """The hips (where the body pitches from) and `at`, a point of the body in the creature's frame."""
    p = B.parts
    c.hips = v3(c.lunge + p.hips[0], 0.0, c.z + p.hips[1])
    if "curl_yaw" in p:
        c.bm = rot("b", c.pitch + c.arch * p.arch) @ rot("c", c.curl * p.curl_yaw)
    else:
        c.bm = rot("b", c.pitch)
    piv = v3(p.pivot)
    hips, bm = c.hips, c.bm
    c.at = lambda q: hips + bm @ (v3(q) - piv)
    c.paint = _coat(B, c)


# ------------------------------------------------------------------------------------------------ coats
def _coat(B, c):
    co, m = B.parts.coat, B.mats
    hips, bm = c.hips, c.bm
    if co.kind == "streak":
        def coat(q, n):
            """The pale belly underneath; darker streaks over the back."""
            loc = (q - hips) @ bm
            nz = (n @ bm)[:, 2]
            belly = nz < co.belly
            streak = ((loc[:, 0] * co.streak[0] + np.abs(loc[:, 1]) * co.streak[1]) % 1.0 < co.streak[2]) & (nz > -0.1)
            return np.where(belly, m.pale, m.coat).astype(object), np.where(streak & ~belly, -1, 0).astype(np.int16)
        return coat
    if co.kind == "pale_chest":
        def coat(q, n):
            """The pale throat and chest under the forebody, a sleek sheen of darker streaks along the back."""
            loc = (q - hips) @ bm
            nl = n @ bm
            pale = (nl[:, 2] < co.chest[0]) & (nl[:, 0] > co.chest[1]) & (loc[:, 0] > co.chest[2])
            s = co.streak
            streak = ((loc[:, 0] * s[0] + np.abs(loc[:, 1]) * s[1]) % s[2] < s[3]) & (nl[:, 2] > s[4])
            return np.where(pale, m.pale, m.coat).astype(object), np.where(streak & ~pale, -1, 0).astype(np.int16)
        return coat

    if co.kind == "vines":
        seed = int(B.opts.get("seed", 0))

        def vines(q, n):
            """M1, the thornback boar: a dark hide with green vines winding over its back and down its flanks (two
            twisting bands), their leaves a step lit, the bristles' grain a step dark."""
            loc = (q - hips) @ bm
            nz = (n @ bm)[:, 2]
            a, b, c3 = loc[:, 0], loc[:, 1], loc[:, 2]
            u = a * co.twist + np.arctan2(b, c3) * 1.6
            band = (np.abs(np.sin(u)) < co.width) & (nz > -0.3)
            leaf = band & (h01v(np.floor(a * 1.6 + 40), np.floor(b * 1.6 + 40), seed % 97 + 3) > 0.8)
            grain = ((a * 0.62 + 0.45 * np.sin(c3 * 0.9 + np.abs(b) * 1.7)) % 1.0 < 0.14) & ~band
            names = np.where(leaf, m.leaf, np.where(band, m.vine, m.hide)).astype(object)
            return names, np.where(grain, -1, np.where(leaf, 1, 0)).astype(np.int16)
        return vines

    if co.kind == "bib":
        seed = int(B.opts.get("seed", 0))

        def coat(q, n):
            """M1, the canines: the pale throat and chest under the forebody and the pale belly; dried mud in blotches on the
            flanks and haunches (`mud`: the share of them left clean), a step darker at their edges."""
            loc = (q - hips) @ bm
            nl = n @ bm
            pale = ((nl[:, 2] < co.chest[0]) & (loc[:, 0] > co.chest[1])) | (nl[:, 2] < co.belly)
            names = np.where(pale, m.pale, m.coat).astype(object)
            bias = np.zeros(len(q), dtype=np.int16)
            if co.get("mud") is not None:
                h = h01v(np.floor(loc[:, 0] * 0.9 + 40), np.floor(loc[:, 2] * 0.9 + np.abs(loc[:, 1]) * 0.6 + 40), seed % 97 + 1)
                mud = (h > co.mud) & (nl[:, 2] < 0.55) & ~pale
                names = np.where(mud, m.mud, names).astype(object)
                bias = np.where(mud & (h < co.mud + 0.04), -1, 0).astype(np.int16)
            return names, bias
        return coat

    def hide(q, n):
        """The pale stripes of its youth along the back and flanks, and short tufts of fur (a groove a step down)."""
        loc = (q - hips) @ bm
        nz = (n @ bm)[:, 2]
        b = np.abs(loc[:, 1])
        a = loc[:, 0]
        on_back = (nz > 0.2) & (a > -2.6 - 1.2 * (b < 1.6)) & (a < 4.6)       # fading out over the rump
        stripe = on_back & (((b > 1.0) & (b < 1.55)) | ((b > 2.6) & (b < 3.05)))
        u = a * 0.62 + 0.45 * np.sin(loc[:, 2] * 0.9 + b * 1.7)
        fr = u - np.floor(u)
        tuft = (fr < 0.16) & ~stripe & (nz > -0.6)
        names = np.where(stripe, m.stripe, m.hide).astype(object)
        bias = np.where(tuft, -1, 0).astype(np.int16)
        return names, bias
    return hide


def _skin(B) -> str:
    """The coat's own material (the head and legs are of it)."""
    return B.mats.get("coat") or B.mats.hide


# ------------------------------------------------------------------------------------------------ body
def _body(P, B, c) -> None:
    fr, bk, at, bm = c.fr, c.bk, c.at, c.bm
    for piece in B.parts.body:
        (a, kf), h = piece.at
        r = tuple(lin(x, fr, bk) for x in piece.r)
        m = bm @ rot("b", -c.arch * piece.arch) if "arch" in piece else bm
        P.add(E(at((a + kf * fr, 0.0, lin(h, fr, bk))), r, _skin(B), "body", m, c.paint))


def _crest(P, B, c) -> None:
    """The bristle crest from the nape down the spine, stirring; raised in anger. M1: `kind` "thorns", pale woody thorns
    along the spine, longer and bristling up further in anger."""
    a, f, at, bm = c.action, c.f, c.at, c.bm
    angry = B.style(a).get("angry", False)
    cr = B.parts.crest
    if cr.get("kind") == "thorns":
        for k in range(cr.n):
            a0 = cr.at[0] - k * cr.step
            u = k / max(1.0, cr.n - 1.0)
            top = cr.at[1] - cr.sag * u * u
            for s in ((0,) if k % 2 == 0 else (1, -1)):
                base = at((a0, s * cr.side, top - 0.6))
                tall = cr.length * (0.75 + 0.35 * math.sin(k * 2.1 + 1.0)) * (1.35 if angry else 1.0)
                tip = base + bm @ v3(-0.9 - (0.0 if angry else 0.5), s * 0.7, tall)
                P.add(L(base, tip, cr.r, 0.12, B.mats.thorn, "thorn", line=False))
        return
    stir = {"idle": 0.3 * wave(a, f), "walk": 0.4 * wave(a, f, 0.25)}.get(a, 0.0)
    if angry:
        stir = -0.5
    for k in range(B.parts.crest.n):
        a0 = 5.0 - k * 1.3
        top = 5.4 - max(0, k - 2) * 0.28
        base = at((a0, 0.0, top - 0.5))
        lean = -0.8 + stir * (0.6 if k % 2 else -0.4)
        tip = base + bm @ v3(lean, 0.0, 1.5 + (0.6 if angry else 0.0) - k * 0.08)
        P.add(L(base, tip, 0.62, 0.22, B.mats.bristle, "crest", line=False))


# ------------------------------------------------------------------------------------------------ heads
def _head_snout(P, B, c) -> None:
    """The rat's and the otter's head: a skull with a snout (a tapering limb to a bead) or a muzzle, a jaw that drops in
    the gape on its teeth, ears (leaves or rounds), eyes with a glint (shut when struck or beaten) and whiskers."""
    h, m = B.parts.head, B.mats
    a, f, fr, bk, at, bm = c.action, c.f, c.fr, c.bk, c.at, c.bm
    st = B.style(a)
    sniff = st.sniff[0] * wave(a, f, st.sniff[1]) if a == "idle" and "sniff" in st else 0.0
    yaw = B.pick("yaw", a, f) * (1.0 - h.yaw * fr)
    if h.kind == "mustelid":                     # the head held up against the body's rearing
        hm = bm @ rot("c", yaw) @ rot("b", h.pitch[0] - c.pitch * h.pitch[1] + c.hpitch + h.pitch[2] * fr)
    else:
        hm = bm @ rot("c", yaw) @ rot("b", h.pitch[0] + c.hpitch + h.pitch[2] * fr)
    (ha, hf), hz = h.at
    hc = at((ha + sniff + hf * fr if sniff else ha + hf * fr, 0.0, lin(hz, fr, bk)))
    hp = lambda q: hc + hm @ v3(q)
    gape = B.pick("gape", a, f)
    P.add(E(hc, h.skull, m.coat, "head", hm, c.paint))
    if "snout" in h:
        q0, q1, r0, r1 = h.snout
        P.add(L(hp(q0), hp(q1), r0, r1, m.coat, "head"))
    else:
        P.add(E(hp(h.muzzle[0]), h.muzzle[1], m.pale, "head", hm))
    if h.nose.kind == "bead":
        P.add(S(hp(h.nose.at), h.nose.r, m.pink, "nose"))
    else:
        P.mark(hp(h.nose.at), colour(h.nose.colour))
    j = h.jaw
    if gape > j.gape:
        jm = hm @ rot("b", -gape * j.turn)
        if j.kind == "limb":
            P.add(L(hp(j.at), hp(j.at) + jm @ v3(j.to), j.r[0], j.r[1], m.pale, "jaw"))
        else:
            P.add(E(hp(j.at) + jm @ v3(j.to), j.r, m.pale, "jaw", jm))
        for t in j.teeth:
            P.mark(hp(t), j.tooth)
    e, ey = h.ears, h.eyes
    for s in (1, -1):
        if e.kind == "leaf":
            ear_m = hm @ rot("a", s * -(e.roll[0] + e.roll[1] * fr)) @ rot("c", s * e.yaw * (1.0 - fr))
            ea, eb, ec = e.at
            ear = hp((ea[0] * (1.0 + ea[1] * bk), s * lin(eb, fr, bk), lin(ec, fr, bk)))
            P.add(E(ear, tuple(lin(x, fr, bk) for x in e.r), m.pink, "ear%d" % s, ear_m))
            P.mark(ear + ear_m @ v3(e.inner), M.RAMPS[m.pink][0])
        closed = shut(ey, a, f)
        (P.mark if closed else P.eye)(hp((ey.at[0], s * ey.at[1], ey.at[2])),
                                      M.RAMPS[m.coat][ey.shut_step] if closed else colour(ey.colour))
        if not closed:
            P.mark(hp((ey.glint[0], s * ey.glint[1], ey.glint[2])), M.GLINT)
        if e.kind == "round":
            ea, eb, ec = e.at
            P.add(S(hp((ea[0] + ea[1] * bk, s * lin(eb, fr, bk), lin(ec, fr, bk))), e.r[0] + e.r[1] * (fr + bk), m.dark, "ear%d" % s))
        w = h.whiskers
        for k in range(w.n):
            P.mark(hp((w.at[0] + k * w.step[0], s * (w.at[1] + k * w.step[1]), w.at[2] + k * w.step[2])), M.RAMPS[m.pale][4])


def _head_suid(P, B, c) -> None:
    """The boarlets' head: skull and jowls, a long snout ending in its disc, tusks curving up from the lower jaw, eyes a
    dark bead under the brow (the hollowed's cold white in a halo), pointed ears pricked forward, flicking, laid back
    in anger."""
    h, m = B.parts.head, B.mats
    a, f, fr, bk, at, bm = c.action, c.f, c.fr, c.bk, c.at, c.bm
    hollow = B.opts.get("hollowed", False)
    hpitch = c.hpitch + h.pitch[1] * fr
    hm = bm @ rot("b", h.pitch[0] + hpitch)
    sniff = B.style(a).sniff[0] * wave(a, f, B.style(a).sniff[1]) if a == "idle" else 0.0
    (ha, hf), (hz, hzf) = h.at
    hc = at((ha + sniff + hf * fr, 0.0, hz + hzf * fr))
    hp = lambda q: hc + hm @ v3(q)
    skull = h.skull
    P.add(E(hc, skull, m.head, "head", hm),
          E(hp((0.4, 0.0, -1.5)), (3.2, 3.9, 2.4), m.head, "head", hm),
          L(hp((2.0, 0.0, -0.6)), hp((6.0, 0.0, -1.4)), 2.3, 1.7, m.head, "head"))
    P.add(E(hp((6.6, 0.0, -1.5)), (0.8, 1.8, 1.6), m.snout, "snout", hm))
    angry = B.style(a).get("angry", False)
    tk = h.get("tusk", 1.0)
    for s in (1, -1):
        P.mark(hp((7.45, s * 0.6, -1.3)), M.RAMPS[m.snout][0])
        if tk == 1.0:
            P.add(L(hp((4.6, s * 1.7, -2.3)), hp((5.8 - 0.4 * fr, s * (2.3 + 0.9 * fr), -0.8 + 0.2 * fr)), 0.45, 0.28, m.tusk, "tusk%d" % s))
        else:
            # M1, the thornback's: a long tusk curving up and back from the lower jaw (two segments).
            t0 = hp((4.6, s * 1.7, -2.3))
            t1 = hp((5.4 + 0.5 * tk - 0.4 * fr, s * (2.4 + 0.9 * fr), -1.4 + 0.6 * tk))
            t2 = hp((5.0 + 0.4 * tk - 0.5 * fr, s * (2.6 + 1.0 * fr), -0.2 + 1.3 * tk))
            P.add(L(t0, t1, 0.55, 0.42, m.tusk, "tusk%d" % s), L(t1, t2, 0.42, 0.2, m.tusk, "tusk%d" % s))
        closed = shut(h.eyes, a, f)
        eye, eye2 = on(hc, skull, hm, s * 50.0, 16.0), on(hc, skull, hm, s * 46.0, 26.0)
        if h.eyes.get("colour") and not closed:
            # M1: a small fierce coloured eye under a heavy brow (the thornback's red), its dark rim.
            P.eye(eye, colour(h.eyes.colour))
            P.mark(eye2, colour(h.eyes.get("rim", "INKY")))
            P.mark(on(hc, skull, hm, s * 52.0, 34.0), M.RAMPS[m.head][0])
        elif hollow and not closed:
            P.eye(eye, M.HOLLOW_EYE)
            P.eye(eye2, M.HOLLOW_EYE)
            P.mark(on(hc, skull, hm, s * 50.0, 38.0), M.EYE_HALO)
        elif closed:
            P.mark(eye, M.RAMPS[m.head][0])
        else:
            P.eye(eye, M.INKY)
            P.eye(eye2, M.INKY)
            P.mark(on(hc, skull, hm, s * 40.0, 28.0), M.GLINT)
        flick = 18.0 if a == "idle" and f in (3, 4) and s > 0 else 0.0
        if angry:
            flick = -20.0
        em = hm @ rot("a", s * -(32.0 + 20.0 * fr)) @ rot("b", 4.0 + flick)
        ear_c = hp((-1.0 - 0.3 * bk, s * (2.7 + 0.6 * fr), 3.5 + 1.0 * bk))
        ear_r = (1.3 * (1.0 + 0.15 * fr), 1.0, 2.8 * (1.0 + 0.15 * fr + 0.1 * bk))
        P.add(E(ear_c, ear_r, m.head, "ear%d" % s, em))
        P.mark(on(ear_c, ear_r, em, 0.0, 20.0), colour(m.ear))


def _head_canine(P, B, c) -> None:
    """M1, the dogs and cats (the ember fox, the mud hound): a skull on a neck from the chest, a tapering muzzle to a
    nose pad, the pale of the muzzle and cheeks (`mask`: below its height, ahead of its reach, in the head's frame), a
    jaw that drops on its fangs (its tongue out while it pants or bites), tall ears (spread head-on, laid back in anger,
    flicking, the inner ear pale, a dark tip; `torn` shortens one), eyes with a glint (shut when struck or beaten), and
    a collar round the neck with a ring hanging from it (`collar`: how far up the neck)."""
    h, m = B.parts.head, B.mats
    a, f, fr, bk, at, bm = c.action, c.f, c.fr, c.bk, c.at, c.bm
    st = B.style(a)
    yaw = B.pick("yaw", a, f) * (1.0 - 0.6 * fr)
    hm = bm @ rot("c", yaw) @ rot("b", h.pitch[0] + c.hpitch + h.pitch[1] * fr)
    (ha, hf), hz = h.at
    hc = at((ha + hf * fr, 0.0, lin(hz, fr, bk)))
    hp = lambda q: hc + hm @ v3(q)
    mz, mr = h.mask

    def face(q, n):
        loc = (q - hc) @ hm
        pale = (loc[:, 2] < mz) & (loc[:, 0] > mr)
        return np.where(pale, m.pale, m.coat).astype(object), np.zeros(len(q), dtype=np.int16)

    n0, r0, r1 = h.neck
    neck_root = at(n0)
    P.add(L(neck_root, hc + hm @ v3(-0.9, 0.0, -0.5), r0, r1, m.coat, "neck", c.paint))
    if h.get("collar"):
        cn = neck_root + (hc - neck_root) * h.collar
        ax = (hc - neck_root) / max(1e-6, float(np.linalg.norm(hc - neck_root)))
        side = np.cross(ax, v3(0.0, 0.0, 1.0))
        side = side / max(1e-6, float(np.linalg.norm(side)))
        up = np.cross(side, ax)
        rad = r0 + (r1 - r0) * h.collar + 0.1
        for k in range(10):
            t = math.radians(k * 36.0)
            P.add(S(cn + (side * math.cos(t) + up * math.sin(t)) * rad, 0.55, m.collar, "collar", line=False))
        P.add(S(cn - up * (rad + 0.7) + ax * 0.3, 0.6, m.ring, "collar"))
    P.add(E(hc, h.skull, m.coat, "head", hm, face))
    q0, q1, mr0, mr1 = h.muzzle
    P.add(L(hp(q0), hp(q1), mr0, mr1, m.coat, "head", face))
    P.add(S(hp(h.nose[0]), h.nose[1], m.nose, "nose"))
    gape = B.pick("gape", a, f)
    j = h.jaw
    if gape > 0.05:
        jm = hm @ rot("b", -gape * j.turn)
        hinge = hp(j.at)
        P.add(L(hinge, hinge + jm @ v3(j.to), j.r[0], j.r[1], m.pale, "jaw"))
        if gape > 0.3 or st.get("tongue"):
            P.add(E(hinge + jm @ v3(j.tongue[0]), j.tongue[1], m.tongue, "tongue", jm, line=False))
        ta, tb, tc = j.teeth
        for s in (1, -1):
            P.mark(hp((ta, s * tb, tc)), M.FANG)
    e = h.ears
    angry = st.get("angry", False)
    flick = B.pick("ears", a, f)
    for s in (1, -1):
        torn = e.torn == s
        lay = e.back if angry else 0.0
        base = hp((e.base[0], s * e.base[1] * (1.0 + e.spread[0] * fr), e.base[2]))
        tip = hp((e.tip[0] - lay - 0.6 * bk - 1.2 * fr, s * (e.tip[1] * (1.0 + e.spread[1] * fr) + 0.5 * lay + (0.4 * flick if s > 0 else 0.0)),
                  e.tip[2] + 0.6 * fr - 0.55 * lay - (0.5 * flick if s > 0 else 0.0)))
        if torn:
            tip = base + (tip - base) * 0.7
        P.add(L(base, tip, e.r[0], e.r[1], m.coat, "ear%d" % s, caps=False))
        # The inner ear, pale, on its face toward the camera's side; the dark tip.
        P.mark(base + (tip - base) * 0.38 + hm @ v3(0.45, 0.0, 0.0), M.RAMPS[m.ear_in][2])
        P.mark(base + (tip - base) * 0.6 + hm @ v3(0.3, 0.0, 0.0), M.RAMPS[m.ear_in][1])
        if e.tip_dark and not torn:
            P.mark(tip, M.RAMPS[m.sock][1])
        if torn:
            P.mark(tip, M.RAMPS[m.coat][0])
        ey = h.eyes
        closed = shut(ey, a, f)
        eye = hp((ey.at[0], s * ey.at[1], ey.at[2]))
        if closed:
            P.mark(eye, M.RAMPS[m.coat][0])
        else:
            P.eye(eye, colour(ey.colour))
            P.mark(hp((ey.at[0] - 0.35, s * (ey.at[1] + 0.05), ey.at[2] + 0.25)), M.INKY if angry else M.RAMPS[m.coat][0])
    if a == "windup" and f in st.get("barks", ()):
        # The bark: short lines thrown off its open jaws.
        tip = hp(h.nose[0])
        for k in range(3):
            d = hm @ v3(1.0, (k - 1) * 0.9, 0.6 + (k - 1) * 0.4)
            for t in (1.2, 1.9):
                P.fx.append((tip + d * t, M.DUST if t < 1.5 else M.DUST_DIM))


# ------------------------------------------------------------------------------------------------ legs
def _legs_paw(P, B, c) -> None:
    """Short forelegs and haunches with long feet; the scurry lands the forepaws together, then the hind; in a rearing
    tell the forepaws lift off the ground."""
    g, m = B.parts.legs, B.mats
    a, f, fr, bk, at, bm, lunge = c.action, c.f, c.fr, c.bk, c.at, c.bm, c.lunge
    rr = B.style(a).get("reared", False)
    reared = rr is True or (isinstance(rr, (list, tuple)) and f in rr)
    fb, hb = lin(g.fore[1], fr, bk), lin(g.hind[1], fr, bk)
    ha = g.hind[0][0] + g.hind[0][1] * fr
    for k, (a0, b0, front) in enumerate(((g.fore[0], fb, True), (g.fore[0], -fb, True), (ha, hb, False), (ha, -hb, False))):
        lift, stride = gait(a, f, 0.0 if front else g.hind_off, g.lift[0] + g.lift[1] * (fr + bk), g.stride)
        if front and reared:
            top = at((a0, b0, g.rear[0][0]))
            paw = top + bm @ v3(g.rear[1])
        else:
            top = at((a0, b0 * (1.0 - g.narrow * (fr + bk)), g.top[0] if front else g.top[1]))
            paw = v3(lunge + a0 + stride + (g.reach[0][0] + g.reach[0][1] * fr if front else g.reach[1]), b0, 0.6 + lift)
        P.add(L(top, paw, g.r[0][0] if front else g.r[0][1], g.r[1], m.coat, "leg%d" % k),
              E(paw + v3(g.foot[0][0] if front else g.foot[0][1], 0.0, -0.1),
                (g.foot[1][0][0] if front else g.foot[1][0][1], g.foot[1][1], g.foot[1][2]), m.pink, "leg%d" % k))


def _legs_lope(P, B, c) -> None:
    """Short legs with dark paws; the lope reaches with the fore pair and gathers the hind pair under; when it sits up
    the forepaws tuck against the chest, and curled in the fall they draw in."""
    g, m = B.parts.legs, B.mats
    a, f, fr, bk, at, bm = c.action, c.f, c.fr, c.bk, c.at, c.bm
    fb, hb = lin(g.fore[1], fr, bk), lin(g.hind[1], fr, bk)
    for k, (a0, b0, front) in enumerate(((g.fore[0], fb, True), (g.fore[0], -fb, True), (g.hind[0], hb, False), (g.hind[0], -hb, False))):
        ph = f / 8.0 * math.tau + (0.0 if front else math.pi)
        stride = g.stride * math.cos(ph) if a == "walk" else 0.0
        up = (g.lift[0] + g.lift[1] * (fr + bk)) * max(0.0, math.sin(ph)) if a == "walk" else 0.0
        top = at((a0, b0 * (1.0 - g.narrow * (fr + bk)), -1.6)) if front else v3(c.hips[0] - 1.0 + 1.6 * fr, b0 * (1.0 - g.narrow * bk), c.z - 1.8)
        if front and c.pitch > 20.0:
            foot = top + bm @ v3(1.6, -b0 * 0.2, -1.4)
        elif front and c.curl > 0.2:
            foot = top + bm @ v3(1.8, 0.0, -2.0)
        else:
            foot = v3(top[0] + stride + (0.8 + 0.8 * fr if front else 0.0), b0, 0.7 + up)
        P.add(L(top, foot, g.r[0], g.r[1], m.coat, "leg%d" % k),
              E(foot + v3(g.foot[0], 0.0, -0.1), g.foot[1], m.dark, "leg%d" % k))


def _legs_hoof(P, B, c) -> None:
    """Forelegs under the shoulder, hind legs under the rump bent back at the hock, dark hooves; the tell paws the ground
    with the near forehoof and braces the hind; the charge reaches; the flinch lifts; the fall buckles the forelegs."""
    m = B.mats
    a, f, fr, bk, at, lunge = c.action, c.f, c.fr, c.bk, c.at, c.lunge
    st = B.style(a)
    fb, hb = 2.5 + 1.3 * fr + 0.5 * bk, 2.7 + 0.5 * fr + 1.2 * bk        # the stance: apart where it is seen head-on
    legs = (("fl", 3.8, fb, 0.0), ("fr", 3.8, -fb, 0.5), ("hl", -5.0 + 1.3 * fr, hb, 0.5), ("hr", -5.0 + 1.3 * fr, -hb, 0.0))
    for name, a0, b0, off in legs:
        front = name[0] == "f"
        lift, stride = gait(a, f, off, 2.0 + 0.9 * (fr + bk), 2.2)
        top = at((a0 + 1.4 if front else a0 + 0.8, b0 * (0.92 - 0.12 * (fr + bk)), -2.4 if front else -1.8))
        foot = v3(lunge + a0 + stride + (0.8 * fr if front else 0.0), b0, 0.9 + lift)
        if "paw" in st and name == "fr":
            foot = foot + v3(*st.paw[f])
        if "brace" in st and not front:
            foot = foot + v3(st.brace * f / 3.0, 0.0, 0.0)
        if "reach" in st:
            foot = foot + v3(*dict(enumerate(st.reach)).get(f, ((0, 0, 0), (0, 0, 0)))[0 if front else 1])
        if "flinch" in st and f == 0:
            foot = foot + v3(*st.flinch[0 if front else 1])
        if "fold_front" in st:
            fold = st.fold_front[f] if front else st.fold_hind[f]
            foot = foot + v3(-2.6 * fold if front else 1.2 * fold, 0.0, 1.6 * fold)
        l1, l2 = (3.0, 2.9) if front else (3.1, 3.0)
        knee, end = ik2(top, foot, l1, l2, v3(1.0 if front else -1.0, 0.0, 0.0))
        P.add(L(top, knee, 1.7 if front else 2.0 + 0.5 * bk, 1.2, m.hide, "leg_" + name),
              L(knee, end, 1.15, 0.95, m.hide, "leg_" + name))
        P.add(E(end + v3(0.3, 0.0, -0.25), (1.15, 1.0, 0.8), m.hoof, "leg_" + name))


def _legs_digit(P, B, c) -> None:
    """M1, the canines: legs of two bones on the toes (the foreleg's elbow and wrist, the hind leg's hock bent back),
    socks on the lower bones, small paws; a trot in diagonal pairs; the pounce reaches with the forepaws and drives off
    the hind; the bark braces the hind legs; curled in the fall they draw in under it."""
    g, m = B.parts.legs, B.mats
    a, f, fr, bk, at, bm, lunge = c.action, c.f, c.fr, c.bk, c.at, c.bm, c.lunge
    st = B.style(a)
    fb, hb = lin(g.fore[1], fr, bk), lin(g.hind[1], fr, bk)
    sock = m.get("sock") or _skin(B)
    for name, a0, b0, off in (("fl", g.fore[0], fb, 0.0), ("fr", g.fore[0], -fb, 0.5), ("hl", g.hind[0], hb, 0.5), ("hr", g.hind[0], -hb, 0.0)):
        front = name[0] == "f"
        lift, stride = gait(a, f, off, g.lift[0] + g.lift[1] * (fr + bk), g.stride)
        top = at((a0 + (0.4 if front else 0.6), b0 * (0.85 - 0.1 * (fr + bk)), g.top[0] if front else g.top[1]))
        foot = v3(lunge + a0 + stride + (0.6 * fr if front else 0.0), b0, 0.55 + lift)
        if "reach" in st:
            foot = foot + v3(*dict(enumerate(st.reach)).get(f, ((0, 0, 0), (0, 0, 0)))[0 if front else 1])
        if "brace" in st and not front:
            foot = foot + v3(-st.brace * min(f + 1, 3) / 3.0, 0.0, 0.0)
        if c.curl > 0.05:
            tuck = top + bm @ v3(1.8 if front else 2.4, 0.0, -1.2)
            foot = foot + (tuck - foot) * c.curl
        l1, l2 = g.bones[0] if front else g.bones[1]
        knee, end = ik2(top, foot, l1, l2, v3(1.0 if front else -1.0, 0.0, 0.0))
        r = g.r[0] if front else g.r[1]
        mid = (r[0] + r[1]) * 0.5
        P.add(L(top, knee, r[0], mid, _skin(B), "leg_" + name, c.paint),
              L(knee, end, mid * 0.85, r[1], sock, "leg_" + name))
        P.add(E(end + v3(0.35, 0.0, -0.15), g.paw, sock, "leg_" + name))


# ------------------------------------------------------------------------------------------------ tails
def _brush_r(t, u: float) -> float:
    """The bushy tail's radius along it (0 at the root, 1 at the tip): swelling to its widest past the middle, tapering
    to its tip."""
    r0, r1, r2 = t.r
    if u < 0.55:
        return r0 + (r1 - r0) * math.sin(u / 0.55 * math.pi * 0.5)
    return r1 + (r2 - r1) * ((u - 0.55) / 0.45) ** 1.5


def _tail_brush(P, B, c) -> None:
    """M1, the canines: a bushy tail from the top of the rump, swelling and tapering, its tip in its own colour, carried
    a little up (raised in the tell), swaying as it trots; head-on swept out to one side so it shows beside the body,
    tail-on held aside; curled round toward the head in the fall. The ember fox's tip burns (`flame`): a flicker of
    flame over it every frame, flaring in its tell."""
    t, m = B.parts.tail, B.mats
    a, f, fr, bk, at = c.action, c.f, c.fr, c.bk, c.at
    st = B.style(a)
    sway = 1.4 * wave(a, f) if a in ("idle", "walk") else 0.4
    up = B.pick("tail", a, f)
    ra, rc = t.root
    root = at((ra + 1.0 * fr, 0.0, rc))
    curl = c.curl
    pts = [root]
    n = t.n
    step = t.length / n
    for k in range(1, n + 1):
        u = k / float(n)
        ang = math.radians(t.rest + 30.0 * up - 30.0 * fr + t.droop * u * (1.0 - 0.6 * min(1.0, up)))
        side = (sway * 0.25 + 2.8 * fr + 0.9 * bk) * (0.4 + u)
        d = v3(-math.cos(ang), side, math.sin(ang))
        d = d / float(np.linalg.norm(d))
        q = pts[-1] + d * step
        if curl > 0.0:      # round toward the belly, as the otter's (on its side, along the ground to its nose)
            q = q + v3(curl * 4.0 * u * u, 0.0, -curl * 5.0 * u * u)
        q[2] = max(q[2], 0.9 - curl * 9.0)
        pts.append(q)
    for k in range(n):
        u0, u1 = k / float(n), (k + 1) / float(n)
        mat = m.tip if u0 >= 1.0 - t.tip - 1e-6 else _skin(B)
        P.add(L(pts[k], pts[k + 1], _brush_r(t, u0), _brush_r(t, u1), mat, "tail", caps=k == 0))
    if t.get("flame"):
        flare = 1.0 + (0.4 + 0.25 * f if a == "windup" and f in st.get("flare", ()) else 0.0)
        tip = pts[-1]
        for k in range(10):
            ph = (k * 1.7 + f * 2.3) % 6.28
            hgt = (0.9 + 0.5 * math.sin(ph) + 0.4 * (k % 2)) * flare
            q = tip + v3(-0.3 + 0.6 * math.cos(ph), 0.7 * math.sin(ph * 1.3), 0.4 + hgt * (0.5 + 0.16 * k))
            P.glow.append((q, M.FLAME_CORE if k < 3 else (M.FLAME if k < 7 else M.FLAME_DEEP)))
        for k in range(4):
            P.glow.append((tip + v3(0.2 * k - 0.3, 0.3 * (k - 1.5), 2.0 * flare + k * 0.7 + (f % 2) * 0.5), M.FLAME_GLOW))


def _tail_reed(P, B, c) -> None:
    """A long tail in alternating segments curving back along the ground, the tip lifting and swaying, lashed high in a
    rearing tell. Facing the camera it lies on the ground swept out to one side behind it with a wave in it, so it
    shows beside the body as a tail (straight back it hides behind the body, and raised it stands up like a stalk)."""
    t, m = B.parts.tail, B.mats
    a, f, fr, at = c.action, c.f, c.fr, c.at
    sway = 2.0 * wave(a, f) if a in ("idle", "walk") else 0.6
    up = B.pick("tail", a, f)
    (ra, rf), rc = t.root
    root = at((ra + rf * fr, 0.0, rc))
    pts = []
    n = t.n
    for k in range(n):
        u = k / (n - 1.0)
        side = v3(root[0] - 10.0 * u + up * 2.4 * u * u, (2.2 + sway) * math.sin(u * 2.6), root[2] - 2.4 * u + (3.0 + up * 3.4) * u * u)
        curl = v3(root[0] - 6.0 * u, -(7.4 + 0.5 * sway) * math.sin(0.5 * math.pi * u) + 1.0 * math.sin(u * 7.0 + sway),
                  root[2] + (0.7 - root[2]) * min(1.0, u * 3.0) + up * 3.4 * u * u)
        pts.append(side + (curl - side) * fr)
    mats = m.tail
    for k in range(n - 1):
        r0 = t.r[0] - t.r[1] * k / (n - 1.0)
        P.add(L(pts[k], pts[k + 1], r0, r0 - t.r[2], mats[k % 2], "tail", caps=k == 0))


def _tail_thick(P, B, c) -> None:
    """The thick tail, tapering, wagging; laid along the ground as a prop when it sits up; walking away it swings wider
    and curves off to one side, so it shows as a tail and not the body running on; curled round toward the belly in the
    fall."""
    t, m = B.parts.tail, B.mats
    a, f, fr, bk = c.action, c.f, c.fr, c.bk
    wag = (t.wag[0] + t.wag[1] * bk) * wave(a, f) if a in ("idle", "walk") else 0.0
    root = c.hips + v3(-3.0 + 1.6 * fr, 0.0, -0.6)
    prev = root
    curl, rear = c.curl, c.pitch
    n = t.n
    for k in range(1, n + 1):
        u = k / float(n)
        q = v3(root[0] - t.length * u + curl * 5.0 * u * u, wag * math.sin(u * 2.4) + bk * 2.4 * u * u,
               root[2] - 3.4 * u + (0.8 * u if rear > 20 else 0.0) - curl * 6.0 * u * u)
        q[2] = max(q[2], 0.9 - curl * 9.0)
        P.add(L(prev, q, t.r[0] - t.r[1] * (k - 1) / float(n), t.r[0] - t.r[1] * k / float(n), m.coat, "tail", caps=k == 1))
        prev = q


def _tail_tassel(P, B, c) -> None:
    """From the top of the rump it droops, a flick of a curl at its end and a dark tassel, swinging."""
    m = B.mats
    a, f, fr, bk, at, bm = c.action, c.f, c.fr, c.bk, c.at, c.bm
    wag = {"idle": (0.0, 0.8, 0.3, -0.5, 0.0, 0.4), "walk": tuple(0.8 * wave("walk", i) for i in range(8))}.get(a, (0.3,) * 8)
    w = wag[min(f, len(wag) - 1)]
    ta = 1.4 * fr
    tail = [at((-7.6 + ta, 0.0, 2.2)), at((-9.0 + ta, w * 0.3, 1.6)), at((-9.8 + ta, w * 0.7, 0.3)),
            at((-9.8 + ta, w * 1.0, -1.1 - 0.9 * bk)), at((-9.2 + ta, w * 1.1, -1.7 - 1.4 * bk))]
    P.add(chain(tail[:2], 0.62 + 0.1 * bk, 0.55 + 0.1 * bk, m.hide, "tail"),
          chain(tail[1:], 0.55 + 0.1 * bk, 0.42 + 0.1 * bk, m.bristle, "tail"))
    P.add(E(tail[-1] + bm @ v3(0.1, 0.0, -0.3), (0.7 + 0.15 * bk, 0.6 + 0.15 * bk, 0.9 + 0.2 * bk), m.bristle, "tail", bm))


# ------------------------------------------------------------------------------------------------ options
def _strands(P, B, c) -> None:
    """The hollowed's grey strands: three thin wisps rising from the spine and curling back, stirring as it breathes.
    Head-on or tail-on they fan out from the spine, so they show as three wisps and not one grey horn."""
    a, f, fr, bk, at = c.action, c.f, c.fr, c.bk, c.at
    st = {"idle": 0.5 * wave(a, f), "walk": 0.7 * wave(a, f, 0.3)}.get(a, 0.9)
    ho = fr + bk
    for k, (a0, b0) in enumerate(((-4.0, 0.5), (-1.2, -0.4), (1.6, 0.3))):
        fan = (1.9, -1.9, 0.0)[k]
        bb = b0 + (fan - b0) * ho
        base = at((a0, bb, 4.3 - 0.5 * ho * abs(fan)))
        rise = 1.0 if a not in ("attack",) else 0.6
        out = 0.9 * ho * fan
        pts = [base, base + v3(-0.4, st * 0.4 * (1 if k % 2 else -1) + out * 0.3, 2.4 * rise),
               base + v3(-1.6, -st * 0.5 * (1 if k % 2 else -1) + out * 0.7, 4.6 * rise),
               base + v3(-1.3 - k * 0.3, st * 0.6 + out, 6.4 * rise - k * 0.5), base + v3(-0.2, st * 0.7 + out * 1.2, 7.2 * rise - k * 0.7)]
        P.add(chain(pts, 0.5, 0.25, "strand", "strand%d" % k, line=False))


def _dust(P, B, c) -> None:
    """Dust: the pawing hoof's scrape in the tell, the charge's skid."""
    a, f, lunge = c.action, c.f, c.lunge
    st = B.style(a)
    if a == "windup" and f in st.get("dust", ()):
        for k in range(4):
            P.fx.append((v3(lunge + 3.8 - 2.6 - k * 1.1, -2.8 - k * 0.5, 0.4 + (k % 2) * 0.8 + f * 0.3), M.DUST if k % 2 else M.DUST_DIM))
    if a == "attack" and f in st.get("dust", ()):
        for k in range(6):
            ang = math.radians(k * 60.0 + f * 20.0)
            r = 2.0 + f * 1.1
            P.fx.append((v3(lunge + 3.0 + math.cos(ang) * r * 0.5, math.sin(ang) * r, 0.4 + (k % 3) * 0.5), M.DUST if k % 2 else M.DUST_DIM))


def _finish(P, B, c) -> None:
    """The fall (rolled onto its side; the hollowed coming apart into grey motes) and the squash."""
    a, f = c.action, c.f
    roll = B.pick("roll", a, f)
    if roll:
        topple(P, roll, B.parts.Z, B.parts.side)
    if a == "death" and B.opts.get("hollowed"):
        P.dissolve = B.pick("dissolve", a, f)
        P.dissolve_col = M.MOTE
    if c.sa != 1.0 or c.sc != 1.0:
        P.squash(c.sa, 1.0 / math.sqrt(c.sa * c.sc), c.sc, (c.lunge, 0.0, 0.0))
