"""Clothes over the body's own solids, so each garment moves with the pose it is cast from.

Shirts (parts.json `shirt`), trousers (`pants`), shoes (`shoes`) and hats (`hat`) are described by a few parameters
each, after the side view's design (in the comment beside each). A garment's regions (belt, lapels, panels, sash, hem,
cuffs, wraps, toe caps) are painted in the frame of the part they sit on, wherever the pose puts it. `cloth` takes the
dye and `panel` a lighter step of it (palettes.DYEABLE), as the side view's luminance dye bake does; trim, belts,
accents and soles keep their colour.
"""
from __future__ import annotations

import numpy as np

from .body import arm_bands, foot_solid, torso
from .geom import unit, vec
from .raster import cone, ellipsoid, limb, sphere

# Shirts.
#   collar  cross: a crossed collar, left over right, edged in `trim`; vee: an open V edged in `trim`
#   panel   a lighter front panel between the lapels (`panel`), with an accent: band (a diagonal stripe), emblem
#   sleeve  wrist (to the wrist, a `cuff` band) | none (bare arms)
#   hem     how far the skirt falls below the belt; `flare` its spread; `apron` a front flap of `panel` below the belt
#   sash    a gold cord knotted at the belt, its ends hanging in front; `dots` scattered gold dots
SHIRTS = {
    # Disciple tunic (the starting shirt): navy teal, a crossed collar edged in gold, a dark belt with a gold buckle, a
    # short skirt to mid-thigh with a gold hem.
    "disciple": {"collar": "cross", "trim": "trim", "sleeve": "wrist", "cuff": "trim", "hem": 3.6, "flare": 0.8,
                 "hem_trim": True, "belt": "belt", "buckle": True},
    # Cloud tunic: grey sleeves and shoulders, a white front panel crossed by a blue and gold stripe, a white apron to the
    # knee, a dark belt.
    "vneck": {"collar": "vee", "trim": "cloth", "panel": "band", "sleeve": "wrist", "cuff": "cloth", "hem": 3.2,
              "flare": 0.7, "apron": 6.4, "belt": "belt"},
    # Sect robe: a long jade robe to the ankle, a V collar, a gold cord knotted at the waist with its ends hanging.
    "cardigan": {"collar": "vee", "trim": "edge", "sleeve": "wrist", "cuff": "edge", "hem": 12.4, "flare": 1.8,
                 "belt": None, "sash": True},
    # Scholar coat: grey sleeves, a white chest with a blue cloud emblem, a black belt, to the hip.
    "scholar": {"collar": "vee", "trim": "cloth", "panel": "emblem", "sleeve": "wrist", "cuff": "cloth", "hem": 3.0,
                "flare": 0.6, "belt": "belt"},
    # Wanderer: a sleeveless jade vest with gold dots, a dark belt, to the hip; the arms bare.
    "sleeveless": {"collar": "vee", "trim": "edge", "sleeve": "none", "hem": 3.0, "flare": 0.6, "belt": "belt",
                   "dots": True},
}

# Trousers. fit: the leg's growth over the body (thigh, knee, ankle); bands: (from, to) along the shin from the knee
# (negative: from the ankle) in `band`.
PANTS = {
    # Silk trousers (the starting pair): loose jade-teal legs gathered at the ankle by grey wraps.
    "loose": {"fit": (1.05, 1.0, 0.95), "bands": [(-1.6, 0.0)], "band": "wrap"},
    # Travel pants: straight teal legs, a grey band under the knee.
    "straight": {"fit": (0.8, 0.75, 0.7), "bands": [(0.6, 1.8)], "band": "wrap"},
    # Leg wraps: teal legs bound with pale green wraps down the shin.
    "cuffed": {"fit": (0.9, 0.75, 0.6), "bands": [(1.0, 2.0), (2.6, 3.6), (-1.4, 0.0)], "band": "wrap"},
    # Scholar pants: plain black, a little wide.
    "scholar": {"fit": (0.95, 0.9, 0.9), "bands": [], "band": "wrap"},
    # Martial pants: navy, tied close at the ankle.
    "martial": {"fit": (1.0, 0.85, 0.55), "bands": [(-1.0, 0.0)], "band": "wrap"},
}

