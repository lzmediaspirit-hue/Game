"""The figure's skeleton: a pose (in the figure's own frame) turned into joints and part frames in the world.

A pose is a dict; missing keys take POSE's defaults. Positions are (f, r, u): forward, the character's right, up, in
figure units from the feet (the anchor). Angles are degrees:
  lean      the chest pitched forward (+) or back (-);      twist   the chest turned to its right (+) or left (-);
  roll      the chest tilted to its right (+);               hip_yaw the hips turned to the right (+);
  head_*    the head's own yaw / pitch (nod down +) / roll;  toe_*   the foot pitched toe down (+);
  tip       the whole figure pitched about its feet (fall forward +, back -), `tip_at` the pivot's f; `turn` then
            yaws it (to its right +) about the same pivot, `sink` lowers it.
Hands are wrist targets reached by two-bone IK (elbows bend toward `elbow_*`), feet are ankle targets (knees bend toward
`knee_*`). `grip_*` is a hand's shape: relaxed, fist, open, seal. `drag` (f, r, u) is where hair and cloth trail.
"""
from __future__ import annotations

import numpy as np

from .geom import FACE_TURN, Frame, ik2, rot, unit, vec

POSE = {
    "pelvis": (0.0, 0.0, 13.4), "lean": 0.0, "roll": 0.0, "twist": 0.0, "hip_yaw": 0.0,
    "head_yaw": 0.0, "head_pitch": 0.0, "head_roll": 0.0,
    "foot_l": (0.0, -2.2, 1.3), "foot_r": (0.0, 2.2, 1.3), "toe_l": 0.0, "toe_r": 0.0,
    "foot_yaw_l": -6.0, "foot_yaw_r": 6.0,
    "knee_l": (1.0, -0.2, 0.0), "knee_r": (1.0, 0.2, 0.0),
    "hand_l": (0.4, -5.9, 13.6), "hand_r": (0.4, 5.9, 13.6),
    "elbow_l": (-1.0, -0.8, 0.0), "elbow_r": (-1.0, 0.8, 0.0),
    "grip_l": "relaxed", "grip_r": "relaxed",
    "tip": 0.0, "tip_at": 0.0, "sink": 0.0, "turn": 0.0,
    "drag": (0.0, 0.0, 0.0), "eyes": "open",
    "weapon": None,
}

# Bone lengths and body frame offsets (figure units).
THIGH, SHIN = 6.1, 5.8
UPPER_ARM, FOREARM = 4.7, 4.2
HIP_W = 2.1
SHOULDER_W = 4.3


def pose(**over) -> dict:
    p = dict(POSE)
    p.update(over)
    return p


