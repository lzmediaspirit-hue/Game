"""Feet: shoes and boots over the body's feet, from a set's spec (sets/shoes.py).

Spec keys:
  boot  the shaft's height up the shin (0: a shoe)
  cuff  the material of the shaft's top band
The upper (`top`) sits over the `sole`.
"""
from __future__ import annotations

import numpy as np

from ..body import foot_solid
from ..geom import unit
from ..raster import cone


def solids(sk, spec: dict) -> list:
    S = []
    for s in ("l", "r"):
        f = foot_solid(sk, s, (2.35, 1.5, 1.25), "sole", "shoe_" + s)
        f.paint = lambda loc, P, n: (np.where((loc[:, 2] > -0.2) & (loc[:, 0] > -0.6), "top", "sole").astype(object),
                                     np.zeros(len(loc), dtype=np.int16))
        S.append(f)
        if spec["boot"] > 0.0:
            kn, an = sk.__dict__["knee_" + s], sk.__dict__["ankle_" + s]
            up = unit(kn - an)
            top = an + up * spec["boot"]
            cuff = spec["cuff"]
            H = spec["boot"] + 0.4
            S.append(cone(an - up * 0.4, top, 1.55, 1.45, "sole", part="shoe_" + s,
                          paint=lambda loc, P, n, H=H, cuff=cuff: (np.where(loc[:, 2] > H - 1.0, cuff, "sole").astype(object),
                                                                   np.zeros(len(loc), dtype=np.int16))))
    return S