# Shoes. `top` the upper over the `sole`; `boot` the shaft's height up the shin, `cuff` its top band.
SHOES = {
    # Cloth shoes (the starting pair): dark brown, a tan upper.
    "slippers": {"boot": 0.0},
    # Jade greaves: navy shoes under pale steel plates to mid-shin.
    "folded": {"boot": 3.6, "cuff": "plate"},
    # Cloud boots: brown boots with a tan cuff.
    "boots": {"boot": 3.0, "cuff": "top"},
}

# Hats (side view: hat_straw, headband, tied, guan, weimao).
#   straw     a wide cone of plaited straw with a jade band
#   headband  a teal cloth band round the brow, gold studs in front
#   tied      a thin teal band tied at the back, its two ends trailing
#   guan      a small jade crown on the top knot, gold-rimmed, a gold pin through it
#   weimao    a dark wide-brimmed hat with a red band and a pale veil hanging from the brim
HATS = {"straw": {"kind": "cone", "brim": 8.2, "height": 5.6},
        "headband": {"kind": "band", "at": 0.30, "half": 0.13, "grow": 0.95, "studs": True},
        "tied": {"kind": "band", "at": 0.36, "half": 0.07, "grow": 0.9, "tails": True},
        "guan": {"kind": "crown"},
        "weimao": {"kind": "veil", "brim": 8.0}}

# Capes (side view: cape_solid, cape_tattered): a sheet from the shoulders down the back.
CAPES = {"solid": {"length": 13.5, "width": 4.4, "ragged": False},
         "tattered": {"length": 11.0, "width": 4.0, "ragged": True}}


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


def shirt(sk, name: str) -> list:
    spec = SHIRTS[name]
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


def pants(sk, name: str) -> list:
    spec = PANTS[name]
    gt, gk, ga = spec["fit"]
    S = [ellipsoid(sk.pelvis - sk.Mp[:, 2] * 0.5, sk.Mp, (2.6 + 0.8, 3.8 + 0.85, 2.4 + 0.8), "cloth", part="hips")]
    for s in ("l", "r"):
        hp, kn, an = (sk.__dict__[k + "_" + s] for k in ("hip", "knee", "ankle"))
        S += limb(hp, kn, 1.85 + gt, 1.5 + gk, "cloth", part="leg_" + s)
        end = an + unit(an - kn) * 0.3
        L = float(np.linalg.norm(end - kn))
        spans = [(a if a >= 0 else L + a, b if b > 0 else L + b) for a, b in spec["bands"]]

        def shin_paint(loc, P, n, spans=spans):
            w = loc[:, 2]
            on = np.zeros(len(loc), dtype=bool)
            for a, b in spans:
                on |= (w >= a) & (w <= b)
            return np.where(on, spec["band"], "cloth").astype(object), np.zeros(len(loc), dtype=np.int16)
        S += [cone(kn, end, 1.5 + gk, 1.15 + ga, "cloth", part="leg_" + s, paint=shin_paint),
              sphere(kn, 1.5 + gk, "cloth", part="leg_" + s)]
    return S


def shoes(sk, name: str) -> list:
    spec = SHOES[name]
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


def hat(sk, name: str) -> list:
    spec = HATS[name]
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
        from .body import SKULL
        from .hair import CAP_AT, CAP_GROW
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
            from .hair import tail
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


def cape(sk, name: str) -> list:
    """A cape hung from the shoulders down the back, trailing the pose's drag; the tattered one ends in rags."""
    from .hair import tail
    spec = CAPES[name]
    back = -sk.Mc[:, 0]
    up = sk.Mc[:, 2]
    start = sk.chest + sk.Mc @ vec(-3.3, 0.0, 2.6)
    S = [ellipsoid(sk.chest + sk.Mc @ vec(-2.0, 0.0, 3.0), sk.Mc, (2.2, 4.6, 0.9), "cape", part="cape_yoke", band="mid")]
    S += tail(sk, start, back * 0.35 - up, spec["length"], spec["width"], spec["width"] + 1.3, segs=6, stiff=0.6,
              mat="cape", part="cape", k=0.16, ragged=spec["ragged"])
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
