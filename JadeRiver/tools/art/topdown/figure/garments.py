"""Clothes over the body's own solids, so each garment moves with the pose it is cast from.

Shirts (parts.json `shirt`), trousers (`pants`) and shoes (`shoes`) are described by a few parameters each; the side
view's design for each is in the comment beside it. A garment's regions (belt, collar trim, hem, cuffs, wraps, toe
caps) are painted in the frame of the part they sit on, wherever the pose puts it. Materials named `cloth` take the
dye (palettes.DYEABLE); trim, belts and soles keep their colour, as in the side view's dye bake.
"""
from __future__ import annotations

import numpy as np

from .body import arm_bands, foot_solid, torso
from .geom import unit, vec
from .raster import cone, ellipsoid, limb, sphere

# Shirts. collar: cross (a crossed collar, left over right, with trim) | vee | none. sleeve: wrist | elbow | none.
# hem: how far the skirt falls below the belt (figure units). trim: the collar, hem and cuff edging's material.
SHIRTS = {
    # Disciple tunic (the starting shirt): navy teal, long sleeves, a crossed collar edged in gold, a dark belt with a gold
    # buckle, a short skirt to mid-thigh with a gold hem.
    "disciple": {"collar": "cross", "sleeve": "wrist", "hem": 3.6, "flare": 0.8, "trim": "trim", "belt": "belt",
                 "cuff": "trim", "hem_trim": True},
}

# Trousers. fit: the leg's growth over the body (thigh, knee, ankle); wrap: an ankle band's material or None.
PANTS = {
    # Silk trousers (the starting pair): loose jade-teal legs gathered at the ankle by grey wraps.
    "loose": {"fit": (1.05, 1.0, 0.95), "wrap": "wrap", "wrap_len": 1.6},
}

# Shoes. top: the upper's material over the `sole` material; `boot` raises the shaft up the shin.
SHOES = {
    # Cloth shoes (the starting pair): dark brown, a tan upper.
    "slippers": {"top": "top", "sole": "sole", "boot": 0.0},
}


def _chest_paint(sk, spec):
    """The shirt's regions over the trunk, in the chest's frame (origin the chest, axes forward/right/up)."""
    wu = float((sk.waist - sk.chest) @ sk.Mc[:, 2])       # the belt's height in the chest frame

    def paint(loc, P, n):
        f, r, u = loc[:, 0], loc[:, 1], loc[:, 2]
        names = np.array(["cloth"] * len(loc), dtype=object)
        bias = np.zeros(len(loc), dtype=np.int16)
        if spec["collar"] == "cross":
            # the lapel edge: from the left of the neck down to the right armpit
            t = (3.2 - u) / 5.6
            edge_r = -1.3 + t * 4.6
            on = (f > 0.4) & (u < 4.2) & (u > wu + 0.9) & (np.abs(r - edge_r) < 0.6)
            names[on] = spec["trim"]
            under = (f > 0.4) & (u > wu + 0.9) & (r > edge_r + 0.6) & (r < edge_r + 1.5) & (u < 4.2)
            bias[under] = -1                                   # the overlapping lapel's shadow
        if spec["belt"]:
            belt = np.abs(u - wu) < 0.95
            names[belt] = spec["belt"]
            buckle = belt & (f > 1.0) & (np.abs(r) < 0.75)
            names[buckle] = "trim"
        return names, bias
    return paint


