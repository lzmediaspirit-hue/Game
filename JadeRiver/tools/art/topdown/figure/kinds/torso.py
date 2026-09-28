"""Torso: a shirt, coat or robe over the body's trunk and arms, from a set's spec (sets/shirt.py), so it moves with the
pose it is cast from. Its regions (belt, lapels, panels, sash, hem, cuffs) are painted in the frame of the part they sit
on. `cloth` takes the dye and `panel` a lighter step of it (palettes.DYEABLE), as the side view's luminance dye bake
does; trim, belts and accents keep their colour.

Spec keys:
  collar  cross: a crossed collar, left over right, edged in `trim`; vee: an open V edged in `trim`
  panel   a lighter front panel between the lapels (`panel`), with an accent: band (a diagonal stripe), emblem
  sleeve  wrist (to the wrist, a `cuff` band) | none (bare arms)
  hem     how far the skirt falls below the belt; `flare` its spread; `apron` a front flap of `panel` below the belt
  sash    a gold cord knotted at the belt, its ends hanging in front; `dots` scattered gold dots
"""
from __future__ import annotations

import numpy as np

from ..body import arm_bands, torso
from ..geom import unit
from ..raster import cone, limb, sphere


def _chest_paint(sk, spec):
    """The shirt's regions over the trunk, in the chest's frame (origin the chest, axes forward/right/up)."""
    wu = float((sk.waist - sk.chest) @ sk.Mc[:, 2])       # the belt's height in the chest frame

    def paint(loc, P, n):
        f, r, u = loc[:, 0], loc[:, 1], loc[:, 2]
        names = np.array(["cloth"] * len(loc), dtype=object)
        bias = np.zeros(len(loc), dtype=np.int16)
        front = f > 0.4
        if spec["collar"] == "cross":
            # the lapel edge: from the left of the neck down to the right armpit
            edge_r = -1.3 + (3.2 - u) / 5.6 * 4.6
            on = front & (u < 4.2) & (u > wu + 0.9) & (np.abs(r - edge_r) < 0.6)
            names[on] = spec["trim"]
            under = front & (u > wu + 0.9) & (r > edge_r + 0.6) & (r < edge_r + 1.5) & (u < 4.2)
            bias[under] = -1                                   # the overlapping lapel's shadow
        else:
            # a V from both sides of the neck to the belt; the panel (or the undershirt's shade) between
            half = np.maximum(0.0, (u - wu) / (4.2 - wu)) * 2.3
            edge = front & (u > wu + 0.8) & (np.abs(np.abs(r) - half) < 0.55)
            inside = front & (u > wu + 0.8) & (np.abs(r) < half - 0.55)
            if spec.get("panel"):
                names[inside] = "panel"
                if spec["panel"] == "band":
                    stripe = inside & (np.abs(r + (u - wu) * 0.55 - 0.9) < 0.55)
                    names[stripe] = "accent"
                    names[inside & (np.abs(r + (u - wu) * 0.55 - 0.1) < 0.28)] = "trim"
                elif spec["panel"] == "emblem":
                    mid = wu + (4.2 - wu) * 0.45
                    names[inside & (np.abs(r) + np.abs(u - mid) * 0.8 < 0.9)] = "accent"
            else:
                bias[inside] = -1
            names[edge] = spec["trim"]
        if spec.get("dots"):
            dot = (((np.floor(r * 0.9 + 7) + np.floor(u * 0.9 + 7) * 3) % 5) == 0) & (np.abs(r % 1.1 - 0.55) < 0.3) & \
                  (np.abs(u % 1.1 - 0.55) < 0.3) & (u > wu + 1.0)
            names[dot & (names == "cloth")] = "trim"
        if spec["belt"]:
            belt = np.abs(u - wu) < 0.95
            names[belt] = spec["belt"]
            if spec.get("buckle"):
                names[belt & (f > 1.0) & (np.abs(r) < 0.75)] = "trim"
        return names, bias
    return paint


