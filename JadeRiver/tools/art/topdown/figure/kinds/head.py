"""Head: a hat over the hair, from a set's spec (sets/hat.py).

Spec `kind`:
  cone  a wide cone (`brim`, `height`) of plaited straw with a band above the crown's rim
  band  a cloth band round the head at `at` (unit height on the hair cap), `half` wide, `grow` off the skull; `studs`
        in front, or `tails`: two ends tied at the back and trailing
  crown a small jade crown on the top knot, gold-rimmed, a gold pin through it
  veil  a wide-brimmed (`brim`) felt hat with a band, a veil of gauze in stripes hanging from the brim
"""
from __future__ import annotations

import numpy as np

from ..body import SKULL
from ..geom import vec
from ..raster import cone, ellipsoid, sphere
from .hair import CAP_AT, CAP_GROW, tail


def solids(sk, spec: dict) -> list:
    Mh = sk.Mh
    up = Mh[:, 2]
    kind = spec["kind"]
    if kind == "cone":
        base = sk.head + up * 4.4
        apex = base + up * spec["height"]
        # a shallow cone with a rounded rim, plaited in radial ribs; the band just above the crown's rim
        return [cone(base, apex, spec["brim"], 0.4, "straw", side=Mh[:, 1], part="hat",
                     paint=lambda loc, P, n: (np.where((loc[:, 2] > 0.9) & (loc[:, 2] < 1.6), "band", "straw").astype(object),
                                              np.where(((np.degrees(np.arctan2(loc[:, 1], loc[:, 0])) + 180) % 24) < 3, -1, 0).astype(np.int16))),
                ellipsoid(base, Mh, (spec["brim"], spec["brim"], 0.45), "straw", part="hat")]
    if kind == "band":
        c = sk.head + Mh @ vec(*CAP_AT)
        radii = np.array(SKULL) + np.array(CAP_GROW) + spec["grow"] - np.array(CAP_GROW)

        def clip(loc):
            u = loc / radii
            u = u / np.maximum(np.linalg.norm(u, axis=1), 1e-9)[:, None]
            return np.abs(u[:, 2] - spec["at"]) < spec["half"]

        def paint(loc, P, n):
            u = loc / radii
            phi = np.degrees(np.arctan2(u[:, 1], u[:, 0]))
            stud = (np.abs(phi) < 50) & ((np.floor((phi + 180) / 12) % 2) == 0) if spec.get("studs") else np.zeros(len(loc), bool)
            return np.where(stud, "stud", "cloth").astype(object), np.zeros(len(loc), dtype=np.int16)
        S = [ellipsoid(c, Mh, radii, "cloth", part="hat", clip=clip, paint=paint, frame=(c, Mh))]
        if spec.get("tails"):
            knot = c + Mh @ vec(-radii[0] * 0.95, 0, radii[2] * spec["at"])
            S.append(sphere(knot, 0.7, "cloth", part="hat"))
            for dr in (-0.8, 0.8):
                S += tail(sk, knot + Mh @ vec(0, dr * 0.5, 0), -Mh[:, 0] * 0.6 + Mh[:, 1] * dr * 0.4 - up * 0.8, 5.5, 0.55,
                          0.4, segs=3, stiff=0.5, mat="cloth", part="hat_tail")
        return S
    if kind == "crown":
        base = sk.head + up * 6.6 - Mh[:, 0] * 0.8
        top = base + up * 2.2
        pin = base + up * 1.3 + Mh[:, 0] * 1.9
        return [cone(base, top, 1.9, 1.5, "jade", side=Mh[:, 1], part="hat",
                     paint=lambda loc, P, n: (np.where((loc[:, 2] < 0.45) | (loc[:, 2] > 1.8), "gold", "jade").astype(object),
                                              np.zeros(len(loc), dtype=np.int16))),
                ellipsoid(top, Mh, (1.5, 1.5, 0.5), "gold", part="hat"),
                cone(pin - Mh[:, 1] * 3.4, pin + Mh[:, 1] * 3.4, 0.45, 0.4, "gold", part="hat_pin")]
    # weimao: brim, crown with a red band, and a veil of pale gauze hanging from the brim (stripes, so the face shows)
    base = sk.head + up * 4.6
    S = [ellipsoid(base, Mh, (spec["brim"], spec["brim"], 0.45), "felt", part="hat"),
         cone(base, base + up * 2.6, 3.7, 3.2, "felt", side=Mh[:, 1], part="hat",
              paint=lambda loc, P, n: (np.where(loc[:, 2] < 0.8, "band", "felt").astype(object), np.zeros(len(loc), dtype=np.int16))),
         ellipsoid(base + up * 2.6, Mh, (3.2, 3.2, 0.6), "felt", part="hat")]

    def veil_clip(loc):
        phi = np.degrees(np.arctan2(loc[:, 1], loc[:, 0])) + 180.0
        return (np.floor(phi / 9.0) % 2) == 0
    S.append(cone(base - up * 0.2, base - up * 6.2, spec["brim"] - 0.2, spec["brim"] + 0.1, "veil", side=Mh[:, 1],
                  part="veil", clip=veil_clip))
    return S
