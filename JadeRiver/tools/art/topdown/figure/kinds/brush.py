"""Brush: a calligraphy brush held in the right hand along the pose's `blade` line (or laid on the ground), from a
set's spec (sets/weapon_brush.py), after the side view's brush (tools/art/bake_weapons.py `brush_frame`): a jointed
bamboo shaft with a lacquered end cap, a lacquered collar and a tuft of hair, pale grey at the root and soaked black
to its point; pieces along the ground's depth are stretched as a blade's are (figure/weapons.py).

A cut (`smear_from` in the pose) leaves an ink stroke where the tuft's point swept since the frame before, as a
calligrapher's stroke: black and broad at the brush, thinning to a hair behind it, and at its tail run dry, grey and
broken where the dry brush skipped (the flying white). Like the jian's smear it has no outline but its own deepest
tone.

Spec keys:
  butt    the shaft's length behind the grip      shaft   its length in front of the grip     radius  its radius
  joints  where the bamboo's joints are, from the grip
  collar  the collar's length                    tuft    the tuft's length                   belly   its widest radius
  stroke  the ink stroke's width at the brush and at its tail     inset   how far inside the point the stroke runs
  gap     the clear angle between the point and the stroke's head, degrees
  dry     how far from its tail the stroke has run dry (grey, feathered), degrees of arc, at most 45% of the sweep
  breaks  where the dry part skips, [(from, to)] degrees of arc from the tail
"""
from __future__ import annotations

import math

import numpy as np

from ..geom import TOWARD, unit
from ..raster import cone, sphere
from ..weapons import band_of, blade_line, stretch
from .fan import sweep


def solids(sk, spec: dict) -> list:
    S = []
    g, d, _flat = blade_line(sk)

    def at(k):
        return stretch(sk, g, g + d * k)
    r = spec["radius"]
    # The shaft, in pieces between its joints (each piece in its own band), a ring at each joint.
    stops = [-spec["butt"]] + sorted(spec["joints"]) + [spec["shaft"]]
    for k0, k1 in zip(stops[:-1], stops[1:]):
        p0, p1 = at(k0), at(k1)
        S.append(cone(p0, p1, r, r, "bamboo", band=band_of(sk, (p0 + p1) * 0.5), part="shaft"))
    for k in spec["joints"]:
        p0, p1 = at(k - 0.22), at(k + 0.22)
        S.append(cone(p0, p1, r + 0.1, r + 0.1, "joint", band=band_of(sk, (p0 + p1) * 0.5), part="joint"))
    cap = at(-spec["butt"])
    S.append(sphere(cap, r + 0.08, "lacquer", band=band_of(sk, cap), part="cap"))
    # The collar and the tuft: its belly just past the collar, then a long taper to the point.
    c0 = spec["shaft"]
    c1 = c0 + spec["collar"]
    p0, p1 = at(c0), at(c1)
    S.append(cone(p0, p1, r + 0.14, r + 0.2, "lacquer", band=band_of(sk, (p0 + p1) * 0.5), part="collar"))
    belly = c1 + spec["tuft"] * 0.28
    tip = c1 + spec["tuft"]
    m, e = at(belly), at(tip)
    S.append(cone(p1, m, r + 0.16, spec["belly"], "tuft", band=band_of(sk, (p1 + m) * 0.5), part="tuft"))
    S.append(sphere(m, spec["belly"], "tuft", band=band_of(sk, m), part="tuft"))
    L_tip = float(np.linalg.norm(e - m))

    def soaked(loc, P, nn):
        # pale at the root, soaked black from a third of the taper on
        return (np.where(loc[:, 2] > L_tip * 0.3, "tip", "tuft").astype(object), np.zeros(len(loc), dtype=np.int16))
    S.append(cone(m, e, spec["belly"], 0.06, "tuft", band=band_of(sk, (m + e) * 0.5), part="tuft", paint=soaked))
    # A cut's ink stroke along the arc the point swept since the frame before, laid a little further from the camera
    # than the brush (the same place on screen) so the tuft always shows over the stroke's head.
    wp = sk.weapon or {}
    if wp.get("smear_from") is not None:
        d0 = unit(sk.w(wp["smear_from"]))
        ang = float(np.degrees(np.arccos(np.clip(d0 @ d, -1.0, 1.0))))
        rc = tip - spec["inset"]                         # the stroke runs along the tuft's point
        steps = max(8, int(ang / 3.0))
        w_head, w_tail = spec["stroke"]
        back = -TOWARD * 2.0
        for j in range(steps):
            t = (j + 0.5) / steps                        # 0: the tail, where the brush was; 1: the head, at the brush
            dj = sweep(d0, d, sk.up, t)
            if math.degrees(math.acos(max(-1.0, min(1.0, float(dj @ d))))) < spec["gap"]:
                continue
            from_tail = t * ang                          # degrees of arc from the tail's end
            dry = from_tail < min(spec["dry"], ang * 0.45)
            if dry and any(lo <= from_tail < hi for lo, hi in spec["breaks"]):
                continue                                 # the dry brush skips
            w = w_tail + (w_head - w_tail) * t
            p0, p1 = stretch(sk, g, g + dj * (rc - w * 0.5)), stretch(sk, g, g + dj * (rc + w * 0.5))
            # flat across the swing's plane: long along the arc so the pieces join, thin through it
            along = sweep(d0, d, sk.up, min(1.0, t + 0.5 / steps)) - sweep(d0, d, sk.up, max(0.0, t - 0.5 / steps))
            thick = rc * math.radians(ang / steps) * 0.75 + 0.15
            S.append(cone(p0 + back, p1 + back, thick, thick, "ink_dry" if dry else "ink", k=0.35, side=along,
                          band=band_of(sk, (p0 + p1) * 0.5), part="stroke"))
    return S
