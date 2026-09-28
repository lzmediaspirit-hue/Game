"""Vectors, the camera and the joints' maths for the top-down figure.

World axes: x east (screen right), y south (toward the camera on the ground), z up. The camera is orthographic and
looks down from the south at ELEV degrees (lower than the world's own oblique view, as sprites in a 3/4 view are drawn,
so the face shows), so a sphere stays round on screen; SCALE art px per unit makes the standing figure about 38 art px
from the soles to the crown.

The figure's own frame (a pose's coordinates) is (f, r, u): forward, the character's right hand side, up. A facing
turns it into the world: forward F on the ground, right R = (-F.y, F.x), up z.
"""
from __future__ import annotations

import math

import numpy as np

ELEV = math.radians(22.0)
SCALE = 0.92                                                        # art px per figure unit
SCR_R = np.array([1.0, 0.0, 0.0])                                 # screen right in the world
SCR_D = np.array([0.0, math.sin(ELEV), -math.cos(ELEV)])           # screen down in the world
TOWARD = np.array([0.0, math.cos(ELEV), math.sin(ELEV)])           # from the figure toward the camera
# One light for the world: high in the upper left (docs/art-contracts.md, art bible §3), a little in front so a face
# turned to the camera is lit.
LIGHT = np.array([-0.60, 0.34, 0.72])
LIGHT = LIGHT / np.linalg.norm(LIGHT)

# The drawn facings (redesign plan §1.4): forward angle on the ground, measured from east toward south. The side and
# back-diagonal facings are turned a little toward the camera, as sprites in a 3/4 view are, so the face and chest read.
FACINGS = {"s": 90.0, "se": 48.0, "e": 14.0, "ne": -36.0, "n": -90.0}
DIRS = ["s", "se", "e", "ne", "n"]
# In the side facing the head turns a little more toward the camera (to its right), so the face reads in three
# quarters as the side-view sprite's does.
FACE_TURN = {"e": 22.0}
MIRROR = {"sw": "se", "w": "e", "nw": "ne"}


def vec(*a) -> np.ndarray:
    return np.array(a, dtype=float)


def unit(a) -> np.ndarray:
    a = np.asarray(a, dtype=float)
    n = float(np.linalg.norm(a))
    return a / n if n > 1e-9 else a


def lerp(a, b, t):
    return a + (b - a) * t


def rot(axis, deg: float) -> np.ndarray:
    """A 3x3 rotation about `axis` by `deg` (right-handed)."""
    x, y, z = unit(axis)
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    C = 1 - c
    return np.array([[c + x * x * C, x * y * C - z * s, x * z * C + y * s],
                     [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
                     [z * x * C - y * s, z * y * C + x * s, c + z * z * C]])


def project(p) -> tuple:
    """A world point on screen: (x right, y down), in art px from the feet."""
    p = np.asarray(p, dtype=float)
    return float(p @ SCR_R) * SCALE, float(p @ SCR_D) * SCALE


def depth(p) -> float:
    """How near the camera a world point is (larger is nearer)."""
    return float(np.asarray(p, dtype=float) @ TOWARD)


class Frame:
    """A facing: the figure's (f, r, u) axes in the world."""

    def __init__(self, facing: str):
        a = math.radians(FACINGS[facing])
        self.facing = facing
        self.F = vec(math.cos(a), math.sin(a), 0.0)
        self.R = vec(-self.F[1], self.F[0], 0.0)
        self.U = vec(0.0, 0.0, 1.0)
        self.M = np.stack([self.F, self.R, self.U], axis=1)   # local (f, r, u) -> world

    def w(self, p) -> np.ndarray:
        """A local point or direction in the world."""
        return self.M @ np.asarray(p, dtype=float)

    def yaw_to_camera(self, fwd_world) -> float:
        """Degrees between a forward direction (on the ground) and the camera's: 0 faces the camera, 180 turns away,
        positive turns toward screen right."""
        f = np.asarray(fwd_world, dtype=float)
        return math.degrees(math.atan2(-f[0], f[1]))


def ik2(a, t, l1: float, l2: float, hint) -> tuple:
    """Two-bone IK: the middle joint for a limb from `a` reaching for `t`, bending toward `hint`. Returns (joint, end);
    a target out of reach leaves the limb straight toward it."""
    a = np.asarray(a, dtype=float)
    t = np.asarray(t, dtype=float)
    d = t - a
    dist = float(np.linalg.norm(d))
    reach = l1 + l2 - 1e-3
    if dist > reach:
        d = d / dist
        return a + d * l1, a + d * reach
    dist = max(dist, abs(l1 - l2) + 1e-3)
    dn = d / max(1e-9, float(np.linalg.norm(d)))
    h = np.asarray(hint, dtype=float)
    n = h - dn * float(h @ dn)
    if float(np.linalg.norm(n)) < 1e-6:
        n = np.cross(dn, vec(0, 0, 1))
        if float(np.linalg.norm(n)) < 1e-6:
            n = vec(1, 0, 0)
    n = unit(n)
    cos_a = (l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist)
    ang = math.acos(max(-1.0, min(1.0, cos_a)))
    joint = a + (dn * math.cos(ang) + n * math.sin(ang)) * l1
    return joint, a + dn * dist
