"""Hands: something worn over the hands and wrists (the training gauntlets), from a set's spec (sets/weapon_gauntlets.py).
"""
from __future__ import annotations

import numpy as np

from ..body import arm_bands
from ..geom import unit
from ..raster import cone, sphere


def solids(sk, spec: dict | None = None) -> list:
    """The training gauntlets (the side view's gauntlet bake): a steel fist over each hand and a bronze-banded steel cuff
    round the wrist."""
    bands = arm_bands(sk)
    S = []
    for s in ("l", "r"):
        el, wr, hd = (sk.__dict__[k + "_" + s] for k in ("elbow", "wrist", "hand"))
        bf = bands["fore_" + s]
        d = unit(wr - el)
        S.append(sphere(hd, 1.65, "steel", band=bf, part="fist_" + s))
        S.append(cone(wr - d * 1.9, wr + d * 0.2, 1.6, 1.75, "steel", band=bf, part="cuff_" + s,
                      paint=lambda loc, P, n: (np.where(loc[:, 2] > 1.5, "bronze", "steel").astype(object),
                                               np.zeros(len(loc), dtype=np.int16))))
    return S
