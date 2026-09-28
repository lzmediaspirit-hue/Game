"""Blade: a blade held in the right hand along the pose's `blade` line (or laid on the ground), from a set's spec
(sets/weapon_short_blade.py, sets/weapon_jian.py): pommel, hilt, guard and blade, each piece in the band its own
depth puts it in, and a cut's smear of jade light where the pose asks for one (`smear_from`).

Spec keys:
  blade  the blade's length     width  its width at the guard     hilt  the hilt's length     guard  the guard's half-width
"""
from __future__ import annotations

import numpy as np

from ..geom import unit
from ..raster import cone, ellipsoid, sphere
from ..weapons import band_of, blade_line, flat_frame, stretch


def solids(sk, spec: dict) -> list:
    S = []
    g, d, flat = blade_line(sk)
    x = flat_frame(d, flat)
    def at(k):
        return stretch(sk, g, g + d * k)
    hilt0 = at(-(spec["hilt"] * 0.5 + 0.2))
    guard = at(spec["hilt"] * 0.5)
    S.append(sphere(at(-(spec["hilt"] * 0.5 + 0.55)), 0.62, "gold", band=band_of(sk, hilt0), part="pommel"))
    S.append(cone(hilt0, guard, 0.5, 0.5, "hilt", band=band_of(sk, g), part="hilt"))
    S.append(ellipsoid(guard, np.stack([x, np.cross(d, x), d], axis=1), (spec["guard"], 0.55, 0.42), "gold",
                       band=band_of(sk, guard), part="guard"))
    # the blade, in pieces so each lies in its own band; flat along x, a pale edge on its lit side
    n = max(2, int(spec["blade"] / 3.0))
    base = spec["hilt"] * 0.5
    for i in range(n):
        a = at(base + spec["blade"] * i / n + 0.15)
        b = at(base + spec["blade"] * (i + 1) / n)
        w0 = spec["width"] * (1.0 - 0.12 * i / n)
        w1 = spec["width"] * (1.0 - 0.12 * (i + 1) / n) if i < n - 1 else 0.3
        # round, not flat: a blade seen edge-on must still draw a pixel wide
        c = cone(a, b, w0, w1, "blade", k=0.9, side=x, band=band_of(sk, (a + b) * 0.5), part="blade",
                 paint=lambda loc, P, nn, w0=w0: (np.where(loc[:, 0] < -w0 * 0.25, "edge", "blade").astype(object),
                                                  np.zeros(len(loc), dtype=np.int16)))
        S.append(c)
    # A cut's smear: the arc the blade's outer half swept since the frame before, a pale sheet of jade light, so the
    # blow reads in every facing even when the blade itself points at the camera.
    wp = sk.weapon or {}
    if wp.get("smear_from") is not None:
        d0 = unit(sk.w(wp["smear_from"]))
        ang = float(np.degrees(np.arccos(np.clip(d0 @ d, -1.0, 1.0))))
        steps = max(6, int(ang / 4.0))
        for j in range(steps):
            t = (j + 0.5) / steps
            dj = unit(d0 * (1 - t) + d * t)
            p0 = stretch(sk, g, g + dj * (base + spec["blade"] * 0.45))
            p1 = stretch(sk, g, g + dj * (base + spec["blade"] * 1.02))
            S.append(cone(p0, p1, 0.5 + 0.3 * t, 0.75 + 0.35 * t, "smear", band=band_of(sk, (p0 + p1) * 0.5), part="smear"))
    return S