def _skirt(sk, spec) -> list:
    """The skirt: from the waist to the hem, swinging with the thighs; a hem trim or a front apron of the panel."""
    knees = (sk.knee_l + sk.knee_r) * 0.5
    hips = (sk.hip_l + sk.hip_r) * 0.5
    down = unit(unit(knees - hips) * 0.55 + (-sk.Mp[:, 2]) * 0.45)
    top = sk.waist - sk.Mp[:, 2] * 0.2
    L = spec["hem"] + 2.0
    long = spec["hem"] > 8.0
    if long:   # a long robe hangs straighter, parting over the stride
        down = unit(down * 0.6 + (-sk.Mp[:, 2]) * 0.4)
    fwd = sk.Mp[:, 0]

    def paint(loc, P, n):
        names = np.array(["cloth"] * len(loc), dtype=object)
        bias = np.zeros(len(loc), dtype=np.int16)
        if spec.get("hem_trim"):
            names[loc[:, 2] > L - 0.75] = spec["trim"]
        if long:
            # the robe's front opening: a darker seam down the middle
            side = (P - top) @ sk.Mp[:, 1]
            ahead = (P - top) @ fwd
            bias[(np.abs(side) < 0.5) & (ahead > 0.8)] = -1
        return names, bias
    S = [cone(top, top + down * L, 3.9, 4.3 + spec["flare"], "cloth", k=0.74 if not long else 0.8, side=sk.Mp[:, 1],
              part="skirt", paint=paint)]
    if spec.get("apron"):
        a0 = top + fwd * 2.4
        S.append(cone(a0, a0 + down * spec["apron"] + fwd * 0.6, 2.2, 2.5, "panel", k=0.3, side=sk.Mp[:, 1], part="apron",
                      paint=lambda loc, P, n: (np.where(np.abs(loc[:, 0] + loc[:, 2] * 0.35 - 1.6) < 0.5, "accent", "panel").astype(object),
                                               np.zeros(len(loc), dtype=np.int16))))
    return S


def solids(sk, spec: dict) -> list:
    bands = arm_bands(sk)
    S = torso(sk, 0.62, "cloth", "shirt", paint=_chest_paint(sk, spec), frame=(sk.chest, sk.Mc))
    S += _skirt(sk, spec)
    if spec["belt"]:
        buckle = spec.get("buckle")
        S.append(cone(sk.waist - sk.Mp[:, 2] * 1.0, sk.waist + sk.Mp[:, 2] * 0.9, 4.25, 4.25, spec["belt"], k=0.74,
                      side=sk.Mp[:, 1], part="shirt", frame=(sk.waist, sk.Mp),
                      paint=lambda loc, P, n: (np.where(bool(buckle) & (loc[:, 0] > 2.6) & (np.abs(loc[:, 1]) < 0.8), "trim", spec["belt"]).astype(object),
                                               np.zeros(len(loc), dtype=np.int16))))
    if spec.get("sash"):
        # a gold cord round the waist, knotted in front, two ends hanging
        S.append(cone(sk.waist - sk.Mp[:, 2] * 0.5, sk.waist + sk.Mp[:, 2] * 0.5, 4.3, 4.3, "trim", k=0.74,
                      side=sk.Mp[:, 1], part="sash"))
        knot = sk.waist + sk.Mp[:, 0] * 3.3 + sk.Mp[:, 1] * 0.8
        S.append(sphere(knot, 0.8, "trim", part="sash"))
        for dr in (-0.4, 0.6):
            end = knot + sk.Mp[:, 1] * dr + (-sk.Mp[:, 2]) * 4.2 + sk.Mp[:, 0] * 0.6
            S += limb(knot, end, 0.4, 0.35, "trim", part="sash")
    if spec["sleeve"] != "none":
        for s in ("l", "r"):
            sh, el, wr = (sk.__dict__[k + "_" + s] for k in ("shoulder", "elbow", "wrist"))
            bu, bf = bands["upper_" + s], bands["fore_" + s]
            S.append(sphere(sh, 2.2, "cloth", band=bu, part="sleeve_" + s))
            S += limb(sh, el, 1.95, 1.85, "cloth", band=bu, part="sleeve_" + s)
            end = wr - unit(wr - el) * 0.25
            L = float(np.linalg.norm(end - el))
            cuff = spec["cuff"]
            S.append(cone(el, end, 1.85, 2.0, "cloth", band=bf, part="sleeve_" + s,
                          paint=lambda loc, P, n, L=L, cuff=cuff: (np.where(loc[:, 2] > L - 1.0, cuff, "cloth").astype(object),
                                                                   np.where(loc[:, 2] > L - 1.0, -1 if cuff == "cloth" else 0, 0).astype(np.int16))))
            S.append(sphere(el, 1.85, "cloth", band=bf, part="sleeve_" + s))
    else:
        # a vest's armholes: the shoulder seam
        for s in ("l", "r"):
            S.append(sphere(sk.__dict__["shoulder_" + s] + sk.Mc[:, 2] * 0.3, 1.5, "cloth", part="shirt"))
    return S
