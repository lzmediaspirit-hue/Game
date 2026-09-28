"""The early weapons (parts.json `weapon`), after the side-view sheets, held in the right hand:

  dagger  Short blade   a short jade-steel blade, gold guard, brown hilt
  sword   Spirit jian   a long straight jade-steel blade with a pale edge, gold guard and pommel, dark hilt
  spear   Jade spear    a long pale shaft wound with brown cord, a jade-steel leaf head on a gold socket

A pose says where a blade points (`blade`: a direction in the figure's frame) and where a pole points (`pole`: a
direction, `two_hand` to run it through both hands, and `butt`, the grip's distance from the butt). Each weapon is cast
from the right hand along that line, piece by piece, and each piece lies in the band (behind or in front of the body)
its own depth puts it in, so a blade can pass behind the head and in front of the legs in one frame.
"""
from __future__ import annotations

import numpy as np

from .geom import depth, unit
from .raster import cone, ellipsoid, sphere

WEAPONS = {
    "dagger": {"kind": "blade", "blade": 7.2, "width": 0.8, "hilt": 2.4, "guard": 1.3},
    "sword": {"kind": "blade", "blade": 18.5, "width": 0.68, "hilt": 3.2, "guard": 1.55},
    "spear": {"kind": "pole", "length": 44.0, "head": 5.2},
}
# A weapon pointed at the camera (or away) is drawn this much longer on screen than the figure's camera would show it:
# the world's own view keeps the ground's depth at full length, so a thrust to the south must still read as a reach.
DEPTH_STRETCH = 1.6


def _stretch(sk, grip, p):
    """A point of the weapon moved away from the grip along the world's south by DEPTH_STRETCH."""
    v = np.asarray(p, float) - grip
    return grip + np.array([v[0], v[1] * DEPTH_STRETCH, v[2]])


def _band(sk, p) -> str:
    return "front" if depth(p) >= depth(sk.chest) - 0.9 else "back"


def _flat_frame(axis, flat):
    w = unit(axis)
    x = unit(flat - w * float(flat @ w))
    if float(np.linalg.norm(x)) < 1e-6:
        x = unit(np.cross(w, np.array([0.0, 0.0, 1.0])))
    return x


def _blade_dir(sk):
    """The blade's grip point, direction and flat in the world (in the right hand, or laid on the ground)."""
    wp = sk.weapon or {}
    laid = wp.get("laid")
    if laid:
        return sk.pt(laid["at"]), unit(sk.w(laid["dir"])), unit(sk.w((0.0, 0.0, 1.0)))
    return sk.hand_r, unit(sk.w(wp.get("blade", (0.35, 0.3, -1.0)))), unit(sk.w(wp.get("flat", (0.0, 1.0, 0.0))))


def _pole_line(sk):
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


def solids(sk, name: str) -> list:
    spec = WEAPONS[name]
    S = []
    if spec["kind"] == "blade":
        g, d, flat = _blade_dir(sk)
        x = _flat_frame(d, flat)
        def at(k):
            return _stretch(sk, g, g + d * k)
        hilt0 = at(-(spec["hilt"] * 0.5 + 0.2))
        guard = at(spec["hilt"] * 0.5)
        S.append(sphere(at(-(spec["hilt"] * 0.5 + 0.55)), 0.62, "gold", band=_band(sk, hilt0), part="pommel"))
        S.append(cone(hilt0, guard, 0.5, 0.5, "hilt", band=_band(sk, g), part="hilt"))
        S.append(ellipsoid(guard, np.stack([x, np.cross(d, x), d], axis=1), (spec["guard"], 0.55, 0.42), "gold",
                           band=_band(sk, guard), part="guard"))
        # the blade, in pieces so each lies in its own band; flat along x, a pale edge on its lit side
        n = max(2, int(spec["blade"] / 3.0))
        base = spec["hilt"] * 0.5
        for i in range(n):
            a = at(base + spec["blade"] * i / n + 0.15)
            b = at(base + spec["blade"] * (i + 1) / n)
            w0 = spec["width"] * (1.0 - 0.12 * i / n)
            w1 = spec["width"] * (1.0 - 0.12 * (i + 1) / n) if i < n - 1 else 0.3
            # round, not flat: a blade seen edge-on must still draw a pixel wide
            c = cone(a, b, w0, w1, "blade", k=0.9, side=x, band=_band(sk, (a + b) * 0.5), part="blade",
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
                p0 = _stretch(sk, g, g + dj * (base + spec["blade"] * 0.45))
                p1 = _stretch(sk, g, g + dj * (base + spec["blade"] * 1.02))
                S.append(cone(p0, p1, 0.5 + 0.3 * t, 0.75 + 0.35 * t, "smear", band=_band(sk, (p0 + p1) * 0.5), part="smear"))
        return S
    d, butt0 = _pole_line(sk)
    grip = sk.hand_r if not (sk.weapon or {}).get("laid") else butt0

    def at(k):
        return _stretch(sk, grip, butt0 + d * k)
    L = spec["length"]
    butt = at(0.0)
    head0 = at(L - spec["head"])
    n = 8
    side = unit(np.cross(d, np.array([0.0, 0.0, 1.0]))) if abs(d[2]) < 0.95 else np.array([1.0, 0.0, 0.0])
    for i in range(n):
        a = at((L - spec["head"]) * i / n)
        b = at((L - spec["head"]) * (i + 1) / n)
        seg = cone(a, b, 0.58, 0.58, "shaft", band=_band(sk, (a + b) * 0.5), part="shaft",
                   paint=lambda loc, P, nn: (np.where(((loc[:, 2] + 0.0) % 2.4) < 0.8, "cord", "shaft").astype(object),
                                             np.zeros(len(loc), dtype=np.int16)))
        S.append(seg)
    S.append(sphere(butt, 0.55, "hilt", band=_band(sk, butt), part="butt"))
    S.append(cone(at(L - spec["head"] - 0.9), at(L - spec["head"] + 0.2), 0.62, 0.72, "gold", band=_band(sk, head0), part="socket"))
    # the leaf head: widest a third of the way up
    mid = at(L - spec["head"] * 0.65)
    tip = at(L)
    S.append(cone(at(L - spec["head"] + 0.2), mid, 0.6, 1.05, "blade", k=0.7, side=side, band=_band(sk, mid), part="head",
                  paint=lambda loc, P, nn: (np.where(loc[:, 0] < -0.3, "edge", "blade").astype(object), np.zeros(len(loc), dtype=np.int16))))
    S.append(cone(mid, tip, 1.05, 0.3, "blade", k=0.7, side=side, band=_band(sk, tip), part="head",
                  paint=lambda loc, P, nn: (np.where(loc[:, 0] < -0.3, "edge", "blade").astype(object), np.zeros(len(loc), dtype=np.int16))))
    return S
