"""How a weapon is held, shared by every weapon generator (kinds/blade.py, kinds/pole.py, and any family's own).

A pose says where a blade points (`blade`: a direction in the figure's frame, `flat` its flat) and where a pole points
(`pole`: a direction, `two_hand` to run it through both hands, and `butt`, the grip's distance from the butt), or lays
the weapon on the ground (`laid`). A weapon is cast from the grip along that line, piece by piece, and each piece lies
in the band (behind or in front of the body) its own depth puts it in (`band_of`), so a blade can pass behind the head
and in front of the legs in one frame. Pieces along the ground's depth are stretched (`stretch`).
"""
from __future__ import annotations

import numpy as np

from .geom import depth, unit

# A weapon pointed at the camera (or away) is drawn this much longer on screen than the figure's camera would show it:
# the world's own view keeps the ground's depth at full length, so a thrust to the south must still read as a reach.
DEPTH_STRETCH = 1.6


def stretch(sk, grip, p):
    """A point of the weapon moved away from the grip along the world's south by DEPTH_STRETCH."""
    v = np.asarray(p, float) - grip
    return grip + np.array([v[0], v[1] * DEPTH_STRETCH, v[2]])


def band_of(sk, p) -> str:
    return "front" if depth(p) >= depth(sk.chest) - 0.9 else "back"


def flat_frame(axis, flat):
    w = unit(axis)
    x = unit(flat - w * float(flat @ w))
    if float(np.linalg.norm(x)) < 1e-6:
        x = unit(np.cross(w, np.array([0.0, 0.0, 1.0])))
    return x


def blade_line(sk):
    """The blade's grip point, direction and flat in the world (in the right hand, or laid on the ground)."""
    wp = sk.weapon or {}
    laid = wp.get("laid")
    if laid:
        return sk.pt(laid["at"]), unit(sk.w(laid["dir"])), unit(sk.w((0.0, 0.0, 1.0)))
    return sk.hand_r, unit(sk.w(wp.get("blade", (0.35, 0.3, -1.0)))), unit(sk.w(wp.get("flat", (0.0, 1.0, 0.0))))


def pole_line(sk):
    """The pole's direction and its butt point in the world."""
    wp = sk.weapon or {}
    laid = wp.get("laid")
    if laid:
        d = unit(sk.w(laid["dir"]))
        return d, sk.pt(laid["at"]) - d * 20.0
    pole = wp.get("pole", {"dir": (0.12, 0.1, 1.0), "butt": 12.6})
    hand = sk.hand_r
    if pole.get("two_hand"):
        d = unit(sk.hand_r - sk.hand_l)
        butt = sk.hand_l - d * float(pole.get("behind", 6.0))
    else:
        d = unit(sk.w(pole["dir"]))
        butt = hand - d * float(pole.get("butt", 12.6))
    return d, butt
