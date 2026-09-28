"""Pole: a pole held along the pose's `pole` line, through both hands when it says so (or laid on the ground), from a
set's spec (sets/weapon_spear.py, sets/weapon_staff.py): a corded shaft with a leaf head on a gold socket, or a
gold-banded staff with a hooked head.

Spec keys:
  length  the pole's length     head  the leaf head's length (0: none)     staff  a staff: gold bands and a hooked head
"""
from __future__ import annotations

import numpy as np

from ..geom import unit
from ..raster import cone, sphere
from ..weapons import band_of, pole_line, stretch


def solids(sk, spec: dict) -> list:
    S = []
    d, butt0 = pole_line(sk)
    grip = sk.hand_r if not (sk.weapon or {}).get("laid") else butt0

    def at(k):
        return stretch(sk, grip, butt0 + d * k)
    L = spec["length"]
    butt = at(0.0)
    head0 = at(L - spec["head"])
    n = 8
    side = unit(np.cross(d, np.array([0.0, 0.0, 1.0]))) if abs(d[2]) < 0.95 else np.array([1.0, 0.0, 0.0])
    if spec.get("staff"):
        for i in range(n):
            a = at(L * i / n)
            b = at(L * (i + 1) / n)
            S.append(cone(a, b, 0.62, 0.62, "hilt", band=band_of(sk, (a + b) * 0.5), part="shaft",
                          paint=lambda loc, P, nn: (np.where((loc[:, 2] % 4.25) < 0.7, "gold", "hilt").astype(object),
                                                    np.zeros(len(loc), dtype=np.int16))))
        top = at(L)
        S.append(sphere(butt, 0.6, "gold", band=band_of(sk, butt), part="butt"))
        for k, (fw, sd) in enumerate(((0.3, 0.2), (1.1, 0.9), (1.4, 1.9), (1.0, 2.8), (0.2, 3.1))):
            p = stretch(sk, grip, butt0 + d * (L + fw)) + side * sd
            S.append(sphere(p, 0.62, "gold", band=band_of(sk, p), part="hook"))
        S.append(sphere(top, 0.7, "gold", band=band_of(sk, top), part="hook"))
        return S
    for i in range(n):
        a = at((L - spec["head"]) * i / n)
        b = at((L - spec["head"]) * (i + 1) / n)
        seg = cone(a, b, 0.58, 0.58, "shaft", band=band_of(sk, (a + b) * 0.5), part="shaft",
                   paint=lambda loc, P, nn: (np.where(((loc[:, 2] + 0.0) % 2.4) < 0.8, "cord", "shaft").astype(object),
                                             np.zeros(len(loc), dtype=np.int16)))
        S.append(seg)
    S.append(sphere(butt, 0.55, "hilt", band=band_of(sk, butt), part="butt"))
    S.append(cone(at(L - spec["head"] - 0.9), at(L - spec["head"] + 0.2), 0.62, 0.72, "gold", band=band_of(sk, head0), part="socket"))
    # the leaf head: widest a third of the way up
    mid = at(L - spec["head"] * 0.65)
    tip = at(L)
    S.append(cone(at(L - spec["head"] + 0.2), mid, 0.6, 1.05, "blade", k=0.7, side=side, band=band_of(sk, mid), part="head",
                  paint=lambda loc, P, nn: (np.where(loc[:, 0] < -0.3, "edge", "blade").astype(object), np.zeros(len(loc), dtype=np.int16))))
    S.append(cone(mid, tip, 1.05, 0.3, "blade", k=0.7, side=side, band=band_of(sk, tip), part="head",
                  paint=lambda loc, P, nn: (np.where(loc[:, 0] < -0.3, "edge", "blade").astype(object), np.zeros(len(loc), dtype=np.int16))))
    return S
