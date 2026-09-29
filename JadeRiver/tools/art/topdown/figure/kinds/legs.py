"""Legs: trousers over the body's hips and legs, from a set's spec (sets/pants.py).

Spec keys:
  fit   the leg's growth over the body at the thigh, knee and ankle
  bands [(from, to)] along the shin from the knee (negative: from the ankle), painted in `band`
  band  the material of those bands (a wrap)
The cloth creases behind the knee and gathers over the ankle (folds.trouser).
"""
from __future__ import annotations

import numpy as np

from ..geom import unit
from ..raster import cone, ellipsoid, limb, sphere
from . import folds as F


def solids(sk, spec: dict) -> list:
    gt, gk, ga = spec["fit"]
    S = [ellipsoid(sk.pelvis - sk.Mp[:, 2] * 0.5, sk.Mp, (2.6 + 0.8, 3.8 + 0.85, 2.4 + 0.8), "cloth", part="hips")]
    for s in ("l", "r"):
        hp, kn, an = (sk.__dict__[k + "_" + s] for k in ("hip", "knee", "ankle"))
        thigh = limb(hp, kn, 1.85 + gt, 1.5 + gk, "cloth", part="leg_" + s)
        thigh[0].paint = F.wrap(None, "cloth", F.trouser(False, float(np.linalg.norm(kn - hp))))
        S += thigh
        end = an + unit(an - kn) * 0.3
        L = float(np.linalg.norm(end - kn))
        spans = [(a if a >= 0 else L + a, b if b > 0 else L + b) for a, b in spec["bands"]]

        def shin_paint(loc, P, n, spans=spans):
            w = loc[:, 2]
            on = np.zeros(len(loc), dtype=bool)
            for a, b in spans:
                on |= (w >= a) & (w <= b)
            return np.where(on, spec["band"], "cloth").astype(object), np.zeros(len(loc), dtype=np.int16)
        S += [cone(kn, end, 1.5 + gk, 1.15 + ga, "cloth", part="leg_" + s,
                   paint=F.wrap(shin_paint, "cloth", F.trouser(True, L))),
              sphere(kn, 1.5 + gk, "cloth", part="leg_" + s)]
    return S
