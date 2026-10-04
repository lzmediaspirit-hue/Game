"""Bell: a bronze hand-bell on a short dark-wood handle in the right hand along the pose's `blade` line (or laid on its
side on the ground), from a set's spec (sets/weapon_bell.py). The side view holds it the same way, drawn along the
short blade's grip (the side view's weapon bake bell_frame): the handle in the fist with a red cord at its end, the bell
past the hand with its mouth along the line, a domed crown, a band under it, a flared lip with a dark rim, and the
clapper in the mouth (its inside a shadowed bronze, so a bell turned to the camera reads as a bronze cup, not a hole).
On a blow's hit frame and the one after, it rings out rings of pale-gold qi round the mouth (kinds/sound.py), fainter
on the frame after.

Spec keys (lengths along the line from the grip):
  handle  the handle's two ends      crown  where the bell's crown sits      dome  the crown's radius and depth
  waist   where the body starts to flare, and its radius      lip  the mouth's distance and radius
  band    the band under the crown (its two ends)      cord  the cord's length
  rings   per stage, the rings' radii about the mouth
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
    lip_k, lip_r = spec["lip"]
    if laid:
        # on its side: the handle's end on the ground, the axis rising so the lip rests on it
        g = g + UP * 0.2
        d = unit(np.array([d[0], d[1], 0.0]) + UP * ((lip_r + 0.1 - g[2]) / lip_k))

    def at(k):
        return stretch(sk, g, g + d * k)
    o = at(0.0)
    axis = unit(at(1.0) - o)
    per = float(np.linalg.norm(at(1.0) - o))
    side = np.cross(axis, UP)
    side = unit(side) if float(np.linalg.norm(side)) > 1e-3 else unit(np.cross(axis, np.array([1.0, 0.0, 0.0])))
    M = np.stack([side, np.cross(axis, side), axis], axis=1)

    # the handle, the fist closed round it (what is inside the hand is left out, so the hand shows over the grip)
    h0, h1 = spec["handle"]
    hand = None if laid else sk.hand_r

    def clip(loc):
        if hand is None:
            return np.ones(len(loc), dtype=bool)
        return np.linalg.norm(o + loc @ M.T - hand, axis=1) > HAND_R * 0.92
    a, b = at(h0), at(h1)
    hb = band_of(sk, (a + b) * 0.5)
    S.append(cone(a, b, 0.5, 0.56, "wood", band=hb, part="handle", clip=clip, frame=(o, M)))
    S.append(sphere(a, 0.62, "bronze", band=band_of(sk, a), part="knob"))
    # the red cord hanging from the handle's end (lying on the ground beyond it when laid)
    hang = unit(np.array([-axis[0], -axis[1], 0.0])) if laid else \
        unit(np.array([0.0, 0.0, -1.0]) + np.asarray(sk.drag, float) * 0.35)
    knot = a + hang * spec["cord"]
    S.append(cone(a, knot, 0.3, 0.3, "cord", band=band_of(sk, knot), part="cord"))
    S.append(sphere(knot, 0.55, "cord", band=band_of(sk, knot), part="cord"))
    S.append(cone(knot, knot + hang * 1.2, 0.45, 0.6, "cord", band=band_of(sk, knot), part="cord"))

    # the bell, one piece in one band
    crown = spec["crown"]
    dome_r, dome_d = spec["dome"]
    waist_k, waist_r = spec["waist"]
    bb = band_of(sk, at((crown + lip_k) * 0.5))
    band0, band1 = spec["band"]

    def paint(loc, P, nn):
        k = loc[:, 2] / per
        names = np.full(len(loc), "bronze", dtype=object)
        names[(k > band0) & (k < band1)] = "rim"
        names[k > lip_k - 0.3] = "rim"
        names[(nn @ TOWARD) < -0.02] = "mouth"          # the inside of the far wall, seen through the mouth
        return names, np.zeros(len(loc), dtype=np.int16)
    S.append(sphere(at(crown - 0.2), 0.72, "bronze", band=bb, part="bell"))
    c = at(crown + dome_d)
    S.append(ellipsoid(c, M, (dome_r, dome_r, dome_d * per), "bronze", band=bb, part="bell"))
    S.append(cone(c, at(waist_k), dome_r, waist_r, "bronze", band=bb, part="bell", paint=paint, frame=(o, M)))
    S.append(cone(at(waist_k), at(lip_k), waist_r, lip_r, "bronze", band=bb, part="bell", paint=paint, frame=(o, M)))
    # the mouth's inside, just within the lip, and the clapper hanging in it
    S.append(ellipsoid(at(lip_k - 0.45), M, (lip_r * 0.9, lip_r * 0.9, 0.05), "mouth", band=bb, part="mouth"))
    S.append(sphere(at(lip_k - 0.1), 0.62, "bronze", band=bb, part="clapper"))

    # the peal: rings of pale-gold qi round the mouth
    st = sound.stage(sk)
    if st is not None:
        mouth = at(lip_k) + axis * 0.8
        n = len(spec["rings"][st])
        S += sound.arcs(mouth, axis, spec["rings"][st], [np.pi] * n, ("ring", "ring_fade")[st], band_of(sk, mouth),
                        shrink=0.0)
    return S
