"""Back: a cape from the shoulders down the back, from a set's spec (sets/cape.py).

Spec keys:
  length, width  the sheet's length and its width at the shoulders
  ragged         its end torn into rags
"""
from __future__ import annotations

from ..geom import vec
from ..raster import ellipsoid
from .hair import tail


def solids(sk, spec: dict) -> list:
    """A cape hung from the shoulders down the back, trailing the pose's drag; the tattered one ends in rags."""
    back = -sk.Mc[:, 0]
    up = sk.Mc[:, 2]
    start = sk.chest + sk.Mc @ vec(-3.3, 0.0, 2.6)
    S = [ellipsoid(sk.chest + sk.Mc @ vec(-2.0, 0.0, 3.0), sk.Mc, (2.2, 4.6, 0.9), "cape", part="cape_yoke", band="mid")]
    S += tail(sk, start, back * 0.35 - up, spec["length"], spec["width"], spec["width"] + 1.3, segs=6, stiff=0.6,
              mat="cape", part="cape", k=0.16, ragged=spec["ragged"])
    return S
