"""Flute: a jade bamboo dizi in the right hand along the pose's `blade` line (or laid on the ground), from a set's spec
(sets/weapon_flute.py). The side view holds it the same way, drawn along the short blade's grip
(tools/art/bake_weapons.py flute_frame): a tube held near its end, dark bamboo joints, finger holes along its upper
face toward the far end, and a red tassel hanging from the hand's end. On a blow's hit frame and the one after, its
note leaves the far end as ripples of pale jade light (kinds/sound.py): arcs opening along the flute, closing into
rings when it points at the camera or away. Played at the lips (`flute_play`), the pose names the note's way (`note`
in its weapon lines, the figure's frame): the ripples leave the tube's open end that way, toward what it plays at,
clear of the face.

Spec keys:
  length  the tube's length      behind  how much of it lies behind the hand      radius  the tube's radius
  nodes   the joints (distances from the hand's end)      node  a joint's half-width      holes  the finger holes
  tassel  the tassel's length    ripples  per stage, the arcs' (radii, spans) about the far end
  play_ripples  how much smaller the ripples are played at the lips
"""
from __future__ import annotations

import numpy as np

from ..body import HAND_R
from ..geom import TOWARD, unit
from ..raster import cone, ellipsoid, sphere
from ..weapons import band_of, blade_line, stretch
from . import sound

UP = np.array([0.0, 0.0, 1.0])


def solids(sk, spec: dict) -> list:
    S = []
    g, d, _flat = blade_line(sk)
    laid = bool((sk.weapon or {}).get("laid"))
    L, back, rad = spec["length"], spec["behind"], spec["radius"]

    def at(k):
        """A point on the flute's axis, k from the hand's end."""
        return stretch(sk, g, g + d * (k - back))
    p0, p1 = at(0.0), at(L)
    axis = unit(p1 - p0)
    per = float(np.linalg.norm(p1 - p0)) / L        # the depth stretch along this axis
    # the tube's upper face: turned to the sky and the camera, where the finger holes are
    top = TOWARD + UP
    top = top - axis * float(top @ axis)
    top = unit(top) if float(np.linalg.norm(top)) > 1e-3 else unit(np.cross(axis, np.array([1.0, 0.0, 0.0])))
    side = np.cross(top, axis)
    M = np.stack([side, top, axis], axis=1)

    def paint(loc, P, nn):
        k = loc[:, 2] / per
        names = np.full(len(loc), "bamboo", dtype=object)
        for c in spec["nodes"]:
            names[np.abs(k - c) < spec["node"]] = "node"
        hole = np.zeros(len(loc), dtype=bool)
        for c in spec["holes"]:
            hole |= np.abs(k - c) < 0.4
        names[hole & ((nn @ top) > 0.5)] = "hole"
        return names, np.zeros(len(loc), dtype=np.int16)
    # the fist closes round the tube: what of it is inside the hand is left out, so the hand shows over the grip
    hand = None if laid else sk.hand_r
    fist = HAND_R * 0.92

    def clip(loc):
        if hand is None:
            return np.ones(len(loc), dtype=bool)
        return np.linalg.norm(p0 + loc @ M.T - hand, axis=1) > fist
    n = 4
    for i in range(n):
        a, b = at(L * i / n), at(L * (i + 1) / n)
        S.append(cone(a, b, rad, rad, "bamboo", band=band_of(sk, (a + b) * 0.5), part="tube", paint=paint,
                      clip=clip, frame=(p0, M)))
    # the tube's two ends, closed by a joint
    for p in (p0, p1):
        S.append(ellipsoid(p, M, (rad * 1.02, rad * 1.02, 0.35), "node", band=band_of(sk, p), part="tube"))
    # the tassel: a cord and a knot from the hand's end, the tuft hanging below (trailing the motion), or lying on the
    # ground beyond the end when the flute is laid down
    if laid:
        hang = unit(np.array([-axis[0], -axis[1], 0.0]))
    else:
        hang = unit(np.array([0.0, 0.0, -1.0]) + np.asarray(sk.drag, float) * 0.35)
    knot = p0 + hang * 1.1
    tip = knot + hang * spec["tassel"]
    S.append(cone(p0, knot, 0.3, 0.3, "cord", band=band_of(sk, knot), part="tassel"))
    S.append(sphere(knot, 0.58, "cord", band=band_of(sk, knot), part="tassel"))
    S.append(cone(knot, tip, 0.5, 0.85, "tassel", band=band_of(sk, knot), part="tassel"))
    # the note: ripples of pale jade light leaving the far end, fainter on the frame after the hit
    st = sound.stage(sk)
    if st is not None:
        radii, spans = spec["ripples"][st]
        note = (sk.weapon or {}).get("note")
        if note is not None:
            way = unit(sk.w(note))
            c = p0 - axis * 2.0 + way * 2.0
            radii = [r * spec["play_ripples"] for r in radii]
        else:
            way = axis
            c = p1 + axis * 0.6
        S += sound.arcs(c, way, radii, spans, ("ripple", "ripple_fade")[st], band_of(sk, c))
    return S