def shirt(sk, name: str) -> list:
    spec = SHIRTS[name]
    bands = arm_bands(sk)
    S = torso(sk, 0.62, "cloth", "shirt", paint=_chest_paint(sk, spec), frame=(sk.chest, sk.Mc))
    # the skirt: from the waist to the hem, swinging with the thighs
    knees = (sk.knee_l + sk.knee_r) * 0.5
    hips = (sk.hip_l + sk.hip_r) * 0.5
    down = unit(knees - hips) * 0.55 + (-sk.Mp[:, 2]) * 0.45
    down = unit(down)
    top = sk.waist - sk.Mp[:, 2] * 0.2
    hem = top + down * (spec["hem"] + 2.0)
    wu = spec["hem"] + 2.0

    def skirt_paint(loc, P, n):
        names = np.array(["cloth"] * len(loc), dtype=object)
        if spec.get("hem_trim"):
            names[loc[:, 2] > wu - 0.75] = spec["trim"]
        return names, np.zeros(len(loc), dtype=np.int16)
    S.append(cone(top, hem, 3.9, 4.3 + spec["flare"], "cloth", k=0.74, side=sk.Mp[:, 1], part="skirt", paint=skirt_paint))
    if spec["belt"]:
        S.append(cone(sk.waist - sk.Mp[:, 2] * 1.0, sk.waist + sk.Mp[:, 2] * 0.9, 4.25, 4.25, spec["belt"], k=0.74,
                      side=sk.Mp[:, 1], part="shirt",
                      paint=lambda loc, P, n: (np.where((loc[:, 0] > 2.6) & (np.abs(loc[:, 1]) < 0.8), "trim", spec["belt"]).astype(object),
                                               np.zeros(len(loc), dtype=np.int16)), frame=(sk.waist, sk.Mp)))
    if spec["sleeve"] != "none":
        for s in ("l", "r"):
            sh, el, wr = (sk.__dict__[k + "_" + s] for k in ("shoulder", "elbow", "wrist"))
            bu, bf = bands["upper_" + s], bands["fore_" + s]
            S.append(sphere(sh, 2.2, "cloth", band=bu, part="sleeve_" + s))
            S += limb(sh, el, 1.95, 1.85, "cloth", band=bu, part="sleeve_" + s)
            if spec["sleeve"] == "wrist":
                end = wr - unit(wr - el) * 0.25
                cuff_at = 1.0

                def cuff_paint(loc, P, n, L=float(np.linalg.norm(end - el))):
                    names = np.where(loc[:, 2] > L - cuff_at, spec["cuff"], "cloth").astype(object)
                    return names, np.zeros(len(loc), dtype=np.int16)
                c = cone(el, end, 1.85, 2.0, "cloth", band=bf, part="sleeve_" + s, paint=cuff_paint)
                S += [c, sphere(el, 1.85, "cloth", band=bf, part="sleeve_" + s)]
    return S


def pants(sk, name: str) -> list:
    spec = PANTS[name]
    gt, gk, ga = spec["fit"]
    S = [ellipsoid(sk.pelvis - sk.Mp[:, 2] * 0.5, sk.Mp, (2.6 + 0.8, 3.8 + 0.85, 2.4 + 0.8), "cloth", part="hips")]
    for s in ("l", "r"):
        hp, kn, an = (sk.__dict__[k + "_" + s] for k in ("hip", "knee", "ankle"))
        S += limb(hp, kn, 1.85 + gt, 1.5 + gk, "cloth", part="leg_" + s)
        wrap = spec["wrap"]
        L = float(np.linalg.norm(an - kn))

        def shin_paint(loc, P, n, L=L, wrap=wrap):
            names = np.where(loc[:, 2] > L - spec["wrap_len"], wrap, "cloth").astype(object) if wrap else \
                np.array(["cloth"] * len(loc), dtype=object)
            return names, np.zeros(len(loc), dtype=np.int16)
        c = cone(kn, an + unit(an - kn) * 0.3, 1.5 + gk, 1.15 + ga, "cloth", part="leg_" + s, paint=shin_paint)
        S += [c, sphere(kn, 1.5 + gk, "cloth", part="leg_" + s)]
    return S


def shoes(sk, name: str) -> list:
    spec = SHOES[name]
    S = []
    for s in ("l", "r"):
        f = foot_solid(sk, s, (2.35, 1.5, 1.25), spec["sole"], "shoe_" + s)
        top = spec["top"]
        sole = spec["sole"]

        def paint(loc, P, n, top=top, sole=sole):
            names = np.where((loc[:, 2] > -0.2) & (loc[:, 0] > -0.6), top, sole).astype(object)
            return names, np.zeros(len(loc), dtype=np.int16)
        f.paint = paint
        S.append(f)
    return S


def gauntlets(sk) -> list:
    """The training gauntlets (tools/art/bake_gauntlets.py): a steel fist over each hand and a bronze-banded steel cuff
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