class Skeleton:
    """Joints and frames in the world for one pose and facing. Attributes are world vectors / 3x3 frames (columns:
    forward, right, up)."""

    def __init__(self, p: dict, facing: str):
        self.p = p
        self.fr = Frame(facing)
        self.facing = facing
        lp = self._local(p, FACE_TURN.get(facing, 0.0))
        # the whole-figure pitch (a fall) about the pivot on the ground
        T = self._T(p)
        piv = vec(float(p["tip_at"]), 0.0, 0.0)
        sink = vec(0, 0, -float(p.get("sink", 0.0)))
        W = self.fr.M
        self.local = lp
        for k, v in lp.items():
            if isinstance(v, np.ndarray) and v.shape == (3,) and k.startswith("dir_"):
                setattr(self, k, W @ T @ v)
            elif isinstance(v, np.ndarray) and v.shape == (3,):
                setattr(self, k, W @ (T @ (v - piv) + piv + sink))
            elif isinstance(v, np.ndarray) and v.shape == (3, 3):
                setattr(self, k, W @ T @ v)
            else:
                setattr(self, k, v)
        self.drag = W @ np.asarray(p["drag"], dtype=float)
        self.grip_l = p["grip_l"]
        self.grip_r = p["grip_r"]
        self.eyes = p["eyes"]
        self.weapon = p.get("weapon")
        self.T = T
        self.up = W @ T @ vec(0, 0, 1)
        self.fwd = W @ T @ vec(1, 0, 0)
        self.right = W @ T @ vec(0, 1, 0)

    @staticmethod
    def _T(p: dict) -> np.ndarray:
        return rot(vec(0, 0, 1), float(p.get("turn", 0.0))) @ rot(vec(0, 1, 0), float(p["tip"]))

    def pt(self, local_point) -> np.ndarray:
        """A point in the figure's frame (after the fall) in the world."""
        T = self.T
        piv = vec(float(self.p["tip_at"]), 0.0, 0.0)
        sink = vec(0, 0, -float(self.p.get("sink", 0.0)))
        v = np.asarray(local_point, dtype=float)
        return self.fr.M @ (T @ (v - piv) + piv + sink)

    def w(self, local_dir) -> np.ndarray:
        """A direction in the figure's frame (after the fall) in the world."""
        return self.fr.M @ self.T @ np.asarray(local_dir, dtype=float)

    @staticmethod
    def _local(p: dict, face_turn: float = 0.0) -> dict:
        o = {}
        pel = vec(*p["pelvis"])
        Mp = rot(vec(0, 0, 1), p["hip_yaw"]) @ rot(vec(0, 1, 0), p["lean"] * 0.35)
        Mc = rot(vec(0, 0, 1), p["hip_yaw"] + p["twist"]) @ rot(vec(0, 1, 0), p["lean"]) @ rot(vec(1, 0, 0), -p["roll"])
        Mh = Mc @ rot(vec(0, 0, 1), p["head_yaw"] + face_turn) @ rot(vec(0, 1, 0), p["head_pitch"] - p["lean"] * 0.45) @ rot(vec(1, 0, 0), -p["head_roll"])
        o["Mp"], o["Mc"], o["Mh"] = Mp, Mc, Mh
        o["pelvis"] = pel
        o["waist"] = pel + Mp @ vec(0, 0, 3.0)
        o["chest"] = o["waist"] + Mc @ vec(0, 0, 3.6)
        o["neck"] = o["chest"] + Mc @ vec(0, 0, 3.2)
        o["head"] = o["neck"] + Mc @ vec(0, 0, 1.6) + Mh @ vec(0.3, 0, 5.4)
        for side, sg in (("l", -1.0), ("r", 1.0)):
            sh = o["chest"] + Mc @ vec(-0.2, sg * SHOULDER_W, 1.7)
            hand_t = vec(*p["hand_" + side])
            el, wr = ik2(sh, hand_t, UPPER_ARM, FOREARM, Mc @ vec(*p["elbow_" + side]))
            o["shoulder_" + side] = sh
            o["elbow_" + side] = el
            o["wrist_" + side] = wr
            o["hand_" + side] = wr + unit(wr - el) * 0.9
            hip = pel + Mp @ vec(0, sg * HIP_W, -1.1)
            ft = vec(*p["foot_" + side])
            kn, an = ik2(hip, ft, THIGH, SHIN, Mp @ vec(*p["knee_" + side]))
            o["hip_" + side] = hip
            o["knee_" + side] = kn
            o["ankle_" + side] = an
            yaw = p["hip_yaw"] + p["foot_yaw_" + side]
            fd = rot(vec(0, 0, 1), yaw) @ rot(vec(0, 1, 0), p["toe_" + side]) @ vec(1, 0, 0)
            o["dir_foot_" + side] = fd
            o["foot_" + side] = an + fd * 1.0 + vec(0, 0, -0.35)
        return o

    def weapon_frame(self):
        """The grip and the weapon's axis in the world: (grip point, tip direction, blade-flat direction)."""
        wp = self.weapon or {}
        hand = self.hand_r
        d = self.w(wp.get("dir", (0.3, 0.1, -1.0)))
        flat = self.w(wp.get("flat", (0.0, 1.0, 0.0)))
        return hand, unit(d), unit(flat)
